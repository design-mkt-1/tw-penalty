"""Turn the raw Nano Banana 2 renders into game-ready sprites.

Nano Banana 2, not Nano Banana Pro. Both exist and this file used to name the
wrong one, inherited from the reference project. Every render in raw/ -- the
plate and all six keeper poses -- came from the model whose catalog id is
`nano_banana_2` on Higgsfield and `imagen-nano-banana-2-flash` on Magnific;
`nano_banana_pro` / `imagen-nano-banana-2` is a different, slower model. Regenerating
a single pose on Pro would put it on a different render treatment from the nine
beside it, which is exactly the failure the shared canvas exists to prevent.


Each raw render sits on a flat background: mid-grey for the goalkeeper poses
and the ball, magenta for the goal. This script keys that background out,
drops isolated artefacts the model hallucinated (stray boots, stray balls),
trims to the subject, downscales and writes WebP.

Two different keying strategies, because the subjects differ:

* grey  — the background is achromatic and mid-bright, while the subject is
          either saturated (kit, gloves) or much brighter (white boots). The
          background predicate is flood-filled in from the frame edge, so
          achromatic parts *inside* the subject (black undershorts) survive.
* rgba  — the source already carries its alpha and only needs resizing.
          No Top Win pose uses this: all eight are generated onto flat grey in
          one session. It is kept for a source that arrives already keyed.

Usage:
    python tools/cutout.py

Input:  raw/_raw-*.png         (kept outside the served tree)
Output: assets/img/*.webp
"""

import os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'assets', 'img')
RAW = os.path.join(ROOT, 'raw')

QUALITY = {}

# Keeper poses are exported on the FULL uncropped canvas. Every raw render
# shares the same 3392x5056 frame and camera, so keeping the canvas keeps every
# pose in one coordinate space: swapping the sprite cannot make the character
# jump in size or position. Trimming each pose to its own bounding box would
# destroy that, because a sprawling low dive and an upright idle have wildly
# different bounding boxes.
#
# Holding one camera across eight generations was expected to need a
# normalisation pass between generation and keying -- measure the feet line and
# the figure height in each render, align them all onto a common canvas. It did
# not: passing the chosen idle back as the character reference held the camera
# on its own. Measured on the keyed renders, the feet line sits at .934, .935
# and .934 of the canvas for idle, cheer and beaten, and the figure spans .856
# and .858 of it for idle and cheer. That is inside a thousandth, so there is
# nothing for an alignment step to correct. Generate against the reference, and
# check these two numbers on every new pose rather than trusting the next one.
#
# name -> (source, key mode, keep-largest-blob, trim, target height, target width)
JOBS = {
    'keeper-idle':             ('_raw-keeper-idle.png',      'grey', True, False, 640, None),
    'keeper-ready':            ('_raw-ready.png',            'grey', True, False, 640, None),
    'keeper-jump_L1':          ('_raw-jump_L1.png',          'grey', True, False, 640, None),
    'keeper-jump_R2':          ('_raw-jump_R2.png',          'grey', True, False, 640, None),
    'keeper-jump_center':      ('_raw-jump_center.png',      'grey', True, False, 640, None),
    'keeper-jump_center_down': ('_raw-jump_center_down.png', 'grey', True, False, 640, None),
    'keeper-cheer':            ('_raw-cheer.png',            'grey', True, False, 640, None),
    'keeper-beaten':           ('_raw-beaten.png',           'grey', True, False, 640, None),
}

# The goal is no longer a sprite: it is painted into assets/img/pitch-spot.webp
# and campaign/main.css measures it. The ball is no longer keyed out of a render
# either -- tools/ball_sheet.py renders it and its rotation frames outright.

# Sprites produced by mirroring another sprite rather than by generation.
# The kit carries no asymmetric mark, so the flip is invisible.
MIRRORS = {
    'keeper-jump_L2': 'keeper-jump_R2',
    'keeper-jump_R1': 'keeper-jump_L1',
}


def border_ring(shape, width=6):
    ring = np.zeros(shape, bool)
    ring[:width, :] = ring[-width:, :] = True
    ring[:, :width] = ring[:, -width:] = True
    return ring


def grey_background(rgb):
    """Flood the achromatic backdrop in from the frame edge."""
    a = rgb.astype(np.int16)
    chroma = a.max(axis=2) - a.min(axis=2)
    luma = a.mean(axis=2)

    ring = border_ring(rgb.shape[:2])
    lo, hi = luma[ring].min(), luma[ring].max()
    chroma_limit = max(14, int(chroma[ring].max()) + 8)

    candidate = (chroma <= chroma_limit) & (luma >= lo - 24) & (luma <= hi + 24)

    # Pad with a guaranteed-true frame so a single seed reaches the whole edge.
    h, w = candidate.shape
    padded = np.zeros((h + 2, w + 2), np.uint8)
    padded[1:-1, 1:-1] = candidate * 255
    padded[0, :] = padded[-1, :] = padded[:, 0] = padded[:, -1] = 255

    # .copy() is required: an image wrapped straight around a numpy buffer is
    # read-only, and floodfill writes into it silently doing nothing.
    img = Image.fromarray(padded, 'L').copy()
    ImageDraw.floodfill(img, (0, 0), 128, thresh=0)
    filled = np.asarray(img)

    bg = filled[1:-1, 1:-1] == 128
    return bg | enclosed_pockets(candidate, bg, luma, luma[ring].mean())


def enclosed_pockets(candidate, edge_bg, luma, ring_luma):
    """Backdrop the edge flood cannot reach, because the subject encloses it.

    A hand on a hip closes a triangle between the arm and the body, and that
    triangle is backdrop with no path to the frame edge. The flood leaves it
    opaque, so the sprite carries a mid-grey hole through the figure -- 6.7% of
    `beaten` and 3.1% of `ready` before this existed, and grey rather than
    transparent is what it looks like on the navy pitch.

    The reference project never hit this: its poses with a hand on a hip came
    into raw/ already keyed and took the `rgba` path, so nothing here ever ran
    on them. Every Top Win pose goes through the flood, so all of them do.

    Judged per connected region and on tone, not on size or position, because
    the thing that must survive is the reason the flood exists at all:
    achromatic parts INSIDE the subject. Black undershorts and the shadowed
    side of a white boot are both far from the backdrop's own brightness, so
    their regions fail this test and stay; a pocket of the actual backdrop
    matches it within a few levels and goes. Comparing a whole region's mean
    rather than single pixels is what keeps a dark fold inside a grey region
    from dragging the region out with it.
    """
    todo = candidate & ~edge_bg
    out = np.zeros_like(todo)
    if not todo.any():
        return out

    arr = (todo * 255).astype(np.uint8)
    tag = 200
    while tag > 1:
        remaining = np.argwhere(arr == 255)
        if remaining.size == 0:
            break
        y, x = remaining[0]
        img = Image.fromarray(arr, 'L').copy()
        ImageDraw.floodfill(img, (int(x), int(y)), tag, thresh=0)
        arr = np.asarray(img).copy()
        region = arr == tag
        if abs(float(luma[region].mean()) - float(ring_luma)) <= 12:
            out |= region
        tag -= 1

    return out


def shrink(mask, size):
    """Erode a boolean mask by `size` pixels."""
    img = Image.fromarray((mask * 255).astype(np.uint8), 'L').copy()
    img = img.filter(ImageFilter.MinFilter(size * 2 + 1))
    return np.asarray(img) > 127


def largest_blob(fg):
    """Keep only the biggest connected run of foreground.

    The model occasionally leaves a spare boot or a spare ball floating in the
    frame; those are separate blobs and get dropped here.
    """
    arr = (fg * 255).astype(np.uint8)
    best_size, best_tag = 0, None
    tag = 200
    while tag > 1:
        remaining = np.argwhere(arr == 255)
        if remaining.size == 0:
            break
        y, x = remaining[0]
        img = Image.fromarray(arr, 'L').copy()
        ImageDraw.floodfill(img, (int(x), int(y)), tag, thresh=0)
        arr = np.asarray(img).copy()
        size = int((arr == tag).sum())
        if size > best_size:
            best_size, best_tag = size, tag
        tag -= 1
    if best_tag is None:
        return fg
    return arr == best_tag


def cut(name, source, mode, keep_largest, trim, height, width):
    src = Image.open(os.path.join(RAW, source))

    if mode == 'rgba':
        out = src.convert('RGBA')
        rgb = np.asarray(out)[..., :3]
        return finish(name, out, rgb, trim, height, width)

    rgb = np.asarray(src.convert('RGB'))
    bg = grey_background(rgb)

    fg = ~bg
    if keep_largest:
        # White boots are ringed by neutral pixels, and the flood eats through
        # that ring far enough to sever a boot from its sock — the boot then
        # looks like a stray artefact and gets dropped. Find the blob on a
        # slightly grown foreground so those bridges survive, then intersect
        # back with the tight mask to keep the edge crisp.
        loose = ~shrink(bg, 3)
        fg = largest_blob(loose) & fg

    alpha = Image.fromarray((fg * 255).astype(np.uint8), 'L')
    # A sub-pixel soften kills the stair-stepping the hard mask leaves behind.
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))

    out = Image.fromarray(rgb).convert('RGBA')
    out.putalpha(alpha)
    return finish(name, out, rgb, trim, height, width)


def finish(name, out, rgb, trim, height, width):
    box = out.getbbox()
    if trim:
        out = out.crop(box)

    if height:
        scale = height / out.height
        out = out.resize((max(1, round(out.width * scale)), height), Image.LANCZOS)
    elif width:
        scale = width / out.width
        out = out.resize((width, max(1, round(out.height * scale))), Image.LANCZOS)

    dst = os.path.join(IMG, name + '.webp')
    out.save(dst, 'WEBP', quality=QUALITY.get(name, 90), method=6)

    # Where the subject sits inside the exported canvas, as fractions. The CSS
    # uses this to size the keeper box so the character reads at the right
    # scale without hard-coding pixel offsets per pose.
    scale = out.height / rgb.shape[0]
    subject = tuple(round(v * scale) for v in box) if box else None
    return dst, out.size, float((np.asarray(out)[..., 3] > 8).mean()), subject


def main():
    made = {}
    for name, (source, mode, keep, trim, height, width) in JOBS.items():
        path = os.path.join(RAW, source)
        if not os.path.exists(path):
            print('skip (missing source):', name)
            continue
        dst, size, coverage, subject = cut(name, source, mode, keep, trim,
                                           height, width)
        made[name] = dst
        note = ''
        if subject and not trim:
            note = '  subject y %s-%s x %s-%s' % (subject[1], subject[3],
                                                  subject[0], subject[2])
        print('%-20s %sx%-5s opaque %4.1f%%  %5.0f KB%s'
              % (name, size[0], size[1], coverage * 100,
                 os.path.getsize(dst) / 1024, note))

    for name, base in MIRRORS.items():
        if base not in made:
            print('skip (missing base):', name)
            continue
        img = Image.open(made[base]).transpose(Image.FLIP_LEFT_RIGHT)
        dst = os.path.join(IMG, name + '.webp')
        img.save(dst, 'WEBP', quality=90, method=6)
        print('%-20s mirrored from %-18s %5.0f KB'
              % (name, base, os.path.getsize(dst) / 1024))

    # The pitch plate keeps its background; it only needs resizing. 1800 wide,
    # because the widest it is ever drawn is 3.9876 goal widths and the goal
    # caps at 560px -- 2233 CSS pixels, which 1800 covers acceptably for a dark
    # backdrop and covers outright on a phone. Anything larger is bytes nobody
    # sees. The goal is painted into this plate; campaign/main.css measures it.
    bg_path = os.path.join(RAW, '_raw-pitch-spot.png')
    if os.path.exists(bg_path):
        img = Image.open(bg_path).convert('RGB')
        scale = 1800 / img.width
        img = img.resize((1800, round(img.height * scale)), Image.LANCZOS)
        dst = os.path.join(IMG, 'pitch-spot.webp')
        img.save(dst, 'WEBP', quality=82, method=6)
        print('%-20s %sx%-5s %19s %5.0f KB'
              % ('pitch-spot', img.width, img.height, '', os.path.getsize(dst) / 1024))


if __name__ == '__main__':
    main()
