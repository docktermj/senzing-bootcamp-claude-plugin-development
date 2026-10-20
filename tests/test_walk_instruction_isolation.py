"""A simulated walk runs under the run's instruction files, not the host's (#733).

Enforces **INV-379**, registered by the maintainer 2026-10-20. ⚠️ It **cannot** establish what the live CLI loads, only what the walk asks it to load; that was probed once against a stub Messages API and is recorded in this entry.

A `/dry-run --simulated confused` walk filed 13 BREAKING `INV-251-multi-question` findings
in its graded slice. Every one of them was the maintainer's own `~/.claude/CLAUDE.md`
("end every response with a 👉 **Suggested next step:** line") reaching the bootcamp
process: the first 👉 in each flagged turn was the plugin's question, the second was the
host's rule. The plugin asked exactly one question, and the shipped plugin contains
"Suggested next step" nowhere. MCP servers were isolated and instruction files were not,
which is one step short of the thing phase 3 measures.

`walk.py` now passes `--setting-sources project,local` on every `claude` call it makes, so
the host's user-level instruction files are not loaded, and records what the walk ran under
as the transcript's first event. `autotest.py` turns that event into a `coverage_limits`
line naming every host instruction file the run could still read.

⛔ **Why not `CLAUDE_CONFIG_DIR`, which `--isolate-config` already sets:** the user-level
instruction file is `$CLAUDE_CONFIG_DIR/CLAUDE.md`, so moving that directory takes the
host's credentials with it and the child exits "Not logged in" without `ANTHROPIC_API_KEY`
— and the walk that found this defect ran without one. `--setting-sources` leaves the
config directory alone, which is what makes it usable as a default.

Checks, each negative-controlled where the positive case could otherwise hold vacuously:

1. **Both processes carry the flags.** Every `claude` call a walk makes — the guide's and
   the simulated Bootcamper's — is sent with `--setting-sources project,local`. The
   blocking case is asserted beside it: with the isolation unavailable, no call carries
   them, so the assertion cannot be satisfied by an argv that never had the flag.
2. **The transcript records what the walk ran under**, before its first turn, so a walk
   that dies mid-turn still says it.
3. **A run that could read a host instruction file names it, with its path**, and a run
   that could not discloses nothing. The contaminated case names a real file on disk.
4. **The new event is not a guide turn** to the linter or the slicer.

No phrase-level pattern (#733): every line this file reads one at a time is one JSON event
of a JSONL transcript it wrote itself. A JSON event is not Markdown prose, so there is no
phrase for a wrap-aware collapse to find and nothing a line boundary can split.

Stdlib only, offline, no import from `plugins/` (INV-108).
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

import autotest  # noqa: E402
import module_banners  # noqa: E402
import transcript_lint  # noqa: E402
import walk  # noqa: E402

POINTER = "\U0001f449"
OPENING = "/senzing-bootcamp:start-bootcamp"
FLAGS = ["--setting-sources", "project,local"]


def _assistant(text):
    return json.dumps({"type": "assistant",
                       "message": {"content": [{"type": "text", "text": text}]}})


def _guide_turn(n):
    return f"Turn {n} of the bootcamp. " + "x" * 220 + f"\n{POINTER} What next?"


def is_guide(argv):
    """A guide call asks for stream-json; the Bootcamper call asks for text."""
    return "stream-json" in argv


class WalkFixture(unittest.TestCase):
    """A walk driven with a stub `claude` standing in for both processes."""

    def setUp(self):
        previous = walk._SUPPORTS_SETTING_SOURCES
        self.addCleanup(setattr, walk, "_SUPPORTS_SETTING_SOURCES", previous)

    def walk_it(self, isolated, turns=3, config_dir=None, project=None):
        """Run `turns` turns; return (argvs, events, transcript path, temp root)."""
        walk._SUPPORTS_SETTING_SOURCES = isolated
        argvs, calls = [], []

        def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
            argvs.append(list(args))
            if not is_guide(args):
                return subprocess.CompletedProcess(args, 0, stdout="yes\n", stderr="")
            calls.append(1)
            return subprocess.CompletedProcess(
                args, 0, stdout=_assistant(_guide_turn(len(calls))) + "\n", stderr="")

        root = tempfile.mkdtemp()
        environment = {"CLAUDE_CONFIG_DIR": str(config_dir)} if config_dir else {}
        out = Path(root) / "t.jsonl"
        with mock.patch.object(walk, "_claude", fake_claude), \
                mock.patch.dict("os.environ", environment), \
                redirect_stdout(io.StringIO()), \
                mock.patch("sys.stderr", io.StringIO()):
            walk.run_walk(str(project or root), out, turns, "terse",
                          Path(root) / "mcp.json", None, None, OPENING, False, 5)
        events = [json.loads(line) for line in out.read_text().splitlines() if line]
        return argvs, events, out, Path(root)


class BothProcessesCarryTheFlags(WalkFixture):
    """Check 1."""

    def test_every_claude_call_is_sent_with_the_isolation_flags(self):
        argvs, _, _, _ = self.walk_it(isolated=True)
        self.assertTrue(any(is_guide(argv) for argv in argvs), "no guide call was made")
        self.assertTrue(any(not is_guide(argv) for argv in argvs),
                        "no Bootcamper call was made")
        for argv in argvs:
            with self.subTest(role="guide" if is_guide(argv) else "bootcamper"):
                index = argv.index(FLAGS[0])
                self.assertEqual(argv[index:index + 2], FLAGS)

    def test_without_the_isolation_no_call_carries_them(self):
        """The blocking case: the flags are absent, so check 1 is not vacuous."""
        argvs, _, _, _ = self.walk_it(isolated=False)
        self.assertTrue(argvs)
        for argv in argvs:
            with self.subTest(role="guide" if is_guide(argv) else "bootcamper"):
                self.assertNotIn(FLAGS[0], argv)

    def test_the_isolation_is_probed_from_the_installed_cli(self):
        """`--setting-sources` is taken from the CLI's own help, never assumed."""
        walk._SUPPORTS_SETTING_SOURCES = None
        help_text = "  --setting-sources <sources>  Comma-separated list of sources\n"
        with mock.patch.object(walk.subprocess, "run", return_value=
                               subprocess.CompletedProcess([], 0, stdout=help_text,
                                                           stderr="")):
            self.assertTrue(walk.supports_instruction_isolation())
        walk._SUPPORTS_SETTING_SOURCES = None
        with mock.patch.object(walk.subprocess, "run", return_value=
                               subprocess.CompletedProcess([], 0, stdout="  --model\n",
                                                           stderr="")):
            self.assertFalse(walk.supports_instruction_isolation())
        walk._SUPPORTS_SETTING_SOURCES = None
        with mock.patch.object(walk.subprocess, "run", side_effect=FileNotFoundError):
            self.assertFalse(walk.supports_instruction_isolation())


class TheTranscriptRecordsWhatTheWalkRanUnder(WalkFixture):
    """Check 2."""

    def test_the_first_event_names_the_isolation(self):
        _, events, _, _ = self.walk_it(isolated=True)
        first = events[0]
        self.assertEqual(first["type"], "walk_isolation")
        self.assertIs(first["instructions_isolated"], True)
        self.assertEqual(first["mechanism"], " ".join(FLAGS))
        self.assertEqual(first["host_instruction_files"], [])

    def test_a_walk_that_cannot_isolate_says_so_first(self):
        _, events, _, _ = self.walk_it(isolated=False)
        self.assertEqual(events[0]["type"], "walk_isolation")
        self.assertIs(events[0]["instructions_isolated"], False)
        self.assertIsNone(events[0]["mechanism"])

    def test_the_event_precedes_every_turn(self):
        """A walk that dies mid-turn still says what it ran under."""
        _, events, _, _ = self.walk_it(isolated=True)
        kinds = [event.get("type") for event in events]
        self.assertEqual(kinds[0], "walk_isolation")
        self.assertEqual(kinds.count("walk_isolation"), 1)
        self.assertIn("walk_stop", kinds)


class AContaminatedRunNamesTheFilesItCouldRead(WalkFixture):
    """Check 3."""

    def config_dir_holding_claude_md(self):
        config = Path(tempfile.mkdtemp()) / ".claude"
        config.mkdir()
        instructions = config / "CLAUDE.md"
        instructions.write_text("End every response with a pointer line.\n",
                                encoding="utf-8")
        return config, instructions

    def test_the_user_layer_is_named_with_its_path_when_it_is_not_isolated(self):
        config, instructions = self.config_dir_holding_claude_md()
        _, events, transcript, _ = self.walk_it(isolated=False, config_dir=config)
        self.assertEqual(events[0]["host_instruction_files"], [str(instructions)])
        disclosure = autotest.instruction_disclosure(transcript)
        self.assertIsNotNone(disclosure)
        self.assertIn(str(instructions), disclosure)
        self.assertIn("scored as the plugin's behavior", disclosure)

    def test_the_same_file_is_not_named_once_it_is_isolated(self):
        """The blocking case for check 3: the file exists, and is no longer readable."""
        config, _ = self.config_dir_holding_claude_md()
        _, events, transcript, _ = self.walk_it(isolated=True, config_dir=config)
        self.assertEqual(events[0]["host_instruction_files"], [])
        self.assertIsNone(autotest.instruction_disclosure(transcript))

    def test_an_instruction_file_above_the_project_is_named_even_when_isolated(self):
        """Isolation keeps the project layer, so a file in a parent is still read."""
        root = Path(tempfile.mkdtemp())
        (root / "CLAUDE.md").write_text("Answer in bullet points.\n", encoding="utf-8")
        project = root / "project"
        project.mkdir()
        _, events, transcript, _ = self.walk_it(isolated=True, project=project)
        self.assertEqual(events[0]["host_instruction_files"],
                         [str(root / "CLAUDE.md")])
        self.assertIn(str(root / "CLAUDE.md"),
                      autotest.instruction_disclosure(transcript))

    def test_the_config_directory_is_read_from_the_environment(self):
        config, instructions = self.config_dir_holding_claude_md()
        with mock.patch.dict("os.environ", {"CLAUDE_CONFIG_DIR": str(config)}):
            self.assertEqual(walk.user_config_dir(), config)
            self.assertIn(str(instructions),
                          walk.readable_host_instructions(config.parent, False))
            self.assertNotIn(str(instructions),
                             walk.readable_host_instructions(config.parent, True))

    def test_a_transcript_without_the_event_discloses_nothing(self):
        path = Path(tempfile.mkdtemp()) / "t.jsonl"
        path.write_text(_assistant("hello") + "\n", encoding="utf-8")
        self.assertIsNone(autotest.instruction_disclosure(path))


class TheNewEventIsNotAGuideTurn(WalkFixture):
    """Check 4."""

    def test_the_linter_and_the_slicer_both_skip_it(self):
        _, _, transcript, _ = self.walk_it(isolated=True, turns=3)
        turns = transcript_lint.load(transcript)
        self.assertEqual(len(turns), 3)
        for text in turns:
            self.assertNotIn("walk_isolation", text)
        lines = transcript.read_text(encoding="utf-8").splitlines()
        self.assertEqual(module_banners.visible_text(lines[0]), "")
        self.assertFalse([f for f in transcript_lint.lint(turns)
                          if f["code"] == "INV-251-multi-question"])


if __name__ == "__main__":
    unittest.main()
