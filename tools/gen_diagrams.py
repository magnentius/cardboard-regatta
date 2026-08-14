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



# ------------------------------------------------------------------------ cover
#
# Two boats crossing on opposite tacks — which is Rule 10, the oldest rule in the
# sport and the one this game leans on hardest: 39% of every Protest issued.
#
# The geometry is the point of drawing this by hand rather than generating it.
# With the wind from the top of the frame:
#
#   left boat   bow up-and-right (heading NE)  -> wind crosses her PORT side,
#                                                 so she is on PORT tack and her
#                                                 sails are set to STARBOARD
#   right boat  bow up-and-left  (heading NW)  -> wind crosses her STARBOARD side,
#                                                 so she is on STARBOARD tack and
#                                                 her sails are set to PORT
#
# Both sails therefore lean inward and nearly touch at the crossing. That mirror
# is what "opposite tacks" looks like from above, and it is exactly the symmetry
# that was inverted in the rules until this session.

# Sail opacity is per-palette, not fixed. Over white, dropping opacity lightens
# a sail and separates the jib from the main; over navy it darkens it, and the
# red boat turns to mud. The dark theme therefore carries both sails much
# closer to solid.
COVER_LIGHT = dict(boatA="#c32a30", boatB="#0f1d41", grid="#0f1d41",
                   wind="#0f1d41", wake="#b6c8dc", main_op=0.88, jib_op=0.60)
COVER_DARK = dict(boatA="#ef5a60", boatB="#e7edf6", grid="#8fb0d4",
                  wind="#8fb0d4", wake="#2c4270", main_op=1.0, jib_op=0.74)


# Side elevation, not plan view. Overhead was tried first — it matches the
# board, and it lets "opposite tacks" be literally true rather than implied —
# but it cannot work: close-hauled boats sheet their sails in almost to the
# centreline, so from directly above the sail sits on top of the hull and
# disappears. Swing the sails out far enough to see and you have drawn two
# boats running downwind, on the same tack, looking like moths.
#
# So the boats are drawn side-on and mirrored, which is the conventional
# shorthand for opposite tacks and is unmistakably a sailboat at any size.

def hull(S):
    """Topsides from the side: a sheer line rising to the bow, a rounded forefoot."""
    return (f"M {-0.92*S:.1f},{-0.02*S:.1f} "
            f"L {1.00*S:.1f},{-0.17*S:.1f} "
            f"L {0.80*S:.1f},{0.20*S:.1f} "
            f"Q {0.04*S:.1f},{0.35*S:.1f} {-0.70*S:.1f},{0.17*S:.1f} Z")


def mainsail(S):
    """Luff up the mast, foot along the boom, leech curved between them."""
    return (f"M {0.02*S:.1f},{-1.70*S:.1f} "
            f"Q {-0.40*S:.1f},{-0.96*S:.1f} {-0.62*S:.1f},{-0.24*S:.1f} "
            f"L {0.08*S:.1f},{-0.19*S:.1f} Z")


def jib(S):
    """Luff down the forestay to the bow, a shallow leech back to the mast."""
    return (f"M {0.05*S:.1f},{-1.50*S:.1f} "
            f"L {0.95*S:.1f},{-0.15*S:.1f} "
            f"Q {0.36*S:.1f},{-0.44*S:.1f} {0.14*S:.1f},{-0.21*S:.1f} Z")


def cover_boat(cx, cy, S, face, heel, colour, wake, main_op, jib_op):
    """A boat under sail. `face` is +1 for bow-right, -1 for bow-left (drawn by
    mirroring, which is what makes the pair read as opposite tacks). `heel`
    leans her away from her wind."""
    g = [f'  <g transform="translate({cx},{cy}) scale({face},1) rotate({heel})">\n']
    g.append(f'    <path d="{jib(S)}" fill="{colour}" opacity="{jib_op}"/>\n')
    g.append(f'    <path d="{mainsail(S)}" fill="{colour}" opacity="{main_op}"/>\n')
    g.append(f'    <line x1="{0.10*S:.1f}" y1="{-0.04*S:.1f}" '
             f'x2="{0.02*S:.1f}" y2="{-1.72*S:.1f}" stroke="{colour}" '
             f'stroke-width="{0.030*S:.1f}" stroke-linecap="round"/>\n')
    g.append(f'    <line x1="{0.08*S:.1f}" y1="{-0.19*S:.1f}" '
             f'x2="{-0.64*S:.1f}" y2="{-0.25*S:.1f}" stroke="{colour}" '
             f'stroke-width="{0.026*S:.1f}" stroke-linecap="round"/>\n')
    g.append(f'    <path d="{hull(S)}" fill="{colour}"/>\n')
    g.append("  </g>\n")
    # Bow wave, drawn outside the heel so it stays level with the water.
    g.append(f'  <path d="M {cx + face*0.98*S:.0f},{cy + 0.20*S:.0f} '
             f'q {face*0.22*S:.0f},{0.10*S:.0f} {face*0.52*S:.0f},{0.04*S:.0f}" '
             f'fill="none" stroke="{wake}" stroke-width="{0.05*S:.1f}" '
             f'stroke-linecap="round" opacity="0.55"/>\n')
    g.append(f'  <path d="M {cx - face*0.90*S:.0f},{cy + 0.17*S:.0f} '
             f'q {-face*0.24*S:.0f},{0.06*S:.0f} {-face*0.50*S:.0f},{0.01*S:.0f}" '
             f'fill="none" stroke="{wake}" stroke-width="{0.04*S:.1f}" '
             f'stroke-linecap="round" opacity="0.35"/>\n')
    return "".join(g)


def cover(pal, themed):
    W = H = 1000
    cx, cy = W / 2, H / 2
    Rh = 46.0
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}" role="img" aria-label="Two sailboats crossing '
         f'on opposite tacks over a hex grid">\n']
    if themed:
        s.append("  <style>\n    .grid { stroke: %s; }\n    .wind { stroke: %s; }\n"
                 "    @media (prefers-color-scheme: dark) {\n"
                 "      .grid { stroke: %s; }\n      .wind { stroke: %s; }\n    }\n"
                 "  </style>\n" % (COVER_LIGHT["grid"], COVER_LIGHT["wind"],
                                   COVER_DARK["grid"], COVER_DARK["wind"]))
    else:
        s.append("  <style>\n    .grid { stroke: %s; }\n    .wind { stroke: %s; }\n"
                 "  </style>\n" % (pal["grid"], pal["wind"]))

    # Flat-top hexes in vertical columns, each faded by its distance from the
    # centre. Per-hex opacity rather than a mask: masks are the first thing an
    # SVG renderer drops, and this has to survive Typst as well as a browser.
    colw, rowh = 1.5 * Rh, math.sqrt(3) * Rh
    for i in range(-1, int(W / colw) + 2):
        for j in range(-1, int(H / rowh) + 2):
            hx = i * colw
            hy = j * rowh + (rowh / 2 if i % 2 else 0)
            d = math.dist((hx, hy), (cx, cy)) / (W * 0.62)
            op = max(0.0, 0.42 * (1 - d ** 1.6))
            if op < 0.02:
                continue
            pts = " ".join(f"{hx + Rh*math.cos(math.radians(a)):.1f},"
                           f"{hy + Rh*math.sin(math.radians(a)):.1f}"
                           for a in range(0, 360, 60))
            s.append(f'  <polygon points="{pts}" fill="none" class="grid" '
                     f'stroke-width="1.2" opacity="{op:.3f}"/>\n')

    for k, x in enumerate((196, 300, 700, 804)):
        top, bot = 60, 150 + (18 if k in (1, 2) else 0)
        s.append(f'  <line x1="{x}" y1="{top}" x2="{x}" y2="{bot}" class="wind" '
                 f'stroke-width="2.4" stroke-linecap="round" opacity="0.5"/>\n')
        s.append(f'  <path d="M {x-7},{bot-9} L {x},{bot+3} L {x+7},{bot-9}" '
                 f'fill="none" class="wind" stroke-width="2.4" stroke-linecap="round" '
                 f'stroke-linejoin="round" opacity="0.5"/>\n')

    S = 178
    # Mirrored, converging: the crossing that Rule 10 exists to settle. A light
    # heel only — enough to say "under press of sail", not enough to read as a
    # claim about which way the wind is blowing in a side elevation.
    s.append(cover_boat(288, 648, S, +1, -4, pal["boatA"], pal["wake"],
                        pal["main_op"], pal["jib_op"]))
    s.append(cover_boat(712, 648, S, -1, -4, pal["boatB"], pal["wake"],
                        pal["main_op"], pal["jib_op"]))
    s.append("</svg>\n")
    return "".join(s)


def main():
    OUT.mkdir(exist_ok=True)
    for name, fn in (("points-of-sail", points_of_sail), ("square-line", square_line)):
        (OUT / f"{name}.svg").write_text(fn(LIGHT, themed=True))
        (OUT / f"{name}-dark.svg").write_text(fn(DARK, themed=False))
        print(f"  wrote {name}.svg and {name}-dark.svg")
    (OUT / "cover.svg").write_text(cover(COVER_LIGHT, themed=True))
    (OUT / "cover-dark.svg").write_text(cover(COVER_DARK, themed=False))
    print("  wrote cover.svg and cover-dark.svg")


if __name__ == "__main__":
    main()
