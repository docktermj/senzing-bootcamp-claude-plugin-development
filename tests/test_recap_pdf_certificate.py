"""The Certificate of Completion follows the shipped Senzing template (INV-156).

The certificate is the one page of the recap that gets detached, printed, framed, and
shown to other people, and it is laid out from a fixed design measured off
`resources/certificate-of-completion.pdf`. Everything pinned here is a defect class that
*reading* the generator cannot catch and that text extraction reports as fine:

1. **The wordmark.** Only the light (white-on-dark) wordmark ships, so the certificate
   repaints it for its white card. Get the mask wrong and every transparent pixel turns
   opaque — the wordmark prints as a solid dark block, which happened during this
   implementation and extracts as nothing at all.
2. **Drift between the two renderers.** INV-066 keeps a stdlib fallback, and INV-126
   requires it to put the same content in the same place. Two independently maintained
   layouts is how "the fallback is fine" turns out to be false at graduation.
3. **A variable-length list on a fixed page.** The module list is the one block that
   grows with the bootcamp, the page has the auto page-break off, and below the list sit
   the seal and the signature row. An uncapped list prints *over* them.
4. **Claims that are not true.** The template's citation reads "all 10 modules". A
   bootcamper who completed four has not completed ten, and a certificate is permanently
   wrong in a way a recap page is not.
5. **Letterspacing.** The template letterspaces its small caps and the recipient's name.
   Faking that with spaces between glyphs makes the name unsearchable and uncopyable —
   "A l e x  R i v e r a" is not a name.

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
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "scripts", "generate_recap_pdf.py"
)

MM = 72.0 / 25.4
PAGE_H_MM = 210.0  # landscape A4

HEADER = """# Senzing Bootcamp Recap

**Bootcamper:** {name}
**Started:** 2026-07-20
**Plugin version:** 9.9.9
"""

MODULE = """
## {title} — 2026-07-20T10:00:00-05:00

### Information Shared

Entity resolution distinguishes records that describe the same real-world thing from
records that merely look similar, which is the whole point of the whole exercise.

### Questions & Responses

- **Q:** What is a false positive?
- **A:** Two records merged into one entity that describe different real people.

### Actions Taken

- Completed the module and recorded what came out of it in the recap.

### End-of-Module Summary

Built a working vocabulary for the hands-on modules that follow this one.
"""


def recap_source(titles, name="Alex Rivera"):
    return HEADER.format(name=name) + "".join(
        MODULE.format(title=title) for title in titles
    )


def load_generator():
    """Import the generator as a module so its helpers can be unit-tested."""
    spec = importlib.util.spec_from_file_location("recap_gen_certificate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recap_gen_certificate"] = module
    spec.loader.exec_module(module)
    return module


def render(markdown):
    """Render `markdown` through the CLI (the real contract) and return the PDF path."""
    workdir = tempfile.mkdtemp()
    src = os.path.join(workdir, "recap.md")
    out = os.path.join(workdir, "recap.pdf")
    with open(src, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--input", src, "--output", out],
        capture_output=True, text=True, cwd=workdir,
    )
    assert proc.returncode == 0, proc.stderr
    return out


def _runs(stream):
    """(x, y, text) triples in points from a decoded content stream."""
    pattern = re.compile(r"([\d.]+)\s+([\d.]+)\s+(?:Td|Tm)\b(.*?)\bTj", re.S)
    runs = []
    for match in pattern.finditer(stream):
        text = re.findall(r"\((.*?)\)\s*$", match.group(3).strip())
        if text:
            runs.append((float(match.group(1)), float(match.group(2)), text[0]))
    return runs


def certificate_runs(path):
    """Drawn runs on the certificate — the recap's last page — as (x, y, text) in points.

    The last page is found through the page tree rather than by taking the last
    `stream ... endstream` in the file: images are streams too, and fpdf2 writes them
    after the pages.
    """
    with open(path, "rb") as handle:
        raw = handle.read()
    objects = {
        int(m.group(1)): m.group(2)
        for m in re.finditer(rb"(\d+) 0 obj\r?\n(.*?)\r?\nendobj", raw, re.S)
    }
    tree = next((b for b in objects.values() if b"/Type /Pages" in b), b"")
    kids = re.findall(rb"(\d+) 0 R", re.search(rb"/Kids \[(.*?)\]", tree, re.S).group(1))
    body = objects[int(kids[-1])]
    contents = int(re.search(rb"/Contents (\d+) 0 R", body).group(1))
    stream = re.search(
        rb"stream\r?\n(.*?)\r?\nendstream", objects[contents], re.S
    ).group(1)
    try:
        stream = zlib.decompressobj().decompress(stream)
    except zlib.error:
        pass
    return _runs(stream.decode("latin-1", "replace"))


def y_mm(y_pt):
    """A PDF baseline in points from the page bottom, as mm from the page top."""
    return PAGE_H_MM - y_pt / MM


class WordmarkIsRepaintedForTheWhiteCard(unittest.TestCase):
    """The shipped wordmark is white; the card is white."""

    def setUp(self):
        self.module = load_generator()
        try:
            from PIL import Image  # noqa: F401
        except ImportError:  # pragma: no cover - Pillow ships with fpdf2
            self.skipTest("Pillow is not installed; the drawn-text fallback applies")
        self.image = self.module._wordmark_on_light()
        if self.image is None:
            self.skipTest("no wordmark asset available in this checkout")

    def test_transparent_pixels_stay_transparent(self):
        """The regression: an opaque paste made the whole canvas a dark block."""
        alpha = self.image.split()[3]
        self.assertEqual(
            0, alpha.getextrema()[0], "the wordmark lost its transparent background"
        )

    def test_letterforms_are_dark_ink(self):
        colors = {c[:3] for _count, c in self.image.convert("RGBA").getcolors(1 << 16)}
        self.assertIn(
            tuple(self.module.INK), colors, "the white letterforms were not repainted"
        )

    def test_the_ember_z_survives(self):
        """Repaint the letterforms, not the logo: the "z" is the brand mark."""
        colors = {c[:3] for _count, c in self.image.convert("RGBA").getcolors(1 << 16)}
        self.assertIn(tuple(self.module.ACCENT), colors, 'the ember "z" was repainted too')

    def test_the_canvas_padding_is_cropped_away(self):
        """The certificate positions the ink, so the asset's padding must be gone."""
        self.assertEqual(self.image.size, self.image.split()[3].getbbox()[2:])


class BothRenderersAgreeOnTheLayout(unittest.TestCase):
    """INV-066/INV-126: the fallback is a plainer rendering of one design, not a second
    design. Positions are compared, because content alone drifted invisibly before."""

    @classmethod
    def setUpClass(cls):
        cls.module = load_generator()
        cls.source = recap_source(["Entity Resolution Concepts", "SDK setup"])
        cls.rich = certificate_runs(render(cls.source))
        recap = cls.module.parse_recap(cls.source)
        cls.plain = _runs(cls.module._stdlib_certificate_stream(recap, 841.89, 595.28))

    def baseline(self, runs, needle):
        found = [y for _x, y, text in runs if needle in text]
        self.assertTrue(found, f"{needle!r} was not drawn")
        return found[0]

    def test_every_shared_line_sits_at_the_same_height(self):
        for needle in (
            "Certificate of Completion",
            "SENZING BOOTCAMP",
            "PROUDLY PRESENTED TO",
            "Alex Rivera",
            "DATE COMPLETED",
            "ISSUED BY",
            "Claude plugin v9.9.9",
        ):
            with self.subTest(line=needle):
                self.assertAlmostEqual(
                    self.baseline(self.rich, needle),
                    self.baseline(self.plain, needle),
                    delta=0.5,
                    msg=f"{needle!r} is at a different height in the two renderers",
                )

    def test_the_fallback_paints_the_band_and_the_card(self):
        """Not text: the backdrop is what made the fallback look like a different page."""
        recap = self.module.parse_recap(self.source)
        stream = self.module._stdlib_certificate_stream(recap, 841.89, 595.28)
        self.assertIn(" re f", stream, "the gradient band is missing")
        self.assertIn(" re B", stream, "the white card and its ember border are missing")


class TheCitationCountsTheModulesActuallyCompleted(unittest.TestCase):
    """The template says "all 10 modules"; the certificate must not."""

    def test_the_count_comes_from_the_recap(self):
        runs = certificate_runs(render(recap_source(["Concepts", "SDK setup"])))
        text = " ".join(t for _x, _y, t in runs)
        self.assertIn("2 modules", text)
        self.assertNotIn("10 modules", text)

    def test_a_single_module_is_not_pluralized(self):
        module = load_generator()
        self.assertIn("1 module of", module._cert_citation(["Concepts"]))
        self.assertIn("2 modules of", module._cert_citation(["Concepts", "SDK"]))

    def test_the_modules_are_named_under_the_citation(self):
        """INV-100 requires the modules completed on the certificate itself."""
        runs = certificate_runs(render(recap_source(["Concepts", "Truth Set visualization"])))
        text = " ".join(t for _x, _y, t in runs)
        self.assertIn("Truth Set visualization", text)


class TheFixedPageCannotBeOverrun(unittest.TestCase):
    """A long module list must shrink, never print over the seal and signature row."""

    @classmethod
    def setUpClass(cls):
        cls.module = load_generator()
        cls.titles = [
            f"Module {i} with a deliberately long descriptive title" for i in range(1, 13)
        ]
        cls.runs = certificate_runs(render(recap_source(cls.titles)))

    def test_the_module_list_stops_above_the_seal(self):
        lines = [y_mm(y) for _x, y, text in self.runs if "deliberately long" in text]
        self.assertTrue(lines, "the module list was not drawn at all")
        self.assertLessEqual(
            max(lines),
            self.module._CERT_Y_SEAL,
            "the module list runs into the seal and the signature blocks",
        )

    def test_the_module_list_is_capped(self):
        lines = [text for _x, _y, text in self.runs if "deliberately long" in text]
        self.assertLessEqual(len(lines), self.module._CERT_MODULE_LINES)

    def test_nothing_is_drawn_below_the_card(self):
        floor = self.module._CERT_CARD_Y + self.module._CERT_CARD_H
        below = [(y_mm(y), text) for _x, y, text in self.runs if y_mm(y) > floor]
        self.assertEqual([], below, f"drawn below the card: {below[:3]}")

    @requires_fpdf2
    def test_a_pathological_name_is_clipped_at_the_shrink_floor(self):
        """Shrinking stops at 12 pt, so it alone does not bound the line: a ~78-character
        name drew from x = -18 mm, off the card and off the page (INV-121)."""
        runs = certificate_runs(render(recap_source(["Concepts"], name="W" * 120)))
        drawn = [(x, text) for x, _y, text in runs if text.startswith("WWW")]
        self.assertTrue(drawn, "the recipient name was not drawn")
        x, text = drawn[0]
        self.assertGreaterEqual(
            x / MM, self.module._CERT_CARD_X, f"name starts outside the card: {text[:20]}…"
        )
        self.assertTrue(text.endswith("..."), "an unfittable name must be clipped, not run off")

    @requires_fpdf2
    def test_a_long_name_shrinks_instead_of_running_off_the_card(self):
        runs = certificate_runs(
            render(recap_source(["Concepts"], name="Bartholomew Featherstonehaugh-Wentworth"))
        )
        drawn = [x for x, _y, text in runs if "Bartholomew" in text]
        self.assertTrue(drawn, "the recipient name was not drawn")
        self.assertGreater(
            drawn[0] / MM,
            self.module._CERT_CARD_X,
            "the recipient name starts outside the card",
        )


class LetterspacingKeepsTheTextReadable(unittest.TestCase):
    """A certificate gets searched and copied out of."""

    def test_the_small_caps_line_extracts_as_words(self):
        runs = certificate_runs(render(recap_source(["Concepts"])))
        texts = [text.strip() for _x, _y, text in runs]
        self.assertIn("THIS CERTIFICATE IS PROUDLY PRESENTED TO", texts)

    def test_the_name_extracts_as_a_name(self):
        runs = certificate_runs(render(recap_source(["Concepts"])))
        self.assertIn("Alex Rivera", [text.strip() for _x, _y, text in runs])

    def test_letterspacing_is_applied_through_the_text_state(self):
        """`Tc`, not padding: the drawn strings above prove nothing was inserted."""
        module = load_generator()
        recap = module.parse_recap(recap_source(["Concepts"]))
        self.assertIn(" Tc ", module._stdlib_certificate_stream(recap, 841.89, 595.28))


if __name__ == "__main__":
    unittest.main()
