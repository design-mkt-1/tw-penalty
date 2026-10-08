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
# if someone ever writes `cp -r . _site/`, this is what still refuses.
NEVER = ("tools", "docs", "raw", ".git", ".github", ".claude")

# Dev files that live INSIDE a directory the allowlist wants. campaign/ is
# staged because the mechanic is there, and the campaign's own Playwright check
# sits beside it -- served, it is the same mistake as publishing tools/, and it
# arrives through a door that is supposed to be open. .github/workflows/pages.yml
# deletes the same two after its copy.
SKIP_FILES = ("campaign/smoke.py",)
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


README = """# {name} — for whoever hosts this

A static landing page. No build step, no server-side code, no runtime
dependency. It talks to exactly one platform, IT's registration API, through
`js/platform.js`, and to the origins listed in the Content-Security-Policy
`<meta>` in `index.html`, and to nothing else. Upload the contents of this
archive to any web server or object store and open `index.html`.

Everything is referenced with RELATIVE paths, so it runs from the root of a
domain or from a subfolder without an edit.

## 1. The five links

`campaign.js` -> `links`. Each one is a URL or an empty string:

    home     the header logo
    login    "Already have an account? Log in"
    terms    the consent sentence, first link      <- BLOCKS GO-LIVE
    privacy  the consent sentence, second link     <- BLOCKS GO-LIVE
    cta      the "GO TO WEBSITE" button on the confirmation screen

An empty string leaves the anchor with NO href, so it is not a link at all: no
tab stop, nothing announced, nothing to click. **Do not write `"#"`.**

`terms` and `privacy` block go-live because the page collects an 18+ consent.
Dead consent links on a gambling registration form are a compliance problem,
not a cosmetic one.

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

`js/platform.js` follows IT's reference landing step for step. Its flow:

1. `GET config.landing` on every load, with `Content-Type` and `Accept:
   application/json`. `data.active` false -> a "temporarily unavailable" card
   with `support@jack-pot.com`, in UA / RU / EN, and nothing else works.
   Otherwise the Terms / Privacy / Login links come from `rules` / `policy` /
   `login`, analytics come from the landing response, and reCAPTCHA v3 loads
   with `data.recaptcha_key`.
2. Submit: reCAPTCHA token (action `register`), the visitor's IP from
   `api.ipify.org`, then `POST config.email_registration`:

       {{ email, password, landing_id, language, currency, country, promocode,
         receivePromos: true, clientIp, "g-recaptcha-response",
         ...URL params from the whitelist in campaign.js § passthrough }}

   `language` is `uk`, `ru` or `en`. The URL params are spread FIRST, so a
   parameter called `email` or `landing_id` cannot overwrite the real field.
3. Success: `response.data.accessToken` and `response.data.redirectUrl` come
   back. The token is POSTed to `<mirror>/api/welcome` as `tmpToken`, where
   `<mirror>` is the origin of `redirectUrl`, with `redirect` = `redirectUrl`
   plus the page's query string. Without `redirectUrl` the fallback is
   `<casino>/api/welcome`, with `redirect=<casino>/<lang>/<redirect_link>?<page
   query>`, where `<casino>` is the host of `data.rules`. The confirmation
   screen that shows a login and a password is never shown.
4. Errors: `{{ errors: [msg] }}`. "already registered" and anything mentioning
   reCAPTCHA get their own translated message; everything else is the generic
   "could not send".

**Development.** On localhost, 127.0.0.1 or `https://land-crm...` the page uses
`campaign.js` -> `platform.dev`, IT's own test landing (id 8). It never reaches
a visitor on the live domain.

**Production.** The page fetches `config.json` from the site root, one file
per landing, with the id IT gives THIS landing:

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
3. **The Content-Security-Policy `<meta>` in `index.html`.** A CSP refusal shows
   ONLY in the browser console; the visitor sees nothing. Add
   `form-action 'self' https://<casino domain>` for the `/api/welcome` POST. The
   directive is absent today because that domain comes from the API at runtime
   and could not be written here. The production API origin is already in
   `connect-src`.
4. **Confirm with IT, because the flow has not been tested against every
   landing:**
   - the registration endpoint accepts `language: "uk"` and `"ru"`;
   - the casino site has `/uk/` and `/ru/` routes for the redirect, and what
     `redirect_link` should be.
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
loads twice. The Content-Security-Policy `<meta>` in `index.html` has no Meta
origin, so `metaPixelId` will be refused. A CSP refusal appears only in the
console: the page looks fine and silently sends nothing.

## 5. Languages

`campaign.js` -> `languages`, in header-menu order; the first is the default
and the fallback. `?lang=xx` on the URL overrides it. All the copy is in
`campaign.js` and `js/strings.js`; there is no per-language HTML file.

## 6. Browsers

Floor: Chrome/Edge 105, Safari 16, Firefox 110. Full motion from Chrome/Edge
117, Safari 17.4, Firefox 129. Below the floor the registration pop-up does not
open -- that one is a hard fail, not a degradation.

## 7. What is NOT in this archive

The four guards in `tools/`, the docs and any source art. They are development
files and have no business on a public URL. The repository is the place for
them: {repo}
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
                    if rel in SKIP_FILES or any(d in f.parts for d in SKIP_DIRS):
                        continue
                    z.write(f, rel)
                    staged.append(rel)
        z.writestr("README-IT.md", readme)
        staged.append("README-IT.md")

    # The check. Cheap, and it is the whole reason to have a script rather than
    # a zip command someone types from memory once a quarter.
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    assert "index.html" in names, "handoff: the archive has no index.html"
    leaked = [n for n in names if n.split("/")[0] in NEVER
              or n in SKIP_FILES or any(d in n.split("/") for d in SKIP_DIRS)]
    assert not leaked, "handoff: the archive contains " + ", ".join(leaked)

    size = zip_path.stat().st_size
    print(f"handoff: {zip_path.relative_to(ROOT).as_posix()} "
          f"— {len(names)} file(s), {size / 1024:.0f} kB")
    print("         staged: " + ", ".join(allowlist()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
