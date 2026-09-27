"""Module 2 Step 5 must not say `search_docs` has no figure for the evaluation record limit.

Step 5's fallback branch fills `{record limit}` from `sdk_guide(topic='load',
record_count=<above the limit>)`, and names that tool rather than "a Senzing MCP tool". Until
#150 it justified the choice with an absence claim: "`search_docs` does **not** answer this —
asked for the evaluation license's record limit it returns EULA and pricing prose with no
figure (re-checked 2026-08-13)". Its `MCP-NEGATIVE` marker said the query "returns no figure",
and the `VERIFIED_QUERIES` entry in `test_prescribed_search_queries.py` said it "gives no
figure".

On server 1.37.13 (docs index 2026-09-24 18:45 UTC) that stopped being true. The top-ranked
hits for the query are still the EULA's grant-of-license sections, which state no figure, but
the result set now carries an FAQ, "What is the 500 record limit and how do I work around
SENZ9000", that states it outright. The route still works; the plugin was telling the guide
something untrue about the server, and a guard certified it.

What lasts is the RANKING property, not an absence: `sdk_guide` states the figure in a fixed
field (`compatibility_notes`), while `search_docs` ranks EULA prose above the FAQ that has it.
The rationale the issue first proposed, that the SDK route reports the ACTIVE license, is false
too (`sdk_guide` reports the documented default; the active license is measured in Step 5a with
`SzProduct.getLicense()`), so it is kept out as well.

This file fails if any of the stale wording comes back: in Step 5's prose, in the marker, or in
the allowlist entry. It also holds the prose free of a figure and of a dated re-check (INV-080).

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import ast
import importlib.util
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "plugins" / "senzing-bootcamp" / "skills" / "module-02-sdk-setup" / "SKILL.md"
ALLOWLIST = REPO / "tests" / "test_prescribed_search_queries.py"
REPORTS = REPO / ".claude" / "skills" / "dry-run" / "coverage_reports.py"

QUERY = "evaluation license record limit how many records without a license"
#: Built, not written, so this file never carries a bare marker token of its own.
TOKEN = "MCP-NEGATIVE" + ":"
#: Step 5's fallback instruction: from the fill rule to the assumption text it fills.
BLOCK_START = "Fill `{record limit}` below from the MCP server"
BLOCK_END = "\"I couldn't read your license from the SDK just now"

#: A set-level absence: the tool does not answer, or the response has no figure at all.
SET_ABSENCE = re.compile(
    r"(?i)does\s+(?:\*\*)?not(?:\*\*)?\s+(?:answer|give|return|state)"
    r"|\b(?:cannot|can't|doesn't|never)\s+(?:answer|give|return|state)"
    r"|\b(?:returns?|gives?)\b[^.]*\bno\s+figure"
    r"|\bwith\s+no\s+figure"
)
#: What makes a "no figure" statement a ranking claim rather than an absence claim.
RANKED = re.compile(r"(?i)\btop-ranked\b|\blower-ranked\b")
MINIMUM_STAMP = (1, 37, 13)


def load_reports():
    spec = importlib.util.spec_from_file_location("coverage_reports", REPORTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def step5_block():
    text = SKILL.read_text(encoding="utf-8")
    start = text.find(BLOCK_START)
    end = text.find(BLOCK_END, start)
    if start < 0 or end < 0:
        raise AssertionError("Step 5's {record limit} fill instruction was not found in %s"
                             % SKILL.relative_to(REPO))
    return text[start:end]


def prose(block):
    """Comment-stripped, fence-stripped, whitespace-collapsed visible prose."""
    block = re.sub(r"<!--.*?-->", " ", block, flags=re.S)
    block = re.sub(r"```.*?```", " ", block, flags=re.S)
    return " ".join(block.split())


def sentences_naming_search_docs(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if "search_docs" in s]


def verified_queries():
    """The allowlist dict, read with `ast` so the other test module is never executed here."""
    tree = ast.parse(ALLOWLIST.read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "VERIFIED_QUERIES"
                        for t in node.targets)):
            return ast.literal_eval(node.value)
    raise AssertionError("VERIFIED_QUERIES not found in %s" % ALLOWLIST.name)


class StepFiveProseMakesNoAbsenceClaim(unittest.TestCase):
    """The visible prose gives the fixed-field-versus-ranked-result reason, and no absence."""

    def setUp(self):
        self.prose = prose(step5_block())
        self.search_docs = sentences_naming_search_docs(self.prose)

    def test_the_prose_still_explains_why_sdk_guide_is_named(self):
        self.assertTrue(self.search_docs,
                        "Step 5 no longer says why it names sdk_guide over search_docs; the "
                        "guards below would pass vacuously")
        self.assertIn("compatibility_notes", self.prose,
                      "the reason sdk_guide is named is that it states the figure in a fixed "
                      "field, compatibility_notes (#150)")
        self.assertRegex(" ".join(self.search_docs), RANKED,
                         "the search_docs half of the reason is a ranking property: its "
                         "top-ranked hits carry no figure, a lower-ranked FAQ does (#150)")

    def test_it_does_not_say_search_docs_has_no_figure(self):
        for sentence in self.search_docs:
            m = SET_ABSENCE.search(sentence)
            self.assertIsNone(
                m,
                "Step 5 says search_docs does not answer, or returns no figure, for the "
                "evaluation record limit (%r). Since the 2026-09-24 index rebuild the result "
                "set carries an FAQ stating the figure; only its ranking is the problem (#150)"
                % (m.group(0) if m else None))

    def test_any_no_figure_statement_is_scoped_to_the_ranking(self):
        for sentence in self.search_docs:
            if re.search(r"(?i)\bno\s+figure\b", sentence):
                self.assertRegex(
                    sentence, RANKED,
                    "a search_docs sentence says 'no figure' without scoping it to the "
                    "top-ranked hits, which reads as a claim about the whole result set: %r"
                    % sentence)

    def test_it_does_not_claim_sdk_guide_reports_the_active_license(self):
        self.assertNotRegex(
            self.prose, r"(?i)\bactive\s+licen[cs]e",
            "sdk_guide is static guidance and reports the documented DEFAULT limit; the active "
            "license is measured in Step 5a with SzProduct.getLicense(). The 'active license' "
            "rationale is false and must not be written (#150)")

    def test_the_prose_carries_no_figure_and_no_dated_recheck(self):
        visible = re.sub(r"INV-\d{3}", " ", self.prose)
        self.assertIsNone(re.search(r"\b\d{3,}\b", visible),
                          "Step 5's fallback prose states a number; the record limit must come "
                          "from the server, never from this file (INV-080)")
        self.assertIsNone(re.search(r"\b20\d\d-\d\d-\d\d\b", visible),
                          "Step 5's fallback prose carries a dated re-check; the dated evidence "
                          "belongs in the marker, which /dry-run re-asks (#150)")

    def test_the_fill_route_is_unchanged(self):
        block = step5_block()
        self.assertIn("sdk_guide(topic='load'", block)
        self.assertRegex(block, r"record_count=\d+")
        self.assertIn("Never substitute a hardcoded or remembered figure", self.prose)
        self.assertIn("INV-080", self.prose)


class TheMarkerIsRescopedNotDeleted(unittest.TestCase):
    """The marker keeps its routing conclusion and states only what the ranking supports."""

    def setUp(self):
        reports = load_reports()
        self.reports = reports
        lines = [line for line in step5_block().split("\n") if TOKEN in line and QUERY in line]
        self.assertEqual(1, len(lines),
                         "expected exactly one marker for the record-limit query in Step 5; "
                         "found %d. Rescope it, do not delete it (#150)" % len(lines))
        self.line = lines[0]
        self.match = reports.MCP_NEGATIVE.search(self.line)
        self.assertIsNotNone(self.match, "the record-limit marker no longer parses as a "
                                         "marker (claim — owner: … — server <v>, <date>)")

    def test_it_is_restamped(self):
        version = tuple(int(p) for p in self.match.group("version").split("."))
        self.assertGreaterEqual(version, MINIMUM_STAMP,
                                "the record-limit marker is stamped server %s, older than the "
                                "1.37.13 re-ask that rescoped it (#150)"
                                % self.match.group("version"))

    def test_its_claim_is_a_ranking_claim(self):
        claim = self.match.group("claim")
        self.assertRegex(claim, r"(?i)\btop-ranked\b")
        self.assertRegex(claim, r"(?i)\blower-ranked\b")
        self.assertNotRegex(claim, r"(?i)\breturns\s+no\s+figure\b",
                            "the marker again says the query returns no figure; the result set "
                            "carries a lower-ranked FAQ that states it (#150)")

    def test_it_stays_a_routing_negative_to_sdk_guide(self):
        owner = self.match.group("owner")
        self.assertIn("sdk_guide(topic='load', record_count=", owner)
        self.assertIn("(routing negative", owner)

    def test_it_is_not_census_shaped(self):
        row = ((), self.match.group("version"), self.match.group("date"),
               self.match.group("claim"), self.match.group("owner"), SKILL.name, 0)
        self.assertEqual([], self.reports.find_census_rationales([row]),
                         "the marker's claim or owner clause pins a result count or a universal "
                         "over the results, which the next index rebuild falsifies (#151)")
        self.assertEqual([], self.reports.find_enumeration_rationales([row]))


class TheAllowlistEntryIsRescoped(unittest.TestCase):
    """The query stays accountable in VERIFIED_QUERIES, recorded as it now behaves."""

    def setUp(self):
        self.entry = verified_queries().get(QUERY)

    def test_the_entry_is_kept(self):
        self.assertTrue(self.entry,
                        "the record-limit query was removed from VERIFIED_QUERIES; rescope it, "
                        "do not remove it (#150)")

    def test_it_does_not_say_the_query_gives_no_figure(self):
        self.assertNotRegex(
            self.entry or "", r"(?i)\b(?:gives|returns)\s+no\s+figure\b",
            "the VERIFIED_QUERIES entry says the query gives no figure; since the 2026-09-24 "
            "index rebuild its result set carries an FAQ that states it (#150)")

    def test_it_records_the_faq_that_carries_the_figure(self):
        self.assertRegex(self.entry or "", r"(?i)lower-ranked FAQ")


if __name__ == "__main__":
    unittest.main()
