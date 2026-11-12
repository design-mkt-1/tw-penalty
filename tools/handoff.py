#!/usr/bin/env python3
"""Zip exactly what a server should serve, plus a note for whoever hosts it.

The deploy allowlist lives in .github/workflows/pages.yml and is the only
statement anywhere of what belongs on a public URL. This script READS that line
rather than restating it: a second copy of the list is a second thing to
forget, and the failure it produces -- tools/, docs/ or raw/ handed to a third
party -- is the one this repo's .gitignore already carries a comment about.

    python tools/handoff.py                 # -> dist/<repo>-<date>.zip
    python tools/handoff.py --out build     # somewhere else

The zip is what IT uploads: open index.html from any static server, no build
step, no runtime dependency, no third-party request. README-IT.md goes in with
it and says what still has to be wired. image.jpg, at the archive root, is a
screenshot of the landing (1440 wide, first screen, ua): IT's own reference
archive carries one and its landing API has a `path_to_image` field.
"""

import argparse
import datetime as dt
import functools
import http.server
import re
import socketserver
import struct
import sys
import tempfile
import threading
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"

# Never shipped, whatever the workflow says. A belt for the allowlist's braces:
# if someone ever writes `cp -r . _site/`, this is what still refuses.
NEVER = ("tools", "docs", "raw", ".git", ".github", ".claude")

# Dev files that live INSIDE a directory the allowlist wants. campaign/ is
# staged because the mechanic is there, and the campaign's own Playwright check
# sits beside it -- served, it is the same mistake as publishing tools/, and it
# arrives through a door that is supposed to be open. .github/workflows/pages.yml
# deletes the same two after its copy.
SKIP_FILES = ("campaign/smoke.py",)
SKIP_DIRS = ("__pycache__",)

# The preview screenshot every archive carries (decision 22).
IMAGE_NAME = "image.jpg"
IMAGE_WIDTH, IMAGE_HEIGHT = 1440, 900
IMAGE_LANG = "ua"
IMAGE_MAX_BYTES = 500 * 1024


def allowlist():
    """The paths the Pages build stages, read out of the workflow."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"cp -r (.+?) _site/", text)
    if not m:
        sys.exit(f"handoff: no `cp -r ... _site/` line in {WORKFLOW}")
    names = [n for n in m.group(1).split() if n]
    bad = [n for n in names if n.split("/")[0] in NEVER or n == "."]
    if bad:
        sys.exit("handoff: the workflow stages something that must not ship: "
                 + ", ".join(bad))
    return names


def staged_files(names):
    """(absolute path, archive path) for every file the allowlist ships."""
    out = []
    for entry in names:
        path = ROOT / entry
        if not path.exists():
            print(f"handoff: {entry} is in the workflow but not in the repo", file=sys.stderr)
            continue
        if path.is_file():
            out.append((path, entry))
            continue
        for f in sorted(path.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(ROOT).as_posix()
            if rel in SKIP_FILES or any(d in f.parts for d in SKIP_DIRS):
                continue
            out.append((f, rel))
    return out


def jpeg_width(data: bytes) -> int:
    """Width from the JPEG's SOF marker; 0 when this is not a JPEG."""
    if data[:3] != b"\xff\xd8\xff":
        return 0
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        (length,) = struct.unpack(">H", data[i + 2:i + 4])
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            return struct.unpack(">H", data[i + 7:i + 9])[0]
        i += 2 + length
    return 0


def preview_image(files):
    """Screenshot the landing exactly as the archive will serve it.

    The staged files are copied into a temp directory and served from loopback,
    so the shot shows what IT's server will show -- and a file missing from the
    allowlist is missing from the picture. Anything that is not loopback is
    aborted: no request reaches IT's API, ipify or Google. With no config.json
    the page runs its demo path on localhost, as tools/smoke.py relies on.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("handoff: playwright is not installed, so image.jpg cannot be made "
                 "and an archive without it is not shipped.\n"
                 "  python -m pip install playwright\n"
                 "  python -m playwright install chromium")

    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp)
        for src, rel in files:
            dest = site / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())

        class Quiet(socketserver.TCPServer):
            allow_reuse_address = True

            def handle_error(self, request, client_address):
                pass

        class Silent(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a):
                pass

        server = Quiet(("127.0.0.1", 0), functools.partial(Silent, directory=str(site)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": IMAGE_WIDTH, "height": IMAGE_HEIGHT})
                page.route("**/*", lambda r: r.continue_()
                           if r.request.url.startswith(f"http://127.0.0.1:{port}/")
                           else r.abort())
                page.goto(f"http://127.0.0.1:{port}/index.html?lang={IMAGE_LANG}",
                          wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(800)          # entrance motion settles
                data = b""
                for quality in (85, 75, 65, 55):
                    data = page.screenshot(type="jpeg", quality=quality)
                    if len(data) <= IMAGE_MAX_BYTES:
                        break
                browser.close()
        finally:
            server.shutdown()
    return data


README = """# {name} — for whoever hosts this

A static landing page. No build step, no server-side code, no runtime
dependency. It talks to one platform, IT's registration API, through
`js/platform.js`, exactly as IT's own template does. There is no
Content-Security-Policy `<meta>` in `index.html`: IT's template has none, and
this page follows it. Upload the contents of this archive to any web server or
object store and open `index.html`.

`image.jpg` is the landing's preview screenshot (1440 wide, first screen,
Ukrainian). The page does not load it.

Everything is referenced with RELATIVE paths, so it runs from the root of a
domain or from a subfolder without an edit.

## 1. The five links

`campaign.js` -> `links`. Each one is a URL or an empty string:

    home     the header logo
    login    "Already have an account? Log in"     <- from the platform
    terms    the consent sentence, first link      <- from the platform
    privacy  the consent sentence, second link     <- from the platform
    cta      the "GO TO WEBSITE" button on the confirmation screen

An empty string leaves the anchor with NO href, so it is not a link at all: no
tab stop, nothing announced, nothing to click. **Do not write `"#"`.**

**Terms, Privacy and Login come from the platform; you do nothing for them.**
With the platform connected, `js/platform.js` (`applyLinks`) sets them from
your landing response, `rules`, `policy` and `login`, on every load and again on
every language switch. The values in `campaign.js` are only a fallback for when
the landing call fails. Check on the live URL that the two consent links in the
form open your Terms and Privacy pages: the page collects an 18+ consent, so
they must not be dead.

## 2. The form

The form is connected to IT's platform by default: `campaign.js` ->
`form.onRegister` hands every registration to `js/platform.js`, which
`index.html` loads. The form is **email and password only**; the phone tab is
removed because the API is registration/email. The platform's own connection
steps are in section 3.

`campaign.js` -> `form.endpoint` is left empty and is not used while
`onRegister` is set. `form.hiddenFields` is copied onto the registration body
BEFORE the platform's own fields, so it can add a field but never overwrite
one.

The password is in the registration body, so the platform's endpoint must be
IT's own TLS endpoint and nowhere else.

## 3. The platform connection -- WHAT WE NEED FROM YOU

`js/platform.js` is IT's template connection (your `_js/main.js`), step for
step: the same requests, headers, order and body. Its flow:

1. `config.json` (below), then `GET config.landing` with `Content-Type` and
   `Accept: application/json`. Analytics come from the landing response.
   `data.active` false -> a "temporarily unavailable" card in UA / RU / EN,
   and nothing else works. It shows `platform.supportEmail` from
   `campaign.js`: TopWin's support address is **support@top-win.com** (a
   mailto link under the sentence "...or write to us:"). If that value is
   ever emptied, the card carries no address.
   Otherwise reCAPTCHA v3 loads (`api.js?render=<recaptcha_key>`) and the
   Terms / Privacy / Login links are set to `rules` / `policy` / `login` as
   your API returns them, with the page's query string appended, as your
   template does (no host filter).
2. `GET https://api.ipify.org?format=json` once at page load; the IP is kept.
3. Submit: `grecaptcha.execute(recaptcha_key, {{action: "register"}})`, then
   `POST config.email_registration` with `Content-Type: application/json`:

       {{ email, password, landing_id, language, currency, country, promocode,
         receivePromos: true, clientIp, ...every URL parameter,
         "g-recaptcha-response" }}

   exactly as your template builds it: every parameter on the page URL is
   spread LAST, so one named like a field overwrites it, as on your page.
   `language` is the active language button lowercased, as in your template:
   `ua`, `ru` or `en`. `promocode` is the one your landing response returns:
   the promo code is set by you, on the landing in your CRM, and nowhere in
   this archive.
4. Success -- as in your template: `response.data.accessToken` is read
   (`redirectUrl` is not). A success modal opens, in TopWin's style, in
   ua / ru / en. When the visitor clicks its button, the token is POSTed to
   `<casino>/api/welcome` as `tmpToken`, with `redirect=<casino>/<lang>/
   <redirect_link>?<page query>`, where `<casino>` is the host of
   `data.rules`. The confirmation screen that shows a login and a password is
   never shown.
5. Errors: `{{ errors: [msg] }}`. "already registered" gets its own translated
   message; anything mentioning reCAPTCHA gets its own translated message and
   a separate modal; everything else is the generic "could not send". The
   server's own text is never shown.

**Development.** On localhost, 127.0.0.1 or `https://land-crm...` the page uses
`campaign.js` -> `platform.dev`, which holds your template's own TEMP_CONFIG
(landing id 8 and its two URLs). A real TopWin dev landing replaces it when
you issue one. Emptied, localhost runs the demo path and land-crm reads
`config.json`. It never reaches a visitor on the live domain.

**Production.** The page fetches `config.json` from next to `index.html` (in
the same folder as the page), one file per landing, with the id IT gives THIS
landing. The path is relative, so this holds on subfolder hosting too: a page
at `/promo/index.html` reads `/promo/config.json`, never a
`config.json` at the domain root.

    {{ "id": <the landing_id IT gave you>,
      "email_registration": "https://<api host>/api/jp/registration/email",
      "landing": "https://<api host>/api/jp/landing/<the same id>" }}

**WITHOUT `config.json` THE PAGE IS NOT CONNECTED.** It still looks finished:
the form validates, writes `[platform] config.json not found: this build is not
connected to the platform.` to the browser console and shows the demo
confirmation screen. Nothing on screen says so.
Check the console on the first deploy.

A copied id sends registrations to another landing with no visible error. Use
only the id IT gives this landing.

### What you have to supply or change

1. **CORS** on the landing and registration endpoints for the domain this page
   is served from: a `GET` carrying `Content-Type: application/json` (so a
   preflight) and a JSON `POST`.
2. **The reCAPTCHA v3 key** (`recaptcha_key` in the landing response) must be
   registered for THIS page's domain with Google.
3. **No Content-Security-Policy.** `index.html` has none, as your template has
   none. If your server adds one as a header, it must allow everything above:
   your API, `api.ipify.org`, `www.google.com/recaptcha/` +
   `www.gstatic.com/recaptcha/`, the analytics hosts, and the `/api/welcome`
   origin of step 4.
4. **Confirm, because the flow has not been tested against every landing:**
   - the registration endpoint accepts `language: "ua"`, `"ru"` and `"en"`
     (your template's rule: the language button lowercased);
   - the casino site has `/ua/`, `/ru/` and `/en/` routes for the fallback
     redirect, and what `redirect_link` should be;
   - which SSO hand-off is right (step 4).
5. **The reCAPTCHA v3 badge is hidden** (`.grecaptcha-badge` in `css/form.css`),
   as IT's LP does it. The `clientIp` from `api.ipify.org` is sent too, as IT's
   LP does it.

## 4. Tracking, and the affiliate click id

`campaign.js` -> `params` is appended to every outbound link and copied into
the form payload.

`campaign.js` -> `passthrough` names query parameters on the LANDING page's own
URL that ride through to the outbound click:

    {passthrough}

That is how an affiliate click id survives the page: the network puts
`?click_id=...` on the landing URL, and the visitor arrives at the operator
with the same id attached. If your redirect drops these, the attribution is
lost here and nowhere else.

Analytics. With the platform connected, Google Analytics, Yandex Metrika and
Google Tag Manager come from the landing response, loaded by `js/platform.js`.
`analytics.gtmId` and `analytics.metaPixelId` in `campaign.js` are still read
by `js/shell.js`: set one only if IT does not already load that tag, or it
loads twice.

## 5. Languages

`campaign.js` -> `languages`, in header-menu order; the first is the default
and the fallback. `?lang=xx` on the URL overrides it. All the copy is in
`campaign.js` and `js/strings.js`; there is no per-language HTML file.

## 6. Browsers

Floor: Chrome/Edge 105, Safari 16, Firefox 110. Full motion from Chrome/Edge
117, Safari 17.4, Firefox 129. Below the floor the registration pop-up does not
open -- that one is a hard fail, not a degradation.

## 7. What is NOT in this archive

The guards and tools in `tools/`, the docs and any source art. They are
development files and have no business on a public URL. The repository is the
place for them: {repo}
"""


def campaign_value(key):
    """One value out of campaign.js, read as text. Good enough for a README and
    deliberately not a JS parser.

    The trailing `// comment` is cut off first. Half the keys in campaign.js
    carry one, and a campaign that adds a comment after `passthrough` would
    otherwise hand IT a README with the comment inside the value -- which is
    exactly what happened at tw-flip-cards-lp with `offer.code`.
    """
    text = (ROOT / "campaign.js").read_text(encoding="utf-8")
    m = re.search(r"^\s*" + key + r":\s*(.+?),?\s*$", text, re.M)
    if not m:
        return ""
    value = re.sub(r"\s*//.*$", "", m.group(1)).strip()
    return value.rstrip(",").strip("'\"")


def shown(path: Path) -> str:
    """Repo-relative when inside the repo, absolute when --out points elsewhere."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="dist", help="where to write the zip (default: dist)")
    args = ap.parse_args()

    name = campaign_value("id") or ROOT.name
    stamp = dt.date.today().isoformat()
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{name}-{stamp}.zip"

    passthrough = campaign_value("passthrough") or "[]"
    readme = README.format(
        name=name,
        repo=f"https://github.com/design-mkt-1/{ROOT.name}",
        passthrough=passthrough,
    )

    files = staged_files(allowlist())
    image = preview_image(files)

    staged = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path, rel in files:
            z.write(path, rel)
            staged.append(rel)
        z.writestr("README-IT.md", readme)
        staged.append("README-IT.md")
        z.writestr(IMAGE_NAME, image)
        staged.append(IMAGE_NAME)

    # The check. Cheap, and it is the whole reason to have a script rather than
    # a zip command someone types from memory once a quarter.
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    assert "index.html" in names, "handoff: the archive has no index.html"
    assert IMAGE_NAME in names, f"handoff: the archive has no {IMAGE_NAME}"
    with zipfile.ZipFile(zip_path) as z:
        width = jpeg_width(z.read(IMAGE_NAME))
    assert width == IMAGE_WIDTH, (f"handoff: {IMAGE_NAME} is not a JPEG "
                                  f"{IMAGE_WIDTH} px wide (got {width})")
    leaked = [n for n in names if n.split("/")[0] in NEVER
              or n in SKIP_FILES or any(d in n.split("/") for d in SKIP_DIRS)]
    assert not leaked, "handoff: the archive contains " + ", ".join(leaked)

    size = zip_path.stat().st_size
    print(f"handoff: {shown(zip_path)} "
          f"— {len(names)} file(s), {size / 1024:.0f} kB, "
          f"{IMAGE_NAME} {len(image) / 1024:.0f} kB")
    print("         staged: " + ", ".join(allowlist()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
