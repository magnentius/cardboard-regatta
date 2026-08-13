// Cardboard Regatta — shared palette, faces and edition stamp.
//
// The colours are US Sailing's: #c32a30 red and #0f1d41 navy, taken from
// ussailing.org. Red, white and blue is not decoration here — it is the sport's
// own signal-flag vocabulary, and two of the three already carry meaning in the
// game. Port is red and starboard is green on every boat afloat, so the accent
// that marks a tactical note is the same red that outlines a port-tack token.

// --- Palette ----------------------------------------------------------------

#let palette-print = (
  paper:     rgb("#ffffff"),
  surface:   rgb("#eef3f9"),   // the faintest wash of the navy
  surface2:  rgb("#dee8f3"),
  border:    rgb("#b6c8dc"),
  ink:       rgb("#0f1d41"),   // US Sailing navy
  muted:     rgb("#48587a"),
  dim:       rgb("#7a89a4"),
  accent:    rgb("#c32a30"),   // US Sailing red
  accent2:   rgb("#9e2329"),   // the deeper red, for rules and hairlines
  port:      rgb("#c32a30"),   // port tack — the same red, and not by accident
  starboard: rgb("#1f8355"),   // starboard tack, dark enough to hold on white
  wind:      rgb("#5b7fa6"),
)

// Dark theme. Navy is the ground rather than the ink, which is the right way
// round for a screen: the book reads as a chart lit at the nav station.
#let palette-screen = (
  paper:     rgb("#0a1224"),
  surface:   rgb("#132244"),
  surface2:  rgb("#1b2d55"),
  border:    rgb("#2c4270"),
  ink:       rgb("#e7edf6"),
  muted:     rgb("#9dafc9"),
  dim:       rgb("#6d7f9e"),
  accent:    rgb("#ef5a60"),   // the red lifted until it holds on navy
  accent2:   rgb("#ff8b8f"),
  port:      rgb("#ef5a60"),
  starboard: rgb("#4fc38a"),
  wind:      rgb("#8fb0d4"),
)

// --- Faces ------------------------------------------------------------------
//
// All three are freely licensed and vendored in typst/fonts, so CI and a laptop
// build the same document. See typst/fonts/README.md for why these three.

#let serif = "XCharter"
#let sans  = "TeX Gyre Heros"
#let mono  = "DejaVu Sans Mono"

// --- Edition ----------------------------------------------------------------

/// What copy of the rules this is, printed in the footer of every page.
///
/// A player holds paper, not a git tag. Releases pass the date in; anything
/// else is labelled a draft, so a local build is never mistaken for published.
#let edition = {
  let e = sys.inputs.at("edition", default: none)
  if e != none { "Edition " + e } else {
    "Draft " + datetime.today().display("[year]-[month]-[day]")
  }
}
