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
* **End to end**, an mp4 is rendered and probed: H.264, yuv420p, 1920x1080, 30 fps, and AAC
  when a voice spoke. Skipped with a reason when Pillow or ffmpeg is absent.

⚠️ Pillow and imageio-ffmpeg are optional dependencies of the *renderer under test*, declared in
`requirements-dev.txt` (INV-306). The tests themselves are standard library only (INV-108):
availability is probed with `importlib.util.find_spec`, and Pillow is reached only through the
script. The skip notices name the cause and the remedy and state no count.

Source issue: #299.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import copy
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
        {"type": "image", "duration": 2, "narration": "Here is the entity graph.",
         "image": "docs/video/broll/graph.png", "heading": "Entity graph"},
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
            self.write_screenshot("docs/video/broll/graph.png")

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
        self.assertIsNone(self.problem("docs/video/broll/graph.png"))

    def test_a_missing_relative_image_is_not_a_validation_error(self):
        """It becomes a title card at render time; see FallbacksAreStated."""
        self.assertIsNone(self.problem("docs/video/broll/not-there.png"))

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
                mock.patch.object(VIDEO, "missing_encoders", return_value=[]):
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
                mock.patch.object(VIDEO, "missing_encoders", side_effect=lacking):
            path, notes = VIDEO.find_ffmpeg()
        self.assertEqual("/opt/ff", path)
        self.assertIn("lacks the libx264 encoder", notes[0])

    def test_path_ffmpeg_is_preferred_and_silent(self):
        with mock.patch.object(VIDEO.shutil, "which", return_value="/usr/bin/ffmpeg"), \
                mock.patch.object(VIDEO, "missing_encoders", return_value=[]):
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
        self.assertIn("FALLBACK: scenes[1] (image): image docs/video/broll/graph.png not found; "
                      "drawing a title card instead.", err.getvalue())

    @requires_pillow
    def test_an_unreadable_image_becomes_a_title_card(self):
        board = a_storyboard()
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stderr(err):
            path = Path(root) / "docs" / "video" / "broll" / "graph.png"
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
                self.assertEqual(VIDEO.AUDIO_RATE, track.getframerate())
                self.assertEqual(sum(p.frames for p in plan) * VIDEO.SAMPLES_PER_FRAME,
                                 track.getnframes())
                samples = struct.unpack("<%dh" % track.getnframes(),
                                        track.readframes(track.getnframes()))
        lead = int(VIDEO.NARRATION_LEAD * VIDEO.AUDIO_RATE)
        self.assertEqual(0, max(samples[:lead]), "the narration starts after the lead-in")
        self.assertEqual(1, samples[lead])
        second = plan[0].frames * VIDEO.SAMPLES_PER_FRAME
        self.assertEqual(1, samples[second + lead], "scene 2's narration starts at scene 2")


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


def probe(ffmpeg, path):
    return subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True,
                          text=True, timeout=120).stderr


@requires_pillow_and_ffmpeg
class TheVideoIsRendered(unittest.TestCase):
    def setUp(self):
        self.ffmpeg, _notes = VIDEO.find_ffmpeg()
        scenes = [
            {"type": "title_card", "duration": 1, "narration": "Hi.", "module": "Business Problem"},
            {"type": "image", "duration": 1, "narration": "Graph.",
             "image": "docs/video/broll/graph.png", "heading": "Entity graph"},
            {"type": "image", "duration": 1, "narration": "Gone.",
             "image": "docs/video/broll/missing.png"},
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
            self.assertRegex(info, r"Audio: aac")
            self.assertIn("Audio track: yes", result.stdout)
        else:
            self.assertNotIn("Audio:", info)
            self.assertIn("Audio track: no (captions carry the narration)", result.stdout)
        self.assertIn("FALLBACK: scenes[2] (image): image docs/video/broll/missing.png not "
                      "found; drawing a title card instead.", result.stderr)
        self.assertIn("no recap at docs/bootcamp_recap.md", result.stderr)

    def test_captions_only(self):
        result = self.project.run("--no-voice")
        self.assertPlayableMp4(result, audio=False)
        self.assertIn("--no-voice", result.stderr)

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
        self.assertIn("espeak-ng voice-over, 5 of 5 scenes narrated", result.stdout)
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


if __name__ == "__main__":
    unittest.main()
