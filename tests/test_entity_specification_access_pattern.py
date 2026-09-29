"""The entity specification is consulted by targeted lookup, never read end to end.

Module 5 Phase 1 Step 3 retrieves the Senzing Generic Entity Specification and makes it the
reference for the phase's comparison steps. `mapping_workflow`, which owns the mapping phase
this module hands off to, says the opposite about reading it — verbatim, server 1.32.9,
2026-08-14, in both its step-2 and step-3 responses:

    You do **NOT** need to open the full 73KB entity specification to plan or map; it is
    available only as an optional deep-dive...

    OPTIONAL DEEP-DIVE (do NOT read in full - reference specific sections only if needed)
    ... **Do NOT attempt to read it end-to-end - that is unnecessary and will overflow
    limited context windows.**

Both instructions are satisfiable at once, by consulting the file *selectively*. The step has
to say so: read literally, "the authoritative reference ... in this step and every subsequent
step" invites the end-to-end read the tool warns will overflow the context window. That is not
a theoretical cost here — context exhaustion is the documented reason no phase-3 dry run has
reached the later modules, and a bootcamper is in one long conversation too.

These tests pin the access pattern, the handoff to the workflow's distilled inline reference,
and the scoping of the authority claim to Phase 1. The sweep is the load-bearing one: no
instruction anywhere in the module may direct an end-to-end read.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping")
PHASE1 = MODULE / "phase1-quality-assessment.md"

#: The scoping this spec falsified. "every subsequent step" made the large file the standing
#: reference for the mapping phase too, where the workflow ships a distilled one instead.
OVERBROAD_SCOPE = re.compile(r"(?i)in this step and every subsequent step")

#: A reading notion that would mean the whole file.
IN_FULL = r"(?:in full|end[\s-]?to[\s-]?end|front to back|full \d+\s*KB|entire specification)"
#: Words that make such a sentence a prohibition rather than an instruction.
NEGATED = re.compile(r"(?i)\b(?:do not|don't|never|not|rather than|no need|instead of)\b")


def flat(path):
    """Whitespace-collapsed text with blockquote markers stripped."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


def module_files():
    return sorted(p for p in MODULE.rglob("*.md") if p.is_file())


def sentences(text):
    return re.split(r"(?<=[.!?])\s+", text)


class NoInstructionDirectsAnEndToEndRead(unittest.TestCase):
    """Criterion 5 — the sweep, over every instruction file in the module."""

    def test_the_module_has_files_to_sweep(self):
        self.assertTrue(module_files(), "module-05 has no markdown to sweep")

    def test_no_sentence_directs_reading_the_specification_in_full(self):
        # Every sentence pairing the specification with a read-it-all notion must be a
        # prohibition. This is what fails if the old wording is restored, and it does not
        # depend on the exact phrasing of the fix.
        pattern = re.compile(r"(?i)specification[^.]{0,120}%s|%s[^.]{0,120}specification"
                             % (IN_FULL, IN_FULL))
        for path in module_files():
            for sentence in sentences(flat(path)):
                if not pattern.search(sentence):
                    continue
                with self.subTest(file=str(path.relative_to(REPO_ROOT)),
                                  sentence=sentence[:100]):
                    self.assertRegex(
                        sentence, NEGATED,
                        "this sentence pairs the entity specification with reading it in "
                        "full and carries no prohibition, so it reads as an instruction to "
                        "do it",
                    )

    def test_the_overbroad_scope_wording_is_gone(self):
        for path in module_files():
            with self.subTest(file=str(path.relative_to(REPO_ROOT))):
                self.assertNotRegex(flat(path), OVERBROAD_SCOPE)


class Step3StatesTheAccessPattern(unittest.TestCase):
    """Criteria 1-2 — targeted lookup, with the size, the reason, and the handoff."""

    def test_it_prescribes_targeted_lookup(self):
        self.assertRegex(flat(PHASE1), r"(?i)targeted lookup, never end to end")

    def test_it_points_to_the_size_rather_than_pinning_one(self):
        """Rescoped by #225 from `test_it_gives_the_size`.

        That test asserted a KB figure for the file, a pinned MCP-content claim INV-219 forbids a
        test to hold: by server 1.37.14 the file had grown past it, and the test kept the stale
        figure in shipped prose. The size still earns its place as the reason for a targeted
        lookup, so this asserts the step says the file is large and names where its size is
        read, the response's `size_bytes` or `total_chars`, and that no KB figure is written.
        """
        text = flat(PHASE1)
        self.assertRegex(
            text, r"(?i)the file is large: its size is the response's `size_bytes` \(or `total_chars`")
        self.assertNotRegex(text, r"(?i)\b\d+\s*KB\b")

    def test_it_gives_the_reason_from_the_tool_that_owns_mapping(self):
        text = flat(PHASE1)
        self.assertIn("overflow limited context windows", text)
        self.assertIn("mapping_workflow", text)

    def test_it_names_the_distilled_inline_reference_as_the_mapping_reference(self):
        text = flat(PHASE1)
        self.assertRegex(text, r"(?i)distilled inline mapping\s+reference")
        self.assertRegex(text, r"(?i)optional deep-dive")

    def test_the_authority_claim_is_scoped_to_this_phase(self):
        self.assertRegex(flat(PHASE1), r"(?i)scope of its authority is this phase")


class TheCanonicalCopyRuleSurvives(unittest.TestCase):
    """Criterion 4 — one copy the guide makes, and the tool's own copy acknowledged."""

    def test_the_single_canonical_copy_rule_is_still_stated(self):
        text = flat(PHASE1)
        self.assertIn("docs/reference/senzing_entity_specification.md", text)
        self.assertRegex(text, r"(?i)do not create duplicate copies elsewhere")

    def test_the_workflows_own_copy_is_acknowledged(self):
        text = flat(PHASE1)
        self.assertRegex(text, r"(?i)two copies on disk is expected")
        # The path it actually lands in, so the reader can tell the two apart.
        self.assertRegex(text, r"(?i)workspace_dir")
        self.assertRegex(text, r"data/mapping/")


class Phase2StillCitesTheInlineReference(unittest.TestCase):
    """Criterion 3's second half — asserted unchanged, not merely assumed."""

    def test_phase2_still_points_at_the_inline_reference(self):
        phase2 = flat(MODULE / "phase2-data-mapping.md")
        self.assertRegex(phase2, r"(?i)mapping reference")


if __name__ == "__main__":
    unittest.main()
