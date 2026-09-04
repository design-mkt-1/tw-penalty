# Where this stands, and what is next

A static penalty-shootout landing page for Top Win: the visitor picks a target
in the goal, the keeper saves the first attempt, the second always goes in, and
the goal opens the registration card. No build step, no runtime dependencies.

Ported from `fs-penalty`, whose architecture this reuses wholesale — the same
fluid no-scroll stage, the same single `--gw` unit, the same Spine-shaped
animator interface over raster sprites, the same Pages allowlist.

Live: **https://design-mkt-1.github.io/tw-penalty/**

## State

| Stage | State |
|---|---|
| 1. Skeleton and port | done — `c5f926a` |
| 2. Brand layer | done — `287593d` |
| 3. Artwork | done — `3918a6d`, `d280b7a`, `3b8e80d` |
| 4. Re-measurement | done — `d280b7a`, `3dbe78e`, `558a42e` |
| 5. Registration card | done — `ffcaf44` |
| 6. i18n | done — `3e81d20` |
| 7. Footer | done — `c27eb9f`, `ddf76cb` |
| 8. Deploy | done and verified on the live URL |
| 9. Handoff | this file |

**Everything buildable is built.** What is left is one gate that cannot be
closed from a desk, one decision that belongs to the client, and three declared
limitations. They are at the bottom of this file.

## What was measured, and why those numbers

Nothing in the geometry is tuned by eye. Each number is a measurement divided by
one unit, and the comments in `css/game.css` carry the raw pixels so the chain
can be re-derived rather than trusted.

**The plate.** In `assets/img/pitch-spot.webp` (1800×1208) the posts stand at
x 681 and 1118, the crossbar's top edge at y 523, the goal line at y 681 — a goal
of 437 × 158 image pixels. Every ratio at `.pitch::before` is one of those
measurements over 437, written as a division rather than as a decimal copy.

The framing target was a single number, not three. In a 3:2 frame, a goal
spanning a quarter of the width forces the height to 2.667 goal widths on its
own. This plate lands at 24.3%, giving 2.76 against the 2.49 the worst case
(430×932) needs, so unlike the reference it needed no synthetic bottom
extension.

**The measuring script matters more than the numbers.** Its first version put
the crossbar 350px too high, because it measured the span between a row's
outermost bright pixels — and a row crossing two floodlights spans the frame
while being two small blobs. Floodlights are brighter than the goal. A crossbar
is a contiguous run, and measuring one matches all four known values to within
half a percent. Re-measure with a run, never a span.

**The goal box has to land on the painted goal, and did not.** Verified by
computing where the posts, the crossbar and the goal line fall inside the
rendered plate and comparing that with `.goal`'s box, at six viewport sizes.
Two faults, both worth remembering:

- `.goal` took its height from `aspect-ratio: 690 / 248` — the reference
  project's render — while `--goal-h` had already been re-measured to the Top
  Win 158/437. One goal, two heights, and the box came out 0.6% short. The
  panels, the keeper and the strike ring are all percentages of that box, so
  every one of them was short by the same fraction.
- The plate hung off the image's centre rather than the goal's. The posts at
  681 and 1118 put the painted goal's centre at 899.5 of 1800 — half a pixel
  left of the image centre — which showed up as a 0.64px offset, identical on
  both edges, scaling with the goal. The half-width is `-899.5/437` now.

Worst deviation is 0.017px across 320×568 to 1920×1200. If a change ever makes
the panels drift off the posts, measure the plate against `.goal` again before
touching anything else.

**The keeper box.** The figure spans **.8562** of its canvas and its feet sit at
**.9344** of it. A 1.88m keeper against a 2.44m goal is .7705 of the goal's
height, so the box is .7705 / .8562 = **89.98%** of it; the box's aspect is the
canvas's, so as a share of the goal's width it is 89.98% × (158/437) × (429/640)
= **21.81%**; and the drop below the goal line is (1 − .9344) × 89.98% =
**5.91%**. The formula was checked against the reference project's published
95.24 / 22.95 / 6.57 before being used here, and reproduces all three to within
two hundredths of a point.

**The dive offsets are solved, not scaled.** For each corner pose: measure where
the reaching glove sits inside its own sprite — the centroid of the 300 pixels
furthest along the direction of the dive — then read the rendered panel centre
and keeper box out of the live page and solve for the translation that lands the
glove four points of the goal's width short of that centre. The panel centres
must be read rather than computed: `.panels` sets its gap and padding in
`clamp()`, so they move with the goal's size.

The two centre poses are deliberately not solved. Both would have to leave the
ground to reach their panel's centre — `jump_center` already reaches above it,
and `jump_center_down` kneels on the goal line — so they keep zero and get their
read from the pose, which is why each has its own render.

## Decisions, with their reasons

**One typeface, Roboto, everywhere.** The brandbook prescribes Russo One for
headlines, but no delivered screen uses it. The card's headline is Roboto
Condensed Black Italic (`wdth 75`, weight 900). The design draws the card and
footer UI in Inter, which is deliberately not followed: the brandbook says
Roboto. Condensed is a coordinate on the family, not a second download, and
`--font-stretch-tight` names it.

**`ua` is not a language tag.** It is the region subtag for Ukraine; the
language is `uk`. `js/i18n.js` keeps `ua` as the internal code the design and
the menu use, and maps it through `LOCALE` wherever a real tag is required —
`documentElement.lang`, and the value `js/form.js` hands the submit hook.
`detect()` reads through the same map, so a browser reporting `uk-UA` matches
Ukrainian instead of reaching it by falling through to the fallback.

**Contrast decides the colours, not fidelity.** The pitch is graded deep navy,
so anything navy on it disappears. The keeper's kit is orange with navy trim
rather than the navy kit the brandbook banners show, because those banners sit
on a light background and this one does not. Two rounds of plate renders were
spent on the same problem: a lit orange hoarding kept appearing straight through
the goal mouth. Asking for "no advertising boards" did not remove it; stating
the requirement as brightness did.

**The sources contradict themselves, and the code says so rather than picking
silently.** The brandbook lists `BG SECONDARY` as a stray copy of the orange
next to a correct RGB triple, and defines `BG THIRD` as two different colours on
consecutive pages. The card's own screens carry two greens (`#43a047` on the
consent box beside `#00a75c` on the links), two reds (`#e74f4f` and `#e53935` on
two fields in one screenshot) and two navies (`#171671` under a `#191970`
title). Each is routed through one token, and `css/form.css` names all three.

**Two services, one model.** The keeper was rendered on Google Nano Banana 2 —
`nano_banana_2` on Higgsfield, `imagen-nano-banana-2-flash` on Magnific — after
the first account hit a daily generation cap partway through the set. 4k at 2:3
returns 3392×5056 from both, verified rather than assumed, so every pose shares
one coordinate space. `docs/ART.md` carries the prompts, the job ids and the
naming trap: Pro is a different model and the two services name the tiers the
other way round.

**Generated art is kept out of git; recipes are kept in.** `raw/` is ignored.
`tools/ball_sheet.py` renders the ball, `tools/cutout.py` turns raw renders into
sprites, and `docs/ART.md` carries the prompts. The plate's recipe was verified
by regenerating `pitch-spot.webp` byte-identical.

## Traps already paid for

- **`FRAMES`, `COLS` and `SIZE` in `tools/ball_sheet.py` are duplicated in
  `js/fx.js`** as `BALL_FRAMES`, `BALL_COLS`, `BALL_CELL`. Change one side alone
  and nothing raises: the sheet stays a valid image and the reader keeps slicing
  it, from the wrong cells. `SHADOW_K` and `landing()` in `js/animator.js` are
  the same hazard against three widths in `css/game.css`.
- **`tools/cutout.py` deliberately does not trim keeper poses.** A sprawling dive
  and an upright idle have different bounding boxes; trimming destroys the shared
  coordinate space that lets `.keeper` be a fixed box.
- **The flood key has a blind spot the poses find.** `grey_background` floods the
  backdrop in from the frame edge, which is what lets achromatic parts inside the
  figure survive — but a hand on a hip closes a triangle the flood cannot reach,
  and the sprite carries a mid-grey hole. Invisible against the grey render, a
  grey blob on the navy pitch. `enclosed_pockets` judges each unreachable region
  on tone. Check any pose where a limb closes a loop.
- **Say there is no ball in the pose prompts.** A diving goalkeeper holding one
  is what the model assumes, and `js/fx.js` draws the real ball on the canvas.
- **A container query does not change specificity.** `css/stage.css` loads before
  `css/game.css` and `css/footer.css`, so a bare class in its landscape block
  loses to the same class declared later — which is why `#stage .tagline` and
  `#stage .ftr` carry the id. The tagline half of that was broken since the port.
- **The header and the footer bracket the play area at `z-index: 46`.**
  Everything the game draws lives below it; the card at 50 covers both. Without
  it the plate painted over the footer and the confetti fell across it.
- **The Pages source must be GitHub Actions.** Left on a branch, the legacy
  builder succeeds and publishes the whole repository, bypassing the allowlist.
  Verify by fetching `tools/cutout.py` from the live site; it must 404.
- **Card width is `width: min(<px>, 100%)`.** The `width: <px>; max-width: 100%`
  form is a no-op on a grid item that declares its width.
- **`python -m http.server` sends no `Cache-Control`,** so Chrome caches
  stylesheets heuristically. A fix that "does not apply" is usually the old file
  still in the page; confirm against `document.styleSheets` before diagnosing.

## Verification

Serve locally on a deliberately chosen port — the reference project lost two
verification passes to an unrelated API already holding 8000:

```
python -m http.server 8099 --bind 127.0.0.1
```

Run and passing: the full sequence end to end; the page handed back afterwards
with the attempt counter at zero and the panels clickable; nothing scrolling in
any state or size; the goal box on the painted goal to 0.017px; the keeper's
feet 0.00px from the goal line and the figure at 77.04% of the goal's height;
each covering glove four points short of its panel centre and level with its
row; the card at 320px with no descendant crossing the sheet, and at desktop
taking its own 504px geometry; all three locales switching every visible string
and surviving a reload; zero requests to `googleapis` or `gstatic`, four of the
six woff2 on UA; the plate and the two preloaded subsets first and the dive
sprites after `domContentLoadedEventEnd`; a card that refuses to open leaving
the page playable and logging `the shot sequence failed`; a submit hook that
throws still showing the visitor their credentials and logging `the submit hook
failed`; the unfilled seams taking no focus and drawing no underline; and on
the live URL, `tools/`, `docs/`, `raw/` and `.gitignore` all 404.

## What is left

**The acceptance gate, and the only one that cannot be closed from a desk.**
iOS Safari and Android Chrome on the live URL: no rubber-band on vertical drag,
no page scroll with the soft keyboard open, landscape, a notched device for
`env(safe-area-inset-*)`, pinch zoom. The reference project never closed this
one.

**Windows High Contrast, for the same reason.** The headline has an explicit
`forced-colors` rule and the panels keep a real border, so the two things the
checklist names are handled. Two more are reasoned rather than observed: the
card's active tab is redrawn as a border there, since a colour-filled bar would
vanish, and the consent checkbox is an `appearance: none` control whose tick is
a background image — the usual hazard in that mode, and untested.

**One decision for the client.** A first visit honours the browser's language
before falling back to Ukrainian, which is the behaviour this file's `detect()`
already had. In the target market that lands on UA or RU either way; on an
English browser the page opens in English. Forcing UA regardless is two lines.

**Declared limitations, not defects.** There is no `favicon.ico`; it 404s in the
console, inherited. The English copy is written in-house and has not been read
by a native speaker. The Russian half of the card was **written, not
transcribed** — the design carries fourteen Registration Form variants and every
one of them is Ukrainian.
