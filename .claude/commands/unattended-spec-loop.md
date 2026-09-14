---
description: Work the specs/ backlog to empty while the maintainer is away, alternating implement and audit, then hand off (maintainer tool).
argument-hint: "[push policy: local | each-cycle | at-end] [max cycles, default 5]"
---

Maintainer request: work the `specs/` backlog unattended.

Invoke the `unattended-spec-loop` skill and follow it end to end.

Run parameters: $ARGUMENTS

- If `$ARGUMENTS` **names a push policy**, take it as answered and do not re-ask.
- ⛔ **If `$ARGUMENTS` is empty and the maintainer is still here, ask the push policy now** —
  local-only, push each cycle, or push once at the end. **Committing is not publishing;
  pushing unreviewed unattended work is.**
- ⛔ **If they are already gone, default to LOCAL ONLY.** Silence is not consent to publish.
- A trailing number caps the cycles; otherwise the skill's five stands.

**Ask the other pre-departure questions while they are still here**, because each changes what
the run does: any spec whose acceptance criteria are conditional on their choice — an unset
priority, two viable designs, an explicit *"if the maintainer chooses"* — and how long "a
while" is, if they offer it. ⚠️ **Do NOT ask which specs to implement.** *"As many as you can"*
is the whole instruction, and re-asking wastes the one turn they are still present for.

**Decide these yourself, without asking:** which spec to take next (highest priority, ties to
the most self-contained), how to implement within the acceptance criteria, skipping a spec that
proves unimplementable unattended, and reverting your own work when the suite cannot be brought
green.

⛔ **Never sign off an invariant — and declining to mint one is NOT declining to ship the
rule.** That distinction is the 2026-08-17 defect exactly. When an implementation ships a hard
rule, ship it **and** write an explicit `DEFERRED INVARIANT` block in the ledger entry naming
the rule, the site, and the drafted `INV-NNN — <statement>` wording, so the maintainer's return
costs one yes. ⛔ **Never `_None yet._`, never silence.**

⛔ **(INV-282) Check for uncited hard rules with a SET DIFFERENCE between
`since --since-last-audit` and `per-rule --uncited` — never a grep for phrases you expect.** A
grep can only confirm lines you already thought of, and the uncited ones are by construction
the ones you did not — that is what the check is *for*. This has produced a wrong ledger claim
**twice**. Run it **before** writing the entry, not after. Every line it reports is then either
cited at the line or named in a deferral; silence is neither.

⛔ **Never call `submit_feedback`.** An `mcp-server`-routed finding gets a spec whose
`Upstream:` line reads *"not yet sent — needs maintainer approval"*, with the message drafted
and ready. **Nothing leaves the machine unattended.**

⛔ **Never decline a spec** — that is the maintainer's alone. A spec you cannot implement is
**blocked**, which is a state you record, never a file you edit into `DECLINED.md`.

⛔ **Never relax an assertion, delete a test, or narrow a guard to reach green.** If a test
fails, either the change is wrong or the test pinned a wrong premise — both are findings. **A
suite made green by weakening it is the one outcome worse than a red suite, because it reads as
success.** ⛔ Never rewrite history, force-push, or amend a previous cycle's commit, and never
delete or overwrite a spec file — check whether it exists before writing, and read it if it does.

**Per cycle:** when the open set is empty or every remainder is blocked, run the audit and
follow it. ⚠️ **The audit reports and files specs; it does not fix in place** — the next
implement pass is the fixing half, so do not collapse the two. ⛔ **Commit the audit record on
its own, BEFORE the next cycle's implementations.** Its hash becomes the next
`--since-last-audit` range start, and a record sharing a commit with the work makes that range
begin at the work, report `0 hard-rule lines added`, and the consumer guard **skip** — going
green by not running, with nobody watching in a loop.

**Stop** when an audit produces no new specs (the success condition), at the cycle cap, when
every remaining spec is blocked, when the suite cannot be brought green on a revert, or when
the MCP server is unreachable and every remaining spec asserts a Senzing fact.

⛔ **State lives in git, `specs/` and `IMPLEMENTED.md` — never in the conversation.** A long
unattended run *will* be compacted, and anything held only in context is already gone. The
handoff leads with **what needs a yes** — every deferred invariant with its drafted wording and
every drafted upstream message — then what is committed against hashes with the start commit,
what is blocked and the question that unblocks each, the audit verdict per cycle on the four
properties separately, the suite and tree state, and ⛔ **what you got wrong.** An unattended
run is trusted on its self-report or not at all.
