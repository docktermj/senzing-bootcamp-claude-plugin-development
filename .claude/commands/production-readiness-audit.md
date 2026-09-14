---
description: Audit the whole plugin for consistency, coherence, completeness and concision — the last static gate before /dry-run (maintainer tool).
argument-hint: "[area to scope the invariant sweep to] (omit to let the lead generators choose)"
---

Maintainer request: audit the Senzing Bootcamp plugin for production readiness.

Invoke the `production-readiness-audit` skill and follow it end to end.

Sweep scope: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, let the run choose the scope: the invariants the step-3
  generators put hits against, the enumerating subset that rots fastest, everything an
  invariant binds that the diff since the last audit entry touched, and the per-module
  outcome blocks on a rotation.
- If `$ARGUMENTS` **names an area**, sweep that first — and still run every lead generator.
  A scoped run that skips them cannot see what it chose not to look at.

**Establish the baseline before looking at anything.** Confirm the suite is green first: a
red suite means you are debugging, not auditing, and the findings get attributed to the
wrong cause. Then read the newest audit entries in `specs/IMPLEMENTED.md`, listing them
newest-first — the file is newest-first, and a `tail` silently hands back the oldest, which
is how one run was given seven July entries and never saw the previous day's five. They name
what was already found and, most usefully, which defect *classes* recur. Re-deriving a
finding already in the ledger is the most common way to waste a run.

⛔ **A full forward sweep of every invariant is no longer feasible in one run.** Scope it
deliberately and **say what you scoped it to**. A run that implies it swept everything is
reporting something it did not do; an honest disclosure of scope is not a shortfall.

⛔ **The lead generators are leads, not verdicts.** A regex cannot tell a deliberately
restated rule from one that drifted, nor a worked illustration from a cached authority. A run
that reports their counts as findings has run a grep, not an audit. For the same reason, read
every count off the ledger or off the run — never from prose, in the skill file or anywhere
else. A number written into prose goes stale silently while continuing to read authoritative.

**Report before changing.** Present the findings and let the maintainer choose what to fix;
fix in place only when asked. Every prior audit worked this way.

⛔ **The conversational invariants are out of scope and MUST be reported as such.** The
one-question-per-turn rule, asked-once, no-unrequested-skips, the 👉 marker and every gate
ordering rule govern what the model *does in a live turn*. Reading cannot establish them, and
an assistant grading its own discipline proves nothing. Say they are untested and route them
to `dry-run` phase 3. A report that lets them pass silently is a false clean bill of health.

**Never mark a property satisfied that you did not check.** An unexamined area is a disclosed
gap, not a pass.

**`specs/INVARIANTS.md` is append-only.** A new invariant needs the maintainer's sign-off on
the wording, the next unused ID, and an index entry in the same edit. Concision is audited
because the maintainer asked for it, not because a rule binds it — if a run finds concision
defects worth binding, **ask**; do not read one into INV-003. And never cut rationale to make
something shorter: the concision win is merging duplicated statements and moving a rule to
where it is used, never deleting why it exists.

Finish by reporting the findings in severity order, leading with anything that breaks a
documented path rather than with the longest list. **State the verdict on each of the four
properties separately** — "consistent and complete; two coherence defects; concision
unchanged" is information, a single pass/fail is not. Name the spec file each finding was
written into and say which are fixed and which are recorded-but-open. Say briefly what you
verified as correct, so the next audit does not re-check it. ⛔ State the coverage limits
explicitly, including the untested conversational invariants and any path this environment
could not exercise. Report your own mistakes plainly — the methodology's value depends on the
reader trusting the parts that did work.

**Offer `/dry-run` as the next step.** This is the gate before it, never a substitute: static
analysis can only confirm the plugin agrees with itself, and cannot see where it disagrees
with the world.
