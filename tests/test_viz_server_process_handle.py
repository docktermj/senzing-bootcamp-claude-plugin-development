"""A module that starts a visualization server must be able to name the process it started.

Truth Set visualization started a background server in Phase 1 and terminated it in Phase 2,
and nothing in between recorded *which process*. The port was recorded (INV-172); the pid was
not. With no handle, the obvious identification is a command-line match:

    pkill -f senzing_viz_server.py

which matches the **matching command's own** command line and so signals the invoking shell.
On a dry run (2026-08-13) that killed the shell with exit code 144 part-way through teardown,
leaving the Truth Set records loaded and the purge — explicitly the last, irreversible action
of the module — unrun. The failure presented as the purge crashing.

A name-based match is also wrong in principle here: the server is built in the Bootcamper's
chosen language (INV-090/INV-002), so in the general case there is no script name to match.
The handle must be the process id.

So this file asserts the contract states the rule as **behavior** (not as a Python detail),
that both modules that start a server carry it, and that no shipped instruction teaches the
command-line match except to forbid it.

Enforces **INV-223** — a module starting a background server records its pid beside its port and terminates by pid, never by a command-line match.

#890 added the launch confirmation: right after the ready line, the port's listener is looked up
and replaces the captured pid when it differs, stated once in the contract with a POSIX, a
PowerShell and a docker-route form, and linked from both launch sites. It also widened the ban
to `pgrep -f` and `ps | grep`. Its wording is INV-223's dated note of 2026-11-10,
registered by the maintainer on 2026-11-10.

Source spec: `specs/visualization-server-teardown-does-not-record-a-pid.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M3B = SKILLS / "module-03b-truthset-visualization"
CONTRACT = M3B / "visualization-api-reference.md"
PHASE1 = M3B / "phase1-visualization.md"
PHASE2 = M3B / "phase2-close.md"
M7_PHASE1 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    """Whitespace-collapsed, so an assertion survives a re-wrap of the paragraph."""
    return re.sub(r"\s+", " ", text)


class TheScanIsNotVacuous(unittest.TestCase):
    def test_every_file_this_guard_reads_exists(self):
        for path in (CONTRACT, PHASE1, PHASE2, M7_PHASE1):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path.relative_to(REPO_ROOT))


class TheContractOwnsTheRule(unittest.TestCase):
    """One statement, in the file every language builds from (INV-090)."""

    def setUp(self):
        self.text = read(CONTRACT)
        self.flat = squash(self.text)

    def test_it_lives_under_server_lifetime(self):
        lifetime = self.text.find("## Server lifetime")
        section = self.text.find("### Identifying the server process")
        self.assertNotEqual(-1, lifetime, "the Server lifetime section moved")
        self.assertNotEqual(-1, section,
                            "the contract does not carry an 'Identifying the server process' "
                            "section — the pid rule has no home that every module reads")
        self.assertGreater(section, lifetime,
                           "the process-handle rule must sit inside Server lifetime, which is "
                           "the section modules are required to honor")

    def test_the_pid_is_captured_at_launch_and_recorded_with_the_port(self):
        self.assertRegex(self.flat, r"(?i)capture the server's process id at launch")
        self.assertRegex(self.flat, r"(?i)record the pid in the same checkpoint")

    def test_both_platform_handles_are_named(self):
        """INV-001: Linux, macOS and Windows. A POSIX-only rule strands Windows."""
        self.assertIn("`$!`", self.flat, "the POSIX handle ($!) is not named")
        self.assertIn("$proc.Id", self.flat, "the PowerShell handle ($proc.Id) is not named")
        self.assertIn("-PassThru", self.flat,
                      "PowerShell's Start-Process needs -PassThru to yield a process object")

    def test_the_command_line_match_is_forbidden_with_its_reason(self):
        self.assertRegex(
            self.flat, r"(?i)never identify the server by matching its command line",
            "the contract does not forbid the command-line match")
        self.assertRegex(
            self.flat, r"(?i)appears in the \*?matching command's own\*? command line",
            "the ban is stated without the reason it exists — the reason is the whole "
            "value, since the failure does not look like a wrong kill target")

    def test_the_fallback_is_the_port_not_the_name(self):
        self.assertIn("lsof -ti:", self.flat, "the POSIX port-based fallback is not named")
        self.assertIn("Get-NetTCPConnection", self.flat,
                      "the PowerShell port-based fallback is not named")

    def test_the_exit_condition_is_the_port_being_free(self):
        self.assertRegex(self.flat, r"(?i)confirm the port is free")
        self.assertRegex(
            self.flat, r"(?i)rather than waiting a fixed interval|a sleep asserts nothing",
            "waiting is not the same as verifying; the contract must say which one is "
            "required or the 5-second wait reads as sufficient")

    def test_the_rule_is_behavior_not_a_python_identifier(self):
        """INV-002/INV-090: a requirement expressed only as a Python name never reaches a
        Java, C#, Rust or TypeScript bootcamp.

        The one permitted mention of the reference server's filename is inside the
        prohibition, where it is the recorded evidence for what went wrong."""
        start = self.text.find("### Identifying the server process")
        end = self.text.find("\n**The teardown gate.**", start)
        section = self.text[start:end if end != -1 else len(self.text)]
        without_evidence = re.sub(r"pkill\s+-f\s+senzing_viz_server\.py", "", squash(section))
        self.assertNotIn(
            "senzing_viz_server.py", without_evidence,
            "the rule leans on the Python reference server's filename outside the "
            "prohibition, so a non-Python bootcamp receives a rule it cannot apply")
        self.assertIn(
            "chosen language (INV-090)", without_evidence,
            "the section does not say why a script name is the wrong handle in general")


class Module03bCarriesIt(unittest.TestCase):
    def test_phase1_captures_the_pid_at_launch(self):
        text = read(PHASE1)
        self.assertRegex(squash(text), r"(?i)record the process id along with the port",
                         "2.3 starts the server without recording its pid")
        self.assertIn("VIZ_PID=$!", text,
                      "the start command does not show the handle being captured")

    def test_phase1_checkpoints_the_pid_beside_the_port(self):
        text = read(PHASE1)
        self.assertRegex(
            text, r'"web_service":\s*\{[^}]*"pid"',
            "the web_service checkpoint records no pid — the field the teardown reads")

    def test_phase2_terminates_by_the_recorded_pid(self):
        flat = squash(read(PHASE2))
        self.assertRegex(flat, r"(?i)pid recorded in Phase 1",
                         "teardown does not name the recorded pid as its target")
        self.assertIn("truthset_visualization.checks.web_service.pid", flat,
                      "teardown does not say where the pid is read from")

    def test_phase2_documents_the_port_fallback(self):
        flat = squash(read(PHASE2))
        self.assertIn("lsof -ti:", flat, "no POSIX fallback for a missing pid")
        self.assertIn("Get-NetTCPConnection", flat, "no Windows fallback for a missing pid")

    def test_phase2_names_the_unsafe_match_and_why(self):
        flat = squash(read(PHASE2))
        self.assertRegex(flat, r"(?i)never `?pkill -f",
                         "teardown does not warn against the command-line match")
        self.assertRegex(
            flat, r"(?i)signals the invoking shell",
            "the warning omits its reason; 'pkill -f is unsafe' without the mechanism "
            "reads as style advice")

    def test_the_purge_waits_on_a_confirmed_free_port(self):
        """The purge is irreversible and order-sensitive; it must not run on an assumption."""
        flat = squash(read(PHASE2))
        self.assertRegex(flat, r"(?i)confirm the port is free",
                         "teardown asserts nothing about whether the server actually stopped")
        self.assertRegex(
            flat, r"(?i)do not start step 4 until the port is confirmed free",
            "nothing orders the purge after a verified teardown")


class Module07CarriesIt(unittest.TestCase):
    """Same server, re-pointed at the bootcamper's data — same failure available."""

    def test_it_states_the_pid_rule(self):
        flat = squash(read(M7_PHASE1))
        self.assertRegex(flat, r"(?i)stop it by the pid captured when it was started",
                         "module 7 stops its server with no handle rule")
        self.assertIn("$proc.Id", flat, "module 7 omits the Windows handle")

    def test_it_checkpoints_the_pid_and_port(self):
        flat = squash(read(M7_PHASE1))
        self.assertRegex(
            flat, r"recording `m7_visualizations`[^.]*?\bpid\b",
            "the m7_visualizations checkpoint instruction records no pid")
        self.assertRegex(
            flat, r'"port": <port>, "pid": <pid>',
            "the m7_visualizations example shows neither the port nor the pid to fall "
            "back to")


class NoInstructionTeachesTheUnsafeMatch(unittest.TestCase):
    """A ban in one file is undone by a recipe in another.

    #890 widened the scan from `pkill` to the lookups that fail the same way: `pgrep -f` and
    `ps | grep` return the wrapping shell's pid as readily as the server's. A retrospective
    recorded exactly that: `pgrep -f` matched the `bash -c` wrapping the launch, the
    checkpoint got the wrapper's pid, and teardown's kill reported success while the server
    kept its port."""

    #: Words that make an occurrence a prohibition rather than an instruction.
    FORBIDDING = re.compile(r"(?i)never|⛔|unsafe|do not|must not")

    #: Every command-line match the rule forbids.
    COMMAND_LINE_MATCH = re.compile(r"pkill|pgrep|\bps\b[^`\n|]{0,12}\|\s*grep")

    @classmethod
    def unforbidden(cls, text):
        """Line numbers of command-line matches with nothing in the 400 characters before
        them forbidding it."""
        found = []
        for match in cls.COMMAND_LINE_MATCH.finditer(text):
            window = text[max(0, match.start() - 400):match.start()]
            if not cls.FORBIDDING.search(window):
                found.append((text[:match.start()].count("\n") + 1, match.group(0)))
        return found

    def test_every_pkill_mention_is_a_prohibition(self):
        for path in sorted(SKILLS.rglob("*.md")):
            with self.subTest(file=path.name):
                self.assertEqual(
                    [], self.unforbidden(read(path)),
                    "%s mentions a command-line match (pkill, pgrep, ps | grep) with nothing "
                    "nearby forbidding it — the match finds the invoking shell, not the server"
                    % path.relative_to(REPO_ROOT))

    def test_pgrep_is_named_wherever_pkill_is(self):
        """The canonical rule and both close sites name the lookup beside the kill."""
        for path in (CONTRACT, PHASE2, M7_PHASE1):
            with self.subTest(file=path.name):
                flat = squash(read(path))
                self.assertIn("pgrep -f", flat, "%s names pkill but not pgrep -f" % path.name)
                self.assertIn("ps | grep", flat, "%s does not name ps | grep" % path.name)

    def test_the_scan_catches_an_unforbidden_mention(self):
        """Negative control: a recipe teaching each match is reported, a ban is not."""
        for recipe in ("Find the pid with `pgrep -f results_server`.",
                       "Find the pid with `ps aux | grep results_server`.",
                       "Stop it with `pkill -f results_server`."):
            with self.subTest(recipe=recipe):
                self.assertTrue(self.unforbidden("Start the server.\n\n" + recipe),
                                "the scan missed a recipe: %r" % recipe)
        self.assertEqual([], self.unforbidden("Never use `pgrep -f` to find the pid."))


#: The docker-route form, which sits indented inside a list item.
DOCKER_FORM = re.compile(r"```bash\n( *<runtime> exec <container> python3 -c '\n.*?)```", re.S)

#: What the canonical launch confirmation must carry, as (description, pattern) pairs.
CONFIRMATION_PARTS = (
    ("anchor", r'<a id="launch-confirmation"></a>'),
    ("after the ready line", r"(?i)once the server prints its ready line"),
    ("the POSIX lsof form", r"lsof -ti:<port> -sTCP:LISTEN"),
    ("the Linux ss form", r"ss -ltnp 'sport = :<port>'"),
    ("the PowerShell form",
     r"Get-NetTCPConnection -LocalPort <port> -State Listen \| "
     r"Select-Object -ExpandProperty OwningProcess"),
    ("the docker /proc form", r"/proc/net/tcp6?.{0,200}socket:\[<inode>\]"),
    ("the container-namespace pid", r"(?i)\*\*container-namespace\*\*\s+pid"),
    ("a different listener replaces the pid",
     r"(?i)exactly one listener, and it is a different pid:\*\* record the listener's pid"),
    ("several, none or no tool keeps the pid and never blocks",
     r"(?i)several listeners, none, or no lookup tool.{0,160}keep the captured pid.{0,60}"
     r"never block the launch"),
    ("the host background-task handle", r"(?i)background-task mechanism is not a pid"),
)


def confirmation_section(text):
    """From the launch-confirmation anchor to the command-line ban that follows it."""
    start = text.find('<a id="launch-confirmation"></a>')
    if start == -1:
        return ""
    end = text.find("Never identify the server by matching its command line", start)
    return text[start:end if end != -1 else len(text)]


def missing_confirmation_parts(text):
    section = squash(confirmation_section(text))
    return [name for name, pattern in CONFIRMATION_PARTS if not re.search(pattern, section)]


class TheLaunchConfirmationIsStatedOnce(unittest.TestCase):
    """#890: the pid recorded at launch is checked against the port's listener right after the
    ready line, while the checkpoint can still be corrected, rather than found wrong at
    teardown (INV-223, INV-001, INV-300)."""

    def setUp(self):
        self.text = read(CONTRACT)

    def test_it_sits_inside_identifying_the_server_process(self):
        section = self.text.find("### Identifying the server process")
        anchor = self.text.find('<a id="launch-confirmation"></a>')
        self.assertNotEqual(-1, anchor, "the launch confirmation has no anchor to link to")
        self.assertGreater(anchor, section,
                           "the launch confirmation sits outside 'Identifying the server "
                           "process'")

    def test_it_carries_every_form_and_outcome(self):
        self.assertEqual([], missing_confirmation_parts(self.text))

    def test_a_dropped_part_is_reported(self):
        """Negative control: each part's absence is caught."""
        section = confirmation_section(self.text)
        mutants = {
            "the PowerShell form": section.replace("-State Listen", ""),
            "the Linux ss form": section.replace("ss -ltnp", "ss"),
            "the host background-task handle": section.replace("is not a pid", "is a pid"),
        }
        for name, mutant in mutants.items():
            with self.subTest(part=name):
                self.assertIn(name, missing_confirmation_parts(mutant))

    def test_the_forms_are_stated_nowhere_else(self):
        """INV-300: the sites link here; a second copy of a form would drift."""
        forms = ("-sTCP:LISTEN", "ss -ltnp", "-State Listen", "/proc/net/tcp")
        for path in sorted(SKILLS.rglob("*.md")):
            if path == CONTRACT:
                continue
            text = read(path)
            for form in forms:
                with self.subTest(file=path.name, form=form):
                    self.assertNotIn(form, text,
                                     "%s restates the launch confirmation's %s form instead "
                                     "of linking to it" % (path.name, form))

    def test_the_docker_form_is_valid_python(self):
        blocks = DOCKER_FORM.findall(self.text)
        self.assertEqual(1, len(blocks), "the docker-route python3 form is not one bash block")
        compile(self.snippet(blocks[0]), "docker-form", "exec")

    @staticmethod
    def snippet(block):
        body = textwrap.dedent(block).split("python3 -c '\n", 1)[1]
        return body[:body.rindex("'")]

    @unittest.skipUnless(Path("/proc/net/tcp").exists(), "needs Linux /proc")
    def test_the_docker_form_names_the_listening_pid(self):
        """Run the shipped snippet against a socket this test holds open: it must name this
        process, and name nothing for a port with no listener. No server is started."""
        import os
        import socket
        import subprocess
        import sys
        code = self.snippet(DOCKER_FORM.findall(self.text)[0])
        self.assertIn("port = 8080", code, "the snippet's port line changed shape")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            found = subprocess.run(
                [sys.executable, "-c", code.replace("port = 8080", "port = %d" % port)],
                capture_output=True, text=True, timeout=60, check=True).stdout.split()
            self.assertEqual([str(os.getpid())], found,
                             "the snippet did not name the process holding the listener")
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            free = probe.getsockname()[1]
        found = subprocess.run(
            [sys.executable, "-c", code.replace("port = 8080", "port = %d" % free)],
            capture_output=True, text=True, timeout=60, check=True).stdout.split()
        self.assertEqual([], found, "the snippet named a pid for a port nobody listens on")


LINK = "visualization-api-reference.md#launch-confirmation"


def links_the_confirmation(text):
    return LINK in text


class TheLaunchSitesLinkToIt(unittest.TestCase):
    def test_both_launch_sites_link_to_it(self):
        for path in (PHASE1, M7_PHASE1):
            with self.subTest(file=path.name):
                self.assertTrue(links_the_confirmation(read(path)),
                                "%s does not link the launch confirmation" % path.name)

    def test_the_container_route_runs_the_docker_form(self):
        self.assertRegex(squash(read(CONTRACT)),
                         r"\[launch confirmation\]\(#launch-confirmation\)'s `docker` form",
                         "'Serving from the SDK container' does not run the docker form")

    def test_a_missing_link_is_reported(self):
        """Negative control."""
        self.assertFalse(links_the_confirmation(read(PHASE1).replace(LINK, "")))

    def test_step_3c_states_the_launch_shape(self):
        blocks = [b for b in re.findall(r"```bash\n(.*?)```", read(M7_PHASE1), re.S)
                  if "$!" in b]
        self.assertEqual(1, len(blocks), "step 3c does not show one launch block reading $!")
        lines = [line.strip() for line in blocks[0].strip().splitlines()]
        self.assertEqual(3, len(lines), "the launch block is not source, launch, read: %r" % lines)
        self.assertRegex(lines[0], r"^\. src/scripts/senzing-env\.sh$",
                         "the env is not sourced as its own statement")
        self.assertTrue(lines[1].endswith(" &") and "&&" not in lines[1],
                        "the server is not the sole backgrounded command on its line")
        self.assertEqual("VIZ_PID=$!", lines[2], "$! is not read on the next line")


if __name__ == "__main__":
    unittest.main()
