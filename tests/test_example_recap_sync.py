"""Tests that the shipped example recap PDF matches its source Markdown.

INV-065 ships a sanitized reference pair inside the plugin:
``docs/examples/bootcamp_recap.example.md`` and its rendered ``.pdf``. The
invariant says the PDF must remain *regenerable* from the ``.md`` — but nothing
checked that the committed PDF still *matches* it, and the pair silently drifted
when the ``.md`` was edited without re-rendering. A stale reference artifact is
the kind of defect nobody notices, because the PDF still opens and still looks
right.

Two traps are pinned here:

1. **Staleness.** Distinctive strings from the current ``.md`` must appear in the
   PDF's extracted text. Editing the Markdown without re-rendering fails.
2. **An image path that only resolves from one directory.** The example used to
   reference its screenshot as ``docs/examples/bootcamp_recap.example.truthset.png``
   — a path relative to a bootcamp *project root* — back when the renderer resolved
   against the current working directory. **INV-161 ended that**: paths now resolve
   against the recap document's own directory, so the references are plainly
   ``visualizations/<tab>.png`` (the PNGs sit in ``docs/examples/visualizations/``,
   beside the ``.md``), which is also what a Markdown reader of the source needs.
   The invariant is explicit that *no step may require a ``cd`` to make assets
   resolve*, so there is no correct working directory to regenerate from any more —
   every directory is.

   The example now carries a full screenshot gallery — the six Truth Set
   visualization tabs, the data-quality assessment, and the six tabs of the
   bootcamper's own results visualization — rather than the single Truth Set PNG it
   shipped with originally. Nothing here hardcodes how many: the expected count is
   read from the ``.md``'s own ``![](...)`` references, so adding or removing a
   screenshot needs no test edit, while *losing* one still fails.

   The 2026-07-28 deep-dive audit caught the pair mid-transition: the resolver had
   been fixed, the example had not, and the committed PDF could no longer be
   reproduced from its own source (``embedded 0 of 1 images``, 4 image objects
   against 5). ``TestPdfRegeneratesFromItsSource`` below now renders freshly from an
   unrelated cwd, so a repeat cannot hide behind a PDF whose image was baked in by
   an earlier render.

   Regenerate from anywhere:

       python3 plugins/senzing-bootcamp/scripts/generate_recap_pdf.py \\
           --input plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.md \\
           --output plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.pdf

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zlib
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "docs", "examples")
EXAMPLE_MD = os.path.join(EXAMPLES, "bootcamp_recap.example.md")
EXAMPLE_PDF = os.path.join(EXAMPLES, "bootcamp_recap.example.pdf")
EXAMPLE_PNG = os.path.join(EXAMPLES, "bootcamp_recap.example.truthset.png")
GENERATOR = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "scripts", "generate_recap_pdf.py"
)


def pdf_text(path):
    """Drawn text from a PDF, decompressing streams (fpdf2 compresses them).

    `(...)Tj` strings may contain escaped parens, so the capture skips `\\(`
    and `\\)`. Fragments are joined with a space because `multi_cell` wraps one
    source line into several `Tj` operators, and joining bare would weld the
    last word of one line onto the first of the next.
    """
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
    fragments = re.findall(r"\(((?:\\.|[^()\\])*)\)\s*Tj", "\n".join(chunks))
    return " ".join(f.replace("\\(", "(").replace("\\)", ")") for f in fragments)


def pdf_text_without_page_footers(path):
    """`pdf_text`, minus fragments that are only a page number.

    A page-number footer is its own `Tj` fragment, so when a source line straddles a
    page break the footer lands *inside* it and `squash` welds the digits into the
    middle of the compared window — "…assuming it **23** recordLimit: 0…". The line is
    present; the comparison window is not contiguous. This module's `sampled_lines`
    docstring already describes that hazard for `_NEW_LINE_LABELS`; it reaches ordinary
    prose too, and which line it hits depends only on where the pagination happens to
    fall, so any edit anywhere in the source can move it.

    Dropping digit-only fragments cannot hide staleness: a sentence that is genuinely
    missing from the PDF is still missing from this haystack. (Added 2026-08-11, when
    a wording change in Module 0 shifted pagination and pushed the license-measurement
    line onto a page boundary — INV-181: fix the assertion's model of the artifact,
    not the artifact.)
    """
    return re.sub(r"\s+\d+\s+", " ", " " + pdf_text(path) + " ")


def squash(text):
    """Reduce to lowercase alphanumerics.

    Comparisons then survive PDF escaping, line wrapping, and whitespace
    differences — the three things that make raw substring matching on extracted
    PDF text unreliable.
    """
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def pdf_bytes():
    with open(EXAMPLE_PDF, "rb") as handle:
        return handle.read()


def normalize(text):
    """Fold the generator's character substitutions, so comparisons are fair.

    Non-Latin-1 typography is approximated on the way into the PDF (en dash -> '-',
    curly quotes -> straight, "∞" -> "infinity"), so the Markdown side must be folded
    the same way before searching.

    ⚠️ **Attribution corrected 2026-07-31.** This used to say it folded "the
    substitutions `_pdf_escape` makes" and hardcoded 9 of them. `_pdf_escape` no longer
    substitutes anything — it carried a 9-entry duplicate of `_UNICODE_MAP` with a `"?"`
    default, which made the stdlib renderer print `?` for the other 24 (INV-143). The
    substitutions still happen; they happen in `_safe` via `_UNICODE_MAP`.

    Derived from `_UNICODE_MAP` rather than restating a subset of it, because a
    hardcoded second copy is exactly the defect that was just removed from the source:
    were the example recap to gain a "≥", a 9-entry list here would silently
    mis-compare.
    """
    for src, dst in _generator_unicode_map().items():
        text = text.replace(src, dst)
    return text


def _generator_unicode_map():
    """`_UNICODE_MAP` from the recap generator, loaded once."""
    global _UNICODE_MAP_CACHE
    if _UNICODE_MAP_CACHE is None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("recap_gen_for_normalize", GENERATOR)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _UNICODE_MAP_CACHE = module._UNICODE_MAP
    return _UNICODE_MAP_CACHE


_UNICODE_MAP_CACHE = None


def example_md_text():
    with open(EXAMPLE_MD, encoding="utf-8") as handle:
        return handle.read()


def referenced_image_targets():
    """Every ``![alt](target)`` path in the example's Markdown, in document order.

    The expected image count is derived here rather than hardcoded, so the gallery can
    grow or shrink without a test edit — but a screenshot that stops resolving still
    fails, because the renderer's own "embedded N of M" count is compared against this.
    Mirrors ``generate_recap_pdf.recap_image_targets``: an image reference is a line
    that *starts* with ``![``.
    """
    return re.findall(r"^!\[[^\]]*\]\(([^)]+)\)", example_md_text(), re.M)


class TestExampleAssetsExist(unittest.TestCase):
    """INV-065: the sanitized reference pair ships inside the plugin."""

    def test_all_three_assets_present(self):
        for path in (EXAMPLE_MD, EXAMPLE_PDF, EXAMPLE_PNG):
            with self.subTest(path=os.path.basename(path)):
                self.assertTrue(os.path.exists(path), f"missing: {path}")

    def test_pdf_is_valid(self):
        raw = pdf_bytes()
        self.assertTrue(raw.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", raw)


class TestPdfEmbedsTheScreenshot(unittest.TestCase):
    """The committed PDF must actually carry the screenshots."""

    WRONG_DIR_HINT = (
        "The example's screenshots did not all embed. Their paths must be relative to "
        "the recap document itself (INV-161) — visualizations/<tab>.png resolving to "
        "docs/examples/visualizations/, not docs/... from a project root — and the "
        "generator names every drop on stderr with an 'embedded N of M images' count "
        "(INV-162). See this module's docstring."
    )

    def test_screenshot_is_embedded(self):
        """The chrome always embeds, so only a count above it can detect a loss.

        The cover logo, its soft mask, and the certificate art resolve relative to the
        *script*, so they embed no matter what happens to the gallery — "any image at
        all" would pass on a PDF that lost every screenshot. Requiring at least one
        object per referenced screenshot puts the floor above the chrome's contribution.
        """
        expected = len(referenced_image_targets())
        self.assertGreater(expected, 0, "the example should reference screenshots")
        raw = pdf_bytes()
        images = raw.count(b"/Subtype /Image") + raw.count(b"/Subtype/Image")
        self.assertGreaterEqual(
            images,
            expected,
            f"The example PDF carries {images} image object(s), expected at least "
            f"{expected} — one per screenshot the Markdown references, before the "
            f"cover logo, its soft mask, and the certificate art. {self.WRONG_DIR_HINT}",
        )

    def test_screenshot_caption_is_rendered(self):
        """A caption travels with its image, so its absence dates the loss.

        Asserted separately from the object count: a future cover change could
        alter how many image objects the chrome contributes, but a caption is
        rendered only when its screenshot itself resolved and embedded. One caption
        is checked from each of the three galleries, so losing a whole gallery
        cannot hide behind the other two.
        """
        text = normalize(pdf_text(EXAMPLE_PDF))
        for caption in (
            "84 resolved entities spread across the force layout",   # Truth Set tabs
            "per-RECORD_TYPE coverage bars",                         # data quality
            "5,000 records collapsed into 4,971 entities",           # own results tabs
        ):
            with self.subTest(caption=caption):
                self.assertIn(
                    caption,
                    text,
                    f"a screenshot caption is missing from the example PDF: {caption!r}. "
                    + self.WRONG_DIR_HINT,
                )

    def test_markdown_references_the_screenshots(self):
        targets = referenced_image_targets()
        self.assertTrue(targets, "the example should reference screenshots")
        for target in targets:
            with self.subTest(target=target):
                resolved = os.path.join(EXAMPLES, target)
                self.assertTrue(
                    os.path.isfile(resolved),
                    f"the example references {target} but no file sits at {resolved}. "
                    "A reference whose PNG was never committed renders as a silent "
                    "drop (INV-065: the PDF must stay regenerable from the .md).",
                )

    def test_the_reference_is_document_relative(self):
        """INV-161: the path a Markdown reader needs is the path the renderer needs."""
        for target in referenced_image_targets():
            with self.subTest(target=target):
                self.assertFalse(
                    os.path.isabs(target),
                    f"{target} is absolute, so it resolves on exactly one machine",
                )
                self.assertFalse(
                    target.startswith("docs/"),
                    f"{target} is written relative to a bootcamp project root; a "
                    "cwd-relative path resolves from exactly one directory, which "
                    "INV-161 forbids",
                )


class TestPdfRegeneratesFromItsSource(unittest.TestCase):
    """INV-065's 'regenerable' is a property of a *fresh* render, not the committed file.

    The committed PDF keeps whatever was baked into it by whichever render produced
    it, so inspecting it cannot tell you the pair still reproduces. The 2026-07-28
    audit found exactly that gap: the resolver had moved to document-relative
    (INV-161), the example had not, and every assertion against the committed bytes
    still passed while a fresh render silently lost the screenshot.
    """

    def _render(self, out_dir):
        script = os.path.join(
            REPO_ROOT, "plugins", "senzing-bootcamp", "scripts", "generate_recap_pdf.py"
        )
        out = os.path.join(out_dir, "regen.pdf")
        proc = subprocess.run(
            [sys.executable, script, "--input", EXAMPLE_MD, "--output", out],
            capture_output=True,
            text=True,
            cwd=tempfile.gettempdir(),  # deliberately unrelated to the repo
        )
        return proc, out

    @requires_fpdf2
    def test_a_fresh_render_embeds_every_referenced_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = self._render(tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            combined = proc.stdout + proc.stderr
            expected = len(referenced_image_targets())
            self.assertIn(
                f"embedded {expected} of {expected} images",
                combined,
                f"the example references {expected} screenshot(s) and every one must "
                "embed (INV-161/INV-162):\n" + combined,
            )
            self.assertNotIn("skipped image", combined)

    @requires_fpdf2
    def test_a_fresh_render_matches_the_committed_pdf_image_count(self):
        """A committed PDF richer than a fresh render means the pair has drifted."""
        with tempfile.TemporaryDirectory() as tmp:
            _, out = self._render(tmp)
            with open(out, "rb") as handle:
                fresh = handle.read()
            committed = pdf_bytes()

            def count(raw):
                return raw.count(b"/Subtype /Image") + raw.count(b"/Subtype/Image")

            self.assertEqual(
                count(fresh),
                count(committed),
                "the committed example PDF is not reproducible from its Markdown "
                "(INV-065). Regenerate it — see this module's docstring.",
            )

    def test_check_mode_reports_no_missing_image(self):
        """--check is what graduation runs; it must be clean on the shipped example."""
        script = os.path.join(
            REPO_ROOT, "plugins", "senzing-bootcamp", "scripts", "generate_recap_pdf.py"
        )
        proc = subprocess.run(
            [sys.executable, script, "--input", EXAMPLE_MD, "--check"],
            capture_output=True,
            text=True,
            cwd=tempfile.gettempdir(),
        )
        self.assertNotIn("embedded image not found", proc.stdout + proc.stderr)


class TestPdfMatchesItsSource(unittest.TestCase):
    """The committed PDF must not lag edits to the Markdown."""

    def setUp(self):
        with open(EXAMPLE_MD, encoding="utf-8") as handle:
            self.md = normalize(handle.read())
        self.pdf = pdf_text(EXAMPLE_PDF)

    def sampled_lines(self):
        """Distinctive prose lines from the recap's rendered subsections.

        Headings and bullets are rendered; blank lines, rules, meta lines and
        image tags are not. Long lines are sampled because short ones repeat.
        """
        keep = []
        in_comment = False
        for raw in self.md.splitlines():
            line = raw.strip()
            # Skip whole HTML comment BLOCKS, not just their opening line. The renderer drops
            # comments by design, so a multi-line maintainer note would otherwise contribute
            # continuation lines that can never appear in the PDF — reported as staleness on a
            # freshly rendered file. (Hit on 2026-07-30 by
            # `refresh-example-recap-to-the-consolidated-app`, which added a multi-line header
            # note; the only pre-existing comment was a single line, so this was latent.)
            if in_comment:
                if "-->" in line:
                    in_comment = False
                continue
            if line.startswith("<!--"):
                if "-->" not in line:
                    in_comment = True
                continue  # maintainer notes: the renderer drops these by design
            if not line or line.startswith(("#", "---", "!", "|", ">", "```")):
                continue
            line = re.sub(r"^[-*]\s+", "", line)
            line = line.replace("**", "").replace("`", "").strip()
            # `Why it matters:` is a `_NEW_LINE_LABELS` label: the renderer draws the
            # label, then starts its value on a fresh line at the margin. So the source
            # line is never one contiguous run in the PDF, and when the break between
            # them is also a *page* break, the page-number footer lands between the two
            # — "Why it matters: 4 These concepts are..." — which `squash` welds into the
            # middle of the compared window. Sampling the value alone models what the
            # renderer actually draws; the value is also the part that detects staleness,
            # since the label itself repeats once per module.
            line = re.sub(r"(?i)^why it matters:\s*", "", line)
            # `Elaboration:` splits the same way, and its label additionally carries the
            # attribution ("written by the bootcamp") that INV-257 requires on the page —
            # so the drawn label is not the source label, and only the value is comparable.
            # `Context:` needs no rule: its label is drawn immediately before its value, so
            # the squashed run still matches.
            line = re.sub(r"(?i)^elaboration:\s*", "", line)
            if len(line) >= 60 and " " in line:
                keep.append(line)
        return keep

    def test_source_lines_appear_in_the_pdf(self):
        lines = self.sampled_lines()
        self.assertGreater(len(lines), 20, "sampler found too little to compare")
        haystack = squash(self.pdf)
        # Compare a distinctive leading run of each line, squashed, so wrapping
        # and PDF escaping cannot produce a false failure. A line that straddles a
        # page break has the page-number footer welded into that window, so retry
        # those against a haystack with digit-only fragments removed.
        no_footers = squash(pdf_text_without_page_footers(EXAMPLE_PDF))
        missing = [
            ln for ln in lines
            if squash(ln)[:50] not in haystack and squash(ln)[:50] not in no_footers
        ]
        self.assertEqual(
            [],
            missing[:5],
            f"{len(missing)} of {len(lines)} source lines are absent from the "
            "example PDF — it is stale relative to the Markdown. Re-render it "
            "(see this module's docstring for the command).",
        )

    def test_certificate_page_present(self):
        """INV-100: the recap ends with a Certificate of Completion page."""
        self.assertIn(squash("Certificate of Completion"), squash(self.pdf))


if __name__ == "__main__":
    unittest.main()


PLUGIN_JSON = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", ".claude-plugin", "plugin.json"
)


class TestExampleClaimsAreTrueOfTheExample(unittest.TestCase):
    """The example's prose describes the example, not an app it does not ship.

    `refresh-example-recap-to-the-consolidated-app`. The shipped reference recap said, in
    Actions Taken, "Captured one screenshot per visualization tab and embedded them all in
    this recap, in the app's tab order" — while embedding **one** image of an app its own
    Information Shared calls six-tab. That is the shape INV-146 exists to forbid, demonstrated
    in the plugin's only model of a finished recap, and the pattern a guide authoring a real
    one copies. It also claimed "all four API endpoints" in three places, against the **ten**
    the Truth Set module now verifies.

    The tests above pin the `.md` <-> `.pdf` relationship thoroughly. They cannot see whether
    the prose is true *of the example*, which is a different property and the one that broke.

    Route B was taken (maintainer decision, 2026-07-30): keep the single real capture and make
    the text say so, rather than shipping five more PNGs — five invented screenshots would
    breach INV-123's "caption derived from the opened image" as surely as the false claim did.
    So what is pinned is the *disclosure*, plus the absence of hardcoded counts that already
    went stale in three places.
    """

    @classmethod
    def setUpClass(cls):
        with open(EXAMPLE_MD, encoding="utf-8") as handle:
            cls.md = handle.read()
        cls.flat = re.sub(r"\s+", " ", cls.md)

    def test_a_per_tab_capture_claim_discloses_what_the_example_ships(self):
        if "screenshot per visualization tab" not in self.flat:
            self.skipTest("the per-tab capture claim is no longer made")
        images = len(re.findall(r"^!\[", self.md, re.M))
        if images >= 6:
            return  # Route A taken later: the claim is simply true
        self.assertRegex(
            self.flat,
            r"(?i)this sanitized example ships only",
            "the example claims a screenshot per tab but embeds %d image(s); it must disclose "
            "what the sanitized example actually ships (INV-146's shape, in the plugin's own "
            "reference recap)" % images,
        )

    def test_the_disclosure_still_states_the_real_rule(self):
        """Disclosing the omission must not teach the omission as correct."""
        if "this sanitized example ships only" not in self.flat.lower():
            self.skipTest("no disclosure present (Route A, or the claim was dropped)")
        self.assertRegex(
            self.flat,
            r"(?i)a real recap carries one image per captured tab, all of them, in tab order",
            "the disclosure must restate what a real recap does (INV-146/INV-147), or a reader "
            "learns that one image is the norm",
        )

    def test_no_hardcoded_endpoint_count(self):
        """The count went stale in three places while the app grew from four endpoints to ten."""
        stale = re.findall(
            r"(?i)(all (?:four|4) API endpoints|(?:four|4)-endpoint contract)", self.flat
        )
        self.assertEqual(
            [],
            stale,
            "the example hardcodes an endpoint count: %s. Use count-free phrasing — the "
            "contract's endpoint set grows, and this claim has already gone stale." % stale,
        )

    def test_the_plugin_version_matches_the_manifest(self):
        """A frozen version reads as a stale fixture; the header tracks plugin.json."""
        with open(PLUGIN_JSON, encoding="utf-8") as handle:
            manifest = json.load(handle)
        m = re.search(r"^\*\*Plugin version:\*\*\s*(\S+)", self.md, re.M)
        self.assertIsNotNone(m, "the example lost its Plugin version meta row (INV-105/INV-126)")
        self.assertEqual(
            manifest["version"],
            m.group(1),
            "the example's Plugin version does not match .claude-plugin/plugin.json — refresh "
            "the example (and re-render its PDF) rather than leaving a stale figure",
        )
