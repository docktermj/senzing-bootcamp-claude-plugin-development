"""Recap structure is validated at the module that writes it, not eleven modules later.

A run wrote the four recap subsections as bold labels (`**Information Shared**`) instead of
H3 headings, at its first module, and reproduced that shape faithfully for all nine. Bold
labels render near-identically in every Markdown viewer, so the recap looked right the
whole way; the failure appeared at graduation, as:

    ERROR: refusing to render docs/bootcamp_recap.md
      - input does not look like a bootcamp recap: 0 of 9 '##' sections carry any
        recognized sub-section
      - catastrophic content loss: only 2% of the input's content would reach the PDF

⛔ **The generator's refusal is the thing that worked, and this spec does not soften it.** A
more permissive generator would have shipped a 2%-retention keepsake. What was wrong was the
eleven-module gap between making the mistake and being told: recovering it meant a
structural rewrite of the entire keepsake in the turn that was supposed to render it.

So Step 2c now runs the same `--check` after every append. These tests pin both halves —
that the step invokes it, and that the generator still refuses the shape it exists to catch.

⚠️ **The general form is worth more than this instance.** A validator whose only invocation
is at the end of an N-module run cannot bound the cost of anything it detects: every finding
is already N repetitions old when it fires. The three labeled summary blocks had already
been pulled forward into Step 2c for that reason; the enclosing heading was left behind
because it had not yet been the failure observed.

Source spec: `specs/recap-subsection-heading-drift-is-caught-only-at-graduation.md`.

Run:  python3 -m unittest discover -s tests
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPT = PLUGIN / "scripts" / "generate_recap_pdf.py"
MODULE_COMPLETION = PLUGIN / "skills" / "bootcamp-onboarding" / "module-completion.md"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"

SUBSECTIONS = ("Information Shared", "Questions & Responses", "Actions Taken",
               "End-of-Module Summary")

BODY = {
    "Information Shared": "- Entity resolution resolves records to entities.",
    "Questions & Responses": "- Asked what success looks like; answered \"one row\".",
    "Actions Taken": "- Wrote the problem statement.",
    "End-of-Module Summary": (
        "**What you accomplished:**\n\n- Framed the business problem.\n\n"
        "**Files produced:**\n\n- `docs/problem-statement.md` — the statement.\n\n"
        "**Why it matters:** every later choice traces back to it."
    ),
}


def recap(heading_style):
    """A one-module recap whose subsections use `###` headings or bold labels."""
    parts = ["# Senzing Bootcamp Recap", "", "**Bootcamper:** Ada Lovelace",
             "**Started:** 2026-08-16", "", "## Discover the Business Problem — 2026-08-16", ""]
    for name in SUBSECTIONS:
        parts.append(f"### {name}" if heading_style == "h3" else f"**{name}**")
        parts.append("")
        parts.append(BODY[name])
        parts.append("")
    return "\n".join(parts) + "\n"


def run_check(markdown):
    """Run the real CLI with --check against `markdown`; return (returncode, output)."""
    workdir = tempfile.mkdtemp()
    docs = Path(workdir) / "docs"
    docs.mkdir()
    (docs / "bootcamp_recap.md").write_text(markdown, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        capture_output=True, text=True, cwd=workdir, timeout=120,
    )
    return proc.returncode, proc.stdout + proc.stderr


class TheGeneratorStillRefusesTheDriftedShape(unittest.TestCase):
    """⛔ The last line of defense, asserted unchanged."""

    def test_a_bold_label_recap_is_reported(self):
        code, out = run_check(recap("bold"))
        self.assertNotEqual(0, code,
                            "a recap whose subsections are bold labels passed --check; "
                            "the generator's refusal is what stopped a 2%-retention "
                            "keepsake from shipping")
        self.assertIn("recognized sub-section", out,
                      f"the report does not name the structural cause:\n{out}")

    def test_the_same_recap_with_h3_headings_passes(self):
        """Fixture control: if this fails, the test above proves nothing about headings."""
        code, out = run_check(recap("h3"))
        self.assertEqual(0, code, f"a correctly-structured recap was rejected:\n{out}")

    def test_check_writes_no_pdf(self):
        """Step 2c runs this every module; it must stay a read-only structural check."""
        workdir = tempfile.mkdtemp()
        docs = Path(workdir) / "docs"
        docs.mkdir()
        (docs / "bootcamp_recap.md").write_text(recap("h3"), encoding="utf-8")
        subprocess.run([sys.executable, str(SCRIPT), "--check"],
                       capture_output=True, text=True, cwd=workdir, timeout=120)
        pdfs = list(Path(workdir).rglob("*.pdf"))
        self.assertEqual([], pdfs, f"--check wrote a PDF: {pdfs}")


class StepTwoCRunsTheCheck(unittest.TestCase):

    def setUp(self):
        self.text = MODULE_COMPLETION.read_text(encoding="utf-8")
        start = self.text.index("### 2c. Verify it landed")
        self.step = self.text[start:self.text.index("Only then display", start)]

    def test_the_step_invokes_the_generator_with_check(self):
        self.assertIn("generate_recap_pdf.py", self.step,
                      "Step 2c does not run the recap generator at all")
        self.assertIn("--check", self.step)

    def test_it_resolves_the_script_the_bundled_way(self):
        """INV-185/INV-252 — never a filesystem search for a bundled script."""
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/scripts/generate_recap_pdf.py", self.step)
        self.assertIn("<this-skill-dir>/../../scripts/generate_recap_pdf.py", self.step)

    def test_it_says_what_to_do_on_a_finding(self):
        flat = " ".join(self.step.split())
        self.assertIn("On a finding:", flat,
                      "the step reports a finding with no instruction for handling it")
        self.assertIn("re-run until it is clean", flat)

    def test_it_is_non_blocking_and_invisible_to_the_bootcamper(self):
        flat = " ".join(self.step.split())
        self.assertIn("INV-012", flat)
        # INV-012 governs the suppression AND the non-blocking here; INV-048 is the recap
        # PDF's and never stated a generic never-blocks (#607, finished by #685).
        self.assertNotIn("INV-048", flat)
        self.assertIn("continue silently", flat)
        self.assertIn("Recap updated: {Name}.", flat,
                      "the Bootcamper-facing line must be unchanged either way")

    def test_it_runs_every_module_not_only_the_first(self):
        flat = " ".join(self.step.split())
        self.assertIn("every module, after the append", flat,
                      "a drift introduced at module five is as invisible as one at "
                      "module one; the check must not be first-module-only")

    def test_it_records_why_a_late_only_validator_cannot_bound_its_cost(self):
        flat = " ".join(self.step.split())
        self.assertIn("already N repetitions old when it fires", flat,
                      "the general shape is not recorded, so the next graduation-time "
                      "check will be added at graduation again")


class StepTwoBNamesTheHeadingRequirement(unittest.TestCase):
    """The drift starts here — at the template that shows the shape without saying it matters."""

    def setUp(self):
        self.text = MODULE_COMPLETION.read_text(encoding="utf-8")
        start = self.text.index("Rules for the four subsections")
        self.rules = self.text[start:self.text.index("### 2c.", start)]

    def test_it_states_the_subsections_are_h3_headings(self):
        flat = " ".join(self.rules.split())
        self.assertIn("`###` headings", flat)
        self.assertIn("heading level is load-bearing", flat)

    def test_it_warns_that_bold_labels_pass_a_visual_read(self):
        flat = " ".join(self.rules.split())
        self.assertIn("look near-identical in every", flat,
                      "nothing says why this drift survives review — it looks correct")


class GraduationRecordsThatItIsNoLongerTheFirstCheck(unittest.TestCase):

    def test_it_says_findings_should_normally_be_empty(self):
        flat = " ".join(GRADUATION.read_text(encoding="utf-8").split())
        self.assertIn("no longer the first time `--check` runs", flat)
        self.assertIn("findings should normally be empty", flat)


if __name__ == "__main__":
    unittest.main()
