"""Module 7 step 4e exports the results for the systems named in Module 1 (#487).

Module 1 Step 10a asks which software the results must interface with and holds the answer as
`integration_targets` (INV-097), and until #487 no module read it to shape an export. A real
Bootcamper loaded the bootcamp's output into a graph database and got "bubbles without any network
and relationship", with the business attributes missing, and had to leave the bootcamp to get a
working file.

Step 4e, a closing step of the Discover phase in `phase2b-discover.md`, is where that answer is
acted on. These tests pin what the step states:

1. **The offer**, driven by `integration_targets`, one system per turn, before Module 7's single
   transition question and never in the same turn as it.
2. **The no-target path**: say so, offer once, and produce nothing unless a system is named.
3. **The unknown-format path**: say so, ask for the format or its documentation, write nothing.
4. **The one-row key check** before the reader is written, with what to do when
   `RELATED_ENTITIES` is absent.
5. **The `get_record` pass** for business attributes, with the live route that re-verifies it.
6. **The count report** (entities, edges, nodes carrying the asked-for attributes) and **the
   zero-edge failure**.
7. **The Senzing side from the MCP server at the step**, the program in the chosen language under
   `src/query/`, and every Discover exit routed through the step.
8. **Module 1 Step 10a** names Module 7 outside its pinned question, which stays verbatim
   (INV-056); no shipped step is named "Enrichment"; and **no target's import schema ships in the
   plugin**.

⛔ Negative control for (1): move the transition question back into step 4d and
`test_the_transition_question_is_asked_after_the_offers_not_in_step_4d` fails.

These assert that the skill files STATE the rules; they cannot establish that a live run follows
them. Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
M7 = SKILLS / "module-07-query-visualize-discover"
PHASE1 = M7 / "phase1-query-visualize.md"
PHASE2 = M7 / "phase2-discover.md"
PHASE2B = M7 / "phase2b-discover.md"
M7_SKILL = M7 / "SKILL.md"
M1_PHASE2 = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

STEP_4D = "### Step 4d: Relationship network exploration"
STEP_4E = "### Step 4e: Export for the systems named in Module 1"
COMPLETION = "### Discover phase completion"

OFFER = "👉 **Would you like me to export your resolved results in [system]'s import format?**"
NO_TARGET_OFFER = (
    "👉 **Is there a system you'd like your resolved results exported for? If so, name it.**")
UNKNOWN_FORMAT = (
    "👉 **I don't know [system]'s import format well enough to write it without guessing. "
    "Could you share the format, or a link to its documentation?**")
ATTRIBUTES = (
    "👉 **Which fields from your source records should each node carry (for example, amounts "
    "or account roles)? Reply \"none\" if the entities and relationships are enough.**")
TRANSITION = "👉 **Would you like to continue to module completion now?**"
M1_INTEGRATION_QUESTION = (
    "👉 **Will your entity-resolution results need to interface with other software (CRM, "
    "search engine, data warehouse, API gateway, downstream app)?**")


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    """Whitespace-collapsed, so an assertion survives a re-wrap of the paragraph."""
    return re.sub(r"\s+", " ", text)


def between(text, start, end):
    """The text from ``start`` up to (not including) ``end``."""
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def step_4e():
    return between(read(PHASE2B), STEP_4E, COMPLETION)


def step_4d():
    return between(read(PHASE2B), STEP_4D, STEP_4E)


def item(section, number):
    """Numbered item ``number`` of ``section``, up to the next top-level numbered item."""
    m = re.search(r"^%d\. " % number, section, re.M)
    if not m:
        raise AssertionError("item %d is missing from step 4e" % number)
    nxt = re.search(r"^(%d)\. |^\*\*Transition\.\*\*" % (number + 1), section[m.end():], re.M)
    return section[m.start():m.end() + nxt.start()] if nxt else section[m.start():]


class TheScanIsNotVacuous(unittest.TestCase):
    def test_every_file_and_anchor_exists(self):
        for path in (PHASE1, PHASE2, PHASE2B, M7_SKILL, M1_PHASE2, GRADUATION):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path.relative_to(REPO))
        text = read(PHASE2B)
        for anchor in (STEP_4D, STEP_4E, COMPLETION):
            with self.subTest(anchor=anchor):
                self.assertEqual(1, text.count(anchor), "retarget this test: %r" % anchor)

    def test_step_4e_sits_after_step_4d_and_before_discover_completion(self):
        text = read(PHASE2B)
        self.assertLess(text.index(STEP_4D), text.index(STEP_4E))
        self.assertLess(text.index(STEP_4E), text.index(COMPLETION))

    def test_the_item_parser_finds_all_ten_items(self):
        section = step_4e()
        for n in range(1, 11):
            with self.subTest(item=n):
                self.assertTrue(item(section, n).startswith("%d. " % n))


class TheOffer(unittest.TestCase):
    """(1) Driven by `integration_targets`, one system per turn."""

    def setUp(self):
        self.section = step_4e()
        self.flat = flat(self.section)

    def test_it_reads_integration_targets_from_the_preferences_file(self):
        first = flat(item(self.section, 1))
        self.assertIn("`integration_targets`", first)
        self.assertIn("`config/bootcamp_preferences.yaml`", first)
        self.assertIn("INV-097", self.flat, "the step must cite the invariant that persists it")

    def test_the_offer_is_pinned_once_and_one_system_per_turn(self):
        self.assertEqual(1, read(PHASE2B).count(OFFER))
        offer = flat(item(self.section, 3))
        self.assertIn(OFFER, offer)
        self.assertRegex(offer, r"one system per turn|in a turn of its own")
        self.assertIn("INV-251", offer)

    def test_each_offer_ends_the_turn(self):
        after = self.section[self.section.index(OFFER):]
        self.assertRegex(flat(after[:400]), r"\*\(Internal: end the turn on this question and wait\.\)\*")

    def test_a_declined_offer_moves_to_the_next_system(self):
        self.assertRegex(flat(item(self.section, 3)),
                         r"\*\*No:\*\* record .*\"declined\".* next system")

    def test_it_runs_on_every_path_and_reads_the_loaded_data(self):
        self.assertIn("It runs on every path", self.flat)
        self.assertIn("reads the loaded data, not Discover's findings", self.flat)

    def test_it_never_loads_the_target_and_needs_no_vendor_tooling(self):
        self.assertIn("does not load the export into the target system", self.flat)
        self.assertIn("no vendor's tooling is a prerequisite", self.flat)


class TheNoTargetPath(unittest.TestCase):
    """(2) Say so, offer once, and produce nothing unless a system is named."""

    def setUp(self):
        self.item = flat(item(step_4e(), 2))

    def test_it_says_no_system_was_named_before_offering(self):
        self.assertIn("didn't name a system", self.item)
        self.assertLess(self.item.index("didn't name a system"), self.item.index(NO_TARGET_OFFER))

    def test_it_offers_once(self):
        self.assertIn(NO_TARGET_OFFER, self.item)
        self.assertIn("offer once (INV-006)", self.item)
        self.assertEqual(1, read(PHASE2B).count(NO_TARGET_OFFER))

    def test_anything_but_a_named_system_produces_nothing(self):
        self.assertIn("Any reply that does not name a system ends the step with nothing produced",
                      self.item)
        self.assertIn('"reason": "no_target"', self.item)


class TheUnknownFormatPath(unittest.TestCase):
    """(3) The format comes from the AI's knowledge or the Bootcamper; nothing is invented."""

    def setUp(self):
        self.item = flat(item(step_4e(), 4))

    def test_the_format_comes_from_the_ais_own_knowledge(self):
        self.assertIn("From your own knowledge of the system", self.item)

    def test_an_unknown_format_is_said_and_asked_for(self):
        self.assertIn("When you cannot name the format confidently, say so and ask for it",
                      self.item)
        self.assertIn(UNKNOWN_FORMAT, self.item)

    def test_nothing_is_written_until_it_arrives_and_nothing_is_invented(self):
        self.assertIn("write nothing until it arrives, and never invent one", self.item)
        self.assertIn('"reason": "format_unknown"', self.item)


class TheOneRowKeyCheck(unittest.TestCase):
    """(4) One row is dumped and its top-level keys read before the reader is written."""

    def setUp(self):
        self.section = step_4e()
        self.item = flat(item(self.section, 7))

    def test_one_row_is_dumped_and_its_keys_read_before_the_reader(self):
        self.assertIn("Check one export row before writing the reader", self.item)
        self.assertIn("fetches one row, prints its top-level keys", self.item)
        self.assertIn("INV-115", self.item)

    def test_the_check_precedes_the_program_that_writes_the_export(self):
        self.assertLess(self.section.index("Check one export row before writing the reader"),
                        self.section.index("Write and run the export program"))

    def test_it_says_what_to_do_when_related_entities_is_absent(self):
        self.assertRegex(self.item, r"`RELATED_ENTITIES` is absent:\*\* the flags did not ask "
                                    r"for relationships")
        self.assertIn("add them, and dump again", self.item)
        self.assertIn("zero-edge failure", self.item)


class TheGetRecordPass(unittest.TestCase):
    """(5) Business attributes need a per-record `get_record` pass, re-verified live."""

    def setUp(self):
        self.item = flat(item(step_4e(), 7))

    def test_the_pass_is_stated_with_its_reason(self):
        self.assertIn("Business attributes need a per-record `get_record` pass", self.item)
        self.assertIn("`SZ_ENTITY_INCLUDE_RECORD_JSON_DATA`", self.item)
        self.assertIn("`JSON_DATA`", self.item)

    def test_it_names_the_live_route_that_re_verifies_it(self):
        self.assertIn(
            "get_sdk_reference(topic='flags', filter='SZ_ENTITY_INCLUDE_RECORD_JSON_DATA')",
            self.item)
        self.assertRegex(self.item, r"server 1\.\d+\.\d+ \(\d{4}-\d{2}-\d{2}\)",
                         "the carried fact must say which server and date it was read from")

    def test_the_dumped_row_stays_the_authority(self):
        self.assertIn("the dumped row is the authority", self.item)


class TheCountReport(unittest.TestCase):
    """(6) Three counts from the written files; zero edges is a failure."""

    def setUp(self):
        self.item = flat(item(step_4e(), 9))

    def test_the_three_counts_are_reported(self):
        for count in ("**entity count**", "**edge count**", "**attribute count**"):
            with self.subTest(count=count):
                self.assertIn(count, self.item)
        self.assertIn("Report all three", self.item)

    def test_they_are_counted_from_the_written_files(self):
        self.assertIn("Count from the written files, never from the exit status", self.item)
        self.assertIn("INV-129", self.item)

    def test_zero_edges_is_a_failure_not_a_finished_export(self):
        self.assertIn("A zero edge count is a failure, never a finished export", self.item)
        self.assertIn("do not hand the file over as finished", self.item)
        self.assertIn("give item 7's result", self.item)
        self.assertIn('"reason": "zero_edges"', self.item)

    def test_missing_attributes_name_the_get_record_pass(self):
        self.assertIn("report the attribute count as zero", self.item)
        self.assertIn("`get_record` pass as the first cause to check", self.item)

    def test_the_file_is_handed_over_only_with_edges(self):
        self.assertIn("When the edge count is above zero", flat(item(step_4e(), 10)))


class TheSenzingSideAndTheProgram(unittest.TestCase):
    """(7) MCP at the step, relationships as edges, chosen language, `src/query/`."""

    def setUp(self):
        self.section = step_4e()
        self.flat = flat(self.section)

    def test_the_senzing_side_comes_from_the_two_reporting_guide_topics(self):
        six = flat(item(self.section, 6))
        self.assertIn("reporting_guide(topic='graph', language='<chosen_language>')", six)
        self.assertIn("reporting_guide(topic='data_mart', language='<chosen_language>'", six)
        self.assertIn("INV-080", six)
        self.assertIn("never from this file or from memory", six)

    def test_edges_are_relationships_with_match_type_and_key_never_features(self):
        six = flat(item(self.section, 6))
        self.assertIn("Edges are Senzing relationships, each carrying its match type and match "
                      "key; never write an edge per shared feature", six)

    def test_the_program_is_in_the_chosen_language_under_src_query(self):
        eight = flat(item(self.section, 8))
        self.assertIn("`programming_language`", eight)
        self.assertIn("INV-002", eight)
        self.assertIn("under `src/query/`", eight)

    def test_graduation_already_copies_src_query(self):
        self.assertRegex(read(GRADUATION),
                         r"\|\s*`src/query/\*\*`\s*\|\s*`production/src/query/`\s*\|",
                         "step 4e relies on graduation's existing src/query copy")

    def test_the_step_checkpoints_under_module_7_query(self):
        self.assertIn("**Checkpoint:** write step 4e under `module_7_query.steps.4e`", self.section)
        self.assertIn('Also set top-level `current_step` to `"4e"`', self.section)

    def test_the_full_checkpoint_example_carries_step_4e(self):
        text = read(PHASE2B)
        start = text.index("The full checkpoint structure")
        block = text[start:]
        body = block[block.index("```json") + len("```json"):]
        body = body[:body.index("```")]
        steps = json.loads(body)["module_7_query"]["steps"]
        self.assertIn("4e", steps)
        self.assertEqual("src/query/", steps["4e"]["targets"][0]["program"][:len("src/query/")])


class TheTransitionQuestion(unittest.TestCase):
    """(1) The offers come before Module 7's single transition question, never with it."""

    def test_the_transition_question_is_asked_after_the_offers_not_in_step_4d(self):
        text = read(PHASE2B)
        self.assertEqual(1, text.count(TRANSITION), "the transition question has one place")
        self.assertNotIn(TRANSITION, step_4d(),
                         "asked in step 4d it precedes the export offers it must follow")
        section = step_4e()
        self.assertIn(TRANSITION, section)
        self.assertLess(section.index(OFFER), section.index(TRANSITION))

    def test_step_4d_hands_on_to_step_4e(self):
        d = flat(step_4d())
        self.assertIn("continue to step 4e below", d)

    def test_the_transition_is_its_own_turn(self):
        section = step_4e()
        tail = flat(section[section.index("**Transition.**"):])
        self.assertIn("never merged with an offer above (INV-251)", tail)


class EveryDiscoverExitReachesStep4e(unittest.TestCase):
    """(7) A declined or shortened Discover phase still gets the offer."""

    def test_the_decline_and_both_early_exits_run_step_4e(self):
        text = flat(read(PHASE2))
        self.assertIn("**Declines:** write `discover_phase: \"skipped\"` to "
                      "`config/bootcamp_progress.json` under `module_7_query`, run step 4e", text)
        self.assertEqual(2, text.count(
            "write `discover_phase: \"skipped\"` to `config/bootcamp_progress.json`, run step 4e"),
            "both early exits (after 4b and after 4c) must run step 4e")

    def test_no_exit_returns_to_the_gate_without_step_4e(self):
        text = flat(read(PHASE2))
        self.assertNotRegex(
            text, r"\"skipped\"` to `config/bootcamp_progress\.json`(?: under `module_7_query`)? "
                  r"and return to `phase1-query-visualize\.md`")

    def test_phase1_and_the_skill_route_to_step_4e(self):
        self.assertIn("step 4e (export for the systems named in Module 1)", flat(read(PHASE1)))
        self.assertIn("step 4e, the export for the systems named in Module 1", flat(read(M7_SKILL)))


class ModuleOneNamesModuleSeven(unittest.TestCase):
    """(8) Step 10a names Module 7 outside its pinned question, which stays verbatim."""

    def setUp(self):
        text = read(M1_PHASE2)
        self.step = flat(between(text, "## 10a. Software integration and deployment target",
                                 "## 11. Create the problem statement document"))

    def test_the_pinned_question_is_unchanged(self):
        self.assertIn(M1_INTEGRATION_QUESTION, self.step)

    def test_module_7_is_named_before_the_question_and_outside_it(self):
        named = self.step.index("Module 7's step 4e")
        self.assertLess(named, self.step.index(M1_INTEGRATION_QUESTION))
        self.assertNotIn("Module 7", M1_INTEGRATION_QUESTION)
        self.assertIn("`../module-07-query-visualize-discover/phase2b-discover.md`", self.step)


def shipped_text_files():
    for path in sorted(PLUGIN.rglob("*")):
        if path.is_file() and path.suffix in (".md", ".py", ".json", ".yaml", ".yml", ".txt"):
            yield path


class NothingShipsThatShouldNot(unittest.TestCase):
    """(8) No step named "Enrichment", and no target's import schema."""

    #: A step heading or step reference whose name is "Enrichment".
    ENRICHMENT_STEP = re.compile(
        r"(?im)^#{1,6}\s+(?:step\s+\w+[:.]?\s*|\d+[a-z]?\.\s*)enrichment\b"
        r"|\bstep\s+\w+\s*[:—-]\s*enrichment\b|\benrichment step\b")

    #: Import syntax of graph and tabular targets. A hit means a target's schema shipped.
    TARGET_SCHEMA = re.compile(
        r"(?i)LOAD CSV|:START_ID|:END_ID|:ID\(|neo4j-admin|\bMERGE \(|\bCREATE \(\w*:|"
        r"<graphml|<gexf|\bCOPY \w+ FROM\b")

    def test_the_scan_reaches_the_plugin(self):
        files = list(shipped_text_files())
        self.assertGreater(len(files), 50)
        self.assertIn(PHASE2B, files)

    def test_no_shipped_step_is_named_enrichment(self):
        hits = []
        for path in shipped_text_files():
            for m in self.ENRICHMENT_STEP.finditer(read(path)):
                hits.append("%s: %r" % (path.relative_to(REPO), m.group(0)))
        self.assertEqual([], hits)

    def test_the_enrichment_pattern_catches_a_step_heading(self):
        self.assertRegex("### Step 4f: Enrichment", self.ENRICHMENT_STEP)
        self.assertRegex("run the enrichment step next", self.ENRICHMENT_STEP)
        self.assertNotRegex("- **Needs enrichment:** Data is missing", self.ENRICHMENT_STEP)

    def test_no_target_import_schema_is_hardcoded(self):
        hits = []
        for path in shipped_text_files():
            for m in self.TARGET_SCHEMA.finditer(read(path)):
                hits.append("%s: %r" % (path.relative_to(REPO), m.group(0)))
        self.assertEqual([], hits)

    def test_the_schema_pattern_catches_a_shipped_header(self):
        self.assertRegex("entityId:ID(Entity),name", self.TARGET_SCHEMA)
        self.assertRegex(":START_ID,:END_ID,matchKey", self.TARGET_SCHEMA)
        self.assertRegex("LOAD CSV WITH HEADERS FROM 'file:///nodes.csv'", self.TARGET_SCHEMA)

    def test_step_4e_ships_no_template(self):
        section = step_4e()
        self.assertNotIn("```", section, "a fenced block in step 4e is a template to copy")
        self.assertIn("No target's import format ships in this plugin", section)


if __name__ == "__main__":
    unittest.main()
