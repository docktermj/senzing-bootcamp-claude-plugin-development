"""A payload routing answer must be honored in effect, not only in form.

MCP-NEGATIVE-SCAN: ignore-file — this file asserts the marker FORMAT (that the shipped
marker names its owning route and carries a server version and date). The token below is a
`startswith` needle in a test body, not a dated claim about the current server, and the
scanner would otherwise report it as a malformed marker. Since #323 the needle finds the
marker inside its `<!-- … -->` wrapper.

A Bootcamper was asked how to route a field and answered **payload**. The mapper kept the
key under its own name at the record root — where that name is a *registered feature
attribute* — so Senzing extracted it as a feature anyway. Their explicit answer was
silently not honored. The same field also went through a list-joining payload route, so
**13,803 of 19,050 records** carried `"XXX; VGB; GBR"` as one literal value.

⛔ **Every static gate passed.** The analyzer, the verbatim check and the routing report each
confirm the output matches the plan and the plan is faithful to the source. None of them
confirms the plan does what the Bootcamper asked, so an answer selecting a *behavior*
rather than a *value* is unverified by construction. That general shape is the finding; the
collision is one instance of it.

⚠️ **The analyzer already knew** — its SCHEMA warning fired and cleared on the rename. The
check was in the wrong place in the flow, not missing, which is why the remedy moves it to
the mapping gate rather than inventing a new instrument.

⛔ **The prohibition is documented; only its consequence is OBSERVATION-ONLY, and these
tests pin that split**, not just the guidance. `mapping_workflow` step 2's inline *SENZING
MAPPING REFERENCE* serves the prohibition itself — a root-level payload attribute "must NOT
be a registered feature attribute" (server 1.37.16, 2026-10-01, #322) — so the guidance cites
that step for the rule. What breaking it does (the key is extracted as a feature) is still
one run, one SDK build, the analyzer as corroborating instrument: neither that step nor any
indexed `search_docs` section states it. That absence is carried as an `MCP-NEGATIVE` marker
with its owning route so a dry run re-asks it (INV-080/INV-149/INV-194/INV-213).

Source spec: `specs/routing-a-registered-feature-attribute-to-payload-is-silently-a-no-op.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE5 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
           "module-05-data-quality-mapping")
PHASE2 = MODULE5 / "phase2-data-mapping.md"
PHASE3 = MODULE5 / "phase3-test-load.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def collision_markers():
    """`(raw line, marker text)` for each wrapped marker whose claim is this collision.

    #323 — the marker is a single-line HTML comment, `<!-- MCP-NEGATIVE: … -->`, so it is
    found inside its wrapper and returned without it. The file also carries an unrelated
    wrapped marker (step 2's `embedded_in` key), so the collision marker is the one whose
    claim, before ` — owner: `, names a registered feature attribute.
    """
    opener, closer = "<!-- ", " -->"
    found = []
    for line in PHASE2.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if raw.startswith(opener + "MCP-NEGATIVE:") and raw.endswith(closer):
            marker = raw[len(opener):-len(closer)]
            if "registered feature attribute" in marker.partition(" — owner: ")[0]:
                found.append((raw, marker))
    return found


class TheCollisionIsCaughtAtTheMappingGate(unittest.TestCase):

    def test_the_rule_is_stated_at_the_mapping_step(self):
        self.assertIn(
            "a root-level `payload` key MUST NOT be a registered feature attribute name",
            flat(PHASE2))

    def test_it_runs_before_the_plan_is_accepted(self):
        text = flat(PHASE2)
        self.assertIn("Before accepting the plan", text)
        self.assertIn("not after the output is analyzed", text)

    def test_it_reuses_the_catalog_lookup_the_module_already_makes(self):
        self.assertIn("the same lookup, asked of the other disposition", flat(PHASE2))


class TheBootcampersAnswerIsNotOverridden(unittest.TestCase):
    """INV-006 — their intent is achievable; only the key name is wrong."""

    def test_silent_re_routing_is_forbidden(self):
        self.assertIn("do NOT silently re-route or override the answer", flat(PHASE2))

    def test_the_collision_offers_a_rename_as_a_pinned_question(self):
        text = PHASE2.read_text(encoding="utf-8")
        question = [l for l in text.splitlines()
                    if l.lstrip().startswith("> 👉") and "registered Senzing feature" in l]
        self.assertEqual(1, len(question), "the collision has no single pinned question")
        self.assertIn("Shall I store it as", question[0])
        self.assertTrue(question[0].rstrip().endswith("(respond yes or no)"),
                        "the collision question is not answerable yes/no (INV-008)")

    def test_it_says_what_senzing_will_actually_do(self):
        self.assertIn("Senzing will resolve on it anyway", flat(PHASE2))

    def test_both_answers_are_recorded(self):
        text = flat(PHASE2)
        self.assertIn("never leave the collision unrecorded either way", text)


class AListValuedPayloadRouteIsWarned(unittest.TestCase):

    def test_the_join_behavior_is_stated_with_its_signature(self):
        text = flat(PHASE2)
        self.assertIn("joined into ONE literal value", text)
        self.assertIn("13,803 of 19,050 records", text)


class TheAnalyzerWarningMovesForward(unittest.TestCase):

    def test_phase_two_reads_the_schema_warnings_at_the_gate(self):
        self.assertIn("Surface the analyzer's SCHEMA warnings here", flat(PHASE2))

    def test_phase_three_routes_this_finding_back_rather_than_absorbing_it(self):
        """⛔ It must not be filed under the recommended-vs-flat conformance split."""
        text = flat(PHASE3)
        self.assertIn("One SCHEMA finding is NOT a conformance notice", text)
        self.assertIn("step 11's collision check did not run", text)


class TheGeneralShapeIsNamed(unittest.TestCase):
    """What the gates structurally cannot see."""

    def test_it_says_the_gates_check_the_plan_not_the_request(self):
        text = flat(PHASE2)
        self.assertIn("None of them confirms the plan does what the Bootcamper **asked "
                      "for**", text)

    def test_it_generalizes_to_any_behavior_selecting_answer(self):
        self.assertIn("Wherever a question's answer chooses a behavior", flat(PHASE2))


class ThePrecedenceMechanismIsMarkedObservationOnly(unittest.TestCase):
    """⛔ INV-080/INV-149 — never presented as MCP-sourced."""

    def test_it_is_labeled_observation_only_with_its_date_and_instrument(self):
        text = flat(PHASE2)
        self.assertIn("This mechanism is OBSERVATION-ONLY", text)
        self.assertIn("2026-08-17", text)
        self.assertIn("analyzer's own SCHEMA warning as the corroborating instrument", text)

    def test_it_tells_the_reader_to_re_confirm_before_relying_on_it(self):
        self.assertIn("re-confirm before relying on it", flat(PHASE2))

    def test_the_absence_carries_a_well_formed_negative_marker(self):
        """INV-194 — a negative with no owning route does not parse and is not evidence.

        #323 — rescoped to the wrapped form: the marker is an HTML comment, so the date is
        anchored before the closing ` -->` rather than at the end of the line.
        """
        lines = collision_markers()
        self.assertEqual(1, len(lines), "expected exactly one marker in this file")
        raw, marker = lines[0]
        self.assertIn("owner:", marker, "the marker names no owning route")
        self.assertIn("absence negative", marker)
        self.assertRegex(raw, r"server \d+\.\d+\.\d+, \d{4}-\d{2}-\d{2} -->$")

    def test_the_marker_is_not_left_as_bare_prose(self):
        """#323 — dated maintainer metadata must not render inside the skill."""
        bare = [n for n, l in enumerate(PHASE2.read_text(encoding="utf-8").splitlines(), 1)
                if l.lstrip().startswith("MCP-NEGATIVE:")]
        self.assertEqual([], bare, "a bare MCP-NEGATIVE marker renders as body text")

    def test_the_rule_is_not_claimed_as_documented(self):
        """#322 — rescoped: the prohibition is cited to its route; the consequence is not.

        Named for what it guarded before the server documented the rule, and kept so its
        history stays readable: what it now refuses is the CONSEQUENCE being claimed as
        documented.
        """
        text = flat(PHASE2)
        self.assertIn("This prohibition is documented: `mapping_workflow` step 2's inline "
                      "*SENZING MAPPING REFERENCE*", text)
        self.assertIn('"must NOT be a registered feature attribute"', text)
        self.assertIn("server **1.37.16, 2026-10-01**", text)
        self.assertIn("Treat the extracted-as-feature consequence as a strong local "
                      "observation, not as documented behavior", text)

    def test_the_prohibition_is_not_called_undocumented_again(self):
        """#322 — the old framing contradicted the tool the guide is already calling."""
        self.assertNotIn("not as a documented rule", flat(PHASE2))

    def test_the_marker_is_rescoped_to_the_consequence(self):
        """#322 / INV-213 — the claim is the consequence; the owner names both routes."""
        lines = collision_markers()
        self.assertEqual(1, len(lines), "expected exactly one marker in this file")
        _, marker = lines[0]
        self.assertTrue(marker.startswith(
            "MCP-NEGATIVE: search_docs(query='payload attribute versus registered feature "
            "attribute record root extracted as feature precedence', "
            "category='data_mapping') — "),
            "the marker's query string or route changed")
        claim, _, rest = marker.partition(" — owner: ")
        self.assertIn("no indexed section states that a root-level key named after a "
                      "registered feature attribute is extracted as a feature", claim)
        self.assertIn("mapping_workflow step 2's inline SENZING MAPPING REFERENCE carries "
                      "the prohibition", rest)
        self.assertIn("states no consequence", rest)
        self.assertIn("search_docs over the Entity Specification IS the route that would "
                      "carry the consequence", rest)
        self.assertIn('"Only the attributes listed here may appear inside a feature object. '
                      'Anything else is treated as payload"', rest)
        self.assertTrue(marker.endswith("(absence negative) — server 1.37.16, 2026-10-01"))


class TheCheckIsNotABlanketObjectionToPayload(unittest.TestCase):
    """Negative control: payload routing itself must stay ordinary and unobstructed."""

    def test_the_rule_is_scoped_to_registered_attribute_names(self):
        """A payload key that is not a registered attribute is untouched by the rule."""
        text = flat(PHASE2)
        self.assertIn("MUST NOT be a registered feature attribute name", text)
        self.assertNotIn("payload routing is discouraged", text)
        self.assertNotIn("avoid payload", text)

    def test_payload_remains_an_offered_disposition(self):
        self.assertIn("`feature`, `payload`, `ignore`, `derived`, or `extract`",
                      flat(PHASE2))

    def test_the_existing_rule_against_downgrading_to_payload_survives(self):
        self.assertIn("Never silently downgrade a bootcamper's choice to `payload`",
                      flat(PHASE2))


class TheGuidanceIsBehaviorNotAHelper(unittest.TestCase):
    """INV-002 — the catalog lookup is a data question, not a Python one."""

    def test_the_new_block_names_no_language_specific_helper(self):
        text = PHASE2.read_text(encoding="utf-8")
        start = text.index("Before accepting the plan")
        end = text.index("something must check the behavior was actually obtained.", start)
        block = text[start:end]
        for token in ("def ", "import ", "python3 "):
            with self.subTest(token=token):
                self.assertNotIn(token, block,
                                 "the rule is stated as code rather than as behavior")


if __name__ == "__main__":
    unittest.main()
