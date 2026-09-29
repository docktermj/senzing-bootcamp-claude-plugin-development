"""An assertion about Senzing the COMPANY needs a source, on the same footing as an SDK fact.

At the Module 4 License Key gate on **2026-08-25** a bootcamper chose *"request a free evaluation
license now through the bootcamp"*. Before any value was collected the guide volunteered that
their account email was on the `senzing.com` domain and that *"if you're at Senzing, you very
likely have access to a license through internal channels"* -- stated flatly, unhedged, arguing
against the option they had picked one turn earlier. Their words: *"I don't want assumptions
presented as fact."*

⛔ **The split is the finding.** The one-per-email and 30-day terms in the same paragraph WERE
sourced, from the MCP server. The internal-channels claim was the guide's own inference about how
Senzing employees obtain licenses. Sourced and unsourced arrived together, indistinguishable.

**Why no rule caught it.** `ground-rules.md`'s pre-response checklist enumerates its own scope --
SDK method names, attribute names, config options, error codes, entity-resolution technical
details -- and **INV-080** repeats that enumeration. A claim about Senzing's *business practices*
is none of those, so the guide had no rule telling it that sentence needed a source. The adjacent
invariant, **INV-247**, governs 👉 questions and nothing was asked. An improvised advisory that
reshapes a decision sat in the gap between "every question has an origin" and "every Senzing fact
has a source".

⚠️ **A second gap, separately fixed: nothing governed what may be INFERRED from identifying
context.** INV-321's identifier-stripping discipline is about what leaves the machine in a bug
report, and sub-step 6a already states it cannot apply to the license call, which does not run
without those details. So the collection side was governed and the reasoning side was not.

⛔ **What this guard CANNOT check, stated plainly.** The offending sentence existed in no file. It
was generated at runtime, and no static test can detect a sentence that is not written down --
`tests/test_no_host_control_is_offered_as_a_question.py` discloses the same limit for INV-247. What
is asserted here is that the RULE ships, is scoped past the technical enumeration, and is stated at
the gate where it lapsed. Whether a given run obeys it is `dry-run` phase 3's observation.

Stdlib only; shipped markdown read as text (INV-108).

Enforces **INV-273** (assertions about Senzing, including non-technical ones, come from an MCP
tool, a shipped skill file or something measured here; the technical enumeration is a floor) and
**INV-274** (identifying context is never a premise for reasoning about what the Bootcamper should
choose). ⚠️ Asserts both rules SHIP; runtime compliance is `dry-run` phase 3's.

Source spec: `specs/an-unsourced-inference-about-the-bootcamper-steered-a-consent-gate.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


class Base(unittest.TestCase):
    def has(self, text, pattern, msg):
        self.assertTrue(re.search(pattern, text), msg)


class TheSourcingRuleReachesPastTheTechnicalEnumeration(Base):
    def setUp(self):
        self.text = flat(GROUND_RULES)

    def test_the_checklist_is_marked_a_floor_not_the_whole_set(self):
        """Read as exhaustive, the enumeration licenses everything outside it."""
        self.has(self.text, r"(?i)floor, \*\*NOT\*\* the exhaustive set|a floor, not the exhaustive",
                 "the pre-response checklist is not marked as a floor, so its technical "
                 "enumeration still reads as the complete set of claims needing a source")

    def test_business_practice_assertions_are_named_as_needing_a_source(self):
        self.has(self.text, r"(?i)Senzing the company",
                 "the sourcing rule does not reach assertions about Senzing the company")
        for subject in ("licensing", "support", "internal process"):
            with self.subTest(subject=subject):
                self.has(self.text, re.escape(subject),
                         f"'{subject}' is not named as a claim class needing a source")

    def test_the_three_permitted_sources_are_named_and_closed(self):
        self.has(self.text, r"(?i)MCP tool, from a shipped skill file, or from something measured",
                 "the permitted sources are not enumerated")
        self.has(self.text, r"(?i)no fourth source",
                 "the source list is not closed, so training data remains an implicit option")

    def test_the_original_checklist_survives_verbatim(self):
        """The spec requires the existing checklist kept, not rewritten."""
        self.has(self.text,
                 r"if your response contains Senzing SDK method names, attribute names, config "
                 r"options, error codes, or entity-resolution technical details, you MUST have "
                 r"called an MCP tool this turn",
                 "the pre-response checklist was altered; this spec adds to it, it does not "
                 "replace it")


class TheRemedyIsLabelOrOmitNotLabelAndProceed(Base):
    def setUp(self):
        self.text = flat(GROUND_RULES)

    def test_label_or_omit_is_stated_as_the_rule(self):
        self.has(self.text, r"(?i)Label-or-omit, never label-and-proceed",
                 "the rule does not distinguish label-or-omit from label-and-proceed, so a hedge "
                 "bolted onto the same advisory reads as compliance")

    def test_silence_is_named_as_correct_at_an_answered_gate(self):
        self.has(self.text,
                 r"(?i)at a gate the bootcamper has already answered.{0,60}silence",
                 "the rule does not say that silence is the correct action at a gate the "
                 "bootcamper has already answered -- which is where it lapsed")

    def test_the_labeling_half_is_scoped_to_being_asked(self):
        self.has(self.text, r"(?i)for when the bootcamper \*\*asks\*\*",
                 "the labeling half is not scoped to answering a question, so it reads as "
                 "permission to volunteer a labeled inference")

    def test_the_recorded_incident_keeps_its_evidence(self):
        """A rule with the case that produced it is one a later editor cannot tidy away."""
        self.has(self.text, r"2026-08-25", "the incident date is not recorded")
        self.has(self.text, r"(?i)internal channels",
                 "the actual unsourced claim is not quoted, so the rule loses the example that "
                 "makes its scope checkable")
        self.has(self.text, r"(?i)assumptions presented as fact",
                 "the bootcamper's own words are not recorded")


class IdentityIsNotAPremise(Base):
    def setUp(self):
        self.text = flat(GROUND_RULES)

    def test_the_rule_is_stated(self):
        self.has(self.text,
                 r"(?i)identifying context is for IDENTIFICATION.{0,120}never a premise",
                 "ground-rules.md does not state that identifying context is not a premise for "
                 "the guide's reasoning")

    def test_the_email_domain_inference_is_the_worked_example(self):
        self.has(self.text,
                 r"(?i)Do not infer employer, affiliation, seniority or entitlement from an email "
                 r"domain",
                 "the email-domain-to-employer inference is not named as the worked example")

    def test_it_forbids_steering_a_decision_on_such_an_inference(self):
        self.has(self.text, r"(?i)never use such an inference to steer a decision",
                 "the rule names the inference without forbidding its use to steer a decision, "
                 "which is what actually happened")


class TheGateSaysItsOptionsAreTheOptions(Base):
    def setUp(self):
        self.text = flat(MODULE_04)

    def test_step_8a_says_to_proceed_with_the_selection(self):
        self.has(self.text,
                 r"(?i)The gate's options ARE the options",
                 "Step 8a does not state that its option list is the option list, so re-arguing a "
                 "selection remains unaddressed at the site it happened")

    def test_it_forbids_re_arguing_and_advocating_an_unlisted_option(self):
        self.has(self.text, r"(?i)[Dd]o\s+not re-argue the choice",
                 "Step 8a does not forbid re-arguing the choice")
        self.has(self.text, r"(?i)do not advocate an option this list does not carry",
                 "Step 8a does not forbid advocating an option it does not list")

    def test_it_routes_a_genuine_invalidation_to_a_branch_not_an_advisory(self):
        self.has(self.text,
                 r"(?i)reported failure with its own branch\*?\*? below, not an advisory",
                 "Step 8a does not distinguish a real invalidation (a branch) from an advisory, "
                 "so the rule reads as forbidding necessary error handling")

    def test_it_names_the_consent_stakes_at_the_gate(self):
        self.has(self.text,
                 r"(?i)only step in the bootcamp that transmits the bootcamper's personal details",
                 "Step 8a's new rule does not say why this gate in particular matters")


class TheConsentDisciplineIsUnchanged(Base):
    """Criterion: this spec constrains what may PRECEDE 6a and changes nothing sent."""

    def setUp(self):
        self.text = flat(MODULE_04)

    def test_the_field_list_survives(self):
        for field in ("firstname", "how_heard"):
            with self.subTest(field=field):
                self.has(self.text, re.escape(field), f"{field} is no longer named")
        self.has(self.text, r"(?i)work.{0,3} email address \(personal domains are rejected\)",
                 "the work-email requirement wording changed")

    def test_the_explicit_yes_gate_survives(self):
        self.has(self.text,
                 r"(?i)MUST NOT happen without their explicit yes",
                 "sub-step 6a's consent gate wording changed")

    def test_the_confirm_then_ask_order_survives(self):
        self.has(self.text,
                 r"(?i)Confirm the current requirements from the tool itself\*?\*? before asking",
                 "the confirm-requirements-first step changed")
        self.has(self.text, r"(?i)Never collect a field \"in case\"",
                 "the no-speculative-collection rule changed")


if __name__ == "__main__":
    unittest.main()
