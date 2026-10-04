"""One wrap-aware matcher for every guard whose rule is about a phrase or a sentence.

Markdown wraps prose wherever the column runs out, so a phrase can start on one line and end on
the next. A guard that reads one line at a time cannot see it there. #387 found exactly that:
Module 7 Step 3a carried a retired claim for a month because "no" ended one line and
"flag is *documented*" began the next. This module holds the one matcher such guards share, so
each does not grow its own collapse rule.

⛔ **A guard whose rule is about a phrase or a sentence MUST match it across a line wrap; a guard
that reads single lines on purpose MUST say why.**

``match_lines(text, pattern)`` returns the 1-based line on which each match of ``pattern``
starts, in order of appearance, so a guard can keep reporting ``file:line``.

How the text is read:

- **Blocks.** The text is cut into Markdown blocks, and ``pattern`` runs on each block on its
  own. No match spans two blocks, and ``^`` and ``$`` anchor at the start and end of a block.
  Within a block every run of whitespace, line breaks included, becomes one space, and the block
  is trimmed. So a match at the start of a block is reported at the block's first non-blank line.
- **Block boundaries:** a blank line; a code-fence line; the end of each table row (a line whose
  first non-blank character is ``|``); an ATX heading line (``#`` to ``######``); and the front
  matter, from a ``---`` on the first line to the next ``---`` line. A heading line, a table row,
  a fence line and the front matter's contents are each a block of their own. A ``---`` line
  anywhere else is a thematic break, and front-matter handling does not apply to it.
- **Fences.** A code-fence line is any line whose first non-blank characters are three
  backticks or ``~~~``, so a fence indented inside a list item counts. A fence opened with one
  character is closed only by a fence line of the same character, so a ``~~~`` fence can hold
  backtick lines as content. Inside a fence only a blank line ends a block: lines starting with
  ``#``, ``|`` or ``---`` are content there, and the fenced contents never join the prose
  around them.
- **Blockquotes.** Outside a fence, a line's leading ``>`` markers (and the space after each)
  are stripped before it is read, so a phrase wrapped inside a blockquote still matches.
  Entering or leaving a blockquote is not a boundary by itself; a line holding only ``>`` is
  blank once its marker is stripped, so it is a boundary.
- **Lists.** Lines of one list with no blank line between them are one block, as #426 specifies.
  A phrase made from the end of one item and the start of the next can therefore match. That is
  accepted; if a guard hits it on correct prose, fix the matcher (INV-282). ⚠️ #381's
  ``sentences`` differs here: its ``BLOCK_BREAK`` also breaks before a list marker.

Its own tests are in ``tests/test_wrapped_text.py``.

Stdlib only; nothing under the plugin is imported (INV-108).

Source issue: #426 (part of #418).
"""
import re

#: Leading blockquote markers, each with the one optional space after it.
_QUOTE_MARKERS = re.compile(r"^[ \t]*(?:>[ ]?[ \t]*)+")
#: A code-fence line: its first non-blank characters are three backticks or three tildes.
_FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
#: An ATX heading line, up to three spaces of indent, then one to six `#` and a space or the end.
_HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")


def _strip_quote(line):
    return _QUOTE_MARKERS.sub("", line, count=1)


def _front_matter_end(lines):
    """Index of the closing ``---`` when the text opens with front matter, else None."""
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i
    return None


def blocks(text):
    """The Markdown blocks of ``text``, each a list of ``(lineno, line)`` pairs, in order.

    ``lineno`` is 1-based. Blockquote markers are already stripped from lines outside a fence.
    """
    lines = text.split("\n")
    out, current = [], []

    def close():
        if current:
            out.append(list(current))
            current.clear()

    start = 0
    end = _front_matter_end(lines)
    if end is not None:
        out.append([(n + 1, lines[n]) for n in range(1, end)])
        start = end + 1

    fence = None  # the fence character while inside a fence, else None
    for i in range(start, len(lines)):
        raw, lineno = lines[i], i + 1
        stripped = _strip_quote(raw)
        opener = _FENCE.match(stripped)
        if opener and (fence is None or opener.group(1)[0] == fence):
            close()
            out.append([(lineno, stripped)])
            fence = None if fence else opener.group(1)[0]
            continue
        if fence:
            if raw.strip():
                current.append((lineno, raw))
            else:
                close()
            continue
        if not stripped.strip():
            close()
        elif _HEADING.match(stripped) or stripped.lstrip().startswith("|"):
            close()
            out.append([(lineno, stripped)])
        else:
            current.append((lineno, stripped))
    close()
    return out


def _collapse(block):
    """A block's text with whitespace collapsed and trimmed, and each character's line."""
    chars, origin = [], []
    in_space = False
    for lineno, line in block:
        for char in line + "\n":
            if char.isspace():
                if not in_space and chars:
                    chars.append(" ")
                    origin.append(lineno)
                in_space = True
            else:
                chars.append(char)
                origin.append(lineno)
                in_space = False
    if chars and chars[-1] == " ":
        chars.pop()
        origin.pop()
    return "".join(chars), origin


def match_lines(text, pattern):
    """1-based line numbers where each match of the compiled ``pattern`` starts, in order.

    ``pattern`` runs on each collapsed, trimmed block of ``text`` on its own (see the module
    docstring), so a phrase wrapped across lines is one match and no match spans two blocks.
    """
    found = []
    for block in blocks(text):
        flat, origin = _collapse(block)
        if not flat:
            continue
        for m in pattern.finditer(flat):
            found.append(origin[min(m.start(), len(origin) - 1)])
    return found
