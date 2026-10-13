#!/usr/bin/env python3
"""Drive a bootcamp walk with two independent Claude processes, and record it.

Process A runs the bootcamp with the plugin loaded. Process B answers as the
Bootcamper. They are separate OS processes with separate contexts, and A is never
told it is under test.

Why two processes rather than one
---------------------------------
``.claude/skills/dry-run/phase3-conversational.md`` forbids self-play for two
reasons. This design answers one and a half of them:

1. *"ground-rules.md forbids fabricating the Bootcamper's response"* — **answered.**
   A fabricates nothing; answers arrive from another process, structurally the same
   as a human typing.
2. *"an assistant that knows it is graded on 👉 discipline will comply"* —
   **answered only by discipline.** A's prompt must never mention the test, the
   invariants, or the linter. Grading happens afterwards, out of band, in
   ``transcript_lint.py``. Put "check INV-005" in A's prompt and you are measuring
   the model's carefulness instead of the plugin's files.

⛔ **What stays unanswered:** a simulated Bootcamper is more cooperative than a real
one — it answers in format, never gets confused, never asks "wait, why?". So this
inherits phase 3's asymmetry rather than fixing it: **findings are trustworthy, a
clean walk is weak evidence.** Personas below are the partial mitigation.

Usage:
    walk.py --project DIR --out transcript.jsonl [--turns 12] [--persona terse]
            [--stop-at-banner "MODULE: SDK SETUP"] [--max-turns 150]

With ``--stop-at-banner`` the walk runs until a turn shows that banner, then
``--turns`` more turns; without it, ``--turns`` turns from the start. Either way
``--max-turns`` caps the walk, and the transcript ends with a ``walk_stop`` event
saying where it stopped and why (``/dry-run`` phase 3's simulated walk reads it).
"""
import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "senzing-bootcamp"

POINTER = "\U0001f449"

# ⛔ Enforced by flag, not by instruction. An unattended run cannot be trusted to
# remember a rule, and both of these reach outside the machine: `submit_feedback`
# files noise upstream under a real name and work email, `download_resource` pulls
# arbitrary payloads.
FORBIDDEN_TOOLS = ("mcp__senzing__submit_feedback", "mcp__senzing__download_resource")

# Different Bootcampers break different things. A single cooperative persona is the
# main reason an automated walk is weaker than a human one, so rotate them.
PERSONAS = {
    "terse": "You answer in as few words as possible — often a single word or "
             "number. You never elaborate and never ask questions.",
    "verbose": "You answer at length, volunteering extra context about your data "
               "and your company that was not asked for.",
    "confused": "You are new to entity resolution. Roughly one answer in three, "
                "you ask a short clarifying question back instead of answering.",
    "impatient": "You try to skip ahead. You often ask to jump straight to loading "
                 "data or seeing results rather than answering the current question.",
    "offscript": "You occasionally answer with something that does not fit the "
                 "question asked, or pick an option number that was not offered.",
}

BOOTCAMPER_BRIEF = """You are role-playing a person taking a hands-on Senzing \
entity-resolution bootcamp inside their terminal. Someone is guiding you.

Your situation: you work at a mid-sized insurance company. You want to find \
duplicate and linked customer records across two systems — a claims database and a \
policy database. You know SQL, you are comfortable in Python, and you are on Linux.

{persona}

Rules:
- Reply with ONLY what you would type. No narration, no stage directions, no
  markdown headers, no meta-commentary about the exercise.
- If you are asked to choose from a numbered list, reply with the number or the
  option text.
- Keep it to a couple of sentences at most.
- Never mention that this is a test or a simulation."""


def banner_seen(banner, text):
    """Whether ``text`` shows ``banner``, ignoring case and runs of whitespace."""
    return " ".join(banner.split()).casefold() in " ".join(text.split()).casefold()


def _claude(args, cwd, stdin_text=None, timeout=600, env=None):
    result = subprocess.run(
        ["claude", *args], cwd=str(cwd), input=stdin_text, timeout=timeout,
        capture_output=True, text=True,
        env={**os.environ, **(env or {})})
    return result


def visible_text(stream_json_text):
    """The assistant text a Bootcamper would have seen, from one -p invocation."""
    parts = []
    for line in stream_json_text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        for block in (event.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
    return "\n".join(p for p in parts if p.strip())


def bootcamper_reply(prompt_text, persona, model, timeout=180):
    """One Bootcamper answer, from a process that has never seen the plugin."""
    brief = BOOTCAMPER_BRIEF.format(persona=PERSONAS[persona])
    args = ["-p", f"The guide just said:\n\n---\n{prompt_text}\n---\n\n"
                  "Reply as yourself, with only what you would type.",
            "--append-system-prompt", brief,
            "--output-format", "text",
            # No tools and no MCP: this process only produces text.
            "--strict-mcp-config",
            "--disallowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "WebFetch", "WebSearch", "Task", "NotebookEdit"]
    if model:
        args += ["--model", model]
    result = _claude(args, cwd=Path.home(), stdin_text="", timeout=timeout)
    reply = (result.stdout or "").strip()
    if not reply:
        return None
    # Strip a leading quote or dash the model sometimes adds.
    return reply.lstrip(">- ").strip()


def run_walk(project, out_path, turns, persona, mcp_config, model, bootcamper_model,
             opening, isolate_config, timeout, max_turns=150, stop_at_banner=None):
    session = str(uuid.uuid4())
    env = {}
    if isolate_config:
        config_dir = Path(project) / ".claude-config"
        config_dir.mkdir(parents=True, exist_ok=True)
        # NOTE: this isolates session state but NOT credentials. Without
        # ANTHROPIC_API_KEY in the environment the child exits "Not logged in".
        env["CLAUDE_CONFIG_DIR"] = str(config_dir)

    base = ["--plugin-dir", str(PLUGIN_DIR),
            "--mcp-config", str(mcp_config), "--strict-mcp-config",
            "--disallowedTools", *FORBIDDEN_TOOLS,
            "--permission-mode", "bypassPermissions",
            "--output-format", "stream-json", "--verbose",
            "--add-dir", str(project)]
    if model:
        base += ["--model", model]

    transcript = []
    message = opening
    # Without a banner the walk is `turns` long; with one, it is open-ended until the
    # banner shows, then `turns` more. `max_turns` caps both.
    limit = max_turns if stop_at_banner else turns
    banner_turn, reason, turn = None, None, 0
    for turn in range(1, max_turns + 1):
        if turn > limit:
            turn -= 1
            reason = (f"start banner at turn {banner_turn}, then --turns {turns}"
                      if banner_turn else f"--turns {turns} reached")
            break
        args = ["-p", message, *base]
        args += ["--session-id", session] if turn == 1 else ["--resume", session]
        result = _claude(args, cwd=project, stdin_text="", timeout=timeout, env=env)
        if result.returncode != 0:
            transcript.append(json.dumps({
                "type": "walk_error", "turn": turn,
                "stderr": (result.stderr or "")[-2000:]}))
            print(f"  turn {turn}: claude exited {result.returncode} — "
                  f"{(result.stderr or '').strip()[:200]}", file=sys.stderr)
            reason = f"claude exited {result.returncode}"
            break

        transcript.extend(
            line for line in result.stdout.splitlines() if line.strip().startswith("{"))
        shown = visible_text(result.stdout)
        print(f"  turn {turn}: {len(shown)} chars"
              f"{' [asks]' if POINTER in shown else ''}")
        if stop_at_banner and banner_turn is None and banner_seen(stop_at_banner, shown):
            banner_turn, limit = turn, turn + turns
            print(f"  turn {turn}: start banner seen; {turns} more turn(s)")

        # ⛔ A walk that never started must not read as a walk that found nothing.
        # `/start-bootcamp` unnamespaced returns "Unknown command", one 32-character
        # turn, no 👉 — which the loop below exits on and the linter then scores as
        # a clean run. Fail loudly instead.
        if turn == 1 and ("Unknown command" in shown or len(shown) < 200):
            Path(out_path).write_text("\n".join(transcript) + "\n", encoding="utf-8")
            raise SystemExit(
                f"walk did not start: turn 1 returned {len(shown)} characters "
                f"({shown.strip()[:120]!r}). Check --opening and --plugin-dir; a "
                "silent non-start would otherwise be reported as a clean run.")

        if POINTER not in shown:
            # Nothing was asked, so there is nothing for the Bootcamper to answer.
            # Stopping here is correct rather than inventing another prompt.
            print(f"  stopping: turn {turn} asked no question")
            reason = "the turn asked no question"
            break

        message = bootcamper_reply(shown, persona, bootcamper_model)
        if not message:
            print("  stopping: the Bootcamper process returned nothing",
                  file=sys.stderr)
            reason = "the Bootcamper process returned nothing"
            break
        transcript.append(json.dumps({"type": "bootcamper", "turn": turn,
                                      "persona": persona, "text": message}))
    else:
        reason = f"--max-turns {max_turns} reached"

    print(f"  stopped after turn {turn}: {reason}")
    transcript.append(json.dumps({"type": "walk_stop", "turn": turn, "reason": reason,
                                  "stop_at_banner": stop_at_banner,
                                  "banner_turn": banner_turn}))
    Path(out_path).write_text("\n".join(transcript) + "\n", encoding="utf-8")
    return len(transcript)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--mcp-config", required=True, type=Path)
    ap.add_argument("--turns", type=int, default=12,
                    help="turns to walk; with --stop-at-banner, turns after it")
    ap.add_argument("--stop-at-banner", default=None,
                    help="walk until a turn shows this banner, then --turns more")
    ap.add_argument("--max-turns", type=int, default=150,
                    help="hard cap on the walk's turns, banner or not")
    ap.add_argument("--persona", default="terse", choices=sorted(PERSONAS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--bootcamper-model", default="claude-haiku-4-5-20251001",
                    help="the Bootcamper only produces short text; a small model "
                         "keeps the walk cheap")
    # Plugin commands are namespaced by plugin name. Bare `/start-bootcamp` comes
    # back "Unknown command", which the walk would otherwise record as a zero-finding
    # clean run — a false pass rather than an error.
    ap.add_argument("--opening", default="/senzing-bootcamp:start-bootcamp")
    ap.add_argument("--isolate-config", action="store_true",
                    help="per-run CLAUDE_CONFIG_DIR (needs ANTHROPIC_API_KEY)")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args(argv)

    if not args.project.is_dir():
        print(f"no such project directory: {args.project}", file=sys.stderr)
        return 2
    lines = run_walk(args.project, args.out, args.turns, args.persona,
                     args.mcp_config, args.model, args.bootcamper_model,
                     args.opening, args.isolate_config, args.timeout,
                     max_turns=args.max_turns, stop_at_banner=args.stop_at_banner)
    print(f"transcript: {args.out} ({lines} events)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
