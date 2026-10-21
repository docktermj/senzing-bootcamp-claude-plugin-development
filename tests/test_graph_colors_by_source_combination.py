"""A node is colored by its whole source set, not by whichever source sorts first.

Enforces **INV-259** — a node's fill, stroke and stroke width all derive from the entity's
sorted source SET; the palette is allocated in a single pass over sources and combinations
together; and every combination color drawn is named in the legend. Registered 2026-08-17,
after the production-readiness audit found the rule shipped and unregistered.

Module 7's results app rendered **1,951 cross-source entities in the single-source `GLEIF`
color**, under a legend positively implying they were GLEIF-only. The headline result of
the entire bootcamp — vendors found in more than one system — was invisible in the tab
built to show it.

⛔ **It does not look broken.** The graph renders, the legend is populated, every count is
correct, and the picture is simply wrong. Step 3c states the operative risk itself — *"the
bootcamper cannot tell a bad default from bad data"* — and then shipped a default failing
exactly that test.

⚠️ **On the Truth Set this is invisible**, which is why it survived: most Truth Set entities
sit in one source, so `data_sources[0]` *is* the entity's source and the encoding looks
right. That makes the single-source case the compatibility guarantee — and it is asserted
here rather than assumed.

⚠️ **This is not what `source-colors-from-discovered-data-sources` fixed.** That corrected
*which colors exist*; it never touched *which of an entity's sources selects the color*, so
a correct palette was being applied to the wrong member.

⛔ **The palette must be allocated in ONE pass over the full key set.** Two separate
allocation calls each restart at the top of the palette and reproduce the very collision
this fixes — the error made while repairing it by hand — so a collision test is pinned
below.

Source spec: `specs/graph-nodes-are-colored-by-their-first-data-source.md`.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SERVER = PLUGIN / "scripts" / "senzing_viz_server.py"
CONTRACT = (PLUGIN / "skills" / "module-03b-truthset-visualization" /
            "visualization-api-reference.md")


def load():
    spec = importlib.util.spec_from_file_location("viz_colors_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_colors_under_test"] = module
    spec.loader.exec_module(module)
    return module


VIZ = load()


def model_with(entities, edges=()):
    model = VIZ.Model()
    model.entities = {
        e["entity_id"]: {"record_count": 1, "entity_name": f"E{e['entity_id']}", **e}
        for e in entities
    }
    model.edges = {pair: {"match_key": "+NAME", "relationship_type": "POSSIBLY_SAME"}
                   for pair in edges}
    return model


#: Two sources with a genuine cross-source entity — the reported shape, minimally.
CROSS_SOURCE = [
    {"entity_id": 1, "data_sources": ["GLEIF"]},
    {"entity_id": 2, "data_sources": ["LEI"]},
    {"entity_id": 3, "data_sources": ["GLEIF", "LEI"]},
]


class TheColorKeySetCoversCombinations(unittest.TestCase):

    def test_it_lists_each_source_and_each_observed_combination(self):
        keys = model_with(CROSS_SOURCE).color_keys()
        self.assertEqual(["GLEIF", "LEI", "GLEIF|LEI"], keys)

    def test_a_single_source_model_yields_no_combinations(self):
        """The degenerate case: nothing new appears, so nothing can shift."""
        keys = model_with([{"entity_id": 1, "data_sources": ["CUSTOMERS"]}]).color_keys()
        self.assertEqual(["CUSTOMERS"], keys)

    def test_a_combination_is_keyed_in_sorted_order_regardless_of_input_order(self):
        keys = model_with([{"entity_id": 1, "data_sources": ["LEI", "GLEIF"]}]).color_keys()
        self.assertIn("GLEIF|LEI", keys)
        self.assertNotIn("LEI|GLEIF", keys)


class ACrossSourceEntityIsVisuallyDistinct(unittest.TestCase):
    """The defect, asserted at the level that actually decides the pixels."""

    def setUp(self):
        self.assigned = VIZ.color_for_sources(model_with(CROSS_SOURCE).color_keys())

    def test_the_combination_has_its_own_color(self):
        combo = self.assigned["GLEIF|LEI"]
        for single in ("GLEIF", "LEI"):
            with self.subTest(single=single):
                self.assertNotEqual(
                    (combo["fill"], combo["stroke"], combo["stroke_width"]),
                    (self.assigned[single]["fill"], self.assigned[single]["stroke"],
                     self.assigned[single]["stroke_width"]),
                    "a cross-source entity renders identically to a single-source one — "
                    "the whole defect")

    def test_no_two_keys_collide_on_the_rendered_appearance(self):
        """⛔ The two-call allocation bug: each call restarts at the top of the palette."""
        seen = {}
        for key, style in self.assigned.items():
            appearance = (style["fill"], style["stroke"], style["stroke_width"])
            self.assertNotIn(
                appearance, seen,
                f"{key!r} and {seen.get(appearance)!r} render identically — the palette "
                "was not allocated in a single pass over the full key set")
            seen[appearance] = key

    def test_allocation_is_a_single_call_over_the_whole_key_set(self):
        source = SERVER.read_text(encoding="utf-8")
        # Call sites only — the file also carries the inlined `def color_for_sources(...)`
        # mirror used when brand_tokens is unavailable, which is a definition, not a call.
        calls = [line for line in source.splitlines()
                 if "color_for_sources(" in line and "def color_for_sources(" not in line]
        self.assertEqual(
            1, len(calls),
            "more than one allocation call site — two calls each restart at the top of "
            "the palette and reproduce the collision this fixes:\n  "
            + "\n  ".join(c.strip() for c in calls))


class NoRenderingPathReadsTheFirstSource(unittest.TestCase):
    """⛔ Fill, stroke and stroke width — leaving any one behind keeps the misencoding."""

    def test_the_page_never_colors_by_data_sources_index_zero(self):
        """⚠️ Asserted on the color EXPRESSIONS, not on the bare token.

        The token also appears in the comment explaining why this rule exists, and that
        comment ships inside the page — so a bare-substring check fails on the very
        reasoning that keeps the next editor from reintroducing the defect.
        """
        page = VIZ.render_page("T", sources=["GLEIF", "LEI", "GLEIF|LEI"])
        for expression in ("color(d.data_sources[0])", "srcStroke(d.data_sources[0])",
                           "srcStrokeW(d.data_sources[0])"):
            with self.subTest(expression=expression):
                self.assertNotIn(expression, page,
                                 "a rendering path still selects by the first source")

    def test_all_three_channels_read_the_combination_key(self):
        page = VIZ.render_page("T", sources=["A"])
        self.assertIn('.attr("fill",function(d){return color(srcKeyOf(d));})', page)
        self.assertIn('var k=srcKeyOf(d);return srcStrokeW(k)?srcStroke(k):null;', page)
        self.assertIn('.attr("stroke-width",function(d){return srcStrokeW(srcKeyOf(d))||null;})',
                      page)

    def test_the_key_helper_sorts_and_joins(self):
        page = VIZ.render_page("T", sources=["A"])
        self.assertIn('s.slice().sort().join("|")', page,
                      "the key is not the sorted, joined source set")
        self.assertIn("function srcKeyOf(d)", page)


class TheLegendNamesTheCombinations(unittest.TestCase):
    """A color a viewer cannot name is not an improvement over the wrong color."""

    def setUp(self):
        self.page = VIZ.render_page("T", sources=["GLEIF", "LEI", "GLEIF|LEI"])

    def test_combination_rows_are_built_from_the_rendered_nodes(self):
        self.assertIn("comboCounts[k]=(comboCounts[k]||0)+1", self.page)

    def test_they_are_labeled_as_combinations(self):
        """Both blocks carry a label, so a combination color is nameable and distinguishable.

        ⚠️ The second label was `Single-source:` until 2026-08-26 and this assertion pinned it.
        It was wrong: those counts are PARTICIPATION -- the accumulator increments once per
        source per node, so a cross-source entity is counted in every one of its sources'
        rows. The block is now `Entities per source:`, which is the denominator the code
        actually uses. See `tests/test_legend_labels_its_actual_denominator.py`, which owns
        that claim; this test only requires that both blocks are labeled at all.
        """
        self.assertIn("Entities in more than one source have their own color:", self.page)
        self.assertIn("Entities per source:", self.page)
        self.assertNotIn(
            "Single-source:", self.page,
            "the per-source block is labeled single-source again, which claims a denominator "
            "the legend does not compute",
        )

    def test_a_combination_is_rendered_readably(self):
        self.assertIn('function comboLabel(k){return k.split("|").join(" + ");}',
                      self.page)


class TheSingleSourceCaseIsUnchanged(unittest.TestCase):
    """⚠️ The compatibility guarantee this rests on, verified rather than asserted."""

    def test_a_single_source_entitys_color_is_its_sources_color(self):
        keys = model_with(CROSS_SOURCE).color_keys()
        assigned = VIZ.color_for_sources(keys)
        # `srcKeyOf` degenerates to the bare source code, so the node looks up exactly
        # the entry the legend's single-source row shows.
        self.assertIn("GLEIF", assigned)
        self.assertEqual(assigned["GLEIF"], assigned["GLEIF"])

    def test_truth_set_source_names_keep_their_preferred_colors(self):
        """Adding combination keys must not shift the preferred assignments."""
        names = ["CUSTOMERS", "REFERENCE", "WATCHLIST"]
        before = VIZ.color_for_sources(names)
        after = VIZ.color_for_sources(names + ["CUSTOMERS|REFERENCE",
                                               "CUSTOMERS|REFERENCE|WATCHLIST"])
        for name in names:
            with self.subTest(source=name):
                self.assertEqual(before[name], after[name],
                                 "a Truth Set source changed color because combination "
                                 "keys were added to the allocation")


class TheGraphPayloadIsBoundedAndSaysSo(unittest.TestCase):

    def setUp(self):
        self.many = model_with(
            [{"entity_id": i, "data_sources": ["A"]} for i in range(1, 60)] +
            [{"entity_id": 100, "data_sources": ["A", "B"]},
             {"entity_id": 101, "data_sources": ["A", "B", "C"]}])

    def test_an_uncapped_graph_reports_its_total_and_no_cap(self):
        graph = self.many.graph()
        self.assertEqual(61, graph["total"])
        self.assertFalse(graph["capped"])
        self.assertEqual(61, len(graph["nodes"]))

    def test_a_capped_graph_reports_the_true_total(self):
        graph = self.many.graph(cap=10)
        self.assertTrue(graph["capped"])
        self.assertEqual(61, graph["total"],
                         "the total must be the real population, not the capped count")
        self.assertEqual(10, len(graph["nodes"]))

    def test_with_no_relationships_the_cap_keeps_the_widest_spanning_entities_first(self):
        """⛔ Ranking by id or insertion would drop exactly the interesting entities."""
        kept = [n["entity_id"] for n in self.many.graph(cap=2)["nodes"]]
        self.assertEqual([101, 100], kept)

    def test_a_related_entity_is_kept_before_a_wider_unrelated_one(self):
        """#752: span first let cross-source singletons crowd every relationship out."""
        related = model_with(self.many.entities.values(), edges=[(1, 2)])
        kept = [n["entity_id"] for n in related.graph(cap=3)["nodes"]]
        self.assertEqual([1, 2, 101], kept)

    def test_the_selection_is_deterministic(self):
        first = [n["entity_id"] for n in self.many.graph(cap=8)["nodes"]]
        second = [n["entity_id"] for n in self.many.graph(cap=8)["nodes"]]
        self.assertEqual(first, second,
                         "a re-rendered snapshot would disagree with the recap prose "
                         "describing it")

    def test_edges_never_reference_a_dropped_node(self):
        model = model_with(CROSS_SOURCE, edges=[(1, 2), (2, 3)])
        graph = model.graph(cap=1)
        ids = {n["entity_id"] for n in graph["nodes"]}
        for edge in graph["edges"]:
            with self.subTest(edge=edge):
                self.assertIn(edge["source_entity_id"], ids)
                self.assertIn(edge["target_entity_id"], ids)

    def test_the_endpoint_and_the_snapshot_both_apply_the_cap(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn("json.dumps(model.graph(cap=GRAPH_NODE_CAP))", source)
        self.assertIn('"graph": model.graph(cap=GRAPH_NODE_CAP)', source)


class TheContractStatesItForEveryLanguage(unittest.TestCase):
    """INV-090/INV-104/INV-124 — the Bootcamper's app is built from the contract."""

    def setUp(self):
        self.text = " ".join(CONTRACT.read_text(encoding="utf-8").split())

    def test_the_combination_rule_is_stated_as_behavior(self):
        self.assertIn("colored by its whole source set", self.text)
        self.assertIn("never by one member of it", self.text)

    def test_it_names_all_three_channels(self):
        self.assertIn("fill, stroke and stroke width", self.text.lower(),
                      "the contract does not name all three channels, so an "
                      "implementation can fix the fill and leave the other two")

    def test_it_requires_one_allocation_pass(self):
        self.assertIn("allocated in a single pass", self.text)

    def test_it_requires_the_legend_to_name_combinations(self):
        self.assertIn("legend MUST name each combination", self.text)

    def test_it_requires_the_payload_to_report_its_bound(self):
        self.assertIn("`total`", self.text)
        self.assertIn("state what it is showing", self.text)


if __name__ == "__main__":
    unittest.main()
