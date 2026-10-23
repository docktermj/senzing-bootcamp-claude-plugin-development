"""Something deterministic must create the recap checkpoint, and every no-op must say so.

`docs/progress/recap_checkpoint.md` was never created across all ten completed modules
of a full bootcamp run, and `docs/progress/` did not exist — in a session that had
crossed a compaction boundary, which is exactly when the checkpoint earns its keep.

The reported root cause ("no step says to write it") was wrong, and the real one was
worse: **every operation on the file was automated except creating it.** The PreCompact
hook folds it, SessionEnd folds it, SessionStart folds it, module-completion clears it —
and writing it was a sentence addressed to the guide. A contract specified entirely from
the consumer's end.

Two things made it undetectable:

1. **The reminder could not fire in time.** It lived in the *PreCompact* hook, so it
   could not reach the model until a compaction was already under way — after the window
   in which the checkpoint had to exist for the fold to have anything to fold.
2. **`fold_checkpoint()` was a silent no-op.** Nothing distinguished "folded a
   checkpoint" from "there was never a checkpoint", so ten modules passed with the safety
   net absent and no signal anywhere (INV-111).

What ships now splits the job honestly. `ensure_checkpoint()` owns the file's
*existence* — deterministically, from a per-turn hook, so it cannot be forgotten. The
guide still owns the *narrative*, because no hook can author prose; what changed is that
its absence is now reported instead of silent, and the reminder arrives on the turn the
file is created rather than mid-compaction.

The scaffold must never be foldable. `generate_recap_pdf.py` warns when the recap still
contains a `RECAP-CHECKPOINT` block, so folding an empty scaffold would both append a
meaningless block to the recap and raise a spurious warning at graduation. The tests
below pin that a scaffold fold writes **nothing at all** — not even an empty recap.

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SCRIPTS = os.path.join(PLUGIN, "scripts")
TICK = os.path.join(SCRIPTS, "checkpoint-tick.py")
HOOKS = os.path.join(PLUGIN, "hooks", "hooks.json")
GROUND_RULES = os.path.join(PLUGIN, "skills", "bootcamp-onboarding", "ground-rules.md")
COMPLETION = os.path.join(PLUGIN, "skills", "bootcamp-onboarding", "module-completion.md")
GRADUATION = os.path.join(PLUGIN, "skills", "graduation", "SKILL.md")
HOOKS_README = os.path.join(PLUGIN, "hooks", "README.md")
CHECKPOINT = os.path.join("docs", "progress", "recap_checkpoint.md")
RECAP = os.path.join("docs", "bootcamp_recap.md")

NARRATIVE = "## Information Shared\n\nEntity 42 resolved across three sources.\n"


def load_module():
    """Import recap_checkpoint the way the hooks do — by directory, not by package."""
    import importlib.util

    path = os.path.join(SCRIPTS, "recap_checkpoint.py")
    spec = importlib.util.spec_from_file_location("recap_checkpoint_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckpointProject:
    """A temp directory shaped like an active bootcamp project."""

    def __init__(self, active=True, module_name="Query, Visualize and Discover"):
        self.active = active
        self.module_name = module_name

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        if self.active:
            os.makedirs(os.path.join(self.root, "config"))
            with open(
                os.path.join(self.root, "config", "bootcamp_progress.json"),
                "w",
                encoding="utf-8",
            ) as fh:
                json.dump({"current_module": self.module_name}, fh)
        self.prev = os.getcwd()
        os.chdir(self.root)
        return self

    def __exit__(self, *exc):
        os.chdir(self.prev)
        self.tmp.cleanup()
        return False

    def path(self, rel):
        return os.path.join(self.root, rel)

    def read(self, rel):
        with open(self.path(rel), encoding="utf-8") as fh:
            return fh.read()

    def fill(self, text=NARRATIVE):
        """Write a narrative between the markers, as the guide would."""
        mod = load_module()
        current = self.read(CHECKPOINT)
        with open(self.path(CHECKPOINT), "w", encoding="utf-8") as fh:
            fh.write(current.replace(mod.END, text + "\n" + mod.END))


class TheFileIsCreatedWithoutModelCompliance(unittest.TestCase):

    def test_ensure_creates_the_file_and_its_parent_directory(self):
        """`docs/progress/` did not exist in the reported run either."""
        with CheckpointProject() as project:
            mod = load_module()
            self.assertFalse(os.path.exists(project.path(CHECKPOINT)))
            self.assertTrue(mod.ensure_checkpoint())
            self.assertTrue(os.path.isfile(project.path(CHECKPOINT)))

    def test_ensure_is_idempotent_and_never_overwrites_a_narrative(self):
        """It runs every turn; overwriting the guide's work would be catastrophic."""
        with CheckpointProject() as project:
            mod = load_module()
            mod.ensure_checkpoint()
            project.fill()
            self.assertFalse(mod.ensure_checkpoint(), "second call must not recreate")
            self.assertIn("Entity 42", project.read(CHECKPOINT))

    def test_the_scaffold_names_the_current_module(self):
        with CheckpointProject(module_name="Data Quality") as project:
            load_module().ensure_checkpoint()
            self.assertIn("Data Quality", project.read(CHECKPOINT))

    def test_a_malformed_progress_file_does_not_break_the_hook(self):
        """A hook must not fail a turn over a half-written scratch file (INV-227)."""
        with CheckpointProject() as project:
            with open(project.path(os.path.join("config", "bootcamp_progress.json")),
                      "w", encoding="utf-8") as fh:
                fh.write("{not json")
            mod = load_module()
            self.assertIsNone(mod.current_module())
            self.assertTrue(mod.ensure_checkpoint())


class AnUnfilledCheckpointIsNotFolded(unittest.TestCase):
    """The scaffold must never reach the recap — `generate_recap_pdf.py` warns on it."""

    def test_state_distinguishes_missing_scaffold_and_filled(self):
        with CheckpointProject() as project:
            mod = load_module()
            self.assertEqual("missing", mod.checkpoint_state())
            mod.ensure_checkpoint()
            self.assertEqual("scaffold", mod.checkpoint_state())
            project.fill()
            self.assertEqual("filled", mod.checkpoint_state())

    def test_an_emptied_checkpoint_counts_as_scaffold(self):
        """module-completion step 2d empties the file; that is not a narrative."""
        with CheckpointProject() as project:
            mod = load_module()
            mod.ensure_checkpoint()
            with open(project.path(CHECKPOINT), "w", encoding="utf-8") as fh:
                fh.write("")
            self.assertEqual("scaffold", mod.checkpoint_state())
            self.assertFalse(mod.fold_checkpoint())

    def test_folding_a_scaffold_writes_nothing_at_all(self):
        """Not even an empty recap: a stray block trips graduation's warning."""
        with CheckpointProject() as project:
            mod = load_module()
            mod.ensure_checkpoint()
            self.assertFalse(mod.fold_checkpoint())
            self.assertFalse(
                os.path.exists(project.path(RECAP)),
                "a scaffold fold must not create the recap — the renderer warns when a "
                "RECAP-CHECKPOINT block survives into it",
            )

    def test_folding_a_filled_checkpoint_carries_the_narrative(self):
        with CheckpointProject() as project:
            mod = load_module()
            mod.ensure_checkpoint()
            project.fill()
            self.assertTrue(mod.fold_checkpoint())
            recap = project.read(RECAP)
            self.assertIn("Entity 42", recap)
            self.assertIn(mod.START, recap)
            self.assertIn(mod.END, recap)

    def test_the_scaffold_guidance_never_reaches_the_recap(self):
        """The scaffold is instructions to the guide, not recap content."""
        with CheckpointProject() as project:
            mod = load_module()
            mod.ensure_checkpoint()
            project.fill()
            mod.fold_checkpoint()
            recap = project.read(RECAP)
            self.assertNotIn("Refresh this at each step boundary", recap)
            self.assertNotIn(mod.SCAFFOLD, recap)

    def test_repeated_folds_do_not_duplicate(self):
        """The pre-existing idempotence guarantee still holds."""
        with CheckpointProject() as project:
            mod = load_module()
            mod.ensure_checkpoint()
            project.fill()
            mod.fold_checkpoint()
            mod.fold_checkpoint()
            self.assertEqual(1, project.read(RECAP).count("Entity 42"))


class EveryOutcomeIsReported(unittest.TestCase):
    """INV-111: the silent no-op is the defect. All three outcomes go to stderr."""

    def _fold_stderr(self, setup):
        with CheckpointProject() as project:
            mod = load_module()
            setup(mod, project)
            import io
            import contextlib

            buffer = io.StringIO()
            with contextlib.redirect_stderr(buffer):
                mod.fold_checkpoint()
            return buffer.getvalue()

    def test_a_missing_checkpoint_is_reported(self):
        text = self._fold_stderr(lambda mod, project: None)
        self.assertRegex(text, r"(?i)nothing to fold")
        self.assertRegex(text, r"(?i)does not exist")

    def test_an_unfilled_checkpoint_is_reported_differently(self):
        """"Nobody created it" and "nobody wrote to it" are different failures."""
        text = self._fold_stderr(lambda mod, project: mod.ensure_checkpoint())
        self.assertRegex(text, r"(?i)nothing to fold")
        self.assertRegex(text, r"(?i)scaffold")
        self.assertNotRegex(text, r"(?i)does not exist")

    def test_a_successful_fold_is_reported(self):
        def setup(mod, project):
            mod.ensure_checkpoint()
            project.fill()

        self.assertRegex(self._fold_stderr(setup), r"(?i)folded")

    def test_reports_go_to_stderr_not_stdout(self):
        """Two callers are hooks whose stdout is a structured channel."""
        with CheckpointProject() as project:
            mod = load_module()
            import io
            import contextlib

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                mod.ensure_checkpoint()
                mod.fold_checkpoint()
            self.assertEqual("", out.getvalue())


class TheHookRunsEveryTurnAndStaysQuiet(unittest.TestCase):
    """Exercises the real script as Claude Code invokes it."""

    def _run(self, payload='{"prompt":"continue"}'):
        return subprocess.run(
            [sys.executable, TICK],
            input=payload,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

    def test_it_creates_the_checkpoint_and_returns_valid_json(self):
        with CheckpointProject() as project:
            result = self._run()
            self.assertEqual(0, result.returncode)
            self.assertTrue(os.path.isfile(project.path(CHECKPOINT)))
            payload = json.loads(result.stdout)
            self.assertEqual(
                "UserPromptSubmit",
                payload["hookSpecificOutput"]["hookEventName"],
            )

    def test_the_reminder_names_the_file_and_the_markers(self):
        with CheckpointProject():
            context = json.loads(self._run().stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
            self.assertIn("docs/progress/recap_checkpoint.md", context)
            self.assertIn("RECAP-CHECKPOINT:START", context)

    def test_later_turns_emit_nothing_on_stdout(self):
        """It must not compete with the step's pending question (INV-012)."""
        with CheckpointProject():
            self._run()
            second = self._run()
            self.assertEqual("", second.stdout.strip())
            self.assertEqual(0, second.returncode)

    def test_outside_a_bootcamp_it_does_nothing(self):
        """The plugin must never alter an unrelated Claude Code session."""
        with CheckpointProject(active=False) as project:
            result = self._run()
            self.assertEqual(0, result.returncode)
            self.assertEqual("", result.stdout.strip())
            self.assertFalse(os.path.exists(project.path(CHECKPOINT)))

    def test_status_never_lands_on_stdout(self):
        with CheckpointProject():
            result = self._run()
            self.assertNotIn("recap-checkpoint:", result.stdout)
            self.assertIn("recap-checkpoint:", result.stderr)


class TheWiringAndTheGuidanceAgree(unittest.TestCase):

    def test_the_hook_is_registered_on_user_prompt_submit(self):
        """The gap this closes was invisible to the whole suite; pin the wiring."""
        with open(HOOKS, encoding="utf-8") as fh:
            data = json.load(fh)
        hooks = data.get("hooks", data)
        # Read BOTH channels. Keying only on `args` made this assertion blind the moment the
        # scripts moved into `command` (INV-052, corrected 2026-08-21) — the shape a guard
        # was written against is not the shape in the file.
        args = [
            token
            for group in hooks["UserPromptSubmit"]
            for hook in group.get("hooks", [])
            for token in ([hook.get("command") or ""] + list(hook.get("args") or []))
        ]
        self.assertTrue(
            any("checkpoint-tick.py" in arg for arg in args),
            "nothing creates the checkpoint unless this hook is registered",
        )

    def test_the_hook_resolves_through_the_plugin_root(self):
        """INV-185: a bundled script is addressed via ${CLAUDE_PLUGIN_ROOT}."""
        with open(HOOKS, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint-tick.py", text)

    def test_the_ground_rules_say_who_creates_and_who_writes(self):
        """No shipped text may describe the checkpoint as maintained by nobody."""
        with open(GROUND_RULES, encoding="utf-8") as fh:
            text = fh.read()
        self.assertRegex(text, r"(?i)plugin creates the file")
        self.assertIn("checkpoint-tick.py", text)

    def test_module_completion_says_clearing_is_safe(self):
        """Step 2d tells the guide to empty or delete it; both must be stated safe."""
        with open(COMPLETION, encoding="utf-8") as fh:
            text = fh.read()
        self.assertRegex(text, r"(?i)(fresh empty scaffold|lays a fresh)")

    def test_graduation_does_not_treat_the_file_existing_as_an_interruption(self):
        """Now that the file normally exists, "a checkpoint remains" would mislead.

        Graduation would fold an empty block and then remove it again, and could report
        an interrupted module that never was.
        """
        with open(GRADUATION, encoding="utf-8") as fh:
            text = fh.read()
        self.assertRegex(text, r"(?i)file existing is not evidence")
        self.assertRegex(text, r"(?i)still holds a \*\*narrative\*\*|between\*\* the `START`")

    def test_the_hooks_readme_lists_the_new_hook(self):
        """The README enumerates the wiring; a stale table is shipped misinformation."""
        with open(HOOKS_README, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("checkpoint-tick.py", text)

    def test_the_scan_is_not_vacuous(self):
        for path in (TICK, HOOKS, GROUND_RULES, COMPLETION, GRADUATION, HOOKS_README):
            with self.subTest(file=os.path.basename(path)):
                self.assertTrue(os.path.isfile(path))
                self.assertGreater(os.path.getsize(path), 500)


if __name__ == "__main__":
    unittest.main()
