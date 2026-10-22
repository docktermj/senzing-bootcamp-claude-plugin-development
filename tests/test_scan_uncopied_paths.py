"""Tests for `scan_uncopied_paths.py`, graduation Step 2's scan of the copied code (#755).

The scanner searches the text of every file under `production/src/` for a project-relative
path that exists in the bootcamp project and not in `production/`, and prints one
`<file>: <path>` line per hit. Graduation turns each line into a migration-checklist item, so
what is pinned here is what reaches that checklist:

- the two #755 reads are found (`config/bootcamp_preferences.yaml` from a loader,
  `data/truth/scenario_truth.json` from a query program), whatever language the file is in;
- a path production has (the registry projection, `data/senzing-ready/`) is not a hit, nor is a
  path the project does not have, a URL's path, or one under build output;
- `\\` separators and a leading `./` are read as the same path, so a program written on Windows
  is scanned like one written anywhere else;
- no hit prints nothing on stdout, and a missing production directory exits 1.

Each fixture is built in a temporary directory with `pathlib`, and the script is run with this
interpreter, so the test runs the same on Linux, macOS and Windows.

No phrase-level pattern (#755): the only lines read are the scanner's stdout, one
`<file>: <path>` record per line, and the script's Python source, parsed with `ast`; no
Markdown prose is matched here.

INV-401 names this file as an enforcer of graduation Step 2's scan. It establishes what the
bundled scanner reports on built fixtures; it does not establish that a live graduation runs it
or turns each hit into a checklist item, which only `dry-run` phase 3 observes.

Run:  python3 -m unittest discover -s tests
"""
import ast
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "scan_uncopied_paths.py"


def load():
    spec = importlib.util.spec_from_file_location("scan_uncopied_paths_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


LOADER = '''PREFS = "config/bootcamp_preferences.yaml"
REGISTRY = "config/data_sources.yaml"
INPUT = "data/senzing-ready/"
DOCS = "https://example.com/config/bootcamp_preferences.yaml"
'''

QUERY = '''String truth = "data/truth/scenario_truth.json";
'''


class Project:
    """A bootcamp project after Step 2's copy, in a temporary directory."""

    def __init__(self, root):
        self.root = root
        self.production = root / "production"
        write(root / "config" / "bootcamp_preferences.yaml", "database_type: postgresql\n")
        write(root / "config" / "data_sources.yaml", "version: 1\n")
        write(root / "data" / "truth" / "scenario_truth.json", "{}\n")
        write(root / "data" / "senzing-ready" / "customers.jsonl", "{}\n")
        write(self.production / "config" / "data_sources.yaml", "version: 1\n")
        write(self.production / "data" / "senzing-ready" / "customers.jsonl", "{}\n")
        write(self.production / "src" / "load" / "loader.py", LOADER)
        write(self.production / "src" / "query" / "Truth.java", QUERY)

    def run(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--project-dir", str(self.root)]
                              + list(args), capture_output=True, text=True)


class TheScanFindsWhatGraduationLeftBehind(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Project(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_755_reads_are_each_one_line(self):
        result = self.project.run()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            ["src/load/loader.py: config/bootcamp_preferences.yaml",
             "src/query/Truth.java: data/truth/scenario_truth.json"],
            result.stdout.splitlines(),
            "each line names the copied file and the path it reads; the registry, the "
            "senzing-ready input and the URL are not hits")
        self.assertIn("2 hit(s)", result.stderr)

    def test_no_hit_prints_nothing(self):
        """Negative control: the same tree with the two reads copied has no hit."""
        write(self.project.production / "config" / "bootcamp_preferences.yaml", "x\n")
        write(self.project.production / "data" / "truth" / "scenario_truth.json", "{}\n")
        result = self.project.run()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout, "no hit adds no checklist item")
        self.assertIn("0 hit(s)", result.stderr)

    def test_a_path_the_project_does_not_have_is_not_a_hit(self):
        write(self.project.production / "src" / "load" / "out.py",
              'LOG = "logs/never_written.log"\nTYPE = "application/json"\n')
        self.assertNotIn("out.py", self.project.run().stdout)

    def test_windows_separators_and_a_leading_dot_are_the_same_path(self):
        write(self.project.production / "src" / "query" / "Truth.cs",
              'var a = "data\\\\truth\\\\scenario_truth.json";\nvar b = "./config/bootcamp_preferences.yaml";\n')
        lines = self.project.run().stdout.splitlines()
        self.assertIn("src/query/Truth.cs: data/truth/scenario_truth.json", lines)
        self.assertIn("src/query/Truth.cs: config/bootcamp_preferences.yaml", lines)

    def test_build_output_and_binary_files_are_skipped(self):
        write(self.project.production / "src" / "load" / "classes" / "Loader.txt", LOADER)
        write(self.project.production / "src" / "load" / "node_modules" / "x.js", LOADER)
        blob = self.project.production / "src" / "load" / "loader.bin"
        blob.write_bytes(b"\0config/bootcamp_preferences.yaml")
        out = self.project.run().stdout
        self.assertNotIn("classes", out)
        self.assertNotIn("node_modules", out)
        self.assertNotIn("loader.bin", out)

    def test_a_missing_production_directory_exits_1(self):
        result = self.project.run("--production-dir", str(self.project.root / "absent"))
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("does not exist", result.stderr)

    def test_the_default_production_directory_is_under_the_project(self):
        """Graduation runs it with no arguments from the project root."""
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=str(self.project.root),
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(2, len(result.stdout.splitlines()))


class TheTokenizer(unittest.TestCase):

    def test_candidates(self):
        candidates = load().candidates
        self.assertEqual(["config/bootcamp_progress.json"],
                         list(candidates('open("config/bootcamp_progress.json")')))
        self.assertEqual([], list(candidates("see https://host/config/x.yaml")))
        self.assertEqual([], list(candidates("a parent-relative ../data/y")))
        self.assertEqual(["data/raw/"], list(candidates("glob('data/raw/*.csv')")))

    def test_the_script_is_stdlib_only(self):
        """Cross-platform (INV-001): it imports nothing outside the standard library."""
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module.split(".")[0])
        self.assertEqual({"__future__", "argparse", "re", "sys", "pathlib"}, imports)


if __name__ == "__main__":
    unittest.main()
