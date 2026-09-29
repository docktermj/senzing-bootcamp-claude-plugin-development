---
description: Dry-run the plugin against the live Senzing MCP server, a real filesystem, and the maintainer (maintainer tool).
argument-hint: "[phases: 1, 2, 3 or all] [module phase 3's analysis starts at]"
---

Maintainer request: dry-run the Senzing Bootcamp plugin to find the defects that
reading it cannot.

Invoke the `dry-run` skill and follow it end to end.

Phases to run: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, run the skill's own question: present the three
  phases as a numbered list and ask which to run. Do not assume, and do not read
  "dry-run the plugin" as "all three".
- If `$ARGUMENTS` **names phases**, take them as the answer to that question and
  start at the lowest one. Phase 1 is the highest yield per minute — it targets
  the plugin's hard dependency and its entire factual foundation — so run it
  first unless the maintainer said otherwise.
- If **phase 3 is among them**, ask the second question before anything runs:
  which module the analysis starts at. A trailing module name in `$ARGUMENTS`
  answers it; otherwise list the eleven, numbered, with the environment's ceiling
  marked. Everything before that module is fast-forwarded with the analysis off.

⛔ **Phase 3 is never implied.** It costs the maintainer's time in a way 1 and 2 do
not, so it is included only when they actually asked for it. A command that accepts
a phase list is precisely where "all" gets inferred from silence; it must not be.

This is a **test-gate action** before publishing, which is why it is invoked
explicitly rather than inferred. Static analysis can only confirm the plugin agrees
with itself; each phase points the plugin at something outside it — the live
server's real schemas, a real filesystem, a human answering questions. Module 5's
mapping workflow was coherent, internally consistent, and could not execute at all.

Before any phase runs:

- **Work outside the repo.** The scratch project goes in `$HOME/senzing-bootcamp-dryrun`
  (or `-phase3`) — never inside the repo, and never under `/tmp`, which a maintainer
  hook blocks.
- **Record the environment's limits up front** (`senzing` importable? `libSz.so`?
  `fpdf2`? `docker`? headless browser?). Missing pieces are fine; silently skipping
  the paths that need them is not, and the report must state them rather than imply
  coverage it did not have.
- **Run `coverage_reports.py`** to choose where to look. `negatives` and `unmarked`
  are phase 1's worklist, not merely reports.

⛔ **Nothing leaves the machine except two outward acts, each under INV-314's gate: show
the maintainer the exact text and get a yes, given out of character, one record at a time.**

1. **A GitHub issue, or a comment on an existing one, in this repository.**
2. **`submit_feedback`, only for a finding whose verdict is `mcp-server`**: certain that the
   defect is the server's and that nothing in the Senzing Bootcamp needs to change.
   *Certain* means re-verified live against the server, with any absence claim carrying
   `owner-checked:` naming the route that owns the fact (INV-194, INV-213). ⛔ A `both`
   finding does not qualify: it gets a GitHub issue with the drafted upstream message
   inside it, for the maintainer to send. The send follows `/feedback-to-issues` Step 8: a
   self-contained technical report, everything identifying stripped (INV-321),
   `category='bug'` or `'feature'`, and ⛔ never `category='license_request'`.

A yes given in character, while answering as the Bootcamper, never authorizes either act.
A dry run must not file junk upstream or transmit a name and email. Verifying a tool's
schema sends nothing; `download_resource` on anything large stays forbidden.

⛔ **(INV-007) Never fabricate a Bootcamper answer** — if the maintainer is unavailable, phase 3
is untested, not approximated. **Commit or `cp` aside before mutating the tree**;
`git restore` cannot tell a fix from an injected defect.

⛔ **(INV-317) Draft each finding into the run's dated `specs/IMPLEMENTED.md` entry as you
find it, marked not yet filed, before fixing anything** — never into a new file under `specs/`,
which is a read-only archive (INV-307). A finding that exists only in the conversation is
not recorded. **Search open and closed issues before filing**; a finding already tracked
points at that issue instead of opening a duplicate. **File at the end of phase 1 or 2,
and when a phase 3 walk pauses or ends**, never mid-walk. ⛔ **(INV-314) Show the
maintainer each title and body and get a yes, one issue at a time**, then replace the
draft's marker with the issue number. **No maintainer present: file nothing** — the draft
stays marked **not filed — needs the maintainer to file it**. **Declined:** recorded as
declined. ⛔ **(INV-318) Never apply `unattended-ok` to an issue the run files.**

⛔ **(INV-317) The scratch project is disposable; the issues and the ledger entry are the run's actual
output.** If a run produced no issue and no ledger entry, it produced nothing durable,
however good the conversation was.

Finish by reporting findings in severity order, naming the issue (or ledger draft)
each became and saying which are fixed and which are recorded-but-open, what was verified as
correct, the coverage limits this environment imposed, and — if phase 3 ran — which
module the analysis started at and that everything before it was walked rather than
tested. Then clean up the scratch project and `__pycache__`, leaving `git status`
showing only the intended changes.
