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
and not one third-party request. Upload the contents of this archive to any web
server or object store and open `index.html`.

Everything is referenced with RELATIVE paths, so it runs from the root of a
domain or from a subfolder without an edit.

## 1. The four links

`js/main.js`, at the top of the file. Each is a URL string or `null`:

    HOME_URL     the logo in the header bar
    LOGIN_URL    "Вже є акаунт? Увійти" under the register button
    TERMS_URL    the consent sentence, first link        <- BLOCKS GO-LIVE
    PRIVACY_URL  the consent sentence, second link       <- BLOCKS GO-LIVE

`null` leaves the anchor with NO href, so it is not a link at all: no tab stop,
nothing announced, nothing to click. **Do not write `"#"`** — that offers a
control that takes focus, is announced as a link and does nothing, and it drops
a bare fragment into the address bar of a page that is not allowed to scroll.

`TERMS_URL` and `PRIVACY_URL` block go-live because the page collects an 18+
consent. Dead consent links on a gambling registration form are a compliance
problem, not a cosmetic one.

## 2. The form, and the fifth URL

`js/form.js`, at the top of the file — this is the one that is easy to miss,
because it is not in the same file as the four above:

    SUBMIT       function (data) { ... }   what receives the registration
    DESTINATION  URL                       the "ПЕРЕЙТИ НА САЙТ" button on the
                                           confirmation screen

With both `null` the page is fully demoable and sends nothing: the card
validates, writes the payload to the browser console, and walks the
confirmation screen anyway. To a visitor that looks like a completed
registration. **Wire `SUBMIT` before go-live, or state in writing that the
console route ships.**

`SUBMIT` receives exactly what the visitor filled in:

    { via: 'email' | 'phone',
      contact:  the email, or the phone as unspaced E.164 (380931234567),
      password: as typed,
      lang:     'uk' | 'ru' | 'en' }

It carries the password, which means **it must post to your own TLS endpoint
and nowhere else**. It is called last, inside a try: a hook that throws costs
you that one delivery, not the visitor's confirmation screen. Look for
`[tw-penalty] the submit hook failed` in the console.

The phone field accepts `931234567`, `0931234567` and `380931234567` and
normalises all three to the same value before your hook sees it.

## 3. Tracking

There is none, and there is no seam for one. This landing predates the
affiliate passthrough that `tw-lp-template` added, so a `?click_id=...` on the
landing URL does NOT ride through to the outbound click — attribution stops
here. If the campaign needs it, say so: it is a change in this repo, not
something to be configured in the archive.

No analytics script, no pixel, no Content-Security-Policy meta. With the page
as shipped it makes zero third-party requests; that is worth keeping.

## 4. Languages

Ukrainian, Russian and English, all three in `js/i18n.js`, switched from the
menu in the header bar. The choice persists in `localStorage` under `tw-lang`.

There is one HTML file, not three, and there is no `?lang=` override on the
URL: to see another language, use the menu. Ukrainian is the default and the
fallback on a first visit.

## 5. Browsers

Read off the features this page uses, not measured on the devices — treat it
as a floor to test against rather than a guarantee:

    Chrome / Edge 105, Safari 16, Firefox 112

Container queries set the first two: `css/stage.css` and `css/game.css` size
the whole pitch with them, so below that the layout does not merely degrade.
Firefox is 112 rather than 110 because the registration card takes the page
behind it out of the accessibility tree with `inert`; below that the card still
opens and still traps focus by hand, but a screen reader can reach what is
behind it.

`backdrop-filter` on the header bar degrades to a flat colour and is not part
of the floor.

## 6. What is NOT in this archive

`tools/`, `docs/` and the source renders in `raw/`. They are development files
and have no business on a public URL — the two guard scripts, the art pipeline
and the session notes all live in the repository instead:

    https://github.com/design-mkt-1/tw-penalty

The live preview is https://design-mkt-1.github.io/tw-penalty/ and is built
from the same allowlist this archive is built from.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="dist", help="where to write the zip (default: dist)")
    args = ap.parse_args()

    stamp = dt.date.today().isoformat()
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{ROOT.name}-{stamp}.zip"

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
        z.writestr("README-IT.md", README)
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
