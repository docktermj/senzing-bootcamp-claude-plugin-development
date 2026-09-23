"""Every live item in the frozen `specs/todo.md` is accounted for in the triage record.

`specs/todo.md` was the repo's future-ideas list. At the 2026-09-15 cutover it became the one
spec file in neither ledger, and #53 triaged what remained in it: six top-level bullets, three
already struck through or marked done, three live. ⛔ **`todo.md` is frozen (INV-307) and was
not edited** — the decisions live in `specs/README.md`, which is a live record.

⚠️ **This guards the RECORD, not the source.** `todo.md` cannot change, so the live set this
derives is fixed; what can change is `specs/README.md`, which is written to. A later edit that
thins the triage table -- dropping a row, or softening a decision to something that names no
disposition -- is what this catches. Saying so because a test whose input cannot vary reads as
stronger than it is.

⛔ **The live set is DERIVED by scanning, never hardcoded** (INV-246). The count 3 is asserted
as an anti-vacuity floor (INV-265), not as the subject: a parser that silently matched nothing
would satisfy every "each live item is recorded" assertion trivially, which is the failure this
repo has already shipped twice in set comparisons.

⛔ **What this does NOT establish:** that the decisions are *right*. Whether letting the web-app
suggestion go was correct, or whether #134 and #135 capture enough to act on, is judgment and is
recorded in #53. This only holds the record to the source.

Stdlib only; both files are read as text (INV-108).

Source issue: #53.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TODO = REPO_ROOT / "specs" / "todo.md"
README = REPO_ROOT / "specs" / "README.md"

#: The heading the triage record lives under, in the one file that is not frozen.
RECORD_HEADING = "## Triage of what remained here"

#: A bullet is settled when its bold lead opens with a completion marker or a strikethrough.
#: Both forms are present in `todo.md`, and the strikethrough sits INSIDE the bold, so a
#: test for a leading `~~` on the raw line finds none of them.
SETTLED = ("✅",)

#: ⚠️ A top-level bullet is a BLOCK, not a line. One item's bold lead wraps across a newline
#: ("…and neither\n  side is the plugin's.**"), so a pattern requiring the opening and closing
#: `**` on one line finds five bullets where there are six -- and the anti-vacuity floor below
#: is what caught that while this guard was being written.
TOP_LEVEL_OPENS = re.compile(r"^- \*\*")
BOLD_LEAD = re.compile(r"^- \*\*(.+?)\*\*", re.S)

#: Words too common to distinguish one item from another.
STOPWORDS = frozenset("""
    the and for with that this from into over than then they them their there here
    already still does not but its it's option rule side neither what which when
    """.split())


def top_level_bullets():
    """Every top-level bullet in `todo.md`, as (whole_block, bold_lead).

    Accumulates continuation lines so a bold lead broken over a newline is still read whole.
    """
    blocks, current = [], None
    for line in TODO.read_text(encoding="utf-8").splitlines():
        if TOP_LEVEL_OPENS.match(line):
            if current is not None:
                blocks.append(current)
            current = [line]
        elif current is not None:
            if line.startswith((" ", "\t")) or not line.strip():
                current.append(line)
            else:
                blocks.append(current)
                current = None
    if current is not None:
        blocks.append(current)

    out = []
    for block in blocks:
        text = "\n".join(block)
        m = BOLD_LEAD.match(text)
        lead = " ".join(m.group(1).split()) if m else ""
        out.append((text, lead))
    return out


def live_items():
    """The bullets #53 had to decide: neither marked done nor struck through.

    ⚠️ The markers are read from the bullet's own BOLD LEAD, not from the whole block. One
    settled bullet carries a nested `✅ SUPERSEDED` sub-bullet, so a whole-block scan would
    call it settled for the wrong reason -- and would wrongly settle a live item that ever
    grew such a note.
    """
    return [(block, lead) for block, lead in top_level_bullets()
            if lead
            and not any(mark in lead for mark in SETTLED)
            and not lead.startswith("~~")]


def tokens(text):
    """Distinctive lowercase word-stems, for matching an item against its recorded row."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) >= 4 and w not in STOPWORDS}


def record_rows():
    """The decision rows of the triage table in `specs/README.md`."""
    text = README.read_text(encoding="utf-8")
    start = text.find(RECORD_HEADING)
    if start < 0:
        return []
    section = text[start:]
    nxt = section.find("\n## ", 1)
    if nxt > 0:
        section = section[:nxt]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        if cells[0].startswith("---") or cells[0] == "Item":
            continue
        rows.append(tuple(cells))
    return rows


class TheInputsAreReal(unittest.TestCase):
    """INV-265 -- every assertion below reads these, so a silent parse of nothing must fail."""

    def test_both_files_exist(self):
        for name, path in (("todo.md", TODO), ("README.md", README)):
            with self.subTest(what=name):
                self.assertTrue(path.is_file(), "%s is missing at %s" % (name, path))

    def test_the_bullet_parser_found_the_known_set(self):
        bullets = top_level_bullets()
        self.assertEqual(
            6, len(bullets),
            "expected 6 top-level bullets in the frozen todo.md, found %d. The file cannot "
            "change (INV-307), so this means the parser drifted -- and every assertion below "
            "would then pass over the wrong set" % len(bullets))

    def test_exactly_three_items_were_live(self):
        live = live_items()
        self.assertEqual(
            3, len(live),
            "expected 3 live items, found %d: %s. Three of the six bullets carry a completion "
            "marker or a strikethrough; if the settled-bullet test has drifted, the triage "
            "record is being checked against the wrong items"
            % (len(live), [lead[:40] for _, lead in live]))

    def test_the_record_section_parsed(self):
        rows = record_rows()
        self.assertTrue(
            rows,
            "no decision rows parsed under %r in %s. Either the record was removed or its "
            "table shape changed; either way the coverage assertion below proves nothing"
            % (RECORD_HEADING, README))


class EveryLiveItemIsAccountedFor(unittest.TestCase):
    """The acceptance criterion of #53: each of the 3 is decided, and the decision is stated."""

    def test_each_live_item_matches_a_recorded_row(self):
        rows = record_rows()
        for _, lead in live_items():
            want = tokens(lead)
            hits = [item for item, _ in rows if len(tokens(item) & want) >= 2]
            with self.subTest(item=lead[:50]):
                self.assertTrue(
                    hits,
                    "the live todo.md item %r has no row in the triage record. #53 closed on "
                    "the claim that all three were decided; a record missing one makes that "
                    "claim false and leaves the item tracked nowhere" % lead[:70])

    def test_each_recorded_row_matches_a_live_item(self):
        """The other direction: a row for something todo.md never raised."""
        live = [tokens(lead) for _, lead in live_items()]
        for item, _decision in record_rows():
            want = tokens(item)
            with self.subTest(row=item[:50]):
                self.assertTrue(
                    any(len(want & got) >= 2 for got in live),
                    "the triage record carries a row %r matching no live todo.md item. The "
                    "record is the decision log for that file; an unmatched row means it has "
                    "started describing something else" % item[:70])

    def test_every_decision_names_a_disposition(self):
        """⛔ 'Decided' means let go or migrated -- never a row that merely restates the item."""
        for item, decision in record_rows():
            with self.subTest(item=item[:40]):
                let_go = "let go" in decision.lower()
                migrated = re.search(r"#\d+", decision) is not None
                self.assertTrue(
                    let_go or migrated,
                    "the row %r records no disposition. #53's acceptance required each item to "
                    "be 'migrated to an issue, or explicitly let go with the reason stated', "
                    "and %r is neither" % (item[:50], decision[:70]))

    def test_a_migrated_row_does_not_point_back_at_the_triage_issue(self):
        """#53 is the triage, not a destination; a row naming it records no onward owner."""
        for item, decision in record_rows():
            with self.subTest(item=item[:40]):
                named = set(re.findall(r"#(\d+)", decision))
                self.assertNotIn(
                    "53", named,
                    "the row %r cites #53 as its disposition. That is the issue that did the "
                    "triage -- citing it back means the item was never given an owner"
                    % item[:50])


class TheStalePointerIsGone(unittest.TestCase):
    """⚠️ The defect this run fixed: a live record pointing at work that has finished."""

    def test_the_readme_does_not_describe_the_triage_as_outstanding(self):
        text = README.read_text(encoding="utf-8")
        self.assertNotIn(
            "Triage of what remains here is issue #53", text,
            "specs/README.md still points forward at #53 as pending triage. That sentence was "
            "true until the triage completed and then reads as authoritative while being "
            "false -- the class specs/README.md itself warns about two sections earlier")


if __name__ == "__main__":
    unittest.main()
