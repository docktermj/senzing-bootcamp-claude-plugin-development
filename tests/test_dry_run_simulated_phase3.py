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
   ends on a `walk_stop` event naming the reason. A banner counts only on a line of its own,
   optionally framed by a tripled glyph (#657): a transition question or a journey map's
   `⬜ Bootcamp graduation` is not a banner.
6. **The slice**: `module_banners.py slice` starts at the chosen module's banner, starts at the
   first turn for Bootcamp preparation, ends an exempt module at the next banner, and exits 3,
   naming the module reached, when the walk never showed the start banner. Bootcamp
   preparation ends at the next banner even when its own never displayed (#657).

7. **The persona, wherever a walk is reported (#696).** Check 2 pins the two `/dry-run` sites by
   name; `/auto-test` drives the same `walk.py` with the same persona vocabulary and reported a
   clean run as "no regression detected" with no persona in it. The sites are now **derived by
   scanning** `.claude/skills/` for the walk's own vocabulary (INV-246), and each one either
   states the clean-run line with the persona or sends the reader to `/dry-run`'s rule, which is
   the shape INV-300 asks for and the route `release-cycle` takes.

⚠️ **What this does NOT establish:** that a live walk reaches a module, that a live session
asks the three questions, or that it never answers for the Bootcamper. Those are properties of
a real run. This pins what the instructions say and what the stop and slice code does.

This module enforces INV-369 (registered 2026-10-13). It asserts the sentences and drives the
walk's stop condition offline; it cannot establish that a live session never answers for the
Bootcamper or that a live walk reaches its start module.

⚠️ **Check 7 enforces a widening of INV-369 that is queued and not yet registered.** The
registered subject sentence names `/dry-run` phase 3; the amendment that makes the disclosure
bind every report of a simulated walk is a block in this run's `specs/IMPLEMENTED.md` entry, for
the maintainer to rule on through `/review-invariants` (INV-307, INV-365). The shipped behavior
changes first and the registered text follows, which is the order this repository works in.

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

from _corpus import corpus_files  # noqa: E402
from _wrapped_text import collapsed_blocks, line_of  # noqa: E402

POINTER = "\U0001f449"

#: A file that drives or reports the simulated walk. ⛔ **Derived from the CLAIM, not from the
#: skills already known to run one (INV-282), and measured before it was narrowed.** Of the 23
#: `.md` files under `.claude/`, 5 name a persona and **4** name the walk; the fifth is
#: `feedback-to-issues/SKILL.md`, whose only hit is the word "personal" in a rule about personal
#: details. So the trigger is the walk's own vocabulary rather than "persona", which is a
#: substring of a common word and reads a file that has nothing to do with a walk.
WALK_VOCAB = re.compile(r"(?i)\bwalk\.py\b|\bsimulated walk\b|\bsimulated Bootcamper\b")
#: A quoted clean-run report line, whatever it carries inside the quotes.
REPORT_LINE = re.compile(r'"no regression detected[^"]*"')
#: The disclosure INV-369 makes load-bearing: the persona the walk ran under.
PERSONA = re.compile(r"\(simulated Bootcamper, persona `<p>`\)")
#: A site that states no report line of its own must send the reader to the rule's owner. ⛔ One
#: block naming INV-369 and `dry-run` together, never a phrasing: INV-300 wants one home for the
#: rule, so pointing at it is the correct shape and must not be read as an omission.
OWNER = re.compile(r"(?i)INV-369")
OWNED_BY = re.compile(r"(?i)`?/?dry-run`?")


def squash(text):
    return " ".join(text.split())


def read(path):
    return squash(path.read_text(encoding="utf-8"))


def report_lines(text):
    """``(line, quotation)`` for each quoted clean-run report line, read wrap-aware (INV-346)."""
    out = []
    for flat, origin in collapsed_blocks(text):
        for m in REPORT_LINE.finditer(flat):
            out.append((line_of(origin, m.start()), m.group(0)))
    return out


def points_at_the_owner(text):
    """True when one block sends the reader to `/dry-run`'s rule instead of restating it."""
    return any(OWNER.search(flat) and OWNED_BY.search(flat) for flat, _ in collapsed_blocks(text))


def persona_problems(where, text):
    """Problems at one walk-reporting site: a clean-run line, and no persona and no pointer."""
    lines = report_lines(text)
    if any(PERSONA.search(quote) for _line, quote in lines):
        return []
    if points_at_the_owner(text):
        return []
    bare = ", ".join("%s:%d %s" % (where, line, quote) for line, quote in lines)
    return ["%s reports a clean walk without the persona INV-369 makes load-bearing, and "
            "points at no owner for the rule%s" % (where, (": " + bare) if bare else "")]


def walk_reporting_sites():
    """``(repo-relative path, text)`` for each `.claude/skills/` file that names the walk."""
    out = []
    for path in corpus_files(".claude/skills", suffixes={".md"}):
        text = path.read_text(encoding="utf-8")
        if WALK_VOCAB.search(squash(text)):
            out.append((path.relative_to(REPO_ROOT).as_posix(), text))
    return out


class TheRewordedRuleForbidsSelfPlay(unittest.TestCase):
    """Check 1: the rule is reworded, not relaxed, at every site #571 names."""

    def test_the_skill_forbids_answering_inside_the_session(self):
        body = read(SKILL)
        for pat in (r"⛔ \*\*\(INV-369\) Never answer as the Bootcamper in the session that runs or grades "
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
        for pat in (r"⛔ \*\*\(INV-369\) Self-play is answering as the Bootcamper inside the session that "
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
                         r"⛔ \*\*\(INV-369\) The rule above is not relaxed here:\*\* this session never "
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
        self.assertRegex(body, r"⛔ \*\*\(INV-369\) A clean simulated walk is reported only as "
                         + self.LINE + r"\*\*, never as \"phase 3 passed\"")
        self.assertRegex(body, r"The report still lists phase 3 with the maintainer as not "
                               r"yet done")

    def test_a_stall_is_reported_never_extrapolated(self):
        self.assertRegex(read(PHASE3), r"Exit 3 means the walk stopped before the start "
                                       r"module:\*\* report the module it reached and leave "
                                       r"the rest untested\. Never extrapolate\.")


#: The `/auto-test` report rule as it shipped from #395 until #696: a clean run with no persona.
PRE_696 = ('> **Findings are trustworthy. A clean run is weak evidence.**\n\n'
           'Report a clean auto-test as "no regression detected", never as "the bootcamp works".\n'
           'Phase 3 with a human still has to happen. The walk drives `walk.py`.\n')


class EveryWalkReportNamesThePersona(unittest.TestCase):
    """Check 7 (#696): a clean walk is reported with its persona wherever the walk is reported.

    INV-369's subject sentence names `/dry-run` phase 3, and the reason the persona is
    load-bearing is a property of the **walk**, not of the skill that launched it: a clean run
    under `confused` and a clean run under `offscript` are different evidence, and a reader given
    "no regression detected" alone cannot tell which one they have. `/auto-test` drives the same
    `walk.py` with the same persona vocabulary and reported a clean run without it.

    ⛔ **The sites are derived by scanning `.claude/skills/`, never listed (INV-246).** A fourth
    skill that grows a walk report is covered the day it is written, which a list of the three
    that have one today cannot be.

    ⚠️ **Two ways to pass, because INV-300 wants one home for a rule.** A site either states the
    clean-run line with the persona in it, or sends the reader to `/dry-run`'s rule. Today
    `.claude/skills/release-cycle/SKILL.md` takes the second route and is correct as written.

    ⛔ **What this cannot establish:** that a live `/auto-test` run prints the persona. It reads
    the instruction, as the rest of this module does.

    ⚠️ **The widening is queued, not registered.** `specs/IMPLEMENTED.md` carries this run's
    amendment block for INV-369; `specs/INVARIANTS.md` is written only by `/review-invariants`
    (INV-307, INV-365), so the shipped behavior changes first and the registered text follows.
    """

    def test_the_scan_finds_the_sites(self):
        """A scan matching nothing would make the assertion below vacuous (INV-308)."""
        found = {rel for rel, _ in walk_reporting_sites()}
        self.assertGreaterEqual(len(found), 3, found)
        for rel in (".claude/skills/auto-test/SKILL.md",
                    ".claude/skills/dry-run/SKILL.md",
                    ".claude/skills/dry-run/phase3-conversational.md"):
            self.assertIn(rel, found)

    def test_every_site_names_the_persona_or_points_at_the_rule(self):
        problems = []
        for rel, text in walk_reporting_sites():
            problems.extend(persona_problems(rel, text))
        self.assertEqual([], problems, "\n" + "\n".join(problems))

    def test_the_auto_test_skill_states_it(self):
        body = read(AUTO_TEST / "SKILL.md")
        self.assertRegex(body, r"⛔ \*\*\(INV-369\) A clean run that included the walk is "
                               r"reported only as " + ACleanSimulatedRunIsNotAPass.LINE +
                         r"\*\*, never as \"phase 3 passed\" or \"the bootcamp works\", and the "
                         r"report lists phase 3 with the maintainer as not yet done\.")
        self.assertRegex(body, r"A probe-only run names no persona, because no walk ran\.")

    def test_the_auto_test_report_step_asks_for_the_persona(self):
        self.assertRegex(read(AUTO_TEST / "SKILL.md"),
                         r"naming the sandbox the run used and whether the walk was included, "
                         r"and, where it was, the persona the clean-run line above requires "
                         r"\(INV-369\)")

    def test_the_pre_696_auto_test_wording_is_reported(self):
        """The control, run before the fix: the shipped rule with no persona and no pointer."""
        problems = persona_problems(".claude/skills/auto-test/SKILL.md", PRE_696)
        self.assertEqual(1, len(problems), problems)
        self.assertIn('"no regression detected"', problems[0])
        self.assertIn("points at no owner", problems[0])

    def test_a_site_that_points_at_the_owner_passes(self):
        text = ("Report the walk as `/dry-run` reports it (INV-369), including the module a "
                "stalled walk reached.\n")
        self.assertEqual([], persona_problems("x.md", text))

    def test_a_pointer_split_across_two_blocks_does_not_count(self):
        text = "A simulated walk runs here. INV-369 governs it.\n\nSee `/dry-run` for more.\n"
        self.assertEqual(1, len(persona_problems("x.md", text)))

    def test_a_site_with_no_report_line_and_no_pointer_is_reported(self):
        problems = persona_problems("x.md", "This skill drives `walk.py` and reports nothing.\n")
        self.assertEqual(1, len(problems), problems)
        self.assertNotIn('"no regression', problems[0])

    def test_a_report_line_wrapped_across_two_lines_is_read_as_one(self):
        """⚠️ (INV-346) Markdown wraps a sentence wherever the column runs out."""
        text = ('A clean simulated walk is reported only as "no regression detected (simulated\n'
                'Bootcamper, persona `<p>`)", never as "phase 3 passed".\n')
        self.assertEqual([], persona_problems("x.md", text))
        self.assertEqual(1, len(report_lines(text)))

    def test_the_live_sites_each_state_or_point(self):
        """Which route each shipped site takes today, so a change of route is visible."""
        routes = {}
        for rel, text in walk_reporting_sites():
            states = any(PERSONA.search(q) for _line, q in report_lines(text))
            routes[rel] = "states" if states else ("points" if points_at_the_owner(text) else "")
        self.assertEqual("states", routes[".claude/skills/auto-test/SKILL.md"])
        self.assertEqual("states", routes[".claude/skills/dry-run/SKILL.md"])
        self.assertEqual("states", routes[".claude/skills/dry-run/phase3-conversational.md"])
        self.assertEqual("points", routes[".claude/skills/release-cycle/SKILL.md"])


class TheHumanWalkIsTheDefault(unittest.TestCase):
    """Check 3: an empty argument asks who answers; the maintainer is the default."""

    def test_the_third_question_is_asked(self):
        body = read(SKILL)
        for pat in (r"⛔ \*\*\(INV-369, INV-333\) Then a third: who answers as the Bootcamper\.\*\* "
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


def _turn_text(turn, banner_at, banner, question_at=None):
    body = f"Turn {turn} of the bootcamp. " + "x" * 220
    if turn == banner_at:
        body = f"━━━\n🚀🚀🚀  {banner}  🚀🚀🚀\n━━━\n" + body
    if turn == question_at:
        return body + f"\n{POINTER} **Are you ready to move on to the next module: SDK setup?**"
    return body + f"\n{POINTER} What would you like to do next?"


class TheWalkStopsOffline(unittest.TestCase):
    """Check 5: the stop condition, with both `claude` calls stubbed; no token is spent."""

    BANNER = "MODULE: SDK SETUP"

    def walk(self, turns, max_turns=150, banner_at=None, stop_at_banner=None,
             question_at=None):
        calls = []

        def fake_claude(args, cwd, stdin_text=None, timeout=600, env=None):
            calls.append(args)
            text = _turn_text(len(calls), banner_at, self.BANNER, question_at)
            return subprocess.CompletedProcess(args, 0, stdout=_assistant(text) + "\n",
                                               stderr="")

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(walk, "_claude", fake_claude), \
                mock.patch.object(walk, "bootcamper_reply", lambda *a, **k: "1"), \
                redirect_stdout(io.StringIO()):
            out = Path(tmp) / "t.jsonl"
            # A project directory of its own: the Bootcamper's cwd is made beside it (#834).
            project = Path(tmp) / "project"
            project.mkdir()
            walk.run_walk(project, out, turns, "terse", Path(tmp) / "mcp.json", None, None,
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

    def test_the_transition_question_is_not_the_banner(self):
        # #657: "next module: SDK setup?" fired the stop one guide turn early.
        count, stop = self.walk(turns=1, banner_at=3, question_at=2,
                                stop_at_banner=self.BANNER)
        self.assertEqual((count, stop["banner_turn"]), (4, 3))

    def test_a_banner_counts_only_on_a_line_of_its_own(self):
        # #657: each pair is (banner, text, shown?), from the 2026-10-14 walk transcript.
        cases = [
            ("BOOTCAMP GRADUATION", "✅ Bootcamp preparation\n⬜ Bootcamp graduation", False),
            ("BOOTCAMP GRADUATION", "Done.\n\n🎓🎓🎓  BOOTCAMP GRADUATION  🎓🎓🎓\n\nWell done.",
             True),
            ("MODULE: SDK SETUP",
             f"{POINTER} **Are you ready to move on to the next module: SDK setup?**", False),
            ("MODULE: SDK SETUP", "🚀🚀🚀  MODULE: SDK SETUP  🚀🚀🚀", True),
            ("module: sdk setup", "🚀🚀🚀  MODULE: SDK SETUP  🚀🚀🚀", True),
            ("MODULE: SDK SETUP", "🚀🚀🚀\tMODULE:  SDK SETUP 🚀🚀🚀\r\n", True),
            ("MODULE: SDK SETUP", "MODULE: SDK SETUP", True),
            ("ENTITY RESOLUTION CONCEPTS",
             "The modules: **Bootcamp preparation**, *Entity Resolution Concepts* (optional)",
             False),
            ("BOOTCAMP GRADUATION", "🔄 Bootcamp graduation", False),
            ("BOOTCAMP GRADUATION", "🎓🎓 BOOTCAMP GRADUATION 🎓🎓", False),
            ("MODULE: SDK SETUP", "🚀🚀🚀  MODULE: SDK SETUP  🚀🚀🚀 Let's begin.", False),
        ]
        for banner, text, shown in cases:
            with self.subTest(banner=banner, text=text):
                self.assertIs(walk.banner_seen(banner, text), shown)

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
        # `run_walk` returns (events written, the abnormal-end reason or None) since #732.
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(walk, "run_walk", return_value=(0, None)) as run, \
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

    def walk_like_2026_10_14(self):
        """The 2026-10-14 walk's shape (#657): banners as lines of their own, and the same
        names in prose, journey maps, transition questions and a tool result."""
        gate = POINTER + " **Are you ready to move on to the next module: {}?**"
        journey = "\n✅ Bootcamp preparation\n{}\n⬜ Bootcamp graduation"
        framed = {n: f"{g * 3}  {self.banner[n]}  {g * 3}"
                  for n, g in ((1, "🧰"), (2, "🧭"), (3, "🚀"), (4, "🚀"))}
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "content": framed[1]}]}})
        events = [
            _assistant("The modules: **Bootcamp preparation**, *Entity Resolution Concepts* "
                       "(optional), **Discover the Business Problem**, ... **Bootcamp "
                       "graduation**.\n" + POINTER + " Any questions?"),
            tool_result,
            _assistant(framed[2] + journey.format("🔄 **Entity Resolution Concepts**")
                       + "\n" + POINTER + " Ready?"),
            _assistant(gate.format("Discover the Business Problem")),
            _assistant(framed[3] + journey.format("🔄 **Discover the Business Problem**")
                       + "\n" + POINTER + " Ready?"),
            _assistant(gate.format("SDK setup")),
            _assistant(framed[4] + journey.format("🔄 **SDK setup**") + "\n" + POINTER
                       + " Ready?"),
        ]
        lines = []
        for turn, event in enumerate(events, 1):
            lines += [event, json.dumps({"type": "bootcamper", "turn": turn, "text": "ok"})]
        lines.append(json.dumps({"type": "walk_stop", "turn": 7, "reason": "--turns 1 reached",
                                 "stop_at_banner": None, "banner_turn": None}))
        return lines

    def test_journey_maps_and_prose_are_not_banners(self):
        # #657: graduation was "reached" from every journey map's "⬜ Bootcamp graduation",
        # and Bootcamp preparation from the welcome prose.
        _, summary = module_banners.slice_transcript(self.walk_like_2026_10_14(), 4)
        self.assertEqual(summary["modules_reached"], ["Entity Resolution Concepts",
                                                      "Discover the Business Problem",
                                                      "SDK setup"])
        self.assertEqual(summary["last_module_reached"], "SDK setup")
        _, summary = module_banners.slice_transcript(self.walk_like_2026_10_14(), 11)
        self.assertFalse(summary["start_found"])

    def test_a_module_starts_at_its_banner_not_the_question_before_it(self):
        # #657: SDK setup started at the transition question, one guide turn early.
        lines = self.walk_like_2026_10_14()
        kept, summary = module_banners.slice_transcript(lines, 4)
        self.assertEqual((summary["start_event"], summary["end_event"]), (12, None))
        self.assertEqual(kept, lines[12:])

    def test_entity_resolution_concepts_runs_from_its_banner_to_the_next(self):
        # #657: the welcome prose matched first, so the slice was the empty 0:0.
        lines = self.walk_like_2026_10_14()
        kept, summary = module_banners.slice_transcript(lines, 2)
        self.assertEqual((summary["start_event"], summary["end_event"]), (4, 8))
        self.assertEqual(kept, lines[4:8])

    def test_preparation_ends_at_the_next_banner_when_its_own_never_showed(self):
        # #657: the preparation banner showed only in a tool result; the slice must still
        # end at the next module's banner, or check_apparatus lints the whole walk as exempt.
        lines = self.walk_like_2026_10_14()
        kept, summary = module_banners.slice_transcript(lines, 1)
        self.assertNotIn("Bootcamp preparation", summary["modules_reached"])
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
