"""Module 7 closes the Module 1 question: step 1 saves it, the document answers it, the gate checks.

The two-act analysis found Module 7's climax "staged as a demonstration that never closes the
Module 1 question": the discoveries document never walked back to what the Bootcamper set out
to learn, and step 1's checkpoint recorded only the step, so by the Query Completeness Gate
(possibly a later session, or after step 3b's return through Modules 5 and 6) there was no list
to check against. #480 closes the loop in three places:

1. **Step 1's checkpoint** saves the settled list as `module_7_query.query_requirements`, each
   entry with its `text` and its Module 1 `source` ("Bootcamper's answer" for their own
   questions). An empty list is `[]`; step 3b never changes it.
2. **The data-discoveries deliverable** gains `## Your question, answered` as its FIRST section,
   a table with the columns *Requirement*, *Answer* and *Where in this document*, whose *Answer*
   cell is a finding, "not answered, because <reason>" or "not fully answered, because <reason>".
   `REQUIRED_SECTIONS` in the generator carries it, so a document without it is warned about.
3. **The Query Completeness Gate** gains an item: every saved requirement appears in the section
   exactly once, or the guide adds the row and re-renders the PDF. It asks nothing and never
   blocks.

The checks are pure functions over the shipped text, so each one also runs on a mutated copy as
its negative control.

⛔ **What this cannot establish:** that a live guide saves the list, writes the rows, or runs the
gate item. Those are properties of a conversation; only `dry-run` phase 3 observes them. This pins
that the skill file STATES them, and that the generator warns when the section is missing. INV-353
names this file as its enforcer; passing it is no evidence that a live run saves the list or writes
faithful rows.

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #480 (part of #465).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE_7 = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
GENERATOR = PLUGIN / "scripts" / "generate_discoveries_pdf.py"

KEY = "module_7_query.query_requirements"
SECTION = "## Your question, answered"
NEXT_SECTION = "## Headline numbers, interpreted"
#: The new section is stated ahead of the six numbered findings sections, so their numbering
#: (and the ⛔ rule on the sixth) is untouched.
FIRST = "**(INV-353) First, `%s`**" % SECTION
FINDINGS_START = "1. **`%s`**" % NEXT_SECTION


def load_generator():
    spec = importlib.util.spec_from_file_location("discoveries_480_under_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: @dataclass resolves its module out of sys.modules.
    sys.modules["discoveries_480_under_test"] = module
    spec.loader.exec_module(module)
    return module


def section(text, start, end_markers):
    """Text from ``start`` up to the first of ``end_markers`` after it ('' when absent)."""
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i:]
    cut = [rest.find(m, len(start)) for m in end_markers]
    cut = [c for c in cut if c > 0]
    return rest[:min(cut)] if cut else rest


def squash(text):
    return re.sub(r"\s+", " ", text)


def step_1(text):
    return section(text, "## 1. Define query requirements", ("\n## ",))


def deliverable(text):
    return section(text, "## Data-discoveries deliverable", ("\n## ",))


def gate(text):
    return section(text, "## Query Completeness Gate", ("\n## ",))


def checkpoint_problems(text):
    """Step 1's checkpoint saves the settled list, with text and source per entry."""
    step = step_1(text)
    at = step.find("**Checkpoint:** write step 1")
    saved = step.find(KEY)
    if at < 0:
        return ["step 1 has no checkpoint"]
    if saved < at:
        return ["step 1's checkpoint does not save %s" % KEY]
    passage = squash(step[at:])
    problems = []
    for what, phrase in {
        "each entry has its text and its Module 1 source": "each with its `text` and its "
                                                           "Module 1 `source`",
        "their own questions are sourced to their answer": "`\"Bootcamper's answer\"`",
        "a derived requirement names its criterion or output": "A derived requirement names "
                                                               "the success criterion or "
                                                               "desired output it was derived "
                                                               "from",
        "an empty list is saved as []": "`\"query_requirements\": []`",
        "step 3b leaves it unchanged": "Step 3b's quality iteration and its return through "
                                       "Modules 5 and 6 leave it as it is",
        "the gate checks the section against it": "The Query Completeness Gate checks the "
                                                  "discoveries document's `## Your question, "
                                                  "answered` section against this list",
    }.items():
        if phrase not in passage:
            problems.append("step 1's checkpoint does not state that %s" % what)
    blocks = re.findall(r"```json\n(.*?)```", step[at:], re.S)
    if not blocks:
        problems.append("step 1's checkpoint shows no JSON example of the saved list")
    else:
        try:
            entries = json.loads(blocks[0])["module_7_query"]["query_requirements"]
        except (ValueError, KeyError, TypeError) as error:
            problems.append("the checkpoint's JSON example does not parse to %s: %s"
                            % (KEY, error))
        else:
            if not entries or any(set(e) != {"text", "source"} for e in entries):
                problems.append("each example entry must carry exactly `text` and `source`")
    return problems


def deliverable_problems(text):
    """The section is first, its table shape is stated, and its edge cases are covered."""
    part = deliverable(text)
    if not part:
        return ["the data-discoveries deliverable is missing"]
    problems = []
    first, second = part.find(FIRST), part.find(FINDINGS_START)
    if first < 0 or second < 0 or first > second:
        problems.append("%r is not listed first, before %r" % (SECTION, NEXT_SECTION))
    flat = squash(part)
    for what, phrase in {
        "there are seven sections": "Write these seven sections, in this order; the generator "
                                    "checks for them by name",
        "the rows come from the saved list": "one row per entry in `%s`" % KEY,
        "the table's header row": "| Requirement | Answer | Where in this document |",
        "an unanswered requirement says why": "`not answered, because <reason>`",
        "a partial answer says why": "`not fully answered, because <reason>`",
        "an empty list writes one line": "No query requirements were confirmed in Module 7 "
                                         "step 1.",
        "no saved list falls back to the conversation": "write the rows from the requirements "
                                                        "in the conversation, or else from "
                                                        "`docs/business_problem.md`",
        "later questions are optional rows": "the gate below does not require it",
        "the Latin-script rule covers it": "The rule covers `## Your question, answered` too",
    }.items():
        if phrase not in flat:
            problems.append("the deliverable does not state that %s" % what)
    return problems


def gate_problems(text):
    """The gate item: exactly once, re-render on a miss, edge cases, no 👉, never blocks."""
    part = gate(text)
    if not part:
        return ["the Query Completeness Gate is missing"]
    problems = []
    item = section(part, "5. **Their question answered?**", ("\n6. ",))
    if not item:
        return ["the gate has no 'Their question answered?' item before 'Ready to proceed?'"]
    if "6. **Ready to proceed?**" not in part:
        problems.append("'Ready to proceed?' is not the gate's last item")
    flat = squash(item)
    for what, phrase in {
        "every saved requirement appears exactly once": "Every requirement in `%s` appears in "
                                                        "the discoveries document's `%s` "
                                                        "section exactly once"
                                                        % (KEY, SECTION),
        "a missing row is added and the PDF re-rendered": "add its row (and remove a "
                                                          "duplicate), then re-render the PDF",
        "an empty list passes on its one line": "An empty saved list** passes",
        "no saved list checks presence only": "check only that the section exists",
        "later rows are not required": "allowed and not required",
        "it adds no question": "adds no 👉 (INV-251)",
        "it never blocks": "never blocks the gate or graduation",
    }.items():
        if phrase not in flat:
            problems.append("the gate item does not state that %s" % what)
    if any(line.strip().startswith("👉 **") for line in part.splitlines()):
        problems.append("the gate asks a 👉 question")
    return problems


class Base(unittest.TestCase):
    def setUp(self):
        self.text = MODULE_7.read_text(encoding="utf-8")


class TheInputsAreReal(Base):
    """INV-265: every check below reads these; a silent miss would pass vacuously."""

    def test_the_three_passages_were_located(self):
        for name, part in (("step 1", step_1(self.text)), ("deliverable", deliverable(self.text)),
                           ("gate", gate(self.text))):
            with self.subTest(name):
                self.assertTrue(part.strip(), "%s not found" % name)


class StepOneSavesTheList(Base):
    def test_the_checkpoint_saves_the_requirements(self):
        self.assertEqual(checkpoint_problems(self.text), [])

    def test_negative_control_checkpoint_without_the_key(self):
        broken = self.text.replace(KEY, "module_7_query.something_else")
        self.assertTrue(checkpoint_problems(broken))

    def test_negative_control_entry_without_a_source(self):
        broken = self.text.replace(', "source": "Bootcamper\'s answer"}', "}", 1)
        self.assertTrue(any("exactly `text` and `source`" in p
                            for p in checkpoint_problems(broken)))


class TheDocumentAnswersItFirst(Base):
    def test_the_section_is_first_and_its_shape_is_stated(self):
        self.assertEqual(deliverable_problems(self.text), [])

    def test_negative_control_section_moved_after_the_findings(self):
        broken = self.text.replace(FIRST, "**Last, it**", 1).replace(
            "6. **`## What was not found, and why`**",
            "6. **`## What was not found, and why`**\n" + FIRST, 1)
        self.assertTrue(any("is not listed first" in p for p in deliverable_problems(broken)))

    def test_negative_control_partial_answer_dropped(self):
        broken = self.text.replace("`not fully answered, because <reason>`", "partly", 1)
        self.assertTrue(any("partial answer" in p for p in deliverable_problems(broken)))


class TheGateChecksIt(Base):
    def test_the_gate_item_is_stated(self):
        self.assertEqual(gate_problems(self.text), [])

    def test_negative_control_gate_item_removed(self):
        broken = self.text.replace("5. **Their question answered?**", "5. **Something else?**")
        self.assertTrue(gate_problems(broken))

    def test_negative_control_gate_asks_a_question(self):
        broken = self.text.replace("6. **Ready to proceed?**",
                                   "👉 **Shall I fix the table?**\n6. **Ready to proceed?**", 1)
        self.assertTrue(any("asks a 👉" in p for p in gate_problems(broken)))


class TheGeneratorWarnsWithoutIt(unittest.TestCase):
    """A document without the section still renders, with the usual missing-section warning."""

    DOC = """# Data Discoveries

## Headline numbers, interpreted

- Loaded 10 records and resolved 9 of them into distinct resolved entities today

## What was not found, and why

Low overlap between the two sources explains the small cross-source merge count.
"""

    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_required_sections_lead_with_the_section(self):
        self.assertEqual(self.generator.REQUIRED_SECTIONS[0], "your question answered")
        self.assertEqual(len(self.generator.REQUIRED_SECTIONS), 7)

    def test_the_heading_as_written_matches(self):
        self.assertIn("your question answered",
                      self.generator._normalize("Your question, answered"))

    def test_a_document_without_it_is_warned_about_and_still_renders(self):
        doc = self.generator.parse_discoveries(self.DOC)
        audit = self.generator.audit_discoveries(doc, self.DOC)
        self.assertTrue(audit.ok, audit.fatal)
        self.assertIn("your question answered", audit.missing_sections)
        self.assertTrue(any("missing sections" in w and "your question answered" in w
                            for w in audit.warnings), audit.warnings)

    def test_negative_control_a_document_with_it_is_not_warned_about_it(self):
        text = self.DOC.replace(
            "## Headline numbers",
            "## Your question, answered\n\n| Requirement | Answer | Where in this document |\n"
            "|---|---|---|\n| Who is in both? | 4 entities | Merges and match keys |\n\n"
            "## Headline numbers", 1)
        audit = self.generator.audit_discoveries(self.generator.parse_discoveries(text), text)
        self.assertNotIn("your question answered", audit.missing_sections)


if __name__ == "__main__":
    unittest.main()
