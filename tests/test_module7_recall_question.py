"""Module 7 step 3a asks one recall question instead of reminding the Bootcamper (#483).

Step 3a used to carry a "Matching-concepts reminder": *"briefly remind the bootcamper of the
matching concepts introduced earlier"*, a sentence or two each on features and match keys,
confidence scores and cross-source connections. Written as a reminder, it re-taught the concepts,
so the Bootcamper never retrieved one themselves.

#483 replaces it with one recall question:

1. **About their own result.** One entity in their current results and one of the three concepts
   it shows. The correct answer is read from that entity's response and checked against the MCP
   server, never taken from training data or the earlier sample data (INV-080).
2. **A numbered choice**, in the shape Module 0's knowledge check states (INV-051), cited there.
3. **It ends 3a's turn as the one 👉 (INV-251).** The ⛔ non-yielding pointer that said "Steps
   2–3a ask nothing" now says they ask nothing unless the recall question is due, and that 3b
   starts on the next turn.
4. **A wrong answer follows Module 0's wrong-answer rule, cited rather than restated (INV-300).**
5. **No question on the zero-or-very-few-matches branch.**
6. **The deeper-refresher offer is kept**, as a statement after the answer.

The checks are pure functions over the file's text, so each also runs on a mutated copy as its
negative control (`TheChecksCatchARegression`), and each mutation must make the check report the
problem it targets.

⚠️ **The 👉 count reads single lines on purpose (INV-346).** A 👉 question is its own line by
construction; counting lines that *start* with `👉 **` keeps prose that mentions the marker ("up
to its next 👉") from being counted. Phrase checks use `_wrapped_text.match_lines`, which matches
across a wrap.

⛔ **What this cannot establish:** that a live guide picks a fitting entity, reads the answer from
it, asks well-formed options, or re-teaches a wrong answer. Those are properties of a conversation;
only `dry-run` phase 3 observes them. This pins that the skill file STATES them. It enforces
INV-362's step 3a half (registered 2026-10-13).

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #483 (part of #465).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _wrapped_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M7_PHASE1 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
CONCEPTS = SKILLS / "module-00-entity-resolution-concepts" / "concepts.md"

RECALL_QUESTION = "👉 **What does that tell you about entity {ENTITY_ID}? Reply with a number:**"
RECALL_HEADING = "**One recall question, last, and it ends this turn.**"
ANSWER_HEADING = "**On the answer, the next turn.**"
ZERO_BRANCH = "**If entity resolution found zero or very few matches:**"
CITED_SECTION = "## Optional knowledge check"
WRONG_ANSWER_RULE = "When the answer is wrong, say so — and re-teach."
REFRESHER = ("If you'd like a deeper refresher on how Senzing matching works, features, scoring, "
             "or cross-source connections, just ask and I'll walk through it again.")

#: Text only the retired reminder carried.
RETIRED = ("Matching-concepts reminder", "briefly remind the bootcamper",
           "Adapt the reminders to the bootcamper's own data context")

#: Module 0's wrong-answer rule, in its own words. A copy of any of these in Module 7 is a
#: restatement of a rule the step claims is stated once (INV-300).
RULE_ONLY_PHRASES = ("Name it as incorrect", "Explain why the chosen option is wrong",
                     "do not re-ask the same one", "False praise")


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


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


def questions(text):
    """The 👉 question lines, in order (see the module docstring for why lines)."""
    return [line.strip() for line in text.splitlines() if line.strip().startswith("👉 **")]


def step3a_problems(phase1):
    problems = []
    step3a = section(phase1, "### 3a. Present query results", ("### 3b.",))
    if not step3a:
        return ["Module 7 has no step 3a"]
    flat = squash(step3a)

    for phrase in RETIRED:
        if phrase in flat:
            problems.append("step 3a still carries the reminder (%r)" % phrase)

    # The one 👉, last in the step's text, under the recall paragraph.
    if questions(step3a) != [RECALL_QUESTION]:
        problems.append("step 3a does not ask exactly the recall question (%r)"
                        % questions(step3a))
    recall = section(step3a, RECALL_HEADING, (ANSWER_HEADING,))
    if not recall:
        problems.append("step 3a has no recall-question paragraph")
    elif RECALL_QUESTION not in recall:
        problems.append("the recall question is not under its paragraph")
    zero = step3a.find(ZERO_BRANCH)
    if zero < 0 or not 0 <= zero < step3a.find(RECALL_HEADING):
        problems.append("the recall question does not follow the results it asks about")

    for what, pattern in {
        "it replaces the reminder": r"recall one matching\s+concept from their own results instead "
                                    r"of reminding them of it",
        "the three concepts": r"features and match\s+keys \(its match key\), confidence scores "
                              r"\(a feature score,.*cross-source connections",
        "one entity in their current results": r"Pick one entity in their current results and one "
                                               r"concept it shows",
        "the answer is read from the result, never training data":
            r"Read the correct answer from that entity's own response, never from training data "
            r"or the\s+earlier sample data",
        "the MCP check, with INV-080": r"check it against the MCP\s+server before asking\*\* "
                                       r"\(INV-080\)",
        "the MCP route that checks it": r"get_sdk_reference\(topic='response_schemas'",
        "the server version it was checked on": r"server \d+\.\d+\.\d+, \d{4}-\d{2}-\d{2}",
        "Module 0 skipped changes nothing": r"never about Module 0's content",
        "a numbered choice, per Module 0's knowledge check (INV-051)":
            r"Ask it as a numbered choice\*\*, the shape Module 0's knowledge check states\s+"
            r"\(`\.\./module-00-entity-resolution-concepts/concepts\.md` → \"Optional knowledge "
            r"check\", INV-051\)",
        "it is the turn's one 👉 (INV-251)": r"the\s+turn's one 👉 \(INV-251\)",
    }.items():
        if not match_lines(recall or step3a, pattern):
            problems.append("step 3a does not state %s" % what)

    # The no-match branch skips it, stated at both ends.
    zero_text = section(step3a, ZERO_BRANCH, ("\n\n",))
    if "asks no recall question" not in squash(zero_text):
        problems.append("the zero-or-very-few-matches branch does not skip the recall question")
    if not match_lines(recall, r"Skip it when the zero-or-very-few-matches\s+branch above ran"):
        problems.append("the recall paragraph does not skip the zero-or-very-few-matches branch")

    # The answer: Module 0's rule, cited and not restated; skip; the refresher; then 3b.
    answer = section(step3a, ANSWER_HEADING, ("**Checkpoint:**",))
    if not answer:
        problems.append("step 3a does not say what follows the answer")
    for what, pattern in {
        "the wrong-answer rule is cited with INV-300":
            r"A wrong answer follows Module 0's wrong-answer rule, stated once in\s+"
            r"`\.\./module-00-entity-resolution-concepts/concepts\.md` → \"Optional knowledge "
            r"check\" \(INV-300\);\s+follow it there rather than a copy here",
        "the re-teach is grounded in their result": r"Ground the re-teach in this entity's result",
        "the question is not re-asked": r"the question is not asked again",
        "skip moves on with no penalty": r"\"Skip\" or\s+an exit signal moves on with no penalty",
        "3b follows in the same turn": r"Continue into 3b in the\s+same turn",
    }.items():
        if not match_lines(answer, pattern):
            problems.append("step 3a does not state %s" % what)
    if REFRESHER not in squash(answer):
        problems.append("the deeper-refresher offer is not kept after the answer")
    elif "as a statement" not in squash(answer):
        problems.append("the deeper-refresher offer is not given as a statement")
    for phrase in RULE_ONLY_PHRASES:
        if phrase in flat:
            problems.append("step 3a restates Module 0's wrong-answer rule (%r)" % phrase)

    # The non-yielding pointer, rewritten (INV-225).
    if "Steps 2–3a ask nothing, so" in flat:
        problems.append("the pointer still says steps 2–3a ask nothing, unconditionally")
    after = squash(phase1[phase1.find("### 3a."):phase1.find("### 3b.")])
    for what, phrase in {
        "the pointer allows the recall question":
            "Steps 2–3a ask nothing unless step 3a's recall question is due",
        "the turn ends on it": "That turn ends on it; 3b starts on the next turn, after the "
                               "answer.",
    }.items():
        if phrase not in after:
            problems.append("step 3a's pointer does not state %s" % what)
    return problems


def cited_section_problems(concepts):
    """The section the step cites exists and holds the rules it defers to."""
    problems = []
    cited = section(concepts, CITED_SECTION, ("\n## ",))
    if not cited:
        return ["concepts.md has no %r section" % CITED_SECTION]
    flat = squash(cited)
    if WRONG_ANSWER_RULE not in flat:
        problems.append("the cited section has no wrong-answer rule")
    if "numbered multiple-choice question" not in flat:
        problems.append("the cited section has no numbered-choice rule")
    if "The bootcamper can exit at any time" not in flat:
        problems.append("the cited section has no exit rule")
    return problems


class StepThreeAAsksOneRecallQuestion(unittest.TestCase):
    def test_step_3a(self):
        self.assertEqual([], step3a_problems(read(M7_PHASE1)))

    def test_the_cited_section_holds_the_rules(self):
        self.assertEqual([], cited_section_problems(read(CONCEPTS)))

    def test_the_reminder_is_gone_from_module_7(self):
        text = squash(read(M7_PHASE1))
        for phrase in RETIRED:
            self.assertNotIn(phrase, text)


class TheChecksCatchARegression(unittest.TestCase):
    """Each mutation must make the check report the problem it targets."""

    def assertReports(self, problems, needle):
        self.assertTrue(any(needle in p for p in problems),
                        "expected a problem containing %r, got %r" % (needle, problems))

    def mutate(self, old, new):
        text = read(M7_PHASE1)
        self.assertIn(old, text, "the mutation's anchor is gone; update the test")
        return step3a_problems(text.replace(old, new, 1))

    def test_reminder_restored(self):
        self.assertReports(
            self.mutate(RECALL_HEADING, "**Matching-concepts reminder.** " + RECALL_HEADING),
            "still carries the reminder")

    def test_question_dropped(self):
        self.assertReports(self.mutate(RECALL_QUESTION + "\n", ""),
                           "does not ask exactly the recall question")

    def test_second_question(self):
        self.assertReports(
            self.mutate(ANSWER_HEADING, "👉 **Did that make sense?**\n\n" + ANSWER_HEADING),
            "does not ask exactly the recall question")

    def test_answer_from_training_data(self):
        self.assertReports(
            self.mutate("never from training data or the\n   earlier sample data",
                        "from what you know"),
            "the answer is read from the result, never training data")

    def test_open_ended(self):
        self.assertReports(self.mutate("**Ask it as a numbered choice**", "**Ask it openly**"),
                           "a numbered choice")

    def test_no_match_branch_asks(self):
        self.assertReports(self.mutate("On this branch step 3a asks no recall question",
                                       "On this branch step 3a asks the recall question"),
                           "does not skip the recall question")

    def test_wrong_answer_rule_restated(self):
        self.assertReports(
            self.mutate("Ground the re-teach", "Name it as incorrect. Ground the re-teach"),
            "restates Module 0's wrong-answer rule")

    def test_wrong_answer_cite_dropped(self):
        self.assertReports(self.mutate("(INV-300);\nfollow it there", ";\nfollow it there"),
                           "the wrong-answer rule is cited with INV-300")

    def test_refresher_dropped(self):
        self.assertReports(self.mutate("just ask and I'll walk through it again.", ""),
                           "deeper-refresher offer is not kept")

    def test_pointer_reverted(self):
        self.assertReports(
            self.mutate("Steps 2–3a ask nothing unless step 3a's recall question is due; when it "
                        "is not,\nthis turn does not end here",
                        "Steps 2–3a ask nothing, so this turn does not end here"),
            "unconditionally")

    def test_cited_section_lost_its_rule(self):
        text = read(CONCEPTS).replace(WRONG_ANSWER_RULE, "When the answer is wrong, move on.")
        self.assertIn("the cited section has no wrong-answer rule",
                      cited_section_problems(text))


if __name__ == "__main__":
    unittest.main()
