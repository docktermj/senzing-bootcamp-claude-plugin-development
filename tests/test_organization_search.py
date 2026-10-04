"""Searching by name must find organizations, not only persons.

The bundled reference server built its search attribute document as
`{"NAME_FULL": query}`. Per the Senzing Entity Specification (Name > Feature: NAME),
`NAME_ORG` is the organization name attribute and `NAME_FULL` is the single-field
attribute for a name whose type is unknown — so an organization name sent as
`NAME_FULL` matches nothing **and raises no error**. `"ABSOLUTE DENTAL"` returned 0
results against data containing it many times, while a person name returned a hit
immediately; on a dataset that was roughly half organizations, search silently failed
for about half the population.

It mattered doubly because the defect was in the *reference implementation* every
non-Python build is modeled on (INV-090), so it propagated into a generated query
program in the same session.

These tests drive the real `Model.search()` with a fake engine that behaves the way
Senzing does — matching a name only under the attribute it was mapped with — plus
guardrails on the guidance so a server in another language inherits the rule.

No phrase-level pattern (#438): its line reads are of Python source, the handler's code lines, as
#424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SERVER = PLUGIN / "scripts" / "senzing_viz_server.py"
CONTRACT = PLUGIN / "skills" / "module-03b-truthset-visualization" / "visualization-api-reference.md"
MODULE07 = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"


def load_server():
    spec = importlib.util.spec_from_file_location("viz_server_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SERVER_MOD = load_server()


class FakeEngine:
    """Matches a query only under the attribute the record was mapped with.

    This is the behavior that makes the defect silent: a wrong attribute yields an
    empty result set, not an error.
    """

    def __init__(self, by_attr):
        self.by_attr = by_attr          # {"NAME_ORG": {"ABSOLUTE DENTAL": 42}, ...}
        self.calls = []                 # attribute docs seen, in order

    def search_by_attributes(self, attrs, flags):
        doc = json.loads(attrs)
        self.calls.append(doc)
        (attr, value), = doc.items()
        entity_id = self.by_attr.get(attr, {}).get(value)
        if entity_id is None:
            return json.dumps({"RESOLVED_ENTITIES": []})
        return json.dumps(
            {
                "RESOLVED_ENTITIES": [
                    {
                        "ENTITY": {"RESOLVED_ENTITY": {"ENTITY_ID": entity_id, "ENTITY_NAME": value}},
                        "MATCH_INFO": {"MATCH_KEY": "+NAME", "ERRULE_CODE": "CNAME"},
                    }
                ]
            }
        )


class RaisingEngine:
    def __init__(self, message="engine unavailable"):
        self.message = message

    def search_by_attributes(self, attrs, flags):
        raise RuntimeError(self.message)


def model():
    """A Model with no loaded entities — search must not depend on local state."""
    inst = SERVER_MOD.Model.__new__(SERVER_MOD.Model)
    inst.entities = {}
    return inst


class OrganizationsAreFound(unittest.TestCase):
    def test_organization_name_is_found_via_name_org(self):
        engine = FakeEngine({"NAME_ORG": {"ABSOLUTE DENTAL": 42}})
        out = model().search(engine, 0, "ABSOLUTE DENTAL")
        self.assertEqual([r["entity_id"] for r in out["results"]], [42])

    def test_name_full_is_tried_before_name_org(self):
        """Order matters: the person case must not pay for an extra call."""
        engine = FakeEngine({"NAME_FULL": {"Robert Smith": 7}})
        out = model().search(engine, 0, "Robert Smith")
        self.assertEqual([r["entity_id"] for r in out["results"]], [7])
        self.assertEqual([list(c)[0] for c in engine.calls], ["NAME_FULL"])

    def test_falls_through_to_name_org_only_when_name_full_finds_nothing(self):
        engine = FakeEngine({"NAME_ORG": {"AUTONATION": 9}})
        model().search(engine, 0, "AUTONATION")
        self.assertEqual([list(c)[0] for c in engine.calls], ["NAME_FULL", "NAME_ORG"])

    def test_both_attributes_are_declared_in_order(self):
        self.assertEqual(("NAME_FULL", "NAME_ORG"), SERVER_MOD.Model.SEARCH_NAME_ATTRS)

    def test_no_source_line_searches_name_full_alone(self):
        """The original defect, pinned: a lone NAME_FULL attribute document."""
        text = SERVER.read_text(encoding="utf-8")
        self.assertNotIn('json.dumps({"NAME_FULL": query})', text)


class EmptyResultsExplainThemselves(unittest.TestCase):
    """INV-115: an empty result is a probable wrong query, not proven absence."""

    def test_reports_which_attributes_were_tried(self):
        engine = FakeEngine({})
        out = model().search(engine, 0, "NOBODY AT ALL")
        self.assertEqual(out["results"], [])
        self.assertEqual(out["attributes_tried"], ["NAME_FULL", "NAME_ORG"])

    def test_successful_search_also_reports_what_was_tried(self):
        engine = FakeEngine({"NAME_ORG": {"ABSOLUTE DENTAL": 42}})
        out = model().search(engine, 0, "ABSOLUTE DENTAL")
        self.assertEqual(out["attributes_tried"], ["NAME_FULL", "NAME_ORG"])

    def test_ui_names_the_attributes_instead_of_claiming_absence(self):
        text = SERVER.read_text(encoding="utf-8")
        self.assertIn("attributes_tried", text)
        self.assertIn("No entity matched", text)
        self.assertNotIn("No matching entities found.", text)

    def test_empty_query_short_circuits(self):
        engine = FakeEngine({})
        self.assertEqual(model().search(engine, 0, "   ")["results"], [])
        self.assertEqual(engine.calls, [])


class EngineErrorsAreSurfaced(unittest.TestCase):
    def test_error_is_reported_when_nothing_matched(self):
        out = model().search(RaisingEngine("boom"), 0, "anything")
        self.assertEqual(out["results"], [])
        self.assertIn("boom", out["error"])

    def test_a_hit_is_not_discarded_by_a_later_failure(self):
        """NAME_FULL hits, NAME_ORG would raise — the hit must survive."""

        class HitThenRaise(FakeEngine):
            def search_by_attributes(self, attrs, flags):
                if list(json.loads(attrs))[0] == "NAME_ORG":
                    raise RuntimeError("second call fails")
                return super().search_by_attributes(attrs, flags)

        engine = HitThenRaise({"NAME_FULL": {"Robert Smith": 7}})
        out = model().search(engine, 0, "Robert Smith")
        self.assertEqual([r["entity_id"] for r in out["results"]], [7])
        self.assertNotIn("error", out)


class AFailedAttemptIsNotTheEndOfTheList(unittest.TestCase):
    """INV-190. The mirror of `test_a_hit_is_not_discarded_by_a_later_failure`.

    The guard was `if not items: return ...`, which is unconditionally true on the
    *first* attribute — so an error searching `NAME_FULL` returned before `NAME_ORG`
    was ever called, reinstating the INV-164 defect on the error path with an engine
    message attached pointing at the attribute that could not have matched anyway.
    """

    class RaiseThenHit(FakeEngine):
        def search_by_attributes(self, attrs, flags):
            if list(json.loads(attrs))[0] == "NAME_FULL":
                raise RuntimeError("first call fails")
            return super().search_by_attributes(attrs, flags)

    def test_name_org_is_still_tried_after_name_full_raises(self):
        engine = self.RaiseThenHit({"NAME_ORG": {"ABSOLUTE DENTAL": 42}})
        out = model().search(engine, 0, "ABSOLUTE DENTAL")
        self.assertEqual([r["entity_id"] for r in out["results"]], [42])
        self.assertEqual(out["attributes_tried"], ["NAME_FULL", "NAME_ORG"])
        self.assertNotIn("error", out, "a hit stands; a failure behind it is not an error")

    def test_a_failed_attempt_is_still_reported_as_tried(self):
        engine = self.RaiseThenHit({})
        out = model().search(engine, 0, "NOBODY AT ALL")
        self.assertEqual(out["attributes_tried"], ["NAME_FULL", "NAME_ORG"])

    def test_a_failure_with_no_hit_anywhere_is_reported_not_silently_no_match(self):
        """Otherwise "the engine could not run this" renders as the clean no-match
        "nothing in your data has that name" (INV-115)."""
        engine = self.RaiseThenHit({})
        out = model().search(engine, 0, "NOBODY AT ALL")
        self.assertEqual(out["results"], [])
        self.assertIn("first call fails", out["error"])
        self.assertIn("NAME_FULL", out["error"], "the error must name the attribute that failed")

    def test_every_failed_attribute_is_named_when_all_fail(self):
        out = model().search(RaisingEngine("boom"), 0, "anything")
        self.assertEqual(out["attributes_tried"], ["NAME_FULL", "NAME_ORG"])
        for attr in SERVER_MOD.Model.SEARCH_NAME_ATTRS:
            self.assertIn(attr, out["error"])

    def test_the_loop_does_not_return_from_its_except_handler(self):
        """Pins the shape, not just the behavior: a `return` inside the handler is
        how the bug is written, whatever the condition guarding it says."""
        source = SERVER.read_text(encoding="utf-8")
        body = source.split("def search(self, engine, flags, query):", 1)[1]
        body = body.split("\n    def ", 1)[0]
        handler = body.split("except Exception as exc:", 1)[1].split("items.extend", 1)[0]
        code = [
            line for line in handler.splitlines() if not line.strip().startswith("#")
        ]  # the comment explains the old `return`; only the code counts
        self.assertNotIn("return", "\n".join(code))


class LegacyBindingSignatureStillWorks(unittest.TestCase):
    """Some bindings take a trailing search-profile argument."""

    def test_three_argument_search_by_attributes(self):
        class ThreeArg:
            def __init__(self):
                self.calls = []

            def search_by_attributes(self, attrs, flags, profile):
                self.calls.append(profile)
                return json.dumps(
                    {
                        "RESOLVED_ENTITIES": [
                            {
                                "ENTITY": {"RESOLVED_ENTITY": {"ENTITY_ID": 1, "ENTITY_NAME": "X"}},
                                "MATCH_INFO": {},
                            }
                        ]
                    }
                )

        engine = ThreeArg()
        out = model().search(engine, 0, "X")
        self.assertEqual([r["entity_id"] for r in out["results"]], [1])
        self.assertEqual(engine.calls, [""])


class GuidanceBindsAnyLanguage(unittest.TestCase):
    """INV-090/INV-124: the rule must live in the contract, not only in Python."""

    def test_contract_requires_name_org(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("NAME_ORG", text)
        self.assertRegex(text, r"(?i)NAME_ORG[^\n]*organization|organization[^\n]*NAME_ORG")

    def test_contract_warns_the_failure_is_silent(self):
        self.assertRegex(
            CONTRACT.read_text(encoding="utf-8"),
            r"(?i)matches \*\*nothing\*\*|silently fail|no error",
        )

    def test_module07_query_guidance_names_name_org(self):
        self.assertIn("NAME_ORG", MODULE07.read_text(encoding="utf-8"))

    def test_contract_requires_chips_be_run_not_merely_derived(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r"(?i)verified.{0,400}?(?:actually run|same search path)",
            "the chips contract must say verification means running the query",
        )


class ChipsAreVerifiedBeforeBeingOffered(unittest.TestCase):
    def test_live_chips_are_dropped_when_they_match_nothing(self):
        text = SERVER.read_text(encoding="utf-8")
        self.assertIn("dropped example chip (no match)", text)

    def test_snapshot_examples_are_dropped_and_reported(self):
        text = SERVER.read_text(encoding="utf-8")
        self.assertIn("dropped snapshot example", text)
        self.assertRegex(text, r"search returned no match")


if __name__ == "__main__":
    unittest.main()
