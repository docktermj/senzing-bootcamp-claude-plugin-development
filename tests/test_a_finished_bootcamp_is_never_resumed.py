"""A finished bootcamp reads as finished, from either file, and is never resumed (#905).

After graduation the progress file still said `current_module: query_visualize_discover` with
`current_step: null`, and completion was recorded only as `bootcamp_complete: true` in the
preferences. `/start-bootcamp` and the session-start hook offer a resume whenever
`current_module` is set, so a finished project was offered "Where you left off: Query,
Visualize and Discover." Clearing `current_module` is no fix: a null one is a fresh bootcamp
and runs onboarding from the top (INV-227).

What changed, and what this file asserts:

- **The write.** Graduation's closing step, on a decline, writes the progress file in the same
  step as the preferences flag: `bootcamp_complete: true`, `completed_at`,
  `current_module: "graduation"`, `current_step: null`, and `graduation` appended to
  `modules_completed` if absent, every other key kept, on the normal path and after Step 2's
  Abort alike.
- **The rule.** The bootcamp is finished when **either** file carries the flag, so a project
  graduated before the write existed still counts. It has one implementation,
  `module_start_apparatus.bootcamp_complete()`, and `stop-nudge.py` delegates to it. Each
  reader is run against the flag in progress only, in preferences only, in both and in
  neither (an active bootcamp, unchanged).
- **The finished start.** `session-start.py` makes no resume offer on a finished project, even
  with the progress file missing or malformed, and tells the guide to follow the finished case
  of `bootcamp-onboarding/SKILL.md` step 2, which `/start-bootcamp` states too: say it is
  complete, name `/package-bootcamp`, end on one open 👉 question. Never onboarding.
- **The journey map.** On a finished bootcamp every row is ✅, Bootcamp graduation included,
  with no 🔄.

Enforces the finished case drafted as an amendment to **INV-227** (#905): a resume decision is
made on recorded content, and a finished bootcamp is a fourth case ahead of the other three.

⛔ The hooks run as subprocesses with a real working directory, the way Claude Code invokes
them. The negative controls run the same checks on a mutated copy of the text or of the
scripts, so each check is shown to fail on the defect it guards. These cannot establish that a
live guide makes the write or says the pinned lines, which only `dry-run` phase 3 observes.

Run:  python3 -m unittest discover -s tests
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"
SESSION_START = "session-start.py"
STOP_NUDGE = "stop-nudge.py"
BUILDER = "module_start_apparatus.py"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"
ONBOARDING = PLUGIN / "skills" / "bootcamp-onboarding" / "SKILL.md"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
START_COMMAND = PLUGIN / "commands" / "start-bootcamp.md"

#: The progress file as the reported run left it: the last module, no step, no flag.
LEFT_ON_LAST_MODULE = {"current_module": "query_visualize_discover", "current_step": None,
                       "modules_completed": ["business_problem", "query_visualize_discover"]}
#: The progress file as graduation's closing step now leaves it.
GRADUATED = {"current_module": "graduation", "current_step": None, "bootcamp_complete": True,
             "completed_at": "2026-11-10T12:00:00Z",
             "modules_completed": ["business_problem", "query_visualize_discover",
                                   "graduation"]}
#: An active bootcamp, partway through a module.
ACTIVE = {"current_module": "sdk_setup", "current_step": 3}

FLAG = "name: Ada\nbootcamp_complete: true\n"
NO_FLAG = "name: Ada\nbootcamp_complete: false\n"

#: (case, progress, preferences, finished?) -- the four cases the issue names.
MATRIX = (
    ("progress only", GRADUATED, NO_FLAG, True),
    ("preferences only", LEFT_ON_LAST_MODULE, FLAG, True),
    ("both", GRADUATED, FLAG, True),
    ("neither", ACTIVE, NO_FLAG, False),
)

#: A final text that asks nothing: the Stop hook blocks on it during an active bootcamp.
PAUSED_TEXT = "Data processing steps 1 and 2 are done. I stopped before step 3."
RESUME_LEAD = "A Senzing bootcamp is in progress."


def flat(text):
    return " ".join(text.split())


def read(path):
    return path.read_text(encoding="utf-8")


class Scripts:
    """The plugin's top-level scripts, or a scratch copy of them with mutations applied."""

    def __init__(self, test, mutations=None):
        self.dir = SCRIPTS
        if mutations:
            tmp = tempfile.TemporaryDirectory()
            test.addCleanup(tmp.cleanup)
            self.dir = Path(tmp.name)
            for path in SCRIPTS.glob("*.py"):
                shutil.copy(path, self.dir / path.name)
            for name, (old, new) in mutations.items():
                source = read(self.dir / name)
                test.assertIn(old, source, "the mutation of %s no longer applies" % name)
                (self.dir / name).write_text(source.replace(old, new), encoding="utf-8")

    def run(self, test, script, project, stdin="{}"):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env.pop("SENZING_BOOTCAMP_DISABLE_STOP_NUDGE", None)
        proc = subprocess.run([sys.executable, str(self.dir / script)],
                              input=stdin.encode("utf-8"), capture_output=True,
                              cwd=str(project), env=env, timeout=60)
        err = proc.stderr.decode("utf-8")
        test.assertEqual(0, proc.returncode, err)
        test.assertNotIn("Traceback", err)
        return proc.stdout

    def predicate(self, test, project, call="bootcamp_complete()"):
        code = ("import sys; sys.path.insert(0, %r)\n"
                "import module_start_apparatus as m\n"
                "print(repr(m.%s))\n" % (str(self.dir), call))
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              cwd=str(project), timeout=60)
        test.assertEqual(0, proc.returncode, proc.stderr)
        return proc.stdout.strip()


def project(test, progress, preferences):
    """A scratch bootcamp project. ``progress`` is a dict, raw text, or None for no file."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    (root / "config").mkdir()
    if progress is not None:
        text = progress if isinstance(progress, str) else json.dumps(progress)
        (root / "config" / "bootcamp_progress.json").write_text(text, encoding="utf-8")
    if preferences is not None:
        (root / "config" / "bootcamp_preferences.yaml").write_text(preferences,
                                                                    encoding="utf-8")
    return root


def session_start_problems(out, finished):
    """What is wrong with session start's message for a finished (or active) project."""
    text = out.decode("utf-8")
    if not finished:
        return [] if RESUME_LEAD in text else ["an active bootcamp lost its resume offer"]
    problems = []
    if RESUME_LEAD in text or "offer to resume from" in text:
        problems.append("a finished bootcamp was offered a resume")
    if "Module-start reminder" in text:
        problems.append("a finished bootcamp got a module-start reminder")
    for needed in ("bootcamp is complete", "/package-bootcamp",
                   "Do not offer to resume a module and do not run onboarding",
                   "bootcamp-onboarding/SKILL.md step 2"):
        if needed not in text:
            problems.append("the finished message does not say %r" % needed)
    try:
        out.decode("ascii")
    except UnicodeDecodeError:
        problems.append("the finished message is not ASCII (a Windows console can break it)")
    return problems


def stop_payload():
    return json.dumps({"stop_hook_active": False, "last_assistant_message": PAUSED_TEXT})


class EveryReaderUsesTheEitherFileRule(unittest.TestCase):
    """The flag in progress only, in preferences only, in both, and in neither."""

    def test_the_shared_predicate(self):
        scripts = Scripts(self)
        for case, progress, preferences, finished in MATRIX:
            with self.subTest(case=case):
                self.assertEqual(repr(finished),
                                 scripts.predicate(self, project(self, progress, preferences)))

    def test_session_start(self):
        scripts = Scripts(self)
        for case, progress, preferences, finished in MATRIX:
            with self.subTest(case=case):
                out = scripts.run(self, SESSION_START, project(self, progress, preferences))
                self.assertEqual([], session_start_problems(out, finished))

    def test_the_stop_nudge(self):
        scripts = Scripts(self)
        for case, progress, preferences, finished in MATRIX:
            with self.subTest(case=case):
                out = scripts.run(self, STOP_NUDGE, project(self, progress, preferences),
                                  stop_payload())
                if finished:
                    self.assertEqual(b"", out, "the Stop hook nudged after graduation")
                else:
                    self.assertEqual("block", json.loads(out.decode("utf-8"))["decision"],
                                     "(control) an active bootcamp's pause no longer blocks")

    def test_the_resume_reminder(self):
        """`resume_reminder()` adds nothing on a finished project, whichever file says so."""
        scripts = Scripts(self)
        not_begun = dict(GRADUATED, bootcamp_complete=False)
        for case, progress, preferences, finished in (
                ("progress only", GRADUATED, NO_FLAG, True),
                ("preferences only", not_begun, FLAG, True),
                ("neither", not_begun, NO_FLAG, False)):
            with self.subTest(case=case):
                out = scripts.predicate(self, project(self, progress, preferences),
                                        "resume_reminder()")
                self.assertEqual(not finished, "Module-start reminder" in out, out)

    def test_a_false_or_absent_progress_flag_is_not_finished(self):
        scripts = Scripts(self)
        for value in (False, "false", "no", None, 0):
            with self.subTest(value=value):
                progress = dict(ACTIVE, bootcamp_complete=value)
                self.assertEqual("False", scripts.predicate(
                    self, project(self, progress, NO_FLAG)))
        for value in (True, "true", "yes"):
            with self.subTest(value=value):
                progress = dict(ACTIVE, bootcamp_complete=value)
                self.assertEqual("True", scripts.predicate(
                    self, project(self, progress, None)))


class AFinishedProjectNeverRunsOnboarding(unittest.TestCase):
    """The edge cases: a finished project whose progress file is missing or malformed."""

    def test_progress_missing_preferences_flag_set(self):
        out = Scripts(self).run(self, SESSION_START, project(self, None, FLAG))
        self.assertEqual([], session_start_problems(out, True))

    def test_progress_malformed_preferences_flag_set(self):
        for raw in ('{"current_module": ', "", "[1, 2]", '{"current_module": null}'):
            with self.subTest(progress=raw):
                out = Scripts(self).run(self, SESSION_START, project(self, raw, FLAG))
                self.assertEqual([], session_start_problems(out, True))

    def test_control_the_same_projects_without_the_flag_say_nothing(self):
        """Without the flag these are fresh starts, and session start stays silent (INV-227)."""
        for raw in (None, '{"current_module": ', '{"current_module": null}'):
            with self.subTest(progress=raw):
                out = Scripts(self).run(self, SESSION_START, project(self, raw, NO_FLAG))
                self.assertEqual(b"", out.strip())


class TheRuleHasOneImplementation(unittest.TestCase):
    """`stop-nudge.py` delegates to `module_start_apparatus.bootcamp_complete()`."""

    def test_stop_nudge_delegates(self):
        self.assertEqual([], delegation_problems(read(SCRIPTS / STOP_NUDGE)))

    def test_session_start_and_the_reminder_use_the_shared_predicate(self):
        for name in (SESSION_START, "module-number-reminder.py"):
            with self.subTest(script=name):
                self.assertIn("module_start_apparatus.bootcamp_complete()",
                              read(SCRIPTS / name))

    def test_session_start_checks_the_finished_case_first(self):
        source = read(SCRIPTS / SESSION_START)
        tests = [ast.unparse(node.test) for node in ast.parse(source).body
                 if isinstance(node, ast.If)]
        self.assertIn("module_start_apparatus.bootcamp_complete()", tests)
        self.assertIn("recap_checkpoint.bootcamp_active()", tests)
        self.assertLess(tests.index("module_start_apparatus.bootcamp_complete()"),
                        tests.index("recap_checkpoint.bootcamp_active()"),
                        "session start checks the resume before the finished case")


def delegation_problems(source):
    """What is wrong with how a ``stop-nudge.py`` source decides the bootcamp is complete."""
    tree = ast.parse(source)
    func = next((node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "bootcamp_complete"), None)
    if func is None:
        return ["stop-nudge.py has no bootcamp_complete()"]
    body = ast.unparse(ast.Module(body=func.body[1:], type_ignores=[]))
    if body.strip() != "return module_start_apparatus.bootcamp_complete()":
        return ["stop-nudge.py's bootcamp_complete() does not delegate: %r" % body.strip()]
    return []


#: The graduation write's clauses, each with the pattern that finds it in the "Declines"
#: branch's first sub-step.
WRITE_CLAUSES = (
    ("the preferences flag", r"Set a top-level `bootcamp_complete: true` key in "
                             r"`config/bootcamp_preferences\.yaml`"),
    ("the progress file, in the same step", r"In the same step, write "
                                            r"`config/bootcamp_progress\.json`"),
    ("the progress flag", r"`config/bootcamp_progress\.json`: set `bootcamp_complete: true`"),
    ("completed_at in ISO 8601", r"`completed_at` to the current time in ISO 8601"),
    ("current_module graduation", r'`current_module: "graduation"`'),
    ("current_step null", r"`current_step: null`"),
    ("graduation appended if absent",
     r"append `graduation` to `modules_completed` if it is absent"),
    ("every other key kept", r"keeping every other key as it is"),
    ("both paths", r"on the normal path and after Step 2's Abort alike"),
)


def declines_step_one(text):
    """The "Declines" branch's first sub-step in graduation's closing step, flattened."""
    m = re.search(r"- \*\*Declines\*\*.*?\n\s+1\. (.*?)\n\s+2\. ", text, re.S)
    return flat(m.group(1)) if m else None


def write_problems(text):
    step = declines_step_one(text)
    if step is None:
        return ["the Declines branch's first sub-step was not found"]
    return ["the closing step does not state %s" % label
            for label, pattern in WRITE_CLAUSES if not re.search(pattern, step)]


class GraduationWritesTheProgressFile(unittest.TestCase):

    def test_the_declines_branch_writes_both_files(self):
        self.assertEqual([], write_problems(read(GRADUATION)))

    def test_keep_exploring_writes_nothing(self):
        text = read(GRADUATION)
        m = re.search(r"- \*\*Wants to keep exploring\*\*(.*?)\n\s+- \*\*Declines\*\*", text,
                      re.S)
        self.assertIsNotNone(m)
        self.assertNotIn("bootcamp_progress.json", m.group(1))
        self.assertNotIn("bootcamp_complete", m.group(1))

    def test_the_documented_write_produces_a_finished_project(self):
        """The write as stated, applied to the reported run's file, reads as finished and
        keeps every other key."""
        progress = dict(LEFT_ON_LAST_MODULE, language="python")
        progress.update(bootcamp_complete=True, completed_at="2026-11-10T12:00:00Z",
                        current_module="graduation", current_step=None)
        if "graduation" not in progress["modules_completed"]:
            progress["modules_completed"] = progress["modules_completed"] + ["graduation"]
        self.assertEqual("python", progress["language"])
        root = project(self, progress, "name: Ada\n")
        self.assertEqual("True", Scripts(self).predicate(self, root))
        out = Scripts(self).run(self, SESSION_START, root)
        self.assertEqual([], session_start_problems(out, True))


def finished_case(text):
    """The finished case of onboarding step 2, flattened, or None."""
    m = re.search(r"- \*\*Finished\*\* — (.*?)\n   - \*\*Missing\*\*", text, re.S)
    return flat(re.sub(r"(?m)^\s*>[ \t]?", "", m.group(1))) if m else None


#: The pinned lines, as read with the quote markers removed.
FINISHED_LINES = (
    "in this form: Your Senzing bootcamp is complete. Run `/package-bootcamp` anytime to "
    "bundle your bootcamp results into one zip you can archive, move to another machine, or "
    "share with others. 👉 **What would you like to explore?**"
)


def step_two_problems(text):
    case = finished_case(text)
    if case is None:
        return ["step 2 has no Finished case directly before the Missing case"]
    problems = []
    for label, pattern in (
            ("either file", r"`bootcamp_complete: true` in `config/bootcamp_progress\.json` "
                            r"\*\*or\*\* in `config/bootcamp_preferences\.yaml`"),
            ("even when missing or malformed", r"even when it is missing or malformed"),
            ("no onboarding, no resume", r"Run no onboarding and make no resume offer"),
            ("the pinned lines", re.escape(FINISHED_LINES))):
        if not re.search(pattern, case):
            problems.append("the Finished case does not state %s" % label)
    if case.count("👉") != 1:
        problems.append("the Finished case carries %d 👉 questions, not one" % case.count("👉"))
    if not re.search(r"Four cases, and the first is checked before the other three", flat(text)):
        problems.append("step 2 does not say the finished case is checked first")
    return problems


def command_problems(text):
    m = re.search(r"- \*\*A finished bootcamp\*\* (.*?)\n- \*\*No file\*\*", text, re.S)
    if m is None:
        return ["/start-bootcamp has no finished case directly before the No file case"]
    case = flat(m.group(1))
    problems = []
    for label, needed in (("either file", "`config/bootcamp_progress.json` or in "
                                          "`config/bootcamp_preferences.yaml`"),
                          ("no onboarding", "do not start onboarding"),
                          ("no resume", "do not offer to resume a module"),
                          ("the packager", "`/package-bootcamp`"),
                          ("one open 👉", "one open 👉 question")):
        if needed not in case:
            problems.append("/start-bootcamp's finished case does not state %s" % label)
    return problems


class TheFinishedStartIsStated(unittest.TestCase):

    def test_onboarding_step_two(self):
        self.assertEqual([], step_two_problems(read(ONBOARDING)))

    def test_the_start_command(self):
        self.assertEqual([], command_problems(read(START_COMMAND)))


JOURNEY_CLAUSE = re.compile(
    r"\*\*On a finished bootcamp\*\* \(`bootcamp_complete: true` in either file, `SKILL\.md` "
    r"step 2\), a journey map shown afterwards marks every row `✅ done`, Bootcamp graduation "
    r"included, and no row 🔄 or ⬜, so N equals M\.")


def journey_problems(text):
    return [] if JOURNEY_CLAUSE.search(flat(text)) else [
        "the journey map's canonical statement has no finished-bootcamp clause"]


class TheJourneyMapOfAFinishedBootcamp(unittest.TestCase):

    def test_the_canonical_statement_marks_every_row_done(self):
        self.assertEqual([], journey_problems(read(GROUND_RULES)))


class NegativeControls(unittest.TestCase):
    """Each check above fails on the defect it guards, run on a mutated copy."""

    def test_a_removed_progress_write_is_caught(self):
        text = read(GRADUATION)
        start = text.index("In the same step, write `config/bootcamp_progress.json`")
        end = text.index("Step 2's Abort alike.", start) + len("Step 2's Abort alike.")
        mutant = text[:start] + text[end:]
        self.assertNotEqual(text, mutant)
        self.assertGreaterEqual(len(write_problems(mutant)), 8, write_problems(mutant))

    def test_a_dropped_clause_is_caught(self):
        text = read(GRADUATION)
        for old, new in ((", keeping every other key as it is", ""),
                         (" and after Step 2's Abort alike", ""),
                         ('`current_module: "graduation"`', '`current_module: null`')):
            with self.subTest(dropped=old):
                mutant = text.replace(old, new, 1)
                self.assertNotEqual(text, mutant)
                self.assertTrue(write_problems(mutant))

    def test_a_predicate_reading_preferences_only_is_caught(self):
        """The old rule: a project whose flag is in the progress file only reads as active."""
        scripts = Scripts(self, {BUILDER: ("return _progress_flag() or _preferences_flag()",
                                           "return _preferences_flag()")})
        root = project(self, GRADUATED, NO_FLAG)
        self.assertEqual("False", scripts.predicate(self, root))
        self.assertTrue(session_start_problems(scripts.run(self, SESSION_START, root), True))

    def test_a_predicate_reading_progress_only_is_caught(self):
        """A project graduated before the write existed would read as active again."""
        scripts = Scripts(self, {BUILDER: ("return _progress_flag() or _preferences_flag()",
                                           "return _progress_flag()")})
        root = project(self, LEFT_ON_LAST_MODULE, FLAG)
        self.assertTrue(session_start_problems(scripts.run(self, SESSION_START, root), True))

    def test_a_session_start_without_the_finished_check_is_caught(self):
        scripts = Scripts(self, {SESSION_START: (
            "if module_start_apparatus.bootcamp_complete():\n    print(FINISHED)",
            "if False:\n    print(FINISHED)")})
        out = scripts.run(self, SESSION_START, project(self, LEFT_ON_LAST_MODULE, FLAG))
        self.assertIn("a finished bootcamp was offered a resume",
                      session_start_problems(out, True))
        out = scripts.run(self, SESSION_START, project(self, None, FLAG))
        self.assertTrue(session_start_problems(out, True),
                        "a missing progress file with the flag set did not fail")

    def test_a_stop_nudge_with_its_own_preferences_check_is_caught(self):
        old = "return module_start_apparatus.bootcamp_complete()"
        new = 'return pref_flag("bootcamp_complete")'
        mutant_source = read(SCRIPTS / STOP_NUDGE).replace(old, new)
        self.assertTrue(delegation_problems(mutant_source))
        scripts = Scripts(self, {STOP_NUDGE: (old, new)})
        out = scripts.run(self, STOP_NUDGE, project(self, GRADUATED, NO_FLAG), stop_payload())
        self.assertNotEqual(b"", out, "the progress-only finished project no longer speaks, "
                                      "so the matrix cannot tell the two rules apart")

    def test_a_dropped_finished_case_is_caught(self):
        text = read(ONBOARDING)
        mutant = text.replace("- **Finished** —", "- **Done** —", 1)
        self.assertTrue(step_two_problems(mutant))
        two = text.replace("👉 **What would you like to explore?**",
                           "👉 **What would you like to explore?** 👉 **Resume?**", 1)
        self.assertTrue(step_two_problems(two))
        command = read(START_COMMAND)
        self.assertTrue(command_problems(command.replace("do not offer to resume a module",
                                                         "offer to resume", 1)))

    def test_a_journey_map_with_graduation_current_is_caught(self):
        text = read(GROUND_RULES)
        mutant = text.replace("marks every row `✅ done`, Bootcamp graduation included, and no\n"
                              "  row 🔄 or ⬜", "marks Bootcamp graduation `🔄 you are here`", 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertTrue(journey_problems(mutant))


if __name__ == "__main__":
    unittest.main()
