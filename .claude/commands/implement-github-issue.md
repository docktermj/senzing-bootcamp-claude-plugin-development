---
description: Take a GitHub issue from reported to pull-request-open on a dedicated branch, documenting every decision on the issue (maintainer tool).
argument-hint: "[GitHub issue URL, owner/repo#n, or bare number] (omit to be asked which issue)"
---

Maintainer request: implement a GitHub issue end to end.

Invoke the `implement-github-issue` skill and follow it end to end.

Issue to implement: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, ask which issue and stop until answered. Do not choose one.
- If `$ARGUMENTS` **names an issue** — a full URL, `owner/repo#n`, or a bare number against
  this repo — resolve it and begin.

⛔ **This command never merges.** No `gh pr merge`, no commit to `main`, no force-push, and
nothing leaves the machine before Gate 2. It stops at "pull request open for review".

**Two approval gates, and silence is not approval at either.** Gate 1 presents the readiness
verdict, the clarifications and the chosen approach before any code is written; Gate 2
presents the diff, the tests and the local CI mirror before anything is pushed. Everything
between them runs unattended.

## ⛔ (INV-309) Invariant capture is a gate on closing, not a step to remember

**An issue MUST NOT be closed until the work either registers an invariant or writes an
explicit `DEFERRED INVARIANT` block in `specs/IMPLEMENTED.md`.** Stating "establishes no
invariant" is the third permitted answer and is equally explicit. Silence is not.

⚠️ **This is not hypothetical.** #38 found **four durable guarantees that shipped with
enforcing tests and no registered invariant, inside eleven days**. Moving all development onto
this command raises the volume passing through that gap, so the omission is made impossible
here rather than left for `/review-invariants` to notice later.

⛔ **This command cannot register an invariant.** Minting an ID is the maintainer's alone, so
the run's obligation is to write the block — the rule it shipped, its drafted wording, and the
enforcer — and leave the verdict to `/review-invariants`. Write the ID as `INV-NNN`: a literal
number would cite an invariant that does not exist and turn `citations.py verify` red.

⚠️ **`pending_invariants.py check` may report `0 rule quotes checked` for a block written
here, and that zero is not a clean check** — it resolves a rule's location only under
`plugins/`, while issue-driven rules usually live in `tests/`, `.claude/` or `specs/`. Verify
the wording by reading the enforcer's assertions instead (#59).

## Scope note: `PARENT_VERSION`

In **child** repositories this command also updates `PARENT_VERSION` when a parity issue
closes. ⛔ **That clause is deliberately unimplemented here**: this is the parent repository
and `PARENT_VERSION` exists nowhere in it, so there is no referent to act on and nothing to
test it against. Recorded so a future reader sees a scoped decision rather than an omission,
and so whoever ports this command to a child knows the clause is owed there.

## What the issue log must contain

Exactly four comments across a full run, so the issue reads as a log rather than a chat
stream: **started** (branch and what will be implemented), **clarifications** (the consolidated
Q&A plus every assumption taken without asking), **approach** (only when implementations were
raced — otherwise fold a one-line note into the result), and **result** (the PR link, the
summary, the test and CI results).

**Never attribute an answer to the issue's author when it came from the maintainer in session**,
and never fabricate one.

## The escape hatch is a real outcome

If the work reveals the issue is invalid, a duplicate, or already fixed: **stop, post what was
found with the evidence, and say so.** Do not manufacture a change to justify the run — an
unnecessary pull request is worse than no pull request.
