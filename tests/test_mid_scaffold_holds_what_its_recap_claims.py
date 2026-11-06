"""The mid-bootcamp scaffold holds every data and config file its own recap names (#872).

`scaffold_project.py`'s mid mode builds a project at Module 5 step 11 whose recap says
`data/raw/customers.csv` was collected, registered in `config/data_sources.yaml` and
profiled, but it wrote none of them. On 2026-11-06 an `/auto-test --seed mid` walk found the
guide unable to resume step 11; it downloaded a different file and closed Module 5 with its
steps unrun (`specs/IMPLEMENTED.md` -> `auto-test-walk-2026-11-06`).

Checks, on a project built in a temporary directory:

1. Every backticked `data/…` or `config/…` path in the recap and the recap checkpoint the
   scaffold writes exists in the built project.
2. The registry's `CUSTOMERS` entry points at that file, and its `record_count` and
   `file_size_bytes` match the file.
3. The mapping checkpoint Module 5 resumes from (`config/mapping_state_<source>.json`) names
   the same source file and has profile and plan done.

Negative control, run when written: removing the `customers.csv` write fails checks 1 and 2.

⚠️ **What this does NOT establish:** that a live guide resumes step 11 from these files; only
a walk shows that.

No phrase-level pattern (#872): its one line read counts the rows of a CSV fixture.

Stdlib only; the scaffold is loaded by file path (INV-108).
"""
import contextlib
import importlib.util
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD = REPO_ROOT / ".claude" / "skills" / "dry-run" / "scaffold_project.py"
NAMED_PATH = re.compile(r"`((?:data|config)/[^`\s]+)`")


def load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold_872", SCAFFOLD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MidScaffoldHoldsWhatItsRecapClaims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scaffold = load_scaffold()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "project"
        with contextlib.redirect_stdout(io.StringIO()):
            cls.scaffold.build(cls.root, fresh=False, seeded=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_named_path_exists(self):
        text = (self.root / "docs/bootcamp_recap.md").read_text(encoding="utf-8") + \
            (self.root / "docs/progress/recap_checkpoint.md").read_text(encoding="utf-8")
        named = sorted(set(NAMED_PATH.findall(text)))
        self.assertIn("data/raw/customers.csv", named)
        self.assertIn("config/data_sources.yaml", named)
        missing = [p for p in named if not (self.root / p).exists()]
        self.assertEqual(missing, [])

    def test_the_registry_entry_matches_the_file(self):
        data = (self.root / "data/raw/customers.csv").read_bytes()
        registry = (self.root / "config/data_sources.yaml").read_text(encoding="utf-8")
        self.assertIn("file_path: data/raw/customers.csv", registry)
        self.assertIn(f"record_count: {len(data.decode().splitlines()) - 1}\n", registry)
        self.assertIn(f"file_size_bytes: {len(data)}\n", registry)
        self.assertIn("mapping_status: in_progress", registry)

    def test_the_mapping_checkpoint_resumes_at_map(self):
        state = json.loads(
            (self.root / "config/mapping_state_customers.json").read_text(encoding="utf-8"))
        self.assertEqual(state["source_file"], "data/raw/customers.csv")
        self.assertEqual(state["data_source"], "CUSTOMERS")
        self.assertEqual(state["completed_steps"], ["profile", "plan"])

    def test_the_progress_file_is_at_module_5_step_11(self):
        progress = json.loads(
            (self.root / "config/bootcamp_progress.json").read_text(encoding="utf-8"))
        self.assertEqual((progress["current_module"], progress["current_step"]),
                         ("data_quality_mapping", "11"))


if __name__ == "__main__":
    unittest.main()
