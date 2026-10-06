"""Generates omawrite-icon.svg: a blocky, menacing temple-terrace dragon head
(like the glazed heads on Chinese temple verandas), drawn as 32x32 pixel art
and mirrored down the middle, on a thick vertical neck.

    python3 macos/make_icon.py > macos/omawrite-icon.svg

Edit LEFT to change the design: it is the left 16 columns of each row, and
the right half is its mirror. Earlier designs live in variants/.
"""

import hashlib

PALETTE = {
    "K": "#141414",  # outline
    "G": "#1fd25c",  # glazed green
    "g": "#0c8a3a",  # deep green
    "L": "#8dffa4",  # green highlight
    "R": "#ff2b2b",  # red
    "r": "#a8101c",  # deep red
    "O": "#ff8a1f",  # orange
    "Y": "#ffd23c",  # gold
    "y": "#c9920f",  # deep gold
    "W": "#fff3d4",  # teeth, eye white
    "m": "#4f0610",  # mouth
}

LEFT = [
    "...KK...........",
    "..KYYK........KK",
    "..KYyYK......KRR",
    "...KYYYK....KROR",
    "...KKYyYK..KROOO",
    ".....KYYYKKROOOO",
    "......KYYKKKKKKK",
    "..KK..KGGgGGLGGG",
    ".KRRK.KGgGGgGGLG",
    "KROORKGKRRRKGgGG",
    ".KRROKGKRRRRRKGG",
    "..KRRKKKKKKRRRKG",
    ".KROOKYYYYYKRRKG",
    "KROORKOOKKWKKKGG",
    ".KRROKOOKKOKgGGG",
    "..KRRKrOOOrKGGgG",
    ".KROOKKKKKKGKKKK",
    "KROORKGGGgGKLLLL",
    ".KRRKGGGGGGKLKKL",
    "..KKKGgGGGGGKKKK",
    "...KYYYYYYYYYYYY",
    "...KWWmWWWmWWmWm",
    "...KWmmmWWmmmmmm",
    "...KmmmmmWmmrRRR",
    "...KWmmmmmmmrRRR",
    "...KWWmWWmWWmWWm",
    "...KYYYYYYYYYYYY",
    "....KKGGgGGGgGGG",
    "......KGgGGgGYYY",
    "......KGGgGGgyyy",
    "......KgGGgGGYYY",
    "......KGGgGGgYYY",
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
    return (digest / 255 - 0.5) * 0.14


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
        if key != "K":
            # A lit top edge and shaded bottom edge give each block some depth.
            out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{CELL:.2f}" height="{CELL * 0.16:.2f}" '
                       f'fill="{shade(base, 0.22)}"/>')
            out.append(f'<rect x="{x:.2f}" y="{y + CELL * 0.84:.2f}" width="{CELL:.2f}" '
                       f'height="{CELL * 0.16:.2f}" fill="{shade(base, -0.25)}"/>')
out.append('  </g>')
out.append('</svg>')
print("\n".join(out))
