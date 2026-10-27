"""
HyHyve map 1: POSTER HALL — empty poster rooms (posters are added as HyHyve
Action Points, so none are drawn on the background) plus an optional foyer.

Run:  python make_poster_hall.py
  -> hyhyve_poster_hall_3150x2100.png
  -> hyhyve_poster_hall_coordinates.csv  (rooms + poster slots, final px)

Edit the SETTINGS block below. make_hyhyve_action_points.py imports slots()
from this file, so the Action Points always follow these settings.

Positions inside a room are given as (across, depth) fractions:
  across: 0 = left wall, 1 = right wall
  depth:  0 = far wall (where the room sign is), 1 = door wall
so the same numbers work for rooms whose door is at the top or the bottom.
Foyer positions are plain (x, y) fractions of the foyer: 0,0 = top-left.
"""
import math
import hyhyve_pixel_kit as k

# =============================== SETTINGS ===============================
HALL_TITLE = "ERS POSTER HALL"          # sign in the foyer

# One room per name, in reading order (top row left->right, then next row).
# Room colours follow kit.ROOM_COLOURS (blue, green, orange, purple, red, ...).
ROOM_NAMES = ["Galaxies", "Transients & \n Cosmology", "Exoplanets\n & Stars",
              "Galaxies, Gas/dust,\n Solar System & Stars", "Black holes \n & Instrumentation"]
# Put "\n" inside a name to split its sign onto two (or more) lines.
ROOM_COLUMNS = 3                    # rooms per row (the foyer takes one cell)
SHOW_FOYER = True                   # foyer sits in the middle of the bottom row
SIGN_TEXT_SIZE = 11                 # room-sign font size (art pixels)
DOOR_WIDTH = 44                     # art pixels (1 art pixel = 5 image pixels)

# Poster slots (invisible; used for Action Points).
# POSTERS_PER_ROOM: how many posters in each room, in the same order as
# ROOM_NAMES, e.g. [10, 6, 8, 12, 5]. A dict also works, e.g. {1: 10, 4: 12}
# (rooms not listed use the default). None = every room uses the default.
# Each room's posters are laid out in a grid that suits the room's shape;
# set POSTER_ROWS to force the number of rows (None = automatic).
POSTERS_PER_ROOM = [7, 12, 7, 7, 7]
DEFAULT_POSTERS = 8
POSTER_ROWS = None

# POSTER_NUMBERS: your own labels for the slots (e.g. abstract/poster numbers).
#   None                      -> automatic ids "<room>.<n>" (1.1, 1.2, ... 2.1, ...)
#   list of lists, one per room, e.g. [[101, 102, 103], [201, 202], ...]
#   dict {room: [labels]}, e.g. {1: [12, 15, 31], 3: ["P7", "P8"]}
#   flat list, e.g. list(range(1, 41)) -> handed out in order, filling room 1
#                                      first (using POSTERS_PER_ROOM counts)
# Where a room has its own list, its length sets that room's poster count.
# Labels must be unique; they become the slot ids used in posters.csv.
POSTER_NUMBERS = {ROOM_NAMES[0]: [62,56,90,22,19,74,84], ROOM_NAMES[1]: [35,46,81,93,68,21,10,65,11,91,38,6], ROOM_NAMES[2]: [42,58,26,2,89,57,92],ROOM_NAMES[3]: [77,72,87,25,32,85,3],ROOM_NAMES[4]: [76,16,33,51,60,5,64]}
WRITE_SLOT_PREVIEW = True   # also save a copy of the map with the slots outlined (for checking)

# Furniture in every poster room
CHAIRS_PER_ROOM = 6                 # small chairs, split along the two side walls
BENCHES_PER_ROOM = 2                # benches along the door wall, either side of the door
ROOM_PLANTS = [(0.05, 0.06), (0.95, 0.06)]           # (across, depth)
ROOM_FLOWER_PLANTS = []                              # pots with pink flowers
ROOM_LAMPS = [(0.05, 0.86), (0.95, 0.86)]            # floor lamps

# Foyer (only drawn if SHOW_FOYER)
FOYER_WELCOME_TEXT = "WELCOME, CASCA!"      # "" for no mat
FOYER_PROGRAMME_BOARD = True
FOYER_BENCHES = 2
FOYER_PLANTS = [(0.15, 0.30)]
FOYER_FLOWER_PLANTS = [(0.85, 0.30)]
FOYER_LAMPS = [(0.15, 0.85), (0.85, 0.85)]

# Wall/hit map: a separate PNG with only the room walls (black) and the
# doorways left open, same size as the background, for drawing walls /
# collision areas in HyHyve.
WRITE_HIT_MAP = True
HIT_MAP_TRANSPARENT = True          # HyHyve hit map: transparent = walkable, black = wall (False = black on white, for viewing)
# ========================================================================

M, GAP_X, CORRIDOR = 14, 13, 40     # outer margin, gap between rooms, corridor height

def layout():
    """Compute room boxes (art px) from the settings.
    Returns (rooms, foyer) with rooms = {index: (name, (x0,y0,x1,y1), door_side)}."""
    n = len(ROOM_NAMES)
    cols = max(1, ROOM_COLUMNS)
    cells = n + (1 if SHOW_FOYER else 0)
    rows = math.ceil(cells / cols)
    cw = (k.W - 2 * M - (cols - 1) * GAP_X) / cols
    ch = (k.H - 2 * M - (rows - 1) * CORRIDOR) / rows
    foyer_cell = (rows - 1, cols // 2) if SHOW_FOYER else None
    order = [(r, c) for r in range(rows) for c in range(cols) if (r, c) != foyer_cell]
    box = lambda r, c: (round(M + c * (cw + GAP_X)), round(M + r * (ch + CORRIDOR)),
                        round(M + c * (cw + GAP_X) + cw), round(M + r * (ch + CORRIDOR) + ch))
    rooms = {}
    for i, name in enumerate(ROOM_NAMES):
        r, c = order[i]
        rooms[i + 1] = (name, box(r, c), "bottom" if r == 0 and rows > 1 else "top")
    foyer = box(*foyer_cell) if SHOW_FOYER else None
    return rooms, foyer

ROOMS, FOYER = layout()

def room_point(box, door, across, depth):
    """(across, depth) fractions -> canvas point, keeping clear of the walls."""
    x0, y0, x1, y1 = box
    m = k.T + 6
    x = x0 + m + across * (x1 - x0 - 2 * m)
    d = m + depth * (y1 - y0 - 2 * m)
    y = y0 + d if door == "bottom" else y1 - d
    return round(x), round(y)

def posters_in_room(i):
    """Number of posters for room i (1-based), from POSTERS_PER_ROOM."""
    p = POSTERS_PER_ROOM
    if p is None:
        return DEFAULT_POSTERS
    if isinstance(p, dict):
        return int(p.get(i, DEFAULT_POSTERS))
    return int(p[i - 1]) if i - 1 < len(p) else DEFAULT_POSTERS

def poster_grid(n, box):
    """Rows x columns for n posters in a room box (art px)."""
    if n <= 0:
        return 0, 0
    if POSTER_ROWS:
        rows = max(1, min(POSTER_ROWS, n))
    else:
        x0, y0, x1, y1 = box
        w, h = (x1 - x0), 0.62 * (y1 - y0)            # usable floor between sign and door
        rows = max(1, min(n, round(math.sqrt(n * h / w))))
    return rows, math.ceil(n / rows)

def slot_labels():
    """{room: [label, ...]} from POSTER_NUMBERS / POSTERS_PER_ROOM."""
    labels, pn = {}, POSTER_NUMBERS
    if isinstance(pn, (list, tuple)) and pn and not isinstance(pn[0], (list, tuple)):
        flat = [str(x) for x in pn]                # flat list: fill rooms in order
        pos = 0
        for i in ROOMS:
            n = posters_in_room(i)
            labels[i] = flat[pos:pos + n]
            pos += n
        if pos < len(flat):
            print(f"warning: {len(flat) - pos} POSTER_NUMBERS left over (rooms are full); "
                  "raise POSTERS_PER_ROOM to fit them")
    else:
        for i in ROOMS:
            own = None
            if isinstance(pn, dict):
                own = pn.get(i)
            elif isinstance(pn, (list, tuple)) and i - 1 < len(pn):
                own = pn[i - 1]
            if own is not None:
                labels[i] = [str(x) for x in own]
            else:
                labels[i] = [f"{i}.{j + 1}" for j in range(posters_in_room(i))]
    seen = {}
    for i, labs in labels.items():
        for lab in labs:
            if lab in seen:
                raise ValueError(f"poster label {lab!r} is used twice (rooms {seen[lab]} and {i})")
            seen[lab] = i
    return labels

def slots():
    """Yield (slot_id, room_index, (cx, cy)) poster positions in FINAL pixels.
    Slots fill row by row from the sign side; a part-filled last row is centred.
    slot_id is your label from POSTER_NUMBERS, or "<room>.<n>" by default."""
    labels = slot_labels()
    for i, (name, box, door) in ROOMS.items():
        labs = labels[i]
        n = len(labs)
        rows, cols = poster_grid(n, box)
        k_ = 0
        for r in range(rows):
            in_row = min(cols, n - r * cols)
            depth = 0.22 + 0.62 * (r + 0.5) / rows     # clear of sign and door
            for c in range(in_row):
                across = (c + 1 + (cols - in_row) / 2) / (cols + 1)
                x, y = room_point(box, door, across, depth)
                yield labs[k_], i, (x * k.P, y * k.P)
                k_ += 1

# ---------------- drawing ----------------
def spread(n, a, b):
    """n evenly spaced values strictly between a and b."""
    return [a + (b - a) * (j + 1) / (n + 1) for j in range(n)]

def poster_room(i, name, box, door):
    x0, y0, x1, y1 = box
    c1, c2, edge, accent = k.ROOM_COLOURS[(i - 1) % len(k.ROOM_COLOURS)]
    cx = (x0 + x1) // 2
    k.striped_rug(x0, y0, x1, y1, c1, c2, edge)
    k.room_walls(x0, y0, x1, y1, [(door, cx, DOOR_WIDTH)])
    # the sign sits on the far wall; decorations that would sit under it are
    # nudged into the room so the sign never covers them
    sh, sw = k.sign_height(name, SIGN_TEXT_SIZE), k.sign_width(name, SIGN_TEXT_SIZE)
    sy = y0 + 8 + sh // 2 if door == "bottom" else y1 - 8 - sh + sh // 2
    def clear(x, y, half_w=7):
        if abs(x - cx) < sw // 2 + half_w and abs(y - sy) < sh // 2 + 10:
            y = sy + sh // 2 + 12 if door == "bottom" else sy - sh // 2 - 12
        return x, y
    for a, d in ROOM_LAMPS:
        x, y = clear(*room_point(box, door, a, d)); k.floor_lamp(x - 2, y - 10)
    for a, d in ROOM_PLANTS:
        x, y = clear(*room_point(box, door, a, d)); k.plant(x - 5, y - 6)
    for a, d in ROOM_FLOWER_PLANTS:
        x, y = clear(*room_point(box, door, a, d)); k.plant(x - 5, y - 6, flowers=True)
    # benches along the door wall, split either side of the doorway
    left = (BENCHES_PER_ROOM + 1) // 2
    wall_y = y1 - k.T - 9 if door == "bottom" else y0 + k.T + 3
    for bx in spread(left, x0 + 16, cx - DOOR_WIDTH // 2 - 4):
        k.bench(round(bx) - 15, wall_y)
    for bx in spread(BENCHES_PER_ROOM - left, cx + DOOR_WIDTH // 2 + 4, x1 - 16):
        k.bench(round(bx) - 15, wall_y)
    # chairs along the side walls
    per_side = [(CHAIRS_PER_ROOM + 1) // 2, CHAIRS_PER_ROOM // 2]
    for side, cnt in zip((0, 1), per_side):
        for d in spread(cnt, 0.2, 0.8):
            x, y = room_point(box, door, side, d)
            k.small_chair(x - 3 + (2 if side == 0 else -2), y - 2)
    k.sign(cx, sy, name, accent, SIGN_TEXT_SIZE)

def foyer(box):
    ex0, ey0, ex1, ey1 = box
    fp = lambda fx, fy: (round(ex0 + fx * (ex1 - ex0)), round(ey0 + fy * (ey1 - ey0)))
    ecx = (ex0 + ex1) // 2
    k.tile_floor(ex0 + 20, ey0 + 30, ex1 - 20, ey1, "#efe9dc", "#e5dccb")
    for fx, fy in FOYER_LAMPS:
        x, y = fp(fx, fy); k.floor_lamp(x - 2, y - 10)
    for fx, fy in FOYER_PLANTS:
        x, y = fp(fx, fy); k.plant(x - 5, y - 6)
    for fx, fy in FOYER_FLOWER_PLANTS:
        x, y = fp(fx, fy); k.plant(x - 5, y - 6, flowers=True)
    next_y = ey0 + 40
    if FOYER_PROGRAMME_BOARD:
        by = max(ey0 + 36, ey0 + (ey1 - ey0) // 3)
        k.programme_board(ecx - 16, by)
        next_y = by + 44
    if FOYER_BENCHES:
        bench_y = max(next_y, ey0 + round((ey1 - ey0) * 0.62))
        if bench_y > ey1 - 34:
            print("note: foyer too small for benches; skipped")
        else:
            for bx in spread(FOYER_BENCHES, ex0 + 20, ex1 - 20):
                k.bench(round(bx) - 15, bench_y)
    if FOYER_WELCOME_TEXT:
        k.welcome_mat(ecx, label=FOYER_WELCOME_TEXT, max_w=(ex1 - ex0) - 60, bottom=ey1 - 9)
    title, tsz = k.fit_label(HALL_TITLE, (ex1 - ex0) - 10, 12, 10)   # sign wraps around the title
    k.sign(ecx, ey0 + 6 + k.sign_height(title, tsz) // 2, title, "#2f3640", tsz)

def main():
    k.start()
    k.wood_floor(0, 0, k.W - 1, k.H - 1)
    areas = []
    for i, (name, box, door) in ROOMS.items():
        poster_room(i, name, box, door)
        areas.append(("room", name, box))
    if FOYER:
        foyer(FOYER)
        areas.append(("foyer", "Entrance foyer", FOYER))
    pts = [("slot", sid, xy) for sid, room, xy in slots()]   # listed in the CSV, not drawn
    k.save("hyhyve_poster_hall_3150x2100.png", areas, "hyhyve_poster_hall_coordinates.csv", pts)
    if WRITE_HIT_MAP:
        k.save_hit_map("hyhyve_poster_hall_walls_3150x2100.png", HIT_MAP_TRANSPARENT)
    if WRITE_SLOT_PREVIEW:   # separate checking image; the background above stays clean
        from PIL import Image, ImageDraw
        im = Image.open("hyhyve_poster_hall_3150x2100.png").convert("RGB")
        d = ImageDraw.Draw(im)
        f = k.font(40)
        for sid, room, (x, y) in slots():
            d.rectangle([x - 50, y - 60, x + 50, y + 60], outline="red", width=6)
            d.text((x - 40, y - 22), sid, fill="red", font=f)
        im.save("hyhyve_poster_hall_slots_preview.png")
        print("saved hyhyve_poster_hall_slots_preview.png")

if __name__ == "__main__":
    main()
