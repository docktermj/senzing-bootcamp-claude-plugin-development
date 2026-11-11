"""The reference visualization server emits a self-contained copy for a project's server (#891).

Query, Visualize and Discover step 3c builds the project's `results_server` modeled on the
reference `scripts/senzing_viz_server.py`, and says that server never imports `brand_tokens.py`
and carries the token values itself (INV-081, INV-091). The reference imported `brand_tokens` at
runtime, so on a Python run the guide copied it into `src/server/` and edited the import out by
hand; one such edit put a docstring above `from __future__ import annotations` and broke the file.

The reference now has an `--emit-standalone <path>` mode, and step 3c's Python route runs it on
the host at first build. These tests enforce INV-422 (registered by the maintainer 2026-11-10) and
pin both; they read and run the code on Linux, and cannot establish that a live guide runs the
emit mode, which only `dry-run` phase 3 observes:

1. **The emitted file.** Emitted into a temporary directory, it compiles; it names no
   `brand_tokens`, no `sys.path.insert`, no `CLAUDE_PLUGIN_ROOT` and no plugin path; its shebang,
   module docstring and `from __future__ import annotations` come first, in that order; and it has
   no emit mode of its own. Imported with `brand_tokens` blocked, its palette constants and its
   `color_for_sources` output equal `brand_tokens`', and that `color_for_sources` is its own
   inlined function, not the token module's.
2. **The emit mode runs where step 3c runs it.** A copy of the reference in a directory with no
   `vendor/`, no `brand_tokens.py` and no engine settings, run in isolated mode with no Senzing SDK
   imported, still emits: the mode exits before the D3 check. The emitted file then starts and
   reaches that D3 check, which it fails visibly because its `vendor/` is not copied here.
3. **The edge cases.** An existing output file is refused, named and left byte-for-byte as it
   was. A source with no plugin-only block, or one that leaves the token import behind, writes
   nothing and leaves no temporary file. A write that fails at the rename leaves no partial file.
4. **Step 3c.** Its Python route runs the emit mode on the host with the plugin path and the
   skill-relative fallback (INV-252), writes `src/server/results_server.py`, stops on a failed emit
   rather than hand-copying, and puts a provenance note inside the docstring, never above
   `from __future__`. A negative control removes each element from an in-memory copy and sees it
   reported.
5. **The reference itself is unchanged in effect.** Loaded normally it still takes its palette
   from `brand_tokens` (INV-081), so Truth Set visualization's direct run is unaffected.

Nothing is served: no test starts a long-running server, and every file lands in a temporary
directory removed afterwards. Stdlib and `tempfile` only, with no shell; the server is loaded from
a file path, never installed (INV-108). CI runs on `ubuntu-latest` only, so this suite does
**not** verify the emit mode on macOS or Windows (INV-001, INV-163); it uses no POSIX-only call.

Enforces **INV-081** and **INV-252** at these sites.

Run:  python3 -m unittest discover -s tests
"""
import ast
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"
SCRIPT = SCRIPTS / "senzing_viz_server.py"
STEP_3C_FILE = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"

#: Text the emitted file must not contain: the token module, the path hack that found it, and
#: every spelling of the plugin's location, including this checkout's own absolute paths.
FORBIDDEN = ("brand_tokens", "sys.path.insert", "CLAUDE_PLUGIN_ROOT", "plugins/senzing-bootcamp",
             str(SCRIPTS), str(PLUGIN), str(REPO_ROOT), "plugin-only", "--emit-standalone",
             "emit_standalone")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_with_brand_tokens_blocked(path, name):
    """Load `path` while `import brand_tokens` raises ImportError."""
    saved = sys.modules.get("brand_tokens", None)
    had = "brand_tokens" in sys.modules
    sys.modules["brand_tokens"] = None  # `import brand_tokens` now raises ImportError
    try:
        return load(path, name)
    finally:
        if had:
            sys.modules["brand_tokens"] = saved
        else:
            del sys.modules["brand_tokens"]


def emit_in_process(viz, dest, source=None):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = viz.emit_standalone(str(dest), source=None if source is None else str(source))
    return code, out.getvalue(), err.getvalue()


#: Source lists for comparing `color_for_sources`: empty, the preferred sources, unknowns, and
#: enough sources to push past every fill, stroke, width and shade cycle.
SOURCE_LISTS = (
    [],
    ["CUSTOMERS"],
    ["CUSTOMERS", "REFERENCE", "WATCHLIST"],
    ["VENDORS", "EMPLOYEES", "", "  "],
    ["CUSTOMERS"] + ["SRC_%03d" % n for n in range(130)],
)


class TheEmittedFileStandsAlone(unittest.TestCase):
    """Criteria 1 and 5 of #891: what the emitted file contains, and its palette."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.viz = load(SCRIPT, "viz_reference_for_emit")
        cls.dest = Path(cls.tmp) / "src" / "server" / "results_server.py"
        cls.code, cls.out, cls.err = emit_in_process(cls.viz, cls.dest)
        cls.text = cls.dest.read_text(encoding="utf-8") if cls.dest.exists() else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_it_is_written_and_named(self):
        self.assertEqual(0, self.code, self.err)
        self.assertTrue(self.dest.is_file())
        self.assertIn(str(self.dest), self.out)
        self.assertEqual([self.dest.name], [p.name for p in self.dest.parent.iterdir()
                                            if p.name != "__pycache__"],
                         "the emit left a temporary file beside the server")

    def test_it_compiles(self):
        compile(self.text, str(self.dest), "exec")

    def test_it_names_no_plugin_import_or_path(self):
        for word in FORBIDDEN:
            with self.subTest(word=word):
                self.assertNotIn(word, self.text)

    def test_the_shebang_docstring_and_future_import_come_first(self):
        lines = self.text.splitlines()
        self.assertEqual("#!/usr/bin/env python3", lines[0])
        self.assertTrue(lines[1].startswith('"""'), "the module docstring is not line 2")
        tree = ast.parse(self.text)
        self.assertIsInstance(tree.body[0], ast.Expr)
        self.assertIsInstance(tree.body[0].value, ast.Constant)
        self.assertIsInstance(tree.body[0].value.value, str)
        self.assertIsInstance(tree.body[1], ast.ImportFrom)
        self.assertEqual("__future__", tree.body[1].module)
        self.assertEqual(["annotations"], [a.name for a in tree.body[1].names])

    def test_it_keeps_the_reference_docstring(self):
        self.assertEqual(ast.get_docstring(ast.parse(SCRIPT.read_text(encoding="utf-8")), False),
                         ast.get_docstring(ast.parse(self.text), False))

    def test_only_the_plugin_only_lines_differ(self):
        """Every emitted line is a reference line, in order: the copy adds nothing."""
        ref = iter(SCRIPT.read_text(encoding="utf-8").splitlines())
        for line in self.text.splitlines():
            for candidate in ref:
                if candidate == line:
                    break
            else:
                self.fail("the copy has a line the reference does not: %r" % line)

    def test_its_palette_equals_brand_tokens_with_the_import_blocked(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            import brand_tokens as bt
        finally:
            sys.path.remove(str(SCRIPTS))
        emitted = load_with_brand_tokens_blocked(self.dest, "emitted_results_server")
        self.assertEqual(bt.SOURCE_COLORS, emitted.SOURCE_COLORS)
        self.assertEqual(list(bt.FALLBACK_COLORS), emitted.FALLBACK_COLORS)
        self.assertEqual(list(bt.SOURCE_STROKES), emitted.SOURCE_STROKES)
        self.assertEqual(list(bt.SOURCE_STROKE_WIDTHS), emitted.SOURCE_STROKE_WIDTHS)
        self.assertEqual(list(bt.SOURCE_FILL_SHADES), emitted.SOURCE_FILL_SHADES)
        self.assertEqual({
            "bg": bt.WARM_OFF_WHITE, "surface": bt.WHITE, "dark": bt.DEEP,
            "ink": bt.DARK_INK, "muted": bt.BODY_INK, "accent": bt.EMBER_CORE,
            "accent_hot": bt.EMBER_HOT, "accent_soft": bt.EMBER_SOFT,
            "line": bt.WARM_LINE, "green": bt.SIGNAL_GREEN,
            "font": bt.FONT_STACK, "code_font": bt.CODE_FONT_STACK,
        }, emitted._BRAND)
        # The `_FALLBACK_*` values are the only palette: the public names are copies of them.
        self.assertEqual(emitted._FALLBACK_SOURCE_COLORS, emitted.SOURCE_COLORS)
        self.assertEqual(emitted._FALLBACK_BRAND, emitted._BRAND)
        self.assertEqual("emitted_results_server", emitted.color_for_sources.__module__,
                         "the copy's color_for_sources is not its own inlined function")
        for sources in SOURCE_LISTS:
            with self.subTest(sources=len(sources)):
                self.assertEqual(bt.color_for_sources(sources),
                                 emitted.color_for_sources(sources))

    def test_it_has_no_emit_mode(self):
        emitted = load_with_brand_tokens_blocked(self.dest, "emitted_results_server_cli")
        self.assertFalse(hasattr(emitted, "emit_standalone"))
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            emitted.build_arg_parser().parse_args(["--emit-standalone", "x.py"])

    def test_the_reference_still_prefers_brand_tokens(self):
        """Truth Set visualization runs the reference directly; its palette source is unchanged."""
        sys.path.insert(0, str(SCRIPTS))
        try:
            import brand_tokens as bt
        finally:
            sys.path.remove(str(SCRIPTS))
        self.assertIs(bt.color_for_sources, self.viz.color_for_sources)
        self.assertEqual(bt.SOURCE_COLORS, self.viz.SOURCE_COLORS)


class TheEmitModeNeedsNoD3SdkOrSettings(unittest.TestCase):
    """Criterion 2 of #891, run as a subprocess with no shell."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def run_script(self, *args):
        env = {k: v for k, v in os.environ.items() if k != "SENZING_ENGINE_CONFIGURATION_JSON"}
        return subprocess.run([sys.executable, "-I", *map(str, args)], cwd=str(self.tmp),
                              env=env, capture_output=True, text=True, timeout=120)

    def test_it_emits_from_a_bare_copy_and_the_copy_starts(self):
        bare = self.tmp / "bare"
        bare.mkdir()
        shutil.copy2(str(SCRIPT), str(bare / SCRIPT.name))
        self.assertFalse((bare / "vendor").exists())
        self.assertFalse((bare / "brand_tokens.py").exists())
        dest = self.tmp / "project" / "src" / "server" / "results_server.py"
        result = self.run_script(bare / SCRIPT.name, "--emit-standalone", dest)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("d3.v7.min.js", result.stderr, "the emit mode reached the D3 check")
        self.assertTrue(dest.is_file())

        # The copy starts as written: it parses its arguments and reaches its own D3 check,
        # which refuses visibly because no `vendor/` was copied beside it here.
        started = self.run_script(dest, "--no-serve")
        self.assertEqual(1, started.returncode, started.stderr)
        self.assertIn("d3.v7.min.js", started.stderr)
        self.assertIn(str(dest.parent / "vendor"), started.stderr,
                      "the copy looks for D3 somewhere other than beside its own file")
        self.assertNotIn("Traceback", started.stderr)

        helped = self.run_script(dest, "--help")
        self.assertEqual(0, helped.returncode, helped.stderr)
        self.assertNotIn("--emit-standalone", helped.stdout)


class TheEdgeCasesWriteNothing(unittest.TestCase):
    """The behavior #891 specifies for an existing file and a failure partway."""

    @classmethod
    def setUpClass(cls):
        cls.viz = load(SCRIPT, "viz_reference_for_edge_cases")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def test_an_existing_file_is_refused_and_named(self):
        dest = self.tmp / "results_server.py"
        dest.write_text("# the Bootcamper's adapted server\n", encoding="utf-8")
        code, _out, err = emit_in_process(self.viz, dest)
        self.assertNotEqual(0, code)
        self.assertIn(str(dest), err)
        self.assertEqual("# the Bootcamper's adapted server\n", dest.read_text(encoding="utf-8"))
        self.assertEqual([dest.name], [p.name for p in self.tmp.iterdir()])

    def assert_nothing_written(self, code, err, dest):
        self.assertNotEqual(0, code)
        self.assertIn("Nothing was written", err)
        self.assertFalse(dest.exists())
        leftovers = [p.name for p in self.tmp.rglob("*") if p.is_file()
                     and p.name != "source.py"]
        self.assertEqual([], leftovers, "a failed emit left a file behind")

    def test_a_source_with_no_plugin_only_block_writes_nothing(self):
        text = SCRIPT.read_text(encoding="utf-8")
        source = self.tmp / "source.py"
        source.write_text(text.replace("# >>> plugin-only", "# (marker removed)")
                              .replace("# <<< plugin-only", "# (marker removed)"),
                          encoding="utf-8")
        dest = self.tmp / "out" / "results_server.py"
        code, _out, err = emit_in_process(self.viz, dest, source)
        self.assert_nothing_written(code, err, dest)
        self.assertIn("no plugin-only block", err)

    def test_a_source_that_leaves_the_import_behind_writes_nothing(self):
        text = SCRIPT.read_text(encoding="utf-8")
        start = text.index("# >>> plugin-only\n# Prefer the shipped token module")
        source = self.tmp / "source.py"
        source.write_text(text[:start] + text[start:].replace("# >>> plugin-only\n", "", 1)
                          .replace("# <<< plugin-only\n", "", 1), encoding="utf-8")
        dest = self.tmp / "results_server.py"
        code, _out, err = emit_in_process(self.viz, dest, source)
        self.assert_nothing_written(code, err, dest)
        self.assertIn("brand_tokens", err)

    def test_an_unbalanced_marker_writes_nothing(self):
        text = SCRIPT.read_text(encoding="utf-8")
        source = self.tmp / "source.py"
        source.write_text(text.replace("\n# <<< plugin-only\n", "\n# (closer removed)\n", 1),
                          encoding="utf-8")
        dest = self.tmp / "results_server.py"
        code, _out, err = emit_in_process(self.viz, dest, source)
        self.assert_nothing_written(code, err, dest)

    def test_a_failed_rename_leaves_no_partial_file(self):
        dest = self.tmp / "results_server.py"
        with mock.patch.object(self.viz.os, "replace", side_effect=OSError(28, "No space left")):
            code, _out, err = emit_in_process(self.viz, dest)
        self.assertNotEqual(0, code)
        self.assertIn("No space left", err)
        self.assertFalse(dest.exists())
        self.assertEqual([], list(self.tmp.iterdir()), "the temporary file was left behind")


#: The elements step 3c's Python route must state, matched wrap-aware (INV-346).
STEP_3C_ELEMENTS = {
    "the emit command, by plugin path":
        r'python3 "\$\{CLAUDE_PLUGIN_ROOT\}/scripts/senzing_viz_server\.py" --emit-standalone '
        r"src/server/results_server\.py",
    "the skill-relative fallback (INV-252)":
        r"fallback\s+`\.\./\.\./scripts/senzing_viz_server\.py`\s+\(INV-252\)",
    "on the host, at first build":
        r"emit mode, on the host, at first build",
    "no copy-and-edit":
        r"never copy the reference and edit its import out",
    "the container route runs it on the host":
        r"`docker` route it runs on the host too",
    "a failed emit stops the step":
        r"A failed emit stops the step\*\*.{0,80}do not hand-copy the reference",
    "the provenance note goes inside the docstring":
        r"provenance note inside the existing module docstring, never above\s+"
        r"`from __future__ import annotations`",
}


def step_3c(text):
    """Step 3c, from its heading to the next heading of the same or a higher level."""
    start = text.index("### 3c. ")
    body = start + len("### 3c. ")
    nxt = re.search(r"(?m)^#{1,3} ", text[body:])
    return text[start:body + nxt.start()] if nxt else text[start:]


def missing_elements(section):
    return sorted(label for label, pattern in STEP_3C_ELEMENTS.items()
                  if not match_lines(section, re.compile(pattern, re.S)))


class StepThreeCRunsTheEmitMode(unittest.TestCase):
    """Criteria 3 and 4 of #891, with a negative control per element."""

    @classmethod
    def setUpClass(cls):
        cls.section = step_3c(STEP_3C_FILE.read_text(encoding="utf-8"))

    def test_the_section_is_found(self):
        self.assertIn("results_server", self.section)

    def test_every_element_is_stated(self):
        self.assertEqual([], missing_elements(self.section))

    def test_the_hand_edit_is_no_longer_taught(self):
        self.assertEqual([], match_lines(self.section, re.compile(
            r"(?i)(?:remove|delete|strip)\w*\s+the\s+`?brand_tokens`?\s+import")))

    def test_each_element_removed_is_reported(self):
        cut = {
            "the emit command, by plugin path": ("--emit-standalone src/server/results_server.py",
                                                 "src/server/results_server.py"),
            "the skill-relative fallback (INV-252)": ("`../../scripts/senzing_viz_server.py` (INV-252)",
                                                      "the skill's scripts"),
            "on the host, at first build": ("emit mode, on the host, at first build",
                                            "emit mode"),
            "no copy-and-edit": ("never copy the reference and edit its import out", "as usual"),
            "the container route runs it on the host": ("route it runs on the host too",
                                                        "route it runs in the container"),
            "a failed emit stops the step": ("do not hand-copy the reference instead",
                                             "copy the reference by hand instead"),
            "the provenance note goes inside the docstring": (
                "provenance note inside the existing module docstring", "provenance note first"),
        }
        self.assertEqual(set(STEP_3C_ELEMENTS), set(cut))
        for label, (old, new) in cut.items():
            with self.subTest(element=label):
                mutated = re.sub(r"\s+".join(map(re.escape, old.split())), new, self.section)
                self.assertNotEqual(mutated, self.section, "the control changed nothing")
                self.assertIn(label, missing_elements(mutated))


if __name__ == "__main__":
    unittest.main()
