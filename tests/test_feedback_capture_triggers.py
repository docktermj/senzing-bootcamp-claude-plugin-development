"""The feedback hook must catch the ways people actually write the request — and no more.

`feedback-capture.py` exists so a bootcamper's "I want to give feedback" is handled the same
way **anywhere** in the bootcamp: it injects the pinned entry/exit banners, the INV-067
append-and-verify rule, the INV-015 save-locally-whatever-the-verdict rule, and the INV-321
show-and-consent gate before anything leaves the machine. Its trigger was a literal alternation
of eight fixed collocations, and ten of thirteen natural paraphrases missed. The one-word gap
between `I have feedback` (hit) and `I have some feedback about module 5` (miss) is the shape of
it: the pair had to be adjacent.

⛔ **The asymmetry is the point, and it is what this file mainly protects.** Modules 5–7 have
the bootcamper writing and debugging their own loader, mapper and query, so `I found a bug`,
`something is broken` and `this step is wrong` overwhelmingly mean *their* code. Injecting the
feedback workflow there prepends banner-and-gather instructions onto a turn where they want a
traceback explained — a derailed debugging turn, where a missed capture would merely have sent
them via `/bootcamp-feedback`. So bare fault language must stay quiet, and the same words with a
bootcamp/plugin/module referent must fire.

The hook is exercised as a **subprocess with real stdin**, in a temporary directory, because it
reads stdin and checks for `config/bootcamp_progress.json` at import time — importing it would
test something else.

Source spec: `specs/feedback-capture-misses-natural-phrasings.md`.

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "feedback-capture.py"

#: Must inject the feedback workflow. Every one names feedback, frames an explicit report,
#: or blames the bootcamp/plugin/module by name.
HITS = (
    "Bootcamp feedback: the banner was wrong",
    "I have feedback",
    "I have feedback on the mapping step",
    "I have some feedback about module 5",
    "I have a bit of feedback",
    "I'd like to give feedback",
    "can I give you some feedback",
    "let me give you some quick feedback",
    "sharing feedback now",
    "submit feedback",
    "provide feedback",
    "feedback about the bootcamp",
    "report a bug",
    "report an issue",
    "I want to report a problem",
    "I found a bug in the bootcamp",
    "something is broken in this bootcamp",
    "something is broken in this plugin",
    "this plugin is broken",
)

#: Must stay quiet: bare fault language with no bootcamp/plugin/module referent, plus
#: ordinary bootcamp conversation.
MISSES = (
    "I found a bug",
    "something is broken",
    "this step is wrong",
    "my loader is broken",
    "there is a bug in my mapper",
    "why is my query wrong",
    "the traceback says something is wrong",
    "load the truth set",
    "what is entity resolution",
    "show me the entity graph",
)

VERBOSITY_HITS = (
    "change verbosity",
    "can you be less wordy",
    "be more concise",
    "please be more detailed",
    "keep it brief",
    "shorter answers please",
    "too verbose",
    "more detail",
)


def run_hook(prompt, in_bootcamp=True):
    """Return the hook's stdout for `prompt`, run in a scratch project directory."""
    with tempfile.TemporaryDirectory() as tmp:
        if in_bootcamp:
            config = Path(tmp) / "config"
            config.mkdir()
            (config / "bootcamp_progress.json").write_text("{}\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"prompt": prompt}),
            capture_output=True, text=True, cwd=tmp, timeout=60,
        )
    return proc.returncode, proc.stdout


class TheHookRuns(unittest.TestCase):
    def test_the_hook_exists(self):
        self.assertTrue(HOOK.is_file(), "feedback-capture.py moved")

    def test_a_plain_feedback_prompt_injects_something(self):
        """Fixture check: if this fails, every HIT assertion below is meaningless."""
        code, out = run_hook("Bootcamp feedback: the banner was wrong")
        self.assertEqual(0, code)
        self.assertGreater(len(out.strip()), 100,
                           "the hook injected nothing for an unambiguous feedback prompt")

    def test_it_stays_silent_outside_a_bootcamp(self):
        """The property that keeps the plugin out of unrelated Claude Code sessions."""
        code, out = run_hook("Bootcamp feedback: something is wrong", in_bootcamp=False)
        self.assertEqual(0, code)
        self.assertEqual("", out.strip(),
                         "the hook spoke with no config/bootcamp_progress.json present")


class TheUnambiguousHalfIsCaught(unittest.TestCase):
    def test_every_feedback_phrasing_injects_the_workflow(self):
        for prompt in HITS:
            with self.subTest(prompt=prompt):
                _code, out = run_hook(prompt)
                self.assertIn("bootcamp feedback workflow", out.lower(),
                              "no feedback workflow injected for %r" % prompt)

    def test_the_injection_carries_its_guarantees(self):
        """A hit that omits the guarantees is the same loss as a miss."""
        _code, out = run_hook("I'd like to give feedback")
        for needle in ("INV-067", "INV-015", "APPEND"):
            with self.subTest(needle=needle):
                self.assertIn(needle, out,
                              "the injected guidance dropped %s" % needle)


class TheAmbiguousHalfStaysQuiet(unittest.TestCase):
    """⛔ Widening this pattern past here derails Modules 5–7."""

    def test_bare_fault_language_does_not_inject(self):
        for prompt in MISSES:
            with self.subTest(prompt=prompt):
                _code, out = run_hook(prompt)
                self.assertNotIn("bootcamp feedback workflow", out.lower(),
                                 "%r triggered the feedback workflow; in Modules 5-7 this "
                                 "is the bootcamper's own code and the injection derails "
                                 "the debugging turn" % prompt)

    def test_the_same_words_with_a_referent_do_inject(self):
        """The pair that proves the distinction is a distinction and not a gap."""
        for bare, attributed in (
            ("I found a bug", "I found a bug in the bootcamp"),
            ("something is broken", "something is broken in this plugin"),
        ):
            with self.subTest(pair=bare):
                _c, quiet = run_hook(bare)
                _c, loud = run_hook(attributed)
                self.assertNotIn("bootcamp feedback workflow", quiet.lower())
                self.assertIn("bootcamp feedback workflow", loud.lower(),
                              "%r did not trigger, so the attributed half is missing "
                              "rather than the bare half being excluded" % attributed)


class TheVerbosityBranchToleratesQualifiers(unittest.TestCase):
    def test_natural_verbosity_requests_are_caught(self):
        for prompt in VERBOSITY_HITS:
            with self.subTest(prompt=prompt):
                _code, out = run_hook(prompt)
                self.assertIn("verbosity", out.lower(),
                              "no verbosity guidance injected for %r" % prompt)


#: Must enter the NOTE flow. Every one is an imperative to record something.
NOTE_HITS = (
    "make a note",
    "take a note",
    "note to self: the vendor file has two name columns",
    "jot this down",
    "jot that down for me",
    "write this down",
    "remind me to check the truth-set counts before I trust this",
    "don't let me forget to ask Legal about the third source",
    "dont let me forget this",
    "add a to-do",
    "put this on my list",
    "for my notes: dba_name could be a second NAME",
    "make a memo",
    "capture this idea",
    "bootcamp note",
    "remember to check the counts",
    "make notes",
    "add a reminder",
)

#: ⛔ Must stay quiet. "note" and "remember" are ordinary words in a debugging turn, and
#: Modules 5–7 are nothing but debugging turns.
NOTE_MISSES = (
    "do you remember what module 3 covered",
    "remember when we loaded the truth set",
    "i remember that the engine resolved these",
    "note that the engine resolved 3 entities",
    "as noted above, the flag is required",
    "the tests are noted in the file",
    "can you write the loader for me",
    "i need to take a break",
)


class TheNoteBranchCatchesTheImperativeAndNothingElse(unittest.TestCase):
    """The inward counterpart to the feedback flow, with the same asymmetry.

    Enforces **INV-254**: the note control exists at any time, its trigger is anchored on
    an imperative to record something rather than on the bare verb, and a message
    satisfying both vocabularies is feedback.
    """

    def test_every_note_phrasing_enters_the_note_flow(self):
        for prompt in NOTE_HITS:
            with self.subTest(prompt=prompt):
                _code, out = run_hook(prompt)
                self.assertIn("bootcamp note workflow", out.lower(),
                              "no note workflow injected for %r" % prompt)

    def test_bare_recall_language_does_not_enter_it(self):
        """⛔ A spurious capture here derails the turn; a missed one costs a slash command."""
        for prompt in NOTE_MISSES:
            with self.subTest(prompt=prompt):
                _code, out = run_hook(prompt)
                self.assertNotIn("bootcamp note workflow", out.lower(),
                                 "the note flow fired on %r" % prompt)

    def test_the_injection_carries_the_notes_guarantees(self):
        _code, out = run_hook("make a note")
        for needle in ("docs/bootcamp_notes.md", "APPEND", "verify it landed",
                       "never merged", "never sent anywhere"):
            with self.subTest(needle=needle):
                self.assertIn(needle, out,
                              "the injected note guidance dropped %r" % needle)

    def test_it_does_not_ask_for_a_note_the_message_already_carries(self):
        """INV-006 — they already said it; asking is the pointless question."""
        _code, out = run_hook("remind me to check the counts")
        self.assertIn("do NOT ask what they would like to note", out)

    def test_a_note_is_never_routed_or_forwarded_like_feedback(self):
        _code, out = run_hook("make a note")
        self.assertNotIn("submit_feedback", out,
                         "a note must never reach the upstream offer")
        self.assertIn("no routing verdict", out.lower())


class FeedbackWinsWhenBothVocabulariesMatch(unittest.TestCase):
    """⛔ "make a note that the bootcamp is broken" is an attributed defect report.

    Routing it to notes would drop a defect report into a private keepsake the maintainer
    never sees. Feedback is also durable, also banner-bracketed, and also resumes the
    pending question, so nothing is lost by preferring it.
    """

    OVERLAPPING = (
        "make a note that the bootcamp is broken",
        "remind me that module 3 is wrong",
        "jot down that the plugin has a bug",
    )

    def test_an_overlapping_message_enters_the_feedback_flow(self):
        for prompt in self.OVERLAPPING:
            with self.subTest(prompt=prompt):
                _code, out = run_hook(prompt)
                self.assertIn("bootcamp feedback workflow", out.lower(),
                              "%r did not reach the feedback flow" % prompt)
                self.assertNotIn("bootcamp note workflow", out.lower(),
                                 "%r reached the note flow instead" % prompt)

    def test_the_precedence_is_stated_and_not_left_to_branch_order(self):
        source = HOOK.read_text(encoding="utf-8")
        flat = source.replace("\n#", " ").replace("\n", " ")
        self.assertIn("PRECEDENCE IS STATED HERE, NOT LEFT TO BRANCH ORDER", flat,
                      "the precedence decision has no reason recorded beside it, so the "
                      "next editor reorders the branches and silently changes it")


class TheReasoningIsRecordedAtThePattern(unittest.TestCase):
    """The regex will be edited again; the reasoning will not be rediscovered."""

    def setUp(self):
        self.source = HOOK.read_text(encoding="utf-8")

    def test_the_note_asymmetry_is_explained_too(self):
        flat = self.source.replace("\n#", " ").replace("\n", " ")
        self.assertIn("THE SAME ASYMMETRY APPLIES HERE", flat,
                      "the note vocabulary carries no record of why it is anchored on an "
                      "imperative rather than on the bare verb")

    def test_the_asymmetry_is_explained(self):
        self.assertIn("THE TWO HALVES OF THIS VOCABULARY ARE NOT SYMMETRIC", self.source,
                      "the comment explaining why bare fault language is excluded is gone")
        self.assertIn("missed capture is far cheaper than a spurious one",
                      self.source.replace("\n#", "").replace("\n", " "),
                      "the trade-off is not stated, so a future reader reads the gap as "
                      "an oversight")

    def test_it_forbids_deleting_the_distinction(self):
        flat = self.source.replace("\n#", " ").replace("\n", " ")
        self.assertIn('Do not "fix" a miss by deleting that distinction', flat,
                      "nothing warns the next editor off the obvious wrong fix")

    def test_the_excluded_referents_are_explained(self):
        flat = self.source.replace("\n#", " ").replace("\n", " ")
        self.assertIn('Deliberately does NOT include "this step"', flat,
                      "the narrowest and least obvious choice — excluding 'this step' — "
                      "has no reason recorded beside it")


if __name__ == "__main__":
    unittest.main()
