"""Tests for the guarded CommonMark pass and the artifact-verification discipline.

Graduation prettifies `docs/*.md` immediately before the recap PDF renders. That ordering
is what makes the content guard load-bearing: a cosmetic pass that dropped prose would
produce a valid, prettier, **shorter** recap, and the generator's retention figure
(INV-110) is computed against the normalized file — so it would report success against
already-damaged input. Nothing else in the pipeline would notice.

Two properties are enforced in code rather than promised in prose, and pinned here:

* **Content preservation** — every source line's non-whitespace content must survive, the
  sole exception being an opening fence gaining an info string (MD040). Otherwise the
  original file is restored and the file is reported.
* **Scope** — top-level `docs/*.md` only, never recursive, so
  `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` cannot be touched (INV-015).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPT = os.path.join(PLUGIN, "scripts", "normalize_docs_markdown.py")
SKILLS = os.path.join(PLUGIN, "skills")
GRADUATION = os.path.join(SKILLS, "graduation", "SKILL.md")
MODULE_COMPLETION = os.path.join(SKILLS, "bootcamp-onboarding", "module-completion.md")
EXAMPLE_RECAP = os.path.join(PLUGIN, "docs", "examples", "bootcamp_recap.example.md")

MESSY = """# Bootcamp Recap
**Bootcamper:** Ada Lovelace
**Plugin version :**0.4.0
## SDK setup
### Information Shared
- The SDK was already installed via Homebrew.
- SQLite is the right database for evaluation.
Trailing prose after the list.
### Actions Taken
```
python3 -m venv data/temp/recap-venv
```
| Field | Value |
|---|---|
| records | 4012 |
Closing prose.
"""


def load():
    spec = importlib.util.spec_from_file_location("normalize_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["normalize_under_test"] = module
    spec.loader.exec_module(module)
    return module


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(args, cwd):
    return subprocess.run(
        [sys.executable, SCRIPT] + list(args), cwd=cwd, capture_output=True, text=True
    )


class HouseRulesApplied(unittest.TestCase):
    """The normalizer's line layout: blank lines around headings, fence lines, list items.

    Line-scoped by design (#424): each rule here is about where lines fall in the output, so
    lines are the unit asserted.
    """

    def setUp(self):
        self.mod = load()
        self.out = self.mod.normalize_text(MESSY)

    def test_blank_line_around_headings(self):
        lines = self.out.splitlines()
        for index, line in enumerate(lines):
            if re.match(r"^#{1,6}\s", line):
                with self.subTest(heading=line):
                    if index:
                        self.assertEqual("", lines[index - 1].strip())
                    if index + 1 < len(lines):
                        self.assertEqual("", lines[index + 1].strip())

    def test_fence_gains_a_language(self):
        self.assertIn("```text", self.out)

    def test_closing_fence_keeps_no_language(self):
        fences = [l for l in self.out.splitlines() if l.startswith("```")]
        self.assertEqual(["```text", "```"], fences)

    def test_label_colon_spacing_is_fixed(self):
        self.assertIn("**Plugin version:** 0.4.0", self.out)
        self.assertNotIn("version :**", self.out)

    def test_list_is_separated_from_surrounding_prose(self):
        lines = self.out.splitlines()
        first = next(i for i, l in enumerate(lines) if l.startswith("- The SDK"))
        last = next(i for i, l in enumerate(lines) if l.startswith("- SQLite"))
        self.assertEqual("", lines[first - 1].strip(), "blank line above the first item")
        self.assertEqual("", lines[last + 1].strip(), "blank line below the last item")

    def test_items_within_one_list_are_not_separated(self):
        """A blank line between every item would split one list into several."""
        self.assertIn(
            "- The SDK was already installed via Homebrew.\n"
            "- SQLite is the right database for evaluation.",
            self.out,
        )

    def test_is_idempotent(self):
        self.assertEqual(self.out, self.mod.normalize_text(self.out))

    def test_no_trailing_blank_lines_and_single_final_newline(self):
        self.assertTrue(self.out.endswith("\n"))
        self.assertFalse(self.out.endswith("\n\n"))


class ContentIsPreserved(unittest.TestCase):
    """The guard that makes this safe to run immediately before the render."""

    def setUp(self):
        self.mod = load()

    def test_every_source_line_survives_normalization(self):
        before = self.mod._signature(MESSY)
        after = self.mod._signature(self.mod.normalize_text(MESSY))
        self.assertTrue(self.mod._signatures_compatible(before, after))

    def test_guard_rejects_a_dropped_line(self):
        lossy = MESSY.replace("- SQLite is the right database for evaluation.\n", "")
        self.assertFalse(
            self.mod._signatures_compatible(
                self.mod._signature(MESSY), self.mod._signature(lossy)
            )
        )

    def test_guard_rejects_rewritten_prose(self):
        reworded = MESSY.replace("Closing prose.", "Closing prose, slightly reworded.")
        self.assertFalse(
            self.mod._signatures_compatible(
                self.mod._signature(MESSY), self.mod._signature(reworded)
            )
        )

    def test_guard_rejects_reordering(self):
        lines = MESSY.splitlines()
        i = lines.index("- SQLite is the right database for evaluation.")
        lines[i - 1], lines[i] = lines[i], lines[i - 1]
        self.assertFalse(
            self.mod._signatures_compatible(
                self.mod._signature(MESSY), self.mod._signature("\n".join(lines))
            )
        )

    def test_guard_permits_only_the_fence_info_string(self):
        self.assertTrue(self.mod._signatures_compatible(["```"], ["```text"]))
        self.assertFalse(self.mod._signatures_compatible(["```"], ["~~~text"]))

    def test_a_lossy_transform_restores_the_file_and_reports_it(self):
        """The end-to-end behavior: the document on disk is never damaged."""
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            target = docs / "bootcamp_recap.md"
            target.write_text(MESSY, encoding="utf-8")
            real = self.mod.normalize_text
            self.mod.normalize_text = lambda t: t.replace(
                "- SQLite is the right database for evaluation.\n", ""
            )
            try:
                result = self.mod.normalize_file(target)
            finally:
                self.mod.normalize_text = real
            self.assertEqual("skipped", result)
            self.assertEqual(MESSY, target.read_text(encoding="utf-8"))


class ScopeCannotReachTheFeedbackFile(unittest.TestCase):
    """INV-015: the bootcamper's feedback file must survive graduation intact."""

    def make_tree(self, tmp):
        docs = Path(tmp) / "docs"
        (docs / "feedback").mkdir(parents=True)
        (docs / "bootcamp_recap.md").write_text(MESSY, encoding="utf-8")
        (docs / "progress").mkdir()
        (docs / "progress" / "recap_checkpoint.md").write_text("# nested\ntext\n", encoding="utf-8")
        feedback = docs / "feedback" / "SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md"
        feedback.write_text("# Feedback\nmust survive\n", encoding="utf-8")
        return docs, feedback

    def test_glob_is_top_level_only(self):
        mod = load()
        with tempfile.TemporaryDirectory() as tmp:
            docs, _ = self.make_tree(tmp)
            names = [p.name for p in mod.target_files(docs)]
            self.assertEqual(["bootcamp_recap.md"], names)

    def test_feedback_file_is_byte_identical_after_a_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs, feedback = self.make_tree(tmp)
            before = feedback.read_bytes()
            result = run([], tmp)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(before, feedback.read_bytes())

    def test_nested_docs_are_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs, _ = self.make_tree(tmp)
            nested = docs / "progress" / "recap_checkpoint.md"
            before = nested.read_bytes()
            run([], tmp)
            self.assertEqual(before, nested.read_bytes())


class CommandLineContract(unittest.TestCase):
    def test_normalizes_and_reports_what_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            (docs / "r.md").write_text(MESSY, encoding="utf-8")
            result = run([], tmp)
            self.assertEqual(0, result.returncode)
            self.assertIn("normalized 1 of 1", result.stdout)
            self.assertIn("r.md", result.stdout)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            target = docs / "r.md"
            target.write_text(MESSY, encoding="utf-8")
            result = run(["--dry-run"], tmp)
            self.assertEqual(0, result.returncode)
            self.assertIn("would normalize", result.stdout)
            self.assertEqual(MESSY, target.read_text(encoding="utf-8"))

    def test_missing_docs_dir_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run([], tmp)
            self.assertEqual(1, result.returncode)
            self.assertIn("no such directory", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_already_clean_file_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            mod = load()
            clean = mod.normalize_text(MESSY)
            target = docs / "r.md"
            target.write_text(clean, encoding="utf-8")
            result = run([], tmp)
            self.assertIn("normalized 0 of 1", result.stdout)
            self.assertEqual(clean, target.read_text(encoding="utf-8"))


class ShippedRecapSurvivesNormalization(unittest.TestCase):
    """A regression guard against the normalizer damaging a real recap."""

    def test_example_recap_normalizes_without_content_change(self):
        mod = load()
        source = read(EXAMPLE_RECAP)
        normalized = mod.normalize_text(source)
        self.assertTrue(
            mod._signatures_compatible(mod._signature(source), mod._signature(normalized)),
            "the shipped example recap must survive the pass intact",
        )

    def test_required_subsections_survive(self):
        mod = load()
        normalized = mod.normalize_text(read(EXAMPLE_RECAP))
        for heading in (
            "### Information Shared",
            "### Questions & Responses",
            "### Actions Taken",
            "### End-of-Module Summary",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, normalized)


class GraduationDocumentsTheDiscipline(unittest.TestCase):
    def setUp(self):
        self.text = read(GRADUATION)

    def test_render_step_requires_verifying_the_artifact(self):
        self.assertIn("Verify the artifact, not the exit code", self.text)

    def test_all_six_checks_are_listed(self):
        for probe in (
            "Rasterize before trusting text extraction",
            "Probe positively for content you know is there",
            "Count unique image XObjects",
            "Open every captured PNG before writing its caption",
            "Re-run `--check --expect-modules",
            "confirm both directions",
        ):
            with self.subTest(probe=probe):
                self.assertIn(probe, self.text)

    def test_checks_are_non_blocking_and_not_questions(self):
        start = self.text.index("Verify the artifact, not the exit code")
        section = self.text[start : start + 2600]
        self.assertIn("non-blocking", section)
        self.assertIn("INV-048", section)
        # The prose legitimately *mentions* the marker ("None of these is a 👉 question"),
        # so assert no line actually POSES one rather than banning the character. Line-scoped
        # by design (#424): a 👉 that opens a line opens a question.
        posed = [l for l in section.splitlines() if l.lstrip().startswith("👉")]
        self.assertEqual([], posed, "a verification step must never be a 👉 question")

    def test_rasterizing_is_no_longer_called_maintainer_only(self):
        """It used to be described as a dev-only aid, which pointed away from the check."""
        self.assertNotIn("dev-only aid", self.text)

    def test_normalizer_script_is_invoked_rather_than_described(self):
        self.assertIn("normalize_docs_markdown.py", self.text)

    def test_normalization_content_guard_is_stated(self):
        squashed = re.sub(r"[*\s]+", " ", self.text)
        self.assertIn("restores the original", squashed)
        self.assertIn("fingerprints each file's non-whitespace content", squashed)
        self.assertIn("INV-110", self.text)

    def test_verify_your_verification_caution_is_present(self):
        self.assertIn("verify your verification", self.text)


class ModuleCompletionCarriesTheRule(unittest.TestCase):
    """The rule must not be graduation-only."""

    def setUp(self):
        self.text = read(MODULE_COMPLETION)

    def test_artifact_verification_rule_is_present(self):
        self.assertRegex(
            self.text, r"verify the artifact itself, not the exit code"
        )

    def test_it_names_the_two_concrete_failures(self):
        self.assertIn("three images of the same tab", self.text)
        self.assertIn("content retained", self.text)

    def test_it_is_best_effort_and_never_blocks(self):
        start = self.text.index("verify the artifact itself")
        section = self.text[start : start + 1200]
        self.assertIn("best-effort", section)
        self.assertIn("never blocks", section)

    def test_it_forbids_describing_the_intended_output(self):
        self.assertRegex(
            self.text, r"never from what the step was supposed to produce"
        )


if __name__ == "__main__":
    unittest.main()
