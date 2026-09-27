"""Every globalization retrieval site carries the filter, and one site carries the strategy.

Module 5 told the guide to answer four questions — UTF-8 encoding, non-Latin support,
cross-script name matching, multi-language data quality practices — from a single
`search_docs(query="globalization")`, then said "Never answer from training data". Asked live
on server 1.32.9 (2026-08-13), that query ranked the Rust SDK's `static GLOBAL_ENVIRONMENT`,
`postgresql-performance-v4`'s "Global — more workers" and an MDM-Lite FAQ on "globally unique
ID" among its top hits, its best Globalization Guide hit was a title-only stub, and the UTF-8
answer was not there at all. That is INV-212's originating shape: an output shape wider than
one obvious query returns, with no strategy for closing the difference, so the step forces a
choice between fabricating and under-delivering.

⚠️ **That census went stale, and the instruction built on it inverted (#149).** After the docs
index was rebuilt (server 1.37.13, docs index 2026-09-24 18:45 UTC), the same query returns
Globalization Guide sections with real prose, ahead of the three unrelated matches. Module 5
still called the Guide hit a stub and said that seeing these results proved a mis-query, so a
guide following it would discard correct content. What lasts is the property, not the ranks:
the bare term admits unrelated `Global*` substring matches, and it did not return the "What
languages does Senzing support?" section on either index, so `category='globalization'` stays
the route. `TheBareQueryParagraphStatesAPropertyNotACensus` keeps the stale reading out.

Three sites asked for this material and they disagreed — `phase3-test-load.md` already passed
`category='globalization'`; `SKILL.md` and `phase2-data-mapping.md` did not. INV-212 had been
registered the same day and applied only at the site its own spec was working on, which is the
"rule applied to some of the sites it binds" class.

⚠️ **Asserts structure, not the corpus's wording (INV-219).** What must not regress is that
every site filters, that exactly one site owns the strategy while the others point at it
(INV-183's no-fork clause), and that the strategy names both query traps. The section titles
and prose quoted in the guidance are the server's and may be reworded upstream; pinning them
here would fail whoever corrects them. The one exception is the literal `category` value,
which is an enumerated parameter of the tool rather than documentation prose.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_05 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
             / "module-05-data-quality-mapping")

STRATEGY_SITE = MODULE_05 / "SKILL.md"
POINTER_SITES = (MODULE_05 / "phase2-data-mapping.md",
                 MODULE_05 / "phase3-test-load.md")

#: A globalization retrieval call in shipped guidance, however its query is spelled.
#: ⚠️ Line-scoped (`[^)\n]`) on purpose. The first version used `[^)]`, which matches newlines,
#: so an *unclosed* call would still match by running past the fence to a `)` paragraphs away —
#: the guard would report a malformed call as well-formed. No such call shipped; this was
#: tightened after a truncated terminal read made one look unclosed, and the false alarm was
#: worth the fix: nothing else in the suite checks that a prescribed call is even syntactic.
GLOBALIZATION_CALL = re.compile(r"search_docs\([^)\n]*globalization[^)\n]*\)")


def text(path):
    return path.read_text(encoding="utf-8")


def prose(path):
    """The guidance with HTML comments removed — a marker QUOTES the call it warns about."""
    return re.sub(r"<!--.*?-->", " ", text(path), flags=re.S)


#: Framing that marks a quoted call as the anti-pattern rather than the instruction.
COUNTER_EXAMPLE = ("does not reach", "bare ", "Bare ")


class EveryGlobalizationRetrievalFilters(unittest.TestCase):
    """A bare `globalization` query reaches homonyms; the filter is what makes it a route.

    ⚠️ The strategy site legitimately *quotes* the unfiltered call in order to forbid it, so
    this asserts every unfiltered occurrence is framed as a counter-example — not that the
    string is absent. Banning a string on the line whose purpose is to forbid it is the
    self-defeating guard shape INV-219 records, and the first draft of this test did exactly
    that: it failed on the ⛔ warning and on the MCP-NEGATIVE marker.
    """

    def test_pointer_sites_only_ever_prescribe_the_filtered_call(self):
        for path in POINTER_SITES:
            calls = GLOBALIZATION_CALL.findall(prose(path))
            with self.subTest(site=path.name):
                self.assertTrue(
                    calls,
                    "%s no longer retrieves globalization material; if that is deliberate, "
                    "drop it from this guard rather than leaving a dead assertion" % path.name,
                )
                for call in calls:
                    self.assertIn(
                        "category=", call,
                        "%s calls search_docs for globalization without category="
                        "'globalization'. Unfiltered, the query also admits unrelated "
                        "Global* matches (the Rust SDK's GLOBAL_ENVIRONMENT, PostgreSQL "
                        "autovacuum tuning), and it is not the route that returns the "
                        "'What languages does Senzing support?' section (INV-212)" % path.name,
                    )

    def test_the_strategy_prescribes_a_filtered_call(self):
        calls = GLOBALIZATION_CALL.findall(prose(STRATEGY_SITE))
        self.assertTrue(any("category=" in c for c in calls),
                        "the strategy must prescribe the filtered call, not only warn")

    def test_any_unfiltered_call_in_the_strategy_is_framed_as_the_anti_pattern(self):
        for para in prose(STRATEGY_SITE).split("\n\n"):
            for call in GLOBALIZATION_CALL.findall(para):
                if "category=" in call:
                    continue
                with self.subTest(call=call[:50]):
                    self.assertTrue(
                        any(cue in para for cue in COUNTER_EXAMPLE),
                        "an unfiltered globalization call appears with no framing marking it "
                        "as the wrong route; a reader cannot tell it from the instruction",
                    )

    def test_no_pointer_site_carries_best_practices_as_query_vocabulary(self):
        """"best practices" ranks Dockerfile/Markdown-lint docs above the Guide."""
        for path in POINTER_SITES:
            for call in GLOBALIZATION_CALL.findall(prose(path)):
                with self.subTest(site=path.name):
                    self.assertNotIn(
                        "best practices", call,
                        "the phrase 'best practices' inside a globalization query returns "
                        "senzingsdk-tools/senzingsdk-runtime docs/best-practices.md above "
                        "the on-topic rows",
                    )


class ExactlyOneSiteOwnsTheStrategy(unittest.TestCase):
    """INV-183: named and linked at the step, never forked into a second copy."""

    def setUp(self):
        self.strategy = text(STRATEGY_SITE)      # markers live in HTML comments
        #: Comment-stripped, for anything a GUIDE must be able to read. A marker mentioning a
        #: trap must not satisfy an assertion about the visible warning — it did once: adding
        #: `docs/best-practices.md` to a marker let the trap be deleted from the prose with
        #: this test still green.
        self.visible = prose(STRATEGY_SITE)

    def test_the_strategy_site_cites_inv212(self):
        self.assertIn("INV-212", self.visible)

    def test_the_strategy_names_the_document_where_it_prescribes_the_call(self):
        """Scoped to the prescribing paragraph, not the file.

        ⚠️ The first version asserted the name appeared *anywhere*, and its mutation escaped:
        the trap warning also quoted `# Senzing Globalization Guide` (at the time, as a
        title-only stub; #149 removed that description once the index stopped returning a
        stub), so deleting the name from the instruction left the assertion green. Sixth
        recorded instance in this repo of asserting a token exists rather than where the claim
        is made. The trap warning still names the Guide, so the scoping is still what matters.
        """
        blocks = prose(STRATEGY_SITE).split("\n\n")
        #: The call may sit in a fenced block of its own, which makes the lead-in naming the
        #: document the PREVIOUS block — so the region is the call's block plus the one before.
        prescribing = [blocks[i - 1] + "\n\n" + b if i else b
                       for i, b in enumerate(blocks)
                       if any("category=" in c for c in GLOBALIZATION_CALL.findall(b))]
        self.assertTrue(prescribing, "no paragraph prescribes the filtered call")
        self.assertTrue(
            any("Senzing Globalization Guide" in p for p in prescribing),
            "the paragraph prescribing the filtered call must name the document that holds "
            "the material; a filter with no document is half a retrieval strategy (INV-212)",
        )

    def test_the_strategy_names_both_query_traps(self):
        """Each trap is a distinct wrong-content route; naming one leaves the other live."""
        self.assertIn("GLOBAL_ENVIRONMENT", self.visible,
                      "the bare-query trap must be named, or a guide seeing it concludes "
                      "the documentation is thin")
        self.assertIn("best-practices.md", self.visible,
                      "the 'best practices' trap must be named; it outranks the on-topic rows")

    def test_the_strategy_marks_its_negatives_for_re_asking(self):
        """A routing negative with no marker is invisible to coverage_reports.py.

        ⚠️ The token is assembled at runtime on purpose. Written as a literal, this line is
        itself marker-shaped, and `coverage_reports.py negatives` reported this test file as a
        third MALFORMED marker — a guard polluting the worklist it exists to protect.
        """
        token = "MCP-" + "NEGATIVE:"
        markers = [ln for ln in self.strategy.split("\n") if token in ln]
        self.assertTrue(markers, "the strategy's tool-absence claims carry no marker")
        for marker in markers:
            with self.subTest(marker=marker.strip()[:60]):
                self.assertIn("owner:", marker,
                              "a marker without an owner: clause does not parse (INV-209)")
                self.assertRegex(
                    marker, r"server \d+\.\d+\.\d+, \d{4}-\d{2}-\d{2}",
                    "a marker must carry its server version and date ON ONE LINE — the "
                    "scanner's regex is not DOTALL, so a wrapped marker falls off the "
                    "worklist entirely, which is worse than having none",
                )

    def test_the_pointer_sites_point_rather_than_restate(self):
        for path in POINTER_SITES:
            body = text(path)
            with self.subTest(site=path.name):
                self.assertIn("SKILL.md", body,
                              "%s must point at the module SKILL.md strategy" % path.name)
                self.assertNotIn(
                    "Senzing Globalization Guide", body,
                    "%s restates the strategy instead of pointing at it, forking a second "
                    "copy that can drift (INV-183)" % path.name,
                )


#: A paragraph that quotes the unfiltered call. It is found by the call literal (either quote
#: style), or by the "bare `globalization`" phrasing the pre-#149 text used, so restoring the old
#: paragraph is still caught rather than slipping past a finder that no longer recognizes it.
#: Two paragraphs match today: the "Multi-language data" lead-in, which points at the filtered
#: call, and the trap warning, which is the one naming the unrelated `Global*` matches.
BARE_QUERY_CUE = re.compile(
    r"search_docs\(query=['\"]globalization['\"]\)|\bbare\s+`globalization`", re.IGNORECASE)
#: Describing a Guide hit as having no content. True on the 2026-08-13 index, false since the
#: 2026-09-24 rebuild, and the reason Module 5 told the guide to discard correct results.
STUB_DESCRIPTION = re.compile(
    r"(?i)\bstubs?\b|title-only|\bno prose\b|without prose|\bbare title\b")
#: Telling the guide that seeing these results means it asked wrongly.
MIS_QUERY = re.compile(r"(?i)mis-?quer(?:y|ied|ies|ying)|evidence you\b")
#: A ranking census. A rank order is what went stale; the property does not rank anything.
RANK_CENSUS = re.compile(r"(?i)\btop hits?\b|\branks?\b|\branked\b|highest-ranked|best guide hit")


class TheBareQueryParagraphStatesAPropertyNotACensus(unittest.TestCase):
    """#149: the bare-query warning must not tell the guide to discard correct Guide content.

    On the 2026-09-24 index the bare query returns Globalization Guide sections with prose.
    The shipped paragraph still called the best Guide hit a title-only stub and said seeing
    these results was evidence of a mis-query, so the instruction inverted. The durable part
    is a property: the bare term also admits unrelated `Global*` matches, and the category
    filter stays the route.

    ⚠️ Scoped to ONE paragraph on purpose. The "best practices" paragraph legitimately says
    "title-only stubs" and "evidence you mis-queried", because both still hold for that query,
    and the HTML-comment markers are stripped because they quote what they record. A file-wide
    ban would fail on the correct trap, which is the self-defeating guard shape INV-219 names.
    """

    def setUp(self):
        blocks = prose(STRATEGY_SITE).split("\n\n")
        #: Every paragraph quoting the bare call: none may call a Guide hit a stub or a mis-query.
        self.bare = [b for b in blocks if BARE_QUERY_CUE.search(b)]
        #: The trap warning itself: the one that names an unrelated `Global*` match.
        self.trap = [b for b in self.bare if "GLOBAL_ENVIRONMENT" in b]
        self.best_practices = [b for b in blocks if "best-practices.md" in b]

    def test_the_bare_query_paragraph_exists_and_stands_alone(self):
        self.assertEqual(
            1, len(self.trap),
            "expected exactly one paragraph warning about the bare globalization call and "
            "naming GLOBAL_ENVIRONMENT; found %d. The guard below reads that paragraph, so a "
            "missing one leaves it vacuous" % len(self.trap))
        self.assertNotIn(
            "best-practices.md", self.trap[0],
            "the two query traps must sit in separate paragraphs, so the 'best practices' "
            "trap's mis-query sentence cannot read as covering the bare query (#149)")

    def test_it_does_not_call_a_guide_hit_a_stub(self):
        self.assertTrue(self.bare, "no paragraph quotes the bare call; the guard is vacuous")
        for para in self.bare:
            m = STUB_DESCRIPTION.search(para)
            self.assertIsNone(
                m,
                "the bare-query paragraph describes a Guide hit as having no content (%r). "
                "Since the 2026-09-24 index rebuild the bare query returns Guide sections "
                "with prose, so this tells the guide to discard correct results (#149)"
                % (m.group(0) if m else None))

    def test_it_does_not_call_its_results_evidence_of_a_mis_query(self):
        for para in self.bare:
            m = MIS_QUERY.search(para)
            self.assertIsNone(
                m,
                "the bare-query paragraph says seeing its results means the guide mis-queried "
                "(%r). Its Guide hits are on-topic and usable; only the unrelated Global* "
                "matches are dropped (#149)" % (m.group(0) if m else None))

    def test_it_states_a_property_rather_than_a_ranking(self):
        self.assertTrue(self.trap, "the bare-query trap paragraph is gone")
        for para in self.trap:
            m = RANK_CENSUS.search(para)
            self.assertIsNone(
                m,
                "the bare-query paragraph describes where results rank (%r). Ranks are what "
                "went stale on the 2026-09-24 rebuild; state the property (unrelated Global* "
                "matches are admitted) instead (#149)" % (m.group(0) if m else None))
            self.assertIn("category='globalization'", para,
                          "the paragraph must keep the filtered call as the route (INV-212)")

    def test_the_best_practices_paragraph_keeps_its_mis_query_sentence(self):
        self.assertTrue(self.best_practices, "the 'best practices' trap paragraph is gone")
        self.assertTrue(
            any(MIS_QUERY.search(b) for b in self.best_practices),
            "the 'best practices' trap still returns no globalization content, so its "
            "'evidence you mis-queried' sentence still holds and must stay (#149)")


class TheGalleryStepNamesTheRuleItIsAnInstanceOf(unittest.TestCase):
    """INV-212 was registered from this step and did not name it (scan-invisible)."""

    def test_pattern_gallery_retrieval_cites_inv212(self):
        step = text(REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
                    / "module-01-business-problem" / "phase1-discovery.md")
        self.assertIn(
            "INV-212", step,
            "the pattern-gallery retrieval step is INV-212's originating instance and must "
            "name it; conformance.py rules cannot see the gap because the section already "
            "cites INV-080",
        )


if __name__ == "__main__":
    unittest.main()
