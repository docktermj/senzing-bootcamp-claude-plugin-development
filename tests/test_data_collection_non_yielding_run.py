"""Data collection's generated-scenario path is marked as the non-yielding run it is.

On the generated-scenario path — the one a Bootcamper who accepted the Business Case Offer
takes — Data collection asks nothing until Step 9's transition. Steps 1-8b are all
non-yielding: Step 2's marker/provenance guard skips the provision question and generates the
files, Step 8a's volume-skip passes when the collected total is inside the license limit, and
Step 8b is silent below its threshold. Observed 2026-08-14 with three generated sources, 36
records against a 500-record limit: zero 👉 questions across Steps 1-8b, exactly as the file
requires.

That behavior is correct under INV-225. What was missing is the **marking**. The module the
plugin holds up as the example of this shape says it twice — `module-03-system-verification`
carries a ⚠️ naming its single 👉, and `phase1-verification.md` opens with a ⛔ — while Data
collection carried neither, so a guide reading it step by step had nothing local telling it
that Step 3 must not end a turn. That is the failure mode INV-225's own spec described: two
rules in separate sections is how the non-yielding case became unfollowable in the first place.

The conditional nature is the sharp edge, and it cuts toward marking rather than away: System
verification is *always* non-yielding, so a reader learns it once; Data collection is
non-yielding only on the generated-scenario path, so a reader who learned the module on the
bring-your-own-data path (where Step 2 does ask) meets the whole non-yielding run unexpectedly.

No new invariant: INV-225 already requires the behavior, the single write and the partial-turn
fallback. This adds the local marking that makes it followable from inside the module, and the
fourth instance to the run list in `ground-rules.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
COLLECTION = PLUGIN / "skills" / "module-04-data-collection" / "SKILL.md"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
VERIFICATION = PLUGIN / "skills" / "module-03-system-verification" / "SKILL.md"


def squash(path):
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def header():
    """The module header, down to its first numbered step.

    Scoped so the marking has to be where a guide reading in order meets it. An assertion
    satisfied by prose buried at step 8 would not discharge the obligation.
    """
    body = squash(COLLECTION)
    end = body.index("### 1.") if "### 1." in body else body.index("## 1.")
    return body[:end]


class TheModuleMarksItsSingleQuestion(unittest.TestCase):
    """Criterion 1 — one 👉, the three branches, and the other path."""

    def test_it_states_there_is_exactly_one_question(self):
        self.assertRegex(
            header(),
            r"(?i)generated-scenario path this module has exactly one 👉 question",
            "the module still has nothing local saying its steps do not end turns",
        )

    def test_it_names_step_9_as_that_question(self):
        self.assertRegex(header(), r"(?i)Step 9's module\s+transition")

    def test_it_names_all_three_branches_that_produce_the_run(self):
        block = header()
        self.assertRegex(block, r"(?i)Step 2's marker/provenance guard")
        self.assertRegex(block, r"(?i)Step 8a's volume-skip")
        self.assertRegex(block, r"(?i)Step 8b says nothing|\*\*Step 8b\*\* says nothing")

    def test_it_says_the_run_is_steps_1_to_8b(self):
        self.assertRegex(header(), r"(?i)Steps 1-8b are all \*\*non-yielding\*\*")

    def test_it_says_the_other_path_does_ask(self):
        """The path-dependence is the half a reader is most likely to be caught by."""
        block = header()
        self.assertRegex(block, r"(?i)path-dependent, not fixed")
        self.assertRegex(block, r"(?i)bring-your-own-data\*\* path, Step 2 \*does\* ask")

    def test_it_tells_the_guide_to_check_the_provenance(self):
        self.assertRegex(
            header(),
            r"(?i)Check the provenance before assuming which shape you are in",
            "naming both shapes without saying how to tell them apart leaves the reader to "
            "guess which one they are in",
        )


class TheCheckpointConsequenceIsStatedLocally(unittest.TestCase):
    """Criterion 2 — one write, the fallback, and no restatement of INV-225."""

    def test_it_states_the_single_write(self):
        block = header()
        self.assertRegex(block, r"(?i)collapse into \*\*one\*\* write at the end")
        self.assertRegex(block, r"(?i)last completed step")

    def test_it_states_the_partial_turn_fallback(self):
        self.assertRegex(
            header(),
            r"(?i)If the turn stops\s+early, write what actually completed",
            "without the fallback a stopped turn loses the progress record and a resume "
            "replays or skips work",
        )

    def test_it_cites_the_ground_rules_protocol_rather_than_restating_the_rule(self):
        block = header()
        self.assertRegex(block, r"(?i)ground-rules\.md` → the 👉 protocol")
        self.assertRegex(block, r"(?i)stated once, there, and not restated here")

    def test_it_does_not_restate_inv_225s_own_musts(self):
        """INV-225 has one home. A second copy of its MUSTs is what drifts."""
        block = header()
        for phrase in ("MUST NOT end a turn", "MUST NOT be given a turn of its own",
                       "MUST be presented in the same turn"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, block)


class TheGroundRulesListNamesTheFourthInstance(unittest.TestCase):
    """Criterion 3 — the enumeration stays complete."""

    def test_the_run_list_names_data_collection(self):
        self.assertRegex(
            squash(GROUND_RULES),
            r"(?i)Data collection's generated-scenario path, whose Steps 1-8b ask nothing",
            "the instance list enumerates three runs and this is a fourth, so the list is "
            "stale by one",
        )

    def test_the_run_list_says_this_one_is_path_dependent(self):
        # The other three are unconditional; recording that difference is what stops a
        # reader generalizing "Data collection never asks".
        self.assertRegex(
            squash(GROUND_RULES),
            r"(?i)that\s+one is path-dependent: the bring-your-own-data path does ask, at Step 2",
        )

    def test_the_three_existing_instances_survive(self):
        block = squash(GROUND_RULES)
        self.assertRegex(block, r"Module 1 Phase 1's 4a/4b/5/5a")
        self.assertRegex(
            block,
            r"SDK setup's 3/4/5/6 on an existing install \(its Step 3 there being only Phase 3 and "
            r"the environment script\)",
        )
        self.assertRegex(block, r"\*\*the whole of System verification\*\*")

    def test_the_model_marking_in_system_verification_is_unchanged(self):
        """This fix copies that module's shape; if it moved, the two have diverged."""
        self.assertRegex(
            squash(VERIFICATION),
            r"⚠️ \*\*This module has exactly one 👉 question\*\* — the module-transition question",
        )


class NoStepBehaviorChanged(unittest.TestCase):
    """Criterion 5 — this adds marking only."""

    def test_the_step_2_provision_question_is_unchanged(self):
        body = COLLECTION.read_text(encoding="utf-8")
        self.assertIn(
            "👉 **How would you like to provide the data for this source? Reply with a number:**",
            body,
            "the pinned provision question moved; the bring-your-own-data path depends on it",
        )
        for option in ("1. Upload a file.", "2. Provide a URL or file path.",
                       "3. Connect to a database.", "4. Use an API endpoint.",
                       "5. I don't have my own data — generate/synthesize it for me."):
            with self.subTest(option=option):
                self.assertIn(option, body)

    def test_the_step_2_guard_still_skips_the_question_on_a_generated_scenario(self):
        block = squash(COLLECTION)
        self.assertRegex(block, r"(?i)Ask nothing, recommend no CORD alternative")
        self.assertRegex(block, r"(?i)Both are bootcamp-generated, so both skip the question")

    def test_the_8a_license_gate_is_unchanged(self):
        self.assertIn(
            "### 8a. Senzing License Key gate (single, volume-gated — INV-093)",
            COLLECTION.read_text(encoding="utf-8"),
        )

    def test_the_8b_warning_is_unchanged(self):
        self.assertIn(
            "### 8b. SQLite load-time warning (collection-time heads-up)",
            COLLECTION.read_text(encoding="utf-8"),
        )

    def test_step_9_is_still_the_transition_question(self):
        self.assertIn(
            "### 9. Module completion and transition to Module 5",
            COLLECTION.read_text(encoding="utf-8"),
        )

    def test_the_one_step_at_a_time_rule_survives(self):
        self.assertRegex(
            header(),
            r"(?i)Never skip, combine, or abbreviate a step containing a 👉 question",
            "the marking must sit alongside that rule, not replace it",
        )


if __name__ == "__main__":
    unittest.main()
