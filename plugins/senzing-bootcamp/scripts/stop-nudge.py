#!/usr/bin/env python3
"""Stop hook: to nudge for a single closing 👉 question (a safety net). It fires
ONLY when a bootcamp is active AND the model actually forgot the question, and it can
NEVER loop.

Gates, checked in order. The hook stays silent (exit 0, no output) unless every
gate passes:
  1. stop_hook_active is true  -> return success immediately. This is the loop
     breaker: a Stop hook that blocks re-runs on the continuation it caused, so
     without this guard the nudge re-fired every turn until Claude Code hit its
     block cap.
  2. No config/bootcamp_progress.json -> not a bootcamp; never touch unrelated
     sessions. This gate tests the file's EXISTENCE on purpose, not
     recap_checkpoint.bootcamp_active(): existence answers "is this a bootcamp
     project", not "is a bootcamp in progress" (INV-227). The onboarding preface
     creates the file empty and nothing records a module until Bootcamp
     preparation's final write, yet the preface and every preparation gate end on a
     pinned 👉 question, so the net must cover them too (hooks/README.md, Gate column).
  3. The bootcamper opted out (env var or preferences key) -> stay silent. Gives a
     documented way to disable/quiet the nudge (see hooks/README.md).
  3b. The bootcamp is complete (``bootcamp_complete: true`` in preferences, set by
     graduation before the terminal "END OF SENZING BOOTCAMP" banner) -> stay silent,
     so the net never nudges for a closing question after the bootcamp is over.
  4. The current turn already ended with a 👉 question -> the closing question
     exists, so add nothing (honors the "ask each question only once" invariant).

Gate 4 reads the turn's final text from the Stop payload first. Claude Code's Stop
input carries an optional ``last_assistant_message`` ("Text content of the last
assistant message before stopping"); when it is a string, that string is the turn's
final text and the transcript is not read at all. Only when the field is absent (an
older Claude Code) does the gate fall back to reading the transcript, below. The
payload comes first because the transcript loses the race: on 2026-11-06 the final
text record was written about 40 ms before the hook ran and was not yet readable, so
the transcript reading saw a thinking-only record, stayed silent as undecided, and
the net never fired on any of 61 Stop events in the saved auto-test sessions (#873).

Gate 4 detection is deliberately biased toward silence. A blocking Stop hook forces
the model to produce output again, so a false positive is how a bootcamper ends up
seeing the same 👉 question twice — the #1 complaint (zero tolerance). Three defenses
address it: (a) the gate inspects the turn's FINAL assistant message (the payload
field, or in the fallback the last transcript record, handling a string OR list
``message.content``) rather than a concatenation, so an unflushed closing line is not
mistaken for a pointer-less turn; (b) in the transcript fallback it treats a turn
that is still settling as undecided and stays silent — when the last transcript
record is a tool call (an assistant record ending in ``tool_use``) or a tool result
(a ``user`` carrier inside the turn), the closing 👉 message has not been written
yet, which is the partial-flush race seen on tool-using turns; and (c) even if the
hook does block, the block reason tells the model to verify its own last message
first and repeat nothing, so a false block can never surface as a duplicate
question. An empty or whitespace-only final text, from either source, is silent.

The block reason also covers the pause that the net exists to catch: a step that asks
no 👉 question is non-yielding (``ground-rules.md``, INV-225) and the guide may not
originate a 👉 question (INV-247), so the reason tells the model to continue to the
next step that asks rather than add a question to a step that asks nothing.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052.
"""
import json
import os
import sys

POINTER = "\U0001f449"  # 👉


def content_of(rec):
    """The message content of a transcript record, or None."""
    msg = rec.get("message")
    return msg.get("content") if isinstance(msg, dict) else None


def assistant_text(rec):
    """Concatenated visible text of an assistant record. Handles both the list
    (content blocks) and the plain-string shapes of ``message.content``."""
    content = content_of(rec)
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    if isinstance(content, str):
        return content
    return ""


def is_real_user_prompt(rec):
    """True for a genuine user prompt, False for a tool-result carrier record.
    Tool results arrive as ``user`` records whose content is a list of
    ``tool_result`` blocks; those do not delimit a new turn."""
    if rec.get("type") != "user":
        return False
    content = content_of(rec)
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(
            isinstance(block, dict) and block.get("type") == "tool_result"
            for block in content
        )
    return False


def truthy(value):
    """Interpret a string/bool as an on/off flag without a YAML dependency."""
    if isinstance(value, bool):
        return value
    return str(value).strip().strip("\"'").lower() in {"1", "true", "yes", "on"}


def pref_flag(key):
    """True if a top-level ``key: <truthy>`` entry is set in
    config/bootcamp_preferences.yaml. The YAML is scanned line-by-line so no
    third-party parser is required (INV-052: python3-only)."""
    prefs = os.path.join("config", "bootcamp_preferences.yaml")
    try:
        with open(prefs, encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.startswith("#") or ":" not in stripped:
                    continue
                name, _, val = stripped.partition(":")
                val = val.split("#", 1)[0]  # ignore any trailing inline comment
                # top-level key only (no leading indentation)
                if name == key and line[:1] not in (" ", "\t"):
                    return truthy(val)
    except OSError:
        pass
    return False


def nudge_disabled():
    """Honor an explicit opt-out: the SENZING_BOOTCAMP_DISABLE_STOP_NUDGE env var,
    or a top-level ``disable_stop_nudge: true`` key in
    config/bootcamp_preferences.yaml (INV-055)."""
    if truthy(os.environ.get("SENZING_BOOTCAMP_DISABLE_STOP_NUDGE", "")):
        return True
    return pref_flag("disable_stop_nudge")


def bootcamp_complete():
    """True once graduation has ended the bootcamp. The graduation closing step
    sets a top-level ``bootcamp_complete: true`` in config/bootcamp_preferences.yaml
    right before it renders the terminal "END OF SENZING BOOTCAMP" banner (which
    ends the turn with no 👉 question). Standing down here keeps the safety net from
    nudging for a closing question after the bootcamp is over."""
    return pref_flag("bootcamp_complete")


def current_turn_records(transcript_path):
    """Return the transcript records produced since the last real user prompt (the
    current turn), or None if the transcript cannot be read."""
    records = []
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return None

    # Find the last genuine user prompt; the current turn is everything after it.
    start = 0
    for idx, rec in enumerate(records):
        if is_real_user_prompt(rec):
            start = idx + 1
    return records[start:]


def payload_final_text(payload):
    """The turn's final assistant text from the Stop payload's
    ``last_assistant_message``, or None when the field is absent or not a string
    (an older Claude Code), in which case the caller falls back to the transcript.
    An empty string is returned as is: the field is present and says the final
    message has no text, which the caller treats as silent."""
    value = payload.get("last_assistant_message")
    return value if isinstance(value, str) else None


def ends_with_tool_use(rec):
    """True if an assistant record's final content block is a ``tool_use`` — i.e.
    the model just invoked a tool and its post-tool message has not been produced
    yet."""
    content = content_of(rec)
    if isinstance(content, list):
        kinds = [
            block.get("type")
            for block in content
            if isinstance(block, dict) and block.get("type") in ("text", "tool_use")
        ]
        return bool(kinds) and kinds[-1] == "tool_use"
    return False


def settled_final_text(records):
    """The text of the turn's FINAL assistant message when the turn has settled (its
    last action was final text), or None when the turn is still in progress — the
    last record is a tool-result carrier (a ``user`` record inside the turn) or an
    assistant record whose last block is a ``tool_use``, or nothing is flushed yet.
    Sidechain (subagent) records are excluded — they are not the user-facing turn.

    Returning None biases the caller to silence: on a tool-using turn the closing 👉
    line races the transcript write, so treating an unsettled turn as "no decision ->
    stay silent" prevents the partial-flush false nudge (INV-054)."""
    turn = [rec for rec in records if not rec.get("isSidechain")]
    if not turn:
        return None
    last = turn[-1]
    # A trailing tool-result carrier (a ``user`` record within the turn) means the
    # assistant's post-tool message is not written yet -> still in progress.
    if last.get("type") == "user":
        return None
    if last.get("type") == "assistant":
        # The model just invoked a tool; its final text is still pending.
        if ends_with_tool_use(last):
            return None
        return assistant_text(last)
    return None


data = sys.stdin.read()
try:
    payload = json.loads(data)
except ValueError:
    payload = {}
if not isinstance(payload, dict):
    payload = {}

# Gate 1: never re-fire on our own continuation. This alone prevents the block-cap
# loop.
if payload.get("stop_hook_active") is True:
    sys.exit(0)

# Gate 2: only act during an active bootcamp.
if not os.path.isfile(os.path.join("config", "bootcamp_progress.json")):
    sys.exit(0)

# Gate 3: respect an explicit opt-out.
if nudge_disabled():
    sys.exit(0)

# Gate 3b: stand down once the bootcamp is complete. Graduation's terminal
# "END OF SENZING BOOTCAMP" banner ends the turn with no 👉 question on purpose;
# without this the safety net would nudge for one after the bootcamp is over.
if bootcamp_complete():
    sys.exit(0)

# Gate 4: block ONLY when we can positively read the current turn's final assistant
# message AND it ended without a 👉 question. The payload's last_assistant_message is
# read first and is decisive when present: it is the final text as Claude Code holds
# it, with no flush race. Only when it is absent does the gate read the transcript,
# and there every other case biases to silence, because a blocking Stop hook forces
# another turn and a false block is how a duplicate 👉 question reaches the
# bootcamper (the #1 complaint). Undecided -> silent covers: no transcript path, a
# missing/unreadable file, a turn still settling (a pending tool call/result — the
# partial-flush race on tool-using turns), and a turn whose final assistant text is
# not yet flushed.
final_text = payload_final_text(payload)
if final_text is None:
    transcript = payload.get("transcript_path", "")
    records = current_turn_records(transcript) if transcript else None
    if records is None:
        sys.exit(0)  # no readable transcript -> undecided -> stay silent
    final_text = settled_final_text(records)
    if final_text is None:
        sys.exit(0)  # turn still settling (tool call/result pending, or nothing flushed) -> silent
if POINTER in final_text:
    sys.exit(0)  # the final message already carries a 👉 question -> stay silent
if not final_text.strip():
    sys.exit(0)  # final message empty -> stay silent

# All gates passed: block once and ask for the single closing question. Gate 1
# releases on the very next Stop, so this blocks at most one time. The reason makes
# a false block harmless: the model checks its own last message and never repeats a
# question it already asked.
print(json.dumps({
    "decision": "block",
    "reason": (
        "Bootcamp is active. Before doing anything else, re-read your own most "
        "recent message. If it ALREADY ends with a single 👉 closing question, you "
        "have asked it — do NOT ask it again; simply end your turn without "
        "repeating the question. If the step you just presented asks no 👉 "
        "question, it is non-yielding and must not end the turn (the ground rules: a "
        "step with no 👉 question is NON-YIELDING): do not add a question to it; "
        "continue now to the next step that asks one, and let that step's single 👉 "
        "question end the turn. Only if your last message genuinely has no 👉 "
        "closing question, and you just finished a bootcamp step and it is your "
        "turn to yield, add exactly one closing question, prefixed with 👉 and "
        "bolded, inviting the next step. If the bootcamp is complete, add nothing."
    ),
}, ensure_ascii=False))
sys.exit(0)
