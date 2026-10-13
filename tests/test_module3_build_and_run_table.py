"""Every Module 3 program is created by an earlier step and is built and run by Step 5's table.

Before #511, Step 5's build table assumed project files that no step created. C# built
`src/system_verification/` with no `.csproj`, Rust built a `Cargo.toml` nobody wrote, and
TypeScript compiled with `--noEmit` while Step 6 then ran the output. Only Python and Java worked.
No step said how to *run* a program either. Step 3 ran `verify_init` before any build step existed,
and Step 5a borrowed "the same per-language build command as Step 5".

⛔ **Step 5's table is the one statement of how a Module 3 program is built and run** (INV-300).
This guard checks the table and its citations:

* the table has a build and a run command for each of Python, Java, C#, Rust and TypeScript;
* every program the table names is created by the step the table says, and that step cites the
  table rather than restating a command;
* C#, Rust and TypeScript programs each get their own folder and manifest, made by the
  toolchain's init command, with the Senzing dependency taken from the server's
  `dependency_note` (Rust, TypeScript) or Module 2's package-source route (C#), and never from a
  public NuGet feed (INV-080, INV-222);
* TypeScript's build emits the JavaScript its run executes, so it has no `--noEmit`;
* Java's run goes through Module 2's launch route, which owns the classpath separator;
* the commands have no shell-specific syntax, so they run unchanged in a POSIX shell and in
  PowerShell (INV-002).

⚠️ It pins the text of the module. It cannot observe a real `dotnet`, `cargo`, `tsc` or `javac`
build of a Bootcamper's program.

Source issue: #511.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PHASE1 = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"

LANGUAGES = ("Python", "Java", "C#", "Rust", "TypeScript")
#: Each program and the step that creates it, as Step 5's program table states them.
PROGRAMS = {
    "verify_init": "Step 3",
    "verify_pipeline": "Step 4",
    "register_data_sources": "Step 5a",
    "validate_results": "Step 7",
    "mari_lookup": "Step 7a",
    "database_operations": "Step 8",
}
#: Steps that build or run a program, and the program each one runs.
RUNNING_STEPS = {
    "### Step 3:": "verify_init",
    "### Step 5a:": "register_data_sources",
    "### Step 6:": "verify_pipeline",
    "### Step 7:": "validate_results",
    "### Step 7a:": "mari_lookup",
    "### Step 8:": "database_operations",
}
CITES_TABLE = "Step 5's table"


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def step(text, heading):
    """The text of the step that starts at `heading`, up to the next `### ` or `## ` heading.

    Empty when the heading is missing, which the callers assert against, so a renamed heading
    fails loudly instead of passing vacuously (INV-265).
    """
    i = text.find(heading)
    if i < 0:
        return ""
    rest = text[i + len(heading):]
    m = re.search(r"\n#{2,3} ", rest)
    return rest if m is None else rest[:m.start()]


def table_rows(text):
    """Step 5's build-and-run rows, keyed by language: (files, build, run)."""
    rows = {}
    for line in step(text, "### Step 5:").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] in LANGUAGES:
            rows[cells[0]] = tuple(cells[1:])
    return rows


class TheTableCoversEveryLanguage(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE1)
        self.rows = table_rows(self.text)

    def test_every_language_has_a_build_and_a_run_command(self):
        for lang in LANGUAGES:
            with self.subTest(language=lang):
                self.assertIn(lang, self.rows, f"Step 5's table has no {lang} row")
                _, build, run = self.rows[lang]
                self.assertTrue(build.startswith("`"), f"{lang} has no build command")
                self.assertTrue(run, f"{lang} has no run command")

    def test_every_program_is_created_by_the_step_the_table_names(self):
        for name, creator in PROGRAMS.items():
            with self.subTest(program=name):
                self.assertIn(f"| `{name}` | {creator} |", self.text)
                heading = "### " + creator + ":"
                body = squash(step(self.text, heading))
                self.assertNotEqual("", body, f"{heading} is gone")
                self.assertIn(f"as the program `{name}`", body,
                              f"{creator} does not save the program `{name}` it is said to create")

    def test_typescript_emits_what_it_runs(self):
        _, build, run = self.rows["TypeScript"]
        self.assertNotIn("--noEmit", build)
        self.assertIn("--outDir src/system_verification/<name>/dist", build)
        self.assertIn("node src/system_verification/<name>/dist/<name>.js", run)

    def test_java_runs_through_module_2s_launch_route(self):
        _, build, run = self.rows["Java"]
        self.assertIn("javac -d src/system_verification/classes", build)
        self.assertIn("Module 2's Java launch route", run)
        self.assertIn("src/system_verification/classes", run)

    def test_commands_are_portable_between_posix_and_powershell(self):
        """No `&&`, `$VAR`, `;` chaining or backslash path: each differs between the shells."""
        for lang, (files, build, run) in self.rows.items():
            for label, cell in (("files", files), ("build", build), ("run", run)):
                for command in re.findall(r"`([^`]+)`", cell):
                    with self.subTest(language=lang, cell=label, command=command):
                        self.assertNotRegex(command, r"&&|\$|;|\\")

    def test_rust_programs_share_one_target_dir(self):
        _, build, run = self.rows["Rust"]
        for cmd in (build, run):
            self.assertIn("--target-dir src/system_verification/target", cmd)


class EveryStepCitesTheTable(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE1)

    def test_each_running_step_cites_step_5s_table(self):
        for heading, name in RUNNING_STEPS.items():
            with self.subTest(step=heading):
                body = squash(step(self.text, heading))
                self.assertNotEqual("", body, f"{heading} is gone")
                self.assertIn(CITES_TABLE, body)
                self.assertIn(f"`{name}`", body)

    def test_no_step_restates_a_build_command(self):
        """The commands live in Step 5 alone; a copy elsewhere is a second thing to keep true."""
        for heading in RUNNING_STEPS:
            body = step(self.text, heading)
            with self.subTest(step=heading):
                self.assertNotRegex(body, r"`(?:javac|dotnet build|cargo build|tsc) ")
                self.assertNotIn("same per-language build command", body)

    def test_step_3_builds_before_it_runs(self):
        body = squash(step(self.text, "### Step 3:"))
        self.assertIn("Build it, then run it", body)
        self.assertLess(body.find("Build it, then run it"),
                        body.find("The run has a 30-second timeout"))


class ManifestsComeFromTheToolchainAndTheServer(unittest.TestCase):
    def setUp(self):
        self.step5 = squash(step(read(PHASE1), "### Step 5:"))

    def test_each_language_uses_its_own_init_command(self):
        for command in ("dotnet new console --name <name> --output src/system_verification/<name>",
                        "cargo init --name <name> --vcs none src/system_verification/<name>",
                        "npm init -y", "tsc --init"):
            with self.subTest(command=command):
                self.assertIn(command, self.step5)

    def test_the_senzing_dependency_comes_from_the_server_or_module_2(self):
        self.assertGreaterEqual(self.step5.count("`dependency_note`"), 2,
                                "Rust and TypeScript must each take the server's dependency_note")
        self.assertIn("Module 2's C# route", self.step5)
        self.assertIn("never from memory (INV-080)", self.step5)

    def test_no_public_nuget_feed(self):
        self.assertIn("Never add a public NuGet feed for `Senzing.Sdk` (INV-222)", self.step5)
        self.assertNotIn("nuget.org", self.step5)

    def test_an_existing_manifest_is_reused(self):
        self.assertIn("The folder already has its manifest", self.step5)
        self.assertIn("Skip the init command", self.step5)


if __name__ == "__main__":
    unittest.main()
