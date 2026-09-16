"""Feedback must not be triaged twice, and the overlap case must not be mishandled.

Feedback files arrive from multiple bootcampers at multiple times, and the working copy
at the repo root is gitignored, so the same content reaches `feedback-to-issues` more than
once — which has produced duplicate specs. The realistic collision is not the identical
file twice but a file that *overlaps* a previous one: a bootcamper's project accumulates
entries during a run, so a later copy carries the earlier entries plus new ones.

`.claude/skills/feedback-to-issues/feedback_ledger.py` therefore makes identity per
**entry**, content-addressed on normalized text, and records each processed entry in
`feedback/PROCESSED.jsonl`. These tests pin the three verdicts, the normalization that
makes a Windows re-save recognizable, and the two bugs found while exercising it:

* `--disposition` split on the FIRST `=`, so a title containing `topic='configure'` lost
  its disposition silently;
* a disposition recorded as `unrecorded` had no correction path that respected
  append-only, hence `annotate` plus last-wins reads.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "feedback_ledger.py"

HEADER = "# Senzing Bootcamp Plugin Feedback\n\n**Started:** 2026-07-28\n\n## Your Feedback\n\n"
ALPHA = "## Improvement: Alpha defect\n\n**Source:** bootcamper-reported\n\nAlpha happened.\n\n"
BRAVO = "## Improvement: Bravo defect\n\n**Source:** self-observed\n\nBravo was silent.\n\n"
# A title containing "=" — the shape that broke --disposition parsing.
EQUALS = (
    "## Improvement: sdk_guide(topic='configure') fails on a fresh datastore\n\n"
    "**Source:** self-observed\n\nThe snippet presupposes a registered config.\n\n"
)


def load():
    spec = importlib.util.spec_from_file_location("feedback_ledger_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["feedback_ledger_under_test"] = module
    spec.loader.exec_module(module)
    return module


LEDGER = load()


def run(repo, *args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), *args],
        capture_output=True, text=True, cwd=str(repo),
    )
    return proc.returncode, proc.stdout, proc.stderr


def project(contents):
    root = Path(tempfile.mkdtemp())
    (root / "candidate.md").write_text(contents, encoding="utf-8")
    return root


class NormalizationSurvivesATrivialResave(unittest.TestCase):
    """A Windows re-save changes bytes without changing content."""

    def test_bom_crlf_and_trailing_space_do_not_change_the_id(self):
        plain = ALPHA
        resaved = "﻿" + ALPHA.replace("\n", "\r\n").replace("happened.", "happened.   ")
        self.assertEqual(LEDGER.entry_id(plain), LEDGER.entry_id(resaved))

    def test_collapsed_blank_runs_do_not_change_the_id(self):
        self.assertEqual(
            LEDGER.entry_id(ALPHA), LEDGER.entry_id(ALPHA.replace("\n\n", "\n\n\n\n"))
        )

    def test_a_reworded_entry_is_a_different_entry(self):
        """Deliberate: a revised report deserves a fresh look."""
        self.assertNotEqual(
            LEDGER.entry_id(ALPHA), LEDGER.entry_id(ALPHA.replace("Alpha happened.", "Alpha happened twice."))
        )

    def test_scaffold_and_empty_headings_are_not_entries(self):
        entries = LEDGER.split_entries(HEADER + ALPHA)
        self.assertEqual(["Improvement: Alpha defect"], [t for t, _ in entries])


class TheThreeVerdicts(unittest.TestCase):
    def test_a_fresh_file_is_new(self):
        root = project(HEADER + ALPHA + BRAVO)
        code, _out, err = run(root, "check", "candidate.md")
        self.assertEqual(0, code)
        self.assertIn("VERDICT: NEW", err)

    def test_an_overlapping_file_is_partial_and_names_the_counts(self):
        """The case whole-file comparison gets wrong in both directions."""
        root = project(HEADER + ALPHA + BRAVO)
        run(root, "commit", "candidate.md", "--disposition", "Improvement: Alpha defect=specs/a.md",
            "--disposition", "Improvement: Bravo defect=specs/b.md")
        (root / "candidate.md").write_text(HEADER + ALPHA + BRAVO + EQUALS, encoding="utf-8")
        code, _out, err = run(root, "check", "candidate.md")
        self.assertEqual(0, code, err)
        self.assertIn("VERDICT: PARTIAL", err)
        self.assertIn("1 new", err)
        self.assertIn("2 already processed", err)

    def test_a_fully_seen_file_is_a_duplicate(self):
        root = project(HEADER + ALPHA + BRAVO)
        run(root, "commit", "candidate.md", "--disposition", "Improvement: Alpha defect=specs/a.md",
            "--disposition", "Improvement: Bravo defect=specs/b.md")
        (root / "candidate.md").write_text(HEADER + ALPHA + BRAVO, encoding="utf-8")
        code, _out, err = run(root, "check", "candidate.md")
        self.assertEqual(3, code)
        self.assertIn("VERDICT: DUPLICATE", err)

    def test_check_writes_nothing(self):
        root = project(HEADER + ALPHA)
        run(root, "check", "candidate.md")
        self.assertTrue((root / "candidate.md").is_file())
        self.assertFalse((root / "feedback").exists())

    def test_a_file_with_no_entries_is_refused(self):
        root = project(HEADER)
        code, _out, err = run(root, "check", "candidate.md")
        self.assertEqual(1, code)
        self.assertIn("no feedback entries", err)


class CommitArchivesAndRecords(unittest.TestCase):
    def test_the_file_moves_into_the_archive_with_a_unixtime_name(self):
        root = project(HEADER + ALPHA)
        code, out, _err = run(root, "commit", "candidate.md",
                              "--disposition", "Improvement: Alpha defect=specs/a.md")
        self.assertEqual(0, code)
        self.assertFalse((root / "candidate.md").exists())
        archives = list((root / "feedback").glob("SENZING_BOOTCAMP_PLUGIN_FEEDBACK_*.md"))
        self.assertEqual(1, len(archives), out)
        self.assertRegex(archives[0].name, r"SENZING_BOOTCAMP_PLUGIN_FEEDBACK_\d+\.md")

    def test_one_ledger_line_per_new_entry_with_its_disposition(self):
        root = project(HEADER + ALPHA + BRAVO)
        run(root, "commit", "candidate.md",
            "--disposition", "Improvement: Alpha defect=specs/a.md",
            "--disposition", "Improvement: Bravo defect=needs-clarification")
        records = LEDGER.read_ledger(root)
        self.assertEqual(2, len(records))
        by_title = {r["title"]: r["disposition"] for r in records.values()}
        self.assertEqual("specs/a.md", by_title["Improvement: Alpha defect"])
        self.assertEqual("needs-clarification", by_title["Improvement: Bravo defect"])

    def test_a_title_containing_equals_still_gets_its_disposition(self):
        """The bug: partition('=') truncated the key at topic='configure'."""
        root = project(HEADER + EQUALS)
        title = "Improvement: sdk_guide(topic='configure') fails on a fresh datastore"
        run(root, "commit", "candidate.md", "--disposition", f"{title}=specs/seed.md")
        dispositions = [r["disposition"] for r in LEDGER.read_ledger(root).values()]
        self.assertEqual(["specs/seed.md"], dispositions)

    def test_an_entry_id_may_be_used_as_the_disposition_key(self):
        root = project(HEADER + EQUALS)
        eid = LEDGER.entry_id(LEDGER.split_entries(HEADER + EQUALS)[0][1])
        run(root, "commit", "candidate.md", "--disposition", f"{eid}=specs/by-id.md")
        dispositions = [r["disposition"] for r in LEDGER.read_ledger(root).values()]
        self.assertEqual(["specs/by-id.md"], dispositions)

    def test_a_missing_disposition_is_recorded_and_warned_about(self):
        root = project(HEADER + ALPHA)
        _code, _out, err = run(root, "commit", "candidate.md")
        self.assertIn("unrecorded", err)
        self.assertEqual(
            ["unrecorded"], [r["disposition"] for r in LEDGER.read_ledger(root).values()]
        )

    def test_a_known_entry_is_not_recorded_twice(self):
        root = project(HEADER + ALPHA)
        run(root, "commit", "candidate.md", "--disposition", "Improvement: Alpha defect=specs/a.md")
        (root / "candidate.md").write_text(HEADER + ALPHA + BRAVO, encoding="utf-8")
        run(root, "commit", "candidate.md", "--disposition", "Improvement: Bravo defect=specs/b.md")
        lines = (root / "feedback" / "PROCESSED.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(2, len(lines), "Alpha must not be re-recorded")


class DuplicateCommitRenamesInPlace(unittest.TestCase):
    def setUp(self):
        self.root = project(HEADER + ALPHA)
        run(self.root, "commit", "candidate.md",
            "--disposition", "Improvement: Alpha defect=specs/a.md")
        self.stamp = next(iter(LEDGER.read_ledger(self.root).values()))["archive_unixtime"]
        (self.root / "candidate.md").write_text(HEADER + ALPHA, encoding="utf-8")

    def test_it_renames_to_the_duplicated_archives_unixtime(self):
        code, out, _err = run(self.root, "commit", "candidate.md")
        self.assertEqual(3, code)
        target = self.root / f"SENZING_BOOTCAMP_PLUGIN_FEEDBACK_{self.stamp}_DUPLICATE.md"
        self.assertTrue(target.is_file(), out)

    def test_it_leaves_the_ledger_untouched(self):
        before = (self.root / "feedback" / "PROCESSED.jsonl").read_text(encoding="utf-8")
        run(self.root, "commit", "candidate.md")
        after = (self.root / "feedback" / "PROCESSED.jsonl").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_it_does_not_move_the_duplicate_into_the_archive(self):
        run(self.root, "commit", "candidate.md")
        archives = list((self.root / "feedback").glob("*.md"))
        self.assertEqual(1, len(archives), "a duplicate must not be archived")


class AnnotateCorrectsWithoutRewriting(unittest.TestCase):
    """Append-only, read last-wins: a correction is a new line, not an edit."""

    def test_it_supersedes_an_unrecorded_disposition(self):
        root = project(HEADER + ALPHA)
        run(root, "commit", "candidate.md")
        eid = next(iter(LEDGER.read_ledger(root)))
        code, _out, _err = run(root, "annotate", eid, "specs/late.md")
        self.assertEqual(0, code)
        self.assertEqual("specs/late.md", LEDGER.read_ledger(root)[eid]["disposition"])

    def test_the_original_line_is_still_present(self):
        root = project(HEADER + ALPHA)
        run(root, "commit", "candidate.md")
        eid = next(iter(LEDGER.read_ledger(root)))
        run(root, "annotate", eid, "specs/late.md")
        lines = (root / "feedback" / "PROCESSED.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(2, len(lines), "history is appended to, never rewritten")
        self.assertEqual("unrecorded", json.loads(lines[0])["disposition"])

    def test_an_unknown_entry_id_is_refused(self):
        root = project(HEADER + ALPHA)
        run(root, "commit", "candidate.md")
        code, _out, err = run(root, "annotate", "0000000000000000", "specs/x.md")
        self.assertEqual(1, code)
        self.assertIn("No ledger record", err)


class TheLedgerReadIsResilient(unittest.TestCase):
    def test_a_malformed_line_does_not_hide_the_rest(self):
        root = project(HEADER + ALPHA)
        run(root, "commit", "candidate.md", "--disposition", "Improvement: Alpha defect=specs/a.md")
        ledger = root / "feedback" / "PROCESSED.jsonl"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write("{ this is not json\n")
        self.assertEqual(1, len(LEDGER.read_ledger(root)))

    def test_an_absent_ledger_reads_as_empty(self):
        self.assertEqual({}, LEDGER.read_ledger(Path(tempfile.mkdtemp())))


class TheArchiveIsNeverPropagated(unittest.TestCase):
    """It carries raw bootcamper text; the public mirror must never see it."""

    def test_the_propagate_manifest_excludes_it(self):
        manifest = (REPO_ROOT / ".claude" / "skills" / "propagate-to-public" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`feedback/**`", manifest)

    def test_the_propagate_script_copies_only_allowlisted_paths(self):
        """The archive must not be an rsync source — which is a claim about CODE.

        This asserted the bare substring against the whole file until 2026-08-16, when
        `cc0a7b0` added a comment naming `/feedback-to-issues` among the maintainer-only
        skills `docs/development.md` indexes. That comment copies nothing, and the guard
        failed on it — a proxy firing on prose. Comment lines are stripped first so the
        assertion tests what it means; any operative mention still fails it.
        """
        script = (REPO_ROOT / ".claude" / "skills" / "propagate-to-public" / "propagate.sh").read_text(
            encoding="utf-8"
        )
        code = "\n".join(
            line for line in script.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertNotIn("feedback", code)


if __name__ == "__main__":
    unittest.main()
