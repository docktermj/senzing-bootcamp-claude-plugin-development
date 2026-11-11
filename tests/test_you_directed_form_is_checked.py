"""The `**You directed:**` line is checked where it is written, in the form its value selects (#915).

The line is written only to the recap file's End-of-Module Summary (`module-completion.md`
Step 2b) and never shown in a turn. In both #855 judging walks, Data Quality, Mapping, and
Transformation recorded `directing_steps: none` and wrote a paraphrase instead of the pinned
no-site form, and nothing caught either half:

- `generate_recap_pdf.py --check` validated the three summary blocks and "nothing else". It
  now reports a directing module whose line is missing or not the form its `directing_steps`
  value selects.
- `transcript_lint.check_directing_steps` looked for the no-site line in the turns only. It
  now also reads the module's section of the walk's `docs/bootcamp_recap.md`, and accepts the
  pinned form only.

`--check` runs as a subprocess in a scratch project; nothing under `plugins/` is imported
(INV-108), and its patterns are read from the script's source. Every negative case has a twin
that passes, and `NegativeControls` cut each half out and require a case to fail.

Enforces INV-354's dated note of 2026-11-11 (#915), registered 2026-11-11. It cannot
establish that a live guide writes the pinned form; only a walk observes that.

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
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
RECAP_PDF = SCRIPTS / "generate_recap_pdf.py"
GROUND_RULES = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
                / "ground-rules.md")
COMPLETION = GROUND_RULES.parent / "module-completion.md"
LINT_DIR = REPO_ROOT / ".claude" / "skills" / "auto-test"
LINT = LINT_DIR / "transcript_lint.py"
sys.path.insert(0, str(LINT_DIR))

import transcript_lint  # noqa: E402

M5 = "Data Quality, Mapping, and Transformation"
M6 = "Data processing"
PARAPHRASE = ("**You directed:** No directing step arose for this source: every column "
              "mapped at 0.80 confidence or above.")
PINNED = {
    "none": ("**You directed:** nothing this module. Every column mapped at 0.80 confidence "
             "or above, so there was no step to hand over."),
    "skipped": ("**You directed:** nothing this module. This module's directing step (step "
                "11) was skipped, so you were not asked to direct it."),
    "guide_chose": ('**You directed:** nothing this module. You asked me to choose ("you '
                    'pick"), so the guide chose the default mapping.'),
    "directed": ("**You directed:** map NAME_ORG as the organization. You caught: the phone "
                 "column was a fax."),
}


def section(name, directed_line):
    lines = ["## %s — 2026-11-11" % name, "", "### Information Shared", "- x", "",
             "### Questions & Responses", "- **Q:** q", "    - **R:** r", "",
             "### Actions Taken", "- y", "", "### End-of-Module Summary",
             "**What you accomplished:**", "- a", "", "**Files produced:**", "- `f` — g", "",
             "**Why it matters:** it matters."]
    if directed_line:
        lines.append(directed_line)
    return "\n".join(lines) + "\n\n"


def recap(*sections):
    return "# Bootcamp recap\n\n" + "".join(sections)


class Project:

    def __init__(self, test, recap_text, steps=None):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "config").mkdir()
        (self.root / "docs" / "bootcamp_recap.md").write_text(recap_text, encoding="utf-8")
        if steps is not None:
            (self.root / "config" / "bootcamp_progress.json").write_text(
                json.dumps({"directing_steps": steps}), encoding="utf-8")

    def check(self, script=RECAP_PDF):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        proc = subprocess.run([sys.executable, str(script), "--check"], capture_output=True,
                              cwd=str(self.root), env=env, timeout=120)
        return proc.returncode, proc.stderr.decode("utf-8")


def directed_problems(err):
    return [line for line in err.splitlines()
            if line.startswith("INCOMPLETE:") and "You directed:" in line]


class TheRecapCheckReadsTheForm(unittest.TestCase):

    def test_the_2026_11_11_paraphrase_is_reported(self):
        code, err = Project(self, recap(section(M5, PARAPHRASE)), {"data_quality_mapping":
                                                                   "none"}).check()
        self.assertEqual(1, code)
        self.assertEqual(1, len(directed_problems(err)), err)
        self.assertIn("not the form directing_steps 'none' selects", err)

    def test_each_pinned_form_passes(self):
        for value, line in PINNED.items():
            with self.subTest(value=value):
                _, err = Project(self, recap(section(M5, line)),
                                 {"data_quality_mapping": value}).check()
                self.assertEqual([], directed_problems(err))

    def test_a_form_for_another_value_is_reported(self):
        _, err = Project(self, recap(section(M5, PINNED["skipped"])),
                         {"data_quality_mapping": "none"}).check()
        self.assertEqual(1, len(directed_problems(err)), err)

    def test_a_missing_line_is_reported(self):
        _, err = Project(self, recap(section(M6, None)), {"data_processing": "directed"}).check()
        self.assertIn("has no **You directed:** line", err)

    def test_nothing_to_check_is_not_reported(self):
        cases = {
            "no progress file": (recap(section(M5, PARAPHRASE)), None),
            "no value": (recap(section(M5, PARAPHRASE)), {}),
            "an unknown value": (recap(section(M5, PARAPHRASE)), {"data_quality_mapping": "?"}),
            "no section": (recap(section(M6, PINNED["directed"])),
                           {"data_quality_mapping": "none", "data_processing": "directed"}),
        }
        for why, (text, steps) in cases.items():
            with self.subTest(why=why):
                _, err = Project(self, text, steps).check()
                self.assertEqual([], directed_problems(err))


class ThePatternsMatchTheTemplates(unittest.TestCase):
    """Each form's template in ground-rules.md, its placeholders filled, matches its pattern
    and only its pattern."""

    def forms(self):
        tree = ast.parse(RECAP_PDF.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                    getattr(t, "id", "") == "YOU_DIRECTED_FORMS" for t in node.targets):
                return {k.value: re.compile(ast.literal_eval(v.args[0]))
                        for k, v in zip(node.value.keys, node.value.values)}
        self.fail("YOU_DIRECTED_FORMS is gone from generate_recap_pdf.py")

    def templates(self):
        text = re.sub(r"\s+", " ", GROUND_RULES.read_text(encoding="utf-8"))
        found = {}
        for label, value in (("handed back", "guide_chose"), ("no site", "none"),
                             ("skipped", "skipped")):
            m = re.search(r"- %s: `(\*\*You directed:\*\*[^`]+)`" % label, text)
            self.assertIsNotNone(m, "ground-rules.md no longer states the %s form" % label)
            found[value] = m.group(1)
        m = re.search(r"- directed: `(\*\*You directed:\*\*[^`]+)`", text)
        self.assertIsNotNone(m, "ground-rules.md no longer states the directed form")
        found["directed"] = m.group(1)
        return {k: re.sub(r"\{[^}]*\}", "x", v) for k, v in found.items()}

    def test_each_template_matches_its_pattern_only(self):
        forms, templates = self.forms(), self.templates()
        self.assertEqual(set(forms), set(templates))
        for value, line in templates.items():
            with self.subTest(value=value):
                self.assertTrue(forms[value].match(line), line)
                others = [k for k, p in forms.items() if k != value and p.match(line)]
                self.assertEqual([], others, "%r also matches %s" % (line, others))


class TheLintReadsTheRecap(unittest.TestCase):

    TURNS = ["Where you left off: %s, step 11." % M5,
             "**Module complete**\n\n\U0001f449 **Are you ready to move on to the next "
             "module: Data processing?**"]

    def findings(self, project):
        return [f for f in transcript_lint.check_directing_steps(self.TURNS, project)
                if f["code"] == "INV-354-directing-step-missing"]

    def test_the_pinned_line_in_the_recap_excuses_module_5(self):
        project = Project(self, recap(section(M5, PINNED["none"])))
        self.assertEqual([], self.findings(str(project.root)))

    def test_the_paraphrase_does_not(self):
        project = Project(self, recap(section(M5, PARAPHRASE)))
        self.assertEqual(1, len(self.findings(str(project.root))))

    def test_with_no_project_or_section_only_the_turns_are_read(self):
        self.assertEqual(1, len(self.findings(None)))
        project = Project(self, recap(section(M6, PINNED["none"])))
        self.assertEqual(1, len(self.findings(str(project.root))))

    def test_lint_passes_the_project(self):
        project = Project(self, recap(section(M5, PINNED["none"])))
        found = transcript_lint.lint(self.TURNS, project=str(project.root))
        self.assertNotIn("INV-354-directing-step-missing", [f["code"] for f in found])


class NegativeControls(unittest.TestCase):

    def test_without_the_form_check_the_paraphrase_passes(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        copy = Path(tmp.name) / "scripts"
        shutil.copytree(SCRIPTS, copy, ignore=shutil.ignore_patterns("__pycache__", "vendor"))
        script = copy / RECAP_PDF.name
        source = script.read_text(encoding="utf-8")
        old = "def directed_line_problems(recap: Recap, steps: Dict[str, str]) -> List[str]:\n"
        self.assertIn(old, source, "the function moved; update the control")
        script.write_text(source.replace(old, old + "    return []\n", 1), encoding="utf-8")
        _, err = Project(self, recap(section(M5, PARAPHRASE)),
                         {"data_quality_mapping": "none"}).check(script)
        self.assertEqual([], directed_problems(err))

    def test_without_the_recap_read_module_5_fails_the_lint(self):
        source = LINT.read_text(encoding="utf-8")
        old = "section = _recap_section(project, span[\"name\"])"
        self.assertIn(old, source, "the recap read moved; update the control")
        namespace = {"__file__": str(LINT), "__name__": "transcript_lint_mutant"}
        exec(compile(source.replace(old, "section = None", 1), str(LINT), "exec"),  # noqa: S102
             namespace)
        project = Project(self, recap(section(M5, PINNED["none"])))
        found = namespace["check_directing_steps"](TheLintReadsTheRecap.TURNS,
                                                   str(project.root))
        self.assertEqual(1, len(found))


class TheSkillSaysSo(unittest.TestCase):

    def test_step_2b_names_the_form_check(self):
        text = re.sub(r"\s+", " ", COMPLETION.read_text(encoding="utf-8"))
        self.assertNotIn("validates the three labels above and nothing else", text)
        self.assertIn("is the form its `directing_steps` value selects", text)


if __name__ == "__main__":
    unittest.main()
