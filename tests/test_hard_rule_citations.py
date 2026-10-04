"""The two hard rules registered on 2026-08-13 keep naming the invariants that govern them.

`triage-the-twelve-uncited-hard-rules` closed a backlog of hard rules — the repo's `⛔` /
bolded MUST/NEVER convention — whose enclosing section cited no invariant. Twelve were
missing citations to rules that already existed; two were genuinely unregistered and became
**INV-220** (branch from recorded provenance, never from a second mechanism or a question)
and **INV-221** (a surface that offers an action opening content must not also render it
inline).

Why a guard: `.claude/skills/dry-run/coverage_reports.py invariants` scored both as uncited
the moment they were appended, which is the exact condition that let INV-060 and INV-097
stand unimplemented for over a month — invisible because no test named them. A new invariant
with no citing test is born into that blind spot.

⚠️ **Asserts the structural property, not the prose (INV-219).** Each rule's wording is free
to change; what must not regress is that the paragraph stating it names its governing ID, and
that each invariant's own text still says the thing the citation promises. Scoped to the
paragraph rather than the line because both citations sit on a continuation line of a wrapped
paragraph — a per-line check would pass while the citation drifted into a neighboring rule.

No phrase-level pattern (#438): its line reads are of entry lines in `specs/INVARIANTS.md`, which is
outside the in-scope corpora, as #424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"

PROVENANCE_RULE = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
ENTITY_ACTIONS = (SKILLS / "module-03b-truthset-visualization"
                  / "visualization-api-reference.md")


def paragraph_containing(path, needle):
    """The blank-line-delimited block that states a rule, or None when the rule is gone."""
    blocks = path.read_text(encoding="utf-8").split("\n\n")
    for block in blocks:
        if needle in block:
            return block
    return None


def invariant_entry(inv_id):
    for line in INVARIANTS.read_text(encoding="utf-8").split("\n"):
        if line.startswith("- **%s**" % inv_id):
            return line
    return None


class TheScenarioProvenanceRuleCitesInv220(unittest.TestCase):
    def setUp(self):
        self.block = paragraph_containing(PROVENANCE_RULE,
                                          "Branch on scenario provenance first")
        self.assertIsNotNone(
            self.block,
            "the scenario-provenance ⛔ is gone from Module 1 Phase 2 step 9; INV-220 was "
            "registered from it and nothing else states the rule",
        )

    def test_the_rule_names_its_governing_invariant(self):
        self.assertIn(
            "INV-220", self.block,
            "the provenance branch rule must name INV-220 in the same paragraph: without it "
            "a later editor cannot look the rule up, and conformance.py rules reports the "
            "line as an unregistered hard rule again",
        )

    def test_the_rule_still_forbids_a_second_mechanism(self):
        """The half INV-220 adds beyond 'do not ask' — drop it and the citation overclaims."""
        self.assertIn("second mechanism", self.block)


class TheNoRedundantListingRuleCitesInv221(unittest.TestCase):
    def setUp(self):
        self.block = paragraph_containing(ENTITY_ACTIONS,
                                          "No redundant inline record listings")
        self.assertIsNotNone(
            self.block,
            "the no-redundant-inline-listings rule is gone from the visualization contract; "
            "INV-221 was registered from it",
        )

    def test_the_rule_names_its_governing_invariant(self):
        self.assertIn(
            "INV-221", self.block,
            "the rule must name INV-221 in the same paragraph. This contract is the only "
            "file a non-Python language build is generated from (INV-090/INV-124), so an "
            "uncited MUST here is unreachable for every other implementation",
        )

    def test_the_rule_still_states_the_action_that_makes_inlining_redundant(self):
        self.assertIn("Records action", self.block)


class BothInvariantsSayWhatTheirCitationsPromise(unittest.TestCase):
    """A citation is only as good as the entry it points at (the INV-129/INV-218 defect)."""

    def test_inv220_binds_the_branch_to_recorded_provenance(self):
        entry = invariant_entry("INV-220")
        self.assertIsNotNone(entry, "INV-220 is missing from INVARIANTS.md")
        self.assertRegex(entry, r"(?i)provenance already recorded")
        self.assertRegex(entry, r"(?i)second mechanism")
        self.assertRegex(entry, r"(?i)question to the Bootcamper")

    def test_inv221_covers_any_surface_not_only_entity_lists(self):
        entry = invariant_entry("INV-221")
        self.assertIsNotNone(entry, "INV-221 is missing from INVARIANTS.md")
        self.assertRegex(entry, r"(?i)bootcamper-facing surface")
        self.assertRegex(entry, r"(?i)MUST NOT also render the same content inline")


if __name__ == "__main__":
    unittest.main()
