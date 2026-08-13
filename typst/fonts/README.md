# Vendored fonts

The rulebook is built against these faces and no others. Both the local build
and CI pass `--font-path typst/fonts --ignore-system-fonts`, so nothing is read
from the machine's own font set and every build produces the same document.

| Family | Files | Source | Licence |
| :--- | :--- | :--- | :--- |
| **XCharter** | `XCharter-{Roman,Bold,Italic,BoldItalic}.otf` | [CTAN: xcharter](https://ctan.org/pkg/xcharter) | Bitstream Charter free licence + LPPL 1.3 — see `XCharter-README.txt` |
| **TeX Gyre Heros** | `texgyreheros-{regular,bold,italic,bolditalic}.otf` | [CTAN: tex-gyre](https://ctan.org/pkg/tex-gyre) | GUST Font Licence — see `GUST-FONT-LICENSE.txt` |
| **DejaVu Sans Mono** | — | ships with Typst | Bitstream Vera licence |

## Why these

The book is 36 pages of justified prose broken up by 32 tables, and it needs a
serif that holds a tight measure without going papery, a sans with enough
authority for headings, and a mono for the running heads, table headers and the
ASCII diagrams whose alignment *is* the content.

- **XCharter** is Matthew Carter's Charter, extended. A sturdy old-style with a
  large x-height, which is what keeps the 9pt text inside callouts readable —
  and roughly a third of the book is set inside a callout.
- **TeX Gyre Heros** is a genuine Helvetica clone, so the headings keep the
  proportions they were drawn with. It also sets the plain, official tone a
  sailing instruction should have. DejaVu Sans, the obvious apt-installable
  alternative, is visibly wider and blockier.
- **DejaVu Sans Mono** has the widest glyph coverage of the three, which matters:
  the book uses `°`, `½`, `➔`, `−` and `✓` throughout, and the diagrams depend on
  every character advancing the same width.

## Glyph coverage

Emoji are **not** available in any vendored face and set as tofu. The converter
strips the decorative ones and maps `✅` to `✓`, which XCharter has. If you add a
symbol to the rules, check it renders before relying on it:

```bash
typst compile --root . --font-path typst/fonts --ignore-system-fonts \
  --format png some-probe.typ probe.png
```

## Adding or updating a face

Drop the `.otf` in this directory, add its licence file, and record it in the
table above. Then rebuild both themes and read a few pages: substitution reflows
the document, and the callouts are tight enough that a wider face pushes tables
onto the following page.

```bash
typst compile --root . --font-path typst/fonts --ignore-system-fonts \
  typst/rules.typ rules.pdf
```
