"""The pattern gallery step carries a retrieval strategy, not just the name of a tool.

Module 1 Step 3 asks for four attributes (problem, goal, typical sources, business value) across
the ten recognized use-case categories, and names `search_docs` as the source. It used to say
nothing about HOW to query — and this corpus needs that said, because the category labels are not
the documentation's vocabulary. A guide runs the obvious query, reaches about four categories, and
must choose between filling the rest from training data (an INV-080 violation, laundered by the
attribution line the step already requires) and improvising a partial gallery. Neither is specified.

⚠️ **The spec behind this test was wrong on its first writing, and the correction is the point.**
It claimed the server covers only 4 of 10 categories. That was concluded from two broad queries --
the same ask-the-wrong-route error that produced INV-208 the same day (INV-194). Queried by SECTOR
vocabulary, `economic-cost-mismatched-identity-data.md` quantifies ten sectors, supplying the
business-value attribute for nearly every category. The gap was retrieval strategy, never coverage.
That history is why the step's rule once read "Query by SECTOR vocabulary". #397 replaced it with
the rule that ships now: query by the document's own title or heading (INV-212), because the
sector-worded query reached the cost document but not its table (#335, below).

Two category names are homonym traps that return confidently WRONG content rather than nothing,
which is the more dangerous shape because a plausible result does not invite a re-query:

* **Supply Chain** -- BM25 matches "chains" and the software sense (libpostal store-chains geodata,
  a `sz_spark` "CI / supply chain" heading). Measured at Step 14.
* **Data Migration** -- returns the V3->V4 SDK migration (`sz_dbupgrade`, `sz_configupgrade`). It is
  the one recognized category with no business-use-case material, so the wrong answer is the only
  answer a plain query gets.

#335 (server 1.37.16, docs index 2026-09-29 22:00 UTC, 2026-10-01) found two of the step's named
documents without a working route. The cost-table query reached the cost document but put its
*"Estimated Annual Cost of Mismatched Identity Records"* table at rank 3, behind the intro and the
*"Remaining Sectors"* section, while the step said it "returns" the table. The
non-person-entity-types FAQ had no query at all, and the obvious one landed on a different FAQ
about *matching* non-person entities, whose caution reads as a reason to drop the pattern. Each
route now names the document it returns and its rank. Like INV-291's query list, the guard pins
that measured result and never the query's wording.

#342 (same server and index, 2026-10-01) added the other four named sources: the use-cases page's
*"Customer 360°"* and *"Fraud Detection"* sections, the USCIS case-study page and the MDM
integration FAQ, each at rank 1. Under both use-cases routes, rank 2 is the same page's bare
`[Read More]` link stub, so the step quotes the stubs and calls them a miss.

Enforces **INV-212**.

Run:  python3 -m unittest discover -s tests
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_01 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-01-business-problem"
PHASE_1 = MODULE_01 / "phase1-discovery.md"
PHASE_2 = MODULE_01 / "phase2-document-confirm.md"

#: The recognized set, as the plugin spells it. Duplicated across two files today, so it can drift.
CATEGORIES = (
    "Customer 360", "Fraud Detection", "Data Migration", "Compliance", "Marketing",
    "Healthcare", "Supply Chain", "KYC", "Insurance", "Vendor MDM",
)


def step_3(text):
    """Step 3's body: from its heading to the next `## ` heading."""
    start = text.index("## 3. If they want patterns")
    end = text.index("\n## ", start)
    return text[start:end]


#: A ⛔ sentence in whitespace-collapsed text: from the marker to the first sentence end, where a
#: closing `**` may follow the full stop.
STOP_SENTENCE = re.compile(r"⛔.*?[.!?](?:\*\*)?(?=\s|$)")


def states_the_title_or_heading_rule(body):
    """True when a ⛔ sentence in ``body`` says to query by the "own title or heading" and cites
    INV-212.

    It pins the phrase and the citation, not the sentence, so polishing the wording still passes.
    It reads whitespace-collapsed text because the sentence wraps in `phase1-discovery.md`.
    """
    return any(
        re.search(r"(?i)own title or heading", sentence) and "INV-212" in sentence
        for sentence in STOP_SENTENCE.findall(flat(body))
    )


class Step3TellsTheGuideHowToQuery(unittest.TestCase):
    def setUp(self):
        self.body = step_3(PHASE_1.read_text(encoding="utf-8"))

    def test_its_stop_rule_says_to_query_by_the_documents_own_title_or_heading(self):
        self.assertTrue(
            states_the_title_or_heading_rule(self.body),
            "Step 3's ⛔ rule must tell the guide to query by the document's own title or heading, "
            "citing INV-212, rather than by the category label or a generic phrase. One generic "
            "query is what made the server's coverage look like four categories of ten.",
        )

    def test_it_names_the_document_carrying_business_value(self):
        self.assertIn(
            "economic-cost-mismatched-identity-data.md", self.body,
            "Step 3 must name the document whose sector cost table supplies the business-value "
            "attribute for nearly every category; without it the guide cannot reach that attribute "
            "by any obvious query.",
        )

    def test_it_names_sources_for_the_other_three_attributes(self):
        for cue in ("use-cases page", "MDM", "non-person-entity"):
            with self.subTest(cue=cue):
                self.assertIn(
                    cue, self.body,
                    f"Step 3 must name where problem/goal/sources come from; {cue!r} missing",
                )

    def test_it_points_at_the_requery_rule_rather_than_restating_it(self):
        self.assertIn(
            "concepts.md", self.body,
            "Step 3 must point at concepts.md's full statement of the re-query rule. A third copy "
            "of that reasoning is what drifts (Step 14 already restates it once).",
        )
        self.assertRegex(
            self.body, r"(?i)do not restate",
            "the pointer must say not to restate the reasoning, matching how Step 14 defers to it",
        )


class TheTitleOrHeadingCheckRejectsTheRetiredRule(unittest.TestCase):
    """Controls for `states_the_title_or_heading_rule`, fed synthetic Step 3 bodies (#423).

    The guard it replaced asked for "sector vocabulary" and stayed green after #397 retired that
    rule, because the measured negative query still contains "by sector". These bodies go through
    the same helper as the real text.
    """

    #: The measured negative query Step 3 still quotes, which kept the old guard green.
    NEGATIVE_QUERY = (
        "`'total economic cost mismatched identity data by sector'` returned the document's "
        "intro at\n  rank 1."
    )

    def test_the_retired_sector_vocabulary_rule_is_rejected(self):
        body = (
            "## 3. If they want patterns\n\n"
            "⛔ **Query by SECTOR vocabulary, not by the category label.** This is the step's "
            "real work, and one\ngeneric query is not it.\n\n"
            "  ⚠️ **A sector-worded query reaches the document but not the table.** "
            + self.NEGATIVE_QUERY + "\n"
        )
        self.assertFalse(
            states_the_title_or_heading_rule(body),
            "The check accepted the retired sector-vocabulary rule. It must not pass on the "
            "measured negative query alone.",
        )

    def test_the_phrase_without_the_citation_is_rejected(self):
        body = "⛔ **Query by the document's own title or\nheading, not by the category label.**"
        self.assertFalse(
            states_the_title_or_heading_rule(body),
            "The check must also require the INV-212 citation in the ⛔ sentence.",
        )

    def test_the_phrase_outside_a_stop_sentence_is_rejected(self):
        body = (
            "⛔ **(INV-212) Query by SECTOR vocabulary.** Some guides query by the document's own "
            "title or heading."
        )
        self.assertFalse(
            states_the_title_or_heading_rule(body),
            "The phrase must be in the ⛔ sentence itself, not in prose after it.",
        )

    def test_a_reworded_rule_keeping_the_phrase_and_citation_passes(self):
        body = (
            "⛔ **Search by each document's own title or heading, never by the bare category "
            "label\n(INV-212).** This is the step's real work."
        )
        self.assertTrue(
            states_the_title_or_heading_rule(body),
            "Rewording that keeps \"own title or heading\" and INV-212 must still pass.",
        )


#: The documents Step 3 names, each with the heading its measured route returns.
MEASURED_ROUTES = {
    "cost table": '*"Estimated Annual Cost of Mismatched Identity Records"* table',
    "non-person FAQ": '*"Adding Non-Person Entity Types to Senzing"*',
    "use-cases page, Customer 360": '*"Customer 360°"* section of *"Senzing Use Cases"*',
    "use-cases page, Fraud Detection": '*"Fraud Detection"* section of *"Senzing Use Cases"*',
    "USCIS case study": '*"USCIS Improves Fraud Analytics with Senzing Entity Resolution"*',
    "MDM integration FAQ":
        '*"How does Senzing integrate with MDM (Master Data Management) systems?"*',
}

#: The use-cases page's bare link stubs, which rank 2 under the two category routes (#342).
USE_CASE_STUBS = ("[Read More](/customer-360/)", "[Read More](/risk-fraud-detection)")

#: A measured route's stamp: rank, then server version, docs index date and measurement date.
ROUTE_STAMP = re.compile(
    r"\*\*rank ([1-3])\*\* \(MCP server 1\.\d+\.\d+, docs index 20\d\d-\d\d-\d\d"
    r"[^)]*, measured 20\d\d-\d\d-\d\d\)")


class Step3RecordsWhatEachNamedRouteReturns(unittest.TestCase):
    """#335, #342: a route names the document it returns and its rank, with a dated stamp."""

    def setUp(self):
        self.flat = flat(step_3(PHASE_1.read_text(encoding="utf-8")))

    def route(self, target):
        """The text from a `search_docs` call's "returns <target>" to the end of its stamp."""
        m = re.search(r"`search_docs\(query='[^']+'(?:, category='[^']+')?\)` returns "
                      r"(?:the )?" + re.escape(target), self.flat)
        self.assertIsNotNone(
            m, "Step 3 has no `search_docs(...)` call recorded as returning %s" % target)
        return self.flat[m.start():m.end() + 200]

    def test_each_named_document_has_a_route_with_rank_and_stamp(self):
        for label, target in MEASURED_ROUTES.items():
            with self.subTest(route=label):
                self.assertRegex(
                    self.route(target), ROUTE_STAMP,
                    "The %s route must record the rank it returned (1, or 3 or better) with the "
                    "server version, docs index date and measurement date. A route without them "
                    "cannot be re-checked when the index moves." % label,
                )

    def test_the_use_cases_routes_call_the_link_stub_a_miss(self):
        """#342: each category route's rank 2 is a bare link stub, which must not read as a hit."""
        for stub in USE_CASE_STUBS:
            with self.subTest(stub=stub):
                self.assertIn(
                    stub, self.flat,
                    "Step 3 must quote the use-cases page's link stub %s that ranks 2 under its "
                    "category route, so the guide recognizes it." % stub,
                )
        self.assertRegex(
            self.flat, r"(?i)bare link stub\*\* \(`\[Read More\].{0,200}is a miss",
            "Step 3 must say the stub under the use-cases routes is a miss, not a second source.",
        )

    def test_the_sector_query_is_not_said_to_return_the_table(self):
        """The defect #335 fixed: a query that reached the document was said to return its table."""
        self.assertNotRegex(
            self.flat,
            r"by sector[^`]*'\)` returns `economic-cost-mismatched-identity-data\.md`, whose",
            "Step 3 again says the sector-worded query returns the cost table. Measured, it put "
            "the table at rank 3, behind the document's intro and its Remaining Sectors section.",
        )

    def test_the_matching_faq_is_distinguished_from_the_linking_faq(self):
        self.assertIn(
            "product matching, vehicle matching, or other non-person entities", self.flat,
            "Step 3 must name the product/vehicle-matching FAQ, so the guide recognizes it when a "
            "query returns it instead of the non-person-entity-types FAQ.",
        )
        self.assertRegex(
            self.flat, r"(?i)different document",
            "Step 3 must say the matching FAQ is a different document.",
        )
        self.assertRegex(
            self.flat, r"\*\*matching\*\* non-person entities.{0,200}\*\*linking\*\* people",
            "Step 3 must say the matching FAQ's caution concerns MATCHING non-person entities, "
            "not LINKING people to them. Without it the caution reads as a reason to drop the "
            "pattern.",
        )


class Step3NamesTheHomonymTraps(unittest.TestCase):
    def setUp(self):
        self.body = step_3(PHASE_1.read_text(encoding="utf-8"))

    def test_supply_chain_trap_is_named_and_delegated_to_its_measured_example(self):
        self.assertRegex(self.body, r"(?i)supply chain")
        self.assertRegex(
            self.body, r"(?i)chains|Step 14",
            "the Supply Chain trap must be named, pointing at Step 14's measured example",
        )

    def test_data_migration_trap_names_what_it_wrongly_returns(self):
        self.assertRegex(
            self.body, r"V3.{0,4}V4",
            "Step 3 must say that 'Data Migration' returns the V3->V4 SDK migration. Naming the "
            "trap without naming the wrong content it yields leaves the guide unable to recognize "
            "it — and the wrong content is plausible and well-formed.",
        )
        self.assertRegex(
            self.body, r"(?i)sz_dbupgrade|sz_configupgrade|migration guides",
            "name at least one concrete artifact the wrong result contains, so it is recognizable",
        )


class Step3ForbidsInventedDetail(unittest.TestCase):
    def setUp(self):
        self.body = step_3(PHASE_1.read_text(encoding="utf-8"))

    def test_training_data_fill_is_forbidden_and_cites_the_invariant(self):
        self.assertRegex(
            self.body, r"(?i)never fill.{0,60}training data|training data \(INV-080\)",
            "Step 3 must forbid filling a category's detail from training data",
        )
        self.assertIn("INV-080", self.body, "and cite the invariant it would violate")

    def test_an_unreached_category_is_named_without_detail(self):
        self.assertRegex(
            self.body, r"(?i)name it as available",
            "an unreached category must be named as available, with an offer to look it up — the "
            "behavior the step previously left to improvisation",
        )

    def test_a_link_stub_is_declared_not_to_be_content(self):
        self.assertRegex(
            self.body, r"(?i)link stub is not content|bare link stub",
            "Step 3 must say a bare link stub is not substantive content — the shape most likely "
            "to be mistaken for coverage",
        )
        self.assertIn("Read More", self.body, "quote the stub shape so it is recognizable")

    def test_the_step_no_longer_promises_all_ten_categories(self):
        self.assertRegex(
            self.body, r"(?i)does not promise all ten|categories the searches actually reached",
            "Step 3 must state that the gallery presents what the searches reached, so a short "
            "sourced gallery reads as correct rather than as a failure",
        )


def flat(chunk):
    """Whitespace-normalized, so a line-wrapped category name still matches.

    Both lists wrap: phase1 breaks "Data\\n  Migration" mid-name. A naive substring check reports
    that as a missing category — a false positive on correct text, which is worse than no guard
    because it trains the reader to distrust the message. Caught on the guard's first run.
    """
    return re.sub(r"\s+", " ", chunk)


def recognized_regions():
    """(phase1_region, phase2_region) — the two hand-duplicated copies of the set.

    phase1's authoritative copy is in Step 4a's Business Case Offer; phase2's is the
    problem-statement template's Use Case Category field.
    """
    p1 = PHASE_1.read_text(encoding="utf-8")
    p2 = PHASE_2.read_text(encoding="utf-8")
    a = p1[p1.index("exactly one use-case category from the recognized set"):][:400]
    b = p2[p2.index("## Use Case Category"):][:300]
    return flat(a), flat(b)


class TheRecognizedCategoryListsAgree(unittest.TestCase):
    """The set is duplicated in two files, so it can drift silently."""

    def test_both_files_list_the_same_recognized_categories(self):
        p1_set, p2_set = recognized_regions()
        for cat in CATEGORIES:
            with self.subTest(category=cat):
                self.assertIn(cat, p1_set, f"{cat} missing from phase1-discovery's recognized set")
                self.assertIn(cat, p2_set, f"{cat} missing from phase2's Use Case Category field")

    def test_neither_file_has_gained_a_category_the_other_lacks(self):
        """Catch drift in the other direction: a category added to one list only."""
        p1_set, p2_set = recognized_regions()

        def names(chunk):
            return {m for m in re.findall(r"[A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*", chunk)
                    if m in CATEGORIES}

        self.assertEqual(
            names(p1_set), names(p2_set),
            "the two recognized-category lists have drifted apart; they are duplicated by hand, "
            "so a category added to one must be added to the other",
        )

    def test_the_agreement_check_is_not_vacuous(self):
        """Both regions must actually contain the set — an empty region would pass silently."""
        p1_set, p2_set = recognized_regions()
        for label, region in (("phase1", p1_set), ("phase2", p2_set)):
            with self.subTest(region=label):
                found = [c for c in CATEGORIES if c in region]
                self.assertEqual(
                    len(CATEGORIES), len(found),
                    f"{label}'s region should hold all {len(CATEGORIES)} categories; found "
                    f"{len(found)}. If the region moved, retarget it rather than letting the "
                    "comparison pass on two empty strings.",
                )


if __name__ == "__main__":
    unittest.main()
