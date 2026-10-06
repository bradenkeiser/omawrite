"""Generates omawrite-icon.svg: a mandala dragon head in profile whose neck is
the paired stem of a DNA hairpin and whose head is the unpaired loop.

    python3 macos/make_icon.py > macos/omawrite-icon.svg
"""

import math

RED = ["#ff5a4e", "#e8202e", "#a3101f"]      # light, primary, deep
GREEN = ["#6fe08a", "#14b85a", "#0b6e3a"]
INK = "#0b1410"


def catmull_rom(points, closed=False):
    """Smooth path through points as cubic Beziers."""
    pts = points[:]
    n = len(pts)
    d = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    count = n if closed else n - 1
    for i in range(count):
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    if closed:
        d.append("Z")
    return " ".join(d)


def sample(points, steps=24, closed=False):
    """Dense polyline along the same Catmull-Rom curve (for beads and rungs)."""
    out = []
    n = len(points)
    count = n if closed else n - 1
    for i in range(count):
        p0 = points[(i - 1) % n] if (closed or i > 0) else points[0]
        p1, p2 = points[i], points[(i + 1) % n]
        p3 = points[(i + 2) % n] if (closed or i + 2 < n) else points[-1]
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t
                       + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                       + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                for k in range(2)))
    if not closed:
        out.append(points[-1])
    return out


def resample(poly, count):
    """`count` points evenly spaced by arc length."""
    lengths = [0.0]
    for a, b in zip(poly, poly[1:]):
        lengths.append(lengths[-1] + math.dist(a, b))
    total = lengths[-1]
    out, j = [], 0
    for i in range(count):
        target = total * i / (count - 1)
        while j < len(lengths) - 2 and lengths[j + 1] < target:
            j += 1
        seg = lengths[j + 1] - lengths[j] or 1
        t = (target - lengths[j]) / seg
        a, b = poly[j], poly[j + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def inside(point, poly):
    x, y = point
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def petal(cx, cy, angle, length, width, fill, stroke=INK, sw=4, opacity=1.0):
    """A pointed leaf from (cx, cy) outward at `angle` degrees."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    tip = (cx + ux * length, cy + uy * length)
    c1 = (cx + ux * length * 0.35 + px * width, cy + uy * length * 0.35 + py * width)
    c2 = (cx + ux * length * 0.35 - px * width, cy + uy * length * 0.35 - py * width)
    return (f'<path d="M{cx:.1f} {cy:.1f} Q{c1[0]:.1f} {c1[1]:.1f} {tip[0]:.1f} {tip[1]:.1f} '
            f'Q{c2[0]:.1f} {c2[1]:.1f} {cx:.1f} {cy:.1f}Z" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linejoin="round" opacity="{opacity}"/>')


# --- the two strands -------------------------------------------------------
# Back strand (red): up the back of the neck, over the skull, along the snout.
back = [(392, 1010), (384, 820), (370, 690), (350, 580), (336, 470), (366, 360),
        (450, 292), (556, 276), (652, 314), (752, 352), (836, 380), (884, 414), (898, 468)]
# Front strand (green): up the throat, under the jaw, to the same snout tip.
front = [(592, 1010), (578, 820), (562, 700), (562, 628), (612, 580), (700, 562),
         (790, 548), (862, 522), (898, 468)]

back_poly = sample(back)
front_poly = sample(front)
# The stem is where the strands pair; above it they open into the loop.
back_split = next(i for i, (_, y) in enumerate(back_poly) if y < 600)
front_split = next(i for i, (_, y) in enumerate(front_poly) if y < 640)
head_outline = back_poly[back_split:] + front_poly[front_split:][::-1][1:]

parts = []
parts.append('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <radialGradient id="bg" cx="0.55" cy="0.38" r="0.75">
      <stop offset="0" stop-color="#16261d"/>
      <stop offset="0.6" stop-color="#0c1511"/>
      <stop offset="1" stop-color="#050807"/>
    </radialGradient>
    <radialGradient id="headfill" cx="0.42" cy="0.45" r="0.7">
      <stop offset="0" stop-color="#1d3b2a"/>
      <stop offset="1" stop-color="#0d1a13"/>
    </radialGradient>
    <linearGradient id="redstrand" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0" stop-color="''' + RED[2] + '''"/>
      <stop offset="0.5" stop-color="''' + RED[1] + '''"/>
      <stop offset="1" stop-color="''' + RED[0] + '''"/>
    </linearGradient>
    <linearGradient id="greenstrand" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0" stop-color="''' + GREEN[2] + '''"/>
      <stop offset="0.5" stop-color="''' + GREEN[1] + '''"/>
      <stop offset="1" stop-color="''' + GREEN[0] + '''"/>
    </linearGradient>
    <radialGradient id="iris" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#ffd166"/>
      <stop offset="0.55" stop-color="''' + GREEN[1] + '''"/>
      <stop offset="1" stop-color="''' + GREEN[2] + '''"/>
    </radialGradient>
    <clipPath id="body">
      <rect x="100" y="100" width="824" height="824" rx="185"/>
    </clipPath>
  </defs>
  <rect x="100" y="100" width="824" height="824" rx="185" fill="url(#bg)"/>
  <g clip-path="url(#body)">''')

# Background mandala halo behind the head.
hx, hy = 540, 430
for ring, (radius, count, length, width, color, op) in enumerate([
        (300, 32, 70, 16, GREEN[2], 0.35), (250, 24, 60, 15, RED[2], 0.4)]):
    for i in range(count):
        ang = 360 * i / count + ring * 7.5
        a = math.radians(ang)
        sx, sy = hx + math.cos(a) * radius, hy + math.sin(a) * radius
        if 100 < sx < 924 and 100 < sy < 924:
            parts.append(petal(sx, sy, ang, length, width, color, stroke="none", opacity=op))
for r, color, op in [(330, GREEN[1], 0.18), (232, RED[1], 0.22)]:
    parts.append(f'<circle cx="{hx}" cy="{hy}" r="{r}" fill="none" stroke="{color}" '
                 f'stroke-width="3" stroke-dasharray="2 14" stroke-linecap="round" opacity="{op}"/>')

# Crest: a fan of petals sweeping back from the skull, alternating strands.
pivot = (382, 392)
for i, ang in enumerate(range(150, 262, 14)):
    length = 230 - abs(ang - 205) * 1.6
    fill = RED[1] if i % 2 == 0 else GREEN[1]
    parts.append(petal(*pivot, ang, length, 34, fill, sw=5))
for i, ang in enumerate(range(157, 255, 14)):
    length = 150 - abs(ang - 205) * 1.1
    fill = RED[0] if i % 2 else GREEN[0]
    parts.append(petal(*pivot, ang, length, 20, fill, sw=4))

# Two horns sweeping back over the crest.
for horn, width in [([(492, 296), (440, 214), (350, 166), (250, 156)], 22),
                    ([(440, 318), (380, 262), (300, 236), (214, 244)], 17)]:
    d = catmull_rom(horn)
    parts.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width + 14}" '
                 f'stroke-linecap="round"/>')
    parts.append(f'<path d="{d}" fill="none" stroke="{RED[0]}" stroke-width="{width}" '
                 f'stroke-linecap="round"/>')
    for t in (0.3, 0.55, 0.8):
        x, y = resample(sample(horn), 21)[int(t * 20)]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{width * 0.22:.1f}" fill="{GREEN[1]}"/>')

# Head: the hairpin loop, filled, with a dotted mandala texture inside it.
parts.append(f'<path d="{catmull_rom(resample(head_outline, 40), closed=True)}" '
             f'fill="url(#headfill)"/>')
ex, ey = 580, 404
for ring in range(1, 12):
    radius = ring * 30
    count = max(8, ring * 9)
    for i in range(count):
        a = 2 * math.pi * i / count + ring * 0.21
        p = (ex + math.cos(a) * radius, ey + math.sin(a) * radius)
        if inside(p, head_outline) and radius > 96:
            color = RED[0] if ring % 2 else GREEN[0]
            parts.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{3.2 + (ring % 3)}" '
                         f'fill="{color}" opacity="0.55"/>')

# Base-pair rungs across the stem: each half takes its strand's color.
stem_back = resample(back_poly[:back_split + 1], 9)
stem_front = resample(front_poly[:front_split + 1], 9)
for (bx, by), (fx, fy) in zip(stem_back[:-1], stem_front[:-1]):
    mx, my = (bx + fx) / 2, (by + fy) / 2
    parts.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{fx:.1f}" y2="{fy:.1f}" '
                 f'stroke="{INK}" stroke-width="24" stroke-linecap="round"/>')
    parts.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{mx - 4:.1f}" y2="{my:.1f}" '
                 f'stroke="{RED[1]}" stroke-width="14" stroke-linecap="round"/>')
    parts.append(f'<line x1="{mx + 4:.1f}" y1="{my:.1f}" x2="{fx:.1f}" y2="{fy:.1f}" '
                 f'stroke="{GREEN[1]}" stroke-width="14" stroke-linecap="round"/>')

# The strands themselves, outlined in ink.
for points, grad in [(back, "redstrand"), (front, "greenstrand")]:
    d = catmull_rom(points)
    parts.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="46" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')
    parts.append(f'<path d="{d}" fill="none" stroke="url(#{grad})" stroke-width="30" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')

# Unpaired nucleotides: beads along the loop.
loop_beads = resample(head_outline, 26)[1:-1]
for i, (x, y) in enumerate(loop_beads):
    color = RED[0] if i % 2 == 0 else GREEN[0]
    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="{color}" '
                 f'stroke="{INK}" stroke-width="3"/>')

# Jaw frill: small petals under the jaw.
for i, ang in enumerate(range(60, 140, 16)):
    parts.append(petal(650 + i * 30, 572 - i * 5, ang, 66 - i * 6, 14,
                       GREEN[1] if i % 2 else RED[1], sw=4))

# Eye: a mandala rosette with a calm, half-lidded eye.
for i in range(16):
    ang = 360 * i / 16
    parts.append(petal(ex, ey, ang, 92, 20, RED[1] if i % 2 else RED[2], sw=4))
for i in range(12):
    ang = 360 * i / 12 + 15
    parts.append(petal(ex, ey, ang, 70, 18, GREEN[1] if i % 2 else GREEN[0], sw=3.5))
parts.append(f'<circle cx="{ex}" cy="{ey}" r="50" fill="{INK}"/>')
parts.append(f'<circle cx="{ex}" cy="{ey}" r="46" fill="none" stroke="{RED[0]}" '
             f'stroke-width="3" stroke-dasharray="3 7"/>')
# Almond eye, slightly narrowed by a level upper lid: neutral, not fierce.
parts.append(f'<path d="M{ex - 40} {ey + 4} Q{ex} {ey - 30} {ex + 42} {ey + 2} '
             f'Q{ex} {ey + 30} {ex - 40} {ey + 4}Z" fill="url(#iris)" stroke="{INK}" '
             f'stroke-width="4"/>')
parts.append(f'<circle cx="{ex + 2}" cy="{ey + 4}" r="12" fill="{INK}"/>')
parts.append(f'<path d="M{ex - 44} {ey - 6} L{ex + 46} {ey - 8}" stroke="{INK}" '
             f'stroke-width="9" stroke-linecap="round"/>')
parts.append(f'<path d="M{ex - 40} {ey - 13} Q{ex} {ey - 20} {ex + 42} {ey - 15}" fill="none" '
             f'stroke="{RED[0]}" stroke-width="4" stroke-linecap="round"/>')
parts.append(f'<circle cx="{ex + 12}" cy="{ey - 1}" r="4" fill="#ffffff" opacity="0.9"/>')

# Nostril curl and a closed, level mouth line.
parts.append(f'<path d="M848 404 q14 -12 26 0 q-10 9 -21 4" fill="none" stroke="{INK}" '
             f'stroke-width="7" stroke-linecap="round"/>')
parts.append(f'<path d="M884 494 Q800 508 700 516" fill="none" stroke="{INK}" '
             f'stroke-width="8" stroke-linecap="round"/>')

# Whiskers: two thin strands trailing from the muzzle, twisting like a helix.
for phase, color in [(0.0, RED[0]), (math.pi, GREEN[0])]:
    pts = []
    for k in range(28):
        t = k / 27
        x = 870 - t * 150 + math.sin(t * 2 * math.pi * 1.5 + phase) * 22
        y = 530 + t * 330
        pts.append((x, y))
    d = catmull_rom(pts)
    parts.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="15" stroke-linecap="round"/>')
    parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"/>')

parts.append('</g>')
parts.append('</svg>')
print("\n".join(parts))
