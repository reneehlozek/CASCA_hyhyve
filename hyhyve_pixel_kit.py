"""
Shared pixel-art drawing kit for the HyHyve maps.

Everything is drawn on a small canvas (1/P of the final size) and scaled up with
nearest-neighbour resampling, so every "pixel" is a crisp P x P block.
Used by make_poster_hall.py and make_session_hall.py.   Requires: pip install pillow
"""
from PIL import Image, ImageDraw, ImageFont

P = 5                        # size of one art pixel in final-image pixels
W, H = 3150 // P, 2100 // P  # low-res canvas: 630 x 420 -> 3150 x 2100 final
im = g = None

def start():
    """Create a fresh canvas. Call once at the top of each map script."""
    global im, g
    im = Image.new("RGB", (W, H))
    g = ImageDraw.Draw(im, "RGBA")
    g.fontmode = "1"         # no anti-aliasing -> pixel-crisp text
    return im

def save(path, areas, csv_path=None, points=()):
    """Upscale, save the PNG, print (and optionally write) area coordinates in final px.
    points: extra (kind, label, (x, y)) rows already in final px (written to the CSV only)."""
    import csv
    big = im.resize((W * P, H * P), Image.NEAREST)
    big.save(path, optimize=True)
    print(f"saved {path}  ({big.width} x {big.height})")
    rows = []
    for kind, name, (x0, y0, x1, y1) in areas:
        b = [x0 * P, y0 * P, x1 * P, y1 * P]
        rows.append([kind, name, *b, (b[0] + b[2]) // 2, (b[1] + b[3]) // 2])
        print(f"{kind:6s} {name:24s} x {b[0]}-{b[2]}, y {b[1]}-{b[3]}")
    if csv_path:
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["type", "label", "x0", "y0", "x1", "y1", "centre_x", "centre_y"])
            w.writerows(rows)
            for kind, name, (x, y) in points:
                w.writerow([kind, name, x, y, x, y, x, y])
        print(f"saved {csv_path}")

import os, glob

# Bold TrueType font. Set the HYHYVE_FONT environment variable to force one;
# otherwise the first of these that exists is used (Linux, macOS, Windows,
# then the DejaVu copy that ships with matplotlib / Anaconda).
def _font_candidates():
    c = [os.environ.get("HYHYVE_FONT", ""),
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/Library/Fonts/Arial Bold.ttf",
         "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
         "C:/Windows/Fonts/arialbd.ttf"]
    try:
        import matplotlib
        c.append(os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf", "DejaVuSans-Bold.ttf"))
    except ImportError:
        pass
    c += glob.glob("/System/Library/Fonts/*.ttf") + glob.glob("/Library/Fonts/*.ttf")
    return [f for f in c if f and os.path.exists(f)]

_FONT_PATH = None
_font_cache = {}
def font(sz):
    global _FONT_PATH
    if sz in _font_cache:
        return _font_cache[sz]
    f = None
    for path in ([_FONT_PATH] if _FONT_PATH else _font_candidates()):
        try:
            f = ImageFont.truetype(path, sz); _FONT_PATH = path; break
        except OSError:
            continue
    if f is None:
        if not _font_cache:
            print("warning: no TrueType font found; labels use Pillow's tiny built-in font. "
                  "Set HYHYVE_FONT=/path/to/SomeFont-Bold.ttf to fix.")
        f = ImageFont.load_default()
    _font_cache[sz] = f
    return f

def text_size(s, f):
    """Width/height of text; works on old and new Pillow and bitmap fonts."""
    if hasattr(f, "getbbox"):
        l, t, r, b = f.getbbox(s)
        return r - l, b - t
    return f.getsize(s)

OL = "#3a2e3c"               # dark outline used on all sprites

# ------------------------------------------------------------------ helpers
def R(x0, y0, x1, y1, fill, ol=None):
    g.rectangle([x0, y0, x1, y1], fill=fill, outline=ol)

def shadow(x0, y0, x1, y1):
    g.rectangle([x0 + 1, y1 + 1, x1 + 1, y1 + 2], fill=(40, 30, 70, 70))

def text(x, y, s, sz, fill="white"):
    """Draw text centred on (x, y) (manual centring: works on any Pillow version)."""
    f = font(sz)
    if hasattr(f, "getbbox"):
        l, t, r, b = f.getbbox(s)
        g.text((x - (l + r) / 2, y - (t + b) / 2), s, font=f, fill=fill)
    else:
        w, h = f.getsize(s)
        g.text((x - w / 2, y - h / 2), s, font=f, fill=fill)

def sign(cx, cy, s, bg, sz=11):
    """Pixel name plate: dark outline, coloured face, light top edge."""
    tw, _ = text_size(s, font(sz))
    w = int(tw) // 2 + 6
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


# ------------------------------------------------------------------ shared palettes
ROOM_COLOURS = [  # (rug colour 1, rug colour 2, rug edge, sign/accent colour)
    ("#cfe0f3", "#d9e8f8", "#aac4e3", "#3b7dc4"),   # blue
    ("#d6ebcf", "#e0f1da", "#b3d6a8", "#4e9a3f"),   # green
    ("#f5e0c8", "#f9e9d6", "#e6c49c", "#d0822c"),   # orange
    ("#e4d5ef", "#ecdff5", "#cbb5e0", "#8b5bb5"),   # purple
    ("#f3d3d8", "#f8dfe3", "#e3adb6", "#c84a5a"),   # red
    ("#cfeeea", "#dbf4f1", "#a6dbd3", "#2b9a8c"),   # teal
    ("#f6efc6", "#faf5d9", "#e6d98f", "#b89a1c"),   # yellow
    ("#e2e4e8", "#eceef1", "#c3c8d0", "#5b6472"),   # grey
]  # rooms beyond the list reuse colours from the start
LOUNGE_RUG = ("#8e8fdc", "#9a9be6", "#7475c4")

# ------------------------------------------------------------------ extra sprites
def welcome_mat(cx, y, label="WELCOME", half=30):
    R(cx - half, y, cx + half, y + 15, "#b04a4a", OL)
    g.rectangle([cx - half + 2, y + 2, cx + half - 2, y + 13], outline="#d97a6a")
    text(cx, y + 8, label, 8, "#fbe9d8")

def programme_board(x, y, label="PROGRAMME"):
    shadow(x, y, x + 32, y + 26)
    R(x, y, x + 32, y + 26, "#8a5a34", OL)
    R(x + 2, y + 2, x + 30, y + 22, "#2f4a3a")
    for ly in range(y + 6, y + 20, 3):
        g.line([(x + 5, ly), (x + 27, ly)], fill="#d8e6dc")
    if label:
        text(x + 16, y + 32, label, 7, "#2b2f36")

def bench(x, y, wd=30):
    shadow(x, y, x + wd, y + 6)
    R(x, y, x + wd, y + 6, "#a86f40", OL)
    g.line([(x + 1, y + 2), (x + wd - 1, y + 2)], fill="#c28651")
    g.line([(x + 1, y + 4), (x + wd - 1, y + 4)], fill="#c28651")

def screen(x0, y, x1, accent="#5a8fe0"):
    """Wall-mounted projector screen, seen from above/front."""
    R(x0 - 2, y, x1 + 2, y + 2, "#3f4652", OL)                  # roller bar
    R(x0, y + 3, x1, y + 20, "#fbfbf6", OL)
    R(x0 + 3, y + 5, x1 - 3, y + 8, accent)                      # slide title
    for ly in range(y + 11, y + 18, 2):
        g.line([(x0 + 4, ly), (x0 + (x1 - x0) * 2 // 3, ly)], fill="#c9ccd2")
    R(x1 - (x1 - x0) // 4 - 2, y + 11, x1 - 4, y + 17, "#cfd6e4")

def podium(x, y):
    shadow(x, y, x + 9, y + 10)
    R(x, y, x + 9, y + 10, "#8a5a34", OL)
    R(x + 1, y + 1, x + 8, y + 3, "#a86f40")
    g.line([(x + 6, y), (x + 8, y - 3)], fill="#3f4652")          # microphone
    g.point((x + 8, y - 4), fill="#22262c")

def chair_rows(x0, y0, cols, rows, aisle_after=None, dx=8, dy=8):
    """Rows of small audience chairs facing up (towards a screen/stage)."""
    for r in range(rows):
        x = x0
        for c in range(cols):
            small_chair(x, y0 + r * dy)
            x += dx + (6 if aisle_after is not None and c == aisle_after else 0)

def speaker(x, y):
    R(x, y, x + 7, y + 11, "#2f333a", OL)
    g.ellipse([x + 2, y + 2, x + 5, y + 5], fill="#555d6b")
    g.ellipse([x + 1, y + 6, x + 6, y + 10], fill="#555d6b")

def stage(x0, y0, x1, y1, title="MAIN STAGE"):
    """Raised wooden stage: curtains, big screen, podium, speakers, front steps."""
    front = 5
    shadow(x0, y0, x1, y1)
    R(x0, y0, x1, y1 - front, "#c28651", OL)                    # deck
    for ly in range(y0 + 4, y1 - front, 4):
        g.line([(x0 + 1, ly), (x1 - 1, ly)], fill="#b57a47")
    R(x0, y1 - front, x1, y1, "#7a4a2a", OL)                    # front face
    g.line([(x0 + 1, y1 - front + 1), (x1 - 1, y1 - front + 1)], fill="#9a6238")
    cw = 14                                                     # curtains
    for cx in (x0, x1 - cw):
        R(cx, y0, cx + cw, y1 - front - 2, "#b8323c", OL)
        for sx in range(cx + 2, cx + cw, 3):
            g.line([(sx, y0 + 1), (sx, y1 - front - 3)], fill="#8e2029")
    R(x0 - 2, y0 - 3, x1 + 2, y0 + 2, "#8e2029", OL)            # valance
    mid = (x0 + x1) // 2
    screen(mid - 45, y0 + 4, mid + 45)
    podium(mid + 50, y1 - front - 16)
    speaker(x0 + cw + 4, y1 - front - 16)
    speaker(x1 - cw - 11, y1 - front - 16)
    R(mid - 12, y1, mid + 12, y1 + 3, "#9a6238", OL)            # steps
    sign(mid, y1 + 12, title, "#5a3b22", 10)

def duo_table(cx, cy, label=None, scale=1.0):
    """Round table for two, one armchair each side. scale=1.0 is the default size."""
    q = lambda v: max(1, round(v * scale))
    rx, ry, cw, ch = q(9), q(7), q(8), q(9)
    for sx in (cx - rx - 2 - cw, cx + rx + 2):
        y0 = cy - ch // 2
        shadow(sx, y0, sx + cw, y0 + ch)
        R(sx, y0, sx + cw, y0 + ch, "#f08a2a", OL)
        R(sx + 1, y0 + 1, sx + cw - 1, y0 + max(2, ch // 3), "#c9681a")
        R(sx + 2, y0 + ch // 2, sx + cw - 2, y0 + ch - 2, "#f7a54e")
    g.ellipse([cx - rx + 1, cy - ry + 2, cx + rx + 1, cy + ry + 2], fill=(40, 30, 70, 70))
    g.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill="#c28651", outline=OL)
    if rx > 5:
        g.ellipse([cx - rx + 3, cy - ry + 2, cx + rx - 3, cy + ry - 3], outline="#b57a47")
    g.point((cx - rx // 2, cy - ry // 2), fill="#e0a86f")
    R(cx + q(3), cy - q(3), cx + q(3) + 3, cy - q(3) + 3, "#e8e8e8", OL)   # mug
    if label:
        text(cx, cy + ry + 7, label, 8, "#f4f2ff")
