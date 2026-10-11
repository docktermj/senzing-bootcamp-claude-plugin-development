"""Module 7 step 1 asks the Bootcamper's question before it shows anything derived.

Step 1 used to open with the guide's own list: requirements derived from
`docs/business_problem.md`, then *"Is there anything you'd like to adjust?"*. Both real
Bootcampers answered "No". A list shown first leaves only "approve it?" to ask, so the
requirements never carried what the Bootcamper wanted to know. The open question, *"What
questions do you need to answer with your data?"*, was asked only on the fallback path.

#478 reverses the order on both paths:

1. **Turn 1** asks only "👉 **What do you want to find out about your data?**" and waits.
2. **Turn 2** on the business-problem path (the confirming gate, `#requirements-gate`) lists the
   Bootcamper's questions, in their own words, beside the derived requirements; each derived one
   the answer did not cover is marked **(not asked for)**; the combined list holds at most 10,
   their questions first and never dropped; the turn ends on one confirming 👉.
3. Dropping the derived requirements, or answering "I don't know", never re-asks the open
   question.

The checks are pure functions over a step's text, so each one also runs on a mutated copy as its
negative control: a derivation moved back before the open question, a retired question restored,
a second 👉 added to the gate.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line in
this file by construction, and counting lines that *start* with `👉 **` is what keeps prose that
mentions the marker ("the same confirming 👉") from being counted as a question. Phrase checks
use `_wrapped_text.match_lines`, which matches across a wrap.

⛔ **What this cannot establish:** that a live guide asks in this order, quotes faithfully, or
marks what was not asked for. Those are properties of a conversation; `dry-run` phase 3 and
`auto-test`'s transcript linter observe them. This pins that the skill file STATES them.

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #478 (part of #465).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _wrapped_text

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE_7 = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
RECAP_EXAMPLE = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"

STEP_HEADING = "## 1. Define query requirements"
OPEN_QUESTION = "👉 **What do you want to find out about your data?**"
CONFIRMING_QUESTION = (
    "👉 **Shall I build queries for this list, or would you like to drop or change any of it?**")
RETIRED_QUESTIONS = ("Is there anything you'd like to adjust?",
                     "What questions do you need to answer with your data?")

GATE_ANCHOR = '<a id="requirements-gate"></a>'
FALLBACK_HEADING = "### After the answer, fallback path"
DONT_KNOW_HEADING = '### When the answer is "I don\'t know" (or similar)'

#: Text that only appears once something derived is being shown or derived.
DERIVED_MARKERS = ("Derive between", "(not asked for)", "From your success criterion",
                   "Here is what your business problem suggests")


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` with ``pattern`` given as a string."""
    return _wrapped_text.match_lines(text, re.compile(pattern))


def section(text, start, end_markers):
    """Text from ``start`` up to the first of ``end_markers`` after it ('' when absent)."""
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i:]
    cut = [rest.find(m, len(start)) for m in end_markers]
    cut = [c for c in cut if c > 0]
    return rest[:min(cut)] if cut else rest


def step_1(text):
    return section(text, STEP_HEADING, ("\n## ",))


def questions(text):
    """The 👉 question lines, in order (see the module docstring for why lines)."""
    return [line.strip() for line in text.splitlines() if line.strip().startswith("👉 **")]


def order_problems(step):
    """The open question must be step 1's first 👉 and precede every derived marker."""
    problems = []
    qs = questions(step)
    if not qs or qs[0] != OPEN_QUESTION:
        problems.append("step 1's first 👉 is %r, not the open question" % (qs[:1] or None))
    at = step.find(OPEN_QUESTION)
    for marker in DERIVED_MARKERS:
        pos = step.find(marker)
        if pos < 0:
            problems.append("%r is missing from step 1" % marker)
        elif at < 0 or pos < at:
            problems.append("%r appears before the open question" % marker)
    if step.count(OPEN_QUESTION) != 1:
        problems.append("the open question appears %d times; it is asked once"
                        % step.count(OPEN_QUESTION))
    for retired in RETIRED_QUESTIONS:
        if retired in step:
            problems.append("the retired question %r is still in step 1" % retired)
    return problems


def gate_problems(step):
    """The confirming gate: both lists, the marking, the cap, and exactly one 👉."""
    gate = section(step, GATE_ANCHOR, (FALLBACK_HEADING,))
    if not gate:
        return ["the confirming gate (%s) is missing" % GATE_ANCHOR]
    problems = []
    if questions(gate) != [CONFIRMING_QUESTION]:
        problems.append("the gate's 👉 questions are %r, not the one confirming question"
                        % questions(gate))
    required = {
        "their questions are listed": r"\*\*Your questions\.\*\*",
        "their own words are quoted": r"quoting their own words",
        "each derived requirement cites its source": r"From your success criterion about \[X\]",
        "uncovered derived requirements are marked": r"marked \*\*\(not asked for\)\*\*",
        "a fully covered answer marks nothing": r"covers every derived requirement, this part "
                                                r"is empty and nothing is marked",
        "the combined list is capped at 10": r"At most 10 requirements in the combined list",
        "their questions are never dropped": r"never dropped to make room",
        "derived ones fill only while under 10": r"only while the list holds fewer than 10",
        "dropping the derived ones keeps theirs": r"Drops the derived requirements:\*\* proceed "
                                                  r"with their questions only",
        "the drop never re-asks": r"Do not ask the open question again",
        "the confirmed list keeps their words": r"keeps their own words",
    }
    for what, pattern in required.items():
        if not match_lines(gate, pattern):
            problems.append("the gate does not state that %s" % what)
    return problems


def turn_problems(step):
    """INV-251: each yielding turn in step 1 ends on exactly one 👉."""
    problems = []
    turn_1 = section(step, "### Turn 1", (GATE_ANCHOR,))
    if questions(turn_1) != [OPEN_QUESTION]:
        problems.append("turn 1 holds %r, not only the open question" % questions(turn_1))
    fallback = section(step, FALLBACK_HEADING, (DONT_KNOW_HEADING,))
    if not fallback:
        problems.append("the fallback path's after-the-answer section is missing")
    elif questions(fallback):
        problems.append("the fallback path asks %r after the answer" % questions(fallback))
    dont_know = section(step, DONT_KNOW_HEADING, ("Common queries",))
    if not dont_know:
        problems.append("the \"I don't know\" section is missing")
    else:
        if not match_lines(dont_know, r"^Do not ask the open question again\."):
            problems.append("the \"I don't know\" section does not forbid re-asking")
        if not match_lines(dont_know, r"every item marked \*\*\(not asked for\)\*\*, and end on "
                                      r"the same confirming 👉"):
            problems.append("an \"I don't know\" on the business-problem path does not show the "
                            "derived list, all marked, under the confirming 👉")
        if len(questions(dont_know)) != 1 or OPEN_QUESTION in questions(dont_know):
            problems.append("the fallback \"I don't know\" turn holds %r, not one options 👉"
                            % questions(dont_know))
    return problems


class Base(unittest.TestCase):
    def setUp(self):
        self.text = MODULE_7.read_text(encoding="utf-8")
        self.step = step_1(self.text)


class TheInputsAreReal(Base):
    """INV-265: every check below reads these; a silent miss would pass vacuously."""

    def test_step_1_was_located(self):
        self.assertTrue(self.step.strip(), "Module 7 step 1 not found under %r" % STEP_HEADING)
        self.assertGreater(len(questions(self.step)), 1, "step 1 holds too few 👉 lines to check")


class TheOpenQuestionComesFirst(Base):
    def test_it_is_the_first_question_and_precedes_everything_derived(self):
        self.assertEqual(order_problems(self.step), [])

    def test_the_inv_275_derivation_rule_still_holds(self):
        for pattern in (r"Derive from the REFINED prose, not from the",
                        r"Raise the discrepancy here rather than deriving a requirement"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(self.step, pattern), pattern)

    def test_a_discrepancy_is_raised_without_a_second_question(self):
        self.assertTrue(match_lines(self.step, r"never as a second 👉 \(INV-251\)"))

    def test_negative_control_derivation_before_the_question(self):
        derive = section(self.step, "Derive between", ("\n\n",))
        moved = self.step.replace(derive, "", 1).replace(
            "### Turn 1", derive + "\n\n### Turn 1", 1)
        self.assertTrue(any("before the open question" in p for p in order_problems(moved)))

    def test_negative_control_the_old_question_restored(self):
        old = self.step.replace(CONFIRMING_QUESTION,
                                "👉 **Is there anything you'd like to adjust?**", 1)
        self.assertTrue(any("retired" in p for p in order_problems(old)))
        old_first = self.step.replace(
            OPEN_QUESTION, "👉 **What questions do you need to answer with your data?**", 1)
        self.assertTrue(order_problems(old_first))


class TheConfirmingGate(Base):
    def test_it_states_every_rule(self):
        self.assertEqual(gate_problems(self.step), [])

    def test_negative_control_a_second_question(self):
        doubled = self.step.replace(CONFIRMING_QUESTION,
                                    "👉 **Anything to add?**\n\n" + CONFIRMING_QUESTION, 1)
        self.assertTrue(gate_problems(doubled))

    def test_negative_control_their_questions_dropped_for_room(self):
        dropped = self.step.replace("never\ndropped to make room", "dropped as needed", 1)
        dropped = dropped.replace("never dropped to make room", "dropped as needed", 1)
        self.assertTrue(any("never dropped" in p for p in gate_problems(dropped)))


class EveryTurnEndsOnOneQuestion(Base):
    def test_each_turn(self):
        self.assertEqual(turn_problems(self.step), [])

    def test_negative_control_the_open_question_re_asked(self):
        re_asked = self.step.replace("Do not ask the open question again.",
                                     OPEN_QUESTION, 1)
        self.assertTrue(turn_problems(re_asked))


class TheRecapExampleShowsTheNewQuestion(unittest.TestCase):
    def test_new_question_in_and_old_one_out(self):
        text = RECAP_EXAMPLE.read_text(encoding="utf-8")
        self.assertIn("- **Q:** What do you want to find out about your data?", text)
        for retired in RETIRED_QUESTIONS:
            with self.subTest(retired=retired):
                self.assertNotIn(retired, text)


if __name__ == "__main__":
    unittest.main()
