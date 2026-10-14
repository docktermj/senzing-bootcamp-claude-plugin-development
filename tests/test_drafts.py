"""The five finding skills run in two stages through one helper, `drafts.py` (#572).

`/feedback-to-issues`, `/retrofit-from-public`, `/delegate-to-mcp-server`,
`/production-readiness-audit` and `/dry-run` each found and filed in one session, so no caller
could collect their findings, merge duplicates and approve them at one checkpoint. Each now takes
`--draft <run-dir>` (find and draft, file nothing) and `--file <run-dir>` (file the approved
drafts and finish the after-filing records). The contract and the manifest format are stated
once, in `.claude/skills/feedback-to-issues/drafts.py`'s docstring (INV-300), and the helper does
the manifest work so no skill does it in prose.

What this pins, each with a negative control where it is a predicate over text:

1. **The helper, offline**: append (ids, the draft file's header, the sorted dedupe key), status
   changes, the issue number written back, the baseline-SHA refusal naming both SHAs, the
   idempotent re-run (a filed record is skipped, never filed twice), the after-filing lines with
   the numbers filled in and a struck record read as declined by the maintainer, the refusal of
   `unattended-ok` (INV-318), no `--repo` in any printed command (INV-319), the hand-run warning
   and `--file` command, and that a whole cycle writes nothing outside `<run-dir>`.
2. **The five skills**: each documents both arguments, cites `drafts.py`, states the stage-one
   rule (files nothing, fixes nothing, sends nothing, writes nothing outside `<run-dir>`), says
   `--draft` is the release cycle's interface (#573) and the caller records unresolved drafts (INV-317),
   ends a draft run with `drafts.py list`, and restates no part of the manifest format (INV-300).
   Its `--file` stage takes a yes for each record or INV-314's batch clause, and the three skills
   that draft upstream messages say `--file` never sends one, which keeps its own yes (#573
   retired #572's "get a yes for each first", written before INV-314's 2026-10-13 note).
3. **`.gitignore`** ignores `.claude/release-cycle/runs/`.

⚠️ **What this does NOT establish:** that a live run stops at its filing step, files only after a
yes, or leaves its ledgers untouched. Those are properties of a session; this pins that the
helper behaves and that the instructions a runner reads say so.

This module enforces INV-368 (registered 2026-10-13). It pins that the helper behaves and that
each skill states the rule; it cannot establish that a live run stops at its filing step or
leaves its ledgers untouched. It also enforces INV-317's 2026-10-13 (#572) note, by pinning the
citation in each skill and the helper's not-yet-durable warning; it cannot establish that a
caller records the drafts.

Stdlib only; no network, no `gh`, no git write (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
SCRIPT = SKILLS_DIR / "feedback-to-issues" / "drafts.py"
SKILLS = ("feedback-to-issues", "retrofit-from-public", "delegate-to-mcp-server",
          "production-readiness-audit", "dry-run")
SHA = "4c932af5" + "0" * 32
OTHER = "e91b9f13" + "1" * 32


def run(*args, stdin=None, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True,
                          text=True, cwd=cwd)


def flat(text):
    """Whitespace collapsed, so a phrase matches across a line wrap (INV-346)."""
    return re.sub(r"\s+", " ", text)


def manifest(run_dir):
    return json.loads((Path(run_dir) / "drafts" / "manifest.json").read_text(encoding="utf-8"))


def tree(root):
    return sorted(str(p.relative_to(root)) for p in Path(root).rglob("*"))


class HelperCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rd = str(self.root / "run")

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, *args, body="The exact body.\n", sha=SHA):
        return run("add", self.rd, *args, "--sha", sha, stdin=body, cwd=self.tmp.name)

    def ok(self, result):
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout


class Append(HelperCase):
    def test_add_numbers_per_skill_and_writes_the_draft(self):
        self.ok(self.add("--skill", "dry-run", "--source", "dry-run phase 2", "--title", "A defect",
                         "--label", "bug", "--body-file", "-",
                         "--site", "b.md:10", "--site", "a.md:9", "--site", "b.md:2"))
        self.ok(self.add("--skill", "dry-run", "--source", "dry-run phase 1", "--title", "B",
                         "--body-file", "-"))
        self.ok(self.add("--skill", "retrofit-from-public", "--source", "retrofit step 4",
                         "--title", "C", "--body-file", "-"))
        m = manifest(self.rd)
        self.assertEqual(SHA, m["baseline_sha"])
        self.assertEqual(["dry-run-01", "dry-run-02", "retrofit-from-public-01"],
                         [r["id"] for r in m["records"]])
        first = m["records"][0]
        self.assertEqual("pending", first["status"])
        self.assertEqual(["a.md:9", "b.md:2", "b.md:10"], first["dedupe_key"])
        draft = (Path(self.rd) / first["draft"]).read_text(encoding="utf-8")
        for part in ("id: dry-run-01", "source: dry-run phase 2", "baseline_sha: " + SHA,
                     "dedupe_key: a.md:9; b.md:2; b.md:10", "labels: bug", "# A defect\n\n",
                     "The exact body."):
            self.assertIn(part, draft)

    def test_an_upstream_message_is_upstream_pending_and_cannot_be_approved(self):
        self.ok(self.add("--skill", "feedback-to-issues", "--source", "Step 8", "--kind", "upstream",
                         "--category", "bug", "--body-file", "-"))
        rec = manifest(self.rd)["records"][0]
        self.assertEqual("upstream-pending", rec["status"])
        refused = run("set", self.rd, rec["id"], "approved")
        self.assertEqual(3, refused.returncode)
        self.ok(run("set", self.rd, rec["id"], "upstream-declined"))

    def test_unattended_ok_is_refused_and_nothing_is_written(self):
        """INV-318: no draft carries `unattended-ok`."""
        result = self.add("--skill", "dry-run", "--source", "x", "--title", "T",
                          "--label", "unattended-ok", "--body-file", "-")
        self.assertEqual(2, result.returncode)
        self.assertIn("INV-318", result.stderr)
        self.assertFalse((Path(self.rd) / "drafts" / "manifest.json").exists())

    def test_a_second_baseline_is_refused(self):
        self.ok(self.add("--skill", "dry-run", "--source", "x", "--title", "T", "--body-file", "-"))
        result = self.add("--skill", "dry-run", "--source", "y", "--title", "U", "--body-file", "-",
                          sha=OTHER)
        self.assertEqual(4, result.returncode)
        self.assertEqual(1, len(manifest(self.rd)["records"]))

    def test_a_bad_site_is_refused(self):
        result = self.add("--skill", "dry-run", "--source", "x", "--title", "T",
                          "--body-file", "-", "--site", "no-line-number")
        self.assertEqual(1, result.returncode)


class FileStage(HelperCase):
    def setUp(self):
        super().setUp()
        self.ok(self.add("--skill", "feedback-to-issues", "--source", "Step 7", "--title", "Filed one",
                         "--label", "bug", "--body-file", "-",
                         "--after", '--disposition "Alpha={outcome}"'))
        self.ok(self.add("--skill", "feedback-to-issues", "--source", "Step 7", "--title", "Struck one",
                         "--body-file", "-", "--after", '--disposition "Bravo={outcome}"'))
        self.ok(self.add("--skill", "feedback-to-issues", "--source", "Step 7", "--title", "Left alone",
                         "--body-file", "-"))
        self.ok(self.add("--skill", "feedback-to-issues", "--source", "Step 6", "--kind", "ledger",
                         "--after", '--disposition "Charlie=already-tracked"'))
        self.ok(self.add("--skill", "feedback-to-issues", "--source", "Step 8", "--kind", "upstream",
                         "--category", "feature", "--body-file", "-"))
        self.ok(run("set", self.rd, "feedback-to-issues-01", "approved"))
        self.ok(run("set", self.rd, "feedback-to-issues-02", "struck"))
        self.ok(run("set", self.rd, "feedback-to-issues-04", "approved"))

    def plan(self, sha=SHA):
        return run("file-plan", self.rd, "--skill", "feedback-to-issues", "--sha", sha)

    def test_file_plan_files_only_approved_issue_records(self):
        out = self.ok(self.plan())
        files = [l for l in out.splitlines() if l.startswith("FILE ")]
        self.assertEqual(1, len(files), out)
        self.assertIn("feedback-to-issues-01", files[0])
        self.assertIn("gh issue create --title 'Filed one' --label bug --body-file", files[0])
        for line in ("STRUCK feedback-to-issues-02", "PENDING feedback-to-issues-03",
                     "LEDGER feedback-to-issues-04", "UPSTREAM feedback-to-issues-05"):
            self.assertIn(line, out)
        body = Path(self.rd) / "drafts" / "feedback-to-issues-01.body.md"
        self.assertEqual("The exact body.\n", body.read_text(encoding="utf-8"))

    def test_no_printed_command_passes_repo(self):
        """INV-319: neither stage files anywhere but this repository."""
        self.assertNotIn("--repo", self.ok(self.plan()))

    def test_a_baseline_mismatch_is_refused_naming_both(self):
        for result in (self.plan(sha=OTHER), run("check-sha", self.rd, "--sha", OTHER)):
            self.assertEqual(4, result.returncode)
            self.assertIn(SHA, result.stderr)
            self.assertIn(OTHER, result.stderr)
        self.ok(run("check-sha", self.rd, "--sha", SHA[:8]))

    def test_the_number_is_written_back_and_a_rerun_files_nothing_twice(self):
        self.ok(run("record-filed", self.rd, "feedback-to-issues-01", "#601"))
        rec = manifest(self.rd)["records"][0]
        self.assertEqual((601, "filed"), (rec["issue"], rec["status"]))
        out = self.ok(self.plan())
        self.assertNotIn("FILE ", out)
        self.assertIn("SKIP feedback-to-issues-01: already filed as #601", out)
        self.ok(run("record-filed", self.rd, "feedback-to-issues-01", "601"))
        self.assertEqual(3, run("record-filed", self.rd, "feedback-to-issues-01", "602").returncode)
        self.assertEqual(601, manifest(self.rd)["records"][0]["issue"])
        self.assertEqual(3, run("set", self.rd, "feedback-to-issues-01", "pending").returncode)

    def test_only_an_approved_record_can_be_recorded_as_filed(self):
        self.assertEqual(3, run("record-filed", self.rd, "feedback-to-issues-03", "700").returncode)
        self.assertEqual(3, run("record-filed", self.rd, "feedback-to-issues-02", "700").returncode)

    def test_after_waits_for_a_complete_set_then_fills_the_numbers(self):
        waiting = run("after", self.rd, "--skill", "feedback-to-issues")
        self.assertEqual(3, waiting.returncode)
        self.assertIn("feedback-to-issues-01", waiting.stderr)
        self.ok(run("record-filed", self.rd, "feedback-to-issues-01", "601"))
        self.ok(run("set", self.rd, "feedback-to-issues-03", "struck"))
        out = self.ok(run("after", self.rd, "--skill", "feedback-to-issues"))
        self.assertEqual(['--disposition "Alpha=#601"',
                          '--disposition "Bravo=declined by the maintainer"',
                          '--disposition "Charlie=already-tracked"'], out.splitlines())

    def test_after_struck_replaces_an_issue_template(self):
        self.ok(self.add("--skill", "delegate-to-mcp-server", "--source", "Step 7", "--title", "D",
                         "--body-file", "-", "--after", "--key k --verdict delegate --issue {issue}",
                         "--after-struck", '--key k --verdict delegate --reason "declined"'))
        self.ok(self.add("--skill", "delegate-to-mcp-server", "--source", "Step 7", "--title", "E",
                         "--body-file", "-", "--after", "--key e --verdict delegate --issue {issue}",
                         "--after-struck", '--key e --verdict delegate --reason "declined"'))
        self.ok(run("set", self.rd, "delegate-to-mcp-server-01", "approved"))
        self.ok(run("record-filed", self.rd, "delegate-to-mcp-server-01", "142"))
        self.ok(run("set", self.rd, "delegate-to-mcp-server-02", "struck"))
        out = self.ok(run("after", self.rd, "--skill", "delegate-to-mcp-server"))
        self.assertEqual(["--key k --verdict delegate --issue 142",
                          '--key e --verdict delegate --reason "declined"'], out.splitlines())

    def test_an_issue_template_without_a_struck_form_is_refused(self):
        result = self.add("--skill", "delegate-to-mcp-server", "--source", "Step 7", "--title", "F",
                          "--body-file", "-", "--after", "--issue {issue}")
        self.assertEqual(1, result.returncode)

    def test_a_retitled_draft_is_refused(self):
        draft = Path(self.rd) / "drafts" / "feedback-to-issues-01.md"
        draft.write_text(draft.read_text(encoding="utf-8").replace("# Filed one", "# Renamed"),
                         encoding="utf-8")
        self.assertEqual(3, self.plan().returncode)

    def test_an_edited_body_is_the_body_filed(self):
        draft = Path(self.rd) / "drafts" / "feedback-to-issues-01.md"
        draft.write_text(draft.read_text(encoding="utf-8").replace("The exact body.", "Merged."),
                         encoding="utf-8")
        self.ok(self.plan())
        body = Path(self.rd) / "drafts" / "feedback-to-issues-01.body.md"
        self.assertEqual("Merged.\n", body.read_text(encoding="utf-8"))


class HandRun(HelperCase):
    def test_list_ends_with_the_not_durable_warning_and_the_file_command(self):
        self.ok(self.add("--skill", "production-readiness-audit", "--source", "Step 8",
                         "--title", "T", "--body-file", "-"))
        out = self.ok(run("list", self.rd, "--skill", "production-readiness-audit"))
        tail = out.strip().splitlines()[-3:]
        self.assertIn("NOT yet a durable record", tail[0])
        self.assertIn("INV-317", tail[1])
        self.assertEqual("File the approved ones with: /production-readiness-audit --file %s"
                         % self.rd, tail[2].strip())

    def test_a_resolved_set_gives_no_warning(self):
        self.ok(self.add("--skill", "dry-run", "--source", "phase 1", "--title", "T", "--body-file", "-"))
        self.ok(run("set", self.rd, "dry-run-01", "struck"))
        self.assertNotIn("durable", self.ok(run("list", self.rd)))

    def test_a_whole_cycle_writes_nothing_outside_the_run_dir(self):
        before = tree(self.root)
        self.ok(self.add("--skill", "dry-run", "--source", "phase 2", "--title", "T", "--body-file", "-"))
        self.ok(run("set", self.rd, "dry-run-01", "approved"))
        self.ok(run("file-plan", self.rd, "--skill", "dry-run", "--sha", SHA, cwd=self.tmp.name))
        self.ok(run("record-filed", self.rd, "dry-run-01", "9", cwd=self.tmp.name))
        self.ok(run("after", self.rd, "--skill", "dry-run", cwd=self.tmp.name))
        self.ok(run("list", self.rd, cwd=self.tmp.name))
        outside = [p for p in tree(self.root) if p not in before and not p.startswith("run")]
        self.assertEqual([], outside)
        self.assertFalse((Path(self.rd) / "drafts" / "manifest.lock").exists())


class TheDocstringIsTheContract(unittest.TestCase):
    """INV-300: the one statement names everything the helper enforces."""

    @classmethod
    def setUpClass(cls):
        source = SCRIPT.read_text(encoding="utf-8")
        cls.doc = flat(source.split('"""', 2)[1])
        cls.source = source

    def test_every_status_kind_and_skill_is_named(self):
        names = re.search(r"STATUSES = \{(.*?)\n\}", self.source, re.S).group(1)
        for status in re.findall(r'^\s+"([a-z-]+)":', names, re.M):
            self.assertIn("`%s`" % status, self.doc)
        for kind in ("issue", "upstream", "ledger"):
            self.assertIn("``%s``" % kind, self.doc)
        for skill in SKILLS:
            self.assertIn("/" + skill, self.doc)

    def test_it_states_both_stages_and_the_manifest(self):
        for phrase in ("this docstring is the one statement", "(INV-300)",
                       "Stage one files nothing, fixes nothing and sends nothing, and writes "
                       "nothing outside `<run-dir>`",
                       "`<run-dir>/drafts/manifest.json`", "dedupe_key", "baseline SHA",
                       "`/release-cycle`'s interface", "The caller records unresolved drafts "
                       "(INV-317)", "get a yes for each", "(INV-314)", "(INV-318)", "(INV-319)",
                       "declined by the maintainer", "never filed twice", BATCH_CLAUSE,
                       "`--file` never sends an `upstream` record", "which only its own yes moves",
                       "`submit_feedback` stays one message, one yes"):
            self.assertIn(phrase.lower(), self.doc.lower())

    def test_the_stale_per_record_lines_are_gone(self):
        """#573: the filing step no longer waits on #570, which PR #586 and PR #588 closed."""
        self.assertEqual([], stale(self.doc))


#: INV-314's 2026-10-13 note, in the one form `tests/test_filing_is_gated.py` finds (#575).
BATCH_CLAUSE = "one yes for the whole list shown in one message (INV-314, 2026-10-13 note)"

#: #572's per-record lines, written before #570's amendments were registered (#573 retired them).
STALE = ("get a yes for each first", "Until #570's amendments are registered")

#: The skills that draft upstream messages, whose `--file` stage says it never sends one.
UPSTREAM_SKILLS = ("feedback-to-issues", "delegate-to-mcp-server", "dry-run")
UPSTREAM_KEPT = "an upstream draft is never sent by `--file` and keeps its own yes"

#: What each skill must state. The rule sentence is the same in all five.
REQUIRED = (
    "`--draft <run-dir>`",
    "`--file <run-dir>`",
    "this run files nothing, fixes nothing and sends nothing, and writes nothing outside `<run-dir>`",
    "drafts.py)",
    "`--draft` is the release cycle's interface (#573), and the caller records unresolved drafts "
    "(INV-317)",
    "ends with `drafts.py list`",
    "file what `drafts.py file-plan` prints",
    "after a yes for each record or " + BATCH_CLAUSE,
    "stated once in `drafts.py` (INV-300)",
)

#: The manifest format and the statuses live in `drafts.py` alone (INV-300).
RESTATED = re.compile(r"manifest\.json|upstream-pending|\bstatus `?(?:approved|struck)|dedupe_key")


def missing(text):
    t = flat(text)
    return [p for p in REQUIRED if p not in t]


def restated(text):
    return RESTATED.findall(text)


def stale(text):
    t = flat(text)
    return [p for p in STALE if p in t]


def skill_text(name):
    return (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")


class EachSkillCitesTheContract(unittest.TestCase):
    def test_each_skill_states_both_stages_and_cites_the_helper(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                self.assertEqual([], missing(skill_text(name)))

    def test_each_argument_hint_names_both_arguments(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                hint = re.search(r'^argument-hint: "(.*)"$', skill_text(name), re.M).group(1)
                self.assertIn("[--draft <run-dir> | --file <run-dir>]", hint)

    def test_each_link_resolves_to_the_helper(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                links = re.findall(r"\[`drafts\.py`\]\(([^)]+)\)", skill_text(name))
                self.assertTrue(links)
                for link in links:
                    self.assertEqual(SCRIPT.resolve(), (SKILLS_DIR / name / link).resolve())

    def test_no_skill_restates_the_manifest_format(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                self.assertEqual([], restated(skill_text(name)))

    def test_feedback_and_delegate_finish_step_9_from_the_after_lines(self):
        for name, sentence in (
                ("feedback-to-issues", "With `--file <run-dir>`, the dispositions are the lines "
                                       "`drafts.py after` prints."),
                ("delegate-to-mcp-server", "With `--file <run-dir>`, run `record` once per line "
                                           "`drafts.py after` prints.")):
            with self.subTest(skill=name):
                text = skill_text(name)
                step9 = text[text.index("## Step 9"):text.index("## Step 10")]
                self.assertIn(sentence, flat(step9))

    def test_no_skill_keeps_the_stale_per_record_line(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                self.assertEqual([], stale(skill_text(name)))

    def test_an_upstream_draft_keeps_its_own_yes(self):
        """`submit_feedback` stays one message, one yes; the batch clause never reaches it."""
        for name in UPSTREAM_SKILLS:
            with self.subTest(skill=name):
                self.assertIn(UPSTREAM_KEPT, flat(skill_text(name)))

    def test_retrofit_repeats_its_tracker_search_before_filing(self):
        self.assertIn("repeat step 3's search for each approved record, since the tracker may have "
                      "changed", flat(skill_text("retrofit-from-public")))

    def test_the_rule_sits_at_each_skill_s_filing_step(self):
        anchors = {"feedback-to-issues": "## Step 7", "retrofit-from-public": "## After it runs",
                   "delegate-to-mcp-server": "## Step 7",
                   "production-readiness-audit": "## Step 8",
                   "dry-run": "## The finding lifecycle"}
        for name, anchor in anchors.items():
            with self.subTest(skill=name):
                text = skill_text(name)
                start = text.index(anchor)
                end = text.find("\n## ", start + len(anchor))
                self.assertIn("files nothing, fixes nothing and sends nothing",
                              flat(text[start:end if end > 0 else None]))


class NegativeControls(unittest.TestCase):
    def test_dropping_the_rule_or_the_citation_is_reported(self):
        text = flat(skill_text("dry-run"))
        self.assertIn(REQUIRED[2], missing(text.replace("fixes nothing and sends", "sends")))
        self.assertIn(REQUIRED[8], missing(text.replace("stated once in `drafts.py` (INV-300)", "")))
        self.assertIn(REQUIRED[4], missing(re.sub(r"\(INV-317\)", "", text)))

    def test_the_stale_line_or_a_dropped_clause_is_reported(self):
        text = flat(skill_text("feedback-to-issues"))
        self.assertTrue(stale(text.replace("after a yes for each record or",
                                           "and get a yes for each first or")))
        self.assertTrue(stale("2. Until #570's amendments are registered, show each record"))
        self.assertIn(REQUIRED[7], missing(text.replace(BATCH_CLAUSE, "")))
        self.assertNotIn(UPSTREAM_KEPT, text.replace(UPSTREAM_KEPT, "an upstream draft is sent"))

    def test_a_restated_status_is_reported(self):
        self.assertTrue(restated("Each record starts with status `approved`."))
        self.assertTrue(restated("append to manifest.json"))
        self.assertFalse(restated(skill_text("feedback-to-issues")))


class GitIgnore(unittest.TestCase):
    def test_run_directories_are_ignored(self):
        lines = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".claude/release-cycle/runs/", [l.strip() for l in lines])


if __name__ == "__main__":
    unittest.main()
