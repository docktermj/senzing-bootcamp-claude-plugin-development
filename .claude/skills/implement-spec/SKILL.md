---
name: implement-spec
description: 'Implement one or more specs from the specs/ directory, re-verifying every Senzing fact the spec asserts against the live Senzing MCP server before changing any code. With no argument, list every spec not yet implemented and ask the maintainer which one(s) to implement; with an argument, implement specs/<argument>.md (name without the .md suffix). Records completed specs in specs/IMPLEMENTED.md, and records any new invariant an implementation establishes in specs/INVARIANTS.md. Maintainer tool for developing the Senzing Bootcamp Claude Plugin (SBCP) — the counterpart to feedback-to-issues, which no longer produces specs (#49) — this skill consumes the frozen archive only.'
---

# Implement Spec

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It takes a spec under `specs/` — a terse, developer-facing description of
a bug fix or improvement — and **implements it in the codebase**, then records
that the spec is done so it is not offered again. When an implementation
establishes a new durable rule, it also promotes that rule to an invariant in
`specs/INVARIANTS.md`.

It is the counterpart to the `feedback-to-specs` skill: that skill *writes*
specs; this skill *implements* them.

**A spec is a plan, not an authority on Senzing.** Its Senzing facts were true when
it was written, against the MCP server version current that day — and that server
ships independently of this plugin. By the time a spec is implemented the behavior it
describes may be fixed, changed, or newly contradicted, so **every Senzing fact a spec
asserts is re-verified against the live server before any code changes** (Step 3.3).
Where the server now disagrees with the spec, the server wins and the deviation is
recorded; implementing a stale spec faithfully means writing a fresh defect into the
plugin, with a spec file that makes it look reviewed.

⛔ **When a spec's diagnosis rests on the server LACKING something, re-ask the OWNER, not the
tools the spec listed.** Its `MCP re-check` line must carry `owner-checked: <route that would
carry the fact> — <what it returned>` (`../feedback-to-specs/spec-template.md`). Re-ask that
route. **A missing `owner-checked:` clause on an absence claim is a blocker, not a note:**
re-diagnose before implementing, because the empty tools the spec named prove something about
those tools and nothing about the negative. Two instances in one session, both from the same
mechanism — a real tool, real parameters, a real empty result, an honest date, and the wrong
tool asked. The first shipped as INV-208 plus a guard banning the correct value; the second
(`pattern-gallery-asks-for-more-than-mcp-can-supply`) was caught at exactly this step, and its
whole diagnosis inverted — the server covered the material all along, reachable by a different
vocabulary. That is this check paying for itself, and it is why the clause is enforced
(INV-194) rather than left to attention.

## Invocation modes

- **No argument** → discovery mode. List every spec that has **not** yet been
  implemented and ask the maintainer to choose one or more to implement.
- **An argument** → the argument is a spec **filename without the `.md`
  suffix** (e.g. `stop-hook-issue` → `specs/stop-hook-issue.md`). Implement that
  spec. Multiple names may be given (space- or comma-separated); implement each.

## The implementation record

`specs/IMPLEMENTED.md` is the **source of truth** for which specs are done. A
spec is considered implemented **iff** `IMPLEMENTED.md` contains a `## <name>`
heading whose text exactly matches the spec's filename without `.md`. Create the
file from the scaffold below if it does not exist. Never delete existing
entries; append new ones (newest first).

## What is (and isn't) a spec

Candidate specs are the `specs/*.md` files **excluding** these meta files, which
are never implementable specs:

- `INVARIANTS.md` — the ruleset every spec must respect (not a task).
- `todo.md` — the lightweight idea backlog (not yet specs).
- `IMPLEMENTED.md` — the record this skill maintains.
- `DECLINED.md` — the record of specs deliberately **not** being built (see below).

## Step 1: Load state

⛔ **Compute the set with the script, not by hand:**

```bash
python3 .claude/skills/implement-spec/list_specs.py
```

It does exactly steps 1–4 below, prints the counts alongside the open set so an empty result is
visible rather than ambiguous, and flags a spec that is in **both** ledgers. Steps 1–4 remain as
the explanation of *what* it computes and *why*; run the script to get the answer.

⚠️ **This became a script because the by-hand version failed.** On 2026-08-13 a run subtracted
only `IMPLEMENTED.md`, reported a **declined** spec as open, recommended it to the maintainer,
and implemented it; `tests/test_declined_ledger.py` caught the contradiction afterwards, but
nothing caught the listing. The instruction below was correct at the time and was simply not
followed — which is the argument for mechanizing it rather than restating it more firmly
(INV-207).

1. **List** `specs/*.md` and drop the meta files above → the candidate set.
2. **Read `specs/IMPLEMENTED.md`** (create it from the scaffold if missing) and
   collect the `## <name>` headings → the implemented set.
3. **Read `specs/DECLINED.md`** (if present) and collect its `## <name>` headings →
   the declined set. Same heading idiom, so the same parser reads both.
4. **Unimplemented = candidates − implemented − declined.**

   A spec reaches one of **two** terminal states, and both are subtracted. Omitting the
   declined set re-offers a spec the maintainer has already ruled out, every run — and
   the spec's own text argues *for* the change with nothing recording the argument
   against it, so the next run re-derives and re-asks.
5. **Read `specs/INVARIANTS.md`.** Every spec begins "Maintain the invariant
   conditions in @INVARIANTS.md" — the implementation must honor it (cross-platform
   Linux/macOS/Windows, language-agnostic, production-ready, consistent/coherent/
   complete, and the per-module outcomes).

## Step 2a: Discovery mode (no argument)

If no unimplemented specs remain, say so and stop.

Otherwise present a compact numbered list — one row per unimplemented spec with
its title and a one-line summary drawn from the spec's `## Problem` section:

```text
Specs not yet implemented:

  1. stop-hook-issue      — Stop hook loops, re-asking the same closing question
  2. PreToolUseWriteError — write-gate blocks legitimate /tmp scratch paths
  ...
```

Then ask exactly one clear question inviting the choice, e.g.:

> 👉 **Which spec(s) would you like me to implement?** (reply with numbers or
> names, `all`, or a range like `1-3`)

Wait for the answer — do not choose for the maintainer. Once they answer,
resolve their choice to spec filenames and proceed to Step 3 for each.

## Step 2b: Named mode (argument given)

For each name given:

1. Strip any trailing `.md` and resolve `specs/<name>.md`.
2. If the file does not exist, say so and list the available unimplemented spec
   names, then stop for that name.
3. If it names a meta file (`INVARIANTS`, `todo`, `IMPLEMENTED`), explain it is
   not an implementable spec and stop for that name.
4. If it is **already implemented** (present in `IMPLEMENTED.md`), report that
   with the recorded date and ask whether to re-implement before proceeding —
   do not silently redo it.

## Step 3: Implement each chosen spec

Work one spec at a time. For each:

0. **Check whether it is already done in the code.** The ledger can be empty or
   stale — a spec may have been implemented before this skill (or ledger) existed.
   Watch for a `**Status:** Implemented` line in the spec header, checked-off
   acceptance criteria, or a diff/commit that already matches `## Proposed change`.
   If the code already satisfies the spec, **do not re-implement it** — jump to
   Step 3.5 (verify against the acceptance criteria) and, if it holds, record it
   in Step 4. Only implement from scratch when the code does not yet satisfy it.
1. **Read the spec in full.** Note its `## Problem`, `## Root cause`,
   `## Proposed change`, `## Acceptance criteria`, and `## Affected files`.
   (Older specs may not use these exact headings — read the whole file and infer
   the intent.)
2. **Confirm the root cause in the code before changing anything.** Open the
   files the spec implicates (`plugins/senzing-bootcamp/hooks/`, `scripts/`,
   `skills/`, `commands/`, etc.), verify the cause is what the spec says, and
   cite `file:line`. If the spec's root cause turns out to be wrong or
   unconfirmable, pause and report it rather than implementing the wrong fix.
3. **Re-verify the spec's Senzing facts against the live MCP server — also before
   changing anything.** The spec is a plan; the server is the authority (INV-080).
   Record the server version first (`get_capabilities` → `server_info.server_version`),
   then re-ask the tool that owns each Senzing claim the spec relies on: a method's
   shape or response via `get_sdk_reference(topic='parameters' | 'response_schemas',
   filter=…, language=…)`, a flag and its `applies_to` via `topic='flags'`, an
   attribute or mapping rule via `search_docs(category='data_mapping')`, an error code
   via `explain_error_code`, export/report/evaluation behavior via `reporting_guide`,
   install or config guidance via `sdk_guide`, an example file via `find_examples`.
   Four outcomes, and each changes what you do:

   - **Confirmed** → implement as specified, and cite the server (tool, parameters,
     version, date) in whatever text you write into the plugin.
   - **Changed** → the fix's *content* changes. Implement what the server says now,
     not what the spec says, and record the deviation (Step 3.6).
   - **Already fixed upstream** → do not add the workaround. If the plugin carries an
     older workaround for the same defect, propose removing it; report and stop rather
     than shipping a mitigation for a defect that no longer exists.
   - **The spec is wrong** → do not implement it. Pause and report, exactly as for a
     wrong root cause. Correcting spec content is `feedback-to-specs`' job; the one
     thing you may add is the Step 3.6 deviation note.

   ⛔ **Never copy a Senzing fact out of a spec into shipped guidance or code without
   re-confirming it this session.** A spec is not an MCP source, and a fact laundered
   through a spec file reads as reviewed when it was merely written down. Where the
   server cannot reach a fact (a field only a live engine returns), keep it marked
   observation-only with its version and date — do not promote it on implementation
   (INV-080/INV-149). If the network is unavailable, say so and implement only the
   parts that need no Senzing fact, leaving the rest reported and unimplemented.
4. **Make the change** described in `## Proposed change`, touching the
   `## Affected files` (and any others the change genuinely requires). Keep edits
   minimal and in the style of the surrounding code. **Honor every invariant** —
   in particular keep the change cross-platform and language-agnostic. Any Senzing
   fact you write into the plugin carries its provenance: the tool and parameters
   that established it, the server version, and the date.

   ⛔ **A Senzing fact that is a *negative* — "tool X does not contain Y" — additionally
   carries an `MCP-NEGATIVE` marker**, so it lands on the worklist a dry run re-asks:

   ```text
   MCP-NEGATIVE: <tool(params) asked> — <what is absent> — owner: <route that owns the fact + outcome> — server <version>, <YYYY-MM-DD>
   ```

   <!-- MCP-NEGATIVE-SCAN: ignore-file — this file documents the marker FORMAT; the template
   above is a placeholder, not a dated claim about the current server, and the scanner would
   otherwise report it as a malformed marker. -->

   A negative is the one claim shape that cannot go stale detectably. The suite is offline
   (INV-108), so nothing notices when the server gains the coverage the plugin routed
   around — it has happened twice, and the second time the claim was in the **guards** too,
   so correcting the prose failed the suite. `coverage_reports.py negatives` lists every
   marker oldest-first; a negative with no marker is invisible to it. Prefer asserting what
   **is** true over what must not be said: the latter is the form that expires.

   ⛔ **`owner:` is required, and it is the field that makes the negative worth anything.**
   Name the route that would **carry** this fact and say what it returned. The empty call in
   the claim slot proves a fact about *that call*; it is not evidence for the negative.
   "`sdk_guide(topic='configure')` returns no license variable" is true and irrelevant —
   the variable lives in `sdk_guide(topic='load', record_count=<above the limit>)`. Two shapes,
   both needing the clause:

   - **Routing negative** — the fact exists elsewhere. The owner is where the reader must go
     instead of concluding absence.
   - **Absence negative** — the fact is served nowhere. The owner is the route you asked and
     found empty, and naming it is the only thing separating this from a wrong-route error.

   A marker with no `owner:` clause **does not parse** and is reported as missing rather than
   well-formed, deliberately. This exists because a wrong-route negative reached a registered
   invariant and a guard that enforced it, with dated evidence throughout, and read as
   reviewed the whole way (INV-194; `specs/mcp-negative-markers-must-name-the-owning-route.md`).

5. **Verify against the acceptance criteria.** Walk each checkbox and confirm it
   holds — run the relevant script/hook/command or exercise the flow where
   possible (consider the `/verify` skill). If a criterion cannot be satisfied,
   do not mark the spec done; report what's blocking.

   Two cases need naming rather than glossing:

   - **A criterion that asserts a Senzing fact** is checked against the server, not
     against the spec that asserted it.
   - **A criterion that needs something this environment does not have** — most often
     a live engine with loaded data — is reported as *not runtime-verified*, naming
     what is missing, in both the report and the ledger entry. Do not tick it, and do
     not silently treat the spec as fully verified. This is not a blocker on its own
     when the criterion's content is implemented and otherwise test-asserted; it is a
     disclosure.
6. **Record any deviation from the spec.** When re-verification, the code, or the
   environment made you implement something other than what the spec says — a
   corrected fact, a substituted route, an unmet criterion — append a
   `## Deviations from this spec, and why (<date>)` section to the spec file saying
   what differed and on what evidence. This is a permitted append (see the
   guardrails), and it is what keeps a future reader from treating the spec's text as
   what shipped.

If a spec is too ambiguous to implement safely, stop and ask for clarification
rather than guessing.

## Step 4: Record the implementation

⛔ **Walk the criteria one at a time before you write the entry — the ledger heading is a
claim, and nothing downstream re-checks it.** For each `- [ ]` in `## Acceptance criteria`,
name what proves it: a `file:line` you changed, a test that asserts it, or a command you
ran. A criterion you cannot prove is **not** ticked — it is either implemented-but-not-
runtime-verified (say what it needs, in both the report and the entry) or a deviation
(Step 3.6). Do not summarize the *narrative* of the work in place of this walk: the
narrative is what a spec's `## Proposed change` already says, and the criteria are what
was actually promised.

This step exists because it was skipped twice, with the same shape both times — a spec's
criterion named a second consumer, only the first was built, and the ledger recorded the
spec as done anyway:

- `relocate-integration-deployment-questions-to-module1` (2026-07-22) — criterion 4 said
  the answers are read "by the Module 1 problem statement **and by graduation**".
  Graduation was never touched; `graduation/SKILL.md` is not even in that entry's
  Files-changed list. INV-097 stood unimplemented for seven weeks.
- `defer-commonmark-to-graduation` (2026-07-16) — criterion 1 said the pass runs over
  `docs/*.md` **and the generated `production/*.md`**. Only `docs/` shipped. INV-060 stood
  unimplemented for six weeks.

Both were invisible to the whole suite, because neither INV-060 nor INV-097 is cited by any
test. So: **a criterion that names a file, a module, or a second consumer is checked
against that file** — open it and look — not against the change you remember making.

⛔ **And the spec's list of sites is not the set of sites — sweep for the rest (INV-246).** A
spec enumerates where its author *noticed* the defect, which is precisely what is wrong when a
rule is applied incompletely. On 2026-08-14 a spec closed with a section titled *"The same branch
exists twice"*, naming two files; the branch existed **three** times, and the third was upstream of
both, in the module where the decision it governed was actually made. It shipped unfixed, guarded
by a test that named the same two paths. So: **the guard you write derives its site set by
scanning, never by hardcoding paths** — a listed guard certifies the sites you already thought of
and is blind to the one you missed, which is the only site that matters.

Two supporting reports exist for the gaps this cannot catch by hand; run them when the
audit workflows ask, or when a spec touches the ledger
(`.claude/skills/dry-run/coverage_reports.py`, both stdlib-only):

```bash
python3 .claude/skills/dry-run/coverage_reports.py invariants   # invariants no test cites
python3 .claude/skills/dry-run/coverage_reports.py shipped      # invariants no SHIPPED file cites
python3 .claude/skills/dry-run/coverage_reports.py affected     # predicted-but-unrecorded files
python3 .claude/skills/dry-run/coverage_reports.py negatives    # dated "tool lacks X" claims
```

⛔ **`shipped` is the one that catches an invariant this skill just minted.** It was missing from
this list until 2026-08-14, so the skill checked whether a *test* cited a new rule and never whether
the *plugin* did — and on 2026-08-14 all eight newly registered invariants (INV-222–INV-229) were
cited by no file under `plugins/`, one day after `aa013dc` had fixed thirteen of the same by hand.
A rule with no ID beside it is one a later editor cannot look up and will "tidy" away.

Only after the change is made **and** its acceptance criteria are met, prepend an
entry to `specs/IMPLEMENTED.md` under the header (newest first). Get the date
with `date +%F` (do not hardcode it). Use the spec's filename-without-`.md` as
the `## ` heading so detection in Step 1 stays reliable:

```markdown
## <spec-name>

- **Implemented:** YYYY-MM-DD
- **Files changed:** `path/one`, `path/two`
- **MCP re-check:** <server version + date, and the outcome — confirmed | changed (what) | already fixed upstream | n/a (no Senzing fact) | unverified (MCP unreachable). Name the tools called.>
- **Summary:** <what was done and how the acceptance criteria were satisfied. Name any criterion that is not runtime-verified and what it needs, and any deviation from the spec with its evidence.>
- **Commit:** <hash, "uncommitted", or "committed (hash not recorded)">
```

Leave a blank line after the `##` heading and around the list (MD022/MD032).

**The `Commit:` field takes one of three values and nothing else** — a hash,
`uncommitted`, or `committed (hash not recorded)` (`tests/test_spec_ledger_invariants.py`
enforces this). Write `uncommitted` when the entry precedes its commit, then **fill the
hash in on the next `implement-spec` run**: before writing a new entry, scan the ledger for
`uncommitted` fields whose work has since been committed and update them. Skipping that is
how 66 entries went stale at once, leaving the field unable to answer the one question it
exists for.

⛔ **Verify the entry LANDED before doing anything else — the editing tool's own report is
not evidence.** Confirm the heading is at a line start and the count grew by exactly the
number of entries you wrote:

```bash
grep -c '^## ' specs/IMPLEMENTED.md          # compare against the count before your write
grep -n '^## <spec-name>' specs/IMPLEMENTED.md   # must print a line; empty means it did not land
python3 .claude/skills/implement-spec/list_specs.py   # the open count must DROP by that many
```

⚠️ **This exists because a write reported success while mangling the artifact.** On
2026-08-21 two entries were inserted with literal `\n` text instead of newlines, spliced into
the middle of an unrelated entry's `- **Summary:**` line — so their `## ` headings were not at a
line start, a third entry was cut in half, and the inserting script printed "2 entries
prepended" from its own `print`. The full suite passed, 3,141 tests, and it was committed. It
was found only because `list_specs.py` reported `open: 11` immediately after two specs had
been implemented. One `grep -n '^## '` would have caught it at the moment of writing. This is
the same shape Step 4 already warns about for the other case — *a tool that exits 0 but
creates/modifies NO files did not do its job* — and the write half needed saying too.
`tests/test_ledger_files_are_well_formed.py` now guards the file, but the guard runs when the
suite runs; this check runs when the damage happens.

⛔ **Re-run `citations.py verify` AFTER the entry is written — it is the last action of this
step, not part of the criterion walk.**

```bash
python3 .claude/skills/compact-dev-environment/citations.py verify
```

The ledger is **inside** the corpus that scan reads, so a clean result recorded before the
entry exists measured a different repo than the one that ships. This is not hypothetical:
an entry whose evidence sentence wrote out an unminted `INV-NNN` created two citations of an
undefined invariant, turning the whole suite red — *after* the same run had recorded
`citations.py verify` as clean. The check was run before the artifact that broke it existed.
Same rule for the full suite when an entry's text could affect it.

⚠️ **And read the runner's verdict line, not just its count.** That run recorded
"1792 passed, 3 skipped" from a `Ran 1792 tests` line while `FAILED (failures=1, skipped=3)`
sat immediately beneath it — so 1792 was the total *run*, the suite was already red, and the
ledger said otherwise. A count is not a result.

If the maintainer chose to re-implement an already-recorded spec, update that
spec's existing entry rather than adding a duplicate.

Leave the spec file itself in place under `specs/` — the ledger, not the file's
location, records completion. Do not commit unless the maintainer asks; if they
do, reference the commit hash in the entry.

## Declining a spec instead of implementing it

Some specs are correct and still should not be built — most often because the change
they propose is an architectural decision rather than a defect repair. That outcome
needs recording, or the spec is offered again on every run and the reasoning against it
is lost.

⛔ **Never decline a spec on your own initiative.** This skill implements what the
maintainer chooses; deciding *not* to build something is theirs alone. If a spec looks
like a poor idea, say so and let them rule — do not write to `DECLINED.md` without their
explicit decision.

When they do decline one, append an entry to `specs/DECLINED.md` using the same
`## <spec-name>` heading idiom as `IMPLEMENTED.md` (Step 1 subtracts both):

```markdown
## <spec-name>

- **Declined:** YYYY-MM-DD
- **Decided by:** <who made the call>
- **Reason:** <why not — required; never leave this empty>
- **Revisit if:** <the condition that would reopen it, or "nothing foreseeable">
```

Two fields carry the weight. **Reason** is required for the same reason
`delegate-to-mcp-server` requires one on a `keep-by-design` verdict: an unreasoned
decline is indistinguishable from nobody having looked, and the next run looks again.
**Revisit if** keeps the file from becoming a graveyard — most declines are made against
current architecture or a current upstream gap, and naming the trigger lets a later run
check cheaply instead of re-arguing.

⛔ **An absence claim in a `Revisit if:` clause or a dated revisit note carries the same
`MCP-NEGATIVE` marker Step 3.4 requires — this file needs it most, not least.** A declined
spec is never implemented, so Step 3.3 never re-asks its facts: a negative written here is
the only Senzing claim in the repo with no re-verification path, while this skill tells the
next reader to trust it *over* the spec's own citations. Write the marker on the same bullet
as the claim:

```markdown
- **Revisit if:** Senzing documents a self-service route for <X>.
  MCP-NEGATIVE: search_docs(query='<terms>') — no indexed document names <X> — owner: search_docs IS the corpus route the condition is written against, so the empty result is the answer rather than a miss (absence negative) — server <version>, <YYYY-MM-DD>
```

`coverage_reports.py negatives` scans `specs/DECLINED.md` (and no other file under `specs/`)
for exactly this reason, so a marker here reaches the worklist a dry run re-asks;
`tests/test_declined_ledger.py` fails on an absence-shaped bullet that has none. Prose that
**quotes a retracted claim** is exempt and must say so on the bullet with
`MCP-NEGATIVE-SCAN: quoted-history`, so a correction can restate what it corrects.

This is INV-194 applied where it was actually breached: the 2026-08-13 revisit note on
`no-route-for-bootcampers-who-cannot-add-an-mcp-server` concluded a binary had lost its
citations after asking a tool description and the tool manifest — when the binary was that
manifest's own `server_name`. Requiring the `owner:` clause is what forces the owning route
to be asked.

**Leave the spec file where it is.** Do not archive, move or delete it: its analysis is
what made the decision possible, and its filename is a permanent address. A declined
spec also stays visible to `feedback-to-specs`' Step 4 deduplication, so the same
subject arriving again finds it rather than producing a second spec.

**Declined is not superseded.** A spec whose facts are wrong, or that a later spec
overtakes, is `feedback-to-specs`' business — the remedy there is a corrected or
superseding spec, not a `DECLINED.md` entry.

## Step 5: Record any new invariants

Some implementations establish a **new invariant** — a durable guarantee that all
future specs and code must maintain, not merely a one-off fix. When that happens,
promote it to `specs/INVARIANTS.md` so future work is bound by it. Judge it this
way:

- **Creates an invariant** — the change adds or hardens a standing rule that
  future work could otherwise violate (e.g. "the write-gate must never block an
  in-project path", "every module banner uses the `MODULE n: [title]` form").
- **Does not create an invariant** — the change merely restores behavior an
  existing invariant already requires, or is a one-off content/doc fix with no
  ongoing constraint. Then skip this step.

If the spec already names the invariant it introduces, use that wording;
otherwise draft it. For each new invariant:

1. **Compute the next ID.** Read `specs/INVARIANTS.md`, find the highest
   `INV-NNN` anywhere in the file, add one, and zero-pad to three digits.
   `specs/INVARIANTS.md`'s own "Maintaining this file" section is the authority
   on the format and rules — follow it.
2. **Confirm the wording with the maintainer.** Invariants are permanent and
   bind every future spec, so show the drafted `INV-NNN — <statement>` and ask
   one clear 👉 question before writing. Never record an invariant the maintainer
   has not agreed to.
3. **Append to `specs/INVARIANTS.md`** under `## Invariants added from
   implemented specs`, directly beneath the `<!-- New invariants... -->` marker,
   as a single testable MUST/ALWAYS condition with provenance (get the date with
   `date +%F`):

   ```markdown
   - **INV-NNN** — <single testable MUST/ALWAYS condition.> (Source: `<spec-name>`, YYYY-MM-DD.)
   ```

   Remove the `_None yet._` placeholder if it is still present. **Never renumber
   or delete an existing invariant** — only append.
4. **Cross-reference the spec.** Append a note to the spec file under `specs/`
   recording which invariant(s) its implementation introduced, so the link is
   bidirectional:

   ```markdown
   ## Invariants introduced

   - `INV-NNN` — <statement> (recorded in `specs/INVARIANTS.md`).
   ```

5. ⛔ **Cite the new ID in the shipped text that states its rule, before recording the spec as
   implemented.** The prose is already there — what is missing is the `INV-NNN` beside it, and
   INV-183 requires a rule binding a step to be reachable **at** that step. Add it at every site
   the rule governs, then re-run `coverage_reports.py shipped` and confirm the new ID is gone from
   its output.

   ⚠️ **This matters most when the invariant is QUEUED for approval**, because then the citation
   is *un-writable* at the moment the prose is written — the ID does not exist yet. That is exactly
   what happened on 2026-08-14: eight implementations shipped with their rules stated and no IDs,
   the eight IDs were minted later in one commit, and nothing sent anyone back to the prose. A
   citation that cannot be written when the prose is written will not be written at all unless a
   step asks for it. So: **minting the ID is not the last action — citing it is.**

If one implementation establishes several invariants, add one entry per
invariant using consecutive IDs.

⛔ **Declining to mint an invariant does NOT decline to ship the rule — and that gap has been
walked into once, at scale.** When the maintainer is unavailable and step 2's sign-off cannot be
obtained, the safe-looking move is "do not record an invariant they have not agreed to". It is only
half safe: if the implementation's *fix* is a hard rule, the rule ships anyway, and the run has then
produced exactly the unregistered guarantee the reverse contract forbids — a rule in the product,
nothing in the ruleset, nothing binding future work to it (INV-134 and INV-155 are the precedents,
each wrong for weeks).

So an implementation that ships a hard rule — a ⛔, a bolded MUST/NEVER, anything
`conformance.py rules` would count — owes **one of two things, never silence**:

- the invariant, recorded; or
- an explicit **deferral in the ledger entry**, naming the rule, the site, and why it was not
  registered — so the next `production-readiness-audit` reads it as known rather than discovering it.

⚠️ **Check before writing the entry, not after** — and ⛔ **`rules` alone cannot answer this
question, so do not check it alone:**

```bash
python3 .claude/skills/production-readiness-audit/conformance.py since --since-last-audit
python3 .claude/skills/production-readiness-audit/conformance.py per-rule --uncited
```

`since` is the one that matters here: it lists the hard-rule lines added since the newest audit
entry's recorded commit — resolved from the ledger, not guessed — which for a run following an
audit is **this run's own additions**. That is
exactly the set the run is answerable for. `per-rule` gives the standing worklist, scoped to the
invariants cited *at* each rule rather than anywhere in its section.

⛔ **`conformance.py rules` is section-scoped and MUST NOT be read as a count of unregistered
rules.** A new rule does not appear in it if it lands anywhere near an unrelated `INV-nnn` — and it
gets *harder* to see as citations grow denser, which is the opposite of what a maturing plugin needs.
Both directions are on record:

- **2026-08-17** — the count went **1 → 10** across eighteen implementations and the audit found
  seven genuinely unregistered rules the same day
  (`specs/seven-hard-rules-shipped-in-one-run-with-no-invariant.md`). Those seven were visible only
  because they happened to land in sections with no citation at all; nothing establishes that seven
  was the whole set.
- **2026-08-21** — seventeen implementations added **26 hard-rule lines** (net +25) and the count
  **did not move at all**, holding at its session baseline of 1, while three of those rules were on
  subjects `INVARIANTS.md` covers nowhere
  (`specs/the-2026-08-21-run-shipped-three-unregistered-guarantees.md`).

A run that adds a hard rule owes a ledger line for it whether or not any count moved. Flagging
loudly is the remedy — not letting the rule ship unmentioned.

## Step 6: Report

For each spec implemented, report:

- The spec name and a one-line summary of the change.
- The files changed (as clickable `path:line` where useful).
- **What the MCP re-check found**, and the server version it ran against — say so
  even when nothing changed, since "confirmed against 1.32.1 today" is itself the
  result. If it changed the implementation, lead with that: it is the highest-value
  thing in the report, and invisible if it only lives in the spec file.
- How each acceptance criterion was verified, naming any that is **not
  runtime-verified** and what it would need.
- The `IMPLEMENTED.md` entry that was added.
- Any new invariant(s) recorded (`INV-NNN`) in `specs/INVARIANTS.md`, or a note
  that the implementation introduced none.
- Any `## Deviations from this spec, and why` note appended, and what it records.

If several specs were requested, give a compact table:

| Spec | Result |
|---|---|
| `<name>` | Implemented → recorded in `specs/IMPLEMENTED.md` |
| `<name>` | Blocked — <reason> |

Then offer next steps (e.g. "want me to commit these?" or "shall I implement the
remaining specs?"). Do not implement specs that were not requested.

## Guardrails

- **Never mark a spec implemented that isn't.** The ledger must reflect reality;
  if verification fails, leave the spec off the record and say why. A criterion
  that could not be run in this environment is disclosed, never ticked.
- **The server outranks the spec on every Senzing fact.** Re-verify before changing
  code (Step 3.3), implement what the server says now, and never copy a Senzing
  fact from a spec into shipped guidance without re-confirming it this session
  (INV-080). A stale spec implemented faithfully ships a fresh defect that looks
  reviewed.
- **Never invent or edit spec content** to make it easier to implement. If a
  spec is wrong, report it — fixing/authoring specs is `feedback-to-specs`' job.
  Two appends are permitted, because both *record* an outcome rather than altering
  the plan: the `## Invariants introduced` note from Step 5, and the
  `## Deviations from this spec, and why` note from Step 3.6.
- **Respect `@INVARIANTS.md`.** A change that would violate an invariant is not a
  valid implementation; surface the conflict instead.
- **New invariants are confirmed and append-only.** Promote a rule to
  `specs/INVARIANTS.md` only after the maintainer signs off on its wording; use
  the next `INV-NNN`, append beneath the marker, and never renumber or delete an
  existing invariant. Keep the link bidirectional (invariant ↔ source spec).
- **Ledger is append/update only.** Never delete implementation history.
