# /// script
# dependencies = []
# ///
# Finds reference images on Wikimedia Commons and saves them with their licence.
import json, sys, urllib.parse, urllib.request

UA = {"User-Agent": "madrid-brochure/0.1 (student brochure project)"}

def search(query, n=4):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": query + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": n,
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1600,
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))
    results = []
    for page in data.get("query", {}).get("pages", {}).values():
        info = page["imageinfo"][0]
        meta = info.get("extmetadata", {})
        results.append({
            "title": page["title"],
            "thumb": info["thumburl"],
            "page": info["descriptionurl"],
            "licence": meta.get("LicenseShortName", {}).get("value", "?"),
            "artist": meta.get("Artist", {}).get("value", "?")[:80],
        })
    return results

if __name__ == "__main__":
    for r in search(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4):
        print(json.dumps(r, ensure_ascii=False))
