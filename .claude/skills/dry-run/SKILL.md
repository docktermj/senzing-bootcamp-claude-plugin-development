---
name: dry-run
description: 'Dry-run the Senzing Bootcamp plugin to find defects that reading it cannot: phase 1 verifies every MCP call against the live Senzing MCP server, phase 2 executes the hooks and bundled scripts against a realistic scratch project, phase 3 walks the conversational layer with the maintainer answering as the Bootcamper. Use when the maintainer wants to dry-run, smoke-test, or exercise the plugin, verify it actually works rather than reads correctly, or asks what a fresh audit should look at next. Maintainer tool — not part of the bootcamper experience.'
---

# Dry Run

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It is never invoked during a bootcamp.

## Why this exists

Three full audits and 399 passing tests all read the plugin. Then one dry run found
that **Module 5's mapping workflow could not execute at all** — `mapping_workflow`
requires a `workspace_dir` parameter the plugin never passed, and five of its eight
documented action names were payload field names rather than actions. The
instructions were coherent, internally consistent, well cross-referenced, and wrong
about the tool they called.

That is the defect class this skill exists for, and it has a shape:

> Static analysis can only confirm the plugin agrees **with itself**. It cannot see
> where the plugin disagrees with the world — the MCP server's real schemas, the
> filesystem, a rendered artifact, or a human being answering questions.

Each phase points at one of those. Run them in order; each is independently useful
and each has found real defects.

| Phase | Checks the plugin against | Needs |
|---|---|---|
| 1 — [MCP call contracts](phase1-mcp-contracts.md) | the live Senzing MCP server's schemas | MCP access |
| 2 — [Hooks and scripts](phase2-hooks-and-scripts.md) | a real filesystem and real artifacts | `python3` |
| 3 — [Conversational layer](phase3-conversational.md) | a human answering questions | **the maintainer** |

Phase 1 is the highest yield per minute — it targets the plugin's hard dependency
and its entire factual foundation. Start there unless the maintainer says otherwise.

## Before you start

1. **Ask which phases to run** if the maintainer did not say. Present them as a
   numbered list (1, 2, 3, or all three); do not assume. Phase 3 costs the
   maintainer's time in a way 1 and 2 do not, so it is never implied by "dry-run
   the plugin".

   ⛔ **If phase 3 is among them, ask a second question before anything else runs:
   which module the analysis starts at.** List the eleven modules in order, numbered,
   and mark which ones this environment can actually reach (step 3 below is that
   check). Everything before the chosen module is walked as a Bootcamper sees it with
   the analysis off; the analysis begins when that module does. This is not a
   refinement — a walk that analyzes from the top runs out of context around Module 1
   every time, which is why no phase-3 run has ever reached the later modules. Full
   rules, including what the fast-forward may and may not do, in
   [phase3-conversational.md](phase3-conversational.md).
2. **Work outside the repo.** Phase 2 and 3 create a bootcamp project. Put it in
   `$HOME/senzing-bootcamp-dryrun` (or `-phase3`), never inside the repo and never
   under `/tmp` — a maintainer hook blocks system-temp writes, and the plugin's own
   file-placement rules assume a project directory.
3. **Note the environment's limits up front**, so the report can state them rather
   than imply coverage it did not have. Check and record: is the `senzing` Python
   package importable? is `libSz.so` present? is `fpdf2` installed? is `docker`
   available? is there a headless browser? Missing pieces are fine — silently
   skipping the paths that need them is not.
4. **Run the coverage reports to choose where to look.** Two blind spots have hidden
   real defects — an invariant no test cites, and a spec file a ledger entry never
   recorded changing. Both are reports rather than tests, because a hit in either is
   usually legitimate; they tell you where a conformance sweep is unguarded:

   ```bash
   python3 .claude/skills/dry-run/coverage_reports.py both
   ```

   `invariants` lists invariants no test mentions by ID — INV-060 and INV-097 both sat
   there while standing unimplemented for weeks. It splits its hits three ways so the
   actionable number is visible: **fully superseded** (filtered — a retired rule needs no
   test, and the list comes from the index's own "Fully superseded" entries, **not** a grep,
   because a *partly* superseded invariant such as INV-040 still binds), **bootcamp outcome
   invariants** (the first 50 ids — banners, questions, "the SDK is installed", which no
   offline suite can assert, so they are phase 3's business rather than test debt), and the
   **development rules** that remain. `shipped` is its mirror on the other side of
   the contract: invariants that **name a shipped artifact** (a path, module, step or bundled
   script) and that no file under `plugins/` cites, so the rule binds a step the guide cannot
   look it up from (INV-183). It is the question `conformance.py rules` cannot ask — that scan
   is satisfied by *any* `INV-NNN` in a section, which is how it reported **0** on 2026-08-13
   while INV-212 was named nowhere near the step it was registered from. Development-environment
   rules are exempt via the `INVARIANTS.md` index group that declares itself the exemption, and
   invariants stating a general property with no artifact are not reported at all — both filters
   exist so the output stays short enough to read. `affected` lists ledgered specs whose
   `## Affected files` predicted a path the entry's `Files changed:` never recorded —
   which is how the graduation half of INV-097 went missing. Its rows are classified, most
   actionable first: **names a real current file**, then **path no longer exists**, **bare
   filename** (an artifact, not a repo path) and **glob**, the last three being predictions
   the scan structurally cannot match. Within the first class, **★ marks the rows whose spec's
   `## Acceptance criteria` name the file** — the discriminator INV-097's defect actually had,
   since an `## Affected files` entry alone is only a prediction. `negatives` lists every dated
   "this MCP tool does **not** contain X" claim, oldest server version first — that one is
   **phase 1's worklist**, not just a report, because a negative is the single claim shape
   the offline suite can never notice going stale. Read-only, stdlib-only, exit 0
   whatever it finds. The `auto-test` skill can call it the same way.

   `unmarked` is `negatives`' complement and the newer half of phase 1's worklist: dated
   tool-absence claims in **shipped plugin prose that carry no marker**, which `negatives` cannot
   see because it only lists what is already tagged. The **date** is the discriminator — undated
   prose explaining how a tool behaves is not a re-checkable claim and is not reported. A hit needs
   judgment (it may be prose *about* behavior), which is why this reports rather than gates, and
   the vocabulary is a phrase list, so a miss is weak evidence. ⛔ **Never mark one of these by
   stamping today's date on it** — re-ask the owning route first; if the server has moved, the fix
   is to correct the prose, not to certify it.

   `negatives` also reads **`specs/DECLINED.md`** — the only file under `specs/` it scans,
   added 2026-08-13. A spec body's Senzing facts are re-asked by `implement-spec` Step 3.3 on
   the way in, but a *declined* spec is never implemented, so a negative in a `Revisit if:`
   clause is re-read as authority and never re-verified. Give those markers the same weight as
   a shipped claim: a wrong one sends the next revisit check to the wrong answer, which is
   exactly what a phase 1 sweep found there.

## Absolute rules

⛔ **Never send anything outside the machine.** Do not call `submit_feedback` under
any category. Verify its *schema* — never invoke it. A dry run must not file junk
upstream or transmit a name and email. The same goes for `download_resource` on
anything large.

⛔ **Never fabricate a Bootcamper answer.** This is what makes phase 3 impossible to
self-play: the plugin forbids simulating the Bootcamper's response, and an assistant
grading its own 👉 discipline proves nothing. If the maintainer is unavailable, say
phase 3 is untested rather than approximating it.

⛔ **Commit or copy aside before mutating the tree.** This one cost real work twice
in the session that produced this skill. `git restore` cannot tell your fix from a
defect you injected to test a guard — it reverts both. Either commit the fix first,
or back the file up with `cp` and restore with `mv`.

⛔ **Clear `__pycache__` after any same-size revert.** `"…"` and `"..."` are both
three bytes; a restored file with the same size and a same-second mtime lets Python
reuse bytecode compiled from the mutated source, so the suite keeps failing on
already-correct code. `find . -name __pycache__ -type d -exec rm -rf {} +`.

⛔ **A `pgrep -f` guard matches its own command line.**
`while pgrep -f "unittest discover -s tests"; do sleep 15; done` never exits: `-f`
matches the full command line, and the watcher's own `bash -c` argument contains the
pattern, so it finds itself. Bracket the first character — `"[u]nittest discover"` — or
match the process rather than the string (`pgrep -f "python3.*unittest"`). Four such
watchers spun for **27 hours** after a phase-2 run here, and they kept each other alive:
killing three would not have freed the fourth, because it still matched them.

⚠️ **The second half is why this is a rule and not a footnote.** Two later "is anything
still running?" sweeps reported *nothing* while all four were spinning — the sweeps
searched for `unittest|until grep` and these used `while`, so the cleanup check missed the
thing it was written to find. When verifying a scratch run left nothing behind, list the
session's own shells (`pgrep -a bash`) rather than grepping for the idiom you remember
using.

## What to do with a finding

A dry-run finding is only half done when the plugin is fixed. Follow this for each:

1. ⛔ **Write it into `specs/` as you find it — before fixing anything.** A finding that
   exists only in the conversation is not recorded, it is *remembered*, and it dies at
   session end or the next compaction. This is not a filing preference; it is the
   difference between a durable improvement and a good afternoon.

   - **File:** `specs/<kebab-case-title>.md`, using the shape in
     `../feedback-to-issues/issue-template.md` — Problem, Root cause, Proposed change,
     Acceptance criteria, Affected files, Source. Cite `file:line`, and date every MCP
     claim with the server version that produced it.
   - **When:** immediately for phase 3, because a walk stops on whatever turn the
     maintainer stops it; by the end of the phase at the latest for phases 1 and 2.
     Do **not** defer to the final report — the report is the last thing that happens
     and the first thing lost.
   - **Even when you fix it the same session.** The spec is what the `IMPLEMENTED.md`
     entry points at, what makes the finding legible to whoever reads it next, and what
     survives if the fix has to be reverted. Writing the spec is not made redundant by
     also fixing it.
   - **Grouping:** one spec per root cause. Several small prose corrections from one walk
     may share a spec when each is a few lines in the same file or two — give each its own
     acceptance criteria so they stay independently implementable — but two unrelated
     defects never share one.
   - **Where not to put it.** Not the session scratchpad: the maintainer's global
     `write-location-gate.py` blocks system-temp paths, so a `/tmp/...` note fails outright.
     Not repo `tmp/` either — it is not gitignored, so it becomes untracked clutter that
     "leave the repo with only intended changes" then tells you to delete. `specs/` is the
     home, and it has the additional property that `/implement-spec` lists it as
     outstanding work.

   Phase 3's collapsed test-notes blocks are *working notes* — the running observation
   channel for a walk in progress. They are never the record.

2. **Fix the class, not the instance,** where the class is cheap to remove. The
   `_clip` ellipsis defect had three call sites; changing the suffix to ASCII inside
   `_clip` made the ordering hazard unreachable instead of fixing three callers.
3. **Write a test in the repo-level `tests/`** — stdlib only, no `plugins/` (INV-108).
   A dry run you cannot repeat cheaply is a one-off; a test is the durable half.
4. ⛔ **Negative-control the test.** Reintroduce the defect, confirm the test fails,
   revert. A guard whose docstring claims more than its assertion checks is worse
   than no guard, because it certifies what it never tested. This is not optional:
   in the originating session, one existing test had **pinned the wrong premise**,
   which is how the defect it covered survived three audits.
5. **Record the outcome** in `specs/IMPLEMENTED.md`, naming the spec from step 1, and
   either register the invariant it establishes in `specs/INVARIANTS.md` or state that it
   establishes none — `tests/test_spec_ledger_invariants.py` enforces this for entries
   dated on or after its cutoff. Two homes, two purposes: the **spec** is the finding as
   pending work, the **ledger** is what was done about it. A finding you did not fix has a
   spec and no ledger entry, which is exactly right — it stays visible as outstanding
   rather than looking handled.
6. **Correct an invariant in place when the invariant itself is wrong.** INV-132
   asserted the MCP reference could not answer parameter shapes; the server answers
   them. Add a dated correction note explaining what was verified and when. An
   invariant that encodes a false premise is worse than a missing one.

⛔ **Do not end a run with unwritten findings.** Before reporting, list what you found and
confirm each one is either in a spec or in the ledger. "I described it in the report" is not
recorded — the report is a message, and messages are not durable. This rule exists because a
phase-3 walk reached eight turns with four findings held only in conversation, and it took
the maintainer asking *"are you keeping notes that might lead to improvements / specs?"* to
surface it.

## Reporting

Report to the maintainer with the severity ordering the findings deserve, and:

- ⛔ **Name the spec file each finding was written into**, and say plainly which findings are
  fixed and which are recorded-but-open. A report that lists findings without naming where
  they live reads as though the work is captured when it is only described.
- **Lead with anything that breaks a documented path**, not with the longest list.
- **Say what you verified as correct**, briefly. "The routing table is right, the
  opaque-state contract is handled, no `add_data_source` confabulation" is
  information, and it stops the next audit re-checking the same ground.
- ⛔ **State the coverage limits explicitly.** "No `libSz.so`, so the live server and
  every SDK-dependent path went unexercised" is the difference between a report and
  a false clean bill of health.
- **Report your own mistakes.** If a probe was wrong, or a fix was under-specified,
  or a `git restore` ate work, say so — the methodology's value depends on the
  reader trusting the parts that did work.

## Cleaning up

Remove the scratch project when the run is done (`rm -rf $HOME/senzing-bootcamp-dryrun`)
and clear `__pycache__`. Leave the repo with only intended changes: `git status`
should show the fixes, the new tests, **and the specs the findings were written into** —
nothing else.

⛔ **The scratch project is disposable; the specs are the run's actual output.** Deleting the
project is cleanup. Deleting or never writing the specs loses the run. If a run produced no
spec and no ledger entry, it produced nothing durable, however good the conversation was.

## Scope note

`.claude/` is **not** propagated to the public repo (`propagate.sh` mirrors
`plugins/`, `.claude-plugin/`, `docs/` and `README.md` only), so this skill and its
`scaffold_project.py` helper never ship to bootcampers.
