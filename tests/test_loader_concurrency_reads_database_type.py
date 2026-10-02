"""Tests that loader generation reads `database_type`, not only the volume tier.

Phase A step 1 captures the *production* volume tier and step 3 selects the loader architecture
from it; every tier except `demo` gets the threaded pattern, sized from Senzing's own
*"Start with 2-8 workers per CPU core"* guidance. The SQLite volume pre-load check then asked a
two-option question — proceed on SQLite, or migrate to PostgreSQL — and on *proceed* said only
"record `sqlite_volume_prompt` … then continue to the Phase B load".

Nothing between those points reduced the concurrency, so the sanctioned path ran a thread-pooled
loader against a database the *same* anti-patterns document calls one that *"does not support
concurrent writes"*, listing *"Database locked errors under concurrent access"* among its symptoms.

Observed live 2026-09-02 (Senzing SDK 4.4.0, build 4.4.0.26242, SQLite, 16 cores → 64 workers,
`medium` tier, 5,000 records): two engine-level `ERR: Resolved entity … is out of sync` lines and
throughput halving across that window (854 → 485 rec/s). The load itself was correct — 5,000
attempted, 5,000 loaded, 0 failed, 1,602 redo drained — so nothing was lost; the costs were a
Bootcamper shown `ERR:` beside "0 failed" with no explanation, and a take-home loader tuned for a
database they are not using.

The server makes the worker count a **database** question in its own words, which is the hook the
plugin was missing (`search_docs(query='loading', category='anti_patterns')`, server **1.36.0**,
2026-09-02): *"Start with 2-8 workers per CPU core and **tune based on your database and storage
throughput**."* No MCP route returns a SQLite worker **number**, so the ceiling is that property's
consequence and must be marked as a derivation rather than presented as served (INV-080/INV-149).

⛔ **The site set is SCANNED, not hardcoded (INV-246).** The sweep confirmed graduation is *not* a
second decision point — it copies `src/load/**` verbatim rather than regenerating it — but that
makes Phase A's code comment the only place the decision is ever explained, since it travels into
`production/` unchanged. The `database_type` file/key is checked against every site that reads it
rather than against the one this test's author had open: the first draft of the fix said
`bootcamp_progress.json`, and every other site says `bootcamp_preferences.yaml`.

Enforces **INV-296** (every recorded input constraining a generated artifact's shape is read at
the point of generation, and a narrowing is applied there and recorded in the artifact) and
**INV-297** (engine output is not conflated with the plugin's own per-record counts; the step
names which is authoritative and gives the reconciliation that settles a contradiction).

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
MODULE_6 = os.path.join(PLUGIN, "skills", "module-06-data-processing")
PHASE_A = os.path.join(MODULE_6, "phaseA-build-loading.md")
PHASE_B = os.path.join(MODULE_6, "phaseB-load-first-source.md")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def shipped_markdown():
    out = []
    for root, _dirs, files in os.walk(PLUGIN):
        if "__pycache__" in root:
            continue
        for name in files:
            if name.endswith(".md"):
                out.append(os.path.join(root, name))
    return sorted(out)


class LoaderGenerationReadsDatabaseType(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_A)

    def test_step_3_reads_database_type(self):
        """The whole defect: the tier decided concurrency and the datastore was not consulted."""
        # The architecture-selection bullet, up to the demo bullet that follows it.
        start = self.text.index("- **`small`, `medium`, or `large`:**")
        end = self.text.index("- **`demo`:**", start)
        section = self.text[start:end]
        self.assertIn(
            "database_type",
            section,
            "step 3 selects the loader architecture and must read database_type there — reading "
            "it only at the SQLite pre-load check leaves the worker count taken from the tier",
        )

    def test_the_tier_picks_the_pattern_and_the_datastore_the_worker_count(self):
        self.assertRegex(
            self.text,
            r"The tier picks the PATTERN; `database_type` picks the WORKER COUNT",
            "the split between what the tier decides and what the datastore decides must be "
            "explicit, since conflating them is the defect",
        )

    def test_sqlite_serializes_and_postgresql_is_uncapped(self):
        start = self.text.index("- **`small`, `medium`, or `large`:**")
        end = self.text.index("- **`demo`:**", start)
        section = self.text[start:end]
        self.assertRegex(
            section,
            r"(?s)\*\*`postgresql`\*\*.{0,220}?nothing is capped",
            "the cap must not leak to other datastores — PostgreSQL keeps the tier's full "
            "concurrency, which is the case the 2-8-per-core figure is written for",
        )
        self.assertRegex(
            section,
            r"(?s)\*\*`sqlite`\*\*.{0,120}serialize the writes",
            "SQLite keeps the tier's pattern but serializes the writes",
        )

    def test_an_absent_database_type_takes_the_conservative_branch(self):
        self.assertRegex(
            self.text,
            r"(?s)Absent or unreadable\*\* — treat it as the SQLite case",
            "a serialized loader on PostgreSQL is merely slower; a thread-pooled loader on "
            "SQLite is the documented failure, so absence takes the branch that cannot corrupt",
        )

    def test_the_ceiling_is_marked_as_derived_not_served(self):
        """INV-080/INV-149: no MCP route returns a SQLite worker number."""
        self.assertRegex(
            self.text,
            r"This ceiling is a\s+DERIVATION, not a served figure",
            "the server serves the property (no concurrent writes) and the tune-by-database "
            "instruction; the number is a consequence and must not be presented as documented",
        )

    def test_the_server_wording_is_quoted_with_its_version(self):
        self.assertIn("tune based on your database and storage", self.text)
        self.assertIn("does not support concurrent\n  writes", self.text)
        self.assertRegex(
            self.text,
            # Re-measured for #383 (was **1.36.0**, 2026-09-02): the prose stamp follows the
            # VERIFIED_QUERIES record in tests/test_prescribed_search_queries.py.
            r"server\s+\*\*1\.37\.19\*\*, docs index 2026-10-02 18:46 UTC, 2026-10-02",
            "a Senzing fact written into the plugin carries the tool, version and date",
        )

    def test_the_comment_names_the_graduation_consumer(self):
        """The comment is the only explanation the Bootcamper ever gets — it ships verbatim."""
        self.assertRegex(
            self.text,
            r"(?s)graduation copies\s+`src/load/\*\*` into `production/src/load/` \*\*verbatim\*\*",
            "naming the downstream consumer is what makes the comment requirement load-bearing "
            "rather than tidy",
        )


class TheProceedBranchStatesItsConsequence(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_A)

    def test_proceed_states_the_architecture_consequence(self):
        start = self.text.index("- **Proceed on SQLite:**")
        end = self.text.index("- **Migrate to PostgreSQL:**", start)
        section = self.text[start:end]
        self.assertRegex(
            section,
            r"Proceeding keeps SQLite \*and\* the serialized writer count",
            "both options in that question are about WHERE the data lands; the proceed branch "
            "must say what happens to HOW it is written",
        )

    def test_proceed_repairs_a_missed_reduction(self):
        start = self.text.index("- **Proceed on SQLite:**")
        end = self.text.index("- **Migrate to PostgreSQL:**", start)
        self.assertIn(
            "apply it before the load",
            self.text[start:end],
            "if database_type was absent at step 3 and is known now, the reduction is applied "
            "rather than a thread-pooled loader carried into a confirmed-SQLite datastore",
        )


class EngineStderrIsDistinguishedFromRecordFailures(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE_B)

    def test_engine_diagnostics_are_named_as_not_record_failures(self):
        self.assertRegex(
            self.text,
            r"engine writes its own diagnostics to that console, and they are NOT per-record\s+failures",
            "steps 6 and 7 point the Bootcamper at the console, where ERR: appears beside "
            "'0 failed' with nothing saying they are different things",
        )

    def test_the_authority_on_record_failures_is_named(self):
        self.assertRegex(
            self.text,
            r"loader's own `failed` count and its error log are the authority on record\s+failures",
            "naming the authority is what lets the Bootcamper resolve the contradiction",
        )

    def test_the_reconciliation_that_settles_it_is_given(self):
        self.assertRegex(
            self.text,
            r"(?s)records attempted equals records loaded.{0,120}redo queue\s+reached empty",
            "an explanation without a check is reassurance; the three-part reconciliation is "
            "what the Bootcamper can actually run",
        )

    def test_the_out_of_sync_message_is_not_explained_as_a_senzing_fact(self):
        """INV-080/INV-149: the corpus does not cover that message."""
        self.assertRegex(
            self.text,
            r"Do not explain what a specific engine message means unless a route serves it",
            "the plugin must not characterize an engine message the corpus does not document",
        )
        self.assertRegex(
            self.text,
            r"reported as \*\*an environment\s+observation\*\*, with the SDK version and date",
            "where no route serves it, the claim is an observation with provenance or nothing",
        )

    def test_the_absence_claim_carries_an_mcp_negative_marker_with_an_owner(self):
        """A negative is the one claim shape that cannot go stale detectably."""
        token = "MCP-" + "NEGATIVE"   # assembled so this file carries no literal marker
        marker = re.search(token + r": search_docs\(query='resolved entity[^>]*?-->", self.text, re.S)
        self.assertIsNotNone(marker, "the absence claim must carry an " + token + " marker")
        body = marker.group(0)
        self.assertIn("owner:", body, "a marker with no owner: clause does not parse (INV-194)")
        self.assertIn("absence negative", body)
        self.assertRegex(body, r"server 1\.36\.0, 2026-09-02")


class TheDatabaseTypeKeyIsReadFromOnePlace(unittest.TestCase):
    """INV-246: check the key against every site that reads it, not the one you had open."""

    def test_no_shipped_file_reads_database_type_from_the_progress_file(self):
        wrong = []
        for path in shipped_markdown():
            text = read(path)
            for m in re.finditer(r"`database_type`[^.\n]{0,80}", text):
                if "bootcamp_progress.json" in m.group(0):
                    wrong.append("%s: %s" % (os.path.relpath(path, REPO_ROOT), m.group(0)[:90]))
        self.assertEqual(
            [],
            wrong,
            "`database_type` is written to and read from config/bootcamp_preferences.yaml (SDK "
            "setup Step 7). A site reading it from bootcamp_progress.json finds nothing and "
            "silently takes the absent branch:\n  " + "\n  ".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()
