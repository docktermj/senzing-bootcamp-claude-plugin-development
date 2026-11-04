"""The journey map has one pinned shape, a Module | Status table with a count line (#852).

The journey map's content was specified (INV-029: the selected modules, marked ✅/🔄/⬜) but its
shape was not, so each guide improvised one. At Truth Set visualization's start one rendered it
as a single arrow-separated line, and the Bootcamper found it hard to scan and asked for a table
showing how far through the bootcamp they were.

`ground-rules.md` → "Module start banners and transitions" now states the shape once (INV-300): a
two-column Markdown table headed **Module | Status**, one row per `selected_modules` entry in
order and by name (INV-079), each Status cell the marker plus its word, and one count line under
it, "N of M modules done". Every verbosity preset, `minimal` included, shows the full table and
the count line, and INV-214's allowance to compress a list of names to a count does not apply.
Graduation's item 1 and Truth Set visualization's mid-module refresh point there and carry no
copy of the shape.

`.claude/skills/auto-test/transcript_lint.py`'s `journey map` pattern also recognizes the table:
two consecutive table rows that each carry a marker. A table header alone, or a module table with
Required/Optional status and no marker, as Bootcamp preparation's Step 2 may render its module
list, is not a map and raises no BREAKING `INV-075-apparatus-in-exempt-phase`.

⛔ Each check here is a pure function of the text, so the negative controls run the SAME check on
a mutated copy (INV-265): the clause removed, each element removed, a module number written into
the count line, a copy of the shape pasted into a pointing site. The checks read the text through
`tests/_wrapped_text.py` (INV-346), so a re-wrap neither hides nor fails a clause.

These assert that the skill files STATE the shape and that the linter RECOGNIZES it; they cannot
establish that a live guide renders the table, which only `dry-run` phase 3 observes. Stdlib
only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import io
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

from _wrapped_text import collapsed_items

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"
TRUTHSET_REFRESH = SKILLS / "module-03b-truthset-visualization" / "phase1-visualization.md"

sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / "auto-test"))

import transcript_lint  # noqa: E402

SECTION = "## Module start banners and transitions\n"
#: Where the shape clause starts inside the module-start bullet.
CLAUSE_LEAD = "**The journey map's shape: this is the canonical statement (INV-300).**"

#: Each element the clause must state, by what it is, with the pattern that finds it.
ELEMENTS = (
    ("the INV-300 canonical claim",
     re.compile(r"journey map's shape: this is the canonical statement \(INV-300\)")),
    ("the Module | Status table", re.compile(r"two-column Markdown table headed \*\*Module \| Status\*\*")),
    ("one row per selected_modules entry, in order, by name",
     re.compile(r"one row per entry in `selected_modules`, in that order and by name \(INV-079\)")),
    ("Bootcamp preparation and Bootcamp graduation as rows",
     re.compile(r"Bootcamp preparation and Bootcamp graduation included")),
    ("the marker plus its word",
     re.compile(r"`✅ done`, `🔄 you are here` or `⬜ upcoming`")),
    ("the count line", re.compile(r"Directly under the table, show one count line, "
                                  r"\*\*\"N of M modules done\"\*\*")),
    ("what M and N count", re.compile(r"M is the number of rows and N the number of ✅ rows")),
    ("the full table under every preset",
     re.compile(r"every verbosity preset, `minimal` included, shows the full table plus the "
                r"count line")),
    ("INV-214's compression does not apply",
     re.compile(r"INV-214's allowance to compress a list of names to a count does not apply")),
)

#: A module number, which INV-079 keeps out of the table and the count line.
MODULE_NUMBER = re.compile(r"\bModule \d")

#: How a pointing site names the owner, and the phrases only the owner may carry.
POINTER = re.compile(r"`\.\./bootcamp-onboarding/ground-rules\.md` → \"Module start banners and "
                     r"transitions\" states once \(INV-300\)")
SHAPE_COPY = re.compile(r"Module \| Status|modules done|`✅ done`|you are here")


def read(path):
    return path.read_text(encoding="utf-8")


def section(text):
    start = text.index(SECTION)
    end = text.find("\n## ", start + len(SECTION))
    return text[start:] if end == -1 else text[start:end]


def clause(text):
    """The shape clause, collapsed: from its lead to the end of its list item, or None."""
    for flat, _origin in collapsed_items(section(text)):
        if CLAUSE_LEAD in flat:
            return flat[flat.index(CLAUSE_LEAD):]
    return None


def clause_problems(text):
    """What the ground-rules clause fails to state, as a list of messages."""
    found = clause(text)
    if found is None:
        return ["ground-rules.md → \"Module start banners and transitions\" no longer states "
                "the journey map's shape (#852)"]
    problems = [f"the journey map's shape clause does not state {what} (#852)"
                for what, pattern in ELEMENTS if not pattern.search(found)]
    if MODULE_NUMBER.search(found):
        problems.append("the journey map's shape clause shows a module number (INV-079)")
    return problems


def pointer_problems(text, name):
    """A pointing site must name the owner and carry no copy of the shape."""
    items = [flat for flat, _origin in collapsed_items(text) if "Journey map" in flat]
    if not items:
        return [f"{name} no longer has its journey map item"]
    problems = []
    if not any(POINTER.search(flat) for flat in items):
        problems.append(f"{name}'s journey map does not point at ground-rules for its shape")
    for flat in items:
        copy = SHAPE_COPY.search(flat)
        if copy:
            problems.append(f"{name}'s journey map carries a copy of the shape: {copy.group(0)!r}")
    return problems


class GroundRulesStatesTheShape(unittest.TestCase):
    def setUp(self):
        self.text = read(GROUND_RULES)

    def test_the_clause_states_every_element(self):
        self.assertEqual([], clause_problems(self.text))

    def test_a_rewrapped_clause_still_passes(self):
        rewrapped = self.text.replace("headed **Module | Status**, with", "headed\n  **Module |"
                                      " Status**, with")
        self.assertNotEqual(self.text, rewrapped)
        self.assertEqual([], clause_problems(rewrapped))


class GroundRulesNegativeControls(unittest.TestCase):
    def setUp(self):
        self.text = read(GROUND_RULES)
        self.found = clause(self.text)
        self.assertIsNotNone(self.found)

    def test_the_clause_removed(self):
        lines = self.text.split("\n")
        start = next(i for i, line in enumerate(lines) if CLAUSE_LEAD in line)
        end = next(i for i in range(start, len(lines)) if lines[i].startswith("- "))
        cut = "\n".join(lines[:start] + lines[end:])
        self.assertEqual(["ground-rules.md → \"Module start banners and transitions\" no longer "
                          "states the journey map's shape (#852)"], clause_problems(cut))

    def test_each_element_removed(self):
        for what, pattern in ELEMENTS[1:]:
            with self.subTest(element=what):
                flat = section(self.text)
                for raw, _origin in collapsed_items(flat):
                    if CLAUSE_LEAD in raw:
                        broken = pattern.sub("", raw)
                        break
                mutated = SECTION + "- " + broken + "\n"
                self.assertIn(f"the journey map's shape clause does not state {what} (#852)",
                              clause_problems(mutated))

    def test_a_module_number_in_the_count_line(self):
        mutated = self.text.replace('**"N of M modules done"**',
                                    '**"N of M modules done (Module 3 next)"**')
        self.assertNotEqual(self.text, mutated)
        self.assertIn("the journey map's shape clause shows a module number (INV-079)",
                      clause_problems(mutated))


class PointingSitesCarryNoCopy(unittest.TestCase):
    SITES = ((GRADUATION, "graduation"), (TRUTHSET_REFRESH, "Truth Set visualization"))

    def test_each_site_points_and_carries_no_copy(self):
        for path, name in self.SITES:
            with self.subTest(site=name):
                self.assertEqual([], pointer_problems(read(path), name))

    def test_a_site_without_its_pointer(self):
        for path, name in self.SITES:
            with self.subTest(site=name):
                text = read(path).replace("states once (INV-300)", "is described")
                self.assertIn(f"{name}'s journey map does not point at ground-rules for its "
                              "shape", pointer_problems(text, name))

    def test_a_site_with_a_pasted_copy(self):
        for path, name in self.SITES:
            with self.subTest(site=name):
                text = read(path).replace("states once (INV-300), with",
                                          "states once (INV-300), a **Module | Status** table, with")
                self.assertEqual([f"{name}'s journey map carries a copy of the shape: "
                                  "'Module | Status'"], pointer_problems(text, name))

    def test_no_other_shipped_file_carries_the_shape(self):
        """A scan, not a list (INV-246): the shape lives in ground-rules.md alone."""
        copies = [str(path.relative_to(REPO_ROOT)) for path in sorted(PLUGIN.rglob("*.md"))
                  if path != GROUND_RULES and SHAPE_COPY.search(read(path))]
        self.assertEqual([], copies)


#: The shape the clause pins, as a guide renders it at graduation.
TABLE = ("| Module | Status |\n|---|---|\n| Bootcamp preparation | ✅ done |\n"
         "| Data processing | ✅ done |\n| Bootcamp graduation | 🔄 you are here |\n\n"
         "2 of 3 modules done")
HEADER_ONLY = "| Module | Status |"
REQUIRED_OPTIONAL = ("| Module | Status |\n|---|---|\n| Bootcamp preparation | Required |\n"
                     "| Entity Resolution Concepts | Optional |\n| SDK setup | Required |")


class TheLinterRecognizesTheTable(unittest.TestCase):
    PATTERN = transcript_lint.APPARATUS["journey map"]

    def test_the_table_is_a_journey_map(self):
        self.assertTrue(self.PATTERN.search(TABLE))
        missing = [f["message"] for f in transcript_lint.check_apparatus([TABLE], "content")]
        self.assertNotIn("content module showed no journey map", missing)

    def test_the_table_is_a_selftest_rendering(self):
        tables = [sample for name, sample in transcript_lint._APPARATUS_RENDERINGS
                  if name == "journey map" and sample.lstrip().startswith("|")]
        self.assertTrue(tables, "no table-form journey map is in _APPARATUS_RENDERINGS")

    def test_the_list_and_heading_forms_still_match(self):
        for sample in ("**Your journey**", "✅ Bootcamp preparation\n🔄 **SDK setup**\n⬜ System "
                       "verification", "Here is your journey map."):
            with self.subTest(sample=sample[:30]):
                self.assertTrue(self.PATTERN.search(sample))

    def test_one_marked_row_is_not_a_map(self):
        self.assertIsNone(self.PATTERN.search("| SDK | ✅ installed |\n| Data | not yet |"))

    def test_no_marker_table_raises_no_exempt_phase_breach(self):
        for sample in (HEADER_ONLY, REQUIRED_OPTIONAL):
            self.assertIsNone(self.PATTERN.search(sample))
            for phase in ("preparation", "module0"):
                with self.subTest(sample=sample[:30], phase=phase):
                    codes = [f["code"] for f in transcript_lint.check_apparatus([sample], phase)]
                    self.assertNotIn("INV-075-apparatus-in-exempt-phase", codes)
            self.assertIn(sample, transcript_lint._EXEMPT_PHASE_TEXT)

    def test_the_table_in_an_exempt_phase_is_still_a_breach(self):
        codes = [f["code"] for f in transcript_lint.check_apparatus([TABLE], "preparation")]
        self.assertIn("INV-075-apparatus-in-exempt-phase", codes)

    def test_the_selftest_fails_with_the_pre_852_pattern(self):
        """The table fixture is load-bearing: the list-only pattern must turn the selftest red."""
        status = transcript_lint._STATUS
        old = re.compile(r"(?im)journey map|^[^\w\n]*your journey[^\w\n]*$"
                         rf"|^[ \t]*{status}[^\n]*\n[ \t]*{status}")
        self.assertIsNone(old.search(TABLE))
        err = io.StringIO()
        with mock.patch.dict(transcript_lint.APPARATUS, {"journey map": old}), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(1, transcript_lint.selftest())
        self.assertIn("journey map pattern missed the plugin's rendering '| Module | Status |",
                      err.getvalue())


if __name__ == "__main__":
    unittest.main()
