"""Step 10's `record_type` guidance, and the retirement condition that keeps it from going stale.

`mapping_workflow`'s step-2 response contradicts itself about `record_type`: its instructions say
*"set record_type to `MIXED`"* on a discriminated source, while the **same response's**
`advance_schema` declares `record_type` as `enum: ["PERSON", "ORGANIZATION", "VESSEL", "AIRCRAFT"]`.
Sending `MIXED` is accepted and warns. Reproduced live on **MCP server 1.33.0, 2026-08-21** by
running `mapping_workflow` start -> step 1 -> step 2 with an 8-field mixed-type source:

    warnings: ["schema_plan[0] (watchlist_pep): record_type 'MIXED' is non-standard —
               expected one of: PERSON, ORGANIZATION, VESSEL, AIRCRAFT"]

So the plugin pre-empts it: send an enum-valid type and declare the mixture via step 3's
`type_discriminator`, which is where the tool's own prose says the typing happens anyway.

⚠️ **The point of this guard is the retirement condition, not the guidance.** This is a note about a
*current* server defect, and the repo has twice shipped a workaround that outlived the defect it
worked around — most recently the eval-license duration note, retired 2026-08-21 only because an
unrelated triage run happened to re-ask the same route. A note like this one must therefore carry,
in shipped text, the condition under which it should be removed; otherwise nothing in an offline
suite (INV-108) can ever notice the server has been fixed.

Source spec: `specs/step-2-prose-prescribes-a-record-type-its-own-schema-rejects.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE2 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping" / "phase2-data-mapping.md")


def plan_step():
    """The step-10 (Plan) section, where the step-2 advance is committed."""
    text = PHASE2.read_text(encoding="utf-8")
    start = text.index("### 10. Plan")
    end = text.index("### 11. Map", start)
    return re.sub(r"\s+", " ", text[start:end])


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_file_exists(self):
        self.assertTrue(PHASE2.is_file(), "phase2-data-mapping.md moved")

    def test_the_plan_step_is_locatable(self):
        self.assertIn("record_id_source", plan_step(),
                      "the Plan step was not located, so every check below is vacuous")


class TheContradictionIsPreEmptedAtTheStepThatHitsIt(unittest.TestCase):
    def setUp(self):
        self.plan = plan_step()

    def test_it_prescribes_an_enum_valid_record_type(self):
        self.assertRegex(
            self.plan, r"(?i)send an enum-valid `record_type`",
            "step 10 does not tell the guide what to send, so it will follow the tool's "
            "prose and warn on every discriminated source")

    def test_it_quotes_both_halves_of_the_same_response(self):
        """A reader has to be able to see the contradiction, not take it on faith."""
        self.assertIn('set record_type to `"MIXED"`', self.plan,
                      "the tool's own instruction is not quoted")
        self.assertRegex(
            self.plan,
            r'enum: \[\s*"PERSON",\s*"ORGANIZATION",\s*"VESSEL",\s*"AIRCRAFT"\s*\]',
            "the advance_schema enum that rejects MIXED is not quoted")
        self.assertRegex(
            self.plan, r"(?i)same response",
            "the note does not say both halves come from one response, which is what makes "
            "it a contradiction rather than two tools disagreeing")

    def test_it_says_the_warning_is_not_the_bootcampers_error(self):
        self.assertRegex(
            self.plan, r"(?i)not your error and not a mapping defect",
            "a guide meeting the warning has nothing telling them it is expected, so they "
            "will iterate on a correct mapping (INV-173)")

    def test_it_does_not_license_ignoring_step_2_warnings_generally(self):
        """The step's other warnings are real; one known-bad interaction is not a blanket."""
        self.assertRegex(
            self.plan, r"(?i)does not\s*license ignoring step-2 warnings generally",
            "the note reads as permission to ignore this step's warnings, which would "
            "suppress the real ones")

    def test_it_names_vessel_and_aircraft_as_valid(self):
        """The prose's "must be PERSON or ORGANIZATION" is wrong against its own enum."""
        self.assertRegex(
            self.plan, r"(?i)`VESSEL` and `AIRCRAFT` are valid",
            "a guide reading the tool's prose will not know these are accepted, which a "
            "watchlist source can genuinely need")


class TheNoteCarriesItsOwnRetirementCondition(unittest.TestCase):
    """The half that keeps a current-defect note from becoming a stale one.

    Negative-controlled by removing the retirement sentence, confirming this fails, and
    restoring it (2026-08-21).
    """

    def setUp(self):
        self.plan = plan_step()

    def test_the_retirement_condition_is_stated_in_shipped_text(self):
        self.assertRegex(
            self.plan,
            r"(?i)Retire this note once step 2's prose and its `advance_schema` agree",
            "the note does not say when to remove it. Nothing offline can detect that the "
            "server was fixed (INV-108), so an unstated condition means the note outlives "
            "the defect — the shape that produced "
            "`the-eval-license-duration-tools-now-agree-so-retire-the-note-and-its-guard`")

    def test_the_claim_is_dated_and_versioned(self):
        self.assertRegex(
            self.plan, r"(?i)server \*\*1\.33\.0, 2026-08-21\*\*",
            "the contradiction is asserted with no server version and date, so a later "
            "reader cannot tell whether it was re-checked or copied forward")


if __name__ == "__main__":
    unittest.main()
