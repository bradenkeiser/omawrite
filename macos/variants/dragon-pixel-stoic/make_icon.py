"""Generates omawrite-icon.svg: a blocky, stoic temple-terrace dragon head
(like the glazed heads on Chinese temple verandas), drawn as 32x32 pixel art
in two tones (scarlet outlines, neon green interiors, black for definition)
and mirrored down the middle, on a thick vertical neck.

    python3 macos/make_icon.py > macos/omawrite-icon.svg

Edit LEFT to change the design: it is the left 16 columns of each row, and
the right half is its mirror. Earlier designs live in variants/.
"""

import hashlib

PALETTE = {
    "R": "#ff2400",  # scarlet: every outline (body, eyes, mouth)
    "G": "#39ff14",  # neon green: every interior
}

LEFT = [
    "................",
    "...RR..........R",
    "...RGR........RG",
    "....RGR......RGG",
    ".....RGR....RGGG",
    "......RGR..RGGGG",
    ".......RGRRGGGGG",
    "......RGGGGGGGGG",
    "..RR..RGGGGGGGGG",
    ".RGGRRGGGGGGGGGG",
    "RGGGGRG.......GG",
    ".RGGGRG..RRR..GG",
    "..RRGRG.R.G.R.GG",
    ".RGGGRG.RGRGR.GG",
    "RGGGGRG.R.G.R.GG",
    ".RGGGRG..RRR..GG",
    "..RRGRG.......GG",
    ".RGGGRGGGGGGGGGG",
    "..RRRRRGGGGGGGGG",
    "......RGGGGGG..G",
    "......RGGGGGGGGG",
    "......RRRRRRRRRR",
    "......RGGGGGGGGG",
    ".......RGGGGGGGG",
    "........RGGGGGGG",
    "........RGG.GGGG",
    "........RGGGG.GG",
    "........RG.GGGGG",
    "........RGGGG.GG",
    "........RGG.GGGG",
    "........RGGGG.GG",
    "........RG.GGGGG",
]

assert len(LEFT) == 32 and all(len(row) == 16 for row in LEFT), "LEFT must be 32 rows of 16"
ROWS = [row + row[::-1] for row in LEFT]

# The grid fills the macOS icon body: 824px inset 100px on a 1024 canvas.
ORIGIN, CELL = 100.0, 824.0 / 32


def shade(color, amount):
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    f = 1 + amount
    return "#" + "".join(f"{max(0, min(255, round(c * f))):02x}" for c in (r, g, b))


def noise(col, row):
    """Stable per-block brightness jitter for a Minecraft-style texture,
    mirrored so both halves match."""
    col = min(col, 31 - col)
    digest = hashlib.md5(f"{col},{row}".encode()).digest()[0]
    return (digest / 255 - 0.5) * 0.08


out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" shape-rendering="crispEdges">',
       '  <defs>',
       '    <clipPath id="body"><rect x="100" y="100" width="824" height="824" rx="185"/></clipPath>',
       '  </defs>',
       '  <rect x="100" y="100" width="824" height="824" rx="185" fill="#000000"/>',
       '  <g clip-path="url(#body)">']
for row, line in enumerate(ROWS):
    for col, key in enumerate(line):
        if key == ".":
            continue
        base = PALETTE[key]
        x, y = ORIGIN + col * CELL, ORIGIN + row * CELL
        out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{CELL + 0.6:.2f}" height="{CELL + 0.6:.2f}" '
                   f'fill="{shade(base, noise(col, row))}"/>')
        # Light the top edge and shade the bottom edge of each shape (not of
        # every block), so flat areas stay flat but the shapes read as blocks.
        if row == 0 or ROWS[row - 1][col] != key:
            out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{CELL:.2f}" height="{CELL * 0.16:.2f}" '
                       f'fill="{shade(base, 0.18)}"/>')
        if row == 31 or ROWS[row + 1][col] != key:
            out.append(f'<rect x="{x:.2f}" y="{y + CELL * 0.84:.2f}" width="{CELL:.2f}" '
                       f'height="{CELL * 0.16:.2f}" fill="{shade(base, -0.28)}"/>')
out.append('  </g>')
out.append('</svg>')
print("\n".join(out))
