"""An auto-test walk can start mid-bootcamp and hold the guide's model and effort (#870).

A walk meant to judge #855 on Modules 5 to 7 started at Bootcamp preparation, and the
simulated Bootcamper followed the guide's model/effort nudge with `/model opus` and
`/effort high`, which `walk.py` applies from then on (#656). So:

1. **`--seed mid`** builds the project with `scaffold_project.py`'s mid-bootcamp mode, which
   takes no mode flag, and the lint then defaults to `--phase content`; an explicit `--phase`
   still wins.
2. **`--effort <level>`** goes on every guide call from the first, as `--model` does.
3. **`--pin`** holds `--model` and `--effort` for the whole walk: a Bootcamper `/model` or
   `/effort` line is logged as `bootcamper_flag_ignored` and changes no flag, and
   `autotest.py` reports each as an INFO `bootcamper-flag-ignored` finding.
4. **Without `--pin`** a Bootcamper slash line still overrides both, as #656 made it.

Each check was negative-controlled when written: reverting the change it guards fails it.

⚠️ **What this does NOT establish:** that a live walk with `--seed mid` actually resumes at
Module 5, or that the CLI honors `--effort` on a resumed call. Both need a live walk; the
stubs here only show what the harness sends.

Stdlib only, offline (INV-108).
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


def _assistant(text):
    return json.dumps({"type": "assistant",
                       "message": {"content": [{"type": "text", "text": text}]}})


def run(replies, turns=3, model=None, effort=None, pin=False):
    """Walk with a stub guide and a scripted Bootcamper; return (argvs, prompts, events)."""
    argvs, prompts, script = [], [], list(replies)

    def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
        argvs.append(list(args))
        text = f"Turn {len(argvs)}. " + "x" * 220 + f"\n{POINTER} What next?"
        return subprocess.CompletedProcess(args, 0, stdout=_assistant(text) + "\n", stderr="")

    def fake_reply(prompt_text, persona, model, cwd=None, timeout=180):
        prompts.append(prompt_text)
        return script.pop(0) if script else "ok"

    with tempfile.TemporaryDirectory() as tmp, \
            mock.patch.object(walk, "_claude", fake_claude), \
            mock.patch.object(walk, "bootcamper_reply", fake_reply), \
            redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        out = Path(tmp) / "t.jsonl"
        project = Path(tmp) / "project"
        project.mkdir()
        walk.run_walk(project, out, turns, "terse", Path(tmp) / "mcp.json", model, None,
                      "/senzing-bootcamp:start-bootcamp", False, 5, effort=effort, pin=pin)
        # No phrase-level pattern (#870): each line read is one JSON transcript event.
        events = [json.loads(line) for line in out.read_text().splitlines() if line]
    return argvs, prompts, events


def values(argv, flag):
    return [argv[i + 1] for i, a in enumerate(argv) if a == flag]


def of_type(events, kind):
    return [e for e in events if e.get("type") == kind]


class EffortIsSentFromTheFirstTurn(unittest.TestCase):
    def test_every_call_carries_the_effort(self):
        argvs, _, _ = run(["yes", "ok"], turns=3, effort="low")
        self.assertEqual(len(argvs), 3)
        for argv in argvs:
            self.assertEqual(values(argv, "--effort"), ["low"])

    def test_no_effort_sends_none(self):
        argvs, _, _ = run(["yes"], turns=2)
        for argv in argvs:
            self.assertEqual(values(argv, "--effort"), [])


class PinHoldsModelAndEffort(unittest.TestCase):
    REPLIES = ["/model claude-opus-5-5\n/effort high\nyes", "ok"]

    def test_a_pinned_walk_never_changes_a_flag(self):
        argvs, _, events = run(self.REPLIES, turns=3, model="claude-haiku-5-5",
                               effort="low", pin=True)
        self.assertEqual(len(argvs), 3)
        for argv in argvs:
            self.assertEqual(values(argv, "--model"), ["claude-haiku-5-5"])
            self.assertEqual(values(argv, "--effort"), ["low"])
        self.assertEqual(argvs[1][:2], ["-p", "yes"])
        self.assertEqual(of_type(events, "bootcamper_flag"), [])
        self.assertEqual(
            [(e["turn"], e["command"]) for e in of_type(events, "bootcamper_flag_ignored")],
            [(1, "/model claude-opus-5-5"), (1, "/effort high")])

    def test_pin_without_values_still_ignores_the_lines(self):
        argvs, _, events = run(self.REPLIES, turns=2, pin=True)
        for argv in argvs:
            self.assertEqual(values(argv, "--model") + values(argv, "--effort"), [])
        self.assertEqual(len(of_type(events, "bootcamper_flag_ignored")), 2)

    def test_a_slash_only_reply_is_asked_again_and_told_it_was_not_applied(self):
        argvs, prompts, _ = run(["/effort high", "yes"], turns=2, effort="low", pin=True)
        self.assertEqual(argvs[1][:2], ["-p", "yes"])
        self.assertIn("It is not applied", prompts[1])
        self.assertEqual(values(argvs[1], "--effort"), ["low"])

    def test_without_pin_the_bootcamper_still_overrides(self):
        argvs, prompts, events = run(self.REPLIES, turns=3, model="claude-haiku-5-5",
                                     effort="low")
        self.assertEqual(values(argvs[1], "--model"), ["claude-opus-5-5"])
        self.assertEqual(values(argvs[1], "--effort"), ["high"])
        self.assertEqual(of_type(events, "bootcamper_flag_ignored"), [])
        self.assertEqual(len(of_type(events, "bootcamper_flag")), 2)


class AutotestPassesItThrough(unittest.TestCase):
    """`autotest.main` with `_run` stubbed: no worktree, no probe, no walk run."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.calls = []
        self.transcript_lines = ['{"turn": 1}']
        for name, value in (("_run", self.fake_run),
                            ("SANDBOX_ROOT", self.tmp / "senzing-autotest"),
                            ("REPORT_DIR", self.tmp / "reports")):
            patcher = mock.patch.object(autotest, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_run(self, cmd, **kw):
        cmd = [str(c) for c in cmd]
        self.calls.append(cmd)
        if cmd[:1] == ["git"]:
            return subprocess.CompletedProcess(cmd, 1, "", "no worktree offline")
        if cmd[1].endswith("walk.py"):
            Path(cmd[cmd.index("--out") + 1]).write_text(
                "\n".join(self.transcript_lines) + "\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "[]", "")

    def main(self, *argv):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            autotest.main(["--walk", "--json", *argv])
        report = sorted((self.tmp / "reports").glob("2*.json"))
        return json.loads([p for p in report if "transcript" not in p.name][-1].read_text())

    def call(self, script):
        return next(c for c in self.calls if c[1].endswith(script))

    def test_seed_mid_runs_the_scaffold_without_a_mode_flag_and_lints_content(self):
        self.main("--seed", "mid")
        scaffold = self.call("scaffold_project.py")
        self.assertFalse({"--fresh", "--seeded", "--mid"} & set(scaffold), scaffold)
        self.assertEqual(values(self.call("transcript_lint.py"), "--phase"), ["content"])

    def test_an_explicit_phase_wins(self):
        self.main("--seed", "mid", "--phase", "module0")
        self.assertEqual(values(self.call("transcript_lint.py"), "--phase"), ["module0"])

    def test_the_default_seed_is_unchanged(self):
        self.main()
        self.assertIn("--fresh", self.call("scaffold_project.py"))
        self.assertEqual(values(self.call("transcript_lint.py"), "--phase"), ["preparation"])

    def test_effort_and_pin_reach_the_walk(self):
        self.main("--effort", "low", "--pin")
        argv = self.call("walk.py")
        self.assertEqual(values(argv, "--effort"), ["low"])
        self.assertIn("--pin", argv)

    def test_neither_is_sent_by_default(self):
        self.main()
        argv = self.call("walk.py")
        self.assertNotIn("--effort", argv)
        self.assertNotIn("--pin", argv)

    def test_each_ignored_line_is_an_info_finding(self):
        self.transcript_lines = [json.dumps({"type": "bootcamper_flag_ignored", "turn": 4,
                                             "command": "/model claude-opus-5-5",
                                             "flag": "--model",
                                             "value": "claude-opus-5-5"}),
                                 "not json"]
        found = [f for f in self.main("--pin")["findings"]
                 if f["code"] == "bootcamper-flag-ignored"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["severity"], "INFO")
        self.assertIn("turn 4", found[0]["message"])
        self.assertIn("/model claude-opus-5-5", found[0]["message"])

    def test_an_unreadable_transcript_gives_no_finding(self):
        self.assertEqual(autotest.ignored_flag_findings(self.tmp / "missing.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
