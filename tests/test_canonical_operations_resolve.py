"""The family's canonical operations resolve, and the two maintainer pages do not restate each other.

`docs/FAMILY_WORKFLOW.md` (#111) is the family-wide normative workflow that the Kiro, ChatGPT,
Copilot and Gemini ports cite by rule number. Its §2 table reserves the **canonical operation
names** family-wide, and R4 makes the point this module has to honor: *the name is the
invariant; the invocation mechanism is the host's business*. So the page names operations
**without a leading slash** -- `parity-check`, not `/parity-check`.

⛔ **That is why this guard could not simply be pointed at the new page.** It began (#55) as
`test_the_flow_diagram_names_real_commands.py`, matching ``/name`` inside fenced diagrams in
`docs/development.md`. Aimed at `FAMILY_WORKFLOW.md` unchanged it would have matched **zero**
names and reported success -- coverage that is really a no-op, which is the defect class the
surrounding work keeps finding. It was renamed and re-aimed instead.

What it holds now:

* **The table against the shipped set, both directions.** Every operation the table marks
  `required` for the parent has a file in `.claude/commands/`; every operation the table marks
  as having no parent counterpart (`—`) does **not**. The second direction matters as much as
  the first: `parity-check` and `escalate-to-parent` are child-only, and a parent that quietly
  grew one would contradict the table four repositories read.
* **The diagrams against the table.** A hyphenated single-token operation named in a mermaid
  block must appear in the table, so a drawing cannot invent an operation.
* **`docs/development.md` against the one-home rule.** It must link to the family page and must
  carry no diagrams of its own -- the restatement INV-300 forbids, and which had already gone
  wrong: until #111 its topology said *"one of three"* children while the family had four.
* **Its slash-command references.** Every ``/name`` there ships or is marked *(children only)*.

⚠️ **Where the diagram check stops**, stated rather than papered over, because a guard whose
reach is unstated gets read as total (INV-308). It reads an operation as a `<br/>`-separated
item that IS a single hyphenated token. So it does not see an operation embedded in a phrase
(*"via escalate-to-parent"*), nor a one-word operation (`release`) -- and it deliberately does
not see a hyphenated adjective that merely appears in prose, which is what the first attempt
got wrong, flagging `cross-repo`, `host-behavior`, `parent-owned` and `unattended-ok`. **The
table half is exact in both directions**; the diagram half catches an invented operation
written the way the diagrams write them.

Source issues: #55 (original), #111 (re-aimed).

Stdlib only; both directories are listed and the docs read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
IMPLEMENT_CMD = REPO_ROOT / ".claude" / "commands" / "implement-github-issue.md"
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"
DEV_DOCS = REPO_ROOT / "docs" / "development.md"

#: A row of the §2 canonical-operation table: | `name` | phase | parent | children | boundary |
TABLE_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|([^|]*)\|([^|]*)\|([^|]*)\|", re.M)

#: A fenced block opened as ```mermaid, up to its closing fence.
MERMAID_BLOCK = re.compile(r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)

#: An HTML tag in a Mermaid label. Replaced by a SPACE, never removed: deleting `<br/>` between
#: two names splices them into one token (#105's lesson, in the sibling guard).
HTML_TAG = re.compile(r"<[^>]*>")

#: A slash command in prose. Three characters minimum after the slash, so `and/or` is not one;
#: not preceded by a word character or dot, so a path segment is not either.
COMMAND = re.compile(r"(?<![\w.])/([a-z][a-z0-9-]{2,})")

#: An operation as a diagram spells it: one token, at least one hyphen, no slash.
DIAGRAM_OP = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")

#: What a node says when it names an operation that ships in the children and not here.
CHILD_ONLY = re.compile(r"\(children only", re.I)

#: What the page says when it names a command this repository USED to ship. ⛔ A third
#: disposition, added because the page legitimately discusses retired commands and forcing a
#: retired name into "ships" or "child-only" is the two-bucket mistake #110 documents: the
#: categories have to match what the corpus actually contains.
RETIRED = re.compile(r"\b(was |were |now )?retired\b", re.I)

#: A fenced code block. Stripped before scanning: `/usr/bin/python3` inside a ```text sample is
#: a path in a transcript, not a command this repository claims to ship.
FENCE = re.compile(r"^```.*?^```", re.M | re.S)

#: The literal placeholder used when the page describes the LIST SHAPE rather than a command.
#: Precedent: `tests/test_comment_test_pointers_resolve.py` excludes `test_x.py` the same way.
PLACEHOLDERS = {"/name"}

MARKER_WINDOW = 80


def shipped():
    return {p.stem for p in COMMANDS_DIR.glob("*.md")}


def table():
    """{operation: (parent_cell, children_cell)} from the §2 canonical-operation table."""
    return {m.group(1): (m.group(3).strip(), m.group(4).strip())
            for m in TABLE_ROW.finditer(FAMILY.read_text(encoding="utf-8"))}


def diagram_operations():
    """Operations named as a line of their own inside the family page's mermaid blocks.

    ⚠️ A node lists its operations one per `<br/>`, so an item that IS a single hyphenated
    token is an operation and an item that merely CONTAINS one -- "the only cross-repo write
    path", "on unattended-ok issues only" -- is prose. Splitting on the break first is what
    tells them apart; scanning every token in the block does not, and flagged four adjectives
    on the first run.
    """
    found = set()
    for block in MERMAID_BLOCK.findall(FAMILY.read_text(encoding="utf-8")):
        for item in re.split(r"<br\s*/?>", block):
            bare = HTML_TAG.sub(" ", item)
            bare = re.sub(r"\(.*?\)", " ", bare)          # drop (children only) and friends
            bare = bare.strip(" \"[]|{}·—-<>\n\t")
            if DIAGRAM_OP.match(bare):
                found.add(bare)
    return found


def slash_commands(path):
    """[(command, disclaimed)] for each ``/name`` occurrence in `path`'s prose.

    `disclaimed` is true when the name carries a marker saying it does not ship here -- either
    *(children only)* or a statement that it was retired.
    """
    text = HTML_TAG.sub(" ", FENCE.sub(" ", path.read_text(encoding="utf-8")))
    hits = list(COMMAND.finditer(text))
    out = []
    for i, m in enumerate(hits):
        stop = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        window = text[m.end():min(stop, m.end() + MARKER_WINDOW)]
        name = "/" + m.group(1)
        if name in PLACEHOLDERS:
            continue
        out.append((name, bool(CHILD_ONLY.search(window) or RETIRED.search(window))))
    return out


class NothingIsEmpty(unittest.TestCase):
    """INV-265 -- every comparison below is satisfied trivially by an empty corpus."""

    def test_the_operation_table_parsed(self):
        ops = table()
        self.assertGreaterEqual(
            len(ops), 10,
            "the canonical-operation table in %s parsed to fewer than ten rows; its shape has "
            "drifted and every check below proves nothing" % FAMILY)
        self.assertIn("implement-github-issue", ops)

    def test_commands_were_found_on_disk(self):
        self.assertIn("implement-github-issue", shipped(),
                      "the command glob is missing one certainly present; the pattern is wrong")

    def test_the_family_page_carries_diagrams(self):
        self.assertGreaterEqual(len(MERMAID_BLOCK.findall(FAMILY.read_text(encoding="utf-8"))), 3)


class TheTableAgreesWithTheShippedSet(unittest.TestCase):
    def test_every_parent_required_operation_ships(self):
        missing = sorted(op for op, (parent, _) in table().items()
                         if "required" in parent and op not in shipped())
        self.assertEqual(
            [], missing,
            "%s marks operation(s) required for the parent that have no file under %s: %s. "
            "Four child repositories read this table as normative"
            % (FAMILY, COMMANDS_DIR, ", ".join(missing)))

    def test_no_child_only_operation_ships_here(self):
        """The direction that catches the parent quietly growing a child-only operation."""
        wrong = sorted(op for op, (parent, _) in table().items()
                       if parent in {"—", "-", ""} and op in shipped())
        self.assertEqual(
            [], wrong,
            "%s records operation(s) as having no parent counterpart, but they ship under %s: "
            "%s. The table and the repository disagree" % (FAMILY, COMMANDS_DIR, ", ".join(wrong)))


class TheDiagramsAgreeWithTheTable(unittest.TestCase):
    def test_every_operation_drawn_is_in_the_table(self):
        unknown = sorted(diagram_operations() - set(table()))
        self.assertEqual(
            [], unknown,
            "mermaid block(s) in %s name operation-shaped token(s) absent from the §2 table: "
            "%s. Either the table is missing an operation or a diagram invented one"
            % (FAMILY, ", ".join(unknown)))


class TheTwoPagesDoNotRestateEachOther(unittest.TestCase):
    """INV-300 -- a rule with two homes is a rule that will disagree with itself."""

    def test_development_md_links_to_the_family_page(self):
        self.assertIn("FAMILY_WORKFLOW.md", DEV_DOCS.read_text(encoding="utf-8"),
                      "docs/development.md does not link to the normative family page")

    def test_development_md_carries_no_diagrams_of_its_own(self):
        blocks = MERMAID_BLOCK.findall(DEV_DOCS.read_text(encoding="utf-8"))
        self.assertEqual(
            [], blocks,
            "docs/development.md carries %d mermaid block(s). The family page is the normative "
            "home for them, and the two already disagreed once -- the topology here said "
            "'one of three' children while the family had grown to four" % len(blocks))


class EverySlashCommandResolvesOrDisclaims(unittest.TestCase):
    def test_development_md_names_no_phantom_command(self):
        phantom = sorted({c for c, child_only in slash_commands(DEV_DOCS)
                          if c.lstrip("/") not in shipped() and not child_only})
        self.assertEqual(
            [], phantom,
            "docs/development.md names command(s) with no file under %s and no marker saying "
            "so -- neither '(children only)' nor a statement that it was retired: %s"
            % (COMMANDS_DIR, ", ".join(phantom)))

    def test_a_marked_command_really_is_absent_here(self):
        mislabeled = sorted({c for c, child_only in slash_commands(DEV_DOCS)
                             if child_only and c.lstrip("/") in shipped()})
        self.assertEqual(
            [], mislabeled,
            "docs/development.md marks %s as '(children only)' while it ships under %s"
            % (", ".join(mislabeled), COMMANDS_DIR))

    def test_the_child_only_branch_is_exercised(self):
        """Without a marked command the marker half is untested and green."""
        self.assertTrue(
            {c for c, m in slash_commands(DEV_DOCS) if m},
            "no command in docs/development.md carries a (children only) marker, so the branch "
            "permitting a non-shipping command is never taken and the rule is unverified")


class R8HasOneHome(unittest.TestCase):
    """INV-300 -- the command restates a family rule, so it must name where the rule lives.

    ⚠️ **This class has changed subject twice, which is the point of keeping it.** At #111 R8 and
    the command disagreed about whether *recommending* was allowed, and the command was brought
    up to R8's ban. At #119 the maintainer **removed that ban** and required a dependency report
    instead, so the assertions moved with the rule rather than being deleted. What survives in
    both directions is that the two texts cannot drift apart silently.

    ⛔ **The user-global skill is deliberately NOT asserted here.**
    `~/.claude/skills/implement-github-issue/SKILL.md` carries the same procedure and lives
    outside this repository, so CI -- which checks out only the repo -- would fail on its
    absence. It is therefore unguarded, and that gap is recorded in the ledger rather than
    papered over with a test that passes only on one machine.
    """

    def test_the_command_requires_a_dependency_report(self):
        text = IMPLEMENT_CMD.read_text(encoding="utf-8")
        self.assertRegex(
            text, r"(?i)review the open issues for dependencies",
            "%s does not require reviewing the open issues for dependencies before asking, "
            "which amended R8 (#119) makes mandatory" % IMPLEMENT_CMD)

    def test_the_command_still_forbids_picking(self):
        """The clause R8 KEPT when it dropped the recommendation ban."""
        text = IMPLEMENT_CMD.read_text(encoding="utf-8")
        self.assertRegex(
            text, r"(?i)do not pick",
            "%s no longer forbids picking an issue. R8 gave up 'does not recommend' at #119 and "
            "kept 'does not pick' -- the command may advise and may not act on its own advice"
            % IMPLEMENT_CMD)

    def test_the_command_names_the_family_rule(self):
        text = IMPLEMENT_CMD.read_text(encoding="utf-8")
        self.assertIn(
            "FAMILY_WORKFLOW.md", text,
            "%s restates family rule R8 without naming where the rule lives, so the two can "
            "drift with nothing pointing from one to the other (INV-300)" % IMPLEMENT_CMD)


class TagsAreNotCommands(unittest.TestCase):
    """The constructions that must NOT be read as names, pinned beside the ones that must."""

    def test_a_closing_html_tag_is_not_a_command(self):
        self.assertEqual(["review-invariants"],
                         COMMAND.findall(HTML_TAG.sub(" ", "<b>/review-invariants</b><i>x</i>")))

    def test_a_short_token_is_not_a_command(self):
        self.assertEqual([], COMMAND.findall("either and/or both"))

    def test_a_path_segment_is_not_a_command(self):
        self.assertEqual([], COMMAND.findall("plugins/senzing-bootcamp/commands"))

    def test_a_repository_name_is_not_an_operation(self):
        self.assertFalse(DIAGRAM_OP.match("kiro power"), "a two-word phrase is not an operation")
        self.assertTrue(DIAGRAM_OP.match("parity-check"))

    def test_a_single_word_is_not_read_as_an_operation(self):
        """`manual` appears in the flow diagram and is not an operation."""
        self.assertFalse(DIAGRAM_OP.match("manual"))


if __name__ == "__main__":
    unittest.main()
