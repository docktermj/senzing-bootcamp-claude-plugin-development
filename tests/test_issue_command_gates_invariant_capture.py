"""The issue command states invariant capture as a gate on closing, not as a step.

`/implement-github-issue` is becoming the only development path in this repository (#50,
part of the 2026-09-15 move from `specs/` to GitHub issues). That concentrates every durable
guarantee the repo ships through one command — and the rule that each one gets recorded lives
in prose, where a well-meant edit can remove it without failing anything.

⚠️ **The gap is measured, not hypothetical.** #38 found **four durable guarantees that shipped
with enforcing tests and no registered invariant, inside eleven days** — the class
`the-github-issue-path-ships-guarantees-with-no-invariant` exists to stop it. Raising the
volume through that path without pinning the gate is how eleven days becomes a quarter.

⛔ **This guard asserts the CONDITION is stated, never the wording.** INV-219 forbids pinning
the verbatim text of a claim: the rule is that closing is gated on invariant capture, and a
later editor MUST be free to say that better. So each assertion below looks for a structural
property — that closing and the deferral mechanism appear in the same requirement, that the
third permitted answer is present, that the command disclaims the ability to register — rather
than for a sentence.

⚠️ **Three answers are permitted and all three must survive.** Register an invariant, write a
`DEFERRED INVARIANT` block, or state plainly that the work establishes none. A guard that
demanded only the first would make the command lie, since minting an ID is the maintainer's
alone; one that forgot the third would push a run into claiming a rule it did not ship.
`tests/test_spec_ledger_invariants.py` already accepts exactly these three at the ledger end —
this pins the same contract at the command end, where the obligation is created.

⛔ **Scoped to the COMMAND, not the skill.** The skill has a copy at
`~/.claude/skills/implement-github-issue/SKILL.md` shared with repositories that have no
`INVARIANTS.md`, so the gate belongs to this repo's front where it is true. See the provenance
note in `.claude/skills/implement-github-issue/SKILL.md`.

Stdlib only; the command is read as text (INV-108).

Source issue: #50 (add `/implement-github-issue`; retire `/implement-spec`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMAND = REPO_ROOT / ".claude" / "commands" / "implement-github-issue.md"
SKILL = REPO_ROOT / ".claude" / "skills" / "implement-github-issue" / "SKILL.md"


def command_text():
    return COMMAND.read_text(encoding="utf-8")


def flat(text):
    """Collapse whitespace so a requirement still matches when its prose wraps."""
    return re.sub(r"\s+", " ", text).lower()


class TheCommandExistsAndFrontsTheSkill(unittest.TestCase):
    """Anti-vacuity: every assertion below reads this file, so it must be real."""

    def test_the_command_file_exists(self):
        self.assertTrue(
            COMMAND.is_file(),
            "%s does not exist; /implement-github-issue cannot be invoked explicitly and "
            "every assertion in this module would pass on an empty read" % COMMAND)

    def test_the_skill_resolves_in_this_project(self):
        """The command names a skill; `installed_skills()` only sees the project copy."""
        self.assertTrue(
            SKILL.is_file(),
            "%s does not exist. The skill also has a copy under ~/.claude/skills/, which no "
            "guard in this repo can see -- so without the project copy the command names a "
            "skill that resolves on one machine and nowhere else" % SKILL)


class ClosingIsGatedOnInvariantCapture(unittest.TestCase):
    """The rule, asserted as a condition rather than as a sentence (INV-219)."""

    def test_closing_and_the_deferral_appear_in_one_requirement(self):
        """Either alone is satisfiable without the gate; together they are the rule."""
        text = flat(command_text())
        gated = re.search(
            r"must not be closed until.{0,400}?deferred invariant", text) or re.search(
            r"deferred invariant.{0,400}?must not be closed until", text)
        self.assertIsNotNone(
            gated,
            "the command does not state that closing an issue is gated on invariant capture. "
            "A run may mention deferrals and still close an issue having recorded nothing, "
            "which is the #38 gap (four guarantees, eleven days) this gate exists to close")

    def test_the_third_answer_survives(self):
        """'Establishes no invariant' is a permitted answer, not a loophole to delete."""
        text = flat(command_text())
        self.assertIn(
            "establishes no invariant", text,
            "the command no longer permits 'establishes no invariant' as an explicit answer. "
            "Without it a run that genuinely shipped no durable rule must either claim one or "
            "leave the obligation open; tests/test_spec_ledger_invariants.py accepts all "
            "three answers at the ledger end and this is the same contract at the command end")

    def test_the_command_disclaims_registering(self):
        """Minting an ID is the maintainer's alone; the command must say so."""
        text = flat(command_text())
        self.assertRegex(
            text, r"cannot register an invariant|never registers an invariant",
            "the command does not disclaim its ability to register an invariant. Only the "
            "maintainer mints an ID, via /review-invariants -- a command that reads as able "
            "to register invites a run to do it unilaterally, and IDs are permanent")

    def test_the_placeholder_id_is_required(self):
        """A literal next id in a pending block turns citations.py verify red."""
        text = command_text()
        self.assertIn(
            "INV-NNN", text,
            "the command does not tell a run to write the deferred id as INV-NNN. A literal "
            "number cites an invariant that does not exist, and only the first block minted "
            "would get the id any of them named")


class ParentVersionIsScopedNotForgotten(unittest.TestCase):
    """#50 carries a clause with no referent here; silence would read as an omission."""

    def test_parent_version_is_recorded_as_child_scoped(self):
        text = flat(command_text())
        self.assertIn(
            "parent_version", text,
            "the command never mentions PARENT_VERSION. #50 requires it in CHILD repos; this "
            "is the parent and has no referent, so the decision is to scope it -- but an "
            "unmentioned clause is indistinguishable from a forgotten one to whoever ports "
            "this command to a child")

    def test_it_is_marked_unimplemented_rather_than_claimed(self):
        text = flat(command_text())
        self.assertRegex(
            text, r"deliberately unimplemented|not implemented here",
            "PARENT_VERSION is mentioned without saying it is unimplemented here, so the "
            "command reads as though it acts on something it does not touch")


if __name__ == "__main__":
    unittest.main()
