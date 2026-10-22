# /// script
# dependencies = ["pillow"]
# ///
# Writes notes onto the map in Nick's handwriting, using the rm-handwrite stroke library.
# Usage: uv run tools/handnotes.py art/map.png art/map-notes.png
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path.home() / ".claude/skills/rm-handwrite/scripts"))
import hw  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from map import SPOTS, xy, MM  # noqa: E402

INK = (25, 25, 25, 255)
HALO = (255, 250, 240, 255)
X_HEIGHT_MM = 2.7  # how tall his small letters end up on the printed map
PEN_MM = 0.55      # ink width

# (text, top-left of the note in mm, rotation, what its leader line points at or None)
NOTES = [
    ("Km 0 here", (66, 58), 0, None),
    ("churros!", (44, 17), 0, (40.4170, -3.7069)),
    ("FREE Thu 16-18", (3, 76), 0, 3),
    ("sunset", (2, 39), 0, None),
    ("17:50", (5, 45), 0, None),
    ("GRAN VIA", (72, 40), 10, None),
    ("free 18-20", (76, 84), 0, None),
    ("boats!", (108, 74), 0, None),
    ("SUNDAY 9-15 only", (24, 110), 0, None),
]


def written(text):
    """Lay out one line of his handwriting and draw it on a transparent image."""
    box = hw.layout(hw.parse(text))
    strokes = []
    hw.place(box, 0.0, 0.0, True, 0, strokes, left=0.0)
    pts = [(p[0], p[1]) for st, _ in strokes for p in st]
    x0 = min(p[0] for p in pts) - 6
    y0 = min(p[1] for p in pts) - 6
    x1 = max(p[0] for p in pts) + 6
    y1 = max(p[1] for p in pts) + 6
    scale = X_HEIGHT_MM * MM / hw.XH
    img = Image.new("RGBA", (int((x1 - x0) * scale), int((y1 - y0) * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pen = int(PEN_MM * MM)
    for width, colour in ((pen * 3, HALO), (pen, INK)):
        for st, _ in strokes:
            line = [((p[0] - x0) * scale, (p[1] - y0) * scale) for p in st]
            if len(line) > 1:
                d.line(line, fill=colour, width=width, joint="curve")
    return img


def leader(d, start, end):
    """A slightly wobbly hand-drawn line from a note to its spot."""
    pen = int(PEN_MM * MM)
    steps = 12
    pts = []
    for i in range(steps + 1):
        t = i / steps
        wob = hw.rng.uniform(-0.15, 0.15) * MM if 0 < i < steps else 0
        pts.append((start[0] + (end[0] - start[0]) * t + wob, start[1] + (end[1] - start[1]) * t + wob))
    d.line(pts, fill=HALO, width=pen * 3, joint="curve")
    d.line(pts, fill=INK, width=pen, joint="curve")


def main(src, out):
    hw.SNAP = False
    page = Image.open(src).convert("RGBA")
    d = ImageDraw.Draw(page)
    for text, (mx, my), angle, target in NOTES:
        note = written(text)
        if angle:
            note = note.rotate(angle, expand=True, resample=Image.BICUBIC)
        x, y = int(mx * MM), int(my * MM)
        if target is not None:
            lat, lon = SPOTS[target] if isinstance(target, int) else target
            tx, ty = xy(lat, lon)
            r = 4.2 * MM if isinstance(target, int) else 0.6 * MM   # stop at the circle's edge
            sx, sy = x + note.width / 2, (y + note.height + 0.5 * MM) if ty > y else (y - 0.5 * MM)
            length = ((tx - sx) ** 2 + (ty - sy) ** 2) ** 0.5
            leader(d, (sx, sy), (tx - (tx - sx) * r / length, ty - (ty - sy) * r / length))
            if not isinstance(target, int):
                d.ellipse([tx - 0.8 * MM, ty - 0.8 * MM, tx + 0.8 * MM, ty + 0.8 * MM], fill=INK)
        page.alpha_composite(note, (x, y))
    page.convert("RGB").save(out)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
