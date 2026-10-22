"""The stdlib PDF writers wrap code and table content; they never clip its tail (#674).

Both bundled generators sliced content **after** the content-retention audit had counted
it, so the audit could not see the loss and no other signal reported it:

* `generate_discoveries_pdf.py` cut every code line at 92 characters (`block.text[:92]`)
  and every table row at the line width (`add(line[:max_width_chars], …)`);
* `generate_recap_pdf.py` cut every table cell at its column width and every row at the
  line budget in `_stdlib_table` (`c[:w]`, `line[:budget]`), and again in
  `_render_table_monospace`, the fallback the **rich** renderer drops to when its grid
  path raises.

A synthetic probe measured discoveries retention 0.988 and recap retention 0.924 while
every sentinel suffix placed past a clipping boundary was absent from the extracted text,
with nothing on stderr and exit 0. That is the shape of the defect these tests pin: the
success signals were all green and the deliverable was missing identifiers, command tails
and findings.

⚠️ **Retention cannot be the assertion here.** It is computed from the parse against the
source, before a renderer runs, so it is structurally unable to see a clip — the same
blindness `test_stdlib_writer_character_safety.py` records for `?` substitution. These
tests extract the text the PDF actually carries and look for the suffixes.

Deliberately **not** guarded by `@requires_fpdf2` except where a test names the fpdf2
renderer: the no-fpdf2 path is the one the issue is about, and the one most bootcampers
hit. `fpdf` is shadowed on `PYTHONPATH` for the end-to-end renders so the fallback runs
whether or not the package is installed.

Graduation stays non-blocking (INV-048/INV-052): a document whose content cannot all be
placed still produces a PDF and exits 0 — it just says so on stderr first.

INV-408 (a bundled generator wraps or re-lays content and never clips it, and reports what it
cannot place before its success line) names this file as its enforcer. It extracts the text the
PDF carries; it does not establish that the page is legible to a human reader, which is a visual
inspection.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import inspect
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
RECAP = os.path.join(SCRIPTS, "generate_recap_pdf.py")
DISCOVERIES = os.path.join(SCRIPTS, "generate_discoveries_pdf.py")

SUCCESS_LINE = "PDF generated:"

#: Sentinels sit at the END of a long value, past every boundary the old code clipped at:
#: 40 and 46 characters (column caps), 87/92/94 (line budgets). Each is a single word, so
#: a word-wrap cannot split it and a failure means the characters are gone, not folded.
CELL_TAIL = "ZYGOMORPHIC_CELL_TAIL"
COLUMN_TAIL = "ALPHA_OMEGA_COLUMN_TAIL"
CODE_TAIL = "CODE_LINE_SENTINEL_TAIL"
RECAP_CELL_TAIL = "PENULTIMATE_RECAP_CELL_TAIL"
#: The last column of a table with more columns than the line can hold even at the
#: narrowest width the layout allows. That row used to be cut at the line budget, so
#: every column past it was gone from the page.
WIDE_TAIL = "WIDE_TABLE_LAST_COLUMN_TAIL"

#: An identifier with no spaces at all, longer than every line budget. It MUST be broken
#: mid-token to fit, so it is checked against the text with whitespace removed — a break is
#: a wrap, not a loss, and the assertion has to tell the two apart.
UNBROKEN = ("IDENTIFIER_WITH_NO_SPACES_AT_ALL_THAT_IS_LONGER_THAN_ANY_LINE_BUDGET_"
            "AND_MUST_BREAK_MID_TOKEN_UNBROKEN_SENTINEL_END")

DISCOVERIES_DOC = """# Data Discoveries

**Bootcamper:** Ada Lovelace
**Sources:** ENFORMION, EQUIFAX

## Your question, answered

| Requirement | Answer | Where in this document |
|---|---|---|
| Which customers appear in both sources? | 4 cross-source merges, near the overlap ceiling, which is as close to the ceiling as these two mapped sources can get %(cell)s | Merges and match keys %(column)s |

## Headline numbers, interpreted

- **Records loaded:** 4,012 across two sources

```
python3 scripts/generate_discoveries_pdf.py --input docs/bootcamp_data_discoveries.md --output docs/bootcamp_data_discoveries.pdf --subtitle "what the data showed" %(code)s
%(unbroken)s
```

## Merges and match keys

Every merge below carries the key that drove it.

| Column alpha one | Column bravo two | Column charlie 3 | Column delta four | Column echo five | Column foxtrot 6 | Column golf seven | Column hotel eight | Column india nine | Column juliett ten | Column kilo eleven | Column lima twelve |
|---|---|---|---|---|---|---|---|---|---|---|---|
| alpha value here | bravo value here | charlie value 03 | delta value four | echo value 00005 | foxtrot value 06 | golf value seven | hotel value eight | india value nine | juliett value ten | kilo value eleven | %(wide)s |

## Review queue

- Two cross-source pairs await one human decision each

## Why and how: worked examples

A worked example, read end to end.

## Relationship networks

One network, three members.

## What was not found, and why

Nothing a loaded source could have answered.
""" % {"cell": CELL_TAIL, "column": COLUMN_TAIL, "code": CODE_TAIL,
       "unbroken": UNBROKEN, "wide": WIDE_TAIL}

RECAP_DOC = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-07-20

## Data processing — 2026-07-21T09:00:00-05:00

### Information Shared

The table below carries cells far longer than any column width.

| Match key | What it means for this pair of records | Count |
|---|---|---|
| +NAME+ADDRESS | both records agree on the full name and on the street address, which is the strongest everyday combination %(cell)s | 12 %(column)s |

### Questions & Responses

- **Q:** Ready to proceed. **R:** Yes

### Actions Taken

- Loaded both sources and drained the redo queue

### End-of-Module Summary

**What you accomplished:** Loaded and resolved both sources end to end.

**Files produced:**
- `database/G2C.db` — the resolved repository

**Why it matters:** Every later module builds on this loaded data.
""" % {"cell": RECAP_CELL_TAIL, "column": COLUMN_TAIL}

#: A row carrying one more cell than the header declares. The grid has nowhere to put it,
#: so it is dropped — and that drop must be REPORTED, which is the other half of #674.
RAGGED_RECAP_DOC = RECAP_DOC.replace(
    "| 12 %s |" % COLUMN_TAIL,
    "| 12 %s | ORPHANED_FOURTH_CELL |" % COLUMN_TAIL,
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves its module via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pdf_text(path):
    """Every `(...) Tj` string in the file, decompressing streams that are compressed.

    The same extraction `test_stdlib_writer_character_safety.py` uses: the stdlib writer's
    own output format, read back, rather than any claim the generator makes about it.
    """
    with open(path, "rb") as handle:
        raw = handle.read()
    out = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S):
        body = match.group(1)
        try:
            body = zlib.decompressobj().decompress(body)
        except zlib.error:
            pass
        out += [t.decode("latin-1") for t in re.findall(rb"\((.*?)\)\s*Tj", body, re.S)]
    return " ".join(out)


def render_without_fpdf2(tmp, script, markdown, name):
    """Render `markdown` with `fpdf` shadowed on PYTHONPATH, so the stdlib writer runs.

    `HOME` is left alone and the working directory is the temp dir: nothing here reads a
    user-level file, and the generators resolve their own helpers from their own directory.
    """
    src = os.path.join(tmp, name)
    out = os.path.join(tmp, "out.pdf")
    with open(src, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    shim = os.path.join(tmp, "shim")
    os.makedirs(shim, exist_ok=True)
    with open(os.path.join(shim, "fpdf.py"), "w", encoding="utf-8") as handle:
        handle.write('raise ImportError("forced for this test")\n')
    env = dict(os.environ, PYTHONPATH=shim)
    result = subprocess.run(
        [sys.executable, script, "--input", src, "--output", out],
        capture_output=True, text=True, cwd=tmp, env=env,
    )
    return result, out


def squeezed(text):
    """`text` with every run of whitespace removed, for checking a mid-token wrap."""
    return re.sub(r"\s+", "", text)


class TheDiscoveriesStdlibWriterKeepsEveryTail(unittest.TestCase):
    """Code lines and table cells reach the page whole, on the path with no fpdf2."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.result, out = render_without_fpdf2(
            self.tmp.name, DISCOVERIES, DISCOVERIES_DOC, "discoveries.md")
        self.assertEqual(0, self.result.returncode, self.result.stderr)
        self.assertIn(SUCCESS_LINE, self.result.stdout)
        self.assertIn("renderer: stdlib", self.result.stdout,
                      "the fpdf shim did not take; this measures the wrong renderer")
        self.text = pdf_text(out)

    def test_a_long_table_cell_keeps_its_suffix(self):
        """`add(line[:max_width_chars])` cut the row; the cell's tail went with it."""
        self.assertIn(CELL_TAIL, self.text,
                      "the end of a long table cell is missing from the extracted text")

    def test_the_last_column_keeps_its_suffix(self):
        """The right-hand column is what a row-width clip eats first."""
        self.assertIn(COLUMN_TAIL, self.text)

    def test_a_table_wider_than_the_line_keeps_its_last_column(self):
        """Twelve columns do not fit at any column width, so the shrink loop gives up and
        the row used to meet `line[:max_width_chars]`. Every column past the budget was
        gone from the page, silently."""
        self.assertIn(WIDE_TAIL, self.text,
                      "the last column of a too-wide table is missing from the page")

    def test_a_long_code_line_keeps_its_tail(self):
        """`block.text[:92]` dropped the end of every long command (#674)."""
        self.assertIn(CODE_TAIL, self.text,
                      "the tail of a long code line is missing — a clipped command")

    def test_an_unbreakable_identifier_survives_being_wrapped(self):
        """Wrapping mid-token is fine; losing the tail is not. The difference is the point."""
        self.assertIn(squeezed(UNBROKEN), squeezed(self.text))
        self.assertNotIn(UNBROKEN, self.text,
                         "fixture no longer exercises the mid-token wrap — it fits the line")

    def test_nothing_is_reported_as_lost(self):
        """The content the layout could not place: none, and stderr says so by silence."""
        self.assertNotIn("did not reach the page in full", self.result.stderr)


class TheRecapStdlibWriterKeepsEveryTail(unittest.TestCase):
    """`_stdlib_table` wrapped nothing: it cut every cell at 40 characters."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.result, out = render_without_fpdf2(
            self.tmp.name, RECAP, RECAP_DOC, "bootcamp_recap.md")
        self.assertEqual(0, self.result.returncode, self.result.stderr)
        self.assertIn(SUCCESS_LINE, self.result.stdout)
        self.assertIn("renderer: stdlib", self.result.stdout,
                      "the fpdf shim did not take; this measures the wrong renderer")
        self.text = pdf_text(out)

    def test_a_long_table_cell_keeps_its_suffix(self):
        self.assertIn(RECAP_CELL_TAIL, self.text,
                      "the end of a long recap table cell is missing from the page")

    def test_the_last_column_keeps_its_suffix(self):
        self.assertIn(COLUMN_TAIL, self.text)

    def test_the_table_is_still_columns_and_not_pipe_source(self):
        """INV-142: the lesser rendering is aligned columns, never the Markdown source."""
        self.assertNotIn("|---|", self.text)
        self.assertIn("Match key", self.text)

    def test_nothing_is_reported_as_lost(self):
        self.assertNotIn("did not reach the page in full", self.result.stderr)


class TheMonospaceLayoutLosesNothing(unittest.TestCase):
    """The shared layout, measured directly — three clipping copies became one function."""

    def setUp(self):
        self.mod = load("recap_tails", RECAP)
        self.mod.reset_content_losses()
        self.addCleanup(self.mod.reset_content_losses)

    def joined(self, lines):
        return squeezed("".join(lines))

    def test_every_cell_survives_the_column_layout(self):
        """Word by word, because the columns interleave: a cell's second line sits on the
        page under its own column, with its neighbors' text between. Containment of the
        whole cell is the wrong assertion for a grid; containment of every word is not."""
        header = ["Requirement", "Answer", "Where"]
        rows = [["Which customers appear in both sources, and which do not?",
                 "a long answer that runs well past any column cap and ends at " + CELL_TAIL,
                 "Merges and match keys " + COLUMN_TAIL]]
        lines = self.mod.monospace_table_lines(header, rows, 87)
        page = " ".join(lines)
        for cell in header + rows[0]:
            for word in cell.split():
                with self.subTest(word=word):
                    self.assertIn(word, page)
        self.assertIsNone(self.mod.content_loss_warning())

    def test_a_table_too_wide_for_columns_becomes_records_rather_than_a_cut_row(self):
        """Twelve columns cannot be squeezed into one line. The old code cut the row."""
        header = ["Column %d" % i for i in range(12)]
        rows = [["value_%d_ending_in_%s_%d" % (i, CELL_TAIL, i) for i in range(12)]]
        lines = self.mod.monospace_table_lines(header, rows, 87)
        page = self.joined(lines)
        for cell in header + rows[0]:
            with self.subTest(cell=cell):
                # The record layout puts each value on its own lines, so the whole cell
                # IS contiguous here — unlike the column layout above.
                self.assertIn(squeezed(cell), page)
        self.assertTrue(
            all(len(line) <= 87 for line in lines),
            "a record line ran past the page's character budget")
        self.assertIsNone(self.mod.content_loss_warning())

    def test_no_line_exceeds_the_budget_it_was_given(self):
        """Wrapping without a budget is the off-page failure INV-121 names, not a fix."""
        header = ["A", "B"]
        rows = [["x" * 300, "y" * 300]]
        lines = self.mod.monospace_table_lines(header, rows, 60)
        self.assertTrue(all(len(line) <= 60 for line in lines), max(lines, key=len))

    def test_a_header_with_no_rows_still_renders_its_column_names(self):
        lines = self.mod.monospace_table_lines(["Alpha", "Beta"], [], 40)
        self.assertIn("Alpha", "".join(lines))
        self.assertIn("Beta", "".join(lines))


class TheVerbatimWrapKeepsEveryCharacter(unittest.TestCase):
    """`_wrap` is for prose; code needs its indentation and its every character."""

    def setUp(self):
        self.mod = load("recap_tails_wrap", RECAP)

    def test_the_chunks_rejoin_into_the_original(self):
        """The join identity is what proves no tail was lost — asserted, not assumed."""
        for text in (
            "    indented = {'key': 'value', 'other': 'value'}  # a trailing comment",
            UNBROKEN,
            "python3 generate_recap_pdf.py --input docs/bootcamp_recap.md --output out.pdf",
            " " * 12,
            "short",
        ):
            with self.subTest(text=text[:30]):
                self.assertEqual(text, "".join(self.mod._wrap_verbatim(text, 20)))

    def test_leading_indentation_is_kept(self):
        """`_wrap` eats it: `"    foo".split(" ")` opens with four empty strings."""
        self.assertTrue(self.mod._wrap_verbatim("    nested()", 40)[0].startswith("    "))
        self.assertFalse(self.mod._wrap("    nested()", 40)[0].startswith("    "))

    def test_no_chunk_exceeds_the_width(self):
        chunks = self.mod._wrap_verbatim(UNBROKEN + " " + UNBROKEN, 25)
        self.assertTrue(all(len(c) <= 25 for c in chunks), max(chunks, key=len))

    def test_an_empty_line_stays_one_line(self):
        self.assertEqual([""], self.mod._wrap_verbatim("", 20))


class TheRichRenderersMonospaceFallbackWraps(unittest.TestCase):
    """`_render_table_monospace` is reached from the fpdf2 path, and clipped too."""

    @requires_fpdf2
    def test_a_long_cell_keeps_its_tail(self):
        from fpdf import FPDF

        mod = load("recap_tails_mono", RECAP)
        mod.reset_content_losses()
        self.addCleanup(mod.reset_content_losses)
        pdf = FPDF(format="A4")
        pdf.add_page()
        pdf.set_font("Helvetica", "", 10.5)
        epw = pdf.w - 2 * pdf.l_margin
        header = ["Match key", "What it means", "Count"]
        rows = [["+NAME+ADDRESS",
                 "both records agree on the name and the address, which ends at "
                 + RECAP_CELL_TAIL,
                 "12 " + COLUMN_TAIL]]
        mod._render_table_monospace(pdf, epw, header, rows)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "mono.pdf")
            pdf.output(out)
            text = pdf_text(out)
        self.assertIn(RECAP_CELL_TAIL, text)
        self.assertIn(COLUMN_TAIL, text)
        self.assertIsNone(mod.content_loss_warning())


class LossThatCannotBeAvoidedIsReportedBeforeSuccess(unittest.TestCase):
    """The second half of the issue: whatever is still dropped must not be silent."""

    def setUp(self):
        self.mod = load("recap_tails_loss", RECAP)
        self.mod.reset_content_losses()
        self.addCleanup(self.mod.reset_content_losses)

    def test_silence_means_nothing_was_lost(self):
        self.assertIsNone(self.mod.content_loss_warning())

    def test_a_recorded_loss_names_the_site_and_the_text(self):
        self.mod.record_content_loss("table cell", "the part that vanished")
        warning = self.mod.content_loss_warning()
        self.assertIsNotNone(warning)
        self.assertIn("table cell", warning)
        self.assertIn("the part that vanished", warning)
        self.assertTrue(warning.startswith("WARNING:"))

    def test_the_warning_says_the_retention_figure_overstates_the_page(self):
        """Without that sentence the two numbers read as agreeing. They do not."""
        self.mod.record_content_loss("table cell", "gone")
        self.assertIn("OVERSTATES", self.mod.content_loss_warning())

    def test_the_warning_is_ascii_so_a_legacy_console_can_print_it(self):
        self.mod.record_content_loss("table cell", "李明 and the rest")
        warning = self.mod.content_loss_warning()
        warning.encode("ascii")  # raises if it is not

    def test_the_same_loss_twice_is_reported_once(self):
        """Both renderers walk the same document; one defect is one line, not two."""
        self.mod.record_content_loss("table cell", "gone")
        self.mod.record_content_loss("table cell", "gone")
        self.assertIn("1 passage(s)", self.mod.content_loss_warning())

    def test_account_emitted_passes_a_faithful_wrap(self):
        self.mod.account_emitted("cell", "one two three", ["one two", "three"])
        self.assertIsNone(self.mod.content_loss_warning())

    def test_account_emitted_reports_the_tail_a_clip_removed(self):
        self.mod.account_emitted("cell", "one two three", ["one two"])
        self.assertIn("three", self.mod.content_loss_warning())

    def test_a_row_with_more_cells_than_the_header_is_reported_not_swallowed(self):
        """`parse_table` truncates it — correctly; the grid has no column for it."""
        header, rows = self.mod.parse_table(
            "| A | B |\n|---|---|\n| one | two | ORPHANED_THIRD |")
        self.assertEqual([["one", "two"]], rows)
        self.assertIn("ORPHANED_THIRD", self.mod.content_loss_warning())

    def test_the_warning_is_written_before_the_success_line(self):
        """A reader who stops at `PDF generated:` must already have seen the warning."""
        source = inspect.getsource(self.mod.main)
        self.assertLess(
            source.index("content_loss_warning()"),
            source.index('f"PDF generated:'),
            "the loss warning must be written before the success line, or it reads as "
            "noise after a clean result")

    def test_graduation_is_still_non_blocking_when_content_is_lost(self):
        """INV-048/INV-052: say what is missing, still ship the PDF, still exit 0."""
        with tempfile.TemporaryDirectory() as tmp:
            result, out = render_without_fpdf2(
                tmp, RECAP, RAGGED_RECAP_DOC, "bootcamp_recap.md")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(SUCCESS_LINE, result.stdout)
            self.assertIn("ORPHANED_FOURTH_CELL", result.stderr)
            self.assertIn("did not reach the page in full", result.stderr)
            self.assertTrue(os.path.getsize(out) > 0, "the PDF must still be written")


class TheClippingIdiomsAreGone(unittest.TestCase):
    """A guard against the fix being undone one convenient slice at a time.

    Line-scoped by design (#674): the corpus is Python source, not Markdown prose, and each
    forbidden idiom is a single expression that cannot wrap. The read is per line precisely
    so a line that is CODE can be told from a line that is a COMMENT recording what was
    removed — collapsing whitespace first would merge the two and make the guard unable to
    allow its own explanatory comments.
    """

    #: The exact expressions #674 removed. Each one re-introduces a silent tail loss that
    #: no success signal in either generator can see.
    FORBIDDEN = (
        "block.text[:max_width_chars]",
        "line[:max_width_chars]",
        "rule[:max_width_chars]",
        "line[:budget]",
        "c[:w].ljust(w)",
    )

    def test_neither_generator_clips_content_to_a_width(self):
        for path in (RECAP, DISCOVERIES):
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            for idiom in self.FORBIDDEN:
                with self.subTest(script=os.path.basename(path), idiom=idiom):
                    # Allowed inside a comment that records what was removed; the point is
                    # that it is not CODE. Lines whose first non-space character is `#`
                    # are the history, not the behavior.
                    live = [
                        line for line in text.splitlines()
                        if idiom in line and not line.lstrip().startswith("#")
                    ]
                    self.assertEqual(
                        [], live,
                        "%s clips content to a width again: %s" % (
                            os.path.basename(path), live))


if __name__ == "__main__":
    unittest.main()
