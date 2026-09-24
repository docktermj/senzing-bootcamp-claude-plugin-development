"""The `delegate-to-mcp-server` sweep's ledger and inventory.

The sweep is periodic and mostly produces *keeps* — a fact the server cannot serve, or
can serve but should not. Those cost real MCP calls to establish and produce no spec, so
the ledger is the only place the work survives. Two properties make it worth testing:

* a verdict expires when the **server version** changes, not when time passes, so a run
  against an unchanged server re-asks nothing;
* a keep must carry its reason, because an unreasoned keep is indistinguishable from
  "nobody looked" and the next sweep re-litigates it.

The inventory is a lead generator. What is pinned here is its *scope* — the example
recap and archived specs stay out, `INVARIANTS.md` stays in — because a drifted glob
turns a sweep that found nothing into a sweep that looked nowhere, and the two read
identically in a report.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude" / "skills" / "delegate-to-mcp-server"
SCRIPT = SKILL / "coverage_ledger.py"


def load():
    spec = importlib.util.spec_from_file_location("coverage_ledger_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEDGER = load()


class LedgerRoundTrip(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "specs").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, *argv):
        return LEDGER.main(["--repo", str(self.repo), "record"] + list(argv))

    def test_a_verdict_round_trips(self):
        self.record("--key", "k", "--verdict", "delegate", "--server", "1.32.2",
                    "--claim", "c", "--tool", "search_docs")
        rows = LEDGER.read_ledger(self.repo)
        self.assertEqual("delegate", rows["k"]["verdict"])
        self.assertEqual("1.32.2", rows["k"]["server_version"])
        self.assertIn("checked", rows["k"], "a verdict with no date cannot be aged out")

    def test_a_keep_by_design_without_a_reason_is_refused(self):
        self.assertEqual(1, self.record("--key", "k", "--verdict", "keep-by-design",
                                        "--server", "1.32.2"))
        self.assertEqual({}, LEDGER.read_ledger(self.repo), "nothing may be written")

    def test_a_keep_by_design_with_a_reason_is_accepted(self):
        self.assertEqual(0, self.record("--key", "k", "--verdict", "keep-by-design",
                                        "--server", "1.32.2", "--reason", "needed offline"))
        self.assertEqual("needed offline", LEDGER.read_ledger(self.repo)["k"]["reason"])

    def test_an_unknown_verdict_is_refused_at_the_cli(self):
        """argparse's `choices` rejects it before `cmd_record` is reached."""
        with self.assertRaises(SystemExit) as raised:
            self.record("--key", "k", "--verdict", "delete-it", "--server", "1.32.2")
        self.assertEqual(2, raised.exception.code)
        self.assertEqual({}, LEDGER.read_ledger(self.repo))

    def test_an_unknown_verdict_is_refused_programmatically_too(self):
        """The second guard: `cmd_record` called directly bypasses argparse entirely."""
        import argparse

        args = argparse.Namespace(
            repo=str(self.repo), key="k", verdict="delete-it", server="1.32.2",
            reason=None, where=None, claim=None, tool=None, issue=None,
            upstream=None, checked=None,
        )
        self.assertEqual(1, LEDGER.cmd_record(args))
        self.assertEqual({}, LEDGER.read_ledger(self.repo))

    def test_a_later_row_supersedes_an_earlier_one_without_rewriting_it(self):
        self.record("--key", "k", "--verdict", "delegate", "--server", "1.32.1")
        self.record("--key", "k", "--verdict", "contradicted", "--server", "1.32.2")
        self.assertEqual("contradicted", LEDGER.read_ledger(self.repo)["k"]["verdict"])
        lines = (self.repo / "specs" / "mcp-coverage.jsonl").read_text().strip().splitlines()
        self.assertEqual(2, len(lines), "history is appended to, never rewritten")
        self.assertEqual("delegate", json.loads(lines[0])["verdict"])

    def test_a_malformed_line_does_not_sink_the_intact_rows(self):
        self.record("--key", "good", "--verdict", "delegate", "--server", "1.32.2")
        path = self.repo / "specs" / "mcp-coverage.jsonl"
        path.write_text("{not json\n" + path.read_text(), encoding="utf-8")
        self.assertIn("good", LEDGER.read_ledger(self.repo))


INDEX_A = "2026-07-29 11:11 UTC"
INDEX_B = "2026-08-04 09:02 UTC"


class VerdictsExpireOnTheServerVersion(unittest.TestCase):
    """Not on elapsed time: nothing the server said can change until it ships."""

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "specs").mkdir()
        LEDGER.main(["--repo", str(self.repo), "record", "--key", "old",
                     "--verdict", "keep-server-lacks-it", "--server", "1.32.1",
                     "--index", INDEX_A])
        LEDGER.main(["--repo", str(self.repo), "record", "--key", "current",
                     "--verdict", "delegate", "--server", "1.32.2", "--index", INDEX_A])

    def tearDown(self):
        self.tmp.cleanup()

    def stale(self, version, index=INDEX_A):
        argv = ["--repo", str(self.repo), "stale", "--server", version]
        if index:
            argv += ["--index", index]
        return LEDGER.main(argv)

    def test_an_unchanged_server_expires_nothing(self):
        """Exit 3 — the signal that a run has no re-asking to do."""
        LEDGER.main(["--repo", str(self.repo), "record", "--key", "old",
                     "--verdict", "keep-server-lacks-it", "--server", "1.32.2",
                     "--index", INDEX_A])
        self.assertEqual(3, self.stale("1.32.2"))

    def test_a_bumped_server_expires_the_older_rows(self):
        self.assertEqual(0, self.stale("1.32.2"))

    def test_a_rollback_expires_them_too(self):
        """Any difference, not only a newer version — a downgrade changes the answers."""
        self.assertEqual(0, self.stale("1.32.1"))

    def test_an_empty_ledger_reports_nothing_to_expire(self):
        import tempfile

        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(3, LEDGER.main(["--repo", empty, "stale", "--server", "1.32.2"]))


class VerdictsAlsoExpireWhenTheDocsAreReindexed(unittest.TestCase):
    """The second axis, and the reason it exists.

    `server_version` versions the MCP server software; `index_built` versions the
    documentation corpus its tools answer from. Senzing can rebuild the corpus and ship
    no server release, so `search_docs` starts answering differently while the version
    sits still. Expiring on the server version alone would report "nothing to re-ask"
    for precisely the rows a re-index changed.
    """

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "specs").mkdir()
        self.record("stamped", "1.32.2", INDEX_A)

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, key, server, index=None):
        argv = ["--repo", str(self.repo), "record", "--key", key,
                "--verdict", "delegate", "--server", server]
        if index:
            argv += ["--index", index]
        return LEDGER.main(argv)

    def test_a_reindex_under_an_unchanged_server_expires_the_row(self):
        """The hole this axis closes."""
        self.assertEqual(0, LEDGER.main(["--repo", str(self.repo), "stale",
                                         "--server", "1.32.2", "--index", INDEX_B]))

    def test_the_same_index_under_the_same_server_expires_nothing(self):
        self.assertEqual(3, LEDGER.main(["--repo", str(self.repo), "stale",
                                         "--server", "1.32.2", "--index", INDEX_A]))

    def test_the_index_is_stored_on_the_row(self):
        self.assertEqual(INDEX_A, LEDGER.read_ledger(self.repo)["stamped"]["index_built"])

    def test_a_row_with_no_index_cannot_be_proved_current(self):
        """Unknown provenance is a reason to look, not a reason to pass by default."""
        self.record("unstamped", "1.32.2")
        reason = LEDGER.expiry_reason(
            LEDGER.read_ledger(self.repo)["unstamped"], "1.32.2", INDEX_A
        )
        self.assertIn("not recorded", reason)

    def test_an_unstamped_row_is_not_expired_when_no_index_is_supplied(self):
        """Nothing to compare against is not evidence of drift."""
        self.record("unstamped", "1.32.2")
        self.assertEqual(
            "", LEDGER.expiry_reason(LEDGER.read_ledger(self.repo)["unstamped"], "1.32.2")
        )

    def test_the_server_axis_is_named_in_the_reason(self):
        row = LEDGER.read_ledger(self.repo)["stamped"]
        self.assertIn("server", LEDGER.expiry_reason(row, "1.33.0", INDEX_A))

    def test_the_index_axis_is_named_in_the_reason(self):
        row = LEDGER.read_ledger(self.repo)["stamped"]
        self.assertIn("re-indexed", LEDGER.expiry_reason(row, "1.32.2", INDEX_B))


class AnUncheckedAxisIsReportedAsUnchecked(unittest.TestCase):
    """INV-163: a check that could not run is reported as skipped, never as passed.

    Omitting `--index` is legitimate — a caller may have no `search_docs` response to
    hand — but the result is partial, and a partial result relayed as a clean bill is
    how a re-indexed corpus gets skipped for a whole release cycle.
    """

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "specs").mkdir()
        LEDGER.main(["--repo", str(self.repo), "record", "--key", "k",
                     "--verdict", "delegate", "--server", "1.32.2", "--index", INDEX_A])

    def tearDown(self):
        self.tmp.cleanup()

    def stale_output(self, *extra):
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = LEDGER.main(["--repo", str(self.repo), "stale",
                                "--server", "1.32.2"] + list(extra))
        return code, buffer.getvalue()

    def test_omitting_the_index_warns_that_the_axis_was_not_checked(self):
        code, output = self.stale_output()
        self.assertEqual(3, code)
        self.assertIn("NOT checked", output)
        self.assertIn("index_built", output)

    def test_it_does_not_claim_both_axes_are_unchanged(self):
        _, output = self.stale_output()
        self.assertNotIn("neither axis", output)

    def test_supplying_the_index_drops_the_caveat(self):
        _, output = self.stale_output("--index", INDEX_A)
        self.assertNotIn("NOT checked", output)
        self.assertIn("neither axis", output)

    def test_recording_without_an_index_says_the_verdict_will_expire(self):
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            LEDGER.main(["--repo", str(self.repo), "record", "--key", "n",
                         "--verdict", "delegate", "--server", "1.32.2"])
        self.assertIn("no --index recorded", buffer.getvalue())


class InventoryScopeIsPinned(unittest.TestCase):
    """A drifted glob makes "found nothing" and "looked nowhere" identical."""

    @classmethod
    def setUpClass(cls):
        cls.hits = LEDGER.inventory(REPO_ROOT)
        cls.files = {h["where"].rsplit(":", 1)[0] for h in cls.hits}

    def test_the_sweep_is_not_vacuous(self):
        self.assertGreater(len(self.hits), 50, "the patterns or the globs have drifted")

    def test_shipped_skill_guidance_is_scanned(self):
        self.assertTrue(
            any("/skills/" in f for f in self.files),
            "the plugin's skill files are the whole point of the sweep",
        )

    def test_invariants_are_scanned(self):
        """An invariant asserting a server limitation is the load-bearing case."""
        self.assertIn("specs/INVARIANTS.md", self.files)

    def test_the_example_recap_is_out_of_scope(self):
        """It records what one Bootcamper was told, not a claim the plugin asserts."""
        self.assertFalse(
            [f for f in self.files if "examples" in f],
            "docs/examples is a rendered fixture; delegating it would be meaningless",
        )

    def test_archived_specs_are_out_of_scope(self):
        others = [f for f in self.files if f.startswith("specs/") and f != "specs/INVARIANTS.md"]
        self.assertEqual([], others, "archived specs are history, not shipped guidance")

    def test_every_category_carries_its_owning_tool(self):
        """A lead a maintainer cannot route is a lead they have to re-derive."""
        for hit in self.hits:
            with self.subTest(category=hit["category"]):
                self.assertTrue(hit["tool"].strip())

    def test_a_category_filter_narrows_the_result(self):
        flags = LEDGER.inventory(REPO_ROOT, "flags")
        self.assertTrue(flags)
        self.assertEqual({"flags"}, {h["category"] for h in flags})


class TheSkillDocumentsWhatTheScriptEnforces(unittest.TestCase):
    """The six verdicts are a contract between SKILL.md and the ledger."""

    def setUp(self):
        self.text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_every_verdict_the_script_accepts_is_documented(self):
        for verdict in LEDGER.VERDICTS:
            with self.subTest(verdict=verdict):
                self.assertIn(verdict, self.text)

    def test_the_skill_names_no_verdict_the_script_would_reject(self):
        import re

        cited = set(re.findall(r"`(keep-[a-z-]+|delegate|contradicted|retire-[a-z-]+|not-a-senzing-fact)`",
                               self.text))
        self.assertTrue(cited)
        self.assertEqual(set(), cited - set(LEDGER.VERDICTS))

    def test_it_is_a_maintainer_tool_that_writes_no_plugin_code(self):
        self.assertIn("Maintainer tool", self.text)
        self.assertRegex(self.text, r"[Nn]ever modify plugin code")


class ProvenanceIsReadFromEitherEra(unittest.TestCase):
    """⛔ #114 replaced `--spec` with `--issue`; the 29 rows already written keep `spec`.

    The ledger is append-only and read last-wins, so migrating those rows is the one thing
    its shape forbids. `produced_by()` therefore reads both field names, and this pins that
    a pre-#114 row does not silently lose its provenance.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "specs").mkdir()
        self.addCleanup(self.tmp.cleanup)

    def test_a_historical_spec_row_still_reports_what_it_produced(self):
        row = {"key": "k", "verdict": "delegate", "server_version": "1.32.2",
               "checked": "2026-08-01", "spec": "specs/some-delegation.md"}
        produced = LEDGER.produced_by(row)
        self.assertIsNotNone(
            produced,
            "a pre-#114 row carrying `spec` reports no provenance. 29 real rows are in this "
            "shape; reading only `issue` silently drops what they produced")
        self.assertIn("specs/some-delegation.md", produced)

    def test_a_new_issue_row_reports_the_issue_number(self):
        produced = LEDGER.produced_by({"key": "k", "issue": 142})
        self.assertEqual("#142", produced)

    def test_a_keep_row_produced_nothing_and_says_so(self):
        """⚠️ Not every row produced something -- a keep is the normal case (INV-265)."""
        self.assertIsNone(
            LEDGER.produced_by({"key": "k", "verdict": "keep-by-design"}),
            "a row that produced nothing reports something anyway, so the caller cannot "
            "distinguish 'nothing was filed' from 'a filing was recorded'")

    def test_the_record_cli_no_longer_accepts_spec(self):
        """⛔ The flag is gone, not merely unused: writing new `spec` rows would re-fork it."""
        parser_src = (Path(LEDGER.__file__).read_text(encoding="utf-8")
                      if hasattr(LEDGER, "__file__") else "")
        self.assertNotIn(
            'add_argument("--spec"', parser_src,
            "`--spec` is still a CLI flag. This skill files issues now (#114); leaving the "
            "flag lets a run write a row pointing into the frozen archive")


if __name__ == "__main__":
    unittest.main()
