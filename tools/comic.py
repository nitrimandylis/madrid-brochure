# /// script
# dependencies = ["pillow", "numpy"]
# ///
# Turns the cover photo into tebeo-style art:
# flat colours from the brochure palette, black ink outlines, halftone dots in the shadows.
# Usage: uv run tools/comic.py SRC_DIR OUT_DIR
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

DPI = 300
MM = DPI / 25.4

# Flat colours a tebeo colourist would use: brochure palette plus skin and stone
PALETTE = [
    (0, 0, 0),         # ink
    (255, 250, 240),   # paper
    (176, 16, 46),     # crimson
    (255, 199, 44),    # sol
    (20, 80, 160),     # metro
    (169, 196, 234),   # sky
    (240, 196, 160),   # skin
    (196, 160, 112),   # stone
]

# slot -> (width mm, height mm, area of the source to use as fractions, line blur)
SLOTS = {
    "cover": (134, 132, (0, 0, 1, 1), 2.4),
}


def fit(img, w, h, box, contain):
    iw, ih = img.size
    img = img.crop((int(box[0] * iw), int(box[1] * ih), int(box[2] * iw), int(box[3] * ih)))
    if contain:
        img.thumbnail((w, h), Image.LANCZOS)
        framed = Image.new("RGB", (w, h), PALETTE[5])
        framed.paste(img, ((w - img.width) // 2, h - img.height))
        return framed
    target = w / h
    iw, ih = img.size
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / target)
        img = img.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    return img.resize((w, h), Image.LANCZOS)


def flat_colours(img):
    """Snap every pixel to the nearest palette colour, then smooth into flat areas."""
    pal = Image.new("P", (1, 1))
    flat = sum(PALETTE, ()) + (0, 0, 0) * (256 - len(PALETTE))
    pal.putpalette(flat)
    punchy = ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(1.3)).enhance(1.25)
    smooth = punchy.filter(ImageFilter.MedianFilter(13))
    return smooth.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB").filter(ImageFilter.ModeFilter(9))


def ink_lines(img, sigma):
    gray = img.convert("L")
    a = np.asarray(gray.filter(ImageFilter.GaussianBlur(sigma)), dtype=float) / 255
    b = np.asarray(gray.filter(ImageFilter.GaussianBlur(sigma * 1.6)), dtype=float) / 255
    lines = ((a - 0.98 * b) < -0.02).astype("uint8") * 255
    return Image.fromarray(lines).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MaxFilter(3))


def halftone(img, shadow):
    """Ben-Day dots over the darker mid-tones."""
    w, h = img.size
    step = int(1.2 * MM)
    yy, xx = np.mgrid[0:h, 0:w]
    dots = ((xx % step - step / 2) ** 2 + (yy % step - step / 2) ** 2) < (step * 0.3) ** 2
    lum = np.asarray(shadow.convert("L"), dtype=float) / 255
    mask = dots & (lum > 0.3) & (lum < 0.45)
    arr = np.asarray(img).copy()
    arr[mask] = (arr[mask] * 0.7).astype("uint8")
    return Image.fromarray(arr)


def comic(src, w_mm, h_mm, box, sigma):
    w, h = int(w_mm * MM), int(h_mm * MM)
    img = fit(Image.open(src).convert("RGB"), w, h, box, contain=False)
    out = halftone(flat_colours(img), img)
    out.paste(Image.new("RGB", (w, h), PALETTE[0]), mask=ink_lines(img, sigma * 1.5))
    return out


if __name__ == "__main__":
    src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (w, h, box, sigma) in SLOTS.items():
        comic(src_dir / f"{name}.jpg", w, h, box, sigma).save(out_dir / f"{name}.png")
        print("drew", name)
