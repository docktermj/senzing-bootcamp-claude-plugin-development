"""The Stop hook stays silent unless it is sure, and both of its opt-outs work.

Guards **INV-054** (the closing-question safety net MUST NEVER make the Bootcamper see the
same 👉 question twice, so it blocks only when it can positively determine the turn ended
without one, and stays silent whenever that determination is not decisive) and **INV-055**
(the nudge MUST be disableable through the `SENZING_BOOTCAMP_DISABLE_STOP_NUDGE` environment
variable or a `disable_stop_nudge` key in `config/bootcamp_preferences.yaml`).

Both rules shipped with `plugins/senzing-bootcamp/scripts/stop-nudge.py` and neither was
guarded by any test, by ID or by behavior, until this file. A `/dry-run` phase 2 sweep ran
every row below by hand on 2026-10-18 against a scaffolded project and recorded the observed
result beside each expectation, so these assertions are known-good rather than hypothetical;
what was missing was anything that re-runs them.

**Why the silence rows and the block row live in ONE file.** A hook that is silent because it
is broken — a syntax error, a gate that returns early, an exception swallowed into exit 0 —
satisfies every silence row on its own. The block row is the positive control that makes them
mean anything, so splitting it into a second file would let either half rot into vacuous truth
without the other noticing (INV-265 is the general form of that failure). For the same reason
each silence case here runs the control itself: the unreadable-transcript case first shows the
same payload blocking with a readable transcript, the `stop_hook_active` case first shows the
same payload blocking without the flag, and both opt-out cases first show the very payload
they then silence producing a block. A test that asserted only emptiness would pass against a
nudge that never fires at all, which is the one outcome that would make INV-054 unfalsifiable.

Negative-controlled on 2026-10-19, each mutation reverted immediately and `__pycache__`
cleared between them: deleting the opt-out check from `nudge_disabled()` fails both INV-055
cases; deleting the `stop_hook_active` guard fails the `stop_hook_active` case; deleting the
unreadable-transcript guard fails the unreadable-transcript case.

The hook reads its payload from stdin and resolves `config/` against the current working
directory, so it cannot be imported — each case runs it as a subprocess with a synthetic
payload and a temp project directory, the way Claude Code invokes it. Standard library only,
and nothing under `plugins/` is imported, so this file stays inside INV-108 and `propagate.sh`
never ships it to a bootcamper.

Scope: the `stop-hook-false-positive` source spec shares an uncited third rule with
`enrich-feedback-context` — the one requiring a "Context when reported" diagnostic section on
every bootcamp feedback entry — and it is deliberately not guarded here. It governs what a
guide writes during a live turn, which is `dry-run` phase 3's business rather than an offline
guard. It is named rather than numbered on purpose: `coverage_reports.py invariants` scores an
ID appearing anywhere under `tests/` as cited, so writing that rule's number in this sentence
would retire it from the uncited list while nothing in this file asserts one word of it --
the false all-clear `tests/test_invariant_enforcer_citations.py` exists to prevent, bought
here for nothing but a better-looking count.

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUDGE = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts", "stop-nudge.py")

#: The documented environment opt-out, one half of INV-055.
OPT_OUT_ENV = "SENZING_BOOTCAMP_DISABLE_STOP_NUDGE"

#: The documented preferences opt-out, the other half. Written as the Bootcamper would:
#: a top-level key, with an unrelated key beside it so a parser that matches anywhere in
#: the file rather than at the top level is not accidentally satisfied.
OPT_OUT_PREFERENCES = "name: Ada\ndisable_stop_nudge: true\n"

#: A settled turn that ended WITHOUT a 👉 question: a real user prompt, then one assistant
#: record whose final content block is text. This is the transcript every case below uses —
#: the silence rows are only informative because this one produces a block.
NO_POINTER_TURN = (
    {"type": "user", "message": {"content": "I have finished writing up the business problem."}},
    {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "text", "text": "Your business problem document is saved in docs/."}
            ]
        },
    },
)


class StopNudgeCase(unittest.TestCase):
    """An active bootcamp project plus the one transcript that makes the hook speak."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.project = tmp.name
        # Gate 2 tests this file's EXISTENCE, not its contents (INV-227).
        os.makedirs(os.path.join(self.project, "config"))
        self.write_project_file(os.path.join("config", "bootcamp_progress.json"), "{}")
        self.transcript = os.path.join(self.project, "transcript.jsonl")
        self.write_project_file(
            "transcript.jsonl",
            "".join(json.dumps(rec) + "\n" for rec in NO_POINTER_TURN),
        )

    def write_project_file(self, relative_path, text):
        path = os.path.join(self.project, relative_path)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def run_nudge(self, payload, env=None):
        """Invoke stop-nudge.py as Claude Code does; return (exit code, stdout)."""
        run_env = dict(os.environ)
        # A runner that happens to export the opt-out would silence every row below and
        # turn the whole file green while asserting nothing, so it is removed rather than
        # assumed absent; the opt-out cases put it back deliberately.
        run_env.pop(OPT_OUT_ENV, None)
        # The block reason carries 👉, so the pipe's encoding is pinned here instead of
        # being inherited from whatever locale the runner has. This decides how the
        # character crosses the pipe, never whether the hook blocks.
        run_env["PYTHONIOENCODING"] = "utf-8"
        if env:
            run_env.update(env)
        proc = subprocess.run(
            [sys.executable, NUDGE],
            input=json.dumps(payload),
            cwd=self.project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=run_env,
        )
        return proc.returncode, proc.stdout

    def assert_silent(self, payload, env=None, because=""):
        code, out = self.run_nudge(payload, env=env)
        self.assertEqual(code, 0, "the hook must exit 0 " + because)
        self.assertEqual(out, "", "the hook must write nothing to stdout " + because)

    def assert_blocks(self, payload, env=None, because=""):
        """The positive control: the same subprocess call, decisive, so it speaks."""
        code, out = self.run_nudge(payload, env=env)
        self.assertEqual(code, 0, "a blocking Stop hook still exits 0 " + because)
        self.assertNotEqual(
            out, "",
            "the hook stayed silent where it had to block " + because
            + " -- every silence case in this file is vacuous while this is true",
        )
        decision = json.loads(out)
        self.assertEqual(decision.get("decision"), "block", "expected a block " + because)
        self.assertTrue(
            decision.get("reason", "").strip(),
            "a block with no reason leaves the model nothing to act on " + because,
        )
        return decision


class TheNetBlocksOnlyWhenItIsSure(StopNudgeCase):
    """INV-054: silent whenever the determination is not decisive."""

    def test_a_settled_turn_without_a_pointer_blocks(self):
        """The positive control, and the one row that gives the others their meaning.

        Observed by hand 2026-10-18: exit 0, stdout `{"decision": "block", ...}`.
        """
        self.assert_blocks(
            {"transcript_path": self.transcript},
            because="on a settled turn whose final assistant message carries no pointer",
        )

    def test_an_unreadable_transcript_is_undecided_and_silent(self):
        """A `transcript_path` naming no file: undecided, so nothing is said.

        Observed by hand 2026-10-18: exit 0, empty stdout. The control runs first and
        differs only in the path, so a silence produced by the hook being inert is
        separated from a silence produced by this guard.
        """
        self.assert_blocks(
            {"transcript_path": self.transcript},
            because="(control) with the readable transcript this payload must block",
        )
        self.assert_silent(
            {"transcript_path": os.path.join(self.project, "no-such-transcript.jsonl")},
            because="where the transcript cannot be read, so the turn is undecided",
        )

    def test_stop_hook_active_is_silent_on_a_readable_transcript(self):
        """The loop breaker: a continuation the nudge itself caused is never re-nudged.

        Observed by hand 2026-10-18: exit 0, empty stdout. The transcript is the one that
        blocks, so the only difference between the control and the case is the flag.
        """
        self.assert_blocks(
            {"transcript_path": self.transcript},
            because="(control) without the flag this exact payload must block",
        )
        self.assert_silent(
            {"stop_hook_active": True, "transcript_path": self.transcript},
            because="where stop_hook_active is true, however decisive the transcript is",
        )


class BothDocumentedOptOutsSilenceTheNudge(StopNudgeCase):
    """INV-055: each opt-out is asserted against the payload that blocks without it."""

    def test_the_environment_variable_opts_out(self):
        """Observed by hand 2026-10-18: exit 0, empty stdout."""
        self.assert_blocks(
            {"transcript_path": self.transcript},
            because="(control) without the environment variable this payload must block",
        )
        self.assert_silent(
            {"transcript_path": self.transcript},
            env={OPT_OUT_ENV: "1"},
            because="where " + OPT_OUT_ENV + " is set",
        )

    def test_the_preferences_key_opts_out(self):
        """Observed by hand 2026-10-18: exit 0, empty stdout."""
        self.assert_blocks(
            {"transcript_path": self.transcript},
            because="(control) with no preferences file this payload must block",
        )
        self.write_project_file(
            os.path.join("config", "bootcamp_preferences.yaml"), OPT_OUT_PREFERENCES
        )
        self.assert_silent(
            {"transcript_path": self.transcript},
            because="where config/bootcamp_preferences.yaml sets disable_stop_nudge: true",
        )


if __name__ == "__main__":
    unittest.main()
