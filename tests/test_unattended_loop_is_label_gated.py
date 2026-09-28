"""The unattended loop works only issues the maintainer labeled, and defaults to doing nothing.

`/unattended-spec-loop` worked the `specs/` backlog to empty. That backlog froze under
INV-307, so #51 renamed it `/unattended-issue-loop` and pointed it at GitHub issues — but
"every open issue" is not a safe default. The tracker carries parity deltas, escalations and
customer-derived feedback, and every one of those needs judgment this loop explicitly does
not have.

⛔ **So the gate is an opt-in label, and its failure direction is DOING NOTHING.** No label,
no work. An unlabeled backlog is a **no-op**, not an error and not a license to widen the
query. ⚠️ That is the whole safety property: a missing gate must mean "assume nothing", never
"assume everything".

⚠️ **Re-pointed 2026-09-28 (#215): the procedure no longer lives in this repository.** The
governing copy is `~/.claude/skills/unattended-issue-loop/SKILL.md`; the project `SKILL.md` is a
pointer stub and `.claude/commands/unattended-issue-loop.md` is the repo overlay. ⛔ **The
governing text under `~/.claude/skills/` is NOT checked in CI** -- a runner checks out only the
repository, so a test reading it would pass on one machine and fail everywhere else (INV-308).
What this module now asserts:

* the label gate against the `docs/FAMILY_WORKFLOW.md` §2 row, which is where this repository
  states it;
* the repository-only obligations (INV-309, INV-307, no `submit_feedback`, no declining) against
  the overlay, where they moved;
* that neither the stub nor the overlay instructs writing into the frozen archive.

Assertions **removed** at #215, each because the text it pinned no longer exists in the
repository and the rule is the governing copy's, not this repository's:

* `--label unattended-ok` in both files -- the governing copy deliberately lists open issues
  and filters by label itself, because `--label` goes through GitHub's lagging search index;
* "comment on the issue" and "remove the `unattended-ok` label" for a blocked issue -- the
  governing copy's blocked-issue procedure;
* the whole `TheUnattendedAuditFilesNothing` class -- the loop that runs has no audit cycle, so
  there is no unattended audit whose filing to forbid. The audit skill keeps its own rule
  (`tests/test_audit_files_issues_not_specs.py`).

⛔ **This asserts what the repository's text INSTRUCTS, never what a run does.** No offline test
can watch an unattended run query GitHub.

Stdlib only; every file is read as text (INV-108).

Source issues: #51 (rename to `/unattended-issue-loop`, label-gated); #215 (the user-level copy
governs).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "unattended-issue-loop"
SKILL = SKILL_DIR / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "unattended-issue-loop.md"
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"

OLD_SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "unattended-spec-loop"
OLD_COMMAND = REPO_ROOT / ".claude" / "commands" / "unattended-spec-loop.md"

#: The opt-in label. Named once here so an assertion cannot drift from the prose it checks.
LABEL = "unattended-ok"

#: An instruction to WRITE into the frozen archive, as opposed to reading or forbidding it.
WRITES_A_SPEC = re.compile(r"(?i)append a `?## Blocked|write .{0,20}into `?specs/ as you find")


def texts():
    return {"SKILL.md": SKILL.read_text(encoding="utf-8"),
            "command": COMMAND.read_text(encoding="utf-8")}


def overlay():
    return flat(COMMAND.read_text(encoding="utf-8"))


def family_row():
    rows = [l for l in FAMILY.read_text(encoding="utf-8").splitlines()
            if l.startswith("| `unattended-issue-loop` |")]
    assert len(rows) == 1, "expected one §2 row for unattended-issue-loop, found %d" % len(rows)
    return flat(rows[0])


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
    """The opt-in gate, asserted where this repository states it: the FAMILY_WORKFLOW row."""

    def test_the_row_names_the_label(self):
        self.assertIn(
            "`%s`" % LABEL, family_row(),
            "the §2 row for unattended-issue-loop no longer names the `%s` label, so nothing "
            "in this repository says which issues the maintainer marked safe" % LABEL)

    def test_an_unlabeled_backlog_is_a_no_op(self):
        """⛔ The failure direction is the safety property, so it is asserted directly."""
        self.assertRegex(
            family_row(), r"no label, no work",
            "the row does not state that an unlabeled backlog is a no-op. Without it a run "
            "finding nothing labeled may 'helpfully' widen the query")

    def test_the_run_may_not_label_issues_itself(self):
        self.assertRegex(
            family_row(), r"never adds the label itself",
            "the row does not forbid the run adding the label itself. Selecting the work is "
            "the maintainer's decision; a loop that can label can select")


class TheArchiveStaysFrozen(unittest.TestCase):
    """The old blocked path wrote into `specs/`, which INV-307 forbids."""

    def test_it_does_not_write_into_the_frozen_archive(self):
        for name, text in texts().items():
            hit = WRITES_A_SPEC.search(text)
            with self.subTest(file=name):
                self.assertIsNone(
                    hit, "%s still instructs writing into the frozen archive (%r). `specs/` "
                         "is read-only (INV-307) and the freeze guard rejects the output"
                         % (name, hit.group(0) if hit else ""))

    def test_the_overlay_names_the_one_file_it_may_write(self):
        """#215: the old copy said "never write into specs/" beside a required ledger entry."""
        self.assertRegex(
            overlay(), r"inv-307.{0,120}except the issue's own `specs/implemented\.md` entry",
            "the overlay does not say which file under specs/ an unattended run may write. "
            "Its predecessor forbade all of specs/ while requiring a ledger entry there")


class TheRepositoryOnlyGatesSurvive(unittest.TestCase):
    """What an unattended run must never decide here, asserted on the overlay."""

    def test_it_does_not_call_submit_feedback(self):
        self.assertRegex(overlay(), r"never call `submit_feedback`")

    def test_it_does_not_decline(self):
        self.assertRegex(overlay(), r"never decline",
                         "the overlay no longer forbids declining; that is the maintainer's alone")


class TheInvariantGateSurvives(unittest.TestCase):
    """#51's second acceptance criterion: unattended work must not skip INV-309."""

    def test_the_loop_points_at_the_sanctioned_deferral_path(self):
        self.assertIn(
            "inv-309", overlay(),
            "the loop overlay no longer cites INV-309, so nothing binds an unattended run to the "
            "invariant-capture gate — and an unattended run is exactly where a shipped rule "
            "goes unrecorded, which is the 2026-08-17 defect this skill was written about")

    def test_it_forbids_signing_off_an_invariant(self):
        self.assertRegex(
            overlay(), r"never sign off an invariant",
            "the loop overlay no longer forbids signing off an invariant. Minting an ID is the "
            "maintainer's alone, and an unattended run has no maintainer to ask")

    def test_declining_to_mint_does_not_decline_to_record(self):
        """The 2026-08-17 defect was the *safe-looking* move, so the trap is named."""
        self.assertRegex(
            overlay(),
            r"declining to\s+\*?\*?mint (?:it|one) "
            r"(?:does not decline|is not declining) to ship the rule",
            "the loop overlay no longer warns that declining to mint is not declining to ship. "
            "That distinction IS the 2026-08-17 defect: 'do not record an invariant the "
            "maintainer has not agreed to' shipped the rule and registered nothing")


if __name__ == "__main__":
    unittest.main()
