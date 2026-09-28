"""The Truth Set acquisition step must make a call that can actually succeed.

Found by the 2026-07-29 dry run (phase 1). Module 3b Step 1.1 — the step that decides
whether the Truth Set is available, and therefore whether INV-077's guaranteed
visualization gets real ground-truth data — said:

    Call `get_sample_data` and inspect the response for a named Truth Set reference.

`dataset` is a **required** parameter. The tool's own schema says so in as many words:
"Required: schema-respecting clients cannot omit it — pass 'list' to discover." So the
call as instructed fails and reports nothing about availability (INV-136).

The classification was stale in the same breath. It read `unavailable` = "only the CORD
collections (Las Vegas, London, Moscow) are present" — but on server 1.32.1
`get_sample_data(dataset='list')` returns **four** datasets, the fourth being `truthset`
with `available: true` and 159 records across CUSTOMERS / REFERENCE / WATCHLIST — exactly
the codes and count the plugin's own example recap cites. And `dataset='truthset'`, the
call that retrieves it, appeared **nowhere in the plugin**.

So the module was written to conclude the MCP primary path had failed when it works,
dropping to the external `github_fallback` and recording the wrong provenance — while the
step's own first line declares MCP "the primary and preferred source".

These tests pin the call shape and the classification, not the record counts: counts come
from the response (INV-080), so asserting them here would re-create the staleness this
finding is about.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "skills")
MOD_3B = os.path.join(SKILLS, "module-03b-truthset-visualization")
PHASE_1 = os.path.join(MOD_3B, "phase1-visualization.md")
SKILL = os.path.join(MOD_3B, "SKILL.md")


def flat(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


class TheCallNamesItsRequiredParameter(unittest.TestCase):
    def test_the_acquisition_step_passes_a_dataset(self):
        self.assertRegex(
            flat(PHASE_1),
            r"get_sample_data\(dataset='list'\)",
            "discovery must pass dataset='list' — a bare call fails (INV-136)",
        )

    def test_the_retrieval_call_is_named(self):
        """`dataset='truthset'` was absent from the entire plugin."""
        self.assertRegex(flat(PHASE_1), r"dataset='truthset'")

    def test_the_skill_overview_names_it_too(self):
        self.assertRegex(flat(SKILL), r"get_sample_data\(dataset='truthset'\)")

    def test_no_bare_call_is_instructed_anywhere_in_the_module(self):
        for path in (PHASE_1, SKILL):
            with self.subTest(file=os.path.basename(path)):
                text = flat(path)
                for match in re.finditer(r"`get_sample_data`(?! *\()", text):
                    window = text[max(0, match.start() - 200): match.end() + 260]
                    self.assertRegex(
                        window,
                        r"dataset=|required",
                        "a bare `get_sample_data` reference must sit beside the required "
                        "parameter, or a reader will call it without one",
                    )

    def test_the_requirement_is_stated_as_a_requirement(self):
        text = flat(PHASE_1)
        self.assertRegex(text, r"(?i)`dataset` is a \*\*required\*\* parameter")
        self.assertRegex(text, r"(?i)bare `get_sample_data\(\)` fails")


class TheClassificationMatchesTheServer(unittest.TestCase):
    def test_availability_is_decided_from_available_datasets(self):
        self.assertRegex(flat(PHASE_1), r"available_datasets")

    def test_unavailable_is_no_truthset_entry_not_a_hardcoded_cord_list(self):
        """The stale form enumerated three collections and missed the fourth dataset."""
        text = flat(PHASE_1)
        self.assertNotRegex(
            text,
            r"only the CORD collections \(Las Vegas, London, Moscow\) are present",
            "the server lists truthset alongside the CORD collections, so an enumeration "
            "of three is a classification that can never see it",
        )
        self.assertRegex(text, r"(?i)no such entry")

    def test_the_fallback_is_described_as_exceptional(self):
        """It read as a routine branch while the primary path in fact works."""
        for path in (PHASE_1, SKILL):
            with self.subTest(file=os.path.basename(path)):
                self.assertRegex(flat(path), r"(?i)exceptional|normally succeeds")

    def test_the_verification_is_dated_and_names_the_server_version(self):
        for path in (PHASE_1, SKILL):
            with self.subTest(file=os.path.basename(path)):
                # A dated server stamp: a version plus a YYYY-MM-DD date (#200).
                self.assertRegex(
                    flat(path), r"(?i)verified on MCP server \d+\.\d+\.\d+, \d{4}-\d{2}-\d{2}"
                )

    def test_the_reader_is_told_to_re_verify_rather_than_trust_the_note(self):
        """INV-080: the server ships independently, so a dated note is not authority."""
        for path in (PHASE_1, SKILL):
            with self.subTest(file=os.path.basename(path)):
                self.assertRegex(flat(path), r"(?i)[Rr]e-?(check|verify)")

    def test_codes_and_counts_come_from_the_response(self):
        """Hardcoding them here is how the previous classification went stale."""
        self.assertRegex(
            flat(PHASE_1), r"(?i)from the response, never from this file"
        )


class TheFallbackMachineryIsUnchanged(unittest.TestCase):
    """The fix narrows when the fallback fires; it does not remove it."""

    def test_the_registry_indirection_survives(self):
        text = flat(PHASE_1)
        self.assertIn("senzing_truthset_demo", text)
        self.assertRegex(text, r"(?i)never a raw URL")

    def test_the_cord_substitute_offer_survives(self):
        self.assertRegex(flat(PHASE_1), r"(?i)non-deterministic CORD collection")

    def test_provenance_values_are_still_recorded(self):
        text = flat(PHASE_1)
        for value in ("mcp_primary", "github_fallback", "cord_substitute"):
            with self.subTest(value=value):
                self.assertIn(value, text)


if __name__ == "__main__":
    unittest.main()
