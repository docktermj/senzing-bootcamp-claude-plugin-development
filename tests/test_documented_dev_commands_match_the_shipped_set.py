"""The documented maintainer-command set equals the shipped one, in both directions.

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
own source and is marked unassertable in the invariant rather than pretended to. The
skill-fronting half is asserted by `test_dev_commands_name_a_real_skill.py`.

⚠️ **A name may ship at user level instead (#239).** `implement-github-issue` and
`unattended-issue-loop` are defined only under `~/.claude/skills/`, and this repository keeps
their obligations in `.claude/skill-overlays/<name>.md`. Their entries carry the marker
*(user level)* right after the name (INV-316: at the point of use, per name). ⛔ **The marker is
a disclaimer, not a silencer**: it is accepted only when `.claude/skill-overlays/<name>.md`
exists **and** `.claude/commands/<name>.md` does not. On a name that still ships a command, or
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

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
OVERLAYS_DIR = REPO_ROOT / ".claude" / "skill-overlays"
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
    return {"/" + p.stem for p in COMMANDS_DIR.glob("*.md")}


def user_level_entries():
    """Documented commands whose entry carries the *(user level)* marker."""
    return {cmd for cmd, desc in documented_entries().items() if USER_LEVEL.match(desc)}


def user_level_problems(commands, commands_dir, overlays_dir):
    """Why each *(user level)* name is not one: a command still ships, or no overlay backs it."""
    problems = []
    for cmd in sorted(commands):
        name = cmd.lstrip("/")
        if (commands_dir / ("%s.md" % name)).exists():
            problems.append("%s: marked (user level) but %s ships, so the marker would silence "
                            "a live command" % (cmd, commands_dir / ("%s.md" % name)))
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

    def test_commands_were_found_on_disk(self):
        shipped = shipped_commands()
        self.assertGreaterEqual(
            len(shipped), 3,
            "fewer than three command files were found in %s; the glob has drifted and the "
            "comparison below proves nothing" % COMMANDS_DIR)
        self.assertIn("/dry-run", shipped,
                      "the command glob is missing one certainly present; the pattern is wrong")

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
            "maintainer command(s) ship but are absent from docs/development.md: %s. They are "
            "undiscoverable to anyone reading the development docs" % ", ".join(missing))

    def test_every_documented_command_ships(self):
        """The phantom direction: the reader told to run something that does not exist."""
        phantom = sorted(set(documented_entries()) - shipped_commands() - user_level_entries())
        self.assertEqual(
            [], phantom,
            "docs/development.md documents command(s) with no file under %s: %s. The entry "
            "reads as authoritative and invokes nothing" % (COMMANDS_DIR, ", ".join(phantom)))


class AUserLevelMarkerIsADisclaimerNotASilencer(unittest.TestCase):
    """INV-316 -- the marker is accepted only with an overlay here and no command here."""

    def test_every_marked_name_really_ships_at_user_level(self):
        problems = user_level_problems(user_level_entries(), COMMANDS_DIR, OVERLAYS_DIR)
        self.assertEqual([], problems, "\n".join(problems))

    def _tree(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        commands, overlays = root / "commands", root / "skill-overlays"
        commands.mkdir()
        overlays.mkdir()
        (overlays / "demo.md").write_text("overlay\n", encoding="utf-8")
        return commands, overlays

    def test_a_well_formed_user_level_name_passes(self):
        commands, overlays = self._tree()
        self.assertEqual([], user_level_problems({"/demo"}, commands, overlays))

    def test_the_marker_fails_when_the_overlay_is_missing(self):
        commands, overlays = self._tree()
        (overlays / "demo.md").unlink()
        self.assertEqual(1, len(user_level_problems({"/demo"}, commands, overlays)))

    def test_the_marker_fails_on_a_command_that_still_ships(self):
        commands, overlays = self._tree()
        (commands / "demo.md").write_text("command\n", encoding="utf-8")
        self.assertEqual(1, len(user_level_problems({"/demo"}, commands, overlays)))


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
