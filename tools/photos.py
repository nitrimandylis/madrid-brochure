# /// script
# dependencies = ["pillow"]
# ///
# Downloads the brochure's photos from Wikimedia Commons, crops them to their slot,
# and records who took each one and under which licence (tools/photos.json).
# Usage: uv run tools/photos.py            all slots
#        uv run tools/photos.py sol debod  only these
import io, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

from PIL import Image

DPI = 300
MM = DPI / 25.4
UA = {"User-Agent": "madrid-brochure/0.1 (student brochure project)"}
OUT = Path("art/photos")

# slot -> (Commons file, width mm, height mm, area of the source to keep as fractions x0 y0 x1 y1)
SQUARE = 48
THUMB = (34, 30)
SLOTS = {
    # history, pages 3-4
    "panel1": ("Muralla musulmana - Catedral de Santa María la Real de la Almudena - Madrid.jpg", SQUARE, SQUARE, (0, 0, 1, 1)),
    "panel2": ("Alfonso VI de León y Castilla 01.jpg", SQUARE, SQUARE, (0, 0, 1, 0.7)),
    "panel3": ("Monumento a Felipe III (Madrid) 03.jpg", SQUARE, SQUARE, (0, 0, 1, 1)),
    "panel4": ("Monumento a Miguel de Cervantes - 03.jpg", SQUARE, SQUARE, (0, 0, 1, 1)),
    "panel5": ("Madrid - Malasaña, Plaza del Dos de Mayo, Monumento a Daoiz y Velarde 2.jpg", SQUARE, SQUARE, (0, 0, 1, 0.8)),
    "panel6": ("Telefónica - Gran Vía 28 - Madrid.jpg", SQUARE, SQUARE, (0, 0, 1, 1)),
    # Prado hunt, page 6
    "meninas": ("Las Meninas, by Diego Velázquez, from Prado in Google Earth.jpg", *THUMB, (0, 0, 1, 1)),
    "bosch": ("Hieronymus Bosch - The Garden of Earthly Delights - Hell.jpg", *THUMB, (0, 0.55, 1, 1)),
    "goya3may": ("El Tres de Mayo, by Francisco de Goya, from Prado in Google Earth.jpg", *THUMB, (0, 0, 1, 1)),
    "saturn": ("Francisco de Goya, Saturno devorando a su hijo (1819-1823).jpg", *THUMB, (0, 0, 1, 0.75)),
    "greco": ("The Nobleman with his hand on his chest, by El Greco (Museo del Prado, Madrid).jpg", *THUMB, (0.1, 0.05, 0.9, 0.7)),
    # Go see, pages 7-8
    "sol": ("Plaza Puerta del Sol, Casa de Correos.jpg", *THUMB, (0, 0, 1, 1)),
    "mayor": ("Plaza Mayor, Madrid, España, 2023-01-03, DD 78.jpg", *THUMB, (0, 0, 1, 1)),
    "palacio": ("Fachada Este - Palacio Real - Madrid 01.jpg", *THUMB, (0, 0, 1, 1)),
    "debod": ("Templo de Debod al atardecer.JPG", *THUMB, (0, 0, 1, 1)),
    "granvia": ("Edificio Metrópolis, calle de Alcalá, Madrid, España, 2017-05-18, DD 08.jpg", *THUMB, (0, 0, 1, 1)),
    "retiro": ("Palacio de Cristal, Parque del Retiro, Madrid, España, 2017-05-18, DD 21.jpg", *THUMB, (0, 0, 1, 1)),
    "rastro": ("Rastro de Madrid (España) 1.jpg", *THUMB, (0, 0, 1, 1)),
    "bernabeu": ("M-estadio-santiago-bernabeu-diciembre-2024-a.jpg", *THUMB, (0, 0, 1, 1)),
    # Toledo, page 10
    "toledo": ("Vista de Toledo desde el mirador del Valle 02.jpg", 134, 52, (0, 0, 1, 1)),
}


def fetch(url):
    # Commons rate-limits bursts: wait and retry on 429
    for wait in (0, 5, 15, 40):
        time.sleep(wait)
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
    raise RuntimeError("still rate-limited: " + url)


def info(title):
    params = {
        "action": "query", "format": "json", "titles": "File:" + title,
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1280,
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    page = next(iter(json.loads(fetch(url))["query"]["pages"].values()))
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    artist = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
    return ii["thumburl"], {
        "title": title,
        "page": ii["descriptionurl"],
        "licence": meta.get("LicenseShortName", {}).get("value", "?"),
        "artist": artist,
    }


def crop(img, w_mm, h_mm, box):
    iw, ih = img.size
    img = img.crop((int(box[0] * iw), int(box[1] * ih), int(box[2] * iw), int(box[3] * ih)))
    w, h = int(w_mm * MM), int(h_mm * MM)
    iw, ih = img.size
    # cover the slot: trim whichever side is too long, keeping the centre
    if iw / ih > w / h:
        nw = int(ih * w / h)
        img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw * h / w)
        img = img.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    return img.resize((w, h), Image.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    credits_file = Path("tools/photos.json")
    credits = json.loads(credits_file.read_text()) if credits_file.exists() else {}
    for slot in sys.argv[1:] or SLOTS:
        title, w, h, box = SLOTS[slot]
        url, credit = info(title)
        data = fetch(url)
        crop(Image.open(io.BytesIO(data)).convert("RGB"), w, h, box).save(OUT / f"{slot}.jpg", quality=90)
        credits[slot] = credit
        print(slot, "|", credit["licence"], "|", credit["artist"])
    credits_file.write_text(json.dumps(credits, indent=1, ensure_ascii=False))
