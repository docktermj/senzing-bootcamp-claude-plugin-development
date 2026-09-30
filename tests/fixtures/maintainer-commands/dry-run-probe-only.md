---
description: Fixture for the command-to-skill guard (an alias whose stem differs from its skill); not a shipped command.
argument-hint: ""
---

Fixture only. `tests/test_dev_commands_name_a_real_skill.py` reads this file while no command
ships under `.claude/commands/`. Claude Code never loads it: it is not under `.claude/commands/`.

Invoke the `dry-run` skill and follow it end to end, running phase 1 only.
