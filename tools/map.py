# /// script
# dependencies = ["pillow"]
# ///
# Draws the comic-style map of central Madrid from OpenStreetMap data.
# Map data © OpenStreetMap contributors (ODbL).
# Usage: uv run tools/map.py OUT.png
import json, math, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

from pathlib import Path

INK = (0, 0, 0)
PAPER = (255, 250, 240)
PARK = (160, 200, 130)
RIVER = (20, 80, 160)
CRIMSON = (176, 16, 46)
BOWLBY = str(Path(__file__).parent / "fonts" / "BowlbyOne-Regular.ttf")
DPI = 300
MM = DPI / 25.4
W, H = int(134 * MM), int(128 * MM)
SOUTH, NORTH, WEST, EAST = 40.4012, 40.4318, -3.7220, -3.6800

SPOTS = {
    1: (40.4169, -3.7035),  # Puerta del Sol
    2: (40.4155, -3.7074),  # Plaza Mayor
    3: (40.4180, -3.7143),  # Palacio Real
    4: (40.4240, -3.7177),  # Templo de Debod
    5: (40.4203, -3.7020),  # Gran Vía
    6: (40.4138, -3.6921),  # Prado
    7: (40.4153, -3.6845),  # Retiro lake
    8: (40.4087, -3.7076),  # El Rastro
}

QUERY = f"""
[out:json][timeout:60];
(
  way["highway"~"^(trunk|primary|secondary|tertiary|pedestrian)$"]({SOUTH},{WEST},{NORTH},{EAST});
  way["leisure"="park"]({SOUTH},{WEST},{NORTH},{EAST});
  rel["leisure"="park"]({SOUTH},{WEST},{NORTH},{EAST});
  way["waterway"="river"]({SOUTH},{WEST},{NORTH},{EAST});
);
out geom;
"""


def xy(lat, lon):
    x = (lon - WEST) / (EAST - WEST) * W
    y = (NORTH - lat) / (NORTH - SOUTH) * H
    return x, y


def main(out):
    # cache the download so redraws don't hit Overpass again
    cache = Path(__file__).parent / "osm-cache.json"
    mirrors = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
    for url in mirrors:
        if cache.exists():
            break
        req = urllib.request.Request(
            url,
            data=urllib.parse.urlencode({"data": QUERY}).encode(),
            headers={"User-Agent": "madrid-brochure/0.1 (student brochure project)"},
        )
        try:
            cache.write_bytes(urllib.request.urlopen(req, timeout=90).read())
        except OSError as e:
            print("Overpass mirror failed:", url, e)
    ways = json.loads(cache.read_text())["elements"]
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # parks as flat green with a black outline (big parks like the Retiro are relations)
    for way in ways:
        if way.get("tags", {}).get("leisure") != "park":
            continue
        if "geometry" in way:
            outlines = [way["geometry"]]
        else:
            outlines = [m["geometry"] for m in way.get("members", []) if m.get("role") == "outer" and "geometry" in m]
        for outline in outlines:
            pts = [xy(p["lat"], p["lon"]) for p in outline]
            if len(pts) > 2:
                d.polygon(pts, fill=PARK, outline=INK, width=3)
    # streets the cartoon way: a black line, then a thinner white line on top
    roads = []
    for way in ways:
        tags = way.get("tags", {})
        if way["type"] != "way" or "geometry" not in way or tags.get("leisure") == "park":
            continue
        pts = [xy(p["lat"], p["lon"]) for p in way["geometry"]]
        if tags.get("area") == "yes":
            continue
        if tags.get("waterway"):
            d.line(pts, fill=RIVER, width=22, joint="curve")
            continue
        size = {"trunk": 16, "primary": 16, "secondary": 12, "tertiary": 8}.get(tags.get("highway"), 6)
        roads.append((pts, size))
    for pts, size in roads:
        d.line(pts, fill=INK, width=size + 6, joint="curve")
    for pts, size in roads:
        d.line(pts, fill="white", width=size, joint="curve")
    # numbered spots, matching pages 7 and 8
    font = ImageFont.truetype(BOWLBY, int(4.2 * MM))
    r = int(3.6 * MM)
    for n, (lat, lon) in SPOTS.items():
        x, y = xy(lat, lon)
        d.ellipse([x - r + 6, y - r + 6, x + r + 6, y + r + 6], fill=INK)
        d.ellipse([x - r, y - r, x + r, y + r], fill=CRIMSON, outline=INK, width=6)
        d.text((x, y + 2), str(n), fill="white", font=font, anchor="mm")
    small = ImageFont.load_default(size=int(2.2 * MM))
    d.text((W - 10, H - 10), "Map data © OpenStreetMap contributors", fill=INK, font=small, anchor="rd")
    img.save(out)
    print("map:", len(ways), "ways")


if __name__ == "__main__":
    main(sys.argv[1])
