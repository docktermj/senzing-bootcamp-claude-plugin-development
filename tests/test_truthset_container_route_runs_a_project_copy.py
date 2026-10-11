"""On SDK setup's container route, Truth Set's Python path runs a project copy of the server.

Issue #490. `phase1-visualization.md` 2.1 resolved the reference server as
`${CLAUDE_PLUGIN_ROOT}/scripts/senzing_viz_server.py`, a **host** path. Module 2 creates the SDK
container with only the project mounted, so the plugin's `scripts/` does not exist inside it, and
the snapshot build (2.2), the live launch (2.3) and the Python fallback could not reach the server.
Copying the one file is not enough either: it loads `brand_tokens.py` and the vendored D3 from
beside its own file, and without D3 it refuses to render (INV-091).

The fix is a copy, not a mount: before each in-container run, the three files are copied from the
plugin's `scripts/` on the host into `data/temp/truthset-viz/` under the project, keeping their
layout. These tests pin it two ways:

1. **The prose.** 2.1 holds the one anchored statement (INV-300): the three files, the
   destination and its `vendor/` layout, the in-container `<viz-server-path>`, the refresh before
   each run, and the stop on a failed copy. 2.2, 2.3, the Python fallback and the contract's
   "Serving from the SDK container" each link the anchor and carry no second copy of the command.
   A negative control strips each link in turn and sees the check report it.
2. **The behavior.** The copy command is read out of 2.1 and run with `sh` against the real
   plugin, in a temporary project. The copied server then passes its INV-091 D3 check: run with
   `--no-serve`, it gets past the check and stops at engine settings (exit 2), so no Senzing SDK
   is needed. It resolves D3 and `brand_tokens.py` beside the copy, not in the plugin. With the
   copy's `vendor/` removed it refuses, exit 1, naming `d3.v7.min.js`, and writes no snapshot.
   Re-running the command overwrites a stale copy, and a plugin missing the D3 asset makes the
   command exit non-zero, which is the failed copy 2.1 says stops the step.

It does **not** establish that a real container sees the copy at `/app/data/temp/truthset-viz/`:
no container runs in this suite. That rests on the project mount Module 2 creates.

Stdlib only; the server is run from a file path, never imported as an installed package (INV-108).
Prose is read wrap-aware (INV-346).

Enforces **INV-091** and **INV-300**.

Run:  python3 -m unittest discover -s tests
"""
import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _wrapped_text import match_lines as _match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"
MODULE_3B = PLUGIN / "skills" / "module-03b-truthset-visualization"
PHASE1 = MODULE_3B / "phase1-visualization.md"
CONTRACT = MODULE_3B / "visualization-api-reference.md"

ANCHOR = '<a id="container-route-server-copy"></a>'
COPY_DIR = "data/temp/truthset-viz"
#: The three files, as paths relative to the plugin's `scripts/` and to the copy's directory.
FILES = ("senzing_viz_server.py", "brand_tokens.py", "vendor/d3.v7.min.js")
ASSET_NAME = "d3.v7.min.js"

#: Each site that runs the server on the container route: (label, file, start, end, link).
LOCAL_LINK = r"\]\(#container-route-server-copy\)"
SITES = (
    ("2.2 snapshot build", PHASE1, "### 2.2 Always produce the standalone snapshot first",
     "### 2.3 Start the live web app", LOCAL_LINK),
    ("2.3 live launch", PHASE1, "### 2.3 Start the live web app", "### 2.4 Verify the endpoints",
     LOCAL_LINK),
    ("Python fallback", PHASE1, "## Fallback: guarantee the snapshot if the live server cannot run",
     "When the bootcamper has finished exploring", LOCAL_LINK),
    ("Serving from the SDK container", CONTRACT, '<a id="container-route"></a>',
     "### Identifying the server process",
     r"\]\(phase1-visualization\.md#container-route-server-copy\)"),
)


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` (INV-346), taking a pattern string."""
    return _match_lines(text, re.compile(pattern))


def read(path):
    return Path(path).read_text(encoding="utf-8")


def between(text, start, end):
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


def section_2_1():
    return between(read(PHASE1), "### 2.1 Choose the path", "### 2.2 ")


def canonical_statement():
    """From 2.1's anchor to the next bullet of 2.1's top-level list."""
    section = section_2_1()
    begin = section.index(ANCHOR)
    return section[begin:section.index("\n- **Any other language**", begin)]


def copy_command():
    """The one fenced `bash` block in the canonical statement, indentation removed."""
    blocks = re.findall(r"```bash\n(.*?)\n[ \t]*```", canonical_statement(), re.S)
    if len(blocks) != 1:
        raise AssertionError(f"expected one bash block in 2.1's statement, found {len(blocks)}")
    return "\n".join(line[2:] if line.startswith("  ") else line
                     for line in blocks[0].splitlines())


def sites():
    for label, path, start, end, link in SITES:
        yield label, between(read(path), start, end), link


def server_env():
    env = {k: v for k, v in os.environ.items()
           if k not in ("SENZING_ENGINE_CONFIGURATION_JSON", "PYTHONPATH")}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


class TwoOneHoldsTheOneStatement(unittest.TestCase):
    def test_one_anchor_in_the_python_bullet(self):
        self.assertEqual(read(PHASE1).count(ANCHOR), 1)
        self.assertIn(ANCHOR, section_2_1())

    def test_it_claims_canonical_ownership_and_cites_inv_300(self):
        self.assertTrue(match_lines(canonical_statement(),
                                    r"This\s+is the canonical statement of the copy.*\(INV-300\)"))

    def test_it_is_scoped_to_the_container_route(self):
        self.assertTrue(match_lines(canonical_statement(),
                                    r"\(INV-091, INV-260\) On SDK setup's container route \(the `docker` path"))
        self.assertTrue(match_lines(section_2_1(), r"every\s+route except SDK setup's container"))
        self.assertTrue(match_lines(canonical_statement(),
                                    r"Native routes run the resolved plugin path with no copy"))

    def test_it_names_the_three_files_and_the_destination_layout(self):
        statement = canonical_statement()
        for pattern in (r"`senzing_viz_server\.py`", r"`brand_tokens\.py`",
                        r"`vendor/d3\.v7\.min\.js`", r"`data/temp/truthset-viz/`",
                        r"`data/temp/truthset-viz/vendor/d3\.v7\.min\.js`",
                        r"keeping\s+their relative layout and overwriting any earlier copy"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(statement, pattern), pattern)

    def test_it_names_the_in_container_server_path(self):
        self.assertTrue(match_lines(
            canonical_statement(),
            r"The in-container `<viz-server-path>` is then\s+"
            r"`data/temp/truthset-viz/senzing_viz_server\.py`"))

    def test_it_refreshes_before_each_run_and_stops_on_a_failed_copy(self):
        statement = canonical_statement()
        for pattern in (r"Before \*\*each\*\* in-container run",
                        r"Copy every time, with no version check",
                        r"A failed copy stops the step \(INV-091\)",
                        r"do not run the server, neither the earlier copy\s+nor a partial one",
                        r"A copy, not a mount"):
            with self.subTest(pattern=pattern):
                self.assertTrue(match_lines(statement, pattern), pattern)


class EveryRunSiteLinksTheStatement(unittest.TestCase):
    def test_each_site_is_found_and_links_the_anchor(self):
        for label, text, link in sites():
            with self.subTest(site=label):
                self.assertTrue(match_lines(text, link), f"{label} must link 2.1's statement")

    def test_negative_control_a_site_without_the_link_is_caught(self):
        for label, text, link in sites():
            with self.subTest(site=label):
                stripped = re.sub(r"\]\([^)]*#container-route-server-copy\)", "]", text)
                self.assertFalse(match_lines(stripped, link))

    def test_no_site_restates_the_copy(self):
        """INV-300: a pointing site carries no second copy of the command or the destination."""
        for label, text, _ in sites():
            with self.subTest(site=label):
                self.assertEqual(match_lines(text, r"\bcp\s+\""), [])
                self.assertEqual(match_lines(text, r"data/temp/truthset-viz"), [])
                self.assertEqual(match_lines(text, r"mkdir -p"), [])

    def test_the_contract_link_resolves_to_a_real_file(self):
        self.assertTrue((CONTRACT.parent / "phase1-visualization.md").is_file())


@unittest.skipUnless(shutil.which("sh"), "needs a POSIX sh to run 2.1's copy command")
class TheCopiedLayoutRuns(unittest.TestCase):
    """Run 2.1's own command against the real plugin, in a temporary project."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "project"
        self.project.mkdir()
        self.copy = self.project / COPY_DIR

    def tearDown(self):
        self.tmp.cleanup()

    def run_copy(self, plugin_root=PLUGIN):
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin_root))
        return subprocess.run(["sh", "-c", copy_command()], cwd=str(self.project), env=env,
                              capture_output=True, text=True, timeout=60)

    def run_server(self, snapshot):
        return subprocess.run(
            [sys.executable, str(self.copy / "senzing_viz_server.py"),
             "--no-serve", "--snapshot", str(snapshot)],
            cwd=str(self.project), env=server_env(), capture_output=True, text=True,
            encoding="utf-8", timeout=120)

    def test_the_command_copies_the_three_files_in_their_layout(self):
        result = self.run_copy()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in FILES:
            with self.subTest(file=name):
                self.assertTrue(filecmp.cmp(SCRIPTS / name, self.copy / name, shallow=False))

    def test_the_copied_server_passes_its_d3_check(self):
        """It gets past the INV-091 check and stops at engine settings, before any engine work."""
        self.assertEqual(self.run_copy().returncode, 0)
        snapshot = self.project / "docs" / "out.html"
        result = self.run_server(snapshot)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn(ASSET_NAME, result.stderr)
        self.assertIn("engine settings", result.stderr.lower())
        self.assertFalse(snapshot.exists())

    def test_the_copy_resolves_d3_and_brand_tokens_beside_itself(self):
        self.assertEqual(self.run_copy().returncode, 0)
        probe = (
            "import importlib.util, sys\n"
            "spec = importlib.util.spec_from_file_location('viz_copy', sys.argv[1])\n"
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
            "import brand_tokens\n"
            "print(m._d3_path()); print(brand_tokens.__file__)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe, str(self.copy / "senzing_viz_server.py")],
            cwd=str(self.project), env=server_env(), capture_output=True, text=True,
            encoding="utf-8", timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        d3_path, tokens_path = result.stdout.split()
        self.assertEqual(Path(d3_path).resolve(), (self.copy / "vendor" / ASSET_NAME).resolve())
        self.assertEqual(Path(tokens_path).resolve(), (self.copy / "brand_tokens.py").resolve())

    def test_negative_control_without_vendor_the_copy_refuses(self):
        self.assertEqual(self.run_copy().returncode, 0)
        shutil.rmtree(self.copy / "vendor")
        snapshot = self.project / "docs" / "out.html"
        result = self.run_server(snapshot)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(ASSET_NAME, result.stderr)
        self.assertIn(str(self.copy / "vendor"), result.stderr)
        self.assertNotIn("engine settings", result.stderr.lower())
        self.assertFalse(snapshot.exists())

    def test_re_running_overwrites_a_stale_copy(self):
        self.assertEqual(self.run_copy().returncode, 0)
        for name in FILES:
            (self.copy / name).write_text("stale\n", encoding="utf-8")
        self.assertEqual(self.run_copy().returncode, 0)
        for name in FILES:
            with self.subTest(file=name):
                self.assertTrue(filecmp.cmp(SCRIPTS / name, self.copy / name, shallow=False))

    def test_a_plugin_missing_the_d3_asset_fails_the_copy(self):
        fake = Path(self.tmp.name) / "plugin"
        (fake / "scripts").mkdir(parents=True)
        for name in FILES[:2]:
            shutil.copy2(SCRIPTS / name, fake / "scripts" / name)
        result = self.run_copy(fake)
        self.assertNotEqual(result.returncode, 0,
                            "a missing source file must fail the copy, so the step stops")
        self.assertFalse((self.copy / "vendor" / ASSET_NAME).exists())


if __name__ == "__main__":
    unittest.main()
