---
description: Work the GitHub issues labeled unattended-ok while the maintainer is away, taking each to a pull request and then a handoff (maintainer tool).
argument-hint: "[--dry-run] [--no-merge]"
---

Maintainer request: work the labeled issue backlog unattended.

Invoke the `unattended-issue-loop` skill and follow it end to end.

Run parameters: $ARGUMENTS

**The governing copy is `~/.claude/skills/unattended-issue-loop/SKILL.md`**, the user-level
skill; `.claude/skills/unattended-issue-loop/SKILL.md` here is a pointer stub. This file is the
**repo overlay**: only the obligations this repository adds on top of the governing copy, which
reads this file and must meet everything below.

The loop's merge policy and its label gate are stated in the
[`docs/FAMILY_WORKFLOW.md`](../../docs/FAMILY_WORKFLOW.md) §2 row for `unattended-issue-loop`
(INV-300), and are not restated here.

## Every worker also meets the implement overlay

Each worker follows `implement-github-issue`, so
[`.claude/commands/implement-github-issue.md`](implement-github-issue.md) binds every issue the
loop works: the INV-309 invariant capture, the MCP re-check, the `specs/IMPLEMENTED.md` ledger
entry, `citations.py verify` after the entry, and this repository's local CI mirror. ⛔ **Put
that file in every worker's brief.** On 2026-09-28 those obligations reached the workers only
because the lead copied them in by hand.

⚠️ **The preflight's CI-mirror probe runs the same mirror**, including the empty-`HOME` legs
that overlay describes. Its `.github/workflows/*.yaml` extension applies here too.

## What an unattended run must never decide in this repository

- ⛔ **Never sign off an invariant — and declining to mint one is NOT declining to ship the
  rule.** That distinction is the 2026-08-17 defect exactly. When an implementation ships a
  hard rule, ship it **and** write an explicit `DEFERRED INVARIANT` block in the ledger entry
  naming the rule, the site, and the drafted `INV-NNN — <statement>` wording, so the
  maintainer's return costs one yes. ⛔ **Never `_None yet._`, never silence.**
- ⛔ **Never call `submit_feedback`.** An `mcp-server`-routed finding goes in the handoff with
  the message drafted and its `Upstream:` line reading *"not yet sent — needs maintainer
  approval"*.
- ⛔ **Never decline** — that is the maintainer's alone. An issue you cannot implement is
  **blocked**, a state you record on the issue, never an entry you write into
  `specs/DECLINED.md`.
- ⛔ **(INV-307) Write nothing under `specs/` except the issue's own `specs/IMPLEMENTED.md`
  entry.** Every other file there is a frozen archive, and `specs/INVARIANTS.md` changes only
  through `/review-invariants`.

⚠️ **The handoff leads with what needs a yes**: every `DEFERRED INVARIANT` with its drafted
wording, and every drafted upstream message.
