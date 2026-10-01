"""Graduation Step 1c offers, writes, renders and checks the graduation video.

The video is the optional third keepsake (#297). Step 1c in `graduation/SKILL.md` turns the
B-roll every module saved (`module-completion.md` Step 2e, #298) into a storyboard and renders it
with the bundled renderer (`generate_recap_video.py`, #299). These tests pin:

* **Where it runs**: Step 1c sits right after Step 1b's recap PDF, before Step 2, because the
  video reuses the certificate's name and date. The preface's step overview and time estimate
  name the video as optional.
* **The two questions**, verbatim: the offer, and the one install offer after exit 2.
* **On no, nothing is written**; the heads-up line appears only after a declined model switch.
* **The time budget**: the reporter's shares, summing to 100%, scaled over the modules taken,
  with each worked example checked against the formula rather than trusted.
* **The storyboard**: the documented example validates through the renderer's own
  `validate_storyboard`, runs exactly 2:00, carries the five animated scenes, and ends on the
  certificate and then "Resolved: [Name], Senzing graduate.".
* ⛔ **No raw record values**, and the fallbacks never block graduation: exit 1, 2 and 3, a
  declined or failed install, the storyboard kept.
* **The checks**: 2:00 ± 10 s with one re-render, frames looked at, audio when a voice existed,
  skipped checks reported.
* **Where it is named**: the closing announcement and the return guide.

Stdlib only; the renderer's validator needs neither Pillow nor ffmpeg (INV-108).

Enforces **INV-340** (graduation's video step: offered once, nothing written on no, aggregates only,
never blocking, storyboard kept, the render verified). It asserts that Step 1c *states* these rules,
and does **not** establish that a live run follows them, which only `dry-run` phase 3 can observe.

Source issue: #300 (part of #297).

Run:  python3 -m unittest discover -s tests
"""
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

OFFER = ("> 👉 **Would you like a narrated 2-minute graduation video of your bootcamp?** "
         "(Saved to `docs/bootcamp_recap.mp4`; reply no to skip.)")
INSTALL = ("> 👉 **Rendering the video needs ffmpeg. May I install `imageio-ffmpeg` into this "
           "project's virtualenv?** (Reply no to skip the video; its storyboard is kept so you "
           "can render it later.)")
TAG_LINE = "Resolved: [Name], Senzing graduate."

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
        self.assertEqual(2, text.count("👉"), "Step 1c asks the offer and the install offer, "
                         "and nothing else")


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

    def test_audio_when_a_voice_was_available(self):
        text = self.verify()
        self.assertIn("When the renderer printed `Audio track: yes`, a speech engine was "
                      "available, and the file carries an audio stream", text)
        self.assertIn("that is not a failure", text)

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


if __name__ == "__main__":
    unittest.main()
