"""The resume message names the recorded module by its name, and that name has one source.

Enforces INV-425 (registered by the maintainer 2026-11-10). It runs the hook as a subprocess; it
cannot establish that a live guide stops showing numbers, which an `auto-test` walk observes.

Issue #874: on two `auto-test` walks the guide's resume offer read "Where you left off:
Module 5, Data Quality, Mapping, and Transformation, at step 11". The number came from neither
the progress file nor shipped verbatim text: `session-start.py` said only "offer to resume from
the last recorded module", `bootcamp-onboarding/SKILL.md` step 2 gave the offer no form, and
the guide improvised one from the skill heading, which carries the number (INV-079).

What this file pins:

- **The resume message names the module.** For every module in the module table,
  `session-start.py` run with that state token as `current_module` prints the module's display
  name as the table spells it, with the step when `current_step` is set, and no `Module <digit>`.
  Graduation uses `module_start_apparatus.GRADUATION_NAME`. An unknown key keeps the generic
  wording, with no name and no number. A module not begun still gets the apparatus reminder
  unchanged.
- **The name has one source (INV-300).** `module_start_apparatus.DISPLAY_NAMES` must equal the
  module table in `bootcamp-preparation/SKILL.md`, parsed here, so a renamed or added module
  fails this test rather than drifting.
- **The offer's form is pinned** in `bootcamp-onboarding/SKILL.md` step 2, with its ⛔ rule
  citing INV-079 on its own line.

Negative controls (INV-265): a copy of `session-start.py` that prints a number, a module table
with a renamed module, and a step 2 with the form or the rule removed each fail a check here.

`session-start.py` resolves `config/` against the working directory, so it runs as a
subprocess in a temp project. `module_start_apparatus.py` is loaded from its file only to read
its constants, as `tests/test_resume_requires_a_recorded_module.py` loads `recap_checkpoint.py`;
nothing under `plugins/` is imported as a package (INV-108). This reads shipped text and runs
the hook; it does not establish that a live guide uses the name it is given, which only a live
walk (`auto-test --seed mid`) observes.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
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
SESSION_START = SCRIPTS / "session-start.py"
BUILDER = SCRIPTS / "module_start_apparatus.py"
PREP = PLUGIN / "skills" / "bootcamp-preparation" / "SKILL.md"
ONBOARDING = PLUGIN / "skills" / "bootcamp-onboarding" / "SKILL.md"

MODULE_NUMBER = re.compile(r"\bModule\s+\d+\b")
GENERIC = ("offer to resume from the last recorded module before doing anything else.")

#: A module-table row: | # | Module | Rule | `state_token` | Maps to |
TABLE_ROW = re.compile(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*`([a-z_]+)`\s*\|")


def table_names(text):
    """``{state token: display name}`` from the module table's rows, in table order."""
    names = {}
    for line in text.splitlines():
        match = TABLE_ROW.match(line)
        if match:
            names[match.group(2)] = match.group(1)
    return names


def load_builder():
    spec = importlib.util.spec_from_file_location("module_start_apparatus_874", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mapping_problems(table, names):
    """Each disagreement between the table and a ``{token: name}`` mapping."""
    problems = []
    for token in sorted(set(table) | set(names)):
        if table.get(token) != names.get(token):
            problems.append("%s: table %r, mapping %r" % (token, table.get(token),
                                                           names.get(token)))
    return problems


def resume_problems(out, name):
    """What is wrong with a resume message that should name ``name``."""
    problems = []
    if name not in out:
        problems.append("does not name %r" % name)
    for hit in MODULE_NUMBER.findall(out):
        problems.append("shows %r" % hit)
    return problems


def run_session_start(test, progress, preferences=None, script=SESSION_START):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "config").mkdir()
        (root / "config" / "bootcamp_progress.json").write_text(
            json.dumps(progress), encoding="utf-8")
        if preferences is not None:
            (root / "config" / "bootcamp_preferences.yaml").write_text(
                preferences, encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONPATH"] = str(SCRIPTS)  # a mutated copy finds its siblings here
        proc = subprocess.run([sys.executable, str(script)], input=b"{}",
                              capture_output=True, cwd=str(root), env=env, timeout=60)
    err = proc.stderr.decode("utf-8")
    test.assertEqual(0, proc.returncode, err)
    test.assertNotIn("Traceback", err)
    out = proc.stdout.decode("utf-8")
    test.assertIn("A Senzing bootcamp is in progress.", out, "the resume message disappeared")
    return out


class TheMappingIsTheModuleTable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.table = table_names(PREP.read_text(encoding="utf-8"))
        cls.builder = load_builder()

    def test_the_table_is_parsed(self):
        self.assertGreaterEqual(len(self.table), 11, self.table)
        self.assertEqual("SDK setup", self.table.get("sdk_setup"))

    def test_the_mapping_equals_the_table(self):
        self.assertEqual([], mapping_problems(self.table, self.builder.DISPLAY_NAMES))

    def test_graduation_name_is_the_tables(self):
        self.assertEqual(self.table["graduation"], self.builder.GRADUATION_NAME)

    def test_negative_control_a_renamed_module_is_caught(self):
        text = PREP.read_text(encoding="utf-8")
        renamed = text.replace("| SDK setup |", "| SDK installation |", 1)
        self.assertNotEqual(text, renamed, "the mutation no longer applies")
        self.assertTrue(mapping_problems(table_names(renamed), self.builder.DISPLAY_NAMES))

    def test_negative_control_an_added_module_is_caught(self):
        added = dict(self.table, new_module="A new module")
        self.assertTrue(mapping_problems(added, self.builder.DISPLAY_NAMES))

    def test_a_name_is_found_from_any_spelling_of_the_key(self):
        for module in ("data_quality_mapping", "module_05_data_quality_mapping",
                       "module-05-data-quality-mapping", "Data Quality, Mapping, and "
                       "Transformation", "DATA_QUALITY_MAPPING", "bootcamp_graduation"):
            with self.subTest(module=module):
                self.assertIsNotNone(self.builder.display_name(module))
        for module in (None, "", "  ", 5, "module_5", "Module 5", "nonsense"):
            with self.subTest(module=module):
                self.assertIsNone(self.builder.display_name(module))


class TheResumeMessageNamesTheModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.table = table_names(PREP.read_text(encoding="utf-8"))

    def test_every_module_is_named_with_its_step(self):
        for token, name in self.table.items():
            with self.subTest(module=token):
                out = run_session_start(self, {"current_module": token, "current_step": 11})
                self.assertEqual([], resume_problems(out, name))
                self.assertIn('"Where you left off: %s, step 11."' % name, out)

    def test_every_module_not_begun_is_named_without_a_step(self):
        for token, name in self.table.items():
            with self.subTest(module=token):
                out = run_session_start(self, {"current_module": token, "current_step": None})
                self.assertEqual([], resume_problems(out, name))
                self.assertIn('"Where you left off: %s."' % name, out)

    def test_the_apparatus_reminder_is_appended_unchanged(self):
        out = run_session_start(self, {"current_module": "sdk_setup", "current_step": None})
        self.assertIn("Module-start reminder: the recorded module, `sdk_setup`, has not begun "
                      "yet", out)
        self.assertIn("offer to resume from the last recorded module, SDK setup,", out)

    def test_graduation_uses_the_graduation_name(self):
        builder = load_builder()
        out = run_session_start(self, {"current_module": "graduation", "current_step": None})
        self.assertIn('"Where you left off: %s."' % builder.GRADUATION_NAME, out)

    def test_a_letter_step_is_kept_and_odd_steps_are_left_out(self):
        out = run_session_start(self, {"current_module": "sdk_setup", "current_step": "4a"})
        self.assertIn('"Where you left off: SDK setup, step 4a."', out)
        for step in ("Module 5 step 3", True, [3], {"n": 3}, "three"):
            with self.subTest(current_step=step):
                out = run_session_start(self, {"current_module": "sdk_setup",
                                               "current_step": step})
                self.assertIn('"Where you left off: SDK setup."', out)
                self.assertEqual([], resume_problems(out, "SDK setup"))

    def test_an_unknown_key_keeps_the_generic_wording(self):
        self.assertIn("Where you left off",
                      run_session_start(self, {"current_module": "sdk_setup"}),
                      "(control: a known key)")
        for module in ("module_5", "Module 5", "something_else"):
            with self.subTest(module=module):
                out = run_session_start(self, {"current_module": module, "current_step": 3})
                self.assertIn(GENERIC, out)
                self.assertNotIn("Where you left off", out)
                self.assertEqual([], MODULE_NUMBER.findall(out))

    def test_negative_control_a_message_with_a_number_is_caught(self):
        source = SESSION_START.read_text(encoding="utf-8")
        old = 'where = "Where you left off: %s" % name'
        self.assertIn(old, source, "the mutation no longer applies")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / SESSION_START.name
            path.write_text(source.replace(
                old, 'where = "Where you left off: Module 5, %s" % name', 1), encoding="utf-8")
            out = run_session_start(self, {"current_module": "data_quality_mapping",
                                           "current_step": 11}, script=path)
        self.assertEqual(["shows 'Module 5'"],
                         resume_problems(out, "Data Quality, Mapping, and Transformation"))


def step_two(text):
    """Step 2 of `bootcamp-onboarding/SKILL.md`, up to step 3 or the next heading."""
    start = text.index("2. **Fresh start vs. resume")
    end = text.index("\n## ", start)
    return text[start:end]


def form_problems(section):
    """What step 2 is missing of the pinned resume offer."""
    flat = re.sub(r"\s+", " ", section)
    problems = []
    if '"Where you left off: {module name}, step {N}."' not in flat:
        problems.append("no pinned form with the step")
    if '"Where you left off: {module name}."' not in flat:
        problems.append("no pinned form without the step")
    rule = [line for line in section.splitlines()
            if re.match(r"⛔ \*\*\((?:INV-\d+, )*INV-079\)", line.strip()) and "never by a module number" in line]
    if not rule:
        problems.append("no ⛔ rule citing INV-079 on its own line")
    return problems


class TheResumeOfferIsPinned(unittest.TestCase):

    def test_step_two_pins_the_form_and_the_rule(self):
        self.assertEqual([], form_problems(step_two(ONBOARDING.read_text(encoding="utf-8"))))

    def test_negative_control_a_step_two_without_them_is_caught(self):
        section = step_two(ONBOARDING.read_text(encoding="utf-8"))
        unpinned = section.replace("{module name}, step {N}.", "{module}.")
        self.assertIn("no pinned form with the step", form_problems(unpinned))
        uncited = re.sub(r"⛔ \*\*\((?:INV-\d+, )*INV-079\)", "⛔ **", section)
        self.assertIn("no ⛔ rule citing INV-079 on its own line", form_problems(uncited))


if __name__ == "__main__":
    unittest.main()
