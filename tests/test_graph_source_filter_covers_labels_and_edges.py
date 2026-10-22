"""The Entity Graph's source filter hides an entity's label and edges, not just its circle.

Clicking a source row in the Entity Graph legend filters the view to the other sources. The
handler selected ``'#graph-container .node'`` and toggled `display` on those groups alone --
but an entity's marks live in **three sibling layers**:

* ``<g class="edge">`` per link (the line *and* its match-key text),
* ``<g class="node">`` per datum (the circle),
* ``<g class="node-labels">`` -- one layer for every entity name, moved out of the per-datum
  group by the paint-order fix so a neighbor's circle can never cover a label.

So filtering out a source removed the circles and left the removed entities' **names painted
over empty space** and their **edges running to discs that are no longer drawn** (#676). The
legend said the source was off and the view still showed it.

⛔ **The repair is one predicate, not three selectors.** ``drawLegend``'s click handler owns
*which sources are off* and passes a visibility predicate; ``graphApplySourceFilter`` --
installed by ``drawGraph`` where all three selections are in scope -- owns *which marks that
covers* and applies it to the nodes, their labels and their edges together. A second selector
is how the three drifted apart in the first place, so this file pins that the handler selects
no marks of its own.

⚠️ **An edge is a connection BETWEEN two entities**, so it survives only while **both** of its
endpoints do. Keeping an edge whose far end was filtered out is the "dangling connection" half
of the report, and it is asserted here over every on/off combination of the fixture's sources,
not only the reported one.

⚠️ **Restoring clears the inline style; it never writes a visible value.** The scale-aware
label defaults (``LABEL_AUTO_OFF``) work by adding ``hide-node-labels`` / ``hide-edge-labels``
to the container and letting CSS descend to the text. An inline ``display:inline`` on a label
would win over that rule and bring back every label the threshold had hidden -- the filter
would silently undo the production-scale default. The applier therefore restores with
``null``, and that is pinned below.

⚠️ **What this guard does NOT assert, stated so the gap is loud.** The suite is offline and
stdlib-only (INV-108): there is no browser and no JS engine here. The filter is exercised by
**transcribing the shipped predicate and applier** into Python and running them over a model
the shipped ``Model.graph()`` built -- the same technique
``test_snapshot_records_beyond_the_graph_cap.py`` uses for the Records shim.
``TheTranscriptionMatchesTheShippedCode`` pins the transcription against the source so the two
cannot drift apart silently. That a real browser agrees is a ``dry-run`` phase-2/3 observation,
not something this file can establish.

INV-406 (a filter applies one visibility predicate to every mark a filtered-out item contributes)
names this file as its enforcer. Where Chrome is absent the browser class skips, so on a bare
runner only the transcription and the structural pins establish it; neither establishes that a
Bootcamper's own implementation of the contract obeys it.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import itertools
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SERVER = PLUGIN / "scripts" / "senzing_viz_server.py"
CONTRACT = (
    PLUGIN / "skills" / "module-03b-truthset-visualization"
    / "visualization-api-reference.md"
)


def load():
    spec = importlib.util.spec_from_file_location("viz_source_filter_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_source_filter_under_test"] = module
    spec.loader.exec_module(module)
    return module


VIZ = load()
SOURCE = SERVER.read_text(encoding="utf-8")

#: The two sources of the reported shape, minimally: one entity in each, and one in both.
CRM, WEB = "CRM_CUSTOMERS", "WEBSTORE_ACCOUNTS"

#: entity_id -> its data sources. 5 spans both, which is what makes "any live source" a real
#: question rather than a synonym for "its source".
FIXTURE_ENTITIES = {
    1: [CRM],
    2: [CRM],
    3: [WEB],
    4: [WEB],
    5: [CRM, WEB],
}

#: (a, b) pairs. Every combination is represented: within CRM, within WEB, across the two,
#: and each single-source side joined to the cross-source entity.
FIXTURE_EDGES = ((1, 2), (1, 3), (3, 4), (2, 5), (4, 5))


def build_model():
    model = VIZ.Model()
    for eid, sources in FIXTURE_ENTITIES.items():
        model.entities[eid] = {
            "entity_id": eid,
            "entity_name": "Entity %d" % eid,
            "record_count": len(sources),
            "data_sources": sorted(sources),
            "records": [
                {"data_source": s, "record_id": "%s-%d" % (s[:3].lower(), eid),
                 "match_key": "+NAME"}
                for s in sorted(sources)
            ],
        }
    for pair in FIXTURE_EDGES:
        model.edges[pair] = {"match_key": "+NAME+ADDRESS",
                             "relationship_type": "POSSIBLY_SAME"}
    model.records_total = sum(e["record_count"] for e in model.entities.values())
    return model


def rendered(model):
    """`drawGraph`'s own mapping: payload -> the `nodes` and `links` it binds data from."""
    payload = model.graph()
    nodes = [dict(n, id=n["entity_id"]) for n in payload["nodes"]]
    idset = {n["id"] for n in nodes}
    links = [
        {"source": e["source_entity_id"], "target": e["target_entity_id"],
         "match_key": e["match_key"], "rtype": e["relationship_type"]}
        for e in payload["edges"]
        if e["source_entity_id"] in idset and e["target_entity_id"] in idset
    ]
    return nodes, links


# --- transcription of the shipped client code ----------------------------------------------
# Pinned against the shipped source by TheTranscriptionMatchesTheShippedCode below.

def legend_predicate(off, srcs):
    """`drawLegend`'s click handler, in Python: which ENTITIES the live sources keep."""
    any_off = any(bool(off.get(x)) for x in srcs)

    def visible(d):
        if not any_off:
            return True
        return any(not off.get(x) for x in (d.get("data_sources") or []))

    return visible


def apply_source_filter(nodes, links, visible):
    """`graphApplySourceFilter`, in Python: the inline `display` written on every mark.

    `None` is d3's "remove the inline style", which is how a restored mark goes back to being
    governed by the container's `hide-node-labels` / `hide-edge-labels` class.
    """
    by_id = {n["id"]: n for n in nodes}

    def vis(d):
        return bool(d) and visible(d)

    def endpoint_of(value):
        # forceLink rewrites source/target from an id to the node datum; both resolve.
        return value if isinstance(value, dict) else by_id.get(value)

    def disp(d):
        return None if vis(d) else "none"

    return {
        "node": {n["id"]: disp(n) for n in nodes},
        "label": {n["id"]: disp(n) for n in nodes},
        "edge": {
            (link["source"] if not isinstance(link["source"], dict) else link["source"]["id"],
             link["target"] if not isinstance(link["target"], dict) else link["target"]["id"]):
            (None if (vis(endpoint_of(link["source"])) and vis(endpoint_of(link["target"])))
             else "none")
            for link in links
        },
    }


def apply_node_layer_only(nodes, links, visible):
    """⛔ The DEFECT, transcribed: `d3.selectAll("#graph-container .node")` and nothing else.

    Kept as the negative control. A fixture that cannot tell this apart from the repair proves
    nothing, so every acceptance assertion below is also run against this and must fail.
    """
    def disp(d):
        return None if visible(d) else "none"

    return {
        "node": {n["id"]: disp(n) for n in nodes},
        "label": {n["id"]: None for n in nodes},
        "edge": {(link["source"], link["target"]): None for link in links},
    }


def as_objects(nodes, links):
    """`links` after forceLink has substituted the node datum for each endpoint id."""
    by_id = {n["id"]: n for n in nodes}
    return [dict(link, source=by_id[link["source"]], target=by_id[link["target"]])
            for link in links]


def filter_to(off_sources):
    """Render the fixture with `off_sources` switched off, and return the display map."""
    nodes, links = rendered(build_model())
    off = {s: True for s in off_sources}
    visible = legend_predicate(off, [CRM, WEB])
    return nodes, links, apply_source_filter(nodes, links, visible)


def hidden_entities(display):
    return {eid for eid, value in display["node"].items() if value == "none"}


class TheFixtureIsTheReportedShape(unittest.TestCase):
    """Without this the rest of the file proves nothing about the reported case."""

    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.links = rendered(build_model())

    def test_two_sources_are_present(self):
        self.assertEqual({CRM, WEB},
                         {s for n in self.nodes for s in n["data_sources"]})

    def test_one_entity_spans_both_sources(self):
        spanning = [n["id"] for n in self.nodes if len(n["data_sources"]) == 2]
        self.assertEqual([5], spanning)

    def test_every_edge_survived_the_payload(self):
        self.assertEqual(len(FIXTURE_EDGES), len(self.links))

    def test_labels_are_enabled_at_this_size(self):
        """"with labels enabled" is the reported precondition — grounded, not assumed."""
        auto_off = re.search(r"const LABEL_AUTO_OFF=(\d+);", SOURCE)
        self.assertTrue(auto_off, "LABEL_AUTO_OFF is gone from the shipped source")
        self.assertLessEqual(
            len(self.nodes), int(auto_off.group(1)),
            "the fixture is above the node count at which both label sets default OFF, so it "
            "would not exercise the ghost-label case at all",
        )


class FilteringOutOneSourceLeavesNoGhostLabels(unittest.TestCase):
    """Acceptance criterion 1 and 3: the labels go with the circles."""

    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.links, cls.display = filter_to([CRM])

    def test_the_right_entities_are_hidden(self):
        """CRM-only entities go; the cross-source entity stays on its live source."""
        self.assertEqual({1, 2}, hidden_entities(self.display))

    def test_no_hidden_entity_keeps_a_label(self):
        for eid in hidden_entities(self.display):
            with self.subTest(entity=eid):
                self.assertEqual(
                    "none", self.display["label"][eid],
                    "entity %d's circle is hidden and its name is still painted — the ghost "
                    "label this issue reports" % eid,
                )

    def test_every_visible_entity_keeps_its_label(self):
        for eid, value in self.display["node"].items():
            if value is None:
                with self.subTest(entity=eid):
                    self.assertIsNone(
                        self.display["label"][eid],
                        "a visible entity lost its name: the filter over-reached",
                    )

    def test_a_visible_label_carries_no_inline_display(self):
        """`None` is the removal — anything else overrides the container's hide rule."""
        self.assertEqual(
            {None, "none"}, set(self.display["label"].values()),
            "the applier wrote a display value other than the restore (`null`) and the hide "
            "(`none`); a visible value on a label beats the container's hide rule and brings "
            "back every label the scale-aware default had hidden",
        )


class FilteringOutOneSourceLeavesNoDanglingConnections(unittest.TestCase):
    """Acceptance criterion 1 and 3: the edges go with the entities they reach."""

    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.links, cls.display = filter_to([CRM])

    def test_an_edge_to_a_hidden_entity_is_hidden(self):
        gone = hidden_entities(self.display)
        for (a, b), value in self.display["edge"].items():
            if a in gone or b in gone:
                with self.subTest(edge=(a, b)):
                    self.assertEqual(
                        "none", value,
                        "edge %s runs to an entity the filter removed — a line to a disc that "
                        "is no longer drawn" % ((a, b),),
                    )

    def test_an_edge_between_two_visible_entities_survives(self):
        gone = hidden_entities(self.display)
        survivors = [pair for pair, value in self.display["edge"].items() if value is None]
        self.assertTrue(survivors, "the filter removed every edge, which is not the rule")
        for a, b in survivors:
            with self.subTest(edge=(a, b)):
                self.assertNotIn(a, gone)
                self.assertNotIn(b, gone)

    def test_the_cross_source_entity_keeps_its_live_side(self):
        """5 is in both sources; with CRM off its WEB edge must still be drawn."""
        self.assertIsNone(self.display["edge"][(4, 5)])
        self.assertEqual("none", self.display["edge"][(2, 5)])


class NoCombinationOfSourcesLeavesAMarkBehind(unittest.TestCase):
    """The rule, over every on/off state — not only the one the report happened to hit."""

    def test_no_visible_edge_ever_reaches_a_hidden_entity(self):
        for size in range(len({CRM, WEB}) + 1):
            for off in itertools.combinations(sorted({CRM, WEB}), size):
                with self.subTest(off=off):
                    _, _, display = filter_to(list(off))
                    gone = hidden_entities(display)
                    dangling = [pair for pair, value in display["edge"].items()
                                if value is None and (pair[0] in gone or pair[1] in gone)]
                    self.assertEqual([], dangling)

    def test_no_hidden_entity_ever_keeps_a_label(self):
        for size in range(len({CRM, WEB}) + 1):
            for off in itertools.combinations(sorted({CRM, WEB}), size):
                with self.subTest(off=off):
                    _, _, display = filter_to(list(off))
                    ghosts = [eid for eid in hidden_entities(display)
                              if display["label"][eid] is None]
                    self.assertEqual([], ghosts)

    def test_an_endpoint_resolves_before_and_after_force_link(self):
        """forceLink swaps each endpoint id for the node datum mid-life; both must work."""
        nodes, links = rendered(build_model())
        visible = legend_predicate({CRM: True}, [CRM, WEB])
        by_id = apply_source_filter(nodes, links, visible)["edge"]
        by_object = apply_source_filter(nodes, as_objects(nodes, links), visible)["edge"]
        self.assertEqual(by_id, by_object)


class MultiSourceSemanticsAndResetAreCoherent(unittest.TestCase):
    """Acceptance criterion 4, asserted rather than assumed."""

    def test_a_cross_source_entity_survives_while_any_source_is_on(self):
        for off in ([CRM], [WEB]):
            with self.subTest(off=off):
                _, _, display = filter_to(off)
                self.assertIsNone(display["node"][5])
                self.assertIsNone(display["label"][5])

    def test_a_cross_source_entity_goes_when_every_source_is_off(self):
        _, _, display = filter_to([CRM, WEB])
        self.assertEqual({1, 2, 3, 4, 5}, hidden_entities(display))
        self.assertEqual({"none"}, set(display["label"].values()))
        self.assertEqual({"none"}, set(display["edge"].values()))

    def test_turning_every_row_back_on_restores_the_whole_view(self):
        """The reset: `off` with no live entry means `anyOff` is false for every mark."""
        nodes, links = rendered(build_model())
        off = {CRM: True}
        off[CRM] = False  # the second click on the same row
        display = apply_source_filter(nodes, links, legend_predicate(off, [CRM, WEB]))
        for layer in ("node", "label", "edge"):
            with self.subTest(layer=layer):
                self.assertEqual({None}, set(display[layer].values()),
                                 "%s marks kept an inline display after the reset" % layer)

    def test_the_untouched_view_writes_nothing(self):
        nodes, links = rendered(build_model())
        display = apply_source_filter(nodes, links, legend_predicate({}, [CRM, WEB]))
        self.assertEqual({None}, set(display["node"].values()) | set(display["label"].values())
                         | set(display["edge"].values()))


class TheFixtureDetectsTheDefect(unittest.TestCase):
    """⛔ Anti-vacuity (INV-265): the pre-fix behavior must FAIL these assertions."""

    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.links = rendered(build_model())
        cls.display = apply_node_layer_only(
            cls.nodes, cls.links, legend_predicate({CRM: True}, [CRM, WEB])
        )

    def test_the_old_handler_hid_the_circles(self):
        self.assertEqual({1, 2}, hidden_entities(self.display))

    def test_the_old_handler_left_ghost_labels(self):
        ghosts = [eid for eid in hidden_entities(self.display)
                  if self.display["label"][eid] is None]
        self.assertEqual(
            [1, 2], sorted(ghosts),
            "the node-layer-only transcription no longer reproduces the reported ghost labels, "
            "so the assertions above would pass against the defect too",
        )

    def test_the_old_handler_left_dangling_edges(self):
        gone = hidden_entities(self.display)
        dangling = sorted(pair for pair, value in self.display["edge"].items()
                          if value is None and (pair[0] in gone or pair[1] in gone))
        self.assertEqual([(1, 2), (1, 3), (2, 5)], dangling)


class TheTranscriptionMatchesTheShippedCode(unittest.TestCase):
    """The transcription is only evidence while it is the shipped code's shape."""

    @classmethod
    def setUpClass(cls):
        start = SOURCE.index("graphApplySourceFilter=function(visible){")
        cls.applier = SOURCE[start:SOURCE.index("\n  };", start)]
        legend = SOURCE.index("function drawLegend(nodes)")
        cls.legend = SOURCE[legend:SOURCE.index("function openModal", legend)]

    def test_the_applier_covers_exactly_the_three_layers(self):
        for mark, why in (
            ('node.style("display",disp);', "the circles"),
            ('label.style("display",disp);', "the names, in their own paint layer"),
            ('edge.style("display",function(d){', "the lines and their match-key text"),
        ):
            with self.subTest(mark=mark):
                self.assertIn(mark, self.applier,
                              "the one applier no longer reaches %s" % why)

    def test_the_applier_restores_by_removing_the_inline_style(self):
        self.assertIn(
            'const disp=function(d){return vis(d)?null:"none";};', self.applier,
            "a restored mark must get `null` — removing the inline style — so the container's "
            "`hide-node-labels` class still governs it",
        )
        for forbidden in ('"inline"', '"block"', '"inherit"', '"initial"'):
            with self.subTest(value=forbidden):
                self.assertNotIn(forbidden, self.applier)

    def test_an_edge_needs_both_of_its_endpoints(self):
        self.assertIn(
            "return (vis(endpointOf(d.source))&&vis(endpointOf(d.target)))?null:\"none\";",
            self.applier,
            "an edge kept while one endpoint is filtered out is the dangling connection",
        )

    def test_the_endpoint_resolver_accepts_an_id_or_a_datum(self):
        self.assertIn(
            'function endpointOf(v){return (v&&typeof v==="object")?v:nodeById[v];}', SOURCE,
            "forceLink substitutes the node datum for the endpoint id, so a resolver that "
            "handles only one form breaks depending on when the filter is clicked",
        )

    def test_the_legend_delegates_instead_of_selecting_marks(self):
        self.assertIn("graphApplySourceFilter(function(d){", self.legend,
                      "the legend row no longer hands its predicate to the one applier")
        self.assertNotIn(
            '#graph-container .node"', SOURCE,
            "a selector for the node layer is back in the source: that is the defect — it "
            "reaches one of the three sibling layers an entity draws into",
        )

    def test_the_legend_predicate_is_what_the_transcription_models(self):
        self.assertIn("const anyOff=srcs.some(function(x){return off[x];});", self.legend)
        self.assertIn("if(!anyOff)return true;", self.legend)
        self.assertTrue(
            re.search(r"\(d\.data_sources\|\|\[\]\)\.some\(function\(x\)\{return !off\[x\];\}\)",
                      self.legend),
            "participation semantics changed: a node must be kept while ANY of its sources is "
            "still on, or a cross-source entity vanishes with the first source switched off",
        )

    def test_the_applier_is_installed_after_the_selections_exist(self):
        """A `const` is not hoisted: installing it earlier throws on the first click."""
        for earlier in ('const node=root.append("g")',
                        'const labelLayer=root.append("g").attr("class","node-labels")',
                        "const label=labelLayer.selectAll"):
            with self.subTest(after=earlier):
                self.assertLess(SOURCE.index(earlier),
                                SOURCE.index("graphApplySourceFilter=function(visible){"))

    def test_the_applier_is_cleared_on_every_redraw(self):
        self.assertIn("let graphApplySourceFilter=null;", SOURCE,
                      "the hook must be declared at top level: `drawLegend` is outside "
                      "`drawGraph`'s closure")
        self.assertIn(
            "if(graphSim){graphSim.stop();graphSim=null;}", SOURCE)
        after = SOURCE.index("if(graphSim){graphSim.stop();graphSim=null;}")
        self.assertIn(
            "graphApplySourceFilter=null;",
            SOURCE[after:after + 500],
            "a redraw must clear the applier with the simulation, or a legend row clicked "
            "after a mode switch styles detached DOM from the previous render",
        )


class TheSurroundingGuaranteesAreUnchanged(unittest.TestCase):
    """Acceptance criterion 2 — the label layer and the scale-aware toggle keep working."""

    def test_the_labels_still_have_their_own_paint_layer(self):
        self.assertRegex(SOURCE, r'root\.append\("g"\)\.attr\("class","node-labels"\)')
        self.assertLess(SOURCE.index('const node=root.append("g")'),
                        SOURCE.index('root.append("g").attr("class","node-labels")'))

    def test_the_hide_rule_still_covers_both_label_groups(self):
        self.assertIn(
            ".hide-node-labels .node text,.hide-node-labels .node-labels text{display:none}",
            SOURCE,
        )
        self.assertIn(".hide-edge-labels .edge text{display:none}", SOURCE)

    def test_the_scale_aware_toggle_still_targets_the_container(self):
        for cls in ("hide-node-labels", "hide-edge-labels"):
            with self.subTest(cls=cls):
                self.assertIn('classList.toggle("%s",auto)' % cls, SOURCE)

    def test_the_relationship_legends_own_filter_is_untouched(self):
        """Network mode filters by relationship type and is a different legend."""
        self.assertIn(
            'edge.style("display",function(d){return (!anyOff||!roff[d.rtype])?null:"none";});',
            SOURCE,
        )


class TheRuleIsMirroredForOtherLanguages(unittest.TestCase):
    """INV-002/INV-090: a rule binding the Bootcamper's build is stated as behavior."""

    @classmethod
    def setUpClass(cls):
        cls.contract = CONTRACT.read_text(encoding="utf-8")

    def test_the_contract_is_actually_the_contract(self):
        """Anti-vacuity: a regex over an empty read proves nothing."""
        self.assertGreater(len(self.contract), 10000)
        self.assertIn("Truth Set Visualization: API Reference", self.contract)

    def test_the_contract_requires_one_predicate_across_every_layer(self):
        self.assertRegex(
            self.contract,
            r"(?i)a filter applies to every mark",
            "a build in another language reproduces the ghost labels unless the rule is "
            "normative in the language-agnostic reference, not just in the Python one",
        )

    def test_the_contract_names_both_halves_of_the_defect(self):
        for needle, why in (
            (r"(?i)ghost label", "the labels left painted over empty space"),
            (r"(?i)both of its endpoints", "the edges left running to a marker nobody draws"),
        ):
            with self.subTest(needle=needle):
                self.assertRegex(self.contract, needle, why)

    def test_the_contract_states_how_a_mark_is_restored(self):
        self.assertRegex(
            self.contract, r"(?i)clearing the per-mark visibility",
            "restoring with a visible value overrides the container-class hide and undoes the "
            "scale-aware label default — the trap needs naming, not just the rule",
        )


def find_chrome():
    for cand in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(cand)
        if path:
            return path
    return None


def fixture_page(post_script):
    """The fixture served as the real page, with `post_script` injected before `</body>`."""
    payload = VIZ._snapshot_payload(build_model())
    shim = ("<script>const __DATA__=" + VIZ._script_json(payload) + ";"
            "window.fetch=function(u){var p=u.split('?')[0].replace('/api/','');"
            "if(p==='search'){return Promise.resolve({json:function(){"
            "return Promise.resolve({results:[]});}});}"
            "return Promise.resolve({json:function(){"
            "return Promise.resolve(__DATA__[p]);}});};</script>")
    page = VIZ.render_page("Source filter fixture", data_shim=shim, sources=[CRM, WEB])
    return page.replace("</body>", post_script + "</body>", 1)


#: Click the per-source legend row. Selected by its title, because the COMBINATION row's text
#: contains both source names and a text match would hit it too.
def click_script(times):
    return ('<script>setTimeout(function(){'
            'var row=document.querySelector(\'#graph-container .legend .row'
            '[title="Show only ' + CRM + ' (click again to restore)"]\');'
            'if(!row)return;'
            'for(var i=0;i<' + str(times) + ';i++){'
            'row.dispatchEvent(new MouseEvent("click",{bubbles:true}));}'
            'document.title="FILTERED";},400);</script>')


#: ⛔ The defect, injected into the shipped page: the handler as it was, reaching the node
#: layer and nothing else. The browser case has to be able to tell the two apart.
OLD_FILTER_SCRIPT = ('<script>setTimeout(function(){'
                     'var off={};off["' + CRM + '"]=true;'
                     'd3.selectAll("#graph-container .node").style("display",function(d){'
                     'var keep=(d.data_sources||[]).some(function(x){return !off[x];});'
                     'return keep?null:"none";});'
                     'document.title="FILTERED";},400);</script>')


@unittest.skipUnless(find_chrome(), "no headless Chrome/Chromium available")
class TheRenderedPageHidesEveryMarkOfAFilteredEntity(unittest.TestCase):
    """The DOM/render regression the issue asks for, driven through a real browser.

    ⚠️ Chrome services requestAnimationFrame only during the initial load, so a force layout
    never settles further here — but node, label and edge **creation** and the legend's click
    handler are synchronous, which is all this measures. Skips where Chrome is absent, as the
    other browser-driven guards in this suite do.
    """

    @classmethod
    def setUpClass(cls):
        cls.chrome = find_chrome()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)

    def dom(self, name, post_script):
        path = Path(self.tmp.name) / name
        path.write_text(fixture_page(post_script), encoding="utf-8")
        result = subprocess.run(
            [self.chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--window-size=1280,800", "--virtual-time-budget=20000",
             "--dump-dom", path.as_uri()],
            capture_output=True, text=True, timeout=180,
        )
        dom = result.stdout
        self.assertIn("<title>FILTERED</title>", dom,
                      "the injected script never ran, so the DOM says nothing")
        return dom

    @staticmethod
    def marks(dom):
        """(hidden nodes, hidden labels, hidden edges) by their INLINE display."""
        labels = re.search(r'<g class="node-labels">(.*?)</g>', dom, re.S)
        return (
            len(re.findall(r'<g class="node"[^>]*display: none', dom)),
            labels.group(1).count("display: none") if labels else -1,
            len(re.findall(r'<g class="edge"[^>]*display: none', dom)),
        )

    def test_the_fixture_draws_every_mark_before_anything_is_filtered(self):
        dom = self.dom("drawn.html", click_script(0))
        self.assertEqual(len(FIXTURE_ENTITIES), dom.count('class="node"'))
        self.assertEqual(len(FIXTURE_EDGES), dom.count('class="edge"'))
        labels = re.search(r'<g class="node-labels">(.*?)</g>', dom, re.S)
        self.assertEqual(len(FIXTURE_ENTITIES), labels.group(1).count("<text "),
                         "labels are not being drawn, so the ghost-label case is untested")
        self.assertEqual((0, 0, 0), self.marks(dom))

    def test_filtering_out_one_source_hides_its_labels_and_edges_too(self):
        """Entities 1 and 2 are CRM-only; edges (1,2), (1,3) and (2,5) reach them."""
        dom = self.dom("filtered.html", click_script(1))
        self.assertEqual((2, 2, 3), self.marks(dom))

    def test_no_label_or_edge_survives_without_its_entity(self):
        """Stated as the rule rather than as the count, over the rendered DOM."""
        dom = self.dom("filtered2.html", click_script(1))
        hidden_nodes, hidden_labels, hidden_edges = self.marks(dom)
        self.assertEqual(hidden_nodes, hidden_labels,
                         "a hidden entity kept its name painted over empty space")
        self.assertGreater(hidden_edges, 0,
                           "every edge reaching a hidden entity is still drawn")

    def test_clicking_the_row_again_restores_the_whole_view(self):
        dom = self.dom("reset.html", click_script(2))
        self.assertEqual((0, 0, 0), self.marks(dom))
        self.assertEqual(len(FIXTURE_ENTITIES), dom.count('class="node"'),
                         "the reset removed marks instead of restoring them")

    def test_the_browser_case_detects_the_defect(self):
        """⛔ Anti-vacuity: the pre-fix handler, injected into the same shipped page."""
        dom = self.dom("defect.html", OLD_FILTER_SCRIPT)
        self.assertEqual(
            (2, 0, 0), self.marks(dom),
            "the node-layer-only handler no longer leaves ghost labels and dangling edges in "
            "a real browser, so the assertions above would pass against the defect too",
        )


if __name__ == "__main__":
    unittest.main()
