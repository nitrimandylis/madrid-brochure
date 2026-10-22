# /// script
# dependencies = ["pillow"]
# ///
# Draws a light-blue street guide of central Madrid from OpenStreetMap, for inking.
# Map data © OpenStreetMap contributors (ODbL).
# Usage: uv run tools/map_guide.py OUT.png
import json, math, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

BLUE = (95, 170, 230)
PALE = (215, 233, 248)
DPI = 200
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
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": QUERY}).encode(),
        headers={"User-Agent": "madrid-brochure/0.1 (student brochure project)"},
    )
    ways = json.load(urllib.request.urlopen(req))["elements"]
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    # parks first, as pale fills (big parks like the Retiro are relations)
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
                d.polygon(pts, fill=PALE)
    for way in ways:
        tags = way.get("tags", {})
        if "geometry" not in way or tags.get("leisure") == "park" or way["type"] != "way":
            continue
        pts = [xy(p["lat"], p["lon"]) for p in way["geometry"]]
        width = 6 if tags.get("waterway") else (4 if tags.get("highway") in ("trunk", "primary") else 3 if tags.get("highway") == "secondary" else 2)
        d.line(pts, fill=BLUE, width=width)
    font = ImageFont.load_default(size=int(4 * MM))
    r = int(3.2 * MM)
    for n, (lat, lon) in SPOTS.items():
        x, y = xy(lat, lon)
        d.ellipse([x - r, y - r, x + r, y + r], fill="white", outline=BLUE, width=4)
        d.text((x, y), str(n), fill=BLUE, font=font, anchor="mm")
    d.text((W - 6, H - 6), "© OpenStreetMap contributors", fill=BLUE, font=ImageFont.load_default(size=int(2.2 * MM)), anchor="rd")
    img.save(out)
    print("map guide:", len(ways), "ways")


if __name__ == "__main__":
    main(sys.argv[1])
