"""
HyHyve map 2: SESSION HALL — parallel-session rooms (same colours as the
poster rooms) above a main hall. In the hall: the main stage in its own room
(with its audience chairs), a lobby around the main entrance to meet and
mingle, discussion tables either side, and stairs up to the poster hall.

Run:  python make_session_hall.py
  -> hyhyve_session_hall_<W>x<H>.png             background
  -> hyhyve_session_hall_walls_<W>x<H>.png       hit map (walls only)
  -> hyhyve_session_hall_coordinates.csv         rooms, stage, lobby, tables, stairs (final px)
  -> hyhyve_session_hall_action_points.json      one action point per discussion table

Edit the SETTINGS block below. Sizes are in art pixels (1 art pixel = 5 image
pixels). Positions are fractions of the room, hall or lobby: (x, y) with
0,0 = the top-left corner and 1,1 = the bottom-right corner.
"""
import math
import hyhyve_pixel_kit as k
from hyhyve_pixel_kit import one_line

# =============================== SETTINGS ===============================
MAP_WIDTH, MAP_HEIGHT = 7000, 4700  # final image size in pixels
DECOR_SCALE = 2                     # plants/lamps/bamboo in the session rooms (whole number: 1 = small, 2 = double)
HALL_DECOR_SCALE = 2                # plants/lamps/bamboo in the main hall, stage room, lobby and quiet room
MAT_SCALE = 2                       # size of the welcome mat (whole number)

# --- parallel-session rooms (one per name, across the top) ---
SESSION_ROOM_NAMES = ["Galaxies", "Transients &\nCosmology", "Exoplanets\n& Stars",
                      "Galaxies, Gas/dust,\nSolar System & Stars", "Black holes\n& Instrumentation"]
# Put "\n" in a name to split its sign onto two lines.
SESSION_ROWS = 6                    # rows of chairs in each session room
SESSION_SEATS_PER_ROW = 10          # chairs per row (split by a centre aisle)
SESSION_CHAIR_SCALE = 2             # chair size in the session rooms (whole number)
SESSION_STAGE_DEPTH = 64            # raised stage (curtains, screen, podium) across the top of each room
SESSION_DOOR_WIDTH = 72             # doorway of each session room (and the matching gap in the hall wall)
SESSION_ROOM_HEIGHT = 270           # art px (taller = more room for seats + sign; shorter = bigger main hall)
SESSION_SIGN_TEXT_SIZE = 20         # long names wrap onto extra lines automatically
SESSION_PLANTS = [(0.05, 0.86)]     # bottom-left corner
SESSION_FLOWER_PLANTS = []
SESSION_LAMPS = [(0.95, 0.86)]      # bottom-right corner

# --- main stage room (centred at the top of the main hall) ---
STAGE_TITLE = "MAIN STAGE"
STAGE_TITLE_SIZE = 22               # font size of the main stage sign
STAGE_ROOM_WIDTH, STAGE_ROOM_HEIGHT = 480, 350   # art px, including its walls (the stage spans the room)
STAGE_DEPTH = 120                   # depth of the raised stage inside the room
AUDIENCE_ROWS = 7                   # rows of chairs in front of the stage
AUDIENCE_SEATS_PER_ROW = 24         # chairs per row (split by a centre aisle)
AUDIENCE_CHAIR_SCALE = 2            # chair size (whole number)
AUDIENCE_GAP = 40                   # space between the stage front and the first row
STAGE_ROOM_CARPET = ("#9e4a5a", "#a8566a", "#843b4b")   # stripe 1, stripe 2, edge
STAGE_ROOM_SIDE_DOORS = True        # doors in the left/right walls as well as the front
STAGE_ROOM_DOOR_WIDTH = 150         # front doorway (towards the lobby)
STAGE_ROOM_SIDE_DOOR_WIDTH = 90     # side doorways
HALL_ENTRANCE_WIDTH = 120           # main entrance in the bottom wall of the hall
STAGE_ROOM_PLANTS = [(0.05, 0.93), (0.95, 0.93)]
STAGE_ROOM_LAMPS = [(0.04, 0.62), (0.96, 0.62)]

# --- lobby around the main entrance: open area to meet and mingle ---
LOBBY_WIDTH = 480                   # art px; it sits below the stage room, down to the entrance
LOBBY_RUG = ("#e9c9a0", "#efd3ad", "#d4ae80")
HALL_WELCOME_TEXT = "WELCOME, CASCA!"       # mat at the main entrance ("" for none)
ENTRANCE_LAMPS = True               # lamps either side of the welcome mat
# Couch area on the left of the lobby: big sofas, coffee tables and armchairs
# clumped together. The middle stays clear as the path from the entrance to the stage.
LOBBY_LOUNGE = True
LOBBY_LOUNGE_POSITION = (0.25, 0.40)  # (x, y) fraction of the lobby: centre of the couch area
LOBBY_LOUNGE_WIDE = True            # True = two sofas on each side (a bigger couch area)
LOBBY_LOUNGE_SCALE = 2              # size of the sofas/chairs/table (whole number)
LOBBY_LOUNGE_ARMCHAIRS = 4          # 0, 2 or 4
# Smaller chair sets on the right: a round table with two armchairs each
LOBBY_CHAIR_SETS = [(0.66, 0.26), (0.88, 0.26), (0.77, 0.55)]   # (x, y) fractions of the lobby
LOBBY_CHAIR_SET_SCALE = 1.8
# Other lobby furniture as (kind, x, y) fractions of the lobby. Kinds: sofa,
# sofa_plain, armchair, coffee_table, coffee_table_laptop, plant, flowers,
# floor_lamp, side_lamp, bookshelf, bamboo, programme_board, pingpong, bench.
LOBBY_FURNITURE = [
    ("plant", 0.04, 0.86), ("flowers", 0.96, 0.86),
]
# Programme board just in front of the welcome mat. It gets an action point
# whose pop-up shows programme.md - the same file the poster hall uses, so both
# programme boards always show the same information.
LOBBY_PROGRAMME_BOARD = True
LOBBY_PROGRAMME_BOARD_POSITION = (0.50, 0.63)   # (x, y) fraction of the lobby
PROGRAMME_FILE = "programme.md"

# --- discussion tables (in the open floor left and right of the stage room) ---
# One table per label, each with TABLE_SEATS chairs; labels sit on a name plate
# under the table and wrap onto extra lines. Tables fill the left grid first,
# row by row (left -> right), then the right grid.
TABLE_LABELS = ["Jobs in labs vs. academia", "Postdocs in Canada vs. USA",
                "Canadian ESO collaboration", "Power/pitfalls of AI", "Pokémon",
                "Science communication", "CASCA Climate", "Open table 3", "Open table 2", "Open table 1"]
# Optional per-table name-plate colours (default slate blue)
TABLE_LABEL_COLOURS = {"Pokémon": "#c0392b"}
TABLE_POSITIONS = None              # None = grid layout; or one (x, y) hall fraction per table
TABLE_SEATS = 10                    # chairs per table (2 = small round table for two)
TABLE_SCALE = 2.4                   # table + chair size: 1.0 = small (3.2 is the most that fits 2 columns)
TABLE_GRID_COLUMNS = 2
TABLE_LABEL_SIZE = 16               # font size of the table name plates              # columns of tables on each side of the stage room

# --- quiet room: a small walled room with soft seating, no talking ---
# It takes a spot in a table grid (the bottom-right spot of the left grid by
# default, next to the lobby). Listed in the coordinates CSV as type "room".
SHOW_QUIET_ROOM = True
QUIET_ROOM_LABEL = "QUIET ROOM"
QUIET_ROOM_NOTE = "shhh..."         # small sign under the title ("" for none)
QUIET_ROOM_SIDE = "left"            # which table grid it sits in: "left" or "right"
QUIET_ROOM_CARPET = ("#cfe3d0", "#d9ebd9", "#a9c9ab")
QUIET_ROOM_DOOR = "right"           # wall with the door: "top", "bottom", "left" or "right"
QUIET_ROOM_DOOR_WIDTH = 56
QUIET_ROOM_FURNITURE = [            # (kind, x, y) fractions of the quiet room
    ("armchair", 0.25, 0.38), ("armchair", 0.62, 0.38), ("armchair", 0.25, 0.56),
    ("bookshelf", 0.2, 0.9), ("plant", 0.72, 0.84),
]

# Extra decoration anywhere in the hall, as (x, y) fractions of the hall
HALL_PLANTS = []
HALL_FLOWER_PLANTS = []
HALL_FLOOR_LAMPS = []
HALL_TABLE_LAMPS = []
HALL_BAMBOO = []
HALL_BOOKSHELVES = []

# Stairs up to the poster hall (a separate HyHyve space). The stairs are
# listed in the coordinates CSV as type "link", so you can put a HyHyve action
# point on them that sends people to the poster-hall space.
SHOW_STAIRS = True
STAIRS_LABEL = "TO POSTER HALL"     # sign above the stairs ("\n" for two lines)
STAIRS_POSITION = None              # None = the last spot of a table grid (see STAIRS_SIDE); or (x, y) hall fraction
STAIRS_SIDE = "right"               # with STAIRS_POSITION = None: "right" = bottom-right spot, "left" = bottom-left
STAIRS_SIZE = (60, 54)              # art px
STAIRS_LABEL_SIZE = 14              # font size of the stairs sign

# Action points for the discussion tables: one per table, the size of the
# table and its chairs, so walking up to a table puts you in that table's
# group call. Written to hyhyve_session_hall_action_points.json.
WRITE_TABLE_ACTION_POINTS = True
TABLE_AP_PADDING = 10               # extra image px around each table's chairs
TABLE_AP_INCLUDE_LABEL = False      # True = the area also covers the name plate
TABLE_AP_CONTENT = "**{label}**\n\nPull up a chair and join the discussion!"   # {label} = topic
# Optional per-table pop-up content, replacing TABLE_AP_CONTENT for that table.
# For the Pokémon table, paste a link to the theme song (e.g. an official
# YouTube upload) into POKEMON_THEME_URL. HyHyve shows it in the table's
# pop-up when someone joins; whether it plays automatically is up to HyHyve.
POKEMON_THEME_URL = ""
TABLE_AP_CONTENT_OVERRIDES = {
    "Pokémon": "**Pokémon** - gotta chat 'em all!\n\n"
               + (f"[Play the theme song]({POKEMON_THEME_URL})" if POKEMON_THEME_URL
                  else "(theme song link goes here)"),
}
TABLE_AP_ANCHOR = "center"          # "center" or "topleft": how HyHyve places a point (test one first)

# Wall/hit map: a separate PNG with only the walls (black) and the doorways
# left open, same size as the background.
WRITE_HIT_MAP = True
HIT_MAP_TRANSPARENT = True          # HyHyve hit map: transparent = walkable, black = wall
# ========================================================================

k.set_size(MAP_WIDTH, MAP_HEIGHT)
k.MAT_SCALE = MAT_SCALE
k.LABEL_SIZE = TABLE_LABEL_SIZE
M, ROOM_GAP, CORRIDOR = 20, 16, 40

def layout():
    n = len(SESSION_ROOM_NAMES)
    rw = (k.W - 2 * M - (n - 1) * ROOM_GAP) / n
    rooms = {i + 1: (name, (round(M + i * (rw + ROOM_GAP)), M,
                             round(M + i * (rw + ROOM_GAP) + rw), M + SESSION_ROOM_HEIGHT))
             for i, name in enumerate(SESSION_ROOM_NAMES)}
    hall = (M, M + SESSION_ROOM_HEIGHT + CORRIDOR, k.W - M, k.H - M)
    hcx = (hall[0] + hall[2]) // 2
    sr_y0 = hall[1] + 24
    stage_room = (hcx - STAGE_ROOM_WIDTH // 2, sr_y0, hcx + STAGE_ROOM_WIDTH // 2, sr_y0 + STAGE_ROOM_HEIGHT)
    lobby = (hcx - LOBBY_WIDTH // 2, stage_room[3] + 16, hcx + LOBBY_WIDTH // 2, hall[3] - k.T - 1)
    return rooms, hall, stage_room, lobby

ROOMS, HALL, STAGE_ROOM, LOBBY = layout()

def frac(box, fx, fy):
    x0, y0, x1, y1 = box
    return round(x0 + fx * (x1 - x0)), round(y0 + fy * (y1 - y0))

def seats(cx, top, rows, per_row, max_w, max_h, dx=9, dy=11, label="", scale=1):
    """Centred block of chairs with a centre aisle, squeezed to fit if needed.
    scale enlarges the chairs (and their spacing) by a whole number."""
    if rows <= 0 or per_row <= 0:
        return (cx, top, cx, top)
    dx, dy = dx * scale, dy * scale
    cw, ch = 6 * scale, 5 * scale
    aisle = 6 * scale if per_row > 3 else 0
    if per_row > 1:
        dx = min(dx, (max_w - 6 - aisle) / (per_row - 1))
    if rows > 1:
        dy = min(dy, (max_h - 5) / (rows - 1))
    if dx < cw + 1 or dy < ch + 1:
        print(f"warning: {label}: {rows} x {per_row} chairs is too many for the space; they will overlap")
    width = (per_row - 1) * dx + aisle + cw
    x_start = cx - width / 2
    half = per_row // 2
    for r in range(rows):
        for c in range(per_row):
            x = x_start + c * dx + (aisle if c >= half else 0)
            k.chair(round(x), round(top + r * dy), scale)
    return (round(x_start), top, round(x_start + width), round(top + (rows - 1) * dy + ch))

def side_zones():
    """Open floor left and right of the stage room and lobby, as (x0, y0, x1, y1) art px."""
    hx0, hy0, hx1, hy1 = HALL
    inner = 24                                   # walkway kept next to the stage room / lobby
    xl = min(STAGE_ROOM[0], LOBBY[0]) - inner
    xr = max(STAGE_ROOM[2], LOBBY[2]) + inner
    left = (hx0 + k.T + 2, hy0 + k.T + 4, xl, hy1 - k.T - 2)
    right = (xr, hy0 + k.T + 4, hx1 - k.T - 2, hy1 - k.T - 2)
    return left, right

def grid_slots(zone, n, cols):
    """n cell centres in a cols-wide grid filling zone (row by row from the top)."""
    if n <= 0:
        return [], 0, 0
    x0, y0, x1, y1 = zone
    cols = max(1, min(cols, n))
    rows = math.ceil(n / cols)
    cw = (x1 - x0) / cols
    rh = (y1 - y0) / rows
    out = [(round(x0 + cw * (i % cols + 0.5)), round(y0 + rh * (i // cols + 0.5))) for i in range(n)]
    return out, cw, rh

def table_layout(n):
    """Cell centres for n tables, plus the cells reserved for the stairs and the
    quiet room, and the label width for the grid.
    Returns (table_cells, stairs_cell, quiet_cell, label_w, cell_size)."""
    left, right = side_zones()
    want = {"left": [], "right": []}               # reserved spots per side (in order)
    if SHOW_QUIET_ROOM:
        want["left" if QUIET_ROOM_SIDE != "right" else "right"].append("quiet")
    if SHOW_STAIRS and STAIRS_POSITION is None:
        want["right" if STAIRS_SIDE == "right" else "left"].append("stairs")
    # split tables so both sides end up with the same number of spots where possible
    total = n + len(want["left"]) + len(want["right"])
    spots_left = (total + 1) // 2
    n_left = max(0, min(n, spots_left - len(want["left"])))
    n_right = n - n_left
    cells = {}
    sizes = []
    for side, zone, nt in (("left", left, n_left), ("right", right, n_right)):
        slots, cw, rh = grid_slots(zone, nt + len(want[side]), TABLE_GRID_COLUMNS)
        sizes.append((cw, rh))
        # reserved spots take the last cells (bottom row); stairs go in the outer corner
        res = want[side]
        if res:
            last = slots[-len(res):]
            slots = slots[:-len(res)]
            for name, cell in zip(res, last):
                cells[name] = cell
            if "stairs" in res and side == "right" and len(last) == 1 and nt % TABLE_GRID_COLUMNS:
                # move the stairs to the bottom-right corner of the grid
                x_last = zone[0] + (zone[2] - zone[0]) * (TABLE_GRID_COLUMNS - 0.5) / TABLE_GRID_COLUMNS
                cells["stairs"] = (round(x_last), last[0][1])
        cells[side] = slots
    cw = min(c for c, _ in sizes if c) if any(c for c, _ in sizes) else 100
    rh = min(r for _, r in sizes if r) if any(r for _, r in sizes) else 100
    label_w = int(cw) - 16
    return cells["left"] + cells["right"], cells.get("stairs"), cells.get("quiet"), label_w, (cw, rh)

def quiet_room(cell, cell_size, areas):
    cx, cy = cell
    cw, rh = cell_size
    hw, hh = int(cw / 2) - 10, int(rh / 2) - 10
    box = (cx - hw, cy - hh, cx + hw, cy + hh)
    x0, y0, x1, y1 = box
    k.striped_rug(x0, y0, x1, y1, *QUIET_ROOM_CARPET)
    along = {"top": cx, "bottom": cx, "left": cy, "right": cy}[QUIET_ROOM_DOOR]
    k.room_walls(x0, y0, x1, y1, [(QUIET_ROOM_DOOR, along, QUIET_ROOM_DOOR_WIDTH)])
    for kind, fx, fy in QUIET_ROOM_FURNITURE:
        k.furniture(kind, *frac(box, fx, fy))
    title_h = k.sign_height(QUIET_ROOM_LABEL, 10)
    k.sign(cx, y0 + k.T + 4 + title_h // 2, QUIET_ROOM_LABEL, "#4e7a5a", 10)
    if QUIET_ROOM_NOTE:
        k.text(cx, y0 + k.T + 8 + title_h + 6, QUIET_ROOM_NOTE, 9, "#3c5a44")
    areas.append(("room", QUIET_ROOM_LABEL.title(), box))

def session_room(i, name, box):
    x0, y0, x1, y1 = box
    c1, c2, edge, accent = k.ROOM_COLOURS[(i - 1) % len(k.ROOM_COLOURS)]
    cx = (x0 + x1) // 2
    k.striped_rug(x0, y0, x1, y1, c1, c2, edge)
    k.room_walls(x0, y0, x1, y1, [("bottom", cx, SESSION_DOOR_WIDTH)])
    k.DECOR_SCALE = DECOR_SCALE
    stg = (x0 + 12, y0 + k.T + 6, x1 - 12, y0 + k.T + 6 + SESSION_STAGE_DEPTH)
    k.stage(*stg, title=None, podium_offset=(x1 - x0) // 4, accent=accent)
    # sign at the bottom (door) wall: wrap the text until it fits the room
    name, sz = k.fit_label(name, (x1 - x0) - 12, SESSION_SIGN_TEXT_SIZE, max(9, SESSION_SIGN_TEXT_SIZE - 4))
    sh, sgw = k.sign_height(name, sz), k.sign_width(name, sz)
    sy = y1 - 6 - sh + sh // 2
    sign_top = sy - sh // 2
    def clear(x, y, half_w=6):   # move decor that would sit under the sign up above it
        if abs(x - cx) < sgw // 2 + half_w * DECOR_SCALE and y > sign_top - 12 * DECOR_SCALE:
            y = sign_top - 12 * DECOR_SCALE
        return x, y
    for fx, fy in SESSION_LAMPS:
        x, y = clear(*frac(box, fx, fy)); k.floor_lamp(x - 2, y - 10)
    for fx, fy in SESSION_PLANTS:
        x, y = clear(*frac(box, fx, fy)); k.plant(x - 5, y - 6)
    for fx, fy in SESSION_FLOWER_PLANTS:
        x, y = clear(*frac(box, fx, fy)); k.plant(x - 5, y - 6, flowers=True)
    seat_top = stg[3] + 14
    avail = (sign_top - 14) - seat_top
    rows = SESSION_ROWS
    cs = SESSION_CHAIR_SCALE
    while rows > 1 and (avail - 5 * cs) / (rows - 1) < 7 * cs:   # drop rows that won't fit above the sign
        rows -= 1
    if rows < SESSION_ROWS:
        print(f"note: {one_line(name)}: only room for {rows} rows of chairs above its sign")
    seats(cx, seat_top, rows, SESSION_SEATS_PER_ROW, (x1 - x0) - 40, avail, label=one_line(name), scale=cs)
    k.sign(cx, sy, name, accent, sz)

def stage_room(areas):
    x0, y0, x1, y1 = STAGE_ROOM
    cx = (x0 + x1) // 2
    k.striped_rug(x0, y0, x1, y1, *STAGE_ROOM_CARPET)
    doors = [("bottom", cx, STAGE_ROOM_DOOR_WIDTH)]
    if STAGE_ROOM_SIDE_DOORS:
        dy = round(y0 + (y1 - y0) * 0.8)
        doors += [("left", dy, STAGE_ROOM_SIDE_DOOR_WIDTH), ("right", dy, STAGE_ROOM_SIDE_DOOR_WIDTH)]
    k.room_walls(x0, y0, x1, y1, doors)
    for fx, fy in STAGE_ROOM_LAMPS:
        k.furniture("floor_lamp", *frac(STAGE_ROOM, fx, fy))
    for fx, fy in STAGE_ROOM_PLANTS:
        k.furniture("plant", *frac(STAGE_ROOM, fx, fy))
    stage = (x0 + 22, y0 + k.T + 8, x1 - 22, y0 + k.T + 8 + STAGE_DEPTH)
    k.stage(*stage, title=STAGE_TITLE, title_size=STAGE_TITLE_SIZE)
    areas.append(("stage", STAGE_TITLE.title(), stage))
    top = stage[3] + AUDIENCE_GAP
    bottom = y1 - k.T - 16
    aud = seats(cx, top, AUDIENCE_ROWS, AUDIENCE_SEATS_PER_ROW, (x1 - x0) - 90, bottom - top,
                dx=9, dy=12, label="audience", scale=AUDIENCE_CHAIR_SCALE)
    areas.append(("zone", "Stage audience", aud))
    areas.append(("room", "Main stage room", STAGE_ROOM))

extra_points = []          # programme board etc., written with the table action points

def lobby(areas):
    lx0, ly0, lx1, ly1 = LOBBY
    lcx = (lx0 + lx1) // 2
    k.striped_rug(lx0, ly0, lx1, ly1, *LOBBY_RUG)
    for kind, fx, fy in LOBBY_FURNITURE:
        k.furniture(kind, *frac(LOBBY, fx, fy))
    if LOBBY_PROGRAMME_BOARD:
        bx, by = frac(LOBBY, *LOBBY_PROGRAMME_BOARD_POSITION)
        k.furniture("programme_board", bx, by)
        areas.append(("board", "Programme board", (bx - 16, by - 13, bx + 16, by + 13)))
        extra_points.append(k.action_point((bx * k.P, by * k.P), "Programme",
                                           k.programme_content(PROGRAMME_FILE), (260, 240)))
    if LOBBY_LOUNGE:
        k.lounge_clump(*frac(LOBBY, *LOBBY_LOUNGE_POSITION), scale=LOBBY_LOUNGE_SCALE,
                       armchairs=LOBBY_LOUNGE_ARMCHAIRS, wide=LOBBY_LOUNGE_WIDE)
    for fx, fy in LOBBY_CHAIR_SETS:
        k.chair_set(*frac(LOBBY, fx, fy), LOBBY_CHAIR_SET_SCALE)
    mat_half = 0
    if HALL_WELCOME_TEXT:
        _, mw, _ = k.mat_size(HALL_WELCOME_TEXT, max_w=260)
        mat_half = mw // 2
        k.welcome_mat(lcx, label=HALL_WELCOME_TEXT, max_w=260, bottom=ly1 - 4)
    if ENTRANCE_LAMPS:
        off = max(44, mat_half + 10 + 4 * DECOR_SCALE)
        k.floor_lamp(lcx - off - 2, ly1 - 26); k.floor_lamp(lcx + off - 2, ly1 - 26)
    areas.append(("zone", "Lobby", LOBBY))

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
    doors = [("top", (b[0] + b[2]) // 2, SESSION_DOOR_WIDTH + 8) for _, b in ROOMS.values()]
    k.room_walls(hx0, hy0, hx1, hy1, doors + [("bottom", hcx, HALL_ENTRANCE_WIDTH)])

    k.DECOR_SCALE = HALL_DECOR_SCALE
    # extra hall decoration first, so furniture draws on top
    for fx, fy in HALL_FLOOR_LAMPS:
        k.furniture("floor_lamp", *frac(HALL, fx, fy))
    for fx, fy in HALL_TABLE_LAMPS:
        k.furniture("side_lamp", *frac(HALL, fx, fy))
    for fx, fy in HALL_BAMBOO:
        k.furniture("bamboo", *frac(HALL, fx, fy))
    for fx, fy in HALL_BOOKSHELVES:
        k.furniture("bookshelf", *frac(HALL, fx, fy))
    for fx, fy in HALL_PLANTS:
        k.furniture("plant", *frac(HALL, fx, fy))
    for fx, fy in HALL_FLOWER_PLANTS:
        k.furniture("flowers", *frac(HALL, fx, fy))

    lobby(areas)
    stage_room(areas)

    # discussion tables (and the stairs spot) either side of the stage room
    cells, stairs_xy, quiet_xy, label_w, cell_size = table_layout(len(TABLE_LABELS))
    if SHOW_QUIET_ROOM and quiet_xy:
        quiet_room(quiet_xy, cell_size, areas)
    if TABLE_POSITIONS:
        positions = [frac(HALL, fx, fy) for fx, fy in TABLE_POSITIONS]
        if len(positions) < len(TABLE_LABELS):
            print("warning: fewer TABLE_POSITIONS than TABLE_LABELS; extra tables skipped")
    else:
        positions = cells
    table_points = []
    for label, (cx, cy) in zip(TABLE_LABELS, positions):
        half, above, below = k.group_table_extent(TABLE_SEATS, label, TABLE_SCALE, label_w)
        if half > label_w // 2 + 16:
            print(f"note: table {one_line(label)!r} is wider than its grid spot; "
                  "lower TABLE_SCALE or TABLE_GRID_COLUMNS")
        cy = round(cy - (above + below) / 2 + above)    # centre table + name plate in the cell
        k.group_table(cx, cy, TABLE_SEATS, label, TABLE_SCALE, label_max_w=label_w,
                      label_colour=TABLE_LABEL_COLOURS.get(label, "#46606b"))
        areas.append(("table", f"Table {one_line(label)}", (cx - half, cy - above, cx + half, cy + below)))
        # action point covering the table + chairs (optionally its name plate too)
        th, ta, tb = k.group_table_extent(TABLE_SEATS, None, TABLE_SCALE)
        bx0, by0 = (cx - th) * k.P - TABLE_AP_PADDING, (cy - ta) * k.P - TABLE_AP_PADDING
        bx1 = (cx + th) * k.P + TABLE_AP_PADDING
        by1 = (cy + (below if TABLE_AP_INCLUDE_LABEL else tb)) * k.P + TABLE_AP_PADDING
        w, h = bx1 - bx0, by1 - by0
        pos = ((bx0 + bx1) // 2, (by0 + by1) // 2) if TABLE_AP_ANCHOR == "center" else (bx0, by0)
        table_points.append(k.action_point(pos, one_line(label),
                                           TABLE_AP_CONTENT_OVERRIDES.get(label,
                                               TABLE_AP_CONTENT.format(label=one_line(label))), (w, h)))

    if SHOW_STAIRS:
        sx, sy = frac(HALL, *STAIRS_POSITION) if STAIRS_POSITION is not None else stairs_xy
        # keep the stairs and their sign inside the hall walls
        half = max(STAIRS_SIZE[0], k.sign_width(STAIRS_LABEL, STAIRS_LABEL_SIZE)) // 2 + 2
        sx = max(hx0 + k.T + half, min(hx1 - k.T - half, sx))
        box = k.stairs(sx, sy + 10, *STAIRS_SIZE, label=STAIRS_LABEL, label_colour="#2f3640",
                       label_size=STAIRS_LABEL_SIZE)
        areas.append(("link", one_line(STAIRS_LABEL).title(), box))
    areas.append(("room", "Main Hall", HALL))

    size = f"{k.W * k.P}x{k.H * k.P}"
    k.save(f"hyhyve_session_hall_{size}.png", areas, "hyhyve_session_hall_coordinates.csv")
    if WRITE_HIT_MAP:
        k.save_hit_map(f"hyhyve_session_hall_walls_{size}.png", HIT_MAP_TRANSPARENT)
    points = (table_points if WRITE_TABLE_ACTION_POINTS else []) + extra_points
    if points:
        import json
        with open("hyhyve_session_hall_action_points.json", "w", encoding="utf-8") as f:
            json.dump(points, f, indent=4, ensure_ascii=False)
        print(f"saved hyhyve_session_hall_action_points.json ({len(points)} action points: "
              f"{len(points) - len(extra_points)} tables + {len(extra_points)} programme board)")

if __name__ == "__main__":
    main()
