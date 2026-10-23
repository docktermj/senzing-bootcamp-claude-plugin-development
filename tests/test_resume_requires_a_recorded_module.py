""""A bootcamp is underway" must mean the progress file RECORDS a module, not that it exists.

The onboarding preface creates `config/bootcamp_progress.json` empty during its silent project
setup, and nothing writes a `current_module` until Bootcamp preparation's final consolidated
write. That window spans the whole preface plus all of Bootcamp preparation — the
Core/Customized gate, module selection, verbosity, the programming-language gate — so any quit
inside it produced, on the next session:

    A Senzing bootcamp is in progress. Read config/bootcamp_progress.json and offer
    to resume from the last recorded module before doing anything else.

…on a project with no recorded module. The guide was told to do something impossible, on a
project whose correct behavior was to run onboarding from the top.

Every resume decision tested the file's **existence** while
`recap_checkpoint.current_module()` already returned `None` for a contentless file — the
distinction the callers needed was computed and then unused. Fixing the shared predicate is
cheaper than fixing four call sites, which is what the spec asked for.

The four callers were checked before tightening it, and none loses anything in that window:
`session-end`/`precompact-recap` have no module recap to fold and no container to stop (containers
start in SDK setup, well after the first write), and `checkpoint-tick`'s scaffold-only case is one
it already skips.

⛔ The hooks are run as **subprocesses** with real stdin and a real working directory, because
they act at import time.

Enforces **INV-227** — a resume decision is made on recorded progress content, never on the progress file's existence.

**#605: one statement, pointed at, and every hook's gate named.** Session start in
`ground-rules.md` still said "If present, resume", and `/graduate` refused only a missing file,
so a file recording no module resumed a bootcamp that never started or passed into graduation.
The rule now lives in `bootcamp-onboarding/SKILL.md` step 2, and both sites point there (INV-300).
The hooks README said every hook gated on the file's existence, while four use
`bootcamp_active()`. Its Gate column is checked against each script's own gate, read from its
source rather than listed, and the three hooks that gate on existence must say why in the table
and in their docstrings: existence answers "is this a bootcamp project", which onboarding needs
before any module is recorded.

Source spec: `specs/empty-progress-file-makes-resume-unsatisfiable.md`; issue #605.

Run:  python3 -m unittest discover -s tests
"""
import ast
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
SESSION_START = SCRIPTS / "session-start.py"
ONBOARDING_SKILL = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
                    / "bootcamp-onboarding" / "SKILL.md")
START_COMMAND = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "commands"
                 / "start-bootcamp.md")
GROUND_RULES = ONBOARDING_SKILL.parent / "ground-rules.md"
GRADUATE_COMMAND = REPO_ROOT / "plugins" / "senzing-bootcamp" / "commands" / "graduate.md"
HOOKS_README = REPO_ROOT / "plugins" / "senzing-bootcamp" / "hooks" / "README.md"

#: The bold label in `bootcamp-onboarding/SKILL.md` step 2 that states the three-case rule (#605).
RULE_LABEL = ("Fresh start vs. resume — decided by the progress file's CONTENT, not its "
              "existence")

#: Progress-file contents that record NO module. Each must read as a fresh start, and none
#: may raise (INV-227).
CONTENTLESS = (
    ("empty object", "{}"),
    ("empty file", ""),
    ("whitespace only", "   \n"),
    ("not an object", "[1, 2, 3]"),
    ("malformed json", '{"current_module": '),
    ("module null", '{"current_module": null}'),
    ("module empty string", '{"current_module": ""}'),
    ("module blank", '{"current_module": "   "}'),
    ("other keys only", '{"os": "linux", "git_init": true}'),
)

RESUMABLE = (
    ("a module name", '{"current_module": "module_4_data_collection"}'),
    ("module plus step", '{"current_module": "sdk_setup", "current_step": 7}'),
)


def load_recap_checkpoint():
    spec = importlib.util.spec_from_file_location(
        "recap_checkpoint_resume_test", SCRIPTS / "recap_checkpoint.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProjectDir:
    """A scratch project with a given progress-file content (or none)."""

    def __init__(self, contents=None):
        self.contents = contents
        self.tmp = tempfile.TemporaryDirectory()

    def __enter__(self):
        root = Path(self.tmp.name)
        if self.contents is not None:
            (root / "config").mkdir()
            (root / "config" / "bootcamp_progress.json").write_text(
                self.contents, encoding="utf-8")
        return root

    def __exit__(self, *exc):
        self.tmp.cleanup()


def predicate_in(root):
    """`bootcamp_active()` as evaluated from `root` — it reads a relative path."""
    code = (
        "import sys; sys.path.insert(0, %r);\n"
        "import recap_checkpoint as r;\n"
        "print('ACTIVE' if r.bootcamp_active() else 'INACTIVE')\n" % str(SCRIPTS)
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          cwd=str(root), timeout=60)
    return proc.returncode, proc.stdout.strip(), proc.stderr


def session_start_in(root):
    proc = subprocess.run([sys.executable, str(SESSION_START)], input="{}",
                          capture_output=True, text=True, cwd=str(root), timeout=60)
    return proc.returncode, proc.stdout


class TheFixtureIsSound(unittest.TestCase):
    def test_the_scripts_exist(self):
        for path in (SCRIPTS / "recap_checkpoint.py", SESSION_START):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path)

    def test_a_resumable_project_is_active(self):
        """If this fails, every "inactive" assertion below could be vacuous."""
        with ProjectDir('{"current_module": "sdk_setup"}') as root:
            code, out, err = predicate_in(root)
            self.assertEqual(0, code, err)
            self.assertEqual("ACTIVE", out)


class AContentlessProgressFileIsNotAnActiveBootcamp(unittest.TestCase):
    def test_the_predicate_is_false_and_never_raises(self):
        for label, contents in CONTENTLESS:
            with self.subTest(case=label):
                with ProjectDir(contents) as root:
                    code, out, err = predicate_in(root)
                    self.assertEqual(0, code,
                                     "bootcamp_active() raised on %s (INV-227): %s"
                                     % (label, err))
                    self.assertEqual("INACTIVE", out,
                                     "%s reads as an active bootcamp, so the guide is "
                                     "told to resume from a module that is not there"
                                     % label)

    def test_session_start_prints_nothing(self):
        for label, contents in CONTENTLESS:
            with self.subTest(case=label):
                with ProjectDir(contents) as root:
                    code, out = session_start_in(root)
                    self.assertEqual(0, code)
                    self.assertEqual("", out.strip(),
                                     "session-start announced a resume for %s" % label)

    def test_a_missing_file_is_also_inactive(self):
        with ProjectDir(None) as root:
            _code, out, _err = predicate_in(root)
            self.assertEqual("INACTIVE", out)
            _code, printed = session_start_in(root)
            self.assertEqual("", printed.strip())


class ARecordedModuleStillResumes(unittest.TestCase):
    def test_the_predicate_is_true(self):
        for label, contents in RESUMABLE:
            with self.subTest(case=label):
                with ProjectDir(contents) as root:
                    _code, out, _err = predicate_in(root)
                    self.assertEqual("ACTIVE", out,
                                     "%s must still resume" % label)

    def test_the_resume_message_is_unchanged(self):
        with ProjectDir('{"current_module": "sdk_setup"}') as root:
            _code, out = session_start_in(root)
            self.assertIn("A Senzing bootcamp is in progress.", out,
                          "the resume message changed or disappeared")
            self.assertIn("offer to resume from the last recorded module", out)


class ThePredicateReadsContentNotExistence(unittest.TestCase):
    """Pins the mechanism, so a revert to `isfile` is caught even if a caller is rewritten."""

    def test_it_delegates_to_current_module(self):
        source = (SCRIPTS / "recap_checkpoint.py").read_text(encoding="utf-8")
        start = source.index("def bootcamp_active")
        body = source[start:source.index("\ndef ", start + 10)]
        self.assertIn("current_module() is not None", body,
                      "bootcamp_active() no longer tests for a recorded module")
        self.assertNotIn("os.path.isfile(PROGRESS)", body,
                         "bootcamp_active() is back to testing the file's existence")

    def test_current_module_still_absorbs_a_broken_file(self):
        """bootcamp_active() now depends on that contract, so it must stay documented."""
        module = load_recap_checkpoint()
        self.assertIsNotNone(module.current_module.__doc__,
                             "current_module() lost its docstring")
        self.assertIn("Never raises", module.current_module.__doc__,
                      "current_module()'s never-raises contract (INV-227) is undocumented, "
                      "and bootcamp_active() now depends on it")


class TheProseStatesTheThreeWayBranch(unittest.TestCase):
    def flat(self, path):
        import re
        return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

    def test_the_onboarding_skill_states_all_three_cases(self):
        flat = self.flat(ONBOARDING_SKILL)
        self.assertRegex(
            flat, r"(?i)decided by the progress file's CONTENT, not its existence",
            "the skill still branches on existence")
        self.assertRegex(flat, r"(?i)\*\*Missing\*\* -> this is a fresh bootcamp")
        self.assertRegex(
            flat, r"(?i)\*\*Present but recording no module\*\*",
            "the middle case — the one that was missing — is still absent")
        self.assertRegex(flat, r"(?i)\*\*Present with a `current_module`\*\* -> a bootcamp is "
                               r"already underway")

    def test_the_onboarding_skill_says_it_is_not_a_corruption(self):
        flat = self.flat(ONBOARDING_SKILL)
        self.assertRegex(
            flat, r"(?i)this is the \*?normal\*? state, not a corruption",
            "without this a guide reports the empty file to the bootcamper, which is the "
            "output INV-012 suppresses")
        self.assertRegex(flat, r"(?i)Never announce a resume you cannot perform",
                         "the rule the defect broke is not stated")

    def test_the_start_command_states_all_three_cases(self):
        flat = self.flat(START_COMMAND)
        self.assertRegex(
            flat, r"(?i)what `config/bootcamp_progress\.json` \*\*contains\*\*, not by whether "
                  r"it exists",
            "the slash command still branches on existence")
        for case in (r"\*\*No file\*\*", r"\*\*A file recording no module\*\*",
                     r"\*\*A file with a `current_module`\*\*"):
            with self.subTest(case=case):
                self.assertRegex(flat, case, "the command omits a case")


def flat(text):
    return re.sub(r"\s+", " ", text)


def section(text, heading):
    """The lines from ``heading`` to the next heading of the same or a higher level."""
    lines = text.split("\n")
    start = lines.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r"#{1,%d} " % level, lines[i])), len(lines))
    return "\n".join(lines[start:end])


def points_at_the_rule(path, text):
    """Whether ``text`` (held at ``path``) has a pointer to the rule's label, citing INV-227."""
    from _pointer_sites import section_pointers
    for _, target, name in section_pointers(path, text):
        if (path.parent / target).resolve() == ONBOARDING_SKILL.resolve() \
                and flat(name) == RULE_LABEL:
            return "INV-227" in text
    return False


def script_gate(source):
    """``"bootcamp_active"`` or ``"existence"``: the gate a hook script's code applies.

    Read from the tests of the script's module-level ``if`` statements, so a docstring that
    names the other gate (as the existence-gated ones now do, to say why) is not mistaken
    for code.
    """
    tests = [ast.unparse(node.test) for node in ast.parse(source).body
             if isinstance(node, ast.If)]
    active = any("recap_checkpoint.bootcamp_active()" in test for test in tests)
    exists = any("os.path.isfile(os.path.join('config', 'bootcamp_progress.json'))" in test
                 for test in tests)
    if active == exists:
        return None
    return "bootcamp_active" if active else "existence"


def readme_gates(text):
    """``{script: gate cell}`` from the hooks README table's Gate column."""
    rows = [line for line in text.splitlines() if line.startswith("| `")]
    header = next(line for line in text.splitlines() if line.startswith("| Event |"))
    cells = [c.strip() for c in header.strip("|").split("|")]
    column = cells.index("Gate")
    gates = {}
    for row in rows:
        parts = [c.strip() for c in row.strip("|").split("|")]
        m = re.match(r"`scripts/([\w-]+\.py)`", parts[1])
        if m:
            gates[m.group(1)] = parts[column]
    return gates


def gate_problems(readme_text, sources):
    """Each disagreement between the README's Gate column and each script's own gate."""
    problems = []
    gates = readme_gates(readme_text)
    for script, source in sorted(sources.items()):
        kind = script_gate(source)
        cell = gates.get(script)
        if cell is None:
            problems.append("%s has no Gate cell" % script)
        elif kind == "bootcamp_active" and not cell.startswith("`bootcamp_active()`"):
            problems.append("%s gates on bootcamp_active() but the README says %r"
                            % (script, cell))
        elif kind == "existence" and not (cell.startswith("Existence:")
                                          and len(cell) > len("Existence:") + 20):
            problems.append("%s gates on existence but the README's cell %r does not say so "
                            "with a reason" % (script, cell))
    return problems


def docstring_states_why(source):
    """Whether a script's docstring says it tests existence on purpose, and why (INV-227)."""
    doc = flat(ast.get_docstring(ast.parse(source)) or "")
    return bool(re.search(r"(?i)existence\W+on purpose", doc)) \
        and "is this a bootcamp project" in doc and "INV-227" in doc


def gated_scripts():
    """``{name: source}`` for every hook script hooks.json registers, read as text (INV-108)."""
    hooks = json.loads((REPO_ROOT / "plugins" / "senzing-bootcamp" / "hooks" / "hooks.json")
                       .read_text(encoding="utf-8"))
    names = set()
    for entries in hooks["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                m = re.search(r"/scripts/([\w-]+\.py)", hook.get("command", ""))
                if m:
                    names.add(m.group(1))
    return {name: (SCRIPTS / name).read_text(encoding="utf-8") for name in names}


class TheRuleIsStatedOnceAndPointedAt(unittest.TestCase):
    """#605: session start and /graduate point at SKILL.md's rule rather than test existence."""

    def test_the_label_names_a_section_of_the_skill(self):
        from _pointer_sites import names_a_section
        self.assertTrue(names_a_section(ONBOARDING_SKILL.read_text(encoding="utf-8"),
                                        RULE_LABEL),
                        "the rule's bold label in SKILL.md step 2 changed; every pointer to it "
                        "now lands nowhere")

    def test_the_skill_says_it_owns_the_rule(self):
        text = flat(ONBOARDING_SKILL.read_text(encoding="utf-8"))
        self.assertRegex(text, r"This step is where the rule is stated: session start .* and "
                               r"`/graduate` point here rather than restating it "
                               r"\(INV-227, INV-300\)")

    def test_session_start_points_at_the_rule(self):
        text = section(GROUND_RULES.read_text(encoding="utf-8"), "## Session start")
        self.assertTrue(points_at_the_rule(GROUND_RULES, text),
                        "ground-rules.md's Session start no longer points at the rule")
        self.assertNotRegex(flat(text), r"(?i)if present, resume",
                            "session start decides by the file's existence again")

    def test_graduate_points_at_the_rule(self):
        text = GRADUATE_COMMAND.read_text(encoding="utf-8")
        self.assertTrue(points_at_the_rule(GRADUATE_COMMAND, text),
                        "/graduate no longer points at the rule")
        self.assertNotRegex(flat(text), r"If no `config/bootcamp_progress\.json` exists",
                            "/graduate decides by the file's existence again")

    def test_graduate_refuses_a_file_that_records_no_module(self):
        text = flat(GRADUATE_COMMAND.read_text(encoding="utf-8"))
        self.assertRegex(text, r"whether the file is missing or records no module, tell the "
                               r"bootcamper there is no bootcamp to graduate")

    def test_the_skill_names_only_the_recap_hooks_as_silent(self):
        text = flat(ONBOARDING_SKILL.read_text(encoding="utf-8"))
        self.assertIn("so the recap hooks stay silent in that window", text)
        self.assertNotIn("so the hooks stay silent", text)


class TheHooksReadmeNamesEachGate(unittest.TestCase):
    """#605: the Gate column agrees with each script's code, which is read, not listed."""

    @classmethod
    def setUpClass(cls):
        cls.sources = gated_scripts()
        cls.readme = HOOKS_README.read_text(encoding="utf-8")

    def test_every_script_has_a_readable_gate(self):
        kinds = {name: script_gate(src) for name, src in self.sources.items()}
        self.assertNotIn(None, kinds.values(),
                         "a hook script's gate is neither form this guard reads: %s" % kinds)
        self.assertGreaterEqual(list(kinds.values()).count("bootcamp_active"), 4, kinds)
        self.assertGreaterEqual(list(kinds.values()).count("existence"), 3, kinds)

    def test_the_readme_gate_column_matches_the_code(self):
        self.assertEqual([], gate_problems(self.readme, self.sources))

    def test_each_existence_gated_script_says_why(self):
        for name, source in sorted(self.sources.items()):
            if script_gate(source) == "existence":
                with self.subTest(script=name):
                    self.assertTrue(docstring_states_why(source),
                                    "%s gates on existence without saying why in its "
                                    "docstring" % name)

    def test_the_readme_no_longer_says_every_hook_gates_on_an_active_bootcamp(self):
        self.assertNotIn("Every hook is gated on an active bootcamp", self.readme)


class NegativeControls(unittest.TestCase):
    """Each check above must turn red on the defect it guards against."""

    def test_the_old_session_start_line_is_caught(self):
        text = section(GROUND_RULES.read_text(encoding="utf-8"), "## Session start")
        start = text.index("- Decide whether to resume")
        end = text.index("\n- ", start + 1)
        reverted = (text[:start] + "- Check `config/bootcamp_progress.json`. If present, "
                    "resume; if not, run onboarding." + text[end:])
        self.assertFalse(points_at_the_rule(GROUND_RULES, reverted))

    def test_a_pointer_to_a_wrong_label_is_caught(self):
        text = GRADUATE_COMMAND.read_text(encoding="utf-8")
        self.assertFalse(points_at_the_rule(
            GRADUATE_COMMAND, text.replace("not its\nexistence", "not its\nshape")
                                  .replace("not its existence", "not its shape")))

    def test_a_wrong_gate_cell_is_caught(self):
        readme = HOOKS_README.read_text(encoding="utf-8")
        sources = gated_scripts()
        row = next(l for l in readme.splitlines() if "`scripts/stop-nudge.py`" in l)
        cell = row.rstrip(" |").rsplit("|", 1)[1].strip()
        self.assertTrue(cell.startswith("Existence:"), cell)
        wrong = readme.replace(row, row.replace(cell, "`bootcamp_active()`: wrong."))
        self.assertTrue(gate_problems(wrong, sources))
        bare = readme.replace(row, row.replace(cell, "Existence:"))
        self.assertTrue(gate_problems(bare, sources), "a cell with no reason passed")

    def test_a_script_switched_to_bootcamp_active_is_caught(self):
        readme = HOOKS_README.read_text(encoding="utf-8")
        sources = gated_scripts()
        sources["write-gate.py"] = sources["write-gate.py"].replace(
            'if not os.path.isfile(os.path.join("config", "bootcamp_progress.json")):',
            "if not recap_checkpoint.bootcamp_active():")
        self.assertEqual("bootcamp_active", script_gate(sources["write-gate.py"]))
        self.assertTrue(gate_problems(readme, sources))

    def test_a_docstring_without_the_reason_is_caught(self):
        source = (SCRIPTS / "feedback-capture.py").read_text(encoding="utf-8")
        self.assertTrue(docstring_states_why(source))
        self.assertFalse(docstring_states_why(source.replace("on purpose", "")))


if __name__ == "__main__":
    unittest.main()
