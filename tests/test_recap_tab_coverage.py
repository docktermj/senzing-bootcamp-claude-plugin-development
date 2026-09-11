"""`embedded N of M images` takes its denominator from the file it is measuring.

A Bootcamper asked whether every visualization tab reached `docs/bootcamp_recap.pdf`.
On that particular PDF they all had — but the *guarantee* did not exist, and the metric
the assistant reached for to answer could not have detected the failure being described:

    generate_recap_pdf.py  image_embed_note(referenced)
        referenced = len(recap_image_targets(source_text))   # links in THIS recap

If only four of six captured tabs were ever embedded, `referenced` is 4 and the line
reads `embedded 4 of 4 images` — a perfect score against an incomplete set. Nothing else
in the chain closes it either: capture is best-effort by contract (INV-122), `--check`
only validated that each link *resolves*, and graduation's check fired only at **zero**,
so 4-of-6 passed everything.

In the reporting session the assistant cited `embedded 12 of 12` to the Bootcamper as
evidence the screenshots were complete. It was right by luck of the input, not by
measurement — the INV-110 failure applied to a count instead of a percentage, and worse
than having no metric at all, because it is the number one naturally reaches for.

The fix is an **external** denominator. `capture_screenshots.py` writes
`<name>-tabs.json` beside the PNGs recording what it actually captured; that is the only
count in the system not derived from the recap. These tests pin:

- the manifest records captured / not-present / failed as three distinct things,
- `--check` fails on a shortfall and names the missing slugs,
- with no manifest the check reports itself **skipped**, never passed (INV-163),
- a corrupt manifest is reported and still yields "skipped", never a clean bill,
- the two counts are worded differently in the success line, so they cannot be
  conflated again.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from _fpdf2_support import requires_fpdf2

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts")
GENERATOR = os.path.join(SCRIPTS, "generate_recap_pdf.py")

TABS = [
    ("graph", "entity-graph"),
    ("stats", "merge-statistics"),
    ("matchkeys", "match-keys"),
    ("features", "feature-scores"),
    ("overlap", "cross-source"),
    ("probe", "search-probe"),
]


def load(name, filename):
    path = os.path.join(SCRIPTS, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tiny_png(path):
    """A real 4x1 PNG — the generator reads dimensions from the IHDR."""
    ihdr = struct.pack(">IIBBBBB", 4, 1, 8, 2, 0, 0, 0)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(
            ">I", zlib.crc32(tag + data)
        )

    raw = b"\x00" + b"\xff\x00\x00" * 4
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def recap_text(embedded_slugs):
    lines = [
        "# Bootcamp Recap",
        "",
        "## Truth Set visualization",
        "",
        "### Information Shared",
        "",
        "Loaded the Senzing Truth Set.",
        "",
        "### Questions & Responses",
        "",
        "- **Q:** Ready? **R:** Yes.",
        "",
        "### Actions Taken",
        "",
        "Captured the app's tabs. See docs/visualizations/truthset.html",
        "",
    ]
    for slug in embedded_slugs:
        lines += ["![a tab](visualizations/truthset-%s.png)" % slug, ""]
    lines += [
        "### End-of-Module Summary",
        "",
        "**What you accomplished:** explored the Truth Set.",
        "",
        "**Why it matters:** it is the shared baseline.",
        "",
        "**Files produced:**",
        "",
        "- docs/visualizations/truthset.html - the visualization",
        "",
    ]
    return "\n".join(lines)


class RecapProject:
    """A temp project with N captured tabs and M of them embedded in the recap."""

    def __init__(self, captured=6, embedded=6, manifest=True):
        self.captured = captured
        self.embedded = embedded
        self.manifest = manifest

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.viz = root / "docs" / "visualizations"
        self.viz.mkdir(parents=True)
        self.slugs = [slug for _, slug in TABS[: self.captured]]
        for slug in self.slugs:
            tiny_png(self.viz / ("truthset-%s.png" % slug))
        if self.manifest:
            self.write_manifest(TABS[: self.captured])
        self.recap = root / "docs" / "bootcamp_recap.md"
        self.recap.write_text(
            recap_text(self.slugs[: self.embedded]), encoding="utf-8"
        )
        self.root = root
        return self

    def write_manifest(self, tabs, failed=(), not_present=()):
        payload = {
            "schema": 1,
            "name": "truthset",
            "requested": [tab for tab, _ in tabs],
            "captured": [
                {
                    "tab": tab,
                    "slug": slug,
                    "file": "truthset-%s.png" % slug,
                    "label": tab,
                }
                for tab, slug in tabs
            ],
            "not_present": [{"tab": t, "reason": "not present"} for t in not_present],
            "failed": [{"tab": t, "reason": "no image"} for t in failed],
        }
        payload["captured_count"] = len(payload["captured"])
        payload["requested_count"] = len(payload["requested"])
        (self.viz / "truthset-tabs.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    def check(self):
        return subprocess.run(
            [sys.executable, GENERATOR, "--input", str(self.recap), "--check"],
            capture_output=True,
            text=True,
            cwd=str(self.root),
        )

    def render(self):
        return subprocess.run(
            [
                sys.executable,
                GENERATOR,
                "--input", str(self.recap),
                "--output", str(self.root / "docs" / "bootcamp_recap.pdf"),
            ],
            capture_output=True,
            text=True,
            cwd=str(self.root),
        )

    def __exit__(self, *exc):
        self.tmp.cleanup()
        return False


class TheShortfallIsDetected(unittest.TestCase):
    """The failure the spec exists to close, proved end to end."""

    def test_four_embedded_of_six_captured_fails_check(self):
        with RecapProject(captured=6, embedded=4) as project:
            result = project.check()
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)

    def test_it_names_the_missing_tab_slugs(self):
        """"Two are missing" is not actionable; which two is."""
        with RecapProject(captured=6, embedded=4) as project:
            stderr = project.check().stderr
            self.assertIn("cross-source", stderr)
            self.assertIn("search-probe", stderr)
            for present in ("entity-graph", "merge-statistics"):
                with self.subTest(slug=present):
                    self.assertNotIn(
                        "missing from the recap — %s" % present, stderr
                    )

    def test_the_self_referential_count_would_have_passed_it(self):
        """The regression guard: prove the old metric cannot see this failure.

        Without this, a future refactor could quietly re-derive the denominator from
        the recap and every other test here would still pass.
        """
        pdf = load("grp_metric", "generate_recap_pdf.py")
        with RecapProject(captured=6, embedded=4) as project:
            source = project.recap.read_text(encoding="utf-8")
            referenced = pdf.recap_image_targets(source)
            self.assertEqual(
                4,
                len(referenced),
                "the recap references 4 images while 6 tabs were captured — the "
                "denominator the embedded count uses is blind to the other 2",
            )

    def test_every_tab_embedded_passes(self):
        with RecapProject(captured=6, embedded=6) as project:
            result = project.check()
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_a_tab_that_failed_capture_is_not_demanded(self):
        """Capture is non-blocking (INV-122); a tab that produced nothing is not a
        recap defect, or every partial capture would fail graduation."""
        with RecapProject(captured=5, embedded=5) as project:
            project.write_manifest(TABS[:5], failed=["probe"])
            result = project.check()
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_an_absent_tab_is_not_demanded_either(self):
        with RecapProject(captured=5, embedded=5) as project:
            project.write_manifest(TABS[:5], not_present=["merges"])
            self.assertEqual(0, project.check().returncode)


class AMissingManifestIsSkippedNotPassed(unittest.TestCase):
    """INV-163: a check that could not run is reported, never folded into a pass."""

    def test_no_manifest_reports_skipped(self):
        with RecapProject(captured=6, embedded=6, manifest=False) as project:
            result = project.check()
            self.assertEqual(0, result.returncode)
            self.assertIn("SKIPPED: tab-coverage check", result.stderr)

    def test_the_skip_message_says_why_the_embedded_count_cannot_substitute(self):
        with RecapProject(captured=6, embedded=6, manifest=False) as project:
            self.assertRegex(
                project.check().stderr,
                r"(?i)denominator comes from this same recap",
            )

    def test_a_shortfall_is_invisible_without_a_manifest(self):
        """States the cost of the skip plainly: this is why it must be reported."""
        with RecapProject(captured=6, embedded=4, manifest=False) as project:
            result = project.check()
            self.assertEqual(
                0,
                result.returncode,
                "without the external denominator a 4-of-6 recap cannot be "
                "detected — which is exactly why the skip is announced",
            )
            self.assertIn("SKIPPED", result.stderr)

    def test_a_corrupt_manifest_is_reported_and_still_skips(self):
        """A parse failure must not read as "no tabs expected"."""
        with RecapProject(captured=6, embedded=4) as project:
            (project.viz / "truthset-tabs.json").write_text("{not json", encoding="utf-8")
            result = project.check()
            self.assertIn("unreadable tab manifest", result.stderr)
            self.assertIn("SKIPPED: tab-coverage check", result.stderr)


class TheTwoCountsAreNeverConflated(unittest.TestCase):
    """INV-193: a completeness figure's denominator must come from outside the
    artifact it measures, and a self-derived one must say what it cannot detect."""

    @requires_fpdf2
    def test_the_success_line_states_coverage_separately(self):
        with RecapProject(captured=6, embedded=6) as project:
            stdout = project.render().stdout
            self.assertIn("embedded 6 of 6 images", stdout)
            self.assertIn("6 of 6 captured tabs reached the recap", stdout)

    def test_the_check_success_line_states_coverage(self):
        with RecapProject(captured=6, embedded=6) as project:
            self.assertIn("Tab coverage: 6 of 6", project.check().stdout)

    def test_the_wordings_are_distinguishable(self):
        """Two counts that read alike are how they got conflated in the first place."""
        pdf = load("grp_wording", "generate_recap_pdf.py")
        with RecapProject(captured=6, embedded=6) as project:
            source = project.recap.read_text(encoding="utf-8")
            os.chdir(project.root)
            try:
                pdf.set_image_context(project.recap)
                coverage = pdf.tab_coverage_note(source, pdf.find_tab_manifests())
            finally:
                os.chdir(REPO_ROOT)
            self.assertIn("captured tabs", coverage)
            self.assertNotIn("images", coverage)

    def test_the_embed_note_docstring_warns_it_is_not_coverage(self):
        """The next reader of that function must not reuse it for coverage."""
        pdf = load("grp_doc", "generate_recap_pdf.py")
        self.assertRegex(
            pdf.image_embed_note.__doc__, r"(?i)measures embedding, not coverage"
        )

    def test_no_manifest_means_no_coverage_claim_in_the_note(self):
        pdf = load("grp_empty", "generate_recap_pdf.py")
        self.assertEqual("", pdf.tab_coverage_note("# x", []))


class TheManifestRecordsWhatCaptureDid(unittest.TestCase):

    def setUp(self):
        self.cs = load("cs_manifest", "capture_screenshots.py")

    def test_it_lands_beside_the_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "viz"
            self.assertTrue(self.cs.write_manifest(out, "v", ["graph"], [], [], ["graph"]))
            self.assertTrue(self.cs.manifest_path(out, "v").is_file())

    def test_captured_absent_and_failed_are_three_distinct_records(self):
        """Collapsing them would make a non-present tab look like lost content."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "viz"
            written = [(self.cs._out_path(out, "v", "graph"), "Entity Graph")]
            self.cs.write_manifest(
                out, "v", ["graph", "probe"], ["merges"], written, ["probe"]
            )
            data = json.loads(self.cs.manifest_path(out, "v").read_text())
            self.assertEqual(["graph"], [e["tab"] for e in data["captured"]])
            self.assertEqual(["probe"], [e["tab"] for e in data["failed"]])
            self.assertEqual(["merges"], [e["tab"] for e in data["not_present"]])
            self.assertEqual(1, data["captured_count"])

    def test_the_recorded_filename_matches_what_capture_writes(self):
        """The join between the two scripts. A slug mismatch here silently makes
        every captured tab look missing from the recap.

        ⚠️ Looks the entry up **by tab** rather than taking ``captured[0]``. Each iteration
        writes into the same directory, and `write_manifest` merges with any prior manifest
        rather than replacing it, so index 0 stays the *first* tab written while this
        iteration's entry is appended. The subject of this test — that the recorded
        filename and slug match what capture writes — is unchanged either way.
        """
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "viz"
            for tab, slug in TABS:
                with self.subTest(tab=tab):
                    written = [(self.cs._out_path(out, "v", tab), "L")]
                    self.cs.write_manifest(out, "v", [tab], [], written, [])
                    data = json.loads(self.cs.manifest_path(out, "v").read_text())
                    entries = [e for e in data["captured"] if e["tab"] == tab]
                    self.assertEqual(1, len(entries),
                                     f"expected exactly one entry for {tab!r}")
                    self.assertEqual(
                        self.cs._out_path(out, "v", tab).name, entries[0]["file"])
                    self.assertEqual(slug, entries[0]["slug"])

    def test_an_unwritable_target_is_reported_not_raised(self):
        """Best-effort like capture (INV-122) — but never silent."""
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "viz"
            blocker.write_text("not a directory", encoding="utf-8")
            import contextlib
            import io

            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                ok = self.cs.write_manifest(blocker, "v", ["graph"], [], [], ["graph"])
            self.assertFalse(ok)
            self.assertIn("could not write the tab manifest", err.getvalue())


if __name__ == "__main__":
    unittest.main()
