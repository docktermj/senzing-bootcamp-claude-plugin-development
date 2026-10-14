"""Every shipped pointer to one `ground-rules.md` section, derived by scan, and its citation (#519).

INV-352, INV-354, INV-355 and INV-357 each state their rule once, in a named section of
`ground-rules.md`, and every other site points there (INV-300). Before #519 those pointer sites
cited INV-300 alone, so a reader at the line could name the single-statement discipline but not
the rule it points at. #519 adds the substantive invariant beside INV-300 at every pointer, and
this module is how the four guards check that each one carries it.

⛔ **The sites are derived, not listed (INV-246).** A list of the eighteen sites #519 found would
certify those eighteen and nothing else: a step added next month that points at "Directing steps"
with INV-300 alone would pass. So ``uncited_pointers`` scans every shipped Markdown file for a
sentence that points at the section, and requires the invariant in that sentence.

How a pointer is found:

- **The corpus.** Every ``.md`` file under ``plugins/``, listed by ``_corpus.corpus_files``,
  except `ground-rules.md` itself: the owner's own cross-references ("see "Worked steers"
  above") sit inside the rule's file and are not pointer sites.
- **The pointer.** A sentence that names the section in double quotes (``"Directing steps"``),
  or that links its anchor (``ground-rules.md#directing-steps``).
- **The sentence.** Each Markdown block from ``_wrapped_text.blocks`` is collapsed to one line,
  so a name or citation wrapped across lines is still one phrase (INV-346), and cut into
  sentences where ``.``, ``!`` or ``?`` (with any closing quote, emphasis or bracket) meets a
  space. The citation must sit in the pointer's own sentence: a paragraph that cites the
  invariant three sentences away does not tell the reader at the pointer which rule it is.
- **The citation.** ``INV-nnn`` as a whole token, anywhere in that sentence.

⚠️ **What the derivation cannot see**, said here once and repeated in each guard's docstring:

- a pointer that names the section in other words ("the ground rules' worked-steer section") or
  by its heading's Markdown link text alone, with neither the quoted name nor the anchor;
- a pointer outside ``plugins/`` or in a file that is not Markdown (a script, a hook's JSON);
- whether the invariant cited is the **right** one for what the sentence says, or whether the
  site restates the rule instead of pointing at it (INV-300's "no second copy");
- a sentence the splitter cuts early, at an abbreviation such as "e.g." before the name.

**Section pointers (#615).** The second half of this module checks every
`<file>.md` → "<name>" pointer in shipped Markdown against the file it names:
``section_pointers`` finds them wrap-aware, ``section_names`` says what a section name is (a
heading or a bold label opening a line, ignoring case, leading numbering and a parenthetical
qualifier at either end), ``section_kind`` says which of the two a name lands on, and
``section_pointer_problems`` resolves the file from the pointer's own file. `tests/test_section_pointers_resolve.py` is its guard.

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issues: #519, #615.
"""
import re
from pathlib import Path

import _corpus
import _wrapped_text

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS = REPO_ROOT / "plugins"
OWNER = PLUGINS / "senzing-bootcamp" / "skills" / "bootcamp-onboarding" / "ground-rules.md"

#: A sentence ends at ., ! or ? (with any closing quote, emphasis or bracket) and a space.
SENTENCE_END = re.compile(r"(?<=[.!?])[\"'*_)\]]*\s+")


def shipped_texts():
    """``{path: text}`` for every shipped Markdown file except the owner, `ground-rules.md`."""
    return {p: p.read_text(encoding="utf-8")
            for p in _corpus.corpus_files("plugins", suffixes={".md"}) if p != OWNER}


def _collapse(block):
    """A block's lines joined with whitespace collapsed, and the source line of each character."""
    chars, origin = [], []
    for lineno, line in block:
        for char in line + "\n":
            if char.isspace():
                if chars and chars[-1] != " ":
                    chars.append(" ")
                    origin.append(lineno)
            else:
                chars.append(char)
                origin.append(lineno)
    while chars and chars[-1] == " ":
        chars.pop()
        origin.pop()
    return "".join(chars), origin


def sentences(text):
    """``(lines, sentence)`` for each sentence of ``text``, wrapped lines joined (INV-346).

    ``lines[i]`` is the 1-based source line of ``sentence[i]``, so a match can be reported at
    the line it starts on.
    """
    for block in _wrapped_text.blocks(text):
        flat, origin = _collapse(block)
        start = 0
        for end in SENTENCE_END.finditer(flat):
            stop = end.start() + len(end.group(0).rstrip())
            yield origin[start:stop], flat[start:stop]
            start = end.end()
        if start < len(flat):
            yield origin[start:], flat[start:]


def pointer_pattern(name, anchor):
    """A sentence naming ``name`` in double quotes, at any wrap, or linking ``#anchor``."""
    quoted = r'"' + r"\s+".join(re.escape(word) for word in name.split()) + r'"'
    return re.compile(quoted + "|" + re.escape("ground-rules.md#" + anchor))


def pointers(texts, name, anchor):
    """``(path, line, sentence)`` for every sentence in ``texts`` that points at the section."""
    pattern = pointer_pattern(name, anchor)
    found = []
    for path, text in sorted(texts.items()):
        for lines, sentence in sentences(text):
            match = pattern.search(sentence)
            if match:
                found.append((path, lines[match.start()], sentence))
    return found


def uncited_pointers(texts, name, anchor, invariant):
    """Every pointer to the section whose sentence does not cite ``invariant``, as ``path:line``."""
    cited = re.compile(r"\b%s\b" % re.escape(invariant))
    problems = []
    for path, line, sentence in pointers(texts, name, anchor):
        if not cited.search(sentence):
            try:
                where = path.relative_to(REPO_ROOT)
            except ValueError:
                where = path
            problems.append("%s:%d points at %r without citing %s: %s"
                            % (where.as_posix(), line, name, invariant, sentence[:160]))
    return problems


def without_citation(texts, path, line, invariant):
    """A copy of ``texts`` whose pointer at ``path:line`` no longer cites ``invariant``.

    For negative controls: the first ``, INV-nnn`` (or bare ``INV-nnn``) on or after ``line``
    is removed, which is where every shipped pointer carries it.
    """
    lines = texts[path].split("\n")
    at = next(i for i in range(line - 1, len(lines)) if invariant in lines[i])
    cited = ", " + invariant
    lines[at] = lines[at].replace(cited if cited in lines[at] else invariant, "", 1)
    out = dict(texts)
    out[path] = "\n".join(lines)
    return out


# --- Section pointers: `<file>.md` → "<name>" (#615) ------------------------------------------
#
# The quoted-name pointers above are found for one section. These are every pointer of the form
# `<file>.md` → "<name>" in shipped Markdown, and they are checked against what the target file
# actually holds. This is the one place that says what a section name is.

#: A backticked Markdown file, an arrow and a double-quoted name, on one collapsed block.
SECTION_POINTER = re.compile(r'`([^`\s]+\.md)` ?→ ?"([^"]+)"')

_FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$")
#: A bold label: a bold span that opens a line, after any indent, blockquote, list marker or ⛔/⚠️.
_BOLD_LABEL = re.compile(
    r"^[ \t]*(?:>[ \t]*)*(?:(?:[-*+]|\d+[.)])[ \t]+)?(?:(?:⛔|⚠️)[ \t]*)?\*\*(.+?)\*\*", re.M | re.S)
_NUMBERING = re.compile(r"^\d+[a-z]?\.\s+", re.I)
#: A parenthetical qualifier at either end: "(required)", "(INV-160)", "(silent)".
_QUALIFIER = re.compile(r"^\([^()]*\)\s*|\s*\([^()]*\)$")


def _normalized(name):
    """``name`` lower-cased, whitespace collapsed, leading numbering (``2.``, ``6c.``) dropped."""
    return _NUMBERING.sub("", " ".join(name.split())).lower()


def section_names_by_kind(text):
    """``{"heading": names, "bold label": names}``: every name a pointer may use for a section.

    A heading outside a code fence, or a bold label opening a line (``**Name.**``,
    ``**Name:**``), names a section. Each is matched as its whole text, ignoring case and leading
    numbering, and also with a parenthetical qualifier at either end dropped, so "Server lifetime"
    names "## Server lifetime (required in every module that starts one)". Nothing shorter: a
    sentence's opening words are not a name.
    """
    headings, fence, prose = [], None, []
    for line in text.split("\n"):
        opener = _FENCE.match(line)
        if opener and (fence is None or opener.group(1)[0] == fence):
            fence = None if fence else opener.group(1)[0]
            prose.append("")
            continue
        heading = None if fence else _HEADING.match(line)
        if heading:
            headings.append(heading.group(1))
        prose.append("" if fence else line)
    labels = [m.group(1).rstrip(".:") for m in _BOLD_LABEL.finditer("\n".join(prose))]
    kinds = {}
    for kind, found in (("heading", headings), ("bold label", labels)):
        names = kinds[kind] = set()
        for name in map(_normalized, found):
            names.add(name)
            names.add(_QUALIFIER.sub("", name))
    return kinds


def section_names(text):
    """Every name a pointer may use for a section of ``text``: a heading or a bold label."""
    kinds = section_names_by_kind(text)
    return kinds["heading"] | kinds["bold label"]


def section_kind(text, name):
    """``"heading"`` or ``"bold label"`` when ``name`` names a section of ``text``, else None.

    A name that is both counts as a heading.
    """
    kinds, key = section_names_by_kind(text), _normalized(name)
    return next((kind for kind in ("heading", "bold label") if key in kinds[kind]), None)


def names_a_section(text, name):
    """True when name is one of section_names(text), read the same way."""
    return section_kind(text, name) is not None


def section_pointers(path, text):
    """``(line, target, name)`` for every `<file>.md` → "<name>" pointer in ``text``, wrap-aware."""
    found = []
    for block in _wrapped_text.blocks(text):
        flat, origin = _collapse(block)
        for m in SECTION_POINTER.finditer(flat):
            found.append((origin[m.start()], m.group(1), m.group(2)))
    return found


def section_pointer_problems(path, text, read=lambda p: p.read_text(encoding="utf-8")):
    """Each pointer in ``text`` whose file does not resolve from ``path``, or names no section."""
    problems = []
    for line, target, name in section_pointers(path, text):
        where = "%s:%d" % (_shown(path), line)
        resolved = path.parent / target
        if not resolved.is_file():
            problems.append('%s: `%s` does not resolve from %s' % (where, target, path.name))
        elif not names_a_section(read(resolved), name):
            problems.append('%s: `%s` → "%s" names no heading or bold label there'
                            % (where, target, name))
    return problems


def _shown(path):
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)
