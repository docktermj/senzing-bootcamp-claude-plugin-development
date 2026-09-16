---
description: Analyze a bootcamp feedback file and file the results as GitHub issues in this repository (maintainer tool).
argument-hint: "[path to feedback file]"
---

Maintainer request: analyze collected bootcamp feedback and turn it into GitHub issues.

Invoke the `feedback-to-issues` skill and follow it end to end: locate and read the
feedback file, parse each item, **check per-entry against `feedback/PROCESSED.jsonl`
whether it has already been triaged** (files arrive from multiple bootcampers at multiple
times, so a later copy often overlaps an earlier one — triage only the new entries, and for
a wholly duplicate file rename it `…_DUPLICATE.md`, write nothing and say so),
**re-verify every Senzing fact against the live Senzing MCP server** (the server ships
independently of this plugin, so a report may be stale, already fixed, or now contradicted),
triage each item against `specs/INVARIANTS.md`, confirm root causes in the codebase, and
**file one GitHub issue per item that warrants one**. Where the current server is itself the
defect, draft an upstream report and ask before sending it via `submit_feedback`. Finish by
archiving the processed file to `feedback/` with its ledger entries, then report the triage
table — including what the MCP re-check found, the server version it ran against, any entries
skipped as already-processed or already-filed, and the archive path — and the list of issues
created. Do not implement the fixes unless asked.

Feedback file to analyze: $ARGUMENTS

If `$ARGUMENTS` is empty, default to `SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` at the
repo root, then `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`; if neither
exists, say so and stop.

## ⛔ It files in its own repository, and nowhere else

`/feedback-to-issues` **never files into another repository.** In child repos, cross-repo
routing is owned exclusively by `/escalate-to-parent`; in this repo — the parent —
parent-to-child change travels by **parity**, so the parent never files into children at
all. ⚠️ A `--repo` argument to `gh issue create`, or any other way of naming a repository,
is a violation of this rule rather than a convenience.

## ⛔ It never writes into `specs/`

`specs/` is a **read-only archive** as of the 2026-09-15 cutover (INV-307). It may be
**read** for historical context — a spec often records why the plugin reads as it does —
but nothing new lands there. A run that wants to record something writes an issue.

## Deduplicate against both the ledger and the issue tracker

`feedback/PROCESSED.jsonl` catches the **same entry arriving again** in a later feedback
file; it is per-entry and content-addressed, and it stays the primary check. ⚠️ It does
**not** catch two *different* entries describing the same defect, so search existing issues
before filing. Where an item is already filed, **reference or update that issue rather than
opening a second one**, and say so in the triage table.

## Keep every Senzing fact sourced

⛔ **(INV-080) Every Senzing fact reaching an issue MUST come from the live MCP server**,
named with its tool, parameters, server version and date. ⛔ **(INV-213) An item whose
diagnosis rests on the server *lacking* something MUST record `owner-checked:` — the route
that would carry the fact, and what it returned.** The tools asked and found empty are
evidence about those tools, not about the absence; a missing `owner-checked:` clause is a
blocker, not a formatting nit.
