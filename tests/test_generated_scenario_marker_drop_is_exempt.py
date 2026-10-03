"""The generated-scenario marker's ROBOT FACE is the one exempt drop -- and only on its own line.

Module 1 Step 11 requires `> \\U0001f916 Bootcamp-generated business case` on its own line under
the title of `docs/business_problem.md`
(`module-01-business-problem/phase2-document-confirm.md:169-171`), and graduation Step 5b renders
that file as a keepsake PDF. The core fonts have no glyph for ROBOT FACE, so it was dropped and
the loss reported -- on **every Core run that accepts the Business Case Offer**, which is the
common path through Module 1.

⛔ **Neither branch of the warning's remedy applied.** It branches on "if it NAMES an entity"
(use the verified Latin-script name) and "if the dropped text IS the subject" (keep it and add an
ASCII description). The marker is neither: it is a machine-readable flag the plugin writes for
its own branches -- Module 4 Step 2, Module 6 Phase C step 15, Module 6 Phase D step 25a -- every one of
which reads it from the **Markdown**. Nothing reads it from the PDF. A guaranteed warning with no
correct response is the shape that teaches warnings are ignorable, which is what this suppresses.

**What is exempt is the PASSAGE, not the character.** The tally entry is skipped only when the
dropped ROBOT FACE was found in the marker line itself; the character is still dropped from the
page, and a ROBOT FACE anywhere else in the document still warns. The tests below pin both
directions, because a character-scoped exemption would silently swallow a real finding -- and the
subtle case is a document containing both: the marker must not consume the collector slot that a
genuine occurrence elsewhere needs.

⛔ **The marker string itself is unchanged and must stay so.** Four shipped files match it
verbatim; "fixing" this by dropping the emoji is a rename across all four with a silent-mismatch
failure mode. `TheMarkerStringIsUnchanged` asserts the sites still agree with the constant the
generator exempts, so the two cannot drift apart.

One string serves all three generators: `generate_document_pdf.py` aliases
`generate_discoveries_pdf.main`, which imports the folding machinery from `generate_recap_pdf.py`.

Also enforces **INV-266** (an exemption from a generator's dropped-character report is scoped to
an identified passage, never a character; leaves the character dropped from the page; is evaluated
before excerpt truncation; does not prevent the same character being reported elsewhere, including
when the exempt passage is rendered first; and is admissible only for a plugin-mandated
machine-readable marker read from the source rather than the artifact), which names this file.
`TheExemptSetIsTheReviewedOne` is the half that keeps the exemption from widening.

Source spec: `specs/generated-scenario-marker-is-dropped-from-the-keepsake-pdf.md`;
INV-266 from `specs/a-renderer-warning-exemption-must-be-scoped-to-a-passage.md`.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"

ROBOT_FACE = chr(0x1F916)
MARKER = "> %s Bootcamp-generated business case" % ROBOT_FACE

#: A non-Latin passage that must always warn. Built from code points so this file stays
#: ASCII-only, the discipline the warning itself follows.
CJK_SUBJECT = "Primary name: " + "".join(chr(c) for c in (0x5F35, 0x4E09))

#: Every shipped file that matches the marker verbatim. Derived by scanning, not listed
#: (INV-246) -- see `TheMarkerStringIsUnchanged`.
MARKER_GLOB = "**/*.md"


def load(name):
    """Load a generator by path, registering it in ``sys.modules`` before exec.

    Required because the generator defines dataclasses, and ``dataclasses._is_type`` resolves
    annotations through ``sys.modules[cls.__module__]`` -- ``None`` for an unregistered module,
    surfacing as an unrelated ``AttributeError`` inside unittest. Same reason and same fix as
    ``test_dropped_character_remedy_branches.load``.
    """
    import sys

    spec = importlib.util.spec_from_file_location("_markerdrop_" + name,
                                                  SCRIPTS / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TheExemptionIsScopedToTheMarkerLine(unittest.TestCase):
    def setUp(self):
        self.gen = load("generate_recap_pdf")
        self.gen.reset_dropped_characters()

    def tearDown(self):
        self.gen.reset_dropped_characters()

    def warn_for(self, *passages):
        self.gen.reset_dropped_characters()
        for passage in passages:
            self.gen._fold_to_latin1(passage)
        return self.gen.dropped_character_warning()

    def test_the_marker_line_alone_produces_no_warning(self):
        self.assertIsNone(
            self.warn_for(MARKER),
            "the generated-scenario marker still warns. It fires on every Core run that "
            "accepts the Business Case Offer, and neither remedy branch applies to it")

    def test_leading_whitespace_does_not_defeat_the_exemption(self):
        self.assertIsNone(
            self.warn_for("   " + MARKER),
            "the exemption is checked after normalizing whitespace; indentation must not "
            "reintroduce the warning")

    def test_the_marker_is_still_dropped_from_the_page(self):
        """Suppressing the tally must not start rendering a glyph the fonts lack.

        INV-143 forbids substituting `?`, and the exemption is about the WARNING only.
        """
        folded = self.gen._fold_to_latin1(MARKER)
        self.assertNotIn(
            ROBOT_FACE, folded,
            "ROBOT FACE survived the fold; the exemption changed what is rendered, not just "
            "what is reported")
        self.assertNotIn("?", folded, "the drop was encoded as '?', which INV-143 forbids")
        self.assertIn(
            "Bootcamp-generated business case", folded,
            "the marker's text was lost along with its emoji")

    def test_a_robot_face_anywhere_else_still_warns(self):
        self.assertIsNotNone(
            self.warn_for("The %s agent wrote this section" % ROBOT_FACE),
            "the exemption is keyed on the character rather than the passage, so any ROBOT "
            "FACE in the document is now silently dropped — a real finding swallowed")

    def test_the_marker_does_not_consume_the_slot_a_real_occurrence_needs(self):
        """The subtle failure: collector keyed by character, marker folded first.

        `_record_dropped_character` returns early when the character is already recorded. If
        the marker were recorded-then-exempted rather than never recorded, a genuine ROBOT
        FACE later in the same document would short-circuit and never be reported.
        """
        self.assertIsNotNone(
            self.warn_for(MARKER, "The %s agent wrote this" % ROBOT_FACE),
            "with the marker rendered first, a genuine ROBOT FACE elsewhere in the same "
            "document stopped warning")

    def test_a_line_merely_containing_the_marker_text_still_warns(self):
        self.assertIsNotNone(
            self.warn_for("See the note: " + MARKER),
            "the exemption matched a passage that only CONTAINS the marker; it must match "
            "the marker line itself, or arbitrary prose can opt out by quoting it")

    def test_other_unrenderable_characters_are_unaffected(self):
        self.assertIsNotNone(
            self.warn_for(CJK_SUBJECT),
            "a non-Latin passage stopped warning; the exemption widened beyond ROBOT FACE")

    def test_a_document_with_both_reports_only_the_real_drop(self):
        warning = self.warn_for(MARKER, CJK_SUBJECT)
        self.assertIsNotNone(warning, "the CJK passage stopped warning")
        self.assertNotIn(
            "ROBOT FACE", warning,
            "the marker's ROBOT FACE was named in a warning raised for a different passage, "
            "so the exemption did not apply when it was not the only drop")

    def test_the_warning_is_still_pure_ascii(self):
        warning = self.warn_for(CJK_SUBJECT)
        warning.encode("ascii")  # raises if the exemption work echoed a dropped character


class TheMarkerStringIsUnchanged(unittest.TestCase):
    """Criterion 2: the marker is untouched in every step that reads it.

    The constant the generator exempts and the string the modules write must be the same
    string. If either side is edited alone, the exemption stops applying (a returning warning,
    merely noisy) or the modules stop matching each other (silent, and much worse).
    """

    def setUp(self):
        self.gen = load("generate_recap_pdf")
        self.sites = sorted(
            p for p in SKILLS.glob(MARKER_GLOB)
            if MARKER in p.read_text(encoding="utf-8"))

    def test_the_generator_exempts_the_string_the_modules_write(self):
        self.assertEqual(
            MARKER, self.gen._EXPECTED_DROP_PASSAGE,
            "the generator's exempt passage and the marker this test pins have drifted apart")
        self.assertEqual(ROBOT_FACE, self.gen._EXPECTED_DROP_CHAR)

    def test_the_marker_still_appears_in_the_shipped_modules(self):
        self.assertGreaterEqual(
            len(self.sites), 4,
            "fewer than four shipped files match the marker verbatim (found %d: %s). The "
            "spec's whole caution is that several shipped files match this exact string, so a rename "
            "fails silently — either one was edited, or this scan no longer reads them"
            % (len(self.sites), [p.name for p in self.sites]))

    def test_module_one_still_requires_it_under_the_title(self):
        author = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
        self.assertIn(
            MARKER, author.read_text(encoding="utf-8"),
            "the module that WRITES the marker no longer contains it, so every reader "
            "branches on a string nothing produces")


class TheExemptSetIsTheReviewedOne(unittest.TestCase):
    """INV-266: an exemption is admissible only for a plugin-mandated marker, argued for.

    The exemption mechanism is a hole in the dropped-character report by construction, and that
    report is the only thing between a Bootcamper and silent content loss on the artifact they
    frame. So the count is pinned: a second exemption fails here until someone raises this
    number deliberately, which is the review step.

    ⛔ This is the same deliberate friction the `search_docs` prose exemption uses, and for the
    same reason — a self-declared exemption is indistinguishable from silencing a real finding.
    """

    #: How many passages the generator may exempt. Raising this is the review.
    REVIEWED_EXEMPT_PASSAGES = 1

    def setUp(self):
        self.gen = load("generate_recap_pdf")

    def test_exactly_one_passage_is_exempt(self):
        exempt = self.gen._EXPECTED_DROP_PASSAGE
        self.assertIsInstance(
            exempt, str,
            "`_EXPECTED_DROP_PASSAGE` is no longer a single string (%r). A collection means the "
            "exemption widened, and INV-266 makes each one admissible only for a "
            "plugin-mandated marker read from the source — raise "
            "REVIEWED_EXEMPT_PASSAGES here as part of arguing for the new one" % type(exempt))
        self.assertEqual(
            self.REVIEWED_EXEMPT_PASSAGES, 1,
            "the reviewed exempt count was changed without this assertion being updated")

    def test_a_second_plugin_marker_is_not_silently_exempt(self):
        """A plausible next candidate must NOT already be covered."""
        self.gen.reset_dropped_characters()
        try:
            other = "> %s Bootcamp-generated data scenario" % ROBOT_FACE
            self.gen._fold_to_latin1(other)
            self.assertIsNotNone(
                self.gen.dropped_character_warning(),
                "a marker line that is NOT the reviewed one was exempted. The exemption must "
                "match the identified passage, so a second plugin marker has to be argued for "
                "rather than inheriting the first one's waiver (INV-266)")
        finally:
            self.gen.reset_dropped_characters()

    def test_the_generator_cites_the_invariant_beside_its_constant(self):
        """INV-183: the rule must be lookup-able where the exemption is implemented."""
        source = (SCRIPTS / "generate_recap_pdf.py").read_text(encoding="utf-8")
        block = source[source.index("_EXPECTED_DROP_PASSAGE") - 2000:
                       source.index("_EXPECTED_DROP_PASSAGE") + 400]
        self.assertIn(
            "INV-266", block,
            "the exemption's implementation does not cite INV-266, so a later editor widening "
            "it cannot look up what constrains it")


class GraduationSaysTheDropNeedsNoAction(unittest.TestCase):
    """Criterion 1: the documentation fix, which the spec calls the one that matters."""

    def setUp(self):
        import re
        self.flat = re.sub(
            r"\s+", " ",
            (SKILLS / "graduation" / "SKILL.md").read_text(encoding="utf-8"))

    def test_step_5b_names_the_marker_and_says_no_action_is_needed(self):
        self.assertIn(
            MARKER, self.flat,
            "graduation does not name the marker, so the guide meeting the warning has "
            "nothing to match it against")
        self.assertRegex(
            self.flat, r"(?i)expected and harmless",
            "graduation does not say the drop is expected, so a guide following the "
            "warning literally still has no correct action")

    def test_step_5b_forbids_editing_the_marker_out_of_the_markdown(self):
        self.assertRegex(
            self.flat, r"(?i)do not edit the marker out of the Markdown",
            "graduation does not warn against the tempting wrong fix — removing the emoji — "
            "which the spec flags as a rename across several files with a silent failure mode")

    def test_step_5b_says_the_exemption_is_the_marker_line_only(self):
        self.assertRegex(
            self.flat, r"(?i)exemption is the marker line and nothing else",
            "graduation does not scope the exemption, so a reader could take any dropped "
            "character as expected")


if __name__ == "__main__":
    unittest.main()
