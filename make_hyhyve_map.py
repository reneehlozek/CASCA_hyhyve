"""
HyHyve poster-space background, pixel-art ("old PC") style.

Everything is drawn on a small canvas (1/P of the final size) and scaled up
with nearest-neighbour resampling, so every "pixel" is a crisp P x P block.

Final size: 3150 x 2100 px.   Requires: pip install pillow
Run:  python make_hyhyve_map.py   -> writes hyhyve_poster_space_3150x2100.png
"""
from PIL import Image, ImageDraw, ImageFont

P = 5                        # size of one art pixel in final-image pixels
W, H = 3150 // P, 2100 // P  # low-res canvas: 630 x 420
OUT = "hyhyve_poster_space_3150x2100.png"

im = Image.new("RGB", (W, H))
g = ImageDraw.Draw(im, "RGBA")
g.fontmode = "1"             # no anti-aliasing -> pixel-crisp text

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # change if needed
def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except OSError:
        return ImageFont.load_default()

OL = "#3a2e3c"               # dark outline used on all sprites

# ------------------------------------------------------------------ helpers
def R(x0, y0, x1, y1, fill, ol=None):
    g.rectangle([x0, y0, x1, y1], fill=fill, outline=ol)

def shadow(x0, y0, x1, y1):
    g.rectangle([x0 + 1, y1 + 1, x1 + 1, y1 + 2], fill=(40, 30, 70, 70))

def text(x, y, s, sz, fill="white", stroke=None):
    g.text((x, y), s, font=font(sz), fill=fill, anchor="mm",
           stroke_width=1 if stroke else 0, stroke_fill=stroke)

def sign(cx, cy, s, bg, sz=11):
    """Pixel name plate: dark outline, coloured face, light top edge."""
    f = font(sz)
    l, t, r, b = g.textbbox((0, 0), s, font=f)
    w = (r - l) // 2 + 6
    shadow(cx - w, cy - 8, cx + w, cy + 8)
    R(cx - w, cy - 8, cx + w, cy + 8, bg, OL)
    g.line([(cx - w + 1, cy - 7), (cx + w - 1, cy - 7)], fill=(255, 255, 255, 90))
    g.line([(cx - w + 1, cy + 7), (cx + w - 1, cy + 7)], fill=(0, 0, 0, 60))
    text(cx, cy, s, sz)

def glow(cx, cy, r):
    for k, a in ((r, 26), (int(r * 0.7), 32), (int(r * 0.4), 40)):
        g.ellipse([cx - k, cy - k, cx + k, cy + k], fill=(255, 226, 150, a))

# ------------------------------------------------------------------ floors & walls
def wood_floor(x0, y0, x1, y1):
    R(x0, y0, x1, y1, "#d8c09a")
    for i, y in enumerate(range(y0, y1, 6)):
        g.line([(x0, y), (x1, y)], fill="#c7ad84")
        off = (i * 17) % 40
        for x in range(x0 + off, x1, 40):
            g.line([(x, y), (x, y + 5)], fill="#c7ad84")
        for x in range(x0 + off + 9, x1, 40):
            g.point((x, y + 3), fill="#cdb48c")

def striped_rug(x0, y0, x1, y1, c1, c2, edge):
    R(x0, y0, x1, y1, c1)
    for x in range(x0, x1, 12):
        R(x, y0, min(x + 5, x1), y1, c2)
    for x in range(x0 + 6, x1, 12):
        for y in range(y0, y1, 2):
            g.point((x + (y // 2) % 2, y), fill=c2)
    g.rectangle([x0, y0, x1, y1], outline=edge)

def tile_floor(x0, y0, x1, y1, c1, c2):
    R(x0, y0, x1, y1, c1)
    for y in range(y0, y1, 8):
        for x in range(x0 + ((y - y0) // 8 % 2) * 8, x1, 16):
            R(x, y, min(x + 7, x1), min(y + 7, y1), c2)

T = 5  # wall thickness
def wall_seg(x0, y0, x1, y1):
    """Cream brick wall block."""
    if x1 < x0 or y1 < y0:
        return
    R(x0, y0, x1, y1, "#f3e9d6")
    for y in range(y0, y1 + 1, 3):
        off = 0 if ((y - y0) // 3) % 2 == 0 else 3
        g.line([(x0, y), (x1, y)], fill="#d9c8a8")
        for x in range(x0 - off, x1 + 1, 6):
            if x >= x0:
                g.line([(x, y), (x, min(y + 2, y1))], fill="#d9c8a8")
    g.rectangle([x0, y0, x1, y1], outline="#6b5a48")

def room_walls(x0, y0, x1, y1, doors):
    """doors: list of (side, centre, width), side in top/bottom/left/right."""
    def run(a, b, side):
        gaps = sorted((c - w // 2, c + w // 2) for s, c, w in doors if s == side)
        segs, cur = [], a
        for ga, gb in gaps:
            segs.append((cur, ga - 1)); cur = gb + 1
        segs.append((cur, b))
        return segs
    for a, b in run(x0, x1, "top"):
        wall_seg(a, y0, b, y0 + T - 1)
    for a, b in run(x0, x1, "bottom"):
        wall_seg(a, y1 - T + 1, b, y1)
    for a, b in run(y0, y1, "left"):
        wall_seg(x0, a, x0 + T - 1, b)
    for a, b in run(y0, y1, "right"):
        wall_seg(x1 - T + 1, a, x1, b)

# ------------------------------------------------------------------ furniture sprites
def sofa(x, y, wd=34, ht=13, cushions=True):
    shadow(x, y, x + wd, y + ht)
    R(x, y, x + wd, y + ht, "#e8c48f", OL)
    R(x + 1, y + 1, x + wd - 1, y + 4, "#d6aa6e")
    R(x + 1, y + 1, x + 3, y + ht - 1, "#d6aa6e")
    R(x + wd - 3, y + 1, x + wd - 1, y + ht - 1, "#d6aa6e")
    g.line([(x + wd // 2, y + 5), (x + wd // 2, y + ht - 2)], fill="#c89a5e")
    R(x + 4, y + ht - 2, x + wd - 4, y + ht - 2, "#f3d7aa")
    if cushions:
        for cx in (x + 6, x + wd - 12):
            R(cx, y + 3, cx + 5, y + 8, "#f2f2f2", OL)
            g.line([(cx + 1, y + 5), (cx + 4, y + 5)], fill="#8a8a9a")
            g.line([(cx + 1, y + 7), (cx + 4, y + 7)], fill="#8a8a9a")

def armchair(x, y, sz=10):
    shadow(x, y, x + sz, y + sz + 1)
    R(x, y, x + sz, y + sz + 1, "#f08a2a", OL)
    R(x + 1, y + 1, x + sz - 1, y + 3, "#c9681a")
    R(x + 1, y + 1, x + 2, y + sz, "#c9681a")
    R(x + sz - 2, y + 1, x + sz - 1, y + sz, "#c9681a")
    R(x + 3, y + 5, x + sz - 3, y + sz - 1, "#f7a54e")

def side_lamp(x, y):
    glow(x + 4, y + 2, 14)
    shadow(x, y + 6, x + 8, y + 12)
    R(x, y + 6, x + 8, y + 12, "#3f4652", OL)
    R(x + 1, y + 7, x + 7, y + 8, "#555d6b")
    R(x + 3, y + 3, x + 5, y + 6, "#8a4b26")
    g.polygon([(x + 1, y + 3), (x + 7, y + 3), (x + 6, y - 2), (x + 2, y - 2)], fill="#f5a13a", outline=OL)
    g.line([(x + 3, y - 1), (x + 3, y + 2)], fill="#ffd27a")

def floor_lamp(x, y):
    glow(x + 2, y + 1, 16)
    g.ellipse([x - 1, y + 16, x + 5, y + 18], fill=(40, 30, 70, 70))
    R(x, y + 15, x + 4, y + 16, "#3f4652", OL)
    g.line([(x + 2, y + 4), (x + 2, y + 15)], fill="#3f4652")
    g.polygon([(x - 2, y + 4), (x + 6, y + 4), (x + 5, y - 2), (x - 1, y - 2)], fill="#f5a13a", outline=OL)
    g.line([(x, y - 1), (x, y + 3)], fill="#ffd27a")

def plant(x, y, flowers=False):
    g.ellipse([x - 1, y + 10, x + 11, y + 13], fill=(40, 30, 70, 70))
    R(x + 1, y + 6, x + 9, y + 12, "#3f4652", OL)
    R(x + 2, y + 7, x + 8, y + 7, "#555d6b")
    if flowers:
        R(x + 3, y + 3, x + 7, y + 6, "#f4f4f4", OL)
        g.line([(x + 5, y + 3), (x + 5, y - 2)], fill="#7a3a3a")
        for fx, fy in ((x + 2, y - 3), (x + 7, y - 4), (x + 5, y - 5), (x + 9, y - 1)):
            R(fx, fy, fx + 1, fy + 1, "#f06aa8")
        return
    for lx, ly, c in ((x - 2, y - 2, "#3f8a3a"), (x + 5, y - 5, "#4fa345"), (x + 7, y, "#3f8a3a"),
                      (x + 1, y - 6, "#5cb850"), (x + 3, y + 1, "#5cb850")):
        g.ellipse([lx, ly, lx + 6, ly + 5], fill=c, outline="#2c5a2a")

def bamboo(x, y, wd=26, ht=16):
    shadow(x, y, x + wd, y + ht)
    R(x, y + 8, x + wd, y + ht, "#3f4652", OL)
    R(x + 1, y + 8, x + wd - 1, y + 10, "#9aa0a8")
    for i, sx in enumerate(range(x + 2, x + wd - 1, 3)):
        top = y - 8 + (i * 5) % 6
        g.line([(sx, top), (sx, y + 9)], fill="#4fa345")
        for ly in range(top + 1, y + 8, 4):
            g.point((sx, ly), fill="#2f7a2c")
            g.line([(sx + 1, ly - 1), (sx + 2, ly - 2)], fill="#6cc860")

def pingpong(x, y, wd=24, ht=30):
    shadow(x, y, x + wd, y + ht)
    R(x, y, x + wd, y + ht, "#4aa35a", "#f4f4f4")
    g.line([(x + wd // 2, y), (x + wd // 2, y + ht)], fill="#f4f4f4")
    R(x - 2, y + ht // 2 - 1, x + wd + 2, y + ht // 2 + 1, "#555d6b", OL)

def coffee_table(x, y, laptop=True):
    shadow(x, y, x + 22, y + 9)
    R(x, y, x + 22, y + 9, "#3f4652", OL)
    R(x + 1, y + 1, x + 21, y + 2, "#555d6b")
    R(x + 3, y + 4, x + 6, y + 7, "#e8e8e8", OL)
    if laptop:
        R(x + 11, y - 3, x + 19, y + 2, "#f4f4f4", OL)
        R(x + 12, y - 2, x + 18, y + 1, "#5a8fe0")
        R(x + 10, y + 3, x + 20, y + 7, "#dcdcdc", OL)
        g.line([(x + 12, y + 5), (x + 18, y + 5)], fill="#9a9aa6")

def bookshelf(x, y, wd=26, ht=30):
    shadow(x, y, x + wd, y + ht)
    R(x, y, x + wd, y + ht, "#8a5a34", OL)
    cols = ["#d9534f", "#5a8fe0", "#f0c040", "#4aa35a", "#9b6bd6", "#f08a2a"]
    for sy in range(y + 2, y + ht - 3, 7):
        R(x + 1, sy + 5, x + wd - 1, sy + 5, "#5e3b20")
        bx, i = x + 2, sy
        while bx < x + wd - 2:
            bw = 1 + (i % 2)
            R(bx, sy + (i % 3 == 0), bx + bw - 1, sy + 4, cols[i % len(cols)])
            bx += bw + 1; i += 1

def wood_table(x0, y0, x1, y1):
    shadow(x0, y0, x1, y1)
    R(x0, y0, x1, y1, "#a86f40", OL)
    R(x0 + 1, y0 + 1, x1 - 1, y1 - 2, "#c28651")
    for ly in range(y0 + 3, y1 - 2, 4):
        g.line([(x0 + 3, ly), (x1 - 3, ly)], fill="#b57a47")

def small_chair(x, y):
    R(x, y, x + 5, y + 4, "#f08a2a", OL)
    g.line([(x + 1, y + 1), (x + 4, y + 1)], fill="#c9681a")

def poster_board(cx, y, accent, num, bw=24, bh=28):
    x0 = cx - bw // 2
    g.line([(x0 + 3, y + bh), (x0 + 1, y + bh + 3)], fill="#6b4a2c")          # easel legs
    g.line([(x0 + bw - 3, y + bh), (x0 + bw - 1, y + bh + 3)], fill="#6b4a2c")
    shadow(x0, y, x0 + bw, y + bh)
    R(x0, y, x0 + bw, y + bh, "#8a5a34", OL)              # frame
    R(x0 + 2, y + 2, x0 + bw - 2, y + bh - 2, "#fbfbf6")  # sheet
    R(x0 + 3, y + 3, x0 + bw - 3, y + 6, accent)          # title bar
    R(x0 + 3, y + 9, x0 + 11, y + 15, "#cfd6e4")          # figure
    g.line([(x0 + 4, y + 14), (x0 + 7, y + 11), (x0 + 10, y + 13)], fill=accent)
    for ly in range(y + 9, y + 16, 2):
        g.line([(x0 + 13, ly), (x0 + bw - 4, ly)], fill="#c9ccd2")
    for ly in range(y + 18, y + bh - 3, 2):
        g.line([(x0 + 4, ly), (x0 + bw - 4, ly)], fill="#c9ccd2")
    text(cx, y + bh + 7, num, 8, "#2b2f36")

def help_desk(cx, y):
    shadow(cx - 26, y, cx + 26, y + 10)
    R(cx - 26, y, cx + 26, y + 10, "#6b7280", OL)
    R(cx - 25, y + 1, cx + 25, y + 3, "#8c94a3")
    R(cx + 12, y - 5, cx + 20, y + 1, "#f4f4f4", OL)      # monitor
    R(cx + 13, y - 4, cx + 19, y, "#5a8fe0")
    R(cx - 20, y - 2, cx - 16, y + 1, "#f06aa8", OL)      # bell

# ------------------------------------------------------------------ background
wood_floor(0, 0, W - 1, H - 1)

rooms = []  # (name, (x0, y0, x1, y1)) in canvas units; printed in final px at the end

POSTER = [  # (rug colour 1, rug colour 2, rug edge, sign/accent colour)
    ("#cfe0f3", "#d9e8f8", "#aac4e3", "#3b7dc4"),
    ("#d6ebcf", "#e0f1da", "#b3d6a8", "#4e9a3f"),
    ("#f5e0c8", "#f9e9d6", "#e6c49c", "#d0822c"),
    ("#e4d5ef", "#ecdff5", "#cbb5e0", "#8b5bb5"),
    ("#f3d3d8", "#f8dfe3", "#e3adb6", "#c84a5a"),
]

def poster_room(i, box, door):
    x0, y0, x1, y1 = box
    c1, c2, edge, accent = POSTER[i]
    cx = (x0 + x1) // 2
    striped_rug(x0, y0, x1, y1, c1, c2, edge)
    room_walls(x0, y0, x1, y1, [(door, cx, 40)])
    iw = x1 - x0
    xs = [x0 + iw * (k + 1) // 4 for k in range(3)]
    if door == "bottom":
        sign_y, rows, pl_y, ly = y0 + 15, (y0 + 29, y0 + 70), y1 - 22, y1 - 26
    else:
        sign_y, rows, pl_y, ly = y1 - 15, (y0 + 12, y0 + 53), y0 + 12, y0 + 10
    n = 1
    for ry in rows:
        for bx in xs:
            poster_board(bx, ry, accent, f"{i + 1}.{n}")
            n += 1
    sign(cx, sign_y, f"POSTER ROOM {i + 1}", accent, 10)
    plant(x0 + 8, pl_y)           # plant in one door-side corner
    floor_lamp(x1 - 12, ly)       # lamp in the other
    rooms.append((f"Poster Room {i + 1}", box))

poster_room(0, (14, 14, 166, 138), "bottom")    # top row, doors face down
poster_room(1, (178, 14, 330, 138), "bottom")
poster_room(2, (342, 14, 494, 138), "bottom")
poster_room(3, (14, 282, 166, 406), "top")      # bottom row, doors face up
poster_room(4, (342, 282, 494, 406), "top")

# ------------------------------------------------------------------ entrance
ex0, ey0, ex1, ey1 = 178, 314, 330, 406
ecx = (ex0 + ex1) // 2
tile_floor(ex0, ey0, ex1, ey1, "#efe9dc", "#e5dccb")
room_walls(ex0, ey0, ex1, ey1, [("top", ecx, 70)])
R(ecx - 30, ey0 + 9, ecx + 30, ey0 + 24, "#b04a4a", OL)       # welcome mat
g.rectangle([ecx - 28, ey0 + 11, ecx + 28, ey0 + 22], outline="#d97a6a")
text(ecx, ey0 + 17, "WELCOME", 8, "#fbe9d8")
R(ex0 + 12, ey0 + 30, ex0 + 44, ey0 + 56, "#8a5a34", OL)      # programme board
R(ex0 + 14, ey0 + 32, ex0 + 42, ey0 + 52, "#2f4a3a")
for ly in range(ey0 + 36, ey0 + 50, 3):
    g.line([(ex0 + 17, ly), (ex0 + 39, ly)], fill="#d8e6dc")
text(ex0 + 28, ey0 + 62, "PROGRAMME", 7, "#2b2f36")
help_desk(ecx + 20, ey0 + 46)
plant(ex1 - 18, ey0 + 12, flowers=True)
floor_lamp(ex1 - 14, ey0 + 34)
sign(ecx, ey1 - 15, "ENTRANCE / HELP", "#2f3640")
rooms.append(("Entrance / Welcome", (ex0, ey0, ex1, ey1)))

# ------------------------------------------------------------------ central lounge / meeting area
cx0, cy0, cx1, cy1 = 50, 164, 458, 256
w, h = cx1 - cx0, cy1 - cy0
wall_seg(cx0, cy0, cx1, cy1)                               # brick border
striped_rug(cx0 + 4, cy0 + 4, cx1 - 4, cy1 - 4, "#8e8fdc", "#9a9be6", "#7475c4")

def at(x, y):  # lounge-local coords -> canvas coords
    return cx0 + x, cy0 + y

bamboo(*at(8, 12))
pingpong(*at(10, h - 40))
side_lamp(*at(52, 9)); sofa(*at(64, 8)); armchair(*at(102, 9))
armchair(*at(56, 36)); coffee_table(*at(72, 38), laptop=False)
plant(*at(46, h - 20)); sofa(*at(64, h - 21), cushions=False); armchair(*at(102, h - 21))
floor_lamp(*at(124, h - 26))
mt_w, mt_h = 84, 22
mx, my = w // 2 - mt_w // 2, h // 2 - mt_h // 2
floor_lamp(*at(mx - 22, 10)); floor_lamp(*at(mx + mt_w + 18, 10))
plant(*at(mx - 26, h - 20)); plant(*at(mx + mt_w + 16, h - 20), flowers=True)
for x in range(mx + 6, mx + mt_w - 4, 12):
    small_chair(*at(x, my - 6)); small_chair(*at(x, my + mt_h + 2))
for y in range(my + 4, my + mt_h - 4, 9):
    R(*at(mx - 6, y), *at(mx - 2, y + 5), "#f08a2a", OL)
    R(*at(mx + mt_w + 2, y), *at(mx + mt_w + 6, y + 5), "#f08a2a", OL)
wood_table(*at(mx, my), *at(mx + mt_w, my + mt_h))
rx = w - 120
side_lamp(*at(rx - 12, 9)); sofa(*at(rx, 8)); armchair(*at(rx + 38, 9))
coffee_table(*at(rx + 6, 40)); armchair(*at(rx + 34, 38))
sofa(*at(rx, h - 21), cushions=False); plant(*at(rx + 40, h - 20), flowers=True)
floor_lamp(*at(rx + 54, h - 26))
plant(*at(w - 34, 10)); bookshelf(*at(w - 44, h - 42))
sign((cx0 + cx1) // 2, (cy0 + cy1) // 2, "MEETING AREA", "#5a3b22", 9)
rooms.append(("Central Meeting Area", (cx0, cy0, cx1, cy1)))

# ------------------------------------------------------------------ private tables (seat 4)
for i, letter in enumerate("ABCD"):
    x0, y0 = 512, 14 + i * 100
    x1, y1 = 616, y0 + 92
    tile_floor(x0, y0, x1, y1, "#dde6ea", "#d2dde2")
    room_walls(x0, y0, x1, y1, [("left", (y0 + y1) // 2, 28)])
    tcx, tcy = (x0 + x1) // 2 + 4, (y0 + y1) // 2 + 6
    armchair(tcx - 13, tcy - 22, 9); armchair(tcx + 4, tcy - 22, 9)
    wood_table(tcx - 14, tcy - 9, tcx + 14, tcy + 9)
    armchair(tcx - 13, tcy + 12, 9); armchair(tcx + 4, tcy + 12, 9)
    sign((x0 + x1) // 2, y0 + 14, f"TABLE {letter}", "#46606b", 10)
    floor_lamp(x1 - 14, y1 - 26)
    plant(x0 + 8, y1 - 20)
    rooms.append((f"Table {letter}", (x0, y0, x1, y1)))

# ------------------------------------------------------------------ export
big = im.resize((W * P, H * P), Image.NEAREST)
big.save(OUT, optimize=True)
print(f"saved {OUT}  ({big.width} x {big.height})")
for name, (x0, y0, x1, y1) in rooms:
    print(f"{name:22s} x {x0 * P}-{x1 * P}, y {y0 * P}-{y1 * P}")
