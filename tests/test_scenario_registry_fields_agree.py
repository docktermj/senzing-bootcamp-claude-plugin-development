"""Module 1 writes the registry fields Data collection reads, as one schema defines them.

Discover the Business Problem decides each generated scenario source's `provenance` (`cord` or
`synthesized`) and, for a `cord` source, its CORD dataset at Step 4b, and writes each source
into `config/data_sources.yaml` at Phase 2 Step 11. Data collection's marker guard then reads
`provenance` from that entry to choose its action, and its generation step reads "the record
counts, entity types and per-source quirks" from it. Before #604 neither Module 1 writer named
a single field, and Module 4's Data Source Registry note defined none of them, so what Module 4
found depended on what the guide happened to write.

The fix is one definition, Module 4's **Scenario source fields** note
(`#scenario-source-fields`, INV-300). Both Module 1 writers point at it, Step 11 names the
fields and the registry shape, and Module 4 Step 2 reads the fields by name. The intended count
is a new field, `scenario_record_count`; `record_count` stays the count measured in the
collected file, null before collection, and Module 1 never writes it (INV-412).

What this file pins:

1. **The schema** defines every field a Module 1 scenario entry carries: `name`, `provenance`,
   `cord_dataset` and `cord_source` (a `cord` source only), `entity_type`, `shape_quirks` and
   `scenario_record_count` (a `synthesized` source only). It says `record_count` is never
   written by Module 1, names `quality_intent` as Step 2's to write, and gives the fallback for
   an entry with no `scenario_record_count`.
2. **Step 11** names every field the schema says Module 1 writes, the `version: "1"` /
   `sources:` shape, and links the schema; it writes no `record_count`.
3. **Phase 1's writer** links the same schema.
4. **Module 4 Step 2 reads them by name**: the guard reads `provenance`, the `cord` branch
   reads `cord_dataset` and `cord_source`, and the generation step reads
   `scenario_record_count`, `entity_type` and `shape_quirks`, falls back to
   `docs/business_problem.md`, and writes the measured `record_count` back.
5. **Agreement**: every field Step 2 reads is in the schema's list and in Step 11's list, and
   Step 11 names no field the schema does not define.

Each predicate is negative-controlled against the text with its clause removed, among them the
issue's own control: a field Module 4 reads, dropped from Step 11's list, fails.

Phrase checks run on whitespace-collapsed text, so a wrapped phrase still matches (INV-346).

Source issue: #604. Invariants applied: INV-300 (one definition, pointers name it), INV-412
(`record_count` is the measured baseline, written only by Data collection; registered 2026-10-23), INV-239 and INV-293 (what the scenario promised).

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
COLLECTION = SKILLS / "module-04-data-collection" / "SKILL.md"
STEP_11_FILE = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
DISCOVERY = SKILLS / "module-01-business-problem" / "phase1-discovery.md"

ANCHOR = '<a id="scenario-source-fields"></a>'
SCHEMA_LINK = "../module-04-data-collection/SKILL.md#scenario-source-fields"
STEP_11_HEAD = ("**Registry write (generated scenario):** record each distinct scenario source "
                "into `config/data_sources.yaml`")

#: What Module 4 Step 2 reads from a Module 1 scenario entry, each with the passage it reads in.
#: `guard` is the marker guard's lead, `cord` its `provenance: cord` branch and `generate` its
#: `provenance: synthesized` generation step.
READS = {
    "provenance": "guard",
    "cord_dataset": "cord",
    "cord_source": "cord",
    "scenario_record_count": "generate",
    "entity_type": "generate",
    "shape_quirks": "generate",
}

#: Every field the schema says Module 1 writes: the reads, plus the DATA_SOURCE's `name`.
WRITES = set(READS) | {"name"}


def squash(text):
    """Collapse whitespace and drop blockquote markers, so wrapped phrases match."""
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M))


def collection():
    return squash(COLLECTION.read_text(encoding="utf-8"))


def schema(body=None):
    """The Scenario source fields note, from its anchor to the next registry note."""
    body = collection() if body is None else body
    i = body.index(ANCHOR)
    return body[i:body.index("**Data File Validation:**", i)]


def schema_fields(text):
    """The fields the schema's list defines: the backticked names leading each list item."""
    fields = set()
    for item in re.findall(r" - ((?:`[a-z_]+`(?:,| and)? ?)+):", text):
        fields.update(re.findall(r"`([a-z_]+)`", item))
    return fields


def guard(body=None):
    """Step 2's marker guard lead, to its first branch."""
    body = collection() if body is None else body
    i = body.index("**The signal is the MARKER; the provenance selects the ACTION.**")
    return body[i:body.index("- **`provenance: cord`**", i)]


def cord_branch(body=None):
    body = collection() if body is None else body
    i = body.index("- **`provenance: cord`** →")
    return body[i:body.index("- **`provenance: synthesized`** →", i)]


def generation(body=None):
    """The `provenance: synthesized` branch's lead, to its first ⛔ rule."""
    body = collection() if body is None else body
    i = body.index("- **`provenance: synthesized`** → **generate the source files.**")
    return body[i:body.index("⛔ **Ask nothing, recommend no CORD alternative", i)]


def passages(body=None):
    return {"guard": guard(body), "cord": cord_branch(body), "generate": generation(body)}


def step_11(text=None):
    """Step 11's **Registry write** line, to the failure clause that follows it (#749)."""
    text = squash(STEP_11_FILE.read_text(encoding="utf-8")) if text is None else text
    i = text.index(STEP_11_HEAD)
    return text[i:text.index("**If writing an artifact fails:**", i)]


def discovery_writer(text=None):
    """Phase 1 Step 4a's success clause, which writes each source into the registry."""
    text = squash(DISCOVERY.read_text(encoding="utf-8")) if text is None else text
    i = text.index("success, record artifacts in Phase 2 Step 11")
    return text[i:text.index("then continue at Step 5", i)]


def named(field, text):
    return "`%s`" % field in text


# --- Predicates. Each takes text and returns the problems it finds, empty when clean. ---

def schema_problems(text):
    problems = []
    defined = schema_fields(text)
    for field in sorted(WRITES - defined):
        problems.append("the schema does not define `%s`" % field)
    if "(INV-300)" not in text or "phase2-document-confirm.md" not in text:
        problems.append("the schema does not name Step 11's file and INV-300 as the one definition")
    if not re.search(r"`cord_dataset` and `cord_source`: a `cord` source only", text):
        problems.append("the CORD key is not scoped to a `cord` source")
    if not re.search(r"A `synthesized` source has neither", text):
        problems.append("a `synthesized` source is not said to carry no CORD key")
    if not re.search(r"`scenario_record_count`: a `synthesized` source only", text):
        problems.append("`scenario_record_count` is not scoped to a `synthesized` source")
    if not re.search(r"never overwrites it, so it can be compared with the measured `record_count`",
                     text):
        problems.append("`scenario_record_count` is not kept beside the measured count")
    if not re.search(r"⛔ \(INV-412\) \*\*`record_count` stays the measured count:\*\* Module 1 "
                     r"never writes it, and it stays null until", text):
        problems.append("the schema does not keep `record_count` measured and unwritten by Module 1")
    if not re.search(r"`quality_intent` belongs to a `synthesized` entry too, written by Step 2's "
                     r"generation", text):
        problems.append("the schema does not say who writes `quality_intent`")
    if not re.search(r"An entry with no `scenario_record_count` was written before the field "
                     r"existed, and Step 2's generation takes the count from "
                     r"`docs/business_problem.md`", text):
        problems.append("the schema gives no fallback for an entry written before the field")
    return problems


def step_11_problems(text, defined):
    problems = []
    if SCHEMA_LINK not in text:
        problems.append("Step 11 does not link the schema")
    if not re.search(r"the one definition \(INV-300\)", text):
        problems.append("Step 11 does not name the schema as the one definition (INV-300)")
    if 'with `version: "1"` and a `sources:` mapping keyed by DATA_SOURCE' not in text:
        problems.append("Step 11 does not name the registry shape")
    for field in sorted(defined - {"record_count", "quality_intent"}):
        if not named(field, text):
            problems.append("Step 11 does not list `%s`" % field)
    listed = set(re.findall(r"`([a-z_]+)`", text)) - {"record_count", "quality_intent"}
    listed &= {f for f in listed if "_" in f or f in {"name", "provenance"}}
    for field in sorted(listed - defined):
        problems.append("Step 11 lists `%s`, which the schema does not define" % field)
    if not re.search(r"Write no `record_count`", text):
        problems.append("Step 11 does not say it writes no `record_count`")
    return problems


def reads_problems(by_passage, defined, step_11_text):
    problems = []
    for field, where in sorted(READS.items()):
        if not named(field, by_passage[where]):
            problems.append("Module 4 Step 2 (%s) does not read `%s`" % (where, field))
        if field not in defined:
            problems.append("Module 4 reads `%s`, which the schema does not define" % field)
        if not named(field, step_11_text):
            problems.append("Module 4 reads `%s`, which Step 11 does not list" % field)
    for where in ("cord", "generate"):
        if "(#scenario-source-fields)" not in by_passage[where]:
            problems.append("Module 4 Step 2 (%s) does not link the schema" % where)
    gen = by_passage["generate"]
    if not re.search(r"An entry with no `scenario_record_count` was written before that field "
                     r"existed: take the count from `docs/business_problem.md`", gen):
        problems.append("the generation step has no fallback for an entry without the field")
    if not re.search(r"record the actual counts back into the registry, as each source's measured "
                     r"`record_count`, and leave `scenario_record_count` as Module 1 wrote it",
                     gen):
        problems.append("the generation step does not keep the two counts apart")
    return problems


class TheSchemaDefinesTheScenarioFields(unittest.TestCase):
    def test_the_anchor_is_in_the_registry_note(self):
        body = collection()
        self.assertEqual(body.count(ANCHOR), 1, "the schema anchor is missing or doubled")
        i = body.index(ANCHOR)
        self.assertLess(body.index("**Data Source Registry:**"), i,
                        "the schema is not inside the Data Source Registry note")

    def test_the_list_is_read(self):
        """Liveness: the reader finds the six-plus fields, so an empty read cannot pass."""
        self.assertGreaterEqual(len(schema_fields(schema())), len(WRITES))

    def test_the_schema_is_complete(self):
        self.assertEqual(schema_problems(schema()), [])

    def test_negative_controls(self):
        text = schema()
        for mutant, why in (
            (text.replace("- `entity_type`:", "- entity type:"), "a field dropped"),
            (text.replace("A `synthesized` source has neither.", ""), "CORD key unscoped"),
            (text.replace("⛔ (INV-412) **`record_count` stays the measured count:**", ""),
             "record_count rule dropped"),
            (text.replace("written before the field existed", "old"), "fallback dropped"),
            (text.replace("(INV-300)", ""), "INV-300 dropped"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(schema_problems(mutant), [], why)


class Step11NamesTheFields(unittest.TestCase):
    def test_step_11_lists_every_field_by_pointer(self):
        self.assertEqual(step_11_problems(step_11(), schema_fields(schema())), [])

    def test_negative_control_a_field_module_4_reads_is_dropped(self):
        """The issue's control: Step 11 missing a field Module 4 reads fails."""
        text, defined = step_11(), schema_fields(schema())
        for field in sorted(READS):
            with self.subTest(field=field):
                mutant = text.replace("`%s`" % field, "the %s" % field.replace("_", " "))
                self.assertIn("Step 11 does not list `%s`" % field,
                              step_11_problems(mutant, defined))
                self.assertIn("Module 4 reads `%s`, which Step 11 does not list" % field,
                              reads_problems(passages(), defined, mutant))

    def test_negative_controls(self):
        text, defined = step_11(), schema_fields(schema())
        for mutant, why in (
            (text.replace(SCHEMA_LINK, "SKILL.md"), "link dropped"),
            (text.replace('`version: "1"`', "a version"), "shape dropped"),
            (text.replace("Write no `record_count`", "Write the `record_count`"),
             "record_count written"),
            (text.replace("`shape_quirks`", "`shape_quirks`, `source_kind`"),
             "an undefined field listed"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(step_11_problems(mutant, defined), [], why)


class PhaseOnePointsAtTheSameSchema(unittest.TestCase):
    def test_the_second_writer_links_the_schema(self):
        self.assertIn(SCHEMA_LINK, discovery_writer())

    def test_negative_control(self):
        self.assertNotIn(SCHEMA_LINK, discovery_writer().replace(SCHEMA_LINK, "SKILL.md"))

    def test_both_links_resolve(self):
        for source in (STEP_11_FILE, DISCOVERY):
            with self.subTest(source=source.name):
                target = (source.parent / SCHEMA_LINK.split("#")[0]).resolve()
                self.assertEqual(target, COLLECTION.resolve())


class Module4ReadsTheFieldsByName(unittest.TestCase):
    def test_every_read_agrees(self):
        self.assertEqual(
            reads_problems(passages(), schema_fields(schema()), step_11()), [])

    def test_negative_controls(self):
        body = collection()
        defined, s11 = schema_fields(schema(body)), step_11()
        for mutant, why in (
            (body.replace("its `scenario_record_count`, `entity_type` and `shape_quirks`",
                          "its counts, entity types and quirks"), "generation reads by name"),
            (body.replace("the entry's `cord_dataset` and `cord_source`", "the source"),
             "cord branch reads by name"),
            (body.replace("as each source's measured `record_count`, and leave "
                          "`scenario_record_count` as Module 1 wrote it", ""),
             "the two counts kept apart"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(reads_problems(passages(mutant), defined, s11), [], why)

    def test_a_read_the_schema_does_not_define_fails(self):
        defined = schema_fields(schema()) - {"shape_quirks"}
        self.assertIn("Module 4 reads `shape_quirks`, which the schema does not define",
                      reads_problems(passages(), defined, step_11()))


if __name__ == "__main__":
    unittest.main()
