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

**Each entry is a record the test reads (#383, INV-291 as narrowed for inline routes).** It
carries the property text naming the section returned, a **rank band** from a closed set, and
its own stamp: server version, docs index date and UTC time, and measurement date. The stamps
used to sit in `#` comments, or fall back to a module-level `VERIFIED_ON`, and no test read
them. An inline route records a band, never an exact rank: ranks move on a rebuild (#149, #150,
#289), and the band still checks INV-291's "a target below rank 3 is not a route":

- `ON TARGET` — the target section is rank 1.
- `ON TARGET BELOW AN ADJACENT TOP HIT` — the target is rank 2 or 3, and every site says to read
  past the first hit.
- `OFF TARGET BY DESIGN`, `EMPTY OF …` — negative evidence: an `MCP-NEGATIVE` evidence slot, or a
  query quoted to be forbidden, whose miss or emptiness is the point.

An entry with a positive band also names, in `sections`, the sections a site must name, and
every shipped site of that query names at least one of them. The pinned lists (`concepts.md`'s
query table and Module 1 Step 3's gallery) keep exact ranks under their own guards
(`test_module_0_suggested_queries_are_measured.py`, `test_pattern_gallery_shortfall.py`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
STEP14 = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"

#: The closed set of rank bands (INV-291, #383). `EMPTY OF <what>` is open in its object only.
POSITIVE_BANDS = ("ON TARGET", "ON TARGET BELOW AN ADJACENT TOP HIT")
NEGATIVE_BANDS = ("OFF TARGET BY DESIGN",)
EMPTY_OF_BAND = re.compile(r"^EMPTY OF [A-Z][A-Z0-9_ '-]*[A-Z0-9]$")
BELOW_TOP_HIT = "ON TARGET BELOW AN ADJACENT TOP HIT"

#: The fields every record carries. `sections` is required (non-empty) for a positive band.
RECORD_FIELDS = ("band", "sections", "returned", "server", "docs_index", "measured")
SERVER_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
DOCS_INDEX_FORMAT = "%Y-%m-%d %H:%M UTC"

# History: the module-level `VERIFIED_ON` fallback read "server 1.32.9, docs index 2026-08-11
# 20:52 UTC, checked 2026-08-12", the date the bulk of the original allowlist was measured
# (fdbc922, #1). #383 copied it into each entry it covered and removed the fallback.
#
# The measurement #383 made, for every entry whose record lacked a docs index time, a band from
# the closed set, or the section returned: server 1.37.19, docs index 2026-10-02 18:46 UTC,
# 2026-10-02, at the default max_results.
#
# The measurement #417 made, for the 15 entries still stamped before the 2026-09-24 index
# rebuild: server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-04, all on that one index, at
# the default max_results, with the category each entry's sites pass. No route was broken; each
# record was re-dated or rewritten to what came back. Two site stamps were left alone because they
# vouch for a second claim that no longer holds (the hardware-sizing and Identifiers records say
# which); the ledger entry for #417 drafts their follow-ups.

#: query -> a record of what the query returned, so the verification is re-checkable and not
#: just asserted. "Verified" means EXECUTED and its result written down — not "ideal". Where a
#: phrasing lands on adjacent rather than on-target material that is said so explicitly, because
#: an allowlist that quietly upgrades "I ran it" into "it is good" is the same laundering this
#: guard exists to stop.
VERIFIED_QUERIES = {
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-30 on server 1.37.16 (docs index 2026-09-29 22:00 UTC) for #289, Module 6
    # Phase D's per-binding flag-availability route. ⚠️ Record the PROPERTY, not ranks or scores.
    "senzing.szengineflags SzEngineFlags SZ_EXPORT_DEFAULT_FLAGS": {
        "band": "ON TARGET",
        "sections": ("szengineflags", "SzEngineFlags"),
        "returned":
            "ON TARGET: the top hit is the Python SDK reference's 'szengineflags' section "
            "(garage.senzing.com/sz-sdk-python/senzing.html), the binding's alphabetical "
            "SzEngineFlags member list, in which SZ_ENTITY_INCLUDE_REPRESENTATIVE_FEATURES is "
            "followed directly by SZ_EXPORT_DEFAULT_FLAGS, so it has no SZ_EXPORT_ALL_FLAGS; the "
            "next hits are the Java SzFlags and SzFlag fields. Naming only the flag and 'python' "
            "('SZ_EXPORT_ALL_FLAGS SzEngineFlags python') put the Java SzFlag field first, which "
            "is why Phase D carries a re-query rule",
        "server": "1.37.16", "docs_index": "2026-09-29 22:00 UTC", "measured": "2026-09-30",
    },
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-30 on server 1.37.16 (docs index 2026-09-29 22:00 UTC) for #287, Module 2
    # Step 3 Phase 3's routes for the Java and C# bindings. The second is also the evidence slot
    # of the C# MCP-NEGATIVE marker. Re-executed 2026-10-01 on server 1.37.16 (docs index
    # 2026-09-29 22:00 UTC) for #320, which made the C# query step 1 of the fallback after
    # `sdk_guide(..., language='csharp')`: same property. ⚠️ Record the PROPERTY, not ranks or
    # scores.
    "Java SDK sz-sdk.jar Maven Usage local Maven repository": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Maven Usage", "Installation in Local Maven Repository"),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT: the top hit is the FAQ 'Where is sz-sdk.jar on "
            "Maven Central?', about a cosmetic JAR-verification warning; the set carries the "
            "Senzing Java SDK 4.x Reference sections 'Installation in Local Maven Repository' "
            "(java -jar sz-sdk.jar prints the mvn install:install-file command) and 'Maven Usage' "
            "('not provided via Maven Central'; system-scoped or local-repository dependency). "
            "Phase 3 names both sections, so the reader reads past the first hit",
        "server": "1.37.16", "docs_index": "2026-09-29 22:00 UTC", "measured": "2026-09-30",
    },
    "C# .NET SDK Senzing.Sdk NuGet package": {
        "band": "ON TARGET",
        "sections": ("Senzing.Sdk for C#",),
        "returned":
            "ON TARGET, AND SILENT ON THE SOURCE: the top hit is 'Senzing.Sdk for C#', which says "
            "'After adding the Senzing.Sdk NuGet package to your project dependencies' and does not "
            "say where the package comes from; the next is 'v4 C# SDK Reference', a link list. "
            "That silence is half the absence the C# marker records for linux_apt, linux_yum and "
            "macos_arm; the other half is their sdk_guide install replies, which have no C# line, "
            "while the windows reply names the source",
        "server": "1.37.16", "docs_index": "2026-09-29 22:00 UTC", "measured": "2026-10-01",
    },
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-28 on server 1.37.14 (docs index 2026-09-28 03:23 UTC) for #194, Module 2
    # Step 1b's update path and Step 2's preview-status relay. The first two are the update
    # commands' route; the third is the point-release notes' route, and the three after it are
    # evidence slots of MCP-NEGATIVE markers. ⚠️ Record the PROPERTY, not ranks or scores.
    "homebrew-senzingsdk upgrade cask brew upgrade senzingsdk": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Upgrade",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT: the top hit is the V3-to-V4 FAQ 'What are the "
            "exact steps to migrate from V3 to V4?'; the set carries senzing/homebrew-senzingsdk "
            "section 'Upgrade' (brew update, brew upgrade --cask senzingsdk) and the README's "
            "'Preview Release — Unsupported' warning. Step 1b says to read past the first result",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    "scoop-senzingsdk update scoop update senzingsdk": {
        "band": "ON TARGET",
        "sections": ("Update", "Preview Release — Unsupported"),
        "returned":
            "ON TARGET: the top hit is the senzing/scoop-senzingsdk README, which opens with the "
            "'Preview Release — Unsupported' warning and carries section 'Update' (scoop update "
            "senzingsdk). Used at two call sites: Step 1b's update command and Step 2's preview relay",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    "upgrading to 4.4.0 from v4.0.0 through v4.3.x no schema change required migration action required": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Migration & Action Required",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT, with category='release_notes': the top hit is "
            "What's New in v4 'Migration guides', a V3-to-V4 link list; the target, v4.4.0 Detailed "
            "Release Notes 'Migration & Action Required' ('No schema change required when upgrading "
            "from any v4 version', plus license and configuration actions), ranks just below it. "
            "Step 1b says to read past the first hit. Quoted at two sites: the step and the "
            "routing negative's owner clause",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    # Executed 2026-09-28 on server 1.37.15 (docs index 2026-09-28 23:38 UTC) for #222: the
    # citation for Step 1b's migration tools, named by the V4 version doing the migration.
    "sz_dbtool upgrade sz_dbupgrade sz_configupgrade replaced 4.4.0 native command-line tools": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Command-line Tools & SDKs",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT, with category='release_notes': the top hit is "
            "What's New in v4 'Migration guides', a V3-to-V4 link list; the set carries v4.4.0 "
            "Detailed Release Notes 'Command-line Tools & SDKs' with the v4.0 - v4.3 | v4.4.0 and "
            "later table (sz_dbupgrade -> sz_dbtool upgrade; sz_configupgrade -> sz_configtool, "
            "configuration upgrades folded in) and What's New in v4 'Infrastructure & tooling' with "
            "the same table. It is a citation, not a query the guide runs",
        "server": "1.37.15", "docs_index": "2026-09-28 23:38 UTC", "measured": "2026-09-28",
    },
    "homebrew-senzingsdk preview release unsupported tap install cask": {
        "band": "ON TARGET",
        "sections": ("Preview Release — Unsupported",),
        "returned":
            "ON TARGET: the top hit is senzing/homebrew-senzingsdk section 'homebrew-senzingsdk', "
            "the 'Preview Release — Unsupported' warning ('provided as-is with no warranty and is "
            "not supported')",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    "brew outdated brew info senzingsdk installed version check": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the macOS check-command negative's evidence: the corpus serves "
            "the tap README's install, upgrade and uninstall sections, its changelog and the macOS "
            "quickstart for it, and no brew outdated or brew info usage",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    "scoop status scoop info senzingsdk installed version check": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the Windows check-command negative's evidence: the corpus serves "
            "the bucket README (install, update, uninstall), its changelog and template docs for "
            "it, and no scoop status or scoop info usage",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },

    # ---------------------------------------------------------------------------------
    # Executed 2026-09-28 on server 1.37.14 (docs index 2026-09-28 03:23 UTC) for #158, the
    # type/name check in Module 5 Phase 1 Step 6. The first backs the "keep" option's cost;
    # the second backs the absence the suffix list's heuristic label rests on, and its
    # emptiness of a suffix list is the evidence.
    "RECORD_TYPE PERSON ORGANIZATION prevent records of different types from resolving": {
        "band": "ON TARGET",
        "sections": ("Feature: RECORD_TYPE",),
        "returned":
            "ON TARGET. #1 is Senzing Entity Specification 'Feature: RECORD_TYPE' (74.7), whose "
            "guidance column reads 'Prevents records of different types from resolving' and "
            "'Use standardized kinds (PERSON, ORGANIZATION)'. #2 is 'What features to map' (31.6), "
            "whose RECORD_TYPE row reads 'Include when known to prevent cross-type resolution'",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    "organization name suffix tokens LLC LTD INC person or organization name classification": {
        "band": "EMPTY OF A SUFFIX LIST",
        "sections": (),
        "returned":
            "EMPTY OF A SUFFIX LIST, WHICH IS THE POINT. #1 is an FAQ on non-person entities "
            "(89.1). #2 is Senzing Entity Specification 'Feature: NAME' (56.0), whose rules read "
            "'use NAME_ORG for organizations' and 'do not mix NAME_ORG with parsed person fields in "
            "the same object' -- the name rule the retype applies. #3-#5 are senzing/libpostal "
            "tokenize and name-normalization scripts. No hit is a list of organization suffixes",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },

    # ---------------------------------------------------------------------------------
    # Executed 2026-09-26 on server 1.37.13 (docs index 2026-09-24 18:45 UTC) for #160, the
    # match-key tokenizing rule in Phase D step 2 and Module 5's no-dashes domain line. The
    # same phrasing is the one the issue's refinement recorded.
    "MATCH_KEY disclosed relationship REL_POINTER role in match key": {
        "band": "ON TARGET",
        "sections": ("MATCH_KEY / WHY_KEY Direction Notation for Disclosed Relationships",
                     "Feature: REL_POINTER", "Feature: REL_ANCHOR"),
        "returned":
            "ON TARGET. #1 is the Senzing MCP server article 'MATCH_KEY / WHY_KEY Direction "
            "Notation for Disclosed Relationships' (278.1), defining the (ROLE:), (:ROLE) and "
            "(ROLE:ROLE) forms; its source is local:// and it is cited by title. #2 is Senzing "
            "Entity Specification 'Feature: REL_POINTER' (259.3), whose REL_POINTER_DOMAIN row "
            "reads 'See REL_ANCHOR_DOMAIN above'. #4 is 'Feature: REL_ANCHOR' (179.5), carrying "
            "'a code (without dashes)' and 'Use a domain code without dashes to avoid confusion in "
            "downstream match key parsing.' Used at two call sites",
        "server": "1.37.13", "docs_index": "2026-09-24 18:45 UTC", "measured": "2026-09-26",
    },

    # ---------------------------------------------------------------------------------
    # Executed 2026-09-02 on server 1.36.0 (twice: during the dry run that produced
    # `specs/proceed-on-sqlite-keeps-the-tier-s-thread-count.md`, and again at
    # implementation). The claim it supports is a NEGATIVE, which is why the query is
    # prescribed at all: Phase B must not characterize an engine message the corpus does
    # not document, so the step names the query whose emptiness is the evidence.
    # Re-executed for #383 on server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02 (the
    # 2026-09-02 record had no docs index): still no hit names the message. The record below
    # replaces the 2026-09-02 one, which ranked the advisory-locking article #1 (86.7) and
    # 'Scaling Out Your Database With Clustering' #2 (76.4).
    "resolved entity is out of sync expected got concurrent loading SQLite lock": {
        "band": "EMPTY OF THE TARGET",
        "sections": (),
        "returned":
            "EMPTY OF THE TARGET, WHICH IS THE POINT. No hit names the "
            "'Resolved entity ... is out of sync' engine message at all. The set is database "
            "material: 'Tuning Your Database' (DB2), 'Database Setup', and 'Enabling the "
            "Per-Entity Feature Store & Advisory Locking in Senzing 4.4.0' section 'Behavior by "
            "database with ENTITY_LOCK_MODE = ADVISORY', whose table states that on SQLite the "
            "engine 'Falls back to LEASE automatically (no-op)' -- adjacent and useful, but not "
            "the message -- then 'Scaling Out Your Database With Clustering'. So the message "
            "is uncovered by the corpus rather than missed by the phrasing, which is what makes "
            "the absence negative at phaseB-load-first-source.md safe to state (INV-194: the "
            "owner route was asked). Re-ask before re-dating; a negative is the one claim shape "
            "that cannot go stale detectably.",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },

    # ---------------------------------------------------------------------------------
    # Executed 2026-08-28 on server 1.33.0, during the `/feedback-to-specs` triage that
    # produced `specs/mapping-step3-rejects-disjoint-name-declarations.md`. The claim it
    # supports is the SCOPE of the NAME rule -- the step-3 validator's message asserts a
    # record-level rule, and the specification states an object-level one.
    # Re-executed for #383 on server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02 (the
    # 2026-08-28 record had no docs index), with category='data_mapping' as both sites pass it:
    # the same two sections in the same order. The 2026-08-28 record called it ON TARGET; the
    # load-bearing section is the second hit, so its band is the read-past one.
    "entity specification attribute names feature tables NAME_ORG ADDR_LINE1 PHONE_NUMBER": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Name > Feature: NAME", "Feature: NAME",
                     "Entities, features and attributes"),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT. The top hit is Senzing Entity Specification "
            "'Entities, features and attributes', the definitions of entity, feature and "
            "attribute. The second is the same document's 'Name > Feature: NAME' section, which "
            "carries the load-bearing sentence -- 'do not mix NAME_ORG with parsed person fields "
            "IN THE SAME OBJECT' -- plus the matching negative example, and its attribute table. "
            "NOTE: the excerpts render attribute names BACKTICKED (`NAME_ORG`), while the same "
            "tables in the document `download_resource` serves render them as PLAIN TEXT; that "
            "divergence is its own finding, in `applicability-and-attribute-catalog-are-authored-"
            "by-hand-and-fail-silently`.",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    # ---------------------------------------------------------------------------------
    # Executed 2026-08-23 on server 1.33.0 (docs index 2026-08-20 17:33 UTC), for
    # `specs/search-docs-instructions-omit-the-required-query-parameter.md`: `query` is
    # `search_docs`' ONLY required parameter, so nine shipped references passing a bare
    # `category=` named a call a schema-respecting client cannot construct. Each query below
    # was chosen by executing it and reading the result, not by paraphrasing the destination.
# Re-executed for #417 (stamp above VERIFIED_QUERIES): every one still returns its recorded
# section at rank 1, except that the REL_ANCHOR_KEY query's first two sections swapped places.
    "community wrapper not the official SDK package registry": {
        "band": "ON TARGET",
        "sections": ("Senzing Anti-Patterns: Ecosystem and Dependencies",),
        "returned":
            "ON TARGET and #1, with category='anti_patterns': Senzing Anti-Patterns: Ecosystem "
            "and Dependencies, which carries 'Do Not pip install senzing', 'Do Not Use Maven "
            "Central Senzing Artifacts' and 'Do Not Use senzing-garage Repos Without Direction' "
            "-- the official-vs-community packaging material a TypeScript community wrapper's "
            "failed from-source build needs. Then 'Installing in Sandboxed or Restricted-Egress "
            "Environments', 'Database Initialization and Container Setup' and 'Operations and "
            "Runtime' (four results). NOTE (2026-08-23): an earlier attempt phrased as "
            "'typescript node install build native bindings' ranked the PostgreSQL/container "
            "article first instead -- the corpus has no TypeScript-specific anti-pattern article, "
            "so the vocabulary that works names the PACKAGING concern, not the language",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "NAME_FULL NAME_ORG parsed person name single field": {
        "band": "ON TARGET",
        "sections": ("Name > Feature: NAME", "Feature: NAME"),
        "returned":
            "ON TARGET and #1: Senzing Entity Specification -> 'Name > Feature: NAME', carrying "
            "both quoted strings verbatim -- NAME_FULL as 'Single-field name when type (person vs "
            "org) is unknown or only a full name is provided', and the Rules line 'Prefer parsed "
            "person names ... use NAME_FULL only when the type is unknown or only a single field "
            "exists'. Then 'Entities, features and attributes' and 'Identifiers > Feature: "
            "LEI_NUMBER'. Used at three call sites",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "REL_ANCHOR_KEY REL_POINTER disclosed relationship keys": {
        "band": "ON TARGET",
        "sections": ("Disclosed relationship mapping guidance", "Feature: REL_POINTER",
                     "Feature: REL_ANCHOR"),
        "returned":
            "ON TARGET: Senzing Entity Specification -> 'Feature: REL_POINTER' first, then "
            "'Disclosed relationship mapping guidance' and 'Feature: REL_ANCHOR', still the top "
            "three (the 2026-08-23 record had the guidance section first). Together these carry "
            "the string-valued JSON examples (\"ORG1001\", \"ACME-1001\") AND the REL_ANCHOR_KEY "
            "row's bare example value 1001 -- both halves of the does-not-mandate-a-type claim "
            "the mapping sites make. Used at two call sites",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "usage type distinguishes multiple instances payload optional attributes": {
        "band": "ON TARGET",
        "sections": ("Usage types and payload (optional attributes)",),
        "returned":
            "ON TARGET and #1: Senzing Entity Specification -> 'Usage types and payload (optional "
            "attributes)', carrying the quoted definition verbatim: 'A short label that "
            "distinguishes multiple instances of the same feature on one entity'. Then 'Payload "
            "attributes (optional)' and 'Mapping usage types'",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "Identifiers NATIONAL_ID PASSPORT TAX_ID TRUSTED_ID feature group": {
        "band": "ON TARGET",
        "sections": ("Identifiers > Feature: TAX_ID", "Identifiers > Feature: NATIONAL_ID"),
        "returned":
            "ON TARGET: Senzing Entity Specification -> 'Identifiers > Feature: TAX_ID', then "
            "'Identifiers > Feature: NATIONAL_ID' and 'Mapping identifiers'. These are members OF "
            "the Identifiers section, which is what the call site's grouping claim rests on -- "
            "the section heading itself is not a separately indexed chunk, so the members are the "
            "evidence. NOTE: the set has no TRUSTED_ID section, and the specification files it as "
            "'Trusted ID > Feature: TRUSTED_ID', not under Identifiers (checked in the same "
            "measurement). The site's list of Identifiers members names TRUSTED_ID, so its prose "
            "stamp was left alone and a follow-up drafted (#417)",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "ACCOUNT_NUMBER ACCOUNT_DOMAIN account feature": {
        "band": "ON TARGET",
        "sections": ("Feature: ACCOUNT",),
        "returned":
            "ON TARGET and #1: Senzing Entity Specification -> 'Identifiers > Feature: ACCOUNT', "
            "carrying 'Domain/system for the account number' verbatim -- the definition the call "
            "site quotes",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "recommended JSON schema FEATURES list multiple values sub-list": {
        "band": "ON TARGET",
        "sections": ("Recommended JSON schema",),
        "returned":
            "ON TARGET and #1: Senzing Entity Specification -> 'Recommended JSON schema', "
            "carrying the quoted sentence verbatim ('In prior versions we allowed a flat JSON "
            "structure with a separate sub-list for each feature that had multiple values. While "
            "we still support that, we now recommend ...'). The 2026-08-23 record also named the "
            "Schema Validation Rules that declare FEATURES required; the excerpt returned here "
            "ends inside the organization example and does not show them, so they are no longer "
            "recorded. No site quotes them",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    # Executed 2026-08-17 on server 1.32.9 (docs index 2026-08-11 20:52 UTC), later than
    # VERIFIED_ON above, which records the date the bulk of this allowlist was measured.
    # Re-run 2026-10-01 on server 1.37.16 (docs index 2026-09-29 22:00 UTC, #322): still
    # returns no section stating the consequence -- that a root-level key named after a
    # registered feature attribute is extracted as a feature. The prohibition itself is now
    # cited to mapping_workflow step 2, so the marker's claim was rescoped to the consequence
    # and this query string was deliberately left unchanged.
    # Re-executed for #383 on server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02, with
    # category='data_mapping' (its record read "ADJACENT, AND DELIBERATELY SO", outside the band
    # set): the same three specification sections, and still no precedence.
    "payload attribute versus registered feature attribute record root extracted as feature precedence": {
        "band": "EMPTY OF THE PRECEDENCE RULE",
        "sections": (),
        "returned":
            "EMPTY OF THE PRECEDENCE RULE, AND DELIBERATELY SO: Senzing Entity Specification -> "
            "'Payload attributes (optional)', 'Attributes for the record key', 'Mapping "
            "identifiers'. These establish that payload and registered features are distinct "
            "categories and that choosing between them is a mapping decision -- they do NOT "
            "state the precedence when a payload-intended root key carries a registered "
            "attribute's name, which is exactly what the MCP-NEGATIVE marker at that call site "
            "claims. The query is prescribed so a reader can re-run the absence, not to "
            "retrieve an answer. NOTE: the highest-scoring results overall are off-topic "
            "pricing sections ('Data Source Records (DSRs) Explained', 'Uniquely Identifying "
            "Records in Senzing') ranked after the data_mapping rows, so category='data_mapping' "
            "boosts rather than filters",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    # Executed 2026-08-21 on server 1.33.0 (docs index 2026-08-20 17:33 UTC), for the datastore
    # mount-crossing guidance added to module-02 Step 7.
    # Re-executed for #383 on server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02, with
    # category='anti_patterns' (its record named only module-02's two sections, while Module 6
    # Phase A reads "Do Not Use SQLite in Production" from the same call). The 2026-08-21 record
    # read: Configuration and Initialization (12.6), then Architecture and Performance (12.0),
    # with a Rust code example (35.4) the filter did not exclude. That example is gone: the call
    # now returns four anti-pattern articles ("Returned 4 of 10 results").
    "loading": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Senzing Anti-Patterns: Architecture and Performance",
                     "Do Not Use SQLite in Production", "Do Not Use Single-Threaded Loading",
                     "Do Not Use Low-IOPS Storage",
                     "Do Not Skip check_repository_performance() Before Production"),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT, with category='anti_patterns': the top hit is "
            "'Senzing Anti-Patterns: Configuration and Initialization' (it carries 'Do Not Skip "
            "check_repository_performance() Before Production', module-02 Step 7's second "
            "anti-pattern); the second is 'Senzing Anti-Patterns: Architecture and Performance', "
            "which carries 'Do Not Use Single-Threaded Loading', 'Do Not Use SQLite in Production' "
            "('use SQLite only for quick local testing with small datasets (under 100K records)'), "
            "'Do Not Use Low-IOPS Storage' and the redo anti-patterns. Then the 'Database "
            "Initialization and Container Setup' and 'Installing in Sandboxed or Restricted-Egress "
            "Environments' articles. NOTE: a single-word query is BM25-fragile by nature -- it "
            "works only because category='anti_patterns' narrows the corpus to a handful of "
            "documents. Every site says to read past the first hit",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    # The six below were measured on server 1.32.9, docs index 2026-08-11 20:52 UTC, on
    # 2026-08-12 (fdbc922): the stamp the module-level VERIFIED_ON recorded for them. #383
    # re-executed two of them; #417 re-executed the other four, with the same sections returned.
    "entity resolution business value": {
        "band": "ON TARGET",
        "sections": ("Five Primary Business Use Cases", "Why Agentic Entity Resolution Matters"),
        "returned":
            "ON TARGET: Entity Resolution Buyer's Guide -> 'Five Primary Business Use Cases > "
            "Step 1: Define your organization's use case for entity resolution before evaluating "
            "solutions'; Agentic Entity Resolution -> 'Why Agentic Entity Resolution Matters', "
            "whose Business Impact list is broken out by use case; then the Buyer's Guide's 'The "
            "Steps To Evaluating Entity Resolution' (Step 6: Time To Value). In the same "
            "measurement 'value proposition Supply Chain' still returns senzing/libpostal geodata "
            "chains scripts first and the sz_spark changelog's 'CI / supply chain' heading, and "
            "'entity resolution business value supply chain' still puts the libpostal "
            "chains_tsv.py script first, above the real material, as Step 14 says",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "what features to map": {
        "band": "ON TARGET",
        "sections": ("What features to map",),
        "returned":
            "ON TARGET, with category='data_mapping': Senzing Entity Specification -> 'What "
            "features to map' (exact section), whose table describes DOB as 'Person date of "
            "birth', NAME (person) as 'Personal names' and NAME (organization) as 'Organization "
            "legal or trade name'. The NATIONALITY, CITIZENSHIP and PLACE_OF_BIRTH rows ('Person "
            "...') and the 'Feature: REGISTRATION_DATE (organizations)' and 'Feature: "
            "REGISTRATION_COUNTRY (organizations)' headings that Phase 1's applicability table "
            "quotes were checked in the same measurement",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    # Re-executed for #383 on server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02: the
    # 2026-08-12 record, "ON TARGET: Senzing Engine Configuration (exact page)", named a page
    # and no section.
    "Senzing engine configuration PostgreSQL connection": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("SQL > CONNECTION",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT: the top hit is the Senzing Engine Configuration "
            "page's introduction, section 'Senzing Engine Configuration' (what the configuration "
            "holds, and that SENZING_ENGINE_CONFIGURATION_JSON is used by default); the second is "
            "the same page's 'Section: SQL > CONNECTION', the connection-URL table with the "
            "PostgreSQL form postgresql://user:password@host:port/database; the third is its "
            "'SENZING_ENGINE_CONFIGURATION_JSON example' with a PostgreSQL CONNECTION",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    # Measured 2026-08-12 (fdbc922) as "ON TARGET: Database Setup -> 'PostgreSQL Setup: Create
    # the database, schema, and permissions'". Re-executed for #383 on server 1.37.19, docs
    # index 2026-10-02 18:46 UTC, 2026-10-02, with category='anti_patterns' as the site passes
    # it, before naming the section at the site: the Database Setup page is no longer in the
    # set, so the 2026-08-12 record was replaced, not re-dated.
    "PostgreSQL schema DDL initialization": {
        "band": "ON TARGET",
        "sections": ("PostgreSQL Schema Is NOT Auto-Created by the SDK",),
        "returned":
            "ON TARGET, with category='anti_patterns': the top hit is 'Senzing Anti-Patterns: "
            "Database Initialization and Container Setup', whose first section, 'PostgreSQL "
            "Schema Is NOT Auto-Created by the SDK', lists the schema DDL files per platform "
            "(szcore-schema-postgresql-create.sql under /opt/senzing/er/resources/schema/ on "
            "Linux and Docker) and says to apply them before creating the factory. Then the "
            "'Configuration and Initialization', 'Architecture and Performance' and 'Operations "
            "and Runtime' articles",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    "CORD datasets: names, contents, and availability for entity resolution scenarios": {
        "band": "ON TARGET",
        "sections": ("What Is a CORD?",),
        "returned":
            "ON TARGET: Collections Of Relatable Data (CORDs) -> 'What Is a CORD?' (the section "
            "name renders in bold); the same page's 'Moscow CORD' section is in the set below it",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "temporary evaluation license for a dataset larger than the default limit": {
        "band": "ON TARGET",
        "sections": ("Senzing Non-Production License",),
        "returned":
            "ON TARGET: End User License Agreement (EULA) & Warranty Statement -> '1. GRANT OF "
            "LICENSE.' > 'A. Senzing Non-Production License', the highest-scoring hit; 'B. "
            "Senzing Production License' follows just below it",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    # Executed against server 1.32.9, docs indexed 2026-08-11 20:52 UTC, on 2026-08-14, for
    # module-04 Step 8b's load-time estimate. Re-executed for #417: the route still holds, and the
    # longer phrasing the 2026-08-14 record warned about now finds the FAQ too (see its NOTE).
    # Re-executed for #439 on the same index (1.37.19, docs index 2026-10-02 18:46 UTC,
    # 2026-10-04): the FAQ is still rank 1 for both phrasings, so the stamp is not re-dated, and
    # Step 8b's warning was replaced by a rule that cites no measurement (see the NOTE).
    "hardware sizing capacity planning": {
        "band": "ON TARGET",
        "sections": ("Hardware Sizing FAQ",),
        "returned":
            "ON TARGET: Hardware Sizing FAQ -> 'Full Article', carrying throughput per engine "
            "core (~5-10 records/second steady state), the three load phases (Phase 1 throughput "
            "can be 10-100x higher than Phase 3) and worked load-time examples (1,000 records ~2 "
            "minutes; 100,000 ~55 minutes). NOTE: the 2026-08-14 record said the longer phrasing "
            "'hardware sizing capacity planning records per second load time' drops the FAQ "
            "entirely. In this measurement that phrasing returns the FAQ first, then add_record "
            "flag docs and loading code snippets (#417, again in #439). #439 resolved Step 8b's "
            "'Nearby wordings do not find the FAQ' warning: it replaced the warning and its "
            "stamp with a rule that cites no measurement, to use the query as written because a "
            "paraphrase is unmeasured (INV-291)",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
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
    "upgrade Senzing SDK 4.3 to 4.4 procedure": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the routing negative's missing half: the corpus serves V3-to-V4 "
            "migration material for this phrasing, top hit the FAQ 'What are the exact steps to "
            "migrate from V3 to V4?' naming sz_dbupgrade/sz_configupgrade/sz_configtool, and no "
            "4.x-to-4.y procedure. The 4.x-to-4.y notes are reached through category='release_notes' "
            "with the 'upgrading to 4.4.0 …' phrasing above, which is what module-02 Step 1b's "
            "marker names as the owner (server 1.37.14, docs index 2026-09-28 03:23 UTC, "
            "re-executed 2026-09-28)",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    # Re-executed for #150 on server 1.37.13, docs index 2026-09-24 18:45 UTC (2026-09-24, and
    # again 2026-09-26 with the same result). The 2026-08-13 record said the query "gives no
    # figure"; the rebuilt index added an FAQ that states the figure outright, so the set now
    # answers it and only the ranking keeps it off target. That record was replaced, not
    # re-dated. ⚠️ Record the ranking property, not ranks or scores: they move on a rebuild.
    "evaluation license record limit how many records without a license": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the negative's evidence, now a ranking one: the top-ranked hits "
            "are the EULA's grant-of-license sections ('Senzing Non-Production License' first, "
            "'solely for up to the number of DSRs designated therein'), which state no figure. The "
            "result set does carry the figure, in a lower-ranked FAQ, 'What is the 500 record limit "
            "and how do I work around SENZ9000'. sdk_guide(topic='load', record_count=<above the "
            "limit>) states it in a fixed field instead, compatibility_notes — 'the default Senzing "
            "license limit of 500' (server 1.37.13, docs index 2026-09-24 18:45 UTC, re-executed "
            "2026-09-26)",
        "server": "1.37.13", "docs_index": "2026-09-24 18:45 UTC", "measured": "2026-09-26",
    },
    # Module 5's multi-language retrieval strategy (INV-212), added 2026-08-13. The first two are
    # queries the step tells the guide to RUN; the last two are the evidence slots of its two
    # `MCP-NEGATIVE` markers — quoted in order to be forbidden. All four executed against server
    # 1.32.9, docs indexed 2026-08-11 20:52 UTC, on 2026-08-13; "globalization" was re-executed
    # for #149 (below), and the other three for #417, in the same measurement as the four
    # "Section to ask for" rows of Module 5's table, which the two prose stamps there vouch for.
    "UTF-8 encoding non-Latin character support multi-language data quality": {
        "band": "ON TARGET",
        "sections": ("What languages does Senzing support?",),
        "returned":
            "ON TARGET with category='globalization': Senzing Globalization Guide -> 'What "
            "languages does Senzing support?', which states the UTF-8 and cross-script answer "
            "outright, then 'Advanced personal name comparisons > Supported cultural groups' and "
            "'... > Additional Cultural Support'. ⚠️ category='code_example' rows (libpostal "
            "encoding.py, a Rust FFI guide) carry a HIGHER relevance_score but are returned AFTER "
            "the on-topic rows -- the filter promotes rather than restricts, so never rank this "
            "set by score",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "data quality practices multi-language non-Latin": {
        "band": "ON TARGET",
        "sections": ("CJK+English cross-script matching",),
        "returned":
            "ON TARGET with category='globalization': Globalization Guide -> 'Address matching "
            "examples > CJK+English cross-script matching (new in v4)', whose prose carries the "
            "practice — native-to-native beats native-to-Romanized, and for non-CJK cross-script, "
            "Romanize via an address-hygiene product and supply both forms. Three Guide rows come "
            "first; repo docs/best-practices.md files follow with a higher relevance_score",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    # Re-executed for #149 on server 1.37.13, docs index 2026-09-24 18:45 UTC, 2026-09-26, at
    # max_results=6 and at the default. The 2026-08-13 record above this entry said its best
    # Guide hit was a bare title with no prose; the rebuilt index returns Guide sections with
    # prose, so that record was replaced rather than re-dated. ⚠️ Record the PROPERTY, not the
    # ranks: a rank order is what went stale here, and the next rebuild can move it again.
    "globalization": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the negative's evidence, and the anti-pattern Module 5 quotes: "
            "the corpus serves Senzing Globalization Guide sections with real prose for it, and the "
            "bare term also admits unrelated Global* substring matches — the Rust SDK's static "
            "GLOBAL_ENVIRONMENT, postgresql-performance-v4's 'Global — more workers' autovacuum "
            "tuning and an MDM-Lite FAQ on 'globally unique ID'. It did not return the 'What "
            "languages does Senzing support?' section, which the category='globalization' query "
            "above ranks first (server 1.37.13, docs index 2026-09-24 18:45 UTC, re-executed "
            "2026-09-26)",
        "server": "1.37.13", "docs_index": "2026-09-24 18:45 UTC", "measured": "2026-09-26",
    },
    "multi-language data quality best practices": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the negative's evidence: the top six of ten hits are repo "
            "docs/best-practices.md template files (senzingsdk-tools, senzingapi-runtime, "
            "senzingapi-tools, senzingsdk-runtime, homebrew-senzingsdk, scoop-senzingsdk), all "
            "about Markdown lint and Dockerfiles, two of them title-only stubs; the rest are a "
            "libpostal-data address-parser quality note, a 'Data Quality & Accuracy' use-case "
            "blurb, an economic-cost appendix and an FFI 'Best Practices' list. No globalization "
            "content at all — the phrase 'best practices' is the whole defect. With "
            "category='globalization' the three Guide rows come first and the same files follow, "
            "scoring ~89 against the Guide's ~9–13",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    "szBuildVersion.json build version file location": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — this is the negative's evidence: no indexed document gives the "
            "file's path on any platform. It serves SDK version-call examples for it, top hit "
            "senzing/code-snippets-v4 -> python/information/get_version.py, and build/packaging "
            "documents. The corpus serves SzProduct.get_version(), not a file location, which is why "
            "Step 1 routes the reader to the SDK call and marks the file paths as environment "
            "observations (server 1.37.13, docs index 2026-09-24 18:45 UTC, re-executed 2026-09-26)",
        "server": "1.37.13", "docs_index": "2026-09-24 18:45 UTC", "measured": "2026-09-26",
    },
    # Executed for #169 on server 1.37.13, docs index 2026-09-24 18:45 UTC, 2026-09-26, at
    # max_results=5. The visualization contract's /api/how entry quotes it in its MCP-NEGATIVE
    # marker as the corpus route asked for a meaning of the flag. Re-executed for #154 on the
    # same server and index, 2026-09-27, with the same result: Phase D's How-state audit quotes
    # it in its own MCP-NEGATIVE marker.
    "NEED_REEVALUATION how entity final state": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the negative's evidence: the top hit is the "
            "how_entity_by_entity_id Flags page's SZ_HOW_ENTITY_DEFAULT_FLAGS section, whose example "
            "payload shows \"NEED_REEVALUATION\": 0; the others are that page's intro, its "
            "SZ_INCLUDE_MATCH_KEY_DETAILS example, an Entity ID FAQ and an unrelated libpostal file. "
            "No hit defines the field or says what sets or clears it",
        "server": "1.37.13", "docs_index": "2026-09-24 18:45 UTC", "measured": "2026-09-27",
    },
    # Executed for #154 on server 1.37.13, docs index 2026-09-24 18:45 UTC, 2026-09-27, at the
    # default max_results. The second corpus query in Phase D's How-state audit MCP-NEGATIVE
    # marker: asked whether any document ties a re-evaluation call to the flag.
    # ⚠️ Record the PROPERTY, not ranks or scores: they move on a rebuild.
    # Re-executed for #383 on server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02 (its
    # record read "ADJACENT, NOT ON TARGET", outside the band set): the same material.
    "reevaluate entity when to call reevaluation needed": {
        "band": "EMPTY OF A NEED_REEVALUATION TIE",
        "sections": (),
        "returned":
            "EMPTY OF A NEED_REEVALUATION TIE — the negative's evidence: re-evaluation code "
            "snippets (Rust, Python), the SzFlag/SzFlags reevaluate-entity flag constants, a "
            "TypeScript 'Reevaluate an entity after rule changes' example, and the engine-config "
            "FAQ 'After config changes, reevaluate splits entities but redo merges them back. Is "
            "this a bug?', which is about config changes. No hit names NEED_REEVALUATION or ties "
            "a re-evaluation call to it",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    # ---------------------------------------------------------------------------------
    # The two below are double-quoted literals, invisible to this guard until #383 matched
    # `query="…"`. Both executed for #383 on server 1.37.19, docs index 2026-10-02 18:46 UTC,
    # 2026-10-02, at the default max_results.
    # Module 6 Phase B's redo-drain step tells the guide to confirm the anti-pattern through it.
    "redo": {
        "band": "ON TARGET",
        "sections": ("Do Not Use count_redo_records() as a Loop Condition",),
        "returned":
            "ON TARGET, with category='anti_patterns': the top hit is 'Senzing Anti-Patterns: "
            "Architecture and Performance', which carries 'Do Not Skip Redo Processing' and 'Do "
            "Not Use count_redo_records() as a Loop Condition' (a full table scan per call, O(n²), "
            "and redo generates more redo; loop on get_redo_record() returning empty). The "
            "category boosts rather than filters: the 'Redo Processing FAQ' and redo code "
            "examples follow with higher raw scores",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    # The onboarding preface quotes it as the probe NOT to use; the claim it carries is that it
    # returns a multi-page FAQ article rather than a cheap reachability answer.
    "health check": {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — quoted as the forbidden probe: the top hit is the Senzing MCP "
            "server article 'Health Monitoring for Senzing Deployments', section 'Full Article', "
            "a multi-section FAQ (health checks, get_stats, check_repository_performance, data "
            "health SQL, redo queue depth) several kilobytes long, followed by unrelated "
            "check-script code examples and Rust check_* function pages. Nothing in it answers "
            "'did the server answer at all', which is why the preface probes with "
            "get_capabilities",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
    # ---------------------------------------------------------------------------------
    # Executed for #392 on server 1.37.19, docs index 2026-10-02 18:46 UTC, 2026-10-02, at the
    # default max_results. Module 6 Phase B's quality_iteration receiving branch cites it for the
    # record-key replacement that lets a reload skip deleting the records whose IDs survived.
    "Data Source Records DSRs Explained same DATA_SOURCE RECORD_ID replaces": {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Uniquely Identifying Records in Senzing",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT: the top three hits are sections of 'Data Source "
            "Records (DSRs) Explained'. The top hit is 'Important Nuances > Expanding Data "
            "Sources'; the second is 'Uniquely Identifying Records in Senzing', which says the "
            "data source code plus the record ID is a record's unique key and that a record sent "
            "with a key that matches a loaded record replaces it; the third is 'Important Nuances "
            "> Event Sources'. The rest of the set is register_data_source code examples. The "
            "site says to read past the first hit",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    },
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

#: Vocabulary that tells the reader to read past the first hit, required at every site of an
#: `ON TARGET BELOW AN ADJACENT TOP HIT` route.
READ_PAST = re.compile(
    r"(?i)\bread (?:past|down past|down to|below)\b|past the (?:first|top) (?:hit|result)"
)

#: Both quote styles (#383): a double-quoted literal was invisible to the single-quote form.
QUERY_LITERAL = re.compile(r"""search_docs\(query=(?:'([^']*)'|"([^"]*)")""")
HEADING = re.compile(r"(?m)^#{2,4} ")


def shipped_markdown():
    return sorted(SKILLS.rglob("*.md"))


def sections(text):
    """(start, end) spans between Markdown headings, so 'the same step' is well-defined."""
    bounds = [m.start() for m in HEADING.finditer(text)] + [len(text)]
    if not bounds or bounds[0] != 0:
        bounds = [0] + bounds
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


def queries_in(label, text):
    """(label, query, enclosing section text) for every query literal in one document."""
    found = []
    spans = sections(text)
    for match in QUERY_LITERAL.finditer(text):
        section = next(
            (text[a:b] for a, b in spans if a <= match.start() < b), text
        )
        literal = match.group(1) if match.group(1) is not None else match.group(2)
        # Whitespace-collapsed: a literal wrapped across source lines is still one
        # query. A line-based scan misses these entirely — three of the eight
        # prescribed queries in this corpus are wrapped, and all three were invisible
        # to the first version of this guard.
        query = re.sub(r"\s+", " ", literal).strip()
        found.append((label, query, section))
    return found


def prescribed_queries():
    """(path, query, enclosing section text) for every prescribed query literal."""
    found = []
    for path in shipped_markdown():
        text = path.read_text(encoding="utf-8")
        found.extend(queries_in(path.relative_to(REPO_ROOT), text))
    return found


def unaccounted(found, allowlist):
    """Query sites with no allowlist entry and no re-query rule in their section."""
    return [
        f"{label}: search_docs(query='{query}')"
        for label, query, section in found
        if query not in allowlist and not REQUERY_RULE.search(section)
    ]


def flat(text):
    """Section text as a reader sees it: no blockquote markers, emphasis, code ticks or wraps."""
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    text = text.replace("`", "").replace("*", "").replace("\\", "")
    return re.sub(r"\s+", " ", text)


def band_is_known(band):
    return (
        band in POSITIVE_BANDS or band in NEGATIVE_BANDS
        or bool(isinstance(band, str) and EMPTY_OF_BAND.match(band))
    )


def record_problems(query, record):
    """Every way one VERIFIED_QUERIES value fails the INV-291 record (#383). Empty means sound."""
    where = f"VERIFIED_QUERIES[{query!r}]"
    if not isinstance(record, dict):
        return [f"{where} is a {type(record).__name__}, not a record with a stamp and a band "
                f"(INV-291)"]
    problems = []
    missing = [f for f in RECORD_FIELDS if f not in record]
    extra = sorted(set(record) - set(RECORD_FIELDS))
    if missing:
        problems.append(f"{where} has no {', '.join(missing)} (INV-291)")
    if extra:
        problems.append(f"{where} has unknown fields {extra} (INV-291)")
    band = record.get("band")
    if "band" in record and not band_is_known(band):
        problems.append(
            f"{where} band {band!r} is outside the closed set {POSITIVE_BANDS + NEGATIVE_BANDS} "
            f"+ 'EMPTY OF …' (INV-291)")
    returned = record.get("returned")
    if "returned" in record and not (isinstance(returned, str) and len(returned) > 15):
        problems.append(f"{where} records no result: a verification with no recorded result "
                        f"cannot be re-checked (INV-291)")
    names = record.get("sections")
    if "sections" in record:
        if not isinstance(names, tuple) or not all(isinstance(n, str) and n for n in names):
            problems.append(f"{where} sections must be a tuple of section names (INV-291)")
        elif band in POSITIVE_BANDS and not names:
            problems.append(f"{where} has a positive band and names no section it returned "
                            f"(INV-291)")
        elif isinstance(returned, str):
            absent = [n for n in names if n not in returned]
            if absent:
                problems.append(f"{where} names sections its recorded result does not mention: "
                                f"{absent} (INV-291)")
    server = record.get("server")
    if "server" in record and not (isinstance(server, str) and SERVER_VERSION.match(server)):
        problems.append(f"{where} server {server!r} is not a version like 1.37.19 (INV-291)")
    index_day = None
    if "docs_index" in record:
        try:
            index_day = datetime.strptime(record["docs_index"], DOCS_INDEX_FORMAT).date()
        except (TypeError, ValueError):
            problems.append(f"{where} docs_index {record['docs_index']!r} is not "
                            f"'YYYY-MM-DD HH:MM UTC' (INV-291)")
    if "measured" in record:
        try:
            measured = date.fromisoformat(record["measured"])
        except (TypeError, ValueError):
            problems.append(f"{where} measured {record['measured']!r} is not 'YYYY-MM-DD' "
                            f"(INV-291)")
        else:
            if index_day and measured < index_day:
                problems.append(f"{where} was measured ({measured}) before its docs index was "
                                f"built ({index_day}) (INV-291)")
    return problems


def site_problems(found, allowlist):
    """Sites of a positive-band entry that name no section it returns, or skip the read-past."""
    problems = []
    for label, query, section in found:
        record = allowlist.get(query)
        if not isinstance(record, dict) or record.get("band") not in POSITIVE_BANDS:
            continue
        text = flat(section)
        if not any(flat(name) in text for name in record.get("sections", ())):
            problems.append(f"{label}: search_docs(query='{query}') names none of "
                            f"{record.get('sections')} (INV-291)")
        if record["band"] == BELOW_TOP_HIT and not READ_PAST.search(text):
            problems.append(f"{label}: search_docs(query='{query}') is {BELOW_TOP_HIT} and its "
                            f"section does not say to read past the first hit (INV-291)")
    return problems


class EveryPrescribedQueryIsAccountedFor(unittest.TestCase):
    def test_the_scan_finds_the_queries(self):
        found = prescribed_queries()
        self.assertGreaterEqual(len(found), 5, "the query scan came up empty or too small")

    def test_the_scan_sees_double_quoted_literals(self):
        quoted = {q for _p, q, _s in prescribed_queries()} & {"redo", "health check"}
        self.assertEqual({"redo", "health check"}, quoted,
                         "QUERY_LITERAL no longer matches search_docs(query=\"…\") (INV-291)")

    def test_each_query_is_verified_or_carries_a_requery_rule(self):
        missing = unaccounted(prescribed_queries(), VERIFIED_QUERIES)
        self.assertEqual(
            [],
            missing,
            "A shipped step prescribes a search_docs query that was never verified against "
            "the server and has no re-query rule in its section (INV-291). search_docs is BM25, "
            "so an unexecuted phrasing can return anything — and a miss looks exactly like "
            "documentation that does not cover the topic. Verify it and add it to "
            "VERIFIED_QUERIES with its observed result, band and stamp, or pair it with a "
            "re-query instruction:\n  " + "\n  ".join(missing),
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

    def test_every_allowlist_entry_is_a_stamped_banded_record(self):
        problems = [p for q, r in VERIFIED_QUERIES.items() for p in record_problems(q, r)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_site_names_its_section_and_reads_past_an_adjacent_top_hit(self):
        problems = site_problems(prescribed_queries(), VERIFIED_QUERIES)
        self.assertEqual(
            [], problems,
            "An inline route's site must name the section its record says it returns, and a "
            "route whose target sits below an adjacent top hit must say to read past the first "
            "hit (INV-291):\n  " + "\n  ".join(problems))


def _good_record(**changes):
    record = {
        "band": "ON TARGET",
        "sections": ("What features to map",),
        "returned": "ON TARGET: Senzing Entity Specification -> 'What features to map'",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-02",
    }
    record.update(changes)
    return record


class TheGuardFailsWhereItShould(unittest.TestCase):
    """Negative controls: each check rejects the defect it exists for, and cites INV-291."""

    def assert_rejected(self, problems, needle):
        self.assertTrue(problems, "the check passed a defective input")
        self.assertTrue(any(needle in p for p in problems), problems)
        self.assertTrue(all("INV-291" in p for p in problems), problems)

    def test_a_sound_record_passes(self):
        self.assertEqual([], record_problems("what features to map", _good_record()))

    def test_an_unallowlisted_double_quoted_literal_fails(self):
        text = "## Step\n\nRun `search_docs(query=\"never measured phrasing\")` and use it.\n"
        missing = unaccounted(queries_in("fixture.md", text), VERIFIED_QUERIES)
        self.assertEqual(["fixture.md: search_docs(query='never measured phrasing')"], missing)

    def test_a_requery_rule_still_exempts_a_double_quoted_literal(self):
        text = ("## Step\n\nRun `search_docs(query=\"never measured phrasing\")`; if it comes "
                "back off-topic, re-query.\n")
        self.assertEqual([], unaccounted(queries_in("fixture.md", text), VERIFIED_QUERIES))

    def test_a_bare_string_entry_fails(self):
        self.assert_rejected(record_problems("q", "ON TARGET: some section, measured once"),
                             "not a record")

    def test_a_missing_stamp_fails(self):
        for field in ("server", "docs_index", "measured"):
            with self.subTest(field=field):
                record = _good_record()
                del record[field]
                self.assert_rejected(record_problems("q", record), f"has no {field}")

    def test_a_malformed_stamp_fails(self):
        cases = {
            "server": ("server", "1.37"),
            "docs_index": ("docs_index", "2026-10-02"),
            "docs_index time": ("docs_index", "2026-10-02 18:46"),
            "measured": ("measured", "2 Oct 2026"),
        }
        for name, (field, value) in cases.items():
            with self.subTest(case=name):
                self.assert_rejected(record_problems("q", _good_record(**{field: value})),
                                     field)

    def test_a_measurement_before_its_index_fails(self):
        self.assert_rejected(record_problems("q", _good_record(measured="2026-10-01")),
                             "before its docs index")

    def test_a_band_outside_the_set_fails(self):
        for band in ("ADJACENT, AND DELIBERATELY SO", "ON TARGET and #1", "RANK 2", "EMPTY OF"):
            with self.subTest(band=band):
                self.assert_rejected(record_problems("q", _good_record(band=band)),
                                     "outside the closed set")

    def test_a_negative_band_is_in_the_set(self):
        record = _good_record(band="EMPTY OF THE TARGET", sections=())
        self.assertEqual([], record_problems("q", record))

    def test_a_positive_band_must_name_a_section(self):
        self.assert_rejected(record_problems("q", _good_record(sections=())),
                             "names no section")

    def test_a_named_section_must_be_in_the_recorded_result(self):
        self.assert_rejected(record_problems("q", _good_record(sections=("Elsewhere",))),
                             "does not mention")

    def test_a_site_that_names_no_section_fails(self):
        allowlist = {"what features to map": _good_record()}
        text = "## Step\n\nRun `search_docs(query='what features to map')`.\n"
        self.assert_rejected(site_problems(queries_in("fixture.md", text), allowlist),
                             "names none of")

    def test_a_below_top_hit_site_without_read_past_fails(self):
        allowlist = {"what features to map": _good_record(band=BELOW_TOP_HIT)}
        text = ("## Step\n\nRun `search_docs(query='what features to map')`; its *What "
                "features to map* section answers it.\n")
        self.assert_rejected(site_problems(queries_in("fixture.md", text), allowlist),
                             "read past the first hit")
        fixed = text.replace("answers it.", "answers it: read past the first hit.")
        self.assertEqual([], site_problems(queries_in("fixture.md", fixed), allowlist))


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
        self.assertIn("1.37.19", flat)
        self.assertIn("2026-10-04", flat)

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
