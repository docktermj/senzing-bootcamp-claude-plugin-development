---
name: implement-github-issue
description: Pointer stub, not a procedure. The governing copy is ~/.claude/skills/implement-github-issue/SKILL.md; this repository's own obligations are the overlay in .claude/commands/implement-github-issue.md. Maintainer tool — not part of the bootcamper experience.
disable-model-invocation: true
---

# implement-github-issue (pointer stub)

This file carries **no procedure**. It exists so the command that fronts it names a skill that
resolves in this repository (INV-303), and so a reader who opens it is sent to the right place.

- **Governing copy:** `~/.claude/skills/implement-github-issue/SKILL.md`, the user-level skill.
  It is the procedure that runs, however the command is invoked.
- **Repo overlay:** [`.claude/commands/implement-github-issue.md`](../../commands/implement-github-issue.md)
  holds only what this repository requires on top of the governing copy: invariant capture
  (INV-309), the `specs/IMPLEMENTED.md` ledger entry, `citations.py verify`, the MCP re-check
  and the local CI mirror. The governing copy is told to read it.
- **Family rule:** [`docs/FAMILY_WORKFLOW.md`](../../../docs/FAMILY_WORKFLOW.md) R8 and the §2
  row for `implement-github-issue`.

⚠️ **The governing text is not checked in CI.** It lives under `~/.claude/skills/`, outside this
repository, and a CI runner checks out only the repository. The tests here assert this stub,
the overlay and `docs/FAMILY_WORKFLOW.md`; nothing here establishes what the governing copy
says on any machine (INV-308).

⛔ **Do not put procedure back in this file.** Until #215 this file was a second, full copy of
the skill. It drifted from the copy that runs, and it claimed a byte-for-byte shared block that
the user-level copy no longer had. A rule that binds only this repository belongs in the
overlay; anything else belongs in the governing copy.
