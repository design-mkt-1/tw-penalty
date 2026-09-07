#!/usr/bin/env python3
"""Zip exactly what a server should serve, plus a note for whoever hosts it.

Ported from tw-lp-template, which was distilled out of this landing. The idea
is the same and is the whole reason this is a script: the deploy allowlist in
.github/workflows/pages.yml is the only statement anywhere of what belongs on
a public URL, so this READS that line rather than restating it. A second copy
of the list is a second thing to forget, and what it produces -- tools/, docs/
or raw/ handed to a third party -- is the failure this repo's .gitignore
already carries a comment about.

    python tools/handoff.py                 # -> dist/tw-penalty-<date>.zip
    python tools/handoff.py --out build     # somewhere else

The zip is what IT uploads: open index.html from any static server, no build
step, no runtime dependency, no third-party request. README-IT.md goes in with
it and says what still has to be wired.
"""

import argparse
import datetime as dt
import re
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"

# Never shipped, whatever the workflow says. A belt for the allowlist's braces:
# if someone ever writes `cp -r . _site/`, this is what still refuses. It has
# fired here before -- when Pages was left on a branch, the legacy builder
# published tools/cutout.py and .gitignore on the live URL.
NEVER = ("tools", "docs", "raw", ".git", ".github", ".claude")

# Dev files that live INSIDE a directory the allowlist wants.
SKIP_DIRS = ("__pycache__",)


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


README = """# tw-penalty — for whoever hosts this

A static landing page: the visitor picks a corner of the goal, the keeper saves
the first attempt, the second always goes in, and the goal opens the
registration card. No build step, no server-side code, no runtime dependency,
and as shipped not one third-party request. Upload the contents of this archive
to any web server or object store and open `index.html`.

Everything is referenced with RELATIVE paths, so it runs from the root of a
domain or from a subfolder without an edit.

## 1. campaign.js is the only file you edit

It sits at the root of the archive and is one file of commented settings.

**The header, the footer and the registration card are not this landing's
code.** They are shared with every other Top Win landing — `css/shell.css`,
`css/form.css`, `css/tokens.css`, `js/strings.js`, `js/i18n.js`, `js/form.js`,
`js/shell.js` — so that one design cannot become three drawings of itself.
Editing them here means the next landing gets a different card. `campaign/` is
the game: the pitch, the keeper, the ball and the effects canvas.

## 2. The five links

`campaign.js` -> `links`. Each is a URL or an empty string:

    home     the logo in the header bar
    login    "Вже є акаунт? Увійти" under the register button
    terms    the consent sentence, first link        <- BLOCKS GO-LIVE
    privacy  the consent sentence, second link       <- BLOCKS GO-LIVE
    cta      the "ПЕРЕЙТИ НА САЙТ" button on the confirmation screen

An empty string leaves the anchor with NO href, so it is not a link at all: no
tab stop, nothing announced, nothing to click. **Do not write `"#"`.**

`terms` and `privacy` block go-live because the page collects an 18+ consent.
Dead consent links on a gambling registration form are a compliance problem,
not a cosmetic one. All five used to live in two different JavaScript files —
four in `js/main.js` and the fifth in `js/form.js` — which is exactly the kind
of split that gets one of them forgotten at handover.

## 3. The form

`campaign.js` -> `form.endpoint`. Set it and the card POSTs JSON there; a
response carrying `{{ "login": "...", "password": "..." }}` fills the
confirmation screen. `form.onRegister(payload)` is the escape hatch for
anything more involved: it returns a promise and overrides `endpoint`.

The payload:

    {{ method: 'email' | 'phone',
      contact: the one that was filled in,
      email, phone, password, consent,
      lang: 'uk' | 'ru' | 'en',
      bonus: '{bonus}',
      landing_id: '{landing}',
      ...form.hiddenFields, ...params }}

It carries the password, which means **`endpoint` must be your own TLS endpoint
and nowhere else**. A CSRF token belongs in `form.hiddenFields`.

Leave both empty and NOTHING IS SENT: the validated payload goes to the browser
console and the confirmation screen is walked anyway, so the page is demoable
before the platform exists. It says so in the console, loudly, so it cannot be
mistaken for a working integration.

The phone field accepts `931234567`, `0931234567` and `380931234567` and
normalises all three before your hook sees them.

## 4. Tracking, and the affiliate click id

`campaign.js` -> `params` is appended to every outbound link and copied into the
form payload.

`campaign.js` -> `passthrough` names query parameters on the LANDING page's own
URL that ride through to the outbound click:

    {passthrough}

That is how an affiliate click id survives the page. This landing had no such
seam at all until it adopted the shared shell: an id on the landing URL was
lost here and nowhere else.

`analytics.gtmId` / `analytics.metaPixelId` are empty and with both empty the
page makes no third-party request. There is no Content-Security-Policy meta in
this page's head, so nothing has to be relaxed for an endpoint on another
origin — and nothing protects it either, which is worth knowing before adding
a tag manager.

## 5. Languages

Ukrainian, Russian and English, one HTML file, switched from the menu in the
header bar and persisted in `localStorage` under `tw-lang`. `?lang=ru` on the
URL forces one for a single creative without persisting it.

Everything the header, the footer and the card say is in `js/strings.js`, which
is the same file in every Top Win landing. What this campaign says — the
tagline over the goal, the six panel labels, the two messages between shots —
is in `campaign.js` -> `strings`.

## 6. Browsers

The hard requirement is `<dialog>` with `showModal()`: Chrome/Edge 79+,
Safari 15.4+, Firefox 98+. Below that the registration card does not open at
all, which is a failure and not a degradation.

Container queries set the practical floor: `css/stage.css` and
`campaign/main.css` size the whole pitch with them, so below Chrome 105 /
Safari 16 / Firefox 110 the layout does not merely degrade. The card's entry
animation needs `@starting-style` (Chrome 117, Safari 17.4, Firefox 129) and
simply appears without it; `backdrop-filter` falls back to a flat colour.

These numbers are read off the features the page uses, not measured on devices.

## 7. What is NOT in this archive

`tools/`, `docs/` and the source renders in `raw/`. They are development files
and have no business on a public URL — the four guards, the art pipeline and
the session notes live in the repository instead:

    https://github.com/design-mkt-1/tw-penalty

The live preview is https://design-mkt-1.github.io/tw-penalty/ and is built
from the same allowlist this archive is built from.
"""


def campaign_value(key):
    """One value out of campaign.js, read as text. Good enough for a README and
    deliberately not a JS parser. The trailing `// comment` is cut first: half
    the keys carry one."""
    text = (ROOT / "campaign.js").read_text(encoding="utf-8")
    m = re.search(r"^\s*" + key + r":\s*(.+?),?\s*$", text, re.M)
    if not m:
        return ""
    value = re.sub(r"\s*//.*$", "", m.group(1)).strip()
    return value.rstrip(",").strip("'\"")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="dist", help="where to write the zip (default: dist)")
    args = ap.parse_args()

    stamp = dt.date.today().isoformat()
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{campaign_value('id') or ROOT.name}-{stamp}.zip"

    staged = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for entry in allowlist():
            path = ROOT / entry
            if not path.exists():
                print(f"handoff: {entry} is in the workflow but not in the repo", file=sys.stderr)
                continue
            if path.is_file():
                z.write(path, entry)
                staged.append(entry)
            else:
                for f in sorted(path.rglob("*")):
                    if not f.is_file():
                        continue
                    rel = f.relative_to(ROOT).as_posix()
                    if any(d in f.parts for d in SKIP_DIRS):
                        continue
                    z.write(f, rel)
                    staged.append(rel)
        z.writestr("README-IT.md", README.format(
            bonus=campaign_value("code"),
            landing=campaign_value("id") or ROOT.name,
            passthrough=campaign_value("passthrough") or "[]"))
        staged.append("README-IT.md")

    # The check. Cheap, and it is the whole reason to have a script rather than
    # a zip command someone types from memory once a quarter.
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    assert "index.html" in names, "handoff: the archive has no index.html"
    leaked = [n for n in names if n.split("/")[0] in NEVER
              or any(d in n.split("/") for d in SKIP_DIRS)]
    assert not leaked, "handoff: the archive contains " + ", ".join(leaked)

    size = zip_path.stat().st_size
    print(f"handoff: {zip_path.relative_to(ROOT).as_posix()} "
          f"— {len(names)} file(s), {size / 1024:.0f} kB")
    print("         staged: " + ", ".join(allowlist()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
