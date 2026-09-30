"""The documented maintainer-operation set equals the shipped one, in both directions.

`tests/test_documented_commands_match_the_shipped_set.py` pins exactly this contract for the
**bootcamper** surface -- `plugins/senzing-bootcamp/commands/` against the table in
`docs/README.md`. The **maintainer** surface had no equivalent, and nothing read
`docs/development.md` at all, so it drifted in both directions at once:

    docs/development.md:119  `/compact-dev-development`   <- no skill and no command by that name
    docs/development.md:118  `/delegate-to-mcp-server`    <- documented, command did not exist
    review-invariants, unattended-spec-loop               <- shipped, documented nowhere

⛔ **The sibling's docstring records that this class already recurred once** because the fix
"wrote the missing rows instead of pinning the set". Four PRs (#22, #23, #24, #25, #26) then
corrected these rows one at a time, which is the same shape again -- correct each time, and
load-bearing on nobody re-introducing a row. This test pins the sets so the next one fails
instead.

⛔ **No count is asserted anywhere in this file, deliberately.** A test pinning "eleven
commands" fails on the next legitimate addition and teaches whoever fixes it to bump a number,
reproducing the defect inside the guard. The two sets are derived and compared; their size is
not the subject.

⚠️ **Both directions matter, and they fail differently.** A documented command that does not
ship tells the maintainer to run something that does not exist -- the phantom above, which
survived long enough for a test docstring to cite it as a worked example. A shipped command
documented nowhere is simply undiscoverable.

⚠️ **This parses prose, not a table.** `docs/development.md` is a maintainer-facing list, so the
parser keys on the ``1. `/name` `` line shape. Restructuring that list breaks this guard
loudly rather than letting it pass silently, which is the right failure direction.

⚠️ **Enforces INV-302**, and not all of it. This module asserts the documentation half: both set
directions, that no entry is bare, and that the docs state no count. It does **NOT** assert
INV-302's clause that *the guard itself* must not pin a count — that clause governs this file's
own source and is marked unassertable in the invariant rather than pretended to.

⚠️ **Dated note, 2026-09-30 (#262): the shipped set is the skills, together with any command.**
INV-302 was narrowed on 2026-09-30 (#241): `/<name>` runs the project skill when a skill and a
command share a name (measured 2026-09-29, Claude Code 2.1.284), so a skill need not be fronted
by a command, and the set compared with `docs/development.md` is every skill under
`.claude/skills/` together with any command under `.claude/commands/`. #262 deleted the ten
same-name command files, so today the set is the skills alone. It is read from
`tests/_maintainer_surface.py`, the one place the "commands or skills" reading lives (INV-300).
The skill-fronting half this module's sibling asserted until #262 is retired with the clause.

⚠️ **A name may ship at user level instead (#239).** `implement-github-issue` and
`unattended-issue-loop` are defined only under `~/.claude/skills/`, and this repository keeps
their obligations in `.claude/skill-overlays/<name>.md`. Their entries carry the marker
*(user level)* right after the name (INV-316: at the point of use, per name). ⛔ **The marker is
a disclaimer, not a silencer**: it is accepted only when `.claude/skill-overlays/<name>.md`
exists **and** no command or skill of that name ships here. On a name that still ships, or
with no overlay behind it, it fails. ⚠️ `~/.claude/skills/` is **not checked in CI** (INV-308),
so nothing here establishes that the user-level skill exists on any machine; the overlay is
what this repository can check.

Stdlib only; both directories are listed and the docs read as text (INV-108).

Source issues: #39 (`the-dev-command-list-has-drifted-from-the-shipped-set`); #239 (the
*(user level)* marker).

Run:  python3 -m unittest discover -s tests
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import _maintainer_surface as surface

REPO_ROOT = surface.REPO_ROOT
COMMANDS_DIR = surface.COMMANDS_DIR
SKILLS_DIR = surface.SKILLS_DIR
OVERLAYS_DIR = surface.OVERLAYS_DIR
DEV_DOCS = REPO_ROOT / "docs" / "development.md"

#: A list entry: ``1. `/name` - description``. The description is captured to assert it exists.
ENTRY = re.compile(r"^\s*1\.\s+`(/[a-z0-9-]+)`(.*)$", re.M)

#: Prose asserting how many maintainer commands there are -- the habit the sibling refuses.
COUNT_CLAIM = re.compile(
    r"(?i)(?:ships|are|have)\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)"
    r"\s+(?:development\s+|maintainer\s+|dev\s+)?slash\s+commands")


#: The marker that says a name ships at user level, directly after the name (INV-316).
USER_LEVEL = re.compile(r"^\s*\*?\(user level\)\*?")


def shipped_commands():
    """Every shipped maintainer operation, as `/name`: each skill, together with any command."""
    return {"/" + name for name in surface.operations()}


def user_level_entries():
    """Documented commands whose entry carries the *(user level)* marker."""
    return {cmd for cmd, desc in documented_entries().items() if USER_LEVEL.match(desc)}


def user_level_problems(commands, commands_dir, overlays_dir, skills_dir=SKILLS_DIR):
    """Why each *(user level)* name is not one: it still ships here, or no overlay backs it."""
    problems = []
    for cmd in sorted(commands):
        name = cmd.lstrip("/")
        if surface.ships(name, commands_dir, skills_dir):
            problems.append("%s: marked (user level) but a command under %s or a skill under %s "
                            "ships, so the marker would silence a live operation"
                            % (cmd, commands_dir, skills_dir))
        if not (overlays_dir / ("%s.md" % name)).is_file():
            problems.append("%s: marked (user level) but %s is missing, so the name points "
                            "nowhere this repository can check" % (cmd, overlays_dir / ("%s.md" % name)))
    return problems


def documented_entries():
    """{command: description text} parsed from the development-loop lists."""
    return {m.group(1): m.group(2).strip()
            for m in ENTRY.finditer(DEV_DOCS.read_text(encoding="utf-8"))}


class NeitherSetIsEmpty(unittest.TestCase):
    """INV-265 -- a set comparison is satisfied trivially when either side is empty."""

    def test_operations_were_found_on_disk(self):
        shipped = shipped_commands()
        self.assertGreaterEqual(
            len(shipped), 3,
            "fewer than three maintainer operations were found under %s and %s; the scan has "
            "drifted and the comparison below proves nothing" % (SKILLS_DIR, COMMANDS_DIR))
        self.assertIn("/dry-run", shipped,
                      "the operation scan is missing one certainly present; the pattern is wrong")

    def test_the_docs_list_parsed(self):
        documented = documented_entries()
        self.assertGreaterEqual(
            len(documented), 3,
            "the command list in docs/development.md parsed to fewer than three entries; the "
            "line pattern has drifted from the list's shape")
        self.assertIn("/dry-run", documented)

    def test_the_user_level_branch_is_exercised(self):
        """INV-265 -- the marker branch below is vacuous if no entry carries the marker."""
        self.assertIn("/implement-github-issue", user_level_entries(),
                      "no docs/development.md entry carries the (user level) marker; the branch "
                      "that checks it proves nothing")


class TheTwoSetsAgree(unittest.TestCase):
    def test_every_shipped_command_is_documented(self):
        missing = sorted(shipped_commands() - set(documented_entries()))
        self.assertEqual(
            [], missing,
            "maintainer operation(s) ship as a skill or command but are absent from "
            "docs/development.md: %s. They are undiscoverable to anyone reading the development "
            "docs" % ", ".join(missing))

    def test_every_documented_command_ships(self):
        """The phantom direction: the reader told to run something that does not exist."""
        phantom = sorted(set(documented_entries()) - shipped_commands() - user_level_entries())
        self.assertEqual(
            [], phantom,
            "docs/development.md documents command(s) with no skill under %s and no command "
            "under %s: %s. The entry reads as authoritative and invokes nothing"
            % (SKILLS_DIR, COMMANDS_DIR, ", ".join(phantom)))


class AUserLevelMarkerIsADisclaimerNotASilencer(unittest.TestCase):
    """INV-316 -- the marker is accepted only with an overlay here and nothing shipping here."""

    def test_every_marked_name_really_ships_at_user_level(self):
        problems = user_level_problems(user_level_entries(), COMMANDS_DIR, OVERLAYS_DIR)
        self.assertEqual([], problems, "\n".join(problems))

    def _tree(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        commands, overlays, skills = root / "commands", root / "skill-overlays", root / "skills"
        commands.mkdir()
        overlays.mkdir()
        skills.mkdir()
        (overlays / "demo.md").write_text("overlay\n", encoding="utf-8")
        return commands, overlays, skills

    def test_a_well_formed_user_level_name_passes(self):
        commands, overlays, skills = self._tree()
        self.assertEqual([], user_level_problems({"/demo"}, commands, overlays, skills))

    def test_the_marker_fails_when_the_overlay_is_missing(self):
        commands, overlays, skills = self._tree()
        (overlays / "demo.md").unlink()
        self.assertEqual(1, len(user_level_problems({"/demo"}, commands, overlays, skills)))

    def test_the_marker_fails_on_a_command_that_still_ships(self):
        commands, overlays, skills = self._tree()
        (commands / "demo.md").write_text("command\n", encoding="utf-8")
        self.assertEqual(1, len(user_level_problems({"/demo"}, commands, overlays, skills)))

    def test_the_marker_fails_on_a_skill_that_ships(self):
        """#262: a skill is a shipped operation too (INV-316's 2026-09-30 note)."""
        commands, overlays, skills = self._tree()
        (skills / "demo").mkdir()
        (skills / "demo" / "SKILL.md").write_text("skill\n", encoding="utf-8")
        self.assertEqual(1, len(user_level_problems({"/demo"}, commands, overlays, skills)))


class ASkillMissingFromTheListFails(unittest.TestCase):
    """Negative control (#262): the shipped direction reads the skills, not only the commands."""

    def test_a_shipped_skill_absent_from_the_docs_is_reported(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        (root / "skills" / "undocumented-262").mkdir(parents=True)
        (root / "skills" / "undocumented-262" / "SKILL.md").write_text("x\n", encoding="utf-8")
        shipped = {"/" + n for n in surface.operations(root / "commands", root / "skills")}
        self.assertEqual(["/undocumented-262"], sorted(shipped - set(documented_entries())))


class EveryEntryCarriesADescription(unittest.TestCase):
    """An entry with a bare name tells the reader the command exists and nothing else."""

    def test_no_entry_is_bare(self):
        bare = sorted(cmd for cmd, desc in documented_entries().items()
                      if not desc.lstrip("- ").strip())
        self.assertEqual(
            [], bare,
            "docs/development.md entr(ies) name a command with no description: %s. Every other "
            "entry carries one, so a bare name reads as an omission rather than a choice"
            % ", ".join(bare))


class NoCountIsStated(unittest.TestCase):
    """A count in prose is a positive false statement the moment a command is added."""

    def test_the_dev_docs_state_no_count(self):
        hit = COUNT_CLAIM.search(DEV_DOCS.read_text(encoding="utf-8"))
        self.assertIsNone(
            hit, "docs/development.md states a number of slash commands (%r); state the set, "
                 "not a count -- the number goes stale silently while reading authoritative"
                 % (hit.group(0) if hit else ""))


if __name__ == "__main__":
    unittest.main()
