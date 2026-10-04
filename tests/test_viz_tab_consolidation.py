"""Tests for the six-tab visualization and the snapshot-rebuild guarantee.

Two coupled changes:

* **Tab consolidation.** "Record Merges" showed a strict subset of what Search / Probe
  shows per entity, and "Relationship Network" was a filtered view of Entity Graph's own
  `/api/graph` data. Both are gone: the relationship subgraph is now an Entity Graph mode
  toggle, and Record Merges' one unique capability — browsing every merged entity with no
  query — is a button on Search / Probe. `/api/merges` is retained because the
  example-query chips and that button both read it.

* **Snapshot rebuild.** The snapshot is built once, before the live server starts, and the
  module purges the Truth Set at close — so a customization made after the build is
  silently lost from the keepsake and cannot be recovered. A change like the tab
  consolidation above is exactly what triggered it: an eight-tab snapshot shipped beside
  recap prose describing six.

The browser-driven test needs headless Chrome and skips without it.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPTS = os.path.join(PLUGIN, "scripts")
SERVER = os.path.join(SCRIPTS, "senzing_viz_server.py")
SKILLS = os.path.join(PLUGIN, "skills")
M3B = os.path.join(SKILLS, "module-03b-truthset-visualization")
CONTRACT = os.path.join(M3B, "visualization-api-reference.md")
PHASE1 = os.path.join(M3B, "phase1-visualization.md")
PHASE2 = os.path.join(M3B, "phase2-close.md")
M7_PHASE1 = os.path.join(
    SKILLS, "module-07-query-visualize-discover", "phase1-query-visualize.md"
)

EXPECTED_TABS = ["graph", "stats", "matchkeys", "features", "overlap", "probe"]
REMOVED_TABS = ["network", "merges"]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def load_server():
    sys.path.insert(0, SCRIPTS)
    spec = importlib.util.spec_from_file_location("viz_server_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_server_under_test"] = module
    spec.loader.exec_module(module)
    return module


def rendered_page(sources=("CUSTOMERS", "REFERENCE", "WATCHLIST")):
    return load_server().render_page("T", sources=list(sources))


def chrome():
    return load_server()._chrome_exe() if hasattr(load_server(), "_chrome_exe") else None


def find_chrome():
    import shutil

    for cand in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(cand)
        if path:
            return path
    return None


class OnlySixTabsAreServed(unittest.TestCase):
    def setUp(self):
        self.page = rendered_page()

    def test_all_tabs_lists_exactly_the_six(self):
        payload = re.search(r"const ALL_TABS=(\[\[.*?\]\]);", self.page).group(1)
        ids = re.findall(r'\["(\w+)","', payload)
        self.assertEqual(EXPECTED_TABS, ids)

    def test_removed_tabs_have_no_section_or_nav_entry(self):
        for tab in REMOVED_TABS:
            with self.subTest(tab=tab):
                self.assertNotIn(f'id="tab-{tab}"', self.page)

    def test_removed_renderers_are_gone(self):
        for symbol in ("drawNetwork", "drawMerges", "network-container", 'id="tt2"'):
            with self.subTest(symbol=symbol):
                self.assertNotIn(symbol, self.page)

    def test_tab_applicable_no_longer_gates_a_network_tab(self):
        self.assertNotIn('if(id==="network")', self.page)

    def test_draw_dispatch_has_no_network_case(self):
        self.assertNotIn('else if(id==="network")', self.page)


class EntityGraphCarriesTheRelationshipMode(unittest.TestCase):
    def setUp(self):
        self.page = rendered_page()

    def test_graph_mode_variable_exists_and_defaults_to_all(self):
        self.assertIn('let graphMode="all"', self.page)

    def test_toggle_is_present_with_the_agreed_label(self):
        self.assertIn("Show only entities with relationships", self.page)

    def test_toggle_is_gated_on_relationships_existing(self):
        """The same condition that used to decide whether the tab appeared at all."""
        self.assertRegex(self.page, r"relationships_total\|\|0\)>0")

    def test_relationship_styling_is_preserved(self):
        """Edge color plus dash, so the types survive a monochrome screenshot."""
        self.assertIn("stroke-dasharray", self.page)
        self.assertIn("function rdash", self.page)

    def test_click_to_filter_legend_is_preserved(self):
        self.assertIn("function drawRelationshipLegend", self.page)
        self.assertIn("Show only this relationship type", self.page)

    def test_empty_relationship_state_is_handled(self):
        self.assertIn("No relationships between entities were found in this data.", self.page)

    def test_stale_simulation_is_stopped_before_a_redraw(self):
        """Toggling re-enters drawGraph; the old sim would otherwise keep ticking."""
        self.assertIn("let graphSim=null", self.page)
        self.assertRegex(self.page, r"if\(graphSim\)\{graphSim\.stop\(\);graphSim=null;\}")


class RecordMergesCapabilityIsPreserved(unittest.TestCase):
    def setUp(self):
        self.page = rendered_page()

    def test_browse_all_button_exists(self):
        self.assertIn("Show all merged entities", self.page)
        self.assertIn("function showAllMerges", self.page)

    def test_merges_endpoint_is_still_served(self):
        module = load_server()
        self.assertIn("/api/merges", read(SERVER))
        # The example-query chips read it too, so removing the route would break them.
        self.assertIn('getJSON("/api/merges")', self.page)

    def test_browse_all_offers_the_same_per_entity_actions(self):
        """Entity surfaces stay consistent (contract: per-entity actions everywhere)."""
        start = self.page.index("function showAllMerges")
        section = self.page[start : start + 1200]
        self.assertIn("addEntityActions", section)


class ContractDescribesSixTabs(unittest.TestCase):
    def setUp(self):
        self.text = read(CONTRACT)

    def test_inventory_has_no_active_row_for_a_removed_tab(self):
        for label in ("**Relationship Network**", "**Record Merges**"):
            with self.subTest(label=label):
                self.assertNotIn(f"| {label} |", self.text)

    def test_removed_ids_are_marked_removed_not_deleted(self):
        """Kept as reserved identifiers so an older snapshot stays capturable."""
        for label in ("Relationship Network — **REMOVED**", "Record Merges — **REMOVED**"):
            with self.subTest(label=label):
                self.assertIn(label, self.text)
        self.assertIn("reserved identifiers, not as tabs to build", self.text)

    def test_deduplication_ruling_is_reversed_explicitly(self):
        self.assertIn('There is **no "Relationship Network" tab.**', self.text)
        self.assertIn("reverses an earlier ruling", self.text)

    def test_record_merges_removal_documents_the_superset_argument(self):
        self.assertIn('There is **no "Record Merges" tab.**', self.text)
        self.assertIn("strict **superset**", self.text)

    def test_entity_graph_row_documents_the_mode_toggle(self):
        # Line-scoped by design (#424): a table row is one line; so is the next test's.
        row = [l for l in self.text.splitlines() if l.startswith("| **Entity Graph**")][0]
        self.assertIn("Show only entities with relationships", row)
        self.assertIn("relationships_total", row)

    def test_search_probe_row_documents_the_browse_all_button(self):
        row = [l for l in self.text.splitlines() if l.startswith("| **Search / Probe**")][0]
        self.assertIn("Show all merged entities", row)
        self.assertIn("/api/merges", row)

    def test_no_prose_still_describes_the_removed_tabs_as_present(self):
        for stale in (
            "the Relationship Network node detail",
            "Applies to both **Entity Graph** and **Relationship Network**",
            "The Record Merges tab and each Search / Probe result carry",
        ):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, self.text)


class SnapshotMustBeRebuiltAfterAnyChange(unittest.TestCase):
    def test_phase_one_has_a_numbered_rebuild_step(self):
        text = read(PHASE1)
        self.assertIn("### 2.4b Any change to the visualization means rebuilding the snapshot", text)

    def test_rebuild_rule_says_re_verifying_the_server_is_not_enough(self):
        text = read(PHASE1)
        self.assertRegex(text, r"(?s)Do not stop at\s*\n?re-verifying the live server")

    def test_rebuild_rule_explains_the_purge_makes_it_permanent(self):
        text = read(PHASE1)
        self.assertRegex(text, r"(?s)purges the Truth Set records")
        self.assertRegex(text, r"(?s)cannot be rebuilt at all")

    def test_completion_gate_compares_snapshot_against_server(self):
        text = read(PHASE2)
        self.assertRegex(text, r"(?s)tab set matches the running\s*\n?>\s*server's current tab set")

    def test_divergence_warns_rather_than_blocking(self):
        text = read(PHASE2)
        self.assertRegex(text, r"(?s)does not block module completion")

    def test_module_seven_carries_the_same_rule(self):
        text = read(M7_PHASE1)
        self.assertRegex(text, r"(?s)rebuild the snapshot and re-capture")


class PurgeIsTheLastAction(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE2)

    def test_ordering_is_stated_explicitly(self):
        self.assertRegex(
            self.text, r"(?s)purge is the LAST action of this module"
        )
        self.assertIn("do not hoist the purge", self.text)

    def test_rebuild_and_capture_precede_termination_and_purge(self):
        """Order in the file is the order the agent executes."""
        order = [
            "1. **Rebuild the snapshot if it is stale.**",
            "2. **Capture any missing screenshots from the live server.**",
            # Anchored without its trailing punctuation: this guard pins the ORDER of the
            # teardown steps, and the heading now continues "— by process id, per …"
            # (`specs/visualization-server-teardown-does-not-record-a-pid.md`).
            "3. **Terminate the web service",
            "4. **Purge the Truth Set data from the database**",
        ]
        positions = []
        for step in order:
            self.assertIn(step, self.text, f"missing step: {step}")
            positions.append(self.text.index(step))
        self.assertEqual(sorted(positions), positions, "teardown steps are out of order")

    def test_search_probe_capture_is_noted_as_needing_the_live_engine(self):
        self.assertRegex(self.text, r"(?s)only show real results against the running engine")


@unittest.skipUnless(find_chrome(), "no headless Chrome/Chromium available")
class RenderedAppBehavesAsSpecified(unittest.TestCase):
    """Static presence is not proof the JS runs; drive the real app.

    Note: Chrome's `--virtual-time-budget` services requestAnimationFrame only during the
    initial load, and d3's force simulation is rAF-driven, so a redraw triggered later never
    *ticks* here — node positions stay unset. Node and legend **creation** is synchronous in
    drawGraph, so counting elements is still sound; only layout coordinates are unavailable.
    Mode is driven by calling drawGraph directly, because an injected script cannot beat
    init()'s microtask-resolved awaits.
    """

    NET_MODE = ('<script>setTimeout(async function(){graphMode="network";'
                'await drawGraph();document.title="NETDONE";},400);</script>')

    @classmethod
    def setUpClass(cls):
        cls.module = load_server()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.chrome = find_chrome()

    def fixture(self, name, pre_script=""):
        srcs = ["CUSTOMERS", "REFERENCE", "WATCHLIST"]
        ents = [
            {"entity_id": 1000 + i, "entity_name": f"Entity {i}",
             "record_count": 1 + (i % 3), "data_sources": [srcs[i % 3]]}
            for i in range(9)
        ]
        edges = [
            {"source_entity_id": 1000, "target_entity_id": 1001,
             "match_key": "+NAME+ADDRESS", "relationship_type": "POSSIBLY_SAME"},
            {"source_entity_id": 1001, "target_entity_id": 1002,
             "match_key": "+NAME-DOB", "relationship_type": "POSSIBLY_RELATED"},
        ]
        merges = [e for e in ents if e["record_count"] > 1]
        payload = {
            "stats": {"records_total": 18, "entities_total": len(ents),
                      "multi_record_entities": len(merges), "cross_source_entities": 2,
                      "relationships_total": len(edges), "data_sources_total": 3,
                      "histogram": {"1": 3, "2": 3, "3": 3, "4+": 0},
                      "bucket_entities": {"1": [], "2": [], "3": [], "4+": []},
                      "sample_entities": merges[:3]},
            "graph": {"nodes": ents, "edges": edges},
            "merges": {"entities": [dict(e, records=[]) for e in merges]},
            "records": {}, "overlap": {"sources": srcs, "matrix": [[3, 1, 0], [1, 3, 0], [0, 0, 3]]},
            "matchkeys": {"keys": []}, "features": {"features": []},
        }
        shim = ("<script>const __DATA__=" + self.module._script_json(payload) + ";"
                "window.fetch=function(u){var p=u.split('?')[0].replace('/api/','');"
                "if(p==='search'){return Promise.resolve({json:function(){"
                "return Promise.resolve({results:[]});}});}"
                "return Promise.resolve({json:function(){"
                "return Promise.resolve(__DATA__[p]);}});};</script>")
        page = self.module.render_page("Fixture", data_shim=shim, sources=srcs)
        if pre_script:
            page = page.replace("</body>", pre_script + "</body>", 1)
        path = Path(self.tmp.name) / name
        path.write_text(page, encoding="utf-8")
        return path

    def dom(self, path):
        result = subprocess.run(
            [self.chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--window-size=1280,800", "--virtual-time-budget=20000",
             "--dump-dom", path.as_uri()],
            capture_output=True, text=True, timeout=120,
        )
        return result.stdout

    def test_nav_renders_exactly_six_buttons(self):
        dom = self.dom(self.fixture("all.html"))
        ids = re.findall(r'id="navbtn-(\w+)"', dom)
        self.assertEqual(EXPECTED_TABS, ids, "nav must show the six tabs, in order")

    def test_mode_toggle_is_rendered_when_relationships_exist(self):
        dom = self.dom(self.fixture("all.html"))
        self.assertIn('id="graph-network-only"', dom)
        self.assertIn("Show only entities with relationships", dom)

    def test_all_mode_draws_every_entity(self):
        dom = self.dom(self.fixture("all.html"))
        self.assertEqual(9, dom.count('class="node"'), "all mode must draw every entity")

    def test_network_mode_draws_only_connected_entities(self):
        """3 of the 9 fixture entities are joined by the 2 relationships."""
        dom = self.dom(self.fixture("net.html", self.NET_MODE))
        self.assertIn("NETDONE", dom, "the network redraw did not complete")
        self.assertEqual(3, dom.count('class="node"'), "network mode must filter to the subgraph")

    def test_network_mode_renders_the_relationship_legend(self):
        dom = self.dom(self.fixture("net2.html", self.NET_MODE))
        self.assertIn("NETDONE", dom, "the network redraw did not complete")
        self.assertIn("possibly the same entity", dom)
        self.assertIn("possibly related", dom)
        self.assertIn("stroke-dasharray", dom)

    def test_all_mode_renders_the_data_source_legend(self):
        """Built FROM the drawn nodes, so an entry cannot exist without matching marks."""
        dom = self.dom(self.fixture("all3.html"))
        for source in ("CUSTOMERS", "REFERENCE", "WATCHLIST"):
            with self.subTest(source=source):
                self.assertIn(f">{source}<", dom)

    def test_browse_all_button_is_rendered(self):
        dom = self.dom(self.fixture("all2.html"))
        self.assertIn('id="show-all-merges"', dom)


if __name__ == "__main__":
    unittest.main()
