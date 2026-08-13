#!/usr/bin/env python3
"""Generate the geometry diagrams in images/.

Four files, from two drawings:

    points-of-sail.svg        square-line.svg        <- for the markdown
    points-of-sail-dark.svg   square-line-dark.svg   <- for the PDF's screen theme

The markdown pair carries a `prefers-color-scheme` block so GitHub adapts them
to the reader's theme. Typst does not implement that media query — it renders
the light branch whatever the page colour — so the screen build needs its dark
colours baked in rather than queried. The light files are still the ones any
browser wants, so both are kept.

Run from the repository root:  python3 tools/gen_diagrams.py
"""
import math
from pathlib import Path

OUT = Path("images")

LIGHT = dict(ink="#1f2328", mute="#6a737d", muteS="#9aa4ae", grid="#c2cad3")
DARK = dict(ink="#e6edf3", mute="#9aa4ae", muteS="#6a737d", grid="#3d444d")

# Fixed hues. These read on either ground and, more to the point, they mean
# something: red is port and green is starboard on every boat afloat.
PORT, STBD, AMBER = "#e0555f", "#35b37e", "#f0a030"
POSCOL = {"IRONS": "#e0555f", "CLOSE-HAULED": "#4a9eda",
          "BROAD REACH": "#f0a030", "RUN": "#9b7ede"}

FONTS = ('.lbl { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", '
         'Helvetica, Arial, sans-serif; }\n'
         '    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, '
         'Consolas, monospace; }')


def style(pal, themed):
    """The stylesheet. `themed` adds the media query the markdown copies want."""
    base = "\n".join(f"    .{k} {{ {'stroke' if k.endswith('S') else 'fill'}: {v}; }}"
                     for k, v in pal.items() if k != "grid")
    base += f"\n    .grid {{ stroke: {pal['grid']}; fill: none; }}"
    out = f"  <style>\n{base}\n    {FONTS}\n"
    if themed:
        d = "\n".join(f"      .{k} {{ {'stroke' if k.endswith('S') else 'fill'}: {v}; }}"
                      for k, v in DARK.items() if k != "grid")
        out += ("    @media (prefers-color-scheme: dark) {\n" + d +
                f"\n      .grid {{ stroke: {DARK['grid']}; }}\n    }}\n")
    return out + "  </style>\n"


# --------------------------------------------------------------- points of sail
DIRS = {0: (0, -1), 1: (0.8660254, -0.5), 2: (0.8660254, 0.5),
        3: (0, 1), 4: (-0.8660254, 0.5), 5: (-0.8660254, -0.5)}
NAME = {0: "0°  N", 1: "60°  NE", 2: "120°  SE",
        3: "180°  S", 4: "240°  SW", 5: "300°  NW"}
POS = {0: "IRONS", 1: "CLOSE-HAULED", 2: "BROAD REACH",
       3: "RUN", 4: "BROAD REACH", 5: "CLOSE-HAULED"}
TACK = {0: "(holds tack)", 1: "PORT", 2: "PORT",
        3: "(holds tack)", 4: "STARBOARD", 5: "STARBOARD"}


def boat(cx, cy, ux, uy, fill, outline):
    px, py = -uy, ux
    L, W = 26, 11
    pts = [(cx + ux * L, cy + uy * L),
           (cx - ux * L * 0.62 + px * W, cy - uy * L * 0.62 + py * W),
           (cx - ux * L * 0.34, cy - uy * L * 0.34),
           (cx - ux * L * 0.62 - px * W, cy - uy * L * 0.62 - py * W)]
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'  <polygon points="{d}" fill="{fill}" stroke="{outline}" '
            f'stroke-width="3.5" stroke-linejoin="round"/>\n')


def points_of_sail(pal, themed):
    W, H, cx, cy = 860, 640, 430, 348
    R, RL, Rw = 150, 208, 268
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}" role="img" aria-label="The six hex facings '
         f'with the wind from the north, showing each one\'s point of sail and '
         f'tack">\n', style(pal, themed)]
    s.append(f'  <path d="M {cx} {cy-Rw} A {Rw} {Rw} 0 0 0 {cx} {cy+Rw} Z" '
             f'fill="{STBD}" opacity="0.09"/>\n')
    s.append(f'  <path d="M {cx} {cy-Rw} A {Rw} {Rw} 0 0 1 {cx} {cy+Rw} Z" '
             f'fill="{PORT}" opacity="0.09"/>\n')
    s.append(f'  <line x1="{cx}" y1="{cy-Rw}" x2="{cx}" y2="{cy+Rw}" class="muteS" '
             f'stroke-width="1" stroke-dasharray="3 5" opacity="0.6"/>\n')
    s.append(f'  <text x="{cx-196}" y="{cy+5}" class="lbl" font-size="14" '
             f'font-weight="700" fill="{STBD}" text-anchor="middle" '
             f'letter-spacing="1.4">STARBOARD</text>\n')
    s.append(f'  <text x="{cx+196}" y="{cy+5}" class="lbl" font-size="14" '
             f'font-weight="700" fill="{PORT}" text-anchor="middle" '
             f'letter-spacing="1.4">PORT</text>\n')
    for x in (cx - 46, cx, cx + 46):
        s.append(f'  <line x1="{x}" y1="30" x2="{x}" y2="92" class="muteS" '
                 f'stroke-width="2.5"/>\n'
                 f'  <path d="M {x-6} 86 L {x} 98 L {x+6} 86 Z" class="mute"/>\n')
    s.append(f'  <text x="{cx}" y="20" class="lbl mute" font-size="14" '
             f'font-weight="700" text-anchor="middle" letter-spacing="3">WIND</text>\n')
    for d, (ux, uy) in DIRS.items():
        col = POSCOL[POS[d]]
        s.append(f'  <line x1="{cx+ux*36:.1f}" y1="{cy+uy*36:.1f}" '
                 f'x2="{cx+ux*(R-30):.1f}" y2="{cy+uy*(R-30):.1f}" stroke="{col}" '
                 f'stroke-width="2" opacity="0.45" stroke-dasharray="4 4"/>\n')
        s.append(boat(cx + ux * R, cy + uy * R, ux, uy, col,
                      PORT if d in (1, 2) else STBD if d in (4, 5) else "#9aa4ae"))
        lx, ly = cx + ux * RL, cy + uy * RL
        anchor = "middle" if abs(ux) < 0.1 else ("start" if ux > 0 else "end")
        lx += 0 if abs(ux) < 0.1 else (34 if ux > 0 else -34)
        ly += 6 if uy > 0.1 else (-14 if uy < -0.1 else 0)
        tc = PORT if d in (1, 2) else STBD if d in (4, 5) else "#9aa4ae"
        s.append(f'  <text x="{lx:.0f}" y="{ly:.0f}" class="mono ink" font-size="14" '
                 f'font-weight="700" text-anchor="{anchor}">{NAME[d]}</text>\n')
        s.append(f'  <text x="{lx:.0f}" y="{ly+18:.0f}" class="lbl" font-size="13" '
                 f'fill="{col}" font-weight="700" text-anchor="{anchor}">{POS[d]}</text>\n')
        s.append(f'  <text x="{lx:.0f}" y="{ly+35:.0f}" class="lbl" font-size="12" '
                 f'fill="{tc}" text-anchor="{anchor}">{TACK[d]}</text>\n')
    s.append(f'  <circle cx="{cx}" cy="{cy}" r="5" class="ink"/>\n')
    s.append(f'  <text x="{cx}" y="{H-16}" class="lbl mute" font-size="13" '
             f'text-anchor="middle">Token outline: red = Port tack · '
             f'green = Starboard tack</text>\n')
    s.append("</svg>\n")
    return "".join(s)


# ----------------------------------------------------------------- square line
R = 32.0
CW, HH_ = 1.5 * R, math.sqrt(3) * R
OX, OY = 150.0, 150.0


def cen(i, j):
    return OX + i * CW, OY + j * HH_ + (HH_ / 2 if i % 2 else 0)


def step(i, j, d):
    if d == "NW":
        return (i - 1, j - 1) if i % 2 == 0 else (i - 1, j)
    return (i - 1, j) if i % 2 == 0 else (i - 1, j + 1)


def hexpath(cx, cy):
    p = [(cx + (R - 1.5) * math.cos(math.radians(a)),
          cy + (R - 1.5) * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in p) + " Z"


def square_line(pal, themed):
    W, H = 940, 560
    GREEN, RED = "#2aa06a", "#e0555f"
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}" role="img" aria-label="Why a square starting '
         f'line zigzags on a flat-top hex grid">\n', style(pal, themed)]
    for x in (430, 490, 550):
        s.append(f'  <line x1="{x}" y1="26" x2="{x}" y2="66" class="muteS" '
                 f'stroke-width="2"/>\n'
                 f'  <path d="M {x-5} 61 L {x} 72 L {x+5} 61 Z" class="mute"/>\n')
    s.append('  <text x="490" y="18" class="lbl mute" font-size="13" '
             'font-weight="700" text-anchor="middle" letter-spacing="3">WIND</text>\n')
    for i in range(0, 13):
        for j in range(0, 6):
            cx, cy = cen(i, j)
            s.append(f'  <path d="{hexpath(cx, cy)}" class="grid" stroke-width="1.1"/>\n')
    i, j = 10, 4
    naive = [cen(i, j)]
    for _ in range(6):
        i, j = step(i, j, "NW"); naive.append(cen(i, j))
    nend = (i, j)
    s.append('  <polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in naive) +
             f'" fill="none" stroke="{RED}" stroke-width="3.5" stroke-dasharray="8 6" '
             f'stroke-linecap="round" stroke-linejoin="round"/>\n')
    i, j = 10, 4
    sq = [cen(i, j)]
    for k in range(6):
        i, j = step(i, j, "NW" if k % 2 == 0 else "SW"); sq.append(cen(i, j))
    pin = (i, j)
    s.append('  <polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in sq) +
             f'" fill="none" stroke="{GREEN}" stroke-width="4.5" '
             f'stroke-linecap="round" stroke-linejoin="round"/>\n')
    for px, py in sq[1:-1]:
        s.append(f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{GREEN}"/>\n')
    cbx, cby = cen(10, 4)
    pnx, pny = cen(*pin)
    s.append(f'  <line x1="{pnx-70:.0f}" y1="{cby:.0f}" x2="{cbx+70:.0f}" y2="{cby:.0f}" '
             f'stroke="{GREEN}" stroke-width="1.2" stroke-dasharray="2 6" opacity="0.85"/>\n')
    for mx, my, lab in ((cbx, cby, "Committee Boat"), (pnx, pny, "Pin")):
        s.append(f'  <circle cx="{mx:.1f}" cy="{my:.1f}" r="13" fill="{AMBER}"/>\n')
        s.append(f'  <text x="{mx:.0f}" y="{my+52:.0f}" class="lbl ink" font-size="14" '
                 f'font-weight="700" text-anchor="middle">{lab}</text>\n')
    nx, ny = cen(*nend)
    s.append(f'  <circle cx="{nx:.1f}" cy="{ny:.1f}" r="6" fill="{RED}"/>\n')
    s.append(f'  <line x1="{nx:.0f}" y1="{ny:.0f}" x2="{nx:.0f}" y2="{cby:.0f}" '
             f'stroke="{RED}" stroke-width="1.2" stroke-dasharray="3 4" opacity="0.8"/>\n')
    s.append(f'  <text x="{nx-26:.0f}" y="{(ny+cby)/2-6:.0f}" class="lbl" font-size="13" '
             f'fill="{RED}" font-weight="700" text-anchor="end">3 hexes</text>\n')
    s.append(f'  <text x="{nx-26:.0f}" y="{(ny+cby)/2+11:.0f}" class="lbl" font-size="13" '
             f'fill="{RED}" text-anchor="end">of free windward</text>\n')
    s.append(f'  <text x="{nx+18:.0f}" y="{ny-26:.0f}" class="lbl" font-size="14" '
             f'fill="{RED}" font-weight="700">One hex axis (300° six times)</text>\n')
    s.append(f'  <text x="{nx+18:.0f}" y="{ny-8:.0f}" class="lbl" font-size="13" '
             f'fill="{RED}">climbs ½ a hex every column — not square</text>\n')
    s.append(f'  <text x="{OX-24:.0f}" y="{H-58}" class="lbl" font-size="14" '
             f'fill="{GREEN}" font-weight="700">Alternating 300° / 240°</text>\n')
    s.append(f'  <text x="{OX-24:.0f}" y="{H-38}" class="lbl" font-size="13" '
             f'fill="{GREEN}">both ends level — a square line</text>\n')
    s.append("</svg>\n")
    return "".join(s)


def main():
    OUT.mkdir(exist_ok=True)
    for name, fn in (("points-of-sail", points_of_sail), ("square-line", square_line)):
        (OUT / f"{name}.svg").write_text(fn(LIGHT, themed=True))
        (OUT / f"{name}-dark.svg").write_text(fn(DARK, themed=False))
        print(f"  wrote {name}.svg and {name}-dark.svg")


if __name__ == "__main__":
    main()
