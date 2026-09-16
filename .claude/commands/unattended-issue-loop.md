---
description: Work the GitHub issues labeled unattended-ok while the maintainer is away, alternating implement and audit, then hand off (maintainer tool).
argument-hint: "[push policy: local | each-cycle | at-end] [max cycles, default 5]"
---

Maintainer request: work the labeled issue backlog unattended.

Invoke the `unattended-issue-loop` skill and follow it end to end.

Run parameters: $ARGUMENTS

⛔ **It works only issues carrying the `unattended-ok` label** —
`gh issue list --state open --label unattended-ok`. **No label, no work**, and an
unlabeled backlog is a **no-op**: the loop stops and says so rather than guessing which
issues are safe. ⛔ **Never add the label yourself**; selecting the work is the
maintainer's decision, and an unlabeled issue has not been declined — it has not been
*offered*.

- If `$ARGUMENTS` **names a push policy**, take it as answered and do not re-ask.
- ⛔ **If `$ARGUMENTS` is empty and the maintainer is still here, ask the push policy now** —
  local-only, push each cycle, or push once at the end. **Committing is not publishing;
  pushing unreviewed unattended work is.**
- ⛔ **If they are already gone, default to LOCAL ONLY.** Silence is not consent to publish.
- A trailing number caps the cycles; otherwise the skill's five stands.

**Ask the other pre-departure questions while they are still here**, because each changes what
the run does: any labeled issue whose acceptance criteria are conditional on their choice — an unset
priority, two viable designs, an explicit *"if the maintainer chooses"* — and how long "a
while" is, if they offer it. ⚠️ **Do NOT ask which labeled issues to implement** — the label already answered that
is the whole instruction, and re-asking wastes the one turn they are still present for.

**Decide these yourself, without asking:** which labeled issue to take next (highest priority,
ties to the most self-contained), how to implement within the acceptance criteria, skipping one that
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

⛔ **Never call `submit_feedback`.** An `mcp-server`-routed finding gets an issue whose
`Upstream:` line reads *"not yet sent — needs maintainer approval"*, with the message drafted
and ready. **Nothing leaves the machine unattended.**

⛔ **Never decline** — that is the maintainer's alone. An issue you cannot implement is
**blocked**, which is a state you record, never a file you edit into `DECLINED.md`.

⛔ **Never relax an assertion, delete a test, or narrow a guard to reach green.** If a test
fails, either the change is wrong or the test pinned a wrong premise — both are findings. **A
suite made green by weakening it is the one outcome worse than a red suite, because it reads as
success.** ⛔ Never rewrite history, force-push, or amend a previous cycle's commit, and never
write into `specs/` at all — it is a read-only archive (INV-307).

**Per cycle:** when the open set is empty or every remainder is blocked, run the audit and
follow it. ⛔ **The audit half is BLOCKED** while `/production-readiness-audit` still writes
spec files into the frozen archive: run the implement half only and stop after one cycle,
recording that in the handoff. ⚠️ **The audit reports; it does not fix in place** — the next
implement pass is the fixing half, so do not collapse the two. ⛔ **Commit the audit record on
its own, BEFORE the next cycle's implementations.** Its hash becomes the next
`--since-last-audit` range start, and a record sharing a commit with the work makes that range
begin at the work, report `0 hard-rule lines added`, and the consumer guard **skip** — going
green by not running, with nobody watching in a loop.

**Stop** when an audit files nothing new (the success condition), at the cycle cap, when
every remaining labeled issue is blocked, when the suite cannot be brought green on a revert,
or when the MCP server is unreachable and every remaining labeled issue asserts a Senzing fact.
⛔ **Stop immediately when no issue carries the label** — that is a no-op, not a failure.

⛔ **State lives in git, the issue tracker and `IMPLEMENTED.md` — never in the conversation.** A long
unattended run *will* be compacted, and anything held only in context is already gone. The
handoff leads with **what needs a yes** — every deferred invariant with its drafted wording and
every drafted upstream message — then what is committed against hashes with the start commit,
what is blocked and the question that unblocks each, the audit verdict per cycle on the four
properties separately, the suite and tree state, and ⛔ **what you got wrong.** An unattended
run is trusted on its self-report or not at all.
