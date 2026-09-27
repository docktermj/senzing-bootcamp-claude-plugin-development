"""The dry-run skill's scaffold must actually reach the paths it claims to.

`.claude/skills/dry-run/` documents a methodology, and its `scaffold_project.py`
builds the fixture that methodology depends on. A fixture that quietly stops
exercising a path turns the whole exercise into theater — and that is not
hypothetical: the scaffold's **first version had exactly that bug**. Its recap's
longest module chip was 41 characters against a 46-character clip threshold, so it
reproduced the precise blind spot the skill documents as the reason a renderer crash
survived three audits. A comment claimed it was "deliberately longer". It was not.

Its second version made the opposite mistake. It measured the RAW 55-character
`— in progress` heading against the clip and told phase 2 that folding, then removing
the fence markers, reaches the cover chip's `_clip(..., 46)`. Carried out on 2026-09-24,
it does not: `parse_recap` splits the `— in progress` suffix off the title before the
chip is built, so the chip is the bare 41-character title — and no real module title is
long enough to clip. The chip-clip path is covered by unit test in
`tests/test_recap_pdf_font_safety.py` instead.

So the claim pinned here is the true numeric one, derived rather than restated: the
fixture's checkpoint, unfenced as module-completion step 2d leaves it, is run through the
shipped `parse_recap`, and every chip label it yields must fit the chip width read from
the generator's own call site, unchanged by the shipped `_clip`. Lengthen the fixture's
title past the clip, or narrow the generator's chip width under it, and this fails —
which is exactly when the scaffold banner's "does not reach" claim would become false.

The scaffold is a maintainer tool under `.claude/`, which `propagate.sh` never
mirrors, so nothing here ships to bootcampers (INV-108 keeps this test in the
repo-level `tests/`, stdlib only).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD = REPO_ROOT / ".claude" / "skills" / "dry-run" / "scaffold_project.py"
SKILL = REPO_ROOT / ".claude" / "skills" / "dry-run" / "SKILL.md"
PREP = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-preparation"
    / "SKILL.md"
)
GENERATOR = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_recap_pdf.py"
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestScaffoldExists(unittest.TestCase):

    def test_the_skill_and_its_scaffold_are_present(self):
        for path in (SKILL, SCAFFOLD):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"missing: {path}")

    def test_the_skill_references_its_phase_files(self):
        text = SKILL.read_text(encoding="utf-8")
        for phase in (
            "phase1-mcp-contracts.md",
            "phase2-hooks-and-scripts.md",
            "phase3-conversational.md",
        ):
            with self.subTest(phase=phase):
                self.assertIn(phase, text)
                self.assertTrue((SKILL.parent / phase).is_file(), f"missing: {phase}")


class TestScaffoldReachesTheClipPath(unittest.TestCase):
    """The fixture does NOT reach the cover-chip clip, and says so truthfully.

    Named for the claim it once pinned, and kept under that name so the guard's history
    stays traceable. Everything is derived from the shipped sources: the chip width from
    the generator's call site, the chip label from `parse_recap`, the clip from `_clip`,
    and the real module names from the Bootcamp preparation module table.
    """

    # The cover chip's call site, matched on the label expression it clips so the width
    # is the chip's and no other call site's. If the expression changes, `chip_label`
    # below may no longer mirror it, so the match fails loudly instead.
    CHIP_CALL_RE = re.compile(
        r'_clip\(\s*_safe\(\s*f"\{mod\.number\}\. \{mod\.title\}"\s*'
        r"if mod\.number is not None\s*else mod\.title\s*\)\s*,\s*(\d+)\s*,?\s*\)",
        re.S,
    )

    def setUp(self):
        self.scaffold = load(SCAFFOLD, "_dryrun_scaffold")
        self.generator = load(GENERATOR, "_dryrun_recap_gen")

    def clip_widths(self):
        # The one-line pattern misses a call whose first argument has its own parentheses,
        # so alone it found only the `_clip` docstring's "_clip(..., 46)"; the chip width
        # is added from its own call site so rewording that prose cannot empty this.
        widths = {
            int(n)
            for n in re.findall(
                r"_clip\([^)]*?,\s*(\d+)\s*\)", GENERATOR.read_text(encoding="utf-8"), re.S
            )
        } | {self.chip_width()}
        self.assertTrue(widths, "no _clip(x, n) call sites parsed from the generator")
        return widths

    def chip_width(self):
        found = self.CHIP_CALL_RE.findall(GENERATOR.read_text(encoding="utf-8"))
        self.assertEqual(
            1, len(found),
            "expected exactly one cover-chip _clip(_safe(<label>), n) call site in the "
            f"generator, parsed {len(found)}; if the label expression changed, update "
            "chip_label() to mirror it",
        )
        return int(found[0])

    @staticmethod
    def chip_label(mod):
        """The label the cover builds — the expression CHIP_CALL_RE matches."""
        return f"{mod.number}. {mod.title}" if mod.number is not None else mod.title

    def unfenced_recap(self):
        """The fixture as module-completion step 2d leaves it: fence markers removed."""
        checkpoint = self.scaffold.CHECKPOINT
        for marker in (
            self.generator.RECAP_CHECKPOINT_START,
            self.generator.RECAP_CHECKPOINT_END,
        ):
            self.assertIn(marker, checkpoint, "the fixture's checkpoint lost its fence")
            checkpoint = checkpoint.replace(marker, "")
        return self.generator.parse_recap(self.scaffold.RECAP + "\n" + checkpoint)

    def test_the_in_progress_heading_parses_to_the_bare_title(self):
        titles = [m.title for m in self.unfenced_recap().modules]
        self.assertIn(
            self.scaffold.LONG_MODULE_NAME, titles,
            "the unfenced checkpoint heading no longer parses to the bare module title; "
            "the scaffold's comments and banner explain the chip by that stripping",
        )
        self.assertNotIn(self.scaffold.IN_PROGRESS_HEADING, titles)

    def test_the_parsed_fixture_chips_fit_the_chip_width_unclipped(self):
        """The banner's "does not reach" claim, measured on the label the chip builds."""
        width = self.chip_width()
        modules = self.unfenced_recap().modules
        self.assertTrue(modules, "the fixture parsed to no modules at all")
        for mod in modules:
            label = self.chip_label(mod)
            with self.subTest(label=label):
                self.assertLessEqual(
                    len(label), width,
                    f"the fixture's chip {label!r} is {len(label)} characters against a "
                    f"chip width of {width}, so it now clips — the scaffold banner and "
                    "comments that say this fixture does not reach the clip are false",
                )
                self.assertEqual(
                    label, self.generator._clip(self.generator._safe(label), width)
                )

    def test_no_real_module_name_alone_would_reach_the_clip(self):
        """Why the fixture cannot reach the clip at all: no real title is long enough."""
        narrowest = min(self.clip_widths())
        self.assertLessEqual(
            len(self.scaffold.LONG_MODULE_NAME),
            narrowest,
            "a bare module name now exceeds the clip width, so the scaffold's comment "
            "saying no real module name reaches the clip is stale",
        )

    def real_modules(self):
        """(number, display name) rows of the Bootcamp preparation module table."""
        rows = [
            (int(m.group(1)), m.group(2))
            for m in re.finditer(
                r"(?m)^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", PREP.read_text(encoding="utf-8")
            )
        ]
        self.assertEqual(11, len(rows), f"parsed {len(rows)} rows from the prep table")
        return rows

    def test_the_fixture_uses_the_longest_real_module_name(self):
        """'No real module title is long enough' holds only if the fixture's is longest."""
        names = [name for _n, name in self.real_modules()]
        self.assertIn(self.scaffold.LONG_MODULE_NAME, names)
        self.assertEqual(max(len(n) for n in names), len(self.scaffold.LONG_MODULE_NAME))

    def test_no_real_module_name_reaches_the_chip_clip_even_numbered(self):
        """A numbered heading builds '<n>. <title>'; the widest n is the worst case."""
        width = self.chip_width()
        rows = self.real_modules()
        widest = max(n for n, _name in rows)
        for _n, name in rows:
            label = f"{widest}. {name}"
            with self.subTest(label=label):
                self.assertLessEqual(len(label), width)


class TestSeededModeExercisesTheHonorPath(unittest.TestCase):
    """A walk where everything was asked only tests the rule's inert direction."""

    def setUp(self):
        self.scaffold = load(SCAFFOLD, "_dryrun_scaffold_seed")

    def test_it_seeds_every_honorable_preference(self):
        seeded = self.scaffold.SEEDED_PREFERENCES
        for key in ("path:", "verbosity:", "programming_language:"):
            with self.subTest(key=key):
                self.assertIn(key, seeded)

    def test_it_does_not_seed_the_retired_preference(self):
        self.assertNotIn(
            "model_guidance",
            self.scaffold.SEEDED_PREFERENCES,
            "model_guidance was retired by INV-137; seeding it would test a path that "
            "no longer exists",
        )

    def test_the_seeded_verbosity_is_the_one_with_a_visible_effect(self):
        """`minimal` suppresses output, so honoring it wrongly is obvious in a walk."""
        self.assertIn("preset: minimal", self.scaffold.SEEDED_PREFERENCES)

    def test_the_phase_three_doc_prescribes_the_seeded_walk(self):
        doc = (SKILL.parent / "phase3-conversational.md").read_text(encoding="utf-8")
        self.assertIn("--seeded", doc)
        self.assertRegex(
            doc,
            r"inert direction",
            "the doc should say why one walk is not enough, not merely offer a flag",
        )

    def test_the_doc_lists_what_the_walk_cannot_test(self):
        doc = (SKILL.parent / "phase3-conversational.md").read_text(encoding="utf-8")
        self.assertRegex(doc, r"cannot test")
        for gap in ("write noise", "hooks do not fire", "own compliance"):
            with self.subTest(gap=gap):
                self.assertRegex(doc, gap.replace(" ", r"\s+"), f"missing: {gap}")


class TestScaffoldGuardrails(unittest.TestCase):
    """It must refuse to build somewhere that would damage the repo."""

    def run_scaffold(self, target):
        return subprocess.run(
            [sys.executable, str(SCAFFOLD), target],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

    def test_it_refuses_to_build_inside_the_repo(self):
        result = self.run_scaffold("./scratch-should-be-refused")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("Refusing to build inside the repo", result.stderr)
        self.assertFalse((REPO_ROOT / "scratch-should-be-refused").exists())

    def test_it_refuses_to_build_under_tmp(self):
        result = self.run_scaffold("/tmp/dry-run-should-be-refused")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("Refusing to build under /tmp", result.stderr)

    def test_explain_writes_nothing(self):
        result = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--explain"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("INV-059", result.stdout, "the fixture map should cite invariants")


if __name__ == "__main__":
    unittest.main()
