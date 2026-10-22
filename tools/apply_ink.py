# /// script
# dependencies = ["pillow", "numpy"]
# ///
# Lays Nick's extracted handwriting over the art, comic-lettering style:
# slightly bolder ink, a paper-coloured halo so it reads on busy art, and closed shapes
# (speech bubbles, the cat's face) filled with paper.
# Usage: uv run tools/apply_ink.py   (reads art/ink/*.png, writes art/*-ink.png)
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PAPER = (255, 250, 240)
INK = (0, 0, 0)
ART = Path("art")

for ink_file in sorted((ART / "ink").glob("*.png")):
    name = ink_file.stem
    art = Image.open(ART / f"{name}.png").convert("RGB")
    ink = Image.open(ink_file).convert("L").point(lambda v: 255 if v > 0 else 0)
    bold = ink.filter(ImageFilter.MaxFilter(3))
    halo = bold.filter(ImageFilter.MaxFilter(13))

    # inside of closed shapes: everything the outside cannot reach once small gaps are closed
    walls = bold.filter(ImageFilter.MaxFilter(9))
    flood = walls.copy()
    ImageDraw.floodfill(flood, (0, 0), 128)
    inside = np.asarray(flood) == 0
    fill = Image.fromarray((inside * 255).astype("uint8")).filter(ImageFilter.MaxFilter(9))

    out = art.copy()
    out.paste(Image.new("RGB", art.size, PAPER), mask=halo)
    out.paste(Image.new("RGB", art.size, PAPER), mask=fill)
    out.paste(Image.new("RGB", art.size, INK), mask=bold)
    out.save(ART / f"{name}-ink.png")
    print("inked", name)
