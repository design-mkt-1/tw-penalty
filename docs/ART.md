# The art, and how to make it again

`raw/` is not tracked. The reference project kept 22 MB of source renders in a
public repository, still downloadable long after the served copy was cleaned,
and this repo does not repeat that. What is kept instead is the recipe: the
model, the prompts, the job ids and the framing every render had to hit. The
art is reproducible from this file.

Everything here was generated through Higgsfield on **Nano Banana 2** — catalog
id `nano_banana_2`, which comes back on the job as the internal type
`nano_banana_flash` under the display name `Nano Banana 2`. Same model, two
names; do not read the second one as a downgrade. All renders are 4k.

`tools/cutout.py` turns the renders into sprites and `tools/ball_sheet.py`
paints the ball outright. Neither needs the network.

## The stadium plate

`assets/img/pitch-spot.webp` — job `2c0de6b7-1532-4ee5-9b03-0deb95117f29`,
aspect `3:2`, 5056x3392, resized to 1800 wide by `tools/cutout.py` from
`raw/_raw-pitch-spot.png`.

> Wide establishing photograph of an empty football stadium at night. The
> camera sits low on the turf, roughly one metre high, about thirty metres back
> from the goal, using a wide-angle lens. Perfectly square to the goal: both
> goalposts vertical and parallel, the crossbar exactly horizontal, no
> perspective tilt and no roll. Symmetrical, goal dead centre.
>
> FRAMING — this is a wide, distant view. The goal is SMALL in the frame: it
> sits in the upper middle and its width spans only about one quarter of the
> image, roughly the middle 25 percent, leaving a broad sweep of empty pitch to
> the left of it and to the right of it. A vast expanse of grass fills the
> entire lower two thirds of the picture and runs to the bottom edge. Do not
> crop in on the goal; keep it distant and small.
>
> CONTRAST — the white goal frame and its taut net must read as bright white
> against near-black darkness. Everything behind the goal and everything seen
> through the net is deep unlit navy, almost black. No bright band, no coloured
> hoarding, no advertising boards, no lit barrier, and no orange whatsoever
> behind the goal or level with the goal mouth. That whole horizontal zone
> stays dark.
>
> Orange light lives only high above the crossbar: four floodlight pylons over
> a black-navy grandstand silhouette, two tall at the outer edges and two
> shorter inboard, flaring warm orange through atmospheric haze.
>
> Foreground: crisp white markings. The penalty arc sweeps across the lower
> third, the six-yard box and penalty box lines run wide to the left and right
> of the goal, mown stripes recede toward it.
>
> Colour grade: deep midnight navy throughout, turf dark blue-green, high
> contrast, cinematic, moody.
>
> Completely empty: no players, no goalkeeper, no ball, no text, no lettering,
> no logos, no watermark.

Seven renders over three rounds, and the rounds were not spent on geometry.

**The framing target is one number, not three.** In a 3:2 frame, a goal
spanning a quarter of the width forces the height to 2.667 goal widths on its
own. Ask for the quarter and the rest follows; ask for three ratios and they
fight. This plate lands at 24.3%.

**Two rounds went on contrast.** The early renders put a lit orange hoarding
straight through the goal mouth — exactly where an orange goalkeeper stands.
Asking for "no advertising boards" did not remove it. Stating the requirement
as *brightness*, and naming the zone it applies to, did. That is the paragraph
headed CONTRAST above, and it is why the prompt says the same thing three ways.

The plate is the composition's ruler: `css/game.css` measures the goal in it
and hangs everything else off that one unit. A new plate invalidates those
numbers — see `docs/NEXT-SESSION.md` for how they are re-derived.

## The ball

Not generated. `tools/ball_sheet.py` paints `assets/img/ball.webp` and the
rotation sheet `assets/img/ball-spin.webp` from the palette, in Orange Fire and
Midnight Navy — six orange pentagons and six navy, white hexagons between them,
checked at render size against the navy pitch.

`FRAMES`, `COLS` and `SIZE` in that script are duplicated in `js/fx.js` as
`BALL_FRAMES`, `BALL_COLS`, `BALL_CELL`. Change one side alone and nothing
raises: the sheet stays a valid image and the reader keeps slicing it, from the
wrong cells.

## The goalkeeper

Eight generated poses on one canvas: `idle`, `ready`, `jump_L1`, `jump_R2`,
`jump_center`, `jump_center_down`, `cheer`, `beaten`. `jump_L2` and `jump_R1`
are horizontal flips of `jump_R2` and `jump_L1`, produced by the `MIRRORS`
table in `tools/cutout.py` — the kit carries no asymmetric mark, so the flip is
invisible. Ten sprites, eight generations.

`aspect_ratio` `2:3`, 3392x5056, on flat mid-grey.

### The method: generate the idle first, then reference it

`idle` is generated from text alone. Every other pose is generated with the
**chosen idle passed back as `image_references`**, and its prompt opens by
naming what must not change:

> Full-body photoreal 3D character render of the SAME male football goalkeeper
> as in the reference image — same face, same short dark hair, same
> clean-shaven athletic build, same kit, same rendering style and lighting.

This was expected to need a normalisation pass afterwards — measure the feet
line and figure height in each render, align them all onto a common canvas.
**It did not.** Measured on the keyed renders, the feet line sits at .934, .935
and .934 of the canvas across `idle`, `cheer` and `beaten`, and the figure
spans .856 and .858 of it for `idle` and `cheer`. That is inside a thousandth.
The reference image holds the camera by itself.

Check those two numbers on every new pose anyway. They are cheap to measure and
they are the thing that breaks silently: `css/game.css` sizes `.keeper` as one
fixed box for all ten sprites, so a pose rendered at a different scale does not
error, it just makes the character grow mid-dive.

### The blocks every pose shares

Appended verbatim to each pose prompt, after its own POSE and FRAMING
paragraphs:

> KIT: long-sleeved goalkeeper shirt and matching shorts in vivid bright
> orange. Deep navy blue trim only: navy cuffs at the wrists, a navy band
> around each sleeve, a navy collar and a navy waistband on the shorts. Orange
> socks with a navy band below the knee. Goalkeeper gloves in bright orange
> with white palms. Plain white football boots. No badges, no sponsor marks, no
> numbers, no lettering of any kind anywhere on the kit.
>
> CAMERA — identical to the reference image: straight-on, eye level, the same
> lens and the same distance, so the man is rendered at the same size as he is
> in the reference. No tilt, no low angle, no high angle, no perspective
> distortion.
>
> BACKGROUND: completely flat, uniform, featureless mid-grey. A single solid
> grey tone across the whole frame. No gradient, no vignette, no floor, no
> horizon line, no cast shadow on the background, no props, no scenery.
>
> Even, soft, neutral studio lighting on the figure from the front. Sharp focus
> throughout, high detail on the fabric and gloves. No text, no logos, no
> watermark.

The kit is orange with navy trim, not the navy kit the brandbook's banners
show. Those banners sit on a light background; this pitch is graded deep navy,
and a navy keeper on it disappears.

The mid-grey background is not a style choice. `cutout.grey_background` floods
the achromatic backdrop in from the frame edge and keeps every saturated or
bright pixel, so the orange kit, the navy trim and the white boots all survive
while grey inside the figure does not get eaten.

### idle

Job `30855b43-f151-47b5-bf35-946bc1e5be68`. Generated as one of two variants on
one prompt; the other, `bec616f2-1753-496f-bc76-ff820d63a3ae`, was not used.
This one is the character reference for everything below, so it is the one
render that cannot be replaced without regenerating the whole set.

Its own prompt carries no reference image, and its POSE and FRAMING read:

> Full-body photoreal 3D character render of a male football goalkeeper,
> standing upright and facing the camera dead on, in a neutral ready stance:
> feet planted a little wider than his shoulders, knees very slightly bent,
> both arms hanging down and held a little away from his body, palms forward,
> gloved hands open. Calm, focused expression. Short dark hair, clean-shaven,
> athletic build, around thirty years old.
>
> FRAMING — this is critical: the ENTIRE figure is inside the frame, head to
> toe, nothing cropped. He is centred horizontally. The top of his head sits a
> little below the top edge with a clear margin of empty background above it,
> and the soles of his boots sit a little above the bottom edge with a clear
> margin of empty background below them. He fills most of the frame height but
> touches neither edge.

That FRAMING paragraph is reused unchanged by every upright pose: `ready`,
`cheer` and `beaten`.

### jump_L1 — low dive, viewer's left

Job `f100c2a6-79c1-4e76-8327-71736dfe94a6`. Mirrored to `jump_R1`.

> POSE: a full-stretch LOW diving save to the viewer's LEFT. He is airborne and
> almost horizontal, low, as though skimming just above the grass. Both arms
> are stretched out straight towards the left edge of the frame, gloves
> together and reaching, head tucked behind the arms, chest still turned partly
> towards the camera, hips and legs trailing away to the right with the
> trailing leg extended straight. The whole body is one long horizontal line
> from the gloves on the left to the trailing boot on the right.
>
> FRAMING — this is critical: the ENTIRE diving figure is inside the frame,
> nothing cropped — the reaching gloves and the trailing boot are both well
> inside the left and right edges. The body lies across the MIDDLE of the frame
> and is centred, with a broad margin of empty grey background above him and
> below him. He is airborne with nothing underneath him.

L and R are the **viewer's**, matching the panel columns in
`js/animator.js`. Getting that backwards sends the keeper away from the ball on
every save.

### jump_center — high, down the middle

Job `7f236278-2640-4206-b26c-3fae3dd5d14a`.

> POSE: a save straight down the MIDDLE, high. He faces the camera dead on and
> leaps straight upwards, both arms stretched vertically above his head, gloves
> open and close together reaching for a ball above him, head between his upper
> arms, body extended and narrow, legs straight and together beneath him with
> the toes pointed, both feet just off the ground.
>
> FRAMING — this is critical: the ENTIRE figure is inside the frame, from the
> raised gloves at the top to the pointed toes at the bottom, nothing cropped.
> He is centred horizontally, with a clear margin of empty background above the
> gloves and below the boots. He fills most of the frame height but touches
> neither edge.

### cheer — saved it

Job `c23ffa13-c415-4fdd-ab2c-153591c967d6`. Upright FRAMING block.

> POSE: celebrating a save. He stands facing the camera, feet apart and
> planted, both arms bent and pulled down tight at his sides with the gloved
> hands clenched into fists, shoulders drawn up, chest out, head tilted back a
> little, mouth open in a roar of celebration. Every muscle tensed, a burst of
> triumph.

### beaten — conceded

Job `f4adf6c9-874d-4a32-b59b-04b09ce23c2e`. Upright FRAMING block.

> POSE: beaten, standing in the goal a moment after conceding. He faces the
> camera with his shoulders dropped and his head hanging down, chin towards his
> chest so the top of his head is towards the camera, both gloved hands resting
> on his hips with the elbows out, back slightly rounded, body slack and
> deflated. Dejected, still, defeated.

"Chin towards his chest so the top of his head is towards the camera" is too
strong: the render obeys it and hides the face entirely, which reads more like
a man looking at his boots than a beaten keeper. If this pose is regenerated,
ask for the head dropped and the eyes down while the face stays visible.

### Outstanding

Three poses are not settled, and none of them is a keying or a framing problem.

- **`ready`** and **`jump_R2`** were never generated: both submissions were
  refused with a daily generation limit on the account. `jump_R2` is worth two
  sprites, since `jump_L2` is its mirror.
- **`jump_center_down`** was generated — job
  `18aa9b00-e6b9-478d-b7f4-04d76ea19316` — and rejected. The prompt below asked
  for a two-knee smother in the lower half of the frame; the render came back
  as an upright one-knee kneel filling .770 of the canvas height against the
  .495 the composition wants, with the gloves apart rather than together. The
  pose is wrong, not mis-framed, so the fix is a regeneration and not a crop.

  > POSE: a LOW save straight down the MIDDLE. He has dropped onto both knees,
  > facing the camera, chest upright and shoulders square, and has brought both
  > gloved hands down together in front of his shins to smother a low ball,
  > palms forward and almost touching the ground. Head up, eyes forward,
  > elbows close to his body.
  >
  > FRAMING — this is critical: the ENTIRE kneeling figure is inside the frame,
  > nothing cropped. He is centred horizontally and sits in the LOWER HALF of
  > the frame: his knees and boots a little above the bottom edge, and a large
  > area of empty grey background above his head. Do not fill the frame with
  > him — he occupies roughly the bottom half of it.

  Worth saying plainly in the retry that he is **sitting back on both heels,
  low and compact**, and that the frame is mostly empty above him.

`ready` and `jump_R2` still need their prompts written; the pose descriptions
that were submitted are in the session that generated the rest.

## The framing the sprites have to hit

Not a target to design against so much as a shape to check against. Measured
off the reference project's sprites, as fractions of the shared canvas — where
each figure's bounding box sits, and how tall it is:

| pose | x0 | y0 | x1 | y1 | height |
|---|---|---|---|---|---|
| idle | .110 | .125 | .900 | .928 | .803 |
| ready | .131 | .125 | .872 | .928 | .803 |
| jump_L1 | .063 | .308 | .944 | .728 | .420 |
| jump_R2 | .100 | .050 | .944 | .880 | .830 |
| jump_center | .303 | .064 | .704 | .908 | .844 |
| jump_center_down | .175 | .422 | .841 | .917 | .495 |
| cheer | .147 | .117 | .872 | .928 | .811 |
| beaten | .214 | .158 | .776 | .933 | .775 |

The Top Win figure is deliberately bigger in its canvas — .856 against .803 —
which is why the keeper box in `css/game.css` is re-derived rather than
inherited. The dives are the rows to read carefully: a dive sprite carries the
body angle only, and the travel across the goal is a CSS translation, so the
figure sits near the centre of its own canvas and does not lean out of it.
