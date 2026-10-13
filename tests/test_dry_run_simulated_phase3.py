"""`/dry-run` phase 3 can run with a simulated Bootcamper, and self-play stays forbidden (#571).

Phase 3 could run only while the maintainer answered every Bootcamper question. `/auto-test`'s
`walk.py` already answers from a second OS process that has never seen the plugin, which is
not self-play, but the no-fabrication rule excluded it by omission. #571 rewords the rule,
adds `--simulated [persona]` to phase 3, and gives the walk a stop condition: the chosen
module's start banner plus `--turns`, capped by `--max-turns` (default 150).

Checks, each negative-controlled when written (#571):

1. **The reworded rule**, at both sites (`dry-run/SKILL.md`'s Absolute rules and
   `phase3-conversational.md`): answering as the Bootcamper inside the session that runs or
   grades the bootcamp is still forbidden, the two-process walk is named as not self-play, and
   this session never adds an answer to it. The fast-forward bullet keeps the rule.
2. **The reporting line**: a clean simulated run is "no regression detected (simulated
   Bootcamper, persona `<p>`)", never "phase 3 passed", with the maintainer's phase 3 listed
   as not yet done.
3. **The default**: the maintainer-answered walk is the default, and an empty argument asks
   who answers along with the other two questions (INV-333).
4. **The banners come from the skill files.** `module_banners.py` finds one for every module
   in Bootcamp preparation's table, a content module's is `MODULE: <its table name>`, and no
   banner text is written into the helper.
5. **The stop condition, offline.** `walk.run_walk` is driven with its two `claude` calls
   stubbed, so no token is spent: it stops `--turns` turns after the banner, at `--max-turns`
   when no banner shows, and after `--turns` turns with no banner given, as before. Each run
   ends on a `walk_stop` event naming the reason.
6. **The slice**: `module_banners.py slice` starts at the chosen module's banner, starts at the
   first turn for Bootcamp preparation, ends an exempt module at the next banner, and exits 3,
   naming the module reached, when the walk never showed the start banner.

⚠️ **What this does NOT establish:** that a live walk reaches a module, that a live session
asks the three questions, or that it never answers for the Bootcamper. Those are properties of
a real run. This pins what the instructions say and what the stop and slice code does.

Stdlib only, offline (INV-108).
"""
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
DRY_RUN = REPO_ROOT / ".claude" / "skills" / "dry-run"
AUTO_TEST = REPO_ROOT / ".claude" / "skills" / "auto-test"
SKILL = DRY_RUN / "SKILL.md"
PHASE3 = DRY_RUN / "phase3-conversational.md"
HELPER = DRY_RUN / "module_banners.py"

sys.path.insert(0, str(AUTO_TEST))
sys.path.insert(0, str(DRY_RUN))

import module_banners  # noqa: E402
import walk  # noqa: E402

POINTER = "\U0001f449"


def squash(text):
    return " ".join(text.split())


def read(path):
    return squash(path.read_text(encoding="utf-8"))


class TheRewordedRuleForbidsSelfPlay(unittest.TestCase):
    """Check 1: the rule is reworded, not relaxed, at every site #571 names."""

    def test_the_skill_forbids_answering_inside_the_session(self):
        body = read(SKILL)
        for pat in (r"⛔ \*\*Never answer as the Bootcamper in the session that runs or grades "
                    r"the bootcamp\.\*\* That is self-play",
                    r"\*\*A simulated walk \(`--simulated`\) is not self-play and not "
                    r"fabrication:\*\* a separate process that has never seen the plugin answers",
                    r"the process running the bootcamp is never told it is under test",
                    r"This session never writes, edits or adds an answer to that walk\.",
                    r"If the maintainer is unavailable and no simulated walk was chosen, say "
                    r"phase 3 is untested"):
            self.assertRegex(body, pat)
        self.assertNotIn("Never fabricate a Bootcamper answer.", body,
                         "the old wording excluded the two-process walk by omission")

    def test_the_phase3_file_distinguishes_the_two(self):
        body = read(PHASE3)
        for pat in (r"⛔ \*\*Self-play is answering as the Bootcamper inside the session that "
                    r"runs or grades the bootcamp, and it stays forbidden\.\*\* A simulated "
                    r"walk is not self-play",
                    r"a second one that has never seen the plugin, and the bootcamp process "
                    r"is never told it is under test",
                    r"This session never writes, edits or adds an answer to that walk\.",
                    r"If the maintainer is not available and no simulated walk was chosen, "
                    r"report phase 3 as \*\*untested\*\*"):
            self.assertRegex(body, pat)

    def test_the_fast_forward_keeps_the_rule(self):
        self.assertRegex(read(PHASE3),
                         r"⛔ \*\*The rule above is not relaxed here:\*\* this session never "
                         r"answers for the Bootcamper, not even to hurry the fast-forward\.")

    def test_no_site_lets_the_session_answer(self):
        for path in (SKILL, PHASE3):
            body = read(path)
            for bad in (r"this session (?:may|can) answer", r"answer on the Bootcamper's behalf",
                        r"fill in (?:the|an) answer"):
                self.assertNotRegex(body, bad, f"{path.name} lets the session answer")


class ACleanSimulatedRunIsNotAPass(unittest.TestCase):
    """Check 2: the reporting line, in the skill's Reporting and the phase 3 procedure."""

    LINE = r'"no regression detected \(simulated Bootcamper, persona `<p>`\)"'

    def test_the_skill_reports_it(self):
        self.assertRegex(read(SKILL),
                         r"a clean run reads " + self.LINE + r"\*\*, never \"phase 3 passed\" "
                         r"or \"the bootcamp works\", and the report lists phase 3 with the "
                         r"maintainer as not yet done\.")

    def test_the_phase3_file_reports_it(self):
        body = read(PHASE3)
        self.assertRegex(body, r"⛔ \*\*A clean simulated walk is reported only as "
                         + self.LINE + r"\*\*, never as \"phase 3 passed\"")
        self.assertRegex(body, r"The report still lists phase 3 with the maintainer as not "
                               r"yet done")

    def test_a_stall_is_reported_never_extrapolated(self):
        self.assertRegex(read(PHASE3), r"Exit 3 means the walk stopped before the start "
                                       r"module:\*\* report the module it reached and leave "
                                       r"the rest untested\. Never extrapolate\.")


class TheHumanWalkIsTheDefault(unittest.TestCase):
    """Check 3: an empty argument asks who answers; the maintainer is the default."""

    def test_the_third_question_is_asked(self):
        body = read(SKILL)
        for pat in (r"⛔ \*\*\(INV-333\) Then a third: who answers as the Bootcamper\.\*\* "
                    r"The maintainer-answered walk is the default",
                    r"a phase-3 argument without it answers it as the maintainer",
                    r"With no argument every question is asked: whether to run phase 3, the "
                    r"start module, and who answers; nothing is assumed\."):
            self.assertRegex(body, pat)

    def test_the_argument_hint_names_the_option(self):
        hint = re.search(r"^argument-hint: (.+)$", SKILL.read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(hint)
        self.assertIn("[--simulated [persona]]", hint.group(1))

    def test_the_max_turns_default_is_150(self):
        for path in (AUTO_TEST / "walk.py", AUTO_TEST / "autotest.py"):
            self.assertRegex(path.read_text(encoding="utf-8"),
                             r'"--max-turns", type=int, default=150',
                             f"{path.name} must cap a walk at 150 turns by default")


class BannersComeFromTheSkillFiles(unittest.TestCase):
    """Check 4: one banner per module, read from that module's files."""

    def setUp(self):
        self.modules = module_banners.modules()

    def test_every_module_in_the_table_has_a_banner(self):
        self.assertEqual(len(self.modules), 11, "the table parser lost a row")
        for entry in self.modules:
            self.assertTrue(entry["banner"], f"{entry['name']}: no banner in its skill files")

    def test_a_content_modules_banner_is_its_table_name(self):
        for entry in self.modules:
            if entry["lint_phase"] == "content":
                self.assertEqual(entry["banner"], "MODULE: " + entry["name"].upper(),
                                 f"{entry['name']}: banner and table name disagree")

    def test_the_setup_stages_keep_their_own_banners(self):
        by_token = {e["token"]: e for e in self.modules}
        self.assertEqual(by_token["bootcamp_preparation"]["lint_phase"], "preparation")
        self.assertEqual(by_token["entity_resolution_concepts"]["lint_phase"], "module0")
        self.assertIsNone(by_token["graduation"]["lint_phase"])
        for token in ("bootcamp_preparation", "entity_resolution_concepts", "graduation"):
            self.assertFalse(by_token[token]["banner"].startswith("MODULE:"))

    def test_no_banner_is_hard_coded(self):
        source = HELPER.read_text(encoding="utf-8")
        for entry in self.modules:
            self.assertNotIn(entry["banner"], source,
                             f"{entry['banner']!r} is written into the helper")

    def test_the_banner_command_prints_it(self):
        out = subprocess.run([sys.executable, str(HELPER), "banner", "4"],
                             capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(out, self.modules[3]["banner"])


def _assistant(text):
    return json.dumps({"type": "assistant",
                       "message": {"content": [{"type": "text", "text": text}]}})


def _turn_text(turn, banner_at, banner):
    body = f"Turn {turn} of the bootcamp. " + "x" * 220
    if turn == banner_at:
        body = f"━━━\n🚀🚀🚀  {banner}  🚀🚀🚀\n━━━\n" + body
    return body + f"\n{POINTER} What would you like to do next?"


class TheWalkStopsOffline(unittest.TestCase):
    """Check 5: the stop condition, with both `claude` calls stubbed; no token is spent."""

    BANNER = "MODULE: SDK SETUP"

    def walk(self, turns, max_turns=150, banner_at=None, stop_at_banner=None):
        calls = []

        def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
            calls.append(args)
            text = _turn_text(len(calls), banner_at, self.BANNER)
            return subprocess.CompletedProcess(args, 0, stdout=_assistant(text) + "\n",
                                               stderr="")

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(walk, "_claude", fake_claude), \
                mock.patch.object(walk, "bootcamper_reply", lambda *a, **k: "1"), \
                redirect_stdout(io.StringIO()):
            out = Path(tmp) / "t.jsonl"
            walk.run_walk(tmp, out, turns, "terse", Path(tmp) / "mcp.json", None, None,
                          "/senzing-bootcamp:start-bootcamp", False, 5,
                          max_turns=max_turns, stop_at_banner=stop_at_banner)
            events = [json.loads(line) for line in out.read_text().splitlines() if line]
        return len(calls), events[-1]

    def test_it_stops_turns_after_the_banner(self):
        count, stop = self.walk(turns=2, banner_at=3, stop_at_banner=self.BANNER)
        self.assertEqual(count, 5)
        self.assertEqual(stop["type"], "walk_stop")
        self.assertEqual(stop["banner_turn"], 3)
        self.assertEqual(stop["turn"], 5)
        self.assertIn("start banner at turn 3", stop["reason"])

    def test_the_banner_matches_regardless_of_case(self):
        count, stop = self.walk(turns=1, banner_at=2, stop_at_banner="module: sdk setup")
        self.assertEqual((count, stop["banner_turn"]), (3, 2))

    def test_it_stops_at_max_turns_when_no_banner_shows(self):
        count, stop = self.walk(turns=2, max_turns=4, stop_at_banner=self.BANNER)
        self.assertEqual(count, 4)
        self.assertIsNone(stop["banner_turn"])
        self.assertEqual(stop["reason"], "--max-turns 4 reached")

    def test_max_turns_caps_the_turns_after_the_banner(self):
        count, stop = self.walk(turns=10, max_turns=6, banner_at=2, stop_at_banner=self.BANNER)
        self.assertEqual(count, 6)
        self.assertEqual(stop["reason"], "--max-turns 6 reached")

    def test_without_a_banner_it_walks_turns_as_before(self):
        count, stop = self.walk(turns=3)
        self.assertEqual(count, 3)
        self.assertEqual(stop["reason"], "--turns 3 reached")

    def test_main_defaults_max_turns_to_150(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(walk, "run_walk", return_value=0) as run, \
                redirect_stdout(io.StringIO()):
            walk.main(["--project", tmp, "--out", str(Path(tmp) / "t.jsonl"),
                       "--mcp-config", str(Path(tmp) / "m.json")])
        self.assertEqual(run.call_args.kwargs, {"max_turns": 150, "stop_at_banner": None})

    def test_the_forbidden_tools_stay_blocked_by_flag(self):
        self.assertEqual(walk.FORBIDDEN_TOOLS, ("mcp__senzing__submit_feedback",
                                                "mcp__senzing__download_resource"))


class TheSliceStartsAtTheChosenModule(unittest.TestCase):
    """Check 6: the analysis slice of a fake transcript."""

    def setUp(self):
        self.banner = {e["number"]: e["banner"] for e in module_banners.modules()}

    def transcript(self, *numbers):
        lines = [_assistant("Welcome to the bootcamp. " + POINTER + " Any questions?"),
                 json.dumps({"type": "bootcamper", "turn": 1, "text": "no"})]
        for n in numbers:
            lines.append(_assistant(f"🚀🚀🚀  {self.banner[n]}  🚀🚀🚀\n{POINTER} Ready?"))
            lines.append(json.dumps({"type": "bootcamper", "turn": n, "text": "yes"}))
        lines.append(json.dumps({"type": "walk_stop", "turn": 9, "reason": "--turns 12 reached",
                                 "stop_at_banner": None, "banner_turn": None}))
        return lines

    def test_a_content_module_starts_at_its_banner_and_runs_on(self):
        lines = self.transcript(1, 3, 4)
        kept, summary = module_banners.slice_transcript(lines, 3)
        self.assertEqual(summary["start_event"], 4)
        self.assertIsNone(summary["end_event"])
        self.assertEqual(kept, lines[4:])
        self.assertEqual(summary["lint_phase"], "content")
        self.assertEqual(summary["walk_stop"]["reason"], "--turns 12 reached")

    def test_preparation_starts_at_the_first_turn_and_ends_at_the_next_banner(self):
        lines = self.transcript(1, 3)
        kept, summary = module_banners.slice_transcript(lines, 1)
        self.assertEqual((summary["start_event"], summary["end_event"]), (0, 4))
        self.assertEqual(kept, lines[:4])

    def test_a_stall_names_the_module_reached(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            path.write_text("\n".join(self.transcript(1, 3)) + "\n", encoding="utf-8")
            run = subprocess.run([sys.executable, str(HELPER), "slice", str(path), "9",
                                  "--out", str(Path(tmp) / "s.jsonl")],
                                 capture_output=True, text=True)
        self.assertEqual(run.returncode, 3)
        summary = json.loads(run.stdout)
        self.assertFalse(summary["start_found"])
        self.assertEqual(summary["last_module_reached"], "Discover the Business Problem")


if __name__ == "__main__":
    unittest.main()
