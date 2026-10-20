"""Every example payload in the visualization contract obeys the field list stated beside it.

Enforces **INV-397**, registered by the maintainer 2026-10-20: an example payload in a contract the
plugin itself defines carries only fields that contract states. ⚠️ It **cannot** establish that a
stated field list is the right one -- that is a Senzing measurement (INV-080) -- or that any
implementation returns what the contract says.

``visualization-api-reference.md`` is the normative contract every Truth Set visualization
server is generated from, in any language (INV-090, INV-002). Its ``/api/records`` entry showed
a record object carrying ``name``, ``address``, ``phone`` and ``identifiers.SSN``. Eight lines
below that example the same entry stated that each record carries ``data_source``, ``record_id``
and ``match_key``; 340 lines above it the same file stated that a server reporting per-record
names without adding the record-feature flags "is inventing them".

⛔ **An example is read as the authority, whatever the prose beside it says.** A guide
generating a server from that example either invents per-record values -- the thing the file
forbids -- or renders three empty columns, which reads as missing data rather than as a payload
that never had those fields (INV-115). The bundled reference already hit the second outcome and
fixed it, and its client still carries the comment recording that a hardcoded Name/Address/Phone
header "rendered three empty columns for every row". Either outcome ships in the standalone
snapshot, which is the keepsake the Bootcamper keeps and may share.

**What is derived, and from where (INV-246).** Nothing here is a hardcoded field list or a
hardcoded line number:

* The **field sets** come from the contract's own sentences. Two shapes state one: the closed
  enumeration ``Each <kind>: `a`, `b`, `c`.`` and ``/api/records``' ``Each record carries the
  same fields `/api/merges` uses -- `a`, `b`, `c` --``. Both are read wrap-aware, because
  Markdown wraps a sentence wherever the column runs out and the ``Each entity: ... Each
  record:`` sentence is wrapped in the shipped file (INV-346).
* The **sites** are every ``json`` fence in the file, found by scanning it, and every object
  inside one that sits in an array named for a kind the contract states fields for
  (``record`` -> ``records``, ``entity`` -> ``entities``, ``node`` -> ``nodes``,
  ``edge`` -> ``edges``). A fence added later is swept on the next run; a fence nobody thought
  of is not exempt.

**What this cannot establish (INV-308).** It checks example payloads against the contract's own
stated field lists, and nothing else. It does not establish that a stated field list is the
right one -- that is a Senzing measurement, recorded beside the list and re-asked against the
MCP server, not something a text scan can settle. It says nothing about the reference server's
payloads: ``tests/test_visualization_api_contract.py`` exercises those against the model. A
sentence that states a field list in some third shape is invisible to the two shapes above, and
an object in an array the contract states no fields for is not checked.

Enforces the example side of INV-090 and INV-002, with the sites derived on every run (INV-246)
and the sentences read across line wraps (INV-346).

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Source issue: #682.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import unittest
from pathlib import Path

from _wrapped_text import blocks

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
            / "module-03b-truthset-visualization" / "visualization-api-reference.md")

#: A run of two or more backticked lowercase identifiers -- the shape a stated field list takes.
#: A backticked token that is not a bare identifier (`` `/api/merges` ``) ends the run, which is
#: what keeps the ``carries the same fields`` sentence from picking up the route it points at.
FIELD_RUN = re.compile(r"`[a-z_]+`(?:\s*(?:,\s*|\s+and\s+)?`[a-z_]+`)+")
IDENTIFIER = re.compile(r"`([a-z_]+)`")
#: ``Each record:``, ``Each entity:``, ``Each node:``, ``Each edge:`` -- a closed enumeration of
#: one kind's fields. The colon form is deliberate: ``Each result includes the base fields (...)
#: plus enrichment fields`` is an OPEN list whose remainder is a table, and sweeping it as closed
#: would fail on correct content.
CLOSED_ENUMERATION = re.compile(r"\bEach ([a-z]+):")
#: ``/api/records`` states its record fields by pointing at ``/api/merges`` and repeating them.
SAME_FIELDS = re.compile(r"\bEach ([a-z]+) carries the same fields\b")
#: An endpoint entry opens with its route in bold, which is how a fence is attributed to one.
ROUTE_HEADING = re.compile(r"^\*\*`GET (/api/[a-z]+)")
#: A fence line, by its first non-blank characters.
FENCE = re.compile(r"^\s*```(\w*)\s*$")


def contract_text():
    return CONTRACT.read_text(encoding="utf-8")


def collapsed_blocks(text):
    """``(line, flat)`` for each Markdown block, whitespace collapsed to one space (INV-346).

    The blocks come from ``_wrapped_text.blocks``, so a sentence wrapped across lines is one
    string and no match spans a blank line, a heading, a table row or a fence.
    """
    for block in blocks(text):
        flat = " ".join(" ".join(line for _, line in block).split())
        if flat:
            yield block[0][0], flat


def plural(singular):
    """The array name the contract uses for a kind: ``entity`` -> ``entities``."""
    return singular[:-1] + "ies" if singular.endswith("y") else singular + "s"


def stated_field_sets(text):
    """``{array name: [(line, frozenset of fields, the sentence fragment), ...]}``.

    Every field list the contract states for a kind of object, found by scanning its prose.
    A kind stated more than once gets one entry per statement, so the statements can be
    compared against each other rather than silently merged.
    """
    out = {}
    for line, flat in collapsed_blocks(text):
        for pattern in (CLOSED_ENUMERATION, SAME_FIELDS):
            for match in pattern.finditer(flat):
                run = FIELD_RUN.search(flat, match.end())
                if run is None:
                    continue
                fields = frozenset(IDENTIFIER.findall(run.group(0)))
                out.setdefault(plural(match.group(1)), []).append(
                    (line, fields, flat[match.start():run.end()]))
    return out


def json_fences(text):
    """``(line, parsed)`` for every ``json`` fence in the file, in order.

    Line-scoped by design (#682): a fence is delimited by whole lines, so finding one is a
    line-level read. The prose this guard matches is read wrap-aware by ``collapsed_blocks``.
    """
    out = []
    lang, start, body = None, 0, []
    for lineno, line in enumerate(text.split("\n"), 1):
        fence = FENCE.match(line)
        if fence and lang is None:
            lang, start, body = fence.group(1), lineno, []
        elif fence:
            if lang == "json":
                out.append((start, json.loads("\n".join(body))))
            lang = None
        elif lang is not None:
            body.append(line)
    return out


def objects_by_kind(payload, wanted):
    """``(array name, object)`` for every dict inside an array named in ``wanted``, at any depth."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in wanted and isinstance(value, list):
                    found.extend((key, item) for item in value if isinstance(item, dict))
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def violations(text):
    """``(line, array name, sorted undocumented keys)`` for every example object that overruns
    the field list its own contract entry states for that kind."""
    stated = stated_field_sets(text)
    allowed = {name: frozenset().union(*[f for _, f, _ in entries])
               for name, entries in stated.items()}
    out = []
    for line, payload in json_fences(text):
        for name, obj in objects_by_kind(payload, allowed):
            extra = sorted(set(obj) - allowed[name])
            if extra:
                out.append((line, name, extra))
    return out


def endpoint_examples(text):
    """``{route: [(line, parsed), ...]}`` -- each ``json`` fence under the entry that opens it.

    Line-scoped by design (#682): a route heading opens a line and a fence is delimited by
    lines, so attributing a fence to an entry is a line-level read.
    """
    starts = []
    for lineno, line in enumerate(text.split("\n"), 1):
        route = ROUTE_HEADING.match(line)
        if route:
            starts.append((lineno, route.group(1)))
    out = {}
    for line, payload in json_fences(text):
        owner = [route for start, route in starts if start < line]
        if owner:
            out.setdefault(owner[-1], []).append((line, payload))
    return out


class TheContractStatesOneRecordFieldSet(unittest.TestCase):
    """The two sentences that state the record fields must agree, or the example cannot."""

    def setUp(self):
        self.stated = stated_field_sets(contract_text())

    def test_the_record_field_set_is_stated_at_all(self):
        entries = self.stated.get("records", [])
        self.assertGreaterEqual(
            len(entries), 2,
            "fewer than two sentences state the record field set, so either a statement was "
            "removed or it was reworded out of the two shapes this guard reads. The sweep "
            "below derives its allowed keys from these sentences, so an empty read would "
            "certify nothing (INV-265).")

    def test_every_statement_of_the_record_field_set_agrees(self):
        entries = self.stated.get("records", [])
        distinct = {fields for _, fields, _ in entries}
        self.assertEqual(
            1, len(distinct),
            "the contract states more than one record field set: "
            + "; ".join(f"line {line}: {sorted(fields)}" for line, fields, _ in entries))

    def test_the_stated_record_fields_are_the_three_the_flags_return(self):
        """The set is read from the file, and pinned here because a change to it is a Senzing
        claim: the entity model is built with ``SZ_ENTITY_DEFAULT_FLAGS``, which excludes the
        record-feature and record-JSON flags, so a fourth field would have to arrive with the
        flag change the same entry describes as optional."""
        entries = self.stated.get("records", [])
        self.assertTrue(entries, "no sentence states the record field set")
        self.assertEqual(
            {"data_source", "record_id", "match_key"}, set(entries[0][1]),
            "the record field set changed. That is a Senzing claim, not an editorial one: "
            "re-verify the flag composite against the MCP server (INV-080) and update the "
            "measurement recorded beside the list before changing this.")


class NoExamplePayloadOverrunsItsStatedFieldList(unittest.TestCase):
    """The sweep: every ``json`` fence in the file, every object in an array the contract
    states fields for."""

    def test_the_sweep_reaches_the_examples(self):
        """An empty sweep is an unrun check, not agreement (INV-265)."""
        text = contract_text()
        allowed = set(stated_field_sets(text))
        swept = [obj for _, payload in json_fences(text)
                 for obj in objects_by_kind(payload, allowed)]
        self.assertGreaterEqual(
            len(swept), 4,
            "the sweep found almost no example objects to check, so a pass here means the "
            "scan broke rather than that the file is clean")

    def test_no_example_object_carries_a_field_its_entry_does_not_state(self):
        offenders = violations(contract_text())
        self.assertEqual(
            [], offenders,
            "an example payload advertises fields the same contract forbids: "
            + "; ".join(f"line {line}: a {name[:-1]} object carries {extra}"
                        for line, name, extra in offenders)
            + ". A guide generating a server from the example either invents those values or "
              "renders empty columns (INV-115).")


class TheRecordsExampleShowsTheSameObjectsAsMerges(unittest.TestCase):
    """``/api/records`` and ``/api/merges`` MUST return the same record objects, so the two
    examples must show the same ones rather than merely the same field names."""

    def setUp(self):
        text = contract_text()
        self.stated = stated_field_sets(text)
        self.examples = endpoint_examples(text)

    def records_example(self):
        fences = self.examples.get("/api/records", [])
        self.assertTrue(fences, "the /api/records entry carries no json example")
        return fences[0][1]

    def merges_example(self):
        fences = self.examples.get("/api/merges", [])
        self.assertTrue(fences, "the /api/merges entry carries no json example")
        return fences[0][1]

    def test_the_records_example_carries_exactly_the_stated_fields(self):
        stated = set(self.stated["records"][0][1])
        records = self.records_example()["records"]
        self.assertTrue(records, "the /api/records example shows no record")
        for record in records:
            with self.subTest(record=record.get("record_id")):
                self.assertEqual(
                    stated, set(record),
                    "the /api/records example's record object is not the field set the same "
                    "entry states. A missing field reads as a payload that never had it and "
                    "an extra one is a field the contract forbids (INV-115).")

    def test_the_two_examples_describe_the_same_entity(self):
        """Otherwise the comparison below would compare nothing and pass by construction
        (INV-265)."""
        merged = [e for e in self.merges_example()["entities"]
                  if e["entity_id"] == self.records_example()["entity_id"]]
        self.assertEqual(
            1, len(merged),
            "the /api/records and /api/merges examples no longer describe one entity, so the "
            "'same record objects' rule is not visible in the examples at all")

    def test_the_two_examples_show_the_same_record_objects(self):
        records = self.records_example()
        merged = [e for e in self.merges_example()["entities"]
                  if e["entity_id"] == records["entity_id"]][0]
        self.assertEqual(
            merged["records"], records["records"],
            "the contract says the two endpoints MUST return the same record objects, not "
            "merely the same field names -- and its own two examples disagree")


class TheGuardFailsOnTheTextItWasWrittenFor(unittest.TestCase):
    """Negative controls, on in-memory fixtures so they cannot be mistaken for the real file."""

    FIXTURE = """\
**`GET /api/merges`:** Multi-record entities with constituent records

```json
{"entities": [{"entity_id": 1, "records": [
  {"data_source": "CUSTOMERS", "record_id": "1001", "match_key": ""}]}]}
```

Each entity: `entity_id`, `records`. Each record:
`data_source`, `record_id`, `match_key`. Only entities with 2+ records are returned.

**`GET /api/records?entity_id=<id>`:** The constituent records of one entity

```json
{"entity_id": 1, "records": [
  {"data_source": "CUSTOMERS", "record_id": "1001", "name": "Robert Smith",
   "address": "123 Main St", "identifiers": {"SSN": "123-45-6789"}}]}
```

Each record carries the same fields `/api/merges` uses -- `data_source`, `record_id`,
`match_key` -- and the two endpoints MUST return **the same record objects**.
"""

    def test_the_wrapped_statement_is_read(self):
        """The shipped sentence wraps after ``Each record:``; a line-at-a-time read misses it."""
        stated = stated_field_sets(self.FIXTURE)
        self.assertEqual(
            [{"data_source", "record_id", "match_key"}] * 2,
            [set(fields) for _, fields, _ in stated["records"]])

    def test_the_defect_is_reported_with_its_fields(self):
        offenders = violations(self.FIXTURE)
        self.assertEqual(
            [["address", "identifiers", "name"]], [extra for _, _, extra in offenders],
            "the sweep did not report the per-record fields the contract forbids")

    def test_a_clean_fixture_passes(self):
        clean = self.FIXTURE.replace(
            '"name": "Robert Smith",\n   "address": "123 Main St", '
            '"identifiers": {"SSN": "123-45-6789"}', '"match_key": ""')
        self.assertNotEqual(clean, self.FIXTURE, "the control fixture was not edited")
        self.assertEqual([], violations(clean))

    def test_a_field_added_to_a_kind_the_contract_also_states_is_reported(self):
        """The sweep is not about records alone: it reaches every kind the contract enumerates."""
        broken = self.FIXTURE.replace('{"entity_id": 1, "records": [\n  {"data_source"',
                                      '{"entity_id": 1, "entity_name": "x", "records": [\n'
                                      '  {"data_source"', 1)
        self.assertNotEqual(broken, self.FIXTURE, "the control fixture was not edited")
        self.assertIn(("entities", ["entity_name"]),
                      [(name, extra) for _, name, extra in violations(broken)])


if __name__ == "__main__":
    unittest.main()
