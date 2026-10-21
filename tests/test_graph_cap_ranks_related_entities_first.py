"""Under the graph cap, entities with relationships are kept first, then by source span.

On a 2026-10-21 Module 7 run the results app's default relationship view showed **2 of 914**
related entities and **1 of 476** edges, with no error (#752). `graph()` ranked by source span
first, 2,098 cross-source entities outnumbered the 1,500-node cap, and every single-source
related entity was dropped before connectivity was considered, along with every edge that had
an end outside the kept set. Above 400 entities the page opens on relationship mode, so the
bootcamp's "wow moment" app opened on an almost empty graph.

⚠️ **The Truth Set (84 entities) never reaches the cap**, so no Module 3b walk can see this;
it appears only on a Bootcamper's own data in Module 7. Hence a fixture built past the cap on
purpose, with the reported run's counts.

What is pinned:

* ``rank_for_graph_cap`` ranks every related entity ahead of every unrelated one, then keeps
  the earlier order: source span, degree, record count, entity id.
* When the related population alone exceeds the cap, the related entities are ranked among
  themselves by that order, edges with a dropped end are dropped, and `related_total` still
  counts the whole datastore.
* With no relationships the ranking is span first, exactly as before.
* On the reported shape, relationship mode shows every related entity and every edge, and the
  encoding self-check (INV-270) is exercised and agrees with the legend.
* The any-language contract states the ranking once, and the full-population note quotes it.

Each guarantee has a negative control: the span-first ranking, put back in place of the
helper, reproduces the reported 2 of 914 and 1 of 476.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "senzing_viz_server.py"
CONTRACT = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
    / "module-03b-truthset-visualization" / "visualization-api-reference.md"
)


def load():
    spec = importlib.util.spec_from_file_location("viz_cap_ranking_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_cap_ranking_under_test"] = module
    spec.loader.exec_module(module)
    return module


VIZ = load()
SOURCE = SERVER.read_text(encoding="utf-8")

#: The full-population note's ranking clause, as the page and the contract both carry it.
RANKING_CLAUSE = "entities with relationships are kept first, then those spanning the most sources"


def node(entity_id, sources, records=1):
    return {"entity_id": entity_id, "entity_name": f"E{entity_id}",
            "data_sources": list(sources), "record_count": records}


def ids(nodes):
    return [n["entity_id"] for n in nodes]


def span_first(nodes, edges):
    """The ranking before #752, for the negative controls: span, degree, records, id."""
    degree = {}
    for a, b in edges:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    return sorted(nodes, key=lambda e: (-len(set(e["data_sources"])),
                                        -degree.get(e["entity_id"], 0),
                                        -e["record_count"], e["entity_id"]))


def model_with(nodes, edges):
    model = VIZ.Model()
    model.entities = {n["entity_id"]: n for n in nodes}
    model.edges = {pair: {"match_key": "+NAME", "relationship_type": "POSSIBLY_SAME"}
                   for pair in edges}
    return model


def reported_shape():
    """The reported run's counts: 2,098 cross-source entities, 914 related, 476 edges.

    Two of the related entities are cross-source and joined to each other; the other 912 are
    single-source, in 437 pairs and two 19-entity rings. Span first keeps the 1,500
    best-connected cross-source entities, which is exactly 2 of 914 and 1 of 476.
    """
    cross = [node(i, ["A", "B"]) for i in range(1, 2099)]
    single = [node(i, ["A"]) for i in range(10001, 10913)]
    edges = [(1, 2)]
    edges += [(10001 + 2 * k, 10002 + 2 * k) for k in range(437)]
    for start in (10875, 10894):
        ring = list(range(start, start + 19))
        edges += [(ring[k], ring[(k + 1) % 19]) for k in range(19)]
    return cross + single, edges


def relationship_view(payload):
    """drawGraph's network-mode filter: the shown entities an edge in the payload connects."""
    connected = set()
    for e in payload["edges"]:
        connected.update((e["source_entity_id"], e["target_entity_id"]))
    return [n for n in payload["nodes"] if n["entity_id"] in connected]


class TheRankingHelper(unittest.TestCase):
    """Direct unit tests of `rank_for_graph_cap`, the one place the ranking lives."""

    def test_a_related_entity_ranks_ahead_of_every_unrelated_one(self):
        nodes = [node(1, ["A", "B", "C"], records=9), node(2, ["A", "B"]), node(3, ["A"]),
                 node(4, ["A"])]
        self.assertEqual([3, 4, 1, 2], ids(VIZ.rank_for_graph_cap(nodes, [(3, 4)])))

    def test_both_ends_of_an_edge_count_as_related(self):
        nodes = [node(1, ["A", "B"]), node(2, ["A"]), node(3, ["A"])]
        self.assertEqual([2, 3, 1], ids(VIZ.rank_for_graph_cap(nodes, [(3, 2)])))

    def test_within_the_related_population_the_earlier_order_holds(self):
        """Span, then degree, then record count, then entity id — the decided tie-breaks."""
        nodes = [node(1, ["A"]), node(2, ["A"], records=5), node(3, ["A"]), node(4, ["A", "B"]),
                 node(5, ["A"]), node(6, ["A"]), node(7, ["A", "B", "C"])]
        edges = [(1, 3), (3, 5), (2, 6), (4, 6), (5, 7)]
        # 7 spans three, 4 two; among the one-source ends 3, 5 and 6 have degree 2, then 2
        # outranks 1 on record count.
        self.assertEqual([7, 4, 3, 5, 6, 2, 1], ids(VIZ.rank_for_graph_cap(nodes, edges)))

    def test_with_no_relationships_it_is_span_first(self):
        nodes = [node(i, ["A"] if i % 3 else ["A", "B"], records=i % 4) for i in range(1, 30)]
        self.assertEqual(ids(span_first(nodes, [])), ids(VIZ.rank_for_graph_cap(nodes, [])))

    def test_the_order_does_not_depend_on_input_order(self):
        """A re-rendered snapshot must not disagree with the recap prose describing it."""
        nodes, edges = reported_shape()
        self.assertEqual(ids(VIZ.rank_for_graph_cap(nodes, edges)),
                         ids(VIZ.rank_for_graph_cap(list(reversed(nodes)), edges[::-1])))

    def test_graph_ranks_through_the_helper(self):
        """The negative controls below patch the helper, so graph() must call it."""
        self.assertIn("nodes = rank_for_graph_cap(nodes, self.edges)[:cap]", SOURCE)


class TheRelatedPopulationAloneExceedsTheCap(unittest.TestCase):
    """The edge case spec revision 1 decided: related entities ranked among themselves."""

    def setUp(self):
        # Eight related one-source entities in a path 1-2-...-8, and two unrelated wide ones.
        nodes = [node(i, ["A"]) for i in range(1, 9)] + [node(20, ["A", "B"]),
                                                         node(21, ["A", "B", "C"])]
        edges = [(i, i + 1) for i in range(1, 8)]
        self.graph = model_with(nodes, edges).graph(cap=5)

    def test_only_related_entities_are_kept(self):
        # The path's inner six have degree 2, its two ends degree 1; id breaks the tie.
        self.assertEqual([2, 3, 4, 5, 6], ids(self.graph["nodes"]))

    def test_edges_with_a_dropped_end_are_dropped(self):
        kept = set(ids(self.graph["nodes"]))
        pairs = [(e["source_entity_id"], e["target_entity_id"]) for e in self.graph["edges"]]
        self.assertEqual([(2, 3), (3, 4), (4, 5), (5, 6)], sorted(pairs))
        self.assertTrue(all(a in kept and b in kept for a, b in pairs))

    def test_the_counts_stay_exact(self):
        self.assertTrue(self.graph["capped"])
        self.assertEqual(10, self.graph["total"])
        self.assertEqual(8, self.graph["related_total"])


class TheReportedCaseShowsEveryRelationship(unittest.TestCase):
    """The acceptance criterion, on the reported run's counts."""

    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.edges = reported_shape()
        cls.payload = model_with(cls.nodes, cls.edges).graph(cap=VIZ.GRAPH_NODE_CAP)
        with mock.patch.object(VIZ, "rank_for_graph_cap", span_first):
            cls.old = model_with(cls.nodes, cls.edges).graph(cap=VIZ.GRAPH_NODE_CAP)

    def test_the_fixture_is_the_reported_shape(self):
        cross = sum(1 for n in self.nodes if len(n["data_sources"]) > 1)
        self.assertGreater(cross, VIZ.GRAPH_NODE_CAP, "cross-source entities must exceed the cap")
        self.assertEqual(914, self.payload["related_total"])
        self.assertEqual(476, len(self.edges))
        self.assertTrue(self.payload["capped"])

    def test_span_first_reproduces_the_report(self):
        """Negative control: without the related-first ranking the defect returns."""
        self.assertEqual(2, len(relationship_view(self.old)))
        self.assertEqual(1, len(self.old["edges"]))

    def test_relationship_mode_shows_every_related_entity_and_edge(self):
        self.assertEqual(VIZ.GRAPH_NODE_CAP, len(self.payload["nodes"]))
        self.assertEqual(914, len(relationship_view(self.payload)))
        self.assertEqual(476, len(self.payload["edges"]))

    def test_the_rest_of_the_cap_still_goes_to_the_widest_entities(self):
        related = set(ids(relationship_view(self.payload)))
        unrelated = [n for n in self.payload["nodes"] if n["entity_id"] not in related]
        self.assertEqual(VIZ.GRAPH_NODE_CAP - 914, len(unrelated))
        self.assertTrue(all(len(n["data_sources"]) == 2 for n in unrelated))

    def test_the_encoding_self_check_is_exercised_and_agrees(self):
        """INV-270: the legend's combination rows equal len(combination_keys), and it ran."""
        check = self.payload["encoding_check"]
        self.assertEqual("ok", check["status"])
        legend_rows = sorted({"|".join(sorted(set(n["data_sources"])))
                              for n in self.payload["nodes"] if len(set(n["data_sources"])) > 1})
        self.assertEqual(len(check["combination_keys"]), len(legend_rows))
        self.assertEqual(["A|B"], check["combination_keys"])


def contract_problems(text):
    """Every way the contract fails "state the ranking once, and the note quotes it"."""
    flat = re.sub(r"\s+", " ", text).replace("**", "")
    found = []
    statements = flat.lower().count("rank candidates with relationships first")
    if statements != 1:
        found.append(f"the ranking is stated {statements} times, not once (INV-300)")
    if "then, within each group, by source span" not in flat:
        found.append("the ranking does not keep source span inside each group")
    if "Rank candidates by source span first" in flat:
        found.append("the span-first ranking is still stated")
    note = re.search(r'"Showing C of M entities — the graph is capped; ([^"]*)\."', flat)
    if note is None or note.group(1) != RANKING_CLAUSE:
        found.append("the full-population note does not quote the ranking clause")
    if "quotes the ranking in \"The graph payload is bounded, and says so\"" not in flat:
        found.append("the note does not point at the section that states the ranking")
    return found


class TheContractStatesTheRankingOnce(unittest.TestCase):
    """INV-090/INV-300: every implementation builds from one statement of the ranking."""

    @classmethod
    def setUpClass(cls):
        cls.text = CONTRACT.read_text(encoding="utf-8")

    def test_the_shipped_contract_holds(self):
        self.assertEqual([], contract_problems(self.text))

    def test_the_page_carries_the_quoted_clause(self):
        page = re.sub(r'"\+\s*"', "", SOURCE)
        self.assertIn(f"is capped; {RANKING_CLAUSE}.", page)

    def test_a_second_statement_is_caught(self):
        doubled = self.text.replace(
            "Shown whenever `capped` is true",
            "Rank candidates with relationships first. Shown whenever `capped` is true", 1)
        self.assertNotEqual([], contract_problems(doubled))

    def test_the_old_ranking_is_caught(self):
        old = self.text.replace("**The ranking under the cap**",
                                "Rank candidates by **source span first**. Then", 1)
        self.assertNotEqual([], contract_problems(old))

    def test_a_note_that_paraphrases_the_ranking_is_caught(self):
        para = self.text.replace("are kept first, then those spanning the most sources.\"",
                                 "come first.\"", 1)
        self.assertNotEqual(self.text, para, "the mutation no longer applies; update the control")
        self.assertNotEqual([], contract_problems(para))


if __name__ == "__main__":
    unittest.main()
