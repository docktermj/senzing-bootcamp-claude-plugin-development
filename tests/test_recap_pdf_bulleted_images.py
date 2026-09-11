"""A screenshot embedded as an Actions Taken bullet must still reach the keepsake.

`module-completion.md` tells the guide to add visualization screenshots *to* the
module's **Actions Taken** — which is a bulleted list. Following that literally yields

    - ![Entity Graph — 12 resolved entities](visualizations/results-entity-graph.png)

and `generate_recap_pdf.py` anchored both its detectors to the start of the line, so it
saw none of them. Measured on a dry run (2026-08-14): 8 captured screenshots, **0**
embedded, exit 0, and a `--check` line reading "captured 8, referenced 0" — which reads
as *the guide forgot to embed them*, the one thing that had not happened. Stripping the
`- ` markers and changing nothing else embedded 8 of 8.

Worse than cosmetic: INV-146 requires every captured screenshot to reach the recap, and
graduation's orphaned-screenshot backfill embeds images "the recap does not already
reference" — so by this detector's reckoning the backfill's view of the recap was the
broken one too, and the safety net had the same blind spot as the thing it guarded.

The pattern also existed **twice** — `IMAGE_LINE_RE` for counting, an inline copy in
`_render_line` for rendering — two definitions of one contract, free to disagree about
what an image line is. The fix collapses them to one, so these tests pin the counter and
the renderer to a single answer.

Asserts the rescue (bulleted images embed and count as referenced) and its limit (an
ordinary bullet is still a bullet, and an image *inside* a sentence is not a block
image), because a fix that swallowed every bullet would pass the first half alone.

Enforces **INV-242** — prose instructing the guide to author content a bundled script must parse states the shape that script accepts.

Source spec: `specs/recap-screenshots-in-bullets-never-reach-the-pdf.md`.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from _fpdf2_support import requires_fpdf2

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_recap_pdf.py"

TABS = [
    ("Statistics", "stats"),
    ("Entity Graph", "entity-graph"),
    ("Merge Statistics", "merge-statistics"),
    ("Match Keys", "match-keys"),
    ("Feature Scores", "feature-scores"),
    ("Search", "search"),
]
PNG_WIDTH = 160


def load_generator():
    """Import the generator so the counter can be exercised without a subprocess."""
    name = "recap_pdf_under_test"
    spec = importlib.util.spec_from_file_location(name, GENERATOR)
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: the generator defines @dataclass types, and dataclasses
    # resolves each class's module out of sys.modules while decorating it.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def tiny_png(path, width=PNG_WIDTH, height=120):
    """A genuinely valid PNG, authored without Pillow (INV-108: stdlib only)."""
    raw = b"".join(b"\x00" + bytes((0x0D, 0x5F, 0x9E)) * width for _ in range(height))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def recap_text(image_lines, extra_actions=()):
    """A recap whose Actions Taken carries the given image lines verbatim."""
    lines = [
        "# Senzing Bootcamp Recap",
        "",
        "**Bootcamper:** Ada Lovelace",
        "",
        "## Query, Visualize and Discover",
        "",
        "### Information Shared",
        "",
        "The visualization served every tab over the resolved data.",
        "",
        "### Questions & Responses",
        "",
        "- **Q:** Would you like an interactive visualization?",
        "    - **R:** Yes.",
        "",
        "### Actions Taken",
        "",
        "- Built the visualization and captured every tab in order.",
    ]
    lines += list(extra_actions)
    lines += [""]
    for line in image_lines:
        lines += [line, ""]
    lines += [
        "### End-of-Module Summary",
        "",
        "**What you accomplished:**",
        "",
        "- Queried and visualized the resolved entities.",
        "",
        "**Files produced:**",
        "",
        "- `docs/visualizations/results.html` — the visualization",
        "",
        "**Why it matters:** seeing the resolution is what makes it credible.",
        "",
    ]
    return "\n".join(lines)


class Project:
    """A temp project laid out like a real bootcamp project.

    ``style`` decides, per tab index, whether that image line carries a list marker —
    so one fixture holds both shapes, which is what the acceptance criterion asks for.
    """

    def __init__(self, style=None, extra_actions=(), count=len(TABS)):
        self.style = style or (lambda i: "")
        self.extra_actions = extra_actions
        self.count = count

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.viz = self.root / "docs" / "visualizations"
        self.viz.mkdir(parents=True)
        self.tabs = TABS[: self.count]
        image_lines = []
        for index, (label, slug) in enumerate(self.tabs):
            name = "results-%s.png" % slug
            tiny_png(self.viz / name)
            image_lines.append(
                "%s![%s — captured tab](visualizations/%s)" % (self.style(index), label, name)
            )
        self.write_manifest()
        self.recap = self.root / "docs" / "bootcamp_recap.md"
        self.recap.write_text(
            recap_text(image_lines, self.extra_actions), encoding="utf-8"
        )
        return self

    def write_manifest(self):
        payload = {
            "schema": 1,
            "name": "results",
            "requested": [label for label, _ in self.tabs],
            "captured": [
                {"tab": label, "slug": slug, "file": "results-%s.png" % slug, "label": label}
                for label, slug in self.tabs
            ],
            "not_present": [],
            "failed": [],
        }
        payload["captured_count"] = len(payload["captured"])
        payload["requested_count"] = len(payload["requested"])
        (self.viz / "results-tabs.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(GENERATOR), "--input", str(self.recap), *args],
            capture_output=True, text=True, cwd=str(self.root),
        )

    def check(self):
        return self._run("--check")

    def render(self):
        self.pdf = self.root / "docs" / "bootcamp_recap.pdf"
        return self._run("--output", str(self.pdf))

    def screenshot_count(self):
        """Image XObject *definitions* of the fixture's width — references overcount."""
        raw = self.pdf.read_bytes()
        found = 0
        for body in re.findall(rb"\d+ 0 obj(.*?)endobj", raw, re.S):
            if b"/Subtype" in body and b"/Image" in body:
                match = re.search(rb"/Width (\d+)", body)
                if match and int(match.group(1)) == PNG_WIDTH:
                    found += 1
        return found

    def __exit__(self, *exc):
        self.tmp.cleanup()
        return False


def bulleted_and_plain(index):
    """Alternate the two shapes so one fixture proves both at once."""
    return "- " if index % 2 == 0 else ""


class AMixedRecapEmbedsEveryImage(unittest.TestCase):
    """The acceptance criterion, end to end through the real generator."""

    @requires_fpdf2
    def test_bulleted_and_unbulleted_images_all_reach_the_pdf(self):
        with Project(style=bulleted_and_plain) as project:
            result = project.render()
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                len(TABS),
                project.screenshot_count(),
                "not every image reached the PDF:\n%s" % result.stdout,
            )

    @requires_fpdf2
    def test_the_success_line_reports_every_image_embedded(self):
        """`embedded N of M` is the counter a bootcamper's evidence rests on (INV-162)."""
        with Project(style=bulleted_and_plain) as project:
            result = project.render()
            self.assertIn("embedded %d of %d images" % (len(TABS), len(TABS)), result.stdout)

    def test_tab_coverage_reports_zero_missing(self):
        with Project(style=bulleted_and_plain) as project:
            result = project.check()
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("missing from the recap", result.stdout + result.stderr)
            self.assertIn(
                "%d of %d captured tabs" % (len(TABS), len(TABS)),
                result.stdout + result.stderr,
            )


@requires_fpdf2
class EveryBulletShapeIsRescued(unittest.TestCase):
    """The regression as reported: a recap whose images are *all* bullets."""

    def test_an_all_bulleted_recap_embeds_all_of_them(self):
        with Project(style=lambda i: "- ") as project:
            result = project.render()
            self.assertEqual(len(TABS), project.screenshot_count(), result.stdout)

    def test_every_markdown_list_marker_is_accepted(self):
        """`-`, `*` and `+` are all valid bullets; a recap may use any of them."""
        markers = ["- ", "* ", "+ ", "  - ", "-   ", ""]
        with Project(style=lambda i: markers[i], count=len(markers)) as project:
            project.render()
            self.assertEqual(len(markers), project.screenshot_count())

    def test_the_counter_and_the_renderer_agree(self):
        """One contract, one definition: the drift the duplicated pattern allowed."""
        with Project(style=bulleted_and_plain) as project:
            source = project.recap.read_text(encoding="utf-8")
            project.render()
            self.assertEqual(
                len(GEN.recap_image_targets(source)),
                project.screenshot_count(),
                "the counter and the renderer disagree about what an image line is",
            )


class OrdinaryBulletsAreUntouched(unittest.TestCase):
    """The limit of the fix — without this, swallowing every bullet would pass above."""

    @requires_fpdf2
    def test_a_plain_text_bullet_is_not_treated_as_an_image(self):
        with Project(
            style=bulleted_and_plain,
            extra_actions=["- Ran the loader and verified the counts."],
        ) as project:
            project.render()
            self.assertEqual(len(TABS), project.screenshot_count())

    def test_an_image_inside_a_sentence_is_not_a_block_image(self):
        """Only a line that is *nothing but* an image is one; mid-line stays inline."""
        line = "- See ![the graph](visualizations/results-stats.png) for the counts."
        self.assertIsNone(GEN.IMAGE_LINE_RE.match(line))
        self.assertEqual([], GEN.recap_image_targets(line))

    def test_a_bare_bullet_is_not_matched(self):
        for line in ("- Ran the loader.", "- **Q:** did it work?", "-"):
            self.assertIsNone(GEN.IMAGE_LINE_RE.match(line), line)


class TheInstructionStatesTheShape(unittest.TestCase):
    """Criterion 2 — the constraint is stated where the images are authored."""

    def test_module_completion_requires_the_image_on_its_own_line(self):
        text = (
            REPO_ROOT
            / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
            / "module-completion.md"
        ).read_text(encoding="utf-8")
        squashed = re.sub(r"\s+", " ", text)
        self.assertIn("Each image goes on a line of its own", squashed)
        self.assertIn("not as a `- ` bullet", squashed)

    def test_the_inv161_path_warning_still_follows_it(self):
        """The two shape hazards sit together; the new text must not displace INV-161."""
        text = (
            REPO_ROOT
            / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
            / "module-completion.md"
        ).read_text(encoding="utf-8")
        squashed = re.sub(r"\s+", " ", text)
        self.assertIn("never `docs/visualizations/…`", squashed)
        self.assertIn("INV-161", squashed)
        self.assertLess(
            squashed.index("Each image goes on a line of its own"),
            squashed.index("never `docs/visualizations/…`"),
            "the own-line rule must precede the path rule, at the same instruction",
        )


if __name__ == "__main__":
    unittest.main()
