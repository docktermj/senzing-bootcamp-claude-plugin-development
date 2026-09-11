"""Tests for the recap PDF generator's content-loss guard.

`plugins/senzing-bootcamp/scripts/generate_recap_pdf.py` used to print
`PDF generated:` and exit 0 even when it had dropped essentially all of its
input — body text is kept only under a module section's `### ` sub-headings, so a
document with `## ` headings and no recognized sub-headings rendered as headings
with empty bodies. A success message plus a plausibly-sized PDF is the failure
nobody checks, so these tests pin the two outcome classes apart:

* recognizable but imperfect recap  -> warn, render, exit 0 (non-blocking)
* not a recap / catastrophic loss   -> no PDF, no success line, exit non-zero

Each case runs the generator as a subprocess (mirroring `test_write_gate.py`) so
the real exit code and the real stdout/stderr contract are asserted, not an
in-process approximation.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPT = os.path.join(PLUGIN, "scripts", "generate_recap_pdf.py")
EXAMPLE = os.path.join(PLUGIN, "docs", "examples", "bootcamp_recap.example.md")

SUCCESS_LINE = "PDF generated:"

# A minimal well-formed recap: one module section carrying all four sub-sections.
# Body text is deliberately long relative to the headings so retention stays high,
# which is what a real recap looks like.
GOOD_RECAP = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-07-20

## Entity Resolution Concepts — 2026-07-20T10:00:00-05:00

### Information Shared

Entity resolution distinguishes records that describe the same real-world thing
from records that merely look similar, which is the whole point of the exercise.

### Questions & Responses

- **Q:** What is a false positive?
- **A:** Two records merged into one entity that describe different real people.

### Actions Taken

- Completed the concepts primer and the optional knowledge check.

### End-of-Module Summary

**What you accomplished:** Built a working vocabulary for the hands-on modules that
follow this one, and confirmed the two failure modes with the knowledge check.

**Files produced:** (no files — conceptual primer)

**Why it matters:** Every later module builds on this vocabulary, so the mapping and
loading work has words for what it is doing.
"""

# H2 headings but no recognized H3 sub-headings: the shape of the discoveries
# document that originally produced a 6-page PDF containing none of its findings.
NON_RECAP = """# Bootcamp Data Discoveries

**Generated:** 2026-07-25

## Headline resolution numbers

3,986 entities resolved from 4,000 records. APM MEDICAL and ABSOLUTE DENTAL were
the two largest merges found in the loaded data.

## What was NOT found, and why

The two sources share only 8 organization names, so 4 cross-source merges is
near the achievable ceiling rather than a weak result.
"""


def run(markdown, args=(), env=None):
    """Render `markdown` in a temp dir; return (exit_code, stdout, stderr, pdf_exists)."""
    workdir = tempfile.mkdtemp()
    src = os.path.join(workdir, "recap.md")
    out = os.path.join(workdir, "recap.pdf")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--input", src, "--output", out, *args],
        capture_output=True, text=True, cwd=workdir, env=run_env,
    )
    return proc.returncode, proc.stdout, proc.stderr, os.path.exists(out)


def run_file(path, args=()):
    """Render an on-disk file (used for the shipped example recap)."""
    out = os.path.join(tempfile.mkdtemp(), "recap.pdf")
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--input", path, "--output", out, *args],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr, os.path.exists(out)


class NonRecapInputFails(unittest.TestCase):
    """The fatal class: refuse to render, and never claim success."""

    def test_exits_non_zero(self):
        code, _, _, _ = run(NON_RECAP)
        self.assertNotEqual(code, 0)

    def test_prints_no_success_line(self):
        # The graduation skill treats a `PDF generated:` line as success, so its
        # absence is the load-bearing assertion of this whole spec.
        _, stdout, _, _ = run(NON_RECAP)
        self.assertNotIn(SUCCESS_LINE, stdout)

    def test_writes_no_pdf(self):
        _, _, _, pdf_exists = run(NON_RECAP)
        self.assertFalse(pdf_exists)

    def test_names_the_structural_mismatch(self):
        _, _, stderr, _ = run(NON_RECAP)
        self.assertIn("does not look like a bootcamp recap", stderr)
        self.assertIn("sub-section", stderr)

    def test_reports_retention_figure(self):
        _, _, stderr, _ = run(NON_RECAP)
        self.assertIn("source characters", stderr)

    def test_no_module_sections_at_all_also_fails(self):
        code, stdout, _, pdf_exists = run("# Notes\n\nJust prose, no sections.\n")
        self.assertNotEqual(code, 0)
        self.assertNotIn(SUCCESS_LINE, stdout)
        self.assertFalse(pdf_exists)


class ValidRecapSucceeds(unittest.TestCase):
    """The non-blocking guarantee: a recognizable recap always renders."""

    def test_complete_recap_renders(self):
        code, stdout, _, pdf_exists = run(GOOD_RECAP)
        self.assertEqual(code, 0)
        self.assertIn(SUCCESS_LINE, stdout)
        self.assertTrue(pdf_exists)

    def test_success_line_reports_retention(self):
        _, stdout, _, _ = run(GOOD_RECAP)
        self.assertIn("source characters", stdout)

    def test_incomplete_recap_still_renders_and_exits_zero(self):
        # One missing sub-section is the "imperfect but recognizable" class: it
        # must warn and still ship the PDF, because graduation is non-blocking.
        incomplete = GOOD_RECAP.replace("### Actions Taken\n", "")
        code, stdout, stderr, pdf_exists = run(incomplete)
        self.assertEqual(code, 0)
        self.assertIn(SUCCESS_LINE, stdout)
        self.assertTrue(pdf_exists)
        self.assertIn("WARNING", stderr)

    def test_shipped_example_recap_renders(self):
        # Guards the retention threshold against false positives: the reference
        # recap must never trip the content-loss check.
        code, stdout, _, pdf_exists = run_file(EXAMPLE)
        self.assertEqual(code, 0)
        self.assertIn(SUCCESS_LINE, stdout)
        self.assertTrue(pdf_exists)


class RendererDowngradeIsNeverSilent(unittest.TestCase):
    """An unavailable fpdf2 must say which case it was, and name the interpreter."""

    def test_broken_install_is_reported(self):
        # A module that raises on import = installed but unusable. Shadowing it on
        # PYTHONPATH simulates that without touching the real environment.
        shim = tempfile.mkdtemp()
        with open(os.path.join(shim, "fpdf.py"), "w", encoding="utf-8") as fh:
            fh.write('raise ImportError("simulated broken fpdf2 install")\n')
        code, stdout, stderr, pdf_exists = run(GOOD_RECAP, env={"PYTHONPATH": shim})
        self.assertEqual(code, 0)                 # INV-066: a PDF is still produced
        self.assertTrue(pdf_exists)
        self.assertIn("could not be imported", stderr)
        self.assertIn(sys.executable, stderr)     # venv mismatch must be legible
        self.assertIn("renderer: stdlib", stdout)


class StdlibFallbackKeepsCertificate(unittest.TestCase):
    """INV-066 + INV-100: the fallback still ends in a landscape certificate."""

    def test_certificate_page_present_in_stdlib_render(self):
        shim = tempfile.mkdtemp()
        with open(os.path.join(shim, "fpdf.py"), "w", encoding="utf-8") as fh:
            fh.write('raise ImportError("force stdlib")\n')
        workdir = tempfile.mkdtemp()
        src = os.path.join(workdir, "recap.md")
        out = os.path.join(workdir, "recap.pdf")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(GOOD_RECAP)
        env = dict(os.environ, PYTHONPATH=shim)
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--input", src, "--output", out],
            capture_output=True, text=True, cwd=workdir, env=env,
        )
        self.assertEqual(proc.returncode, 0)
        with open(out, "rb") as fh:
            raw = fh.read().decode("latin-1")
        self.assertIn("Certificate of Completion", raw)
        landscape = [
            (w, h)
            for w, h in re.findall(r"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", raw)
            if float(w) > float(h)
        ]
        self.assertEqual(len(landscape), 1, "expected exactly one landscape page")


# A recap whose lists exercise every spacing decision at once: spaced subsections,
# the spaced "What you accomplished" label block, and the two deliberate exclusions.
# One rendered line is 5.5 mm ≈ 15.6 pt; the inter-item gap adds 2.4 mm ≈ 6.8 pt. A
# separation above this means "more than one line apart", i.e. the gap was emitted.
# Named rather than repeated as a bare 17.0, because it is the yardstick every spacing
# assertion in this file compares against — and because the whole defect is that a
# wrapped item's *internal* line spacing is indistinguishable from it without one.
_WRAPPED_ITEM_GAP_PT = 17.0

SPACING_RECAP = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-07-20
**Plugin version:** 9.9.9

## SDK setup — 2026-07-20T10:00:00-05:00

### Information Shared

- First shared item, long enough that it wraps onto a second rendered line so the
  gap between items has to be larger than the gap inside one item.
- Second shared item, also long enough to wrap across more than a single line in
  the rendered output of this subsection.
- Third and final shared item of this list.

### Questions & Responses

- **Q:** Which database would you like to use?
  - **R:** SQLite
- **Q:** Do you have a Senzing License Key?
  - **R:** No, request an evaluation license

### Actions Taken

- Created the SQLite database and schema at database/G2C.db.
- Created the engine configuration at config/engine_config.json.

### End-of-Module Summary

**What you accomplished:**
- Verified the SDK works end to end.
- Configured the database and engine.

**Files produced:**
- `artifacts/alpha-marker.db` — the SQLite database holding every resolved entity, its records and the relationships Senzing inferred between them during this module
- `artifacts/beta-marker.json` — the engine configuration, including the registered data sources and the resolution settings this module established
"""


def load_generator():
    """Import the generator as a module so its helpers can be unit-tested."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("recap_gen_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recap_gen_under_test"] = module
    spec.loader.exec_module(module)
    return module


def drawn_runs_by_page(path):
    """Drawn text runs grouped per page: ``[(page_width, [(x, y, text), ...]), ...]``.

    Needed wherever a bound depends on the page: the recap mixes orientations, since the
    Certificate of Completion is landscape (INV-100). Pages are read through the page
    tree's ``/Kids`` order and each page's own ``/Contents`` stream — never by walking
    every ``stream ... endstream`` in file order, because embedded images are streams too
    and counting one as a page silently shifts every later page's width.
    """
    import zlib

    with open(path, "rb") as handle:
        raw = handle.read()
    objects = {
        int(m.group(1)): m.group(2)
        for m in re.finditer(rb"(\d+) 0 obj\r?\n(.*?)\r?\nendobj", raw, re.S)
    }
    tree = next((b for b in objects.values() if b"/Type /Pages" in b), b"")
    kids = re.search(rb"/Kids \[(.*?)\]", tree, re.S)
    default = re.search(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", tree)
    pattern = re.compile(r"([\d.]+)\s+([\d.]+)\s+(?:Td|Tm)\b(.*?)\bTj", re.S)
    pages = []
    for number in (int(n) for n in re.findall(rb"(\d+) 0 R", kids.group(1) if kids else b"")):
        body = objects.get(number, b"")
        box = re.search(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", body) or default
        contents = re.search(rb"/Contents (\d+) 0 R", body)
        if not (box and contents):
            continue
        stream = re.search(
            rb"stream\r?\n(.*?)\r?\nendstream", objects.get(int(contents.group(1)), b""), re.S
        )
        if not stream:
            continue
        try:
            body = zlib.decompressobj().decompress(stream.group(1))
        except zlib.error:
            body = stream.group(1)
        runs = []
        for match in pattern.finditer(body.decode("latin-1", "replace")):
            text = re.findall(r"\((.*?)\)\s*$", match.group(3).strip())
            if text:
                runs.append(
                    (round(float(match.group(1)), 1), round(float(match.group(2)), 1), text[0])
                )
        pages.append((float(box.group(1)), runs))
    return pages


def drawn_runs(path):
    """Every drawn text run as (x, y, text) in points.

    Position is what distinguishes "rendered" from "present in the file", and it is the
    only way to measure spacing. A stream that will not decompress is kept raw rather
    than skipped — dropping it fabricates missing content (it did, during this
    implementation, and briefly looked like a lost module section).
    """
    import zlib

    with open(path, "rb") as handle:
        raw = handle.read()
    runs = []
    pattern = re.compile(r"([\d.]+)\s+([\d.]+)\s+(?:Td|Tm)\b(.*?)\bTj", re.S)
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S):
        body = match.group(1)
        # `decompressobj` decodes the valid prefix and tolerates a slice whose tail
        # is off by a few bytes; strict `decompress` raises on that, which silently
        # hid a whole page of text and looked exactly like a lost module section.
        try:
            body = zlib.decompressobj().decompress(body)
        except zlib.error:
            pass
        for run_match in pattern.finditer(body.decode("latin-1", "replace")):
            text = re.findall(r"\((.*?)\)\s*$", run_match.group(3).strip())
            if text:
                runs.append(
                    (round(float(run_match.group(1)), 1), round(float(run_match.group(2)), 1), text[0])
                )
    return runs


def render_to(markdown, args=()):
    """Render `markdown` and return the output PDF path (kept for inspection)."""
    workdir = tempfile.mkdtemp()
    src = os.path.join(workdir, "recap.md")
    out = os.path.join(workdir, "recap.pdf")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--input", src, "--output", out, *args],
        capture_output=True, text=True, cwd=workdir,
    )
    assert proc.returncode == 0, proc.stderr
    return out


class CertificateCarriesThePluginVersion(unittest.TestCase):
    """The certificate is the page most likely to be detached and shared on its own, so
    it has to say which plugin produced it."""

    def test_version_line_is_rendered(self):
        runs = drawn_runs(render_to(SPACING_RECAP))
        self.assertTrue(
            any("Senzing Bootcamp Claude plugin v9.9.9" == t for _x, _y, t in runs),
            "the certificate must name the plugin version from the header meta row",
        )

    def test_version_is_omitted_when_the_meta_row_is_absent(self):
        """Omit, never a placeholder — a certificate is permanently visible."""
        without = SPACING_RECAP.replace("**Plugin version:** 9.9.9\n", "")
        runs = drawn_runs(render_to(without))
        self.assertFalse(any("Claude plugin v" in t for _x, _y, t in runs))
        self.assertTrue(
            any(t.strip() == "Senzing Bootcamp" for _x, _y, t in runs),
            "the existing attribution line must survive",
        )

    def test_both_attribution_lines_clear_the_card_border(self):
        """A line laid over the card's ember border is sliced in half by the stroke.

        Text extraction reported the string present and correct while the glyphs were
        visually cut, so this asserts geometry, not presence. The bound is derived from
        the certificate's own constants rather than typed in, so moving the card moves
        the test with it.
        """
        module = load_generator()
        runs = drawn_runs(render_to(SPACING_RECAP))
        # Landscape A4 is 210 mm tall. The card's bottom edge is stroked, centered on the
        # path, so the ink reaches half a line width past it; both attribution lines must
        # sit above the top of that stroke.
        border_top = (
            210.0 - module._CERT_CARD_Y - module._CERT_CARD_H - module._CERT_BORDER / 2.0
        ) * 72.0 / 25.4
        attribution = [
            (y, t) for _x, y, t in runs
            if t.strip() == "Senzing Bootcamp" or "Claude plugin v" in t
        ]
        self.assertEqual(2, len(attribution), "expected exactly two attribution lines")
        for y, text in attribution:
            with self.subTest(text=text):
                # y is a PDF baseline in points from the page bottom.
                self.assertGreater(y, border_top, f"{text!r} is clipped by the border")
        self.assertEqual(2, len(module._cert_attribution(module.parse_recap(SPACING_RECAP))))

    def test_partition_meta_docstring_matches_the_code(self):
        """It used to claim identity rows drive the certificate; they do not."""
        module = load_generator()
        doc = re.sub(r"\s+", " ", module._partition_meta.__doc__ or "")
        self.assertIn("cover card", doc)
        self.assertRegex(doc, r"certificate does \*\*not\*\* consume this partition")


class ListItemsAreSpacedWhereItHelps(unittest.TestCase):
    """Bullets ended with no trailing gap, so the space between two items equaled the
    space inside one wrapped item and multi-line bullets ran together."""

    def setUp(self):
        self.module = load_generator()
        self.runs = drawn_runs(render_to(SPACING_RECAP))

    def _y_of(self, needle):
        for _x, y, text in self.runs:
            if needle in text:
                return y
        self.fail(f"{needle!r} was not drawn")

    def test_spacing_is_opt_out_not_opt_in(self):
        """Inverted 2026-07-31. The opt-in tuple was itself the defect: a list added
        or renamed later was silently unspaced, and that is how "Files produced" —
        the recap's index — shipped as an undifferentiated block."""
        self.assertEqual((), self.module._UNSPACED_SUBSECTIONS)
        self.assertEqual((), self.module._UNSPACED_LABELS)
        self.assertFalse(
            hasattr(self.module, "_SPACED_SUBSECTIONS"),
            "the opt-in constants must be gone, not merely unused — a leftover pair "
            "reads as the live mechanism",
        )
        self.assertFalse(hasattr(self.module, "_SPACED_LABELS"))

    def _stdlib_gaps(self, content, name="End-of-Module Summary"):
        """Drive the stdlib renderer in-process; return the emitted token kinds.

        The positional tests above measure the fpdf2 PDF, which `render_to` renders in
        a **subprocess** — so a constant patched in this process cannot reach it. The
        stdlib path takes plain callables, so it can be driven directly. That also
        makes these the only tests covering the second renderer's spacing, which
        INV-066 requires not to drift from the first.
        """
        tokens = []
        self.module._stdlib_subsection(
            lambda text, font, size, indent: tokens.append((font, text)),
            lambda text, font, size, indent: tokens.append(("WRAP", text)),
            name,
            content,
        )
        return tokens

    def test_the_opt_out_is_a_live_mechanism_not_dead_code(self):
        """An empty escape hatch is worth nothing unless it demonstrably works.

        Populating it must actually suppress the gap — otherwise the next maintainer
        who needs a tight list adds a name, sees no effect, and hard-codes something.
        """
        content = [
            "**Files produced:**",
            "- `a.db` — the database",
            "- `b.json` — the config",
        ]
        default = self._stdlib_gaps(content)
        self.assertIn("GAP", [f for f, _ in default], "spacing must be on by default")

        self.module._UNSPACED_LABELS = ("files produced",)
        try:
            opted_out = self._stdlib_gaps(content)
        finally:
            self.module._UNSPACED_LABELS = ()
        self.assertNotIn(
            "GAP",
            [f for f, _ in opted_out],
            "naming a label in _UNSPACED_LABELS must suppress its gaps",
        )

    def test_the_subsection_opt_out_works_too(self):
        content = ["- first item", "- second item"]
        self.assertIn("GAP", [f for f, _ in self._stdlib_gaps(content, "Actions Taken")])

        self.module._UNSPACED_SUBSECTIONS = ("actions taken",)
        try:
            opted_out = self._stdlib_gaps(content, "Actions Taken")
        finally:
            self.module._UNSPACED_SUBSECTIONS = ()
        self.assertNotIn("GAP", [f for f, _ in opted_out])

    def test_the_stdlib_renderer_keeps_a_response_with_its_question(self):
        """INV-066: the second renderer must not drift from the first.

        Asserted here because the positional PDF tests only exercise fpdf2.
        """
        tokens = self._stdlib_gaps(
            [
                "- **Q:** first question",
                "    - **R:** first answer",
                "- **Q:** second question",
                "    - **R:** second answer",
            ],
            "Questions & Responses",
        )
        kinds = [f for f, _ in tokens]
        # Exactly one gap: after the first answer, before the second question.
        self.assertEqual(
            1, kinds.count("GAP"), "expected one gap between the two Q/R pairs"
        )
        gap_at = kinds.index("GAP")
        self.assertIn("first answer", tokens[gap_at - 1][1])
        self.assertIn("second question", tokens[gap_at + 1][1])

    def test_the_fpdf2_path_also_spaces_a_source_wrapped_item(self):
        """The same continuation fix, asserted against the real PDF geometry.

        Added because a mutation reverting *only* the fpdf2 path's gap condition to
        `_is_bullet(line)` broke nothing: the stdlib tests below cover the rule, and
        the other positional tests all use single-source-line items. Information
        Shared's fixture items wrap across source lines, so they are the shape that
        exercises it — and INV-066 requires the two renderers not to drift.
        """
        internal = self._y_of("First shared item") - self._y_of(
            "gap between items has to be"
        )
        self.assertGreater(internal, 0, "item 1 must span two rendered lines")
        tail_to_next = self._y_of("gap between items has to be") - self._y_of(
            "Second shared item"
        )
        self.assertGreater(
            tail_to_next,
            internal * 1.2,
            "a source-wrapped item must be separated from the next in the fpdf2 "
            "renderer too, not just the stdlib fallback",
        )

    def test_a_source_wrapped_item_still_gets_its_gap(self):
        """A latent defect this spec's assertion exposed (2026-07-31).

        The gap used to be decided on the bullet line, asking "is the next *source*
        line another item?" For a bullet whose Markdown wraps across two source lines
        the answer is no — it is that item's own continuation — so such an item got
        **no gap at all**. It stayed invisible because the shipped example recap writes
        every entry as one long source line and lets the renderer wrap it, so no
        fixture exercised the shape.

        Pre-existing, not introduced here: the same shape held under the opt-in rule.
        """
        wrapped = [
            "- first item that runs long and",
            "  continues on this source line",
            "- second item",
        ]
        self.assertEqual(
            1,
            [f for f, _ in self._stdlib_gaps(wrapped, "Information Shared")].count("GAP"),
            "an item whose Markdown wraps across source lines must still be separated "
            "from the next item",
        )

    def test_the_gap_lands_after_the_items_last_source_line(self):
        """Not after its first — otherwise it falls *inside* the item."""
        tokens = self._stdlib_gaps(
            ["- first item and", "  its continuation", "- second item"],
            "Information Shared",
        )
        kinds = [f for f, _ in tokens]
        gap_at = kinds.index("GAP")
        self.assertIn("its continuation", tokens[gap_at - 1][1])
        self.assertIn("second item", tokens[gap_at + 1][1])

    def test_a_blank_line_closes_the_item(self):
        self.assertFalse(self.module._still_in_list_item("", True))
        self.assertTrue(self.module._still_in_list_item("  continuation", True))
        self.assertFalse(
            self.module._still_in_list_item("  continuation", False),
            "an indented line only continues an item that was already open",
        )
        self.assertFalse(
            self.module._still_in_list_item("**Files produced:**", True),
            "an unindented label closes the list above it",
        )

    def test_a_two_space_indent_is_also_treated_as_a_sub_bullet(self):
        """The template mandates four spaces, but a recap written with two must not
        have its answers torn away from their questions — that is the regression the
        original blanket exclusion existed to prevent."""
        for indent in ("  ", "    ", "\t"):
            with self.subTest(indent=repr(indent)):
                self.assertFalse(
                    self.module._is_top_level_bullet(f"{indent}- **R:** an answer")
                )
        self.assertTrue(self.module._is_top_level_bullet("- **Q:** a question"))

    def test_action_taken_singular_is_covered_by_the_opt_out(self):
        """INV-048 names it singular; every surface uses the plural. The normalization
        still has to hold, or an opt-out written either way would silently miss."""
        self.assertEqual(
            self.module._normalize_heading("Action Taken"),
            self.module._normalize_heading("Actions Taken"),
        )

    @requires_fpdf2
    def test_consecutive_actions_taken_items_are_more_than_one_line_apart(self):
        first = self._y_of("Created the SQLite database")
        second = self._y_of("Created the engine configuration")
        gap = first - second
        # One line is 5.5 mm ≈ 15.6 pt; the item gap adds 2.4 mm ≈ 6.8 pt.
        self.assertGreater(
            gap, _WRAPPED_ITEM_GAP_PT, "Actions Taken items are still one line apart"
        )

    def test_question_and_response_stay_together(self):
        """Spacing here would separate each answer from the question it answers."""
        question = self._y_of("Which database would you like to use")
        response = self._y_of("SQLite")
        self.assertLess(
            question - response,
            _WRAPPED_ITEM_GAP_PT,
            "Q/R pairing must not be broken by item spacing",
        )

    def test_files_produced_wrapped_items_are_separated(self):
        """⚠️ Reverses `test_files_produced_list_stays_tight` (2026-07-31).

        That test asserted the opposite, on the originating spec's stated premise that
        "Files produced" is "a short reference list of one-line paths". The premise is
        false: `bootcamp-onboarding/module-completion.md:83` templates every entry as
        `` - `{path}` — {what it is} `` and its line 98 makes the gloss a ⛔
        requirement, so real recaps run 5-12 items at 110-188 characters. Measured
        across the reporting run's nine sections, every one had items that wrap.

        The assertion is the exact condition the generator's own comment describes: a
        wrapped item ends with no trailing gap, so the space between two items equals
        the space *inside* one, and multi-line entries run together. Comparing against
        a wrapped item's own internal line spacing is what makes this catch the real
        defect — a character count cannot see it, and neither can a gap threshold
        measured on single-line items.

        ⚠️ The comparison must be **last line of item 1 → first line of item 2**, not
        first-line-to-first-line. A wrapped item spans two lines whatever the spacing,
        so a first-to-first measurement clears any fixed threshold even with the gap
        switched off — the first draft of this test did exactly that and would have
        passed vacuously. The yardstick is the item's own internal line spacing,
        measured from the same render.
        """
        internal = self._y_of("artifacts/alpha-marker.db") - self._y_of(
            "relationships Senzing inferred"
        )
        self.assertGreater(
            internal, 0, "item 1 must actually render-wrap for this to mean anything"
        )
        tail_to_next = self._y_of("relationships Senzing inferred") - self._y_of(
            "artifacts/beta-marker.json"
        )
        self.assertGreater(
            tail_to_next,
            internal * 1.2,
            "'Files produced' is the recap's index — the list a reader uses to find "
            "what the bootcamp built — so it is the worst one to render as a block. "
            "The space after an item's last line must exceed the space between that "
            "item's own wrapped lines, or the entries still run together.",
        )

    @requires_fpdf2
    def test_question_and_response_pairs_are_separated_from_each_other(self):
        """Spacing Q&R top-level bullets was the other half of the reversal.

        The originating spec excluded the whole subsection, correctly arguing against
        splitting a response from its question — but that argument does not reach the
        top-level `- **Q:**` items, which ran together with no separation between one
        pair and the next.
        """
        first_response = self._y_of("SQLite")
        next_question = self._y_of("Do you have a Senzing License Key")
        self.assertGreater(
            first_response - next_question,
            _WRAPPED_ITEM_GAP_PT,
            "one Q/R pair must be visibly separated from the next",
        )

    @requires_fpdf2
    def test_accomplishments_list_is_spaced(self):
        first = self._y_of("Verified the SDK works end to end")
        second = self._y_of("Configured the database and engine")
        self.assertGreater(first - second, _WRAPPED_ITEM_GAP_PT)

    def test_gap_is_between_items_never_after_the_last(self):
        lines = [
            "- first item",
            "- second item",
            "",
            "not a bullet",
        ]
        self.assertTrue(self.module._next_nonblank_is_bullet(lines, 0))
        self.assertFalse(self.module._next_nonblank_is_bullet(lines, 1))
        self.assertFalse(self.module._next_nonblank_is_bullet(lines, 3))

    def test_block_label_only_matches_a_standalone_label(self):
        """A bullet carrying `- **Q:**` must not switch spacing on."""
        self.assertEqual(
            "what you accomplished", self.module._block_label("**What you accomplished:**")
        )
        self.assertEqual("", self.module._block_label("- **Q:** a question"))

    def test_content_is_not_lost_to_the_added_spacing(self):
        """INV-110/INV-121: extra vertical space must never push content out."""
        for probe in (
            "First shared item",
            "Third and final shared item",
            "Created the engine configuration",
            "Verified the SDK works end to end",
            "config/engine_config.json",
        ):
            with self.subTest(probe=probe):
                self.assertTrue(any(probe in t for _x, _y, t in self.runs))


class StdlibFallbackMatchesTheFpdf2Certificate(unittest.TestCase):
    """The two renderers must not drift on the certificate footer."""

    def test_stdlib_certificate_carries_the_version_line(self):
        module = load_generator()
        recap = module.parse_recap(SPACING_RECAP)
        stream = module._stdlib_certificate_stream(recap, 842.0, 595.0)
        self.assertIn("Senzing Bootcamp Claude plugin v9.9.9", stream)
        self.assertIn("Senzing Bootcamp", stream)

    def test_stdlib_certificate_omits_an_absent_version(self):
        module = load_generator()
        recap = module.parse_recap(SPACING_RECAP.replace("**Plugin version:** 9.9.9\n", ""))
        stream = module._stdlib_certificate_stream(recap, 842.0, 595.0)
        self.assertNotIn("Claude plugin v", stream)
        self.assertIn("Senzing Bootcamp", stream)

    def test_stdlib_gap_token_emits_no_text_operator(self):
        """A GAP token is pure vertical space; it must not reference a font."""
        module = load_generator()
        recap = module.parse_recap(SPACING_RECAP)
        out = os.path.join(tempfile.mkdtemp(), "stdlib.pdf")
        self.assertTrue(module.render_with_stdlib(recap, __import__("pathlib").Path(out)))
        with open(out, "rb") as handle:
            raw = handle.read().decode("latin-1")
        self.assertNotIn("/GAP", raw, "the gap sentinel must never reach the PDF")
        self.assertIn("Certificate of Completion", raw)


class CheckModeContract(unittest.TestCase):
    """`--check` keeps its exit semantics: 0 when complete, non-zero on any gap."""

    def test_complete_recap_passes_check(self):
        code, stdout, _, _ = run(GOOD_RECAP, args=("--check",))
        self.assertEqual(code, 0)
        self.assertIn("Recap complete", stdout)

    def test_incomplete_recap_fails_check(self):
        incomplete = GOOD_RECAP.replace("### Actions Taken\n", "")
        code, _, stderr, _ = run(incomplete, args=("--check",))
        self.assertNotEqual(code, 0)
        self.assertIn("INCOMPLETE", stderr)

    def test_check_does_not_write_a_pdf(self):
        _, _, _, pdf_exists = run(GOOD_RECAP, args=("--check",))
        self.assertFalse(pdf_exists)


class UnfinalizedModuleIsReported(unittest.TestCase):
    """A missed module-completion step 2d must not pass silently.

    Step 2d appends the finalized `## {Name}` section and then removes the
    durability hooks' folded `<!-- RECAP-CHECKPOINT -->` block. Skipping the
    removal leaves two copies of the module, and the markers are HTML comments
    that the renderers drop — so the keepsake PDF renders the module twice with
    nothing on stderr to say why. Neither symptom blocks graduation (INV-110
    keeps a recognizable recap renderable), but both must be *reported*.
    """

    def duplicated(self):
        """GOOD_RECAP with its module section repeated."""
        head, sep, body = GOOD_RECAP.partition("## Entity Resolution Concepts")
        return head + sep + body + "\n" + sep + body

    def with_marker_block(self):
        head, sep, body = GOOD_RECAP.partition("## Entity Resolution Concepts")
        return (
            head
            + "<!-- RECAP-CHECKPOINT:START -->\n\n"
            + sep
            + body
            + "\n<!-- RECAP-CHECKPOINT:END -->\n"
        )

    def test_duplicate_section_fails_check(self):
        code, _, stderr, _ = run(self.duplicated(), args=("--check",))
        self.assertNotEqual(code, 0, "a duplicated module section must fail --check")
        self.assertIn("more than one recap section", stderr)

    def test_duplicate_section_still_renders_but_warns(self):
        """Non-blocking: graduation still gets its PDF (INV-048/INV-110)."""
        code, stdout, stderr, pdf_exists = run(self.duplicated())
        self.assertEqual(code, 0, stderr)
        self.assertIn(SUCCESS_LINE, stdout)
        self.assertTrue(pdf_exists)
        self.assertIn("more than one recap section", stderr)

    def test_stray_checkpoint_block_fails_check(self):
        code, _, stderr, _ = run(self.with_marker_block(), args=("--check",))
        self.assertNotEqual(code, 0, "a surviving checkpoint block must fail --check")
        self.assertIn("RECAP-CHECKPOINT", stderr)

    def test_stray_checkpoint_block_still_renders_but_warns(self):
        code, stdout, stderr, pdf_exists = run(self.with_marker_block())
        self.assertEqual(code, 0, stderr)
        self.assertIn(SUCCESS_LINE, stdout)
        self.assertTrue(pdf_exists)
        self.assertIn("RECAP-CHECKPOINT", stderr)

    def test_markers_match_the_hook_that_writes_them(self):
        """The renderer's fence constants must equal recap_checkpoint.py's."""
        import re

        def constants(path):
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            return set(re.findall(r'"(<!-- RECAP-CHECKPOINT:(?:START|END) -->)"', text))

        hook = os.path.join(PLUGIN, "scripts", "recap_checkpoint.py")
        self.assertEqual(
            constants(hook),
            constants(SCRIPT),
            "the fold hook and the renderer disagree on the checkpoint markers, "
            "so the renderer would stop detecting unfinalized modules",
        )

    def test_clean_recap_reports_neither(self):
        code, _, stderr, _ = run(GOOD_RECAP, args=("--check",))
        self.assertEqual(code, 0, stderr)
        self.assertNotIn("more than one recap section", stderr)
        self.assertNotIn("RECAP-CHECKPOINT", stderr)


TABLE_RECAP = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-07-27T10:00:00-04:00
**Plugin version:** 9.9.9

---

## Data processing - 2026-07-27T11:00:00-04:00

### Information Shared
- Match-key frequency across the loaded sources:

| Match key | Count |
|---|---|
| +NAME+ADDRESS | 412 |
| +RAGGED |
| +NAME+PHONE | 88 | extra |

### Questions & Responses
- **Q:** Ready to load?
    - **R:** Yes

### Actions Taken
- Loaded 23,152 records.

### End-of-Module Summary
**What you accomplished:**
- Loaded and resolved every source.

**Files produced:**
- `src/load/load_all.py` - the loader

**Why it matters:** The data is resolved.

---
"""


class TablesInTheRecapRenderAsTables(unittest.TestCase):
    """A Markdown table in a recap section is drawn, not printed as its source.

    INV-142 binds "a bundled generator", not one of them. The fix landed in
    `generate_discoveries_pdf.py` only, so this generator kept emitting pipe rows as
    literal text — `|---|---|` alignment row and all — into the crown-jewel keepsake,
    while `PDF generated:`, exit 0 and a 91% retention figure all reported success.
    The characters *were* in the content stream; they just did not render as a table,
    which is precisely what a retention count cannot see.
    """

    @classmethod
    def setUpClass(cls):
        cls.pdf = render_to(TABLE_RECAP)
        cls.runs = drawn_runs(cls.pdf)
        cls.texts = [t.strip() for _x, _y, t in cls.runs]

    def test_no_raw_pipe_source_survives(self):
        offenders = [t for t in self.texts if t.startswith("|") or "|---" in t]
        self.assertEqual(
            [], offenders, f"raw Markdown table source drawn into the recap PDF: {offenders[:5]}"
        )

    def test_the_alignment_row_is_dropped(self):
        self.assertNotIn("---", self.texts)

    @requires_fpdf2
    def test_cells_are_drawn_as_separate_runs(self):
        """A grid means one run per cell, not one run per source line."""
        for cell in ("Match key", "Count", "+NAME+ADDRESS", "412", "+NAME+PHONE", "88"):
            with self.subTest(cell=cell):
                self.assertIn(cell, self.texts, f"{cell!r} is not its own drawn cell")

    def test_a_ragged_row_does_not_desynchronize_the_grid(self):
        """Short rows are padded and over-long rows truncated to the header width."""
        self.assertIn("+RAGGED", self.texts, "the short row vanished")
        self.assertNotIn("extra", self.texts, "a 3rd cell rendered in a 2-column grid")

    def test_every_cell_renders_inside_the_text_column(self):
        """Positional, not presence: off-page content extracts fine (INV-121/INV-129)."""
        margin = 10.0
        # Per page, not one fixed width: the recap mixes orientations (INV-100), so a
        # portrait bound would report the landscape certificate's right-hand signature
        # block as off-page.
        offenders = [
            (x, text)
            for page_w, runs in drawn_runs_by_page(self.pdf)
            for x, _y, text in runs
            if x < margin or x > page_w - margin
        ]
        self.assertEqual([], offenders, f"text drawn outside the page: {offenders[:5]}")

    def test_the_stdlib_fallback_also_renders_a_table(self):
        """INV-142 binds both renderers; the fallback may align columns but never
        emit pipe source. It needs a monospace face to align at all."""
        gen = load_generator()
        import pathlib

        out = pathlib.Path(tempfile.mkdtemp()) / "stdlib.pdf"
        self.assertTrue(gen.render_with_stdlib(gen.parse_recap(TABLE_RECAP), out))
        texts = [t.strip() for _x, _y, t in drawn_runs(str(out))]
        self.assertEqual(
            [], [t for t in texts if t.startswith("|") or "|---" in t],
            "the stdlib fallback emitted raw pipe source",
        )
        self.assertTrue(
            any("Match key" in t and "Count" in t for t in texts),
            "the header cells are not laid out as a row",
        )
        with open(out, "rb") as handle:
            self.assertIn(
                b"/Courier", handle.read(),
                "space-padded columns in a proportional face are not aligned columns",
            )


if __name__ == "__main__":
    unittest.main()
