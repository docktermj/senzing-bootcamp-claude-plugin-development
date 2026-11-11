"""After a reply shows a module number, the guide is reminded to name modules by name.

Enforces INV-425 (registered by the maintainer 2026-11-10). It runs the hook as a subprocess; it
cannot establish that a live guide stops showing numbers, which an `auto-test` walk observes.

Issue #874: two `auto-test` walks raised BREAKING INV-079-module-number findings ("Module 5",
"Module 4", "Module 2") although the guide had read `ground-rules.md`'s INV-079 bullet first.
A rule already read did not hold, so `scripts/module-number-reminder.py` (`UserPromptSubmit`)
reads the guide's previous turn and, when any of its assistant text shows a module number,
puts a silent reminder into the guide's context before the next reply. It never blocks.

What this file pins:

- **The reminder** quotes each hit, tells the guide to name modules by name from now on, and
  tells it not to correct or apologize for the earlier reply and not to mention the reminder.
- **Every assistant text of the previous turn is scanned**, not only the final message: walk 1
  showed "Before I record Module 5 as complete" in a text block before a tool call. Fenced code
  is scanned too. Sidechain and meta records, earlier turns and the Bootcamper's own prompt are
  not.
- **The gates**: the progress file's existence (not `bootcamp_active()`), a bootcamp not
  complete, a readable, settled previous turn, and a match. Every silent case runs its twin
  first, the same fixture with only the triggering element changed, and requires the reminder
  from it, so a hook that is silent because it is broken cannot pass a silence assertion.
- **One pattern**: the hook's `MODULE_NUMBER` equals the pattern
  `transcript_lint.check_module_numbers` compiles, read from both sources.
- **One reader**: the hook reads the transcript through `transition_reply.previous_turn_texts`
  and carries no reader of its own.

Negative controls (INV-265), each run against a mutated copy of the hook: one that ignores a
match, one that scans only the final message, one whose pattern differs from the linter's, and
one that quotes a hit split across a line break without collapsing its whitespace. Each must
fail a check here.

The hook reads its payload from stdin and resolves `config/` against the working directory, so
each case runs it as a subprocess in a temp project, the way Claude Code invokes it. Standard
library only; nothing under `plugins/` is imported (INV-108). It cannot establish that a live
guide stops writing module numbers once reminded; only a live walk (`auto-test --seed mid`)
observes that.

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
HOOK = SCRIPTS / "module-number-reminder.py"
READER = SCRIPTS / "transition_reply.py"
HOOKS_JSON = PLUGIN / "hooks" / "hooks.json"
HOOKS_README = PLUGIN / "hooks" / "README.md"
LINTER = REPO_ROOT / ".claude" / "skills" / "auto-test" / "transcript_lint.py"

ACTIVE = {"current_module": "data_quality_mapping", "current_step": 11}
CLEAN = "Profiling is done. Next we map the CUSTOMERS file."
LEAK = "Module 5 is partly done, so we pick up at the mapping step."


def assistant(text, *, as_list=True, sidechain=False, meta=False, tool_use=False):
    content = [{"type": "text", "text": text}] if as_list else text
    if tool_use:
        content = [{"type": "text", "text": text},
                   {"type": "tool_use", "id": "t1", "name": "Read", "input": {}}]
    rec = {"type": "assistant", "message": {"role": "assistant", "content": content}}
    if sidechain:
        rec["isSidechain"] = True
    if meta:
        rec["isMeta"] = True
    return rec


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool_result():
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


def turn(*texts):
    """A settled previous turn: a prompt, then one assistant record per text."""
    return [user("yes, continue")] + [assistant(text) for text in texts]


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
        # A mutated copy runs from a temp directory, so its siblings come from PYTHONPATH.
        env["PYTHONPATH"] = str(SCRIPTS)
        proc = subprocess.run(
            [sys.executable, str(script)], input=stdin.encode("utf-8"),
            capture_output=True, cwd=str(self.root), env=env, timeout=60)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


def mutant(test, replacements):
    """A copy of the hook with each ``(old, new)`` applied once; fails if one no longer
    applies, so a negative control cannot pass by mutating nothing."""
    source = HOOK.read_text(encoding="utf-8")
    for old, new in replacements:
        test.assertIn(old, source, "the mutation no longer applies: %r" % old)
        source = source.replace(old, new, 1)
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    path = Path(tmp.name) / HOOK.name
    path.write_text(source, encoding="utf-8")
    return path


class HookCase(unittest.TestCase):

    def run_hook(self, project, records=None, payload=None, raw=None, script=HOOK):
        """Run the hook; return (exit code, stdout)."""
        if raw is None:
            if payload is None:
                path = project.write_transcript(records) if records is not None else ""
                payload = {"hook_event_name": "UserPromptSubmit", "prompt": "yes",
                           "transcript_path": path}
            raw = json.dumps(payload)
        code, out, err = project.run(script, raw)
        self.assertNotIn("Traceback", err, "the hook raised")
        return code, out

    def reminder_from(self, project, records=None, script=HOOK, **kw):
        """The reminder text, or None when the hook stayed silent."""
        code, out = self.run_hook(project, records, script=script, **kw)
        self.assertEqual(0, code, "the hook must exit 0")
        if out == "":
            return None
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual("UserPromptSubmit", hso["hookEventName"])
        self.assertNotIn("decision", json.loads(out), "the hook must never block")
        return hso["additionalContext"]

    def assert_reminder(self, project, records=None, because="", **kw):
        text = self.reminder_from(project, records, **kw)
        self.assertIsNotNone(text, "the hook stayed silent where it had to remind " + because)
        return text

    def assert_silent(self, project, records=None, because="", **kw):
        code, out = self.run_hook(project, records, **kw)
        self.assertEqual(0, code, "the hook must exit 0 " + because)
        self.assertEqual("", out, "the hook must write nothing to stdout " + because)


class ALeakGetsTheReminder(HookCase):

    def test_the_reminder_quotes_the_hit_and_says_what_to_do(self):
        text = self.assert_reminder(Project(self), turn(LEAK))
        self.assertIn('"Module 5"', text, "the reminder must quote the hit")
        self.assertIn("From now on name every module by its name", text)
        self.assertIn("never by a number (INV-079)", text)
        self.assertIn("Do not correct or apologize for the earlier reply", text)
        self.assertIn("do not mention this reminder to the bootcamper", text)
        self.assertIsNone(re.search(r"\bModule\s+\d+\b", text.replace('"Module 5"', "")),
                          "the reminder itself must name no other module number")

    def test_every_distinct_hit_is_quoted_once_in_order(self):
        text = self.assert_reminder(Project(self), turn(
            "Module 5 is partly done.", "Re-running SDK setup (Module 2) first, then Module 5."))
        self.assertIn('("Module 5", "Module 2")', text)

    def test_a_hit_before_a_tool_call_is_read(self):
        """Walk 1: "Before I record Module 5 as complete" sat in an intermediate block."""
        records = [user("done"),
                   assistant("Before I record Module 5 as complete, one check.", tool_use=True),
                   tool_result(),
                   assistant(CLEAN)]
        self.assertIn('"Module 5"', self.assert_reminder(Project(self), records))

    def test_a_hit_inside_a_fenced_block_is_read(self):
        fenced = "Here is your status:\n\n```\nCurrent: Module 5 (mapping)\n```\n"
        self.assert_reminder(Project(self), turn(fenced))

    def test_a_string_content_message_is_read(self):
        self.assert_reminder(Project(self), [user("go"), assistant(LEAK, as_list=False)])

    def test_a_wrapped_hit_is_quoted_on_one_line(self):
        """A hit split across a line break or a run of whitespace is quoted as the
        Bootcamper read it, "Module 5", and counts as the same hit as one written plainly."""
        for gap in ("\n", "\r\n", " \t "):
            with self.subTest(gap=repr(gap)):
                text = self.assert_reminder(
                    Project(self), turn("We finished Module%s5 earlier." % gap))
                self.assertIn('("Module 5")', text)
        text = self.assert_reminder(Project(self), turn("Module\n5 first.", "Then Module 5."))
        self.assertIn('("Module 5")', text, "a wrapped and a plain hit are one hit")

    def test_an_empty_progress_file_still_counts(self):
        """Existence, not bootcamp_active(): the preface and Bootcamp preparation name
        modules before any module is recorded."""
        self.assert_reminder(Project(self, progress="{}"), turn(LEAK))
        self.assert_reminder(Project(self, progress=""), turn(LEAK))

    def test_the_reminder_repeats_on_every_turn_that_shows_a_number(self):
        project = Project(self)
        first = self.assert_reminder(project, turn(LEAK))
        second = self.assert_reminder(project, turn(LEAK) + turn(LEAK))
        self.assertEqual(first, second, "no state is kept between turns")

    def test_the_output_is_ascii_escaped(self):
        _code, out = self.run_hook(Project(self), turn("Module 5 — done \U0001f449"))
        self.assertTrue(out.isascii(), out)


class SilentCasesEachWithATwinThatSpeaks(HookCase):

    def test_no_progress_file(self):
        self.assert_reminder(Project(self), turn(LEAK), "(control: a bootcamp project)")
        self.assert_silent(Project(self, progress=None), turn(LEAK), "outside a bootcamp")

    def test_a_completed_bootcamp(self):
        self.assert_reminder(Project(self, preferences="bootcamp_complete: false\n"),
                             turn(LEAK), "(control: not complete)")
        self.assert_silent(Project(self, preferences="bootcamp_complete: true\n"),
                           turn(LEAK), "after graduation")

    def test_no_module_number(self):
        self.assert_reminder(Project(self), turn(LEAK), "(control: a number)")
        for text in (CLEAN, "Data Quality, Mapping, and Transformation is partly done.",
                     "module 5 in lower case", "Modules 5 and 6", "Module five",
                     "MODULE: DATA QUALITY, MAPPING, AND TRANSFORMATION"):
            with self.subTest(text=text):
                self.assert_silent(Project(self), turn(text), "with no module number")

    def test_a_number_only_in_an_earlier_turn(self):
        self.assert_reminder(Project(self), turn(CLEAN) + turn(LEAK), "(control: last turn)")
        self.assert_silent(Project(self), turn(LEAK) + turn(CLEAN), "for an earlier turn")

    def test_a_number_only_in_a_sidechain_or_meta_record(self):
        for flag in ("sidechain", "meta"):
            with self.subTest(record=flag):
                self.assert_reminder(Project(self), [user("go"), assistant(LEAK),
                                                     assistant(CLEAN)],
                                     "(control: a user-facing record)")
                self.assert_silent(Project(self), [user("go"),
                                                   assistant(LEAK, **{flag: True}),
                                                   assistant(CLEAN)],
                                   "for a %s record" % flag)

    def test_a_number_only_in_the_bootcamper_prompt(self):
        self.assert_reminder(Project(self), turn(LEAK) + [user("ok")],
                             "(control: the guide wrote it)")
        self.assert_silent(Project(self), turn(CLEAN) + [user("Is Module 5 done?")],
                           "for the prompt being submitted")

    def test_a_turn_still_settling(self):
        self.assert_reminder(Project(self), turn(LEAK), "(control: settled)")
        self.assert_silent(Project(self), [user("go"), assistant(LEAK, tool_use=True)],
                           "while the turn ends on a tool call")
        self.assert_silent(Project(self), [user("go"), assistant(LEAK, tool_use=True),
                                           tool_result()],
                           "while the turn ends on a tool result")

    def test_missing_or_unreadable_transcript(self):
        project = Project(self)
        self.assert_reminder(project, turn(LEAK), "(control: readable)")
        for path in ("", str(project.root / "nope.jsonl"), str(project.root)):
            with self.subTest(path=path):
                self.assert_silent(project, payload={"transcript_path": path})
        bad = project.root / "bad.jsonl"
        bad.write_bytes(b"\xff\xfe not utf-8 Module 5\n")
        self.assert_silent(project, payload={"transcript_path": str(bad)})

    def test_malformed_payload(self):
        project = Project(self)
        self.assert_reminder(project, turn(LEAK), "(control: well-formed)")
        for raw in ("", "not json", "[]", '"a string"', '{"transcript_path": 7}'):
            with self.subTest(raw=raw):
                self.assert_silent(project, raw=raw)


def compiled_pattern(node):
    """``(pattern, flags source)`` of a ``re.compile(...)`` call node, else None."""
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "compile" and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "re" and node.args
            and isinstance(node.args[0], ast.Constant)):
        flags = [ast.unparse(arg) for arg in node.args[1:]]
        flags += [ast.unparse(kw.value) for kw in node.keywords if kw.arg == "flags"]
        return node.args[0].value, tuple(flags)
    return None


def linter_pattern(source):
    """The pattern ``check_module_numbers`` compiles, read from the linter's source."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == "check_module_numbers":
            found = [compiled_pattern(n) for n in ast.walk(node)]
            found = [f for f in found if f]
            return found[0] if len(found) == 1 else None
    return None


def hook_pattern(source):
    """The hook's ``MODULE_NUMBER``, read from its source."""
    for node in ast.parse(source).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "MODULE_NUMBER"):
            return compiled_pattern(node.value)
    return None


class TheHookAndTheLinterShareOnePattern(unittest.TestCase):

    def test_both_patterns_are_found(self):
        self.assertIsNotNone(linter_pattern(LINTER.read_text(encoding="utf-8")),
                             "check_module_numbers no longer compiles one readable pattern")
        self.assertIsNotNone(hook_pattern(HOOK.read_text(encoding="utf-8")),
                             "the hook no longer defines MODULE_NUMBER with re.compile")

    def test_the_patterns_are_equal(self):
        self.assertEqual(linter_pattern(LINTER.read_text(encoding="utf-8")),
                         hook_pattern(HOOK.read_text(encoding="utf-8")),
                         "the hook and transcript_lint disagree on what a module number is")

    def test_negative_control_a_different_pattern_is_caught(self):
        source = HOOK.read_text(encoding="utf-8")
        for old, new in ((r're.compile(r"\bModule\s+\d+\b")', r're.compile(r"\bModule\s+\d\b")'),
                         (r're.compile(r"\bModule\s+\d+\b")',
                          r're.compile(r"\bModule\s+\d+\b", re.I)')):
            with self.subTest(mutation=new):
                self.assertIn(old, source, "the mutation no longer applies")
                self.assertNotEqual(linter_pattern(LINTER.read_text(encoding="utf-8")),
                                    hook_pattern(source.replace(old, new, 1)))


class NegativeControls(HookCase):
    """INV-265: each check above turns red on the defect it guards against."""

    def test_a_hook_that_ignores_a_match_is_caught(self):
        broken = mutant(self, [("if not hits:\n    sys.exit(0)", "if True:\n    sys.exit(0)")])
        self.assertIsNotNone(self.reminder_from(Project(self), turn(LEAK)), "(control)")
        self.assertIsNone(self.reminder_from(Project(self), turn(LEAK), script=broken),
                          "the mutant still reminded, so the positive cases cannot see it")

    def test_a_hook_that_scans_only_the_final_message_is_caught(self):
        broken = mutant(self, [("texts = transition_reply.previous_turn_texts(payload)\n",
                                "texts = transition_reply.previous_turn_texts(payload)\n"
                                "texts = texts[-1:] if texts else texts\n")])
        records = [user("done"),
                   assistant("Before I record Module 5 as complete, one check.", tool_use=True),
                   tool_result(),
                   assistant(CLEAN)]
        self.assertIsNotNone(self.reminder_from(Project(self), records), "(control)")
        self.assertIsNone(self.reminder_from(Project(self), records, script=broken),
                          "a final-only scan still found the intermediate hit")

    def test_a_hook_that_quotes_a_wrapped_hit_raw_is_caught(self):
        broken = mutant(self, [('hit = " ".join(match.group(0).split())',
                                "hit = match.group(0)")])
        records = turn("We finished Module\n5 earlier.")
        self.assertIn('"Module 5"', self.assert_reminder(Project(self), records), "(control)")
        self.assertNotIn('"Module 5"', self.assert_reminder(Project(self), records,
                                                           script=broken),
                         "a hook quoting the raw match still quoted the hit on one line, so "
                         "test_a_wrapped_hit_is_quoted_on_one_line cannot see the collapse")


#: The transcript reader's own function names. A hook that defines one carries a second
#: reader, which a fix to the shared one would not reach.
READER_NAMES = ("read_records", "previous_turn", "previous_texts", "previous_final_text",
                "is_real_user_prompt", "ends_with_tool_use", "message_text", "content_of")


def defined_names(source):
    return {node.name for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def imports_of(source):
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def second_reader(source):
    """What a hook carries of a transcript reader: a reader function name, or an ``open``."""
    found = sorted(defined_names(source) & set(READER_NAMES))
    calls = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "open"]
    if calls:
        found.append("open")
    return found


class TheHookSharesTheTranscriptReader(unittest.TestCase):

    def test_the_reader_defines_what_this_test_looks_for(self):
        self.assertEqual(set(), set(READER_NAMES) - defined_names(
            READER.read_text(encoding="utf-8")))

    def test_the_hook_imports_the_reader_and_carries_no_copy(self):
        source = HOOK.read_text(encoding="utf-8")
        self.assertIn("transition_reply", imports_of(source))
        self.assertEqual([], second_reader(source))

    def test_negative_control_a_pasted_reader_is_caught(self):
        source = HOOK.read_text(encoding="utf-8")
        pasted = source.replace(
            "def hits_in(texts):",
            "def read_records(path):\n    with open(path) as fh:\n        return fh.read()\n\n\n"
            "def hits_in(texts):", 1)
        self.assertNotEqual(source, pasted, "the mutation no longer applies")
        self.assertEqual(["read_records", "open"], second_reader(pasted))


class TheHookIsRegisteredAndDocumented(unittest.TestCase):

    def test_hooks_json_registers_it_in_the_quoted_command_form(self):
        """INV-052: the interpreter and the quoted script in one `command` string."""
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        commands = [hook.get("command") for group in hooks.get("UserPromptSubmit", [])
                    for hook in group.get("hooks", [])]
        self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/module-number-reminder.py"',
                      commands)

    def test_the_readme_row_states_a_to_purpose_and_its_gate(self):
        """INV-016: the purpose begins with "to"; the Gate cell says Existence and why.
        Line-scoped by design (#874): a table row is one line."""
        rows = [line for line in HOOKS_README.read_text(encoding="utf-8").splitlines()
                if "`scripts/module-number-reminder.py`" in line and line.startswith("| ")]
        self.assertEqual(1, len(rows), "the hook needs exactly one README row")
        cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        self.assertEqual("`UserPromptSubmit`", cells[0])
        self.assertTrue(cells[2].startswith("to "), cells[2])
        self.assertIn("INV-079", cells[2])
        self.assertIn("never blocks", cells[2])
        self.assertTrue(cells[3].startswith("Existence:"), cells[3])

    def test_the_hook_uses_only_the_standard_library(self):
        siblings = {path.stem for path in SCRIPTS.glob("*.py")}
        stdlib = set(getattr(sys, "stdlib_module_names", ()))
        if not stdlib:
            self.skipTest("sys.stdlib_module_names needs Python 3.10+")
        for script in (HOOK, READER):
            with self.subTest(script=script.name):
                self.assertEqual(set(), imports_of(script.read_text(encoding="utf-8"))
                                 - stdlib - siblings)


if __name__ == "__main__":
    unittest.main()
