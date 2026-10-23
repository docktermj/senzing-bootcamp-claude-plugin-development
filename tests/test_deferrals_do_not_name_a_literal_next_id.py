"""A pending deferred invariant never states a literal "next free id".

`specs/IMPLEMENTED.md` accumulates `DEFERRED INVARIANT — awaiting the maintainer's sign-off`
blocks, each holding drafted wording for an invariant only the maintainer may mint. Each block
carried a parenthetical naming the next free id as a number. On 2026-09-01 there were **eight**
pending blocks and **seven** of them said *"next free id: 285"*.

285 was correct — for the first one minted, and no other. The operative instruction ("mint at
the next free id") is self-correcting; the **number** cannot survive the queue being worked,
and six of seven become wrong the moment sign-off starts while reading exactly as
authoritative as when written.

⚠️ The stale-enumeration class applied to a figure rather than a list: each copy was accurate
on the day it was written, and only the *set* is wrong — which is what makes it invisible to
review of any single block.

⛔ Scoped to **pending** blocks. `DEFERRED INVARIANT (resolved INV-NNN, …)` entries are
historical records of what a draft said before it was minted, and a number inside one is a
fact about the past. Prose *about* this defect — an audit entry quoting it — is likewise not a
deferral hint.

⚠️ **(#778) The blocks are read through `pending_invariants.blocks()`, never by a marker string.**
This file found a pending block by the "awaiting the maintainer's sign-off" marker after #770
stopped the queue doing so, so a block worded any other way -- an amendment's header, or the
"a new id is owed" wording #770 recorded -- was invisible here while `list` showed it. Every
block whose header records no decision is read now, held or pending, whatever its wording.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "specs" / "IMPLEMENTED.md"
HELPER = REPO / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"

#: "next free id: 285", "next unused id 300", "the next id is 291" — a number offered as THE id.
LITERAL_NEXT_ID = re.compile(r"(?i)next\s+(?:free|unused|available)\s+id\D{0,4}\d{2,}")


def helper(ledger=LEDGER):
    """The review queue's helper, loaded by path as `tests/test_review_invariants_queue.py` loads it."""
    spec = importlib.util.spec_from_file_location("pending_invariants", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.LEDGER = ledger
    return mod


def pending_blocks():
    """Each undecided block's text (pending or held), as the helper splits the ledger."""
    return [b["text"] for b in helper().blocks()]


def drafting_blocks():
    """The undecided blocks that draft wording, whose id is therefore written as NNN.

    ⚠️ An undecided block that drafts nothing -- the older held form, whose drafted statement
    lives in its frozen spec -- owes no NNN explanation, because it writes no id here.
    """
    mod = helper()
    return [b["text"] for b in mod.blocks() if mod.parse(b)["wording"]]


class NoPendingDeferralNamesALiteralId(unittest.TestCase):
    def test_the_scan_finds_the_pending_blocks(self):
        """A scan matching nothing would make the assertion below vacuous.

        ⚠️ Zero is legitimate ONLY when the queue is genuinely empty, which happened on
        2026-09-02 when the maintainer decided the last nine. So zero must be told apart from
        a reader that found nothing at all (#778): the same reader, asked for decided blocks
        too, must still return blocks. A reader that cannot see the ledger finds none in either
        state, and would otherwise look exactly like a finished queue.
        """
        if pending_blocks():
            return
        every_block = helper().blocks(include_resolved=True)
        self.assertGreater(
            len(every_block), 0,
            "no pending blocks AND no decided ones either: the reader found no block headers "
            "in any state, so this guard has stopped reading the maintainer's worklist — the "
            "scan is broken, not the queue empty.",
        )
        self.assertTrue(
            all(b["resolved"] for b in every_block),
            "the reader returned undecided blocks with include_resolved=True and none without "
            "it — the queue filter is broken, not the queue empty.",
        )

    def test_no_pending_block_states_a_literal_next_free_id(self):
        offenders = []
        for block in pending_blocks():
            m = LITERAL_NEXT_ID.search(block)
            if m:
                offenders.append(m.group(0))
        self.assertEqual(
            [], offenders,
            "A pending deferral names a literal next-free id. At most one pending block can be "
            "right about that number, and the rest go wrong silently the moment sign-off "
            "starts. Say 'mint at the next free id, read it off INVARIANTS.md' instead. "
            "Found: %r" % offenders,
        )

    def test_the_blocks_still_explain_why_the_id_is_written_as_NNN(self):
        """⛔ The reason is real and must not be lost with the number.

        A literal id in a deferral turns `citations.py verify` red, because it reads as a
        citation of an invariant that does not exist. Dropping that explanation would invite
        the next author to write the id in.
        """
        for block in drafting_blocks():
            with self.subTest(block=block[:60]):
                self.assertRegex(
                    block, r"(?i)written as NNN deliberately",
                    "Every pending deferral must still say why the id is written as NNN. "
                    "Removing the number without the reason is how it comes back.",
                )

    def test_the_instruction_to_read_the_id_off_the_ruleset_is_present(self):
        for block in drafting_blocks():
            with self.subTest(block=block[:60]):
                self.assertRegex(
                    block, r"(?i)read it off `INVARIANTS\.md`",
                    "Each block must tell the maintainer where the real next id lives, since "
                    "the number is no longer written here.",
                )


class TheGuardSeesEveryHeaderWording(unittest.TestCase):
    """⛔ (#778) A pending block is read whatever its header says, not only the marker form."""

    def test_a_literal_id_under_an_unmarked_header_is_seen(self):
        for header in ("DEFERRED INVARIANT — a new id is owed; NOT minted.",
                       "PROPOSED AMENDMENT to INV-216 — draft."):
            with self.subTest(header=header), tempfile.TemporaryDirectory() as tmp:
                ledger = Path(tmp) / "IMPLEMENTED.md"
                ledger.write_text(
                    "# Implemented\n\n## a-spec\n\n- **%s** Mint at the next free id: 285.\n"
                    % header, encoding="utf-8")
                texts = [b["text"] for b in helper(ledger).blocks()]
                self.assertEqual(1, len(texts), "the helper did not read the fixture block")
                self.assertRegex(texts[0], LITERAL_NEXT_ID)


class ResolvedDeferralsAreLeftAlone(unittest.TestCase):
    """A number inside a resolved block is a fact about the past, not a stale hint."""

    def test_resolved_blocks_are_not_scanned(self):
        text = LEDGER.read_text(encoding="utf-8")
        resolved = re.findall(r"DEFERRED INVARIANT \(resolved INV-\d+", text)
        if not resolved:
            self.skipTest("no resolved deferrals recorded yet")
        for block in pending_blocks():
            self.assertNotIn(
                "(resolved INV-", block[:80],
                "the pending-block scan picked up a resolved deferral; those record what a "
                "draft said before it was minted and must not be rewritten",
            )


if __name__ == "__main__":
    unittest.main()
