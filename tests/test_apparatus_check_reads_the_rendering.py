"""A module opening that shows the apparatus is not reported as missing it.

`.claude/skills/auto-test/transcript_lint.py`'s `check_apparatus` graded a Truth Set
visualization opening that showed the apparatus correctly and reported three items
missing (#734). Two of the three patterns matched the maintainer's internal *name* for
the apparatus — "before/after framing", "step overview", the vocabulary of
`ground-rules.md` — and not the shape the guide renders, a present-state/end-state pair
of run-in labels and a short label line over a numbered list. That wording is not
pinned: unlike a ⛔ gate question, which INV-056 requires be reproduced verbatim, the
apparatus is specified by what it must convey (INV-030 names the before/after framing,
INV-031 the step overview). The journey map escaped the same defect only because it
already carried a structural alternative beside its name-based ones.

The third was worse. INV-096 requires the time estimate **suppressed entirely under the
`minimal` verbosity preset**, the walk ran `--seed seeded`, and `scaffold_project.py`'s
seeded fixture writes exactly that preset. The guide suppressed the estimate, which the
rule required, and the grader called it a breach — a finding raised against conformance.

**Both directions, over the same function.** `check_apparatus` is run here on a real
module opening and on that same opening with one apparatus item cut out of it. A
`check_apparatus` that returned no findings at all would satisfy the clean half and fail
every cut, so the clean half cannot pass vacuously.

**The fixture is real walk output, not an example.** `tests/fixtures/walk-module-opening.jsonl`
is the first assistant event of
`.claude/release-cycle/runs/2026-10-16/exercise/walk/slice-module6.jsonl`, verbatim: the
turn the three findings in #734 were raised against, from a
`/dry-run --simulated confused --seed seeded` walk on 2026-10-18. The run directory is
not committed (`.gitignore`), so the fixture is the only copy, and the negative controls
are cut from it rather than written beside it.

⛔ **What this cannot establish.** It reads one captured turn. That `check_apparatus`
recognizes every rendering a live guide may produce is not testable from a fixture, and
a clean apparatus lint is not a passed phase 3 — `transcript_lint.py`'s own docstring
sets that limit for every check it runs, `check_apparatus` included. Nothing here grades
an estimate that *appears* under `minimal`, which INV-096 also forbids, or its line count
under `concise`; those stay with `dry-run` phase 3.

Stdlib only, no import from `plugins/` (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUTO_TEST = REPO_ROOT / ".claude" / "skills" / "auto-test"
DRY_RUN = REPO_ROOT / ".claude" / "skills" / "dry-run"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "walk-module-opening.jsonl"

sys.path.insert(0, str(AUTO_TEST))
sys.path.insert(0, str(DRY_RUN))

import scaffold_project  # noqa: E402
import transcript_lint  # noqa: E402

#: The paragraph marker each negative control cuts. Locating a paragraph by the words it
#: happens to use is not pinning the wording: the cut is how a turn that lacks the item is
#: made from one that has it, and the assertion is about what the grader then says.
BEFORE_AFTER = "**Where you are:**"
STEP_OVERVIEW = "**Steps**"


def project_with(preset, root):
    """A project directory under ``root`` whose preferences name ``preset``."""
    project = Path(root) / preset
    (project / transcript_lint.PREFERENCES.parent).mkdir(parents=True, exist_ok=True)
    (project / transcript_lint.PREFERENCES).write_text(
        f"path: core\nverbosity:\n  preset: {preset}\nprogramming_language: Java\n",
        encoding="utf-8")
    return project


def without(text, marker):
    """``text`` with the one paragraph carrying ``marker`` removed."""
    paragraphs = text.split("\n\n")
    kept = [p for p in paragraphs if marker not in p]
    if len(kept) == len(paragraphs):
        raise AssertionError(f"the fixture no longer carries {marker!r}")
    return "\n\n".join(kept)


class TheFixtureIsTheTurnTheIssueQuotes(unittest.TestCase):
    """A fixture that lost its content would make every assertion below vacuous."""

    def setUp(self):
        self.turns = transcript_lint.load(FIXTURE)

    def test_it_is_one_module_opening_turn(self):
        self.assertEqual(1, len(self.turns),
                         f"{FIXTURE.name} should hold exactly one assistant turn")
        self.assertIn("MODULE: TRUTH SET VISUALIZATION", self.turns[0])

    def test_it_shows_the_apparatus_without_naming_it(self):
        """The whole point: a conforming rendering that no name-based pattern can see."""
        text = self.turns[0].lower()
        for shown in ("**your journey:**", BEFORE_AFTER.lower(), STEP_OVERVIEW.lower()):
            self.assertIn(shown, text)
        for name in ("step overview", "what we'll do", "what we will cover",
                     "before/after", "before and after", "before → after"):
            self.assertNotIn(name, text,
                             f"the fixture names the apparatus ({name!r}), so a "
                             "name-based pattern would match it and the structural "
                             "fallback would go untested")

    def test_the_seeded_walk_really_ran_under_minimal(self):
        """`--seed seeded` is what the graded walk used, and it sets the preset."""
        with tempfile.TemporaryDirectory() as scratch:
            project = Path(scratch) / "seeded"
            (project / transcript_lint.PREFERENCES.parent).mkdir(parents=True)
            (project / transcript_lint.PREFERENCES).write_text(
                scaffold_project.SEEDED_PREFERENCES, encoding="utf-8")
            self.assertEqual("minimal", transcript_lint.verbosity_preset(project))


class AConformingOpeningRaisesNoFinding(unittest.TestCase):
    """Direction one: the turn the plugin actually produced grades clean."""

    def setUp(self):
        self.turns = transcript_lint.load(FIXTURE)
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)

    def apparatus(self, turns, preset):
        project = project_with(preset, self.scratch.name) if preset else None
        return transcript_lint.check_apparatus(turns, "content", project)

    def test_under_minimal_it_is_clean(self):
        findings = self.apparatus(self.turns, "minimal")
        self.assertEqual(
            [], findings,
            "a module opening that showed the journey map, the before/after framing, "
            "the step overview and the model nudge, with the estimate suppressed as "
            "INV-096 requires under `minimal`, was reported as missing apparatus: "
            + "; ".join(f["message"] for f in findings))

    def test_under_standard_only_the_suppressed_estimate_is_missing(self):
        """Not clean everywhere: under `standard` INV-096 does require the estimate."""
        findings = self.apparatus(self.turns, "standard")
        self.assertEqual(
            [("WATCH", "INV-028-apparatus-missing",
              "content module showed no time estimate")],
            [(f["severity"], f["code"], f["message"]) for f in findings])

    def test_an_unreadable_preset_is_a_coverage_limit(self):
        """Neither a pass nor a finding: the grader says it could not judge it."""
        findings = self.apparatus(self.turns, None)
        self.assertEqual(1, len(findings), [f["message"] for f in findings])
        self.assertEqual("INFO", findings[0]["severity"])
        self.assertEqual("INV-096-estimate-ungraded", findings[0]["code"])
        self.assertIn("ungraded", findings[0]["message"])

    def test_a_preferences_file_with_no_preset_is_also_ungraded(self):
        project = Path(self.scratch.name) / "nopreset"
        (project / transcript_lint.PREFERENCES.parent).mkdir(parents=True)
        (project / transcript_lint.PREFERENCES).write_text(
            "path: core\nprogramming_language: Java\n", encoding="utf-8")
        self.assertIsNone(transcript_lint.verbosity_preset(project))
        codes = [f["code"] for f in
                 transcript_lint.check_apparatus(self.turns, "content", project)]
        self.assertEqual(["INV-096-estimate-ungraded"], codes)


class AnOpeningMissingAnItemStillRaisesIt(unittest.TestCase):
    """Direction two: cut one item out of the same real turn and the finding returns."""

    def setUp(self):
        self.text = transcript_lint.load(FIXTURE)[0]
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.minimal = project_with("minimal", self.scratch.name)

    def messages(self, text):
        return [f["message"] for f in
                transcript_lint.check_apparatus([text], "content", self.minimal)]

    def test_a_turn_without_the_before_after_framing_is_flagged(self):
        self.assertEqual(["content module showed no before/after"],
                         self.messages(without(self.text, BEFORE_AFTER)))

    def test_a_turn_without_the_step_overview_is_flagged(self):
        self.assertEqual(["content module showed no step overview"],
                         self.messages(without(self.text, STEP_OVERVIEW)))

    def test_a_turn_showing_none_of_it_is_flagged_for_every_item(self):
        """The anti-vacuity floor: a grader that stayed silent here would be useless."""
        self.assertEqual(
            {"content module showed no journey map",
             "content module showed no before/after",
             "content module showed no step overview",
             "content module showed no model nudge"},
            set(self.messages("Starting the module now.")))


class TheStructuralFallbacksStayNarrow(unittest.TestCase):
    """They read in both directions, so a loose one invents a breach (INV-075).

    `check_apparatus` raises BREAKING in Bootcamp preparation and Module 0, which show
    no apparatus at all (INV-075, INV-078). Both samples here ran inside that exempt
    stretch of the 2026-10-18 walk: Module 0's teaching list under a sentence heading,
    and the numbered options under a 👉 question.
    """

    EXEMPT_SHAPES = (
        "**How it works, step by step**\n1. Ingestion and standardization\n"
        "2. Candidate selection (blocking or indexing)\n3. Comparison and scoring\n"
        "4. Classification: match, no match, or possible match\n5. Entity clustering",
        "\U0001f449 **What does a well-designed entity resolution system do with this "
        "record? Reply with a number:**\n\n"
        "1. Attach it to whichever of the three people looks most similar.\n"
        "2. Create a new, fourth entity for it.\n"
        "3. Mark it as ambiguous and hold it as a possible match.",
    )

    def test_no_exempt_phase_breach_on_an_ordinary_numbered_list(self):
        for sample in self.EXEMPT_SHAPES:
            for phase in ("preparation", "module0"):
                findings = transcript_lint.check_apparatus([sample], phase)
                self.assertEqual([], findings,
                                 f"{phase}: {[f['message'] for f in findings]}")

    def test_the_real_opening_would_still_breach_the_exemption(self):
        """The same patterns must keep catching the apparatus where it is forbidden."""
        turns = transcript_lint.load(FIXTURE)
        codes = {f["code"] for f in
                 transcript_lint.check_apparatus(turns, "preparation")}
        self.assertEqual({"INV-075-apparatus-in-exempt-phase"}, codes)


class TheProjectReachesTheLinter(unittest.TestCase):
    """`autotest.py` must hand the sandbox over, or the preset is never read."""

    def test_autotest_passes_project_to_the_lint(self):
        source = (AUTO_TEST / "autotest.py").read_text(encoding="utf-8")
        call = source[source.index('"transcript_lint.py"'):]
        call = call[:call.index("])") + 2]
        self.assertIn('"--project", str(project)', call,
                      "the lint call does not pass the walked project, so "
                      "check_apparatus cannot read the verbosity preset")

    def test_the_cli_accepts_project(self):
        result = subprocess.run(
            [sys.executable, str(AUTO_TEST / "transcript_lint.py"), "--help"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--project", result.stdout)


if __name__ == "__main__":
    unittest.main()
