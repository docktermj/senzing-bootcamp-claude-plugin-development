"""With 2+ sources, Phase B's first source is chosen by Step 14's heuristics, and said so.

Module 6 Phase B loads one source. Phase C Step 14 teaches the ordering heuristics — reference
before transactional, quality-first "for a strong entity baseline", and so on — but it runs after
that first load, so the heuristics could not apply to the source they matter most for. Phase B
gave no rule, the guide picked silently, and the order Step 14 "presents for the bootcamper to
review" was partly a record of a decision already made. Observed during a /dry-run phase-3 walk,
Data processing, 2026-09-25: four mapped sources, and the guide applied Step 14's heuristics early
because Phase B said nothing.

The fix keeps Steps 12–14 where they are (checkpoints and tests rely on the numbering) and
asserts, on comment-stripped prose:

1. Phase B's opening chooses the first source by Step 14's heuristics when 2+ sources exist, and
   cites Step 14 rather than restating the list (INV-300), so the two cannot drift;
2. it tells the bootcamper the chosen source and the deciding heuristic before Step 5, as a
   statement — the opening poses no 👉 question (INV-225);
3. it records the choice and its reason in `docs/loading_strategy.md` and notes it in the
   checkpoint;
4. Step 14 reads that record, presents the first source as already decided and loaded, and ranks
   only the remaining sources;
5. Step 14 handles a Step 13 dependency the first choice broke by recording it and ordering the
   rest to honor it, with no reload.

Step 14 must also stay question-free: `test_phasec_generated_path_asks_once.py` counts on it.

Everything is asserted as behavior in shipped guidance, so any implementation language satisfies
it (INV-002). Source: GitHub issue #165.

Enforces **INV-327** (the first source is chosen by Phase C Step 14's heuristics, announced as a
statement, and a dependency it broke is honored rather than repaired by a reload). ⚠️ It pins the
text and cannot observe a live run's choice.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE6 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
           "module-06-data-processing")
PHASE_B = MODULE6 / "phaseB-load-first-source.md"
PHASE_C = MODULE6 / "phaseC-multi-source.md"

#: A pinned bootcamper question: the 👉 marker followed by bold text.
PINNED_QUESTION = re.compile(r"👉\s*\*\*")

#: Step 14's heuristics, as Step 14 words them. Phase B must cite the step, not copy these.
HEURISTICS = ("reference before transactional", "quality-first",
              "attribute-density-first", "volume-first")


def prose(path):
    """The file with HTML comments removed and whitespace collapsed."""
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    return " ".join(text.split())


def opening():
    """Phase B's opening: everything before the Step 5 heading."""
    text = prose(PHASE_B)
    return text[:text.index("## 5. ")]


def phase_b_step(number):
    text = prose(PHASE_B)
    start = text.index("## %d. " % number)
    return text[start:text.index("## %d. " % (number + 1), start)]


def step14():
    text = prose(PHASE_C)
    start = text.index("## 14. Determine load order")
    return text[start:text.index("## 15. ", start)]


class PhaseBsOpeningChoosesTheFirstSource(unittest.TestCase):
    """Assertion 1: with 2+ sources, the choice follows Step 14's heuristics, by citation."""

    def setUp(self):
        self.opening = opening()

    def test_it_gives_a_first_source_rule_for_two_or_more_sources(self):
        self.assertIn("**Choosing the first source (2 or more sources only).**", self.opening,
                      "Phase B's opening no longer says how the first source is chosen")
        self.assertIn("`mapping_status: complete`", self.opening)

    def test_it_chooses_by_step_fourteens_heuristics(self):
        self.assertIn("Choose it by the ordering heuristics in Phase C step 14 "
                      "(`phaseC-multi-source.md`, \"Determine load order\")", self.opening)
        self.assertIn("in that step's priority order", self.opening)

    def test_it_cites_step_fourteen_rather_than_restating_it(self):
        self.assertIn("cite it rather than restating it here", self.opening)
        self.assertIn("(INV-300)", self.opening)
        restated = [h for h in HEURISTICS if h in self.opening.lower()]
        self.assertEqual([], restated,
                         "Phase B's opening restates Step 14's heuristics; cite the step so "
                         "the two cannot drift (INV-300)")

    def test_step_fourteen_still_states_the_heuristics_it_is_cited_for(self):
        """The citation needs a target: Step 14 must still carry the whole list."""
        body = step14()
        for heuristic in HEURISTICS:
            with self.subTest(heuristic=heuristic):
                self.assertIn(heuristic, body)

    def test_a_missing_heuristic_input_moves_to_the_next_heuristic(self):
        self.assertIn("If a heuristic's input is missing for a source", self.opening)
        self.assertIn("skip that heuristic and apply the next one", self.opening)

    def test_a_single_source_is_unaffected(self):
        self.assertIn("With a single source there is no choice: say nothing and record nothing",
                      self.opening)


class TheChoiceIsStatedBeforeStepFive(unittest.TestCase):
    """Assertion 2: one line naming the source and heuristic, and no 👉 question."""

    def setUp(self):
        self.opening = opening()

    def test_it_tells_the_bootcamper_the_source_and_the_heuristic(self):
        self.assertIn("Before step 5, tell the bootcamper in one line which source loads first "
                      "and the heuristic that actually decided it", self.opening)

    def test_it_is_a_statement_not_a_question(self):
        self.assertIn("This is a statement, not a 👉 question (INV-225).", self.opening)
        self.assertIn("It asks nothing and does not end the turn", self.opening)

    def test_the_opening_poses_no_pinned_question(self):
        posed = PINNED_QUESTION.findall(self.opening)
        self.assertEqual([], posed,
                         "Phase B's opening poses a 👉 question; the first-source choice is a "
                         "statement, not a gate (INV-225)")


class TheChoiceIsRecorded(unittest.TestCase):
    """Assertion 3: `docs/loading_strategy.md` and the checkpoint carry the choice."""

    def test_it_is_recorded_in_the_loading_strategy(self):
        body = opening()
        self.assertIn("Record the choice and its reason in `docs/loading_strategy.md` as the "
                      "**first-source choice**", body)

    def test_it_is_noted_in_the_checkpoint(self):
        self.assertIn("Note it in step 5's checkpoint", opening())
        self.assertIn("**Checkpoint:** write step 5 (with 2 or more sources, note the "
                      "first-source choice).", phase_b_step(5))


class StepFourteenPresentsTheFirstSourceAsDecided(unittest.TestCase):
    """Assertion 4: Step 14 reads the record and ranks only the remaining sources."""

    def setUp(self):
        self.step = step14()

    def test_it_reads_the_recorded_choice(self):
        self.assertIn("Read the first-source choice Phase B's opening recorded in "
                      "`docs/loading_strategy.md`, which survives a resumed session", self.step)

    def test_it_presents_the_first_source_as_already_loaded(self):
        self.assertIn("**already loaded, chosen by `<heuristic>`**", self.step)

    def test_it_ranks_only_the_remaining_sources(self):
        self.assertIn("Then rank only the remaining sources", self.step)

    def test_it_asks_nothing(self):
        """`test_phasec_generated_path_asks_once.py` relies on Step 14 asking nothing."""
        self.assertEqual([], PINNED_QUESTION.findall(self.step),
                         "Step 14 poses a 👉 question; it must stay question-free")
        self.assertIn("This step asks nothing", self.step)


class StepFourteenHonorsABrokenDependencyWithoutReloading(unittest.TestCase):
    """Assertion 5: a dependency the first choice broke is recorded and honored for the rest."""

    def setUp(self):
        self.step = step14()

    def test_it_records_the_broken_dependency(self):
        self.assertIn("If step 13 recorded a dependency the first choice broke", self.step)
        self.assertIn("record it in `docs/loading_strategy.md` beside the first-source choice",
                      self.step)

    def test_it_orders_the_rest_to_honor_it(self):
        self.assertIn("order the remaining sources to honor it", self.step)

    def test_it_does_not_reload_the_first_source(self):
        self.assertIn("**(INV-327) Do not reload the first source.**", self.step)


if __name__ == "__main__":
    unittest.main()
