"""Every module saves its graduation-video B-roll at completion, in one pinned format.

`module-completion.md` Step 2e appends the completed module's entry to `docs/video/broll.json`,
so graduation builds the recap video (#297) from one manifest rather than reconstructing the
bootcamp from memory. These tests pin:

* **The instruction** is in Step 2, the step every module runs, and the process overview names
  the file. The module closes that list Step 2's substeps themselves (Entity Resolution
  Concepts, System verification, Truth Set visualization) name 2e too: a citation that lists
  substeps and leaves one out is the hazard INV-226 names.
* **The format**: one JSON object keyed by the module's state token from Bootcamp preparation's
  module list, each value holding exactly `module`, `images`, `facts`, `highlight` and
  `captured_at`. The documented example parses and obeys it, and its facts line up with the
  scene fields the video renderer (#299) validates, so #300 can build the storyboard from them.
* ⛔ **No raw record values**: only counts, source names, field and attribute names, and
  statistics.
* **Re-completion replaces** the entry; a **missing or unreadable file is recreated**; and the
  entry **never blocks** module completion.
* **Bootcamp preparation writes no entry** (INV-075).

Enforces **INV-341** (every completed module saves one aggregates-only B-roll entry, replaced on
re-completion, never blocking completion). It asserts what `module-completion.md` *states*, and does
**not** establish that a live run writes a conforming entry, which only `dry-run` phase 3 can observe.

Source issue: #298 (part of #297).

Run:  python3 -m unittest discover -s tests
"""
import datetime
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
MODULE_COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"
PREPARATION = SKILLS / "bootcamp-preparation" / "SKILL.md"
RENDERER = PLUGIN / "scripts" / "generate_recap_video.py"

#: The module closes that enumerate Step 2's work themselves, so each must name 2e.
ENUMERATING_CLOSES = {
    "entity_resolution_concepts": SKILLS / "module-00-entity-resolution-concepts" / "SKILL.md",
    "system_verification": SKILLS / "module-03-system-verification" / "phase2-report-close.md",
    "truthset_visualization":
        SKILLS / "module-03b-truthset-visualization" / "phase2-close.md",
}

ENTRY_KEYS = ("module", "images", "facts", "highlight", "captured_at")
FACT_KEYS = ("sources", "mappings", "records_loaded", "entities_resolved", "statistics")


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def step_2e():
    text = read(MODULE_COMPLETION)
    start = text.index("### 2e.")
    end = text.index("\n## ", start)
    return text[start:end]


def example_manifest():
    blocks = re.findall(r"```json\n(.*?)```", step_2e(), re.S)
    if len(blocks) != 1:
        raise AssertionError("Step 2e must carry exactly one ```json example, found %d"
                             % len(blocks))
    return json.loads(blocks[0])


def state_tokens():
    """Bootcamp preparation's module list: state token -> display name."""
    rows = re.findall(r"^\| \d+ \| ([^|]+?) \| [^|]+ \| `([a-z_]+)` \|", read(PREPARATION), re.M)
    return {token: name for name, token in rows}


def load_renderer():
    spec = importlib.util.spec_from_file_location("generate_recap_video_for_broll", RENDERER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TheInstructionIsWhereEveryModuleRunsIt(unittest.TestCase):

    def test_step_2e_saves_the_entry_to_broll_json(self):
        section = step_2e()
        self.assertIn("### 2e. Save this module's B-roll entry", section)
        self.assertIn("`docs/video/broll.json`", section)

    def test_it_sits_inside_step_2_before_step_3(self):
        text = read(MODULE_COMPLETION)
        self.assertLess(text.index("## Step 2:"), text.index("### 2e."))
        self.assertLess(text.index("### 2e."), text.index("## Step 3:"))

    def test_the_process_overview_names_the_file(self):
        overview = read(MODULE_COMPLETION).split("## Step 1:")[0]
        self.assertIn("`docs/video/broll.json`", overview)

    def test_every_module_that_runs_step_2_runs_it(self):
        self.assertIn("Every module that runs Step 2 runs this substep", squash(step_2e()))

    def test_closes_that_enumerate_step_2_name_2e(self):
        for token, path in ENUMERATING_CLOSES.items():
            with self.subTest(close=path.relative_to(REPO_ROOT).as_posix()):
                text = squash(read(path))
                self.assertRegex(text, r"\*?\*?2e\*?\*?",
                                 "this close lists Step 2's work itself and leaves out 2e, so "
                                 "following it literally saves no B-roll (INV-226)")
                self.assertIn("`%s`" % token, text,
                              "the close must name the key its entry is saved under")

    def test_bootcamp_preparation_writes_no_entry(self):
        text = squash(step_2e())
        self.assertIn("Bootcamp preparation writes no entry", text)
        self.assertIn("INV-075", text)
        self.assertIn("`config/bootcamp_preferences.yaml`", text)


class TheFormatIsPinned(unittest.TestCase):

    def test_each_entry_key_is_documented(self):
        section = step_2e()
        for key in ENTRY_KEYS:
            with self.subTest(key=key):
                self.assertIn("- **`%s`**" % key, section)

    def test_each_fact_key_is_documented(self):
        section = step_2e()
        for key in FACT_KEYS:
            with self.subTest(key=key):
                self.assertIn("`%s`" % key, section)

    def test_it_is_keyed_by_the_preparation_state_token(self):
        text = squash(step_2e())
        self.assertIn("**state token**", text)
        self.assertIn("`../bootcamp-preparation/SKILL.md`", text)

    def test_the_example_is_one_object_keyed_by_real_state_tokens(self):
        manifest = example_manifest()
        tokens = state_tokens()
        self.assertIn("business_problem", tokens, "could not read the module list")
        self.assertIsInstance(manifest, dict)
        self.assertTrue(manifest)
        for key, entry in manifest.items():
            with self.subTest(key=key):
                self.assertIn(key, tokens)
                self.assertNotIn(key, ("bootcamp_preparation", "graduation"))
                self.assertEqual(entry["module"], tokens[key],
                                 "`module` must be the module's display name")

    def test_the_example_entries_hold_exactly_the_five_keys(self):
        for key, entry in example_manifest().items():
            with self.subTest(key=key):
                self.assertEqual(tuple(entry), ENTRY_KEYS)
                self.assertIsInstance(entry["images"], list)
                self.assertIsInstance(entry["facts"], dict)
                self.assertTrue(set(entry["facts"]) <= set(FACT_KEYS))
                self.assertIsInstance(entry["highlight"], str)
                self.assertTrue(entry["highlight"].strip())

    def test_captured_at_is_iso_8601_with_an_offset(self):
        for key, entry in example_manifest().items():
            with self.subTest(key=key):
                stamp = datetime.datetime.fromisoformat(entry["captured_at"])
                self.assertIsNotNone(stamp.utcoffset())

    def test_images_are_project_relative(self):
        text = squash(step_2e())
        self.assertIn("relative to the project root, not to the recap", text)
        for key, entry in example_manifest().items():
            for image in entry["images"]:
                with self.subTest(key=key, image=image):
                    self.assertTrue(image.startswith("docs/"), image)
                    self.assertFalse(image.startswith("/"))

    def test_no_new_capture_is_added(self):
        text = squash(step_2e())
        self.assertIn("**already** produced", text)
        self.assertIn("Add no capture for this", text)

    def test_the_example_facts_become_valid_renderer_scenes(self):
        """The facts line up with the scene fields #299's renderer validates."""
        video = load_renderer()
        scenes = []
        for entry in example_manifest().values():
            facts = entry["facts"]
            if "sources" in facts:
                scenes.append({"type": "counter", "duration": 6, "narration": entry["highlight"],
                               "title": "Records per source",
                               "items": [{"label": s["name"], "value": s["records"]}
                                         for s in facts["sources"]]})
            for mapping in facts.get("mappings", []):
                scenes.append({"type": "mapping", "duration": 6, "narration": entry["highlight"],
                               "source": mapping["source"], "fields": mapping["fields"]})
            for image in entry["images"]:
                scenes.append({"type": "image", "duration": 6, "narration": entry["highlight"],
                               "image": image, "module": entry["module"]})
        self.assertTrue(scenes)
        storyboard = {"video": {"bootcamper": "Bootcamper", "graduation_date": "2026-09-30"},
                      "scenes": scenes}
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(video.validate_storyboard(storyboard, Path(root)), [])


class TheRulesAreStated(unittest.TestCase):

    def test_no_raw_record_values(self):
        text = squash(step_2e())
        self.assertIn("⛔ **(INV-341) No raw record values, anywhere in the entry.**", text)
        self.assertIn("Only counts, source names, field and attribute names, and statistics",
                      text)
        for forbidden in ("a name", "an address", "an identifier"):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, text)
        self.assertIn("not even inside `highlight`", text)

    def test_re_completion_replaces_the_entry(self):
        text = squash(step_2e())
        self.assertIn("**(INV-341) Re-completing a module replaces its entry.**", text)
        self.assertIn("never a second entry", text)

    def test_a_missing_or_unreadable_file_is_recreated(self):
        text = squash(step_2e())
        self.assertIn("When the file is missing, create `docs/video/`", text)
        self.assertIn("When it does not parse as a JSON object, write a new object", text)

    def test_it_never_blocks_module_completion(self):
        text = squash(step_2e())
        self.assertIn("⛔ **(INV-341) The B-roll entry never blocks module completion", text)
        self.assertIn("A failed read or write is not a module failure", text)
        opening = squash(read(MODULE_COMPLETION).split("## Step 1:")[0])
        self.assertIn("The one exception is the B-roll entry (2e), which never blocks "
                      "completion", opening,
                      "the opening says any failed write stops completion; it must carve "
                      "out 2e")

    def test_it_is_quiet(self):
        self.assertIn("with no bootcamper-facing line", squash(step_2e()))


if __name__ == "__main__":
    unittest.main()
