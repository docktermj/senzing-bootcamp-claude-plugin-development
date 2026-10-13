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
  than the ground rules restates one of Module 3's commands or the build timeout.

Each check is a function returning its problems, and a negative control mutates the real text and
sees the check report it: a drifted command, a command restated in Module 3, a missing citation,
and the retired phrase come back.

⚠️ It pins the text. It cannot observe a real `dotnet`, `cargo`, `tsc` or `javac` build of a
Bootcamper's program. The comparison with the earlier Module 3 needs the full git history, which
the suite's CI checkout fetches (`fetch-depth: 0`); in a shallow clone it fails rather than
skipping, because a skipped comparison would certify nothing.

Source issues: #511, #562.

Run:  python3 -m unittest discover -s tests
"""
import re
import subprocess
import unittest
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
PHASE1 = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"

#: `origin/main` when #562 began: the last commit whose Module 3 Step 5 held the table itself.
MODULE3_BEFORE_THE_MOVE = "db3dac7f61aba4cb267cd04b973f332f78866f6e"
MODULE3_DIR = "src/system_verification"
MODULE3_FILES = "skills/module-03-system-verification/"

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
#: A command of the statement's shape, in any directory.
COMMAND_SHAPE = re.compile(
    r"`(?:python3 -m py_compile|javac |dotnet (?:build|run|new|add)|cargo (?:build|run|init)"
    r"|tsc |npm init|node \S+/dist/)"
)
#: The build timeout said again outside the section.
BUILD_TIMEOUT_RESTATED = re.compile(
    r"120-second build|120-second timeout for all build|Step 5's 120-second"
)
MISSING_TOOLS = ("`dotnet`", "`cargo`", "`tsc`", "`node`", "`javac`")


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
    reports a command of the statement's shape in any directory, which Module 3 must not carry;
    other modules still build their programs their own way until #563 moves them.
    """
    problems = []
    statement = section(ground_rules)
    commands = [at(c, MODULE3_DIR) for row in table_rows(statement).values()
                for cell in row[1:] for c in spans(cell)]
    for item in project_items(statement).values():
        commands += [at(c, MODULE3_DIR) for c in spans(item) if " " in c]
    flat = squash(text)
    for command in commands:
        if "`%s`" % command in flat:
            problems.append("%s restates `%s`" % (path, command))
    for m in COMMAND_SHAPE.finditer(text if any_directory else ""):
        problems.append("%s restates a command: %s" % (path, text[m.start():m.start() + 40]))
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
        for directory in ("src/system_verification", "src/load", "src/transform", "src/query"):
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
        self.assertIn("run unchanged in a POSIX shell and in PowerShell (INV-002)", self.statement)

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
        files = corpus_files("plugins", suffixes={".md"})
        self.assertIn(PHASE1, files, "the scan does not reach Module 3 (INV-265)")
        problems = []
        for path in files:
            if path != GROUND_RULES:
                rel = path.relative_to(REPO_ROOT).as_posix()
                problems += restatements(rel, read(path), self.ground_rules,
                                         any_directory=MODULE3_FILES in rel)
        self.assertEqual([], problems)

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


if __name__ == "__main__":
    unittest.main()
