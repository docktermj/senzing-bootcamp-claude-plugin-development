#!/usr/bin/env python3
"""Shared helper for the bootcamp container lifecycle hooks (INV-101).

Any container the bootcamp starts is recorded in ``config/bootcamp_progress.json``
under a ``docker_containers`` list (each entry carrying at least a ``name``, and a
``runtime`` naming the CLI that started it). This module lets the SessionEnd hook
stop those recorded containers when the session ends, and the SessionStart hook
surface them on resume so the guide can restart or regenerate them.

The bootcamp does not always run on Docker. Docker Desktop cannot be installed
non-interactively (it needs administrator privileges an agent cannot supply), so on
macOS Apple Silicon a bootcamp may legitimately run under Apple's ``container`` CLI
instead. Each entry therefore records the runtime that started it, and every action
here dispatches on that runtime rather than assuming ``docker``. An entry with no
``runtime`` key is treated as ``docker``, so progress files written by earlier runs
keep working unchanged.

The list key stays ``docker_containers`` even though its entries are no longer
Docker-only: renaming it to ``containers`` would read better but would break every
in-flight bootcamp's progress file for a cosmetic gain.

All container-CLI interaction is OPTIONAL and gated on that runtime's CLI being
present: when the CLI is absent, missing, or erroring, every function
warns-and-continues and never blocks the hook. Pure Python 3 stdlib, no third-party
dependency (INV-052/INV-001/INV-002).

This is NOT a hook itself. It is imported by the SessionEnd and SessionStart hook
scripts, which run as ``python3 "<hook>.py"``; Python puts each hook
script's own directory (this ``scripts/`` directory) on ``sys.path``, so
``import docker_lifecycle`` resolves here on Linux, macOS, and Windows alike.
Importing it runs nothing: the command line below exists only under ``__main__``.

It is also the helper SDK setup calls BEFORE it creates a container (#461), so that
two bootcamp projects on one machine never share a container name, and therefore
never stop, report or reuse each other's containers through the hooks above:

    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/docker_lifecycle.py" container-name <base> [--runtime <runtime>]
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/docker_lifecycle.py" free-port <preferred>

Both run from the bootcamp project root (the directory holding ``config/``), on the
host. ``container-name`` prints ``<base>-<slug>-<hash6>`` derived from that
directory, moving to ``-2`` ... ``-9`` past a name another project's container holds;
``free-port`` prints a host loopback port that can be bound. Neither ever removes,
stops, starts or runs a container: the only container command either issues is the
read-only ``ps`` probe of ``_container_state``. Each exits non-zero, with a message on
stderr, when it has nothing safe to print.

And it is the host-side half of serving a visualization from the SDK container (#460),
where the server binds the container's own interface address on port 8080 and the host
reaches it only through the port SDK setup published to host loopback:

    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/docker_lifecycle.py" viz-port <container>
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/docker_lifecycle.py" confirm-viz <container> --log <file> [--wait <seconds>]
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/docker_lifecycle.py" confirm-viz <container> --nonce <nonce>

``viz-port`` prints the ``host_port`` recorded on that container's ``docker_containers``
entry, and exits 3 when the entry records none (a container created before the port
was published, which the guide offers to recreate). ``confirm-viz`` reads the nonce the
server printed on its startup line, probes ``http://127.0.0.1:<host_port>/api/stats``
FROM THE HOST, and prints the Bootcamper's URL only when the nonce answered there is
the one printed; a disagreement or an unanswerable probe exits non-zero (INV-260).
Neither issues any container command at all: they read the progress file and make one
HTTP request.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

PROGRESS = os.path.join("config", "bootcamp_progress.json")

DEFAULT_RUNTIME = "docker"

# Container runtimes the bootcamp can start, mapped to the CLI that manages each.
# Deliberately a closed set: an entry naming anything else is reported but never
# acted on, so a hook cannot be made to execute an arbitrary binary named in a
# progress file, and no speculative runtime gets guidance nobody has exercised.
KNOWN_RUNTIMES = {
    "docker": "docker",
    "podman": "podman",
    "container": "container",  # Apple's container CLI (macOS Apple Silicon)
}

# Runtimes whose CLI implements docker's ``ps -a --filter ... --format ...``
# interface, so a container's state can be read. Apple's ``container`` uses a
# different list syntax that this plugin has not verified, so its state is reported
# as unknown rather than guessed at with a command that would merely fail.
STATE_PROBE_RUNTIMES = ("docker", "podman")


def _load_progress():
    try:
        with open(PROGRESS, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def entry_runtime(entry):
    """Return the runtime recorded for an entry, defaulting to ``docker``.

    Legacy entries (a bare name string, or a dict with no ``runtime``) predate
    runtime recording and were all Docker, so they keep behaving exactly as before.
    """
    runtime = ""
    if isinstance(entry, dict):
        runtime = str(entry.get("runtime") or "").strip().lower()
    return runtime or DEFAULT_RUNTIME


def runtime_cli(runtime):
    """Return the path to the CLI managing ``runtime``, or None.

    None means "do not act": either the runtime is not one the bootcamp starts, or
    its CLI is not on PATH. Both are warn-and-continue conditions, never errors.
    """
    cli = KNOWN_RUNTIMES.get(runtime)
    if not cli:
        return None
    return shutil.which(cli)


def tracked_containers():
    """Return the recorded bootcamp-started containers (list of dicts).

    Each returned entry carries at least a ``name`` and a resolved ``runtime``.
    Tolerates a bare list of name strings, and returns ``[]`` when the field is
    absent or unreadable.
    """
    data = _load_progress()
    if not isinstance(data, dict):
        return []
    raw = data.get("docker_containers") or []
    if not isinstance(raw, list):
        return []
    out = []
    for entry in raw:
        if isinstance(entry, str) and entry.strip():
            out.append({"name": entry.strip(), "runtime": DEFAULT_RUNTIME})
        elif isinstance(entry, dict) and entry.get("name"):
            resolved = dict(entry)
            resolved["runtime"] = entry_runtime(entry)
            out.append(resolved)
    return out


def _run(args, timeout=30):
    """Run a container-CLI command, returning (ok, stdout). Never raises."""
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return proc.returncode == 0, (proc.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return False, ""


def stop_started_containers():
    """Stop each recorded container with the CLI that started it (``<cli> stop``,
    never remove) so it can be restarted on resume. Skips any entry whose runtime
    is unknown or whose CLI is unavailable — the hook never reaches for a different
    CLI than the one that started the container. Returns the names for which a stop
    succeeded. Warn-and-continue on every failure; never raises."""
    stopped = []
    for c in tracked_containers():
        name = c.get("name")
        if not name:
            continue
        cli = runtime_cli(entry_runtime(c))
        if not cli:
            continue
        ok, _ = _run([cli, "stop", name])
        if ok:
            stopped.append(name)
    return stopped


def _container_state(name, runtime=DEFAULT_RUNTIME):
    """Return 'running', 'stopped', 'missing', or 'unknown' for a container.

    'unknown' covers every case the probe cannot answer: an unavailable CLI, a
    failing command, or a runtime with no verified ``ps`` interface.
    """
    cli = runtime_cli(runtime)
    if not cli or runtime not in STATE_PROBE_RUNTIMES:
        return "unknown"
    ok, out = _run(
        [
            cli, "ps", "-a",
            "--filter", "name=^%s$" % name,
            "--format", "{{.Names}}\t{{.State}}",
        ]
    )
    if not ok:
        return "unknown"
    for line in out.splitlines():
        parts = line.split("\t")
        if parts and parts[0] == name:
            state = parts[1].strip().lower() if len(parts) > 1 else ""
            return "running" if state == "running" else "stopped"
    return "missing"


def _group_by_runtime(containers):
    """Group container names by recorded runtime, preserving first-seen order."""
    order = []
    grouped = {}
    for c in containers:
        name = c.get("name")
        if not name:
            continue
        runtime = entry_runtime(c)
        if runtime not in grouped:
            grouped[runtime] = []
            order.append(runtime)
        grouped[runtime].append(name)
    return [(runtime, grouped[runtime]) for runtime in order]


def resume_summary():
    """Return a one-paragraph resume message about recorded containers for the
    guide to act on, or '' when there are none. Names the runtime that actually
    started each container, so the message never claims Docker for a container
    Docker did not start. Never raises."""
    groups = _group_by_runtime(tracked_containers())
    if not groups:
        return ""
    clauses = []
    unavailable = []
    for runtime, names in groups:
        # An unrecognized runtime is reported under the name it was recorded with:
        # the guide can act on it even though this module will not run it.
        cli = KNOWN_RUNTIMES.get(runtime, runtime)
        if runtime_cli(runtime) is None:
            unavailable.append(cli)
            clauses.append(
                "`%s`: %s — the `%s` CLI is not available here"
                % (cli, ", ".join(names), cli)
            )
        else:
            states = ["%s (%s)" % (n, _container_state(n, runtime)) for n in names]
            clauses.append("`%s`: %s" % (cli, ", ".join(states)))
    message = (
        "This bootcamp started container(s) — "
        + "; ".join(clauses)
        + ". Offer to restart any that are stopped, or regenerate any that are "
        "missing, before resuming work that needs them."
    )
    if unavailable:
        seen = sorted(set(unavailable))
        message += (
            " For the container(s) whose CLI is unavailable, offer to help the "
            "bootcamper start %s or regenerate them." % " or ".join(seen)
        )
    return message


# ---------------------------------------------------------------------------
# Naming a container before it is created (#461). Everything below is reached only
# through the functions it defines or the ``__main__`` command line; the hooks above
# never call it.
# ---------------------------------------------------------------------------

#: The container-name charset docker and podman enforce. ``<base>`` must already match
#: it, and the slug and hash appended to it keep the result inside it.
NAME_CHARSET = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*\Z")

#: Characters a slug keeps; every run of anything else becomes one ``-``.
_SLUG_DROP = re.compile(r"[^a-z0-9_.-]+")
SLUG_MAX = 32
SLUG_FALLBACK = "project"

#: Suffixes tried, in order, past a name another project's container holds.
CONFLICT_SUFFIXES = tuple(range(2, 10))

#: ``free-port`` tries the preferred port, then this many after it (5432 -> 5433-5531).
PORT_SPAN = 99
LOOPBACK = "127.0.0.1"


def project_slug(project_dir):
    """The readable half of a derived name: the project directory's basename,
    lowercased, each run of characters outside ``[a-z0-9_.-]`` replaced by ``-``,
    leading and trailing ``-_.`` stripped, truncated to 32 characters, or
    ``project`` when nothing is left."""
    base = os.path.basename(os.path.realpath(project_dir)).lower()
    slug = _SLUG_DROP.sub("-", base).strip("-_.")[:SLUG_MAX]
    return slug or SLUG_FALLBACK


def project_hash6(project_dir):
    """The unique half: the first 6 hex characters of SHA-256 over the normcased
    real path (UTF-8), so two projects with the same basename still differ."""
    key = os.path.normcase(os.path.realpath(project_dir))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:6]


def derived_container_name(base, project_dir=None):
    """``<base>-<slug>-<hash6>`` for ``project_dir`` (default: the working directory).

    Raises ``ValueError`` when ``base`` is outside the runtime name charset."""
    if not NAME_CHARSET.match(base or ""):
        raise ValueError("container base name %r is outside [a-zA-Z0-9][a-zA-Z0-9_.-]*" % base)
    if project_dir is None:
        project_dir = os.getcwd()
    return "%s-%s-%s" % (base, project_slug(project_dir), project_hash6(project_dir))


def container_name(base, runtime=DEFAULT_RUNTIME):
    """Choose the name SDK setup creates a container with, from the project root.

    Returns ``(name, how)``. ``how`` is ``"recorded"`` (this project's
    ``docker_containers`` already holds the name, so it is this project's own container
    and is printed unchanged), ``"free"`` (the probe found no container of that name),
    ``"unprobed"`` (the probe could not answer: Apple ``container``, a missing CLI or a
    failing command, so the name is printed as derived), or ``"exhausted"`` with a
    ``None`` name (the derived name and ``-2`` ... ``-9`` all belong to containers this
    project does not record).

    The only container command this issues is ``_container_state``'s read-only
    ``ps``. It never removes, stops, starts or runs anything: a name in use that this
    project does not record is another project's container, and is left alone
    (INV-349).
    """
    derived = derived_container_name(base)
    recorded = {c.get("name") for c in tracked_containers()}
    candidates = [derived] + ["%s-%d" % (derived, n) for n in CONFLICT_SUFFIXES]
    for candidate in candidates:
        if candidate in recorded:
            return candidate, "recorded"
        state = _container_state(candidate, runtime)
        if state == "missing":
            return candidate, "free"
        if state == "unknown":
            return candidate, "unprobed"
    return None, "exhausted"


def _can_bind(port, host=LOOPBACK):
    """Whether a TCP socket can bind ``host:port`` right now.

    Deliberately WITHOUT ``SO_REUSEADDR``: with it, a bind can succeed on a port
    another process is using, which is exactly the answer this must not give."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def free_port(preferred):
    """The preferred port if it can be bound on loopback, else the first of the next
    ``PORT_SPAN`` ports that can, else ``None``."""
    last = min(preferred + PORT_SPAN, 65535)
    for port in range(preferred, last + 1):
        if _can_bind(port):
            return port
    return None


# ---------------------------------------------------------------------------
# Serving a visualization from the SDK container (#460). Host-side only: these read the
# progress file and make one HTTP request to host loopback. They issue no container
# command, not even ``ps``, and they never start, stop or remove anything (INV-349).
# ---------------------------------------------------------------------------

#: The port a visualization server listens on INSIDE the SDK container, always. The
#: container's own network namespace has nothing else on it, and SDK setup publishes
#: ``127.0.0.1:<host_port>`` to it, choosing ``host_port`` with ``free-port 8080``.
VIZ_CONTAINER_PORT = 8080

#: Exit codes shared by ``viz-port`` and ``confirm-viz``. The guide branches on 0 (go
#: on) and 3 (offer to recreate the container); every other code stops the step and
#: relays the message on stderr.
EXIT_OK = 0
EXIT_CONFLICT = 1          # a DIFFERENT server answered the published port
EXIT_NO_HOST_PORT = 3      # the container is recorded, but with no published port
EXIT_UNRECORDED = 4        # this project's docker_containers does not record it
EXIT_NO_ANSWER = 5         # no startup line, no nonce, or the probe could not complete
EXIT_BAD_RECORD = 6        # the recorded host_port is not a TCP port

#: The token every visualization server ends its startup line with (any language).
NONCE_TOKEN = re.compile(r"server_nonce=([A-Za-z0-9._-]+)")
STARTUP_MARK = "Visualization running:"


def recorded_host_port(name):
    """Look up ``name`` in this project's ``docker_containers``.

    Returns ``(code, value)``: ``(EXIT_OK, port)``, ``(EXIT_NO_HOST_PORT, None)`` when the
    entry carries no ``host_port``, ``(EXIT_UNRECORDED, None)`` when no entry has that
    name, or ``(EXIT_BAD_RECORD, raw)`` when the recorded value is not a TCP port.
    """
    for entry in tracked_containers():
        if entry.get("name") != name:
            continue
        raw = entry.get("host_port")
        if raw is None or raw == "":
            return EXIT_NO_HOST_PORT, None
        try:
            port = int(raw)
        except (TypeError, ValueError):
            return EXIT_BAD_RECORD, raw
        if isinstance(raw, bool) or not 1 <= port <= 65535:
            return EXIT_BAD_RECORD, raw
        return EXIT_OK, port
    return EXIT_UNRECORDED, None


def _record_problem(code, name, raw=None):
    """The stderr message for a ``recorded_host_port`` code other than ``EXIT_OK``."""
    if code == EXIT_NO_HOST_PORT:
        return (
            "%s is recorded with no host_port: it was created before SDK setup published "
            "the visualization port, and a port cannot be published on an existing "
            "container. Ask the Bootcamper whether to recreate it with the port published "
            "(Module 2, \"Publishing the visualization port on the SDK container\", "
            "item 4). Never start a relay or proxy instead.\n" % name)
    if code == EXIT_UNRECORDED:
        return (
            "%s is not in this project's docker_containers. Never act on a container this "
            "project does not record (INV-349); read the SDK container's name from "
            "config/bootcamp_progress.json.\n" % name)
    return ("%s records host_port %r, which is not a TCP port (1-65535). Stop and tell "
            "the Bootcamper; do not guess a port.\n" % (name, raw))


def nonce_from_startup_log(path, wait=0.0, poll=0.5):
    """The nonce on the LAST startup line in ``path``, waiting up to ``wait`` seconds for
    one to appear (the model build runs before the server binds). ``None`` when no
    startup line carrying ``server_nonce=`` turned up in time."""
    deadline = time.monotonic() + max(wait, 0.0)
    while True:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            lines = []
        for line in reversed(lines):
            if STARTUP_MARK in line:
                found = NONCE_TOKEN.search(line)
                if found:
                    return found.group(1)
                break
        if time.monotonic() >= deadline:
            return None
        time.sleep(poll)


def probe_published_viz(host_port, nonce, timeout=5.0):
    """Ask ``http://127.0.0.1:<host_port>/api/stats``, on the host, which server answers.

    Returns ``(code, answered)``: ``EXIT_OK`` when the answered ``server_nonce`` equals
    ``nonce``, ``EXIT_CONFLICT`` when it differs (or is absent), ``EXIT_NO_ANSWER`` when
    the request could not complete. A probe that cannot complete is a failure, never a
    pass: the failure this gate exists for looks exactly like success.
    """
    url = "http://%s:%d/api/stats" % (LOOPBACK, host_port)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - any failure here must stop the handover
        return EXIT_NO_ANSWER, "%s: %s" % (type(exc).__name__, exc)
    answered = body.get("server_nonce") if isinstance(body, dict) else None
    if answered == nonce:
        return EXIT_OK, answered
    return EXIT_CONFLICT, answered


def bootcamper_url(host_port):
    """The URL handed to the Bootcamper: always built from the recorded ``host_port``."""
    return "http://localhost:%d" % host_port


def _port_number(text):
    value = int(text)
    if not 1 <= value <= 65535:
        raise argparse.ArgumentTypeError("%s is not a TCP port (1-65535)" % text)
    return value


def main(argv=None):
    """The ``python3 docker_lifecycle.py <subcommand>`` entry point. Returns an exit code."""
    parser = argparse.ArgumentParser(
        prog="docker_lifecycle.py",
        description="Name a bootcamp container, or pick its host port, before creating it; "
                    "read and check the SDK container's published visualization port.")
    sub = parser.add_subparsers(dest="command")
    named = sub.add_parser(
        "container-name", help="print the project-derived name to create a container with")
    named.add_argument("base", help="the site's base name, e.g. senzing-bootcamp")
    named.add_argument("--runtime", default=DEFAULT_RUNTIME, type=str.lower,
                       choices=sorted(KNOWN_RUNTIMES),
                       help="the CLI that will create the container (default: docker)")
    port = sub.add_parser("free-port", help="print a free host loopback port")
    port.add_argument("preferred", type=_port_number, help="the port to try first, e.g. 5432")
    viz_port = sub.add_parser(
        "viz-port", help="print the host_port recorded for a container (exit 3: none recorded)")
    viz_port.add_argument("name", help="the SDK container's recorded name")
    confirm = sub.add_parser(
        "confirm-viz",
        help="probe the published visualization port from the host and print the URL "
             "only if the server answering is the one just started")
    confirm.add_argument("name", help="the SDK container's recorded name")
    source = confirm.add_mutually_exclusive_group(required=True)
    source.add_argument("--nonce", help="the server_nonce the server printed")
    source.add_argument("--log", help="the server's output file, to read the startup line from")
    confirm.add_argument("--wait", type=float, default=0.0,
                         help="seconds to wait for the startup line in --log (default: 0)")
    confirm.add_argument("--timeout", type=float, default=5.0,
                         help="seconds the HTTP probe may take (default: 5)")
    args = parser.parse_args(argv)

    if args.command == "container-name":
        if not NAME_CHARSET.match(args.base):
            sys.stderr.write("container-name: %r is not a valid container name base.\n" % args.base)
            return 2
        name, how = container_name(args.base, args.runtime)
        if name is None:
            derived = derived_container_name(args.base)
            sys.stderr.write(
                "container-name: %s and %s-2 ... %s-9 are all in use by containers this "
                "project's docker_containers does not record. Nothing was removed, stopped "
                "or reused. Ask the Bootcamper how to proceed; do not invent a name.\n"
                % (derived, derived, derived))
            return 1
        if how == "unprobed":
            sys.stderr.write(
                "container-name: could not check whether %s is in use (the %s CLI is "
                "unavailable, failed, or has no verified ps). If creating it fails because "
                "the name is taken, append -2, -3 ... yourself and tell the Bootcamper; never "
                "remove or stop the existing container.\n" % (name, args.runtime))
        print(name)
        return 0

    if args.command == "free-port":
        found = free_port(args.preferred)
        if found is None:
            sys.stderr.write(
                "free-port: no port from %d to %d can be bound on %s. Ask the Bootcamper "
                "how to proceed.\n"
                % (args.preferred, min(args.preferred + PORT_SPAN, 65535), LOOPBACK))
            return 1
        print(found)
        return 0

    if args.command in ("viz-port", "confirm-viz"):
        code, value = recorded_host_port(args.name)
        if code != EXIT_OK:
            sys.stderr.write("%s: %s" % (args.command, _record_problem(code, args.name, value)))
            return code
        host_port = value
        if args.command == "viz-port":
            print(host_port)
            return EXIT_OK
        nonce = args.nonce
        if nonce is None:
            nonce = nonce_from_startup_log(args.log, wait=args.wait)
            if nonce is None:
                sys.stderr.write(
                    "confirm-viz: no startup line carrying server_nonce= appeared in %s "
                    "within %gs. The server did not finish starting, or does not print its "
                    "nonce; read the log, and do not hand over any URL.\n"
                    % (args.log, args.wait))
                return EXIT_NO_ANSWER
        code, answered = probe_published_viz(host_port, nonce, timeout=args.timeout)
        if code == EXIT_NO_ANSWER:
            sys.stderr.write(
                "confirm-viz: nothing answered http://%s:%d/api/stats from the host (%s). "
                "The server started inside %s, but the published port does not reach it. "
                "Do not hand over the URL, and do not start a relay; report this to the "
                "Bootcamper.\n" % (LOOPBACK, host_port, answered, args.name))
            return code
        if code == EXIT_CONFLICT:
            sys.stderr.write(
                "confirm-viz: host port %d is answered by a DIFFERENT server.\n"
                "  started:     %s\n"
                "  answered by: %s\n"
                "The page at that URL would show the other server's data under this "
                "project's title. Do not hand over the URL; stop and report the conflict "
                "(INV-260).\n"
                % (host_port, nonce, answered or "(no server_nonce in the response)"))
            return code
        print(bootcamper_url(host_port))
        return EXIT_OK

    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
