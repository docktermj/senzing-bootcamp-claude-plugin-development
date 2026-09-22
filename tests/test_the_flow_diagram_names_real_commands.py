"""Every command named in a `docs/development.md` diagram resolves, or says it does not.

`tests/test_documented_dev_commands_match_the_shipped_set.py` pins the maintainer command
set in both directions -- but it parses the numbered ``1. `/name` `` list shape and nothing
else. A command name inside a fenced ```mermaid block is invisible to it, which matters now
that the file carries flow diagrams naming a dozen commands (#55).

⛔ **The diagrams deliberately name two commands that do not ship here.** `/parity-check`
and `/escalate-to-parent` belong to the child ports; a drawing of the four-repository system
that omitted them would be wrong. So the rule cannot be "every name ships" -- it is **every
name either ships or is marked child-only**, and this module holds both halves.

⚠️ **The marker is matched per command, not per line.** Phase 1's node label carries five
commands in one label, one of which is child-only. A line-scoped check would let that one
marker vouch for the other four, and would still be green if `/feedback-to-issues` were
renamed to something that does not exist. Each occurrence is therefore scored against the
text between it and the **next** command name, capped, so a marker can only ever speak for
the command it follows.

⚠️ **HTML is stripped before names are read** (INV-282: the phrasings that must NOT be
flagged are pinned beside the ones that must). Mermaid labels carry `<br/>`, `<b>` and
`<i>`, and `</i>` read naively is a command named `/i`. `TagsAreNotCommands` pins that.

⚠️ **What this does NOT establish:** that the diagrams render, that they render the same way
on GitHub as under any local renderer, or that what they draw is a true account of the
system. Those are not properties a text scan can reach. It establishes only that no node
names a command the reader cannot run and is not told they cannot run.

Source issue: #55 (`add-a-workflow-flow-chart-to-docs-development-md`).

Stdlib only; the shipped set is discovered by glob rather than listed (INV-246).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
DEV_DOCS = REPO_ROOT / "docs" / "development.md"

#: A fenced block opened as ```mermaid, up to its closing fence.
MERMAID_BLOCK = re.compile(r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)

#: An HTML tag in a Mermaid label. Replaced by a SPACE, never removed: `</i>` read
#: naively is a command `/i`, and deleting `<br/>` between two commands splices them into
#: one token whose second half the lookbehind then rejects -- a silent miss, not a noisy one.
HTML_TAG = re.compile(r"<[^>]*>")

#: A slash command. Three characters minimum after the slash, so `and/or` is not a command;
#: not preceded by a word character or dot, so a path segment is not one either.
COMMAND = re.compile(r"(?<![\w.])/([a-z][a-z0-9-]{2,})")

#: What a node says when it names a command that ships in the children and not here.
CHILD_ONLY = re.compile(r"\(children only", re.I)

#: How far past a command name its marker may sit before it stops counting as that
#: command's marker. Comfortably wider than the longest real marker phrase.
MARKER_WINDOW = 80


def shipped_commands():
    return {"/" + p.stem for p in COMMANDS_DIR.glob("*.md")}


def diagram_blocks():
    return MERMAID_BLOCK.findall(DEV_DOCS.read_text(encoding="utf-8"))


def named_commands():
    """[(command, is_marked_child_only)] for every command occurrence in every diagram."""
    found = []
    for block in diagram_blocks():
        text = HTML_TAG.sub(" ", block)
        hits = list(COMMAND.finditer(text))
        for i, m in enumerate(hits):
            stop = hits[i + 1].start() if i + 1 < len(hits) else len(text)
            window = text[m.end():min(stop, m.end() + MARKER_WINDOW)]
            found.append(("/" + m.group(1), bool(CHILD_ONLY.search(window))))
    return found


class NothingIsEmpty(unittest.TestCase):
    """INV-265 -- every assertion below is satisfied trivially by an empty corpus."""

    def test_the_diagrams_were_found(self):
        blocks = diagram_blocks()
        self.assertGreaterEqual(
            len(blocks), 3,
            "fewer than three ```mermaid blocks were found in %s; the fence pattern has "
            "drifted from the file and every check below proves nothing" % DEV_DOCS)

    def test_commands_were_found_in_them(self):
        self.assertGreaterEqual(
            len(named_commands()), 8,
            "the diagrams parsed to fewer than eight command names; the pattern has drifted "
            "and the comparison below is vacuous")

    def test_commands_were_found_on_disk(self):
        shipped = shipped_commands()
        self.assertIn("/implement-github-issue", shipped,
                      "the command glob is missing one certainly present; the pattern is wrong")

    def test_the_child_only_branch_is_exercised(self):
        """Without a marked command, the marker half of the rule is untested and green."""
        marked = {c for c, child_only in named_commands() if child_only}
        self.assertTrue(
            marked,
            "no diagram node carries a (children only) marker, so the branch that permits a "
            "non-shipping command is never taken; the rule below is then just 'every name "
            "ships' and the marker logic is unverified")


class EveryNameResolvesOrDisclaims(unittest.TestCase):
    def test_no_node_names_a_command_that_neither_ships_nor_disclaims(self):
        shipped = shipped_commands()
        phantom = sorted({c for c, child_only in named_commands()
                          if c not in shipped and not child_only})
        self.assertEqual(
            [], phantom,
            "diagram node(s) in %s name command(s) with no file under %s and no '(children "
            "only)' marker: %s. The node reads as something the maintainer can run and "
            "invokes nothing -- mark it child-only, or fix the name"
            % (DEV_DOCS, COMMANDS_DIR, ", ".join(phantom)))

    def test_a_marked_command_really_is_absent_here(self):
        """The marker is a disclaimer, not a silencer: it must not cover a shipping command."""
        shipped = shipped_commands()
        mislabeled = sorted({c for c, child_only in named_commands()
                             if child_only and c in shipped})
        self.assertEqual(
            [], mislabeled,
            "diagram node(s) mark %s as '(children only)' while it ships under %s. The "
            "marker tells the reader not to reach for a command that is in fact available"
            % (", ".join(mislabeled), COMMANDS_DIR))


class TagsAreNotCommands(unittest.TestCase):
    """The constructions that must NOT be read as commands, pinned beside the ones that must."""

    def test_a_closing_html_tag_is_not_a_command(self):
        text = HTML_TAG.sub(" ", "<b>/review-invariants</b><br/><i>note</i>")
        self.assertEqual(["review-invariants"], COMMAND.findall(text),
                         "an HTML tag was read as a command name")

    def test_a_short_token_is_not_a_command(self):
        self.assertEqual([], COMMAND.findall("either and/or both"),
                         "'and/or' was read as a command named /or")

    def test_a_path_segment_is_not_a_command(self):
        self.assertEqual([], COMMAND.findall("plugins/senzing-bootcamp/commands"),
                         "a path segment was read as a command name")

    def test_a_real_command_still_parses(self):
        self.assertEqual(["dry-run"], COMMAND.findall('label["/dry-run"]'))

    def test_two_commands_separated_only_by_a_break_are_both_seen(self):
        """Deleting the tag rather than replacing it splices these into one token, and the
        lookbehind then rejects the second -- a miss that reports as a clean scan."""
        text = HTML_TAG.sub(" ", "/feedback-to-issues<br/>/retrofit-from-public")
        self.assertEqual(["feedback-to-issues", "retrofit-from-public"],
                         COMMAND.findall(text),
                         "a command following a <br/> was lost")


if __name__ == "__main__":
    unittest.main()
