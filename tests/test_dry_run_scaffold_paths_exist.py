"""Every path the dry-run scaffold fabricates must be a path the plugin actually uses.

The scaffold builds a mid-bootcamp fixture tree so phase 2 can run the hooks and bundled
scripts against something realistic. A fixture at a filename the plugin never reads is
worse than no fixture: it looks like coverage. `--explain` says so itself — "Every fixture
is here because a naive one hid a defect".

One had drifted. The scaffold wrote `src/system_verification/records.jsonl`; System
verification Step 2 writes `src/system_verification/verification_data.jsonl`, and that is
the only spelling `plugins/` contains. So a mid-bootcamp dry run started *without* the file
the plugin looks for, and the fixture that exists to catch resume defects could not.

Nothing caught it because the scaffold is a maintainer tool under `.claude/` while the
repo's tests cover `plugins/`. This file closes that specific gap in the general form: a
project-relative path named in `FIXTURE_MAP` must appear somewhere under `plugins/`.

Stdlib only, and it never imports from `plugins/` (INV-108); the scaffold is loaded by
file path because `.claude/skills/dry-run` is not an importable package.

Source spec: `specs/dry-run-scaffold-uses-a-verification-filename-the-plugin-never-writes.md`.

No phrase-level pattern (#438): its line reads are the JSON lines of a scaffold's records, as #424
recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD = REPO_ROOT / ".claude" / "skills" / "dry-run" / "scaffold_project.py"
PLUGINS = REPO_ROOT / "plugins"

#: Directories whose contents are build artifacts, not plugin sources.
SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def load_scaffold():
    spec = importlib.util.spec_from_file_location("dry_run_scaffold", SCAFFOLD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plugin_corpus():
    """Every readable file under `plugins/`, concatenated. Big, but read once."""
    chunks = []
    for path in sorted(PLUGINS.rglob("*")):
        if not path.is_file() or SKIP_DIRS & set(path.parts):
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue          # binary asset; it cannot name a path
    return "\n".join(chunks)


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_scaffold_is_where_this_test_thinks_it_is(self):
        self.assertTrue(SCAFFOLD.is_file(), "scaffold_project.py moved")

    def test_the_fixture_map_is_populated(self):
        rows = load_scaffold().FIXTURE_MAP
        self.assertGreater(len(rows), 5, "FIXTURE_MAP looks empty — did its shape change?")

    def test_the_corpus_is_real(self):
        corpus = plugin_corpus()
        self.assertGreater(len(corpus), 100_000,
                           "the plugins/ corpus came back tiny; a path check against it "
                           "would pass by finding nothing to contradict")


class EveryFixturePathIsAPathThePluginUses(unittest.TestCase):
    def setUp(self):
        self.rows = load_scaffold().FIXTURE_MAP
        self.corpus = plugin_corpus()

    def test_each_path_appears_somewhere_under_plugins(self):
        checked = 0
        for display, path, modes, _why in self.rows:
            if path is None:
                continue          # a row annotating a key inside another fixture
            checked += 1
            with self.subTest(path=path):
                if path in self.corpus:
                    continue
                base, doc = self._variant_of(path)
                self.assertTrue(
                    base and doc,
                    "the scaffold writes %r (row %r, modes %s) and no file under "
                    "plugins/ names that path — the fixture exercises something the "
                    "plugin never touches.\n"
                    "  If it is a deliberate NEGATIVE VARIANT of a real fixture (a "
                    "deformed copy passed to a plugin script's own flag to drive a "
                    "specific gate), it must satisfy BOTH: its base path — this one with "
                    "the trailing `_suffix` removed — appears under plugins/, and the "
                    "variant filename is named in the dry-run phase docs so a maintainer "
                    "can find out which gate it reaches.\n"
                    "  base %r under plugins/: %s;  named in dry-run docs: %s"
                    % (path, display, sorted(modes),
                       self._base_path(path), bool(base), bool(doc)))
        self.assertGreater(checked, 5, "almost no rows carried a path to check")

    @staticmethod
    def _base_path(path):
        """`config/engine_config_incomplete.json` -> `config/engine_config.json`."""
        stem, dot, ext = path.rpartition(".")
        if not dot or "_" not in stem.rsplit("/", 1)[-1]:
            return path
        return stem.rsplit("_", 1)[0] + dot + ext

    def _variant_of(self, path):
        """(base-is-real, variant-is-documented) for a path absent from plugins/.

        ⚠️ Rescoped 2026-09-02, not loosened. `scaffold-engine-config-never-reaches-the-sdk-path`
        added `config/engine_config_incomplete.json`: a deliberately deformed copy of the real
        `config/engine_config.json`, passed to `senzing_viz_server.py --settings` to reach the
        config-completeness pre-flight (exit 2) while the default fixture reaches the SDK gate
        (exit 1). The plugin DOES read it -- when told to -- so the guard's premise ("a filename
        the plugin never reads") does not hold for it.

        ⛔ The two conditions together are what keep the teeth. The drift this file was written
        for, `src/system_verification/records.jsonl`, still fails: strip its suffix and the base
        is still absent from plugins/, so a plain typo cannot slip through by claiming to be a
        variant. And a variant nobody documented fails too, because a fixture whose gate is
        unwritten is the "looks like coverage" problem in a new costume.
        """
        base = self._base_path(path)
        base_is_real = base != path and base in self.corpus
        name = path.rsplit("/", 1)[-1]
        docs = (REPO_ROOT / ".claude" / "skills" / "dry-run").glob("*.md")
        documented = any(name in d.read_text(encoding="utf-8") for d in docs)
        return base_is_real, documented

    def test_the_verification_records_fixture_uses_the_plugins_spelling(self):
        """The specific drift, named, so a revert is unambiguous rather than generic."""
        paths = {row[1] for row in self.rows if row[1]}
        self.assertIn("src/system_verification/verification_data.jsonl", paths,
                      "the System verification fixture is not at the filename Step 2 writes")
        self.assertNotIn("src/system_verification/records.jsonl", paths,
                         "records.jsonl is a filename the plugin never uses")


class TheFixtureMatchesWhatStepTwoAsksFor(unittest.TestCase):
    """A right filename holding the wrong shape resumes into different nonsense."""

    def setUp(self):
        import json
        self.records = [json.loads(line)
                        for line in load_scaffold().RECORDS.splitlines() if line.strip()]

    def test_at_least_four_records(self):
        self.assertGreaterEqual(len(self.records), 4,
                                "Step 2 requires at least 4 records")

    def test_every_record_is_the_verify_source_with_a_unique_id(self):
        self.assertEqual({"VERIFY"}, {r["DATA_SOURCE"] for r in self.records},
                         "Step 2 gives every record a DATA_SOURCE of VERIFY")
        ids = [r["RECORD_ID"] for r in self.records]
        self.assertEqual(len(ids), len(set(ids)), "RECORD_IDs must be unique")

    def test_there_is_a_merge_cluster_and_a_distractor(self):
        names = [f["NAME_FULL"]
                 for r in self.records for f in r["FEATURES"] if "NAME_FULL" in f]
        self.assertEqual(len(self.records), len(names), "every record needs a name")
        surnames = [n.rsplit(" ", 1)[-1] for n in names]
        biggest = max(surnames.count(s) for s in set(surnames))
        self.assertGreaterEqual(biggest, 2,
                                "no merge cluster: no two records share a surname")
        self.assertGreaterEqual(len(set(surnames)), 2,
                                "no distractor: every record is the same person, so "
                                "nothing has to stay a singleton")

    def test_features_are_nested_and_addresses_are_not_mixed(self):
        """Entity Specification: features live in FEATURES; ADDR_FULL is never mixed with
        parsed ADDR_* fields in the same object (server 1.32.9, 2026-08-14)."""
        for record in self.records:
            with self.subTest(record_id=record["RECORD_ID"]):
                self.assertIsInstance(record.get("FEATURES"), list)
                for feature in record["FEATURES"]:
                    if "ADDR_FULL" in feature:
                        parsed = [k for k in feature
                                  if k.startswith("ADDR_") and k not in ("ADDR_FULL",
                                                                         "ADDR_TYPE")]
                        self.assertEqual([], parsed,
                                         "ADDR_FULL mixed with parsed address fields")

    def test_the_records_carry_no_root_level_features(self):
        """The old fixture put PRIMARY_NAME_FULL/ADDR_FULL at the record root."""
        for record in self.records:
            with self.subTest(record_id=record["RECORD_ID"]):
                self.assertEqual({"DATA_SOURCE", "RECORD_ID", "FEATURES"},
                                 set(record),
                                 "features belong in FEATURES, not at the record root")


if __name__ == "__main__":
    unittest.main()
