#!/usr/bin/env python3
"""UserPromptSubmit hook: "to keep the in-progress recap checkpoint durable", and to remind
the guide of a module-completion record still missing once the module has closed.

Guarantees `docs/progress/recap_checkpoint.md` exists while a bootcamp is running,
and reminds the guide to keep it current **before** anything is at risk.

Why this runs per turn rather than at session start. A bootcamp becomes active
partway through a session — `config/bootcamp_progress.json` is written during
onboarding — by which time the SessionStart hook has already run and found no
bootcamp. Only a per-turn hook creates the file within one turn of the bootcamp
starting. The cost is one `os.path.exists` on turns where it already exists.

Why the reminder cannot live only in the PreCompact hook. That hook cannot fire until
a compaction is already under way, which is after the window in which the checkpoint
had to have been written for there to be anything to preserve. A full bootcamp ran ten
modules without the file existing, in a session that had crossed a compaction
boundary. So the reminder is emitted here, once per session, while it can still act.

The missing-record reminder (#858). Module completion's Step 0 catches a required step
that never ran, but only the model's attention makes Step 0 itself run. On the Bootcamper's
reply to the transition question or the graduation offer — detected by
``transition_reply.py``, the one detector ``module-start-reminder.py`` also uses — this hook
reads `config/bootcamp_progress.json` for the two records that can still be repaired once
the module has closed:

- ``directing_steps.<token>`` unset for a directing module in ``modules_completed``
  (ground-rules.md -> "Directing steps", INV-354);
- a ``steer_triggers`` entry with ``"kind": "reversal"`` and ``"filed": false``, in any
  module (ground-rules.md -> "Worked steers", INV-352; INV-373);
- a failed program run that ``failed-run-net.py`` observed in an Act 2 hands-on module
  (``config/steer_observations.json``) while that module's ``steer_triggers`` has no entry
  (#910): trigger 1 fired and was never recorded.

It names each one and tells the guide to repair it silently: record ``skipped``, and file
the reversal, and record the observed failure. A missing worked steer is not checked: the checkpoint that would show a steer
was cleared by module completion's Step 2d. It stays with module completion's Step 0 (#856) and
``transcript_lint`` (#857). The reminder is not conditional on the reply: module
completion's Step 1 has closed the module whatever the answer (INV-413). A record the guide
leaves unrepaired is named again at the next transition.

Non-blocking and silent apart from these reminders: the checkpoint's own status goes
to stderr (see recap_checkpoint.py), never to stdout, which for this event carries a
structured JSON payload. When both fall on one turn, they share one ``additionalContext``.
Anything undecided — a malformed payload, an unreadable transcript, a missing, unreadable or
wrongly typed progress file — adds no missing-record reminder, and nothing here raises.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. The JSON on stdout
is ASCII-escaped, so no console code page can break it.
"""
import json
import os
import sys

import recap_checkpoint
import transition_reply

PROGRESS = os.path.join("config", "bootcamp_progress.json")
OBSERVATIONS = os.path.join("config", "steer_observations.json")

#: The modules with a directing step, as their name tokens (ground-rules.md -> "Directing
#: steps"; the three modules with a `**You directed:**` line, module-completion.md Step 2b).
DIRECTING_MODULES = ("data_quality_mapping", "data_processing", "query_visualize_discover")

#: The longest piece of a reversal's evidence quoted back into the reminder.
EVIDENCE_LIMIT = 200

CHECKPOINT_ANNOUNCEMENT = (
    "The bootcamp's in-progress recap checkpoint now exists at "
    "docs/progress/recap_checkpoint.md (created empty). Keep it current: at "
    "each step boundary -- not per sub-step -- write the module's "
    "accumulating Information Shared / Questions & Responses / Actions Taken "
    "/ End-of-Module Summary-so-far between its "
    "<!-- RECAP-CHECKPOINT:START --> and <!-- RECAP-CHECKPOINT:END --> "
    "markers. This is the only copy that survives a quit, compaction, or new "
    "session mid-module; the PreCompact, SessionEnd and SessionStart hooks "
    "fold whatever is in it into docs/bootcamp_recap.md, and fold nothing "
    "while it holds only its scaffold. Finalize and clear it on module "
    "completion (module-completion.md step 2d). Do not mention this file to "
    "the bootcamper and do not let it interrupt the current step."
)


def _progress():
    """The progress file as a dict, or None. Never raises."""
    try:
        with open(PROGRESS, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def unset_directing_steps(progress):
    """The directing modules in ``modules_completed`` whose ``directing_steps`` value is
    unset, in DIRECTING_MODULES order. Empty when either key has the wrong type."""
    completed = progress.get("modules_completed")
    steps = progress.get("directing_steps", {})
    if not isinstance(completed, list) or not isinstance(steps, dict):
        return []
    return [token for token in DIRECTING_MODULES
            if token in completed and steps.get(token) in (None, "")]


def unfiled_reversals(progress):
    """``(module token, evidence)`` for every reversal entry with ``filed`` false, in file
    order. A wrongly typed ``steer_triggers``, list or entry is skipped."""
    triggers = progress.get("steer_triggers")
    if not isinstance(triggers, dict):
        return []
    found = []
    for token, entries in triggers.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if (isinstance(entry, dict) and entry.get("kind") == "reversal"
                    and entry.get("filed") is False):
                evidence = entry.get("evidence")
                evidence = evidence if isinstance(evidence, str) else ""
                if len(evidence) > EVIDENCE_LIMIT:
                    evidence = evidence[:EVIDENCE_LIMIT].rstrip() + "..."
                found.append((str(token), evidence))
    return found


def _observations():
    """``config/steer_observations.json`` as a dict, or ``{}``. Never raises."""
    try:
        with open(OBSERVATIONS, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def unrecorded_failures(progress, observed):
    """``(module token, evidence)`` for every failure ``failed-run-net.py`` observed in a module
    whose ``steer_triggers`` has no entry, in file order (#910). A wrongly typed
    ``steer_triggers`` reads as decided: nothing is named."""
    triggers = progress.get("steer_triggers", {})
    if not isinstance(triggers, dict):
        return []
    found = []
    for token, entry in observed.items():
        if not isinstance(entry, dict) or triggers.get(token):
            continue
        evidence = entry.get("evidence")
        evidence = evidence if isinstance(evidence, str) else ""
        if len(evidence) > EVIDENCE_LIMIT:
            evidence = evidence[:EVIDENCE_LIMIT].rstrip() + "..."
        found.append((str(token), evidence))
    return found


def missing_record_reminder(progress, observed=None):
    """The reminder naming each missing record and its repair, or ``""`` when none is
    missing."""
    directing = unset_directing_steps(progress)
    reversals = unfiled_reversals(progress)
    failures = unrecorded_failures(progress, observed or {})
    if not directing and not reversals and not failures:
        return ""
    items = ["directing_steps.%s is unset, and %s is in modules_completed" % (token, token)
             for token in directing]
    items += ['steer_triggers.%s has a reversal with "filed": false (evidence: "%s")'
              % (token, evidence) for token, evidence in reversals]
    items += ['steer_triggers.%s has no entry, but a generated program failed when it ran '
              'in that module (evidence: "%s")' % (token, evidence)
              for token, evidence in failures]
    repairs = []
    if directing:
        repairs.append(
            "set each unset directing_steps value named above to skipped in "
            "config/bootcamp_progress.json, as module-completion.md Step 0a would have "
            "(ground-rules.md -> \"Directing steps\"), and do not run the directing step late")
    if reversals:
        repairs.append(
            "file each unfiled reversal named above through feedback.md -> \"Silent in-run "
            "append\", whose last step sets its filed to true; a filing that fails leaves it "
            "false and blocks nothing (INV-373)")
    if failures:
        repairs.append(
            "add each failure named above to steer_triggers as {\"kind\": \"failure\", "
            "\"evidence\": <the evidence named>} (ground-rules.md -> \"Worked steers\"); its "
            "module has closed, so show no steer late")
    return (
        "Module-completion records still missing: %s. Module completion has already "
        "closed these modules, so repair the records now, silently and before anything else "
        "in this turn: %s. Ask no question for this, do not mention it to the bootcamper, "
        "and do not rewrite any completed recap section. Then handle the bootcamper's reply "
        "as usual." % ("; ".join(items), "; then ".join(repairs))
    )


# Drain stdin first, whatever the gates decide: a hook that leaves it unread can break the
# writer on some platforms. Read as bytes so a Windows console code page cannot fail the
# decode; json.loads takes UTF-8 bytes directly.
try:
    payload = json.loads(sys.stdin.buffer.read())
except (AttributeError, OSError, ValueError):
    payload = None

if not recap_checkpoint.bootcamp_active():
    sys.exit(0)

created = recap_checkpoint.ensure_checkpoint()

context = []

# Announce the checkpoint once per session, on the turn the file is created. On every
# later turn this announcement is silent, so it never competes with the current step's
# pending question (INV-012).
if created:
    context.append(CHECKPOINT_ANNOUNCEMENT)

# On a reply to the transition question or the graduation offer, name any record module
# completion left missing (#858).
if transition_reply.offered_module(payload) is not None:
    progress = _progress()
    if progress is not None:
        reminder = missing_record_reminder(progress, _observations())
        if reminder:
            context.append(reminder)

if context:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n\n".join(context),
        }
    }))

sys.exit(0)
