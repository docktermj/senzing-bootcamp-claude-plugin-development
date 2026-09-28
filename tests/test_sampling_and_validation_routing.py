"""Two ways a technically perfect load produced nothing useful.

**Random sampling destroyed the cross-source overlap.** Module 4 offered sampling at the
license gate with no strategy guidance, and the natural instinct — a random sample is
representative — is right for profiling and wrong for entity resolution, which needs the
same real-world entities to appear in more than one source. A random 300 records from each
of five sources loaded flawlessly (1,147 records, zero errors, redo drained, quality
94-100%) and produced ZERO cross-source matches outside one fully-included pair. The
overlap was real: 507 shared names across 21,284 x 63,193 candidates for the largest pair.

The correct guidance already existed at Step 8b, in the branch that fires only on
SQLite load-time concerns — never on the license-driven path a bootcamper meets first.
The module also said "Ensure the sample is representative of the full dataset", which is
the harmful instinct stated as instruction.

**Module 6 routed counts to reporting_guide without naming a topic**, while being specific
everywhere else, so topic='reports' is the name a reader picks for "counts and statistics"
— and its SQL targets a data mart the bootcamp never builds. Note the server itself
discloses that (verified 1.32.1, 2026-07-28), so the defect is the plugin's routing, not
the tool's candor; the guidance quotes the tool rather than asserting on its own
authority.

These tests pin the single-source-of-truth structure, since this defect *was* two copies
of one rule disagreeing.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"
MODULE_06 = SKILLS / "module-06-data-processing" / "SKILL.md"
PHASE_D = SKILLS / "module-06-data-processing" / "phaseD-validation.md"


def flat(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


class TheSamplingRuleExistsOnce(unittest.TestCase):
    """The defect was two places disagreeing, so the rule gets one home."""

    def test_the_canonical_rule_has_an_anchor(self):
        self.assertIn('<a id="overlap-preserving-sampling"></a>', MODULE_04.read_text(encoding="utf-8"))

    def test_it_declares_itself_canonical(self):
        self.assertRegex(flat(MODULE_04), r"(?i)This is the canonical statement")

    def test_the_other_two_paths_reference_it_rather_than_restate(self):
        text = MODULE_04.read_text(encoding="utf-8")
        refs = text.count("(#overlap-preserving-sampling)")
        self.assertGreaterEqual(refs, 2, "the smaller-slice path and Step 8b must both link it")

    def test_step_8b_defers_instead_of_restating(self):
        self.assertRegex(flat(MODULE_04), r"(?i)canonical statement; do not restate it here")


class TheHazardIsStated(unittest.TestCase):
    def test_random_selection_is_named_as_destructive_for_multi_source(self):
        self.assertRegex(
            flat(MODULE_04),
            r"(?i)when 2\+ sources are present, random selection destroys the signal",
        )

    def test_the_profiling_versus_er_distinction_is_explained(self):
        text = flat(MODULE_04)
        self.assertRegex(text, r"(?i)right instinct for \*\*profiling\*\*")
        self.assertRegex(text, r"(?i)wrong one for \*\*entity resolution\*\*")

    def test_the_green_signals_warning_is_present(self):
        """Why it is dangerous: nothing a bootcamper checks catches it."""
        self.assertRegex(flat(MODULE_04), r"(?i)[Ee]very operational signal a bootcamper checks stays green")

    def test_the_measured_case_is_cited(self):
        text = flat(MODULE_04)
        self.assertIn("1,147 records", text)
        self.assertRegex(text, r"zero\*\* cross-source matches|zero cross-source matches")
        self.assertIn("507 shared names", text)


class TheGuidanceIsActionable(unittest.TestCase):
    """"Preserve overlaps" alone is not something a reader can execute."""

    def test_it_gives_a_numbered_selection_method(self):
        text = flat(MODULE_04)
        self.assertRegex(text, r"(?i)Identify candidate join keys")
        self.assertRegex(text, r"(?i)participate in values appearing in 2\+ sources")

    def test_it_says_to_keep_matched_groups_whole(self):
        self.assertRegex(
            flat(MODULE_04), r"(?i)taking one side of a pair is as useless as taking neither"
        )

    def test_it_still_fills_the_remaining_budget(self):
        """An overlap-only sample would exercise no singletons or non-matches."""
        self.assertRegex(flat(MODULE_04), r"(?i)[Ff]ill the remaining budget")

    def test_the_single_source_case_is_exempted(self):
        self.assertRegex(flat(MODULE_04), r"(?i)single-source\*\* dataset none of this applies")


class RepresentativenessIsNoLongerTheInstruction(unittest.TestCase):
    """The module used to instruct exactly the harmful default."""

    def test_the_bare_representative_instruction_is_gone(self):
        self.assertNotRegex(
            flat(MODULE_04),
            r"Ensure the sample is representative of the full dataset\.",
            "that sentence is the harmful instinct stated as instruction",
        )

    def test_representativeness_is_distinguished_from_what_er_needs(self):
        self.assertRegex(
            flat(MODULE_04),
            r"(?i)representative of every source individually can contain no cross-source matches",
        )

    def test_the_method_and_its_reason_are_both_recorded(self):
        self.assertRegex(flat(MODULE_04), r"(?i)sampling method AND why it was chosen")


class Module6ReadsTheSamplingMethodFirst(unittest.TestCase):
    def test_the_check_is_in_the_cross_source_step_not_single_source(self):
        """A single-source load has no cross-source count to misread."""
        text = PHASE_D.read_text(encoding="utf-8")
        pos = text.index("Before treating a low or zero cross-source entity count")
        self.assertGreater(pos, text.index("## 23. Validate cross-source results"))
        self.assertLess(pos, text.index("## 24."))

    def test_it_names_where_the_method_is_recorded(self):
        self.assertIn("config/data_sources.yaml", flat(PHASE_D))

    def test_it_names_the_remedy_as_resampling_not_remapping(self):
        self.assertRegex(
            flat(PHASE_D), r"(?i)overlap-preserving re-sample.{0,40}not a mapping change"
        )

    def test_it_forbids_reporting_absence_without_the_check(self):
        self.assertRegex(
            flat(PHASE_D),
            r"(?i)never report \"Senzing found no cross-source matches\" without checking",
        )


class ValidationRoutingNamesItsTopic(unittest.TestCase):
    def test_no_bare_reporting_guide_count_routing_remains(self):
        for path in (MODULE_06, PHASE_D):
            with self.subTest(file=path.name):
                text = flat(path)
                self.assertNotRegex(
                    text,
                    r"[Cc]ounts,? and stats come from `reporting_guide`\.",
                    "route counts to a named topic, not to the tool alone",
                )

    def test_evaluation_is_named_for_this_phase(self):
        self.assertRegex(
            flat(PHASE_D),
            r"reporting_guide\(topic='evaluation', language='<chosen_language>'\)\` "
            r"for the single-pass export statistics",
        )

    def test_the_count_bullet_names_the_topic(self):
        self.assertRegex(
            flat(PHASE_D),
            r"reporting_guide\(topic='evaluation', language='<chosen_language>'\)\` for counts",
            "the topic must be named AND carry `language` — `evaluation` gates on it and "
            "returns a needs_input tree with no content when it is omitted (1.32.2)",
        )

    def test_reports_is_characterized_rather_than_merely_avoided(self):
        text = flat(PHASE_D)
        self.assertRegex(text, r"(?i)`topic='reports'` is not this bootcamp's route")
        self.assertRegex(text, r"sz_dm_entity")

    def test_the_disclosure_is_quoted_from_the_tool_with_provenance(self):
        """INV-080: the tool's own words, dated — not the plugin's assertion."""
        text = flat(PHASE_D)
        self.assertRegex(text, r"(?i)NOT part of the Senzing SDK and do \*\*NOT\*\* exist out of the box|NOT part of the Senzing SDK")
        # A dated server stamp: a version plus a YYYY-MM-DD date (#200).
        self.assertRegex(text, r"(?i)verified on MCP server \d+\.\d+\.\d+, \d{4}-\d{2}-\d{2}")

    def test_the_usable_subset_is_named(self):
        """"Wrong topic" must not read as "nothing here helps"."""
        self.assertRegex(flat(PHASE_D), r"(?i)`Validation:` patterns, which run against \*\*exported entity JSON")

    def test_the_no_sql_rule_survives(self):
        for path in (MODULE_06, PHASE_D):
            with self.subTest(file=path.name):
                self.assertRegex(flat(path), r"(?i)never direct SQL against|[Nn]ever generate SQL against")


if __name__ == "__main__":
    unittest.main()
