# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp. Every entry is saved here, whatever it turns
out to be about. Entries routed `mcp-server` may **also** have been forwarded to Senzing —
only ever with your explicit yes, and with identifying details stripped; each entry's
`Upstream:` field records what happened.

**Started:** 2026-10-21

## Your Feedback

## Improvement: Missing 👉 question after presenting a generated business scenario

**Date:** 2026-10-21
**Module:** Discover the Business Problem
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — a turn ended with zero 👉 questions while presenting the generated Customer 360 scenario, violating the one-question-per-turn protocol; the skill's own non-yielding-step rule would have been satisfied by continuing into Step 5/5a/6a in the same turn, so this is an execution lapse against the plugin's own ground rules, not an MCP server or host defect.
**Upstream:** not applicable

### What happened

After accepting the Business Case Offer (option 3) and having a Customer 360 scenario generated, the guide presented the scenario description as a standalone message with no 👉 question ending the turn.

### Why it matters

It breaks the one-question-per-turn flow the bootcamp is supposed to follow.

### Suggested fix

Always end a generated-scenario turn with its 👉 confirm-match question rather than presenting it as a standalone statement.

### Context when reported

- **Time:** 2026-10-21 10:46 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-sonnet-5 / Unknown (not explicitly set via /effort this session; module recommendation is medium)
- **Context size:** Unknown (not directly observable this session)
- **Module / step:** business_problem / null (not yet checkpointed this module — steps 1–4a had not been written to `config/bootcamp_progress.json` at the time of this report)
- **Recent questions:** "How would you like to define the business problem? Reply with a number:" (1/2/3) — answered "3" (generate a scenario)
- **Bootcamper responses:** "3", then (after the gap) the feedback report itself
- **Behind the scenes:** Module 1 Phase 1, Step 4a (Business Case Offer acceptance) — the guide generated and presented the scenario, then should have continued, in the same turn, through Step 5 (infer details) and Step 5a (record-count threshold check, non-yielding) to Step 6a's confirm question, per the 👉 protocol's non-yielding-step rule in `ground-rules.md`.
- **Observed problem:** The scenario was presented and the turn ended with no question at all.
- **Expected behavior:** `ground-rules.md`'s 👉 protocol (INV-225) requires every turn to end on exactly one 👉 question; a non-yielding step (Step 4a/5/5a carry no question of their own) must be folded into the same turn as the next step that does ask one (Step 6a).
- **Divergence:** The guide stopped after the non-yielding scenario-presentation step instead of continuing in the same turn to Step 6a's confirm question.

## Improvement: Data collection's quality self-check and Module 5's formula disagree on the record key

**Date:** 2026-10-21
**Module:** Data Quality, Mapping, and Transformation
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — Module 4's worked band table assumes the record key is outside the completeness denominator, while Module 5 Phase 1 step 6 counts it as a structural key; neither the MCP server nor the host is involved.
**Upstream:** not applicable

### What happened

At Data collection the generated CRM_EXPORT source was self-checked at 77.9 (inside the required 70-79 band) and that figure was reported to the bootcamper and written to `quality_intent.measured_score`. At Module 5 Phase 1 step 6 the same file, measured with Module 5's formula, scored 80.2, because Module 5 counts the record key (`crm_id`, the RECORD_ID counterpart) as a structural key in the completeness denominator and the self-check had left it out. The claim that CRM_EXPORT sat in the 70-79 band was withdrawn; the generator's self-check was corrected to include the key, the data was confirmed byte-identical, and the registry now records 80.2. On this run no source reaches the 70-79 gate, so the remediation conversation INV-239 requires to be reachable does not happen.

### Why it matters

INV-239 exists so the generated scenario exercises the 70-79 gate. A self-check that scores with a different denominator than Module 5 can certify a band that Module 5 then does not see, and the bootcamper is told a band that does not hold.

### Suggested fix

State in Module 4 Step 2 (beside the band table) that the self-check must include the structural keys (RECORD_ID counterpart) in the completeness denominator exactly as Module 5 Phase 1 step 6 does, and give the band table's worked example with the key counted, so a generator targets the band Module 5 will measure.

### Context when reported

- **Time:** 2026-10-21 11:59 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** data_quality_mapping / step 6
- **Recent questions:** Are you done modifying the model and effort?
- **Bootcamper responses:** yes
- **Behind the scenes:** Module 5 Phase 1 step 6 quality assessment (`src/transform/assess_quality.py`); generator `src/scripts/generate_scenario_data.py` self-check.
- **Observed problem:** CRM_EXPORT measured 80.2 at Module 5 versus 77.9 at the Data collection self-check.
- **Expected behavior:** Module 4 Step 2 says to score the generated source using Module 5's formula, so the two figures should agree.
- **Divergence:** the self-check omitted the record key from the denominator; Module 5 counts it as a structural key.

## Improvement: Introduce the prediction questions before asking them

**Date:** 2026-10-21
**Module:** Query, Visualize and Discover
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the Discover phase's prediction steps (4a-pairs, 4b item 1a) and the ground rules' "Predictions before results" decide what is said before the questions; no MCP tool or host behavior is involved.
**Upstream:** not applicable

### What happened

The section where the Bootcamper predicts whether record pairs are the same entity, and which features joined an entity's records, began without being introduced. As a Bootcamper, I couldn't tell why these questions were being asked of me.

### Why it matters

The section on checking that the Bootcamper and Senzing agree is valuable, but without an introduction its purpose is lost and the questions feel arbitrary.

### Suggested fix

Before this section, tell the Bootcamper what is going to happen. Also tell the Bootcamper what will happen when the Bootcamper agrees with the Senzing engine, and what happens when the Bootcamper and the Senzing engine disagree.

### Context when reported

- **Time:** 2026-10-21 13:15 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 4b (completed: entity_resolution_concepts, business_problem, sdk_setup, system_verification, truthset_visualization, data_collection, data_quality_mapping, data_processing)
- **Recent questions:** "Are these two records the same entity?" (three pairs); "Which features do you think joined these records? Reply with the numbers, comma-separated — reply "skip" to just see the engine's answer."
- **Bootcamper responses:** 3 (skip), 1 (same), 1 (same); the features question was pending when feedback was given.
- **Behind the scenes:** module-07-query-visualize-discover, phase2-discover.md step 4a-pairs then step 4b item 1a (Truth Set alumni own-entity prediction), following ground-rules.md "Predictions before results".
- **Observed problem:** the first pair was introduced with one line ("Before Senzing explains its reasoning, you get to make the call on three pairs of records") and no explanation of the purpose, of what happens on agreement, or of what happens on disagreement.
- **Expected behavior:** neither step 4a-pairs nor "Predictions before results" requires an introduction to the prediction section; both specify only the pair presentation, the pinned 👉, and the reveal (prediction, engine call, agreed/differed, one line of engine evidence, never graded).
- **Divergence:** the guidance has no introduction step, so the guide followed it as written; the Bootcamper needed framing the skill does not ask for.

## Improvement: SQLite schema-exists check compares the table name case-sensitively

**Date:** 2026-10-21
**Module:** SDK setup
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the check is a command shipped in module-02-sdk-setup/SKILL.md; neither the MCP server nor the host is involved.
**Upstream:** not applicable

### What happened

SDK setup's "is the schema already applied?" check for SQLite runs `SELECT 1 FROM sqlite_master WHERE type='table' AND name='sys_cfg'`. On this install the table is recorded as `SYS_CFG`, so the check returned False on a datastore whose schema was applied. I verified it case-insensitively instead and told the bootcamper the check was wrong.

### Why it matters

A false "no schema" answer sends the next step toward re-applying the schema DDL to a datastore that already has it, and the guide has to notice the contradiction to avoid that.

### Suggested fix

Compare case-insensitively, e.g. `... AND lower(name)='sys_cfg'` (or `name = 'SYS_CFG' COLLATE NOCASE`), and keep the PostgreSQL form as it is.

### Context when reported

- **Time:** 2026-10-21 13:29 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** sdk_setup / step 7
- **Recent questions:** (retrospective at graduation)
- **Bootcamper responses:** (retrospective at graduation)
- **Behind the scenes:** SDK setup Step 7 schema check, SQLite branch.
- **Observed problem:** SDK setup's "is the schema already applied?" check for SQLite runs `SELECT 1 FROM sqlite_master WHERE type='table' AND name='sys_cfg'`.
- **Expected behavior:** The check returns True when the schema is applied.
- **Divergence:** The SQLite table name's case differs from the literal the check compares against.

## Improvement: Discover the Business Problem did not write config/data_sources.yaml

**Date:** 2026-10-21
**Module:** Discover the Business Problem
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the instruction is in module-01-business-problem/phase2-document-confirm.md; the guide followed the module and missed the write.
**Upstream:** not applicable

### What happened

Module 1 Phase 2 says to record each distinct scenario source into `config/data_sources.yaml`. The guide did not write it at that point; it was created later, during System verification, and that was disclosed then.

### Why it matters

Every later module reads the registry. A step this easy to pass over in a long phase is likely to be missed again, and the later module has to notice and repair it.

### Suggested fix

Make the registry write a named, checkpointed step in Module 1 Phase 2 (or have the module's completion step assert the file exists before the transition question).

### Context when reported

- **Time:** 2026-10-21 13:29 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** business_problem / phase 2
- **Recent questions:** (retrospective at graduation)
- **Bootcamper responses:** (retrospective at graduation)
- **Behind the scenes:** Module 1 Phase 2, Document and Confirm.
- **Observed problem:** Module 1 Phase 2 says to record each distinct scenario source into `config/data_sources.yaml`.
- **Expected behavior:** `config/data_sources.yaml` exists at the end of Module 1 with one entry per scenario source.
- **Divergence:** The write is one bullet inside a longer step and was skipped.

## Improvement: Data processing's gate does not define per-record match accuracy when an answer key exists

**Date:** 2026-10-21
**Module:** Data processing
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the iterate-vs-proceed gate's routing table is in module-06-data-processing/phaseD-validation.md.
**Upstream:** not applicable

### What happened

The gate routes on a "per-record match accuracy" figure but never says how to compute it. With the generated scenario's answer key available, two honest readings existed: merged records joined to the right person (2,519 of 2,519, 100%) and the share of true pairs found (recall 87.3%), and a third from the step-21 sample (8 of 10 groups as expected). I routed on the first and reported the others beside it; the other readings would have sent the bootcamper to the accuracy-shortfall branch and a remap that could not help (the misses were name-only records).

### Why it matters

The gate's branch, and therefore whether the bootcamper is told to remap, depends on a definition the guide has to invent.

### Suggested fix

Define the figure in the gate: e.g. per-record accuracy = merged records whose merge is correct ÷ merged records checked, with recall reported as a separate finding; say which sample it is computed on.

### Context when reported

- **Time:** 2026-10-21 13:29 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** data_processing / iterate-vs-proceed gate
- **Recent questions:** (retrospective at graduation)
- **Bootcamper responses:** (retrospective at graduation)
- **Behind the scenes:** Phase D gate after the match-key and how-state audits.
- **Observed problem:** The gate routes on a "per-record match accuracy" figure but never says how to compute it.
- **Expected behavior:** One defined accuracy figure decides the branch.
- **Divergence:** The term is used but not defined.

## Improvement: Module 7's Marginal band always asks proceed-or-iterate, even when the finding is not mapping-actionable

**Date:** 2026-10-21
**Module:** Query, Visualize and Discover
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the band rules are in module-07-query-visualize-discover/phase1-query-visualize.md step 3b.
**Upstream:** not applicable

### What happened

Possible matches landed at 11.7% (Marginal). The evidence showed 452 of 453 near-misses were name-only, caused by sparse CRM fields and deliberate name sharing, so remapping could not help. The Marginal rule still requires asking whether to proceed or iterate, while the stricter Poor band, given the same not-mapping-actionable finding, continues with no question. The bootcamper asked why the question was needed and whether it resolved anything; it did not.

### Why it matters

A question whose answer the evidence has already decided costs the bootcamper's trust in every later question.

### Suggested fix

Give the Marginal band the Poor band's three outcomes: ask only when the finding is mapping-actionable; otherwise state it and continue to 3c.

### Context when reported

- **Time:** 2026-10-21 13:29 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 3b
- **Recent questions:** (retrospective at graduation)
- **Bootcamper responses:** (retrospective at graduation)
- **Behind the scenes:** Step 3b quality evaluation, Marginal branch.
- **Observed problem:** Possible matches landed at 11.7% (Marginal).
- **Expected behavior:** No question when the evidence shows remapping cannot change the result (as in the Poor band's outcome 2).
- **Divergence:** The Marginal branch has no not-mapping-actionable exit.

## Improvement: Results-app graph cap drops nearly all relationships when cross-source entities exceed the cap

**Date:** 2026-10-21
**Module:** Query, Visualize and Discover
**Priority:** High
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the cap ordering is in scripts/senzing_viz_server.py (graph()), which Module 7's results server is modeled on.
**Upstream:** not applicable

### What happened

The graph endpoint caps nodes at 1,500 and ranks by source span first. This data has 2,098 cross-source entities, so the cap was filled entirely with them, while nearly all relationships join single-source entities. The relationship mode (the default view above 400 nodes) showed 2 of 914 related entities and 1 of 476 edges. I changed the ranking to keep every entity with a relationship first, then source span; it then showed 914 entities and all 476 edges, and the encoding self-check still passed.

### Why it matters

The default view of the bootcamp's 'wow moment' app looked empty of relationships on the bootcamper's own data, with no error, and the recap screenshots would have captured it.

### Suggested fix

In graph(), rank entities with at least one relationship ahead of source span (or reserve cap room for the related population), and say in the cap note which entities are kept first.

### Context when reported

- **Time:** 2026-10-21 13:29 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 3c
- **Recent questions:** (retrospective at graduation)
- **Bootcamper responses:** (retrospective at graduation)
- **Behind the scenes:** results_server.py built from senzing_viz_server.py, run on the export stream.
- **Observed problem:** The graph endpoint caps nodes at 1,500 and ranks by source span first.
- **Expected behavior:** Relationship mode shows the related population when it fits under the cap.
- **Divergence:** The cap ordering assumes cross-source entities are fewer than the cap.

## Improvement: Discoveries PDF subtitle says "your data" on a generated scenario

**Date:** 2026-10-21
**Module:** Query, Visualize and Discover
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the default subtitle is in scripts/generate_discoveries_pdf.py.
**Upstream:** not applicable

### What happened

docs/bootcamp_data_discoveries.pdf printed the cover subtitle "What Senzing found in your data" although every source was synthesized by the bootcamp. The Discover phase's own rule (INV-399) is to say "the data the bootcamp generated" on such a scenario, and the document's body does.

### Why it matters

The keepsake's cover contradicts its own first paragraph on the most common Core path.

### Suggested fix

Give generate_discoveries_pdf.py a --subtitle option (as generate_document_pdf.py has) and have step 3's deliverable pass a provenance-aware subtitle.

### Context when reported

- **Time:** 2026-10-21 13:29 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / data-discoveries deliverable
- **Recent questions:** (retrospective at graduation)
- **Bootcamper responses:** (retrospective at graduation)
- **Behind the scenes:** generate_discoveries_pdf.py default cover.
- **Observed problem:** docs/bootcamp_data_discoveries.pdf printed the cover subtitle "What Senzing found in your data" although every source was synthesized by the bootcamp.
- **Expected behavior:** Cover wording matches the data's provenance.
- **Divergence:** The subtitle is fixed in the generator.

## Improvement: Simplify graduation's "Next time" question

**Date:** 2026-10-21
**Module:** Bootcamp graduation
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — the question is pinned verbatim in skills/graduation/SKILL.md Step 0b; no MCP tool or host behavior is involved.
**Upstream:** not applicable

### What happened

The question "Next time there is no bootcamp script: what one request would you give an AI assistant with the Senzing MCP server to start a build on a new source of your own data?" is confusing.

### Why it matters

A confusing question is hard to answer, and it comes at the very end of the bootcamp, where the answer is meant to be the Bootcamper's starting point for their next build.

### Suggested fix

Simplify the question.

### Context when reported

- **Time:** 2026-10-21 13:39 EDT
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** graduation / 0b-next-time (completed: entity_resolution_concepts, business_problem, sdk_setup, system_verification, truthset_visualization, data_collection, data_quality_mapping, data_processing, query_visualize_discover)
- **Recent questions:** "In one line, what will you take away from this bootcamp?"; "Next time there is no bootcamp script: what one request would you give an AI assistant with the Senzing MCP server to start a build on a new source of your own data?"
- **Bootcamper responses:** "I have a better understanding of how to build with Senzing using Agentic AI."; the "Next time" question was pending when feedback was given.
- **Behind the scenes:** graduation Step 0b (hand over the ability), the pinned "Next time" question, asked verbatim per INV-056.
- **Observed problem:** the pinned question packs several ideas (no script, one request, an AI assistant with the Senzing MCP server, a new source of your own data) into one sentence.
- **Expected behavior:** the pinned wording, as Step 0b specifies it.
- **Divergence:** the guide asked the question as pinned; the wording itself is what the Bootcamper found confusing.

## Improvement: Production loader reads a bootcamp file that graduation excludes

**Date:** 2026-10-21
**Module:** Bootcamp graduation
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — Data processing has the loader read `database_type` from config/bootcamp_preferences.yaml, and graduation Step 2 excludes that file from production/; no MCP tool is involved.
**Upstream:** not applicable

### What happened

src/load/loader.py picks its worker count (1 on SQLite, 4 per core on PostgreSQL) from `database_type` in config/bootcamp_preferences.yaml. Graduation copies src/load/** into production/ verbatim but excludes config/bootcamp_preferences.yaml, so the production loader always falls back to 1 worker, even after a move to PostgreSQL. The same applies to src/query/ programs that read data/truth/scenario_truth.json, which is not copied either.

### Why it matters

The handed-over loader silently runs single-threaded on a production database. Nothing fails; it is only slow, so the cause is hard to find.

### Suggested fix

Have Data processing derive the database type from the engine configuration's `SQL.CONNECTION` (or an environment variable) rather than a bootcamp file, or have graduation Step 2 check copied code for reads of excluded paths and list them in the migration checklist. This run added a checklist item by hand.

### Context when reported

- **Time:** 2026-10-21 (graduation Step 4)
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-34-generic (x86_64)
- **Model / effort:** claude-opus-5-5
- **Module / step:** graduation / 4 (migration checklist)
- **Behind the scenes:** graduation Step 2 copy table and exclusion list; src/load/loader.py `database_type()`.
- **Observed problem:** the copied loader reads a path the copy excludes.
- **Expected behavior:** production/ code reads nothing that production/ does not contain.
- **Divergence:** the exclusion list and the loader's input were designed separately.
