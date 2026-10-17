"""Module 7 step 1's confirming gate shows the Bootcamper's Module 1 words beside each derived requirement.

The query requirements Module 7 step 1 derives are the guide's rendering of
`docs/business_problem.md`, and the confirming gate (`#requirements-gate`, as #478 left it) showed
only that rendering. On 2026-08-25 a *possible*-fraud routing rule was rendered as *confirmed*
fraud in Module 1, and requirement 7 came out as "Confirmed-fraud candidate list"; the Bootcamper
approved it, reviewing only the refined list. Module 1's own gate already shows both versions
(INV-275); this gate now does too, using the `> "…"` quotes the document already saves.

What is pinned, at the gate:

1. **The quote beside each derived requirement**, read from `docs/business_problem.md` (never the
   conversation), and labeled as the Bootcamper's Module 1 words.
2. **The mismatch statement**: the gate says which line is whose, and that a mismatch between a
   requirement and the quote beside it is what the confirming question asks about.
3. **No invented quote**: a source with no `> "…"` line (a Step 6d desired-output selection, the
   generated scenario) shows the requirement without one.
4. **No question added**: the both-versions material precedes the gate's single 👉 (INV-251), and
   the business-problem "I don't know" path, which ends on the same 👉, shows the quotes too.

The checks are pure functions over step 1's text, so each one also runs on a mutated copy as its
negative control.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line in this
file by construction; counting lines that *start* with `👉 **` keeps prose that mentions the marker
("the same confirming 👉") from counting as a question. Phrase checks use
`_wrapped_text.match_lines`, which matches across a wrap.

⛔ **What this cannot establish:** that a live guide copies the quote faithfully, puts it beside the
right requirement, or leaves one out where the file has none. Those are properties of a
conversation; only `dry-run` phase 3 observes them. This pins that the skill file STATES them, and
that the Module 1 template really carries the quote slots the gate reads.

Enforces **INV-275** at Module 7's gate (the both-versions rule, widened beyond
`docs/business_problem.md`'s own gate by the amendment #482 drafts; until it is applied, INV-275's
registered enforcer is `tests/test_business_problem_preserves_the_original_wording.py`).

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #482 (part of #465).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _wrapped_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_7 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
DOC_CONFIRM = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"

STEP_HEADING = "## 1. Define query requirements"
GATE_ANCHOR = '<a id="requirements-gate"></a>'
FALLBACK_HEADING = "### After the answer, fallback path"
DONT_KNOW_HEADING = '### When the answer is "I don\'t know" (or similar)'
CONFIRMING_QUESTION = (
    "👉 **Shall I build queries for this list, or would you like to drop or change any of it?**")

QUOTE_SLOT = '> "[Their own words, verbatim]"'
#: The Module 1 sections a Module 7 requirement is derived from.
SOURCE_SECTIONS = ("Success Criteria", "Desired Output")

#: What the gate must state, each as a wrap-aware pattern, grouped by the criterion it serves.
QUOTE_RULES = {
    "the rule cites INV-275 on its ⛔ line": r"⛔ \*\*\(INV-275\) Show both versions",
    "the quote goes beside each derived requirement": r"beside each derived requirement, the "
                                                      r"Bootcamper's own Module 1 words",
    "it is the `> \"…\"` line from docs/business_problem.md": r"show the `> \"…\"` line that "
                                                             r"`docs/business_problem.md` carries",
    "it names the source sections": r"\(Success Criteria or Desired Output\)",
    "it is labeled as theirs": r"labeled as theirs: \"Your words in Discover the Business "
                               r"Problem:\"",
    "it is copied exactly": r"exactly as the file has it",
    "it comes from the file, never the conversation": r"Take it from the file, never from memory "
                                                      r"of the conversation",
    "a shared source repeats beside each requirement": r"its quote goes beside each of them",
}
MISMATCH_RULES = {
    "it says which is which": r"Say which is which, before the question",
    "the quote is named as theirs": r"each \"Your words in Discover the Business Problem\" line "
                                    r"is what they said",
    "the requirement is named as the guide's": r"the requirement above it is your rendering of it",
    "a mismatch is what the question asks about": r"a mismatch between a requirement and the quote "
                                                  r"beside it is exactly what the confirming "
                                                  r"question is asking about",
    "it adds no question": r"it adds no 👉 \(INV-251\)",
}
NO_INVENTION_RULES = {
    "no quote in the file means none shown": r"No quote in the document, none shown",
    "the requirement is shown without one": r"show the requirement without one and never invent one",
    "a Step 6d selection carries none": r"a desired output picked from Step 6d's options",
    "the generated scenario carries none": r"the generated scenario, whose document carries no "
                                           r"quotes at all",
    "the reason is given": r"An invented \"verbatim\" line is worse than none",
    "their own questions need no second version": r"Their questions need no second version",
}


def match_lines(text, pattern):
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


def gate(step):
    return section(step, GATE_ANCHOR, (FALLBACK_HEADING,))


def questions(text):
    """The 👉 question lines, in order (see the module docstring for why lines)."""
    return [line.strip() for line in text.splitlines() if line.strip().startswith("👉 **")]


def missing(text, rules):
    return ["the gate does not state that %s" % what
            for what, pattern in rules.items() if not match_lines(text, pattern)]


def gate_problems(step):
    """Every both-versions clause is stated, before the gate's one confirming 👉."""
    g = gate(step)
    if not g:
        return ["the confirming gate (%s) is missing" % GATE_ANCHOR]
    problems = (missing(g, QUOTE_RULES) + missing(g, MISMATCH_RULES)
                + missing(g, NO_INVENTION_RULES))
    if questions(g) != [CONFIRMING_QUESTION]:
        problems.append("the gate's 👉 questions are %r, not the one confirming question"
                        % questions(g))
    at = g.find(CONFIRMING_QUESTION)
    for marker in ("⛔ **(INV-275) Show both versions", "**Say which is which, before the question.**"):
        pos = g.find(marker)
        if pos >= 0 and at >= 0 and pos > at:
            problems.append("%r comes after the confirming question" % marker)
    if not match_lines(g, r"marked \*\*\(not asked for\)\*\*, with its source's Module 1 quote "
                          r"beneath it"):
        problems.append("part 2 of the list does not carry its source's Module 1 quote")
    return problems


def dont_know_problems(step):
    """The business-problem "I don't know" turn ends on the same 👉, so it shows the quotes too."""
    dk = section(step, DONT_KNOW_HEADING, ("Common queries",))
    if not dk:
        return ["the \"I don't know\" section is missing"]
    problems = []
    if not match_lines(dk, r"Each item carries its Module 1 quote, or none, as Turn 2 shows it, "
                           r"and the turn says which is which before the 👉"):
        problems.append("the \"I don't know\" path shows the derived list without the quotes")
    return problems


class Base(unittest.TestCase):
    def setUp(self):
        self.step = step_1(MODULE_7.read_text(encoding="utf-8"))


class TheInputsAreReal(Base):
    """INV-265: every check below reads these; a silent miss would pass vacuously."""

    def test_the_gate_was_located(self):
        self.assertTrue(self.step.strip(), "Module 7 step 1 not found under %r" % STEP_HEADING)
        self.assertGreater(len(gate(self.step)), 1500, "the confirming gate did not parse")

    def test_module_1_saves_the_quotes_the_gate_reads(self):
        """The gate reads `> "…"` lines from the Success Criteria and Desired Output sections."""
        text = DOC_CONFIRM.read_text(encoding="utf-8")
        start = text.index("# Business Problem Statement")
        template = text[start:text.index("```", start)]
        for name in SOURCE_SECTIONS:
            with self.subTest(section=name):
                at = template.index("## %s" % name)
                nxt = template.find("\n## ", at + 1)
                self.assertIn(QUOTE_SLOT, template[at:nxt],
                              "the Module 1 template carries no quote slot under '%s', so the "
                              "gate has nothing to read for it" % name)

    def test_module_1_says_a_generated_scenario_carries_no_quote(self):
        """The no-invented-quote rule's generated-scenario case rests on Step 15b."""
        flat = " ".join(DOC_CONFIRM.read_text(encoding="utf-8").split())
        self.assertIn("a `docs/business_problem.md` carrying **zero** of them is the expected "
                      "result", flat)


class TheGateShowsBothVersions(Base):
    def test_it_states_every_clause(self):
        self.assertEqual(gate_problems(self.step), [])

    def test_the_dont_know_path_shows_them_too(self):
        self.assertEqual(dont_know_problems(self.step), [])

    def test_the_derivation_still_reads_the_refined_prose(self):
        """The quotes are shown, not derived from: the INV-275 derivation rule still holds."""
        for pattern in (r"Derive from the REFINED prose, not from the",
                        r"Raise the discrepancy here rather than deriving a requirement"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(self.step, pattern), pattern)


class TheChecksCatchARegression(Base):
    """Negative controls: each mutation must produce the specific problem it targets."""

    def assertCaught(self, mutated, fragment, check=gate_problems):
        self.assertNotEqual(mutated, self.step, "the mutation changed nothing")
        problems = check(mutated)
        self.assertTrue(any(fragment in p for p in problems),
                        "expected a problem containing %r, got %r" % (fragment, problems))

    def test_the_quote_taken_from_the_conversation(self):
        mutated = self.step.replace("Take it from the file, never from memory of the conversation",
                                    "Take it from the conversation", 1)
        self.assertCaught(mutated, "never the conversation")

    def test_the_label_dropped(self):
        mutated = self.step.replace('labeled as theirs: "Your words in Discover the Business '
                                    'Problem:" and then\nthe quote', "and then\nthe quote", 1)
        self.assertCaught(mutated, "labeled as theirs")

    def test_the_mismatch_statement_dropped(self):
        g = gate(self.step)
        para = section(g, "**Say which is which, before the question.**", ("\n\n",))
        self.assertCaught(self.step.replace(para, "", 1), "a mismatch is what the question asks")

    def test_the_no_invention_rule_dropped(self):
        g = gate(self.step)
        bullet = section(g, "- **No quote in the document, none shown.**", ("\n- ",))
        self.assertCaught(self.step.replace(bullet, "", 1), "shown without one")

    def test_a_question_added_for_the_quotes(self):
        mutated = self.step.replace(
            CONFIRMING_QUESTION, "👉 **Do these match what you said?**\n\n" + CONFIRMING_QUESTION, 1)
        self.assertCaught(mutated, "not the one confirming question")

    def test_the_rule_moved_after_the_question(self):
        g = gate(self.step)
        rule = section(g, "⛔ **(INV-275) Show both versions", ("Then end the turn on",))
        moved = self.step.replace(rule, "", 1).replace(
            "*(Internal: end the turn on this question and wait.)*\n\n- **Confirms",
            "*(Internal: end the turn on this question and wait.)*\n\n" + rule + "- **Confirms", 1)
        self.assertCaught(moved, "comes after the confirming question")

    def test_the_dont_know_quotes_dropped(self):
        mutated = self.step.replace(
            " Each item carries its Module 1 quote, or none, as\n  Turn 2 shows it, and the turn "
            "says which is which before the 👉.", "", 1)
        self.assertCaught(mutated, "without the quotes", check=dont_know_problems)


if __name__ == "__main__":
    unittest.main()
