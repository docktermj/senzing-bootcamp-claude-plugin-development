---
name: compact-dev-environment
description: 'Compact the Senzing Bootcamp plugin development environment — consolidate overlapping or superseded invariants, archive specs whose work is long landed, merge redundant test traversals, and prune stale feedback — without losing the reasoning future development depends on. Use when the maintainer wants to clean up, tidy, prune, consolidate or de-duplicate the dev environment, when INVARIANTS.md has grown unwieldy, or when the specs/tests backlog is slowing work down. Maintainer tool — not part of the bootcamper experience.'
---

# Compact the development environment

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It reviews the four things that accumulate — **invariants, specs, tests,
feedback** — and reduces what future development must carry, without losing what
future development needs to know.

**Why "compact" and not "clean".** Cleaning implies removal; the job here is
compaction in the database sense — same information, less to drag along. Almost
every good outcome of this skill is a *merge* or a *move*, not a delete. The name
matters because the failure mode is a maintainer who runs a "clean" skill and
loses the reason a rule exists.

## The one thing to understand before touching anything

The four asset classes look similar and behave completely differently, because
each is either an **address** other things point at, or a **record** that stands
alone. Measured in this repo on 2026-07-31:

| Asset | What it is | Citations | Safe operation |
|---|---|---|---|
| Invariant `INV-NNN` | an **address**: 4,981 live citations across plugin text, specs, tests and skills — **plus 813 in commit messages, which cannot be edited** | very high | merge, supersede, trim — **never renumber casually** |
| Spec file | a **record**; its address is the `## <name>` heading in `IMPLEMENTED.md` | moderate | archive (move), rarely delete |
| Test | **enforcement**; deleting one silently removes a guarantee | n/a | merge traversals, never merge assertions |
| Feedback archive | a **record**; its address is the `entry_id` hash in `feedback/PROCESSED.jsonl` | low | prune files, **never prune ledger lines** |

**Never break an address. Records may be moved or pruned.** That single rule
decides most calls this skill has to make.

⚠️ **Re-measure these numbers; do not cite them.** The 2026-07-30 versions of the
two figures above were **wrong the day they were written** — the table claimed
5,210 live citations and Step 2 claimed 43 uncited invariants, while the tools
shipped in that same commit (`f4a8e56`) reported **4,587** and **93**. Neither
tool has been modified since, so there is no counting-method explanation; they
were simply never measured. The 43 was the costlier one, because Step 2 built a
whole guidance section on it: a later maintainer seeing 91 would reasonably infer
that ~48 invariants had lost their enforcement, when the real movement was
93 → 91, i.e. slightly better. This is the failure Step 4's first item describes —
a false claim made load-bearing — occurring in this skill's own prose, where
re-measuring never reaches it because a reader trusts the stated figure instead.
So: run Step 1, use what it prints, and treat every number in this file as a
dated illustration of scale.

## Renumbering invariants: read this before proposing it

Renumbering is the operation maintainers ask for most and the one with the worst
cost/benefit in this repo. `specs/INVARIANTS.md` forbids it in its own rules
("IDs are permanent references"), and the reason is measurable rather than
stylistic:

- **Thousands of `INV-NNN` citations live in commit messages** — 2,321 when last
  measured, 2026-09-24, and one more with every commit that cites one. Git history is
  immutable, so none of them can be corrected. ⚠️ **Re-measure rather than quoting that
  figure**; it is here to show the order of magnitude, and the argument does not depend
  on the exact value.
- After a renumber, those citations do not dangle — they **silently resolve to a
  different real invariant**. A 2026-07-30 commit explaining a fix to "INV-132"
  would, post-renumber, point at whatever now holds 132. Dangling references get
  noticed; wrong-but-plausible ones do not.
- The same applies to the three archived feedback files and to any spec text
  quoting a historical decision.

So: **the default is consolidation without renumbering.** Merging two invariants
into one new ID and marking both superseded achieves "consistent, coherent,
concise" with no address broken — the file gets shorter and every old citation
still resolves to something true.

If the maintainer directs a renumber anyway, it is a separate, explicitly
authorized operation and it MUST:

1. Be **all at once** — never a partial renumber; two numbering schemes in flight
   is unrecoverable.
2. Ship a permanent, machine-readable `RENUMBERING.md` map (`old → new`, with the
   date) **at the repository root**, kept forever, so a historical citation can be
   resolved by hand. ⛔ **Not under `specs/`** — the archive is frozen (INV-307) and
   `tests/test_specs_are_frozen.py` rejects a new file there, so the instruction this
   replaced could not be carried out at all: following it turned the suite red. ⚠️ Not
   under `docs/` either, which `propagate.sh` mirrors to the public access repo. The
   root is where `invariant-manifest.json` already sits for the same reasons, and it is
   inside a tagged release — which is what a child needs, since children key their
   inherited-invariant registers on the parent's `INV-NNN`.
3. Rewrite every live citation mechanically (never by eye) and then pass
   `citations.py verify` with zero unresolved and zero unexpected IDs.
4. State in the report, plainly, that every `INV-NNN` citation in a commit message is
   now wrong and that `RENUMBERING.md` is the only way to read them. ⛔ **Measure the
   figure at renumber time and give it with its date** — do not quote one from this
   file. `git log --format=%B | grep -oE 'INV-[0-9]{3}' | wc -l` is the count.
   ⚠️ This step used to name a literal **813**, measured 2026-07-31 and never
   re-measured; by 2026-09-24 the real figure was **2,321** and rising with every
   commit. A number a document tells you to quote stops being a dated illustration
   whatever the caveat above says — which is the failure the section two above this
   one exists to describe, reproduced here.

Item 4 is not a formality. A maintainer who has not been told this will later
read old commits and be misled by them.

## Scope and guardrails

- **Report first, change second.** The default run produces a plan and changes
  nothing. Every destructive step is separately confirmed by the maintainer.
- **Compaction targets duplication *across* invariants, never rationale *within*
  one.** These invariants read long because each carries the failure that produced
  it — that narrative is what stops the rule being re-argued or re-broken. Cutting
  it makes the file shorter and the project dumber. Merge overlapping rules; keep
  every "observed:" clause that names a real defect.
- **Nothing is removed before a citation census.** `citations.py census` first,
  always. An invariant cited by shipped plugin text or by a test is load-bearing
  whatever it looks like in isolation.
- **A test is a guarantee.** Deleting one removes a promise. Merge traversals for
  speed; never merge two assertions into one, and never delete a test without
  naming which invariant or behavior loses its enforcement.
- **`IMPLEMENTED.md` and `PROCESSED.jsonl` are append-only.** They are the ledgers
  that make specs and feedback re-findable. Files they point at may move; the
  ledger lines never go.
- **Git is not a backup for the working set.** "It's in history" is true and
  nearly useless — nobody greps history for a rule they don't know exists. Use it
  to justify pruning *records*, never to justify dropping a *rule*.
- **Respect `@INVARIANTS.md`** — including its own maintenance section, which this
  skill is uniquely positioned to violate.

## Step 1: Take the census

```bash
python3 .claude/skills/compact-dev-environment/citations.py census
python3 .claude/skills/compact-dev-environment/citations.py verify
python3 .claude/skills/dry-run/coverage_reports.py invariants   # invariants no test cites
```

`census` reports every `INV-NNN` with where it is cited (plugin / specs / tests /
skills), every spec file against its ledger heading, and the feedback archive
against its ledger. `verify` is the referential-integrity check — run it again
after every change in this skill and require it to stay clean.

Record the baseline numbers. The report in Step 6 is meaningless without a
before/after.

## Step 2: Assess the invariants

Read `specs/INVARIANTS.md` in full. Sort every invariant into one of five:

| Verdict | Means | Action |
|---|---|---|
| `load-bearing` | states a rule still true, cited or enforced | keep, untouched |
| `mergeable` | two or more invariants state **one** rule from different angles | propose a merge (below) |
| `superseded` | its rule is now stated by a later invariant | mark superseded; never delete |
| `unenforced` | no test cites it and none could | see below — usually a keep |
| `not-an-invariant` | guidance or preference, not a testable MUST | propose demotion to `ground-rules.md` |

**Merging is the main win.** Two invariants that say one thing become one new
invariant at the next free ID, with both originals marked
`(superseded by INV-NNN)`. The file gets shorter, the rule gets clearer, and
every existing citation still resolves. Propose merges only where the rules are
genuinely the same — an invariant that is a *special case* of another is not a
duplicate, and collapsing it loses the case.

**On the ~91 invariants no test cites** (measured 2026-07-31): "no test cites it"
is a prompt, not a verdict. Three different things produce it:

- The invariant governs **prose the tests do not read** (module wording, question
  phrasing) — add a test if one is cheap, otherwise keep it and say so.
- The invariant is **enforced by a test that does not name it** — the guarantee is
  real, the citation is missing. Fix the citation, not the invariant.
- The invariant is **unenforceable by construction** (it constrains a live
  bootcamp run). Keep it. An unenforceable rule is still the thing that stops the
  next person doing it wrong.

Only the third case with *no* remaining relevance is a demotion candidate.

## Step 3: Assess the specs

A spec is a record of a decision; the ledger heading is what makes it findable.

- **Implemented and stable** → leave them. ⛔ **Archiving was measured on 2026-07-30
  and rejected**; an earlier draft of this skill recommended it, wrongly. Three
  findings, all of which a future run should re-check rather than re-derive: (a) the
  benefit is **3.5 ms** — spec discovery over 215 files is a glob, and no maintainer
  reads 212 spec files, they read the computed list; (b) `feedback-to-issues` Step 4
  lists **every** `specs/*.md` to deduplicate against, so archiving would hide solved
  problems and it would start writing duplicate specs, silently; (c)
  `tests/test_spec_ledger_invariants.py` resolves an invariant's `Source:` via
  `SPECS / f"{name}.md"`. Archiving is only worth revisiting if those consumers are
  taught to read `specs/archive/` **first**, and the reading burden is
  `IMPLEMENTED.md` (2,986 lines) regardless, which archiving does not touch.
- **Implemented but the change was later reverted or superseded** → the spec is
  now *misleading*, because it reads as describing shipped behavior. Do not
  delete it: append a dated note saying what superseded it, then archive. The
  ledger entry stays.
- **Cited as a `Source:` by an invariant** → the name must remain resolvable.
  Archiving is fine; deleting is not, because `INVARIANTS.md` names it.
- **Never implemented and no longer wanted** → the only real delete candidate,
  and it still needs the maintainer's explicit yes.

⛔ **Do not delete a spec to make a count smaller.** `IMPLEMENTED.md` was 2,986
lines on 2026-07-31 and is the actual reading burden; the spec files are looked at
one at a time. Archiving helps the glob; deleting helps nothing and costs
provenance.

## Step 4: Assess the tests

⛔ **Speed is not the reason to touch these tests.** Measured 2026-07-30: the four
files that walk the corpus more than once run in **~0.3 s each** against 42 files /
786 KB, while the suite's 67 s is dominated by PDF rendering (six tests at ~1.5 s
doing real fpdf2 work). An earlier draft of this skill cited "17 separate walks" and
implied consolidating them mattered; the count conflated `glob` with `rglob`, the real
figure is nine files, and the saving is unmeasurable. **Do not consolidate for
performance** — the churn risks the failure messages, which in this suite are most of
a test's value. Consolidate only where one file genuinely re-reads the corpus for
checks that belong together.

When you do combine, **combine the traversal, never the assertions.** The right shape reads each file
once and runs N independent checks, each in its own `subTest`:

```python
for path in shipped_markdown():
    text = path.read_text(encoding="utf-8")
    for name, check in CHECKS:
        with self.subTest(check=name, file=path.name):
            self.assertEqual([], check(text), ...)
```

One walk, N results, and a failure still names *which* check on *which* file.
The anti-pattern is `assertTrue(a and b)`: it halves the walk and destroys the
diagnosis, which in this repo is most of a test's value — the suite's failure
messages routinely explain the defect better than the code does.

**The findings that are actually worth hunting**, in value order — the 2026-07-30 pass
took item 4 and left the rest standing:

1. **A test pinning a premise that has gone stale.** Worse than no test: it makes
   a false claim load-bearing and fails the suite when someone corrects the truth.
   Three were found on 2026-07-30, all asserting the plugin still *said* something
   the MCP server had since contradicted. Look for assertions that pin the
   *absence* of a capability, or that quote wording rather than behavior.
2. **A test whose subject was deleted** — passes vacuously forever.
3. **Duplicate coverage** — two files asserting the same guarantee. Keep the one
   whose failure message is better; delete the other only after saying which
   invariant it cited.
4. **A vacuous scan** — a glob that no longer matches. Every corpus-walking test
   needs a not-vacuous guard, and this repo already uses that idiom
   (`test_the_scan_is_not_vacuous`); add it where it is missing.

   ⚠️ **Grep cannot find this — read every hit, or report nothing.** On 2026-07-31 a
   line-based scan for a count assertion flagged **ten** files as unguarded. On reading
   them, **all ten were false positives** and the real answer was *zero* — every
   corpus-walking test in this repo is already guarded. Four distinct reasons, each of
   which will recur:

   - **The guard spans lines.** `assertGreaterEqual(\n  len(...)` does not match a
     single-line pattern (`test_markdown_is_actually_being_scanned`,
     `test_the_check_is_actually_scanning_deferrals`).
   - **The guard names a member instead of counting.**
     `test_generated_html_deliverables.py` asserts two specific filenames are in the
     sweep's result. That is *stronger* than a count — a count passes on the wrong
     files — so a detector looking for `assertGreater` scores the better idiom as absent.
   - **Empty is the pass condition.** `test_verbatim_check_limitation.py` asserts
     `assertEqual([], PLUGIN.rglob("sz_verbatim_check*.py"))` — the plugin must ship no
     copy of the checker. A not-vacuous guard there would invert the test.
   - **The glob is over a fixture the test just created**, not the corpus
     (`test_feedback_ledger.py` globs its own tmpdir). Vacuity is impossible.

   So do not report this class from a grep at all. The signal is narrow — a glob over a
   **real** corpus path whose results are *iterated* rather than *asserted about*, with
   no count check **and** no named-member check anywhere in the file — and confirming it
   means reading the file. A ten-hit list relayed as ten findings is how a clean result
   gets reported as a backlog.

## Step 5: Assess the feedback

Check the actual size before proposing anything. On 2026-07-31 the archive was
**4 files, 80.4 KB, 28 ledger entries** — not a burden, and no pruning was
warranted. Say so rather than inventing work; a skill that always finds something
to delete is a liability.

The more useful check at this size is not the total but **whether every entry has a
disposition**: `census` reports that, and an entry left at `unrecorded` has lost the
entry→spec link the ledger exists to hold. Correct one with
`feedback_ledger.py annotate <entry_id> <disposition>`, which appends a superseding
line — the ledger reads last-wins and is never edited in place.

⚠️ **Read the ledger last-wins, and do not trust a single `unrecorded` line.** On
2026-07-31 `census` reported one entry with no disposition; the *next line in the
ledger* already named its spec, because it had been corrected on 2026-07-28. The bug
was in `census`, which read raw lines instead of collapsing by `entry_id` — and the
run wasted an append "fixing" a ledger that was already right. `feedback_state()` now
collapses last-wins and reports how many lines were superseded, and
`tests/test_citation_census.py` pins it. The general lesson outlives the bug: in an
append-only ledger, **the presence of a bad line is not evidence of a bad state** —
only the last line for a key means anything.

When it does grow:

- **`feedback/PROCESSED.jsonl` is never pruned.** It is content-addressed dedup;
  dropping a line makes an old feedback file re-processable, and the next
  `feedback-to-issues` run re-files work already done.
- **Archived `.md` files may be pruned** once every entry they carry is in the
  ledger with a disposition, and every spec they produced exists. `census` checks
  exactly that.
- **Pruning does not remove the PII.** These files are committed deliberately
  (see `feedback/README.md`) and contain bootcamper details; deletion from the
  working tree leaves them in history. Never offer pruning as a privacy measure —
  if privacy is the goal, that is a history-rewrite conversation, not this skill.

## Step 6: Report, then act on the confirmed subset

Report before/after numbers per asset class, then the plan as a table:

| Asset | Verdict | Proposed | Citations at risk |
|---|---|---|---|
| `INV-0xx` + `INV-0yy` | `mergeable` | merge → new ID, both superseded | 14 live, 0 broken |
| `specs/<name>.md` | implemented, stable | archive | ledger heading unchanged |
| `tests/test_a.py` + `test_b.py` | duplicate walk | one traversal, subTest per check | — |
| feedback | below threshold | no action | — |

Then:

- **Semantic changes go through a spec** — merging invariants, demoting one,
  deleting a test, deleting a spec. File it, let `/implement-github-issue` execute it. The
  spec is where the reasoning survives.
- **Mechanical changes may be executed here**, one class at a time, each with the
  maintainer's explicit yes: archiving specs, merging test traversals, pruning
  feedback files. After each, run `citations.py verify` and the full suite, and
  report both.
- **Renumbering, if authorized at all, is last** and is its own confirmation.

⛔ **Never batch a delete with a move.** If a run does both, a maintainer
reviewing the diff cannot tell which was which, and the delete is the one that
needed the attention.

Close by stating what was *not* compacted and why — an asset class you examined
and left alone is a result, and saying so stops the next run re-deriving it.
