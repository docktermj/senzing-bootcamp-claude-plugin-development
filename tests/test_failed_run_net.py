"""A failed run of generated code leaves a trace even when the guide repairs it in silence (#910).

On 2026-11-10 a walk's lookup program failed at Data processing step 21 (turn 31), the guide
created the missing `src/query/` folder and retried, and no worked steer and no
`steer_triggers` entry followed. Only `transcript_lint` saw it, after the walk. Two hooks
now catch it while the bootcamp runs:

- `scripts/failed-run-net.py` (`PostToolUse` and `PostToolUseFailure` on Bash) recognizes a
  failed program run, records the first one of an Act 2 hands-on module in
  `config/steer_observations.json`, and reminds the guide of "Worked steers";
- `scripts/checkpoint-tick.py` names, at the module's transition, an observation whose
  module's `steer_triggers` is still empty.

What a failed program run is lives in one place, `scripts/failed_run.py`, which
`transcript_lint` reads too (INV-300); `TheDefinitionIsShared` fails on a second copy.

Each hook runs as a subprocess in a scratch project, the way Claude Code invokes it, and
nothing under `plugins/` is imported here (INV-108). Every silent case has a twin that speaks,
and `NegativeControls` runs mutants of the hooks with the recognition, the module gate or the
transition case removed, and requires a case to fail on each.

Enforces INV-352's dated note of 2026-11-11 (#910), registered 2026-11-11, from the ledger entry
(`a-failed-program-run-at-data-processing-step-21-was-repaired-with-no-worked-steer-and-no-steer-triggers-record`).
It cannot establish that a live guide shows the steer after the reminder; only a live walk
(`auto-test` or `dry-run` phase 3) observes that.

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"
NET = "failed-run-net.py"
TICK = "checkpoint-tick.py"
HOOKS_JSON = PLUGIN / "hooks" / "hooks.json"
HOOKS_README = PLUGIN / "hooks" / "README.md"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
LINT = REPO_ROOT / ".claude" / "skills" / "auto-test" / "transcript_lint.py"

POINTER = "\U0001f449"
TRANSITION = ("%s **Are you ready to move on to the next module: Query, Visualize and "
              "Discover?**" % POINTER)
LABEL = "Module-completion records still missing"

#: Turn 31 of the 2026-11-10 walk, shortened: the heredoc that saves the program, into a
#: folder that did not exist, followed by the run.
TURN_31_COMMAND = (
    "export LD_LIBRARY_PATH=/opt/senzing/er/lib PYTHONPATH=/opt/senzing/er/sdk/python "
    "SENZING_ENGINE_CONFIGURATION_JSON=\"$(tr -d '\\n' < config/engine_config.json)\" && "
    "cat > src/query/lookup_record.py <<'EOF'\n#! /usr/bin/env python3\nimport json\nEOF\n"
    "python3 src/query/lookup_record.py CUSTOMERS 1001")
TURN_31_ERROR = (
    "Exit code 1\n/bin/bash: line 29: src/query/lookup_record.py: No such file or directory\n"
    "python3: can't open file '.../project/src/query/lookup_record.py': [Errno 2] No such "
    "file or directory")
EVIDENCE = "/bin/bash: line 29: src/query/lookup_record.py: No such file or directory"


def failure_payload(command=TURN_31_COMMAND, error=TURN_31_ERROR):
    return {"hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
            "tool_input": {"command": command}, "error": error, "is_interrupt": False}


def success_payload(command=TURN_31_COMMAND, stdout="RESOLVED_ENTITY ..."):
    return {"hook_event_name": "PostToolUse", "tool_name": "Bash",
            "tool_input": {"command": command},
            "tool_response": {"stdout": stdout, "stderr": "", "interrupted": False}}


def progress(**overrides):
    data = {"current_module": "data_processing", "current_step": 21,
            "modules_completed": ["data_collection", "data_quality_mapping"],
            "directing_steps": {"data_quality_mapping": "directed",
                                "data_processing": "directed"},
            "steer_triggers": {}}
    data.update(overrides)
    return data


class Project:
    """A scratch project with its own copy of the plugin scripts, so a mutant can run."""

    def __init__(self, test, progress_data, scripts=SCRIPTS):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.scripts = scripts
        (self.root / "config").mkdir()
        (self.root / "docs" / "progress").mkdir(parents=True)
        (self.root / "docs" / "progress" / "recap_checkpoint.md").write_text(
            "<!-- RECAP-CHECKPOINT:SCAFFOLD -->\n", encoding="utf-8")
        text = progress_data if isinstance(progress_data, str) else json.dumps(progress_data)
        (self.root / "config" / "bootcamp_progress.json").write_text(text, encoding="utf-8")

    @property
    def observations(self):
        return self.root / "config" / "steer_observations.json"

    def write_progress(self, data):
        (self.root / "config" / "bootcamp_progress.json").write_text(
            json.dumps(data), encoding="utf-8")

    def run(self, script, raw):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run([sys.executable, str(self.scripts / script)],
                              input=raw.encode("utf-8"), capture_output=True,
                              cwd=str(self.root), env=env, timeout=60)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def net(self, payload):
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        return self.run(NET, raw)

    def tick(self):
        transcript = self.root / "transcript.jsonl"
        records = [
            {"type": "user", "message": {"role": "user", "content": "Done."}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "**Module complete**\n\n" + TRANSITION}]}}]
        transcript.write_text("".join(json.dumps(r) + "\n" for r in records),
                              encoding="utf-8")
        return self.run(TICK, json.dumps({"hook_event_name": "UserPromptSubmit",
                                          "prompt": "yes",
                                          "transcript_path": str(transcript)}))


class NetCase(unittest.TestCase):

    def reminded(self, project, payload, because=""):
        code, out, err = project.net(payload)
        self.assertNotIn("Traceback", err, "the hook raised " + because)
        self.assertEqual(0, code, "the hook must exit 0, never block")
        self.assertTrue(out, "the hook stayed silent where it had to remind " + because)
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(payload["hook_event_name"], hso["hookEventName"])
        return hso["additionalContext"]

    def silent(self, project, payload, because=""):
        code, out, err = project.net(payload)
        self.assertNotIn("Traceback", err, "the hook raised " + because)
        self.assertEqual(0, code, "the hook must exit 0 " + because)
        self.assertEqual("", out, "the hook must write nothing to stdout " + because)
        self.assertFalse(project.observations.exists(), "nothing may be recorded " + because)


class TheTurn31FailureIsObserved(NetCase):

    def test_the_reminder_names_the_rule_and_the_module(self):
        project = Project(self, progress())
        text = self.reminded(project, failure_payload())
        self.assertIn('"Worked steers"', text)
        self.assertIn("Data processing", text)
        self.assertIn("steer_triggers", text)
        self.assertIn("do not mention this reminder to the bootcamper", text)
        self.assertIn("Do not apologize", text, "the reminder asks for no apology")

    def test_it_never_insists_where_a_site_says_report_and_continue(self):
        text = self.reminded(Project(self, progress()), failure_payload())
        self.assertIn("report the failure in one line and continue, follow them", text)

    def test_the_observation_is_recorded_in_its_own_file(self):
        project = Project(self, progress())
        before = (project.root / "config" / "bootcamp_progress.json").read_text()
        self.reminded(project, failure_payload())
        self.assertEqual({"data_processing": {"evidence": EVIDENCE}},
                         json.loads(project.observations.read_text(encoding="utf-8")))
        self.assertEqual(before, (project.root / "config" / "bootcamp_progress.json")
                         .read_text(), "the progress file stays the guide's to write")

    def test_a_non_zero_exit_reported_through_post_tool_use_counts(self):
        payload = success_payload(stdout="Exit code 2\nTraceback (most recent call last):")
        self.reminded(Project(self, progress()), payload)

    def test_only_the_first_failure_of_a_module_is_reminded(self):
        project = Project(self, progress())
        self.reminded(project, failure_payload())
        code, out, _ = project.net(failure_payload(error="Exit code 1\nKeyError: 'X'"))
        self.assertEqual("", out, "a second failure in the module is not reminded")
        self.assertIn(EVIDENCE, project.observations.read_text(encoding="utf-8"))


class TheNetIsSilentElsewhere(NetCase):

    def test_a_successful_run(self):
        self.silent(Project(self, progress()), success_payload(), "on a successful run")

    def test_a_failed_command_that_is_not_a_program_run(self):
        payload = failure_payload(command="ls src/query", error="Exit code 2\nls: no such")
        self.silent(Project(self, progress()), payload, "on a failure that runs no program")

    def test_the_env_script_is_not_a_program(self):
        payload = failure_payload(command="python3 src/scripts/env_check.py")
        self.silent(Project(self, progress()), payload, "for src/scripts/")

    def test_an_act_1_module(self):
        for module in ("sdk_setup", "system_verification", "truthset_visualization",
                       "bootcamp_preparation", "graduation"):
            with self.subTest(module=module):
                self.silent(Project(self, progress(current_module=module)), failure_payload(),
                            "in " + module)

    def test_onboarding_before_any_module(self):
        project = Project(self, "{}")
        (project.root / "config" / "bootcamp_progress.json").unlink()
        self.silent(project, failure_payload(), "with no progress file")

    def test_a_module_whose_trigger_is_recorded(self):
        data = progress(steer_triggers={"data_processing": [
            {"kind": "failure", "evidence": "Exit code 1"}]})
        self.silent(Project(self, data), failure_payload(), "once steer_triggers has an entry")

    def test_a_finished_bootcamp(self):
        self.silent(Project(self, progress(bootcamp_complete=True)), failure_payload(),
                    "once the bootcamp is complete")

    def test_malformed_input(self):
        project = Project(self, progress())
        for raw in ("", "not json", "[]", json.dumps({"tool_name": "Bash"}),
                    json.dumps({"tool_name": "Write", "tool_input": {"command": "x"},
                                "error": "Exit code 1"}),
                    json.dumps({"tool_name": "Bash", "tool_input": {"command": 7},
                                "error": "Exit code 1"})):
            with self.subTest(raw=raw):
                self.silent(project, raw, "on unreadable input")

    def test_a_malformed_progress_or_observation_file(self):
        self.silent(Project(self, "not json"), failure_payload(), "on a malformed progress file")
        self.silent(Project(self, progress(steer_triggers=[])), failure_payload(),
                    "on a wrongly typed steer_triggers")
        project = Project(self, progress())
        project.observations.write_text("not json", encoding="utf-8")
        self.reminded(project, failure_payload(), "a malformed observation file reads empty")


class TheTransitionNamesAnUnrecordedFailure(unittest.TestCase):

    def tick(self, project):
        code, out, err = project.tick()
        self.assertNotIn("Traceback", err)
        self.assertEqual(0, code, "the hook must never block")
        return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""

    def test_an_observed_failure_with_no_trigger_is_named(self):
        project = Project(self, progress())
        project.net(failure_payload())
        project.write_progress(progress(
            current_module="query_visualize_discover", current_step=None,
            modules_completed=["data_collection", "data_quality_mapping", "data_processing"]))
        text = self.tick(project)
        self.assertIn(LABEL, text)
        self.assertIn("steer_triggers.data_processing has no entry", text)
        self.assertIn(EVIDENCE, text)

    def test_silent_once_the_guide_recorded_the_trigger(self):
        project = Project(self, progress())
        project.net(failure_payload())
        project.write_progress(progress(
            current_module="query_visualize_discover", current_step=None,
            steer_triggers={"data_processing": [{"kind": "failure", "evidence": EVIDENCE}]}))
        self.assertEqual("", self.tick(project))


class NegativeControls(unittest.TestCase):
    """Each mutant removes one part, and a case above must then fail."""

    def mutant(self, script, old, new):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        copy = Path(tmp.name) / "scripts"
        shutil.copytree(SCRIPTS, copy, ignore=shutil.ignore_patterns("__pycache__", "vendor"))
        path = copy / script
        source = path.read_text(encoding="utf-8")
        self.assertIn(old, source, "the mutation site moved; update the control")
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
        return copy

    def test_without_recognition_the_turn_31_failure_is_missed(self):
        scripts = self.mutant("failed_run.py", "return is_error is True or", "return False and")
        _, out, _ = Project(self, progress(), scripts).net(failure_payload())
        self.assertEqual("", out)

    def test_without_the_module_gate_act_1_is_reminded(self):
        scripts = self.mutant(NET, "if token not in STEER_MODULES:", "if False:")
        _, out, _ = Project(self, progress(current_module="sdk_setup"), scripts).net(
            failure_payload())
        self.assertNotEqual("", out)

    def test_without_the_transition_case_the_failure_is_not_named(self):
        scripts = self.mutant(TICK, "failures = unrecorded_failures(progress, observed or {})",
                              "failures = []")
        project = Project(self, progress(), scripts)
        project.net(failure_payload())
        project.write_progress(progress(current_module="query_visualize_discover",
                                        current_step=None))
        _, out, _ = project.tick()
        self.assertNotIn("steer_triggers.data_processing has no entry", out)


class TheDefinitionIsShared(unittest.TestCase):

    def test_the_lint_holds_no_copy_of_the_definition(self):
        lint = LINT.read_text(encoding="utf-8")
        self.assertIn("import failed_run", lint)
        self.assertIn("failed_run.failed_program_run(", lint)
        for pattern in ("BUILDS_OR_RUNS = re.compile", "PROGRAM_PATH = re.compile",
                        "EXIT_CODE = re.compile"):
            self.assertNotIn(pattern, lint, "a second copy of the definition (INV-300)")

    def test_the_net_uses_it(self):
        self.assertIn("failed_run.failed_program_run(",
                      (SCRIPTS / NET).read_text(encoding="utf-8"))


class TheNetIsRegisteredAndDocumented(unittest.TestCase):

    def test_registered_on_both_bash_events(self):
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        for event in ("PostToolUse", "PostToolUseFailure"):
            with self.subTest(event=event):
                entries = hooks[event]
                self.assertTrue(any(e.get("matcher") == "Bash" and any(
                    NET in h["command"] for h in e["hooks"]) for e in entries))

    def test_the_readme_has_its_row(self):
        self.assertIn("`scripts/%s`" % NET, HOOKS_README.read_text(encoding="utf-8"))

    def test_ground_rules_points_at_the_net_once(self):
        text = GROUND_RULES.read_text(encoding="utf-8")
        self.assertEqual(1, text.count(NET), "one pointer line, restating nothing (INV-300)")


if __name__ == "__main__":
    unittest.main()
