"""Two Phase 1 defects: an aggregate score that penalizes organizations, and a
readiness check that reaches for a method whose prerequisite is undocumented.

**Per-record-type completeness.** Phase 1 step 6 defined "present" rigorously — `false`
and `0` count as present; presence is a property of the value, not the key — and then
averaged each feature's coverage across the whole source. A feature that does not apply
to a record is not missing data, so a sanctions list with NAME and ADDRESS on 100% of
records scored 52% completeness / 69% overall, landing in "recommend fixing before
mapping", because DOB (32%) and other person-oriented features were averaged across a
source where 71 of 110 records are ORGANIZATIONS. Per-record-type rescoring gave 97%.
It fails toward false alarm, on exactly the mixed person/organization sources the
plugin's headline use cases describe.

The Senzing Entity Specification marks type in its own wording — verified on MCP server
1.32.1, 2026-07-28: `DOB` is "Person date of birth", `NATIONALITY`/`CITIZENSHIP`/
`PLACE_OF_BIRTH` are "Person …", and `REGISTRATION_DATE`/`REGISTRATION_COUNTRY` sit under
section headings titled "(organizations)". So applicability is derivable from the
specification rather than needing a table hardcoded in the plugin, which is what the
guidance now teaches. `RECORD_TYPE` is "Recommended", not required, so records with no
type needed handling the original report did not mention.

**getRecordPreview's prerequisite.** Preview returns Senzing's interpretation of a record
without loading it, which is the authoritative readiness test — but it requires the
record's DATA_SOURCE to be registered, and the readiness check naturally runs before
registration. Verified 2026-07-28: `get_sdk_reference(topic='parameters',
filter='getRecordPreview')` returns both overloads for every binding with no mention of
the prerequisite. Unlike this session's SENZ7221 case, `explain_error_code('SENZ2207')`
*does* return the fix, so the plugin's job is signposting rather than diagnosis.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE1 = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
    / "module-05-data-quality-mapping" / "phase1-quality-assessment.md"
)


def flat():
    text = PHASE1.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


def raw():
    return PHASE1.read_text(encoding="utf-8")


class CompletenessIsPerRecordType(unittest.TestCase):
    def test_the_rule_is_stated(self):
        self.assertRegex(
            flat(),
            r"(?i)PER RECORD against the features that apply to that record's `RECORD_TYPE`",
        )

    def test_it_forbids_the_per_feature_average(self):
        self.assertRegex(flat(), r"(?i)never as one average per feature across the whole source")

    def test_it_says_why_an_inapplicable_feature_is_not_missing_data(self):
        self.assertRegex(flat(), r"(?i)does not apply to a record is not missing data")

    def test_the_rule_precedes_the_thresholds_it_feeds(self):
        """The score routes the gate, so the correction must come before the bands."""
        text = raw()
        self.assertLess(
            text.index("PER RECORD against the features"),
            text.index("Use these thresholds to guide the decision"),
        )

    def test_the_worked_case_is_present_with_both_figures(self):
        text = flat()
        self.assertRegex(text, r"52% completeness")
        self.assertRegex(text, r"\*\*97%\*\*")
        self.assertRegex(text, r"(?i)71 of 110")


class ApplicabilityComesFromTheSpecification(unittest.TestCase):
    """INV-080: derive it from MCP, do not ship a static table as authority."""

    def test_it_routes_the_question_to_search_docs(self):
        self.assertRegex(flat(), r"search_docs\(query='what features to map'")

    def test_it_teaches_how_the_specification_marks_type(self):
        text = flat()
        self.assertRegex(text, r'(?i)"\*\*Person\*\* date of birth"')
        self.assertRegex(text, r'(?i)section heading "\*\*\(organizations\)\*\*"')

    def test_the_illustrative_table_disclaims_itself(self):
        text = flat()
        self.assertRegex(text, r"(?i)Re-read it for the source you are assessing")
        self.assertRegex(text, r"(?i)deliberately partial")

    def test_the_provenance_is_recorded(self):
        # A dated search_docs stamp: server version, docs-index timestamp and the
        # verification date, in the repo's existing form (#200).
        self.assertRegex(
            flat(),
            r"(?i)Verified against MCP server \d+\.\d+\.\d+, docs indexed "
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC, \d{4}-\d{2}-\d{2}",
        )

    def test_type_neutral_features_are_not_excluded(self):
        """Over-correcting would drop ADDRESS/PHONE/EMAIL from every denominator."""
        self.assertRegex(flat(), r"(?i)either — do not exclude these")


class RecordsWithNoTypeAreHandled(unittest.TestCase):
    """RECORD_TYPE is "Recommended", not required — the report did not cover this."""

    def test_untyped_records_are_scored_against_type_independent_features(self):
        self.assertRegex(flat(), r"(?i)Score those against the features that apply to \*\*any\*\* type")

    def test_their_count_is_reported(self):
        self.assertRegex(flat(), r"(?i)report how many records were scored that way")

    def test_a_mostly_untyped_source_is_itself_a_finding(self):
        self.assertRegex(flat(), r"(?i)is itself a finding worth raising")


class TheSanityCheckCoversApplicability(unittest.TestCase):
    def test_a_low_score_with_high_name_coverage_is_flagged(self):
        self.assertRegex(
            flat(),
            r"(?i)low completeness score on a source whose NAME and ADDRESS coverage is high",
        )

    def test_the_presence_rules_are_explicitly_left_intact(self):
        """This adds a second question; it must not weaken the first."""
        text = flat()
        self.assertRegex(text, r"(?i)presence rules above are unchanged")
        self.assertRegex(text, r"(?i)`false`, `0` and `0\.0` count as PRESENT")


class PreviewPrerequisiteIsDocumented(unittest.TestCase):
    def test_the_method_is_named_in_the_readiness_step(self):
        text = raw()
        step = text[text.index("## 5a."):text.index("## 6.")]
        self.assertIn("getRecordPreview", step)

    def test_the_registered_source_prerequisite_is_stated(self):
        self.assertRegex(
            flat(),
            r"(?i)requires the record's `DATA_SOURCE` code to be registered first",
        )

    def test_it_says_preview_writes_nothing(self):
        """The counter-intuitive part is why the guidance is needed at all."""
        self.assertRegex(flat(), r"(?i)even though it\s+writes nothing|writes nothing")

    def test_the_working_order_is_given(self):
        self.assertRegex(flat(), r"(?i)register the source code\(s\).{0,120}then preview")

    def test_senz2207_is_named_and_routed_to_explain_error_code(self):
        text = flat()
        self.assertIn("SENZ2207", text)
        self.assertRegex(text, r"explain_error_code\('SENZ2207'\)")

    def test_it_does_not_restate_the_error_codes_resolution_steps(self):
        """They are good; duplicating them invites drift."""
        self.assertRegex(flat(), r"(?i)do not\s+restate them here")

    def test_the_signature_is_obtained_per_binding_rather_than_restated(self):
        text = flat()
        self.assertRegex(text, r"get_sdk_reference\(topic='parameters', filter='getRecordPreview'\)")
        self.assertRegex(text, r"(?i)differ per binding")

    def test_no_hardcoded_signature_ships_in_the_step(self):
        """Naming the method is fine; pinning an argument list is not (INV-132)."""
        text = raw()
        step = text[text.index("## 5a."):text.index("## 6.")]
        self.assertNotIn("getRecordPreview(recordDefinition", step)

    def test_the_registration_code_comes_from_mcp(self):
        self.assertRegex(flat(), r"sdk_guide\(topic='configure'\)")

    def test_the_check_is_optional_and_non_blocking(self):
        text = flat()
        self.assertRegex(text, r"(?i)Optional and non-blocking")
        self.assertIn("INV-048", text)

    def test_it_says_which_check_ran(self):
        """"Senzing-ready" must not imply a stronger test than was performed."""
        self.assertRegex(flat(), r"(?i)never implies a stronger test than was\s+performed")

    def test_the_prerequisite_is_scoped_beyond_cord(self):
        """Step 5a is CORD-only; the reported failure was on a non-CORD source."""
        self.assertRegex(
            flat(), r"(?i)wherever a preview-based check is used, not only to the CORD"
        )


if __name__ == "__main__":
    unittest.main()
