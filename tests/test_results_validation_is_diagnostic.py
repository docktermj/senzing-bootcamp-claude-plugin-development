"""A results mismatch must be diagnosed, not reported as the bootcamper's system failing.

System verification's Step 2 asks the guide to invent synthetic records and **predict how Senzing
will resolve them**, from its own reasoning. Step 7 then grades the engine against that prediction
and writes a pass/fail check. So a miscalibrated prediction reports a **verification failure on a
healthy install** — at the end of the module whose entire purpose is to tell the bootcamper their
install works.

Observed on a real walk (Senzing 4.3.4, 2026-08-13): three records for one person with the first
name varied `Marisol` / `Mari` / `Marisol` and one record missing its phone resolved to **3
entities** and Step 7 reported FAILED; the same three with the name identical and only formatting
varied resolved to **2 entities** and passed. The engine was right both times. `Mari` is a nickname
variant and that record carried one fewer corroborating feature, so declining to merge is
defensible — arguably correct.

Two causes compound, and the fix has to address both:

* **"Trivial variation" carried all the load and was undefined.** The two attempts differ *only* in
  how that phrase was read.
* **Nothing could distinguish a wrong prediction from an engine fault**, so every mismatch read as
  the latter.

⛔ This is also the one place the module asks the guide to assert engine behavior unaided — the
class of claim INV-080 exists to prevent. The remedy is not to fetch the prediction from somewhere
(there is nowhere) but to make the construction unambiguous and then let the engine explain itself
when the outcome differs.

Enforces **INV-229** — a guide-made prediction's mismatch is diagnosed against the engine's own explanation before it is reported as an install failure.

⛔ **The report that GRADES the check is in a third file, and the first version of this guard could
not see it.** Step 7 diagnosing correctly buys nothing while `phase2-report-close.md` Step 9 records
"Pass or fail status" and branches on "If ANY checks failed" — that path printed
`SYSTEM VERIFICATION: FAILURES DETECTED … re-run system verification`, skipped Step 10's `VERIFY`
purge (leaving the synthetic records in the database), and told the recap to capture "all 8 checks
passed". So the failure INV-229 forbids survived one step later for a day, under 24 green
assertions, two of them named `test_a_coherent_explanation_does_not_fail_the_system` and
`test_it_forbids_the_false_report_here_too`. A guard that reads only the files the implementer
edited certifies the one place a regression will not come from.

Source specs: `specs/verification-grades-the-engine-against-the-guides-own-prediction.md` (Step 7,
SKILL.md) and `specs/verification-report-cannot-express-an-expectation-mismatch.md` (Step 9, the
schemas, the cleanup gate, the recap line).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
M3 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-03-system-verification"
PHASE1 = M3 / "phase1-verification.md"
PHASE2 = M3 / "phase2-report-close.md"
SKILL = M3 / "SKILL.md"

#: The third outcome: counts differed and the engine's own explanation accounts for it, so the
#: install is working and the prediction was wrong. Recording it as `failed` is the false report;
#: recording it as `passed` hides a result worth telling the bootcamper about.
THIRD_STATUS = "expectation_mismatch"


def squash(text):
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M))


def section(path, start, end):
    text = path.read_text(encoding="utf-8")
    i = text.index(start)
    j = text.find(end, i + len(start))
    return squash(text[i:j if j != -1 else len(text)])


def step_2():
    return section(PHASE1, "### Step 2: Generate Synthetic Verification Records", "### Step 3")


def step_7():
    return section(PHASE1, "### Step 7: Deterministic Results Validation", "### Step 8")


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_files_exist(self):
        for path in (PHASE1, SKILL):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path)

    def test_both_steps_are_locatable(self):
        self.assertIn("merge cluster", step_2(), "Step 2 was not located")
        self.assertIn("Entity count", step_7(), "Step 7 was not located")


class TheMergeClusterIsUnambiguousByConstruction(unittest.TestCase):
    def setUp(self):
        self.step = step_2()

    def test_the_undefined_phrase_is_gone(self):
        self.assertNotRegex(
            self.step,
            r"(?i)sharing enough features\s*\(matching full name \+ date of birth \+ address, with "
            r"only trivial variation\)",
            "the phrase that produced two opposite verdicts is still doing all the work")

    def test_it_says_construction_not_judgment(self):
        self.assertRegex(
            self.step, r"(?i)Make this unambiguous by construction, not by judgment",
            "nothing states the principle the constraints below implement")

    def test_the_sameness_constraints_are_explicit(self):
        for required in (r"`NAME_FIRST`, `NAME_LAST`, and `NAME_MIDDLE` wherever present",
                         r"`DATE_OF_BIRTH`",
                         r"(?i)address \*\*content\*\*",
                         r"(?i)the same feature \*set\*"):
            with self.subTest(constraint=required[:40]):
                self.assertRegex(self.step, required,
                                 "a sameness constraint is missing")

    def test_the_permitted_variation_is_an_explicit_allowlist(self):
        self.assertRegex(self.step, r"(?i)May vary — formatting only",
                         "what may vary is not enumerated")
        for allowed in ("Punctuation and spacing", "Phone-number formatting",
                        "abbreviated to its initial"):
            with self.subTest(allowed=allowed):
                self.assertIn(allowed, self.step, "a permitted variation is missing")

    def test_the_three_disqualifying_variations_are_named(self):
        self.assertRegex(
            self.step, r"(?i)These are NOT trivial variation",
            "nothing rules out the variations that caused the false failure")
        for banned in (r"(?i)\*\*nickname\*\*", r"(?i)\*\*initial in place of a first name\*\*",
                       r"(?i)\*\*omitted feature\*\*"):
            with self.subTest(banned=banned):
                self.assertRegex(self.step, banned, "a disqualifying variation is unnamed")

    def test_it_says_why_they_disqualify(self):
        self.assertRegex(
            self.step, r"(?i)reduces corroboration",
            "the ban is stated without its mechanism, so it reads as arbitrary")
        self.assertRegex(
            self.step, r"(?i)defensible resolution decision, not a fault",
            "nothing says the engine declining to merge is correct behavior")

    def test_the_worked_counter_example_is_present(self):
        """The spec's fourth proposal: a real case makes 'trivial' concrete."""
        self.assertRegex(self.step, r"(?i)Worked counter-example",
                         "the counter-example is missing")
        for detail in ("Marisol", "Mari", "3 entities", "2 entities"):
            with self.subTest(detail=detail):
                self.assertIn(detail, self.step,
                              "the counter-example lost a load-bearing detail")
        self.assertRegex(
            self.step, r"(?i)The engine was right both times",
            "the counter-example does not state its conclusion")

    def test_the_observation_is_marked_as_an_observation(self):
        """INV-080/INV-149: engine behavior seen on one install is not an MCP claim."""
        self.assertRegex(
            self.step,
            r"(?i)observation of this\s*install's behavior, not an MCP claim",
            "a measured engine behavior is stated without being marked observation-only")


class AMismatchIsDiagnosed(unittest.TestCase):
    def setUp(self):
        self.step = step_7()

    def test_a_failure_is_framed_as_a_diagnostic(self):
        self.assertRegex(
            self.step,
            r"(?i)this is a DIAGNOSTIC, not a verdict on the install",
            "a failing check still reads as a verdict on the bootcamper's system")
        self.assertRegex(
            self.step, r"(?i)two\s*candidate explanations",
            "the two causes are not named, so there is nothing to tell apart")

    def test_it_says_why_this_check_is_different(self):
        self.assertRegex(
            self.step,
            r"(?i)compares the engine against \*\*a prediction the guide made\*\*",
            "the reason this check is unlike the installation checks is unstated")

    def test_it_asks_the_engine_why(self):
        self.assertRegex(self.step, r"(?i)Ask the engine why, before concluding anything",
                         "no lookup is triggered on a mismatch")
        self.assertIn("why_records", self.step, "why_records is not called")
        self.assertIn("why_entities", self.step, "why_entities is not called")
        self.assertRegex(
            self.step, r"(?i)get_sdk_reference` \+\s*`sdk_guide` — never from memory",
            "the why_* call is not routed through the MCP tools (INV-080)")

    def test_it_reports_the_match_key_and_feature_scores(self):
        self.assertRegex(
            self.step, r"(?i)\*\*match key\*\* and the \*\*feature scores\*\*",
            "the engine's explanation is requested but its content is not reported")

    def test_a_coherent_explanation_does_not_fail_the_system(self):
        self.assertRegex(
            self.step,
            r"(?i)the expectation was\s*wrong, and the install is fine",
            "an explained mismatch still reports the install as broken")
        self.assertRegex(
            self.step, r"(?i)Do not report the system as having failed verification",
            "nothing forbids the false report this spec exists to stop")
        self.assertRegex(
            self.step, r"(?i)do not tell the\s*bootcamper to re-run the load",
            "the old remedy — re-run the load — is still offered for a case where "
            "nothing is wrong with the load")

    def test_an_unexplained_mismatch_still_fails(self):
        self.assertRegex(
            self.step,
            r"(?i)does not account for the difference",
            "the real-finding branch is gone, so the check can no longer fail at all")
        self.assertRegex(
            self.step, r"(?i)this is a real finding",
            "the second branch does not say it is a genuine failure")

    def test_the_check_is_reported_separately(self):
        self.assertRegex(
            self.step,
            r"(?i)reported separately from the other checks",
            "a mismatch can still turn the module's overall result into a failure")

    def test_the_four_checks_still_exist(self):
        for check in ("Entity count", "Merge cluster resolves to one entity",
                      "Cross-record resolution", "Distractor stays a singleton"):
            with self.subTest(check=check):
                self.assertIn(check, self.step, "a validation check was lost")


class TheSuccessIndicatorDistinguishesTheChecks(unittest.TestCase):
    def setUp(self):
        self.flat = squash(SKILL.read_text(encoding="utf-8"))

    def test_it_no_longer_lumps_all_eight_together(self):
        self.assertNotRegex(
            self.flat,
            r'(?i)✅ All 8 System Verification checks report "passed"',
            "the success indicator still gives the bootcamper no way to tell an install "
            "failure from a wrong prediction")

    def test_it_names_the_eight_install_checks(self):
        # #282: the count was "7" and each "seven" list dropped a different check. Phase 1
        # records eight installation checkpoints; the lists are pinned to Phase 1's own
        # `**Checkpoint:**` keys by `test_module3_check_lists_agree.py`.
        self.assertRegex(
            self.flat, r"(?i)\*\*8 installation checks\*\*",
            "the install checks are not counted separately")
        for check in ("MCP connectivity", "engine initialization", "SDK initialization",
                      "code generation", "build", "data-source registration", "loading",
                      "database operations"):
            with self.subTest(check=check):
                self.assertIn(check, self.flat, "an install check is unnamed")

    def test_it_marks_results_validation_as_separate(self):
        self.assertRegex(
            self.flat,
            r"(?i)\*\*results validation\*\*, which is reported separately",
            "results validation is not distinguished in the success indicator")
        self.assertRegex(
            self.flat, r"(?i)Results validation is kept separate on purpose",
            "the separation is done without its reason, so a later editor will merge it "
            "back for tidiness")

    def test_it_forbids_the_false_report_here_too(self):
        self.assertRegex(
            self.flat,
            r"(?i)is an expectation mismatch, \*\*not\*\* a failed verification",
            "the rule is stated only in phase 1; the success indicator is where a reader "
            "decides what to tell the bootcamper")


class TheReportCanExpressTheThirdOutcome(unittest.TestCase):
    """Step 9 grades the module. A binary report undoes Step 7's diagnosis one step later."""

    def setUp(self):
        self.raw = PHASE2.read_text(encoding="utf-8")
        self.flat = squash(self.raw)

    def test_the_file_exists(self):
        self.assertTrue(PHASE2.is_file(), "%s is missing" % PHASE2)

    def test_the_check_status_admits_a_third_value(self):
        self.assertRegex(
            self.raw,
            r'"results_validation":\s*\{"status":\s*"passed\|%s\|failed"' % THIRD_STATUS,
            "Step 9's persisted schema still offers only passed|failed, so the outcome "
            "Step 7 defines cannot be recorded — and graduation reads this file, not the prose")

    def test_phase1_checkpoint_admits_it_too(self):
        self.assertRegex(
            PHASE1.read_text(encoding="utf-8"),
            r'"results_validation":\s*\{"status":\s*"passed\|%s\|failed"' % THIRD_STATUS,
            "Step 7 defines a third outcome in prose and writes a two-valued checkpoint "
            "eight lines below it")

    def test_the_engine_explanation_is_carried_into_state(self):
        self.assertIn(
            "engine_explanation", self.raw,
            "the why_* match key and feature scores are computed in Step 7 and dropped "
            "before Step 9 can report them")

    def test_the_success_branch_is_scoped_to_the_install_checks(self):
        # ⚠️ Anchored to "display a success banner". The bare phrase also appears at item 6
        # (proceed to Step 10), so an unanchored regex passed on the WRONG site while the
        # banner branch read "If ALL checks passed" — caught by its own negative control.
        self.assertRegex(
            self.flat,
            r"(?i)If all the installation checks passed:\*\* display a success banner",
            "the success banner still branches on ALL checks, so an explained mismatch "
            "cannot reach it")
        self.assertNotRegex(
            self.flat, r"(?i)\*\*If ALL checks passed:\*\* display",
            "the ALL-checks wording is still on the banner branch")

    def test_the_failure_branch_is_scoped_to_the_install_checks(self):
        self.assertNotRegex(
            self.flat, r"(?i)\*\*If ANY checks failed:\*\*",
            "the failure summary still fires on any check, which is the FAILURES DETECTED "
            "banner on a healthy install")
        self.assertRegex(
            self.flat, r"(?i)If ANY of the installation checks failed",
            "the failure branch does not say which checks it reads")

    def test_the_banner_does_not_claim_all_checks_passed(self):
        self.assertNotIn(
            "All checks passed.", self.raw,
            "the banner is displayed on an expectation_mismatch, so this wording is false "
            "there — and it is bootcamper-facing")

    def test_the_mismatch_is_kept_out_of_the_failure_summary(self):
        self.assertRegex(
            self.flat,
            r"(?i)An `%s` MUST NOT appear here" % THIRD_STATUS,
            "nothing forbids listing an explained mismatch as a failed check")

    def test_the_mismatch_is_reported_beneath_the_banner(self):
        self.assertRegex(
            self.flat,
            r"(?i)Report `results_validation` beneath the banner",
            "the banner speaks only for the install checks, so nothing tells the "
            "bootcamper what results validation returned")

    def test_cleanup_is_not_gated_on_the_mismatch(self):
        self.assertNotRegex(
            self.flat, r"(?i)\*\*If all checks passed:\*\* proceed to Step 10",
            "cleanup is still gated on every check, so an explained mismatch skips the "
            "VERIFY purge and strands the synthetic records")
        self.assertRegex(
            self.flat, r"(?i)Cleanup MUST NOT be gated on an `%s`" % THIRD_STATUS,
            "the reason cleanup must still run is unstated, so a later edit re-gates it")

    def test_the_module_status_comes_from_the_install_checks(self):
        self.assertRegex(
            self.flat,
            r"(?i)module-level `status` is set from the installation checks only",
            "a healthy install can still be recorded as a failed module, and graduation "
            "reads that value")

    def test_the_recap_line_is_not_an_unconditional_claim(self):
        self.assertNotRegex(
            self.flat, r"(?i)capture that all 8 checks passed",
            "the recap — the keepsake — is still told to assert something that is false "
            "on the expectation_mismatch path")
        self.assertNotRegex(
            self.flat, r"(?i)all \d+ (?:System Verification )?checks passed",
            "a counted all-passed claim is back, and it counts results validation among the "
            "checks that passed")
        self.assertRegex(
            self.flat, r"(?i)Never write that every check passed unconditionally",
            "nothing stops the unconditional claim being restored for tidiness")

    def test_the_fix_instructions_exclude_the_mismatch(self):
        self.assertRegex(
            self.flat,
            r"(?i)An `%s` contributes NO entry" % THIRD_STATUS,
            "an explained mismatch can still generate remediation text for something "
            "that needs no remediation")


if __name__ == "__main__":
    unittest.main()
