"""`/review-invariants` performs the registration and stops; it never commits and never pushes.

Registering an invariant is the most permanent act in this repository. `INVARIANTS.md` is
append-only — a wrong id is corrected by a dated note beneath it and never removed — and the
wording binds every future change. ⛔ **It was the one permanent act here with no gate at all.**
The skill said *"Verify, then commit"* and named no destination, so it committed onto whatever
branch was checked out, which for a maintainer who has just merged and pulled is `main`.

⚠️ **The gap was easy to miss because the maintainer is standing right there.** They approved the
wording a moment earlier, so the commit feels approved too. It is not the same approval:
`/implement-github-issue` waits twice on the same repository, `/release` never pushes, and
`/propagate-to-public` never commits — this skill did both with neither.

⛔ **The fix is the strictest of those patterns, not a pre-push pause.** Nothing is committed, so
nothing can be pushed by accident, and the maintainer commits where they judge right. ⚠️ That was
also the only shape available: the `git-conventions` hook names branches
`<issue-number>-<github-username>-<n>`, and a review session has no single issue — the
2026-09-14 session registered **seven** ids drawn from different sources. Instructing a bypass of
the maintainer's own convention was the alternative and was declined (#78).

⚠️ **A guarantee became guidance, and that is a real cost.** *One invariant per commit* used to
happen because the skill did it; now it happens if the maintainer does. The revert property it
protects is weaker and no test can hold anyone to it — so the skill states it at the moment it
hands the diff over, and this file asserts that it still does.

⛔ **This asserts what the skill INSTRUCTS, never what a run does.** No offline test can watch a
run refrain from `git commit`, and nothing here establishes that one does. The same limit the MCP
re-check and label-gate guards carry, named here rather than left for the file name to imply
otherwise.

Stdlib only; both files are read as text (INV-108).

Source issue: #78.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "review-invariants.md"

#: An instruction to COMMIT the registration, as opposed to describing what the maintainer does
#: with it afterwards. The pattern targets the imperative the skill used to carry.
COMMITS_THE_REGISTRATION = re.compile(r"(?i)verify,?\s+then\s+commit|then commit it and push")


def texts():
    return {"SKILL.md": SKILL.read_text(encoding="utf-8"),
            "command": COMMAND.read_text(encoding="utf-8")}


def flat(s):
    return re.sub(r"\s+", " ", s).lower()


class BothFilesExist(unittest.TestCase):
    """Anti-vacuity: every assertion below reads these, so they must be real."""

    def test_the_files_exist(self):
        for name, path in (("skill", SKILL), ("command", COMMAND)):
            with self.subTest(what=name):
                self.assertTrue(
                    path.is_file(),
                    "%s is missing at %s; every assertion in this module would pass on an "
                    "empty read" % (name, path))


class TheRunStopsAtTheWorkingTree(unittest.TestCase):
    def test_both_files_forbid_committing_and_pushing(self):
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"does not commit and does not push",
                    "%s does not forbid committing the registration. Registering is permanent "
                    "and append-only, and this was the one permanent act here with no gate at "
                    "all" % name)

    def test_neither_file_still_says_verify_then_commit(self):
        for name, text in texts().items():
            hit = COMMITS_THE_REGISTRATION.search(text)
            with self.subTest(file=name):
                self.assertIsNone(
                    hit, "%s still instructs the run to commit the registration (%r). The "
                         "maintainer approved a wording, which is not the same as approving a "
                         "commit" % (name, hit.group(0) if hit else ""))

    def test_the_skill_says_where_the_changes_are_left(self):
        """'Do not commit' without a destination loses the work at session end."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"stop(s)? (?:at|with) the (?:changes in the )?working tree",
            "the skill forbids committing but never says the changes stay in the working tree, "
            "so a reader cannot tell whether the registration was written at all")

    def test_the_skill_reports_every_file_it_touched(self):
        """A maintainer about to commit needs the list, and the skill already knows it."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"report every file it touched|every file touched",
            "the skill hands over a working tree without naming what it changed. Four files "
            "move per registration and the maintainer is the one committing them")


class TheCostIsStatedRatherThanHidden(unittest.TestCase):
    """⚠️ A guarantee became guidance; the skill must say so where it hands over."""

    def test_one_invariant_per_commit_survives_as_the_maintainers_rule(self):
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"one invariant per commit is (?:now|then) the maintainer's",
                    "%s dropped the one-invariant-per-commit rule when the skill stopped "
                    "committing. It exists so a later revert takes only the rule that was "
                    "questioned; the skill can no longer enforce it, which is exactly why it "
                    "must still say it" % name)

    def test_the_skill_says_why_a_branch_was_not_required(self):
        """⚠️ Otherwise the next editor 'fixes' this by instructing a hook bypass."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"review session has no single issue",
            "the skill does not record why it leaves the tree rather than making a branch. The "
            "branch-name convention needs an issue number and a review session has none, so "
            "the next editor reaches for a bypass of the maintainer's own hook")


class TheSkillStillPerformsTheRegistration(unittest.TestCase):
    """⛔ Over-correcting into 'do nothing' would delete the reason this skill exists."""

    def test_it_still_edits_the_invariants_file(self):
        text = texts()["SKILL.md"]
        self.assertIn(
            "INVARIANTS.md", text,
            "the skill no longer names INVARIANTS.md. The gate is about what leaves the working "
            "tree, not about who does the mechanical registration")

    def test_it_still_runs_the_verification_commands(self):
        """⛔ Asserted inside the verify BLOCK, not anywhere in the file.

        The first version searched the whole document and passed a negative control that deleted
        the command from the block: `citations.py verify` is also named in the prose explaining
        what registering buys you, 130 lines earlier. A guard satisfied by a mention somewhere
        else is the shape this repository keeps finding -- so the block is located first and the
        assertion runs only inside it.
        """
        text = texts()["SKILL.md"]
        start = text.find("Verify:")
        self.assertNotEqual(
            -1, start,
            "the verification block's heading is gone, so this test cannot locate what it "
            "checks; re-anchor it rather than letting it search the whole file")
        block = text[start:text.find("###", start)]
        for cmd in ("citations.py verify", "coverage_reports.py shipped",
                    "unittest discover -s tests"):
            with self.subTest(command=cmd):
                self.assertIn(
                    cmd, block,
                    "the skill no longer runs `%s` before handing over. Stopping earlier must "
                    "not mean verifying less -- the maintainer is about to commit this" % cmd)


if __name__ == "__main__":
    unittest.main()
