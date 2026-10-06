"""Generates omawrite-icon.svg: a front-facing guardian lion (shishi) face,
thick and blocky, in a kaleidoscopic red and green burst.

    python3 macos/make_icon.py > macos/omawrite-icon.svg

Everything off the center line is drawn once and mirrored, so the face is
exactly symmetrical.
"""

import math

RED = ["#ff6a5c", "#e8202e", "#9c0e1c"]     # light, primary, deep
GREEN = ["#7af29b", "#16c060", "#08693a"]
GOLD = ["#ffe08a", "#ffc23c", "#c98a12"]
INK = "#0a0f0c"
CX, CY = 512, 520
OUT = []


def fmt(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


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


def shape(points, fill, sw=10, both=True, closed=True, extra=""):
    """A smooth filled shape with an ink outline; mirrored unless both=False."""
    sets = [points, mirror(points)[::-1]] if both else [points]
    for pts in sets:
        OUT.append(f'<path d="{smooth(pts, closed)}" fill="{fill}" stroke="{INK}" '
                   f'stroke-width="{sw}" stroke-linejoin="round" {extra}/>')


def circle(x, y, r, fill, sw=8, both=True, stroke=INK, extra=""):
    for px in ([x, 2 * CX - x] if both and x != CX else [x]):
        OUT.append(f'<circle cx="{px:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" '
                   f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def star(cx, cy, points, r_out, r_in, rot=0.0):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi * i / points + rot
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def spiral(cx, cy, r, turns, mirror_x=False):
    """An Archimedean spiral path, used for mane curls and cheek swirls."""
    pts = []
    steps = int(turns * 28)
    for i in range(steps + 1):
        t = i / steps
        a = t * turns * 2 * math.pi
        rr = r * (1 - t) + 2
        x = cx + math.cos(a) * rr * (-1 if mirror_x else 1)
        pts.append((x, cy + math.sin(a) * rr))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def curl(cx, cy, r, fill, ring, mirror_x=False):
    circle(cx, cy, r, fill, sw=9, both=False)
    OUT.append(f'<path d="{spiral(cx, cy, r * 0.78, 2.2, mirror_x)}" fill="none" '
               f'stroke="{ring}" stroke-width="{r * 0.16:.1f}" stroke-linecap="round"/>')


# --- background: a kaleidoscope burst -------------------------------------
OUT.append('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <radialGradient id="bg" cx="0.5" cy="0.5" r="0.7">
      <stop offset="0" stop-color="#1f3d2a"/>
      <stop offset="0.55" stop-color="#0d1c14"/>
      <stop offset="1" stop-color="#040806"/>
    </radialGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#ffe08a" stop-opacity="0.55"/>
      <stop offset="1" stop-color="#ffe08a" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="iris" cx="0.5" cy="0.45" r="0.55">
      <stop offset="0" stop-color="#ffe08a"/>
      <stop offset="0.5" stop-color="#ffc23c"/>
      <stop offset="1" stop-color="#e8202e"/>
    </radialGradient>
    <clipPath id="body">
      <rect x="100" y="100" width="824" height="824" rx="185"/>
    </clipPath>
  </defs>
  <rect x="100" y="100" width="824" height="824" rx="185" fill="url(#bg)"/>
  <g clip-path="url(#body)">''')

# Rays alternating red and green, fanned from the center.
rays = 24
for i in range(rays):
    a0 = 2 * math.pi * i / rays
    a1 = 2 * math.pi * (i + 1) / rays
    pts = [(CX, CY), (CX + math.cos(a0) * 760, CY + math.sin(a0) * 760),
           (CX + math.cos(a1) * 760, CY + math.sin(a1) * 760)]
    color = RED[2] if i % 2 else GREEN[2]
    OUT.append(f'<polygon points="{fmt(pts)}" fill="{color}" opacity="0.55"/>')

# Nested stars, each turned half a point from the last.
for k, (r_out, color) in enumerate([(470, GREEN[1]), (420, RED[1]), (372, GOLD[1]),
                                    (338, GREEN[2]), (310, RED[2])]):
    pts = star(CX, CY, 16, r_out, r_out * 0.8, rot=k * math.pi / 16)
    OUT.append(f'<polygon points="{fmt(pts)}" fill="{color}" stroke="{INK}" '
               f'stroke-width="6" stroke-linejoin="round"/>')
# A dark halo so the mane reads against the burst.
OUT.append(f'<circle cx="{CX}" cy="{CY}" r="318" fill="{INK}"/>')
OUT.append(f'<circle cx="{CX}" cy="{CY}" r="306" fill="none" stroke="{GOLD[1]}" '
           f'stroke-width="6" stroke-dasharray="1 16" stroke-linecap="round"/>')
OUT.append(f'<circle cx="{CX}" cy="{CY}" r="300" fill="url(#glow)"/>')

# --- mane: two rings of spiral curls ---------------------------------------
for ring, (radius, count, size, offset) in enumerate([(262, 18, 50, 0.0), (218, 16, 42, 0.5)]):
    for i in range(count):
        a = 2 * math.pi * (i + offset) / count - math.pi / 2
        x, y = CX + math.cos(a) * radius, CY + math.sin(a) * radius * 1.02
        fill = GREEN[1] if (i + ring) % 2 else RED[1]
        ringc = GOLD[0] if (i + ring) % 2 else GREEN[0]
        curl(x, y, size, fill, ringc, mirror_x=x > CX)

# --- face ------------------------------------------------------------------
# A broad, blocky head: squarish forehead, wide cheeks, heavy jaw.
face = [(512, 300), (608, 306), (684, 330), (722, 392), (730, 470), (722, 560),
        (700, 640), (650, 700), (580, 730), (512, 738)]
face_full = face + mirror(face)[::-1][1:-1]
OUT.append(f'<path d="{smooth(face_full)}" fill="{RED[1]}" stroke="{INK}" '
           f'stroke-width="14" stroke-linejoin="round"/>')
# Inner face plane, lighter, for a blocky carved look.
inner = [(512, 340), (590, 346), (650, 372), (676, 430), (672, 520), (640, 600),
         (590, 650), (512, 668)]
OUT.append(f'<path d="{smooth(inner + mirror(inner)[::-1][1:-1])}" fill="{RED[0]}" '
           f'opacity="0.55"/>')

# Ears: chunky lobes at the top corners.
shape([(676, 316), (744, 262), (790, 300), (770, 372), (716, 380)], GREEN[1], sw=11)
shape([(700, 322), (744, 292), (764, 316), (748, 352), (718, 356)], GOLD[1], sw=6)

# Heavy brows that roll outward into curls.
shape([(520, 392), (560, 352), (630, 338), (692, 352), (716, 392), (690, 414),
       (640, 398), (584, 404), (536, 420)], GREEN[1], sw=11)
for side in (False, True):
    x = 700 if not side else 2 * CX - 700
    OUT.append(f'<path d="{spiral(x, 384, 22, 1.6, side)}" fill="none" stroke="{GOLD[0]}" '
               f'stroke-width="6" stroke-linecap="round"/>')

# Third eye: a gem on the forehead.
gem = [(512, 300), (546, 334), (512, 372), (478, 334)]
OUT.append(f'<polygon points="{fmt(gem)}" fill="{GREEN[1]}" stroke="{INK}" stroke-width="9" '
           f'stroke-linejoin="round"/>')
OUT.append(f'<polygon points="{fmt([(512, 316), (532, 334), (512, 356), (492, 334)])}" '
           f'fill="{GOLD[1]}"/>')
circle(512, 334, 7, INK, sw=0)

# Eyes: big, round and bulging, with a level upper lid for a calm gaze.
EX, EY, ER = 612, 470, 62
circle(EX, EY, ER + 16, GREEN[1], sw=11)
circle(EX, EY, ER, "#fff6dc", sw=7)
circle(EX, EY, ER * 0.72, "url(#iris)", sw=6)
for r in (ER * 0.55, ER * 0.40):
    circle(EX, EY, r, "none", sw=3, stroke=RED[2])
circle(EX, EY, ER * 0.26, INK, sw=0)
circle(EX - 12, EY - 14, 8, "#ffffff", sw=0)
# The lid: a flat band across the top of the eye in the face color.
lid = [(EX - ER - 14, EY - 18), (EX - ER + 4, EY - ER - 4), (EX + ER - 4, EY - ER - 4),
       (EX + ER + 14, EY - 18)]
for pts in (lid, mirror(lid)[::-1]):
    OUT.append(f'<path d="M{pts[0][0]:.1f} {pts[0][1]:.1f} '
               f'C{pts[1][0]:.1f} {pts[1][1]:.1f} {pts[2][0]:.1f} {pts[2][1]:.1f} '
               f'{pts[3][0]:.1f} {pts[3][1]:.1f} Z" fill="{RED[1]}" stroke="{INK}" '
               f'stroke-width="9" stroke-linejoin="round"/>')
OUT.append(f'<path d="M{EX - ER - 14} {EY - 18} L{EX + ER + 14} {EY - 18}" stroke="{GOLD[1]}" '
           f'stroke-width="6" stroke-linecap="round"/>')
OUT.append(f'<path d="M{2 * CX - EX - ER - 14} {EY - 18} L{2 * CX - EX + ER + 14} {EY - 18}" '
           f'stroke="{GOLD[1]}" stroke-width="6" stroke-linecap="round"/>')

# Cheeks: puffed rounds with swirls.
for side in (False, True):
    x = 656 if not side else 2 * CX - 656
    circle(x, 588, 50, RED[0], sw=10, both=False)
    OUT.append(f'<path d="{spiral(x, 588, 36, 2.0, side)}" fill="none" stroke="{RED[2]}" '
               f'stroke-width="7" stroke-linecap="round"/>')

# Nose: a broad block with flared nostrils.
nose = [(512, 430), (548, 446), (566, 520), (606, 560), (590, 600), (540, 610), (512, 604)]
OUT.append(f'<path d="{smooth(nose + mirror(nose)[::-1][1:-1])}" fill="{GREEN[1]}" '
           f'stroke="{INK}" stroke-width="12" stroke-linejoin="round"/>')
OUT.append(f'<path d="{smooth([(512, 448), (530, 470), (536, 540), (512, 556), (488, 540), (494, 470)])}" '
           f'fill="{GREEN[0]}" opacity="0.7"/>')
circle(560, 578, 18, INK, sw=0)
circle(560, 578, 8, GREEN[2], sw=0)

# Mouth: wide and closed, with lips turned in a level line and two small fangs.
lip = [(512, 640), (560, 632), (620, 644), (650, 668), (612, 690), (512, 694)]
OUT.append(f'<path d="{smooth(lip + mirror(lip)[::-1][1:-1])}" fill="{RED[2]}" '
           f'stroke="{INK}" stroke-width="11" stroke-linejoin="round"/>')
OUT.append(f'<path d="M{CX - 132} 664 Q{CX} 676 {CX + 132} 664" fill="none" '
           f'stroke="{INK}" stroke-width="9" stroke-linecap="round"/>')
shape([(572, 664), (590, 664), (582, 700)], "#fff6dc", sw=6)

# Beard: a block of curls under the chin.
for i, (dx, dy, r) in enumerate([(0, 772, 40), (-66, 754, 34), (66, 754, 34), (-34, 826, 32),
                                 (34, 826, 32), (0, 872, 28)]):
    fill = GREEN[1] if i % 2 else GOLD[1]
    ring = GOLD[0] if i % 2 else RED[1]
    curl(CX + dx, dy, r, fill, ring, mirror_x=dx > 0)

OUT.append('</g>')
OUT.append('</svg>')
print("\n".join(OUT))
