"""The audit records findings as issues or in the ledger, never into the frozen archive.

`/production-readiness-audit` told a run to write each finding into `specs/` as it found it.
`specs/` froze at the 2026-09-15 cutover (INV-307) and `tests/test_specs_are_frozen.py`
rejects any new file there, so every finding landed as output the freeze guard fails on.

⚠️ **It was the third command still writing specs and the only one nobody had filed against**
— missed because it files *findings* rather than "specs" by name, which is the word the
migration audit searched for.

⛔ **The attended and unattended paths are DIFFERENT, and that asymmetry is the substance of
#69 rather than an accident of it.** Switching the output format alone would have replaced
"writes output the freeze guard rejects" with "performs an outward-facing act the autonomy
contract forbids":

* **Attended** — file a GitHub issue, after showing the maintainer the title and body and
  getting a yes. Filing is immediate and visible the moment it happens; an issue can be
  edited or closed but never un-filed.
* **Unattended** — ⛔ **file nothing.** `gh issue create` **leaves the machine**, and
  `/unattended-issue-loop`'s contract is that nothing leaves the machine unattended. The
  finding goes into the dated ledger entry and the handoff, marked *not filed*.

⚠️ **A later editor will reasonably want to collapse those two branches into one.** The
assertions below pin both, so collapsing them fails rather than quietly re-arming an
outward-facing act inside an unattended run.

⛔ **The self-feeding hazard has its own assertion.** An audit that applied `unattended-ok`
to issues it filed would let the loop work findings **it generated itself**, with no
maintainer between generation and execution. `/unattended-issue-loop` already forbids a run
adding the label — but that rule lives in the loop's file, and the audit is a different
command whose reader may never open it.

⛔ **This asserts what the skill INSTRUCTS, never what a run does.** No offline test can
observe `gh issue create` being called, or — harder still — *not* being called. Nothing here
establishes that an unattended run refrains from filing; only that it is told to, in terms a
later editor cannot quietly drop.

Stdlib only; both files are read as text (INV-108).

Source issue: #69 — titled for the defect it fixed, which has not described this command
since 2026-09-16. The number is the citation; the old title is not repeated here, because
a line quoting it reads as a present-tense claim about current behavior (#90).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude" / "skills" / "production-readiness-audit" / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "production-readiness-audit.md"

#: An instruction to WRITE a finding into the archive, as opposed to reading it or
#: forbidding the write. `specs/IMPLEMENTED.md` and `specs/INVARIANTS.md` are live records
#: the audit legitimately reads and appends to, so the pattern targets the act, not the path.
WRITES_A_FINDING = re.compile(
    r"(?i)write it into `?specs/|one spec per\s+root cause|write the spec\b")


def texts():
    return {"SKILL.md": SKILL.read_text(encoding="utf-8"),
            "command": COMMAND.read_text(encoding="utf-8")}


def flat(s):
    return re.sub(r"\s+", " ", s).lower()


class BothFilesExist(unittest.TestCase):
    """Anti-vacuity: every assertion below reads these, so they must be real."""

    def test_the_files_exist(self):
        for name, path in (("skill", SKILL), ("command", COMMAND)):
            with self.subTest(what=name):
                self.assertTrue(
                    path.is_file(),
                    "%s is missing at %s; every assertion in this module would pass on an "
                    "empty read" % (name, path))


class NothingIsWrittenIntoTheFrozenArchive(unittest.TestCase):
    """INV-307 — the archive is read-only, and the freeze guard rejects new files."""

    def test_no_instruction_writes_a_finding_into_specs(self):
        for name, text in texts().items():
            hit = WRITES_A_FINDING.search(text)
            with self.subTest(file=name):
                self.assertIsNone(
                    hit, "%s still instructs writing a finding into the archive (%r). "
                         "`specs/` is read-only (INV-307) and the freeze guard rejects the "
                         "output" % (name, hit.group(0) if hit else ""))

    def test_the_prohibition_is_stated(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"never write into `?specs/",
            "the skill does not say `specs/` may not be written to, so a reader has no way "
            "to know why findings go elsewhere now")

    def test_reading_the_archive_is_still_permitted(self):
        """Over-correcting into 'never touch specs/' would break the audit's own inputs."""
        self.assertIn(
            "specs/IMPLEMENTED.md", texts()["SKILL.md"],
            "the skill no longer reads specs/IMPLEMENTED.md. It is live, exempt from the "
            "freeze, and both the audit's own dated record and the prior-audit context it "
            "must read before starting")


class TheTwoPathsStayDifferent(unittest.TestCase):
    """⛔ Collapsing them re-arms an outward-facing act inside an unattended run."""

    def test_the_attended_path_files_an_issue(self):
        self.assertIn(
            "gh issue create", texts()["SKILL.md"],
            "the skill never names `gh issue create`, so an attended audit has no stated way "
            "to record a finding durably")

    def test_filing_is_gated_on_the_maintainer(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"get a yes first|getting a yes",
            "filing is no longer gated on the maintainer. It is outward-facing and immediate "
            "-- an issue can be edited or closed afterwards but never un-filed -- which is "
            "the same reason /feedback-to-issues gates it")

    def test_the_unattended_path_files_nothing(self):
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"file nothing|files nothing",
                    "%s does not say an unattended audit files nothing. `gh issue create` "
                    "leaves the machine, and /unattended-issue-loop's contract is that "
                    "nothing leaves the machine unattended" % name)

    def test_the_unattended_finding_still_lands_somewhere(self):
        """'File nothing' without a destination loses the finding entirely."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"not filed",
            "the unattended path says what not to do but never where the finding goes. A "
            "finding held in conversation dies at session end, which is the failure the "
            "whole of Step 8 exists to prevent")


class TheAuditNeverLabelsItsOwnFindings(unittest.TestCase):
    """The self-feeding hazard: an audit that labels its output arms the loop on it."""

    def test_it_never_applies_the_opt_in_label(self):
        for name, text in texts().items():
            with self.subTest(file=name):
                self.assertRegex(
                    flat(text), r"never apply the `?unattended-ok`? label",
                    "%s does not forbid applying `unattended-ok` to an issue it files. An "
                    "audit that labels its own findings lets /unattended-issue-loop work "
                    "issues it generated itself, with no maintainer in between" % name)


class TheAbsenceClauseIsCarried(unittest.TestCase):
    """INV-213, whose subject was widened to cover issues on 2026-09-16."""

    def test_owner_checked_is_required(self):
        self.assertIn(
            "owner-checked:", texts()["SKILL.md"],
            "the skill no longer requires `owner-checked:` on an absence claim (INV-213). An "
            "empty result from the wrong route reads exactly like evidence of absence")


if __name__ == "__main__":
    unittest.main()
