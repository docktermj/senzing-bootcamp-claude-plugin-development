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

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issue: #519.
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
