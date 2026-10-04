"""The audit skill states no count that the repository contradicts.

`production-readiness-audit/SKILL.md` carried measured figures as prose — "194 invariants",
"24 of 194 … enumerate", "42 shipped markdown files, 114,576 words", "130 repeated passages
across 91 file pairs", all dated 2026-07-31 — and a required-reading list naming six ledger
entries by date. Nothing re-measured any of them. By 2026-08-21 every figure was superseded
(260 invariants, 45 enumerating, 44 files, 165,299 words, 157 passages across 98 pairs) and the
reading list pointed at the six oldest of **thirty-two** audit entries, routing every run past
the newest — which is the one that matters most after an unattended session.

⚠️ **The list was also wrong when written.** The `deep-dive-audit-*` series has seven entries;
`deep-dive-audit-2026-07-29-minor-fixes` was never named. So the defect is not only staleness:
a fixed set in prose is unverifiable by construction, and it reads authoritative either way.

The fix removed the figures rather than refreshing them, since a fresh number rots identically.
This guard keeps them out: any count of invariants or of audit entries that appears in the file
must agree with the repository, and a **dated historical** figure must say so. It does not ban
numbers — the narrative figures that carry the skill's evidence ("372 tests green in the first",
"the count went 1 → 10") are exactly what INV-003's rationale rule protects and are left alone.

⛔ **Asserts agreement, not absence.** A guard that simply banned digits would be satisfied by
prose that says "roughly two hundred", which is the same defect in words.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import blocks, match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude/skills/production-readiness-audit/SKILL.md"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
IMPLEMENTED = REPO_ROOT / "specs" / "IMPLEMENTED.md"

# Number words this file might reasonably use for a small set, so "six entries" is caught as
# surely as "6 entries". Stops where prose stops counting things by hand.
WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "twenty-four": 24, "twenty-five": 25, "thirty-one": 31, "thirty-two": 32,
}
NUMBER = r"(?:\d+|%s)" % "|".join(sorted(WORDS, key=len, reverse=True))


def as_int(token):
    return WORDS.get(token.lower(), None) if not token.isdigit() else int(token)


def live_invariant_count():
    """Distinct numeric INV ids DEFINED at a line start.

    Not `grep -c '^- \\*\\*INV-'`: that counts 261, because the append template carries a
    literal `- **INV-NNN**` placeholder with no digits. `citations.py verify` reports 260, and
    these two must not disagree.
    """
    ids = re.findall(r"(?m)^- \*\*INV-(\d{3})\*\*", INVARIANTS.read_text(encoding="utf-8"))
    return len(set(ids))


def live_audit_entry_count():
    heads = re.findall(r"(?m)^## ((?:production-readiness-audit|deep-dive-audit)\S*)$",
                       IMPLEMENTED.read_text(encoding="utf-8"))
    return len(heads)


def without_fences(text):
    """``text`` with every fence line and fenced line blanked, so line numbers are kept."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else line)
    return "\n".join(out)


def statements_in(text, pattern):
    """(line number, matched number, start line) for each hit in ``text``, skipping fenced code.

    Matched across line wraps (#425): "194" can end one line and "invariants" begin the next.
    The lines come from ``match_lines``; the numbers come from the same blocks, collapsed the
    same way and searched in the same order, so the two lists line up. The line returned is the
    one the match starts on, so ``HISTORICAL`` is read there, as it was read on the one line
    before; a marker that wraps to the next line does not exempt (fails closed).
    """
    text = without_fences(text)
    compiled = re.compile(pattern, re.IGNORECASE)
    numbers = []
    for block in blocks(text):
        flat = " ".join(" ".join(line for _n, line in block).split())
        numbers += [m.group(1) for m in compiled.finditer(flat)]
    starts = match_lines(text, compiled)
    assert len(starts) == len(numbers), "match_lines and the block scan disagree"
    lines = text.split("\n")
    return [(n, number, lines[n - 1].strip()) for n, number in zip(starts, numbers)]


def statements(pattern):
    """``statements_in`` over the audit skill."""
    return statements_in(SKILL.read_text(encoding="utf-8"), pattern)


#: "<N> invariants". ⛔ Not `N invariants` bare: "vocabulary retired two invariants ago" is a
#: relative DISTANCE, not a count of the ruleset, and the first version of this guard failed on
#: it. A trailing ago/later/earlier/apart marks the idiom.
INVARIANT_COUNT = r"\b(%s)\s+invariants\b(?!\s+(?:ago|later|earlier|apart))" % NUMBER

#: "<N> audit entries", "<N> `deep-dive-audit-*` runs" and the like.
AUDIT_ENTRY_COUNT = (r"\b(%s)\s+(?:`?(?:deep-dive-audit|production-readiness-audit)[`*-]*\s+)?"
                     r"(?:prior\s+|ledger\s+|audit\s+)*(?:entries|runs)\b" % NUMBER)


# A figure presented as a dated historical fact is legitimate; one presented as the current
# state is the defect. The marker is a date or an explicitly past framing on the same line.
HISTORICAL = re.compile(r"20\d\d-\d\d-\d\d|earlier version|by 20\d\d|was wrong when written"
                        r"|an earlier|previously|then\b")


class NoStaleInvariantCount(unittest.TestCase):
    def test_every_invariant_count_agrees_with_invariants_md(self):
        live = live_invariant_count()
        self.assertGreater(live, 0, "parsed no invariants from INVARIANTS.md")
        offenders = []
        for lineno, token, line in statements(INVARIANT_COUNT):
            value = as_int(token)
            if value is None or HISTORICAL.search(line):
                continue
            if value != live:
                offenders.append("line %d says %r; INVARIANTS.md defines %d — %s"
                                 % (lineno, token, live, line[:100]))
        self.assertEqual(
            [], offenders,
            "the audit skill states an invariant count the ruleset contradicts. Prefer stating "
            "no count at all — the generators print the current one — over refreshing a figure "
            "that will rot again:\n  %s" % "\n  ".join(offenders))


class NoStaleAuditEntryCount(unittest.TestCase):
    def test_every_audit_entry_count_agrees_with_the_ledger(self):
        live = live_audit_entry_count()
        self.assertGreater(live, 0, "parsed no audit entries from IMPLEMENTED.md")
        offenders = []
        for lineno, token, line in statements(AUDIT_ENTRY_COUNT):
            value = as_int(token)
            if value is None or HISTORICAL.search(line):
                continue
            if value != live:
                offenders.append("line %d says %r; the ledger holds %d — %s"
                                 % (lineno, token, live, line[:100]))
        self.assertEqual(
            [], offenders,
            "the audit skill states a count of audit entries the ledger contradicts. The "
            "required-reading rule is supposed to name no fixed count or set:\n  %s"
            % "\n  ".join(offenders))


class CountsAreMatchedAcrossLineWraps(unittest.TestCase):
    """Negative controls (#425): a count wrapped across a line break is still a count."""

    def test_a_wrapped_invariant_count_is_found_at_its_first_line(self):
        wrapped = "Step 2 checks all 194\ninvariants on every run.\n"
        self.assertEqual([(1, "194")], [(n, t) for n, t, _ in statements_in(wrapped,
                                                                          INVARIANT_COUNT)])
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(re.search(INVARIANT_COUNT, l, re.I) for l in wrapped.split("\n")))

    def test_a_wrapped_audit_entry_count_is_found_at_its_first_line(self):
        wrapped = "Read the\nsix `deep-dive-audit`\nentries first.\n"
        self.assertEqual([(2, "six")], [(n, t) for n, t, _ in statements_in(wrapped,
                                                                          AUDIT_ENTRY_COUNT)])
        self.assertFalse(any(re.search(AUDIT_ENTRY_COUNT, l, re.I) for l in wrapped.split("\n")))

    def test_a_wrapped_distance_is_not_a_count(self):
        """Must not flag (INV-282): the "ago" idiom still reads as a distance when it wraps."""
        self.assertEqual([], statements_in("vocabulary retired two invariants\nago.\n",
                                           INVARIANT_COUNT))

    def test_a_count_inside_a_fence_is_still_skipped(self):
        """Must not flag: fenced output is printed by a generator, not stated by the skill."""
        fenced = "```text\n194\ninvariants\n```\n"
        self.assertEqual([], statements_in(fenced, INVARIANT_COUNT))


class TheReadingListIsARuleNotASet(unittest.TestCase):
    """The higher-severity half: a wrong count wastes attention, a wrong list changes what a
    run knows."""

    def test_step_1_does_not_enumerate_the_entries_to_read(self):
        text = SKILL.read_text(encoding="utf-8")
        dated = re.findall(r"`(?:deep-dive-audit|production-readiness-audit)-20\d\d-\d\d-\d\d",
                           text)
        # A dated entry may be CITED as evidence for a specific finding. What must not exist is
        # a run's reading list fixed to particular dates.
        self.assertNotRegex(
            text, r"(?i)read the (?:six|seven|five|\d+) `?deep-dive-audit",
            "Step 1 names a fixed number of entries to read. Express it as a rule over the most "
            "recent entries instead; the set changes every run and the prose does not.")
        self.assertNotRegex(
            text, r"(?i)those (?:six|seven|\d+) entries are required reading",
            "the header fixes the required reading to a counted set.")
        self.assertLessEqual(
            len(dated), 4,
            "the file names %d dated audit entries (%s). A few citations supporting specific "
            "findings are fine; a list is the defect." % (len(dated), ", ".join(sorted(set(dated)))))

    def test_it_tells_the_run_how_to_get_the_current_list(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn(
            "grep -n '^## \\(production-readiness-audit\\|deep-dive-audit\\)'", text,
            "Step 1 should give the command that produces today's list, so the rule is "
            "actionable rather than an instruction to remember.")


class AFullSweepIsNotImplied(unittest.TestCase):
    def test_step_2_says_a_full_forward_sweep_is_not_feasible_and_how_to_scope(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertRegex(
            text, r"(?i)full forward sweep .{0,60}no longer feasible",
            "Step 2 still reads as though every invariant is checked each run. Thirty-plus runs "
            "of evidence say otherwise; say so and prescribe the scoping.")
        for cue in ("generators put hits against", "enumerating subset",
                    "diff since the last audit", "per-module outcome blocks"):
            self.assertIn(cue, text,
                          "Step 2 does not prescribe how to scope the sweep (missing %r)" % cue)


if __name__ == "__main__":
    unittest.main()
