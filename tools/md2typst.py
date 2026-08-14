#!/usr/bin/env python3
"""One-shot converter: rules.md -> typst/rules.typ. HISTORICAL.

This is the record of how the rulebook was converted, not a pipeline. It cannot
be re-run: rules.md was deleted once the conversion was verified, and
typst/rules.typ is now the single source of truth for the rules.

It is kept because the conversion made judgement calls worth being able to
audit — which markdown blockquote became which kind of callout, how the
LaTeX maths was translated, and how anchors were mapped to Typst labels.

The interesting part was the cross-references. rules.md carried 437 internal
links across 76 anchors, the glossary alone being linked from nearly every
chapter. In markdown a stale one silently scrolled nowhere; as Typst labels a
stale one fails the build. That is why the rules stopped being markdown.
"""
import re
import sys
import collections
from pathlib import Path

SRC = Path("rules.md")
DST = Path("typst/rules.typ")
REPO = "https://github.com/magnentius/cardboard-regatta/blob/main"

ESC_STAR = "\x03"

# The vendored faces carry no emoji, so decorative ones would set as tofu.
# U+2705 is the one emoji doing real work — it marks the satisfied conditions in
# the mark-rounding table — so it becomes a plain check mark, which XCharter has.
EMOJI = "⛵📐🏁⚡🏆😬🌬🚩💨⚠"
CHAR_MAP = {"✅": "✓"}

# GitHub alert flavour -> the Typst block it becomes. The book uses these four
# with real consistency: IMPORTANT is always binding, TIP is always advice.
CALLOUT = {
    "IMPORTANT": "rule-box",
    "TIP": "tactic",
    "NOTE": "ruling",
    "WARNING": "warning",
}


def slug(s: str) -> str:
    """GitHub's heading anchor, so link targets in the markdown still match."""
    s = re.sub(r"`|\*\*|\*|\[|\]\(#[^)]*\)", "", s).lower().strip()
    return re.sub(r"[^\w\s-]", "", s).replace(" ", "-")


def tlabel(anchor: str) -> str:
    """A markdown anchor -> a Typst label name.

    Prefixed because several anchors begin with a hyphen once their emoji is
    stripped, and a label may not start with one.
    """
    return "x-" + re.sub(r"[^a-z0-9]+", "-", anchor.lower()).strip("-")


def emphasis(s: str) -> str:
    """Markdown emphasis -> Typst, via a state machine.

    A regex cannot do this: bold wrapping italic closes as `***`, and any
    non-greedy pattern splits that run the wrong way.
    """
    out, i, bold, ital = [], 0, False, False
    while i < len(s):
        if s[i] == "*":
            j = i
            while j < len(s) and s[j] == "*":
                j += 1
            run = j - i
            if run >= 3:
                if not bold and not ital:
                    out.append("*_"); bold = ital = True
                else:
                    out.append("_*"); bold = ital = False
            elif run == 2:
                out.append("*"); bold = not bold
            else:
                out.append("_"); ital = not ital
            i = j
        else:
            out.append(s[i]); i += 1
    return "".join(out)


class Converter:
    def __init__(self, text: str):
        self.lines = text.split("\n")
        self.anchors = set()
        self.missing = collections.Counter()
        self._collect_anchors()

    def _collect_anchors(self):
        for line in self.lines:
            m = re.match(r"^(#{1,6}) (.+)$", line)
            if m:
                self.anchors.add(slug(m.group(2).strip()))
            for a in re.findall(r'<a id="([^"]+)"', line):
                self.anchors.add(a)

    # --- inline ------------------------------------------------------------
    def inline(self, s: str) -> str:
        saved = []

        def stash(code: str) -> str:
            saved.append(code)
            return f"\x00{len(saved) - 1}\x00"

        for a, b in CHAR_MAP.items():
            s = s.replace(a, b)
        s = s.replace(r"\*", ESC_STAR)

        # Anchors defined inline in the glossary table.
        s = re.sub(r'<a id="([^"]+)"></a>',
                   lambda m: stash(f'#anchor("{tlabel(m.group(1))}")'), s)

        # Math spans, stashed whole so the escaping pass below cannot touch
        # them. Typst delimits inline maths with $...$ as well, but the bodies
        # are LaTeX in a few places and need translating.
        s = re.sub(r"\$\$(.+?)\$\$",
                   lambda m: stash("$ " + self.math(m.group(1)) + " $"), s)
        s = re.sub(r"\$([^$]+)\$",
                   lambda m: stash("$" + self.math(m.group(1)) + "$"), s)

        # Images, then links. Internal links become label references the Typst
        # compiler must resolve; a stale one is a build failure, by design.
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                   lambda m: stash(
                       f'#fig("/{m.group(2)}")[{self.inline(m.group(1))}]'), s)
        s = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)",
                   lambda m: stash(self.link(m.group(1), m.group(2))), s)

        for ch in ("\\", "#", "@", "$", "<", ">", "_"):
            s = s.replace(ch, "\\" + ch)

        s = emphasis(s)
        s = s.replace(ESC_STAR, "\\*")
        s = re.sub(r"[" + EMOJI + r"]\uFE0F?\s*", "", s)
        return re.sub(r"\x00(\d+)\x00", lambda m: saved[int(m.group(1))], s)

    def link(self, text: str, target: str) -> str:
        body = emphasis(re.sub(r"[" + EMOJI + r"]\uFE0F?\s*", "", text))
        if target.startswith("#"):
            anchor = target[1:]
            if anchor not in self.anchors:
                self.missing[anchor] += 1
                return body
            return f'#link(label("{tlabel(anchor)}"))[{body}]'
        if target.startswith(("http://", "https://")):
            return f'#link("{target}")[{body}]'
        # A sibling markdown file is meaningless in a PDF; point at the repo.
        return f'#link("{REPO}/{target}")[{body}]'

    @staticmethod
    def math(expr: str) -> str:
        """LaTeX maths -> Typst maths.

        Only three commands appear in the book: \\text, \\mathbf and \\div.
        \\text is resolved first so that the \\mathbf wrapping it in the scoring
        section sees a finished string rather than a nested brace group.
        """
        expr = re.sub(r"\\text\{([^}]*)\}", lambda m: ' "' + m.group(1).strip() + '" ', expr)
        expr = re.sub(r"\\mathbf\{([^}]*)\}", lambda m: "bold(" + m.group(1).strip() + ")", expr)
        expr = expr.replace(r"\div", " div ")
        return re.sub(r"\s+", " ", expr).strip()

    def line_md(self, line: str) -> str:
        """One line of body text including its list marker.

        Needed inside callouts, where a leading `- ` is a bullet; handing it to
        the emphasis pass instead opens an italic that never closes.
        """
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            depth = len(m.group(1)) // 2
            bullet = "+" if m.group(2).endswith(".") else "-"
            return "  " * depth + bullet + " " + self.inline(m.group(3))
        return self.inline(line)

    # --- tables ------------------------------------------------------------
    @staticmethod
    def split_row(line: str):
        body = re.sub(r"(?<!\\)\|\s*$", "", re.sub(r"^\|", "", line.strip()))
        return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", body)]

    @staticmethod
    def parse_aligns(sep: str):
        out = []
        for c in Converter.split_row(sep):
            l, r = c.startswith(":"), c.endswith(":")
            out.append("center" if l and r else "right" if r else "left")
        return out

    def convert_table(self, rows, aligns):
        cols = len(aligns)
        out = ["#table(", f"  columns: {cols},",
               "  align: (" + ", ".join(aligns) + ",),"]
        for r in rows:
            cells = self.split_row(r)
            cells += [""] * (cols - len(cells))
            out.append("  " + ", ".join("[" + self.inline(c) + "]"
                                        for c in cells[:cols]) + ",")
        out.append(")")
        return out

    # --- blocks ------------------------------------------------------------
    @staticmethod
    def typst_str(s: str) -> str:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

    def convert(self):
        return self.convert_lines(self.lines)

    def convert_lines(self, lines):
        """The block parser. Runs on any list of markdown lines, which is
        what lets a callout body — 48 of the book's table rows live inside
        one — go through exactly the same path as top-level prose."""
        out, i, n = [], 0, len(lines)
        while i < n:
            line = lines[i]
            stripped = line.strip()

            # --- fenced blocks ---------------------------------------------
            if stripped.startswith("```"):
                lang = stripped[3:].strip()
                body, j = [], i + 1
                while j < n and not lines[j].strip().startswith("```"):
                    body.append(lines[j]); j += 1
                if lang == "mermaid":
                    out += [PHASE_FLOW, ""]
                else:
                    text = "\n".join(body).rstrip()
                    out += [f"#diagram(raw({self.typst_str(text)}))", ""]
                i = j + 1
                continue

            # --- tables -----------------------------------------------------
            if stripped.startswith("|") and i + 1 < n and \
                    re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
                aligns = self.parse_aligns(lines[i + 1])
                body, j = [], i + 2
                while j < n and lines[j].strip().startswith("|"):
                    body.append(lines[j]); j += 1
                out += self.convert_table([lines[i]] + body, aligns) + [""]
                i = j
                continue

            # --- headings ---------------------------------------------------
            m = re.match(r"^(#{1,6}) (.+)$", line)
            if m:
                level, title = len(m.group(1)), m.group(2).strip()
                out.append(f"{'=' * max(1, level - 1)} {self.inline(title)} "
                           f"<{tlabel(slug(title))}>")
                out.append("")
                i += 1
                continue

            # --- blockquotes: alerts, then epigraphs ------------------------
            if stripped.startswith(">"):
                block, j = [], i
                while j < n and (lines[j].strip().startswith(">")
                                 or lines[j].strip() == ""):
                    if lines[j].strip() == "":
                        if j + 1 < n and lines[j + 1].strip().startswith(">"):
                            block.append(""); j += 1; continue
                        break
                    block.append(re.sub(r"^\s*>\s?", "", lines[j])); j += 1
                out += self.convert_quote(block) + [""]
                i = j
                continue

            if stripped == "---":
                i += 1
                continue

            m = re.match(r"^(\s*)([-*]|\d+\.) (.*)$", line)
            if m:
                depth = len(m.group(1)) // 2
                bullet = "+" if m.group(2).endswith(".") else "-"
                out.append("  " * depth + bullet + " " + self.inline(m.group(3)))
                i += 1
                continue

            out.append(self.inline(line) if stripped else "")
            i += 1
        return out

    def convert_quote(self, block):
        first = block[0].strip() if block else ""
        m = re.match(r"^\[!(\w+)\]", first)
        if m:
            kind = CALLOUT.get(m.group(1).upper(), "ruling")
            rest = block[1:]
            while rest and not rest[0].strip():
                rest.pop(0)
            return [f"#{kind}[", *self.convert_lines(rest), "]"]

        text = "\n".join(block).strip()
        # A wholly italic single paragraph with no bold is a lead-in, not a
        # ruling: it orients the reader and carries no rule at all.
        if (len(block) == 1 and text.startswith("*") and text.endswith("*")
                and "**" not in text and not text.startswith('*"')):
            return [f"#aside[{self.inline(text.strip('*'))}]"]
        # An epigraph: an italic quotation, optionally attributed.
        if text.startswith('*"') or text.startswith('_"'):
            if "—" in text:
                quote, source = text.rsplit("—", 1)
                return [f"#epigraph[{self.inline(quote.strip().strip('*_'))}]"
                        f"[{self.inline(source.strip())}]"]
            return [f"#epigraph[{self.inline(text.strip('*_'))}][]"]
        return ["#ruling[", *self.convert_lines(block), "]"]


PHASE_FLOW = """#phase-flow(
  [*Phase 1*\\ Wind & Forecast],
  [*Phase 2*\\ Planning],
  [*Phase 3*\\ Movement],
  [*Phase 4*\\ Cleanup],
)"""

COVER = '''#cover(
  "Cardboard Regatta",
  "The Tactical Board Game of Competitive Sailboat Racing",
  "/images/cover.svg",
  tagline: [Harness the wind, master right-of-way tactics, and outmaneuver your
    rivals to take the bullet.],
)

#outline(title: [Contents], depth: 3, indent: auto)

'''

HEADER = '''// Cardboard Regatta — the rulebook.
//
// Converted from rules.md by tools/md2typst.py, then edited by hand. This file
// is the source of truth.
//
// Build:
//   typst compile --root . --font-path typst/fonts --ignore-system-fonts \\
//     typst/rules.typ rules.pdf

#import "lib/rulebook.typ": *

#show: rulebook.with(theme: sys.inputs.at("theme", default: "print"))

'''


def main():
    conv = Converter(SRC.read_text())
    body = "\n".join(conv.convert())

    # Everything above the first chapter is the title block and the markdown
    # table of contents. The cover replaces the former and #outline the latter.
    start = body.index("= Start Here: Your First Race")
    body = COVER + body[start:]
    body = re.sub(r"\n{3,}", "\n\n", body)

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(HEADER + body + "\n")

    print(f"wrote {DST} — {len(body.splitlines())} lines")
    print(f"anchors defined: {len(conv.anchors)}")
    if conv.missing:
        print("\nUNRESOLVED LINK TARGETS (emitted as plain text):")
        for a, c in conv.missing.most_common():
            print(f"  {a}  x{c}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
