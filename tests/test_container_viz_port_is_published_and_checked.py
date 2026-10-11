"""The SDK container publishes the visualization port to host loopback, and the host checks who answers it.

Issue #460. On SDK setup's container route the visualization server ran inside a container and
bound `127.0.0.1`, the container's own loopback, and nothing published a port to the host. The
browser could not reach either visualization module, and the guide improvised a TCP relay on
`0.0.0.0` inside the container: the wildcard INV-260 forbids. The fix has four parts, and these
tests pin the three that live outside the server (the server's `--bind-host`, wildcard refusal and
startup-line nonce are pinned in `test_viz_server_bind_and_identity.py`):

1. **Module 2 publishes the port at creation.** `free-port 8080` chooses the host port; the
   container is created with `-p 127.0.0.1:<host_port>:8080` and records `host_port`. No `-p` in
   the plugin publishes 8080 without the `127.0.0.1:` host address (negative control: the
   unqualified forms are caught).
2. **`docker_lifecycle.py viz-port <name>`** prints the recorded `host_port`, and exits 3 for an
   entry that records none, which is the migration path: Module 2 asks the Bootcamper, then
   recreates the container, keeping the SDK by `commit` when `<runtime> commit --help` succeeds
   and otherwise repeating the in-container install. No relay is ever offered.
3. **`docker_lifecycle.py confirm-viz <name>`** reads the nonce from the server's startup line,
   probes `http://127.0.0.1:<host_port>/api/stats` FROM THE HOST against real sockets here, and
   prints `http://localhost:<host_port>` only when the nonce answered there is the one printed.
   A different server (exit 1) or no answer (exit 5) prints no URL (INV-260). The URL comes from
   the recorded port, never from the server's own line (which names the container's address).

⛔ Neither helper issues a container command, not even the `ps` probe `container-name` makes:
every test runs under `FakeCli` and asserts the recorded command list is empty (INV-349). The
contract's "Serving from the SDK container" is the one statement of the launch; both launch steps
link it and carry no copy of its `exec` command (INV-300). Prose is read wrap-aware (INV-346).

It does **not** establish that a real docker, podman or Apple `container` forwards the published
port to the container's interface address, or that `gethostbyname(gethostname())` names that
interface on each runtime: no container runs in this suite. The host-side probe is the gate that
turns either failure into a stopped step rather than a dead link.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import io
import json
import os
import re
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from _wrapped_text import match_lines as _match_lines
from test_container_lifecycle_runtimes import FakeCli, load_module

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SKILLS = os.path.join(PLUGIN, "skills")
MODULE_2 = os.path.join(SKILLS, "module-02-sdk-setup", "SKILL.md")
CONTRACT = os.path.join(SKILLS, "module-03b-truthset-visualization",
                        "visualization-api-reference.md")
TRUTHSET_LAUNCH = os.path.join(SKILLS, "module-03b-truthset-visualization",
                               "phase1-visualization.md")
MODULE_7 = os.path.join(SKILLS, "module-07-query-visualize-discover", "phase1-query-visualize.md")

NAME = "senzing-bootcamp-demo-1a2b3c"
NONCE = "0123456789abcdef0123456789abcdef"


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` (INV-346), taking a pattern string or a compiled one."""
    return _match_lines(text, re.compile(pattern) if isinstance(pattern, str) else pattern)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@contextlib.contextmanager
def project_with(containers):
    """A temporary bootcamp project recording these containers, as the working directory."""
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "config"))
        os.makedirs(os.path.join(root, "logs"))
        with open(os.path.join(root, "config", "bootcamp_progress.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"current_module": "Truth Set visualization",
                       "docker_containers": list(containers)}, fh)
        previous = os.getcwd()
        os.chdir(root)
        try:
            yield root
        finally:
            os.chdir(previous)


def stats_handler(nonce):
    """A `/api/stats` responder carrying `nonce` (None: no `server_nonce` key), counting hits."""

    class Handler(BaseHTTPRequestHandler):
        hits = []

        def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's interface
            Handler.hits.append(self.path)
            payload = {"records_total": 84, "entities_total": 60}
            if nonce is not None:
                payload["server_nonce"] = nonce
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


@contextlib.contextmanager
def published(handler):
    """Stand `handler` up on a host loopback port, as the runtime's published port would be."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()


class Helper(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def run_cli(self, argv, containers):
        """Run the helper's CLI in a project recording `containers`, every container CLI stubbed."""
        out, err = io.StringIO(), io.StringIO()
        with project_with(containers) as root, \
                FakeCli(self.mod, present=("docker", "podman", "container")) as cli, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.mod.main(argv(root) if callable(argv) else argv)
        self.assertEqual(cli.commands, [], "the helper issued a container command (INV-349)")
        return code, out.getvalue(), err.getvalue()


class VizPort(Helper):
    def test_the_recorded_host_port_is_printed(self):
        for recorded in (8080, 8081, "8082"):
            with self.subTest(recorded=recorded):
                code, out, _ = self.run_cli(
                    ["viz-port", NAME],
                    [{"name": NAME, "runtime": "docker", "host_port": recorded}])
                self.assertEqual((code, out.strip()), (0, str(int(recorded))))

    def test_it_reads_the_named_entry_not_the_postgres_one(self):
        code, out, _ = self.run_cli(
            ["viz-port", NAME],
            [{"name": "bootcamp-postgres-demo-1a2b3c", "runtime": "docker", "host_port": 5432},
             {"name": NAME, "runtime": "podman", "host_port": 8083}])
        self.assertEqual((code, out.strip()), (0, "8083"))

    def test_an_entry_without_host_port_is_the_migration_path(self):
        for entry in ({"name": NAME, "runtime": "docker"}, {"name": NAME, "host_port": None},
                      {"name": NAME, "runtime": "container", "host_port": ""}, NAME):
            with self.subTest(entry=entry):
                code, out, err = self.run_cli(["viz-port", NAME], [entry])
                self.assertEqual((code, out), (3, ""))
                self.assertIn("Ask the Bootcamper whether to recreate it", err)
                self.assertIn("Never start a relay or proxy instead", err)

    def test_a_name_this_project_does_not_record_is_refused(self):
        code, out, err = self.run_cli(["viz-port", "someone-elses-container"],
                                      [{"name": NAME, "host_port": 8080}])
        self.assertEqual((code, out), (4, ""))
        self.assertIn("INV-349", err)

    def test_a_recorded_value_that_is_not_a_port_is_refused(self):
        for bad in ("http", 0, 70000, True, -1):
            with self.subTest(bad=bad):
                code, out, err = self.run_cli(["viz-port", NAME],
                                              [{"name": NAME, "host_port": bad}])
                self.assertEqual((code, out), (6, ""))
                self.assertIn("do not guess a port", err)


class ConfirmViz(Helper):
    """Real sockets: a responder on host loopback stands in for the runtime's published port."""

    def confirm(self, port, *extra, entry=None):
        entry = entry or {"name": NAME, "runtime": "docker", "host_port": port}
        return self.run_cli(["confirm-viz", NAME] + list(extra), [entry])

    def test_our_server_on_the_published_port_yields_the_url(self):
        with published(stats_handler(NONCE)) as port:
            code, out, err = self.confirm(port, "--nonce", NONCE)
        self.assertEqual((code, out.strip(), err), (0, "http://localhost:%d" % port, ""))

    def test_negative_control_a_different_server_prints_no_url(self):
        """⛔ The two-server condition, constructed: the published port answers someone else."""
        with published(stats_handler("a-different-server")) as port:
            code, out, err = self.confirm(port, "--nonce", NONCE)
        self.assertEqual((code, out), (1, ""))
        for figure in (str(port), NONCE, "a-different-server", "DIFFERENT server", "INV-260"):
            self.assertIn(figure, err)

    def test_a_responder_with_no_nonce_is_a_conflict(self):
        with published(stats_handler(None)) as port:
            code, out, err = self.confirm(port, "--nonce", NONCE)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("(no server_nonce in the response)", err)

    def test_an_unanswerable_published_port_prints_no_url(self):
        """⚠️ The container's server started, but the published port does not reach it."""
        port = free_port()
        code, out, err = self.run_cli(
            ["confirm-viz", NAME, "--nonce", NONCE, "--timeout", "1"],
            [{"name": NAME, "host_port": port}])
        self.assertEqual((code, out), (5, ""))
        self.assertIn("do not start a relay", err)

    def test_the_probe_asks_host_loopback_at_the_recorded_port(self):
        seen = []

        def urlopen(url, timeout=None):
            seen.append(url)
            raise OSError("stubbed")

        real = self.mod.urllib.request.urlopen
        self.mod.urllib.request.urlopen = urlopen
        try:
            code, _, _ = self.confirm(8085, "--nonce", NONCE)
        finally:
            self.mod.urllib.request.urlopen = real
        self.assertEqual(code, 5)
        self.assertEqual(seen, ["http://127.0.0.1:8085/api/stats"])

    def test_the_nonce_is_read_from_the_last_startup_line_of_the_log(self):
        def argv(root):
            with open(os.path.join(root, "logs", "viz-server.log"), "w", encoding="utf-8") as fh:
                fh.write("Entity model built: 84 records, 60 entities\n"
                         "Visualization running: http://172.17.0.2:8080 server_nonce=stale\n"
                         "Visualization running: http://172.17.0.2:8080 server_nonce=%s\n"
                         "Press Ctrl+C to stop.\n" % NONCE)
            return ["confirm-viz", NAME, "--log", os.path.join("logs", "viz-server.log")]

        with published(stats_handler(NONCE)) as port:
            code, out, _ = self.run_cli(argv, [{"name": NAME, "host_port": port}])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "http://localhost:%d" % port,
                         "the URL must come from the recorded host_port, not the server's line")

    def test_negative_control_a_startup_line_without_the_token_prints_no_url(self):
        def argv(root):
            with open(os.path.join(root, "logs", "viz-server.log"), "w", encoding="utf-8") as fh:
                fh.write("Visualization running: http://localhost:8080\n")
            return ["confirm-viz", NAME, "--log", os.path.join("logs", "viz-server.log")]

        with published(stats_handler(NONCE)) as port:
            code, out, err = self.run_cli(argv, [{"name": NAME, "host_port": port}])
        self.assertEqual((code, out), (5, ""))
        self.assertIn("no startup line carrying server_nonce=", err)

    def test_wait_covers_a_server_still_building_its_model(self):
        def argv(root):
            log = os.path.join(root, "logs", "viz-server.log")

            def later():
                time.sleep(0.6)
                with open(log, "w", encoding="utf-8") as fh:
                    fh.write("Visualization running: http://172.17.0.2:8080 server_nonce=%s\n"
                             % NONCE)

            threading.Thread(target=later, daemon=True).start()
            return ["confirm-viz", NAME, "--log", log, "--wait", "10"]

        with published(stats_handler(NONCE)) as port:
            code, out, _ = self.run_cli(argv, [{"name": NAME, "host_port": port}])
        self.assertEqual((code, out.strip()), (0, "http://localhost:%d" % port))

    def test_no_host_port_stops_before_any_probe(self):
        handler = stats_handler(NONCE)
        with published(handler):
            code, out, err = self.run_cli(["confirm-viz", NAME, "--nonce", NONCE],
                                          [{"name": NAME, "runtime": "docker"}])
        self.assertEqual((code, out), (3, ""))
        self.assertEqual(handler.hits, [])
        self.assertIn("Never start a relay or proxy instead", err)

    def test_free_port_from_8080_moves_upward_past_a_busy_port(self):
        tried = []

        def can_bind(port, host="127.0.0.1"):
            tried.append(port)
            return port != 8080

        real = self.mod._can_bind
        self.mod._can_bind = can_bind
        self.addCleanup(setattr, self.mod, "_can_bind", real)
        self.assertEqual(self.mod.free_port(8080), 8081)
        self.assertEqual(tried, [8080, 8081])


#: A `-p` that publishes container port 8080 without the `127.0.0.1:` host address.
UNQUALIFIED_8080 = re.compile(r"(?<![\w-])-p\s+(?!127\.0\.0\.1:)[^\s`]*:8080\b")


def plugin_markdown():
    for root, _, files in os.walk(PLUGIN):
        for name in files:
            if name.endswith(".md"):
                yield os.path.join(root, name)


class Module2PublishesTheVisualizationPort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(MODULE_2)
        anchor = cls.text.index('<a id="visualization-port"></a>')
        cls.rule = cls.text[anchor:cls.text.index("**Phase 3", anchor)]
        route = cls.text.index("For the `docker` path")
        cls.route = cls.text[route:cls.text.index('<a id="container-naming"></a>')]

    def test_one_anchored_canonical_rule(self):
        self.assertEqual(self.text.count('<a id="visualization-port"></a>'), 1)
        self.assertTrue(match_lines(self.rule, r"This is the canonical statement .* \(INV-300\)"))
        self.assertTrue(match_lines(self.route, r"\(#visualization-port\)"))

    def test_the_host_port_comes_from_free_port_8080_and_is_published_to_loopback(self):
        for pattern in (r'scripts/docker_lifecycle\.py" free-port 8080',
                        r"-p 127\.0\.0\.1:<host_port>:8080",
                        r"Record it as `host_port`",
                        r"`docker_lifecycle\.py`'s `viz-port <name>`",
                        r"The container port stays `8080`"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(self.rule, pattern), pattern)
        self.assertTrue(match_lines(self.route, r"`-p 127\.0\.0\.1:<host_port>:8080`"))

    def test_no_plugin_file_publishes_8080_without_the_loopback_address(self):
        found = []
        for path in plugin_markdown():
            for line, _ in match_lines(read(path), UNQUALIFIED_8080):
                found.append((os.path.relpath(path, REPO_ROOT), line))
        self.assertEqual(found, [])

    def test_negative_control_the_unqualified_forms_are_caught(self):
        for sample in ("docker run -p 8080:8080 img", "-p <host_port>:8080",
                       "podman run -p 0.0.0.0:8081:8080", "-p\n  8080:8080"):
            with self.subTest(sample=sample):
                self.assertTrue(match_lines(sample, UNQUALIFIED_8080), sample)
        self.assertFalse(match_lines("-p 127.0.0.1:<host_port>:8080", UNQUALIFIED_8080))

    def test_the_recreate_path_asks_first_and_keeps_the_sdk_where_it_can(self):
        for pattern in (r"`viz-port <name>` exits `3`",
                        r"run `<runtime> commit --help` with the recorded runtime",
                        r"Phase 1 asks the EULA question again \(INV-338\)",
                        r"👉 \*\*Shall I recreate the SDK container `<name>` with the visualization "
                        r"port published, so the visualization can open in your browser\?\*\*",
                        r"`<runtime> commit <name> <name>-sdk`",
                        r"`<runtime> stop <name>`, `<runtime> rm <name>`",
                        r"the visualization cannot be served live from this container"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(self.rule, pattern), pattern)

    def test_the_question_ends_the_turn(self):
        """INV-056/ground rules: the disclosure precedes the 👉, and nothing argues after it."""
        before, _, after = self.rule.partition("👉 **Shall I recreate")
        self.assertTrue(match_lines(before, r"Before the question, say what will happen"))
        self.assertTrue(match_lines(before, r"end the turn on it"))
        following = after[after.index("?**") + len("?**"):].strip()
        self.assertTrue(following.startswith("- **Yes:**"), following[:80])

    def test_no_relay_is_ever_offered(self):
        self.assertTrue(match_lines(
            self.rule, r"Never offer a relay or a proxy, inside or outside the container"))


class TheContractOwnsTheContainerLaunch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(CONTRACT)
        anchor = cls.text.index('<a id="container-route"></a>')
        cls.section = cls.text[anchor:cls.text.index("### Identifying the server process", anchor)]

    def test_one_anchored_canonical_section(self):
        self.assertEqual(self.text.count('<a id="container-route"></a>'), 1)
        self.assertTrue(match_lines(self.section, r"This is the canonical statement .* \(INV-300\)"))

    def test_it_calls_both_helpers_and_binds_the_interface_address_on_8080(self):
        for pattern in (r'docker_lifecycle\.py" viz-port <container>',
                        r'docker_lifecycle\.py" confirm-viz <container> --log logs/viz-server\.log',
                        r"socket\.gethostbyname\(socket\.gethostname\(\)\)",
                        r'--port 8080 --bind-host "\$BIND"',
                        r"Exit `3` means the container was created before SDK setup published",
                        r"Only exit `0` hands over a URL",
                        r"never start a relay or proxy in its place",
                        r"Never build the URL from the server's startup line"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(self.section, pattern), pattern)

    def test_it_dispatches_on_the_recorded_runtime(self):
        """INV-195: no literal `docker exec` in the container-route procedure."""
        self.assertTrue(match_lines(self.section, r"`<runtime>`\s+and `<container>` are the SDK "
                                                  r"container's recorded `runtime` and `name`"))
        self.assertEqual(match_lines(self.section, r"\bdocker exec\b"), [])

    def test_teardown_probes_the_bound_address_not_the_host_port(self):
        self.assertTrue(match_lines(self.section, r"probing the address it\s+bound"))
        self.assertTrue(match_lines(self.section, r"Never probe the host port to confirm teardown"))


class BothLaunchStepsLinkTheContainerRoute(unittest.TestCase):
    """Each launch step points at the contract and carries no copy of its command (INV-300)."""

    SITES = {
        "Truth Set visualization 2.3": (TRUTHSET_LAUNCH, "### 2.3 Start the live web app",
                                        "### 2.4 Verify the endpoints"),
        "Query, Visualize and Discover 3c": (MODULE_7, "### 3c. Visualization offer",
                                             "## Next: Discover phase"),
    }

    def sites(self):
        for label, (path, start, end) in self.SITES.items():
            text = read(path)
            begin = text.index(start)
            yield label, text[begin:text.index(end, begin)]

    def test_each_links_the_contract_section_and_hands_out_the_helpers_url(self):
        for label, step in self.sites():
            with self.subTest(step=label):
                self.assertTrue(match_lines(
                    step, r'visualization-api-reference\.md` → "Serving from the SDK\s+container"'))
                self.assertTrue(match_lines(step, r"canonical statement .* \(INV-300\)"))
                self.assertTrue(match_lines(step, r"the URL\s+`confirm-viz`\s+printed"))
                self.assertTrue(match_lines(step, r"`host_port`"))
                self.assertTrue(match_lines(step, r"there is no live server"))

    def test_neither_restates_the_container_launch(self):
        for label, step in self.sites():
            with self.subTest(step=label):
                self.assertEqual(match_lines(step, r"exec <container> sh -c"), [])
                self.assertEqual(match_lines(step, r"--bind-host"), [])


if __name__ == "__main__":
    unittest.main()
