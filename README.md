# tw-penalty

The Top Win penalty landing page, built on
[`tw-lp-template`](https://github.com/design-mkt-1/tw-lp-template).

The visitor picks a target in the goal. The keeper saves the first attempt,
the second always scores, and the goal opens the registration card. Static: no
build step, no runtime dependencies, no third-party request.

## What is the template's, and what is this repo's

Everything in `css/`, `js/`, `tools/` (the four guards) and
`.github/workflows/` came from the template and must not be edited here.
`python tools/drift.py` fails if one of them changes — a fix that belongs to
every campaign belongs in the template repo, and this landing is where the
habit of fixing it locally produced four different oranges.

This campaign is five files:

| file | what it is |
|---|---|
| `campaign.js` | the offer, the five link seams, the languages, the copy |
| `campaign/main.js` | the game: two scripted shots, ending in `TW.openForm()` |
| `campaign/fx.js` | the canvas — ball in flight, its shadow, the net, confetti |
| `campaign/animator.js` | the keeper's ten sprites and the dives |
| `campaign/audio.js` | the seven clips and the mute state |
| `campaign/main.css` | the pitch, the goal, the plates, the keeper, the ball |
| `campaign/smoke.py` | the mechanic's own browser check |
| `index.html` | the `<main>` block, and the `css/stage.css` link |

`tools/ball_sheet.py`, `tools/cutout.py` and `tools/sfx.py` are this campaign's
art and sound tools, kept because `docs/ART.md` is the recipe for reproducing
every render.

## Before it goes live

`campaign.js § links` is empty. `terms` and `privacy` block go-live: the card
collects an 18+ consent, and dead consent links on a gambling registration form
are a compliance problem. An unset seam leaves the anchor with **no href at
all** — never `"#"`, which `tools/smoke.py` fails on.

`form.endpoint` is empty too, so a submitted form logs its payload to the
console and walks the confirmation screen. That is deliberate: the page is
fully demoable before the platform exists, and it cannot silently half-ship.

## Running it

```bash
python -m pip install fonttools brotli playwright
python -m playwright install chromium

python tools/drift.py            # the shared files are the template's
python tools/tokens.py --check   # no colour literal outside css/tokens.css
python tools/fonts.py --check    # every rendered character exists in a face
python tools/smoke.py            # a real browser, 2 viewports x 3 languages,
                                 # plus campaign/smoke.py's own three shots
python -m http.server 8000
```

**Repository → Settings → Pages → Source: GitHub Actions.** Left on a branch,
the legacy builder publishes the whole repository and the `_site` allowlist in
`.github/workflows/pages.yml` never runs.
