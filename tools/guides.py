# /// script
# dependencies = ["pillow", "numpy"]
# ///
# Turns reference images into light-blue line guides for inking on the reMarkable.
# Usage: uv run tools/guides.py SRC_DIR OUT_DIR
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BLUE = (95, 170, 230)  # "non-photo blue": easy to see, easy to strip later
DPI = 200
MM = DPI / 25.4

# slot name -> (width mm, height mm, label, area of the photo to use as fractions, blur)
SLOTS = {
    "cover": (134, 110, "Cover: the bear and the strawberry tree", (0, 0.12, 0.85, 0.95), 2.2),
    "panel1": (52, 52, "Panel 1, late 800s: the Moorish wall", (0.25, 0, 0.75, 1), 2.2),
    "panel2": (52, 52, "Panel 2, 1085: Alfonso VI", (0, 0, 1, 0.62), 2.0),
    "panel3": (52, 52, "Panel 3, 1561: Philip II", (0.1, 0, 0.9, 0.62), 2.0),
    "panel4": (52, 52, "Panel 4, 1600s: Cervantes", (0.05, 0.1, 0.95, 0.8), 2.0),
    "panel5": (52, 52, "Panel 5, 2 May 1808 (Goya)", (0.2, 0, 1, 1), 2.8),
    "panel6": (52, 52, "Panel 6, the Telefónica tower, shelled in the siege", (0, 0, 1, 0.66), 2.0),
}


def crop_to(img, w, h):
    """Centre-crop img to the w:h ratio."""
    target = w / h
    iw, ih = img.size
    if iw / ih > target:
        new_w = int(ih * target)
        left = (iw - new_w) // 2
        return img.crop((left, 0, left + new_w, ih))
    new_h = int(iw / target)
    top = (ih - new_h) // 2
    return img.crop((0, top, iw, top + new_h))


def line_art(img, sigma=1.6, k=1.6, tau=0.98, eps=-0.02):
    """XDoG edge drawing: returns a boolean array, True where a line goes."""
    gray = img.convert("L")
    a = np.asarray(gray.filter(ImageFilter.GaussianBlur(sigma)), dtype=float) / 255
    b = np.asarray(gray.filter(ImageFilter.GaussianBlur(sigma * k)), dtype=float) / 255
    return (a - tau * b) < eps


def guide(src, w_mm, h_mm, box, sigma):
    w, h = int(w_mm * MM), int(h_mm * MM)
    img = Image.open(src).convert("RGB")
    iw, ih = img.size
    img = img.crop((int(box[0] * iw), int(box[1] * ih), int(box[2] * iw), int(box[3] * ih)))
    if w_mm == 134:
        # cover: fit the whole statue, white margins are fine
        img.thumbnail((w, h), Image.LANCZOS)
        framed = Image.new("RGB", (w, h), "white")
        framed.paste(img, ((w - img.width) // 2, h - img.height))
        img = framed
    else:
        img = crop_to(img, w, h).resize((w, h), Image.LANCZOS)
    lines = line_art(img, sigma=sigma)
    # drop specks so only real outlines remain
    mask = Image.fromarray((lines * 255).astype("uint8")).filter(ImageFilter.MedianFilter(5))
    # light blue tone underneath, so dark shapes (bronze, black clothes) still show
    lum = np.asarray(img.convert("L"), dtype=float) / 255
    tone = np.where(lum < 0.3, 0.38, np.where(lum < 0.55, 0.16, 0.0))
    tone_mask = Image.fromarray((tone * 255).astype("uint8")).filter(ImageFilter.MedianFilter(7))
    out = Image.new("RGB", (w, h), "white")
    out.paste(Image.new("RGB", (w, h), BLUE), mask=tone_mask)
    out.paste(Image.new("RGB", (w, h), BLUE), mask=mask)
    return out


def page(art, label):
    """Put one guide on a page with a label and a frame, for the reMarkable."""
    pad = int(10 * MM)
    page_w = art.width + 2 * pad
    page_h = art.height + 3 * pad
    sheet = Image.new("RGB", (page_w, page_h), "white")
    sheet.paste(art, (pad, 2 * pad))
    d = ImageDraw.Draw(sheet)
    d.rectangle([pad - 2, 2 * pad - 2, pad + art.width + 2, 2 * pad + art.height + 2], outline=BLUE, width=3)
    font = ImageFont.load_default(size=int(4 * MM))
    d.text((pad, pad // 2), label, fill=BLUE, font=font)
    d.text((pad, pad // 2 + int(5 * MM)), "Ink over the lines you want to keep. Skip the rest.", fill=BLUE, font=font)
    return sheet


if __name__ == "__main__":
    src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for name, (w, h, label, box, sigma) in SLOTS.items():
        src = src_dir / f"{name}.jpg"
        if not src.exists():
            print("missing", src)
            continue
        art = guide(src, w, h, box, sigma)
        art.save(out_dir / f"{name}.png")
        pages.append(page(art, label))
    map_png = out_dir / "map.png"
    if map_png.exists():
        pages.insert(1, page(Image.open(map_png).convert("RGB"), "Map: trace the streets you need, keep the numbered circles"))
    pages[0].save(out_dir / "guides.pdf", save_all=True, append_images=pages[1:], resolution=DPI)
    print("wrote", len(pages), "guides to", out_dir)
