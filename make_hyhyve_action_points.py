"""
Generate HyHyve Action Points (JSON) for the poster slots on
hyhyve_poster_hall_3150x2100.png.

The number of posters in each room is set by POSTERS_PER_ROOM in
make_poster_hall.py. Slots are numbered <room>.<n> by default, counting row
by row from the room sign towards the door (e.g. 2.1 is the first poster in
room 2), or use your own labels via POSTER_NUMBERS there; either way, the
"slot" column of posters.csv uses the same ids.
Nothing is drawn on the map for them, so you can move any point afterwards in
HyHyve. This script imports the geometry from make_poster_hall.py, so keep
both files in the same folder; hyhyve_poster_hall_coordinates.csv lists every
slot id with its position.

Usage
-----
  python make_hyhyve_action_points.py                       # placeholders for every slot
  python make_hyhyve_action_points.py --posters posters.csv # fill in names + PDFs
  python make_hyhyve_action_points.py --posters posters.csv --existing export.json
        # append to an existing HyHyve export instead of starting fresh

posters.csv columns (header row required):
  slot,name,content
  1.1,Poster Ordog,[56_AOrdog_CASCA2026.pdf](https://cdn.hyhyve.com/uploads/.../56_AOrdog_CASCA2026.pdf)
(a column called "board" is also accepted instead of "slot")

Slots not listed in the CSV are skipped (use --all to include empty placeholders).

Coordinates are pixels of the 3150 x 2100 background, origin top-left.
If HyHyve places a point by its top-left corner rather than its centre, use
--anchor topleft. If the map is shown at a different size in HyHyve, use
--scale (e.g. --scale 2 for a map displayed at 6300 x 4200).
"""
import argparse, csv, json, random, re, string
from make_poster_hall import slots

# ---------------- HyHyve action point template ----------------
def new_id(k=21):
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))

def action_point(position, name, content, size, sign):
    return {
        "id": new_id(),
        "position": position,
        "content": content,
        "name": name,
        "callType": "Group",
        "sign": sign,
        "openFullscreen": False,
        "startCallMinimized": False,
        "overrideDisableAutoJoinStaticMeetingAreas": None,
        "msTeamsAutoStartRecording": None,
        "wherebyAutoStartRecording": None,
        "wherebyLiveTranscription": None,
        "wherebyTranscriptionLanguage": None,
        "wherebyAutoStartTranscription": None,
        "customMeetingUrl": None,
        "customMeetingUrlHost": None,
        "actions": [],
        "size": size,
    }

# Default = no sign graphic. Use --sign flipchart/wood to show a poster stand in HyHyve.
# ---------------- poster thumbnails on the map ----------------
# HyHyve draws an action point's "sign" image on the map and shows the action
# point's content inside the sign's text area (that's how your "Poster test"
# polaroid showed its screenshot). So to see a small version of each poster on
# the map, the content must be an embedded image (![..](url), done
# automatically below) and the sign needs a picture-sized text area:
#   --sign polaroid  built-in HyHyve frame, works straight away (389 x 246 px)
#   --sign square    pixel-art board matching the squares on the poster-hall
#                    map (120 x 120 px), thumbnail fills the paper. One-time setup:
#     1. python make_hyhyve_action_points.py --make-square-sign
#          -> writes hyhyve_square_sign.png
#     2. Upload it to HyHyve (e.g. drop it into any action point's content
#        editor) and copy the https://cdn.hyhyve.com/... link it gives you.
#     3. Paste the link into SQUARE_SIGN_SRC below (or pass --sign-src URL).
# DEFAULT: --sign none. Nothing extra is drawn on the map (the numbered squares
# are already on the background); the embedded image pops up in the action
# point's panel when someone walks onto it. --sign auto uses the square board
# once SQUARE_SIGN_SRC is set, and the polaroid until then.
SQUARE_SIGN_SRC = ""                 # e.g. "https://cdn.hyhyve.com/uploads/.../hyhyve_square_sign.png"
SQUARE_SIGN_PX = 120                 # = POSTER_SQUARE_SIZE (24) x 5 in make_poster_hall.py
SQUARE_TEXT_AREA = {"position": [10, 27], "size": [100, 83]}   # the paper: where the thumbnail goes

def square_sign(src):
    return {"tag": "Sign", "asset": {"src": src, "size": [SQUARE_SIGN_PX, SQUARE_SIGN_PX],
                                     "textArea": SQUARE_TEXT_AREA}}

def make_square_sign_png(path="hyhyve_square_sign.png", accent="#3b7dc4"):
    """Draw the square poster-board sign in the same pixel style as the maps."""
    from PIL import Image, ImageDraw
    P = 5
    n = SQUARE_SIGN_PX // P                       # 24 x 24 art pixels
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    OL = "#3a2e3c"
    d.rectangle([1, n - 2, n - 1, n - 1], fill=(40, 30, 70, 70))     # shadow
    d.rectangle([0, 0, n - 2, n - 3], fill="#8a5a34", outline=OL)     # wooden frame
    d.rectangle([2, 2, n - 4, n - 5], fill="#fbfbf6")                 # paper
    d.rectangle([3, 3, n - 5, 4], fill=accent)                        # title strip
    for x in (2, n - 5):                                              # pins
        d.rectangle([x, 2, x + 1, 2], fill="#d9534f")
    im.resize((n * P, n * P), Image.NEAREST).save(path)
    print(f"wrote {path} ({n * P} x {n * P}); upload it to HyHyve and set SQUARE_SIGN_SRC")

SIGNS = {
    "none": {"tag": "Default"},
    "flipchart": {"tag": "Sign", "asset": {"src": "/static/game/signs/flipchart.png", "size": [207, 270],
                  "textArea": {"position": [50, 23], "size": [104, 126]}}},
    "wood": {"tag": "Sign", "asset": {"src": "/static/game/signs/wood.png", "size": [248, 233],
             "textArea": {"position": [30, 20], "size": [190, 105]}}},
    "polaroid": {"tag": "Sign", "asset": {"src": "/static/game/signs/polaroid.png", "size": [389, 246],
                 "textArea": {"position": [138, 29], "size": [125, 135]}}},
    "square": None,                  # filled in from SQUARE_SIGN_SRC / --sign-src
    "auto": None,                    # square if SQUARE_SIGN_SRC is set, else polaroid
    "poster": None,                  # each point's own poster image, shown as a small square
}

# ---------------- show images inline ----------------
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")

def embed_images(content):
    """Turn markdown links to images into embedded images, so HyHyve shows the
    picture instead of the file name:
        [poster.png](https://.../poster.png)  ->  ![poster.png](https://.../poster.png)
        https://.../poster.png                ->  ![poster.png](https://.../poster.png)
    Links to other files (e.g. PDFs) are left as clickable links."""
    def is_img(url):
        return url.split("?")[0].split("#")[0].lower().endswith(IMAGE_EXT)
    # [text](url) not already preceded by "!"
    content = re.sub(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)",
                     lambda m: f"![{m.group(1)}]({m.group(2)})" if is_img(m.group(2)) else m.group(0),
                     content)
    # bare image URLs on their own
    content = re.sub(r"(?<![(\[!])\b(https?://\S+)",
                     lambda m: f"![{m.group(1).rsplit('/', 1)[-1]}]({m.group(1)})" if is_img(m.group(1)) else m.group(0),
                     content)
    return content

def first_image_url(content):
    """URL of the first image (or image link) in the markdown content, or None."""
    for m in re.finditer(r"\(([^)\s]+)\)|(https?://\S+)", content):
        url = m.group(1) or m.group(2)
        if url.split("?")[0].split("#")[0].lower().endswith(IMAGE_EXT):
            return url
    return None

def poster_sign(url, px):
    """Sign that shows the poster image itself as a px x px square on the map
    (no text area, so HyHyve writes nothing over it)."""
    return {"tag": "Sign", "asset": {"src": url, "size": [px, px],
                                     "textArea": {"position": [0, 0], "size": [0, 0]}}}

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posters", help="CSV with columns slot,name,content")
    ap.add_argument("--existing", help="existing HyHyve action-point JSON to append to")
    ap.add_argument("--all", action="store_true", help="include slots with no poster assigned")
    ap.add_argument("--anchor", choices=["center", "topleft"], default="center")
    ap.add_argument("--size", type=int, nargs=2, default=[200, 200],
                    help="trigger area size in px (default 200 200, a square about one poster's footprint)")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--sign", choices=list(SIGNS), default="poster",
                    help="sign drawn on the map (default poster: a small square of the poster image "
                         "itself, sitting on the numbered square; none = nothing on the map, the "
                         "poster only pops up)")
    ap.add_argument("--thumb-size", type=int, default=120,
                    help="side of the square poster thumbnail in px (default 120 = the squares on the map)")
    ap.add_argument("--sign-src", default=SQUARE_SIGN_SRC,
                    help="URL of the uploaded hyhyve_square_sign.png (for --sign square)")
    ap.add_argument("--make-square-sign", action="store_true",
                    help="write hyhyve_square_sign.png and stop")
    ap.add_argument("--out", default="hyhyve_action_points.json")
    ap.add_argument("--no-embed-images", action="store_true",
                    help="keep image links as links (default: embed them, so the sign shows a thumbnail)")
    a = ap.parse_args()
    if a.make_square_sign:
        make_square_sign_png()
        return
    if a.sign == "auto":
        a.sign = "square" if a.sign_src else "polaroid"
        print(f"sign: {a.sign}" + ("" if a.sign_src else
              " (set SQUARE_SIGN_SRC to use the square board that matches the map)"))
    if a.sign == "square":
        if not a.sign_src:
            raise SystemExit(
                "The square sign needs its image hosted on HyHyve first:\n"
                "  1. python make_hyhyve_action_points.py --make-square-sign\n"
                "  2. upload hyhyve_square_sign.png to HyHyve and copy its cdn.hyhyve.com link\n"
                "  3. set SQUARE_SIGN_SRC in this script, or add --sign-src <link>\n"
                "(or use --sign polaroid, which needs no upload)")
        SIGNS["square"] = square_sign(a.sign_src)

    posters = {}
    if a.posters:
        with open(a.posters, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                sid = (row.get("slot") or row.get("board") or "").strip()
                content = row.get("content", "").strip()
                if not a.no_embed_images:
                    content = embed_images(content)
                posters[sid] = (row.get("name", "").strip(), content)
    use_all = a.all or not a.posters

    s = a.scale
    size = [round(a.size[0] * s), round(a.size[1] * s)]
    points = json.load(open(a.existing, encoding="utf-8")) if a.existing else []
    known = set()
    for sid, room, (cx, cy) in slots():
        known.add(sid)
        if sid not in posters and not use_all:
            continue
        cx, cy = round(cx * s), round(cy * s)
        name, content = posters.get(sid, (f"Poster {sid}", ""))
        pos = [cx, cy] if a.anchor == "center" else [cx - size[0] // 2, cy - size[1] // 2]
        sign = SIGNS[a.sign]
        if a.sign == "poster":
            url = first_image_url(content)
            sign = poster_sign(url, a.thumb_size) if url else SIGNS["none"]
            if not url:
                print(f"note: slot {sid} has no image link; no thumbnail for it")
        points.append(action_point(pos, name, content, size, sign))

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4, ensure_ascii=False)
    print(f"wrote {a.out} ({len(points)} action points)")
    unknown = set(posters) - known
    if unknown:
        print("warning: unknown slot ids in CSV:", ", ".join(sorted(unknown)))

if __name__ == "__main__":
    main()
