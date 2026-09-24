"""The dry-run skill warns about the host Markdown hook, and its claims stay true.

A maintainer running a `/dry-run` phase-3 walk inside their own environment hit a user-level
`PostToolUse` hook matching `Write|Edit` that rejected the guide's writes to
`docs/bootcamp_recap.md` for MD022/MD032 at every module close -- rules
`bootcamp-onboarding/ground-rules.md` defers to graduation on purpose.

⛔ **Nothing shipped is in conflict.** The plugin registers no `PostToolUse` hook, so no
Bootcamper can encounter this; it is host configuration. That is why #135 is a documentation
issue and why `plugins/` is untouched by it.

⚠️ **What makes this guard worth having is not the prose check.** Two of the page's claims are
statements ABOUT things in this repository, so they can be checked against those things:

* *"the plugin ships no `PostToolUse` hook"* -- checked against `hooks.json`. If the plugin
  ever gains one, the sentence becomes false and this fails, naming the page to update.
* *"top-level `docs/*.md`, non-recursively"* -- checked against the normalizer that defines
  that set. If its scope changes, the documented exclusion is wrong and this fails.

⛔ **A documentation guard that only asserts words are present cannot notice the world moving
under them.** Those two assertions are the whole reason this file exists; the presence checks
are scaffolding around them.

⚠️ **What this does NOT establish:** that excluding those paths actually silences any
particular host hook. Nothing here runs a hook, and the hook belongs to the maintainer's
environment rather than to this repository -- it is unobservable from inside the suite.

⛔ **One home (INV-300).** The statement lives in the dry-run skill and must not be restated
in `docs/development.md`; a rule with two homes disagrees with itself.

Stdlib only; files are read as text and `hooks.json` as JSON (INV-108).

Source issue: #135.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude" / "skills" / "dry-run" / "SKILL.md"
HOOKS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "hooks" / "hooks.json"
NORMALIZER = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
              / "normalize_docs_markdown.py")
DEVELOPMENT = REPO_ROOT / "docs" / "development.md"

#: The section the warning belongs in -- what a maintainer reads before a walk.
SECTION = "## Before you start"


def skill_text():
    return SKILL.read_text(encoding="utf-8")


def before_you_start():
    """The section body, from its heading to the next `## ` heading."""
    t = skill_text()
    start = t.find(SECTION)
    if start < 0:
        return ""
    rest = t[start + len(SECTION):]
    nxt = rest.find("\n## ")
    return rest if nxt < 0 else rest[:nxt]


def registered_hooks():
    data = json.loads(HOOKS.read_text(encoding="utf-8"))
    return set(data.get("hooks", data).keys())


class TheInputsAreReal(unittest.TestCase):
    """INV-265 -- every assertion below reads these."""

    def test_the_files_exist(self):
        for name, path in (("dry-run SKILL.md", SKILL), ("hooks.json", HOOKS),
                           ("normalize_docs_markdown.py", NORMALIZER)):
            with self.subTest(what=name):
                self.assertTrue(path.is_file(), "%s is missing at %s" % (name, path))

    def test_the_section_was_located(self):
        self.assertTrue(
            before_you_start().strip(),
            "%r was not found in %s, so every prose assertion below would pass over an "
            "empty string" % (SECTION, SKILL))

    def test_the_hooks_file_parses_to_something(self):
        self.assertTrue(
            registered_hooks(),
            "no hook events parsed from %s. An empty set would make the "
            "no-PostToolUse assertion below true for the wrong reason" % HOOKS)


class TheWarningIsWhereAMaintainerWillReadIt(unittest.TestCase):
    """The acceptance criteria of #135, as prose checks."""

    def test_the_conflict_is_named(self):
        body = before_you_start()
        for token in ("PostToolUse", "bootcamp_recap.md"):
            with self.subTest(token=token):
                self.assertIn(
                    token, body,
                    "%r does not mention %r. A maintainer preparing a walk is the reader "
                    "this warning exists for" % (SECTION, token))

    def test_it_names_the_exclusion_set(self):
        body = re.sub(r"\s+", " ", before_you_start())
        self.assertRegex(
            body, r"top-level `docs/\*\.md`",
            "the warning does not name the exclusion set. Saying a hook conflicts without "
            "saying what to exclude leaves the reader with a problem and no action")

    def test_it_points_at_the_normalizer_rather_than_a_file_list(self):
        body = re.sub(r"\s+", " ", before_you_start())
        self.assertIn(
            "normalize_docs_markdown.py", body,
            "the exclusion set is stated without naming the script that defines it. A "
            "hand-kept list drifts the moment the normalizer's scope changes, which is the "
            "failure this wording is shaped to avoid")

    def test_it_says_the_plugin_ships_no_such_hook(self):
        body = re.sub(r"\s+", " ", before_you_start())
        self.assertRegex(
            body, r"no\s+`?PostToolUse`?\s+hook",
            "the warning does not say the plugin ships no PostToolUse hook. Without that, it "
            "reads as a defect report against the product rather than as host configuration, "
            "and the obvious 'fix' is to change the plugin")


class TheDocumentedClaimsAreStillTrue(unittest.TestCase):
    """⛔ The half that can notice the world moving. Prose checks cannot."""

    def test_the_plugin_still_registers_no_post_tool_use_hook(self):
        self.assertNotIn(
            "PostToolUse", registered_hooks(),
            "the plugin now registers a PostToolUse hook, so the dry-run skill's claim that "
            "it ships none is FALSE. Update %s -- and reconsider #135's conclusion, which "
            "rests on no Bootcamper being able to encounter this" % SKILL)

    #: ⛔ Bound to the CALL, not to the characters. Two traps, both surfaced by this guard's
    #: own negative control:
    #:
    #: 1. `rglob("*.md")` CONTAINS `glob("*.md")`, so a substring test passes on the
    #:    recursive form -- the exact change this exists to catch.
    #: 2. The script's own docstring quotes ``Path.glob("*.md")``, so a pattern not bound to
    #:    `docs_dir` is satisfied by PROSE while the code does something else.
    NON_RECURSIVE_GLOB = re.compile(r"docs_dir\.glob\(\"\*\.md\"\)")

    def test_the_normalizer_still_globs_top_level_docs_non_recursively(self):
        source = NORMALIZER.read_text(encoding="utf-8")
        self.assertRegex(
            source, self.NON_RECURSIVE_GLOB,
            "%s no longer calls `docs_dir.glob(\"*.md\")`, so the documented "
            "exclusion set (top-level `docs/*.md`) may be wrong. The page derives its set "
            "from this script deliberately, so a change here is a change there" % NORMALIZER)
        self.assertNotRegex(
            source, r"docs_dir\.rglob",
            "%s now walks `docs/` recursively. The page states that `docs/feedback/` is out "
            "of scope STRUCTURALLY (INV-015) rather than by an exclusion someone maintains; "
            "recursion makes that false and the documented set wrong" % NORMALIZER)
        self.assertIn(
            "p.parent == docs_dir", source,
            "the normalizer no longer filters to the top level, so `docs/*.md` may now "
            "descend into `docs/feedback/`. The page says that directory is out of scope "
            "STRUCTURALLY (INV-015); if that stopped being true, the page is wrong")


class TheStatementHasOneHome(unittest.TestCase):
    """⛔ INV-300 -- a rule with two homes will disagree with itself."""

    def test_development_md_does_not_restate_it(self):
        body = re.sub(r"\s+", " ", DEVELOPMENT.read_text(encoding="utf-8"))
        self.assertNotIn(
            "PostToolUse", body,
            "docs/development.md now discusses the PostToolUse hook conflict, which the "
            "dry-run skill owns. Two copies drift, and the duplication scan reports EXACT "
            "repeats -- so two statements that have stopped matching are precisely what it "
            "cannot see. Point at the owner instead of restating it")


if __name__ == "__main__":
    unittest.main()
