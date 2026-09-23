---
description: Compare the SHARED-RULES block between this repository's skills and their user-level twins, and report any that have drifted.
argument-hint: "(no arguments)"
---

Maintainer request: check whether this repository's skills have drifted from their user-level
twins under `~/.claude/skills/`.

Invoke the `check-skill-drift` skill and follow it.

⛔ **Report what it could not see, not just what it found.** The script prints two blind spots on
every run — a commit made outside a Claude Code session, and an edit to a user-level copy — and
both belong in the answer. A clean result that omits them reads as coverage the check does not
have (INV-308).

⚠️ **Drift in the delimited block is a defect; difference outside it is not.** This repository's
copy cites `docs/FAMILY_WORKFLOW.md` and `specs/INVARIANTS.md`, which do not exist in the
repositories the user-level copy serves. Never "fix" that by copying those citations across.
