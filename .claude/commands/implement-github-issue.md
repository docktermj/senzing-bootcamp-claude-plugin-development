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

## ⛔ Re-verify every Senzing fact against the live MCP server before changing code

⛔ **(INV-080) A Senzing fact carried from the issue into the code without re-asking the
server is a guess with a citation on it.** The Senzing MCP server ships **independently of
this plugin**, so an issue's facts may be stale, already fixed, or now contradicted — and an
issue filed weeks ago is exactly the case. Re-ask before changing anything, and record the
outcome on the ledger entry's `MCP re-check` line: the server version, the date, the tools
called, and one of — still reproduces | fixed upstream | server now contradicts the plugin |
server does not cover it | n/a (no Senzing fact) | unverified (MCP unreachable).

⚠️ **`n/a (no Senzing fact)` is a real answer and must be re-confirmed, not assumed.** Most
repo-apparatus work genuinely asserts nothing about Senzing; say so explicitly rather than
omitting the line.

⛔ **(INV-213) An absence claim is a blocker until it names the route that owns the fact.**
Where the diagnosis rests on the server *lacking* something — "returns no X", "does not
cover", "no MCP tool answers this" — the `MCP re-check` line MUST also carry
`owner-checked: <the route that would CARRY this fact> — <what it returned>`. **The tools you
asked and found empty are evidence about those tools, never about the negative:**
"`sdk_guide(topic='configure')` returns no license variable" is true and worthless as support
for "no license variable exists", because the variable lives in
`sdk_guide(topic='load', record_count=<above the limit>)`. Treat a missing clause as a
**blocker** and re-diagnose rather than implement — an absence concluded from the wrong route
has already, once, become a registered invariant plus a guard enforcing it, with the offline
suite certifying both.

⚠️ **Where re-verification changes what the issue asked for, say so** rather than silently
implementing the corrected version. The next reader needs to know the issue and the change
differ, and why.

## Step 4: Record the implementation

Write the `specs/IMPLEMENTED.md` entry — what changed, the `MCP re-check` outcome, and the
invariant answer the gate above requires.

⛔ **Run `citations.py verify` AFTER the entry is written, never before.** Naming the command
without the ordering is what already failed: a run took the scan during its criterion walk,
wrote the entry afterwards, and the entry was what broke it — while the run had already
recorded the scan as clean.

⚠️ **The reason, because without it the ordering reads as ceremony and gets optimized away:**
the **ledger is inside the corpus** the scan reads. A clean result obtained before the entry
exists measured a different repository than the one that ships.

⛔ **A count is not a result.** One run recorded "1792 passed, 3 skipped" from a
`Ran 1792 tests` line while `FAILED (failures=1, skipped=3)` sat directly beneath it — a red
suite ledgered as green, and the figure became a baseline later work was checked against.
**Read the runner's verdict line, not its count.**

## Declining an issue instead of implementing it

Some issues are correct and still should not be built — most often because the change they
propose is an architectural decision rather than a defect repair. That outcome needs
recording in `specs/DECLINED.md`, or the subject returns and the reasoning against it is lost.

⛔ **Never decline on your own initiative.** This command implements what the maintainer
chooses; deciding *not* to build something is theirs alone. If an issue looks like a poor
idea, say so and let them rule — do not write to `DECLINED.md` without their explicit
decision. ⚠️ This is distinct from the escape hatch above: *invalid, duplicate, or already
fixed* is a finding about the world and is reported; *declined* is a decision about what to
build and is the maintainer's.

When they do decline one, append an entry using the same `## <name>` heading idiom as
`IMPLEMENTED.md`:

```markdown
## <issue-slug>

- **Declined:** YYYY-MM-DD
- **Decided by:** <who made the call>
- **Reason:** <why not — required; never leave this empty>
- **Revisit if:** <the condition that would reopen it, or "nothing foreseeable">
```

Two fields carry the weight. **Reason** is required because an unreasoned decline is
indistinguishable from nobody having looked, and the next run looks again. **Revisit if**
keeps the file from becoming a graveyard — most declines are made against current
architecture or a current upstream gap, and naming the trigger lets a later run check
cheaply instead of re-arguing.

⛔ **(INV-217) An absence claim in a `Revisit if:` clause or a dated revisit note carries the
same `MCP-NEGATIVE` marker — this file needs it most, not least.** A declined item is never
implemented, so the re-verification above never re-asks its facts: a negative written here is
**the only Senzing claim in the repo with no re-verification path**, while the record tells
the next reader to trust it *over* the original citations. Write the marker on the same
bullet as the claim:

```markdown
- **Revisit if:** Senzing documents a self-service route for <X>.
  MCP-NEGATIVE: search_docs(query='<terms>') — no indexed document names <X> — owner: search_docs IS the corpus route the condition is written against, so the empty result is the answer rather than a miss (absence negative) — server <version>, <YYYY-MM-DD>
```

`coverage_reports.py negatives` scans `specs/DECLINED.md` and no other file under `specs/`
for exactly this reason, so a marker here reaches the worklist a dry run re-asks;
`tests/test_declined_ledger.py` fails on an absence-shaped bullet that has none. Prose that
**quotes a retracted claim** is exempt and must say so on the bullet with
`MCP-NEGATIVE-SCAN: quoted-history`, so a correction can restate what it corrects.

⚠️ **`specs/DECLINED.md` stays live and writable** even though the rest of `specs/` is a
read-only archive (INV-307). It is a record of decisions, not a backlog.

**Declined is not superseded.** An issue whose facts are wrong, or that a later issue
overtakes, is closed with that reason — not given a `DECLINED.md` entry.

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
