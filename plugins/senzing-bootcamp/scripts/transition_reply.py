#!/usr/bin/env python3
"""Shared detector: is the prompt being submitted a reply to the module transition question?

Two ``UserPromptSubmit`` hooks act on the Bootcamper's reply to the pinned transition question
("Are you ready to move on to the next module: {name}?", module-completion.md Step 4) or the
graduation offer (module-completion.md "Reaching graduation"):

- ``module-start-reminder.py`` (#851) reminds the guide of the module-start apparatus;
- ``checkpoint-tick.py`` (#858) reminds the guide of a required record module completion left
  missing.

Both detect that reply here, so there is one detector and the two cannot disagree about
which turn is a transition (#858). ``offered_module(payload)`` is the entry point; the record
helpers below it are what it is built from.

How the reply is recognized, gate by gate; every failed gate returns None:
  1. The payload is a JSON object with a string ``transcript_path`` naming a readable,
     UTF-8 transcript.
  2. The previous turn has settled on a final assistant message: not a tool call, not a
     tool result. Sidechain (subagent) and meta records are not the user-facing turn and
     are skipped. The prompt being submitted is skipped if it is already on disk.
  3. That message's last 👉 line is one of the two pinned questions.

The reply itself is not classified: what each hook does with a "not yet" is its own
decision. Biased toward silence like ``stop-nudge.py`` (INV-054): anything undecided returns
None, and nothing here raises on bad input.

This is NOT a hook. Python puts each hook script's own directory (this ``scripts/``
directory) on ``sys.path``, so ``import transition_reply`` resolves here on Linux, macOS and
Windows alike. Standard library only (INV-052).
"""
import json
import re

import module_start_apparatus

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


def offered_module_in(text):
    """The module the message's last 👉 line offers to start, or None. The graduation offer
    gives ``module_start_apparatus.GRADUATION_NAME``."""
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


def offered_module(payload):
    """The module the previous turn's transition question or graduation offer named, when
    the prompt being submitted replies to one; otherwise None. ``payload`` is the hook's
    parsed stdin, of any type."""
    transcript = payload.get("transcript_path") if isinstance(payload, dict) else None
    if not isinstance(transcript, str) or not transcript:
        return None  # malformed payload or no transcript -> undecided
    records = read_records(transcript)
    if records is None:
        return None  # unreadable transcript
    final_text = previous_final_text(records)
    if not final_text:
        return None  # previous turn not settled, or nothing to read
    return offered_module_in(final_text)
