"""Graduation Step 1c offers, writes, renders and checks the graduation video.

The video is the optional third keepsake (#297). Step 1c in `graduation/SKILL.md` turns the
B-roll every module saved (`module-completion.md` Step 2e, #298) into a storyboard and renders it
with the bundled renderer (`generate_recap_video.py`, #299). These tests pin:

* **Where it runs**: Step 1c sits right after Step 1b's recap PDF, before Step 2, because the
  video reuses the certificate's name and date. The preface's step overview and time estimate
  name the video as optional.
* **The three questions**, verbatim: the offer, the Piper voice offer after the storyboard and
  before the first render (#341, with its Pillow / `imageio-ffmpeg` variant), and the one install
  offer after exit 2.
* **The Piper paths** (#341): on yes one `python -m pip` into `data/temp/recap-venv/` and the voice
  download into `data/temp/piper-voices/`, then `--check` and the render with the venv's Python; on
  no or a failure, Step 1b's interpreter and the platform engine; no `--voice-model`; the voice
  named from the `Voice:` line.
* **On no, nothing is written**; the heads-up line appears only after a declined model switch.
* **The time budget**: the reporter's shares, summing to 100%, scaled over the modules taken,
  with each worked example checked against the formula rather than trusted.
* **The storyboard**: the documented example validates through the renderer's own
  `validate_storyboard`, runs exactly 2:00, carries the five animated scenes, and ends on the
  certificate and then "Resolved: [Name], Senzing graduate.".
* ⛔ **No raw record values**, and the fallbacks never block graduation: exit 1, 2 and 3, a
  declined or failed install, the storyboard kept.
* ⛔ **Only name-free screenshots** (#326): Step 1c's allow-list is exactly the `match-keys`,
  `feature-scores` and `cross-source` tab slugs, each a slug in `capture_screenshots.py` `TABS`;
  every `image` scene in the example ends in `-<slug>.png` with one of them; the name-bearing
  captures are named as left out; and module completion Step 2e defers the choice to graduation.
  Negative controls feed the checks a `merge-statistics`, an `entity-graph` and a single-page
  `<name>.png` image, and a widened allow-list.
* **The checks**: 2:00 ± 10 s with one re-render, frames looked at, audio read from the `Voice:`
  and `Music:` lines (#339), skipped checks reported.
* **Where it is named**: the closing announcement and the return guide.

Stdlib only; the renderer's validator needs neither Pillow nor ffmpeg (INV-108).

Enforces **INV-340** (graduation's video step: offered once, nothing written on no, aggregates only,
never blocking, storyboard kept, the render verified). It asserts that Step 1c *states* these rules,
and does **not** establish that a live run follows them, which only `dry-run` phase 3 can observe.

Source issues: #300 (part of #297), #341, #326.

Run:  python3 -m unittest discover -s tests
"""
import ast
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
GRADUATION = SKILLS / "graduation" / "SKILL.md"
GRADUATE_COMMAND = PLUGIN / "commands" / "graduate.md"
PREPARATION = SKILLS / "bootcamp-preparation" / "SKILL.md"
RENDERER = PLUGIN / "scripts" / "generate_recap_video.py"
CAPTURE = PLUGIN / "scripts" / "capture_screenshots.py"
MODULE_COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"

#: The name-free tab slugs from #326, revision 1. Restated here on purpose: it is the spec
#: Step 1c's table is checked against, not a copy of the table.
NAME_FREE_SLUGS = {"match-keys", "feature-scores", "cross-source"}

OFFER = ("> 👉 **Would you like a narrated 2-minute graduation video of your bootcamp?** "
         "(Saved to `docs/bootcamp_recap.mp4`; reply no to skip.)")
INSTALL = ("> 👉 **Rendering the video needs ffmpeg. May I install `imageio-ffmpeg` into this "
           "project's virtualenv?** (Reply no to skip the video; its storyboard is kept so you "
           "can render it later.)")
TAG_LINE = "Resolved: [Name], Senzing graduate."
PIPER_OFFER = ("> 👉 **May I install the Piper neural voice so the narration sounds natural?** It "
               "downloads about 200 MB into this project: `piper-tts` (GPL-3.0, runs on your "
               "machine) into `data/temp/recap-venv/`, and the public-domain `en_US-ljspeech-high` "
               "voice into `data/temp/piper-voices/`. (Reply no to narrate with your computer's "
               "built-in voice.)")
PIPER_VARIANT = ("…into `data/temp/recap-venv/` along with Pillow and `imageio-ffmpeg`, which "
                 "rendering needs, and the public-domain `en_US-ljspeech-high` voice…")

#: The reporter's budget from #300, before scaling for skipped modules. Restated here on
#: purpose: it is the spec the step's table is checked against, not a copy of the table.
BUDGET = {
    "Bootcamp preparation": 5,
    "Entity Resolution Concepts": 5,
    "Discover the Business Problem": 15,
    "SDK setup": 3,
    "System verification": 3,
    "Truth Set visualization": 10,
    "Data collection": 10,
    "Data Quality, Mapping, and Transformation": 10,
    "Data processing": 5,
    "Query, Visualize and Discover": 30,
    "You graduated!": 4,
}
ALWAYS_COUNTED = ("Bootcamp preparation", "You graduated!")
REMAINDER_MODULE = "Query, Visualize and Discover"
OPTIONAL = ("Entity Resolution Concepts", "System verification", "Truth Set visualization")

#: The reporter's five animated scenes: module -> the scene type that draws it.
ANIMATED = {
    "Discover the Business Problem": "title_card",
    "Data collection": "counter",
    "Data Quality, Mapping, and Transformation": "mapping",
    "Data processing": "loading",
    "Query, Visualize and Discover": "entity_merge",
}


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def section(text, start_marker, end_marker):
    start = text.index(start_marker)
    return text[start:text.index(end_marker, start + len(start_marker))]


def step_1c():
    return section(read(GRADUATION), "### 1c.", "\n## Step 2:")


def table_rows(text, header_start):
    """The body rows of the Markdown table whose header row begins with `header_start`."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(header_start):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                rows.append([cell.strip() for cell in row.strip("|").split("|")])
            return rows
    raise AssertionError("no table whose header starts %r" % header_start)


def budget_table():
    """module -> (state token, share, seconds with every module taken)."""
    out = {}
    for module, token, share, seconds in table_rows(step_1c(), "| Module | State token | Share"):
        out[module] = (token.strip("`"), int(share.rstrip("%")), float(seconds))
    return out


def scaled(counted):
    """The step's formula: 120 x share / counted total, one decimal, remainder to QVD."""
    total = sum(BUDGET[m] for m in counted)
    seconds = {m: round(120 * BUDGET[m] / total, 1) for m in counted}
    seconds[REMAINDER_MODULE] = round(
        seconds[REMAINDER_MODULE] + 120 - sum(seconds.values()), 1)
    return seconds


def example_storyboard():
    blocks = re.findall(r"```json\n(.*?)```", step_1c(), re.S)
    if len(blocks) != 1:
        raise AssertionError("Step 1c must carry exactly one ```json storyboard, found %d"
                             % len(blocks))
    return json.loads(blocks[0])


def state_tokens():
    """Bootcamp preparation's module list: display name -> state token."""
    rows = re.findall(r"^\| \d+ \| ([^|]+?) \| [^|]+ \| `([a-z_]+)` \|", read(PREPARATION), re.M)
    return {name: token for name, token in rows}


def load_renderer():
    spec = importlib.util.spec_from_file_location("generate_recap_video_for_step_1c", RENDERER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def stated_name_free_slugs(text):
    """The slugs Step 1c's image table lets into the video: rows whose verdict starts "yes"."""
    slugs = set()
    for image, _tab, verdict in table_rows(text, "| Image | Tab | In the video"):
        if verdict.startswith("yes"):
            match = re.fullmatch(r"`<name>-([a-z-]+)\.png`", image)
            if not match:
                raise AssertionError("a name-free row names no `<name>-<slug>.png`: %r" % image)
            slugs.add(match.group(1))
    return slugs


def image_problems(storyboard, allowed):
    """Every `image` scene path that does not end in `-<slug>.png` with `<slug>` allowed."""
    problems = []
    for scene in storyboard["scenes"]:
        if scene["type"] != "image":
            continue
        name = scene["image"].rsplit("/", 1)[-1]
        if not any(name.endswith("-%s.png" % slug) for slug in allowed):
            problems.append(scene["image"])
    return problems


def capture_tab_slugs():
    """The filename slugs in `capture_screenshots.py` `TABS`, read without importing it."""
    for node in ast.parse(read(CAPTURE)).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", None) == "TABS"):
            return {slug for slug, _label in ast.literal_eval(node.value).values()}
    raise AssertionError("capture_screenshots.py defines no TABS")


class TheStepIsWhereTheVideoCanReuseTheCertificate(unittest.TestCase):

    def test_step_1c_sits_after_1b_and_before_step_2(self):
        text = read(GRADUATION)
        self.assertLess(text.index("### 1b. Render the PDF"), text.index("### 1c."))
        self.assertLess(text.index("### 1c."), text.index("## Step 2:"))
        self.assertIn("### 1c. Offer the graduation video (optional)", text)

    def test_the_preface_names_the_optional_video(self):
        preface = squash(section(read(GRADUATION), "## Bootcamp graduation preface",
                                 "## Best-value model/effort prompt"))
        overview = preface[preface.index("**What we'll do.**"):
                           preface.index("**Estimated time.**")]
        self.assertIn("optional narrated 2-minute graduation video", overview)
        self.assertIn("`docs/bootcamp_recap.mp4`", overview)
        estimate = preface[preface.index("**Estimated time.**"):]
        self.assertIn("a few minutes more if you choose the optional graduation video",
                      estimate)

    def test_the_graduate_command_names_the_video(self):
        self.assertIn("offer the optional graduation video", squash(read(GRADUATE_COMMAND)))

    def test_it_uses_the_bundled_renderer_through_the_plugin_root(self):
        text = step_1c()
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/scripts/generate_recap_video.py"', text)
        self.assertNotRegex(text, r"(?m)^python3 scripts/generate_recap_video\.py",
                            "a bare project-relative script path does not resolve (INV-185)")


class TheQuestionsArePinned(unittest.TestCase):

    def test_the_offer_is_verbatim_and_asked_once(self):
        text = step_1c()
        self.assertEqual(1, text.count(OFFER))
        self.assertIn("Ask it once per graduation (INV-006, INV-056)", squash(text))

    def test_the_install_offer_is_verbatim_and_asked_once(self):
        text = step_1c()
        self.assertEqual(1, text.count(INSTALL))
        self.assertIn("**The install offer (exit 2).** Offer it once (INV-006, INV-340)", squash(text))

    def test_the_install_offer_names_pillow_when_it_is_missing(self):
        text = squash(step_1c())
        self.assertIn("When Pillow is missing as well, name it in the same question", text)
        self.assertIn("May I install `imageio-ffmpeg` and Pillow into this project's "
                      "virtualenv?", text)

    def test_the_install_follows_inv_066(self):
        text = step_1c()
        self.assertIn("project-local virtualenv (INV-066)", squash(text))
        self.assertIn("data/temp/recap-venv/bin/python -m pip install imageio-ffmpeg", text)
        self.assertNotRegex(text, r"(?m)^\s*pip install", "never a bare pip (INV-066)")

    def test_no_question_asks_about_the_model(self):
        text = squash(step_1c())
        self.assertIn("There is no second model question", text)
        self.assertEqual(3, text.count("👉"), "Step 1c asks the offer, the Piper voice offer "
                         "(#341) and the install offer, and nothing else")


class NoMeansNothingWritten(unittest.TestCase):

    def test_on_no_no_video_file_is_written(self):
        text = squash(step_1c())
        self.assertIn("⛔ **(INV-340) On no, write no video file at all:** no "
                      "`docs/video/storyboard.json` and no `docs/bootcamp_recap.mp4`", text)
        self.assertIn("The storyboard is written only after a yes", text)
        self.assertIn("- **No:** continue straight to Step 2 in the same reply turn", text)

    def test_the_heads_up_follows_only_a_declined_switch(self):
        text = squash(step_1c())
        self.assertIn("Only when the bootcamper answered **no** to that switch question, open "
                      "the yes reply with one statement line, not a question", text)
        self.assertIn("Say nothing about the model when no switch question was asked", text)
        self.assertIn("or when they accepted the switch", text)
        heads_up = re.search(r"^> ℹ️ (.+)$", step_1c(), re.M)
        self.assertIsNotNone(heads_up, "the heads-up line must be pinned")
        self.assertNotIn("?", heads_up.group(1), "the heads-up is a statement, not a question")


class TheTimeBudget(unittest.TestCase):

    def test_the_table_holds_the_reporters_shares(self):
        table = budget_table()
        self.assertEqual(list(BUDGET), list(table), "the modules, in the bootcamp's order")
        for module, share in BUDGET.items():
            with self.subTest(module=module):
                self.assertEqual(share, table[module][1])
        self.assertEqual(100, sum(share for _t, share, _s in table.values()))

    def test_the_tokens_are_bootcamp_preparations(self):
        tokens = state_tokens()
        self.assertIn("business_problem", tokens.values(), "could not read the module list")
        for module, (token, _share, _seconds) in budget_table().items():
            with self.subTest(module=module):
                self.assertIn(token, tokens.values())
                if module in tokens:
                    self.assertEqual(tokens[module], token)

    def test_the_full_path_seconds_follow_the_formula(self):
        expected = scaled(BUDGET)
        for module, (_token, _share, seconds) in budget_table().items():
            with self.subTest(module=module):
                self.assertAlmostEqual(expected[module], seconds, places=1)
        self.assertAlmostEqual(120, sum(s for _t, _sh, s in budget_table().values()), places=6)

    def test_the_formula_and_its_rounding_are_stated(self):
        text = squash(step_1c())
        self.assertIn("The planned length is **2:00**", text)
        self.assertIn("`seconds = 120 × share ÷ (sum of the shares that count)`", text)
        self.assertIn("give any rounding remainder to Query, Visualize and Discover so the "
                      "total is exactly 120", text)
        self.assertIn("Bootcamp preparation and You graduated! always count", text)
        self.assertIn("Every other module counts only when it is in `modules_completed`", text)
        self.assertIn("scale the shares of the rest back up to 100%", text)

    def test_the_skipped_optional_modules_example_is_rescaled(self):
        counted = [m for m in BUDGET if m not in OPTIONAL]
        self.assertEqual(82, sum(BUDGET[m] for m in counted))
        self.assertIn("counts 82%", squash(step_1c()))
        rows = table_rows(step_1c(), "| Module | Seconds (82% counted)")
        example = {module: float(seconds) for module, seconds in rows}
        self.assertEqual(counted, list(example), "every counted module, and only those")
        expected = scaled(counted)
        for module in counted:
            with self.subTest(module=module):
                self.assertAlmostEqual(expected[module], example[module], places=1)
        self.assertAlmostEqual(120, sum(example.values()), places=6)


class TheStoryboard(unittest.TestCase):

    def test_the_example_is_a_valid_renderer_storyboard(self):
        video = load_renderer()
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual([], video.validate_storyboard(example_storyboard(), Path(root)))

    def test_the_example_runs_exactly_two_minutes(self):
        total = sum(scene["duration"] for scene in example_storyboard()["scenes"])
        self.assertAlmostEqual(120, total, places=6)

    def test_each_modules_scenes_add_up_to_its_seconds(self):
        by_token = {token: seconds for token, _share, seconds in budget_table().values()}
        planned = {}
        for scene in example_storyboard()["scenes"]:
            planned[scene["_module"]] = planned.get(scene["_module"], 0) + scene["duration"]
        self.assertEqual(set(by_token), set(planned), "a Core storyboard covers every module")
        for token, seconds in by_token.items():
            with self.subTest(module=token):
                self.assertAlmostEqual(seconds, planned[token], places=6)

    def test_scenes_follow_the_bootcamp_order(self):
        order = [token for token, _share, _seconds in budget_table().values()]
        seen = []
        for scene in example_storyboard()["scenes"]:
            if not seen or seen[-1] != scene["_module"]:
                seen.append(scene["_module"])
        self.assertEqual(order, seen)

    def test_it_has_the_five_animated_scenes(self):
        tokens = state_tokens()
        rows = {module: kind for module, kind, _from in
                table_rows(step_1c(), "| Module | Scene type | Built from")}
        scenes = example_storyboard()["scenes"]
        for module, kind in ANIMATED.items():
            with self.subTest(module=module):
                self.assertIn("`%s`" % kind, rows[module])
                self.assertTrue(any(s["_module"] == tokens[module] and s["type"] == kind
                                    for s in scenes),
                                "the example carries no %s scene for %s" % (kind, module))

    def test_it_ends_on_the_certificate_then_the_tag_line(self):
        scenes = example_storyboard()["scenes"]
        name = example_storyboard()["video"]["bootcamper"]
        self.assertEqual(["certificate", "tag_line"], [s["type"] for s in scenes[-2:]])
        self.assertEqual(TAG_LINE.replace("[Name]", name), scenes[-1]["text"])
        self.assertEqual(1, sum(s["type"] == "certificate" for s in scenes))
        self.assertEqual(1, sum(s["type"] == "tag_line" for s in scenes))

    def test_the_ending_is_stated(self):
        text = squash(step_1c())
        self.assertIn("The last two scenes are always the `certificate`, then the `tag_line` "
                      "with the text **\"%s\"**" % TAG_LINE, text)
        self.assertIn("where `[Name]` is `video.bootcamper`", text)

    def test_it_is_personalized_with_the_certificate_name(self):
        text = squash(step_1c())
        self.assertIn("`video.bootcamper` is the name the certificate prints", text)
        storyboard = example_storyboard()
        first = storyboard["video"]["bootcamper"].split()[0]
        self.assertIn(first, storyboard["scenes"][0]["narration"])

    def test_bootcamp_preparation_comes_from_the_preferences(self):
        text = squash(step_1c())
        self.assertIn("**Bootcamp preparation** always comes from "
                      "`config/bootcamp_preferences.yaml`", text)
        self.assertIn("That module writes no B-roll entry (#298)", text)

    def test_the_sources_and_the_older_bootcamp_fallback(self):
        text = squash(step_1c())
        self.assertIn("its entry in `docs/video/broll.json`, keyed by its state token", text)
        self.assertIn("**A bootcamp with no `broll.json`** (it started on an older plugin "
                      "version)", text)
        self.assertIn("`docs/bootcamp_recap.md` and the screenshots under "
                      "`docs/visualizations/`", text)

    def test_the_example_images_are_project_relative(self):
        for scene in example_storyboard()["scenes"]:
            if scene["type"] == "image":
                with self.subTest(image=scene["image"]):
                    self.assertTrue(scene["image"].startswith("docs/visualizations/"))


class NoRawRecordValues(unittest.TestCase):

    def test_the_rule_is_stated(self):
        text = squash(step_1c())
        self.assertIn("⛔ **(INV-340) Aggregates only: no raw record values anywhere in the storyboard.**",
                      text)
        self.assertIn("counts, source names, field and attribute names, and statistics", text)
        for forbidden in ("a name", "an address", "a phone number", "an identifier"):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, text)
        self.assertIn("the narration and captions included", text)
        self.assertIn("on the fallback path lift only its aggregates", text)

    def test_the_example_carries_only_aggregates(self):
        """Every string in a scene's data is a label, a module name or narration; every
        number is a count or statistic. No field holds a record's own value."""
        allowed_text = {"type", "narration", "caption", "module", "highlight", "heading",
                        "title", "image", "source", "text", "_module", "unit"}
        for scene in example_storyboard()["scenes"]:
            for key, value in scene.items():
                with self.subTest(scene=scene["_module"], key=key):
                    if isinstance(value, str):
                        self.assertIn(key, allowed_text)
                    elif isinstance(value, list):
                        self.assertIn(key, ("items", "fields", "sources"))

    def test_never_invent_a_number(self):
        self.assertIn("Never invent a number to fill a scene", squash(step_1c()))


class OnlyNameFreeScreenshots(unittest.TestCase):
    """#326: a screenshot can show record values, so the video takes only allow-listed tabs."""

    def test_the_rule_is_stated(self):
        text = squash(step_1c())
        self.assertIn("⛔ **(INV-340) Only name-free screenshots go in the video.**", text)
        self.assertIn("only when its file name is `<name>-<slug>.png` with `<slug>` one of the "
                      "three name-free tab slugs below", text)
        self.assertIn("Every other image is left out of the storyboard.", text)
        self.assertIn("**The allow-list is the only way in.**", text)

    def test_the_stated_allow_list_is_exactly_the_name_free_slugs(self):
        self.assertEqual(NAME_FREE_SLUGS, stated_name_free_slugs(step_1c()))

    def test_each_name_free_slug_is_a_capture_tab(self):
        tabs = capture_tab_slugs()
        self.assertIn("merge-statistics", tabs, "the TABS reader went vacuous")
        for slug in NAME_FREE_SLUGS:
            with self.subTest(slug=slug):
                self.assertIn(slug, tabs)

    def test_the_name_bearing_captures_are_named_as_left_out(self):
        left_out = [image + " " + tab for image, tab, verdict in
                    table_rows(step_1c(), "| Image | Tab | In the video") if verdict.startswith("no")]
        joined = " ".join(left_out)
        for named in ("`<name>-merge-statistics.png`", "`<name>-search-probe.png`",
                      "`<name>-entity-graph.png`", "`<name>.png`, a single-page capture",
                      "`relationship-network`", "`record-merges`"):
            with self.subTest(named=named):
                self.assertIn(named, joined)
        self.assertIn("whenever the graph has 40 nodes or fewer", squash(step_1c()))

    def test_the_example_uses_only_allow_listed_images(self):
        storyboard = example_storyboard()
        self.assertTrue(any(s["type"] == "image" for s in storyboard["scenes"]),
                        "the example carries no image scene, so this check would be vacuous")
        self.assertEqual([], image_problems(storyboard, stated_name_free_slugs(step_1c())))
        self.assertEqual([], image_problems(storyboard, NAME_FREE_SLUGS))

    def test_the_example_shows_truth_set_images_too(self):
        images = [s["image"] for s in example_storyboard()["scenes"]
                  if s["type"] == "image" and s["_module"] == "truthset_visualization"]
        self.assertTrue(images)
        self.assertTrue(all("/truthset_verification-" in image for image in images))

    def test_the_rule_reaches_the_truth_set_and_the_fallback(self):
        text = squash(step_1c())
        self.assertIn("**One rule for every image.** It applies to the Truth Set's images "
                      "(`truthset_verification-…`) as to the bootcamper's own, and on the "
                      "fallback path to the screenshots under `docs/visualizations/` the recap "
                      "embeds.", text)
        self.assertIn("Use only the name-free ones among them, by the same rule.", text)
        self.assertIn("Its name-free `images`", text)

    def test_a_module_left_with_no_image(self):
        text = squash(step_1c())
        self.assertIn("**A module left with no image** gets no `image` scene.", text)
        self.assertIn("in the same seconds", text)
        self.assertIn("**Nothing is cropped or edited.**", text)

    def test_the_results_row_says_name_free(self):
        rows = {module: built for module, _kind, built in
                table_rows(step_1c(), "| Module | Scene type | Built from")}
        self.assertIn("the name-free results screenshots", rows[REMAINDER_MODULE])

    def test_broll_images_are_not_called_aggregates(self):
        text = squash(read(GRADUATION))
        self.assertNotIn("`broll.json` already holds only aggregates", text)
        self.assertIn("`broll.json`'s text fields hold only aggregates (INV-341), but its "
                      "`images` name every screenshot the module produced", text)

    def test_module_completion_leaves_the_choice_to_graduation(self):
        text = squash(read(MODULE_COMPLETION))
        self.assertIn("List every screenshot the module produced, name-bearing ones included: "
                      "graduation, not this manifest, decides which are name-free enough for "
                      "the video (`../graduation/SKILL.md` Step 1c).", text)

    def test_negative_controls(self):
        allowed = stated_name_free_slugs(step_1c())
        for bad in ("docs/visualizations/truthset_verification-merge-statistics.png",
                    "docs/visualizations/results_visualization-entity-graph.png",
                    "docs/visualizations/results_visualization-search-probe.png",
                    "docs/visualizations/data_quality_assessment.png",
                    "docs/visualizations/results_visualization-record-merges.png"):
            with self.subTest(image=bad):
                storyboard = example_storyboard()
                scene = next(s for s in storyboard["scenes"] if s["type"] == "image")
                scene["image"] = bad
                self.assertEqual([bad], image_problems(storyboard, allowed))
        widened = step_1c().replace("| Entity Graph | no:", "| Entity Graph | yes:")
        self.assertNotEqual(widened, step_1c(), "the widening mutation matched nothing")
        self.assertNotEqual(NAME_FREE_SLUGS, stated_name_free_slugs(widened))
        narrowed = step_1c().replace("| Cross-Source | yes:", "| Cross-Source | no:")
        self.assertNotEqual(narrowed, step_1c(), "the narrowing mutation matched nothing")
        self.assertNotEqual(NAME_FREE_SLUGS, stated_name_free_slugs(narrowed))


class TheFallbacksNeverBlockGraduation(unittest.TestCase):

    def test_the_video_never_blocks(self):
        text = squash(step_1c())
        self.assertIn("⛔ **(INV-340) The video never blocks graduation (INV-048).**", text)
        self.assertIn("a declined install, a failed install, an invalid storyboard or a failed "
                      "render, skips the video with a one-line message naming what failed, and "
                      "graduation continues to Step 2", text)

    def test_every_exit_code_is_handled(self):
        text = squash(step_1c())
        self.assertIn("- **0, rendered.**", text)
        self.assertIn("- **1, invalid storyboard.** Each `INVALID:` line names the field at "
                      "fault. Fix those fields and run it again. If it is still invalid, skip "
                      "the video.", text)
        self.assertIn("- **2, a capability is missing.**", text)
        self.assertIn("- **3, the render failed.** Skip the video.", text)

    def test_a_declined_or_failed_install_skips_the_video(self):
        self.assertIn("On no, or when the venv or the install fails, skip the video and keep "
                      "the storyboard.", squash(step_1c()))

    def test_the_storyboard_is_kept(self):
        text = squash(step_1c())
        self.assertIn("⛔ **(INV-340) Keep the storyboard whenever it was written.**", text)
        self.assertIn("so the video can be rendered later by running the renderer again", text)

    def test_the_check_runs_before_the_render(self):
        text = step_1c()
        self.assertLess(text.index("generate_recap_video.py\" --check"),
                        text.index("generate_recap_video.py\"\n"))


class TheVideoIsChecked(unittest.TestCase):

    def verify(self):
        text = step_1c()
        return squash(text[text.index("#### Verify the video"):])

    def test_verify_the_artifact_not_the_exit_code(self):
        self.assertIn("⛔ **Verify the rendered video, not the exit code (INV-129, INV-340).**",
                      self.verify())

    def test_the_duration_tolerance_and_one_re_render(self):
        text = self.verify()
        self.assertIn("**Duration: within 2:00 ± 10 s**, that is 1:50 to 2:10", text)
        self.assertIn("re-render **once**", text)
        self.assertIn("If it is still outside, keep the video and say so", text)
        self.assertIn("Read it from the file", text)

    def test_frames_are_looked_at(self):
        text = self.verify()
        self.assertIn("Extract one frame at the midpoint of each scene, including the "
                      "certificate and the tag line, and look at each one", text)

    def test_audio_when_a_voice_or_the_music_is_present(self):
        """#339: item 3 reads the renderer's `Voice:` and `Music:` lines."""
        text = self.verify()
        self.assertIn("**Audio.** Read the renderer's `Voice:` and `Music:` lines. There is an "
                      "audio stream whenever either one is present: a `Voice:` line naming an "
                      "engine (`Voice: <engine> (<n> of <m> scenes narrated)`), or `Music: yes`. "
                      "Then the file carries an audio stream", text)
        self.assertIn("`Voice: none (…)` names why no voice spoke (`--no-voice`, `no speech "
                      "engine found`, or `<engine> voiced no scene`)", text)
        self.assertIn("that is not a failure", text)
        self.assertIn("Only with `Voice: none (…)` and `Music: off (storyboard)` together is "
                      "there no audio stream.", text)

    def test_the_exit_0_bullet_names_the_new_lines(self):
        self.assertIn("- **0, rendered.** It prints `Video generated:`, a `Duration:` line, a "
                      "`Voice:` line and a `Music:` line.", squash(step_1c()))

    def test_the_old_audio_track_line_is_gone_negative_control(self):
        self.assertNotIn("Audio track", step_1c())

    def test_skipped_checks_are_reported(self):
        text = self.verify()
        self.assertIn("A check that cannot run is recorded as skipped, naming the check "
                      "(INV-163)", text)
        self.assertIn("⛔ **Never install a tool only to run a check (INV-129).**", text)


class TheVideoIsNamedWhereTheBootcamperLooks(unittest.TestCase):

    def test_the_closing_names_the_video_when_it_was_produced(self):
        closing = squash(read(GRADUATION)[read(GRADUATION).index("## Mandatory closing step"):])
        self.assertIn("**(INV-340) Also name the graduation video, `docs/bootcamp_recap.mp4`, only if "
                      "Step 1c produced it:**", closing)

    def test_the_return_guide_names_it(self):
        guide = squash(section(read(GRADUATION), "### 6c. Return guide", "## Step 7:"))
        self.assertIn("Name `docs/bootcamp_recap.mp4` too when Step 1c produced it", guide)
        self.assertIn("`docs/video/storyboard.json` is kept", guide)


class ThePiperOfferIsPinned(unittest.TestCase):
    """#341: one pinned Piper install offer, after the storyboard, before the first render."""

    def piper(self):
        text = step_1c()
        return text[text.index("#### Offer the Piper voice"):text.index("#### Render it")]

    def test_the_offer_is_verbatim_and_asked_once(self):
        self.assertEqual(1, step_1c().count(PIPER_OFFER))
        self.assertIn("Ask it once per graduation (INV-006, INV-056)", squash(self.piper()))

    def test_it_comes_after_the_storyboard_and_before_the_first_render(self):
        text = step_1c()
        self.assertLess(text.index("#### Write the storyboard"), text.index(PIPER_OFFER))
        self.assertLess(text.index(PIPER_OFFER), text.index("generate_recap_video.py\" --check"))
        self.assertIn("after the storyboard is written and before the first render",
                      squash(self.piper()))

    def test_the_pillow_and_imageio_ffmpeg_variant(self):
        text = squash(self.piper())
        self.assertIn("When the venv will also get Pillow or `imageio-ffmpeg`", text)
        self.assertIn(PIPER_VARIANT, text)
        self.assertIn("Every other word stays the same", text)
        variant = PIPER_OFFER.replace("into `data/temp/recap-venv/`, and",
                                      "into `data/temp/recap-venv/` along with Pillow and "
                                      "`imageio-ffmpeg`, which rendering needs, and")
        self.assertNotEqual(PIPER_OFFER, variant, "the variant splices into the pinned offer")

    def test_it_is_made_only_when_piper_is_not_set_up(self):
        text = squash(self.piper())
        self.assertIn("`data/temp/recap-venv/` exists and its Python can find `piper`", text)
        self.assertIn("`en_US-ljspeech-high.onnx` and its `en_US-ljspeech-high.onnx.json` both "
                      "exist", text)
        self.assertIn("When Piper is set up, make no offer, and run `--check` and the render "
                      "below with the venv's Python", text)

    def test_yes_installs_into_the_project_with_an_explicit_interpreter(self):
        text = self.piper()
        flat = squash(text)
        self.assertIn("Run **one** `python -m pip install` with the venv's Python", flat)
        self.assertIn("plus Pillow when the venv's Python cannot `import PIL`", flat)
        self.assertIn("plus `imageio-ffmpeg` when there is no ffmpeg on `PATH`", flat)
        self.assertIn("data/temp/recap-venv/bin/python -m pip install piper-tts", text)
        self.assertIn("data/temp/recap-venv/bin/python -m piper.download_voices "
                      "en_US-ljspeech-high --data-dir data/temp/piper-voices", text)
        self.assertIn("skipping each step that is already satisfied", flat)
        self.assertNotRegex(text, r"(?m)^\s*pip install", "never a bare pip (INV-066)")
        self.assertNotRegex(text, r"(?m)^\s*sudo\b", "never sudo (INV-066)")

    def test_installs_go_only_into_the_two_project_folders(self):
        blocks = re.findall(r"```bash\n(.*?)```", self.piper(), re.S)
        self.assertEqual(1, len(blocks), "the Piper install has one command block")
        commands = [l for l in blocks[0].splitlines()
                    if " -m pip install" in l or "download_voices" in l]
        self.assertEqual(4, len(commands), "pip and the download, on Linux/macOS and Windows")
        for line in commands:
            with self.subTest(line=line):
                self.assertRegex(line, r"^data[/\\]temp[/\\]recap-venv[/\\]")
                if "download_voices" in line:
                    self.assertRegex(line, r"--data-dir data[/\\]temp[/\\]piper-voices$")

    def test_after_a_yes_the_venv_python_renders(self):
        flat = squash(self.piper())
        self.assertIn("When every step succeeds, **run `--check` and the render below with the "
                      "venv's Python** from then on", flat)
        self.assertIn("the exit-2 install offer cannot follow a successful install", flat)
        render = step_1c()[step_1c().index("#### Render it"):]
        self.assertIn('data/temp/recap-venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/'
                      'generate_recap_video.py" --check', render)

    def test_no_or_a_failure_renders_with_step_1bs_interpreter(self):
        flat = squash(self.piper())
        self.assertIn("**On no, or on any failure** (creating the venv, the `pip` install or "
                      "the download), render with the interpreter Step 1b used", flat)
        self.assertIn("Graduation continues (INV-048, INV-340), and the exit-2 install offer "
                      "still applies to that render", flat)

    def test_the_render_passes_no_voice_model(self):
        render = step_1c()[step_1c().index("#### Render it"):]
        self.assertIn("Pass no `--voice-model`", render)
        self.assertNotRegex(render, r"generate_recap_video\.py\"[^\n]*--voice-model")

    def test_the_offer_names_the_licenses(self):
        self.assertIn("`piper-tts` (GPL-3.0, runs on your machine)", PIPER_OFFER)
        self.assertIn("the public-domain `en_US-ljspeech-high` voice", PIPER_OFFER)

    def test_the_voice_is_named_from_the_voice_line(self):
        flat = squash(step_1c())
        self.assertIn("naming the voice from the renderer's `Voice:` line", flat)
        self.assertIn("narrated by Piper (en_US-ljspeech-high).", flat)


if __name__ == "__main__":
    unittest.main()
