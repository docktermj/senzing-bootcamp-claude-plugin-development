"""An instruction to source a Senzing figure from MCP must name the route that carries it.

Module 1's Step 5a told the guide to compare a record count against the built-in evaluation
license's capacity, "confirmed via the Senzing MCP server (never a hardcoded figure)". That is a
rule with no operation attached: there are thirteen tools, the capacity lives in exactly one place,
and a guide that had already read a *different* license's figure from `submit_feedback`'s tool
description earlier in the session had no prompt to go anywhere else.

On 2026-08-18 it used that other figure. The comparison passed when it should have failed,
`license_guidance_deferred` was left unset, and Module 4's Step 8a gate -- the single volume-gated
License Key prompt in the bootcamp, and the only thing that would have warned the Bootcamper before
they met the cap mid-load -- never fired. **Getting this comparison wrong removes a warning rather
than producing a wrong one.**

(Dated note, 2026-10-23, #780: the paragraph above describes the step as it was then. Step 8a
reads and clears `license_guidance_deferred` but never branches on it; it decides from the
measured collected total. So a wrong comparison records a wrong expectation, and the step now
says so. The route this file guards is unchanged and still matters for that record.)

Module 2 Step 5a asks for the same fact correctly, naming
`sdk_guide(topic='load', language=..., record_count=<above the limit>)` outright. The asymmetry was
the defect: two steps, one fact, one of them runnable.

⚠️ **This is INV-194's shape applied to a POSITIVE claim.** INV-194 governs concluding an *absence*
from the wrong route; here a *value* was concluded from the wrong route, and the step gave the guide
nothing better to do. INV-080 forbids the remembered figure and was violated -- but a step that says
only "ask the server" makes that violation the path of least resistance rather than a lapse.

**Scope: this guard covers the Step 5a fix only.** The spec also proposed a repo-wide sweep of every
"source this from MCP" instruction, and possibly a new invariant for the class. The maintainer split
that out for separate review, so this file asserts the one site and does not sweep.

Source spec: `specs/module1-threshold-check-says-the-mcp-server-where-module2-names-the-route.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PHASE1 = PLUGIN / "skills" / "module-01-business-problem" / "phase1-discovery.md"
MODULE2 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"

#: The route that owns the built-in capacity. A `record_count` under the limit does not surface it.
OWNING_ROUTE = re.compile(r"sdk_guide\(topic='load'")


def step_5a():
    text = PHASE1.read_text(encoding="utf-8")
    start = text.index("### 5a. Record-count threshold check")
    end = text.index("## 6. Confirm inferred details", start)
    return re.sub(r"\s+", " ", text[start:end])


class TheScanIsNotVacuous(unittest.TestCase):
    def test_step_5a_is_locatable(self):
        self.assertIn("license_guidance_deferred", step_5a(),
                      "Step 5a was not located; every check below is vacuous")


class TheInstructionNamesItsRoute(unittest.TestCase):
    def setUp(self):
        self.step = step_5a()

    def test_it_names_the_owning_route(self):
        self.assertRegex(
            self.step, OWNING_ROUTE,
            "Step 5a does not name the tool that carries the built-in capacity. 'Ask the MCP "
            "server' is a rule with no operation attached, and the guide that followed it used "
            "a different license's figure")

    def test_it_says_the_record_count_must_exceed_the_limit(self):
        """A record_count under the cap does not surface the figure at all."""
        self.assertRegex(
            self.step, r"(?i)above the limit",
            "the instruction does not say the record_count must exceed the limit, so the call "
            "can be made in a form that returns nothing and reads as the server not covering it")

    def test_it_forbids_the_vague_form_it_replaced(self):
        self.assertNotRegex(
            self.step, r"(?i)confirmed via the\s*Senzing MCP server \(never a hardcoded figure\)",
            "the route-less instruction is back")

    def test_it_names_the_confusable_figure(self):
        """Naming the right route does not remove the wrong number from the guide's context."""
        self.assertRegex(
            self.step, r"(?i)submit_feedback\(category='license_request'\)",
            "the step does not name the requestable license as the confusable figure. The "
            "guide that got this wrong had read that tool's description earlier in the same "
            "session; a step that names only the right route leaves the wrong number sitting "
            "in context")

    def test_it_states_what_the_comparison_decides(self):
        """#780: the flag is Module 1's recorded expectation; Step 8a never branches on it."""
        self.assertRegex(
            self.step, r"(?i)records Module 1's expectation in `license_guidance_deferred`",
            "the step does not say what the comparison decides: it records Module 1's "
            "expectation, so the cost of a wrong comparison is invisible where it happens")
        self.assertRegex(
            self.step, r"(?i)does not decide whether Module 4's Step 8a License Key gate fires",
            "the step does not say that Step 8a decides from the measured total, not the flag")
        self.assertNotRegex(
            self.step, r"(?i)unset \*?\*?suppresses\*?\*? Module 4's Step 8a",
            "the step again says leaving license_guidance_deferred unset suppresses Module 4's "
            "Step 8a gate. Step 8a reads and clears the flag but never branches on it")

    def test_the_absent_branch_distinguishes_itself_from_the_inv244_error(self):
        """Assuming the built-in figure here is correct; presenting it as measured is not."""
        self.assertRegex(
            self.step, r"(?i)INV-244",
            "the Absent/null branch reads an unwritten field and assumes the built-in capacity "
            "without saying why that is not the inference INV-244 forbids")
        self.assertRegex(
            self.step, r"(?i)never present it as a detected value",
            "the branch does not forbid presenting the assumption as a measurement")


class TheTwoStepsNowAgree(unittest.TestCase):
    """The defect was an asymmetry, so the fix is checked against the site that was right."""

    def test_module_2_still_names_the_same_route(self):
        self.assertRegex(
            re.sub(r"\s+", " ", MODULE2.read_text(encoding="utf-8")), OWNING_ROUTE,
            "Module 2 Step 5a no longer names the route, so the pair this fix aligned has "
            "drifted the other way")


if __name__ == "__main__":
    unittest.main()
