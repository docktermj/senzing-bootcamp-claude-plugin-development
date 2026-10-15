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

#603 corrected the count. The 2026-08-14 walk sat inside the limit, but Discover the Business
Problem sizes a generated scenario by default well above the built-in evaluation license's limit
(INV-277 forbids tying that size to the license), so on the default scenario Step 8a's License Key
gate fires. The header and the ground-rules list said "exactly one 👉" and "Steps 1-8b ask nothing";
they now name Step 9 as the one question that always fires and Steps 8a and 8b as the two
conditional gates. #603 also states, once, beside the `recordLimit: 0` rule in the generation block,
what to generate when the effective limit is below the scenario's count: the full count, with no
question, leaving capacity to Steps 8a and 8b.

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


def generation_block():
    """The `provenance: synthesized` generation block, from its capacity directive to the
    paragraph that follows the block."""
    body = squash(COLLECTION)
    start = body.index("How many records to generate is a LICENSE-CAPACITY decision")
    end = body.index("Both are bootcamp-generated, so both skip the question", start)
    return body[start:end]


OLD_CLAIMS = (
    "exactly one 👉 question",
    "Steps 1-8b are all **non-yielding**",
    "which that step calls the common case",
)


def header_problems(block):
    """What is wrong with a header's account of which questions this path asks.

    A function rather than inline assertions so the negative control can run the same check on
    the old wording and watch it fail.
    """
    problems = []
    required = (
        (r"(?i)generated-scenario path this module has one 👉 question that always fires",
         "it does not say Step 9's question is the one that always fires"),
        (r"(?i)two conditional gates, Step 8a's and Step 8b's, that ask only when their condition "
         r"holds", "it does not name Steps 8a and 8b as conditional gates"),
        (r"(?i)Step 8a's License Key gate asks its question when the collected total exceeds the "
         r"effective limit", "it does not say when Step 8a's gate asks"),
        (r"(?i)A default-sized scenario from Discover the Business Problem exceeds the built-in "
         r"evaluation license's limit", "it does not say the default scenario trips Step 8a"),
        (r"(?i)Step 8b asks its question when the database is SQLite and the loadable total is "
         r"above the SQLite threshold", "it does not say when Step 8b asks"),
    )
    for pattern, problem in required:
        if not re.search(pattern, block):
            problems.append(problem)
    for old in OLD_CLAIMS:
        if old in block:
            problems.append("it still carries the old claim %r" % old)
    return problems


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

    def test_it_names_the_one_question_that_always_fires_and_the_two_gates(self):
        self.assertEqual(header_problems(header()), [])

    def test_the_old_exactly_one_question_claim_fails_the_check(self):
        """Negative control: the wording before #603 must not satisfy the check."""
        old = header().replace(
            "has one 👉 question that always fires", "has exactly one 👉 question")
        self.assertIn("it still carries the old claim 'exactly one 👉 question'",
                      header_problems(old))
        old_8a = header().replace(
            "Step 8a's License Key gate asks its question when the collected total exceeds the "
            "effective limit",
            "Step 8a's volume-skip passes without a question when the collected total is inside "
            "the license limit, which that step calls the common case")
        self.assertIn("it does not say when Step 8a's gate asks", header_problems(old_8a))

    def test_it_names_step_9_as_that_question(self):
        self.assertRegex(header(), r"(?i)Step 9's module\s+transition")

    def test_it_names_all_three_branches_that_produce_the_run(self):
        block = header()
        self.assertRegex(block, r"(?i)Step 2's marker/provenance guard")
        self.assertRegex(block, r"(?i)Step 8a's volume-skip passes without a question only when")
        self.assertRegex(block, r"(?i)or the limit is `0`")
        self.assertRegex(block, r"(?i)It says nothing at or below that threshold")

    def test_it_says_the_run_is_steps_1_to_8_and_silent_gates(self):
        block = header()
        self.assertRegex(block, r"(?i)Steps 1-8 are all \*\*non-yielding\*\*")
        self.assertRegex(block, r"(?i)and so are Steps 8a and 8b whenever their gate stays silent")
        self.assertRegex(block, r"(?i)inside the turn that ends on the next 👉 question")

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
            r"(?i)Data collection's generated-scenario path, whose Steps 1-8 ask nothing",
            "the instance list enumerates three runs and this is a fourth, so the list is "
            "stale by one",
        )

    def test_the_run_list_names_both_conditional_gates(self):
        block = squash(GROUND_RULES)
        self.assertRegex(block, r"(?i)and whose Steps 8a and 8b ask only when their gates fire")
        self.assertRegex(
            block,
            r"(?i)Step 8a's License Key question when the collected total exceeds the effective "
            r"limit, which a default-sized scenario does under the built-in evaluation license",
        )
        self.assertRegex(
            block,
            r"(?i)Step 8b's SQLite question when the loadable total is above the SQLite threshold",
        )

    def test_the_run_list_drops_the_old_claim(self):
        self.assertNotIn("whose Steps 1-8b ask nothing", squash(GROUND_RULES))

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
        """This fix copies that module's shape; if it moved, the two have diverged.

        The count is two since #479 added the Mari prediction; the ⚠️ marking that names each
        👉 is the shape this fix copied, and it is unchanged.
        """
        self.assertRegex(
            squash(VERIFICATION),
            r"⚠️ \*\*This module has exactly two 👉 questions\*\* — the Mari prediction at Step 7a "
            r"of `phase1-verification\.md`, and the module-transition question",
        )


class TheOverLimitGenerationRuleIsStatedOnce(unittest.TestCase):
    """#603 — one rule for a generated scenario larger than the effective limit."""

    RULE = ("When the effective limit is below the record count the scenario calls for, "
            "generate the full count anyway, and ask nothing here.")

    def test_the_rule_is_in_the_generation_block(self):
        self.assertIn(self.RULE, generation_block())

    def test_the_rule_is_stated_once(self):
        self.assertEqual(squash(COLLECTION).count(self.RULE), 1)

    def test_it_sits_beside_the_record_limit_zero_rule(self):
        block = generation_block()
        self.assertLess(block.index("On a measured `recordLimit: 0`, size the generated data"),
                        block.index(self.RULE))

    def test_it_leaves_capacity_to_steps_8a_and_8b(self):
        block = generation_block()
        rule = block[block.index(self.RULE):]
        self.assertRegex(rule, r"never a gate, and it is not tied to license capacity \(INV-277\)")
        self.assertRegex(rule, r"Step 8a's License Key gate asks when the collected total exceeds")
        self.assertRegex(rule, r"Step 8b warns when the loadable total is above the SQLite")
        self.assertRegex(rule, r"means never measured \(INV-244\), so it is no reason to downsize")
        self.assertRegex(rule, r"loads a license-capped subset of the files generated here, and "
                               r"nothing is regenerated")

    def test_it_states_no_license_figure(self):
        """The built-in limit is sourced at request time; a figure here would go stale."""
        block = generation_block()
        rule = block[block.index(self.RULE):]
        rule = re.sub(r"INV-\d+", "", rule)
        self.assertIsNone(re.search(r"\d[\d,]{2,}", rule), "the over-limit rule states a figure")


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
