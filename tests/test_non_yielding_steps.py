"""A step that asks nothing must have a legal way to be executed.

Three rules collided with no legal move. INV-251: a turn never carries two or more 👉, and INV-225 forbids ending on none, so
presenting a statement-only step alone ends a turn with **zero**. "Advance exactly one step at
a time", so folding it into the next step's turn looks like advancing two. And the post-nudge
sequence said the reply turn ends "on Step 1's single 👉 question" — which Module 1's Step 1,
a privacy reminder explicitly labeled statement-only, does not have.

The obvious resolution was unwritten, so the guide had to break a rule and learn to read ⛔ as
advisory. The consequential form is not one step: Module 1 Phase 1 has four non-yielding steps
in a row, SDK setup has four on an existing install, and **System verification had exactly one
👉 in the whole module** — so a faithful walk generates code, runs it and loads data inside a
single turn, while three of that module's own instructions describe a mechanism it never
provides.

⚠️ **System verification now has exactly two 👉 (#479).** The Mari prediction at Step 7a is the
second, because a prediction must be asked before the engine decides, and asked after its result
it predicts nothing (`ground-rules.md` → "Predictions before results"). The rule is unchanged:
Steps 1–7 are still a non-yielding run, now inside the turn that ends on the prediction, and the
reveal, Step 8 and the close run inside the turn that ends on the transition question. The
ground rules, the module's SKILL.md and phase 1's header each say so and say why; this file pins
all three.

The fix names the concept once in the ground rules and decouples checkpoint boundaries from
turn boundaries. This file pins that, and pins the module that made it urgent.

Enforces **INV-225** — a step with no 👉 is non-yielding: it shares the next asking step's turn and never ends one.

Source spec: `specs/statement-only-step-cannot-satisfy-one-question-per-turn.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
DISCOVERY = SKILLS / "module-01-business-problem" / "phase1-discovery.md"
M3_SKILL = SKILLS / "module-03-system-verification" / "SKILL.md"
M3_PHASE1 = SKILLS / "module-03-system-verification" / "phase1-verification.md"


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


class TheScanIsNotVacuous(unittest.TestCase):
    def test_every_file_exists(self):
        for path in (GROUND_RULES, DISCOVERY, M3_SKILL, M3_PHASE1):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path)

    def test_the_one_question_rule_is_still_there(self):
        """The new rule interprets INV-251 (two-or-more) and INV-225 (zero), not INV-005."""
        self.assertIn(
            "**Exactly one** 👉 question ends each yielding turn", read(GROUND_RULES),
            "the rule the non-yielding step reconciles with is gone")


class TheGroundRulesDefineTheNonYieldingStep(unittest.TestCase):
    def setUp(self):
        self.flat = squash(read(GROUND_RULES))

    def test_it_is_named_and_does_not_take_a_turn(self):
        self.assertRegex(
            self.flat,
            r"(?i)A step with no 👉 question is NON-YIELDING: it does not end a turn, and it "
            r"does not get a\s*turn of its own",
            "the non-yielding step is not defined")

    def test_it_shares_the_next_asking_step_s_turn(self):
        self.assertRegex(
            self.flat,
            r"(?i)Present it in the same turn as the next step that \*?\*?does\*?\*? ask",
            "nothing says which turn a non-yielding step belongs to")
        self.assertRegex(
            self.flat, r"(?i)let that\s*step's single 👉 end the turn for both",
            "nothing says the shared turn still ends on exactly one 👉")

    def test_it_reconciles_with_one_step_at_a_time(self):
        self.assertRegex(
            self.flat,
            r"(?i)what \"advance exactly one step at a time\" means for a step\s*"
            r"that has nothing to wait for",
            "the collision with the one-step rule is not resolved, so the guide still has "
            "to pick a rule to break")

    def test_the_one_step_rule_itself_points_at_the_carve_out(self):
        """Two rules in different sections is how this became unfollowable."""
        self.assertRegex(
            self.flat,
            r"(?i)Advance exactly one step at a time — which for a\s*\*\*non-yielding\*\* step",
            "the one-step-at-a-time rule does not mention the non-yielding case, so a "
            "reader who reaches it first still concludes one turn per step")

    def test_a_run_of_them_is_covered_not_just_a_single_step(self):
        self.assertRegex(
            self.flat, r"(?i)A run of them is the same case, not a worse one",
            "the rule reads as being about one statement-only step; the consequential "
            "form is four or eleven in a row")
        self.assertRegex(
            self.flat, r"(?i)the whole of System verification",
            "the limiting case — a module with one 👉 — is not named, so the rule looks "
            "like it could not have been meant to stretch that far")

    def test_checkpoints_are_decoupled_from_turns(self):
        self.assertRegex(
            self.flat, r"(?i)Checkpoint boundaries are step boundaries, not turn boundaries",
            "nothing separates the two, so a turn covering eleven steps either writes "
            "eleven times or contradicts the per-step rule")
        self.assertRegex(
            self.flat,
            r"(?i)one write at the end of the turn\*?\*? carrying the last completed step",
            "the resolution is named but not specified")
        self.assertRegex(
            self.flat, r"(?i)do not drop the intermediate steps from `step_history`",
            "collapsing the writes must not lose the per-step record")

    def test_the_progress_section_says_the_same_thing(self):
        self.assertRegex(
            self.flat, r"(?i)A step boundary is not a turn boundary",
            "the progress-and-state section still ties writes to step boundaries with no "
            "mention of the shared turn, which is where the contradiction was read from")


class ThePostNudgeSequenceNoLongerAssumesStepOneAsks(unittest.TestCase):
    def setUp(self):
        self.flat = squash(read(GROUND_RULES))

    def test_the_stale_sentence_is_gone(self):
        self.assertNotIn("ending on Step 1's single 👉 question", self.flat,
                         "the post-nudge sequence still asserts Step 1 ends on a 👉, which "
                         "is false for the first module a bootcamper reaches after the nudge")

    def test_both_places_say_the_next_question(self):
        occurrences = len(re.findall(r"the next single 👉 question", self.flat))
        self.assertGreaterEqual(
            occurrences, 2,
            "the correction must appear in both post-nudge sentences; found %d"
            % occurrences)

    def test_module_1_is_named_as_the_case(self):
        self.assertRegex(
            self.flat, r"(?i)Module 1's Step 1 is exactly this case",
            "the sentence is corrected in the abstract; naming the module that hits it is "
            "what stops it being re-derived")


class ModuleOneStepOneIsMarkedNonYielding(unittest.TestCase):
    def setUp(self):
        self.text = read(DISCOVERY)
        self.flat = squash(self.text)

    def test_the_heading_says_so(self):
        self.assertIn("## 1. Data privacy reminder (statement, no question — NON-YIELDING)",
                      self.text,
                      "step 1's heading does not use the defined vocabulary")

    def test_it_states_the_shared_turn_and_the_reason(self):
        self.assertRegex(
            self.flat, r"(?i)does not get a turn of its own",
            "step 1 does not say it shares a turn")
        self.assertRegex(
            self.flat, r"(?i)would end with \*?\*?zero\*?\*? 👉, which\s*INV-225 forbids",
            "the reason is not given, so the marking reads as a style note")

    def test_its_checkpoint_is_written_at_the_shared_boundary(self):
        self.assertRegex(
            self.flat,
            r"(?i)write step 1 — but as one write with Step 2's at the end of the shared turn",
            "step 1's checkpoint instruction still implies its own write")

    def test_step_2_still_carries_the_question(self):
        self.assertIn(
            "👉 **Would you like to see examples of common business problems that entity "
            "resolution can solve?**", self.text,
            "the question the shared turn ends on is gone")


class SystemVerificationSaysItHasTwoQuestions(unittest.TestCase):
    """The module whose own gate-precedence rule was unimplementable end to end.

    It had one 👉 until #479 added the Mari prediction as a second. Every place that counts the
    module's questions must count two and give the reason, or the guide is told two things.
    """

    def test_the_skill_file_names_both_questions(self):
        flat = squash(read(M3_SKILL))
        self.assertRegex(
            flat, r"(?i)This module has exactly two 👉 questions\*\* — the Mari prediction at "
                  r"Step 7a of `phase1-verification\.md`, and the module-transition question",
            "the module does not name the two 👉 it provides")
        self.assertRegex(
            flat, r"(?i)The prediction is the second because it must be asked before the engine "
                  r"decides",
            "the second 👉 is permitted without saying why")
        self.assertNotRegex(flat, r"(?i)exactly one 👉 question",
                            "a stale 'exactly one' count survives beside the new one")
        self.assertRegex(
            flat, r"(?i)a rule about\s*order and completeness, not about turns",
            "the rule is not reinterpreted, so it remains unfollowable as written")

    def test_the_ground_rules_permit_the_second_question_and_say_why(self):
        flat = squash(read(GROUND_RULES))
        self.assertRegex(
            flat, r"(?i)\*\*the whole of System verification\*\*, which contains exactly two 👉 — "
                  r"its Mari prediction",
            "the non-yielding rule still counts one 👉 in System verification")
        self.assertRegex(
            flat, r"(?i)a prediction asked after its result predicts nothing",
            "the ground rules permit the second 👉 without the reason")
        self.assertNotRegex(flat, r"(?i)which contains exactly one 👉",
                            "the stale one-question count survives in the ground rules")

    def test_phase1_names_the_one_yielding_step_and_says_why(self):
        flat = squash(read(M3_PHASE1))
        self.assertRegex(
            flat, r"(?i)Every step in this phase is NON-YIELDING except Step 7a \(INV-225\)",
            "phase 1's header does not name the one step that asks")
        self.assertRegex(
            flat, r"(?i)a prediction asked after its result predicts nothing",
            "phase 1's header permits the second 👉 without the reason")
        self.assertNotRegex(flat, r"(?i)this module's only 👉 is the module-transition",
                            "phase 1's header still says the transition is the only 👉")
        step = flat[flat.index("### Step 7a"):flat.index("### Step 8")]
        self.assertEqual(step.count("👉 **"), 1, "Step 7a must ask exactly one 👉 question")
        rest = flat.replace(step, "")
        self.assertNotIn("👉 **", rest, "a phase 1 step other than 7a asks a 👉 question")

    def test_phase1_says_its_steps_are_non_yielding(self):
        flat = squash(read(M3_PHASE1))
        self.assertRegex(
            flat, r"(?i)Every step in this phase is NON-YIELDING",
            "phase 1 still tells the guide to signal a stop by ending on a 👉 question it "
            "never provides")

    def test_phase1_agent_rule_10_collapses_its_writes(self):
        flat = squash(read(M3_PHASE1))
        self.assertRegex(
            flat,
            r"(?i)one write at the end of that turn\*?\*? carrying the last completed step",
            "agent rule 10 still requires a write per step, which puts eleven writes in "
            "one turn")
        self.assertNotRegex(
            flat, r"every step MUST write its checkpoint to `config/bootcamp_progress.json`\s*"
                  r"immediately upon completion",
            "the immediate-write wording survives and contradicts the collapse")

    def test_the_partial_turn_case_is_handled(self):
        """A turn that dies mid-run must still leave resume on the right step."""
        flat = squash(read(M3_PHASE1))
        self.assertRegex(
            flat, r"(?i)If the turn cannot complete, write what did complete before stopping",
            "collapsing writes to the end of the turn loses everything if the turn fails")


if __name__ == "__main__":
    unittest.main()
