"""A single-page deliverable must produce exactly one image, not zero.

`module-completion.md` told the guide to capture a single-page HTML deliverable — the Data
Quality, Mapping, and Transformation module's quality and mapping pages — "as one image, with
no `--tabs` argument". Following that captured **nothing**: `--tabs` defaults to the six-tab
app set, so an omitted `--tabs` requested all six, none of which exist on a single-page
document, and the helper exited having written no files. The same paragraph named the
consequence two sentences earlier while prescribing the invocation that caused it.

Nothing recovered it, either: graduation's orphaned-screenshot backfill embeds PNGs the recap
does not reference, and here no PNG existed to backfill.

The concept was missing from the helper, not merely mis-invoked — so `--single` exists, and a
page with no tab controls at all is captured whole rather than exiting empty. The INV-122
skip-and-report path is untouched for a **tabbed** app whose tab ids are merely wrong, because
capturing the whole page there would put the default tab in a file named for a tab it does not
show.

The capture assertions need headless Chrome and skip without it; the argument-handling and
path-naming assertions do not.

Source spec: `specs/single-page-capture-instruction-produces-zero-images.md`.

A later spec — `single-page-capture-crops-to-the-viewport-and-calls-it-full-page` — found the
mode producing one image that was only the *top* of the page while printing the label
"Full page". Enforces **INV-235**: the printed label must describe what the capture achieved,
never what the mode intended, because INV-123 makes that label the caption's input.
Enforces **INV-241** too: a guard for a rule about an artifact's content asserts that
content, not a proxy — see `png_rows` for why the height is a proxy that passes a
broken build.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
HELPER = SCRIPTS / "capture_screenshots.py"
MODULE_COMPLETION = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
                     / "bootcamp-onboarding" / "module-completion.md")

SINGLE_PAGE_HTML = (
    "<!doctype html><html><head><title>Data Quality Assessment</title></head>"
    "<body><h1>Data Quality Assessment</h1><p>Completeness 94%.</p></body></html>"
)

#: A tabbed app whose only tab id is one nobody asks for.
MISTABBED_HTML = (
    "<!doctype html><html><body>"
    "<button id='navbtn-alpha'>Alpha</button><section id='tab-alpha'>A</section>"
    "</body></html>"
)


def load_helper():
    spec = importlib.util.spec_from_file_location("capture_helper", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_chrome():
    for name in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    return None


class TheHelperKnowsWhatASinglePageIs(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def test_the_single_page_id_is_not_a_tab(self):
        """`--tabs page` must stay an unknown id, so --single is the only route in."""
        self.assertNotIn(self.helper.SINGLE_PAGE_ID, self.helper.TABS,
                         "the single-page pseudo-id leaked into the tab inventory")
        with self.assertRaises(ValueError):
            self.helper.resolve_tabs(self.helper.SINGLE_PAGE_ID)

    def test_a_single_page_capture_has_no_slug_suffix(self):
        out = self.helper._out_path(Path("/x"), "data_quality_assessment",
                                    self.helper.SINGLE_PAGE_ID)
        self.assertEqual("data_quality_assessment.png", out.name,
                         "the single-page image must be {name}.png so the embed target "
                         "is predictable")

    def test_a_tabbed_capture_still_carries_its_slug(self):
        out = self.helper._out_path(Path("/x"), "viz", "graph")
        self.assertEqual("viz-entity-graph.png", out.name,
                         "the tabbed naming convention moved")

    def test_omitting_tabs_still_means_all_of_them(self):
        """The default is load-bearing: changing it would alter every existing call."""
        self.assertEqual(list(self.helper.DEFAULT_TABS), self.helper.resolve_tabs(""))

    def test_all_is_an_explicit_spelling_of_the_default(self):
        self.assertEqual(list(self.helper.DEFAULT_TABS), self.helper.resolve_tabs("all"))
        self.assertEqual(list(self.helper.DEFAULT_TABS), self.helper.resolve_tabs("ALL"))

    def test_tab_controls_are_detected(self):
        self.assertFalse(self.helper._has_tab_controls(SINGLE_PAGE_HTML),
                         "a page with no tab bar was reported as tabbed")
        self.assertTrue(self.helper._has_tab_controls(MISTABBED_HTML),
                        "a page with navbtn-/tab- ids was reported as untabbed, which "
                        "would turn a misnamed-tab skip into a whole-page capture")

    def test_an_unreadable_page_is_not_treated_as_untabbed(self):
        """Empty source means "could not read"; guessing single-page there would
        capture the whole page under a tab's name."""
        self.assertFalse(self.helper._has_tab_controls(""))


class TheCliRefusesAmbiguousCombinations(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.page = Path(self.tmp.name) / "single.html"
        self.page.write_text(SINGLE_PAGE_HTML, encoding="utf-8")

    def test_single_with_tabs_is_refused(self):
        code = self.helper.main(["--html", str(self.page), "--out-dir", self.tmp.name,
                                 "--name", "x", "--single", "--tabs", "graph"])
        self.assertEqual(1, code,
                         "--single and --tabs together must be refused rather than one "
                         "silently winning")


@unittest.skipUnless(find_chrome(), "no headless Chrome/Chromium available")
class CapturingRealPages(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "out"

    def page(self, name, html):
        path = Path(self.tmp.name) / name
        path.write_text(html, encoding="utf-8")
        return path

    def pngs(self):
        return sorted(p.name for p in self.out.glob("*.png"))

    def manifest(self, name):
        with open(self.out / f"{name}-tabs.json", encoding="utf-8") as handle:
            return json.load(handle)

    def test_single_produces_exactly_one_png(self):
        page = self.page("single.html", SINGLE_PAGE_HTML)
        code = self.helper.main(["--html", str(page), "--out-dir", str(self.out),
                                 "--name", "data_quality_assessment", "--single"])
        self.assertEqual(0, code)
        self.assertEqual(["data_quality_assessment.png"], self.pngs())
        written = (self.out / "data_quality_assessment.png").read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", written[:8], "not a PNG")
        self.assertGreater(len(written), 1000, "the PNG is suspiciously small")

    def test_the_manifest_records_the_single_capture(self):
        """Graduation's coverage check reads this; an empty manifest reads as skipped."""
        page = self.page("single.html", SINGLE_PAGE_HTML)
        self.helper.main(["--html", str(page), "--out-dir", str(self.out),
                          "--name", "dq", "--single"])
        manifest = self.manifest("dq")
        self.assertEqual(1, manifest["captured_count"])
        entry = manifest["captured"][0]
        self.assertEqual("dq.png", entry["file"])
        self.assertEqual("Full page", entry["label"])
        self.assertEqual([], manifest["failed"])
        self.assertEqual([], manifest["not_present"])

    def test_single_skips_the_tab_pre_flight_entirely(self):
        """`--single` is not merely a shortcut to the safety net.

        With the flag, no tab is ever requested, so the six "tab X is not present"
        reports do not happen. Without this assertion, deleting the `--single` branch
        passes every other test here — the safety net catches the same page and writes the
        same PNG — while every single-page capture goes back to failing six pre-flight
        checks and telling the reader about tabs the page was never going to have.
        """
        import contextlib
        import io

        page = self.page("single.html", SINGLE_PAGE_HTML)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with contextlib.redirect_stdout(io.StringIO()):
                code = self.helper.main(["--html", str(page), "--out-dir", str(self.out),
                                         "--name", "dq", "--single"])
        self.assertEqual(0, code)
        self.assertNotIn("is not present in this visualization", stderr.getvalue(),
                         "--single still runs the tab pre-flight, so it is doing nothing "
                         "the safety net was not already doing")
        self.assertNotIn("Pass --single to say so explicitly", stderr.getvalue(),
                         "--single took the safety-net path, which advises passing the "
                         "flag that was already passed")

    def test_a_single_page_capture_makes_no_activation_copy(self):
        """There is no tab to activate, so injecting the activation script is waste.

        Pinned by making `_snapshot_copy` fail: a single-page capture must not reach it.
        Left unpinned, routing the single page through it passes — the injected script
        finds no tab, exhausts its retries, and the page still renders.
        """
        page = self.page("single.html", SINGLE_PAGE_HTML)
        original = self.helper._snapshot_copy

        def refuse(*args, **kwargs):
            raise AssertionError("a single-page capture must not make an activation copy")

        self.helper._snapshot_copy = refuse
        try:
            code = self.helper.main(["--html", str(page), "--out-dir", str(self.out),
                                     "--name", "dq", "--single"])
        finally:
            self.helper._snapshot_copy = original
        self.assertEqual(0, code)
        self.assertEqual(["dq.png"], self.pngs())

    def test_a_tabless_page_without_the_flag_is_captured_anyway(self):
        """The reported invocation. It must no longer write zero files."""
        page = self.page("single.html", SINGLE_PAGE_HTML)
        code = self.helper.main(["--html", str(page), "--out-dir", str(self.out),
                                 "--name", "dq"])
        self.assertEqual(0, code, "the no-flag invocation still fails")
        self.assertEqual(["dq.png"], self.pngs())

    def test_a_mistabbed_app_still_reports_and_skips(self):
        """INV-122 preserved: not replaced by a whole-page capture."""
        page = self.page("mistabbed.html", MISTABBED_HTML)
        code = self.helper.main(["--html", str(page), "--out-dir", str(self.out),
                                 "--name", "mis", "--tabs", "graph,stats"])
        self.assertEqual(2, code, "a tabbed app with misnamed tabs must exit 2")
        self.assertEqual([], self.pngs(),
                         "a whole-page image was written under a tab-naming request, "
                         "which is the defect tab-naming exists to prevent")
        manifest = self.manifest("mis")
        self.assertEqual(0, manifest["captured_count"])
        self.assertEqual(["graph", "stats"],
                         sorted(e["tab"] for e in manifest["not_present"]))

    def test_the_tabbed_app_capture_is_unchanged(self):
        """Six images, same slugs and labels, by the same invocation as before."""
        page = self.page("tabbed.html", self.tabbed_app())
        code = self.helper.main(["--html", str(page), "--out-dir", str(self.out),
                                 "--name", "results_visualization"])
        self.assertEqual(0, code)
        self.assertEqual(
            sorted("results_visualization-%s.png" % self.helper.TABS[t][0]
                   for t in self.helper.DEFAULT_TABS),
            self.pngs(),
            "the tabbed app's six-image capture changed")

    def tabbed_app(self):
        """The real visualization page, rendered with a fetch shim."""
        spec = importlib.util.spec_from_file_location(
            "viz_for_capture_test", SCRIPTS / "senzing_viz_server.py")
        viz = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(SCRIPTS))
        spec.loader.exec_module(viz)
        srcs = ["CUSTOMERS", "REFERENCE", "WATCHLIST"]
        ents = [{"entity_id": 1000 + i, "entity_name": "Entity %d" % i,
                 "record_count": 1 + (i % 3), "data_sources": [srcs[i % 3]]}
                for i in range(9)]
        merges = [e for e in ents if e["record_count"] > 1]
        payload = {
            "stats": {"records_total": 18, "entities_total": len(ents),
                      "multi_record_entities": len(merges), "cross_source_entities": 2,
                      "relationships_total": 0, "data_sources_total": 3,
                      "histogram": {"1": 3, "2": 3, "3": 3, "4+": 0},
                      "bucket_entities": {"1": [], "2": [], "3": [], "4+": []},
                      "sample_entities": merges[:3]},
            "graph": {"nodes": ents, "edges": []},
            "merges": {"entities": [dict(e, records=[]) for e in merges]},
            "records": {},
            "overlap": {"sources": srcs, "matrix": [[3, 1, 0], [1, 3, 0], [0, 0, 3]]},
            "matchkeys": {"keys": []}, "features": {"features": []},
        }
        shim = ("<script>const __DATA__=" + viz._script_json(payload) + ";"
                "window.fetch=function(u){var p=u.split('?')[0].replace('/api/','');"
                "if(p==='search'){return Promise.resolve({json:function(){"
                "return Promise.resolve({results:[]});}});}"
                "return Promise.resolve({json:function(){"
                "return Promise.resolve(__DATA__[p]);}});};</script>")
        return viz.render_page("Fixture", data_shim=shim, sources=srcs)


class TheInstructionMatchesTheHelper(unittest.TestCase):
    def setUp(self):
        self.text = MODULE_COMPLETION.read_text(encoding="utf-8")
        self.flat = re.sub(r"\s+", " ", self.text)

    def test_it_prescribes_single(self):
        self.assertRegex(
            self.flat, r"(?i)capture it as \*?\*?one\s*image\*?\*? with `--single`",
            "module-completion still prescribes an invocation that captures nothing")

    def test_the_old_invocation_is_gone(self):
        self.assertNotIn("with no `--tabs` argument", self.flat,
                         "the instruction that produced zero images survives")

    def test_it_explains_why_omitting_tabs_is_not_none(self):
        self.assertRegex(
            self.flat,
            r"(?i)An omitted `--tabs` does not mean \"no tabs\", it means \*?\*?all\s*six",
            "the reason the old invocation failed is not stated, so a reader may "
            "reinvent it")

    def test_it_shows_a_runnable_command(self):
        self.assertIn("--single", self.text)
        self.assertRegex(self.text, r"python3 <helper> --html [^\n]*\n\s*--name \{name\} --single",
                         "no copyable single-page invocation is given")

    def test_it_names_the_output_file(self):
        self.assertRegex(self.flat, r"(?i)writes `\{name\}\.png`",
                         "the embed target is unstated, so the recap reference is a guess")

    def test_it_does_not_present_auto_detect_as_the_route(self):
        self.assertRegex(
            self.flat, r"(?i)Do not rely on that",
            "the safety net is described without saying it is a net, which invites "
            "dropping the flag")


#: A document taller than the 1440x900 viewport, ending in a distinctively DARK footer.
#: The footer is the assertion target on purpose: it is the last thing on the page, so it is
#: the first thing a crop loses. (The real defect lost an entire data source and the offline
#: footer from a three-source quality page.)
TALL_PAGE_FOOTER_RGB = (17, 17, 17)
TALL_PAGE_HTML = (
    "<!doctype html><html><head><title>Tall</title></head>"
    "<body style='margin:0'><h1>Data Quality Assessment</h1>"
    + "".join(
        "<section style='height:380px;background:#eeeeff;margin:12px;padding:16px'>"
        "<h2>SOURCE_%d</h2><p>completeness 87%%</p></section>" % i
        for i in range(1, 7)
    )
    + "<footer style='height:80px;background:#111111'></footer></body></html>"
)


def png_size(path):
    """(width, height) from the IHDR — no third-party image library (INV-108)."""
    import struct

    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return struct.unpack(">II", data[16:24])


def png_rows(path):
    """(width, height, channels, [row bytes]) for an 8-bit PNG, using zlib only.

    ⛔ The pixels are decoded, not just the header, because **height alone does not prove
    the page is in the image** — and that is not a hypothetical. The first fix measured
    `scrollHeight` and screenshotted at exactly that height, producing a PNG whose height
    equaled the page height while the footer was still missing: under `--headless=new`
    Chrome's `--window-size` includes window chrome, so the viewport was ~87px shorter than
    the image and the bottom of the page was never rendered into it. A height-only
    assertion passes that build. Looking at the bottom pixels is what fails it.
    """
    import struct
    import zlib

    data = Path(path).read_bytes()
    pos, idat, width, height, ctype = 8, b"", None, None, None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, ctype = struct.unpack(">IIBB", chunk[:10])
            if depth != 8:
                raise ValueError("expected an 8-bit PNG, got %d-bit" % depth)
        elif kind == b"IDAT":
            idat += chunk
        elif kind == b"IEND":
            break
        pos += 12 + length
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = width * channels
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(height):
        filt = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if filt == 1:
            for x in range(channels, stride):
                line[x] = (line[x] + line[x - channels]) & 255
        elif filt == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif filt == 3:
            for x in range(stride):
                left = line[x - channels] if x >= channels else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif filt == 4:
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                b = prev[x]
                c = prev[x - channels] if x >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pred) & 255
        rows.append(bytes(line))
        prev = line
    return width, height, channels, rows


def count_footer_rows(path, rgb=TALL_PAGE_FOOTER_RGB, tolerance=24):
    """How many rows contain the footer's color at mid-width."""
    width, height, channels, rows = png_rows(path)
    x = (width // 2) * channels
    found = 0
    for row in rows:
        pixel = tuple(row[x:x + 3])
        if all(abs(pixel[i] - rgb[i]) <= tolerance for i in range(3)):
            found += 1
    return found


@unittest.skipUnless(find_chrome(), "headless Chrome is required to capture")
class SinglePageCapturesTheWholeDocument(unittest.TestCase):
    """`--single` captures a DOCUMENT, whose height is its content's, not the viewport's."""

    def setUp(self):
        self.helper = load_helper()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "out"
        self.page = Path(self.tmp.name) / "tall.html"
        self.page.write_text(TALL_PAGE_HTML, encoding="utf-8")

    def capture(self, name="tall", extra=()):
        code = self.helper.main(
            ["--html", str(self.page), "--out-dir", str(self.out), "--name", name,
             "--single", *extra]
        )
        png = self.out / f"{name}.png"
        if not png.is_file():
            self.skipTest("no headless backend produced a capture in this environment")
        return code, png

    def test_the_capture_is_taller_than_the_viewport(self):
        _, png = self.capture()
        _, height = png_size(png)
        self.assertGreater(
            height, self.helper._WINDOW[1],
            "the capture is still viewport-height, so a document taller than 900px is "
            "cropped and labeled as if it were not",
        )

    def test_the_bottom_of_the_page_is_actually_in_the_image(self):
        """The assertion that catches a crop a height check cannot — see `png_rows`."""
        _, png = self.capture()
        self.assertGreaterEqual(
            count_footer_rows(png), 40,
            "the page's footer is missing from the capture, so content below the "
            "rendered viewport was lost even though the PNG is tall enough to hold it",
        )

    def test_the_label_says_full_page_when_it_is(self):
        self.capture(name="dq")
        with open(self.out / "dq-tabs.json", encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual("Full page", manifest["captured"][0]["label"])

    def test_a_short_page_is_still_a_full_page(self):
        short = Path(self.tmp.name) / "short.html"
        short.write_text(SINGLE_PAGE_HTML, encoding="utf-8")
        self.helper.main(["--html", str(short), "--out-dir", str(self.out),
                          "--name", "short", "--single"])
        png = self.out / "short.png"
        if not png.is_file():
            self.skipTest("no headless backend produced a capture in this environment")
        with open(self.out / "short-tabs.json", encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual("Full page", manifest["captured"][0]["label"])


class TheLabelDescribesWhatHappened(unittest.TestCase):
    """Criterion 2 — "Full page" only when a full-page capture actually succeeded."""

    def setUp(self):
        self.helper = load_helper()

    def test_the_three_outcomes_have_distinct_labels(self):
        full = self.helper._single_page_label(self.helper.FULL_PAGE_FULL)
        clamped = self.helper._single_page_label(self.helper.FULL_PAGE_CLAMPED, 30000, 12000)
        viewport = self.helper._single_page_label(self.helper.FULL_PAGE_VIEWPORT, 2100, 900)
        self.assertEqual("Full page", full)
        self.assertEqual(3, len({full, clamped, viewport}), "two outcomes share a label")
        for label in (clamped, viewport):
            with self.subTest(label=label):
                self.assertNotEqual("Full page", label)

    def test_a_viewport_fallback_cannot_be_mistaken_for_the_full_page(self):
        label = self.helper._single_page_label(self.helper.FULL_PAGE_VIEWPORT, 2100, 900)
        self.assertNotIn("Full page", label)
        self.assertRegex(label, r"(?i)viewport")

    def test_the_default_outcome_is_not_full_page(self):
        """A backend that records nothing must not inherit the "Full page" claim."""
        self.assertEqual(self.helper.FULL_PAGE_VIEWPORT, self.helper._FULL_PAGE_OUTCOME)

    def test_the_clamp_is_named_in_its_label_and_documented(self):
        self.assertIn("12000", str(self.helper._MAX_FULL_PAGE_PX))
        label = self.helper._single_page_label(self.helper.FULL_PAGE_CLAMPED, 30000, 12000)
        self.assertIn(str(self.helper._MAX_FULL_PAGE_PX), label)
        self.assertRegex(label, r"(?i)clamp")

    def test_a_shortfall_warns_on_stderr_with_both_heights(self):
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            self.helper._record_full_page(self.helper.FULL_PAGE_VIEWPORT, 2100, 900)
        warning = buffer.getvalue()
        self.assertIn("2100", warning)
        self.assertIn("900", warning)
        self.assertIn("INV-123", warning, "the caption rule this misleads is not named")

    def test_the_label_comment_does_not_make_the_label_inv_123s_input(self):
        """INV-123 derives the caption from the opened image and the tab it shows (#234).

        The comment above `SINGLE_PAGE_LABEL_VIEWPORT` said INV-123 names the printed label
        as the caption's designated input. Negative-controlled by restoring that sentence.
        """
        source = HELPER.read_text(encoding="utf-8")
        m = re.search(r"((?:^#.*\n)+)SINGLE_PAGE_LABEL_VIEWPORT = ", source, re.M)
        self.assertIsNotNone(m, "no comment block sits directly above the viewport label")
        comment = " ".join(re.sub(r"(?m)^#\s?", "", m.group(1)).split())
        self.assertNotRegex(comment, r"INV-123 (?:names|designates|makes) (?:that|the)",
                            "the comment attributes the label-as-caption-input to INV-123")
        self.assertIn("INV-123 derives the caption from the opened image and the tab it shows",
                      comment)

    def test_a_clamp_warns_on_stderr(self):
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            self.helper._record_full_page(self.helper.FULL_PAGE_CLAMPED, 30000, 12000)
        warning = buffer.getvalue()
        self.assertIn("30000", warning)
        self.assertIn(str(self.helper._MAX_FULL_PAGE_PX), warning)

    def test_a_full_capture_is_silent(self):
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            self.helper._record_full_page(self.helper.FULL_PAGE_FULL, 1200, 1200)
        self.assertEqual("", buffer.getvalue(), "a successful capture must not warn")


class EveryWindowSizingBackendCorrectsForWindowChrome(unittest.TestCase):
    """A window-sized backend must add the chrome offset back, or it crops silently.

    ⛔ Asserted against the SOURCE, not by running the backend, because this suite is
    stdlib-only (INV-108) and may not import `selenium` or `playwright`. That is a real
    limitation and it hid a real bug: `_capture_selenium` assumed a headless window and its
    viewport "agree closely enough", and on 2026-08-14 a live run measured a **139px**
    difference — a 2704px page captured at 2565px, the whole footer missing, while the
    function reported a FULL capture and the label read "Full page". An INV-235 breach in the
    one path no test could execute.

    So the guard pins the *mechanism* each window-sizing backend must carry. `_capture_
    playwright` is exempt by construction: it sets the **viewport** directly and uses
    Playwright's native `full_page=True`, so no window chrome is involved — verified the same
    day at exactly the page height (2704px, footer present).
    """

    def setUp(self):
        self.source = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
                       / "capture_screenshots.py").read_text(encoding="utf-8")

    def _body(self, name):
        start = self.source.index("def %s(" % name)
        end = self.source.index("\ndef ", start + 1)
        return self.source[start:end]

    def test_the_chrome_cli_path_measures_the_offset(self):
        body = self._body("_measure_chrome_cli")
        self.assertIn("data-sz-inner-height", self.source)
        self.assertRegex(body, r"_WINDOW\[1\] - int\(inner\.group\(1\)\)",
                         "the CLI path no longer derives the offset from innerHeight")

    def test_the_chrome_cli_path_adds_the_offset_back(self):
        self.assertRegex(
            self._body("_capture_chrome_cli"), r"height = covered \+ chrome_px",
            "the measured offset is not added to the requested window height, so the bottom "
            "of every tall page is cropped",
        )

    def test_the_selenium_path_measures_inner_height_and_corrects(self):
        body = self._body("_capture_selenium")
        self.assertIn("window.innerHeight", body)
        self.assertRegex(
            body, r"captured \+ \(captured - inner\)",
            "the Selenium path sizes the window without correcting for window chrome, which "
            "crops the bottom of the page while still reporting a full capture (INV-235)",
        )

    def test_the_selenium_path_records_why(self):
        self.assertRegex(
            self._body("_capture_selenium"), r"(?i)INV-235",
            "the reason the correction exists is unrecorded, so it reads as removable",
        )

    def test_the_playwright_path_sets_the_viewport_not_a_window(self):
        body = self._body("_capture_playwright")
        self.assertIn("full_page=True", body)
        self.assertIn("set_viewport_size", body)
        self.assertNotIn("window-size", body)


class TheTabbedPathKeepsTheFixedViewport(unittest.TestCase):
    """Criterion 3 — this change is scoped to `--single`; a tab's premise is different."""

    def setUp(self):
        self.helper = load_helper()

    def test_the_viewport_is_still_the_documented_fixed_size(self):
        self.assertEqual((1440, 900), self.helper._WINDOW)

    def test_a_tab_capture_is_not_in_single_page_mode(self):
        self.helper._CURRENT_TAB = "graph"
        self.assertFalse(self.helper._single_page_mode())
        self.helper._CURRENT_TAB = self.helper.SINGLE_PAGE_ID
        self.assertTrue(self.helper._single_page_mode())

    def test_a_tab_label_is_unaffected_by_the_single_page_outcome(self):
        self.helper._FULL_PAGE_OUTCOME = self.helper.FULL_PAGE_VIEWPORT
        self.assertEqual("Entity Graph", self.helper._tab_label("graph"))


if __name__ == "__main__":
    unittest.main()
