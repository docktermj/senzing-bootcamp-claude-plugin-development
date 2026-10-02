"""The dry-run scaffold's fixture banner describes the mode it actually built.

`scaffold_project.py`'s banner exists to tell the operator what the project exercises, and
`dry-run/SKILL.md` introduces it as "The scaffold prints which fixture exercises which
invariant. Each one is there because a naive fixture hid a defect." It was a **static** list
printed in all three modes, while `build()` branches: `--fresh`/`--seeded` write two config
files, the default mid-bootcamp path writes six.

Run with `--fresh` on 2026-08-12 the banner claimed 8 fixtures over a 4-file project, and one
claim was not merely stale but **inverted** — it described `bootcamp_preferences.yaml` as
carrying "saved verbosity + language to test honor-don't-ask (INV-133)" when in `--fresh` that
file is deliberately empty, which is the entire point of the mode. `phase3-conversational.md`
is explicit that a walk where everything was asked exercises the honor path "only in its inert
direction", which is why a separate `--seeded` walk exists at all. A banner claiming otherwise
invites exactly the false conclusion that doc was written to prevent.

That matters more than tooling polish usually would: `dry-run/SKILL.md` requires a report to
"State the coverage limits explicitly" and calls an unstated limit "the difference between a
report and a false clean bill of health". The banner is the operator's primary input for
writing that section, and in two of three modes it inflated it.

The fix is structural rather than a corrected list. Each `FIXTURE_MAP` row carries the modes
it applies to **and** the project-relative path it describes, so the tests below can build a
real project per mode and compare the banner against the filesystem in both directions:
nothing is described that was not written, and nothing is written that is not described. A
future fixture added to `build()` without a banner row fails here, which a corrected static
list would not have prevented.

Enforces **INV-175**'s 2026-10-02 note (#328) for the dry-run fixtures: the modes that start before
Step 8 do not pre-create `config/engine_config.json`. It does **not** establish anything about the
env script itself, which `tests/test_env_script_shell_portability.py` executes.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import io
import contextlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD = REPO_ROOT / ".claude" / "skills" / "dry-run" / "scaffold_project.py"
GENERATOR = (
    REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_recap_pdf.py"
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


scaffold = load(SCAFFOLD, "scaffold_project_banner")

#: (mode, fresh, seeded) — the three ways build() can be invoked.
INVOCATIONS = (("mid", False, False), ("fresh", True, False), ("seeded", False, True))


def built_files(root):
    """Project-relative POSIX paths of every file build() wrote."""
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def build_in_mode(fresh, seeded):
    """Build into a temp dir and return (root_paths, banner_text). Caller owns nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "project"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scaffold.build(root, fresh, seeded)
        return built_files(root), buf.getvalue()


class TheBannerMatchesTheFilesystem(unittest.TestCase):
    """Both directions, in every mode — this is what makes the banner drift-proof."""

    def test_every_described_fixture_exists(self):
        for mode, fresh, seeded in INVOCATIONS:
            with self.subTest(mode=mode):
                files, _ = build_in_mode(fresh, seeded)
                described = {row[1] for row in scaffold.fixtures_for(mode) if row[1]}
                missing = sorted(described - files)
                self.assertEqual(
                    [], missing,
                    f"--{mode} banner describes fixtures the mode does not create: {missing}",
                )

    def test_every_written_file_is_described(self):
        for mode, fresh, seeded in INVOCATIONS:
            with self.subTest(mode=mode):
                files, _ = build_in_mode(fresh, seeded)
                described = {row[1] for row in scaffold.fixtures_for(mode) if row[1]}
                undescribed = sorted(files - described)
                self.assertEqual(
                    [], undescribed,
                    f"--{mode} writes files the banner never mentions, so the operator "
                    f"cannot know they are exercised: {undescribed}",
                )

    def test_the_printed_banner_names_the_mode(self):
        for mode, fresh, seeded in INVOCATIONS:
            with self.subTest(mode=mode):
                _, out = build_in_mode(fresh, seeded)
                self.assertIn(mode, out)


class FreshNoLongerOverClaims(unittest.TestCase):
    """The specific false lines from the 2026-08-12 run, pinned as absent."""

    MID_ONLY = (
        "docs/bootcamp_recap.md",
        "docs/progress/recap_checkpoint.md",
        "docs/loading_strategy.md",
        "src/system_verification/verification_data.jsonl",
    )

    def setUp(self):
        _, self.out = build_in_mode(fresh=True, seeded=False)
        self.described = [row[0] for row in scaffold.fixtures_for("fresh")]

    def test_no_mid_only_fixture_is_described(self):
        for path in self.MID_ONLY:
            with self.subTest(path=path):
                self.assertNotIn(path, self.described)

    def test_no_docker_containers_line(self):
        """INV-101's warn-and-continue path needs a progress file that names a container."""
        self.assertNotIn("  └ docker_containers", self.described)
        self.assertNotIn("INV-101", self.out)

    def test_the_preferences_line_is_not_inverted(self):
        """The inversion was the worst of it: empty described as carrying saved values."""
        prefs = [
            row for row in scaffold.fixtures_for("fresh")
            if row[1] == "config/bootcamp_preferences.yaml"
        ]
        self.assertEqual(1, len(prefs), "exactly one preferences row must apply to fresh")
        why = prefs[0][3]
        self.assertIn("EMPTY", why)
        self.assertIn("INERT", why)
        self.assertNotIn("saved verbosity", why)

    def test_the_absent_fixtures_are_named_as_absent(self):
        """Stating the limit is the banner's whole job for a dry-run report."""
        self.assertIn("NOT in this mode", self.out)
        for path in self.MID_ONLY:
            with self.subTest(path=path):
                self.assertIn(path, self.out)


class SeededDescribesItsOwnCoverage(unittest.TestCase):
    def setUp(self):
        _, self.out = build_in_mode(fresh=False, seeded=True)
        self.rows = scaffold.fixtures_for("seeded")

    def test_the_preferences_line_is_the_seeded_one(self):
        prefs = [r for r in self.rows if r[1] == "config/bootcamp_preferences.yaml"]
        self.assertEqual(1, len(prefs))
        self.assertIn("honor-don't-ask (INV-133)", prefs[0][3])

    def test_the_four_mid_only_fixtures_are_omitted(self):
        described = {r[1] for r in self.rows}
        for path in FreshNoLongerOverClaims.MID_ONLY:
            with self.subTest(path=path):
                self.assertNotIn(path, described)


class MidBootcampOutputIsUnchanged(unittest.TestCase):
    """Criterion 4: the mode the original banner already described correctly."""

    def test_all_nine_original_rows_still_apply(self):
        described = [row[0] for row in scaffold.fixtures_for("mid")]
        for display in (
            "config/bootcamp_progress.json",
            "  └ docker_containers",
            "config/bootcamp_preferences.yaml",
            "docs/bootcamp_recap.md",
            "docs/progress/recap_checkpoint.md",
            "docs/feedback/...FEEDBACK.md",
            "docs/loading_strategy.md",
            "src/system_verification/verification_data.jsonl",
            "config/engine_config.json",
        ):
            with self.subTest(display=display):
                self.assertIn(display, described)

    def test_mid_omits_nothing(self):
        """Nothing is absent in mid, so the limits block must not appear."""
        _, out = build_in_mode(fresh=False, seeded=False)
        self.assertNotIn("NOT in this mode", out)


class ExplainNamesItsMode(unittest.TestCase):
    """Criterion 6: --explain writes nothing, so it must say what it is describing."""

    def test_explain_defaults_to_mid_and_says_so(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scaffold.explain(scaffold.mode_name(False, False))
        self.assertIn("mid", buf.getvalue())

    def test_explain_follows_the_mode_flags(self):
        for mode, fresh, seeded in INVOCATIONS:
            with self.subTest(mode=mode):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    scaffold.explain(scaffold.mode_name(fresh, seeded))
                self.assertIn(mode, buf.getvalue())

    def test_mode_name_resolves_seeded_before_fresh(self):
        """build() treats --seeded as winning; the banner must agree or it mislabels."""
        self.assertEqual("seeded", scaffold.mode_name(True, True))
        self.assertEqual("fresh", scaffold.mode_name(True, False))
        self.assertEqual("mid", scaffold.mode_name(False, False))


class TheScaffoldStaysStdlibOnly(unittest.TestCase):
    """INV-108: the suite and this tooling import nothing from plugins/."""

    def test_no_plugin_import(self):
        source = SCAFFOLD.read_text(encoding="utf-8")
        self.assertNotIn("from plugins", source)
        self.assertNotIn("import plugins", source)

    def test_paths_stay_pathlib_based(self):
        """Cross-platform: no os.path string joining crept in with this change."""
        source = SCAFFOLD.read_text(encoding="utf-8")
        self.assertNotIn("os.path.join", source)


if __name__ == "__main__":
    unittest.main()


class TheCheckpointFixtureSaysWhatFoldingCannotReach(unittest.TestCase):
    """The banner must say truthfully what this fixture does and does not reach.

    It told a phase-2 run the long '— in progress' heading reaches the cover's 46-character
    clip if you "FOLD FIRST, then render". Measured on 2026-09-02: it does not. Folding puts
    that heading inside the RECAP-CHECKPOINT fence, which `generate_recap_pdf.py` strips
    before module parsing, so the section is absent from cover, contents and body — and
    `audit_recap` correctly warns a module was folded but never finalized.

    The 2026-09-02 correction then prescribed "fold 3x, THEN remove the two fence markers,
    then render". Carried out on 2026-09-24, **that does not reach the clip either**: the PDF
    rendered cleanly and its chips read `Data collection` and `Data Quality, Mapping, and
    Transformation`, no ellipsis. `parse_recap` strips the `— in progress` suffix, so the chip
    is the bare 41-character title, and no real module title is long enough to clip. The
    fixture cannot reach the path by any documented sequence; the chip clip is covered by
    unit test in `tests/test_recap_pdf_font_safety.py`.

    ⚠️ **The fixture is right; the recipe was wrong, twice.** An unfinalized block is exactly
    what the INV-059 idempotency check needs, and that check passes. So this guards the
    instruction, not the fixture — and specifically guards that the REASON survives, because
    a later editor who reads the banner's caveat as noise is one edit from restoring a
    recipe that silently tests nothing. The numbers the banner states are checked against
    the shipped parser and the generator's own chip width, so they cannot drift quietly.

    Stdlib only; nothing under ``plugins/`` is imported (INV-108) — the generator is loaded
    by path.
    """

    def banner(self):
        return re.sub(r"\s+", " ", SCAFFOLD.read_text(encoding="utf-8"))

    def test_the_banner_does_not_claim_folding_alone_reaches_the_clip(self):
        b = self.banner()
        self.assertNotRegex(
            b, r"46-char clip, so FOLD FIRST",
            "the banner tells a phase-2 run that folding is enough to exercise the cover "
            "clip. It is not: the folded heading sits inside a fence the renderer strips, "
            "so the run sees one 15-character chip and believes it tested the clip.",
        )

    def checkpoint_row(self):
        """The recap_checkpoint.md banner text exactly as the mid-bootcamp build prints it."""
        rows = [
            row[3] for row in scaffold.fixtures_for("mid")
            if row[1] == "docs/progress/recap_checkpoint.md"
        ]
        self.assertEqual(1, len(rows), "exactly one recap_checkpoint.md row must apply")
        return re.sub(r"\s+", " ", rows[0])

    def test_the_banner_names_the_unit_test_that_covers_the_clip(self):
        """Was `..._names_finalizing_as_the_step_that_reaches_it`; repointed 2026-09-24.

        Nothing in the fixture reaches the clip, so the banner must name where the path IS
        covered, and why the fixture cannot reach it.
        """
        row = self.checkpoint_row()
        self.assertIn(
            "test_recap_pdf_font_safety", row,
            "saying the fixture does not reach the clip, without saying what does cover it, "
            "leaves the operator knowing the path is untested here and not where it is.",
        )
        self.assertRegex(
            row, r"(?i)strips the '— in progress' suffix",
            "the banner must give the reason the unfenced heading still cannot clip: the "
            "parser strips the '— in progress' suffix, leaving the bare title.",
        )

    def test_the_banner_gives_no_recipe_for_the_clip(self):
        """The fold-then-remove-markers recipe was measured not to clip on 2026-09-24."""
        row = self.checkpoint_row()
        for recipe in (r"(?i)to exercise the clip", r"(?i)remove the two fence markers"):
            with self.subTest(recipe=recipe):
                self.assertNotRegex(row, recipe)
        self.assertRegex(row, r"(?i)does NOT reach the PDF cover's \d+-char chip clip")

    def test_the_banner_numbers_are_the_measured_ones(self):
        """The widths the banner states are derived here from the shipped sources."""
        generator = load(GENERATOR, "_banner_recap_gen")
        source = GENERATOR.read_text(encoding="utf-8")
        chip = re.findall(
            r'_clip\(\s*_safe\(\s*f"\{mod\.number\}\. \{mod\.title\}"[^)]*\)\s*,\s*(\d+)',
            source,
        )
        self.assertEqual(1, len(chip), "the cover-chip _clip call site no longer parses")
        checkpoint = scaffold.CHECKPOINT
        for marker in (generator.RECAP_CHECKPOINT_START, generator.RECAP_CHECKPOINT_END):
            checkpoint = checkpoint.replace(marker, "")
        titles = [m.title for m in generator.parse_recap(checkpoint).modules]
        self.assertEqual(1, len(titles), f"the checkpoint parsed to {titles}")

        row = self.checkpoint_row()
        stated_width = re.search(r"(\d+)-char chip clip", row)
        stated_title = re.search(r"bare (\d+)-character title", row)
        self.assertIsNotNone(stated_width, "the banner no longer states the chip width")
        self.assertIsNotNone(stated_title, "the banner no longer states the title length")
        self.assertEqual(int(chip[0]), int(stated_width.group(1)))
        self.assertEqual(len(titles[0]), int(stated_title.group(1)))

    def test_the_banner_keeps_the_reason_folding_cannot_reach_it(self):
        """⚠️ The reason is what stops the caveat being 'simplified' back into a recipe."""
        self.assertRegex(
            self.banner(),
            r"(?i)strips before module parsing|RECAP-CHECKPOINT fence, which"
            r"|strips the '— in progress' suffix",
            "the banner must say WHY the fixture cannot reach the clip — the fence is "
            "stripped before module parsing, and unfenced the parser strips the "
            "'— in progress' suffix. Without it the caveat reads as ceremony.",
        )

    def test_the_idempotency_fixture_is_still_described(self):
        """Fixing the recipe must not cost the check the fixture actually exists for."""
        self.assertRegex(
            self.banner(), r"(?i)fold idempotency, run it 3x \(INV-059\)",
            "the unfinalized block's primary purpose is the INV-059 idempotency check. If "
            "the clip recipe crowded it out, the more valuable half was traded away.",
        )


class EarlyModesDoNotPreCreateTheStep8Config(unittest.TestCase):
    """#328: `--fresh` and `--seeded` start before Module 2 Step 8, which writes
    `config/engine_config.json`. Pre-creating it there hid the env script refusing to load
    until Step 8. The mid-bootcamp mode keeps it, so phase 2 still reaches both config gates.
    """

    CONFIG = "config/engine_config.json"
    INCOMPLETE = "config/engine_config_incomplete.json"

    def test_fresh_and_seeded_do_not_write_the_engine_config(self):
        for mode, fresh, seeded in INVOCATIONS[1:]:
            with self.subTest(mode=mode):
                files, out = build_in_mode(fresh, seeded)
                self.assertNotIn(self.CONFIG, files)
                self.assertNotIn(self.CONFIG, {r[1] for r in scaffold.fixtures_for(mode)})
                self.assertIn("NOT in this mode", out)
                limits = out[out.index("NOT in this mode"):]
                self.assertIn(self.CONFIG, limits, "the banner must name it as absent")

    def test_mid_keeps_both_config_gates(self):
        files, _ = build_in_mode(fresh=False, seeded=False)
        self.assertIn(self.CONFIG, files)
        self.assertIn(self.INCOMPLETE, files)

    def test_the_incomplete_fixture_stays_in_every_mode(self):
        """Out of scope for #328: the pre-flight fixture is not moved."""
        for mode, fresh, seeded in INVOCATIONS:
            with self.subTest(mode=mode):
                files, _ = build_in_mode(fresh, seeded)
                self.assertIn(self.INCOMPLETE, files)
