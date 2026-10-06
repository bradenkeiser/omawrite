"""Generates omawrite-icon.svg: a stoic temple-terrace dragon head in two
tones on black. Every part is a thick scarlet outline with a fine neon green
inner line, black inside, and detailed with guardian-lion patterns: a
key-fret brow, square-spiral crown scrolls, layered mandala eyes, a closed
toothed muzzle and a scaled neck, in front of a dimmed mandala burst.

    python3 macos/make_icon.py > macos/omawrite-icon.svg

The design is exactly symmetrical: left-hand parts are mirrored across
x = 512. Earlier designs live in variants/.
"""

import math

RED, GREEN, BLACK = "#ff2400", "#39ff14", "#000000"
CX = 512
OUT = []


def mx(x):
    return 2 * CX - x


def mirror(points):
    return [(mx(x), y) for x, y in points][::-1]


def path(points, closed=True):
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)
    return d + (" Z" if closed else "")


def inset(points, d):
    """Offset a convex, clockwise-on-screen polygon inward by d (miter joins)."""
    n = len(points)
    lines = []
    for i in range(n):
        (x1, y1), (x2, y2) = points[i], points[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        nx, ny = -dy / length, dx / length  # inward normal for screen-clockwise order
        lines.append(((x1 + nx * d, y1 + ny * d), (dx, dy)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        det = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / det
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def part(points, outline=22, line=7, gap=24, fill=BLACK):
    """A black shape with a thick scarlet outline and a fine green inner line."""
    OUT.append(f'<path d="{path(points)}" fill="{fill}" stroke="{RED}" stroke-width="{outline}" '
               f'stroke-linejoin="miter"/>')
    if line:
        OUT.append(f'<path d="{path(inset(points, gap))}" fill="none" stroke="{GREEN}" '
                   f'stroke-width="{line}" stroke-linejoin="miter"/>')


def box(x0, y0, x1, y1, **kw):
    part([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)


def chamfer(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1),
            (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def line(points, color, width, closed=False, cap="square"):
    OUT.append(f'<path d="{path(points, closed)}" fill="none" stroke="{color}" '
               f'stroke-width="{width}" stroke-linecap="{cap}" stroke-linejoin="miter"/>')


def both(points, color, width, closed=False, cap="square"):
    line(points, color, width, closed, cap)
    line([(mx(x), y) for x, y in points], color, width, closed, cap)


def square_spiral(cx, cy, size, step, turns_in=None):
    """Points of a rectangular spiral winding inward, clockwise from top-left."""
    x0, y0, x1, y1 = cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2
    pts = [(x0, y1), (x0, y0)]
    while x1 - x0 > step and y1 - y0 > step:
        pts += [(x1, y0), (x1, y1), (x0 + step, y1)]
        x0, y0, x1, y1 = x0 + step, y0 + step, x1 - step, y1 - step
        pts += [(x0, y0)]
    return pts


# --- background: a dimmed mandala bursting out from behind the head ---------
MX, MY = 512, 430  # centered on the face
BG_OPACITY = 0.42


def petal_ring(radius, count, length, width, color, turn=0.0, sw=4):
    for i in range(count):
        a = 2 * math.pi * (i + turn) / count
        ux, uy, px, py = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        base = (MX + ux * radius, MY + uy * radius)
        tip = (base[0] + ux * length, base[1] + uy * length)
        l = (base[0] + ux * length * 0.4 + px * width, base[1] + uy * length * 0.4 + py * width)
        r = (base[0] + ux * length * 0.4 - px * width, base[1] + uy * length * 0.4 - py * width)
        line([base, l, tip, r], color, sw, closed=True)


# A faint scarlet glow behind everything, for the blast.
OUT.append(f'<circle cx="{MX}" cy="{MY}" r="720" fill="url(#blast)"/>')
OUT.append(f'<g opacity="{BG_OPACITY}">')
# The blast: rays fanning out, alternating red and green, long and short.
for i in range(72):
    a = 2 * math.pi * i / 72
    r0, r1 = (150, 760) if i % 2 == 0 else (240, 560)
    line([(MX + math.cos(a) * r0, MY + math.sin(a) * r0),
          (MX + math.cos(a) * r1, MY + math.sin(a) * r1)], RED if i % 4 == 0 else GREEN,
         5 if i % 2 == 0 else 3)
# Rings of petals, each turned half a petal from the last.
petal_ring(300, 24, 70, 18, GREEN)
petal_ring(380, 32, 84, 17, RED, turn=0.5)
petal_ring(476, 40, 96, 16, GREEN)
petal_ring(586, 48, 110, 15, RED, turn=0.5)
# Sixteen-point stars and dotted circles between the petal rings.
for radius, color, rot in [(270, RED, 0), (362, GREEN, 0.5), (456, RED, 0), (566, GREEN, 0.5)]:
    pts = []
    for i in range(32):
        a = math.pi * (i + rot) / 16
        rr = radius if i % 2 == 0 else radius * 0.94
        pts.append((MX + math.cos(a) * rr, MY + math.sin(a) * rr))
    line(pts, color, 4, closed=True)
for radius, color in [(250, GREEN), (440, GREEN), (700, RED)]:
    OUT.append(f'<circle cx="{MX}" cy="{MY}" r="{radius}" fill="none" stroke="{color}" '
               f'stroke-width="6" stroke-dasharray="2 18" stroke-linecap="round"/>')
OUT.append('</g>')

# --- neck: wide, vertical, scaled, with belly plates ----------------------
neck = [(300, 690), (724, 690), (724, 1060), (300, 1060)]
part(neck, outline=26, gap=28)
# Scales: rows of blocky scallops down each side.
for row, y in enumerate(range(790, 960, 34)):
    offset = 17 if row % 2 else 0
    for x in range(338 + offset, 430, 34):
        both([(x, y), (x, y + 14), (x + 6, y + 22), (x + 22, y + 22), (x + 28, y + 14),
              (x + 28, y)], GREEN, 5)
# Belly plates.
for y in range(784, 960, 44):
    box(446, y, 578, y + 32, outline=8, line=4, gap=9)

# --- horns: blocky, ringed ---------------------------------------------------
horn = [(258, 300), (196, 122), (266, 104), (346, 284)]
part(horn, outline=20, gap=22)
part(mirror(horn), outline=20, gap=22)
inner = inset(horn, 22)  # rings run between the horn's inner lines
for t in (0.3, 0.52, 0.74):
    a = tuple(inner[0][k] + (inner[1][k] - inner[0][k]) * t for k in (0, 1))
    b = tuple(inner[3][k] + (inner[2][k] - inner[3][k]) * t for k in (0, 1))
    both([a, b], GREEN, 6)

# --- face: wide at the brow, tapering fast to a raised jaw ------------------
face = [(250, 254), (774, 254), (812, 292), (812, 452), (730, 566), (294, 566),
        (212, 452), (212, 292)]
part(face, outline=26, gap=30)

# --- jaw: narrow, set back behind the muzzle --------------------------------
part(chamfer(338, 668, 686, 764, 18), outline=20, gap=22)

# --- crown: a double scroll on top of the head -------------------------------
part(chamfer(388, 132, 636, 270, 22), outline=22, gap=24)
spiral = square_spiral(452, 201, 86, 17)
line(spiral, GREEN, 7)
line([(mx(x), y) for x, y in spiral], GREEN, 7)

# --- brow: a level ridge carrying a key-fret band ------------------------------
part([(258, 290), (766, 290), (766, 340), (258, 340)], outline=14, line=0)
top, bot, unit = 302, 328, 36
for k in range(7):
    x = 512 - (k + 1) * unit
    key = [(x + unit, bot), (x, bot), (x, top), (x + unit * 0.7, top),
           (x + unit * 0.7, top + 14), (x + unit * 0.35, top + 14)]
    both(key, GREEN, 5)

# --- nose bridge between the eyes --------------------------------------------
part([(486, 344), (538, 344), (538, 500), (486, 500)], outline=12, gap=14, line=4)
for y in (376, 408, 440, 472):
    line([(498, y), (526, y)], GREEN, 5)

# --- mandala eyes: wide apart, unframed --------------------------------------
def mandala(cx, cy, r=90):
    diamond = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    OUT.append(f'<path d="{path(diamond)}" fill="{BLACK}" stroke="{RED}" stroke-width="16" '
               f'stroke-linejoin="miter"/>')
    line(inset(diamond, 16), GREEN, 5, closed=True)
    OUT.append(f'<circle cx="{cx}" cy="{cy}" r="60" fill="none" stroke="{RED}" stroke-width="10"/>')
    for i in range(24):  # tick ring
        a = 2 * math.pi * i / 24
        line([(cx + math.cos(a) * 68, cy + math.sin(a) * 68),
              (cx + math.cos(a) * 76, cy + math.sin(a) * 76)], GREEN, 4)
    star = []
    for i in range(16):  # eight-point star of petals
        a = math.pi * i / 8 - math.pi / 2
        rr = 50 if i % 2 == 0 else 28
        star.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    line(star, GREEN, 5, closed=True)
    OUT.append(f'<circle cx="{cx}" cy="{cy}" r="20" fill="{RED}"/>')
    OUT.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{BLACK}"/>')
    sq = [(cx, cy - 34), (cx + 34, cy), (cx, cy + 34), (cx - 34, cy)]
    line(sq, RED, 4, closed=True)


mandala(370, 440)
mandala(mx(370), 440)

# --- the muzzle stands in front of the eyes: a cast shadow gives depth ----
MUZZLE_TOP = 494  # covers the lower fifth of the eyes
OUT.append(f'<rect x="250" y="{MUZZLE_TOP - 70}" width="524" height="70" fill="url(#shade)"/>')

# --- nostrils: thick bumps peeking over the muzzle -----------------------------
for x in (440, mx(440)):
    OUT.append(f'<ellipse cx="{x}" cy="{MUZZLE_TOP + 8}" rx="56" ry="50" fill="{BLACK}" '
               f'stroke="{RED}" stroke-width="20"/>')
    OUT.append(f'<ellipse cx="{x}" cy="{MUZZLE_TOP + 8}" rx="32" ry="27" fill="none" '
               f'stroke="{GREEN}" stroke-width="6"/>')
    OUT.append(f'<ellipse cx="{x}" cy="{MUZZLE_TOP - 24}" rx="16" ry="8" fill="{RED}"/>')

# --- muzzle: a beefy closed rectangle, wider than the jaw ----------------------
muzzle = chamfer(244, MUZZLE_TOP, 780, 716, 22)
part(muzzle, outline=26, gap=30)
seam = (MUZZLE_TOP + 716) // 2
line([(276, seam), (748, seam)], RED, 12)
for x in range(292, 732, 40):  # closed teeth, upper and lower rows
    if x + 28 > 732:
        break
    line([(x, seam - 10), (x, seam - 52), (x + 28, seam - 52), (x + 28, seam - 10)], GREEN, 5)
    line([(x + 20, seam + 10), (x + 20, seam + 52), (x + 48, seam + 52), (x + 48, seam + 10)],
         GREEN, 5)

print(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <radialGradient id="blast" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0.25" stop-color="{RED}" stop-opacity="0.30"/>
      <stop offset="0.6" stop-color="{RED}" stop-opacity="0.10"/>
      <stop offset="1" stop-color="{RED}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0.75"/>
    </linearGradient>
    <clipPath id="body"><rect x="100" y="100" width="824" height="824" rx="185"/></clipPath>
  </defs>
  <rect x="100" y="100" width="824" height="824" rx="185" fill="{BLACK}"/>
  <g clip-path="url(#body)">
{chr(10).join(OUT)}
  </g>
</svg>''')
