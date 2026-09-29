"""
HyHyve map 2: SESSION HALL — parallel-session rooms (same colours as the
poster rooms) above a main hall with a stage, audience seating and
2-person meeting tables around the edge.

Run:  python make_session_hall.py
  -> hyhyve_session_hall_3150x2100.png
  -> hyhyve_session_hall_coordinates.csv   (rooms, stage, tables in final px)

Edit the SETTINGS block below. Sizes are in art pixels (1 art pixel = 5 image
pixels). Positions are fractions of the room or hall: (x, y) with 0,0 = the
top-left corner and 1,1 = the bottom-right corner.
"""
import hyhyve_pixel_kit as k

# =============================== SETTINGS ===============================
# --- parallel-session rooms (one per name, across the top) ---
SESSION_ROOM_NAMES = ["SESSION 1", "SESSION 2", "SESSION 3", "SESSION 4", "SESSION 5"]
SESSION_ROWS = 4                    # rows of chairs in each session room
SESSION_SEATS_PER_ROW = 8           # chairs per row (split by a centre aisle)
SESSION_ROOM_HEIGHT = 132           # art px
SESSION_SIGN_TEXT_SIZE = 10
SESSION_PODIUM = True
SESSION_PLANTS = [(0.1, 0.1)]
SESSION_FLOWER_PLANTS = []
SESSION_LAMPS = [(0.08, 0.84), (0.92, 0.84)]

# --- main hall ---
STAGE_TITLE = "MAIN STAGE"
STAGE_WIDTH, STAGE_DEPTH = 220, 52  # art px (centred at the top of the hall)
AUDIENCE_ROWS = 5                   # rows of chairs in front of the stage
AUDIENCE_SEATS_PER_ROW = 16         # chairs per row (split by a centre aisle)

# 2-person tables: one per label. Positions None = spread automatically along
# the left, right and bottom edges; or give one (x, y) fraction per table.
TABLE_LABELS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
TABLE_POSITIONS = None
TABLE_SCALE = 1.0                   # 1.0 = default size, 1.3 = 30% bigger, ...

# Decoration in the hall, as (x, y) fractions of the hall
HALL_PLANTS = [(0.24, 0.10), (0.24, 0.42), (0.76, 0.42)]
HALL_FLOWER_PLANTS = [(0.76, 0.10)]
HALL_FLOOR_LAMPS = [(0.30, 0.12), (0.70, 0.12)]
HALL_TABLE_LAMPS = [(0.15, 0.30), (0.85, 0.30)]
HALL_BAMBOO = [(0.04, 0.12), (0.96, 0.12)]
HALL_BOOKSHELVES = [(0.03, 0.83), (0.97, 0.83)]
HALL_PROGRAMME_BOARDS = [(0.47, 0.75), (0.53, 0.75)]
HALL_WELCOME_TEXT = "WELCOME"       # mat at the main entrance ("" for none)
ENTRANCE_LAMPS = True               # lamps either side of the entrance
# ========================================================================

M, ROOM_GAP, CORRIDOR = 14, 10, 30

def layout():
    n = len(SESSION_ROOM_NAMES)
    rw = (k.W - 2 * M - (n - 1) * ROOM_GAP) / n
    rooms = {i + 1: (name, (round(M + i * (rw + ROOM_GAP)), M,
                             round(M + i * (rw + ROOM_GAP) + rw), M + SESSION_ROOM_HEIGHT))
             for i, name in enumerate(SESSION_ROOM_NAMES)}
    hall = (M, M + SESSION_ROOM_HEIGHT + CORRIDOR, k.W - M, k.H - M)
    hcx = (hall[0] + hall[2]) // 2
    stage = (hcx - STAGE_WIDTH // 2, hall[1] + 16, hcx + STAGE_WIDTH // 2, hall[1] + 16 + STAGE_DEPTH)
    return rooms, hall, stage

ROOMS, HALL, STAGE = layout()

def frac(box, fx, fy):
    x0, y0, x1, y1 = box
    return round(x0 + fx * (x1 - x0)), round(y0 + fy * (y1 - y0))

def seats(cx, top, rows, per_row, max_w, max_h, dx=9, dy=11, label=""):
    """Centred block of chairs with a centre aisle, squeezed to fit if needed."""
    if rows <= 0 or per_row <= 0:
        return (cx, top, cx, top)
    aisle = 6 if per_row > 3 else 0
    if per_row > 1:
        dx = min(dx, (max_w - 6 - aisle) / (per_row - 1))
    if rows > 1:
        dy = min(dy, (max_h - 5) / (rows - 1))
    if dx < 7 or dy < 6:
        print(f"warning: {label}: {rows} x {per_row} chairs is too many for the space; they will overlap")
    width = (per_row - 1) * dx + aisle + 6
    x_start = cx - width / 2
    half = per_row // 2
    for r in range(rows):
        for c in range(per_row):
            x = x_start + c * dx + (aisle if c >= half else 0)
            k.small_chair(round(x), round(top + r * dy))
    return (round(x_start), top, round(x_start + width), round(top + (rows - 1) * dy + 5))

def auto_table_positions(n):
    """Spread n tables along left, right and bottom edges of the hall (fractions)."""
    side = round(n / 4)
    bottom = n - 2 * side
    left = [(0.056, y) for y in ([0.25, 0.55] if side == 2 else
                                 [0.25 + 0.4 * (j + 0.5) / side for j in range(side)])]
    right = [(0.944, y) for _, y in left]
    bl, br = (bottom + 1) // 2, bottom // 2
    bot = [(0.12 + 0.26 * (j + 0.5) / bl, 0.87) for j in range(bl)] + \
          [(0.62 + 0.26 * (j + 0.5) / br, 0.87) for j in range(br)]
    return left + right + bot   # T1.. down the left, then the right, then along the bottom

def session_room(i, name, box):
    x0, y0, x1, y1 = box
    c1, c2, edge, accent = k.ROOM_COLOURS[(i - 1) % len(k.ROOM_COLOURS)]
    cx = (x0 + x1) // 2
    k.striped_rug(x0, y0, x1, y1, c1, c2, edge)
    k.room_walls(x0, y0, x1, y1, [("bottom", cx, 30)])
    sw = min(30, (x1 - x0) // 2 - 12)
    k.screen(cx - sw, y0 + 7, cx + sw, accent)
    if SESSION_PODIUM:
        k.podium(x1 - 24, y0 + 32)
    for fx, fy in SESSION_LAMPS:
        x, y = frac(box, fx, fy); k.floor_lamp(x - 2, y - 10)
    for fx, fy in SESSION_PLANTS:
        x, y = frac(box, fx, fy); k.plant(x - 5, y - 6)
    for fx, fy in SESSION_FLOWER_PLANTS:
        x, y = frac(box, fx, fy); k.plant(x - 5, y - 6, flowers=True)
    seats(cx, y0 + 50, SESSION_ROWS, SESSION_SEATS_PER_ROW,
          (x1 - x0) - 20, (y1 - 26) - (y0 + 50) - 6, label=name)
    k.sign(cx, y1 - 14, name, accent, SESSION_SIGN_TEXT_SIZE)

def main():
    k.start()
    k.wood_floor(0, 0, k.W - 1, k.H - 1)
    areas = []
    for i, (name, box) in ROOMS.items():
        session_room(i, name, box)
        areas.append(("room", name, box))

    hx0, hy0, hx1, hy1 = HALL
    hcx = (hx0 + hx1) // 2
    k.striped_rug(hx0, hy0, hx1, hy1, *k.LOUNGE_RUG)
    doors = [("top", (b[0] + b[2]) // 2, 36) for _, b in ROOMS.values()]
    k.room_walls(hx0, hy0, hx1, hy1, doors + [("bottom", hcx, 60)])

    # decoration first, so furniture draws on top
    for fx, fy in HALL_FLOOR_LAMPS:
        x, y = frac(HALL, fx, fy); k.floor_lamp(x - 2, y - 10)
    for fx, fy in HALL_TABLE_LAMPS:
        x, y = frac(HALL, fx, fy); k.side_lamp(x - 4, y - 6)
    for fx, fy in HALL_BAMBOO:
        x, y = frac(HALL, fx, fy); k.bamboo(x - 13, y - 8)
    for fx, fy in HALL_BOOKSHELVES:
        x, y = frac(HALL, fx, fy); k.bookshelf(x - 13, y - 15)
    for fx, fy in HALL_PLANTS:
        x, y = frac(HALL, fx, fy); k.plant(x - 5, y - 6)
    for fx, fy in HALL_FLOWER_PLANTS:
        x, y = frac(HALL, fx, fy); k.plant(x - 5, y - 6, flowers=True)
    for fx, fy in HALL_PROGRAMME_BOARDS:
        x, y = frac(HALL, fx, fy); k.programme_board(x - 16, y - 13, None)

    k.stage(*STAGE, title=STAGE_TITLE)
    areas.append(("stage", STAGE_TITLE.title(), STAGE))
    top = STAGE[3] + 24
    aud = seats(hcx, top, AUDIENCE_ROWS, AUDIENCE_SEATS_PER_ROW,
                (hx1 - hx0) - 2 * 90, (hy1 - 50) - top, dx=8, label="audience")
    areas.append(("zone", "Stage audience", aud))

    positions = TABLE_POSITIONS or auto_table_positions(len(TABLE_LABELS))
    if len(positions) < len(TABLE_LABELS):
        print("warning: fewer TABLE_POSITIONS than TABLE_LABELS; extra tables skipped")
    for label, (fx, fy) in zip(TABLE_LABELS, positions):
        cx, cy = frac(HALL, fx, fy)
        k.duo_table(cx, cy, label, TABLE_SCALE)
        hw = round(21 * TABLE_SCALE)
        areas.append(("table", f"Table {label}", (cx - hw, cy - round(10 * TABLE_SCALE),
                                                  cx + hw, cy + round(10 * TABLE_SCALE) + 10)))

    if HALL_WELCOME_TEXT:
        k.welcome_mat(hcx, hy1 - 22, HALL_WELCOME_TEXT, 26)
    if ENTRANCE_LAMPS:
        k.floor_lamp(hcx - 44, hy1 - 28); k.floor_lamp(hcx + 40, hy1 - 28)
    areas.append(("room", "Main Hall", HALL))

    k.save("hyhyve_session_hall_3150x2100.png", areas, "hyhyve_session_hall_coordinates.csv")

if __name__ == "__main__":
    main()
