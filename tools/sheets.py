# /// script
# dependencies = ["pillow"]
# ///
# Puts each piece of art on its own page, at print size, for handwriting on the reMarkable.
# Usage: uv run tools/sheets.py ART_DIR OUT.pdf
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DPI = 300
MM = DPI / 25.4

# art file -> what to add by hand
PAGES = {
    "cover": "Cover",
    "map": "Map (the notes are generated in your handwriting)",
    "panel1": "Panel 1, late 800s",
    "panel2": "Panel 2, 1085",
    "panel3": "Panel 3, 1561",
    "panel4": "Panel 4, Golden Age",
    "panel5": "Panel 5, 2 May 1808",
    "panel6": "Panel 6, 1936 to the 1980s",
}


def sheet(art, note):
    pad = int(12 * MM)
    page = Image.new("RGB", (art.width + 2 * pad, art.height + 3 * pad), "white")
    page.paste(art, (pad, 2 * pad))
    d = ImageDraw.Draw(page)
    font = ImageFont.load_default(size=int(4 * MM))
    d.text((pad, pad // 2), note, fill=(120, 120, 120), font=font)
    d.text((pad, pad // 2 + int(5.5 * MM)), "Review and polish: add, fix or redo anything. Black pen.", fill=(120, 120, 120), font=font)
    return page


if __name__ == "__main__":
    art_dir, out = Path(sys.argv[1]), sys.argv[2]
    pages = []
    for name, note in PAGES.items():
        # use the version that already carries handwriting, when there is one
        inked = [art_dir / f"{name}-ink.png", art_dir / f"{name}-notes.png"]
        src = next((f for f in inked if f.exists()), art_dir / f"{name}.png")
        pages.append(sheet(Image.open(src).convert("RGB"), note))
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI)
    print("wrote", len(pages), "pages to", out)
