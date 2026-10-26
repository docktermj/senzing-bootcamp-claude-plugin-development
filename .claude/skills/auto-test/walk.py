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

With ``--stop-at-banner`` the walk runs until a turn shows that banner on a line of its
own (``banner_seen``), then ``--turns`` more turns; without it, ``--turns`` turns from the start. Either way
``--max-turns`` caps the walk, and the transcript ends with a ``walk_stop`` event
saying where it stopped and why (``/dry-run`` phase 3's simulated walk reads it).

Slash lines in a Bootcamper reply (#656)
----------------------------------------
``claude -p`` parses a prompt that starts with ``/`` as a slash command, so a reply of
``/effort high`` then ``yes`` never reached the guide. A leading reply line that is exactly
``/effort <level>`` or ``/model <name>`` (``SLASH_FLAGS``) becomes a sticky ``--effort`` or
``--model`` flag on that turn's ``claude -p … --resume`` call and every later one; the
latest value wins. ``/effort`` itself does not persist under ``-p --resume``, which is why
the flag is re-sent on every call. The rest of the reply is the turn. The ``bootcamper``
event keeps the reply exactly as the Bootcamper process returned it, and a
``bootcamper_flag`` event, which is not a turn, records each flag applied. A reply that is
only slash lines asks the Bootcamper once more with the same guide turn; a second one stops
the walk. Any other reply that starts with ``/``, such as a path, is sent with one leading
space (``as_turn``), which the CLI does not parse as a command. The opening message is
sent as given.

The host's instruction files stay out (#733)
-------------------------------------------
⛔ **(INV-379) The bootcamp process MUST run under instruction files belonging to the run,
never the host's, or the report MUST name the host instruction files it could read.** Phase 3 measures
the guide's literal output, so a host ``~/.claude/CLAUDE.md`` rule such as "end every response
with a 👉 **Suggested next step:** line" is obeyed by the guide and then scored as the
plugin's behavior: one walk filed 13 BREAKING ``INV-251-multi-question`` findings against
plugin text that is correct, and whether a given run was contaminated was not visible in its
report. MCP servers were isolated and instructions were not, one step short of the thing
phase 3 measures.

``INSTRUCTION_SOURCES`` is what keeps them out, on every call and by default. ⛔ **Do not
isolate instructions by moving ``CLAUDE_CONFIG_DIR`` (what ``--isolate-config`` does):** the
user-level instruction file is ``$CLAUDE_CONFIG_DIR/CLAUDE.md``, so relocating that directory
takes the credentials with it and the child exits "Not logged in" without
``ANTHROPIC_API_KEY`` — and the walk that found this defect ran without one.

The settings source does not reach the project layer. On CLI 2.1.310, under
``--setting-sources project,local``, a child still loads ``.claude/CLAUDE.md``, ``CLAUDE.md``,
``CLAUDE.local.md`` and ``.claude/rules/*.md`` from its cwd and every ancestor (#794's probe),
so a child whose cwd is under ``$HOME`` reads the host's ``~/.claude/CLAUDE.md``. Neither
child runs there (#834): ``autotest.py`` puts the run root under the system temp directory,
the guide runs from ``<run root>/project``, and the Bootcamper from ``<run root>/bootcamper``,
an empty directory this file creates beside the project (``bootcamper_dir``).
``readable_host_instructions`` names every such file in either child's cwd or an ancestor,
which is what still reaches a walk on Windows, where the temp directory is under the
user profile.

A crashed walk keeps its transcript (#732)
------------------------------------------
⛔ **(INV-376) A walk's transcript MUST hold every turn the walk completed, whatever ended the walk:
each event is appended to the output file and flushed as it is produced, never held in
memory for one write on the way out.** A ``try/finally`` that writes the whole transcript on
the way out still loses every turn to a ``SIGKILL``, an out-of-memory kill or a pulled plug,
and the walk that produced this rule ran 68 turns over 37 minutes and left nothing at all on
disk.

The closing ``walk_stop`` event is written from a ``try/finally`` around the turn loop, so an
abnormal end is recorded as well as survived; a ``subprocess.TimeoutExpired`` from either
``claude`` call ends the walk with a reason naming the timeout rather than propagating; and
``main`` exits non-zero afterwards, because a walk that ended abnormally is a failure of the
run rather than a run that found nothing.

A ``claude`` child that exits non-zero is the same kind of end (#794). The guide's exit code
used to set a stop reason and no failure, so ``main`` exited 0 and the run read as clean,
and the Bootcamper's exit code was not read at all. Either child's non-zero exit now ends
the walk as a failure, with a ``walk_error`` event (``turn``, ``process``, ``returncode``,
``stderr``) that keeps the child's whole stderr, and the same stderr printed whole to the
console: a cause is usually on the last line, so a cut copy keeps the noise and loses it.
A Bootcamper that exits non-zero is a failure whatever its stdout held, and that stdout is
never sent to the guide; a failure while a slash-only reply is being re-asked ends the walk
at once rather than being re-asked again.
"""
import argparse
import json
import os
import re
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

# ⛔ Instruction isolation, applied to both processes of every walk (#733). The host's
# user-level instruction files are dropped by naming the setting sources the run keeps;
# `CLAUDE_CONFIG_DIR` is left alone, so the host's credentials still resolve and a walk still
# runs with no `ANTHROPIC_API_KEY`. The sandbox project's own instruction files are kept on
# purpose: they are part of what the walk is testing.
INSTRUCTION_SOURCES = ("--setting-sources", "project,local")

# The user-level instruction files a `claude` child reads out of its config directory. A
# contaminated run names the ones that exist rather than claiming the whole set.
USER_INSTRUCTION_FILES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md")

# The project-layer instruction files a `claude` child loads from its cwd and every ancestor,
# isolation or not: exactly what #794's probe showed loading on CLI 2.1.310, plus every
# `*.md` directly in `PROJECT_RULES_DIR`. `AGENTS.md` and `.claude/CLAUDE.local.md` loaded in
# no case, so they are not scanned here (#834).
PROJECT_INSTRUCTION_FILES = (".claude/CLAUDE.md", "CLAUDE.md", "CLAUDE.local.md")
PROJECT_RULES_DIR = ".claude/rules"

# Probed once per process, because the answer cannot change inside one walk and the probe
# costs a `claude --help`. Tests set it directly.
_SUPPORTS_SETTING_SOURCES = None


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
- If you type a slash command such as /effort or /model, put it on its own line,
  before your answer.
- Never mention that this is a test or a simulation."""


# A displayed banner's frame: three of one non-ASCII glyph on each side of the text,
# "🚀🚀🚀  MODULE: SDK SETUP  🚀🚀🚀" (the shape of module_banners.py's BANNER_LINE).
BANNER_FRAME = re.compile(r"^([^\x00-\x7f])\1\1 (.+?) \1\1\1$")


def banner_seen(banner, text):
    """Whether ``text`` shows ``banner`` on a line of its own (#657).

    A line matches when it equals the banner, ignoring case and runs of whitespace, either
    as it stands or once one tripled-glyph frame is stripped. A substring test matched
    prose: "⬜ Bootcamp graduation" in every journey map, and "move on to the next
    module: SDK setup?" one turn before the SDK setup banner. A single leading glyph such
    as ``⬜``, ``✅`` or ``🔄`` is not a frame, and a banner with other words on its line
    does not match.
    """
    wanted = " ".join(banner.split()).casefold()
    for line in text.splitlines():
        line = " ".join(line.split()).casefold()
        framed = BANNER_FRAME.match(line)
        if wanted in (line, framed.group(2) if framed else None):
            return True
    return False


# #656: the slash commands a Bootcamper reply line may carry, each mapped to the CLI flag
# that carries it from then on. Extend here; any other leading `/` is sent as text.
SLASH_FLAGS = {"/effort": "--effort", "/model": "--model"}
SLASH_LINE = re.compile(r"(\S+) (\S+)")


def split_reply(reply):
    """The reply's leading allowlisted slash lines, and the rest of it (#656).

    Returns ``(flags, rest)``: ``flags`` lists ``(line, flag, value)`` for each leading line
    that is exactly ``/effort <level>`` or ``/model <name>``, in order; blank lines between
    them are skipped. ``rest`` is what follows, or the whole reply when it has no such line,
    and is empty for a reply that is only slash lines.
    """
    lines = reply.splitlines()
    flags, index = [], 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        match = SLASH_LINE.fullmatch(stripped)
        if not match or match.group(1) not in SLASH_FLAGS:
            break
        flags.append((stripped, SLASH_FLAGS[match.group(1)], match.group(2)))
    else:
        index = len(lines)
    if not flags:
        return [], reply
    return flags, "\n".join(lines[index:]).strip()


def as_turn(text):
    """``text`` in a form ``claude -p`` reads as a prompt, not as a slash command (#656).

    The CLI parses a prompt that starts with ``/`` as a command (``/help me pick`` never
    reaches the model). One leading space keeps every character of the reply and makes
    the CLI send it as text; checked against CLI 2.1.300.
    """
    return " " + text if text.startswith("/") else text


class EventLog:
    """The transcript, appended event by event and flushed before the next one (#732).

    ``run_walk`` used to hold every event in a list and write the file once, at the end, so
    the two expensive processes could run for 37 minutes and leave an empty directory. The
    flush is the part that matters: it puts each event in the operating system's hands before
    the turn that follows it begins, so an abnormal end costs the turn in flight and nothing
    earlier -- including an end that runs no Python at all, which is the case a ``finally``
    cannot reach.

    ``count`` is the number of events written, which is what ``main`` reports.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w", encoding="utf-8")
        self.count = 0

    def write(self, line):
        """Append one already-serialized JSON event, and flush it."""
        self._handle.write(line + "\n")
        self._handle.flush()
        self.count += 1

    def extend(self, lines):
        for line in lines:
            self.write(line)

    def event(self, **fields):
        self.write(json.dumps(fields))

    def close(self):
        self._handle.close()


def user_config_dir():
    """The directory a ``claude`` child reads its user-level instruction files from."""
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(override) if override else Path.home() / ".claude"


def supports_instruction_isolation(timeout=60):
    """Whether the installed CLI takes ``--setting-sources`` (checked against 2.1.303).

    A CLI that does not would reject the flag and end the walk at turn 1. Walking anyway and
    disclosing the contamination is the better failure: refusing to run at all is exactly
    what ruled ``--isolate-config`` out as a default (#733).
    """
    try:
        result = subprocess.run(["claude", "--help"], capture_output=True, text=True,
                                timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return False
    return INSTRUCTION_SOURCES[0] in (result.stdout or "")


def instructions_isolated():
    """Whether this process can keep the host's instruction files out of a child."""
    global _SUPPORTS_SETTING_SOURCES
    if _SUPPORTS_SETTING_SOURCES is None:
        _SUPPORTS_SETTING_SOURCES = supports_instruction_isolation()
    return _SUPPORTS_SETTING_SOURCES


def instruction_sources():
    """The isolation flags one ``claude`` call carries, or nothing when it cannot."""
    return list(INSTRUCTION_SOURCES) if instructions_isolated() else []


def bootcamper_dir(project):
    """The Bootcamper child's cwd: ``bootcamper/`` beside the project (#834).

    Never ``$HOME`` and never inside the project. ``autotest.py`` makes the project
    ``<run root>/project``, so this is ``<run root>/bootcamper``.
    """
    return Path(project).resolve().parent / "bootcamper"


def project_instruction_files(directory):
    """The project-layer instruction files present in one directory, in a stable order."""
    directory = Path(directory)
    found = [directory / name for name in PROJECT_INSTRUCTION_FILES]
    rules = directory / PROJECT_RULES_DIR
    if rules.is_dir():
        found += sorted(rules.glob("*.md"))
    return [path for path in found if path.is_file()]


def readable_host_instructions(project, isolated):
    """Host instruction files a walk's children can still read, as paths (#733, #834).

    Two layers reach a child. The **user** layer is the config directory's own instruction
    files, which isolation drops. The **project** layer is the child's cwd and every
    directory above it, which isolation keeps and must — the project's own files are part of
    what the walk tests — so a host file there is read either way and belongs in the report
    whichever mode the walk ran in. Both children are scanned: the guide from the project,
    the Bootcamper from ``bootcamper_dir``. Each file is named once, with its path.
    """
    found = []
    if not isolated:
        config = user_config_dir()
        found += [config / name for name in USER_INSTRUCTION_FILES if (config / name).is_file()]
    for cwd in (Path(project).resolve(), bootcamper_dir(project)):
        for directory in (cwd, *cwd.parents):
            found += project_instruction_files(directory)
    named = []
    for path in found:
        if str(path) not in named:
            named.append(str(path))
    return named


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


class BootcamperFailed(Exception):
    """The Bootcamper process exited non-zero (#794); carries its exit code and stderr."""

    def __init__(self, returncode, stderr):
        super().__init__(f"the Bootcamper process exited {returncode}")
        self.returncode = returncode
        self.stderr = stderr or ""


def report_child_failure(log, turn, process, returncode, stderr):
    """Record a ``claude`` child's non-zero exit and print its stderr whole (#794).

    Returns the walk's stop reason. Nothing is cut: the transcript's ``walk_error`` event and
    the console both get every character the child wrote to stderr.
    """
    stderr = stderr or ""
    log.event(type="walk_error", turn=turn, process=process, returncode=returncode,
              stderr=stderr)
    reason = f"the {process} process exited {returncode}"
    print(f"  turn {turn}: {reason}; its stderr follows", file=sys.stderr)
    print(stderr.rstrip() if stderr.strip() else "  (nothing on stderr)", file=sys.stderr)
    return reason


def bootcamper_reply(prompt_text, persona, model, cwd, timeout=180):
    """One Bootcamper answer, from a process that has never seen the plugin.

    ``cwd`` is ``bootcamper_dir(project)``: never ``$HOME``, whose instruction files the CLI
    would load as project memory, and never the project (#834).

    Raises ``BootcamperFailed`` when the process exits non-zero, whatever its stdout held:
    that stdout is never a reply the guide should answer (#794).
    """
    brief = BOOTCAMPER_BRIEF.format(persona=PERSONAS[persona])
    args = ["-p", f"The guide just said:\n\n---\n{prompt_text}\n---\n\n"
                  "Reply as yourself, with only what you would type.",
            "--append-system-prompt", brief,
            "--output-format", "text",
            # No tools and no MCP: this process only produces text. Its instruction files
            # are isolated as well: a host rule shapes what the Bootcamper types back, and
            # what the Bootcamper types is what the next guide turn answers (#733).
            *instruction_sources(),
            "--strict-mcp-config",
            "--disallowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "WebFetch", "WebSearch", "Task", "NotebookEdit"]
    if model:
        args += ["--model", model]
    result = _claude(args, cwd=cwd, stdin_text="", timeout=timeout)
    if result.returncode != 0:
        raise BootcamperFailed(result.returncode, result.stderr)
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

    isolated = instructions_isolated()
    # The Bootcamper's empty cwd, beside the project, made before anything is scanned (#834).
    bootcamper_cwd = bootcamper_dir(project)
    bootcamper_cwd.mkdir(mode=0o700, exist_ok=True)
    base = ["--plugin-dir", str(PLUGIN_DIR),
            "--mcp-config", str(mcp_config), "--strict-mcp-config",
            *instruction_sources(),
            "--disallowedTools", *FORBIDDEN_TOOLS,
            "--permission-mode", "bypassPermissions",
            "--output-format", "stream-json", "--verbose",
            "--add-dir", str(project)]
    # The CLI flags every call carries: --model from the command line, then each sticky
    # flag a Bootcamper slash line set (#656). The latest value of a flag wins.
    flags = {"--model": model} if model else {}

    log = EventLog(out_path)
    # Written before the first turn, so a walk that dies mid-turn still says what it ran
    # under. `autotest.py` reads it and discloses any file named here in the report.
    host_instructions = readable_host_instructions(project, isolated)
    log.event(type="walk_isolation", instructions_isolated=isolated,
              mechanism=" ".join(INSTRUCTION_SOURCES) if isolated else None,
              host_instruction_files=host_instructions)
    print("  instructions: "
          + (f"isolated ({' '.join(INSTRUCTION_SOURCES)})" if isolated
             else "NOT isolated; this CLI has no " + INSTRUCTION_SOURCES[0])
          + (f"; readable host instruction files: {', '.join(host_instructions)}"
             if host_instructions else ""))
    message = opening
    # Without a banner the walk is `turns` long; with one, it is open-ended until the
    # banner shows, then `turns` more. `max_turns` caps both.
    limit = max_turns if stop_at_banner else turns
    banner_turn, reason, turn, failure = None, None, 0, None
    try:
        for turn in range(1, max_turns + 1):
            if turn > limit:
                turn -= 1
                reason = (f"start banner at turn {banner_turn}, then --turns {turns}"
                          if banner_turn else f"--turns {turns} reached")
                break
            args = ["-p", message, *base]
            for flag, value in flags.items():
                args += [flag, value]
            args += ["--session-id", session] if turn == 1 else ["--resume", session]
            try:
                result = _claude(args, cwd=project, stdin_text="", timeout=timeout,
                                 env=env)
            except subprocess.TimeoutExpired as expiry:
                # `subprocess.run` raises this on expiry and nothing used to catch it, so
                # the walk died mid-turn with its whole record in memory (#732). Ending
                # here keeps the transcript and names the cause; `main` exits non-zero.
                failure = reason = f"the guide timed out after {expiry.timeout}s"
                print(f"  stopping: {reason}", file=sys.stderr)
                break
            if result.returncode != 0:
                # A failure, not just a stop: a crashed guide used to end the walk with
                # `main` exiting 0, so the run read as clean (#794).
                failure = reason = report_child_failure(
                    log, turn, "guide", result.returncode, result.stderr)
                break

            log.extend(line for line in result.stdout.splitlines()
                       if line.strip().startswith("{"))
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
                failure = reason = (f"walk did not start: turn 1 returned {len(shown)} "
                                    "characters")
                raise SystemExit(
                    f"{reason} ({shown.strip()[:120]!r}). Check --opening and "
                    "--plugin-dir; a silent non-start would otherwise be reported as a "
                    "clean run.")

            if POINTER not in shown:
                # Nothing was asked, so there is nothing for the Bootcamper to answer.
                # Stopping here is correct rather than inventing another prompt.
                print(f"  stopping: turn {turn} asked no question")
                reason = "the turn asked no question"
                break

            prompt, message = shown, None
            for _attempt in range(2):
                try:
                    reply = bootcamper_reply(prompt, persona, bootcamper_model,
                                             cwd=bootcamper_cwd)
                except subprocess.TimeoutExpired as expiry:
                    failure = reason = ("the Bootcamper process timed out after "
                                        f"{expiry.timeout}s")
                    print(f"  stopping: {reason}", file=sys.stderr)
                    break
                except BootcamperFailed as crash:
                    # Ends the walk at once, even mid-retry, and its stdout is never
                    # sent to the guide (#794).
                    failure = reason = report_child_failure(
                        log, turn, "Bootcamper", crash.returncode, crash.stderr)
                    break
                if not reply:
                    break
                # The reply as the Bootcamper process returned it, slash lines included.
                log.event(type="bootcamper", turn=turn, persona=persona, text=reply)
                applied, rest = split_reply(reply)
                for line, flag, value in applied:
                    flags[flag] = value
                    log.event(type="bootcamper_flag", turn=turn, command=line,
                              flag=flag, value=value)
                    print(f"  turn {turn}: {line} -> {flag} {value} on every later call")
                if rest:
                    message = as_turn(rest)
                    break
                # Only slash lines: nothing to send. Ask once more with the guide's same
                # turn; the Bootcamper process still authors the answer (INV-369).
                entered = "\n".join(line for line, _flag, _value in applied)
                prompt = (f"{shown}\n\n(You entered:\n{entered}\nIt is applied. The guide "
                          "is still waiting for your answer to the message above.)")
            else:
                print("  stopping: the Bootcamper replied only with slash commands",
                      file=sys.stderr)
                reason = "the Bootcamper replied only with slash commands"
                break
            # The Bootcamper call timed out or exited non-zero: its own reason is already
            # set, and the "returned nothing" branch below would overwrite it.
            if failure:
                break
            if not message:
                print("  stopping: the Bootcamper process returned nothing",
                      file=sys.stderr)
                reason = "the Bootcamper process returned nothing"
                break
        else:
            reason = f"--max-turns {max_turns} reached"
    except BaseException as ending:
        # Recorded here and re-raised: the `finally` below writes the `walk_stop`, so an
        # end nothing anticipated reaches the transcript as well as stderr (#732).
        if reason is None:
            reason = f"{type(ending).__name__}: {ending}"
        failure = reason
        raise
    finally:
        print(f"  stopped after turn {turn}: {reason}")
        log.event(type="walk_stop", turn=turn, reason=reason,
                  stop_at_banner=stop_at_banner, banner_turn=banner_turn)
        log.close()
    return log.count, failure


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
    # ⛔ Not what keeps the host's instruction files out: that is on by default and costs
    # no credentials (INSTRUCTION_SOURCES). This isolates session state, and the price of
    # moving CLAUDE_CONFIG_DIR is an API key (#733).
    ap.add_argument("--isolate-config", action="store_true",
                    help="per-run CLAUDE_CONFIG_DIR for session state "
                         "(needs ANTHROPIC_API_KEY; instructions are isolated anyway)")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args(argv)

    if not args.project.is_dir():
        print(f"no such project directory: {args.project}", file=sys.stderr)
        return 2
    events, failure = run_walk(args.project, args.out, args.turns, args.persona,
                               args.mcp_config, args.model, args.bootcamper_model,
                               args.opening, args.isolate_config, args.timeout,
                               max_turns=args.max_turns,
                               stop_at_banner=args.stop_at_banner)
    print(f"transcript: {args.out} ({events} events)")
    if failure:
        # Exiting 0 here is what let a crashed 68-turn walk be filed as a coverage
        # limit by `autotest.py`, which reads this exit code (#732).
        print(f"walk ended abnormally: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
