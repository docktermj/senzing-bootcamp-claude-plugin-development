"""Guide-run container-route blocks declare their shell, and the schema DDL comes from the SDK container (#508).

INV-001 makes Windows a supported platform, and SDK setup's container route is the route Windows
users take (Python on Windows, and Windows without Scoop). Six blocks on that route were written
for a POSIX shell with no word on which shell runs them. All six are **guide-run**: the guide runs
them with its Bash tool, which on Windows is Git Bash. None is **hand-run**, the case #391 gave
PowerShell 5.1 forms.

The fix has three parts, and these tests pin each:

1. **One statement.** `ground-rules.md` → "Windows and PowerShell" holds the policy once, under the
   anchor `guide-run-blocks` (INV-300): guide-run blocks run in the guide's POSIX shell (Git Bash
   on Windows) and need no PowerShell form; hand-run blocks need a PowerShell 5.1 form (INV-167).
2. **One pointer line at each site.** Each of the six blocks is followed by the same line, which
   links the anchor and carries the INV-163 "unverified on Windows" disclosure in the #391 wording
   ("…unverified on Windows: no test runs them there."). Each site is found by a line of its own
   block, never by a line number (INV-246). A sweep also holds every link to the anchor, anywhere
   in the plugin, to that same wording.
3. **The schema DDL.** On the container route the host has no `/opt/senzing`, so Option 1 step 4
   copies the DDL out of the SDK container into the project's `database/` with the SDK container's
   recorded runtime (`<runtime> cp`, INV-195, INV-200) and applies the project copy. The path is a
   placeholder taken from MCP at runtime (INV-080). The native route still applies the host file.
   The container-route block is run with `sh` against stub runtimes in a temporary project, so the
   test sees the DDL reach `psql`'s stdin from the project copy. Option 2 (a local PostgreSQL)
   applies the DDL "as above" with `psql -f`, so its sentence also says that on the container
   route the DDL comes from the SDK container, the way Option 1's container-route command takes it,
   never from a host path.

Each check is a function returning its problems, and a negative control mutates the real text and
sees the check report it.

It does **not** establish that any of these blocks runs under Git Bash on Windows (this repo's CI
runs on Linux, which is what the disclosure says), or that a real `docker cp` / `podman cp` copies
out of a real container: no container runs in this suite.

Prose is read wrap-aware (INV-346). Stdlib only (INV-108).

Enforces **INV-001**, **INV-163**, **INV-167**, **INV-195**, **INV-200** and **INV-300** at these
sites.

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

from _wrapped_text import match_lines as _match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
PHASE1 = SKILLS / "module-03b-truthset-visualization" / "phase1-visualization.md"
CONTRACT = SKILLS / "module-03b-truthset-visualization" / "visualization-api-reference.md"

ANCHOR_ID = "guide-run-blocks"
ANCHOR = f'<a id="{ANCHOR_ID}"></a>'
LINK = f"../bootcamp-onboarding/ground-rules.md#{ANCHOR_ID}"
#: The one pointer line, in the same wording at every site.
POINTER = ("Guide-run in the guide's POSIX shell (Git Bash on Windows); unverified on Windows: no "
           f"test runs it there ([guide-run blocks]({LINK})).")
#: The #391 disclosure's wording (`graduation/database-backup.md`), which the pointer reuses.
DISCLOSURE = "unverified on Windows: no test runs it there"

#: The six guide-run sites, each found by one line of its own block (INV-246): (label, file, line).
SITES = (
    ("Truth Set 2.1 project copy", PHASE1, 'VIZ_SRC="${CLAUDE_PLUGIN_ROOT}/scripts"'),
    ("viz server launch in the SDK container", CONTRACT, "VIZ_PID=$(<runtime> exec <container> sh -c '"),
    ("SDK container creation", MODULE_2,
     '<runtime> run -d -it --name <name> -p 127.0.0.1:<host_port>:8080 -v "$(pwd)":/app'),
    ("SQLite schema through Python", MODULE_2, 'python3 -c "import sqlite3,sys;'),
    ("PostgreSQL container run", MODULE_2, "docker run -d --name <pg-container> \\"),
    ("PostgreSQL schema, container route", MODULE_2,
     '<runtime> cp "<sdk-container>:<schema path from MCP>"'),
)

STEP_4 = "4. Apply the Senzing PostgreSQL schema DDL"
OPTION_2 = "**Option 2 — Install PostgreSQL locally:**"
OPTION_3 = "**Option 3 — Use an existing PostgreSQL server:**"
STEP_5 = "5. Wire the connection into the engine config"
CONTAINER_ROUTE = "**On SDK setup's container route**"
NATIVE_ROUTE = "**On a native route**"
FENCE = re.compile(r"^[ \t]*```")
HOST_OPT_REDIRECT = re.compile(r"<\s*\"?/opt/senzing")


def read(path):
    return Path(path).read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` (INV-346), taking a pattern string."""
    return _match_lines(text, re.compile(pattern))


def windows_section(text):
    return between(text, "## Windows and PowerShell", "\n## ")


def statement(text):
    """From the anchor to the next heading: the one canonical statement."""
    section = windows_section(text)
    begin = section.index(ANCHOR)
    return section[begin:]


def fenced_block_after(text, marker):
    """``(block_lines, rest)``: the fenced block holding the line ``marker``, and the text after it."""
    lines = text.splitlines()
    at = next((i for i, line in enumerate(lines) if marker in line), None)
    if at is None:
        raise LookupError(marker)
    start = max(i for i in range(at + 1) if FENCE.match(lines[i]))
    end = next(i for i in range(at + 1, len(lines)) if FENCE.match(lines[i]))
    return lines[start + 1:end], "\n".join(lines[end + 1:])


def paragraph_after(rest):
    """The first paragraph after a block, whitespace collapsed, so a wrapped line still reads."""
    para = rest.lstrip("\n").split("\n\n", 1)[0]
    return flat(para)


# --- checks: each returns a list of problems ------------------------------------------------


def ground_rules_problems(text):
    problems = []
    if "## Windows and PowerShell" not in text:
        return ["no 'Windows and PowerShell' section"]
    section = windows_section(text)
    if section.count(ANCHOR) != 1 or text.count(ANCHOR) != 1:
        return [f"{ANCHOR} must appear once, inside 'Windows and PowerShell'"]
    body = statement(text)
    for pattern in (r"This is the canonical statement of which command blocks need a\s+PowerShell form",
                    r"\(INV-300\)",
                    r"A guide-run block\*\* is one the guide runs itself with its Bash tool",
                    r"guide's\s+POSIX shell, which on Windows is Git Bash, so it needs no PowerShell form",
                    r"A hand-run block\*\* is one the Bootcamper types",
                    r"needs a\s+PowerShell 5\.1 form that meets the rules above \(INV-167\)",
                    r"\(INV-163\)",
                    r"There is\s+no PowerShell fallback"):
        if not match_lines(body, pattern):
            problems.append(f"statement lacks {pattern!r}")
    if flat(POINTER.split(" ([")[0]) not in flat(body):
        problems.append("statement does not quote the pointer line's wording")
    return problems


def site_problems(text, marker):
    try:
        _, rest = fenced_block_after(text, marker)
    except (LookupError, ValueError, StopIteration):
        return [f"site not found by {marker!r}"]
    following = paragraph_after(rest)
    if following != POINTER:
        return [f"line after the block is {following[:120]!r}, not the pointer"]
    return []


def pointer_sweep_problems(files):
    """Every paragraph in the plugin that links the anchor is the pointer, word for word."""
    problems = []
    for path in files:
        for para in re.split(r"\n[ \t]*\n", read(path)):
            if f"#{ANCHOR_ID})" in para and flat(para) != POINTER:
                problems.append(f"{path.name}: {flat(para)[:100]!r}")
    return problems


def schema_step_problems(text):
    problems = []
    try:
        step = between(text, STEP_4, STEP_5)
        container = between(step, CONTAINER_ROUTE, NATIVE_ROUTE)
        native = step[step.index(NATIVE_ROUTE):]
    except ValueError:
        return ["step 4 or its two routes not found"]
    for line in step.splitlines():
        if HOST_OPT_REDIRECT.search(line):
            problems.append(f"redirects from a host /opt/senzing path: {line.strip()!r}")
    block, _ = fenced_block_after(container, "psql")
    code = "\n".join(block)
    if not re.search(r'^\s*<runtime> cp "<sdk-container>:<schema path from MCP>" database/\S+\.sql &&$',
                     code, re.M):
        problems.append("container route does not `<runtime> cp` the MCP path into database/")
    if re.search(r"^\s*docker cp\b", code, re.M):
        problems.append("container route hardcodes `docker cp` (INV-195)")
    if not re.search(r"psql -U senzing -d G2 < database/\S+\.sql$", code, re.M):
        problems.append("container route's psql does not read the project copy")
    if not match_lines(container, r"recorded `runtime` as `<runtime>` \(INV-195\)"):
        problems.append("container route does not dispatch on the recorded runtime")
    if not match_lines(container, r"\(INV-200\)"):
        problems.append("container route does not keep the copy in the project (INV-200)")
    if not match_lines(container, r"A failed copy\s+stops the step"):
        problems.append("container route has no failed-copy rule")
    if not match_lines(step, r"`<schema path from MCP>`.*at runtime \(INV-080\)"):
        problems.append("the path is not taken from MCP at runtime")
    native_block, _ = fenced_block_after(native, "psql")
    if not re.search(r'psql -U senzing -d G2 < "<schema path from MCP>"$', "\n".join(native_block),
                     re.M):
        problems.append("native route no longer applies the host file")
    return problems


def option_2_problems(text):
    """Option 2's "as above" sentence takes the DDL from the SDK container on the container route."""
    try:
        option = between(text, OPTION_2, OPTION_3)
    except ValueError:
        return ["Option 2 not found"]
    problems = []
    for pattern, what in (
            (r"On SDK setup's container route the DDL is taken from the SDK container",
             "does not take the DDL from the SDK container on the container route"),
            (r"as Option 1's container-route command takes it, never from a host path",
             "does not point at Option 1's container-route command, or allows a host path"),
            (r"copy it into `database/` with that command's `<runtime> cp`",
             "does not copy the DDL into database/ with the recorded runtime's cp"),
            (r"apply the copy with `psql -f database/szcore-schema-postgresql-create\.sql`",
             "does not apply the project copy")):
        if not match_lines(option, pattern):
            problems.append(f"Option 2 {what}")
    for line in option.splitlines():
        if HOST_OPT_REDIRECT.search(line) or re.search(r"psql -f \"?/opt/senzing", line):
            problems.append(f"Option 2 reads a host /opt/senzing path: {line.strip()!r}")
    return problems


# --- tests -----------------------------------------------------------------------------------


class GroundRulesHoldTheOneStatement(unittest.TestCase):
    def test_statement_is_present(self):
        self.assertEqual(ground_rules_problems(read(GROUND_RULES)), [])

    def test_negative_control_removing_the_anchor(self):
        self.assertTrue(ground_rules_problems(read(GROUND_RULES).replace(ANCHOR, "")))

    def test_negative_control_dropping_the_hand_run_clause(self):
        text = read(GROUND_RULES).replace("PowerShell 5.1 form that meets the rules above (INV-167)",
                                          "form")
        self.assertTrue(ground_rules_problems(text))

    def test_negative_control_dropping_git_bash(self):
        text = read(GROUND_RULES).replace("which on Windows is Git Bash", "which varies")
        self.assertTrue(ground_rules_problems(text))

    def test_negative_control_anchor_outside_the_section(self):
        text = read(GROUND_RULES).replace(ANCHOR, "")
        text = text.replace("## Markdown files", ANCHOR + "\n\n## Markdown files")
        self.assertTrue(ground_rules_problems(text))


class EverySiteCarriesThePointer(unittest.TestCase):
    def test_pointer_links_the_anchor_and_discloses(self):
        self.assertIn(f"]({LINK})", POINTER)
        self.assertIn(DISCLOSURE, POINTER)

    def test_each_site_is_followed_by_the_pointer(self):
        for label, path, marker in SITES:
            with self.subTest(site=label):
                self.assertEqual(site_problems(read(path), marker), [])

    def test_each_link_resolves_to_the_anchor(self):
        for label, path, _ in SITES:
            with self.subTest(site=label):
                target = (path.parent / LINK.split("#")[0]).resolve()
                self.assertEqual(target, GROUND_RULES.resolve())
                self.assertIn(ANCHOR, read(target))

    def test_six_sites(self):
        self.assertEqual(len(SITES), 6)
        self.assertEqual(sum(read(p).count(POINTER) for p in {PHASE1, CONTRACT, MODULE_2}), 7,
                         "six sites, plus the native schema route beside the container one")

    def test_every_link_to_the_anchor_uses_the_one_wording(self):
        self.assertEqual(pointer_sweep_problems(sorted(SKILLS.rglob("*.md"))), [])

    def test_negative_control_a_site_without_the_pointer(self):
        for label, path, marker in SITES:
            with self.subTest(site=label):
                text = read(path)
                _, rest = fenced_block_after(text, marker)
                head = text[:len(text) - len(rest)]
                stripped = head + rest.replace(POINTER, "", 1)
                self.assertTrue(site_problems(stripped, marker))

    def test_negative_control_a_reworded_pointer(self):
        for label, path, marker in SITES:
            with self.subTest(site=label):
                text = read(path).replace("no test runs it there", "nobody checked")
                self.assertTrue(site_problems(text, marker))

    def test_negative_control_the_sweep_catches_a_drifted_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            drifted = Path(tmp) / "x.md"
            drifted.write_text(f"Runs in Git Bash ([guide-run blocks]({LINK})).\n", encoding="utf-8")
            self.assertTrue(pointer_sweep_problems([drifted]))

    def test_negative_control_a_site_whose_block_is_gone(self):
        self.assertTrue(site_problems(read(MODULE_2), "no such line anywhere in the file"))


class SchemaDdlComesFromTheSdkContainer(unittest.TestCase):
    def test_step_4(self):
        self.assertEqual(schema_step_problems(read(MODULE_2)), [])

    def test_negative_control_the_old_host_redirect(self):
        text = read(MODULE_2).replace(
            "psql -U senzing -d G2 < database/szcore-schema-postgresql-create.sql",
            "psql -U senzing -d G2 < /opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql")
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_hardcoded_docker_cp(self):
        text = read(MODULE_2).replace('<runtime> cp "<sdk-container>:', 'docker cp "<sdk-container>:')
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_a_literal_path(self):
        text = read(MODULE_2).replace(
            '"<sdk-container>:<schema path from MCP>"',
            '"<sdk-container>:/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql"')
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_native_route_removed(self):
        text = read(MODULE_2).replace('< "<schema path from MCP>"', "< schema.sql")
        self.assertTrue(schema_step_problems(text))

    def test_negative_control_copy_outside_the_project(self):
        text = read(MODULE_2).replace("database/szcore-schema-postgresql-create.sql &&",
                                      "/tmp/szcore-schema-postgresql-create.sql &&")
        self.assertTrue(schema_step_problems(text))


class OptionTwoTakesTheDdlFromTheSdkContainer(unittest.TestCase):
    """Option 2 (a local PostgreSQL) applies the DDL "as above"; on the container route it must say
    the DDL comes from the SDK container as Option 1's container-route command takes it (#508)."""

    def test_option_2(self):
        self.assertEqual(option_2_problems(read(MODULE_2)), [])

    def test_negative_control_the_container_route_sentence_removed(self):
        text = read(MODULE_2)
        option = between(text, OPTION_2, OPTION_3)
        cut = option[:option.index("On SDK setup's")].rstrip() + "\n\n"
        self.assertTrue(option_2_problems(text.replace(option, cut)))

    def test_negative_control_a_host_path(self):
        text = read(MODULE_2)
        option = between(text, OPTION_2, OPTION_3)
        hosted = option.replace(
            "psql -f database/szcore-schema-postgresql-create.sql",
            "psql -f /opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql")
        problems = option_2_problems(text.replace(option, hosted))
        self.assertTrue(any("host /opt/senzing" in p for p in problems), problems)

    def test_negative_control_option_2_gone(self):
        self.assertTrue(option_2_problems(read(MODULE_2).replace(OPTION_2, "**Option 2:**")))


def _stub(path, body):
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@unittest.skipUnless(shutil.which("sh") and os.name == "posix",
                     "needs a POSIX sh to run the container-route block against stub runtimes")
class TheContainerRouteBlockRuns(unittest.TestCase):
    """Run step 4's own container-route block, with stub `<runtime>` and `docker`, in a temp project.

    The stub runtime's `cp` reads `<container>:<path>` from a fake container root, so the test
    sees the copy come from the container and land in the project; the stub `docker` records
    what `psql` receives on stdin.
    """

    DDL = "CREATE TABLE sys_cfg (x INT);\n"
    IN_CONTAINER = "/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.project = root / "project"
        (self.project / "database").mkdir(parents=True)
        self.container_root = root / "sdk-container-fs"
        ddl = self.container_root / self.IN_CONTAINER.lstrip("/")
        ddl.parent.mkdir(parents=True)
        ddl.write_text(self.DDL, encoding="utf-8")
        self.bin = root / "bin"
        self.bin.mkdir()
        self.stdin_log = root / "psql-stdin.sql"
        _stub(self.bin / "stubrt",
              'test "$1" = cp || exit 9\n'
              'src="${2#*:}"\n'
              f'cp "{self.container_root}$src" "$3"\n')
        _stub(self.bin / "docker", f'cat > "{self.stdin_log}"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def block(self):
        step = between(read(MODULE_2), STEP_4, STEP_5)
        lines, _ = fenced_block_after(between(step, CONTAINER_ROUTE, NATIVE_ROUTE), "psql")
        code = "\n".join(line.strip() for line in lines)
        return (code.replace("<runtime>", "stubrt")
                    .replace("<sdk-container>", "senzing-bootcamp-demo-1a2b3c")
                    .replace("<schema path from MCP>", self.IN_CONTAINER)
                    .replace("<pg-container>", "bootcamp-postgres-demo-1a2b3c"))

    def run_block(self, code):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}")
        return subprocess.run(["sh", "-c", code], cwd=self.project, env=env,
                              capture_output=True, text=True, timeout=30)

    def test_the_ddl_reaches_psql_from_the_project_copy(self):
        result = self.run_block(self.block())
        self.assertEqual(result.returncode, 0, result.stderr)
        copy = self.project / "database" / "szcore-schema-postgresql-create.sql"
        self.assertEqual(copy.read_text(encoding="utf-8"), self.DDL)
        self.assertEqual(self.stdin_log.read_text(encoding="utf-8"), self.DDL)

    def test_negative_control_a_failed_copy_fails_the_block(self):
        (self.container_root / self.IN_CONTAINER.lstrip("/")).unlink()
        result = self.run_block(self.block())
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.stdin_log.exists(), "psql must not run after a failed copy")

    def test_negative_control_without_the_chain_a_stale_copy_is_applied(self):
        """Why the block chains with `&&`: unchained, a failed copy still applies an older copy."""
        (self.container_root / self.IN_CONTAINER.lstrip("/")).unlink()
        stale = self.project / "database" / "szcore-schema-postgresql-create.sql"
        stale.write_text("-- stale\n", encoding="utf-8")
        result = self.run_block(self.block().replace(" &&\n", "\n"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.stdin_log.read_text(encoding="utf-8"), "-- stale\n")


if __name__ == "__main__":
    unittest.main()
