"""An `auto-test` walk reports a skipped directing step or worked steer (#857).

At graduation a Bootcamper's audit found required steps that never ran: the directing steps of
Data Quality, Mapping, and Transformation and of Data processing (INV-354), Discover's step
4a-pairs (INV-357) and every worked steer (INV-352). Nothing in an automated walk would have
reported any of them (#855). `.claude/skills/auto-test/transcript_lint.py` runs two more
functions from `CHECKS`:

* ``check_directing_steps`` (`BREAKING`): a hands-on module that ends without its pinned
  directing 👉. Data Quality, Mapping, and Transformation is excused by the no-site
  ``**You directed:**`` form.
* ``check_worked_steers`` (`WATCH`): an Act 2 module's first failed build or run of a `src/`
  program with no later `What went wrong:` line in that module.

**The pairs check is retired (#889).** #857 added a third, ``check_pairs_step``, for Discover's
step 4a-pairs. #889 removed that step, because Data processing's step 21 expectation check now
asks the "same entity?" question, so the check and its two finding codes went with it.
``PairsStepIsRetired`` holds the negative controls: a Discover that ends without the pairs 👉
reports nothing, and a pairs check or a pairs 👉 put back is reported.

A module is graded only once the walk reaches its end (its transition 👉, or the next module's
banner), and the module boundaries come from `module_banners.modules()` and `walk.banner_seen`,
the detection `dry-run`'s slicer already uses. `load_walk(path, tool_results=True)` adds the
walk's tool results and leaves the turns and replies as they were.

**Every pattern is pinned to its site.** Each pinned 👉, the no-site form, the steer's first line,
the transition question, the module lists and the build and run commands are read from the
shipped skill files here, so a reworded site fails this file rather than silencing a check.

⛔ **What this cannot establish.** These are regexes over a recorded walk. They see whether a
step's question was asked and whether a steer line followed a failure; whether the guide built
what was directed, compared honestly, held a prediction's answer back or steered well are
judgments only `dry-run` phase 3 observes. A clean lint is not a passed phase 3.

Stdlib only, no import from `plugins/` (INV-108). Holds on Linux, macOS and Windows: paths are
built with `pathlib`, files are read and written as UTF-8, and the command-line test runs
`sys.executable`.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
AUTO_TEST = REPO_ROOT / ".claude" / "skills" / "auto-test"
LINTER = AUTO_TEST / "transcript_lint.py"
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
MODULE_COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"
SITES = {
    "data_quality_mapping": SKILLS / "module-05-data-quality-mapping" / "phase2-data-mapping.md",
    "data_processing": SKILLS / "module-06-data-processing" / "phaseD-validation.md",
    "query_visualize_discover": (SKILLS / "module-07-query-visualize-discover"
                                 / "phase1-query-visualize.md"),
}
DISCOVER = SKILLS / "module-07-query-visualize-discover" / "phase2-discover.md"
EXISTING_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "walk-confused-questions.jsonl"

sys.path.insert(0, str(AUTO_TEST))

import transcript_lint as lint  # noqa: E402

POINTER = "\U0001f449"
BANNERS = {m["token"]: m["banner"] for m in lint.module_table()}
NAMES = {m["name"]: m["token"] for m in lint.module_table()}

READY = f"{POINTER} **Are you ready to move on to the next module: Query, Visualize and Discover?**"
GRADUATE = (f"{POINTER} **Would you like to graduate now and generate your production project "
            "and recap?**")
DIRECTED = {
    "data_quality_mapping": (f"{POINTER} **What should each of these columns become in "
                             "CUSTOMERS's mapped record? Say it in your own words.**"),
    "data_processing": (f"{POINTER} **How do you expect Senzing to have resolved these records? "
                        "Reply with a number:**"),
    "query_visualize_discover": f"{POINTER} **What do you want to find out about your data?**",
}
PAIRS = (f"{POINTER} **Are these two records the same entity? Reply with a number, and add a "
         "few words on why if you like:**")
NO_SITE = ("**You directed:** nothing this module. Every column was one `mapping_workflow` "
           "recognized, so there was no step to hand over.")
HANDED_BACK = ("**You directed:** nothing this module. You asked me to choose (\"you pick\"), "
               "so the guide chose the mapping.")
STEER = ("What went wrong: the loader stopped — given away by `KeyError: 'NAME_FULL'`.\n"
         "What the AI was asked to change: read the column the file has.")


def banner(token):
    """The module's banner as the guide displays it, framed."""
    return f"\U0001f680\U0001f680\U0001f680  {BANNERS[token]}  \U0001f680\U0001f680\U0001f680"


def codes(findings, code):
    return [f for f in findings if f["code"] == code]


def failed(after, command="python3 src/load/load_customers.py", is_error=True,
           text="Exit code 1\nKeyError: 'NAME_FULL'"):
    return {"after": after, "tool": "Bash", "command": command, "is_error": is_error,
            "text": text}


def project_with(scratch, record):
    """A project directory whose progress file holds ``record`` (a dict, or raw text)."""
    project = Path(scratch) / "project"
    (project / "config").mkdir(parents=True, exist_ok=True)
    text = record if isinstance(record, str) else json.dumps(record)
    (project / "config" / "bootcamp_progress.json").write_text(text, encoding="utf-8")
    return project


# ------------------------------------------------------------------ stream-json events


def said(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def runs(use_id, command):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": use_id, "name": "Bash", "input": {"command": command}}]}}


def result(use_id, content, is_error):
    return {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": use_id, "content": content,
         "is_error": is_error}]}}


def replied(text):
    return {"type": "bootcamper", "turn": 0, "persona": "terse", "text": text}


def write_walk(scratch, events):
    path = Path(scratch) / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n",
                    encoding="utf-8")
    return path


#: A walk through Data processing and Query, Visualize and Discover that skips the steps:
#: Data processing's run fails with no steer and no directing 👉, and Discover ends without
#: its directing 👉.
SKIPPING_WALK = [
    said(banner("data_processing") + "\n\nLoading your records now."),
    runs("toolu_1", "python3 src/load/load_customers.py"),
    result("toolu_1", [{"type": "text", "text": "Exit code 1\nKeyError: 'NAME_FULL'"}], True),
    said("Fixed the loader; all 500 records are in."),
    said(READY),
    replied("yes"),
    said(banner("query_visualize_discover") + "\n\nLet's look at your data."),
    runs("toolu_2", "python3 src/query/find_entity.py"),
    result("toolu_2", "{\"RESOLVED_ENTITY\": {}}", False),
    said(GRADUATE),
]


class LoadWalkReturnsToolResults(unittest.TestCase):
    """`load_walk` returns tool results only when asked, and the turns and replies never move."""

    def test_the_turns_and_replies_are_the_same_either_way(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = write_walk(scratch, SKIPPING_WALK)
            turns, replies = lint.load_walk(path)
            with_tools = lint.load_walk(path, tool_results=True)
        self.assertEqual(3, len(with_tools))
        self.assertEqual((turns, replies), with_tools[:2])
        self.assertEqual(5, len(turns), turns)
        self.assertEqual("yes", replies[2])

    def test_each_tool_result_carries_its_place_command_and_text(self):
        with tempfile.TemporaryDirectory() as scratch:
            tools = lint.load_walk(write_walk(scratch, SKIPPING_WALK), tool_results=True)[2]
        self.assertEqual([
            {"after": 1, "tool": "Bash", "command": "python3 src/load/load_customers.py",
             "is_error": True, "text": "Exit code 1\nKeyError: 'NAME_FULL'", "executed": True},
            {"after": 4, "tool": "Bash", "command": "python3 src/query/find_entity.py",
             "is_error": False, "text": "{\"RESOLVED_ENTITY\": {}}", "executed": True},
        ], tools)

    def test_a_result_with_no_tool_use_has_no_command(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = write_walk(scratch, [said("hello"), result("toolu_x", "done", False)])
            tools = lint.load_walk(path, tool_results=True)[2]
        self.assertEqual([{"after": 1, "tool": None, "command": None, "is_error": False,
                           "text": "done", "executed": True}], tools)

    def test_the_existing_fixture_is_unchanged_and_has_no_tool_results(self):
        turns, replies, tools = lint.load_walk(EXISTING_FIXTURE, tool_results=True)
        self.assertEqual((turns, replies), lint.load_walk(EXISTING_FIXTURE))
        self.assertEqual(lint.load(EXISTING_FIXTURE), turns)
        self.assertEqual([], tools)


class ModuleSpansUseTheBannerDetection(unittest.TestCase):
    def test_a_module_ends_at_its_transition_question(self):
        spans = lint.module_spans([banner("data_processing"), "work", READY, "ack"])
        self.assertEqual([{"token": "data_processing", "name": "Data processing",
                           "start": 1, "end": 3}], spans)

    def test_a_module_ends_before_the_next_banner(self):
        spans = lint.module_spans([banner("data_processing"), "work",
                                   banner("query_visualize_discover"), "more"])
        self.assertEqual([(1, 2), (3, None)], [(s["start"], s["end"]) for s in spans])

    def test_a_banner_named_in_prose_is_not_a_module_start(self):
        """`walk.banner_seen` matches a banner only on a line of its own (#657)."""
        text = f"Next we will do {BANNERS['data_processing']} together."
        self.assertEqual([], lint.module_spans([text]))

    def test_the_spans_use_the_module_tables_banner_matcher(self):
        with mock.patch.object(lint, "banner_seen", return_value=False):
            self.assertEqual([], lint.module_spans([banner("data_processing"), READY]))


class DirectingStepIsReported(unittest.TestCase):
    """``check_directing_steps``: fires on a finished module that skipped it, else silent."""

    def test_each_module_without_its_directing_question_is_reported(self):
        for token in lint.DIRECTING_QUESTIONS:
            with self.subTest(token=token):
                found = lint.check_directing_steps([banner(token), "work", READY])
                self.assertEqual(1, len(found), found)
                self.assertEqual(("BREAKING", "INV-354-directing-step-missing", 3),
                                 (found[0]["severity"], found[0]["code"], found[0]["turn"]))

    def test_each_module_with_its_directing_question_is_silent(self):
        for token, question in DIRECTED.items():
            with self.subTest(token=token):
                self.assertEqual([], lint.check_directing_steps(
                    [banner(token), question, "work", READY]))

    def test_another_modules_question_does_not_count(self):
        found = lint.check_directing_steps(
            [banner("data_processing"), DIRECTED["query_visualize_discover"], READY])
        self.assertEqual(1, len(found), found)

    def test_a_module_that_ends_at_the_next_banner_is_graded(self):
        found = lint.check_directing_steps(
            [banner("data_processing"), "work", banner("query_visualize_discover")])
        self.assertEqual([2], [f["turn"] for f in found])

    def test_a_walk_that_ends_inside_the_module_is_silent(self):
        self.assertEqual([], lint.check_directing_steps([banner("data_processing"), "work"]))

    def test_the_no_site_form_excuses_data_quality_mapping(self):
        self.assertEqual([], lint.check_directing_steps(
            [banner("data_quality_mapping"), "work", NO_SITE, READY]))

    def test_the_no_site_form_excuses_no_other_module(self):
        for token in ("data_processing", "query_visualize_discover"):
            with self.subTest(token=token):
                found = lint.check_directing_steps([banner(token), NO_SITE, READY])
                self.assertEqual(1, len(found), found)

    def test_the_handed_back_form_is_not_the_no_site_form(self):
        """Handing the step back follows the 👉, so without the 👉 it is still a skip."""
        found = lint.check_directing_steps(
            [banner("data_quality_mapping"), HANDED_BACK, READY])
        self.assertEqual(1, len(found), found)

    def test_without_the_end_detection_nothing_is_graded(self):
        """Negative control: the transition question is what makes a module gradable."""
        with mock.patch.object(lint, "TRANSITION", re.compile(r"(?!x)x")):
            self.assertEqual([], lint.check_directing_steps(
                [banner("data_processing"), "work", READY]))


#: The finding codes the retired pairs check reported (#857, retired by #889).
RETIRED_CODES = {"INV-357-pairs-step-missing", "INV-357-pairs-step-ungraded"}


def retired_pairs_problems(module, discover_text):
    """What a reintroduced 4a-pairs site would leave behind (#889), as a list of problems."""
    problems = []
    if hasattr(module, "check_pairs_step"):
        problems.append("transcript_lint defines check_pairs_step again")
    if any(f.__name__ == "check_pairs_step" for f in module.CHECKS):
        problems.append("CHECKS runs check_pairs_step again")
    if any(POINTER in line and "same entity?" in line for line in discover_text.splitlines()):
        problems.append("phase2-discover.md pins a \"same entity?\" 👉 again")
    return problems


class PairsStepIsRetired(unittest.TestCase):
    """#889: step 4a-pairs is gone, so nothing grades it, with negative controls."""

    WALK = [banner("query_visualize_discover"), DIRECTED["query_visualize_discover"], GRADUATE]

    def test_nothing_is_left_of_it(self):
        self.assertEqual([], retired_pairs_problems(lint, DISCOVER.read_text(encoding="utf-8")))

    def test_a_discover_without_the_pairs_question_reports_nothing(self):
        with tempfile.TemporaryDirectory() as scratch:
            project = project_with(scratch, {"module_7_query": {"discover_phase": "completed"}})
            found = lint.lint(self.WALK, project=project)
        self.assertEqual([], [f for f in found if f["code"] in RETIRED_CODES])

    def test_negative_control_the_check_put_back(self):
        def check_pairs_step(turns, project=None):
            return []
        with mock.patch.object(lint, "check_pairs_step", check_pairs_step, create=True), \
                mock.patch.object(lint, "CHECKS", lint.CHECKS + (check_pairs_step,)):
            self.assertEqual(["transcript_lint defines check_pairs_step again",
                              "CHECKS runs check_pairs_step again"],
                             retired_pairs_problems(lint, DISCOVER.read_text(encoding="utf-8")))

    def test_negative_control_the_pairs_question_put_back(self):
        text = DISCOVER.read_text(encoding="utf-8").replace(
            "### Step 4b: Why Analysis introduction",
            PAIRS + "\n\n### Step 4b: Why Analysis introduction", 1)
        self.assertEqual(['phase2-discover.md pins a "same entity?" 👉 again'],
                         retired_pairs_problems(lint, text))


class WorkedSteerIsReported(unittest.TestCase):
    """``check_worked_steers``: an Act 2 module's first failed program run needs a steer."""

    WALK = [banner("data_processing"), "Loading.", "Fixed it; all records are in.", READY]

    def test_a_failed_run_with_no_steer_is_reported(self):
        found = lint.check_worked_steers(self.WALK, [failed(1)])
        self.assertEqual([("WATCH", "INV-352-steer-missing", 2)],
                         [(f["severity"], f["code"], f["turn"]) for f in found])
        self.assertIn("src/load/load_customers.py", found[0]["message"])

    def test_a_steer_later_in_the_module_is_silent(self):
        walk = self.WALK[:2] + [STEER] + self.WALK[2:]
        self.assertEqual([], lint.check_worked_steers(walk, [failed(2)]))

    def test_a_steer_before_the_failure_does_not_count(self):
        walk = self.WALK[:1] + [STEER] + self.WALK[1:]
        self.assertEqual(1, len(lint.check_worked_steers(walk, [failed(3)])))

    def test_a_steer_after_the_module_end_does_not_count(self):
        walk = self.WALK + [STEER]
        self.assertEqual(1, len(lint.check_worked_steers(walk, [failed(1)])))

    def test_only_the_first_failure_needs_the_steer(self):
        walk = self.WALK[:2] + [STEER] + self.WALK[2:]
        self.assertEqual([], lint.check_worked_steers(walk, [failed(2), failed(3)]))

    def test_every_act_2_module_is_graded(self):
        for token in lint.STEER_MODULES:
            with self.subTest(token=token):
                walk = [banner(token)] + self.WALK[1:]
                self.assertEqual(1, len(lint.check_worked_steers(walk, [failed(1)])))

    def test_act_1_is_never_graded(self):
        walk = [banner("system_verification")] + self.WALK[1:]
        self.assertEqual([], lint.check_worked_steers(walk, [failed(1)]))

    def test_a_non_zero_exit_without_is_error_is_reported(self):
        tool = failed(1, is_error=False, text="Exit code 2\nusage: load_customers.py")
        self.assertEqual(1, len(lint.check_worked_steers(self.WALK, [tool])))

    def test_a_clean_run_is_silent(self):
        tool = failed(1, is_error=False, text="Loaded 500 records.")
        self.assertEqual([], lint.check_worked_steers(self.WALK, [tool]))

    def test_an_error_from_something_other_than_a_program_run_is_silent(self):
        for command in ("cat src/load/load_customers.py", "python3 -c 'print(1)'",
                        "source src/scripts/senzing-env.sh",
                        "ls docs/missing"):
            with self.subTest(command=command):
                self.assertEqual([], lint.check_worked_steers(
                    self.WALK, [failed(1, command=command)]))

    def test_a_failure_outside_the_module_is_silent(self):
        self.assertEqual([], lint.check_worked_steers(self.WALK, [failed(0), failed(4)]))

    def test_no_tool_results_is_silent(self):
        """A transcript answered by hand carries no tool results, so nothing is graded."""
        self.assertEqual([], lint.check_worked_steers(self.WALK, []))
        self.assertEqual([], lint.check_worked_steers(self.WALK, None))

    def test_a_walk_that_ends_inside_the_module_is_silent(self):
        self.assertEqual([], lint.check_worked_steers(self.WALK[:3], [failed(1)]))

    def test_the_windows_forms_count(self):
        """INV-001: native Windows runs each command through one PowerShell call."""
        command = ("powershell.exe -NoProfile -Command '. .\\src\\scripts\\senzing-env.ps1; "
                   "python3 src\\load\\load_customers.py'")
        self.assertEqual(1, len(lint.check_worked_steers(
            self.WALK, [failed(1, command=command)])))
        for env_only in (
                "powershell.exe -NoProfile -Command '. .\\src\\scripts\\senzing-env.ps1'",
                # A runner, but the only `src\` path is the env script every call sources.
                "powershell.exe -NoProfile -Command '. .\\src\\scripts\\senzing-env.ps1; "
                "python3 -c \"import senzing\"'"):
            with self.subTest(command=env_only):
                self.assertEqual([], lint.check_worked_steers(
                    self.WALK, [failed(1, command=env_only)]))


def with_meta(event, *entries):
    """``event`` carrying a ``tool_result_meta`` list, as the walk's stream-json logs it."""
    return dict(event, tool_result_meta=list(entries))


REJECTED = {"id": "toolu_1", "non_execution_kind": "permission-rule",
            "permission_decision": {"decision": "reject", "source": "hook",
                                    "reason_type": "hook"}}
HOOK_ERROR = ("PreToolUse:Bash hook error: [python3 write-gate.py]: Write blocked: use a "
              "project-relative path, not a system temp or Downloads directory.")


class ARejectedCallIsNotAFailedRun(unittest.TestCase):
    """#921: a call a hook or permission rule rejected never ran, so it owes no steer."""

    def walk(self, *meta):
        events = [said(banner("data_processing") + "\n\nLoading."),
                  runs("toolu_1", "python3 src/load/load_customers.py > /tmp/out.txt"),
                  with_meta(result("toolu_1", HOOK_ERROR, True), *meta) if meta
                  else result("toolu_1", HOOK_ERROR, True),
                  said("Fixed it; all records are in."), said(READY)]
        with tempfile.TemporaryDirectory() as scratch:
            turns, _, tools = lint.load_walk(write_walk(scratch, events), tool_results=True)
        return lint.check_worked_steers(turns, tools), tools

    def test_a_hook_rejection_is_silent(self):
        found, tools = self.walk(REJECTED)
        self.assertFalse(tools[0]["executed"])
        self.assertEqual([], found)

    def test_either_signal_alone_marks_it_not_run(self):
        decision_only = {"id": "toolu_1", "permission_decision": {"decision": "reject"}}
        kind_only = {"id": "toolu_1", "non_execution_kind": "permission-rule",
                     "permission_decision": {"decision": "accept"}}
        for entry in (decision_only, kind_only):
            with self.subTest(entry=entry):
                found, tools = self.walk(entry)
                self.assertFalse(tools[0]["executed"])
                self.assertEqual([], found)

    def test_an_accepted_call_that_failed_is_still_reported(self):
        accepted = {"id": "toolu_1", "permission_decision": {"decision": "accept",
                                                             "source": "config"}}
        found, tools = self.walk(accepted)
        self.assertTrue(tools[0]["executed"])
        self.assertEqual(["INV-352-steer-missing"], [f["code"] for f in found])

    def test_a_rejection_of_another_call_does_not_excuse_this_one(self):
        found, _ = self.walk(dict(REJECTED, id="toolu_other"))
        self.assertEqual(1, len(found))

    def test_no_metadata_grades_as_before(self):
        """A transcript without ``tool_result_meta`` counts every call as executed."""
        found, tools = self.walk()
        self.assertTrue(tools[0]["executed"])
        self.assertEqual(1, len(found))

    def test_malformed_metadata_grades_as_before(self):
        for meta in ("reject", None, ["reject"], {"id": "toolu_1"}):
            with self.subTest(meta=meta):
                events = [said(banner("data_processing")),
                          runs("toolu_1", "python3 src/load/load_customers.py"),
                          dict(result("toolu_1", "Exit code 1", True), tool_result_meta=meta),
                          said(READY)]
                with tempfile.TemporaryDirectory() as scratch:
                    tools = lint.load_walk(write_walk(scratch, events), tool_results=True)[2]
                self.assertTrue(tools[0]["executed"])

    def test_only_the_executed_flag_decides(self):
        tools = [dict(failed(1), executed=False)]
        walk = [banner("data_processing"), "Loading.", "Fixed it.", READY]
        self.assertEqual([], lint.check_worked_steers(walk, tools))
        self.assertEqual(1, len(lint.check_worked_steers(walk, [dict(tools[0], executed=True)])))


#: Claude Code's answer to the 2026-11-12 15:11 walk's turn 40 call (#928).
NO_SUCH_TOOL = ("<tool_use_error>Error: No such tool available: bash. Tool names are "
                "case-sensitive: call Bash instead.</tool_use_error>")
#: That call's command, shortened: it writes a program and would have run it.
SHOW_ENTITY = ("cd project && mkdir -p src/query && cat > src/query/show_entity.py <<'EOF'\n"
               "import json\nEOF\npython3 src/query/show_entity.py")


def calls(use_id, tool, command):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": use_id, "name": tool, "input": {"command": command}}]}}


class ACallToAMissingToolIsNotAFailedRun(unittest.TestCase):
    """#928: a call to a tool that does not exist never ran, so it owes no steer, and only
    ``Bash`` calls are graded, as only they reach the ``failed-run-net.py`` hook."""

    def walk(self, tool, text, is_error=True):
        # Shaped on the 15:11 walk's turns 39-40: the call, Claude Code's answer, the guide
        # going on, then the transition.
        events = [said(banner("data_processing") + "\n\nWriting the lookup program."),
                  calls("toolu_1", tool, SHOW_ENTITY), result("toolu_1", text, is_error),
                  said("The program is written and shows the entity."), said(READY)]
        with tempfile.TemporaryDirectory() as scratch:
            turns, _, tools = lint.load_walk(write_walk(scratch, events), tool_results=True)
        return lint.check_worked_steers(turns, tools), tools

    def test_the_walks_lowercase_bash_call_is_silent(self):
        found, tools = self.walk("bash", NO_SUCH_TOOL)
        self.assertFalse(tools[0]["executed"])
        self.assertEqual([], found)

    def test_a_bash_call_answered_no_such_tool_is_not_run(self):
        found, tools = self.walk("Bash", NO_SUCH_TOOL)
        self.assertFalse(tools[0]["executed"])
        self.assertEqual([], found)

    def test_another_tools_error_is_not_graded(self):
        found, tools = self.walk("bash", "Exit code 1\nTraceback (most recent call last):")
        self.assertTrue(tools[0]["executed"])
        self.assertEqual([], found)

    def test_a_bash_call_that_ran_and_failed_is_still_reported(self):
        found, tools = self.walk("Bash", "Exit code 1\nTraceback (most recent call last):")
        self.assertTrue(tools[0]["executed"])
        self.assertEqual(["INV-352-steer-missing"], [f["code"] for f in found])

    def test_the_message_counts_only_as_a_tool_use_error(self):
        # The words alone, in a program's own output, are not Claude Code's answer.
        found, tools = self.walk("Bash", "Exit code 1\nNo such tool available: lookup")
        self.assertTrue(tools[0]["executed"])
        self.assertEqual(1, len(found))

    def test_negative_control_the_conditions_cut(self):
        source = LINTER.read_text(encoding="utf-8")
        cuts = (('\n                                  and not NO_SUCH_TOOL.search(text or "")})',
                 "})"),
                ('and t.get("tool") == "Bash" and t.get("executed", True)',
                 'and t.get("executed", True)'))
        cut = source
        for old, new in cuts:
            self.assertIn(old, cut, "the condition moved; update the control: %r" % old)
            cut = cut.replace(old, new)
        namespace = {"__file__": str(LINTER), "__name__": "transcript_lint_mutant"}
        exec(compile(cut, str(LINTER), "exec"), namespace)  # noqa: S102 - the repo's own file
        events = [said(banner("data_processing") + "\n\nWriting the lookup program."),
                  calls("toolu_1", "bash", SHOW_ENTITY), result("toolu_1", NO_SUCH_TOOL, True),
                  said("The program is written."), said(READY)]
        with tempfile.TemporaryDirectory() as scratch:
            turns, _, tools = namespace["load_walk"](write_walk(scratch, events),
                                                     tool_results=True)
        self.assertEqual(1, len(namespace["check_worked_steers"](turns, tools)))


class AWalkOutsideModulesFiveToSevenReportsNothingNew(unittest.TestCase):
    def test_the_existing_walk_raises_none_of_them(self):
        turns, replies, tools = lint.load_walk(EXISTING_FIXTURE, tool_results=True)
        found = lint.lint(turns, replies=replies, tools=tools)
        new = {"INV-354-directing-step-missing", "INV-352-steer-missing"} | RETIRED_CODES
        self.assertEqual([], [f for f in found if f["code"] in new])


class TheChecksAreRegisteredAndRun(unittest.TestCase):
    NEW = ("check_directing_steps", "check_worked_steers")

    def test_each_is_in_checks(self):
        names = [f.__name__ for f in lint.CHECKS]
        for name in self.NEW:
            self.assertIn(name, names)

    def test_lint_passes_each_its_input(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = write_walk(scratch, SKIPPING_WALK)
            turns, replies, tools = lint.load_walk(path, tool_results=True)
            project = project_with(scratch, {"module_7_query": {"discover_phase": "completed"}})
            found = lint.lint(turns, project=project, replies=replies, tools=tools)
        self.assertEqual(
            [("INV-352-steer-missing", 2), ("INV-354-directing-step-missing", 3),
             ("INV-354-directing-step-missing", 5)],
            sorted((f["code"], f["turn"]) for f in found))

    def test_the_command_line_reads_the_tool_results_and_the_project(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = write_walk(scratch, SKIPPING_WALK)
            project = project_with(scratch, {"module_7_query": {"discover_phase": "completed"}})
            run = subprocess.run(
                [sys.executable, str(LINTER), str(path), "--project", str(project), "--json"],
                capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(1, run.returncode, run.stderr)
        found = {f["code"] for f in json.loads(run.stdout)}
        self.assertEqual({"INV-352-steer-missing", "INV-354-directing-step-missing"}, found)


# ------------------------------------------------------------- pinned to their sites


def pointer_line(path, needle):
    for line in path.read_text(encoding="utf-8").splitlines():
        if POINTER in line and needle in line:
            return line
    raise AssertionError(f"{path.name} has no 👉 line holding {needle!r}")


def section(path, heading):
    text = path.read_text(encoding="utf-8")
    start = text.index(f"\n## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end > 0 else None]


class EachPatternMatchesItsSite(unittest.TestCase):
    """The checks match what the plugin pins today, read from the shipped files."""

    def test_each_directing_question_matches_its_site(self):
        needles = {"data_quality_mapping": "What should each of these columns become",
                   "data_processing": "How do you expect Senzing to have resolved",
                   "query_visualize_discover": "What do you want to find out"}
        for token, path in SITES.items():
            with self.subTest(token=token):
                line = pointer_line(path, needles[token]).replace("{source}", "CUSTOMERS")
                self.assertRegex(line, lint.DIRECTING_QUESTIONS[token])

    def test_the_directing_table_names_exactly_these_modules(self):
        rows = re.findall(r"^\| ([^|]+?) \| `\.\./module-",
                          section(GROUND_RULES, "Directing steps"), re.M)
        self.assertEqual(set(lint.DIRECTING_QUESTIONS), {NAMES[name] for name in rows})

    def test_the_no_site_form_matches_the_ground_rules(self):
        form = re.search(r"no site: `(\*\*You directed:\*\*[^`]+)`",
                         " ".join(section(GROUND_RULES, "Directing steps").split())).group(1)
        self.assertRegex(form.replace("{Why the step did not arise}", "No column was new"),
                         lint.NO_SITE)

    def test_the_steer_modules_are_the_act_2_hands_on_modules(self):
        flat = " ".join(section(GROUND_RULES, "Worked steers").split())
        listed = re.search(r"Act 2 hands-on modules are (.+?)\. ", flat).group(1)
        names = [re.sub(r"^and ", "", part.strip()) for part in listed.split(";")]
        self.assertEqual(set(lint.STEER_MODULES), {NAMES[name] for name in names})

    def test_the_steer_line_opens_the_pinned_steer(self):
        self.assertRegex(section(GROUND_RULES, "Worked steers"),
                         r"(?m)^\s*" + re.escape(lint.STEER_LINE) + " ")

    def test_the_transition_and_graduation_questions_end_a_module(self):
        step4 = " ".join(section(MODULE_COMPLETION, "Step 4: Transition question").split())
        question = re.search(r"\"(Are you ready to move on to the next module: [^\"]+)\"",
                             step4).group(1)
        self.assertRegex(question, lint.TRANSITION)
        self.assertRegex(pointer_line(MODULE_COMPLETION, "graduate now"), lint.TRANSITION)

    def test_every_build_and_run_command_is_a_program_run(self):
        table = section(GROUND_RULES, "Building and running a program")
        rows = re.findall(r"^\| (Python|Java|C#|Rust|TypeScript) \|(.+)$", table, re.M)
        self.assertEqual(5, len(rows), rows)
        commands = []
        for language, cells in rows:
            build, run = [c.strip() for c in cells.split("|")[1:3]]
            for cell in (build, run):
                span = re.match(r"`([^`]+)`", cell).group(1)
                if "<dir>" not in span:
                    continue    # Java's run names a class; its classpath names <dir>/classes
                commands.append(span.replace("<dir>", "src/load")
                                .replace("<name>", "load_customers"))
        self.assertEqual(9, len(commands), commands)
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(lint._failed_program_run(failed(1, command=command)))


if __name__ == "__main__":
    unittest.main()
