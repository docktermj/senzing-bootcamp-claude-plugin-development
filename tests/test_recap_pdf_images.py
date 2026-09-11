"""Tests that recap screenshots reach the PDF, and that a lost one is audible.

`plugins/senzing-bootcamp/scripts/generate_recap_pdf.py` resolved a relative
`![alt](path)` against `Path.cwd()`. Graduation Step 1a writes those paths relative
to `docs/bootcamp_recap.md` — what every Markdown renderer expects — and Step 1b runs
the generator from the project root, so `visualizations/x.png` was looked for at
`<project>/visualizations/x.png` while the file sat at `<project>/docs/visualizations/`.
Every image was dropped, and the success line still reported ~99% of characters
rendered, because the characters did render. Six of the bootcamper's screenshots
vanished from the keepsake with no error, no warning, and a success message.

These tests pin the fix and the reporting that makes the failure class visible:

* document-relative paths embed when rendering from the project root (the real
  invocation), from the recap's own directory, and via an absolute `--input`
* a missing image is reported on stderr, once, naming where it looked — and the PDF
  is still written and still exits 0 (INV-048/INV-111)
* the success line carries `embedded N of M images`, which retention cannot see
  (INV-110)
* `--check` flags an unresolvable image target without rendering
* a remote URL is never fetched (INV-081)

Each case runs the generator as a subprocess so the real exit code and the real
stdout/stderr contract are asserted, not an in-process approximation.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPT = os.path.join(PLUGIN, "scripts", "generate_recap_pdf.py")

SUCCESS_LINE = "PDF generated:"
TABS = ["stats", "entity-graph", "merge-statistics", "match-keys", "feature-scores", "search"]


def _png_bytes(width=160, height=120):
    """A small, genuinely valid PNG (no Pillow needed to author it)."""
    raw = b"".join(b"\x00" + bytes((0x0D, 0x5F, 0x9E)) * width for _ in range(height))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def _recap_markdown(image_lines):
    return """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace

## Query, Visualize and Discover

### Information Shared

The visualization served every tab over the resolved data, which is the evidence
that entity resolution actually ran on this workstation rather than in theory.

### Questions & Responses

- **Q:** Would you like an interactive visualization of your resolved data?
- **A:** Yes, and the screenshots should reach the recap.

### Actions Taken

- Built the visualization, verified the server, and captured every tab in order.

{images}

### End-of-Module Summary

**What you accomplished:** Queried, visualized and explored the resolved entities,
and kept the screenshots as evidence in the recap.

**Files produced:** `docs/visualizations/results_visualization.html`

**Why it matters:** Seeing the resolution is what makes the result credible to a
team that was not present for the load.
""".format(images=image_lines)


def make_project(tabs=TABS, extra_images=(), missing=()):
    """A project laid out like a real bootcamp project; returns its root.

    Images live at `docs/visualizations/`, and the recap references them relative to
    itself as `visualizations/<file>.png` — exactly what Step 1a instructs.
    """
    root = tempfile.mkdtemp()
    viz = os.path.join(root, "docs", "visualizations")
    os.makedirs(viz)
    lines = []
    for tab in tabs:
        name = "results_visualization-%s.png" % tab
        if tab not in missing:
            with open(os.path.join(viz, name), "wb") as fh:
                fh.write(_png_bytes())
        lines.append("![Results visualization — %s tab](visualizations/%s)" % (tab, name))
    lines.extend(extra_images)
    recap = os.path.join(root, "docs", "bootcamp_recap.md")
    with open(recap, "w", encoding="utf-8") as fh:
        fh.write(_recap_markdown("\n\n".join(lines)))
    return root


def render(root, cwd=None, input_path=None, args=(), output="docs/bootcamp_recap.pdf"):
    """Run the generator; return (code, stdout, stderr, pdf_path)."""
    out = output if os.path.isabs(output) else os.path.join(root, output)
    src = input_path or os.path.join("docs", "bootcamp_recap.md")
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--input", src, "--output", out, *args],
        capture_output=True, text=True, cwd=cwd or root,
    )
    return proc.returncode, proc.stdout, proc.stderr, out


def image_xobjects(pdf_path):
    """Widths of the PDF's image XObjects — object definitions, not references.

    Counting `/Subtype /Image` occurrences overcounts, because a reference is
    counted too; this reads the object definitions, which is the honest count.
    """
    with open(pdf_path, "rb") as fh:
        raw = fh.read()
    widths = []
    for body in re.findall(rb"\d+ 0 obj(.*?)endobj", raw, re.S):
        if b"/Subtype" in body and b"/Image" in body:
            match = re.search(rb"/Width (\d+)", body)
            if match:
                widths.append(int(match.group(1)))
    return widths


def screenshot_count(pdf_path):
    """How many of the fixture's 160px screenshots reached the PDF."""
    return sum(1 for width in image_xobjects(pdf_path) if width == 160)


@unittest.skipUnless(
    subprocess.run([sys.executable, "-c", "import fpdf"], capture_output=True).returncode == 0,
    "fpdf2 not installed for this interpreter; the stdlib renderer embeds no images",
)
class DocumentRelativePathsEmbed(unittest.TestCase):
    """The paths Step 1a writes must work from the directory Step 1b runs in."""

    def test_embeds_when_run_from_project_root(self):
        root = make_project()
        code, stdout, stderr, pdf = render(root)  # cwd = project root, as graduation does
        self.assertEqual(code, 0, stderr)
        self.assertIn(SUCCESS_LINE, stdout)
        self.assertEqual(screenshot_count(pdf), len(TABS), stdout)

    def test_embeds_when_run_from_the_recap_directory(self):
        """The old workaround must not become the new requirement."""
        root = make_project()
        code, _, stderr, pdf = render(
            root, cwd=os.path.join(root, "docs"), input_path="bootcamp_recap.md",
            output=os.path.join(root, "docs", "from_docs.pdf"),
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(screenshot_count(pdf), len(TABS))

    def test_embeds_with_absolute_input_from_unrelated_cwd(self):
        """A cwd that cannot possibly help must not prevent resolution."""
        root = make_project()
        elsewhere = tempfile.mkdtemp()
        code, _, stderr, pdf = render(
            root, cwd=elsewhere,
            input_path=os.path.join(root, "docs", "bootcamp_recap.md"),
            output=os.path.join(elsewhere, "recap.pdf"),
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(screenshot_count(pdf), len(TABS))

    def test_success_line_reports_embedded_image_count(self):
        root = make_project()
        _, stdout, _, _ = render(root)
        self.assertIn("embedded %d of %d images" % (len(TABS), len(TABS)), stdout)


class LostImagesAreAudible(unittest.TestCase):
    """A dropped screenshot must never be silent — but must never break the PDF."""

    @requires_fpdf2
    def test_missing_image_reported_on_stderr_with_paths_searched(self):
        root = make_project(missing={"search"})
        code, _, stderr, _ = render(root)
        self.assertEqual(code, 0, stderr)
        self.assertIn("skipped image (not found)", stderr)
        self.assertIn("results_visualization-search.png", stderr)
        self.assertIn("looked in:", stderr)

    def test_missing_image_still_writes_the_pdf_and_exits_zero(self):
        root = make_project(missing={"search"})
        code, stdout, _, pdf = render(root)
        self.assertEqual(code, 0)
        self.assertIn(SUCCESS_LINE, stdout)
        self.assertTrue(os.path.exists(pdf))
        self.assertGreater(os.path.getsize(pdf), 0)

    @requires_fpdf2
    def test_missing_image_reported_once_despite_two_render_passes(self):
        """fpdf2 builds the document twice; one lost image is one message."""
        root = make_project(missing={"search"})
        _, _, stderr, _ = render(root)
        self.assertEqual(stderr.count("skipped image (not found)"), 1, stderr)

    @requires_fpdf2
    def test_shortfall_visible_in_the_success_line(self):
        root = make_project(missing={"search"})
        _, stdout, _, _ = render(root)
        self.assertIn("embedded %d of %d images" % (len(TABS) - 1, len(TABS)), stdout)


class RemoteImagesAreNeverFetched(unittest.TestCase):
    """INV-081: the render stays offline."""

    @requires_fpdf2
    def test_remote_url_is_skipped_and_reported(self):
        root = make_project(extra_images=["![Remote](https://example.invalid/x.png)"])
        code, _, stderr, _ = render(root)
        self.assertEqual(code, 0)
        self.assertIn("remote URL, never fetched", stderr)

    def test_check_does_not_flag_a_remote_url_as_missing(self):
        root = make_project(extra_images=["![Remote](https://example.invalid/x.png)"])
        code, stdout, stderr, _ = render(root, args=("--check",))
        self.assertEqual(code, 0, stderr + stdout)


class CheckAuditsImageTargets(unittest.TestCase):
    """--check must surface a lost screenshot where it can still be fixed."""

    def test_check_flags_an_unresolvable_target(self):
        root = make_project(missing={"search"})
        code, _, stderr, _ = render(root, args=("--check",))
        self.assertNotEqual(code, 0)
        self.assertIn("embedded image not found", stderr)
        self.assertIn("results_visualization-search.png", stderr)

    def test_check_passes_when_every_target_resolves(self):
        root = make_project()
        code, stdout, stderr, _ = render(root, args=("--check",))
        self.assertEqual(code, 0, stderr)
        self.assertIn("Recap complete", stdout)

    def test_check_writes_no_pdf(self):
        root = make_project(missing={"search"})
        _, _, _, pdf = render(root, args=("--check",))
        self.assertFalse(os.path.exists(pdf))


class TheSkillsInstructAResolvablePath(unittest.TestCase):
    """Fixing the resolver is half the job; the instructions must produce the path.

    INV-161 moved resolution to the recap document's own directory. The recap is
    ``docs/bootcamp_recap.md`` and its screenshots are ``docs/visualizations/*.png``,
    so the one path that resolves — and the one a Markdown reader of the recap needs
    — is ``visualizations/<file>.png``. A ``docs/``-prefixed path resolves to
    ``docs/docs/…`` and embeds nothing.

    The 2026-07-28 deep-dive audit found the resolver fixed and three instruction
    sites still teaching the broken form, while graduation taught the correct one and
    explicitly warned against the broken one — so every module-time embed was lost
    from every recap PDF, and graduation's backfill could not recover them (an embed
    that exists but points nowhere is not a *missed* embed). This file's own fixture
    at ``make_project`` writes the correct form, which is why the generator's tests
    passed throughout: nothing compared the fixture against what the skills say.
    """

    SITES = (
        os.path.join("skills", "bootcamp-onboarding", "module-completion.md"),
        os.path.join("skills", "module-03b-truthset-visualization", "phase2-close.md"),
        os.path.join("skills", "graduation", "SKILL.md"),
    )

    def _read(self, rel):
        with open(os.path.join(PLUGIN, rel), encoding="utf-8") as handle:
            return handle.read()

    def test_no_skill_instructs_a_docs_prefixed_embed(self):
        for rel in self.SITES:
            with self.subTest(file=os.path.basename(rel)):
                for match in re.finditer(r"!\[[^\]]*\]\((docs/visualizations/[^)]*)\)", self._read(rel)):
                    self.fail(
                        f"{rel} instructs `![...]({match.group(1)})`. Relative to "
                        "docs/bootcamp_recap.md that resolves to docs/docs/... and "
                        "embeds nothing (INV-161). Use visualizations/... instead."
                    )

    def test_the_embed_instruction_uses_the_document_relative_form(self):
        for rel in self.SITES[:2]:  # the two that tell the guide what to write
            with self.subTest(file=os.path.basename(rel)):
                self.assertRegex(
                    self._read(rel),
                    r"!\[[^\]]*\]\(visualizations/",
                    "the embed instruction must show the path that actually resolves",
                )

    def test_each_site_says_why_the_docs_prefix_is_wrong(self):
        """A bare correct example gets 'helpfully' corrected back; the reason does not."""
        for rel in self.SITES[:2]:
            with self.subTest(file=os.path.basename(rel)):
                text = re.sub(r"\s+", " ", self._read(rel))
                self.assertRegex(text, r"never `docs/visualizations/")
                self.assertRegex(text, r"docs/docs/")

    @requires_fpdf2
    def test_the_generator_agrees_with_the_instructed_path(self):
        """Render a recap written exactly as the skills instruct, and require it embeds."""
        root = make_project()
        code, stdout, stderr, _ = render(root)
        self.assertEqual(code, 0, stderr)
        self.assertIn("embedded 6 of 6 images", stdout + stderr)

    def test_no_site_claims_missing_images_are_skipped_silently(self):
        """INV-162: every drop is named on stderr with an embedded-of-referenced count."""
        for rel in self.SITES:
            with self.subTest(file=os.path.basename(rel)):
                text = re.sub(r"\s+", " ", self._read(rel))
                self.assertNotRegex(
                    text,
                    r"(?i)silently skip",
                    "INV-162 requires each dropped image to be reported, not skipped silently",
                )


if __name__ == "__main__":
    unittest.main()
