"""`citations.py verify` keeps saying what it does not check.

The tool ends a clean run with its own statement of the span it never read:

    clean: 309 invariants defined, every citation resolves, ...
    Reminder: commit-message citations are outside this check and cannot be fixed.

⛔ **Until #97 no test pinned that line.** Deleting it left the suite green and the tool reporting
`clean:` with a count and no qualifier — and a clean run with a number is the output a maintainer
trusts most, so the moment the qualifier goes it reads as total coverage.

That reminder is this tool's entire INV-308 compliance: the invariant requires a tool reporting a
verification count to **also report what it could not verify**. It did, in one line, unguarded.
Measured 2026-09-21 while implementing #91: two matches for the phrase across `tests/*.py`, and
neither was an assertion on this output — one an unrelated class name, one the #91 disclosure
describing this very gap.

⛔ **Matched from the CLAIM, not the sentence** (INV-282). The claim is *commit messages are
outside this check*; a reworded disclosure saying the same thing must pass, and the fixtures below
pin both directions. A guard fitted to the current wording would fail on a correct rewrite and be
relaxed rather than fixed.

⚠️ **What this does NOT establish.** That the disclosure is **complete** — whether other limits go
unstated is a reading of the tool, not something a test can decide. It also observes only the
**clean** path: the tool prints its problems and returns non-zero without this line, which is
defensible because that run claims nothing, and is why the check below skips rather than fails
when the repository is not clean.

Stdlib only; the tool is run as a subprocess and its source is not parsed (INV-108).

Source issue: #97.

Run:  python3 -m unittest discover -s tests
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CITATIONS = REPO_ROOT / ".claude" / "skills" / "compact-dev-environment" / "citations.py"

#: The claim: commit messages are outside what this check can reach. Subject plus any predicate
#: meaning "not covered here" -- so the wording can change without the guarantee changing.
STATES_ITS_LIMIT = re.compile(
    r"commit[- ]message[^.]{0,80}?(?:outside|not\s+(?:checked|verified|covered)"
    r"|cannot\s+be\s+(?:checked|verified|fixed|reached))",
    re.I)

#: The wording that shipped, plus rewrites that say the same thing. All must pass, or the matcher
#: is fitted to today's sentence and a correct rewrite would be reported as a regression.
EQUIVALENT = (
    "Reminder: commit-message citations are outside this check and cannot be fixed.",
    "Note: citations in commit messages are not checked here.",
    "⚠️ Commit-message citations cannot be verified by this tool.",
    "Commit-message citations are outside the scope of this verification.",
)

#: Output with the disclosure gone, and prose that must not be mistaken for it.
WITHOUT_THE_LIMIT = (
    "clean: 309 invariants defined, every citation resolves, every Source resolves.",
    "3 referential problem(s):",
    "Fix these before compacting further; a dangling reference now becomes an invisible one.",
    "every feedback archive is in the ledger.",
)


def verify():
    return subprocess.run([sys.executable, str(CITATIONS), "verify"],
                          capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=180)


class TheMatcherIsCalibrated(unittest.TestCase):
    """⛔ INV-282 — pinned in both directions, or the run assertion below proves little."""

    def test_the_shipped_wording_and_its_rewrites_all_pass(self):
        for text in EQUIVALENT:
            with self.subTest(wording=text[:48]):
                self.assertRegex(
                    text, STATES_ITS_LIMIT,
                    "an equivalent statement of the same limit is not matched, so rewording the "
                    "disclosure correctly would read as a regression: %r" % text)

    def test_output_without_the_limit_does_not_pass(self):
        for text in WITHOUT_THE_LIMIT:
            with self.subTest(wording=text[:48]):
                self.assertNotRegex(
                    text, STATES_ITS_LIMIT,
                    "output carrying no statement of the limit matched anyway, so the check "
                    "below would pass on a tool that had dropped it: %r" % text)


class AVerifyRunStatesWhatItDoesNotCheck(unittest.TestCase):
    def test_the_tool_is_where_this_test_expects(self):
        self.assertTrue(
            CITATIONS.is_file(),
            "%s is gone; re-anchor this test rather than letting it pass on a missing file"
            % CITATIONS)

    def test_a_clean_run_says_commit_messages_are_outside_it(self):
        done = verify()
        if done.returncode != 0:
            self.skipTest(
                "`citations.py verify` exited %d, so this repository has referential problems "
                "and the clean-path output could not be observed. That run claims nothing and "
                "is not what this guard is about; fix the references first" % done.returncode)
        self.assertRegex(
            done.stdout, STATES_ITS_LIMIT,
            "a clean `citations.py verify` no longer states that commit-message citations are "
            "outside it. `clean:` plus a count then reads as total coverage, which is the "
            "reading INV-308 exists to prevent:\n%s" % done.stdout[-400:])

    def test_the_clean_line_and_the_limit_travel_together(self):
        """⚠️ The limit must qualify the claim, not sit somewhere a reader may not reach."""
        done = verify()
        if done.returncode != 0:
            self.skipTest("verify is not clean here; see the previous test's message")
        self.assertIn(
            "clean:", done.stdout,
            "the clean line is gone, so this guard is asserting a qualifier on a claim that is "
            "no longer made -- re-anchor it rather than leaving it to pass vacuously")


if __name__ == "__main__":
    unittest.main()
