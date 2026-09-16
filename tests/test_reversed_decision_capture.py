"""A reversed decision must be filed when it happens, not recalled at graduation.

The graduation retrospective (`graduation/SKILL.md` Step 0) has existed for a while and is
thorough, but it asks the assistant to *review this session* — and by graduation the session
may have crossed several compaction boundaries, so the most valuable findings are exactly the
ones least likely to still be in context. A reported run lost these:

* `EFX_YREST` ("year business established") mapped onto the feature already carrying an
  incorporation filing date. The two measure different things, so the sources systematically
  disagreed and Senzing correctly suppressed merges over a conflict that was an artifact of
  the mapping. **Every static quality gate passed, and the data-quality score went UP when the
  bad mapping was added.** Only the match-key audit — reading the engine's own output —
  exposed it.
* Three defects in a quality-scoring implementation the assistant wrote. Correcting one
  honestly *lowered* the reported score.
* A proposed identifier remap, abandoned after checking the Entity Specification. Cheap
  because it happened before it was acted on; invisible afterwards.

⚠️ Those Senzing specifics are **field observations from one run** and are deliberately NOT
asserted as facts anywhere here or in shipped guidance — INV-080 requires re-asking the server,
and this spec's own criteria forbid promoting them. What these tests pin is the *mechanism*.

What is asserted:

* the trigger is a **named condition** with its three concrete cases, not "notice reversals"
* it fires at the step that actually detects it — the match-key audit
* the append is silent (no banner, no 👉) and never blocks
* graduation **sweeps** for withdrawn mappings, corrected scoring code and abandoned
  proposals, and does not re-file what the in-run path already recorded
* an entry written this way still parses with `feedback_ledger.py check`
* the score-cannot-see-semantics guidance — which predates this spec — stays put

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SKILLS = os.path.join(PLUGIN, "skills")
GROUND_RULES = os.path.join(SKILLS, "bootcamp-onboarding", "ground-rules.md")
FEEDBACK = os.path.join(SKILLS, "bootcamp-onboarding", "feedback.md")
GRADUATION = os.path.join(SKILLS, "graduation", "SKILL.md")
PHASE_D = os.path.join(SKILLS, "module-06-data-processing", "phaseD-validation.md")
QUALITY = os.path.join(
    SKILLS, "module-05-data-quality-mapping", "phase1-quality-assessment.md"
)
LEDGER = os.path.join(
    REPO_ROOT, ".claude", "skills", "feedback-to-issues", "feedback_ledger.py"
)

SOURCE_VALUE = "self-observed (assistant retrospective)"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def flat(path):
    return re.sub(r"\s+", " ", read(path))


def section(text, start, end=None):
    """The slice from heading `start` up to `end` — or to EOF when `end` is absent.

    Tolerating a missing `end` matters: the in-run append path is the LAST section of
    `feedback.md`, so demanding a following heading makes the helper raise rather than
    return the section it was asked for.
    """
    begin = text.index(start)
    if end is None:
        return text[begin:]
    try:
        return text[begin : text.index(end, begin + len(start))]
    except ValueError:
        return text[begin:]


class TheTriggerIsANamedCondition(unittest.TestCase):
    """"Capture reversals" is unactionable; a condition is checkable."""

    def setUp(self):
        self.rules = read(GROUND_RULES)
        self.flatrules = flat(GROUND_RULES)

    def test_the_rule_exists_in_the_ground_rules(self):
        self.assertIn("Reversed decisions: file them when they happen", self.rules)

    def test_it_rejects_a_disposition_in_favor_of_a_condition(self):
        self.assertRegex(
            self.flatrules, r"(?i)The trigger is a named condition, not a disposition"
        )

    def test_all_three_concrete_conditions_are_named(self):
        for phrase in (
            r"match-key audit finding leads to a mapping being changed or removed",
            r"scoring implementation you wrote is corrected",
            r"proposed change is abandoned",
        ):
            with self.subTest(condition=phrase):
                self.assertRegex(self.flatrules, r"(?i)" + phrase)

    def test_the_correction_that_lowers_a_number_is_explicitly_included(self):
        """The most useful reversal is the one nobody wants to file."""
        self.assertRegex(self.flatrules, r"(?i)correction \*?\*?lowers\*?\*? the reported number")

    def test_the_signal_is_the_engines_output_not_a_static_gate(self):
        """All three significant reversals came from engine output; no gate caught any."""
        self.assertRegex(self.flatrules, r"(?i)Why the engine's output and not a gate")
        self.assertRegex(
            self.flatrules,
            r"(?i)Every static gate can pass while a mapping is semantically wrong",
        )

    def test_it_routes_to_the_append_path_with_the_right_source_value(self):
        self.assertIn("Silent in-run append", self.rules)
        self.assertIn(SOURCE_VALUE, self.rules)


class TheAppendIsSilentAndNonBlocking(unittest.TestCase):
    """INV-012 and INV-048: the Bootcamper neither sees nor waits on this."""

    def setUp(self):
        self.feedback = read(FEEDBACK)
        self.entry = section(self.feedback, "## Silent in-run append", "\n## ")

    def test_the_append_path_exists(self):
        self.assertIn("## Silent in-run append", self.feedback)

    def test_it_says_the_bootcamper_facing_flow_does_not_apply(self):
        """Reusing the file must not mean reusing the banners and questions."""
        flatsec = re.sub(r"\s+", " ", self.entry)
        self.assertRegex(flatsec, r"(?i)none of it applies here")

    def test_it_forbids_a_banner_and_a_question(self):
        flatsec = re.sub(r"\s+", " ", self.entry)
        self.assertRegex(flatsec, r"(?i)No banners, no 👉 question")
        self.assertIn("INV-012", self.entry)

    def test_it_never_blocks(self):
        self.assertRegex(re.sub(r"\s+", " ", self.entry), r"(?i)Never blocks")
        self.assertIn("INV-048", self.entry)

    def test_it_does_not_offer_the_upstream_forward(self):
        """That offer needs a 👉 question, which this path must not ask."""
        flatsec = re.sub(r"\s+", " ", self.entry)
        self.assertRegex(flatsec, r"(?i)Do not offer the upstream forward here")

    def test_it_keeps_the_verify_it_landed_discipline(self):
        """An unwritten silent note is worse than none — nobody is watching."""
        self.assertRegex(re.sub(r"\s+", " ", self.entry), r"(?i)Verify it landed")

    def test_it_stays_local(self):
        self.assertRegex(re.sub(r"\s+", " ", self.entry), r"(?i)Local only")

    def test_it_reuses_the_step_3_template_rather_than_a_variant(self):
        """A second template is a second thing to keep in sync with the ledger."""
        self.assertRegex(
            re.sub(r"\s+", " ", self.entry), r"(?i)Step 3 template verbatim"
        )


class GraduationSweepsRatherThanRecalls(unittest.TestCase):

    def setUp(self):
        self.text = read(GRADUATION)
        self.step0 = section(self.text, "## Step 0:", "\n## Step 1")
        self.flat0 = re.sub(r"\s+", " ", self.step0)

    def test_it_says_not_to_rely_on_memory(self):
        self.assertRegex(self.flat0, r"(?i)do not rely on remembering them")
        self.assertRegex(self.flat0, r"(?i)compaction boundaries")

    def test_it_sweeps_for_all_three_artifacts(self):
        for phrase in (
            r"Withdrawn or changed mappings",
            r"Corrected scoring or accuracy code",
            r"Abandoned proposals",
        ):
            with self.subTest(sweep=phrase):
                self.assertRegex(self.flat0, r"(?i)" + phrase)

    def test_the_sweep_names_where_to_look(self):
        """A sweep with no target is a recall prompt wearing a different hat."""
        self.assertIn("docs/data_source_evaluation.md", self.step0)
        self.assertRegex(self.flat0, r"(?i)mapper code under `src/`")

    def test_it_does_not_double_file_what_the_in_run_path_recorded(self):
        self.assertRegex(self.flat0, r"(?i)Do not re-file what is already there")
        self.assertRegex(self.flat0, r"(?i)Read the existing entries first")

    def test_the_four_recall_categories_survive(self):
        """The sweep is additive; it must not have displaced what was there."""
        for category in ("False starts", "Errors", "Course corrections", "Learnings"):
            with self.subTest(category=category):
                self.assertIn(category, self.step0)

    def test_it_still_files_with_the_self_observed_source(self):
        self.assertIn(SOURCE_VALUE, self.step0)

    def test_it_is_still_non_blocking_and_not_a_gate(self):
        self.assertRegex(self.flat0, r"(?i)Non-blocking")
        self.assertRegex(self.flat0, r"(?i)Not a gate")


class TheAuditStepFiresTheTrigger(unittest.TestCase):
    """The rule is stated once in ground-rules and must fire where it is detected.

    A rule stated only centrally is a rule nobody reads at the moment it applies
    (INV-183). The match-key audit is the step that reads engine output and overturns a
    mapping, so it is the step that has to say "file it now".
    """

    def setUp(self):
        self.text = read(PHASE_D)
        self.flat = re.sub(r"\s+", " ", self.text)

    def test_the_audit_step_names_the_filing_obligation(self):
        self.assertRegex(
            self.flat,
            r"(?i)If a finding here causes a mapping to change or be withdrawn, file it",
        )

    def test_it_points_at_the_single_statement_of_the_rule(self):
        self.assertRegex(self.flat, r"(?i)Reversed decisions: file them when they happen")

    def test_it_says_why_here_rather_than_at_graduation(self):
        self.assertRegex(self.flat, r"(?i)by then the reasoning may have been compacted away")

    def test_it_is_silent_and_non_blocking_at_the_step_too(self):
        self.assertRegex(self.flat, r"(?i)No banner, no question, never blocking")

    def test_the_audits_three_outcomes_are_unchanged(self):
        """This added a sixth step; it must not have disturbed the audit itself."""
        self.assertRegex(self.flat, r"(?i)three\*?\*? outcomes, not two")
        self.assertRegex(self.flat, r"(?i)could-not-measure|could not measure")


class TheScoreCannotDetectSemanticsGuidanceStays(unittest.TestCase):
    """⚠️ This criterion was ALREADY satisfied before this spec was implemented.

    The spec proposed adding it; `phase1-quality-assessment.md` already carried it, and
    `phaseD-validation.md` already carried the match-key audit that answers it. These are
    regression guards for text this spec did not write — pinned here because the spec's
    criterion names it, and an unpinned guarantee is one refactor from gone.
    """

    def test_the_score_disclaims_semantic_correctness(self):
        text = flat(QUALITY)
        self.assertRegex(text, r"(?i)What this score does not measure")
        self.assertRegex(
            text, r"(?i)says nothing about whether a field will be mapped to a feature"
        )

    def test_it_names_the_match_key_audit_as_what_can(self):
        self.assertRegex(
            flat(QUALITY),
            r"(?i)semantic correctness is only established after loading, by the match-key audit",
        )

    def test_it_states_a_high_score_can_still_hide_a_suppressor(self):
        self.assertRegex(
            flat(QUALITY),
            r"(?i)can score \d+% and still carry a mapping that suppresses",
        )

    def test_the_audit_names_the_static_gates_it_compensates_for(self):
        text = flat(PHASE_D)
        self.assertRegex(text, r"(?i)static, single-source, and\*?\*? structural")
        self.assertRegex(text, r"(?i)None of\s*\*?\*?them evaluates \*?meaning")


class AnInRunEntryIsStillMachineReadable(unittest.TestCase):
    """Criterion 5, run rather than asserted: the shared template must keep parsing.

    If the in-run path drifted into its own entry format, `feedback-to-issues` would stop
    seeing these entries — the worst failure mode, because the file would look full while
    the triage tool reported nothing to do.
    """

    ENTRY = """# Senzing Bootcamp Plugin Feedback

## Your Feedback

## Improvement: a mapping withdrawn after the match-key audit

**Date:** 2026-07-31
**Module:** Data processing
**Priority:** Medium
**Source:** %s
**Routing:** plugin — the guidance let two differently-meaning fields reach one feature
**Upstream:** not applicable

### What happened

Two source fields measuring different things were mapped to one feature. The match-key
audit showed that feature detracting on a large share of cross-source comparisons, so the
mapping was withdrawn and one field routed to payload instead.

### Why it matters

Every static gate passed while the mapping was wrong.

### Suggested fix

State at the mapping step that two fields reaching one feature must be checked for shared
meaning, not just for shared type.
""" % SOURCE_VALUE

    def test_the_ledger_parses_an_entry_this_path_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self.ENTRY)
            result = subprocess.run(
                [sys.executable, LEDGER, "check", path],
                capture_output=True, text=True, cwd=REPO_ROOT,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            # Assert on the JSON payload rather than the human VERDICT line, which the
            # helper writes to stderr — the machine contract is what matters here.
            import json

            payload = json.loads(result.stdout)
            self.assertEqual(1, payload["entries_total"], "the entry must be seen")
            self.assertEqual([], payload["known"])
            self.assertEqual(1, len(payload["new"]))
            self.assertIn(
                "a mapping withdrawn after the match-key audit",
                payload["new"][0]["title"],
            )
            self.assertTrue(payload["new"][0]["entry_id"], "content-addressed id required")

    def test_the_source_value_matches_what_the_triage_skill_expects(self):
        """`feedback-to-issues` Step 2 keys weighting off this exact string."""
        triage = read(
            os.path.join(REPO_ROOT, ".claude", "skills", "feedback-to-issues", "SKILL.md")
        )
        self.assertIn(SOURCE_VALUE, triage)


class TheIllustrativeSenzingFactsAreNotPromoted(unittest.TestCase):
    """INV-080: the entry's Senzing specifics are one run's observations.

    The spec's own criteria forbid writing them into shipped guidance without re-asking the
    server, and INV-194 adds that one tool's silence is not proof of absence either. This
    implementation ships the mechanism and cites no such fact — asserted, because the
    tempting thing to do was to quote the vivid example.
    """

    def test_no_new_senzing_fact_was_added_to_the_shipped_rule(self):
        rules = section(
            read(GROUND_RULES),
            "## Reversed decisions",
            "\n## Verbosity",
        )
        for fact in ("EFX_YREST", "TRUSTED_ID", "SCORE_BEHAVIOR", "REGISTRATION_DATE"):
            with self.subTest(fact=fact):
                self.assertNotIn(
                    fact,
                    rules,
                    "a one-run observation must not be promoted into shipped guidance "
                    "without re-asking the server (INV-080)",
                )

    def test_the_append_path_cites_no_senzing_specifics_either(self):
        entry = section(read(FEEDBACK), "## Silent in-run append", "\n## ")
        for fact in ("EFX_YREST", "SCORE_BEHAVIOR", "REGISTRATION_DATE"):
            with self.subTest(fact=fact):
                self.assertNotIn(fact, entry)

    def test_the_scan_is_not_vacuous(self):
        for path in (GROUND_RULES, FEEDBACK, GRADUATION, PHASE_D, QUALITY):
            with self.subTest(file=os.path.basename(path)):
                self.assertTrue(os.path.isfile(path))
                self.assertGreater(len(read(path)), 2000)


if __name__ == "__main__":
    unittest.main()
