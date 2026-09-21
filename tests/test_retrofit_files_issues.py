"""`/retrofit-from-public` files issues; it never writes into the development tree.

The command copied the public repo's propagated paths into the dev working tree and applied the
inverse slug rewrite in place. Under the issue-driven workflow (#54) its output is **GitHub
issues describing what diverged**, and the working tree is left alone.

⚠️ **The divergence is real, not hypothetical.** The public repo carries Dependabot bumps and a CI
workflow added directly there — edits that never passed through development.

⛔ **Not copying also removes a hazard the old procedure could only warn about.** `tests/` is not
in the public mirror and cannot come back, so a copied prose edit landed in a shipped file while
the dev-only test quoting that sentence kept asserting the old wording. Measured 2026-08-16 on
`2223961`, the British→US spelling corrections: a **correct** edit, faithfully retrofitted, left
**12 failed / 2730 passed** — ten of them that desync. Nothing is copied now, so nothing desyncs.

⚠️ **The inverse slug transform is still required and is now manual**, applied by whoever
implements a filed issue. A guard cannot check that it happened; the skill says so instead.

⛔ **This asserts what the skill and script INSTRUCT, never what a run does.** The public
repository is not present on every machine — it was absent when this was written — so no offline
test can watch a run refrain from copying. The script is read as text and its shell is never
executed here.

Stdlib only; every file is read as text (INV-108).

Source issue: #54.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude" / "skills" / "retrofit-from-public" / "SKILL.md"
SCRIPT = REPO_ROOT / ".claude" / "skills" / "retrofit-from-public" / "retrofit.sh"

#: Shell that writes into the destination tree. ⛔ Targets the ACT, not one command's name: the
#: script used `rsync -a` and a Python block opening files for writing, and a later editor
#: reaching for `cp -r` or `install` would be doing the same thing under another name.
WRITES_INTO_DEV = re.compile(
    r"\brsync\b(?![^\n]*--dry-run)|\bcp\s+-[a-zA-Z]*r|\binstall\s+-|"
    r"open\([^)]*[\"']w[\"']|\bfh\.write\(|>\s*\"\$here/",
    re.I)


def texts():
    return {"SKILL.md": SKILL.read_text(encoding="utf-8"),
            "retrofit.sh": SCRIPT.read_text(encoding="utf-8")}


def flat(s):
    return re.sub(r"\s+", " ", s).lower()


class BothFilesExist(unittest.TestCase):
    """INV-265 — every assertion below reads these, so they must be real."""

    def test_the_files_exist(self):
        for name, path in (("skill", SKILL), ("script", SCRIPT)):
            with self.subTest(what=name):
                self.assertTrue(path.is_file(), "%s is missing at %s" % (name, path))


class TheScriptWritesNothing(unittest.TestCase):
    def test_no_write_into_the_destination_survives(self):
        hit = WRITES_INTO_DEV.search(texts()["retrofit.sh"])
        self.assertIsNone(
            hit, "retrofit.sh still writes into the development tree (%r). The command's output "
                 "is issues now; a copy that lands in the working tree is the thing #54 retired "
                 "-- and it brings back the desync that left 12 tests failing on 2026-08-16"
                 % (hit.group(0) if hit else ""))

    def test_it_says_it_wrote_nothing(self):
        """⚠️ A reader must be able to tell a report from a sync without reading the source."""
        self.assertRegex(
            texts()["retrofit.sh"], r"NOTHING WAS WRITTEN",
            "the script does not say it wrote nothing. Its predecessor copied, so a run that "
            "looks similar and says neither leaves the maintainer unsure whether to review a "
            "diff or file an issue")


class TheSkillFilesIssuesInItsOwnRepo(unittest.TestCase):
    def test_it_files_issues(self):
        self.assertIn(
            "gh issue create", texts()["SKILL.md"],
            "the skill never names `gh issue create`, so the command has no stated way to "
            "produce the output #54 requires")

    def test_filing_is_gated_on_the_maintainer(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"get a yes|getting a yes",
            "filing is not gated on the maintainer. It is outward-facing and immediate -- an "
            "issue can be edited or closed afterwards but never un-filed -- which is why "
            "/feedback-to-issues and /production-readiness-audit gate it too")

    def test_duplicates_are_checked_against_the_tracker(self):
        """#54's second acceptance criterion: an absorbed change files nothing."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"gh issue list[^.]{0,80}search",
            "the skill does not search the tracker before filing, so a change already absorbed "
            "or already filed gets a second issue")

    def test_it_never_files_in_another_repository(self):
        """⛔ Cross-repo filing is owned by /escalate-to-parent alone."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"escalate-to-parent",
            "the skill does not say that cross-repo filing belongs to /escalate-to-parent. "
            "Children inherit this command, and one that files upward is a second escalation "
            "path nobody chose")


class TheReasonForNotCopyingSurvives(unittest.TestCase):
    """⛔ Cutting the narrative would make this look like a style change (INV-246's lesson)."""

    def test_the_desync_that_motivated_it_is_still_recorded(self):
        text = flat(texts()["SKILL.md"])
        self.assertIn(
            "2223961", text,
            "the worked example is gone. A retrofit that copied correct prose left 12 tests "
            "failing because `tests/` cannot come back from public; without that, a later "
            "editor reads 'do not copy' as caution rather than as a measured result")
        self.assertRegex(
            text, r"12 failed",
            "the measured outcome is gone from the skill; the number is what makes the rule "
            "hold up against 'surely copying is simpler'")

    def test_the_inverse_transform_is_still_required_manually(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"inverse (?:slug )?transform is still required",
            "the skill no longer says the inverse slug rewrite must still be applied by hand. "
            "The script stopped doing it; if nothing says so, dev ends up carrying public "
            "self-references")


if __name__ == "__main__":
    unittest.main()
