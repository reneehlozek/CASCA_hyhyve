"""
Shared pixel-art drawing kit for the HyHyve maps.

Everything is drawn on a small canvas (1/P of the final size) and scaled up with
nearest-neighbour resampling, so every "pixel" is a crisp P x P block.
Used by make_poster_hall.py and make_session_hall.py.   Requires: pip install pillow
"""
from PIL import Image, ImageDraw, ImageFont

P = 5                        # size of one art pixel in final-image pixels
W, H = 7000 // P, 4700 // P  # low-res canvas (art px); change with set_size()

def set_size(width_px, height_px):
    """Set the final map size in image pixels (rounded down to whole art pixels).
    Call before computing any layout that uses W / H."""
    global W, H
    W, H = int(width_px) // P, int(height_px) // P
    return W, H
im = g = None
hit = hg = None              # wall/hit map: walls only, drawn alongside the art

def start():
    """Create a fresh canvas. Call once at the top of each map script."""
    global im, g, hit, hg
    im = Image.new("RGB", (W, H))
    g = ImageDraw.Draw(im, "RGBA")
    g.fontmode = "1"         # no anti-aliasing -> pixel-crisp text
    hit = Image.new("L", (W, H), 255)      # white = walkable
    hg = ImageDraw.Draw(hit)
    return im

def save_hit_map(path, transparent=False):
    """Write the wall/hit map: black walls, transparent (or white) everywhere else,
    same size as the background so it lines up exactly."""
    big = hit.resize((W * P, H * P), Image.NEAREST)
    if transparent:
        rgba = Image.new("RGBA", big.size, (0, 0, 0, 0))
        rgba.putalpha(big.point(lambda v: 255 if v == 0 else 0))
        big = rgba
    big.save(path, optimize=True)
    print(f"saved {path}  (wall/hit map)")

def save(path, areas, csv_path=None, points=()):
    """Upscale, save the PNG, print (and optionally write) area coordinates in final px.
    points: extra (kind, label, (x, y)) rows already in final px (written to the CSV only)."""
    import csv
    big = im.resize((W * P, H * P), Image.NEAREST)
    big.save(path, optimize=True)
    print(f"saved {path}  ({big.width} x {big.height})")
    rows = []
    for kind, name, (x0, y0, x1, y1) in areas:
        name = one_line(name)
        b = [x0 * P, y0 * P, x1 * P, y1 * P]
        rows.append([kind, name, *b, (b[0] + b[2]) // 2, (b[1] + b[3]) // 2])
        print(f"{kind:6s} {name:24s} x {b[0]}-{b[2]}, y {b[1]}-{b[3]}")
    if csv_path:
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["type", "label", "x0", "y0", "x1", "y1", "centre_x", "centre_y"])
            w.writerows(rows)
            for kind, name, (x, y) in points:
                name = one_line(name)
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

def sign_lines(s):
    """Split a label on "\n" into stripped lines (blank lines dropped)."""
    return [ln.strip() for ln in str(s).split("\n") if ln.strip()] or [""]

def one_line(s):
    """Label as a single line (for CSV/printing)."""
    return " ".join(sign_lines(s))

def sign_height(s, sz=11):
    """Height in art px of the name plate sign() draws for this label."""
    return max(16, len(sign_lines(s)) * (sz + 3) + 2)

def wrap_label(s, sz, max_w):
    """Re-wrap a label (keeping its own "\n" breaks) so each line of the sign
    fits within max_w art px at font size sz. Returns the new label."""
    f = font(sz)
    out = []
    for line in sign_lines(s):
        cur = ""
        words = []
        for w in line.split():           # keep "&" with the word after it
            if words and words[-1] == "&":
                words[-1] = "& " + w
            else:
                words.append(w)
        for word in words:
            trial = (cur + " " + word).strip()
            if cur and text_size(trial, f)[0] + 12 > max_w:
                out.append(cur); cur = word
            else:
                cur = trial
        out.append(cur)
    return "\n".join(out)

def fit_label(s, max_w, sz=10, min_sz=9):
    """Pick the largest size in [min_sz, sz] at which the label fits max_w
    (wrapping words onto extra lines if needed). Returns (label, size).
    Sizes below ~9 get hard to read in pixel text, so wrapping is preferred."""
    for size in range(sz, min_sz - 1, -1):
        lab = wrap_label(s, size, max_w)
        if sign_width(lab, size) <= max_w and len(sign_lines(lab)) <= len(sign_lines(s)) + (sz - size):
            return lab, size
    return wrap_label(s, min_sz, max_w), min_sz

def sign_width(s, sz=11):
    """Width in art px of the name plate sign() draws for this label."""
    f = font(sz)
    return 2 * (int(max(text_size(ln, f)[0] for ln in sign_lines(s))) // 2 + 6)

def sign(cx, cy, s, bg, sz=11):
    """Pixel name plate centred on (cx, cy). Put "\n" in the label for extra lines."""
    lines = sign_lines(s)
    f = font(sz)
    w = int(max(text_size(ln, f)[0] for ln in lines)) // 2 + 6
    h = sign_height(s, sz)
    top, bot = cy - h // 2, cy - h // 2 + h
    shadow(cx - w, top, cx + w, bot)
    R(cx - w, top, cx + w, bot, bg, OL)
    g.line([(cx - w + 1, top + 1), (cx + w - 1, top + 1)], fill=(255, 255, 255, 90))
    g.line([(cx - w + 1, bot - 1), (cx + w - 1, bot - 1)], fill=(0, 0, 0, 60))
    # common vertical reference so every line sits on the same baseline grid
    if hasattr(f, "getbbox"):
        _, rt, _, rb = f.getbbox("HAg")
    else:
        rt, rb = 0, f.getsize("HAg")[1]
    lh = (h - 2) / len(lines)
    for i, ln in enumerate(lines):
        ly = top + 1 + lh * (i + 0.5)
        lw = text_size(ln, f)[0]
        l0 = f.getbbox(ln)[0] if hasattr(f, "getbbox") else 0
        g.text((cx - lw / 2 - l0, ly - (rt + rb) / 2), ln, font=f, fill="white")

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
    hg.rectangle([x0, y0, x1, y1], fill=0)  # also mark it on the wall/hit map
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

def _side_lamp(x, y):
    glow(x + 4, y + 2, 14)
    shadow(x, y + 6, x + 8, y + 12)
    R(x, y + 6, x + 8, y + 12, "#3f4652", OL)
    R(x + 1, y + 7, x + 7, y + 8, "#555d6b")
    R(x + 3, y + 3, x + 5, y + 6, "#8a4b26")
    g.polygon([(x + 1, y + 3), (x + 7, y + 3), (x + 6, y - 2), (x + 2, y - 2)], fill="#f5a13a", outline=OL)
    g.line([(x + 3, y - 1), (x + 3, y + 2)], fill="#ffd27a")

def _floor_lamp(x, y):
    glow(x + 2, y + 1, 16)
    g.ellipse([x - 1, y + 16, x + 5, y + 18], fill=(40, 30, 70, 70))
    R(x, y + 15, x + 4, y + 16, "#3f4652", OL)
    g.line([(x + 2, y + 4), (x + 2, y + 15)], fill="#3f4652")
    g.polygon([(x - 2, y + 4), (x + 6, y + 4), (x + 5, y - 2), (x - 1, y - 2)], fill="#f5a13a", outline=OL)
    g.line([(x, y - 1), (x, y + 3)], fill="#ffd27a")

def _plant(x, y, flowers=False):
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

def _bamboo(x, y, wd=26, ht=16):
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

def _small_chair(x, y):
    R(x, y, x + 5, y + 4, "#f08a2a", OL)
    g.line([(x + 1, y + 1), (x + 4, y + 1)], fill="#c9681a")

def small_chair(x, y):
    """Audience chair, 6 x 5 art px at CHAIR_SCALE 1; (x, y) is its top-left."""
    f = CHAIR_SCALE
    if f <= 1:
        _small_chair(x, y)
    else:
        scaled_sprite(lambda cx, cy: _small_chair(cx - 3, cy - 2), x + 3 * f, y + 2.5 * f, f, box=10)

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
def _mat_size(label="WELCOME", sz=9, max_w=None):
    """(label, width, height) of the welcome mat for this text: the mat wraps
    around the text; if max_w is given, long text wraps onto extra lines."""
    if max_w:
        label = wrap_label(label, sz, max_w - 4)
    lines = sign_lines(label)
    f = font(sz)
    w = int(max(text_size(ln, f)[0] for ln in lines)) + 16
    if max_w:
        w = min(w, max_w)
    h = len(lines) * (sz + 3) + 6
    return label, w, h

def _welcome_mat(cx, y=None, label="WELCOME", sz=9, max_w=None, bottom=None):
    """Red doormat sized to its text. Give the top edge y, or bottom=..."""
    label, w, h = _mat_size(label, sz, max_w)
    if y is None:
        y = bottom - h
    half = w // 2
    R(cx - half, y, cx + half, y + h, "#b04a4a", OL)
    g.rectangle([cx - half + 2, y + 2, cx + half - 2, y + h - 2], outline="#d97a6a")
    lines = sign_lines(label)
    for i, ln in enumerate(lines):
        text(cx, y + 3 + (sz + 3) * (i + 0.5) + 0.5, ln, sz, "#fbe9d8")

def programme_board(x, y, label="PROGRAMME"):
    shadow(x, y, x + 32, y + 26)
    R(x, y, x + 32, y + 26, "#8a5a34", OL)
    R(x + 2, y + 2, x + 30, y + 22, "#2f4a3a")
    for ly in range(y + 6, y + 20, 3):
        g.line([(x + 5, ly), (x + 27, ly)], fill="#d8e6dc")
    if label:
        text(x + 16, y + 32, label, 9, "#2b2f36")

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

def stage(x0, y0, x1, y1, title="MAIN STAGE", podium_offset=50, accent="#5a8fe0"):
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
    sw = max(30, min(90, (x1 - x0) * 2 // 9))
    screen(mid - sw, y0 + 4, mid + sw, accent)
    podium(min(mid + podium_offset, x1 - cw - 26), y1 - front - 16)
    speaker(x0 + cw + 4, y1 - front - 16)
    speaker(x1 - cw - 11, y1 - front - 16)
    R(mid - 12, y1, mid + 12, y1 + 3, "#9a6238", OL)            # steps
    if not title:
        return
    title, tsz = fit_label(title, (x1 - x0) - 20, 10)
    th = sign_height(title, tsz)
    sign(mid, y1 + 4 + th // 2, title, "#5a3b22", tsz)

def duo_table(cx, cy, label=None, scale=1.0, label_max_w=None, label_colour="#46606b"):
    """Round table for two, one armchair each side. scale=1.0 is the default size.
    The label goes on a small name plate under the table; with label_max_w set,
    long labels wrap onto extra lines to fit that width."""
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
        lab = wrap_label(label, 9, label_max_w) if label_max_w else str(label)
        lh = sign_height(lab, 9)
        sign(cx, cy + ry + 4 + lh // 2, lab, label_colour, 9)

def duo_table_extent(label=None, scale=1.0, label_max_w=None):
    """(half_width, height_above, height_below) a duo_table occupies, incl. its label."""
    q = lambda v: max(1, round(v * scale))
    rx, ry, cw = q(9), q(7), q(8)
    half = rx + 2 + cw
    below = ry + 2
    if label:
        lab = wrap_label(label, 9, label_max_w) if label_max_w else str(label)
        half = max(half, sign_width(lab, 9) // 2)
        below = ry + 4 + sign_height(lab, 9)
    return half, max(ry, q(9) // 2) + 1, below

def stairs(cx, cy, w=34, h=30, label=None, label_colour="#2f3640", label_size=9, arrow=True,
           label_below=False):
    """Staircase going down (top-down view) with handrails, an arrow painted on
    the steps and an optional sign above it. (cx, cy) is the centre of the stairs.
    Returns the stairs box (x0, y0, x1, y1)."""
    x0, y0 = cx - w // 2, cy - h // 2
    x1, y1 = x0 + w, y0 + h
    shadow(x0, y0, x1, y1)
    R(x0, y0, x1, y1, "#3a2e3c")                         # dark stairwell
    steps = max(3, (h - 2) // 4)
    sh = (h - 2) / steps
    for i in range(steps):                                # treads get darker going down
        t = i / max(1, steps - 1)
        c = tuple(round(a + (b - a) * t) for a, b in ((0xe8, 0x9a), (0xd2, 0x86), (0xb4, 0x6c)))
        ty0 = round(y0 + 1 + i * sh)
        ty1 = round(y0 + 1 + (i + 1) * sh) - 1
        R(x0 + 3, ty0, x1 - 3, ty1, c)
        g.line([(x0 + 3, ty1), (x1 - 3, ty1)], fill=(60, 40, 30, 150))   # riser shadow
        g.line([(x0 + 3, ty0), (x1 - 3, ty0)], fill=(255, 255, 255, 70))  # nosing highlight
    for rx in (x0, x1 - 2):                               # handrails
        R(rx, y0, rx + 2, y1, "#8a5a34", OL)
    g.rectangle([x0, y0, x1, y1], outline=OL)
    if arrow:                                             # downward arrow on the steps
        ax, ay = cx, cy
        R(ax - 1, ay - 7, ax + 1, ay + 2, "#fbfbf6")
        g.polygon([(ax - 5, ay + 2), (ax + 5, ay + 2), (ax, ay + 7)], fill="#fbfbf6")
    if label:
        lh = sign_height(label, label_size)
        ly = y1 + 4 + lh // 2 if label_below else y0 - 4 - lh + lh // 2
        sign(cx, ly, label, label_colour, label_size)
    return (x0, y0, x1, y1)

def poster_square(cx, cy, size=24, label="", accent="#3b7dc4", sz=10):
    """Square poster board seen from above, with a number/label on the paper.
    (cx, cy) is the centre; size in art px."""
    x0, y0 = cx - size // 2, cy - size // 2
    x1, y1 = x0 + size, y0 + size
    shadow(x0, y0, x1, y1)
    R(x0, y0, x1, y1, "#8a5a34", OL)                     # wooden frame
    R(x0 + 2, y0 + 2, x1 - 2, y1 - 2, "#fbfbf6")          # paper
    R(x0 + 3, y0 + 3, x1 - 3, y0 + 5, accent)             # title strip
    for px in (x0 + 2, x1 - 3):                           # pins
        g.point((px, y0 + 2), fill="#d9534f"); g.point((px + 1, y0 + 2), fill="#d9534f")
    if label:
        # largest size (>= 9; smaller pixel text breaks up) whose lines fit the paper
        lab, lsz = str(label), 9
        for tsz in range(sz, 8, -1):
            if max(text_size(ln, font(tsz))[0] for ln in sign_lines(lab)) <= size - 5:
                lsz = tsz
                break
        else:
            lab = wrap_label(lab, 9, size + 7)        # wrap_label pads by 12
        lines = sign_lines(lab)
        lh = lsz + 2
        top = (y0 + 6 + y1 - 2) / 2 - lh * len(lines) / 2
        for j, ln in enumerate(lines):
            text(cx, top + lh * (j + 0.5), ln, lsz, "#2b2f36")

def _group_dims(seats, scale):
    q = lambda v: max(1, round(v * scale))
    ends = 2 if seats >= 6 else (seats % 2)          # chairs at the two short ends
    per_side = (seats - ends + 1) // 2               # chairs along each long side
    gap = q(9)                                        # chair spacing
    tw = max(q(16), per_side * gap + q(4))           # table length
    th = q(13)                                        # table depth
    cw, ch = q(6), q(5)                               # chair size
    return per_side, ends, gap, tw, th, cw, ch

def group_table(cx, cy, seats=10, label=None, scale=1.0, label_max_w=None, label_colour="#46606b"):
    """Long wooden table with `seats` chairs around it (split along both sides,
    one at each end for 6+). Label on a name plate below, wrapped to label_max_w."""
    if seats <= 2:
        return duo_table(cx, cy, label, scale, label_max_w, label_colour)
    per_side, ends, gap, tw, th, cw, ch = _group_dims(seats, scale)
    x0, y0 = cx - tw // 2, cy - th // 2
    x1, y1 = x0 + tw, y0 + th
    top_n = per_side
    bot_n = seats - ends - per_side
    def chair(x, y, w, h):
        shadow(x, y, x + w, y + h)
        R(x, y, x + w, y + h, "#f08a2a", OL)
        R(x + 1, y + 1, x + w - 1, y + max(1, h // 3), "#c9681a")
    for n, yy in ((top_n, y0 - ch - 1), (bot_n, y1 + 2)):
        for j in range(n):
            x = x0 + (tw - (n - 1) * gap) / 2 + j * gap - cw / 2
            chair(round(x), yy, cw, ch)
    if ends >= 1:
        chair(x0 - ch - 2, cy - cw // 2, ch, cw)
    if ends >= 2:
        chair(x1 + 2, cy - cw // 2, ch, cw)
    shadow(x0, y0, x1, y1)
    R(x0, y0, x1, y1, "#a86f40", OL)
    R(x0 + 1, y0 + 1, x1 - 1, y1 - 2, "#c28651")
    for ly in range(y0 + 3, y1 - 2, 3):
        g.line([(x0 + 2, ly), (x1 - 2, ly)], fill="#b57a47")
    for j in range(max(1, seats // 4)):                    # a few mugs / notepads
        mx = x0 + 4 + j * (tw - 8) // max(1, seats // 4)
        R(mx, cy - 2, mx + 2, cy, "#e8e8e8", OL)
    if label:
        lab = wrap_label(label, 9, label_max_w) if label_max_w else str(label)
        lh = sign_height(lab, 9)
        sign(cx, y1 + ch + 4 + lh // 2, lab, label_colour, 9)

def group_table_extent(seats=10, label=None, scale=1.0, label_max_w=None):
    """(half_width, height_above, height_below) a group_table occupies, incl. its label."""
    if seats <= 2:
        return duo_table_extent(label, scale, label_max_w)
    per_side, ends, gap, tw, th, cw, ch = _group_dims(seats, scale)
    half = tw // 2 + (ch + 3 if ends else 0)
    above = th // 2 + ch + 1
    below = th // 2 + ch + 3
    if label:
        lab = wrap_label(label, 9, label_max_w) if label_max_w else str(label)
        half = max(half, sign_width(lab, 9) // 2)
        below = th // 2 + ch + 4 + sign_height(lab, 9)
    return half, above, below

# ------------------------------------------------------------------ HyHyve action points
def action_point(position, name, content="", size=None, sign=None, call_type="Group"):
    """One HyHyve action point in the same JSON shape as a HyHyve export.
    position/size in final image px. sign=None -> no sign graphic on the map."""
    import random, string
    ap = {
        "id": "".join(random.choices(string.ascii_letters + string.digits, k=21)),
        "position": [int(position[0]), int(position[1])],
        "content": content,
        "name": name,
        "callType": call_type,
        "sign": sign or {"tag": "Default"},
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
    }
    if size:
        ap["size"] = [int(size[0]), int(size[1])]
    return ap

# ------------------------------------------------------------------ furniture by name
FURNITURE_SCALE = 1       # size of sofas, armchairs, coffee tables, shelves, boards (whole number)
CHAIR_SCALE = 1           # size of audience chairs (whole number)
DECOR_KINDS = {"plant", "flowers", "floor_lamp", "side_lamp", "bamboo"}

def furniture(kind, x, y):
    """Draw one piece of furniture centred (roughly) on (x, y), by name.
    Plants/lamps/bamboo follow DECOR_SCALE; everything else FURNITURE_SCALE."""
    if kind.lower() not in DECOR_KINDS and FURNITURE_SCALE > 1:
        scaled_sprite(lambda cx, cy: _furniture(kind, cx, cy), x, y, FURNITURE_SCALE, box=90)
    else:
        _furniture(kind, x, y)

def _furniture(kind, x, y):
    """Draw one piece of furniture centred (roughly) on (x, y), by name:
    sofa, sofa_plain, armchair, coffee_table, coffee_table_laptop, plant, flowers,
    floor_lamp, side_lamp, bookshelf, bamboo, programme_board, pingpong, bench."""
    k = kind.lower()
    if k == "sofa":                 sofa(x - 17, y - 6)
    elif k == "sofa_plain":         sofa(x - 17, y - 6, cushions=False)
    elif k == "armchair":           armchair(x - 5, y - 5)
    elif k == "coffee_table":       coffee_table(x - 11, y - 4, laptop=False)
    elif k == "coffee_table_laptop": coffee_table(x - 11, y - 4, laptop=True)
    elif k == "plant":              plant(x - 5, y - 6)
    elif k == "flowers":            plant(x - 5, y - 6, flowers=True)
    elif k == "floor_lamp":         floor_lamp(x - 2, y - 10)
    elif k == "side_lamp":          side_lamp(x - 4, y - 6)
    elif k == "bookshelf":          bookshelf(x - 13, y - 15)
    elif k == "bamboo":             bamboo(x - 13, y - 8)
    elif k == "programme_board":    programme_board(x - 16, y - 13, None)
    elif k == "pingpong":           pingpong(x - 12, y - 15)
    elif k == "bench":              bench(x - 15, y - 3)
    else:
        print(f"warning: unknown furniture {kind!r}")

# ------------------------------------------------------------------ bigger decorations
# DECOR_SCALE makes plants, lamps and bamboo bigger; MAT_SCALE the welcome mats.
# Whole-number factors keep the pixel grid crisp (2 = twice the size, chunkier pixels).
DECOR_SCALE = 1
MAT_SCALE = 1

def scaled_sprite(draw_at, cx, cy, factor, box=80):
    """Draw a sprite on a scratch canvas centred at (box/2, box/2) using
    draw_at(x, y), scale it up by an integer factor and paste it centred on (cx, cy)."""
    global im, g
    if factor <= 1:
        draw_at(cx, cy)
        return
    main_im, main_g = im, g
    tmp = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    im, g = tmp, ImageDraw.Draw(tmp, "RGBA")
    g.fontmode = "1"
    try:
        draw_at(box // 2, box // 2)
    finally:
        im, g = main_im, main_g
    big = tmp.resize((box * factor, box * factor), Image.NEAREST)
    main_im.paste(big, (round(cx - box * factor / 2), round(cy - box * factor / 2)), big)

def plant(x, y, flowers=False):
    """Pot plant; (x, y) is the top-left of the 1x sprite (centre = x+5, y+6)."""
    f = DECOR_SCALE
    scaled_sprite(lambda cx, cy: _plant(cx - 5, cy - 6, flowers), x + 5, y + 6 - (f - 1) * 6, f)

def floor_lamp(x, y):
    f = DECOR_SCALE
    scaled_sprite(lambda cx, cy: _floor_lamp(cx - 2, cy - 8), x + 2, y + 8 - (f - 1) * 8, f)

def side_lamp(x, y):
    f = DECOR_SCALE
    scaled_sprite(lambda cx, cy: _side_lamp(cx - 4, cy - 5), x + 4, y + 5 - (f - 1) * 5, f)

def bamboo(x, y, wd=26, ht=16):
    f = DECOR_SCALE
    scaled_sprite(lambda cx, cy: _bamboo(cx - wd // 2, cy - ht // 2, wd, ht),
                  x + wd // 2, y + ht // 2 - (f - 1) * ht // 2, f, box=max(80, wd + 30))

def mat_size(label="WELCOME", sz=9, max_w=None):
    """(label, width, height) of the welcome mat as drawn (MAT_SCALE included).
    max_w is the widest the mat may be (in art px, after scaling)."""
    f = MAT_SCALE
    lab, w, h = _mat_size(label, sz, max_w / f if max_w else None)
    return lab, w * f, h * f

def welcome_mat(cx, y=None, label="WELCOME", sz=9, max_w=None, bottom=None):
    """Red doormat sized to its text (scaled by MAT_SCALE). Give the top edge y, or bottom=..."""
    f = MAT_SCALE
    lab, w, h = mat_size(label, sz, max_w)
    if y is None:
        y = bottom - h
    raw_max = max_w / f if max_w else None
    box = int(max(w, h) / f) + 20
    scaled_sprite(lambda x, yy: _welcome_mat(x, label=label, sz=sz, max_w=raw_max,
                                               bottom=yy + h / f / 2),
                  cx, y + h / 2, f, box=box)

def chair(x, y, scale=1):
    """Audience chair (small_chair) at top-left (x, y), scaled by a whole number."""
    scale = max(1, int(round(scale)))
    if scale == 1:
        small_chair(x, y)
        return
    scaled_sprite(lambda cx, cy: small_chair(cx - 3, cy - 2), x + 3 * scale, y + 2 * scale + 1,
                  scale, box=12)

DECOR_KINDS = {"plant", "flowers", "floor_lamp", "side_lamp", "bamboo"}   # sized by DECOR_SCALE

def furniture_scaled(kind, x, y, scale=1):
    """furniture() at a whole-number scale (plants/lamps use DECOR_SCALE instead)."""
    scale = max(1, int(round(scale)))
    if scale == 1 or kind.lower() in DECOR_KINDS:
        furniture(kind, x, y)
    else:
        scaled_sprite(lambda cx, cy: furniture(kind, cx, cy), x, y, scale, box=60)

def lounge_clump(cx, cy, scale=2, armchairs=4, laptop=False, wide=False):
    """A tight lounge island centred on (cx, cy): facing sofas around a coffee
    table with armchairs at the ends. wide=True doubles it: two sofas on each
    side and two coffee tables. Returns its (x0, y0, x1, y1) box."""
    s = max(1, int(round(scale)))
    xs = [-18, 18] if wide else [0]                      # sofa / table columns (unscaled)
    for i, dx in enumerate(xs):
        furniture_scaled("sofa", cx + dx * s, cy - 17 * s, s)
        furniture_scaled("coffee_table_laptop" if (laptop and i == 0) else "coffee_table",
                         cx + dx * s, cy, s)
        furniture_scaled("sofa_plain", cx + dx * s, cy + 15 * s, s)
    end = 43 if wide else 25
    spots = {2: [(-end, 0), (end, 0)], 4: [(-end, -7), (-end, 9), (end, -7), (end, 9)]}
    for dx, dy in spots.get(armchairs, spots[2] if armchairs else []):
        furniture_scaled("armchair", cx + dx * s, cy + dy * s, s)
    hw = end + 6
    return (cx - hw * s, cy - 24 * s, cx + hw * s, cy + 22 * s)

def chair_set(cx, cy, scale=1.8):
    """Small cafe set: a round table with an armchair either side (no label)."""
    duo_table(cx, cy, None, scale)

def programme_content(path="programme.md"):
    """Text for the programme-board action points, read from a shared markdown
    file so every map shows the same information."""
    import os
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    print(f"note: {path!r} not found; programme board shows a placeholder")
    return "**Programme**\n\n(programme goes here)"
