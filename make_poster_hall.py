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
HALL_TITLE = "POSTER HALL"          # sign in the foyer

# One room per name, in reading order (top row left->right, then next row).
# Room colours follow kit.ROOM_COLOURS (blue, green, orange, purple, red, ...).
ROOM_NAMES = ["POSTER ROOM 1", "POSTER ROOM 2", "POSTER ROOM 3",
              "POSTER ROOM 4", "POSTER ROOM 5"]
ROOM_COLUMNS = 3                    # rooms per row (the foyer takes one cell)
SHOW_FOYER = True                   # foyer sits in the middle of the bottom row
SIGN_TEXT_SIZE = 11                 # room-sign font size (art pixels)
DOOR_WIDTH = 44                     # art pixels (1 art pixel = 5 image pixels)

# Poster slots (invisible; used for Action Points): columns x rows per room
SLOT_COLS, SLOT_ROWS = 4, 2

# Furniture in every poster room
CHAIRS_PER_ROOM = 6                 # small chairs, split along the two side walls
BENCHES_PER_ROOM = 2                # benches along the door wall, either side of the door
ROOM_PLANTS = [(0.05, 0.06), (0.95, 0.06)]           # (across, depth)
ROOM_FLOWER_PLANTS = []                              # pots with pink flowers
ROOM_LAMPS = [(0.05, 0.86), (0.95, 0.86)]            # floor lamps

# Foyer (only drawn if SHOW_FOYER)
FOYER_WELCOME_TEXT = "WELCOME"      # "" for no mat
FOYER_PROGRAMME_BOARD = True
FOYER_BENCHES = 2
FOYER_PLANTS = [(0.15, 0.30)]
FOYER_FLOWER_PLANTS = [(0.85, 0.30)]
FOYER_LAMPS = [(0.15, 0.85), (0.85, 0.85)]
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

def slots():
    """Yield (slot_id, room_index, (cx, cy)) poster positions in FINAL pixels."""
    for i, (name, box, door) in ROOMS.items():
        for r in range(SLOT_ROWS):
            depth = 0.22 + 0.62 * (r + 0.5) / SLOT_ROWS     # clear of sign and door
            for c in range(SLOT_COLS):
                across = (c + 1) / (SLOT_COLS + 1)
                x, y = room_point(box, door, across, depth)
                yield f"{i}.{r * SLOT_COLS + c + 1}", i, (x * k.P, y * k.P)

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
    for a, d in ROOM_LAMPS:
        x, y = room_point(box, door, a, d); k.floor_lamp(x - 2, y - 10)
    for a, d in ROOM_PLANTS:
        x, y = room_point(box, door, a, d); k.plant(x - 5, y - 6)
    for a, d in ROOM_FLOWER_PLANTS:
        x, y = room_point(box, door, a, d); k.plant(x - 5, y - 6, flowers=True)
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
    sy = y0 + 16 if door == "bottom" else y1 - 16          # sign on the far wall
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
        k.welcome_mat(ecx, ey1 - 24, FOYER_WELCOME_TEXT, 34)
    k.sign(ecx, ey0 + 14, HALL_TITLE, "#2f3640", 12)

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

if __name__ == "__main__":
    main()
