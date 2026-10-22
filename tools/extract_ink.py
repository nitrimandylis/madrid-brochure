# /// script
# dependencies = ["pillow", "numpy", "pypdfium2"]
# ///
# Pulls Nick's handwriting out of a reMarkable export: anything that differs from the
# sheets we uploaded is his ink. Saves one transparent PNG per piece of art.
# Usage: uv run tools/extract_ink.py ORIGINAL.pdf EXPORT.pdf OUT_DIR
import sys
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

DPI = 300
MM = DPI / 25.4
NAMES = ["cover", "map", "panel1", "panel2", "panel3", "panel4", "panel5", "panel6"]


def render(doc, i):
    return np.asarray(doc[i].render(scale=DPI / 72).to_pil().convert("RGB"), dtype=int)


if __name__ == "__main__":
    orig, export, out = pdfium.PdfDocument(sys.argv[1]), pdfium.PdfDocument(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    pad = int(12 * MM)  # same margins as tools/sheets.py
    for i, name in enumerate(NAMES):
        a, b = render(orig, i), render(export, i)
        h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
        # his pen is black: keep dark pixels in the export where the original was not dark nearby
        dark_now = b[:h, :w].sum(axis=2) < 3 * 45
        orig_lum = Image.fromarray((a[:h, :w].sum(axis=2) // 3).astype("uint8")).filter(ImageFilter.MinFilter(9))
        light_before = np.asarray(orig_lum) > 60
        mask = Image.fromarray(((dark_now & light_before) * 255).astype("uint8")).filter(ImageFilter.MedianFilter(3))
        # crop to the art area (labels at the top are ours, not his)
        art = Image.open(Path("art") / f"{name}.png")
        box = (pad, 2 * pad, pad + art.width, 2 * pad + art.height)
        mask = mask.crop(box)
        count = int(np.asarray(mask).astype(bool).sum())
        if count < 200:
            print(name, "no ink")
            continue
        mask.save(out / f"{name}.png")
        print(name, count, "ink pixels")
