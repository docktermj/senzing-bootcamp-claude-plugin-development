"""`pending_invariants.py` counts deferral BLOCKS, not lines that mention deferrals.

The helper exists because a hand count of pending invariants on 2026-09-01 returned **29**
against a true **11**: it grepped `specs/IMPLEMENTED.md` for the phrase "DEFERRED
INVARIANT", and ledger prose *about* deferrals -- audit summaries, "INVARIANT REGISTERED"
entries quoting the term, a bullet explaining the deferral convention -- matched too.

The first version of the helper reproduced that same overcount (25 against 9), because it
kept any bullet containing the phrase rather than any block carrying the sign-off MARKER.
Twice in one day, in the fix for itself, is the argument for pinning it here.

This asserts the count by a **different mechanism** than the helper uses: a flat scan for
the marker string, versus the helper's block splitting. Agreement between two mechanisms
is evidence; re-running the helper's own logic would not be.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

⛔ **(#770) The scan counts HEADERS that are not decided, never the sign-off marker.** It
counted blocks carrying the "awaiting the maintainer's sign-off" marker, the same definition the
helper used, so when seven blocks were written with a header reading "a new id is owed …; NOT
minted" both mechanisms dropped them together and agreed on a queue that was missing them.
Two mechanisms are evidence only where they could differ: both now find a block by its header,
but the helper splits blocks and reads each header's bold text while this scans line by line, and
`AnUnfamiliarHeaderIsNeverDropped` drives the helper over headers nobody has written yet.

⛔ **(#778, INV-409) The decision pattern here is this file's own, never a copy of the helper's.** Until
#778 this file's `DECIDED` pattern was the helper's `DECIDED_IN_HEADER` pasted in, so when that pattern matched a
bare `resolved` or `superseded` -- and an undecided header reading "not yet resolved" left the
queue -- both mechanisms dropped it together and agreed. `records_a_decision` is written as string
tests over the six forms, the helper as one regex; the negated-word fixtures are the negative
control that fails if the helper's pattern widens again.

INV-409 (the queue admits every block by its header and treats it as decided only when the header
records the decision) names this file as its enforcer. It establishes how the helper classifies
fixture headers and the live ledger; it does not establish that a writer puts its decision in
the header, which the skill's Step 1 asks of the maintainer.

No phrase-level pattern (#438): its line reads are of `specs/IMPLEMENTED.md`, the ledger, which is
outside the in-scope corpora, as #425 recorded (INV-346).
"""

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"
LEDGER = REPO / "specs" / "IMPLEMENTED.md"

# ⚠️ A block whose spec required approval before implementation never records a `HELD` paragraph
# -- its header says this. Scanning without it found 0 held where 1 is held, and the
# disagreement with the helper is what surfaced it: two mechanisms are evidence precisely when
# they differ.
HELD_IN_BLOCK = "must be approved before implementation"

#: A block's header line: a deferral, an amendment, or the older `- ⛔ **` form (#770).
HEADER = re.compile(r"^- (?:⛔ )?\*\*(?:DEFERRED INVARIANT|PROPOSED AMENDMENT)\b")
#: How a header records the maintainer's decision (#770, #778): an opening that only a decision
#: writes, never a decision WORD -- "not yet resolved" and "would be superseded" decide nothing.
DECISION_PHRASES = ("(resolved INV-", "resolved as an amendment", "resolved by amendment",
                    "— superseded by ")
#: `(resolved <date>` and `— applied <date>` carry an ISO date, read by `iso_date_follows`.
DATED_DECISIONS = ("(resolved ", "— applied ")


def iso_date_follows(text, opener):
    """True when some `opener` in `text` is followed directly by a YYYY-MM-DD date."""
    start = text.find(opener)
    while start != -1:
        date = text[start + len(opener): start + len(opener) + 10]
        if len(date) == 10 and date[4] == date[7] == "-" and (date[:4] + date[5:7]
                                                              + date[8:]).isdigit():
            return True
        start = text.find(opener, start + 1)
    return False


def records_a_decision(header):
    """True when a block's bold header text records a decision in one of the ledger's forms."""
    return (any(phrase in header for phrase in DECISION_PHRASES)
            or any(iso_date_follows(header, opener) for opener in DATED_DECISIONS))


def undecided_header(line):
    """True when `line` opens a block whose header records no decision."""
    return bool(HEADER.match(line)) and not records_a_decision(line.split("**")[1])


def helper(*args):
    r = subprocess.run([sys.executable, str(HELPER), *args],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, f"helper exited {r.returncode}: {r.stderr[:400]}"
    return r.stdout


#: The hold the skill records INSIDE a block (#58): a `**HELD YYYY-MM-DD:**` paragraph. An
#: issue-driven deferral has no spec file, so this is its only reachable held state.
HELD_PARAGRAPH = re.compile(r"\*\*HELD \d{4}-\d{2}-\d{2}:\*\*")


def counted_by_scanning():
    """(pending, held) derived by a flat header scan -- not by splitting blocks.

    ⚠️ A hold is read from the ledger only, as the helper reads it: a `**HELD <date>:**` paragraph
    inside the block, or `HELD_IN_BLOCK` on its header line. The scan reads line by line: a
    paragraph seen after a pending block's header line, and before the next block or section
    starts, moves that block from pending to held. The first issue-driven hold (2026-09-29) is
    what showed the scan could not see it. (#778) The spec-file route this scan also read is gone:
    the helper dropped it in #58, the one block that used it carries its `HELD` paragraph in the
    ledger, and a second route here could only agree with a hold the helper cannot see.
    """
    text = LEDGER.read_text(encoding="utf-8")
    pending, held, open_pending = 0, 0, False
    for line in text.splitlines():
        if line.startswith("## "):
            open_pending = False
        elif re.match(r"^- (?:⛔ )?\*\*", line) and not undecided_header(line):
            open_pending = False
        if open_pending and HELD_PARAGRAPH.search(line):
            pending, held, open_pending = pending - 1, held + 1, False
            continue
        if not undecided_header(line):
            continue
        is_held = HELD_IN_BLOCK in line
        held += is_held
        pending += not is_held
        open_pending = not is_held
    return pending, held


class TheQueueCountsBlocksNotMentions(unittest.TestCase):
    def setUp(self):
        self.out = helper("list")
        m = re.search(r"pending: (\d+)\s+held: (\d+)", self.out)
        self.assertIsNotNone(m, f"`list` printed no counts:\n{self.out[:400]}")
        self.reported = (int(m.group(1)), int(m.group(2)))

    def test_the_pending_count_agrees_with_a_flat_header_scan(self):
        pending, _ = counted_by_scanning()
        self.assertEqual(
            pending, self.reported[0],
            f"the helper reports {self.reported[0]} pending; scanning for undecided block "
            f"headers finds {pending}. More reported means prose that merely mentions a "
            "deferral is being counted as one; fewer means a block the helper cannot see "
            "(#770).",
        )

    def test_a_held_block_is_never_listed_as_pending(self):
        """The other half: a decision already made must not be re-offered."""
        _, held = counted_by_scanning()
        self.assertEqual(
            held, self.reported[1],
            "the helper's held count disagrees with the holds the ledger records. A block "
            "carrying a `**HELD <date>:**` paragraph has been decided, and presenting it as "
            "awaiting review asks for a decision that already exists.",
        )
        self.assertIn("HELD: already decided, NOT for review", self.out)

    def test_every_quoted_rule_still_matches_its_source(self):
        """`check` is the guard the skill runs before quoting a block to the maintainer."""
        out = helper("check")
        m = re.search(r"(\d+) rule quotes checked, (\d+) mismatched", out)
        self.assertIsNotNone(m, out[:300])
        self.assertEqual(
            "0", m.group(2),
            f"a deferral quotes a rule its named file does not contain:\n{out}",
        )
        # ⚠️ Zero CHECKED is legitimate once every deferral carrying `— in `path`` bullets has
        # been resolved — which happened on 2026-09-02. It is not legitimate while such a
        # block is still pending, so the floor is conditional on the queue rather than fixed.
        # A fixed floor of 1 fails on a finished queue and reads as a defect; no floor at all
        # would let a broken scan report a clean run forever.
        # Block-aware: a rule bullet counts only while inside an UNRESOLVED block. Counting
        # every such bullet in the file counts the resolved ones too, which are exactly what
        # the helper stops checking — so the floor never falls and a finished queue reads as
        # a broken scan.
        quotable, inside = 0, False
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            if re.match(r"^- (?:⛔ )?\*\*", line) or line.startswith("## "):
                inside = undecided_header(line)
            elif inside and line.lstrip().startswith("- ") and "⛔ **" in line and "— in `" in line:
                quotable += 1
        if quotable:
            self.assertGreater(
                int(m.group(1)), 0,
                f"the ledger still carries {quotable} quotable rule bullet(s) and the scan "
                "checked none — the scan is broken, not the queue empty.",
            )

    def test_check_resolves_every_path_a_rule_names(self):
        """A named path that does not resolve leaves its quote unverified (#59).

        ⚠️ **Enforces INV-308.** It asserts that `check` still emits an unresolved count and
        that the count is zero — the half that can be observed from outside the helper.

        ⛔ It does **NOT** establish that the count is *correct*. A resolver that silently
        widened to match everything would report zero unresolved and pass this, exactly as a
        correct one does; `tests/test_deferral_quotes_match_their_source.py` imports the same
        `resolve`, so it cannot catch that either. What closes it is the mismatch assertion
        above — a wrongly-resolved path yields a quote that is not in the file — plus reading
        the diff. ⚠️ It also does not establish the wider rule INV-308 states about the
        **other** verification tools in this repo. That gap was total when this was written and
        is now partial, so it is stated per view rather than per file (#91):

        * `conformance.py reverse-check` — covered by
          `tests/test_reverse_check_counts_what_it_cannot_test.py`: the untested span is counted
          and named, and a run with untested lines is never called clean.
        * `conformance.py since`, at the range boundary — covered by
          `tests/test_the_range_boundary_reports_what_it_retires.py`: what a record retired is
          reported, and the tool refuses to claim it was examined.
        * `conformance.py all` — covered by
          `tests/test_all_runs_every_argument_free_view.py`: the aggregate must name **both**
          views it skips and how to run each.
        * `pending_invariants.py sites` — covered by
          `tests/test_sites_states_the_corpus_it_scanned.py`: what was scanned and what was not
          is printed on every run.
        * ⛔ `conformance.py rules`, `per-rule`, `duplication`, `enumerations` and `size` —
          **nothing asserts this of them.**
        * ⚠️ `coverage_reports.py` — **partial**: an invariant in no index group is asserted to be
          surfaced rather than silently exempted (`tests/test_coverage_reports.py`). Its other
          reports are unasserted in this respect.
        * ⛔ `citations.py` — **nothing.** It prints its own statement of what it could not
          verify — that commit-message citations are outside the check — and **no test pins that
          line**, so deleting it would break nothing. That is the cheapest remaining gap to close
          and is named here so it is not rediscovered.

        ⚠️ **This paragraph claimed the gap was total until 2026-09-21**, five guards after the
        first of them landed. A disclosure that outlives its fix **understates** coverage, which
        sends the next reader to build what already exists.

        ⛔ **This is the assertion that makes the new counter load-bearing.** Before #59
        `check` skipped an unresolvable location without counting it, so a run that verified
        nothing printed `0 rule quotes checked, 0 mismatched` — indistinguishable from a
        clean run, and presented as one to the maintainer in three consecutive reviews.

        ⚠️ `check` deliberately still exits 0 in this condition, so that callers expecting a
        zero status keep working and `helper()` above keeps its `returncode == 0` assertion.
        The warning is the human-facing signal; **this test is the enforcing one**, and
        without it the improved output would be advice nobody is held to.

        ⚠️ Counted apart from `no-prose-site`, which is legitimate: a rule encoded in code or
        tests rather than stated in prose names no path, owes nothing, and must not make this
        fail — INV-301 and INV-304..307 all take that form.
        """
        out = helper("check")
        m = re.search(r"(\d+) unresolved", out)
        self.assertIsNotNone(
            m, f"`check` no longer reports an unresolved count; the #59 counter is gone "
               f"and an unverifiable quote is silent again:\n{out[:300]}")
        self.assertEqual(
            "0", m.group(1),
            f"a deferral names a path that does not resolve under any resolution root, so "
            f"its quote is UNVERIFIED while the queue reads as checked:\n{out}")

    def test_next_id_is_one_past_the_highest(self):
        inv = (REPO / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        highest = max(int(x) for x in re.findall(r"\*\*INV-(\d{3})\*\*", inv))
        self.assertEqual(f"INV-{highest + 1:03d}", helper("next-id").strip())


def module(ledger_text, tmp):
    """The helper loaded by path, reading `ledger_text` as its ledger."""
    spec = importlib.util.spec_from_file_location("pending_invariants", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ledger = Path(tmp) / "IMPLEMENTED.md"
    ledger.write_text("# Implemented\n\n## a-spec\n\n%s\n" % ledger_text, encoding="utf-8")
    mod.LEDGER = ledger
    return mod


#: A block's body below its header, the same for every fixture.
BODY = """
    - ⛔ **A rule that ships with no id.** — in `docs/development.md`

  **INV-NNN** — the drafted wording."""


class AnUnfamiliarHeaderIsNeverDropped(unittest.TestCase):
    """⛔ (#770) A block is in the queue unless its header records a decision.

    The helper used to admit a block only when it carried an exact marker, and seven blocks
    worded "a new id is owed …; NOT minted" were left out while `list` reported
    `pending: 0`. These fixtures run the helper itself over headers in both directions.
    """

    def queued(self, header):
        with tempfile.TemporaryDirectory() as tmp:
            pending, held = module("- **%s**%s" % (header, BODY), tmp).queue()
            return len(pending), len(held)

    def test_a_negated_decision_word_is_pending(self):
        """⛔ (#778) The negative control: a decision WORD in an undecided header decides nothing.

        #770's pattern matched `resolved` and `superseded` anywhere in the header, so each of
        these left the queue while undecided. This fails if the helper's pattern widens again.
        """
        for header in (
                "DEFERRED INVARIANT — not yet resolved; NOT minted.",
                "DEFERRED INVARIANT — would be superseded if a later block replaces it; NOT minted.",
                "PROPOSED AMENDMENT to INV-216 — awaiting the maintainer's sign-off; NOT applied."):
            with self.subTest(header=header[:60]):
                self.assertEqual((1, 0), self.queued(header))
                self.assertFalse(records_a_decision(header),
                                 "this file's own decision pattern reads the fixture as decided")

    def test_the_wording_that_was_dropped_is_pending(self):
        self.assertEqual((1, 0), self.queued(
            # The live wording, its INV citation split so it is not read as one here.
            "DEFERRED INVARIANT — a new id is owed (INV-" "309); NOT minted."))

    def test_a_wording_nobody_has_used_is_pending(self):
        self.assertEqual((1, 0), self.queued("DEFERRED INVARIANT — to be decided."))

    def test_an_undecided_amendment_in_new_words_is_pending(self):
        self.assertEqual((1, 0), self.queued("PROPOSED AMENDMENT to INV-216 — draft."))

    def test_each_decision_leaves_the_queue(self):
        for header in (
                "DEFERRED INVARIANT (resolved INV-400, registered by the maintainer 2026-10-22).",
                "DEFERRED INVARIANT — resolved as an amendment, not a new id — PROPOSED "
                "AMENDMENT to INV-399 — applied 2026-10-22 by the maintainer.",
                "DEFERRED INVARIANT — NOT minted (an amendment, not a new id) — PROPOSED "
                "AMENDMENT to INV-107 — applied 2026-10-19.",
                "DEFERRED INVARIANT — NOT minted — superseded by the #239 block.",
                "DEFERRED INVARIANT (resolved by amendment, decided by the maintainer "
                "2026-09-16 — NO id minted).",
                "DEFERRED INVARIANT (resolved 2026-10-20 — NOT minted as its own id)."):
            with self.subTest(header=header[:60]):
                self.assertEqual((0, 0), self.queued(header))
                self.assertTrue(records_a_decision(header),
                                "this file's own decision pattern misses a decision form")

    def test_a_decision_word_below_the_header_decides_nothing(self):
        """Only the header records the decision; the body may quote anything."""
        with tempfile.TemporaryDirectory() as tmp:
            text = ("- **DEFERRED INVARIANT — a new id is owed.**%s\n\n"
                    "  Unlike #239's block, this was not superseded or resolved.") % BODY
            pending, _held = module(text, tmp).queue()
            self.assertEqual(1, len(pending))

    def test_prose_about_a_deferral_is_not_a_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = ("- **Queues one new invariant**: the `DEFERRED INVARIANT` above, "
                    "a new id is owed.")
            self.assertEqual([], module(text, tmp).blocks(include_resolved=True))

    def test_the_live_ledger_drops_no_header(self):
        """Every header the flat scan finds is a block the helper splits, decided or not."""
        with tempfile.TemporaryDirectory() as tmp:
            mod = module("", tmp)
        mod.LEDGER = LEDGER
        split = {b["line"] for b in mod.blocks(include_resolved=True)}
        headers = {n for n, line in enumerate(LEDGER.read_text(encoding="utf-8").splitlines(), 1)
                   if HEADER.match(line)}
        self.assertGreater(len(headers), 0, "the scan found no block headers at all (INV-265)")
        self.assertEqual(set(), headers - split,
                         "a block header the helper never split, so no view can show it")


if __name__ == "__main__":
    unittest.main()
