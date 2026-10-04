"""Every capture path must request the capture-oriented render (INV-298/INV-299).

The render was first wired into the two per-tab branches — live server and file snapshot — and
**not** into the single-page branch, which sits three lines above them in the same
``if/elif/else``. ``_settle_expected`` then encoded the same omission a second time, keying on
tab ids that exclude the single-page pseudo-id, so a ``--single`` capture of an animated view
would have been both unsettled **and** recorded as owing no signal — the one combination INV-298
exists to prevent.

⚠️ **Not reachable through documented use**, which is why the finding was Low: ``--single`` is
scoped to the tabless Data Quality, Mapping and Transformation pages, and the auto-detect
fallback fires only for a page with no tab controls, so it cannot pick up the tabbed app. The
gap mattered because nothing would have noticed the day a quality page gained an animated
element.

⛔ **The site set is DERIVED BY SCANNING the URL assignments, never by naming the branches that
were fixed** (INV-246). A guard listing the three paths known today certifies exactly the paths
whose omission has already been found, and is blind to the fourth — which is the only one that
would matter. This scans ``capture()`` for every ``url = …`` assignment and requires each to go
through the single helper.

Stdlib only; the script is read as text and loaded by path, never imported from ``plugins/`` as
a package (INV-108).

No phrase-level pattern (#438): its line reads are of Python source lines it finds with `ast`, as
#424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""

import ast
import importlib.util
import os
import re
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "scripts", "capture_screenshots.py"
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def load_module():
    spec = importlib.util.spec_from_file_location("cap_paths_mod", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["cap_paths_mod"] = module
    spec.loader.exec_module(module)
    return module


def url_assignments():
    """[(lineno, source)] for every `url = …` inside `capture()`, found with ast.

    ⚠️ Parsed rather than grepped so a reformatting cannot hide an assignment from this guard,
    and so the set is whatever the function actually contains today.
    """
    tree = ast.parse(read(SCRIPT))
    out = []
    lines = read(SCRIPT).split("\n")
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == "capture"):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "url" for t in inner.targets
            ):
                out.append((inner.lineno, lines[inner.lineno - 1].strip()))
    return out


class EveryUrlTheCaptureBuildsAsksForTheRender(unittest.TestCase):
    def test_the_scan_finds_the_assignments(self):
        """A scan that finds nothing would pass the class below vacuously."""
        found = url_assignments()
        self.assertGreaterEqual(
            len(found), 3,
            "expected at least the three URL branches in capture() — single-page, live-server "
            "and file-snapshot. Finding fewer means the scan has stopped seeing them, not that "
            "the branches are gone:\n  " + "\n  ".join("%d: %s" % f for f in found),
        )

    def test_every_assignment_routes_through_the_helper(self):
        offenders = []
        for lineno, src in url_assignments():
            if "_with_capture(" in src or "_tab_url(" in src:
                continue
            offenders.append("capture_screenshots.py:%d — %s" % (lineno, src))
        self.assertEqual(
            [], offenders,
            "a capture path builds a URL without requesting the capture-oriented render "
            "(INV-298/INV-299). Route it through `_with_capture`, or through `_tab_url`, which "
            "adds the parameter itself. A path that does not ask gets ~5 of the ~300 layout "
            "ticks the graph needs, and produces an image of a layout that has barely "
            "started:\n  " + "\n  ".join(offenders),
        )


class TheRequestSurvivesAnExistingQueryString(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_a_url_with_no_query_gets_a_question_mark(self):
        self.assertEqual(
            "file:///tmp/x.html?capture=1",
            self.module._with_capture("file:///tmp/x.html"),
        )

    def test_a_url_that_already_has_a_query_gets_an_ampersand(self):
        """A live-server URL may already carry `?tab=`; a second `?` would break it."""
        self.assertEqual(
            "http://localhost:8080/?tab=graph&capture=1",
            self.module._with_capture("http://localhost:8080/?tab=graph"),
        )

    def test_the_live_server_tab_url_asks_too(self):
        got = self.module._tab_url("http://localhost:8080/", "graph")
        self.assertIn("capture=1", got)
        self.assertIn("tab=graph", got)


class TheSinglePageAnswerIsDeliberate(unittest.TestCase):
    """⛔ It answered False by omission; the point is that it now answers False by decision."""

    def setUp(self):
        self.module = load_module()
        self.text = read(SCRIPT)

    def test_the_single_page_id_owes_no_signal(self):
        self.assertFalse(
            self.module._settle_expected(self.module.SINGLE_PAGE_ID),
            "`--single` targets static deliverables with no layout to settle; demanding a "
            "signal there would report `unsettled` on every quality and mapping page and train "
            "the reader to ignore the warning that matters",
        )

    def test_the_reason_is_recorded_at_the_function(self):
        start = self.text.index("def _settle_expected(")
        doc = self.text[start:start + 1400]
        self.assertRegex(
            doc, r"(?i)by DECISION, not by omission",
            "the single-page answer must be explained where it is given. It was False because "
            "the pseudo-id happened not to be in a set of tab ids — indistinguishable from "
            "nobody having considered it.",
        )
        self.assertRegex(
            doc, r"(?i)do not add the single-page id to `_ANIMATED_TABS`",
            "that set also sizes the virtual-time budget and feeds the tab-label lookup, so "
            "widening it to answer a settle question would change two unrelated behaviors",
        )

    def test_an_animated_tab_still_owes_one(self):
        for tab in sorted(self.module._ANIMATED_TABS):
            with self.subTest(tab=tab):
                self.assertTrue(self.module._settle_expected(tab))


if __name__ == "__main__":
    unittest.main()
