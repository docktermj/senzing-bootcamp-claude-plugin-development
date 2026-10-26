"""A simulated walk that dies keeps its turns, and the run says so (#732).

Enforces **INV-376**, registered by the maintainer 2026-10-19. ⚠️ This file **cannot**
establish that a live walk survives a real `SIGKILL`, an out-of-memory kill or a pulled
plug -- only that each event reaches the file before the next turn begins, which is the
property that makes surviving one possible. Nor can it establish that the cause a failed
walk reports is the true one; only that the stream carrying the cause is printed rather
than short-circuited away. An `Enforced by` clause naming this file is therefore not a
claim that a real crash was ever survived in the field.

A `/dry-run --simulated confused` walk ran 68 turns over 37 minutes, drove the bootcamp from
the onboarding preface through System verification, died mid-turn-68, and left nothing on
disk. `autotest.py` filed that as a line in `coverage_limits` -- "the walk produced no
transcript, so no interaction invariant was checked" -- and **exited 0**. The most expensive
evidence a dry run gathers was spent, lost, and reported as a clean bill of health.

Two halves, both guarded here:

1. **`walk.py` keeps what it has walked.** Each event is appended to `--out` and flushed as
   it is produced, so the record is durable before the next turn begins. The closing
   `walk_stop` event comes from a `try/finally` around the turn loop, so an abnormal end is
   recorded as well as survived, and a `subprocess.TimeoutExpired` from either `claude` call
   ends the walk with a reason naming the timeout instead of propagating. `main` then exits
   non-zero.
2. **`autotest.py` reports a failed walk as a failure.** It reads the walk's exit code, files
   a BREAKING finding for a non-zero one (so the run exits non-zero), and prints the walk's
   stderr whenever the walk failed -- the `stdout or stderr` short-circuit destroyed the one
   traceback that would have named what killed that 68-turn walk, which is why the cause is
   still unknown.

A `claude` child that **exits non-zero** is an abnormal end too (#794), and before #794 this file
never stubbed one: the guide's non-zero exit set a stop reason and no failure, so `main`
exited 0, and the Bootcamper's exit code was never read. `AChildThatExitsNonZeroIsAFailure`
stubs a non-zero exit at each child, through the real `bootcamper_reply`, with stderr over
2,000 characters marked at both ends, and requires the whole of it in the `walk_error` event
and on the console; each case runs beside the same stub exiting 0, which keeps today's
verdict.

⚠️ **Why a `try/finally` write would pass most of these and still be wrong.** It survives an
exception and loses everything to a `SIGKILL`, an out-of-memory kill or a pulled plug.
`test_every_turn_is_on_disk_before_the_next_one_starts` is the assertion that tells the two
designs apart: it reads the file from inside the walk, between turns, where a write on the way
out has not happened yet.

⚠️ **Vacuity.** A stub that always fails and a harness that always reports BREAKING look the
same from the assertion's side, so every failure case here runs its own control in the same
test method: the same stub, the same arguments, exit code 0, and the opposite verdict
required. The stub also prints 68 turn lines to stdout before its traceback, which is the
shape the old short-circuit could not see past, and one test pins that shape on its own so
the stub cannot quietly stop having it.

No phrase-level pattern (#732): every line this file reads is one JSON event of a JSONL
transcript or one line of a harness's captured output. Neither is Markdown prose, so there is
no phrase for a wrap-aware collapse to find and nothing a line boundary can split.

Stdlib only; nothing under `plugins/` is imported (INV-108).

Source issue: #732 (a crashed simulated walk loses its whole transcript and is reported as a
coverage limit with exit 0); #794 (a child that exits non-zero is reported as clean, with its
stderr cut).

Run:  python3 -m unittest discover -s tests
"""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
AUTO_TEST = REPO_ROOT / ".claude" / "skills" / "auto-test"

sys.path.insert(0, str(AUTO_TEST))

import autotest  # noqa: E402
import walk  # noqa: E402

POINTER = "\U0001f449"
OPENING = "/senzing-bootcamp:start-bootcamp"


def _assistant(text):
    return json.dumps({"type": "assistant",
                       "message": {"content": [{"type": "text", "text": text}]}})


def _guide_turn(n):
    """A turn long enough to clear the non-start guard, ending in a question."""
    return f"Turn {n} of the bootcamp. " + "x" * 220 + f"\n{POINTER} What next?"


def _events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _project(tmp):
    """``<tmp>/project``, the layout ``autotest.py`` gives a walk: ``walk.py`` creates the
    Bootcamper's cwd beside the project, so a project at ``tmp`` itself would put it in the
    shared temp directory (#834)."""
    project = Path(tmp) / "project"
    project.mkdir(exist_ok=True)
    return str(project)


class ACrashedWalkKeepsEveryTurnItCompleted(unittest.TestCase):
    """Half 1: `walk.py`, with both `claude` calls stubbed. No token is spent."""

    def walk(self, guide_dies_at=None, bootcamper_dies_at=None, raises=None, turns=4):
        """Walk `turns` turns, optionally dying at a given call; return (failure, events)."""
        calls, replies = [], []

        def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
            calls.append(list(args))
            if len(calls) == guide_dies_at:
                raise (raises or subprocess.TimeoutExpired(cmd=["claude"], timeout=timeout))
            return subprocess.CompletedProcess(
                args, 0, stdout=_assistant(_guide_turn(len(calls))) + "\n", stderr="")

        def fake_reply(prompt_text, persona, model, cwd=None, timeout=180):
            replies.append(prompt_text)
            if len(replies) == bootcamper_dies_at:
                raise subprocess.TimeoutExpired(cmd=["claude"], timeout=timeout)
            return "1"

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(walk, "_claude", fake_claude), \
                mock.patch.object(walk, "bootcamper_reply", fake_reply), \
                redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
            out = Path(tmp) / "t.jsonl"
            events, failure = None, None
            try:
                events, failure = walk.run_walk(
                    _project(tmp), out, turns, "terse", Path(tmp) / "mcp.json", None, None,
                    OPENING, False, 600)
            except Exception as raised:          # re-raised by design; see the test below
                failure = raised
            written = _events(out)
        if events is not None:
            self.assertEqual(events, len(written),
                             "run_walk reported an event count the file does not hold")
        return failure, written

    def test_a_guide_timeout_keeps_the_turns_before_it_and_names_itself(self):
        failure, written = self.walk(guide_dies_at=3)
        self.assertIn("timed out", failure)
        self.assertIn("600", failure)
        self.assertEqual(2, sum(e["type"] == "assistant" for e in written))
        stop = written[-1]
        self.assertEqual("walk_stop", stop["type"])
        self.assertEqual(stop["reason"], failure)
        self.assertEqual(3, stop["turn"])

        # Control: the identical walk without the timeout ends normally and reports none.
        clean_failure, clean = self.walk()
        self.assertIsNone(clean_failure)
        self.assertEqual(4, sum(e["type"] == "assistant" for e in clean))
        self.assertEqual("--turns 4 reached", clean[-1]["reason"])

    def test_a_bootcamper_timeout_ends_the_walk_the_same_way(self):
        failure, written = self.walk(bootcamper_dies_at=2)
        self.assertIn("Bootcamper", failure)
        self.assertIn("timed out", failure)
        self.assertEqual("walk_stop", written[-1]["type"])
        self.assertEqual(written[-1]["reason"], failure)
        # Turn 2's guide output arrived before the Bootcamper was asked, so it is kept.
        self.assertEqual(2, sum(e["type"] == "assistant" for e in written))

        clean_failure, clean = self.walk()
        self.assertIsNone(clean_failure)
        self.assertEqual("--turns 4 reached", clean[-1]["reason"])

    def test_an_unanticipated_exception_is_recorded_and_then_re_raised(self):
        """The `finally` writes the stop event; the exception still reaches the caller."""
        failure, written = self.walk(guide_dies_at=3, raises=RuntimeError("boom"))
        self.assertIsInstance(failure, RuntimeError)
        self.assertEqual("walk_stop", written[-1]["type"])
        self.assertIn("RuntimeError", written[-1]["reason"])
        self.assertIn("boom", written[-1]["reason"])
        self.assertEqual(2, sum(e["type"] == "assistant" for e in written))

        clean_failure, clean = self.walk()
        self.assertIsNone(clean_failure)
        self.assertEqual("--turns 4 reached", clean[-1]["reason"])

    def test_every_turn_is_on_disk_before_the_next_one_starts(self):
        """⛔ The assertion a `try/finally` write fails: it reads the file mid-walk.

        A write on the way out leaves every snapshot below empty, however the walk ends, so
        this is the test that tells append-as-produced from a tidy exit path.
        """
        snapshots = []

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "t.jsonl"

            def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
                snapshots.append(_events(out))
                return subprocess.CompletedProcess(
                    args, 0,
                    stdout=_assistant(_guide_turn(len(snapshots))) + "\n", stderr="")

            with mock.patch.object(walk, "_claude", fake_claude), \
                    mock.patch.object(walk, "bootcamper_reply", lambda *a, **k: "1"), \
                    redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                walk.run_walk(_project(tmp), out, 3, "terse", Path(tmp) / "mcp.json",
                              None, None, OPENING, False, 600)

        self.assertEqual(3, len(snapshots))
        # The walk writes one `walk_isolation` preamble before turn 1 (#733). No *turn* may
        # precede turn 1, which is what this assertion is about, so it is stated that way
        # rather than relaxed to "whatever happens to be there".
        self.assertEqual(["walk_isolation"], [e["type"] for e in snapshots[0]],
                         "turn 1 cannot have a predecessor on disk beyond the preamble")
        for turn, seen in enumerate(snapshots[1:], start=2):
            with self.subTest(turn=turn):
                kinds = [e["type"] for e in seen]
                self.assertEqual(turn - 1, kinds.count("assistant"),
                                 f"turn {turn} began with {kinds.count('assistant')} guide "
                                 "turn(s) on disk; every completed turn must already be "
                                 "there")
                self.assertEqual(turn - 1, kinds.count("bootcamper"))
                self.assertNotIn("walk_stop", kinds)
                self.assertEqual(1, kinds.count("walk_isolation"))

    def test_main_exits_non_zero_after_an_abnormal_end_and_zero_otherwise(self):
        def run(dies_at):
            calls = []

            def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
                calls.append(list(args))
                if len(calls) == dies_at:
                    raise subprocess.TimeoutExpired(cmd=["claude"], timeout=timeout)
                return subprocess.CompletedProcess(
                    args, 0, stdout=_assistant(_guide_turn(len(calls))) + "\n", stderr="")

            with tempfile.TemporaryDirectory() as tmp, \
                    mock.patch.object(walk, "_claude", fake_claude), \
                    mock.patch.object(walk, "bootcamper_reply", lambda *a, **k: "1"), \
                    redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                return walk.main(["--project", _project(tmp),
                                  "--out", str(Path(tmp) / "t.jsonl"),
                                  "--mcp-config", str(Path(tmp) / "m.json"),
                                  "--turns", "3"])

        self.assertEqual(1, run(dies_at=2))
        self.assertEqual(0, run(dies_at=None))


#: Over 2,000 characters, marked at both ends: the old guide path kept the last 2,000 in the
#: transcript and the first 200 on the console, so each cut loses one marker (#794).
LONG_STDERR = ("STDERR-HEAD-794 the first line\n" + "frame line\n" * 300
               + "RuntimeError: STDERR-TAIL-794 the cause\n")
BOOTCAMPER_STDOUT = "BOOTCAMPER-STDOUT-794 I would type 1"


def _is_guide(argv):
    """A guide call asks for stream-json; the Bootcamper call asks for text."""
    return "stream-json" in argv


class AChildThatExitsNonZeroIsAFailure(unittest.TestCase):
    """#794: a non-zero exit at either `claude` child ends the walk as a failure.

    One stub stands in for both children, so the Bootcamper path runs through the real
    `bootcamper_reply`. Every failing case is paired with the identical stub exiting 0.
    """

    def setUp(self):
        self.assertGreater(len(LONG_STDERR), 2000)
        previous = walk._SUPPORTS_SETTING_SOURCES
        self.addCleanup(setattr, walk, "_SUPPORTS_SETTING_SOURCES", previous)
        walk._SUPPORTS_SETTING_SOURCES = True

    def walk(self, guide_exit_at=None, bootcamper_exit_at=None, code=1,
             bootcamper_replies=None, turns=3, via_main=False):
        """Run a stubbed walk; return (result, events, guide argvs, console stderr).

        `guide_exit_at` / `bootcamper_exit_at` name the 1-based call of that child that
        exits `code` with `LONG_STDERR` (the Bootcamper's also prints `BOOTCAMPER_STDOUT`).
        `bootcamper_replies` scripts the Bootcamper's stdout per call (default "1").
        `result` is `main`'s exit code with `via_main`, else `run_walk`'s failure.
        """
        guide, bootcamper = [], []

        def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
            if _is_guide(args):
                guide.append(list(args))
                turn = _assistant(_guide_turn(len(guide))) + "\n"
                if len(guide) == guide_exit_at:
                    return subprocess.CompletedProcess(args, code, stdout=turn,
                                                       stderr=LONG_STDERR)
                return subprocess.CompletedProcess(args, 0, stdout=turn, stderr="")
            bootcamper.append(list(args))
            if len(bootcamper) == bootcamper_exit_at:
                return subprocess.CompletedProcess(args, code, stdout=BOOTCAMPER_STDOUT,
                                                   stderr=LONG_STDERR)
            scripted = bootcamper_replies or []
            text = scripted[len(bootcamper) - 1] if len(bootcamper) <= len(scripted) else "1"
            return subprocess.CompletedProcess(args, 0, stdout=text + "\n", stderr="")

        console = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(walk, "_claude", fake_claude), \
                redirect_stdout(io.StringIO()), mock.patch("sys.stderr", console):
            out = Path(tmp) / "t.jsonl"
            if via_main:
                result = walk.main(["--project", _project(tmp), "--out", str(out),
                                    "--mcp-config", str(Path(tmp) / "m.json"),
                                    "--turns", str(turns)])
            else:
                _count, result = walk.run_walk(_project(tmp), out, turns, "terse",
                                               Path(tmp) / "mcp.json", None, None,
                                               OPENING, False, 600)
            written = _events(out)
        return result, written, guide, console.getvalue()

    def assert_whole_stderr_kept(self, written, console, process):
        errors = [e for e in written if e["type"] == "walk_error"]
        self.assertEqual(1, len(errors), "exactly one walk_error event")
        self.assertEqual(process, errors[0]["process"])
        self.assertEqual(1, errors[0]["returncode"])
        self.assertEqual(LONG_STDERR, errors[0]["stderr"],
                         "the walk_error event must keep the child's whole stderr")
        self.assertIn(LONG_STDERR.rstrip(), console,
                      "the console must print the child's whole stderr")

    def test_a_guide_that_exits_non_zero_is_a_failure_with_its_whole_stderr(self):
        failure, written, _guide, console = self.walk(guide_exit_at=2)
        self.assertEqual("the guide process exited 1", failure)
        self.assert_whole_stderr_kept(written, console, "guide")
        self.assertEqual("walk_stop", written[-1]["type"])
        self.assertEqual(failure, written[-1]["reason"])
        self.assertEqual(2, written[-1]["turn"])
        # Turn 1 completed before the crash, so it is kept.
        self.assertEqual(1, sum(e["type"] == "assistant" for e in written))

        # Control: the same stub exiting 0 keeps today's verdict -- no failure, no error.
        failure, written, _guide, console = self.walk(guide_exit_at=2, code=0)
        self.assertIsNone(failure)
        self.assertEqual("--turns 3 reached", written[-1]["reason"])
        self.assertNotIn("walk_error", [e["type"] for e in written])

    def test_a_bootcamper_that_exits_non_zero_is_a_failure_and_its_stdout_is_not_sent(self):
        failure, written, guide, console = self.walk(bootcamper_exit_at=2)
        self.assertEqual("the Bootcamper process exited 1", failure)
        self.assert_whole_stderr_kept(written, console, "Bootcamper")
        self.assertEqual(failure, written[-1]["reason"])
        self.assertEqual(2, written[-1]["turn"])
        # The walk ended there: no third guide call, and the failed reply reached nobody.
        self.assertEqual(2, len(guide))
        self.assertFalse([argv for argv in guide if any(BOOTCAMPER_STDOUT in a for a in argv)],
                         "a failed Bootcamper's stdout was sent to the guide")
        self.assertFalse([e for e in written if e["type"] == "bootcamper"
                          and BOOTCAMPER_STDOUT in e["text"]])

        # Control: the same stub exiting 0 is an ordinary reply, and the walk runs on.
        failure, written, guide, _console = self.walk(bootcamper_exit_at=2, code=0)
        self.assertIsNone(failure)
        self.assertEqual("--turns 3 reached", written[-1]["reason"])
        self.assertEqual(3, len(guide))
        self.assertTrue(any(BOOTCAMPER_STDOUT in a for argv in guide for a in argv),
                        "the control's reply should have reached the guide")

    def test_a_failure_while_a_slash_only_reply_is_re_asked_ends_the_walk_at_once(self):
        # Call 1 is only a slash line, so the Bootcamper is asked again; call 2 fails.
        failure, written, guide, console = self.walk(
            bootcamper_exit_at=2, bootcamper_replies=["/effort high"])
        self.assertEqual("the Bootcamper process exited 1", failure)
        self.assert_whole_stderr_kept(written, console, "Bootcamper")
        self.assertEqual(1, len(guide), "the walk went on after the failed re-ask")
        self.assertEqual(1, written[-1]["turn"])

        # Control: the re-ask answers normally and the walk runs on.
        failure, written, guide, _console = self.walk(
            bootcamper_exit_at=2, code=0, bootcamper_replies=["/effort high"])
        self.assertIsNone(failure)
        self.assertEqual("--turns 3 reached", written[-1]["reason"])

    def test_main_exits_one_for_a_non_zero_exit_at_either_child(self):
        for child in ("guide", "bootcamper"):
            with self.subTest(child=child):
                where = ({"guide_exit_at": 2} if child == "guide"
                         else {"bootcamper_exit_at": 2})
                code, _written, _guide, console = self.walk(via_main=True, **where)
                self.assertEqual(1, code)
                self.assertIn("walk ended abnormally", console)
                # Control: the same stub exiting 0.
                code, _written, _guide, _console = self.walk(via_main=True, code=0, **where)
                self.assertEqual(0, code)


#: 68 turn lines, then a traceback: the shape that defeated `walk.stdout or walk.stderr`.
TURN_LINES = 68
TRACEBACK = (
    "Traceback (most recent call last):\n"
    '  File "walk.py", line 257, in run_walk\n'
    "    result = _claude(args, cwd=project, stdin_text=\"\", timeout=timeout, env=env)\n"
    "subprocess.TimeoutExpired: Command 'claude' timed out after 600 seconds\n")

STUB_WALK_HEAD = '''\
import sys
from pathlib import Path

out = Path(sys.argv[sys.argv.index("--out") + 1])
for turn in range(1, %d + 1):
    print("  turn %%d: 234 chars [asks]" %% turn)
''' % TURN_LINES

STUB_TRANSCRIPT = (
    '{"type": "assistant", "message": {"content": []}}\n'
    '{"type": "walk_stop", "turn": 68, "reason": "the guide timed out after 600s",'
    ' "stop_at_banner": null, "banner_turn": null}\n')


class ACrashedWalkIsBreakingNotACoverageLimit(unittest.TestCase):
    """Half 2: `autotest.py`, driven against a stub `walk.py` on disk.

    Offline and sandboxed: `SKILL_DIR` points at a temporary directory holding three stub
    scripts, `SANDBOX_ROOT` and `REPORT_DIR` point into the same temporary directory, the
    scaffold path is made absent so the sandbox falls back to `mkdir`, and the git worktree
    is replaced. Nothing touches `~/senzing-autotest`, the network or the real repository.
    """

    def setUp(self):
        import shutil
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.skill = self.tmp / "skill"
        self.skill.mkdir()
        for name in ("mcp_probe.py", "transcript_lint.py"):
            (self.skill / name).write_text("print('[]')\n", encoding="utf-8")
        saved = (autotest.SKILL_DIR, autotest.SANDBOX_ROOT, autotest.REPORT_DIR,
                 autotest.SCAFFOLD, autotest.make_worktree, autotest.drop_worktree)

        def restore():
            (autotest.SKILL_DIR, autotest.SANDBOX_ROOT, autotest.REPORT_DIR,
             autotest.SCAFFOLD, autotest.make_worktree,
             autotest.drop_worktree) = saved
        self.addCleanup(restore)
        autotest.SKILL_DIR = self.skill
        autotest.SANDBOX_ROOT = self.tmp / "senzing-autotest"
        autotest.REPORT_DIR = autotest.SANDBOX_ROOT / "reports"
        autotest.SCAFFOLD = self.tmp / "no-such-scaffold.py"
        autotest.make_worktree = lambda root, ref: (root / "plugin-src", "a" * 40)
        autotest.drop_worktree = lambda worktree: None
        self.runs = 0

    def run_autotest(self, exit_code, transcript=True, stderr_text=TRACEBACK):
        """Write the stub walk, run `autotest.main --walk`, return (code, output, report)."""
        body = [STUB_WALK_HEAD]
        if transcript:
            body.append("out.write_text(%r, encoding=\"utf-8\")\n" % STUB_TRANSCRIPT)
        if stderr_text:
            body.append("sys.stderr.write(%r)\n" % stderr_text)
        body.append("sys.exit(%d)\n" % exit_code)
        (self.skill / "walk.py").write_text("".join(body), encoding="utf-8")

        self.runs += 1
        reports = self.tmp / f"reports-{self.runs}"
        printed = io.StringIO()
        with redirect_stdout(printed), redirect_stderr(io.StringIO()):
            code = autotest.main(["--walk", "--report-dir", str(reports)])
        report = json.loads((reports / "latest.json").read_text(encoding="utf-8"))
        return code, printed.getvalue(), report

    @staticmethod
    def _codes(report):
        return [f["code"] for f in report["findings"]]

    def test_a_non_zero_walk_is_breaking_and_the_run_exits_non_zero(self):
        code, printed, report = self.run_autotest(exit_code=1)
        self.assertEqual(1, code)
        self.assertIn("walk-failed", self._codes(report))
        failed = [f for f in report["findings"] if f["code"] == "walk-failed"]
        self.assertEqual(["BREAKING"], [f["severity"] for f in failed])
        self.assertIn("exited 1", failed[0]["message"])
        self.assertIn("TimeoutExpired", failed[0]["message"])
        self.assertIn("[BREAKING] walk-failed", printed)

        # Control: the same stub, the same arguments, exit 0 -- no finding, exit 0.
        code, _printed, report = self.run_autotest(exit_code=0, stderr_text="")
        self.assertEqual(0, code)
        self.assertEqual([], self._codes(report))

    def test_the_walks_stderr_is_printed_although_stdout_was_full(self):
        code, printed, _report = self.run_autotest(exit_code=1)
        self.assertEqual(1, code)
        # The stub really did fill stdout; otherwise the old short-circuit would have
        # reached stderr on its own and this would prove nothing.
        self.assertIn(f"turn {TURN_LINES}: 234 chars", printed)
        self.assertIn("TimeoutExpired: Command 'claude' timed out", printed)

        # Control: a walk that succeeded still shows its stdout and reports nothing.
        code, clean, report = self.run_autotest(exit_code=0, stderr_text="")
        self.assertEqual(0, code)
        self.assertIn(f"turn {TURN_LINES}: 234 chars", clean)
        self.assertEqual([], self._codes(report))

    def test_a_long_child_stderr_reaches_the_console_whole(self):
        """#794: the walk's stderr now carries a child's whole stderr; none of it is cut."""
        long_stderr = LONG_STDERR + "walk ended abnormally: the guide process exited 1\n"
        code, printed, report = self.run_autotest(exit_code=1, stderr_text=long_stderr)
        self.assertEqual(1, code)
        self.assertIn(long_stderr.rstrip(), printed)
        self.assertIn("walk-failed", self._codes(report))
        failed = [f for f in report["findings"] if f["code"] == "walk-failed"]
        self.assertIn("the guide process exited 1", failed[0]["message"])

        # Control: the same stderr from a walk that exited 0 files nothing.
        code, _printed, report = self.run_autotest(exit_code=0, stderr_text=long_stderr)
        self.assertEqual(0, code)
        self.assertEqual([], self._codes(report))

    def test_the_old_short_circuit_cannot_reach_the_traceback(self):
        """Negative control on the stub's own shape, not on the code under test."""
        stdout = "".join(f"  turn {n}: 234 chars [asks]\n"
                         for n in range(1, TURN_LINES + 1))
        self.assertNotIn("TimeoutExpired", stdout.rstrip() or TRACEBACK.rstrip()[:400])

    def test_a_crash_that_left_no_transcript_is_more_than_a_coverage_limit(self):
        code, _printed, report = self.run_autotest(exit_code=1, transcript=False)
        self.assertEqual(1, code)
        limits = [l for l in report["coverage_limits"] if "produced no transcript" in l]
        self.assertEqual(1, len(limits))
        self.assertIn(
            "walk-failed", self._codes(report),
            "the missing transcript was filed as a coverage limit and nothing else, which "
            "is the defect: a crashed walk read as a run that found nothing")

        # Control: no transcript and no crash stays exactly what it was -- a coverage
        # limit, no finding, exit 0.
        code, _printed, report = self.run_autotest(exit_code=0, transcript=False,
                                                   stderr_text="")
        self.assertEqual(0, code)
        self.assertEqual([], report["findings"])
        self.assertTrue(any("produced no transcript" in l
                            for l in report["coverage_limits"]))

    def test_a_partial_transcript_from_a_crashed_walk_is_still_read(self):
        """The turns the walk did complete are linted, not discarded with the walk."""
        code, _printed, report = self.run_autotest(exit_code=1)
        self.assertEqual(1, code)
        self.assertEqual([], [l for l in report["coverage_limits"]
                              if "produced no transcript" in l])
        self.assertTrue(report.get("transcript_path", "").endswith(".transcript.jsonl"))


if __name__ == "__main__":
    unittest.main()
