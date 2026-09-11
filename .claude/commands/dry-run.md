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

⛔ **Send nothing outside the machine.** Verify `submit_feedback`'s schema; never
invoke it. ⛔ **Never fabricate a Bootcamper answer** — if the maintainer is
unavailable, phase 3 is untested, not approximated. ⛔ **Commit or `cp` aside before
mutating the tree**; `git restore` cannot tell a fix from an injected defect.

⛔ **Write each finding into `specs/` as you find it, before fixing anything.** The
specs are the run's output; the scratch project is disposable. A run that produced no
spec produced nothing durable, however good the conversation was.

Finish by reporting findings in severity order, naming the spec file each was written
into and saying which are fixed and which are recorded-but-open, what was verified as
correct, the coverage limits this environment imposed, and — if phase 3 ran — which
module the analysis started at and that everything before it was walked rather than
tested. Then clean up the scratch project and `__pycache__`, leaving `git status`
showing only the intended changes.
