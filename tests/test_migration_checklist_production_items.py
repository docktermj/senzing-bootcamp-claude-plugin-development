"""The migration checklist carries its production-database item, and both revised items
reach the generated file (#904).

Graduation Step 4 writes ``production/MIGRATION_CHECKLIST.md`` from
``plugins/senzing-bootcamp/skills/graduation/SKILL.md``. Two of its items are written there
as quoted text that the guide copies into the file:

* **Database:** SQLite is an evaluation and starter database; move to a supported production
  database before deploying, with PostgreSQL named as Senzing's documented recommendation
  (*"For anything beyond evaluation, use PostgreSQL"*, ``search_docs(query='SQLite evaluation
  PostgreSQL production database recommendation')``, recorded in
  ``test_prescribed_search_queries.py``). A starter
  still on SQLite is not ready to deploy unchanged. The item must not say SQLite cannot run in
  production: the documentation recommends, and the checklist says no more than that.
* **Performance:** the DEFAULT-flags item, whose qualification
  ``test_checklist_items_ship_their_exceptions.py`` guards in detail.

The checklist is written by the guide, not by a script, so there is no generator to run.
``render_checklist`` builds the representative file the way Step 4 says to: the six sections
in order, the top note, and each "MUST carry" item's quoted text as one ``- [ ]`` line under
its section. The tests read the rendered file as well as the source, so an item whose words
sit outside the quote, or under the wrong section, fails here even when the source still
contains them.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRADUATION = REPO / "plugins" / "senzing-bootcamp" / "skills" / "graduation" / "SKILL.md"

SECTIONS = ("Database", "Security", "Licensing", "Performance", "Data", "Deployment")

#: The Step 4 bullet that defines the checklist, up to the next top-level bullet or prose.
CHECKLIST_LEAD = "- **`production/MIGRATION_CHECKLIST.md`:**"

#: One "MUST carry" sub-bullet: its section and its quoted item.
MUST_CARRY = re.compile(
    r"^  - \*\*The (\w+) section MUST carry the [^*]+ item\*\* — ⚠️ \*\"(.+?)\"\*",
    re.M | re.S,
)

TOP_NOTE = ("⚠️ Some production topics (performance, security, monitoring, deployment) are "
            "not covered in depth during the bootcamp: complete these items before deploying.")


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def checklist_block(text):
    start = text.index(CHECKLIST_LEAD)
    end = text.find("\n\n", start)
    return text[start: end if end != -1 else len(text)]


def must_carry_items(text):
    """{section: quoted item} for every "MUST carry" sub-bullet of the checklist bullet."""
    return {m.group(1): flat(m.group(2)) for m in MUST_CARRY.finditer(checklist_block(text))}


def render_checklist(text):
    """A representative ``production/MIGRATION_CHECKLIST.md`` built from the source."""
    items = must_carry_items(text)
    lines = ["# Migration checklist", "", TOP_NOTE]
    for section in SECTIONS:
        lines += ["", f"## {section}", ""]
        if section in items:
            lines.append(f"- [ ] ⚠️ {items[section]}")
    return "\n".join(lines) + "\n"


def section_of(rendered, name):
    m = re.search(rf"^## {name}\n(.*?)(?=^## |\Z)", rendered, re.M | re.S)
    return m.group(1) if m else ""


def database_problems(text):
    """Every way the Database item fails #904, as readable strings."""
    item = must_carry_items(text).get("Database")
    if item is None:
        return ["the checklist has no Database 'MUST carry' item"]
    problems = []
    required = {
        "SQLite as an evaluation and starter database": r"(?i)SQLite is an evaluation and "
                                                         r"starter database",
        "the move before deploying": r"(?i)before deploying, move to a supported production "
                                     r"database",
        "PostgreSQL as the documented recommendation": r"(?i)recommends PostgreSQL",
        "the starter not ready unchanged": r"(?i)SQLite, this starter is not ready to deploy "
                                           r"unchanged",
    }
    for what, pattern in required.items():
        if not re.search(pattern, item):
            problems.append(f"the Database item does not state {what}")
    if re.search(r"(?i)SQLite (?:cannot|can't|must not|is not supported|is unsupported)|"
                 r"not (?:supported|capable) (?:in|for) production", item):
        problems.append("the Database item says SQLite cannot be used in production")
    return problems


class TheDatabaseItem(unittest.TestCase):
    def setUp(self):
        self.text = GRADUATION.read_text(encoding="utf-8")

    def test_the_item_is_complete(self):
        self.assertEqual([], database_problems(self.text))

    def test_it_ships_whatever_the_database_type(self):
        """A PostgreSQL project confirms the item; it is not left out for one."""
        self.assertIn("Ship it whatever `database_type` is", checklist_block(self.text))

    def test_graduation_changes_no_template(self):
        """The item asks for a migration; Step 4 performs none (out of scope for #904)."""
        self.assertIn("graduation changes no template and migrates no data",
                      flat(checklist_block(self.text)))

    def test_the_guidance_carries_the_documented_wording(self):
        block = flat(checklist_block(self.text))
        self.assertIn("For anything beyond evaluation, use PostgreSQL", block)
        self.assertIn("search_docs(query='SQLite evaluation PostgreSQL production database "
                      "recommendation')", block)


class TheGeneratedChecklist(unittest.TestCase):
    def setUp(self):
        self.text = GRADUATION.read_text(encoding="utf-8")
        self.rendered = render_checklist(self.text)

    def test_every_section_is_present_in_order(self):
        found = re.findall(r"^## (\w+)$", self.rendered, re.M)
        self.assertEqual(list(SECTIONS), found)

    def test_both_revised_items_are_present(self):
        self.assertEqual({"Database", "Performance"}, set(must_carry_items(self.text)))

    def test_the_database_section_carries_the_production_database_item(self):
        section = section_of(self.rendered, "Database")
        self.assertRegex(section, r"(?m)^- \[ \] ⚠️ SQLite is an evaluation and starter database")
        self.assertIn("PostgreSQL", section)
        self.assertIn("not ready to deploy unchanged", section)

    def test_the_performance_section_carries_the_qualified_flags_item(self):
        section = section_of(self.rendered, "Performance")
        self.assertRegex(section, r"(?m)^- \[ \] ⚠️ Replace `\*_DEFAULT_FLAGS`")
        for phrase in ("including the export call", "RELATED_ENTITIES",
                       "every field and relationship your code reads",
                       "leave this item unchecked"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)
        self.assertNotIn("except the export call", section)

    def test_each_item_is_one_checkbox(self):
        """The qualification lives on the box it qualifies, not on a line after it."""
        for name in ("Database", "Performance"):
            with self.subTest(section=name):
                lines = [ln for ln in section_of(self.rendered, name).splitlines() if ln]
                self.assertEqual(1, len(lines), lines)
                self.assertTrue(lines[0].startswith("- [ ] "))


class TheGuardCatchesEachRegression(unittest.TestCase):
    """Negative controls: each mutation of the shipped text must be reported."""

    def setUp(self):
        self.text = GRADUATION.read_text(encoding="utf-8")

    def mutate(self, old, new):
        self.assertIn(old, self.text, "the control's anchor is gone; re-anchor it")
        return self.text.replace(old, new, 1)

    def test_a_missing_database_item_is_reported(self):
        start = self.text.index("  - **The Database section MUST carry")
        end = self.text.index("  - **The Performance section MUST carry")
        problems = database_problems(self.text[:start] + self.text[end:])
        self.assertEqual(["the checklist has no Database 'MUST carry' item"], problems)

    def test_a_missing_postgresql_recommendation_is_reported(self):
        text = self.mutate("Senzing's documentation recommends PostgreSQL for anything beyond "
                           "evaluation.", "Pick a production database.")
        self.assertTrue(any("PostgreSQL" in p for p in database_problems(text)))

    def test_a_missing_not_ready_clause_is_reported(self):
        text = self.mutate("this starter is not ready to deploy", "this starter is ready to deploy")
        self.assertTrue(any("not ready" in p for p in database_problems(text)))

    def test_calling_sqlite_unusable_is_reported(self):
        text = self.mutate("SQLite is an\n    evaluation and starter database:",
                           "SQLite is an\n    evaluation and starter database and SQLite cannot "
                           "run in production:")
        self.assertTrue(any("cannot be used" in p for p in database_problems(text)))

    def test_a_qualification_outside_the_quote_leaves_the_rendered_box(self):
        """The rendered file loses what the source keeps beside the quote."""
        old = ("Until you have, keep the\n    current flags and leave this item unchecked.\"*")
        text = self.mutate(old, "\"*\n    Until you have, keep the current flags and leave this "
                                "item unchecked.")
        self.assertIn("leave this item unchecked", text)
        self.assertNotIn("leave this item unchecked",
                         section_of(render_checklist(text), "Performance"))


if __name__ == "__main__":
    unittest.main()
