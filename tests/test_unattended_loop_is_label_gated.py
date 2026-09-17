"""The unattended loop works only issues the maintainer labeled, and defaults to doing nothing.

`/unattended-spec-loop` worked the `specs/` backlog to empty. That backlog froze under
INV-307, so #51 renamed it `/unattended-issue-loop` and pointed it at GitHub issues — but
"every open issue" is not a safe default. The tracker carries parity deltas, escalations and
customer-derived feedback, and every one of those needs judgment this loop explicitly does
not have.

⛔ **So the gate is an opt-in label, and its failure direction is DOING NOTHING.** No label,
no work. An unlabeled backlog is a **no-op**, not an error and not a license to widen the
query. ⚠️ That is the whole safety property: a missing gate must mean "assume nothing", never
"assume everything", and a loop that silently fell back to the full backlog would be
indistinguishable from one working correctly until it had already done the damage.

⚠️ **The label does not exist in the repository yet, deliberately.** The maintainer creates it
once with `gh label create`; until then every run of this loop is a no-op. Creating it is an
outward-facing change to repository metadata and is the maintainer's to make — which is also
why no assertion here requires the label to exist. The loop must be correct *before* it is
armed.

⛔ **The audit half is BLOCKED and the loop must say so.** `/production-readiness-audit` still
writes spec files into the frozen archive, so an unattended audit would produce output the
freeze guard rejects and the loop's stop condition would be measured against files that cannot
land. Asserting that the loop states this is what stops a run from cycling on a half that
cannot work.

⛔ **This asserts what the loop INSTRUCTS, never what a run does.** No offline test can watch
an unattended run query GitHub, so nothing here establishes that the label filter is applied —
only that it is stated, in terms a later editor cannot quietly drop. The same limit as the MCP
re-check guard, and named here rather than left for the file name to imply otherwise.

Stdlib only; both files are read as text (INV-108).

Source issue: #51 (rename to `/unattended-issue-loop`, label-gated).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "unattended-issue-loop"
SKILL = SKILL_DIR / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "unattended-issue-loop.md"

OLD_SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "unattended-spec-loop"
OLD_COMMAND = REPO_ROOT / ".claude" / "commands" / "unattended-spec-loop.md"

#: The opt-in label. Named once here so an assertion cannot drift from the prose it checks.
LABEL = "unattended-ok"

#: An instruction to WRITE into the frozen archive, as opposed to reading or forbidding it.
WRITES_A_SPEC = re.compile(r"(?i)append a `?## Blocked|write .{0,20}into `?specs/ as you find")


def texts():
    return {"SKILL.md": SKILL.read_text(encoding="utf-8"),
            "command": COMMAND.read_text(encoding="utf-8")}


def flat(s):
    return re.sub(r"\s+", " ", s).lower()


class TheRenameIsCompleteInBothDirections(unittest.TestCase):
    """Anti-vacuity: every assertion below reads these files, so they must be the real ones."""

    def test_the_new_paths_exist(self):
        for label, path in (("skill", SKILL), ("command", COMMAND)):
            with self.subTest(what=label):
                self.assertTrue(
                    path.is_file(),
                    "%s is missing at %s; the rename is half-applied and every assertion in "
                    "this module would pass on an empty read" % (label, path))

    def test_the_old_paths_are_gone(self):
        """A leftover copy is worse than none: two loops, one working a frozen backlog."""
        for label, path in (("skill directory", OLD_SKILL_DIR), ("command", OLD_COMMAND)):
            with self.subTest(what=label):
                self.assertFalse(
                    path.exists(),
                    "the old %s still exists at %s. Both names would resolve, and the stale "
                    "one still works the frozen `specs/` backlog" % (label, path))

    def test_the_skill_declares_its_new_name(self):
        self.assertIn(
            "name: unattended-issue-loop", texts()["SKILL.md"],
            "SKILL.md's frontmatter still declares the old name, so the command fronts a "
            "skill whose own manifest disagrees with it")


class OnlyLabeledIssuesAreWorked(unittest.TestCase):
    """The opt-in gate, and the no-op default that makes it safe."""

    def test_the_label_filter_is_stated(self):
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertIn(
                    "--label %s" % LABEL, text,
                    "%s never names the `--label %s` filter, so nothing tells an unattended "
                    "run which issues the maintainer marked safe — and the whole backlog "
                    "becomes the default" % (name, LABEL))

    def test_an_unlabeled_backlog_is_a_no_op(self):
        """⛔ The failure direction is the safety property, so it is asserted directly."""
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"no label, no work",
                    "%s does not state that an unlabeled backlog is a no-op. Without it a "
                    "run finding nothing labeled may 'helpfully' widen the query, which is "
                    "the one outcome the gate exists to prevent" % name)

    def test_the_run_may_not_label_issues_itself(self):
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"never add the label yourself",
                    "%s does not forbid the run adding the label itself. Selecting the work "
                    "is the maintainer's decision; a loop that can label can select" % name)


class ABlockedIssueIsRecordedOnTheIssue(unittest.TestCase):
    """The old blocked path wrote into `specs/`, which INV-307 now forbids."""

    def test_it_does_not_write_into_the_frozen_archive(self):
        for name, text in texts().items():
            hit = WRITES_A_SPEC.search(text)
            with self.subTest(file=name):
                self.assertIsNone(
                    hit, "%s still instructs writing into the frozen archive (%r). `specs/` "
                         "is read-only (INV-307) and the freeze guard rejects the output"
                         % (name, hit.group(0) if hit else ""))

    def test_the_block_is_recorded_on_the_issue(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"comment on the issue",
            "the blocked path no longer records anything on the issue. The loop's own rule is "
            "that a note living only in the handoff dies with the conversation")

    def test_the_label_is_removed_when_blocked(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"remove the `?%s`? label" % LABEL,
            "a blocked issue keeps its label, so the next unattended run retries it blindly "
            "and the loop can spin on one issue it cannot finish")


class TheUnattendedAuditFilesNothing(unittest.TestCase):
    """⚠️ INVERTED, not deleted, on 2026-09-16 (#69).

    This class previously asserted the audit half was **blocked**, because
    `/production-readiness-audit` wrote findings into the frozen archive. #69 fixed that —
    but not by making the unattended audit file issues. ⛔ **`gh issue create` leaves the
    machine, and this loop's contract is that nothing leaves the machine unattended.** So an
    unattended audit records findings in its dated ledger entry and files none of them.

    ⛔ The assertion was **re-pointed at the new rule rather than removed**: deleting it would
    have left the loop free to file issues unattended with nothing failing, which is the
    hazard the block note was standing in for all along.
    """

    def test_both_files_say_an_unattended_audit_files_nothing(self):
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"files nothing",
                    "%s does not say an unattended audit files nothing. `gh issue create` "
                    "leaves the machine, and this loop's contract is that nothing leaves the "
                    "machine unattended -- so an unattended audit that files issues breaks "
                    "the contract as surely as one calling submit_feedback would" % name)

    def test_neither_file_lets_a_run_file_the_findings_afterwards(self):
        """The loophole the first version left: record now, file at the end of the run."""
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"never file (?:the audit's findings|those findings) yourself",
                    "%s does not forbid a run filing the recorded findings itself before it "
                    "ends. Deferring the outward-facing act to the last step of an unattended "
                    "run does not make it attended" % name)


class TheInvariantGateSurvives(unittest.TestCase):
    """#51's second acceptance criterion: unattended work must not skip INV-309."""

    def test_the_loop_points_at_the_sanctioned_deferral_path(self):
        text = texts()["SKILL.md"]
        self.assertIn(
            "INV-309", text,
            "the loop no longer cites INV-309, so nothing binds an unattended run to the "
            "invariant-capture gate — and an unattended run is exactly where a shipped rule "
            "goes unrecorded, which is the 2026-08-17 defect this skill was written about")

    def test_it_forbids_signing_off_an_invariant(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"never sign off an invariant",
            "the loop no longer forbids signing off an invariant. Minting an ID is the "
            "maintainer's alone, and an unattended run has no maintainer to ask")

    def test_declining_to_mint_does_not_decline_to_record(self):
        """The 2026-08-17 defect was the *safe-looking* move, so the trap is named."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"declining to\s+\*?\*?mint it does not decline to ship the rule",
            "the loop no longer warns that declining to mint is not declining to ship. That "
            "distinction IS the 2026-08-17 defect: 'do not record an invariant the maintainer "
            "has not agreed to' shipped the rule and registered nothing")


if __name__ == "__main__":
    unittest.main()
