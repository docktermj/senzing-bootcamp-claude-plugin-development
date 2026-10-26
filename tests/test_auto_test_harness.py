"""The /auto-test harness must work, and must keep working offline.

Two jobs, and the second is the interesting one.

**Job 1 — the harness is negative-controlled.** `transcript_lint.py` ships a
selftest that asserts every rule fires on input built to break it and stays silent
on input built to pass. A guard whose docstring claims more than its assertion
checks is worse than no guard, so the suite runs that selftest rather than trusting
it exists.

**Job 2 — the plugin conforms to the last observed MCP contract, offline.**
`.claude/skills/auto-test/baseline/mcp-snapshot.json` is a committed record of what
the live server accepted, including the value sets discovered by sending deliberate
bad values. Checking the plugin against that file needs no network, so it belongs in
this suite (INV-108: stdlib only, offline, fast) while `/auto-test` refreshes the
file online.

That split is what keeps `tests/test_mcp_call_contracts.py` honest. That test pins
the contract as prose constants a human transcribed on a date; this one checks
against a machine-captured snapshot with a diffable provenance. When the two
disagree, `mcp_probe.py`'s `audit_static_contract` says so.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / ".claude" / "skills" / "auto-test"
BASELINE = HARNESS / "baseline" / "mcp-snapshot.json"

sys.path.insert(0, str(HARNESS))


def _load_baseline():
    return json.loads(BASELINE.read_text(encoding="utf-8"))


class TestHarnessIsPresent(unittest.TestCase):
    """The skill is a maintainer tool; it must not leak into the shipped plugin."""

    def test_every_component_exists(self):
        for name in ("SKILL.md", "mcp_probe.py", "transcript_lint.py", "walk.py",
                     "autotest.py"):
            self.assertTrue((HARNESS / name).is_file(), f"missing {name}")

    def test_baseline_is_committed(self):
        self.assertTrue(BASELINE.is_file(),
                        "the MCP baseline must be committed; without it the offline "
                        "conformance check below silently covers nothing")

    def test_harness_is_not_shipped_to_bootcampers(self):
        """propagate.sh mirrors plugins/, .claude-plugin/, docs/ and README.md."""
        self.assertNotIn("plugins", HARNESS.relative_to(REPO_ROOT).parts,
                         "the harness must live under .claude/, which is not "
                         "propagated to the public repo")


class TestTranscriptLinterIsNegativeControlled(unittest.TestCase):
    def test_selftest_passes(self):
        result = subprocess.run(
            [sys.executable, str(HARNESS / "transcript_lint.py"), "--selftest"],
            capture_output=True, text=True)
        self.assertEqual(
            0, result.returncode,
            f"transcript_lint selftest failed:\n{result.stdout}\n{result.stderr}")

    def test_a_clean_transcript_is_clean(self):
        import transcript_lint as lint
        good = ["Nice — a claims database is exactly the case this is built for.\n\n"
                "\U0001f449 **Which source would you like to start with?**\n\n"
                "1. Claims\n2. Policies\n\n(respond with a number)"]
        self.assertEqual([], lint.lint(good))

    def test_selftest_fails_with_the_old_apparatus_patterns(self):
        """#658: the selftest holds the patterns to the plugin's own renderings.

        Restoring the patterns that missed "Your journey", "⏱️ Roughly 20–45
        minutes" and "Before → After" must turn the selftest red; otherwise it
        does not guard the widening.
        """
        import contextlib
        import io
        import re
        from unittest import mock

        import transcript_lint as lint
        old = dict(lint.APPARATUS)
        old.update({
            "journey map": re.compile(r"(?i)journey map"),
            "before/after": re.compile(r"(?i)\bbefore\s*(?:/|and)\s*after\b"),
            "time estimate": re.compile(
                r"(?i)\b(?:takes|about|approx\w*)\s+\d+\s*(?:-|to)?\s*\d*\s*minutes?\b"),
        })
        err = io.StringIO()
        with mock.patch.dict(lint.APPARATUS, old), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(err):
            self.assertEqual(1, lint.selftest())
        for name in ("journey map", "before/after", "time estimate"):
            self.assertIn(f"{name} pattern missed", err.getvalue())


class TestPluginConformsToTheCapturedContract(unittest.TestCase):
    """The offline half of the MCP check, against the committed snapshot."""

    def setUp(self):
        import mcp_probe
        self.probe = mcp_probe
        self.live = _load_baseline()

    def test_no_breaking_conformance_findings(self):
        # url=None keeps this offline: a suspicion that would need a live call to
        # settle is skipped rather than guessed at.
        findings = self.probe.conformance(self.live, url=None)
        breaking = [f for f in findings if f["severity"] == self.probe.BREAKING]
        self.assertEqual(
            [], breaking,
            "the plugin calls the MCP server in a way the captured contract "
            "rejects:\n  " + "\n  ".join(f["message"] for f in breaking))

    def test_every_probed_parameter_still_has_a_value_set(self):
        """A baseline whose probes all came back empty would pass everything."""
        enumerated = [
            (tool, param)
            for tool, meta in self.live["tools"].items()
            for param, info in (meta.get("probed_values") or {}).items()
            if info.get("mode") == self.probe.ENUMERATED and info.get("values")
        ]
        self.assertGreaterEqual(
            len(enumerated), 8,
            "fewer enumerated parameters than expected — the conformance check "
            f"only covers {len(enumerated)}; re-run `mcp_probe.py update`")

    def test_the_workflow_actions_match_the_other_test(self):
        """Cross-check against test_mcp_call_contracts.py's hand-written constant."""
        import re
        contract = (REPO_ROOT / "tests" / "test_mcp_call_contracts.py").read_text()
        match = re.search(r"VALID_WORKFLOW_ACTIONS\s*=\s*\{([^}]*)\}", contract)
        self.assertIsNotNone(match, "VALID_WORKFLOW_ACTIONS not found")
        pinned = set(re.findall(r'"([a-z_]+)"', match.group(1)))
        captured = set(
            self.live["tools"]["mapping_workflow"]["probed_values"]["action"]["values"])
        self.assertEqual(
            pinned, captured,
            "the hand-written contract and the captured snapshot disagree about "
            "mapping_workflow's actions; one of them is wrong")

    def test_both_language_value_lists_are_captured(self):
        """#659: an `update` taken while the language regexes missed stored `[]`.

        `diff_baseline` reports `prose-unextractable` only when the baseline list is
        non-empty, so an empty list here would silence that check for good.
        """
        for tool in ("generate_scaffold", "sdk_guide"):
            values = self.live["tools"][tool]["prose_values"].get("language") or []
            self.assertEqual(
                {"python", "java", "csharp", "rust", "typescript"},
                self.probe._canon_set(values),
                f"{tool}.language prose_values in the baseline are {values}")

    def test_no_correct_name_org_use_is_flagged(self):
        """#659: NAME_ORG is the correct attribute; the server warns about EMPLOYER_NAME."""
        flagged = [f["message"] for f in self.probe.conformance(self.live, url=None)
                   if f["code"] == "confabulation" and "`NAME_ORG`" in f["message"]]
        self.assertEqual([], flagged)


class TestTheProbeTablesMatchServer1390(unittest.TestCase):
    """#659: CONFABULATIONS, PROSE_VALUES and declared enums against server 1.39.0.

    The description strings are quoted from `tools/list` on sz-mcp-coworker 1.39.0
    (2026-10-15), trimmed to the sentences the regexes read.
    """

    GENERATE_SCAFFOLD = (
        "Generate SDK scaffold code for common workflows. Languages: python, java, "
        "csharp (official V4 SDKs); rust, typescript (community-maintained wrappers, "
        "not official). Workflows: initialize, configure, add_records, delete, query, "
        "redo, stewardship, information, error_handling, full_pipeline.")
    SDK_GUIDE = (
        "If `platform` is omitted for install and this server runs on the install host "
        "itself, it detects the platform from that host's os-release. Languages: 5 "
        "(Python, Java, C#, Rust, TypeScript). Returns real, compilable code snippets.")
    # The patterns that missed both strings, kept for the negative control.
    OLD_LANGUAGE_PATTERNS = {
        ("generate_scaffold", "language"): r"Languages:\s*([a-z#,\s]+?)\.",
        ("sdk_guide", "language"): r"\d+\s+languages\s*\(([^)]+)\)",
    }
    LANGUAGES = {"python", "java", "csharp", "rust", "typescript"}
    FIXTURE = REPO_ROOT / "plugins" / "probe-fixture.md"

    def setUp(self):
        import mcp_probe
        self.probe = mcp_probe

    def languages(self, tool, description):
        return self.probe.extract_prose_values(tool, description)["language"]

    def test_generate_scaffold_languages_parse(self):
        self.assertEqual(["python", "java", "csharp", "rust", "typescript"],
                         self.languages("generate_scaffold", self.GENERATE_SCAFFOLD))

    def test_sdk_guide_languages_parse(self):
        values = self.languages("sdk_guide", self.SDK_GUIDE)
        self.assertEqual(["python", "java", "c#", "rust", "typescript"], values)
        self.assertEqual(self.LANGUAGES, self.probe._canon_set(values))

    def test_the_older_wording_still_parses(self):
        self.assertEqual(
            ["python", "java", "csharp", "rust"],
            self.languages("generate_scaffold", "Languages: python, java, csharp, rust."))
        self.assertEqual(
            self.LANGUAGES,
            self.probe._canon_set(self.languages(
                "sdk_guide", "and 5 languages (Python, Java, C#, Rust, TypeScript).")))

    def test_the_old_patterns_miss_the_1390_wording(self):
        """Negative control: the strings above are the ones that broke the old regexes."""
        from unittest import mock
        with mock.patch.dict(self.probe.PROSE_VALUES, self.OLD_LANGUAGE_PATTERNS):
            self.assertEqual([], self.languages("generate_scaffold", self.GENERATE_SCAFFOLD))
            self.assertEqual([], self.languages("sdk_guide", self.SDK_GUIDE))

    def confabulations(self, text, pairs=None):
        """Run the conformance check over one fixture file, offline."""
        from unittest import mock
        live = {"tools": {"get_capabilities": {"required": []}}}
        with mock.patch.object(self.probe, "_skill_files",
                               lambda: iter([(self.FIXTURE, text)])):
            if pairs is None:
                found = self.probe.conformance(live, url=None)
            else:
                with mock.patch.object(self.probe, "CONFABULATIONS", pairs):
                    found = self.probe.conformance(live, url=None)
        return [f["message"] for f in found if f["code"] == "confabulation"]

    UNCUED_EMPLOYER = "Map the employer column to EMPLOYER_NAME.\n"
    CORRECT_NAME_ORG = "Map the company name column to NAME_ORG.\n"

    def test_an_uncued_employer_name_is_flagged(self):
        flagged = self.confabulations(self.UNCUED_EMPLOYER)
        self.assertEqual(1, len(flagged), flagged)
        self.assertIn("`EMPLOYER_NAME`", flagged[0])
        self.assertIn("`NAME_ORG`", flagged[0])

    def test_a_correct_name_org_is_not_flagged(self):
        self.assertEqual([], self.confabulations(self.CORRECT_NAME_ORG))

    def test_a_cued_employer_name_is_not_flagged(self):
        self.assertEqual([], self.confabulations("Use NAME_ORG, never EMPLOYER_NAME.\n"))

    def test_the_inverted_pair_gets_both_wrong(self):
        """Negative control: restoring the pre-#659 pair flips both verdicts."""
        inverted = tuple(p for p in self.probe.CONFABULATIONS
                         if p != ("EMPLOYER_NAME", "NAME_ORG")) + (
            ("NAME_ORG", "BUSINESS_NAME_ORG"),)
        self.assertEqual([], self.confabulations(self.UNCUED_EMPLOYER, inverted))
        self.assertEqual(1, len(self.confabulations(self.CORRECT_NAME_ORG, inverted)))

    # mapping_workflow.action's declared enum on 1.39.0, as the snapshot stores it.
    ACTION_ENUM = [None, "advance", "back", "reset", "start", "status"]

    def test_a_declared_enum_joins_the_accepted_set_without_null(self):
        accepted = self.probe.accepted_values({"enums": {"action": self.ACTION_ENUM}},
                                              "action")
        self.assertEqual({"advance", "back", "reset", "start", "status"}, accepted)
        self.assertNotIn(None, accepted)

    def test_a_declared_enum_is_unioned_with_the_probed_set(self):
        meta = {"enums": {"topic": ["install", "setup"]},
                "probed_values": {"topic": {"mode": self.probe.ENUMERATED,
                                            "values": ["install", "load"]}}}
        self.assertEqual({"install", "setup", "load"},
                         self.probe.accepted_values(meta, "topic"))

    def test_a_declared_enum_never_adds_a_rejection(self):
        """Without a probed enumeration, a value outside the enum is not accused."""
        from unittest import mock
        live = {"tools": {"mapping_workflow": {"required": [],
                                               "enums": {"action": self.ACTION_ENUM}}}}
        text = "Call `mapping_workflow(action='zzz_not_a_value')`.\n"
        with mock.patch.object(self.probe, "_skill_files",
                               lambda: iter([(self.FIXTURE, text)])):
            found = self.probe.conformance(live, url=None)
        self.assertEqual([], [f for f in found if f["code"] == "invalid-value"])


class TestTheHarnessRefusesDangerousCalls(unittest.TestCase):
    """Enforced by flag, not by instruction — an unattended run forgets rules."""

    def test_probe_never_calls_the_forbidden_tools(self):
        import mcp_probe
        self.assertEqual({"submit_feedback", "download_resource"},
                         set(mcp_probe.NEVER_CALL))
        for tool, _param, _base in mcp_probe.PROBE_MATRIX:
            self.assertNotIn(tool, mcp_probe.NEVER_CALL,
                             f"{tool} is in PROBE_MATRIX but must never be called")
        for tool, _args in mcp_probe.CONTENT_PROBES:
            self.assertNotIn(tool, mcp_probe.NEVER_CALL)

    def test_the_walk_disallows_them_by_flag(self):
        import walk
        self.assertEqual(
            ("mcp__senzing__submit_feedback", "mcp__senzing__download_resource"),
            walk.FORBIDDEN_TOOLS)


GATE = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "write-gate.py"
#: A substring of the gate's temp/Downloads message (`write-gate.py` reads stdin at import
#: time, so its constants cannot be imported; `tests/test_write_gate.py` does the same).
TEMP_MSG = "system temp or Downloads"
#: What every shipped or maintainer file said before #834: the sandbox under `$HOME`, and the
#: gate as the reason it could not be in the temp directory.
RETIRED_SANDBOX_CLAIM = re.compile(
    r"senzing-autotest/runs"
    r"|Project dir(?:ectory)?\W* under\W+\$HOME"
    r"|sandbox there (?:would )?tests? the gate"
    r"|Never put the sandbox under\W+/tmp")


class TestSandboxLocation(unittest.TestCase):
    """Each run's root is a fresh private directory under the system temp directory (#834).

    Claude Code loads every ancestor's `.claude/CLAUDE.md`, `CLAUDE.md`, `CLAUDE.local.md` and
    `.claude/rules/*.md` as project memory, even under `--setting-sources project,local`
    (#794's probe, CLI 2.1.310), so a run root under `$HOME` hands the guide the host's
    `~/.claude/CLAUDE.md`. The reason this class used to give for staying under `$HOME`,
    that `write-gate.py` blocks a project under `/tmp`, does not hold: the gate exempts the
    project directory first. The gate tests below reproduce that against the real gate, with
    a project laid out exactly as `autotest.make_run_root` lays one out.

    The run roots here are made under the real, unpatched `SANDBOX_ROOT` -- that location is
    what is under test -- and each is removed when its test ends.
    """

    def setUp(self):
        import autotest
        self.autotest = autotest

    def run_root(self, persona="terse"):
        import shutil
        root = self.autotest.make_run_root("20261026-000000", persona)
        self.addCleanup(shutil.rmtree, root, True)
        return root

    def test_the_default_root_is_the_system_temp_directory(self):
        import tempfile
        self.assertEqual(Path(tempfile.gettempdir()), self.autotest.SANDBOX_ROOT)

    def test_each_run_root_is_fresh_private_and_resolved_under_the_temp_directory(self):
        import os
        import stat
        import tempfile
        first, second = self.run_root(), self.run_root()
        self.assertNotEqual(first, second, "two runs shared a root")
        temp = Path(tempfile.gettempdir()).resolve()
        for root in (first, second):
            with self.subTest(root=root):
                self.assertEqual(root, root.resolve())
                self.assertEqual(temp, root.parent)
                self.assertTrue(root.name.startswith("senzing-autotest-20261026-000000-terse-"))
                if os.name != "nt":   # Windows has no POSIX mode bits to assert
                    self.assertEqual(0o700, stat.S_IMODE(root.stat().st_mode))

    def test_neither_the_project_nor_the_bootcampers_cwd_is_under_home(self):
        """Linux and macOS. On Windows the temp directory is under the user profile."""
        import os
        import tempfile
        import walk
        if os.name == "nt":
            self.skipTest("on Windows %TEMP% is under the profile; the walk discloses it")
        home = Path.home().resolve()
        if home == Path(tempfile.gettempdir()).resolve() or \
                home in Path(tempfile.gettempdir()).resolve().parents:
            self.skipTest(f"this host's temp directory is under HOME ({home})")
        root = self.run_root()
        for path in (root / "project", walk.bootcamper_dir(root / "project")):
            with self.subTest(path=path):
                self.assertEqual(root, path.parent)
                self.assertNotEqual(home, path)
                self.assertNotIn(home, path.parents)

    def gate(self, project, target):
        """Run the real `write-gate.py` from `project`, as the hook runs; (exit, stderr)."""
        import json
        (project / "config").mkdir(parents=True, exist_ok=True)
        (project / "config" / "bootcamp_progress.json").write_text("{}", encoding="utf-8")
        payload = json.dumps({"tool_input": {"file_path": str(target), "content": "x = 1\n"}})
        done = subprocess.run([sys.executable, str(GATE)], input=payload, cwd=str(project),
                              capture_output=True, text=True)
        return done.returncode, done.stderr

    def test_the_write_gate_allows_an_in_project_write_under_the_temp_directory(self):
        project = self.run_root() / "project"
        project.mkdir()
        for target in (project / "src" / "load.py", "src/load.py"):
            with self.subTest(target=target):
                self.assertEqual((0, ""), self.gate(project, target))

    def test_the_write_gate_blocks_a_temp_write_outside_the_project(self):
        """The blocking case: the same gate, the same project, a target outside it."""
        import tempfile
        root = self.run_root()
        project = root / "project"
        project.mkdir()
        elsewhere = Path(tempfile.gettempdir()).resolve() / "elsewhere" / "x.py"
        for target in (elsewhere, root / "bootcamper" / "x.py"):
            with self.subTest(target=target):
                code, stderr = self.gate(project, target)
                self.assertEqual(2, code)
                self.assertIn(TEMP_MSG, stderr)
        code, _stderr = self.gate(project, "~/x.py")
        self.assertEqual(2, code, "a write to HOME passed the gate")

    def test_an_unresolved_spelling_of_the_project_is_outside_it_to_the_gate(self):
        """Why the root is resolved: the gate compares with `os.getcwd()` (macOS's `/var`).

        A symlink stands in for `/var` -> `/private/var`: the same in-project file, spelled
        through the link, is blocked, and spelled through the resolved root, allowed.
        """
        import os
        root = self.run_root()
        project = root / "project"
        project.mkdir()
        link = Path(str(root) + "-link")
        try:
            os.symlink(root, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("this host cannot create a symlink")
        self.addCleanup(link.unlink)
        self.assertEqual(2, self.gate(project, link / "project" / "x.py")[0])
        self.assertEqual(0, self.gate(project, project / "x.py")[0])

    def test_no_file_says_the_sandbox_is_under_home_or_that_the_gate_blocks_it(self):
        """The retired reason is gone from every shipped and maintainer file (#834).

        Read through `_wrapped_text.match_lines`, so a phrase wrapped across lines still
        matches (INV-346). `specs/` is a frozen archive and keeps its history; `tests/` is
        not scanned, so this file's own fixtures are not read.
        """
        sys.path.insert(0, str(REPO_ROOT / "tests"))
        from _corpus import corpus_files
        from _wrapped_text import match_lines
        files = corpus_files(".claude", "plugins", "docs", suffixes=(".md", ".py"))
        files += [REPO_ROOT / "README.md"]
        self.assertTrue([f for f in files if f.name == "autotest.py"], "the scan read nothing")
        found = []
        for path in files:
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in match_lines(text, RETIRED_SANDBOX_CLAIM):
                found.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{line}")
        self.assertEqual([], found)

    def test_the_retired_claims_are_matched(self):
        """Negative control: each pre-#834 sentence fails the scan above."""
        from _wrapped_text import match_lines
        for text in (
                "Each run builds `~/senzing-autotest/runs/<timestamp>-<persona>/`.",
                "| Project dir under `$HOME` | `write-gate.py` blocks `/tmp`, `/var/tmp`, "
                "`/private/tmp` — a sandbox there tests the gate, not the bootcamp |",
                "* **Project directory** under ``$HOME``, one per run, timestamped. Never\n"
                "  ``/tmp``: the plugin's own ``write-gate.py`` blocks ``/tmp``, ``/var/tmp`` and\n"
                "  ``/private/tmp``, so a sandbox there would test the gate instead.",
                "- **Never put the sandbox under `/tmp`.**"):
            with self.subTest(text=text[:40]):
                self.assertTrue(match_lines(text, RETIRED_SANDBOX_CLAIM))
        self.assertEqual([], match_lines(
            "Each run builds a fresh private directory under the system temp directory. "
            "Reports stay in `~/senzing-autotest/reports/`.", RETIRED_SANDBOX_CLAIM))


class TestReportDirectory(unittest.TestCase):
    """`--report-dir DIR` takes the report, the transcript copy and `latest.json` (#609).

    `/dry-run --draft <run-dir>` passes `<run-dir>/walk/`, so a simulated walk keeps nothing
    outside its run directory but the sandbox, which is removed when the run ends (INV-368).
    Without the option the reports go to `~/senzing-autotest/reports` as before; the sandbox
    is a fresh directory under `SANDBOX_ROOT`, the temp directory unless patched (#834).

    Offline: `autotest._run` is replaced, so no git worktree, no MCP probe and no walk run;
    the fake walk writes a one-line transcript where `walk.py --out` would. `SANDBOX_ROOT` and
    `REPORT_DIR` point into a temporary directory, so the real `~/senzing-autotest` is untouched.
    """

    def setUp(self):
        import tempfile
        import autotest
        self.autotest = autotest
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        saved = (autotest._run, autotest.SANDBOX_ROOT, autotest.REPORT_DIR)
        self.default = autotest.REPORT_DIR
        self.default_root = autotest.SANDBOX_ROOT

        def restore():
            autotest._run, autotest.SANDBOX_ROOT, autotest.REPORT_DIR = saved
        self.addCleanup(restore)
        autotest.SANDBOX_ROOT = self.tmp / "senzing-autotest"
        autotest.REPORT_DIR = autotest.SANDBOX_ROOT / "reports"
        autotest._run = self.fake_run

    @staticmethod
    def fake_run(cmd, **kw):
        if cmd[:1] == ["git"]:
            return subprocess.CompletedProcess(cmd, 1, "", "no worktree offline")
        if any(str(c).endswith("walk.py") for c in cmd):
            Path(cmd[cmd.index("--out") + 1]).write_text('{"turn": 1}\n', encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "[]", "")

    def main(self, *argv):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return self.autotest.main(["--walk", *argv])

    def files(self, root):
        return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())

    def test_the_option_takes_all_three_files_and_creates_the_directory(self):
        target = self.tmp / "run-dir" / "walk"
        self.assertEqual(0, self.main("--report-dir", str(target)))
        names = self.files(target)
        self.assertIn("latest.json", names)
        self.assertEqual(1, sum(n.endswith(".transcript.jsonl") for n in names), names)
        self.assertEqual(2, sum(n.endswith(".json") for n in names), names)
        latest = json.loads((target / "latest.json").read_text(encoding="utf-8"))
        self.assertTrue(latest["transcript_path"].startswith(str(target)))
        self.assertTrue(latest["report_path"].startswith(str(target)))

    def sandbox(self, report_dir):
        """The run root `latest.json` reports."""
        latest = json.loads((report_dir / "latest.json").read_text(encoding="utf-8"))
        return Path(latest["sandbox"])

    def test_with_the_option_nothing_is_left_outside_it(self):
        """Only the sandbox is written elsewhere, and it is removed (no `--keep`)."""
        target = self.tmp / "run-dir" / "walk"
        self.main("--report-dir", str(target))
        # The run was made under the patched root, so the check below is not vacuous (#834).
        sandbox = self.sandbox(target)
        self.assertEqual(self.autotest.SANDBOX_ROOT.resolve(), sandbox.parent)
        self.assertFalse(sandbox.exists())
        self.assertEqual([], self.files(self.autotest.SANDBOX_ROOT))
        self.assertFalse(self.autotest.REPORT_DIR.exists())

    def test_the_leftover_check_fails_when_the_run_root_is_not_removed(self):
        """Negative control for the check above: `--keep` leaves the root, and it is seen."""
        target = self.tmp / "run-dir" / "walk"
        self.main("--keep", "--report-dir", str(target))
        sandbox = self.sandbox(target)
        self.assertTrue(sandbox.is_dir())
        self.assertNotEqual([], self.files(self.autotest.SANDBOX_ROOT))

    def test_the_reported_sandbox_is_its_own_resolved_path(self):
        """A symlinked `SANDBOX_ROOT` stands in for macOS's `/var` -> `/private/var` (#834)."""
        import os
        real = self.tmp / "real-temp"
        real.mkdir()
        link = self.tmp / "linked-temp"
        try:
            os.symlink(real, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("this host cannot create a symlink")
        self.autotest.SANDBOX_ROOT = link
        target = self.tmp / "run-dir" / "walk"
        self.main("--report-dir", str(target))
        sandbox = self.sandbox(target)
        self.assertEqual(str(sandbox.resolve()), str(sandbox))
        self.assertEqual(real.resolve(), sandbox.parent)

    def test_without_the_option_the_default_is_unchanged(self):
        self.main()
        names = self.files(self.autotest.REPORT_DIR)
        self.assertIn("latest.json", names)
        self.assertEqual(1, sum(n.endswith(".transcript.jsonl") for n in names), names)

    def test_the_default_is_the_reports_directory(self):
        """The unpatched default is `~/senzing-autotest/reports`, the path before #609.

        It no longer derives from `SANDBOX_ROOT`, which moved to the temp directory (#834).
        """
        self.assertEqual(Path.home() / "senzing-autotest" / "reports", self.default)
        self.assertNotIn(self.default_root, self.default.parents)

if __name__ == "__main__":
    unittest.main()
