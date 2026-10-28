"""An auto-test walk runs on the scaffold it asked for, or does not run at all (#840).

#834 moved each run root under the system temp directory, and dry-run's
`scaffold_project.py` refused every path under `/tmp/`. `autotest.build_sandbox` caught the
refusal, printed one stderr line and walked five empty folders under the label the run had
asked for: a `--seed seeded` walk was a fresh one, the honor-don't-ask path (INV-133) was
never exercised, and the report said "0 BREAKING" with exit 0.

Pinned here:

1. **`build_sandbox` builds each mode under the temp directory.** The real scaffold, run as a
   real subprocess into a `tempfile.mkdtemp()` root (never a literal `/tmp`), writes the
   seeded `config/bootcamp_preferences.yaml` for `seeded` and the fresh fixtures for `fresh`,
   and the call carries `--run-root <the run root>`, the flag that vouches for it.
2. **A failed scaffold skips the walk.** `walk.py` is never started, the report carries a
   BREAKING `scaffold-failed` finding in `walk-failed`'s shape (#732) naming the scaffold's
   error, the probe's findings are still reported, and `main()` returns 1. A missing scaffold
   file is the same failure: there is no fallback project to walk.
3. **The walk is handed the project its seed built.** `autotest.main --walk`, with the real
   scaffold and a stub `walk.py` that records the project it was given, walks a project
   inside the run root `--run-root` vouched for, holding that seed's fixtures (grafted from
   the race's approach A, #840).

This is the walk-failure rule of INV-376 one step earlier; INV-376's 2026-10-27 note (#840)
says so, registered, applied 2026-10-27.

Negative controls, each run by hand when this was written: the scaffold's old unconditional
`/tmp` refusal put back fails (1) and (3) on a host whose temp directory is `/tmp`;
`--run-root` dropped from `build_sandbox`'s call fails (1) on every host, through the
recorded call; the five-folder fallback put back fails (2); `main()` handing the walk the run
root instead of its project fails (3).

Offline and stdlib only (INV-108): the scaffold writes only into the test's own temporary
directory, and in (2) and (3) the probe, the walk and the lint are stub scripts.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / ".claude" / "skills" / "auto-test"
SCAFFOLD = REPO_ROOT / ".claude" / "skills" / "dry-run" / "scaffold_project.py"

sys.path.insert(0, str(HARNESS))
import autotest  # noqa: E402


def load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold_project_840", SCAFFOLD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TheScaffoldBuildsUnderTheTempDirectory(unittest.TestCase):
    """Half 1: the real scaffold, through `build_sandbox`, into a fresh temp-directory root."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="senzing-autotest-840-")).resolve()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.calls = []
        real_run = autotest._run

        def spy(cmd, **kw):
            self.calls.append([str(c) for c in cmd])
            return real_run(cmd, **kw)
        saved = (autotest._run, autotest.SCAFFOLD)

        def restore():
            autotest._run, autotest.SCAFFOLD = saved
        self.addCleanup(restore)
        autotest._run = spy
        autotest.SCAFFOLD = SCAFFOLD
        self.scaffold = load_scaffold()

    def build(self, seed):
        with redirect_stderr(io.StringIO()):
            project, error = autotest.build_sandbox(self.root, seed)
        self.assertIsNone(error, f"the scaffold failed under {self.root}: {error}")
        self.assertIn(Path(tempfile.gettempdir()).resolve(), project.parents)
        return project

    def test_seeded_writes_the_seeded_preferences(self):
        project = self.build("seeded")
        prefs = project / "config" / "bootcamp_preferences.yaml"
        self.assertEqual(self.scaffold.SEEDED_PREFERENCES, prefs.read_text(encoding="utf-8"))
        self.assertEqual("{}\n", (project / "config" / "bootcamp_progress.json")
                         .read_text(encoding="utf-8"))

    def test_fresh_writes_the_fresh_fixtures(self):
        project = self.build("fresh")
        self.assertEqual("{}\n", (project / "config" / "bootcamp_progress.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual("", (project / "config" / "bootcamp_preferences.yaml")
                         .read_text(encoding="utf-8"))
        self.assertTrue((project / "docs" / "feedback"
                         / "SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md").is_file())
        # More than the five folders of the retired fallback, and none of the mid fixtures.
        self.assertTrue((project / "src" / "system_verification").is_dir())
        self.assertFalse((project / "docs" / "bootcamp_recap.md").exists())

    def test_the_call_vouches_for_this_run_root(self):
        """Holds on every host: the flag is on the call, naming this run's own root."""
        self.build("seeded")
        scaffold_calls = [c for c in self.calls if str(SCAFFOLD) in c]
        self.assertEqual(1, len(scaffold_calls), self.calls)
        call = scaffold_calls[0]
        self.assertIn("--run-root", call)
        self.assertEqual(str(self.root), call[call.index("--run-root") + 1])
        self.assertIn("--seeded", call)


#: The probe's stub reports one finding, so the report can be checked for it after a failure.
PROBE_FINDING = {"severity": "WATCH", "code": "silent-accept",
                 "message": "the probe's own finding survives a failed scaffold"}


class AutotestWalkHarness(unittest.TestCase):
    """`autotest.main --walk` with stub probe, walk and lint scripts on disk.

    The stub walk leaves a marker file when it starts, recording the project it was handed and
    the seed files it found there, so "the walk never ran" and "what the walk was given" are
    read off the disk rather than inferred. `SANDBOX_ROOT` and `REPORT_DIR` point into the
    test's temporary directory, which is under the system temp directory, and the git worktree
    is replaced; nothing touches `~/senzing-autotest`.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.skill = self.tmp / "skill"
        self.skill.mkdir()
        self.marker = self.tmp / "walk-ran"
        (self.skill / "mcp_probe.py").write_text(
            "import json\nprint(json.dumps([%r]))\n" % PROBE_FINDING, encoding="utf-8")
        (self.skill / "transcript_lint.py").write_text("print('[]')\n", encoding="utf-8")
        (self.skill / "walk.py").write_text(
            "import json, sys\nfrom pathlib import Path\n"
            "project = Path(sys.argv[sys.argv.index('--project') + 1])\n"
            "def read(name):\n"
            "    path = project / 'config' / name\n"
            "    return path.read_text(encoding='utf-8') if path.is_file() else None\n"
            "Path(%r).write_text(json.dumps({'project': str(project),\n"
            "    'preferences': read('bootcamp_preferences.yaml'),\n"
            "    'progress': read('bootcamp_progress.json')}), encoding='utf-8')\n"
            "out = Path(sys.argv[sys.argv.index('--out') + 1])\n"
            "out.write_text('{\"turn\": 1}\\n', encoding='utf-8')\n" % str(self.marker),
            encoding="utf-8")
        saved = (autotest.SKILL_DIR, autotest.SANDBOX_ROOT, autotest.REPORT_DIR,
                 autotest.SCAFFOLD, autotest.build_sandbox, autotest.make_worktree,
                 autotest.drop_worktree)

        def restore():
            (autotest.SKILL_DIR, autotest.SANDBOX_ROOT, autotest.REPORT_DIR,
             autotest.SCAFFOLD, autotest.build_sandbox, autotest.make_worktree,
             autotest.drop_worktree) = saved
        self.addCleanup(restore)
        autotest.SKILL_DIR = self.skill
        autotest.SANDBOX_ROOT = self.tmp / "senzing-autotest"
        autotest.REPORT_DIR = autotest.SANDBOX_ROOT / "reports"
        autotest.make_worktree = lambda root, ref: (root / "plugin-src", "a" * 40)
        autotest.drop_worktree = lambda worktree: None
        self.runs = 0

    def run_autotest(self, seed="seeded"):
        """Run `autotest.main --walk`; return (code, stdout, stderr, report)."""
        self.runs += 1
        reports = self.tmp / f"reports-{self.runs}"
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = autotest.main(["--walk", "--seed", seed, "--report-dir", str(reports)])
        report = json.loads((reports / "latest.json").read_text(encoding="utf-8"))
        return code, out.getvalue(), err.getvalue(), report

    def walked(self):
        """What the stub walk recorded, or None when it never ran; clears the record."""
        if not self.marker.is_file():
            return None
        record = json.loads(self.marker.read_text(encoding="utf-8"))
        self.marker.unlink()
        return record


class AFailedScaffoldSkipsTheWalk(AutotestWalkHarness):
    """Half 2: a failed scaffold is a BREAKING finding, and no walk."""

    def assert_scaffold_failed(self, code, printed, report, error):
        self.assertEqual(1, code)
        failed = [f for f in report["findings"] if f["code"] == "scaffold-failed"]
        self.assertEqual(1, len(failed), report["findings"])
        self.assertEqual({"severity": "BREAKING", "code": "scaffold-failed", "source": "walk"},
                         {k: failed[0][k] for k in ("severity", "code", "source")})
        self.assertIn(error, failed[0]["message"])
        self.assertIn("--seed seeded", failed[0]["message"])
        self.assertIn("[BREAKING] scaffold-failed", printed)
        self.assertFalse(self.marker.exists(), "walk.py ran although the scaffold failed")
        self.assertNotIn("walk-failed", [f["code"] for f in report["findings"]])
        # The probe ran first, and its findings are still reported.
        self.assertIn(PROBE_FINDING["code"], [f["code"] for f in report["findings"]])
        self.assertTrue(any("scaffold failed" in limit for limit in report["coverage_limits"]))

    def test_a_scaffold_step_that_fails_skips_the_walk(self):
        error = "Refusing to build under the stub's directory: stubbed to fail"
        autotest.build_sandbox = lambda root, seed: (
            root / "project", "Traceback (most recent call last):\n  ...\n" + error)
        code, printed, stderr, report = self.run_autotest()
        self.assert_scaffold_failed(code, printed, report, error)
        self.assertIn("Traceback (most recent call last)", stderr, "the whole error is printed")

        # Control: the same run with a scaffold step that succeeds walks, and exits 0.
        autotest.build_sandbox = lambda root, seed: (root / "project", None)
        code, _printed, _stderr, report = self.run_autotest()
        self.assertEqual(0, code)
        self.assertTrue(self.marker.exists(), "the control never reached the walk")
        self.assertEqual(["silent-accept"], [f["code"] for f in report["findings"]])

    def test_a_scaffold_that_exits_non_zero_carries_its_stderr(self):
        """The real `build_sandbox`, against a scaffold script that refuses its target."""
        error = "Refusing to build here: stubbed refusal"
        autotest.SCAFFOLD = self.tmp / "scaffold_project.py"
        autotest.SCAFFOLD.write_text(
            "import sys\nsys.stderr.write(%r)\nsys.exit(2)\n" % (error + "\n"),
            encoding="utf-8")
        code, printed, _stderr, report = self.run_autotest()
        self.assert_scaffold_failed(code, printed, report, error)

    def test_a_missing_scaffold_is_a_failure_not_a_fallback(self):
        autotest.SCAFFOLD = self.tmp / "no-such-scaffold.py"
        code, printed, _stderr, report = self.run_autotest()
        self.assert_scaffold_failed(code, printed, report, "the scaffold is missing")
        self.assertNotIn("artifacts", report, "a project was reported for a walk never run")

    def test_a_probe_only_run_never_builds_a_project(self):
        """No `--walk`: no scaffold, no finding, the probe's report as before."""
        autotest.build_sandbox = lambda root, seed: self.fail("a probe-only run scaffolded")
        reports = self.tmp / "probe-only"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = autotest.main(["--report-dir", str(reports)])
        report = json.loads((reports / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(0, code)
        self.assertEqual(["silent-accept"], [f["code"] for f in report["findings"]])
        self.assertFalse(self.marker.exists())


class TheWalkGetsTheProjectItsSeedBuilt(AutotestWalkHarness):
    """Half 3: the hand-off from the real scaffold to the walk (approach A's test, #840)."""

    def test_each_seed_reaches_the_walk(self):
        self.assertEqual(SCAFFOLD, autotest.SCAFFOLD, "the real scaffold must be under test")
        scaffold = load_scaffold()
        for seed in ("seeded", "fresh"):
            with self.subTest(seed=seed):
                code, printed, stderr, report = self.run_autotest(seed)
                self.assertEqual(
                    [], [f for f in report["findings"] if f["code"] == "scaffold-failed"],
                    printed + stderr)
                self.assertEqual(0, code, printed + stderr)
                walked = self.walked()
                self.assertIsNotNone(walked, "the walk did not run")
                project = Path(walked["project"])
                # The walk's project is inside the run root `--run-root` vouched for, which
                # is itself under the system temp directory.
                self.assertIn(Path(report["sandbox"]), project.parents)
                self.assertIn(Path(tempfile.gettempdir()).resolve(), project.parents)
                expected = scaffold.SEEDED_PREFERENCES if seed == "seeded" else ""
                self.assertEqual(expected, walked["preferences"],
                                 f"--seed {seed}: the walk got the wrong preferences file")
                self.assertEqual("{}\n", walked["progress"],
                                 f"--seed {seed}: the walk got the wrong progress file")
                self.assertIn(str(Path("config", "bootcamp_preferences.yaml")),
                              report["artifacts"])


if __name__ == "__main__":
    unittest.main()
