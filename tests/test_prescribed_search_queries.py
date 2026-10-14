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

**#513 closed three gaps that let unmeasured routes through.** Measured on server 1.37.27, docs
index 2026-10-11 18:43 UTC, 2026-10-12:

- **Records are keyed on `(query, category)`.** Module 5 Phase 3 passed `"globalization"` with
  `category="globalization"`, and the guard matched it to the record for the bare term, whose band
  is `OFF TARGET BY DESIGN`, so its positive use was never checked.
- **A record's `sections` names only what its band supports.** The MATCH_KEY record listed
  `Feature: REL_ANCHOR`, which it returns fourth, so a site citing that query for the no-dashes
  rule passed. A target below rank 3 is not a route.
- **A `search_docs` mention that passes `category=` and names no `query=` fails**, in prose as well
  as in a call: Module 2 said "call `search_docs` with `category='anti_patterns'`", which
  `test_search_docs_calls_pass_a_query.py` cannot see because it reads only `search_docs(` calls.

**A route used at more than one site is stated once, and the other sites point at it (INV-300).**
A pointing site says the route "is stated once, in `<file>` → \"<heading or bold lead>\"". The
guard follows the pointer, takes the measured routes in the section it lands on, and checks the
pointing site against their records: it must name a section one of them returns. A pointer that
lands nowhere, or on a section with no measured route, fails. The read-past obligation stays with
the canonical site, which INV-291 binds; a pointer is outside INV-291's scope by its own text.

**#600 closed what #513 left open.** Measured on server 1.38.2, docs index 2026-10-14 20:27 UTC,
2026-10-14, at each tool's default `max_results`:

- **A route stated in full under two headings fails.** The loading anti-patterns route was stated
  at seven sites that already differed on `version="current"` and on their stamps. A literal inside
  an `MCP-NEGATIVE` marker's owner clause is evidence, not a statement, and so is a negative-band
  quote.
- **`find_examples(query=` is scanned too**, keyed on `(tool, query, language)` in the same record
  type. Its search returns one example per repository in repository order, so a route is a query
  whose target repository and file come first.
- **The record is the route's one stamp.** A shipped site names the query and the section it relies
  on and carries no server version or docs index of its own: those went stale at every rebuild and
  disagreed with the record. `STAMPED_IN_PROSE` lists the sites that still do, and only shrinks.

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

#: (tool, query, category-or-language) -> a record of what the query returned, so the
#: verification is re-checkable and not just asserted. The tool is `search_docs` or
#: `find_examples` (#600). The third member is the `category=` a `search_docs` call passes or the
#: `language=` a `find_examples` call passes, or None for a call that passes none (#513):
#: `category` boosts rather than filters, so the same words under two categories are two
#: measurements, and keying on the words alone matched a filtered call to an unfiltered call's
#: record. Each record is the route's one stamp: a shipped site names the query and the section
#: it relies on, and carries no date of its own (#600). "Verified" means EXECUTED and its result written down — not "ideal". Where a
#: phrasing lands on adjacent rather than on-target material that is said so explicitly, because
#: an allowlist that quietly upgrades "I ran it" into "it is good" is the same laundering this
#: guard exists to stop.
VERIFIED_QUERIES = {
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-30 on server 1.37.16 (docs index 2026-09-29 22:00 UTC) for #289, Module 6
    # Phase D's per-binding flag-availability route. ⚠️ Record the PROPERTY, not ranks or scores.
    ("search_docs", "senzing.szengineflags SzEngineFlags SZ_EXPORT_DEFAULT_FLAGS", None): {
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
    # Step 3 Phase 3's route for the Java bindings. The C# query recorded beside it (#287, #320)
    # was removed by #566 (2026-10-13): on server 1.37.28 every platform's install reply names
    # the C# source, so the fallback no longer asks `search_docs` and no shipped file prescribes
    # the query. ⚠️ Record the PROPERTY, not ranks or scores.
    ("search_docs", "Java SDK sz-sdk.jar Maven Usage local Maven repository", None): {
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
    # ---------------------------------------------------------------------------------
    # Executed 2026-09-28 on server 1.37.14 (docs index 2026-09-28 03:23 UTC) for #194, Module 2
    # Step 1b's update path and Step 2's preview-status relay. The first two are the update
    # commands' route; the third is the point-release notes' route, and the three after it are
    # evidence slots of MCP-NEGATIVE markers. ⚠️ Record the PROPERTY, not ranks or scores.
    ("search_docs", "homebrew-senzingsdk upgrade cask brew upgrade senzingsdk", None): {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Upgrade",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT: the top hit is the V3-to-V4 FAQ 'What are the "
            "exact steps to migrate from V3 to V4?'; the set carries senzing/homebrew-senzingsdk "
            "section 'Upgrade' (brew update, brew upgrade --cask senzingsdk) and the README's "
            "'Preview Release — Unsupported' warning. Step 1b says to read past the first result",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    # Re-executed for #600 at the default max_results: the same top hit. Step 1b states the
    # route; Step 2's preview relay points at it (INV-300).
    ("search_docs", "scoop-senzingsdk update scoop update senzingsdk", None): {
        "band": "ON TARGET",
        "sections": ("Update", "Preview Release — Unsupported"),
        "returned":
            "ON TARGET: the top hit is the senzing/scoop-senzingsdk README, which opens with the "
            "'Preview Release — Unsupported' warning and carries section 'Update' (scoop update "
            "senzingsdk); its CHANGELOG and template docs follow. Stated at Step 1b's update "
            "command; Step 2's preview relay points there",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    ("search_docs", "upgrading to 4.4.0 from v4.0.0 through v4.3.x no schema change required migration action required",
     "release_notes"): {
        "band": "ON TARGET",
        "sections": ("Migration & Action Required",),
        "returned":
            "ON TARGET, with category='release_notes': the top hit is v4.4.0 Detailed Release "
            "Notes 'Migration & Action Required' (130.59: 'No schema change required when "
            "upgrading from any v4 version', plus license and configuration actions), in a "
            "0.14-point near-tie with What's New in v4 'Migration guides' (130.45), a V3-to-V4 "
            "link list. The order has flipped before (#567), so Step 1b selects the section by "
            "title and section name and names no rank. Quoted at two sites: the step and the "
            "routing negative's owner clause",
        "server": "1.37.29", "docs_index": "2026-10-13 23:20 UTC", "measured": "2026-10-13",
    },
    # Executed 2026-09-28 on server 1.37.15 (docs index 2026-09-28 23:38 UTC) for #222: the
    # citation for Step 1b's migration tools, named by the V4 version doing the migration.
    # Re-measured for #567 on server 1.37.29, docs index 2026-10-13 23:20 UTC, 2026-10-13, at the
    # default max_results: 'Migration guides' 105.75, 'Command-line Tools & SDKs' 93.50,
    # 'Infrastructure & tooling' 72.58. The citation carries its own read-past clause.
    ("search_docs", "sz_dbtool upgrade sz_dbupgrade sz_configupgrade replaced 4.4.0 native command-line tools",
     "release_notes"): {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Command-line Tools & SDKs",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT, with category='release_notes': the top hit is "
            "What's New in v4 'Migration guides', a V3-to-V4 link list; the set carries v4.4.0 "
            "Detailed Release Notes 'Command-line Tools & SDKs' with the v4.0 - v4.3 | v4.4.0 and "
            "later table (sz_dbupgrade -> sz_dbtool upgrade; sz_configupgrade -> sz_configtool, "
            "configuration upgrades folded in) and What's New in v4 'Infrastructure & tooling' with "
            "the same table. It is a citation, not a query the guide runs, and it says to read "
            "past the first hit to 'Command-line Tools & SDKs'",
        "server": "1.37.29", "docs_index": "2026-10-13 23:20 UTC", "measured": "2026-10-13",
    },
    ("search_docs", "homebrew-senzingsdk preview release unsupported tap install cask", None): {
        "band": "ON TARGET",
        "sections": ("Preview Release — Unsupported",),
        "returned":
            "ON TARGET: the top hit is senzing/homebrew-senzingsdk section 'homebrew-senzingsdk', "
            "the 'Preview Release — Unsupported' warning ('provided as-is with no warranty and is "
            "not supported')",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    ("search_docs", "brew outdated brew info senzingsdk installed version check", None): {
        "band": "OFF TARGET BY DESIGN",
        "sections": (),
        "returned":
            "OFF TARGET BY DESIGN — the macOS check-command negative's evidence: the corpus serves "
            "the tap README's install, upgrade and uninstall sections, its changelog and the macOS "
            "quickstart for it, and no brew outdated or brew info usage",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    ("search_docs", "scoop status scoop info senzingsdk installed version check", None): {
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
    # type/name check in Module 5 Phase 1 Step 6. It backs the "keep" option's cost.
    ("search_docs", "RECORD_TYPE PERSON ORGANIZATION prevent records of different types from resolving",
     "data_mapping"): {
        "band": "ON TARGET",
        "sections": ("Feature: RECORD_TYPE",),
        "returned":
            "ON TARGET. #1 is Senzing Entity Specification 'Feature: RECORD_TYPE' (74.7), whose "
            "guidance column reads 'Prevents records of different types from resolving' and "
            "'Use standardized kinds (PERSON, ORGANIZATION)'. #2 is 'What features to map' (31.6), "
            "whose RECORD_TYPE row reads 'Include when known to prevent cross-type resolution'",
        "server": "1.37.14", "docs_index": "2026-09-28 03:23 UTC", "measured": "2026-09-28",
    },
    # "organization name suffix tokens LLC LTD INC person or organization name classification"
    # was listed here as EMPTY OF A SUFFIX LIST (server 1.37.27, docs index 2026-10-11 18:43 UTC,
    # 2026-10-12) and is gone: it backed the suffix-list label's "No MCP route serves one", which
    # #590 retracted. The query still returns no list (re-run on server 1.38.1, docs index
    # 2026-10-14 15:57 UTC, 2026-10-14), but it was the wrong route: `mapping_workflow` step 2's
    # inline SENZING MAPPING REFERENCE carries "Corporate suffix tokens signal ORG", and the label
    # now cites that. Left as a comment rather than deleted, so the phrasing is not reintroduced
    # as the owner check for a suffix list.

    # ---------------------------------------------------------------------------------
    # Executed 2026-09-26 on server 1.37.13 (docs index 2026-09-24 18:45 UTC) for #160, the
    # match-key tokenizing rule in Phase D step 2 and Module 5's no-dashes domain line. The
    # same phrasing is the one the issue's refinement recorded.
    # Re-executed for #513 on server 1.37.27, docs index 2026-10-11 18:43 UTC, 2026-10-12, at the
    # default max_results: the same order. 'Feature: REL_ANCHOR' is fourth, and a target below
    # rank 3 is not a route (INV-291), so it is no longer in `sections` and no site cites this
    # query for it. The dash rule's sites point at the relationship-key route below instead.
    ("search_docs", "MATCH_KEY disclosed relationship REL_POINTER role in match key", None): {
        "band": "ON TARGET",
        "sections": ("MATCH_KEY / WHY_KEY Direction Notation for Disclosed Relationships",),
        "returned":
            "ON TARGET. The top hit is the Senzing MCP server article 'MATCH_KEY / WHY_KEY "
            "Direction Notation for Disclosed Relationships', defining the (ROLE:), (:ROLE) and "
            "(ROLE:ROLE) forms; its source is local:// and it is cited by title. Then the Entity "
            "Specification's 'Feature: REL_POINTER' and 'Disclosed relationship mapping guidance', "
            "and only then 'Feature: REL_ANCHOR', which carries the no-dashes rule: fourth, so "
            "this query is not that rule's route. Used at one call site, Phase D step 2, for the "
            "article",
        "server": "1.37.27", "docs_index": "2026-10-11 18:43 UTC", "measured": "2026-10-12",
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
    ("search_docs", "resolved entity is out of sync expected got concurrent loading SQLite lock", None): {
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
    # Re-executed for #600 at the default max_results: the same two first. Module 5 Phase 1 Step
    # 3 states it; Phase 2's step-3 rejection note now reaches *Feature: NAME* by pointing at
    # step 11's NAME_FULL route, which returns that section first (INV-300).
    ("search_docs", "entity specification attribute names feature tables NAME_ORG ADDR_LINE1 PHONE_NUMBER",
     "data_mapping"): {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Name > Feature: NAME", "Feature: NAME",
                     "Entities, features and attributes"),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT. The top hit is Senzing Entity Specification "
            "'Entities, features and attributes', the definitions of entity, feature and "
            "attribute. The second is the same document's 'Name > Feature: NAME' section, which "
            "carries the load-bearing sentence -- 'do not mix NAME_ORG with parsed person fields "
            "IN THE SAME OBJECT' -- plus the matching negative example, and its attribute table. "
            "Then 'Mapping identifiers'. "
            "NOTE: the excerpts render attribute names BACKTICKED (`NAME_ORG`), while the same "
            "tables in the document `download_resource` serves render them as PLAIN TEXT; that "
            "divergence is its own finding, in `applicability-and-attribute-catalog-are-authored-"
            "by-hand-and-fail-silently`.",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # ---------------------------------------------------------------------------------
    # Executed 2026-08-23 on server 1.33.0 (docs index 2026-08-20 17:33 UTC), for
    # `specs/search-docs-instructions-omit-the-required-query-parameter.md`: `query` is
    # `search_docs`' ONLY required parameter, so nine shipped references passing a bare
    # `category=` named a call a schema-respecting client cannot construct. Each query below
    # was chosen by executing it and reading the result, not by paraphrasing the destination.
# Re-executed for #417 (stamp above VERIFIED_QUERIES): every one still returns its recorded
# section at rank 1, except that the REL_ANCHOR_KEY query's first two sections swapped places.
    ("search_docs", "community wrapper not the official SDK package registry", "anti_patterns"): {
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
    # Re-executed for #513 on server 1.37.27, docs index 2026-10-11 18:43 UTC, 2026-10-12, at the
    # default max_results: the same top three, with two FAQs carrying a higher relevance_score
    # returned after them (the category boosts rather than filters). Phase 1 Step 6's retype
    # rule now reaches this route by pointing at Module 5 step 11, its canonical statement.
    # Re-executed for #600 at the default max_results: the same top three. Module 4 Step 2 and
    # Module 5 Phase 1 Step 5a restated it with older stamps; both now point at step 11.
    ("search_docs", "NAME_FULL NAME_ORG parsed person name single field", "data_mapping"): {
        "band": "ON TARGET",
        "sections": ("Name > Feature: NAME", "Feature: NAME"),
        "returned":
            "ON TARGET and #1: Senzing Entity Specification -> 'Name > Feature: NAME', carrying "
            "both quoted strings verbatim -- NAME_FULL as 'Single-field name when type (person vs "
            "org) is unknown or only a full name is provided', and the Rules line 'Prefer parsed "
            "person names ... use NAME_FULL only when the type is unknown or only a single field "
            "exists'. Then 'Entities, features and attributes' and 'Identifiers > Feature: "
            "LEI_NUMBER'; an FAQ with a higher relevance_score is returned after them. Stated once, "
            "at Module 5 step 11; every other site points there",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # Re-executed for #513 on server 1.37.27, docs index 2026-10-11 18:43 UTC, 2026-10-12, at the
    # default max_results: the same top three in the same order. The 2026-10-04 record called it
    # ON TARGET, but every site relies on 'Feature: REL_ANCHOR' (the REL_ANCHOR_KEY row, the
    # no-dashes rule), which is third, so its band is the read-past one (INV-291). Module 5 step
    # 11 states the route once; Module 4, Module 5's later step 11 lines and Phase D point at it.
    ("search_docs", "REL_ANCHOR_KEY REL_POINTER disclosed relationship keys", "data_mapping"): {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Disclosed relationship mapping guidance", "Feature: REL_POINTER",
                     "Feature: REL_ANCHOR"),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT: Senzing Entity Specification -> 'Feature: "
            "REL_POINTER' first, then 'Disclosed relationship mapping guidance', then 'Feature: "
            "REL_ANCHOR', which carries the REL_ANCHOR_KEY row's bare example value 1001, the "
            "domain as 'a code (without dashes)' and the rule 'Use a domain code without dashes to "
            "avoid confusion in downstream match key parsing.' The MCP server's direction-notation "
            "article is fourth. Together the three carry the string-valued JSON examples "
            "(\"ORG1001\", \"ACME-1001\") AND the bare 1001 -- both halves of the "
            "does-not-mandate-a-type claim -- and the no-dashes rule. The canonical site says to "
            "read past the first hit",
        "server": "1.37.27", "docs_index": "2026-10-11 18:43 UTC", "measured": "2026-10-12",
    },
    ("search_docs", "usage type distinguishes multiple instances payload optional attributes", "data_mapping"): {
        "band": "ON TARGET",
        "sections": ("Usage types and payload (optional attributes)",),
        "returned":
            "ON TARGET and #1: Senzing Entity Specification -> 'Usage types and payload (optional "
            "attributes)', carrying the quoted definition verbatim: 'A short label that "
            "distinguishes multiple instances of the same feature on one entity'. Then 'Payload "
            "attributes (optional)' and 'Mapping usage types' (re-executed for #600, the same "
            "three)",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # Re-executed for #440 on the same index (1.37.19, docs index 2026-10-02 18:46 UTC,
    # 2026-10-04): same top three, so the stamp is not re-dated. Phase 1 Step 6's sentence was
    # corrected to match the specification and its prose stamp re-dated (see the NOTE).
    ("search_docs", "Identifiers NATIONAL_ID PASSPORT TAX_ID TRUSTED_ID feature group", "data_mapping"): {
        "band": "ON TARGET",
        "sections": ("Identifiers > Feature: TAX_ID", "Identifiers > Feature: NATIONAL_ID"),
        "returned":
            "ON TARGET: Senzing Entity Specification -> 'Identifiers > Feature: TAX_ID', then "
            "'Identifiers > Feature: NATIONAL_ID' and 'Mapping identifiers'. These are members OF "
            "the Identifiers section, which is what the call site's grouping claim rests on -- "
            "the section heading itself is not a separately indexed chunk, so the members are the "
            "evidence. NOTE: the set has no TRUSTED_ID section, and the specification files it as "
            "'Trusted ID > Feature: TRUSTED_ID', not under Identifiers (checked in the same "
            "measurement). The query string still names TRUSTED_ID; the site does not count it "
            "as a member. #440 rewrote the site to name Identifiers members non-exhaustively "
            "('such as' NATIONAL_ID, PASSPORT, TAX_ID and LEI_NUMBER), to say TRUSTED_ID is "
            "filed under its own Trusted ID heading, and to re-date its prose stamp",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    ("search_docs", "ACCOUNT_NUMBER ACCOUNT_DOMAIN account feature", "data_mapping"): {
        "band": "ON TARGET",
        "sections": ("Feature: ACCOUNT",),
        "returned":
            "ON TARGET and #1: Senzing Entity Specification -> 'Identifiers > Feature: ACCOUNT', "
            "carrying 'Domain/system for the account number' verbatim -- the definition the call "
            "site quotes",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    ("search_docs", "recommended JSON schema FEATURES list multiple values sub-list", "data_mapping"): {
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
    ("search_docs", "payload attribute versus registered feature attribute record root extracted as feature precedence",
     "data_mapping"): {
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
    # Re-executed for #600 at the default max_results: the same four, in the same order. It was
    # stated in full at seven sites, which had drifted apart on `version="current"` and on their
    # stamps. Module 6 Phase A's "Anti-pattern check" states it now; the other six point there and
    # each keeps the section it relies on (INV-300).
    ("search_docs", "loading", "anti_patterns"): {
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
            "documents. The stating site says to read past the first hit",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # The six below were measured on server 1.32.9, docs index 2026-08-11 20:52 UTC, on
    # 2026-08-12 (fdbc922): the stamp the module-level VERIFIED_ON recorded for them. #383
    # re-executed two of them; #417 re-executed the other four, with the same sections returned.
    ("search_docs", "entity resolution business value", None): {
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
    ("search_docs", "what features to map", "data_mapping"): {
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
    ("search_docs", "Senzing engine configuration PostgreSQL connection", None): {
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
    ("search_docs", "PostgreSQL schema DDL initialization", "anti_patterns"): {
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
    ("search_docs", "CORD datasets: names, contents, and availability for entity resolution scenarios", None): {
        "band": "ON TARGET",
        "sections": ("What Is a CORD?",),
        "returned":
            "ON TARGET: Collections Of Relatable Data (CORDs) -> 'What Is a CORD?' (the section "
            "name renders in bold); the same page's 'Moscow CORD' section is in the set below it",
        "server": "1.37.19", "docs_index": "2026-10-02 18:46 UTC", "measured": "2026-10-04",
    },
    ("search_docs", "temporary evaluation license for a dataset larger than the default limit", None): {
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
    ("search_docs", "hardware sizing capacity planning", None): {
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
    ("search_docs", "upgrade Senzing SDK 4.3 to 4.4 procedure", None): {
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
    ("search_docs", "evaluation license record limit how many records without a license", None): {
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
    # Re-executed for #513 on server 1.37.27, docs index 2026-10-11 18:43 UTC, 2026-10-12, at the
    # default max_results: the same three Guide rows first. Phase 3's encoding line now reaches
    # this route by pointing at Module 5's SKILL.md instead of passing the bare term with the
    # filter, whose call the guard had matched to the bare term's OFF TARGET record below.
    ("search_docs", "UTF-8 encoding non-Latin character support multi-language data quality", "globalization"): {
        "band": "ON TARGET",
        "sections": ("What languages does Senzing support?",),
        "returned":
            "ON TARGET with category='globalization': Senzing Globalization Guide -> 'What "
            "languages does Senzing support?', which states the UTF-8 and cross-script answer "
            "outright, then 'Advanced personal name comparisons > Supported cultural groups' and "
            "'... > Additional Cultural Support'. ⚠️ Rows of other categories (a Rust FFI guide's "
            "encoding notes, a data-providers page) carry a HIGHER relevance_score but are "
            "returned AFTER the on-topic rows -- the filter promotes rather than restricts, so "
            "never rank this set by score",
        "server": "1.37.27", "docs_index": "2026-10-11 18:43 UTC", "measured": "2026-10-12",
    },
    # Re-executed for #600 at the default max_results: the practice now sits in the top hit's own
    # section, 'Address matching examples', and 'CJK+English cross-script matching' (organization
    # names) is second, so the record names the first and step 11's site names it too.
    ("search_docs", "data quality practices multi-language non-Latin", "globalization"): {
        "band": "ON TARGET",
        "sections": ("Address matching examples",),
        "returned":
            "ON TARGET with category='globalization': Globalization Guide -> 'Address matching "
            "examples', whose prose carries the practice — native-to-native beats "
            "native-to-Romanized, and for non-CJK cross-script, Romanize via an address-hygiene "
            "product and supply both forms. Then 'CJK+English cross-script matching' (organization "
            "names) and 'Enhanced address comparisons'; repo docs/best-practices.md files follow "
            "with a higher relevance_score",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # Re-executed for #149 on server 1.37.13, docs index 2026-09-24 18:45 UTC, 2026-09-26, at
    # max_results=6 and at the default. The 2026-08-13 record above this entry said its best
    # Guide hit was a bare title with no prose; the rebuilt index returns Guide sections with
    # prose, so that record was replaced rather than re-dated. ⚠️ Record the PROPERTY, not the
    # ranks: a rank order is what went stale here, and the next rebuild can move it again.
    # Keyed with no category since #513, the form its sites quote. Phase 3's encoding line passed
    # the same term WITH category='globalization' and was matched to this negative record, so its
    # positive use was never checked. Re-asked for #513 both ways on server 1.37.27, docs index
    # 2026-10-11 18:43 UTC, 2026-10-12: each returns Guide sections plus the Global* matches, and
    # neither returns the 'What languages' section. Not re-dated, because Module 5's prose stamp
    # for this paragraph vouches for the 2026-09-26 measurement.
    ("search_docs", "globalization", None): {
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
    ("search_docs", "multi-language data quality best practices", None): {
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
    ("search_docs", "szBuildVersion.json build version file location", None): {
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
    ("search_docs", "NEED_REEVALUATION how entity final state", None): {
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
    ("search_docs", "reevaluate entity when to call reevaluation needed", None): {
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
    ("search_docs", "redo", "anti_patterns"): {
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
    ("search_docs", "health check", None): {
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
    ("search_docs", "Data Source Records DSRs Explained same DATA_SOURCE RECORD_ID replaces", None): {
        "band": "ON TARGET BELOW AN ADJACENT TOP HIT",
        "sections": ("Uniquely Identifying Records in Senzing",),
        "returned":
            "ON TARGET BELOW AN ADJACENT TOP HIT: the top three hits are sections of 'Data Source "
            "Records (DSRs) Explained'. The top hit is 'Important Nuances > Expanding Data "
            "Sources'; the second is 'Uniquely Identifying Records in Senzing', which says the "
            "data source code plus the record ID is a record's unique key and that a record sent "
            "with a key that matches a loaded record replaces it; the third is 'Important Nuances "
            "> Event Sources' (re-executed for #600: 'Overview' is third now). The rest of the set "
            "is register_data_source code examples. The site says to read past the first hit, and "
            "Module 7's record-identity rule points at it",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # ---------------------------------------------------------------------------------
    # The two below were executed for #513 on server 1.37.27, docs index 2026-10-11 18:43 UTC,
    # 2026-10-12, at the default max_results. Each replaces a route that named no query: Module 2
    # Step 3's "call search_docs with category='anti_patterns'" (a call a schema-respecting
    # client cannot construct, INV-212), and Module 2 Step 8's SENZ2027 FAQ citation, stamped
    # "search_docs, verified 2026-07-30". Module 2's Agent Behavior list and Module 3 Step 1a
    # point at these two sites rather than restating them (INV-300).
    ("search_docs", "install Senzing SDK installation pitfalls", "anti_patterns"): {
        "band": "ON TARGET",
        "sections": ("Senzing Anti-Patterns: Installing in Sandboxed or Restricted-Egress "
                     "Environments",),
        "returned":
            "ON TARGET, with category='anti_patterns' (four results): the top hit is the MCP "
            "server article 'Senzing Anti-Patterns: Installing in Sandboxed or Restricted-Egress "
            "Environments' (unreachable package repositories and the MCP-hosted direct "
            "downloads, PyPI bindings are not the runtime, vendor buckets, 'Do Not Hand-Code "
            "Install Commands From Training Data', and the macOS SUPPORTPATH template trap). Then "
            "'Database Initialization and Container Setup', 'Ecosystem and Dependencies' and "
            "'Operations and Runtime'. The query names no platform, so it is one call on every "
            "platform; the site says to read every article it returns",
        "server": "1.37.27", "docs_index": "2026-10-11 18:43 UTC", "measured": "2026-10-12",
    },
    ("search_docs", "SENZ2027 Plugin initialization error GNR data files failed to load", None): {
        "band": "ON TARGET",
        "sections": ("I get SENZ2027 Plugin initialization error GNR data files failed to load",),
        "returned":
            "ON TARGET: the top hit is the FAQ 'I get SENZ2027 Plugin initialization error GNR "
            "data files failed to load' ('You are missing the senzingsdk-runtime data directory. "
            "The libraries are present but the GNR data files (in resources/data/) are not "
            "deployed'), from the v4 hardware and software requirements page. The rest is "
            "recipes and code-snippet loaders and the engine error-code entry for SENZ2027 "
            "(EAS_ERR_PLUGIN_INIT). explain_error_code('SENZ2027') returns only generic "
            "resolution steps, which is why Module 2 cites the FAQ. The #513 issue expected no "
            "route to reach this FAQ at rank 3 or better; this one does, at rank 1",
        "server": "1.37.27", "docs_index": "2026-10-11 18:43 UTC", "measured": "2026-10-12",
    },
    # ---------------------------------------------------------------------------------
    # The six below were executed for #600 on server 1.38.2, docs index 2026-10-14 20:27 UTC,
    # 2026-10-14, at each tool's default max_results. The two `search_docs` routes replace
    # citations that named the tool and no query (#513 item 4's class): the ground rules' Truth
    # Set spelling and the visualization contract's longest feature code.
    ("search_docs", "truth set demo data customers reference watchlist quickstart", None): {
        "band": "ON TARGET",
        "sections": ("Truth Set Setup",),
        "returned":
            "ON TARGET: the top hit is the documentation page titled 'Truth Set Setup', section "
            "'Step 1: Install Senzing and load the truth set data' ('loading the truth set data "
            "files'); the same page's 'Truth Set Setup' section ('loading the Senzing truth set "
            "demo data') is third, after the senzing/truth-sets README. 'truth set' is two words "
            "throughout. The phrasing is the one tests/test_truth_set_spelling.py records",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    ("search_docs", "Feature: REGISTRATION_COUNTRY organizations", "data_mapping"): {
        "band": "ON TARGET",
        "sections": ("Feature: REGISTRATION_COUNTRY (organizations)",),
        "returned":
            "ON TARGET with category='data_mapping': the top hit is Senzing Entity Specification "
            "'Physical and other characteristics > Feature: REGISTRATION_COUNTRY (organizations)', "
            "whose attribute is REGISTRATION_COUNTRY; the second is the 'What features to map' "
            "table rows from ACCOUNT to REL_ANCHOR, which list REGISTRATION_COUNTRY beside "
            "REGISTRATION_DATE and GROUP_ASSOCIATION",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # `find_examples` (#600). Its search returns one example per repository, official
    # repositories first, so the set is bounded by the repositories the query matches and a
    # repository's place in it is that order, not a relevance rank. A route is a query whose
    # target repository and file come first; the band set is the same.
    ("find_examples", "Unable to get settings", None): {
        "band": "ON TARGET",
        "sections": ("java/snippets/information/GetRepositoryInfo.java",),
        "returned":
            "ON TARGET: the top hit is senzing/code-snippets-v4 -> "
            "java/snippets/information/GetRepositoryInfo.java, which prints 'Unable to get "
            "settings.' and throws when System.getenv(\"SENZING_ENGINE_CONFIGURATION_JSON\") is "
            "null. With language='csharp' the top hit is the C# twin, "
            "csharp/snippets/information/GetRepositoryInfo/Program.cs (ArgumentException). "
            "Module 3 Step 1a states it; Module 2's environment-script notes point there",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # Historical evidence in Module 6 Phase A (`.ts` is indexed), re-run rather than trusted.
    ("find_examples", "add record engine initialization", "typescript"): {
        "band": "ON TARGET",
        "sections": ("bindings/node/ts/options.ts",),
        "returned":
            "ON TARGET for the claim it backs, that .ts files are indexed: the top hit is "
            "brianmacy/sz-rust-sdk-configtool -> bindings/node/ts/options.ts, then brianmacy/"
            "sz-napi -> code-snippets/initialization/engine-priming/index.ts (the file the 1.33.0 "
            "measurement named first) and brianmacy/sz-napi-docs -> SzExportIterator/addRecord.ts",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # The two below are the evidence slots of Module 6 Phase C's orchestrator MCP-NEGATIVE marker.
    ("find_examples", "multi-source", None): {
        "band": "EMPTY OF A MULTI-SOURCE ORCHESTRATOR",
        "sections": (),
        "returned":
            "EMPTY OF A MULTI-SOURCE ORCHESTRATOR: without a language it returns two examples, the "
            "CHANGELOG.md files of senzing/senzing-bootcamp-claude-plugin and senzing/"
            "senzing-bootcamp-kiro-power; with language='java' it returns examples: [] and a hint "
            "to try single SDK method names, generate_scaffold or search_docs",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    ("find_examples", "orchestrator load multiple data sources", None): {
        "band": "EMPTY OF A MULTI-SOURCE ORCHESTRATOR",
        "sections": (),
        "returned":
            "EMPTY OF A MULTI-SOURCE ORCHESTRATOR: code-snippets-v4 "
            "java/snippets/configuration/RegisterDataSources.java first, then single-source "
            "loaders (code-snippets-v3 Add10KQueue.py), CHANGELOGs, queue consumers and redoers, "
            "a Spark tutorial and config-tool data-source code, one per repository; with "
            "language='python' or 'java' the same kinds. No example loads several sources in "
            "order with per-source isolation",
        "server": "1.38.2", "docs_index": "2026-10-14 20:27 UTC", "measured": "2026-10-14",
    },
    # Three `find_examples` phrasings are gone, removed by #600 rather than recorded: Module 7's
    # integration patterns prescribed 'REST API' and 'batch report', and Module 4's XML note
    # 'XML data loading'. Measured on server 1.38.2, 2026-10-14, at the default: 'REST API' and
    # 'batch report' return code-snippets-v4's SnippetRunner and test_snippets.py first and the one
    # REST example (brianmacy/sz_search_flask-v4) about thirtieth in repository order; 'XML data
    # loading' returns JSON loaders and no XML parsing. Left as a comment so they are not
    # reintroduced; the integration line now routes to generate_scaffold and reporting_guide.
    # "entity resolution quality evaluation" was listed here as OFF TARGET on 2026-08-12 and is
    # gone: Module 7 Step 3b no longer prescribes it. It returned the Buyer's Guide's
    # vendor-selection steps rather than precision/recall material, and
    # step3b-quality-lookup-misroutes-and-omits-the-evidence-requirement replaced it with
    # reporting_guide(topic='evaluation'), the tool that owns the material. Left as a comment
    # rather than deleted, so the phrasing is not helpfully reintroduced.
}

#: Routes whose shipped sentence still carries a dated stamp of its own (#600). The record above
#: is the stamp, and a prose copy is a second one that goes stale on the next index rebuild, so
#: this list only shrinks: a site that is edited drops its stamp and its key leaves the list, and
#: a route not listed here may not gain one. Some of these stamps vouch for a second claim beside
#: the route (Step 14's stamp, which its own test asserts; a historical server observation), which
#: is why they were not dropped wholesale.
STAMPED_IN_PROSE = (
    ("find_examples", "add record engine initialization", "typescript"),
    ("search_docs", "ACCOUNT_NUMBER ACCOUNT_DOMAIN account feature", "data_mapping"),
    ("search_docs", "Identifiers NATIONAL_ID PASSPORT TAX_ID TRUSTED_ID feature group",
     "data_mapping"),
    ("search_docs", "MATCH_KEY disclosed relationship REL_POINTER role in match key", None),
    ("search_docs",
     "RECORD_TYPE PERSON ORGANIZATION prevent records of different types from resolving",
     "data_mapping"),
    ("search_docs", "SENZ2027 Plugin initialization error GNR data files failed to load", None),
    ("search_docs", "entity resolution business value", None),
    ("search_docs", "recommended JSON schema FEATURES list multiple values sub-list",
     "data_mapping"),
    ("search_docs",
     "sz_dbtool upgrade sz_dbupgrade sz_configupgrade replaced 4.4.0 native command-line tools",
     "release_notes"),
)

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
#: The `category=` that follows the query, in either quote style and across a line wrap, is
#: captured too (#513), because a record is keyed on it. `find_examples(query=` is read the same
#: way, with the `language=` that follows it (#600): it is the other retrieval route a step
#: prescribes by phrasing.
QUERY_LITERAL = re.compile(
    r"""\b(?P<tool>search_docs|find_examples)\(query=(?:'(?P<q1>[^']*)'|"(?P<q2>[^"]*)")"""
    r"""(?:\s*,\s*(?P<arg>category|language)=(?:'(?P<a1>[^']*)'|"(?P<a2>[^"]*)"))?""")
#: The argument each tool's third key member is read from.
KEY_ARG = {"search_docs": "category", "find_examples": "language"}
HEADING = re.compile(r"(?m)^#{2,4} ")
#: An `MCP-NEGATIVE` marker. Its owner clause names a route as evidence, so a route quoted there
#: is not a second statement of it (#600).
#: (Split so that the marker scanner, which reads this file too, does not take it for one.)
NEGATIVE_MARKER = re.compile(r"(?s)<!--\s*MCP-NEGATIVE" r":.*?-->")
#: A dated measurement written into prose: an MCP server version (1.x) or a docs index date.
PROSE_STAMP = re.compile(
    r"(?i)\b(?:server|on)\s+\**1\.\d+\.\d+\b|\bdocs index(?:ed)?\s+\d{4}-\d{2}-\d{2}")

#: A `category=` argument with a value, and a `query=` argument, anywhere in a sentence (#513).
#: The value is required so that prose about the parameter ("a bare `category=` is a call a
#: client cannot construct") is not read as a call.
CATEGORY_ARG = re.compile(r"""\bcategory\s*=\s*['"]""")
QUERY_ARG = re.compile(r"\bquery\s*=")
#: Where a sentence ends: a terminator before whitespace, a blank line, or a new list item.
SENTENCE_BREAK = re.compile(r"[.!?](?=\s)|\n[ \t]*\n|\n[ \t]*(?:[-*+]|\d+[.)])[ \t]")
#: The exemption `test_search_docs_calls_pass_a_query.py` reviews and caps: prose that names a
#: category to describe what it indexes. Honored here on the same terms, so the two guards cannot
#: disagree about one site.
CATEGORY_PROSE_MARKER = "SEARCH-DOCS-CATEGORY-PROSE:"
MARKER_LOOKBEHIND_LINES = 4

#: A site that points at a route stated elsewhere (#513, INV-300):
#: "… route … is stated once, in `<file>` → "<heading or bold lead>"". Read on text with
#: emphasis removed and wraps collapsed, so a pointer wrapped across lines is still one pointer.
ROUTE_POINTER = re.compile(
    r"\broute\b[^.;]{0,160}?\bis stated once\b[^`]{0,80}?`(?P<path>[^`\s]+\.md)`"
    r"\s*→\s*\"(?P<anchor>[^\"]+)\"")


def call_text(key):
    """How a record key reads as a call, for messages."""
    tool, query, value = key
    if value is None:
        return f"{tool}(query='{query}')"
    return f"{tool}(query='{query}', {KEY_ARG[tool]}='{value}')"


def shipped_markdown():
    return sorted(SKILLS.rglob("*.md"))


def sections(text):
    """(start, end) spans between Markdown headings, so 'the same step' is well-defined."""
    bounds = [m.start() for m in HEADING.finditer(text)] + [len(text)]
    if not bounds or bounds[0] != 0:
        bounds = [0] + bounds
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


def literal_key(match):
    """The (tool, query, category-or-language) key of one QUERY_LITERAL match."""
    tool = match.group("tool")
    literal = match.group("q1") if match.group("q1") is not None else match.group("q2")
    value = match.group("a1") if match.group("a1") is not None else match.group("a2")
    if match.group("arg") != KEY_ARG[tool]:
        value = None
    # Whitespace-collapsed: a literal wrapped across source lines is still one
    # query. A line-based scan misses these entirely — three of the eight
    # prescribed queries in this corpus are wrapped, and all three were invisible
    # to the first version of this guard.
    return tool, re.sub(r"\s+", " ", literal).strip(), value


def queries_in(label, text):
    """(label, key, enclosing section text) for every query literal in a document.

    The key's third member is None for a call that passes no category or language.
    """
    found = []
    spans = sections(text)
    for match in QUERY_LITERAL.finditer(text):
        section = next(
            (text[a:b] for a, b in spans if a <= match.start() < b), text
        )
        found.append((label, literal_key(match), section))
    return found


def statements_in(label, text, allowlist):
    """(label, key, section start, sentence) for each positive-band route a document states.

    A literal inside an `MCP-NEGATIVE` marker is evidence for the marker, not a statement, and
    a negative-band literal is a quoted miss, so neither counts (#600).
    """
    markers = [m.span() for m in NEGATIVE_MARKER.finditer(text)]
    starts = [a for a, _b in sections(text)]
    breaks = sorted({0, len(text)} | {
        m.end() if m.group(0)[0] in ".!?" else m.start() for m in SENTENCE_BREAK.finditer(text)})
    found = []
    for match in QUERY_LITERAL.finditer(text):
        key = literal_key(match)
        record = allowlist.get(key)
        if (not isinstance(record, dict) or record.get("band") not in POSITIVE_BANDS
                or any(a <= match.start() < b for a, b in markers)):
            continue
        start = max(b for b in breaks if b <= match.start())
        end = min(b for b in breaks if b > match.start())
        sentence = NEGATIVE_MARKER.sub("", text[start:end])
        found.append((label, key, max(a for a in starts if a <= match.start()), sentence))
    return found


def restated_routes(statements):
    """Routes stated in full under more than one heading (INV-300, #600)."""
    where = {}
    for label, key, section, _sentence in statements:
        where.setdefault(key, set()).add((str(label), section))
    return [f"{call_text(key)} is stated in full at {len(places)} places "
            f"({', '.join(sorted({p for p, _s in places}))}): keep one and point the others at "
            f"it in the form \"stated once, in `<file>` → \"<heading or bold lead>\"\" "
            f"(INV-291, INV-300)"
            for key, places in where.items() if len(places) > 1]


def stamp_problems(statements, grandfathered):
    """Prose stamps beside a recorded route, against the shrink-only list (#600).

    The record is the route's one stamp. A site whose sentence carries its own server version
    or docs index date is a second copy that goes stale on the next rebuild, so only a key in
    `grandfathered` may still carry one, and a key there that no longer does must leave it.
    """
    stamped = {key for _l, key, _s, sentence in statements if PROSE_STAMP.search(sentence)}
    problems = [f"{call_text(key)}: a site carries a dated stamp of its own; the record in "
                f"VERIFIED_QUERIES is the route's one stamp, so drop it from the prose (INV-291)"
                for key in sorted(stamped - set(grandfathered), key=str)]
    problems += [f"{call_text(key)} no longer carries a prose stamp: remove it from "
                 f"STAMPED_IN_PROSE, which only shrinks (INV-291)"
                 for key in sorted(set(grandfathered) - stamped, key=str)]
    return problems


def shipped_statements():
    found = []
    for path in shipped_markdown():
        found.extend(statements_in(path.relative_to(REPO_ROOT), path.read_text(encoding="utf-8"),
                                   VERIFIED_QUERIES))
    return found


def prescribed_queries():
    """(path, key, enclosing section text) for every prescribed query literal."""
    found = []
    for path in shipped_markdown():
        text = path.read_text(encoding="utf-8")
        found.extend(queries_in(path.relative_to(REPO_ROOT), text))
    return found


def unaccounted(found, allowlist):
    """Query sites with no allowlist entry and no re-query rule in their section."""
    return [
        f"{label}: {call_text(key)}"
        for label, key, section in found
        if key not in allowlist and not REQUERY_RULE.search(section)
    ]


def key_problems(key):
    """A VERIFIED_QUERIES key that is not a (tool, query, category-or-language-or-None) triple.

    #513 keyed records on (query, category); #600 added the tool, for `find_examples`.
    """
    if (isinstance(key, tuple) and len(key) == 3 and key[0] in KEY_ARG
            and isinstance(key[1], str) and key[1]
            and (key[2] is None or (isinstance(key[2], str) and key[2]))):
        return []
    return [f"VERIFIED_QUERIES key {key!r} is not a (tool, query, category or language or None) "
            f"triple, so a site cannot be matched to the call it makes (INV-291)"]


def bare_category_mentions(label, text):
    """Sentences that mention `search_docs`, pass a `category=` value and name no `query=`.

    `query` is the tool's only required parameter, so such a mention prescribes a call a
    schema-respecting client cannot construct, and names no vocabulary to re-run (INV-212).
    """
    breaks = [0]
    for match in SENTENCE_BREAK.finditer(text):
        breaks.append(match.end() if match.group(0)[0] in ".!?" else match.start())
    breaks.append(len(text))
    lines = text.split("\n")
    problems, seen = [], set()
    for match in re.finditer(r"search_docs", text):
        start = max(b for b in breaks if b <= match.start())
        end = min(b for b in breaks if b > match.start())
        if start in seen:
            continue
        seen.add(start)
        sentence = " ".join(text[start:end].split())
        if not CATEGORY_ARG.search(sentence) or QUERY_ARG.search(sentence):
            continue
        line_no = text.count("\n", 0, match.start()) + 1
        window = lines[max(0, line_no - 1 - MARKER_LOOKBEHIND_LINES):line_no]
        if any(CATEGORY_PROSE_MARKER in line for line in window):
            continue
        problems.append(f"{label}:{line_no}: a search_docs mention passes category= and names "
                        f"no query=: {sentence[:110]!r} (INV-212)")
    return problems


def pointer_text(text):
    """Text as the pointer regex reads it: no blockquote markers or emphasis, wraps collapsed."""
    text = re.sub(r"(?m)^\s*>\s?", "", text).replace("*", "")
    return re.sub(r"\s+", " ", text.replace("“", "\"").replace("”", "\""))


def route_pointers(label, text):
    """(label, path, anchor, enclosing section text) for every route pointer in a document."""
    found = []
    for a, b in sections(text):
        for match in ROUTE_POINTER.finditer(pointer_text(text[a:b])):
            found.append((label, match.group("path"), match.group("anchor"), text[a:b]))
    return found


def owner_section(text, anchor):
    """The heading section holding `anchor` as a heading or a bold lead, or None."""
    for match in re.finditer(r"(?m)^.*$", text):
        line = match.group(0)
        heading = re.match(r"#{1,6}\s+(.*)$", line)
        if heading:
            hit = heading.group(1).replace("*", "").replace("`", "").strip() == anchor
        else:
            hit = re.match(r"\s*(?:[-*+]\s+)?\*\*" + re.escape(anchor), line) is not None
        if hit:
            return next(text[a:b] for a, b in sections(text) if a <= match.start() < b)
    return None


def pointer_problems(pointers, allowlist, load):
    """Route pointers that land nowhere, on no measured route, or name none of its sections.

    `load(label, path)` returns the target's (label, text), or None when it does not resolve.
    """
    problems = []
    for label, path, anchor, site in pointers:
        where = f"{label}: the route pointer to `{path}` → \"{anchor}\""
        target = load(label, path)
        if target is None:
            problems.append(f"{where} names no shipped file (INV-291, INV-300)")
            continue
        target_label, target_text = target
        owner = owner_section(target_text, anchor)
        if owner is None:
            problems.append(f"{where} names no heading or bold lead in {target_label} "
                            f"(INV-291, INV-300)")
            continue
        records = [allowlist[key] for _l, key, _s in queries_in(target_label, owner)
                   if isinstance(allowlist.get(key), dict)
                   and allowlist[key].get("band") in POSITIVE_BANDS]
        if not records:
            problems.append(f"{where} lands on a section with no measured search_docs route "
                            f"(INV-291, INV-300)")
            continue
        names = [n for r in records for n in r.get("sections", ())]
        if not any(flat(name) in flat(site) for name in names):
            problems.append(f"{where} names none of the sections its route returns: "
                            f"{sorted(set(names))} (INV-291)")
    return problems


def shipped_pointers():
    found = []
    for path in shipped_markdown():
        found.extend(route_pointers(path.relative_to(REPO_ROOT),
                                    path.read_text(encoding="utf-8")))
    return found


def load_shipped(label, path):
    """Resolve a pointer's path against the pointing file's directory, as a Markdown link is."""
    target = (REPO_ROOT / label).parent / path
    try:
        target = target.resolve()
        target.relative_to(SKILLS.resolve())
    except ValueError:
        return None
    if not target.is_file():
        return None
    return target.relative_to(REPO_ROOT.resolve()), target.read_text(encoding="utf-8")


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


def record_problems(key, record):
    """Every way one VERIFIED_QUERIES value fails the INV-291 record (#383). Empty means sound."""
    where = f"VERIFIED_QUERIES[{key!r}]"
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
    for label, key, section in found:
        record = allowlist.get(key)
        if not isinstance(record, dict) or record.get("band") not in POSITIVE_BANDS:
            continue
        text = flat(section)
        if not any(flat(name) in text for name in record.get("sections", ())):
            problems.append(f"{label}: {call_text(key)} names none of "
                            f"{record.get('sections')} (INV-291)")
        if record["band"] == BELOW_TOP_HIT and not READ_PAST.search(text):
            problems.append(f"{label}: {call_text(key)} is {BELOW_TOP_HIT} and its "
                            f"section does not say to read past the first hit (INV-291)")
    return problems


class EveryPrescribedQueryIsAccountedFor(unittest.TestCase):
    def test_the_scan_finds_the_queries(self):
        found = prescribed_queries()
        self.assertGreaterEqual(len(found), 5, "the query scan came up empty or too small")

    def test_the_scan_sees_double_quoted_literals(self):
        quoted = {q for _p, (_t, q, _c), _s in prescribed_queries()} & {"redo", "health check"}
        self.assertEqual({"redo", "health check"}, quoted,
                         "QUERY_LITERAL no longer matches search_docs(query=\"…\") (INV-291)")

    def test_each_query_is_verified_or_carries_a_requery_rule(self):
        missing = unaccounted(prescribed_queries(), VERIFIED_QUERIES)
        self.assertEqual(
            [],
            missing,
            "A shipped step prescribes a search_docs or find_examples query that was never "
            "verified against the server and has no re-query rule in its section (INV-291). "
            "Retrieval is by phrasing, so an unexecuted phrasing can return anything — and a miss looks exactly like "
            "documentation that does not cover the topic. Verify it and add it to "
            "VERIFIED_QUERIES with its observed result, band and stamp, or pair it with a "
            "re-query instruction:\n  " + "\n  ".join(missing),
        )

    def test_the_allowlist_has_no_dead_entries(self):
        """An allowlist that outlives its queries starts exempting things by accident."""
        live = {key for _p, key, _s in prescribed_queries()}
        dead = sorted(set(VERIFIED_QUERIES) - live, key=str)
        self.assertEqual(
            [], dead,
            "VERIFIED_QUERIES lists phrasings no shipped file prescribes any more — remove "
            "them so the allowlist keeps meaning what it says: %s" % dead,
        )

    def test_every_allowlist_entry_is_a_stamped_banded_record(self):
        problems = [p for k, r in VERIFIED_QUERIES.items()
                    for p in key_problems(k) + record_problems(k, r)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_the_scan_reads_the_category_in_either_quote_style(self):
        """A category passed with double quotes keys its site as surely as one with single."""
        keys = {key for _p, key, _s in prescribed_queries()}
        self.assertIn(("search_docs", "redo", "anti_patterns"), keys,
                      "QUERY_LITERAL no longer reads category=\"…\" (#513)")
        self.assertIn(("search_docs", "loading", "anti_patterns"), keys)
        self.assertIn(("search_docs", "globalization", None), keys,
                      "a call with no category must key on None (#513)")

    def test_the_scan_reads_find_examples_and_its_language(self):
        """#600: `find_examples(query=` is a prescribed route too, keyed with its language."""
        keys = {key for _p, key, _s in prescribed_queries()}
        self.assertIn(("find_examples", "Unable to get settings", None), keys)
        self.assertIn(("find_examples", "add record engine initialization", "typescript"), keys,
                      "QUERY_LITERAL no longer reads find_examples' language= (#600)")

    def test_every_site_names_its_section_and_reads_past_an_adjacent_top_hit(self):
        problems = site_problems(prescribed_queries(), VERIFIED_QUERIES)
        self.assertEqual(
            [], problems,
            "An inline route's site must name the section its record says it returns, and a "
            "route whose target sits below an adjacent top hit must say to read past the first "
            "hit (INV-291):\n  " + "\n  ".join(problems))

    def test_no_mention_passes_a_category_without_a_query(self):
        problems = [p for path in shipped_markdown()
                    for p in bare_category_mentions(path.relative_to(REPO_ROOT),
                                                    path.read_text(encoding="utf-8"))]
        self.assertEqual(
            [], problems,
            "A shipped sentence tells the guide to call search_docs with a category and names no "
            "query (#513). `query` is the tool's only required parameter, so the call cannot be "
            "constructed, and a reader cannot re-run it. Name the measured query in the same "
            "sentence (INV-212, INV-291):\n  " + "\n  ".join(problems))


class EveryRoutePointerLandsOnItsRecord(unittest.TestCase):
    """#513: a route stated once is followed from each site that points at it (INV-300)."""

    def test_the_scan_finds_the_pointers(self):
        """Anti-vacuity: the sites #513 converted to pointers are all found."""
        labels = {str(label) for label, _p, _a, _s in shipped_pointers()}
        for name in ("phase3-test-load.md", "phaseD-validation.md",
                     "module-04-data-collection/SKILL.md", "phase1-verification.md",
                     "phase1-quality-assessment.md", "module-02-sdk-setup/SKILL.md",
                     # #600's consolidations.
                     "phaseA-build-loading.md", "module-06-data-processing/SKILL.md",
                     "phase1-query-visualize.md", "phase2-data-mapping.md"):
            with self.subTest(site=name):
                self.assertTrue(any(label.endswith(name) for label in labels),
                                f"no route pointer found in {name}; the pointer form moved and "
                                f"this guard is checking nothing there")

    def test_every_pointer_lands_on_a_measured_route_and_names_its_section(self):
        problems = pointer_problems(shipped_pointers(), VERIFIED_QUERIES, load_shipped)
        self.assertEqual(
            [], problems,
            "A site points at a route stated elsewhere, and the route does not hold for it: the "
            "pointer must land on a heading or bold lead whose section carries a measured "
            "search_docs route, and the pointing site must name a section that route returns "
            "(INV-291, INV-300):\n  " + "\n  ".join(problems))


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
        allowlist = {("search_docs", "what features to map", None): _good_record()}
        text = "## Step\n\nRun `search_docs(query='what features to map')`.\n"
        self.assert_rejected(site_problems(queries_in("fixture.md", text), allowlist),
                             "names none of")

    def test_a_below_top_hit_site_without_read_past_fails(self):
        allowlist = {("search_docs", "what features to map", None): _good_record(band=BELOW_TOP_HIT)}
        text = ("## Step\n\nRun `search_docs(query='what features to map')`; its *What "
                "features to map* section answers it.\n")
        self.assert_rejected(site_problems(queries_in("fixture.md", text), allowlist),
                             "read past the first hit")
        fixed = text.replace("answers it.", "answers it: read past the first hit.")
        self.assertEqual([], site_problems(queries_in("fixture.md", fixed), allowlist))


#: Module 5 Phase 3's encoding line before #513: the bare term WITH the globalization filter.
PRE_513_PHASE_3 = ("## Encoding\n\n- Non-Latin scripts: `search_docs(query=\"globalization\", "
                   "category=\"globalization\")`. For the sections, see this module's `SKILL.md` "
                   "→ \"Multi-language data\" (INV-212, INV-300).\n")
#: Phase D step 2 and Module 5 step 11 before #513: the MATCH_KEY query cited for the dash rule.
PRE_513_DASH_RULE = ("## Step\n\nThe Entity Specification's *Feature: REL_ANCHOR* gives the rule "
                     "*\"Use a domain code without dashes\"* (`search_docs(query='MATCH_KEY "
                     "disclosed relationship REL_POINTER role in\nmatch key')`, server 1.37.13).\n")
#: Module 2 Step 3 before #513: a category and no query.
PRE_513_ANTI_PATTERNS = ("## Step 3\n\n**Before recommending any approach**, call `search_docs` "
                         "with `category='anti_patterns'` to\ncheck for known pitfalls.\n")


class TheRekeyedGuardFailsWhereItShould(unittest.TestCase):
    """#513 negative controls: each new check rejects the shape that let a route through."""

    def test_a_key_that_is_not_a_query_category_pair_fails(self):
        for key in ("globalization", ("globalization", None), ("search_docs", "globalization"),
                    ("search_docs", "globalization", ""), ("search_docs", "", None),
                    ("web_search", "globalization", None)):
            with self.subTest(key=key):
                problems = key_problems(key)
                self.assertTrue(problems)
                self.assertIn("INV-291", problems[0])
        self.assertEqual([], key_problems(("search_docs", "globalization", None)))
        self.assertEqual([], key_problems(("search_docs", "loading", "anti_patterns")))
        self.assertEqual([], key_problems(("find_examples", "Unable to get settings", None)))

    def test_the_pre_513_phase_3_call_no_longer_matches_the_bare_terms_record(self):
        """The filtered call was matched to the bare term's OFF TARGET record and never checked."""
        found = queries_in("fixture.md", PRE_513_PHASE_3)
        self.assertEqual([("search_docs", "globalization", "globalization")],
                         [k for _l, k, _s in found])
        self.assertIn(("search_docs", "globalization", None), VERIFIED_QUERIES)
        self.assertEqual(
            ["fixture.md: search_docs(query='globalization', category='globalization')"],
            unaccounted(found, VERIFIED_QUERIES))

    def test_the_same_words_under_two_categories_are_two_records(self):
        """A site is checked against its own category's record, never the other one's."""
        allowlist = {
            ("search_docs", "globalization", None): _good_record(band="OFF TARGET BY DESIGN",
                                                                 sections=()),
            ("search_docs", "globalization", "globalization"): _good_record(
                sections=("Supported cultural groups",),
                returned="ON TARGET: 'Advanced personal name comparisons > Supported cultural "
                         "groups'"),
        }
        filtered = "## Step\n\nRun `search_docs(query='globalization', category='globalization')`.\n"
        bare = "## Step\n\nNever run `search_docs(query='globalization')`.\n"
        self.assertEqual([], unaccounted(queries_in("f.md", filtered + bare), allowlist))
        # The filtered site is held to the positive record, and names none of its sections.
        problems = site_problems(queries_in("f.md", filtered), allowlist)
        self.assertTrue(any("names none of" in p and "category='globalization'" in p
                            for p in problems), problems)
        # The bare site is held to the negative record, which asks nothing of it.
        self.assertEqual([], site_problems(queries_in("f.md", bare), allowlist))
        # Keyed on the words alone, the filtered site took the negative record and passed:
        # the defect #513 fixed.
        by_words = {"globalization": allowlist[("search_docs", "globalization", None)]}
        self.assertNotIn("names none of", " ".join(
            site_problems([(l, k[1], s) for l, k, s in queries_in("f.md", filtered)], by_words)))

    def test_a_site_citing_the_match_key_query_only_for_rel_anchor_fails(self):
        problems = site_problems(queries_in("fixture.md", PRE_513_DASH_RULE), VERIFIED_QUERIES)
        self.assertTrue(any("names none of" in p for p in problems), problems)
        self.assertNotIn("Feature: REL_ANCHOR", VERIFIED_QUERIES[
            ("search_docs", "MATCH_KEY disclosed relationship REL_POINTER role in match key",
             None)]["sections"],
            "Feature: REL_ANCHOR is fourth for the MATCH_KEY query; a target below rank 3 is "
            "not a route (INV-291)")

    def test_a_bare_category_mention_fails(self):
        problems = bare_category_mentions("fixture.md", PRE_513_ANTI_PATTERNS)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("fixture.md:3", problems[0])
        self.assertIn("INV-212", problems[0])
        double = PRE_513_ANTI_PATTERNS.replace("'anti_patterns'", '"anti_patterns"')
        self.assertEqual(1, len(bare_category_mentions("fixture.md", double)))
        in_a_call = "## Step\n\nUse `search_docs(category='anti_patterns')` first.\n"
        self.assertEqual(1, len(bare_category_mentions("fixture.md", in_a_call)))

    def test_a_category_mention_with_its_query_passes(self):
        """Must-not-flag: the corrected sentence, prose about the parameter, and the marker."""
        fixed = ("## Step 3\n\nCheck with `search_docs(query='install Senzing SDK installation "
                 "pitfalls',\ncategory='anti_patterns')` before recommending anything.\n")
        about = ("## Step\n\n`query` is `search_docs`' only required parameter — a bare "
                 "`category=` is a call no client can construct.\n")
        marked = ("## Step\n\n<!-- SEARCH-DOCS-CATEGORY-PROSE: names the `sdk` category -->\n"
                  "`search_docs(category='sdk')` indexes community wrapper docs too.\n")
        for text in (fixed, about, marked):
            with self.subTest(text=text[:40]):
                self.assertEqual([], bare_category_mentions("fixture.md", text))

    def test_a_sentence_boundary_ends_the_search_for_a_query(self):
        """A query in the NEXT sentence does not license a bare category in this one."""
        text = ("## Step\n\nCall `search_docs` with `category='anti_patterns'`. Then run "
                "`search_docs(query='loading', category='anti_patterns')`.\n")
        self.assertEqual(1, len(bare_category_mentions("fixture.md", text)))


#: A two-file fixture: a canonical route and the sites that point at it.
OWNER_FILE = ("# Owner\n\n## 11. Map\n\nConfirm with `search_docs(query='REL_ANCHOR_KEY "
              "REL_POINTER disclosed relationship keys', category='data_mapping')`; read past the "
              "first hit to *Feature: REL_ANCHOR*.\n\n## 12. Next\n\nNothing measured here.\n")


def _pointer_site(anchor="11. Map", path="owner.md", names="*Feature: REL_ANCHOR*"):
    return (f"## Audit\n\nThe rule is {names}'s. Its route is stated once, in\n`{path}` → "
            f"\"{anchor}\" (INV-300).\n")


def _load_fixture(label, path):
    return ("owner.md", OWNER_FILE) if path == "owner.md" else None


class TheRoutePointerCheckFailsWhereItShould(unittest.TestCase):
    """#513 negative controls for the pointer-following check (INV-300, INV-291)."""

    def problems(self, site):
        return pointer_problems(route_pointers("site.md", site), VERIFIED_QUERIES, _load_fixture)

    def assert_rejected(self, problems, needle):
        self.assertTrue(problems, "the check passed a defective pointer")
        self.assertTrue(any(needle in p for p in problems), problems)
        self.assertTrue(all("INV-291" in p for p in problems), problems)

    def test_a_sound_pointer_passes(self):
        self.assertEqual(1, len(route_pointers("site.md", _pointer_site())))
        self.assertEqual([], self.problems(_pointer_site()))

    def test_a_pointer_wrapped_across_lines_is_still_found(self):
        site = _pointer_site().replace("stated once, in\n", "stated\nonce, in\n")
        self.assertEqual(1, len(route_pointers("site.md", site)))

    def test_a_pointer_to_no_file_fails(self):
        self.assert_rejected(self.problems(_pointer_site(path="missing.md")), "names no shipped")

    def test_a_pointer_to_no_heading_fails(self):
        self.assert_rejected(self.problems(_pointer_site(anchor="13. Gone")),
                             "names no heading or bold lead")

    def test_a_pointer_to_a_section_with_no_measured_route_fails(self):
        self.assert_rejected(self.problems(_pointer_site(anchor="12. Next")),
                             "no measured search_docs route")

    def test_a_pointing_site_that_names_none_of_the_routes_sections_fails(self):
        """The pointing site is checked against the record of the route it lands on."""
        self.assert_rejected(self.problems(_pointer_site(names="*Feature: NAME*")),
                             "names none of the sections its route returns")

    def test_a_bold_lead_anchors_a_pointer(self):
        owner = OWNER_FILE.replace("## 11. Map\n\n", "## Notes\n\n- **Relationship keys:** ")

        def load(label, path):
            return ("owner.md", owner) if path == "owner.md" else None
        site = _pointer_site(anchor="Relationship keys")
        self.assertEqual([], pointer_problems(route_pointers("site.md", site),
                                              VERIFIED_QUERIES, load))


class EveryRouteIsStatedOnceWithOneStamp(unittest.TestCase):
    """#600: one full statement per route, and the record is the route's only stamp."""

    def test_the_scan_finds_the_statements(self):
        """Anti-vacuity: the routes #600 consolidated each have their one statement."""
        keys = {key for _l, key, _s, _t in shipped_statements()}
        for key in (("search_docs", "loading", "anti_patterns"),
                    ("search_docs", "NAME_FULL NAME_ORG parsed person name single field",
                     "data_mapping"),
                    ("search_docs", "scoop-senzingsdk update scoop update senzingsdk", None),
                    ("find_examples", "Unable to get settings", None)):
            with self.subTest(key=key):
                self.assertIn(key, keys)

    def test_no_route_is_stated_in_full_twice(self):
        problems = restated_routes(shipped_statements())
        self.assertEqual(
            [], problems,
            "A measured route is stated in full under more than one heading, so the copies drift "
            "(#600 found seven of one route, differing on version= and on their stamps):\n  "
            + "\n  ".join(problems))

    def test_no_new_prose_stamp_and_the_old_ones_only_shrink(self):
        problems = stamp_problems(shipped_statements(), STAMPED_IN_PROSE)
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_grandfathered_key_is_a_record(self):
        self.assertEqual([], sorted(set(STAMPED_IN_PROSE) - set(VERIFIED_QUERIES), key=str))


#: A route stated under two headings: the shape #600 found at seven sites.
RESTATED = ("## A\n\nCall `search_docs(query='loading', category='anti_patterns')`.\n\n"
            "## B\n\nAgain `search_docs(query=\"loading\", category=\"anti_patterns\")`.\n")


class TheStatedOnceChecksFailWhereTheyShould(unittest.TestCase):
    """#600 negative controls: a second statement, a find_examples literal, a new stamp."""

    def statements(self, text, allowlist=None):
        return statements_in("f.md", text, VERIFIED_QUERIES if allowlist is None else allowlist)

    def test_a_route_stated_under_two_headings_fails(self):
        problems = restated_routes(self.statements(RESTATED))
        self.assertEqual(1, len(problems), problems)
        self.assertIn("stated in full at 2 places", problems[0])
        self.assertIn("INV-300", problems[0])

    def test_one_heading_or_a_pointer_passes(self):
        same = RESTATED.replace("\n\n## B\n\n", "\n\n")
        self.assertEqual([], restated_routes(self.statements(same)))
        pointed = RESTATED.split("## B")[0] + (
            "## B\n\nThe route is stated once, in `f.md` → \"A\" (INV-300).\n")
        self.assertEqual([], restated_routes(self.statements(pointed)))

    def test_a_route_quoted_in_an_mcp_negative_owner_clause_is_not_a_statement(self):
        marked = RESTATED.replace(
            "Again `search_docs(query=\"loading\", category=\"anti_patterns\")`.",
            "<!-- MCP-NEGATIVE" ": x — y — owner: search_docs(query='loading', "
            "category='anti_patterns') IS the route (routing negative) — server 1.38.2, "
            "2026-10-14 -->")
        self.assertEqual([], restated_routes(self.statements(marked)))

    def test_a_negative_band_quote_is_not_a_statement(self):
        twice = ("## A\n\nNever `search_docs(query='globalization')`.\n\n"
                 "## B\n\nNot `search_docs(query='globalization')` either.\n")
        self.assertEqual([], restated_routes(self.statements(twice)))

    def test_an_unrecorded_find_examples_literal_fails(self):
        text = "## Step\n\nUse `find_examples(query='never measured', language='java')`.\n"
        found = queries_in("f.md", text)
        self.assertEqual([("find_examples", "never measured", "java")], [k for _l, k, _s in found])
        self.assertEqual(["f.md: find_examples(query='never measured', language='java')"],
                         unaccounted(found, VERIFIED_QUERIES))

    def test_a_find_examples_site_naming_no_returned_file_fails(self):
        text = "## Step\n\nRun `find_examples(query='Unable to get settings')`.\n"
        problems = site_problems(queries_in("f.md", text), VERIFIED_QUERIES)
        self.assertTrue(any("names none of" in p for p in problems), problems)

    def test_a_new_prose_stamp_fails_and_a_dropped_one_leaves_the_list(self):
        stamped = ("## Step\n\nCall `search_docs(query='loading', category='anti_patterns')` "
                   "(server 1.38.2, docs index 2026-10-14 20:27 UTC).\n")
        key = ("search_docs", "loading", "anti_patterns")
        problems = stamp_problems(self.statements(stamped), ())
        self.assertEqual(1, len(problems), problems)
        self.assertIn("one stamp", problems[0])
        self.assertEqual([], stamp_problems(self.statements(stamped), (key,)))
        bare = stamped.replace(" (server 1.38.2, docs index 2026-10-14 20:27 UTC)", "")
        self.assertEqual([], stamp_problems(self.statements(bare), ()))
        problems = stamp_problems(self.statements(bare), (key,))
        self.assertTrue(problems and "only shrinks" in problems[0], problems)

    def test_a_senzing_version_is_not_a_stamp(self):
        """`upgrading to 4.4.0` names the SDK, not the MCP server that measured the route."""
        self.assertIsNone(PROSE_STAMP.search("upgrading to 4.4.0 on 4.3.2"))
        self.assertIsNotNone(PROSE_STAMP.search("re-verified on\n1.37.27"))
        self.assertIsNotNone(PROSE_STAMP.search("server **1.37.19**"))


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
