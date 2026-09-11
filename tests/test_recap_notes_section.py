"""The Bootcamper's own notes reach the keepsake — and are never mistaken for a module.

Enforces **INV-258**. The notes section is the one part of the recap the Bootcamper wrote,
and the whole risk in adding it is that the recap's structure has exactly one shape for a
``## `` heading: a module. `parse_recap` turns every ``## `` into a `ModuleSection`, and
five downstream consumers then treat it as one — the certificate's module citation
(INV-100), both renderers' cover module lists, the table of contents, the four-subsection
completeness check (INV-103), and the retention accounting that can REFUSE to render
(INV-110).

So these tests are mostly about what the notes section must **not** become. The fence
markers, not the heading text, are what tell the two apart: a section recognized by its
title would be one renamed module away from being mis-parsed, and a Bootcamper's private
note one heading away from being printed on their certificate.

⚠️ **The retention test is the one whose absence would be silent.** Miss the accounting and
the failure is not a wrong page — it is a Bootcamper who wrote a lot of notes watching the
generator refuse to produce their recap at all, with the reason given as content loss.

Source spec: `specs/bootcamp-notes-capture-and-recap-section.md`.

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
SCRIPT = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_recap_pdf.py"

MODULES = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-08-16

## Discover the Business Problem — 2026-08-16

### Objectives

- Understand the duplicate-customer problem.

### Information Shared

- Entity resolution resolves records to entities.

### Questions & Responses

- Asked what success looks like; answered "one row per customer".

### Actions Taken

- Wrote the problem statement.

### Key Learnings

- The problem is a data problem before it is a code problem.

### End-of-Module Summary

**What you accomplished:** framed the business problem.
**Files produced:** `docs/problem-statement.md`
**Why it matters:** every later choice traces back to it.

## Query, Visualize and Discover — 2026-08-16

### Objectives

- Query the resolved entities.

### Information Shared

- The engine exposes why-analysis for every decision.

### Questions & Responses

- Asked which entity to inspect; answered "the largest".

### Actions Taken

- Ran the queries and captured screenshots.

### Key Learnings

- A match key explains itself if you ask it.

### End-of-Module Summary

**What you accomplished:** queried and visualized the data.
**Files produced:** `docs/visualizations/network.png`
**Why it matters:** it is the payoff the whole pipeline was built for.
"""

NOTES = """
<!-- BOOTCAMP-NOTES:START -->
## Notes, Ideas and Questions

### Idea: map dba_name as a second NAME

**Captured:** 2026-08-16T10:05:00-05:00
**Module:** Data Quality and Mapping
**Type:** idea

MARKERIDEA we could map the vendor file's dba_name as a second NAME rather than payload.

**Context:** MARKERCONTEXT step 4; pending question was "Ready to map?"

### Question: does whyEntities need a flag?

**Captured:** 2026-08-16T11:00:00-05:00
**Module:** Query, Visualize and Discover
**Type:** question

MARKERQUESTION does whyEntities need a flag I have not set?

**Elaboration:** MARKERELAB the default flag set omits record data.
<!-- BOOTCAMP-NOTES:END -->
"""

WITH_NOTES = MODULES + NOTES
NOTES_TITLE = "Notes, Ideas and Questions"


def load_generator():
    spec = importlib.util.spec_from_file_location("recap_gen_notes_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recap_gen_notes_under_test"] = module
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def render_to(markdown, args=()):
    """Render `markdown` with the real CLI and return the output PDF path."""
    workdir = tempfile.mkdtemp()
    src = os.path.join(workdir, "recap.md")
    out = os.path.join(workdir, "recap.pdf")
    with open(src, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", src, "--output", out, *args],
        capture_output=True, text=True, cwd=workdir,
    )
    assert proc.returncode == 0, proc.stderr
    return out


def pages_of_text(path):
    """``[text_of_page_1, text_of_page_2, ...]`` in page-tree order.

    Read through the page tree's ``/Kids`` rather than by walking every
    ``stream ... endstream`` in file order: embedded images are streams too, and
    counting one as a page shifts every later page's index — which is precisely what
    these tests measure.
    """
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


class TheNotesAreParsedButAreNeverAModule(unittest.TestCase):

    def setUp(self):
        self.recap = GEN.parse_recap(WITH_NOTES)

    def test_the_notes_do_not_become_module_sections(self):
        titles = [m.title for m in self.recap.modules]
        self.assertEqual(
            ["Discover the Business Problem", "Query, Visualize and Discover"], titles)
        self.assertNotIn(NOTES_TITLE, titles)

    def test_the_notes_are_parsed_into_their_own_field(self):
        self.assertIsNotNone(self.recap.notes)
        self.assertEqual(NOTES_TITLE, self.recap.notes.title)
        self.assertEqual(2, len(self.recap.notes.entries))

    def test_each_note_keeps_its_type_title_stamp_and_module(self):
        first = self.recap.notes.entries[0]
        self.assertEqual("idea", first.type.lower())
        self.assertEqual("map dba_name as a second NAME", first.title)
        self.assertEqual("2026-08-16T10:05:00-05:00", first.captured)
        self.assertEqual("Data Quality and Mapping", first.module)

    def test_context_and_elaboration_are_never_merged_into_the_bootcampers_words(self):
        """INV-257. A paragraph they did not write must stay distinguishable forever."""
        first, second = self.recap.notes.entries
        body = " ".join(first.body)
        self.assertIn("MARKERIDEA", body)
        self.assertNotIn("MARKERCONTEXT", body,
                         "the context block was merged into the Bootcamper's own text")
        self.assertIn("MARKERCONTEXT", first.context)
        self.assertNotIn("MARKERELAB", " ".join(second.body),
                         "the elaboration was merged into the Bootcamper's own text")
        self.assertIn("MARKERELAB", second.elaboration)

    def test_the_notes_title_is_absent_from_the_certificate_citation(self):
        """INV-100 — the certificate cites modules completed, and a note is not one."""
        _, _, labels = GEN._cert_fields(self.recap)
        self.assertEqual(
            ["Discover the Business Problem", "Query, Visualize and Discover"], labels)

    def test_check_never_demands_the_module_subsections_of_the_notes(self):
        """A recap whose only "defect" is that notes are present reports zero problems."""
        self.assertEqual([], GEN.verify_recap(GEN.parse_recap(WITH_NOTES)))
        self.assertEqual([], GEN.audit_recap(GEN.parse_recap(WITH_NOTES),
                                             WITH_NOTES).fatal)

    def test_the_fence_and_not_the_heading_is_the_discriminator(self):
        """A module renamed to the notes title is still parsed as a module."""
        collide = MODULES.replace("## Query, Visualize and Discover —",
                                  f"## {NOTES_TITLE} —")
        recap = GEN.parse_recap(collide)
        self.assertIn(NOTES_TITLE, [m.title for m in recap.modules])
        self.assertIsNone(recap.notes, "an unfenced heading was read as a notes section")

    def test_an_unterminated_fence_still_keeps_the_notes_out_of_the_modules(self):
        """⛔ A write truncated mid-fold must never promote a note to a module.

        The fence runs to end of text when its closing marker is missing, because
        graduation appends the block after the last module. Reading the opening marker
        as absent instead would parse the notes heading as a module section — and a
        module section is cited on the Certificate of Completion (INV-100).
        """
        truncated = WITH_NOTES.replace(GEN.BOOTCAMP_NOTES_END, "")
        recap = GEN.parse_recap(truncated)
        self.assertEqual(2, len(recap.modules))
        self.assertNotIn(NOTES_TITLE, [m.title for m in recap.modules])
        self.assertNotIn(NOTES_TITLE, GEN._cert_fields(recap)[2])
        self.assertIsNotNone(recap.notes)


class TheRetentionFigureCountsTheNotes(unittest.TestCase):
    """⚠️ INV-110/INV-258. Miss this and writing notes makes the generator refuse."""

    def test_the_notes_characters_are_counted_as_rendered(self):
        without = GEN._rendered_content_chars(GEN.parse_recap(MODULES))
        with_notes = GEN._rendered_content_chars(GEN.parse_recap(WITH_NOTES))
        self.assertGreater(with_notes, without)

    def test_retention_does_not_fall_when_notes_are_added(self):
        bare = GEN.audit_recap(GEN.parse_recap(MODULES), MODULES)
        noted = GEN.audit_recap(GEN.parse_recap(WITH_NOTES), WITH_NOTES)
        self.assertGreaterEqual(
            round(noted.retention, 2), round(bare.retention, 2),
            "adding notes lowered the retention figure — the Bootcamper's own words "
            "are being counted as content the PDF lost")

    def test_a_long_notes_file_still_renders(self):
        """The failure this prevents: notes long enough to cross MIN_CONTENT_RETENTION."""
        long_notes = NOTES.replace(
            "MARKERIDEA we could map the vendor file's dba_name as a second NAME "
            "rather than payload.",
            " ".join(["MARKERIDEA a long note about the mapping decision."] * 200))
        source = MODULES + long_notes
        audit = GEN.audit_recap(GEN.parse_recap(source), source)
        self.assertEqual([], audit.fatal)
        self.assertGreaterEqual(audit.retention, GEN.MIN_CONTENT_RETENTION)

    def test_the_fence_markers_are_not_counted_as_source_content(self):
        marked = GEN._source_content_chars(
            f"line\n{GEN.BOOTCAMP_NOTES_START}\n{GEN.BOOTCAMP_NOTES_END}\n")
        self.assertEqual(len("line"), marked)


class TheNotesPageIsRenderedInBothRenderers(unittest.TestCase):
    """INV-066 — the stdlib fallback keeps parity with fpdf2."""

    @requires_fpdf2
    def test_fpdf2_places_the_notes_after_the_modules_and_before_the_certificate(self):
        pages = pages_of_text(render_to(WITH_NOTES))
        last_module = page_index_containing(pages, "Query, Visualize and Discover")
        notes = page_index_containing(pages, "In your own words")
        cert = page_index_containing(pages, "Certificate of Completion")
        self.assertNotEqual(-1, notes, "the notes page was not rendered at all")
        self.assertNotEqual(-1, cert, "the certificate page was not found")
        self.assertLess(last_module, notes,
                        "the notes page renders before the last module page")
        self.assertLess(notes, cert,
                        "the notes page renders after the Certificate of Completion")

    def test_fpdf2_renders_the_bootcampers_words_and_both_labels(self):
        text = " ".join(pages_of_text(render_to(WITH_NOTES)))
        for marker in ("MARKERIDEA", "MARKERCONTEXT", "MARKERQUESTION", "MARKERELAB"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertIn("ELABORATION", text.upper(),
                      "the elaboration is not labeled on the page, so a reader cannot "
                      "tell the bootcamp's words from the Bootcamper's")
        self.assertIn("CONTEXT", text.upper())

    def test_the_stdlib_renderer_also_carries_the_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stdlib.pdf"
            self.assertTrue(GEN.render_with_stdlib(GEN.parse_recap(WITH_NOTES), out))
            text = " ".join(pages_of_text(out))
            self.assertIn("MARKERIDEA", text)
            self.assertIn("MARKERQUESTION", text)

    def test_the_stdlib_cover_module_list_excludes_the_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stdlib.pdf"
            GEN.render_with_stdlib(GEN.parse_recap(WITH_NOTES), out)
            first_page = pages_of_text(out)[0]
            self.assertIn("Modules completed", first_page)
            head, _, tail = first_page.partition("Modules completed")
            self.assertNotIn(NOTES_TITLE, tail[:200],
                             "the notes title is listed among the modules completed")


@requires_fpdf2
class TheTableOfContentsListsTheNotes(unittest.TestCase):

    def _toc_page(self, markdown):
        pages = pages_of_text(render_to(markdown))
        index = page_index_containing(pages, "Contents")
        self.assertNotEqual(-1, index, "no table of contents page was rendered")
        return pages[index]

    def test_the_notes_have_a_row_with_their_real_start_page(self):
        pages = pages_of_text(render_to(WITH_NOTES))
        toc = pages[page_index_containing(pages, "Contents")]
        self.assertIn(NOTES_TITLE, toc, "the notes have no row in the contents")
        # The row's number must be the 1-based page the notes actually start on. A
        # measure pass that skipped the notes page would print a plausible wrong number
        # here, which is why this reads the real page rather than trusting the row.
        expected = page_index_containing(pages, "In your own words") + 1
        tail = toc.split(NOTES_TITLE)[-1][:40]
        found = re.search(r"(\d+)", tail)
        self.assertTrue(found, f"the notes row carries no page number; tail {tail!r}")
        self.assertEqual(str(expected), found.group(1),
                         f"the notes row points at page {found.group(1)} but the notes "
                         f"start on page {expected}")

    def test_module_page_numbers_are_unchanged_by_the_presence_of_notes(self):
        """The two-pass render must paginate identically up to the notes page."""
        def module_rows(markdown):
            toc = self._toc_page(markdown)
            rows = {}
            for title in ("Discover the Business Problem",
                          "Query, Visualize and Discover"):
                tail = toc.split(title)[-1][:40]
                match = re.search(r"(\d+)", tail)
                rows[title] = match.group(1) if match else None
            return rows

        self.assertEqual(module_rows(MODULES), module_rows(WITH_NOTES))


class WithNoNotesNothingChanges(unittest.TestCase):
    """An empty notes section on a keepsake is worse than an absent one."""

    def test_a_recap_without_the_fence_parses_with_no_notes(self):
        self.assertIsNone(GEN.parse_recap(MODULES).notes)

    def test_an_empty_fence_produces_no_notes_section(self):
        empty = MODULES + (
            f"\n{GEN.BOOTCAMP_NOTES_START}\n## {NOTES_TITLE}\n"
            f"{GEN.BOOTCAMP_NOTES_END}\n")
        self.assertIsNone(GEN.parse_recap(empty).notes,
                          "an empty notes section reached the keepsake")

    def test_no_notes_page_and_no_toc_row_are_rendered(self):
        pages = pages_of_text(render_to(MODULES))
        self.assertEqual(-1, page_index_containing(pages, "In your own words"))
        toc = pages[page_index_containing(pages, "Contents")]
        self.assertNotIn(NOTES_TITLE, toc)

    def test_the_page_count_is_unchanged(self):
        self.assertEqual(len(pages_of_text(render_to(MODULES))) + 1,
                         len(pages_of_text(render_to(WITH_NOTES))),
                         "adding notes changed the page count by something other than "
                         "the one notes page")


if __name__ == "__main__":
    unittest.main()
