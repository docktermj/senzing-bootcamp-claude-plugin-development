"""The skills whose user-level copy governs say so, and the repository keeps only its overlay.

`implement-github-issue` and `unattended-issue-loop` each had a full `SKILL.md` here and another
under `~/.claude/skills/`. The user-level copy is the one that loads, and the two had drifted
into different procedures: the project loop described local-only implement-then-audit cycles
while the loop that ran merged nine PRs on 2026-09-28, and the project `implement-github-issue`
claimed a shared block the user-level copy no longer had. The tests here checked the copies that
did not run (#215).

#215 turned the project `SKILL.md` into a pointer stub and the command file into the repo
overlay. #239 finished the job: a skill name is defined in one place, so for both skills

* this repository defines **neither name**: no `.claude/skills/<name>/` and no
  `.claude/commands/<name>.md`;
* the **repo overlay** is `.claude/skill-overlays/<name>.md`, which is neither a skill nor a
  command: no frontmatter, no command boilerplate, only this repository's obligations plus one
  line naming the governing copy, which is told to read the overlay;
* the loop's merge policy is stated once, in the `docs/FAMILY_WORKFLOW.md` §2 row (INV-300);
* the old tracked run-state directory is gone. The governing copy keeps state under
  `<git-common-dir>/claude-state/`.

⚠️ **`~/.claude/skills/` is NOT checked in CI, and nothing here reads it.** A CI runner checks
out only the repository, so a test reading the governing copy would fail there and pass on one
machine (INV-308). Nothing here can see the governing copies' `argument-hint`, which is why #239
dropped the check that pinned it: the command files that carried a copy of the hint are gone.

⚠️ **What this does NOT establish:** that the governing copy actually reads the overlay, or
that a run meets the overlay's obligations. It pins that the repository's text points the right
way and holds no second procedure.

#294 added `order-github-issues` to `GOVERNED`. It never had a copy here; its overlay exists so
that `/order-github-issues` *(user level)* resolves to something this repository can check
(INV-316), and says that the governing copy has no overlay hook and that this repository adds
no obligations.

Source issues: #215, #239, #294.

Stdlib only; every surface is read as text (INV-108).

Run:  python3 -m unittest discover -s tests

INV-337 is the invariant this module enforces: a skill governed at user level is not also defined
here, and the repository keeps only its overlay. Like the rest of this module it checks the
repository's side; it cannot establish what the user-level copy says on any machine (INV-308).
⚠️ It covers only the skills named in `GOVERNED`, a fixed list: it cannot find a skill governed
at user level that the list leaves out, because CI cannot list `~/.claude` (#395).
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE = REPO_ROOT / ".claude"
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"

#: The skills whose user-level copy governs. This repository carries only their overlays.
#:
#: ⚠️ **A fixed list, and the guard cannot see past it (INV-308).** Every check below reads only
#: the names here. A skill governed at user level that is missing from this tuple is checked by
#: nothing, and this guard cannot find it: that would mean listing `~/.claude/skills/`, which a
#: CI runner does not have. Adding a name here is a manual step whenever an overlay is added
#: under `.claude/skill-overlays/` (#395). A check that this tuple matches that directory was
#: considered and not chosen.
GOVERNED = ("implement-github-issue", "unattended-issue-loop", "order-github-issues")

#: Command boilerplate an overlay must not carry: it is not a command (#239).
BOILERPLATE = (r"\$ARGUMENTS", r"(?i)\binvoke the `[a-z-]+` skill", r"(?im)^maintainer request:",
               r"(?i)pointer stub")

#: The merge-policy clause. It must appear exactly once in the repository's own text.
MERGE_POLICY = re.compile(r"`--no-merge` leaves every PR open")


def overlay(name):
    return CLAUDE / "skill-overlays" / ("%s.md" % name)


def normative(text):
    """Text with FAMILY_WORKFLOW's §10 amendment log removed; the log quotes old wording."""
    i = text.find("## 10. Amendments")
    return text[:i] if i != -1 else text


def own_markdown():
    """The repository's own Markdown under `.claude/` and `docs/`, never a scratch worktree."""
    for root in (CLAUDE, REPO_ROOT / "docs"):
        for p in sorted(root.rglob("*.md")):
            if "worktrees" in p.relative_to(REPO_ROOT).parts:
                continue
            yield p


class ThisRepositoryDefinesNeitherName(unittest.TestCase):
    """A skill name is defined in one place, and for these two that place is `~/.claude/skills/`."""

    def test_no_project_skill_or_command_carries_the_name(self):
        for name in GOVERNED:
            for path in (CLAUDE / "skills" / name, CLAUDE / "commands" / ("%s.md" % name)):
                with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                    self.assertFalse(
                        path.exists(),
                        "%s is back. It is a second definition of a name the user-level copy "
                        "already defines; the repository's rules for it belong in %s"
                        % (path.relative_to(REPO_ROOT), overlay(name).relative_to(REPO_ROOT)))


class TheOverlaysAreRepoOnly(unittest.TestCase):
    def test_each_overlay_exists(self):
        for name in GOVERNED:
            with self.subTest(skill=name):
                self.assertTrue(overlay(name).is_file(), "%s is missing" % overlay(name))

    def test_no_overlay_carries_frontmatter_or_command_boilerplate(self):
        for name in GOVERNED:
            text = overlay(name).read_text(encoding="utf-8")
            with self.subTest(skill=name, what="frontmatter"):
                self.assertFalse(text.startswith("---"),
                                 "the overlay has frontmatter, so it reads as a command or a "
                                 "skill again")
            for pattern in BOILERPLATE:
                with self.subTest(skill=name, what=pattern):
                    self.assertNotRegex(text, pattern)

    def test_each_overlay_states_the_ci_limit(self):
        """INV-308: the overlay is the one place a reader learns the governing copy is unchecked."""
        for name in GOVERNED:
            text = re.sub(r"\s+", " ", overlay(name).read_text(encoding="utf-8"))
            with self.subTest(skill=name):
                self.assertIn("not checked in CI", text)

    def test_each_overlay_names_the_governing_copy(self):
        for name in GOVERNED:
            text = re.sub(r"\s+", " ", overlay(name).read_text(encoding="utf-8"))
            with self.subTest(skill=name):
                self.assertRegex(
                    text, r"governing copy is `~/\.claude/skills/%s/SKILL\.md`" % re.escape(name))

    def test_the_implement_overlay_no_longer_restates_the_no_argument_review(self):
        text = overlay("implement-github-issue").read_text(encoding="utf-8")
        for stale in ("review the open issues for dependencies", "is **empty**"):
            with self.subTest(stale=stale):
                self.assertNotIn(
                    stale, text,
                    "the overlay restates the no-argument dependency review. R8 now gives it to "
                    "the operation that chooses the issue; a second statement here drifts")

    def test_the_loop_overlay_asks_no_push_policy_and_runs_no_audit(self):
        text = overlay("unattended-issue-loop").read_text(encoding="utf-8")
        for stale in (r"(?i)push policy", r"(?i)local[ -]only", r"(?i)audit cycle",
                      r"/production-readiness-audit"):
            with self.subTest(stale=stale):
                self.assertNotRegex(
                    text, stale,
                    "the loop overlay still describes the retired local-only "
                    "implement-then-audit loop, which is not the loop that runs")

    def test_the_loop_overlay_sends_workers_to_the_implement_overlay(self):
        text = overlay("unattended-issue-loop").read_text(encoding="utf-8")
        self.assertIn(".claude/skill-overlays/implement-github-issue.md", text,
                      "the loop overlay does not bind its workers to the implement overlay, so "
                      "INV-309 and the ledger reach them only if the lead copies them by hand")


class TheMergePolicyIsStatedOnce(unittest.TestCase):
    def test_it_is_stated_in_the_family_row(self):
        row = [l for l in FAMILY.read_text(encoding="utf-8").splitlines()
               if l.startswith("| `unattended-issue-loop` |")]
        self.assertEqual(1, len(row), "the §2 row for unattended-issue-loop is missing")
        self.assertRegex(row[0], MERGE_POLICY)
        self.assertRegex(row[0], r"(?i)\bmerges\b")

    def test_nowhere_else_restates_it(self):
        hits = []
        for p in own_markdown():
            text = p.read_text(encoding="utf-8")
            if p == FAMILY:
                text = normative(text)
            hits += [str(p.relative_to(REPO_ROOT))] * len(MERGE_POLICY.findall(text))
        self.assertEqual(["docs/FAMILY_WORKFLOW.md"], hits,
                         "the loop's merge policy is stated in more than one place, or none "
                         "(INV-300): %s" % hits)

    def test_the_overlay_links_to_the_row(self):
        self.assertIn("FAMILY_WORKFLOW.md",
                      overlay("unattended-issue-loop").read_text(encoding="utf-8"))


class NoSecondCopyIsLeftBehind(unittest.TestCase):
    def test_the_tracked_run_state_directory_is_gone(self):
        state = CLAUDE / "skills" / "implement-github-issue" / "state"
        self.assertFalse(state.exists(),
                         "%s still exists. The governing copy keeps state under "
                         "<git-common-dir>/claude-state/, so files here are stale" % state)

    def test_no_file_claims_this_repository_ships_a_second_copy(self):
        stale = re.compile(r"(?i)the one that ships to the (?:four )?child ports"
                           r"|byte-identical in both")
        found = [str(p.relative_to(REPO_ROOT)) for p in own_markdown()
                 if stale.search(p.read_text(encoding="utf-8"))]
        self.assertEqual([], found,
                         "a file still claims a shared copy of a governed skill lives here")

    def test_the_corpus_is_not_empty(self):
        """INV-265: the scans above pass trivially over nothing."""
        self.assertGreaterEqual(len(list(own_markdown())), 10)


if __name__ == "__main__":
    unittest.main()
