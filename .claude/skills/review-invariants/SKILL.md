---
name: review-invariants
description: 'Walk the maintainer through every DEFERRED INVARIANT block in specs/IMPLEMENTED.md one at a time — showing the rules already shipping, the drafted wording, and every site a citation must reach — then ask for a verdict (register / hold / amend) and carry out the mechanical registration for the ones approved. Never signs off an invariant itself. Maintainer tool for developing the Senzing Bootcamp Claude Plugin (SBCP); the counterpart to implement-spec, which produces the deferrals this skill resolves.'
---

# Review Invariants

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It is never invoked during a bootcamp.

A deferred invariant is a **rule that is already shipping** in the plugin, guarded by a
test, and recorded in no invariant. `/implement-github-issue` and `unattended-issue-loop` produce
them by design: minting an invariant is the maintainer's alone, so an implementation that
ships a hard rule writes a `DEFERRED INVARIANT` block instead of registering one. This
skill is where those blocks get decided.

## Why this exists

Deciding one takes about a minute. Registering one correctly takes six steps across four
files, and every one of them has a way to go quietly wrong. On **2026-09-01** two
invariants were registered by hand and the mechanical half produced four separate defects:

- A count of pending blocks taken by **grepping for the phrase** returned 29 against a
  true 11 — ledger prose *about* deferrals matched too.
- A block the maintainer had **already held, twice**, with a recorded revisit condition,
  was presented as awaiting a first decision.
- A rule was cited at the **two sites the deferral listed** when it shipped in **three**;
  the third was named inside another bullet's prose and reached only by scanning.
- The guard checking that deferral quotes match their source **skipped 3 of 17 bullets**
  it could not parse, and reported a clean run over the rest.

None of those is a hard problem. All four are the same problem: the work is repetitive,
the failures are silent, and reading is what is being relied on. So the queue, the sites
and the quote check are computed by `pending_invariants.py`, and this file is the
procedure around them.

⛔ **This skill never signs off an invariant.** It presents, it asks, it waits, and it
executes what the maintainer decided. A verdict the maintainer did not give is not a
default this skill gets to choose — that is the whole reason the deferral exists.

## The three verdicts

Present all three every time. **Two of them are not "no".**

| Verdict | What it means | What happens |
|---|---|---|
| **Register** | The wording is right. | Mint the next free ID, cite it everywhere the rule ships, resolve the block. Permanent. |
| **Hold** | Not yet — and here is what would change that. | The block stays, with the maintainer's **reason and revisit condition** recorded. Not a rejection. |
| **Amend** | The rule is right, the wording is not. | Change the wording first, then register the changed text. |

**Amend includes splitting.** On 2026-08-27 a maintainer review split one draft into two
because it had grown a second subject — what an archive *is*, and what the Bootcamper
*consents to* — and bolting a second subject onto a statement is how the first omission
happened. Two subjects is two invariants.

## ⛔ What approving and disapproving actually differ by

State this in the maintainer's own terms at the first invariant of a session, because the
intuition is wrong in a way that matters:

> **Declining does not remove the rule.** It is already in the plugin, already shipped to
> Bootcampers, and already enforced by a test. Nothing about the product changes either
> way today.

What changes is whether the ruleset **knows about it**:

- **Register** → the guarantee has an address. A later change that contradicts it fails a
  guard or is caught by a conformance sweep, `citations.py verify` can resolve it, and a
  future editor who finds the rule can look up why it exists. The cost: IDs are permanent
  (`INVARIANTS.md` is append-only — never renumbered, never deleted), so a wrong invariant
  gets a dated correction note rather than a removal. Registering a rule whose wording is
  still moving means amending a fresh invariant.
- **Hold** → the rule keeps shipping and the ruleset stays silent about it. Nothing binds
  future work to it, and nothing notices when a later change contradicts it. That is not
  hypothetical: **INV-134** shipped as a guarantee with no invariant and two files then
  cited **INV-076** — an invariant about something else entirely — as its authority.

So the question is never *"is this rule good?"* — it is already shipping either way. The
question is **"is this wording one I am willing to be held to permanently?"** If yes,
register. If the rule is right but the words are still moving, amend. If something has to
happen before the wording can settle, hold and say what.

⚠️ **A hold is worth as much as its revisit condition.** *"Wait"* with nothing attached
comes back to the same question next month with nothing new to weigh. *"Revisit after
`dry-run` phases 2 and 3 have exercised the flow"* is a condition someone can check.

## Step 1: Load the queue

```bash
python3 .claude/skills/review-invariants/pending_invariants.py list
```

It prints the pending blocks numbered, the count, the next free ID, and — separately —
any block that is **held**, with the recorded reason.

⛔ **Never present a held block as awaiting a decision.** It has one. Re-offering it asks
the maintainer to re-derive a decision they already made and recorded, and the reason is
in the spec, not in the ledger, which is why the helper reads both. Mention held blocks
once, as context, and move on. Bring one back only when its revisit condition is **met** —
and say which condition, and what met it.

Then confirm the ledger is honest before quoting it:

```bash
python3 .claude/skills/review-invariants/pending_invariants.py check
```

Every rule quote must appear verbatim in the file it names. A mismatch means the block
quotes something the plugin does not say — truncated, paraphrased, or since reworded — and
**that is not a wording to approve from**. Fix the quote against its source first.

⛔ **(INV-308) Read all four counts, not the mismatch count alone.** `check` reports
`<n> checked, <n> mismatched, <n> unresolved, <n> no-prose-site`:

- **unresolved** — a bullet names a path that does not exist. ⛔ Its quote is **unverified**,
  and this is not a clean check. Fix the path before quoting the block.
- **no-prose-site** — the bullet names no path because the rule is encoded in code or tests
  rather than stated in prose. Legitimate; nothing is owed.
- **checked = 0** — nothing was verified. ⚠️ An **empty** check, not a clean one.

⚠️ Until #59 this printed only the first two counts and skipped the rest without counting
them, so a run that verified nothing read exactly like a run that verified everything — and
was presented to the maintainer as clean in three consecutive reviews.

## Step 2: Present one invariant

One at a time. Do not batch — the maintainer is deciding, not skimming.

```bash
python3 .claude/skills/review-invariants/pending_invariants.py show <n>
python3 .claude/skills/review-invariants/pending_invariants.py sites <n>
```

Present, in this order:

1. **What it is** — the spec it came from, in one line.
2. **The rules already shipping**, verbatim, with their locations. This is the concrete
   thing; the drafted wording is the abstraction over it.
3. **The drafted wording** in full. Never summarize it — it is the text being approved.
4. **Where a citation would land** — `sites` prints three groups. The **named** ones are
   definite; the **prose-named** ones are sites whose bullet nobody wrote and are where
   the misses have been; the **candidates** are leads to read, never sites to cite blind.
5. **Anything the block already rejected.** Several blocks record a near-miss citation
   that was considered and turned down — INV-097 for the multi-select rule, INV-080 and
   INV-149 for the provenance rule. That reasoning is the expensive part and it is already
   written; surface it rather than making the maintainer re-derive it.
6. **What is different if this is held** — in this rule's own terms, not the general form.

Then ask, as **one** question, and stop. Register / hold / amend.

## Step 3: Carry out the verdict

### Register

⛔ **Read the ID again, now.** Do not carry a number from Step 1 or from the block text —
several deferrals are pending and **only the first one minted gets the ID any of them
would have named**. Every block writes `INV-NNN` deliberately for this reason.

```bash
python3 .claude/skills/review-invariants/pending_invariants.py next-id
```

Then, per `INVARIANTS.md`'s own maintenance rules:

1. **Index entry and invariant in ONE edit** (rule 3 — `tests/test_invariants_index.py`
   fails otherwise). Add the ID to the matching group under *Index by subject*, and append
   the invariant where the last few landed. Keep the provenance: `(Source: <spec-name>,
   YYYY-MM-DD.)`
2. **Keep the rejected-citation note in the invariant text.** It is the reason this is a
   separate rule rather than a citation to an existing one, and it is what stops the
   question being re-litigated.
3. **Cite the new ID at every site the rule ships** — `(INV-NNN)` first inside the rule's
   own bold, so it is on the rule's line. ⛔ **Derive the site set from `sites` and from
   scanning, never from the deferral's bullet list** (INV-246): the list is where the
   author noticed the rule, which is exactly what is unreliable.
4. **Back-cite from the enforcer.** If the invariant says *"Enforced by `tests/x.py`"*,
   that test must name the invariant back (`tests/test_invariant_enforcer_citations.py`).
   Say in the back-citation what the test does **not** establish — usually that a live turn
   obeys the rule, which only `dry-run` phase 3 can observe — so an `Enforced by` clause
   cannot be read as a compliance claim.
5. **Re-derive `EXPECTED_PAIRS`** in that guard by running its extractor. ⛔ Never
   increment it to make the assertion pass.
6. **Resolve the block** in `IMPLEMENTED.md`: `**DEFERRED INVARIANT (resolved INV-NNN,
   registered by the maintainer YYYY-MM-DD).**`, keeping the rules and wording in place —
   the block becomes the record of what was approved.

Verify, then commit:

```bash
python3 .claude/skills/compact-dev-environment/citations.py verify        # resolves, count +1
python3 .claude/skills/dry-run/coverage_reports.py shipped | grep INV-NNN # must be empty
python3 -m unittest discover -s tests
```

`shipped` listing the new ID means the plugin does not cite it — step 3 was incomplete.

⛔ **One invariant per commit.** A batch commit makes a later revert take rules with it
that nobody questioned.

### Hold

Record the reason and the revisit condition **in the spec file**, where the next reader
looks — a note only in the conversation dies with it. Leave the block pending. Nothing
else changes.

### Amend

Change the wording in the block first, show the maintainer the changed text, and get a
second yes on **that**. Then register it. An amendment approved in passing is a wording
nobody read.

## Step 4: Next, and the session record

Move to the next pending block and repeat from Step 2. When the maintainer stops — whether
the queue is empty or not — write a dated `## invariant-review-YYYY-MM-DD` entry in
`specs/IMPLEMENTED.md`, marked **Not a spec**, recording what was registered, what was
held with its reason, what was amended, and what remains. That is the precedent set by
`invariant-review-2026-08-27`.

⛔ **A review record mints IDs and adds citations; it establishes no invariant of its
own.** Every invariant it registers was established by an earlier spec's implementation.

## Scope note

`.claude/` is not propagated to the public repo (`propagate.sh` mirrors `plugins/`,
`.claude-plugin/`, `docs/` and `README.md` only), so this skill never ships to bootcampers.
