# ⛵ Cardboard Regatta

**The Tactical Board Game of Competitive Sailboat Racing**

> *Harness the wind, master right-of-way tactics, and outmaneuver your rivals to take the bullet!*

---


## 🏆 Overview

**Cardboard Regatta** brings the high-stakes strategy and adrenaline of real competitive sailboat racing to your tabletop in a fast-paced, accessible hex-grid game. 

Whether you're a seasoned sailor or a tabletop strategist, **Cardboard Regatta** delivers deep tactical gameplay through action-programming, dynamic wind shifts, and authentic right-of-way duels. 

---

## ✨ Game Highlights

- ⛵ **Authentic Sailing Physics, Simplified**: Command your boat across hex points of sail (*Close-Hauled*, *Broad Reach*, *Run*). Push your polar speed limits, trim your sails, and avoid getting pinched in *Irons*!
- 🧠 **Action-Programming & Tacking Duels**: Secretly plan 4 maneuver actions each round (`Head Up`, `Bear Off`, `Tack`, `Gybe`, `Trim`, `Luff`). React round-robin in upwind initiative order to execute brilliant tactical blocks.
- ⏱️ **Thrilling Pre-Start Countdown**: Maneuver for prime starting line position during a 3-turn pre-start sequence. Hit the starting line at full speed right as the gun fires—just don't end up **OCS** (On Course Side)!
- 🌬️ **Dynamic Weather System**: Adapt to shifting wind zones across the course. Catch a **Puff** for a burst of speed, or capitalize on **Wind Shifts** to gain a massive tactical advantage upwind.
- ⚖️ **Steal the Wind & Enforce the Rules**: Lock opponents in your **Wind Shadow** to slow them down. Leverage official right-of-way rules (*Starboard over Port*, *Leeward over Windward*) to force rivals into penalty turns—or push them into disqualification!

---

## 🎲 Game Specifications

| Specification | Details |
|---|---|
| **Players** | 2 – 8 Players |
| **Play Time** | 15 – 45 Minutes (by course) |
| **Complexity** | Easy to Learn, High Tactical Depth |
| **Mechanisms** | Action Programming, Grid Movement, Initiative, Secret Selection |

---

## 📖 Rulebook

Ready to set sail? **[Download the rulebook PDF](../../releases)**. The last two pages are
a **Quick Reference** card — print them double-sided and keep them beside the board.

The rulebook is written in [Typst](https://typst.app). Its source is
**[`typst/rules.typ`](typst/rules.typ)**, with the reference card in
[`typst/lib/quick-reference.typ`](typst/lib/quick-reference.typ). Together they are the
single authority on the rules: there is no markdown copy to fall out of step with them.

### The PDF

Published on the [Releases page](../../releases) in two versions, built from the same source:

| | For |
| :--- | :--- |
| `cardboard-regatta-rulebook-<edition>.pdf` | **Printing** — navy on white |
| `cardboard-regatta-rulebook-screen-<edition>.pdf` | **Reading on a screen** — light on navy |

Every page carries its edition date in the footer, so you can tell at a glance whether the
copy in your hands matches the one on the table.

To build it yourself you need [Typst](https://github.com/typst/typst) 0.15 or later. Fonts
are vendored in `typst/fonts`, and the build ignores system fonts so it produces the same
document everywhere:

```bash
typst compile --root . --font-path typst/fonts --ignore-system-fonts \
  typst/rules.typ rules.pdf

# ...and the screen version
typst compile --root . --font-path typst/fonts --ignore-system-fonts \
  --input theme=screen typst/rules.typ rules-screen.pdf
```

The geometry diagrams in `images/` are generated — edit `tools/gen_diagrams.py` and
re-run it rather than editing the SVGs by hand, which CI checks.

---

## 📄 License & Copyright

© 2026 John Karakashian.

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/). 
You are free to share and adapt the material for non-commercial purposes, provided you give appropriate credit and distribute your contributions under the same license.
