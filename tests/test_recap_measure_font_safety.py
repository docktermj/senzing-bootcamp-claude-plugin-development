"""Measuring text is as font-sensitive as drawing it, and only drawing was guarded.

Found by the 2026-07-29 dry run (phase 2). With ``fpdf2`` installed, the generator still
reported ``renderer: stdlib`` — which the dry-run skill flags as a defect rather than a
fallback, because the honest fallback message hides the real cause:

    fpdf2 render failed: Character "—" at index 60 in text is outside the range
    of characters supported by the font used: "helvetica".

fpdf2's ``get_string_width`` runs the same ``normalize_text`` as its text writers, so it
raises on exactly the characters ``_safe`` exists to fold. Every *write* went through
``_safe``; **none of the five measurements did**. An em dash in a module title therefore
killed the whole fpdf2 render, and the Bootcamper's keepsake silently lost real tables
(INV-142) and the branded certificate (INV-156) — at exit 0, with a single
``renderer: stdlib`` word as the only signal. ``test_recap_pdf_font_safety.py`` passed
throughout, because it covers the write path.

The em dash arrived by an ordinary route. INV-085 mandates ``## {Module name} — {date}``
headings, and ``_split_title_date`` only split when the tail parsed as a date — so the
``— in progress`` suffix the durability hooks leave on a folded-but-unfinalized section
(INV-059) stayed glued to the title. That one stale title caused *two* defects: the
certificate joins and fits module titles, so the em dash rode into a width measurement;
and ``--check --expect-modules`` compares against the title, so the module read as absent
while the same run validated its subsections by name — reporting one section as both
found and "has no recap section at all", which sends graduation to backfill a section
that is already there (INV-157 warns against precisely that).

Both halves are pinned here: the class (no raw measurement anywhere) and the trigger
(the title split), plus end-to-end assertions that the renderer actually stays on fpdf2.

No phrase-level pattern (#438): its line reads are of Python source, the `get_string_width` calls,
as #424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPTS = os.path.join(PLUGIN, "scripts")
GENERATOR = os.path.join(SCRIPTS, "generate_recap_pdf.py")

sys.path.insert(0, SCRIPTS)
import generate_recap_pdf as G  # noqa: E402

try:
    import fpdf  # noqa: F401
    HAVE_FPDF = True
except ImportError:  # pragma: no cover - environment dependent
    HAVE_FPDF = False


def recap_text(heading, body_extra=""):
    """A minimal recap that satisfies the generator's structural gate."""
    return (
        "# Senzing Bootcamp Recap\n\n"
        "**Bootcamper:** Test Person\n\n"
        f"## {heading}\n\n"
        "### Information Shared\n\n- A thing was explained.\n\n"
        "### Questions & Responses\n\n- **Q:** Ready? **A:** Yes.\n\n"
        f"### Actions Taken\n\n- Did the work.{body_extra}\n\n"
        "### End-of-Module Summary\n\n"
        "**What you accomplished:** the work.\n\n"
        "**Files produced:** `data/x.jsonl`\n\n"
        "**Why it matters:** it matters.\n"
    )


def render(text, args=()):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "bootcamp_recap.md")
        out = os.path.join(tmp, "bootcamp_recap.pdf")
        with open(src, "w", encoding="utf-8") as handle:
            handle.write(text)
        proc = subprocess.run(
            [sys.executable, GENERATOR, "--input", src, "--output", out, *args],
            capture_output=True, text=True, cwd=tmp,
        )
        return proc.returncode, proc.stdout + proc.stderr


class MeasurementIsFolded(unittest.TestCase):
    """The class: no text reaches a width call without passing through `_safe`."""

    def test_no_raw_get_string_width_call_survives(self):
        with open(GENERATOR, encoding="utf-8") as handle:
            src = handle.read()
        body = src.split("def _width(", 1)[1]
        after = body.split("\n\n\n", 1)[1] if "\n\n\n" in body else body
        offenders = [
            line.strip()
            for line in after.split("\n")
            if "pdf.get_string_width(" in line and not line.lstrip().startswith("#")
        ]
        self.assertEqual(
            [], offenders,
            "measure through _width(pdf, text) — a raw get_string_width raises on the "
            "characters _safe exists to fold, killing the whole render",
        )

    @unittest.skipUnless(HAVE_FPDF, "fpdf2 not installed")
    def test_width_does_not_raise_on_unrepresentable_text(self):
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "", 10)
        # 李明 folds to "" — INV-159 forbids the plugin transliterating a non-Latin
        # script — so the width is legitimately 0. What matters is that it does not raise.
        for text in ("plain", "em — dash", "ellipsis …", "李明", "Łukasz", "a→b"):
            with self.subTest(text=text):
                width = G._width(pdf, text)
                self.assertIsInstance(width, (int, float))
                self.assertGreaterEqual(width, 0)

    @unittest.skipUnless(HAVE_FPDF, "fpdf2 not installed")
    def test_width_equals_the_width_of_what_gets_drawn(self):
        """Measuring the folded string is also the correct width, not just a safe one."""
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "", 10)
        raw = "Data Quality, Mapping, and Transformation — in progress"
        self.assertAlmostEqual(
            G._width(pdf, raw), pdf.get_string_width(G._safe(raw)), places=6
        )


class TheTitleSplitHandlesTheInProgressMarker(unittest.TestCase):
    def test_a_timestamp_still_splits(self):
        self.assertEqual(
            G._split_title_date("Data collection — 2026-01-01T11:00:00-07:00"),
            ("Data collection", "2026-01-01T11:00:00-07:00"),
        )

    def test_the_in_progress_marker_splits(self):
        self.assertEqual(
            G._split_title_date("Data Quality, Mapping, and Transformation — in progress"),
            ("Data Quality, Mapping, and Transformation", "in progress"),
        )

    def test_the_marker_is_matched_case_insensitively(self):
        self.assertEqual(G._split_title_date("Mod — In Progress")[0], "Mod")

    def test_an_arbitrary_suffix_still_does_not_split(self):
        """Narrower than loosening the date test: a real name keeping its em dash."""
        name = "Query, Visualize — and Discover"
        self.assertEqual(G._split_title_date(name), (name, ""))

    def test_a_hyphen_separator_also_works(self):
        self.assertEqual(G._split_title_date("Mod - in progress"), ("Mod", "in progress"))


@unittest.skipUnless(HAVE_FPDF, "fpdf2 not installed")
class TheRendererStaysOnFpdf2(unittest.TestCase):
    """End-to-end: with fpdf2 installed, `renderer: stdlib` means something crashed."""

    def assert_fpdf2(self, text, why):
        code, out = render(text)
        self.assertEqual(code, 0, out)
        self.assertIn("PDF generated:", out)
        self.assertNotIn("fpdf2 render failed", out, f"{why}\n{out}")
        self.assertIn("renderer: fpdf2", out, f"{why}\n{out}")

    def test_an_unfinalized_heading_renders_with_fpdf2(self):
        self.assert_fpdf2(
            recap_text("Data Quality, Mapping, and Transformation — in progress"),
            "the em dash in an unfinalized heading must not kill the render",
        )

    def test_a_non_latin1_module_title_renders_with_fpdf2(self):
        """Even a title _safe can only fold, not represent, must not crash measurement."""
        self.assert_fpdf2(
            recap_text("Módulo de Calidad — 2026-01-01T10:00:00-07:00"),
            "a folded title must still measure",
        )

    def test_non_latin1_body_content_renders_with_fpdf2(self):
        self.assert_fpdf2(
            recap_text(
                "Data collection — 2026-01-01T10:00:00-07:00",
                body_extra="\n- **Bold — prefix:** with an ellipsis … and 李明",
            ),
            "a bold prefix is measured before it is drawn",
        )


class CheckDoesNotCallAPresentSectionAbsent(unittest.TestCase):
    """INV-157: a false 'missing' sends graduation to backfill what is already there."""

    def test_an_unfinalized_section_is_found_by_expect_modules(self):
        text = recap_text("Data Quality, Mapping, and Transformation — in progress")
        code, out = render(
            text,
            args=("--check", "--expect-modules", "Data Quality, Mapping, and Transformation"),
        )
        self.assertNotIn("has no recap section at all", out, out)

    def test_a_genuinely_absent_module_is_still_reported(self):
        """The guard must not be satisfied by never reporting anything."""
        text = recap_text("Data collection — 2026-01-01T10:00:00-07:00")
        code, out = render(text, args=("--check", "--expect-modules", "Data processing"))
        self.assertIn("has no recap section at all", out, out)

    def test_check_and_render_agree_on_the_section_name(self):
        """The contradiction was one run calling the same section found and absent."""
        text = recap_text("Data Quality, Mapping, and Transformation — in progress")
        _, out = render(
            text,
            args=("--check", "--expect-modules", "Data Quality, Mapping, and Transformation"),
        )
        self.assertNotIn(
            "Transformation — in progress's",
            out,
            "the status suffix must not be part of the reported module name",
        )


if __name__ == "__main__":
    unittest.main()
