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
| 3. Artwork | ball and stadium plate done; **goalkeeper outstanding** |
| 4. Re-measurement | plate geometry done; **keeper box and dive offsets outstanding** |
| 5. Registration card | not started |
| 6. i18n | not started |
| 7. Footer | not started |
| 8. Deploy | done and verified live |
| 9. Handoff | this file |

**The one gap.** `assets/img/keeper-*.webp` is still ignored in `.gitignore` and
the ten sprites 404 on the live page. Everything else — the plate, the ball, the
type, the tokens, the deploy chain — is in place and working.

## What was measured, and why those numbers

Nothing in the geometry is tuned by eye. Each number is a measurement divided by
one unit, and the comments in `css/game.css` carry the raw pixels so the chain
can be re-derived rather than trusted.

**The plate.** In `assets/img/pitch-spot.webp` (1800×1208) the posts stand at
x 681 and 1118, the crossbar's top edge at y 523, the goal line at y 681 — a goal
of 437 × 158 image pixels. Every ratio at `.pitch::before` is one of those
measurements over 437: 4.1190 wide, 2.7643 tall, crossbar 1.1968 below the top.

The framing target was a single number, not three. In a 3:2 frame, a goal
spanning a quarter of the width forces the height to 2.667 goal widths on its
own — which is where the reference page's 2.66 came from. This plate lands at
24.3%, giving 2.76 against the 2.49 the worst case (430×932) needs, so unlike
the reference it needed no synthetic bottom extension.

**The measuring script matters more than the numbers.** It was validated against
the reference plate, whose values were already known, and it earned that: its
first version put the crossbar 350px too high, because it measured the span
between a row's outermost bright pixels — and a row crossing two floodlights
spans the frame while being two small blobs. Floodlights are brighter than the
goal. A crossbar is a contiguous run, and measuring one matches all four known
values to within half a percent. Re-measure with a run, never a span.

**Still to derive** (stage 4): the keeper box in `css/game.css` and the dive
offsets in `js/animator.js`. Both follow from the new `idle` sprite, whose figure
spans **0.855** of its canvas where the reference spanned .809. The box is
figure-fraction × (1.88 m keeper / 2.44 m goal) for height, canvas aspect for
width, feet position for the drop below the goal line — all three move together.
`POSES` are percentages of the keeper's own box, so they only hold while the box
keeps its proportion to the goal; the comment there records them breaking exactly
this way once before. `WRONG_WAY` stays derived from the panel grid — the hand
table it replaced sent the keeper onto the ball.

## Decisions, with their reasons

**One typeface, Roboto, everywhere.** The brandbook prescribes Russo One for
headlines, but no delivered screen uses it — it appears only on the brandbook's
own pages. The card's headline is Roboto Condensed Black Italic (`wdth 75`,
weight 900), so the "Russo One has no cursive" worry never applied. The card and
footer UI text is drawn in Inter, which is deliberately not followed: the
brandbook says Roboto. This was confirmed as a real design choice and not a
missing-font substitution — the typography page renders `Russo_One:Regular` and
`Roboto:Regular` correctly in the same file.

The inherited Roboto files carried `wght` only. They were replaced with the
variable build carrying `wght 100–900` **and** `wdth 75–100`, plus a real italic
cut: six woff2, three subsets by two styles. Condensed is a coordinate on the
family, not a second download, and `--font-stretch-tight` names it.

**Contrast decides the colours, not fidelity.** The pitch is graded deep navy, so
anything navy on it disappears. The ball's twelve pentagons are six Orange Fire
and six Midnight Navy — checked at render size, where the white hexagons frame
the navy ones and they read as panels. The keeper's kit is orange with navy trim
rather than the navy kit the brandbook banners show, because those banners sit on
a light background and this one does not. Two rounds of plate renders were spent
on the same problem: a lit orange hoarding kept appearing straight through the
goal mouth, where an orange keeper stands. Asking for "no advertising boards" did
not remove it; stating the requirement as brightness did.

**The brandbook contradicts itself twice**, and `css/tokens.css` says so rather
than silently picking. `BG SECONDARY` lists a hex that is a stray copy of the
orange next to an RGB triple that is correct. `BG THIRD` is two different colours
on consecutive pages; both are kept under names that say which is which.

**Ramps are derived, not invented.** Each 500 is the brandbook value verbatim;
every other step is that value mixed with white or black on a schedule written in
the file. The reference project ended up with three different greens in three
stylesheets, all meant to be one colour.

**Generated art is kept out of git; recipes are kept in.** `tools/ball_sheet.py`
renders the ball and writes straight to `assets/img/` — it used to emit
differently-named files into the working directory, leaving a rename step
recorded nowhere, which is not a reproducible recipe. `tools/cutout.py` turns raw
renders into sprites. `docs/ART.md` will carry the prompts and job ids. The
reference repo left 22 MB of source renders tracked in a public repo, still
downloadable long after the served copy was cleaned.

## Traps already paid for

- **`FRAMES`, `COLS` and `SIZE` in `tools/ball_sheet.py` are duplicated in
  `js/fx.js`** as `BALL_FRAMES`, `BALL_COLS`, `BALL_CELL`. Change one side alone
  and nothing raises: the sheet stays a valid image and the reader keeps slicing
  it, from the wrong cells.
- **`tools/cutout.py` deliberately does not trim keeper poses.** A sprawling dive
  and an upright idle have different bounding boxes; trimming destroys the shared
  coordinate space that lets `.keeper` be a fixed box. Generative framing drifts,
  so raw renders must be aligned onto one canvas before keying.
- **The Pages source must be GitHub Actions.** Left on a branch, the legacy
  builder does not merely race the workflow — it succeeds and publishes the whole
  repository, bypassing the allowlist entirely. That happened here: `tools/` and
  `.gitignore` served 200 on the public URL until the source was switched. Verify
  by fetching `tools/cutout.py` from the live site; it must 404.
- **Card width is `width: min(<px>, 100%)`.** The `width: <px>; max-width: 100%`
  form is a no-op on a grid item that declares its width, and left 57px of card
  off-screen at 320px on a page that cannot scroll to reach it.

## What is next

**Stage 3 — the goalkeeper.** Eight poses (`idle`, `ready`, `jump_L1`,
`jump_R2`, `jump_center`, `jump_center_down`, `cheer`, `beaten`), not ten:
`MIRRORS` in `tools/cutout.py` derives `jump_L2` and `jump_R1` by flipping, and
the kit carries no asymmetric mark. Generate `idle` first and use it as the
character reference so face, kit and camera hold. Renders go on a flat mid-grey
background — `cutout.grey_background` floods the achromatic backdrop in from the
frame edge and keeps saturated or bright subject pixels, which the orange kit,
navy trim and white boots all satisfy; this is already proven on the chosen
`idle`. Align the framing, add the `JOBS` entries, run the script, then delete
the placeholder block from `.gitignore` and write `docs/ART.md`.

**Stage 4 — the keeper box and dive offsets.** See the measurement section above.

**Stage 5 — the registration card.** Rewrite `css/form.css`, the card markup in
`index.html`, and the field and validation logic in `js/form.js`. Keep form.js's
machinery: the focus trap (`focusables`, `onKeydown`), `background`,
`open`/`close`/`restore`, and the two-step error fade (`clearError`/`showError`
with `ERR_OUT`, which unhides a frame before adding the class so a chunk of card
does not appear at once). The card is a white-themed dialog with a promo header,
email/phone tabs, a password field with an eye toggle, an 18+ checkbox checked by
default with two links, and a coloured CTA — no bonus select, so `#tw-bonus` goes.
Both breakpoints come from their own Figma nodes, not scaled from one another.

Figma file `mAJyDSaXdr9GO72b7FGvI8`, page `19:2893`:

| screen | desktop | mobile |
|---|---|---|
| default | `19:4677` | `19:4559` |
| error | `19:4713` | `19:4598` |
| success | `19:4755` | `19:4637` |
| registration complete | `19:4796` | `19:4829` |
| footer | `19:3624` | `19:3717` |

**Stage 6 — i18n.** Rewrite the content of `js/i18n.js`, not its machinery:
`LANGS`, `FALLBACK`, `ENDONYM` and `STRINGS` change; the language selector is
language-agnostic and stays. Retire the inherited `uz` locale, `flag-uz.svg`, its
line in `assets/img/icons/FLAGS-LICENSE.txt`, and its two `index.html` references
together — the file was kept deliberately, since deleting it before the markup
would only have made a 404. Flip the font preload in `<head>` to the cyrillic
subset; that line follows the default language.

**Stage 7 — footer.** A fixed row at the bottom of the stage, inside the
zero-scroll rule: only `.pitch` is elastic, so it absorbs the difference. Tokens
`--footer-bg`, `--footer-fg` and `--footer-brd` already exist.

## Verification

The gates that catch this work, beyond the usual flow check:

1. The six panels sit between the painted posts and the keeper's feet stand on
   the painted line, at every viewport size.
2. All ten sprites are the same person in the same place — no jump in size or
   position, mirrors included.
3. Each covering glove lands just short of its panel centre; a wrong guess sends
   the keeper away from the ball.
4. From 320×568 to 1920×1200 plus landscape, the ball lands on the panel centre.
5. Nothing scrolls in any state, including with the footer present and the soft
   keyboard open: `scrollHeight === clientHeight`.
6. No descendant of `.card` exceeds `.sheet` at 320px.
7. Zero `fonts.googleapis` or `gstatic` entries in resource timing.
8. On the live URL, `tools/`, `docs/`, `raw/` and `.gitignore` all 404.
9. **The acceptance gate, and the only one that cannot be closed from a desk:**
   iOS Safari and Android Chrome on the live URL — no rubber-band on vertical
   drag, no page scroll with the soft keyboard open, landscape, a notched device
   for `env(safe-area-inset-*)`, pinch zoom.

Serve locally with a deliberately chosen port; the reference project lost two
verification passes to an unrelated API already holding 8000:

```
python -m http.server 8099 --bind 127.0.0.1
```

## Known limitations

- The goalkeeper sprites are absent, so the live page has no keeper.
- There is no `favicon.ico`; it 404s in the console. Inherited — the reference
  page had none either.
- English copy is written in-house and has not been reviewed by a native speaker.
  Ukrainian and Russian are transcribed from the design.
