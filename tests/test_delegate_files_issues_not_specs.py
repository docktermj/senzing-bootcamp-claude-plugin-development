"""`/delegate-to-mcp-server` files GitHub issues and writes nothing into the frozen archive.

It was the last command that still wrote spec files. Under the `specs/` freeze (INV-307) its
output had nowhere to land, so running it produced a file `tests/test_specs_are_frozen.py`
rejects -- a maintenance capability the repository believed it had and did not. #114 reworked
the output path to file issues, matching `/feedback-to-issues` (#49).

⛔ **This pins the SHAPE of the rework, never that a run behaves correctly.** Nothing offline
can observe the command filing an issue, and this guard does not pretend to: it asserts the
instructions say to file issues, name the approval gate, forbid `--repo`, and carry an issue
template rather than a spec template. ⚠️ **A run's actual behavior is unobservable here** --
only a real invocation shows it, and a real invocation files real issues, so it is not a test
this suite can run.

⚠️ **The ledger is not an exception to the freeze.** `specs/mcp-coverage.jsonl` lives under
`specs/` and is still written to, which looks like a carve-out and is not: the freeze guard
globs `*.md`, so a `.jsonl` file is outside it **by construction**. Asserted below, because a
reader who assumes an exemption will eventually grant a real one.

Stdlib only; every file is read as text (INV-108).

Source issue: #114.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "delegate-to-mcp-server"
SKILL = SKILL_DIR / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "delegate-to-mcp-server.md"
LEDGER_SCRIPT = SKILL_DIR / "coverage_ledger.py"
ISSUE_TEMPLATE = SKILL_DIR / "issue-template.md"
SPEC_TEMPLATE = SKILL_DIR / "spec-template.md"

#: The instruction that makes the output a GitHub issue rather than a file.
FILES_ISSUES = re.compile(r"gh issue create", re.I)

#: ⛔ The approval gate. Filing is outward-facing and cannot be undone.
APPROVAL_GATE = re.compile(
    r"(?:show the maintainer|get (?:an )?explicit yes|before filing)", re.I)

#: ⛔ The parent never files into a child (R2): propagation is a pull from a tagged release.
NO_REPO_FLAG = re.compile(r"never pass `--repo`", re.I)


def text(path):
    return path.read_text(encoding="utf-8")


class TheInputsAreReal(unittest.TestCase):
    """INV-265 -- every assertion below reads these files."""

    def test_the_skill_and_its_command_exist(self):
        for name, path in (("SKILL.md", SKILL), ("command", COMMAND),
                           ("coverage_ledger.py", LEDGER_SCRIPT)):
            with self.subTest(what=name):
                self.assertTrue(path.is_file(), "%s is missing at %s" % (name, path))


class TheTemplateIsAnIssueTemplate(unittest.TestCase):
    """Acceptance: `spec-template.md` is gone; an issue template replaces it."""

    def test_the_spec_template_is_gone(self):
        self.assertFalse(
            SPEC_TEMPLATE.exists(),
            "%s still exists. It is the output format this rework replaced; leaving it means "
            "a run can still be told to produce a spec file" % SPEC_TEMPLATE)

    def test_an_issue_template_replaces_it(self):
        self.assertTrue(
            ISSUE_TEMPLATE.is_file(),
            "%s is missing. Deleting the spec template without providing an issue template "
            "leaves the skill naming a template that does not exist" % ISSUE_TEMPLATE)

    def test_the_skill_points_at_the_issue_template(self):
        self.assertIn(
            "issue-template.md", text(SKILL),
            "SKILL.md does not name `issue-template.md`, so the file exists and nothing "
            "directs a run to it")

    def test_nothing_still_points_at_the_spec_template(self):
        for name, path in (("SKILL.md", SKILL), ("command", COMMAND)):
            with self.subTest(what=name):
                self.assertNotIn(
                    "spec-template.md", text(path),
                    "%s still names `spec-template.md`, which no longer exists -- a pointer "
                    "that reads as authoritative and resolves to nothing" % name)


class TheOutputPathIsAnIssue(unittest.TestCase):
    """Acceptance: it files GitHub issues, deduplicated, behind the maintainer's yes."""

    def test_the_skill_says_to_file_an_issue(self):
        self.assertRegex(
            text(SKILL), FILES_ISSUES,
            "SKILL.md never names `gh issue create`. Saying 'file an issue' without the "
            "command is how the previous version said 'write a spec' and produced a file "
            "nobody could land")

    def test_filing_is_gated_on_the_maintainers_yes(self):
        self.assertRegex(
            text(SKILL), APPROVAL_GATE,
            "SKILL.md does not gate filing on the maintainer's approval. An issue is visible "
            "the moment it is created, cannot be un-filed, and its notifications have already "
            "gone out -- the same reason Step 8 gates `submit_feedback`")

    def test_the_parent_never_files_into_a_child(self):
        for name, path in (("SKILL.md", SKILL), ("command", COMMAND)):
            with self.subTest(what=name):
                self.assertRegex(
                    text(path), NO_REPO_FLAG,
                    "%s does not forbid `--repo`. This is the parent repository; "
                    "parent-to-child change travels by parity from a tagged release, so the "
                    "parent never files into a child at all" % name)

    def test_the_ledger_records_an_issue_number(self):
        self.assertIn(
            "--issue", text(SKILL),
            "SKILL.md's Step 9 does not record `--issue`, so a filed issue leaves no "
            "provenance on the ledger row and the next sweep re-litigates it")


class NothingIsWrittenIntoTheFrozenArchive(unittest.TestCase):
    """⛔ INV-307 -- the reason this rework was needed at all."""

    def test_the_skill_forbids_writing_under_specs(self):
        self.assertRegex(
            text(SKILL), r"Write nothing under `specs/`",
            "SKILL.md no longer forbids writing under `specs/`. That prohibition is the "
            "point of this rework, not a side effect of it")

    def test_the_ledger_is_explained_as_a_named_live_exception(self):
        """⚠️ It lives under `specs/` and is still written. That needs stating, not assuming.

        ⛔ **This assertion used to require the OPPOSITE explanation and was renamed (#142).**
        It demanded the phrase *"by construction"* / *"not `*.md`"* — pinning the claim that the
        ledger escapes the freeze because the guard globs `specs/*.md` and a `.jsonl` slips
        past. ⚠️ **That is a permission resting on a guard's blind spot**, and this repository
        rejects the identical reasoning elsewhere: `invariant_manifest.py` puts its artifact at
        the repository root rather than in `specs/` precisely so its legality does not depend on
        *"a scope-narrowing that happens to produce correct behavior, which INV-308 says must
        not be relied on."* Widening the freeze guard would have silently revoked an exception
        nobody had written down — and `docs/FAMILY_WORKFLOW.md` §8 said *"four live exceptions"*
        while this was the fifth.

        The ledger is now a **recorded decision** in INV-307 and §8, and both sites must say so.
        """
        for name, path in (("SKILL.md", SKILL), ("command", COMMAND)):
            with self.subTest(what=name):
                body = re.sub(r"\s+", " ", text(path))
                self.assertRegex(
                    body, r"mcp-coverage\.jsonl.{0,200}?(?:named live exception|live exception)",
                    "%s writes `specs/mcp-coverage.jsonl` without saying it is a NAMED live "
                    "exception to the freeze. An exception is a decision and belongs in "
                    "INV-307 and FAMILY_WORKFLOW.md §8; a reader told only that the guard does "
                    "not reach it has been given a blind spot, not a permission" % name)

    def test_neither_site_still_rests_on_the_glob(self):
        """⛔ The retired justification must not survive anywhere, in either copy."""
        for name, path in (("SKILL.md", SKILL), ("command", COMMAND)):
            with self.subTest(what=name):
                body = re.sub(r"\s+", " ", text(path))
                stale = re.search(
                    r"mcp-coverage\.jsonl[^.]{0,120}?(?:is|sits)[^.]{0,80}?outside the freeze "
                    r"by construction", body)
                self.assertIsNone(
                    stale,
                    "%s still justifies the ledger as outside the freeze *by construction*. "
                    "That reasoning was retired by #142: it rests on the guard globbing "
                    "`specs/*.md`, so it evaporates the moment anyone widens the guard" % name)

    def test_the_ledger_is_in_the_documented_exception_list(self):
        """The decision is recorded where a reader looks for it, not only where it is used."""
        section = text(REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md")
        self.assertIn(
            "specs/mcp-coverage.jsonl", section,
            "docs/FAMILY_WORKFLOW.md does not list `specs/mcp-coverage.jsonl` among the live "
            "exceptions to the freeze, so a live file under a read-only archive is recorded "
            "nowhere a reader would look")

    def test_the_freeze_guard_still_globs_markdown(self):
        """⚠️ Kept, with its reason corrected.

        This asserted the `*.md` glob *because* the ledger's exemption depended on it. That
        dependency is gone (#142). The glob is still worth pinning — the freeze's enforced
        subject is `specs/*.md` and a reader of INV-307 should be able to rely on that — but
        a change to it is now a scope question, no longer a silent revocation.
        """
        guard = text(REPO_ROOT / "tests" / "test_specs_are_frozen.py")
        self.assertIn(
            'glob("*.md")', guard,
            "the freeze guard no longer globs `*.md`; INV-307's enforced subject has moved and "
            "the exception list should be re-read against it")


class TheClaimIsBoundToTheCommand(unittest.TestCase):
    """⛔ A document-wide match is satisfied by a DIFFERENT command's row.

    ⚠️ Found by this guard's own negative control. `specs/README.md` lists five reworked
    commands, four of which already said "files GitHub issues". Deleting the
    `/delegate-to-mcp-server` row entirely left a file that still matched "files issues"
    somewhere -- so the assertion passed over a document that had stopped making the claim
    at all. Proximity to the subject is what makes the match mean anything.
    """

    #: How far from the command name the claim must appear. One table row, generously.
    WINDOW = 160

    def claim_near_the_command(self, path):
        body = re.sub(r"\s+", " ", text(path))
        for m in re.finditer(r"delegate-to-mcp-server", body, re.I):
            window = body[m.start():m.start() + self.WINDOW]
            if re.search(r"files?\s+(?:GitHub\s+)?issues", window, re.I):
                return True
        return False

    def test_each_document_says_THIS_command_files_issues(self):
        for name, path in (("docs/development.md", REPO_ROOT / "docs" / "development.md"),
                           ("specs/README.md", REPO_ROOT / "specs" / "README.md")):
            with self.subTest(file=name):
                self.assertTrue(
                    self.claim_near_the_command(path),
                    "%s never says that `/delegate-to-mcp-server` files issues within %d "
                    "characters of naming it. The file may still match 'files issues' "
                    "elsewhere -- four other commands say it -- which is exactly the match "
                    "this assertion must not accept" % (name, self.WINDOW))

    def test_the_proximity_check_rejects_a_distant_match(self):
        """INV-282 -- the negative pinned beside the positive, or the window proves nothing."""
        self.assertFalse(
            re.search(r"files?\s+(?:GitHub\s+)?issues",
                      ("delegate-to-mcp-server" + " padding" * 60)[:self.WINDOW], re.I),
            "a window of %d characters already contains the claim before any real text does, "
            "so the proximity check would accept any document naming the command"
            % self.WINDOW)


class TheStaleWarningIsGone(unittest.TestCase):
    """Acceptance: `docs/development.md` no longer warns against running it."""

    def test_development_md_does_not_warn_against_running_it(self):
        body = re.sub(r"\s+", " ", text(REPO_ROOT / "docs" / "development.md"))
        self.assertNotRegex(
            body, r"should not be run until its rework lands",
            "docs/development.md still tells the maintainer not to run a command that now "
            "works. That warning is what #114 set out to remove")

    def test_no_live_document_claims_it_has_no_issue(self):
        """⛔ The claim was false from the day #114 was filed, and had four homes."""
        scanned = (sorted((REPO_ROOT / "docs").rglob("*.md"))
                   + [REPO_ROOT / "specs" / "README.md"])
        offenders = [str(p.relative_to(REPO_ROOT)) for p in scanned
                     if "no issue yet" in text(p)]
        self.assertEqual(
            [], offenders,
            "live document(s) still say the command has no issue: %s. #114 IS that issue, so "
            "the claim has been false since the day it was filed" % offenders)


if __name__ == "__main__":
    unittest.main()
