"""`/feedback-to-issues` files GitHub issues, here, and never writes into the archive.

Renamed from `feedback-to-specs` and reworked in #49, part of the 2026-09-15 move from
`specs/` to GitHub issues. Three rules came with that change and none of them was enforced
by anything, which is what this module fixes.

⛔ **It files in its own repository and nowhere else.** In child repos cross-repo routing is
owned exclusively by `/escalate-to-parent`; in this repo -- the parent -- parent-to-child
change travels by parity, so the parent never files into children at all. ⚠️ The mechanism
that would break this is a single flag: `gh issue create --repo <other>`. A rule stated in
prose and contradicted by one flag is why the flag itself is banned below rather than only
the behavior described.

⛔ **It never writes into `specs/`.** The directory is a read-only archive (INV-307), so the
skill may READ it -- a spec often records why the plugin reads as it does -- while writing
nothing there. That distinction is why the assertion below bans a write instruction rather
than the string `specs/`, which legitimately appears throughout: `specs/INVARIANTS.md` is
live and still governs, and `specs/DECLINED.md` must be checked before re-proposing
something that was already declined.

⚠️ **Deduplication has two different jobs and needs both.** `feedback/PROCESSED.jsonl` is
per-entry and content-addressed, and catches the same entry arriving again in a later
feedback file -- the realistic collision, since files accumulate entries across a bootcamp.
It does **not** catch two *different* entries describing one defect, which only a search of
the tracker finds. Dropping either leaves a hole the other cannot cover.

⛔ **This asserts what the skill INSTRUCTS, never what a run does.** Filing an issue is an
outward-facing side effect no offline test may perform, so nothing here establishes that a
real run obeys these rules -- only that it is told to, in terms a later editor cannot
quietly drop. That gap is real and is named rather than left for the file name to imply
otherwise.

Stdlib only; both files are read as text (INV-108).

Source issue: #49 (rename `/feedback-to-specs`; file issues instead of specs).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues"
SKILL = SKILL_DIR / "SKILL.md"
TEMPLATE = SKILL_DIR / "issue-template.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "feedback-to-issues.md"

OLD_SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "feedback-to-specs"
OLD_COMMAND = REPO_ROOT / ".claude" / "commands" / "feedback-to-specs.md"

#: `gh issue create --repo other/thing` -- the one flag that breaks the own-repo rule.
REPO_FLAG = re.compile(r"--repo(?:\s|=)(?!.*never)", re.I)

#: An instruction to WRITE a spec file, as opposed to reading the archive.
WRITES_A_SPEC = re.compile(r"write\s+`?specs/|`specs/<[^>]*>\.md`\s*(?:using|with)", re.I)


def texts():
    return {"SKILL.md": SKILL.read_text(encoding="utf-8"),
            "issue-template.md": TEMPLATE.read_text(encoding="utf-8"),
            "command": COMMAND.read_text(encoding="utf-8")}


def flat(s):
    return re.sub(r"\s+", " ", s).lower()


class TheRenameIsCompleteInBothDirections(unittest.TestCase):
    """Anti-vacuity: every assertion below reads these files, so they must be the real ones."""

    def test_the_new_paths_exist(self):
        for label, path in (("skill", SKILL), ("template", TEMPLATE), ("command", COMMAND)):
            with self.subTest(what=label):
                self.assertTrue(
                    path.is_file(),
                    "%s is missing at %s; the rename is half-applied and every assertion in "
                    "this module would pass on an empty read" % (label, path))

    def test_the_old_paths_are_gone(self):
        """A leftover old copy is worse than none: two skills, one stale, both resolvable."""
        for label, path in (("skill directory", OLD_SKILL_DIR), ("command", OLD_COMMAND)):
            with self.subTest(what=label):
                self.assertFalse(
                    path.exists(),
                    "the old %s still exists at %s. Both names would resolve, and the stale "
                    "one still tells a run to write into a frozen archive" % (label, path))

    def test_the_skill_declares_its_new_name(self):
        self.assertIn(
            "name: feedback-to-issues", texts()["SKILL.md"],
            "SKILL.md's frontmatter still declares the old name, so the command fronts a "
            "skill whose own manifest disagrees with it")


class ItFilesInItsOwnRepositoryOnly(unittest.TestCase):
    """One flag is the whole attack surface, so the flag is what gets banned."""

    def test_the_rule_is_stated(self):
        for name, text in texts().items():
            if name == "issue-template.md":
                continue          # the template is a body, not a procedure
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"never files? (?:into|in) another repositor|nowhere else",
                    "%s does not state that this command files only in its own repository. "
                    "Cross-repo routing belongs to /escalate-to-parent in children, and the "
                    "parent never files into children at all" % name)

    def test_no_repo_flag_is_offered(self):
        """A rule in prose plus a `--repo` example is an invitation, not a rule."""
        for name, text in texts().items():
            hits = [m.group(0) for m in REPO_FLAG.finditer(text)]
            with self.subTest(file=name):
                self.assertEqual(
                    [], hits,
                    "%s contains a `--repo` usage (%s). That flag is the single mechanism "
                    "that breaks the own-repository rule, so it must appear only where the "
                    "text forbids it" % (name, hits))

    def test_it_creates_issues(self):
        self.assertIn(
            "gh issue create", texts()["SKILL.md"],
            "the skill never names `gh issue create`, so its deliverable is unstated — the "
            "whole point of #49 was changing the output from spec files to issues")


class ItNeverWritesIntoTheArchive(unittest.TestCase):
    """Reading `specs/` is required; writing to it is forbidden (INV-307)."""

    def test_no_instruction_writes_a_spec_file(self):
        for name, text in texts().items():
            hit = WRITES_A_SPEC.search(text)
            with self.subTest(file=name):
                self.assertIsNone(
                    hit, "%s still instructs writing a spec file (%r). `specs/` is a "
                         "read-only archive (INV-307); the freeze guard would reject the "
                         "output" % (name, hit.group(0) if hit else ""))

    def test_the_freeze_is_stated(self):
        self.assertIn(
            "inv-307", flat(texts()["SKILL.md"]),
            "the skill never cites INV-307, so a reader has no way to know why it may read "
            "`specs/` but not write there")

    def test_reading_the_archive_is_still_permitted(self):
        """Over-correcting into 'never touch specs/' would lose the decline check."""
        self.assertIn(
            "declined.md", flat(texts()["SKILL.md"]),
            "the skill no longer points at specs/DECLINED.md. The archive stays readable for "
            "exactly this reason: it records the argument AGAINST a change that the spec "
            "itself argues for, so re-proposing one needs that check")


class DeduplicationCoversBothCollisions(unittest.TestCase):
    """The ledger and the tracker catch different things; neither substitutes."""

    def test_the_per_entry_ledger_survives(self):
        self.assertIn(
            "processed.jsonl", flat(texts()["SKILL.md"]),
            "the per-entry ledger is gone from the skill. It is what stops a re-submitted "
            "feedback file re-filing every entry it already triaged")

    def test_the_tracker_is_searched_before_filing(self):
        self.assertIn(
            "gh issue list", flat(texts()["SKILL.md"]),
            "the skill never searches existing issues, so two different feedback entries "
            "describing one defect produce two issues — the collision PROCESSED.jsonl "
            "structurally cannot catch")


class TheAbsenceClauseSurvivedTheFormatChange(unittest.TestCase):
    """INV-213's wording says 'a spec'; the obligation had to be carried, not dropped."""

    def test_the_template_carries_owner_checked(self):
        self.assertIn(
            "owner-checked:", texts()["issue-template.md"],
            "the issue template dropped the `owner-checked:` clause. INV-213 requires an "
            "absence claim to name the route that would carry the fact; losing it at the "
            "format change is how the discipline lapses without anything failing")

    def test_the_skill_still_requires_it(self):
        self.assertIn(
            "owner-checked:", texts()["SKILL.md"],
            "the skill no longer requires `owner-checked:` on an absence claim (INV-213)")


if __name__ == "__main__":
    unittest.main()
