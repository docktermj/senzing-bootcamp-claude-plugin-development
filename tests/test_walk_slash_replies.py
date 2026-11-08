"""A Bootcamper reply that starts with `/` reaches the walk's session as typed (#656).

`walk.py` sent every Bootcamper reply as `claude -p <reply>`, and the CLI parses a prompt that
starts with `/` as a slash command. A simulated walk stalled at the first effort gate: the
reply `/effort high` then `yes` ran `/effort` with the argument `high\\n\\nyes`, and the CLI's
"Invalid argument" became the next "turn". `/effort` run under `-p --resume` does not persist
either (checked against CLI 2.1.300 on 2026-10-15), so the maintainer chose sticky flags.

Checks, each driven through `walk.run_walk` with a stub `claude` that records every call's
argv and a scripted Bootcamper; each was negative-controlled when written:

1. **The flag reaches every later turn.** A leading reply line that is exactly
   `/effort <level>` or `/model <name>` becomes `--effort` / `--model` on that turn's
   `claude -p … --resume` call and on every later one, and the latest value wins.
2. **The original text is logged.** The `bootcamper` event holds the reply exactly as the
   Bootcamper process returned it; a `bootcamper_flag` event records each flag; neither
   counts as a turn, and `transcript_lint.load` and `module_banners.slice_transcript` do not
   read the new event as a guide turn.
3. **A path reply is the turn.** A reply that starts with `/` but is not an allowlisted line,
   such as `/data/claims.csv`, is sent with one leading space, the form the CLI does not
   parse, and sets no flag.
4. **A slash-only reply** asks the Bootcamper once more with the guide's same turn, giving
   each line's status (#877); a second slash-only reply stops the walk with its own
   `walk_stop` reason.
5. **The opening** `/senzing-bootcamp:start-bootcamp` is still sent unchanged at turn 1.
6. **The brief** tells the Bootcamper to put a slash command on its own line, first.
7. **A bare line** (#877): a leading line that is exactly `/model` or `/effort` is a slash
   line with no value. It never reaches the guide as text, sets no flag, and is logged as
   `bootcamper_flag_ignored` with `value: null` and `reason: "no value"`; the valued lines
   around it behave as check 1 says. A slash-only reply is re-asked with one status per line,
   in order (`— applied`, `— not applied (no value)`), and a second one still stops the walk.

⚠️ **What this does NOT establish:** that the live CLI still applies `--effort` and `--model`
on a resumed call, or still sends a space-led prompt as text. Both were probed once, against
a local stub Messages API with scratch `HOME` and `CLAUDE_CONFIG_DIR` (no credentials, no
model call), and are recorded in the #656 ledger entry; a CLI release can change either.

Stdlib only, offline (INV-108).
"""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
AUTO_TEST = REPO_ROOT / ".claude" / "skills" / "auto-test"
DRY_RUN = REPO_ROOT / ".claude" / "skills" / "dry-run"

sys.path.insert(0, str(AUTO_TEST))
sys.path.insert(0, str(DRY_RUN))

import module_banners  # noqa: E402
import transcript_lint  # noqa: E402
import walk  # noqa: E402

POINTER = "\U0001f449"
OPENING = "/senzing-bootcamp:start-bootcamp"


def _assistant(text):
    return json.dumps({"type": "assistant",
                       "message": {"content": [{"type": "text", "text": text}]}})


def _guide_turn(n):
    return f"Turn {n} of the bootcamp. " + "x" * 220 + f"\n{POINTER} What next?"


def run(replies, turns=3, model=None):
    """Walk ``turns`` turns with a scripted Bootcamper; return (argvs, prompts, events)."""
    argvs, prompts, script = [], [], list(replies)

    def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
        argvs.append(list(args))
        return subprocess.CompletedProcess(args, 0, stdout=_assistant(
            _guide_turn(len(argvs))) + "\n", stderr="")

    def fake_reply(prompt_text, persona, model, cwd=None, timeout=180):
        prompts.append(prompt_text)
        return script.pop(0) if script else "ok"

    with tempfile.TemporaryDirectory() as tmp, \
            mock.patch.object(walk, "_claude", fake_claude), \
            mock.patch.object(walk, "bootcamper_reply", fake_reply), \
            redirect_stdout(io.StringIO()), \
            mock.patch("sys.stderr", io.StringIO()):
        out = Path(tmp) / "t.jsonl"
        # A project directory of its own: the Bootcamper's cwd is made beside it (#834).
        project = Path(tmp) / "project"
        project.mkdir()
        walk.run_walk(project, out, turns, "terse", Path(tmp) / "mcp.json", model, None,
                      OPENING, False, 5)
        events = [json.loads(line) for line in out.read_text().splitlines() if line]
    return argvs, prompts, events


def flag_values(argv, flag):
    return [argv[i + 1] for i, a in enumerate(argv) if a == flag]


def of_type(events, kind):
    return [e for e in events if e.get("type") == kind]


class TheFlagReachesEveryLaterTurn(unittest.TestCase):
    """Check 1."""

    def test_effort_high_then_yes_advances_with_the_flag(self):
        argvs, _, events = run(["/effort high\n\nyes", "1", "2"], turns=4)
        self.assertEqual(len(argvs), 4)
        self.assertEqual(events[-1]["reason"], "--turns 4 reached")
        self.assertEqual(flag_values(argvs[0], "--effort"), [])
        self.assertEqual(argvs[1][:2], ["-p", "yes"])
        for argv in argvs[1:]:
            with self.subTest(argv=argv[:2]):
                self.assertEqual(flag_values(argv, "--effort"), ["high"])
                self.assertIn("--resume", argv)

    def test_the_latest_value_wins_and_replaces_the_model(self):
        argvs, _, _ = run(["/effort high\nyes",
                           "/effort low\n/model claude-sonnet-4-5\nok", "x"],
                          turns=4, model="claude-opus-5-5")
        self.assertEqual(flag_values(argvs[0], "--model"), ["claude-opus-5-5"])
        self.assertEqual(flag_values(argvs[1], "--effort"), ["high"])
        self.assertEqual(flag_values(argvs[1], "--model"), ["claude-opus-5-5"])
        for argv in argvs[2:]:
            with self.subTest(argv=argv[:2]):
                self.assertEqual(flag_values(argv, "--effort"), ["low"])
                self.assertEqual(flag_values(argv, "--model"), ["claude-sonnet-4-5"])
        self.assertEqual(argvs[2][:2], ["-p", "ok"])

    def test_only_an_exact_leading_line_is_a_flag(self):
        cases = {
            "/effort high\n\nyes": ([("/effort high", "--effort", "high")], "yes"),
            "  /model claude-sonnet-4-5  \n/effort max\nok":
                ([("/model claude-sonnet-4-5", "--model", "claude-sonnet-4-5"),
                  ("/effort max", "--effort", "max")], "ok"),
            "/effort high": ([("/effort high", "--effort", "high")], ""),
            "yes\n/effort high": ([], "yes\n/effort high"),
            "/effort": ([("/effort", "--effort", None)], ""),
            "/effort very high\nyes": ([], "/effort very high\nyes"),
            "/effortless yes": ([], "/effortless yes"),
            "/help me": ([], "/help me"),
        }
        for reply, expected in cases.items():
            with self.subTest(reply=reply):
                self.assertEqual(walk.split_reply(reply), expected)
        self.assertEqual(set(walk.SLASH_FLAGS), {"/effort", "/model"})


class TheOriginalTextIsLogged(unittest.TestCase):
    """Check 2."""

    def test_the_bootcamper_event_keeps_the_slash_line(self):
        _, _, events = run(["/effort high\n\nyes"], turns=2)
        said = of_type(events, "bootcamper")
        self.assertEqual(said[0]["text"], "/effort high\n\nyes")
        self.assertEqual(of_type(events, "bootcamper_flag"), [
            {"type": "bootcamper_flag", "turn": 1, "command": "/effort high",
             "flag": "--effort", "value": "high"}])

    def test_the_flag_event_is_not_a_guide_turn(self):
        _, _, events = run(["/effort high\n\nyes", "1"], turns=3)
        lines = [json.dumps(e) for e in events]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertEqual(len(transcript_lint.load(path)), 3)
        _, summary = module_banners.slice_transcript(lines, 1)
        self.assertEqual(summary["walk_stop"]["reason"], "--turns 3 reached")
        self.assertEqual(len(of_type(events, "assistant")), 3)


class APathReplyIsTheTurn(unittest.TestCase):
    """Check 3."""

    def test_a_path_is_sent_with_a_leading_space(self):
        argvs, _, events = run(["/data/claims.csv", "1"], turns=3)
        self.assertEqual(len(argvs), 3)
        self.assertEqual(argvs[1][:2], ["-p", " /data/claims.csv"])
        for argv in argvs:
            self.assertEqual(flag_values(argv, "--effort"), [])
        self.assertEqual(of_type(events, "bootcamper_flag"), [])
        self.assertEqual(of_type(events, "bootcamper")[0]["text"], "/data/claims.csv")

    def test_a_non_allowlisted_command_is_text_too(self):
        argvs, _, _ = run(["/help me pick"], turns=2)
        self.assertEqual(argvs[1][:2], ["-p", " /help me pick"])

    def test_the_rest_after_a_flag_is_protected_as_well(self):
        argvs, _, _ = run(["/effort high\n/data/claims.csv"], turns=2)
        self.assertEqual(argvs[1][:2], ["-p", " /data/claims.csv"])
        self.assertEqual(flag_values(argvs[1], "--effort"), ["high"])

    def test_ordinary_text_is_unchanged(self):
        self.assertEqual(walk.as_turn("yes /effort"), "yes /effort")
        self.assertEqual(walk.as_turn("/x"), " /x")


class ASlashOnlyReplyAsksAgain(unittest.TestCase):
    """Check 4."""

    def test_it_asks_once_more_with_the_same_turn(self):
        argvs, prompts, events = run(["/effort high", "yes"], turns=2)
        self.assertEqual(len(argvs), 2)
        # Two asks for turn 1, then turn 2's (the walk asks before it checks --turns).
        self.assertEqual(len(prompts), 3)
        self.assertTrue(prompts[1].startswith(prompts[0]))
        self.assertIn("/effort high", prompts[1][len(prompts[0]):])
        self.assertEqual(argvs[1][:2], ["-p", "yes"])
        self.assertEqual(flag_values(argvs[1], "--effort"), ["high"])
        self.assertEqual([e["text"] for e in of_type(events, "bootcamper")][:2],
                         ["/effort high", "yes"])
        self.assertEqual(events[-1]["reason"], "--turns 2 reached")

    def test_a_second_slash_only_reply_stops_the_walk(self):
        argvs, prompts, events = run(["/effort high", "/model claude-sonnet-4-5"], turns=3)
        self.assertEqual(len(argvs), 1)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(events[-1]["type"], "walk_stop")
        self.assertEqual(events[-1]["reason"], "the Bootcamper replied only with slash commands")
        self.assertEqual([e["flag"] for e in of_type(events, "bootcamper_flag")],
                         ["--effort", "--model"])


class ABareLineIsRecognizedAndSetsNothing(unittest.TestCase):
    """Check 7 (#877)."""

    def test_a_bare_line_is_a_slash_line_with_no_value(self):
        cases = {
            "/model": ([("/model", "--model", None)], ""),
            "  /effort  \n\nyes": ([("/effort", "--effort", None)], "yes"),
            "/model\n/effort high\nok": ([("/model", "--model", None),
                                          ("/effort high", "--effort", "high")], "ok"),
            # Not exact: each is text, as before.
            "/models": ([], "/models"),
            "/model claude opus": ([], "/model claude opus"),
            "/model claude opus\nyes": ([], "/model claude opus\nyes"),
            "/effortless": ([], "/effortless"),
            "/help": ([], "/help"),
        }
        for reply, expected in cases.items():
            with self.subTest(reply=reply):
                self.assertEqual(walk.split_reply(reply), expected)

    def test_bare_lines_never_reach_the_guide_and_set_no_flag(self):
        argvs, _, events = run(["/model\n/effort\nyes"], turns=2, model="claude-opus-5-5")
        self.assertEqual(argvs[1][:2], ["-p", "yes"])
        for argv in argvs:
            with self.subTest(argv=argv[:2]):
                self.assertEqual(flag_values(argv, "--model"), ["claude-opus-5-5"])
                self.assertEqual(flag_values(argv, "--effort"), [])
        self.assertEqual(of_type(events, "bootcamper_flag"), [])
        self.assertEqual(of_type(events, "bootcamper_flag_ignored"), [
            {"type": "bootcamper_flag_ignored", "turn": 1, "command": "/model",
             "flag": "--model", "value": None, "reason": "no value"},
            {"type": "bootcamper_flag_ignored", "turn": 1, "command": "/effort",
             "flag": "--effort", "value": None, "reason": "no value"}])

    def test_the_value_is_null_in_the_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "t.jsonl"
            project = Path(tmp) / "project"
            project.mkdir()
            script = ["/effort\nyes"]

            def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
                return subprocess.CompletedProcess(args, 0, stdout=_assistant(
                    _guide_turn(1)) + "\n", stderr="")

            with mock.patch.object(walk, "_claude", fake_claude), \
                    mock.patch.object(walk, "bootcamper_reply",
                                      lambda *a, **k: script.pop(0) if script else "ok"), \
                    redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                walk.run_walk(project, out, 2, "terse", Path(tmp) / "mcp.json", None, None,
                              OPENING, False, 5)
            raw = [line for line in out.read_text().splitlines()
                   if '"bootcamper_flag_ignored"' in line]
        self.assertEqual(len(raw), 1)
        self.assertIn('"value": null', raw[0])
        self.assertIn('"reason": "no value"', raw[0])

    def test_a_bare_line_among_valued_lines_leaves_them_applied(self):
        argvs, _, events = run(["/model claude-sonnet-4-5\n/effort\n/effort low\nyes"],
                               turns=2, model="claude-opus-5-5")
        self.assertEqual(argvs[1][:2], ["-p", "yes"])
        self.assertEqual(flag_values(argvs[1], "--model"), ["claude-sonnet-4-5"])
        self.assertEqual(flag_values(argvs[1], "--effort"), ["low"])
        self.assertEqual([e["command"] for e in of_type(events, "bootcamper_flag")],
                         ["/model claude-sonnet-4-5", "/effort low"])
        self.assertEqual([(e["command"], e["reason"])
                          for e in of_type(events, "bootcamper_flag_ignored")],
                         [("/effort", "no value")])

    def test_the_re_ask_gives_one_status_per_line_in_order(self):
        argvs, prompts, _ = run(["/model opus\n/effort", "yes"], turns=2)
        added = prompts[1][len(prompts[0]):]
        self.assertIn("/model opus — applied\n/effort — not applied (no value)\n", added)
        self.assertNotIn("It is applied", added)
        self.assertNotIn("It is not applied", added)
        self.assertEqual(argvs[1][:2], ["-p", "yes"])
        self.assertEqual(flag_values(argvs[1], "--model"), ["opus"])

    def test_a_bare_only_reply_is_asked_again_not_sent(self):
        argvs, prompts, _ = run(["/effort", "yes"], turns=2)
        self.assertEqual(len(argvs), 2)
        self.assertIn("/effort — not applied (no value)", prompts[1][len(prompts[0]):])
        self.assertEqual(argvs[1][:2], ["-p", "yes"])

    def test_a_second_slash_only_reply_still_stops_the_walk(self):
        argvs, prompts, events = run(["/effort", "/model"], turns=3)
        self.assertEqual(len(argvs), 1)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(events[-1]["reason"], "the Bootcamper replied only with slash commands")


class TheOpeningIsUnchanged(unittest.TestCase):
    """Check 5."""

    def test_turn_one_sends_the_opening_as_given(self):
        argvs, _, _ = run(["/data/claims.csv"], turns=2)
        self.assertEqual(argvs[0][:2], ["-p", OPENING])
        self.assertIn("--session-id", argvs[0])


class TheBriefPutsTheCommandFirst(unittest.TestCase):
    """Check 6."""

    def test_the_brief_carries_the_rule(self):
        brief = " ".join(walk.BOOTCAMPER_BRIEF.split())
        self.assertIn("If you type a slash command such as /effort or /model, put it on its "
                      "own line, before your answer.", brief)


if __name__ == "__main__":
    unittest.main()
