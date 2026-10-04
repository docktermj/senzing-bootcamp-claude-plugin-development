"""Module 5 describes three parts of the Entity Specification the way `search_docs` serves them.

#417 re-measured Module 5's prescribed `search_docs` routes on server 1.37.19, docs index
2026-10-02 18:46 UTC, and found three descriptions of the specification's structure that the
served sections contradict. #440 re-measured them on the same index and corrected each:

1. **Phase 1 Step 6** said the *Identifiers* section groups `NATIONAL_ID`, `PASSPORT`, `TAX_ID`,
   `LEI_NUMBER` and `TRUSTED_ID`. The specification files `TRUSTED_ID` under its own *Trusted ID*
   heading (*Trusted ID > Feature: TRUSTED_ID*), and *Identifiers* has members the list omitted
   (*Identifiers > Feature: ACCOUNT*). The step now names the members non-exhaustively ("such
   as") and says `TRUSTED_ID` has its own heading.
2. **Phase 2 step 11** said the specification "marks all three ❌". *Name > Feature: NAME* shows
   two ❌ examples (the split, and `NAME_ORG` with parsed person fields); the `NAME_FULL` mix is
   a Rules line only.
3. **Phase 2's numeric-value section** called the column holding `REL_ANCHOR_KEY`'s bare `1001`
   the "guidance column". In *Feature: REL_ANCHOR* it is the Example column.

Each retired description is a phrase in prose, so every check reads across line wraps with
`match_lines` from `tests/_wrapped_text.py` (INV-346), and each has a wrapped negative control
that a line-at-a-time read misses. The pre-#440 sentences, kept verbatim as fixtures, must fail.

⚠️ **This guards three sentences' wording, not the specification.** If a later measurement shows
the specification changed, re-measure and change the prose and this test together (INV-080).

Stdlib only (INV-108).

Source issue: #440.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_5 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
            / "module-05-data-quality-mapping")
PHASE_1 = MODULE_5 / "phase1-quality-assessment.md"
PHASE_2 = MODULE_5 / "phase2-data-mapping.md"

#: The *Identifiers* grouping sentence listing `TRUSTED_ID` among its members. The list ends at
#: the first `.`, `;` or `(`, so a separate clause that names `TRUSTED_ID` is not a member.
TRUSTED_ID_IN_IDENTIFIERS = re.compile(
    r"\*Identifiers\*\s+section\s+groups\b[^.;()]*?`TRUSTED_ID`")
#: "marks all three ❌": the NAME section has two ❌ examples.
MARKS_ALL_THREE = re.compile(r"(?i)\bmarks\s+all\s+three\b")
#: The `REL_ANCHOR_KEY` 1001 column called the "guidance column".
GUIDANCE_COLUMN_1001 = re.compile(
    r"(?i)`?REL_ANCHOR_KEY`?\s+guidance\s+column|guidance\s+column[^.]{0,40}\b1001\b")

RETIRED = (
    (PHASE_1, TRUSTED_ID_IN_IDENTIFIERS,
     "Phase 1 Step 6 lists TRUSTED_ID as a member of the Identifiers section; the specification "
     "files it under its own 'Trusted ID' heading (#440)"),
    (PHASE_2, MARKS_ALL_THREE,
     "Phase 2 says the specification 'marks all three' name rules with a ❌ example; "
     "'Name > Feature: NAME' shows two, and states the NAME_FULL mix as a Rules line (#440)"),
    (PHASE_2, GUIDANCE_COLUMN_1001,
     "Phase 2 calls the column holding REL_ANCHOR_KEY's bare 1001 the 'guidance column'; in "
     "'Feature: REL_ANCHOR' it is the Example column (#440)"),
)

#: What the corrected sites must say instead.
NON_EXHAUSTIVE = re.compile(
    r"\*Identifiers\*\s+section\s+groups\s+identifiers\s+such\s+as\b[^.;()]*?`LEI_NUMBER`")
OWN_HEADING = re.compile(r"`TRUSTED_ID`[^.()]*?\bits\s+own\s+\*Trusted\s+ID\*\s+heading")
TWO_EXAMPLES = re.compile(
    r"(?i)shows\s+❌\s+worked\s+examples\s+for\s+the\s+last\s+two\b[^.]*?\bsplit\b[^.]*?`NAME_ORG`")
NAME_FULL_RULES_ONLY = re.compile(r"`NAME_FULL`\s+mix\s+has\s+the\s+Rules\s+line\s+only")
EXAMPLE_COLUMN = re.compile(r"`REL_ANCHOR_KEY`\s+row\s+shows\s+a\s+bare\s+`1001`\s+in\s+the\s+"
                            r"Example\s+column")

REQUIRED = (
    (PHASE_1, NON_EXHAUSTIVE, "Phase 1 Step 6 no longer names Identifiers members as a "
                              "non-exhaustive 'such as' list"),
    (PHASE_1, OWN_HEADING, "Phase 1 Step 6 no longer says TRUSTED_ID has its own Trusted ID "
                           "heading"),
    (PHASE_2, TWO_EXAMPLES, "Phase 2 step 11 no longer says the ❌ examples cover the split and "
                            "NAME_ORG with parsed person fields"),
    (PHASE_2, NAME_FULL_RULES_ONLY, "Phase 2 step 11 no longer says the NAME_FULL mix is a Rules "
                                    "line only"),
    (PHASE_2, EXAMPLE_COLUMN, "Phase 2 no longer names the Example column as the one holding "
                              "the bare 1001"),
)

# The sentences as they were before #440 (on 0ee6e1e), verbatim, wraps included.
PRE_440_PHASE_1 = (
    "cross-source join prediction.** Completeness for a grouped family — the Entity "
    "Specification's\n"
    "*Identifiers* section groups `NATIONAL_ID`, `PASSPORT`, `TAX_ID`, `LEI_NUMBER` and "
    "`TRUSTED_ID`\n"
    "(verified via `search_docs(query='Identifiers NATIONAL_ID PASSPORT TAX_ID TRUSTED_ID feature "
    "group',\n"
    "category='data_mapping')`, server 1.32.9, 2026-08-17; query re-verified on 1.33.0, "
    "2026-08-23,\n")
PRE_440_PHASE_2_NAME = (
    "`NAME_FULL` with parsed name fields in one `NAME` object, do not mix `NAME_ORG` with parsed "
    "person\n"
    "fields, and do not split one name across two `NAME` objects — the specification marks all "
    "three ❌\n"
    "with worked examples. An organization name belongs in `NAME_ORG`, not `NAME_FULL`.\n")
PRE_440_PHASE_2_REL = (
    "   the relationship keys, the specification's JSON examples show string values (`\"ORG1001\"`,\n"
    "   `\"ACME-1001\"`) while its `REL_ANCHOR_KEY` guidance column shows a bare `1001`, so it "
    "does not\n"
    "   mandate a type (verified 2026-07-28). Neither emission is made correct or incorrect by "
    "what the\n")


def offenders(text, pattern):
    return match_lines(text, pattern)


class TheShippedSitesDescribeTheSpecificationAsServed(unittest.TestCase):
    def test_no_retired_description_is_back(self):
        for path, pattern, why in RETIRED:
            with self.subTest(file=path.name, pattern=pattern.pattern):
                found = offenders(path.read_text(encoding="utf-8"), pattern)
                self.assertEqual([], found, f"{path.name}:{found}: {why}")

    def test_each_corrected_description_is_present(self):
        for path, pattern, why in REQUIRED:
            with self.subTest(file=path.name, pattern=pattern.pattern):
                self.assertTrue(offenders(path.read_text(encoding="utf-8"), pattern),
                                f"{path.name}: {why} (#440)")


class ThePre440SentencesFail(unittest.TestCase):
    """Negative controls: each retired sentence, as it shipped, is reported at its first line."""

    def test_each_pre_440_sentence_is_reported(self):
        for fixture, pattern, line in (
                (PRE_440_PHASE_1, TRUSTED_ID_IN_IDENTIFIERS, 2),
                (PRE_440_PHASE_2_NAME, MARKS_ALL_THREE, 2),
                (PRE_440_PHASE_2_REL, GUIDANCE_COLUMN_1001, 2)):
            with self.subTest(pattern=pattern.pattern):
                self.assertEqual([line], offenders(fixture, pattern))

    def test_the_pre_440_sentences_lack_the_corrections(self):
        for fixture, pattern in ((PRE_440_PHASE_1, NON_EXHAUSTIVE),
                                 (PRE_440_PHASE_1, OWN_HEADING),
                                 (PRE_440_PHASE_2_NAME, TWO_EXAMPLES),
                                 (PRE_440_PHASE_2_NAME, NAME_FULL_RULES_ONLY),
                                 (PRE_440_PHASE_2_REL, EXAMPLE_COLUMN)):
            with self.subTest(pattern=pattern.pattern):
                self.assertEqual([], offenders(fixture, pattern))


class EachCheckReadsAcrossAWrap(unittest.TestCase):
    """Wrapped negative controls (INV-346): a line-at-a-time read misses each of these."""

    WRAPPED = (
        (TRUSTED_ID_IN_IDENTIFIERS,
         "the *Identifiers* section groups `PASSPORT`, `TAX_ID`\nand `TRUSTED_ID` together.\n"),
        (TRUSTED_ID_IN_IDENTIFIERS,
         "the *Identifiers*\nsection groups identifiers such as `PASSPORT` and `TRUSTED_ID`.\n"),
        (MARKS_ALL_THREE, "the specification marks all\nthree ❌ with worked examples.\n"),
        (GUIDANCE_COLUMN_1001, "while its `REL_ANCHOR_KEY`\nguidance column shows a bare value.\n"),
        (GUIDANCE_COLUMN_1001, "the guidance\ncolumn shows a bare `1001` here.\n"),
    )

    def test_each_wrapped_offender_is_reported_at_its_first_line(self):
        for pattern, wrapped in self.WRAPPED:
            with self.subTest(pattern=pattern.pattern, fixture=wrapped):
                self.assertEqual([1], offenders(wrapped, pattern))
                # The line-at-a-time read, kept only to show the fixture is the hard case.
                self.assertFalse(any(pattern.search(l) for l in wrapped.split("\n")))

    def test_each_wrapped_correction_is_found(self):
        for pattern, wrapped in (
                (NON_EXHAUSTIVE, "the *Identifiers* section groups identifiers such as\n"
                                 "`NATIONAL_ID`, `PASSPORT`, `TAX_ID` and\n`LEI_NUMBER`; more.\n"),
                (OWN_HEADING, "`TRUSTED_ID` is not one of them, and is filed under its own\n"
                              "*Trusted ID* heading.\n"),
                (EXAMPLE_COLUMN, "its `REL_ANCHOR_KEY` row shows a bare `1001` in the\n"
                                 "Example column.\n")):
            with self.subTest(pattern=pattern.pattern):
                self.assertEqual([1], offenders(wrapped, pattern))
                self.assertFalse(any(pattern.search(l) for l in wrapped.split("\n")))


class TheCorrectedProseIsNotFlagged(unittest.TestCase):
    """Must-not-flag fixtures (INV-282): prose near each retired phrase that is correct."""

    def test_a_separate_trusted_id_clause_is_not_a_member(self):
        for text in (
                "*Identifiers* section groups identifiers such as `NATIONAL_ID` and `LEI_NUMBER`;\n"
                "`TRUSTED_ID` is not one of them.\n",
                "*Identifiers* section groups `PASSPORT` and `TAX_ID` (the query names\n"
                "`TRUSTED_ID` too).\n"):
            with self.subTest(text=text):
                self.assertEqual([], offenders(text, TRUSTED_ID_IN_IDENTIFIERS))

    def test_the_example_column_and_other_guidance_are_not_flagged(self):
        for text in ("its `REL_ANCHOR_KEY` row shows a bare `1001` in the Example column.\n",
                     "the Guidance column says to use the current record's `RECORD_ID`.\n"):
            with self.subTest(text=text):
                self.assertEqual([], offenders(text, GUIDANCE_COLUMN_1001))

    def test_two_examples_is_not_flagged(self):
        self.assertEqual([], offenders("shows ❌ worked examples for the last two.\n",
                                       MARKS_ALL_THREE))


if __name__ == "__main__":
    unittest.main()
