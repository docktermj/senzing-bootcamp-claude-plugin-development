"""The module-start apparatus reminder fires when a module is about to start, and only then.

Issue #851: in one session the module-start apparatus (banner, journey map, before/after
framing, step overview, time estimate, model/effort nudge) was skipped at five of eight
module starts, although every module's `**First:**` line states it. Two hooks now put a
reminder into the guide's context at the moment it is due:

- `scripts/module-start-reminder.py` (`UserPromptSubmit`), on the reply to the pinned
  transition question or the graduation offer;
- `scripts/session-start.py` (`SessionStart`), on a resume into a module whose
  `current_step` is null.

Both build the text with `scripts/module_start_apparatus.py`, so it is stated once
(INV-300); `TheReminderIsStatedOnce` reads both hooks' code for a second copy.

**Every silent and exempt case has a twin that speaks.** A hook that is silent because it is
broken satisfies every silence assertion on its own, so each silent case below runs the same
fixture with only the triggering element changed and requires the reminder from it first
(the shape `tests/test_stop_nudge_silence_and_opt_outs.py` uses). Without the twin, a
silence assertion would pass against a hook that never fires.

The hooks read their payload from stdin and resolve `config/` against the working
directory, so each case runs them as subprocesses in a temp project, the way Claude Code
invokes them. Standard library only; nothing under `plugins/` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"
HOOK = SCRIPTS / "module-start-reminder.py"
SESSION_START = SCRIPTS / "session-start.py"
BUILDER = SCRIPTS / "module_start_apparatus.py"
HOOKS_JSON = PLUGIN / "hooks" / "hooks.json"
HOOKS_README = PLUGIN / "hooks" / "README.md"

POINTER = "\U0001f449"


def transition(name):
    """The pinned transition question, as the module skills render it."""
    return "%s **Are you ready to move on to the next module: %s?**" % (POINTER, name)


GRADUATION_OFFER = ("%s **Would you like to graduate now and generate your production "
                    "project and recap?**" % POINTER)
OTHER_QUESTION = "%s **Are you done modifying the model and effort?**" % POINTER
SUMMARY = "**Module complete: Discover the Business Problem**\n\nWhat you accomplished: ..."

#: A module recorded and not begun: the state module completion's Step 1 leaves.
ACTIVE = {"current_module": "sdk_setup", "current_step": None}

#: Every apparatus item the reminder must name, as a pattern on its text.
MODULE_ITEMS = (
    ("banner", r"MODULE: banner"),
    ("journey map", r"journey map"),
    ("before/after", r"before/after framing"),
    ("step overview", r"numbered step overview"),
    ("time estimate per verbosity", r"time-to-complete per the active verbosity preset, "
                                    r"suppressed under minimal and one line under concise"),
    ("model/effort nudge", r"model/effort nudge"),
)

#: The graduation form's items: its own banner, and the terminal journey map.
GRADUATION_ITEMS = (
    ("graduation banner", r"BOOTCAMP GRADUATION banner"),
    ("terminal journey map", r"journey map with every selected module checked as "
                             r"experienced, Bootcamp graduation as the current and final "
                             r"stage, and nothing upcoming"),
    ("before/after", r"before/after framing"),
    ("step overview", r"numbered step overview"),
    ("time estimate per verbosity", r"time-to-complete per the active verbosity preset, "
                                    r"suppressed under minimal and one line under concise"),
    ("model/effort nudge", r"model/effort nudge"),
)


def assistant(text, *, as_list=True, sidechain=False, tool_use=False):
    content = [{"type": "text", "text": text}] if as_list else text
    if tool_use:
        content = [{"type": "text", "text": text},
                   {"type": "tool_use", "id": "t1", "name": "Read", "input": {}}]
    rec = {"type": "assistant", "message": {"role": "assistant", "content": content}}
    if sidechain:
        rec["isSidechain"] = True
    return rec


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool_result():
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


def closing(question):
    """A settled previous turn whose final message ends on ``question``."""
    return [user("I am done with this module."), assistant(SUMMARY + "\n\n" + question)]


class Project:
    """A scratch bootcamp project: a progress file, optional preferences, a transcript."""

    def __init__(self, test, progress=ACTIVE, preferences=None):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "config").mkdir()
        if progress is not None:
            text = progress if isinstance(progress, str) else json.dumps(progress)
            (self.root / "config" / "bootcamp_progress.json").write_text(
                text, encoding="utf-8")
        if preferences is not None:
            (self.root / "config" / "bootcamp_preferences.yaml").write_text(
                preferences, encoding="utf-8")
        self.transcript = self.root / "transcript.jsonl"

    def write_transcript(self, records):
        self.transcript.write_text(
            "".join(json.dumps(rec) + "\n" for rec in records), encoding="utf-8")
        return str(self.transcript)

    def run(self, script, stdin):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(script)], input=stdin.encode("utf-8"),
            capture_output=True, cwd=str(self.root), env=env, timeout=60)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class HookCase(unittest.TestCase):

    def run_hook(self, project, records=None, prompt="yes", payload=None, raw=None):
        """Run the hook; return (exit code, stdout)."""
        if raw is None:
            if payload is None:
                path = project.write_transcript(records) if records is not None else ""
                payload = {"hook_event_name": "UserPromptSubmit", "prompt": prompt,
                           "transcript_path": path}
            raw = json.dumps(payload)
        code, out, err = project.run(HOOK, raw)
        self.assertNotIn("Traceback", err, "the hook raised")
        return code, out

    def assert_reminder(self, project, records=None, because="", **kw):
        """The positive control: the hook speaks, with a well-formed UserPromptSubmit
        payload. Returns the reminder text."""
        code, out = self.run_hook(project, records, **kw)
        self.assertEqual(0, code, because)
        self.assertNotEqual("", out.strip(),
                            "the hook stayed silent where it had to remind " + because)
        data = json.loads(out)
        hso = data["hookSpecificOutput"]
        self.assertEqual("UserPromptSubmit", hso["hookEventName"])
        return hso["additionalContext"]

    def assert_silent(self, project, records=None, because="", **kw):
        code, out = self.run_hook(project, records, **kw)
        self.assertEqual(0, code, "the hook must exit 0 " + because)
        self.assertEqual("", out, "the hook must write nothing to stdout " + because)


class TheTransitionQuestionTriggersTheModuleForm(HookCase):

    def test_the_reminder_names_the_module_and_every_item_in_order(self):
        text = self.assert_reminder(Project(self), closing(transition("SDK setup")))
        self.assertTrue(text.startswith("Module-start reminder. Only if this reply accepts "
                                        "starting SDK setup:"), text)
        positions = []
        for label, pattern in MODULE_ITEMS:
            match = re.search(pattern, text)
            self.assertIsNotNone(match, "the reminder omits the %s" % label)
            positions.append(match.start())
        self.assertEqual(sorted(positions), positions, "the items are out of order")
        ack = text.index("one-line acknowledgment naming SDK setup")
        self.assertLess(ack, text.index("invoke that module's skill"),
                        "the acknowledgment must come before the skill is invoked")
        self.assertLess(ack, positions[0], "the acknowledgment must come first")
        self.assertIn("SDK setup current", text, "the journey map must mark the module")
        self.assertTrue(text.endswith("Do not mention this reminder to the bootcamper."))

    def test_the_module_name_is_used_as_written(self):
        name = "Data Quality, Mapping, and Transformation"
        text = self.assert_reminder(Project(self), closing(transition(name)))
        self.assertIn("Only if this reply accepts starting %s:" % name, text)

    def test_a_string_content_message_is_read(self):
        records = [user("done"),
                   assistant(SUMMARY + "\n\n" + transition("SDK setup"), as_list=False)]
        self.assertIn("SDK setup", self.assert_reminder(Project(self), records))

    def test_the_reply_already_on_disk_is_skipped(self):
        """The prompt being submitted may be flushed before the hook runs."""
        records = closing(transition("SDK setup")) + [user("yes")]
        self.assertIn("SDK setup", self.assert_reminder(Project(self), records))

    def test_a_trailing_sidechain_record_is_skipped(self):
        records = closing(transition("SDK setup")) + [
            assistant("subagent says hello", sidechain=True)]
        self.assertIn("SDK setup", self.assert_reminder(Project(self), records))

    def test_a_malformed_transcript_line_is_skipped(self):
        project = Project(self)
        project.write_transcript(closing(transition("SDK setup")))
        with open(project.transcript, "a", encoding="utf-8") as fh:
            fh.write("{not json\n[1, 2]\n")
        payload = {"prompt": "yes", "transcript_path": str(project.transcript)}
        self.assert_reminder(project, payload=payload)

    def test_the_output_is_ascii_escaped(self):
        """No console code page can break an ASCII stream (Windows)."""
        project = Project(self)
        _code, out = self.run_hook(project, closing(transition("SDK setup")))
        out.encode("ascii")


class TheGraduationOfferTriggersTheGraduationForm(HookCase):

    def test_the_reminder_uses_the_graduation_form(self):
        project = Project(self, {"current_module": "graduation", "current_step": None})
        text = self.assert_reminder(project, closing(GRADUATION_OFFER))
        self.assertTrue(text.startswith("Module-start reminder. Only if this reply accepts "
                                        "starting Bootcamp graduation:"), text)
        positions = []
        for label, pattern in GRADUATION_ITEMS:
            match = re.search(pattern, text)
            self.assertIsNotNone(match, "the graduation form omits the %s" % label)
            positions.append(match.start())
        self.assertEqual(sorted(positions), positions)
        self.assertLess(text.index("one-line acknowledgment naming graduation"),
                        positions[0])
        self.assertIn("invoke the graduation skill", text)
        self.assertNotIn("MODULE: banner", text,
                         "graduation has its own banner, not the module banner")

    def test_the_twin_transition_gets_the_module_form(self):
        """Negative control: the same fixture with a transition question is not the
        graduation form, so the assertions above key on the offer."""
        project = Project(self, {"current_module": "graduation", "current_step": None})
        text = self.assert_reminder(project, closing(transition("SDK setup")))
        self.assertIn("MODULE: banner", text)
        self.assertNotIn("BOOTCAMP GRADUATION", text)


class ANotYetReplyCannotBecomeAModuleStart(HookCase):
    """The reply is not classified; the reminder is conditional instead."""

    def test_the_not_yet_reminder_is_conditional_only(self):
        project = Project(self)
        records = closing(transition("SDK setup"))
        text = self.assert_reminder(project, records, prompt="not yet")
        lead = "Only if this reply accepts starting SDK setup:"
        self.assertIn(lead, text)
        self.assertIn("If this reply does not accept starting SDK setup", text)
        self.assertIn("ignore this reminder", text)
        # Nothing but the label comes before the condition...
        self.assertEqual("Module-start reminder. ", text[:text.index(lead)])
        # ...and no sentence of its own commands a start unconditionally.
        for sentence in re.split(r"(?<=[.;:])\s+", text):
            self.assertNotRegex(sentence, r"(?i)^(start|begin|invoke|present|show)\b",
                                "unconditional start instruction: %r" % sentence)

    def test_the_reply_does_not_change_the_reminder(self):
        project = Project(self)
        records = closing(transition("SDK setup"))
        self.assertEqual(self.assert_reminder(project, records, prompt="yes"),
                         self.assert_reminder(project, records, prompt="not yet"))
        self.assertEqual(self.assert_reminder(project, records, prompt="yes"),
                         self.assert_reminder(project, records, prompt="noch nicht"))


class SilentCasesEachWithATwinThatSpeaks(HookCase):

    def test_no_bootcamp_active(self):
        records = closing(transition("SDK setup"))
        self.assert_reminder(Project(self), records, because="(control: module recorded)")
        for label, progress in (("no module recorded", {}),
                                ("module null", {"current_module": None}),
                                ("malformed progress", '{"current_module": '),
                                ("no progress file", None)):
            with self.subTest(case=label):
                self.assert_silent(Project(self, progress), records, because=label)

    def test_no_question_in_the_final_message(self):
        self.assert_reminder(Project(self), closing(transition("SDK setup")),
                             because="(control: the question is present)")
        self.assert_silent(Project(self), closing("Your SDK is installed."),
                           because="with no transition or graduation question")

    def test_another_pointer_question(self):
        self.assert_reminder(Project(self), closing(transition("SDK setup")),
                             because="(control: the transition question)")
        self.assert_silent(Project(self), closing(OTHER_QUESTION),
                           because="on some other pointer question")

    def test_the_transition_question_without_a_pointer(self):
        """Prose that quotes the question is not the pinned question."""
        self.assert_reminder(Project(self), closing(transition("SDK setup")))
        quoted = transition("SDK setup").replace(POINTER + " ", "")
        self.assert_silent(Project(self), closing("I will ask: " + quoted),
                           because="where the question carries no pointer")

    def test_a_later_pointer_question_overrides_an_earlier_transition(self):
        self.assert_reminder(
            Project(self), closing(OTHER_QUESTION + "\n" + transition("SDK setup")),
            because="(control: the transition question is the last pointer line)")
        self.assert_silent(
            Project(self), closing(transition("SDK setup") + "\n" + OTHER_QUESTION),
            because="where the final pointer line is another question")

    def test_missing_or_unreadable_transcript(self):
        project = Project(self)
        self.assert_reminder(project, closing(transition("SDK setup")),
                             because="(control: a readable transcript)")
        bad = project.root / "bad.jsonl"
        bad.write_bytes(b"\xff\xfe\x00 not utf-8 \xc3\x28\n")
        for label, path in (("empty path", ""),
                            ("no such file", str(project.root / "missing.jsonl")),
                            ("a directory", str(project.root)),
                            ("undecodable bytes", str(bad))):
            with self.subTest(case=label):
                self.assert_silent(project, payload={"prompt": "yes",
                                                     "transcript_path": path},
                                   because=label)
        self.assert_silent(project, payload={"prompt": "yes"},
                           because="with no transcript_path key")

    def test_malformed_payload(self):
        project = Project(self)
        path = project.write_transcript(closing(transition("SDK setup")))
        self.assert_reminder(project, payload={"transcript_path": path},
                             because="(control: a well-formed payload)")
        for label, raw in (("not JSON", "{transcript_path: "),
                           ("empty stdin", ""),
                           ("a JSON list", json.dumps([path])),
                           ("a JSON string", json.dumps(path)),
                           ("path not a string", json.dumps({"transcript_path": [path]}))):
            with self.subTest(case=label):
                self.assert_silent(project, raw=raw, because=label)

    def test_a_sidechain_question_is_not_the_users_turn(self):
        question = SUMMARY + "\n\n" + transition("SDK setup")
        self.assert_reminder(Project(self), [user("go"), assistant(question)],
                             because="(control: the same record on the main thread)")
        self.assert_silent(
            Project(self),
            [user("go"), assistant("Done."), assistant(question, sidechain=True)],
            because="where the question is in a subagent's record")

    def test_a_turn_still_settling(self):
        question = SUMMARY + "\n\n" + transition("SDK setup")
        self.assert_reminder(Project(self), [user("go"), assistant(question)],
                             because="(control: the turn ended on final text)")
        self.assert_silent(Project(self), [user("go"), assistant(question, tool_use=True)],
                           because="where the last record is a tool call")
        self.assert_silent(Project(self), [user("go"), assistant(question), tool_result()],
                           because="where the last record is a tool result")
        self.assert_silent(Project(self), [user("go")],
                           because="where nothing has been flushed")

    def test_an_apparatus_exempt_module(self):
        self.assert_reminder(Project(self), closing(transition("SDK setup")),
                             because="(control: a content module)")
        for name in ("Entity Resolution Concepts", "Bootcamp preparation"):
            with self.subTest(module=name):
                self.assert_silent(Project(self), closing(transition(name)),
                                   because="for the exempt module %s" % name)


class SessionStartAddsTheReminderOnResume(unittest.TestCase):
    """The resume clause: only when `current_step` is null and the module is not exempt."""

    def resume(self, progress, preferences=None):
        project = Project(self, progress, preferences)
        code, out, err = project.run(SESSION_START, "{}")
        self.assertEqual(0, code, err)
        self.assertNotIn("Traceback", err)
        self.assertIn("A Senzing bootcamp is in progress.", out,
                      "the resume message itself disappeared")
        return out

    def test_a_module_not_begun_gets_the_module_form(self):
        out = self.resume({"current_module": "sdk_setup", "current_step": None})
        self.assertIn("Module-start reminder: the recorded module, `sdk_setup`, has not "
                      "begun yet", out)
        self.assertIn("Only if the bootcamper accepts resuming", out)
        for label, pattern in MODULE_ITEMS:
            with self.subTest(item=label):
                self.assertRegex(out, pattern)
        self.assertIn("Do not mention this reminder to the bootcamper.", out)

    def test_an_absent_current_step_is_not_begun(self):
        """Bootcamp preparation's write records the first module and no step."""
        self.assertIn("Module-start reminder",
                      self.resume({"current_module": "business_problem"}))

    def test_a_set_current_step_adds_nothing(self):
        self.assertIn("Module-start reminder",
                      self.resume({"current_module": "sdk_setup", "current_step": None}),
                      "(control: the same module, not begun)")
        for step in (3, 0, "4a"):
            with self.subTest(current_step=step):
                self.assertNotIn("Module-start reminder", self.resume(
                    {"current_module": "sdk_setup", "current_step": step}))

    def test_graduation_gets_the_graduation_form(self):
        out = self.resume({"current_module": "graduation", "current_step": None})
        self.assertIn("Module-start reminder: Bootcamp graduation has not begun yet", out)
        for label, pattern in GRADUATION_ITEMS:
            with self.subTest(item=label):
                self.assertRegex(out, pattern)
        self.assertNotIn("MODULE: banner", out)

    def test_an_exempt_module_adds_nothing(self):
        self.assertIn("Module-start reminder",
                      self.resume({"current_module": "sdk_setup", "current_step": None}),
                      "(control: a content module)")
        for module in ("entity_resolution_concepts", "bootcamp_preparation",
                       "Entity Resolution Concepts"):
            with self.subTest(module=module):
                self.assertNotIn("Module-start reminder", self.resume(
                    {"current_module": module, "current_step": None}))

    def test_a_completed_bootcamp_adds_nothing(self):
        """After graduation, `current_module` is still graduation with no step."""
        progress = {"current_module": "graduation", "current_step": None}
        self.assertIn("Module-start reminder",
                      self.resume(progress, "name: Ada\nbootcamp_complete: false\n"),
                      "(control: not complete)")
        self.assertNotIn("Module-start reminder",
                         self.resume(progress, "name: Ada\nbootcamp_complete: true\n"))


def module_constants(path):
    """Every string constant in a script's code, docstrings excluded."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
                  and node.body and isinstance(node.body[0], ast.Expr)
                  and isinstance(node.body[0].value, ast.Constant)}
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in docstrings]


def imports_of(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


#: Phrases only the apparatus reminder carries. A second hand-written copy of the reminder
#: would carry at least one of them.
APPARATUS_PHRASES = ("journey map", "before/after", "step overview", "time-to-complete",
                     "model/effort", "Do not mention this reminder")


def copies_in(path):
    """The apparatus phrases a script's code (not its docstrings) states itself."""
    return sorted({phrase for text in module_constants(path) for phrase in APPARATUS_PHRASES
                   if phrase in text})


class TheReminderIsStatedOnce(unittest.TestCase):
    """INV-300: one builder, imported by both hooks, and no second copy in either."""

    def test_both_hooks_import_the_builder(self):
        for script in (HOOK, SESSION_START):
            with self.subTest(script=script.name):
                self.assertIn("module_start_apparatus", imports_of(script))

    def test_neither_hook_carries_a_copy(self):
        self.assertTrue(copies_in(BUILDER), "the builder no longer states the reminder")
        for script in (HOOK, SESSION_START):
            with self.subTest(script=script.name):
                self.assertEqual([], copies_in(script))

    def test_negative_control_a_pasted_copy_is_caught(self):
        source = SESSION_START.read_text(encoding="utf-8")
        mutant = source.replace("print(message)",
                                'print(message + " Present the journey map.")', 1)
        self.assertNotEqual(source, mutant, "the mutation no longer applies")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session-start.py"
            path.write_text(mutant, encoding="utf-8")
            self.assertEqual(["journey map"], copies_in(path))

    def test_the_hook_and_the_resume_share_the_apparatus_sentence(self):
        project = Project(self)
        path = project.write_transcript(closing(transition("SDK setup")))
        _code, out, _err = project.run(HOOK, json.dumps({"transcript_path": path}))
        hook_text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        _code, resume_text, _err = project.run(SESSION_START, "{}")
        shared = hook_text[hook_text.index("present the module-start apparatus"):
                           hook_text.index("If this reply")]
        self.assertIn(shared.replace("SDK setup current", "that module current"),
                      resume_text)


class TheHookIsRegisteredAndDocumented(unittest.TestCase):

    def test_hooks_json_registers_it_in_the_quoted_command_form(self):
        """INV-052: the interpreter and the quoted script in one `command` string."""
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        commands = [hook.get("command") for group in hooks.get("UserPromptSubmit", [])
                    for hook in group.get("hooks", [])]
        self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/module-start-reminder.py"',
                      commands)

    def test_the_readme_row_states_a_to_purpose_and_its_gate(self):
        """INV-016: the purpose begins with "to"; the Gate cell names `bootcamp_active()`.

        Line-scoped by design (#851): a table row is one line.
        """
        rows = [line for line in HOOKS_README.read_text(encoding="utf-8").splitlines()
                if "`scripts/module-start-reminder.py`" in line and line.startswith("| ")]
        self.assertEqual(1, len(rows), "the hook needs exactly one README row")
        cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        self.assertEqual("`UserPromptSubmit`", cells[0])
        self.assertTrue(cells[2].startswith("to "), cells[2])
        self.assertTrue(cells[3].startswith("`bootcamp_active()`:"), cells[3])

    def test_the_scripts_use_only_the_standard_library(self):
        siblings = {path.stem for path in SCRIPTS.glob("*.py")}
        stdlib = set(getattr(sys, "stdlib_module_names", ()))
        if not stdlib:
            self.skipTest("sys.stdlib_module_names needs Python 3.10+")
        for script in (HOOK, BUILDER):
            with self.subTest(script=script.name):
                self.assertEqual(set(), imports_of(script) - stdlib - siblings)


if __name__ == "__main__":
    unittest.main()
