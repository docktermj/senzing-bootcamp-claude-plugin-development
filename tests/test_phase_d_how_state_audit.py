"""Data processing validation audits every multi-record entity's construction history.

Phase D treated "redo queue drained" as the resolution-complete signal and then validated from
the export alone. Observed 2026-09-25 (SDK 4.4.1, SQLite, one load process per source, redo
drained to an empty queue): `how_entity` returned `FINAL_STATE.NEED_REEVALUATION: 1` and **two**
virtual entities for three entities that `get_entity` and the export reported as clean 5- and
3-record entities. The spot-check, the ratio and the stats passed all three, and the first place
the state surfaced was an opt-in Discover demonstration in Module 7 (issue #154).

The fix is a **How-state audit** in `phaseD-validation.md`, placed between the match-key audit
and the iterate-vs-proceed gate. It checks every entity with 2+ records, flags either sign,
reports one of three outcomes with "checked N of M", records the count (including zero) in
`docs/results_validation.md`, and offers **no remedy**: no Senzing route documents what the flag
means or how to clear it, which the section records in a dated `MCP-NEGATIVE` marker.

⚠️ **This asserts the prose shape, not engine behavior.** INV-108 keeps the suite offline and
stdlib-only, so nothing here can notice that Senzing started documenting the flag; the marker is
what puts that question on the online runs' worklist.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import os
import re
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "skills")
PHASE_D = os.path.join(SKILLS, "module-06-data-processing", "phaseD-validation.md")
DISCOVER = os.path.join(
    SKILLS, "module-07-query-visualize-discover", "phase2-discover.md"
)
REPORTS = os.path.join(REPO_ROOT, ".claude", "skills", "dry-run", "coverage_reports.py")

AUDIT_HEADING = "## How-state audit"
MATCH_KEY_HEADING = "## Match-key audit"
GATE_HEADING = "## Iterate vs. proceed decision gate"
REDO_LINE = "- ✅ Redo queue drained after loading"

#: Any binding's spelling of the re-evaluation calls. The section must not suggest one: no route
#: documents that it is the response to this flag (issue #154, Scope item 5).
REMEDY = re.compile(r"(?i)reevaluate_?(?:entity|record)")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_reports():
    spec = importlib.util.spec_from_file_location("coverage_reports_how_state", REPORTS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def section(text, heading, level="## "):
    """The body from `heading` up to the next heading of the same level, or None."""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if start is None and line.startswith(heading):
            start = i
            continue
        if start is not None and line.startswith(level) and not line.startswith(level + "#"):
            return "\n".join(lines[start:i])
    return None if start is None else "\n".join(lines[start:])


def flat(text):
    """Collapse whitespace so a phrase check survives the prose being re-wrapped."""
    return " ".join((text or "").split())


def heading_line(text, heading):
    for i, line in enumerate(text.split("\n")):
        if line.startswith(heading):
            return i
    return None


class TheSectionExistsWhereTheGateCanSeeIt(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_D)

    def test_the_section_exists(self):
        self.assertIsNotNone(
            heading_line(self.text, AUDIT_HEADING),
            "phaseD-validation.md has no %r section — without it Module 6 signs off record "
            "counts the engine's own construction history does not support (#154)" % AUDIT_HEADING,
        )

    def test_it_sits_after_the_match_key_audit_and_before_the_gate(self):
        audit = heading_line(self.text, AUDIT_HEADING)
        match_key = heading_line(self.text, MATCH_KEY_HEADING)
        gate = heading_line(self.text, GATE_HEADING)
        self.assertIsNotNone(audit, "the how-state audit section is missing")
        self.assertIsNotNone(match_key, "the match-key audit heading moved or was renamed")
        self.assertIsNotNone(gate, "the iterate-vs-proceed gate heading moved or was renamed")
        self.assertLess(match_key, audit, "the how-state audit must follow the match-key audit")
        self.assertLess(audit, gate, "the how-state audit must precede the gate it feeds")

    def test_it_runs_on_both_paths(self):
        body = flat(section(self.text, AUDIT_HEADING))
        for path in ("single-source", "multi-source"):
            self.assertIn(
                path, body,
                "the audit must say it runs on the %s path; it sits outside both path "
                "blocks, so a reader needs to be told it applies to each" % path,
            )


class TheAuditChecksEveryMultiRecordEntity(unittest.TestCase):
    def setUp(self):
        self.body = flat(section(read(PHASE_D), AUDIT_HEADING))

    def test_it_names_the_method_and_both_signs(self):
        for token in ("how_entity", "NEED_REEVALUATION", "VIRTUAL_ENTITIES", "FINAL_STATE"):
            self.assertIn(token, self.body, "the audit must name %r" % token)

    def test_every_entity_with_two_or_more_records_and_no_sampling(self):
        self.assertIn("2 or more records", self.body)
        self.assertIn(
            "No sampling", self.body,
            "the audit covers every multi-record entity; a sample is how the three unsettled "
            "entities passed a 25/25 spot-check",
        )

    def test_it_reports_coverage(self):
        self.assertIn("checked N of M", self.body)
        self.assertIn(
            "checked 0 of 0", self.body,
            "the no-multi-record-entities case must be stated, or an empty run reads as a "
            "skipped one",
        )

    def test_either_sign_is_enough_and_the_sign_is_named(self):
        self.assertRegex(self.body, r"(?i)\beither sign\b")
        self.assertRegex(
            self.body, r"(?i)which sign fired|sign or signs",
            "the audit must report which sign fired for each entity — nothing documents "
            "whether the two always go together",
        )
        self.assertRegex(
            self.body, r"more than one element",
            "the VIRTUAL_ENTITIES sign is 'more than one element', not 'non-empty'",
        )

    def test_the_method_name_comes_from_the_binding(self):
        self.assertIn(
            "get_sdk_reference(topic='parameters'", self.body,
            "the method name differs per binding; the audit must take it from "
            "get_sdk_reference rather than copy one binding's spelling",
        )
        self.assertIn("language='<chosen_language>'", self.body)

    def test_one_response_is_dumped_before_parsing(self):
        self.assertIn("INV-115", self.body)
        self.assertRegex(self.body, r"(?i)dump ONE `how_entity` response")


class ItHasThreeOutcomesAndNeverBlocks(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_D)
        self.body = flat(section(self.text, AUDIT_HEADING))

    def test_three_outcomes(self):
        for outcome in ("**Finding**", "**No finding**", "**Could not measure**"):
            self.assertIn(outcome, self.body, "the audit must state the %s outcome" % outcome)

    def test_no_finding_requires_every_entity_checked(self):
        self.assertIn(
            '(INV-115) Never report "no finding" unless N equals M', self.body,
            "'no finding' must require every entity to have been checked — a response that "
            "never arrived rendered as a clean result is what INV-115 forbids",
        )
        self.assertIn("Never collapse a partial run into \"no finding\" (INV-115)", self.body)

    def test_it_cites_bootcamper_facing_invariants_only(self):
        """INV-308 binds the repo's verification tooling, not a Bootcamper's guide."""
        self.assertNotIn(
            "INV-308", self.body,
            "the how-state audit cites INV-308, which governs the repository's own "
            "verification tooling; the Bootcamper-facing rule for a result that never "
            "arrived is INV-115",
        )

    def test_it_never_blocks(self):
        self.assertIn("The outcome never blocks (INV-117, INV-264)", self.body)

    def test_the_gate_presents_the_outcome(self):
        gate = flat(section(self.text, GATE_HEADING))
        self.assertIn(
            "how-state audit", gate,
            "the iterate-vs-proceed gate must present the how-state audit's outcome",
        )
        self.assertIn("does not move the gate to a different branch", gate)


class NoRemedyAndTheNegativeIsMarked(unittest.TestCase):
    def setUp(self):
        self.body = section(read(PHASE_D), AUDIT_HEADING) or ""

    def test_no_reevaluation_call_is_suggested(self):
        self.assertTrue(self.body, "the how-state audit section is missing")
        hit = REMEDY.search(self.body)
        self.assertIsNone(
            hit,
            "the how-state audit names %r — it must not suggest a re-evaluation call or any "
            "other remedy: no Senzing route documents what NEED_REEVALUATION means or what "
            "clears it (#154)" % (hit.group(0) if hit else None),
        )

    def test_the_meaning_is_observation_only(self):
        self.assertIn("observation-only", self.body)
        self.assertIn("INV-080/INV-149", self.body)

    def test_the_marker_parses_and_names_both_owner_routes(self):
        reports = load_reports()
        markers = [m for m in (reports.MCP_NEGATIVE.search(line)
                               for line in self.body.split("\n")) if m]
        self.assertEqual(
            len(markers), 1,
            "the section must carry exactly one well-formed MCP-NEGATIVE marker on one line "
            "(INV-209); found %d" % len(markers),
        )
        marker = markers[0]
        self.assertIn("NEED_REEVALUATION", marker.group("claim"))
        whole = marker.group(0)
        self.assertIn("search_docs(", whole, "search_docs is one owner route (INV-194)")
        self.assertIn(
            "get_sdk_reference(topic='response_schemas'", marker.group("owner"),
            "the response-schema route is the owner that would carry a field description",
        )
        self.assertRegex(marker.group("version"), r"^\d+\.\d+")
        self.assertRegex(marker.group("date"), r"^\d{4}-\d{2}-\d{2}$")


class TheResultsDocumentRecordsTheCount(unittest.TestCase):
    def setUp(self):
        self.body = flat(section(read(PHASE_D), AUDIT_HEADING))

    def test_it_writes_to_results_validation(self):
        self.assertIn("docs/results_validation.md", self.body)
        self.assertIn("`## How-state audit`", self.body)

    def test_including_zero(self):
        self.assertIn(
            "including zero", self.body,
            "the count of unsettled entities is recorded even when it is zero — an absent "
            "section cannot be told apart from an audit that never ran",
        )

    def test_flagged_record_counts_are_marked_unconfirmed(self):
        self.assertIn("unconfirmed by the engine's construction history", self.body)


class TheSuccessCriterionSitsBesideTheRedoLine(unittest.TestCase):
    def test_new_line_follows_the_unchanged_redo_line(self):
        lines = read(PHASE_D).split("\n")
        self.assertIn(REDO_LINE, lines, "the 'Redo queue drained' line must stay as it is")
        after = lines[lines.index(REDO_LINE) + 1]
        self.assertTrue(
            after.startswith("- ✅ How-state audit run"),
            "the how-state success criterion must sit directly after the redo line; found %r"
            % after,
        )


class DiscoverStep4cPointsToTheAudit(unittest.TestCase):
    def test_the_step_4c_note(self):
        body = flat(section(read(DISCOVER), "### Step 4c", level="### "))
        self.assertTrue(body, "phase2-discover.md has no Step 4c section")
        for token in ("NEED_REEVALUATION", "VIRTUAL_ENTITIES[]", "How-state audit",
                      "../module-06-data-processing/phaseD-validation.md"):
            self.assertIn(
                token, body,
                "step 4c must say so when its how_entity response shows either sign and "
                "point to Phase D's audit; missing %r" % token,
            )

    def test_the_cross_reference_resolves(self):
        self.assertTrue(os.path.isfile(PHASE_D))
        self.assertIsNotNone(heading_line(read(PHASE_D), AUDIT_HEADING))


if __name__ == "__main__":
    unittest.main()
