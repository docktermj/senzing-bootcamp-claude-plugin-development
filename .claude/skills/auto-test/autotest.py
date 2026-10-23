#!/usr/bin/env python3
"""Run one sandboxed auto-test of the Senzing Bootcamp plugin (maintainer tool).

Builds an isolated sandbox, runs the MCP checks, optionally walks the bootcamp with
a simulated Bootcamper, lints the transcript, and writes a report. Safe to run many
times a day and concurrently with itself.

Isolation, and why each layer is here
-------------------------------------
* **Project directory** under ``$HOME``, one per run, timestamped. Never ``/tmp``:
  the plugin's own ``write-gate.py`` blocks ``/tmp``, ``/var/tmp`` and
  ``/private/tmp``, so a sandbox there would test the gate instead of the bootcamp.
* **A git worktree pinned to a commit.** You will be editing the repo while runs
  execute; pointing ``--plugin-dir`` at a live tree means a run tests a half-saved
  file and its findings are unattributable. The worktree makes every finding belong
  to a SHA.
* **A per-run MCP config** with ``--strict-mcp-config``, so the run sees the Senzing
  server and nothing else — none of your authenticated claude.ai connectors.
* **A distinct session id** per walk, so concurrent runs never share history.
* **The host's instruction files, by default** (``walk.py``'s
  ``INSTRUCTION_SOURCES``). The bootcamp process reads the sandbox's instruction
  files and none of the host user's, so a rule in ``~/.claude/CLAUDE.md`` is not
  obeyed by the guide and then scored as the plugin's behavior. It leaves
  ``CLAUDE_CONFIG_DIR`` alone, so this costs no credentials.
  ⛔ **(INV-379) A walk that could read a host instruction file MUST say so in its
  report, naming the file and its path** -- a contaminated run must never read as a clean
  one (#733).
* **Optional ``CLAUDE_CONFIG_DIR``** (``--isolate-config``). Isolates session state
  but NOT credentials — it needs ``ANTHROPIC_API_KEY`` or the child exits
  "Not logged in". It is not what isolates instructions.

When the walk fails
-------------------
⛔ **(INV-376) A walk that ended abnormally MUST be reported as a failure of the run rather than as a
coverage limit: the run exits non-zero for it, and the walk's stderr is printed whenever the
walk failed, whatever its stdout held.** A 68-turn walk died mid-turn, and this file filed it
as "the walk produced no transcript" and exited 0 -- while ``walk.stdout or walk.stderr``
short-circuited on 68 turn lines and dropped the traceback that would have named the cause,
which is why that cause is still unknown (#732).

Usage:
    autotest.py                      # MCP checks only (fast, free)
    autotest.py --walk               # + a simulated bootcamp walk
    autotest.py --walk --persona confused --turns 16
    autotest.py --walk --stop-at-banner "MODULE: SDK SETUP"   # walk to a module, then --turns more
    autotest.py --keep               # do not delete the sandbox afterwards
    autotest.py --walk --report-dir DIR   # write the report, transcript and latest.json to DIR

``--report-dir`` defaults to ``~/senzing-autotest/reports``. ``/dry-run --draft <run-dir>``
passes ``<run-dir>/walk/`` so a simulated walk keeps nothing outside its run directory but
this sandbox, which it never keeps (INV-368).
"""
import argparse
import datetime as _dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
SANDBOX_ROOT = Path.home() / "senzing-autotest"
# Reports and transcripts live OUTSIDE the sandbox on purpose. The sandbox is the
# big disposable thing and is removed at the end of every run; the report is the
# only thing the run produced. An earlier version wrote report.json inside the
# sandbox and deleted it moments later, so a scheduled run left no evidence it had
# ever happened.
REPORT_DIR = SANDBOX_ROOT / "reports"
SCAFFOLD = REPO_ROOT / ".claude" / "skills" / "dry-run" / "scaffold_project.py"

MCP_URL = "https://mcp.senzing.com/mcp"


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def make_worktree(root, ref):
    """Pin the plugin under test to a commit, so findings attribute to a SHA."""
    worktree = root / "plugin-src"
    result = _run(["git", "-C", str(REPO_ROOT), "worktree", "add", "--detach",
                   str(worktree), ref])
    if result.returncode != 0:
        print(f"  worktree failed ({result.stderr.strip()[:160]}); "
              "falling back to the live tree — findings will not be "
              "attributable to a commit", file=sys.stderr)
        return REPO_ROOT, None
    sha = _run(["git", "-C", str(worktree), "rev-parse", "HEAD"]).stdout.strip()
    return worktree, sha


def drop_worktree(worktree):
    if worktree and worktree != REPO_ROOT and worktree.exists():
        _run(["git", "-C", str(REPO_ROOT), "worktree", "remove", "--force",
              str(worktree)])


def build_sandbox(root, seed):
    """A realistic project. Uses dry-run's scaffold so fixtures stay in one place."""
    project = root / "project"
    if SCAFFOLD.is_file():
        args = [sys.executable, str(SCAFFOLD), str(project)]
        if seed:
            args.append(f"--{seed}")
        result = _run(args)
        if result.returncode == 0:
            return project
        print(f"  scaffold failed: {result.stderr.strip()[:200]}", file=sys.stderr)
    for sub in ("config", "data/raw", "docs", "logs", "src"):
        (project / sub).mkdir(parents=True, exist_ok=True)
    return project


def write_mcp_config(root):
    path = root / "mcp.json"
    path.write_text(json.dumps(
        {"mcpServers": {"senzing": {"type": "http", "url": MCP_URL}}}, indent=2))
    return path


def instruction_disclosure(transcript):
    """The coverage limit a walk owes the report when a host rule could have shaped it.

    ``walk.py`` records what the bootcamp process could read as the transcript's first
    event. Naming the files is the whole point: a host instruction file is obeyed by the
    guide and then scored against the plugin, so a run that could read one must never read
    as a clean one (#733). Returns ``None`` when there is nothing to disclose.
    """
    try:
        with transcript.open(encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                # The event is the transcript's first line; a few more are read so a future
                # preamble cannot silently drop the disclosure.
                if index > 10:
                    break
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "walk_isolation":
                    continue
                files = event.get("host_instruction_files") or []
                if not files:
                    return None
                return ("the bootcamp process could read host instruction files, so a rule "
                        "of the host's is scored as the plugin's behavior: "
                        + ", ".join(files))
    except OSError:
        return None
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--walk", action="store_true",
                    help="also run a simulated bootcamp walk and lint it")
    ap.add_argument("--turns", type=int, default=12)
    ap.add_argument("--stop-at-banner", default=None,
                    help="walk until this banner shows, then --turns more (walk.py)")
    ap.add_argument("--max-turns", type=int, default=150,
                    help="hard cap on the walk's turns (walk.py)")
    ap.add_argument("--persona", default="terse")
    ap.add_argument("--phase", default="preparation",
                    choices=("preparation", "module0", "content"))
    ap.add_argument("--seed", choices=("fresh", "seeded"), default="fresh")
    ap.add_argument("--ref", default="HEAD", help="commit to pin the plugin at")
    ap.add_argument("--model", default=None)
    ap.add_argument("--keep", action="store_true", help="keep the sandbox")
    ap.add_argument("--report-dir", type=Path, default=REPORT_DIR,
                    help="where the report, the transcript copy and latest.json go "
                         "(default: %(default)s)")
    ap.add_argument("--isolate-config", action="store_true")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    args = ap.parse_args(argv)

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    root = SANDBOX_ROOT / "runs" / f"{stamp}-{args.persona}"
    root.mkdir(parents=True, exist_ok=True)
    print(f"sandbox: {root}")

    report = {"run": stamp, "sandbox": str(root), "persona": args.persona,
              "findings": [], "coverage_limits": []}
    worktree = None
    try:
        worktree, sha = make_worktree(root, args.ref)
        report["plugin_sha"] = sha
        print(f"plugin:  {sha or 'live tree (unpinned)'}")
        if sha is None:
            report["coverage_limits"].append(
                "plugin was not pinned to a commit; a concurrent edit may have "
                "changed the files mid-run")

        mcp_config = write_mcp_config(root)

        # --- MCP: drift, conformance, server quality. Zero tokens. -------------
        print("\n=== MCP checks ===")
        probe = _run([sys.executable, str(SKILL_DIR / "mcp_probe.py"), "check",
                      "--json"])
        if probe.returncode == 2:
            print(f"  probe failed: {probe.stderr.strip()[:200]}", file=sys.stderr)
            report["coverage_limits"].append(
                "the MCP server was unreachable, so no MCP check ran at all")
        else:
            try:
                mcp_findings = json.loads(probe.stdout or "[]")
            except json.JSONDecodeError:
                mcp_findings = []
                report["coverage_limits"].append(
                    "the MCP probe produced unparseable output")
            for finding in mcp_findings:
                finding["source"] = "mcp"
            report["findings"].extend(mcp_findings)
            print(f"  {len(mcp_findings)} finding(s)")

        # --- The walk, and the lint over it -----------------------------------
        if args.walk:
            print("\n=== Bootcamp walk ===")
            project = build_sandbox(root, args.seed)
            transcript = root / "transcript.jsonl"
            walk = _run([sys.executable, str(SKILL_DIR / "walk.py"),
                         "--project", str(project), "--out", str(transcript),
                         "--mcp-config", str(mcp_config), "--turns", str(args.turns),
                         "--persona", args.persona, "--max-turns", str(args.max_turns)]
                        + (["--stop-at-banner", args.stop_at_banner]
                           if args.stop_at_banner else [])
                        + (["--model", args.model] if args.model else [])
                        + (["--isolate-config"] if args.isolate_config else []))
            if walk.stdout.strip():
                print(walk.stdout.rstrip())
            # A traceback goes to stderr, and `stdout or stderr` never reached it: the turn
            # lines had already filled stdout. On a failure the whole of stderr is printed,
            # because a traceback names its exception on the LAST line, so a head-trimmed
            # copy keeps the frames and loses the cause (#732).
            if walk.stderr.strip() and (walk.returncode != 0 or not walk.stdout.strip()):
                print(walk.stderr.rstrip() if walk.returncode != 0
                      else walk.stderr.rstrip()[:400])

            if walk.returncode != 0:
                # A finding of its own, at BREAKING, so the run exits non-zero: a documented
                # path is broken now, and the turns after the stop were never walked (#732).
                tail = walk.stderr.strip().splitlines()
                report["findings"].append({
                    "severity": "BREAKING", "code": "walk-failed", "source": "walk",
                    "message": (
                        f"the walk exited {walk.returncode}, so it stopped before it had "
                        "walked the turns asked of it and everything past that point is "
                        "untested: "
                        + (tail[-1].strip()[:200] if tail else "nothing on stderr")),
                })

            if transcript.is_file() and transcript.stat().st_size > 0:
                # --project: the apparatus check reads the sandbox's verbosity
                # preset, because INV-096 suppresses the time estimate under
                # `minimal` and a check with no notion of the preset reported the
                # guide's conformance as a finding (#734). The sandbox still
                # exists here; it is removed in the `finally` below.
                lint = _run([sys.executable, str(SKILL_DIR / "transcript_lint.py"),
                             str(transcript), "--phase", args.phase,
                             "--project", str(project), "--json"])
                try:
                    lint_findings = json.loads(lint.stdout or "[]")
                except json.JSONDecodeError:
                    lint_findings = []
                for finding in lint_findings:
                    finding["source"] = "transcript"
                report["findings"].extend(lint_findings)
                print(f"  {len(lint_findings)} transcript finding(s)")
            else:
                report["coverage_limits"].append(
                    "the walk produced no transcript, so no interaction invariant "
                    "was checked")

            disclosure = instruction_disclosure(transcript)
            if disclosure:
                report["coverage_limits"].append(disclosure)

            report["coverage_limits"].append(
                "the Bootcamper was simulated, so a clean walk is weak evidence — "
                "findings are trustworthy, clean stretches are not (phase 3)")
            report["artifacts"] = sorted(
                str(p.relative_to(project))
                for p in project.rglob("*") if p.is_file())
        else:
            report["coverage_limits"].append(
                "no walk was run, so no interaction invariant was checked")

        report_dir = args.report_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{stamp}-{args.persona}.json"
        report["report_path"] = str(report_path)
        report_path.write_text(json.dumps(report, indent=2))
        # The transcript is the record/replay artifact: it lets a linter change be
        # re-scored against a real walk without paying for the walk again.
        walk_transcript = root / "transcript.jsonl"
        if walk_transcript.is_file():
            kept = report_dir / f"{stamp}-{args.persona}.transcript.jsonl"
            shutil.copy2(walk_transcript, kept)
            report["transcript_path"] = str(kept)
            report_path.write_text(json.dumps(report, indent=2))
        (report_dir / "latest.json").write_text(json.dumps(report, indent=2))

        print("\n=== Report ===")
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            breaking = [f for f in report["findings"] if f["severity"] == "BREAKING"]
            watch = [f for f in report["findings"] if f["severity"] == "WATCH"]
            for finding in breaking + watch:
                print(f"  [{finding['severity']}] {finding['code']}: "
                      f"{finding['message'][:150]}")
            print(f"\n  {len(breaking)} BREAKING, {len(watch)} WATCH, "
                  f"{len(report['findings'])} total")
            print("\n  Coverage limits:")
            for limit in report["coverage_limits"]:
                print(f"    - {limit}")
            print(f"\n  report: {report_path}")
            if report.get("transcript_path"):
                print(f"  transcript: {report['transcript_path']}")
        return 1 if any(f["severity"] == "BREAKING" for f in report["findings"]) else 0
    finally:
        drop_worktree(worktree)
        if not args.keep and root.exists():
            shutil.rmtree(root, ignore_errors=True)
            print(f"\nsandbox removed (use --keep to retain): {root}")


if __name__ == "__main__":
    sys.exit(main())
