"""`/release-cycle` runs the release cycle as one resumable run, and its helper does the mechanics (#573).

The skill is `.claude/skills/release-cycle/SKILL.md`, the procedure; `cycle.py` beside it owns
everything a session could otherwise do twice or get wrong by hand: the run state, the next
step, what each step runs, the stage-1 merge by dedupe key, the checkpoint verdicts, the filing
order, and the run's one `specs/IMPLEMENTED.md` entry. It reads and changes the drafts manifest
only through `drafts.py` (INV-300, INV-368).

What this pins, each predicate over text with a negative control:

1. **The helper, offline.** The kickoff answers are required, never defaulted (INV-333). A
   resumed run starts at the first unfinished step, and a finished step is refused, so nothing
   runs twice; a draft step with no drafts is `clean` and skips its build pass. Drafts citing the
   same sites merge into one record listing every source, once, however often `merge-drafts`
   runs, and the list has no duplicate dedupe key; overlapping keys are shown. A "yes except N"
   strikes exactly what was shown, and refuses a draft changed or added after the list was shown
   (INV-314, 2026-10-13 note). A merged draft takes its record's issue number, so its own
   skill's `--file` files nothing for it; a stopped `--file` prints a tracker search before
   filing again. The ledger entry records each step and every unresolved draft, marked not filed
   (INV-317's 2026-10-13 note), passes the ledger's own checks, is written once in place, and is
   withdrawn only when it is exactly what was written. The after-filing steps that write tracked
   files are held at `--file`, printed only at stage 5, before `/review-invariants`, and never
   run twice on resume (the graft from race approach B). No printed step adds `unattended-ok`,
   sends `submit_feedback`, pushes, or names a version bump, and the loop gets `--no-merge`
   unless the kickoff says to merge.
2. **The skill** states each checkpoint and every guardrail, says it follows the three
   slash-only skills' files rather than invoking them, is slash-only itself, cites both
   helpers, and restates no part of the manifest format. Where a run writes is stated once, in
   "Stopping, and the ledger entry", naming every write; `cycle.py` cites it, the pending block
   quotes it and drafts the same rule, and no site keeps the retired "nothing under `specs/`
   until the run stops" (#609).
3. **The register**: `docs/FAMILY_WORKFLOW.md` §2 lists `release-cycle` (drives 1–4, parent
   required, children not mandated) and §3 names it. That the name resolves both ways is
   `tests/test_canonical_operations_resolve.py` and
   `tests/test_documented_dev_commands_match_the_shipped_set.py`.

⚠️ **What this does NOT establish:** that a live run stops only at its checkpoints, that a
subagent never asks the maintainer anything, that the session runs what `cycle.py next`
prints, or that the slash-only skills' gates hold when followed. Those are properties of a
session; this pins that the helper behaves and that the instructions say so.

This module enforces the DEFERRED INVARIANT (INV-NNN, not yet minted) in the
`release-cycle-runs-the-cycle-with-five-checkpoints` ledger entry. It pins that the helper
refuses a repeated step and filing, and that the skill states the rules; it cannot establish
that a live run obeys them.

Stdlib only; no network, no `gh`, no git write (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_spec_ledger_invariants as ledger_checks

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "release-cycle"
SKILL = SKILL_DIR / "SKILL.md"
CYCLE = SKILL_DIR / "cycle.py"
DRAFTS = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "drafts.py"
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"
BLUEPRINT = REPO_ROOT / "BLUEPRINT.md"
SHA = "4c932af5" + "0" * 32
FRESH = "e91b9f13" + "1" * 32


def flat(text):
    """Whitespace collapsed, so a phrase matches across a line wrap (INV-346)."""
    return re.sub(r"\s+", " ", text)


def cycle(*args):
    return subprocess.run([sys.executable, str(CYCLE), *map(str, args)], capture_output=True, text=True)


def drafts(*args, stdin=None):
    return subprocess.run([sys.executable, str(DRAFTS), *map(str, args)], input=stdin,
                          capture_output=True, text=True)


def tree(root):
    return sorted(str(p.relative_to(root)) for p in Path(root).rglob("*"))


class RunCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rd = self.root / ".claude" / "release-cycle" / "runs" / "2026-10-14"

    def tearDown(self):
        self.tmp.cleanup()

    def ok(self, result):
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        return result.stdout

    def init(self, *extra, merge="yes"):
        args = ("--simulated", "yes", "--persona", "terse", "--module", "5") if not extra else extra
        return self.ok(cycle("init", self.rd, *args, "--merge", merge, "--threshold", "70%",
                             "--sha", SHA))

    def add(self, skill, title, *sites, kind="issue", after=None, after_struck=None, rd=None, sha=SHA):
        args = ["add", rd or self.rd, "--skill", skill, "--source", "%s step" % skill,
                "--kind", kind, "--body-file", "-", "--sha", sha]
        if kind == "issue":
            args += ["--title", title]
        if kind == "upstream":
            args += ["--category", "bug"]
        for site in sites:
            args += ["--site", site]
        if after:
            args += ["--after", after]
        if after_struck:
            args += ["--after-struck", after_struck]
        return self.ok(drafts(*args, stdin="Body of %s.\n" % title)).split()[0]

    def state(self):
        return json.loads((self.rd / "state.json").read_text(encoding="utf-8"))

    def manifest(self, sub=""):
        return json.loads((self.rd / sub / "drafts" / "manifest.json").read_text(encoding="utf-8"))

    def record(self, rid, sub=""):
        return next(r for r in self.manifest(sub)["records"] if r["id"] == rid)

    def to_checkpoint_a(self):
        """Three drafts, two of them one finding seen by two skills, and an upstream message."""
        self.init()
        self.a = self.add("feedback-to-issues", "Dup", "a.md:10", "b.md:2",
                          after='--disposition "Alpha={outcome}"')
        self.b = self.add("delegate-to-mcp-server", "Dup again", "b.md:2", "a.md:10",
                          after="--key k --issue {issue}", after_struck='--key k --reason "declined"')
        self.c = self.add("production-readiness-audit", "Near", "a.md:9-11")
        self.u = self.add("feedback-to-issues", "Up", kind="upstream")
        self.ok(cycle("mark", self.rd, "find-draft", "done"))
        return self.ok(cycle("merge-drafts", self.rd))


class Kickoff(RunCase):
    def test_init_records_the_answers_and_the_baseline(self):
        self.init(merge="no")
        state = self.state()
        self.assertEqual(SHA, state["baseline_sha"]["find"])
        self.assertEqual({"simulated": True, "persona": "terse", "module": "5", "merge": False,
                          "threshold": 0.7}, state["kickoff"])
        self.assertEqual("done", state["steps"]["kickoff"]["outcome"])

    def test_a_costly_choice_is_never_defaulted(self):
        """INV-333: a simulated walk with no persona or module is refused, not filled in."""
        for args in (("--simulated", "yes", "--persona", "terse"), ("--simulated", "yes", "--module", "5")):
            with self.subTest(args=args):
                result = cycle("init", self.rd, *args, "--merge", "yes", "--threshold", "0.7", "--sha", SHA)
                self.assertEqual(1, result.returncode)
                self.assertFalse((self.rd / "state.json").exists())
        for missing in ("--merge", "--threshold", "--simulated"):
            args = {"--simulated": "no", "--merge": "yes", "--threshold": "0.7"}
            args.pop(missing)
            flat_args = [x for kv in args.items() for x in kv]
            with self.subTest(missing=missing):
                self.assertNotEqual(0, cycle("init", self.rd, *flat_args, "--sha", SHA).returncode)

    def test_the_threshold_is_refine_s_range(self):
        for bad in ("0.5", "1.2", "40%"):
            with self.subTest(threshold=bad):
                result = cycle("init", self.rd, "--simulated", "no", "--merge", "yes",
                               "--threshold", bad, "--sha", SHA)
                self.assertEqual(1, result.returncode)

    def test_a_run_outside_the_gitignored_directory_is_refused(self):
        result = cycle("init", self.root / "elsewhere" / "2026-10-14", "--simulated", "no",
                       "--merge", "yes", "--threshold", "0.7", "--sha", SHA)
        self.assertEqual(1, result.returncode)
        self.assertIn(".claude/release-cycle/runs", result.stderr)

    def test_a_second_init_is_refused(self):
        self.init()
        result = cycle("init", self.rd, "--simulated", "no", "--merge", "yes", "--threshold", "0.7",
                       "--sha", SHA)
        self.assertEqual(3, result.returncode)

    def test_kickoff_shows_the_standing_threshold_and_the_last_walk(self):
        self.init()
        out = self.ok(cycle("kickoff", self.rd.parent))
        self.assertIn("standing refine threshold: 0.7", out)
        self.assertIn("run 2026-10-14: unfinished, next stage 1 Find, step find-draft", out)
        self.assertIn("persona terse, from module 5", out)


class Resume(RunCase):
    def test_next_names_the_first_unfinished_step(self):
        self.init()
        self.assertIn("NEXT stage 1 Find, step find-draft", self.ok(cycle("next", self.rd)))

    def test_a_finished_step_is_never_marked_again(self):
        self.init()
        self.add("dry-run", "X", "a.md:1", rd=self.rd)
        self.ok(cycle("mark", self.rd, "find-draft", "done"))
        result = cycle("mark", self.rd, "find-draft", "started")
        self.assertEqual(3, result.returncode)
        self.assertIn("never run again", result.stderr)

    def test_a_step_cannot_be_skipped(self):
        self.init()
        result = cycle("mark", self.rd, "refine", "done")
        self.assertEqual(3, result.returncode)
        self.assertIn("find-draft comes before refine", result.stderr)

    def test_a_stopped_step_is_where_the_run_resumes(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        self.ok(cycle("mark", self.rd, "find-file", "stopped", "--note", "maintainer away"))
        out = self.ok(cycle("next", self.rd))
        self.assertIn("NEXT stage 1 Find, step find-file", out)
        self.assertIn("maintainer away", out)

    def test_a_clean_draft_step_skips_its_build_pass(self):
        self.init()
        self.ok(cycle("mark", self.rd, "find-draft", "done"))
        state = self.state()
        self.assertEqual("clean", state["steps"]["find-draft"]["outcome"])
        for step in ("find-merge", "checkpoint-a", "find-file", "refine", "build-loop", "build-leftovers"):
            self.assertEqual("skipped", state["steps"][step]["outcome"])
        self.assertIn("step exercise-draft", self.ok(cycle("next", self.rd)))

    def test_a_step_its_command_owns_cannot_be_marked_done_by_hand(self):
        self.to_checkpoint_a()
        result = cycle("mark", self.rd, "checkpoint-a", "done")
        self.assertEqual(3, result.returncode)
        self.assertIn("verdicts", result.stderr)

    def test_the_fresh_baseline_is_required_for_stage_four(self):
        self.init()
        self.ok(cycle("mark", self.rd, "find-draft", "done"))
        self.assertEqual(1, cycle("mark", self.rd, "exercise-draft", "done").returncode)
        self.add("dry-run", "Walk", "m.md:3", rd=self.rd / "exercise", sha=FRESH)
        self.ok(cycle("mark", self.rd, "exercise-draft", "done", "--sha", FRESH))
        self.assertEqual(FRESH, self.state()["baseline_sha"]["exercise"])


class Merge(RunCase):
    def test_same_sites_merge_into_one_record_listing_every_source(self):
        out = self.to_checkpoint_a()
        items = [l for l in out.splitlines() if re.match(r"^\d+\. ", l)]
        self.assertEqual(2, len(items), out)
        self.assertIn(self.a, items[0])
        self.assertIn("found by /feedback-to-issues, /delegate-to-mcp-server", out)
        self.assertEqual({self.a: [self.b]}, self.state()["merges"]["find"])
        body = (self.rd / "drafts" / ("%s.md" % self.a)).read_text(encoding="utf-8")
        self.assertEqual(1, body.count("**Found by:**"))
        self.assertIn("`/delegate-to-mcp-server`", body)

    def test_the_list_has_no_duplicate_dedupe_key(self):
        self.to_checkpoint_a()
        keys = [tuple(self.record(s["id"])["dedupe_key"]) for s in self.state()["listings"]["find"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_overlapping_but_different_keys_are_shown_side_by_side(self):
        out = self.to_checkpoint_a()
        self.assertIn("OVERLAP %s and %s" % (self.a, self.c), out)
        self.assertIn("a.md:10 ~ a.md:9-11", out)

    def test_an_upstream_draft_is_not_on_the_list(self):
        out = self.to_checkpoint_a()
        self.assertIn("UPSTREAM %s [upstream-pending]: not on the list; the cycle never sends it" % self.u, out)

    def test_a_second_merge_merges_nothing_twice(self):
        self.to_checkpoint_a()
        draft = self.rd / "drafts" / ("%s.md" % self.a)
        before = (draft.read_text(encoding="utf-8"), self.state()["merges"], self.manifest())
        out = self.ok(cycle("merge-drafts", self.rd))
        self.assertNotIn("merged now", out)
        self.assertEqual(before, (draft.read_text(encoding="utf-8"), self.state()["merges"], self.manifest()))

    def test_same_skill_duplicates_merge_too(self):
        self.init()
        one = self.add("dry-run", "One", "x.md:1")
        two = self.add("dry-run", "Two", "x.md:1")
        self.ok(cycle("mark", self.rd, "find-draft", "done"))
        self.ok(cycle("merge-drafts", self.rd))
        self.assertEqual({one: [two]}, self.state()["merges"]["find"])


class CheckpointA(RunCase):
    def test_yes_except_strikes_the_numbered_items_and_their_riders(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "1"))
        self.assertEqual("struck", self.record(self.a)["status"])
        self.assertEqual("struck", self.record(self.b)["status"])
        self.assertEqual("approved", self.record(self.c)["status"])
        self.assertEqual("upstream-pending", self.record(self.u)["status"])

    def test_a_rider_waits_for_its_record(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        self.assertEqual("approved", self.record(self.a)["status"])
        self.assertEqual("pending", self.record(self.b)["status"])

    def test_a_draft_edited_after_it_was_shown_is_refused(self):
        self.to_checkpoint_a()
        path = self.rd / "drafts" / ("%s.md" % self.c)
        path.write_text(path.read_text(encoding="utf-8") + "Edited.\n", encoding="utf-8")
        result = cycle("verdicts", self.rd, "--strike", "none")
        self.assertEqual(3, result.returncode)
        self.assertIn(self.c, result.stderr)
        self.assertEqual("pending", self.record(self.a)["status"])

    def test_a_draft_added_after_the_list_was_shown_is_refused(self):
        self.to_checkpoint_a()
        late = self.add("retrofit-from-public", "Late", "z.md:4")
        result = cycle("verdicts", self.rd, "--strike", "none")
        self.assertEqual(3, result.returncode)
        self.assertIn(late, result.stderr)

    def test_a_number_not_on_the_list_is_refused(self):
        self.to_checkpoint_a()
        self.assertEqual(1, cycle("verdicts", self.rd, "--strike", "3").returncode)

    def test_the_checkpoint_is_answered_once(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        self.assertEqual(3, cycle("verdicts", self.rd, "--strike", "1").returncode)
        self.assertEqual("approved", self.record(self.a)["status"])


class Filing(RunCase):
    def file_first(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        out = self.ok(cycle("file-next", self.rd))
        self.assertIn("FILE /feedback-to-issues --file", out)
        self.ok(drafts("record-filed", self.rd, self.a, "601"))
        self.ok(cycle("filed", self.rd, "feedback-to-issues"))

    def test_a_rider_takes_its_record_s_number_and_is_never_filed(self):
        self.file_first()
        out = self.ok(cycle("file-next", self.rd))
        self.assertIn("FILE /delegate-to-mcp-server --file", out)
        rider = self.record(self.b)
        self.assertEqual(("filed", 601), (rider["status"], rider["issue"]))
        plan = self.ok(drafts("file-plan", self.rd, "--skill", "delegate-to-mcp-server", "--sha", SHA))
        self.assertNotIn("FILE ", plan)
        self.assertIn("SKIP %s: already filed as #601" % self.b, plan)
        after = self.ok(drafts("after", self.rd, "--skill", "delegate-to-mcp-server"))
        self.assertEqual(["--key k --issue 601"], after.splitlines())

    def test_filed_refuses_a_skill_with_records_still_unfiled(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        result = cycle("filed", self.rd, "feedback-to-issues")
        self.assertEqual(3, result.returncode)
        self.assertIn(self.a, result.stderr)

    def test_a_stopped_file_stage_searches_the_tracker_before_filing_again(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        first = self.ok(cycle("file-next", self.rd))
        self.assertNotIn("CHECK", first)
        again = self.ok(cycle("file-next", self.rd))
        self.assertIn("CHECK %s:" % self.a, again)
        self.assertIn("gh issue list --state all --search 'Dup in:title'", again)

    def test_a_finished_filing_is_never_run_again(self):
        self.file_first()
        self.ok(cycle("file-next", self.rd))
        self.ok(cycle("filed", self.rd, "delegate-to-mcp-server"))
        self.ok(drafts("record-filed", self.rd, self.c, "602"))
        out = self.ok(cycle("filed", self.rd, "production-readiness-audit"))
        self.assertIn("find-file done", out)
        self.assertEqual("filed #601, #602", self.state()["steps"]["find-file"]["note"])
        for args in (("file-next", self.rd), ("filed", self.rd, "feedback-to-issues"),
                     ("mark", self.rd, "find-file", "started"), ("merge-drafts", self.rd)):
            with self.subTest(args=args[0]):
                if args[0] == "merge-drafts":
                    self.assertNotIn("merged now", self.ok(cycle(*args)))
                else:
                    self.assertEqual(3, cycle(*args).returncode)
        self.assertIn("NEXT stage 2 Refine, step refine", self.ok(cycle("next", self.rd)))

    def test_redraft_is_refused_once_anything_is_filed(self):
        self.file_first()
        self.assertEqual(3, cycle("redraft", self.rd, "--sha", FRESH).returncode)

    def test_redraft_before_filing_sets_the_old_drafts_aside(self):
        self.to_checkpoint_a()
        self.ok(cycle("redraft", self.rd, "--sha", FRESH))
        self.assertTrue((self.rd / ("drafts.superseded-%s" % SHA[:12])).is_dir())
        self.assertEqual(FRESH, self.state()["baseline_sha"]["find"])
        self.assertIn("step find-draft", self.ok(cycle("next", self.rd)))


class HeldAfterFiling(RunCase):
    """The after-filing steps that write tracked files wait for stage 5 (the graft from race B).

    `/feedback-to-issues` Step 9 archives under `feedback/` and `/delegate-to-mcp-server` Step 9
    appends to `specs/mcp-coverage.jsonl`; run at checkpoint A, either would dirty the tree
    before stage 3's preflight and change `specs/` before it.
    """

    def file_all(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        self.outs = [self.ok(cycle("file-next", self.rd))]
        self.ok(drafts("record-filed", self.rd, self.a, "601"))
        self.ok(cycle("filed", self.rd, "feedback-to-issues"))
        self.outs.append(self.ok(cycle("file-next", self.rd)))
        self.ok(cycle("filed", self.rd, "delegate-to-mcp-server"))
        self.outs.append(self.ok(cycle("file-next", self.rd)))
        self.ok(drafts("record-filed", self.rd, self.c, "602"))
        self.ok(cycle("filed", self.rd, "production-readiness-audit"))

    def to_stage_five(self):
        self.file_all()
        self.to_stage_five_from_filed()

    def test_file_next_holds_the_steps_that_write_tracked_files(self):
        self.file_all()
        feedback, delegate, audit = self.outs
        self.assertIn("HOLD /feedback-to-issues's after-filing step (Step 9): file its records, then "
                      "stop before it", feedback)
        self.assertIn("HOLD /delegate-to-mcp-server's after-filing step (Step 9)", delegate)
        self.assertIn("FILE /production-readiness-audit --file", audit)
        self.assertNotIn("HOLD", audit)
        held = self.state()["held"]["find"]
        self.assertEqual({"feedback-to-issues", "delegate-to-mcp-server"}, set(held))
        self.assertTrue(all(not h.get("run") for h in held.values()))

    def test_a_held_step_is_not_emitted_before_stage_five(self):
        self.file_all()
        for step in STEP_ORDER[:STEP_ORDER.index("after-filing")]:
            with self.subTest(step=step):
                out = self.ok(cycle("args", self.rd, step))
                self.assertNotIn("drafts.py after", out)
                self.assertNotIn("after-filed", out)
        out = self.ok(cycle("next", self.rd))
        self.assertIn("NEXT stage 2 Refine", out)
        self.assertNotIn("drafts.py after", out)

    def test_it_is_emitted_at_stage_five_before_review_invariants(self):
        self.to_stage_five()
        out = self.ok(cycle("next", self.rd))
        self.assertIn("NEXT stage 5 Settle, step after-filing", out)
        for skill in ("feedback-to-issues", "delegate-to-mcp-server"):
            self.assertIn("RUN python3 .claude/skills/feedback-to-issues/drafts.py after %s --skill %s"
                          % (self.rd, skill), out)
            self.assertIn("THEN /%s's held after-filing step, Step 9" % skill, out)
            self.assertIn("after-filed %s %s" % (self.rd, skill), out)
        self.assertNotIn("--skill production-readiness-audit", out)
        self.assertLess(out.index("drafts.py after"), out.index("/review-invariants"))
        self.assertNotIn("INVOKE /review-invariants", out)

    def test_resume_never_repeats_a_held_step(self):
        self.to_stage_five()
        self.ok(cycle("after-filed", self.rd, "feedback-to-issues"))
        out = self.ok(cycle("next", self.rd))
        self.assertNotIn("--skill feedback-to-issues", out)
        self.assertIn("--skill delegate-to-mcp-server", out)
        again = cycle("after-filed", self.rd, "feedback-to-issues")
        self.assertEqual(3, again.returncode)
        self.assertIn("never run again", again.stderr)
        self.assertIn("after-filing done", self.ok(cycle("after-filed", self.rd, "delegate-to-mcp-server")))
        out = self.ok(cycle("next", self.rd))
        self.assertIn("NEXT stage 5 Settle, step checkpoint-d", out)
        self.assertIn("INVOKE /review-invariants", out)
        self.assertNotIn("drafts.py after", out)
        self.assertEqual(3, cycle("after-filed", self.rd, "delegate-to-mcp-server").returncode)

    def test_a_held_step_cannot_run_early_or_be_skipped(self):
        self.file_all()
        self.assertEqual(3, cycle("after-filed", self.rd, "feedback-to-issues").returncode)
        self.to_stage_five_from_filed()
        result = cycle("mark", self.rd, "after-filing", "done")
        self.assertEqual(3, result.returncode)
        self.assertIn("/feedback-to-issues (stage 1)", result.stderr)
        # `/dry-run` has no after-filing step to hold, so argparse refuses the name (exit 2).
        self.assertEqual(2, cycle("after-filed", self.rd, "dry-run").returncode)

    def to_stage_five_from_filed(self):
        for step in ("refine", "build-loop", "build-leftovers"):
            self.ok(cycle("mark", self.rd, step, "done"))
        self.ok(cycle("mark", self.rd, "exercise-draft", "done", "--sha", FRESH))

    def test_with_nothing_held_stage_five_skips_it(self):
        self.init()
        self.add("production-readiness-audit", "Only", "q.md:1")
        self.ok(cycle("mark", self.rd, "find-draft", "done"))
        self.ok(cycle("merge-drafts", self.rd))
        self.ok(cycle("verdicts", self.rd, "--strike", "none"))
        self.assertNotIn("HOLD", self.ok(cycle("file-next", self.rd)))
        self.assertEqual({}, self.state()["held"].get("find", {}))
        self.assertIn("SKIP: no after-filing step is held", self.ok(cycle("args", self.rd, "after-filing")))

    def test_a_stop_before_stage_five_lists_each_held_step_in_the_entry(self):
        self.file_all()
        self.ok(cycle("mark", self.rd, "refine", "stopped", "--note", "maintainer stopped"))
        entry = self.ok(cycle("ledger", self.rd))
        self.assertIn("- **After-filing steps held for stage 5, not yet run:** 2,", entry)
        self.assertIn("`/feedback-to-issues` (stage 1): Step 9", entry)
        self.assertIn('    > --disposition "Alpha=#601"', entry)
        self.assertIn("    > --key k --issue 601", entry)
        self.assertFalse(re.search(r"^## ", entry.partition("\n")[2], re.M))


STEP_ORDER = (
    "kickoff", "find-draft", "find-merge", "checkpoint-a", "find-file", "refine", "build-loop",
    "build-leftovers", "exercise-draft", "exercise-merge", "checkpoint-c", "exercise-file",
    "exercise-refine", "exercise-build-loop", "exercise-build-leftovers", "after-filing",
    "checkpoint-d", "blueprint", "release", "manual-test", "propagate",
)


class Steps(RunCase):
    def args(self, step, **kw):
        extra = []
        for k, v in kw.items():
            extra += ["--" + k, v]
        return self.ok(cycle("args", self.rd, step, *extra))

    def test_the_finding_skills_run_with_draft_in_subagents(self):
        self.init()
        out = self.args("find-draft")
        for skill in ("feedback-to-issues", "retrofit-from-public", "delegate-to-mcp-server",
                      "production-readiness-audit"):
            self.assertIn("SUBAGENT /%s --draft %s" % (skill, self.rd), out)

    def test_dry_run_takes_the_kickoff_answers(self):
        self.init()
        self.assertIn("SUBAGENT /dry-run all 5 --simulated terse --draft %s" % (self.rd / "exercise"),
                      self.args("exercise-draft"))

    def test_the_three_slash_only_skills_are_followed_not_invoked(self):
        self.init()
        for step, name in (("refine", "refine-github-issue"), ("build-loop", "unattended-issue-loop"),
                           ("build-leftovers", "implement-github-issue")):
            with self.subTest(step=step):
                out = self.args(step)
                self.assertIn("FOLLOW ~/.claude/skills/%s/SKILL.md in this session" % name, out)
                self.assertNotIn("INVOKE", out)
        self.assertIn("--batch --threshold 0.7", self.args("refine"))

    def test_the_loop_merges_only_when_the_kickoff_says_so(self):
        self.init(merge="yes")
        self.assertIn("as /unattended-issue-loop with no argument", self.args("build-loop"))
        other = self.rd.parent / "2026-10-15"
        self.ok(cycle("init", other, "--simulated", "no", "--merge", "no", "--threshold", "0.7",
                      "--sha", SHA))
        self.assertIn("as /unattended-issue-loop --no-merge", self.ok(cycle("args", other, "build-loop")))

    def test_no_step_runs_a_forbidden_act(self):
        """The guardrails, as what the helper prints: no label, no send, no push, no bump."""
        self.init(merge="no")
        forbidden = re.compile(r"unattended-ok|--add-label|submit_feedback|git push|git commit"
                               r"|--major|--minor|--patch")
        for step in STEP_ORDER:
            if step == "blueprint":
                continue
            with self.subTest(step=step):
                self.assertEqual([], forbidden.findall(self.args(step)))
        self.assertIn("no argument: it asks the maintainer for the bump", self.args("release"))

    def test_blueprint_runs_only_when_its_header_is_behind_main(self):
        self.init()
        bp = self.root / "BLUEPRINT.md"
        bp.write_text("# Blueprint\n<!-- blueprint: sha=%s date=2026-10-04 -->\n" % SHA[:12], encoding="utf-8")
        self.assertIn("SKIP", self.args("blueprint", head=SHA, blueprint=str(bp)))
        self.assertIn("INVOKE update-blueprint", self.args("blueprint", head=FRESH, blueprint=str(bp)))

    def test_stage_four_refines_only_what_it_filed(self):
        self.init()
        self.assertIn("SKIP: stage 4 filed nothing", self.args("exercise-refine"))


class Ledger(RunCase):
    LEDGER = "# Implemented\n\n<!--\nformat\n-->\n\n## older-entry\n\n- **Commit:** abc1234\n"

    def stopped_run(self):
        self.to_checkpoint_a()
        self.ok(cycle("verdicts", self.rd, "--strike", "2"))
        self.ok(cycle("mark", self.rd, "find-file", "stopped", "--note", "maintainer stopped"))

    def test_the_entry_records_every_step_and_every_unresolved_draft(self):
        self.stopped_run()
        entry = self.ok(cycle("ledger", self.rd))
        self.assertTrue(entry.startswith("## release-cycle-2026-10-14\n"))
        for step in ("kickoff", "find-draft", "checkpoint-a [A]", "find-file", "refine [B]",
                     "checkpoint-d [D]", "propagate [E]"):
            self.assertIn(step + ":", entry)
        self.assertIn("find-file: stopped (maintainer stopped)", entry)
        self.assertIn("`%s` (issue" % self.a, entry)
        self.assertIn("approved, **not filed**", entry)
        self.assertIn("rides on %s; **not filed**" % self.a, entry)
        self.assertIn("`%s` (upstream" % self.u, entry)
        self.assertIn("**not sent** — needs maintainer approval", entry)
        self.assertIn("    > Body of Dup.", entry)
        self.assertIn("**Struck at the checkpoint:** `%s`" % self.c, entry)

    def test_the_entry_passes_the_ledger_s_own_checks(self):
        self.stopped_run()
        entry = self.ok(cycle("ledger", self.rd))
        body = entry.partition("\n")[2]
        self.assertFalse(re.search(r"^## ", body, re.M), "a draft body must not open a new entry")
        self.assertTrue(ledger_checks.COMMIT_FIELD.search(body))
        self.assertEqual("uncommitted", ledger_checks.COMMIT_FIELD.search(body).group(1).strip())
        self.assertTrue(any(ledger_checks.flatten(p) in ledger_checks.flatten(body)
                            for p in ledger_checks.NO_INVARIANT_PHRASES))
        self.assertRegex(body, r"\*\*Implemented:\*\*\s*2026-\d\d-\d\d")

    def test_it_is_written_once_below_the_format_comment_and_replaced_in_place(self):
        self.stopped_run()
        path = self.root / "IMPLEMENTED.md"
        path.write_text(self.LEDGER, encoding="utf-8")
        self.ok(cycle("ledger", self.rd, "--write", path))
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Implemented\n\n<!--\nformat\n-->\n\n## release-cycle-2026-10-14\n"))
        self.ok(cycle("ledger", self.rd, "--write", path))
        again = path.read_text(encoding="utf-8")
        self.assertEqual(1, again.count("## release-cycle-2026-10-14"))
        self.assertEqual(text, again)
        self.assertTrue(again.endswith("## older-entry\n\n- **Commit:** abc1234\n"))

    def test_a_resumed_run_withdraws_the_entry_and_the_tree_is_as_before(self):
        self.stopped_run()
        path = self.root / "IMPLEMENTED.md"
        path.write_text(self.LEDGER, encoding="utf-8")
        self.ok(cycle("ledger", self.rd, "--write", path))
        self.assertIn("WITHDRAW", self.ok(cycle("next", self.rd)))
        self.ok(cycle("ledger", self.rd, "--withdraw", path))
        self.assertEqual(self.LEDGER, path.read_text(encoding="utf-8"))
        self.assertNotIn("WITHDRAW", self.ok(cycle("next", self.rd)))

    def test_an_edited_entry_is_never_withdrawn(self):
        self.stopped_run()
        path = self.root / "IMPLEMENTED.md"
        path.write_text(self.LEDGER, encoding="utf-8")
        self.ok(cycle("ledger", self.rd, "--write", path))
        path.write_text(path.read_text(encoding="utf-8").replace("maintainer stopped", "edited"),
                        encoding="utf-8")
        self.assertEqual(3, cycle("ledger", self.rd, "--withdraw", path).returncode)
        self.assertIn("edited", path.read_text(encoding="utf-8"))

    def test_nothing_is_written_outside_the_run_directory_until_the_ledger(self):
        before = tree(self.root)
        self.stopped_run()
        self.ok(cycle("next", self.rd))
        self.ok(cycle("ledger", self.rd))
        outside = [p for p in tree(self.root) if p not in before and not p.startswith(".claude")]
        self.assertEqual([], outside)


class TheHelperReadsTheManifestThroughDrafts(unittest.TestCase):
    """INV-300: `drafts.py` is the one statement of the manifest; this helper parses none of it."""

    def test_it_loads_drafts_py_and_names_no_manifest_file(self):
        source = CYCLE.read_text(encoding="utf-8")
        code = source.split('"""', 2)[2]
        self.assertIn('"feedback-to-issues" / "drafts.py"', code)
        self.assertNotIn("manifest.json", code)
        self.assertNotIn("manifest.lock", code)
        for call in ("drafts.load(", "drafts.open_records(", "drafts.split_draft(", "drafts.render("):
            self.assertIn(call, code)


def skill_text():
    return flat(SKILL.read_text(encoding="utf-8"))


#: What the skill must state: each checkpoint, how it runs each skill, and each guardrail.
STATED = (
    "| 0 Kickoff |", "**A**: approve the drafts as one list", "**B**: the pooled questions",
    "**C**: approve the drafts as one list", "**D**: the invariant verdicts",
    "**E**: the version bump, the manual test, and the public repo's commit and push",
    "`--draft <run-dir>`", "`--file <run-dir>`",
    "`/dry-run all <module> --simulated <persona> --draft <exercise-dir>`",
    "This skill reads and follows each one's `~/.claude/skills/<name>/SKILL.md` in the main session",
    "The maintainer's `/release-cycle` invocation is the explicit invocation each of them requires",
    "every gate inside each of them still applies",
    "A subagent never asks the maintainer anything.",
    "It never signs off an invariant: the verdicts are the maintainer's, at checkpoint D (INV-365).",
    "It never chooses the version bump: `/release` asks (INV-333).",
    "It never commits or pushes the public repo: `/propagate-to-public` stops at its working tree, and the maintainer commits and pushes it.",
    "It never sends `submit_feedback`.",
    "It never applies `unattended-ok` outside refine's approved batch (INV-318, 2026-10-13 note).",
    "It never merges unless the kickoff answer says to",
    "Each record it creates is created by the skill that owns it, under that skill's gate (INV-314).",
    "⛔ **A finished step is never run again, and a record that carries an issue number is never "
    "filed again.**",
    "⛔ **This skill writes nothing under `specs/` before stage 5 (the held after-filing steps and "
    "checkpoint D), and its own entry only at a stop.**",
    "⛔ **Hold each skill's after-filing step until stage 5.**",
    "`cycle.py after-filed <run-dir> <skill>`, which refuses a step already run",
    "`cycle.py ledger <run-dir> --write specs/IMPLEMENTED.md`",
    "marked **not filed** (INV-317's 2026-10-13 note)",
    "left uncommitted for the maintainer (INV-310)",
    "One yes covers only the records in that message (INV-314, 2026-10-13 note).",
    "⛔ **(INV-300) Each skill's own file governs it, and this one restates none of their rules.**",
    "never start or resume costly work from silence (INV-333)",
)


def unstated(text):
    return [p for p in STATED if p not in text]


class TheSkillStatesItsRules(unittest.TestCase):
    def test_every_checkpoint_and_guardrail_is_stated(self):
        self.assertEqual([], unstated(skill_text()))

    def test_it_is_slash_only(self):
        head = SKILL.read_text(encoding="utf-8").split("---", 2)[1]
        self.assertIn("disable-model-invocation: true", head)
        self.assertRegex(head, r"(?m)^argument-hint: \".+\"$")

    def test_it_invokes_none_of_the_three_slash_only_skills(self):
        """They are followed from their files; `/<name>` in the skill would read as invoking one."""
        text = SKILL.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?i)invoke[sd]?\s+`?/?(?:refine-github-issue|unattended-issue-loop"
                                  r"|implement-github-issue)")
        self.assertNotIn("/refine-github-issue", re.sub(r"skills/refine-github-issue/", "", text))

    def test_its_links_resolve(self):
        text = SKILL.read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)#]+)\)", text)
        self.assertTrue(links)
        for link in links:
            with self.subTest(link=link):
                self.assertTrue((SKILL_DIR / link).resolve().exists(), link)
        self.assertIn("(cycle.py)", text)
        self.assertIn("(../feedback-to-issues/drafts.py)", text)

    def test_it_restates_no_part_of_the_manifest_format(self):
        restated = re.compile(r"manifest\.json|upstream-pending|\bstatus `?(?:approved|struck)|dedupe_key")
        self.assertEqual([], restated.findall(SKILL.read_text(encoding="utf-8")))


#: The one statement of where a run writes (#609), in "Stopping, and the ledger entry".
BOUNDARY = ("⛔ **This skill writes nothing under `specs/` before stage 5 (the held after-filing "
            "steps and checkpoint D), and its own entry only at a stop.**")
#: The rule's words, shared by the statement and the pending block's drafted wording.
BOUNDARY_RULE = ("nothing under `specs/` before stage 5 (the held after-filing steps and "
                 "checkpoint D), and its own entry only at a stop")
#: Each write the statement must name, so a later edit cannot drop one silently.
NAMED_WRITES = (
    "the gitignored run directory", "`/dry-run`'s disposable scratch project",
    "A simulated walk's sandbox is that scratch project, removed when the walk ends",
    "its own ledger entry among them, are on its issue branch", "the held after-filing steps",
    "`specs/mcp-coverage.jsonl`", "checkpoint D's `/review-invariants`, which edits "
    "`specs/INVARIANTS.md` and the ledger", "**At a stop**, this skill writes its one entry",
)
#: The rule #609 retired, in any of the forms it shipped in (#573).
CONTRADICTS = re.compile(r"(?i)nothing under `specs/` (?:changes )?(?:until|before) (?:the run|it) "
                         r"stops|nothing tracked changes while the run")
LEDGER = REPO_ROOT / "specs" / "IMPLEMENTED.md"
PENDING = "## release-cycle-runs-the-cycle-with-five-checkpoints"


def boundary_section():
    text = SKILL.read_text(encoding="utf-8")
    start = text.index("## Stopping, and the ledger entry")
    return flat(text[start:text.index("When the run stops", start)])


def pending_entry():
    text = LEDGER.read_text(encoding="utf-8")
    start = text.index(PENDING)
    return flat(text[start:text.index("\n## ", start + len(PENDING))])


def boundary_sites():
    """Every site that says where a run writes."""
    return {"SKILL.md": skill_text(), "cycle.py": flat(CYCLE.read_text(encoding="utf-8")),
            "drafts.py": flat(DRAFTS.read_text(encoding="utf-8")),
            "FAMILY_WORKFLOW.md": flat(FAMILY.read_text(encoding="utf-8")),
            "BLUEPRINT.md": flat(BLUEPRINT.read_text(encoding="utf-8")),
            "the pending block": pending_entry()}


def unnamed(section):
    return [w for w in NAMED_WRITES if w not in section]


class TheWriteBoundaryIsStatedOnce(unittest.TestCase):
    """#609: stage 5 writes under `specs/` before the stop, so the rule says so, once (INV-300).

    The statement lives in `SKILL.md`'s "Stopping, and the ledger entry"; `cycle.py`'s docstring
    cites it, and the pending `DEFERRED INVARIANT` block quotes it and drafts the same rule, so
    `/review-invariants` registers what the skill states. No site may keep the retired wording.
    """

    def test_the_skill_states_it_once_and_names_every_write(self):
        self.assertEqual(1, skill_text().count(BOUNDARY))
        self.assertTrue(boundary_section().startswith("## Stopping, and the ledger entry " + BOUNDARY))
        self.assertEqual([], unnamed(boundary_section()))

    def test_no_site_contradicts_it(self):
        for name, text in boundary_sites().items():
            with self.subTest(site=name):
                self.assertEqual([], CONTRADICTS.findall(text))

    def test_no_other_site_restates_it(self):
        for name, text in boundary_sites().items():
            if name not in ("SKILL.md", "the pending block"):
                with self.subTest(site=name):
                    self.assertNotIn(BOUNDARY_RULE, text)

    def test_cycle_py_cites_it(self):
        self.assertIn('stated once, in `SKILL.md` ("Stopping, and the ledger entry"), and this helper '
                      "restates none of it (INV-300)", flat(CYCLE.read_text(encoding="utf-8")))

    def test_the_pending_block_quotes_it_and_drafts_the_same_rule(self):
        entry = pending_entry()
        self.assertIn(BOUNDARY + " — in `.claude/skills/release-cycle/SKILL.md` (\"Stopping, and the "
                      "ledger entry\")", entry)
        drafted = entry[entry.index("**INV-NNN** — `/release-cycle`"):]
        self.assertIn("It MUST write " + BOUNDARY_RULE, drafted)
        self.assertIn("Dated note, 2026-10-14 (#609)", entry)


class NegativeControls(unittest.TestCase):
    def test_the_retired_rule_or_a_dropped_write_is_reported(self):
        """#609's controls: each form of the old line is caught, and so is a dropped write."""
        for old in ("⛔ **Nothing under `specs/` changes until the run stops.**",
                    "It MUST write nothing under `specs/` before it stops, holding",
                    "gitignored, so nothing tracked changes while the run is in progress"):
            with self.subTest(old=old):
                self.assertTrue(CONTRADICTS.findall(old))
        section = boundary_section()
        for write in NAMED_WRITES:
            with self.subTest(write=write):
                self.assertIn(write, unnamed(section.replace(write, "")))
        self.assertIn(BOUNDARY, unstated(skill_text().replace(BOUNDARY, "⛔ **Nothing under `specs/` "
                                                                       "changes until the run stops.**")))

    def test_dropping_a_guardrail_or_a_checkpoint_is_reported(self):
        text = skill_text()
        for phrase in ("It never sends `submit_feedback`.", "**D**: the invariant verdicts",
                       "It never merges unless the kickoff answer says to",
                       "⛔ **Hold each skill's after-filing step until stage 5.**"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, unstated(text.replace(phrase, "")))

    def test_an_invoked_slash_only_skill_is_caught(self):
        self.assertRegex("Invoke `/unattended-issue-loop`.",
                         r"(?i)invoke[sd]?\s+`?/?(?:refine-github-issue|unattended-issue-loop"
                         r"|implement-github-issue)")


class TheRegisterListsIt(unittest.TestCase):
    def test_section_2_has_its_row(self):
        text = FAMILY.read_text(encoding="utf-8")
        section = text[text.index("## 2. Canonical operations"):text.index("## 3. The per-change flow")]
        row = re.search(r"^\| `release-cycle` \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", section, re.M)
        self.assertIsNotNone(row)
        self.assertEqual(("drives 1–4", "required", "*not mandated*"),
                         tuple(c.strip() for c in row.groups()))

    def test_section_3_names_it(self):
        text = FAMILY.read_text(encoding="utf-8")
        section = text[text.index("## 3. The per-change flow"):text.index("### Maintenance")]
        self.assertIn("<b>release-cycle</b>", section)
        self.assertIn("`release-cycle` runs the four phases", section)


if __name__ == "__main__":
    unittest.main()
