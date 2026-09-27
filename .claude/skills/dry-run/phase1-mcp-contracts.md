# Phase 1 — MCP call contracts

Verify every MCP call the plugin documents against the **live** Senzing MCP server's
schemas. Highest yield per minute of the three phases, because the MCP server is the
plugin's hard dependency and its entire factual foundation: INV-080 routes every
Senzing fact through it, so a wrong tool name, a missing required parameter, or an
invented enum value breaks a module rather than degrading it.

## Procedure

1. **Load the schemas, don't read the plugin's prose about them.**
   `ToolSearch("select:mcp__senzing__get_capabilities,mcp__senzing__get_sdk_reference,…")`.
   The schema is the contract; the plugin's description of the schema is the thing
   under test.

2. **Call `get_capabilities` first** — the plugin's own session-start rule, and it
   returns the full tool manifest, the suggested workflows, and (valuably) a
   `common_confabulations` list of mistakes the server expects an LLM to make.

3. **Enumerate every MCP call the plugin makes**, then check each against its schema:

   ```bash
   grep -rhno "mcp__senzing__[a-z_]*\|\b\(mapping_workflow\|sdk_guide\|reporting_guide\|search_docs\|get_sdk_reference\|generate_scaffold\|find_examples\|get_sample_data\|explain_error_code\|analyze_record\|download_resource\|submit_feedback\|get_capabilities\)(" plugins/senzing-bootcamp/skills/
   grep -rhno "action='[a-z_]*'\|topic='[a-z_]*'\|category='[a-z_]*'" plugins/senzing-bootcamp/skills/ | sort -u
   ```

   For each: does the tool exist? Is every **required** parameter named somewhere in
   the calling file? Is every `action=` / `topic=` / `category=` value in the schema's
   **enum**?

4. **Probe empirically where the plugin makes a claim about the server.** Reading the
   schema catches missing parameters; only a call catches a wrong claim. The
   originating run disproved INV-132 with one call —
   `get_sdk_reference(topic='methods', filter='find_network_by_entity_id')` returned
   the exact signature the invariant said was unobtainable.

5. **Re-ask every dated negative — this is the worklist the offline suite cannot build.**

   ```bash
   python3 .claude/skills/dry-run/coverage_reports.py negatives
   ```

   Each row is a claim that some tool does **not** contain something, with the server
   version and date it was last checked, oldest first. Call that tool and see whether the
   claim still holds. A negative is the one shape that cannot go stale detectably: INV-108
   keeps the suite offline, so nothing notices when the server gains the coverage the
   plugin routed around — which has happened twice
   (`senz7221-now-names-its-own-remedy`, `explain-error-code-now-owns-senz7426`).

   ⛔ **A re-ask has THREE outcomes, not two.** A marker has two halves that age at
   different rates: the **claim** ("tool X does not contain Y") and the **rationale** — the
   `owner:` clause plus the detail saying why the claim is the answer rather than a miss.
   Re-asking only exercises the claim, so:

   - **Claim false** → correct the prose and invert or rescope the guard (below).
   - **Claim true, rationale reproduces** → restamp the server version and date.
   - **Claim true, rationale does NOT reproduce** → ⛔ **correct the rationale in the same
     edit as the restamp**, and say in the report which rationales were rewritten. A
     restamp that carries the rationale forward unchecked certifies text nobody read: the
     date says "checked 2026-09-01" about the **whole comment**, not about its first
     sentence.

   The rationale is what a later reader uses to decide whether the routing conclusion still
   stands, so a stale one is not cosmetic. On 2026-08-31 all 25 DUE claims still held and
   **three rationales did not reproduce** — one of them the entire evidence for calling an
   absence a *rename* rather than a *gap*, which is the distinction the plugin acts on
   (`specs/mcp-negative-markers-carry-rationale-nothing-reverifies.md`).

   ⚠️ **Prefer a discriminating property over a census.** Two of those three drifted because
   they pinned a **count** ("all four hits are…") or an **exhaustive field list** ("carries
   applies_to, composite_members, …") — the shapes that cannot survive an index rebuild or a
   schema addition. Where the negative does not depend on the enumeration, write what
   distinguishes it ("no field names a binding type") instead of what it happened to contain.
   A positive universal over the results ("every hit is V3-to-V4 material") is a census too:
   on 2026-09-24 one such rationale was falsified by two new hits while its claim held (#151).
   Say what the corpus serves ("V3-to-V4 migration material and no 4.x-to-4.y procedure").

   ⛔ **When a negative no longer holds, the prose is only half the fix.** The second
   instance had the stale claim written into the **guards** as well: two assertions
   *required* the retired wording, so correcting the text failed the suite and the failure
   messages told the fixer the opposite of what the server said. Check for a test pinning
   the claim, and **invert or rescope it rather than deleting it** — the guard's underlying
   rule is usually still right, only its premise expired. Start the oldest row first.

6. **Cross-check the server's `common_confabulations`** against the plugin. It names
   `add_data_source` (a CLI command, not an SDK method), wrong env var names, and
   wrong method signatures. Grep for each.

## The defect patterns this phase finds

Ordered by what they cost. Each was a real finding.

| Pattern | Why it survives an audit | How to spot it |
|---|---|---|
| A **required parameter** never mentioned | the prose reads complete; nothing in the plugin references the schema | diff required params against every calling file |
| A **payload field name written as an action** | it looks like a call and reads plausibly | check every literal against the enum |
| A **topic the plugin routes around** | the plugin's table looks authoritative | list the schema's topics, subtract the ones the plugin names |
| A **PII-requiring call with no consent gate** | consent lives in a different file for a different category | for each call, ask what leaves the machine |
| A **figure hardcoded** that the server says to look up | the number is plausible and was once right | grep for digits near capacity/limit/version claims |
| An **invariant asserting a server limitation** | tests pin the invariant, so the false premise is load-bearing | probe the claim directly |

## Watch for the mis-triage trap

When the plugin has filed an upstream bug, check whether the plugin's own call was
valid. The originating run found INV-125's "step-3 validation rejects the payload
with no actionable reason" sitting on the exact line that called
`action='schema_mappings'` — an invalid action. A rejection caused by our own
malformed call, triaged as an MCP-server defect and filed upstream, produces a
fallback path that papers over a plugin bug.

Also read the tool's own notes on client behavior. `mapping_workflow` documents that
a client read cap below 64 KB "silently TRUNCATES step guidance mid-text and **reads
as a server bug**" — a documented cause the plugin had never mentioned while filing
truncation upstream.

## Do not

⛔ Call `submit_feedback`. Verify its schema; never invoke it. Under `bug` it files
noise upstream; under `license_request` it transmits a real name and work email.

⛔ Treat a large response as a cheap probe. `search_docs(query="health check")` — the
liveness probe `onboarding-flow.md` calls "lightweight" — returns a ~5 KB FAQ
article. Prefer `get_capabilities`, which the guide already calls.
