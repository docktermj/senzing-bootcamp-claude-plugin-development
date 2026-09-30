# unattended-issue-loop: this repository's overlay

**The governing copy is `~/.claude/skills/unattended-issue-loop/SKILL.md`** (INV-337), the user-level
skill. This file is the **repo overlay**: only the obligations this repository adds on top of
the governing copy, which reads this file and must meet everything below.

⚠️ **The governing copy is not checked in CI.** It lives under `~/.claude/skills/`, outside
this repository, and a CI runner checks out only the repository. The tests here assert this
overlay and `docs/FAMILY_WORKFLOW.md`; nothing here establishes what the governing copy says
on any machine (INV-308).

The loop's merge policy and its label gate are stated in the
[`docs/FAMILY_WORKFLOW.md`](../../docs/FAMILY_WORKFLOW.md) §2 row for `unattended-issue-loop`
(INV-300), and are not restated here.

## Every worker also meets the implement overlay

Each worker follows `implement-github-issue`, so
[`.claude/skill-overlays/implement-github-issue.md`](implement-github-issue.md) binds every issue the
loop works: the INV-309 invariant capture, the MCP re-check, the `specs/IMPLEMENTED.md` ledger
entry, `citations.py verify` after the entry, and this repository's local CI mirror. ⛔ **(INV-309) Put
that file in every worker's brief.** On 2026-09-28 those obligations reached the workers only
because the lead copied them in by hand.

⚠️ **The preflight's CI-mirror probe runs the same mirror**, including the empty-`HOME` legs
that overlay describes. Its `.github/workflows/*.yaml` extension applies here too.

## What an unattended run may create

⛔ **An unattended run creates only the records on this list, and only on the issue it is
working** (INV-314; scope note pending at `/review-invariants`, #216). INV-314's registered
text still says *create nothing*; the pending note makes the maintainer's `unattended-ok`
label assent, given in advance, to exactly these acts on that issue:

1. the four `/implement-github-issue` log comments (Started, Clarifications, Approach, Result);
2. one blocked comment, plus removing `unattended-ok`;
3. pushing that issue's branch and opening its PR;
4. merging that PR and deleting its branch, unless the run was started with `--no-merge`.

It creates nothing else: no new issue, no comment on any other issue, no `submit_feedback`,
and it never adds `unattended-ok`. Each of those is drafted in the handoff and the ledger
instead, marked **not filed**; an upstream message carries the `Upstream:` value the
`submit_feedback` rule below gives.

## What an unattended run must never decide in this repository

- ⛔ **(INV-309) Never sign off an invariant — and declining to mint one is NOT declining to ship the
  rule.** That distinction is the 2026-08-17 defect exactly. When an implementation ships a
  hard rule, ship it **and** write an explicit `DEFERRED INVARIANT` block in the ledger entry
  naming the rule, the site, and the drafted `INV-NNN — <statement>` wording, so the
  maintainer's return costs one yes. ⛔ **(INV-309) Never `_None yet._`, never silence.**
- ⛔ **(INV-314) Never call `submit_feedback`.** An `mcp-server`-routed finding goes in the handoff with
  the message drafted and its `Upstream:` line reading *"not yet sent — needs maintainer
  approval"*.
- ⛔ **(INV-332) Never decline** — that is the maintainer's alone. An issue you cannot implement is
  **blocked**, a state you record on the issue, never an entry you write into
  `specs/DECLINED.md`.
- ⛔ **(INV-307) Write nothing under `specs/` except the issue's own `specs/IMPLEMENTED.md`
  entry.** Every other file there is a frozen archive, and `specs/INVARIANTS.md` changes only
  through `/review-invariants`.

⚠️ **The handoff leads with what needs a yes**: every `DEFERRED INVARIANT` with its drafted
wording, and every drafted upstream message.
