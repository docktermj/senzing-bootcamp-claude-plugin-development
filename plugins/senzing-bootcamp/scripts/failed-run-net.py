#!/usr/bin/env python3
"""PostToolUse / PostToolUseFailure hook on Bash: "to catch a failed run of generated code
that got no worked steer" (#910).

A worked steer's trigger 1 is code the AI generated failing when it runs (ground-rules.md ->
"Worked steers", INV-352). Only the guide's attention recorded it: on 2026-11-10 a lookup
program failed at Data processing step 21, the guide repaired it in silence, and no
``steer_triggers`` entry was written, so module completion's Step 0 (#856) and
``checkpoint-tick.py``'s transition reminder (#858) had nothing to read. Only the
after-the-walk lint saw it.

This hook reads the tool's own result. When a Bash call is a failed program run
(``failed_run.py``, the one definition, shared with ``transcript_lint``) in an Act 2 hands-on
module whose ``steer_triggers`` has no entry yet, it:

- records the observation (module token, the evidence line quoted from the output) in
  ``config/steer_observations.json``, a file of its own. It never writes
  ``config/bootcamp_progress.json``: the trigger record stays the guide's to write;
- adds one reminder to the guide's context naming the "Worked steers" rule.

Only the first unrecorded failure of a module is observed and reminded (INV-352: "at most one
per module, and only the first"). ``checkpoint-tick.py`` reads the observation at the
module's transition and names it if ``steer_triggers`` is still empty.

Silent in Act 1 modules, onboarding and graduation, once the module's ``steer_triggers`` has
an entry, once the bootcamp is complete, on a successful run, and on any input it cannot read
decisively. It never blocks and never raises.

Claude Code reports a Bash call that exits non-zero through ``PostToolUseFailure`` (with an
``error`` string) rather than ``PostToolUse`` (with a ``tool_response``), so the hook is
registered on both and reads either shape.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the interpreter
and this script, quoted, per INV-052. The JSON on stdout is ASCII-escaped.
"""
import json
import os
import sys

import failed_run
import module_start_apparatus
import recap_checkpoint

PROGRESS = os.path.join("config", "bootcamp_progress.json")
OBSERVATIONS = os.path.join("config", "steer_observations.json")

#: The Act 2 hands-on modules a worked steer applies to, as state tokens
#: (ground-rules.md -> "Worked steers").
STEER_MODULES = ("data_collection", "data_quality_mapping", "data_processing",
                 "query_visualize_discover")

#: The longest evidence line kept.
EVIDENCE_LIMIT = 200


def _read_json(path):
    """``path`` as a dict, or None. Never raises."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def observations():
    """The observation file as ``{module token: {"evidence": str}}``; empty when it is
    missing or malformed. Never raises."""
    data = _read_json(OBSERVATIONS) or {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, dict)}


def _result(payload):
    """``(command, text, is_error)`` from a PostToolUse or PostToolUseFailure payload, or
    None when it is not a Bash call this hook can read."""
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return None
    if isinstance(payload.get("error"), str):
        return command, payload["error"], True
    response = payload.get("tool_response")
    if isinstance(response, dict):
        parts = [response.get(key) for key in ("stdout", "stderr")]
        text = "\n".join(p for p in parts if isinstance(p, str))
        return command, text, response.get("is_error") is True
    if isinstance(response, str):
        return command, response, False
    return None


def evidence_line(text):
    """The first line of the output that says what failed: the first non-empty line after an
    ``Exit code N`` line, or that line itself when nothing follows."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return ""
    first = lines[1] if failed_run.EXIT_CODE.match(lines[0]) and len(lines) > 1 else lines[0]
    return first[:EVIDENCE_LIMIT]


def reminder(name):
    return (
        "A program the AI generated just failed when it ran, in %s, and no worked steer has "
        "been recorded for this module yet. ground-rules.md -> \"Worked steers\" governs: if "
        "you fix this failure, it is the module's first trigger, so show the module's worked "
        "steer as that section says and record it under steer_triggers in "
        "config/bootcamp_progress.json at the step boundary. If this step's instructions say "
        "to report the failure in one line and continue, follow them: that is not a steer. "
        "Do not apologize, and do not mention this reminder to the bootcamper." % name
    )


def main(payload):
    result = _result(payload)
    if result is None or not failed_run.failed_program_run(*result):
        return
    progress = _read_json(PROGRESS)
    if progress is None or module_start_apparatus.bootcamp_complete():
        return
    module = progress.get("current_module")
    if not isinstance(module, str):
        return
    token = module_start_apparatus.token(module)
    if token not in STEER_MODULES:
        return
    triggers = progress.get("steer_triggers", {})
    if not isinstance(triggers, dict):
        return
    if triggers.get(token):
        return
    seen = observations()
    if token in seen:
        return
    seen[token] = {"evidence": evidence_line(result[1])}
    try:
        with open(OBSERVATIONS, "w", encoding="utf-8") as fh:
            json.dump(seen, fh, indent=2)
            fh.write("\n")
    except OSError:
        pass
    event = payload.get("hook_event_name")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event if event in ("PostToolUse", "PostToolUseFailure")
            else "PostToolUse",
            "additionalContext": reminder(
                module_start_apparatus.display_name(token) or token),
        }
    }))


# Drain stdin first, whatever the gates decide. Read as bytes so a Windows console code page
# cannot fail the decode.
try:
    PAYLOAD = json.loads(sys.stdin.buffer.read())
except (AttributeError, OSError, ValueError):
    PAYLOAD = None

# A worked steer belongs to a recorded module, so the gate is a recorded one (INV-227).
if not recap_checkpoint.bootcamp_active():
    sys.exit(0)

try:
    main(PAYLOAD)
except Exception:  # noqa: BLE001 - a hook never raises
    pass
sys.exit(0)
