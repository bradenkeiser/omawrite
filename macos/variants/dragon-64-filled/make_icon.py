"""Generates omawrite-icon.svg: a stoic, blocky temple-terrace dragon head in
two tones (scarlet outlines, neon green interiors, black for definition),
with the rolling curls of a Chinese guardian lion drawn as square spirals.

    python3 macos/make_icon.py > macos/omawrite-icon.svg

The design is rasterized onto a 64x64 block grid. Each part is a shape;
painting it carves a black gap around it, then fills it with a thick
scarlet outline and a green interior. Only the left half is drawn: the
right half is its mirror. Earlier designs live in variants/.
"""

N = 64
HALF = N // 2
PALETTE = {"R": "#ff2400", "G": "#39ff14"}  # scarlet outline, neon green fill
grid = [["." for _ in range(N)] for _ in range(N)]


def inside(x, y, poly):
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def polygon(points):
    """Blocks whose centers fall inside the polygon (left half only)."""
    return {(x, y) for y in range(N) for x in range(HALF) if inside(x + 0.5, y + 0.5, points)}


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, min(x1, HALF - 1) + 1)
            if 0 <= y < N}


def touches_outside(cell, cells, reach):
    x, y = cell
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            nx, ny = x + dx, y + dy
            # The center line is not an edge: the mirror continues the shape.
            if nx >= HALF:
                nx = N - 1 - nx
            # Nor is the bottom edge: the neck runs on past it.
            if ny >= N:
                continue
            if (nx, ny) not in cells:
                return True
    return False


def paint(cells, outline=3, gap=1):
    """Carve a black gap around `cells`, then fill them: scarlet within
    `outline` blocks of the edge, green inside."""
    for x, y in cells:
        for dy in range(-gap, gap + 1):
            for dx in range(-gap, gap + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < HALF and 0 <= ny < N and (nx, ny) not in cells:
                    grid[ny][nx] = "."
    for x, y in cells:
        grid[y][x] = "R" if touches_outside((x, y), cells, outline - 1) else "G"


def spiral(x0, y0, size, stroke, gap):
    """A square spiral of scarlet `stroke`-wide lines inside a size x size box."""
    step = stroke + gap
    legs = [size - stroke] * 3
    length = size - stroke
    while True:
        length -= step
        if length <= 0:
            break
        legs += [length, length]
    x, y = 0, 0
    heading = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    cells = set()
    for i, leg in enumerate(legs):
        dx, dy = heading[i % 4]
        for _ in range(leg + 1):
            for by in range(stroke):
                for bx in range(stroke):
                    cells.add((x0 + x + bx, y0 + y + by))
            x, y = x + dx, y + dy
        x, y = x - dx, y - dy
    for cx, cy in cells:
        if 0 <= cx < HALF and 0 <= cy < N:
            grid[cy][cx] = "R"


def curl(x0, y0, size, stroke=1, gap=1, outline=2, separate=1):
    """A blocky lionhead curl: a square spiral in an outlined block."""
    paint(rect(x0, y0, x0 + size - 1, y0 + size - 1), outline=outline, gap=separate)
    inset = outline + 1
    spiral(x0 + inset, y0 + inset, size - 2 * inset, stroke, gap)


def mandala_eye(cx, cy, r=6):
    """Square outline around nested diamonds: a blank, staring mandala."""
    paint(rect(cx - r, cy - r, cx + r, cy + r), outline=2)
    rings = {0: "R", 1: "R", 2: "G", 3: ".", 4: "R", 5: "G", 6: "."}
    for y in range(cy - r + 2, cy + r - 1):
        for x in range(cx - r + 2, cx + r - 1):
            grid[y][x] = rings.get(abs(x - cx) + abs(y - cy), ".")


# Neck: thick and strictly vertical, running off the bottom.
paint(rect(18, 46, 31, N - 1))
for y in range(56, N, 4):
    for x in range(22 + (y // 4) % 2 * 2, 31, 4):
        grid[y][x] = "."

# Horns rising from the crown.
paint(polygon([(9, 1), (15, 1), (19, 14), (13, 14)]), outline=2)

# Head: one broad block, tapering to a lean jaw.
paint(polygon([(32, 12), (13, 12), (10, 16), (10, 36), (13, 44), (18, 50), (32, 50)]))

# Crown curl across the top of the head; it meets its mirror in the middle
# as a double scroll.
curl(18, 2, 14)

# Brow: a level band of curls set into the face, a fret-like rolling texture.
for x in (13, 21, 28):
    curl(x, 15, 8, outline=1, separate=0)

# Mandala eyes.
mandala_eye(23, 29)

# Cheek curls, set into the face.
curl(12, 35, 11, outline=1, separate=0)

# Nose: a wide block with black nostrils.
paint(rect(26, 36, 31, 41), outline=2)
for y in (38, 39):
    for x in (28, 29):
        grid[y][x] = "."

# Mouth: closed, a straight thick scarlet line with a black lip above it.
for x in range(17, HALF):
    grid[43][x] = "."
    grid[44][x] = "R"
    grid[45][x] = "R"

# Beard: curls under the chin, paired into opposing scrolls by the mirror.
curl(23, 47, 11)

rows = ["".join(r[:HALF]) + "".join(r[:HALF])[::-1] for r in grid]

# --- SVG --------------------------------------------------------------------
ORIGIN, CELL = 100.0, 824.0 / N


def shade(color, amount):
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{max(0, min(255, round(c * (1 + amount)))):02x}" for c in (r, g, b))


out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" shape-rendering="crispEdges">',
       '  <defs>',
       '    <clipPath id="body"><rect x="100" y="100" width="824" height="824" rx="185"/></clipPath>',
       '  </defs>',
       '  <rect x="100" y="100" width="824" height="824" rx="185" fill="#000000"/>',
       '  <g clip-path="url(#body)">']
for row, line in enumerate(rows):
    y = ORIGIN + row * CELL
    col = 0
    while col < N:  # merge runs of one color into a single rect
        key = line[col]
        end = col
        while end + 1 < N and line[end + 1] == key:
            end += 1
        if key != ".":
            x = ORIGIN + col * CELL
            out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{(end - col + 1) * CELL + 0.5:.2f}" '
                       f'height="{CELL + 0.5:.2f}" fill="{PALETTE[key]}"/>')
            # Light top edges and shade bottom edges of shapes for blockiness.
            for c in range(col, end + 1):
                cx = ORIGIN + c * CELL
                if row == 0 or rows[row - 1][c] != key:
                    out.append(f'<rect x="{cx:.2f}" y="{y:.2f}" width="{CELL + 0.5:.2f}" '
                               f'height="{CELL * 0.22:.2f}" fill="{shade(PALETTE[key], 0.2)}"/>')
                if row == N - 1 or rows[row + 1][c] != key:
                    out.append(f'<rect x="{cx:.2f}" y="{y + CELL * 0.78:.2f}" width="{CELL + 0.5:.2f}" '
                               f'height="{CELL * 0.22:.2f}" fill="{shade(PALETTE[key], -0.32)}"/>')
        col = end + 1
out.append('  </g>')
out.append('</svg>')
print("\n".join(out))
