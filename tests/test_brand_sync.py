"""Guard against silent drift between brand_tokens.py and the inlined fallback
palettes in senzing_viz_server.py, generate_recap_pdf.py and generate_discoveries_pdf.py.

This file discharges **INV-184** — "every shipped generator that inlines a fallback copy
of the brand palette" — not only **INV-107**, which enumerates the first two. INV-107 is
the narrower, older statement and remains binding; INV-184 is the one that puts the third
generator in scope, so a new generator with an inlined palette belongs here on sight.

Each script keeps a hardcoded copy of the brand palette so it still renders if
brand_tokens.py is unavailable. The runtime prefers the imported values whenever
brand_tokens loads, so a stale fallback is never exercised in practice — and would
drift undetected. Here brand_tokens IS importable, so the live module globals are
the brand_tokens-derived values; asserting they equal the named fallback copies
proves the fallbacks are in sync with the source of truth.

Run:  python3 -m unittest discover -s tests
"""
import glob
import importlib.util
import os
import re
import sys
import types
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts")
sys.path.insert(0, SCRIPTS)

#: A module-level inlined fallback copy of the brand palette. INV-184 binds "every shipped
#: generator" that has one, so the set is DISCOVERED here rather than listed (INV-246).
FALLBACK_CONSTANT = re.compile(r"^_?FALLBACK_[A-Z_]+\s*=", re.M)

#: Carriers known to be covered when this sweep was written. A floor, not the site set:
#: the scan decides what must be covered, this only stops the scan degrading to silence.
KNOWN_CARRIERS = frozenset({
    "brand_tokens", "senzing_viz_server", "generate_recap_pdf", "generate_discoveries_pdf",
})


def fallback_carriers():
    """Every shipped script inlining a brand-palette fallback, by module name."""
    found = set()
    for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
        with open(path, encoding="utf-8") as fh:
            if FALLBACK_CONSTANT.search(fh.read()):
                found.add(os.path.splitext(os.path.basename(path))[0])
    return found


def load_viz_with_brand_tokens_unavailable():
    """A fresh `senzing_viz_server` whose brand_tokens import failed.

    ⛔ Without this, an "inline fallback matches the helper" test compares the helper to
    **itself**: brand_tokens imports fine under test, so `viz.color_for_sources` IS
    `brand_tokens.color_for_sources` and the inline copy is never executed. That vacuity
    was demonstrated — a mutation gutting the inline copy's encoding space escaped the
    assertion entirely.

    Blocking the import is done by planting a module whose attribute access raises, so the
    script's own `except Exception` fallback branch runs exactly as it would in the wild.
    """
    blocker = types.ModuleType("brand_tokens")

    def _unavailable(name):
        raise AttributeError("brand_tokens is unavailable in this test")

    blocker.__getattr__ = _unavailable
    saved = sys.modules.get("brand_tokens")
    sys.modules["brand_tokens"] = blocker
    try:
        spec = importlib.util.spec_from_file_location(
            "viz_without_brand_tokens", os.path.join(SCRIPTS, "senzing_viz_server.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if saved is None:
            del sys.modules["brand_tokens"]
        else:
            sys.modules["brand_tokens"] = saved


class TheCarrierSetIsDerived(unittest.TestCase):
    """INV-246: the set of generators this file must cover is scanned, never listed.

    INV-184 exists *because* this exact guard once enumerated its sites. INV-107 named two
    generators; `generate_discoveries_pdf.py` drifted out of scope unnoticed while its own
    comment claimed a test asserted it, and the remedy then was to add the third BY HAND.
    A hardcoded list would repeat that history the day a fourth generator ships, so the
    carrier set is discovered from the corpus and a carrier this file does not exercise is
    a failure rather than a silence.

    ⛔ This sweep proves a carrier is EXERCISED here, not that its assertions are adequate.
    It catches a generator nobody added; only reading catches a generator added weakly.
    """

    def test_the_scan_is_not_vacuous(self):
        found = fallback_carriers()
        self.assertGreaterEqual(
            len(found), len(KNOWN_CARRIERS),
            "the fallback-constant scan found fewer carriers than were known to exist "
            "(%s vs %s) — the constant naming convention changed and this sweep is now "
            "inspecting a set it cannot see" % (sorted(found), sorted(KNOWN_CARRIERS)))

    def test_every_discovered_carrier_is_exercised_by_this_file(self):
        source = open(os.path.abspath(__file__), encoding="utf-8").read()
        uncovered = sorted(m for m in fallback_carriers()
                           if not re.search(r"\b%s\b" % re.escape(m), source))
        self.assertEqual(
            [], uncovered,
            "a shipped script inlines a brand-palette fallback and this file never "
            "mentions it, so its copy can drift from brand_tokens.py undetected — the "
            "failure INV-184 was written from. Add its sync assertions here: %s"
            % uncovered)


class BrandTokenSync(unittest.TestCase):
    def test_brand_tokens_importable(self):
        import brand_tokens  # noqa: F401  (fixture: the whole suite assumes this)

    def test_viz_server_fallback_in_sync(self):
        import senzing_viz_server as viz
        self.assertEqual(viz._BRAND, viz._FALLBACK_BRAND)
        self.assertEqual(viz.SOURCE_COLORS, viz._FALLBACK_SOURCE_COLORS)
        self.assertEqual(viz.FALLBACK_COLORS, viz._FALLBACK_COLORS)

    def test_recap_pdf_fallback_in_sync(self):
        import generate_recap_pdf as recap
        for name, rgb in recap._FALLBACK_RGB.items():
            self.assertEqual(getattr(recap, name), rgb,
                             f"{name} fallback diverged from brand_tokens.py")

    def test_source_stroke_fallback_in_sync(self):
        import senzing_viz_server as viz
        self.assertEqual(viz.SOURCE_STROKES, viz._FALLBACK_STROKES)

    def test_the_further_encoding_channels_are_also_in_sync(self):
        """Stroke width and fill shading are channels too, so they drift the same way."""
        import senzing_viz_server as viz
        self.assertEqual(viz.SOURCE_STROKE_WIDTHS, viz._FALLBACK_STROKE_WIDTHS)
        self.assertEqual(viz.SOURCE_FILL_SHADES, viz._FALLBACK_FILL_SHADES)

    def test_discoveries_pdf_fallback_in_sync(self):
        """The third generator with an inlined fallback — previously unguarded.

        INV-107 names `senzing_viz_server.py` and `generate_recap_pdf.py` only, so this
        one's copies could drift silently. They happened to be in sync when the
        2026-07-30 sweep checked them, and the script's own comment already claimed
        "tests/test_brand_sync.py asserts it" — which was not true until now. The literals
        also used to appear twice, once per `except` branch; they are one named dict now.

        **INV-184** is the invariant this test discharges: it generalized INV-107 from those
        two files to the pattern, which is what makes this third generator in scope at all.
        """
        import generate_discoveries_pdf as disc
        for name, rgb in disc._FALLBACK_RGB.items():
            self.assertEqual(
                getattr(disc, name), rgb,
                f"{name} fallback diverged from brand_tokens.py",
            )


    def test_recap_video_fallback_in_sync(self):
        """The recap-video renderer (#299) inlines a fallback too, so INV-184 binds it on sight.

        Its palette is keyed by the video's own names (``EMBER_END`` for brand_tokens'
        ``EMBER_GRAD_END``, and so on), mapped once in ``_TOKEN_NAMES``; the check is that the
        palette it resolved from brand_tokens equals the inlined copy, entry for entry.
        """
        import generate_recap_video as video
        self.assertEqual(set(video._FALLBACK_RGB), set(video._TOKEN_NAMES))
        for name, rgb in video._FALLBACK_RGB.items():
            self.assertEqual(video.PALETTE[name], rgb,
                             f"{name} fallback diverged from brand_tokens.py")


class SourceColorsComeFromTheData(unittest.TestCase):
    """`SOURCE_COLORS` names the Truth Set's sources, and no bootcamper uses those names
    for their own data — so a name-keyed lookup dropped every real source to one identical
    fallback color, in the module where cross-source structure is the point. Colors must be
    assigned from the sources actually present."""

    def setUp(self):
        import brand_tokens
        self.bt = brand_tokens
        self.assign = brand_tokens.color_for_sources

    def fills(self, sources):
        m = self.assign(sources)
        return [m[s]["fill"] for s in sorted(sources)]

    def test_the_reported_case_gets_distinct_colors(self):
        sources = ["PPP_LOANS", "EQUIFAX", "NOMINO-RISK"]
        fills = self.fills(sources)
        self.assertEqual(len(sources), len(set(fills)), f"sources collapsed to {set(fills)}")

    def test_truth_set_keeps_its_preferred_assignment(self):
        """The Truth Set visualization must not regress."""
        m = self.assign(["CUSTOMERS", "REFERENCE", "WATCHLIST"])
        for code, expected in self.bt.SOURCE_COLORS.items():
            with self.subTest(code=code):
                self.assertEqual(expected, m[code]["fill"])

    def test_mixed_model_never_reuses_a_preferred_color(self):
        m = self.assign(["CUSTOMERS", "PPP_LOANS", "EQUIFAX"])
        fills = [v["fill"] for v in m.values()]
        self.assertEqual(3, len(set(fills)))
        self.assertEqual(self.bt.SOURCE_COLORS["CUSTOMERS"], m["CUSTOMERS"]["fill"])

    def test_assignment_is_deterministic(self):
        """A rebuilt snapshot must match the screenshot the recap already describes."""
        self.assertEqual(self.assign(["C", "A", "B"]), self.assign(["B", "C", "A"]))

    @staticmethod
    def rendered(entry):
        """The key the browser actually draws.

        A stroke appears only when a stroke width is set, so `stroke` alone overstates the
        space: a source with no stroke still carries a stroke *color* in the returned dict.
        This mirrors the served JS exactly — `srcStrokeW(src) ? srcStroke(src) : null` for
        the color, `srcStrokeW(src) || null` for the width — which is the whole point:
        asserting on the returned tuple instead is what certified 6×3 combinations while
        the canvas had 6×4.
        """
        return (entry["fill"],
                entry["stroke"] if entry["stroke_width"] else None,
                entry["stroke_width"])

    def test_more_sources_than_colors_stay_distinguishable(self):
        """The reported case: one wrap past the palette. Kept, and still correct."""
        sources = [f"SRC{i}" for i in range(len(self.bt.FALLBACK_COLORS) + 3)]
        m = self.assign(sources)
        keys = {self.rendered(v) for v in m.values()}
        self.assertEqual(len(sources), len(keys),
                         "a second channel must distinguish the repeat")

    def test_every_size_up_to_capacity_stays_distinct_as_rendered(self):
        """The assertion the old guard should have been.

        It stopped at `len(FALLBACK_COLORS) + 3` = 9, which never approaches the encoding
        space, and it compared `(fill, stroke)`, which at n=9 agrees with the rendered key
        only by accident — no source has reached the wrap where a no-stroke entry and a
        stroked entry share a stroke color. Both under-scopings hid the same defect: the
        25th source rendered identically to the 7th.
        """
        capacity = self.bt.SOURCE_ENCODING_CAPACITY
        self.assertGreaterEqual(capacity, 64,
                                "capacity must be tested past 64; a smaller ceiling needs "
                                "to be stated in INV-127 rather than merely reached")
        for n in (2, 6, 7, 24, 25, 42, 64, capacity):
            with self.subTest(sources=n):
                m = self.assign([f"SRC_{i:04d}" for i in range(n)])
                keys = {self.rendered(v) for v in m.values()}
                if len(keys) != n:
                    seen, collided = {}, []
                    for code, v in sorted(m.items()):
                        key = self.rendered(v)
                        if key in seen:
                            collided.append(f"{seen[key]} == {code} as {key}")
                        seen[key] = code
                    self.fail(f"n={n}: {n - len(keys)} collision(s) as RENDERED — "
                              + "; ".join(collided[:4]))

    def test_the_first_size_past_capacity_warns_rather_than_colliding_silently(self):
        """An acknowledged ceiling is defensible; an invisible one is not."""
        over = self.bt.SOURCE_ENCODING_CAPACITY + 1
        with self.assertWarns(UserWarning) as caught:
            self.assign([f"SRC_{i:04d}" for i in range(over)])
        self.assertIn(str(self.bt.SOURCE_ENCODING_CAPACITY), str(caught.warning))

    def test_capacity_at_or_below_does_not_warn(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assign([f"SRC_{i:04d}"
                         for i in range(self.bt.SOURCE_ENCODING_CAPACITY)])

    def test_the_rendered_appearance_is_unchanged_where_it_was_already_correct(self):
        """Up to 24 sources the old encoding was right, so nothing may move there.

        Re-derives the pre-fix rendering — stroke drawn only when the wrap counter is
        non-zero, color `SOURCE_STROKES[cycle % 3]`, width always 1.5 — and requires the
        new code to agree with it exactly. Without this, widening the space is free to
        recolor every existing bootcamp's graph.
        """
        strokes = self.bt.SOURCE_STROKES
        for n in (2, 3, 6, 7, 12, 18, 24):
            with self.subTest(sources=n):
                codes = [f"SRC_{i:04d}" for i in range(n)]
                m = self.assign(codes)
                for i, code in enumerate(sorted(codes)):
                    cycle = i // len(self.bt.FALLBACK_COLORS)
                    expected = (self.bt.FALLBACK_COLORS[i % len(self.bt.FALLBACK_COLORS)],
                                strokes[cycle % len(strokes)] if cycle else None,
                                1.5 if cycle else None)
                    self.assertEqual(expected, self.rendered(m[code]),
                                     f"n={n} {code} changed appearance")

    def test_stroke_width_is_the_property_a_renderer_keys_on(self):
        """`cycle` must not be what decides visibility — that was the defect."""
        m = self.assign([f"SRC_{i:04d}" for i in range(50)])
        by_cycle = {}
        for v in m.values():
            by_cycle.setdefault(v["cycle"], set()).add(v["stroke_width"])
        self.assertIn(None, by_cycle[0], "cycle 0 must draw no stroke")
        widths = {w for widths in by_cycle.values() for w in widths if w}
        self.assertGreater(len(widths), 1,
                           "stroke width never varies, so it is not a channel")

    def test_signal_green_is_never_a_source_color(self):
        m = self.assign([f"S{i}" for i in range(30)])
        self.assertNotIn(self.bt.SIGNAL_GREEN, {v["fill"] for v in m.values()})

    def test_empty_and_blank_inputs_are_safe(self):
        self.assertEqual({}, self.assign([]))
        self.assertEqual({}, self.assign(None))
        self.assertEqual({}, self.assign(["", "  "]))

    def test_viz_server_inline_fallback_matches_the_token_helper(self):
        """The import-failure path must behave identically, not merely exist.

        Loaded with brand_tokens blocked, so this really runs the inline copy — see
        `load_viz_with_brand_tokens_unavailable`.
        """
        viz = load_viz_with_brand_tokens_unavailable()
        self.assertIsNot(viz.color_for_sources, self.assign,
                         "the inline copy was not reached; this compares the helper to "
                         "itself and proves nothing")
        sources = ["CUSTOMERS", "PPP_LOANS", "EQUIFAX", "NOMINO-RISK"]
        self.assertEqual(self.assign(sources), viz.color_for_sources(sources))

    def test_the_inline_fallback_matches_past_the_palette_too(self):
        """A four-source comparison agrees on both sides of the defect this fixed.

        The inline copy is only reached when brand_tokens fails to import, so a version
        that silently kept the 24-source ceiling would never be exercised in a test that
        never passes 24 sources.
        """
        viz = load_viz_with_brand_tokens_unavailable()
        for n in (7, 25, 60, self.bt.SOURCE_ENCODING_CAPACITY):
            with self.subTest(sources=n):
                sources = [f"SRC_{i:04d}" for i in range(n)]
                self.assertEqual(self.assign(sources), viz.color_for_sources(sources))


class VizServerUsesTheAssignedColors(unittest.TestCase):
    def setUp(self):
        import senzing_viz_server as viz
        self.viz = viz

    def test_rendered_page_carries_a_per_source_map(self):
        import re
        page = self.viz.render_page("T", sources=["PPP_LOANS", "EQUIFAX", "NOMINO-RISK"])
        payload = re.search(r"const SRC_COLORS=(\{.*?\});", page).group(1)
        for code in ("PPP_LOANS", "EQUIFAX", "NOMINO-RISK"):
            with self.subTest(code=code):
                self.assertIn(code, payload)
        self.assertIn('"fill"', payload)
        self.assertIn('"stroke"', payload)

    def test_no_hardcoded_single_fallback_remains(self):
        """`SRC_COLORS[src]||"#8b5cf6"` is what made every source one color."""
        page = self.viz.render_page("T", sources=["A", "B"])
        self.assertNotIn('SRC_COLORS[src]||"#8b5cf6"', page)

    def test_unassigned_source_is_visually_distinct_from_assigned_ones(self):
        """"Unassigned" must not masquerade as a real category."""
        page = self.viz.render_page("T", sources=["A", "B", "C"])
        self.assertIn("UNKNOWN_SRC", page)
        self.assertNotIn(f'UNKNOWN_SRC="{self.viz.FALLBACK_COLORS[0]}"', page)

    def test_fallback_colors_are_actually_consumed(self):
        """The palette existed but was dead code; the defect was that nothing used it."""
        page = self.viz.render_page("T", sources=["ONE", "TWO"])
        self.assertIn(self.viz.FALLBACK_COLORS[0], page)

    def test_the_page_carries_the_stroke_width_channel(self):
        """A widened assignment the renderer ignores changes nothing on screen."""
        page = self.viz.render_page("T", sources=[f"SRC_{i:04d}" for i in range(30)])
        self.assertIn('"stroke_width"', page,
                      "the per-source map does not carry the width channel")
        self.assertIn("function srcStrokeW(", page,
                      "nothing in the page can read the width channel")

    def test_no_draw_site_keys_on_the_wrap_counter(self):
        """`cycle` does not reach the canvas; keying on it is what capped the space at 24."""
        page = self.viz.render_page("T", sources=["A", "B"])
        self.assertNotIn("srcCycle", page,
                         "a draw site still decides stroke visibility from the wrap "
                         "counter, so widths and shades never render")

    def test_the_legend_and_the_node_use_the_same_expression(self):
        """Criterion: swatch and mark must agree for the same key above 24 sources.

        ⚠️ The node's expression changed on 2026-08-17 from `d.data_sources[0]` to
        `srcKeyOf(d)` — a node is colored by its whole source COMBINATION, not by whichever
        of its sources sorts first. The criterion is unchanged: both sides still resolve
        through `srcStyle`, so a swatch and the marks it describes cannot disagree. For a
        single-source entity `srcKeyOf(d)` degenerates to that source code, which is why
        the single-source legend rows still key on `s`.
        """
        page = self.viz.render_page("T", sources=["A", "B"])
        node = 'var k=srcKeyOf(d);return srcStrokeW(k)?srcStroke(k):null;'
        legend = 'srcStrokeW(s)?("inset 0 0 0 "+srcStrokeW(s)+"px "+srcStroke(s)):null'
        self.assertIn(node, page, "the node stroke is not derived from the width channel")
        self.assertIn(legend, page,
                      "the legend swatch does not mirror the node's stroke and width, so "
                      "the two can describe different appearances for one key")

    def test_model_reports_its_data_sources_sorted(self):
        model = self.viz.Model()
        model.entities = {
            1: {"data_sources": ["WATCHLIST", "CUSTOMERS"]},
            2: {"data_sources": ["CUSTOMERS", ""]},
        }
        self.assertEqual(["CUSTOMERS", "WATCHLIST"], model.data_sources())


if __name__ == "__main__":
    unittest.main()
