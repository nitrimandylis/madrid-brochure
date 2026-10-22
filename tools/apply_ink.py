# /// script
# dependencies = ["pillow", "numpy", "scipy"]
# ///
# Lays Nick's extracted handwriting over the art, comic-lettering style:
# a paper-coloured halo so it reads on busy art, and closed shapes
# (speech bubbles, the cat's face) filled with paper.
# Usage: uv run tools/apply_ink.py   (reads art/ink/*.png, writes art/*-ink.png)
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

PAPER = (255, 250, 240)
INK = (0, 0, 0)
ART = Path("art")

# stroke weight per piece: >1 thickens, <1 thins, 1 keeps his line as written
WEIGHT = {"cover": 3, "panel1": -3, "panel2": 1}

# nudges: move every stroke lying fully inside (x0, y0, x1, y1) by (dx, dy) pixels
NUDGES = {
    "cover": [((252, 270, 475, 374), -30, 0)],  # "IB2!" further from the bubble's edge
}

# pixel moves, for strokes that touch something else (the "!" touches the bubble outline)
PIXEL_MOVES = {
    "cover": [((460, 328, 477, 346), -30, 0)],  # the "!" dot, which touches the outline
}


def move_pixels(mask, moves):
    arr = np.asarray(mask) > 0
    out = arr.copy()
    for (x0, y0, x1, y1), dx, dy in moves:
        block = arr[y0:y1, x0:x1].copy()
        out[y0:y1, x0:x1] = False
        out[y0 + dy:y1 + dy, x0 + dx:x1 + dx] |= block
    return Image.fromarray((out * 255).astype("uint8"))


def nudge(mask, moves):
    arr = np.asarray(mask) > 0
    labels, count = ndimage.label(arr, structure=np.ones((3, 3)))
    out = arr.copy()
    for (x0, y0, x1, y1), dx, dy in moves:
        for i, sl in enumerate(ndimage.find_objects(labels), start=1):
            ys, xs = sl
            if xs.start >= x0 and xs.stop <= x1 and ys.start >= y0 and ys.stop <= y1:
                piece = labels == i
                out[piece] = False
                out[np.roll(np.roll(piece, dy, axis=0), dx, axis=1)] = True
    return Image.fromarray((out * 255).astype("uint8"))


def weigh(mask, weight):
    if weight > 1:
        return mask.filter(ImageFilter.MaxFilter(weight))
    if weight < -1:
        return mask.filter(ImageFilter.MinFilter(-weight))
    return mask


for ink_file in sorted((ART / "ink").glob("*.png")):
    name = ink_file.stem
    art = Image.open(ART / f"{name}.png").convert("RGB")
    ink = Image.open(ink_file).convert("L").point(lambda v: 255 if v > 0 else 0)
    ink = nudge(ink, NUDGES.get(name, []))
    ink = move_pixels(ink, PIXEL_MOVES.get(name, []))
    line = weigh(ink, WEIGHT.get(name, 1))
    halo = line.filter(ImageFilter.MaxFilter(9))

    # inside of closed shapes: everything the outside cannot reach once small gaps are closed
    walls = ink.filter(ImageFilter.MaxFilter(9))
    flood = walls.copy()
    ImageDraw.floodfill(flood, (0, 0), 128)
    inside = np.asarray(flood) == 0
    fill = Image.fromarray((inside * 255).astype("uint8")).filter(ImageFilter.MaxFilter(9))

    out = art.copy()
    out.paste(Image.new("RGB", art.size, PAPER), mask=halo)
    out.paste(Image.new("RGB", art.size, PAPER), mask=fill)
    out.paste(Image.new("RGB", art.size, INK), mask=line)
    out.save(ART / f"{name}-ink.png")
    print("inked", name)
