"""The reverse-contract guard flags an uncited `.claude/` rule, and clears a cited or deferred one.

`tests/test_new_hard_rules_are_cited_or_deferred.py` checks the rules the live
since-last-audit range reports. What that range holds changes with every merge, and after an
audit it may hold nothing at all, so a green run there proves only that today's lines pass. This
module is the other half (INV-282): synthetic `since` reports, fed to the guard's own parser and
predicate, that fix what the guard must decide whatever the live range holds.

- **MUST flag:** an uncited rule under each `.claude/` root in `SCAN_ROOTS`: `.claude/skills/…`
  and `.claude/skill-overlays/…`. Until #233 every `.claude/` root was counted and never
  checked.
- **MUST NOT flag:** a `.claude/skills/…` rule citing an `INV-` id on its line, and a
  `.claude/` rule whose text is quoted in a `DEFERRED INVARIANT` block.

⚠️ **Dated note, 2026-09-30 (#262): the command root's fixtures are gone with the root.** #262
deleted the ten same-name command files and dropped `.claude/commands` from `SCAN_ROOTS`, so
its MUST-flag fixture went too and the cited fixture moved under `.claude/skills`.
`TheFixtureRootsAreTheProducersRoots` still demands one fixture per producer root, so a root
added back is unproven until it gets one.

⛔ **The guard is imported, never re-implemented.** A second copy of the parser or the predicate
here would prove the copy, not the guard. The deferral fixture replaces only the ledger path the
guard reads, so the guard's own `deferred_rule_text()` extracts the block.

Stdlib only; the guard is imported by path (INV-108).

Source issue: #233 (check the `.claude/` maintainer surface in the reverse-contract guard).

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = REPO_ROOT / "tests" / "test_new_hard_rules_are_cited_or_deferred.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("reverse_contract_guard", GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["reverse_contract_guard"] = module
    spec.loader.exec_module(module)
    return module


GUARD = _load_guard()
unaccounted = GUARD.EveryNewHardRuleIsAccountedFor._unaccounted

#: One rule per root. The headings name files that do not exist, so the guard's source-line
#: lookup falls back to the reported text and the fixture decides the line alone.
UNCITED = "⛔ **Never file an issue the maintainer has not seen.**"
MUST_FLAG = {
    ".claude/skills": ".claude/skills/fixture-233/SKILL.md",
    ".claude/skill-overlays": ".claude/skill-overlays/fixture-233.md",
}
CITED = ("⛔ **(INV-314) Never file an issue the maintainer has not seen.**",
         ".claude/skills/fixture-233-cited/SKILL.md")
DEFERRED = ("⛔ **Never merge a pull request whose issue carries no ledger entry.**",
            ".claude/skills/fixture-233-deferred/SKILL.md")

#: A ledger holding one deferral that quotes `DEFERRED`'s rule verbatim, in the D1–D3 shape.
FIXTURE_LEDGER = """## fixture-233

- **DEFERRED INVARIANT — awaiting the maintainer's sign-off; NOT minted.** The rule already
  shipping:
    - %s — in `%s` — **cite INV-NNN**

  **INV-NNN** — A fixture rule, drafted so the block carries wording.
""" % DEFERRED


def report(*entries):
    """A `since` report shaped as `cmd_since` prints it: a heading, then `+ ` rule lines."""
    out = ["== hard-rule lines added since deadbee (shipped markdown + the .claude/ surface)", ""]
    for heading, rule in entries:
        out += ["   " + heading, "     + " + rule]
    out += ["", "   CORPUS: " + ", ".join(GUARD.SCAN_ROOTS) + " — and `.md` only."]
    return "\n".join(out) + "\n"


@contextlib.contextmanager
def fixture_ledger():
    """Point the guard at a ledger holding only `FIXTURE_LEDGER`."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "IMPLEMENTED.md"
        path.write_text(FIXTURE_LEDGER, encoding="utf-8")
        with mock.patch.object(GUARD, "IMPLEMENTED", path):
            yield


def checked_lines(since_output):
    parsed = GUARD.parse_since(since_output)
    assert not parsed.unresolved and not parsed.unknown_headings, parsed
    return parsed, [line for _heading, line in parsed.checked]


class TheFixtureRootsAreTheProducersRoots(unittest.TestCase):
    """INV-265 — a fixture under a root the producer no longer scans would prove nothing."""

    def test_every_maintainer_root_has_a_must_flag_fixture(self):
        claude_roots = {r for r in GUARD.SCAN_ROOTS if r.startswith(".claude/")}
        self.assertTrue(claude_roots, "conformance.py's SCAN_ROOTS names no `.claude/` root")
        self.assertEqual(
            claude_roots, set(MUST_FLAG),
            "the producer's `.claude/` roots and this module's MUST-flag fixtures differ. A new "
            "root needs a fixture here, or the guard's reach over it is unproven")


class AnUncitedMaintainerRuleIsFlagged(unittest.TestCase):
    def test_each_maintainer_root_is_checked_and_its_uncited_rule_flagged(self):
        for root, heading in MUST_FLAG.items():
            with self.subTest(root=root), fixture_ledger():
                parsed, lines = checked_lines(report((heading, UNCITED)))
                self.assertEqual(
                    1, len(parsed.checked),
                    "the rule under %r was not placed in the checked population, so the guard "
                    "counts it and checks nothing" % root)
                self.assertEqual(
                    [UNCITED], unaccounted(lines),
                    "an uncited rule under %r, named in no deferral, was not flagged" % root)

    def test_the_guard_test_itself_fails_on_it(self):
        """The assertion path, not only the predicate: the guard's own test goes red."""
        case = GUARD.EveryNewHardRuleIsAccountedFor(
            "test_each_rule_added_since_the_last_audit_is_cited_or_deferred")
        since = report((MUST_FLAG[".claude/skill-overlays"], UNCITED))
        result = unittest.TestResult()
        with fixture_ledger(), \
                mock.patch.object(GUARD, "conformance", lambda *a: since), \
                contextlib.redirect_stderr(io.StringIO()) as notice:
            case.run(result)
        self.assertEqual(1, len(result.failures),
                         "the guard did not fail on an uncited `.claude/skill-overlays` rule "
                         "(errors: %s, skipped: %s)" % (result.errors, result.skipped))
        self.assertIn("Never file an issue the maintainer has not seen", result.failures[0][1])
        self.assertIn("[new-hard-rules] 1 line(s) reported since the last audit: 1 checked",
                      notice.getvalue(), "the breakdown line was not printed (INV-308)")


class ACitedOrDeferredMaintainerRuleIsNotFlagged(unittest.TestCase):
    def test_a_maintainer_rule_citing_an_id_on_its_line_passes(self):
        with fixture_ledger():
            _parsed, lines = checked_lines(report(CITED[::-1]))
            self.assertEqual([], unaccounted(lines))

    def test_a_rule_quoted_in_a_deferral_block_passes(self):
        with fixture_ledger():
            _parsed, lines = checked_lines(report(DEFERRED[::-1]))
            self.assertEqual([], unaccounted(lines))

    def test_the_deferral_clears_only_the_rule_it_quotes(self):
        """The deferred fixture must pass by its quote, not because the ledger matches anything."""
        with fixture_ledger():
            _parsed, lines = checked_lines(report(DEFERRED[::-1], (MUST_FLAG[".claude/skills"],
                                                                    UNCITED)))
            self.assertEqual([UNCITED], unaccounted(lines))

    def test_the_guard_test_itself_passes_on_them(self):
        case = GUARD.EveryNewHardRuleIsAccountedFor(
            "test_each_rule_added_since_the_last_audit_is_cited_or_deferred")
        since = report(CITED[::-1], DEFERRED[::-1])
        result = unittest.TestResult()
        with fixture_ledger(), \
                mock.patch.object(GUARD, "conformance", lambda *a: since), \
                contextlib.redirect_stderr(io.StringIO()):
            case.run(result)
        self.assertEqual(([], [], []), (result.failures, result.errors, result.skipped))


if __name__ == "__main__":
    unittest.main()
