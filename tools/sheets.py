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
    "cover": "Cover: a speech bubble for the bear, or your name and the trip dates",
    "map": "Map: notes like 'churros here', 'metro Sol', arrows, street names",
    "panel1": "Panel 1: label the wall, add a sound effect",
    "panel2": "Panel 2: a bubble for Alfonso VI",
    "panel3": "Panel 3: a bubble for Philip II",
    "panel4": "Panel 4: a bubble for Cervantes",
    "panel5": "Panel 5: a sound effect, ¡BANG!",
    "panel6": "Panel 6: a caption or a punk scream",
}


def sheet(art, note):
    pad = int(12 * MM)
    page = Image.new("RGB", (art.width + 2 * pad, art.height + 3 * pad), "white")
    page.paste(art, (pad, 2 * pad))
    d = ImageDraw.Draw(page)
    font = ImageFont.load_default(size=int(4 * MM))
    d.text((pad, pad // 2), note, fill=(120, 120, 120), font=font)
    d.text((pad, pad // 2 + int(5.5 * MM)), "Black pen, write on top of the picture.", fill=(120, 120, 120), font=font)
    return page


if __name__ == "__main__":
    art_dir, out = Path(sys.argv[1]), sys.argv[2]
    pages = [sheet(Image.open(art_dir / f"{name}.png").convert("RGB"), note) for name, note in PAGES.items()]
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI)
    print("wrote", len(pages), "pages to", out)
