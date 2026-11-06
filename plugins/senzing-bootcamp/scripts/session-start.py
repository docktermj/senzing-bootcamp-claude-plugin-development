#!/usr/bin/env python3
"""SessionStart hook: to resume an in-progress bootcamp by injecting resume context.

Also folds any in-progress module recap checkpoint into docs/bootcamp_recap.md on
resume, so a module that was interrupted (quit / compaction / prior session) keeps
its in-progress narrative in the recap (see recap_checkpoint.py).

When the recorded module has not begun (`current_step` null), the resume message also
carries the module-start apparatus reminder, built by module_start_apparatus.py (#851,
INV-420): the INV-102 form for graduation, nothing for an apparatus-exempt module or a
resume partway through a module.

The resume message names the recorded module by its display name, from
``module_start_apparatus.DISPLAY_NAMES`` (#874), and gives the pinned form of the offer
("Where you left off: {name}, step {N}."), so the guide never improvises it from a skill
heading that carries a module number (INV-079). A key it does not know gets the generic
wording, with no name and no number.

Cross-platform: invoked as a ``type: command`` hook whose ``command`` names the
interpreter and this script, quoted (``python3 "<path>"``), per INV-052. Python is already a hard bootcamp dependency (the graduation recap PDF always
runs under python3; the Truth Set visualization server also does when the chosen language is
Python).
"""
import re
import sys

import docker_lifecycle
import module_start_apparatus
import recap_checkpoint

#: A step value safe to print in the resume line: a number with an optional letter or
#: decimal part ("11", "4a", "2.5"). Anything else is left out of the line, so a hand-edited
#: progress file cannot put arbitrary text, a module number included, in front of the guide.
STEP = re.compile(r"^\d+[a-z]?(?:\.\d+)?$")


def resume_offer():
    """The opening of the resume message, naming the recorded module by its display name
    (#874, INV-079) when its key is known; otherwise the generic wording, which names no
    module and no number."""
    module, step = module_start_apparatus.recorded_position()
    name = module_start_apparatus.display_name(module)
    if name is None:
        return ("A Senzing bootcamp is in progress. Read config/bootcamp_progress.json "
                "and offer to resume from the last recorded module before doing anything "
                "else.")
    where = "Where you left off: %s" % name
    if not isinstance(step, bool) and isinstance(step, (int, str)) \
            and STEP.match(str(step).strip()):
        where += ", step %s" % str(step).strip()
    return ("A Senzing bootcamp is in progress. Read config/bootcamp_progress.json "
            "and offer to resume from the last recorded module, %s, before doing anything "
            "else. Name it by that name in the offer, never by a module number or its "
            "state token (INV-079), in the form bootcamp-onboarding/SKILL.md step 2 pins: "
            "\"%s.\"" % (name, where))


if recap_checkpoint.bootcamp_active():
    folded = recap_checkpoint.fold_checkpoint()
    # Fold first, then guarantee the file exists for the module about to resume.
    recap_checkpoint.ensure_checkpoint()
    message = resume_offer()
    if folded:
        message += (
            " An in-progress module recap checkpoint was found and folded into "
            "docs/bootcamp_recap.md (source: docs/progress/recap_checkpoint.md). "
            "Continue that module and finalize its recap section on completion."
        )
    else:
        message += (
            " No in-progress recap narrative was found to fold. Keep "
            "docs/progress/recap_checkpoint.md current at each step boundary of the "
            "resumed module — it is the only copy that survives a compaction."
        )
    containers = docker_lifecycle.resume_summary()
    if containers:
        message += " " + containers
    # A module recorded but not begun (current_step null) starts with its apparatus; the
    # reminder is built in one place, shared with module-start-reminder.py (INV-300).
    apparatus = module_start_apparatus.resume_reminder()
    if apparatus:
        message += " " + apparatus
    print(message)

sys.exit(0)
