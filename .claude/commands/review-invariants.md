---
description: Walk the deferred-invariant queue one block at a time and carry out the maintainer's register/hold/amend verdict (maintainer tool).
argument-hint: "[block number to start from] (omit to start at the top of the pending queue)"
---

Maintainer request: review the deferred invariants awaiting a decision.

Invoke the `review-invariants` skill and follow it end to end.

Start at block: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, load the queue and start at the first pending block.
- If `$ARGUMENTS` **names a number**, start there — it is the `<n>` that
  `pending_invariants.py show <n>` and `sites <n>` take.

**Load the queue and check it before quoting anything.** Run `pending_invariants.py list` for
the pending blocks, the count and the next free ID, then `pending_invariants.py check`. ⛔ **A
rule quote that is not verbatim in the file it names is not a wording to approve from** —
truncated, paraphrased or since reworded — so fix the quote against its source first.

⛔ **This skill NEVER signs off an invariant.** It presents, it asks, it waits, and it executes
what the maintainer decided. **A verdict the maintainer did not give is not a default to
choose** — that is the entire reason the deferral exists.

**Present one block at a time and stop. Do not batch** — the maintainer is deciding, not
skimming. Lead with the rules **already shipping**, verbatim and located, because that is the
concrete thing and the drafted wording is only the abstraction over it. Then the drafted
wording **in full, never summarized** — it is the text being approved.

**Present all three verdicts every time. Two of them are not "no."**

- **Register** — the wording is right. Mint the next free ID, cite it everywhere the rule
  ships, resolve the block. Permanent.
- **Hold** — not yet, *and here is what would change that*. The block stays, with the reason
  and revisit condition recorded. **Not a rejection.**
- **Amend** — the rule is right, the wording is not. Change the wording, then register it.
  ⛔ **Amend includes splitting: two subjects is two invariants.**

⛔ **State what approving and declining actually differ by, at the first block of the session,
in the maintainer's own terms** — the intuition is wrong in a way that matters:

> **Declining does not remove the rule.** It already ships, it already reaches Bootcampers, and
> a test already enforces it. Nothing about the product changes either way today.

What changes is whether the **ruleset knows about it**. Registered, the guarantee has an
address: a later contradiction fails a guard, `citations.py verify` resolves it, and a future
editor can look up why it exists — at the cost that IDs are permanent, so a wrong one gets a
dated correction note rather than a removal. Held, the rule keeps shipping and the ruleset
stays silent, so nothing binds future work to it. **So the question is never "is this rule
good?"** — it ships either way — **it is "is this wording one I am willing to be held to
permanently?"**

⚠️ **A hold is worth as much as its revisit condition.** *"Wait"* with nothing attached returns
next month with nothing new to weigh; *"revisit after `dry-run` phases 2 and 3 have exercised
the flow"* is a condition someone can check.

⛔ **Never present a held block as awaiting a decision.** It has one, and re-offering it asks
the maintainer to re-derive a call they already made and recorded. Mention held blocks once as
context and move on; bring one back only when its revisit condition is **met**, saying which
condition and what met it.

**Read `sites <n>` before citing, and respect its three groups.** The **named** sites are
definite; the **prose-named** ones — sites whose bullet nobody wrote — are **where the misses
have been**; the **candidates** are leads to read and ⛔ never sites to cite blind. A rule has
already been cited at the two sites its deferral listed when it shipped in three.

**Surface what the block already rejected.** Several record a near-miss citation considered and
turned down; that reasoning is the expensive part and it is already written, so show it rather
than making the maintainer re-derive it.

Close by writing the dated `## invariant-review-YYYY-MM-DD` entry in `specs/IMPLEMENTED.md`,
marked **Not a spec**, recording what was registered, what was held and with which revisit
condition, what was amended, and what remains — whether or not the queue was emptied. ⛔ **A
review record mints IDs and adds citations; it establishes no invariant of its own**, since
every invariant it registers was established by an earlier spec's implementation.
