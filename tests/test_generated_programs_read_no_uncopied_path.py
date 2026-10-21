"""#755: a generated program reads at runtime no path graduation leaves behind.

Graduation's Step 2 copies `src/load/**` and `src/query/**` into `production/` verbatim and
leaves the rest behind. One run's loader read `database_type` from
`config/bootcamp_preferences.yaml` at runtime to pick its worker count, so the handed-over loader
found no such file and fell back to one worker on PostgreSQL too: nothing failed, it was just
slow. On the same run `src/query/` programs read `data/truth/scenario_truth.json`, which
graduation neither copies nor excludes. Neither read was prescribed; nothing forbade them.

Three things are pinned here:

1. **The rule, stated once** (`phaseA-build-loading.md`, beside INV-296): the worker count is a
   constant in the generated code; no generated program reads, at runtime, a path graduation
   Step 2 does not copy, which is cited by pointer to Step 2 and never restated (INV-300); an
   input taken from the registry entry is not such a read; a runtime choice by database comes
   from `SQL.CONNECTION`'s scheme. Module 7's query step points at it.
2. **The guard over the program-generation instructions.** No Module 6 or Module 7 skill file
   directs a generated program to read an uncopied path. The uncopied set is computed from
   Step 2 (INV-246): a project path that no Source cell of its copy table covers, which takes in
   its **Exclude** list and anything it neither copies nor excludes. A directive is a sentence in
   which a program, loader, orchestrator, exporter, script or code reads, loads, opens or parses
   a backticked path, or reads one "at runtime" / "when it runs". A sentence tied to the
   registry (`config/data_sources.yaml`, `file_path`, "registry") is the rule's own exception, and
   a negated one ("no program reads …") is a prohibition, not a directive.
3. **Graduation Step 2 states the scan**: it runs the bundled `scan_uncopied_paths.py`, and each
   line it prints becomes a migration-checklist item naming the file and the path. The script's
   behavior is tested in `tests/test_scan_uncopied_paths.py`.

⚠️ **What the guard cannot see:** a directive worded without one of those verbs or subjects, a
path written without backticks, and a read the guide improvises with no instruction behind it.
The last is the case #755 found; graduation's scan is the net for it.

Stdlib-only and no `plugins/` import (INV-108): the files are read as text.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import collapsed_blocks
from test_module6_data_dirs_are_copied_or_excluded import EXCLUDE, excluded, step2

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE6 = SKILLS / "module-06-data-processing"
MODULE7 = SKILLS / "module-07-query-visualize-discover"
PHASE_A = MODULE6 / "phaseA-build-loading.md"
QUERY_STEP = MODULE7 / "phase1-query-visualize.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

ANCHOR = "no-runtime-reads-of-uncopied-paths"
RULE_LEAD = ("⛔ **The worker count is fixed in the generated code, and no generated program "
             "reads at runtime a path graduation leaves behind.**")
SCAN_LEAD = "**Scan the copied code for paths this step left behind.**"

BACKTICKED = re.compile(r"`([^`]+)`")
#: A generated program as the subject, then a read verb; what it reads follows, up to `;` or a
#: sentence-ending `.` (a `.` inside `bootcamp_preferences.yaml` does not end it).
PROGRAM_READS = re.compile(
    r"\b(?:programs?|loaders?|orchestrator|exporter|scripts?|code)\s+(?:\w+\s+){0,3}?"
    r"(?:reads?|loads?|opens?|parses?)\b((?:[^.;]|\.(?=\S)){0,100})", re.I)
#: A read verb, then what it reads, then "at runtime" or "when it runs".
READS_AT_RUNTIME = re.compile(
    r"\b(?:reads?|loads?|opens?|parses?)\b((?:[^.;]|\.(?=\S)){0,140}?)"
    r"\b(?:at runtime|when it runs)\b", re.I)

#: The rule's own exception: an input the program takes from its registry entry.
REGISTRY = re.compile(r"registry|`file_path`|`config/data_sources\.yaml`")
NEGATED = re.compile(r"\b(?:no|never|not|nothing)\b", re.I)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z*`(⛔⚠👉])")


def flat(text):
    return " ".join(text.split())


def copy_sources(graduation):
    """Each backticked Source cell of Step 2's copy table, `**` dropped.

    Line-scoped by design (#755, as #424 settled for this table): a table row is one line.
    """
    sources = set()
    for line in step2(graduation).splitlines():
        if line.startswith("| `"):
            sources.update(p.replace("**", "") for p in BACKTICKED.findall(line.split("|")[1]))
    return sources


def project_roots(graduation):
    """The project's top-level directories Step 2 names, as copied or as excluded."""
    return {p.split("/")[0] for p in copy_sources(graduation) | excluded(graduation) if "/" in p}


def is_uncopied(path, graduation):
    """True for a project path that no Source cell of Step 2's copy table covers."""
    if path.split("/")[0] not in project_roots(graduation):
        return False
    for source in copy_sources(graduation):
        if path.rstrip("/") == source.rstrip("/"):
            return False
        if source.endswith("/") and path.startswith(source):
            return False
    return True


def sentences(text):
    """Each sentence of each Markdown block, wrapped lines joined (INV-346)."""
    for block, _origin in collapsed_blocks(text):
        yield from SENTENCE_END.split(block)


def directives(text, graduation):
    """Each `(path, sentence)` where ``text`` directs a program to read an uncopied path."""
    found = []
    for sentence in sentences(text):
        if REGISTRY.search(sentence):
            continue
        for pattern in (PROGRAM_READS, READS_AT_RUNTIME):
            for m in pattern.finditer(sentence):
                if NEGATED.search(sentence[max(0, m.start() - 20):m.end()]):
                    continue
                for path in BACKTICKED.findall(m.group(1)):
                    if is_uncopied(path, graduation):
                        found.append((path, sentence[:160]))
    return found


def generation_instructions():
    return sorted(MODULE6.glob("*.md")) + sorted(MODULE7.glob("*.md"))


def rule_paragraph(text):
    start = text.index('<a id="%s"></a>' % ANCHOR)
    end = text.index("\n\n", start)
    return flat(text[start:end])


def scan_paragraphs(graduation):
    """Step 2's scan, from its lead to the paragraph that ends the step."""
    section = step2(graduation)
    start = section.index(SCAN_LEAD)
    end = section.index("Present a short, one-line statement", start)
    return flat(section[start:end])


class TheRuleIsStatedOnceInModule6(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = PHASE_A.read_text(encoding="utf-8")
        cls.graduation = GRADUATION.read_text(encoding="utf-8")
        cls.rule = rule_paragraph(cls.text)

    def test_the_rule_sits_in_the_worker_count_bullet(self):
        start = self.text.index("- **`small`, `medium`, or `large`:**")
        end = self.text.index("- **`demo`:**", start)
        self.assertIn(RULE_LEAD, flat(self.text[start:end]),
                      "the rule belongs beside INV-296, where the worker count is chosen")

    def test_the_worker_count_is_a_constant_the_program_never_reads(self):
        self.assertIn("The guide reads `database_type` here, while generating; the program "
                      "never does.", self.rule)
        self.assertIn("Write the count into the code as a constant", self.rule)

    def test_the_forbidden_set_is_cited_by_pointer_to_step_2(self):
        self.assertIn('`../graduation/SKILL.md` → "Step 2: Build the production project" does '
                      "not copy into `production/`", self.rule)
        self.assertIn("its **Exclude** list, and anything it neither copies nor excludes",
                      self.rule)
        self.assertIn("## Step 2: Build the production project", self.graduation,
                      "the pointer's target heading moved")

    def test_the_rule_restates_no_entry_of_the_exclude_list(self):
        """INV-300: a pointer, not a copy. Computed from the live Exclude list."""
        restated = sorted(e for e in excluded(self.graduation) if e in self.rule)
        self.assertEqual([], restated, "the rule restates Step 2's Exclude list; point at it")

    def test_restating_the_list_is_caught(self):
        """Negative control for the test above."""
        copy = self.rule + " Never read `config/bootcamp_progress.json`."
        self.assertEqual(["config/bootcamp_progress.json"],
                         sorted(e for e in excluded(self.graduation) if e in copy))

    def test_a_runtime_choice_comes_from_the_connection_scheme(self):
        self.assertIn("derives it from the scheme of `SQL.CONNECTION` in "
                      "`SENZING_ENGINE_CONFIGURATION_JSON` (`sqlite3://`, `postgresql://`, …)",
                      self.rule)

    def test_a_registry_input_is_the_stated_exception(self):
        self.assertIn("An input file a program takes from its `config/data_sources.yaml` entry "
                      "is not such a read", self.rule)

    def test_the_rule_is_stated_once(self):
        """Module 6 and Module 7 carry the lead once, in Phase A, and nowhere else."""
        carriers = [p.name for p in generation_instructions()
                    if RULE_LEAD in flat(p.read_text(encoding="utf-8"))]
        self.assertEqual(["phaseA-build-loading.md"], carriers)

    def test_module_7s_query_step_points_at_it(self):
        text = flat(QUERY_STEP.read_text(encoding="utf-8"))
        start = text.index("## 2. Create query programs")
        end = text.index("⛔ **(INV-152)", start)
        self.assertIn("(../module-06-data-processing/phaseA-build-loading.md#%s)" % ANCHOR,
                      text[start:end])

    def test_graduation_step_2_points_at_it(self):
        self.assertIn("(../module-06-data-processing/phaseA-build-loading.md#%s)" % ANCHOR,
                      scan_paragraphs(self.graduation))


class NoGenerationInstructionDirectsAnUncopiedRead(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graduation = GRADUATION.read_text(encoding="utf-8")

    def test_the_uncopied_set_is_computed_from_step_2(self):
        """Not vacuous: the set holds the Exclude list and what Step 2 never names."""
        g = self.graduation
        self.assertIn("src/load/", copy_sources(g), "the copy table no longer parses")
        self.assertTrue(is_uncopied("config/bootcamp_preferences.yaml", g))
        self.assertTrue(is_uncopied("data/truth/scenario_truth.json", g),
                        "a path Step 2 neither copies nor excludes is uncopied too")
        self.assertFalse(is_uncopied("config/data_sources.yaml", g))
        self.assertFalse(is_uncopied("data/senzing-ready/customers.jsonl", g))
        self.assertFalse(is_uncopied("src/load", g))
        self.assertFalse(is_uncopied("../graduation/SKILL.md", g), "not a project path")

    def test_no_module_6_or_7_file_directs_an_uncopied_read(self):
        found = []
        for path in generation_instructions():
            for p, sentence in directives(path.read_text(encoding="utf-8"), self.graduation):
                found.append("%s: `%s` in: %s" % (path.name, p, sentence))
        self.assertEqual(
            [], found,
            "a program-generation instruction directs a runtime read of a path graduation "
            "Step 2 does not copy, so the handed-over program finds nothing there; see "
            "phaseA-build-loading.md#%s:\n  " % ANCHOR + "\n  ".join(found))

    def test_the_scan_reads_every_module_6_and_7_file(self):
        names = {p.parent.name for p in generation_instructions()}
        self.assertEqual({MODULE6.name, MODULE7.name}, names)
        self.assertGreaterEqual(len(generation_instructions()), 9)

    def test_negative_controls(self):
        """The #755 reads, written as instructions, each turn the guard red."""
        g = self.graduation
        for text, path in (
                ("The loader reads `database_type` from `config/bootcamp_preferences.yaml` to "
                 "pick its worker count.", "config/bootcamp_preferences.yaml"),
                ("Have each query program read\n`data/truth/scenario_truth.json` and score "
                 "its answers.", "data/truth/scenario_truth.json"),
                ("Save it so that it opens `config/bootcamp_progress.json` when it runs.",
                 "config/bootcamp_progress.json"),
                ("The exporter loads `data/samples/` at runtime.", "data/samples/")):
            with self.subTest(text=text):
                for target in (PHASE_A, QUERY_STEP):
                    shipped = target.read_text(encoding="utf-8")
                    self.assertEqual([], directives(shipped, g))
                    mutated = shipped + "\n\n" + text + "\n"
                    self.assertIn(path, [p for p, _ in directives(mutated, g)], target.name)

    def test_what_is_not_a_directive(self):
        g = self.graduation
        for text in (
                "Read `database_type` from `config/bootcamp_preferences.yaml` here.",
                "No program reads `config/bootcamp_progress.json` at runtime.",
                "The loader reads `data/senzing-ready/` input.",
                "The loader reads its registry `file_path` under `data/subsets/`."):
            with self.subTest(text=text):
                self.assertEqual([], directives(text, g))


class GraduationStep2StatesTheScan(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graduation = GRADUATION.read_text(encoding="utf-8")
        cls.scan = scan_paragraphs(cls.graduation)

    def test_the_scan_is_in_step_2_after_the_exclude_list(self):
        section = step2(self.graduation)
        self.assertLess(section.index(EXCLUDE), section.index(SCAN_LEAD))

    def test_it_runs_the_bundled_script_through_the_plugin_root(self):
        self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scan_uncopied_paths.py"', self.scan)
        self.assertIn("or, if CLAUDE_PLUGIN_ROOT is unset: python3 "
                      "<this-skill-dir>/../../scripts/scan_uncopied_paths.py", self.scan)
        script = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "scan_uncopied_paths.py"
        self.assertTrue(script.is_file())

    def test_each_hit_becomes_a_checklist_item_naming_file_and_path(self):
        self.assertIn("**Each line becomes one `- [ ]` item in the Data section of Step 4's "
                      "`production/MIGRATION_CHECKLIST.md`**, naming the file and the path it "
                      "reads", self.scan)

    def test_no_hit_adds_no_item(self):
        self.assertIn("No line, no item.", self.scan)

    def test_the_search_is_language_agnostic_and_says_what_it_cannot_tell(self):
        self.assertIn("searches the text of every file under `production/src/`, in any language",
                      self.scan)
        self.assertIn("A text search cannot tell a read from a write or a comment", self.scan)

    def test_step_4_points_at_the_scan(self):
        start = self.graduation.index("## Step 4: Production README and migration checklist")
        end = self.graduation.index("## Step 5: Graduation report", start)
        self.assertIn("**The Data section carries Step 2's scan items**, one per line "
                      "[the scan](#scan-the-copied-code) printed.", self.graduation[start:end])
        self.assertIn('<a id="scan-the-copied-code"></a>', step2(self.graduation))

    def test_negative_control_the_scan_removed(self):
        start = self.graduation.index(SCAN_LEAD)
        end = self.graduation.index("Present a short, one-line statement", start)
        without = self.graduation[:start] + self.graduation[end:]
        with self.assertRaises(ValueError):
            scan_paragraphs(without)


if __name__ == "__main__":
    unittest.main()
