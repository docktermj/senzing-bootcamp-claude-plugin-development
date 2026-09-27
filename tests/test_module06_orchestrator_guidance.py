"""The orchestrator must be told that per-source statistics are not free.

MCP-NEGATIVE-SCAN: ignore-file — this file quotes the `MCP-NEGATIVE:` token as a LOCATOR, to
find Step 17's real marker and assert its `owner:` clause (#156). Those string literals are
matchers, not dated claims, so the scanner would otherwise report them as malformed markers.

Phase C step 17 requires "per-source progress/error tracking with error isolation, statistics
aggregation, and a completion summary", and step 16 frames the Module 6 loading program as the
template to build from. Both halves come from MCP scaffolds — and the loading scaffold keeps
its counters as process-global state. Confirmed on server 1.32.9 (2026-08-14):
`sdk_guide(topic='load', language='java', record_count=1000)` returns
`senzing/code-snippets-v4` `java/snippets/loading/LoadViaFutures.java`, which declares

    private static int errorCount = 0;
    private static int successCount = 0;
    private static int retryCount = 0;

That is correct for a standalone `main()` and wrong the moment it is called once per source in
one process. Observed on three sources of 10 / 10 / 8 records, the completion summary read
10, then 20, then 28.

What makes it worth a ⛔ rather than a note is that the load was **correct** — 28 records, zero
errors, the datastore holding exactly what it should. Only the reporting was wrong, and it was
wrong in the least visible way available: plausible, monotonic, summing to the right total. The
same arithmetic hides a real failure, since a source that loads 0 of 8 still shows a rising
count inherited from its predecessors. A wrong number is worse than a blank field (INV-115),
because a blank invites a second look and a number does not.

These tests pin the hazard, both resolutions, and the reconciliation requirement — the last of
which is the part that actually catches the defect at runtime, since every check that looks
only at the aggregate passes.

Enforces **INV-243** — a per-source figure reported to the Bootcamper is reconciled against that source's own input count before it is shown.

Enforces **INV-245** — a value that failed its own verification check is not presented as a result; the discrepancy is reported in its place. (Split out of INV-243 on maintainer review, 2026-08-14, so each states one condition; both are enforced here, which is the "one test named by several invariants" case `test_invariant_enforcer_citations.py` counts pairs for.)

Source spec: `specs/orchestrator-per-source-stats-vs-static-scaffold-counters.md`.

`TheNoHandWrittenRuleIsScopedToSdkCalls` (#156) pins where the no-hand-written rule stops. As
worded before, "Orchestrator and redo code comes from the MCP tools, never hand-written" forbade
the orchestrator itself, while no MCP route serves one: `find_examples(query='multi-source')`
returned `examples: []` and `generate_scaffold` has no orchestration workflow (server 1.37.13,
2026-09-26, recorded as the step's `MCP-NEGATIVE` marker). The SDK calls stay MCP-derived, through
the Step 3 loader; the orchestration around them is ordinary code (INV-240: a prohibition states
its general rule).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE_C = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-06-data-processing"
    / "phaseC-multi-source.md"
)


def step_17():
    """Step 17's body — the hazard must be reachable at the step it governs (INV-183)."""
    text = PHASE_C.read_text(encoding="utf-8")
    start = text.index("## 17. Create orchestrator program")
    end = text.index("## 18. Test orchestrator", start)
    return re.sub(r"\s+", " ", text[start:end])


def _prose(text):
    """Comment-stripped, whitespace-collapsed prose, so a marker cannot satisfy a prose check."""
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", " ", text, flags=re.S))


def header():
    """Phase C's preamble: everything before the conditional gate."""
    text = PHASE_C.read_text(encoding="utf-8")
    return _prose(text[: text.index("**Conditional gate.**")])


def step_17_raw():
    text = PHASE_C.read_text(encoding="utf-8")
    start = text.index("## 17. Create orchestrator program")
    return text[start:text.index("## 18. Test orchestrator", start)]


class TheHazardIsNamed(unittest.TestCase):
    def test_the_counters_are_described_as_process_global(self):
        body = step_17()
        self.assertIn("process-global", body)

    def test_the_concrete_declaration_is_quoted_with_its_provenance(self):
        """A named symbol is what lets a reader check the claim against their own scaffold."""
        body = step_17()
        self.assertIn("LoadViaFutures.java", body)
        self.assertIn("private static int", body)
        self.assertIn("1.32.9", body)
        self.assertIn("sdk_guide(topic='load'", body)

    def test_it_says_why_the_scaffold_is_not_wrong(self):
        """Without this the guide 'fixes' a snippet that is correct for its own shape."""
        body = step_17()
        self.assertIn("standalone", body)
        self.assertIn("runs once and exits", body)

    def test_it_is_not_stated_as_a_java_only_problem(self):
        """INV-002: the bootcamper may be in any of five bindings."""
        body = step_17()
        self.assertIn("module-level or global state", body)
        self.assertIn("INV-002", body)

    def test_the_symptom_is_described_as_plausible_not_broken(self):
        """The reason it survives review is that it looks like data."""
        body = step_17()
        self.assertIn("accumulate", body)
        self.assertRegex(body, r"10, then 20, then 28")
        self.assertIn("0 of 8", body)


class BothResolutionsAreGiven(unittest.TestCase):
    """One resolution is a constraint; two is a choice the bootcamper's stack can make."""

    def test_scoping_the_counters_is_offered(self):
        body = step_17()
        self.assertIn("Scope the counters per source", body)
        self.assertIn("reset at each", body)

    def test_a_separate_process_per_source_is_offered(self):
        body = step_17()
        self.assertIn("own process", body)
        self.assertIn("starts clean", body)

    def test_neither_resolution_displaced_the_existing_requirements(self):
        """The step's original contract must survive the insertion."""
        body = step_17()
        for phrase in (
            "ordered loading with dependency enforcement",
            "per-source progress/error tracking with error isolation",
            "Retry with exponential backoff",
            "Error isolation",
            "Orchestrator health monitoring",
        ):
            self.assertIn(phrase, body, "%r was displaced" % phrase)


class TheFiguresMustBeReconciled(unittest.TestCase):
    """Criterion 2 — and the only part that catches the defect at runtime."""

    def test_per_source_counts_are_checked_against_the_input(self):
        body = step_17()
        self.assertIn("input record count", body)

    def test_the_per_source_counts_must_sum_to_the_aggregate(self):
        self.assertIn("sum to the aggregate", step_17())

    def test_the_comparison_is_reported_not_merely_performed(self):
        """An unreported check is indistinguishable from no check."""
        body = step_17()
        self.assertIn("Report the comparison", body)

    def test_a_disagreement_stops_rather_than_prints(self):
        body = step_17()
        self.assertIn("say so and stop", body)

    def test_it_says_why_aggregate_only_checking_is_insufficient(self):
        """The accumulating counters sum correctly; that is the trap."""
        self.assertIn("passes every check that looks", step_17())


class TheNoHandWrittenRuleIsScopedToSdkCalls(unittest.TestCase):
    """#156: the rule covers what the MCP tools serve, and names orchestration as ordinary code."""

    def test_the_header_scopes_the_rule_to_senzing_sdk_calls(self):
        body = header()
        self.assertIn("Senzing SDK calls", body)
        self.assertIn("never hand-written", body)
        self.assertNotIn("Orchestrator and redo code comes from the MCP tools", body)

    def test_the_header_names_orchestration_as_ordinary_code_and_says_why(self):
        body = header()
        self.assertIn("orchestration around them", body)
        self.assertIn("ordinary code", body)
        self.assertIn("no MCP route serves it", body)

    def test_the_module_rule_points_orchestration_at_the_phase_c_header(self):
        skill = _prose((PHASE_C.parent / "SKILL.md").read_text(encoding="utf-8"))
        start = skill.index("Loading, redo, and query code come from the MCP tools")
        rule = skill[start:skill.index("Override MCP-suggested paths", start)]
        self.assertIn("orchestrates", rule)
        self.assertIn("ordinary code", rule)
        self.assertIn("phaseC-multi-source.md", rule)

    def test_step_17_prescribes_no_query_that_returns_nothing(self):
        self.assertNotIn("multi-source", _prose(step_17_raw()))

    def test_step_17_names_the_step_3_loader_as_its_sdk_source(self):
        body = _prose(step_17_raw())
        self.assertIn("Senzing calls come from the Step 3 loader", body)
        self.assertIn("workflow='add_records'", body)

    def test_retryable_exceptions_are_routed_to_error_handling(self):
        body = _prose(step_17_raw())
        self.assertIn("sdk_guide(topic='error_handling'", body)
        self.assertIn("backoff loop is ordinary code", body)

    def test_the_absence_is_a_dated_negative_naming_both_owner_routes(self):
        marker = [ln for ln in step_17_raw().splitlines() if "MCP-NEGATIVE:" in ln]
        self.assertEqual(len(marker), 1, marker)
        line = marker[0]
        self.assertRegex(line, r"MCP-NEGATIVE: find_examples\(query='multi-source'")
        self.assertRegex(line, r"owner: find_examples IS the route")
        self.assertIn("generate_scaffold IS the route", line)
        self.assertRegex(line, r"server [0-9][0-9.]*, \d{4}-\d{2}-\d{2}")


if __name__ == "__main__":
    unittest.main()
