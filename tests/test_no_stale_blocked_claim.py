"""No live document says the audit half is blocked, or that the audit writes spec files.

`/production-readiness-audit` wrote spec files into the frozen archive, and `/unattended-issue-loop`
therefore carried a blocked audit half. **#69 fixed both on 2026-09-16.** The prose describing the
old world was not swept, so on 2026-09-21 — five days later — **five sites still said otherwise**,
including `docs/development.md`, which told the maintainer ⛔ *not to run a command that works*.
One of them, `tests/test_unattended_loop_is_label_gated.py`, contradicted **itself**: its module
docstring said the audit half was blocked while its own class forty lines down recorded the
assertion as inverted because #69 fixed it. (#90, found by the 2026-09-21 audit.)

⛔ **The matcher is derived from the CLAIM, not from the five phrasings that shipped** (INV-282).
The claim has two halves — *the audit half is blocked* and *`/production-readiness-audit` writes
specs* — and each is matched by its subject plus a present-tense predicate, so a sixth wording
nobody has written yet is caught too.

⚠️ **The hard half is what this must NOT flag, and it is pinned beside the positives.** Three
constructions are legitimate and must stay legal:

* **History**, in the past tense — "the audit half **was** blocked", "this paragraph **said** the
  audit half was blocked until 2026-09-21". Recording why a rule exists is this repository's
  house style, and a guard that forbade it would delete the reason along with the error.
* **The one command the claim is still true of** — `/delegate-to-mcp-server` **does** still write
  specs and has no issue. "One maintainer command still writes spec files" is correct prose.
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

#: "`/production-readiness-audit` (still) writes spec(s)" — bound to that actor, because the same
#: predicate is TRUE of `/delegate-to-mcp-server` and must stay sayable about it.
AUDIT_WRITES_SPECS = re.compile(
    r"production-readiness-audit`?\s*(?:still\s+)?writes?\s+spec", re.I)

#: Every phrasing that actually shipped, pinned so the matcher cannot be narrowed until it
#: stops catching them (INV-282).
SHIPPED_PHRASINGS = (
    "its audit half stays blocked while `/production-readiness-audit` writes specs",
    "⛔ **The audit half is BLOCKED and the loop must say so.**",
    "`/production-readiness-audit` still writes spec files into the frozen archive",
    "with its audit half blocked for exactly this reason",
)

#: Constructions that MUST NOT be flagged. A guard that flags correct prose is relaxed rather
#: than fixed, and each of these is prose this repository needs to keep writing.
LEGITIMATE = (
    "The audit half WAS blocked, and this docstring said so five days after it stopped",
    "This paragraph said the audit half was blocked until 2026-09-21",
    "One maintainer command still writes spec files -- `/delegate-to-mcp-server`",
    "⛔ **Still writes specs**; needs the same rework, no issue yet",
    "`/production-readiness-audit` files a GitHub issue when attended",
    "`/production-readiness-audit` wrote spec files into the frozen archive, so an unattended",
)


def hits(text):
    return [m.group(0) for p in (AUDIT_HALF_BLOCKED, AUDIT_WRITES_SPECS)
            for m in p.finditer(text)]


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


class TheOneCommandStillWritingSpecsIsStillNamed(unittest.TestCase):
    """⛔ Over-correcting into "everything is fixed" would hide the one real remaining case."""

    def test_delegate_to_mcp_server_is_still_described_as_writing_specs(self):
        for name, path in (("docs/development.md", REPO_ROOT / "docs" / "development.md"),
                           ("specs/README.md", REPO_ROOT / "specs" / "README.md")):
            text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            with self.subTest(file=name):
                self.assertRegex(
                    text, r"delegate-to-mcp-server",
                    "%s no longer names `/delegate-to-mcp-server`, the one command that DOES "
                    "still write spec files. Sweeping the fixed claims must not take the "
                    "unfixed one with them" % name)
                self.assertRegex(
                    text.lower(), r"(still writes specs|still\s+writes\s+spec files)",
                    "%s no longer says any command still writes specs. One does, it has no "
                    "issue, and running it turns the suite red" % name)


if __name__ == "__main__":
    unittest.main()
