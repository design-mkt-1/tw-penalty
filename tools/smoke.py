#!/usr/bin/env python3
"""Drive the page in a real browser and fail on the things text checks cannot see.

Generalised from tw-flip-cards-lp/tools/smoke.py, which earned four of the
assertions below the hard way. They are kept because both bugs they exist for
are template-wide, not campaign-specific.

Serves the repo from a loopback SimpleHTTPRequestHandler on a random port, so
nothing here needs a build, a deploy, or the network.

Run:
    python -m pip install playwright && python -m playwright install chromium
    python tools/smoke.py
    python tools/smoke.py --headed        # watch it

A campaign adds its own assertions in campaign/smoke.py, exposing
`def check(page, viewport, lang):`. This file imports it if it exists and
calls it once per viewport per language.
"""

import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

# Windows consoles still default to cp1252, and these tools report Ukrainian
# and Russian copy back to the user. Without this the report itself crashes on
# the first Cyrillic character -- which turns a real finding into a traceback.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import platform_stub as stubmod          # noqa: E402  (the stub the platform test uses)

VIEWPORTS = [("desktop", 1440, 900), ("mobile", 375, 812)]

# Ignore-list for console noise a campaign is entitled to produce. The
# unwired-form notice is the template's own and is deliberately loud.
CONSOLE_OK = ("not wired to anything",)


def serve():
    class Quiet(socketserver.TCPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            pass

    class Silent(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    server = Quiet(("127.0.0.1", 0),
                   functools.partial(Silent, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def languages():
    """The campaign's own list, read out of campaign.js without running it."""
    text = (ROOT / "campaign.js").read_text(encoding="utf-8")
    start = text.find("languages:")
    if start < 0:
        return ["ua"]
    chunk = text[start:text.find("]", start)]
    return [bit.strip().strip("'\"") for bit in chunk.split("[")[1].split(",") if bit.strip()]


# Decision 18: every control has a hit area of at least 24x24 CSS px. The hit
# area is the element's own box, or -- where the visible control is smaller and
# a pseudo-element carries the target -- whatever still resolves to the element
# 11.5px either side of its centre. Both are checked with elementFromPoint, so a
# control covered by something else fails as well. Returns one line per failure.
TAP_TARGETS = '''(root) => {
  const NEED = 24, HALF = NEED / 2 - 0.5;
  const scope = root ? document.querySelector(root) : document;
  if (!scope) return ['no element matches ' + root];
  const label = el => (el.className && el.className.baseVal === undefined && el.className) || el.tagName;
  const bad = [];
  for (const el of scope.querySelectorAll(
      'a[href], button, input, select, textarea, [role=option], [role=tab]')) {
    let rects = [...el.getClientRects()].filter(r => r.width > 0 && r.height > 0);
    if (!rects.length) continue;
    if (rects.every(r => r.width >= NEED && r.height >= NEED)) continue;
    const first = rects[0];
    if (first.top < 0 || first.bottom > innerHeight || first.left < 0 || first.right > innerWidth) {
      el.scrollIntoView({block: 'center', inline: 'center'});   // elementFromPoint needs it on screen
      rects = [...el.getClientRects()].filter(r => r.width > 0 && r.height > 0);
    }
    for (const t of rects) {
      if (t.width >= NEED && t.height >= NEED) continue;
      const cx = t.left + t.width / 2, cy = t.top + t.height / 2;
      const dx = t.width >= NEED ? 0 : HALF, dy = t.height >= NEED ? 0 : HALF;
      const hit = (x, y) => { const e = document.elementFromPoint(x, y);
                              return !!e && (e === el || el.contains(e)); };
      const ok = hit(cx - dx, cy - dy) && hit(cx + dx, cy + dy)
              && hit(cx - dx, cy + dy) && hit(cx + dx, cy - dy);
      if (!ok) bad.push(label(el) + ' ' + Math.round(t.width) + 'x' + Math.round(t.height));
    }
  }
  return bad;
}'''


def tap_targets(page, tag, what, fails, root=None):
    small = page.evaluate(TAP_TARGETS, root)
    fails.check(not small, f"{tag} tap target(s) under 24px in {what}: {'; '.join(small)}")


def until(page, js, arg=None, timeout=5000, what="the page"):
    """Poll `js` (an arrow function) until it returns true. Not wait_for_function:
    that evaluates its predicate as a string, which the page's own CSP refuses
    (no 'unsafe-eval'); page.evaluate goes through the debugger and is not
    subject to it. Returns False on timeout instead of raising, so the caller
    reports it as a failure with the page's name on it."""
    waited = 0
    while waited <= timeout:
        if page.evaluate(js, arg):
            return True
        page.wait_for_timeout(50)
        waited += 50
    return False


def settled(page, selector):
    """The element has stopped moving: no running animation or transition."""
    return until(page, "(sel) => document.querySelector(sel).getAnimations({subtree: true}).length === 0",
                 selector)


class Failures(list):
    def check(self, condition, message):
        if not condition:
            self.append(message)


def run_page(page, where, lang, fails):
    tag = f"[{where} {lang}]"

    # 1. The shell mounted. Proves js/shell.js ran and index.html still has
    #    its two mount points -- the one thing a campaign can break in a file
    #    it is allowed to edit.
    for sel, what in ((".tw-hdr", "header"), (".tw-ftr", "footer")):
        box = page.locator(sel).bounding_box()
        fails.check(box and box["width"] > 0 and box["height"] > 0,
                    f"{tag} the {what} did not mount ({sel} has no box)")

    # 2. The page opens where it was written to open.
    fails.check(page.evaluate("window.scrollY") == 0, f"{tag} the page did not open at the top")

    # 3. Nothing is left in flow below the footer. Deliberately not
    #    dialog-aware: it catches anything that parks itself under the last
    #    thing the visitor is meant to see.
    over = page.evaluate("""() => {
        const f = document.querySelector('.tw-ftr');
        const bottom = f ? f.getBoundingClientRect().bottom + window.scrollY : 0;
        return document.documentElement.scrollHeight
             - Math.max(bottom, window.innerHeight);
    }""")
    fails.check(over <= 1, f"{tag} {over}px of page sits below the footer")

    # 4. The closed dialog computes display:none, so the UA's own
    #    `dialog:not([open])` rule is not being beaten by a class. When it was,
    #    the page carried 650px of apparent emptiness and an autofocus that
    #    scrolled to the footer.
    fails.check(
        page.eval_on_selector("#tw-signup", "el => getComputedStyle(el).display") == "none",
        f"{tag} the closed dialog is not display:none")

    # 5. No unresolved key. Catches a campaign that added a string in one
    #    locale and forgot another: the fallback chain ends at the key itself.
    unresolved = page.evaluate("""() => [...document.querySelectorAll('[data-i18n]')]
        .filter(el => el.textContent.trim() === el.getAttribute('data-i18n'))
        .map(el => el.getAttribute('data-i18n'))""")
    fails.check(not unresolved, f"{tag} untranslated key(s): {', '.join(unresolved)}")

    # 6. No dead links. An unset seam leaves NO href; href="#" is a control
    #    that takes focus, is announced as a link and then does nothing.
    dead = page.evaluate("""() => [...document.querySelectorAll('a[href]')]
        .filter(a => { const h = a.getAttribute('href'); return (!h || h === '#') && !a.classList.contains('mail-link'); })
        .map(a => a.className || a.textContent.trim().slice(0, 24))""")
    fails.check(not dead, f"{tag} dead link(s) with href=\"#\": {', '.join(dead)}")
    if page.locator("a.mail-link[href=\"#\"]").count():
        KNOWN_IT.append('IT markup: <a class="mail-link" href="#"> in the page-disabled modal (main.js fills it only when the landing is off)')

    # 7. The dialog works: opens, takes focus, Escape closes it, focus returns.
    page.evaluate("TW.openForm()")
    page.wait_for_timeout(350)
    fails.check(page.eval_on_selector("#tw-signup", "el => el.open"),
                f"{tag} TW.openForm() did not open the dialog")
    # The pop-up's own controls, measured while it is open. They used to be
    # measured only by accident, when a slow runner had not yet finished the
    # dialog's exit transition (see the wait after Escape below).
    settled(page, "#tw-signup")
    tap_targets(page, tag, "the registration pop-up", fails, "#tw-signup")
    fails.check(page.evaluate(
        "document.getElementById('tw-signup').contains(document.activeElement)"),
        f"{tag} focus did not move into the open dialog")

    # 8. The language survives the dialog. i18n.apply(root) exists precisely
    #    because this class of bug is real.
    others = [c for c in page.evaluate("TW.config.languages") if c != lang]
    if others:
        page.evaluate(f"TW.setLang('{others[0]}')")
        page.wait_for_timeout(120)
        fails.check(page.inner_text(".tw-promo__title").strip() != "",
                    f"{tag} the promo block emptied after a language change")
        page.evaluate(f"TW.setLang('{lang}')")

    page.keyboard.press("Escape")
    fails.check(page.evaluate("(async () => { await new Promise(r => setTimeout(r, 50));"
                              " return !document.getElementById('tw-signup').open; })()"),
                f"{tag} Escape did not close the dialog")
    # Wait for the exit transition to END, not for a fixed 350ms. The closing
    # dialog keeps display:flex until its 160ms transition completes (display is
    # allow-discrete), and on a loaded CI runner that is later than 350ms. The
    # old fixed wait then measured the half-closed pop-up's controls as page
    # content: email input 390x19, eye 20x20. Passed locally, flaked on GitHub.
    fails.check(until(page, "() => getComputedStyle(document.getElementById('tw-signup')).display === 'none'"),
                f"{tag} the dialog is still displayed 5s after Escape")

    # 9. Every tap target is at least 24x24. WCAG 2.2 target size (minimum),
    #    decision 18. The pop-up was measured above while open; this is the page.
    tap_targets(page, tag, "the page", fails)


# Known deviations of IT's own markup / CSS from this template's checks
# (decision 25: IT's code is copied 1:1 and is NOT fixed here). They are
# measured and printed, never failed, so the day IT fixes one it shows up as
# gone and a NEW offender still fails the run.
KNOWN_IT = []


def tap_targets_it(page, tag, what, fails, root, expected):
    """tap_targets for IT's markup: the entries in `expected` are IT's known
    deviations (listed, not failed); anything else still fails."""
    small = page.evaluate(TAP_TARGETS, root)
    known = [s for s in small if any(e in s for e in expected)]
    new = [s for s in small if s not in known]
    for s in known:
        KNOWN_IT.append(f"{tag} {what}: {s}")
    fails.check(not new, f"{tag} tap target(s) under 24px in {what}: {'; '.join(new)}")


def run_platform(browser, base, where, w, h, langs, fails):
    """The shell as IT's registration code fills it in, against the stub: not
    one real request. The states the plain run cannot reach -- the Terms /
    Privacy / Login links, which exist only once the landing response supplies
    them, IT's success and reCAPTCHA modals, and IT's page-disabled modal."""
    def context(**state):
        ctx = browser.new_context(viewport={"width": w, "height": h})
        st = stubmod.new_state(**state)
        stubmod.install(ctx, st, [base])
        return ctx, st

    def fits(page, sel):
        return page.evaluate("""(sel) => {
            const r = document.querySelector(sel).getBoundingClientRect();
            return r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight; }""", sel)

    lang = langs[0]
    tag = f"[{where} {lang} platform]"
    ctx, st = context()
    page = ctx.new_page()
    page.goto(f"{base}/index.html?lang={lang}")
    fails.check(until(page, "() => [...document.querySelectorAll('.tw-agree__text a, .tw-foot a')]"
                            ".every(a => a.getAttribute('href'))", timeout=8000),
                f"{tag} IT's code never filled in the Terms / Privacy / Login links")
    tap_targets(page, tag, "the header", fails, ".tw-hdr")
    page.evaluate("TW.openForm()")
    settled(page, "#tw-signup")
    tap_targets(page, tag, "the pop-up with the platform's links", fails, "#tw-signup")
    ctx.close()

    # IT's two result modals: success (their button waits for a click) and the
    # reCAPTCHA refusal. Both are fully on screen.
    for name, state, sel, card in (("success", {}, ".success-modal", ".success-modal__card"),
                                   ("recaptcha", {"recaptcha_ok": False}, ".modal__wrap", ".modal")):
        tag = f"[{where} {langs[0]} {name} modal]"
        ctx, st = context(**state)
        page = ctx.new_page()
        page.goto(f"{base}/index.html?lang={langs[0]}")
        until(page, "() => typeof grecaptcha !== 'undefined'", timeout=8000)
        page.evaluate("TW.openForm()")
        settled(page, "#tw-signup")
        page.fill("#tw-email", "player@example.com")
        page.fill("#tw-password", "Sup3rSecret!")
        page.click('.tw-cta[type="submit"]')
        fails.check(until(page, "(sel) => document.querySelector(sel).classList.contains('active')",
                          sel, timeout=8000), f"{tag} did not open")
        fails.check(fits(page, card), f"{tag} the card does not fit the viewport")
        tap_targets_it(page, tag, f"the {name} modal", fails, sel, [])
        fails.check(not page.evaluate("document.getElementById('tw-signup').open"),
                    f"{tag} the pop-up is still open behind it")
        ctx.close()

    for lang in langs:
        tag = f"[{where} {lang} page disabled]"
        ctx, st = context(active=False)
        page = ctx.new_page()
        page.goto(f"{base}/index.html?lang={lang}")
        fails.check(until(page, "() => document.querySelector('.disabled-modal').classList.contains('active')"
                                " && !!document.querySelector('.mail-link').textContent", timeout=8000),
                    f"{tag} IT's modal did not open with the support address")
        fails.check(page.get_attribute(".mail-link", "href") == "mailto:support@top-win.com",
                    f"{tag} the support address is not support@top-win.com")
        fails.check(fits(page, ".modal-content"), f"{tag} the card does not fit the viewport")
        # IT's .mail-link is a 20px-high line of text: the one known offender.
        tap_targets_it(page, tag, "IT's page-disabled modal", fails, ".disabled-modal", ["mail-link"])
        ctx.close()


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("smoke: playwright is not installed.\n"
              "  python -m pip install playwright\n"
              "  python -m playwright install chromium", file=sys.stderr)
        return 1

    campaign_check = None
    campaign_smoke = ROOT / "campaign" / "smoke.py"
    if campaign_smoke.is_file():
        sys.path.insert(0, str(ROOT / "campaign"))
        import smoke as campaign_module          # noqa: E402
        campaign_check = getattr(campaign_module, "check", None)

    server, port = serve()
    fails = Failures()
    langs = languages()
    headed = "--headed" in sys.argv[1:]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        for where, w, h in VIEWPORTS:
            for lang in langs:
                ctx = browser.new_context(viewport={"width": w, "height": h})
                state = stubmod.new_state()
                stubmod.install(ctx, state, [f"http://127.0.0.1:{port}"])
                page = ctx.new_page()
                noise = []
                page.on("console", lambda m, n=noise: n.append(f"{m.type}: {m.text}")
                        if m.type in ("error", "warning") else None)
                page.on("pageerror", lambda e, n=noise: n.append(f"pageerror: {e}"))

                page.goto(f"http://127.0.0.1:{port}/index.html?lang={lang}")
                page.wait_for_timeout(1700)   # IT's main.js starts 1s late on localhost, then the stub answers

                run_page(page, where, lang, fails)
                if campaign_check:
                    campaign_check(page, where, lang)

                real = [n for n in noise if not any(ok in n for ok in CONSOLE_OK)]
                fails.check(not real, f"[{where} {lang}] console: {' | '.join(real)}")
                fails.check(not state["leaks"], f"[{where} {lang}] left the page: {state['leaks']}")
                page.close()
                ctx.close()
            run_platform(browser, f"http://127.0.0.1:{port}", where, w, h, langs, fails)
        browser.close()

    server.shutdown()

    if KNOWN_IT:
        print(f"smoke: {len(set(KNOWN_IT))} known deviation(s) of IT's own markup (decision 25, not fixed):")
        for k in dict.fromkeys(KNOWN_IT):
            print("  " + k)

    if fails:
        print(f"smoke: {len(fails)} failure(s)\n")
        for f in fails:
            print("  " + f)
        return 1

    print(f"smoke: {len(VIEWPORTS)} viewport(s) x {len(langs)} language(s), "
          "IT's modals and links included, all clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
