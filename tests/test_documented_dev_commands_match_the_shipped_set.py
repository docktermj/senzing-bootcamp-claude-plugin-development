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

Stdlib only; both directories are listed and the docs read as text (INV-108).

Source issue: #39 (`the-dev-command-list-has-drifted-from-the-shipped-set`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
DEV_DOCS = REPO_ROOT / "docs" / "development.md"

#: A list entry: ``1. `/name` - description``. The description is captured to assert it exists.
ENTRY = re.compile(r"^\s*1\.\s+`(/[a-z0-9-]+)`(.*)$", re.M)

#: Prose asserting how many maintainer commands there are -- the habit the sibling refuses.
COUNT_CLAIM = re.compile(
    r"(?i)(?:ships|are|have)\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)"
    r"\s+(?:development\s+|maintainer\s+|dev\s+)?slash\s+commands")


def shipped_commands():
    return {"/" + p.stem for p in COMMANDS_DIR.glob("*.md")}


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
        self.assertIn("/implement-github-issue", shipped,
                      "the command glob is missing one certainly present; the pattern is wrong")

    def test_the_docs_list_parsed(self):
        documented = documented_entries()
        self.assertGreaterEqual(
            len(documented), 3,
            "the command list in docs/development.md parsed to fewer than three entries; the "
            "line pattern has drifted from the list's shape")
        self.assertIn("/implement-github-issue", documented)


class TheTwoSetsAgree(unittest.TestCase):
    def test_every_shipped_command_is_documented(self):
        missing = sorted(shipped_commands() - set(documented_entries()))
        self.assertEqual(
            [], missing,
            "maintainer command(s) ship but are absent from docs/development.md: %s. They are "
            "undiscoverable to anyone reading the development docs" % ", ".join(missing))

    def test_every_documented_command_ships(self):
        """The phantom direction: the reader told to run something that does not exist."""
        phantom = sorted(set(documented_entries()) - shipped_commands())
        self.assertEqual(
            [], phantom,
            "docs/development.md documents command(s) with no file under %s: %s. The entry "
            "reads as authoritative and invokes nothing" % (COMMANDS_DIR, ", ".join(phantom)))


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
