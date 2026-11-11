"""The write-gate's Bash branch: a shell write into system temp or Downloads is blocked (#876).

On 2026-11-06 an `/auto-test` walk saw the guide run
`curl -fsSL -o /tmp/rds_register.py https://mcp.senzing.com/examples/…` while repairing the SDK
path in Data Processing. `write-gate.py` was registered for `Write|Edit` only, so no hook saw
the command, and "Working examples" in `ground-rules.md` said to fetch a file without saying
where to save it.

This enforces INV-200's 2026-11-06 note (#876, registered by the maintainer 2026-11-10). It runs the
hook against command strings; it cannot establish what a live guide's shell actually writes.

The Bash branch is deliberately narrower than the Write/Edit one (the issue's Scope):

* it blocks only a **top-level output target** that resolves to system temp or Downloads
  **outside the project**, with the Write/Edit path's `LOC_MSG`; a target elsewhere outside
  the project (`/opt/senzing`, `~/.cargo`) is allowed, because installers write there;
* the forms it reads are `curl -o/--output/--output-dir`, `wget -O/-P`, `>`/`>>` (with a
  descriptor, `2>`), `tee`, and the destination of `cp`/`mv`;
* a quoted payload (`sh -c '...'`, `docker exec ... bash -c '...'`) is one word and is not
  parsed again, which is what leaves Module 2's in-container install rows unblocked;
* an unparseable command is allowed, and the secret check (INV-109) does not run on Bash.

Each blocking case asserts the MESSAGE as well as the exit code, as `test_write_gate.py`
explains: `LOC_MSG` is the only message the Bash branch emits, so a block carrying any other
text came from the Write/Edit path the payload should never have reached.

`write-gate.py` reads stdin at import time, so each case runs it as a subprocess, as
`test_write_gate.py` does. Stdlib only (INV-108).

Source issue: #876.

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
GATE = os.path.join(PLUGIN, "scripts", "write-gate.py")
HOOKS_JSON = os.path.join(PLUGIN, "hooks", "hooks.json")
HOOKS_README = os.path.join(PLUGIN, "hooks", "README.md")
GROUND_RULES = os.path.join(PLUGIN, "skills", "bootcamp-onboarding", "ground-rules.md")
MODULE_2 = os.path.join(PLUGIN, "skills", "module-02-sdk-setup", "SKILL.md")

ALLOW, BLOCK = 0, 2
TEMP_MSG = "system temp or Downloads"      # a substring of LOC_MSG, as test_write_gate.py
INCIDENT = "curl -fsSL -o /tmp/rds_register.py https://mcp.senzing.com/examples/…"
URL = "https://mcp.senzing.com/examples/x.py"


def make_project(parent=None):
    proj = tempfile.mkdtemp(dir=parent, prefix="write-gate-bash-")
    os.makedirs(os.path.join(proj, "config"))
    with open(os.path.join(proj, "config", "bootcamp_progress.json"), "w") as fh:
        fh.write("{}")
    return proj


def run_bash(command, cwd, env=None, raw=None):
    """Run the gate on a Bash tool call from `cwd`; return (exit_code, stderr)."""
    payload = raw if raw is not None else json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": command}})
    run_env = dict(os.environ)
    run_env.update(env or {})
    proc = subprocess.run([sys.executable, GATE], input=payload, cwd=cwd,
                          capture_output=True, text=True, env=run_env)
    return proc.returncode, proc.stderr


class _Project(unittest.TestCase):
    """A bootcamp project under the system temp directory, removed after each test."""

    def setUp(self):
        self.proj = os.path.realpath(make_project())
        self.addCleanup(shutil.rmtree, self.proj, True)

    def assertBlocked(self, command, **kw):
        rc, err = run_bash(command, kw.pop("cwd", self.proj), **kw)
        self.assertEqual(rc, BLOCK, "not blocked: %r" % command)
        self.assertIn(TEMP_MSG, err, "blocked, but not with LOC_MSG: %r" % command)

    def assertAllowed(self, command, **kw):
        rc, err = run_bash(command, kw.pop("cwd", self.proj), **kw)
        self.assertEqual(rc, ALLOW, "blocked (%s): %r" % (err.strip(), command))


class TheIncidentCommandIsBlocked(_Project):
    def test_from_a_project_outside_the_temp_directory(self):
        """The acceptance criterion's case: the project is NOT under /tmp.

        The project is made under HOME, the case a Bootcamper's project is. Skipped where
        HOME is itself under a temp prefix, since the project would then not be outside it.
        """
        home = os.path.realpath(os.path.expanduser("~"))
        temp = os.path.realpath(tempfile.gettempdir())
        if home == temp or home.startswith(temp + os.sep) or home.startswith("/tmp/"):
            self.skipTest("HOME (%s) is under the temp directory" % home)
        try:
            proj = make_project(parent=home)
        except OSError as exc:
            self.skipTest("HOME is not writable: %s" % exc)
        self.addCleanup(shutil.rmtree, proj, True)
        self.assertFalse(proj.startswith("/tmp/"), proj)
        self.assertBlocked(INCIDENT, cwd=proj)
        self.assertAllowed(INCIDENT.replace("/tmp/", "src/resources/"), cwd=proj)

    def test_from_a_project_under_the_temp_directory(self):
        """/tmp/rds_register.py is outside a project at /tmp/write-gate-bash-XXXX too."""
        self.assertBlocked(INCIDENT)


class EveryNamedFormIsBlocked(_Project):
    CASES = {
        "curl -o": "curl -o /tmp/x.py " + URL,
        "curl -o attached": "curl -o/tmp/x.py " + URL,
        "curl --output": "curl --output /tmp/x.py " + URL,
        "curl --output=": "curl --output=/tmp/x.py " + URL,
        "curl --output-dir": "curl --output-dir /tmp -O " + URL,
        "curl --output-dir=": "curl --output-dir=/var/tmp -O " + URL,
        "curl -fsSL -o": "curl -fsSL -o /tmp/x.py " + URL,
        "curl -sSfo": "curl --proto =https --tlsv1.2 -sSfo /tmp/rustup-init.sh https://sh.rustup.rs",
        "curl, option after the URL": "curl " + URL + " -o /tmp/x.py",
        "wget -O": "wget -O /tmp/x.deb " + URL,
        "wget -qO": "wget -qO /tmp/x.deb " + URL,
        "wget --output-document=": "wget --output-document=/tmp/x.deb " + URL,
        "wget -P": "wget -P /tmp " + URL,
        "wget --directory-prefix=": "wget --directory-prefix=/tmp " + URL,
        "> spaced": "echo hi > /tmp/out.txt",
        "> attached": "echo hi >/tmp/out.txt",
        ">>": "echo hi >> /tmp/out.txt",
        "2>": "ls 2> /tmp/err.txt",
        "2> attached": "ls 2>/tmp/err.txt",
        "&>": "ls &>/tmp/all.txt",
        "tee": "echo hi | tee /tmp/out.txt",
        "tee -a": "echo hi | tee -a /tmp/out.txt",
        "cp into a temp file": "cp src/a.py /tmp/a.py",
        "cp into the temp dir itself": "cp src/a.py /tmp",
        "cp -r": "cp -r src /tmp/backup",
        "cp, descriptor redirect after": "cp src/a.py /tmp/a.py 2>/dev/null",
        "cp -t": "cp -t /tmp src/a.py src/b.py",
        "cp --target-directory=": "cp --target-directory=/tmp src/a.py",
        "cp --target-directory": "cp --target-directory /tmp src/a.py",
        "mv into Downloads": "mv src/a.py ~/Downloads/",
        "mv into $HOME/Downloads": "mv src/a.py $HOME/Downloads/a.py",
    }

    def test_each_form(self):
        for name, command in self.CASES.items():
            with self.subTest(form=name):
                self.assertBlocked(command)


class TheCommandIsSplitOnItsOperators(_Project):
    """A write after `;`, `&&`, `||`, `|` or a newline is still a top-level write."""

    def test_each_operator(self):
        for command in (
                "cd src && curl -o /tmp/x.py " + URL,
                "true; wget -O /tmp/x.deb " + URL,
                "false || cp src/a.py /tmp/",
                "cat src/a.py | tee /tmp/a.py",
                "echo start\ncurl -o /tmp/x.py " + URL,
                "echo a \\\n  > /tmp/out.txt",
                "if true; then curl -o /tmp/x.py " + URL + "; fi",
                "sudo -u root curl -o /tmp/x.py " + URL,
                "X=1 curl -o /tmp/x.py " + URL,
                "cp src/a.py /tmp/a.py  # keep a copy",
                "cat > /tmp/x.txt <<'EOF'\nhello\nEOF"):
            with self.subTest(command=command):
                self.assertBlocked(command)


class TempIsRecognizedEveryWayItIsSpelled(_Project):
    def test_spellings(self):
        for target in ("$TMPDIR/x.py", "${TMPDIR}/x.py", "${TMPDIR:-/tmp}/x.py",
                       "%TEMP%\\x.py", "%Tmp%\\x.py", "~/Downloads/x.py",
                       "/c/Users/someone/AppData/Local/Temp/x.py",
                       "/var/tmp/x.py", "/private/tmp/x.py"):
            with self.subTest(target=target):
                self.assertBlocked("curl -o %s %s" % (shlex.quote(target), URL))

    def test_a_relocated_temp_dir_named_by_the_environment(self):
        """The Write/Edit path's env-var branch serves Bash too: no static prefix names it."""
        self.assertBlocked("curl -o /opt/relocated-temp-xyz/x.py " + URL,
                           env={"TMPDIR": "/opt/relocated-temp-xyz"})
        self.assertAllowed("curl -o /opt/relocated-temp-xyz/x.py " + URL)


class NegativeControlsAreAllowed(_Project):
    def test_a_project_relative_target(self):
        self.assertAllowed("curl -fsSL -o src/resources/x.py " + URL)
        self.assertAllowed("wget -P src/resources " + URL)

    def test_a_project_under_the_temp_directory_writing_inside_itself(self):
        """The auto-test sandbox case: the project itself is under /tmp."""
        self.assertTrue(self.proj.startswith(os.path.realpath(tempfile.gettempdir())))
        inside = os.path.join(self.proj, "src", "resources", "x.py")
        for command in ("curl -o %s %s" % (inside, URL),
                        "cp src/a.py %s" % os.path.dirname(inside),
                        "echo hi > %s" % inside,
                        "cp src/a.py %s" % self.proj):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_device_paths(self):
        for command in ("ls > /dev/null", "ls 2>/dev/null", "ls >/dev/null 2>&1",
                        "ls &>/dev/null", "echo hi > /dev/stderr", "echo hi | tee /dev/stdout"):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_temp_as_a_source_is_not_a_target(self):
        for command in ("cat /tmp/x.txt", "cp /tmp/x.py src/", "mv /tmp/x.py src/resources/",
                        "sort < /tmp/in.txt > data/sorted.txt", "ls /tmp",
                        # Carried over from the losing race approach (#876, comment 3): a
                        # temp path among several sources, in a URL, as the script a
                        # program runs, and as a read redirect before tee's own target.
                        "cp /tmp/a /tmp/b src/resources/",
                        "curl -o src/x https://example.com/tmp/x",
                        "python3 /tmp/x.py > src/out.txt", "tee < /tmp/in src/out"):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_the_source_cases_block_when_their_target_is_temp(self):
        """Positive control for the cases above: the same forms, with the target moved to
        temp, are blocked, so the allow is the source/target distinction at work."""
        for command in ("cp /tmp/a /tmp/b /tmp/", "curl -o /tmp/x https://example.com/src/x",
                        "python3 src/x.py > /tmp/out.txt", "tee < src/in /tmp/out"):
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_outside_the_project_but_not_temp(self):
        """Out of scope by decision: installers write to /opt/senzing and ~/.cargo."""
        for command in ("curl -o /opt/senzing/x.tgz " + URL, "cp x ~/.cargo/bin/",
                        "curl -o ~/tmp/x.py " + URL):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_a_quoted_payload_is_not_parsed(self):
        for command in ("bash -c 'curl -o /tmp/x.py %s'" % URL,
                        'sh -c "wget -qO /tmp/x.deb %s"' % URL,
                        "echo 'cp a /tmp/b'"):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_a_here_document_body_is_data(self):
        body = "cp src/a.py /tmp/a.py"
        self.assertBlocked(body)    # positive control: the body alone is a blocked command
        self.assertAllowed("cat > src/scripts/backup.sh <<'EOF'\n%s\nEOF\necho done" % body)
        self.assertAllowed("cat > src/scripts/backup.sh <<-EOF\n\t%s\n\tEOF" % body)

    def test_an_unparseable_command(self):
        self.assertAllowed('echo "unbalanced > /tmp/x.txt')

    def test_no_bootcamp_no_gate(self):
        os.remove(os.path.join(self.proj, "config", "bootcamp_progress.json"))
        self.assertAllowed(INCIDENT)
        self.assertAllowed("echo hi > /tmp/out.txt")


class ModuleTwoInContainerRowsAreAllowed(_Project):
    """Module 2's in-container install rows write to /tmp INSIDE the container.

    Read from the shipped table rather than copied, so a row that changes is tested as it
    ships. The positive control runs the same row unquoted and expects a block, so the
    allow below is the quoting at work and not a row that names no temp target.
    """

    def rows(self):
        with open(MODULE_2, encoding="utf-8") as fh:
            text = fh.read()
        rows = {}
        for lang in ("C#", "Rust"):
            m = re.search(r"(?m)^\s*\| %s \| `([^`]+)` \|" % re.escape(lang), text)
            self.assertIsNotNone(m, "Module 2 has no %s install row" % lang)
            rows[lang] = m.group(1)
        return rows

    def test_the_rows_name_a_temp_target(self):
        for lang, install in self.rows().items():
            with self.subTest(lang=lang):
                self.assertIn("/tmp/", install)
                self.assertBlocked(install)

    def test_the_rows_inside_docker_exec_and_docker_run(self):
        for lang, install in self.rows().items():
            for command in (
                    "docker exec -e DEBIAN_FRONTEND=noninteractive senzing bash -c %s"
                    % shlex.quote(install),
                    "docker run --rm debian:12 sh -c %s" % shlex.quote(install),
                    'podman exec senzing bash -c "%s"' % install.replace('"', '\\"')):
                with self.subTest(lang=lang, command=command[:40]):
                    self.assertAllowed(command)


class TheWriteAndEditPathIsUnchanged(_Project):
    def test_a_bash_command_with_a_secret_shaped_string_is_not_blocked(self):
        """INV-109's secret check stays on Write and Edit."""
        for command in ("echo AKIA" + "A" * 16, "echo '-----BEGIN RSA PRIVATE KEY-----'",
                        "echo AQAAAD" + "abc123XYZ+/=" * 4):
            with self.subTest(command=command[:12]):
                self.assertAllowed(command)

    def test_a_named_write_tool_still_blocks_temp_and_secrets(self):
        """tool_name on the payload must not route Write or Edit into the Bash branch."""
        for tool in ("Write", "Edit"):
            with self.subTest(tool=tool):
                temp = json.dumps({"tool_name": tool, "tool_input": {
                    "file_path": "/tmp/x.py", "content": "x = 1"}})
                rc, err = run_bash(None, self.proj, raw=temp)
                self.assertEqual((rc, TEMP_MSG in err), (BLOCK, True))
                outside = json.dumps({"tool_name": tool, "tool_input": {
                    "file_path": "/opt/not-the-project/x.py", "content": "x = 1"}})
                self.assertEqual(run_bash(None, self.proj, raw=outside)[0], BLOCK)
                secret = json.dumps({"tool_name": tool, "tool_input": {
                    "file_path": "config/x", "content": "AKIA" + "A" * 16}})
                self.assertEqual(run_bash(None, self.proj, raw=secret)[0], BLOCK)

    def test_a_bash_payload_that_is_not_json_is_allowed(self):
        self.assertAllowed(None, raw='{"tool_name": "Bash", "tool_input": {"command": "echo >')


class TheHookIsWiredAndDocumented(unittest.TestCase):
    def test_hooks_json_registers_the_gate_for_bash(self):
        with open(HOOKS_JSON, encoding="utf-8") as fh:
            hooks = json.load(fh)["hooks"]
        matchers = [entry.get("matcher", "") for entry in hooks.get("PreToolUse", [])
                    if any("write-gate.py" in h.get("command", "")
                           for h in entry.get("hooks", []))]
        self.assertEqual(len(matchers), 1, "write-gate.py is not registered exactly once")
        self.assertEqual(set(matchers[0].split("|")), {"Write", "Edit", "Bash"})

    def test_the_readme_row_says_what_bash_is_checked_for(self):
        with open(HOOKS_README, encoding="utf-8") as fh:
            row = next(line for line in fh if "`scripts/write-gate.py`" in line
                       and line.startswith("|"))
        self.assertIn("Bash", row.split("|")[1], "the Event cell does not name Bash")
        for form in ("`curl -o`", "`wget -O`", "`tee`", "`cp`", "`mv`", "`>`"):
            with self.subTest(form=form):
                self.assertIn(form, row)

    def test_working_examples_names_the_save_location(self):
        with open(GROUND_RULES, encoding="utf-8") as fh:
            text = fh.read()
        start = text.index("- **Working examples: search mode")
        end = text.index("\n- **", start + 1)
        paragraph = " ".join(text[start:end].split())
        for token in ("`src/resources/`", '"File placement"', "INV-200"):
            with self.subTest(token=token):
                self.assertIn(token, paragraph)


if __name__ == "__main__":
    unittest.main()
