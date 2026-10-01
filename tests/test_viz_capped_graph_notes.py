"""A capped Entity Graph says it is capped, with exact counts, and never claims "all".

On a 2026-10-01 walk (7,084 entities, 5,647 relationships) the relationship-mode note read
*"Showing the 286 entities that have relationships, of 7084 total ... Uncheck the toggle above
to show them all."* The 286 counted relationship-bearing entities **inside the payload the
graph endpoint had already capped at 1,500**, while at least 4,551 entities carried a link, so
the note understated the linked population about 16 times. Unchecking the toggle showed 1,500
entities, not "all", and full mode said nothing about the cap (#327).

⚠️ **The Truth Set (84 entities) never reaches the cap**, so no Module 3b walk can see this;
it appears only on a Bootcamper's own data in Module 7. Hence a fixture capped on purpose.

What is pinned:

* `graph()` carries `related_total` — the distinct endpoints of every edge, counted before
  the cap — in both capped and uncapped payloads.
* With `capped` true, the relationship-mode note, its empty variant and the full-population
  note each state the cap with exact counts and none says "all".
* With `capped` false, the notes render exactly as they did before (INV-154's wording).

The JS is exercised by transcribing the shipped note expressions out of the page source and
rendering them against a real `graph()` payload, rather than running a browser: the guarantee
is string assembly, and a headless browser is not available on every machine that runs this
suite (INV-052/INV-066). Each check is a function of the source text, so the negative controls
run the same checks over mutated copies of it.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "senzing_viz_server.py"


def load():
    spec = importlib.util.spec_from_file_location("viz_capped_notes_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_capped_notes_under_test"] = module
    spec.loader.exec_module(module)
    return module


VIZ = load()
SOURCE = SERVER.read_text(encoding="utf-8")

#: Today's uncapped wording, byte for byte (INV-154). The capped branch must not disturb it.
UNCAPPED_RELATIONSHIP_NOTE = (
    "Showing the 286 entities that have relationships, of 7084 total — the full population "
    "is too dense to read at this scale. Uncheck the toggle above to show them all."
)
UNCAPPED_EMPTY_NOTE = "No relationships between entities were found in this data."


def model_with(entities, edges=()):
    model = VIZ.Model()
    model.entities = {
        e["entity_id"]: {"record_count": 1, "entity_name": f"E{e['entity_id']}", **e}
        for e in entities
    }
    model.edges = {pair: {"match_key": "+NAME", "relationship_type": "POSSIBLY_SAME"}
                   for pair in edges}
    return model


#: Entities 1-5 span two sources, so a cap of 5 keeps exactly them. One relationship falls
#: inside the kept set; four fall wholly outside it, so a count taken after the cap is wrong.
WIDE = [{"entity_id": i, "data_sources": ["A", "B"]} for i in range(1, 6)]
NARROW = [{"entity_id": i, "data_sources": ["A"]} for i in range(6, 13)]
EDGES = [(1, 2), (6, 7), (8, 9), (10, 11), (7, 12)]
RELATED = 9   # {1, 2, 6, 7, 8, 9, 10, 11, 12}
CAP = 5


# --- transcription of the shipped JS -------------------------------------------------------

_TOKEN = re.compile(r'\s*(?:"((?:[^"\\]|\\.)*)"|([A-Za-z_][\w.]*)|(\+))')


def render(expr, env):
    """Evaluate a JS `"literal"+name+"literal"` concatenation, refusing anything else."""
    out, pos, expr = [], 0, expr.strip()
    while pos < len(expr):
        m = _TOKEN.match(expr, pos)
        if not m or m.end() == pos:
            raise ValueError(f"not a plain concatenation at {expr[pos:pos + 40]!r}")
        literal, name, _plus = m.groups()
        if literal is not None:
            out.append(literal)
        elif name is not None:
            if name not in env:
                raise KeyError(name)
            out.append(str(env[name]))
        pos = m.end()
    return "".join(out)


def branches(src):
    """The capped and uncapped note expressions, as the page ships them."""
    rel = re.search(
        r'\.text\(capped\?(?P<capped>"Showing ".*?)\s*:(?P<uncapped>"Showing the ".*?)\);',
        src, re.S)
    empty = re.search(
        r'\.text\(network\?\(g\.capped\?(?P<capped>".*?)\s*:(?P<uncapped>"No relationships[^"]*")\)',
        src, re.S)
    full = re.search(
        r'if\(graphMode!=="network"&&capped\)\s*box\.append\("div"\)\.attr\("class","why"\)\s*'
        r'\.text\((?P<capped>".*?)\);',
        src, re.S)
    return rel, empty, full


def relationship_count(payload):
    """drawGraph's network-mode filter: shown entities that an edge in the payload connects."""
    connected = set()
    for e in payload["edges"]:
        connected.update((e["source_entity_id"], e["target_entity_id"]))
    return sum(1 for n in payload["nodes"] if n["entity_id"] in connected)


def notes(src, payload, entities_total):
    """Render every Entity Graph note the page would show for `payload`."""
    rel, empty, full = branches(src)
    for name, m in (("relationship", rel), ("empty", empty), ("full", full)):
        if m is None:
            raise AssertionError(f"the {name} note's capped/uncapped branch is not in the page")
    env = {
        "nodeCount": relationship_count(payload),
        "STATS.entities_total": entities_total,
        "graphPayload.related_total": payload["related_total"],
        "graphPayload.nodes.length": len(payload["nodes"]),
        "graphPayload.total": payload["total"],
        "g.related_total": payload["related_total"],
        "g.nodes.length": len(payload["nodes"]),
    }
    pick = "capped" if payload["capped"] else "uncapped"
    out = {
        "relationship": render(rel.group(pick), env),
        "empty": render(empty.group(pick), env),
    }
    # The full-population note exists only on the capped branch.
    if payload["capped"]:
        out["full"] = render(full.group("capped"), env)
    return out


def problems(src):
    """Every way `src` fails the capped/uncapped wording contract; empty when it holds."""
    found = []
    try:
        capped = model_with(WIDE + NARROW, EDGES).graph(cap=CAP)
        lonely = model_with(WIDE + NARROW, EDGES[1:]).graph(cap=CAP)
        c = notes(src, capped, capped["total"])
        e = notes(src, lonely, lonely["total"])
        shown = relationship_count(capped)
        total = capped["total"]
        if f"Showing {shown} of the {RELATED} entities that have relationships" not in c["relationship"]:
            found.append("capped relationship note does not name the shown count as part of "
                         f"related_total: {c['relationship']!r}")
        if f"capped at {CAP} of {total} entities" not in c["relationship"]:
            found.append(f"capped relationship note does not state the cap: {c['relationship']!r}")
        if f"Showing {CAP} of {total} entities" not in c["full"] or \
                "entities spanning the most sources are kept first" not in c["full"]:
            found.append(f"capped full note does not state the cap and ranking: {c['full']!r}")
        if f"None of the {RELATED - 2} entities with relationships are among the {CAP} shown." \
                != e["empty"]:
            found.append(f"capped empty note does not place the related entities outside the "
                         f"cap: {e['empty']!r}")
        for name, text in list(c.items()) + [("empty", e["empty"])]:
            if re.search(r"\ball\b", text):
                found.append(f"capped {name} note claims 'all': {text!r}")

        uncapped = notes(src, {"nodes": [{"entity_id": i} for i in range(286)],
                               "edges": [{"source_entity_id": i, "target_entity_id": i + 1}
                                         for i in range(0, 286, 2)],
                               "total": 7084, "capped": False, "related_total": 286}, 7084)
        if uncapped["relationship"] != UNCAPPED_RELATIONSHIP_NOTE:
            found.append(f"uncapped relationship note changed: {uncapped['relationship']!r}")
        if uncapped["empty"] != UNCAPPED_EMPTY_NOTE:
            found.append(f"uncapped empty note changed: {uncapped['empty']!r}")
        if any("capped" in t for t in uncapped.values()):
            found.append("an uncapped payload yields capped wording")
    except (AssertionError, KeyError, ValueError) as exc:
        found.append(str(exc))

    if not re.search(r"graphPayload=g;", src):
        found.append("drawGraph does not hand its payload to addGraphControls")
    if not re.search(r"const capped=!!graphPayload\.capped;", src):
        found.append("addGraphControls does not read the payload's own `capped`")
    if not re.search(r'if\(graphMode!=="network"&&capped\)', src):
        found.append("the full-population note is not gated on `capped` alone")
    return found


class TheGraphPayloadCarriesRelatedTotal(unittest.TestCase):

    def test_a_capped_payload_counts_related_entities_before_the_cap(self):
        graph = model_with(WIDE + NARROW, EDGES).graph(cap=CAP)
        self.assertTrue(graph["capped"])
        self.assertEqual(12, graph["total"])
        self.assertEqual(CAP, len(graph["nodes"]))
        self.assertEqual(RELATED, graph["related_total"],
                         "related_total must count the whole datastore, not the capped subset")
        self.assertLess(relationship_count(graph), graph["related_total"],
                        "the fixture no longer drops related entities, so it proves nothing")

    def test_an_uncapped_payload_carries_the_same_count(self):
        graph = model_with(WIDE + NARROW, EDGES).graph()
        self.assertFalse(graph["capped"])
        self.assertEqual(RELATED, graph["related_total"])
        self.assertEqual(RELATED, relationship_count(graph))

    def test_no_relationships_means_zero(self):
        self.assertEqual(0, model_with(WIDE).graph(cap=2)["related_total"])


class TheNotesStateTheCap(unittest.TestCase):

    def test_the_shipped_page_meets_the_contract(self):
        self.assertEqual([], problems(SOURCE))

    def test_the_uncapped_wording_is_unchanged(self):
        rel, empty, _ = branches(SOURCE)
        self.assertIn(
            '"Showing the "+nodeCount+" entities that have relationships, of "+\n'
            '            STATS.entities_total+" total — the full population is too dense to read '
            'at this "+\n            "scale. Uncheck the toggle above to show them all."',
            rel.group("uncapped"))
        self.assertEqual(f'"{UNCAPPED_EMPTY_NOTE}"', empty.group("uncapped"))


class TheChecksFailWhenTheyShould(unittest.TestCase):
    """Negative controls: each mutation reintroduces a variant of the reported defect."""

    def assert_caught(self, old, new, why):
        self.assertIn(old, SOURCE, "the mutation no longer applies; update the control")
        self.assertNotEqual([], problems(SOURCE.replace(old, new, 1)), why)

    def test_counting_the_capped_subset_as_the_population_is_caught(self):
        self.assert_caught('" of the "+graphPayload.related_total+"', '" of the "+nodeCount+"',
                           "the capped note may not name the capped subset as the population")

    def test_offering_all_when_capped_is_caught(self):
        self.assert_caught('"is capped; entities spanning the most sources are kept first."',
                           '"is capped. Uncheck the toggle to show them all."',
                           "a capped note may not claim 'all'")

    def test_dropping_the_cap_from_the_relationship_note_is_caught(self):
        self.assert_caught('"relationships — the graph is capped at "',
                           '"relationships — showing "',
                           "the capped relationship note must state the cap")

    def test_the_old_empty_note_on_a_capped_payload_is_caught(self):
        self.assert_caught('"None of the "+g.related_total+" entities with relationships are among the "+',
                           '"No relationships between entities were found in this data. "+',
                           "a capped empty subgraph says the related entities are outside the cap")

    def test_gating_the_full_note_on_the_threshold_is_caught(self):
        self.assert_caught('if(graphMode!=="network"&&capped)',
                           'if(graphMode!=="network"&&capped&&STATS.entities_total>GRAPH_SUBGRAPH_DEFAULT_ABOVE)',
                           "the full-population note must show whenever capped is true")

    def test_rewording_the_uncapped_branch_is_caught(self):
        self.assert_caught('"scale. Uncheck the toggle above to show them all."',
                           '"scale. Uncheck the toggle above to show more."',
                           "the uncapped wording is pinned by INV-154")

    def test_a_payload_without_the_cap_flag_is_caught(self):
        self.assert_caught("const capped=!!graphPayload.capped;", "const capped=false;",
                           "the notes must read the payload's own capped flag")


if __name__ == "__main__":
    unittest.main()
