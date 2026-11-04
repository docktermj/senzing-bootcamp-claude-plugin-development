#!/usr/bin/env python3
"""UserPromptSubmit hook: to remind the guide of the module-start apparatus when a module
is about to start (#851).

The apparatus (banner, journey map, before/after framing, step overview, time estimate,
model/effort nudge) is stated in ``ground-rules.md`` and in every content module's
``**First:**`` line, and one session still skipped it at five of eight module starts. This
hook puts a reminder into the guide's context at the moment it is due, so compliance does
not depend on recalling a rule from a skill file not yet read. It never blocks, and the
reminder tells the guide not to mention it, so the bootcamper never sees it.

Gates, checked in order; every failed gate is silent (exit 0, no stdout):
  1. ``recap_checkpoint.bootcamp_active()``: a transition question exists only after a
     module is recorded (INV-227).
  2. The payload is a JSON object with a string ``transcript_path`` naming a readable,
     UTF-8 transcript.
  3. The previous turn has settled on a final assistant message: not a tool call, not a
     tool result. Sidechain (subagent) and meta records are not the user-facing turn and
     are skipped. The prompt being submitted is skipped if it is already on disk.
  4. That message's last 👉 line is one of the two pinned questions: the transition
     question "Are you ready to move on to the next module: {name}?" (module-completion.md
     Step 4) or the graduation offer (module-completion.md "Reaching graduation").
  5. The module it names is not apparatus-exempt (INV-075, INV-078).

The reply itself is not classified. The reminder is conditional ("only if this reply
accepts starting {name}"), so it is inert on a "not yet" in any phrasing or language. The
module is ``{name}`` as written in the question, not cross-checked against the progress
file. The reminder text is built by ``module_start_apparatus.py``, which ``session-start.py``
also uses, so it is stated once (INV-300).

Biased toward silence like ``stop-nudge.py`` (INV-054): a missed reminder costs less than a
wrong one, so anything undecided is silent and nothing here raises on bad input.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. The JSON on stdout
is ASCII-escaped, so no console code page can break it.
"""
import json
import re
import sys

import module_start_apparatus
import recap_checkpoint

POINTER = "\U0001f449"  # 👉

#: The pinned transition question (INV-079). ``name`` is the module as written.
TRANSITION = re.compile(
    r"Are you ready to move on to the next module:\s*(?P<name>[^?]+?)\s*\?", re.I)

#: The pinned graduation offer.
GRADUATION_OFFER = re.compile(
    r"Would you like to graduate now and generate your production project and recap\s*\?",
    re.I)


def content_of(rec):
    """The message content of a transcript record, or None."""
    msg = rec.get("message")
    return msg.get("content") if isinstance(msg, dict) else None


def message_text(rec):
    """The visible text of a record, from a string or a list ``message.content``."""
    content = content_of(rec)
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
            and isinstance(block.get("text"), str))
    return content if isinstance(content, str) else ""


def is_real_user_prompt(rec):
    """True for a typed prompt; False for a tool-result carrier, which is a ``user`` record
    whose content lists ``tool_result`` blocks and does not start a turn."""
    if rec.get("type") != "user":
        return False
    content = content_of(rec)
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(isinstance(block, dict) and block.get("type") == "tool_result"
                       for block in content)
    return False


def ends_with_tool_use(rec):
    """True when an assistant record's last text-or-tool block is a ``tool_use``."""
    content = content_of(rec)
    if not isinstance(content, list):
        return False
    kinds = [block.get("type") for block in content
             if isinstance(block, dict) and block.get("type") in ("text", "tool_use")]
    return bool(kinds) and kinds[-1] == "tool_use"


def read_records(path):
    """The transcript's JSON-object records, or None if it cannot be read. Bad lines are
    skipped; an undecodable file is unreadable (``UnicodeDecodeError`` is a ValueError)."""
    records = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    records.append(rec)
    except (OSError, ValueError):
        return None
    return records


def previous_final_text(records):
    """The previous turn's final assistant text, or None while it is undecided: nothing
    flushed, or a turn still settling (its last record a tool call or a tool result)."""
    turn = [rec for rec in records
            if rec.get("type") in ("user", "assistant")
            and not rec.get("isSidechain") and not rec.get("isMeta")]
    if turn and is_real_user_prompt(turn[-1]):
        turn.pop()  # the prompt being submitted, already on disk
    if not turn:
        return None
    last = turn[-1]
    if last.get("type") != "assistant" or ends_with_tool_use(last):
        return None
    return message_text(last)


def offered_module(text):
    """The module the message's last 👉 line offers to start, or None."""
    lines = [line for line in text.splitlines() if POINTER in line]
    if not lines:
        return None
    question = lines[-1]
    if GRADUATION_OFFER.search(question):
        return module_start_apparatus.GRADUATION_NAME
    match = TRANSITION.search(question)
    if match:
        name = match.group("name").strip(" *_`")
        return name or None
    return None


# Drain stdin first, whatever the gates decide: a hook that leaves it unread can break the
# writer on some platforms. Read as bytes so a Windows console code page cannot fail the
# decode; json.loads takes UTF-8 bytes directly.
try:
    payload = json.loads(sys.stdin.buffer.read())
except (AttributeError, OSError, ValueError):
    payload = None

# Gate 1: only during an active bootcamp, one whose progress file records a module.
if not recap_checkpoint.bootcamp_active():
    sys.exit(0)

transcript = payload.get("transcript_path") if isinstance(payload, dict) else None
if not isinstance(transcript, str) or not transcript:
    sys.exit(0)  # malformed payload or no transcript -> undecided -> silent
records = read_records(transcript)
if records is None:
    sys.exit(0)  # unreadable transcript -> silent
final_text = previous_final_text(records)
if not final_text:
    sys.exit(0)  # previous turn not settled, or nothing to read -> silent
module = offered_module(final_text)
if module is None:
    sys.exit(0)  # no transition or graduation question -> silent
text = module_start_apparatus.reminder(module)
if not text:
    sys.exit(0)  # apparatus-exempt module -> silent

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": text,
    }
}))
sys.exit(0)
