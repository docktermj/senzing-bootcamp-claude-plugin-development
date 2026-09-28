"""The two skills whose user-level copy governs say so, and the repository keeps only its overlay.

`implement-github-issue` and `unattended-issue-loop` each had a full `SKILL.md` here and another
under `~/.claude/skills/`. The user-level copy is the one that loads, and the two had drifted
into different procedures: the project loop described local-only implement-then-audit cycles
while the loop that ran merged nine PRs on 2026-09-28, and the project `implement-github-issue`
claimed a shared block the user-level copy no longer had. The tests here checked the copies that
did not run (#215).

So, for both skills:

* the project `SKILL.md` is a **pointer stub**: it names the governing copy and the overlay, and
  carries no procedure and no shared block;
* the project command file is the **repo overlay**: only this repository's obligations, plus one
  line naming the governing copy, which is told to read the overlay;
* the loop's merge policy is stated once, in the `docs/FAMILY_WORKFLOW.md` §2 row (INV-300);
* the old tracked run-state directory is gone. The governing copy keeps state under
  `<git-common-dir>/claude-state/`.

⚠️ **`~/.claude/skills/` is NOT checked in CI, and nothing here reads it.** A CI runner checks
out only the repository, so a test reading the governing copy would fail there and pass on one
machine (INV-308). The pinned `argument-hint` values below are the governing copies' values on
2026-09-28; if a governing copy changes its hint, this test cannot see it and the overlay has to
be updated by hand.

⚠️ **What this does NOT establish:** that the governing copy actually reads the overlay, or
that a run meets the overlay's obligations. It pins that the repository's text points the right
way and holds no second procedure.

Source issue: #215.

Stdlib only; every surface is read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE = REPO_ROOT / ".claude"
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"

#: The skills whose user-level copy governs, with the governing copy's `argument-hint`.
GOVERNED = {
    "implement-github-issue": '"<GitHub issue URL or number>"',
    "unattended-issue-loop": '"[--dry-run] [--no-merge]"',
}

#: The merge-policy clause. It must appear exactly once in the repository's own text.
MERGE_POLICY = re.compile(r"`--no-merge` leaves every PR open")


def stub(name):
    return CLAUDE / "skills" / name / "SKILL.md"


def overlay(name):
    return CLAUDE / "commands" / ("%s.md" % name)


def split_frontmatter(path):
    """Return (frontmatter dict, body) for a Markdown file with a leading `---` block."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert m, "%s has no frontmatter block" % path
    fields = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, m.group(2)


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


class TheStubsPointAtTheGoverningCopy(unittest.TestCase):
    def test_each_stub_exists(self):
        """INV-303: each command still names a skill that resolves to a `SKILL.md` here."""
        for name in GOVERNED:
            with self.subTest(skill=name):
                self.assertTrue(stub(name).is_file(), "%s is missing" % stub(name))

    def test_the_frontmatter_keeps_name_and_description_and_is_not_model_invocable(self):
        for name in GOVERNED:
            fields, _ = split_frontmatter(stub(name))
            with self.subTest(skill=name):
                self.assertEqual(name, fields.get("name"))
                self.assertTrue(fields.get("description"), "the stub has no description")
                self.assertEqual(
                    "true", fields.get("disable-model-invocation"),
                    "the stub is model-invocable, so the model can load the project text through "
                    "the Skill tool while a slash command loads the governing copy -- two "
                    "procedures depending on how it was invoked")

    def test_the_body_names_the_governing_copy_the_overlay_and_the_ci_limit(self):
        for name in GOVERNED:
            _, body = split_frontmatter(stub(name))
            flat = re.sub(r"\s+", " ", body)
            for needed in ("~/.claude/skills/%s/SKILL.md" % name,
                           ".claude/commands/%s.md" % name,
                           "not checked in CI"):
                with self.subTest(skill=name, needed=needed):
                    self.assertIn(needed, flat)

    def test_the_stub_carries_no_procedure_and_no_shared_block(self):
        for name in GOVERNED:
            _, body = split_frontmatter(stub(name))
            with self.subTest(skill=name):
                self.assertNotIn("SHARED-RULES", body,
                                 "the stub carries a shared-rules block; the user-level copy "
                                 "has none, so the block would claim a twin that does not exist")
                self.assertNotIn("```", body, "the stub carries a command block: procedure")
                headings = re.findall(r"^#{2,} ", body, re.M)
                self.assertEqual([], headings,
                                 "the stub has section headings, so it is growing a procedure "
                                 "again beside the governing copy")


class TheOverlaysAreRepoOnly(unittest.TestCase):
    def test_each_overlay_names_the_governing_copy(self):
        for name in GOVERNED:
            text = re.sub(r"\s+", " ", overlay(name).read_text(encoding="utf-8"))
            with self.subTest(skill=name):
                self.assertRegex(
                    text, r"governing copy is `~/\.claude/skills/%s/SKILL\.md`" % re.escape(name))

    def test_each_overlay_hint_matches_the_governing_copy(self):
        for name, hint in GOVERNED.items():
            fields, _ = split_frontmatter(overlay(name))
            with self.subTest(skill=name):
                self.assertEqual(hint, fields.get("argument-hint"))

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
        self.assertIn("implement-github-issue.md", text,
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

    def test_the_stub_and_the_overlay_link_to_the_row(self):
        for path in (stub("unattended-issue-loop"), overlay("unattended-issue-loop")):
            with self.subTest(path=path.name):
                self.assertIn("FAMILY_WORKFLOW.md", path.read_text(encoding="utf-8"))


class NoSecondCopyIsLeftBehind(unittest.TestCase):
    def test_the_tracked_run_state_directory_is_gone(self):
        state = stub("implement-github-issue").parent / "state"
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
