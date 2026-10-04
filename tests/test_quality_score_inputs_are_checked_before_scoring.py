"""The two hand-authored inputs to the quality score are checked before it is reported.

Module 5 Phase 1's quality score has two inputs authored **per run** rather than derived.
Both produced wrong numbers that looked like findings about the data, and both were caught
only after the wrong number existed.

**1. Applicability.** Four fields on a 72,799-record source were marked as applying to both
record types while measuring 100% / 91.5% / 42.3% / 100% on ORGANIZATION and **0%** on
PERSON — that source's person records are officer and contact records attached to a company,
where a business address structurally cannot exist. The source scored **70.5%** and landed in
the remediation band; corrected it scores **85.7%** and passes. ⛔ **The wrong score would
have sent a Bootcamper to remediate a source with nothing wrong with it** — the INV-264 false
alarm — on the largest source in the project.

⚠️ **The existing rules were correct and were followed.** `phase1-quality-assessment.md`
already computes completeness per RECORD_TYPE (INV-174) and already warns that a low score
with high NAME/ADDRESS coverage is probably an applicability error. Both fired — *after* the
wrong number was computed. What was missing is a precondition on the input, which is why the
new rule is a stop-the-score check keyed on the applicability set rather than another
heuristic keyed on the output.

**2. The attribute catalog.** Built with a backticked-token regex, it found **21** attributes
instead of **110** and reported NAME_ORG, ADDR_LINE1 and PHONE_NUMBER as unrecognized.
Re-measured on the served document (server 1.33.0, 2026-08-28): 102 plain-text first-column
names, 21 backticked tokens anywhere, 110 in the union — the reported figures exactly.

⚠️ **The same names render the other way through `search_docs`**, whose excerpts show them
backticked. A parse tuned on an excerpt works there and under-collects by 81% against the
document Step 4 actually reads. That divergence is the trap, and naming it is the fix.

⚠️ What this does NOT establish: that a live run prints the breakdown or parses correctly.
Both are runtime behaviors no offline suite can assert (INV-108).

Source spec:
`specs/applicability-and-attribute-catalog-are-authored-by-hand-and-fail-silently.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins"
#: An attribute count pinned into shipped prose — the figure nobody re-measures.
#: A specification attribute COUNT pinned into shipped prose. Requires a counting word
#: adjacent to the number, in either order, so that a version string, a date fragment or a
#: line reference on a line that merely mentions attributes is not flagged.
#: ⚠️ Two earlier versions were wrong in opposite directions: the first required the number
#: to come first and missed "Do not pin an attribute count in this file. 110 is what the
#: document holds today" — a rule against pinning a count, stated with the count. The second
#: matched any of the three numbers on any line mentioning "attribute" and flagged an
#: unrelated MCP-NEGATIVE marker whose query text contains the word twice.
PINNED_COUNT = re.compile(
    r"\b(?:102|110|21)\b\s+(?:\w+\s+){0,3}?(?:specification\s+)?attributes?\b|"
    r"\battributes?\b\s+(?:\w+\s+){0,3}?(?:is|are|totals?|holds?)\s+\b(?:102|110|21)\b|"
    r"\battribute\s+count[^\n]{0,40}?\b(?:102|110|21)\b", re.I)


def flatten(text):
    return re.sub(r"\s+", " ", text).lower()


def pinned_counts(text):
    """1-based lines where a pinned attribute count starts, outside the measurement note.

    ⚠️ **Matched across line wraps (#424).** "110\nspecification attributes" was invisible
    to a line-at-a-time read; ``match_lines`` reads each Markdown block with whitespace
    collapsed. The exemption still reads the line the match starts on, as before, so a note
    whose wording wraps away from that line is flagged rather than exempted.
    """
    lines = text.split("\n")
    return [n for n in match_lines(text, PINNED_COUNT)
            if "measured on the served document" not in flatten(lines[n - 1])
            and "re-measure" not in flatten(lines[n - 1])]


def scoring_files():
    """Shipped files that compute the completeness/quality score — derived, not hardcoded."""
    return sorted(p for p in PLUGIN.rglob("*.md")
                  if "__pycache__" not in p.parts
                  and "completeness (0-100)" in p.read_text(encoding="utf-8"))


def catalog_files():
    """Shipped files that save the Entity Specification for a catalog build."""
    return sorted(p for p in PLUGIN.rglob("*.md")
                  if "__pycache__" not in p.parts
                  and "senzing_entity_specification.md" in p.read_text(encoding="utf-8"))


class ApplicabilityIsCheckedBeforeTheScore(unittest.TestCase):
    def test_the_scoring_site_is_found(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        self.assertTrue(scoring_files(), "no shipped file computes a completeness score")

    def test_a_both_types_field_requires_a_per_record_type_breakdown(self):
        for p in scoring_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("per-`record_type` presence breakdown", flat,
                              "the score can be reported without a per-RECORD_TYPE breakdown "
                              "of the fields marked as applying to both types — the input "
                              "that was wrong")
                self.assertRegex(
                    flat, r"100%/0% split as an applicability\s*error",
                    "the 100%/0% signature is not named as an applicability error, so the "
                    "breakdown is printed with no rule for reading it")

    def test_it_stops_the_score_rather_than_annotating_it(self):
        """⛔ A precondition, not a note beside the number."""
        for p in scoring_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("before reporting the score", flat,
                              "the check does not run before the score is reported")
                self.assertIn("stops the score", flat,
                              "the check does not stop the score, so a wrong applicability "
                              "set still produces a band and can still route remediation")

    def test_the_existing_heuristic_survives(self):
        """⛔ The post-hoc NAME/ADDRESS check caught this once — it is not replaced."""
        for p in scoring_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("probable applicability error, not a data problem", flat,
                              "the pre-existing low-score heuristic was removed; the new "
                              "precondition is additional to it, not a replacement")
                self.assertIn("sanity-check any 0% or 100% figure", flat,
                              "the uniformity sanity-check was removed — it is what caught "
                              "the catalog fault")


class TheCatalogParseRuleIsStated(unittest.TestCase):
    def test_the_catalog_site_is_found(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        self.assertTrue(catalog_files(), "no shipped file saves the Entity Specification")

    def test_the_plain_text_rendering_is_named(self):
        hits = [p for p in catalog_files()
                if "first column" in flatten(p.read_text(encoding="utf-8"))]
        self.assertTrue(
            hits,
            "no shipped file says the specification's attribute names are plain text in the "
            "first column, so a backtick-tuned parse under-collects with nothing to warn it")

    def test_the_contrasting_search_docs_rendering_is_named(self):
        """Without this an author tunes on the wrong sample and reproduces the defect."""
        hits = [p for p in catalog_files()
                if "first column" in flatten(p.read_text(encoding="utf-8"))]
        for p in hits:
            flat = flatten(p.read_text(encoding="utf-8"))
            i = flat.index("first column")
            window = flat[i:i + 1500]
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("search_docs", window,
                              "the note does not say search_docs renders the same names "
                              "backticked, which is the whole trap")

    def test_no_attribute_count_is_pinned_in_shipped_prose(self):
        """⛔ A figure in shipped prose is one nobody re-measures."""
        bad = []
        for p in catalog_files():
            text = p.read_text(encoding="utf-8")
            for n in pinned_counts(text):
                bad.append(f"{p.relative_to(REPO_ROOT)}:{n}  {text.split(chr(10))[n - 1].strip()[:90]}")
        self.assertEqual(
            [], bad,
            "a shipped file pins a specification attribute count outside the dated "
            "measurement note. Confirm the parse against the saved copy instead:\n  "
            + "\n  ".join(bad))

    def test_a_wrapped_count_is_caught_at_its_first_line(self):
        """Negative control (#424): "110" ends line 1 and "specification attributes" line 2."""
        wrapped = "Save the saved copy. The specification defines 110\nspecification attributes.\n"
        self.assertEqual([1], pinned_counts(wrapped))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(PINNED_COUNT.search(l) for l in wrapped.split("\n")))

    def test_the_dated_measurement_note_is_not_a_pin(self):
        """Must-not-flag (INV-282): the note that measured the count may state it."""
        self.assertEqual([], pinned_counts(
            "It held 110 specification attributes, measured on the served document.\n"))

    def test_the_scan_is_not_vacuous(self):
        for planted in ("the specification defines 110 attributes",
                        "Do not pin an attribute count in this file. 110 is what it holds",
                        "there are 21 attributes"):
            with self.subTest(planted=planted):
                self.assertTrue(PINNED_COUNT.search(planted),
                                "the count matcher no longer detects a pinned figure")
        for ok in ("enforce a 120-second timeout",
                   "search_docs(query='payload attribute versus registered feature attribute "
                   "record root extracted as feature precedence')",
                   "server 1.33.0, verified 2026-08-21"):
            with self.subTest(ok=ok):
                self.assertFalse(PINNED_COUNT.search(ok),
                                 "the count matcher flags text that pins no attribute count, "
                                 "which would push an editor into deleting correct prose")


if __name__ == "__main__":
    unittest.main()
