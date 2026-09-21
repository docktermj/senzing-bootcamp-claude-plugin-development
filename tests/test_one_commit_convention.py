"""One commit convention is documented, and no normal path needs the hook bypassed.

This repository ran **two** commit conventions on purpose. `.claude/memory/` required
`#<issue-number> <description>` subjects for *"the `implement-spec` skill, or any change made
while processing a spec under `specs/`"* — deliberately **not** Conventional Commits — with the
reminder hook bypassed via `SKIP_GIT_CONVENTIONS=1`. Everything else used Conventional Commits.

⛔ **That scope stopped describing anything.** `specs/` froze at the 2026-09-15 cutover (INV-307)
and `/implement-spec` was retired under #60, so issue work fell in the gap between the two rules
(#56).

⚠️ **And the stale rule went unnoticed because behavior had already moved.** Commits were being
written as Conventional Commits with an `issue: #<n>` trailer — correctly, per the `commit`
skill — while the memory said otherwise. Guidance and behavior diverged **silently**, which is
the failure this guard exists to make loud.

⚠️ **`Refs: #n` was proposed and is not what shipped.** #56's 2026-09-15 decision named that
footer; `issue: #n` was already in use and is what the `commit` skill mandates, so the repo
writes `issue:`. Both link identically — GitHub scans the whole message for `#<number>`. A second
trailer form would have split the history for nothing, so this guard pins the **property** (an
issue reference in a trailer, not the subject) rather than one spelling of it.

⛔ **This asserts what the documents INSTRUCT, never what a commit contains.** No offline test
reads git history here, and a repository can document one convention while its commits use
another — which is exactly what happened. `tests/test_spec_ledger_invariants.py` checks recorded
hashes; nothing checks message shape, and this does not either.

Stdlib only; every file is read as text (INV-108).

Source issue: #56.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY = REPO_ROOT / ".claude" / "memory"
DOCS = sorted((REPO_ROOT / ".claude").rglob("*.md")) + sorted((REPO_ROOT / "docs").rglob("*.md"))

#: An instruction to put the issue number in the SUBJECT, which is the retired convention. The
#: matcher targets the act -- prefixing a title/subject with `#n` -- not the phrasings that
#: shipped (INV-282).
#: Both orders occur -- "the title must be prefixed with `#n`" and "use `#n ...` as the subject"
#: -- so the claim is matched rather than one sentence shape: an instruction, the issue token,
#: and the words subject/title, in either arrangement. ⚠️ The verbs are \b-anchored so "used to
#: require" (history) does not read as "use".
SUBJECT_PREFIX_RULE = re.compile(
    r"(?:title|subject)[^.]{0,80}?prefix[^.]{0,40}?`?#<?(?:issue[- ]?number|n)>?"
    r"|\b(?:prefix|prefixed|use|must be)\b[^.]{0,80}?#<?(?:issue[- ]?number|n)>?"
    r"[^.]{0,80}?(?:subject|title)",
    re.I)

#: An instruction to bypass the reminder hook. Prose ABOUT the bypass existing is legitimate;
#: telling a normal path to use it is not, so the matcher requires an imperative near it.
BYPASS_INSTRUCTION = re.compile(
    r"(?:use|prefix|run|add)[^.]{0,60}?SKIP_GIT_CONVENTIONS", re.I)

#: Pinned so the matchers cannot be narrowed until they stop catching what actually shipped.
RETIRED_WORDINGS = (
    "the commit **title** must be prefixed with `#<issue-number> ` followed by a plain description",
    "use `#n <description>` as the subject",
    "prefix the commit command with `SKIP_GIT_CONVENTIONS=1` to bypass that reminder",
)

#: Constructions that must stay legal. A guard that flags these is relaxed rather than fixed.
LEGITIMATE = (
    "Keep the `#` (`issue: #42`, not `issue: 42`), or it links nothing.",
    "The `SKIP_GIT_CONVENTIONS=1` escape exists for genuinely non-conforming commits",
    "The alternative was to instruct a `SKIP_GIT_CONVENTIONS=1` bypass of the convention",
    "this memory used to require `#<issue-number> <description>` subjects",
)


def hits(text):
    return [m.group(0) for p in (SUBJECT_PREFIX_RULE, BYPASS_INSTRUCTION)
            for m in p.finditer(text)]


class TheMatchersAreCalibrated(unittest.TestCase):
    """⛔ INV-282 — pinned in both directions, or the sweep below proves nothing."""

    def test_every_retired_wording_is_caught(self):
        for wording in RETIRED_WORDINGS:
            with self.subTest(wording=wording[:46]):
                self.assertTrue(
                    hits(wording),
                    "a wording that actually shipped is not matched: %r" % wording)

    def test_no_legitimate_construction_is_caught(self):
        for wording in LEGITIMATE:
            with self.subTest(wording=wording[:46]):
                self.assertEqual(
                    [], hits(wording),
                    "correct prose is flagged: %r. Naming the bypass, or recording that the old "
                    "rule existed, must stay sayable -- a guard that forbids describing history "
                    "deletes the reason with the error" % wording)


class OnlyOneConventionIsDocumented(unittest.TestCase):
    def test_the_scan_has_files_to_read(self):
        """INV-265 — the sweep passes trivially over an empty file list."""
        self.assertGreater(
            len([f for f in DOCS if f.is_file()]), 20,
            "fewer than 20 documents found under .claude/ and docs/; the paths have moved")

    def test_no_document_instructs_the_retired_convention(self):
        offenders = []
        for f in DOCS:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                for hit in hits(line):
                    offenders.append("%s:%d  %r" % (f.relative_to(REPO_ROOT), n, hit))
        self.assertEqual(
            [], offenders,
            "a document still instructs the retired convention -- an issue number in the "
            "subject, or bypassing the reminder hook on a normal path. One convention covers "
            "this repository (#56):\n  " + "\n  ".join(offenders))


class TheCurrentRuleIsStatedWhereItIsRead(unittest.TestCase):
    """⛔ Removing the old rule without stating the new one leaves nothing to follow."""

    def test_the_memory_states_conventional_commits_and_the_trailer(self):
        names = [f.name for f in MEMORY.glob("*.md")]
        self.assertIn(
            "commit-message-format.md", names,
            "the commit-convention memory is gone. It is the file that tells a run how to "
            "write a commit here; deleting it leaves the rule in a skill shared with other "
            "projects and nothing repository-specific. Found: %s" % names)
        text = re.sub(r"\s+", " ", (MEMORY / "commit-message-format.md").read_text(encoding="utf-8"))
        self.assertIn("Conventional Commits", text, "the memory no longer names the convention")
        self.assertRegex(
            text, r"issue: #<?n?",
            "the memory no longer names the issue trailer, so nothing says how a commit is "
            "linked to its issue now that the subject does not carry the number")

    def test_the_index_points_at_the_renamed_file(self):
        index = (MEMORY / "MEMORY.md").read_text(encoding="utf-8")
        self.assertIn(
            "commit-message-format.md", index,
            "MEMORY.md does not point at the commit-convention memory; the index is what is "
            "loaded each session, so a memory missing from it is one nobody reads")
        self.assertNotIn(
            "spec-commit-message-format.md", index,
            "MEMORY.md still points at the pre-#56 filename, which no longer exists")


if __name__ == "__main__":
    unittest.main()
