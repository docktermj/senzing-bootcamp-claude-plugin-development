"""Tests that the plugin's pre-code SDK lookup covers INPUTS, not just outputs.

INV-115 requires looking up a method's **response** structure before parsing it. Nothing
required confirming what a method *takes*: `get_sdk_reference`'s `flags` and
`response_schemas` topics do not cover parameter shapes. A bootcamp did both of those
lookups correctly and still lost a round trip passing
`{"ENTITIES": [{"ENTITY_ID": n}]}` to `find_network_by_entity_id`, which takes `List[int]`.

⚠️ **Corrected 2026-07-26 by a dry run against the live MCP server.** This module previously
pinned the conclusion that, since `flags` and `response_schemas` miss parameter shapes, "the
only remaining source is cross-language documentation" and the guide should fall back to
introspecting the installed binding. That was wrong:
`get_sdk_reference(topic='methods', filter='find_network_by_entity_id')` returns the
binding's own signature outright. The tests below now pin the corrected routing — MCP first,
via the `methods` topic, with local introspection as a genuine last resort — because routing
the guide *away* from MCP is precisely what INV-080 forbids, and a test that pins the wrong
premise makes the mistake permanent.

A second, related gap: flag *families* answer different questions. On the export methods
`SZ_EXPORT_INCLUDE_*` selects which entities appear as rows while `SZ_ENTITY_INCLUDE_*`
selects what detail each row carries, so an export flagged with only the former succeeds
and writes rows containing nothing but `ENTITY_ID`.

⚠️ These tests also pin a **correction**: `SZ_EXPORT_ALL_FLAGS` does exist for the export
methods (MCP: `get_sdk_reference(topic='flags', filter='export_json_entity_report')`,
sourced from the Java SDK flag enum). It is the *Python* binding that lacks it. The
guidance must qualify it by binding rather than deny it, because writing a Senzing
falsehood into the plugin breaches INV-080 exactly as a guess would.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "skills")
GROUND_RULES = os.path.join(SKILLS, "bootcamp-onboarding", "ground-rules.md")
PHASE_D = os.path.join(SKILLS, "module-06-data-processing", "phaseD-validation.md")
PHASE_2B = os.path.join(
    SKILLS, "module-07-query-visualize-discover", "phase2b-discover.md"
)
QUERY_PHASE_1 = os.path.join(
    SKILLS, "module-07-query-visualize-discover", "phase1-query-visualize.md"
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def squash(text):
    return re.sub(r"[*\s]+", " ", text)


class GroundRulesCoverParameterShapes(unittest.TestCase):
    def setUp(self):
        self.text = read(GROUND_RULES)

    def test_parameter_shape_rule_exists(self):
        self.assertIn("Parameter shapes, for the bootcamper's binding", self.text)

    def test_it_says_every_topic_carries_the_signature_when_filtered_by_a_method(self):
        """The 2026-07-30 correction: this pinned the opposite until server 1.32.2
        disproved it. `flags` and `response_schemas` both return a `method_signatures`
        block when `filter` names a method, so telling the reader those topics cover
        only what a method *returns* teaches them to distrust data they can see."""
        squashed = squash(self.text)
        self.assertIn("whenever `filter` names a method", squashed)
        self.assertIn("method_signatures", squashed)
        self.assertNotIn("not what it takes", squashed)

    def test_the_methods_topic_is_named_as_the_route_to_parameter_shapes(self):
        """The correction: MCP answers this, so the guide must be sent to MCP."""
        self.assertIn("topic='methods'", self.text)
        self.assertIn(
            "find_network_by_entity_id(entity_ids: List[int]",
            self.text,
            "ground-rules should show the signature the methods topic returns, so the "
            "reader can see that MCP does answer parameter shapes",
        )

    def test_it_no_longer_claims_mcp_cannot_reach_parameter_shapes(self):
        """Guards the correction against being reverted by a future edit."""
        squashed = squash(self.text)
        for false_premise in (
            "the only remaining source is cross-language documentation",
            "When the MCP reference does not cover the shape",
        ):
            with self.subTest(premise=false_premise):
                self.assertNotIn(squash(false_premise), squashed)

    def test_cross_language_docs_are_declared_non_authoritative(self):
        """Still true, and still needed: the divergence is real per binding."""
        self.assertRegex(
            self.text, r"Cross-language documentation is (still )?not authoritative"
        )

    def test_introspection_is_the_documented_last_resort(self):
        for probe in ("inspect.signature", "dir(SzEngineFlags)"):
            with self.subTest(probe=probe):
                self.assertIn(probe, self.text)
        squashed = squash(self.text)
        self.assertIn(
            "Only when `topic='methods'` genuinely does not cover it",
            squashed,
            "introspection must be framed as the fallback AFTER the MCP lookup, not as "
            "the primary route (INV-080)",
        )

    def test_flag_families_rule_exists(self):
        self.assertIn("Flag families answer different questions", self.text)

    def test_flag_families_state_rows_versus_detail(self):
        squashed = squash(self.text)
        self.assertIn("chooses which entities appear as rows", squashed)
        self.assertIn("chooses what detail each row carries", squashed)
        self.assertIn("nothing but `ENTITY_ID`", squashed)


class ExportCompositeIsQualifiedByBinding(unittest.TestCase):
    """The correction: qualify by binding, never deny the constant outright."""

    def test_neither_file_claims_the_composite_does_not_exist(self):
        for path in (GROUND_RULES, PHASE_D):
            with self.subTest(path=os.path.basename(path)):
                text = read(path)
                self.assertNotRegex(text, r"[Tt]here is no `SZ_EXPORT_ALL_FLAGS`")
                self.assertNotRegex(text, r"`SZ_EXPORT_ALL_FLAGS` does not exist")

    def test_ground_rules_qualifies_it_by_binding(self):
        squashed = squash(read(GROUND_RULES))
        self.assertIn("absent from the Python binding's `SzEngineFlags`", squashed)

    def test_phase_d_qualifies_it_by_binding(self):
        squashed = squash(read(PHASE_D))
        self.assertIn("absent from the Python binding's `SzEngineFlags`", squashed)


class PhaseDCarriesAWorkedExportExpression(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_D)

    def test_a_runnable_flag_expression_is_shown(self):
        self.assertIn("SZ_EXPORT_DEFAULT_FLAGS", self.text)
        self.assertRegex(self.text, r"(?s)```python.{0,900}export_json_entity_report")

    def test_it_marks_itself_as_needing_an_mcp_lookup(self):
        """A worked example must not become a substitute for the MCP lookup (INV-080).

        The requirement is unchanged; the vocabulary is. "This session" was retired as a
        freshness claim because it read as permission to present an earlier turn's result
        (`specs/mcp-freshness-contract-says-this-turn-and-this-session.md`), so a
        sourcing floor now says what it actually means: from the server, not from this file.
        """
        squashed = squash(self.text)
        self.assertIn(
            "Re-confirm both names via MCP rather than from this file "
            "(INV-080; a sourcing floor)", squashed)
        self.assertNotIn("via MCP this session", squashed,
                         "the retired freshness phrasing came back")
        self.assertIn("INV-080", self.text)

    def test_it_uses_the_correct_close_call(self):
        """`close_export_report`, not `close_export` — the Python-specific name."""
        self.assertIn("close_export_report", self.text)

    def test_raw_row_dump_precedes_parsing(self):
        squashed = squash(read(PHASE_D))
        self.assertIn("dump one raw row", squashed)
        self.assertIn("INV-115", read(PHASE_D))


class GraphMethodParameterShapesAreDocumented(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_2B)

    def test_step_4d_says_the_signature_is_already_in_the_response_it_just_read(self):
        """Same 2026-07-30 correction as ground-rules: this file carried the same false
        premise, and here it is sharper — step 4d has *just* told the reader to call
        `topic='flags'` and `topic='response_schemas'`, so the signature is literally in
        the response in front of them."""
        squashed = squash(self.text)
        self.assertIn("whenever `filter` names a method", squashed)
        self.assertNotIn("Neither of those topics tells you the ARGUMENT types", squashed)

    def test_step_4d_routes_to_the_methods_topic_not_to_guesswork(self):
        """Same correction as ground-rules: this file carried the false premise too."""
        self.assertIn("topic='methods'", self.text)
        self.assertNotIn(
            "the only remaining source is cross-language documentation",
            self.text,
            "step 4d again claims cross-language docs are the only source for parameter "
            "shapes; the methods topic answers them (verified 2026-07-26)",
        )

    def test_python_signature_is_given_for_both_graph_methods(self):
        self.assertIn("find_network_by_entity_id(entity_ids: List[int]", self.text)
        self.assertIn("find_path_by_entity_id(start_entity_id: int", self.text)

    def test_the_wrong_form_is_named_explicitly(self):
        """Naming the wrong shape is what prevents the natural inference."""
        self.assertIn('{"ENTITIES": [{"ENTITY_ID"', self.text)
        self.assertIn("SzSdkError", self.text)

    def test_guidance_stays_language_agnostic(self):
        """INV-002: only the known-divergent case is spelled out."""
        squashed = squash(self.text)
        self.assertIn("For any other language, confirm the shape from the installed binding", squashed)
        self.assertIn("INV-002", self.text)

    def test_response_schema_rule_still_present(self):
        """The new input rule must not have displaced the INV-115 output rule."""
        self.assertIn("INV-115", self.text)
        self.assertIn("response_schemas", self.text)


class AnEmptyCompositeMembersFieldIsNotAnAbsentFact(unittest.TestCase):
    """INV-194: one tool's silence is not the server's silence.

    The default-flags rule needs an unhappy path, and the right one.

    `phase1-query-visualize.md` tells the guide to read a composite's
    `composite_members` and confirm the flag populating a field is in it. A lookup can
    come back without that field. The worked example is `SZ_SEARCH_BY_ATTRIBUTES_DEFAULT_FLAGS`:
    no `composite_members`, only a description saying it "is defined as
    SZ_SEARCH_BY_ATTRIBUTES_ALL", whose own row lists its members (re-verified on MCP server
    1.37.14, 2026-09-28). A rule with no unhappy path silently becomes "assume it is fine".

    ⚠️ The obvious unhappy path is the wrong one. "No `composite_members`, so the check
    cannot be run" is a conclusion about **the tool that was asked**, not about the
    server: the description names the equivalent composite, and `search_docs` is the next
    route. This repo has already had to retract two over-generalized absolutes (INV-169);
    an empty structured field is the same trap in a new place.

    The example used to be the three `why_*` default composites, which returned no
    `composite_members`, a glob `applies_to` and a breaking-changes `source_file` at server
    1.32.2 (2026-07-31). That defect no longer reproduces at 1.37.14 (#196), so the
    narrative is retired, and a guard below keeps it from coming back. What the `why_*`
    composites still teach is their membership: the composite is **one** flag, carrying no
    entity-name flag, so `why_entities` returns `ENTITY_NAME: null` while match level, why
    key, ER rule, every feature score and CONFIRMATIONS/DENIALS all render. That is the
    deceptive half-populated row (INV-148).
    """

    def setUp(self):
        self.text = read(QUERY_PHASE_1)
        self.flat = squash(self.text)

    def test_the_rule_has_an_unhappy_path(self):
        self.assertRegex(
            self.flat,
            r"(?i)returns a composite with NO `?composite_members`?",
            "the procedure must say what to do when the lookup comes back without "
            "membership, or it silently becomes 'assume it is fine'",
        )

    def test_the_unhappy_path_sends_the_reader_to_the_other_tool(self):
        """Not "give up and OR blindly" — ask `search_docs`, which has the prose."""
        self.assertRegex(self.flat, r"(?i)you asked the wrong tool")
        self.assertRegex(
            self.flat, r"(?i)ask `search_docs` before concluding anything"
        )

    def test_it_states_the_general_lesson_not_only_the_instance(self):
        self.assertRegex(
            self.flat,
            r"(?i)only ever \"the tool I asked does not document X",
            "scoped to one composite alone, this would not survive the next composite "
            "whose structured membership comes back empty",
        )
        self.assertRegex(self.flat, r"(?i)empty structured field is not an absent fact")

    def test_the_worked_example_is_one_the_server_produces(self):
        """The unhappy path is taught with a composite that still has no structured members."""
        self.assertIn("SZ_SEARCH_BY_ATTRIBUTES_DEFAULT_FLAGS", self.text)
        self.assertRegex(
            self.flat,
            r"(?i)read the description first — it may name the composite it\s*equals — then "
            r"ask `search_docs` before concluding anything",
        )
        self.assertRegex(self.flat, r"It is defined as SZ_SEARCH_BY_ATTRIBUTES_ALL")

    def test_the_retired_why_defect_narrative_stays_gone(self):
        """#196: the why_* composites list their members now; the old account must not return."""
        for stale in ('["why_entities*"]', "For all three `why_*` default composites",
                      "breaking-changes document rather than the flags reference"):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, self.text)
        self.assertRegex(
            self.flat,
            r"seen at server 1\.32\.2 on 2026-07-31 and does not reproduce at 1\.37\.14",
            "the fix is recorded as a dated note, not silently erased",
        )

    def test_or_ing_blindly_is_the_last_resort_not_the_first(self):
        """Ordering is the whole point: two tools, then explicit OR, then disclosure."""
        both_empty = self.flat.lower().index("only if both tools come back empty")
        wrong_tool = self.flat.lower().index("you asked the wrong tool")
        self.assertLess(
            wrong_tool,
            both_empty,
            "the explicit-OR fallback must come after the second lookup, or a reader "
            "takes it as the immediate remedy",
        )

    def test_the_why_composite_membership_is_recorded_with_its_consequence(self):
        self.assertIn("SZ_WHY_ENTITIES_DEFAULT_FLAGS", self.text)
        self.assertRegex(self.flat, r"(?i)Equivalent to: `SZ_INCLUDE_FEATURE_SCORES`")
        self.assertRegex(
            self.flat,
            r"(?i)`ENTITY_NAME` comes back `null`",
            "the membership alone is trivia; the null field is what a reader recognizes",
        )
        self.assertIn("SZ_ENTITY_INCLUDE_ENTITY_NAME", self.text)

    def test_the_deceptive_shape_is_named(self):
        """INV-148, in its worse form: only the labels are missing."""
        self.assertIn("INV-148", self.text)
        self.assertRegex(self.flat, r"(?i)reads as unnamed data")

    def test_the_siblings_are_verified_rather_than_inferred(self):
        """INV-169: the entry inferred them; the server was asked about each."""
        for flag in (
            "SZ_WHY_RECORDS_DEFAULT_FLAGS",
            "SZ_WHY_RECORD_IN_ENTITY_DEFAULT_FLAGS",
        ):
            with self.subTest(flag=flag):
                self.assertIn(flag, self.text)
        self.assertRegex(self.flat, r"(?i)checked \*\*individually\*\*|checked individually")
        self.assertIn("INV-169", self.text)

    def test_the_claims_carry_their_provenance(self):
        """INV-080: a Senzing fact ships with the tool, version and date."""
        self.assertRegex(self.flat, r"server 1\.32\.2")
        self.assertRegex(self.flat, r"2026-07-31")

    def test_the_existing_rows_survive(self):
        """This extended the table; it must not have replaced it."""
        for composite in (
            "SZ_SEARCH_BY_ATTRIBUTES_ALL",
            "SZ_FIND_NETWORK_DEFAULT_FLAGS",
            "SZ_ENTITY_DEFAULT_FLAGS",
        ):
            with self.subTest(composite=composite):
                self.assertIn(composite, self.text)

    def test_the_scan_is_not_vacuous(self):
        self.assertTrue(os.path.isfile(QUERY_PHASE_1))
        self.assertGreater(len(self.text), 2000)


if __name__ == "__main__":
    unittest.main()
