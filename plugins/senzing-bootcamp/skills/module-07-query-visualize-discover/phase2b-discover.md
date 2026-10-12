# Module 7, Phase 2b: Discover, Part B (steps 4d–4e)

Follow the ground rules. `🛑`/`⛔` are internal directives, never render them; signal a stop by
ending the turn on the single 👉 question and waiting. On load, read
`config/bootcamp_progress.json` and check which 4x sub-steps are already checkpointed under
`module_7_query.steps`. Resume from the first incomplete step; do not re-run completed
demonstrations.

Load this file after completing steps 4a–4c in `phase2-discover.md`, or for step 4e alone from any
Discover exit (the opt-in decline and the two early exits in `phase2-discover.md`). When complete,
return to `phase1-query-visualize.md` for the Query Completeness Gate.

**No direct SQL and no fabricated methods (see SKILL.md):** `find_network` and `find_path` are
SDK methods, not MCP tools. Generate the SDK code, sourcing flags and signatures from
`get_sdk_reference` and network/path patterns from `reporting_guide(topic='graph', language='<chosen_language>')`. Never
query `database/G2C.db` tables directly.

## Step 4d: Discover (continued)

### Step 4d: Relationship network exploration

Demonstrate relationship-network exploration using entities identified in step 4a that have
disclosed relationships or shared attributes. This teaches the bootcamper how to explore
connections between entities using `find_network` and `find_path`.

1. **Entity selection:** use entities from step 4a with disclosed relationships or shared
   attributes. State which and why: "I'll use Entities [ID1], [ID2], and [ID3], which have
   disclosed relationships or shared attributes. These give us a connected set of entities to
   explore as a network."
2. **Flag and response-shape lookup:** before generating the `find_network` or `find_path` calls,
   look up available flags **and the response structure** (the narrowing parameter is `filter`,
   not `method`):
   - `get_sdk_reference(topic='flags', filter='find_network')` and
     `get_sdk_reference(topic='response_schemas', filter='find_network')` for network exploration.
   - `get_sdk_reference(topic='flags', filter='find_path')` and
     `get_sdk_reference(topic='response_schemas', filter='find_path')` for path finding.

   ⛔ **Look up the response structure before writing any code that parses the response — never
   infer field names from an example snippet** (INV-115).

   ⚠️ **That lookup reaches inside a link element — and neither the array name nor the
   endpoint names are the ones you would guess.** For each graph method `response_schemas`
   returns **that method's own** outer arrays **and** each link element's own fields
   (re-verified on MCP server 1.32.2, docs indexed 2026-07-29 11:11 UTC, 2026-07-31).
   **The two documents differ in exactly one key — the array you index by.** `find_path`
   returns its edges under **`ENTITY_PATH_LINKS[]`**; `find_network` returns them under
   **`ENTITY_NETWORK_LINKS[]`**. Everything else matches **across the two documents**: both carry
   `ENTITIES[]` and `ENTITY_PATHS[]` with the same sub-fields (`START_ENTITY_ID`, `END_ENTITY_ID`,
   `ENTITIES[]`), and **both link elements carry the same seven fields**, which is what makes the
   array name the one difference a shared parser misses. ⛔ **That is a claim about the two
   DOCUMENTS and nothing more — it does not mean the endpoint convention is uniform.** See the
   within-response trap below, which this sentence would otherwise talk you out of noticing.
   `find_network` returning `ENTITY_PATHS[]` is the sharpest edge of it — seeing "PATH" in a
   network response is not evidence that `ENTITY_PATH_LINKS[]` is there.
   **The matching-info flags are paired, not shared:** `SZ_FIND_PATH_INCLUDE_MATCHING_INFO`
   has `applies_to` of the two `find_path_*` methods, `SZ_FIND_NETWORK_INCLUDE_MATCHING_INFO`
   of the two `find_network_*` methods, and each default composite carries its own. So
   **neither the flags nor the parser can be carried from one of these calls to the other** —
   do it and you get a path whose entity names render while every edge prints
   `(link detail not returned)`, which reads as a path with no relationship detail rather than
   as two wrong names at once (INV-148). Route: `get_sdk_reference(topic='response_schemas',
   filter='find_path')` and the same with `filter='find_network'` (server 1.32.2, docs indexed
   2026-07-29 11:11 UTC, verified 2026-07-31). Dump one raw link element and read
   its keys anyway before writing the parser. Do **not** assume a link's two
   endpoints use the `ENTITY_ID` / `RELATED_ENTITY_ID` pairing that related-entity records use:
   two sessions found both endpoints blank under those names while `MATCH_KEY` rendered fine, and
   a live dump on SDK 4.3.3 found them under **`MIN_ENTITY_ID` / `MAX_ENTITY_ID`** (normalized
   low-to-high) — which is what the schema now documents too. Those keys are recorded in
   `../module-03b-truthset-visualization/visualization-api-reference.md` → "MCP-confirmed response
   paths"; they were dump-only when first recorded, so they are MCP-confirmed names rather than an
   unverified caution. **Run the lookup and dump anyway** — its coverage grows, this entry is proof of
   that, and the dumped element remains the authority for what your installation returns (INV-080).
   An empty or shallow result is still coverage, not a failed call — do not retry it (INV-149).

   ⛔ **The second wrong endpoint guess, and the worse one: ONE `find_network` response uses two
   different endpoint conventions.**

   | Array in that one response | Endpoint keys |
   |---|---|
   | `ENTITY_PATHS[]` | `START_ENTITY_ID` / `END_ENTITY_ID` — **directed** |
   | `ENTITY_NETWORK_LINKS[]` | `MIN_ENTITY_ID` / `MAX_ENTITY_ID` — **undirected**, normalized low-to-high |

   (Re-verified on MCP server 1.32.9, 2026-08-17, via `get_sdk_reference(topic='response_schemas',
   filter='find_network', language='java')`.)

   ⚠️ **`START_`/`END_` is the natural wrong guess precisely BECAUSE the sibling array in the same
   response uses it** — unlike the `ENTITY_ID`/`RELATED_ENTITY_ID` guess above, which comes from a
   different call's shape. The reason for the split is what makes it stick: **a link is an unordered
   pair, a path is directed**, so a link normalizes its endpoints and a path preserves its
   direction. Read the endpoint names off a link element, never off a path.

   Observed cost: all **38 edges** of a corporate hierarchy printed `null -> null`, with no error —
   and a silently empty edge list is indistinguishable from *"this data has no relationships"*, which
   is the wrong conclusion to hand an analyst in the capability the fraud-detection pattern leans on
   hardest.

   ⛔ (INV-080) **Per-record source values come from the entity call itself, with the right flag
   OR-ed in.** `RECORDS[].JSON_DATA` needs `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA`, which
   `SZ_ENTITY_DEFAULT_FLAGS` omits. Without it those paths render blank for every record, and the fix
   is the flag, not a switch to `get_record`. For the mapped attributes instead, use
   `RECORDS[].FEATURES.<TYPE>[].ATTRIBUTES.*` with `SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS`. The
   two routes, their paths and the flags' `applies_to` are in the same reference section.

   ⛔ **If some fields of a row populate and others come back blank, suspect the blank ones' names
   — not the data.** A half-populated row reads as a real result precisely because part of it
   worked, which makes it more deceptive than an empty one (INV-115).

   ⛔ **Confirm the ARGUMENT types before writing the call — and note you may already have
   them.** `get_sdk_reference` returns a `method_signatures` block whenever `filter` names a
   method, under **any** topic, so the signature is already in the `flags` or
   `response_schemas` response you just read (verified on MCP server 1.32.2, 2026-07-30).
   Where you hold neither, ask directly:
   `get_sdk_reference(topic='parameters', filter='find_network_by_entity_id')`. Read the one for
   the bootcamper's language: cross-language documentation is **not** authoritative for the
   shape you pass, and it is wrong for Python here.

   For **Python**, both graph methods take native collections, not an entity-IDs JSON document:

   ```text
   find_network_by_entity_id(entity_ids: List[int], max_degrees: int,
                             build_out_degrees: int, build_out_max_entities: int, flags: int)
   find_path_by_entity_id(start_entity_id: int, end_entity_id: int, max_degrees: int, ...)
   ```

   So pass `[300418, 501752, 500174]` — **not**
   `json.dumps({"ENTITIES": [{"ENTITY_ID": 300418}, ...]})`, which the flags documentation and the
   Java/C# signatures imply and which raises
   `SzSdkError: value {"ENTITIES": [...]} has type str, should be a list of int(s)`. (Credit to
   the SDK: that error names the expected signature outright, so recovery is immediate — but the
   round trip is avoidable.)

   For any other language, confirm the shape for that binding with
   `get_sdk_reference(topic='parameters', filter='<method>', language='<chosen_language>')` rather
   than copying Python's or another language's form (INV-002 — this module is language-agnostic;
   only the *known-divergent* case is spelled out). Only where that topic does not answer for the
   binding, fall back to the installed binding itself: its own reference, `help()`, or equivalent
   introspection (INV-132).

   Select flags appropriate for relationship exploration and explain each: "I'm using [flag] so
   we can see [what it provides]." For example: "I'm using [relationship detail flag] so we can
   see the full attribute information for each entity in the network. This helps us understand
   what connects them."
3. **find_network demonstration:** call `find_network` with a set of related entity IDs (at
   least 2–3 of the entities with relationships from step 4a). Present the resulting network
   structure:
   - **Which entities are connected:** list each entity and its connections, with entity IDs
     and brief identifying information (name, data source).
   - **What attributes they share:** for each connection, explain the common attributes —
     shared addresses, phone numbers, names, or other features that create the link.
   - **Degrees of separation:** show how many hops separate each pair. "Entity A is directly
     connected to Entity B (1 degree), and Entity B connects to Entity C (so A and C are 2
     degrees apart)."

   Present this as a clear textual network diagram or structured list so the bootcamper can
   follow the connections.
4. **find_path demonstration:** demonstrate `find_path` between two indirectly connected
   entities (2+ degrees of separation if available). On address-dense data almost every candidate
   pair is directly linked, so do not pick pairs at random. **Find a 2+ degree pair with the hub
   method:**
   1. Take the entity with the most relationships from step 4a — the **hub**.
   2. Pick two of its neighbors that are **not related to each other**: neither appears among the
      other's related entities.
   3. Confirm with `find_path`: a shortest path of **2 or more degrees** means the pair is good. Set
      the degree limit high enough to return a 2-degree path, taking the parameter's name and type
      for the bootcamper's binding from `get_sdk_reference` (the signature above), never from
      another language.
   4. If the pair turns out to be directly linked, try another pair of the hub's neighbors, then
      the next hub (the entity with the next-most relationships). A hub with fewer than two
      neighbors is skipped. **Stop after three hubs.**

   **If no 2+ degree pair is found after three hubs,** demonstrate `find_path` on a directly
   linked (1-degree) pair instead, and say plainly that this data has no path of 2+ degrees to
   show: "In your data, every pair I checked is directly connected, so there's no path of 2 or
   more degrees to show. Here is `find_path` on a direct connection instead." In that case, leave
   out the "these aren't directly connected" line below.

   ⛔ **(INV-239) On a generated scenario that promised households, this fallback is a bootcamp
   defect.** The scenario promised them when a loaded source's entry in `config/data_sources.yaml`
   records `provenance: synthesized` and its `quality_intent` carries a `relationship_intent`, or
   when a loaded source records `provenance: synthesized` and the scenario's success criteria in
   `docs/business_problem.md` name households or related parties. The second test covers a scenario
   generated before `relationship_intent` existed. Either way, Data collection was required to
   generate households and the chains between them, which give a path of 2 or more degrees. Reaching
   this fallback, or step 7's, on such a scenario means the bootcamp's generated data is missing what
   its scenario promised, not that the Bootcamper's data lacks it. Say so plainly with the fallback,
   and suggest `/bootcamp-feedback`: "This scenario promised households and related people, so there
   should be a path of 2 or more degrees here. It's missing because of a defect in the data the
   bootcamp generated, not anything about your data. You can report it with `/bootcamp-feedback`."
   On a CORD source, the Bootcamper's own data, or a generated scenario with no `relationship_intent`
   and no success criterion naming households or related parties, the fallback's wording stands as
   written.

   Show the shortest path of relationships:
   - State which two entities and why: "Let's find the shortest path between Entity [ID1] and
     Entity [ID2]. These aren't directly connected, so we'll see the intermediate entities
     that link them."
   - Present each step in the path: Entity A → Entity B → Entity C, with the connecting
     attributes at each hop.
   - Explain what the path reveals about the relationship between the two endpoints.
5. **Network structure explanation:**
   - **How entities connect through shared attributes:** "Entities in Senzing connect through
     shared features, when two entities share an address, phone number, or other attribute,
     that creates a relationship link between them."
   - **What relationship types mean:** explain disclosed relationships (explicitly stated in
     source data, like 'spouse' or 'employer') versus discovered relationships (inferred from
     shared attributes like a common address).
   - **How to interpret degrees of separation:** "Degrees of separation tell you how many
     entity-to-entity hops connect two entities. Direct connections are 1 degree; connections
     through an intermediary are 2 degrees, and so on."
6. **Practical use cases:**
   - **Fraud ring detection:** "find_network reveals clusters of connected entities that share
     attributes. This is how investigators discover fraud rings where multiple identities
     share addresses, phones, or other features."
   - **Supply chain analysis:** "Tracing entity connections helps identify hidden relationships
     between suppliers, intermediaries, and end customers in complex supply chains."
   - **Beneficial ownership tracing:** "find_path can trace the chain of relationships from a
     company to its ultimate beneficial owners through intermediate entities."
   - **Customer household grouping:** "find_network identifies entities that share a household
     address, helping group related customers for marketing or risk assessment."
7. **Graceful fallback (no relationships in data):** if the bootcamper's data contains no entity
   relationships or disclosed connections (as determined in step 4a), do NOT attempt the live
   demonstration. Instead:
   - ⛔ **(INV-239) On a generated scenario that promised households** (the condition in step 4's
     generated-scenario paragraph, including a scenario whose success criteria name households or
     related parties), first say that the bootcamp's generated data is missing the
     relationships its scenario promised, that this is a bootcamp defect rather than a property of
     the Bootcamper's data, and suggest `/bootcamp-feedback`. Then continue below.
   - State: "Your data doesn't contain disclosed relationships, so I'll explain what this would
     look like with connected data."
   - Describe what `find_network` returns when entities are connected: a graph structure with
     entity nodes, relationship edges, shared attributes at each connection, and degrees of
     separation.
   - Describe what `find_path` returns: an ordered list of entities forming the shortest path
     between two endpoints, with the connecting attributes at each hop.
   - Explain the SDK methods conceptually so the bootcamper understands how to use them with
     relationship-rich data.
   - Write step 4d status as `"skipped"` with reason `"no_relationships"` in the checkpoint.
8. **Transition:** relationship-network exploration is the final Discover demonstration. After
   presenting it (or the fallback above), write this step's checkpoint and continue to step 4e
   below. Ask no transition question here: step 4e's export offers come next, and Discover ends
   at step 4e's close without one.

**Checkpoint:** write step 4d under `module_7_query.steps.4d`:

- If relationships were demonstrated: `{"status": "completed"}`.
- If no relationships exist in data: `{"status": "skipped", "reason": "no_relationships"}`.

Include the `reason` field only when the step is skipped. Also set top-level `current_step` to
`"4d"`.

### Step 4e: Export for the systems named in Module 1

Module 1 Step 10a asked whether the results must interface with other software, and held the
systems the Bootcamper named as `integration_targets` in `config/bootcamp_preferences.yaml`
(INV-097). This step is where that answer is acted on: it offers to export the resolved results
in each named system's import format, proves the export carries the entities, the relationships
between them and the business attributes asked for, and only then hands the file over.

**It runs on every path:** after step 4d, and from every Discover exit (the opt-in decline and the
two early exits in `phase2-discover.md`). The export reads the loaded data, not Discover's
findings, so a skipped or shortened walkthrough changes nothing here. On resume, do not re-offer a
system already recorded under `module_7_query.steps.4e.targets` (INV-006).

The step does not load the export into the target system, and no vendor's tooling is a
prerequisite: the deliverable is the written file (or files) and the program that writes them.

⛔ **No target's import format ships in this plugin: take it from your own knowledge of the system, or from the Bootcamper.**
There is no template, schema or column list here to copy for any system, and no fixed list of
supported systems.

1. **Read the targets.** Read `integration_targets` from `config/bootcamp_preferences.yaml`. A
   missing key or an empty list means no system was named.
2. **No system named.** Say so as a statement first: "In Module 1 you didn't name a system your
   results need to feed, so there's nothing set up to export for." Then offer once (INV-006):

   👉 **Is there a system you'd like your resolved results exported for? If so, name it.**

   *(Internal: end the turn on this question and wait.)* A reply that names a system continues at
   item 3's **Yes** branch for that one system, without asking item 3's question again. Record it
   in this step's checkpoint, not in `config/bootcamp_preferences.yaml`, which Module 1 owns.
   ⛔ **Any reply that does not name a system ends the step with nothing produced.**
   Write the checkpoint `{"status": "skipped", "reason": "no_target"}` and go to the close
   below.
3. **Offer, one system per turn.** For each named system, in the order Module 1 recorded them,
   each offer in a turn of its own (INV-251):

   👉 **Would you like me to export your resolved results in [system]'s import format?**

   *(Internal: end the turn on this question and wait.)* `[system]` is the name as recorded.
   - **No:** record `{"system": "<name>", "status": "declined"}` and offer the next system on the
     next turn.
   - **Yes:** run items 4–10 for this system, then offer the next one.
4. **Name the target format.** From your own knowledge of the system, state its import format and
   the files it takes (a property-graph database, for example, often takes one file of nodes and
   one of edges), so the Bootcamper can correct you before anything is written.
   ⛔ **When you cannot name the format confidently, say so and ask for it; write nothing until it arrives, and never invent one.**
   Ask:

   👉 **I don't know [system]'s import format well enough to write it without guessing. Could you share the format, or a link to its documentation?**

   *(Internal: end the turn on this question and wait.)* Write the export from what they share. If
   they have neither, record `{"system": "<name>", "status": "skipped", "reason":
   "format_unknown"}`, write nothing for this system, and offer the next one.
5. **Ask which business attributes the nodes must carry.** Senzing resolves the entities and the
   relationships; the business payload, such as amounts, account roles or statuses, is in the
   source records' own fields. Ask, as its own turn:

   👉 **Which fields from your source records should each node carry (for example, amounts or account roles)? Reply "none" if the entities and relationships are enough.**

   *(Internal: end the turn on this question and wait.)* Hold the fields named; item 9 checks the
   export against them.
6. **Take the Senzing side from the MCP server, at this step.** ⛔ (INV-080) Which SDK calls and flags the program uses, and which entities and relationships become nodes and edges, come from the server now, never from this file or from memory:
   - `reporting_guide(topic='graph', language='<chosen_language>')`: the export and network
     patterns, and the graph anti-patterns.
   - `reporting_guide(topic='data_mart', language='<chosen_language>', scale='<scale>')`: the
     relationship pattern an edge list follows. The topic requires `scale`; take it from the
     topic's own decision tree against the loaded record count rather than asking another
     question.
   - `get_sdk_reference(topic='flags', filter='export_json_entity_report')` and
     `get_sdk_reference(topic='response_schemas', filter='export_json_entity_report')`: the export's
     flags and its row shape. The method's signature for the Bootcamper's binding comes back with
     them; read that binding's, not another language's.

   ⛔ **Edges are Senzing relationships, each carrying its match type and match key; never write an edge per shared feature.**
   That is the `graph` topic's own anti-pattern (server 1.37.27, 2026-10-11): feature-level edges
   bloat the graph with noise.
7. **Check one export row before writing the reader.** ⛔ (INV-115) Dump one row and read its top-level keys before any code parses the export.
   Generate a short program that opens the export with the flags chosen in item 6, fetches one
   row, prints its top-level keys, and prints whether one of its records carries that record's
   source JSON (`JSON_DATA`). Show the Bootcamper the keys. Then:
   - **`RELATED_ENTITIES` is absent:** the flags did not ask for relationships. Find the
     relationship flags in item 6's `flags` response, add them, and dump again. If it is still
     absent there are no relationships to export; continue, and item 9 reports the zero-edge
     failure with this result.
   - **Business attributes need a per-record `get_record` pass.** The fields asked for in item 5
     live in each record's `JSON_DATA`, and `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA` is the flag that
     returns it. Re-ask before relying on this:
     `get_sdk_reference(topic='flags', filter='SZ_ENTITY_INCLUDE_RECORD_JSON_DATA')`. On server
     1.37.27 (2026-10-11) its `applies_to` lists `get_record` and the entity, search, why, path
     and network calls, but neither export method, so an export row does not carry the record JSON
     however its flags are set; `get_record`'s default composite, `SZ_RECORD_DEFAULT_FLAGS`, is
     that one flag. So for each record in each exported entity, call `get_record` and read the
     fields from its `JSON_DATA`. If the lookup now lists an export method and the dumped row
     already carries `JSON_DATA`, read the fields from the row and skip the pass: the dumped row is
     the authority for what this installation returns.
     <!-- MCP-NEGATIVE: get_sdk_reference(topic='flags', filter='SZ_ENTITY_INCLUDE_RECORD_JSON_DATA') — its applies_to names get_record and the entity, search, why, path and network calls, and neither export_json_entity_report nor export_csv_entity_report — owner: the flag's own applies_to IS the route that carries which methods accept it; search_docs returns the Java SzFlag javadoc listing SZ_EXPORT_FLAGS among its usage groups, which is why the dumped row decides (absence negative) — server 1.37.27, 2026-10-11 -->
8. **Write and run the export program.** Write it in the Bootcamper's chosen language
   (`programming_language` in `config/bootcamp_preferences.yaml`, INV-002), with the SDK code
   sourced as item 6 says, and save it under `src/query/` (for example
   `src/query/export_<system>.<ext>`), so graduation's existing `src/query/**` copy carries it into
   `production/` unchanged. It writes its files under `data/temp/exports/<system>/`, which it
   recreates on every run. Run it.
9. **Count what was written, then report it.** ⛔ (INV-129) Count from the written files, never from the exit status or the program's own log:
   - the **entity count**: nodes written;
   - the **edge count**: edges written;
   - the **attribute count**: nodes that carry the fields asked for in item 5 (left out when the
     answer was "none").

   Report all three to the Bootcamper.
   ⛔ **A zero edge count is a failure, never a finished export.**
   Say the export failed, give item 7's result (whether `RELATED_ENTITIES` appeared, and with
   which flags), and do not hand the file over as finished. Record `"status": "failed", "reason":
   "zero_edges"` for this system. When step 4a found no relationships in the data, say that too.
   When the fields asked for are on no node, report the attribute count as zero and name item 7's
   `get_record` pass as the first cause to check.
10. **Hand over.** When the edge count is above zero, give the path of each written file and of the
    program, and the command that reruns it. Record `"status": "exported"` with the format, the
    program, the outputs and the three counts.

**Close: no transition question.** When every named system has been offered (or the single offer
in item 2 was answered), ask no question about moving on. Both answers to one would take the same
route, so a "yes" there would carry no decision (#488). In the same turn that settles the last
offer, continue to Discover phase completion below, then to the Query Completeness Gate in
`phase1-query-visualize.md`. End that turn on the next 👉 the flow already has, never on a new one
(INV-251): the visualization server teardown question (`phase1-query-visualize.md` → "Visualization
server teardown"), or, when no server was started, the graduation offer at the end of Module
Completion. Each offer above still ends its own turn. This close is the same on every path: entered
from step 4d, or from a Discover exit, where the Bootcamper already chose to move on at that exit's
question.

**Checkpoint:** write step 4e under `module_7_query.steps.4e`:

- When no system was named and none was given at item 2:
  `{"status": "skipped", "reason": "no_target"}`.
- Otherwise `{"status": "completed", "targets": [...]}`, one entry per system, each written as
  soon as that system's offer is settled: `{"system": "<name>", "status": "declined"}`,
  `{"system": "<name>", "status": "skipped", "reason": "format_unknown"}`, `{"system": "<name>",
  "status": "failed", "reason": "zero_edges", "entities": <n>, "edges": 0, "attribute_nodes":
  <n>}`, or `{"system": "<name>", "status": "exported", "format": "<format>", "program":
  "src/query/<file>", "outputs": [...], "entities": <n>, "edges": <n>, "attribute_nodes": <n>}`.

Also set top-level `current_step` to `"4e"`.

### Discover phase completion

After step 4e is complete (or after any early exit), update the top-level `discover_phase`
status in `config/bootcamp_progress.json` under `module_7_query`:

- Set `"discover_phase": "completed"` when all steps 4a–4d have been checkpointed (whether
  completed or individually skipped due to data limitations). Step 4e runs on every path, so it
  does not decide this status.
- Set `"discover_phase": "skipped"` when the bootcamper declines the Discover phase at the
  opt-in prompt or exits early at any transition point.

(The data-specific visualization suggestions that were once numbered step 4e are now tabs of the
Phase 1 step-3c visualization app (Match Keys, Feature Scores, Cross-Source, and Entity Graph's
relationship mode) and are no longer part of the Discover phase. Step 4e is now the export above.)

The full checkpoint structure in `config/bootcamp_progress.json` is:

```json
{
  "module_7_query": {
    "steps": {
      "4a": {"status": "completed", "patterns_found": {"multi_record": 5, "cross_source": 3, "relationships": 2}},
      "4b": {"status": "completed", "entity_demonstrated": 1234},
      "4c": {"status": "completed", "entity_demonstrated": 5678},
      "4d": {"status": "completed"},
      "4e": {"status": "completed", "targets": [{"system": "<as named>", "status": "exported", "format": "<format named in item 4>", "program": "src/query/<program file>", "outputs": ["data/temp/exports/<system>/<file>"], "entities": 1200, "edges": 340, "attribute_nodes": 1150}]}
    },
    "discover_phase": "completed"
  }
}
```

After updating the `discover_phase` status, return to `phase1-query-visualize.md` for the Query
Completeness Gate.

**Success:** Discover phase completed (or explicitly skipped), data patterns analyzed, why/how
analysis demonstrated, relationship networks explored, and an export offered for each system named
in Module 1 (or once, when none was named). (Data-specific visualization
suggestions are offered separately at the Phase 1 step-3c visualization gate.)
