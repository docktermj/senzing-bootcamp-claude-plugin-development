"""No shipped file claims `WHY_KEY_DETAILS` is populated by nothing.

Three files carried an observation-only note whose central claim was *"no flag is documented
as populating it"*, written against server 1.32.9 on 2026-08-17 and correct then. On server
**1.35.3, 2026-09-01** the requirement is documented:

    get_sdk_reference(topic='response_schemas', filter='why_entities')
        -> WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS
           requires_flags: ["SZ_INCLUDE_MATCH_KEY_DETAILS"]

    get_sdk_reference(topic='flags', filter='SZ_INCLUDE_MATCH_KEY_DETAILS')
        -> applies_to includes why_entities / why_records / why_record_in_entity, and the
           description documents the relations-flag dependency the plugin had recorded as an
           unexplained observation.

⚠️ The correction is narrower than "it is documented now", and the narrower version is the
useful one: the **flags** topic still attributes only `RELATED_ENTITIES[].MATCH_KEY_DETAILS`
to that flag, so a reader who checks only that topic still concludes the why-side field is
unattributed. Both topics have to be read. That is what these files must now say.

⛔ This guard asserts the retired claim is ABSENT and the citation is PRESENT. Asserting only
the first would pass on a file that deleted the note entirely, losing the operational
guidance that stops an empty section being rendered as a result.

⚠️ **The absence check reads whitespace-normalized text, not one line at a time** (#387). Run
line by line it missed the claim in Module 7 Step 3a for a month, because "no" ended one line
and "flag is *documented*" began the next. It now also matches bold (``**documented**``), and
still reports each offender as ``file:line``, mapped back from the normalized match.
``WRAPPED_RETIRED_SENTENCE`` is the wrapped Step 3a sentence #387 removed, kept as a permanent
negative control. Since #426 the matching is the shared ``match_lines(text, RETIRED)`` from
``tests/_wrapped_text.py``, which collapses whitespace within each Markdown block rather than
across the whole file; this file's own ``retired_claim_lines`` is gone.

Also enforces **INV-346** as its first consumer: the absence check reads wrapped prose through
``match_lines``, with a wrapped negative control. It does **not** establish that any other guard
does the same.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"

#: The retired claim, in every phrasing that shipped, plain, italic or bold. Matched by
#: ``match_lines`` against whitespace-collapsed Markdown blocks (``tests/_wrapped_text.py``), so
#: a single space stands for any run of whitespace, line breaks included.
RETIRED = re.compile(r"(?i)no flag is \*{0,2}documented\*{0,2}[^.]{0,30}populat")

#: The Step 3a sentence #387 removed, wrapped as it shipped
#: (`phase1-query-visualize.md:441-443` at `c762046`). "no" ends the second line and
#: "flag is *documented*" begins the third, which is what a line-at-a-time scan missed.
WRAPPED_RETIRED_SENTENCE = """⚠️ **Getting
`WHY_KEY_DETAILS` to appear may require `SZ_INCLUDE_MATCH_KEY_DETAILS` plus a relations flag**: no
flag is *documented* to populate it, yet it was absent without that flag on two SDK builds
(observation-only). If it is missing for the flags in force, say so explicitly and fall back to
"""


def shipped_markdown():
    return sorted(SKILLS.rglob("*.md"))


def files_mentioning_the_field():
    """Derived by scan (INV-246) — the note lived in three files and could spread."""
    return [p for p in shipped_markdown()
            if "WHY_KEY_DETAILS" in p.read_text(encoding="utf-8")]


class TheRetiredClaimIsGone(unittest.TestCase):
    def test_no_file_says_no_flag_documents_the_field(self):
        offenders = []
        for md in shipped_markdown():
            for lineno in match_lines(md.read_text(encoding="utf-8"), RETIRED):
                offenders.append("%s:%d" % (md.relative_to(REPO), lineno))
        self.assertEqual(
            [], offenders,
            "A shipped file still claims no flag is documented to populate WHY_KEY_DETAILS. "
            "response_schemas carries requires_flags: ['SZ_INCLUDE_MATCH_KEY_DETAILS'] on that "
            "path (server 1.35.3, 2026-09-01; still so on 1.37.19, 2026-10-02). "
            "Offenders: %s" % offenders,
        )

    def test_the_matcher_catches_the_wrapped_sentence_it_once_missed(self):
        """Negative control (#387): the line-wrapped Step 3a sentence is caught, at its line.

        The match starts at "no", which ends the fixture's second line.
        """
        self.assertEqual([2], match_lines(WRAPPED_RETIRED_SENTENCE, RETIRED))
        # The old line-at-a-time scan, kept here only to show the fixture is the hard case.
        self.assertFalse(any(RETIRED.search(line)
                             for line in WRAPPED_RETIRED_SENTENCE.split("\n")),
                         "the fixture no longer splits the phrase across lines, so it no "
                         "longer tests the wrapped case")

    def test_the_matcher_catches_every_emphasis_form(self):
        for word in ("documented", "*documented*", "**documented**"):
            with self.subTest(form=word):
                self.assertEqual(
                    [1], match_lines("No flag is %s as populating it." % word, RETIRED))

    def test_the_matcher_reports_the_line_of_each_match(self):
        text = "intro\nno flag is documented to\npopulate it.\n\nok\nno flag\nis **documented** to populate it."
        self.assertEqual([2, 6], match_lines(text, RETIRED))

    def test_the_matcher_passes_the_documented_requirement(self):
        """The corrected wording names the flag; it must not trip the retired-claim matcher."""
        self.assertEqual([], match_lines(
            "`WHY_KEY_DETAILS` needs `SZ_INCLUDE_MATCH_KEY_DETAILS`, and that flag needs a "
            "relations\nflag — the server documents both.", RETIRED))

    def test_the_scan_still_finds_the_files(self):
        """A scan matching nothing would make every assertion below vacuous."""
        self.assertGreaterEqual(
            len(files_mentioning_the_field()), 3,
            "Fewer than three files mention WHY_KEY_DETAILS. The note lived in three; if the "
            "count dropped, check whether guidance was deleted rather than corrected.",
        )


class EveryMentionCitesTheDocumentedRequirement(unittest.TestCase):
    def test_each_file_names_the_flag_that_populates_it(self):
        for md in files_mentioning_the_field():
            with self.subTest(file=md.relative_to(REPO)):
                self.assertIn(
                    "SZ_INCLUDE_MATCH_KEY_DETAILS", md.read_text(encoding="utf-8"),
                    "a file discussing WHY_KEY_DETAILS must name the flag the server "
                    "documents as populating it",
                )

    def test_each_file_names_the_route_that_documents_it(self):
        """⚠️ The route matters more than the flag: it is where the reader must look."""
        for md in files_mentioning_the_field():
            with self.subTest(file=md.relative_to(REPO)):
                self.assertRegex(
                    re.sub(r"\s+", " ", md.read_text(encoding="utf-8")),
                    r"requires_flags",
                    "each file must cite `requires_flags` from response_schemas — the "
                    "annotation that carries the requirement. Naming the flag without the "
                    "route leaves the next reader checking `flags`, which does not say it.",
                )

    def test_each_file_carries_a_current_server_version_and_date(self):
        for md in files_mentioning_the_field():
            with self.subTest(file=md.relative_to(REPO)):
                text = md.read_text(encoding="utf-8")
                self.assertRegex(
                    text, r"1\.35\.\d",
                    "the corrected claim must carry the server version it was verified "
                    "against (INV-080)")
                self.assertRegex(text, r"20\d\d-\d\d-\d\d")


class TheFlagsTopicCaveatSurvives(unittest.TestCase):
    """The half that makes the correction useful rather than merely true."""

    def test_the_files_warn_that_the_flags_topic_alone_does_not_say_it(self):
        for md in files_mentioning_the_field():
            with self.subTest(file=md.relative_to(REPO)):
                self.assertRegex(
                    re.sub(r"\s+", " ", md.read_text(encoding="utf-8")),
                    r"RELATED_ENTITIES\[\]\.MATCH_KEY_DETAILS",
                    "each file must say the flags topic attributes only the related-entity "
                    "path to this flag — otherwise a reader checks `flags`, finds the "
                    "why-side field unattributed, and re-derives the retired conclusion.",
                )


class TheOperationalGuidanceIsUntouched(unittest.TestCase):
    """⛔ Correcting the provenance must not delete the advice that prevents a blank section."""

    def test_the_empty_section_fallback_survives(self):
        phase2 = (SKILLS / "module-07-query-visualize-discover" /
                  "phase2-discover.md").read_text(encoding="utf-8")
        self.assertRegex(
            re.sub(r"\s+", " ", phase2), r"(?i)FEATURE_SCORES",
            "the fallback to FEATURE_SCORES when the breakdown is absent must survive — it "
            "is what stops an empty section rendering as though Senzing found nothing.",
        )

    def test_the_engine_side_observation_is_still_marked_observation_only(self):
        """INV-149: the paired-build observation is still an observation, not a doc fact.

        ⚠️ Anchored to the SDK-build claim, not to the file. Checked file-wide this passed
        with the marker deleted, because `visualization-api-reference.md` carries other
        observation-only notes elsewhere — a marker 2,000 characters from the claim it
        qualifies marks nothing.
        """
        ref = re.sub(r"\s+", " ", (SKILLS / "module-03b-truthset-visualization" /
                                   "visualization-api-reference.md").read_text(encoding="utf-8"))
        m = re.search(r"4\.3\.2", ref)
        self.assertIsNotNone(
            m, "the paired-build observation (4.3.4 / 4.3.2) must still be recorded — it is "
               "the evidence that the flag is load-bearing on a why call")
        window = ref[max(0, m.start() - 320): m.end() + 320]
        self.assertRegex(
            window, r"observation-only",
            "the 4.3.4/4.3.2 engine-side observation must stay marked observation-only AT "
            "THE CLAIM — what the server documents is the flag, not what two SDK builds "
            "returned (INV-149).",
        )


if __name__ == "__main__":
    unittest.main()
