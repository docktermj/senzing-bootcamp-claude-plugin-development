"""Tests for the data-discoveries PDF generator and its wiring.

`docs/bootcamp_data_discoveries.md` + `.pdf` are the payoff for every preceding
module, and they used to exist only if the bootcamper opted into the Discover
tutorial. `generate_discoveries_pdf.py` is the sibling renderer that produces the
PDF; these tests pin both halves of the fix:

* The renderer honors the same two-outcome contract as the recap generator
  (INV-110): an imperfect document renders, a document it cannot meaningfully
  parse does not — no PDF, no success line, non-zero exit. Pointing it at a
  recap-shaped document is the concrete case that motivated it.
* The stdlib fallback produces a genuinely valid PDF carrying the findings. The
  reporting bootcamper had no PDF dependency installed at all, so that path is
  the common case, not an edge case — and a `PDF generated:` line is not
  evidence, so the text is extracted and searched.
* The module skill produces the deliverable on every branch of the Discover
  opt-in, at the convergence point all four branches return to.

Enforces **INV-121** (no full-width write in a bundled generator depends on the ambient
cursor position, verified positionally rather than by text extraction), which names this
file as its enforcer. INV-121's coverage here is path-scoped by design -- see its note.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPT = os.path.join(PLUGIN, "scripts", "generate_discoveries_pdf.py")
MODULE7 = os.path.join(PLUGIN, "skills", "module-07-query-visualize-discover")
PHASE1 = os.path.join(MODULE7, "phase1-query-visualize.md")
WRAPPER = os.path.join(PLUGIN, "scripts", "generate_document_pdf.py")
GRADUATION = os.path.join(PLUGIN, "skills", "graduation", "SKILL.md")
PHASE2 = os.path.join(MODULE7, "phase2-discover.md")

SUCCESS_LINE = "PDF generated:"

GOOD_DOC = """# Data Discoveries

**Bootcamper:** Ada Lovelace
**Sources:** ENFORMION, EQUIFAX

## Headline numbers, interpreted

- **Records loaded:** 4,012 across two sources, which is the full mapped set
- **Resolved entities:** 3,864 — a 3.7% collapse, modest and expected at this overlap

## Merges and match keys

Every merge below carries the match key that drove it, so each one is auditable.

| Entity | Match key | Sources |
|---|---|---|
| 1042 | +NAME+ADDRESS | ENFORMION, EQUIFAX |

## Review queue

Cross-source pairs awaiting one human decision each before they can be actioned.

- **Entity 2210 / 8891:** POSSIBLY_SAME on +NAME-REGISTRATION_DATE

## Why and how: worked examples

### A near miss worth reading

Entity 3301 did not merge with 3302 because the two addresses disagreed outright.

## Relationship networks

Multi-hop paths that no single record states on its own were found here.

## What was not found, and why

The two sources shared only 8 organization names, so 4 cross-source merges was
near the achievable ceiling. This is low overlap in the source data, not pipeline
underperformance, and the measurement above is what distinguishes the two.
"""

# A recap-shaped document: the concrete input that produced a near-empty PDF and
# exit 0 before this renderer existed.
RECAP_SHAPED = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace

## Data collection — 2026-07-21T09:00:00-05:00

### Information Shared

We talked through where the records were going to come from originally.

### Actions Taken

Collected two source extracts and registered them in the data source registry.
"""

NO_HEADINGS = "just some prose about the data\nand a second line of prose\n"

PARTIAL_DOC = """# Data Discoveries

## Headline numbers, interpreted

- Loaded 10 records and resolved 9 of them into distinct resolved entities today

## What was not found, and why

Low overlap between the two sources explains the small cross-source merge count.
"""


def run(args, cwd):
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def load_generator_module():
    """Import the generator so its renderers and dataclasses can be driven directly."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("discoveries_gen_shared", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves its module via sys.modules.
    sys.modules["discoveries_gen_shared"] = module
    spec.loader.exec_module(module)
    return module


def write_doc(directory, text, name="bootcamp_data_discoveries.md"):
    docs = os.path.join(directory, "docs")
    os.makedirs(docs, exist_ok=True)
    path = os.path.join(docs, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def _pdf_streams(path):
    """Every content stream in a PDF, decompressed where possible."""
    with open(path, "rb") as handle:
        raw = handle.read()
    chunks = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S):
        body = match.group(1)
        # `decompressobj` decodes the valid prefix and tolerates a slice whose tail
        # is off by a few bytes; strict `decompress` raises on that, which silently
        # hid a whole page of text and looked exactly like a lost module section.
        try:
            body = zlib.decompressobj().decompress(body)
        except zlib.error:
            pass
        chunks.append(body.decode("latin-1", "replace"))
    return chunks


def pdf_text(path):
    """Extract drawn text from a PDF, decompressing streams when needed.

    fpdf2 compresses its content streams, so a raw byte search reports a false
    negative — the mistake this helper exists to prevent.

    ⛔ Presence here is NOT proof the text is *visible*: a run positioned outside the
    page box is still in the content stream. Use `pdf_runs` for that — it is the only
    thing that catches off-page rendering.
    """
    joined = "\n".join(_pdf_streams(path))
    return "".join(re.findall(r"\((.*?)\)\s*Tj", joined))


# A4 portrait in PostScript points, the unit the content stream is written in.
A4_W_PT, A4_H_PT = 595.28, 841.89


def pdf_runs(path):
    """Every drawn text run as ``(x, y, text)`` in points, in document order.

    Positions are what distinguishes "rendered" from "present in the file". The
    off-page-table defect this guards put full, correct text into the stream at
    x ≈ 567 pt on a 595 pt page — `pdf_text` saw it, the reader did not.
    """
    runs = []
    # `Td` always follows its two operands. Keying off the operator rather than `BT`
    # handles both writers: fpdf2 emits `BT /F1 22 Tf ET  q BT x y Td (t) Tj ET Q`,
    # the stdlib fallback emits `BT /F1 10.5 Tf x y Td (t) Tj ET`.
    pattern = re.compile(r"([\d.]+)\s+([\d.]+)\s+Td\b(.*?)\bTj", re.S)
    for stream in _pdf_streams(path):
        for match in pattern.finditer(stream):
            body = re.findall(r"\((.*?)\)\s*$", match.group(3).strip())
            if body:
                runs.append((float(match.group(1)), float(match.group(2)), body[0]))
    return runs


def pdf_runs_with_font(path):
    """``(x, y, font, text)`` per drawn run — the font resource in force.

    Boldness is a *different font resource*, not an attribute, so this is what
    distinguishes a repeated table header from the body row beneath it. The
    regression it guards left the font bold after re-emitting a header across a
    page break, so the first data row on every continuation page rendered as a
    second header — a defect no text extraction and no retention figure can see.
    """
    runs = []
    font_op = re.compile(r"/(F\d+)\s+[\d.]+\s+Tf")
    run_op = re.compile(r"([\d.]+)\s+([\d.]+)\s+Td\b(.*?)\bTj", re.S)
    for stream in _pdf_streams(path):
        for match in re.finditer(r"/F\d+\s+[\d.]+\s+Tf|[\d.]+\s+[\d.]+\s+Td.*?Tj", stream, re.S):
            piece = match.group(0)
            font_match = font_op.fullmatch(piece)
            if font_match:
                current = font_match.group(1)
                continue
            run_match = run_op.match(piece)
            if not run_match:
                continue
            body = re.findall(r"\((.*?)\)\s*$", run_match.group(3).strip())
            if body:
                runs.append(
                    (float(run_match.group(1)), float(run_match.group(2)),
                     locals().get("current", "?"), body[0])
                )
    return runs


# Two adjacent tables, a ragged row, a table long enough to break across a page,
# consecutive paragraphs, and a soft-wrapped `**Label:**` line — every shape the
# table/spacing work has to get right, in one document.
TABLE_DOC = """# Data Discoveries

**Bootcamper:** Ada Lovelace

## Headline numbers, interpreted

First paragraph making a claim about the data that was loaded here today.

Second paragraph supplying the evidence, which must not run together with it.

| Measure | Value |
|---|---|
| Records loaded | 4,966 |

| Second table | Adjacent to the first |
|---|---|
| separated by | a blank line only |

**Cross-source overlap:** GLEIF and OPEN-OWNERSHIP produced the largest cluster,
and this continuation line must not be split from its label by a blank line.

## Merges and match keys

| Match key pattern | Count | Source |
|---|---|---|
""" + "\n".join(
    f"| +NAME+ADDRESS+ID{i:02d} | {1000 - i} | source-{i % 3} |" for i in range(1, 46)
) + """
| +RAGGED |
| +NAME+ADDRESS+EXTRA | 1 | source-0 | dropped |

## Review queue

Nothing awaiting review.

## Why and how: worked examples

Nothing to explain.

## Relationship networks

No multi-hop paths.

## What was not found, and why

Low overlap between the two sources explains the small cross-source merge count.
"""


class TestTablesRenderAsAGrid(unittest.TestCase):
    """Markdown tables are drawn, not printed as their source.

    The generator used to emit one block *per row* and print each row verbatim in
    a monospace font, by design — its docstring said so. 61 raw pipe lines reached
    the bootcamper's PDF, in the six passages carrying every quantitative finding
    in the document.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        write_doc(cls.tmp.name, TABLE_DOC)
        result = run([], cls.tmp.name)
        assert result.returncode == 0, result.stderr
        cls.pdf = os.path.join(cls.tmp.name, "docs", "bootcamp_data_discoveries.pdf")
        cls.runs = pdf_runs(cls.pdf)
        cls.typed = pdf_runs_with_font(cls.pdf)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_no_raw_pipe_source_survives(self):
        offenders = [t for _x, _y, t in self.runs if t.strip().startswith("|") or "|---" in t]
        self.assertEqual(
            [], offenders, f"raw Markdown table source drawn into the PDF: {offenders[:5]}"
        )

    @requires_fpdf2
    def test_cells_are_drawn_as_separate_runs(self):
        """A grid means one run per cell — not one run per source line."""
        texts = [t.strip() for _x, _y, t in self.runs]
        for cell in ("Measure", "Value", "Records loaded", "4,966"):
            with self.subTest(cell=cell):
                self.assertIn(cell, texts, f"{cell!r} is not its own drawn cell")

    def test_the_alignment_row_is_dropped(self):
        self.assertNotIn("---", [t.strip() for _x, _y, t in self.runs])

    @requires_fpdf2
    def test_a_ragged_row_does_not_desynchronize_the_grid(self):
        """Short and over-long rows are padded/truncated to the header width."""
        texts = [t.strip() for _x, _y, t in self.runs]
        self.assertIn("+RAGGED", texts, "the short row vanished")
        self.assertIn("+NAME+ADDRESS+EXTRA", texts, "the over-long row vanished")
        # The extra 4th cell has nowhere to go in a 3-column grid; dropping it is
        # correct, but it must not shift a neighboring row's cells along.
        xs = {t: x for x, _y, t in self.runs}
        self.assertAlmostEqual(
            xs["+NAME+ADDRESS+EXTRA"], xs["+NAME+ADDRESS+ID01"], delta=0.5,
            msg="a ragged row shifted the column origin",
        )

    @requires_fpdf2
    def test_two_adjacent_tables_are_visibly_separated(self):
        """Sharing an edge, two grids read as one table with a bold middle row."""
        y = {t.strip(): yy for _x, yy, t in self.runs}
        last_row_of_first = y["Records loaded"]
        header_of_second = y["Second table"]
        pitch = abs(y["Measure"] - y["Records loaded"])  # one row's height
        gap = abs(last_row_of_first - header_of_second)
        self.assertGreater(
            gap, pitch * 1.5,
            f"only {gap:.1f}pt between two tables against a {pitch:.1f}pt row pitch — "
            "they will read as a single grid",
        )

    @requires_fpdf2
    def test_a_repeated_header_leaves_the_body_row_unbolded(self):
        """The page-break regression: the row after a repeated header went bold."""
        headers = [r for r in self.typed if r[3].strip() == "Match key pattern"]
        self.assertGreaterEqual(len(headers), 2, "the table did not span a page break")
        header_font = headers[-1][2]
        after = [r for r in self.typed if r[1] < headers[-1][1] and r[3].startswith("+NAME")]
        self.assertTrue(after, "no body row followed the repeated header")
        self.assertNotEqual(
            header_font, after[0][2],
            f"the first body row after the repeated header uses the header font "
            f"({header_font}) — it will render as a second header",
        )


@requires_fpdf2
class TestParagraphsAreSeparated(unittest.TestCase):
    """Paragraph breaks are structure: the author used them to separate points."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        write_doc(cls.tmp.name, TABLE_DOC)
        result = run([], cls.tmp.name)
        assert result.returncode == 0, result.stderr
        cls.runs = pdf_runs(os.path.join(cls.tmp.name, "docs", "bootcamp_data_discoveries.pdf"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _y(self, needle):
        hits = [y for _x, y, t in self.runs if needle in t]
        self.assertTrue(hits, f"{needle!r} did not render")
        return hits[0]

    def _advance(self, top, bottom):
        return abs(self._y(top) - self._y(bottom))

    # Calibrated from the document itself rather than hardcoded: a plain line
    # advance measured ~15.6 pt and a paragraph break ~25.8 pt, but both move with
    # the font size and leading. Comparing the two distances keeps the assertion
    # meaningful after a type change; a fixed threshold would not.
    def test_consecutive_paragraphs_have_a_blank_line_between_them(self):
        paragraphs = self._advance(
            "First paragraph making a claim", "Second paragraph supplying the evidence"
        )
        line = self._advance("Cross-source overlap", "and this continuation line")
        self.assertGreater(
            paragraphs, line * 1.4,
            f"paragraph break ({paragraphs:.1f}pt) is barely more than a plain line "
            f"advance ({line:.1f}pt) — the paragraphs read as one wall of text",
        )

    def test_a_soft_wrapped_label_is_not_split_mid_sentence(self):
        """`**Label:** text` + continuation is ONE paragraph, not two.

        The parser emits the continuation as its own block, so gapping uniformly
        put a blank line into the middle of a sentence.
        """
        line = self._advance("Cross-source overlap", "and this continuation line")
        paragraphs = self._advance(
            "First paragraph making a claim", "Second paragraph supplying the evidence"
        )
        self.assertLess(
            line, paragraphs * 0.85,
            f"the label and its continuation are {line:.1f}pt apart, close to the "
            f"{paragraphs:.1f}pt paragraph break — a blank line was inserted "
            "mid-sentence",
        )


class TestRendersASoundDocument(unittest.TestCase):
    def test_renders_and_reports_retention(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, GOOD_DOC)
            result = run([], tmp)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(SUCCESS_LINE, result.stdout)
            self.assertIn("content retained:", result.stdout)
            self.assertTrue(
                os.path.exists(os.path.join(tmp, "docs", "bootcamp_data_discoveries.pdf"))
            )

    def test_check_mode_passes_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, GOOD_DOC)
            result = run(["--check"], tmp)
            self.assertEqual(0, result.returncode, result.stderr)
            # "findings" dropped 2026-07-31: the list is a parameter now, so the
            # count is against whatever was expected, not against six findings.
            self.assertIn("6/6 expected sections present", result.stdout)
            self.assertFalse(
                os.path.exists(os.path.join(tmp, "docs", "bootcamp_data_discoveries.pdf")),
                "--check must not write a PDF.",
            )

    def test_pdf_carries_the_findings(self):
        """A success line is not verification; the text must be in the PDF."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, GOOD_DOC)
            run([], tmp)
            text = pdf_text(os.path.join(tmp, "docs", "bootcamp_data_discoveries.pdf"))
            for probe in (
                "Data Discoveries",
                "What Senzing found in your data",
                "Headline numbers",
                "Review queue",
                "POSSIBLY_SAME",
                "achievable ceiling",
                "Relationship networks",
                # Table content. Its absence was invisible to this test for as long as
                # the probe list omitted it, while the whole table rendered off-page.
                "Match key",
                "+NAME+ADDRESS",
            ):
                with self.subTest(probe=probe):
                    self.assertIn(probe, text)


LAYOUT_DOC = """# Data Discoveries

**Bootcamper:** Ada Lovelace
**Sources:** ENFORMION, EQUIFAX
**Records:** 4,012 loaded across two sources with a 3.7% entity collapse observed

## Headline numbers, interpreted

- **Records loaded:** 4,012 across two sources, which is the full mapped set
- **Resolved entities:** 3,864 with a modest collapse that is expected at this overlap
- Plain trailing bullet with no bold label at all, closing the list

## Merges and match keys

| Match key pattern | Count | Sources |
|---|---|---|
| +NAME+ADDRESS | 118 | ENFORMION, EQUIFAX |

```text
verbatim code block that must also start at the left margin
```

## Review queue

- **ABC AUTOMOTIVE INVESTMENTS pair (entities 300099, 300054):** these two agree on name and city but disagree outright on registration date, so Senzing declined the merge.
- **Short:** stays inline beside its label.

## Why and how: worked examples

Entity 3301 did not merge with 3302 because the two addresses disagreed outright.

## Relationship networks

Multi-hop paths that no single record states on its own were found here.

## What was not found, and why

The two sources shared only 8 organization names, near the achievable ceiling.
"""


class TestEverythingRendersInsideThePage(unittest.TestCase):
    """fpdf2's `multi_cell` leaves the cursor at the right margin (`new_x=RIGHT`).

    A following full-width `multi_cell` that does not reset x draws from there across
    the full width — off-sheet, silently. The generator still exits 0 and still
    reports high content retention, because the text *is* in the content stream.
    Only position catches it.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        write_doc(self.tmp.name, LAYOUT_DOC)
        result = run([], self.tmp.name)
        self.assertEqual(0, result.returncode, result.stderr)
        self.pdf = os.path.join(self.tmp.name, "docs", "bootcamp_data_discoveries.pdf")
        self.runs = pdf_runs(self.pdf)
        self.assertTrue(self.runs, "no drawn text runs found")

    def test_no_text_starts_beyond_the_right_margin(self):
        """The direct detector for the off-page defect."""
        # fpdf2's default margin is 10 mm ≈ 28.35 pt; allow the full text column plus
        # a little slack, and fail on anything starting at or past the right margin.
        limit = A4_W_PT - 25.0
        offenders = [(x, y, t) for x, y, t in self.runs if x >= limit]
        self.assertEqual([], offenders, f"text drawn past x={limit:.0f}pt: {offenders[:5]}")

    def test_table_rows_render_in_the_text_column(self):
        rows = [r for r in self.runs if "NAME+ADDRESS" in r[2] or "Match key" in r[2]]
        self.assertTrue(rows, "the table did not render at all")
        for x, _y, text in rows:
            with self.subTest(text=text):
                self.assertLess(x, A4_W_PT / 2, "table row drawn outside the text column")

    def test_code_block_renders_in_the_text_column(self):
        block = [r for r in self.runs if "verbatim code block" in r[2]]
        self.assertTrue(block, "the code block did not render at all")
        self.assertLess(block[0][0], A4_W_PT / 2)

    @requires_fpdf2
    def test_cover_subtitle_renders_in_full_at_the_left_margin(self):
        subtitle = [r for r in self.runs if "What Senzing found" in r[2]]
        self.assertTrue(subtitle, "cover subtitle missing")
        x, _y, text = subtitle[0]
        self.assertEqual("What Senzing found in your data", text, "subtitle was truncated")
        self.assertLess(x, 40.0, "subtitle drawn away from the left margin")

    @requires_fpdf2
    def test_every_metadata_line_renders_in_the_text_column(self):
        """Only the first meta line was safe: `ln()` reset x, the loop never did."""
        for key in ("Bootcamper", "Sources", "Records"):
            hits = [r for r in self.runs if r[2].startswith(key)]
            with self.subTest(key=key):
                self.assertTrue(hits, f"meta line {key} missing")
                self.assertLess(hits[0][0], 40.0, f"meta line {key} drawn off-column")


class TestLabeledBulletsStayReadable(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        write_doc(self.tmp.name, LAYOUT_DOC)
        run([], self.tmp.name)
        self.runs = pdf_runs(
            os.path.join(self.tmp.name, "docs", "bootcamp_data_discoveries.pdf")
        )

    def _run_with(self, needle):
        hits = [r for r in self.runs if needle in r[2]]
        self.assertTrue(hits, f"{needle!r} not drawn")
        return hits[0]

    @requires_fpdf2
    def test_long_bold_label_breaks_to_its_own_line(self):
        label = self._run_with("ABC AUTOMOTIVE INVESTMENTS")
        body = self._run_with("these two agree on name")
        self.assertLess(body[1], label[1], "long-labeled body did not break to a new line")
        self.assertLess(body[0], A4_W_PT / 3, "body did not return to (near) the left margin")

    def test_short_label_keeps_its_body_inline(self):
        label = self._run_with("Short")
        body = self._run_with("stays inline")
        self.assertEqual(body[1], label[1], "short label should not break the line")


class TestListItemsAreSeparated(unittest.TestCase):
    """A wrapped bullet's continuation lines sat at the same spacing as the gap
    between two separate bullets, so multi-line items ran together."""

    def _bullet_baselines(self, runs):
        markers = [r for r in runs if r[2].strip() == "-"]
        return sorted({round(r[1], 2) for r in markers}, reverse=True)

    @requires_fpdf2
    def test_consecutive_bullets_are_further_apart_than_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, LAYOUT_DOC)
            run([], tmp)
            runs = pdf_runs(os.path.join(tmp, "docs", "bootcamp_data_discoveries.pdf"))
        baselines = self._bullet_baselines(runs)
        self.assertGreaterEqual(len(baselines), 3, "expected several bullets")
        # The three "Headline numbers" bullets are single-line, so consecutive markers
        # are one line (5.5 mm ≈ 15.6 pt) plus the new inter-item gap (2.4 mm ≈ 6.8 pt).
        gaps = [a - b for a, b in zip(baselines, baselines[1:])]
        same_list = [g for g in gaps if g < 40]  # exclude cross-section jumps
        self.assertTrue(same_list, "no within-list bullet gaps found")
        for gap in same_list:
            with self.subTest(gap=round(gap, 1)):
                self.assertGreater(gap, 17.0, "bullets are still only one line apart")

    def test_stdlib_renderer_also_separates_items(self):
        from pathlib import Path

        module = TestStdlibFallback.load_module(TestStdlibFallback())
        doc = module.parse_discoveries(LAYOUT_DOC)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stdlib.pdf"
            self.assertTrue(module.render_with_stdlib(doc, out))
            runs = pdf_runs(out)
        self.assertTrue(runs, "stdlib renderer drew nothing")
        # The stdlib path prefixes bullets into the wrapped text rather than drawing a
        # separate marker, so key off the item bodies instead.
        loaded = [r for r in runs if "Records loaded" in r[2]]
        resolved = [r for r in runs if "Resolved entities" in r[2]]
        self.assertTrue(loaded and resolved, "stdlib bullets missing")
        gap = loaded[0][1] - resolved[0][1]
        self.assertGreater(gap, 14.0, "stdlib items are still exactly one line apart")

    def test_no_gap_trails_the_last_item_of_a_list(self):
        """The gap is emitted only when the *next* block is also a list item."""
        module = TestStdlibFallback.load_module(TestStdlibFallback())
        blocks = module.parse_discoveries(LAYOUT_DOC).blocks
        indices = [i for i, b in enumerate(blocks) if b.kind in ("bullet", "subbullet")]
        self.assertTrue(indices)
        for i in indices:
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            expected = nxt is not None and nxt.kind in ("bullet", "subbullet")
            with self.subTest(index=i, kind=blocks[i].kind):
                self.assertEqual(expected, module._needs_item_gap(blocks, i))


class TestRefusesToShipAnEmptyDeliverable(unittest.TestCase):
    """INV-110: no success line and no file when content would be lost."""

    def assert_refused(self, tmp, doc_name="bootcamp_data_discoveries.md"):
        out_pdf = os.path.join(tmp, "docs", "out.pdf")
        result = run(
            ["--input", os.path.join("docs", doc_name), "--output", os.path.join("docs", "out.pdf")],
            tmp,
        )
        self.assertNotEqual(0, result.returncode, "must exit non-zero")
        self.assertNotIn(SUCCESS_LINE, result.stdout, "must print no success line")
        self.assertFalse(os.path.exists(out_pdf), "must write no PDF")
        return result

    def test_recap_shaped_document_is_refused(self):
        """Wording generalized 2026-07-31 ("required findings sections" -> "required
        sections") because the list is now a parameter: with `--require-sections` the
        expected headings are not findings at all, so the old phrase would be wrong for
        every document but one. The actionable half — naming what was looked for — is
        asserted here rather than the adjective."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, RECAP_SHAPED)
            result = self.assert_refused(tmp)
            self.assertIn("none of the required sections is present", result.stderr)
            self.assertIn("looked for:", result.stderr)
            self.assertIn("headline numbers", result.stderr)

    def test_document_without_headings_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, NO_HEADINGS)
            result = self.assert_refused(tmp)
            self.assertIn("no '## ' sections", result.stderr)

    def test_missing_input_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "docs"), exist_ok=True)
            result = run([], tmp)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Input not found", result.stderr)


class TestPartialDocumentStillRenders(unittest.TestCase):
    """Incomplete but recognizable: warn, render, exit 0 — never block."""

    def test_warns_and_renders(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, PARTIAL_DOC)
            result = run([], tmp)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(SUCCESS_LINE, result.stdout)
            # Generalized with the flag (2026-07-31); the named sections are the point.
            self.assertIn("missing sections", result.stderr)


class TestStdlibFallback(unittest.TestCase):
    """No optional PDF dependency installed is the common case, not an edge one."""

    def load_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("discoveries_gen", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        # Register before exec: @dataclass resolves its module via sys.modules.
        sys.modules["discoveries_gen"] = module
        spec.loader.exec_module(module)
        return module

    def test_stdlib_renderer_writes_a_valid_pdf_with_content(self):
        from pathlib import Path

        module = self.load_module()
        doc = module.parse_discoveries(GOOD_DOC)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stdlib.pdf"
            self.assertTrue(module.render_with_stdlib(doc, out))
            with open(out, "rb") as handle:
                raw = handle.read()
            self.assertTrue(raw.startswith(b"%PDF-"), "must be a valid PDF")
            self.assertIn(b"%%EOF", raw)
            text = pdf_text(out)
            self.assertIn("Headline numbers", text)
            self.assertIn("POSSIBLY_SAME", text)

    def test_audit_accepts_the_good_document(self):
        module = self.load_module()
        doc = module.parse_discoveries(GOOD_DOC)
        audit = module.audit_discoveries(doc, GOOD_DOC)
        self.assertTrue(audit.ok, audit.fatal)
        self.assertEqual([], audit.missing_sections)
        self.assertGreater(audit.retention, module.MIN_CONTENT_RETENTION)


class TestModuleWiring(unittest.TestCase):
    """The deliverable must be produced on every branch of the Discover opt-in."""

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def test_gate_produces_the_deliverable(self):
        text = self.read(PHASE1)
        self.assertIn("docs/bootcamp_data_discoveries.md", text)
        self.assertIn("generate_discoveries_pdf.py", text)

    def test_all_six_sections_are_specified(self):
        text = self.read(PHASE1)
        for section in (
            "Headline numbers",
            "Merges and match keys",
            "Review queue",
            "Why and how",
            "Relationship networks",
            "What was not found",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_decline_branch_says_findings_are_not_skipped(self):
        text = self.read(PHASE2)
        self.assertIn("Declining skips the walkthrough, not the findings", text)

    def test_deliverable_is_non_blocking(self):
        text = self.read(PHASE1)
        self.assertIn("never blocks the gate below or graduation", text)

    def test_verification_is_required_not_just_a_success_line(self):
        text = self.read(PHASE1)
        self.assertIn("is not verification", text)

    def test_findings_come_through_mcp_not_sql(self):
        text = self.read(PHASE1)
        self.assertIn("never direct SQL", text)

    def test_recap_generator_is_not_reused_for_this_document(self):
        text = self.read(PHASE1)
        self.assertIn("do not point", text.lower())


# A document with NONE of the discoveries headings, but plenty of content, so it clears
# the retention floor. This is the shape that was refused: business_problem.md.
OTHER_DOC = """# Business Problem

**Bootcamper:** A. Person
**Date:** 2026-07-31

## The problem in one sentence

Duplicate customer records across two acquired systems make it impossible to tell how many
distinct customers the combined business serves, which blocks accurate churn reporting.

## Why it matters

Marketing spend is allocated per contact, so duplicates inflate cost and irritate customers
who receive the same campaign several times over.

## Success criteria

- A single resolved view of customers across both source systems.
- A defensible count of distinct customers, with merge evidence available for review.

## Desired outputs

A resolved-entity table, a review queue for ambiguous merges, and a short report naming the
match keys that drove the largest merges.
"""

OTHER_SECTIONS = "the problem in one sentence;why it matters;success criteria;desired outputs"


class TestAnyDocumentCanRenderWithItsOwnSections(unittest.TestCase):
    """The required-section list is a parameter, not a constant.

    `generate_discoveries_pdf.py` is already a general styled-Markdown renderer — its
    layout engine carries nothing discoveries-specific — but `REQUIRED_SECTIONS` was a
    module-level constant checked fatally with no CLI override, so it rendered exactly one
    file. `docs/business_problem.md` and `docs/data_source_evaluation.md` were both refused.

    The guard itself is correct and stays: it is what stops the script being pointed at
    unrelated Markdown and silently emitting a near-empty PDF (INV-110). The defect was
    expressing it as one document's section names.
    """

    def test_the_flag_lets_another_document_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            out = os.path.join("docs", "business_problem.pdf")
            result = run(
                ["--input", os.path.join("docs", "business_problem.md"),
                 "--output", out, "--require-sections", OTHER_SECTIONS],
                tmp,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(SUCCESS_LINE, result.stdout)
            written = os.path.join(tmp, out)
            self.assertTrue(os.path.exists(written))
            # INV-129: the PDF must carry the content, not merely exist.
            text = pdf_text(written)
            for probe in ("Business Problem", "Success criteria", "churn reporting"):
                with self.subTest(probe=probe):
                    self.assertIn(probe.lower(), text.lower())

    def test_omitting_the_flag_still_refuses_the_same_document(self):
        """The companion assertion: the guard is relaxed only when asked."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            out = os.path.join("docs", "business_problem.pdf")
            result = run(
                ["--input", os.path.join("docs", "business_problem.md"), "--output", out],
                tmp,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertNotIn(SUCCESS_LINE, result.stdout)
            self.assertFalse(os.path.exists(os.path.join(tmp, out)))
            self.assertIn("none of the required sections is present", result.stderr)

    def test_the_discoveries_default_is_byte_for_byte_unchanged(self):
        """No flags must behave exactly as before, or every existing call site shifts."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, GOOD_DOC)
            result = run([], tmp)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(SUCCESS_LINE, result.stdout)

    def test_no_section_check_skips_only_the_section_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            result = run(
                ["--input", os.path.join("docs", "business_problem.md"), "--check",
                 "--no-section-check"],
                tmp,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("would render", result.stdout)

    def test_the_retention_floor_is_not_weakened_by_either_flag(self):
        """The floor — not the section list — is what stops unrelated Markdown (INV-110).

        Asserted against a document that genuinely fails retention (55% against a 60%
        floor), so this cannot pass by the input happening to be fine. An earlier draft
        accepted either outcome and was nearly tautological.
        """
        thin = "# T\n\n## A\n\nreal\n" + "\n---\n" * 10
        for extra in (["--no-section-check"], ["--require-sections", "a"]):
            with self.subTest(flag=extra[0]):
                with tempfile.TemporaryDirectory() as tmp:
                    write_doc(tmp, thin, name="thin.md")
                    out = os.path.join("docs", "thin.pdf")
                    result = run(
                        ["--input", os.path.join("docs", "thin.md"), "--output", out, *extra],
                        tmp,
                    )
                    self.assertNotEqual(
                        0, result.returncode, "the retention floor must still refuse"
                    )
                    self.assertIn("content retention", result.stderr)
                    self.assertNotIn(SUCCESS_LINE, result.stdout)
                    self.assertFalse(os.path.exists(os.path.join(tmp, out)))

    def test_the_cover_subtitle_is_overridable(self):
        """⚠️ The spec says the layout engine "contains nothing specific to the
        discoveries document". That is false for one string: the cover subtitle read
        "What Senzing found in your data" in **both** renderers, so rendering
        business_problem.md put a discoveries line on a stakeholder-facing keepsake —
        the first thing its reader sees."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            out = os.path.join("docs", "business_problem.pdf")
            result = run(
                ["--input", os.path.join("docs", "business_problem.md"), "--output", out,
                 "--require-sections", OTHER_SECTIONS,
                 "--subtitle", "The problem this bootcamp set out to solve"],
                tmp,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            text = pdf_text(os.path.join(tmp, out))
            self.assertIn("The problem this bootcamp set out to solve", text)
            self.assertNotIn("What Senzing found in your data", text)

    def test_the_default_subtitle_is_unchanged_for_discoveries(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, GOOD_DOC)
            out = os.path.join("docs", "d.pdf")
            self.assertEqual(0, run(["--output", out], tmp).returncode)
            self.assertIn("What Senzing found in your data", pdf_text(os.path.join(tmp, out)))

    @requires_fpdf2
    def test_both_renderers_honor_the_subtitle(self):
        """INV-066: the fallback writer must not keep the discoveries cover line."""
        module = load_generator_module()
        doc = module.parse_discoveries(OTHER_DOC)
        doc.subtitle = "A custom cover line"
        with tempfile.TemporaryDirectory() as tmp:
            for renderer in (module.render_with_fpdf2, module.render_with_stdlib):
                with self.subTest(renderer=renderer.__name__):
                    out = os.path.join(tmp, f"{renderer.__name__}.pdf")
                    self.assertTrue(renderer(doc, Path(out)))
                    text = pdf_text(out)
                    self.assertIn("A custom cover line", text)
                    self.assertNotIn("What Senzing found in your data", text)

    def test_character_handling_is_unchanged_on_the_new_path(self):
        """INV-143/INV-159: out-of-font characters are transliterated, not dropped.

        The renderer is the same one, so this is a guard against a future change routing
        the new path around `_safe`/`dropped_character_warning` rather than a new
        behavior. `->` and `>=` are what the reader should see; a `(cid:` artifact or a
        vanished clause is the failure.
        """
        doc = (
            "# Business Problem\n\n## Success criteria\n\n"
            "A resolved view of customers → one entity per person, with ≥ 95% "
            "precision, over ranges of 10–20 records.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, doc, name="chars.md")
            out = os.path.join("docs", "chars.pdf")
            result = run(
                ["--input", os.path.join("docs", "chars.md"), "--output", out,
                 "--require-sections", "success criteria"],
                tmp,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            text = pdf_text(os.path.join(tmp, out))
            self.assertIn("->", text)
            self.assertIn(">=", text)
            self.assertIn("95% precision", text, "the clause must survive intact")
            self.assertNotIn("(cid:", text)

    def test_an_empty_require_sections_value_is_an_error_not_a_silent_skip(self):
        """`--require-sections ""` must not quietly mean `--no-section-check`."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            result = run(
                ["--input", os.path.join("docs", "business_problem.md"), "--check",
                 "--require-sections", ""],
                tmp,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("--no-section-check", result.stderr)

    def test_section_names_are_matched_case_insensitively(self):
        """Callers pass a document's headings verbatim, capitals and all."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            result = run(
                ["--input", os.path.join("docs", "business_problem.md"), "--check",
                 "--require-sections", "Success Criteria;Desired Outputs"],
                tmp,
            )
            self.assertEqual(0, result.returncode, result.stderr)

    def test_the_check_line_counts_against_the_effective_list(self):
        """Reporting `n/6` while requiring two sections would be a lie."""
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            result = run(
                ["--input", os.path.join("docs", "business_problem.md"), "--check",
                 "--require-sections", "success criteria;desired outputs"],
                tmp,
            )
            self.assertIn("2/2", result.stdout)


class TestTheRendererIsFindable(unittest.TestCase):
    """An otherwise generic renderer named for one document is a discoverability bug."""

    def test_the_wrapper_exists_and_delegates(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_doc(tmp, OTHER_DOC, name="business_problem.md")
            out = os.path.join("docs", "business_problem.pdf")
            result = subprocess.run(
                [sys.executable, WRAPPER,
                 "--input", os.path.join("docs", "business_problem.md"),
                 "--output", out, "--require-sections", OTHER_SECTIONS],
                capture_output=True, text=True, cwd=tmp,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn(SUCCESS_LINE, result.stdout)
            self.assertTrue(os.path.exists(os.path.join(tmp, out)))

    def test_the_wrapper_adds_no_behavior_of_its_own(self):
        """It must not be able to drift from the script it wraps: no argument parsing,
        no defaults, no rendering — just a delegated `main`."""
        with open(WRAPPER, encoding="utf-8") as handle:
            body = handle.read()
        self.assertIn("from generate_discoveries_pdf import main", body)
        for forbidden in ("add_argument", "ArgumentParser", "REQUIRED_SECTIONS"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body.split('"""', 2)[-1])

    def test_the_wrapper_reports_a_broken_install_rather_than_crashing(self):
        self.assertRegex(
            open(WRAPPER, encoding="utf-8").read(),
            r"(?s)except ImportError.*Cannot import generate_discoveries_pdf",
        )

    def test_graduation_renders_both_documents_via_the_plugin_root(self):
        """INV-185: a bundled script is addressed through ${CLAUDE_PLUGIN_ROOT}."""
        with open(GRADUATION, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/scripts/generate_document_pdf.py", text)
        for doc in ("docs/business_problem.md", "docs/data_source_evaluation.md"):
            with self.subTest(doc=doc):
                self.assertIn(doc, text)

    def test_graduation_says_to_read_the_documents_own_headings(self):
        """There is no fixed list to hard-code — that is why the flag exists."""
        flat = re.sub(r"\s+", " ", open(GRADUATION, encoding="utf-8").read())
        self.assertRegex(flat, r"(?i)Read each document's actual H2 headings")
        self.assertIn("--require-sections", flat)

    def test_graduation_keeps_the_step_non_blocking_and_verified(self):
        text = open(GRADUATION, encoding="utf-8").read()
        start = text.index("## Step 5b:")
        section = text[start : text.index("## Step 6:", start)]
        self.assertIn("INV-048", section)
        self.assertIn("INV-129", section)
        self.assertRegex(
            re.sub(r"\s+", " ", section), r"(?i)Extract text from the written file"
        )
        self.assertIn("INV-110", section)
        self.assertRegex(
            section, r"(?i)INV-143", "the character-drop report must not be bypassed"
        )

    def test_step_5b_sits_between_5a_and_the_revisit_bundle(self):
        text = open(GRADUATION, encoding="utf-8").read()
        self.assertLess(text.index("## Step 5a:"), text.index("## Step 5b:"))
        self.assertLess(text.index("## Step 5b:"), text.index("## Step 6:"))


if __name__ == "__main__":
    unittest.main()
