"""Finding an SDK already installed skips the INSTALL, never Step 3 entirely.

SDK setup's Step 3 does two jobs: it installs the SDK, and it writes the
project-local environment script that exports the library and language paths.
Only the first is redundant when the SDK is already present. Skipping both
leaves the Bootcamper with a healthy install and no environment, and every later
module then fails at import with ``libSz.so: cannot open shared object file`` --
which reads as a broken install, in a *later* module, far from the decision that
caused it.

Step 1's own filesystem fallback exists precisely because the import check fails
on a working install when ``PYTHONPATH``/``LD_LIBRARY_PATH`` are unset, so routing
past the step that fixes that is the specific trap.

The module said both things at once: its fallback paragraph read "skip Steps 2 and
3 entirely" while the branch 27 lines below read "Not Step 3 entirely". The first
is what a guide reads at the moment the check succeeds, and it is phrased as a
complete instruction.

#284 added the sites its `DEFERRED INVARIANT` block names that nothing here covered: the
fallback sentence's Phase 3 half, the environment-script section's opening, the troubleshooting
entry, and the two update-offer routes back onto the existing-install path.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"

#: "skip ... Step 3" with no narrowing word between them. ``[^.\n]`` keeps the
#: match inside one sentence so a later sentence's "Step 3" cannot satisfy it.
SKIPS_STEP_3 = re.compile(r"skip[^.\n]{0,60}\bStep(?:s)?\s+2\s+and\s+3\b", re.IGNORECASE)

#: The words that narrow such a statement to the install half.
NARROWERS = ("installation", "install commands", "not step 3 entirely")


def shipped_markdown():
    return sorted(SKILLS.rglob("*.md"))


class NoShippedTextLicensesSkippingStep3Wholesale(unittest.TestCase):
    def test_no_sentence_says_to_skip_steps_2_and_3_without_narrowing_it(self):
        """Derived by scanning (INV-246), not by naming the file the spec cited."""
        offenders = []
        for path in shipped_markdown():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not SKIPS_STEP_3.search(line):
                    continue
                window = line.lower()
                if any(w in window for w in NARROWERS):
                    continue
                offenders.append("%s:%d %s" % (path.relative_to(REPO), n, line.strip()[:90]))
        self.assertEqual(
            [], offenders,
            "A shipped line tells the guide to skip Steps 2 and 3 without narrowing the skip to "
            "the INSTALLATION. Step 3 also writes the project-local environment script, which an "
            "existing install is the most likely thing to be missing -- and the failure surfaces "
            "in a later module as what looks like a broken SDK: %s" % offenders,
        )

    def test_the_scan_pattern_still_matches_the_historical_defect(self):
        """Guards the guard: a pattern matching nothing passes vacuously forever."""
        historical = ("If the library is present, report the SDK as installed, skip Steps 2 and 3 "
                      "entirely, and proceed to Step 4 verification.")
        self.assertTrue(
            SKIPS_STEP_3.search(historical),
            "The scan no longer matches the exact sentence this guard was written for, so it "
            "would not catch the defect returning.",
        )
        self.assertFalse(
            any(w in historical.lower() for w in NARROWERS),
            "The historical sentence must NOT contain a narrowing word -- if it did, the guard "
            "would exempt the very line it exists to reject.",
        )


class Step1StillRoutesAnExistingInstallThroughTheEnvironmentScript(unittest.TestCase):
    def setUp(self):
        self.text = (SKILLS / "module-02-sdk-setup" / "SKILL.md").read_text(encoding="utf-8")

    def test_the_fallback_paragraph_names_the_environment_script(self):
        """A guide arriving via the fallback must be routed without reading further branches.

        The contradiction was survivable only for a reader who continued to the
        V4.0+ branch; the fallback paragraph is a complete instruction on its own
        and is where the wrong turn was taken.
        """
        i = self.text.find("If the library is present")
        self.assertNotEqual(i, -1, "Step 1's filesystem-fallback conclusion was not found.")
        window = self.text[i:i + 500].lower()
        self.assertTrue(
            "environment-script" in window or "environment script" in window,
            "Step 1's fallback conclusion must say the environment-script work still runs. "
            "Without it the paragraph reads as a complete instruction to skip all of Step 3.",
        )

    def test_the_required_stops_block_is_intact(self):
        """The spec's third criterion: the fix must not disturb the block it points at."""
        for expected in ("Required stops", "senzing-env.sh"):
            self.assertIn(
                expected, self.text,
                "The 'Required stops' block is what the corrected sentence now points at; "
                "it must survive the fix intact.",
            )


class TheRuleHoldsAtEverySiteTheDeferralNames(unittest.TestCase):
    """The sites #284's `DEFERRED INVARIANT` block names that no assertion above covered.

    The block drafts "an existing install still runs Step 3's Phase 3 and its environment-script
    work" for `/review-invariants`, the half INV-222 does not state. Each test pins one site it
    lists. ⚠️ The block also names `## Agent Behavior`'s "Skip to verification" line as a site
    that contradicts the rule; that line is left unasserted because fixing it changes shipped
    text, which #284 excludes.
    """

    def setUp(self):
        self.text = (SKILLS / "module-02-sdk-setup" / "SKILL.md").read_text(encoding="utf-8")
        self.flat = re.sub(r"\s+", " ", self.text)

    def test_the_fallback_names_both_halves_that_still_run(self):
        """Step 1's fallback: the install is skipped, Phase 3 and the env script are not."""
        i = self.flat.find("If the library is present, report the SDK as installed")
        self.assertNotEqual(i, -1, "Step 1's filesystem-fallback conclusion was not found.")
        window = self.flat[i:i + 500]
        self.assertIn(
            "skip the **installation** — Step 2, and Step 3's install commands (its Phase 1 EULA "
            "question and its Phase 2 SDK package).",
            window,
        )
        self.assertIn(
            "Not Step 3 entirely: its Phase 3 and its environment-script work still run", window
        )

    def test_the_environment_script_section_says_every_path_ends_there(self):
        heading = "### Create the project-local environment script"
        at = self.text.index(heading)
        opening = re.sub(r"\s+", " ", self.text[at + len(heading):at + len(heading) + 250])
        self.assertIn(
            "Every path through Step 3 ends here, including Step 1's existing-install path, which "
            "skips the install phases and still writes this script.",
            opening,
        )

    def test_the_troubleshooting_entry_checks_for_the_script_first(self):
        self.assertIn(
            "on the existing-install path it is the artifact most likely to be missing",
            self.flat,
        )

    def test_the_update_offer_routes_back_onto_the_path(self):
        """No newer version, and a declined offer, both continue on the existing-install path."""
        self.assertIn(
            "there is no lookup and no offer: record the outcome (see the checkpoint below) and "
            "continue on the existing-install path in Step 1.",
            self.flat,
        )
        self.assertIn(
            '**On no:** one line — "Keeping [installed]." — then Step 1\'s existing-install path.',
            self.flat,
        )


if __name__ == "__main__":
    unittest.main()
