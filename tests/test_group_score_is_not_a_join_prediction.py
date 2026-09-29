"""A grouped completeness score must not be read as a cross-source join prediction.

Enforces **INV-261** — a named cross-source pair is labeled `measured` (backed by a count of
distinct values shared on the named attribute) or `candidate, overlap unmeasured`; a grouped
score is not evidence for a per-attribute claim. Registered 2026-08-17, scoped deliberately
to cross-source join predictions rather than to predictions generally (maintainer decision).

Two sources both scored **IDENTIFIER 100%** — the group counts as present when *any* of
its members is populated — and the evaluation report named them the highest-confidence
cross-source pair, "both carrying LEI". One carried 2,375 LEI values; the other carried
**one**, across 137 records. Exactly one LEI value was shared in the entire dataset. The
prediction was wrong by ~38x on the attribute it named, and nothing disproved it until
after loading, when the match keys showed LEI in a single match key.

⛔ **The metric was right; the reading was wrong, and that is a different class of failure.**
The module already forbids three adjacent *measurement* errors — presence is a property of
the value not the key, sanity-check any 0%/100% figure, measure per record against the
record's own `RECORD_TYPE`. Every one of those guards the number's accuracy. None guarded
its interpretation, and the 0%/100% sanity-check actively fails here: it fires on a uniform
figure as a probable *measurement* failure, and this 100% was entirely real — so a guide
following it confirms the number and proceeds with the wrong inference intact.

⚠️ **The group metric itself is deliberately unchanged.** It is correct for completeness and
the quality gate depends on it; per-record-type scoping already constrains it properly. This
adds a second measurement for a second question rather than redefining the first — so these
tests assert the existing rules are all still present, not merely that the new one is.

Everything here is asserted as **behavior in shipped guidance**, never as a Python helper,
so any implementation language satisfies it (INV-002).

Source spec: `specs/a-shared-feature-group-is-read-as-a-shared-attribute-when-predicting-joins.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

# ⚠️ **Matches the ROUTE, not the exact argument string.** These assertions pinned the literal
# `search_docs(category='data_mapping')`, which stopped matching when
# `specs/search-docs-instructions-omit-the-required-query-parameter.md` gave every shipped
# reference the `query` the tool actually requires -- so the guards failed on the correction they
# should have welcomed, the pattern `specs/guards-pinning-a-dated-negative-outlive-it.md`
# describes. What they exist to assert is that the claim names its route; the route is still named.
ROUTE_DATA_MAPPING = re.compile(
    r"search_docs\([^)]*?category='data_mapping'\)")

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE1 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
          "module-05-data-quality-mapping" / "phase1-quality-assessment.md")


def flat():
    return " ".join(PHASE1.read_text(encoding="utf-8").split())


class TheGroupScoreIsScopedWhereItIsDefined(unittest.TestCase):

    def test_it_says_a_group_score_is_not_evidence_of_a_shared_attribute(self):
        self.assertIn(
            "A GROUP score is not evidence that two sources share an ATTRIBUTE", flat())

    def test_it_names_the_reason_a_join_needs_presence_of_same(self):
        text = flat()
        self.assertIn("presence-of-**same**", text)
        self.assertIn("not presence-of-any", text)

    def test_it_says_the_uniform_figure_sanity_check_does_not_catch_this(self):
        """⛔ The closest existing guard, and following it confirms the wrong inference."""
        self.assertIn("sanity-check above does not catch this", flat())

    def test_the_worked_example_carries_its_measured_numbers(self):
        text = flat()
        for figure in ("2,375", "137 records", "~38x"):
            with self.subTest(figure=figure):
                self.assertIn(figure, text)

    def test_the_grouped_family_is_sourced_from_the_entity_specification(self):
        """INV-080 — the attribute names are the server's, with provenance recorded."""
        text = flat()
        self.assertRegex(text, ROUTE_DATA_MAPPING)
        self.assertIn("server 1.32.9, 2026-08-17", text)


class APredictionCarriesItsEvidenceOrItsAbsence(unittest.TestCase):

    def test_a_named_pair_requires_a_distinct_value_overlap_count(self):
        text = flat()
        self.assertIn("distinct values shared on the named", text)

    def test_an_unmeasured_prediction_has_prescribed_wording(self):
        """The rule's own wording is INV-261's label, the one the template below uses (#234).

        It read "candidate on group coverage, overlap unmeasured", a third label beside the
        invariant's two. Asserted at the rule site, since the template alone would satisfy a
        bare search for the label; negative-controlled by restoring the old wording.
        """
        text = flat()
        self.assertIn(
            "If that count was not run, write the pair as a *candidate, overlap unmeasured*",
            text)
        self.assertNotIn("candidate on group coverage", text,
                         "INV-261 has two labels, `measured` and `candidate, overlap "
                         "unmeasured`; a third one reads as a different status")

    def test_the_evaluation_report_template_carries_both_labels(self):
        text = flat()
        self.assertIn("Cross-Source Outlook", text)
        self.assertIn("candidate, overlap unmeasured", text)
        self.assertIn("Distinct values shared:", text)

    def test_the_report_is_named_as_a_kept_deliverable(self):
        """Why an unmarked prediction does lasting damage."""
        text = flat()
        self.assertIn("docs/data_source_evaluation.pdf", text)
        self.assertIn("deliverable the Bootcamper keeps", text)

    def test_ranking_by_group_coverage_alone_is_forbidden(self):
        self.assertIn("Never rank pairs by confidence on group coverage alone", flat())


class TheExistingMeasurementRulesAreUnchanged(unittest.TestCase):
    """⚠️ The group metric, its scoping and the gate's routing must be untouched."""

    def test_presence_is_still_a_property_of_the_value(self):
        self.assertIn("Presence is a property of the VALUE, never of the key", flat())

    def test_the_uniform_figure_sanity_check_is_still_required(self):
        self.assertIn("Sanity-check any 0% or 100% figure before it routes the gate",
                      flat())

    def test_per_record_type_scoping_is_still_required(self):
        text = flat()
        self.assertIn("Measure completeness PER RECORD against the features that apply",
                      text)
        self.assertIn("71 of 110", text, "the worked rescoring example was lost")

    def test_falsey_values_still_count_as_present(self):
        self.assertIn("`false`, `0` and `0.0` count as PRESENT", flat())


class TheGuidanceIsBehaviorNotAHelper(unittest.TestCase):
    """INV-002 — any implementation language must be able to satisfy it."""

    def test_the_new_rules_name_no_python_helper(self):
        text = PHASE1.read_text(encoding="utf-8")
        start = text.index("A GROUP score is not evidence")
        end = text.index("what did the damage.", start)
        block = text[start:end]
        for token in ("def ", "import ", ".py`"):
            with self.subTest(token=token):
                self.assertNotIn(token, block,
                                 "the rule is stated as code rather than as behavior")


if __name__ == "__main__":
    unittest.main()
