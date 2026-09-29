"""
Generate HyHyve Action Points (JSON) for the poster slots on
hyhyve_poster_hall_3150x2100.png.

Each poster room has 8 suggested slots (4 across x 2 deep), numbered
<room>.<n>: 1.1-1.4 is the row nearest the room sign, 1.5-1.8 the row nearer
the door. Nothing is drawn on the map for them, so you can move any point
afterwards in HyHyve. To change the slot grid, edit SLOT_COLS / SLOT_ROWS in
make_poster_hall.py (this script imports its geometry, so keep both files in
the same folder).

Usage
-----
  python make_hyhyve_action_points.py                       # placeholders for all 40 slots
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
import argparse, csv, json, random, string
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
SIGNS = {
    "none": {"tag": "Default"},
    "flipchart": {"tag": "Sign", "asset": {"src": "/static/game/signs/flipchart.png", "size": [207, 270],
                  "textArea": {"position": [50, 23], "size": [104, 126]}}},
    "wood": {"tag": "Sign", "asset": {"src": "/static/game/signs/wood.png", "size": [248, 233],
             "textArea": {"position": [30, 20], "size": [190, 105]}}},
}

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posters", help="CSV with columns slot,name,content")
    ap.add_argument("--existing", help="existing HyHyve action-point JSON to append to")
    ap.add_argument("--all", action="store_true", help="include slots with no poster assigned")
    ap.add_argument("--anchor", choices=["center", "topleft"], default="center")
    ap.add_argument("--size", type=int, nargs=2, default=[200, 220],
                    help="trigger area size in px (default 200 220, about one poster's footprint)")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--sign", choices=list(SIGNS), default="none")
    ap.add_argument("--out", default="hyhyve_action_points.json")
    a = ap.parse_args()

    posters = {}
    if a.posters:
        with open(a.posters, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                sid = (row.get("slot") or row.get("board") or "").strip()
                posters[sid] = (row.get("name", "").strip(), row.get("content", "").strip())
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
        points.append(action_point(pos, name, content, size, SIGNS[a.sign]))

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4, ensure_ascii=False)
    print(f"wrote {a.out} ({len(points)} action points)")
    unknown = set(posters) - known
    if unknown:
        print("warning: unknown slot ids in CSV:", ", ".join(sorted(unknown)))

if __name__ == "__main__":
    main()
