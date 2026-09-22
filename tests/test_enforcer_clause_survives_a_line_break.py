"""An `Enforced by` clause is read whether or not Markdown wrapped it, and an unreadable one says so.

`parse()` extracted the enforcing test with a pattern requiring single spaces:
``Enforced by `path` ``. Markdown wraps prose wherever the column runs out, so a clause broken
between `Enforced` and `by`, or before its path, was invisible -- and `show` then reported
`enforcer: (none named)` for a block that named one.

⛔ **That is not a cosmetic miss.** The enforcer is what tells the maintainer whether a rule
already ships guarded, which is an argument for registering it; `(none named)` argues for
holding. On 2026-09-22 BOTH reviewed blocks wrapped the clause, both reported none, and both
in fact named an enforcer -- a miss rate of 2 of 2 on that session's queue, against 25 of 27
clauses matched across the whole ledger.

⛔ **(INV-308) Three states, never two.** A named path, none named, and *present but
unreadable* are different answers. An unclosed backtick matched nothing under the old pattern
and reported as `(none named)`, which states something false about the block: there IS a
clause, and what failed was the reading of it. `enforcer_label` and `enforcer_unreadable`
exist to keep *nothing to read* and *could not read* apart, and `TheThreeStatesAreDistinct`
pins that they never collapse.

⚠️ **Backticks closing across a line break are unreadable, not a path.** `[^`]+` matches
newlines, so such a clause "succeeds" and yields a path with a newline in it -- which resolves
nowhere and would surface as a missing file rather than as a clause nobody can read. It is
classified with the unclosed case deliberately.

⚠️ **What this does NOT establish:** that a named enforcer exists on disk, that it cites the
invariant back, or that it actually guards the rule. Those are
`tests/test_invariant_enforcer_citations.py`'s subject. This pins only that the clause is READ.

Source issue: #105.

Stdlib only; the helper is loaded by path, since it takes no `--repo` argument (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"
LEDGER = REPO_ROOT / "specs" / "IMPLEMENTED.md"

#: The pattern as it stood before #105, kept as the measuring stick rather than as a fallback:
#: the tests below compare against it so the recovery is stated in numbers, not asserted.
OLD_PATTERN = re.compile(r"Enforced by `([^`]+)`")


def helper():
    spec = importlib.util.spec_from_file_location("pending_invariants", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parsed(body):
    """`parse()` over a minimal block carrying `body` as its wording."""
    return helper().parse({"text": "**INV-NNN** — a rule. " + body, "line": 0, "spec": "s"})


#: Every way the shipped ledger has actually broken the clause, plus the unbroken form.
#: ⛔ (INV-282) Derived from the CLAIM -- "whitespace between the words may include a newline"
#: -- not from the two phrasings that happened to break. A future break at a new point is
#: covered by the rule and by these fixtures together.
WRAPPED = {
    "unbroken": "Enforced by `tests/test_a.py`.",
    "broken after Enforced": "Enforced\nby `tests/test_a.py`.",
    "broken before the path": "Enforced by\n`tests/test_a.py`.",
    "broken and indented": "Enforced\n  by `tests/test_a.py`.",
    "two spaces": "Enforced  by  `tests/test_a.py`.",
}

#: Constructions that MUST NOT yield a path. Pinned beside the ones that must (INV-282).
NOT_A_CLAUSE = {
    "prose about enforcement, no path": "This rule is enforced by a test somewhere.",
    "no clause at all": "There is nothing of the sort here.",
}


class AClauseIsReadHoweverItWrapped(unittest.TestCase):
    def test_every_wrapping_yields_the_same_path(self):
        for label, body in WRAPPED.items():
            with self.subTest(wrapping=label):
                self.assertEqual(
                    "tests/test_a.py", parsed(body)["enforcer"],
                    "the clause wrapped as %r was not read; a line break is not a different "
                    "clause" % label)

    def test_the_old_pattern_really_did_miss_these(self):
        """INV-265 in miniature: if the old pattern matched them too, this suite proves nothing."""
        missed = [k for k, v in WRAPPED.items() if not OLD_PATTERN.search(v)]
        self.assertTrue(
            missed,
            "the pre-#105 pattern matched every fixture here, so none of them reproduces the "
            "defect and the assertions above would pass against the unfixed code")


class UnreadableIsNotAbsent(unittest.TestCase):
    """⛔ (INV-308) The two states the old code collapsed."""

    def test_an_unclosed_backtick_is_unreadable(self):
        p = parsed("Enforced by `tests/test_a.py")
        self.assertIsNone(p["enforcer"])
        self.assertTrue(p["enforcer_unreadable"],
                        "a clause whose backtick never closes was reported as naming no "
                        "enforcer; there is a clause, and reading it is what failed")

    def test_backticks_closing_across_a_line_break_are_unreadable(self):
        p = parsed("Enforced by `tests/test_\na.py`.")
        self.assertIsNone(p["enforcer"],
                          "a path containing a newline was returned as if it were a path")
        self.assertTrue(p["enforcer_unreadable"])

    def test_a_block_naming_none_is_still_none(self):
        for label, body in NOT_A_CLAUSE.items():
            with self.subTest(construction=label):
                p = parsed(body)
                self.assertIsNone(p["enforcer"])
                self.assertFalse(
                    p["enforcer_unreadable"],
                    "%r was read as an unreadable clause; it is not a clause at all, and "
                    "crying unreadable here would send the maintainer to fix nothing" % label)


class TheThreeStatesAreDistinct(unittest.TestCase):
    """The labels must not collapse: that collapse is the whole defect."""

    def test_each_state_reads_differently(self):
        mod = helper()
        labels = {
            "named": mod.enforcer_label(parsed("Enforced by `tests/test_a.py`.")),
            "unreadable": mod.enforcer_label(parsed("Enforced by `tests/test_a.py")),
            "absent": mod.enforcer_label(parsed("Nothing of the sort.")),
        }
        self.assertEqual(3, len(set(labels.values())),
                         "two of the three enforcer states print the same text: %r" % labels)
        self.assertIn("tests/test_a.py", labels["named"])
        self.assertIn("UNREADABLE", labels["unreadable"])
        self.assertIn("none named", labels["absent"])


class TheShippedLedgerParses(unittest.TestCase):
    """The corpus is the point: every phrasing in the real file is a fixture (INV-282)."""

    def test_the_ledger_carries_clauses_to_check(self):
        """INV-265 -- an empty corpus satisfies the comparison below trivially."""
        text = LEDGER.read_text(encoding="utf-8")
        self.assertGreaterEqual(
            len(helper().ENFORCER.findall(text)), 10,
            "fewer than ten `Enforced by` clauses were found in %s; the pattern has drifted "
            "from the file and the comparison below proves nothing" % LEDGER)

    def test_the_new_pattern_is_a_superset_of_the_old(self):
        """It must recover clauses, never lose one that already matched."""
        text = LEDGER.read_text(encoding="utf-8")
        old, new = OLD_PATTERN.findall(text), helper().ENFORCER.findall(text)
        lost = [p for p in old if p not in new]
        self.assertEqual([], lost,
                         "the widened pattern stopped matching clause(s) the old one found: "
                         "%s" % ", ".join(lost))
        self.assertGreaterEqual(
            len(new), len(old),
            "the widened pattern matched fewer clauses than the pattern it replaced")

    def test_no_clause_in_the_ledger_is_unreadable(self):
        """A live unreadable clause is a real defect in the file, not in this parser."""
        mod = helper()
        bad = [b["spec"] for b in mod.blocks() if mod.parse(b)["enforcer_unreadable"]]
        self.assertEqual(
            [], bad,
            "deferral block(s) carry an `Enforced by` clause whose path cannot be read: %s. "
            "Fix the wording in specs/IMPLEMENTED.md -- an unreadable clause means the "
            "maintainer cannot tell whether the rule ships guarded" % ", ".join(bad))


if __name__ == "__main__":
    unittest.main()
