"""The ground rules hold the one statement of how a Bootcamper program is created, built and run.

#511 wrote that statement as Module 3 Phase 1 Step 5's build-and-run table, keyed on `<name>` and
fixed to `src/system_verification`. #562 moved it to `ground-rules.md` → "Building and running a
program", generic over the program's directory `<dir>` as well, so every later module that builds
a program can cite it (#563) instead of writing a second table.

⛔ **The section is the one statement (INV-300).** This guard checks the section, and checks that
Module 3 cites it and keeps no copy:

* the section sits directly after "File placement" and cites INV-300;
* it gives each of Python, Java, C#, Rust and TypeScript the program's files, a build command and a
  run command, written over `<dir>` and `<name>` with no directory of its own;
* it states the 120-second build timeout, the run-from-the-project-root rule and the missing-tool
  Fix_Instruction;
* C#, Rust and TypeScript programs each get their own folder and manifest, made by the toolchain's
  init command, with the Senzing dependency taken from the server's `dependency_note` (Rust,
  TypeScript) or Module 2's package-source route (C#), and never from a public NuGet feed (INV-080,
  INV-222, INV-283);
* TypeScript's build emits the JavaScript its run executes, Java's run goes through Module 2's
  launch route, and Rust programs in one `<dir>` share one target directory;
* the commands have no shell-specific syntax, so they run unchanged in a POSIX shell and in
  PowerShell (INV-002);
* **with `<dir>` = `src/system_verification`, every command is the one Module 3 ran before the
  move.** The expected commands are read from Module 3's text at `MODULE3_BEFORE_THE_MOVE` with
  `git show`, never copied into this file, so there is one record of them (the commit) and not
  two;
* Module 3 Step 5 cites the section by file and section name, with `<dir>` named; Steps 3, 4, 5a,
  6, 7, 7a and 8 cite it directly and name their program; no step says "Step 5's table" or "as
  Step 5 says"; Module 3 restates no command of the statement's shape; and no shipped file other
  than the ground rules restates one of Module 3's commands or the build timeout. Since #595 only
  the section itself is exempt: the rest of `ground-rules.md` is held to the same scan, which keeps
  out the in-container syntax-check list it used to carry.

#563 moved every other program onto the statement, and #594 made the guard find those sites rather
than list them (INV-246):

* **the sites are derived from the statement.** The scan reads the `<dir>` list from the section's
  own bullet, then takes every step of every shipped skill file (a heading's text, outside code
  fences) with a paragraph naming one of those directories beside a verb that saves, builds or
  runs. In Modules 3, 3b, 5, 6 and 7 it also takes every step carrying a marker of the SDK code a
  step writes (`generate_scaffold(`, `sdk_guide(topic=`, `reporting_guide(`, "generated SDK
  code"), though it names no directory. `EXEMPT` names the steps it finds that write no program,
  each with its reason, and an exemption whose step is gone fails;
* every site names each program as "the program `<name>` in `<dir>`", in every `<dir>` it names,
  and cites the section by file and section name;
* **every program is created before it is built or run:** walked in the order a Bootcamper meets
  the files (`WALK`, which every file with a site must be in), a site that builds or runs a program
  must come at or after a site that saves it at the path the section gives, including
  `register_data_sources` and `er_stats` from Module 5;
* no shipped file restates a build or run command in any directory, in a code span or on a line
  of a fenced block, including `node` on a `.js`, `python3` on a `.py` and `mvn` (the plugin's own
  scripts, and Module 2's own C# package-source and Java jar routes, which the statement cites,
  excepted), and none names a loose program file such as `src/load/orchestrator.[ext]`, which C#,
  Rust and TypeScript cannot build;
* the two undefined references ("the same per-language build command as the loader", "the run
  command for the chosen language") are gone; Module 5 builds one program per source, the
  transform; Module 7 step 2 says each C#, Rust or TypeScript program carries its own engine setup;
* graduation's root-manifest row says only Python's `requirements.txt` sits at the root, its
  `src/**` copy leaves out the build output the section's commands write, its production
  `.gitignore` lists each of those folders, and `production/README.md`'s Usage gives each program's
  commands from the section;
* the held `module3-build-and-run-table` block is still held, and the widened drafted wording
  #563 proposes for it covers every module that builds programs and names the section. That
  wording sits in #563's own ledger entry, as its "Correction to the #511 entry": a run writes
  nothing under `specs/` but its own entry (INV-307), so the #511 block is left as it was.

#793 put Data collection's programs on the statement and said how a run passes arguments (INV-370's
dated note of 2026-10-23, applied 2026-10-26):

* the section states once, in its own "Every language" bullet, that a program's arguments follow
  its Run command, after a `--` for `cargo run` and `dotnet run`, and that on native Windows and
  on the `docker` route the Run command and its arguments together are the `<command>` the call
  carries;
* `src/collect` is on the `<dir>` list, so the scan finds Data collection's converters
  (`convert_[name]`) and paginated-API collection program (`collect_[name]`), which its step saves
  at the section's path and builds and runs by citing it; its file has its place in `WALK`, after
  Truth Set visualization and before Module 5;
* Module 5's `transform_[name]` takes its input and output as run arguments (step 13), and steps
  14, 15 and 18 each name the input and the output they pass, the input in `data/samples/` or
  `data/raw/` and never the registry's `file_path`; Module 4 and Module 5 point at the section for
  how, and neither restates the `--`.

Each check is a function returning its problems, and a negative control mutates the real text and
sees the check report it: a drifted command, a command restated in Module 3 or at a #563 site
(in a fenced block too, and `node` on a `.js`, `python3` on a `.py` or `mvn`), a missing citation
or program name at a found site, a new step that saves a program or writes SDK code with neither,
a `<dir>` the statement adds, a stale exemption, a file with no place in the walk, a program built
before any step creates it, a loose program path (with a placeholder extension, or a placeholder
alone, such as `src/query/<file>`), and the retired phrases come back. A positive control shows a
run of the plugin's own script is not reported.

⚠️ It pins the text. It cannot observe a real `dotnet`, `cargo`, `tsc` or `javac` build of a
Bootcamper's program. The comparison with the earlier Module 3 needs the full git history, which
the suite's CI checkout fetches (`fetch-depth: 0`); in a shallow clone it fails rather than
skipping, because a skipped comparison would certify nothing.

This module enforces INV-370 (registered 2026-10-13). It pins the text; it cannot establish that
a real `dotnet`, `cargo`, `tsc` or `javac` build succeeds on a Bootcamper's machine.

Source issues: #511, #562, #563, #594, #793.

Run:  python3 -m unittest discover -s tests
"""
import re
import subprocess
import unittest
from collections import namedtuple
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
PHASE1 = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"

#: `origin/main` when #562 began: the last commit whose Module 3 Step 5 held the table itself.
MODULE3_BEFORE_THE_MOVE = "db3dac7f61aba4cb267cd04b973f332f78866f6e"
MODULE3_DIR = "src/system_verification"

SECTION = "## Building and running a program"
PREVIOUS_SECTION = "## File placement"
#: How a step cites the section: by file and by section name.
CITATION = '`../bootcamp-onboarding/ground-rules.md` → "Building and running a program"'
CREATING = "**Creating a C#, Rust or TypeScript program's project.**"

LANGUAGES = ("Python", "Java", "C#", "Rust", "TypeScript")
PROJECT_LANGUAGES = ("C#", "Rust", "TypeScript")
#: Each program and the step that creates it, as Step 5's program table states them.
PROGRAMS = {
    "verify_init": "Step 3",
    "verify_pipeline": "Step 4",
    "register_data_sources": "Step 5a",
    "validate_results": "Step 7",
    "mari_lookup": "Step 7a",
    "database_operations": "Step 8",
}
#: Steps that save, build or run a program, and the program each one names.
CITING_STEPS = {
    "### Step 3:": "verify_init",
    "### Step 4:": "verify_pipeline",
    "### Step 5a:": "register_data_sources",
    "### Step 6:": "verify_pipeline",
    "### Step 7:": "validate_results",
    "### Step 7a:": "mari_lookup",
    "### Step 8:": "database_operations",
}
RETIRED_PHRASES = ("Step 5's table", "as Step 5 says")
#: A build or run command, in any directory: the shapes the statement's commands take, and the
#: other ways to build or run a program file (#594): `node` on any `.js`, `python3` on any `.py`,
#: and `mvn`. `COMMAND_SHAPE` reads an inline code span; `FENCED_COMMAND` a line of a fenced block.
_COMMANDS = (r"(?:python3? -m py_compile|python3? src/|python3? \S+\.py\b|javac "
             r"|dotnet (?:build|run|new|add)|cargo (?:build|run|init)|tsc |npm init"
             r"|node \S+\.js\b|mvn )")
COMMAND_SHAPE = re.compile(r"`" + _COMMANDS)
FENCED_COMMAND = re.compile(r"(?m)^[ \t]*" + _COMMANDS)
#: A run of one of the plugin's own scripts, which the plugin ships and runs for the guide: not a
#: Bootcamper program, so not a command of the statement's shape.
PLUGIN_SCRIPT_RUN = re.compile(
    r'python3? (?:\\?"\$\{CLAUDE_PLUGIN_ROOT\}/scripts/|<this-skill-dir>/\.\./\.\./scripts/)')
#: The build timeout said again outside the section.
BUILD_TIMEOUT_RESTATED = re.compile(
    r"120-second build|120-second timeout for all build|Step 5's 120-second"
)
MISSING_TOOLS = ("`dotnet`", "`cargo`", "`tsc`", "`node`", "`javac`")

SKILLS = PLUGIN / "skills"
M2 = "module-02-sdk-setup/SKILL.md"
M4 = "module-04-data-collection/SKILL.md"
M5_MAPPING = "module-05-data-quality-mapping/phase2-data-mapping.md"
M5_TEST_LOAD = "module-05-data-quality-mapping/phase3-test-load.md"
M6_A = "module-06-data-processing/phaseA-build-loading.md"
M6_B = "module-06-data-processing/phaseB-load-first-source.md"
M6_C = "module-06-data-processing/phaseC-multi-source.md"
M7_QUERY = "module-07-query-visualize-discover/phase1-query-visualize.md"
M7_DISCOVER = "module-07-query-visualize-discover/phase2b-discover.md"
GROUND_RULES_REL = "bootcamp-onboarding/ground-rules.md"
GRADUATION_REL = "graduation/SKILL.md"
#: How the ground rules' own "Showing one resolved entity as text" cites the section in its file.
CITATION_HERE = '"Building and running a program" below'
#: The statement's own bullet that lists every `<dir>`. The scan reads its directories from here.
DIR_BULLET = "- **`<dir>`** is the program's directory"
#: Where a step mentions a `<dir>` it saves, builds or runs a program in, such as `src/load` or
#: `src/load/`; a file under one, such as `src/load/records.jsonl`, is data, not a program.
DIR_MENTION = r"`(%s)/?`"
#: A paragraph that names a `<dir>` and one of these verbs saves, builds or runs a program there.
PROGRAM_VERB = re.compile(
    r"(?i)\b(?:sav(?:e|es|ed|ing)|generat(?:e|es|ed|ing)|writ(?:e|es|ten|ing)"
    r"|build(?:s|ing)?|built|run(?:s|ning)?)\b")
#: The modules #594 scans for the markers of SDK code a step writes, though it names no `<dir>`.
MARKER_MODULES = ("module-03-system-verification/", "module-03b-truthset-visualization/",
                  "module-05-data-quality-mapping/", "module-06-data-processing/",
                  "module-07-query-visualize-discover/")
CODE_MARKERS = re.compile(
    r"generate_scaffold\(|sdk_guide\(topic=|reporting_guide\(|generated SDK code")
#: Steps the scan finds that write no program of their own, each with the reason (#594). A step
#: here is still read by every other check; only the program-site check skips it.
EXEMPT = {
    (GROUND_RULES_REL, "## Building and running a program"):
        "the statement itself: it defines `<dir>` and `<name>` for the steps that cite it",
    ("module-03-system-verification/phase1-verification.md", "## Agent Rules"):
        "rules on where Module 3's artifacts live and what a re-run overwrites; Steps 3 to 8 save "
        "the programs",
    ("module-03-system-verification/phase1-verification.md",
     "### Step 1a: Engine Initialization Check"):
        "re-runs Module 2 Step 9's engine check from the code Module 2 already generated; it "
        "saves no program in a `<dir>`",
    ("module-03-system-verification/phase1-verification.md", "### Step 5: Build/Compile"):
        "builds every Module 3 program over its program table, citing the section with `<dir>` "
        "named; `ModuleThreeCitesTheSectionAndKeepsNoCopy` pins it",
    ("module-03b-truthset-visualization/visualization-api-reference.md", "## API Endpoints"):
        "the server's response contract, which cites `reporting_guide` for one export's shape; "
        "the program is `truthset_server`, saved at Step 2",
    ("module-06-data-processing/SKILL.md",
     "## Loading code and safety (applies to every load step)"):
        "a rule for every load step on where code and counts come from; the phases save the "
        "programs",
    ("module-06-data-processing/phaseA-build-loading.md", "## 1. Assess production record volume"):
        "picks the loading pattern that step 3's `load_[name]` is built from",
    ("module-06-data-processing/phaseA-build-loading.md",
     "## 4. Use MCP tools for code generation"):
        "names the MCP calls for step 3's `load_[name]`; it saves no program of its own",
    ("module-06-data-processing/phaseD-validation.md",
     "# Module 6, Phase D: Validation (steps 21–28)"):
        "the file's header note on which `reporting_guide` topics the phase uses",
    ("module-07-query-visualize-discover/phase1-query-visualize.md",
     "# Module 7, Phase 1: Query and Visualize (steps 1–3c)"):
        "the file's header note that every entity query is generated SDK code",
    ("module-07-query-visualize-discover/phase1-query-visualize.md", "### 3b. Quality evaluation"):
        "reads two `reporting_guide` topics for method and interpretation; the figures it judges "
        "come from step 3's query programs",
    ("module-07-query-visualize-discover/phase1-query-visualize.md",
     "## Data-discoveries deliverable (produced on every path)"):
        "says where the document's figures come from; the programs that produce them are saved "
        "at earlier steps",
    ("module-07-query-visualize-discover/phase2-discover.md",
     "# Module 7, Phase 2a: Discover, Part A (steps 4a–4c)"):
        "the file's header note on which routes give the SDK methods",
    ("module-07-query-visualize-discover/phase2b-discover.md",
     "# Module 7, Phase 2b: Discover, Part B (steps 4d–4e)"):
        "the file's header note on which routes give the SDK methods",
}
#: The order a Bootcamper first follows each file with program sites, so a program is built only
#: after the step that creates it. The ground rules' entity section is first followed at Module 6
#: step 9, so it sits there. Module 2's `register-sources` detour sits after Module 6 step 4a;
#: offered from Data collection, before Module 5, it finds no program and has items 2 and 3 create
#: it, which `test_module_2_creates_it_when_it_is_missing` pins. A file with a program site and no
#: place here fails the walk, so a new file cannot be skipped.
WALK = (
    "module-03-system-verification/phase1-verification.md",
    "module-03-system-verification/phase2-report-close.md",
    "module-03b-truthset-visualization/phase1-visualization.md",
    "module-03b-truthset-visualization/phase2-close.md",
    M4,
    "module-05-data-quality-mapping/phase1-quality-assessment.md",
    M5_MAPPING, M5_TEST_LOAD, M6_A, M2, M6_B, GROUND_RULES_REL, M6_C,
    "module-06-data-processing/phaseD-validation.md",
    M7_QUERY,
    "module-07-query-visualize-discover/phase2-discover.md",
    M7_DISCOVER,
)
#: The undefined references #563 replaced, and the loose save path it retired.
RETIRED_563 = ("same per-language build command", "the run command for the chosen language",
               "Save to `src/")
#: A program file named with a placeholder extension, or a path whose last part is a placeholder
#: alone, such as `src/query/<file>` (#594): a loose file, which the C#, Rust and TypeScript rows of
#: the statement cannot build, since each of them builds a folder. `<name>` is the statement's own
#: placeholder for that folder, so it is not a loose file.
LOOSE_PROGRAM_PATH = re.compile(
    r"src/[\w/\[\]<>{}-]*\.(?:\[ext\]|<ext>|\{ext\})"
    r"|src/[\w/\[\]<>{}-]*/(?!<name>)(?:<[^<>/`\"]+>|\[[^\]/`\"]+\]|\{[^}/`\"]+\})(?![\w/.<\[{])")
#: Commands a file states as its own route, which the statement cites rather than holds: Module
#: 2's C# package-source route, `../module-02-sdk-setup/SKILL.md` → Phase 3, the C# bullet, and
#: the command its Java route says `java -jar sz-sdk.jar` prints, which installs the SDK jar and
#: builds no Bootcamper program. `dotnet new nugetconfig` is the same C# route's project-local
#: package-source file (#618, INV-199), which builds no program either.
ROUTE_COMMANDS = {M2: ("`dotnet add package Senzing.Sdk --source SenzingLocal`",
                       "`dotnet new nugetconfig`",
                       "`mvn install:install-file`")}
#: #793: the section's one statement of how a run passes a program's arguments.
ARGUMENTS_BULLET = "- **A program's arguments follow its Run command**"
#: The Run commands that need a `--` before the program's arguments, so the tool passes them on.
DASH_DASH_RUNS = ("cargo run", "dotnet run")
#: How Module 4 and Module 5 point at it, rather than restating it.
ARGUMENTS_POINTER = "as that section says"
#: Module 5's transform: each run step, and the input and output arguments it names (#793).
TRANSFORM_RUNS = {
    "### 14. ": ("the source's sample file under `data/samples/`",
                 "`data/mapping/{source}_sample.jsonl`"),
    "### 15. ": ("the source's file in `data/raw/`", "`data/mapping/{source}_quality.jsonl`"),
    "### 18. ": ("the source's file in `data/raw/`", "`data/senzing-ready/[name].jsonl`"),
}
#: Module 4's programs, saved in `src/collect` (#793).
COLLECT_PROGRAMS = {("convert_[name]", "src/collect"), ("collect_[name]", "src/collect")}
IMPLEMENTED = REPO_ROOT / "specs" / "IMPLEMENTED.md"
HELD_BLOCK = "## module3-build-and-run-table"
#: #563's own ledger entry, and the correction in it that drafts the held block's widened wording.
WIDENING_ENTRY = "## build-and-run-statement-in-modules-5-6-7"
WIDENING_CORRECTION = "- **Correction to the #511 entry (dated 2026-10-13, #563):**"
#: The modules the widened drafted wording must cover, by the names the plugin uses.
MODULES_THAT_BUILD = ("System verification", "Data Quality, Mapping, and Transformation",
                      "Data processing", "Query, Visualize and Discover", "SDK setup",
                      "graduation")
#: What the statement's build and init commands write under a `<dir>`: Java's `classes`, Rust's
#: shared `target`, TypeScript's `dist` and `node_modules`, and C#'s `bin` and `obj`. Graduation's
#: copy leaves each out, and its production `.gitignore` lists each (#594).
BUILD_OUTPUT = ("classes/", "target/", "dist/", "node_modules/", "bin/", "obj/")
#: Where the statement's commands write the first three, so the list above follows the statement.
BUILD_OUTPUT_IN_THE_STATEMENT = ("-d <dir>/classes", "--target-dir <dir>/target",
                                 "--outDir <dir>/<name>/dist")
NO_BUILD_OUTPUT = "**The `src/**` rows copy source, never build output.**"
GITIGNORE_BULLET = "- **`.gitignore`:**"
STATEMENT_PATH = ('`plugins/senzing-bootcamp/skills/bootcamp-onboarding/ground-rules.md` → '
                  '"Building and running a program"')


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def block(text, heading, stop):
    """The text after `heading` up to the next line matching `stop`, or "" without the heading.

    Empty when the heading is missing, which the callers assert against, so a renamed heading
    fails loudly instead of passing vacuously (INV-265).
    """
    i = text.find(heading)
    if i < 0:
        return ""
    rest = text[i + len(heading):]
    m = re.search(stop, rest)
    return rest if m is None else rest[:m.start()]


def section(text):
    return block(text, SECTION, r"\n## ")


def outside_the_section(text):
    """The ground rules with "Building and running a program" cut out (#595).

    The section is the one statement, so only it may hold the commands; the rest of the file is
    held to the restatement guard like every other shipped file. Unchanged when the heading is
    missing, so a renamed section exempts nothing rather than everything (INV-265).
    """
    body = section(text)
    return text.replace(SECTION + body, "", 1) if body else text


def step(text, heading):
    return block(text, heading, r"\n#{2,3} ")


def table_rows(text):
    """Build-and-run rows, keyed by language: (files, build, run)."""
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] in LANGUAGES:
            rows[cells[0]] = tuple(cells[1:])
    return rows


def project_items(text):
    """The C#, Rust and TypeScript items of a project-creation list, keyed by language."""
    found = re.finditer(r"(?ms)^\d\. \*\*(C#|Rust|TypeScript):\*\*(.*?)(?=^\d\. |\Z)", text)
    return {m.group(1): m.group(2) for m in found}


def spans(text):
    return re.findall(r"`([^`]+)`", text)


def at(cell, directory):
    return cell.replace("<dir>", directory)


def module3_before_the_move():
    """Module 3 Phase 1's text at `MODULE3_BEFORE_THE_MOVE`, read from git."""
    rel = PHASE1.relative_to(REPO_ROOT).as_posix()
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", "%s:%s" % (MODULE3_BEFORE_THE_MOVE, rel)],
        capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise AssertionError(
            "cannot read %s at %s (%s). The comparison needs the full history, as CI's "
            "fetch-depth: 0 checkout has." % (rel, MODULE3_BEFORE_THE_MOVE, proc.stderr.strip()))
    return proc.stdout


def commands_that_drifted(ground_rules, before):
    """Every command whose `<dir>` = `src/system_verification` form differs from Module 3's."""
    problems = []
    statement = section(ground_rules)
    old_step5 = step(before, "### Step 5:")
    new_rows, old_rows = table_rows(statement), table_rows(old_step5)
    if len(old_rows) != len(LANGUAGES):
        problems.append("the earlier Module 3 has %d table rows, not 5" % len(old_rows))
    for lang in LANGUAGES:
        if lang not in new_rows:
            problems.append("the section has no %s row" % lang)
            continue
        for label, new, old in zip(("files", "build", "run"), new_rows[lang],
                                   old_rows.get(lang, ("",) * 3)):
            if at(new, MODULE3_DIR) != old:
                problems.append("%s %s: %r is not Module 3's %r" % (lang, label, new, old))
    new_items = project_items(statement[statement.find(CREATING):])
    old_items = project_items(old_step5[old_step5.find(CREATING):])
    for lang in PROJECT_LANGUAGES:
        new = [at(s, MODULE3_DIR) for s in spans(new_items.get(lang, ""))]
        old = spans(old_items.get(lang, ""))
        if not old:
            problems.append("the earlier Module 3 has no %s project item" % lang)
        if new != old:
            problems.append("%s project creation: %r is not Module 3's %r" % (lang, new, old))
    return problems


def restatements(path, text, ground_rules, any_directory=True):
    """Commands, or the build timeout, that a file outside the section says again.

    Every file is held to Module 3's own commands and the build timeout. `any_directory` also
    reports a command of the statement's shape in any directory. Since #563 every shipped file is
    held to that, except the route commands `ROUTE_COMMANDS` names in their own file.
    """
    problems = []
    statement = section(ground_rules)
    commands = [at(c, MODULE3_DIR) for row in table_rows(statement).values()
                for cell in row[1:] for c in spans(cell)]
    for item in project_items(statement).values():
        commands += [at(c, MODULE3_DIR) for c in spans(item) if " " in c]
    for rel, allowed in ROUTE_COMMANDS.items():
        if path.endswith(rel):
            for command in allowed:
                text = text.replace(command, "")
    flat = squash(text)
    for command in commands:
        if "`%s`" % command in flat:
            problems.append("%s restates `%s`" % (path, command))
    for shape, skip in ((COMMAND_SHAPE, 1), (FENCED_COMMAND, 0)):
        for m in shape.finditer(text if any_directory else ""):
            command = text[m.start() + skip:].lstrip(" \t")
            if not PLUGIN_SCRIPT_RUN.match(command):
                problems.append("%s restates a command: %s" % (path, text[m.start():m.start() + 40]
                                                                .strip()))
    for m in BUILD_TIMEOUT_RESTATED.finditer(flat):
        problems.append("%s restates the build timeout: %s" % (path, m.group(0)))
    return problems


def uncited_steps(text):
    """Steps that do not cite the section directly, or that still cite Step 5 for commands."""
    problems = []
    for heading, name in CITING_STEPS.items():
        body = squash(step(text, heading))
        if not body:
            problems.append("%s is gone" % heading)
            continue
        if CITATION not in body:
            problems.append("%s does not cite %s" % (heading, CITATION))
        if "`%s`" % name not in body:
            problems.append("%s does not name its program `%s`" % (heading, name))
        if MODULE3_DIR not in body:
            problems.append("%s does not name its directory %s" % (heading, MODULE3_DIR))
        for phrase in RETIRED_PHRASES:
            if phrase in body:
                problems.append("%s still says %r" % (heading, phrase))
    return problems


def site_body(text, start):
    """A #563 site's own text: from `start` to its next heading, list item or paragraph break.

    A heading site runs to the next heading of any level, so a sub-step's text is not the
    step's; a numbered item to the next numbered item; a bullet to the next blank line. Empty
    when `start` is missing, which the callers report (INV-265).
    """
    m = re.search(r"(?m)^" + re.escape(start), text)
    if m is None:
        return ""
    if start.startswith("#"):
        stop = r"\n#{1,6} "
    elif re.match(r"\d+\. ", start):
        stop = r"\n\d+\. \*\*"
    else:
        stop = r"\n\s*\n"
    rest = text[m.end():]
    e = re.search(stop, rest)
    return rest if e is None else rest[:e.start()]


def skill_texts():
    """Every shipped skill file's text, keyed by its path under `skills/`."""
    return {path.relative_to(SKILLS).as_posix(): read(path)
            for path in corpus_files("plugins/senzing-bootcamp/skills", suffixes={".md"})}


def statement_dirs(ground_rules):
    """The `<dir>` list, read from the statement's own bullet, so the scan follows the statement.

    Empty when the bullet is missing, which the callers assert against (INV-265).
    """
    bullet = block(section(ground_rules), DIR_BULLET, r"\n- |\n\n")
    return tuple(s for s in spans(squash(bullet)) if s.startswith("src/"))


def steps_of(text):
    """Each heading line and its text, up to the next heading of any level outside a code fence."""
    heads, fenced, offset = [], False, 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,6} ", line):
            heads.append((offset, line.rstrip("\n")))
        offset += len(line)
    for i, (start, heading) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        yield heading, text[start + len(heading):end]


Site = namedtuple("Site", "rel heading body dirs marked")


def program_sites(texts, dirs, exempt=EXEMPT):
    """Every step that saves, builds or runs a program, found by scanning, never listed (INV-246).

    A step is a program site when a paragraph of it names one of the statement's `<dir>`s with a
    verb that saves, builds or runs, or, in Modules 3, 3b, 5, 6 and 7, when it carries a marker of
    the SDK code it writes. Steps in `exempt` are skipped. In walk order within each file.
    """
    mention = re.compile(DIR_MENTION % "|".join(map(re.escape, dirs)))
    sites = []
    for rel in sorted(texts):
        for heading, body in steps_of(texts[rel]):
            if (rel, heading) in exempt:
                continue
            found = set()
            for paragraph in re.split(r"\n\s*\n", body):
                paragraph = squash(paragraph)
                if PROGRAM_VERB.search(paragraph):
                    found |= {m.group(1) for m in mention.finditer(paragraph)}
            flat = squash(body)
            marked = rel.startswith(MARKER_MODULES) and CODE_MARKERS.search(flat) is not None
            if found or marked:
                sites.append(Site(rel, heading, flat, frozenset(found), marked))
    return sites


def named_programs(body, dirs):
    """Every (`<name>`, `<dir>`) a step names, as "the program `<name>` in `<dir>`"."""
    alt = "|".join(map(re.escape, dirs))
    named = {(m.group(1), m.group(2))
             for m in re.finditer(r"program,? `([^`]+)` in `(%s)`" % alt, body)}
    named |= {(m.group(2), m.group(1))
              for m in re.finditer(r"`<dir>` = `(%s)` and `<name>` = `([^`]+)`" % alt, body)}
    return named


def creates_program(body, name, directory):
    """Saved as the program at the path the section gives."""
    return ("as the program `%s` in `%s`" % (name, directory) in body
            and "gives" in body and re.search(r"(?i)\bsav(e|es|ed)\b", body) is not None)


def site_name(site):
    return "%s %s" % (site.rel, site.heading)


def uncited_sites(sites, dirs):
    """Program sites that do not cite the section, or do not name each program and its `<dir>`."""
    problems = []
    for site in sites:
        citation = CITATION_HERE if site.rel == GROUND_RULES_REL else CITATION
        if citation not in site.body:
            problems.append("%s does not cite %s" % (site_name(site), citation))
        named = named_programs(site.body, dirs)
        if not named:
            problems.append("%s names no program `<name>` in a `<dir>`" % site_name(site))
        for directory in sorted(site.dirs - {d for _, d in named}):
            problems.append("%s does not name its program in `%s`" % (site_name(site), directory))
    return problems


def walked(sites):
    """The sites in the order a Bootcamper meets them, and the files `WALK` does not place."""
    order = {rel: i for i, rel in enumerate(WALK)}
    unplaced = sorted({s.rel for s in sites} - set(order))
    return sorted((s for s in sites if s.rel in order), key=lambda s: order[s.rel]), unplaced


def built_before_created(sites, dirs):
    """Sites that build or run a program before any site saves it at the section's path."""
    ordered, unplaced = walked(sites)
    problems = ["%s has a program site and no place in WALK" % rel for rel in unplaced]
    created = set()
    for site in ordered:
        named = named_programs(site.body, dirs)
        created |= {program for program in named if creates_program(site.body, *program)}
        for name, directory in sorted(named - created):
            problems.append("%s builds or runs `%s` in `%s` before any step creates it"
                            % (site_name(site), name, directory))
    return problems


def arguments_bullet(ground_rules):
    """The section's arguments bullet, squashed, or "" when it is missing (INV-265)."""
    return squash(block(section(ground_rules), ARGUMENTS_BULLET, r"\n- |\n\n"))


def argument_problems(ground_rules):
    """The arguments bullet, checked against the table: which Run commands take a `--` first."""
    bullet = arguments_bullet(ground_rules)
    if not bullet:
        return ["the section has no %r" % ARGUMENTS_BULLET]
    problems = []
    for lang, (_files, _build, run) in sorted(table_rows(section(ground_rules)).items()):
        command = (spans(run) or [""])[0]
        needs = command.startswith(DASH_DASH_RUNS)
        named = any(command.startswith(r) and "`%s`" % r in bullet for r in DASH_DASH_RUNS)
        if needs and not named:
            problems.append("%s's Run command `%s` needs a `--` the bullet does not give"
                            % (lang, command))
    if "`cargo run` and `dotnet run` take a `--` first" not in bullet:
        problems.append("the bullet does not say `cargo run` and `dotnet run` take a `--` first")
    if "the Run command, then `--`, then the arguments" not in bullet:
        problems.append("the bullet does not say where the `--` goes")
    if "Every other Run command takes them directly after it" not in bullet:
        problems.append("the bullet does not say the other Run commands take them directly")
    if "after `<ClassName>`" not in bullet:
        problems.append("the bullet does not say where Java's arguments go")
    if "the Run command and its arguments together are the `<command>`" not in bullet:
        problems.append("the bullet does not say how the `docker` route wraps a run with arguments")
    if "On native Windows and on the `docker` route" not in bullet:
        problems.append("the bullet does not say native Windows' call carries the arguments too")
    return problems


def restated_argument_rule(path, text):
    """A paragraph outside the section that says again where a run's `--` goes (INV-300)."""
    problems = []
    for paragraph in re.split(r"\n\s*\n", text):
        flat = squash(paragraph)
        if "`--`" in flat and re.search(r"argument|cargo run|dotnet run", flat):
            problems.append("%s restates the arguments rule: %s" % (path, flat[:80]))
    return problems


def transform_run_problems(text):
    """Module 5's transform: the argument contract at step 13, and each run's input and output."""
    problems = []
    body = squash(site_body(text, "### 13. "))
    for phrase in ("`transform_[name]` takes two, in this order: the file it transforms and the "
                   "file it writes, passed %s a program's arguments are." % ARGUMENTS_POINTER,
                   "Its code fixes no input path"):
        if phrase not in body:
            problems.append("step 13 does not say %r" % phrase)
    for start, (given, written) in TRANSFORM_RUNS.items():
        body = squash(site_body(text, start))
        if "%s as its input argument" % given not in body:
            problems.append("%s does not pass %s as its input" % (start.strip(), given))
        if not any(form % written in body for form in ("%s, its output argument",
                                                         "%s as its output argument")):
            problems.append("%s does not pass %s as its output" % (start.strip(), written))
    return problems


def build_output_problems(graduation):
    """Graduation's copy that carries build output, or a production `.gitignore` that misses it."""
    problems = []
    rule = squash(block(graduation, NO_BUILD_OUTPUT, r"\n\n"))
    if not rule:
        problems.append("graduation has no %r" % NO_BUILD_OUTPUT)
    gitignore = next((line for line in graduation.splitlines()
                      if line.startswith(GITIGNORE_BULLET)), "")
    if not gitignore:
        problems.append("graduation has no production `.gitignore` bullet")
    for folder in BUILD_OUTPUT:
        if rule and "`%s`" % folder not in rule:
            problems.append("graduation's copy does not skip `%s`" % folder)
        if gitignore and "`%s`" % folder not in gitignore:
            problems.append("the production `.gitignore` does not list `%s`" % folder)
    return problems


def stale_exemptions(texts, exempt=EXEMPT):
    """Exempt steps that are gone, or that give no reason."""
    problems = []
    for (rel, heading), reason in exempt.items():
        if heading not in {h for h, _ in steps_of(texts.get(rel, ""))}:
            problems.append("the exempt step %s %s is gone" % (rel, heading))
        if not reason.strip():
            problems.append("the exempt step %s %s gives no reason" % (rel, heading))
    return problems


def retired_references(path, text):
    flat = squash(text)
    problems = ["%s still says %r" % (path, p) for p in RETIRED_563 if p in flat]
    problems += ["%s names a loose program file %s" % (path, m.group(0))
                 for m in LOOSE_PROGRAM_PATH.finditer(text)]
    return problems


def widening_correction(ledger):
    """The text of #563's correction to the #511 entry, or "" when it is missing."""
    entry = block(ledger, WIDENING_ENTRY + "\n", r"\n## ")
    return block(entry, WIDENING_CORRECTION, r"\n- \*\*")


def held_block_problems(ledger):
    """The held block stays held, and the widened wording drafted for it covers every module.

    The wording is read from #563's own entry, not from the block: INV-307 keeps a run out of
    another entry, so the block keeps #511's wording until `/review-invariants` takes this one.
    """
    body = block(ledger, HELD_BLOCK + "\n", r"\n## ")
    if not body:
        return ["specs/IMPLEMENTED.md has no %r" % HELD_BLOCK]
    problems = []
    if "**HELD 2026-10-13:**" not in body:
        problems.append("the block is no longer held")
    correction = widening_correction(ledger)
    if not correction:
        return problems + ["%s has no %r" % (WIDENING_ENTRY, WIDENING_CORRECTION)]
    m = re.search(r"(?m)^  \*\*INV-NNN\*\* — (.*)$", correction)
    if m is None:
        return problems + ["the correction has no drafted wording"]
    wording = m.group(1)
    if STATEMENT_PATH not in wording:
        problems.append("the drafted wording does not name %s" % STATEMENT_PATH)
    for module in MODULES_THAT_BUILD:
        if module not in wording:
            problems.append("the drafted wording does not cover %s" % module)
    if "Phase 1 Step 5's one build-and-run table" in wording:
        problems.append("the drafted wording still names Module 3's table")
    return problems


class TheSectionIsTheOneStatement(unittest.TestCase):
    def setUp(self):
        self.text = read(GROUND_RULES)
        self.statement = squash(section(self.text))
        self.assertTrue(self.statement, "ground-rules.md has no %r" % SECTION)

    def test_it_sits_directly_after_file_placement(self):
        after = block(self.text, PREVIOUS_SECTION, r"\n## ")
        self.assertTrue(after, "ground-rules.md has no %r" % PREVIOUS_SECTION)
        rest = self.text[self.text.find(PREVIOUS_SECTION) + len(PREVIOUS_SECTION) + len(after):]
        self.assertTrue(rest.lstrip("\n").startswith(SECTION),
                        "the section is not the one directly after %r" % PREVIOUS_SECTION)

    def test_it_says_it_is_the_one_statement_and_cites_inv_300(self):
        self.assertIn("This section is the one statement of how a Bootcamper program is "
                      "created, built and run (INV-300).", self.statement.replace("**", ""))

    def test_a_citing_step_names_its_dir_and_name(self):
        self.assertIn("names its `<dir>` and `<name>` and cites this section", self.statement)
        for directory in ("src/system_verification", "src/collect", "src/load", "src/transform",
                          "src/query", "src/server"):
            with self.subTest(directory=directory):
                self.assertIn("`%s`" % directory, self.statement)


class EveryLanguageHasFilesABuildAndARun(unittest.TestCase):
    def setUp(self):
        self.rows = table_rows(section(read(GROUND_RULES)))

    def test_every_language_has_files_a_build_and_a_run_command(self):
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                self.assertIn(lang, self.rows, "the section has no %s row" % lang)
                files, build, run = self.rows[lang]
                for label, cell in (("files", files), ("build", build), ("run", run)):
                    self.assertTrue(cell.startswith("`"), "%s has no %s" % (lang, label))

    def test_every_cell_is_generic_over_dir_and_name(self):
        """No row names a directory of its own: `<dir>` is the citing step's to fill in."""
        for lang, row in self.rows.items():
            for label, cell in zip(("files", "build", "run"), row):
                with self.subTest(language=lang, cell=label):
                    self.assertIn("<dir>", cell)
                    self.assertNotRegex(cell, r"\bsrc/(?!main\.rs)")
            with self.subTest(language=lang, cell="build"):
                self.assertIn("<name>", row[1])

    def test_python_and_java_are_flat_and_the_rest_use_a_folder(self):
        for lang in ("Python", "Java"):
            with self.subTest(language=lang):
                self.assertRegex(self.rows[lang][0], r"^`<dir>/<name>\.\w+`$")
        for lang in PROJECT_LANGUAGES:
            with self.subTest(language=lang):
                self.assertTrue(self.rows[lang][0].startswith("`<dir>/<name>/` holding"))

    def test_typescript_emits_what_it_runs(self):
        _, build, run = self.rows["TypeScript"]
        self.assertNotIn("--noEmit", build)
        self.assertIn("--outDir <dir>/<name>/dist", build)
        self.assertIn("node <dir>/<name>/dist/<name>.js", run)

    def test_java_compiles_into_dir_classes_and_runs_through_module_2s_launch_route(self):
        _, build, run = self.rows["Java"]
        self.assertIn("javac -d <dir>/classes -sourcepath <dir>", build)
        self.assertIn("Module 2's Java launch route", run)
        self.assertIn("<dir>/classes", run)

    def test_rust_programs_in_one_dir_share_one_target_dir(self):
        _, build, run = self.rows["Rust"]
        for cmd in (build, run):
            self.assertIn("--target-dir <dir>/target", cmd)

    def test_commands_are_portable_between_posix_and_powershell(self):
        """No `&&`, `$VAR`, `;` chaining or backslash path: each differs between the shells."""
        for lang, row in self.rows.items():
            for label, cell in zip(("files", "build", "run"), row):
                for command in spans(cell):
                    with self.subTest(language=lang, cell=label, command=command):
                        self.assertNotRegex(command, r"&&|\$|;|\\")


class TheRulesForEveryLanguage(unittest.TestCase):
    def setUp(self):
        self.statement = squash(section(read(GROUND_RULES))).replace("**", "")

    def test_the_build_timeout_includes_dependency_resolution(self):
        self.assertIn("Every build has a 120-second timeout, dependency resolution included.",
                      self.statement)

    def test_every_command_runs_from_the_project_root_in_the_sourced_shell(self):
        self.assertIn("Run every command from the project root, in the shell where Module 2's "
                      "env script is sourced", self.statement)
        # ⛔ INV-001, not INV-002 (#690): one spelling surviving a POSIX shell and PowerShell is
        # a PLATFORM claim. INV-002 is language agnosticism and governs the per-language rows of
        # the table above, not this sentence; `graduation/database-backup.md:52` already reads
        # the PowerShell hazard the same way, as "(INV-166, INV-001)".
        self.assertIn("run unchanged in a POSIX shell and in PowerShell (INV-001)", self.statement)

    def test_a_missing_tool_is_named_in_the_fix_instruction(self):
        self.assertIn("A build that fails because a tool is not found gets a Fix_Instruction "
                      "naming that tool", self.statement)
        for tool in MISSING_TOOLS:
            with self.subTest(tool=tool):
                self.assertIn(tool, self.statement)


class ManifestsComeFromTheToolchainAndTheServer(unittest.TestCase):
    def setUp(self):
        self.statement = squash(section(read(GROUND_RULES)))

    def test_each_language_uses_its_own_init_command(self):
        for command in ("dotnet new console --name <name> --output <dir>/<name>",
                        "cargo init --name <name> --vcs none <dir>/<name>",
                        "npm init -y", "tsc --init"):
            with self.subTest(command=command):
                self.assertIn("`%s`" % command, self.statement)

    def test_the_senzing_dependency_comes_from_the_server_or_module_2(self):
        self.assertGreaterEqual(self.statement.count("`dependency_note`"), 2,
                                "Rust and TypeScript must each take the server's dependency_note")
        self.assertIn("Module 2's C# route", self.statement)
        self.assertIn("never from memory (INV-080)", self.statement)

    def test_no_public_nuget_feed_and_a_missing_source_stops(self):
        self.assertIn("Never add a public NuGet feed for `Senzing.Sdk` (INV-222)", self.statement)
        self.assertNotIn("nuget.org", self.statement)
        self.assertIn("stop with the route's own outcome (INV-283)", self.statement)

    def test_an_existing_manifest_is_reused(self):
        self.assertIn("The folder already has its manifest", self.statement)
        self.assertIn("Skip the init command", self.statement)

    def test_the_absence_claim_carries_its_marker(self):
        # Assembled, so this line is not itself read as a marker by the negatives scanner.
        marker = "<!-- MCP-" + "NEGATIVE: generate_scaffold(workflow='full_pipeline')"
        self.assertIn(marker, self.statement)


class ModuleThreesCommandsAreUnchanged(unittest.TestCase):
    """With `<dir>` = `src/system_verification`, the section gives Module 3's own commands."""

    def setUp(self):
        self.ground_rules = read(GROUND_RULES)
        self.before = module3_before_the_move()

    def test_every_command_is_the_one_module_3_ran(self):
        self.assertEqual([], commands_that_drifted(self.ground_rules, self.before))

    def test_a_drifted_command_is_reported(self):
        for old, new, lang in (
                ("--target-dir <dir>/target`", "--target-dir <dir>/build`", "Rust"),
                ("`python3 <dir>/<name>.py`", "`python <dir>/<name>.py`", "Python"),
                ("--output <dir>/<name>`", "--output <dir>`", "C# project creation")):
            with self.subTest(language=lang):
                self.assertIn(old, self.ground_rules)
                drifted = self.ground_rules.replace(old, new, 1)
                problems = commands_that_drifted(drifted, self.before)
                self.assertTrue(any(p.startswith(lang) for p in problems), problems)


class ModuleThreeCitesTheSectionAndKeepsNoCopy(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE1)
        self.ground_rules = read(GROUND_RULES)

    def test_step_5_cites_the_section_by_file_and_name_with_its_dir(self):
        body = squash(step(self.text, "### Step 5:"))
        self.assertNotEqual("", body, "Step 5 is gone")
        self.assertIn("(INV-300) Every Module 3 program is created, built and run as %s says, "
                      "with `<dir>` = `%s`." % (CITATION, MODULE3_DIR), body.replace("**", ""))

    def test_step_5_keeps_its_program_table_build_check_and_checkpoint(self):
        body = step(self.text, "### Step 5:")
        for name, creator in PROGRAMS.items():
            with self.subTest(program=name):
                self.assertIn("| `%s` | %s |" % (name, creator), body)
        for item in ("1. Execute the build command for `verify_pipeline`",
                     "2. **If the build exits with code 0:**", "3. **If the build fails**",
                     "4. **If the build does not complete within that section's build timeout:**",
                     '"build_compilation"'):
            with self.subTest(item=item):
                self.assertIn(item, body)

    def test_step_5_has_no_command_project_creation_or_timeout_value(self):
        body = step(self.text, "### Step 5:")
        self.assertNotIn(CREATING, body)
        self.assertNotIn("120", body)
        self.assertNotIn("Program files", body)

    def test_every_program_is_created_by_the_step_the_table_names(self):
        for name, creator in PROGRAMS.items():
            with self.subTest(program=name):
                body = squash(step(self.text, "### " + creator + ":"))
                self.assertNotEqual("", body, "%s is gone" % creator)
                self.assertIn("as the program `%s` in `%s`" % (name, MODULE3_DIR), body,
                              "%s does not save the program `%s` it is said to create"
                              % (creator, name))

    def test_each_citing_step_cites_the_section_directly(self):
        self.assertEqual([], uncited_steps(self.text))

    def test_a_missing_citation_is_reported(self):
        body = step(self.text, "### Step 8:")
        self.assertIn(squash(CITATION), squash(body))
        uncited = self.text.replace(body, re.sub(r"ground-rules\.md", "ground-rule.md", body))
        self.assertIn("### Step 8: does not cite %s" % CITATION, uncited_steps(uncited))

    def test_the_retired_phrase_coming_back_is_reported(self):
        body = step(self.text, "### Step 6:")
        returned = self.text.replace(body, body + "\nBuild it with Step 5's table.\n")
        self.assertIn("### Step 6: still says \"Step 5's table\"", uncited_steps(returned))

    def test_step_3_builds_before_it_runs(self):
        body = squash(step(self.text, "### Step 3:"))
        self.assertIn("Build it, then run it", body)
        self.assertLess(body.find("Build it, then run it"),
                        body.find("The run has a 30-second timeout"))

    def test_no_shipped_file_but_the_ground_rules_restates_a_command(self):
        """Only the section is exempt: the rest of `ground-rules.md` is scanned too (#595)."""
        files = corpus_files("plugins", suffixes={".md"})
        self.assertIn(PHASE1, files, "the scan does not reach Module 3 (INV-265)")
        self.assertIn(GROUND_RULES, files, "the scan does not reach the ground rules (INV-265)")
        problems = []
        for path in files:
            rel = path.relative_to(REPO_ROOT).as_posix()
            text = read(path)
            if path == GROUND_RULES:
                text = outside_the_section(text)
            problems += restatements(rel, text, self.ground_rules)
        self.assertEqual([], problems)

    def test_a_restated_command_elsewhere_in_the_ground_rules_is_reported(self):
        """Negative control: the syntax-check list #595 removed, put back, fails the scan."""
        anchor = "- **Confirm it with a compile, not by re-reading the source.**"
        self.assertIn(anchor, self.ground_rules)
        for line, expect in (
                ("Syntax-check it with `python3 -m py_compile <file>` or `tsc --noEmit`.",
                 "restates a command: `python3 -m py_compile"),
                ("Build it with `dotnet build src/system_verification/verify_pipeline`.",
                 "restates a command: `dotnet build")):
            with self.subTest(line=line):
                restated = self.ground_rules.replace(anchor, line + "\n" + anchor, 1)
                problems = restatements("ground-rules", outside_the_section(restated),
                                        self.ground_rules)
                self.assertTrue(any(expect in p for p in problems), problems)

    def test_the_section_itself_stays_exempt(self):
        body = section(self.ground_rules)
        self.assertIn("`dotnet build <dir>/<name>`", body)
        self.assertNotIn("`dotnet build <dir>/<name>`", outside_the_section(self.ground_rules))
        self.assertEqual(
            [], restatements("ground-rules", outside_the_section(self.ground_rules),
                             self.ground_rules))
        renamed = self.ground_rules.replace(SECTION, "## Building a program", 1)
        self.assertEqual(renamed, outside_the_section(renamed),
                         "a renamed section must exempt nothing (INV-265)")

    def test_a_restated_command_in_module_3_is_reported(self):
        body = step(self.text, "### Step 6:")
        for line, expect in (
                ("Build it with `python3 -m py_compile src/system_verification/<name>.py`.",
                 "restates `python3 -m py_compile"),
                ("Build it with `dotnet build src/system_verification/verify_pipeline`.",
                 "restates a command: `dotnet build"),
                ("Enforce a 120-second build timeout.", "restates the build timeout")):
            with self.subTest(line=line):
                restated = self.text.replace(body, body + "\n" + line + "\n")
                problems = restatements("phase1", restated, self.ground_rules)
                self.assertTrue(any(expect in p for p in problems), problems)


class EveryOtherProgramCitesTheSection(unittest.TestCase):
    """#563, #594: every step found to save, build or run a program builds through the section."""

    def setUp(self):
        self.texts = skill_texts()
        self.dirs = statement_dirs(read(GROUND_RULES))
        self.sites = program_sites(self.texts, self.dirs)

    def test_the_scan_reads_every_dir_the_statement_lists(self):
        self.assertEqual(("src/system_verification", "src/collect", "src/load", "src/transform",
                          "src/query", "src/server"), self.dirs)

    def test_the_scan_reaches_every_module_that_builds_programs(self):
        """A floor, not the list: the sites #563 and #594 named are among those found (INV-265)."""
        found = {(s.rel, s.heading.split(":")[0].split(". ")[0]) for s in self.sites}
        for rel, heading in (
                ("module-03-system-verification/phase1-verification.md", "### Step 3"),
                ("module-03-system-verification/phase2-report-close.md", "## Step 10"),
                ("module-03b-truthset-visualization/phase1-visualization.md", "### 1.2 Register"
                 " the Truth Set data source codes and load"),
                ("module-03b-truthset-visualization/phase1-visualization.md", "## Step 2"),
                ("module-03b-truthset-visualization/phase2-close.md", "## Step 4"),
                (M4, "### 2"),
                ("module-05-data-quality-mapping/phase1-quality-assessment.md", "## 5a"),
                (M5_MAPPING, "### 13"), (M5_TEST_LOAD, "#### 24a"), (M6_A, "## 3"),
                (M2, "## Receiving a `setup_detour` (from a later module)"), (M6_B, "## 9"),
                (M6_B, "## Receiving a `quality_iteration` (from Query, Visualize and Discover, or "
                       "Phase D)"),
                (GROUND_RULES_REL, "## Showing one resolved entity as text"), (M6_C, "## 20"),
                ("module-06-data-processing/phaseD-validation.md", "## 21"),
                ("module-06-data-processing/phaseD-validation.md",
                 "## Match-key audit (run before the iterate-vs-proceed gate)"),
                (M7_QUERY, "## 2"), (M7_QUERY, "### 3c"),
                ("module-07-query-visualize-discover/phase2-discover.md", "### Step 4a"),
                (M7_DISCOVER, "### Step 4e")):
            with self.subTest(site=(rel, heading)):
                self.assertIn((rel, heading), found)

    def test_each_site_names_its_program_and_cites_the_section(self):
        self.assertEqual([], uncited_sites(self.sites, self.dirs))

    def test_every_program_is_created_before_it_is_built_or_run(self):
        self.assertEqual([], built_before_created(self.sites, self.dirs))

    def test_every_exemption_names_a_step_and_gives_a_reason(self):
        self.assertEqual([], stale_exemptions(self.texts))

    def test_module_5_creates_register_data_sources_and_er_stats(self):
        created = {program for s in self.sites if s.rel == M5_TEST_LOAD
                   for program in named_programs(s.body, self.dirs)
                   if creates_program(s.body, *program)}
        self.assertEqual({("register_data_sources", "src/load"), ("er_stats", "src/query")},
                         created)

    def test_phase_c_reuses_phase_bs_process_redo(self):
        """Where a program already exists, the site names it rather than a new one (#594)."""
        body = squash(site_body(self.texts[M6_C], "## 20. "))
        self.assertIn("the program `process_redo` in `src/load`", body)
        self.assertNotIn("as the program", body)

    def test_module_2_creates_it_when_it_is_missing(self):
        body = squash(site_body(self.texts[M2], "- **`register-sources`.**"))
        self.assertIn("Where it does not, items 2 and 3 create and build it first.", body)

    def test_no_shipped_file_keeps_a_retired_reference_or_a_loose_program_path(self):
        files = corpus_files("plugins", suffixes={".md"})
        self.assertIn(SKILLS / M6_A, files, "the scan does not reach Module 6 (INV-265)")
        problems = []
        for path in files:
            problems += retired_references(path.relative_to(REPO_ROOT).as_posix(), read(path))
        self.assertEqual([], problems)

    def test_module_5_builds_one_program_per_source_the_transform(self):
        body = squash(site_body(self.texts[M5_MAPPING], "### 13. "))
        self.assertIn("The `<name>_mapper.<ext>` that `mapping_workflow` step 4 asks for is this "
                      "program's foundation, not a separate program to build.", body)

    def test_module_6_builds_and_runs_register_data_sources_by_the_section(self):
        body = squash(site_body(self.texts[M6_A], "## 4a. "))
        self.assertIn("with `<dir>` = `src/load` and `<name>` = `register_data_sources`, in every "
                      "language", body)
        self.assertIn("Run it before the Phase B load,** with that section's run command", body)

    def test_module_7_step_2_gives_each_program_its_own_engine_setup(self):
        body = squash(site_body(self.texts[M7_QUERY], "## 2. "))
        self.assertIn("In C#, Rust and TypeScript there is no shared helper to write: each "
                      "program is its own project in its own folder, so each carries its own "
                      "engine setup, and the factory-lifetime rule applies inside it.", body)

    def test_a_load_keeps_the_sections_build_timeout(self):
        body = squash(site_body(self.texts[M6_B], "## 7. "))
        self.assertIn("The load's own timeout is this step's; the build, at Phase A step 3, keeps "
                      "that section's build timeout.", body)

    def sites_with(self, rel, text, dirs=None):
        dirs = dirs or self.dirs
        return program_sites(dict(self.texts, **{rel: text}), dirs), dirs

    def test_a_missing_citation_is_reported(self):
        for rel, start in ((M7_QUERY, "## 3. "),
                           ("module-06-data-processing/phaseD-validation.md", "## 21. "),
                           ("module-03b-truthset-visualization/phase1-visualization.md",
                            "### 1.2 ")):
            with self.subTest(site=(rel, start)):
                text = self.texts[rel]
                body = site_body(text, start)
                self.assertIn("ground-rules.md", body)
                sites, dirs = self.sites_with(rel, text.replace(
                    body, body.replace("ground-rules.md", "ground-rule.md")))
                heading = next(s.heading for s in sites if s.rel == rel
                               and s.heading.startswith(start.strip()))
                self.assertIn("%s %s does not cite %s" % (rel, heading, CITATION),
                              uncited_sites(sites, dirs))

    def test_a_dropped_program_name_is_reported(self):
        rel = "module-03b-truthset-visualization/phase1-visualization.md"
        text = self.texts[rel]
        broken = re.sub(r"the program `truthset_server`\s+in `src/server`",
                        "it under `src/server/`", text)
        self.assertNotEqual(text, broken)
        problems = uncited_sites(*self.sites_with(rel, broken))
        self.assertTrue(any(p.startswith(rel + " ### 2.1 Choose the path")
                            and "src/server" in p for p in problems), problems)

    def test_a_new_step_that_saves_a_program_in_a_dir_is_found(self):
        """A site added next month is found without anyone adding it to this file."""
        rel = "module-06-data-processing/phaseD-validation.md"
        added = self.texts[rel] + ("\n## 29. Report the matches\n\nGenerate a short program and "
                                   "save it in `src/query/`, then run it.\n")
        problems = uncited_sites(*self.sites_with(rel, added))
        self.assertIn("%s ## 29. Report the matches does not cite %s" % (rel, CITATION), problems)
        self.assertIn("%s ## 29. Report the matches does not name its program in `src/query`"
                      % rel, problems)

    def test_a_new_step_that_writes_sdk_code_with_no_dir_is_found(self):
        rel = M7_DISCOVER
        added = self.texts[rel] + ("\n### Step 4f: Count the merges\n\nUse `reporting_guide("
                                   "topic='evaluation', language='<chosen_language>')` and count "
                                   "them.\n")
        problems = uncited_sites(*self.sites_with(rel, added))
        self.assertIn("%s ### Step 4f: Count the merges names no program `<name>` in a `<dir>`"
                      % rel, problems)

    def test_a_dir_the_statement_adds_is_scanned(self):
        """The `<dir>` list is read from the statement, so a new directory is scanned at once."""
        ground_rules = read(GROUND_RULES)
        widened = ground_rules.replace("`src/query` or `src/server`",
                                       "`src/query`, `src/server` or `src/reports`", 1)
        self.assertNotEqual(ground_rules, widened)
        dirs = statement_dirs(widened)
        self.assertIn("src/reports", dirs)
        rel = M7_DISCOVER
        added = (self.texts[rel]
                 + "\n### Step 4f: Report\n\nSave the report program in `src/reports`.\n")
        problems = uncited_sites(*self.sites_with(rel, added, dirs))
        self.assertIn("%s ### Step 4f: Report does not name its program in `src/reports`" % rel,
                      problems)

    def test_an_exemption_whose_step_is_gone_is_reported(self):
        rel, heading = GROUND_RULES_REL, "## Building and running a program"
        renamed = dict(self.texts, **{rel: self.texts[rel].replace(heading, "## Building", 1)})
        self.assertIn("the exempt step %s %s is gone" % (rel, heading), stale_exemptions(renamed))
        self.assertIn("the exempt step a.md # A gives no reason",
                      stale_exemptions({"a.md": "# A\n"}, {("a.md", "# A"): " "}))

    def test_a_program_built_before_any_step_creates_it_is_reported(self):
        text = self.texts[M5_MAPPING]
        broken = re.sub(r"Save it as\s+the program `transform_\[name\]` in `src/transform`",
                        "Save it in `src/transform`", text, count=1)
        self.assertNotEqual(text, broken)
        problems = built_before_created(*self.sites_with(M5_MAPPING, broken))
        self.assertIn("%s ### 14. Test builds or runs `transform_[name]` in `src/transform` before "
                      "any step creates it" % M5_MAPPING, problems)

    def test_a_run_moved_ahead_of_its_creator_is_reported(self):
        i = next(n for n, s in enumerate(self.sites)
                 if s.rel == M6_C and s.heading.startswith("## 17. "))
        reordered = self.sites[:i] + [self.sites[i + 1], self.sites[i]] + self.sites[i + 2:]
        self.assertTrue(self.sites[i + 1].heading.startswith("## 18. "))
        self.assertIn("%s %s builds or runs `orchestrator` in `src/load` before any step "
                      "creates it" % (M6_C, self.sites[i + 1].heading),
                      built_before_created(reordered, self.dirs))

    def test_a_file_with_no_place_in_the_walk_is_reported(self):
        texts = dict(self.texts, **{"module-08-new/SKILL.md":
                                    "# New\n\nSave the program `x` in `src/load`.\n"})
        self.assertIn("module-08-new/SKILL.md has a program site and no place in WALK",
                      built_before_created(program_sites(texts, self.dirs), self.dirs))

    def test_a_restated_command_at_a_site_is_reported(self):
        ground_rules = read(GROUND_RULES)
        text = self.texts[M6_A]
        for line, expect in (
                ("3. Build it with `dotnet build src/load/register_data_sources`.",
                 "restates a command: `dotnet build"),
                ("Run it with `python3 src/load/register_data_sources.py`.",
                 "restates a command: `python3 src/"),
                ("Add it with `dotnet add package Senzing.Sdk --source SenzingLocal`.",
                 "restates a command: `dotnet add"),
                ("\n```bash\ncargo run --manifest-path src/query/review_entities/Cargo.toml\n```",
                 "restates a command: cargo run"),
                ("Run it with `node src/server/results_server/dist/results_server.js`.",
                 "restates a command: `node src/server"),
                ("Build it with `mvn package`.", "restates a command: `mvn package"),
                ("Run it with `python3 tools/check_load.py`.",
                 "restates a command: `python3 tools")):
            with self.subTest(line=line):
                restated = text.replace("## 4a. ", "## 4a. " + line + "\n", 1)
                problems = restatements(M6_A, restated, ground_rules)
                self.assertTrue(any(expect in p for p in problems), problems)

    def test_a_run_of_the_plugins_own_script_is_not_a_restated_command(self):
        """The positive control: the plugin's scripts are the guide's tools, not programs."""
        text = ('Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/capture_screenshots.py"`.\n\n'
                '```bash\npython3 "${CLAUDE_PLUGIN_ROOT}/scripts/package_bootcamp.py" --check\n'
                'python3 <this-skill-dir>/../../scripts/generate_recap_pdf.py\n```\n')
        self.assertEqual([], restatements(M6_A, text, read(GROUND_RULES)))

    def test_the_retired_references_coming_back_are_reported(self):
        for line, expect in (
                ("using the same per-language build command as the loader",
                 "same per-language build command"),
                ("using the run command for the chosen language",
                 "the run command for the chosen language"),
                ("Save to `src/load/orchestrator.[ext]`.", "loose program file"),
                ('"program": "src/query/<file>"', "loose program file")):
            with self.subTest(line=line):
                problems = retired_references(M6_A, self.texts[M6_A] + "\n" + line + "\n")
                self.assertTrue(any(expect in p for p in problems), problems)


class ArgumentsFollowTheRunCommand(unittest.TestCase):
    """#793: argument passing is stated once, and Module 4 and Module 5 build through the section."""

    def setUp(self):
        self.ground_rules = read(GROUND_RULES)
        self.texts = skill_texts()
        self.dirs = statement_dirs(self.ground_rules)

    def test_the_section_says_how_a_run_passes_arguments(self):
        self.assertEqual([], argument_problems(self.ground_rules))

    def test_it_is_an_every_language_bullet(self):
        every = block(section(self.ground_rules), "**Every language:**", r"\n\*\*Per language")
        self.assertIn(ARGUMENTS_BULLET, every)

    def test_a_dropped_dash_dash_is_reported(self):
        for old, new, expect in (
                ("`cargo run` and `dotnet run` take a `--` first", "`cargo run` takes a `--` first",
                 "C#'s Run command `dotnet run"),
                ("the Run command, then `--`, then the arguments", "the Run command, then them",
                 "where the `--` goes"),
                ("On native Windows and on the `docker` route", "On the `docker` route",
                 "native Windows' call")):
            with self.subTest(old=old):
                self.assertIn(old, self.ground_rules)
                problems = argument_problems(self.ground_rules.replace(old, new, 1))
                self.assertTrue(any(expect in p for p in problems), problems)
        gone = self.ground_rules.replace(ARGUMENTS_BULLET, "- **Arguments**", 1)
        self.assertEqual(["the section has no %r" % ARGUMENTS_BULLET], argument_problems(gone))

    def test_no_shipped_file_but_the_section_restates_it(self):
        problems = []
        for path in corpus_files("plugins", suffixes={".md"}):
            text = read(path)
            if path == GROUND_RULES:
                text = outside_the_section(text)
            problems += restated_argument_rule(path.relative_to(REPO_ROOT).as_posix(), text)
        self.assertEqual([], problems)

    def test_a_restated_arguments_rule_is_reported(self):
        text = self.texts[M5_MAPPING]
        restated = text.replace("### 14. Test\n", "### 14. Test\n\nFor Rust, put `--` before the "
                                "two arguments.\n", 1)
        self.assertNotEqual(text, restated)
        self.assertTrue(restated_argument_rule(M5_MAPPING, restated))
        self.assertEqual([], restated_argument_rule(M5_MAPPING, text))

    def test_module_5s_transform_takes_its_input_and_output_as_arguments(self):
        self.assertEqual([], transform_run_problems(self.texts[M5_MAPPING]))

    def test_module_5_steps_18_input_is_never_the_registry_file_path(self):
        body = squash(site_body(self.texts[M5_MAPPING], "### 18. "))
        self.assertIn("the input is never that `file_path`, which then names the output", body)

    def test_a_transform_run_that_names_no_input_is_reported(self):
        text = self.texts[M5_MAPPING]
        for old, new, expect in (
                ("Pass the source's file in `data/raw/` as its input argument",
                 "Pass the source's `file_path` as its input argument", "### 18. does not pass"),
                ("pass the source's sample file under `data/samples/` as its input argument",
                 "pass a sample", "### 14. does not pass"),
                ("Its code fixes no input path", "Its code reads its input", "step 13 does not say")):
            with self.subTest(old=old):
                self.assertIn(old, text)
                problems = transform_run_problems(text.replace(old, new, 1))
                self.assertTrue(any(p.startswith(expect) for p in problems), problems)

    def test_module_4_creates_its_programs_in_src_collect_and_cites_the_section(self):
        sites = [s for s in program_sites(self.texts, self.dirs) if s.rel == M4]
        self.assertEqual(["### 2. For each data source, collect the data"],
                         [s.heading for s in sites])
        created = {program for s in sites for program in named_programs(s.body, self.dirs)
                   if creates_program(s.body, *program)}
        self.assertEqual(COLLECT_PROGRAMS, created)
        self.assertEqual([], uncited_sites(sites, self.dirs))
        self.assertIn("passing its arguments %s" % ARGUMENTS_POINTER, sites[0].body)
        self.assertNotIn("`src/scripts/` that fetches", sites[0].body,
                         "the collection program left `src/scripts/`, the env script's folder")

    def test_a_restated_command_at_module_4s_site_is_reported(self):
        text = self.texts[M4]
        anchor = "**Converter and collection programs.**"
        self.assertIn(anchor, text)
        self.assertEqual([], restatements(M4, text, self.ground_rules))
        for line, expect in (
                ("Run it with `python3 src/collect/convert_customers.py in.xlsx data/raw/c.csv`.",
                 "restates a command: `python3 src/"),
                ("Run it with `cargo run --manifest-path src/collect/collect_api/Cargo.toml -- x`.",
                 "restates a command: `cargo run")):
            with self.subTest(line=line):
                restated = text.replace(anchor, line + "\n\n" + anchor, 1)
                problems = restatements(M4, restated, self.ground_rules)
                self.assertTrue(any(expect in p for p in problems), problems)

    def test_a_dropped_citation_at_module_4s_site_is_reported(self):
        text = self.texts[M4]
        anchor = "**Converter and collection programs.**"
        start = text.index(anchor)
        end = text.index("\n\n", start)
        para = text[start:end]
        broken = text.replace(para, para.replace("ground-rules.md", "ground-rule.md"), 1)
        sites = [s for s in program_sites(dict(self.texts, **{M4: broken}), self.dirs)
                 if s.rel == M4]
        self.assertIn("%s %s does not cite %s" % (M4, sites[0].heading, CITATION),
                      uncited_sites(sites, self.dirs))


class GraduationCarriesTheManifests(unittest.TestCase):
    def setUp(self):
        self.text = read(SKILLS / GRADUATION_REL)

    def test_the_root_manifest_row_says_only_python_sits_at_the_root(self):
        row = next((line for line in self.text.splitlines()
                    if line.startswith("| `requirements.txt`")), "")
        self.assertIn("Only Python's `requirements.txt` sits at the root", row)
        self.assertIn("C#, Rust and TypeScript manifests travel inside their program folders",
                      row)

    def test_src_is_copied_whole_so_each_program_folder_keeps_its_manifest(self):
        for tree in ("transform", "load", "query"):
            with self.subTest(tree=tree):
                self.assertIn("| `src/%s/**` | `production/src/%s/` |" % (tree, tree), self.text)

    def test_the_copy_carries_no_build_output_and_the_gitignore_lists_it(self):
        self.assertEqual([], build_output_problems(self.text))
        statement = section(read(GROUND_RULES))
        for written in BUILD_OUTPUT_IN_THE_STATEMENT:
            with self.subTest(written=written):
                self.assertIn(written, statement)

    def test_build_output_in_the_copy_or_out_of_the_gitignore_is_reported(self):
        no_classes = self.text.replace("`target/`, `classes/`, `bin/`", "`target/`, `bin/`", 1)
        self.assertNotEqual(self.text, no_classes)
        self.assertIn("the production `.gitignore` does not list `classes/`",
                      build_output_problems(no_classes))
        whole = self.text.replace(NO_BUILD_OUTPUT, "**The `src/**` rows copy everything.**", 1)
        self.assertIn("graduation has no %r" % NO_BUILD_OUTPUT, build_output_problems(whole))
        rule = block(self.text, NO_BUILD_OUTPUT, r"\n\n")
        kept = self.text.replace(rule, rule.replace("`node_modules/`", "the packages"), 1)
        self.assertNotEqual(self.text, kept)
        self.assertIn("graduation's copy does not skip `node_modules/`",
                      build_output_problems(kept))

    def test_usage_gives_each_programs_commands_from_the_section(self):
        body = squash(block(self.text, "**Usage gives each copied program's build and run "
                                       "commands.**", r"\n  - \*\*|\n- \*\*"))
        self.assertNotEqual("", body, "the Usage bullet is gone")
        self.assertIn(CITATION, body)
        self.assertIn("with that program's `<dir>` and `<name>`, run from `production/`", body)


class TheHeldBlockCoversEveryModule(unittest.TestCase):
    def setUp(self):
        self.ledger = read(IMPLEMENTED)

    def test_the_drafted_wording_covers_every_module_that_builds_programs(self):
        self.assertEqual([], held_block_problems(self.ledger))

    def test_the_old_wording_is_reported(self):
        body = widening_correction(self.ledger)
        m = re.search(r"(?m)^  \*\*INV-NNN\*\* — .*$", body)
        old = ("  **INV-NNN** — Every program System verification builds MUST be created by an "
               "earlier step and MUST be built and run by the commands in Phase 1 Step 5's one "
               "build-and-run table, which every other step cites rather than restates (INV-300).")
        reverted = self.ledger.replace(m.group(0), old, 1)
        problems = held_block_problems(reverted)
        self.assertIn("the drafted wording does not name %s" % STATEMENT_PATH, problems)
        self.assertIn("the drafted wording does not cover Data processing", problems)

    def test_a_missing_correction_is_reported(self):
        stripped = self.ledger.replace(WIDENING_CORRECTION, "- **Removed:**", 1)
        self.assertIn("%s has no %r" % (WIDENING_ENTRY, WIDENING_CORRECTION),
                      held_block_problems(stripped))

    def test_a_released_hold_is_reported(self):
        body = block(self.ledger, HELD_BLOCK + "\n", r"\n## ")
        released = self.ledger.replace(body, body.replace("**HELD 2026-10-13:**", "", 1), 1)
        self.assertIn("the block is no longer held", held_block_problems(released))


if __name__ == "__main__":
    unittest.main()
