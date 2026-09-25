"""The source-set encoding check is contract behavior, not a Python-reference feature.

INV-259 requires a graph node's fill, stroke and stroke width to derive from the entity's whole
**sorted set** of data sources. That rule is stated in three places -- the any-language contract,
Module 7 step 3c, and the invariant itself -- and on **2026-08-25** it was still re-implemented
wrong in a generated Java app, which colored from `data_sources[0]`: 294 of 5,619 cross-source
entities rendered in a single-source color, beneath a legend saying they were single-source. The
bundled Python reference was already correct and had been for eight days; the defect reappeared
where the rule had to be *followed* rather than *inherited*.

⛔ **So the gap was never a missing rule -- it was that nothing checked the generated app against
one.** This guard covers the check that closes it: the **combination rows** the legend names MUST
equal the combination keys among the sorted source-set keys over the nodes drawn. First-source
coloring collapses every combination onto a single-source key, so the legend names 0 combination
rows against N exactly when the misencoding is present.

⛔ **Corrected 2026-09-25 (#159) -- this guard previously pinned "legend color keys MUST equal
distinct source-set keys".** The legend also names one per-source *participation* row per source,
which is not a source-set key, so its total exceeds the key count whenever a source appears in view
only inside combinations. On a Bootcamper's capped graph (9,820 entities, 1,500 emitted, `OFAC`'s 4
unrelated single-source entities cut) that stopped a correctly encoded capture: 8 keys, 9 rows.
`TheLegendModelAgreesWithTheCheck` below models the legend's rows over that shape.

⚠️ **INV-002 is the reason this guard exists at all.** A check that lives only in
`senzing_viz_server.py` reaches generated code solely through the reference -- the failure INV-164
and INV-190 each had to record case by case, and precisely the failure that produced this
recurrence. So the assertions below are about the **contract** and the **build steps**; the
reference is checked separately, for behavior, and must not be the only place the rule exists.

⚠️ **INV-265 is the other half.** With no combination key in view -- one registered data source,
or several sharing no entity -- the comparison cannot fail, and a "pass" would be agreement from a
match that could not disagree. So a build site must be able to say **not exercised** rather than
passed.

⛔ **Corrected 2026-08-28 -- this docstring previously called that "the *normal* Truth Set
situation ... why the module that builds the app cannot provoke the defect". It is false.** The
Truth Set registers three data sources (CUSTOMERS, REFERENCE, WATCHLIST, 159 records) and one full
load emitted 7 distinct source-set keys, 4 of them combinations, so the comparison is live at the
Truth Set site too. The assertions below were never wrong -- they require each build site to *name*
the not-exercised outcome, which is correct in either case -- but the premise stated around them
was, and a false premise in a guard's own prose reads as reviewed. INV-270 carried the same claim
and was corrected in place the same day.

Stdlib only. The contract and build steps are read as text; the reference's own check is exercised
by import, which is a dev-only read of a bundled script (INV-108).

Enforces **INV-270** (the graph endpoint exposes the distinct source-set key count, the build
step compares the legend's combination rows against the combination keys before capture, and with
no combination key in view it reports *not exercised* rather than a pass).

Source spec: `specs/the-source-set-coloring-rule-is-stated-three-times-and-verified-nowhere.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
CONTRACT = SKILLS / "module-03b-truthset-visualization" / "visualization-api-reference.md"

#: The field the contract defines and both build steps compare against. One name, so a build step
#: cannot claim to run the check while comparing something else.
FIELD = "encoding_check"
COUNT_FIELD = "distinct_source_set_keys"
COMBO_FIELD = "combination_keys"

#: The toggle that, left on, puts the graph in relationship mode -- whose legend has no source-color
#: rows. Above 400 nodes it is on by default, so a build site must say to clear it before counting.
TOGGLE = "Show only entities with relationships"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def build_sites():
    """The shipped steps that stand up the app and capture from it.

    Derived by scanning for steps that invoke the bundled capture script, rather than by naming
    paths (INV-246): a third module that builds the app inherits this guard.
    """
    out = []
    for path in sorted(SKILLS.glob("**/*.md")):
        text = flat(path)
        if "capture_screenshots.py" in text and FIELD in text:
            out.append((path, text))
    return out


class TheContractStatesItAsBehavior(unittest.TestCase):
    """INV-002 — stated for every language, not only in the reference."""

    def setUp(self):
        self.text = flat(CONTRACT)

    def test_the_contract_defines_the_self_check(self):
        self.assertIn(FIELD, self.text,
                      "the any-language contract does not define the encoding self-check, so it "
                      "can only reach generated code through the Python reference (INV-002)")
        self.assertIn(COUNT_FIELD, self.text)
        self.assertIn(COMBO_FIELD, self.text)

    def test_it_is_marked_required_and_language_neutral(self):
        self.assertRegex(
            self.text,
            r"encoding self-check \(required — behavior, in every language\)",
            "the self-check section is not marked required-behavior-in-every-language, the heading "
            "form the rest of this contract uses for rules that bind generated code",
        )

    def test_it_states_the_equality_that_detects_the_defect(self):
        self.assertRegex(
            self.text,
            r"(?i)combination rows the legend names\*?\*?.{0,40}MUST equal\s+`?len\(combination_keys\)",
            "the contract does not state the equality between the legend's combination rows and "
            "len(combination_keys), which is the whole detection mechanism (INV-270)",
        )

    def test_it_does_not_compare_every_legend_row(self):
        """#159 -- the withdrawn comparison false-alarms on a correctly encoded capped graph."""
        self.assertNotRegex(
            self.text,
            r"(?i)legend names\*?\*? MUST equal\s+`?distinct_source_set_keys",
            "the contract compares every legend row with distinct_source_set_keys again; per-source "
            "rows are not source-set keys, so that stops a correct capture whenever a source is in "
            "view only inside combinations (INV-270, corrected 2026-09-25)",
        )

    def test_it_reads_the_source_legend_not_the_relationship_legend(self):
        self.assertRegex(
            self.text, r"(?i)read it off the \*\*source\*\* legend",
            "the contract does not say which legend to count; the relationship legend has no "
            "source-color rows",
        )

    def test_it_explains_why_the_equality_catches_first_source_coloring(self):
        self.assertRegex(
            self.text, r"(?i)collapses every combination onto a single-source key",
            "the contract states the check without saying why it works, so a reader cannot tell "
            "whether a mismatch is the defect or a bug in the check",
        )

    def test_it_requires_not_exercised_rather_than_passed(self):
        """INV-265 — an empty or trivial match is an unrun check, never agreement."""
        self.assertIn("not_exercised", self.text)
        self.assertRegex(
            self.text, r"(?i)never \"passed\"|never ['\"]?passed",
            "the contract does not forbid reporting a pass when the check cannot fail (INV-265)",
        )
        self.assertRegex(
            self.text, r"(?i)no combination key in view means the check was not exercised",
            "the contract's not-exercised condition is not 'no combination key in view', the one "
            "state in which the combination-row comparison cannot fail (INV-265)",
        )

    def test_it_stops_before_capture_on_a_mismatch(self):
        self.assertRegex(
            self.text, r"(?i)stop and fix the encoding before capturing",
            "the contract does not require stopping before capture on a mismatch, so the wrong "
            "picture is captured into the recap and found afterwards",
        )


class BothBuildSitesInvokeIt(unittest.TestCase):
    def test_two_build_sites_are_found(self):
        found = build_sites()
        self.assertGreaterEqual(
            len(found), 2,
            "fewer than the two shipped build sites reference the encoding check — the Truth Set "
            f"build and Module 7 step 3c must both run it (found {len(found)})",
        )

    def test_each_build_site_compares_against_the_contract_field(self):
        for path, text in build_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertRegex(
                    text, r"combination rows\*?\*? the source legend names against "
                          r"`len\(encoding_check\.combination_keys\)`",
                    "the build step does not compare the source legend's combination rows against "
                    "len(encoding_check.combination_keys), so 'run the check' is unfalsifiable or "
                    "compares the withdrawn totals (INV-270)",
                )

    def test_each_build_site_clears_the_relationship_toggle_first(self):
        """Above 400 nodes the default view is relationship mode, with no source legend."""
        for path, text in build_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertRegex(
                    text, r'(?i)uncheck "' + re.escape(TOGGLE) + '"',
                    "the build step does not say to uncheck the relationship toggle before "
                    "counting, so on real data it reads a legend with no source colors",
                )

    def test_each_build_site_names_the_new_not_exercised_condition(self):
        for path, text in build_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertRegex(
                    text, r"(?i)no\s+combination key (?:is )?in view",
                    "the build step does not report not-exercised on 'no combination key in "
                    "view' (INV-265)",
                )

    def test_each_build_site_stops_rather_than_capturing_on_a_mismatch(self):
        for path, text in build_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertRegex(
                    text, r"(?i)fix the encoding.{0,80}(?:before capture|re-render before capture)"
                          r"|stop and\s+fix the encoding",
                    "the build step does not say to stop and fix before capturing, so a mismatch "
                    "still produces screenshots of the wrong encoding",
                )

    def test_the_truthset_site_says_the_check_is_usually_vacuous_there(self):
        """The defect's whole survival mechanism, stated where it applies."""
        truthset = [t for p, t in build_sites() if "module-03b" in str(p)]
        self.assertTrue(truthset, "the Truth Set build site no longer references the check")
        self.assertRegex(
            truthset[0], r"(?i)not exercised|not_exercised",
            "the Truth Set build step does not name the not-exercised outcome, which it must be "
            "able to report when a load registers fewer than two data sources (INV-265). Note the "
            "Truth Set itself carries three, so a real verdict is the expected result there",
        )

    def test_the_module7_site_says_the_check_has_teeth_there(self):
        module7 = [t for p, t in build_sites() if "module-07" in str(p)]
        self.assertTrue(module7, "Module 7 step 3c no longer references the check")
        self.assertRegex(
            module7[0], r"(?i)not vacuous|has teeth|multi-source by construction",
            "Module 7 step 3c does not say the check is meaningful on the bootcamper's data, "
            "which is the one run where the defect actually shows",
        )


class TheReferenceImplementsIt(unittest.TestCase):
    """Behavior, exercised -- the reference must stay a correct example of the contract."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SCRIPTS))
        from senzing_viz_server import Model  # noqa: E402
        # staticmethod(...) so `self.check(nodes)` does not bind `self` as the first argument.
        cls.check = staticmethod(Model._encoding_check)

    def test_a_cross_source_set_is_keyed_by_the_whole_sorted_set(self):
        result = self.check([{"data_sources": ["REFERENCE", "CUSTOMERS"]}])
        self.assertEqual(["CUSTOMERS|REFERENCE"], result["source_set_keys"],
                         "the key is not the sorted, joined source set (INV-259)")

    def test_key_order_does_not_depend_on_input_order(self):
        a = self.check([{"data_sources": ["REFERENCE", "CUSTOMERS"]}])
        b = self.check([{"data_sources": ["CUSTOMERS", "REFERENCE"]}])
        self.assertEqual(a["source_set_keys"], b["source_set_keys"])

    def test_a_single_source_corpus_is_not_exercised_rather_than_ok(self):
        """INV-265 — a single-source corpus must not report agreement.

        ⚠️ Not "the Truth Set case": the Truth Set has three data sources. The corpus built
        below is synthetic and single-source on purpose, which is System verification's
        `VERIFY` shape rather than the Truth Set's.
        """
        result = self.check([{"data_sources": ["CUSTOMERS"]}] * 5)
        self.assertEqual("not_exercised", result["status"])
        self.assertNotIn("passed", result["detail"].lower())

    def test_a_combination_key_is_exercised(self):
        result = self.check([{"data_sources": ["A"]}, {"data_sources": ["A", "B"]}])
        self.assertEqual("ok", result["status"])
        self.assertEqual(2, result["distinct_source_set_keys"])
        self.assertEqual(["A|B"], result["combination_keys"])

    def test_several_sources_with_no_combination_are_not_exercised(self):
        """INV-265 -- the narrowing #159 made: 0 combination rows against 0 cannot disagree."""
        result = self.check([{"data_sources": ["A"]}, {"data_sources": ["B"]}])
        self.assertEqual(2, result["distinct_source_set_keys"])
        self.assertEqual([], result["combination_keys"])
        self.assertEqual("not_exercised", result["status"])
        self.assertNotIn("passed", result["detail"].lower())

    def test_the_detail_states_the_combination_row_comparison(self):
        detail = self.check([{"data_sources": ["A", "B"]}])["detail"]
        self.assertIn("combination rows", detail)
        self.assertIn("len(combination_keys)", detail)
        self.assertNotIn("Compare distinct_source_set_keys", detail,
                         "the detail string states the withdrawn comparison (#159)")

    def test_empty_and_sourceless_nodes_do_not_raise_or_pass(self):
        for nodes in ([], [{}], [{"data_sources": []}]):
            with self.subTest(nodes=nodes):
                self.assertEqual("not_exercised", self.check(nodes)["status"])

    def test_the_graph_payload_carries_the_field(self):
        source = (SCRIPTS / "senzing_viz_server.py").read_text(encoding="utf-8")
        self.assertRegex(
            source, r'"encoding_check":\s*self\._encoding_check\(nodes\)',
            "the graph payload does not carry encoding_check, so the build step has nothing to read",
        )

    def test_the_reference_still_colors_by_the_whole_set(self):
        """Unchanged by this spec -- srcKeyOf must survive at all three attributes.

        Asserted per attribute rather than by counting call sites: a count is wrong the
        moment anything nearby is refactored, while "fill derives from the set key" is the
        property INV-259 actually requires. Leaving any ONE of the three reading the first
        source keeps a partial version of the same misencoding, so each is named.
        """
        source = (SCRIPTS / "senzing_viz_server.py").read_text(encoding="utf-8")
        self.assertIn("function srcKeyOf(d)", source)
        # assertTrue(re.search(...)) rather than assertRegex: a failed assertRegex embeds the
        # whole 240KB script in its message, which buries the finding it is reporting.
        for attribute, pattern in (
            ("fill", r'\.attr\("fill",.{0,80}?srcKeyOf\(d\)'),
            ("stroke", r'\.attr\("stroke",.{0,80}?srcKeyOf\(d\)'),
            ("stroke-width", r'\.attr\("stroke-width",.{0,80}?srcKeyOf\(d\)'),
        ):
            with self.subTest(attribute=attribute):
                self.assertTrue(
                    re.search(pattern, source),
                    f"the node's {attribute} no longer derives from srcKeyOf, so cross-source "
                    "entities are encoded by one member of their source set (INV-259)",
                )
        self.assertTrue(
            re.search(r"srcKeyOf\(n\);\s*if\(isCombo\(k\)\)", source),
            "the legend no longer counts combinations over the source-set key, so a color on "
            "screen can have no row naming it (INV-259)",
        )


# -- The legend, modeled -------------------------------------------------------------------------
# A stdlib test cannot run the page's `drawLegend`, so these mirror how it derives its rows, and
# `TheModelIsWiredToThePage` below pins the page to the same derivation.

def src_key_of(node):
    """The page's `srcKeyOf`: the whole sorted source set, joined (INV-259)."""
    sources = node.get("data_sources") or []
    return "|".join(sorted(sources)) if sources else ""


def first_source_key(node):
    """The INV-259 defect: keyed by one member of the set, as the 2026-08-25 Java app did."""
    sources = node.get("data_sources") or []
    return sources[0] if sources else ""


def legend_combination_rows(nodes, key_of=src_key_of):
    """`drawLegend`'s combination rows: one per distinct combination key over the drawn nodes."""
    return sorted({k for k in map(key_of, nodes) if "|" in k})


def legend_source_rows(nodes):
    """`drawLegend`'s per-source participation rows: one per source any drawn node carries."""
    return sorted({s for n in nodes for s in n.get("data_sources") or []})


def model_with(viz, entities, edges=()):
    model = viz.Model()
    model.entities = {
        e["entity_id"]: {"record_count": 1, "entity_name": "E%d" % e["entity_id"], **e}
        for e in entities
    }
    model.edges = {pair: {"match_key": "+NAME", "relationship_type": "POSSIBLY_SAME"}
                   for pair in edges}
    return model


def capped_population():
    """The 2026-09-25 shape, scaled down: 5 combinations, and `OFAC` only inside them once capped.

    Every entity spanning sources outranks every single-source one, and among single-source
    entities the four unrelated `OFAC` ones rank last, so a cap of `total - 4` cuts exactly them --
    by the reference's own ranking, not by a hand-picked slice.
    """
    combos = (["GLEIF", "ICIJ"], ["GLEIF", "OFAC"], ["ICIJ", "OFAC"],
              ["OFAC", "OPEN-SANCTIONS"], ["GLEIF", "ICIJ", "OFAC"])
    singles = ("GLEIF", "ICIJ", "OPEN-SANCTIONS")
    entities, edges, eid = [], [], 0
    for sources in combos:
        for _ in range(2):
            eid += 1
            entities.append({"entity_id": eid, "data_sources": list(reversed(sources))})
    for source in singles:
        for _ in range(3):
            eid += 1
            entities.append({"entity_id": eid, "data_sources": [source]})
            edges.append((1, eid))  # connected, so they outrank the unrelated OFAC singletons
    for _ in range(4):
        eid += 1
        entities.append({"entity_id": eid, "data_sources": ["OFAC"]})
    return entities, edges


#: Uncapped, with `WATCHLIST` present only inside combinations -- no cap needed to trip it.
UNCAPPED = [
    {"entity_id": 1, "data_sources": ["CUSTOMERS"]},
    {"entity_id": 2, "data_sources": ["REFERENCE"]},
    {"entity_id": 3, "data_sources": ["WATCHLIST", "CUSTOMERS"]},
    {"entity_id": 4, "data_sources": ["REFERENCE", "CUSTOMERS"]},
    {"entity_id": 5, "data_sources": ["WATCHLIST", "REFERENCE", "CUSTOMERS"]},
]


class TheLegendModelAgreesWithTheCheck(unittest.TestCase):
    """#159 -- no false alarm when a source is in view only inside combinations; the defect still fails."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SCRIPTS))
        import senzing_viz_server as viz  # noqa: E402
        entities, edges = capped_population()
        capped = model_with(viz, entities, edges).graph(cap=len(entities) - 4)
        uncapped = model_with(viz, UNCAPPED).graph()
        cls.graphs = {"capped": capped, "uncapped": uncapped}

    def test_the_fixtures_reproduce_the_false_alarm(self):
        """⛔ INV-265 -- if the old comparison agreed here, these fixtures would test nothing."""
        capped = self.graphs["capped"]
        self.assertTrue(capped["capped"], "the capped fixture was not capped")
        self.assertEqual(8, capped["encoding_check"]["distinct_source_set_keys"])
        self.assertEqual(5, len(capped["encoding_check"]["combination_keys"]))
        for name, graph in self.graphs.items():
            with self.subTest(graph=name):
                nodes = graph["nodes"]
                old_legend_keys = (len(legend_combination_rows(nodes))
                                   + len(legend_source_rows(nodes)))
                self.assertGreater(
                    old_legend_keys, graph["encoding_check"]["distinct_source_set_keys"],
                    "the fixture no longer has a source in view only inside combinations, so it "
                    "cannot show the withdrawn comparison's false alarm")

    def test_whole_set_keying_matches_on_capped_and_uncapped_graphs(self):
        for name, graph in self.graphs.items():
            with self.subTest(graph=name):
                check = graph["encoding_check"]
                self.assertEqual("ok", check["status"])
                self.assertEqual(
                    len(check["combination_keys"]), len(legend_combination_rows(graph["nodes"])),
                    "a correctly encoded graph reports a mismatch (#159)")

    def test_first_source_keying_still_fails_on_capped_and_uncapped_graphs(self):
        for name, graph in self.graphs.items():
            with self.subTest(graph=name):
                check = graph["encoding_check"]
                rows = legend_combination_rows(graph["nodes"], key_of=first_source_key)
                self.assertEqual([], rows)
                self.assertNotEqual(
                    len(check["combination_keys"]), len(rows),
                    "first-source coloring no longer fails the check (INV-259, INV-270)")


class TheModelIsWiredToThePage(unittest.TestCase):
    """The Python model above is only evidence while the page derives its rows the same way."""

    @classmethod
    def setUpClass(cls):
        source = (SCRIPTS / "senzing_viz_server.py").read_text(encoding="utf-8")
        cls.source = source
        start = source.find("function drawLegend(nodes){")
        end = source.find("\nfunction ", start + 1)
        cls.draw_legend = source[start:end] if start >= 0 else ""

    def test_draw_legend_is_found(self):
        self.assertTrue(self.draw_legend, "drawLegend(nodes) is gone from the embedded page")

    def test_src_key_of_is_the_sorted_joined_set(self):
        self.assertIn('function srcKeyOf(d){var s=(d&&d.data_sources)||[];'
                      'return s.length?s.slice().sort().join("|"):"";}', self.source)
        self.assertIn('function isCombo(k){return k.indexOf("|")>=0;}', self.source)

    def test_combination_rows_come_from_src_key_of_over_the_drawn_nodes(self):
        for what, pattern in (
            ("counts keyed by srcKeyOf over nodes",
             r"\(nodes\|\|\[\]\)\.forEach\(function\(n\)\{const k=srcKeyOf\(n\);"
             r"if\(isCombo\(k\)\)comboCounts\[k\]="),
            ("one row per combination key", r"const combos=Object\.keys\(comboCounts\)"),
            ("the rows drawn from those keys", r"combos\.forEach\(function\(k\)"),
            ("per-source rows from each node's sources",
             r"\(n\.data_sources\|\|\[\]\)\.forEach\(function\(s\)\{counts\[s\]="),
        ):
            with self.subTest(what=what):
                self.assertTrue(re.search(pattern, self.draw_legend),
                                "drawLegend no longer derives its rows as the test models them: "
                                + what)

    def test_the_legend_is_drawn_from_the_rendered_nodes(self):
        self.assertTrue(re.search(r"else\{drawLegend\(nodes\);\}", self.source),
                        "the source legend is not drawn from the rendered nodes")


if __name__ == "__main__":
    unittest.main()
