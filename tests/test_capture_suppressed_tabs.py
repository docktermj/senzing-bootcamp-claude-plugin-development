"""A tab the app suppresses is never captured, and never counted as covered.

The visualization hides a tab whose data does not exist rather than rendering an empty
one — Cross-Source needs two data sources, Match Keys and Feature Scores need at least
one multi-record entity (`tabApplicable()` in `senzing_viz_server.py`). It gates the
**nav button**, but the `tab-<id>` pane is emitted unconditionally, and capture's
presence pre-flight looked at the pane. So capture activated the hidden pane and
photographed it.

Observed live on 2026-08-14 (Senzing 4.3.4, 4 records, one data source `VERIFY`,
2 entities / 1 multi-record): six PNGs written for a page showing **five** tabs, with
`dryrun-cross-source.png` holding two lines of explanatory text over ~700px of empty
background, and the manifest reporting `captured_count: 6, not_present: []`.

⛔ **The count is the load-bearing half.** `generate_recap_pdf.py`'s tab-coverage note
takes its denominator from this manifest's `captured` list precisely because a count
derived from the recap itself would be self-certifying. An over-count there is a perfect
score against a set the app never offered — the mirror of the under-count the manifest
was introduced to prevent, and the reason capture must not merely skip the image but
also leave it out of `captured`.

⚠️ **Not an INV-122 violation.** INV-122 forbids saving *the default tab* under another
tab's name; the pane activated here really was Cross-Source and rendered its own correct
message. Those two skips stay separate in the manifest (`not_present` vs
`not_applicable`) because they send a reader to different faults: a drifted tab inventory
versus a dataset that simply has no such data.

`test_python_rule_matches_the_apps_javascript_rule` is the important one: the fix mirrors
a JS rule in Python across a boundary no import can cross, and an unguarded second copy of
a rule is exactly how the pane/button divergence arose in the first place.

Enforces **INV-232** — a suppressed tab is neither captured nor counted in the manifest's
`captured` list, is recorded under `not_applicable` distinctly from `not_present`, and
degrades to "every tab applicable" whenever applicability cannot be determined.

Source spec: `specs/capture-screenshots-captures-tabs-the-app-suppressed.md`.

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

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPT = os.path.join(PLUGIN, "scripts", "capture_screenshots.py")
VIZ_SERVER = os.path.join(PLUGIN, "scripts", "senzing_viz_server.py")


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_module():
    spec = importlib.util.spec_from_file_location("capture_suppressed_mod", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["capture_suppressed_mod"] = module
    spec.loader.exec_module(module)
    return module


ALL_SIX = ["graph", "stats", "matchkeys", "features", "overlap", "probe"]

ONE_SOURCE = {"data_sources_total": 1, "multi_record_entities": 1}
NO_MERGES = {"data_sources_total": 1, "multi_record_entities": 0}
TWO_SOURCES = {"data_sources_total": 2, "multi_record_entities": 1}


def snapshot_page(stats):
    """A page shaped like a real standalone snapshot: data inlined as `const __DATA__=`."""
    payload = {"stats": stats, "graph": {"nodes": []}}
    return (
        '<!doctype html><html><head><title>Viz</title></head><body>\n'
        '<section class="tab" id="tab-graph"></section>\n'
        '<section class="tab" id="tab-stats"></section>\n'
        '<section class="tab" id="tab-matchkeys"></section>\n'
        '<section class="tab" id="tab-features"></section>\n'
        '<section class="tab" id="tab-overlap"></section>\n'
        '<section class="tab" id="tab-probe"></section>\n'
        "<script>const __DATA__=" + json.dumps(payload) + ";var __RECS__=null;</script>\n"
        "</body></html>\n"
    )


class ApplicabilityRule(unittest.TestCase):
    def test_one_data_source_suppresses_cross_source_only(self):
        mod = load_module()
        applicable, suppressed = mod._tabs_applicable(ONE_SOURCE, ALL_SIX)
        self.assertEqual(["overlap"], suppressed)
        self.assertNotIn("overlap", applicable)
        # Match Keys / Feature Scores have a multi-record entity, so they stay.
        for tab in ("matchkeys", "features"):
            self.assertIn(tab, applicable)

    def test_no_multi_record_entities_suppresses_match_keys_and_features(self):
        mod = load_module()
        applicable, suppressed = mod._tabs_applicable(NO_MERGES, ALL_SIX)
        self.assertEqual({"matchkeys", "features", "overlap"}, set(suppressed))
        self.assertEqual(["graph", "stats", "probe"], applicable)

    def test_two_sources_with_a_merge_suppresses_nothing(self):
        mod = load_module()
        applicable, suppressed = mod._tabs_applicable(TWO_SOURCES, ALL_SIX)
        self.assertEqual([], suppressed)
        self.assertEqual(ALL_SIX, applicable)

    def test_absent_stats_suppress_nothing(self):
        """An unreadable page must degrade to the old behavior, never to capturing none."""
        mod = load_module()
        for stats in ({}, None):
            applicable, suppressed = mod._tabs_applicable(stats or {}, ALL_SIX)
            self.assertEqual([], suppressed)
            self.assertEqual(ALL_SIX, applicable)

    def test_python_rule_matches_the_apps_javascript_rule(self):
        """The Python mirror and the app's `tabApplicable` must encode the same rule.

        The defect being fixed *was* two notions of "this tab exists" drifting apart, so
        a second unguarded copy would reintroduce it in a new place. Parse the JS and
        compare the set of gated tabs and the field each is gated on.
        """
        mod = load_module()
        with open(VIZ_SERVER, encoding="utf-8") as handle:
            js = handle.read()
        match = re.search(r"function tabApplicable\(id\)\{(.*?)\n", js, re.S)
        self.assertIsNotNone(match, "tabApplicable() not found in senzing_viz_server.py")
        body = js[match.start():js.index("return true;}", match.start()) + len("return true;}")]

        gated = dict(re.findall(r'id==="(\w+)"\)return \(s\.(\w+)\|\|0\)', body))
        self.assertEqual(
            {"overlap": "data_sources_total",
             "features": "multi_record_entities",
             "matchkeys": "multi_record_entities"},
            gated,
            "the app's tabApplicable() gates a different set of tabs (or on different "
            "stats fields) than capture_screenshots._APPLICABILITY mirrors. Update both.",
        )
        self.assertEqual(
            set(gated), set(mod._APPLICABILITY),
            "capture_screenshots._APPLICABILITY and the app's tabApplicable() disagree "
            "about WHICH tabs are conditional.",
        )
        # And the thresholds: >=2 sources, >0 multi-record.
        self.assertIn('id==="overlap")return (s.data_sources_total||0)>=2', body)
        self.assertTrue(mod._APPLICABILITY["overlap"]({"data_sources_total": 2}))
        self.assertFalse(mod._APPLICABILITY["overlap"]({"data_sources_total": 1}))
        self.assertTrue(mod._APPLICABILITY["features"]({"multi_record_entities": 1}))
        self.assertFalse(mod._APPLICABILITY["features"]({"multi_record_entities": 0}))


class StatsExtraction(unittest.TestCase):
    def test_stats_are_parsed_from_an_inlined_snapshot(self):
        mod = load_module()
        self.assertEqual(
            TWO_SOURCES, mod._page_stats(snapshot_page(TWO_SOURCES), "x.html", False)
        )

    def test_a_page_without_inlined_data_yields_no_stats(self):
        mod = load_module()
        self.assertEqual({}, mod._page_stats("<html><body>hi</body></html>", "x.html", False))

    def test_unparseable_inlined_data_yields_no_stats(self):
        """Malformed data must not raise — capture is best-effort by contract."""
        mod = load_module()
        self.assertEqual(
            {}, mod._page_stats("<script>const __DATA__={oops;</script>", "x.html", False)
        )


class ManifestCounts(unittest.TestCase):
    def test_suppressed_tabs_are_recorded_and_not_counted_as_captured(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            mod.write_manifest(
                mod.Path(tmp), "run", ["graph"], [], [], [], ["overlap"]
            )
            data = read_json(os.path.join(tmp, "run-tabs.json"))

        self.assertEqual(["overlap"], [e["tab"] for e in data["not_applicable"]])
        self.assertEqual([], data["not_present"],
                         "a suppressed tab must not be reported as an absent one")
        self.assertNotIn(
            "overlap", [e["tab"] for e in data["captured"]],
            "a suppressed tab must not appear in `captured` — that list is the recap's "
            "coverage denominator.",
        )
        self.assertEqual(0, data["captured_count"])
        # It was still asked for, so it stays in `requested`.
        self.assertIn("overlap", data["requested"])


class EndToEnd(unittest.TestCase):
    def _run(self, page_text, tabs, name):
        tmp = tempfile.mkdtemp()
        page = os.path.join(tmp, "snap.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(page_text)
        out = os.path.join(tmp, "shots")
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--html", page, "--name", name,
             "--out-dir", out, "--tabs", tabs],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        return proc, out

    def test_every_tab_suppressed_writes_no_image_and_says_why(self):
        """All-suppressed exits 2 before any browser is needed, so this never skips."""
        proc, out = self._run(snapshot_page(NO_MERGES), "matchkeys,features", "sup")
        self.assertEqual(2, proc.returncode)
        self.assertIn("inapplicable to this data", proc.stderr)
        self.assertNotIn(
            "None of the requested tabs exist", proc.stderr,
            "reporting a suppressed tab as a missing one would send the reader after a "
            "drifted tab inventory instead of a dataset with no merges.",
        )
        pngs = [f for f in os.listdir(out) if f.endswith(".png")] if os.path.isdir(out) else []
        self.assertEqual([], pngs)

        data = read_json(os.path.join(out, "sup-tabs.json"))
        self.assertEqual({"matchkeys", "features"},
                         {e["tab"] for e in data["not_applicable"]})
        self.assertEqual(0, data["captured_count"])

    def test_a_retired_slug_is_still_reported_as_absent_not_inapplicable(self):
        """INV-122's existing behavior is unchanged by the new skip."""
        proc, out = self._run(snapshot_page(ONE_SOURCE), "network", "ret")
        self.assertEqual(2, proc.returncode)
        self.assertIn("not present in this visualization", proc.stderr)
        data = read_json(os.path.join(out, "ret-tabs.json"))
        self.assertEqual(["network"], [e["tab"] for e in data["not_present"]])
        self.assertEqual([], data["not_applicable"])


class TheDefaultTabsCommentStatesTheRule(unittest.TestCase):
    """The comment above `DEFAULT_TABS` describes a suppressed tab as INV-232 handles it (#234).

    It said a tab whose data is absent "simply renders its empty state", which is the
    behavior this module exists to forbid. A reader of the helper meets that comment
    before the code, so it is guarded like the code. Negative-controlled by restoring it.
    """

    def test_the_comment_names_not_applicable_and_the_invariant(self):
        with open(SCRIPT, encoding="utf-8") as handle:
            source = handle.read()
        m = re.search(r"((?:^#.*\n)+)DEFAULT_TABS = ", source, re.M)
        self.assertIsNotNone(m, "no comment block sits directly above DEFAULT_TABS")
        comment = " ".join(re.sub(r"(?m)^#\s?", "", m.group(1)).split())
        self.assertIn("`not_applicable`", comment)
        self.assertIn("INV-232", comment)
        self.assertNotRegex(comment, r"(?i)renders its empty state",
                            "the comment says a suppressed tab is captured empty; INV-232 "
                            "says it is not captured at all")


if __name__ == "__main__":
    unittest.main()
