"""The viz server picks engine settings by CONTENT, and never proceeds on an incomplete set.

The resolution used to be `if os.path.exists(args.settings)` — existence-based. A
`config/engine_config.json` containing `{"PIPELINE": {}}` is valid JSON and truthy, so it beat
a fully populated `SENZING_ENGINE_CONFIGURATION_JSON` and passed the `if not settings` check,
and the run then died inside the engine with:

    SENZ7426|Transliteration failed: No transliteration rules found!

That error's documented meaning sends the reader somewhere else entirely. Verified against the
live MCP server (1.32.9, 2026-08-13), `explain_error_code('7426')` lists as its first common
cause "SUPPORTPATH points at a directory with no transliteration modules … This is a
configuration error, NOT a broken install", and its first resolution step is "Check SUPPORTPATH
FIRST". So a bootcamper hitting this goes and inspects a SUPPORTPATH that is correct in the
place they are looking — because the value actually in force came from a file nobody told them
was preferred. Correct guidance, applied to a wrongly-reported cause.

These tests pin three things:

1. **Content-aware precedence** — a complete env var beats an incomplete file.
2. **The gate** — an incomplete set fails loudly, names the source and the missing keys, and
   does NOT mention transliteration (the whole point is not to reproduce the misdirection).
3. **No silent discard** — when both sources are present, which one won is always stated.

Deliberately SDK-free (INV-108): `resolve_settings` is pure, so every case is exercised without
`libSz.so`, a database or a license. Assertions are on the message and on the absence of a
snapshot, never on engine behavior.

Enforces **INV-210**.

No phrase-level pattern (#438): its one line read takes the first line of a resolver's problem
message, as #424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "senzing_viz_server.py"

COMPLETE = {
    "PIPELINE": {"CONFIGPATH": "/etc/opt/senzing", "RESOURCEPATH": "/opt/senzing/er/resources",
                 "SUPPORTPATH": "/opt/senzing/data"},
    "SQL": {"CONNECTION": "sqlite3://na:na@/tmp/sqlite/G2C.db"},
}
STUB = {"PIPELINE": {}}


def load():
    spec = importlib.util.spec_from_file_location("viz_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["viz_under_test"] = module
    spec.loader.exec_module(module)
    return module


viz = load()


def resolve(file_doc, env_value):
    """(settings, source, problem, stderr) for a scratch settings file + env value."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "engine_config.json")
        if file_doc is not None:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(file_doc if isinstance(file_doc, str) else json.dumps(file_doc))
        log = io.StringIO()
        settings, source, problem = viz.resolve_settings(path, env_value, log)
        return settings, source, problem, log.getvalue()


class AnIncompleteSettingSetNeverReachesTheEngine(unittest.TestCase):
    def test_a_stub_file_alone_fails_naming_the_source_and_the_missing_keys(self):
        settings, source, problem, _log = resolve(STUB, "")
        self.assertEqual("", settings, "no settings may be returned for the engine to use")
        self.assertIsNotNone(problem, "a stub PIPELINE must not be accepted")
        self.assertIn("engine_config.json", problem, "the message must name the source in force")
        for key in viz.REQUIRED_PIPELINE_KEYS:
            self.assertIn(key, problem, f"the message must name the missing key {key}")
        self.assertIn("engine_config.json", str(source))

    def test_the_failure_message_does_not_reproduce_the_senz7426_misdirection(self):
        """It may *warn* about SENZ7426; it must not present transliteration as the cause."""
        _s, _src, problem, _log = resolve(STUB, "")
        first_line = problem.splitlines()[0]
        self.assertNotIn(
            "ransliteration", first_line,
            "the headline cause must be the incomplete settings, not transliteration — "
            "reporting the downstream symptom is the defect this fixes",
        )
        self.assertIn("incomplete", first_line.lower())

    def test_a_partially_complete_pipeline_names_only_what_is_missing(self):
        doc = {"PIPELINE": {"CONFIGPATH": "/etc/opt/senzing"}}
        _s, _src, problem, _log = resolve(doc, "")
        self.assertIn("RESOURCEPATH", problem)
        self.assertIn("SUPPORTPATH", problem)
        self.assertNotIn("CONFIGPATH", problem, "a key that IS present must not be reported")

    def test_a_present_but_blank_key_counts_as_missing(self):
        doc = {"PIPELINE": {"CONFIGPATH": "/etc", "RESOURCEPATH": "  ", "SUPPORTPATH": ""}}
        _s, _src, problem, _log = resolve(doc, "")
        self.assertIsNotNone(problem, "whitespace and empty strings are not values")
        self.assertIn("RESOURCEPATH", problem)
        self.assertIn("SUPPORTPATH", problem)

    def test_unparseable_json_is_reported_as_such(self):
        _s, _src, problem, _log = resolve("{not json", "")
        self.assertIsNotNone(problem)
        self.assertIn("not usable JSON", problem)

    def test_neither_source_keeps_the_original_message(self):
        _s, _src, problem, _log = resolve(None, "")
        self.assertEqual("No engine settings (missing --settings file and env var).\n", problem)


class PrecedenceIsContentAwareAndNeverSilent(unittest.TestCase):
    def test_a_complete_env_var_beats_an_incomplete_file(self):
        env = json.dumps(COMPLETE)
        settings, source, problem, log = resolve(STUB, env)
        self.assertIsNone(problem, "a complete env var must rescue an incomplete file")
        self.assertEqual(env, settings, "the env var's values must be the ones used")
        self.assertIn("SENZING_ENGINE_CONFIGURATION_JSON", source)
        self.assertIn("SENZING_ENGINE_CONFIGURATION_JSON", log,
                      "stderr must say which source won")
        self.assertIn("PIPELINE", log, "and why the file lost")

    def test_a_complete_file_wins_and_says_so_when_both_are_set_and_differ(self):
        other = json.loads(json.dumps(COMPLETE))
        other["PIPELINE"]["SUPPORTPATH"] = "/somewhere/else"
        settings, source, problem, log = resolve(COMPLETE, json.dumps(other))
        self.assertIsNone(problem)
        self.assertEqual(COMPLETE, json.loads(settings), "the file's values are in force")
        self.assertIn("engine_config.json", source)
        self.assertIn("the file wins", log,
                      "the losing source must never be discarded silently")

    def test_identical_sources_need_no_narration(self):
        raw = json.dumps(COMPLETE)
        _s, _src, problem, log = resolve(COMPLETE, raw)
        self.assertIsNone(problem)
        self.assertEqual("", log.strip(),
                         "nothing to report when both sources agree — narrating it is noise")

    def test_a_complete_file_alone_is_silent(self):
        _s, source, problem, log = resolve(COMPLETE, "")
        self.assertIsNone(problem)
        self.assertIn("engine_config.json", source)
        self.assertEqual("", log.strip(), "the ordinary path stays quiet")

    def test_both_incomplete_reports_the_file_rather_than_the_env_var(self):
        """The file is what the caller passed, so it is the actionable one to name first."""
        _s, source, problem, _log = resolve(STUB, json.dumps(STUB))
        self.assertIsNotNone(problem)
        self.assertIn("engine_config.json", str(source))


class TheDocstringStatesThePrecedence(unittest.TestCase):
    def test_the_module_docstring_gives_the_order_and_the_reason(self):
        doc = viz.__doc__ or ""
        self.assertIn("content-aware", doc,
                      "the docstring must say the precedence is content-aware, since "
                      "'file or env var' reads as existence-based")
        self.assertIn("SENZ7426", doc,
                      "the docstring must record why validating first matters — the "
                      "misdiagnosis is the whole reason for the gate")
        for key in viz.REQUIRED_PIPELINE_KEYS:
            self.assertIn(key, doc)


if __name__ == "__main__":
    unittest.main()
