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

#381 widened the scan to all three phrasings INV-339 forbids ("skip Steps 2 and 3", a bare
"skip Step 3", and "straight to verification"), sentence by sentence over whitespace-collapsed
text, after Step 1's existing-install announcement shipped "skipping straight to configuration
verification" wrapped across two lines where the per-line, one-phrasing scan could not see it.

#510 pinned the path's far end: its step list stopped at Step 7 and completed Module 2 "once
verification passes", and its "Required stops" block named only Steps 3, 4 and 5, so neither
reached Step 8's engine configuration or Step 9's engine-class check (INV-037).

Enforces **INV-339** (an existing install skips only the installation: Phase 3 and the environment
script still run before verification). It asserts that Module 2 *states* the rule at each site, and
does **not** establish that a live run follows it, which only `dry-run` phase 3 can observe.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"

#: "skip ... Steps 2 and 3" with no narrowing word between them. ``[^.\n]`` keeps the
#: match inside one sentence so a later sentence's "Step 3" cannot satisfy it. Counts in
#: every shipped file: no other skill numbers a "Steps 2 and 3" pair it could mean.
SKIPS_STEP_3 = re.compile(r"skip[^.\n]{0,60}\bStep(?:s)?\s+2\s+and\s+3\b", re.IGNORECASE)

#: A bare "skip ... Step 3" (#381). Other skills have a Step 3 of their own, so this counts
#: only in Module 2's files or in a sentence that names Module 2 (see ``in_module_2_scope``).
SKIPS_BARE_STEP_3 = re.compile(r"\bskip\w*\b[^.\n]{0,60}?\bStep\s+3\b", re.IGNORECASE)

#: "straight to ... verification" or "skip(ping) to ... verification" (#381): the route past
#: Step 3 named by its destination instead of by its number. Same scope as the bare pattern.
STRAIGHT_TO_VERIFICATION = re.compile(
    r"(?:\bstraight\s+to|\bskip\w*\s+to)\b[^.\n]{0,60}?\bverification\b", re.IGNORECASE
)

#: The words that narrow such a statement to the install half, or deny the skip outright.
NARROWERS = ("installation", "install commands", "not step 3 entirely", "never skipped")

#: A sentence naming Module 2 brings the scoped patterns into play outside its own files.
MODULE_2_NAMES = re.compile(r"\bSDK setup\b|\bModule 2\b", re.IGNORECASE)

#: Where one markdown block ends and the next begins: a blank line, a list item, a heading,
#: a table row or a fence. Sentences are split inside a block, never across one.
BLOCK_BREAK = re.compile(r"\n\s*\n|\n(?=\s*(?:[-*+]\s|\d+[.)]\s|#|\||```|>))")

#: A sentence ends at ., ! or ? (with any closing quote, emphasis or bracket) and a space.
SENTENCE_END = re.compile(r"(?<=[.!?])[\"'*_)\]]*\s+")


def shipped_markdown():
    return sorted(SKILLS.rglob("*.md"))


def sentences(text):
    """Each sentence of ``text`` with whitespace collapsed, so a wrapped sentence is one unit."""
    for block in BLOCK_BREAK.split(text):
        flat = re.sub(r"\s+", " ", block).strip()
        for sentence in SENTENCE_END.split(flat):
            if sentence:
                yield sentence


def in_module_2_scope(sentence, in_module_2_file):
    return in_module_2_file or bool(MODULE_2_NAMES.search(sentence))


def forbidden_skips(sentence, in_module_2_file):
    """The INV-339 phrasings ``sentence`` uses, by name; empty when it uses none.

    A sentence carrying a narrowing word is never flagged: it confines the skip to the
    installation, or says the steps are not skipped at all.
    """
    if any(w in sentence.lower() for w in NARROWERS):
        return []
    found = []
    if SKIPS_STEP_3.search(sentence):
        found.append("skip Steps 2 and 3")
    if in_module_2_scope(sentence, in_module_2_file):
        if SKIPS_BARE_STEP_3.search(sentence):
            found.append("skip Step 3")
        if STRAIGHT_TO_VERIFICATION.search(sentence):
            found.append("straight to verification")
    return found


class NoShippedTextLicensesSkippingStep3Wholesale(unittest.TestCase):
    def test_no_sentence_says_to_skip_step_3_without_narrowing_it(self):
        """Derived by scanning (INV-246), not by naming the file the spec cited.

        Sentence by sentence over whitespace-collapsed text (#381): the defect this widening
        was written for wrapped "skipping" and "straight to configuration verification" onto
        two lines, so a per-line scan could not see it.
        """
        module_2 = SKILLS / "module-02-sdk-setup"
        offenders = []
        for path in shipped_markdown():
            in_module_2_file = module_2 in path.parents
            for sentence in sentences(path.read_text(encoding="utf-8")):
                found = forbidden_skips(sentence, in_module_2_file)
                if found:
                    offenders.append("%s [%s] %s" % (
                        path.relative_to(REPO), ", ".join(found), sentence[:120]))
        self.assertEqual(
            [], offenders,
            "A shipped sentence tells the guide to skip Step 3, or Steps 2 and 3, or to go "
            "straight to verification, without narrowing the skip to the INSTALLATION. Step 3 "
            "also writes the project-local environment script, which an existing install is the "
            "most likely thing to be missing -- and the failure surfaces in a later module as "
            "what looks like a broken SDK: %s" % offenders,
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


class TheWidenedGuardFailsOnEachForbiddenPhrasing(unittest.TestCase):
    """Negative controls for #381: each phrasing INV-339 names, fed through the real scan."""

    def flagged(self, text, in_module_2_file):
        return [f for s in sentences(text) for f in forbidden_skips(s, in_module_2_file)]

    def test_skip_steps_2_and_3_is_flagged_in_any_file(self):
        self.assertEqual(
            ["skip Steps 2 and 3"],
            self.flagged("Report the SDK as installed and skip Steps 2 and 3.", False),
        )

    def test_a_bare_skip_step_3_is_flagged(self):
        self.assertIn("skip Step 3", self.flagged("The SDK is present, so skip Step 3.", True))

    def test_a_bare_skip_step_3_naming_module_2_is_flagged_outside_its_files(self):
        self.assertIn(
            "skip Step 3",
            self.flagged("On an existing install, SDK setup can skip Step 3.", False),
        )

    def test_the_historical_announcement_is_flagged_where_it_wrapped(self):
        """The #381 defect verbatim, with the line break it shipped with."""
        historical = ('Tell the user: "Senzing SDK is already installed (version [X]). No need to '
                      'reinstall, skipping\nstraight to configuration verification."')
        self.assertEqual(["straight to verification"], self.flagged(historical, True))

    def test_skip_to_verification_is_flagged(self):
        self.assertIn(
            "straight to verification",
            self.flagged("If the SDK is installed, skip to verification.", True),
        )

    def test_another_skills_own_step_3_is_not_flagged(self):
        """The `bootcamp-preparation:228` shape: its own Step 3, naming neither Module 2 nor SDK setup."""
        self.assertEqual(
            [], self.flagged("Skip straight from Step 3 to Step 4 and confirm the result.", False)
        )

    def test_the_narrowed_sentences_module_2_ships_are_not_flagged(self):
        for correct in (
            "If the library is present, report the SDK as installed and skip the **installation** "
            "— Step 2, and Step 3's install commands.",
            "These steps are NEVER skipped, even when the SDK is already installed.",
            "Not Step 3 entirely: its Phase 3 and its environment-script work still run.",
        ):
            with self.subTest(correct=correct):
                self.assertEqual([], self.flagged(correct, True))


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

    def test_the_existing_install_announcement_skips_only_the_installation(self):
        """#381: the V4.0+ announcement is what the Bootcamper hears; it narrows the skip.

        Presence of "skip the installation", not the verbatim sentence, so the wording can be
        polished without breaking the guard.
        """
        flat = re.sub(r"\s+", " ", self.text)
        i = flat.find('"Senzing SDK is already installed (version [X]).')
        self.assertNotEqual(i, -1, "Step 1's existing-install announcement was not found.")
        announcement = flat[i:flat.index('"', i + 1) + 1]
        self.assertIn(
            "skip the installation", announcement,
            "The existing-install announcement must narrow the skip to the installation "
            "(INV-339): %s" % announcement,
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
    lists. The block also named `## Agent Behavior`'s "Skip to verification" line as a site that
    contradicted the rule. That line was fixed under #284 (3c55ea7, the INV-339 registration), and
    no test here pins its wording: since #381, `NoShippedTextLicensesSkippingStep3Wholesale`
    reads every sentence of Module 2's files, so it fails if the line contradicts INV-339 again.
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


#: Where Step 1's existing-install path list begins and ends, and where its "Required stops"
#: block ends (#510).
PATH_START = "This is the **existing-install path** (INV-339)."
STOPS_START = "**Required stops (INV-339):**"
STOPS_END = "**If the SDK is found but version is incompatible"

#: The steps after Step 7, in the order the path must name them. ``Step 8\b(?!a)`` keeps
#: "Step 8a" from standing in for Step 8.
LATER_STEPS = (("Step 8", r"\bStep 8\b(?!a)"), ("Step 8a", r"\bStep 8a\b"),
               ("Step 9", r"\bStep 9\b"))


def flatten(text):
    """``text`` with blockquote markers dropped and whitespace collapsed, so a reflow is a no-op."""
    return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", text)).strip()


def existing_install_sites(text):
    """Step 1's existing-install path list and its "Required stops" block, each flattened."""
    start, stops = text.find(PATH_START), text.find(STOPS_START)
    end = text.find(STOPS_END, stops)
    if -1 in (start, stops, end) or not start < stops < end:
        return None, None
    return flatten(text[start:stops]), flatten(text[stops:end])


def existing_install_path_problems(path, stops):
    """Why the path list or the Required-stops block stops short of Step 9; empty when neither does."""
    problems = []
    at = path.find("Step 7")
    if at == -1:
        problems.append("the path list does not name Step 7")
    else:
        for name, pattern in LATER_STEPS:
            found = re.compile(pattern).search(path, at + 1)
            if not found:
                problems.append("the path list does not name %s after the step before it" % name)
                break
            at = found.end()
    completion = [s for s in sentences(path) if "Mark Module 2 as complete" in s]
    if len(completion) != 1:
        problems.append("the path list has no single 'Mark Module 2 as complete' sentence")
    elif not re.search(r"\bStep 9\b", completion[0]):
        problems.append("the completion sentence does not name Step 9: %s" % completion[0])
    if "once verification passes" in path:
        problems.append("the path list still says 'once verification passes', readable as Step 4")
    bullet = [b for b in stops.split(" - ") if "Steps 6, 7, 8, 8a and 9" in b]
    if len(bullet) != 1:
        problems.append("the Required stops block has no bullet naming Steps 6, 7, 8, 8a and 9")
    elif "Module 2 completes only after Step 9" not in bullet[0]:
        problems.append("the Required stops bullet does not say Module 2 completes only after "
                        "Step 9: %s" % bullet[0])
    return problems


class TheExistingInstallPathRunsThroughStep9(unittest.TestCase):
    """#510: the path reaches Steps 8, 8a and 9 and completes Module 2 only after Step 9.

    The list stopped at Step 7 and completed Module 2 "once verification passes", and the
    "Required stops" block named only Steps 3, 4 and 5, so a guide following either one finished
    Module 2 with no engine configuration and no engine-class check (INV-037, INV-339). Read over
    whitespace-collapsed text, as the classes above are, so a reflowed line does not break it.
    """

    #: The path list's last two items as they shipped before #510.
    HISTORICAL = ("  Step 6 (create the project directory structure), then Step 7 (database).\n"
                  "- Mark Module 2 as complete once verification passes.\n")

    def setUp(self):
        self.text = (SKILLS / "module-02-sdk-setup" / "SKILL.md").read_text(encoding="utf-8")

    def problems(self, text):
        path, stops = existing_install_sites(text)
        self.assertIsNotNone(path, "Step 1's existing-install path or its Required stops block "
                                   "was not found.")
        return existing_install_path_problems(path, stops)

    def test_the_path_and_its_required_stops_reach_step_9(self):
        self.assertEqual(
            [], self.problems(self.text),
            "Step 1's existing-install path must continue past Step 7 to Steps 8, 8a and 9, and "
            "both its completion sentence and its Required stops block must name Step 9: "
            "otherwise a guide completes Module 2 with no engine config and no verified engine.",
        )

    def test_the_text_before_510_is_caught(self):
        """Negative control: today's text, spliced back in, fails the same check."""
        at = self.text.index("  Step 6 (create the project directory structure), then Step 7")
        end = self.text.index("\n\n", at)
        regressed = self.text[:at] + self.HISTORICAL + self.text[end + 1:]
        found = self.problems(regressed)
        self.assertIn("the path list does not name Step 8 after the step before it", found)
        self.assertTrue(any("does not name Step 9" in p for p in found), found)
        self.assertIn(
            "the path list still says 'once verification passes', readable as Step 4", found
        )

    def test_the_issue_quoted_text_is_caught_on_its_own(self):
        """The sentence the issue quotes, checked with no file around it."""
        old = flatten("After Step 5, proceed to Step 6 (create the project directory structure), "
                      "then Step 7 (database).\n- Mark Module 2 as complete once verification "
                      "passes.")
        self.assertNotEqual([], existing_install_path_problems(old, ""))

    def test_a_required_stops_block_without_the_bullet_is_caught(self):
        path, stops = existing_install_sites(self.text)
        cut = re.sub(r" - \*\*Steps 6, 7, 8, 8a and 9\*\*.*", "", stops)
        self.assertIn(
            "the Required stops block has no bullet naming Steps 6, 7, 8, 8a and 9",
            existing_install_path_problems(path, cut),
        )

    def test_step_8a_alone_does_not_stand_in_for_step_8(self):
        path, stops = existing_install_sites(self.text)
        dropped = path.replace("then Step 8 (engine configuration), ", "then ")
        self.assertNotEqual(path, dropped, "negative control is stale: Step 8's item is gone")
        self.assertIn("the path list does not name Step 8 after the step before it",
                      existing_install_path_problems(dropped, stops))

    def test_a_reflowed_path_still_passes(self):
        reflowed = self.text.replace("then Step 7 (database), then Step 8 (engine\n  configuration)",
                                     "then Step 7\n  (database), then Step 8 (engine configuration)")
        self.assertNotEqual(self.text, reflowed, "negative control is stale: the wrap moved")
        self.assertEqual([], self.problems(reflowed))


if __name__ == "__main__":
    unittest.main()
