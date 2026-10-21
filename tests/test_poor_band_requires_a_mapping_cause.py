"""A high possible-match rate is a finding; only a mapping-actionable one reaches Module 5.

Enforces **INV-264** — a quality band MUST NOT by itself route the Bootcamper into remediation;
the step MUST establish whether the cause is a data characteristic or a mapping defect first.
Registered 2026-08-21 at the maintainer's sign-off, with all three band-routing sites recorded.

Step 3b bands the possible-match rate and routed **Poor** (>15%) straight to *"The results suggest
mapping improvements would help"* plus the Module 5 remap loop. A run measured **48.9%** and the
sampled evidence showed the cause was not a mapping defect: about half the near-misses came from one
source's genuinely empty contact fields (PHONE 45.7% populated, ADDRESS_LINE1 55% -- correctly
mapped, the values simply absent from the source), and the rest from coincidental full-name
collisions in a synthetic generator's limited name pool. Neither is fixable by remapping. The loop
was offered anyway, accepted, and had nothing to change.

**The band was acting as a diagnosis.** The old wording said the shared match-key pattern *is* what
points at an unmapped feature, so the evidence was gathered and then narrated toward a conclusion the
band had already reached -- nothing let the evidence cancel the offer.

⚠️ **This is not what `step3b-quality-lookup-misroutes-and-omits-the-evidence-requirement` fixed.**
That spec added the sample-and-show requirement and said explicitly that it changed *what the guide
must show, not where the bands sit*. The evidence is now collected. What was still missing is that it
**decides**.

**The server states all three of the things the plugin was missing** (re-asked on
`reporting_guide(topic='evaluation', language='python')`, server **1.33.0, 2026-08-21**): the
diagnosis is conditional on **concentration** rather than on the rate; it is hedged as **likely**;
and it names **two** causes -- "unmapped **or has data quality issues**" -- of which the plugin
carried only the first. The same response also supplies the discriminator the plugin never ran, the
profiler-uniqueness sanity comparison.

⚠️ **The thresholds are deliberately untouched.** `< 5%` / `5-15%` / `> 15%` still decide whether to
look hard; this spec changed only what may follow from looking. `TheThresholdsAreUnchanged` pins them.

**Widened to Marginal (#751).** The Marginal band (5-15%) asked proceed-or-iterate on every
verdict, with no cause established, while the stricter Poor band continued with no question on the
same not-mapping-actionable finding: a run with 452 of 453 near-misses name-only was still asked.
The sanity comparison, the actionability test and the three outcomes are now one statement, "the
cause check", that both bands cite (INV-300); only its mapping-actionable outcome asks, the Module 5
feedback loop on Poor and the pinned Marginal question on Marginal. `TheMarginalBandRunsTheCauseCheck`
asserts it, with negative controls on mutated copies (INV-265).

Source spec: `specs/poor-band-offers-the-remap-loop-before-anything-establishes-a-mapping-cause.md`.
Widened by GitHub issue #751.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE1 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-07-query-visualize-discover" / "phase1-query-visualize.md")


CAUSE_ANCHOR = '<a id="the-cause-check"></a>'


def squash(text):
    """Blockquote markers stripped, whitespace collapsed."""
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M))


def step_3b():
    """Step 3b, with blockquote markers stripped and whitespace collapsed.

    The server quotes are wrapped blockquotes, so a `>` continuation lands mid-phrase after a
    naive collapse -- "unmapped **or has data > quality issues**". Strip the markers first, the
    same way `test_verbatim_check_limitations_freshness.squash` does.
    """
    text = PHASE1.read_text(encoding="utf-8")
    start = text.index("**Quality assessment:**")
    end = text.index("### 3c. Visualization offer", start)
    body = re.sub(r"^[ \t]*>[ \t]?", "", text[start:end], flags=re.M)
    return re.sub(r"\s+", " ", body)


class TheScanIsNotVacuous(unittest.TestCase):
    def test_step_3b_is_locatable(self):
        self.assertIn("Possible matches", step_3b(),
                      "step 3b was not located; every check below is vacuous")


class TheThresholdsAreUnchanged(unittest.TestCase):
    """The one thing this spec must NOT have moved."""

    def test_all_three_bands_still_read_as_before(self):
        s = step_3b()
        self.assertIn("possible matches < 5%", s)
        self.assertIn("possible matches 5–15%", s)
        self.assertIn("possible matches > 15%", s)


class ThePoorBandIsAFindingNotAVerdict(unittest.TestCase):
    def setUp(self):
        self.s = step_3b()

    def test_it_no_longer_asserts_an_unmapped_feature(self):
        self.assertNotIn(
            "since that is what points at the unmapped feature", self.s,
            "the branch still asserts that a shared match-key pattern points at an unmapped "
            "feature, which presupposes the diagnosis the evidence is supposed to establish")

    def test_it_calls_the_rate_a_finding(self):
        self.assertRegex(
            self.s, r"(?i)finding, not a verdict on the mapping",
            "the Poor band still reads as a verdict rather than a finding")

    def test_it_relays_the_servers_conditional_and_hedge(self):
        self.assertIn("concentrated on one match key pattern", self.s,
                      "the server's concentration test is not relayed")
        self.assertIn("likely", self.s, "the server's hedge is not relayed")
        self.assertRegex(
            self.s, r"unmapped \*{0,2}or has data\s*\*{0,2}quality issues",
            "the server's SECOND cause is not relayed, which is the half the plugin dropped "
            "and the half the reported run actually hit")

    def test_it_cites_the_route_version_and_date(self):
        self.assertIn("reporting_guide(topic='evaluation'", self.s)
        self.assertRegex(self.s, r"1\.33\.0, 2026-08-21")


class TheLoopIsReachableOnlyFromTheActionableOutcome(unittest.TestCase):
    def setUp(self):
        self.s = step_3b()

    def test_three_outcomes_are_named(self):
        for phrase in ("Mapping-actionable", "Not mapping-actionable", "Could not determine"):
            with self.subTest(outcome=phrase):
                self.assertIn(phrase, self.s, "outcome %r is not named" % phrase)

    def test_the_non_actionable_outcomes_do_not_ask_the_module_5_question(self):
        self.assertRegex(
            self.s, r"(?i)Outcomes 2 and 3 do NOT ask the Module 5 question",
            "nothing prevents a non-actionable or undetermined outcome from reaching the remap "
            "offer, which is the defect: a band alone routing a Bootcamper into a remap")

    def test_they_continue_into_3c_so_the_turn_still_closes(self):
        """A branch that must ask a question it has none for is the unsatisfiable class."""
        self.assertRegex(
            self.s, r"(?i)continuing into 3c, whose pinned visualization offer closes the turn",
            "the non-actionable outcomes do not say how their turn ends, so a guide either "
            "invents a question or ends with zero")

    def test_remapping_is_said_not_to_help_on_the_non_actionable_path(self):
        self.assertRegex(
            self.s, r"(?i)remapping\s*would not change it",
            "the non-actionable outcome does not tell the Bootcamper that a remap would not "
            "help, which is what stops them accepting a loop with nothing to change")


class TheNonActionableCausesAreNamed(unittest.TestCase):
    def setUp(self):
        self.s = step_3b()

    def test_source_field_sparsity_is_named_and_routed_to_completeness(self):
        self.assertRegex(self.s, r"(?i)Source field sparsity")
        self.assertRegex(
            self.s, r"(?i)Module 5 already measured it as `completeness`",
            "the sparsity check invents a measurement instead of routing to the one Module 5 "
            "already produced")

    def test_name_collisions_are_named(self):
        self.assertRegex(self.s, r"(?i)Name-only collisions")

    def test_the_generated_scenario_link_is_stated(self):
        """The plugin creates the very characteristic that produces non-actionable near-misses."""
        self.assertRegex(
            self.s, r"(?i)INV-239 requires a source\s*gapped into the 70-79% band",
            "nothing connects this to the generated-scenario path, where the plugin itself "
            "gaps a source into the low band and thereby manufactures the sparsity")


class TheSanityComparisonIsPrescribed(unittest.TestCase):
    def test_the_profiler_comparison_comes_before_the_diagnosis(self):
        s = step_3b()
        self.assertRegex(
            s, r"(?i)Run the sanity comparison first",
            "the profiler-uniqueness comparison is not prescribed before diagnosing")
        self.assertIn("source profiler", s, "the server's own wording is not quoted")


def cause_check_problems(text):
    """#751: both bands cite one cause check; only its first outcome asks, on either band."""
    if text.count(CAUSE_ANCHOR) != 1:
        return ["the cause check's anchor is missing or stated twice"]
    flat = squash(text)
    problems = []
    for band, start, end in (("Marginal", "- **Marginal:**", "- **Poor:**"),
                             ("Poor", "- **Poor:**", CAUSE_ANCHOR)):
        i = text.find(start)
        j = text.find(end, i + 1) if i != -1 else -1
        if i == -1 or j == -1:
            problems.append("the %s bullet moved" % band)
            continue
        if "[the cause check](#the-cause-check)" not in text[i:j]:
            problems.append("the %s bullet does not cite the cause check" % band)
    if "then ask whether to proceed or iterate" in flat:
        problems.append("the Marginal band still asks proceed-or-iterate before any cause is "
                        "established")
    for phrase in ("The cause check: the Marginal and Poor bands both run it, and it has THREE "
                   "outcomes, of which only the first asks a question",
                   "This is the one statement of the check",
                   "Outcomes 2 and 3 do NOT ask the Module 5 question, and on a Marginal verdict "
                   "they do NOT ask the Marginal question either",
                   "on either band they end by continuing into 3c"):
        if phrase not in flat.replace("**", ""):
            problems.append("the cause check does not say %r" % phrase)
    for once in ("Run the sanity comparison first", "Then route on what the evidence shows",
                 "1. **Mapping-actionable**", "2. **Not mapping-actionable**",
                 "3. **Could not determine**"):
        if flat.count(once) != 1:
            problems.append("%r is stated %d times, not once (INV-300)" % (once, flat.count(once)))
    i = flat.find("1. **Mapping-actionable**")
    j = flat.find("2. **Not mapping-actionable**")
    if i == -1 or j == -1 or not ("Poor" in flat[i:j] and "#the-marginal-question" in flat[i:j]):
        problems.append("outcome 1 does not name each band's question")
    return problems


class TheMarginalBandRunsTheCauseCheck(unittest.TestCase):
    """#751: Marginal and Poor share one cause check, and only the actionable outcome asks."""

    def setUp(self):
        self.text = PHASE1.read_text(encoding="utf-8")

    def test_both_bands_cite_one_cause_check(self):
        self.assertEqual([], cause_check_problems(self.text))

    def mutate(self, old, new=""):
        self.assertIn(old, self.text, "negative control is stale: %r is gone" % old[:60])
        return self.text.replace(old, new, 1)

    def test_a_marginal_bullet_that_skips_the_check_fails(self):
        mutated = self.mutate("Then\n  run [the cause check](#the-cause-check) below before asking "
                              "anything.", "Then ask whether to proceed or iterate.")
        self.assertTrue(cause_check_problems(mutated))

    def test_a_second_copy_of_the_outcomes_fails(self):
        mutated = self.mutate("- **Poor:**", "  Then route on what the evidence shows.\n- **Poor:**")
        self.assertTrue(cause_check_problems(mutated))

    def test_a_non_actionable_marginal_outcome_that_asks_fails(self):
        mutated = self.mutate("and on a Marginal verdict they do\nNOT ask the Marginal question "
                              "either", "and on a Marginal verdict they ask the Marginal question")
        self.assertTrue(cause_check_problems(mutated))


class TheFindingSurvives(unittest.TestCase):
    def test_a_non_actionable_finding_reaches_the_recap(self):
        self.assertRegex(
            step_3b(), r"(?i)non-actionable Marginal or Poor finding still goes in the module recap",
            "a finding that routed nowhere is silently discarded")


if __name__ == "__main__":
    unittest.main()
