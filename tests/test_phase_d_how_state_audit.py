"""Data processing validation audits every multi-record entity's construction history.

Phase D treated "redo queue drained" as the resolution-complete signal and then validated from
the export alone. Observed 2026-09-25 (SDK 4.4.1, SQLite, one load process per source, redo
drained to an empty queue): `how_entity` returned `FINAL_STATE.NEED_REEVALUATION: 1` and **two**
virtual entities for three entities that `get_entity` and the export reported as clean 5- and
3-record entities. The spot-check, the ratio and the stats passed all three, and the first place
the state surfaced was an opt-in Discover demonstration in Module 7 (issue #154).

The fix is a **How-state audit** in `phaseD-validation.md`, placed between the match-key audit
and the iterate-vs-proceed gate. It checks every entity with 2+ records, flags either sign,
reports one of four outcomes with "checked N of M", records the count (including zero) in
`docs/results_validation.md`, and offers **no remedy**: no Senzing route documents what the flag
means or how to clear it, which the section records in a dated `MCP-NEGATIVE` marker.

⛔ **An empty population is its own outcome, never "no finding" (issue #232, INV-265).** #154
shipped M = 0 as "checked 0 of 0" and "no finding", which is an empty input reported as the
audit's clean result — and zero multi-record entities is also exactly what a reader that parses
`RESOLVED_ENTITY.RECORDS[]` under the wrong name produces (INV-115). So M = 0 is **Nothing to
check**, reached only when the export returned at least one entity and its `RECORDS[]` lengths sum
to the records loaded; otherwise **Could not measure**. Its `docs/results_validation.md` section
omits the "0 unsettled" line, which stays the rule for **No finding**. The checks for that are
functions over the text, so `EmptyPopulationNegativeControls` can show each one fails on the
wording it replaced.

⚠️ **This asserts the prose shape, not engine behavior.** INV-108 keeps the suite offline and
stdlib-only, so nothing here can notice that Senzing started documenting the flag; the marker is
what puts that question on the online runs' worklist.

Run:  python3 -m unittest discover -s tests

INV-334 is the invariant this module enforces: the audit of every multi-record entity, its four
outcomes and the M = 0 rule. Like every guard here it pins the text; it cannot establish that a
live run performs the audit, which only a dry-run phase 3 walk observes.
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


OUTCOMES = ("**Finding**", "**No finding**", "**Nothing to check**", "**Could not measure**")
NOTHING_TO_CHECK = "Nothing to check"
RECORD_IT = "**Record it in `docs/results_validation.md`**"
GATE_LINE = "**Present the how-state audit's outcome beside the match-key audit's**"
INCLUDING_ZERO = 'including zero: write "0 unsettled" rather than omitting the section'


def outcome_bullets(audit):
    """{label: bullet body} for the section's top-level `- **Label** —` bullets.

    A bullet runs until the next line that starts at column 0, so its indented sub-bullets and
    indented continuation paragraphs stay with it.
    """
    bullets, label, body = {}, None, []
    for line in (audit or "").split("\n"):
        m = re.match(r"^- \*\*([^*]+)\*\* —", line)
        if m or (line and not line[0].isspace()):
            if label is not None:
                bullets[label] = "\n".join(body)
            label, body = (m.group(1), [line]) if m else (None, [])
        elif label is not None:
            body.append(line)
    if label is not None:
        bullets[label] = "\n".join(body)
    return bullets


def paragraph_from(text, start):
    """From `start` up to the next blank line, flattened; "" when `start` is absent."""
    i = (text or "").find(start)
    if i < 0:
        return ""
    end = text.find("\n\n", i)
    return flat(text[i:] if end < 0 else text[i:end])


def four_outcome_problems(text):
    audit = section(text, AUDIT_HEADING) or ""
    labels = outcome_bullets(audit)
    problems = []
    for outcome in OUTCOMES:
        if outcome.strip("*") not in labels:
            problems.append("no top-level %s outcome bullet" % outcome)
    if re.search(r"(?i)\bthree outcomes\b", audit):
        problems.append("the section still announces three outcomes")
    return problems


def zero_population_problems(text):
    """M = 0 is **Nothing to check**, and is never mapped to "no finding" (INV-265)."""
    audit = section(text, AUDIT_HEADING) or ""
    bullets = outcome_bullets(audit)
    problems = []
    if "0 of 0" in flat(bullets.get("No finding", "")):
        problems.append("the No finding bullet still covers the 0-of-0 case")
    if re.search(r'"checked 0 of 0"\s+and\s+"no finding"', flat(audit)):
        problems.append('the section still pairs "checked 0 of 0" with "no finding"')
    ntc = flat(bullets.get(NOTHING_TO_CHECK, ""))
    for phrase in ("M is 0", '"checked 0 of 0"', 'never "no finding"', "(INV-265)"):
        if phrase not in ntc:
            problems.append("the Nothing to check bullet does not say %r" % phrase)
    return problems


def precondition_problems(text):
    """Both conditions, and could-not-measure naming the one that failed."""
    audit = section(text, AUDIT_HEADING) or ""
    bullets = outcome_bullets(audit)
    ntc = flat(bullets.get(NOTHING_TO_CHECK, ""))
    problems = []
    for phrase, why in (
        ("only when **both** hold", "both conditions are required"),
        ("at least one entity**", "the export must have returned at least one entity"),
        ("`RESOLVED_ENTITY.RECORDS[]`, summed across the whole export",
         "the record sum is taken over the whole export"),
        ("equal the total records loaded", "the sum is compared with the records loaded"),
        ("step 28", "the records-loaded figure is the one step 28 wrote"),
        ("the outcome is **could not measure**, naming which condition failed",
         "a failed condition is could not measure, naming which"),
    ):
        if phrase not in ntc:
            problems.append("%s (missing %r)" % (why, phrase))
    if "nothing to check** condition failed" not in flat(bullets.get("Could not measure", "")):
        problems.append("the Could not measure bullet does not cover a failed nothing-to-check "
                        "condition")
    return problems


def recording_problems(text):
    """Nothing to check writes the section, with no "0 unsettled" line."""
    record = paragraph_from(section(text, AUDIT_HEADING) or "", RECORD_IT)
    problems = []
    if INCLUDING_ZERO not in record:
        problems.append("the including-zero rule is gone from the recording paragraph")
    omission = record.find('For **nothing to check**, still write the section')
    if omission < 0:
        problems.append("the recording paragraph does not say the section is still written for "
                        "nothing to check")
        return problems
    tail = record[omission:]
    for phrase in ('"checked 0 of 0"', '**omit the "0 unsettled" line**'):
        if phrase not in tail:
            problems.append("the nothing-to-check record does not say %r" % phrase)
    if "That rule is for **no finding**" not in record:
        problems.append("the recording paragraph does not keep including-zero for no finding")
    return problems


def gate_problems(text):
    line = paragraph_from(section(text, GATE_HEADING) or "", GATE_LINE)
    if not line:
        return ["the gate's how-state line is missing"]
    if "no finding, nothing to check, or could not measure" not in line:
        return ["the gate's how-state line does not list nothing to check among the outcomes"]
    return []


def success_problems(text):
    lines = text.split("\n")
    if REDO_LINE not in lines:
        return ["the redo success line is missing"]
    i = lines.index(REDO_LINE) + 1
    criterion = flat(" ".join(lines[i:i + 2]))
    if "unsettled entities named, zero recorded, or nothing to check stated" not in criterion:
        return ["the how-state success criterion does not state nothing to check"]
    return []


EMPTY_POPULATION_CHECKS = (
    four_outcome_problems, zero_population_problems, precondition_problems,
    recording_problems, gate_problems, success_problems,
)


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


class ItHasFourOutcomesAndNeverBlocks(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_D)
        self.body = flat(section(self.text, AUDIT_HEADING))

    def test_four_outcomes(self):
        for outcome in OUTCOMES:
            self.assertIn(outcome, self.body, "the audit must state the %s outcome" % outcome)
        self.assertEqual(four_outcome_problems(self.text), [])

    def test_no_finding_requires_every_entity_checked(self):
        self.assertIn(
            '(INV-163) Never report "no finding" unless N equals M', self.body,
            "'no finding' must require every entity to have been checked — a response that "
            "never arrived rendered as a clean result is what INV-163 forbids",
        )
        self.assertIn("Never collapse a partial run into \"no finding\" (INV-163)", self.body)

    def test_it_cites_bootcamper_facing_invariants_only(self):
        """INV-308 binds the repo's verification tooling, not a Bootcamper's guide."""
        self.assertNotIn(
            "INV-308", self.body,
            "the how-state audit cites INV-308, which governs the repository's own "
            "verification tooling; the Bootcamper-facing rule for a result that never "
            "arrived is INV-163",
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
        self.assertIn(
            'including zero: write "0 unsettled" rather than omitting the section', self.body,
            "#154's DEFERRED INVARIANT block, resolved as INV-334, quotes this rule verbatim",
        )

    def test_flagged_record_counts_are_marked_unconfirmed(self):
        self.assertIn("unconfirmed by the engine's construction history", self.body)


class TheSuccessCriterionSitsBesideTheRedoLine(unittest.TestCase):
    def test_it_names_nothing_to_check(self):
        self.assertEqual(success_problems(read(PHASE_D)), [])

    def test_new_line_follows_the_unchanged_redo_line(self):
        lines = read(PHASE_D).split("\n")
        self.assertIn(REDO_LINE, lines, "the 'Redo queue drained' line must stay as it is")
        after = lines[lines.index(REDO_LINE) + 1]
        self.assertTrue(
            after.startswith("- ✅ How-state audit run"),
            "the how-state success criterion must sit directly after the redo line; found %r"
            % after,
        )


class AnEmptyPopulationIsNothingToCheck(unittest.TestCase):
    """Issue #232: M = 0 is its own outcome, reached only after the export is proven read."""

    def setUp(self):
        self.text = read(PHASE_D)

    def test_the_real_text_passes_every_check(self):
        for check in EMPTY_POPULATION_CHECKS:
            with self.subTest(check=check.__name__):
                self.assertEqual(check(self.text), [])

    def test_the_bullets_are_found(self):
        """Anti-vacuity (INV-265): every check above reads a bullet or paragraph that exists."""
        audit = section(self.text, AUDIT_HEADING)
        self.assertEqual(
            sorted(outcome_bullets(audit)),
            sorted(o.strip("*") for o in OUTCOMES),
        )
        self.assertTrue(paragraph_from(audit, RECORD_IT))
        self.assertTrue(paragraph_from(section(self.text, GATE_HEADING), GATE_LINE))

    def test_the_quoted_rules_survive(self):
        """#154's DEFERRED INVARIANT block, resolved as INV-334, quotes these three verbatim."""
        body = flat(section(self.text, AUDIT_HEADING))
        for rule in ('Never report "no finding" unless N equals M',
                     "The outcome never blocks", INCLUDING_ZERO):
            self.assertIn(rule, body)


def _mutate(test, text, old, new):
    test.assertIn(old, text, "negative control is stale: %r is no longer in the file" % old)
    return text.replace(old, new, 1)


class EmptyPopulationNegativeControls(unittest.TestCase):
    """Each check reports a problem on the wording it replaced, or with its clause removed."""

    def setUp(self):
        self.text = read(PHASE_D)
        self.ntc = outcome_bullets(section(self.text, AUDIT_HEADING))[NOTHING_TO_CHECK]

    def test_the_pre_232_zero_case(self):
        """#154's wording: the 0-of-0 case inside No finding, and three outcomes."""
        text = _mutate(self, self.text, self.ntc + "\n", "")
        text = _mutate(
            self, text,
            "response never arrived is not an entity with nothing to report.\n",
            "response never arrived is not an entity with nothing to report. With no "
            "multi-record\n  entities at all, report \"checked 0 of 0\" and \"no finding\": "
            "nothing was there to check.\n",
        )
        text = _mutate(self, text, "**Four outcomes", "**Three outcomes")
        self.assertTrue(four_outcome_problems(text))
        self.assertTrue(zero_population_problems(text))
        self.assertTrue(precondition_problems(text))

    def test_no_inv_265_on_the_zero_case(self):
        text = _mutate(self, self.text, "(INV-265) With M = 0", "With M = 0")
        self.assertTrue(zero_population_problems(text))

    def test_without_the_entity_condition(self):
        text = _mutate(self, self.text, "**at least one entity**", "entities")
        self.assertTrue(precondition_problems(text))

    def test_without_the_record_sum_condition(self):
        text = _mutate(self, self.text, "**equal the total", "**match the")
        self.assertTrue(precondition_problems(text))

    def test_without_could_not_measure_naming_the_condition(self):
        text = _mutate(self, self.text, ", naming which condition failed", "")
        self.assertTrue(precondition_problems(text))

    def test_with_zero_unsettled_written_for_nothing_to_check(self):
        text = _mutate(self, self.text, '**omit the "0 unsettled" line**',
                       'write "0 unsettled"')
        self.assertTrue(recording_problems(text))

    def test_without_the_nothing_to_check_record(self):
        text = _mutate(self, self.text, "For **nothing to check**, still write the", "Still write the")
        self.assertTrue(recording_problems(text))

    def test_gate_line_with_three_outcomes(self):
        text = _mutate(self, self.text, "no finding, nothing to check, or could not measure",
                       "no finding, or could not measure")
        self.assertTrue(gate_problems(text))

    def test_the_pre_232_success_criterion(self):
        text = _mutate(
            self, self.text,
            "unsettled entities named, zero recorded, or\n  nothing to check stated,",
            "unsettled entities named, or zero recorded,\n ",
        )
        self.assertTrue(success_problems(text))


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
