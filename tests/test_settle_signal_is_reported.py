"""An animated view captured without its settled signal must be REPORTED, not passed off.

INV-298 has two halves. The capture waits on the layout's own settled signal
(``data-graph-settled`` on the document element), and **a capture that proceeds without it
must say so**. This guards the second half, which is the half that needs no layout decision:

* the graph tab captured with the signal present   -> manifest ``settled``, stderr silent
* the graph tab captured without it                -> manifest ``unsettled``, stderr reports it
* a static tab, which never animates               -> manifest ``n/a``, stderr silent

⛔ **``unsettled`` and ``unknown`` are different findings and are kept apart deliberately.**
``unsettled`` means the page was asked and said no; ``unknown`` means the backend cannot read
the DOM at all (``wkhtmltoimage``). Reporting a backend limitation as an unsettled layout blames
the artifact for the instrument, which is the reverse of what INV-129 asks for -- so an animated
tab starts at ``unknown`` and only a backend that actually read the attribute may downgrade it.

⚠️ **Why this matters more than it looks.** Measured 2026-09-03 through this helper's own path on
the 85-entity Truth Set, the force layout advances about **five of the ~300 ticks** it needs, at
every virtual-time budget from 5s to 300s, because d3's timer is driven by
``requestAnimationFrame`` and headless virtual time does not advance it. So today this reports
``unsettled`` on every real graph capture -- correctly. The image is still written, because
capture is best-effort by contract (INV-122) and an unfinished layout is still the best available
view; what changed is that it no longer ships silently
(``specs/graph-capture-budget-does-not-converge-at-truth-set-density.md``).

Stdlib only; the script is run as a subprocess and never imported from ``plugins/`` (INV-108).

Run:  python3 -m unittest discover -s tests
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "capture_screenshots.py"
VIZ = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "senzing_viz_server.py"

#: A minimal tabbed page. No d3 and no data: the signal is a DOM attribute by contract, so a
#: fixture can honor or withhold it without a force simulation — which is precisely the point
#: of specifying an attribute rather than a JS internal.
_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Viz</title>
<style>.tab{display:none}.tab.active{display:block}</style></head><body>
<nav id="nav"></nav>
<section class="tab active" id="tab-graph">ENTITY GRAPH</section>
<section class="tab" id="tab-stats">MERGE STATISTICS</section>
<script>
var ALL=[["graph","Entity Graph"],["stats","Merge Statistics"]];
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
  __SETTLE__
}, 200);
</script></body></html>
"""
_SETS_SIGNAL = 'document.documentElement.setAttribute("data-graph-settled","1");'


def load_module():
    spec = importlib.util.spec_from_file_location("cap_settle_mod", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["cap_settle_mod"] = module
    spec.loader.exec_module(module)
    return module


def has_browser():
    return load_module()._chrome_exe() is not None


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run_capture(page_html, tabs):
    """(stderr, manifest) for a capture of `page_html`."""
    tmp = tempfile.mkdtemp(prefix="settle-")
    html = os.path.join(tmp, "app.html")
    with open(html, "w", encoding="utf-8") as handle:
        handle.write(page_html)
    out = os.path.join(tmp, "out")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--html", html, "--out-dir", out,
         "--name", "viz", "--tabs", tabs],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
    )
    manifest = {}
    path = os.path.join(out, "viz-tabs.json")
    if os.path.isfile(path):
        manifest = json.loads(read(path))
    return proc.stderr, manifest


def settled_for(manifest, tab):
    for entry in manifest.get("captured", []):
        if entry.get("tab") == tab:
            return entry.get("settled")
    return None


@unittest.skipUnless(has_browser(), "no headless Chrome/Chromium available")
class TheCaptureReportsWhatItActuallySaw(unittest.TestCase):
    def test_a_page_that_reports_settled_is_recorded_and_not_warned_about(self):
        stderr, manifest = run_capture(_PAGE.replace("__SETTLE__", _SETS_SIGNAL), "graph")
        self.assertEqual(
            "settled", settled_for(manifest, "graph"),
            "the page set data-graph-settled, so the manifest must say so:\n" + stderr,
        )
        self.assertNotIn(
            "BEFORE the layout reported itself settled", stderr,
            "a settled capture must not be warned about — a warning on a correct capture "
            "trains the reader to ignore the one that matters",
        )

    def test_a_page_that_withholds_the_signal_is_reported(self):
        stderr, manifest = run_capture(_PAGE.replace("__SETTLE__", ""), "graph")
        self.assertEqual(
            "unsettled", settled_for(manifest, "graph"),
            "an animated tab captured with no settled signal is recorded as unsettled, per "
            "tab, so graduation's coverage check and a later reader can both see it:\n"
            + stderr,
        )
        self.assertIn("BEFORE the layout reported itself settled", stderr)
        self.assertIn(
            "INV-298", stderr,
            "the message must name the rule it enforces, so a reader can look it up",
        )

    def test_the_image_is_still_written_when_unsettled(self):
        """⛔ Reporting must not become refusing — capture is best-effort (INV-122)."""
        stderr, manifest = run_capture(_PAGE.replace("__SETTLE__", ""), "graph")
        self.assertEqual(
            1, len(manifest.get("captured", [])),
            "an unfinished layout is still the best available view and must still reach the "
            "recap (INV-146). Reporting it is the change; withholding it would be a "
            "regression:\n" + stderr,
        )

    def test_a_static_tab_is_not_asked_for_a_signal(self):
        stderr, manifest = run_capture(_PAGE.replace("__SETTLE__", ""), "stats")
        self.assertEqual(
            "n/a", settled_for(manifest, "stats"),
            "a tab that does not animate owes no settled signal; recording it as unsettled "
            "would make the field meaningless:\n" + stderr,
        )
        self.assertNotIn("BEFORE the layout reported itself settled", stderr)

    def test_one_tabs_outcome_does_not_label_another(self):
        """The record is a module global; a stale value would mislabel the next tab."""
        stderr, manifest = run_capture(_PAGE.replace("__SETTLE__", ""), "graph,stats")
        self.assertEqual("unsettled", settled_for(manifest, "graph"), stderr)
        self.assertEqual("n/a", settled_for(manifest, "stats"), stderr)


class TheContractIsWiredAtBothEnds(unittest.TestCase):
    """Structural half — no browser needed, so it holds wherever the suite runs."""

    def test_the_renderer_emits_the_signal(self):
        text = read(VIZ)
        for needle, why in (
            ('data-graph-settled', "the attribute INV-298 names"),
            ('sim.on("end"', "d3's own definition of a finished layout"),
            ('graphSettled(false)', "cleared as a layout begins, or a redraw reports stale"),
            ('graphSettled(true)', "set at final positions"),
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text, why)

    def test_the_empty_graph_reports_settled_immediately(self):
        """Otherwise a waiter on a zero-node graph waits out its whole timeout."""
        text = read(VIZ)
        start = text.index('addGraphControls("graph-container",0)')
        self.assertIn(
            "graphSettled(true)", text[start:start + 400],
            "the empty-graph branch must report settled — there is nothing to lay out, and "
            "INV-298 requires the signal immediately in that case",
        )

    def test_the_chrome_backend_reads_the_signal_in_the_screenshot_run(self):
        text = read(SCRIPT)
        start = text.index("def _capture_chrome_cli")
        block = text[start:start + 2000]
        self.assertIn("--dump-dom", block)
        self.assertIn(
            "--screenshot", block,
            "the settled read must ride along with the screenshot in ONE invocation — a "
            "separate browser run could describe a different render than the image it labels",
        )

    def test_unsettled_and_unknown_stay_distinct(self):
        text = read(SCRIPT)
        for needle in ("SETTLED_UNKNOWN", "SETTLED_NO", "SETTLED_NA", "SETTLED_YES"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        self.assertRegex(
            text, r"could not read the settled signal",
            "a backend that cannot inspect the DOM reports UNKNOWN, with its own message. "
            "Folding it into the unsettled warning would blame the artifact for the "
            "instrument.",
        )

    def test_a_backend_that_never_reads_the_dom_leaves_the_state_unknown(self):
        """⛔ The unsettled/unknown distinction, asserted BEHAVIORALLY.

        The first version of this class only checked that both constants and the
        "could not read" message existed in the source — which survives the exact mutation
        it was written to catch: changing the reset default from UNKNOWN to NO left all ten
        tests green, because the Chrome backend overwrites the default before anything
        observes it, so only a DOM-blind backend (`wkhtmltoimage`) ever surfaces it. That is
        a guard whose name claims more than its assertion checked. This substitutes a
        backend that captures without reading the DOM — the `wkhtmltoimage` case — and
        requires the record to stay `unknown`.
        """
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "viz-entity-graph.png"

            def blind_backend(url, path):
                Path(path).write_bytes(b"\x89PNG\r\n\x1a\n")
                return True

            module._capture_one("file:///dev/null", out, blind_backend, tab="graph")
            self.assertEqual(
                module.SETTLED_UNKNOWN, module._SETTLED_STATE,
                "a backend that cannot inspect the DOM must leave the settle state UNKNOWN. "
                "Defaulting an animated tab to `unsettled` reports a finding nobody "
                "established — blaming the artifact for the instrument, which is the "
                "reverse of INV-129.",
            )
            module._capture_one("file:///dev/null", out, blind_backend, tab="stats")
            self.assertEqual(
                module.SETTLED_NA, module._SETTLED_STATE,
                "a static tab owes no signal, so its state is n/a rather than unknown",
            )

    def test_the_animated_tab_set_drives_the_expectation(self):
        """Derived from _ANIMATED_TABS, not a second hardcoded list (INV-246)."""
        module = load_module()
        self.assertTrue(module._settle_expected("graph"))
        self.assertFalse(module._settle_expected("stats"))
        for tab in module._ANIMATED_TABS:
            with self.subTest(tab=tab):
                self.assertTrue(
                    module._settle_expected(tab),
                    "every animated tab owes a settled signal; a second list would drift "
                    "from _ANIMATED_TABS",
                )


if __name__ == "__main__":
    unittest.main()
