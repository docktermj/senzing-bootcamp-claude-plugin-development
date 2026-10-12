"""One resolved own-data entity is shown as text, by one procedure, at three places.

#486 (part of #465) moves the bootcamp's peak from the Truth Set to the Bootcamper's own data.
Three places now show one resolved entity from their data as text:

1. **The midpoint entity**, at the end of Module 6 step 9, once the redo queue reports empty: the
   entity with the most records, ties broken by the lowest ``ENTITY_ID``, text only, no
   visualization and no 👉.
2. **The headline entity**, at the end of Module 7 step 1, once the requirements are settled and
   never before the open question (#478) is answered: the entity with the most data sources,
   ties broken by the most records, then by the lowest ``ENTITY_ID``.
3. **The headline block** that opens Module 7's recap section: its records, its data sources and
   why they resolved together, written whether or not the visualization ran.

How the entity is retrieved (generated SDK code, never SQL), what is shown, and what happens when
no entity has two or more records is stated **once**, in `ground-rules.md` → "Showing one
resolved entity as text" (INV-300). The three sites cite it and carry only their own selection
rule and placement. Every selection rule ends on the lowest ``ENTITY_ID`` (grafted from the
losing race approach): the export's row order is not a tie-break, and step 1, its checkpoint and
the recap block re-run at Module 7's close must all name the same entity. These checks pin both halves: the owner carries the procedure in full, and
each pointer names it, cites INV-300 and INV-355, and carries no second copy of the procedure's
own phrases.
The Module 6 midpoint and the recap block also cite INV-355 on their selection rule's own line,
since each states that clause of the invariant beside its pointer (#519).
⚠️ That last check is narrower than INV-300's "no second copy": it can only see the procedure's
distinctive phrases reappearing, not a paraphrase.

The checks are pure functions over a passage's text, so each also runs on a mutated copy as its
negative control.

**At every pointer, derived** (`pointer_citation_problems`, #519): every shipped sentence that
points at "Showing one resolved entity as text", found by scan rather than from the three sites
above (INV-246), cites INV-355. The scan, not a list, is what found that Module 7 step 1's pointer
cited INV-300 alone while its ⛔ bullet below carried INV-355.

⚠️ **What the derived scan cannot see** (`tests/_pointer_sites.py` says how it reads): a pointer
that names the section in other words, with neither the quoted name nor the
`ground-rules.md#entity-as-text` anchor; a pointer outside `plugins/` or outside Markdown; the
owner's own cross-references inside `ground-rules.md` (its "Worked steers" item 5 mention among
them), which are excluded; whether INV-355 is the right invariant for what the sentence says; and
a sentence cut early at an abbreviation.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line by
construction, and counting lines that *start* with `👉 **` keeps prose that mentions the marker
("no 👉 of its own") from being counted as a question. Phrase checks collapse whitespace, so they
match across a wrap.

⛔ **What this cannot establish:** that a live guide shows the right entity, or retrieves it with
SDK code. Those are properties of a run; `dry-run` phase 3 and `auto-test`'s transcript linter
observe them. This pins that the skill files STATE them. INV-355 names this file as its enforcer;
passing it is no evidence that a live run obeys it.

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #486; the citation at every pointer, #519.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

import _pointer_sites

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
MODULE_6_B = SKILLS / "module-06-data-processing" / "phaseB-load-first-source.md"
MODULE_7 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
CONTRACT = SKILLS / "module-03b-truthset-visualization" / "visualization-api-reference.md"
RECAP_EXAMPLE = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"
GENERATOR = PLUGIN / "scripts" / "generate_recap_pdf.py"

OWNER_HEADING = "## Showing one resolved entity as text"
OWNER_ANCHOR = '<a id="entity-as-text"></a>'
OWNER_LINK = "ground-rules.md#entity-as-text"
#: The section every pointer names, its anchor, and the invariant each pointer cites (#519).
SECTION, ANCHOR, INVARIANT = "Showing one resolved entity as text", "entity-as-text", "INV-355"
#: The citation each pointer carries: the single statement (INV-300) and the rule (INV-355).
POINTER_CITATION = "(INV-300, INV-355)"

#: Phrases only the procedure may carry. A pointer that repeats one has begun a second copy.
PROCEDURE_ONLY = (
    "export_json_entity_report",
    "get_entity_by_entity_id",
    "response_schemas",
    "single-record entity",
    "and N more",
)

OPEN_QUESTION = "👉 **What do you want to find out about your data?**"

#: The non-deterministic tie-break the race's winner first shipped. Export row order is not a rule.
EXPORT_ORDER_TIE = "first of the tied entities the export returned"


def flat(text):
    """Whitespace collapsed, so a phrase matches across a line wrap."""
    return " ".join(text.split())


def section(text, start, end_markers):
    """Text from ``start`` up to the first of ``end_markers`` after it ('' when absent)."""
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i:]
    cut = [rest.find(m, len(start)) for m in end_markers]
    cut = [c for c in cut if c > 0]
    return rest[:min(cut)] if cut else rest


def questions(text):
    """The 👉 question lines (see the module docstring for why lines)."""
    return [line.strip() for line in text.splitlines() if line.strip().startswith("👉 **")]


def owner(text):
    return section(text, OWNER_HEADING, ("\n## ",))


def owner_problems(text):
    """The canonical statement: declared, cited, and carrying the whole procedure."""
    body = owner(text)
    if not body:
        return ["%r is missing from ground-rules.md" % OWNER_HEADING]
    problems = []
    if OWNER_ANCHOR not in text[:text.find(OWNER_HEADING)][-200:]:
        problems.append("the %s anchor does not sit directly above the heading" % OWNER_ANCHOR)
    f = flat(body)
    required = {
        "the owner declaration": "This is the canonical statement",
        "the INV-300 citation": "(INV-300)",
        "retrieval by generated SDK code": "Retrieve it with generated SDK code, never SQL",
        "the export route": "reporting_guide(topic='export'",
        "the multi-record export flag lookup": "filter='export_json_entity_report'",
        "the per-source record summary": "per-source record summary",
        "the fetch by entity ID": "filter='get_entity_by_entity_id'",
        "the response-shape lookup": "topic='response_schemas'",
        "INV-115": "(INV-115)",
        "text, never a visualization": "never a visualization",
        "the records": "one line per record",
        "the data sources": "its data sources",
        "why they resolved together": "why they resolved together",
        "INV-340's boundary": "(INV-340)",
        "the statement rule": "It is a statement with no 👉",
        "INV-225": "(INV-225)",
        "the no-multi-record case": "No entity has two or more records",
        "show no entity": "show no entity",
        "never a single-record substitute": "Never show a single-record entity in its place",
        "never invented": "never make one up",
        "the recap block's no-entity wording": "In the recap's headline block, that one line is the block",
        "the failure case": "The program fails",
        "the deterministic final tie-break": "Every caller's rule ends on the lowest entity ID",
        "the same entity on a re-run": "a re-run over the same data names the same entity",
    }
    for what, phrase in required.items():
        if phrase not in f:
            problems.append("the procedure lacks %s (%r)" % (what, phrase))
    for anchor in ("#midpoint-entity", "#headline-entity", "#headline-block"):
        if anchor not in body:
            problems.append("the procedure does not name the site %s" % anchor)
    if EXPORT_ORDER_TIE in f:
        problems.append("the procedure breaks ties by export row order (%r)" % EXPORT_ORDER_TIE)
    if questions(body):
        problems.append("the procedure carries a 👉 question: %r" % questions(body))
    return problems


def pointer_problems(passage, rule_phrases, name):
    """A citing site: names the owner, cites INV-300 and INV-355, has its own rule and no copy."""
    if not passage:
        return ["%s is missing" % name]
    problems = []
    f = flat(passage)
    if OWNER_LINK not in passage:
        problems.append("%s does not link %s" % (name, OWNER_LINK))
    if POINTER_CITATION not in f:
        problems.append("%s does not cite INV-300 and INV-355 %s" % (name, POINTER_CITATION))
    if "stated once" not in f:
        problems.append("%s does not say the procedure is stated once" % name)
    for phrase in rule_phrases:
        if phrase not in f:
            problems.append("%s lacks its own rule %r" % (name, phrase))
    for phrase in PROCEDURE_ONLY:
        if phrase in f:
            problems.append("%s restates the procedure (%r)" % (name, phrase))
    if questions(passage):
        problems.append("%s carries a 👉 question: %r" % (name, questions(passage)))
    return problems


def step_9(text):
    return section(text, "## 9. Process redo records", ("\n## 10.",))


#: Step 9's checkpoint, which since #507 goes on to record `midpoint_record` (pinned by
#: `test_predictions_before_results.py`), so only its opening is matched here.
STEP_9_CHECKPOINT = "**Checkpoint:** write step 9 ("


def midpoint(text):
    return section(step_9(text), '<a id="midpoint-entity"></a>', ("**Checkpoint:**",))


def midpoint_problems(text):
    step = step_9(text)
    passage = midpoint(text)
    problems = pointer_problems(
        passage,
        ("the entity with the most records, ties broken by the lowest `ENTITY_ID`** (INV-355)",
         "from the first source",
         "Text only, with no visualization", "No 👉", "does not end the turn (INV-225)",
         "shows no midpoint entity"),
        "Module 6 step 9's midpoint entity")
    if passage:
        if step.find("Processing the redo queue now") > step.find(passage):
            problems.append("the midpoint entity comes before the redo queue is drained")
        if "reports empty" not in flat(passage):
            problems.append("the midpoint entity is not placed after the queue reports empty")
        if step.find(passage) > step.find(STEP_9_CHECKPOINT):
            problems.append("the midpoint entity is not at the end of step 9")
    return problems


def step_1(text):
    return section(text, "## 1. Define query requirements", ("\n## ",))


def headline(text):
    return section(step_1(text), '<a id="headline-entity"></a>', ("**Checkpoint:**",))


def headline_problems(text):
    step = step_1(text)
    passage = headline(text)
    problems = pointer_problems(
        passage,
        ("the entity with the most data sources, ties broken by the most records, then by "
         "the lowest `ENTITY_ID`",
         "all name the same entity",
         "On a single-source run every entity has one data source, so the most records "
         "decides, then the lowest `ENTITY_ID`",
         "Never before the open question is answered", "never in the gate's turn",
         "No 👉 of its own", "(INV-225, INV-251)", "module_7_query.headline_entity"),
        "Module 7 step 1's headline entity")
    if passage:
        at = step.find(passage)
        for earlier in (OPEN_QUESTION, '<a id="requirements-gate"></a>',
                        "### After the answer, fallback path",
                        '### When the answer is "I don\'t know"'):
            pos = step.find(earlier)
            if pos < 0 or pos > at:
                problems.append("the headline entity does not come after %r" % earlier)
        if step.find("**Checkpoint:** write step 1") < at:
            problems.append("the headline entity is not at the end of step 1")
    return problems


def completion(text):
    return section(text, "## Module completion", ("\n## ",))


def recap_block(text):
    return section(completion(text), '<a id="headline-block"></a>',
                   ("**The Module 7 recap section records every quality iteration.**",))


def recap_block_problems(text):
    return pointer_problems(
        recap_block(text),
        ("The Module 7 recap section opens with the headline block",
         "at the top of `### Information Shared`", "**Headline entity:**",
         "its records, its data sources, and why they resolved together",
         "step 1's selection rule (most data sources, then most records, then the lowest "
         "`ENTITY_ID`; INV-355)", "Written whether or not the visualization ran",
         "Screenshots keep the app's tab order"),
        "Module 7's recap headline block")


def pointer_citation_problems(texts):
    """Every derived pointer to the procedure cites INV-355 in its own sentence (#519)."""
    return _pointer_sites.uncited_pointers(texts, SECTION, ANCHOR, INVARIANT)


def load_generator():
    spec = importlib.util.spec_from_file_location("recap_gen_headline_under_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recap_gen_headline_under_test"] = module
    spec.loader.exec_module(module)
    return module


def tab_slugs_in_order():
    """Screenshot slugs from the contract's tab table, in row order, REMOVED rows dropped."""
    slugs = []
    for line in CONTRACT.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[4].startswith("`") and "REMOVED" not in cells[0]:
            slugs.append(cells[4].strip("`"))
    return slugs


class TheProcedureIsStatedOnce(unittest.TestCase):
    TEXT = GROUND_RULES.read_text(encoding="utf-8")

    def test_the_owner_carries_the_whole_procedure(self):
        self.assertEqual([], owner_problems(self.TEXT))

    def test_the_owner_sits_beside_the_no_sql_rule(self):
        """It enforces that rule, so it follows it, and every module already reads this file."""
        self.assertLess(self.TEXT.find("## No direct SQL against the Senzing database"),
                        self.TEXT.find(OWNER_HEADING))
        self.assertEqual(1, self.TEXT.count(OWNER_HEADING))

    def test_control_a_missing_rule_is_reported(self):
        for phrase in ("never make one up", "(INV-300)", "filter='export_json_entity_report'"):
            mutated = self.TEXT.replace(phrase, "XX")
            self.assertTrue(owner_problems(mutated), phrase)

    def test_control_an_export_order_tie_break_is_reported(self):
        """The race winner's first text broke ties by export row order; that must not return."""
        mutated = self.TEXT.replace(
            "Every\n     caller's rule ends on the lowest entity ID",
            "A tie the\n     rule leaves open goes to the " + EXPORT_ORDER_TIE)
        self.assertNotEqual(mutated, self.TEXT)
        problems = owner_problems(mutated)
        self.assertTrue(any("export row order" in p for p in problems), problems)

    def test_control_a_question_in_the_procedure_is_reported(self):
        mutated = self.TEXT.replace("5. **The program fails.**",
                                    "👉 **Shall I show it?**\n\n5. **The program fails.**")
        self.assertTrue(any("👉" in p for p in owner_problems(mutated)))


class TheMidpointEntity(unittest.TestCase):
    TEXT = MODULE_6_B.read_text(encoding="utf-8")

    def test_it_is_placed_and_cited(self):
        self.assertEqual([], midpoint_problems(self.TEXT))

    def test_control_a_dropped_final_tie_break_is_reported(self):
        mutated = self.TEXT.replace("the most records, ties broken by the lowest `ENTITY_ID`",
                                    "the most records")
        self.assertNotEqual(mutated, self.TEXT)
        self.assertTrue(midpoint_problems(mutated))

    def test_control_a_restated_procedure_is_reported(self):
        mutated = self.TEXT.replace(
            "**Text only, with no visualization.**",
            "Never show a single-record entity in its place. **Text only, with no visualization.**")
        self.assertTrue(any("restates" in p for p in midpoint_problems(mutated)))

    def test_control_a_question_is_reported(self):
        mutated = self.TEXT.replace(STEP_9_CHECKPOINT,
                                    "👉 **Want to see another?**\n\n" + STEP_9_CHECKPOINT)
        self.assertNotEqual(mutated, self.TEXT)
        self.assertTrue(midpoint_problems(mutated))

    def test_control_moved_before_the_drain_is_reported(self):
        passage = midpoint(self.TEXT)
        removed = self.TEXT.replace(passage, "")
        mutated = removed.replace("## 9. Process redo records\n",
                                  "## 9. Process redo records\n\n" + passage)
        self.assertTrue(midpoint_problems(mutated))


class TheHeadlineEntity(unittest.TestCase):
    TEXT = MODULE_7.read_text(encoding="utf-8")

    def test_it_is_placed_and_cited(self):
        self.assertEqual([], headline_problems(self.TEXT))

    def test_control_moved_before_the_open_question_is_reported(self):
        passage = headline(self.TEXT)
        removed = self.TEXT.replace(passage, "")
        mutated = removed.replace("### Turn 1: the open question (both paths)\n",
                                  passage + "### Turn 1: the open question (both paths)\n")
        self.assertTrue(headline_problems(mutated))

    def test_control_a_changed_selection_rule_is_reported(self):
        mutated = self.TEXT.replace("ties broken by the most records", "ties broken by name")
        self.assertTrue(headline_problems(mutated))

    def test_control_a_dropped_final_tie_break_is_reported(self):
        """Without the lowest-ID rule, step 1 and the recap block may name different entities."""
        mutated = re.sub(r"ties broken by the most records, then by the\s+lowest `ENTITY_ID`",
                         "ties broken by the most records", self.TEXT)
        self.assertNotEqual(mutated, self.TEXT)
        self.assertTrue(headline_problems(mutated))

    def test_step_1_still_asks_the_open_question_once(self):
        """#478's order is untouched: the open question is still step 1's first 👉."""
        qs = questions(step_1(self.TEXT))
        self.assertEqual(OPEN_QUESTION, qs[0])
        self.assertEqual(1, step_1(self.TEXT).count(OPEN_QUESTION))


class TheRecapHeadlineBlock(unittest.TestCase):
    TEXT = MODULE_7.read_text(encoding="utf-8")

    def test_it_is_placed_and_cited(self):
        self.assertEqual([], recap_block_problems(self.TEXT))

    def test_control_a_dropped_final_tie_break_is_reported(self):
        mutated = re.sub(r"then most records, then the\s+lowest `ENTITY_ID`",
                         "then most records", self.TEXT)
        self.assertNotEqual(mutated, self.TEXT)
        self.assertTrue(recap_block_problems(mutated))

    def test_control_a_dropped_decline_clause_is_reported(self):
        mutated = self.TEXT.replace("Written whether or not the visualization ran", "XX")
        self.assertTrue(recap_block_problems(mutated))

    def test_information_shared_is_the_first_section_the_pdf_renders(self):
        """Why the block sits inside "Information Shared": the PDF renders the four named
        subsections first, so any other subsection would not lead in the PDF."""
        gen = load_generator()
        self.assertEqual("Information Shared", gen.REQUIRED_SECTIONS[0])


class EveryPointerCitesTheRule(unittest.TestCase):
    """The pointer sites are derived by scan (INV-246), so a later one without INV-355 fails."""

    def test_every_pointer_cites_inv_355(self):
        self.assertEqual([], pointer_citation_problems(_pointer_sites.shipped_texts()))

    def test_the_scan_finds_the_three_sites(self):
        """Not vacuous: the derived set holds the midpoint, the headline and the recap block."""
        found = [path for path, _, _ in _pointer_sites.pointers(
            _pointer_sites.shipped_texts(), SECTION, ANCHOR)]
        self.assertGreaterEqual(found.count(MODULE_6_B), 1)
        self.assertGreaterEqual(found.count(MODULE_7), 2)

    def test_control_each_derived_pointer_loses_its_citation(self):
        """Every shipped pointer (three since #519), in turn, is reported when it drops INV-355."""
        shipped = _pointer_sites.shipped_texts()
        sites = _pointer_sites.pointers(shipped, SECTION, ANCHOR)
        self.assertGreaterEqual(len(sites), 3, "the scan went blind")
        for path, line, _ in sites:
            with self.subTest(site="%s:%d" % (path.name, line)):
                problems = pointer_citation_problems(
                    _pointer_sites.without_citation(shipped, path, line, INVARIANT))
                where = "%s:%d" % (path.relative_to(REPO_ROOT).as_posix(), line)
                self.assertTrue(any(where in p for p in problems), problems)

    def test_control_a_new_pointer_site_without_the_citation(self):
        """A site no list names: the scan finds it by the section's name, wrapped (INV-346)."""
        texts = _pointer_sites.shipped_texts()
        texts[SKILLS / "graduation" / "new-step.md"] = (
            "How it is shown is stated once in `ground-rules.md` → \"Showing one resolved\n"
            "entity as text\" (INV-300); follow it there rather than restating it.\n")
        self.assertTrue(any("graduation/new-step.md:1" in p
                            for p in pointer_citation_problems(texts)))

    def test_control_a_new_pointer_by_anchor_only(self):
        texts = {SKILLS / "graduation" / "new-step.md":
                 "Show it as [the ground rules say](../bootcamp-onboarding/ground-rules.md"
                 "#entity-as-text) (INV-300).\n"}
        self.assertTrue(pointer_citation_problems(texts))

    def test_control_a_site_without_inv_355_fails_its_site_check(self):
        """Each site's own check needs INV-355 at the pointer and, where it states the selection
        rule beside the pointer, on that rule too."""
        recap_pointer = ('as text" (INV-300, INV-355); follow it there rather than restating '
                         'it.\n\n- **Written')
        for problems_of, path, old, needle in (
                (midpoint_problems, MODULE_6_B, 'as text" (INV-300, INV-355)',
                 "does not cite INV-300 and INV-355"),
                (midpoint_problems, MODULE_6_B, "`ENTITY_ID`** (INV-355)",
                 "lacks its own rule"),
                (headline_problems, MODULE_7,
                 'as text" (INV-300, INV-355); follow it there rather than restating it.\n\n'
                 '- ⛔',
                 "does not cite INV-300 and INV-355"),
                (recap_block_problems, MODULE_7, recap_pointer,
                 "does not cite INV-300 and INV-355"),
                (recap_block_problems, MODULE_7, "`ENTITY_ID`; INV-355)", "lacks its own rule")):
            with self.subTest(old=old):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(1, text.count(old))
                cut = (old.replace(", INV-355", "").replace(" (INV-355)", "")
                       .replace("; INV-355", ""))
                problems = problems_of(text.replace(old, cut))
                self.assertTrue(any(needle in p for p in problems), problems)


class TheExampleRecapModelsIt(unittest.TestCase):
    TEXT = RECAP_EXAMPLE.read_text(encoding="utf-8")

    def module_7(self):
        gen = load_generator()
        recap = gen.parse_recap(self.TEXT)
        found = [m for m in recap.modules if m.title.startswith("Query, Visualize and Discover")]
        self.assertEqual(1, len(found))
        return found[0]

    def test_module_7_opens_with_the_headline_block(self):
        lines = [l for l in self.module_7().subsection("Information Shared") if l.strip()]
        self.assertTrue(lines[0].startswith("**Headline entity:**"), lines[0])
        block = "\n".join(lines[:lines.index("**Also shared:**")])
        self.assertIn("2 data sources", block)
        self.assertIn("**Why they resolved together:**", block)

    def test_module_7_screenshots_keep_the_tab_order(self):
        section_text = section(self.TEXT, "## Query, Visualize and Discover", ("\n## ",))
        found = re.findall(r"results_visualization-([a-z-]+)\.png\)", section_text)
        order = tab_slugs_in_order()
        self.assertEqual(6, len(order))
        self.assertEqual([s for s in order if s in found], found)
        self.assertLess(section_text.find("**Headline entity:**"),
                        section_text.find("![", ))

    def test_the_truth_set_section_no_longer_calls_itself_the_wow_moment(self):
        truth = section(self.TEXT, "## Truth Set visualization", ("\n## ",))
        self.assertNotIn("wow moment", truth.lower())
        self.assertIn("practice data, built to contain matches", truth)


if __name__ == "__main__":
    unittest.main()
