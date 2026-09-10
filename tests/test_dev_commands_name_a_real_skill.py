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

⛔ **The reverse direction -- every skill has a command -- is deliberately NOT asserted here.**
Most maintainer skills currently have no command file, and each is being added under its own
issue. A guard demanding the full set would fail on every one of those until the last landed,
which trains its reader to expect red and to push past it. When the set is complete, that
assertion belongs here; asserting it early would make this file a nuisance rather than a check.

⚠️ **What a green run means.** Every skill *named* in a command file resolves to a directory
with a `SKILL.md`. It does not mean the command invokes the right skill, that the skill does
what the command claims, or that the wiring of `$ARGUMENTS` matches the skill's interface --
those need reading. It is the phantom-reference direction only.

The command's filename stem is **not** required to equal the skill it invokes. All three
current commands happen to match, but pinning that would forbid a future alias -- two commands
onto one skill with different defaults -- for no defect ever observed.

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


if __name__ == "__main__":
    unittest.main()
