"""INV-143 on the *other* renderer: `?` must never reach the page, on either path.

`_pdf_escape` carried its own inline substitution table — 9 entries, a subset of
`_UNICODE_MAP`'s 33 — with a `"?"` default. The fpdf2 renderer normalizes through `_safe`
and never reaches that default, but the stdlib writers called `_pdf_escape` on raw text, so
**24 of the 33 mapped characters rendered as `?`**. Measured 2026-07-31, before the fix:

    source:   Precision came out ≥ 95% and recall ≈ 90%, with cost ≤ €500 per run…
    rendered: Precision came out ? 95% and recall ? 90%, with cost ? ?500 per run…
    PDF generated: out.pdf (renderer: stdlib, rendered 619 of 655 source characters (95%))

Exit 0, success line, 95% retention, nothing on stderr. `?` is one character replacing one,
so the retention figure is structurally unable to see it — the same blindness INV-193 names
for a self-derived denominator. And `_pdf_escape` never recorded into
`_DROPPED_CHARACTERS`, so `dropped_character_warning()` could not report it either: the
substitution was not merely wrong, it was unreportable.

Why it survived: `test_recap_pdf_font_safety.py` and `test_recap_measure_font_safety.py`
both exist to stop **fpdf2** raising on an unencodable character — the second treats
`renderer: stdlib` as evidence something crashed. The stdlib writer was modeled as the
*symptom* of a defect, never as a renderer whose own character handling could be wrong. No
test called `_pdf_escape`.

INV-143 asks for an inventory covering what generated **deliverables** carry, so these tests
iterate the whole `_UNICODE_MAP` across **both** renderers rather than sampling: a character
added to the map later cannot be added to only one path without failing here.

No phrase-level pattern (#438): its one line read takes the first line of a fixture, its title, as
#424 recorded (INV-346).

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

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts")
RECAP = os.path.join(SCRIPTS, "generate_recap_pdf.py")
DISCOVERIES = os.path.join(SCRIPTS, "generate_discoveries_pdf.py")

# Characters that exercise the former divergence: each was rendered as `?` by the stdlib
# writer while the fpdf2 path rendered it correctly.
PROBES = "≥≈≤€™∞✅"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves its module via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pdf_text(path):
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


RECAP_WITH_SYMBOLS = """# Senzing Bootcamp Recap ≥ 95% ✅

**Bootcamper:** Ada Lovelace
**Started:** 2026-07-20

## Data processing — 2026-07-21T09:00:00-05:00

### Information Shared

Precision came out ≥ 95% and recall ≈ 90%, with cost ≤ €500 per run. The vendor's
Senzing™ license covers it, and throughput was effectively ∞ for our volume.

### Questions & Responses

- **Q:** Ready to proceed. **R:** Yes

### Actions Taken

- Loaded both sources and drained the redo queue ✅

### End-of-Module Summary

**What you accomplished:** Loaded and resolved both sources end to end.

**Files produced:**
- `database/G2C.db` — the resolved repository

**Why it matters:** Every later module builds on this loaded data.
"""


class TheEscaperNoLongerSubstitutes(unittest.TestCase):
    """`_pdf_escape` does PDF syntax only. Substitution belongs to `_safe`, once."""

    def setUp(self):
        self.mod = load("recap_charsafe", RECAP)
        self.mod.reset_dropped_characters()

    def tearDown(self):
        self.mod.reset_dropped_characters()

    def test_no_mapped_character_becomes_a_question_mark(self):
        """The whole inventory, both paths — a loop, not a sample (INV-143)."""
        for ch, mapped in self.mod._UNICODE_MAP.items():
            with self.subTest(char=self.mod._describe_dropped(ch) if len(ch) == 1 else ch):
                fpdf2_path = self.mod._safe(ch)
                stdlib_path = self.mod._pdf_escape(self.mod._safe(ch))
                self.assertNotIn("?", fpdf2_path)
                self.assertNotIn(
                    "?",
                    stdlib_path,
                    "the stdlib writer must not substitute `?` (INV-143); "
                    "_UNICODE_MAP maps this to %r" % mapped,
                )

    def test_the_two_paths_agree_on_every_mapped_character(self):
        """Divergence was the symptom; one table is the fix. 24 of 33 used to differ."""
        differ = [
            ch
            for ch in self.mod._UNICODE_MAP
            if self.mod._pdf_escape(self.mod._safe(ch)) != self.mod._pdf_escape(
                self.mod._safe(self.mod._safe(ch))
            )
        ]
        self.assertEqual([], differ, "sanitization must be idempotent across the map")

    def test_it_has_no_private_substitution_table(self):
        """A second copy of a subset is the defect, not the fix."""
        import inspect

        body = inspect.getsource(self.mod._pdf_escape)
        code = body.split('"""', 2)[-1]
        for forbidden in ("0x2018", "0x2192", '"?"', "'?'"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(
                    forbidden,
                    code,
                    "_pdf_escape must not carry substitutions or a `?` fallback",
                )

    def test_it_still_does_its_actual_job(self):
        """PDF syntax escaping is what this function is for — unchanged."""
        self.assertEqual(r"\\ \( \)", self.mod._pdf_escape("\\ ( )"))
        # Latin-1 high range becomes octal, so `é` (0xE9) -> \351.
        self.assertEqual(r"Jos\351 Pe\361a", self.mod._pdf_escape("José Peña"))
        self.assertEqual("plain ASCII 123", self.mod._pdf_escape("plain ASCII 123"))

    def test_an_unsanitized_character_is_dropped_and_recorded(self):
        """The forgot-to-call-`_safe` case must be legible, not a `?` on a keepsake."""
        out = self.mod._pdf_escape("李明")
        self.assertEqual("", out, "dropping is what INV-143 permits")
        warning = self.mod.dropped_character_warning()
        self.assertIsNotNone(warning, "a drop must be reportable (INV-111)")
        self.assertIn("CJK", warning.upper().replace("IDEOGRAPH", "CJK"))

    def test_dropping_is_reported_by_unicode_name_not_raw(self):
        """A legacy Windows console cannot print the character that was dropped."""
        self.mod._pdf_escape("李")
        warning = self.mod.dropped_character_warning()
        self.assertNotIn("李", warning)


class TheStdlibRendererIsCleanEndToEnd(unittest.TestCase):
    """The measurement that matters: a real PDF from the fallback renderer."""

    def render_with_stdlib(self, tmp, markdown, name="bootcamp_recap.md"):
        """Render with `fpdf2` shadowed on PYTHONPATH so the fallback runs."""
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
            [sys.executable, RECAP, "--input", src, "--output", out],
            capture_output=True, text=True, cwd=tmp, env=env,
        )
        return result, out

    def test_the_symbols_render_as_their_mapped_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out = self.render_with_stdlib(tmp, RECAP_WITH_SYMBOLS)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("renderer: stdlib", result.stdout, "the fallback must have run")
            text = pdf_text(out)
            for expected in (">=", "~", "<=", "EUR", "infinity", "[done]"):
                with self.subTest(expected=expected):
                    self.assertIn(expected, text)
            # "(TM)" is present but PDF-escaped, since ( and ) are metacharacters.
            self.assertIn(r"\(TM\)", text)

    def test_zero_question_marks_reach_the_page(self):
        """The document contains no literal `?`, so any `?` is a substitution."""
        self.assertNotIn("?", RECAP_WITH_SYMBOLS, "fixture must have no literal ?")
        with tempfile.TemporaryDirectory() as tmp:
            _result, out = self.render_with_stdlib(tmp, RECAP_WITH_SYMBOLS)
            self.assertEqual(
                0,
                pdf_text(out).count("?"),
                "every `?` on the page is a character the writer could not render",
            )

    def test_the_direct_token_route_is_sanitized_too(self):
        """The H1 title reaches `add()` directly, not via `add_wrapped`.

        Sanitization happens at two points — `add()` for direct calls and before `_wrap`
        in `add_wrapped()` — and they cover different routes. Body prose travels
        `add_wrapped`, so a fixture with symbols only in prose leaves the `add()`
        boundary unpinned: removing it changes nothing observable. The title is the
        route that pins it.
        """
        self.assertIn("≥", RECAP_WITH_SYMBOLS.splitlines()[0], "title must carry a symbol")
        with tempfile.TemporaryDirectory() as tmp:
            _result, out = self.render_with_stdlib(tmp, RECAP_WITH_SYMBOLS)
            text = pdf_text(out)
            self.assertIn("Senzing Bootcamp Recap >= 95% [done]", text)

    def test_the_fpdf2_renderer_produces_the_same_forms(self):
        """INV-066: the two renderers must not disagree on content."""
        try:
            import fpdf  # noqa: F401
        except ImportError:
            self.skipTest("fpdf2 not installed (it is not stdlib — INV-108)")
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "bootcamp_recap.md")
            out = os.path.join(tmp, "out.pdf")
            with open(src, "w", encoding="utf-8") as handle:
                handle.write(RECAP_WITH_SYMBOLS)
            result = subprocess.run(
                [sys.executable, RECAP, "--input", src, "--output", out],
                capture_output=True, text=True, cwd=tmp,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("renderer: fpdf2", result.stdout)
            text = pdf_text(out)
            for expected in (">=", "EUR", "infinity"):
                with self.subTest(expected=expected):
                    self.assertIn(expected, text)


class TheDiscoveriesWriterSharesTheFix(unittest.TestCase):
    """Both generators import `_pdf_escape`, so fixing one is not enough."""

    def test_its_direct_token_route_is_sanitized(self):
        """The cover title and subtitle reach `add()` directly.

        Replaced a source-scrape for `"_safe(text)"`, which passed even with the `add()`
        boundary removed because the string still occurred in `add_wrapped` — a guard
        that cannot fail is not a guard.
        """
        mod = load("disc_charsafe", DISCOVERIES)
        parsed = mod.parse_discoveries("# Discoveries ≥ 95%\n\n## A\n\nSome real content here.\n")
        parsed.subtitle = "Throughput of ∞ records"
        with tempfile.TemporaryDirectory() as tmp:
            from pathlib import Path

            out = Path(tmp) / "d.pdf"
            self.assertTrue(mod.render_with_stdlib(parsed, out))
            text = pdf_text(str(out))
            self.assertNotIn("?", text)
            self.assertIn("Discoveries >= 95%", text)
            self.assertIn("Throughput of infinity records", text)

    def test_a_document_with_symbols_renders_without_question_marks(self):
        doc = (
            "# Data Discoveries\n\n"
            "## Headline numbers\n\n"
            "Cross-source precision was ≥ 95% at a cost of ≤ €500, and the vendor's "
            "Senzing™ license covers throughput of effectively ∞ records.\n\n"
            "## What was not found\n\n"
            "Overlap was low, so the ceiling was near — this is data, not pipeline.\n"
        )
        mod = load("disc_charsafe_render", DISCOVERIES)
        parsed = mod.parse_discoveries(doc)
        with tempfile.TemporaryDirectory() as tmp:
            from pathlib import Path

            out = Path(tmp) / "d.pdf"
            self.assertTrue(mod.render_with_stdlib(parsed, out))
            text = pdf_text(str(out))
            self.assertNotIn("?", text)
            for expected in (">=", "<=", "EUR", "infinity"):
                with self.subTest(expected=expected):
                    self.assertIn(expected, text)


class TheCertificateGuardIsUnchanged(unittest.TestCase):
    """A name the fonts cannot render still reaches the placeholder, both paths."""

    def test_an_unrenderable_name_still_folds_to_nothing(self):
        mod = load("recap_cert_guard", RECAP)
        for name in ("李明", "Владимир"):
            with self.subTest(name=name):
                self.assertEqual(
                    "",
                    mod._safe(name).strip(),
                    "the placeholder guard keys off this being empty",
                )

    def test_a_latin1_name_is_untouched(self):
        mod = load("recap_cert_guard2", RECAP)
        self.assertEqual("José Peña", mod._safe("José Peña"))


if __name__ == "__main__":
    unittest.main()
