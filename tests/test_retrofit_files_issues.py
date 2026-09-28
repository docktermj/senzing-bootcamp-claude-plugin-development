"""`/retrofit-from-public` files issues; it never writes into the development tree.

The command copied the public repo's propagated paths into the dev working tree and applied the
inverse slug rewrite in place. Under the issue-driven workflow (#54) its output is **GitHub
issues describing what diverged**, and the working tree is left alone.

⚠️ **The divergence is real, not hypothetical.** The public repo carries Dependabot bumps and a CI
workflow added directly there — edits that never passed through development.

⛔ **Not copying also removes a hazard the old procedure could only warn about.** `tests/` is not
in the public mirror and cannot come back, so a copied prose edit landed in a shipped file while
the dev-only test quoting that sentence kept asserting the old wording. Measured 2026-08-16 on
`2223961`, the British→US spelling corrections: a **correct** edit, faithfully retrofitted, left
**12 failed / 2730 passed** — ten of them that desync. Nothing is copied now, so nothing desyncs.

⚠️ **The inverse slug transform is still required and is now manual**, applied by whoever
implements a filed issue. A guard cannot check that it happened; the skill says so instead.

**Enforces INV-312** — a command bringing another repository's changes into this one writes
nothing into the working tree, reports what diverged, and files issues in its own repository only.
⛔ **What this test does NOT establish:** that a run refrains from copying. The public repository
is absent on some machines — it was absent when this was written — so the behavior cannot be
observed offline, and an `Enforced by` clause pointing here is not a compliance claim.

⛔ **The first four classes assert what the skill and script INSTRUCT, never what a run does.**
The public repository is not present on every machine — it was absent when this was written — so
no offline test can watch a run against it refrain from copying. Those classes read the script as
text.

⚠️ **`TheScriptReportsEveryPath` does run the script, against fixture repositories (#191).** The
script ran under `set -euo pipefail`, and its listing pipeline carried `diff`'s exit 1 whenever a
path differed, so the first differing path ended the run: the report only finished when there was
nothing to report. No text assertion could see that, because every line of the report was present
in the source; only running it shows where it stops. The fixtures are temporary git repos built
here, never the real public clone, and the class skips where `bash`, `git` or `diff` is missing.

Stdlib only; every file is read as text (INV-108), and the fixtures use `subprocess` and
`tempfile`.

Source issues: #54, #191.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude" / "skills" / "retrofit-from-public" / "SKILL.md"
SCRIPT = REPO_ROOT / ".claude" / "skills" / "retrofit-from-public" / "retrofit.sh"

#: Shell that writes into the destination tree. ⛔ Targets the ACT, not one command's name: the
#: script used `rsync -a` and a Python block opening files for writing, and a later editor
#: reaching for `cp -r` or `install` would be doing the same thing under another name.
WRITES_INTO_DEV = re.compile(
    r"\brsync\b(?![^\n]*--dry-run)|\bcp\s+-[a-zA-Z]*r|\binstall\s+-|"
    r"open\([^)]*[\"']w[\"']|\bfh\.write\(|>\s*\"\$here/",
    re.I)


def texts():
    return {"SKILL.md": SKILL.read_text(encoding="utf-8"),
            "retrofit.sh": SCRIPT.read_text(encoding="utf-8")}


def flat(s):
    return re.sub(r"\s+", " ", s).lower()


class BothFilesExist(unittest.TestCase):
    """INV-265 — every assertion below reads these, so they must be real."""

    def test_the_files_exist(self):
        for name, path in (("skill", SKILL), ("script", SCRIPT)):
            with self.subTest(what=name):
                self.assertTrue(path.is_file(), "%s is missing at %s" % (name, path))


class TheScriptWritesNothing(unittest.TestCase):
    def test_no_write_into_the_destination_survives(self):
        hit = WRITES_INTO_DEV.search(texts()["retrofit.sh"])
        self.assertIsNone(
            hit, "retrofit.sh still writes into the development tree (%r). The command's output "
                 "is issues now; a copy that lands in the working tree is the thing #54 retired "
                 "-- and it brings back the desync that left 12 tests failing on 2026-08-16"
                 % (hit.group(0) if hit else ""))

    def test_it_says_it_wrote_nothing(self):
        """⚠️ A reader must be able to tell a report from a sync without reading the source."""
        self.assertRegex(
            texts()["retrofit.sh"], r"NOTHING WAS WRITTEN",
            "the script does not say it wrote nothing. Its predecessor copied, so a run that "
            "looks similar and says neither leaves the maintainer unsure whether to review a "
            "diff or file an issue")


class TheSkillFilesIssuesInItsOwnRepo(unittest.TestCase):
    def test_it_files_issues(self):
        self.assertIn(
            "gh issue create", texts()["SKILL.md"],
            "the skill never names `gh issue create`, so the command has no stated way to "
            "produce the output #54 requires")

    def test_filing_is_gated_on_the_maintainer(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"get a yes|getting a yes",
            "filing is not gated on the maintainer. It is outward-facing and immediate -- an "
            "issue can be edited or closed afterwards but never un-filed -- which is why "
            "/feedback-to-issues and /production-readiness-audit gate it too")

    def test_duplicates_are_checked_against_the_tracker(self):
        """#54's second acceptance criterion: an absorbed change files nothing."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"gh issue list[^.]{0,80}search",
            "the skill does not search the tracker before filing, so a change already absorbed "
            "or already filed gets a second issue")

    def test_it_never_files_in_another_repository(self):
        """⛔ Cross-repo filing is owned by /escalate-to-parent alone."""
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"escalate-to-parent",
            "the skill does not say that cross-repo filing belongs to /escalate-to-parent. "
            "Children inherit this command, and one that files upward is a second escalation "
            "path nobody chose")


class TheReasonForNotCopyingSurvives(unittest.TestCase):
    """⛔ Cutting the narrative would make this look like a style change (INV-246's lesson)."""

    def test_the_desync_that_motivated_it_is_still_recorded(self):
        text = flat(texts()["SKILL.md"])
        self.assertIn(
            "2223961", text,
            "the worked example is gone. A retrofit that copied correct prose left 12 tests "
            "failing because `tests/` cannot come back from public; without that, a later "
            "editor reads 'do not copy' as caution rather than as a measured result")
        self.assertRegex(
            text, r"12 failed",
            "the measured outcome is gone from the skill; the number is what makes the rule "
            "hold up against 'surely copying is simpler'")

    def test_the_inverse_transform_is_still_required_manually(self):
        self.assertRegex(
            flat(texts()["SKILL.md"]), r"inverse (?:slug )?transform is still required",
            "the skill no longer says the inverse slug rewrite must still be applied by hand. "
            "The script stopped doing it; if nothing says so, dev ends up carrying public "
            "self-references")


# --- #191: the script runs to the end -------------------------------------------------------- #

#: The four propagated paths, in the order the script compares them.
PROPAGATED = ("plugins", ".claude-plugin", "docs", "README.md")
#: The listing line and the status capture the fix added. Each is a guard the negative
#: controls below remove, so each must appear exactly once for the mutation to be meaningful.
GUARDED_LISTING = """diff -rq "$src/$rel" "$here/$rel" 2>&1 | sed 's/^/      /' | head -40 || true"""
GUARDED_STATUS = """diff -rq "$src/$rel" "$here/$rel" >/dev/null 2>&1 || status=$?"""
#: The escape the old summary printed literally, built from parts so no tool turns it into the
#: character it names on the way into this file.
LITERAL_ESCAPE = chr(92) + "u26d4"
STOP_SIGN = "⛔"
#: Output that describes a sync, which the script has not performed since #54.
CLAIMS_A_WRITE = re.compile(
    r"applied to the working tree|commit manually|before committing|will overlay|"
    r"retrofit applied", re.I)
HAVE_TOOLS = all(shutil.which(tool) for tool in ("bash", "git", "diff"))


def _env(home):
    """The caller's environment with its git configuration shut out.

    ⚠️ A maintainer's global `commit.gpgsign` or `tag.gpgsign` would otherwise make every fixture
    commit ask for a signing key, and a global hook or `core.autocrlf` would change the fixture.
    """
    return dict(os.environ, HOME=str(home), GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def _git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.com",
         "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "-c", "core.autocrlf=false",
         *args],
        check=True, capture_output=True, env=_env(Path(repo).parent))


def _write(root, rel, text):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _script_text():
    """The script with LF line endings, so a CRLF checkout still runs under bash."""
    return SCRIPT.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


class Fixture:
    """A dev repo carrying a copy of the script, and a public repo whose origin passes the guard.

    The script finds the dev root from its own path (`$(dirname "${BASH_SOURCE[0]}")/../../..`),
    so the copy sits at the same depth as the real one.
    """

    def __init__(self, tmp, dev_files, public_files, public_origin=None, script=None):
        self.dev = Path(tmp) / "dev"
        self.public = Path(tmp) / "public"
        self.script = self.dev / ".claude" / "skills" / "retrofit-from-public" / "retrofit.sh"
        _write(self.dev, "plugins/senzing-bootcamp/.keep", "")
        for rel, text in dev_files.items():
            _write(self.dev, rel, text)
        _write(self.dev, self.script.relative_to(self.dev).as_posix(),
               script if script is not None else _script_text())
        _git(self.dev, "init", "-q")
        _git(self.dev, "add", "-A")
        _git(self.dev, "commit", "-q", "-m", "dev")
        self.public.mkdir(parents=True)
        _write(self.public, "plugins/senzing-bootcamp/.keep", "")
        for rel, text in public_files.items():
            _write(self.public, rel, text)
        _git(self.public, "init", "-q")
        _git(self.public, "remote", "add", "origin", public_origin
             or "https://github.com/Senzing/senzing-bootcamp-claude-plugin.git")
        _git(self.public, "add", "-A")
        _git(self.public, "commit", "-q", "-m", "release")
        _git(self.public, "tag", "v1.0.0")
        # A commit after the tag, in a governance path the script never reads, so it shows in
        # the commit list without changing what the comparison sees.
        _write(self.public, ".github/workflows/ci.yml", "on: push\n")
        _git(self.public, "add", "-A")
        _git(self.public, "commit", "-q", "-m", "fix: a public-side edit after the tag")

    def run(self):
        done = subprocess.run(
            ["bash", self.script.as_posix(), self.public.as_posix()],
            capture_output=True, cwd=str(self.dev), env=_env(self.dev.parent))
        self.stdout = done.stdout.decode("utf-8", "replace")
        self.stderr = done.stderr.decode("utf-8", "replace")
        self.returncode = done.returncode
        return self

    def dev_status(self):
        return subprocess.run(["git", "-C", str(self.dev), "status", "--porcelain"],
                              check=True, capture_output=True,
                              env=_env(self.dev.parent)).stdout.decode("utf-8", "replace")


def _differing_pair():
    """Dev and public trees that differ in plugins/ (60 files, past the 40-line cut) and docs/.

    README.md differs too; .claude-plugin/ is absent in public; one dev file under plugins/ has
    no public counterpart.
    """
    dev, public = {}, {}
    for i in range(60):
        rel = "plugins/senzing-bootcamp/skills/s%02d.md" % i
        dev[rel], public[rel] = "dev %d\n" % i, "public %d\n" % i
    dev["plugins/senzing-bootcamp/dev-only.md"] = "not propagated yet\n"
    dev["docs/guide.md"], public["docs/guide.md"] = "dev guide\n", "public guide\n"
    dev[".claude-plugin/marketplace.json"] = "{}\n"
    dev["README.md"], public["README.md"] = "dev readme\n", "public readme\n"
    return dev, public


def _identical_pair():
    files = {"plugins/senzing-bootcamp/a.md": "same\n", ".claude-plugin/marketplace.json": "{}\n",
             "docs/guide.md": "same\n", "README.md": "same\n"}
    return dict(files), dict(files)


def _differs_only(fx):
    return [line for line in fx.stdout.splitlines() if line.startswith("  DIFFERS")]


def _listing_after(fx, rel):
    """The indented listing lines printed under `rel`'s status line."""
    lines = fx.stdout.splitlines()
    start = next(i for i, line in enumerate(lines) if line.split()[-1:] == [rel]
                 and line.startswith("  DIFFERS"))
    listing = []
    for line in lines[start + 1:]:
        if not line.startswith("      "):
            break
        listing.append(line)
    return listing


@unittest.skipUnless(HAVE_TOOLS, "bash, git and diff are needed to run retrofit.sh")
class TheScriptReportsEveryPath(unittest.TestCase):
    """#191: a differing path, or one `diff` cannot compare, never ends the report early."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.fx = Fixture(os.path.join(cls._tmp.name, "differ"), *_differing_pair()).run()

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _tmpdir(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return tmp.name

    def test_a_differing_tree_is_reported_to_the_end_and_exits_zero(self):
        fx = self.fx
        self.assertEqual(
            fx.returncode, 0,
            "retrofit.sh exited %d on a tree that merely differs; a difference is the report, not "
            "a failure (#191).\nstdout:\n%s\nstderr:\n%s" % (fx.returncode, fx.stdout, fx.stderr))
        self.assertEqual(
            [line.split()[-1] for line in _differs_only(fx)], ["plugins", "docs", "README.md"],
            "every differing propagated path must be reported, not only the first:\n" + fx.stdout)
        self.assertIn("(absent in public)      .claude-plugin", fx.stdout)
        for heading in ("=== Public commits since the newest tag",
                        "=== In dev but not in public"):
            with self.subTest(section=heading):
                self.assertIn(heading, fx.stdout, "a section never printed:\n" + fx.stdout)
        self.assertIn("fix: a public-side edit after the tag", fx.stdout,
                      "the commit list is missing the public commit after the tag")
        self.assertIn("  plugins/senzing-bootcamp/dev-only.md", fx.stdout,
                      "the in-dev-not-in-public list is missing the unpropagated dev file")
        self.assertRegex(fx.stdout, r"3 propagated path\(s\) differ\. .* NOTHING WAS WRITTEN\.")

    def test_the_summary_shows_the_stop_sign(self):
        summary = next((line for line in self.fx.stdout.splitlines()
                        if "NOTHING WAS WRITTEN" in line), None)
        self.assertIsNotNone(summary, "the run never printed its summary:\n" + self.fx.stdout)
        self.assertIn(STOP_SIGN, summary, "the summary line lost its stop sign: %r" % summary)
        self.assertNotIn(LITERAL_ESCAPE, self.fx.stdout,
                         "the summary printed the escape sequence instead of the stop sign")

    def test_a_long_listing_is_cut_at_forty_lines_and_the_run_goes_on(self):
        self.assertEqual(len(_listing_after(self.fx, "plugins")), 40,
                         "plugins/ has 61 differing entries; its listing must stop at 40")
        self.assertIn("  DIFFERS                 docs", self.fx.stdout,
                      "the path after the truncated listing was never compared")

    def test_no_line_claims_a_write_or_a_commit(self):
        hit = CLAIMS_A_WRITE.search(self.fx.stdout + self.fx.stderr)
        self.assertIsNone(hit, "the output still describes a sync (%r); the script has written "
                               "nothing since #54" % (hit.group(0) if hit else ""))

    def test_the_run_leaves_the_dev_tree_untouched(self):
        self.assertEqual(self.fx.dev_status(), "", "the run changed the fixture dev tree (INV-312)")

    def test_a_path_diff_cannot_compare_is_an_error_and_the_run_goes_on(self):
        """docs/ is a file in public and a directory in dev, so `diff` exits 2."""
        dev, public = _differing_pair()
        public["docs"] = public.pop("docs/guide.md")
        fx = Fixture(self._tmpdir(), dev, public).run()
        self.assertNotEqual(fx.returncode, 0,
                            "a comparison that could not run must make the script fail")
        self.assertRegex(fx.stdout, r"(?m)^  ERROR +docs\b",
                         "the uncomparable path is not reported as ERROR:\n" + fx.stdout)
        self.assertIn("  DIFFERS                 README.md", fx.stdout,
                      "the path after the ERROR was never compared")
        for text in ("=== Public commits since the newest tag", "=== In dev but not in public",
                     "NOTHING WAS WRITTEN", "could not be compared"):
            with self.subTest(text=text):
                self.assertIn(text, fx.stdout, "the run stopped at the ERROR:\n" + fx.stdout)

    def test_identical_trees_report_same_and_exit_zero(self):
        fx = Fixture(self._tmpdir(), *_identical_pair()).run()
        self.assertEqual(fx.returncode, 0, fx.stdout + fx.stderr)
        for rel in PROPAGATED:
            with self.subTest(path=rel):
                self.assertIn("  same                    " + rel, fx.stdout)
        self.assertIn("0 propagated path(s) differ.", fx.stdout)

    def test_the_origin_guard_still_aborts_before_comparing(self):
        fx = Fixture(self._tmpdir(), *_identical_pair(),
                     public_origin="https://github.com/someone/else.git").run()
        self.assertNotEqual(fx.returncode, 0)
        self.assertIn("Refusing: source", fx.stderr)
        self.assertNotIn("=== Comparing", fx.stdout)

    def test_negative_control_the_unguarded_pipeline_stops_the_report(self):
        """Removing either guard must make the run stop at the first differing path."""
        text = _script_text()
        for guard, unguarded in ((GUARDED_LISTING, GUARDED_LISTING[:-len(" || true")]),
                                 (GUARDED_STATUS, GUARDED_STATUS[:-len(" || status=$?")])):
            with self.subTest(guard=guard):
                self.assertEqual(text.count(guard), 1, "retrofit.sh no longer carries %r" % guard)
                fx = Fixture(self._tmpdir(), *_differing_pair(),
                             script=text.replace(guard, unguarded)).run()
                self.assertNotEqual(fx.returncode, 0)
                self.assertNotIn("NOTHING WAS WRITTEN", fx.stdout,
                                 "the fixture no longer exercises the early exit #191 fixed")


if __name__ == "__main__":
    unittest.main()
