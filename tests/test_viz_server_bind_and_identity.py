"""A busy port can still accept a bind, so the server asks who is answering.

Enforces **INV-260** — bind loopback explicitly, never the wildcard, and confirm the process
answering `/api/stats` is the one just started by comparing a per-process nonce; a
disagreement stops rather than warns. Registered 2026-08-17, after the production-readiness
audit found the rule shipped and unregistered.

`lsof -ti:8080` reported port 8080 busy — an unrelated `VizServer` from another project,
started three weeks earlier, bound to `127.0.0.1:8080`. The bootcamp's server bound
**successfully anyway**, to `*:8080`, because a loopback bind and a wildcard bind do not
collide. Two processes then listened on one port and either could answer a localhost
request. The first `/api/stats` probe happened to reach the new server, which is the only
reason it looked fine.

⛔ **Had the browser reached the other one**, the Bootcamper would have been shown a
three-week-old dataset under their own project's title, every number on the page someone
else's, and the keepsake screenshots would have captured it. The existing guidance treated
a port conflict as a *bind failure*; this is a success that produces nondeterministic
results, which is strictly worse — a failure stops the step and this does not.

⚠️ **The bundled Python server was already safe and was not the defect.** It has always
bound `127.0.0.1` explicitly. The Bootcamper was running their **own** implementation,
ported from the reference per Module 7 step 3c, and the any-language contract never stated
the bind host — so a Java port using the idiomatic `InetSocketAddress(port)`, a wildcard
bind, was fully conformant and carried the defect. That is the INV-002 boundary exactly: a
rule constraining the Bootcamper's code must be stated as behavior in the contract, never
only in the Python reference.

⛔ **The two remedies cover opposite directions and neither alone is enough.** A loopback
bind makes a colliding *loopback* listener fail cleanly; it does nothing when the
pre-existing listener is *wildcard*-bound, where our loopback bind is the one that succeeds
alongside it. Only asking which server answered covers both — so the identity probe is
tested here against a **constructed two-listener condition**, not against the happy path.

⚠️ **The container route (#460) is the one place the bind host is not loopback, and it is
narrow.** Inside SDK setup's container, `127.0.0.1` is the container's own loopback, which the port
published to the host does not reach. The server therefore takes `--bind-host`, default `127.0.0.1`,
and the container route passes the container's own interface address. Every wildcard spelling is
refused, on the command line and again where the socket is bound. The in-process probe asks the
address actually bound, and the startup line carries `server_nonce=<nonce>` so the host-side check
(`docker_lifecycle.py confirm-viz`, pinned in `test_container_viz_port_is_published_and_checked.py`)
can compare it against what the published port answers. With no flag, the bind, the probe and the
start of the startup line are what they were.

Source spec: `specs/the-viz-contract-never-states-the-bind-host-so-a-port-conflict-can-succeed.md`;
the container route, GitHub issue #460.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import json
import re
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SERVER = PLUGIN / "scripts" / "senzing_viz_server.py"
CONTRACT = (PLUGIN / "skills" / "module-03b-truthset-visualization" /
            "visualization-api-reference.md")
LIFECYCLE = PLUGIN / "scripts" / "docker_lifecycle.py"

#: Every wildcard spelling `--bind-host` must refuse. The first three are the issue's.
WILDCARDS = ("", "0.0.0.0", "::", " 0.0.0.0 ", "::0", "0:0:0:0:0:0:0:0", "*")

#: A stand-in for a container's interface address, for the tests that never open a socket.
CONTAINER_ADDRESS = "172.17.0.2"


def load_server():
    spec = importlib.util.spec_from_file_location("viz_server_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_server_under_test"] = module
    spec.loader.exec_module(module)
    return module


VIZ = load_server()


def free_port(host="127.0.0.1"):
    with socket.socket() as probe:
        probe.bind((host, 0))
        return probe.getsockname()[1]


def bindable(host):
    """Whether this machine can bind `host` (127.0.0.2 binds on Linux, not on macOS)."""
    try:
        free_port(host)
        return True
    except OSError:
        return False


def load_lifecycle():
    spec = importlib.util.spec_from_file_location("docker_lifecycle_for_viz_test", LIFECYCLE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Foreign(BaseHTTPRequestHandler):
    """A stranger's server: valid, answers /api/stats, and is not us."""

    nonce = "a-different-server"

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's interface
        body = json.dumps({"records_total": 100, "entities_total": 80,
                           "server_nonce": self.nonce}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class Ours(Foreign):
    """Same shape, but carrying this process's real nonce."""

    @property
    def nonce(self):
        return VIZ.SERVER_NONCE


class serve_on:
    """Run `handler` on `port` for the duration of the block."""

    def __init__(self, handler, port):
        self.handler, self.port = handler, port

    def __enter__(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), self.handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


class TheBindHostIsPinned(unittest.TestCase):
    """⛔ A future edit must not widen this to the wildcard address."""

    def test_the_constant_is_loopback(self):
        self.assertEqual("127.0.0.1", VIZ.BIND_HOST)

    def test_with_no_flag_the_bind_host_is_the_constant(self):
        """Unchanged default: a run without `--bind-host` binds what it always bound."""
        self.assertEqual(VIZ.build_arg_parser().parse_args([]).bind_host, "127.0.0.1")

    def test_the_server_binds_only_a_checked_host(self):
        source = SERVER.read_text(encoding="utf-8")
        body = source[source.index("def start_serving("):source.index("def build_arg_parser(")]
        self.assertIn("ThreadingHTTPServer((host, port), handler)", body)
        self.assertLess(body.index("host = check_bind_host(host)"),
                        body.index("ThreadingHTTPServer((host, port), handler)"))
        self.assertIn("type=_bind_host_arg", source)

    def test_no_wildcard_bind_address_appears_in_the_server(self):
        source = SERVER.read_text(encoding="utf-8")
        for wildcard in ('("", args.port)', '("0.0.0.0"', "'0.0.0.0'"):
            with self.subTest(wildcard=wildcard):
                self.assertNotIn(wildcard, source)

    def test_the_reason_is_recorded_beside_the_constant(self):
        """The rule will be edited again; the reasoning will not be rediscovered."""
        source = " ".join(SERVER.read_text(encoding="utf-8").split())
        self.assertIn("wildcard bind does NOT collide with an existing loopback listener",
                      source)


class EveryWildcardIsRefused(unittest.TestCase):
    """⛔ The wildcard stays forbidden on every route, the container route included."""

    def test_the_command_line_refuses_every_wildcard(self):
        for value in WILDCARDS:
            with self.subTest(value=value):
                err = io.StringIO()
                with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
                    VIZ.build_arg_parser().parse_args(["--bind-host", value])
                self.assertEqual(caught.exception.code, 2)
                self.assertIn("wildcard", err.getvalue())

    def test_the_bind_itself_refuses_every_wildcard(self):
        """Defense in depth: a caller that skips argparse still cannot bind the wildcard."""
        for value in WILDCARDS:
            with self.subTest(value=value):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    self.assertIsNone(VIZ.start_serving(Ours, value, free_port()))
                self.assertIn("wildcard", err.getvalue())

    def test_a_hostname_or_a_non_ipv4_address_is_refused(self):
        """A hostname could resolve to anything, the wildcard included."""
        for value in ("localhost", "container.local", "::1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    VIZ.check_bind_host(value)

    def test_negative_control_concrete_addresses_are_accepted(self):
        """Without this, a check that refused everything would pass the tests above."""
        for value in ("127.0.0.1", CONTAINER_ADDRESS, "10.88.0.5", "192.168.64.3"):
            with self.subTest(value=value):
                self.assertEqual(VIZ.check_bind_host(value), value)
                self.assertEqual(
                    VIZ.build_arg_parser().parse_args(["--bind-host", value]).bind_host, value)


class TheDefaultBindIsLoopback(unittest.TestCase):
    """Runtime: with no flag, the server binds 127.0.0.1 and its probe asks 127.0.0.1."""

    def test_start_serving_binds_loopback_and_confirms_itself(self):
        port = free_port()
        started = VIZ.start_serving(Ours, VIZ.BIND_HOST, port)
        self.assertIsNotNone(started)
        httpd, _ = started
        try:
            self.assertEqual(httpd.server_address, ("127.0.0.1", port))
            self.assertTrue(VIZ.confirm_server_identity(port))
        finally:
            httpd.shutdown()
            httpd.server_close()


class TheContainerModeBind(unittest.TestCase):
    """The container route binds the container's interface address, and its own probe asks it."""

    def test_the_in_process_probe_targets_the_bound_address(self):
        """Platform-independent: no socket, the bind and the probe recorded."""
        seen = {}

        class FakeServer:
            def __init__(self, address, handler):
                seen["bound"] = address

            def serve_forever(self):
                pass

            def shutdown(self):
                pass

            def server_close(self):
                pass

        def probe(port, host=None, timeout=None):
            seen["probed"] = (host, port)
            return True

        real_server, real_probe = VIZ.ThreadingHTTPServer, VIZ.confirm_server_identity
        VIZ.ThreadingHTTPServer, VIZ.confirm_server_identity = FakeServer, probe
        try:
            self.assertIsNotNone(VIZ.start_serving(Ours, CONTAINER_ADDRESS, 8080))
        finally:
            VIZ.ThreadingHTTPServer, VIZ.confirm_server_identity = real_server, real_probe
        self.assertEqual(seen["bound"], (CONTAINER_ADDRESS, 8080))
        self.assertEqual(seen["probed"], (CONTAINER_ADDRESS, 8080))

    def test_a_non_loopback_bind_answers_there_and_not_on_127_0_0_1(self):
        """Runtime, on a second address (127.0.0.2 on Linux): the reason the probe must move.

        A loopback probe of a server bound elsewhere finds nothing and would stop the
        handover; the probe of the bound address finds this process."""
        address = "127.0.0.2"
        if not bindable(address):
            self.skipTest("%s cannot be bound on this platform" % address)
        port = free_port(address)
        if not bindable("127.0.0.1") or not _port_free("127.0.0.1", port):
            self.skipTest("port %d is in use on 127.0.0.1" % port)
        started = VIZ.start_serving(Ours, address, port)
        self.assertIsNotNone(started)
        httpd, _ = started
        try:
            self.assertEqual(httpd.server_address, (address, port))
            self.assertTrue(VIZ.confirm_server_identity(port, host=address))
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertFalse(VIZ.confirm_server_identity(port, timeout=0.5))
        finally:
            httpd.shutdown()
            httpd.server_close()


def _port_free(host, port):
    with socket.socket() as probe:
        try:
            probe.bind((host, port))
            return True
        except OSError:
            return False


def _nothing_listening(host, port):
    """Whether no server accepts connections on ``host:port``.

    ⚠️ Not a bind test. The probe the server just answered leaves the server's side of that
    connection in TIME_WAIT on this port, so a bind without ``SO_REUSEADDR`` can fail with
    nothing listening at all, and the check would then fail at random. What a refused start
    must guarantee is that no listener is left behind, which is what a connect asks.
    """
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex((host, port)) != 0


class TheStartupLineCarriesTheNonce(unittest.TestCase):
    """Every server ends its startup line with `server_nonce=<nonce>` (any language)."""

    def test_the_default_line_is_the_old_line_plus_the_token(self):
        line = VIZ.startup_line(VIZ.BIND_HOST, 8080)
        self.assertEqual(line, "Visualization running: http://localhost:8080 server_nonce=%s"
                         % VIZ.SERVER_NONCE)

    def test_a_container_mode_line_names_the_bound_address_and_the_token(self):
        line = VIZ.startup_line(CONTAINER_ADDRESS, 8080)
        self.assertTrue(line.startswith("Visualization running: http://%s:8080 "
                                        % CONTAINER_ADDRESS), line)
        self.assertTrue(line.endswith("server_nonce=" + VIZ.SERVER_NONCE), line)

    def test_the_host_side_helper_reads_the_nonce_the_server_prints(self):
        """The two halves agree on the token, so the host-side check compares like with like."""
        lifecycle = load_lifecycle()
        for host in (VIZ.BIND_HOST, CONTAINER_ADDRESS):
            with self.subTest(host=host):
                found = lifecycle.NONCE_TOKEN.search(VIZ.startup_line(host, 8080))
                self.assertIsNotNone(found)
                self.assertEqual(found.group(1), VIZ.SERVER_NONCE)
                self.assertIn(lifecycle.STARTUP_MARK, VIZ.startup_line(host, 8080))

    def test_negative_control_the_pre_460_line_carries_no_token(self):
        self.assertIsNone(load_lifecycle().NONCE_TOKEN.search(
            "Visualization running: http://localhost:8080"))

    def test_main_prints_the_startup_line_flushed(self):
        """Flushed: on the container route stdout is a log file the host reads."""
        source = SERVER.read_text(encoding="utf-8")
        main = source[source.index("def main(argv=None):"):]
        self.assertIn("print(startup_line(args.bind_host, args.port), flush=True)", main)


class TheStatsPayloadCarriesAPerProcessNonce(unittest.TestCase):

    def test_the_nonce_is_exposed(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn('"server_nonce": SERVER_NONCE', source)

    def test_it_is_unique_per_process(self):
        """Two loads of the module must not agree, or the probe proves nothing."""
        other = load_server()
        self.assertNotEqual(VIZ.SERVER_NONCE, other.SERVER_NONCE)


class TheIdentityProbeDetectsAForeignServer(unittest.TestCase):
    """⛔ Negative control — the two-listener condition, constructed."""

    def test_a_foreign_server_on_the_port_is_detected(self):
        port = free_port()
        with serve_on(Foreign, port):
            self.assertFalse(
                VIZ.confirm_server_identity(port),
                "the probe accepted a server that is not this process — the Bootcamper "
                "would be shown a stranger's data under their own project's title")

    def test_our_own_server_is_accepted(self):
        """Fixture control: without this, the test above passes for the wrong reason."""
        port = free_port()
        with serve_on(Ours, port):
            self.assertTrue(VIZ.confirm_server_identity(port))

    def test_a_server_with_no_nonce_at_all_is_rejected(self):
        class Nonceless(Foreign):
            nonce = None

        port = free_port()
        with serve_on(Nonceless, port):
            self.assertFalse(VIZ.confirm_server_identity(port))

    def test_an_unanswerable_probe_is_a_failure_not_a_pass(self):
        """⚠️ The failure mode looks like success, so silence is not permission."""
        self.assertFalse(VIZ.confirm_server_identity(free_port(), timeout=0.5))

    def test_the_conflict_report_names_the_port_and_both_figures(self):
        port = free_port()
        import io
        import contextlib
        buffer = io.StringIO()
        with serve_on(Foreign, port), contextlib.redirect_stderr(buffer):
            VIZ.confirm_server_identity(port)
        message = buffer.getvalue()
        self.assertIn(str(port), message)
        self.assertIn(VIZ.SERVER_NONCE, message)
        self.assertIn("a-different-server", message)
        self.assertIn("DIFFERENT server", message)


class TheStartupSequenceIsOrderedCorrectly(unittest.TestCase):
    """⚠️ Runtime where it can be, source order where it cannot.

    `main()`'s serve path needs a live Senzing engine, so nothing in this offline suite
    (INV-108) can run it end to end. `start_serving` — the bind, the background thread and
    the identity probe — needs no engine, so it is run here against real sockets: our own
    handler is accepted, a responder with another nonce is refused and leaves nothing
    bound, and a held port is a reported bind failure. What stays source-order is `main`'s
    use of it, which decides whether the Bootcamper can ever see a URL that was not checked.
    """

    def setUp(self):
        self.source = SERVER.read_text(encoding="utf-8")
        self.serving = self.source[self.source.index("def start_serving("):
                                   self.source.index("def build_arg_parser(")]
        self.main = self.source[self.source.index("    handler = make_handler("):]

    def test_the_url_is_printed_only_after_start_serving_returned(self):
        started = self.main.index("start_serving(handler, args.bind_host, args.port)")
        refused = self.main.index("if started is None:\n        return 1")
        url = self.main.index("print(startup_line(")
        self.assertLess(started, refused)
        self.assertLess(refused, url,
                        "the URL is printed before the identity probe — a Bootcamper "
                        "could open a page served by another process")

    def test_the_probe_asks_the_bound_address(self):
        self.assertIn("if not confirm_server_identity(port, host=host, timeout=timeout):",
                      self.serving)

    def test_a_failed_probe_shuts_down_without_printing(self):
        probe = self.serving.index("if not confirm_server_identity(")
        block = self.serving[probe:self.serving.index("return None", probe) + len("return None")]
        self.assertIn("httpd.shutdown()", block)
        self.assertIn("httpd.server_close()", block)
        self.assertNotIn("Visualization running", self.serving)

    def test_a_failed_probe_at_runtime_returns_none_and_frees_the_port(self):
        """⛔ Negative control: the responder carries another nonce, as a stranger would."""
        port = free_port()
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(VIZ.start_serving(Foreign, VIZ.BIND_HOST, port, timeout=2))
        self.assertIn("DIFFERENT server", err.getvalue())
        self.assertTrue(_nothing_listening("127.0.0.1", port),
                        "a refused server kept listening on the port")

    def test_the_server_is_shut_down_before_its_socket_is_closed(self):
        tail = self.main[self.main.index("finally:"):]
        self.assertLess(tail.index("httpd.shutdown()"), tail.index("httpd.server_close()"),
                        "server_close runs while serve_forever is still looping")

    def test_a_bind_failure_is_reported_and_does_not_proceed(self):
        held = socket.socket()
        self.addCleanup(held.close)
        held.bind(("127.0.0.1", 0))
        held.listen(1)
        port = held.getsockname()[1]
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(VIZ.start_serving(Ours, VIZ.BIND_HOST, port))
        self.assertIn("could not bind 127.0.0.1:%d" % port, err.getvalue())
        self.assertIn("--port", err.getvalue())


class TheContractStatesBothRulesForEveryLanguage(unittest.TestCase):
    """INV-002/INV-090/INV-124 — the defect was a conformant non-Python implementation."""

    def setUp(self):
        self.text = " ".join(CONTRACT.read_text(encoding="utf-8").split())

    def test_the_loopback_bind_is_required_with_its_reason(self):
        self.assertIn("Bind the LOOPBACK interface explicitly", self.text)
        self.assertIn("does **not** collide with an existing loopback listener",
                      self.text)

    def test_it_names_the_idiomatic_wrong_form_in_other_languages(self):
        """The rule a faithful port gets wrong by writing the shorter thing."""
        for idiom in ("new InetSocketAddress(port)", 'server.listen(port, "127.0.0.1")',
                      "IPAddress.Loopback"):
            with self.subTest(idiom=idiom):
                self.assertIn(idiom, self.text)

    def test_a_successful_bind_is_not_treated_as_proof_the_port_was_free(self):
        self.assertIn("A successful bind is NOT proof the port was free", self.text)

    def test_the_identity_probe_is_required_and_specifies_what_it_compares(self):
        self.assertIn("probe `/api/stats` and confirm the responder is the server just "
                      "started", self.text)
        self.assertIn("Compare the nonce, not the record count", self.text)

    def test_a_disagreement_stops_rather_than_warns(self):
        self.assertIn("On disagreement, STOP and report the conflict", self.text)
        self.assertIn("must not degrade to a warning", self.text)

    def test_it_explains_why_both_remedies_are_needed(self):
        self.assertIn("they cover opposite directions", self.text)

    def test_the_container_variant_binds_the_interface_address_never_the_wildcard(self):
        self.assertIn("(INV-260) The one other address: inside the SDK container, bind the "
                      "container's own interface address, on port `8080`.", self.text)
        self.assertIn("**inside the container, at launch**", self.text)
        self.assertIn('socket.gethostbyname(socket.gethostname())', self.text)
        self.assertIn("Never hard-code it, and never take it from host-side inspection", self.text)
        self.assertIn("The wildcard stays forbidden on every route (INV-260).", self.text)
        self.assertIn("Refuse `\"\"`, `0.0.0.0` and `::` as a bind address", self.text)
        self.assertIn("published to host loopback (`-p 127.0.0.1:<host_port>:8080`)", self.text)

    def test_every_language_prints_the_nonce_on_its_startup_line(self):
        self.assertIn("every implementation, in every language, prints one line that starts "
                      "`Visualization running:` and ends with the token `server_nonce=<nonce>`",
                      self.text)

    def test_the_container_route_gates_the_url_on_a_host_side_probe(self):
        self.assertIn("(INV-260) On the container route the server's own probe is not the gate; "
                      "a probe from the host is.", self.text)
        self.assertIn("A disagreement or an unanswerable probe stops the step and reports the "
                      "conflict", self.text)
        self.assertIn("its own probe asks the bound address", self.text)

    def test_the_rules_are_stated_as_behavior_not_as_python(self):
        """INV-002 — a Java/C#/TypeScript implementation must be able to satisfy them."""
        start = self.text.index("Bind the LOOPBACK interface explicitly")
        end = self.text.index("Identifying the server process", start)
        block = self.text[start:end]
        self.assertNotIn("ThreadingHTTPServer", block)
        self.assertNotIn("senzing_viz_server.py", block)


if __name__ == "__main__":
    unittest.main()
