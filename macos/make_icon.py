"""Generates omawrite-icon.svg: a front-facing Chinese dragon, thick and
blocky, red and green on black: a scaled head with a wide snout, crocodile
eye ridges, antler horns and flame mane, on a serpentine neck that runs off
the bottom of the icon.

    python3 macos/make_icon.py > macos/omawrite-icon.svg

Everything off the center line is drawn once and mirrored, so the face is
exactly symmetrical. The lion this replaced lives in variants/lion/.
"""

import math

RED = ["#ff6a5c", "#e8202e", "#9c0e1c"]     # light, primary, deep
GREEN = ["#7af29b", "#16c060", "#08693a"]
GOLD = ["#ffe08a", "#ffc23c", "#c98a12"]
INK = "#0a0f0c"
CX = 512
OUT = []


def mirror(points):
    return [(2 * CX - x, y) for x, y in points]


def smooth(points, closed=True):
    """Catmull-Rom spline through points as a cubic Bezier path."""
    n = len(points)
    d = [f"M{points[0][0]:.1f} {points[0][1]:.1f}"]
    for i in range(n if closed else n - 1):
        p0 = points[(i - 1) % n] if (closed or i) else points[0]
        p1, p2 = points[i], points[(i + 1) % n]
        p3 = points[(i + 2) % n] if (closed or i + 2 < n) else points[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(d) + (" Z" if closed else "")


def symmetric(half):
    """A closed outline from its right half, listed top center to bottom center."""
    return half + mirror(half)[::-1][1:-1]


def fill(points, color, sw=10, opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    OUT.append(f'<path d="{smooth(points)}" fill="{color}" stroke="{INK if sw else "none"}" '
               f'stroke-width="{sw}" stroke-linejoin="round"{op}/>')


def pair(points, color, sw=10):
    """A shape on the right and its mirror on the left."""
    fill(points, color, sw)
    fill(mirror(points)[::-1], color, sw)


def stroke(points, color, width, outline=12, both=True):
    for pts in ([points, mirror(points)] if both else [points]):
        d = smooth(pts, closed=False)
        if outline:
            OUT.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width + outline}" '
                       f'stroke-linecap="round" stroke-linejoin="round"/>')
        OUT.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')


def circle(x, y, r, color, sw=8, both=True):
    for px in ([x, 2 * CX - x] if both and x != CX else [x]):
        OUT.append(f'<circle cx="{px:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" '
                   f'stroke="{INK}" stroke-width="{sw}"/>')


def flame(cx, cy, angle, length, width, color, sw=8, bend=0.35):
    """A curved, pointed tuft from (cx, cy) outward at `angle` degrees."""
    a = math.radians(angle)
    ux, uy, px, py = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    tip = (cx + ux * length + px * length * bend, cy + uy * length + py * length * bend)
    l = (cx + ux * length * 0.45 + px * width, cy + uy * length * 0.45 + py * width)
    r = (cx + ux * length * 0.45 - px * width * 0.6, cy + uy * length * 0.45 - py * width * 0.6)
    return (f'<path d="M{cx - px * width * 0.5:.1f} {cy - py * width * 0.5:.1f} '
            f'Q{l[0]:.1f} {l[1]:.1f} {tip[0]:.1f} {tip[1]:.1f} '
            f'Q{r[0]:.1f} {r[1]:.1f} {cx + px * width * 0.5:.1f} {cy + py * width * 0.5:.1f}Z" '
            f'fill="{color}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')


def flames(cx, cy, angle, length, width, color, sw=8, bend=0.35):
    OUT.append(flame(cx, cy, angle, length, width, color, sw, bend))
    OUT.append(flame(2 * CX - cx, cy, 180 - angle, length, width, color, sw, -bend))


def inside(point, poly):
    x, y = point
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def scales(region, avoid, top, bottom, step, color, width):
    """Rows of fish-scale arcs, offset each row, kept inside `region`."""
    row = 0
    y = top
    while y < bottom:
        x = CX - 400 + (step / 2 if row % 2 else 0)
        while x < CX + 400:
            r = step / 2
            if all(inside(p, region) for p in [(x - r, y), (x + r, y), (x, y + r)]) \
                    and not any(inside((x, y), a) for a in avoid):
                OUT.append(f'<path d="M{x - r:.1f} {y:.1f} A{r:.1f} {r:.1f} 0 0 0 {x + r:.1f} {y:.1f}" '
                           f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')
            x += step
        y += step * 0.55
        row += 1


OUT.append('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <radialGradient id="iris" cx="0.5" cy="0.4" r="0.6">
      <stop offset="0" stop-color="#ffe08a"/>
      <stop offset="0.55" stop-color="#ffc23c"/>
      <stop offset="1" stop-color="#16c060"/>
    </radialGradient>
    <clipPath id="body">
      <rect x="100" y="100" width="824" height="824" rx="185"/>
    </clipPath>
  </defs>
  <rect x="100" y="100" width="824" height="824" rx="185" fill="#000000"/>
  <g clip-path="url(#body)">
  <g transform="translate(512 -90) scale(1.12 1) translate(-512 0)">''')

# --- serpentine neck --------------------------------------------------------
def neck_x(y):
    return CX + 46 * math.sin((y - 700) / 120)


def neck_half(y):
    return 150 + (y - 700) * 0.16


ys = [700 + i * 20 for i in range(23)]
right = [(neck_x(y) + neck_half(y), y) for y in ys]
left = [(neck_x(y) - neck_half(y), y) for y in ys]
neck = right + left[::-1]
OUT.append(f'<path d="{smooth(neck)}" fill="{GREEN[1]}" stroke="{INK}" stroke-width="14" '
           f'stroke-linejoin="round"/>')
# Belly plates down the front, following the curve.
belly = []
for y in range(724, 1140, 52):
    cx, half = neck_x(y + 26), neck_half(y) * 0.5
    plate = [(cx, y), (cx + half, y + 6), (cx + half * 0.96, y + 40), (cx, y + 50),
             (cx - half * 0.96, y + 40), (cx - half, y + 6)]
    belly.append(plate)
    OUT.append(f'<path d="{smooth(plate)}" fill="{GOLD[1]}" stroke="{INK}" stroke-width="9" '
               f'stroke-linejoin="round"/>')
scales(neck, belly, 760, 1100, 34, GREEN[2], 6)

# --- flame mane behind the head ---------------------------------------------
for i, (angle, length, width, color) in enumerate([
        (-30, 150, 66, RED[1]), (-5, 160, 70, RED[1]), (20, 160, 70, RED[1]),
        (45, 140, 62, RED[1]), (-55, 120, 56, RED[1])]):
    base = [(700, 420), (712, 480), (706, 540), (688, 600), (676, 370)][i]
    flames(*base, angle, length, width, color, sw=10)
for angle, base in [(-20, (706, 450)), (8, (708, 512)), (34, (696, 572))]:
    flames(*base, angle, 96, 38, GOLD[1], sw=7)

# --- antler horns ---------------------------------------------------------
stroke([(566, 336), (596, 288), (640, 252), (700, 232)], GOLD[1], 32, outline=16)
stroke([(612, 270), (606, 236), (620, 210)], GOLD[1], 22, outline=14)
stroke([(656, 246), (682, 214), (716, 204)], GOLD[1], 18, outline=12)

# --- head -----------------------------------------------------------------
head_half = [(512, 318), (582, 322), (640, 344), (684, 392), (700, 452), (690, 512),
             (716, 556), (742, 610), (736, 672), (698, 716), (612, 740), (512, 748)]
head = symmetric(head_half)
fill(head, GREEN[1], sw=14)

# The snout: a wide, flat block across the lower face.
snout_half = [(512, 520), (580, 524), (660, 548), (706, 600), (704, 662), (668, 700),
              (590, 716), (512, 720)]
snout = symmetric(snout_half)
fill(snout, GREEN[0], sw=10)
# Bridge running up between the eyes.
bridge = symmetric([(512, 400), (546, 410), (560, 470), (566, 530), (512, 536)])
fill(bridge, GREEN[0], sw=0, opacity=0.8)

# Scales over the brow and cheeks, kept off the snout, eyes and bridge.
eye_ridge = [(536, 480), (556, 410), (612, 372), (676, 404), (700, 480), (612, 500)]
scales(head, [snout, bridge, eye_ridge, mirror(eye_ridge)], 330, 720, 30, GREEN[2], 5)
scales(snout, [], 540, 610, 24, "#3ccf6e", 4)

# Crocodile eyes: high, raised ridges arching over a slit-pupil eye.
pair(eye_ridge, RED[1], sw=12)
for i, t in enumerate((0.25, 0.5, 0.75)):
    x = 556 + t * 130
    y = 420 - math.sin(t * math.pi) * 46 + (0 if i != 1 else -4)
    flames(x, y, -90 + (t - 0.5) * 70, 36, 18, RED[1], sw=6, bend=0.1)
EX, EY = 618, 452
eye = [(566, 466), (590, 426), (628, 414), (664, 432), (678, 466), (622, 478)]
pair(eye, "url(#iris)", sw=9)
for x in (EX, 2 * CX - EX):
    OUT.append(f'<ellipse cx="{x}" cy="{EY}" rx="8" ry="24" fill="{INK}"/>')
    OUT.append(f'<circle cx="{x + (-14 if x > CX else 14)}" cy="{EY - 10}" r="6" fill="#ffffff"/>')
# A level upper lid: calm, neither wide-eyed nor glaring.
lid = [(566, 428), (590, 412), (628, 404), (666, 414), (680, 428), (626, 422)]
pair(lid, RED[1], sw=9)

# Forehead pearl.
OUT.append(f'<polygon points="512,334 540,362 512,394 484,362" fill="{GOLD[1]}" stroke="{INK}" '
           f'stroke-width="9" stroke-linejoin="round"/>')
OUT.append(f'<circle cx="512" cy="362" r="9" fill="{RED[1]}"/>')

# Nostrils: small dark flares rimmed in red, close together on the snout.
pair([(540, 578), (556, 560), (582, 556), (592, 572), (578, 590), (552, 592)], RED[1], sw=9)
pair([(552, 578), (562, 568), (578, 566), (582, 574), (574, 582), (558, 584)], INK, sw=0)

# Mouth: a wide, closed, level line across the snout with fangs over the lip.
OUT.append(f'<path d="M{CX - 186} 666 Q{CX - 90} 684 {CX} 678 Q{CX + 90} 684 {CX + 186} 666" '
           f'fill="none" stroke="{INK}" stroke-width="11" stroke-linecap="round"/>')
pair([(590, 676), (612, 674), (600, 712)], "#fff6dc", sw=6)
pair([(650, 668), (668, 664), (660, 696)], "#fff6dc", sw=6)
# Teeth row hint along the lip.
for x in range(CX - 150, CX + 151, 30):
    if abs(x - CX) not in (90, 150):
        OUT.append(f'<circle cx="{x}" cy="{676 + abs(x - CX) * -0.05:.1f}" r="4" fill="{GOLD[0]}"/>')

# Whiskers: long serpentine barbels sweeping out from the snout.
stroke([(690, 620), (770, 600), (836, 640), (840, 730), (800, 800), (836, 880)], RED[1], 14)
stroke([(668, 686), (720, 730), (744, 800), (720, 870)], GOLD[1], 10)

# Cheek fins along the jaw.
for angle, base, length in [(10, (720, 600), 90), (35, (712, 650), 80), (60, (690, 700), 70)]:
    flames(*base, angle, length, 26, GREEN[1], sw=8, bend=0.25)

# Beard: three bold flame tufts under the chin.
for angle, dx, length in [(90, 0, 118), (104, 56, 100), (118, 108, 82)]:
    OUT.append(flame(CX + dx, 740, angle, length, 52, RED[1], sw=9, bend=0.12))
    if dx:
        OUT.append(flame(CX - dx, 740, 180 - angle, length, 52, RED[1], sw=9, bend=-0.12))

OUT.append('</g>')
OUT.append('</g>')
OUT.append('</svg>')
print("\n".join(OUT))
