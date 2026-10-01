"""INV-198: Module 5's fast-path skips the module, so it must be gated on the question it
claims to answer, not on the cheaper one next to it.

Step 5a used to name the right distinction and then act on the wrong half: the prose said
the structural test "cannot tell you whether an attribute name will actually participate in
matching", and the offer was presented on `senzing_ready`, which was that structural test's
result. A real CORD record — `get_sample_data(dataset='las-vegas', source='PPP_LOANS')` —
carries eight specification attributes and eleven raw source columns, satisfies every
structural indicator, and would have been offered the skip. Structurally loadable is not
fully mapped.

The failure had no natural detector: fast-pathing a fully-mapped source is *correct*, so no
test can assert the offer never fires, and `senzing_ready: true` was a true statement about
structure. What is assertable is the shape of the decision — that both questions exist, that
the offer hangs off the second, and that a source with undecided columns is routed to mapping
with those columns named.

Two things this deliberately pins beyond "the words are present":

* **Order.** Structural check, then coverage check, then offer. A coverage check that ran
  after the offer would read identically in a grep and gate nothing.
* **The reasoning for the threshold.** A bare rule invites the next reader to "improve" it
  into a percentage, which is the tuning problem the count avoids.

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
PHASE_1 = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
    / "module-05-data-quality-mapping" / "phase1-quality-assessment.md"
)

# The eleven columns the fast-path used to skip, from the record the spec cites.
PPP_UNMAPPED = (
    "Business_Type", "CD", "DateApproved", "JobsReported", "Lender", "Loan_Range",
    "NAICS_Code", "NonProfit", "OwnedBy", "OwnedByRaceEthnicity", "OwnedByVeteran",
)


def text():
    return PHASE_1.read_text(encoding="utf-8")


def step_5a():
    t = text()
    return t[t.index("## 5a. Senzing-readiness check") : t.index("## 6. Assess data quality")]


def flat(chunk):
    return re.sub(r"\s+", " ", chunk.replace("**", ""))


def position(needle, chunk=None):
    """Index of a marker inside step 5a, so ordering can be asserted rather than assumed."""
    chunk = step_5a() if chunk is None else chunk
    idx = chunk.find(needle)
    if idx < 0:
        raise AssertionError(f"marker not found in step 5a: {needle!r}")
    return idx


class BothQuestionsAreAsked(unittest.TestCase):
    """The distinction the step already stated in prose is now two separate checks."""

    def test_the_structural_check_asks_whether_it_loads(self):
        self.assertIn("Perform the structural check: will it load?", step_5a())

    def test_the_coverage_check_asks_whether_anything_is_left_to_map(self):
        self.assertIn(
            "Perform the coverage check: is every field actually decided about?", step_5a()
        )

    def test_the_structural_result_is_labeled_as_the_entry_condition_only(self):
        squashed = flat(step_5a())
        self.assertIn("This is the entry condition, not the fast-path condition", squashed)
        self.assertIn(
            "Structurally loadable means the engine will accept the record; it does not mean "
            "every field in it has been decided about",
            squashed,
        )

    def test_the_two_results_are_recorded_as_two_fields(self):
        squashed = flat(step_5a())
        for field in ("`senzing_loadable`", "`fully_mapped`", "`unmapped_fields`"):
            with self.subTest(field=field):
                self.assertIn(field, squashed)

    def test_the_retired_single_field_is_handled_on_resume(self):
        """An existing registry must not be silently reinterpreted as coverage-checked."""
        squashed = flat(step_5a())
        self.assertIn("still carries `senzing_ready`", squashed)
        self.assertIn("treat `fully_mapped` as unknown", squashed)


class TheOfferIsNotGatedOnStructureAlone(unittest.TestCase):
    def test_the_offer_requires_all_three_results(self):
        """The heading names every gate: structure, coverage, and (#292, INV-335) type/name."""
        self.assertIn(
            "**If structurally loadable, fully mapped AND free of type/name candidates: "
            "present the fast-path offer.**",
            step_5a(),
        )

    def test_no_path_presents_the_offer_on_the_structural_result_alone(self):
        """Every branch that reaches the 👉 offer must have said 'fully mapped' first."""
        chunk = step_5a()
        offers = [m.start() for m in re.finditer(r"👉 \*\*Your CORD source", chunk)]
        self.assertEqual(1, len(offers), "there must be exactly one fast-path offer")
        gate = chunk.rfind("fully mapped", 0, offers[0])
        self.assertGreater(gate, position("Perform the coverage check"),
                           "the offer's nearest gate must be the coverage result")

    def test_the_checks_run_before_the_offer_in_that_order(self):
        self.assertLess(position("Perform the structural check"),
                        position("Perform the coverage check"))
        self.assertLess(position("Perform the coverage check"),
                        position("👉 **Your CORD source"))

    def test_the_offer_states_the_coverage_figure(self):
        squashed = flat(step_5a())
        self.assertIn(
            "all [N] of its fields resolve to the Senzing Entity Specification", squashed
        )


class AnUndecidedSourceIsRoutedToMappingWithItsColumnsNamed(unittest.TestCase):
    def test_the_partial_case_routes_to_mapping(self):
        self.assertIn(
            "**If structurally loadable but NOT fully mapped: route to mapping, and name the "
            "columns.**",
            step_5a(),
        )

    def test_it_is_a_statement_not_a_question(self):
        """Routing is not the bootcamper's choice; asking would imply it is."""
        self.assertIn("no 👉 question; the routing is not a choice", flat(step_5a()))

    def test_every_column_must_be_named_not_counted(self):
        squashed = flat(step_5a())
        self.assertIn("Name every unrecognized column", squashed)
        self.assertIn(
            "A count alone tells the bootcamper a decision exists without telling them what it "
            "is about",
            squashed,
        )

    def test_the_worked_example_names_all_eleven_columns(self):
        squashed = flat(step_5a())
        for column in PPP_UNMAPPED:
            with self.subTest(column=column):
                self.assertIn(column, squashed)


class TheThresholdIsStatedWithItsReasoning(unittest.TestCase):
    def test_the_rule_is_a_count_not_a_proportion(self):
        self.assertIn(
            "The threshold is a count, not a proportion: zero unrecognized keys, or no "
            "fast-path offer.",
            flat(step_5a()),
        )

    def test_it_says_why_not_a_percentage(self):
        squashed = flat(step_5a())
        self.assertIn("Why not a percentage", squashed)
        self.assertIn("one undecided column in thirty passes an 80%-coverage rule", squashed)

    def test_it_says_what_happens_to_payload_worthy_columns(self):
        """The spec's open question, answered explicitly rather than left to the reader."""
        squashed = flat(step_5a())
        self.assertIn("Why `payload`-worthy columns are NOT excluded from the count", squashed)
        self.assertIn("they are counted as undecided", squashed)
        for disposition in ("`feature`", "`payload`", "`ignore`", "`derived`", "`extract`"):
            with self.subTest(disposition=disposition):
                self.assertIn(disposition, squashed)

    def test_it_says_why_this_does_not_re_introduce_pointless_work(self):
        squashed = flat(step_5a())
        self.assertIn("Why this does not re-introduce pointless work", squashed)
        self.assertIn("has zero unrecognized keys and still fast-paths", squashed)

    def test_exact_string_matching_is_ruled_out_with_its_counter_example(self):
        """An exact match against the catalog fails a genuinely-mapped source."""
        squashed = flat(step_5a())
        self.assertIn("Do not resolve the second set by exact string match", squashed)
        self.assertIn("BUSINESS_NAME_ORG", squashed)
        self.assertIn("`NAME_ORG`", squashed)


class TheSenzingFactsCarryTheirProvenance(unittest.TestCase):
    """INV-080: every fact here came from a tool call, and says which."""

    def test_the_catalog_names_are_attributed_to_the_specification(self):
        squashed = flat(step_5a())
        self.assertIn("Entity Specification, *Feature: NAME*", squashed)
        self.assertIn("Usage types and payload (optional attributes)", squashed)
        self.assertRegex(squashed, ROUTE_DATA_MAPPING)

    def test_the_dispositions_are_attributed_to_the_tool_schema(self):
        self.assertIn("confirmed against the live tool schema", flat(step_5a()))

    def test_every_senzing_claim_names_a_server_version(self):
        self.assertGreaterEqual(
            len(re.findall(r"MCP server 1\.\d+\.\d+", step_5a())), 2,
            "each re-verified fact carries the server version it was confirmed against",
        )

    def test_the_undocumented_part_is_marked_as_observed_not_specified(self):
        """INV-080/INV-149: the label encoding is a shape we saw, not a rule the server states."""
        squashed = flat(step_5a())
        self.assertIn(
            "is an observed shape, not something the indexed specification states", squashed
        )


class NothingTheSpecRequiredToSurviveWasLost(unittest.TestCase):
    def test_both_record_shapes_are_still_admitted(self):
        """INV-145: the legacy flat structure is not a second-class shape."""
        squashed = flat(step_5a())
        self.assertIn("Loadable is a wider test than \"has a FEATURES array\"", squashed)
        self.assertIn("legacy flat structure", squashed)

    def test_the_step_is_still_cord_only(self):
        chunk = step_5a()
        self.assertIn("(CORD sources only)", chunk)
        self.assertIn(
            "**Non-CORD sources:** Skip this step entirely. Never present the fast-path offer "
            "for sources\n   with provenance other than `cord`.",
            chunk,
        )

    def test_record_preview_remains_optional_and_keeps_its_registration_caveat(self):
        squashed = flat(step_5a())
        self.assertIn("Optional and non-blocking", squashed)
        self.assertIn(
            "Preview requires the record's `DATA_SOURCE` code to be registered first", squashed
        )
        self.assertIn("SENZ2207", squashed)

    def test_record_preview_is_not_promoted_to_the_gate(self):
        """It cannot be: registration belongs to the loading phase."""
        chunk = step_5a()
        gate = chunk[position("Perform the coverage check"): position("👉 **Your CORD source")]
        self.assertNotIn("getRecordPreview returns", gate)
        self.assertIn("or use the\n   optional `getRecordPreview` check above", gate)


class AFullyPreMappedRunIsNeverSilent(unittest.TestCase):
    """The bootcamper came to learn mapping. A run where everything fast-paths teaches none."""

    def test_the_all_pre_mapped_case_is_handled(self):
        self.assertIn(
            "if ALL of them were fully pre-mapped, say so and\n   offer mapping practice",
            step_5a(),
        )

    def test_it_tells_the_bootcamper_what_they_would_miss(self):
        squashed = flat(step_5a())
        self.assertIn("the mapping exercise has nothing to work on", squashed)
        self.assertIn("you'd finish the bootcamp without writing a mapping", squashed)

    def test_it_offers_an_alternative_rather_than_just_reporting(self):
        squashed = flat(step_5a())
        self.assertIn("Would you like to add a raw, unmapped source", squashed)
        self.assertIn("a raw variant of the same data", squashed)
        self.assertIn("senzing-bootcamp-free-data", squashed)

    def test_declining_is_recorded_rather_than_dropped(self):
        self.assertIn(
            "Record the choice so graduation can state that no mapping was", step_5a()
        )

    def test_it_fires_only_when_no_source_reached_the_mapping_route(self):
        self.assertIn("This\n   fires only when no selected source reached step 6.", step_5a())


if __name__ == "__main__":
    unittest.main()
