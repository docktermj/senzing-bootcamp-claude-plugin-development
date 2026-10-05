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
here, never the real public clone, and the class skips where `bash`, `git`, `diff`, `tar`,
`rsync` or `python3` is missing (the last three because every run now builds a baseline).

⚠️ **`TheReportIsTakenAgainstTheLastPropagation` runs it too (#202).** The script compared public
against dev's CURRENT tree, so every dev change since the last propagation, and every file carrying
the dev slug, read as a public edit. It now compares against a baseline: the dev tag named like
public's newest tag (or `--base`), run through that tag's own `propagate.sh`. The fixture's dev
repo carries the real `propagate.sh`, so the forward rewrite and the `docs/` exclusions under test
are the shipped ones, not a copy. Its negative controls point the comparison back at dev's tree
and show the tests fail.

⚠️ **The command and the skill described the retired copy for a second time until #224.** #54
changed what the command does and left "add/update", "run the copy" and "reconcile every test" in
the prose around it. `NoCopyWordingReturns` fails if any of those phrases comes back.
`TheBuildArtifactsAreNotDifferences` runs the script against a public tree carrying
`__pycache__/`, `*.pyc` and `.pytest_cache/`, which the baseline never holds because
`propagate.sh` excludes them.

⚠️ **Dated note, 2026-09-30 (#262): the command-side assertions are dropped.** Until #262
`NoCopyWordingReturns` read the `retrofit-from-public` command file as well as the skill.
`/<name>` runs the skill (measured 2026-09-29, Claude Code 2.1.284, #241), so the command never
ran; #262 deleted it. The check and its negative control now read the skill alone.

Stdlib only; every file is read as text (INV-108), and the fixtures use `subprocess` and
`tempfile`.

Source issues: #54, #191, #202, #224.

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
PROPAGATE_REL = ".claude/skills/propagate-to-public/propagate.sh"
PROPAGATE = REPO_ROOT / PROPAGATE_REL

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
#: Both carry the build-artifact exclusions (#224); `IGNORED` names them once for both.
IGNORED = "-x __pycache__ -x '*.pyc' -x .pytest_cache "
GUARDED_LISTING = """diff -rq %s"$src/$rel" "$base/$rel" 2>&1 | sed 's/^/      /' | head -40 || true""" % IGNORED
GUARDED_STATUS = """diff -rq %s"$src/$rel" "$base/$rel" >/dev/null 2>&1 || status=$?""" % IGNORED
#: The escape the old summary printed literally, built from parts so no tool turns it into the
#: character it names on the way into this file.
LITERAL_ESCAPE = chr(92) + "u26d4"
STOP_SIGN = "⛔"
#: Output that describes a sync, which the script has not performed since #54.
CLAIMS_A_WRITE = re.compile(
    r"applied to the working tree|commit manually|before committing|will overlay|"
    r"retrofit applied", re.I)
HAVE_TOOLS = all(shutil.which(tool) for tool in ("bash", "git", "diff", "tar", "rsync", "python3"))
#: The section #202 retitled: files the baseline holds that public lacks.
MISSING_HEADING = "=== In the last propagation but not in public"
DEV_SLUG = "docktermj/senzing-bootcamp-claude-plugin-development"
PUBLIC_SLUG = "Senzing/senzing-bootcamp-claude-plugin"


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


def _propagate_text():
    """The shipped propagate.sh, LF-only, so the fixture's baseline is built by the real one."""
    return PROPAGATE.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


class Fixture:
    """A dev repo carrying a copy of the script, and a public repo whose origin passes the guard.

    The script finds the dev root from its own path (`$(dirname "${BASH_SOURCE[0]}")/../../..`),
    so the copy sits at the same depth as the real one. The dev repo also carries the shipped
    `propagate.sh` and is tagged `public_tag`, so by default the baseline (#202) is exactly
    `dev_files` as propagate publishes them.

    * `dev_after` -- files committed in dev AFTER the tag (a None value deletes the file).
    * `dev_dirty` -- files left uncommitted in the dev working tree.
    * `dev_tags` -- ordered (tag, {files}) pairs: each commits its files, then tags. Replaces the
      single `public_tag` tag on dev when given.
    * `public_tag` -- the tag public carries; None leaves public untagged.
    * `propagate` -- the propagate.sh text the tag carries; None leaves it out of the tag.
    """

    def __init__(self, tmp, dev_files, public_files, public_origin=None, script=None,
                 dev_after=None, dev_dirty=None, dev_tags=None, public_tag="v1.0.0",
                 propagate=True):
        self.dev = Path(tmp) / "dev"
        self.public = Path(tmp) / "public"
        self.tmpdir = Path(tmp) / "tmpdir"
        self.tmpdir.mkdir(parents=True)
        self.script = self.dev / ".claude" / "skills" / "retrofit-from-public" / "retrofit.sh"
        _write(self.dev, "plugins/senzing-bootcamp/.keep", "")
        for rel, text in dev_files.items():
            _write(self.dev, rel, text)
        if propagate is not None:
            _write(self.dev, PROPAGATE_REL, _propagate_text() if propagate is True else propagate)
        _write(self.dev, self.script.relative_to(self.dev).as_posix(),
               script if script is not None else _script_text())
        _git(self.dev, "init", "-q")
        _git(self.dev, "add", "-A")
        _git(self.dev, "commit", "-q", "-m", "dev")
        for tag, files in (dev_tags if dev_tags is not None else [(public_tag or "v1.0.0", {})]):
            self._commit(files, "dev for " + tag)
            _git(self.dev, "tag", tag)
        self._commit(dev_after or {}, "dev work after the tag")
        for rel, text in (dev_dirty or {}).items():
            _write(self.dev, rel, text)
        self.public.mkdir(parents=True)
        _write(self.public, "plugins/senzing-bootcamp/.keep", "")
        for rel, text in public_files.items():
            _write(self.public, rel, text)
        _git(self.public, "init", "-q")
        _git(self.public, "remote", "add", "origin", public_origin
             or "https://github.com/Senzing/senzing-bootcamp-claude-plugin.git")
        _git(self.public, "add", "-A")
        _git(self.public, "commit", "-q", "-m", "release")
        if public_tag is not None:
            _git(self.public, "tag", public_tag)
        # A commit after the tag, in a governance path the script never reads, so it shows in
        # the commit list without changing what the comparison sees.
        _write(self.public, ".github/workflows/ci.yml", "on: push\n")
        _git(self.public, "add", "-A")
        _git(self.public, "commit", "-q", "-m", "fix: a public-side edit after the tag")

    def _commit(self, files, message):
        if not files:
            return
        for rel, text in files.items():
            if text is None:
                (self.dev / rel).unlink()
            else:
                _write(self.dev, rel, text)
        _git(self.dev, "add", "-A")
        _git(self.dev, "commit", "-q", "-m", message)

    def run(self, *args):
        """Run the script; `args` go before the public path (e.g. `"--base", "v1.0.0"`).

        TMPDIR points at a directory of the fixture's own, so a test can see whether the run's
        temporary baseline was removed.
        """
        self.status_before = self.dev_status()
        env = _env(self.dev.parent)
        env["TMPDIR"] = str(self.tmpdir)
        done = subprocess.run(
            ["bash", self.script.as_posix(), *args, self.public.as_posix()],
            capture_output=True, cwd=str(self.dev), env=env)
        self.stdout = done.stdout.decode("utf-8", "replace")
        self.stderr = done.stderr.decode("utf-8", "replace")
        self.returncode = done.returncode
        return self

    def dev_status(self):
        return subprocess.run(["git", "-C", str(self.dev), "status", "--porcelain"],
                              check=True, capture_output=True,
                              env=_env(self.dev.parent)).stdout.decode("utf-8", "replace")

    def leftovers(self):
        """Whatever the run left in its temporary directory; a clean run leaves nothing."""
        return sorted(os.listdir(str(self.tmpdir)))


def _differing_pair():
    """Dev and public trees that differ in plugins/ (60 files, past the 40-line cut) and docs/.

    README.md differs too; .claude-plugin/ is absent in public; one file the dev tag propagated
    under plugins/ has no public counterpart.
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
        for heading in ("=== Public commits since the newest tag", MISSING_HEADING):
            with self.subTest(section=heading):
                self.assertIn(heading, fx.stdout, "a section never printed:\n" + fx.stdout)
        self.assertIn("fix: a public-side edit after the tag", fx.stdout,
                      "the commit list is missing the public commit after the tag")
        self.assertIn("  plugins/senzing-bootcamp/dev-only.md", fx.stdout,
                      "the last-propagation-not-in-public list is missing the file public lacks")
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
        for text in ("=== Public commits since the newest tag", MISSING_HEADING,
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


# --- #202: the report is taken against the last propagation ------------------------------------ #

#: The report_path comparison lines, and the deletion section's file source. Each is what a
#: negative control below points back at dev's tree, so each must appear as counted.
BASE_OPERAND = '"$base/$rel"'
BASELINE_FILES = 'git -C "$base" ls-files -z --others'
#: What pointing the deletion section back at dev looks like: dev's tracked files.
DEV_FILES = 'git -C "$here" ls-files -z'
#: A copy of propagate's logic inside retrofit.sh, which INV-300 and the spec rule out.
COPIED_PROPAGATE_LOGIC = re.compile(
    r"\.replace\(|\"name\": \"docktermj\"|development\.md|FAMILY_WORKFLOW\.md|"
    r"\bsed\b[^\n]*docktermj", re.I)


def _propagation_scenario():
    """The #202 acceptance fixture: (dev at the tag, public, dev after the tag, dev uncommitted).

    Public is what the tag's propagate.sh publishes -- written out BY HAND here, so the
    expectation does not come from the code under test -- plus one edit under plugins/. Dev
    then edits one file and adds one after the tag, and leaves one uncommitted edit.
    """
    dev = {
        "plugins/senzing-bootcamp/a.md": "a\n",
        "plugins/senzing-bootcamp/b.md": "b\n",
        "plugins/senzing-bootcamp/slug.md": "See https://github.com/%s\n" % DEV_SLUG,
        ".claude-plugin/marketplace.json":
            '{\n  "name": "senzing-bootcamp-dev",\n  "owner": { "name": "docktermj" },\n'
            '  "source": "%s"\n}\n' % DEV_SLUG,
        "docs/guide.md": "guide\n",
        "docs/development.md": "maintainer only -- propagate.sh excludes this\n",
        "README.md": "Install from %s\n" % DEV_SLUG,
    }
    public = {
        "plugins/senzing-bootcamp/a.md": "a, edited in public\n",
        "plugins/senzing-bootcamp/b.md": "b\n",
        "plugins/senzing-bootcamp/slug.md": "See https://github.com/%s\n" % PUBLIC_SLUG,
        ".claude-plugin/marketplace.json":
            '{\n  "name": "senzing-bootcamp",\n  "owner": { "name": "Senzing" },\n'
            '  "source": "%s"\n}\n' % PUBLIC_SLUG,
        "docs/guide.md": "guide\n",
        "README.md": "Install from %s\n" % PUBLIC_SLUG,
    }
    after = {"plugins/senzing-bootcamp/b.md": "b, changed in dev after the tag\n",
             "plugins/senzing-bootcamp/new.md": "added in dev after the tag\n"}
    dirty = {"docs/guide.md": "an uncommitted dev edit\n"}
    return dev, public, after, dirty


def _missing_section(fx):
    """The lines listed under "In the last propagation but not in public"."""
    lines = fx.stdout.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(MISSING_HEADING))
    listed = []
    for line in lines[start + 1:]:
        if not line.strip():
            break
        listed.append(line.strip())
    return listed


def _script_with(old, new, count):
    text = _script_text()
    if text.count(old) != count:
        raise AssertionError("retrofit.sh carries %r %d time(s), not %d; the negative control "
                             "no longer mutates what it names" % (old, text.count(old), count))
    return text.replace(old, new)


@unittest.skipUnless(HAVE_TOOLS, "bash, git, diff, tar, rsync and python3 are needed")
class TheReportIsTakenAgainstTheLastPropagation(unittest.TestCase):
    """#202: public is compared against the baseline tag as its own propagate.sh publishes it."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        dev, public, after, dirty = _propagation_scenario()
        cls.fx = Fixture(os.path.join(cls._tmp.name, "scenario"), dev, public,
                         dev_after=after, dev_dirty=dirty).run()

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _tmpdir(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return tmp.name

    def _report(self, fx):
        return "\nstdout:\n%s\nstderr:\n%s" % (fx.stdout, fx.stderr)

    def test_only_the_public_edit_is_reported(self):
        fx = self.fx
        self.assertEqual(fx.returncode, 0, self._report(fx))
        self.assertEqual([line.split()[-1] for line in _differs_only(fx)], ["plugins"],
                         "only plugins/ changed in public since the tag" + self._report(fx))
        listing = _listing_after(fx, "plugins")
        self.assertEqual(len(listing), 1, "plugins/ must list only the public edit" + self._report(fx))
        self.assertIn("plugins/senzing-bootcamp/a.md", listing[0])
        for rel in (".claude-plugin", "docs", "README.md"):
            with self.subTest(path=rel):
                self.assertIn("  same                    " + rel, fx.stdout, self._report(fx))

    def test_dev_work_after_the_tag_is_not_reported(self):
        for name in ("b.md", "new.md", "an uncommitted dev edit"):
            with self.subTest(file=name):
                self.assertNotIn(name, self.fx.stdout,
                                 "dev work since the tag reads as a public edit" + self._report(self.fx))

    def test_a_slug_only_difference_is_not_reported(self):
        """slug.md and marketplace.json differ from dev only by the forward rewrite.

        README.md does too; it has a path line of its own, which the first test asserts `same`.
        The two marketplace.json files differ in the marketplace name as well as the owner
        (#449), so a name-only difference must not be reported either.
        """
        for name in ("slug.md", "marketplace.json"):
            with self.subTest(file=name):
                self.assertNotIn(name, self.fx.stdout, self._report(self.fx))

    def test_the_header_names_the_baseline_and_how_it_was_chosen(self):
        self.assertRegex(self.fx.stdout, r"(?m)^Baseline: +dev tag v1\.0\.0 \(public's newest tag\)",
                         self._report(self.fx))

    def test_the_run_leaves_dev_unchanged_and_removes_its_temp_directory(self):
        """INV-312: the fixture's dev tree is dirty on purpose, so "unchanged" is not "clean"."""
        self.assertNotEqual(self.fx.status_before, "", "the fixture lost its uncommitted edit")
        self.assertEqual(self.fx.dev_status(), self.fx.status_before,
                         "the run changed dev's working tree (INV-312)")
        self.assertEqual(self.fx.leftovers(), [], "the run left its temporary baseline behind")

    def test_a_file_public_deleted_is_listed_and_a_dev_addition_is_not(self):
        dev, public, after, dirty = _propagation_scenario()
        del public["plugins/senzing-bootcamp/b.md"]
        fx = Fixture(self._tmpdir(), dev, public, dev_after=after, dev_dirty=dirty).run()
        listed = _missing_section(fx)
        self.assertIn("plugins/senzing-bootcamp/b.md", listed, self._report(fx))
        for rel in ("plugins/senzing-bootcamp/new.md", "docs/development.md"):
            with self.subTest(path=rel):
                self.assertNotIn(rel, listed, "the baseline never published it" + self._report(fx))

    def test_base_overrides_public_s_newest_tag(self):
        """Committed in public, not yet tagged: public still carries v0.9.0 but holds v1.0.0."""
        dev, public, _, _ = _propagation_scenario()
        public["plugins/senzing-bootcamp/a.md"] = "a, released in v1.0.0\n"
        tags = [("v0.9.0", {}), ("v1.0.0", {"plugins/senzing-bootcamp/a.md": "a, released in v1.0.0\n"})]
        fx = Fixture(self._tmpdir(), dev, public, dev_tags=tags, public_tag="v0.9.0").run()
        self.assertRegex(fx.stdout, r"(?m)^Baseline: +dev tag v0\.9\.0 \(public's newest tag\)")
        self.assertEqual([line.split()[-1] for line in _differs_only(fx)], ["plugins"],
                         "by default the new release reads as a public edit" + self._report(fx))
        fx = fx.run("--base", "v1.0.0")
        self.assertEqual(fx.returncode, 0, self._report(fx))
        self.assertRegex(fx.stdout, r"(?m)^Baseline: +dev tag v1\.0\.0 \(named by --base\)")
        self.assertEqual(_differs_only(fx), [], "--base v1.0.0 was not the baseline" + self._report(fx))
        self.assertIn("0 propagated path(s) differ.", fx.stdout)

    def _assert_aborts_before_printing(self, fx, *named):
        self.assertNotEqual(fx.returncode, 0, "a run with no baseline must fail" + self._report(fx))
        self.assertEqual(fx.stdout, "", "a no-baseline abort printed a report" + self._report(fx))
        for text in named + ("--base",):
            with self.subTest(names=text):
                self.assertIn(text, fx.stderr)
        self.assertEqual(fx.leftovers(), [], "the abort left its temporary directory behind")
        self.assertEqual(fx.dev_status(), fx.status_before, "the abort changed dev (INV-312)")

    def test_public_with_no_tag_aborts(self):
        fx = Fixture(self._tmpdir(), *_identical_pair(), public_tag=None).run()
        self._assert_aborts_before_printing(fx, "has no tag")

    def test_no_dev_tag_of_that_name_aborts(self):
        fx = Fixture(self._tmpdir(), *_identical_pair(), dev_tags=[("v0.1.0", {})]).run()
        self._assert_aborts_before_printing(fx, "'v1.0.0'")

    def test_a_tag_without_propagate_aborts(self):
        """Dev tags 0.3.5 and 0.3.6 predate propagate.sh."""
        fx = Fixture(self._tmpdir(), *_identical_pair(), propagate=None).run()
        self._assert_aborts_before_printing(fx, "'v1.0.0'", "propagate.sh")

    def test_base_naming_no_tag_aborts(self):
        fx = Fixture(self._tmpdir(), *_identical_pair()).run("--base", "v9.9.9")
        self._assert_aborts_before_printing(fx, "'v9.9.9'")

    def test_a_failing_propagate_aborts_with_its_stderr(self):
        """The trap's case: the temp directory exists when this abort happens."""
        broken = "#!/usr/bin/env bash\necho 'normal output'\necho 'propagate broke' >&2\nexit 3\n"
        fx = Fixture(self._tmpdir(), *_identical_pair(), propagate=broken).run()
        self._assert_aborts_before_printing(fx, "'v1.0.0'", "propagate broke")
        self.assertNotIn("normal output", fx.stderr)

    def test_retrofit_carries_no_copy_of_propagate_s_logic(self):
        """INV-300: the rewrite and the docs/ exclusions come from the tag's propagate.sh."""
        hit = COPIED_PROPAGATE_LOGIC.search(_script_text())
        self.assertIsNone(hit, "retrofit.sh carries a copy of propagate.sh's logic (%r)"
                               % (hit.group(0) if hit else ""))

    def test_negative_control_comparing_against_dev_reports_dev_work(self):
        dev, public, after, dirty = _propagation_scenario()
        fx = Fixture(self._tmpdir(), dev, public, dev_after=after, dev_dirty=dirty,
                     script=_script_with(BASE_OPERAND, '"$here/$rel"', 2)).run()
        self.assertNotEqual([line.split()[-1] for line in _differs_only(fx)], ["plugins"],
                            "pointed at dev, the report still showed only the public edit; the "
                            "tests above would not catch the regression #202 fixed" + self._report(fx))
        self.assertIn("new.md", fx.stdout, self._report(fx))

    def test_negative_control_listing_dev_files_reports_a_dev_addition(self):
        dev, public, after, dirty = _propagation_scenario()
        del public["plugins/senzing-bootcamp/b.md"]
        fx = Fixture(self._tmpdir(), dev, public, dev_after=after, dev_dirty=dirty,
                     script=_script_with(BASELINE_FILES, DEV_FILES, 1)).run()
        self.assertIn("plugins/senzing-bootcamp/new.md", _missing_section(fx),
                      "pointed at dev, the deletion section did not list the dev addition" +
                      self._report(fx))


# --- #224: the prose describes the report, and build artifacts are not differences ------------- #

#: Wording from the copy #54 retired. Each describes work this command no longer does.
STALE_PHRASES = ("add/update", "Run the copy", "reconcile every test", "Step 5",
                 "back into this development repo")


def _stale_hits(text):
    """The retired phrases `text` carries, whitespace-flattened so a line wrap cannot hide one."""
    body = flat(text)
    return [phrase for phrase in STALE_PHRASES if flat(phrase) in body]


class NoCopyWordingReturns(unittest.TestCase):
    """#224: the skill describes the report, not the copy #54 retired."""

    def _files(self):
        return (("the skill", SKILL),)

    def test_the_skill_does_not_describe_the_copy(self):
        for name, path in self._files():
            with self.subTest(file=name):
                self.assertEqual(
                    [], _stale_hits(path.read_text(encoding="utf-8")),
                    "%s describes the copy #54 retired. The command compares, reports and files "
                    "issues; the prose around it said otherwise until #224" % name)

    def test_negative_control_a_planted_phrase_is_caught(self):
        """INV-282: each phrase planted into the real text, across a line wrap too, is found."""
        for name, path in self._files():
            clean = path.read_text(encoding="utf-8")
            for phrase in STALE_PHRASES:
                for planted in (phrase, phrase.replace(" ", "\n  ", 1)):
                    with self.subTest(file=name, planted=planted):
                        self.assertIn(phrase, _stale_hits(clean + "\n" + planted + "\n"))


#: `propagate.sh`'s plugin-payload exclusions: the array its `rsync` expands.
PROPAGATE_EXCLUDES = re.compile(r"^excludes=\((?P<body>[^)\n]*)\)", re.M)


def _propagate_excludes():
    m = PROPAGATE_EXCLUDES.search(_propagate_text())
    return {p.rstrip("/") for p in re.findall(r"--exclude='([^']+)'", m.group("body"))} if m else set()


def _retrofit_ignores(line):
    return {x.strip("'") for x in re.findall(r"-x ('[^']+'|\S+)", line)}


#: Build artifacts in public, one per exclusion. The baseline never holds them.
ARTIFACTS = {
    "plugins/senzing-bootcamp/scripts/__pycache__/x.pyc": "bytecode\n",
    "plugins/senzing-bootcamp/scripts/y.pyc": "bytecode\n",
    "plugins/senzing-bootcamp/.pytest_cache/v/cache/lastfailed": "{}\n",
}


@unittest.skipUnless(HAVE_TOOLS, "bash, git, diff, tar, rsync and python3 are needed")
class TheBuildArtifactsAreNotDifferences(unittest.TestCase):
    """#224: a public checkout where anything has run still reports `plugins` `same`."""

    def _tmpdir(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return tmp.name

    def _run(self, public_extra, script=None):
        """Dev and public share `scripts/`, so an artifact nested in it is the only difference."""
        dev, public = _identical_pair()
        for tree in (dev, public):
            tree["plugins/senzing-bootcamp/scripts/run.py"] = "print('run')\n"
        public.update(public_extra)
        return Fixture(self._tmpdir(), dev, public, script=script).run()

    def test_retrofit_ignores_what_propagate_excludes(self):
        """The baseline lacks exactly what propagate.sh excludes, so the comparison must too."""
        expected = _propagate_excludes()
        self.assertTrue(expected, "propagate.sh's `excludes=(...)` array did not parse")
        for guard in (GUARDED_STATUS, GUARDED_LISTING):
            with self.subTest(line=guard):
                self.assertEqual(_script_text().count(guard), 1,
                                 "retrofit.sh no longer carries %r" % guard)
                self.assertEqual(_retrofit_ignores(guard), expected)

    def test_artifacts_in_public_leave_plugins_same(self):
        fx = self._run(ARTIFACTS)
        self.assertEqual(fx.returncode, 0, fx.stdout + fx.stderr)
        self.assertIn("  same                    plugins", fx.stdout, fx.stdout)
        self.assertIn("0 propagated path(s) differ.", fx.stdout)

    def test_the_listing_of_a_real_edit_names_no_artifact(self):
        edit = {"plugins/senzing-bootcamp/a.md": "edited in public\n"}
        fx = self._run(dict(ARTIFACTS, **edit))
        listing = _listing_after(fx, "plugins")
        self.assertEqual(len(listing), 1, "plugins/ must list only the public edit:\n" + fx.stdout)
        self.assertIn("plugins/senzing-bootcamp/a.md", listing[0])

    def test_negative_control_each_artifact_differs_without_its_exclusion(self):
        for flag in sorted(_retrofit_ignores(GUARDED_STATUS)):
            quoted = "'%s'" % flag if "*" in flag else flag
            with self.subTest(dropped=flag):
                fx = self._run(ARTIFACTS, script=_script_with("-x %s " % quoted, "", 2))
                self.assertIn("  DIFFERS                 plugins", fx.stdout,
                              "without -x %s the artifacts still read same; the fixture no longer "
                              "exercises that exclusion:\n%s" % (flag, fx.stdout))

    def test_negative_control_an_unexcluded_listing_prints_the_artifacts(self):
        """The status line alone is not enough: the listing would still print the artifacts."""
        edit = {"plugins/senzing-bootcamp/a.md": "edited in public\n"}
        fx = self._run(dict(ARTIFACTS, **edit),
                       script=_script_with(GUARDED_LISTING, GUARDED_LISTING.replace(IGNORED, ""), 1))
        self.assertGreater(len(_listing_after(fx, "plugins")), 1, fx.stdout)


if __name__ == "__main__":
    unittest.main()
