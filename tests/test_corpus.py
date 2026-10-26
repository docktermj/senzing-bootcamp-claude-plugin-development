"""The shared corpus listing, `tests/_corpus.py`, keeps loop scratch and Claude Code's runtime out.

#515: the suite went red in the main checkout whenever untracked scratch sat under
`.claude/worktrees/`, because each guard walked the filesystem itself and only some of them
skipped that directory. Every guard that walks the repository from its root or from `.claude/`
now takes its files from `corpus_files()`. Two guards hold that in place:

- **The canary guard** builds a temporary git repository, plants a canary file under
  `.claude/worktrees/` and under every other directory in `RUNTIME_DIRS` (one of them even
  staged, so git itself reports it), and asserts the listing returns none of them while it still
  returns a tracked file and an untracked, non-ignored one. It runs the git route and the
  fallback walk, and pins the edge cases #515 names: a tracked file deleted from the working
  tree, an ignored file, and a name with spaces and non-ASCII characters. The fallback also
  prunes `/release-cycle`'s run scratch, `.claude/release-cycle/runs/`, by its root path (#610),
  and keeps a directory named `runs` anywhere else.
- **The hand-rolled walk guard** scans `tests/*.py` (except `_corpus.py` and this file) for a
  walk rooted at the repository root or anywhere under `.claude/`, and fails on a match. Its
  known forms are `REPO_ROOT.rglob`, `REPO_ROOT.glob("**…`, `CLAUDE.rglob`, `os.walk(REPO_ROOT`,
  `os.walk(CLAUDE` and, since #796, any `rglob`, `glob("**…")` or `os.walk` on a path under
  `.claude/` written in place (`(REPO_ROOT / ".claude" / "skills").rglob`) or through a name bound
  to one: a simple assignment, a `for` target, a parameter default or a test helper's name
  (`surface.SKILLS_DIR`), resolved to a fixed point. #796 found three tests walking a `.claude/`
  subdirectory that way, and moved them to `corpus_files()`.

⚠️ **The limit of the second guard, stated because a clean run does not mean what it looks
like:** it is a text scan. A walk through a name it cannot resolve (one built by a function call,
an attribute of an object, a name bound by unpacking), a recursive `iterdir`, or a call head split
across lines is not caught. The canary guard, which proves the helper excludes what it must, and
review cover that gap.

This module enforces INV-367 (registered 2026-10-13). Its walk guard is a text scan for the known
walk forms: it cannot see a walk through a name it cannot resolve or a recursive `iterdir`.

Stdlib only (INV-108).

Source issue: #515.

Run:  python3 -m unittest discover -s tests
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _corpus
from _corpus import RUNTIME_DIRS, corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS = REPO_ROOT / "tests"

#: A string literal naming `.claude/` or any path under it.
CLAUDE_PATH = r"""[rbuf]*["']\.claude(?:/[^"'\n]*)?["']"""
#: The call that makes a walk: ``.rglob(`` or a ``.glob("**…")``.
WALK_CALL = r"""(?:\.rglob\(|\.glob\(\s*[rbuf]*["']\*\*)"""

#: The walk forms #515 names, each rooted at the repository root or `.claude/`, widened by #796 to
#: a walk of any path under `.claude/` written in place: ``(REPO_ROOT / ".claude" / "skills")``,
#: ``(CLAUDE / "skills")`` and ``os.walk(REPO_ROOT / ".claude" / …)``. A walk through a NAME bound
#: to such a path is found by ``hand_rolled_walks``, which resolves the names first.
HAND_ROLLED_WALK = re.compile(
    r"\bREPO_ROOT" + WALK_CALL
    + r"|\bCLAUDE" + WALK_CALL
    + r"|\(\s*(?:CLAUDE\b|[^()\n]*" + CLAUDE_PATH + r")[^()\n]*\)" + WALK_CALL
    + r"|\bos\.walk\(\s*(?:str\(\s*)?\(?\s*(?:(?:REPO_ROOT|CLAUDE)\b|[^()\n]*" + CLAUDE_PATH
    + r")")

#: A simple binding: ``NAME = <expression>`` (an annotation allowed), ``for NAME in <expression>``,
#: and a parameter default ``name=<expression>`` inside a ``def`` signature.
ASSIGN = re.compile(r"^[ \t]*([A-Za-z_]\w*)[ \t]*(?::[^=\n]+)?=(?!=)[ \t]*(.+)$", re.M)
FOR = re.compile(r"^[ \t]*for[ \t]+([A-Za-z_]\w*)[ \t]+in[ \t]+(.+?):?[ \t]*$", re.M)
SIGNATURE = re.compile(r"\bdef\s+\w+\s*\(([^)]*)\)")
PARAMETER = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*([^,]+)")
#: A test helper imported by module name (``import _maintainer_surface as surface``).
HELPER_IMPORT = re.compile(r"^[ \t]*import[ \t]+(_\w+)(?:[ \t]+as[ \t]+(\w+))?", re.M)


def _bindings(text):
    found = ASSIGN.findall(text) + FOR.findall(text)
    for signature in SIGNATURE.findall(text):
        found += PARAMETER.findall(signature)
    return found


def claude_names(text, helpers=None, seen=()):
    """Names in ``text`` bound to a path under `.claude/`, resolved to a fixed point (#796).

    A name is one when its binding names a `.claude` literal, ``CLAUDE``, or another such name,
    including a helper module's (``surface.SKILLS_DIR``, where ``_maintainer_surface`` binds it).
    """
    helpers = TESTS if helpers is None else Path(helpers)
    names = set()
    for module, alias in HELPER_IMPORT.findall(text):
        helper = helpers / (module + ".py")
        if module not in seen and helper.is_file():
            names |= {"%s.%s" % (alias or module, n) for n in claude_names(
                helper.read_text(encoding="utf-8"), helpers, seen + (module,)) if "." not in n}
    bindings = _bindings(text)
    changed = True
    while changed:
        changed = False
        for name, value in bindings:
            if name in names:
                continue
            if (re.search(CLAUDE_PATH, value) or re.search(r"\bCLAUDE\b", value)
                    or any(re.search(r"(?<![\w.])%s\b" % re.escape(n), value) for n in names)):
                names.add(name)
                changed = True
    return {n for n in names if "." not in n}


def hand_rolled_walks(text, helpers=None):
    """``[(line, text)]`` for each walk of the root or of a path under `.claude/` in ``text``.

    Line-scoped: each walk form is the head of one call. ``HAND_ROLLED_WALK`` reads the forms
    written in place; a walk through a name ``claude_names`` resolves is read here as well.
    """
    patterns = [HAND_ROLLED_WALK.pattern]
    names = sorted(claude_names(text, helpers))
    if names:
        alternation = "|".join(re.escape(n) for n in names)
        patterns += [r"(?<![\w.])(?:%s)" % alternation + WALK_CALL,
                     r"\(\s*(?:%s)\b[^()\n]*\)" % alternation + WALK_CALL,
                     r"\bos\.walk\(\s*(?:str\(\s*)?\(?\s*(?:%s)\b" % alternation]
    walk = re.compile("|".join("(?:%s)" % p for p in patterns))
    return [(n, line.strip()) for n, line in enumerate(text.splitlines(), 1) if walk.search(line)]

#: Files the walk guard does not scan: the helper itself, and this file's fixtures.
NOT_SCANNED = {"_corpus.py", Path(__file__).name}

GIT = shutil.which("git")


def git(repo, *args):
    done = subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError("git %s failed in fixture: %s" % (" ".join(args), done.stderr))
    return done.stdout


def write(path, text="canary\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def rel(paths, root):
    return {p.relative_to(root).as_posix() for p in paths}


class Fixture:
    """A repository tree with a canary under every runtime directory."""

    TRACKED = "docs/tracked.md"
    UNTRACKED = "docs/just-written.md"
    ODD_NAME = "docs/an \"odd\" näme.md"
    DELETED = "docs/deleted.md"
    IGNORED = "build/ignored.md"
    CANARIES = ["/".join(runtime) + "/canary.md" for runtime in RUNTIME_DIRS]
    #: The same runtime directories one level down, as `**/.claude/worktrees/` matches them.
    NESTED_CANARIES = ["plugins/x/" + "/".join(runtime) + "/canary.md" for runtime in RUNTIME_DIRS]

    @classmethod
    def build(cls, root, with_git):
        for name in (cls.TRACKED, cls.UNTRACKED, cls.ODD_NAME, cls.DELETED, cls.IGNORED,
                     *cls.CANARIES, *cls.NESTED_CANARIES):
            write(root / name)
        write(root / ".gitignore", "/build/\n")
        if with_git:
            git(root, "init", "--quiet")
            git(root, "add", cls.TRACKED, cls.DELETED, ".gitignore")
            # Staged on purpose: git now REPORTS this canary, so only the prune can drop it.
            git(root, "add", "-f", cls.CANARIES[0])
            (root / cls.DELETED).unlink()
        else:
            (root / cls.DELETED).unlink()


@unittest.skipUnless(GIT, "git is not installed; the fallback-walk canary still runs")
class TheGitListingKeepsTheCanariesOut(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        Fixture.build(self.root, with_git=True)
        self.found = rel(corpus_files(root=self.root), self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_fixture_really_is_a_work_tree(self):
        """Negative control: the git route answered, so the fallback is not what passed."""
        self.assertIsNotNone(_corpus._git_listing(self.root))

    def test_no_runtime_canary_is_returned(self):
        for name in Fixture.CANARIES + Fixture.NESTED_CANARIES:
            with self.subTest(canary=name):
                self.assertTrue((self.root / name).is_file(), "the canary was never planted")
                self.assertNotIn(name, self.found)

    def test_a_staged_canary_is_pruned_whatever_git_reports(self):
        reported = _corpus._git_listing(self.root)
        self.assertIn(Fixture.CANARIES[0], reported, "the fixture no longer stages the canary")
        self.assertNotIn(Fixture.CANARIES[0], self.found)

    def test_a_tracked_file_is_returned(self):
        self.assertIn(Fixture.TRACKED, self.found)

    def test_an_untracked_non_ignored_file_is_returned(self):
        self.assertIn(Fixture.UNTRACKED, self.found)

    def test_a_name_with_quotes_spaces_and_non_ascii_is_returned_verbatim(self):
        self.assertIn(Fixture.ODD_NAME, self.found)

    def test_a_tracked_file_deleted_from_the_working_tree_is_dropped(self):
        self.assertNotIn(Fixture.DELETED, self.found)

    def test_an_ignored_file_is_not_returned(self):
        self.assertNotIn(Fixture.IGNORED, self.found)

    def test_subtree_and_suffix_filters_narrow_the_listing(self):
        got = rel(corpus_files("docs", root=self.root, suffixes={".md"}), self.root)
        self.assertEqual({Fixture.TRACKED, Fixture.UNTRACKED, Fixture.ODD_NAME}, got)
        self.assertEqual(set(), rel(corpus_files(".claude", root=self.root), self.root))


#: `/release-cycle`'s run scratch, `.gitignore`d at the root (#572); the fallback prunes it (#610).
RUN_SCRATCH = ".claude/release-cycle/runs/2026-10-14/state.json"
#: A directory named `runs` elsewhere, and the same path one level down: both are corpus.
OTHER_RUNS = "docs/runs/x.md"
NESTED_RUN_PATH = "plugins/x/.claude/release-cycle/runs/x.md"


class TheFallbackWalkKeepsTheCanariesOut(unittest.TestCase):
    """git missing, or exiting non-zero: the listing falls back to a pruned walk and never fails."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        Fixture.build(self.root, with_git=False)
        write(self.root / ".git" / "config")
        write(self.root / "tests" / "__pycache__" / "x.md")
        write(self.root / ".pytest_cache" / "x.md")
        write(self.root / ".history" / "x.md")
        write(self.root / RUN_SCRATCH)
        write(self.root / OTHER_RUNS)
        write(self.root / NESTED_RUN_PATH)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, found):
        found = rel(found, self.root)
        self.assertIn(Fixture.TRACKED, found)
        self.assertIn(Fixture.UNTRACKED, found)
        self.assertIn(Fixture.ODD_NAME, found)
        self.assertNotIn(Fixture.DELETED, found)
        for name in Fixture.CANARIES + Fixture.NESTED_CANARIES:
            self.assertNotIn(name, found)
        for name in (".git/config", "tests/__pycache__/x.md", ".pytest_cache/x.md",
                     ".history/x.md", RUN_SCRATCH):
            self.assertNotIn(name, found)
        # #610: pruned by path, not by name, so `runs` elsewhere is still the repository's.
        self.assertIn(OTHER_RUNS, found)
        self.assertIn(NESTED_RUN_PATH, found)

    def test_git_not_found(self):
        with mock.patch.object(_corpus.subprocess, "run", side_effect=FileNotFoundError("git")):
            self.check(corpus_files(root=self.root))

    def test_git_exits_non_zero(self):
        failed = subprocess.CompletedProcess(["git"], 128, b"", b"fatal: not a git repository")
        with mock.patch.object(_corpus.subprocess, "run", return_value=failed):
            self.check(corpus_files(root=self.root))

    def test_the_run_scratch_is_pruned_by_path_not_by_name(self):
        """Negative control: with the path entry gone, the walk reads the run scratch again."""
        self.assertIn((".claude", "release-cycle", "runs"), _corpus.FALLBACK_PRUNED_PATHS)
        self.assertNotIn("runs", _corpus.FALLBACK_PRUNED)
        with mock.patch.object(_corpus, "FALLBACK_PRUNED_PATHS", ()):
            self.assertIn(RUN_SCRATCH, _corpus._walk_listing(self.root))
        self.assertNotIn(RUN_SCRATCH, _corpus._walk_listing(self.root))


class ThisRepositorysListing(unittest.TestCase):

    def test_it_holds_this_file_and_no_runtime_path(self):
        found = corpus_files()
        self.assertIn(Path(__file__).resolve(), found)
        offenders = [p for p in found if _corpus.is_runtime(p.relative_to(REPO_ROOT).parts)]
        self.assertEqual([], offenders)


class NoTestWalksTheRootByHand(unittest.TestCase):

    def test_every_known_walk_form_is_matched(self):
        """Positive control: each form #515 names trips the pattern."""
        for line in ('REPO_ROOT.rglob("*.csv")',
                     'REPO_ROOT.glob("**/*.md")',
                     '(REPO_ROOT / ".claude").rglob("*.md")',
                     'CLAUDE.rglob("*")',
                     'os.walk(REPO_ROOT)',
                     'os.walk(CLAUDE)'):
            with self.subTest(line=line):
                self.assertRegex(line, HAND_ROLLED_WALK)

    def test_a_walk_of_an_out_of_scope_subtree_is_not_matched(self):
        for line in ('(REPO_ROOT / "docs").rglob("*.md")',
                     'PLUGIN.rglob("*.md")',
                     'SPECS.rglob("*")',
                     'REPO_ROOT.glob("*.md")',
                     '(REPO_ROOT / "plugins" / ".claude-plugin").rglob("*")',
                     'corpus_files(".claude/skills", suffixes={".md"})'):
            with self.subTest(line=line):
                self.assertNotRegex(line, HAND_ROLLED_WALK)

    def test_a_walk_of_a_claude_subdirectory_is_matched(self):
        """#796: INV-367 binds a walk rooted anywhere under `.claude/`, written in place."""
        for line in ('(REPO_ROOT / ".claude" / "skills").rglob("*.md")',
                     "(REPO_ROOT / '.claude/skills/dry-run').glob('**/*.py')",
                     '(CLAUDE / "skill-overlays").rglob("*.md")',
                     'os.walk(REPO_ROOT / ".claude" / "commands")',
                     'os.walk(str(REPO_ROOT / ".claude/skills"))'):
            with self.subTest(line=line):
                self.assertRegex(line, HAND_ROLLED_WALK)

    def test_a_walk_through_a_name_bound_under_claude_is_found(self):
        """#796: the three tests #796 moved walked a `.claude/` subdirectory through a name."""
        fixture = ('REPO_ROOT = Path(__file__).resolve().parent.parent\n'
                   'SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "compact-dev-environment"\n'
                   'OVERLAYS = REPO_ROOT / ".claude" / "skill-overlays"\n'
                   'DOCS = REPO_ROOT / "docs"\n'
                   'def skill_files():\n'
                   '    return sorted(SKILL_DIR.rglob("*"))\n'
                   'def corpus(overlays_dir=OVERLAYS):\n'
                   '    return sorted(overlays_dir.rglob("*.md"))\n'
                   'def trees():\n'
                   '    for tree in (SKILL_DIR, OVERLAYS):\n'
                   '        yield from tree.glob("**/*.md")\n'
                   'def docs():\n'
                   '    return sorted(DOCS.rglob("*.md"))\n')
        self.assertEqual([6, 8, 11], [n for n, _ in hand_rolled_walks(fixture)])
        for line in fixture.splitlines():
            self.assertNotRegex(line, HAND_ROLLED_WALK, "the pattern alone saw it: no widening")

    def test_a_name_bound_in_a_helper_module_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "_helper.py", 'SKILLS_DIR = REPO_ROOT / ".claude" / "skills"\n')
            fixture = ("import _helper as helper\nSKILLS_DIR = helper.SKILLS_DIR\n"
                       'found = SKILLS_DIR.rglob("*.md")\n')
            self.assertEqual([3], [n for n, _ in hand_rolled_walks(fixture, tmp)])

    def test_no_test_hand_rolls_a_root_or_claude_walk(self):
        """Line-scoped by design (#515): each walk form is the head of one Python call
        (`REPO_ROOT.rglob(`), which is one token run on one line, and the scan reports the
        `file:line` to fix. A call head split across lines is among the limits the module
        docstring states."""
        scanned = [p for p in sorted(TESTS.glob("*.py")) if p.name not in NOT_SCANNED]
        self.assertGreater(len(scanned), 100, "the scan found almost no test files")
        offenders = []
        for path in scanned:
            text = path.read_text(encoding="utf-8")
            for n, line in hand_rolled_walks(text):
                offenders.append("tests/%s:%d: %s" % (path.name, n, line))
        self.assertEqual(
            [], offenders,
            "walk the repository root or `.claude/` through `tests/_corpus.py`'s "
            "`corpus_files()`, so loop scratch and Claude Code's runtime directories stay out")


if __name__ == "__main__":
    unittest.main()
