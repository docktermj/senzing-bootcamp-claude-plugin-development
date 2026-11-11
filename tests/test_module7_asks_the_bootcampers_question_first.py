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

#888 amends INV-359 (its dated note of 2026-11-10, registered by the maintainer on 2026-11-10):
a bare question left a Bootcamper with nothing to start from, so Turn 1
now shows numbered examples **before** the unchanged open question (`turn_1_problems`):

- on the business-problem path 1 to 4 examples from the refined prose of
  `docs/business_problem.md`, never topped up with the common queries, each naming its source and
  carrying no Module 1 quote; on the fallback path all five common queries;
- one framing line, a statement, inviting picks by number plus their own words, naming no example
  as the one to pick, and pointing at `ground-rules.md` → "Directing steps" → "Numbered examples
  before the open 👉" (INV-354);
- the open question still Turn 1's only 👉, with no numbered list directly beneath it.

Turn 2 lists each picked example after their own questions ("You picked: '…'"), with its source and
Module 1 quote, never marked **(not asked for)**; picked examples fill the cap of 10 after their
questions and before the derived ones (`gate_problems`). The record saves a picked example with a
`"Picked example — …"` source, and an answer that only picks examples directs the step
(`picked_problems`).

The checks are pure functions over a step's text, so each one also runs on a mutated copy as its
negative control: a derivation moved back before the open question, a retired question restored,
a second 👉 added to the gate; and since #888 an example list directly beneath the open question,
a second 👉 in Turn 1, a picked example marked **(not asked for)**, a list padded with the common
queries, and a re-ask.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line in
this file by construction, and counting lines that *start* with `👉 **` is what keeps prose that
mentions the marker ("the same confirming 👉") from being counted as a question. Phrase checks
use `_wrapped_text.match_lines`, which matches across a wrap.

⛔ **What this cannot establish:** that a live guide asks in this order, quotes faithfully, or marks
what was not asked for. Those are properties of a conversation; only `dry-run` phase 3 observes
them. This pins that the skill file STATES them. INV-359 names this file as its enforcer; passing it
is no evidence that a live run obeys it.

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #478 (part of #465); the examples before the question, #888.

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
                                                  r"with their questions and picked examples only",
        # #888: a picked example is theirs, listed after their questions, with its quote.
        "a picked example is listed as picked": r"Then each picked\s+example, as Turn 1 worded it "
                                                r"\(\"You picked: '…'\"\)",
        "a picked example carries its quote": r"with that source's Module 1 quote beneath it",
        "a picked example is never marked": r"A picked example is theirs: it\s+is never marked "
                                            r"\*\*\(not asked for\)\*\*",
        "part 2 holds only what was neither picked nor covered":
            r"Each derived requirement their answer neither picked nor\s+covered",
        "picked examples fill after their questions": r"add picked examples next, then derived "
                                                      r"requirements, each only while the\s+list "
                                                      r"holds fewer than 10",
        "a picked example gets the INV-275 quote": r"Under each picked example in part 1 and each "
                                                   r"requirement in part 2",
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


#: The shared bullet Turn 1 points at for the examples (#888, INV-354).
EXAMPLES_POINTER = (r'`\.\./bootcamp-onboarding/ground-rules\.md` → "Directing steps" → "Numbered '
                    r'examples before the\s+open 👉" states \(INV-354\)')

#: What Turn 1 must state about the examples it shows before the open question (#888).
TURN_1_REQUIRED = {
    "the examples come first, numbered": r"\*\*Starting points first, numbered\.\*\* Before "
                                         r"the question, show a numbered list of example",
    "1 to 4 examples on the business-problem path": r"\*\*Business-problem path:\*\* 1 to 4 "
                                                    r"examples drawn from the refined prose",
    "never from the quotes (INV-275)": r"never from its `> \"…\"` quotes \(INV-275\)",
    "never padded with the common queries": r"never top the list up with the common queries",
    "one example when the document supports one": r"a\s+document that supports one example "
                                                  r"shows one",
    "each example names its source": r"Each example names the success criterion or\s+desired "
                                     r"output it comes from",
    "no Module 1 quote in Turn 1": r"carries no Module 1 quote",
    "a disagreeing quote waits for Turn 2": r"raised in Turn 2, beside the picked example, never "
                                            r"here",
    "all five common queries on the fallback path": r"\*\*Fallback path:\*\* all five common "
                                                    r"queries \(below\), numbered",
    "the framing line is a statement": r"one line, a statement and not a question",
    "they may pick any number and add their own": r"pick any number of them by number and to "
                                                  r"add\s+questions of their own, in their own "
                                                  r"words",
    "no example is recommended": r"Name no example as the one to pick",
    "the list never sits beneath the 👉": r"come before the 👉, never beneath it",
    "it points at the shared bullet": EXAMPLES_POINTER,
}


def numbered_after(text, question):
    """True when a numbered list sits directly beneath ``question`` (blank and internal lines
    skipped)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == question:
            for later in lines[i + 1:]:
                s = later.strip()
                if not s or s.startswith("*(Internal"):
                    continue
                return bool(re.match(r"\d+\. ", s))
    return False


def turn_1_problems(step):
    """#888: numbered examples before the unchanged open question, never beneath it."""
    turn_1 = section(step, "### Turn 1", ("**This is Module 7's directing step.**",))
    if not turn_1:
        return ["Turn 1 is missing"]
    problems = []
    for what, pattern in TURN_1_REQUIRED.items():
        if not match_lines(turn_1, pattern):
            problems.append("Turn 1 does not state that %s" % what)
    at = turn_1.find(OPEN_QUESTION)
    first = turn_1.find("**Starting points first, numbered.**")
    if at < 0 or first < 0 or first > at:
        problems.append("Turn 1's examples do not come before the open question")
    if numbered_after(turn_1, OPEN_QUESTION):
        problems.append("a numbered list sits directly beneath the open question")
    if questions(turn_1) != [OPEN_QUESTION]:
        problems.append("Turn 1 holds %r, not only the open question" % questions(turn_1))
    if "(not asked for)" in turn_1[:at if at >= 0 else len(turn_1)]:
        problems.append("Turn 1 marks something (not asked for) before the open question")
    return problems


def picked_problems(text):
    """#888: a picked example directs the step, and is saved with its own source."""
    step = step_1(text)
    problems = []
    for what, pattern in {
        "a picked example is kept with its source": r"Each example they pick by number is a\s+"
                                                    r"\*\*picked example\*\*",
        "only picking examples still directs": r"An answer that only\s+picks examples still "
                                               r"directs the step; it is not the handed-back case",
        "picking only examples is recorded as directed": r"An answer that only picks examples is "
                                                         r"directed,\s+not the guide choosing, and "
                                                         r"Turn 2's confirming gate is still asked "
                                                         r"once",
        "the fallback path builds one per picked query": r"one per common query they picked",
        "a picked success criterion's source": r"`\"Picked example — Success criterion: <…>\"`",
        "a picked desired output's source": r"`\"Picked example — Desired output: <…>\"`",
        "a picked common query's source": r"`\"Picked example — Common query: <…>\"`",
        "their own questions keep their source": r"`\"Bootcamper's answer\"`",
    }.items():
        if not match_lines(step, pattern):
            problems.append("step 1 does not state that %s" % what)
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


class TurnOneShowsExamplesBeforeTheQuestion(Base):
    """#888: starting points before the open question, which stays Turn 1's only 👉."""

    def test_it_states_every_rule(self):
        self.assertEqual(turn_1_problems(self.step), [])

    def test_a_picked_example_directs_and_is_recorded(self):
        self.assertEqual(picked_problems(self.text), [])

    def assertCaught(self, problems, needle):
        self.assertTrue(any(needle in p for p in problems),
                        "expected a problem containing %r, got %r" % (needle, problems))

    def mutated(self, old, new):
        step = self.step.replace(old, new, 1)
        self.assertNotEqual(step, self.step, "the mutation no longer applies: %r" % old)
        return step

    def test_negative_control_list_beneath_the_question(self):
        step = self.mutated(OPEN_QUESTION + "\n", OPEN_QUESTION + "\n\n1. Find duplicates within "
                            "a source\n2. Find cross-source matches\n")
        self.assertCaught(turn_1_problems(step), "directly beneath the open question")

    def test_negative_control_a_second_question_in_turn_1(self):
        step = self.mutated(OPEN_QUESTION, "👉 **Which of these examples do you want?**\n\n"
                            + OPEN_QUESTION)
        self.assertCaught(turn_1_problems(step), "not only the open question")

    def test_negative_control_examples_after_the_question(self):
        turn_1 = section(self.step, "**Starting points first, numbered.**", (OPEN_QUESTION,))
        step = self.mutated(turn_1, "").replace(
            "own words for each.", "own words for each.\n\n" + turn_1, 1)
        self.assertCaught(turn_1_problems(step), "do not come before the open question")

    def test_negative_control_padded_with_common_queries(self):
        step = self.mutated("never top the list up with the common queries",
                            "top the list up to 4 with the common queries")
        self.assertCaught(turn_1_problems(step), "never padded")

    def test_negative_control_a_quote_in_turn_1(self):
        step = self.mutated("and carries no Module 1 quote",
                            "with its Module 1 quote beneath it")
        self.assertCaught(turn_1_problems(step), "no Module 1 quote in Turn 1")

    def test_negative_control_an_example_recommended(self):
        step = self.mutated("Name no example as the one to pick",
                            "Recommend the example that fits best")
        self.assertCaught(turn_1_problems(step), "no example is recommended")

    def test_negative_control_a_picked_example_marked_not_asked_for(self):
        step = self.mutated("A picked example is theirs: it\n   is never marked",
                            "A picked example is the guide's: it\n   is marked")
        self.assertCaught(gate_problems(step), "a picked example is never marked")

    def test_negative_control_picked_examples_dropped_with_the_derived(self):
        step = self.mutated("proceed with their questions and picked examples only",
                            "proceed with their questions only")
        self.assertCaught(gate_problems(step), "dropping the derived ones keeps theirs")

    def test_negative_control_only_picking_hands_back(self):
        text = self.text.replace("An answer that only picks examples is directed,\nnot the guide "
                                 "choosing", "An answer that only picks examples is the guide\n"
                                 "choosing", 1)
        self.assertNotEqual(text, self.text)
        self.assertCaught(picked_problems(text), "picking only examples is recorded as directed")

    def test_negative_control_picked_source_dropped(self):
        text = self.text.replace('`"Picked example — Common query: <…>"`',
                                 '`"Bootcamper\'s answer"`', 1)
        self.assertNotEqual(text, self.text)
        self.assertCaught(picked_problems(text), "a picked common query's source")


class TheRecapExampleShowsTheNewQuestion(unittest.TestCase):
    def test_new_question_in_and_old_one_out(self):
        text = RECAP_EXAMPLE.read_text(encoding="utf-8")
        self.assertIn("- **Q:** What do you want to find out about your data?", text)
        for retired in RETIRED_QUESTIONS:
            with self.subTest(retired=retired):
                self.assertNotIn(retired, text)


if __name__ == "__main__":
    unittest.main()
