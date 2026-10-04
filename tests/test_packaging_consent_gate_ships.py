"""The packaging flow's consent rules ship: measure, then ask, then write.

An archive is a distribution channel, so what the Bootcamper consents to is precisely **which of
their files travel**. Two rules make that consent informed, and both were shipped on 2026-08-26
with no invariant covering them:

- ⛔ **Run the dry run first. The question quotes a measured size, never an estimate.**
- ⛔ **Option 3 writes nothing at all.**

⚠️ **They were not overlooked; they were mis-accounted.** The implementing run followed
`implement-spec` Step 5's deferral path and pointed at the spec's pre-existing drafted invariant —
which covers the archive's *contents* and *verification* and was written **before the
conversational layer existed**, so it is silent on the gate. `production-readiness-audit-2026-08-26`
found it by reading all 36 hard-rule lines that run added. The lesson, worth more than the fix: a
deferral written against a draft inherits the draft's blind spots, so it must be written against
the diff.

⛔ **What this guard CANNOT check, said plainly rather than implied away.** Whether a given run
actually measures before asking, asks exactly once, and writes nothing on cancel is a property of
the conversation, not of the files. No static test reaches it — `dry-run` phase 3 owns it. What is
asserted here is that the rules **ship**, in the flow and in the command, and that the script they
depend on genuinely supports measuring without writing (which *is* testable, and is tested in
`tests/test_package_bootcamp.py`).

Stdlib only; shipped markdown read as text (INV-108).

Source spec: `specs/the-packaging-consent-gate-is-an-unregistered-guarantee.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
FLOW = PLUGIN / "skills" / "bootcamp-onboarding" / "packaging.md"
COMMAND = PLUGIN / "commands" / "package-bootcamp.md"
SPEC = (REPO_ROOT / "specs"
        / "the-bootcamp-cannot-leave-the-machine-it-was-built-on.md")


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


class Base(unittest.TestCase):
    def has(self, text, pattern, msg):
        self.assertTrue(re.search(pattern, text), msg)


class TheMeasureBeforeAskingRuleShips(Base):
    def setUp(self):
        self.text = flat(FLOW)

    def test_the_dry_run_precedes_the_question(self):
        self.has(self.text, r"(?i)Run the dry run first",
                 "the flow does not require the dry run before the question, so the consent "
                 "question can quote a number nobody measured")

    def test_it_forbids_an_estimate_explicitly(self):
        self.has(self.text, r"(?i)quotes a measured size, never an estimate",
                 "the flow does not forbid an estimated size; 'run the dry run' alone permits "
                 "asking with a guessed figure anyway")

    def test_the_dry_run_is_stated_to_write_nothing(self):
        self.has(self.text, r"(?i)\*\*writes nothing\*\*|writes \*\*nothing\*\*",
                 "the flow does not say the dry run writes nothing, so a reader cannot tell it "
                 "is safe to run before consent")

    def test_the_question_comes_before_any_write(self):
        """Ordering, as far as file order can carry it: the ask precedes the write step."""
        raw = FLOW.read_text(encoding="utf-8")
        ask = raw.index("👉 **What should the package contain?")
        write = raw.index("## Step 4: Write it")
        measure = raw.index("Run the dry run first")
        self.assertLess(measure, ask, "the dry-run step is documented after the question")
        self.assertLess(ask, write, "the question is documented after the write step")


class TheCancelOptionWritesNothing(Base):
    def setUp(self):
        self.text = flat(FLOW)

    def test_a_cancel_option_exists(self):
        self.has(self.text, r"(?i)3\.\s*\*\*Cancel",
                 "the consent question has no cancel option, so a bootcamper who wants neither "
                 "profile has no answer that declines")

    def test_cancel_is_stated_to_write_nothing(self):
        self.has(self.text, r"(?i)Option 3 writes nothing at all",
                 "the flow does not state that cancel writes nothing, which is the half a "
                 "reader cannot infer from the option label")


class TheQuestionIsSingularPinnedAndNumbered(Base):
    """INV-051/INV-056/INV-251 — one pinned, numbered question."""

    def setUp(self):
        self.raw = FLOW.read_text(encoding="utf-8")

    def test_exactly_one_question_is_asked(self):
        """Counts questions, not marker occurrences.

        ⚠️ A bare `.count("👉")` reads 2 here, and the second is the trigger paragraph's prose
        reference to "one 👉 question per yielding turn (INV-251)" -- a citation of the rule,
        not a question. INV-251 governs questions asked; only a marker that OPENS a line is one.
        Line-scoped by design for that reason (#424): a question opens on one line however it
        wraps after that.
        """
        asked = [line for line in self.raw.splitlines() if line.lstrip().startswith("👉")]
        self.assertEqual(
            1, len(asked),
            "the packaging flow asks %d questions; it must ask exactly one (INV-251): %r"
            % (len(asked), [a[:60] for a in asked]),
        )

    def test_the_question_is_numbered(self):
        self.has(" ".join(self.raw.split()), r"(?i)Reply with a number",
                 "the question does not ask for a numbered reply")
        for option in ("1. ", "2. ", "3. "):
            with self.subTest(option=option):
                self.assertIn(option, self.raw)

    def test_it_is_marked_pinned_verbatim(self):
        self.has(" ".join(self.raw.split()), r"(?i)Pin this verbatim \(INV-051/INV-056\)",
                 "the question is not marked pinned-verbatim, so its wording may be improvised "
                 "and the size figures rephrased away")


class TheCommandDoesNotLetAnArgumentStandInForConsent(Base):
    """An argument names a profile; it does not consent to what the archive carries."""

    def test_the_command_still_requires_the_dry_run_and_the_question(self):
        text = flat(COMMAND)
        self.has(text, r"(?i)still run the dry run and still ask the question",
                 "the command lets a profile argument skip the gate; the size and the "
                 "exclusions are what the bootcamper is consenting to")


class TheDraftedInvariantCoversTheGate(Base):
    """The finding itself: the draft governed contents and verification only."""

    def setUp(self):
        self.text = flat(SPEC)

    def test_the_draft_states_the_consent_gate_guarantee(self):
        """⚠️ The draft was SPLIT on 2026-08-27, so the gate is now its own statement.

        Before the split this asserted the single draft carried a "consent gate is part of the
        guarantee" clause. The gate is now draft 2 of 2 in its own right, which is a stronger
        form of the same property -- so the assertion moved to the heading that establishes it.
        """
        self.has(self.text, r"(?i)Draft 2 of 2 — what the Bootcamper CONSENTS to",
                 "the drafted invariant no longer carries the consent gate as its own statement, "
                 "so the two rules above remain guarantees the ruleset does not record")

    def test_the_draft_requires_a_measured_size(self):
        self.has(self.text,
                 r"(?i)MUST come from a `--dry-run` measurement rather than an\s+estimate",
                 "the draft's gate clause omits the measured-size requirement")

    def test_the_draft_requires_cancel_to_write_nothing(self):
        self.has(self.text, r"(?i)cancel option MUST write nothing",
                 "the draft's gate clause omits the cancel requirement")

    def test_the_amendment_records_why_it_was_missing(self):
        """A rule carrying the case that produced it is one a later editor cannot tidy away."""
        self.has(self.text, r"(?i)predated the\s+conversational layer",
                 "the draft does not record why the gate was omitted, so the lesson -- a "
                 "deferral written against a draft inherits its blind spots -- is lost")

    def test_the_split_records_why_the_two_are_separate(self):
        """Bolting a second subject onto a statement is how the first omission happened."""
        self.has(self.text, r"(?i)independently amendable|separate drafts with separate IDs",
                 "the split is recorded without its reason, so a later editor may merge the two "
                 "back and re-create the single statement that lost the gate")


if __name__ == "__main__":
    unittest.main()
