r"""The citation census behind `compact-dev-environment`.

That skill proposes invariant merges, merges test traversals and prunes feedback, and it
reads the frozen specs archive without changing it. Each change it makes or proposes can
break a reference, and the reference density here rules out doing it by eye: 4,614 live
`INV-NNN` citations across shipped plugin text, specs, tests and skills on 2026-07-30.

What is pinned here is the census's *accuracy*, because every judgment the skill makes
rests on it. In particular the template placeholder: `INVARIANTS.md` documents its own
format with a literal `- **INV-NNN** — <single testable MUST/ALWAYS condition.>` line,
and a naive `grep '^- \*\*INV-'` counts it as a real invariant. That off-by-one was live
in an ad-hoc survey before this script existed, and an inflated count is exactly the kind
of error that makes a compaction report look thorough while being wrong.

`verify` is the safety net the skill runs after every change, so its failure modes are
pinned too — a check that cannot fail protects nothing.

This file is excluded from the scan it tests (citations.py: ignore-file) — its
fixture identifiers are not references to anything.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / ".claude" / "skills" / "compact-dev-environment"
SCRIPT = SKILL / "citations.py"


def load():
    spec = importlib.util.spec_from_file_location("citations_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CIT = load()


def scratch(tmp, invariants="", ledger="", specs=(), feedback=None):
    """A minimal repo skeleton the script can be pointed at."""
    root = Path(tmp)
    (root / "specs").mkdir(parents=True, exist_ok=True)
    (root / "specs" / "INVARIANTS.md").write_text(invariants, encoding="utf-8")
    (root / "specs" / "IMPLEMENTED.md").write_text(ledger, encoding="utf-8")
    for name, body in specs:
        (root / "specs" / (name + ".md")).write_text(body, encoding="utf-8")
    if feedback is not None:
        fb = root / "feedback"
        fb.mkdir(exist_ok=True)
        archives, entries = feedback
        for name, body in archives:
            (fb / name).write_text(body, encoding="utf-8")
        (fb / "PROCESSED.jsonl").write_text(
            "".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8"
        )
    return root


class TheTemplatePlaceholderIsNotAnInvariant(unittest.TestCase):
    """`INV-NNN` documents the format; counting it inflates every downstream number."""

    def test_the_real_file_excludes_the_placeholder(self):
        defined = CIT.defined_invariants(REPO_ROOT)
        self.assertNotIn("INV-NNN", defined)
        self.assertTrue(all(d[4:].isdigit() for d in defined), defined[:5])

    def test_a_placeholder_line_is_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants=(
                "- **INV-NNN** — <single testable MUST/ALWAYS condition.>\n"
                "- **INV-001** — a real one.\n"
            ))
            self.assertEqual(["INV-001"], CIT.defined_invariants(root))

    def test_the_real_corpus_is_actually_being_read(self):
        """Guard the guard: a drifted path would make every count zero and look calm."""
        self.assertGreater(len(CIT.defined_invariants(REPO_ROOT)), 100)
        self.assertGreater(sum(sum(c.values()) for c in
                               CIT.citations_by_area(REPO_ROOT).values()), 1000)


class CitationsAreCountedByArea(unittest.TestCase):
    def test_invariants_md_is_excluded_from_its_own_census(self):
        """Its cross-references would drown the signal: who depends on this from outside."""
        cited = CIT.citations_by_area(REPO_ROOT)
        for counts in cited.values():
            self.assertNotIn("invariants", counts)

    def test_shipped_plugin_text_is_scanned(self):
        cited = CIT.citations_by_area(REPO_ROOT)
        self.assertTrue(any("plugin" in c for c in cited.values()),
                        "the plugin cites invariants; a census blind to it is useless")

    def test_tests_are_scanned(self):
        cited = CIT.citations_by_area(REPO_ROOT)
        self.assertTrue(any("tests" in c for c in cited.values()))


class VerifyCatchesWhatCompactionBreaks(unittest.TestCase):
    """Each failure mode corresponds to a real operation the skill performs."""

    def run_verify(self, root):
        import argparse

        return CIT.cmd_verify(argparse.Namespace(repo=str(root)))

    def test_a_clean_skeleton_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a rule.\n", ledger="")
            self.assertEqual(0, self.run_verify(root))

    def test_a_citation_of_a_deleted_invariant_is_caught(self):
        """The signature of a botched merge or a half-finished renumber."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a rule.\n")
            (root / "tests").mkdir()
            (root / "tests" / "t.py").write_text("# see INV-999\n", encoding="utf-8")
            self.assertEqual(2, self.run_verify(root))

    def test_a_dangling_source_reference_is_caught(self):
        """Deleting a spec an invariant names as its Source orphans the provenance."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a rule. (Source: `gone`, 2026-07-30.)\n")
            self.assertEqual(2, self.run_verify(root))

    def test_a_source_resolved_by_an_archived_spec_passes(self):
        """Archiving is the sanctioned move; it must not read as a break."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a rule. (Source: `kept`, 2026-07-30.)\n")
            (root / "specs" / "archive").mkdir()
            (root / "specs" / "archive" / "kept.md").write_text("x", encoding="utf-8")
            self.assertEqual(0, self.run_verify(root))

    def test_a_source_resolved_by_a_ledger_entry_passes(self):
        """Some Sources name an audit recorded only in the ledger, never a spec file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(
                tmp,
                invariants="- **INV-001** — a rule. (Source: `deep-dive-audit`, 2026-07-30.)\n",
                ledger="## deep-dive-audit\n\n- **Implemented:** 2026-07-30\n",
            )
            self.assertEqual(0, self.run_verify(root))

    def test_a_duplicate_invariant_id_is_caught(self):
        """Two definitions of one address — the worst outcome of a careless merge."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a.\n- **INV-001** — b.\n")
            self.assertEqual(2, self.run_verify(root))

    def test_an_unledgered_feedback_archive_is_caught(self):
        """Pruning it would lose the only record that it was processed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a rule.\n",
                           feedback=([("FEEDBACK_1.md", "x")], []))
            self.assertEqual(2, self.run_verify(root))

    def test_a_ledgered_feedback_archive_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a rule.\n",
                           feedback=([("FEEDBACK_1.md", "x")],
                                     [{"entry_id": "a", "archive": "FEEDBACK_1.md"}]))
            self.assertEqual(0, self.run_verify(root))

    def test_the_live_repo_verifies_clean(self):
        """If this fails, something already dangles — fix it before compacting."""
        self.assertEqual(0, self.run_verify(REPO_ROOT))


class TheFeedbackLedgerIsReadLastWins(unittest.TestCase):
    """`PROCESSED.jsonl` is append-only; a disposition is corrected by a later line.

    A reader that treats every line as a distinct entry reports the *superseded* value
    next to the current one. On 2026-07-31 `census` did exactly that, reported a phantom
    undisposed entry whose very next ledger line already named the right spec, and the
    compaction run "fixed" it with a redundant no-op append. These assert the collapse
    behaviorally — a raw-line reader passes none of them.
    """

    UNRECORDED = {"entry_id": "e1", "title": "t", "archive": "F_1.md",
                  "disposition": "unrecorded"}
    CORRECTED = {"entry_id": "e1", "title": "t", "archive": "F_1.md",
                 "disposition": "specs/real-spec.md"}

    def state(self, entries):
        with tempfile.TemporaryDirectory() as tmp:
            root = scratch(tmp, invariants="- **INV-001** — a rule.\n",
                           feedback=([("F_1.md", "x")], entries))
            return CIT.feedback_state(root)

    def test_a_superseding_line_replaces_the_disposition_it_corrects(self):
        _archives, entries, lines = self.state([self.UNRECORDED, self.CORRECTED])
        self.assertEqual(2, lines, "both lines must still be read")
        self.assertEqual(1, len(entries), "one entry_id is one entry, not two")
        self.assertEqual("specs/real-spec.md", entries[0]["disposition"])

    def test_the_earlier_line_does_not_win(self):
        """Order matters: the fix is last-wins, not first-non-unrecorded."""
        _archives, entries, _lines = self.state([self.CORRECTED, self.UNRECORDED])
        self.assertEqual("unrecorded", entries[0]["disposition"],
                         "a later line wins even when it is the less complete one")

    def test_distinct_entries_are_not_collapsed_together(self):
        other = dict(self.CORRECTED, entry_id="e2")
        _archives, entries, lines = self.state([self.UNRECORDED, self.CORRECTED, other])
        self.assertEqual(3, lines)
        self.assertEqual({"e1", "e2"}, {e["entry_id"] for e in entries})

    def test_an_entry_with_no_id_is_kept_rather_than_dropped(self):
        """It cannot be superseded, but it must still be counted and reported."""
        _archives, entries, _lines = self.state(
            [{"title": "no id", "archive": "F_1.md"}, {"title": "also none",
                                                       "archive": "F_1.md"}])
        self.assertEqual(2, len(entries), "id-less lines must not collapse onto each other")

    def test_the_live_ledger_has_no_effectively_undisposed_entry(self):
        """The real check Step 5 wants — run against the repo, not a fixture."""
        _archives, entries, _lines = CIT.feedback_state(REPO_ROOT)
        self.assertTrue(entries, "the scan is not vacuous")
        undisposed = [e.get("title") for e in entries
                      if e.get("disposition") in (None, "", "unrecorded")]
        self.assertEqual([], undisposed,
                         "every entry needs its spec link; correct one with "
                         "feedback_ledger.py annotate <entry_id> <disposition>")


class TheSkillDocumentsWhatTheScriptCannotProtect(unittest.TestCase):
    """The renumbering hazard is the reason the skill has a default, so it must be stated."""

    def setUp(self):
        self.text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_it_names_commit_messages_as_unprotectable(self):
        self.assertRegex(self.text, r"(?i)commit message")
        self.assertRegex(self.text, r"(?i)immutable|cannot be edited")

    def test_it_warns_that_renumbering_silently_repoints(self):
        """A wrong reference is worse than a dangling one, and only one is detectable."""
        self.assertRegex(self.text, r"(?is)silently.{0,60}different real invariant")

    def test_it_is_a_maintainer_tool_that_reports_before_changing(self):
        self.assertIn("Maintainer tool", self.text)
        self.assertRegex(self.text, r"(?i)report first, change second")

    def test_it_protects_rationale_from_being_compacted_away(self):
        """"Concise" must not eat the recorded defect that motivates each rule."""
        self.assertRegex(self.text, r"(?i)duplication \*across\* invariants")


if __name__ == "__main__":
    unittest.main()
