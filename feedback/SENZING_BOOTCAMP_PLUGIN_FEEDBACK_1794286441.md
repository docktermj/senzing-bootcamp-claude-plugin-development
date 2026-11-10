# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp. Every entry is saved here, whatever it turns
out to be about. Entries routed `mcp-server` may **also** have been forwarded to Senzing —
only ever with your explicit yes, and with identifying details stripped; each entry's
`Upstream:` field records what happened.

**Started:** 2026-11-09

## Your Feedback

## Improvement: Data processing's record look-up question needs a preface explaining what and why

**Date:** 2026-11-09
**Module:** Data processing
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the question's framing comes from the bootcamp's own Phase D step 21 instructions (the "directing step"); no MCP tool output is involved.
**Upstream:** not applicable

### What happened

At the start of Phase D validation the bootcamp asked "Which of your records should I look up to check how Senzing resolved them? Name them in your own words, with what you expect Senzing to have done with them and why." with only a one-line lead-in. There was no preface explaining what this check does or why the bootcamper is being asked, so the purpose of the question was confusing.

### Why it matters

The bootcamper cannot give a useful answer to a question whose purpose they do not understand; the directing step loses its teaching value when it reads as an unexplained request.

### Suggested fix

Add a preface before the question that explains what is being done (looking up specific records to see how Senzing resolved them, and comparing that with what the bootcamper expected) and why (it is the bootcamper's chance to test their own expectations of the data against the engine's decisions, and "you pick" is a fine answer on generated data).

### Context when reported

- **Time:** 2026-11-09 21:58 EST
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64), Ubuntu 24.04
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown (long session; one compaction earlier)
- **Module / step:** data_processing / 21
- **Recent questions:** "The generated sources have no load-order dependencies, and I recommend the Sequential loading strategy for this dataset — shall I proceed on both?"; then "Which of your records should I look up to check how Senzing resolved them? Name them in your own words, with what you expect Senzing to have done with them and why."
- **Bootcamper responses:** "yes"; then this feedback instead of an answer.
- **Behind the scenes:** module-06-data-processing skill, phaseD-validation.md step 21 "directing step" (ground-rules "Directing steps"). It prescribes only a one-line lead-in before the pinned question ("this check looks at records they choose, and they can name records by ID or describe them").
- **Observed problem:** the question arrived after a long load summary with no explanation of the check's purpose or why the bootcamper's input is wanted.
- **Expected behavior:** a question the bootcamper can answer knowingly: what the check is, what they will see, and why their expectation is being asked for.
- **Divergence:** the skill's specified lead-in is a single line about how to name records, not why; the guide followed it as written, so the gap is in the step's instructions.

## Improvement: Record look-up question needs concrete examples to choose from, not only an open question

**Date:** 2026-11-09
**Module:** Data processing
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — Phase D step 21's directing question is the bootcamp's own pinned wording; no MCP tool output is involved.
**Upstream:** not applicable

### What happened

Even after a preface was added, the question "Which of your records should I look up to check how Senzing resolved them?" assumed the bootcamper knows what records they have. With bootcamp-generated data they do not, and with data they supply themselves they may not either.

### Why it matters

An open-ended question with no concrete starting point cannot be answered meaningfully, so the directing step stalls or degrades to "you pick".

### Suggested fix

Offer a short list of specific example records or record groups to choose among (drawn from the loaded data, e.g. a customer present in several sources, a same-name pair, a within-source duplicate), as numbered options, alongside the open-ended answer.

### Context when reported

- **Time:** 2026-11-09 22:12 EST
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64), Ubuntu 24.04
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown (long session; one compaction earlier)
- **Module / step:** data_processing / 21
- **Recent questions:** the step 21 directing question, re-presented after the previous feedback with a preface and generic ideas (cross-source customer, same-name pair, campaign duplicate) but no specific records.
- **Bootcamper responses:** this feedback instead of an answer.
- **Behind the scenes:** module-06-data-processing phaseD-validation.md step 21 directing step; ground-rules "Directing steps" (open question, "you pick" fallback). Related entry: the preface feedback filed just before this one.
- **Observed problem:** the bootcamper has no way to name records they have never seen.
- **Expected behavior:** a directing question the bootcamper can actually answer.
- **Divergence:** the step's design assumes the bootcamper knows their records; it offers only an open question plus "you pick", with no concrete candidates drawn from the loaded data.

## Improvement: Redesign Data processing's validation directing step as a guided, one-example-at-a-time expectation check

**Date:** 2026-11-09
**Module:** Data processing
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — the structure of Phase D step 21's directing step is defined by the bootcamp's own skill files; no MCP tool output is involved.
**Upstream:** not applicable

### What happened

After two earlier fixes (a preface, then a list of example records), the step was still not explained well. It still asked one open question covering several records at once, without stating its purpose or how the conversation would proceed.

### Why it matters

The step's purpose, checking that the bootcamper's expectations of entity resolution match Senzing's outcomes, is lost when it is presented as an unexplained open request; disagreements are where the learning happens, and the current design gives them no structure.

### Suggested fix

1. Explain what is happening and why: to verify that the Bootcamper's expectations of entity resolution match the outcomes generated by Senzing.
2. Tell the Bootcamper they will be given a few examples from the data and will work out the outcome, to verify that Senzing's outcome matches; where the outcomes differ, dialog with the Bootcamper to reach a common understanding of what should be done.
3. One at a time, give an example with potential outcomes; the Bootcamper selects an outcome or describes one in their own words; compare it with Senzing's outcome; on disagreement, dialog to either improve the Bootcamper's understanding of entity resolution or uncover a sub-optimal Senzing configuration (e.g. data mapping).
4. Keep providing examples until it is clear the Bootcamper and Senzing agree, or until the Bootcamper wants to move forward.

### Context when reported

- **Time:** 2026-11-09 22:46 EST
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64), Ubuntu 24.04
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown (long session; one compaction earlier)
- **Module / step:** data_processing / 21
- **Recent questions:** the step 21 directing question, re-presented with three example groups (a customer in three systems, a same-name pair, a repeat support ticket); a side question about whether get_capabilities works (answered: yes, server 1.46.0, 13 tools).
- **Bootcamper responses:** two earlier feedback entries on this same step (preface; concrete examples), then this redesign.
- **Behind the scenes:** module-06-data-processing phaseD-validation.md step 21 directing step and ground-rules "Directing steps" (a single open 👉 covering every record, then the result beside the expectation). Ground-rules "Predictions before results" already defines a one-at-a-time numbered prediction pattern used elsewhere (System verification's Mari record, Module 7's pairs); this step does not use it.
- **Observed problem:** a single open question over several records, with no stated purpose and no structure for working through a disagreement.
- **Expected behavior:** a guided expectation check: purpose stated, one example at a time with outcome options, comparison with Senzing's answer, a dialog on disagreement, and an explicit stopping rule.
- **Divergence:** the directing-step design asks for open, free-form direction; the bootcamper needs a structured prediction-and-compare loop, which the plugin already has elsewhere but does not use here.

## Improvement: Query requirements question needs business-case examples, an invitation to add more, and multi-select

**Date:** 2026-11-09
**Module:** Query, Visualize and Discover
**Priority:** High
**Source:** bootcamper-reported
**Routing:** plugin — step 1's open question and INV-359 (no derived requirement shown before the answer) are the bootcamp's own skill text; no MCP tool output is involved.
**Upstream:** not applicable

### What happened

Step 1 opened with only "What do you want to find out about your data?", which is too open-ended.

### Why it matters

Without a starting point the bootcamper has to invent questions cold, even though the business problem documented in Discover the Business Problem already says what they care about.

### Suggested fix

After the question, suggest 2–4 example questions derived from the documented business case, invite the bootcamper to add requests of their own, and let them pick one or more examples (multi-select) plus their own additions. This conflicts with INV-359, which forbids showing any derived requirement in Turn 1, so that rule needs revisiting.

### Context when reported

- **Time:** 2026-11-09 23:01 EST
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown (long session; compacted earlier)
- **Module / step:** query_visualize_discover / 1
- **Recent questions:** module transition (answered "yes"), then step 1's open question.
- **Bootcamper responses:** this feedback instead of an answer.
- **Behind the scenes:** module-07 phase1-query-visualize.md step 1 Turn 1 (directing step; INV-359 forbids showing derived requirements first). Related to the Data processing step 21 entries asking for concrete examples.
- **Observed problem:** open question with no examples.
- **Expected behavior:** examples from the business case, an invitation to add more, and multi-select.
- **Divergence:** the skill deliberately withholds examples in Turn 1.

## Improvement: The "you vs. Senzing" prediction exercise runs twice — keep it in Data processing only

**Date:** 2026-11-09
**Module:** Query, Visualize and Discover
**Priority:** Not stated (the bootcamper answered the priority question with a direction instead)
**Source:** bootcamper-reported
**Routing:** plugin — both prediction sites (Data processing Phase D step 21 and Discover step 4a-pairs, plus step 4b item 1a) are the bootcamp's own skill text under ground-rules "Predictions before results"; no MCP tool output is involved.
**Upstream:** not applicable

### What happened

After Data processing's step 21 expectation check (redesigned per earlier feedback as a one-example-at-a-time "you vs. Senzing" comparison), Discover's step 4a-pairs asked the same kind of question again ("Are these two records the same entity?"), and step 4b item 1a would have added a third.

### Why it matters

Repeating an exercise the bootcamper has already done reads as the bootcamp not knowing what it has covered, and costs turns.

### Why it is in two places (answer given to the bootcamper)

Each module adds its own prediction point under the shared "Predictions before results" rule (INV-357), and the module files are authored independently. Data processing's version validates the load; Discover's warms up the why/how demonstrations. Once step 21 was reshaped, the two became nearly identical, and nothing checks for cross-module duplication.

### Suggested fix (bootcamper's decision)

"Implement the best practices of the exercise in the 'Data processing' module only." Keep the prediction exercise solely in Data processing step 21 (one example at a time, outcome options, dialog on disagreement). Remove Discover's step 4a-pairs and step 4b item 1a; Discover's Why analysis should explain an engine decision without a fresh prediction, ideally reusing a Data processing example.

### Context when reported

- **Time:** 2026-11-09 23:18 EST
- **Plugin version:** 0.7.0
- **Workstation:** Linux 7.0.0-42-generic (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown (long session; compacted earlier)
- **Module / step:** query_visualize_discover / 4a (4a-pairs, pair 1 of 3 shown)
- **Recent questions:** Discover opt-in (yes); 4a-pairs pair 1 (Rick Oakshaw vs Rick Larkshaw).
- **Bootcamper responses:** this feedback instead of an answer; then the decision above.
- **Behind the scenes:** module-07 phase2-discover.md steps 4a-pairs and 4b item 1a; module-06 phaseD-validation.md step 21; ground-rules "Predictions before results".
- **Observed problem:** the same prediction exercise in two modules.
- **Expected behavior:** the exercise once, in Data processing.
- **Divergence:** prediction sites are defined per module with no cross-module de-duplication.
- **Applied in this run:** Discover's prediction pairs and step 4b's prediction were skipped at the bootcamper's direction.

## Improvement: Visualization server pid captured at launch is the shell wrapper, so teardown's kill does not stop the server

**Date:** 2026-11-09
**Module:** Query, Visualize and Discover
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — step 3c / teardown say "stop it by the pid captured when it was started" but give no launch pattern that yields the server's own pid; no MCP tool output is involved.
**Upstream:** not applicable

### What happened

The results server was started in the background through the harness shell (`nohup python3 ... &`). `pgrep -f` matched the wrapping `bash -c` first, so the recorded pid was the wrapper. At teardown, killing it reported "stopped" while the server kept listening on port 8081; the port check caught it and the real pid had to be found from `ss -ltnp`.

### Why it matters

Without the port check, teardown would have reported a stopped server that was still running, which is the failed-stop case INV-394 warns about.

### Suggested fix

Have step 3c record the listening process's pid from the port (e.g. `ss -ltnp` / `lsof -i :<port>`) after the server prints its ready line, or have the server write its own pid file, and make the teardown check the port before reporting.

### Context when reported

- **Time:** 2026-11-09 (graduation retrospective)
- **Plugin version:** 0.7.0
- **Workstation:** Linux (x86_64)
- **Model / effort:** claude-opus-5-5 / high
- **Module / step:** query_visualize_discover / 3c and teardown
- **Observed problem:** wrong pid recorded; first kill left the server running.
- **Expected behavior:** the recorded pid stops the server.
- **Divergence:** the skill names a pid but not how to capture the right one when launched through a shell.

## Improvement: Reference visualization server imports brand_tokens at runtime, contradicting step 3c's "inline the tokens" rule

**Date:** 2026-11-09
**Module:** Query, Visualize and Discover
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the shipped `senzing_viz_server.py` and step 3c's INV-081 instruction disagree.
**Upstream:** not applicable

### What happened

Step 3c says the project's `results_server` must never import `brand_tokens.py` and must carry the token values itself. The reference server it is modeled on does `import brand_tokens as _bt` with an inlined fallback. Copying it into `src/server/` required hand-editing the import out so the inlined fallback is always used; a first edit (prepending a header docstring) also broke `from __future__ import annotations`, which must stay first in the file.

### Why it matters

Every Python run copies the reference the same way, so every guide repeats this edit, and getting it wrong only shows when the server fails to start.

### Suggested fix

Ship the reference with a `--no-plugin-imports` mode or a ready-to-copy project variant whose tokens are inlined, and document the copy step (keep the shebang and `from __future__` first).

### Context when reported

- **Time:** 2026-11-09 (graduation retrospective)
- **Plugin version:** 0.7.0
- **Model / effort:** claude-opus-5-5 / high
- **Module / step:** query_visualize_discover / 3c
- **Observed problem:** reference server and skill rule disagree; manual edit needed.
- **Expected behavior:** a copy that satisfies INV-081 without edits.
- **Divergence:** the reference was written for running from the plugin, not for copying into the project.

## Improvement: Query programs write outputs relative to the current directory, which drifts during a session

**Date:** 2026-11-09
**Module:** Query, Visualize and Discover
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — "Building and running a program" gives run commands but no rule that programs resolve output paths from the project root.
**Upstream:** not applicable

### What happened

Three new query programs wrote `data/query_results/*.json` relative to the working directory. They were run from `src/query/` (the shell's directory had drifted there), so the files landed in `src/query/data/query_results/` and later steps could not find them until they were moved.

### Why it matters

The working directory drifts in long sessions, and production copies of these programs will be run from other directories too.

### Suggested fix

State in ground-rules that generated programs resolve project paths from the project root (e.g. `Path(__file__).resolve().parents[2]`) rather than the current directory.

### Context when reported

- **Time:** 2026-11-09 (graduation retrospective)
- **Plugin version:** 0.7.0
- **Model / effort:** claude-opus-5-5 / high
- **Module / step:** query_visualize_discover / 2
- **Observed problem:** outputs written under `src/query/data/`.
- **Expected behavior:** outputs under the project's `data/`.
- **Divergence:** no rule pins output paths to the project root.

## Improvement: Packager excludes config/license.json but not its copy in backups/revisit/state/

**Date:** 2026-11-09
**Module:** Bootcamp graduation (packaging)
**Priority:** Medium
**Source:** bootcamper-reported
**Routing:** plugin — graduation Step 6b copies config/license.json into backups/revisit/state/, and package_bootcamp.py's exclusion rule matches only the config/ path; no MCP tool output is involved.
**Upstream:** not applicable

### What happened

The transfer package (backups/packages/senzing-bootcamp-transfer-20261110.zip, built twice) excluded config/license.json by rule, yet included backups/revisit/state/license.json, the snapshot graduation Step 6b made of the same file.

### Why it matters

packaging.md says config/license.json is never packaged in either profile; the copy defeats that rule silently, and the dry-run manifest does not flag it.

### Suggested fix

Exclude license files by name wherever they sit (e.g. any `license.json` or `*.lic` under backups/revisit/state/), or have Step 6b not snapshot config/license.json, or record it in RESUME_STATE.json as "supply on restore".

### Context when reported

- **Time:** 2026-11-09 23:40 EST
- **Plugin version:** 0.7.0
- **Model / effort:** claude-opus-5-5 / high
- **Module / step:** graduation complete; /package-bootcamp, transfer profile
- **Recent questions:** packaging question (answered 2, twice).
- **Behind the scenes:** package_bootcamp.py --profile transfer; graduation Step 6b state snapshot.
- **Observed problem:** license copy included in the archive.
- **Expected behavior:** no license file in either profile.
- **Divergence:** the exclusion is path-specific; the snapshot copy has a different path.
