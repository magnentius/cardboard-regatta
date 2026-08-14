// Cardboard Regatta — rulebook template.
//
// The book uses four kinds of set-apart block, and they mean different things.
// Markdown collapsed them into GitHub's four alert flavours, which look alike
// enough that a reader learns nothing from the shape. Here they are drawn
// apart, because the difference is load-bearing:
//
//   rule      binding. You must do this.            navy, solid rule
//   tactic    advice. You may ignore it and lose.   red, the accent
//   ruling    a clarification or an edge case.      quiet, hairline
//   warning   a trap that will cost you a Protest.  red, filled
//
// Cross-references are Typst labels, so a link to a section or a glossary term
// that no longer exists fails the build instead of quietly misdirecting a
// player mid-race. That is the main reason the rules stopped being markdown.

#import "regatta.typ": palette-print, palette-screen, sans, serif, mono, edition

#let pal = state("rules-pal", palette-print)
#let theme-name = state("rules-theme", "print")

// --- Shell ------------------------------------------------------------------

#let rulebook(theme: "print", title: "Cardboard Regatta", body) = {
  let p = if theme == "screen" { palette-screen } else { palette-print }
  pal.update(p)
  theme-name.update(theme)

  set document(title: title, author: "John Karakashian")
  set page(
    paper: "us-letter",
    margin: (x: 2.2cm, top: 2.1cm, bottom: 1.9cm),
    fill: p.paper,
    header: context {
      if counter(page).get().first() <= 2 { return }
      // Prefer a chapter opening on THIS page; otherwise the last one before
      // it. Querying only what precedes would name the previous chapter on
      // every chapter-opening page.
      let all = query(heading.where(level: 1))
      let on-page = all.filter(h => h.location().page() == here().page())
      let before = all.filter(h => h.location().page() < here().page())
      let name = if on-page.len() > 0 { on-page.first().body }
                 else if before.len() > 0 { before.last().body }
                 else { [] }
      set text(font: mono, size: 7pt, fill: p.dim)
      grid(columns: (1fr, auto), align: (left, right), upper(title), name)
      v(-6pt)
      line(length: 100%, stroke: 0.4pt + p.border)
    },
    footer: context {
      if counter(page).get().first() <= 1 { return }
      set text(font: mono, size: 7pt, fill: p.muted)
      grid(columns: (1fr, auto, 1fr), align: (left, center, right),
        text(fill: p.dim)[#edition], counter(page).display(), [])
    },
  )

  set text(font: serif, size: 10pt, fill: p.ink, lang: "en")
  set par(justify: true, leading: 0.62em, first-line-indent: 0pt, spacing: 0.85em)

  // A chapter opens a page, under a navy bar with a red keel line beneath it —
  // the only place the two brand colours meet directly.
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    block(width: 100%, above: 0pt, below: 14pt, {
      set text(font: sans, size: 21pt, weight: "bold", fill: p.ink)
      block(it.body)
      v(4pt)
      // Stacked, not two blocks: paragraph spacing between them would open a
      // gap and the red would read as a stray rule rather than a keel line.
      stack(
        spacing: 1.6pt,
        line(length: 100%, stroke: 1.4pt + p.ink),
        line(length: 22%, stroke: 1.4pt + p.accent),
      )
    })
  }
  show heading.where(level: 2): it => block(above: 18pt, below: 8pt, {
    set text(font: sans, size: 13.5pt, weight: "bold", fill: p.ink)
    it.body
  })
  show heading.where(level: 3): it => block(above: 14pt, below: 6pt, {
    set text(font: sans, size: 11pt, weight: "bold", fill: p.accent)
    it.body
  })
  show heading.where(level: 4): it => block(above: 11pt, below: 5pt, {
    set text(font: sans, size: 9.5pt, weight: "bold", fill: p.muted)
    upper(it.body)
  })

  // The book carries 437 cross-references — most paragraphs hold three or four,
  // because every game term links to the glossary. Setting them all in the
  // accent turns solid pages speckled and makes the red mean nothing. They keep
  // the body colour and are marked instead by a fine underline, which says
  // "defined elsewhere" quietly and survives being printed in black and white.
  show link: it => {
    if type(it.dest) == label {
      underline(offset: 1.6pt, stroke: 0.4pt + p.accent.transparentize(45%), it)
    } else {
      text(fill: p.accent, it)
    }
  }

  // The book has 60-odd tables and they are consulted, not admired.
  set table(
    stroke: (x, y) => (
      top: if y == 0 { 0.7pt + p.border } else if y == 1 { 0.5pt + p.border }
           else { 0.3pt + p.border.transparentize(55%) },
      bottom: 0.7pt + p.border,
    ),
    inset: (x: 6pt, y: 4.5pt),
    fill: (x, y) => if y == 0 { p.surface } else { none },
  )
  show table.cell.where(y: 0): set text(
    font: mono, size: 7.5pt, fill: p.muted, weight: "regular")

  set list(marker: ([•], [–], [·]), indent: 6pt, spacing: 0.65em)
  set enum(indent: 6pt, spacing: 0.65em)

  body
}

// --- Set-apart blocks -------------------------------------------------------

#let _callout(label-text, colour, fill-tint, body) = context {
  let p = pal.get()
  let c = colour(p)
  block(
    width: 100%, above: 10pt, below: 10pt,
    fill: if fill-tint == none { none } else { c.transparentize(fill-tint) },
    stroke: (left: 2pt + c),
    inset: (x: 9pt, y: 7pt),
    {
      if label-text != none {
        text(font: mono, size: 6.8pt, fill: c, tracking: 0.12em)[#label-text]
        v(3pt)
      }
      set text(size: 9pt, fill: p.ink)
      body
    },
  )
}

/// Binding. A player who skips this is playing a different game.
#let rule-box(body) = _callout("RULE", p => p.ink, 96%, body)

/// Advice. Ignoring it is legal, and slow.
#let tactic(body) = _callout("TACTICS", p => p.accent, 95%, body)

/// A clarification, an edge case, or the reasoning behind a rule.
#let ruling(body) = _callout("RULING", p => p.dim, none, body)

/// An unlabelled aside — the italic lead-in that opens a chapter. Labelling
/// these "RULING" was worse than leaving them bare: it promised a ruling and
/// delivered a sentence of orientation.
#let aside(body) = _callout(none, p => p.border, none, body)

/// A trap that will cost you a Protest.
#let warning(body) = _callout("WARNING", p => p.accent, 88%, body)

/// A figure whose artwork follows the theme.
///
/// The SVGs carry a `prefers-color-scheme` block so GitHub adapts them, but
/// Typst does not implement that query — it would render the light branch on a
/// navy page and the labels would vanish. So the screen build loads a `-dark`
/// sibling with its colours baked in.
#let fig(path, caption) = context {
  let src = if theme-name.get() == "screen" {
    path.replace(".svg", "-dark.svg")
  } else { path }
  figure(image(src, width: 92%), caption: caption)
}

/// Attach the label a cross-reference resolves to. Used for the glossary terms,
/// which are table cells rather than headings and so carry no label of their own.
#let anchor(name) = [#metadata(name)#label(name)]

/// A worked example: played out card by card.
#let example(body) = context {
  let p = pal.get()
  block(width: 100%, above: 10pt, below: 10pt,
    fill: p.surface, stroke: 0.5pt + p.border, radius: 3pt,
    inset: (x: 9pt, y: 7pt), body)
}

/// The chapter epigraphs.
#let epigraph(quote, source) = context {
  let p = pal.get()
  block(width: 100%, above: 2pt, below: 14pt, inset: (left: 10pt),
    stroke: (left: 1.5pt + p.accent.transparentize(50%)), {
      set text(size: 9.5pt, style: "italic", fill: p.muted)
      quote
      linebreak()
      text(font: mono, size: 7.5pt, style: "normal")[— #source]
    })
}

/// Preformatted diagrams — the wind shadow cone, the overlap fan, the beat.
/// Monospace and unjustified, because the alignment is the content.
#let diagram(body) = context {
  let p = pal.get()
  block(width: 100%, above: 10pt, below: 10pt,
    fill: p.surface, stroke: 0.5pt + p.border, radius: 3pt,
    inset: (x: 10pt, y: 9pt),
    align(center, block(align(left, {
      set par(justify: false, leading: 0.5em)
      set text(font: mono, size: 8pt, fill: p.ink)
      body
    }))))
}

/// The four-phase round, drawn rather than described. Replaces the mermaid
/// graph in the markdown, which no PDF toolchain can render.
#let phase-flow(..phases) = context {
  let p = pal.get()
  let items = phases.pos()
  block(width: 100%, above: 12pt, below: 12pt, align(center, {
    set text(font: sans, size: 8pt, fill: p.ink)
    grid(
      columns: items.map(_ => auto).intersperse(auto),
      align: horizon + center,
      column-gutter: 5pt,
      ..items
        .map(ph => box(
          fill: p.surface, stroke: 0.6pt + p.border, radius: 2pt,
          inset: (x: 7pt, y: 6pt), ph))
        .intersperse(text(fill: p.accent, size: 11pt)[#sym.arrow.r]),
    )
  }))
}

// --- Cover ------------------------------------------------------------------

#let cover(title, subtitle, art, tagline: none, designer: none, license: none) = context {
  let p = pal.get()
  set page(header: none, footer: none)
  align(center + horizon, block(width: 100%, {
    // Signal-flag bar: the three colours, in the order they appear on the water.
    grid(columns: (1fr, 1fr, 1fr), rows: 4pt, column-gutter: 0pt,
      rect(width: 100%, height: 4pt, fill: p.accent, stroke: none),
      rect(width: 100%, height: 4pt, fill: p.paper, stroke: 0.4pt + p.border),
      rect(width: 100%, height: 4pt, fill: p.ink, stroke: none))
    v(18pt)
    text(font: mono, size: 9pt, fill: p.accent, tracking: 0.3em)[CARDBOARD REGATTA]
    v(10pt)
    text(font: sans, size: 38pt, weight: "bold", fill: p.ink)[#title]
    v(6pt)
    text(size: 12pt, style: "italic", fill: p.muted)[#subtitle]
    if designer != none {
      v(10pt)
      text(font: sans, size: 9.5pt, fill: p.dim, tracking: 0.05em)[
        Designed by #text(weight: "bold", fill: p.ink)[#designer]]
    }
    v(22pt)
    // The cover art follows the theme, same as any other figure: Typst does
    // not implement prefers-color-scheme, so the screen build loads a sibling
    // with its colours baked in.
    if art != none {
      let src = if theme-name.get() == "screen" {
        art.replace(".svg", "-dark.svg")
      } else { art }
      image(src, width: 62%)
    }
    v(14pt)
    text(font: mono, size: 8pt, fill: p.muted, tracking: 0.1em)[#upper(edition)]
    if tagline != none {
      v(16pt)
      block(width: 72%, align(center,
        text(size: 9pt, style: "italic", fill: p.dim, tagline)))
    }
    // The dedication belongs on the cover, not buried in a colophon: whoever
    // holds a photocopy of this book should be able to see that copying it was
    // always allowed.
    if license != none {
      v(18pt)
      text(font: mono, size: 7pt, fill: p.muted, tracking: 0.14em)[#upper(license)]
    }
  }))
  pagebreak()
}
