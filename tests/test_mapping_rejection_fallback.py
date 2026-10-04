"""Tests for handling a `mapping_workflow` step-3 rejection with no actionable reason.

The skill already degraded gracefully when a validation *script* is unavailable (HTTP
404). It had no handling for a validator that runs and rejects with an unusable reason —
the observed case being a truncated error string cut off before it named the offending
field. With no readable reason the documented path is unusable and the only remaining
options were to retry blindly or improvise, so a bootcamp hand-authored two of three
mappers: exactly what `mapping_workflow` exists to prevent.

These tests pin the recovery path: bounded retry, raw evidence captured for the upstream
fix, a pinned question rather than an improvised one, and a fallback that keeps every
gate the workflow would have run.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

from _wrapped_text import match_lines

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE5 = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills", "module-05-data-quality-mapping"
)
PHASE2 = os.path.join(MODULE5, "phase2-data-mapping.md")
SKILL = os.path.join(MODULE5, "SKILL.md")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


#: " or " inside a pinned question's bold run. Matched by ``match_lines`` across line wraps
#: (#424), so an "or" on the line a long question wraps onto is still read.
OR_IN_QUESTION = re.compile(r"👉\s*\*\*(?:(?!\*\*).)*? or ")


def or_in_question(text):
    """1-based lines of each 👉 question offering alternatives with "or".

    The first line opened by a 👉 is read whole, as before #424; ``match_lines`` adds a bold
    run that wraps, which that line alone cannot show.
    """
    lines = text.split("\n")
    first = next((n for n, line in enumerate(lines, 1) if line.strip().startswith("👉")), None)
    hits = set(match_lines(text, OR_IN_QUESTION))
    if first is not None and " or " in lines[first - 1]:
        hits.add(first)
    return sorted(hits)


def rejection_section():
    """The unactionable-rejection block, from its heading to the next ⛔ directive."""
    text = read(PHASE2)
    start = text.index("When `mapping_workflow`'s step-3 validation rejects the payload")
    end = text.index("These gates are structural, not semantic", start)
    return text[start:end]


class TestUnactionableRejectionIsHandled(unittest.TestCase):
    def test_the_failure_mode_is_defined_observably(self):
        section = rejection_section()
        self.assertRegex(
            section,
            r"(?s)names no field and carries no\s*\n?\s*line or pointer",
            "'unactionable' must be defined observably, not left to judgment",
        )

    def test_retry_is_bounded_at_two_attempts(self):
        self.assertRegex(rejection_section(), r"(?i)after two unactionable rejections")

    def test_fallback_is_not_offered_preemptively(self):
        self.assertRegex(
            read(PHASE2),
            r"(?s)Never offer this fallback\s*\n?\s*preemptively",
            "mapping_workflow must remain the default path",
        )


class TestRawRejectionIsCaptured(unittest.TestCase):
    """The truncated text was the only evidence, and it was not preserved."""

    def test_section_requires_capturing_the_raw_text(self):
        self.assertRegex(rejection_section(), r"(?s)raw rejection text \*\*verbatim\*\*")

    def test_checkpoint_schema_carries_the_rejections(self):
        text = read(PHASE2)
        self.assertIn("validation_rejections", text)
        self.assertIn("mapper_source", text)

    def test_text_must_not_be_truncated_or_summarized(self):
        self.assertRegex(
            read(PHASE2),
            r"(?s)truncating or summarizing it destroys",
            "the capture must forbid editing the evidence",
        )


class TestPinnedFallbackQuestion(unittest.TestCase):
    def setUp(self):
        self.section = rejection_section()

    def test_question_is_pinned_with_the_marker(self):
        self.assertIn(
            "👉 **The mapping validator rejected this source twice without saying why. "
            "How would you like to proceed? Reply with a number:**",
            self.section,
        )

    def test_question_offers_three_numbered_options(self):
        for option in (
            "Write the mapper against the Senzing Entity Specification",
            "Try the mapping workflow once more",
            "Skip this source",
        ):
            with self.subTest(option=option):
                self.assertIn(option, self.section)

    def test_question_avoids_the_word_or_between_alternatives(self):
        """INV-009 discourages 'or'; the options are a numbered list instead."""
        self.assertIn("👉", self.section)
        self.assertEqual([], or_in_question(self.section))

    def test_a_wrapped_or_in_the_question_is_caught(self):
        """Negative control (#424): the bold run wraps and "or" is on its second line."""
        wrapped = ("👉 **The validator rejected this source twice. Shall I write the mapper\n"
                   "by hand or skip the source?**\n")
        self.assertEqual([1], or_in_question(wrapped))
        # The old check read only the 👉 line, kept here to show the fixture is the hard case.
        self.assertNotIn(" or ", wrapped.split("\n")[0])

    def test_or_in_the_options_below_the_question_is_not_the_question(self):
        """Must-not-flag (INV-282): an option may say "or"; the rule is about the question."""
        self.assertEqual([], or_in_question(
            "👉 **How would you like to proceed? Reply with a number:**\n"
            "1. Retry once more, or\n2. Skip this source\n"))

    def test_turn_ends_on_the_question(self):
        """INV-007: the bootcamper answers; the plugin never assumes."""
        self.assertRegex(self.section, r"(?s)end the turn on this question and wait")


class TestFallbackKeepsEveryGate(unittest.TestCase):
    def setUp(self):
        self.section = rejection_section()

    def test_attribute_names_still_come_from_the_specification(self):
        self.assertRegex(
            self.section,
            r"(?s)Entity Specification in\s*\n?\s*`docs/reference/`",
        )
        self.assertRegex(
            self.section,
            r"(?s)\*\*never\*\* from training data",
            "INV-080 must be restated where the fallback is authorized",
        )

    def test_all_three_quality_gates_still_run(self):
        self.assertRegex(self.section, r"(?s)\*\*All three quality gates still run\*\*")

    def test_cross_source_collision_check_still_runs(self):
        self.assertRegex(self.section, r"(?s)shared-feature collision check still runs")

    def test_result_is_still_only_structurally_validated(self):
        self.assertRegex(self.section, r"(?s)structurally\*\* validated")
        self.assertIn("INV-117", self.section)

    def test_provenance_of_each_mapper_is_recorded(self):
        self.assertRegex(
            self.section,
            r"(?s)which sources went through `mapping_workflow` and which did not",
        )


class TestSkillCrossReference(unittest.TestCase):
    def test_error_handling_points_at_both_failure_modes(self):
        text = read(SKILL)
        self.assertIn("validation script is unavailable", text)
        self.assertIn("no actionable reason", text)
        self.assertRegex(
            text,
            r"(?s)do not improvise\s*\n?\s*either one",
            "the skill must route to the defined handling rather than improvisation",
        )


if __name__ == "__main__":
    unittest.main()
