"""System verification has one rule for a failure, and a failed run ends on a pinned question.

Two rules in `phase1-verification.md` disagreed. Step 1a said that when the engine does not
initialize, "report the error and stop here rather than proceeding to generation or loading";
Agent Rule 4 said "if any step fails, continue executing all subsequent steps. No
short-circuiting." And a failed run ended on no question at all: `phase2-report-close.md` Step 9
item 7 told the guide to "advise the bootcamper to fix the issues and re-run System verification
from the beginning", which offered nothing to answer and named no step to run next (INV-284).
#529 (part of #504) reconciles the two and pins the end of a failed run:

* Agent Rule 4 names its one exception, a Step 1a failure: Steps 2–8 cannot run, so their checks
  are recorded as `"status": "skipped"`, and Phase 2's report is still written in full;
* Step 1a records each remaining check as `skipped` — the keys are derived from Phase 1's own
  `**Checkpoint:**` blocks, so a check added later is required here too — and goes to Step 9;
* Step 9 item 7 ends a failed run on a pinned 👉 question (INV-051, INV-056) with two numbered
  options, and a handler for each answer that names where the flow resumes (INV-284): retry
  resumes at Phase 1 Step 1, uncapped, as a new state rather than an INV-006 repeat; moving on
  runs Step 10 then Step 11, with the report's module-level `status` left `failed`, because the
  step-9 resume check reads it to re-present the pending question and the report records the
  failed run honestly (#608: the reason was "graduation reads it from there", which no
  graduation file does, and the INV-229 citation named the rule on expectation mismatch);
* an interruption before the answer resumes at the question;
* `SKILL.md` and Phase 1's header say a failed run asks this question too.

⛔ **Each check is a function of the file text, so the negative controls run the SAME check on a
mutated copy** (INV-265). Prose is matched with whitespace collapsed, and every control also runs
on a re-wrapped copy (INV-346). These tests assert that the skill files *state* the rules and
**cannot** establish that a live run follows them, which only `dry-run` phase 3 can observe.

Source issues: #529 (part of #504), #608. Invariants: INV-006, INV-051, INV-056, INV-284, and
INV-371 (the failed status survives moving on), which this file enforces: it pins the rule's text
and its two reasons, and cannot establish that a live run leaves the status alone.

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

from test_database_switch_detours_through_sdk_setup import between, flat, missing, rewrap
from test_module3_check_lists_agree import checkpoint_keys

REPO_ROOT = Path(__file__).resolve().parent.parent
M3 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-03-system-verification"
FILES = {"phase1": M3 / "phase1-verification.md", "phase2": M3 / "phase2-report-close.md",
         "skill": M3 / "SKILL.md"}

QUESTION = ("👉 **System verification found failures. What would you like to do? Reply with a "
            "number:**")
OPTION_1 = "1. Retry System verification from the beginning, once the issues above are fixed."
OPTION_2 = "2. Move on to the next module, with System verification recorded as failed."
#: The prose #529 replaces.
RETIRED = "Advise the bootcamper to fix the issues and re-run System verification"
#: The reason #608 replaces: no graduation file reads Module 3's status.
RETIRED_REASON = "graduation reads it from there"


def read_all():
    return {k: p.read_text(encoding="utf-8") for k, p in FILES.items()}


def rule_4(p1):
    return between(p1, "4. **All checks execute regardless of failures:**",
                   "5. **Artifact isolation:**")


def step_1a(p1):
    return between(p1, "### Step 1a: Engine Initialization Check", "### Step 2:")


def item_7(p2):
    return between(p2, "7. **If any installation check failed**", "**Checkpoint:** write step 9")


def phase1_header(p1):
    return between(p1, "Every step in this phase is NON-YIELDING", "## Opt-Out Gate")


def skill_count(skill):
    return between(skill, "This module has exactly two 👉 questions", "**First:**")


# ---------------------------------------------------------------------------------- checks


def rule_4_problems(p1):
    block = rule_4(p1)
    if block is None:
        return ["phase 1 has no Agent Rule 4"]
    return missing(block, (
        "No short-circuiting.",
        "The one exception is a Step 1a failure.",
        "Steps 2–8 cannot run: record each of their checks as `\"status\": \"skipped\"`",
        "whose Verification Report is still written in full, every check included",
        "Every other failure continues to the next step.",
    ), "Agent Rule 4")


def step_1a_problems(p1):
    block = step_1a(p1)
    if block is None:
        return ["phase 1 has no Step 1a"]
    problems = missing(block, (
        # Pinned by tests/test_engine_verification_and_senz2027.py as well.
        "stop here rather than proceeding to generation or loading",
        "Then record the rest as skipped and go to the report (Agent Rule 4's one exception).",
        "Record `engine_initialization` as `failed`",
        "`\"status\": \"skipped\"`",
        "Step 7a's Mari prediction is not asked",
        "Continue in the same turn to `phase2-report-close.md` Step 9",
        "ends the turn on its retry-or-move-on question",
    ), "Step 1a")
    # Derived from the live file, not the text under test: a re-wrap control re-flows the
    # prose checkpoint Step 1a writes, and the keys are what Step 1a must name, not its subject.
    keys, _ = checkpoint_keys(FILES["phase1"].read_text(encoding="utf-8"))
    if "engine_initialization" not in keys:
        return problems + ["phase 1's checkpoints no longer record engine_initialization"]
    later = keys[keys.index("engine_initialization") + 1:]
    if not later:
        problems.append("no checks follow engine_initialization; the derivation found nothing")
    for key in later:
        if "`%s`" % key not in block:
            problems.append("Step 1a does not record `%s` as skipped" % key)
    return problems


def item_7_problems(p2):
    block = item_7(p2)
    if block is None:
        return ["Step 9 has no item 7 for a failed run"]
    problems = []
    if block.count("👉") != 1:
        problems.append("Step 9 item 7 does not end on exactly one 👉 question")
    # INV-056 pins the wording verbatim; INV-051 wants a neutral lead and a numbered list.
    for needle, what in ((QUESTION, "the pinned question"), (OPTION_1, "option 1, retry"),
                         (OPTION_2, "option 2, move on")):
        if flat(needle) not in flat(block):
            problems.append("Step 9 item 7 does not carry %s verbatim" % what)
    problems += missing(block, (
        "do NOT proceed to cleanup yet",
        "*(Internal: end the turn on this question and wait.)*",
        "Handling each answer (INV-284).",
        # Option 1: where it resumes, no second confirmation, uncapped as a new state.
        "1, \"Retry\":",
        "(INV-006) The answer IS the go-ahead, so ask no second confirmation.",
        "Resume at `phase1-verification.md` Step 1",
        "Retries are not capped: each attempt measures a new state",
        "is NOT an INV-006 repeat and MUST NOT be suppressed as one",
        # Option 2: where it resumes, and the status it leaves.
        "2, \"Move on\":",
        "run Step 10 (Cleanup), then Step 11 (Module Close)",
        "⛔ **(INV-371) The report's module-level `status` stays `failed`:** do not rewrite it on "
        "the way "
        "out.",
        "The step-9 resume check below reads it to re-present the pending question",
        "the report must record honestly that the run failed",
        # An interruption.
        "An interruption that leaves this question unanswered resumes at it.",
        "re-present it verbatim",
        "rather than going on to Step 10",
    ), "Step 9 item 7")
    question = flat(block).find(flat(QUESTION))
    handling = flat(block).find("Handling each answer (INV-284).")
    if question != -1 and handling != -1 and handling < question:
        problems.append("Step 9 item 7 handles the answers before it asks the question")
    return problems


def retired_problems(p2):
    problems = []
    if flat(RETIRED) in flat(p2):
        problems.append("Step 9 still only advises a re-run instead of asking")
    if flat("Please resolve the issues above and re-run system verification.") in flat(p2):
        problems.append("the failure banner still tells the bootcamper only to re-run")
    if flat(RETIRED_REASON) in flat(p2):
        problems.append("the failed-status rule still says graduation reads the status")
    return problems


def count_problems(skill, p1):
    problems = []
    block = skill_count(skill)
    if block is None:
        problems.append("SKILL.md no longer counts the module's 👉 questions")
    else:
        problems += missing(block, (
            "That count is a passing run's. A failed run also asks Step 9's retry-or-move-on "
            "question",
            "skips Steps 2–8 and the Mari prediction",
        ), "SKILL.md")
    header = phase1_header(p1)
    if header is None:
        problems.append("phase 1 has no header before the opt-out gate")
    else:
        problems += missing(header, (
            "A failed run asks one more 👉: Step 9's retry-or-move-on question",
            "Every turn still ends on exactly one 👉.",
        ), "phase 1's header")
    return problems


def all_problems(f):
    return (rule_4_problems(f["phase1"]) + step_1a_problems(f["phase1"])
            + item_7_problems(f["phase2"]) + retired_problems(f["phase2"])
            + count_problems(f["skill"], f["phase1"]))


# ----------------------------------------------------------------------------------- tests


class TheLiveFilesMeetEveryCriterion(unittest.TestCase):
    def setUp(self):
        self.f = read_all()

    def test_the_sites_are_found(self):
        """⛔ INV-265: a scan of a moved site certifies nothing."""
        self.assertIsNotNone(rule_4(self.f["phase1"]))
        self.assertIsNotNone(step_1a(self.f["phase1"]))
        self.assertIsNotNone(item_7(self.f["phase2"]))
        self.assertIsNotNone(phase1_header(self.f["phase1"]))
        self.assertIsNotNone(skill_count(self.f["skill"]))
        keys, unread = checkpoint_keys(self.f["phase1"])
        self.assertEqual([], unread)
        self.assertGreaterEqual(len(keys), 9, "phase 1's checkpoints moved; nothing is derived")

    def test_rule_4_names_the_step_1a_exception(self):
        self.assertEqual([], rule_4_problems(self.f["phase1"]))

    def test_step_1a_records_the_remaining_checks_as_skipped(self):
        self.assertEqual([], step_1a_problems(self.f["phase1"]))

    def test_a_failed_run_ends_on_the_pinned_question_with_both_handlers(self):
        self.assertEqual([], item_7_problems(self.f["phase2"]))

    def test_the_advice_only_ending_is_retired(self):
        self.assertEqual([], retired_problems(self.f["phase2"]))

    def test_the_question_count_says_what_a_failed_run_adds(self):
        self.assertEqual([], count_problems(self.f["skill"], self.f["phase1"]))

    def test_the_question_is_stated_once(self):
        """INV-300: the pinned wording lives in Step 9 only."""
        self.assertEqual(1, self.f["phase2"].count(QUESTION))
        self.assertNotIn(QUESTION, self.f["phase1"])
        self.assertNotIn(QUESTION, self.f["skill"])

    def test_a_rewrap_still_passes(self):
        """INV-346: the checks read prose, not line breaks."""
        self.assertEqual([], all_problems({k: rewrap(v) for k, v in self.f.items()}))


class EachCheckFailsWhenItsSiteIsBroken(unittest.TestCase):
    """Negative controls: the same checks, run on mutated copies, must each report a problem."""

    def setUp(self):
        self.f = read_all()

    def mutate(self, name, old, new=""):
        self.assertIn(old, self.f[name], "negative control is stale: %r is gone" % old[:60])
        return dict(self.f, **{name: self.f[name].replace(old, new, 1)})

    def assertCaught(self, f):
        self.assertNotEqual([], all_problems(f))
        self.assertNotEqual([], all_problems({k: rewrap(v) for k, v in f.items()}),
                            "a re-wrapped regression was missed")

    def test_rule_4_loses_its_exception(self):
        self.assertCaught(self.mutate("phase1", "**The one exception is a Step 1a failure.**",
                                      "**There are no exceptions.**"))

    def test_step_1a_drops_a_skipped_check(self):
        self.assertCaught(self.mutate("phase1", "`build_compilation`, `data_source_registration`",
                                      "`data_source_registration`"))

    def test_step_1a_no_longer_goes_to_the_report(self):
        self.assertCaught(self.mutate(
            "phase1", "Continue in the same turn to `phase2-report-close.md` Step 9",
            "End the module here"))

    def test_the_question_removed(self):
        self.assertCaught(self.mutate("phase2", QUESTION + "\n", ""))

    def test_the_question_as_prose(self):
        self.assertCaught(self.mutate("phase2", QUESTION, "Ask whether to retry or move on."))

    def test_the_options_joined_with_or(self):
        self.assertCaught(self.mutate(
            "phase2", OPTION_1 + "\n   " + OPTION_2,
            "1. Retry System verification or move on to the next module."))

    def test_the_retry_handler_removed(self):
        self.assertCaught(self.mutate("phase2", "Resume at `phase1-verification.md` Step 1",
                                      "Start again"))

    def test_retries_capped(self):
        self.assertCaught(self.mutate("phase2", "Retries are not capped",
                                      "Retries are capped at three"))

    def test_the_move_on_handler_skips_cleanup(self):
        self.assertCaught(self.mutate("phase2",
                                      "run Step 10 (Cleanup), then Step 11 (Module Close)",
                                      "run Step 11 (Module Close)"))

    def test_moving_on_rewrites_the_status(self):
        self.assertCaught(self.mutate(
            "phase2", "The report's module-level `status` stays `failed`:",
            "Set the report's module-level `status` to `passed`:"))

    def test_the_status_rule_cites_inv_229_again(self):
        """#608: INV-229 governs expectation mismatch, not the status surviving move-on."""
        self.assertCaught(self.mutate(
            "phase2", "⛔ **(INV-371) The report's module-level `status` stays `failed`:**",
            "⛔ **(INV-229) The report's module-level `status` stays `failed`:**"))

    def test_the_graduation_reason_restored(self):
        self.assertCaught(self.mutate(
            "phase2", "the run failed.\n",
            "the run failed. On the way out, graduation reads it from there.\n"))

    def test_the_resume_reason_dropped(self):
        self.assertCaught(self.mutate(
            "phase2", "The step-9 resume check below reads it to re-present the pending question,",
            "The guide reads it later,"))

    def test_the_interruption_rule_removed(self):
        self.assertCaught(self.mutate("phase2",
                                      "An interruption that leaves this question unanswered resumes at it.",
                                      "An interruption goes on to Step 10."))

    def test_the_advice_only_ending_restored(self):
        self.assertCaught(self.mutate(
            "phase2", "do NOT proceed to\n   cleanup yet.",
            "do NOT proceed to\n   cleanup. " + RETIRED + " from the beginning."))

    def test_the_skill_count_forgets_the_failed_run(self):
        self.assertCaught(self.mutate("skill", "That count is a passing run's.", ""))

    def test_the_phase1_header_forgets_the_failed_run(self):
        self.assertCaught(self.mutate("phase1", "A failed run asks one more 👉", "A failed run"))


if __name__ == "__main__":
    unittest.main()
