"""Data collection describes SHAPE; only the mapping module says what a field maps to.

A guide recorded, in **both** `config/data_sources.yaml` and `docs/data_source_locations.md`,
that a CRM's `full_name` "needs splitting into NAME_FIRST / NAME_LAST" and that a loyalty
file's `"Last, First"` `member_name` needed "a different split". Reading the Entity
Specification at Module 5 reversed both: a single name field maps to `NAME_FULL`.

⚠️ **The reversal was cheap — no mapper existed yet — but the wrong plan had already been
committed to two documents a module earlier, where it read as settled fact.** Splitting the
names would have produced a mapping that loads and validates cleanly while degrading
resolution quality silently, which is the class Module 5 warns a quality score cannot detect.

⛔ **Two causes, and the second is the one the report missed.** Module 1 and Module 4 both
require a claim about *how the data maps* while the governing document has not been read
(sequencing) — and Module 4's own two examples of "mapping complexity", a joined name and a
free-text address, are **direct mappings** under that specification rather than
transformations. So a scenario generated to satisfy Module 4's notion of complexity could
satisfy none of Module 1's "at least one transformation" invariant through them, and the
module was teaching that a joined name is a transformation waiting to happen.

⚠️ **What is deliberately untouched:** the branch's other generation requirements — quality
bands, per-campaign duplicates, off-pattern values, record-key integrity (INV-180/INV-239) —
are real work and unaffected. Only the two leading examples and the inference drawn from them
were wrong, so these tests assert those requirements survive.

Verified on server **1.32.9, 2026-08-17** via `search_docs(category='data_mapping')`: the
specification's *Name > Feature: NAME* section documents `NAME_FULL` as the *"Single-field name
when type (person vs org) is unknown or only a full name is provided"* and rules *"Prefer
parsed person names … when available; use `NAME_ORG` for organizations; use `NAME_FULL` only
when the type is unknown or only a single field exists"*.

Source spec: `specs/data-collection-records-mapping-claims-before-the-entity-specification-is-read.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE1 = SKILLS / "module-01-business-problem" / "phase1-discovery.md"
MODULE4 = SKILLS / "module-04-data-collection" / "SKILL.md"
MODULE5 = SKILLS / "module-05-data-quality-mapping" / "phase2-data-mapping.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def generation_branch():
    """Module 4's synthesized-generation directives, sliced by their own content."""
    text = MODULE4.read_text(encoding="utf-8")
    start = text.index("Generate the SHAPE differences the scenario promised")
    end = text.index("Both are bootcamp-generated, so both skip the question", start)
    return text[start:end]


class TheBranchDescribesShapeNotMapping(unittest.TestCase):

    def setUp(self):
        self.branch = " ".join(generation_branch().split())

    def test_the_directive_asks_for_shape_differences(self):
        self.assertIn("Generate the SHAPE differences the scenario promised", self.branch)

    def test_it_forbids_stating_what_a_field_maps_to(self):
        self.assertIn("Describe SHAPE only — do not state, or invite, what any field maps "
                      "to", self.branch)

    def test_it_says_why_the_claim_cannot_be_made_here(self):
        self.assertIn("is not read until Data Quality, Mapping, and Transformation",
                      self.branch)

    def test_it_names_the_two_documents_the_claim_reached(self):
        self.assertIn("config/data_sources.yaml", self.branch)
        self.assertIn("docs/data_source_locations.md", self.branch)

    def test_it_gives_the_wording_to_use_instead(self):
        self.assertIn('Record "one name field" or "name in two parts"', self.branch)


class NoSplittingClaimSurvivesForASingleNameField(unittest.TestCase):
    """⛔ The reported claim, scanned for across every shipped file."""

    #: The claim shape, in the phrasings a generator or a guide would write.
    SPLIT_CLAIMS = (
        "needs splitting into NAME_FIRST",
        "needs splitting into `NAME_FIRST`",
        "split into NAME_FIRST / NAME_LAST",
        "names split into components in one source and joined in another",
    )

    #: Words marking a mention as a retraction rather than an instruction.
    RETRACTIONS = ("never", "not a transformation", "reversed", "do not", "wrong",
                   "would have produced")

    def test_no_shipped_file_asserts_the_split_claim(self):
        offenders = []
        for path in sorted((REPO_ROOT / "plugins").rglob("*.md")):
            text = " ".join(path.read_text(encoding="utf-8").split())
            for claim in self.SPLIT_CLAIMS:
                start = 0
                while True:
                    found = text.find(claim, start)
                    if found == -1:
                        break
                    start = found + 1
                    window = text[max(0, found - 260):found + 260]
                    if any(mark in window for mark in self.RETRACTIONS):
                        continue
                    offenders.append(f"{path.relative_to(REPO_ROOT)}: {claim!r}")
        self.assertEqual(
            [], offenders,
            "a shipped file plans to split a single-field name — the specification maps it "
            "to NAME_FULL:\n  " + "\n  ".join(offenders))

    def test_the_scan_is_not_vacuous(self):
        window = "The CRM's full_name needs splitting into NAME_FIRST / NAME_LAST."
        self.assertFalse(any(m in window for m in self.RETRACTIONS))


class TheNameFullRuleIsStatedWhereItChangesGeneration(unittest.TestCase):

    def setUp(self):
        self.branch = " ".join(generation_branch().split())

    def test_the_rule_is_stated_in_the_generation_branch(self):
        self.assertIn("a source carrying **one** name field maps to `NAME_FULL`", self.branch)

    def test_a_joined_name_is_named_as_not_a_transformation(self):
        self.assertIn("A joined name is therefore NOT a transformation waiting to happen",
                      self.branch)

    def test_the_rule_carries_its_route_version_and_date(self):
        """INV-080 — quoted from the specification, not adopted.

        #600: the route is stated once, at Module 5 step 11, and this branch points there; the
        version and date are the route's record, which test_prescribed_search_queries.py
        follows from the pointer (was a prose stamp, "server 1.32.9, 2026-08-17").
        """
        self.assertRegex(
            self.branch,
            r"the route to it is stated once, in `\.\./module-05-data-quality-mapping/"
            r"phase2-data-mapping\.md` → \"11\. Map\"")
        from test_prescribed_search_queries import VERIFIED_QUERIES
        record = VERIFIED_QUERIES[("search_docs", "NAME_FULL NAME_ORG parsed person name single "
                                   "field", "data_mapping")]
        self.assertRegex(record["server"], r"^\d+\.\d+\.\d+$")
        self.assertIn("Name > Feature: NAME", record["sections"])

    def test_the_quoted_rule_is_the_one_the_corpus_returns(self):
        """⚠️ The wording matters: this is what was verified, not a stronger paraphrase."""
        self.assertIn("use `NAME_FULL` only when the type is unknown or only a single field "
                      "exists", self.branch)

    def test_it_defers_the_full_rules_to_module_five(self):
        self.assertIn("The full mapping rules stay in that module", self.branch)


class ModuleOnesInvariantIsSatisfiable(unittest.TestCase):

    def setUp(self):
        self.text = flat(MODULE1)

    def test_it_asks_for_cross_source_mapping_divergence(self):
        self.assertIn("cross-source mapping divergence", self.text)

    def test_the_unqualified_transformation_wording_is_gone(self):
        self.assertNotIn("needs at least one transformation when mapped to the Senzing "
                         "Entity Specification", self.text)

    def test_it_forbids_the_unqualified_wording_in_terms(self):
        self.assertIn('Do not state this as "at least one transformation"', self.text)

    def test_it_names_kinds_that_actually_qualify(self):
        for kind in ("date normalization", "standardization", "composing a `RECORD_ID`"):
            with self.subTest(kind=kind):
                self.assertIn(kind, self.text)

    def test_it_also_forbids_recording_mappings_at_this_stage(self):
        self.assertIn("Do not record what any field maps to here either", self.text)


class ModuleFiveHoldsTheAuthority(unittest.TestCase):
    """The routes above point here, so the rule must actually be stated here."""

    def setUp(self):
        self.text = flat(MODULE5)

    def test_the_rule_is_stated_as_a_rule_not_only_shown_in_an_example(self):
        self.assertIn("A single name field maps to `NAME_FULL` — it is not split", self.text)

    def test_it_carries_the_specification_wording_and_provenance(self):
        self.assertIn("Single-field name when type (person vs org) is unknown or only a "
                      "full name is provided", self.text)
        # #600: the provenance is the route, named in full here, the one statement of it; its
        # version and date are the record in test_prescribed_search_queries.py.
        self.assertIn("search_docs(query='NAME_FULL NAME_ORG parsed person name single field', "
                      "category='data_mapping')", self.text)
        self.assertIn("This is the canonical statement of the *Feature: NAME* route", self.text)

    def test_it_explains_what_when_available_means(self):
        """The clause that decides the case — a single column is not "available" parts."""
        self.assertIn("the source provides separate fields", self.text)

    def test_the_adjacent_mixing_rules_are_stated(self):
        self.assertIn("Do not mix `NAME_FULL` with parsed name fields", self.text)
        self.assertIn("An organization name belongs in `NAME_ORG`", self.text)


class TheOtherGenerationRequirementsSurvive(unittest.TestCase):
    """⚠️ Only the two leading examples were wrong; the real work is unaffected."""

    def setUp(self):
        self.branch = " ".join(generation_branch().split())

    def test_quality_gaps_are_still_required(self):
        self.assertIn("INV-239", self.branch)
        self.assertIn("Generate realistic quality gaps", self.branch)

    def test_the_record_key_integrity_rule_survives(self):
        self.assertIn("Never put a gap in a record key", self.branch)
        self.assertIn("INV-180", self.branch)

    def test_the_quality_intent_record_survives(self):
        self.assertIn("quality_intent", self.branch)

    def test_the_license_sizing_directive_survives(self):
        """Added earlier the same day, in the same branch — it must not have been lost."""
        self.assertIn("LICENSE-CAPACITY decision", self.branch)


if __name__ == "__main__":
    unittest.main()
