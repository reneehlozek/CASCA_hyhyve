"""
HyHyve map 1: POSTER HALL — poster rooms that grow with the number of posters
they hold, numbered poster squares, and a foyer with stairs back down to the
session hall.

Run:  python make_poster_hall.py
  -> hyhyve_poster_hall_<W>x<H>.png            background
  -> hyhyve_poster_hall_walls_<W>x<H>.png      hit map (walls only)
  -> hyhyve_poster_hall_slots_preview.png      checking copy with slots outlined
  -> hyhyve_poster_hall_coordinates.csv        rooms, foyer, stairs, poster slots (final px)

Edit the SETTINGS block below. make_hyhyve_action_points.py imports slots()
from this file, so the Action Points always follow these settings.

Positions inside a room are given as (across, depth) fractions:
  across: 0 = left wall, 1 = right wall
  depth:  0 = far wall (where the room sign is), 1 = door wall
so the same numbers work for rooms whose door is at the top or the bottom.
Foyer positions are plain (x, y) fractions of the foyer: 0,0 = top-left.
Sizes are in art pixels (1 art pixel = 5 image pixels).
"""
import math
import hyhyve_pixel_kit as k

# =============================== SETTINGS ===============================
MAP_WIDTH, MAP_HEIGHT = 7000, 4700  # final image size in pixels
DECOR_SCALE = 2                     # size of plants, lamps, bamboo (whole number: 1 = small, 2 = double)
MAT_SCALE = 2                       # size of the welcome mat (whole number)
HALL_TITLE = "POSTER HALL"          # sign in the foyer

# One room per name, in reading order (top row left->right, then next row).
# Room colours follow kit.ROOM_COLOURS (blue, green, orange, purple, red, ...).
ROOM_NAMES = ["Galaxies", "Transients & \n Cosmology", "Exoplanets\n & Stars",
              "Galaxies, Gas/dust,\n Solar System & Stars", "Black holes \n & Instrumentation"]
# Put "\n" inside a name to split its sign onto two (or more) lines.
ROOM_COLUMNS = 3                    # rooms per row (the foyer takes one cell)
SHOW_FOYER = True                   # foyer (networking area) takes the middle cell of a row
FOYER_ROW = "top"                   # "top" = in the first row of rooms, "bottom" = in the last row
SIGN_TEXT_SIZE = 20                 # room-sign font size (art pixels)
DOOR_WIDTH = 130                    # doorway of each poster room (art pixels; 100 = 500 px)

# Room size follows the posters: each room gets a grid of poster spots spaced
# POSTER_SPACING apart, plus margins; rooms with more posters are bigger.
# The whole layout is then scaled up to fill the map, so spacing only grows.
POSTER_SPACING = 64                 # minimum distance between poster centres (art px; 64 = 320 px)
ROOM_SIDE_MARGIN = 36               # space between the outer posters and the side walls
ROOM_SIGN_MARGIN = 60               # space between the sign wall and the first row of posters
ROOM_DOOR_MARGIN = 60               # space between the last row and the door wall
MIN_ROOM_WIDTH = 220
# Poster arrangement inside each room:
#   "scatter" - posters spread over the whole floor, both across and front-to-back,
#               each placed as far as possible from the others and the walls
#   "rows"    - staggered rows with a little random wobble
POSTER_LAYOUT = "scatter"
POSTER_JITTER = 0.18                # "rows" only: 0 = neat rows, 0.3 = quite loose
POSTER_CLEARANCE = 46               # art px kept clear from the walls, sign and door (46 = 230 px)
POSTER_SEED = 7                     # change for a different (but repeatable) wobble
# "scatter" only: how close posters may come to the edges of the poster area.
# Higher = posters spread further out towards the walls (fills big rooms).
POSTER_SPREAD = 3.5
POSTER_SPREAD_BY_ROOM = {2: 12}     # per-room overrides, by room number (2 = Transients & Cosmology)
# Pin individual posters to a spot. Key = poster number as shown on the square
# (the CSV "name") or its slot id (e.g. "2.4"). Value = one of
#   "sign-left"  - between the left corner plant and the room sign
#   "sign-right" - between the room sign and the right corner plant
#   (across, depth) fractions of the room, like the plant positions
# The other posters in the room are spread around the pinned ones.
POSTER_PLACEMENT = {"35": "sign-left", "81": "sign-right",
                    "16": (0.5, 0.22),      # Black holes: just in front of the room sign
                    "33": (0.85, 0.84),     # Black holes: top-right corner (by the door)
                    "64": (0.15, 0.84),     # Black holes: top-left corner (by the door)
                    "3": (0.36, 0.84),      # Galaxies, Gas/dust...: near the door
                    "72": (0.5, 0.22),      # Galaxies, Gas/dust...: just in front of the room sign
                    "56": (0.33, 0.17),     # Galaxies: just below the sign, left
                    "90": (0.67, 0.17),     # Galaxies: just below the sign, right
                    "19": (0.82, 0.50),     # Galaxies: over towards the right-hand wall
                    "57": (0.36, 0.86)}     # Exoplanets & Stars: next to the door
PINNED_WALL_GAP = 22                # "sign-left/right": space between the wall and the poster (art px)
FOYER_WIDTH = 420                   # foyer: open meet-and-mingle area (art px, before scaling)

# Poster slots (used for Action Points).
# POSTERS_PER_ROOM: how many posters in each room, in the same order as
# ROOM_NAMES, e.g. [10, 6, 8, 12, 5]. A dict also works, e.g. {1: 10, 4: 12}
# (rooms not listed use the default). None = every room uses the default.
# POSTER_CSV (below) overrides these counts when it is set.
# POSTER_ROWS forces the number of rows in every room (None = automatic).
POSTERS_PER_ROOM = [8, 8, 8, 8, 8]
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
POSTER_NUMBERS = None
WRITE_SLOT_PREVIEW = True   # also save a copy of the map with the slots outlined (for checking)

# Poster list: the same CSV you give make_hyhyve_action_points.py
# (columns board/slot, name, content). If set, it decides how many posters
# each room has (from the slot ids, e.g. 2.12 -> room 2 has 12) and the
# number/label written on each poster square (from SQUARE_LABEL_COLUMN).
# None = use POSTERS_PER_ROOM above and label squares with their slot ids.
POSTER_CSV = "posters_ERS.csv"
SQUARE_LABEL_COLUMN = "name"        # CSV column shown on each square
DRAW_POSTER_SQUARES = True          # draw a square board at every poster slot
POSTER_SQUARE_SIZE = 46             # art px (46 = 230 image px)
POSTER_SQUARE_TEXT_SIZE = 19

# Furniture in every poster room
CHAIRS_PER_ROOM = 6                 # chairs, split along the two side walls
ROOM_CHAIR_SCALE = 2                # chair size (whole number: 1 = small, 2 = double)
BENCHES_PER_ROOM = 2                # benches along the door wall, either side of the door
ROOM_PLANTS = [(0.03, 0.04), (0.97, 0.04)]           # (across, depth)
ROOM_FLOWER_PLANTS = []                              # pots with pink flowers
ROOM_LAMPS = [(0.03, 0.9), (0.97, 0.9)]              # floor lamps

# Foyer (only drawn if SHOW_FOYER): an open lounge to meet and mingle
FOYER_WELCOME_TEXT = "WELCOME"      # "" for no mat
FOYER_PROGRAMME_BOARD = True
FOYER_PROGRAMME_BOARD_POSITION = (0.5, 0.82)   # (x, y) fraction of the foyer: just above the welcome mat
# The board gets an action point whose pop-up shows programme.md - the same file
# the session hall's lobby board uses, so both show the same information.
PROGRAMME_FILE = "programme.md"
FOYER_BENCHES = 0
FOYER_PLANTS = [(0.06, 0.18), (0.94, 0.18)]
FOYER_FLOWER_PLANTS = []
FOYER_LAMPS = [(0.29, 0.90), (0.71, 0.90)]   # either side of the welcome mat
# Extra lounge furniture as (kind, x, y): kinds are sofa, sofa_plain, armchair,
# coffee_table, coffee_table_laptop, plant, flowers, floor_lamp, side_lamp,
# bookshelf, bamboo, programme_board, pingpong, bench
FOYER_FURNITURE = [
    ("bookshelf", 0.94, 0.86),
]
# Couch cluster on the foyer rug: facing sofas, coffee tables and armchairs
# grouped together (same as the session-hall lobby).
FOYER_LOUNGE = True
FOYER_LOUNGE_POSITION = (0.31, 0.50)   # (x, y) fraction of the foyer: centre of the cluster
FOYER_LOUNGE_SCALE = 2
FOYER_LOUNGE_WIDE = True            # True = two sofas on each side
FOYER_LOUNGE_ARMCHAIRS = 4

# Stairs back down to the session hall (a separate HyHyve space). Listed in
# the coordinates CSV as type "link" so you can put an action point on them.
SHOW_STAIRS = True
STAIRS_LABEL = "TO SESSION HALL"
STAIRS_POSITION = (0.78, 0.50)      # (x, y) fraction of the foyer: centre of the stairs
STAIRS_SIZE = (34, 30)

# More seating in the networking areas: small cafe sets (a round table with two
# armchairs). FOYER_CHAIR_SETS are (x, y) fractions of the foyer;
# CORRIDOR_CHAIR_SETS are spread along the corridor between the two rows of
# rooms, keeping the doorways clear.
FOYER_CHAIR_SETS = [(0.66, 0.24), (0.88, 0.24), (0.88, 0.66)]
CORRIDOR_CHAIR_SETS = 5
CHAIR_SET_SCALE = 1.8

# Wall/hit map: a separate PNG with only the room walls (black) and the
# doorways left open, same size as the background.
WRITE_HIT_MAP = True
HIT_MAP_TRANSPARENT = True          # HyHyve hit map: transparent = walkable, black = wall
# ========================================================================

k.set_size(MAP_WIDTH, MAP_HEIGHT)
k.DECOR_SCALE, k.MAT_SCALE = DECOR_SCALE, MAT_SCALE
M, MIN_GAP_X, CORRIDOR = 20, 24, 90         # outer margin, min gap between rooms, corridor between rows

# ---------------- poster counts and labels ----------------
def read_poster_csv():
    """{slot_id: row} from POSTER_CSV (empty if not set)."""
    if not POSTER_CSV:
        return {}
    import csv, os
    if not os.path.exists(POSTER_CSV):
        print(f"warning: POSTER_CSV {POSTER_CSV!r} not found; using POSTERS_PER_ROOM")
        return {}
    rows = {}
    with open(POSTER_CSV, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            sid = (row.get("slot") or row.get("board") or "").strip()
            if sid:
                rows[sid] = row
    return rows

POSTER_ROWS_CSV = read_poster_csv()
ROOM_IDS = list(range(1, len(ROOM_NAMES) + 1))

def posters_in_room(i):
    """Number of posters for room i (1-based): from POSTER_CSV slot ids
    (highest <room>.<n>), else POSTERS_PER_ROOM."""
    if POSTER_ROWS_CSV:
        ns = [int(sid.split(".")[1]) for sid in POSTER_ROWS_CSV
              if sid.split(".")[0] == str(i) and sid.count(".") == 1 and sid.split(".")[1].isdigit()]
        return max(ns) if ns else 0
    p = POSTERS_PER_ROOM
    if p is None:
        return DEFAULT_POSTERS
    if isinstance(p, dict):
        return int(p.get(i, DEFAULT_POSTERS))
    return int(p[i - 1]) if i - 1 < len(p) else DEFAULT_POSTERS

def slot_labels():
    """{room: [label, ...]} from POSTER_NUMBERS / poster counts."""
    labels, pn = {}, POSTER_NUMBERS
    if isinstance(pn, (list, tuple)) and pn and not isinstance(pn[0], (list, tuple)):
        flat = [str(x) for x in pn]                # flat list: fill rooms in order
        pos = 0
        for i in ROOM_IDS:
            n = posters_in_room(i)
            labels[i] = flat[pos:pos + n]
            pos += n
        if pos < len(flat):
            print(f"warning: {len(flat) - pos} POSTER_NUMBERS left over (rooms are full); "
                  "raise POSTERS_PER_ROOM to fit them")
    elif pn is None and POSTER_ROWS_CSV:
        # the CSV decides which posters exist: one slot per row, keeping its id
        def key(sid):
            a, _, b = sid.partition(".")
            return (int(a) if a.isdigit() else 0, int(b) if b.isdigit() else 0, sid)
        for i in ROOM_IDS:
            labels[i] = sorted((sid for sid in POSTER_ROWS_CSV if sid.split(".")[0] == str(i)), key=key)
    else:
        for i in ROOM_IDS:
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

LABELS = slot_labels()

def room_grid(n):
    """(rows, cols) for n posters: wide rooms, ~2 columns per row."""
    if n <= 0:
        return 0, 0
    rows = POSTER_ROWS or max(1, round(math.sqrt(n / 2)))
    rows = min(rows, n)
    return rows, math.ceil(n / rows)

# ---------------- layout ----------------
def layout():
    """Room boxes (art px) sized by poster count, packed in rows and scaled to
    fill the map. Returns (rooms, foyer, scale) with
    rooms = {i: dict(name, box, door, rows, cols, n)}."""
    n_rooms = len(ROOM_NAMES)
    cols = max(1, ROOM_COLUMNS)
    cells = n_rooms + (1 if SHOW_FOYER else 0)
    nrows = math.ceil(cells / cols)
    if not SHOW_FOYER:
        foyer_cell = None
    elif FOYER_ROW == "top":
        foyer_cell = (0, min(cols // 2, cells - 1))
    else:
        foyer_cell = (nrows - 1, min(cols // 2, cells - (nrows - 1) * cols - 1))
    order = [(r, c) for r in range(nrows) for c in range(cols)
             if (r, c) != foyer_cell and r * cols + c < cells + (0 if SHOW_FOYER else 0)]
    # natural sizes
    nat = {}
    for i in ROOM_IDS:
        rws, cls = room_grid(len(LABELS[i]))
        w = max(MIN_ROOM_WIDTH, cls * POSTER_SPACING + 2 * ROOM_SIDE_MARGIN)
        h = max(1, rws) * POSTER_SPACING + ROOM_SIGN_MARGIN + ROOM_DOOR_MARGIN
        nat[i] = (w, h, rws, cls)
    cell_of = {i: order[i - 1] for i in ROOM_IDS}
    rows_cells = [[] for _ in range(nrows)]               # [(kind, id, w, h)]
    for i in ROOM_IDS:
        r, c = cell_of[i]
        rows_cells[r].append((c, "room", i, nat[i][0], nat[i][1]))
    if SHOW_FOYER:
        r, c = foyer_cell
        rows_cells[r].append((c, "foyer", 0, FOYER_WIDTH, 0))
    for row in rows_cells:
        row.sort()
    row_h = [max([h for *_, h in row] + [1]) for row in rows_cells]
    row_w = [sum(w for _, _, _, w, _ in row) + MIN_GAP_X * (len(row) - 1) for row in rows_cells]
    avail_w = k.W - 2 * M
    avail_h = k.H - 2 * M - CORRIDOR * (nrows - 1)
    # stretch widths and heights separately so the rooms fill the whole map
    sx = avail_w / max(row_w)
    sy = avail_h / sum(row_h)
    corridor = CORRIDOR
    rooms, foyer = {}, None
    y = M
    for r, row in enumerate(rows_cells):
        h = row_h[r] * sy
        ws = [w * sx for _, _, _, w, _ in row]
        gap = (avail_w - sum(ws)) / max(1, len(row) - 1) if len(row) > 1 else 0
        x = M if len(row) > 1 else M + (avail_w - ws[0]) / 2
        door = "bottom" if (r == 0 and nrows > 1) else "top"
        for (c, kind, i, w, _), wsc in zip(row, ws):
            box = (round(x), round(y), round(x + wsc), round(y + h))
            if kind == "room":
                rows_n, cols_n = nat[i][2], nat[i][3]
                rooms[i] = dict(name=ROOM_NAMES[i - 1], box=box, door=door,
                                rows=rows_n, cols=cols_n, n=len(LABELS[i]))
            else:
                foyer = box
            x += wsc + gap
        y += h + corridor
    return dict(sorted(rooms.items())), foyer, (sx, sy)

ROOMS, FOYER, (SCALE_X, SCALE_Y) = layout()

def room_point(box, door, across, depth):
    """(across, depth) fractions -> canvas point, keeping clear of the walls."""
    x0, y0, x1, y1 = box
    m = k.T + 6
    x = x0 + m + across * (x1 - x0 - 2 * m)
    d = m + depth * (y1 - y0 - 2 * m)
    y = y0 + d if door == "bottom" else y1 - d
    return round(x), round(y)

def room_rows(n, w, h):
    """Split n posters into rows for a w x h floor: as many rows as suits the
    room's shape, counts as even as possible (e.g. 7 -> 3, 2, 2)."""
    if n <= 0:
        return []
    rows = POSTER_ROWS or max(1, min(n, round(math.sqrt(n * h / max(1, w)))))
    base, extra = divmod(n, rows)
    return [base + (1 if r < extra else 0) for r in range(rows)]

def scatter_points(n, w, h, rng, tries=60, spread=3.5, fixed=()):
    """n points spread evenly but irregularly over a w x h area (best-candidate
    sampling): each new point is the candidate farthest from the points so far
    and from the edges, so posters fill the room in both directions."""
    pts = []
    for _ in range(n):
        best, best_d = None, -1.0
        for _ in range(tries * (len(pts) + 1)):
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            d_edge = spread * min(x, w - x, y, h - y)    # room from the walls (lower = further in)
            d = min([math.hypot(x - a, y - b) for a, b in list(pts) + list(fixed)] + [d_edge])
            if d > best_d:
                best, best_d = (x, y), d
        pts.append(best)
    return pts

def pinned_spot(rm, spot):
    """Canvas (x, y) for a POSTER_PLACEMENT value in room rm."""
    x0, y0, x1, y1 = rm["box"]
    door = rm["door"]
    if isinstance(spot, (tuple, list)):
        return room_point(rm["box"], door, *spot)
    name = rm["name"]
    sh, sw = k.sign_height(name, SIGN_TEXT_SIZE), k.sign_width(name, SIGN_TEXT_SIZE)
    cx = (x0 + x1) // 2
    sy = y0 + 8 + sh // 2 if door == "bottom" else y1 - 8 - sh + sh // 2
    half = POSTER_SQUARE_SIZE // 2
    sy = max(sy, y0 + k.T + PINNED_WALL_GAP + half) if door == "bottom" else min(sy, y1 - k.T - PINNED_WALL_GAP - half)
    # corner plants sit at ROOM_PLANTS[0] / [1] (left / right); default to the corners
    lp = room_point(rm["box"], door, *(ROOM_PLANTS[0] if ROOM_PLANTS else (0.03, 0.04)))
    rp = room_point(rm["box"], door, *(ROOM_PLANTS[1] if len(ROOM_PLANTS) > 1 else (0.97, 0.04)))
    plant_half = 7 * DECOR_SCALE
    if spot == "sign-left":
        return round(((lp[0] + plant_half) + (cx - sw // 2)) / 2), sy
    if spot == "sign-right":
        return round(((cx + sw // 2) + (rp[0] - plant_half)) / 2), sy
    raise ValueError(f"unknown POSTER_PLACEMENT spot {spot!r}")

def slots():
    """Yield (slot_id, room_index, (cx, cy)) poster positions in FINAL pixels.
    Posters are spread over the room in staggered rows (filled from the sign
    side), with a small repeatable random wobble."""
    import random
    for i, rm in ROOMS.items():
        x0, y0, x1, y1 = rm["box"]
        labs = LABELS[i]
        if not labs:
            continue
        rng = random.Random(POSTER_SEED * 1000 + i)
        name = rm["name"]
        sign_band = 8 + k.sign_height(name, SIGN_TEXT_SIZE) + POSTER_CLEARANCE
        door_band = k.T + 12 + POSTER_CLEARANCE          # benches + doorway
        side = k.T + POSTER_CLEARANCE
        w, h = (x1 - x0) - 2 * side, (y1 - y0) - sign_band - door_band
        if POSTER_LAYOUT == "scatter":
            # pinned posters first (positions in the same local coordinates as the scatter)
            pinned = {}
            for sid in labs:
                row = POSTER_ROWS_CSV.get(sid) or {}
                key = (row.get(SQUARE_LABEL_COLUMN, "") or "").strip()
                spot = POSTER_PLACEMENT.get(key, POSTER_PLACEMENT.get(sid))
                if spot is None:
                    continue
                cx, cy = pinned_spot(rm, spot)
                d = (cy - y0) if rm["door"] == "bottom" else (y1 - cy)
                pinned[sid] = (cx - x0 - side, d - sign_band)
            free = [sid for sid in labs if sid not in pinned]
            pts = scatter_points(len(free), w, h, rng,
                                 spread=POSTER_SPREAD_BY_ROOM.get(i, POSTER_SPREAD),
                                 fixed=list(pinned.values()))
            pts.sort(key=lambda p: (round(p[1] / (h / max(1, round(math.sqrt(len(labs)))))), p[0]))
            placed = dict(zip(free, pts))
            placed.update(pinned)
            for sid in labs:
                px, py = placed[sid]
                x = x0 + side + px
                y = y0 + sign_band + py if rm["door"] == "bottom" else y1 - sign_band - py
                yield sid, i, (round(x) * k.P, round(y) * k.P)
            continue
        counts = room_rows(len(labs), w, h)
        rh = h / len(counts)
        j = 0
        for r, cnt in enumerate(counts):
            cw = w / cnt
            d = sign_band + rh * (r + 0.5)
            for c in range(cnt):
                x = x0 + side + cw * (c + 0.5)
                dd = d + rng.uniform(-1, 1) * POSTER_JITTER * rh
                x += rng.uniform(-1, 1) * POSTER_JITTER * cw
                y = y0 + dd if rm["door"] == "bottom" else y1 - dd
                yield labs[j], i, (round(x) * k.P, round(y) * k.P)
                j += 1

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
            cw, ch = 6 * ROOM_CHAIR_SCALE, 5 * ROOM_CHAIR_SCALE
            cx_ = x - 1 if side == 0 else x - cw + 1        # keep clear of the wall
            k.chair(cx_, y - ch // 2, ROOM_CHAIR_SCALE)
    k.sign(cx, sy, name, accent, SIGN_TEXT_SIZE)

EXTRA_POINTS = []          # programme board action point(s)

def corridor_chairs(areas):
    """Cafe sets spread along the corridor(s) between rows of rooms, clear of doors."""
    if not CORRIDOR_CHAIR_SETS:
        return
    boxes = [rm["box"] for rm in ROOMS.values()] + ([FOYER] if FOYER else [])
    tops = sorted({b[1] for b in boxes})
    if len(tops) < 2:
        return
    for upper, lower in zip(tops, tops[1:]):
        y_top = max(b[3] for b in boxes if b[1] == upper)
        y_bot = lower
        cy = (y_top + y_bot) // 2
        doors = [(b[0] + b[2]) / 2 for b in boxes if b[1] in (upper, lower)]
        x0, x1 = M + 30, k.W - M - 30
        # free stretches of corridor between the doorways
        cuts = sorted(d for d in doors)
        segs, cur = [], x0
        for d in cuts:
            a, b = d - DOOR_WIDTH, d + DOOR_WIDTH
            if a > cur:
                segs.append((cur, a))
            cur = max(cur, b)
        if cur < x1:
            segs.append((cur, x1))
        total = sum(b - a for a, b in segs)
        # share the sets out by stretch length, then space them evenly in each
        shares = [CORRIDOR_CHAIR_SETS * (b - a) / total for a, b in segs]
        counts = [int(v) for v in shares]
        for idx in sorted(range(len(segs)), key=lambda i: shares[i] - counts[i], reverse=True):
            if sum(counts) >= CORRIDOR_CHAIR_SETS:
                break
            counts[idx] += 1
        for (a, b), n in zip(segs, counts):
            for j in range(n):
                k.chair_set(round(a + (b - a) * (j + 0.5) / n), cy, CHAIR_SET_SCALE)

def foyer(box, areas):
    ex0, ey0, ex1, ey1 = box
    fp = lambda fx, fy: (round(ex0 + fx * (ex1 - ex0)), round(ey0 + fy * (ey1 - ey0)))
    ecx = (ex0 + ex1) // 2
    k.tile_floor(ex0, ey0 + 30, ex1, ey1, "#efe9dc", "#e5dccb")
    k.striped_rug(*fp(0.04, 0.32), *fp(0.58, 0.76), "#e9c9a0", "#efd3ad", "#d4ae80")   # lounge rug
    for fx, fy in FOYER_LAMPS:
        k.furniture("floor_lamp", *fp(fx, fy))
    for fx, fy in FOYER_PLANTS:
        k.furniture("plant", *fp(fx, fy))
    for fx, fy in FOYER_FLOWER_PLANTS:
        k.furniture("flowers", *fp(fx, fy))
    for kind, fx, fy in FOYER_FURNITURE:
        k.furniture(kind, *fp(fx, fy))
    if FOYER_LOUNGE:
        k.lounge_clump(*fp(*FOYER_LOUNGE_POSITION), scale=FOYER_LOUNGE_SCALE,
                       armchairs=FOYER_LOUNGE_ARMCHAIRS, wide=FOYER_LOUNGE_WIDE)
    for fx, fy in FOYER_CHAIR_SETS:
        k.chair_set(*fp(fx, fy), CHAIR_SET_SCALE)
    if FOYER_PROGRAMME_BOARD:
        bx, by = fp(*FOYER_PROGRAMME_BOARD_POSITION)
        k.programme_board(bx - 16, by - 13)
        areas.append(("board", "Programme board", (bx - 16, by - 13, bx + 16, by + 13)))
        EXTRA_POINTS.append(k.action_point((bx * k.P, by * k.P), "Programme",
                                           k.programme_content(PROGRAMME_FILE), (260, 260)))
    for bx in spread(FOYER_BENCHES, ex0 + 20, ex1 - 20):
        k.bench(round(bx) - 15, ey0 + round((ey1 - ey0) * 0.85))
    if FOYER_WELCOME_TEXT:
        k.welcome_mat(ecx, label=FOYER_WELCOME_TEXT, max_w=min(260, (ex1 - ex0) - 60), bottom=ey1 - 9)
    if SHOW_STAIRS:
        sx, sy = fp(*STAIRS_POSITION)
        sbox = k.stairs(sx, sy, *STAIRS_SIZE, label=STAIRS_LABEL, label_colour="#2f3640")
        areas.append(("link", k.one_line(STAIRS_LABEL).title(), sbox))
    title, tsz = k.fit_label(HALL_TITLE, (ex1 - ex0) - 10, 12, 10)   # sign wraps around the title
    k.sign(ecx, ey0 + 6 + k.sign_height(title, tsz) // 2, title, "#2f3640", tsz)

def main():
    k.start()
    k.wood_floor(0, 0, k.W - 1, k.H - 1)
    areas = []
    for i, rm in ROOMS.items():
        poster_room(i, rm["name"], rm["box"], rm["door"])
        areas.append(("room", rm["name"], rm["box"]))
    if DRAW_POSTER_SQUARES:
        for sid, room, (x, y) in slots():
            accent = k.ROOM_COLOURS[(room - 1) % len(k.ROOM_COLOURS)][3]
            row = POSTER_ROWS_CSV.get(sid)
            label = (row.get(SQUARE_LABEL_COLUMN, "") or "").strip() if row else sid
            k.poster_square(x // k.P, y // k.P, POSTER_SQUARE_SIZE, label, accent,
                            POSTER_SQUARE_TEXT_SIZE)
    corridor_chairs(areas)
    if FOYER:
        foyer(FOYER, areas)
        areas.append(("foyer", "Entrance foyer", FOYER))
    size = f"{k.W * k.P}x{k.H * k.P}"
    pts = [("slot", sid, xy) for sid, room, xy in slots()]   # listed in the coordinates CSV
    k.save(f"hyhyve_poster_hall_{size}.png", areas, "hyhyve_poster_hall_coordinates.csv", pts)
    if WRITE_HIT_MAP:
        k.save_hit_map(f"hyhyve_poster_hall_walls_{size}.png", HIT_MAP_TRANSPARENT)
    if EXTRA_POINTS:
        import json
        with open("hyhyve_poster_hall_action_points.json", "w", encoding="utf-8") as f:
            json.dump(EXTRA_POINTS, f, indent=4, ensure_ascii=False)
        print(f"saved hyhyve_poster_hall_action_points.json ({len(EXTRA_POINTS)} programme board point)")
    if WRITE_SLOT_PREVIEW:   # separate checking image; the background above stays clean
        from PIL import Image, ImageDraw
        im = Image.open(f"hyhyve_poster_hall_{size}.png").convert("RGB")
        d = ImageDraw.Draw(im)
        f = k.font(40)
        for sid, room, (x, y) in slots():
            d.rectangle([x - 100, y - 100, x + 100, y + 100], outline="red", width=6)
            d.text((x - 40, y + 64), sid, fill="red", font=f)
        im.save("hyhyve_poster_hall_slots_preview.png")
        print("saved hyhyve_poster_hall_slots_preview.png")

if __name__ == "__main__":
    main()
