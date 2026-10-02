"""The shipped example recap must not call a resolved entity a "golden record".

Since #335 the Module 0 primer says: "Do **not** call a resolved entity a *golden record*". The
documentation uses that term for a master data management function (deciding which attribute
values survive when records merge), which it places beyond entity resolution. The example recap
mirrors what Module 0 teaches, and it went on teaching the old term: "Three outputs: resolved
entities (golden record), …" survived #335 because the example is kept in sync with a rendered
PDF and needed its own change.

The check is deliberately wide: any "golden record" in the example fails, matched
case-insensitively and across line breaks. The example has no MDM passage where the term would
be correct, and a narrower match would need sentence parsing. It reads the example only; the
primer's own sentence forbidding the term is out of its reach by design.

The check is negative-controlled: it is run against the pre-fix line and must fire there, so a
pattern that matches nothing is caught.

Source issue: #377.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
EXAMPLE_MD = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"
PRIMER = PLUGIN / "skills" / "module-00-entity-resolution-concepts" / "concepts.md"

PRIMER_RULE = "Do **not** call a resolved entity a *golden record*"
GOLDEN_RECORD = re.compile(r"golden\s+record", re.IGNORECASE)

#: The line the example carried before #377, kept as the negative control.
PRE_FIX_LINE = ("- Three outputs: resolved entities (golden record), cross-source relationships, "
                "deduplication.")


def golden_record_lines(text):
    """The 1-based line numbers where "golden record" starts, across line breaks."""
    return [text.count("\n", 0, match.start()) + 1 for match in GOLDEN_RECORD.finditer(text)]


class TheExampleRecapFollowsThePrimer(unittest.TestCase):

    def test_the_primer_still_states_the_rule(self):
        self.assertIn(
            PRIMER_RULE, re.sub(r"\s+", " ", PRIMER.read_text(encoding="utf-8")),
            "the Module 0 primer no longer says not to call a resolved entity a golden record. "
            "This guard enforces that rule on the example recap; re-decide it if the primer "
            "changed its mind")

    def test_the_example_does_not_say_golden_record(self):
        found = golden_record_lines(EXAMPLE_MD.read_text(encoding="utf-8"))
        self.assertEqual(
            found, [],
            "bootcamp_recap.example.md says \"golden record\" at line(s) %s. The Module 0 "
            "primer (concepts.md) says: \"%s\" — the documentation uses that term for an MDM "
            "function beyond entity resolution. Use the primer's \"What it produces\" wording "
            "instead, then re-render the PDF (tests/test_example_recap_sync.py gives the "
            "command)." % (found, PRIMER_RULE))


class TheCheckFiresOnThePreFixLine(unittest.TestCase):

    def test_the_pre_fix_line_is_caught(self):
        self.assertEqual(golden_record_lines(PRE_FIX_LINE), [1])

    def test_a_line_break_inside_the_term_is_caught(self):
        self.assertEqual(golden_record_lines("intro\nresolved entities (golden\nrecord)"), [2])

    def test_the_fixed_wording_is_not_caught(self):
        self.assertEqual(golden_record_lines(
            "- What it produces: matched records grouped into unified entities, and "
            "relationships tracked between those entities."), [])


if __name__ == "__main__":
    unittest.main()
