"""The transcript linter reports a re-ask, not a sanctioned re-presentation (#842).

`.claude/skills/auto-test/transcript_lint.py` reported ten WATCH findings on a 16-turn
`confused` walk on 2026-10-27, and nine were false positives:

* **`check_repeat_questions` (INV-006)** flagged every 👉 line whose first twelve words had
  appeared before. A curious Bootcamper asked a side question after each "Do you have any
  other questions about entity resolution before we continue?", and the guide re-presented
  the pending question each time, as `ground-rules.md` → "Ask-once" requires. Five findings
  came from that, one more from the onboarding question, and one from the note recital's
  confirm question, which `notes.md` Step 3 says is not a re-ask under INV-006.
* **`check_or_joined_choices` (INV-051)** read the recited note
  "> Ask the data team: is our claims/policy feed batch or streaming?", the Bootcamper's
  own words in a blockquote, as a choice offered to them, at two turns.

The one real finding was a re-ask: the Bootcamper replied "Make a note about asking the data
team. Ready to continue.", and after the note's exit banner the guide asked the same
question again (#841). The linter now reads the Bootcamper's replies from the walk's
`bootcamper` events and reports a repeat only when the reply to its previous asking had no
`?` (the answer rule, spec revision 1), never reports the recital's confirm question, and
skips blockquoted lines and fenced code when looking for or-joined choices.

**The fixture is the walk, trimmed.** `tests/fixtures/walk-confused-questions.jsonl` holds the
assistant text events and `bootcamper` events of
`~/senzing-autotest/reports/20261027-113426-confused.transcript.jsonl`, verbatim and in
order, and nothing else: no tool input or output, no system event, no host path. The
linter numbers the real re-ask turn 16 (it counts every assistant text event, three of them
before the Bootcamper's first reply) and reports it as a repeat of turn 13.

⛔ **What this cannot establish.** The answer rule is mechanical, and its known limit is in
`check_repeat_questions`' docstring: a reply that answers and also asks something reads as a
side question, so a re-ask after it is not reported. Only `dry-run` phase 3 observes that
case. A clean lint is not a passed phase 3 (`transcript_lint.py`'s own docstring). INV-359's
no-re-ask clause for Module 7 step 1 is seen through `check_repeat_questions` too, so the
same limit applies there; the #842 ledger entry queues a dated note to INV-359 saying so.

Stdlib only, no import from `plugins/` (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
AUTO_TEST = REPO_ROOT / ".claude" / "skills" / "auto-test"
LINTER = AUTO_TEST / "transcript_lint.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "walk-confused-questions.jsonl"
NOTES = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
         / "notes.md")

sys.path.insert(0, str(AUTO_TEST))

import transcript_lint  # noqa: E402

PENDING = "Do you have any other questions about entity resolution before we continue?"
#: The turn the guide asked PENDING again after "Ready to continue." (#841), as the linter
#: numbers it, and the turn of the asking that reply answered.
RE_ASK, ANSWERED = 16, 13
#: The turns of the nine false positives the linter reported before #842.
SIDE_QUESTION_REPEATS = (5, 12, 13, 17, 18, 19)
RECITAL_REPEAT = 15
QUOTED_NOTE = (14, 15)

#: An absolute path on any of the three platforms, read in the decoded text.
HOST_PATH = re.compile(r"(?:/home/|/Users/|/tmp/|/var/|/private/|~/"
                       r"|\b[A-Za-z]:[\\/]\w|\\\\\w)")


def codes(findings, code):
    return [f for f in findings if f["code"] == code]


class TheFixtureIsTheWalkTrimmed(unittest.TestCase):
    """A fixture that lost its replies or its re-ask would make the checks below vacuous."""

    def setUp(self):
        self.events = [json.loads(line) for line in
                       FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_it_holds_only_assistant_text_and_bootcamper_replies(self):
        for event in self.events:
            self.assertIn(event["type"], ("assistant", "bootcamper"))
            if event["type"] == "assistant":
                blocks = event["message"]["content"]
                self.assertEqual(["text"], [b["type"] for b in blocks],
                                 "an assistant event carries something besides text")
            else:
                self.assertEqual({"type", "turn", "persona", "text"}, set(event))

    def test_it_names_no_host_path(self):
        for number, event in enumerate(self.events, 1):
            if event["type"] == "assistant":
                said = [b["text"] for b in event["message"]["content"]]
            else:
                said = [event["text"], event["persona"]]
            for text in said:
                hit = HOST_PATH.search(text)
                self.assertIsNone(hit, f"{FIXTURE.name} event {number} names a host "
                                       f"path: {hit and hit.group(0)!r}")

    def test_it_carries_the_walk_the_issue_describes(self):
        turns, replies = transcript_lint.load_walk(FIXTURE)
        self.assertEqual(19, len(turns))
        self.assertEqual(16, sum(r is not None for r in replies))
        self.assertIn("NOTE SAVED — BACK TO THE BOOTCAMP", turns[RE_ASK - 1])
        self.assertIn(PENDING, turns[RE_ASK - 1])
        self.assertIn(PENDING, turns[ANSWERED - 1])
        self.assertEqual("Make a note about asking the data team. Ready to continue.",
                         replies[ANSWERED - 1])

    def test_load_still_returns_the_turns_alone(self):
        self.assertEqual(transcript_lint.load_walk(FIXTURE)[0],
                         transcript_lint.load(FIXTURE))


class TheWalkReportsOnlyTheRealReAsk(unittest.TestCase):
    """Criterion 1: no INV-051 finding and exactly one INV-006 finding, the re-ask."""

    def setUp(self):
        self.turns, self.replies = transcript_lint.load_walk(FIXTURE)

    def assert_only_the_re_ask(self, findings):
        self.assertEqual([], codes(findings, "INV-051-or-joined"))
        re_asked = codes(findings, "INV-006-re-asked")
        self.assertEqual([RE_ASK], [f["turn"] for f in re_asked], re_asked)
        self.assertIn(f"repeats turn {ANSWERED}", re_asked[0]["message"])
        self.assertEqual(re_asked, findings, "the walk raised another finding")

    def test_lint(self):
        self.assert_only_the_re_ask(transcript_lint.lint(self.turns, replies=self.replies))

    def test_the_command_line(self):
        run = subprocess.run([sys.executable, str(LINTER), str(FIXTURE), "--json"],
                             capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(0, run.returncode, run.stderr)
        self.assert_only_the_re_ask(json.loads(run.stdout))


class RemovingAnExemptionBringsItsFalsePositivesBack(unittest.TestCase):
    """Criterion 2's negative control: each exemption is what silences its findings."""

    def setUp(self):
        self.turns, self.replies = transcript_lint.load_walk(FIXTURE)

    def turns_flagged(self, code, **patch):
        with mock.patch.multiple(transcript_lint, **patch):
            findings = transcript_lint.lint(self.turns, replies=self.replies)
        return sorted({f["turn"] for f in codes(findings, code)})

    def test_without_the_replies_the_side_question_repeats_return(self):
        findings = transcript_lint.lint(self.turns)
        self.assertEqual(sorted(SIDE_QUESTION_REPEATS + (RE_ASK,)),
                         [f["turn"] for f in codes(findings, "INV-006-re-asked")])

    def test_without_the_recital_exemption_the_recital_returns(self):
        flagged = self.turns_flagged("INV-006-re-asked",
                                     RECITAL_CONFIRM="a question nobody ever asks")
        self.assertEqual([RECITAL_REPEAT, RE_ASK], flagged)

    def test_without_the_quote_and_fence_skip_the_quoted_note_returns(self):
        flagged = self.turns_flagged(
            "INV-051-or-joined", _outside_quotes_and_fences=lambda text: text.splitlines())
        self.assertEqual(list(QUOTED_NOTE), flagged)


class ARealReAskIsStillReported(unittest.TestCase):
    """Criteria 2 and 3 on synthetic turns: the rule bites where it should."""

    QUESTION = "\U0001f449 **Which data source would you like to start with?**"

    def repeats(self, replies):
        findings = transcript_lint.check_repeat_questions(
            [self.QUESTION, "Noted.", self.QUESTION], replies)
        return [f["turn"] for f in findings]

    def test_a_re_ask_after_an_answer_is_reported(self):
        self.assertEqual([3], self.repeats(["The claims file.", None, None]))

    def test_an_answer_split_across_turns_is_still_an_answer(self):
        self.assertEqual([3], self.repeats(["The claims file.", "Sure.", None]))

    def test_a_re_presentation_after_a_side_question_is_not(self):
        self.assertEqual([], self.repeats(["What counts as a data source?", None, None]))

    def test_a_side_question_anywhere_before_the_repeat_sanctions_it(self):
        self.assertEqual([], self.repeats(["Hmm.", "Wait, what is a record?", None]))

    def test_a_repeat_with_no_reply_between_is_reported(self):
        self.assertEqual([3], self.repeats([None, None, None]))
        self.assertEqual([3], self.repeats(None))

    def test_each_repeat_is_judged_against_the_asking_before_it(self):
        """Side question, then an answer: the second repeat is the re-ask."""
        findings = transcript_lint.check_repeat_questions(
            [self.QUESTION] * 3, ["Why do you ask?", "The claims file.", None])
        self.assertEqual([3], [f["turn"] for f in findings])
        self.assertIn("repeats turn 2", findings[0]["message"])

    def test_an_or_joined_choice_outside_a_blockquote_is_reported(self):
        line = "\U0001f449 Would you like to start with claims or policies?"
        for text in (line, f"> Your note.\n\n{line}", f"```\ncode\n```\n{line}"):
            self.assertEqual(1, len(transcript_lint.check_or_joined_choices([text])), text)

    def test_quoted_and_fenced_or_lines_are_not(self):
        for text in ("> Is our feed batch or streaming?",
                     "  > Is our feed batch or streaming?",
                     "```text\nIs our feed batch or streaming?\n```",
                     "~~~\nIs our feed batch or streaming?\n~~~"):
            self.assertEqual([], transcript_lint.check_or_joined_choices([text]), text)


class TheExemptQuestionIsTheShippedRecital(unittest.TestCase):
    """`RECITAL_CONFIRM` must be the question `notes.md` Step 3 pins, or it exempts nothing."""

    def test_it_matches_notes_step_3(self):
        text = NOTES.read_text(encoding="utf-8")
        step = re.search(r"^## Step 3: Recite it for approval\n(.*?)(?=^## )", text,
                         re.M | re.S)
        self.assertIsNotNone(step, "notes.md has no 'Step 3: Recite it for approval'")
        asked = [line for line in step.group(1).splitlines()
                 if re.match(r"^>\s*\U0001f449\s*\*\*", line)]
        self.assertEqual(1, len(asked), asked)
        question = re.sub(r"^[>\s]*\U0001f449\s*\**", "", asked[0])
        self.assertTrue(question.startswith(transcript_lint.RECITAL_CONFIRM),
                        f"notes.md Step 3 now asks {question!r}")


class TheDocstringStatesTheRuleAndItsLimit(unittest.TestCase):
    """Criterion 4."""

    def test_docstring(self):
        doc = " ".join(transcript_lint.check_repeat_questions.__doc__.split())
        for clause in ("a reply is an answer when it contains no ``?``",
                       "a side question, after which re-presenting the pending question "
                       "is sanctioned",
                       "**Known limit.**",
                       "a re-ask after it is not reported"):
            self.assertIn(clause, doc)


if __name__ == "__main__":
    unittest.main()
