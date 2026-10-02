"""The reference visualization server refuses to render when its vendored D3 is missing.

D3 is vendored at ``scripts/vendor/d3.v7.min.js`` so the visualization renders with no
network access (INV-091). The reference server used to fall back to a
``<script src="https://d3js.org/d3.v7.min.js">`` tag when that file was missing, while
Module 7 tells the guide to build a project-local server modeled on it and to *"Keep the
refusal-to-render when no asset is found"*. A guide that copied the reference inherited a
silent network fetch in exactly the case the step says must fail visibly (#332).

These tests pin the refusal:

1. **Behavioral (subprocess):** a copy of the server with no ``vendor/`` beside it, run with
   ``--no-serve --snapshot``, exits non-zero, names the missing asset on stderr, says nothing
   about engine settings (the check runs before settings resolution, so no engine or settings
   are needed), writes no snapshot, and prints no ``d3js.org`` URL.
2. **Behavioral (in process):** with the asset gone, ``render_page`` raises instead of
   returning a page, so the live server cannot serve a CDN tag either.
3. **Static:** the string ``d3js.org`` appears nowhere in the server's source.

With the asset present, D3 is still inlined, so supported installs are unchanged.

4. **Module 3b's two sites (#382):** the step that generates a language-native Truth Set
   server stated only the no-CDN half of the rule. The "Render offline (INV-091)" bullet in
   ``phase1-visualization.md`` and "Offline rendering (required)" in
   ``visualization-api-reference.md`` must each state all four elements of the refusal — a
   missing or unreadable asset makes the server refuse to render and fail visibly; the failure
   names the missing asset; no page or snapshot is written; there is no fallback to the
   ``d3js.org`` CDN or any other network source — and cite INV-091. A negative control deletes
   each element in turn from an in-memory copy and sees the check report it. Module 7's
   refusal is pinned by ``tests/test_project_local_visualization_finds_its_d3.py``.

Stdlib only; the server is loaded from a file path, never installed or imported as a
package (INV-108). No Senzing engine is needed.

Enforces **INV-091**.

Run:  python3 -m unittest discover -s tests
"""

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
SCRIPT = SCRIPTS / "senzing_viz_server.py"
VENDORED = SCRIPTS / "vendor" / "d3.v7.min.js"

CDN_HOST = "d3js.org"
ASSET_NAME = "d3.v7.min.js"

MODULE_3B = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-03b-truthset-visualization"
PHASE1 = MODULE_3B / "phase1-visualization.md"
CONTRACT = MODULE_3B / "visualization-api-reference.md"

#: The four elements of INV-091's refusal (its 2026-10-02 correction), element 1 split into
#: its three parts so "missing" alone cannot stand in for "missing or unreadable", plus the
#: citation. Matched against whitespace-collapsed text; backticks are optional.
REFUSAL_ELEMENTS = {
    "1a. missing or unreadable": r"\bmissing\s+or\s+unreadable\b",
    "1b. refuses to render": r"\brefus(?:e|es|ing)\s+to\s+render\b",
    "1c. fails visibly": r"\bfail(?:s|ing)?\s+visibly\b",
    "2. names the missing asset": r"\bnam(?:e|es|ing)\s+the\s+missing\s+asset\b.{0,20}?d3\.v7\.min\.js",
    "3. writes no page or snapshot": r"\bwrites?\s+no\s+page\s+or\s+snapshot\b",
    "4. no CDN or network fallback": (
        r"\b(?:never|MUST\s+NOT|must\s+not)\s+fall\s+back\s+to\s+the\s+`?d3js\.org`?\s+CDN"
        r"\s+or\s+any\s+other\s+network\s+source\b"
    ),
    "citation": r"\bINV-091\b",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


class ACopyWithNoVendoredAssetRefusesToRender(unittest.TestCase):
    """Run a copy of the server that has no ``vendor/`` beside it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.copy = cls.dir / "senzing_viz_server.py"
        shutil.copy2(SCRIPT, cls.copy)
        cls.snapshot = cls.dir / "docs" / "visualizations" / "out.html"
        env = {k: v for k, v in os.environ.items()
               if k != "SENZING_ENGINE_CONFIGURATION_JSON"}
        env["PYTHONIOENCODING"] = "utf-8"
        cls.result = subprocess.run(
            [sys.executable, str(cls.copy), "--no-serve", "--snapshot", str(cls.snapshot)],
            cwd=str(cls.dir), env=env, capture_output=True, text=True,
            encoding="utf-8", timeout=120,
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_it_exits_non_zero(self):
        self.assertNotEqual(
            self.result.returncode, 0,
            "with no vendored D3 the server must fail visibly, not succeed. "
            f"stderr: {self.result.stderr!r}",
        )

    def test_stderr_names_the_missing_asset(self):
        self.assertIn(
            ASSET_NAME, self.result.stderr,
            "the failure must name the vendored asset it could not find, so the reader "
            "knows what to restore rather than chasing an engine or settings problem.",
        )

    def test_the_check_runs_before_settings_resolution(self):
        """No settings exist here; a settings complaint means the D3 check ran too late."""
        self.assertNotIn(
            "engine settings", self.result.stderr.lower(),
            "the vendored-asset check must run straight after argument parsing, before "
            "settings resolution, so a missing asset is reported as itself.",
        )

    def test_no_snapshot_is_written(self):
        self.assertFalse(
            self.snapshot.exists(),
            "a snapshot built without the vendored D3 would pass the exit-code gate and "
            "break offline; none may be written.",
        )

    def test_no_cdn_url_is_printed(self):
        for stream, text in (("stdout", self.result.stdout), ("stderr", self.result.stderr)):
            with self.subTest(stream=stream):
                self.assertNotIn(
                    CDN_HOST, text,
                    "the refusal must not point at, or fall back to, a CDN (INV-091).",
                )


class ThePageCannotBeRenderedWithoutTheAsset(unittest.TestCase):
    """The asset disappearing after startup: rendering raises rather than linking a CDN."""

    def test_render_page_raises_and_returns_no_cdn_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "senzing_viz_server.py"
            shutil.copy2(SCRIPT, copy)
            module = load(copy, "viz_without_d3_under_test")
            try:
                page = module.render_page("t")
            except Exception as exc:  # noqa: BLE001 - any raise is a refusal
                self.assertIn(ASSET_NAME, str(exc),
                              "the raise must name the missing vendored asset.")
                return
            self.assertNotIn(CDN_HOST, page,
                             "render_page emitted a CDN tag for the missing D3 (INV-091).")
            self.fail("render_page must refuse (raise) when the vendored D3 is missing; "
                      "it returned a page instead.")


class TheSourceNamesNoCdn(unittest.TestCase):
    def test_d3js_org_appears_nowhere_in_the_server(self):
        self.assertNotIn(
            CDN_HOST, SCRIPT.read_text(encoding="utf-8"),
            "no code path may emit a d3js.org URL: the offline guarantee is the reason D3 "
            "is vendored at all (INV-091).",
        )


class WithTheAssetPresentD3IsStillInlined(unittest.TestCase):
    def test_the_vendored_asset_is_inlined(self):
        module = load(SCRIPT, "viz_with_d3_under_test")
        tag = module._d3_script()
        self.assertTrue(tag.startswith("<script>") and tag.endswith("</script>"),
                        "the vendored D3 must be inlined, not linked.")
        self.assertIn(VENDORED.read_text(encoding="utf-8"), tag,
                      "the inlined script must carry the vendored asset's contents.")


def _flat(text):
    return re.sub(r"\s+", " ", text)


def render_offline_bullet(text):
    """Module 3b ``phase1-visualization.md``: the "Render offline (INV-091)" bullet, nested lines included."""
    match = re.search(r"^- \*\*Render offline \(INV-091\):\*\*.*?(?=^- |^#|\Z)", text, re.S | re.M)
    return match.group(0) if match else ""


def offline_rendering_section(text):
    """``visualization-api-reference.md``: the "Offline rendering (required)" section."""
    match = re.search(r"^### Offline rendering \(required\)\n.*?(?=^#{1,3} |\Z)", text, re.S | re.M)
    return match.group(0) if match else ""


def missing_elements(section):
    flat = _flat(section)
    return [name for name, pattern in REFUSAL_ELEMENTS.items()
            if not re.search(pattern, flat, re.I)]


class Module3bStatesTheRefusalInFull(unittest.TestCase):
    """Both Module 3b sites that tell the guide how to build the server state all four elements."""

    SITES = (
        ("phase1-visualization.md, Render offline", PHASE1, render_offline_bullet),
        ("visualization-api-reference.md, Offline rendering (required)", CONTRACT,
         offline_rendering_section),
    )

    def sections(self):
        for label, path, extract in self.SITES:
            yield label, extract(path.read_text(encoding="utf-8"))

    def test_each_site_is_found(self):
        for label, section in self.sections():
            with self.subTest(site=label):
                self.assertTrue(section.strip(), f"{label}: the section was not found; "
                                "a rename must move this guard with it.")

    def test_each_site_states_every_element_and_cites_inv_091(self):
        for label, section in self.sections():
            with self.subTest(site=label):
                self.assertEqual(
                    [], missing_elements(section),
                    f"{label} must state INV-091's refusal in full: a missing or unreadable "
                    "vendored D3 makes the server refuse to render and fail visibly, naming the "
                    "missing asset, writing no page or snapshot, and never falling back to the "
                    "d3js.org CDN or any other network source.",
                )

    def test_removing_any_element_is_caught(self):
        """Negative control: delete each element in turn from an in-memory copy."""
        for label, section in self.sections():
            for name, pattern in REFUSAL_ELEMENTS.items():
                with self.subTest(site=label, element=name):
                    mutated = re.sub(pattern, "", _flat(section), flags=re.I)
                    self.assertIn(name, missing_elements(mutated))

    def test_the_rule_is_not_narrowed_to_a_python_mechanism(self):
        """The generated server may be in any language (INV-090)."""
        for label, section in self.sections():
            with self.subTest(site=label):
                self.assertNotIn("__file__", section)


if __name__ == "__main__":
    unittest.main()
