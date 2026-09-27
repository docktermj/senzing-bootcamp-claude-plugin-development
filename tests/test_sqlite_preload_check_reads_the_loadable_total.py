"""The SQLite pre-load heads-up judges the load about to run, not the production tier.

Data processing Step 1 asks about the **production** system and forbids substituting the
bootcamp's own record count. The SQLite volume pre-load check at the end of Phase A then read
that same `production_volume.tier` to decide whether to stop the Bootcamper before **this** load,
with a pinned question worded about "this data volume" that offers a database migration.

Observed during a /dry-run phase-3 walk, 2026-09-25: tier `medium`, `database_type: sqlite`,
9,996 loadable records. The Bootcamper was offered a PostgreSQL migration before a load an order
of magnitude below the server's own SQLite guidance (`search_docs(query='loading',
category='anti_patterns')` -> "Do Not Use SQLite in Production", *"under 100K records"*; re-checked
live on server 1.37.13, 2026-09-26).

⛔ **Two questions were conflated, and the fix splits them.** The 👉 now fires on the **loadable
total** (every mapped source's file in `data/senzing-ready/`, since Phases B and C share one
SQLite database) against the MCP-sourced threshold. The production tier gets one line with no 👉
about the take-home system — a note, not a gate on today's load.

⚠️ **Changing the trigger moves two things the check feeds**, and both are pinned here:

- the `sqlite_volume_prompt` marker records `loadable`, and "already decided" matches on it
  rather than on `tier`/`raw_value`, which no longer describe the question asked;
- Phase B Step 7's "start with the first 1,000 records" note is gated on the same loadable-total
  trigger. Read as it was, it fired whenever **no** marker existed — and with the new trigger a
  below-threshold load leaves no marker, so it would fire on nearly every small load, reading an
  absent, conditionally written field as an answer (INV-244).

Everything is asserted as behavior in shipped guidance, so any implementation language
satisfies it (INV-002). The pinned question's wording (INV-056) and the proceed branch's INV-296
line are out of scope and stay pinned by `test_loader_concurrency_reads_database_type.py`.

Source: GitHub issue #163.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE6 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
           "module-06-data-processing")
PHASE_A = MODULE6 / "phaseA-build-loading.md"
PHASE_B = MODULE6 / "phaseB-load-first-source.md"

POINTER = "\U0001F449"  # the pinned-question marker, spelled out so the intent is explicit


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


class PreLoadCheck(unittest.TestCase):

    def setUp(self):
        self.text = flat(PHASE_A)
        self.check = between(self.text, "## SQLite volume pre-load check",
                             "Proceed to Phase B (`phaseB-load-first-source.md`).")
        self.item1 = between(self.check, "1. **Read inputs**",
                             "2. **Decide whether it was already decided.**")
        self.item2 = between(self.check, "2. **Decide whether it was already decided.**",
                             "3. **Prompt only when it matters.**")
        self.item3 = between(self.check, "3. **Prompt only when it matters.**",
                             "4. **When prompting**")


class TheTriggerIsTheLoadableTotal(PreLoadCheck):
    """Assertion 1: item 3 names the loadable total and no longer names the tier."""

    def test_item_1_reads_the_loadable_total_across_every_source(self):
        self.assertIn("**loadable total:**", self.item1)
        self.assertRegex(
            self.item1,
            r"\*\*every\*\* mapped source's file in `data/senzing-ready/` together",
            "the data about to be loaded is every mapped source together — Phases B and C land "
            "in the same SQLite database",
        )
        self.assertIn("loadable total cannot be computed, treat it as indeterminate", self.item1)

    def test_item_3_triggers_on_the_loadable_total_against_the_threshold(self):
        self.assertIn(
            "AND the **loadable total** exceeds the SQLite guidance threshold",
            self.item3,
            "the 👉 fires only when the records about to be loaded exceed the threshold",
        )

    def test_item_3_no_longer_triggers_on_the_production_tier(self):
        self.assertNotRegex(
            self.item3,
            r"tier is `medium` or `large`",
            "the production tier describes the take-home system; triggering the pre-load 👉 "
            "on it offered a migration before a ~10,000-record bootcamp load",
        )
        self.assertNotIn(
            "raw_value", self.item3,
            "item 3 no longer reads raw_value — the loadable total is the only volume input",
        )

    def test_the_threshold_stays_mcp_sourced(self):
        self.assertIn('search_docs(query="loading", category="anti_patterns")', self.item3)
        self.assertIn("Do Not Use SQLite in Production", self.item3)
        self.assertIn("never substitute a remembered figure (INV-080)", self.item3)


class TheMarkerRecordsAndMatchesOnLoadable(PreLoadCheck):
    """Assertion 2: the marker records `loadable`, and item 2 matches on it."""

    def test_both_branches_record_loadable_and_keep_the_existing_fields(self):
        records = re.findall(r"`\{decided: true, choice: \"(\w+)\", ([^}]*)\}`", self.check)
        self.assertEqual(
            ["proceed", "migrate"], [choice for choice, _ in records],
            "both item 4 branches must record sqlite_volume_prompt",
        )
        for choice, fields in records:
            names = [f.strip() for f in fields.split(",")]
            self.assertIn("loadable", names, "the %s branch must record loadable" % choice)
            for kept in ("tier", "raw_value"):
                self.assertIn(kept, names,
                              "the %s branch dropped %s — the change is additive" % (choice, kept))

    def test_item_2_matches_on_loadable_not_on_the_tier(self):
        self.assertIn("its `loadable` matches the current loadable total", self.item2)
        self.assertNotIn(
            "`tier`/`raw_value` match the current selection", self.item2,
            "tier/raw_value no longer describe the question the marker answers",
        )

    def test_an_older_marker_without_loadable_does_not_match(self):
        self.assertIn("a marker with no `loadable`", self.item2)
        self.assertIn("does not match, so re-evaluate on the loadable total", self.item2)

    def test_the_module_4_clause_stays(self):
        self.assertIn("an applicable Module 4 SQLite load-time decision covers this same load",
                      self.item2)


class TheProductionLineIsAStatement(PreLoadCheck):
    """Assertion 3: a medium/large tier on SQLite gets one line with no 👉."""

    def setUp(self):
        super().setUp()
        self.assertIn("**Production line", self.check,
                      "a medium/large tier on SQLite must get its one production line")
        self.para = between(self.check, "**Production line", "*(Internal:")

    def test_the_production_line_is_gated_on_sqlite_and_a_medium_or_large_tier(self):
        self.assertIn(
            "when the database is SQLite and `production_volume.tier` is `medium` or `large`",
            self.para,
        )
        self.assertIn("On PostgreSQL, or on a `demo`/`small` tier, say nothing", self.para)

    def test_the_spoken_line_carries_no_pointer_and_asks_nothing(self):
        spoken = re.findall(r'"([^"]+)"', self.para)
        self.assertEqual(1, len(spoken), "the production line is exactly one quoted line")
        line = spoken[0]
        self.assertNotIn(POINTER, line, "the production line is a statement, never a 👉 question")
        self.assertNotIn("?", line, "the production line asks nothing")
        self.assertIn("PostgreSQL", line)
        self.assertIn("graduation migration checklist", line)

    def test_it_is_said_whether_or_not_the_question_fires_and_changes_nothing(self):
        self.assertIn("Say it whether or not item 4's question fires", self.para)
        self.assertIn("so the turn still ends on the question", self.para)
        self.assertIn("It changes nothing about today's load", self.para)

    def test_the_paragraph_holds_no_pinned_question(self):
        self.assertNotIn("Reply with a number", self.para)
        self.assertNotIn(POINTER + " **", self.para)


class PhaseBUsesTheSameTrigger(unittest.TestCase):
    """Assertion 4: Phase B Step 7's start-smaller note is gated on the loadable total."""

    def setUp(self):
        text = flat(PHASE_B)
        self.note = between(text, "**⚠️ SQLite performance note", "**Checkpoint:** write step 7.")
        self.gate = between(self.note, "Only when ", "Let's start with the first 1,000 records")

    def test_the_suggestion_is_gated_on_the_loadable_total(self):
        self.assertIn("the loadable total exceeds the MCP-sourced threshold", self.gate)
        self.assertIn("the database is SQLite", self.gate)
        self.assertIn("**no** decision is recorded", self.gate)

    def test_it_is_not_gated_on_the_marker_alone(self):
        self.assertNotRegex(
            self.gate,
            r"^Only when \*\*no\*\* decision is recorded and the database is SQLite may",
            "an absent marker alone would fire the note on nearly every below-threshold load",
        )

    def test_an_absent_marker_is_not_an_answer(self):
        self.assertIn('An absent marker is "not asked", never "answered" (INV-244)', self.note)
        self.assertIn("leaves no marker; say nothing here and write none", self.note)

    def test_the_recorded_choice_carries_loadable(self):
        self.assertIn("Record the resulting choice in `sqlite_volume_prompt`, with `loadable`",
                      self.note)


if __name__ == "__main__":
    unittest.main()
