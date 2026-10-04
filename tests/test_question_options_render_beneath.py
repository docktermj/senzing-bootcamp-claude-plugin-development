"""A 👉 question's answer options render beneath it, never on the question's own line.

``ground-rules.md``'s 👉 protocol states it as a ⛔ with an explicit "no exception":

    A 👉 question's answer options render DIRECTLY BENEATH it — pinned or generated at
    runtime, no exception. … A question that says "reply with a number" above a list the
    bootcamper has already scrolled past is asking them to answer upwards.

Three shipped questions rendered their options inline instead -- 3 of the 40 "Reply with a
number" gates. The consequence is the one the rule names: a guide meeting an inline example
has two defensible renderings, the shipped shape or the stated rule, and nothing decides
between them, so the same gate renders two ways depending on which file was weighted.
INV-224 is satisfied by both readings and does not break the tie.

⚠️ Nothing detected this, and the reason is structural: the RULE lives in ``ground-rules.md``
and the VIOLATIONS lived in two other files. A section-scoped conformance scan is satisfied by
any ``INV-NNN`` in the surrounding section, and both ends cite invariants independently, so
the pair was never compared -- the INV-212 shape. A cross-file guard is the only thing that
closes it.

Enforces **INV-286** — a question whose options are complements is asked as a multi-select,
and every option chosen is recorded in full wherever the answer is persisted or rendered.

⚠️ What this asserts is that the multi-select form and the record-in-full rule **ship**. That
a live walk actually records "1 and 3" in full is a claim about a turn, and needs a
``dry-run`` phase 3 pass down the Business Case Offer path.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"

#: A 👉 line that carries a numbered option on the SAME line. Anchored on the option marker
#: "(1)" rather than on any particular question wording, so a new gate with a new phrasing is
#: caught by the same pattern (INV-282: match the claim, not the phrasings already seen).
INLINE_OPTIONS = re.compile(r"👉.*?\(1\)\s*\S")
#: The same shape across a line wrap (#424). Markdown renders a wrapped paragraph as one, so
#: a "(1)" on the line the question wraps onto still renders on the question's line.
#: ``match_lines`` reads each block with whitespace collapsed; the match stops at another 👉.
INLINE_OPTIONS_WRAPPED = re.compile(r"👉(?:(?!👉).)*?\(1\)\s*\S")


def inline_option_lines(text):
    """1-based lines of each 👉 whose options render inline, on its line or wrapped."""
    hits = {n for n, line in enumerate(text.split("\n"), 1)
            if "👉" in line and INLINE_OPTIONS.search(line)}
    return sorted(hits | set(match_lines(text, INLINE_OPTIONS_WRAPPED)))


#: Both prompt idioms in the plugin: single-select and the comma-separated multi-select.
NUMBER_PROMPT = re.compile(r"(?i)reply with (?:a number|the numbers)")


def question_lines():
    """[(path, lineno, line)] for every 👉 line in shipped skills.

    Only the non-vacuity floor reads these lines now (#424): a floor fails closed, since a
    wrap can only lower the count it measures.
    """
    out = []
    for md in sorted(SKILLS.rglob("*.md")):
        for lineno, line in enumerate(md.read_text(encoding="utf-8").split("\n"), 1):
            if "👉" in line:
                out.append((md, lineno, line))
    return out


class OptionsNeverShareTheQuestionsLine(unittest.TestCase):
    def test_no_question_carries_its_options_inline(self):
        offenders = []
        for md in sorted(SKILLS.rglob("*.md")):
            text = md.read_text(encoding="utf-8")
            offenders += ["%s:%d  %s" % (md.relative_to(REPO), n, text.split("\n")[n - 1].strip()[:90])
                          for n in inline_option_lines(text)]
        self.assertEqual(
            [], offenders,
            "A 👉 question renders its options on its own line. `ground-rules.md` requires them "
            "DIRECTLY BENEATH, with no exception — and a placement rule that says 'no exception' "
            "while shipping exceptions teaches that ⛔ rules are approximate.\n  "
            + "\n  ".join(offenders),
        )

    def test_the_scan_actually_sees_the_questions(self):
        """A scan matching nothing would make the guard above vacuously green forever."""
        numbered = [l for _, _, l in question_lines() if NUMBER_PROMPT.search(l)]
        self.assertGreaterEqual(
            len(numbered), 20,
            "Fewer than 20 numbered-choice questions found across the shipped skills. The "
            "population this guards is around 40; if the scan stopped finding them, fix the "
            "scan rather than trusting an empty offender list.",
        )

    def test_the_pattern_catches_an_inline_question(self):
        """Positive control in-process: the matcher must fire on the historical shape."""
        historical = ("👉 **What priority would you give this? Reply with a number:** "
                      "(1) High, (2) Medium, (3) Low.")
        self.assertRegex(
            historical, INLINE_OPTIONS,
            "The matcher must catch the exact shape that shipped, or the guard proves nothing.",
        )

    def test_a_wrapped_question_with_inline_options_is_caught(self):
        """Negative control (#424): the question wraps and its "(1)" is on the second line."""
        wrapped = ("👉 **What priority would you give this? Reply with a number:**\n"
                   "(1) High, (2) Medium, (3) Low.\n")
        self.assertEqual([1], inline_option_lines(wrapped))
        # The old line-at-a-time check, kept only to show the fixture is the hard case.
        self.assertFalse(any("👉" in l and INLINE_OPTIONS.search(l) for l in wrapped.split("\n")))

    def test_options_in_a_list_beneath_are_not_inline(self):
        """Must-not-flag (INV-282): a blank line, then the numbered list."""
        self.assertEqual([], inline_option_lines(
            "👉 **What priority would you give this? Reply with a number:**\n\n"
            "1. High\n2. Medium\n3. Low\n"))

    def test_the_pattern_leaves_a_correct_question_alone(self):
        """⚠️ Negative control: a 👉 whose options are beneath it must NOT match."""
        for correct in (
            "👉 **What priority would you give this? Reply with a number:**",
            "👉 **Which optional modules would you like to include? Reply with the numbers "
            "from the list below, comma-separated — reply \"none\" for just the required "
            "modules:**",
            "👉 **How many distinct data sources will we work with?**",
        ):
            with self.subTest(question=correct[:44]):
                self.assertNotRegex(
                    correct, INLINE_OPTIONS,
                    "A correctly-rendered question must not be flagged. A guard that fires on "
                    "compliant prose gets switched off.",
                )


class TheDesiredOutcomeGateIsMultiSelect(unittest.TestCase):
    """Step 6d's options are complements, so a single-select loses a real answer."""

    def setUp(self):
        self.discovery = (SKILLS / "module-01-business-problem" /
                          "phase1-discovery.md").read_text(encoding="utf-8")
        self.document = (SKILLS / "module-01-business-problem" /
                         "phase2-document-confirm.md").read_text(encoding="utf-8")

    def test_step_6d_asks_for_multiple_numbers(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.discovery),
            r"What does the end result look like\? Reply with the numbers from the list below,"
            r" comma-separated",
            "Step 6d must be a multi-select. A clean master list, an API over it and reports "
            "off it are the three normal deliverables of one project; asked as single-select, "
            "a Bootcamper's '1 and 3' has nowhere to go.",
        )

    def test_it_reuses_the_existing_multi_select_idiom(self):
        """One multi-select shape in the plugin, not two."""
        prep = (SKILLS / "bootcamp-preparation" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Reply with the numbers from the list below, comma-separated", prep,
            "Step 6d was written to match Bootcamp preparation's multi-select wording. If that "
            "wording moved, the two have drifted and both should be re-read together.",
        )

    def test_step_6b_stays_single_select(self):
        """Its 'Both' option already covers the combinations; widening it is not this change."""
        self.assertRegex(
            re.sub(r"\s+", " ", self.discovery),
            r"Which records are you working with\? Reply with a number:",
            "Step 6b must remain single-select — record types are a closed three-way set with "
            "an explicit Both, not an open list.",
        )

    def test_the_document_records_every_chosen_option(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.document),
            r"(?i)Desired Output records EVERY option",
            "Step 11 must say Desired Output carries every chosen option. Without it the "
            "multi-select is asked and then narrowed one step later, which is the same lost "
            "answer by a different route.",
        )

    def test_the_downstream_consumer_is_named(self):
        """A narrowed requirement does not stop here; say where it goes."""
        self.assertRegex(
            re.sub(r"\s+", " ", self.document),
            r"(?i)Module 7 step 1 derives",
            "The rule must name Module 7 as the consumer. 'Record every option' reads as "
            "tidiness until the reader knows a dropped option becomes a query requirement "
            "the Bootcamper never asked for.",
        )


class NoQuestionWasPinnedByThisChange(unittest.TestCase):
    """⚠️ Both specs say so explicitly: the fix is placement, not wording."""

    def test_the_three_corrected_questions_are_not_pinned(self):
        for rel, needle in (
            ("module-01-business-problem/phase1-discovery.md",
             "Which records are you working with?"),
            ("module-01-business-problem/phase1-discovery.md",
             "What does the end result look like?"),
            ("bootcamp-onboarding/feedback.md",
             "What priority would you give this?"),
        ):
            with self.subTest(question=needle):
                text = (SKILLS / rel).read_text(encoding="utf-8")
                i = text.index(needle)
                window = text[max(0, i - 400): i + 400]
                self.assertNotIn(
                    "INV-056", window,
                    "These three questions are unpinned today, and re-rendering their options "
                    "must not pin them. An INV-056 pin freezes wording nobody reviewed for "
                    "pinning — a larger commitment than the fix.",
                )


if __name__ == "__main__":
    unittest.main()
