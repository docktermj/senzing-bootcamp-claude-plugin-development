"""The recap-video renderer: storyboard validation, frame drawing, and an end-to-end render.

`plugins/senzing-bootcamp/scripts/generate_recap_video.py` (#299) turns the storyboard the agent
writes at graduation into `docs/bootcamp_recap.mp4`. These tests pin its contract:

* **Validation** names the field at fault, exits 1 and writes nothing. It needs neither Pillow
  nor ffmpeg, so this tier runs everywhere, including the CI leg with no optional packages.
* **Images** must be project-relative local files; absolute paths, URLs and paths that escape
  the project are rejected, while a missing project-relative image becomes a title card.
* **Exit codes** are separate: 0 rendered, 1 invalid storyboard, 2 a required capability
  (ffmpeg or Pillow) is missing, 3 the encode failed. Nothing is written unless 0.
* **Fallbacks** are stated on stderr (INV-111): no speech engine, ffmpeg from imageio-ffmpeg,
  a missing image, no recap for the certificate.
* **The timeline** never truncates narration: an overrun extends its scene and is reported.
* **Frame drawing** is measured through `render_scene_frame`, the drawing layer's seam, which
  needs Pillow but not ffmpeg. Skipped with a reason when Pillow is absent.
* **The audio** is 48 kHz stereo: the narration, and a music bed synthesized with the standard
  library (deterministic, one 8 s cycle repeated), ducked under the voice by `sidechaincompress`
  and normalized by `loudnorm` in the encode's own ffmpeg call. The filter graph is asserted as a
  pure function; `find_ffmpeg` requires the two filters as it requires the encoders. The
  `Voice:` and `Music:` report lines are pinned, all four voice cases and both music cases (#339).
* **The Piper voice** (#341) is chosen by a voice-selection stage before the platform engines:
  Piper is found with a stubbed `find_spec` (never imported) and run through a fake subprocess
  as `sys.executable -m piper`. Each case that keeps it out is named on stderr; a failure on any
  scene re-voices every scene with the platform engine (a Piper that succeeds keeps every scene,
  the negative control); numbers are spelled out in Piper's text only; and the default voice is
  the public-domain `en_US-ljspeech-high`, never a `ryan`, `hfc_*` or `lessac` voice. Piper
  1.8.0 itself is never installed or run by these tests.
* **End to end**, an mp4 is rendered and probed: H.264, yuv420p, 1920x1080, 30 fps, and one
  48 kHz stereo AAC stream whenever a voice spoke or the music played, measuring -16 ± 1 LUFS
  with a true peak at or under -1.0 dBFS (ffmpeg's `ebur128`). Skipped with a reason when
  Pillow or ffmpeg is absent.
* **The voice leveler** (#372): every voiced stream is compressed, keyed on itself, before it
  keys the ducking or reaches `loudnorm`. Step 1c's worked two-minute storyboard, voiced by a
  speech-like stand-in (`FAKE_SPEECH`), measures in the band, and the same render with the
  graph from before #372 misses it (the negative control).

⚠️ Pillow and imageio-ffmpeg are optional dependencies of the *renderer under test*, declared in
`requirements-dev.txt` (INV-306). The tests themselves are standard library only (INV-108):
availability is probed with `importlib.util.find_spec`, and Pillow is reached only through the
script. The skip notices name the cause and the remedy and state no count.

Enforces **INV-342** (the renderer validates first, keeps exit codes 0/1/2/3 separate and writes no
video on failure, burns captions in, never truncates narration, accepts only project-relative local
images, works offline, and draws the certificate from the recap PDF's fields). It does **not**
establish the macOS and Windows speech paths, which it covers only by the commands it builds.

Source issues: #299, #339, #341, #372.

Run:  python3 -m unittest discover -s tests
"""
import array
import ast
import contextlib
import copy
import inspect
import textwrap
import importlib.machinery
import importlib.util
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
SCRIPT = SCRIPTS / "generate_recap_video.py"

INSTALL_HINT = "python3 -m pip install -r requirements-dev.txt"


def _load():
    spec = importlib.util.spec_from_file_location("generate_recap_video_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # Registered before it runs: its dataclasses resolve their own module through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VIDEO = _load()

HAVE_PILLOW = importlib.util.find_spec("PIL") is not None
HAVE_FFMPEG = bool(shutil.which("ffmpeg")) or importlib.util.find_spec("imageio_ffmpeg") is not None

requires_pillow = unittest.skipUnless(
    HAVE_PILLOW,
    "Pillow is not installed; these tests measure the frames the video renderer draws, and "
    "it cannot draw without Pillow (%s)" % INSTALL_HINT)

requires_pillow_and_ffmpeg = unittest.skipUnless(
    HAVE_PILLOW and HAVE_FFMPEG,
    "Pillow or ffmpeg is missing; an end-to-end render needs both. ffmpeg is looked for on "
    "PATH and from the imageio-ffmpeg package (%s)" % INSTALL_HINT)


def scenes_of_every_type():
    """One valid scene per type, in a sensible running order."""
    return [
        {"type": "title_card", "duration": 2, "narration": "It started with a business problem.",
         "module": "Business Problem", "highlight": "Three sources, one customer view"},
        {"type": "image", "duration": 2, "narration": "Here are the match keys.",
         "image": "docs/visualizations/results_visualization-match-keys.png",
         "heading": "Match keys"},
        {"type": "counter", "duration": 2, "narration": "Records loaded per source.",
         "title": "Records loaded",
         "items": [{"label": "CRM", "value": 1200}, {"label": "WEB", "value": 800}]},
        {"type": "mapping", "duration": 2, "narration": "Fields mapped to Senzing.",
         "source": "CRM", "fields": [{"from": "cust_name", "to": "NAME_FULL"},
                                     {"from": "addr1", "to": "ADDR_LINE1"}]},
        {"type": "loading", "duration": 2, "narration": "Loading the records.",
         "records": 5000, "entities": 3200},
        {"type": "entity_merge", "duration": 2, "narration": "Records converge.",
         "records": 12, "entities": 3, "sources": ["CRM", "WEB"]},
        {"type": "certificate", "duration": 2, "narration": "Congratulations.",
         "modules": ["1. Business Problem"]},
        {"type": "tag_line", "duration": 2, "narration": "Resolved."},
    ]


def a_storyboard(scenes=None):
    return {"video": {"bootcamper": "Ada Lovelace", "graduation_date": "2026-09-30"},
            "scenes": scenes if scenes is not None else scenes_of_every_type()}


def index_of(storyboard, kind):
    return next(i for i, s in enumerate(storyboard["scenes"]) if s["type"] == kind)


class Project:
    """A scratch project directory holding a storyboard (and, optionally, a screenshot)."""

    def __init__(self, storyboard, with_image=False):
        self._tmp = tempfile.TemporaryDirectory(prefix="sbcp-video-test-")
        self.root = Path(self._tmp.name)
        self.storyboard_path = self.root / "docs" / "video" / "storyboard.json"
        self.storyboard_path.parent.mkdir(parents=True)
        if isinstance(storyboard, str):
            self.storyboard_path.write_text(storyboard, encoding="utf-8")
        else:
            self.storyboard_path.write_text(json.dumps(storyboard), encoding="utf-8")
        self.output = self.root / "docs" / "bootcamp_recap.mp4"
        if with_image:
            self.write_screenshot("docs/visualizations/results_visualization-match-keys.png")

    def write_screenshot(self, rel):
        from PIL import Image, ImageDraw  # only reached from Pillow-guarded tests
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (1600, 1000), (240, 240, 240))
        draw = ImageDraw.Draw(img)
        for x in range(0, 1600, 80):
            draw.line((x, 0, x, 1000), fill=(200, 100, 50), width=4)
        img.save(path)
        return path

    def run(self, *extra, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--storyboard", str(self.storyboard_path),
             "--output", str(self.output), "--project-root", str(self.root), *extra],
            capture_output=True, text=True, cwd=str(self.root), env=env, timeout=600)

    def written(self):
        """Every video file under docs/, the partial included."""
        return sorted(p.name for p in (self.root / "docs").iterdir() if p.suffix in
                      (".mp4", ".partial") or p.name.endswith(".partial"))

    def close(self):
        self._tmp.cleanup()


def run_main(*argv):
    """main() in-process: (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = VIDEO.main(list(argv))
    return code, out.getvalue(), err.getvalue()


# --------------------------------------------------------------------------- #
# The table
# --------------------------------------------------------------------------- #
class TheSchemaIsOneTable(unittest.TestCase):
    def test_every_scene_type_the_issue_names_is_in_the_table(self):
        self.assertEqual(
            {"title_card", "image", "counter", "mapping", "loading", "entity_merge",
             "certificate", "tag_line"},
            set(VIDEO.SCENE_TYPES))

    def test_every_type_has_a_drawer_and_known_field_kinds(self):
        for name, scene_type in VIDEO.SCENE_TYPES.items():
            with self.subTest(scene_type=name):
                self.assertEqual(name, scene_type.name)
                self.assertTrue(callable(scene_type.draw))
                specs = list(scene_type.fields) + [
                    item for s in scene_type.fields for item in s.item_fields]
                for spec in specs:
                    self.assertIn(spec.kind, VIDEO.FIELD_KINDS, spec.name)

    def test_the_documented_types_are_the_table(self):
        """The docstring's list is what #300's author reads; it must not drift from the table."""
        documented = set(re.findall(r"^\* ``([a-z_]+)`` --", VIDEO.__doc__, re.M))
        self.assertEqual(set(VIDEO.SCENE_TYPES), documented)

    def test_the_documented_example_shows_only_name_free_screenshots(self):
        """#393: the docstring example is what a storyboard author copies, so its images obey
        graduation's name-free allow-list (INV-340's #326 note) and live where screenshots
        live, `docs/visualizations/`. The renderer itself still accepts any project-relative
        image (INV-342); this pins the example, not the behavior."""
        images = re.findall(r'"image":\s*"([^"]+)"', VIDEO.__doc__)
        self.assertTrue(images, "the docstring example names no image scene")
        for image in images:
            with self.subTest(image=image):
                self.assertRegex(
                    image,
                    r"^docs/visualizations/[a-z0-9_]+-(match-keys|feature-scores|cross-source)"
                    r"\.png$")

    def test_schema_flag_prints_the_table(self):
        code, out, _ = run_main("--schema")
        self.assertEqual(0, code)
        schema = json.loads(out)
        self.assertEqual(set(VIDEO.SCENE_TYPES), set(schema["scene_types"]))
        self.assertIn("image", schema["scene_types"]["image"]["fields"])


# --------------------------------------------------------------------------- #
# Validation: no Pillow, no ffmpeg
# --------------------------------------------------------------------------- #
class AValidStoryboardValidates(unittest.TestCase):
    def test_one_scene_of_every_type_is_valid(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual([], VIDEO.validate_storyboard(a_storyboard(), Path(root)))

    def test_comment_keys_are_ignored(self):
        board = a_storyboard()
        board["_note"] = "written by graduation"
        board["scenes"][0]["_why"] = "module 1 has nothing on screen"
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual([], VIDEO.validate_storyboard(board, Path(root)))

    def test_check_mode_exits_0_and_renders_nothing(self):
        project = Project(a_storyboard())
        self.addCleanup(project.close)
        result = project.run("--check")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Storyboard valid", result.stdout)
        self.assertEqual([], project.written())


class AnInvalidStoryboardNamesItsField(unittest.TestCase):
    """Exit 1, the named field on stderr, nothing written."""

    def problems(self, mutate):
        board = a_storyboard()
        mutate(board)
        with tempfile.TemporaryDirectory() as root:
            return VIDEO.validate_storyboard(board, Path(root))

    def assertNames(self, field_path, mutate):
        problems = self.problems(mutate)
        self.assertTrue(any(p.startswith(field_path + ":") for p in problems),
                        "expected a problem naming %s, got %r" % (field_path, problems))

    def test_missing_narration(self):
        self.assertNames("scenes[0].narration", lambda b: b["scenes"][0].pop("narration"))

    def test_unknown_scene_type(self):
        self.assertNames("scenes[0].type", lambda b: b["scenes"][0].update(type="slideshow"))

    def test_duration_must_be_positive_seconds(self):
        self.assertNames("scenes[0].duration", lambda b: b["scenes"][0].update(duration=0))
        self.assertNames("scenes[0].duration", lambda b: b["scenes"][0].update(duration=6000))
        self.assertNames("scenes[0].duration", lambda b: b["scenes"][0].update(duration="6"))

    def test_an_item_field_is_named_by_its_index(self):
        def bad(board):
            board["scenes"][index_of(board, "counter")]["items"][1]["value"] = "lots"
        self.assertNames("scenes[2].items[1].value", bad)

    def test_a_misspelt_field_is_not_silently_ignored(self):
        self.assertNames("scenes[0].hilight", lambda b: b["scenes"][0].update(hilight="x"))

    def test_the_video_metadata_is_required(self):
        self.assertNames("video.bootcamper", lambda b: b["video"].pop("bootcamper"))
        self.assertNames("video.graduation_date",
                         lambda b: b["video"].update(graduation_date="30/09/2026"))
        self.assertNames("video.graduation_date",
                         lambda b: b["video"].update(graduation_date="2026-02-30"))

    def test_more_entities_than_records(self):
        def bad(board):
            board["scenes"][index_of(board, "entity_merge")]["entities"] = 99
        self.assertNames("scenes[5].entities", bad)

    def test_no_scenes(self):
        self.assertNames("scenes", lambda b: b.update(scenes=[]))

    def test_the_cli_exits_1_and_writes_nothing(self):
        board = a_storyboard()
        del board["scenes"][0]["narration"]
        project = Project(board)
        self.addCleanup(project.close)
        result = project.run()
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("INVALID: scenes[0].narration", result.stderr)
        self.assertNotIn("Video generated", result.stdout)
        self.assertEqual([], project.written())

    def test_malformed_json_exits_1_and_writes_nothing(self):
        project = Project('{"video": {"bootcamper": "Ada"')
        self.addCleanup(project.close)
        result = project.run()
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("not valid JSON", result.stderr)
        self.assertEqual([], project.written())


class ImagesMustBeProjectRelative(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "project"
        self.root.mkdir()

    def problem(self, value):
        return VIDEO.project_relative_problem(value, self.root)

    def test_a_relative_path_inside_the_project_is_accepted(self):
        self.assertIsNone(self.problem("docs/visualizations/results_visualization-match-keys.png"))

    def test_a_missing_relative_image_is_not_a_validation_error(self):
        """It becomes a title card at render time; see FallbacksAreStated."""
        self.assertIsNone(self.problem("docs/visualizations/not-there.png"))

    def test_absolute_paths_are_rejected(self):
        for value in ("/etc/hosts", "C:\\Users\\ada\\shot.png", "C:shot.png",
                      "\\\\server\\share\\shot.png", "~/shot.png"):
            with self.subTest(value=value):
                self.assertIn("absolute", self.problem(value) or "")

    def test_urls_are_rejected(self):
        for value in ("https://example.com/shot.png", "http://localhost/shot.png",
                      "file:///etc/hosts", "data:image/png;base64,AAAA"):
            with self.subTest(value=value):
                self.assertIn("URL", self.problem(value) or "")

    def test_escaping_the_project_is_rejected(self):
        self.assertIn("outside the project", self.problem("../elsewhere/shot.png") or "")
        self.assertIn("outside the project", self.problem("docs/../../shot.png") or "")

    @unittest.skipIf(sys.platform == "win32", "creating symlinks needs privileges on Windows")
    def test_a_symlink_out_of_the_project_is_rejected(self):
        outside = Path(self._tmp.name) / "secret.png"
        outside.write_bytes(b"not really a png")
        (self.root / "docs").mkdir()
        os.symlink(outside, self.root / "docs" / "shot.png")
        self.assertIn("outside the project", self.problem("docs/shot.png") or "")

    def test_the_storyboard_names_the_rejected_image_field(self):
        board = a_storyboard()
        board["scenes"][1]["image"] = "https://example.com/shot.png"
        problems = VIDEO.validate_storyboard(board, self.root)
        self.assertTrue(any(p.startswith("scenes[1].image:") for p in problems), problems)

    def test_the_certificate_recap_path_obeys_the_same_rule(self):
        board = a_storyboard()
        board["scenes"][index_of(board, "certificate")]["recap"] = "/etc/passwd"
        problems = VIDEO.validate_storyboard(board, self.root)
        self.assertTrue(any(".recap:" in p for p in problems), problems)

    def test_a_url_image_exits_1_without_fetching_or_writing(self):
        board = a_storyboard()
        board["scenes"][1]["image"] = "https://example.com/shot.png"
        project = Project(board)
        self.addCleanup(project.close)
        result = project.run()
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("scenes[1].image", result.stderr)
        self.assertEqual([], project.written())


class TheRendererIsOffline(unittest.TestCase):
    def test_no_network_module_is_imported(self):
        source = SCRIPT.read_text(encoding="utf-8")
        pattern = re.compile(r"^\s*(?:import|from)\s+(%s)\b" % "|".join(VIDEO.NETWORK_MODULES),
                             re.M)
        self.assertEqual([], pattern.findall(source),
                         "the renderer must open only local files and never fetch")


# --------------------------------------------------------------------------- #
# Exit codes and capabilities
# --------------------------------------------------------------------------- #
class ExitCodesAreDocumented(unittest.TestCase):
    def test_the_codes_are_distinct(self):
        codes = (VIDEO.EXIT_RENDERED, VIDEO.EXIT_INVALID_STORYBOARD,
                 VIDEO.EXIT_MISSING_CAPABILITY, VIDEO.EXIT_RENDER_FAILED)
        self.assertEqual((0, 1, 2, 3), codes)

    def test_the_docstring_documents_each_code(self):
        doc = VIDEO.__doc__
        for line in ("0 rendered", "1 invalid storyboard",
                     "2 a required capability is missing (no ffmpeg, or no Pillow)",
                     "3 the encode itself failed"):
            self.assertIn(line, doc)


class AMissingCapabilityExits2(unittest.TestCase):
    """No Pillow or no ffmpeg: exit 2, the cause and remedy on stderr, nothing written."""

    def setUp(self):
        self.project = Project(a_storyboard())
        self.addCleanup(self.project.close)

    def main(self):
        return run_main("--storyboard", str(self.project.storyboard_path),
                        "--output", str(self.project.output),
                        "--project-root", str(self.project.root))

    def test_no_pillow(self):
        with mock.patch.object(VIDEO, "_find_spec", return_value=None):
            code, out, err = self.main()
        self.assertEqual(2, code, err)
        self.assertIn("Pillow is not installed for %s" % sys.executable, err)
        self.assertIn("python3 -m pip install Pillow", err)
        self.assertNotIn("Video generated", out)
        self.assertEqual([], self.project.written())

    def test_no_ffmpeg_on_path_or_from_imageio(self):
        with mock.patch.object(VIDEO, "load_pillow", return_value=(None, None, None)), \
                mock.patch.object(VIDEO.shutil, "which", return_value=None), \
                mock.patch.object(VIDEO, "_imageio_ffmpeg",
                                  return_value=(None, "imageio-ffmpeg is not installed")):
            code, out, err = self.main()
        self.assertEqual(2, code, err)
        self.assertIn("ffmpeg is not on PATH", err)
        self.assertIn("python3 -m pip install imageio-ffmpeg", err)
        self.assertEqual([], self.project.written())

    def test_the_cli_exits_2_without_ffmpeg(self):
        """Out of process: PATH holds no ffmpeg and imageio-ffmpeg is hidden."""
        if importlib.util.find_spec("imageio_ffmpeg") is not None:
            self.skipTest("imageio-ffmpeg is installed here, so ffmpeg cannot be made absent "
                          "out of process; the in-process test covers this branch")
        if not HAVE_PILLOW:
            self.skipTest("Pillow is not installed, so the render stops at the Pillow check "
                          "first; test_no_pillow covers that (%s)" % INSTALL_HINT)
        empty = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, empty)
        env = dict(os.environ, PATH=empty)
        result = self.project.run("--no-voice", env=env)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("no usable ffmpeg", result.stderr)
        self.assertEqual([], self.project.written())


class FallbacksAreStated(unittest.TestCase):
    """INV-111: every lesser path says so on stderr."""

    def test_ffmpeg_comes_from_imageio_when_path_has_none(self):
        fake = types.ModuleType("imageio_ffmpeg")
        fake.__spec__ = importlib.machinery.ModuleSpec("imageio_ffmpeg", None)
        fake.get_ffmpeg_exe = lambda: "/opt/imageio/ffmpeg-bundled"
        with mock.patch.dict(sys.modules, {"imageio_ffmpeg": fake}), \
                mock.patch.object(VIDEO.shutil, "which", return_value=None), \
                mock.patch.object(VIDEO, "missing_encoders", return_value=[]), \
                mock.patch.object(VIDEO, "missing_filters", return_value=[]):
            path, notes = VIDEO.find_ffmpeg()
        self.assertEqual("/opt/imageio/ffmpeg-bundled", path)
        self.assertEqual(1, len(notes))
        self.assertIn("ffmpeg is not on PATH", notes[0])
        self.assertIn("imageio-ffmpeg", notes[0])

    def test_path_ffmpeg_without_the_encoders_falls_back_and_says_why(self):
        def lacking(exe):
            return ["libx264"] if exe == "/usr/local/bin/ffmpeg" else []
        with mock.patch.object(VIDEO.shutil, "which", return_value="/usr/local/bin/ffmpeg"), \
                mock.patch.object(VIDEO, "_imageio_ffmpeg", return_value=("/opt/ff", "")), \
                mock.patch.object(VIDEO, "missing_encoders", side_effect=lacking), \
                mock.patch.object(VIDEO, "missing_filters", return_value=[]):
            path, notes = VIDEO.find_ffmpeg()
        self.assertEqual("/opt/ff", path)
        self.assertIn("lacks the libx264 encoder", notes[0])

    def test_path_ffmpeg_is_preferred_and_silent(self):
        with mock.patch.object(VIDEO.shutil, "which", return_value="/usr/bin/ffmpeg"), \
                mock.patch.object(VIDEO, "missing_encoders", return_value=[]), \
                mock.patch.object(VIDEO, "missing_filters", return_value=[]):
            self.assertEqual(("/usr/bin/ffmpeg", []), VIDEO.find_ffmpeg())

    def test_no_speech_engine_means_captions_only(self):
        with mock.patch.object(VIDEO.shutil, "which", return_value=None):
            engine, note = VIDEO.choose_voice(False)
        self.assertIsNone(engine)
        self.assertIn("no speech engine found", note)
        self.assertIn("captions carry the narration", note)

    def test_no_voice_flag_is_stated_too(self):
        engine, note = VIDEO.choose_voice(True)
        self.assertIsNone(engine)
        self.assertIn("--no-voice", note)

    def test_linux_engines_are_tried_in_order(self):
        found = {"espeak": "/usr/bin/espeak"}
        with mock.patch.object(VIDEO.shutil, "which", side_effect=found.get), \
                mock.patch.object(VIDEO.sys, "platform", "linux"):
            engine, tried = VIDEO.find_speech_engine()
        self.assertEqual("espeak", engine.name)
        self.assertEqual(["espeak-ng (not on PATH)"], tried)
        argv, _env = engine.command("in.txt", "out.wav")
        self.assertEqual(["/usr/bin/espeak", "-w", "out.wav", "-f", "in.txt"], argv)

    def test_the_certificate_without_a_recap_uses_the_storyboard_and_says_so(self):
        notes = []
        with tempfile.TemporaryDirectory() as root:
            cert = VIDEO.certificate_fields(
                {"type": "certificate", "modules": ["1. Business Problem"]},
                {"bootcamper": "Ada Lovelace", "graduation_date": "2026-09-30"},
                Path(root), notes.append)
        self.assertEqual("Ada Lovelace", cert.name)
        self.assertEqual("September 30, 2026", cert.date)
        self.assertEqual(["1. Business Problem"], cert.modules)
        self.assertTrue(any("no recap at docs/bootcamp_recap.md" in n for n in notes), notes)

    @requires_pillow
    def test_a_missing_image_becomes_a_title_card(self):
        board = a_storyboard()
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stderr(err):
            ctx = VIDEO.RenderContext(VIDEO.load_pillow(), board["video"], Path(root))
            plan = VIDEO.plan_timeline(board, ctx, None, None, None)
        self.assertEqual("title_card", plan[1].kind)
        self.assertEqual("image", plan[1].type)
        self.assertIn("FALLBACK: scenes[1] (image): image "
                      "docs/visualizations/results_visualization-match-keys.png not found; "
                      "drawing a title card instead.", err.getvalue())

    @requires_pillow
    def test_an_unreadable_image_becomes_a_title_card(self):
        board = a_storyboard()
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stderr(err):
            path = (Path(root) / "docs" / "visualizations"
                    / "results_visualization-match-keys.png")
            path.parent.mkdir(parents=True)
            path.write_bytes(b"this is not a png")
            ctx = VIDEO.RenderContext(VIDEO.load_pillow(), board["video"], Path(root))
            plan = VIDEO.plan_timeline(board, ctx, None, None, None)
        self.assertEqual("title_card", plan[1].kind)
        self.assertIn("could not be read", err.getvalue())


RECAP = """# Senzing Bootcamp Recap

**Bootcamper:** Recap Name
**Started:** 2026-09-01T09:00:00+00:00
**Completed:** 2026-09-29

---

## Business Problem — 2026-09-01T10:00:00+00:00

### Information Shared

- The problem.

### Questions & Responses

- **Q:** Why? **R:** Because.

### Actions Taken

- Wrote it down.

### End-of-Module Summary

**What you accomplished:** defined the problem.

**Files produced:** `docs/business_problem.md`

**Why it matters:** everything follows from it.

---
"""


class TheCertificateIsTheRecapPdfs(unittest.TestCase):
    """INV-100: the same name, date and module list as the recap PDF's certificate."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "bootcamp_recap.md").write_text(RECAP, encoding="utf-8")
        self.recap_pdf = importlib.import_module("generate_recap_pdf")

    def fields(self):
        notes = []
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            cert = VIDEO.certificate_fields(
                {"type": "certificate"},
                {"bootcamper": "Ada Lovelace", "graduation_date": "2026-09-30"},
                self.root, notes.append)
        return cert, notes, err.getvalue()

    def test_the_fields_are_what_the_recap_pdf_prints(self):
        cert, notes, err = self.fields()
        expected = self.recap_pdf._cert_fields(self.recap_pdf.parse_recap(RECAP))
        self.assertEqual(expected, (cert.name, cert.date, cert.modules))
        self.assertEqual("Recap Name", cert.name)
        self.assertEqual([], notes)
        self.assertIn("certificate prints 'Recap Name'", err,
                      "a storyboard name that differs from the certificate's must be stated")

    def test_the_preferences_name_outranks_the_recap_as_it_does_for_the_pdf(self):
        (self.root / "config").mkdir()
        (self.root / "config" / "bootcamp_preferences.yaml").write_text(
            "name: Preferred Name\n", encoding="utf-8")
        cert, _notes, _err = self.fields()
        self.assertEqual("Preferred Name", cert.name)
        self.assertEqual("", self.recap_pdf._CERTIFICATE_NAME_OVERRIDE,
                         "the override must be cleared after it is read")


# --------------------------------------------------------------------------- #
# The timeline
# --------------------------------------------------------------------------- #
def pcm_seconds(seconds):
    return b"\x01\x00" * int(seconds * VIDEO.AUDIO_RATE)


FAKE_ENGINE = VIDEO.SpeechEngine("fake-voice", lambda txt, wav: ([], {}))


@requires_pillow
class NarrationIsNeverTruncated(unittest.TestCase):
    def plan(self, board, engine, pcm_for=None, failing=False):
        err = io.StringIO()

        def synth(engine, text, ffmpeg, workdir, stem):
            if failing:
                raise RuntimeError("the voice fell over")
            return pcm_for(text)

        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stderr(err), \
                mock.patch.object(VIDEO, "synthesize_pcm", side_effect=synth):
            ctx = VIDEO.RenderContext(VIDEO.load_pillow(), board["video"], Path(root))
            plan = VIDEO.plan_timeline(board, ctx, engine, "ffmpeg", Path(root))
        return plan, err.getvalue()

    def test_a_long_narration_extends_its_scene_and_is_reported(self):
        board = a_storyboard([
            {"type": "title_card", "duration": 2, "narration": "long", "module": "A"},
            {"type": "title_card", "duration": 3, "narration": "short", "module": "B"},
        ])
        plan, err = self.plan(board, FAKE_ENGINE,
                              lambda text: pcm_seconds(10 if text == "long" else 0.5))
        need = VIDEO.NARRATION_LEAD + 10 + VIDEO.NARRATION_TAIL
        self.assertGreaterEqual(plan[0].duration, need)
        self.assertLess(plan[0].duration, need + 1.0 / VIDEO.FPS + 1e-9)
        self.assertEqual(plan[0].frames, round(plan[0].duration * VIDEO.FPS))
        self.assertEqual(3.0, plan[1].duration, "a narration that fits keeps the planned length")
        self.assertIn("OVERRUN: scenes[0] (title_card)", err)
        self.assertNotIn("OVERRUN: scenes[1]", err)
        self.assertTrue(plan[0].voiced and plan[1].voiced)

    def test_without_a_voice_the_estimate_extends_the_scene(self):
        words = " ".join(["word"] * 80)
        board = a_storyboard([
            {"type": "title_card", "duration": 2, "narration": words, "module": "A"}])
        plan, err = self.plan(board, None)
        self.assertGreaterEqual(plan[0].duration, 80 * 60 / VIDEO.WORDS_PER_MINUTE)
        self.assertIn("OVERRUN: scenes[0]", err)
        self.assertIn("no voice", err)
        self.assertFalse(plan[0].voiced)

    def test_a_failed_synthesis_is_stated_and_the_scene_is_captioned(self):
        board = a_storyboard([
            {"type": "title_card", "duration": 2, "narration": "hello", "module": "A"}])
        plan, err = self.plan(board, FAKE_ENGINE, failing=True)
        self.assertFalse(plan[0].voiced)
        self.assertIn("could not voice this narration", err)

    def test_the_audio_track_is_frame_aligned(self):
        board = a_storyboard([
            {"type": "title_card", "duration": 1, "narration": "one", "module": "A"},
            {"type": "title_card", "duration": 1.25, "narration": "two", "module": "B"},
        ])
        plan, _err = self.plan(board, FAKE_ENGINE, lambda text: pcm_seconds(0.2))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "track.wav"
            VIDEO.write_audio_track(plan, path)
            with wave.open(str(path), "rb") as track:
                self.assertEqual(48000, track.getframerate())
                self.assertEqual(2, track.getnchannels(), "the track is stereo")
                self.assertEqual(sum(p.frames for p in plan) * VIDEO.SAMPLES_PER_FRAME,
                                 track.getnframes())
                both = struct.unpack("<%dh" % (2 * track.getnframes()),
                                     track.readframes(track.getnframes()))
        samples = both[0::2]
        self.assertEqual(samples, both[1::2], "the narration is the same on both channels")
        lead = int(VIDEO.NARRATION_LEAD * VIDEO.AUDIO_RATE)
        self.assertEqual(0, max(samples[:lead]), "the narration starts after the lead-in")
        self.assertEqual(1, samples[lead])
        second = plan[0].frames * VIDEO.SAMPLES_PER_FRAME
        self.assertEqual(1, samples[second + lead], "scene 2's narration starts at scene 2")


# --------------------------------------------------------------------------- #
# The audio: the music switch, the bed, the mix graph, the filters, the report lines (#339)
# --------------------------------------------------------------------------- #
class TheMusicSwitchIsValidated(unittest.TestCase):
    def problems(self, board):
        with tempfile.TemporaryDirectory() as root:
            return VIDEO.validate_storyboard(board, Path(root))

    def test_true_false_and_absent_are_valid(self):
        for value in (True, False, None):
            with self.subTest(music=value):
                board = a_storyboard()
                if value is not None:
                    board["video"]["music"] = value
                self.assertEqual([], self.problems(board))

    def test_a_non_boolean_names_the_field(self):
        for value in ("yes", 1, 0, "false", None, []):
            with self.subTest(music=value):
                board = a_storyboard()
                board["video"]["music"] = value
                problems = self.problems(board)
                self.assertTrue(any(p.startswith("video.music:") for p in problems), problems)

    def test_the_cli_exits_1_naming_the_field(self):
        board = a_storyboard()
        board["video"]["music"] = "on"
        project = Project(board)
        self.addCleanup(project.close)
        result = project.run()
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("INVALID: video.music: must be true or false", result.stderr)
        self.assertEqual([], project.written())

    def test_the_schema_names_it(self):
        _code, out, _err = run_main("--schema")
        music = json.loads(out)["video"]["music"]
        self.assertEqual("boolean", music["kind"])
        self.assertFalse(music["required"])
        self.assertIn("defaults to true", music["help"])


def modules_reached(func, seen=None):
    """Top-level names of every module `func` reaches: the modules its globals name and the
    import statements in its source, following each module-level function it calls."""
    seen = set() if seen is None else seen
    seen.add(func)
    found = set()
    for node in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(func)))):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])

    def names(code):
        yield from code.co_names
        for const in code.co_consts:
            if isinstance(const, types.CodeType):
                yield from names(const)

    for name in names(func.__code__):
        value = func.__globals__.get(name)
        if isinstance(value, types.ModuleType):
            found.add(value.__name__.split(".")[0])
        elif isinstance(value, types.FunctionType) and value not in seen:
            found |= modules_reached(value, seen)
    return found


def _bed_with_a_global_numpy():
    return numpy.zeros(4)  # noqa: F821 -- given a fake numpy below; never called


def _bed_importing_numpy():
    import numpy  # noqa: F401 -- never called; only its source is read
    return b""


class TheMusicBedIsStdlibAndDeterministic(unittest.TestCase):
    def test_it_reaches_only_the_standard_library(self):
        if not hasattr(sys, "stdlib_module_names"):
            self.skipTest("sys.stdlib_module_names needs Python 3.10 or later")
        reached = modules_reached(VIDEO.write_music_bed)
        self.assertIn("math", reached, "the walk did not reach the synthesizer")
        self.assertEqual(set(), reached - set(sys.stdlib_module_names),
                         "the music bed must need nothing beyond the standard library")

    def test_the_check_catches_numpy_negative_control(self):
        fake = types.FunctionType(_bed_with_a_global_numpy.__code__,
                                  {"numpy": types.ModuleType("numpy")})
        self.assertIn("numpy", modules_reached(fake))
        self.assertIn("numpy", modules_reached(_bed_importing_numpy))

    def test_the_same_length_gives_the_same_bytes(self):
        self.assertEqual(VIDEO.synthesize_music_bed(3.5), VIDEO.synthesize_music_bed(3.5))

    def test_it_is_48k_stereo_and_spans_the_length(self):
        bed = VIDEO.synthesize_music_bed(3.5)
        self.assertEqual(48000, VIDEO.AUDIO_RATE)
        self.assertEqual(round(3.5 * 48000) * 2 * 2, len(bed))
        samples = array.array("h", bed)
        self.assertEqual((0, 0), (samples[0], samples[1]), "the fade-in starts from silence")
        self.assertLess(max(abs(v) for v in samples[-200:]), 400, "the fade-out ends quiet")
        self.assertGreater(max(abs(v) for v in samples), 4000, "the bed is silent")
        self.assertNotEqual(samples[0::2], samples[1::2], "the arpeggio is panned")

    def test_one_cycle_is_repeated(self):
        """Between the fades, the bed is one 8 s cycle repeated."""
        rate = VIDEO.AUDIO_RATE
        samples = array.array("h", VIDEO.synthesize_music_bed(20))
        start, cycle = 2 * rate * 2, 8 * rate * 2
        self.assertEqual(samples[start:start + 7 * rate * 2],
                         samples[start + cycle:start + cycle + 7 * rate * 2])

    def test_the_wav_is_written_at_48k_stereo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "music.wav"
            VIDEO.write_music_bed(1.0, path)
            with wave.open(str(path), "rb") as bed:
                self.assertEqual((2, 2, 48000, 48000), (bed.getnchannels(), bed.getsampwidth(),
                                                        bed.getframerate(), bed.getnframes()))


def graph_sources(graph):
    """Each label of an ffmpeg filter graph -> the input streams ("1:a", ...) it derives from."""
    sources = {}
    for chain in graph.split(";"):
        ins = re.match(r"((?:\[[^\]]+\])*)", chain).group(1)
        outs = re.search(r"((?:\[[^\]]+\])*)$", chain).group(1)
        derived = set()
        for label in re.findall(r"\[([^\]]+)\]", ins):
            derived |= sources.get(label, {label})
        for label in re.findall(r"\[([^\]]+)\]", outs):
            sources[label] = derived
    return sources


def sidechain_inputs(graph, compressor=VIDEO.DUCKING):
    """(main input's sources, sidechain key's sources) of the graph's `compressor` chain.

    The ducking compressor by default. The voice's leveler (#372) is a second
    sidechaincompress, keyed on the voice itself, so each is picked by its own parameters. A
    ducking chain written without them (a negative control's) is the first sidechaincompress
    that is not the leveler.
    """
    leveler = VIDEO.LEVELER.split(";")[-1].split("]")[-1]
    params = compressor.split(";")[-1].split("]")[-1]
    chains = graph.split(";")
    chain = next((c for c in chains if params in c), None)
    if chain is None and compressor is VIDEO.DUCKING:
        chain = next((c for c in chains if "sidechaincompress" in c and leveler not in c), None)
    if chain is None:
        raise StopIteration("no %s chain in %s" % (params, graph))
    main, key = re.findall(r"\[([^\]]+)\]", re.match(r"((?:\[[^\]]+\])*)", chain).group(1))
    sources = graph_sources(graph)
    return sources.get(main, {main}), sources.get(key, {key})


def unleveled_graph(voice, music):
    """The graph as it was before #372: no leveler, the voice split straight into key and mix.

    The negative control for the leveler. A real two-minute narration mixed this way measured
    about -17.6 LUFS, outside -16 ± 1.
    """
    if voice is not None and music is not None:
        return (f"[{music}:a]volume={VIDEO.MUSIC_VOLUME}[music];"
                f"[{voice}:a]asplit=2[key][voice];"
                f"[music][key]{VIDEO.DUCKING}[ducked];"
                f"[ducked][voice]amix=inputs=2:duration=first,{VIDEO.LOUDNORM}[aout]")
    alone = voice if voice is not None else music
    return None if alone is None else f"[{alone}:a]{VIDEO.LOUDNORM}[aout]"


class TheMixGraphDucksTheMusicUnderTheVoice(unittest.TestCase):
    LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"

    def test_the_voice_keys_the_compressor_on_the_music(self):
        graph = VIDEO.audio_filter_graph(1, 2)
        self.assertEqual(({"2:a"}, {"1:a"}), sidechain_inputs(graph))
        self.assertIn("[2:a]volume=0.3[", graph)
        self.assertIn("sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600", graph)

    def test_the_mix_of_voice_and_ducked_music_ends_in_loudnorm(self):
        graph = VIDEO.audio_filter_graph(1, 2)
        self.assertTrue(graph.endswith(",%s[aout]" % self.LOUDNORM), graph)
        self.assertEqual({"1:a", "2:a"}, graph_sources(graph)["aout"])
        last = graph.split(";")[-1]
        self.assertIn("amix=inputs=2", last)

    def test_a_graph_keyed_on_the_music_is_caught_negative_control(self):
        swapped = ("[2:a]asplit=2[key][music];[1:a]volume=0.3[voice];"
                   "[voice][key]sidechaincompress[ducked];[ducked][music]amix,%s[aout]"
                   % self.LOUDNORM)
        self.assertNotEqual(({"2:a"}, {"1:a"}), sidechain_inputs(swapped))

    def test_one_loudness_target_for_every_stream(self):
        self.assertEqual("[1:a]%s[aout]" % self.LOUDNORM, VIDEO.audio_filter_graph(None, 1))
        self.assertEqual("[1:a]%s,%s[aout]" % (self.LEVELER, self.LOUDNORM),
                         VIDEO.audio_filter_graph(1, None))
        self.assertIsNone(VIDEO.audio_filter_graph(None, None))

    # The voice leveler (#372): every voiced stream is compressed, keyed on itself, before it
    # keys the ducking or reaches loudnorm. The parameters are the ones #372 measured.
    LEVELER = ("asplit=2[lv][lk];"
               "[lv][lk]sidechaincompress=threshold=0.05:ratio=4:attack=5:release=150:makeup=1")

    def test_the_leveler_is_keyed_on_the_voice_itself(self):
        self.assertEqual(self.LEVELER, VIDEO.LEVELER)
        for graph in (VIDEO.audio_filter_graph(1, 2), VIDEO.audio_filter_graph(1, None)):
            self.assertEqual(({"1:a"}, {"1:a"}), sidechain_inputs(graph, VIDEO.LEVELER), graph)

    def test_the_voice_is_leveled_before_the_ducking_split(self):
        graph = VIDEO.audio_filter_graph(1, 2)
        self.assertIn("[1:a]%s,asplit=2[key][voice];" % self.LEVELER, graph)
        self.assertLess(graph.index(self.LEVELER), graph.index(VIDEO.DUCKING))
        self.assertEqual(1, graph.count("[lv][lk]sidechaincompress"))

    def test_an_unleveled_graph_is_caught_negative_control(self):
        """Today's chain before #372 (the voice split straight into key and mix) fails."""
        unleveled = unleveled_graph(1, 2)
        self.assertNotIn(self.LEVELER, unleveled)
        with self.assertRaises(StopIteration):
            sidechain_inputs(unleveled, VIDEO.LEVELER)

    def test_the_encode_call_carries_the_graph(self):
        voice, music, out = Path("voice.wav"), Path("music.wav"), Path("out.mp4")
        cmd = VIDEO.encode_command("ffmpeg", voice, out, music)
        self.assertEqual(["voice.wav", "music.wav"],
                         [cmd[i + 1] for i, a in enumerate(cmd) if a == "-i"][1:])
        self.assertEqual(VIDEO.audio_filter_graph(1, 2), cmd[cmd.index("-filter_complex") + 1])
        self.assertEqual("[aout]", cmd[cmd.index("[aout]")])
        self.assertEqual("48000", cmd[cmd.index("-ar") + 1])
        self.assertEqual("2", cmd[cmd.index("-ac") + 1])
        self.assertEqual("aac", cmd[cmd.index("-c:a") + 1])

    def test_music_alone_is_input_1(self):
        cmd = VIDEO.encode_command("ffmpeg", None, Path("out.mp4"), Path("music.wav"))
        self.assertEqual(VIDEO.audio_filter_graph(None, 1), cmd[cmd.index("-filter_complex") + 1])

    def test_no_voice_and_no_music_maps_no_audio(self):
        cmd = VIDEO.encode_command("ffmpeg", None, Path("out.mp4"), None)
        for flag in ("-filter_complex", "-c:a", "-ac"):
            self.assertNotIn(flag, cmd)
        self.assertEqual(1, cmd.count("-i"))


FILTERS_LISTING = """Filters:
  T.. = Timeline support
 ..C sidechaincompress AA->A      Sidechain compressor.
 ... loudnorm          A->A       EBU R128 loudness normalization
 ..C amix              N->A       Audio mixing.
"""


class FfmpegNeedsTheMixFilters(unittest.TestCase):
    """The two filters are required the way the libx264 and aac encoders are."""

    def listing(self, stdout):
        return mock.patch.object(VIDEO.subprocess, "run", return_value=types.SimpleNamespace(
            stdout=stdout, stderr="", returncode=0))

    def test_the_probe_reads_ffmpeg_filters(self):
        with self.listing(FILTERS_LISTING):
            self.assertEqual([], VIDEO.missing_filters("ffmpeg"))

    def test_the_probe_names_a_missing_filter_negative_control(self):
        without = "\n".join(l for l in FILTERS_LISTING.splitlines() if "loudnorm" not in l)
        with self.listing(without):
            self.assertEqual(["loudnorm"], VIDEO.missing_filters("ffmpeg"))

    def test_a_binary_that_cannot_run_lacks_both(self):
        with mock.patch.object(VIDEO.subprocess, "run", side_effect=OSError("no such file")):
            self.assertEqual(["sidechaincompress", "loudnorm"], VIDEO.missing_filters("x"))

    def test_path_ffmpeg_without_a_filter_falls_back_and_names_it(self):
        def lacking(exe):
            return ["loudnorm"] if exe == "/usr/local/bin/ffmpeg" else []
        with mock.patch.object(VIDEO.shutil, "which", return_value="/usr/local/bin/ffmpeg"), \
                mock.patch.object(VIDEO, "_imageio_ffmpeg", return_value=("/opt/ff", "")), \
                mock.patch.object(VIDEO, "missing_encoders", return_value=[]), \
                mock.patch.object(VIDEO, "missing_filters", side_effect=lacking):
            path, notes = VIDEO.find_ffmpeg()
        self.assertEqual("/opt/ff", path)
        self.assertIn("lacks the loudnorm filter", notes[0])
        self.assertIn("imageio-ffmpeg", notes[0])

    def test_neither_with_the_filters_exits_2(self):
        project = Project(a_storyboard())
        self.addCleanup(project.close)
        with mock.patch.object(VIDEO, "load_pillow", return_value=(None, None, None)), \
                mock.patch.object(VIDEO.shutil, "which", return_value="/usr/local/bin/ffmpeg"), \
                mock.patch.object(VIDEO, "_imageio_ffmpeg", return_value=("/opt/ff", "")), \
                mock.patch.object(VIDEO, "missing_encoders", return_value=[]), \
                mock.patch.object(VIDEO, "missing_filters", return_value=["sidechaincompress"]):
            code, out, err = run_main("--storyboard", str(project.storyboard_path),
                                      "--output", str(project.output),
                                      "--project-root", str(project.root))
        self.assertEqual(2, code, err)
        self.assertIn("no usable ffmpeg", err)
        self.assertIn("lacks the sidechaincompress filter", err)
        self.assertIn("python3 -m pip install imageio-ffmpeg", err)
        self.assertNotIn("Video generated", out)
        self.assertEqual([], project.written())


@requires_pillow
class TheReportNamesVoiceAndMusic(unittest.TestCase):
    """The exact `Voice:` and `Music:` lines, without ffmpeg: the encode is stubbed, and the
    stub records which audio inputs the renderer handed it."""

    def setUp(self):
        self.board = a_storyboard([
            {"type": "title_card", "duration": 1, "narration": "one", "module": "A"},
            {"type": "title_card", "duration": 1, "narration": "two", "module": "B"},
        ])
        self.inputs = None

    def render(self, *flags, music=None, engine=FAKE_ENGINE, synth=None, found=True):
        if music is not None:
            self.board["video"]["music"] = music
        project = Project(self.board)
        self.addCleanup(project.close)

        def encode(ctx, plan, ffmpeg, audio, output, log_path, music=None):
            self.inputs = (audio, music)
            output.write_bytes(b"mp4")
            return True, ""

        engines = ((engine, []) if found else (None, ["espeak-ng (not on PATH)"]))
        with mock.patch.object(VIDEO, "find_ffmpeg", return_value=("ffmpeg", [])), \
                mock.patch.object(VIDEO, "find_speech_engine", return_value=engines), \
                mock.patch.object(VIDEO, "synthesize_pcm",
                                  side_effect=synth or (lambda *a: pcm_seconds(0.2))), \
                mock.patch.object(VIDEO, "stream_frames", side_effect=encode):
            code, out, err = run_main("--storyboard", str(project.storyboard_path),
                                      "--output", str(project.output),
                                      "--project-root", str(project.root), *flags)
        self.assertEqual(0, code, err)
        return out.splitlines()[2:], err

    def test_a_voice_that_spoke(self):
        lines, _err = self.render()
        self.assertEqual(["Voice: fake-voice (2 of 2 scenes narrated)", "Music: yes"], lines)
        self.assertTrue(all(self.inputs), "the narration and the music both reach the encode")

    def test_some_scenes_voiced(self):
        def synth(engine, text, *rest):
            if text == "two":
                raise RuntimeError("the voice fell over")
            return pcm_seconds(0.2)
        lines, _err = self.render(synth=synth)
        self.assertEqual("Voice: fake-voice (1 of 2 scenes narrated)", lines[0])

    def test_no_voice_flag(self):
        lines, _err = self.render("--no-voice")
        self.assertEqual(["Voice: none (--no-voice)", "Music: yes"], lines)
        self.assertIsNone(self.inputs[0])
        self.assertIsNotNone(self.inputs[1], "--no-voice turns off only the voice")

    def test_no_speech_engine(self):
        lines, _err = self.render(found=False)
        self.assertEqual(["Voice: none (no speech engine found)", "Music: yes"], lines)
        self.assertIsNotNone(self.inputs[1])

    def test_an_engine_that_voiced_no_scene(self):
        def synth(*args):
            raise RuntimeError("the voice fell over")
        lines, err = self.render(synth=synth)
        self.assertEqual(["Voice: none (fake-voice voiced no scene)", "Music: yes"], lines)
        self.assertIn("fake-voice voiced no scene", err)

    def test_music_off_with_a_voice(self):
        lines, _err = self.render(music=False)
        self.assertEqual(["Voice: fake-voice (2 of 2 scenes narrated)",
                          "Music: off (storyboard)"], lines)
        self.assertIsNone(self.inputs[1])

    def test_music_off_and_no_voice_means_no_audio_stream(self):
        lines, err = self.render("--no-voice", music=False)
        self.assertEqual(["Voice: none (--no-voice)", "Music: off (storyboard)"], lines)
        self.assertEqual((None, None), self.inputs)
        self.assertIn("the video has no audio stream", err)

    def test_the_old_line_is_gone_negative_control(self):
        lines, _err = self.render()
        self.assertFalse(any(l.startswith("Audio track:") for l in lines), lines)
        self.assertNotIn("Voice: none", "\n".join(lines))


# --------------------------------------------------------------------------- #
# Frame drawing: Pillow, no ffmpeg
# --------------------------------------------------------------------------- #
@requires_pillow
class FramesAreDrawn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = Project(a_storyboard(), with_image=True)
        cls.board = a_storyboard()
        cls._err = contextlib.redirect_stderr(io.StringIO())
        cls._err.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._err.__exit__(None, None, None)
        cls.project.close()

    def frame(self, index, t, board=None):
        return VIDEO.render_scene_frame(board or self.board, index, t, self.project.root)

    def test_every_scene_type_draws_a_full_hd_rgb_frame(self):
        for index, scene in enumerate(self.board["scenes"]):
            with self.subTest(scene_type=scene["type"]):
                img = self.frame(index, 1.5)
                self.assertEqual((VIDEO.WIDTH, VIDEO.HEIGHT), img.size)
                self.assertEqual("RGB", img.mode)
                spread = max(hi - lo for lo, hi in img.getextrema())
                self.assertGreater(spread, 60, "the frame is blank")

    def test_the_animated_types_move(self):
        from PIL import ImageChops
        for kind in ("image", "counter", "mapping", "loading", "entity_merge"):
            with self.subTest(scene_type=kind):
                index = index_of(self.board, kind)
                early, late = self.frame(index, 0.5), self.frame(index, 1.8)
                self.assertIsNotNone(ImageChops.difference(early, late).getbbox(),
                                     "%s draws the same frame at 0.5 s and 1.8 s" % kind)

    def caption_band(self, img):
        return img.crop((0, VIDEO.HEIGHT - 200, VIDEO.WIDTH, VIDEO.HEIGHT))

    def test_the_caption_is_burned_in(self):
        from PIL import ImageChops
        board = copy.deepcopy(self.board)
        board["scenes"][0]["caption"] = "A completely different caption"
        with_caption = self.frame(0, 1.5, board)
        default = self.frame(0, 1.5)
        self.assertIsNotNone(
            ImageChops.difference(self.caption_band(with_caption),
                                  self.caption_band(default)).getbbox(),
            "changing the caption changed nothing at the foot of the frame")

    def test_the_caption_defaults_to_the_narration(self):
        from PIL import ImageChops
        board = copy.deepcopy(self.board)
        board["scenes"][0]["caption"] = board["scenes"][0]["narration"]
        self.assertIsNone(ImageChops.difference(self.frame(0, 1.5, board),
                                                self.frame(0, 1.5)).getbbox())

    def test_captions_are_burned_in_without_a_voice(self):
        """Planned with no voice at all, every scene's finished frame still carries its caption:
        the foot of the frame differs from what the scene's drawer alone produced."""
        from PIL import ImageChops
        ctx = VIDEO.RenderContext(VIDEO.load_pillow(), self.board["video"], self.project.root)
        plan = VIDEO.plan_timeline(self.board, ctx, None, None, None)
        for ps in plan:
            with self.subTest(scene_type=ps.type):
                t = ps.duration / 2
                drawn = VIDEO.SCENE_TYPES[ps.kind].draw(ctx, ps, t)
                finished = VIDEO.frame_image(ctx, ps, t)
                self.assertFalse(ps.voiced)
                self.assertIsNotNone(
                    ImageChops.difference(self.caption_band(drawn),
                                          self.caption_band(finished)).getbbox(),
                    "no caption was burned into the %s frame" % ps.type)

    def test_a_long_caption_is_paged_not_cut(self):
        board = copy.deepcopy(self.board)
        board["scenes"][0]["narration"] = " ".join("resolution%d" % n for n in range(60))
        ctx = VIDEO.RenderContext(VIDEO.load_pillow(), board["video"], self.project.root)
        plan = VIDEO.plan_timeline(board, ctx, None, None, None)
        chunks = plan[0].chunks
        self.assertGreater(len(chunks), 1)
        self.assertEqual(board["scenes"][0]["narration"].split(),
                         " ".join(chunks).split(), "a word of the caption was lost")
        shown = [VIDEO.caption_at(plan[0], t / 10) for t in range(int(plan[0].duration * 10))]
        self.assertEqual(chunks, list(dict.fromkeys(shown)),
                         "every caption screen is shown, in order")

    def test_an_invalid_storyboard_is_refused_by_the_drawing_seam(self):
        board = copy.deepcopy(self.board)
        del board["scenes"][0]["narration"]
        with self.assertRaises(ValueError):
            self.frame(0, 1.0, board)


# --------------------------------------------------------------------------- #
# End to end: Pillow and ffmpeg
# --------------------------------------------------------------------------- #
FAKE_ESPEAK = """#!{python}
import math, struct, sys, wave
out = sys.argv[sys.argv.index("-w") + 1]
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
    w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(i / 8.0)))
                           for i in range(int(22050 * 1.5))))
"""

# A speech-like stand-in for espeak-ng (#372), standard library only and deterministic. Real
# narration peaks far above its loudness: voiced syllables are glottal-pulse trains (in-phase
# harmonics), stress varies syllable to syllable, and pauses are short. FAKE_ESPEAK's steady
# sine has none of that, which is why it normalized fine while real speech did not. Tuned
# against a real espeak-ng narration of Step 1c's worked storyboard (-17.5 LUFS, -0.9 dBTP
# assembled): this one assembles to about -19.2 LUFS, -0.8 dBTP, and through the chain
# before #372 its mix measures about -18.5 LUFS, as real speech's did (-17.6).
FAKE_SPEECH = """#!{python}
import math, random, struct, sys, wave
RATE = 22050
def speak(text, rng, base=15000):
    out = []
    for word in text.split():
        for _ in range(max(1, min(4, sum(ch in "aeiouyAEIOUY" for ch in word)))):
            if rng.random() < 0.4:  # a fricative onset
                n = int(RATE * 0.06)
                out += [int(0.18 * base * math.sin(math.pi * i / n) * rng.uniform(-1, 1))
                        for i in range(n)]
            amp = base * (1.0 if rng.random() < 0.2 else rng.choice((0.25, 0.45)))  # stress
            f0, glide = rng.uniform(100, 160), rng.uniform(-0.25, 0.25)
            n, phase = int(RATE * rng.uniform(0.12, 0.22)), 0.0
            for i in range(n):
                phase += 2 * math.pi * f0 * (1 + glide * i / n) / RATE
                env = math.sin(math.pi * i / n) ** 0.6
                out.append(int(amp * env * sum(math.cos(k * phase) for k in range(1, 9)) / 4))
            out += [0] * int(RATE * 0.01)
        out += [0] * int(RATE * 0.03)
        if word[-1:] in ".,!?:;":
            out += [0] * int(RATE * 0.2)
    return out
out = sys.argv[sys.argv.index("-w") + 1]
text = open(sys.argv[sys.argv.index("-f") + 1], encoding="utf-8").read()
pcm = speak(text, random.Random(len(text)))
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, s))) for s in pcm))
"""


def fake_engine_env(root, script=FAKE_SPEECH):
    """An environment whose PATH finds `script` as espeak-ng first."""
    fake_bin = Path(root) / "fake-bin"
    fake_bin.mkdir(exist_ok=True)
    espeak = fake_bin / "espeak-ng"
    espeak.write_text(script.format(python=sys.executable), encoding="utf-8")
    espeak.chmod(0o755)
    return dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ.get("PATH", ""))


def probe(ffmpeg, path):
    return subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True,
                          text=True, timeout=120).stderr


@requires_pillow_and_ffmpeg
class TheVideoIsRendered(unittest.TestCase):
    def setUp(self):
        self.ffmpeg, _notes = VIDEO.find_ffmpeg()
        self.scenes = scenes = [
            {"type": "title_card", "duration": 1, "narration": "Hi.", "module": "Business Problem"},
            {"type": "image", "duration": 1, "narration": "Match keys.",
             "image": "docs/visualizations/results_visualization-match-keys.png",
             "heading": "Match keys"},
            {"type": "image", "duration": 1, "narration": "Gone.",
             "image": "docs/visualizations/missing.png"},
            {"type": "certificate", "duration": 1, "narration": "Well done."},
            {"type": "tag_line", "duration": 1, "narration": "Resolved."},
        ]
        self.project = Project(a_storyboard(scenes), with_image=True)
        self.addCleanup(self.project.close)

    def assertPlayableMp4(self, result, audio):
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Video generated: %s" % self.project.output, result.stdout)
        self.assertTrue(self.project.output.is_file())
        self.assertEqual(["bootcamp_recap.mp4"], self.project.written(),
                         "the partial file was left behind")
        info = probe(self.ffmpeg, self.project.output)
        self.assertRegex(info, r"Video: h264")
        self.assertIn("yuv420p", info)
        self.assertIn("1920x1080", info)
        self.assertRegex(info, r"\b30 fps\b")
        printed = float(re.search(r"^Duration: \d+:\d\d \(([\d.]+) s", result.stdout,
                                  re.M).group(1))
        h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info).groups()
        self.assertAlmostEqual(printed, int(h) * 3600 + int(m) * 60 + float(s), delta=0.2)
        if audio:
            self.assertEqual(1, len(re.findall(r"Audio: aac", info)), info)
            self.assertRegex(info, r"Audio: aac.*48000 Hz, stereo")
        else:
            self.assertNotIn("Audio:", info)
        self.assertNotIn("Audio track:", result.stdout, "the old report line is gone")
        self.assertIn("FALLBACK: scenes[2] (image): image docs/visualizations/missing.png not "
                      "found; drawing a title card instead.", result.stderr)
        self.assertIn("no recap at docs/bootcamp_recap.md", result.stderr)

    def test_no_voice_still_carries_the_music(self):
        result = self.project.run("--no-voice")
        self.assertPlayableMp4(result, audio=True)
        self.assertIn("--no-voice", result.stderr)
        self.assertIn("Voice: none (--no-voice)\nMusic: yes\n", result.stdout)

    def test_no_voice_and_no_music_has_no_audio_stream(self):
        board = a_storyboard(self.scenes)
        board["video"]["music"] = False
        self.project.storyboard_path.write_text(json.dumps(board), encoding="utf-8")
        result = self.project.run("--no-voice")
        self.assertPlayableMp4(result, audio=False)
        self.assertIn("Voice: none (--no-voice)\nMusic: off (storyboard)\n", result.stdout)
        self.assertIn("the video has no audio stream", result.stderr)

    @unittest.skipIf(sys.platform in ("win32", "darwin"),
                     "the stand-in voice is an espeak-ng on PATH, which Windows and macOS "
                     "would pass over for their own built-in engines")
    def test_with_a_voice(self):
        """A stand-in espeak-ng speaks 1.5 s per scene: every 1 s scene overruns."""
        fake_bin = self.project.root / "fake-bin"
        fake_bin.mkdir()
        espeak = fake_bin / "espeak-ng"
        espeak.write_text(FAKE_ESPEAK.format(python=sys.executable), encoding="utf-8")
        espeak.chmod(0o755)
        env = dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ.get("PATH", ""))
        result = self.project.run(env=env)
        self.assertPlayableMp4(result, audio=True)
        self.assertIn("Voice: espeak-ng (5 of 5 scenes narrated)\nMusic: yes\n", result.stdout)
        self.assertEqual(5, len(re.findall(r"^OVERRUN: scenes\[\d\]", result.stderr, re.M)),
                         result.stderr)
        printed = float(re.search(r"\(([\d.]+) s,", result.stdout).group(1))
        need = 5 * (VIDEO.NARRATION_LEAD + 1.5 + VIDEO.NARRATION_TAIL)
        self.assertGreaterEqual(printed + 1e-6, need, "a narration was cut short")

    def test_an_existing_video_survives_a_failed_encode(self):
        self.project.output.write_bytes(b"previous video")
        with mock.patch.object(VIDEO, "encode_command",
                               return_value=[self.ffmpeg, "-f", "no-such-format", "-i",
                                             "pipe:0", "x.mp4"]):
            code, out, err = run_main(
                "--storyboard", str(self.project.storyboard_path),
                "--output", str(self.project.output),
                "--project-root", str(self.project.root), "--no-voice")
        self.assertEqual(3, code, err)
        self.assertIn("no video written", err)
        self.assertEqual(b"previous video", self.project.output.read_bytes())
        self.assertEqual(["bootcamp_recap.mp4"], self.project.written())


def integrated_lufs(ffmpeg, path):
    """The integrated loudness of `path`'s audio, measured by ffmpeg's ebur128 filter."""
    r = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a",
                        "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True,
                       timeout=300)
    found = re.findall(r"^\s*I:\s+(-?[\d.]+) LUFS", r.stderr, re.M)
    if not found:
        raise AssertionError("ebur128 measured nothing: %s" % r.stderr[-500:])
    return float(found[-1])


def true_peak(ffmpeg, path):
    """The true peak of `path`'s audio in dBFS, as delivered (ebur128, peak=true)."""
    r = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a",
                        "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True,
                       text=True, timeout=300)
    found = re.findall(r"^\s*Peak:\s+(-?[\d.]+|-inf) dBFS", r.stderr, re.M)
    if not found:
        raise AssertionError("ebur128 measured no true peak: %s" % r.stderr[-500:])
    return float(found[-1])


#: The true-peak limit on the delivered AAC (#372). loudnorm targets -1.5 dBTP; AAC encoding
#: overshoots that by a few tenths of a dB, which this limit allows for.
DELIVERED_TRUE_PEAK = -1.0


@requires_pillow_and_ffmpeg
class TheMixIsNormalizedToMinus16Lufs(unittest.TestCase):
    """One target for every stream: voice and music, or music alone, at -16 ± 1 LUFS."""

    def setUp(self):
        self.ffmpeg, _notes = VIDEO.find_ffmpeg()
        listing = subprocess.run([self.ffmpeg, "-hide_banner", "-filters"],
                                 capture_output=True, text=True, timeout=60).stdout
        if not re.search(r"^\s*\S+\s+ebur128\b", listing, re.M):
            self.skipTest("this ffmpeg has no ebur128 filter, so loudness cannot be measured")
        scenes = [{"type": "title_card", "duration": 3, "narration": "Scene %d." % n,
                   "module": "Module %d" % n} for n in range(4)]
        self.project = Project(a_storyboard(scenes))
        self.addCleanup(self.project.close)

    def assertNormalized(self, result):
        self.assertEqual(0, result.returncode, result.stderr)
        info = probe(self.ffmpeg, self.project.output)
        self.assertEqual(1, len(re.findall(r"Audio: aac", info)), info)
        self.assertRegex(info, r"Audio: aac.*48000 Hz, stereo")
        lufs = integrated_lufs(self.ffmpeg, self.project.output)
        self.assertAlmostEqual(-16.0, lufs, delta=1.0)
        self.assertLessEqual(true_peak(self.ffmpeg, self.project.output), DELIVERED_TRUE_PEAK)

    @unittest.skipIf(sys.platform in ("win32", "darwin"),
                     "the stand-in voice is an espeak-ng on PATH, which Windows and macOS "
                     "would pass over for their own built-in engines")
    def test_voice_alone(self):
        """`video.music: false` with a speech-like voice: the leveled voice alone (#372)."""
        storyboard = json.loads(self.project.storyboard_path.read_text(encoding="utf-8"))
        storyboard["video"]["music"] = False
        self.project.storyboard_path.write_text(json.dumps(storyboard), encoding="utf-8")
        result = self.project.run(env=fake_engine_env(self.project.root))
        self.assertIn("Voice: espeak-ng (4 of 4 scenes narrated)\nMusic: off (storyboard)\n",
                      result.stdout)
        self.assertNormalized(result)

    def test_music_alone(self):
        result = self.project.run("--no-voice")
        self.assertIn("Voice: none (--no-voice)\nMusic: yes\n", result.stdout)
        self.assertNormalized(result)

    @unittest.skipIf(sys.platform in ("win32", "darwin"),
                     "the stand-in voice is an espeak-ng on PATH, which Windows and macOS "
                     "would pass over for their own built-in engines")
    def test_voice_and_music(self):
        fake_bin = self.project.root / "fake-bin"
        fake_bin.mkdir()
        espeak = fake_bin / "espeak-ng"
        espeak.write_text(FAKE_ESPEAK.format(python=sys.executable), encoding="utf-8")
        espeak.chmod(0o755)
        env = dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ.get("PATH", ""))
        result = self.project.run(env=env)
        self.assertIn("Voice: espeak-ng (4 of 4 scenes narrated)\nMusic: yes\n", result.stdout)
        self.assertNormalized(result)


def worked_storyboard():
    """Step 1c's worked two-minute storyboard, read by the suite's one copy of the parser."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import test_graduation_video_step  # noqa: E402 - a sibling test module, as in INV-265's guard
    return test_graduation_video_step.example_storyboard()


@requires_pillow_and_ffmpeg
@unittest.skipIf(sys.platform in ("win32", "darwin"),
                 "the stand-in voice is an espeak-ng on PATH, which Windows and macOS would "
                 "pass over for their own built-in engines")
class TheWorkedStoryboardReachesTheTargetWithASpeechLikeVoice(unittest.TestCase):
    """#372: a two-minute speech-like narration with the music measures -16 ± 1 LUFS.

    The short scenes above normalize with or without the leveler; a full narration did not
    (-17.6 LUFS with real espeak-ng, -17.9 with Piper). So this renders Step 1c's own worked
    storyboard, voiced by FAKE_SPEECH, and renders it again in-process with the graph from
    before #372 as the negative control: that one must miss the target.
    """

    @classmethod
    def setUpClass(cls):
        cls.ffmpeg, _notes = VIDEO.find_ffmpeg()
        listing = subprocess.run([cls.ffmpeg, "-hide_banner", "-filters"],
                                 capture_output=True, text=True, timeout=60).stdout
        if not re.search(r"^\s*\S+\s+ebur128\b", listing, re.M):
            raise unittest.SkipTest("this ffmpeg has no ebur128 filter, so loudness cannot "
                                    "be measured")
        cls.scenes = len(worked_storyboard()["scenes"])
        cls.project = Project(worked_storyboard())
        env = fake_engine_env(cls.project.root)
        cls.result = cls.project.run(env=env)
        cls.control = cls.project.root / "docs" / "unleveled.mp4"
        with mock.patch.dict(os.environ, {"PATH": env["PATH"]}), \
                mock.patch.object(VIDEO, "audio_filter_graph", unleveled_graph):
            cls.control_code, _out, cls.control_err = run_main(
                "--storyboard", str(cls.project.storyboard_path), "--output", str(cls.control),
                "--project-root", str(cls.project.root))

    @classmethod
    def tearDownClass(cls):
        cls.project.close()

    def test_it_is_voiced_with_the_music(self):
        self.assertEqual(0, self.result.returncode, self.result.stderr)
        self.assertIn("Voice: espeak-ng (%d of %d scenes narrated)\nMusic: yes\n"
                      % (self.scenes, self.scenes), self.result.stdout)

    def test_the_mix_measures_minus_16_lufs(self):
        self.assertEqual(0, self.result.returncode, self.result.stderr)
        self.assertAlmostEqual(-16.0, integrated_lufs(self.ffmpeg, self.project.output),
                               delta=1.0)

    def test_the_true_peak_stays_under_the_delivered_limit(self):
        self.assertEqual(0, self.result.returncode, self.result.stderr)
        self.assertLessEqual(true_peak(self.ffmpeg, self.project.output), DELIVERED_TRUE_PEAK)

    def test_the_unleveled_chain_misses_the_target_negative_control(self):
        """Without the leveler the same render falls outside the band, so the test can fail."""
        self.assertEqual(0, self.control_code, self.control_err)
        self.assertLess(integrated_lufs(self.ffmpeg, self.control), -17.0)


# --------------------------------------------------------------------------- #
# The Piper voice: the voice-selection stage before the platform engines (#341)
# --------------------------------------------------------------------------- #
PIPER_SPEC = importlib.machinery.ModuleSpec("piper", None)
_REAL_FIND_SPEC = VIDEO._find_spec


def piper_findable(name):
    """A stand-in for `find_spec`: `piper` is findable, everything else is as it really is."""
    return PIPER_SPEC if name == "piper" else _REAL_FIND_SPEC(name)


def piper_missing(name):
    return None if name == "piper" else _REAL_FIND_SPEC(name)


def write_voice(root, model=True, config=True, rel=None):
    """The default voice's model and config under `root`; returns the model's path."""
    path = Path(root) / (rel or VIDEO.DEFAULT_VOICE_MODEL)
    path.parent.mkdir(parents=True, exist_ok=True)
    if model:
        path.write_bytes(b"onnx")
    if config:
        VIDEO.piper_config_path(path).write_text("{}", encoding="utf-8")
    return path


class FakeProcesses:
    """A fake `subprocess.run` for Piper, a platform engine and ffmpeg's decode.

    Each engine writes a WAV whose samples all carry its own marker, and the fake decode hands
    the samples back, so a scene's PCM says which engine voiced it. `calls` records each
    engine run with the text it was given, in order.
    """

    PIPER, PLATFORM = 7, 3

    def __init__(self, piper_fails_on=None):
        self.piper_fails_on = piper_fails_on
        self.calls = []

    def run(self, argv, **_kw):
        argv = [str(a) for a in argv]
        if argv[0] == "ffmpeg":
            data = Path(argv[argv.index("-i") + 1]).read_bytes()[44:]
            return subprocess.CompletedProcess(argv, 0, stdout=data, stderr=b"")
        if argv[:3] == [sys.executable, "-m", "piper"]:
            who, marker = "piper", self.PIPER
            text_file, wav = argv[argv.index("-i") + 1], argv[argv.index("-f") + 1]
        elif argv[0] == "fake-platform":
            who, marker, text_file, wav = "platform", self.PLATFORM, argv[1], argv[2]
        else:
            raise AssertionError("unexpected subprocess %r" % argv)
        text = Path(text_file).read_text(encoding="utf-8")
        self.calls.append((who, text))
        if who == "piper" and self.piper_fails_on and self.piper_fails_on in text:
            return subprocess.CompletedProcess(argv, 1, stdout=b"", stderr=b"piper fell over")
        Path(wav).write_bytes(b"\0" * 44 + struct.pack("<h", marker) * 4800)
        return subprocess.CompletedProcess(argv, 0, stdout=b"", stderr=b"")

    def who(self):
        return [who for who, _text in self.calls]


FAKE_PLATFORM = VIDEO.SpeechEngine("fake-platform",
                                   lambda txt, wav: (["fake-platform", txt, wav], {}))


def markers(pcm):
    return set(array.array("h", pcm))


class NumbersAreSpelledForPiper(unittest.TestCase):
    """`spell_numbers` is pure: integers with and without separators, and decimals."""

    CASES = {
        "10,000": "ten thousand",
        "3.5": "three point five",
        "0": "zero",
        "19": "nineteen",
        "42": "forty-two",
        "100": "one hundred",
        "7084": "seven thousand eighty-four",
        "1,540": "one thousand five hundred forty",
        "2,000,001": "two million one",
        "3.50": "three point five zero",
    }

    def test_the_pinned_cases(self):
        for digits, words in self.CASES.items():
            with self.subTest(digits=digits):
                self.assertEqual(words, VIDEO.spell_numbers(digits))

    def test_numbers_inside_a_sentence(self):
        self.assertEqual("All one thousand five hundred forty records loaded into one "
                         "thousand three hundred ten entities.",
                         VIDEO.spell_numbers("All 1,540 records loaded into 1,310 entities."))
        self.assertEqual("In two thousand twenty-six, one hundred eighteen of them.",
                         VIDEO.spell_numbers("In 2026, 118 of them."))

    def test_digits_joined_to_letters_are_left_negative_control(self):
        for text in ("CORD2", "v4", "4th", "x_5", "CORD2 and v4"):
            with self.subTest(text=text):
                self.assertEqual(text, VIDEO.spell_numbers(text))

    def test_text_without_numbers_is_unchanged(self):
        self.assertEqual("Resolved: Ada Lovelace, Senzing graduate.",
                         VIDEO.spell_numbers("Resolved: Ada Lovelace, Senzing graduate."))

    def test_it_is_standard_library_only(self):
        if not hasattr(sys, "stdlib_module_names"):
            self.skipTest("sys.stdlib_module_names needs Python 3.10 or later")
        self.assertEqual(set(), modules_reached(VIDEO.spell_numbers)
                         - set(sys.stdlib_module_names))


class PiperIsFoundOrTheCaseIsNamed(unittest.TestCase):
    """INV-111: each case that keeps Piper out is named; with all three present it is used."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def find(self, finder, model):
        with mock.patch.object(VIDEO, "_find_spec", side_effect=finder):
            return VIDEO.find_piper_voice(model)

    def test_piper_not_installed_names_the_interpreter(self):
        engine, note = self.find(piper_missing, write_voice(self.root))
        self.assertIsNone(engine)
        self.assertIn("Piper (piper-tts) is not installed for %s" % sys.executable, note)

    def test_a_missing_model_names_its_path(self):
        model = write_voice(self.root, model=False, config=False)
        engine, note = self.find(piper_findable, model)
        self.assertIsNone(engine)
        self.assertIn("no Piper voice model at %s" % model, note)

    def test_a_missing_config_is_named(self):
        model = write_voice(self.root, config=False)
        engine, note = self.find(piper_findable, model)
        self.assertIsNone(engine)
        self.assertIn("has no config beside it", note)
        self.assertIn(str(VIDEO.piper_config_path(model)), note)

    def test_all_present_gives_the_piper_engine(self):
        model = write_voice(self.root)
        engine, note = self.find(piper_findable, model)
        self.assertIsNone(note)
        self.assertEqual("Piper (en_US-ljspeech-high)", engine.name)

    def test_it_runs_as_a_subprocess_of_this_interpreter(self):
        model = write_voice(self.root)
        engine, _note = self.find(piper_findable, model)
        argv, env = engine.command("in.txt", "out.wav")
        self.assertEqual([sys.executable, "-m", "piper",
                          "-m", str(model), "-c", str(model) + ".json",
                          "-i", "in.txt", "-f", "out.wav",
                          "--length-scale", "1.0", "--sentence-silence", "0.15"], argv)
        self.assertEqual({}, env)

    def test_the_config_sits_beside_the_model(self):
        self.assertEqual(Path("v/en_US-ljspeech-high.onnx.json"),
                         VIDEO.piper_config_path(Path("v/en_US-ljspeech-high.onnx")))


def imports_piper(source):
    """Every way `source` imports `piper`: import statements, import_module, __import__."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name.split(".")[0] == "piper"]
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "piper":
            found.append(node.module)
        elif isinstance(node, ast.Call):
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if name in ("import_module", "__import__") and any(
                    isinstance(a, ast.Constant) and str(a.value).split(".")[0] == "piper"
                    for a in node.args):
                found.append(name)
    return found


class PiperIsNeverImported(unittest.TestCase):

    def test_the_renderer_never_imports_piper(self):
        self.assertEqual([], imports_piper(SCRIPT.read_text(encoding="utf-8")))

    def test_the_check_catches_an_import_negative_control(self):
        for source in ("import piper", "from piper.voice import PiperVoice",
                       "importlib.import_module('piper')", "__import__('piper')"):
            with self.subTest(source=source):
                self.assertNotEqual([], imports_piper(source))

    def test_finding_it_imports_nothing(self):
        with tempfile.TemporaryDirectory() as root, \
                mock.patch.object(VIDEO, "_find_spec", side_effect=piper_findable):
            VIDEO.find_piper_voice(write_voice(root))
        self.assertNotIn("piper", sys.modules)


#: The voice families whose licenses (CC BY-NC-SA, Blizzard 2013) rule them out.
FORBIDDEN_VOICES = re.compile(r"(?:^|[-_])(?:ryan|hfc_\w+|lessac)(?:[-_]|$)")


class TheDefaultVoiceIsPublicDomain(unittest.TestCase):

    def test_the_default_is_ljspeech_high(self):
        self.assertEqual("en_US-ljspeech-high", VIDEO.DEFAULT_PIPER_VOICE)
        self.assertEqual("data/temp/piper-voices/en_US-ljspeech-high.onnx",
                         VIDEO.DEFAULT_VOICE_MODEL)

    def test_the_default_is_no_forbidden_family(self):
        for name in (VIDEO.DEFAULT_PIPER_VOICE, VIDEO.DEFAULT_VOICE_MODEL):
            with self.subTest(name=name):
                self.assertIsNone(FORBIDDEN_VOICES.search(Path(name).name))

    def test_the_check_catches_the_forbidden_families_negative_control(self):
        for name in ("en_US-ryan-high", "en_US-hfc_female-medium", "en_US-hfc_male-medium",
                     "en_US-lessac-high"):
            with self.subTest(name=name):
                self.assertIsNotNone(FORBIDDEN_VOICES.search(name))

    def test_the_license_record_sits_beside_the_constant(self):
        source = SCRIPT.read_text(encoding="utf-8")
        at = source.index('DEFAULT_PIPER_VOICE = "en_US-ljspeech-high"')
        record = squash_comment(source[source.rindex("\n\n", 0, at):at])
        for fact in ("en_US-ljspeech-high", "trained from scratch on the LJ Speech dataset",
                     "public domain", "model card was read 2026-10-01",
                     "piper-tts 1.8.0 is GPL-3.0-or-later",
                     "installed into the Bootcamper's venv and run as a separate process",
                     "the plugin does not ship it"):
            with self.subTest(fact=fact):
                self.assertIn(fact, record)

    def test_the_docstring_names_piper_and_the_flag(self):
        doc = VIDEO.__doc__
        fallbacks = doc[doc.index("Fallbacks, each stated"):doc.index("Exit codes\n")]
        self.assertIn("Piper", fallbacks)
        self.assertIn("--voice-model", fallbacks)
        usage = doc[doc.index("Usage::"):]
        self.assertIn("[--voice-model <model.onnx>]", usage)


def squash_comment(text):
    """A `#:` comment block as one line of prose, without its markers or backticks."""
    lines = [re.sub(r"^\s*#:?\s?", "", l) for l in text.strip().splitlines()]
    return re.sub(r"\s+", " ", " ".join(lines)).replace("``", "")


class TheVoiceStageIsAllOrNothing(unittest.TestCase):
    """`voice_with_piper`, with a fake subprocess: no Pillow, no ffmpeg, no Piper."""

    SCENES = [{"type": "title_card", "narration": "We loaded 10,000 records."},
              {"type": "counter", "narration": "At 3.5 a second, with CORD2."},
              {"type": "tag_line", "narration": "Resolved."}]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        with mock.patch.object(VIDEO, "_find_spec", side_effect=piper_findable):
            self.piper, _note = VIDEO.find_piper_voice(write_voice(self.root))
        self.work = self.root / "work"
        self.work.mkdir()

    def stage(self, fake):
        notes = []
        with mock.patch.object(VIDEO.subprocess, "run", side_effect=fake.run):
            voices = VIDEO.voice_with_piper(self.SCENES, self.piper, "ffmpeg", self.work,
                                            notes.append)
        return voices, notes

    def test_a_piper_that_succeeds_voices_every_scene_negative_control(self):
        fake = FakeProcesses()
        voices, notes = self.stage(fake)
        self.assertEqual(3, len(voices))
        for pcm in voices:
            self.assertEqual({FakeProcesses.PIPER}, markers(pcm))
        self.assertEqual([], notes)

    def test_piper_speaks_the_numbers_spelled_out(self):
        fake = FakeProcesses()
        self.stage(fake)
        self.assertEqual(["We loaded ten thousand records.",
                          "At three point five a second, with CORD2.", "Resolved."],
                         [text for _who, text in fake.calls])

    def test_a_failure_on_one_scene_gives_none_and_says_so(self):
        fake = FakeProcesses(piper_fails_on="three point five")
        voices, notes = self.stage(fake)
        self.assertIsNone(voices)
        self.assertEqual(1, len(notes))
        self.assertIn("scenes[1] (counter): Piper (en_US-ljspeech-high) could not voice", notes[0])
        self.assertIn("Piper is dropped for the whole video", notes[0])
        self.assertIn("never mixes two voices", notes[0])
        self.assertEqual(["piper", "piper"], fake.who(), "it stops at the first failure")

    def test_a_failure_leaves_no_partial_output(self):
        self.stage(FakeProcesses(piper_fails_on="Resolved"))
        self.assertEqual([], list(self.work.iterdir()))


@requires_pillow
class PiperComesFirstInTheRender(unittest.TestCase):
    """The whole render, with Piper findable through a stubbed `find_spec`, a fake subprocess
    for every engine and the decode, and the encode stubbed to record the plan."""

    def setUp(self):
        self.board = a_storyboard([
            {"type": "title_card", "duration": 1, "narration": "We loaded 10,000 records.",
             "module": "A"},
            {"type": "title_card", "duration": 1, "narration": "At 3.5 a second.",
             "module": "B"},
        ])
        self.project = Project(self.board)
        self.addCleanup(self.project.close)
        self.plan = None
        self.platform_lookups = 0

    def render(self, fake, *flags, finder=piper_findable, voice=True, config=True,
               platform=FAKE_PLATFORM):
        write_voice(self.project.root, model=voice, config=config)

        def encode(ctx, plan, ffmpeg, audio, output, log_path, music=None):
            self.plan = plan
            output.write_bytes(b"mp4")
            return True, ""

        def find_speech_engine():
            self.platform_lookups += 1
            return (platform, []) if platform else (None, ["espeak-ng (not on PATH)"])

        with mock.patch.object(VIDEO, "_find_spec", side_effect=finder), \
                mock.patch.object(VIDEO, "find_ffmpeg", return_value=("ffmpeg", [])), \
                mock.patch.object(VIDEO, "find_speech_engine", side_effect=find_speech_engine), \
                mock.patch.object(VIDEO.subprocess, "run", side_effect=fake.run), \
                mock.patch.object(VIDEO, "stream_frames", side_effect=encode):
            code, out, err = run_main("--storyboard", str(self.project.storyboard_path),
                                      "--output", str(self.project.output),
                                      "--project-root", str(self.project.root), *flags)
        self.assertEqual(0, code, err)
        return out.splitlines()[2:], err

    def scene_markers(self):
        return [markers(ps.pcm) for ps in self.plan]

    def test_piper_narrates_with_the_default_model_and_no_flag(self):
        fake = FakeProcesses()
        lines, err = self.render(fake)
        self.assertEqual(["Voice: Piper (en_US-ljspeech-high) (2 of 2 scenes narrated)",
                          "Music: yes"], lines)
        self.assertEqual([{FakeProcesses.PIPER}] * 2, self.scene_markers())
        self.assertEqual(["piper", "piper"], fake.who())
        self.assertEqual(0, self.platform_lookups, "Piper voiced it; no platform engine is "
                         "looked for")
        self.assertNotIn("Piper", err)

    def test_a_piper_failure_re_voices_the_whole_video(self):
        fake = FakeProcesses(piper_fails_on="three point five")
        lines, err = self.render(fake)
        self.assertEqual("Voice: fake-platform (2 of 2 scenes narrated)", lines[0])
        self.assertEqual([{FakeProcesses.PLATFORM}] * 2, self.scene_markers(),
                         "no scene keeps Piper audio")
        self.assertEqual(["piper", "piper", "platform", "platform"], fake.who(),
                         "Piper is tried first, then the platform engine voices every scene")
        self.assertIn("Piper is dropped for the whole video", err)

    def test_a_piper_failure_with_no_platform_engine_has_no_voice(self):
        fake = FakeProcesses(piper_fails_on="ten thousand")
        lines, err = self.render(fake, platform=None)
        self.assertEqual(["Voice: none (no speech engine found)", "Music: yes"], lines)
        self.assertTrue(all(not ps.voiced for ps in self.plan))
        self.assertIn("Piper is dropped for the whole video", err)

    def test_only_piper_hears_the_numbers_spelled_out(self):
        fake = FakeProcesses(piper_fails_on="three point five")
        self.render(fake)
        self.assertEqual([("piper", "We loaded ten thousand records."),
                          ("piper", "At three point five a second."),
                          ("platform", "We loaded 10,000 records."),
                          ("platform", "At 3.5 a second.")], fake.calls)
        self.assertEqual(["We loaded 10,000 records.", "At 3.5 a second."],
                         [ps.caption for ps in self.plan], "the captions keep the digits")

    def test_piper_missing_falls_back_and_names_the_interpreter(self):
        fake = FakeProcesses()
        lines, err = self.render(fake, finder=piper_missing)
        self.assertEqual("Voice: fake-platform (2 of 2 scenes narrated)", lines[0])
        self.assertIn("FALLBACK: Piper (piper-tts) is not installed for %s" % sys.executable,
                      err)
        self.assertEqual(["platform", "platform"], fake.who())

    def test_a_missing_model_falls_back_and_names_it(self):
        fake = FakeProcesses()
        lines, err = self.render(fake, voice=False, config=False)
        self.assertEqual("Voice: fake-platform (2 of 2 scenes narrated)", lines[0])
        self.assertIn("no Piper voice model at %s"
                      % (self.project.root / VIDEO.DEFAULT_VOICE_MODEL), err)
        self.assertEqual(["platform", "platform"], fake.who())

    def test_a_missing_config_falls_back_and_says_so(self):
        fake = FakeProcesses()
        lines, err = self.render(fake, config=False)
        self.assertEqual("Voice: fake-platform (2 of 2 scenes narrated)", lines[0])
        self.assertIn("has no config beside it", err)
        self.assertEqual(["platform", "platform"], fake.who())

    def test_an_explicit_voice_model_is_used(self):
        other = write_voice(self.project.root, rel="voices/en_GB-alba-medium.onnx")
        fake = FakeProcesses()
        lines, _err = self.render(fake, "--voice-model", str(other), voice=False, config=False)
        self.assertEqual("Voice: Piper (en_GB-alba-medium) (2 of 2 scenes narrated)", lines[0])

    def test_no_voice_skips_piper_too(self):
        fake = FakeProcesses()
        lines, err = self.render(fake, "--no-voice")
        self.assertEqual(["Voice: none (--no-voice)", "Music: yes"], lines)
        self.assertEqual([], fake.calls)
        self.assertNotIn("Piper", err)


if __name__ == "__main__":
    unittest.main()
