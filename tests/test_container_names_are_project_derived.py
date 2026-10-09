"""Every container SDK setup creates takes a project-derived name, and no project touches another's.

Issue #461. On a 2026-10-05 run, `docker run --name senzing-bootcamp` failed because a
container of that name already existed from a different bootcamp project on the same machine.
Nothing in Module 2 named a convention: the container route said only "give it a stable
`--name`", and PostgreSQL Option 1 hard-coded `bootcamp-postgres` and host port 5432. The
lifecycle hooks find containers by exact name (`docker_lifecycle._container_state` and
`stop_started_containers`), so with a shared name one project's SessionEnd stops, and its
SessionStart reports, the other project's container. The obvious recovery for the failed
`run`, removing the container in the way, would have destroyed another project's environment.

What these tests pin:

1. **Derivation** (`container-name`): `<base>-<slug>-<hash6>`, deterministic; the slug rules
   (lowercase, runs outside `[a-z0-9_.-]` become `-`, strip `-_.`, truncate to 32, `project`
   when empty); SHA-256 over the normcased real path, so two projects with one basename differ;
   the runtime name charset.
2. **Conflict**: a name held by a container this project does not record moves to `-2` ... `-9`;
   a name this project records is returned unchanged; exhaustion exits non-zero; Apple
   `container` and a missing CLI print the derived name unprobed. ⛔ In every case the only
   container command issued is the read-only `ps` probe: the assertion is an allowlist (every
   command is `ps`), checked non-vacuously (the probe cases issue at least one command), with a
   negative control proving the same predicate flags the hooks' own `stop`.
3. **Port** (`free-port`): the preferred port when it binds, else the first of the next 99; a
   port the test holds bound is skipped; `SO_REUSEADDR` is never set; exhaustion exits non-zero.
4. **Two projects**: each records its derived name, and each project's SessionEnd stops only its
   own container. The negative control replays the old fixed name and shows the collision.
5. **Module 2's text**: no literal `--name senzing-bootcamp`, `--name bootcamp-postgres` or
   `127.0.0.1:5432:5432`, and no container command naming a fixed base; one anchored naming
   rule, which both creation sites link; the never-touch rule stated once; Option 1 records and
   uses `host_port`. Each prose check is run on a copy of the pre-#461 text as its negative
   control.
6. **Import is inert**: importing `docker_lifecycle` (as both hooks do) runs no command.

Every container CLI is stubbed (`FakeCli` from `test_container_lifecycle_runtimes`): the
development machine has a real `docker`, and an unstubbed test could act on real containers.
The one real-world call is a TCP bind on 127.0.0.1, which `free-port` exists to make.

The safety rule is drafted as a DEFERRED INVARIANT in `specs/IMPLEMENTED.md`
(`sdk-setup-container-names-are-project-derived`); it extends INV-101 and INV-195.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import hashlib
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import unittest

from _wrapped_text import match_lines as _match_lines
from test_container_lifecycle_runtimes import FakeCli, SCRIPTS, load_module

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_2 = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills", "module-02-sdk-setup", "SKILL.md")

#: The container subcommands #461 forbids the helper to issue. `destructive()` below is an
#: allowlist rather than a check against this set, so a sibling verb (`restart`, `kill`,
#: `create`) is caught too; the set feeds the negative control.
FORBIDDEN_VERBS = ("rm", "stop", "start", "run")


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` (INV-346), taking a pattern string or a compiled one."""
    return _match_lines(text, re.compile(pattern) if isinstance(pattern, str) else pattern)


def subcommands(commands):
    """The container subcommand of each recorded command (`ps`, `stop`, ...)."""
    return [cmd[1] for cmd in commands if len(cmd) > 1]


def destructive(commands):
    """Every recorded command that is anything other than the read-only `ps` probe."""
    return [cmd for cmd in commands if len(cmd) < 2 or cmd[1] != "ps"]


@contextlib.contextmanager
def project_at(root, containers=()):
    """Make `root` an active bootcamp project with these recorded containers, and cd into it."""
    os.makedirs(os.path.join(root, "config"), exist_ok=True)
    with open(os.path.join(root, "config", "bootcamp_progress.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"current_module": "SDK Setup", "docker_containers": list(containers)}, fh)
    previous = os.getcwd()
    os.chdir(root)
    try:
        yield root
    finally:
        os.chdir(previous)


class TempRoot(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class Derivation(TempRoot):
    def test_the_name_is_base_slug_and_hash6_of_the_normcased_real_path(self):
        project = os.path.join(self.tmp, "Acme Bootcamp")
        os.makedirs(project)
        expected_hash = hashlib.sha256(
            os.path.normcase(os.path.realpath(project)).encode("utf-8")).hexdigest()[:6]
        name = self.mod.derived_container_name("senzing-bootcamp", project)
        self.assertEqual(name, "senzing-bootcamp-acme-bootcamp-%s" % expected_hash)
        self.assertRegex(name, r"\A[a-zA-Z0-9][a-zA-Z0-9_.-]*\Z")

    def test_the_derivation_is_deterministic(self):
        project = os.path.join(self.tmp, "demo")
        os.makedirs(project)
        first = self.mod.derived_container_name("bootcamp-postgres", project)
        self.assertEqual(first, self.mod.derived_container_name("bootcamp-postgres", project))
        with project_at(project):
            self.assertEqual(first, self.mod.derived_container_name("bootcamp-postgres"))

    def test_sanitization(self):
        cases = {
            "My Project (v2)": "my-project-v2",
            "--Data__Set..": "data__set",
            "a/b": "b",
            "x" * 40: "x" * 32,
            "Ünïcode Ñame": "n-code-ame",
            # Strip first, then truncate, as #461 orders it: a cut can end on a `-`.
            "y" * 31 + "-zz": "y" * 31 + "-",
        }
        for basename, slug in cases.items():
            with self.subTest(basename=basename):
                self.assertEqual(self.mod.project_slug(os.path.join(self.tmp, basename)), slug)

    def test_a_basename_that_sanitizes_to_nothing_becomes_project(self):
        for basename in ("___", "!!!", "...", "-_.", "日本語"):
            with self.subTest(basename=basename):
                path = os.path.join(self.tmp, basename)
                self.assertEqual(self.mod.project_slug(path), "project")
                self.assertRegex(self.mod.derived_container_name("senzing-bootcamp", path),
                                 r"\Asenzing-bootcamp-project-[0-9a-f]{6}\Z")

    def test_two_directories_with_one_basename_get_different_names(self):
        first = os.path.join(self.tmp, "one", "bootcamp")
        second = os.path.join(self.tmp, "two", "bootcamp")
        os.makedirs(first)
        os.makedirs(second)
        self.assertEqual(self.mod.project_slug(first), self.mod.project_slug(second))
        self.assertNotEqual(self.mod.derived_container_name("senzing-bootcamp", first),
                            self.mod.derived_container_name("senzing-bootcamp", second))

    def test_a_base_outside_the_runtime_charset_is_refused(self):
        for base in ("", "-leading", "has space", "slash/name"):
            with self.subTest(base=base):
                with self.assertRaises(ValueError):
                    self.mod.derived_container_name(base, self.tmp)


class ConflictProbe(TempRoot):
    """The probe reuses `_container_state`; FakeCli answers `ps` from `states`."""

    def setUp(self):
        super().setUp()
        self.project = os.path.join(self.tmp, "demo")
        os.makedirs(self.project)
        self.derived = self.mod.derived_container_name("senzing-bootcamp", self.project)

    def choose(self, recorded=(), present=("docker",), states=None, runtime="docker"):
        with project_at(self.project, recorded), FakeCli(
                self.mod, present=present, states=states or {}) as cli:
            name, how = self.mod.container_name("senzing-bootcamp", runtime)
        return name, how, cli.commands

    def test_a_free_name_is_the_derived_name(self):
        name, how, commands = self.choose()
        self.assertEqual((name, how), (self.derived, "free"))
        self.assertEqual(subcommands(commands), ["ps"])
        self.assertEqual(destructive(commands), [])

    def test_a_conflict_yields_dash_2_and_no_destructive_command(self):
        name, how, commands = self.choose(states={self.derived: "running"})
        self.assertEqual((name, how), (self.derived + "-2", "free"))
        self.assertTrue(commands, "the probe must actually run, or 'no rm/stop' is vacuous")
        self.assertEqual(subcommands(commands), ["ps", "ps"])
        self.assertEqual(destructive(commands), [])

    def test_a_stopped_container_of_that_name_is_a_conflict_too(self):
        name, _, commands = self.choose(states={self.derived: "exited"})
        self.assertEqual(name, self.derived + "-2")
        self.assertEqual(destructive(commands), [])

    def test_each_taken_suffix_is_skipped_in_order(self):
        states = {self.derived: "running", self.derived + "-2": "exited"}
        name, _, commands = self.choose(states=states)
        self.assertEqual(name, self.derived + "-3")
        self.assertEqual(destructive(commands), [])

    def test_a_name_this_project_recorded_is_returned_unchanged(self):
        recorded = [{"name": self.derived, "runtime": "docker"}]
        name, how, commands = self.choose(recorded=recorded,
                                          states={self.derived: "running"})
        self.assertEqual((name, how), (self.derived, "recorded"))
        self.assertEqual(destructive(commands), [])

    def test_a_recorded_suffix_is_this_projects_own_and_is_returned(self):
        """This project took `-2` earlier because another project held the base name."""
        recorded = [{"name": self.derived + "-2", "runtime": "docker"}]
        states = {self.derived: "running", self.derived + "-2": "exited"}
        name, how, commands = self.choose(recorded=recorded, states=states)
        self.assertEqual((name, how), (self.derived + "-2", "recorded"))
        self.assertEqual(destructive(commands), [])

    def test_all_suffixes_taken_is_exhaustion_with_no_destructive_command(self):
        states = {self.derived: "running"}
        states.update({"%s-%d" % (self.derived, n): "running" for n in range(2, 10)})
        name, how, commands = self.choose(states=states)
        self.assertEqual((name, how), (None, "exhausted"))
        self.assertEqual(subcommands(commands), ["ps"] * 9)
        self.assertEqual(destructive(commands), [])

    def test_the_cli_exits_non_zero_on_exhaustion_and_prints_no_name(self):
        states = {self.derived: "running"}
        states.update({"%s-%d" % (self.derived, n): "running" for n in range(2, 10)})
        out, err = io.StringIO(), io.StringIO()
        with project_at(self.project), FakeCli(self.mod, present=["docker"], states=states) as cli, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.mod.main(["container-name", "senzing-bootcamp"])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("Ask the Bootcamper", err.getvalue())
        self.assertEqual(destructive(cli.commands), [])

    def test_podman_probes_with_podman(self):
        name, _, commands = self.choose(present=("podman",), runtime="podman",
                                        states={self.derived: "running"})
        self.assertEqual(name, self.derived + "-2")
        self.assertEqual({os.path.basename(c[0]) for c in commands}, {"podman"})
        self.assertEqual(destructive(commands), [])

    def test_apple_container_prints_the_derived_name_unprobed(self):
        name, how, commands = self.choose(present=("container",), runtime="container")
        self.assertEqual((name, how), (self.derived, "unprobed"))
        self.assertEqual(commands, [])

    def test_a_missing_cli_warns_and_prints_the_derived_name(self):
        out, err = io.StringIO(), io.StringIO()
        with project_at(self.project), FakeCli(self.mod, present=()) as cli, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.mod.main(["container-name", "senzing-bootcamp"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), self.derived)
        self.assertIn("could not check", err.getvalue())
        self.assertEqual(cli.commands, [])

    def test_negative_control_the_predicate_flags_the_hooks_stop(self):
        """`destructive()` must fire on a real destructive call, or its silence proves nothing."""
        with project_at(self.project, [{"name": self.derived, "runtime": "docker"}]), \
                FakeCli(self.mod, present=["docker"]) as cli:
            self.mod.stop_started_containers()
        self.assertEqual(destructive(cli.commands),
                         [["/usr/bin/docker", "stop", self.derived]])
        for verb in FORBIDDEN_VERBS + ("restart", "kill", "create"):
            with self.subTest(verb=verb):
                self.assertTrue(destructive([["/usr/bin/docker", verb, "x"]]))


class FreePort(TempRoot):
    def stub_bind(self, free):
        tried = []

        def can_bind(port, host="127.0.0.1"):
            tried.append(port)
            return port in free

        real = self.mod._can_bind
        self.mod._can_bind = can_bind
        self.addCleanup(setattr, self.mod, "_can_bind", real)
        return tried

    def test_the_preferred_port_when_it_binds(self):
        self.stub_bind({5432, 5433})
        self.assertEqual(self.mod.free_port(5432), 5432)

    def test_the_first_free_port_in_5433_to_5531(self):
        tried = self.stub_bind({5440, 5450})
        self.assertEqual(self.mod.free_port(5432), 5440)
        self.assertEqual(tried, list(range(5432, 5441)))

    def test_no_free_port_is_none_after_trying_exactly_5432_to_5531(self):
        tried = self.stub_bind(set())
        self.assertIsNone(self.mod.free_port(5432))
        self.assertEqual(tried, list(range(5432, 5532)))

    def test_the_cli_exits_non_zero_when_no_port_is_free(self):
        self.stub_bind(set())
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.mod.main(["free-port", "5432"])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("5432 to 5531", err.getvalue())

    def test_the_cli_refuses_a_port_out_of_range(self):
        for bad in ("0", "65536", "http"):
            with self.subTest(port=bad), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    self.mod.main(["free-port", bad])

    def test_a_port_the_test_holds_bound_is_skipped(self):
        held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(held.close)
        held.bind(("127.0.0.1", 0))
        held.listen(1)
        port = held.getsockname()[1]
        if port + 99 > 65535:
            self.skipTest("ephemeral port %d leaves no range above it" % port)
        found = self.mod.free_port(port)
        self.assertIsNotNone(found)
        self.assertNotEqual(found, port)
        self.assertTrue(port < found <= port + 99, found)

    def test_so_reuseaddr_is_never_set(self):
        calls = []

        class RecordingSocket:
            def __init__(self, *args):
                calls.append(("socket", args))

            def setsockopt(self, *args):
                calls.append(("setsockopt", args))

            def bind(self, address):
                calls.append(("bind", address))

            def close(self):
                calls.append(("close",))

        real = self.mod.socket.socket
        self.mod.socket.socket = RecordingSocket
        self.addCleanup(setattr, self.mod.socket, "socket", real)
        self.assertTrue(self.mod._can_bind(5432))
        self.assertIn(("bind", ("127.0.0.1", 5432)), calls)
        self.assertEqual([c for c in calls if c[0] == "setsockopt"], [])


class TwoProjectsOnOneMachine(TempRoot):
    """Each project's SessionEnd stops only its own container (what `session-end.py` calls)."""

    def two_projects(self):
        first = os.path.join(self.tmp, "alice", "bootcamp")
        second = os.path.join(self.tmp, "bob", "bootcamp")
        os.makedirs(first)
        os.makedirs(second)
        return first, second

    def session_end(self, project, recorded):
        with project_at(project, recorded), FakeCli(self.mod, present=["docker"]) as cli:
            stopped = self.mod.stop_started_containers()
        return stopped, cli.commands

    def test_each_projects_session_end_stops_only_its_own_container(self):
        first, second = self.two_projects()
        names = {}
        for project in (first, second):
            with project_at(project), FakeCli(self.mod, present=["docker"]):
                names[project], how = self.mod.container_name("senzing-bootcamp")
            self.assertEqual(how, "free")
        self.assertNotEqual(names[first], names[second])
        for own, other in ((first, second), (second, first)):
            with self.subTest(project=own):
                stopped, commands = self.session_end(
                    own, [{"name": names[own], "runtime": "docker"}])
                self.assertEqual(stopped, [names[own]])
                self.assertEqual(commands, [["/usr/bin/docker", "stop", names[own]]])
                self.assertNotIn(names[other], [part for c in commands for part in c])

    def test_negative_control_a_fixed_name_stops_the_other_projects_container(self):
        """The pre-#461 behavior: both projects record `senzing-bootcamp`, so A's SessionEnd
        stops the container B is using. If this stopped failing to collide, the test above
        would no longer prove anything."""
        first, second = self.two_projects()
        fixed = [{"name": "senzing-bootcamp", "runtime": "docker"}]
        _, commands_a = self.session_end(first, fixed)
        with project_at(second, fixed):
            b_names = [c["name"] for c in self.mod.tracked_containers()]
        self.assertIn(commands_a[0][2], b_names)


class ImportIsInert(unittest.TestCase):
    def test_importing_the_module_runs_no_command_and_prints_nothing(self):
        probe = (
            "import subprocess, sys\n"
            "calls = []\n"
            "subprocess.run = lambda *a, **k: calls.append(a)\n"
            "sys.path.insert(0, %r)\n"
            "import docker_lifecycle\n"
            "sys.stdout.write('calls=%%d' %% len(calls))\n" % SCRIPTS)
        result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True,
                                timeout=60, cwd=REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "calls=0")
        self.assertEqual(result.stderr, "")


#: The pre-#461 text of both creation sites, verbatim, for the negative controls below.
PRE_461 = """- **Record the container for lifecycle tracking (INV-101).** When you start the container,
  give it a stable `--name` and append an entry to a `docker_containers` list in
  `config/bootcamp_progress.json` — at least its `name` and the `runtime` you actually used

   ```bash
   docker run -d --name bootcamp-postgres \\
     -e POSTGRES_USER=senzing -e POSTGRES_PASSWORD=<generated-password> -e POSTGRES_DB=G2 \\
     -p 127.0.0.1:5432:5432 -v "$(pwd)/database/postgres:/var/lib/postgresql/data" postgres:16
   ```

   On a later resume, restart the existing container with `docker start bootcamp-postgres` (which
   preserves the baked-in password) rather than a fresh `docker run`.

3. Wait until the server is ready (poll `docker exec bootcamp-postgres pg_isready`).

   docker run -d --name senzing-bootcamp -it -v "$(pwd)":/app -w /app debian:bookworm-slim bash
"""

#: Literals #461 names, which must not survive in Module 2.
FORBIDDEN_LITERALS = ("--name senzing-bootcamp", "--name bootcamp-postgres", "127.0.0.1:5432:5432")

#: A container command that names a fixed base rather than the helper's printed name. Read on
#: whitespace-collapsed blocks (INV-346), and kept inside one code span by `[^`]`.
LITERAL_COMMAND = re.compile(
    r"\b(?:docker|podman|container)\s+(?:run|start|stop|exec|rm|restart|kill)\b[^`]*?"
    r"(?<![\w<-])(?:senzing-bootcamp|bootcamp-postgres)(?![\w-])")

NEVER_TOUCH = re.compile(
    r"Never remove, stop, start or reuse a container that this project's `docker_containers` "
    r"does not record")


def forbidden_literals(text):
    return [(lit, match_lines(text, re.escape(lit))) for lit in FORBIDDEN_LITERALS
            if match_lines(text, re.escape(lit))]


class Module2CreatesOnlyHelperNamedContainers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MODULE_2, encoding="utf-8") as fh:
            cls.text = fh.read()
        start = cls.text.index("**Option 1 — PostgreSQL in a Docker container:**")
        cls.option_1 = cls.text[start:cls.text.index("**Option 2", start)]
        route = cls.text.index("For the `docker` path")
        cls.anchor = cls.text.index('<a id="container-naming"></a>')
        cls.route = cls.text[route:cls.anchor]
        cls.rule = cls.text[cls.anchor:cls.text.index("**Phase 3", cls.anchor)]

    def test_no_forbidden_literal_remains(self):
        self.assertEqual(forbidden_literals(self.text), [])

    def test_no_container_command_names_a_fixed_base(self):
        self.assertEqual(match_lines(self.text, LITERAL_COMMAND), [])

    def test_negative_control_the_pre_461_text_is_caught(self):
        self.assertEqual([lit for lit, _ in forbidden_literals(PRE_461)],
                         list(FORBIDDEN_LITERALS))
        self.assertEqual(len(match_lines(PRE_461, LITERAL_COMMAND)), 4)
        self.assertEqual(match_lines(PRE_461, r"\(#container-naming\)"), [])

    def test_one_anchored_naming_rule_that_calls_the_helper(self):
        self.assertEqual(self.text.count('<a id="container-naming"></a>'), 1)
        self.assertTrue(match_lines(self.rule, r"This is the canonical statement"))
        self.assertTrue(match_lines(
            self.rule, r'scripts/docker_lifecycle\.py" container-name <base> --runtime <runtime>'))
        for clause in (r"-2` … `-9", r"Apple `container`", r"stop and ask the Bootcamper",
                       r"`host_port`"):
            with self.subTest(clause=clause):
                self.assertTrue(match_lines(self.rule, clause), clause)

    def test_both_creation_sites_link_the_rule(self):
        self.assertTrue(match_lines(self.route, r"\(#container-naming\)"))
        self.assertTrue(match_lines(self.route, r"base `senzing-bootcamp`"))
        self.assertTrue(match_lines(self.option_1, r"\(#container-naming\)"))

    def test_the_never_touch_rule_is_stated_once_in_the_rule(self):
        self.assertEqual(len(match_lines(self.text, NEVER_TOUCH)), 1)
        self.assertEqual(len(match_lines(self.rule, NEVER_TOUCH)), 1)
        self.assertEqual(match_lines(self.option_1, r"[Nn]ever remove"), [])

    def test_option_1_takes_its_name_and_port_from_the_helper(self):
        for pattern in (
                r'docker_lifecycle\.py" container-name bootcamp-postgres --runtime docker',
                r'docker_lifecycle\.py" free-port 5432',
                r"docker run -d --name <pg-container>",
                r"-p 127\.0\.0\.1:<host_port>:5432",
                r"docker start <pg-container>",
                r"docker exec <pg-container> pg_isready",
                r"docker exec -i <pg-container> psql"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(self.option_1, pattern), pattern)

    def test_option_1_records_host_port_and_uses_it_in_sql_connection(self):
        self.assertTrue(match_lines(self.option_1, r"and `host_port` \(`<host_port>`\)"))
        self.assertTrue(match_lines(
            self.option_1,
            r"`SQL\.CONNECTION` URL is `postgresql://user:password@host:port/database`.*"
            r"`port` is the container's recorded `host_port`"))


if __name__ == "__main__":
    unittest.main()
