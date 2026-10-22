# /// script
# dependencies = ["pillow", "numpy", "pypdfium2"]
# ///
# The cover's speech bubble: drawn here, lettered by Nick on the reMarkable.
#   uv run tools/bubble.py sheet OUT.pdf          three empty bubbles to write in
#   uv run tools/bubble.py apply EXPORT.pdf N     his lettering from bubble N (1-3) onto the cover
import sys

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DPI = 300
MM = DPI / 25.4
PAPER = (255, 250, 240)
INK = (0, 0, 0)

# bubble on the cover, in cover.png pixels: the oval, and the tail pointing at the bear's head
OVAL = (40, 90, 470, 370)
TAIL = [(330, 340), (400, 320), (420, 470)]
# area of the cover shown on the sheet around each bubble
CROP = (0, 30, 640, 530)
# where the three crops sit on the A4 sheet
A4 = (int(210 * MM), int(297 * MM))
SLOTS = [(int(20 * MM), int((30 + 85 * i) * MM)) for i in range(3)]


def draw_bubble(img):
    # one shape (oval + tail), outlined as a whole so the tail joins with no line across it
    shape = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(shape)
    d.ellipse(OVAL, fill=255)
    d.polygon(TAIL, fill=255)
    outline = shape.filter(ImageFilter.MaxFilter(9))
    img.paste(Image.new("RGB", img.size, INK), mask=outline)
    img.paste(Image.new("RGB", img.size, PAPER), mask=shape)
    return img


def make_sheet():
    cover = draw_bubble(Image.open("art/cover.png").convert("RGB")).crop(CROP)
    page = Image.new("RGB", A4, "white")
    d = ImageDraw.Draw(page)
    font = ImageFont.load_default(size=int(4 * MM))
    d.text((SLOTS[0][0], int(12 * MM)), "Write '¡Hola IB2!' in each bubble. Black pen, best one wins.", fill=(140, 140, 140), font=font)
    for x, y in SLOTS:
        page.paste(cover, (x, y))
    return page


def apply(export, n):
    original = np.asarray(make_sheet(), dtype=int)
    doc = pdfium.PdfDocument(export)
    written = np.asarray(doc[0].render(scale=DPI / 72).to_pil().convert("RGB"), dtype=int)
    h, w = min(original.shape[0], written.shape[0]), min(original.shape[1], written.shape[1])
    # his pen: dark now, where the sheet was not dark
    dark_now = written[:h, :w].sum(axis=2) < 3 * 45
    before = Image.fromarray((original[:h, :w].sum(axis=2) // 3).astype("uint8")).filter(ImageFilter.MinFilter(9))
    ink = Image.fromarray(((dark_now & (np.asarray(before) > 60)) * 255).astype("uint8")).filter(ImageFilter.MedianFilter(3))
    x, y = SLOTS[n - 1]
    letters = ink.crop((x, y, x + CROP[2] - CROP[0], y + CROP[3] - CROP[1]))
    # keep only strokes inside the oval, so stray marks outside it are dropped
    inside = Image.new("L", letters.size, 0)
    ox0, oy0, ox1, oy1 = OVAL
    ImageDraw.Draw(inside).ellipse((ox0 - CROP[0] + 10, oy0 - CROP[1] + 10, ox1 - CROP[0] - 10, oy1 - CROP[1] - 10), fill=255)
    letters = Image.fromarray(np.minimum(np.asarray(letters), np.asarray(inside)))
    letters = letters.filter(ImageFilter.MaxFilter(3))  # a touch bolder so it holds up in print
    cover = draw_bubble(Image.open("art/cover.png").convert("RGB"))
    full = Image.new("L", cover.size, 0)
    full.paste(letters, (CROP[0], CROP[1]))
    cover.paste(Image.new("RGB", cover.size, INK), mask=full)
    cover.save("art/cover-ink.png")
    print("cover lettered from bubble", n)


if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        make_sheet().save(sys.argv[2], resolution=DPI)
        print("wrote", sys.argv[2])
    else:
        apply(sys.argv[2], int(sys.argv[3]))
