#!/usr/bin/env python3
"""UserPromptSubmit hook: to remind the guide of the module-start apparatus when a module
is about to start (#851, INV-420).

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
also uses, so it is stated once (INV-300). Gates 2-4 are ``transition_reply.py``, the one
detector of a reply to the transition question, which ``checkpoint-tick.py`` also uses (#858).

Biased toward silence like ``stop-nudge.py`` (INV-054): a missed reminder costs less than a
wrong one, so anything undecided is silent and nothing here raises on bad input.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. The JSON on stdout
is ASCII-escaped, so no console code page can break it.
"""
import json
import sys

import module_start_apparatus
import recap_checkpoint
import transition_reply


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

# Gates 2-4: the previous turn settled on the transition question or the graduation offer,
# detected once for both hooks that act on that reply (transition_reply.py, #858).
module = transition_reply.offered_module(payload)
if module is None:
    sys.exit(0)  # undecided, or no transition or graduation question -> silent
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
