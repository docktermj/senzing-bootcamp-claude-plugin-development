"""Graduation's handover reaches the keepsake as its own page — and is never a module (#481).

Graduation folds "Decisions you made", "How you got it built", the Bootcamper's one-line
takeaway and their "Next time" request into `docs/bootcamp_recap.md` inside a
`<!-- BOOTCAMP-HANDOVER:START/END -->` fence. The block opens with a ``## `` heading, and the
recap has exactly one shape for a ``## ``: a module. So, as for the notes fence (INV-258),
most of these tests are about what the handover must **not** become — a module section, a
certificate citation (INV-100), a cover-list entry, a four-subsection failure under
``--check`` (INV-103), or content the retention figure scores as lost (INV-110).

The lift is a **dedicated** one, `_extract_handover_block`, modeled on
`_extract_notes_block` and leaving it untouched; `TheNotesAreUnchanged` pins that the notes
section parses identically with a handover beside it.

The rendering tests use the shipped example recap (`docs/examples/bootcamp_recap.example.md`,
INV-065) as the real fixture: it already carries a notes fence, so the order modules →
notes → handover → certificate is measured on a recap shaped like a Bootcamper's. The
``--check`` tests use a small image-free recap, because the example's screenshots do not
resolve from a temporary directory and ``--check`` rightly reports that.

Source issue: #481 (Graduation hands over the ability).

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
from pathlib import Path

from _fpdf2_support import requires_fpdf2

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPT = PLUGIN / "scripts" / "generate_recap_pdf.py"
EXAMPLE_MD = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"

HANDOVER_TITLE = "What You Take With You"
SUBTITLE_PROBE = "From here there is no script"

HANDOVER = """
<!-- BOOTCAMP-HANDOVER:START -->
## What You Take With You

### Decisions you made

- Discover the Business Problem: MARKERDECISION chose to find duplicate customers across the CRM and billing files.
- Data processing: chose the small-production loader (option 2).

### How you got it built

- **Data processing:** MARKERBUILT you asked for a loader for both sources; the AI built `src/load/load_sources.py` with the Senzing MCP server.

### Your takeaway

MARKERTAKEAWAY Entity resolution is a data problem before it is a code problem.

### Next time

MARKERNEXT Help me map and load our vendor master file into Senzing and find the vendors that are also customers.
<!-- BOOTCAMP-HANDOVER:END -->
"""

MODULES = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-10-11

## Discover the Business Problem — 2026-10-11

### Information Shared

- Entity resolution resolves records to entities.

### Questions & Responses

- **Q:** What does success look like?
    - **R:** One row per customer.

### Actions Taken

- Wrote the problem statement.

### End-of-Module Summary

**What you accomplished:**
- Framed the business problem.

**Files produced:**
- `docs/business_problem.md` — the problem statement

**Why it matters:** every later choice traces back to it.
"""


def load_generator():
    spec = importlib.util.spec_from_file_location("recap_gen_handover_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recap_gen_handover_under_test"] = module
    spec.loader.exec_module(module)
    return module


GEN = load_generator()
EXAMPLE = EXAMPLE_MD.read_text(encoding="utf-8")
WITH_HANDOVER = EXAMPLE + HANDOVER


def run_cli(markdown, *args):
    """Run the real CLI on ``markdown`` from a fresh directory; return (proc, output path)."""
    workdir = tempfile.mkdtemp()
    src = os.path.join(workdir, "recap.md")
    out = os.path.join(workdir, "recap.pdf")
    with open(src, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", src, "--output", out, *args],
        capture_output=True, text=True, cwd=workdir,
    )
    return proc, out


def render_to(markdown):
    proc, out = run_cli(markdown)
    assert proc.returncode == 0, proc.stderr
    return out


def pages_of_text(path):
    """``[text_of_page_1, ...]`` in page-tree order (the notes tests' reader, INV-258)."""
    with open(path, "rb") as handle:
        raw = handle.read()
    objects = {
        int(m.group(1)): m.group(2)
        for m in re.finditer(rb"(\d+) 0 obj\r?\n(.*?)\r?\nendobj", raw, re.S)
    }
    tree = next((b for b in objects.values() if b"/Type /Pages" in b), b"")
    kids = re.search(rb"/Kids \[(.*?)\]", tree, re.S)
    out = []
    for number in (int(n) for n in
                   re.findall(rb"(\d+) 0 R", kids.group(1) if kids else b"")):
        body = objects.get(number, b"")
        contents = re.search(rb"/Contents (\d+) 0 R", body)
        if not contents:
            continue
        stream = re.search(rb"stream\r?\n(.*?)\r?\nendstream",
                           objects.get(int(contents.group(1)), b""), re.S)
        if not stream:
            continue
        try:
            data = zlib.decompressobj().decompress(stream.group(1))
        except zlib.error:
            data = stream.group(1)
        text = data.decode("latin-1", "replace")
        out.append(" ".join(re.findall(r"\((.*?)\)\s*Tj", text)))
    return out


def page_index_containing(pages, needle):
    for i, text in enumerate(pages):
        if needle in text:
            return i
    return -1


def module_titles(markdown):
    return [m.title for m in GEN.parse_recap(markdown).modules]


class TheFixtureIsReal(unittest.TestCase):
    """Non-vacuity: the example recap still has modules and a notes fence to measure against."""

    def test_the_example_has_modules_and_notes(self):
        recap = GEN.parse_recap(EXAMPLE)
        self.assertGreaterEqual(len(recap.modules), 5)
        self.assertIsNotNone(recap.notes, "the example lost its notes fence")
        self.assertIsNone(recap.handover, "the example already carries a handover block")


class TheHandoverIsParsedButIsNeverAModule(unittest.TestCase):

    def setUp(self):
        self.recap = GEN.parse_recap(WITH_HANDOVER)

    def test_the_handover_does_not_become_a_module_section(self):
        self.assertEqual(module_titles(EXAMPLE), module_titles(WITH_HANDOVER))
        self.assertNotIn(HANDOVER_TITLE, module_titles(WITH_HANDOVER))

    def test_the_handover_is_parsed_into_its_own_field_in_order(self):
        self.assertIsNotNone(self.recap.handover)
        self.assertEqual(HANDOVER_TITLE, self.recap.handover.title)
        self.assertEqual(
            ["Decisions you made", "How you got it built", "Your takeaway", "Next time"],
            [heading for heading, _ in self.recap.handover.parts])
        self.assertIn("MARKERNEXT", " ".join(self.recap.handover.part("Next time")))

    def test_the_handover_is_absent_from_the_certificate_citation(self):
        """INV-100 — the certificate cites modules completed, and a handover is not one."""
        _, _, labels = GEN._cert_fields(self.recap)
        self.assertEqual(GEN._cert_fields(GEN.parse_recap(EXAMPLE))[2], labels)
        self.assertNotIn(HANDOVER_TITLE, labels)

    def test_verify_reports_exactly_what_it_reported_without_the_handover(self):
        """INV-103 — the handover is never held to the four-subsection check."""
        self.assertEqual(GEN.verify_recap(GEN.parse_recap(EXAMPLE)),
                         GEN.verify_recap(self.recap))
        self.assertEqual([], GEN.verify_recap(GEN.parse_recap(MODULES + HANDOVER)))
        self.assertEqual([], GEN.audit_recap(self.recap, WITH_HANDOVER).fatal)

    def test_the_fence_and_not_the_heading_is_the_discriminator(self):
        """An unfenced heading with the handover's title is a module, and no handover."""
        unfenced = (WITH_HANDOVER.replace(GEN.BOOTCAMP_HANDOVER_START, "")
                    .replace(GEN.BOOTCAMP_HANDOVER_END, ""))
        recap = GEN.parse_recap(unfenced)
        self.assertIn(HANDOVER_TITLE, [m.title for m in recap.modules])
        self.assertIsNone(recap.handover)

    def test_an_unterminated_fence_still_keeps_the_handover_out_of_the_modules(self):
        """A write truncated mid-fold runs to end of text; it never promotes a module."""
        truncated = WITH_HANDOVER.replace(GEN.BOOTCAMP_HANDOVER_END, "")
        recap = GEN.parse_recap(truncated)
        self.assertEqual(module_titles(EXAMPLE), [m.title for m in recap.modules])
        self.assertNotIn(HANDOVER_TITLE, GEN._cert_fields(recap)[2])
        self.assertIsNotNone(recap.handover)

    def test_an_unterminated_handover_stops_at_a_notes_fence_after_it(self):
        """The sweep ends at the next fence of another type, so later notes survive."""
        modules_only, _ = GEN._extract_notes_block(EXAMPLE)
        notes_block = EXAMPLE[EXAMPLE.index(GEN.BOOTCAMP_NOTES_START):
                              EXAMPLE.index(GEN.BOOTCAMP_NOTES_END)
                              + len(GEN.BOOTCAMP_NOTES_END)]
        source = (modules_only + HANDOVER.replace(GEN.BOOTCAMP_HANDOVER_END, "")
                  + "\n" + notes_block + "\n")
        recap = GEN.parse_recap(source)
        self.assertIsNotNone(recap.handover)
        self.assertIsNotNone(recap.notes, "the truncated handover swallowed the notes")
        self.assertEqual(GEN.parse_recap(EXAMPLE).notes, recap.notes)
        self.assertEqual(module_titles(EXAMPLE), [m.title for m in recap.modules])

    def test_a_truncated_notes_fence_does_not_swallow_a_handover_after_it(self):
        """The handover is lifted first, so an unterminated notes fence cannot annex it."""
        truncated = EXAMPLE.replace(GEN.BOOTCAMP_NOTES_END, "") + HANDOVER
        recap = GEN.parse_recap(truncated)
        self.assertIsNotNone(recap.handover)
        self.assertIsNotNone(recap.notes)
        note_titles = [n.title for n in recap.notes.entries]
        self.assertNotIn("Decisions you made", note_titles)
        self.assertEqual(module_titles(EXAMPLE), [m.title for m in recap.modules])

    def test_a_stray_start_never_costs_a_module_and_is_reported(self):
        """INV-288 — a stray START is left in place and named, never swept."""
        stray = MODULES.replace(
            "## Discover the Business Problem",
            GEN.BOOTCAMP_HANDOVER_START + "\n\n## Discover the Business Problem") + HANDOVER
        recap = GEN.parse_recap(stray)
        self.assertEqual(["Discover the Business Problem"], [m.title for m in recap.modules])
        self.assertIsNotNone(recap.handover)
        reported = [m for m, _ in GEN.stray_fence_markers(stray)]
        self.assertIn(GEN.BOOTCAMP_HANDOVER_START, reported)
        self.assertTrue(any("stray " + GEN.BOOTCAMP_HANDOVER_START in w
                            for w in GEN.audit_recap(recap, stray).warnings))


class ReRunningReplacesAndNeverAppends(unittest.TestCase):
    """INV-085 — one block. A second is lifted (never a module) and reported."""

    def setUp(self):
        self.doubled = MODULES + HANDOVER + HANDOVER.replace("MARKERNEXT", "MARKERNEWER")

    def test_both_blocks_are_lifted_and_the_newest_is_rendered(self):
        recap = GEN.parse_recap(self.doubled)
        self.assertEqual(["Discover the Business Problem"], [m.title for m in recap.modules])
        self.assertIn("MARKERNEWER", " ".join(recap.handover.part("Next time")))

    def test_the_audit_reports_the_second_block(self):
        warnings = GEN.audit_recap(GEN.parse_recap(self.doubled), self.doubled).warnings
        self.assertTrue(any("INV-085" in w and "2 " + GEN.BOOTCAMP_HANDOVER_START in w
                            for w in warnings), warnings)
        self.assertEqual(1, GEN.handover_block_count(MODULES + HANDOVER))

    def test_check_fails_on_the_second_block(self):
        proc, _ = run_cli(self.doubled, "--check")
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("INCOMPLETE:", proc.stderr)
        self.assertIn("INV-085", proc.stderr)


class CheckDoesNotCountTheHandoverAsAModule(unittest.TestCase):
    """Compatibility: a recap with or without the block passes ``--check`` alike."""

    def test_check_passes_with_and_without_the_handover(self):
        for label, source in (("without", MODULES), ("with", MODULES + HANDOVER)):
            with self.subTest(recap=label):
                proc, _ = run_cli(source, "--check")
                self.assertEqual(0, proc.returncode, proc.stderr)
                self.assertIn("Recap complete", proc.stdout)
                self.assertNotIn(HANDOVER_TITLE, proc.stderr)

    def test_expect_modules_is_not_satisfied_by_the_handover(self):
        """A handover titled like a missing module never stands in for it."""
        source = MODULES + HANDOVER.replace(HANDOVER_TITLE, "Data processing")
        proc, _ = run_cli(source, "--check", "--expect-modules", "Data processing")
        self.assertEqual(1, proc.returncode)
        self.assertIn("expected module 'Data processing' has no recap section", proc.stderr)


class NothingRecordedMeansNothingRendered(unittest.TestCase):
    """A list with no entries is left out; an all-empty block is no handover at all."""

    def test_an_empty_part_is_dropped(self):
        source = MODULES + HANDOVER.replace(
            "MARKERTAKEAWAY Entity resolution is a data problem before it is a code problem.",
            "")
        recap = GEN.parse_recap(source)
        self.assertIsNone(recap.handover.part("Your takeaway"))
        self.assertEqual(["Decisions you made", "How you got it built", "Next time"],
                         [h for h, _ in recap.handover.parts])

    def test_an_all_empty_fence_produces_no_handover(self):
        empty = MODULES + (
            f"\n{GEN.BOOTCAMP_HANDOVER_START}\n## {HANDOVER_TITLE}\n\n### Decisions you made\n"
            f"\n### Next time\n{GEN.BOOTCAMP_HANDOVER_END}\n")
        self.assertIsNone(GEN.parse_recap(empty).handover)

    def test_a_recap_without_the_fence_has_no_handover(self):
        self.assertIsNone(GEN.parse_recap(MODULES).handover)


class TheNotesAreUnchanged(unittest.TestCase):
    """Strategy: a dedicated lifter. The notes section parses exactly as before."""

    def test_the_notes_parse_identically_beside_a_handover(self):
        self.assertEqual(GEN.parse_recap(EXAMPLE).notes, GEN.parse_recap(WITH_HANDOVER).notes)


class TheRetentionFigureCountsTheHandover(unittest.TestCase):
    """INV-110 — the Bootcamper's own words are never scored as content the PDF lost."""

    def test_the_handover_characters_are_counted_as_rendered(self):
        self.assertGreater(GEN._rendered_content_chars(GEN.parse_recap(WITH_HANDOVER)),
                           GEN._rendered_content_chars(GEN.parse_recap(EXAMPLE)))

    def test_retention_does_not_fall_when_the_handover_is_added(self):
        bare = GEN.audit_recap(GEN.parse_recap(MODULES), MODULES)
        handed = GEN.audit_recap(GEN.parse_recap(MODULES + HANDOVER), MODULES + HANDOVER)
        self.assertGreaterEqual(round(handed.retention, 2), round(bare.retention, 2))

    def test_a_long_handover_still_renders(self):
        long_handover = HANDOVER.replace(
            "- Data processing: chose the small-production loader (option 2).",
            "\n".join(["- MARKERDECISION a long recorded decision about the mapping."] * 300))
        source = MODULES + long_handover
        audit = GEN.audit_recap(GEN.parse_recap(source), source)
        self.assertEqual([], audit.fatal)
        self.assertGreaterEqual(audit.retention, GEN.MIN_CONTENT_RETENTION)

    def test_the_fence_markers_are_not_counted_as_source_content(self):
        marked = GEN._source_content_chars(
            f"line\n{GEN.BOOTCAMP_HANDOVER_START}\n{GEN.BOOTCAMP_HANDOVER_END}\n")
        self.assertEqual(len("line"), marked)


class TheHandoverPageIsRenderedInBothRenderers(unittest.TestCase):
    """INV-066 — the stdlib fallback keeps parity with fpdf2."""

    @requires_fpdf2
    def test_fpdf2_places_it_after_the_notes_and_before_the_certificate(self):
        pages = pages_of_text(render_to(WITH_HANDOVER))
        notes = page_index_containing(pages, "In your own words")
        handover = page_index_containing(pages, SUBTITLE_PROBE)
        cert = page_index_containing(pages, "Certificate of Completion")
        self.assertNotEqual(-1, handover, "the handover page was not rendered at all")
        self.assertNotEqual(-1, notes, "the notes page was not found")
        self.assertLess(notes, handover, "the handover renders before the notes page")
        self.assertLess(handover, cert, "the handover renders after the certificate")
        page = pages[handover]
        for marker in ("MARKERDECISION", "MARKERBUILT", "MARKERTAKEAWAY", "MARKERNEXT"):
            with self.subTest(marker=marker):
                self.assertIn(marker, page)

    @requires_fpdf2
    def test_fpdf2_adds_exactly_one_page(self):
        self.assertEqual(len(pages_of_text(render_to(EXAMPLE))) + 1,
                         len(pages_of_text(render_to(WITH_HANDOVER))))

    def test_the_stdlib_renderer_also_carries_the_handover(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stdlib.pdf"
            self.assertTrue(GEN.render_with_stdlib(GEN.parse_recap(WITH_HANDOVER), out))
            text = " ".join(pages_of_text(out))
            for marker in ("MARKERDECISION", "MARKERBUILT", "MARKERTAKEAWAY", "MARKERNEXT",
                           SUBTITLE_PROBE):
                with self.subTest(marker=marker):
                    self.assertIn(marker, text)
            self.assertLess(text.index(GEN.parse_recap(EXAMPLE).notes.title),
                            text.index(SUBTITLE_PROBE),
                            "the stdlib renderer puts the handover before the notes")

    def test_the_stdlib_cover_module_list_excludes_the_handover(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stdlib.pdf"
            GEN.render_with_stdlib(GEN.parse_recap(WITH_HANDOVER), out)
            first_page = pages_of_text(out)[0]
            _, _, tail = first_page.partition("Modules completed")
            self.assertTrue(tail, "the stdlib cover has no module list")
            self.assertNotIn(HANDOVER_TITLE, tail[:400])


@requires_fpdf2
class TheTableOfContentsListsTheHandover(unittest.TestCase):

    def test_the_handover_has_a_row_with_its_real_start_page(self):
        pages = pages_of_text(render_to(WITH_HANDOVER))
        toc = pages[page_index_containing(pages, "Contents")]
        self.assertIn(HANDOVER_TITLE, toc, "the handover has no row in the contents")
        expected = page_index_containing(pages, SUBTITLE_PROBE) + 1
        found = re.search(r"(\d+)", toc.split(HANDOVER_TITLE)[-1][:40])
        self.assertTrue(found, "the handover row carries no page number")
        self.assertEqual(str(expected), found.group(1))

    def test_module_and_notes_page_numbers_are_unchanged(self):
        """The two-pass render paginates identically up to the handover page."""
        notes_title = GEN.parse_recap(EXAMPLE).notes.title

        def toc_numbers(markdown):
            """Every page number up to and including the notes row's."""
            pages = pages_of_text(render_to(markdown))
            toc = pages[page_index_containing(pages, "Contents")]
            head, _, tail = toc.partition(notes_title)
            notes_row = re.search(r"(\d+)", tail[:40])
            self.assertTrue(notes_row, "the notes row carries no page number")
            return re.findall(r"\b(\d+)\b", head) + [notes_row.group(1)]

        self.assertEqual(toc_numbers(EXAMPLE), toc_numbers(WITH_HANDOVER))

    def test_without_the_handover_there_is_no_page_and_no_row(self):
        pages = pages_of_text(render_to(EXAMPLE))
        self.assertEqual(-1, page_index_containing(pages, SUBTITLE_PROBE))
        self.assertNotIn(HANDOVER_TITLE, pages[page_index_containing(pages, "Contents")])


if __name__ == "__main__":
    unittest.main()
