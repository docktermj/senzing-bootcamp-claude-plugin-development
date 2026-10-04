"""The visualization model can be built from the export stream, not one call per record.

The reference server built its model by reading a records file and calling
``get_entity_by_record_id`` once per record — correct and fast at the Truth Set's 84
entities. Module 7 then points the same design at the Bootcamper's own data, which on the
reporting run meant **19,584 round trips to build one page** (2026-08-26). Rebuilt on the
export stream, the same model took ~15 seconds.

⚠️ **The correctness gain outlives the speed one.** A records-file build can only see
entities that have a record in the file it was handed; the export stream yields **every
resolved entity**, including embedded-master records a mapper emitted that appear in no
input file. So the per-record build can silently under-represent the multi-source
resolution Module 7 exists to show.

Enforces **INV-289** — where a reference implementation is reused by instruction, any
part of it whose correctness depends on the scale or shape of the data it was written
against is named at the point of reuse. ⚠️ It asserts BOTH ends: Module 7 stating the
strategy its data requires, and Module 3b stating that its per-record build is scoped to
the Truth Set. The second was missing until the invariant was registered, and asserting
only the first would have certified half a rule.

⚠️ What this establishes is that both statements SHIP. Whether a live walk actually
carries the right strategy forward is a claim about a turn, and `dry-run` phase 3's to
observe.

Method names and argument types verified against the live server per binding
(``get_sdk_reference(topic='parameters', …, language='python')``, server 1.35.3,
2026-09-01)::

    export_json_entity_report(flags: int = SZ_EXPORT_DEFAULT_FLAGS) -> int
    fetch_next(export_handle: int) -> str
    close_export_report(export_handle: int) -> None

⛔ These are **offline** tests against a fake engine. They assert that the export path
exists, absorbs identically, and closes its handle — never that it is fast, which needs a
live engine with a loaded datastore and stays the reporter's observation.

Stdlib only; the server is loaded by path (INV-108).
"""

import ast
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "plugins" / "senzing-bootcamp" / "scripts" / "senzing_viz_server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("_viz_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_viz_server"] = module
    spec.loader.exec_module(module)
    return module


def entity_doc(eid, records, related=()):
    return {
        "RESOLVED_ENTITY": {
            "ENTITY_ID": eid,
            "ENTITY_NAME": "Entity %d" % eid,
            "RECORDS": [{"DATA_SOURCE": ds, "RECORD_ID": rid, "MATCH_KEY": mk}
                        for ds, rid, mk in records],
        },
        "RELATED_ENTITIES": [{"ENTITY_ID": t, "MATCH_KEY": "+NAME",
                              "MATCH_LEVEL_CODE": "POSSIBLY_SAME"} for t in related],
    }


DOCS = [
    entity_doc(1, [("CUSTOMERS", "A1", ""), ("REFERENCE", "R1", "+NAME+ADDR")], related=[2]),
    entity_doc(2, [("WATCHLIST", "W1", "")]),
    # An entity with no record in any input file — an embedded master. The records-file
    # build cannot reach it; the export stream yields it.
    entity_doc(3, [("CUSTOMERS", "EMBEDDED-1", "")]),
]


class FakeRecordEngine:
    """Serves get_entity_by_record_id, like a records-file build sees it."""

    def __init__(self, docs):
        self.by_key = {}
        for doc in docs:
            for rec in doc["RESOLVED_ENTITY"]["RECORDS"]:
                self.by_key[(rec["DATA_SOURCE"], rec["RECORD_ID"])] = doc
        self.calls = 0

    def get_entity_by_record_id(self, ds, rid, flags):
        self.calls += 1
        return json.dumps(self.by_key[(ds, rid)])


class FakeExportEngine:
    """Serves the export triple, and records that the handle was closed.

    ⚠️ **It does not interpret real flag bits, and no test here should be read as
    validating the flag set.** ``flags`` is recorded in ``flags_seen`` (so the argument is
    at least observable rather than silently dropped) and ``strip`` simulates the ONE
    consequence that matters: a field the engine did not return. What a real engine does
    with ``SzEngineFlags`` is not knowable offline (INV-108) or on a machine with no
    datastore, so it is simulated explicitly instead of implied.
    """

    def __init__(self, docs, strip=()):
        self.docs = list(docs)
        self.closed = []
        self.opened = 0
        self.flags_seen = []
        self.strip = set(strip)
        self._streams = {}

    def _served(self, doc):
        """Return ``doc`` with every field in ``strip`` removed, at any depth."""
        if isinstance(doc, dict):
            return {k: self._served(v) for k, v in doc.items() if k not in self.strip}
        if isinstance(doc, list):
            return [self._served(v) for v in doc]
        return doc

    def export_json_entity_report(self, flags):
        self.opened += 1
        self.flags_seen.append(flags)
        handle = 900 + self.opened
        self._streams[handle] = iter(
            [json.dumps(self._served(d)) for d in self.docs])
        return handle

    def fetch_next(self, handle):
        return next(self._streams[handle], "")

    def close_export_report(self, handle):
        self.closed.append(handle)


class TheExportPathExists(unittest.TestCase):
    def setUp(self):
        self.viz = load_server()

    def test_the_model_has_an_export_build(self):
        self.assertTrue(
            hasattr(self.viz.Model, "build_from_export"),
            "Model must offer an export-stream build; the per-record build is the Truth "
            "Set path and does not scale to a Bootcamper's datastore.",
        )

    def test_the_records_file_build_still_exists(self):
        """The Truth Set path is unchanged — this adds a strategy, it does not replace one."""
        self.assertTrue(hasattr(self.viz.Model, "build"))


class BothPathsAbsorbIdentically(unittest.TestCase):
    """The claim that made the change small: an export row is shaped like a get_entity."""

    def setUp(self):
        self.viz = load_server()

    def test_the_two_builds_agree_on_entities_and_edges(self):
        keys = [(r["DATA_SOURCE"], r["RECORD_ID"])
                for d in DOCS for r in d["RESOLVED_ENTITY"]["RECORDS"]]
        per_record = self.viz.Model().build(FakeRecordEngine(DOCS), 0, keys)
        exported = self.viz.Model().build_from_export(FakeExportEngine(DOCS), 0)

        self.assertEqual(
            sorted(per_record.entities), sorted(exported.entities),
            "both build paths must produce the same entity set from the same documents — "
            "that equivalence is why the absorb step is shared rather than duplicated",
        )
        self.assertEqual(
            sorted(per_record.edges), sorted(exported.edges),
            "both build paths must produce the same relationship edges",
        )

    def test_records_total_counts_records_not_export_rows(self):
        """An export row is one ENTITY; `records_total` is a record count."""
        exported = self.viz.Model().build_from_export(FakeExportEngine(DOCS), 0)
        expected = sum(len(d["RESOLVED_ENTITY"]["RECORDS"]) for d in DOCS)
        self.assertEqual(
            expected, exported.records_total,
            "records_total must count RECORDS. Incrementing once per export row would "
            "report 3 where the model holds 4 records, and the stats tab reads this.",
        )


class TheExportHandleIsAlwaysClosed(unittest.TestCase):
    """⛔ An unclosed export handle holds engine resources for the life of the process."""

    def setUp(self):
        self.viz = load_server()

    def test_the_handle_is_closed_on_a_clean_run(self):
        engine = FakeExportEngine(DOCS)
        self.viz.Model().build_from_export(engine, 0)
        self.assertEqual(1, len(engine.closed), "the export handle must be closed")

    def test_the_handle_is_closed_when_the_stream_raises(self):
        engine = FakeExportEngine(DOCS)

        def exploding(handle):
            raise RuntimeError("engine went away mid-stream")

        engine.fetch_next = exploding
        with self.assertRaises(RuntimeError):
            self.viz.Model().build_from_export(engine, 0)
        self.assertEqual(
            1, len(engine.closed),
            "the handle must be closed even when the stream raises — that is what the "
            "try/finally is for, and a leaked handle outlives the failed build",
        )


class TheExportPathIsReachableFromTheShippedServer(unittest.TestCase):
    """The MEDIUM finding of `production-readiness-audit-2026-09-01d`.

    `build_from_export` was added and **nothing in the shipped script called it**:
    `build_model` built per-record unconditionally and `--records` was `required=True`, so
    no invocation could reach it. Its only callers were these tests, which is dead code in
    a shipped artifact — and Module 7 tells the guide to model their own server on this
    file while mandating the export path, so the reference contradicted the instruction
    pointing at it.

    ⚠️ Asserted against the **call graph**, not the presence of the method. The ledger
    ticked a criterion reading *"can build … and does so when pointed at a Bootcamper
    datastore"* on the evidence that the method existed — which established the first half
    only. A test for `hasattr` would have passed on the defect.
    """

    def setUp(self):
        self.source = SERVER.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def _build_model_fn(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == "build_model":
                return node
        self.fail("build_model() not found in the shipped server")

    def _calls_within(self, fn):
        out = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                out.add(node.func.attr)
        return out

    def test_build_model_can_reach_the_export_path(self):
        calls = self._calls_within(self._build_model_fn())
        self.assertIn(
            "build_from_export", calls,
            "build_model() must be able to reach the export build. Adding the method "
            "without a call site leaves dead code in a shipped script that Module 7 tells "
            "the guide to model on, while instructing the very path it cannot take.",
        )

    def test_build_model_still_reaches_the_per_record_path(self):
        calls = self._calls_within(self._build_model_fn())
        self.assertIn(
            "build", calls,
            "the per-record path must remain reachable — it is correct for the Truth Set, "
            "which is what this reference serves.",
        )

    def test_the_records_argument_is_optional(self):
        """The route that selects the export path: omitting --records."""
        self.assertNotRegex(
            re.sub(r"\s+", " ", self.source),
            r'add_argument\("--records"[^)]*required=True',
            "--records must be optional; while it was required no invocation could select "
            "the export build.",
        )

    def test_the_export_call_uses_the_export_documented_composite(self):
        """The export call passes SZ_ENTITY_DEFAULT_FLAGS, not hand-assembled members.

        ⚠️ **This assertion was reversed on 2026-09-01, and the reversal is the point.**
        It previously required the opposite — an explicit `SZ_ENTITY_INCLUDE_*` set, with
        `SZ_EXPORT_DEFAULT_FLAGS` banned — because Module 7 said so and the server's
        production caution backs enumerating flags in general.

        That was pinning a wrong premise. `module-06-data-processing/phaseD-validation.md`
        already recorded a bootcamp session that assembled export flags from those members
        and got rows with **no `RELATED_ENTITIES` key at all, and no error** — for this
        model, a graph with nodes and no edges. The documentation says the same thing more
        quietly: the relationship and record-detail flags do not list the export methods in
        their `applies_to`, while `SZ_ENTITY_DEFAULT_FLAGS` does and its `response_paths`
        cover exactly what `_absorb` reads (server 1.35.4, 2026-09-01).

        So the claim being pinned is *"the export call requests entity content the way the
        export family documents"* — not any particular spelling of it.
        """
        fn = self._build_model_fn()
        names = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        self.assertIn(
            "SZ_ENTITY_DEFAULT_FLAGS", names,
            "the export call must request entity content through the composite the export "
            "family documents. Hand-assembling SZ_ENTITY_INCLUDE_* members has been "
            "OBSERVED to return rows with no RELATED_ENTITIES and no error.",
        )
        self.assertIn("SZ_EXPORT_INCLUDE_ALL_ENTITIES", names)
        hand_assembled = {n for n in names if n.startswith("SZ_ENTITY_INCLUDE_")}
        self.assertEqual(
            set(), hand_assembled,
            "the export flag set must not go back to hand-assembled SZ_ENTITY_INCLUDE_* "
            f"members: {sorted(hand_assembled)}. That is the composition observed to drop "
            "relationships silently.",
        )


class TheHeaderDescribesBothBuildPaths(unittest.TestCase):
    """The MEDIUM finding of `production-readiness-audit-2026-09-01e`.

    After the export path was wired, the module header still said the data source was
    ``get_entity_by_record_id`` … "one call per loaded record" — the path Module 7
    **forbids** for a Bootcamper's datastore, presented as the file's only behavior. The
    header is the first thing a reader sees, and Module 7 tells the guide to *"build it
    modeled on the shipped Truth Set visualization server"*, so a guide modeling on this
    file was told the wrong thing by its opening paragraph.

    ⚠️ That was the same instruction/reference disagreement the previous audit had just
    fixed in the call graph, relocated into the prose: one rule, several sites, fixed at
    one of them.
    """

    def setUp(self):
        source = SERVER.read_text(encoding="utf-8")
        # The module docstring only — a match anywhere else in a 2,000-line file would
        # not tell a reader at the top of it anything.
        self.header = ast.get_docstring(ast.parse(source)) or ""
        # ⚠️ And the DATA SOURCE section only, for the claims about it. Checked against
        # the whole docstring, `test_the_header_names_both_paths` passed with the entire
        # two-path block deleted — because the Usage block below it also says "export
        # stream". An assertion a neighboring section can satisfy is not an assertion
        # about the section it names.
        self.data_source = self.header.split("Usage:")[0]

    def test_the_header_names_both_paths(self):
        for path in ("get_entity_by_record_id", "export stream"):
            with self.subTest(path=path):
                self.assertIn(
                    path, self.data_source,
                    "the module header must name both build paths. Describing only the "
                    "per-record one tells a guide modeling on this file to implement "
                    "exactly what Module 7's stop-sign forbids.",
                )

    def test_the_header_says_what_selects_each(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.data_source),
            r"(?i)--records given.*--records omitted",
            "naming both paths is not enough — the header must say which condition "
            "selects each, or a reader cannot tell which one they are getting.",
        )

    def test_the_header_no_longer_claims_one_call_per_record_is_the_data_source(self):
        """The retired sentence, pinned so it cannot come back as a 'simplification'."""
        self.assertNotRegex(
            re.sub(r"\s+", " ", self.data_source),
            r"so nodes and edges come from one call per loaded record",
            "the header must not present the per-record build as the file's only data "
            "source.",
        )

    def test_the_no_direct_sql_guarantee_survives_and_covers_both(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.data_source),
            r"(?i)no direct SQL is ever run against the database on either",
            "the no-direct-SQL guarantee must survive the rewrite and must be stated as "
            "covering both paths — it is true of both, and dropping it to make room for "
            "the second path would trade a real guarantee for a description.",
        )

    def test_the_usage_block_shows_the_export_invocation(self):
        """A form shown nowhere is a form a reader does not know exists."""
        usage = self.header[self.header.index("Usage:"):]
        # Line-scoped by design (#424): each usage example is one command line.
        without_records = [
            line for line in usage.splitlines()
            if "senzing_viz_server.py" in line and "--records" not in line
        ]
        self.assertTrue(
            without_records,
            "the Usage block must show an invocation WITHOUT --records. Every example "
            "passing it means the export form is undiscoverable to a reader working "
            "top-to-bottom, which is how the path stayed unreachable in the first place.",
        )


class TheModuleSaysWhichStrategyApplies(unittest.TestCase):
    """Module 7 delegates by resemblance, so the scale assumption travels unless it is named."""

    def setUp(self):
        self.text = (REPO / "plugins" / "senzing-bootcamp" / "skills" /
                     "module-07-query-visualize-discover" /
                     "phase1-query-visualize.md").read_text(encoding="utf-8")
        # ⚠️ And the EXPORT-CALL block only, for claims about the export call. Checked
        # against the whole file, the "names the composite" assertion passed with every
        # mention deleted from the export guidance — satisfied by the flag-composite table
        # ~550 lines earlier, which is about `get_entity`. A file-wide `assertIn` on a
        # token this common tests that the module mentions a flag somewhere, which was
        # never the claim.
        start = self.text.index("Build the model from the EXPORT STREAM")
        rest = self.text[start:]
        nxt = re.search(r"\n- \*\*Keep all|\n- Keep all", rest)
        self.export_block = rest[:nxt.start()] if nxt else rest

    def test_it_instructs_the_export_stream_build(self):
        self.assertRegex(
            self.text, r"(?i)Build the model from the EXPORT STREAM",
            "Module 7 must say which build strategy applies to the Bootcamper's own data — "
            "'model it on the Truth Set server' otherwise carries the Truth Set's scale "
            "assumption into a 19,584-record datastore.",
        )

    def test_it_names_the_correctness_reason_not_only_speed(self):
        self.assertRegex(
            self.text, r"(?i)every \*\*resolved entity\*\*|appear in no input file",
            "the instruction must give the correctness reason too. Stated as a speed tip it "
            "reads as optional; the records-file build also MISSES entities.",
        )

    def test_it_sends_the_reader_to_the_server_for_the_signature(self):
        self.assertRegex(
            self.text, r"filter='export_json_entity_report'",
            "the export signature differs by binding in both name and argument type, so the "
            "instruction must name the route rather than showing one binding's form "
            "(INV-002/INV-080).",
        )

    def test_it_says_what_to_pass_to_the_export_call(self):
        """The guidance names the composite, and says why the usual advice is wrong here.

        ⚠️ Also reversed on 2026-09-01. The retired version required the module to warn
        *against* pinning a DEFAULT composite into the export call — advice that could not
        be followed (no `SZ_ENTITY_INCLUDE_*` flag lists the export methods in `applies_to`,
        so there is no enumerated set to request) and that pointed at the exact composition
        observed to lose every relationship. Pinning the instruction rather than the claim
        is what let it stand while `module-06` shipped the opposite.
        """
        flat = re.sub(r"\s+", " ", self.export_block)
        self.assertIn(
            "SZ_ENTITY_DEFAULT_FLAGS", flat,
            "the export guidance must name the composite it wants passed; a reader who is "
            "only told what not to do has to invent the rest.",
        )
        self.assertRegex(
            flat, r"(?i)no `?RELATED_ENTITIES`? key at all",
            "the guidance must carry the OBSERVATION, not just the conclusion. The reason "
            "this rule inverts the module's usual advice is the whole reason it survives "
            "a later tidy-up (INV-169).",
        )
        self.assertNotRegex(
            flat, r"(?i)Do not pin a `?\*_DEFAULT_FLAGS`? composite into the export call",
            "the retired instruction must not come back — it contradicted module-06 and "
            "named the composition observed to drop relationships.",
        )


if __name__ == "__main__":
    unittest.main()


# The fields `_absorb` reads, each against the export response document that carries it.
# Source: get_sdk_reference(topic='response_schemas', filter='export_json_entity_report',
# language='python') — server 1.35.4, 2026-09-01. `requires` is the flag the schema marks
# the path with; None means the schema documents the path with no `requires_flags`, which
# is true of every path this model reads.
ABSORBED_FIELDS = {
    "RESOLVED_ENTITY": ("RESOLVED_ENTITY", None),
    "ENTITY_ID": ("RESOLVED_ENTITY.ENTITY_ID", None),
    "ENTITY_NAME": ("RESOLVED_ENTITY.ENTITY_NAME", None),
    "RECORDS": ("RESOLVED_ENTITY.RECORDS[]", None),
    "RECORD_ID": ("RESOLVED_ENTITY.RECORDS[].RECORD_ID", None),
    "DATA_SOURCE": ("RESOLVED_ENTITY.RECORDS[].DATA_SOURCE", None),
    "MATCH_KEY": ("RESOLVED_ENTITY.RECORDS[].MATCH_KEY", None),
    "ERRULE_CODE": ("RELATED_ENTITIES[].ERRULE_CODE", None),
    "MATCH_LEVEL_CODE": ("RELATED_ENTITIES[].MATCH_LEVEL_CODE", None),
    "RELATED_ENTITIES": ("RELATED_ENTITIES[]", None),
    # Not a response field: the fallback string for an edge with neither code.
    "RELATED": (None, None),
}


class EveryAbsorbedFieldIsAccountedFor(unittest.TestCase):
    """The tripwire that makes the ``_absorb`` ↔ ``export_flags`` coupling fire.

    Neither end can see the other: `_absorb` is ~1,450 lines above the flag set, and a
    field read there whose flag is missing from the export list comes back **absent** —
    no error, no warning, a blank cell in the rendered page (INV-179). A comment saying
    so is read by whoever already suspects it. This fails instead.
    """

    def setUp(self):
        self.source = SERVER.read_text(encoding="utf-8")
        tree = ast.parse(self.source)
        self.absorb = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "_absorb")

    def read_fields(self):
        """Every SCREAMING_CASE string constant in `_absorb` — derived, never listed.

        ⛔ (INV-246) Scanned rather than hardcoded on purpose: a hardcoded list certifies
        the fields already thought of and is blind to the one a later edit adds, which is
        the only field this test exists to catch.
        """
        return {n.value for n in ast.walk(self.absorb)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", n.value)}

    def test_every_field_read_is_in_the_map(self):
        unknown = self.read_fields() - set(ABSORBED_FIELDS)
        self.assertEqual(
            set(), unknown,
            "`Model._absorb` reads a field this test does not account for: "
            f"{sorted(unknown)}. Look the path up in get_sdk_reference("
            "topic='response_schemas', filter='export_json_entity_report'), add it to "
            "ABSORBED_FIELDS, and — if the schema marks it with `requires_flags` — add "
            "that flag to `export_flags` in build_model. On the export path a field "
            "whose flag is missing renders blank with no error (INV-179).",
        )

    def test_every_required_flag_is_in_the_export_set(self):
        """No field read today is flag-gated; this fires when one becomes so."""
        flags_block = self.source[self.source.index("export_flags = ("):]
        flags_block = flags_block[:flags_block.index(")")]
        for field, (path, requires) in sorted(ABSORBED_FIELDS.items()):
            if requires is None:
                continue
            with self.subTest(field=field):
                self.assertIn(
                    requires, flags_block,
                    f"{field} ({path}) needs {requires}, which `export_flags` does not "
                    "request. The per-record path would still work — it passes the broad "
                    "SZ_ENTITY_DEFAULT_FLAGS — so this breaks only the Bootcamper's own "
                    "datastore, silently.",
                )

    def test_the_map_is_not_stale(self):
        """A field in the map that `_absorb` no longer reads means the map went stale."""
        unread = set(ABSORBED_FIELDS) - self.read_fields()
        self.assertEqual(
            set(), unread,
            f"ABSORBED_FIELDS lists {sorted(unread)}, which `_absorb` no longer reads. "
            "A map that has drifted from the code stops being evidence about it.",
        )


class AMissingFieldIsSilentNotLoud(unittest.TestCase):
    """The failure mode the coupling comment claims: absent field, no error, blank cell.

    This is what stops `test_the_two_paths_agree` being read as validation of the flag
    set. The fake ignores real flag bits, so the agreement it demonstrates holds only for
    the fields the fake was asked to serve — and here is what happens to a field it was
    not.
    """

    def setUp(self):
        self.viz = load_server()

    def test_a_stripped_match_key_renders_blank_rather_than_raising(self):
        docs = [{
            "RESOLVED_ENTITY": {
                "ENTITY_ID": 1,
                "ENTITY_NAME": "Alpha",
                "RECORDS": [{"DATA_SOURCE": "TEST", "RECORD_ID": "1",
                             "MATCH_KEY": "+NAME"}],
            },
            "RELATED_ENTITIES": [],
        }]
        full = self.viz.Model().build_from_export(FakeExportEngine(docs), 0)
        self.assertEqual(
            "+NAME", full.entities[1]["records"][0]["match_key"],
            "Precondition: the field is read when the engine serves it.",
        )

        stripped = self.viz.Model().build_from_export(
            FakeExportEngine(docs, strip={"MATCH_KEY"}), 0)
        self.assertEqual(
            "", stripped.entities[1]["records"][0]["match_key"],
            "A field the engine did not return must degrade to blank, not raise — which "
            "is exactly why a missing flag is invisible and needs a test rather than a "
            "comment (INV-179).",
        )
        self.assertEqual(
            1, len(stripped.entities),
            "The entity itself must still be built; a missing optional field must not "
            "cost the whole row.",
        )

    def test_the_flags_argument_reaches_the_engine(self):
        """`build_from_export` must pass its flags through, not drop them."""
        engine = FakeExportEngine([])
        self.viz.Model().build_from_export(engine, 12345)
        self.assertEqual(
            [12345], engine.flags_seen,
            "The flags argument must reach export_json_entity_report. A build that "
            "computes a flag set and then does not pass it is the defect this whole "
            "coupling is about, in its most direct form.",
        )


SHIPPED = REPO / "plugins" / "senzing-bootcamp"


class EveryShippedSiteAgreesAboutTheExportFlags(unittest.TestCase):
    """No shipped file may tell a reader to hand-assemble the export flag set.

    ⛔ (INV-246) The site set is SCANNED, not listed. The defect this guards against
    survived because the rule lived in three files that disagreed — `module-06` said start
    from the export composite, `module-07` said never pin one, and the reference server did
    a third thing — and every guard checked one file at a time, so no assertion could see
    the disagreement. A hardcoded pair of paths would reproduce that blindness exactly.
    """

    RETIRED = re.compile(
        r"(?i)do not pin a `?\*?_?DEFAULT_FLAGS`? composite into the export call")

    def shipped_files(self):
        for path in sorted(SHIPPED.rglob("*")):
            if path.suffix in (".md", ".py") and path.is_file():
                yield path

    def test_no_shipped_file_carries_the_retired_instruction(self):
        # Matched across line wraps (#424): the instruction is a sentence, and prose wraps.
        offenders = [
            f"{p.relative_to(REPO)}:{i}"
            for p in self.shipped_files()
            for i in match_lines(p.read_text(encoding="utf-8"), self.RETIRED)
        ]
        self.assertEqual(
            [], offenders,
            "a shipped file still tells the reader not to pin a DEFAULT composite into the "
            f"export call: {offenders}. That instruction cannot be followed — no "
            "SZ_ENTITY_INCLUDE_* flag lists the export methods in applies_to — and it names "
            "the composition observed to return no RELATED_ENTITIES at all.",
        )

    def test_a_wrapped_retired_instruction_is_caught(self):
        """Negative control (#424): the sentence wraps between "composite" and "into"."""
        wrapped = ("For the export, do not pin a `DEFAULT_FLAGS` composite\n"
                   "into the export call; pass the flags directly.\n")
        self.assertEqual([1], match_lines(wrapped, self.RETIRED))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(self.RETIRED.search(l) for l in wrapped.split("\n")))

    def test_the_modules_that_teach_the_export_call_name_the_composite(self):
        """Both teaching sites must name what to pass, not only what to avoid."""
        teaching = [
            p for p in self.shipped_files()
            if p.suffix == ".md" and "export_json_entity_report" in
            p.read_text(encoding="utf-8") and "flags" in p.read_text(encoding="utf-8")
        ]
        self.assertTrue(teaching, "no shipped file teaches the export call — scan is wrong")
        silent = [
            str(p.relative_to(REPO)) for p in teaching
            if "DEFAULT_FLAGS" not in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            [], silent,
            f"these files teach the export call without naming a flag composite: {silent}. "
            "A reader told to call the method but not what to pass will assemble members, "
            "which is the case observed to drop relationships.",
        )


class BothEndsOfTheReuseNameTheScaleScope(unittest.TestCase):
    """INV-289 binds the module where the reference is CORRECT, not only the one that changes.

    Module 7 always named its scale dependence — that is the finding its spec came from.
    Module 3b did not: it instructed "one `get_entity_by_record_id` call per record" flatly,
    as required behavior, while also telling the guide to build the server "modeled on the
    shipped reference". A guide could follow both modules correctly and still carry a
    per-record server into Module 7, because nothing at the 3b end said the instruction was
    scoped to the Truth Set.

    ⚠️ Found while REGISTERING the invariant, not while implementing the spec. The block
    named one file; the rule governs reuse-by-instruction, and the plugin instructs that in
    two modules. An invariant registered while one of its own sites fails it is how INV-097
    stood unimplemented for seven weeks and INV-060 for six.
    """

    M07 = (REPO / "plugins" / "senzing-bootcamp" / "skills" /
           "module-07-query-visualize-discover" / "phase1-query-visualize.md")
    M03B = (REPO / "plugins" / "senzing-bootcamp" / "skills" /
            "module-03b-truthset-visualization" / "phase1-visualization.md")

    def flat(self, path):
        return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

    def test_module_7_requires_the_export_stream(self):
        self.assertRegex(
            self.flat(self.M07), r"(?i)Build the model from the EXPORT STREAM",
            "Module 7 must state the strategy its data requires, not leave it to resemblance.",
        )

    def test_module_3b_says_its_per_record_build_is_scoped(self):
        """The half that was missing. Asserts the CLAIM, not one phrasing of it."""
        self.assertRegex(
            self.flat(self.M03B), r"(?i)correct HERE.{0,60}scoped to the Truth Set",
            "module-03b must say its per-record build is scoped to the Truth Set. Stated "
            "flatly it is an instruction that travels — the guide carries the server into "
            "Module 7 and the scale dependence goes with it, unnamed (INV-289).",
        )

    def test_module_3b_points_at_where_the_other_strategy_lives(self):
        self.assertRegex(
            self.flat(self.M03B),
            r"module-07-query-visualize-discover/phase1-query-visualize\.md",
            "naming the scope without naming where the other strategy is stated leaves the "
            "guide knowing the instruction is scoped and not knowing to what.",
        )

    def test_module_3b_gives_the_completeness_reason_not_only_the_speed_one(self):
        """⚠️ The reason that outlives the other. Speed is noticed; completeness is not."""
        self.assertRegex(
            self.flat(self.M03B), r"(?i)no input file|invisible to it|embedded-master",
            "the scope note must carry the COMPLETENESS reason — a records-file build cannot "
            "see entities with no record in the file it was handed. A note giving only the "
            "round-trip cost reads as an optimization, and an optimization is skippable.",
        )

    M03B_SKILL = (REPO / "plugins" / "senzing-bootcamp" / "skills" /
                  "module-03b-truthset-visualization" / "SKILL.md")

    def test_module_3bs_overview_also_names_the_scope(self):
        """The third site, found by the 2026-09-02 audit the day INV-289 was registered.

        `SKILL.md` carries the reuse instruction twice (*"modeled on the shipped
        reference"*) and stated the per-record build flatly beside it. The operative
        instruction in `phase1-visualization.md` was scoped when INV-289 was minted; the
        overview — which a guide reads first to orient — was not. Both halves unqualified
        in the file read first is how the strategy travels.
        """
        self.assertRegex(
            self.flat(self.M03B_SKILL), r"(?i)per-record build is scoped to the Truth Set",
            "module-03b/SKILL.md states the per-record build without saying it is scoped. "
            "INV-289 binds both ends of a reuse, and this file carries the reuse "
            "instruction at :33 and :118.",
        )

    def test_the_overview_points_at_the_reasoning_rather_than_repeating_it(self):
        """⚠️ INV-183 puts a rule where it is used; two copies is the drift class.

        The overview needs the FACT that a scope exists and where to read it — not the
        round-trip count and the embedded-master argument, which belong at the build step
        and are asserted there by `test_module_3b_gives_the_completeness_reason_...`.
        """
        # ⚠️ The SCOPE BULLET only. Checked against the whole file this passed with the
        # pointer deleted — `phase1-visualization.md` is named again in the phase overview
        # ~13 lines below, about something else entirely.
        text = self.M03B_SKILL.read_text(encoding="utf-8")
        start = text.index("(INV-289) That per-record build is scoped")
        flat = re.sub(r"\s+", " ", text[start:text.index("\n- ", start)])
        self.assertRegex(
            flat, r"phase1-visualization\.md",
            "the overview must say where the reasoning lives, or a guide told the build is "
            "scoped has no way to find out to what.",
        )
        self.assertNotRegex(
            flat, r"(?i)embedded-master|round trip",
            "the overview must not restate the reasoning — one rule, stated at the step "
            "that needs it (INV-183). Two copies drift, which is the class this whole "
            "invariant came from.",
        )
