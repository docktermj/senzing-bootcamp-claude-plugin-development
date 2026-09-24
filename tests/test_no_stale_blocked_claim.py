"""No live document says a reworked command still writes spec files, or is blocked.

`/production-readiness-audit` wrote spec files into the frozen archive, and `/unattended-issue-loop`
therefore carried a blocked audit half. **#69 fixed both on 2026-09-16.** The prose describing the
old world was not swept, so on 2026-09-21 — five days later — **five sites still said otherwise**,
including `docs/development.md`, which told the maintainer ⛔ *not to run a command that works*.
One of them, `tests/test_unattended_loop_is_label_gated.py`, contradicted **itself**: its module
docstring said the audit half was blocked while its own class forty lines down recorded the
assertion as inverted because #69 fixed it. (#90, found by the 2026-09-21 audit.)

⛔ **The matcher is derived from the CLAIM, not from the phrasings that shipped** (INV-282).
Each claim is matched by its subject plus a present-tense predicate, so a wording nobody has
written yet is caught too. There are now three:

1. *the audit half is blocked*
2. *`/production-readiness-audit` writes specs*
3. *`/delegate-to-mcp-server` writes specs* — added by #114, which reworked it to file issues

⚠️ **The third was this guard's own stated exemption until #114.** The docstring you are reading
used to call `/delegate-to-mcp-server` "the one command the claim is still true of" and pinned
two phrasings as prose that must stay legal. Reworking it turned both into exactly the stale
claim this file exists to catch, so they moved from the negatives to the positives. ⛔ **An
exemption justified by a fact is only as durable as that fact** — which is the same lesson as
the rest of this docstring, arrived at from the other direction.

⚠️ **The hard half is what this must NOT flag, and it is pinned beside the positives.** Three
constructions are legitimate and must stay legal:

* **History**, in the past tense — "the audit half **was** blocked", "this paragraph **said** the
  audit half was blocked until 2026-09-21". Recording why a rule exists is this repository's
  house style, and a guard that forbade it would delete the reason along with the error.
* **The current behavior of either command** — "`/delegate-to-mcp-server` files issues and
  writes nothing here". Saying what a command does now must not trip a guard about what it
  used to do.
* **The current behavior** — "`/production-readiness-audit` files a GitHub issue when attended".

⚠️ **`specs/IMPLEMENTED.md` and the frozen archive are out of scope deliberately.** The ledger's
own audit entry quotes the stale claims verbatim, because that is what an audit record is for; a
guard that scanned it would fail on the record of the defect it enforces.

Stdlib only; every file is read as text (INV-108).

Source issue: #90.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Live documents a maintainer reads to decide what to run. ⛔ `specs/` carries only its README:
#: the archive is frozen and the ledger records history verbatim, including this defect.
SCANNED = (
    sorted((REPO_ROOT / "docs").rglob("*.md"))
    + sorted((REPO_ROOT / ".claude").rglob("*.md"))
    + sorted((REPO_ROOT / "tests").rglob("*.py"))
    + [REPO_ROOT / "specs" / "README.md"]
)

#: ⛔ (INV-207) This file scans itself out. It MUST hold the shipped phrasings as fixtures --
#: that is what calibrates the matcher -- so a scan including it reports its own fixtures as
#: violations. The exclusion is narrow (one path) and stated rather than achieved by a pattern
#: that happens to miss them, which would also miss the real thing.
SCANNED = [f for f in SCANNED if f.resolve() != Path(__file__).resolve()]

#: "the audit half is/stays/remains/still blocked" — the subject plus a PRESENT-tense predicate.
#: Past tense is deliberately unmatched: "was blocked" is history, which must stay sayable.
AUDIT_HALF_BLOCKED = re.compile(r"audit half\s+(?:is|stays|remains|still\s+)?\s*blocked", re.I)

#: "`/production-readiness-audit` (still) writes spec(s)" — bound to that actor.
AUDIT_WRITES_SPECS = re.compile(
    r"production-readiness-audit`?\s*(?:still\s+)?writes?\s+spec", re.I)

#: "`/delegate-to-mcp-server` (still) writes spec(s)" — true until #114, stale after it.
#: ⚠️ Bound to `writes spec` specifically, never to `writes` alone: the correct replacement
#: prose says this command "writes nothing under `specs/`", and a looser pattern would flag
#: the very sentence that fixed the defect.
DELEGATE_WRITES_SPECS = re.compile(
    r"delegate-to-mcp-server`?[^.\n]{0,60}?(?:still\s+)?writes?\s+spec", re.I)

#: The same claim written from the other end: "One command ... still writes spec files —
#: `/delegate-to-mcp-server`", where the subject trails the predicate.
DELEGATE_WRITES_SPECS_TRAILING = re.compile(
    r"(?:still\s+)?writes?\s+spec[^.\n]{0,60}?delegate-to-mcp-server", re.I)

#: Every phrasing that actually shipped, pinned so the matcher cannot be narrowed until it
#: stops catching them (INV-282).
SHIPPED_PHRASINGS = (
    "its audit half stays blocked while `/production-readiness-audit` writes specs",
    "⛔ **The audit half is BLOCKED and the loop must say so.**",
    "`/production-readiness-audit` still writes spec files into the frozen archive",
    "with its audit half blocked for exactly this reason",
    # Both shipped and were correct until #114 reworked the command. Moved here from
    # LEGITIMATE, where this file had pinned them as prose that must stay legal.
    "One maintainer command still writes spec files -- `/delegate-to-mcp-server`",
    # ⚠️ Pinned as the WHOLE TABLE ROW, which is how it shipped in `specs/README.md`.
    # The status cell alone -- "⛔ **Still writes specs**; needs the same rework, no issue
    # yet" -- names no command, so no subject-bound matcher can catch it, and pinning the
    # cell would have forced a subject-free pattern that fires on any sentence about any
    # command writing specs, including the history this file must keep sayable.
    "| `/delegate-to-mcp-server` | ⛔ **Still writes specs**; needs the same rework, "
    "no issue yet |",
)

#: Constructions that MUST NOT be flagged. A guard that flags correct prose is relaxed rather
#: than fixed, and each of these is prose this repository needs to keep writing.
LEGITIMATE = (
    "The audit half WAS blocked, and this docstring said so five days after it stopped",
    "This paragraph said the audit half was blocked until 2026-09-21",
    "`/production-readiness-audit` files a GitHub issue when attended",
    "`/production-readiness-audit` wrote spec files into the frozen archive, so an unattended",
    # #114's replacement prose. ⛔ These are the sentences that FIXED the defect; a matcher
    # that flags them is one that punishes the correction.
    "`/delegate-to-mcp-server` files issues and writes nothing under `specs/` (#114)",
    "✅ Reworked -- it files GitHub issues now, and writes nothing here (#114)",
    "`/delegate-to-mcp-server` wrote spec files until #114 reworked it",
)


#: Every matcher the scan applies. ⛔ Adding a claim means adding it here as well as
#: above -- a pattern defined and never consulted is a guard that reads as present and
#: checks nothing.
MATCHERS = (AUDIT_HALF_BLOCKED, AUDIT_WRITES_SPECS,
            DELEGATE_WRITES_SPECS, DELEGATE_WRITES_SPECS_TRAILING)


def hits(text):
    return [m.group(0) for p in MATCHERS for m in p.finditer(text)]


class TheMatcherIsCalibrated(unittest.TestCase):
    """⛔ INV-282 — pinned in both directions, or the scan below proves nothing."""

    def test_every_shipped_phrasing_is_caught(self):
        for phrasing in SHIPPED_PHRASINGS:
            with self.subTest(phrasing=phrasing[:50]):
                self.assertTrue(
                    hits(phrasing),
                    "a wording that actually shipped is not matched, so the scan below would "
                    "have passed over it: %r" % phrasing)

    def test_no_legitimate_construction_is_caught(self):
        for phrasing in LEGITIMATE:
            with self.subTest(phrasing=phrasing[:50]):
                self.assertEqual(
                    [], hits(phrasing),
                    "correct prose is flagged: %r. A guard that fires on the history of a fix, "
                    "or on the one command the claim is still true of, gets relaxed rather than "
                    "fixed -- and the reason goes with it" % phrasing)

    def test_the_scan_has_files_to_read(self):
        """INV-265 — the assertion below passes trivially over an empty file list."""
        self.assertGreater(
            len([f for f in SCANNED if f.is_file()]), 50,
            "fewer than 50 live documents were found to scan; the paths have moved and the "
            "guard is reading almost nothing")


class NoLiveDocumentCarriesTheStaleClaim(unittest.TestCase):
    def test_no_document_says_the_audit_half_is_blocked_or_writes_specs(self):
        offenders = []
        for f in SCANNED:
            if not f.is_file():
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                for hit in hits(line):
                    offenders.append("%s:%d  %r" % (f.relative_to(REPO_ROOT), n, hit))
        self.assertEqual(
            [], offenders,
            "a live document asserts, in the present tense, that the loop's audit half remains "
            "unavailable, or that the audit command still writes into the frozen archive. #69 "
            "fixed both on 2026-09-16, and prose saying otherwise routes a maintainer away from "
            "a command that works. (Worded around the claim itself, per INV-207, so this "
            "message is not a violation of the rule it reports.):\n  "
            + "\n  ".join(offenders))


class TheReworkIsRecordedRatherThanSilent(unittest.TestCase):
    """⛔ **Inverted by #114, not deleted.** What it guards is unchanged; the fact flipped.

    This class used to assert the opposite — that both documents **must** say
    `/delegate-to-mcp-server` still writes specs — on the ground that sweeping the claims #69
    fixed must not take the one real remaining case with them. That was right while the case
    was real. #114 reworked the command to file GitHub issues, so the assertion it made is now
    the stale claim the rest of this file exists to catch, and the scan above would flag the
    very prose this class demanded.

    ⚠️ **The precedent is `tests/test_unattended_loop_is_label_gated.py`**, whose assertion #69
    inverted for the same reason and which this module's docstring cites for contradicting
    itself when the inversion was not carried into its prose. Inverting in place, with the
    reason kept, is how that is avoided — a deleted class takes its reasoning with it and the
    next reader cannot tell a retired guard from a forgotten one.

    ⛔ **The surviving obligation: a sweep must not make the command VANISH.** Erasing the row
    would leave no record that the rework happened and no way to tell a reworked command from
    one nobody ever documented.
    """

    #: What each document must now say: the command is named, and described as reworked
    #: rather than merely dropped. ⚠️ Matched on `files ... issues` + `#114`, never on the
    #: absence of the old wording -- an assertion satisfied by deletion is satisfied by a
    #: sweep that erased the row.
    REWORKED = re.compile(r"delegate-to-mcp-server", re.I)
    FILES_ISSUES = re.compile(r"files?\s+(?:github\s+)?issues", re.I)

    def test_both_documents_still_name_the_command(self):
        for name, path in (("docs/development.md", REPO_ROOT / "docs" / "development.md"),
                           ("specs/README.md", REPO_ROOT / "specs" / "README.md")):
            text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            with self.subTest(file=name):
                self.assertRegex(
                    text, self.REWORKED,
                    "%s no longer names `/delegate-to-mcp-server` at all. The rework (#114) is "
                    "recorded by naming the command and saying what it does now -- dropping the "
                    "row instead leaves no way to tell a reworked command from one nobody "
                    "documented" % name)

    def test_both_documents_describe_it_as_filing_issues(self):
        for name, path in (("docs/development.md", REPO_ROOT / "docs" / "development.md"),
                           ("specs/README.md", REPO_ROOT / "specs" / "README.md")):
            text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            with self.subTest(file=name):
                self.assertRegex(
                    text, self.FILES_ISSUES,
                    "%s names the command but does not say it files issues now (#114). A "
                    "reader is left with a command whose output format is unstated, which is "
                    "how the previous claim survived eight days after it stopped being true"
                    % name)

    def test_the_scan_no_longer_exempts_it(self):
        """⛔ The exemption and the inversion must go together, or one re-opens the other."""
        source = Path(__file__).read_text(encoding="utf-8")
        marker = "One maintainer command still writes spec files -- `/delegate-to-mcp-server`"
        before, _, after = source.partition("LEGITIMATE = (")
        self.assertNotIn(
            marker, after.split(")\n")[0],
            "the delegate phrasing is still pinned as LEGITIMATE while this class asserts the "
            "command was reworked. Those two cannot both be right: a wording held up as "
            "correct prose is one the scan will never report")


if __name__ == "__main__":
    unittest.main()
