"""Tests for per-tab screenshot capture and the caption rules that depend on it.

`capture_screenshots.py` used to vary the browser window size across a single page
load and had no interaction step at all, so every image showed whichever tab was active
by default. It wrote three files and exited 0, so nothing looked wrong — and the recap
shipped three near-identical Entity Graph shots captioned as Cross-Source, Match Keys
and Search / Probe. Tab diversity was never achievable, so those captions could not have
been right.

These tests pin the parts that make the defect unreachable:

* One capture per **tab**, not per viewport, with tab-named output — a tab-named file
  makes a drifting caption structurally hard.
* Tab ids are contract: the helper's inventory and the visualization contract's table
  must agree, so a server in any language (INV-090) stays capturable.
* The offline guarantee (INV-091) and the exit-2 degradation (INV-052/INV-066) survive.
* Search / Probe needs the live server; `--query` against a static snapshot is refused
  rather than producing an empty search box that a caption might describe as results.

The capture backends themselves need a headless browser, so browser-dependent tests skip
when none is installed.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
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
SKILLS = os.path.join(PLUGIN, "skills")
VIZ_REF = os.path.join(
    SKILLS, "module-03b-truthset-visualization", "visualization-api-reference.md"
)
MODULE_COMPLETION = os.path.join(SKILLS, "bootcamp-onboarding", "module-completion.md")
GRADUATION = os.path.join(SKILLS, "graduation", "SKILL.md")

# A page shaped like the contract: `tab-<id>` sections, `navbtn-<id>` buttons, and an
# `activate(id)` function that appears only after an async init — the timing the
# helper's retry loop exists for.
FIXTURE = """<!doctype html><html><head><meta charset="utf-8"><title>Viz</title>
<style>.tab{display:none}.tab.active{display:block}</style></head><body>
<nav id="nav"></nav>
<section class="tab active" id="tab-graph">ENTITY GRAPH</section>
<section class="tab" id="tab-stats">MERGE STATISTICS</section>
<section class="tab" id="tab-overlap">CROSS SOURCE</section>
<script>
var ALL=[["graph","Entity Graph"],["stats","Merge Statistics"],["overlap","Cross-Source"]];
function activate(id){
  document.querySelectorAll(".tab").forEach(function(t){t.className="tab";});
  var el=document.getElementById("tab-"+id); if(el)el.className="tab active";
}
setTimeout(function(){
  var nav=document.getElementById("nav");
  ALL.forEach(function(t){
    var b=document.createElement("button"); b.id="navbtn-"+t[0]; b.textContent=t[1];
    b.onclick=function(){activate(t[0]);}; nav.appendChild(b);
  });
}, 300);
</script></body></html>
"""


def load_module():
    spec = importlib.util.spec_from_file_location("capture_tabs_mod", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["capture_tabs_mod"] = module
    spec.loader.exec_module(module)
    return module


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(args):
    return subprocess.run(
        [sys.executable, SCRIPT] + args, capture_output=True, text=True, cwd=REPO_ROOT
    )


def has_browser():
    return load_module()._chrome_exe() is not None


class TestNoViewportVariants(unittest.TestCase):
    """The root cause: capture varied window size, never the tab."""

    def test_no_viewport_variant_list_remains(self):
        source = read(SCRIPT)
        self.assertNotIn("_VIEWS", source, "per-viewport capture must be gone")
        for stale in ("1280, 1600", "(1024, 768", '"wide"', '"tall"', '"compact"'):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, source)

    def test_output_is_named_after_the_tab(self):
        module = load_module()
        from pathlib import Path

        path = module._out_path(Path("docs/visualizations"), "results_visualization", "overlap")
        self.assertEqual("results_visualization-cross-source.png", path.name)
        self.assertNotRegex(path.name, r"-\d+\.png$", "a numeric suffix carries no content")

    def test_every_tab_has_a_distinct_slug_and_label(self):
        module = load_module()
        slugs = [slug for slug, _label in module.TABS.values()]
        self.assertEqual(len(slugs), len(set(slugs)), "slugs must be unique to map back to tabs")


class TestTabResolution(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_default_tab_set_is_the_applicable_app_tabs(self):
        self.assertEqual(list(self.module.DEFAULT_TABS), self.module.resolve_tabs(""))

    def test_explicit_tabs_keep_their_order_and_deduplicate(self):
        self.assertEqual(
            ["probe", "graph"], self.module.resolve_tabs("probe, graph, probe")
        )

    def test_unknown_tab_is_rejected_with_the_known_ids(self):
        with self.assertRaises(ValueError) as ctx:
            self.module.resolve_tabs("graph,nope")
        self.assertIn("nope", str(ctx.exception))
        self.assertIn("graph", str(ctx.exception))

    def test_url_gets_tab_query_parameter(self):
        url = self.module._tab_url("http://localhost:8080", "stats")
        self.assertIn("tab=stats", url)

    def test_query_is_only_applied_to_the_probe_tab(self):
        self.assertIn("q=Acme", self.module._tab_url("http://localhost:8080", "probe", "Acme"))
        self.assertNotIn("q=Acme", self.module._tab_url("http://localhost:8080", "graph", "Acme"))


class TestArgumentGuards(unittest.TestCase):
    def test_remote_url_is_refused(self):
        result = run(["--url", "http://evil.example.com/"])
        self.assertEqual(1, result.returncode)
        self.assertIn("INV-091", result.stderr)

    def test_query_without_a_live_server_is_refused(self):
        """A snapshot's search box is inert; capturing it as 'results' would mislead."""
        result = run(["--html", "x.html", "--query", "Acme"])
        self.assertEqual(1, result.returncode)
        self.assertIn("--query needs --url", result.stderr)

    def test_unknown_tab_exits_one(self):
        result = run(["--html", "x.html", "--tabs", "bogus"])
        self.assertEqual(1, result.returncode)
        self.assertIn("unknown tab id", result.stderr)

    def test_html_and_url_are_mutually_exclusive(self):
        result = run(["--html", "x.html", "--url", "http://localhost:1/"])
        self.assertEqual(2, result.returncode)  # argparse usage error

    def test_missing_html_file_is_reported(self):
        result = run(["--html", os.path.join(REPO_ROOT, "no-such-file.html")])
        self.assertEqual(1, result.returncode)
        self.assertIn("no such HTML file", result.stderr)


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TestCapturesOneImagePerTab(unittest.TestCase):
    def test_each_tab_produces_a_distinct_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = os.path.join(tmp, "app.html")
            with open(html, "w", encoding="utf-8") as handle:
                handle.write(FIXTURE)
            out = os.path.join(tmp, "out")
            result = run(
                ["--html", html, "--out-dir", out, "--name", "viz", "--tabs", "graph,stats,overlap"]
            )
            self.assertEqual(0, result.returncode, result.stderr)

            expected = {
                "viz-entity-graph.png": "Entity Graph",
                "viz-merge-statistics.png": "Merge Statistics",
                "viz-cross-source.png": "Cross-Source",
            }
            written = sorted(f for f in os.listdir(out) if f.endswith(".png"))
            self.assertEqual(sorted(expected), written)
            # The manifest must name exactly the PNGs written, since the recap's
            # coverage check compares the recap's image links against it.
            with open(os.path.join(out, "viz-tabs.json"), encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(
                sorted(expected), sorted(e["file"] for e in manifest["captured"])
            )

            # Each line reports its tab label, so the caller derives the caption from
            # the capture rather than from its plan.
            for name, label in expected.items():
                with self.subTest(name=name):
                    self.assertIn(label, result.stdout)

            blobs = {}
            for name in written:
                with open(os.path.join(out, name), "rb") as handle:
                    blobs[name] = handle.read()
            self.assertEqual(
                len(blobs),
                len(set(blobs.values())),
                "images are byte-identical — the tab was not switched",
            )

            leftovers = [f for f in os.listdir(tmp) if f.startswith(".app-")]
            self.assertEqual([], leftovers, "injected temp copies must be deleted")


class TestAbsentTabIsNeverCapturedUnderItsName(unittest.TestCase):
    """Found while verifying: without a pre-flight, asking for a tab the app lacks still
    wrote a PNG — of the **default** tab. So `viz-feature-scores.png` contained the
    Entity Graph: a filename lying about its content, which is the whole defect class
    tab-naming exists to prevent."""

    def setUp(self):
        self.module = load_module()

    def test_present_and_absent_tabs_are_split_by_the_markup(self):
        present, absent = self.module._tabs_present(FIXTURE, ["graph", "stats", "features"])
        self.assertEqual(["graph", "stats"], present)
        self.assertEqual(["features"], absent)

    def test_unreadable_source_treats_every_tab_as_present(self):
        """Best-effort: an unreadable page must never block capture."""
        present, absent = self.module._tabs_present("", ["graph", "features"])
        self.assertEqual(["graph", "features"], present)
        self.assertEqual([], absent)

    @unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
    def test_absent_tab_produces_no_file_and_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = os.path.join(tmp, "app.html")
            with open(html, "w", encoding="utf-8") as handle:
                handle.write(FIXTURE)
            out = os.path.join(tmp, "out")
            result = run(["--html", html, "--out-dir", out, "--name", "viz",
                          "--tabs", "graph,features"])
            self.assertEqual(0, result.returncode, result.stderr)
            # PNGs only: the sidecar tab manifest also lands here (see
            # test_recap_tab_coverage.py), and it is not a capture.
            pngs = sorted(f for f in os.listdir(out) if f.endswith(".png"))
            self.assertEqual(["viz-entity-graph.png"], pngs)
            self.assertNotIn("viz-feature-scores.png", os.listdir(out))
            self.assertIn("not present in this visualization", result.stderr)
            # The absent tab must be recorded as absent, not as failed capture:
            # the recap's coverage check would otherwise expect an image for it.
            with open(os.path.join(out, "viz-tabs.json"), encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(
                ["features"], [e["tab"] for e in manifest["not_present"]]
            )
            self.assertEqual([], manifest["failed"])

    def test_no_requested_tab_exists_reports_that_reason_not_a_missing_browser(self):
        """Reporting the wrong reason would be this spec's own defect class."""
        with tempfile.TemporaryDirectory() as tmp:
            html = os.path.join(tmp, "app.html")
            with open(html, "w", encoding="utf-8") as handle:
                handle.write(FIXTURE)
            result = run(["--html", html, "--out-dir", os.path.join(tmp, "out"),
                          "--name", "viz", "--tabs", "features,merges"])
            self.assertEqual(2, result.returncode)
            self.assertIn("None of the requested tabs exist", result.stderr)
            self.assertNotIn("No headless screenshot capability", result.stderr)


class TestNoHeadlessCapabilityDegradesGracefully(unittest.TestCase):
    """INV-052/INV-066: exit 2 and a clear message, never a crash or a blocked module."""

    def test_capture_returns_nothing_when_every_backend_fails(self):
        module = load_module()
        from pathlib import Path

        original = module._BACKENDS
        module._BACKENDS = tuple(lambda url, out: False for _ in original)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                html = Path(tmp) / "app.html"
                html.write_text(FIXTURE, encoding="utf-8")
                written = module.capture(
                    str(html), Path(tmp) / "out", "viz", ["graph", "stats"]
                )
            self.assertEqual([], written)
        finally:
            module._BACKENDS = original

    def test_first_tab_failure_stops_rather_than_retrying_every_tab(self):
        """Walking four dead backends once per tab would multiply the cost pointlessly."""
        module = load_module()
        from pathlib import Path

        calls = []

        def dead(url, out):
            calls.append(url)
            return False

        original = module._BACKENDS
        module._BACKENDS = (dead,)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                html = Path(tmp) / "app.html"
                html.write_text(FIXTURE, encoding="utf-8")
                module.capture(str(html), Path(tmp) / "out", "viz", ["graph", "stats", "overlap"])
            self.assertEqual(1, len(calls), "must stop after the first tab fails outright")
        finally:
            module._BACKENDS = original

    def test_temp_copies_are_removed_even_when_capture_fails(self):
        module = load_module()
        from pathlib import Path

        original = module._BACKENDS
        module._BACKENDS = (lambda url, out: False,)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                html = Path(tmp) / "app.html"
                html.write_text(FIXTURE, encoding="utf-8")
                module.capture(str(html), Path(tmp) / "out", "viz", ["graph"])
                leftovers = [f for f in os.listdir(tmp) if f.startswith(".app-")]
            self.assertEqual([], leftovers)
        finally:
            module._BACKENDS = original


class TestTabIdsAreContract(unittest.TestCase):
    """A server in any language (INV-090) must be capturable, so the ids are contract."""

    def test_contract_documents_the_tab_identifier_table(self):
        self.assertIn("Tab identifiers and deep-linking", read(VIZ_REF))

    def test_helper_inventory_matches_the_contract_table(self):
        module = load_module()
        text = read(VIZ_REF)
        start = text.index("### Tab identifiers and deep-linking")
        section = text[start : text.index("Headline counts belong", start)]
        documented = {}
        # Line-scoped by design (#424): the contract is a table, and a table row is one line.
        for line in section.splitlines():
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 5 and cells[1].startswith("`") and cells[1] != "`Id`":
                documented[cells[1].strip("`")] = cells[4].strip("`")
        self.assertEqual(
            {tab: slug for tab, (slug, _l) in module.TABS.items()},
            documented,
            "the helper's tab inventory and the contract's table must agree",
        )

    def test_contract_requires_activate_and_deep_linking(self):
        text = read(VIZ_REF)
        for hook in ("activate(<id>)", "?tab=<id>", "?q=<text>"):
            with self.subTest(hook=hook):
                self.assertIn(hook, text)

    def test_deep_linking_must_tolerate_an_unknown_tab(self):
        self.assertRegex(
            read(VIZ_REF),
            r"(?s)unknown or non-applicable `tab` value leaves the default tab",
        )


class TestVizServerDeepLink(unittest.TestCase):
    def setUp(self):
        self.source = read(VIZ_SERVER)

    def test_apply_deep_link_exists(self):
        self.assertIn("function applyDeepLink()", self.source)

    def test_it_runs_at_the_end_of_init_after_nav_is_built(self):
        init = re.search(r"async function init\(\)\{[^\n]*", self.source).group(0)
        self.assertIn("applyDeepLink()", init)
        self.assertLess(
            init.index("buildNav()"),
            init.index("applyDeepLink()"),
            "deep-link must apply after buildNav, or the nav button will not exist yet",
        )

    def test_query_without_tab_defaults_to_probe(self):
        self.assertRegex(self.source, r'if\(q!==null&&!tab\)tab="probe";')

    def test_it_guards_on_applicability_and_presence(self):
        self.assertRegex(
            self.source,
            r"tabApplicable\(tab\)&&document\.getElementById\(\"tab-\"\+tab\)",
        )


class TestCaptionRules(unittest.TestCase):
    def test_caption_must_come_from_the_opened_image(self):
        text = read(MODULE_COMPLETION)
        self.assertRegex(
            text,
            r"(?s)Every caption is derived from the capture, never from the plan",
        )
        self.assertRegex(text, r"(?s)open the image and\s*\n?\s*confirm it shows that tab")

    def test_caption_rule_cites_the_invariant_it_extends(self):
        self.assertIn("INV-115", read(MODULE_COMPLETION))

    def test_static_snapshot_probe_must_not_imply_results(self):
        self.assertRegex(
            read(MODULE_COMPLETION),
            r"(?s)never imply a result set that was not captured",
        )

    def test_capture_is_per_tab_not_several_of_one(self):
        # Flattened before matching: the phrase spans a line break in the source, and where
        # that break falls moves whenever the paragraph is re-wrapped. It moved on 2026-07-29
        # (module5-quality-pages-are-branded-visual-deliverables scoped this section to the
        # tabbed app) and failed this assertion on prose that still said exactly the right
        # thing. Assert the requirement, not the current line wrapping.
        self.assertRegex(
            re.sub(r"\s+", " ", read(MODULE_COMPLETION)),
            r"one image per tab.{0,80}never several shots of one",
        )


class TestGraduationVerifiesScreenshots(unittest.TestCase):
    def setUp(self):
        self.text = read(GRADUATION)

    def test_warns_when_a_visualization_module_has_no_image(self):
        """Reworded 2026-07-31: the check widened from zero to any shortfall.

        The old assertion pinned the heading "visualization-producing module with no
        image", which described a check that only fired at **zero** — a section with 4
        of 6 captured tabs passed it. Assert the requirement, not the old heading (the
        same reasoning as `test_module_completion_requires_one_image_per_tab` above).
        Zero is still covered, and is asserted separately below.
        """
        self.assertRegex(
            re.sub(r"\s+", " ", self.text),
            r"(?i)fewer images than were captured|Warn on any \*\*shortfall\*\*",
        )
        self.assertRegex(
            re.sub(r"\s+", " ", self.text),
            r"(?i)not only on zero",
            "a check that fires only at zero is what let 4-of-6 ship",
        )

    def test_the_zero_image_case_is_still_covered(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.text), r"(?i)Zero remains the worst case"
        )

    def test_the_self_referential_count_is_not_offered_as_evidence(self):
        """`embedded N of M images` cannot answer the coverage question at all.

        Its denominator is the recap's own `![](…)` link count, so 4 of 6 captured
        tabs reads `embedded 4 of 4 images`. A prior session cited `embedded 12 of 12`
        to a Bootcamper as proof of completeness while being asked exactly this.
        """
        flat = re.sub(r"\s+", " ", self.text)
        self.assertRegex(flat, r"(?i)Do not use the generator's `embedded N of M images`")
        self.assertRegex(flat, r"(?i)captured tabs reached the recap")

    def test_warns_on_duplicate_images_in_one_section(self):
        self.assertRegex(self.text, r"(?s)byte-identical")

    def test_checks_are_non_blocking(self):
        start = self.text.index("Verify the screenshots the recap actually carries")
        section = self.text[start : start + 1400]
        self.assertIn("non-blocking", section)
        self.assertIn("INV-048", section)

    def test_backfill_derives_captions_from_the_tab_slug(self):
        self.assertRegex(self.text, r"(?s)tab slug gives the caption")


class TestCaptureIsSequentialOnly(unittest.TestCase):
    """`_CURRENT_TAB` is a module global read by `_capture_chrome_cli` to size the
    virtual-time budget. That is correct only while captures run one at a time.
    Parallelizing `capture()`'s loop would apply one tab's budget to another tab's
    capture — an under-settled PNG, not an error, which is the quiet way to break
    INV-122. The precondition is unenforceable by types, so it is pinned here.
    """

    def setUp(self):
        self.mod = load_module()

    def test_the_precondition_is_written_down(self):
        source = read(SCRIPT)
        at = source.index('_CURRENT_TAB = ""')
        window = source[max(0, at - 1200) : at]
        self.assertIn("one at a time", window)
        self.assertIn("INV-122", window)

    def test_the_tab_is_restored_even_when_a_backend_raises(self):
        def explodes(url, out):
            raise RuntimeError("backend died")

        with self.assertRaises(RuntimeError):
            self.mod._capture_one("file:///x", "/tmp/x.png", backend=explodes, tab="graph")
        self.assertFalse(
            self.mod._CAPTURE_IN_FLIGHT,
            "an in-flight flag left set would warn on every later capture",
        )

    def test_a_concurrent_capture_is_reported_not_silently_mis_sized(self):
        """The guard fires on reentrancy — a future parallelization announces itself."""
        seen = []

        def reenters(url, out):
            # Stands in for a second capture running while this one is in flight.
            self.mod._capture_one(
                "file:///second", out, backend=lambda u, o: True, tab="merges"
            )
            seen.append(self.mod._CURRENT_TAB)
            return True

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.mod._capture_one("file:///first", "/tmp/x.png", backend=reenters, tab="graph")
        message = err.getvalue()
        self.assertIn("still in flight", message)
        self.assertIn("INV-122", message)
        # And the hazard the warning describes is real, not hypothetical: the inner
        # capture overwrote the outer one's tab, which is the wrong settle budget.
        self.assertEqual(["merges"], seen)

    def test_a_normal_sequential_run_warns_about_nothing(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            for tab in ("graph", "merges"):
                self.mod._capture_one(
                    "file:///x", "/tmp/x.png", backend=lambda u, o: True, tab=tab
                )
        self.assertEqual("", err.getvalue())


#: A SIX-tab page with `overlap` deliberately absent from the markup. The module-level FIXTURE
#: carries only three tabs, which cannot express criterion 2 of
#: `capture-screenshots-aborts-where-inv-122-says-skip`: "Case B skipping `overlap` while still
#: capturing the other five with slug names".
SIX_TAB_FIXTURE = """<!doctype html><html><head><meta charset="utf-8"><title>Viz</title>
<style>.tab{display:none}.tab.active{display:block}</style></head><body>
<nav id="nav"></nav>
<section class="tab active" id="tab-graph">ENTITY GRAPH</section>
<section class="tab" id="tab-stats">MERGE STATISTICS</section>
<section class="tab" id="tab-matchkeys">MATCH KEYS</section>
<section class="tab" id="tab-features">FEATURE SCORES</section>
<section class="tab" id="tab-probe">SEARCH PROBE</section>
<script>
var ALL=[["graph","Entity Graph"],["stats","Merge Statistics"],["matchkeys","Match Keys"],
         ["features","Feature Scores"],["probe","Search / Probe"]];
function activate(id){
  document.querySelectorAll(".tab").forEach(function(t){t.className="tab";});
  var el=document.getElementById("tab-"+id); if(el)el.className="tab active";
}
setTimeout(function(){
  var nav=document.getElementById("nav");
  ALL.forEach(function(t){
    var b=document.createElement("button"); b.id="navbtn-"+t[0]; b.textContent=t[1];
    b.onclick=function(){activate(t[0]);}; nav.appendChild(b);
  });
}, 300);
</script></body></html>
"""


class TestUnrecognizedIdAndAbsentTabAreDifferentFailures(unittest.TestCase):
    """INV-122's two cases, pinned side by side because one clause used to cover both.

    ⛔ **The maintainer's decision, 2026-09-02: keep the abort, scope the invariant.** INV-122
    said only that "a tab that is not present in the page MUST be skipped and reported", which
    read as forbidding the abort this script performs on an unrecognized id -- so a defensible
    implementation looked like a violation. The two cases answer different questions:

    * **Case A, unrecognized id** -- outside the script's own tab vocabulary. A request error,
      rejected BEFORE any capture, exit **1**, no files, message naming every valid id. A typo
      caught before work beats a silently short set a caller takes for complete.
    * **Case B, recognized tab absent from THIS page** -- the app does not render it for this
      data. Skipped and reported, the other tabs still captured under their slug names, exit
      **0**.

    Neither behavior changed; the invariant now says which is which
    (`specs/capture-screenshots-aborts-where-inv-122-says-skip.md`).
    """

    def setUp(self):
        self.module = load_module()

    def test_case_a_one_bad_id_writes_nothing_even_beside_valid_present_tabs(self):
        """The cost of the abort, stated as a test rather than left implicit."""
        with tempfile.TemporaryDirectory() as tmp:
            html = os.path.join(tmp, "app.html")
            with open(html, "w", encoding="utf-8") as handle:
                handle.write(SIX_TAB_FIXTURE)
            out = os.path.join(tmp, "out")
            os.makedirs(out)
            result = run(["--html", html, "--out-dir", out, "--name", "viz",
                          "--tabs", "graph,nosuchtab,matchkeys"])
            self.assertEqual(
                1, result.returncode,
                "an unrecognized id is a caller error and exits 1 (INV-122), not 0 or 2:\n"
                + result.stderr)
            self.assertEqual(
                [], sorted(f for f in os.listdir(out) if f.endswith(".png")),
                "the run must write NO files -- `graph` and `matchkeys` are both valid and "
                "both present, and are deliberately not captured, so a typo can never yield "
                "a partial set that reads as complete")
            self.assertIn("unknown tab id(s): nosuchtab", result.stderr)
            for valid in self.module.DEFAULT_TABS:
                with self.subTest(valid=valid):
                    self.assertIn(
                        valid, result.stderr,
                        "the message must name every valid id, or the caller cannot fix the "
                        "typo without reading the source")

    @unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
    def test_case_b_absent_overlap_is_skipped_and_the_other_five_are_captured(self):
        """Criterion 2, verbatim: skip `overlap`, capture the other five with slug names."""
        with tempfile.TemporaryDirectory() as tmp:
            html = os.path.join(tmp, "app.html")
            with open(html, "w", encoding="utf-8") as handle:
                handle.write(SIX_TAB_FIXTURE)
            out = os.path.join(tmp, "out")
            result = run(["--html", html, "--out-dir", out, "--name", "viz", "--tabs", "all"])
            self.assertEqual(
                0, result.returncode,
                "a recognized-but-absent tab is a skip, and the run still succeeds for the "
                "tabs it captured:\n" + result.stderr)
            expected = sorted(
                "viz-%s.png" % self.module.TABS[t][0]
                for t in self.module.DEFAULT_TABS if t != "overlap")
            self.assertEqual(
                expected, sorted(f for f in os.listdir(out) if f.endswith(".png")),
                "all five present tabs must be captured under their own slug names")
            self.assertNotIn("viz-cross-source.png", os.listdir(out),
                             "the absent tab must never be saved under its name -- that is the "
                             "defect INV-122 exists for")
            self.assertIn("overlap", result.stderr)

    def test_the_three_exit_codes_are_documented_in_the_invariant(self):
        """Criterion 3: a reader must be able to look up what each code means."""
        text = read(os.path.join(REPO_ROOT, "specs", "INVARIANTS.md"))
        start = text.index("- **INV-122**")
        clause = text[start:text.index("\n- **INV-", start + 5)]
        for code, meaning in (("0", "captured"), ("1", "caller"), ("2", "headless")):
            with self.subTest(code=code):
                self.assertRegex(
                    clause, r"\*\*%s\*\*" % code,
                    "INV-122 must document exit %s (%s). Three codes that are not written "
                    "down are three codes a run reports interchangeably." % (code, meaning))

    def test_the_script_cites_the_rule_where_it_rejects(self):
        """INV-183: the rule must be citable at the step it binds."""
        text = read(SCRIPT)
        i = text.index('unknown tab id(s)')
        window = text[max(0, i - 1200):i]
        self.assertIn(
            "INV-122", window,
            "the rejection site must cite INV-122. It did not until 2026-09-02, which is how "
            "a behavior the invariant had not scoped read as a violation of it.")


if __name__ == "__main__":
    unittest.main()
