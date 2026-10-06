# Senzing Bootcamp Plugin Feedback

Feedback captured during the Senzing Bootcamp. Every entry is saved here, whatever it turns
out to be about. Entries routed `mcp-server` may **also** have been forwarded to Senzing —
only ever with your explicit yes, and with identifying details stripped; each entry's
`Upstream:` field records what happened.

**Started:** 2026-10-05

## Your Feedback

## Improvement: Generated scenario's small name pool puts every Customer 360 run in the "Poor" possible-match band

**Date:** 2026-10-05
**Module:** Query, Visualize and Discover
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the synthetic data generator and the Module 7 step-3b bands are both plugin content
**Upstream:** not applicable

### What happened

The Data collection generator built three sources from a small name pool: 129 first names and 135 last names in WEB_ORDERS, so 76.5% of full names were unique. After loading, Senzing created 1,141 POSSIBLY_SAME relationships, every one on `+NAME` alone. 1,843 of 5,632 entities (32.7%) had a possible match, which lands in Module 7 step 3b's "Poor" band (>15%). Ground truth showed 1,013 of the 1,141 pairs are different people who share a name. Resolution itself was excellent: precision 100%, recall 97.05%, 0 merges, and no match-key suppressors.

### Why it matters

On the generated-scenario path the plugin manufactures the condition that triggers its own Poor verdict. The bootcamper is shown a "Poor" band on a clean result, and only the Poor band's outcome-2 discussion ("name-only collisions in small or synthetic datasets") explains it. That happens on every Core run that uses a generated people scenario.

### Suggested fix

Widen the generator's name pool, for example several hundred first and last names, or a surname distribution with a long tail, so that name-only collisions between different synthetic people are rare. Alternatively, have step 3b pre-classify name-only POSSIBLY_SAME links on a generated scenario before applying the band.

### Context when reported

- **Time:** 2026-10-05 12:45 local
- **Plugin version:** 0.6.0
- **Workstation:** macOS 26.6.2 (arm64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 3b
- **Recent questions:** "Would you like an interactive visualization of your resolved data — …?"
- **Bootcamper responses:** yes
- **Behind the scenes:** phase1-query-visualize.md step 3b, the Poor band's three-outcome routing; outcome 2, not mapping-actionable
- **Observed problem:** 32.7% possible-match rate, all `+NAME`, on synthetic data
- **Expected behavior:** a generated scenario should exercise matching without tripping the Poor band through its own name pool
- **Divergence:** generator name pool too small for about 5,500 synthetic people

## Improvement: Generated Customer 360 scenario promises households but generates none

**Date:** 2026-10-05
**Module:** Data collection
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — Module 1's Business Case Offer wrote the criterion, and Module 4's generator did not produce data for it
**Upstream:** not applicable

### What happened

The generated business problem listed the success criterion "See related customers, such as people in the same household." The generator never placed two different people at a shared address or phone. Across 10,000 records, the only non-name relationships were 4 POSSIBLY_RELATED links, all between records of the same person, and 0 were disclosed. Module 7's related-customers query and find_network worked, but they could only show name-only clusters.

### Why it matters

One of the three success criteria could not be demonstrated on the plugin's own scenario. The data-discoveries report had to explain that the data, not the pipeline, was the reason.

### Suggested fix

When the scenario names households or related parties, have the generator emit them. For example, give a few hundred pairs of different people a shared street address or home phone, and record them in the ground-truth file as related-not-same, so Module 7 can demonstrate POSSIBLY_RELATED links and find_path over 2+ degrees.

### Context when reported

- **Time:** 2026-10-05 12:45 local
- **Plugin version:** 0.6.0
- **Workstation:** macOS 26.6.2 (arm64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 4d
- **Recent questions:** "What would you like to do next?" (after How Analysis)
- **Bootcamper responses:** 1 — continue to Relationship Networks
- **Behind the scenes:** phase2b-discover.md step 4d hub method; no 2+ degree pair after 18 neighbour pairs across 3 hubs
- **Observed problem:** no household or 2+ degree relationships existed to show
- **Expected behavior:** the generated data supports every success criterion the generated business case states
- **Divergence:** the generator's quirk list has no shared-address or shared-phone households

## Improvement: Docker route on macOS needs a port relay for the visualization server

**Date:** 2026-10-05
**Module:** Truth Set visualization
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — the reference viz server's loopback-only bind meets the plugin's Docker route
**Upstream:** not applicable

### What happened

On the Docker route for the Python SDK on macOS, `senzing_viz_server.py` binds 127.0.0.1 inside the container. That is correct by design, since it never binds a wildcard. But Docker's published port reaches the container's network interface, not its loopback, so the app was unreachable from the Mac's browser. I added a small TCP relay inside the container (0.0.0.0:8081 to 127.0.0.1:8080) and recreated the container with `-p 127.0.0.1:8080:8081`. The same relay was needed again in Module 7.

### Why it matters

Every macOS Python bootcamper on the Docker route hits this at the first visualization. The failure looks like a broken server rather than a networking detail.

### Suggested fix

Ship the relay, or a `--bind-host` option for container use, with the Docker route. Have SDK setup publish the relay port when it creates the container, so both visualization modules work without improvisation.

### Context when reported

- **Time:** 2026-10-05 12:45 local
- **Plugin version:** 0.6.0
- **Workstation:** macOS 26.6.2 (arm64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** truthset_visualization / 2, recurring in query_visualize_discover / 3c
- **Recent questions:** visualization offers
- **Bootcamper responses:** yes
- **Behind the scenes:** visualization-api-reference.md "Binding the port"; Docker route from SDK setup
- **Observed problem:** the browser could not reach the server bound to container loopback
- **Expected behavior:** the visualization opens at http://localhost:8080 on every supported route
- **Divergence:** the loopback-only bind and Docker port publishing are incompatible without a relay

## Improvement: Fixed Docker container name collides across bootcamp projects

**Date:** 2026-10-05
**Module:** SDK setup
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — container naming is chosen by the plugin's Docker route
**Upstream:** not applicable

### What happened

Creating the SDK container as `senzing-bootcamp` failed because a container with that name already existed from a different bootcamp project on the same machine. I used a project-suffixed name instead and left the other container untouched.

### Why it matters

Anyone running a second bootcamp on the same machine hits this. The obvious fix (removing the existing container) would destroy another project's environment.

### Suggested fix

Derive the container name from the project directory by default, for example `senzing-bootcamp-<project-dir>`, and record it in `config/bootcamp_progress.json`.

### Context when reported

- **Time:** 2026-10-05 12:45 local
- **Plugin version:** 0.6.0
- **Workstation:** macOS 26.6.2 (arm64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** sdk_setup / Docker route
- **Recent questions:** EULA acceptance
- **Bootcamper responses:** yes
- **Behind the scenes:** Docker route container creation
- **Observed problem:** `docker run --name senzing-bootcamp` reported a name conflict
- **Expected behavior:** a per-project container that cannot collide
- **Divergence:** a global fixed name

## Improvement: mapping_workflow's sz_json_analyzer.py fails on Python 3.9

**Date:** 2026-10-05
**Module:** Data Quality, Mapping, and Transformation
**Priority:** Medium
**Source:** self-observed (assistant retrospective)
**Routing:** mcp-server — the script is served by the Senzing MCP server's mapping_workflow, not shipped by the plugin
**Upstream:** submitted 2026-10-05

### What happened

The `sz_json_analyzer.py` script, downloaded through `mapping_workflow` for the analyzer gate, raised a SyntaxError on import under Python 3.9, which is the macOS system `python3`. It ran cleanly under Python 3.11 inside the SDK container.

### Why it matters

macOS ships Python 3.9 as `python3`. A bootcamper running the analyzer gate on the host hits a SyntaxError in Senzing-provided code, which reads as a broken download.

### Suggested fix

Keep the analyzer compatible with Python 3.9, or state the minimum Python version in the script header and in the `mapping_workflow` step that hands it out, so the failure is a clear version message.

### Context when reported

- **Time:** 2026-10-05 12:45 local
- **Plugin version:** 0.6.0
- **Workstation:** macOS 26.6.2 (arm64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** data_quality_mapping / mapping_workflow validation
- **Recent questions:** mapping plan approval
- **Bootcamper responses:** 1
- **Behind the scenes:** phase2-data-mapping.md analyzer gate
- **Observed problem:** SyntaxError from the analyzer script under Python 3.9
- **Expected behavior:** the analyzer runs on the platform's default python3, or names its minimum version
- **Divergence:** the script uses syntax newer than Python 3.9

## Improvement: mapping_workflow's sz_routing_report.py accepts JSONL only

**Date:** 2026-10-05
**Module:** Data Quality, Mapping, and Transformation
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** mcp-server — the routing-report script is served by the Senzing MCP server
**Upstream:** submitted 2026-10-05

### What happened

The routing report from `mapping_workflow` (`sz_routing_report.py`) reads its source input as JSONL only. Two of the three sources were CSV, so they had to be converted to JSONL before the routing check could run.

### Why it matters

CSV is the most common source format a bootcamper brings. Every CSV source needs a hand-written conversion step before a required quality gate.

### Suggested fix

Accept CSV directly, with a header row as field names, or have the workflow step say JSONL is required and provide the conversion.

### Context when reported

- **Time:** 2026-10-05 12:45 local
- **Plugin version:** 0.6.0
- **Workstation:** macOS 26.6.2 (arm64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** data_quality_mapping / routing report gate
- **Recent questions:** mapping plan approval
- **Bootcamper responses:** 1
- **Behind the scenes:** phase2-data-mapping.md routing-report gate
- **Observed problem:** the routing report cannot read CSV sources
- **Expected behavior:** the routing report accepts the source in its collected format
- **Divergence:** a JSONL-only input reader

## Improvement: Match Keys tab clips the longest match-key label

**Date:** 2026-10-05
**Module:** Query, Visualize and Discover
**Priority:** Low
**Source:** self-observed (assistant retrospective)
**Routing:** plugin — layout of the bundled visualization server
**Upstream:** not applicable

### What happened

In the Match Keys tab, the longest label (`+NAME+ADDRESS+PHONE+EMAIL`) is cut off at the left edge of the chart, in both the live app and the captured screenshot.

### Why it matters

The most frequent match key is the one most likely to be long. The screenshot of it goes into the recap PDF and the graduation video.

### Suggested fix

Size the label column from the longest key, or wrap or truncate with a tooltip.

### Context when reported

- **Time:** 2026-10-05 12:45 local
- **Plugin version:** 0.6.0
- **Workstation:** macOS 26.6.2 (arm64)
- **Model / effort:** claude-opus-5-5 / high
- **Context size:** Unknown
- **Module / step:** query_visualize_discover / 3c
- **Recent questions:** visualization offer
- **Bootcamper responses:** yes
- **Behind the scenes:** senzing_viz_server.py Match Keys tab
- **Observed problem:** the label is clipped on the left
- **Expected behavior:** every label fully visible
- **Divergence:** fixed label-column width
