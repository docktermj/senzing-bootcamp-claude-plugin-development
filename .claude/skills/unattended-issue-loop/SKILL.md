---
name: unattended-issue-loop
description: Pointer stub, not a procedure. The governing copy is ~/.claude/skills/unattended-issue-loop/SKILL.md; this repository's own obligations are the overlay in .claude/commands/unattended-issue-loop.md. Maintainer tool — not part of the bootcamper experience.
disable-model-invocation: true
---

# unattended-issue-loop (pointer stub)

This file carries **no procedure**. It exists so the command that fronts it names a skill that
resolves in this repository (INV-303), and so a reader who opens it is sent to the right place.

- **Governing copy:** `~/.claude/skills/unattended-issue-loop/SKILL.md`, the user-level skill.
  It is the procedure that runs, however the command is invoked.
- **Repo overlay:** [`.claude/commands/unattended-issue-loop.md`](../../commands/unattended-issue-loop.md)
  holds only what this repository requires on top of the governing copy. The governing copy is
  told to read it.
- **Merge policy and label gate:** the [`docs/FAMILY_WORKFLOW.md`](../../../docs/FAMILY_WORKFLOW.md)
  §2 row for `unattended-issue-loop` states them (INV-300). They are not restated here.

⚠️ **The governing text is not checked in CI.** It lives under `~/.claude/skills/`, outside this
repository, and a CI runner checks out only the repository. The tests here assert this stub,
the overlay and `docs/FAMILY_WORKFLOW.md`; nothing here establishes what the governing copy
says on any machine (INV-308).

⛔ **Do not put procedure back in this file.** Until #215 this file described a different loop
(implement-then-audit cycles, local-only by default) from the one that runs, and the tests
checked it. A rule that binds only this repository belongs in the overlay; anything else
belongs in the governing copy.
