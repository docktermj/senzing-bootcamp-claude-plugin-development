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

#788 carried the rule to the rest of the bundled generators. The recap PDF's rich renderer cut
its contents rows and page headings with `_clip` and the recap video capped its cards' lines,
both at exit 0 with nothing on stderr. The contents rows and headings now wrap; the fixed-
geometry sites (the cover's module chips, the certificate's name and module list, and the
video's title card, certificate citation and closing card) keep their caps and record what
they cut. `EveryGeneratorRecordsWhatItClips` scans every `scripts/generate_*.py` for an
unrecorded clip, and `EveryFixedGeometrySiteReports*` render overlong fields and read the
report, each with a negative control.

Run:  python3 -m unittest discover -s tests
"""
import ast
import glob
import importlib.util
import inspect
import json
import os
import re
import shutil
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
VIDEO = os.path.join(SCRIPTS, "generate_recap_video.py")

#: Every bundled generator INV-408 binds, found rather than listed, so a new one is guarded
#: the day it lands (#788).
GENERATORS = sorted(glob.glob(os.path.join(SCRIPTS, "generate_*.py")))

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
    allow its own explanatory comments. Widened to every bundled generator by #788.
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

    def test_no_generator_clips_content_to_a_width(self):
        for path in GENERATORS:
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


# --------------------------------------------------------------------------- #
# #788: no generator clips without recording what it cut
# --------------------------------------------------------------------------- #
#: Calls that record a loss: a hit inside a function that makes one is a REPORTED clip.
RECORDERS = ("record_content_loss", "account_emitted")
#: The wrap helpers whose output a slice would cut (`wrap_text(...)[:3]`).
WRAPPERS = ("wrap_text", "_wrap_to_width")
#: A name holding wrapped lines (`lines`, `title_lines`), whose head slice drops the rest.
LINES_NAME = re.compile(r"\w*lines")


def _called(node):
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _head_slice(node):
    """`x[:n]` — a slice that keeps a head and drops whatever follows it."""
    cut = node.slice
    return (isinstance(cut, ast.Slice) and cut.lower is None and cut.upper is not None
            and cut.step is None)


def _records(func):
    return func is not None and any(
        isinstance(n, ast.Call) and _called(n) in RECORDERS for n in ast.walk(func))


def unrecorded_clips(source):
    """(line, idiom, function) for every clipping idiom in a function that records no loss.

    The idioms #788 names: a `_clip(` call, a head slice of wrapped output, and a head slice
    of a `lines` list. Read from the syntax tree, so a docstring or comment that NAMES an
    idiom is not a hit, and an idiom split over several lines still is. A hit is allowed only
    inside a function that also calls `record_content_loss` or `account_emitted`: that is
    the function reporting what its clip cut, which INV-408 permits at fixed geometry.
    """
    hits = []

    def visit(node, func):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(child, child)
                continue
            idiom = None
            if isinstance(child, ast.Call) and _called(child) == "_clip":
                idiom = "_clip("
            elif isinstance(child, ast.Subscript) and _head_slice(child):
                value = child.value
                if isinstance(value, ast.Call) and _called(value) in WRAPPERS:
                    idiom = "%s(...)[:" % _called(value)
                elif isinstance(value, ast.Name) and LINES_NAME.fullmatch(value.id):
                    idiom = "%s[:N]" % value.id
            if idiom and not _records(func):
                hits.append((child.lineno, idiom, func.name if func else "<module>"))
            visit(child, func)

    visit(ast.parse(source), None)
    return hits


#: Each idiom #788 forbids, in a function that records nothing. Appended to a copy of a
#: generator, every one of them must be reported.
UNRECORDED_PROBE = """

def _probe_788(font, text, pdf):
    label = _clip(text, 46)
    title = wrap_text(font, text, 1500)[:3]
    names = _wrap_to_width(text, 100.0, len)[:2]
    lines = text.split()
    kept = lines[:MAX_LINES]
    return label, title, names, kept
"""

#: The same idioms in a function that records its loss: allowed.
RECORDED_PROBE = UNRECORDED_PROBE.replace(
    "_probe_788", "_probe_788_recorded").replace(
    "    return label", "    record_content_loss('probe', text)\n    return label")


class EveryGeneratorRecordsWhatItClips(unittest.TestCase):
    """INV-408 at every bundled generator: a clip either wraps, or records what it cut."""

    def test_the_generators_are_found(self):
        """Four ship today; a glob that finds fewer has stopped looking where they are."""
        names = {os.path.basename(path) for path in GENERATORS}
        for expected in ("generate_recap_pdf.py", "generate_discoveries_pdf.py",
                         "generate_document_pdf.py", "generate_recap_video.py"):
            self.assertIn(expected, names)

    def test_no_shipped_generator_clips_without_recording(self):
        for path in GENERATORS:
            with open(path, encoding="utf-8") as handle:
                hits = unrecorded_clips(handle.read())
            with self.subTest(script=os.path.basename(path)):
                self.assertEqual(
                    [], hits,
                    "%s clips content in a function that records no loss (INV-408): "
                    "wrap it, or call record_content_loss with the site and the text cut"
                    % os.path.basename(path))

    def test_an_inserted_unrecorded_clip_is_caught_in_every_generator(self):
        """Negative control: each idiom, added to a copy of each generator, is reported."""
        for path in GENERATORS:
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            with self.subTest(script=os.path.basename(path)):
                hits = unrecorded_clips(source + UNRECORDED_PROBE)
                self.assertEqual(
                    ["_clip(", "wrap_text(...)[:", "_wrap_to_width(...)[:", "lines[:N]"],
                    [idiom for _line, idiom, func in hits if func == "_probe_788"])

    def test_a_clip_in_a_function_that_records_its_loss_is_allowed(self):
        with open(GENERATORS[0], encoding="utf-8") as handle:
            source = handle.read()
        self.assertEqual([], unrecorded_clips(source + RECORDED_PROBE))

    def test_a_docstring_naming_an_idiom_is_not_a_hit(self):
        self.assertEqual([], unrecorded_clips(
            'def f():\n    """Every call site was `_clip(_safe(x), n)`; lines[:3]."""\n'))


def load_mutated(name, path, replace=(), append=""):
    """`path` as a fresh module, with each (old, new) in `replace` applied to its source.

    Compiled under the generator's own file name, so it finds its sibling helpers exactly as
    the shipped file does. Each `old` must occur, or the mutation would test nothing.
    """
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    for old, new in replace:
        if old not in source:
            raise AssertionError("mutation target not found in %s: %r" % (path, old))
        source = source.replace(old, new)
    module = type(sys)(name)
    module.__file__ = path
    sys.modules[name] = module
    exec(compile(source + append, path, "exec"), module.__dict__)
    return module


# --------------------------------------------------------------------------- #
# The recap PDF's fixed-geometry sites (#788)
# --------------------------------------------------------------------------- #
#: Longer than the cover chip's 46 characters; every other title fits a chip.
LONG_CHIP_TITLE = "Data Quality, Mapping, and Transformation for the CHIP_TAIL_788"
#: One unbreakable word, past what the certificate's shrink floor fits on the card.
OVERLONG_NAME = "W" * 120
#: Enough module titles that the certificate's list cannot fit three lines at 7 pt.
LIST_TITLES = ["Module title number %02d padded out to the chip" % i for i in range(1, 25)]

#: Each fixed-geometry site in the recap PDF, and the record call that reports it.
PDF_SITES = {
    "cover module chip": 'record_content_loss("cover module chip"',
    "certificate name": "record_content_loss(_CERT_CLIP_SITES.get(key",
    "certificate module list": 'record_content_loss("certificate module list"',
}

NO_RECORD = "\n\ndef _no_record_788(*_args, **_kwargs):\n    return None\n"


def overlong_recap_source():
    modules = "".join(
        "\n## %s — 2026-07-20T10:00:00-05:00\n\n### Information Shared\n\n- A line.\n"
        "\n### Questions & Responses\n\n- **Q:** Ready? **R:** Yes\n"
        "\n### Actions Taken\n\n- Did it.\n"
        "\n### End-of-Module Summary\n\n**What you accomplished:** It.\n\n"
        "**Files produced:**\n- `x.md` — it\n\n**Why it matters:** It.\n" % title
        for title in [LONG_CHIP_TITLE] + LIST_TITLES)
    return ("# Senzing Bootcamp Recap\n\n**Bootcamper:** %s\n**Started:** 2026-07-20\n"
            % OVERLONG_NAME) + modules


def fpdf2_losses(module):
    """Render the overlong recap with `module`'s fpdf2 renderer; return its loss warning."""
    module.reset_content_losses()
    recap = module.parse_recap(overlong_recap_source())
    with tempfile.TemporaryDirectory() as tmp:
        ok = module.render_with_fpdf2(recap, module.Path(os.path.join(tmp, "out.pdf")))
    assert ok, "the fpdf2 renderer refused the fixture"
    warning = module.content_loss_warning() or ""
    module.reset_content_losses()
    return warning


class EveryFixedGeometrySiteReportsInTheRecapPdf(unittest.TestCase):
    """Overlong fields at each fixed-geometry site are reported, at exit 0 (INV-408)."""

    @requires_fpdf2
    def test_the_cli_names_every_site_before_success_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "bootcamp_recap.md")
            out = os.path.join(tmp, "out.pdf")
            with open(src, "w", encoding="utf-8") as handle:
                handle.write(overlong_recap_source())
            result = subprocess.run(
                [sys.executable, RECAP, "--input", src, "--output", out],
                capture_output=True, text=True, cwd=tmp)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("renderer: fpdf2", result.stdout)
            self.assertTrue(os.path.getsize(out) > 0, "the PDF must still be written")
        warnings = [line for line in result.stderr.splitlines()
                    if "did not reach the page in full" in line]
        self.assertEqual(1, len(warnings), "one aggregated WARNING line: %s" % result.stderr)
        self.assertTrue(warnings[0].startswith("WARNING: 3 passage(s)"), warnings[0])
        for site, excerpt in (("cover module chip", "CHIP_TAIL_788"),
                              ("certificate name", "WWWW"),
                              ("certificate module list", "Module title number")):
            with self.subTest(site=site):
                self.assertRegex(warnings[0], re.escape(site) + ": [^;]*" + excerpt)

    @requires_fpdf2
    def test_removing_any_one_record_call_silences_its_site(self):
        """Negative control: the fixture above fails when one site stops recording."""
        self.assertEqual(set(PDF_SITES), {
            site for site in PDF_SITES
            if site + ":" in fpdf2_losses(load_mutated("recap_788_whole", RECAP))})
        for site, call in PDF_SITES.items():
            with self.subTest(site=site):
                mutated = load_mutated(
                    "recap_788_" + site.replace(" ", "_"), RECAP,
                    replace=[(call, call.replace("record_content_loss", "_no_record_788"))],
                    append=NO_RECORD)
                warning = fpdf2_losses(mutated)
                self.assertNotIn(site + ":", warning)
                for other in set(PDF_SITES) - {site}:
                    self.assertIn(other + ":", warning)

    def test_the_certificate_module_list_reports_in_the_stdlib_layout_too(self):
        """`_cert_module_layout` is shared by both renderers (INV-066), so its report is."""
        module = load("recap_788_layout", RECAP)
        module.reset_content_losses()
        self.addCleanup(module.reset_content_losses)
        lines, _size = module._cert_module_layout(LIST_TITLES, lambda s, pt: len(s) * pt)
        self.assertEqual(module._CERT_MODULE_LINES, len(lines))
        self.assertTrue(lines[-1].endswith(" ..."), "the truncation stays last and visible")
        self.assertIn("certificate module list: ", module.content_loss_warning() or "")

    def test_a_list_that_fits_records_nothing(self):
        module = load("recap_788_fits", RECAP)
        module.reset_content_losses()
        self.addCleanup(module.reset_content_losses)
        module._cert_module_layout(["Concepts", "Data collection"], lambda s, pt: len(s))
        self.assertIsNone(module.content_loss_warning())


class TheRecapPdfWrapsItsContentsAndHeadings(unittest.TestCase):
    """The contents rows and the page headings have room to grow, so they wrap (#788)."""

    @requires_fpdf2
    def test_every_word_of_a_long_title_reaches_the_contents_and_its_page(self):
        module = load("recap_788_wrap", RECAP)
        module.reset_content_losses()
        self.addCleanup(module.reset_content_losses)
        tails = {"module": "MODULE_HEADING_TAIL_788", "notes": "NOTES_TITLE_TAIL_788",
                 "handover": "HANDOVER_TITLE_TAIL_788"}
        long_text = ("a title long enough to run well past the width of the page heading "
                     "and of the contents column ")
        source = overlong_recap_source().replace(
            LONG_CHIP_TITLE, "Module 1: " + long_text + tails["module"], 1)
        recap = module.parse_recap(source)
        recap.notes = module.NotesSection(
            title=long_text + tails["notes"],
            entries=[module.NoteEntry(title="One note", body=["Written by me."])])
        recap.handover = module.HandoverSection(
            title=long_text + tails["handover"],
            parts=[("Decisions you made", ["- Kept the defaults."])])
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.pdf")
            self.assertTrue(module.render_with_fpdf2(recap, module.Path(out)))
            text = pdf_text(out)
        for what, tail in tails.items():
            with self.subTest(title=what):
                # Once in the contents, once in the page's own heading.
                self.assertGreaterEqual(text.count(tail), 2, "%s title was cut" % what)
        warning = module.content_loss_warning() or ""
        for site in ("contents row", "page heading"):
            self.assertNotIn(site + ":", warning, "a wrapped site lost text: " + warning)

    def test_no_contents_row_or_page_heading_calls_clip(self):
        with open(RECAP, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        for func in ast.walk(tree):
            if isinstance(func, ast.FunctionDef) and func.name in (
                    "_render_toc", "_render_toc_row", "_render_title_band",
                    "_render_module_page", "_render_notes_page", "_render_handover_page"):
                with self.subTest(function=func.name):
                    self.assertNotIn("_clip", {
                        _called(n) for n in ast.walk(func) if isinstance(n, ast.Call)})


# --------------------------------------------------------------------------- #
# The recap video's fixed-geometry sites (#788)
# --------------------------------------------------------------------------- #
class StubFont:
    """Every character `factor` x the size wide, so the layout is the same on any machine."""

    def __init__(self, size, factor=0.6):
        self.size, self.factor = size, factor

    def getlength(self, text):
        return len(text) * self.size * self.factor


class StubContext:
    def font(self, _style, size):
        return StubFont(size)


#: Each video site, and the call that caps it and records what the cap drops.
VIDEO_SITES = {
    "title card module": '_cap_lines("title card module"',
    "title card highlight": '_cap_lines("title card highlight"',
    "certificate citation": '_cap_lines("certificate citation"',
    "closing card": '_cap_lines("closing card"',
}

UNRECORDED_CAP = ("\n\ndef _cap_unrecorded_788(where, lines, cap):\n"
                  "    return list(lines)[:cap]\n")

OVERLONG_MODULE = " ".join(["Mapping"] * 40) + " MODULE_TAIL_788"
OVERLONG_HIGHLIGHT = " ".join(["highlight"] * 60) + " HIGHLIGHT_TAIL_788"
OVERLONG_CITATION = " ".join(["citation"] * 80) + " CITATION_TAIL_788"
OVERLONG_BOOTCAMPER = " ".join(["Bartholomew-Montgomery"] * 12) + " NAME_TAIL_788"


def video_losses(module):
    """Lay out every capped card with overlong fields; return the video's loss warning."""
    module.reset_content_losses()
    ctx = StubContext()
    module.title_card_lines(ctx.font("bold", 96), ctx.font("regular", 48),
                            OVERLONG_MODULE, OVERLONG_HIGHLIGHT)
    module.certificate_citation_lines(ctx, OVERLONG_CITATION)
    module.tag_line_layout(ctx, "Resolved: %s, Senzing Bootcamp graduate." % OVERLONG_BOOTCAMPER)
    warning = module.content_loss_warning() or ""
    module.reset_content_losses()
    return warning


class EveryFixedGeometrySiteReportsInTheRecapVideo(unittest.TestCase):
    """The video's cards keep their caps, and say what the caps dropped (INV-408)."""

    def test_every_site_is_named_with_the_text_it_dropped(self):
        warning = video_losses(load_mutated("video_788_whole", VIDEO))
        self.assertTrue(warning.startswith("WARNING: 4 passage(s) did not reach the video in "
                                           "full"), warning)
        self.assertEqual(1, len(warning.strip().splitlines()), "one aggregated line")
        warning.encode("ascii")
        for site, tail in (("title card module", "Mapping"),
                           ("title card highlight", "highlight"),
                           ("certificate citation", "citation"),
                           ("closing card", "Bartholomew")):
            with self.subTest(site=site):
                self.assertRegex(warning, re.escape(site) + ": [^;]*" + tail)

    def test_removing_any_one_record_call_silences_its_site(self):
        """Negative control: the fixture above fails when one site stops recording."""
        for site, call in VIDEO_SITES.items():
            with self.subTest(site=site):
                mutated = load_mutated(
                    "video_788_" + site.replace(" ", "_"), VIDEO,
                    replace=[(call, call.replace("_cap_lines", "_cap_unrecorded_788"))],
                    append=UNRECORDED_CAP)
                warning = video_losses(mutated)
                self.assertNotIn(site + ":", warning)
                for other in set(VIDEO_SITES) - {site}:
                    self.assertIn(other + ":", warning)

    def test_fields_that_fit_record_nothing(self):
        module = load_mutated("video_788_fits", VIDEO)
        ctx = StubContext()
        module.reset_content_losses()
        module.title_card_lines(ctx.font("bold", 96), ctx.font("regular", 48),
                                "Business Problem", "Three sources, one customer view")
        module.certificate_citation_lines(ctx, "for completing the Senzing Bootcamp.")
        module.tag_line_layout(ctx, "Resolved: Ada Lovelace, Senzing Bootcamp graduate.")
        self.assertIsNone(module.content_loss_warning())

    def test_the_warning_is_written_before_the_success_line(self):
        with open(VIDEO, encoding="utf-8") as handle:
            source = handle.read()
        main = source[source.index("\ndef main("):]
        self.assertLess(main.index("content_loss_warning()"),
                        main.index('print(f"Video generated:'))

    def test_the_warning_has_the_recap_pdfs_shape(self):
        """The same aggregated line: count, sites as `site: excerpt` joined by `; `."""
        video = load_mutated("video_788_shape", VIDEO)
        pdf = load("recap_788_shape", RECAP)
        for module in (video, pdf):
            module.reset_content_losses()
            for i in range(6):
                module.record_content_loss("site %d" % i, "lost text %d" % i)
            warning = module.content_loss_warning()
            module.reset_content_losses()
            with self.subTest(module=module.__name__):
                self.assertRegex(
                    warning,
                    r"^WARNING: 6 passage\(s\) did not reach the (page|video) in full\. "
                    r"The text below was laid out but part of it was not (emitted|drawn): "
                    r"site 0: lost text 0; site 1: lost text 1; site 2: lost text 2; "
                    r"site 3: lost text 3; and 2 more\. ")


@unittest.skipUnless(
    importlib.util.find_spec("PIL") is not None
    and (shutil.which("ffmpeg") or importlib.util.find_spec("imageio_ffmpeg") is not None),
    "Pillow or ffmpeg is missing; an end-to-end video render needs both "
    "(python3 -m pip install -r requirements-dev.txt)")
class TheVideoCliReportsBeforeSuccess(unittest.TestCase):
    """End to end: overlong storyboard fields, one WARNING line, the video still written."""

    def test_overlong_cards_are_reported_and_the_video_is_written(self):
        board = {
            "video": {"bootcamper": OVERLONG_BOOTCAMPER, "graduation_date": "2026-09-30",
                      "music": False},
            "scenes": [
                {"type": "title_card", "duration": 1, "narration": "Hi.",
                 "module": OVERLONG_MODULE, "highlight": OVERLONG_HIGHLIGHT},
                {"type": "tag_line", "duration": 1, "narration": "Resolved."},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "docs", "video", "storyboard.json")
            os.makedirs(os.path.dirname(path))
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(board, handle)
            out = os.path.join(tmp, "docs", "bootcamp_recap.mp4")
            result = subprocess.run(
                [sys.executable, VIDEO, "--storyboard", path, "--output", out,
                 "--project-root", tmp, "--no-voice"],
                capture_output=True, text=True, cwd=tmp, timeout=600)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Video generated:", result.stdout)
            self.assertTrue(os.path.getsize(out) > 0)
        warnings = [line for line in result.stderr.splitlines()
                    if "did not reach the video in full" in line]
        self.assertEqual(1, len(warnings), result.stderr)
        self.assertTrue(warnings[0].startswith("WARNING: "), warnings[0])
        for site in ("title card module", "title card highlight", "closing card"):
            with self.subTest(site=site):
                self.assertIn(site + ": ", warnings[0])


if __name__ == "__main__":
    unittest.main()
