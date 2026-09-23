"""The ledger FILES are well-formed -- not just the entries a regex managed to find.

On 2026-08-21 two entries were written into `specs/IMPLEMENTED.md` with literal backslash-n text
instead of newlines, spliced into the middle of an unrelated entry's Summary line: two entries as
one 4,539-character line, their `## ` headings not at line start, and a third pre-existing entry cut
in half around the splice point.

**The full suite passed. 3,141 tests, exit 0. It was committed.**

Nothing could see it. `test_spec_ledger_invariants` finds entries with `(?m)^## (\\S+)$`, so a
heading that is not line-anchored is not *invalid* -- it is **absent**. Every downstream check
inherits that: the `Commit:`-vocabulary gate, the affected-files accounting and the forward-coverage
check all iterate the entries the regex found, so a malformed entry is simply not among them. The
corruption was caught by `list_specs.py` reporting a spec count that disagreed with what had just
been implemented -- a comparison a human happened to make.

⚠️ **This file validates the FILE; its siblings validate ENTRIES.** That is the whole distinction.
An entry-shaped assertion cannot notice that a region of the file is not an entry, because the parse
is the gate.

⛔ **These checks never modify a ledger.** Both files are append-only records; the repair path is to
restore from the last good commit and re-insert, which is what happened. A guard that tried to fix
formatting would risk rewriting the history the file exists to preserve. Fail loudly, name the line.

Source spec: `specs/a-malformed-ledger-entry-is-invisible-to-every-guard.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS = REPO_ROOT / "specs"
IMPLEMENTED = SPECS / "IMPLEMENTED.md"
DECLINED = SPECS / "DECLINED.md"
LEDGERS = (IMPLEMENTED, DECLINED)

#: The template placeholder both ledgers carry inside their format comment.
PLACEHOLDER = "<spec-name>"

def code_spans_removed(text):
    """Strip fenced blocks and inline code, where a literal backslash-n is legitimate."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


class TheLedgersExist(unittest.TestCase):
    def test_both_ship(self):
        for p in LEDGERS:
            with self.subTest(file=p.name):
                self.assertTrue(p.is_file(), "%s is missing" % p.name)


class NoLiteralEscapeSequenceOutsideCode(unittest.TestCase):
    """The corruption's signature: newlines that arrived as two characters."""

    def test_no_literal_backslash_n_in_prose(self):
        for p in LEDGERS:
            with self.subTest(file=p.name):
                stripped = code_spans_removed(p.read_text(encoding="utf-8"))
                bad = [
                    i for i, line in enumerate(stripped.splitlines(), 1)
                    if "\\" + "n" in line
                ]
                self.assertEqual(
                    [], bad,
                    "%s carries a literal backslash-n outside a code span, at line(s) %s. That is "
                    "the signature of an entry written with escaped newlines -- the 2026-08-21 "
                    "corruption, which passed 3,141 tests. If the mention is deliberate, put it in "
                    "a code span." % (p.name, bad))


class EveryHeadingStartsALine(unittest.TestCase):
    """A heading mid-line is invisible to every entry-level guard rather than invalid."""

    # ⚠️ **This binds what a ledger ENTRY may write, and that is deliberate.** An entry needing
    # to mention a heading pattern in prose must write the slug without the `## ` prefix --
    # `` `production-readiness-audit-*` `` rather than `` `## production-readiness-audit-*` `` --
    # because the second is indistinguishable from the corruption this detects. It fired on
    # exactly that, on 2026-08-21, against an entry describing the ref resolver. Rewording the
    # prose costs nothing; relaxing the check would give back the code-span blind spot that let
    # the original corruption pass 3,141 tests.

    def test_no_entry_heading_appears_mid_line(self):
        for p in LEDGERS:
            with self.subTest(file=p.name):
                offenders = []
                for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    # Both ledgers DOCUMENT the format in prose -- "`## <name>` heading" -- so a
                    # heading-looking token inside a code span is legitimate and must be stripped
                    # before looking. A first version reported the header's own explanation.
                    # ⛔ **Scanned RAW, with no code-span strip, and that is deliberate.** A first
                    # version stripped code spans first, and a reproduction of the 2026-08-21
                    # corruption then PASSED -- because the splice landed inside a backtick span
                    # (`coverage_reports.py shipped`) and the strip deleted the injected heading
                    # along with the span. Corruption does not respect span boundaries, so the
                    # blind spot was the whole defect. Verified against both real files: the
                    # slug shape below has ZERO raw-line hits today, so no strip is needed.
                    bare = line
                    # Only an ENTRY heading matters, and one looks like `## some-spec-slug`:
                    # lowercase, hyphenated, no spaces, long. Three narrowings, each from a
                    # false positive on the real file: `(?<!#)` because `### ⚠️ Correction` is a
                    # legitimate sub-heading; the slug shape because prose legitimately quotes
                    # section names ('added a "## Markdown files" ground rule'); and the slug shape
                    # also keeps it off the ledgers' own `## <name>` format documentation.
                    # No trailing-whitespace requirement: the corruption puts a literal backslash
                    # right after the slug (`## a-name` + backslash-n), so requiring \s or $ made a
                    # first version miss its own reproduction in BOTH tested positions.
                    for m in re.finditer(r"(?<!#)## [a-z0-9][a-z0-9-]{9,}", bare):
                        if m.start() != 0:
                            offenders.append("%s:%d" % (p.name, i))
                            break
                self.assertEqual(
                    [], offenders,
                    "an entry heading is not at line start, so `(?m)^## (\\S+)$` cannot see it and "
                    "every entry-level guard silently skips it: %s" % offenders)

    def test_two_independent_parses_agree_on_the_entry_count(self):
        """Line-anchored regex vs splitting on a newline plus '## '. Disagreement means malformed."""
        for p in LEDGERS:
            with self.subTest(file=p.name):
                text = p.read_text(encoding="utf-8")
                by_regex = len(re.findall(r"(?m)^## (\S+)$", text))
                by_split = len([s for s in text.split("\n## ")[1:] if s.split("\n", 1)[0].strip()])
                self.assertEqual(
                    by_regex, by_split,
                    "%s parses to %d entries by line-anchored regex and %d by splitting -- the two "
                    "disagree, which is what a malformed entry looks like from outside"
                    % (p.name, by_regex, by_split))


# ⛔ **There is deliberately no line-length check, and the measurement is why.** A ceiling looked
# like the obvious detector -- the corruption was one 4,539-character line -- until it was measured
# against the real file: the longest LEGITIMATE ledger line is 8,902 characters, because a Summary
# is one wrapped paragraph. So any ceiling low enough to catch that corruption fires on ordinary
# entries, and any ceiling high enough to pass them cannot catch it. Length carries no signal here.
# Do not add one; the four checks above and below each catch the same corruption on structure
# instead, which is what actually distinguishes it.


# ⛔ **There is deliberately no "every heading resolves to a specs/<name>.md" check either, and the
# reason is the same shape as the line-length one: it has no reliable discriminator.** The ledger
# legitimately carries 51+ dated PROCESS-RUN entries -- `deep-dive-audit-*`, `production-readiness-
# audit-*`, `dry-run-*`, and one-off triage records -- which correctly have no spec file. The newer
# ones are marked **Not a spec**; the older ones, from `deep-dive-audit-2026-07-27` onward, are not,
# because that convention was adopted partway through. So exempting by marker misses half of them and
# exempting by name pattern is circular. A first version of this check reported all 51 as defects.
# The two structural checks above catch the corruption this file exists for without needing to know
# which entries are specs.


class NoEntryIsSwallowedByTheFormatComment(unittest.TestCase):
    """A whole REGION of the ledger commented out -- the same blind spot, one level up.

    Both ledgers open their entry area with `<!-- New entries go directly below this line.
    Format:`, a template, and `-->`. Taken literally, "directly below this line" points INSIDE
    the comment -- and on 2026-08-22 that is where every entry prepended to
    `specs/IMPLEMENTED.md` since the file was created had gone: the comment opened at line 33
    and closed at line 293, with the format template drifted to the *end* of the span, so
    **29 real entries** -- all of 2026-08-21's work and four `production-readiness-audit-*`
    records -- sat inside it and rendered as nothing.

    ⛔ **Every existing guard passed, including this file's siblings, and so did the full
    suite.** An HTML comment does not move a heading off its line, so `(?m)^## (\\S+)$` finds
    all 456 headings and `grep -c '^## '` agrees; the two-parse cross-check agrees too, because
    both parses are line-based and neither models comments. `list_specs.py` also reads lines, so
    the open-set arithmetic was correct throughout. Nothing in the repo distinguished
    "recorded" from "recorded where no reader will ever see it".

    `specs/DECLINED.md` had the intended shape the whole time -- comment 33-42, template only --
    which is what identified `IMPLEMENTED.md` as the file that had drifted rather than the
    convention being ambiguous. The repair was a pure move of the template and `-->` above the
    entries; the assertion below is what keeps the next prepend from landing inside again.
    """

    #: The comment the ledgers use to document their entry format.
    OPENER = "<!-- New entries go directly below this line. Format:"

    def _comment_span(self, path):
        lines = path.read_text(encoding="utf-8").split("\n")
        try:
            opened = next(i for i, l in enumerate(lines) if l.startswith(self.OPENER))
        except StopIteration:
            self.fail("%s no longer carries the format comment this guard reads; either the "
                      "convention changed or the header was rewritten" % path.name)
        rest = lines[opened + 1:]
        for offset, line in enumerate(rest):
            if line.rstrip().endswith("-->"):
                return lines, opened, opened + 1 + offset
        self.fail("%s opens a format comment at line %d that is never terminated, so the rest "
                  "of the file is commented out" % (path.name, opened + 1))

    def test_the_format_comment_encloses_nothing_but_its_template(self):
        for p in LEDGERS:
            with self.subTest(file=p.name):
                lines, opened, closed = self._comment_span(p)
                swallowed = [
                    "%s:%d" % (p.name, i + 1)
                    for i, line in enumerate(lines[opened:closed], start=opened)
                    if line.startswith("## ") and PLACEHOLDER not in line]
                self.assertEqual(
                    [], swallowed,
                    "%d real entry heading(s) sit INSIDE %s's format comment, so they render as "
                    "nothing while every line-based guard still counts them: %s. The comment "
                    "must contain only its `## %s` template — move the template and `-->` above "
                    "the entries" % (len(swallowed), p.name, swallowed[:5], PLACEHOLDER))

    def test_the_comment_is_short_enough_to_be_a_template(self):
        """A belt-and-braces bound: a template is ~10 lines, not ~260."""
        for p in LEDGERS:
            with self.subTest(file=p.name):
                _, opened, closed = self._comment_span(p)
                span = closed - opened + 1
                self.assertLess(
                    span, 30,
                    "%s's format comment spans %d lines. It is meant to hold one `## %s` "
                    "template; at this size it has swallowed content" % (p.name, span,
                                                                        PLACEHOLDER))

    def test_entries_exist_outside_the_comment(self):
        """Anti-vacuity: the checks above pass trivially on a ledger with no entries at all."""
        for p in LEDGERS:
            with self.subTest(file=p.name):
                lines, _, closed = self._comment_span(p)
                after = [l for l in lines[closed + 1:]
                         if l.startswith("## ") and PLACEHOLDER not in l]
                self.assertGreater(
                    len(after), 0,
                    "%s has no entry heading after its format comment; this guard is inspecting "
                    "an empty set" % p.name)


class EveryEntryHeadingIsUnique(unittest.TestCase):
    """Two entries under one heading make the ledger's own done-test ambiguous.

    `IMPLEMENTED.md` states that a spec is done **iff** it has a `## <name>` heading matching
    the spec's filename. Two identical headings break that: `entries()` in
    `test_spec_ledger_invariants.py` yields both, `citations.py` resolves a `Source:` against
    whichever it reaches first, and nothing distinguishes them.

    ⚠️ **The realistic cause is a same-day collision, not corruption.** Three invariant
    reviews ran on 2026-09-16; the third was suffixed at the time and the first two were both
    written as the bare date, hours apart, by the same author. The repo already had the
    remedy — `deep-dive-audit-2026-07-30` and `-30b` — but nothing required it.

    ⛔ **No existing guard caught this.** The class above pins that headings start a line and
    that no spec sits in both ledgers; neither notices the same heading twice in one file.

    ⚠️ **The placeholder is excluded deliberately.** Both ledgers carry `## <spec-name>` once
    in their format comment, which is legitimate and must not be counted as a collision.
    """

    def test_the_scan_finds_headings_at_all(self):
        """INV-265 -- a uniqueness check over zero headings passes trivially."""
        for p in LEDGERS:
            with self.subTest(file=p.name):
                found = [l for l in p.read_text(encoding="utf-8").splitlines()
                         if l.startswith("## ") and PLACEHOLDER not in l]
                self.assertGreaterEqual(
                    len(found), 3,
                    "fewer than three entry headings parsed from %s; the scan has drifted "
                    "and the uniqueness check below proves nothing" % p.name)

    def test_no_entry_heading_appears_twice(self):
        for p in LEDGERS:
            with self.subTest(file=p.name):
                names = [l[3:].strip() for l in p.read_text(encoding="utf-8").splitlines()
                         if l.startswith("## ") and PLACEHOLDER not in l]
                dupes = sorted({n for n in names if names.count(n) > 1})
                self.assertEqual(
                    [], dupes,
                    "%s carries the same entry heading more than once: %s. The file's own "
                    "rule is that an entry is identified BY its heading, so a repeated one "
                    "is ambiguous to every reader and every tool. Suffix the later entry -- "
                    "`<name>b`, `<name>c` -- following the deep-dive-audit-2026-07-30 / -30b "
                    "precedent; never merge or renumber the entries, since each records a "
                    "different piece of work." % (p.name, ", ".join(dupes)))


class TheInventoryArithmeticHolds(unittest.TestCase):
    """`list_specs.py` is what caught the corruption. Make it a test, not a human comparison."""

    def run_list_specs(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tests/list_specs.py")],
            capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(0, proc.returncode, proc.stderr)
        return proc.stdout

    # ⛔ REMOVED, and the reason is worth more than the test was: an earlier version asserted
    # `specs - implemented - declined == open` from list_specs.py's own output. That is a
    # TAUTOLOGY. list_specs.py reports `implemented` as the count of ledger headings that
    # INTERSECT the candidate set, and derives `open` as exactly that subtraction, so the
    # identity holds by construction and the test cannot fail. Verified 2026-08-21: appending
    # `## a-ghost-entry-with-no-spec-file` to IMPLEMENTED.md left the line unchanged at
    # `specs: 402 implemented: 390 declined: 6 open: 6` and the test still passed. Replaced by
    # the cross-check below, which compares two INDEPENDENT sources: what list_specs reports
    # open, and what the ledger text contains.

    def test_no_open_spec_has_a_ledger_heading_anywhere(self):
        """The corruption's other side: an entry present but not line-anchored.

        On 2026-08-21 two entries were spliced mid-line, so `^## name$` did not find them and
        both specs kept counting as open -- while their `## name` text sat in the file. This
        looks for that disagreement directly: a spec reported OPEN whose `## <name>` appears
        in a ledger at all, anchored or not. Unlike the arithmetic it replaces, both sides
        come from different places, so it can fail.
        """
        out = self.run_list_specs()
        counts = re.search(r"open:\s*\d+", out)
        self.assertIsNotNone(counts, "list_specs.py output did not parse:\n%s" % out)
        tail = out[counts.end():]
        open_names = re.findall(r"(?m)^  ([a-z0-9][a-z0-9.-]+)\s*$", tail)
        self.assertTrue(
            open_names or "open: 0" in out,
            "parsed no open spec names from list_specs.py; the output format moved:\n%s" % out)
        ledgers = "\n".join(f.read_text(encoding="utf-8") for f in (IMPLEMENTED, DECLINED))
        buried = [n for n in open_names if ("## " + n) in ledgers]
        self.assertEqual(
            [], buried,
            "spec(s) reported OPEN whose `## <name>` is present in a ledger: %s. Either the "
            "heading is not at a line start (the 2026-08-21 corruption shape) or the spec was "
            "recorded under a name that no longer matches its file." % buried)

    def test_no_spec_is_in_both_ledgers(self):
        impl = set(re.findall(r"(?m)^## (\S+)$", IMPLEMENTED.read_text(encoding="utf-8")))
        dec = set(re.findall(r"(?m)^## (\S+)$", DECLINED.read_text(encoding="utf-8")))
        both = sorted((impl & dec) - {PLACEHOLDER})
        self.assertEqual(
            [], both,
            "spec(s) recorded as BOTH implemented and declined: %s. The two are terminal states "
            "and `list_specs.py` subtracts both, so an overlap double-subtracts." % both)


if __name__ == "__main__":
    unittest.main()
