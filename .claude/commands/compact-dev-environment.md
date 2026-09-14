---
description: Compact the development environment — consolidate invariants, archive landed specs, merge test traversals, prune stale feedback (maintainer tool).
argument-hint: "[asset class: invariants | specs | tests | feedback] (omit to census all four)"
---

Maintainer request: compact the Senzing Bootcamp plugin development environment.

Invoke the `compact-dev-environment` skill and follow it end to end.

Asset class to work: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, take the full census in Step 1 and assess all four classes,
  then propose a plan. Breadth is cheap here; it is the *acting* that is expensive.
- If `$ARGUMENTS` **names a class**, still take the full census — the census is what makes any
  removal safe — and scope only the assessment and the plan to that class.

⛔ **Report first, change second.** The default run produces a **plan and changes nothing**.
Every destructive step is separately confirmed by the maintainer, one asset class at a time.

**The one rule that decides most calls: never break an address; records may be moved or
pruned.** An invariant `INV-NNN` is an **address** that thousands of live citations point at.
A spec file and a feedback archive are **records**, addressed by their ledger entry. A test is
**enforcement**. Which of the three a thing is decides what may be done to it.

⛔ **Never renumber an invariant**, and do not propose it. `INVARIANTS.md` forbids it in its own
rules, and the cost is measurable rather than stylistic: hundreds of `INV-NNN` citations live
in **commit messages**, which are immutable. After a renumber those citations do not dangle —
they **silently resolve to a different real invariant**. A dangling reference gets noticed; a
wrong-but-plausible one does not.

⛔ **Compaction targets duplication ACROSS invariants, never rationale WITHIN one.** These
invariants read long because each carries the failure that produced it, and that narrative is
what stops the rule being re-argued or re-broken. Cutting it makes the file shorter and the
project dumber. Merge overlapping rules; keep every `observed:` clause that names a real defect.

⛔ **Nothing is removed before a citation census.** Run `citations.py census` first, always —
an invariant cited by shipped plugin text or by a test is load-bearing whatever it looks like
in isolation. Re-run `citations.py verify` after **every** change and require it to stay clean.

**A test is a guarantee.** Merge traversals for speed; ⛔ never merge two assertions into one,
and never delete a test without naming which invariant or behavior loses its enforcement.

**`specs/IMPLEMENTED.md` and the feedback `PROCESSED.jsonl` are append-only.** They are what
make specs and feedback re-findable. The files they point at may move; the ledger lines never go.

⛔ **"It's in git history" justifies pruning a RECORD, never dropping a RULE.** Nobody greps
history for a rule they do not know exists.

⛔ **Never batch a delete with a move.** A maintainer reviewing the diff cannot tell which was
which, and the delete is the one that needed the attention.

**Semantic changes go through a spec** — merging invariants, demoting one, deleting a test or a
spec. Write the spec and let `implement-spec` execute it; the spec is where the reasoning
survives. **Mechanical changes may be executed here**, one class at a time, each with an
explicit yes, each followed by `citations.py verify` and the full suite, reporting both.

⛔ **Re-measure every number; never cite the figures written in the skill file.** Its own prose
records that two of its stated counts were wrong the day they were written, and that the costlier
one had a whole guidance section built on it — a false figure stays load-bearing precisely
because a reader trusts it instead of re-running the tool. Run Step 1 and use what it prints.

Finish with before/after numbers per asset class and the plan as a table. **Close by stating
what was NOT compacted and why** — an asset class you examined and left alone is a result, and
saying so stops the next run re-deriving it.
