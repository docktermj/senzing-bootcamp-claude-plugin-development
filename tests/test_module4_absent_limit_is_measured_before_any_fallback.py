"""#593: no Module 4 sentence takes an absent `license_record_limit` straight to a fallback.

Module 4 → "6. Create sample files if needed" restated the canonical framing's branches, and
stated the absent one backwards: *"When it is absent or null, fall back to the built-in
evaluation capacity confirmed via the Senzing MCP server."* The framing it cited two
paragraphs earlier says the opposite: absent means **never measured**, so measure it by Step 8a
sub-step 7, persist it, re-enter the branches, and fall back **only if the measurement fails**
(INV-244). The copy also left out the provisional-marker re-measure (INV-295). It sat at the
step where the sampling decision is made, so a Bootcamper whose license has no cap could be
steered to a smaller dataset.

The fix routes Step 6 to *"License limit and dataset size (canonical framing)"* and restates
no branch there (INV-300), as Step 2's generation-sizing directive already did. The framing's
parenthesis about who writes the field now states the measured-only property and names no
writer set; `test_license_limit_is_written_only_from_a_measurement.py` keeps writer counts out.

⛔ **The guard is derived from the CLAIM, not from the one sentence that shipped (INV-282).**
Every sentence of every Module 4 markdown file that names the field's absence (`absent`,
`null` or `missing`) next to a fallback (`fall back`, `fallback`) must mention measuring
before the fallback. Calibrated 2026-10-14 against the pre-fix text: exactly one hit, the Step
6 sentence above, and none after the fix.

#810: Step 8b's other fallback, for an absent `database_type`, read "the engine recorded by
Module 2 in `config/bootcamp_progress.json`", which nothing writes. It now reads the scheme of
`SQL.CONNECTION` in `config/engine_config.json`, by Data processing Phase A's engine fallback.
That fallback is not a license one and this scan never matched it, so it is pinned below with a
negative control that restores the old fallback, by the checks
`test_module4_6_7_steps_act_on_real_files.py` owns.

⚠️ What this does NOT establish: that a live run measures before falling back. That is
turn-level behavior no offline suite can assert (INV-108).

Stdlib only; shipped markdown read as text.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from test_module4_6_7_steps_act_on_real_files import (
    MODULE_02, PHASE_A, engine_fallback_problems, progress_file_engine_reads)

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_04 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-04-data-collection"
MODULE_04_SKILL = MODULE_04 / "SKILL.md"

FRAMING_HEADING = "## License limit and dataset size (canonical framing)"
STEP_6_HEADING = "### 6. Create sample files if needed"
#: The pointer Step 6 must carry, by the framing's full heading text.
FRAMING_POINTER = '*"License limit and dataset size (canonical framing)"*'

ABSENCE = re.compile(r"\b(?:absent|null|missing)\b")
FALLBACK = re.compile(r"\bfall(?:s|ing)?\s+back\b|\bfallback\b")
MEASURE = re.compile(r"\bmeasur")
#: A sentence boundary in flattened text: end punctuation, or a list-item dash.
SENTENCE = re.compile(r"(?<=[.!?])\s+|\s-\s")


def flatten(text):
    """Whitespace-collapsed, `*`/backtick-stripped, lowercased (as the sibling license guard)."""
    return re.sub(r"[*`]", "", re.sub(r"\s+", " ", text)).lower()


def unmeasured_fallbacks(text):
    """Sentences pairing an absence with a fallback that no measurement precedes."""
    bad = []
    for sentence in SENTENCE.split(flatten(text)):
        fallback = FALLBACK.search(sentence)
        if fallback and ABSENCE.search(sentence) and not MEASURE.search(
                sentence[:fallback.start()]):
            bad.append(sentence[:240])
    return bad


def section(text, heading):
    """The body under `heading`, up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    start = text.index(heading) + len(heading)
    stop = re.compile(r"^#{1,%d} " % level, re.M).search(text, start)
    return text[start:stop.start() if stop else len(text)]


def module_04_files():
    """Every Module 4 markdown file — derived, not listed (INV-246)."""
    return sorted(MODULE_04.rglob("*.md"))


class Module4MeasuresBeforeAnyFallback(unittest.TestCase):
    def test_the_scan_reaches_module_4(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        files = module_04_files()
        self.assertIn(MODULE_04_SKILL, files)
        text = MODULE_04_SKILL.read_text(encoding="utf-8")
        sentences = SENTENCE.split(flatten(text))
        self.assertTrue(any(ABSENCE.search(s) for s in sentences),
                        "no Module 4 sentence names an absence; the scan broke")
        self.assertTrue(any(FALLBACK.search(s) for s in sentences),
                        "no Module 4 sentence names a fallback; the framing's "
                        "measurement-fails fallback is gone or the matcher broke")

    def test_no_sentence_falls_back_on_an_absence_without_measuring_first(self):
        bad = []
        for path in module_04_files():
            for sentence in unmeasured_fallbacks(path.read_text(encoding="utf-8")):
                bad.append(f"{path.relative_to(REPO_ROOT)}: ...{sentence}...")
        self.assertEqual(
            [], bad,
            "a Module 4 sentence takes an absent value straight to a fallback. An absent "
            "`license_record_limit` means never measured (INV-244): measure it first, and fall "
            "back only if the measurement fails. Route to the canonical framing instead of "
            "restating its branches (INV-300):\n  " + "\n  ".join(bad))

    def test_step_6_routes_to_the_framing_and_restates_no_branch(self):
        text = MODULE_04_SKILL.read_text(encoding="utf-8")
        step_6 = section(text, STEP_6_HEADING)
        self.assertIn(FRAMING_POINTER, step_6,
                      "Step 6 no longer points to the canonical framing by its heading")
        self.assertIn(FRAMING_HEADING, text,
                      "the framing Step 6 points to has been renamed or removed")
        flat = flatten(step_6)
        for restated in ("when it is absent", "when it is 0", "absent or null",
                         "built-in evaluation capacity"):
            with self.subTest(restated=restated):
                self.assertNotIn(restated, flat,
                                 "Step 6 restates a branch of the canonical framing again; "
                                 "a copy here is what stated the absent branch backwards")

    def test_the_framing_states_the_property_and_names_no_writer(self):
        framing = flatten(section(MODULE_04_SKILL.read_text(encoding="utf-8"), FRAMING_HEADING))
        self.assertIn("every step that writes it writes only a measured value", framing,
                      "the framing's lead no longer states the measured-only property")
        self.assertNotIn("step 8a writes it", framing,
                         "the framing names Step 8a as the writer again; other steps write "
                         "the field too, so name the property, not a writer set")


class TheMatcherIsNotVacuous(unittest.TestCase):
    """⛔ INV-265 — the shipped defect and its siblings fail; the framing's own shape passes."""

    def test_the_shipped_defect_and_its_variants_are_caught(self):
        for planted in (
            "When it is absent or null, fall back to the built-in evaluation capacity "
            "confirmed via the Senzing MCP server.",
            "If `license_record_limit` is missing, fall back to the built-in license.",
            "- **Absent or null:** use the built-in evaluation capacity as the fallback.",
            "When the value is null, the guide falls back to 500 records.",
        ):
            with self.subTest(planted=planted[:46]):
                self.assertTrue(unmeasured_fallbacks(planted),
                                "the matcher misses an unmeasured fallback on an absence")

    def test_measuring_first_and_unrelated_fallbacks_pass(self):
        for ok in (
            "When it is absent, measure it by Step 8a sub-step 7, and only if the measurement "
            "fails fall back to the built-in evaluation license.",
            "- **Only if the measurement fails** (no engine yet, SDK error) fall back to the "
            "**built-in evaluation license** the bootcamper already has by default.",
            "Note it internally, and fall back to the scheme of `SQL.CONNECTION` in "
            "`config/engine_config.json`.",
            "That block says what to do when it is missing.",
        ):
            with self.subTest(ok=ok[:46]):
                self.assertEqual([], unmeasured_fallbacks(ok),
                                 "the matcher flags a sentence that measures first or names "
                                 "no absence, which would push an editor to delete correct text")


class TheEngineFallbackReadsTheConnectionScheme(unittest.TestCase):
    """#810: Step 8b's `database_type` fallback reads a value Module 2 actually writes."""

    NEW = ("fall back to the scheme of `SQL.CONNECTION` in `config/engine_config.json` before "
           "giving up on\n     the check,")
    OLD = ("fall back to the engine recorded by Module 2 in `config/bootcamp_progress.json` "
           "before giving\n     up on the check,")

    def setUp(self):
        self.module_02 = MODULE_02.read_text(encoding="utf-8")
        self.module_04 = MODULE_04_SKILL.read_text(encoding="utf-8")
        self.phase_a = PHASE_A.read_text(encoding="utf-8")

    def test_step_8b_falls_back_to_the_connection_scheme(self):
        self.assertIn(self.NEW, self.module_04)
        self.assertEqual(
            [], engine_fallback_problems(self.module_02, self.module_04, self.phase_a))
        self.assertEqual([], progress_file_engine_reads([("module-04", self.module_04)]))

    def test_restoring_the_old_fallback_fails(self):
        broken = self.module_04.replace(self.NEW, self.OLD, 1)
        self.assertNotEqual(broken, self.module_04, "control did not apply")
        problems = engine_fallback_problems(self.module_02, broken, self.phase_a)
        self.assertTrue(any("progress file" in p for p in problems), problems)
        self.assertTrue(progress_file_engine_reads([("module-04", broken)]),
                        "the old fallback reads an engine nothing writes, and must fail")


if __name__ == "__main__":
    unittest.main()
