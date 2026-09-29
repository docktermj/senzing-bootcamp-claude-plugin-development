"""The reverse-contract gate places every root `conformance.py since` can report.

`since` diffs every root in `SCAN_ROOTS`; `tests/test_new_hard_rules_are_cited_or_deferred.py` parses its
output back into files and checks each rule at its source line. Between those two halves sat
an unwritten agreement about what the report looks like, and the consumer's half was wrong:
its parser opened a file heading only when the heading started with `plugins/`. Every line the
view reported under `.claude/` — **112 of them at ref `7b43eee`** — was therefore dropped
silently, and the empty result took the gate's "no hard rules added" skip. The guard that
exists to catch unregistered guarantees reported the absence of new rules while looking at 112.

⛔ **This is the negative control in permanent form.** The defect was not a wrong answer, it
was a *missing question*: nothing anywhere compared the producer's roots against the consumer's.
Asserting today's count is right would re-create it one level up — a parser that drops nothing
because nothing is there to drop. So each root is fed through the parser as a synthetic report
and must come out placed, and an unknown root must come out **named**, not ignored.

⛔ **Placed is checked (#233).** From #74 until #233 a maintainer-surface rule was placed and
then only counted, on the premise that command files restate their skill's rules and cite
nothing. #233 found the premise no longer held (the reasons are in the gate's docstring) and
removed the split, so a line under every scanned root, `.claude/` roots included, lands in the
population the citation check reads. `test_every_scanned_root_is_checked` pins that decision.

Stdlib only; both modules are imported by path (INV-108).

Source issue: #74 (the reverse-contract gate silently discards every rule outside `plugins/`).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude" / "skills" / "production-readiness-audit" / "conformance.py"
GATE = REPO_ROOT / "tests" / "test_new_hard_rules_are_cited_or_deferred.py"

#: Every module that needs to know which roots `since` reports, and the attribute on each that
#: holds them. ⛔ **All of them read the producer's constant; none keeps a copy.** The third
#: entry was found by this change: it scraped the roots out of the `git diff` call's source
#: text, which looked like reading them and stopped working the moment the call was rewritten.
#: A fourth consumer added without a line here is the drift this whole module is about.
CONSUMERS = {
    "test_new_hard_rules_are_cited_or_deferred.py": "SCAN_ROOTS",
    "test_since_view_sees_the_maintainer_surface.py": "diff_pathspecs",
    "test_conformance_sees_a_rule_beside_a_citation.py": "SINCE_ROOTS",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def report_for(roots):
    """A synthetic `since` report: one file heading per root, one rule line under each.

    Shaped exactly as `cmd_since` prints it — three spaces before a heading, five and a `+`
    before a rule — so this exercises the real parser against the real format rather than a
    convenient one.
    """
    out = ["== hard-rule lines added since deadbee (shipped markdown + the .claude/ surface)", ""]
    for i, root in enumerate(roots):
        out.append("   %s/synthetic-%d.md" % (root, i))
        out.append("     + ⛔ **Never ship a rule with no invariant.**")
    return "\n".join(out) + "\n"


class BothHalvesAreLoadable(unittest.TestCase):
    """INV-265 — every assertion below imports these, so a missing one must fail loudly."""

    def test_the_producer_defines_its_roots(self):
        self.assertTrue(CONFORMANCE.is_file(), "%s is gone" % CONFORMANCE)
        roots = getattr(load(CONFORMANCE, "conformance_roots"), "SCAN_ROOTS", None)
        self.assertTrue(
            roots,
            "conformance.py defines no non-empty scanned-root list. The consumer reads it "
            "rather than keeping a copy, so an empty one disables the consumer's parser "
            "entirely -- which is the failure mode this module exists for")

    def test_the_consumer_reads_the_producer_s_roots(self):
        """⛔ Imported, never restated — the copy IS the defect."""
        self.assertTrue(GATE.is_file(), "%s is gone" % GATE)
        producer = tuple(load(CONFORMANCE, "conformance_roots").SCAN_ROOTS)
        consumer = tuple(load(GATE, "gate_under_test").SCAN_ROOTS)
        self.assertEqual(
            producer, consumer,
            "the gate's root list is not the one `since` scans. Two lists that agree today "
            "are still two lists; they disagreed for every root added after the parser was "
            "written, and nothing failed when they did")


class EveryConsumerReadsTheOneDefinition(unittest.TestCase):
    """INV-308 — resolution roots have ONE definition, and every consumer reads it."""

    def test_every_consumer_agrees_with_the_producer(self):
        producer = set(load(CONFORMANCE, "conformance_roots").SCAN_ROOTS)
        for filename, attr in CONSUMERS.items():
            with self.subTest(consumer=filename):
                path = REPO_ROOT / "tests" / filename
                self.assertTrue(path.is_file(), "%s is gone; re-anchor this list" % path)
                value = getattr(load(path, "consumer_" + attr.lower()), attr, None)
                self.assertIsNotNone(
                    value, "%s no longer exposes %s, so what it believes the scanned roots are "
                           "cannot be compared with what they are" % (filename, attr))
                roots = set(value() if callable(value) else value)
                self.assertEqual(
                    producer, roots,
                    "%s reads %s as the scanned roots; `since` scans %s. A consumer that "
                    "disagrees with the producer about which roots exist processes the "
                    "difference as nothing at all"
                    % (filename, sorted(roots), sorted(producer)))


class EveryScannedRootIsPlaced(unittest.TestCase):
    def setUp(self):
        self.gate = load(GATE, "gate_under_test")
        self.roots = tuple(load(CONFORMANCE, "conformance_roots").SCAN_ROOTS)

    def test_no_reported_line_is_dropped(self):
        parsed = self.gate.parse_since(report_for(self.roots))
        self.assertEqual(
            len(self.roots), parsed.reported,
            "the parser did not see one line per scanned root in a report that contains "
            "exactly that")
        self.assertEqual(
            parsed.reported,
            len(parsed.checked) + len(parsed.unresolved),
            "reported lines do not add up to the lines placed. The difference is lines that "
            "went nowhere, which is precisely how 112 of them disappeared")

    def test_each_root_lands_in_exactly_one_population(self):
        for root in self.roots:
            with self.subTest(root=root):
                parsed = self.gate.parse_since(report_for([root]))
                self.assertEqual(
                    [], parsed.unresolved,
                    "a rule reported under the scanned root %r could not be attributed to any "
                    "file, so it is checked by nothing and counted by nothing" % root)
                self.assertEqual(
                    [], parsed.unknown_headings,
                    "the parser does not recognize %r as a scanned root, although `since` "
                    "diffs it and reports rules under it" % root)
                self.assertEqual(
                    1, len(parsed.checked),
                    "the line under %r did not land in the checked population" % root)

    def test_every_scanned_root_is_checked(self):
        """The scoping decision itself (#233), pinned so a later edit states its intent."""
        self.assertTrue(any(r.startswith(".claude/") for r in self.roots),
                        "the producer scans no `.claude/` root, so this pins nothing about it")
        parsed = self.gate.parse_since(report_for(self.roots))
        self.assertEqual(
            sorted(self.roots), sorted(self.gate._root_of(h) for h, _line in parsed.checked),
            "a scanned root's line did not reach the citation check. Every root in SCAN_ROOTS, "
            "the maintainer surface included, is checked with the same predicate (#233); a "
            "root counted but not checked is the gap #233 closed")


class AnUnknownRootIsNamedRatherThanIgnored(unittest.TestCase):
    """⛔ The failure direction: a heading the parser cannot place must be loud."""

    def setUp(self):
        self.gate = load(GATE, "gate_under_test")

    def test_a_heading_outside_every_root_is_reported(self):
        parsed = self.gate.parse_since(report_for(["docs/somewhere-new"]))
        self.assertEqual(
            ["docs/somewhere-new/synthetic-0.md"], parsed.unknown_headings,
            "a heading matching no scanned root was not reported as unknown. If `since` is "
            "widened to a fourth root and this parser is not, the gate must say so -- the "
            "alternative is what happened with `.claude/`: silence that reads as green")
        self.assertEqual(
            1, len(parsed.unresolved),
            "the rule under an unplaceable heading was discarded rather than counted. A "
            "discarded line and a line that was never reported look identical from here")


if __name__ == "__main__":
    unittest.main()
