---
description: Analyze a bootcamp feedback file and generate improvement specs under specs/ (maintainer tool).
argument-hint: "[path to feedback file]"
---

Maintainer request: analyze collected bootcamp feedback and turn it into
improvement specs.

Invoke the `feedback-to-specs` skill and follow it end to end: locate and read
the feedback file, parse each item, **check per-entry against `feedback/PROCESSED.jsonl`
whether it has already been triaged** (files arrive from multiple bootcampers at multiple
times, so a later copy often overlaps an earlier one — triage only the new entries, and for
a wholly duplicate file rename it `…_DUPLICATE.md`, write nothing and say so), **re-verify every Senzing fact against the live
Senzing MCP server** (the server ships independently of this plugin, so a report may
be stale, already fixed, or now contradicted), triage each item against
`specs/INVARIANTS.md` and the existing `specs/*.md` (deduplicating), confirm root
causes in the codebase, and write one or more `specs/<title>.md` files. Where the
current server is itself the defect, draft an upstream report and ask before sending
it via `submit_feedback`. Finish by archiving the processed file to `feedback/` with its ledger entries, then the
triage table — including what the MCP re-check found, the server version it ran against,
any entries skipped as already-processed, and the archive path — and the list of specs
created. Do not
implement the fixes unless asked.

Feedback file to analyze: $ARGUMENTS

If `$ARGUMENTS` is empty, default to `SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md` at the
repo root, then `docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md`; if neither
exists, say so and stop.
