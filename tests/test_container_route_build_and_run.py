"""On SDK setup's container route, every build and run happens in the SDK container (#595).

`ground-rules.md` → "Building and running a program" is the one statement of how a Bootcamper
program is built and run (INV-370, INV-300). Its "Every language" rules assumed the host shell, so
a Bootcamper on the `docker` route, the route Windows users take (#508), had no `<runtime> exec`
form, no working directory and no toolchain in the container. #595 fixed it in three places, and
these tests pin each:

1. **The container-route form, stated once.** The section gives
   `<runtime> exec -w /app <container> bash -c '. src/scripts/senzing-env.sh && <command>'`, with
   `<runtime>` and `<container>` read from `config/bootcamp_progress.json` → `docker_containers`,
   followed by the #508 guide-run pointer line. No other shipped file restates it. It is `bash -c`,
   not the `sh -c` the issue's revision 1 wrote (the maintainer's ruling, comment 2 on #595):
   Module 2's env script finds itself through
   `${BASH_SOURCE[0]}`, which dash, the `sh` of a Debian image, rejects with "Bad substitution".
   `TheFormRunsTheEnvScript` runs the form against a stub runtime, with the env script Module 2
   ships, to show both halves of that.
2. **The toolchain.** Module 2's container route installs the chosen language's toolchain in the
   SDK container: the server's command when its `sdk_guide` install reply gives one, otherwise a
   pinned row per language, each ending in a version command checked against the minimum the
   server serves, run with `DEBIAN_FRONTEND=noninteractive` so `apt-get` never waits on a prompt.
   On server 1.39.0 (2026-10-15) no route gave the command, which the site's
   `MCP-NEGATIVE` marker records with its owner. Every row is parsed by `bash -n`, holds no single
   quote (it runs inside `bash -c '…'`), and installs from the image's own package manager.
3. **The in-container compile check.** "Running a file you just wrote" no longer lists its own
   syntax-check commands (`python3 -m py_compile <file>`, `node --check <file>`, `javac`,
   `tsc --noEmit`); it runs the section's Build command in the container-route form.

`tests/test_build_and_run_statement.py` narrows its exemption of `ground-rules.md` to the section
(#594's decision 594-4), so a restatement elsewhere in that file fails there.

Each check is a function returning its problems, and a negative control mutates the real text and
sees the check report it.

It does **not** establish that a row installs a working toolchain in a real `debian:bookworm-slim`
container, or that `<runtime> exec` behaves as the stub does: no container runs in this suite, and
Windows (Git Bash) is unverified, as the pointer line says.

Stdlib only (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"

SECTION = "## Building and running a program"
RUNNING_ELSEWHERE = "## Running a file you just wrote, when the run happens somewhere else"
FORM = "<runtime> exec -w /app <container> bash -c '. src/scripts/senzing-env.sh && <command>'"
#: Any statement of the wrapping, in either shell: what no other file may restate (INV-300).
WRAPPING = re.compile(r"exec -w /app \S+ (?:ba)?sh -c '\. src/scripts/senzing-env\.sh")
POINTER = ("Guide-run in the guide's POSIX shell (Git Bash on Windows); unverified on Windows: no "
           "test runs it there ([guide-run blocks](../bootcamp-onboarding/ground-rules.md"
           "#guide-run-blocks)).")
TOOLCHAIN = "- **Install the chosen language's toolchain in the container.**"
INSTALL_LINE = "<runtime> exec -e DEBIAN_FRONTEND=noninteractive <container> bash -c '<install>'"
LANGUAGES = ("Python", "Java", "C#", "Rust", "TypeScript")
#: Each row's version command, which the step checks against the server's minimum.
VERSION_CHECKS = {
    "Python": "python3 --version",
    "Java": "javac -version",
    "C#": "dotnet --version",
    "Rust": "cargo --version",
    "TypeScript": "tsc --version",
}
#: What each row installs, so a row cannot silently swap its toolchain.
INSTALLS = {
    "Python": ("apt-get install -y python3",),
    "Java": ("apt-get install -y default-jdk-headless",),
    "C#": ("https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb",
           "apt-get install -y dotnet-sdk-10.0"),
    "Rust": ("https://sh.rustup.rs", "-y --profile minimal", "/usr/local/bin/"),
    "TypeScript": ("apt-get install -y nodejs npm", "npm install -g typescript"),
}
#: The retired syntax-check list (#594's decision 594-2, moved here).
RETIRED_CHECKS = ("`python3 -m py_compile <file>`", "`node --check <file>`", "`tsc --noEmit`")
#: The marker's opening, split so the negatives scanner does not read this file as a marker.
MARKER_OPEN = "<!-- MCP-" + "NEGATIVE: "
ENV_TEMPLATE_START = "# --- resolve this script's own location (bash and zsh)"
ENV_TEMPLATE_END = "unset _sz_self _sz_root _sz_settings"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def between(text, start, stop):
    """The text from `start` to the next line matching `stop`, or "" without `start` (INV-265)."""
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i + len(start):]
    m = re.search(stop, rest)
    return start + (rest if m is None else rest[:m.start()])


def fenced_blocks(text):
    return re.findall(r"(?ms)^[ \t]*```[a-z]*\n(.*?)^[ \t]*```", text)


def toolchain_bullet(text):
    return between(text, TOOLCHAIN, r"\n(?:- \*\*|<a id=)")


def install_rows(text):
    """{language: install command} from the toolchain bullet's table."""
    rows = {}
    for line in toolchain_bullet(text).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0] in LANGUAGES:
            rows[cells[0]] = cells[1].strip("`")
    return rows


# --- checks: each returns a list of problems ------------------------------------------------


def form_problems(ground_rules):
    section = between(ground_rules, SECTION, r"\n## ")
    if not section:
        return ["no 'Building and running a program' section"]
    problems = []
    blocks = [b.strip() for b in fenced_blocks(section)]
    if blocks.count(FORM) != 1:
        problems.append(f"the section does not give the container-route form once in a block: {FORM}")
    else:
        after = section[section.index(FORM):].split("```", 1)[1]
        if flat(after.lstrip("\n").split("\n\n", 1)[0]) != POINTER:
            problems.append("the form is not followed by the guide-run pointer line")
    text = flat(section)
    for phrase, what in (
            ("`<command>` is the table's Build or Run command unchanged", "what <command> is"),
            ("`runtime` and `name` of the SDK container's entry in `config/bootcamp_progress.json` "
             "→ `docker_containers`", "where the runtime and the container name come from"),
            ("an entry with no `runtime` is `docker`", "the default runtime"),
            ("The project is mounted at `/app`, so `-w /app` is the project root", "the mount"),
            ("It is `bash -c`, not `sh -c`", "why bash"),
            ("\"Bad substitution\"", "the dash failure it avoids"),
            ("Install the chosen language's toolchain in the container", "the toolchain step"),
            ("With no `docker_containers` entry there is no container to run in",
             "the missing-entry rule")):
        if phrase not in text:
            problems.append(f"the section does not state {what}: {phrase!r}")
    if "On the `docker` route the tool is missing from the container" not in text:
        problems.append("the missing-tool Fix_Instruction does not cover the container")
    return problems


def restated_wrapping(files):
    """Shipped files other than the ground rules that state the wrapping (INV-300)."""
    return [f"{p.name}: {m.group(0)}"
            for p in files if p != GROUND_RULES
            for m in WRAPPING.finditer(read(p))]


def compile_check_problems(ground_rules):
    section = between(ground_rules, RUNNING_ELSEWHERE, r"\n## ")
    if not section:
        return ["no 'Running a file you just wrote' section"]
    problems = [f"the compile check still lists {c}" for c in RETIRED_CHECKS if c in section]
    if re.search(r"`javac`,", section):
        problems.append("the compile check still lists `javac`")
    text = flat(section)
    if ("Run the chosen language's Build command from \"Building and running a program\" *inside* "
            "the container, in that section's container-route form (INV-090)") not in text:
        problems.append("the compile check does not run the section's Build command in the "
                        "container-route form")
    if "retried ONCE before it is believed" not in text:
        problems.append("the one-retry rule is gone")
    return problems


def toolchain_problems(module_2):
    bullet = toolchain_bullet(module_2)
    if not bullet:
        return ["Module 2 has no toolchain bullet"]
    problems = []
    docker_path = between(module_2, "For the `docker` path (Intel Mac", r"\n<a id=\"container-naming\">")
    if TOOLCHAIN not in docker_path:
        problems.append("the toolchain bullet is not on Phase 2's docker path")
    text = flat(bullet)
    for phrase, what in (
            ("`../bootcamp-onboarding/ground-rules.md` → \"Building and running a program\" gives; "
             "do not restate it here (INV-300)", "the pointer to the one statement"),
            ("`sdk_guide(topic='install', platform='docker', language='<chosen_language>')`",
             "the server's install call"),
            ("run it there instead of the row below", "the server's command first"),
            ("with `<runtime>` and `<container>` from its `docker_containers` entry",
             "the recorded container"),
            ("`search_docs(query='v4 System Requirements languages supported')`",
             "the minimum-version route"),
            ("Below the minimum, stop and name both versions; never pick another version from "
             "memory (INV-080)", "the below-minimum stop"),
            ("run the Rust row too", "TypeScript's build-from-source case"),
            ("`DEBIAN_FRONTEND=noninteractive` passed in so `apt-get` never waits on a prompt",
             "why the install runs noninteractive"),
            ("\"tool is not found\" Fix_Instruction", "the failed-row outcome")):
        if phrase not in text:
            problems.append(f"the toolchain bullet does not state {what}: {phrase!r}")
    blocks = [b.strip() for b in fenced_blocks(bullet)]
    if blocks != [INSTALL_LINE]:
        problems.append(f"the toolchain bullet's one block is not {INSTALL_LINE!r}: {blocks!r}")
    elif POINTER not in bullet:
        problems.append("the install block is not followed by the guide-run pointer line")
    if WRAPPING.search(bullet):
        problems.append("the toolchain bullet restates the build-and-run wrapping")
    marker = re.search(re.escape(MARKER_OPEN) + r"(.*?) -->", bullet, re.S)
    if marker is None:
        problems.append("the absence of a server install command carries no MCP-NEGATIVE marker")
    elif "owner: sdk_guide(topic='install', platform='docker', language=<lang>) IS the route" \
            not in marker.group(1):
        problems.append("the MCP-NEGATIVE marker names no owner route (INV-213)")
    rows = install_rows(module_2)
    for lang in LANGUAGES:
        row = rows.get(lang)
        if row is None:
            problems.append(f"no {lang} row")
            continue
        if not row.startswith("apt-get update && "):
            problems.append(f"{lang} row does not start from the image's package index")
        if not row.endswith("&& " + VERSION_CHECKS[lang]):
            problems.append(f"{lang} row does not end with `{VERSION_CHECKS[lang]}`")
        for piece in INSTALLS[lang]:
            if piece not in row:
                problems.append(f"{lang} row does not install with {piece!r}")
        if "'" in row:
            problems.append(f"{lang} row holds a single quote, which ends `bash -c '<install>'`")
        if "sudo" in row.split():
            problems.append(f"{lang} row uses sudo; in the container the guide is root")
    if set(rows) - set(LANGUAGES):
        problems.append(f"rows for unknown languages: {sorted(set(rows) - set(LANGUAGES))}")
    return problems


def env_template(module_2):
    """The env script Module 2 ships, from its fenced template."""
    for block in fenced_blocks(module_2):
        if ENV_TEMPLATE_START in block:
            start = block.index(ENV_TEMPLATE_START)
            end = block.rindex(ENV_TEMPLATE_END) + len(ENV_TEMPLATE_END)
            return block[start:end] + "\n"
    raise LookupError("Module 2's env-script template")


STUB_RUNTIME = """#!/bin/sh
# A stand-in runtime: `exec -w /app <container> <cmd...>` runs <cmd...> in $STUB_APP, the mount.
[ "$1" = exec ] && [ "$2" = -w ] && [ "$3" = /app ] || { echo "stub: unexpected $*" >&2; exit 97; }
[ "$4" = "$STUB_CONTAINER" ] || { echo "stub: no container $4" >&2; exit 98; }
shift 4
cd "$STUB_APP" && exec "$@"
"""


def run_form(form, project, command):
    """Run `form` as the guide would, against the stub runtime, in `project`."""
    bin_dir = project.parent / "bin"
    bin_dir.mkdir(exist_ok=True)
    stub = bin_dir / "docker"
    stub.write_text(STUB_RUNTIME, encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    line = (form.replace("<runtime>", "docker").replace("<container>", "senzing-bootcamp-demo")
            .replace("<command>", command))
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
               STUB_APP=str(project), STUB_CONTAINER="senzing-bootcamp-demo")
    return subprocess.run(["bash", "-c", line], cwd=str(project.parent), env=env,
                          capture_output=True, text=True, timeout=60)


def sh_is_dash():
    """True when `sh` rejects `${BASH_SOURCE[0]}`, as a Debian image's dash does."""
    if shutil.which("sh") is None:
        return False
    probe = subprocess.run(["sh", "-c", "x=${BASH_SOURCE[0]:-$0}"], capture_output=True,
                           text=True, timeout=30)
    return probe.returncode != 0 and "Bad substitution" in probe.stderr


# --- tests -----------------------------------------------------------------------------------


class TheSectionStatesTheContainerForm(unittest.TestCase):
    def setUp(self):
        self.text = read(GROUND_RULES)

    def test_the_form(self):
        self.assertEqual(form_problems(self.text), [])

    def test_negative_control_sh_instead_of_bash(self):
        self.assertTrue(form_problems(self.text.replace(FORM, FORM.replace("bash -c", "sh -c"))))

    def test_negative_control_the_pointer_dropped(self):
        broken = self.text.replace(FORM + "\n  ```\n\n  " + POINTER, FORM + "\n  ```\n\n  Runs.")
        self.assertNotEqual(broken, self.text)
        self.assertTrue(form_problems(broken))

    def test_negative_control_the_runtime_from_preferences(self):
        broken = self.text.replace("`config/bootcamp_progress.json` →\n  `docker_containers`",
                                   "`config/bootcamp_preferences.yaml`")
        self.assertNotEqual(broken, self.text)
        self.assertTrue(form_problems(broken))

    def test_no_other_shipped_file_restates_the_wrapping(self):
        files = corpus_files("plugins", suffixes={".md"})
        self.assertIn(MODULE_2, files, "the scan does not reach Module 2 (INV-265)")
        self.assertEqual(restated_wrapping(files), [])

    def test_negative_control_a_restated_wrapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "SKILL.md"
            copy.write_text(read(MODULE_2) + "\nRun `docker exec -w /app box bash -c '. "
                            "src/scripts/senzing-env.sh && make'`.\n", encoding="utf-8")
            self.assertTrue(restated_wrapping([copy]))


class TheCompileCheckUsesTheBuildCommand(unittest.TestCase):
    def setUp(self):
        self.text = read(GROUND_RULES)

    def test_the_compile_check(self):
        self.assertEqual(compile_check_problems(self.text), [])

    def test_negative_control_the_old_list(self):
        old = ("container in the bootcamper's chosen language (INV-090) — `python3 -m py_compile "
               "<file>`, `node --check <file>`, `javac`, `tsc --noEmit`.")
        section = between(self.text, RUNNING_ELSEWHERE, r"\n## ")
        broken = self.text.replace(section, section + "\n" + old + "\n")
        self.assertTrue(compile_check_problems(broken))


class ModuleTwoInstallsTheToolchain(unittest.TestCase):
    def setUp(self):
        self.text = read(MODULE_2)

    def test_the_toolchain_step(self):
        self.assertEqual(toolchain_problems(self.text), [])

    def test_every_row_parses_as_bash(self):
        for lang, row in install_rows(self.text).items():
            with self.subTest(language=lang):
                proc = subprocess.run(["bash", "-n", "-c", row], capture_output=True, text=True,
                                      timeout=30)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_negative_control_a_row_without_its_version_check(self):
        row = install_rows(self.text)["Java"]
        self.assertTrue(toolchain_problems(self.text.replace(row, row.replace(
            " && javac -version", ""))))

    def test_negative_control_a_single_quote_in_a_row(self):
        row = install_rows(self.text)["Rust"]
        self.assertTrue(toolchain_problems(self.text.replace(row, row.replace(
            "--proto =https", "--proto '=https'"))))

    def test_negative_control_the_noninteractive_flag_dropped(self):
        broken = self.text.replace(INSTALL_LINE, INSTALL_LINE.replace(
            "-e DEBIAN_FRONTEND=noninteractive ", ""), 1)
        self.assertNotEqual(broken, self.text)
        self.assertTrue(toolchain_problems(broken))

    def test_negative_control_the_csharp_row_back_on_dotnet_8(self):
        row = install_rows(self.text)["C#"]
        self.assertTrue(toolchain_problems(self.text.replace(row, row.replace(
            "dotnet-sdk-10.0", "dotnet-sdk-8.0"))))

    def test_negative_control_the_server_first_rule_dropped(self):
        broken = re.sub(r"run\s+it\s+there\s+instead\s+of\s+the\s+row\s+below", "ignore it",
                        self.text)
        self.assertNotEqual(broken, self.text)
        self.assertTrue(toolchain_problems(broken))

    def test_negative_control_the_marker_dropped(self):
        broken = re.sub(r"\n  " + re.escape(MARKER_OPEN) + r"sdk_guide\(topic='install', "
                        r"platform='docker'.*?-->", "", self.text, count=1, flags=re.S)
        self.assertNotEqual(broken, self.text)
        self.assertTrue(toolchain_problems(broken))


@unittest.skipIf(shutil.which("bash") is None, "bash is not installed")
class TheFormRunsTheEnvScript(unittest.TestCase):
    """The form against a stub runtime, with the env script Module 2 ships, in a scratch project."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "proj"
        (self.project / "src" / "scripts").mkdir(parents=True)
        (self.project / "src" / "system_verification").mkdir(parents=True)
        (self.project / "config").mkdir()
        (self.project / "config" / "bootcamp_progress.json").write_text("{}", encoding="utf-8")
        (self.project / "src" / "scripts" / "senzing-env.sh").write_text(
            env_template(read(MODULE_2)), encoding="utf-8")
        (self.project / "src" / "system_verification" / "verify_pipeline.py").write_text(
            "print('ok')\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_form_sources_the_env_script_and_runs_from_the_project_root(self):
        proc = run_form(FORM, self.project, 'printf "%s|%s" "$SENZING_PROJECT_ROOT" "$PWD"')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        root = str(self.project.resolve())
        self.assertEqual(proc.stdout.split("|"), [root, root])

    @unittest.skipIf(shutil.which("python3") is None, "python3 is not installed")
    def test_the_python_build_runs_unchanged_inside_the_form(self):
        proc = run_form(FORM, self.project,
                        "python3 -m py_compile src/system_verification/verify_pipeline.py")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    @unittest.skipUnless(sh_is_dash(), "sh accepts ${BASH_SOURCE[0]} here, so dash is not on PATH")
    def test_negative_control_sh_cannot_source_the_env_script(self):
        proc = run_form(FORM.replace("bash -c", "sh -c"), self.project,
                        'printf "%s" "$SENZING_PROJECT_ROOT"')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Bad substitution", proc.stderr)

    def test_negative_control_an_unrecorded_container(self):
        proc = run_form(FORM.replace("<container>", "someone-elses"), self.project, "true")
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
