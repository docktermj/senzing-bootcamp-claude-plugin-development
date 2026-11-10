"""The Stop hook reads the turn's final text from the payload first (#873).

On 2026-11-06 two `/auto-test` walks ended a Data Processing turn partway through its
non-yielding steps with no 👉 question, and `plugins/senzing-bootcamp/scripts/stop-nudge.py`
ran on both turns and said nothing. The guide's session logs showed why: at hook time the
turn's final text record (written about 40 ms earlier) was not yet readable, so the last
record the hook could see was a **thinking-only** assistant record. Its text is empty, the
transcript reading treats that as undecided, and the hook stayed silent as **INV-054**
requires. Across all 61 Stop events in the saved auto-test sessions it never produced output.

Claude Code's Stop input carries an optional `last_assistant_message` ("Text content of the
last assistant message before stopping"). The hook now reads it first and falls back to the
transcript only when it is absent. These cases pin that order:

- the walks' shape (field without 👉, transcript ending in a thinking-only record) blocks;
- a field containing 👉 is silent whatever the transcript holds (INV-054);
- an empty or whitespace field is silent, as the transcript's empty-text case is;
- a missing or non-string field falls back to the transcript reading, which
  `tests/test_stop_nudge_silence_and_opt_outs.py` covers unchanged;
- Gates 1-3b (`stop_hook_active`, no progress file, the opt-outs, a completed bootcamp) still
  run before the field is read;
- the block reason tells the guide to continue to the next step that asks when the step it
  just presented asks nothing (INV-225), rather than adding a question (INV-247).

**Negative control, kept in the suite.** `PayloadIsDecisive.test_ignoring_the_field_
reproduces_the_walks_silence` runs a copy of the hook with the field read replaced by
`None` and asserts it stays silent on the walks' payload, so the first case fails against a
hook that ignores the field. Checked by hand on 2026-11-06 as well: with the same edit made
to the real script, `test_the_walks_shape_blocks` failed ("the hook stayed silent where it
had to block").

Each case runs the hook as a subprocess, the way Claude Code invokes it, using the project
fixture and helpers of `tests/test_stop_nudge_silence_and_opt_outs.py`. Standard library
only, and nothing under `plugins/` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_stop_nudge_silence_and_opt_outs import NUDGE, OPT_OUT_ENV, StopNudgeCase

#: The field the hook reads first. Named once so a rename in Claude Code's schema is a
#: one-line change here.
FIELD = "last_assistant_message"

#: The guide's final text on the 2026-11-06 walk's turn 6, reduced: a progress report that
#: stopped partway through Data Processing and asked nothing.
PAUSED_TEXT = (
    "Data Processing steps 1 and 2 are done. I stopped before step 3 and will continue "
    "on your next message."
)

#: A final text that ends on the step's pinned 👉 question.
ASKING_TEXT = "Your data is loaded.\n\n👉 **Ready to look at the results?**"

#: The current turn as the hook could read it on both walks: a real prompt, a tool call and
#: its result, then a THINKING-ONLY assistant record. The final text record that followed it
#: was not yet readable, so the transcript reading saw empty text and stayed silent.
THINKING_ONLY_TURN = (
    {"type": "user", "message": {"content": "Yes, let's process the data."}},
    {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "thinking", "thinking": "Run step 2.", "signature": "x"},
                {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}},
            ]
        },
    },
    {
        "type": "user",
        "message": {
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "data/"}]
        },
    },
    {
        "type": "assistant",
        "message": {
            "content": [{"type": "thinking", "thinking": "Report and stop.", "signature": "y"}]
        },
    },
)


class PayloadCase(StopNudgeCase):
    """The shared fixture plus a second transcript in the walks' shape."""

    def setUp(self):
        super().setUp()
        self.thinking_transcript = self.write_project_file(
            "thinking.jsonl",
            "".join(json.dumps(rec) + "\n" for rec in THINKING_ONLY_TURN),
        )

    def walks_payload(self, **extra):
        payload = {"transcript_path": self.thinking_transcript, FIELD: PAUSED_TEXT}
        payload.update(extra)
        return payload


class PayloadIsDecisive(PayloadCase):
    """Acceptance criteria 1, 2 and 5: the field decides whenever it is present."""

    def test_the_walks_shape_blocks(self):
        """The control shows the transcript alone cannot decide; the field then does."""
        self.assert_silent(
            {"transcript_path": self.thinking_transcript},
            because="(control) on a thinking-only last record with no field, as on both walks",
        )
        self.assert_blocks(
            self.walks_payload(),
            because="where last_assistant_message has no 👉 and the transcript is thinking-only",
        )

    def test_a_field_with_a_pointer_is_silent_whatever_the_transcript_holds(self):
        """INV-054. The control shows the readable transcript blocks on its own."""
        self.assert_blocks(
            {"transcript_path": self.transcript},
            because="(control) the shared transcript, with no field, must block",
        )
        for transcript in (
            self.transcript,
            self.thinking_transcript,
            os.path.join(self.project, "no-such-transcript.jsonl"),
        ):
            with self.subTest(transcript=os.path.basename(transcript)):
                self.assert_silent(
                    {"transcript_path": transcript, FIELD: ASKING_TEXT},
                    because="where last_assistant_message already carries a 👉 question",
                )

    def test_the_field_needs_no_transcript(self):
        """The field alone decides: no transcript path, or one naming no file, still blocks."""
        self.assert_blocks({FIELD: PAUSED_TEXT}, because="with no transcript_path at all")
        self.assert_blocks(
            {
                "transcript_path": os.path.join(self.project, "no-such-transcript.jsonl"),
                FIELD: PAUSED_TEXT,
            },
            because="with a transcript_path naming no file",
        )

    def test_ignoring_the_field_reproduces_the_walks_silence(self):
        """Negative control (criterion 5): a hook that never reads the field is silent on
        the walks' payload, so `test_the_walks_shape_blocks` fails against it."""
        with open(NUDGE, encoding="utf-8") as handle:
            source = handle.read()
        read = 'payload.get("{}")'.format(FIELD)
        self.assertEqual(
            source.count(read), 1,
            "the hook must read {} in exactly one place for this mutation to mean anything"
            .format(FIELD),
        )
        scratch = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, scratch)
        mutant = os.path.join(scratch, "stop-nudge.py")
        with open(mutant, "w", encoding="utf-8") as handle:
            handle.write(source.replace(read, "None"))
        env = dict(os.environ)
        env.pop(OPT_OUT_ENV, None)
        env["PYTHONIOENCODING"] = "utf-8"
        # The copy imports module_start_apparatus (#905); it finds its siblings here.
        env["PYTHONPATH"] = os.path.dirname(NUDGE)
        proc = subprocess.run(
            [sys.executable, mutant],
            input=json.dumps(self.walks_payload()),
            cwd=self.project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            proc.stdout, "",
            "a hook that ignores {} blocked on the walks' payload, so the payload-first "
            "test no longer proves the field is read".format(FIELD),
        )


class EmptyOrAbsentField(PayloadCase):
    """The edge cases: empty text is silent; a missing field falls back to the transcript."""

    def test_an_empty_or_whitespace_field_is_silent(self):
        """As today's empty-text case. The control: the same transcript blocks with no field."""
        self.assert_blocks(
            {"transcript_path": self.transcript},
            because="(control) the shared transcript, with no field, must block",
        )
        for text in ("", "   \n\t"):
            with self.subTest(text=repr(text)):
                self.assert_silent(
                    {"transcript_path": self.transcript, FIELD: text},
                    because="where last_assistant_message is present but has no text",
                )

    def test_a_missing_or_non_string_field_falls_back_to_the_transcript(self):
        """Older Claude Code: the transcript reading decides, block and silence alike."""
        for value in (None, 42, ["text"]):
            with self.subTest(value=value):
                self.assert_blocks(
                    {"transcript_path": self.transcript, FIELD: value},
                    because="where the field is not a string and the transcript is decisive",
                )
                self.assert_silent(
                    {"transcript_path": self.thinking_transcript, FIELD: value},
                    because="where the field is not a string and the transcript is undecided",
                )

    def test_a_non_object_payload_is_silent(self):
        """The hook never raises on bad input: a JSON list or garbage stays silent."""
        for raw in ("[1, 2]", "not json", ""):
            with self.subTest(raw=raw):
                env = dict(os.environ)
                env.pop(OPT_OUT_ENV, None)
                proc = subprocess.run(
                    [sys.executable, NUDGE],
                    input=raw,
                    cwd=self.project,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=env,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout, "")


class EarlierGatesStillRunFirst(PayloadCase):
    """Gates 1-3b are unchanged and precede the field. Each case's control is the walks'
    payload blocking in the same project."""

    def test_stop_hook_active_wins_over_the_field(self):
        self.assert_blocks(self.walks_payload(), because="(control)")
        self.assert_silent(
            self.walks_payload(stop_hook_active=True),
            because="where stop_hook_active is true (Gate 1: at most one block per stop)",
        )

    def test_no_progress_file_wins_over_the_field(self):
        self.assert_blocks(self.walks_payload(), because="(control)")
        os.remove(os.path.join(self.project, "config", "bootcamp_progress.json"))
        self.assert_silent(self.walks_payload(), because="outside a bootcamp project (Gate 2)")

    def test_the_opt_outs_win_over_the_field(self):
        self.assert_blocks(self.walks_payload(), because="(control)")
        self.assert_silent(
            self.walks_payload(), env={OPT_OUT_ENV: "1"}, because="with the env opt-out (Gate 3)"
        )
        self.write_project_file(
            os.path.join("config", "bootcamp_preferences.yaml"), "disable_stop_nudge: true\n"
        )
        self.assert_silent(self.walks_payload(), because="with the preferences opt-out (Gate 3)")

    def test_a_completed_bootcamp_wins_over_the_field(self):
        self.assert_blocks(self.walks_payload(), because="(control)")
        self.write_project_file(
            os.path.join("config", "bootcamp_preferences.yaml"), "bootcamp_complete: true\n"
        )
        self.assert_silent(self.walks_payload(), because="once the bootcamp is complete (Gate 3b)")


class TheBlockReasonContinuesANonYieldingStep(PayloadCase):
    """Criterion 4: a step that asks nothing continues to the next step that asks (INV-225),
    and the reason does not tell the guide to add a question to it (INV-247)."""

    def test_the_reason_sends_a_non_yielding_step_on(self):
        reason = self.assert_blocks(self.walks_payload(), because="on the walks' payload")["reason"]
        self.assertIn("asks no 👉 question", reason)
        self.assertIn("NON-YIELDING", reason)
        self.assertIn("continue now to the next step that asks one", reason)
        self.assertIn("do not add a question to it", reason)

    def test_the_continue_clause_comes_before_the_add_a_question_clause(self):
        """Read in order, the model meets 'continue' before the fallback that adds a
        question, so a pause in a non-yielding run is not answered with an invented 👉."""
        reason = self.assert_blocks(self.walks_payload(), because="on the walks' payload")["reason"]
        self.assertLess(
            reason.index("continue now to the next step that asks one"),
            reason.index("add exactly one closing question"),
        )


if __name__ == "__main__":
    unittest.main()
