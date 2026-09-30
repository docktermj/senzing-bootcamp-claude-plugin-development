"""Every maintainer slash command names a skill that exists.

A file under `.claude/commands/` is a thin front: it exists only to invoke a skill under
`.claude/skills/`. That indirection is the whole value of the file, and it is also the whole
failure mode -- a command whose skill has been renamed or removed still parses, still appears in
the slash-command list, and still reads as authoritative. It simply invokes nothing.

Nothing connected the two directories, so a rename on either side was silent. `docs/development.md`
demonstrated the class in prose before any command file did: it listed
`/compact-dev-development` and `/production-ready-review`, and the skills are named
`compact-dev-environment` and `production-readiness-audit`. Two names pointing at nothing,
documented as if they worked.

⚠️ **Dated note, 2026-09-30 (#262): no command ships, so this guard reads fixture commands.**
`/<name>` runs the project skill when a skill and a command share a name (measured 2026-09-29 on
Claude Code 2.1.284, #241), so the ten same-name command files never ran and #262 deleted them.
INV-303 still binds any command added later, an alias included. While `.claude/commands/` holds
no file, `_maintainer_surface.command_files_under_test()` hands this guard the fixture commands
under `tests/fixtures/maintainer-commands/` instead, so the check never passes over an empty set
(INV-265). The day a command ships again, the guard reads it and the fixtures step aside.

⚠️ **The reverse direction -- every skill has a command -- is retired (#262).** It was asserted
here as `test_every_skill_is_fronted_by_a_command` from #26 until INV-302 was narrowed on
2026-09-30 (#241): a skill need not be fronted by a command, because the skill is what `/<name>`
runs. The skill set is now compared with `docs/development.md` directly, by
`test_documented_dev_commands_match_the_shipped_set.py`.

⚠️ **A directory under `.claude/skills/` with no `SKILL.md` is not a skill**, and the skill scan
excludes it. `implement-github-issue` and `unattended-issue-loop` are defined only at user level,
under `~/.claude/skills/`, so neither is a skill or a command here, and this repository keeps only
`.claude/skill-overlays/<name>.md` for them. ⛔ The user-level copies are not checked in CI
(INV-308).

⚠️ **What a green run means.** Every skill *named* in a command file (shipped, or a fixture while
none ships) resolves to a directory with a `SKILL.md`, and no command file is silent about the
skill it fronts. It does not mean a command invokes the right skill, that the skill does what the
command claims, or that the wiring of `$ARGUMENTS` matches the skill's interface -- those need
reading. It is the phantom-reference direction only.

The command's filename stem is **not** required to equal the skill it invokes. Pinning that would
forbid an alias -- two commands onto one skill with different defaults -- for no defect ever
observed; one fixture is such an alias, so the permission is exercised.

⚠️ **Enforces INV-303**, the command→skill direction: `test_no_command_names_a_missing_skill` and
`test_every_command_names_at_least_one_skill`. `ANonConformingCommandFails` is the negative
control: a fixture command naming no real skill, or naming none, fails each assertion. INV-302's
documentation half is asserted by `test_documented_dev_commands_match_the_shipped_set.py`.

Stdlib only; the directories are listed and the command files read as text (INV-108).

Source issues: #18 (`/propagate-to-public`); #262 (fixture commands).

Run:  python3 -m unittest discover -s tests
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import _maintainer_surface as surface

SKILLS_DIR = surface.SKILLS_DIR
FIXTURES_DIR = surface.FIXTURE_COMMANDS_DIR

#: How a command file names its skill: "Invoke the `<name>` skill".
INVOCATION = re.compile(r"`([a-z0-9][a-z0-9-]*)`\s+skill")


def command_files():
    """The shipped command files, or the fixture commands while none ships (INV-265)."""
    return surface.command_files_under_test()[1]


def skills_named_by(path):
    return set(INVOCATION.findall(path.read_text(encoding="utf-8")))


def installed_skills():
    return surface.skills()


def phantom_references(paths, skills):
    """`file -> `name`` for each skill a command names that is not in `skills`."""
    return sorted("%s -> `%s`" % (path.name, name)
                  for path in paths for name in skills_named_by(path) - skills)


def silent_commands(paths):
    """Command files that name no skill at all."""
    return sorted(p.name for p in paths if not skills_named_by(p))


class NeitherSideIsEmpty(unittest.TestCase):
    """INV-265 -- a set comparison is satisfied trivially when either side is empty."""

    def test_command_files_were_found(self):
        """Non-empty is the floor: one command added later, an alias say, is a real set."""
        where, found = surface.command_files_under_test()
        self.assertTrue(
            found,
            "no command file was found in %s; the glob has drifted and the checks below prove "
            "nothing" % where)

    def test_fixtures_stand_in_only_while_no_command_ships(self):
        """The fixtures are read exactly when `.claude/commands/` holds no file."""
        where, _ = surface.command_files_under_test()
        expected = surface.COMMANDS_DIR if surface.command_files() else FIXTURES_DIR
        self.assertEqual(expected, where)

    def test_skills_were_found_on_disk(self):
        skills = installed_skills()
        self.assertGreaterEqual(
            len(skills), 3,
            "fewer than three skills were found in %s; the directory scan has drifted, and "
            "every command would report as phantom" % SKILLS_DIR)
        self.assertIn(
            "dry-run", skills,
            "the skill scan is missing one certainly present; it is looking in the wrong "
            "place or expecting the wrong layout")

    def test_the_invocation_pattern_parses(self):
        """Anchored on a fixture that fronts `dry-run`, so it cannot pass tautologically.

        Re-anchored from `implement-github-issue` at #239, which moved that file out of
        `.claude/commands/` to become a repo overlay, and onto the fixtures at #262.
        """
        anchor = FIXTURES_DIR / "dry-run-probe-only.md"
        self.assertTrue(anchor.is_file(), "%s is gone; re-anchor this test" % anchor)
        self.assertIn(
            "dry-run", skills_named_by(anchor),
            "the invocation pattern did not find the skill named in %s; command files state "
            "their skill in a shape this regex no longer matches" % anchor.name)

    def test_an_alias_is_among_the_fixtures(self):
        """The stem need not equal the skill; one fixture exercises that permission."""
        self.assertTrue(
            [p for p in surface.command_files(FIXTURES_DIR) if p.stem not in skills_named_by(p)],
            "no fixture command is an alias, so the permission INV-303 grants is unexercised")


class EverySkillNamedExists(unittest.TestCase):
    def test_no_command_names_a_missing_skill(self):
        phantom = phantom_references(command_files(), installed_skills())
        self.assertEqual(
            [], phantom,
            "command file(s) invoke a skill that does not exist under %s: %s. The command "
            "still appears in the slash-command list and still reads as authoritative; it "
            "invokes nothing" % (SKILLS_DIR, "; ".join(phantom)))

    def test_every_command_names_at_least_one_skill(self):
        """A front that names no skill is not a front -- it is a prompt with a slash on it."""
        silent = silent_commands(command_files())
        self.assertEqual(
            [], silent,
            "command file(s) name no skill to invoke: %s. Either the file states its skill "
            "in a shape this guard cannot see, or it does not front one at all"
            % ", ".join(silent))


class ANonConformingCommandFails(unittest.TestCase):
    """Negative control (#262): the fixture set plus one bad command fails each assertion."""

    def _fixtures_plus(self, name, body):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        for path in surface.command_files(FIXTURES_DIR):
            shutil.copy(path, root / path.name)
        (root / name).write_text(body, encoding="utf-8")
        return surface.command_files(root)

    def test_a_fixture_naming_no_real_skill_is_a_phantom(self):
        paths = self._fixtures_plus("phantom.md", "Invoke the `no-such-skill-262` skill.\n")
        self.assertEqual(["phantom.md -> `no-such-skill-262`"],
                         phantom_references(paths, installed_skills()))

    def test_a_fixture_naming_no_skill_is_silent(self):
        paths = self._fixtures_plus("silent.md", "Do the thing, end to end.\n")
        self.assertEqual(["silent.md"], silent_commands(paths))

    def test_the_fixtures_alone_pass(self):
        paths = surface.command_files(FIXTURES_DIR)
        self.assertEqual([], phantom_references(paths, installed_skills()))
        self.assertEqual([], silent_commands(paths))


class ADirectoryWithoutASkillMdIsNotASkill(unittest.TestCase):
    def test_a_directory_without_a_skill_md_is_not_counted(self):
        """⛔ Anti-vacuity: the exclusion must be real, not assumed."""
        stubs = [d.name for d in SKILLS_DIR.iterdir()
                 if d.is_dir() and not (d / "SKILL.md").is_file()]
        for name in stubs:
            self.assertNotIn(
                name, installed_skills(),
                "%r has no SKILL.md yet is counted as a skill, so every comparison of the "
                "skill set would demand a document entry for a directory that is not one"
                % name)


if __name__ == "__main__":
    unittest.main()
