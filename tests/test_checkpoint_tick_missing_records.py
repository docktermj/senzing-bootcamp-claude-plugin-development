"""`checkpoint-tick.py` names a record module completion left missing, on a transition reply.

Issue #858 (a sub-issue of #855): module completion's Step 0 (#856) catches a required step
that never ran, but only the model's attention makes Step 0 itself run. On the Bootcamper's
reply to the transition question or the graduation offer, the `UserPromptSubmit` hook
`scripts/checkpoint-tick.py` reads `config/bootcamp_progress.json` and names the two
records that can still be repaired once the module has closed:

- `directing_steps.<token>` unset for a directing module in `modules_completed`;
- a `steer_triggers` entry with `"kind": "reversal"` and `"filed": false`.

It tells the guide to repair each silently. It never blocks. The reply is detected by
`scripts/transition_reply.py`, the one detector `module-start-reminder.py` (#851) also uses;
`TheTransitionIsDetectedOnce` reads both hooks for a second copy.

**Every silent case has a twin that speaks.** A hook that is silent because it is broken
satisfies every silence assertion on its own, so each silent case below runs the same
fixture with only the triggering element changed and requires the reminder from it first
(the shape `tests/test_module_start_reminder.py` uses).

The hook reads its payload from stdin and resolves `config/` and `docs/` against the working
directory, so each case runs it as a subprocess in a temp project, the way Claude Code
invokes it. Standard library only; nothing under `plugins/` is imported (INV-108).

Enforces **INV-354**'s 2026-11-05 note (#858: the guide records `skipped` on this hook's reminder):
it runs the hook against scratch projects and cannot establish that a live guide makes the repair,
which only a live walk (`auto-test` or `dry-run` phase 3) observes.

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
TICK = SCRIPTS / "checkpoint-tick.py"
REMINDER_HOOK = SCRIPTS / "module-start-reminder.py"
DETECTOR = SCRIPTS / "transition_reply.py"
HOOKS_README = PLUGIN / "hooks" / "README.md"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"

POINTER = "\U0001f449"
LABEL = "Module-completion records still missing"
ANNOUNCEMENT = "in-progress recap checkpoint now exists"

TRANSITION = "%s **Are you ready to move on to the next module: Data processing?**" % POINTER
GRADUATION_OFFER = ("%s **Would you like to graduate now and generate your production "
                    "project and recap?**" % POINTER)
OTHER_QUESTION = "%s **Which records would you like to look up?**" % POINTER


def assistant(text):
    return {"type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def closing(question):
    """A settled previous turn whose final message ends on ``question``."""
    return [user("Done."), assistant("**Module complete**\n\nWhat you accomplished: ...\n\n"
                                     + question)]


def reversal(filed, evidence="match-key audit: ADDR_FULL routed to payload"):
    return {"kind": "reversal", "evidence": evidence, "filed": filed}


def failure():
    return {"kind": "failure", "evidence": "EMPTY: nothing matched"}


def progress(**overrides):
    """A progress file after Data Quality, Mapping, and Transformation has closed with its
    directing step recorded and nothing missing."""
    data = {
        "current_module": "data_processing",
        "current_step": None,
        "modules_completed": ["sdk_setup", "data_collection", "data_quality_mapping"],
        "directing_steps": {"data_quality_mapping": "directed"},
        "steer_triggers": {"data_quality_mapping": [failure()]},
    }
    data.update(overrides)
    return data


class Project:
    """A scratch bootcamp project with a progress file, a transcript, and a checkpoint that
    already exists, so the once-per-session announcement stays out of the way unless a case
    asks for it."""

    def __init__(self, test, progress_data, checkpoint=True):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "config").mkdir()
        text = (progress_data if isinstance(progress_data, str)
                else json.dumps(progress_data))
        (self.root / "config" / "bootcamp_progress.json").write_text(text, encoding="utf-8")
        if checkpoint:
            (self.root / "docs" / "progress").mkdir(parents=True)
            (self.root / "docs" / "progress" / "recap_checkpoint.md").write_text(
                "<!-- RECAP-CHECKPOINT:SCAFFOLD -->\n", encoding="utf-8")
        self.transcript = self.root / "transcript.jsonl"

    def run(self, records=None, raw=None):
        if raw is None:
            path = ""
            if records is not None:
                self.transcript.write_text(
                    "".join(json.dumps(rec) + "\n" for rec in records), encoding="utf-8")
                path = str(self.transcript)
            raw = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "yes",
                              "transcript_path": path})
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(TICK)], input=raw.encode("utf-8"), capture_output=True,
            cwd=str(self.root), env=env, timeout=60)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class TickCase(unittest.TestCase):

    def context(self, project, records=None, **kw):
        """Run the hook; return its additionalContext, or "" when stdout is empty."""
        code, out, err = project.run(records, **kw)
        self.assertNotIn("Traceback", err, "the hook raised")
        self.assertEqual(0, code, "the hook must exit 0, never block")
        if out == "":
            return ""
        data = json.loads(out)
        hso = data["hookSpecificOutput"]
        self.assertEqual("UserPromptSubmit", hso["hookEventName"])
        self.assertEqual({"hookSpecificOutput"}, set(data), "stdout carries only the payload")
        return hso["additionalContext"]

    def assert_reminder(self, project, records=None, because="", **kw):
        text = self.context(project, records, **kw)
        self.assertIn(LABEL, text, "the hook stayed silent where it had to remind " + because)
        return text

    def assert_silent(self, project, records=None, because="", **kw):
        code, out, err = project.run(records, **kw)
        self.assertNotIn("Traceback", err, "the hook raised " + because)
        self.assertEqual(0, code, "the hook must exit 0 " + because)
        self.assertEqual("", out, "the hook must write nothing to stdout " + because)


class AnUnsetDirectingStepIsNamed(TickCase):

    def test_a_completed_directing_module_with_no_value(self):
        project = Project(self, progress(directing_steps={}))
        text = self.assert_reminder(project, closing(TRANSITION))
        self.assertIn("directing_steps.data_quality_mapping is unset", text)
        self.assertIn("set each unset directing_steps value named above to skipped", text)
        self.assertIn("do not run the directing step late", text)
        self.assertNotIn("Silent in-run append", text, "no reversal is missing")

    def test_an_absent_directing_steps_key_counts_as_unset(self):
        data = progress()
        del data["directing_steps"]
        text = self.assert_reminder(Project(self, data), closing(TRANSITION))
        self.assertIn("directing_steps.data_quality_mapping is unset", text)

    def test_every_completed_directing_module_is_checked(self):
        data = progress(
            modules_completed=["data_quality_mapping", "data_processing",
                               "query_visualize_discover"],
            directing_steps={"data_processing": "guide_chose"})
        text = self.assert_reminder(Project(self, data), closing(GRADUATION_OFFER))
        self.assertIn("directing_steps.data_quality_mapping is unset", text)
        self.assertIn("directing_steps.query_visualize_discover is unset", text)
        self.assertNotIn("directing_steps.data_processing", text)

    def test_every_recorded_value_counts_as_set(self):
        for value in ("directed", "guide_chose", "none", "skipped"):
            with self.subTest(value=value):
                data = progress(directing_steps={"data_quality_mapping": value})
                self.assert_silent(Project(self, data), closing(TRANSITION))


class AnUnfiledReversalIsNamed(TickCase):

    def test_an_unfiled_reversal_in_any_module(self):
        data = progress(steer_triggers={"sdk_setup": [reversal(False)]})
        text = self.assert_reminder(Project(self, data), closing(TRANSITION))
        self.assertIn('steer_triggers.sdk_setup has a reversal with "filed": false', text)
        self.assertIn("match-key audit: ADDR_FULL routed to payload", text)
        self.assertIn('feedback.md -> "Silent in-run append"', text)
        self.assertIn("INV-373", text)
        self.assertNotIn("directing_steps", text, "no directing step is missing")

    def test_long_evidence_is_shortened(self):
        data = progress(steer_triggers={"sdk_setup": [reversal(False, "x" * 500)]})
        text = self.assert_reminder(Project(self, data), closing(TRANSITION))
        self.assertIn("x" * 200 + "...", text)
        self.assertNotIn("x" * 201, text)

    def test_both_kinds_together_and_the_repair_order(self):
        data = progress(directing_steps={},
                        steer_triggers={"data_quality_mapping": [failure(), reversal(False)]})
        text = self.assert_reminder(Project(self, data), closing(TRANSITION))
        self.assertLess(text.index("set each unset directing_steps"),
                        text.index("file each unfiled reversal"))

    def test_the_reminder_says_silent_no_question_and_no_recap_rewrite(self):
        data = progress(steer_triggers={"sdk_setup": [reversal(False)]})
        text = self.assert_reminder(Project(self, data), closing(TRANSITION))
        self.assertIn("silently and before anything else in this turn", text)
        self.assertIn("Ask no question for this, do not mention it to the bootcamper", text)
        self.assertIn("do not rewrite any completed recap section", text)


class TheReplyIsNotClassified(TickCase):
    """Module completion's Step 1 has closed the module whatever the answer (INV-413), so
    a "not yet" gets the same reminder as a yes."""

    def test_a_not_yet_reply_gets_the_same_reminder(self):
        project = Project(self, progress(directing_steps={}))
        records = closing(TRANSITION)
        yes = self.assert_reminder(project, records + [user("yes")])
        not_yet = self.assert_reminder(project, records + [user("not yet")])
        self.assertEqual(yes, not_yet)


class SilentCasesEachWithATwinThatSpeaks(TickCase):

    def test_nothing_missing(self):
        self.assert_reminder(Project(self, progress(directing_steps={})), closing(TRANSITION),
                             because="(twin: the directing step unset)")
        self.assert_silent(Project(self, progress()), closing(TRANSITION))

    def test_no_bootcamp_active(self):
        self.assert_reminder(Project(self, progress(directing_steps={})), closing(TRANSITION),
                             because="(twin: a module recorded)")
        self.assert_silent(Project(self, progress(directing_steps={}, current_module=None)),
                           closing(TRANSITION))

    def test_not_a_transition_reply(self):
        project = Project(self, progress(directing_steps={}))
        self.assert_reminder(project, closing(TRANSITION), because="(twin: the transition)")
        self.assert_silent(project, closing(OTHER_QUESTION))
        self.assert_silent(project, closing("No question at all."))

    def test_the_graduation_offer_is_a_transition(self):
        project = Project(self, progress(directing_steps={}))
        self.assert_reminder(project, closing(GRADUATION_OFFER))

    def test_a_directing_module_not_yet_completed(self):
        self.assert_reminder(Project(self, progress(directing_steps={})), closing(TRANSITION),
                             because="(twin: the module completed)")
        data = progress(directing_steps={},
                        modules_completed=["sdk_setup", "data_collection"])
        self.assert_silent(Project(self, data), closing(TRANSITION))

    def test_a_reversal_already_filed(self):
        self.assert_reminder(
            Project(self, progress(steer_triggers={"sdk_setup": [reversal(False)]})),
            closing(TRANSITION), because="(twin: filed false)")
        self.assert_silent(
            Project(self, progress(steer_triggers={"sdk_setup": [reversal(True)]})),
            closing(TRANSITION))

    def test_a_failure_entry(self):
        self.assert_reminder(
            Project(self, progress(steer_triggers={"data_processing": [reversal(False)]})),
            closing(TRANSITION), because="(twin: a reversal)")
        self.assert_silent(
            Project(self, progress(steer_triggers={"data_processing": [failure()]})),
            closing(TRANSITION))
        # A failure entry carries no `filed`; one that wrongly does is still not a reversal.
        malformed = dict(failure(), filed=False)
        self.assert_silent(
            Project(self, progress(steer_triggers={"data_processing": [malformed]})),
            closing(TRANSITION), because="(a failure entry with filed: false)")

    def test_a_bad_progress_file(self):
        self.assert_reminder(Project(self, progress(directing_steps={})), closing(TRANSITION),
                             because="(twin: a readable progress file)")
        cases = {
            "malformed JSON": '{"current_module": "data_processing", ',
            "not an object": "[]",
            "modules_completed not a list": progress(directing_steps={},
                                                     modules_completed="data_quality_mapping"),
            "directing_steps not an object": progress(directing_steps=["data_quality_mapping"]),
            "steer_triggers not an object": progress(steer_triggers=[reversal(False)]),
            "an entry list not a list": progress(steer_triggers={"sdk_setup": reversal(False)}),
            "an entry not an object": progress(steer_triggers={"sdk_setup": ["reversal"]}),
            "filed not a boolean": progress(steer_triggers={"sdk_setup": [
                {"kind": "reversal", "evidence": "e", "filed": "false"}]}),
            "filed zero": progress(steer_triggers={"sdk_setup": [
                {"kind": "reversal", "evidence": "e", "filed": 0}]}),
            "filed absent": progress(steer_triggers={"sdk_setup": [
                {"kind": "reversal", "evidence": "e"}]}),
        }
        for name, data in cases.items():
            with self.subTest(case=name):
                self.assert_silent(Project(self, data), closing(TRANSITION), because=name)

    def test_an_undecided_payload_or_transcript(self):
        project = Project(self, progress(directing_steps={}))
        self.assert_reminder(project, closing(TRANSITION), because="(twin: a readable turn)")
        self.assert_silent(project, raw="not json")
        self.assert_silent(project, raw="[]")
        self.assert_silent(project, raw=json.dumps({"transcript_path": 7}))
        self.assert_silent(project, raw=json.dumps(
            {"transcript_path": str(project.root / "missing.jsonl")}))
        settling = closing(TRANSITION) + [{"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}]
        self.assert_silent(project, settling)


class TheAnnouncementKeepsItsBehavior(TickCase):

    def test_the_announcement_alone_on_its_first_turn(self):
        project = Project(self, progress(), checkpoint=False)
        text = self.context(project, closing(OTHER_QUESTION))
        self.assertIn(ANNOUNCEMENT, text)
        self.assertNotIn(LABEL, text)
        self.assertEqual("", self.context(project, closing(OTHER_QUESTION)),
                         "the announcement is once per session")

    def test_both_on_one_turn_share_one_payload(self):
        project = Project(self, progress(directing_steps={}), checkpoint=False)
        text = self.context(project, closing(TRANSITION))
        self.assertIn(ANNOUNCEMENT, text)
        self.assertIn(LABEL, text)
        self.assertLess(text.index(ANNOUNCEMENT), text.index(LABEL))

    def test_the_output_is_ascii_escaped(self):
        data = progress(steer_triggers={"sdk_setup": [reversal(False, "café \U0001f449")]})
        _code, out, _err = Project(self, data).run(closing(TRANSITION))
        self.assertTrue(out.isascii(), "the JSON on stdout must be ASCII-escaped")


#: The detector's own definitions. A hook that defines any of them again carries a second
#: detector.
DETECTOR_NAMES = ("previous_final_text", "offered_module", "offered_module_in",
                  "read_records", "is_real_user_prompt", "ends_with_tool_use")
TRANSITION_PHRASE = "Are you ready to move on to the next module"


def defined_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def code_strings(path):
    """String constants in a script's code, docstrings excluded."""
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


def second_detector(path):
    """What a script carries of the detector itself: its function names, or the pinned
    transition phrase in a code string."""
    found = sorted(defined_names(path) & set(DETECTOR_NAMES))
    if any(TRANSITION_PHRASE in text for text in code_strings(path)):
        found.append(TRANSITION_PHRASE)
    return found


class TheTransitionIsDetectedOnce(unittest.TestCase):
    """#858: one detector, imported by both hooks that act on a transition reply."""

    def test_both_hooks_import_the_detector(self):
        for script in (TICK, REMINDER_HOOK):
            with self.subTest(script=script.name):
                self.assertIn("transition_reply", imports_of(script))

    def test_neither_hook_carries_a_copy(self):
        self.assertEqual(sorted(DETECTOR_NAMES + (TRANSITION_PHRASE,)),
                         sorted(second_detector(DETECTOR)),
                         "the detector no longer holds what this test looks for")
        for script in (TICK, REMINDER_HOOK):
            with self.subTest(script=script.name):
                self.assertEqual([], second_detector(script))

    def test_negative_control_a_pasted_copy_is_caught(self):
        source = TICK.read_text(encoding="utf-8")
        mutant = source.replace(
            "def _progress():",
            "def previous_final_text(records):\n    return None\n\n\ndef _progress():", 1)
        self.assertNotEqual(source, mutant, "the mutation no longer applies")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint-tick.py"
            path.write_text(mutant, encoding="utf-8")
            self.assertEqual(["previous_final_text"], second_detector(path))

    def test_the_scripts_use_only_the_standard_library(self):
        siblings = {path.stem for path in SCRIPTS.glob("*.py")}
        stdlib = set(getattr(sys, "stdlib_module_names", ()))
        if not stdlib:
            self.skipTest("sys.stdlib_module_names needs Python 3.10+")
        for script in (TICK, DETECTOR):
            with self.subTest(script=script.name):
                self.assertEqual(set(), imports_of(script) - stdlib - siblings)


class TheRuleAndTheReadmeSayIt(unittest.TestCase):

    def test_ground_rules_names_the_late_skipped_record(self):
        text = re.sub(r"\s+", " ", GROUND_RULES.read_text(encoding="utf-8"))
        self.assertIn("Only module completion writes it", text)
        self.assertIn("When module completion closed a module and left the value unset, "
                      "`checkpoint-tick.py`'s reminder at the next reply to the transition "
                      "question or graduation offer has the guide record `skipped` then, "
                      "silently and without running the step late (#858).", text)

    def test_the_readme_row_names_the_reminder_and_keeps_its_gate(self):
        """INV-016: the purpose begins with "to"; the Gate cell names `bootcamp_active()`.

        Line-scoped by design (#858): a table row is one line.
        """
        rows = [line for line in HOOKS_README.read_text(encoding="utf-8").splitlines()
                if "`scripts/checkpoint-tick.py`" in line and line.startswith("| ")]
        self.assertEqual(1, len(rows), "the hook needs exactly one README row")
        cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        self.assertEqual("`UserPromptSubmit`", cells[0])
        self.assertTrue(cells[2].startswith("to "), cells[2])
        self.assertIn("a record module completion left missing", cells[2])
        self.assertIn("it never blocks and is never shown to you", cells[2])
        self.assertTrue(cells[3].startswith("`bootcamp_active()`:"), cells[3])


if __name__ == "__main__":
    unittest.main()
