"""Regression tests for the `_NEW_LINE_LABELS` label/gap/indent layout.

Two bootcamper-reported formatting defects were fixed by giving each PDF generator a
small allowlist of long-form `**Label:** paragraph` callouts that break to their own
line — the label, a gap, then the body indented — instead of continuing inline and
hanging-indenting under wherever the label happened to end:

* `generate_recap_pdf.py` — `Why it matters:` in every End-of-Module Summary.
* `generate_discoveries_pdf.py` — the `Near-miss (the one that teaches more):` and
  `Measurement:` callouts.

Both fixes worked and **nothing asserted them**. The existing recap suites check that
the three End-of-Module Summary *labels are present* (INV-103), which is
shape-independent, so they pass identically whether the value renders inline or on its
own line. That left the fix silently regressible three ways, each restoring the exact
defect reported:

1. **A key edited out of, or renamed in, either allowlist.** The keys are *normalized*
   forms — `"near miss the one that teaches more"` carries no hyphen and no parentheses,
   because the discoveries generator's `_normalize` replaces every non-alphanumeric with
   a space. A plausible-looking "tidy-up" to match the label as it appears on the page
   would stop matching and produce no error, just the old layout.
2. **The `not force_new_line` guard removed** from the pre-existing hanging-indent
   branch, re-applying the hanging indent on top of the new layout.
3. **The gap or indent constants changed** while chasing an unrelated spacing issue.

The allowlist's *narrowness* is itself load-bearing and is pinned here too: a blanket
"every `**Label:**` breaks to its own line" change broke
`test_consecutive_paragraphs_have_a_blank_line_between_them` and
`test_a_soft_wrapped_label_is_not_split_mid_sentence` in `tests/test_discoveries_pdf.py`,
because a short label like `Cross-source overlap:` is meant to stay inline with its
wrapped continuation. So each generator is asserted from both sides: the allowlisted
labels break, a non-allowlisted label does not.

⛔ Layout is asserted **relatively** — the value sits on a later line and further right
than its label — never against the millimeter constants (`_ITEM_GAP_MM * 2`, `+= 12`).
A deliberate design tweak must stay possible; an accidental collapse back to inline must
fail. Text position is read from the PDF content stream directly rather than via
`pdftotext`, which is absent on some supported platforms (see
`specs/pdf-layout-verification-without-poppler.md`).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zlib
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts")
RECAP_SCRIPT = os.path.join(SCRIPTS, "generate_recap_pdf.py")
DISCOVERIES_SCRIPT = os.path.join(SCRIPTS, "generate_discoveries_pdf.py")


def load(name, path):
    """Import a bundled generator by path — they are scripts, not an installed package.

    Registered in ``sys.modules`` *before* ``exec_module`` because both generators
    declare dataclasses, and the dataclass machinery resolves annotations through
    ``sys.modules[cls.__module__]`` — absent that entry it raises on the first
    ``@dataclass``.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Loaded once: importing a generator twice under two names would give two independent
# copies of the very constants under test.
RECAP_GEN = load("recap_gen_new_line_labels", RECAP_SCRIPT)
DISCOVERIES_GEN = load("discoveries_gen_new_line_labels", DISCOVERIES_SCRIPT)


def pdf_pages(path):
    """Text runs per page as ``[(x, y, text), ...]``, in the page tree's own order.

    Pages are resolved through ``/Type /Pages`` -> ``/Kids`` -> each page's
    ``/Contents`` stream rather than by walking every ``stream ... endstream`` in file
    order, because embedded images are streams too and counting one as a page shifts
    every later page.

    Per-page grouping is what makes the y comparisons below sound: y grows *upward* in
    PDF user space, so "further down the page" is a smaller y — a comparison that is
    meaningless across a page break.
    """
    with open(path, "rb") as handle:
        raw = handle.read()
    objects = {
        int(m.group(1)): m.group(2)
        for m in re.finditer(rb"(\d+) 0 obj\r?\n(.*?)\r?\nendobj", raw, re.S)
    }
    tree = next((b for b in objects.values() if b"/Type /Pages" in b), b"")
    kids = re.search(rb"/Kids \[(.*?)\]", tree, re.S)
    pattern = re.compile(r"([\d.]+)\s+([\d.]+)\s+(?:Td|Tm)\b(.*?)\bTj", re.S)
    pages = []
    for number in (int(n) for n in re.findall(rb"(\d+) 0 R", kids.group(1) if kids else b"")):
        body = objects.get(number, b"")
        contents = re.search(rb"/Contents (\d+) 0 R", body)
        if not contents:
            continue
        stream = re.search(
            rb"stream\r?\n(.*?)\r?\nendstream", objects.get(int(contents.group(1)), b""), re.S
        )
        if not stream:
            continue
        try:
            decoded = zlib.decompressobj().decompress(stream.group(1))
        except zlib.error:
            decoded = stream.group(1)
        runs = []
        for match in pattern.finditer(decoded.decode("latin-1", "replace")):
            text = re.findall(r"\((.*?)\)\s*$", match.group(3).strip())
            if text:
                runs.append(
                    (round(float(match.group(1)), 1), round(float(match.group(2)), 1), text[0])
                )
        pages.append(runs)
    return pages


def squash(text):
    """Reduce to lowercase alphanumerics, so PDF escaping cannot fail a comparison."""
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def locate(pages, label, value_start):
    """Find ``label`` and the run beginning ``value_start`` on the same page.

    Returns ``((label_x, label_y), (value_x, value_y))``. The value is searched only
    *after* the label within that page's run order, so a phrase that also appears
    earlier cannot be matched by accident.
    """
    want_label, want_value = squash(label), squash(value_start)
    for runs in pages:
        for i, (_x, _y, text) in enumerate(runs):
            if squash(text) != want_label:
                continue
            for x2, y2, text2 in runs[i + 1:]:
                if squash(text2).startswith(want_value[:40]):
                    return (runs[i][0], runs[i][1]), (x2, y2)
    return None, None


def render(script, markdown, filename="doc.md", subdir=None):
    """Render `markdown` through `script` and return the output PDF path."""
    workdir = tempfile.mkdtemp()
    target = os.path.join(workdir, subdir) if subdir else workdir
    os.makedirs(target, exist_ok=True)
    src = os.path.join(target, filename)
    out = os.path.join(workdir, "out.pdf")
    with open(src, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    proc = subprocess.run(
        [sys.executable, script, "--input", src, "--output", out],
        capture_output=True,
        text=True,
        cwd=workdir,
    )
    assert proc.returncode == 0, proc.stderr
    assert os.path.exists(out), proc.stdout + proc.stderr
    return out


# A multi-sentence "Why it matters" is the shape that made the defect visible: a short
# value fits beside its label either way, so only a value long enough to wrap shows
# whether the continuation hangs under the label or starts a clean indented paragraph.
WHY_VALUE = (
    "Resolving these records is what turns four disconnected extracts into one "
    "auditable customer view, which is the outcome the whole engagement is measured "
    "against and the reason the mapping work earlier in the module mattered at all."
)
INLINE_LABEL_VALUE = (
    "Two sources were registered and both loaded without a single rejected record, "
    "which is the checkpoint this module exists to reach before any querying starts."
)

RECAP = f"""# Bootcamp Recap

**Bootcamper:** Ada Lovelace

## Data processing — 2026-07-29T09:00:00-07:00

### Information Shared

- How records are loaded and resolved.

### Questions & Responses

- **Q:** Which sources should load first?
  - **A:** The reference source, then the watchlist.

### Actions Taken

- **What we did:** {INLINE_LABEL_VALUE}

### End-of-Module Summary

**What you accomplished:**
- Loaded both sources and confirmed the resolution counts.

**Files produced:**
- `src/load.py` — the loader.

**Why it matters:** {WHY_VALUE}

---
"""

NEAR_MISS_VALUE = (
    "Entity 3301 did not merge with entity 3302 because the two addresses disagreed "
    "outright, and reading that disagreement is what teaches the difference between a "
    "principled non-merge and a missed one."
)
MEASUREMENT_VALUE = (
    "Four cross-source merges against eight shared organization names, which is the "
    "ratio that distinguishes low source overlap from pipeline underperformance."
)
OVERLAP_VALUE = (
    "Only eight organization names appear in both sources, so the achievable ceiling "
    "was always going to be small relative to the record counts."
)

DISCOVERIES = f"""# Data Discoveries

**Bootcamper:** Ada Lovelace

## Headline numbers, interpreted

- **Records loaded:** 4,012 across two sources.

**Cross-source overlap:** {OVERLAP_VALUE}

## Merges and match keys

Every merge carries the match key that drove it.

## Review queue

One human decision each.

## Why and how: worked examples

**Near-miss (the one that teaches more):** {NEAR_MISS_VALUE}

## Relationship networks

Multi-hop paths no single record states on its own.

## What was not found, and why

**Measurement:** {MEASUREMENT_VALUE}
"""


class LabelLayoutAssertions(unittest.TestCase):
    """Shared relative-layout assertions, so both generators are held to one contract."""

    def assert_breaks_to_its_own_line(self, pages, label, value_start):
        anchor, value = locate(pages, label, value_start)
        self.assertIsNotNone(
            anchor, f"neither the label {label!r} nor its value was rendered"
        )
        label_x, label_y = anchor
        value_x, value_y = value
        self.assertLess(
            value_y,
            label_y,
            f"{label!r} rendered its value on the same line as the label "
            f"(label y={label_y}, value y={value_y}). The value must start on a "
            "later line — check the generator's _NEW_LINE_LABELS allowlist still "
            "matches this label through its own normalizer.",
        )
        self.assertGreater(
            value_x,
            label_x,
            f"{label!r}'s value is not indented relative to its label "
            f"(label x={label_x}, value x={value_x}).",
        )

    def assert_stays_inline(self, pages, label, value_start):
        anchor, value = locate(pages, label, value_start)
        self.assertIsNotNone(
            anchor, f"neither the label {label!r} nor its value was rendered"
        )
        _label_x, label_y = anchor
        value_x, value_y = value
        self.assertEqual(
            label_y,
            value_y,
            f"{label!r} is NOT in the allowlist, so its value must stay inline on the "
            f"label's line (label y={label_y}, value y={value_y}). Forcing every "
            "'**Label:**' onto its own line puts a blank line mid-sentence for short "
            "labels — the case the allowlist exists to protect.",
        )
        self.assertGreater(value_x, 0)


@requires_fpdf2
class RecapWhyItMattersBreaksToItsOwnLine(LabelLayoutAssertions):
    """The recap generator's `Why it matters:` layout, as reported and fixed."""

    @classmethod
    def setUpClass(cls):
        cls.pages = pdf_pages(render(RECAP_SCRIPT, RECAP, filename="recap.md"))

    def test_value_starts_on_a_later_line_and_indented(self):
        self.assert_breaks_to_its_own_line(self.pages, "Why it matters:", WHY_VALUE)

    def test_a_label_outside_the_allowlist_stays_inline(self):
        self.assert_stays_inline(self.pages, "What we did: ", INLINE_LABEL_VALUE)


@requires_fpdf2
class DiscoveriesLongLabelsBreakToTheirOwnLine(LabelLayoutAssertions):
    """The discoveries generator's two allowlisted callouts, and one that must not break."""

    @classmethod
    def setUpClass(cls):
        cls.pages = pdf_pages(
            render(
                DISCOVERIES_SCRIPT,
                DISCOVERIES,
                filename="bootcamp_data_discoveries.md",
                subdir="docs",
            )
        )

    def test_near_miss_value_starts_on_a_later_line_and_indented(self):
        self.assert_breaks_to_its_own_line(
            self.pages, "Near-miss (the one that teaches more):", NEAR_MISS_VALUE
        )

    def test_measurement_value_starts_on_a_later_line_and_indented(self):
        self.assert_breaks_to_its_own_line(self.pages, "Measurement:", MEASUREMENT_VALUE)

    def test_a_short_label_stays_inline(self):
        self.assert_stays_inline(self.pages, "Cross-source overlap: ", OVERLAP_VALUE)


class AllowlistKeysMatchTheLabelsTheyName(unittest.TestCase):
    """Each key must match its label *through the generator's own normalizer*.

    This is the regression that would otherwise be invisible. The keys are normalized
    forms, not the label text as it appears on the page, so editing one to "match what
    the document says" silently disables the fix — no error, no failing test, just the
    old hanging-indent layout returning.
    """

    def test_recap_key_matches_why_it_matters(self):
        self.assertIn(
            RECAP_GEN._normalize_heading("Why it matters"),
            RECAP_GEN._NEW_LINE_LABELS,
            "generate_recap_pdf.py's _NEW_LINE_LABELS no longer matches the "
            "'Why it matters' label through _normalize_heading, so the label would "
            "render inline again.",
        )

    def test_every_recap_key_is_reachable_from_some_label(self):
        """A key no label can produce is dead configuration — catch it here."""
        for key in RECAP_GEN._NEW_LINE_LABELS:
            with self.subTest(key=key):
                self.assertEqual(
                    key,
                    RECAP_GEN._normalize_heading(key),
                    f"{key!r} is not in _normalize_heading's normal form, so no label "
                    "can ever equal it.",
                )

    def test_discoveries_keys_match_their_labels(self):
        for label in ("Near-miss (the one that teaches more)", "Measurement"):
            with self.subTest(label=label):
                self.assertIn(
                    DISCOVERIES_GEN._normalize(label),
                    DISCOVERIES_GEN._NEW_LINE_LABELS,
                    f"generate_discoveries_pdf.py's _NEW_LINE_LABELS no longer matches "
                    f"{label!r} through _normalize, so the callout would render inline "
                    "again.",
                )

    def test_every_discoveries_key_is_reachable_from_some_label(self):
        for key in DISCOVERIES_GEN._NEW_LINE_LABELS:
            with self.subTest(key=key):
                self.assertEqual(
                    key,
                    DISCOVERIES_GEN._normalize(key),
                    f"{key!r} is not in _normalize's normal form, so no label can ever "
                    "equal it.",
                )

    def test_a_short_label_is_deliberately_absent(self):
        """`Cross-source overlap:` must stay out of the allowlist (see module docstring)."""
        self.assertNotIn(
            DISCOVERIES_GEN._normalize("Cross-source overlap"),
            DISCOVERIES_GEN._NEW_LINE_LABELS,
        )


class TheHangingIndentBranchStaysSuppressed(unittest.TestCase):
    """Guard #2: the `not force_new_line` condition on the pre-existing indent branch.

    Removing it re-applies the hanging indent on top of the new layout — the value
    still starts below its label, so the layout tests above still pass, and the defect
    returns anyway. Asserted on the source because the resulting shift is a few
    millimeters and would make a rendered assertion brittle.
    """

    def test_both_generators_guard_the_indent_branch(self):
        for path in (RECAP_SCRIPT, DISCOVERIES_SCRIPT):
            with self.subTest(script=os.path.basename(path)):
                with open(path, encoding="utf-8") as handle:
                    source = handle.read()
                self.assertIn(
                    "if not force_new_line and remaining <",
                    source,
                    f"{os.path.basename(path)} no longer suppresses the hanging-indent "
                    "branch for an allowlisted label; the label breaks to its own line "
                    "AND the body is hanging-indented under it.",
                )


if __name__ == "__main__":
    unittest.main()
