"""The family workflow's amendment log cites rules that exist, and there is one of each.

`docs/FAMILY_WORKFLOW.md` is normative for five repositories and its rules are cited **by
number** from four other trackers. So two things have to hold that nothing was checking (#117):

* **Every rule number the amendment log names is a rule the document defines.** An amendment
  citing `R13` when the document stops at `R12` points a reader at nothing, and the reader is
  in another repository with no way to tell whether they are holding a stale copy or the log is
  wrong.
* **No number is defined twice.** The log's own rule is that an amendment never renumbers -- a
  withdrawn rule keeps its number and says so -- for the reason `INVARIANTS.md` never reuses an
  id: ⛔ **a citation that silently resolves to a DIFFERENT rule is worse than one that fails.**

⚠️ **Why the log is guarded at all, when it is prose.** R2 forbids the parent from filing into a
child, so a child cannot be told that a rule moved; it finds out by reading this page when
parity brings it down. The log is therefore not documentation *about* the notification channel
-- it **is** the channel, and a broken citation in it is a broken notification.

⚠️ **What this does NOT establish:** that an amendment entry is accurate, that every changed
rule got an entry, or that the previous wording it quotes is what the page really said. Those
are properties of the editing, not of the text, and no offline check reaches them. The entries
quote their pre-amendment wording so a reader holding an earlier copy can settle it themselves.

Source issue: #117.

Stdlib only; the document is read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"

#: A rule as the document DEFINES it: ``**R8 — ...``
DEFINED = re.compile(r"\*\*R(\d+)\s+—")

#: A rule as anything CITES it. Word-bounded so `R2D2` is not a citation and `R8's` is.
CITED = re.compile(r"\bR(\d+)\b")

#: The amendment log, from its heading to the end of the document.
LOG_HEADING = "## 10. Amendments"

#: A dated entry inside it.
ENTRY = re.compile(r"^### (\d{4}-\d{2}-\d{2}) — ", re.M)


def document():
    return FAMILY.read_text(encoding="utf-8")


def amendment_log():
    t = document()
    i = t.find(LOG_HEADING)
    return t[i:] if i != -1 else ""


def defined_rules():
    return [int(n) for n in DEFINED.findall(document())]


class TheLogIsThereAndNotEmpty(unittest.TestCase):
    """INV-265 -- an absent or empty log satisfies every citation check trivially."""

    def test_the_amendment_section_exists(self):
        self.assertNotEqual(
            "", amendment_log(),
            "%s has no %r section. Four repositories cite its rules by number and the parent "
            "cannot file into any of them (R2), so this section is the only channel by which a "
            "rule change reaches a child" % (FAMILY, LOG_HEADING))

    def test_it_carries_at_least_one_dated_entry(self):
        entries = ENTRY.findall(amendment_log())
        self.assertTrue(
            entries,
            "the amendment section carries no dated entry, so the citation check below passes "
            "over an empty set and proves nothing")

    def test_rules_were_found_to_check_against(self):
        self.assertGreaterEqual(
            len(defined_rules()), 10,
            "fewer than ten numbered rules parsed from %s; the definition pattern has drifted "
            "and every comparison below is vacuous" % FAMILY)


class EveryAmendmentCitesARuleThatExists(unittest.TestCase):
    def test_no_amendment_names_an_undefined_rule(self):
        defined = set(defined_rules())
        dangling = sorted({int(n) for n in CITED.findall(amendment_log())} - defined)
        self.assertEqual(
            [], dangling,
            "the amendment log cites rule(s) %s, which %s does not define. A reader in another "
            "repository cannot tell whether they hold a stale copy or the log is wrong"
            % (", ".join("R%d" % n for n in dangling), FAMILY))


class NoRuleNumberIsDefinedTwice(unittest.TestCase):
    """⛔ An amendment never renumbers; a citation resolving to a different rule is the harm."""

    def test_each_number_is_defined_once(self):
        seen, dupes = set(), []
        for n in defined_rules():
            (dupes.append(n) if n in seen else seen.add(n))
        self.assertEqual(
            [], sorted(set(dupes)),
            "rule number(s) %s are defined more than once in %s. A citation from another "
            "repository now resolves to whichever one the reader reaches first"
            % (", ".join("R%d" % n for n in sorted(set(dupes))), FAMILY))


class ThePatternsReadWhatTheyShould(unittest.TestCase):
    """The constructions that must and must not be read as rules, pinned together (INV-282)."""

    def test_a_definition_is_recognized(self):
        self.assertEqual(["8"], DEFINED.findall("**R8 — never chooses its own target.**"))

    def test_a_possessive_citation_is_recognized(self):
        self.assertEqual(["12"], CITED.findall("R12's requirement is unchanged"))

    def test_an_alphanumeric_token_is_not_a_citation(self):
        self.assertEqual([], CITED.findall("the R2D2 fixture"))

    def test_a_bare_mention_is_not_a_definition(self):
        self.assertEqual([], DEFINED.findall("see R8 above"))


if __name__ == "__main__":
    unittest.main()
