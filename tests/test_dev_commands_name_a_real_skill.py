"""Every maintainer slash command names a skill that exists.

`.claude/commands/*.md` are thin fronts: each one exists only to invoke a skill under
`.claude/skills/` explicitly, so the maintainer reaches a release-path action by typing it
rather than by the model choosing to. That indirection is the whole value of the file, and
it is also the whole failure mode -- a command whose skill has been renamed or removed still
parses, still appears in the slash-command list, and still reads as authoritative. It simply
invokes nothing.

Nothing connected the two directories, so a rename on either side was silent. `docs/development.md`
demonstrates the class already, in prose rather than in a command file: it lists
`/compact-dev-development` and `/production-ready-review`, and the skills are named
`compact-dev-environment` and `production-readiness-audit`. Two names pointing at nothing,
documented as if they worked.

✅ **The reverse direction -- every skill has a command -- IS now asserted**, in
`EverySkillHasACommand` below. It was deliberately deferred while the commands were being added
one issue at a time (#18-#26): a guard demanding the full set would have failed on every one of
those until the last landed, which trains its reader to expect red and to push past it. #26
landed the last one, so the condition this file recorded for adding it -- "when the set is
complete" -- is met, and the deferral is discharged rather than left as a promise in prose.

⚠️ **A directory under `.claude/skills/` with no `SKILL.md` is not a skill** and is excluded
from that assertion. `implement-github-issue/` is one: the skill itself is user-level and global,
and what lives here is only its per-issue run state.

⚠️ **What a green run means.** Every skill *named* in a command file resolves to a directory
with a `SKILL.md`. It does not mean the command invokes the right skill, that the skill does
what the command claims, or that the wiring of `$ARGUMENTS` matches the skill's interface --
those need reading. It is the phantom-reference direction only.

The command's filename stem is **not** required to equal the skill it invokes. All three
current commands happen to match, but pinning that would forbid a future alias -- two commands
onto one skill with different defaults -- for no defect ever observed.

⚠️ **Enforces INV-303 and INV-302's skill-fronting half — two invariants, opposite directions.**
**INV-303** is the command→skill direction asserted by `test_no_command_names_a_missing_skill` and
`test_every_command_names_at_least_one_skill`: a command must name a skill that resolves.
**INV-302's** half is skill→command, asserted by `test_every_skill_is_fronted_by_a_command`.
⚠️ **Enforces INV-302's skill-fronting half.** It asserts that every command names a skill that
exists, that none is silent about the skill it fronts, and that every skill with a `SKILL.md` is
fronted by a command. It does **NOT** establish that a command actually invokes its skill when
typed, that the skill does what the command claims, or that `$ARGUMENTS` matches the skill's
interface — those need reading, or a live session. The documentation half is asserted by
`test_documented_dev_commands_match_the_shipped_set.py`.

Stdlib only; both directories are listed and the command files read as text (INV-108).

Source issue: #18 (`/propagate-to-public`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

#: How a command file names its skill: "Invoke the `<name>` skill".
INVOCATION = re.compile(r"`([a-z0-9][a-z0-9-]*)`\s+skill")


def command_files():
    return sorted(COMMANDS_DIR.glob("*.md"))


def skills_named_by(path):
    return set(INVOCATION.findall(path.read_text(encoding="utf-8")))


def installed_skills():
    return {d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file()}


class NeitherSideIsEmpty(unittest.TestCase):
    """INV-265 -- a set comparison is satisfied trivially when either side is empty."""

    def test_command_files_were_found(self):
        found = command_files()
        self.assertGreaterEqual(
            len(found), 3,
            "fewer than three command files were found in %s; the glob has drifted and the "
            "checks below prove nothing" % COMMANDS_DIR)

    def test_skills_were_found_on_disk(self):
        skills = installed_skills()
        self.assertGreaterEqual(
            len(skills), 3,
            "fewer than three skills were found in %s; the directory scan has drifted, and "
            "every command would report as phantom" % SKILLS_DIR)
        self.assertIn(
            "implement-spec", skills,
            "the skill scan is missing one certainly present; it is looking in the wrong "
            "place or expecting the wrong layout")

    def test_the_invocation_pattern_parses(self):
        """Anchored on a command that predates this guard, so it cannot pass tautologically."""
        anchor = COMMANDS_DIR / "implement-spec.md"
        self.assertTrue(anchor.is_file(), "%s is gone; re-anchor this test" % anchor)
        self.assertIn(
            "implement-spec", skills_named_by(anchor),
            "the invocation pattern did not find the skill named in %s; command files state "
            "their skill in a shape this regex no longer matches" % anchor.name)


class EverySkillNamedExists(unittest.TestCase):
    def test_no_command_names_a_missing_skill(self):
        skills = installed_skills()
        phantom = sorted(
            "%s -> `%s`" % (path.name, name)
            for path in command_files()
            for name in skills_named_by(path) - skills)
        self.assertEqual(
            [], phantom,
            "command file(s) invoke a skill that does not exist under %s: %s. The command "
            "still appears in the slash-command list and still reads as authoritative; it "
            "invokes nothing" % (SKILLS_DIR, "; ".join(phantom)))

    def test_every_command_names_at_least_one_skill(self):
        """A front that names no skill is not a front -- it is a prompt with a slash on it."""
        silent = sorted(p.name for p in command_files() if not skills_named_by(p))
        self.assertEqual(
            [], silent,
            "command file(s) name no skill to invoke: %s. Either the file states its skill "
            "in a shape this guard cannot see, or it does not front one at all"
            % ", ".join(silent))


class EverySkillHasACommand(unittest.TestCase):
    """The reverse direction, deferred until the set was complete and now asserted.

    A skill with no command is reachable only by the model choosing it -- which is the exact
    condition every one of #18-#26 was filed to remove. Without this, the set can silently
    regress: a new skill lands, no command is written, and nothing says so.
    """

    def test_every_skill_is_fronted_by_a_command(self):
        fronted = set()
        for path in command_files():
            fronted |= skills_named_by(path)
        orphaned = sorted(installed_skills() - fronted)
        self.assertEqual(
            [], orphaned,
            "skill(s) under %s are fronted by no command file: %s. Each is reachable only by "
            "the model choosing it, which is the condition #18-#26 were filed to remove"
            % (SKILLS_DIR, ", ".join(orphaned)))

    def test_a_directory_without_a_skill_md_is_not_counted(self):
        """⛔ Anti-vacuity in the other direction: the exclusion must be real, not assumed."""
        stubs = [d.name for d in SKILLS_DIR.iterdir()
                 if d.is_dir() and not (d / "SKILL.md").is_file()]
        for name in stubs:
            self.assertNotIn(
                name, installed_skills(),
                "%r has no SKILL.md yet is counted as a skill, so the assertion above would "
                "demand a command for a directory that is not one" % name)


if __name__ == "__main__":
    unittest.main()
