"""An explained count delta is a reconciled load, not a failed one.

Phase B's rule said: if the loaded count and the source's input count disagree, set
`load_status: failed`. A source loaded **3,727** records against a measured `record_count`
of **3,488** — 239 distinct lenders emitted as embedded masters, exactly as that source's
mapping specification prescribes, every input record loaded, zero errors. The only compliant
action was to file a completely successful load as `failed`, and to write that into the
Bootcamper's own loading strategy.

⛔ **The rule tested for equality, and the mapping the bootcamp TEACHES breaks equality by
design.** `embedded_master` is not an unanticipated edge case: Module 5 teaches it under its
own heading, defined as *"the value becomes its own Senzing record, and the parent points at
it"*. A disposition whose definition is "emit an additional record" necessarily makes the
loaded count exceed the input count. So the branch is reachable by design, not by accident.

⚠️ **INV-245 never required this**, which is why the fix sits inside it rather than against
it. Its condition is that a value which **failed its own verification check** must not be
presented as a result. A delta the mapping specification *predicts* has not failed
verification — it is verified and reconciled. The step collapsed three states (equal /
explained delta / unexplained delta) into two, and INV-245 governs only the third. No
invariant needed amending.

⛔ **The explained branch must be unreachable without a citation.** "The mapping probably
explains it" is exactly the failure INV-245 exists to prevent, and an uncited escape hatch
would let it through wearing the new rule as a disguise — so the negative control here is
that the uncited case never reaches `expected_delta`.

⚠️ **#157 split the rule into two stages, and the three outcomes became four.** The rule
compared the loaded count against the collected `record_count` only, so every source loaded from
a Module 4 working sample — GLEIF: 7,386 of a 7,386-record load file against 63,863 collected —
read as a delta no branch named, and a strict reading filed a clean load as `failed`. Stage 1
now compares the loaded count against the **load input** and alone can record `failed`; stage 2
relates the load input to `record_count` through a cited chain (the `sample:` block, a subset
limit, mapping dispositions) and routes to `pass` / `expected_delta` / `unexplained_delta`. So
the uncited case falls through to `unexplained_delta` — loaded, shown as unverified — rather
than to `failed`. The file keeps its name: stage 2 is the three-way rule, and the new guard for
the two-stage shape is `test_load_reconciliation_has_two_stages.py`.

Everything is asserted as **behavior in shipped guidance**, never as a Python helper, so any
implementation language satisfies it (INV-002).

Source spec: `specs/count-mismatch-rule-files-a-mapping-explained-delta-as-a-failed-load.md`.

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE6 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
           "module-06-data-processing")
PHASE_B = MODULE6 / "phaseB-load-first-source.md"
PHASE_C = MODULE6 / "phaseC-multi-source.md"
PHASE_D = MODULE6 / "phaseD-validation.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


class PhaseBRoutesThreeWays(unittest.TestCase):

    def setUp(self):
        self.text = flat(PHASE_B)

    def test_it_says_there_are_four_outcomes_across_two_stages(self):
        """#157: the count changed from three to four, deliberately."""
        self.assertIn("Four outcomes across two stages, not two", self.text)
        self.assertNotIn("A disagreement has THREE outcomes, not two", self.text)

    def test_the_explained_delta_records_loaded(self):
        self.assertIn("**Explained delta**", self.text)
        self.assertIn("load_count_matches_source: expected_delta", self.text)

    def test_the_unexplained_delta_records_loaded_and_unverified(self):
        """#157: an uncited stage-2 gap is loaded, with every figure in an `issues` entry."""
        self.assertIn("**Unexplained delta**", self.text)
        self.assertIn("load_count_matches_source: unexplained_delta", self.text)
        self.assertIn("an `issues` entry with every figure", self.text)

    def test_a_stage_one_mismatch_still_records_failed(self):
        """The original `failed` branch, intact — moved to the stage that can verify a load."""
        self.assertIn("**Loaded ≠ load input** | `failed`", self.text)
        self.assertIn("both figures in the `issues` entry", self.text)

    def test_the_equal_case_is_unchanged(self):
        self.assertIn("load_count_matches_source: pass", self.text)

    def test_it_records_a_reconciliation_note_naming_the_predicting_record(self):
        """#157: the note names every chain step, not only a mapping disposition."""
        self.assertIn("`load_reconciliation` note naming **each chain step and the record "
                      "it cites**", self.text)


class TheExplainedBranchNeedsACitation(unittest.TestCase):
    """⛔ Without this it is a universal escape hatch and the rule protects nothing."""

    def setUp(self):
        self.text = flat(PHASE_B)

    def test_a_citation_is_required_not_an_assertion(self):
        self.assertIn("reachable ONLY with a citation, never with an assertion", self.text)

    def test_it_names_which_artifacts_count(self):
        self.assertIn("the source's own mapping specification", self.text)
        self.assertIn("recorded disposition in `config/data_sources.yaml`", self.text)

    def test_the_uncited_case_falls_through_to_unexplained_delta(self):
        """#157: at stage 2 an uncited gap is unverified, not failed."""
        self.assertIn("No citation → `unexplained_delta`", self.text)
        self.assertNotIn("No citation → **unexplained** → `failed`", self.text)

    def test_the_disguise_is_named(self):
        self.assertIn("wearing the rule as a disguise", self.text)


class TheBaselineStaysImmutable(unittest.TestCase):
    """INV-243 — the half of the rule that was correct and did not change."""

    def setUp(self):
        self.text = flat(PHASE_B)

    def test_every_branch_keeps_the_input_baseline(self):
        self.assertIn("The baseline stays immutable in every branch", self.text)
        self.assertIn("`record_count` and `expected_record_count` are never overwritten",
                      self.text)
        self.assertIn("never overwritten and the loaded figure is recorded beside it",
                      self.text)

    def test_the_registry_write_no_longer_overwrites_the_count_up_front(self):
        """It used to say "update record_count to the actual loaded count"."""
        self.assertNotIn("update `load_status` to `loaded` and `record_count` to the "
                         "actual loaded count", self.text)
        self.assertIn("Do not write the loaded count over `record_count`", self.text)

    def test_overwriting_is_still_called_the_worst_outcome(self):
        self.assertIn("Overwriting on a mismatch is the worst outcome available",
                      self.text)


class TheReportedCaseIsRecorded(unittest.TestCase):
    """The embedded_master case that produced this report, end to end in the guidance."""

    def setUp(self):
        self.text = flat(PHASE_B)

    def test_the_figures_are_named(self):
        self.assertIn("**3,727**", self.text)
        self.assertIn("**3,488**", self.text)
        self.assertIn("239 distinct lenders", self.text)

    def test_the_teaching_disposition_is_named_as_the_cause(self):
        self.assertIn("`embedded_master`", self.text)
        self.assertIn("necessarily** makes the loaded count exceed the input count",
                      self.text)

    def test_it_says_the_bootcamp_teaches_the_mapping_that_reaches_this(self):
        self.assertIn("the bootcamp teaches the mapping that reaches it", self.text)


class TheThirdStateIsCarriedDownstream(unittest.TestCase):
    """⛔ Both consumers read `load_status` straight back out and present it."""

    def test_phase_c_step_12_distinguishes_it(self):
        text = flat(PHASE_C)
        self.assertIn("is a RECONCILED result, not a failure and not a plain pass", text)
        self.assertIn("never render it as `failed`", text)

    def test_phase_c_shows_the_figures_and_the_chain(self):
        """#157: the display names the chain, collected figure included."""
        text = flat(PHASE_C)
        self.assertIn("3,727 loaded from 3,488 collected records", text)
        self.assertIn("7,386 loaded from a 7,386-record overlap-preserving sample of 63,863 "
                      "collected", text)

    def test_phase_d_writes_it_as_reconciled(self):
        text = flat(PHASE_D)
        self.assertIn("four reconciliation outcomes to write here, not two", text)
        self.assertIn("never as a failure, and never as a bare matching count", text)

    def test_phase_d_says_why_both_wrong_renderings_are_wrong(self):
        text = flat(PHASE_D)
        self.assertIn("tells them a clean load broke", text)
        self.assertIn("hides that anything happened", text)


class TheGuidanceIsBehaviorNotAHelper(unittest.TestCase):
    """INV-002 — a comparison between two recorded figures, in any language."""

    def test_the_reconciliation_rule_names_no_language_specific_helper(self):
        body = PHASE_B.read_text(encoding="utf-8")
        start = body.index("Reconcile the loaded count in two stages")
        end = body.index("The baseline stays immutable", start)
        block = body[start:end]
        for token in ("def ", "import ", "python3 ", ".py`"):
            with self.subTest(token=token):
                self.assertNotIn(token, block,
                                 "the rule is stated as code rather than as behavior")


if __name__ == "__main__":
    unittest.main()
