"""Every prescribed `search_docs` query is either verified against the server or paired
with a re-query rule.

`search_docs` is BM25, so phrasing decides what comes back — a fact
`module-00-entity-resolution-concepts/concepts.md` documents at length, together with a ⛔
re-query rule, both added because a *composed* query had already failed in a real run.

Module 1 Step 14 was written with the same instinct (name the query so the guide does not
improvise) but as a **template with a substitution slot** that was never executed for the
categories it would be substituted with, and without the safeguard. Measured on server 1.32.9,
docs index 2026-08-11, checked 2026-08-12:

- `value proposition Supply Chain` — the prescribed template with a category from the plugin's
  own recognized set — returns `senzing/libpostal`'s geodata *store-chains* scripts and a
  `sz_spark` changelog's "CI / supply chain" heading. BM25 matched "chains" and the *software*
  sense of "supply chain"; "value proposition" contributed nothing.
- `entity resolution business value` returns the real material: the *Entity Resolution Buyer's
  Guide* ("Five Primary Business Use Cases") and *Agentic Entity Resolution* ("Why Agentic
  Entity Resolution Matters", whose Business Impact list is broken out by use case).
- `entity resolution business value supply chain` — the working query **plus** the category —
  puts the libpostal script back at the top, outranking the real material (57.9 vs 57.5).

That last measurement is why the shipped fix forbids appending the category rather than
offering it as an optional refinement: the category token is the defect, not a refinement of a
working query. The category selects which part of the results to use; it does not retrieve them.

Why the failure shape matters more than the wasted call, in the plugin's own words: "a query
that misses looks exactly like documentation that does not cover the topic", which "makes a
training-data fallback feel justified on the grounds that MCP 'had no answer'" — and Step 14
sits immediately before the confirmation gate on the path to *every* Module 1 completion.

The allowlist below is not a convenience. Each entry was executed against the live server at
the date recorded, and the observed top hit is written down so a later reader can re-check the
claim rather than trust it. A query added without either verification or a re-query rule fails.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
STEP14 = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"

#: When every phrasing below was last executed against the live server.
VERIFIED_ON = "server 1.32.9, docs index 2026-08-11 20:52 UTC, checked 2026-08-12"

#: query -> the top hit observed, so the verification is re-checkable and not just asserted.
#: "Verified" means EXECUTED and its result written down — not "ideal". Where a phrasing lands
#: on adjacent rather than on-target material that is said so explicitly, because an allowlist
#: that quietly upgrades "I ran it" into "it is good" is the same laundering this guard exists
#: to stop.
VERIFIED_QUERIES = {
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-30 on server 1.37.16 (docs index 2026-09-29 22:00 UTC) for #289, Module 6
    # Phase D's per-binding flag-availability route. ⚠️ Record the PROPERTY, not ranks or scores.
    "senzing.szengineflags SzEngineFlags SZ_EXPORT_DEFAULT_FLAGS":
        "ON TARGET: the top hit is the Python SDK reference's 'szengineflags' section "
        "(garage.senzing.com/sz-sdk-python/senzing.html), the binding's alphabetical "
        "SzEngineFlags member list, in which SZ_ENTITY_INCLUDE_REPRESENTATIVE_FEATURES is "
        "followed directly by SZ_EXPORT_DEFAULT_FLAGS, so it has no SZ_EXPORT_ALL_FLAGS; the "
        "next hits are the Java SzFlags and SzFlag fields. Naming only the flag and 'python' "
        "('SZ_EXPORT_ALL_FLAGS SzEngineFlags python') put the Java SzFlag field first, which "
        "is why Phase D carries a re-query rule",
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-30 on server 1.37.16 (docs index 2026-09-29 22:00 UTC) for #287, Module 2
    # Step 3 Phase 3's routes for the Java and C# bindings. The second is also the evidence slot
    # of the C# MCP-NEGATIVE marker. Re-executed 2026-10-01 on server 1.37.16 (docs index
    # 2026-09-29 22:00 UTC) for #320, which made the C# query step 1 of the fallback after
    # `sdk_guide(..., language='csharp')`: same property. ⚠️ Record the PROPERTY, not ranks or
    # scores.
    "Java SDK sz-sdk.jar Maven Usage local Maven repository":
        "ON TARGET BELOW AN ADJACENT TOP HIT: the top hit is the FAQ 'Where is sz-sdk.jar on "
        "Maven Central?', about a cosmetic JAR-verification warning; the set carries the "
        "Senzing Java SDK 4.x Reference sections 'Installation in Local Maven Repository' "
        "(java -jar sz-sdk.jar prints the mvn install:install-file command) and 'Maven Usage' "
        "('not provided via Maven Central'; system-scoped or local-repository dependency). "
        "Phase 3 names both sections, so the reader reads past the first hit",
    "C# .NET SDK Senzing.Sdk NuGet package":
        "ON TARGET, AND SILENT ON THE SOURCE: the top hit is 'Senzing.Sdk for C#', which says "
        "'After adding the Senzing.Sdk NuGet package to your project dependencies' and does not "
        "say where the package comes from; the next is 'v4 C# SDK Reference', a link list. "
        "That silence is half the absence the C# marker records for linux_apt, linux_yum and "
        "macos_arm; the other half is their sdk_guide install replies, which have no C# line, "
        "while the windows reply names the source",
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-28 on server 1.37.14 (docs index 2026-09-28 03:23 UTC) for #194, Module 2
    # Step 1b's update path and Step 2's preview-status relay. The first two are the update
    # commands' route; the third is the point-release notes' route, and the three after it are
    # evidence slots of MCP-NEGATIVE markers. ⚠️ Record the PROPERTY, not ranks or scores.
    "homebrew-senzingsdk upgrade cask brew upgrade senzingsdk":
        "ON TARGET BELOW AN ADJACENT TOP HIT: the top hit is the V3-to-V4 FAQ 'What are the "
        "exact steps to migrate from V3 to V4?'; the set carries senzing/homebrew-senzingsdk "
        "section 'Upgrade' (brew update, brew upgrade --cask senzingsdk) and the README's "
        "'Preview Release — Unsupported' warning. Step 1b says to read past the first result",
    "scoop-senzingsdk update scoop update senzingsdk":
        "ON TARGET: the top hit is the senzing/scoop-senzingsdk README, which opens with the "
        "'Preview Release — Unsupported' warning and carries section 'Update' (scoop update "
        "senzingsdk). Used at two call sites: Step 1b's update command and Step 2's preview relay",
    "upgrading to 4.4.0 from v4.0.0 through v4.3.x no schema change required migration action required":
        "ON TARGET BELOW AN ADJACENT TOP HIT, with category='release_notes': the top hit is "
        "What's New in v4 'Migration guides', a V3-to-V4 link list; the target, v4.4.0 Detailed "
        "Release Notes 'Migration & Action Required' ('No schema change required when upgrading "
        "from any v4 version', plus license and configuration actions), ranks just below it. "
        "Step 1b says to read past the first hit. Quoted at two sites: the step and the "
        "routing negative's owner clause",
    # Executed 2026-09-28 on server 1.37.15 (docs index 2026-09-28 23:38 UTC) for #222: the
    # citation for Step 1b's migration tools, named by the V4 version doing the migration.
    "sz_dbtool upgrade sz_dbupgrade sz_configupgrade replaced 4.4.0 native command-line tools":
        "ON TARGET BELOW AN ADJACENT TOP HIT, with category='release_notes': the top hit is "
        "What's New in v4 'Migration guides', a V3-to-V4 link list; the set carries v4.4.0 "
        "Detailed Release Notes 'Command-line Tools & SDKs' with the v4.0 - v4.3 | v4.4.0 and "
        "later table (sz_dbupgrade -> sz_dbtool upgrade; sz_configupgrade -> sz_configtool, "
        "configuration upgrades folded in) and What's New in v4 'Infrastructure & tooling' with "
        "the same table. It is a citation, not a query the guide runs",
    "homebrew-senzingsdk preview release unsupported tap install cask":
        "ON TARGET: the top hit is senzing/homebrew-senzingsdk section 'homebrew-senzingsdk', "
        "the 'Preview Release — Unsupported' warning ('provided as-is with no warranty and is "
        "not supported')",
    "brew outdated brew info senzingsdk installed version check":
        "OFF TARGET BY DESIGN — the macOS check-command negative's evidence: the corpus serves "
        "the tap README's install, upgrade and uninstall sections, its changelog and the macOS "
        "quickstart for it, and no brew outdated or brew info usage",
    "scoop status scoop info senzingsdk installed version check":
        "OFF TARGET BY DESIGN — the Windows check-command negative's evidence: the corpus serves "
        "the bucket README (install, update, uninstall), its changelog and template docs for "
        "it, and no scoop status or scoop info usage",

    # ---------------------------------------------------------------------------------
    # Executed 2026-09-28 on server 1.37.14 (docs index 2026-09-28 03:23 UTC) for #158, the
    # type/name check in Module 5 Phase 1 Step 6. The first backs the "keep" option's cost;
    # the second backs the absence the suffix list's heuristic label rests on, and its
    # emptiness of a suffix list is the evidence.
    "RECORD_TYPE PERSON ORGANIZATION prevent records of different types from resolving":
        "ON TARGET. #1 is Senzing Entity Specification 'Feature: RECORD_TYPE' (74.7), whose "
        "guidance column reads 'Prevents records of different types from resolving' and "
        "'Use standardized kinds (PERSON, ORGANIZATION)'. #2 is 'What features to map' (31.6), "
        "whose RECORD_TYPE row reads 'Include when known to prevent cross-type resolution'",
    "organization name suffix tokens LLC LTD INC person or organization name classification":
        "EMPTY OF A SUFFIX LIST, WHICH IS THE POINT. #1 is an FAQ on non-person entities "
        "(89.1). #2 is Senzing Entity Specification 'Feature: NAME' (56.0), whose rules read "
        "'use NAME_ORG for organizations' and 'do not mix NAME_ORG with parsed person fields in "
        "the same object' -- the name rule the retype applies. #3-#5 are senzing/libpostal "
        "tokenize and name-normalization scripts. No hit is a list of organization suffixes",

    # ---------------------------------------------------------------------------------
    # Executed 2026-09-26 on server 1.37.13 (docs index 2026-09-24 18:45 UTC) for #160, the
    # match-key tokenizing rule in Phase D step 2 and Module 5's no-dashes domain line. The
    # same phrasing is the one the issue's refinement recorded.
    "MATCH_KEY disclosed relationship REL_POINTER role in match key":
        "ON TARGET. #1 is the Senzing MCP server article 'MATCH_KEY / WHY_KEY Direction "
        "Notation for Disclosed Relationships' (278.1), defining the (ROLE:), (:ROLE) and "
        "(ROLE:ROLE) forms; its source is local:// and it is cited by title. #2 is Senzing "
        "Entity Specification 'Feature: REL_POINTER' (259.3), whose REL_POINTER_DOMAIN row "
        "reads 'See REL_ANCHOR_DOMAIN above'. #4 is 'Feature: REL_ANCHOR' (179.5), carrying "
        "'a code (without dashes)' and 'Use a domain code without dashes to avoid confusion in "
        "downstream match key parsing.' Used at two call sites",

    # ---------------------------------------------------------------------------------
    # Executed 2026-09-02 on server 1.36.0 (twice: during the dry run that produced
    # `specs/proceed-on-sqlite-keeps-the-tier-s-thread-count.md`, and again at
    # implementation). The claim it supports is a NEGATIVE, which is why the query is
    # prescribed at all: Phase B must not characterize an engine message the corpus does
    # not document, so the step names the query whose emptiness is the evidence.
    "resolved entity is out of sync expected got concurrent loading SQLite lock":
        "EMPTY OF THE TARGET, WHICH IS THE POINT. No hit names the "
        "'Resolved entity ... is out of sync' engine message at all. #1 is 'Enabling the "
        "Per-Entity Feature Store & Advisory Locking in Senzing 4.4.0' (86.7), whose "
        "behavior-by-database table states that on SQLite the engine 'Falls back to LEASE "
        "automatically (no-op)' with no advisory locks -- adjacent and useful, but not the "
        "message. #2 is 'Scaling Out Your Database With Clustering' (76.4). So the message "
        "is uncovered by the corpus rather than missed by the phrasing, which is what makes "
        "the absence negative at phaseB-load-first-source.md safe to state (INV-194: the "
        "owner route was asked). Re-ask before re-dating; a negative is the one claim shape "
        "that cannot go stale detectably.",

    # ---------------------------------------------------------------------------------
    # Executed 2026-08-28 on server 1.33.0, during the `/feedback-to-specs` triage that
    # produced `specs/mapping-step3-rejects-disjoint-name-declarations.md`. The claim it
    # supports is the SCOPE of the NAME rule -- the step-3 validator's message asserts a
    # record-level rule, and the specification states an object-level one.
    "entity specification attribute names feature tables NAME_ORG ADDR_LINE1 PHONE_NUMBER":
        "ON TARGET. #1 is Senzing Entity Specification / 'Entities, features and attributes' "
        "(99.8). #2 is the same document's 'Name > Feature: NAME' section (83.5), which "
        "carries the load-bearing sentence -- 'do not mix NAME_ORG with parsed person fields "
        "IN THE SAME OBJECT' -- plus the matching negative example. NOTE: the excerpts render "
        "attribute names BACKTICKED (`OTHER_ID_TYPE`), while the same tables in the document "
        "`download_resource` serves render them as PLAIN TEXT; that divergence is its own "
        "finding, in `applicability-and-attribute-catalog-are-authored-by-hand-and-fail-"
        "silently`.",
    # ---------------------------------------------------------------------------------
    # Executed 2026-08-23 on server 1.33.0 (docs index 2026-08-20 17:33 UTC), for
    # `specs/search-docs-instructions-omit-the-required-query-parameter.md`: `query` is
    # `search_docs`' ONLY required parameter, so nine shipped references passing a bare
    # `category=` named a call a schema-respecting client cannot construct. Each query below
    # was chosen by executing it and reading the result, not by paraphrasing the destination.
    "community wrapper not the official SDK package registry":
        "ON TARGET and #1: Senzing Anti-Patterns: Ecosystem and Dependencies (36.2), which "
        "carries 'Do Not pip install senzing', 'Do Not Use Maven Central Senzing Artifacts' "
        "and 'Do Not Use senzing-garage Repos Without Direction' -- the official-vs-community "
        "packaging material a TypeScript community wrapper's failed from-source build needs. "
        "Then 'Installing in Sandboxed or Restricted-Egress Environments' (27.1). NOTE: an "
        "earlier attempt phrased as 'typescript node install build native bindings' ranked "
        "the PostgreSQL/container article first instead -- the corpus has no TypeScript-"
        "specific anti-pattern article, so the vocabulary that works names the PACKAGING "
        "concern, not the language",
    "NAME_FULL NAME_ORG parsed person name single field":
        "ON TARGET and #1: Senzing Entity Specification -> 'Name > Feature: NAME' (68.7), "
        "carrying both quoted strings verbatim -- NAME_FULL as 'Single-field name when type "
        "(person vs org) is unknown or only a full name is provided', and the Rules line "
        "'Prefer parsed person names ... use NAME_FULL only when the type is unknown or only "
        "a single field exists'. Used at three call sites",
    "REL_ANCHOR_KEY REL_POINTER disclosed relationship keys":
        "ON TARGET and #1: Senzing Entity Specification -> 'Disclosed relationship mapping "
        "guidance' (213.3), then 'Feature: REL_POINTER' (205.5) and 'Feature: REL_ANCHOR' "
        "(163.3). Together these carry the string-valued JSON examples (\"ORG1001\", "
        "\"ACME-1001\") AND the REL_ANCHOR_KEY guidance column's bare 1001 -- both halves of "
        "the does-not-mandate-a-type claim the mapping sites make. Used at two call sites",
    "usage type distinguishes multiple instances payload optional attributes":
        "ON TARGET and #1: Senzing Entity Specification -> 'Usage types and payload (optional "
        "attributes)' (86.6), carrying the quoted definition verbatim: 'A short label that "
        "distinguishes multiple instances of the same feature on one entity'",
    "Identifiers NATIONAL_ID PASSPORT TAX_ID TRUSTED_ID feature group":
        "ON TARGET: Senzing Entity Specification -> 'Identifiers > Feature: TAX_ID' (106.0) "
        "and 'Identifiers > Feature: NATIONAL_ID' (95.9). These are members OF the Identifiers "
        "section, which is what the call site's grouping claim rests on -- the section heading "
        "itself is not a separately indexed chunk, so the members are the evidence",
    "ACCOUNT_NUMBER ACCOUNT_DOMAIN account feature":
        "ON TARGET and #1: Senzing Entity Specification -> 'Identifiers > Feature: ACCOUNT' "
        "(98.2), carrying 'Domain/system for the account number' verbatim -- the definition "
        "the call site quotes",
    "recommended JSON schema FEATURES list multiple values sub-list":
        "ON TARGET and #1: Senzing Entity Specification -> 'Recommended JSON schema' (82.8), "
        "carrying the quoted sentence verbatim ('In prior versions we allowed a flat JSON "
        "structure with a separate sub-list for each feature that had multiple values. While "
        "we still support that, we now recommend ...') plus the Schema Validation Rules that "
        "declare FEATURES required",
    # Executed 2026-08-17 on server 1.32.9 (docs index 2026-08-11 20:52 UTC), later than
    # VERIFIED_ON above, which records the date the bulk of this allowlist was measured.
    # Re-run 2026-10-01 on server 1.37.16 (docs index 2026-09-29 22:00 UTC, #322): still
    # returns no section stating the consequence -- that a root-level key named after a
    # registered feature attribute is extracted as a feature. The prohibition itself is now
    # cited to mapping_workflow step 2, so the marker's claim was rescoped to the consequence
    # and this query string was deliberately left unchanged.
    "payload attribute versus registered feature attribute record root extracted as feature precedence":
        "ADJACENT, AND DELIBERATELY SO: Senzing Entity Specification -> 'Payload attributes "
        "(optional)' (57.9), 'Attributes for the record key' (49.8), 'Mapping identifiers' "
        "(48.1). These establish that payload and registered features are distinct "
        "categories and that choosing between them is a mapping decision -- they do NOT "
        "state the precedence when a payload-intended root key carries a registered "
        "attribute's name, which is exactly what the MCP-NEGATIVE marker at that call site "
        "claims. The query is prescribed so a reader can re-run the absence, not to "
        "retrieve an answer. NOTE: the highest-scoring result overall was an off-topic "
        "pricing document ('Data Source Records (DSRs) Explained', 105.0) despite "
        "category='data_mapping', so the category filter did not exclude it",
    # Executed 2026-08-21 on server 1.33.0 (docs index 2026-08-20 17:33 UTC), for the datastore
    # mount-crossing guidance added to module-02 Step 7.
    "loading":
        "ON TARGET for the two anti-patterns the step relays, though neither is the #1 hit: "
        "with category='anti_patterns' the ranking was 'Senzing Anti-Patterns: Configuration "
        "and Initialization' (12.6), then 'Senzing Anti-Patterns: Architecture and "
        "Performance' (12.0). The first carries 'Do Not Skip check_repository_performance() "
        "Before Production' with the SzDiagnostic signature; the second carries 'Do Not Use "
        "Low-IOPS Storage' with the avoid-network-attached-storage rule. Both are quoted at "
        "the call site. NOTE: a single-word query is BM25-fragile by nature -- it works here "
        "only because category='anti_patterns' narrows the corpus to a handful of documents, "
        "and the top hit by raw relevance was a Rust code example (35.4) that the category "
        "filter did NOT exclude. Re-check the two titles rather than the ordering",
    "entity resolution business value":
        "ON TARGET: Entity Resolution Buyer's Guide -> 'Five Primary Business Use Cases'; "
        "Agentic Entity Resolution -> 'Why Agentic Entity Resolution Matters'",
    "what features to map":
        "ON TARGET: Senzing Entity Specification -> 'What features to map' (exact section)",
    "Senzing engine configuration PostgreSQL connection":
        "ON TARGET: Senzing Engine Configuration (exact page)",
    "PostgreSQL schema DDL initialization":
        "ON TARGET: Database Setup -> 'PostgreSQL Setup: Create the database, schema, and "
        "permissions'",
    "CORD datasets: names, contents, and availability for entity resolution scenarios":
        "ON TARGET: Collections Of Relatable Data (CORDs) -> 'What Is a CORD?'",
    "temporary evaluation license for a dataset larger than the default limit":
        "ON TARGET: End User License Agreement (EULA) -> 'Senzing Non-Production License' "
        "(relevance 171, the highest in this set)",
    # Executed against server 1.32.9, docs indexed 2026-08-11 20:52 UTC, on 2026-08-14, for
    # module-04 Step 8b's load-time estimate.
    "hardware sizing capacity planning":
        "ON TARGET: Hardware Sizing FAQ -> 'Full Article' (relevance 113.4), carrying "
        "throughput per engine core (~5-10 rec/sec steady state), the three load phases "
        "(Phase 1 is 10-100x faster than Phase 3) and worked load-time examples (1,000 "
        "records ~2 min; 100,000 ~55 min). ⚠️ The phrasing is load-bearing: adding the "
        "obvious extra terms — 'hardware sizing capacity planning records per second load "
        "time' — drops the FAQ entirely and returns add_record flag docs and loading code "
        "snippets instead. Step 8b says so at the call site",
    # ⚠️ The three below are NOT queries a step tells the guide to RUN. Each is the evidence slot
    # of an `MCP-NEGATIVE` marker — a query that was executed and came back without the fact. The
    # guard cannot tell the two apart (both are `search_docs(query='…')` literals in shipped
    # markdown), and that is the right default: an unexecuted phrasing is indistinguishable from an
    # executed one, so both must be accountable. All three executed against server 1.32.9, docs
    # indexed 2026-08-11 20:52 UTC, on 2026-08-13; the first was re-executed for #151 and the
    # second for #150 (below).
    # ⚠️ Record what the corpus SERVES, not how many hits or that "all" of them are one thing:
    # "all six hits are V3-to-V4" stood here while the index grew to ten hits, two of them not
    # migration material (server 1.37.13, 2026-09-24). Nothing scans this file for that shape.
    # Re-executed for #194 on server 1.37.14, docs index 2026-09-28 03:23 UTC, 2026-09-28: the
    # marker it backs is now a ROUTING negative, and this phrasing is its missing half.
    "upgrade Senzing SDK 4.3 to 4.4 procedure":
        "OFF TARGET BY DESIGN — the routing negative's missing half: the corpus serves V3-to-V4 "
        "migration material for this phrasing, top hit the FAQ 'What are the exact steps to "
        "migrate from V3 to V4?' naming sz_dbupgrade/sz_configupgrade/sz_configtool, and no "
        "4.x-to-4.y procedure. The 4.x-to-4.y notes are reached through category='release_notes' "
        "with the 'upgrading to 4.4.0 …' phrasing above, which is what module-02 Step 1b's "
        "marker names as the owner (server 1.37.14, docs index 2026-09-28 03:23 UTC, "
        "re-executed 2026-09-28)",
    # Re-executed for #150 on server 1.37.13, docs index 2026-09-24 18:45 UTC (2026-09-24, and
    # again 2026-09-26 with the same result). The 2026-08-13 record said the query "gives no
    # figure"; the rebuilt index added an FAQ that states the figure outright, so the set now
    # answers it and only the ranking keeps it off target. That record was replaced, not
    # re-dated. ⚠️ Record the ranking property, not ranks or scores: they move on a rebuild.
    "evaluation license record limit how many records without a license":
        "OFF TARGET BY DESIGN — the negative's evidence, now a ranking one: the top-ranked hits "
        "are the EULA's grant-of-license sections ('Senzing Non-Production License' first, "
        "'solely for up to the number of DSRs designated therein'), which state no figure. The "
        "result set does carry the figure, in a lower-ranked FAQ, 'What is the 500 record limit "
        "and how do I work around SENZ9000'. sdk_guide(topic='load', record_count=<above the "
        "limit>) states it in a fixed field instead, compatibility_notes — 'the default Senzing "
        "license limit of 500' (server 1.37.13, docs index 2026-09-24 18:45 UTC, re-executed "
        "2026-09-26)",
    # Module 5's multi-language retrieval strategy (INV-212), added 2026-08-13. The first two are
    # queries the step tells the guide to RUN; the last two are the evidence slots of its two
    # `MCP-NEGATIVE` markers — quoted in order to be forbidden. All four executed against server
    # 1.32.9, docs indexed 2026-08-11 20:52 UTC, on 2026-08-13; "globalization" was re-executed
    # for #149 (below).
    "UTF-8 encoding non-Latin character support multi-language data quality":
        "ON TARGET with category='globalization': Senzing Globalization Guide -> 'What languages "
        "does Senzing support?', which states the UTF-8 and cross-script answer outright. ⚠️ Three "
        "of six hits are category='code_example' rows (libpostal encoding.py, a Rust FFI guide) "
        "carrying HIGHER relevance_score (63.6 vs 39.8) but returned AFTER the on-topic rows — the "
        "filter promotes rather than restricts, so never rank this set by score",
    "data quality practices multi-language non-Latin":
        "ON TARGET with category='globalization': Globalization Guide -> 'Address matching examples "
        "> CJK+English cross-script matching (new in v4)' (relevance 12.8), whose prose carries the "
        "practice — native-to-native beats native-to-Romanized, and for non-CJK cross-script, "
        "Romanize via an address-hygiene product and supply both forms. All three hits are the Guide",
    # Re-executed for #149 on server 1.37.13, docs index 2026-09-24 18:45 UTC, 2026-09-26, at
    # max_results=6 and at the default. The 2026-08-13 record above this entry said its best
    # Guide hit was a bare title with no prose; the rebuilt index returns Guide sections with
    # prose, so that record was replaced rather than re-dated. ⚠️ Record the PROPERTY, not the
    # ranks: a rank order is what went stale here, and the next rebuild can move it again.
    "globalization":
        "OFF TARGET BY DESIGN — the negative's evidence, and the anti-pattern Module 5 quotes: "
        "the corpus serves Senzing Globalization Guide sections with real prose for it, and the "
        "bare term also admits unrelated Global* substring matches — the Rust SDK's static "
        "GLOBAL_ENVIRONMENT, postgresql-performance-v4's 'Global — more workers' autovacuum "
        "tuning and an MDM-Lite FAQ on 'globally unique ID'. It did not return the 'What "
        "languages does Senzing support?' section, which the category='globalization' query "
        "above ranks first (server 1.37.13, docs index 2026-09-24 18:45 UTC, re-executed "
        "2026-09-26)",
    "multi-language data quality best practices":
        "OFF TARGET BY DESIGN — the negative's evidence: FIVE OF FIVE hits are repo "
        "docs/best-practices.md template files (senzingsdk-tools, scoop-senzingsdk, "
        "homebrew-senzingsdk, senzingapi-tools, senzingsdk-runtime), all about Markdown lint and "
        "Dockerfiles, scores 89.5-89.8, two of them title-only stubs. No globalization content at "
        "all — the phrase 'best practices' is the whole defect",
    "szBuildVersion.json build version file location":
        "OFF TARGET BY DESIGN — this is the negative's evidence: no indexed document gives the "
        "file's path on any platform. It serves SDK version-call examples for it, top hit "
        "senzing/code-snippets-v4 -> python/information/get_version.py, and build/packaging "
        "documents. The corpus serves SzProduct.get_version(), not a file location, which is why "
        "Step 1 routes the reader to the SDK call and marks the file paths as environment "
        "observations (server 1.37.13, docs index 2026-09-24 18:45 UTC, re-executed 2026-09-26)",
    # Executed for #169 on server 1.37.13, docs index 2026-09-24 18:45 UTC, 2026-09-26, at
    # max_results=5. The visualization contract's /api/how entry quotes it in its MCP-NEGATIVE
    # marker as the corpus route asked for a meaning of the flag. Re-executed for #154 on the
    # same server and index, 2026-09-27, with the same result: Phase D's How-state audit quotes
    # it in its own MCP-NEGATIVE marker.
    "NEED_REEVALUATION how entity final state":
        "OFF TARGET BY DESIGN — the negative's evidence: the top hit is the "
        "how_entity_by_entity_id Flags page's SZ_HOW_ENTITY_DEFAULT_FLAGS section, whose example "
        "payload shows \"NEED_REEVALUATION\": 0; the others are that page's intro, its "
        "SZ_INCLUDE_MATCH_KEY_DETAILS example, an Entity ID FAQ and an unrelated libpostal file. "
        "No hit defines the field or says what sets or clears it",
    # Executed for #154 on server 1.37.13, docs index 2026-09-24 18:45 UTC, 2026-09-27, at the
    # default max_results. The second corpus query in Phase D's How-state audit MCP-NEGATIVE
    # marker: asked whether any document ties a re-evaluation call to the flag.
    # ⚠️ Record the PROPERTY, not ranks or scores: they move on a rebuild.
    "reevaluate entity when to call reevaluation needed":
        "ADJACENT, NOT ON TARGET — the negative's evidence: re-evaluation code snippets (Rust, "
        "Python), the SzFlag/SzFlags reevaluate-entity flag constants, a TypeScript "
        "'reevaluate an entity after rule changes' example, and the engine-config FAQ 'After "
        "config changes, reevaluate splits entities but redo merges them back. Is this a bug?', "
        "which is about config changes. No hit names NEED_REEVALUATION or ties a re-evaluation "
        "call to it",
    # "entity resolution quality evaluation" was listed here as OFF TARGET on 2026-08-12 and is
    # gone: Module 7 Step 3b no longer prescribes it. It returned the Buyer's Guide's
    # vendor-selection steps rather than precision/recall material, and
    # step3b-quality-lookup-misroutes-and-omits-the-evidence-requirement replaced it with
    # reporting_guide(topic='evaluation'), the tool that owns the material. Left as a comment
    # rather than deleted, so the phrasing is not helpfully reintroduced.
}

#: Vocabulary that shows a step handles a miss instead of assuming a hit.
REQUERY_RULE = re.compile(
    r"(?i)re-?quer(?:y|ies|ying)|nothing relevant|off-topic|empty or off-topic"
)

QUERY_LITERAL = re.compile(r"search_docs\(query='([^']*)'")
HEADING = re.compile(r"(?m)^#{2,4} ")


def shipped_markdown():
    return sorted(SKILLS.rglob("*.md"))


def sections(text):
    """(start, end) spans between Markdown headings, so 'the same step' is well-defined."""
    bounds = [m.start() for m in HEADING.finditer(text)] + [len(text)]
    if not bounds or bounds[0] != 0:
        bounds = [0] + bounds
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


def prescribed_queries():
    """(path, query, enclosing section text) for every prescribed query literal."""
    found = []
    for path in shipped_markdown():
        text = path.read_text(encoding="utf-8")
        spans = sections(text)
        for match in QUERY_LITERAL.finditer(text):
            section = next(
                (text[a:b] for a, b in spans if a <= match.start() < b), text
            )
            # Whitespace-collapsed: a literal wrapped across source lines is still one
            # query. A line-based scan misses these entirely — three of the eight
            # prescribed queries in this corpus are wrapped, and all three were invisible
            # to the first version of this guard.
            query = re.sub(r"\s+", " ", match.group(1)).strip()
            found.append((path.relative_to(REPO_ROOT), query, section))
    return found


class EveryPrescribedQueryIsAccountedFor(unittest.TestCase):
    def test_the_scan_finds_the_queries(self):
        found = prescribed_queries()
        self.assertGreaterEqual(len(found), 5, "the query scan came up empty or too small")

    def test_each_query_is_verified_or_carries_a_requery_rule(self):
        unaccounted = []
        for path, query, section in prescribed_queries():
            if query in VERIFIED_QUERIES:
                continue
            if REQUERY_RULE.search(section):
                continue
            unaccounted.append(f"{path}: search_docs(query='{query}')")
        self.assertEqual(
            [],
            unaccounted,
            "A shipped step prescribes a search_docs query that was never verified against "
            "the server and has no re-query rule in its section. search_docs is BM25, so an "
            "unexecuted phrasing can return anything — and a miss looks exactly like "
            "documentation that does not cover the topic. Verify it and add it to "
            "VERIFIED_QUERIES with its observed top hit, or pair it with a re-query "
            "instruction:\n  " + "\n  ".join(unaccounted),
        )

    def test_the_allowlist_has_no_dead_entries(self):
        """An allowlist that outlives its queries starts exempting things by accident."""
        live = {query for _p, query, _s in prescribed_queries()}
        dead = sorted(set(VERIFIED_QUERIES) - live)
        self.assertEqual(
            [], dead,
            "VERIFIED_QUERIES lists phrasings no shipped file prescribes any more — remove "
            "them so the allowlist keeps meaning what it says: %s" % dead,
        )

    def test_every_allowlist_entry_records_what_it_returned(self):
        for query, top_hit in VERIFIED_QUERIES.items():
            with self.subTest(query=query):
                self.assertTrue(
                    top_hit and len(top_hit) > 15,
                    "a verification with no recorded result cannot be re-checked",
                )


class StepFourteenHandlesAMiss(unittest.TestCase):
    def flat(self):
        text = STEP14.read_text(encoding="utf-8")
        text = re.sub(r"(?m)^\s*>\s?", "", text)
        return re.sub(r"\s+", " ", text)

    def test_the_broken_template_is_gone(self):
        self.assertNotIn("value proposition <use_case_category>", self.flat())

    def test_it_prescribes_the_verified_query(self):
        self.assertIn("search_docs(query='entity resolution business value')", self.flat())

    def test_it_carries_the_verification_stamp(self):
        flat = self.flat()
        self.assertIn("1.32.9", flat)
        self.assertIn("2026-08-12", flat)

    def test_it_forbids_appending_the_category(self):
        """The measured cause: the category token, not the abstract phrasing."""
        flat = self.flat()
        self.assertRegex(flat, r"(?i)Do not append the use-case category to the query")
        self.assertRegex(flat, r"(?i)libpostal")

    def test_it_carries_the_requery_rule_and_defers_for_the_reasoning(self):
        flat = self.flat()
        self.assertRegex(flat, REQUERY_RULE)
        self.assertRegex(flat, r"(?i)concepts\.md")
        self.assertRegex(flat, r"(?i)[Dd]o not restate that reasoning here")

    def test_it_gives_an_honest_fallback(self):
        flat = self.flat()
        self.assertRegex(flat, r"(?i)say less — do not invent value")
        self.assertIn("INV-080", flat)


if __name__ == "__main__":
    unittest.main()
