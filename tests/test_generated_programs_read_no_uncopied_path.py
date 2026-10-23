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
   from `SQL.CONNECTION`'s scheme. Module 7's query step and Module 5's transform step point at
   it, and Module 5's transform takes its input and output as run arguments (#793).
2. **The guard over the program-generation instructions.** No program-generation instruction
   directs a generated program to read an uncopied path. Which files those are is derived from
   Step 2 too (#793, INV-246), never listed: each `src/**` copy row gives a directory, such as
   `src/transform`, and every file of every skill that names one of them as a program's home (a
   backticked `src/transform` or `src/transform/`, not a file under it) is scanned. That brings in
   Module 5's transform, Modules 6 and 7, and the producer of any `src/**` row added later. The
   uncopied set is computed from Step 2 (INV-246): a project path that no Source cell of its copy
   table covers, which takes in its **Exclude** list and anything it neither copies nor excludes. A directive is a sentence in
   which a program, loader, orchestrator, exporter, script or code reads, loads, opens or parses
   a backticked path, or reads one "at runtime" / "when it runs". A sentence tied to the
   registry (`config/data_sources.yaml`, `file_path`, "registry") is the rule's own exception, and
   a negated one ("no program reads …") is a prohibition, not a directive.
3. **Graduation Step 2 names each mapped source's raw transform input** (#793, INV-187): the
   transform takes it as a run argument from the excluded `data/raw/`, so the Step 5 report's
   files-excluded table and `production/README.md` → Configuration say the reader supplies it.
   A fast-pathed source keeps its own paragraph and gets no second line; a `skipped` one gets none.
   The paragraph carries the `#mapped-source-raw-input` anchor, and Step 4, which writes the
   README, has a Configuration bullet naming each transform's raw input that links to it.
4. **Graduation Step 2 states the scan**: it runs the bundled `scan_uncopied_paths.py`, and each
   line it prints becomes a migration-checklist item naming the file and the path. The script's
   behavior is tested in `tests/test_scan_uncopied_paths.py`.

⚠️ **What the guard cannot see:** a directive worded without one of those verbs or subjects, a
path written without backticks, and a read the guide improvises with no instruction behind it.
The last is the case #755 found; graduation's scan is the net for it.

INV-401 (no generated program reads at runtime a path graduation leaves behind, and graduation
Step 2 scans for one) names this file as an enforcer: it establishes that the skill files state the
rule, point at it and direct no such read, and that Step 2 states the scan. It does not establish
that a live guide never improvises such a read, which only `dry-run` phase 3 observes; the scan is
the net for that, and `tests/test_scan_uncopied_paths.py` tests the scanner itself.

Stdlib-only and no `plugins/` import (INV-108): the files are read as text.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks
from test_module6_data_dirs_are_copied_or_excluded import EXCLUDE, excluded, step2

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE5 = SKILLS / "module-05-data-quality-mapping"
MODULE6 = SKILLS / "module-06-data-processing"
MODULE7 = SKILLS / "module-07-query-visualize-discover"
PHASE_A = MODULE6 / "phaseA-build-loading.md"
QUERY_STEP = MODULE7 / "phase1-query-visualize.md"
TRANSFORM_STEP = MODULE5 / "phase2-data-mapping.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

ANCHOR = "no-runtime-reads-of-uncopied-paths"
RULE_LEAD = ("⛔ **(INV-401) The worker count is fixed in the generated code, and no generated program "
             "reads at runtime a path graduation leaves behind.**")
SCAN_LEAD = "**(INV-401) Scan the copied code for paths this step left behind.**"
FAST_PATH_LEAD = "⛔ **`data/raw/` is excluded, so a CORD fast-pathed source's input is not carried over.**"
RAW_INPUT_LEAD = "**A mapped source's raw input is not carried over either.**"
#: What the raw-input paragraph must say (#793, INV-187).
RAW_INPUT_PHRASES = (
    "takes the file it transforms as a run argument",
    "`../module-05-data-quality-mapping/phase2-data-mapping.md` step 13",
    "the source's file in the excluded `data/raw/`",
    "`docs/mapping/transformation_lineage_[name].md`",
    "Step 5 graduation report's **files-excluded** table",
    "`production/README.md` → Configuration",
    "the reader supplies that input as the transform's argument (INV-187)",
    "A source Module 5 fast-pathed has no transform, so the paragraph above is its only disclosure",
    "a `skipped` source has no transform either, and gets no line",
)
#: The anchor Step 4's README bullet links to, directly before the paragraph's lead.
RAW_INPUT_ANCHOR = '<a id="mapped-source-raw-input"></a>'
STEP4 = "## Step 4: Production README and migration checklist"
#: Step 4's README → Configuration bullet that names each transform's raw input (#793, INV-187).
README_BULLET_LEAD = "- **Configuration names each transform's raw input.** (INV-187)"
README_BULLET_PHRASES = (
    "For each mapped source, name its file in `data/raw/`",
    "as the input the reader supplies as `transform_[name]`'s input argument",
    "Step 2's [mapped-source paragraph](#mapped-source-raw-input) says",
    "No mapped source → omit that sentence.",
)

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


def copied_program_dirs(graduation):
    """Each directory a `src/**` row of Step 2's copy table carries, such as `src/transform`."""
    return sorted({s.rstrip("/") for s in copy_sources(graduation) if s.startswith("src/")})


def names_a_home(text, dirs):
    """True when `text` names one of `dirs` as a program's home: `src/load` or `src/load/`.

    A file under it, such as `src/load/records.jsonl`, is not a home, and graduation's own
    `src/load/**` Source cell and `production/src/load/` destination do not match either.
    """
    return bool(dirs) and re.search(r"`(?:%s)/?`" % "|".join(map(re.escape, dirs)), text) is not None


def skill_texts():
    """Every shipped skill file's text, keyed by its path."""
    return {p: p.read_text(encoding="utf-8")
            for p in corpus_files("plugins/senzing-bootcamp/skills", suffixes={".md"})}


def generation_instructions(graduation, texts=None):
    """Every file of every skill that names a directory Step 2 copies as a program's home (#793).

    Derived from Step 2's `src/**` rows, never a module list (INV-246): a skill whose files save a
    program in `src/transform` is a producer of what graduation copies, so all of its files are
    read, including the ones that name no directory themselves.
    """
    texts = skill_texts() if texts is None else texts
    dirs = copied_program_dirs(graduation)
    producers = {p.parent for p, text in texts.items() if names_a_home(text, dirs)}
    return sorted(p for p in texts if p.parent in producers)


def uncopied_reads(graduation, texts=None):
    """Every directive, in every generation instruction, to read a path Step 2 does not copy."""
    texts = skill_texts() if texts is None else texts
    found = []
    for path in generation_instructions(graduation, texts):
        for p, sentence in directives(texts[path], graduation):
            found.append("%s: `%s` in: %s" % (path.relative_to(SKILLS).as_posix(), p, sentence))
    return found


def rule_paragraph(text):
    start = text.index('<a id="%s"></a>' % ANCHOR)
    end = text.index("\n\n", start)
    return flat(text[start:end])


def raw_input_problems(graduation):
    """Step 2's paragraph naming each mapped source's raw transform input, checked (#793)."""
    section = step2(graduation)
    if RAW_INPUT_LEAD not in section:
        return ["Step 2 has no %r" % RAW_INPUT_LEAD]
    start = section.index(RAW_INPUT_LEAD)
    paragraph = flat(section[start:section.index("\n\n", start)])
    problems = ["the raw-input paragraph does not say %r" % p for p in RAW_INPUT_PHRASES
                if p not in paragraph]
    if FAST_PATH_LEAD not in section or section.index(FAST_PATH_LEAD) > start:
        problems.append("the raw-input paragraph does not follow the fast-pathed one")
    if not section[:start].endswith(RAW_INPUT_ANCHOR + "\n"):
        problems.append("the raw-input paragraph does not carry %r directly before its lead"
                        % RAW_INPUT_ANCHOR)
    return problems


def step4(graduation):
    """Graduation's Step 4, up to the next `## ` heading."""
    start = graduation.index(STEP4)
    end = graduation.find("\n## ", start + len(STEP4))
    return graduation[start:] if end == -1 else graduation[start:end]


def readme_bullet_problems(graduation):
    """Step 4's README → Configuration bullet naming each transform's raw input (#793, INV-187)."""
    section = step4(graduation)
    if README_BULLET_LEAD not in section:
        return ["Step 4 has no %r" % README_BULLET_LEAD]
    start = section.index(README_BULLET_LEAD)
    end = section.find("\n  - ", start + 1)
    bullet = flat(section[start:] if end == -1 else section[start:end])
    problems = ["the README bullet does not say %r" % p for p in README_BULLET_PHRASES
                if p not in bullet]
    if RAW_INPUT_ANCHOR not in step2(graduation):
        problems.append("the README bullet links #mapped-source-raw-input, which Step 2 does "
                        "not define")
    return problems


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
        """The generation instructions carry the lead once, in Phase A, and nowhere else."""
        carriers = [p.name for p in generation_instructions(self.graduation)
                    if RULE_LEAD in flat(p.read_text(encoding="utf-8"))]
        self.assertEqual(["phaseA-build-loading.md"], carriers)

    def test_module_7s_query_step_points_at_it(self):
        text = flat(QUERY_STEP.read_text(encoding="utf-8"))
        start = text.index("## 2. Create query programs")
        end = text.index("⛔ **(INV-152)", start)
        self.assertIn("(../module-06-data-processing/phaseA-build-loading.md#%s)" % ANCHOR,
                      text[start:end])

    def test_module_5s_transform_step_points_at_it(self):
        text = flat(TRANSFORM_STEP.read_text(encoding="utf-8"))
        start = text.index("### 13. Build the transformation program")
        end = text.index("### 14. Test", start)
        self.assertIn("(INV-401; [the rule](../module-06-data-processing/phaseA-build-loading.md#%s))"
                      % ANCHOR, text[start:end])

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

    def test_no_generation_instruction_directs_an_uncopied_read(self):
        found = uncopied_reads(self.graduation)
        self.assertEqual(
            [], found,
            "a program-generation instruction directs a runtime read of a path graduation "
            "Step 2 does not copy, so the handed-over program finds nothing there; see "
            "phaseA-build-loading.md#%s:\n  " % ANCHOR + "\n  ".join(found))

    def test_the_scanned_files_are_derived_from_step_2s_src_rows(self):
        """#793: the directories come from the copy table, and the files from the directories."""
        self.assertEqual(["src/load", "src/query", "src/transform", "src/utils"],
                         copied_program_dirs(self.graduation))
        scanned = generation_instructions(self.graduation)
        # A floor, not the list (INV-265): Module 5's transform step and every Module 6 and
        # Module 7 file, the ones the guard read before it was derived, are among those found.
        self.assertIn(TRANSFORM_STEP, scanned)
        for module in (MODULE6, MODULE7):
            with self.subTest(module=module.name):
                self.assertTrue(set(module.glob("*.md")) <= set(scanned))
        self.assertNotIn(GRADUATION, scanned, "graduation copies the programs; it writes none")

    def test_a_new_src_row_brings_in_its_producer(self):
        """A copy row added to Step 2 scans the skill that saves programs there, unlisted."""
        g = self.graduation
        texts = {SKILLS / "module-08-reports" / "SKILL.md":
                 "Save it as the program `weekly` in `src/reports`.\n\n"
                 "Have the program open `config/bootcamp_progress.json` when it runs.\n"}
        self.assertEqual([], generation_instructions(g, texts))
        row = "| `src/utils/**` | `production/src/utils/` | Shared helpers |"
        self.assertIn(row, g)
        widened = g.replace(row, row + "\n| `src/reports/**` | `production/src/reports/` | Reports |")
        self.assertIn("src/reports", copied_program_dirs(widened))
        self.assertEqual(list(texts), generation_instructions(widened, texts))
        self.assertTrue(any("config/bootcamp_progress.json" in f
                            for f in uncopied_reads(widened, texts)))

    def test_negative_control_a_module_5_program_reads_data_raw(self):
        """#793: the transform told to read its source from `data/raw/` turns the guard red."""
        g = self.graduation
        texts = skill_texts()
        self.assertEqual([], uncopied_reads(g, texts))
        shipped = texts[TRANSFORM_STEP]
        anchor = "**The input and the output are run arguments.**"
        self.assertIn(anchor, shipped)
        for line, path in (
                ("Its code reads `data/raw/[name].csv`, the source's file.", "data/raw/[name].csv"),
                ("Have the program open `data/raw/` when it runs.", "data/raw/")):
            with self.subTest(line=line):
                mutated = dict(texts)
                mutated[TRANSFORM_STEP] = shipped.replace(anchor, line + "\n\n" + anchor, 1)
                self.assertTrue(any("phase2-data-mapping.md: `%s`" % path in f
                                    for f in uncopied_reads(g, mutated)),
                                uncopied_reads(g, mutated))

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
                for target in (PHASE_A, QUERY_STEP, TRANSFORM_STEP):
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


class GraduationNamesTheTransformsRawInput(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graduation = GRADUATION.read_text(encoding="utf-8")

    def test_step_2_names_it_for_the_report_and_the_readme(self):
        self.assertEqual([], raw_input_problems(self.graduation))

    def test_negative_controls(self):
        g = self.graduation
        for old, new, expect in (
                ("`production/README.md` → Configuration, saying\nthat the reader",
                 "the README, saying\nthat the reader", "`production/README.md` → Configuration"),
                ("a run argument", "a fixed path", "as a run argument"),
                ("no transform either, and gets no line", "a line too", "gets no line"),
                (RAW_INPUT_LEAD, "**Raw input.**", "Step 2 has no"),
                (RAW_INPUT_ANCHOR + "\n", "", "directly before its lead")):
            with self.subTest(old=old):
                self.assertIn(old, g)
                problems = raw_input_problems(g.replace(old, new, 1))
                self.assertTrue(any(expect in p for p in problems), problems)

    def test_step_4s_readme_configuration_names_it(self):
        """Step 4 writes the README, so its Configuration list names the input too (#793)."""
        self.assertEqual([], readme_bullet_problems(self.graduation))

    def test_readme_bullet_negative_controls(self):
        g = self.graduation
        lead = README_BULLET_LEAD
        start = g.index(lead)
        bullet = g[start:g.index("\n  - ", start)] + "\n"
        self.assertIn(bullet, g)
        self.assertEqual(["Step 4 has no %r" % lead], readme_bullet_problems(g.replace(bullet, "", 1)))
        for old, new, expect in (
                ("(#mapped-source-raw-input)", "(#scan-the-copied-code)", "mapped-source paragraph"),
                ("`transform_[name]`'s input argument", "the transform's input",
                 "input argument"),
                ("No mapped source → omit that\n    sentence.", "", "omit that sentence")):
            with self.subTest(old=old):
                self.assertIn(old, bullet)
                mutated = g.replace(bullet, bullet.replace(old, new, 1), 1)
                problems = readme_bullet_problems(mutated)
                self.assertTrue(any(expect in p for p in problems), problems)
        unanchored = g.replace(RAW_INPUT_ANCHOR + "\n", "", 1)
        self.assertTrue(any("does not define" in p for p in readme_bullet_problems(unanchored)))


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
