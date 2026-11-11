#!/usr/bin/env python3
"""The one definition of "a failed program run" (#910, INV-352 trigger 1).

A failed program run is a Bash command that builds or runs a project program under one of
`ground-rules.md` -> "Building and running a program"'s ``src/<dir>/`` program directories,
not the env script's ``src/scripts/``, and whose result is an error or a non-zero
``Exit code``. Two readers use it, so it is stated here once (INV-300):

- ``failed-run-net.py``, the ``PostToolUse``/``PostToolUseFailure`` hook that notices the
  failure while the module is still running;
- ``.claude/skills/auto-test/transcript_lint.py``'s ``check_worked_steers``, which grades a
  finished walk.

This is NOT a hook. Python puts each hook script's own directory on ``sys.path``, so
``import failed_run`` resolves here on Linux, macOS and Windows alike. Standard library
only (INV-052). Nothing here raises.
"""
import re

#: A command that builds or runs a program: the tools of `ground-rules.md` ->
#: "Building and running a program".
BUILDS_OR_RUNS = re.compile(r"\b(?:python3?|javac|java|dotnet|cargo|tsc|node)\b")
#: A project file under one of that section's ``src/<dir>`` program directories. The env
#: script under ``src/scripts/`` is not one: every native-Windows call dot-sources it.
PROGRAM_PATH = re.compile(r"(?:^|[\s'\"=:;(,/\\])src[/\\](?!scripts[/\\])\w")
#: Claude Code's Bash result for a non-zero exit begins "Exit code N".
EXIT_CODE = re.compile(r"^\s*(?:Error:\s*)?Exit code (-?\d+)")


def is_program_run(command):
    """Whether ``command`` builds or runs a project program."""
    if not isinstance(command, str):
        return False
    return bool(BUILDS_OR_RUNS.search(command) and PROGRAM_PATH.search(command))


def failed_program_run(command, text, is_error=False):
    """Whether a Bash call running ``command``, whose result text is ``text``, is a failed
    build or run of a project program. ``is_error`` is the tool result's error flag."""
    if not is_program_run(command):
        return False
    exit_code = EXIT_CODE.match(text if isinstance(text, str) else "")
    return is_error is True or bool(exit_code and exit_code.group(1) != "0")
