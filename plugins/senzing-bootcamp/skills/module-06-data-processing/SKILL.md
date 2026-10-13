---
name: module-06-data-processing
description: 'Bootcamp Module 6: Data Processing. Use when the bootcamper starts or resumes Module 6, or needs to load mapped data into Senzing (single source then multi-source) and validate the load.'
---

# Module 6: Data Processing

> **MCP grounding (mandatory — applies to this entire skill).** Every Senzing fact you present —
> SDK method and attribute names, config options, error codes, and entity-resolution specifics —
> MUST come from the Senzing MCP tools, never from training data, memory, or speculation.
> **Pre-response checklist:** if a reply contains any Senzing specific, you MUST have called an MCP
> tool this turn to obtain it; if not, stop and call it first. This has the same precedence as a ⛔
> gate. The full rule and tool routing are the "MCP-first invariant" in
> `../bootcamp-onboarding/ground-rules.md`.

Follow `../bootcamp-onboarding/ground-rules.md` throughout (👉 one-question-at-a-time,
MCP-first, file placement, checkpointing). Execute every numbered step one at a time, in
order. Never skip, combine, or abbreviate a step containing a 👉 question. This has the same
absolute precedence as a mandatory gate.

**Worked steer.** When the AI's first attempt fails in this module, show the module's one worked
steer, and ask first: the pinned ask-first 👉 comes before the fix, and it may end a turn in a step
this module says asks nothing. What fires it, its two lines, at most one per module, how the
Bootcamper's answer is handled, minimal verbosity and the checkpoint note are stated once in
`../bootcamp-onboarding/ground-rules.md` → "Worked steers"; follow them there rather than a copy
here (INV-300, INV-352).

**First:** Read `config/bootcamp_progress.json`, then (per ground-rules) show the module start
banner, journey map, before/after framing, a brief numbered overview of this module's steps, an estimated time-to-complete (INV-096), and the recommended model/effort nudge (INV-063), before any module work.
**(INV-366) When it carries a `quality_iteration`, none of this runs:** route by its `stage`, at the first
source not listed in `completed`. `reload` goes straight to Phase B →
[Receiving a `quality_iteration`](phaseB-load-first-source.md#receiving-a-quality-iteration). `remap`
reaches this module only on an interrupted return its Phase D gate offered, and goes to Module 5's
[Receiving a `quality_iteration`](../module-05-data-quality-mapping/phase2-data-mapping.md#receiving-a-quality-iteration).
Do not re-present Phase D's gate or its source question, whose answers are already recorded. The
route is stated once, in `../module-07-query-visualize-discover/phase1-query-visualize.md` step 3b →
"The quality-iteration route" (INV-300). A return runs only the steps it names, so the steps it
leaves out are not skipped steps.
**(INV-366) When it carries a `setup_detour`, none of this runs either:** Phase A's switch to PostgreSQL is
part-way through, so go to SDK setup's
[Receiving a `setup_detour`](../module-02-sdk-setup/SKILL.md#receiving-a-setup-detour), which
finishes it and returns to Phase A's
[SQLite volume pre-load check](phaseA-build-loading.md#sqlite-volume-pre-load-check-stop-and-confirm-heads-up-not-a-mandatory-gate).

**Purpose:** Guide the Data Processing workflow: build a production-quality loading program,
load all data sources into Senzing, process redo records, and validate entity resolution
results (from first load through cross-source validation).

**Before/After:** You have Senzing-formatted JSON files in `data/senzing-ready/` (and possibly
test-load results from the Data Quality, Mapping, and Transformation module). After this module, all your data is loaded, redo
records are processed, and entity resolution results are validated, duplicates matched,
cross-source connections found.

**Prerequisites:** Module 5 complete (at least one transformed data source in
`data/senzing-ready/`), SDK installed and configured (Module 2), database configured (SQLite at
`database/G2C.db`, or PostgreSQL), transformation validated with the linter.

**Success indicator:** ✅ All data sources loaded into Senzing + redo records processed + no
critical errors + entity resolution results validated.

## Error handling

When the bootcamper hits an error during this module:

1. **SENZ error code** (message contains `SENZ` + digits, e.g. `SENZ2027`): call
   `explain_error_code(error_code="<code>", version="current")` and present the fix. If it
   returns nothing, continue to step 2.
2. Present the matching pitfall/fix for this module (full `common-pitfalls` reference is a
   later porting phase; for now, use `search_docs` to look up the symptom, e.g.
   `search_docs(query="loading", category="anti_patterns", version="current")`, whose loading
   pitfalls are in its second hit, *Senzing Anti-Patterns: Architecture and Performance*: read
   past the first hit).

## Loading code and safety (applies to every load step)

- **Loading, redo, and query code come from the MCP tools, never hand-written.** Use
  `generate_scaffold` (workflows `add_records`, `redo`, `query`) and `sdk_guide` for
  version-correct SDK code. Inline examples may use outdated SDK patterns. The rule covers
  the Senzing SDK calls; code that only orchestrates them is ordinary code (see the
  Phase C header, `phaseC-multi-source.md`).
- **Override MCP-suggested paths.** If a generated scaffold uses `/tmp/`, `ExampleEnvironment`,
  or any path outside the working directory, override the database path to `database/G2C.db`
  and keep all output files project-relative.
- **Back up before loading.** Ensure a backup of `database/G2C.db` exists before a load so a
  failed load can be recovered (see Phase D → Recovery from Failed Load).
- **No direct SQL.** Never generate SQL against `database/G2C.db` or its internal tables. All
  entity access goes through generated SDK code. Counts, stats, and reporting come from
  `reporting_guide` — **with a topic named**:
  `reporting_guide(topic='evaluation', language='<chosen_language>')` for this module's statistics,
  `reporting_guide(topic='export', language='<chosen_language>')` for extraction. Not
  `topic='reports'`, whose SQL targets a data mart the bootcamp never builds (see Phase D's header
  note).

## Phases

- **Phase A, Build Loading Program** (steps 1–4a): `phaseA-build-loading.md`
- **Phase B, Load First Source** (steps 5–11): `phaseB-load-first-source.md`
- **Phase C, Multi-Source Orchestration** (conditional, 2+ sources, steps 12–20):
  `phaseC-multi-source.md`
- **Phase D, Validation** (steps 21–28): `phaseD-validation.md`

Read `current_step` from `config/bootcamp_progress.json` and resume at the right phase.
