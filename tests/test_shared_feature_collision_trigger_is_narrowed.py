"""The shared-feature collision check asks only about pairs whose sameness the guide cannot show.

Module 5 Phase 2's cross-source check used to fire on any "two or more sources send different
source fields to the same Senzing feature", with one 👉 question per collision. On a generated
three-source scenario every collision was the same quantity by construction (`full_name` vs.
`first_name` + `last_name`, `address` vs. its parsed parts, `date_of_birth` vs. `birth_date`), so
a literal reading spent five turns on questions with self-evident answers (INV-012), and the walk
bundled them in a way the text did not sanction.

These tests pin the narrowed trigger (#336):

- the two exemption rules (parsed vs. full NAME/ADDRESS with the same subject and role; a
  same-quantity rename on a feature-specific feature such as `DOB` or `SSN`);
- the pairs still asked (feature-generic features, different quantities, a mismatched or unclear
  subject or role, anything the guide cannot show), with the date and identifier near-miss
  examples kept;
- one 👉 question per source listing every asked pair, the answer recorded per pair (INV-251);
- where an exempt pair is recorded: one line in the source's `docs/mapping/` write-up in both
  `mapping_verbosity` modes, the rationale column in verbose, and no chat output (INV-012);
- the step-3 summary pointing at the narrowed trigger rather than restating the old one.

Each predicate is negative-controlled against the pre-#336 text, held below as `OLD_CHECK`.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASE2 = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills",
    "module-05-data-quality-mapping", "phase2-data-mapping.md",
)

HEAD = "⛔ **Shared-feature collision check (cross-source)"
END = "This is the one check"

# The check as it stood before #336, verbatim, for the negative controls.
OLD_CHECK = """⛔ **Shared-feature collision check (cross-source).** After mapping a source, compare its feature
targets against the sources already mapped. When **two or more sources send different source fields
to the same Senzing feature**, stop and confirm the two fields measure the *same quantity* — not
merely the same *kind* of thing. Ask one 👉 question naming both fields and the feature (its wording
is necessarily specific to the collision, so it is not a pinned question), and record the answer
with the mapping rationale.

This is the one check the validation scripts structurally **cannot** perform: they each see a single
source, and the defect only exists in the relationship between two. Watch **date** and **identifier**
features hardest, where near-miss semantics are the norm — "year established" vs. "incorporation
filing date" are both plausible `REGISTRATION_DATE` candidates and mean different things; `BID` vs.
`EFX_ID` are both identifiers and are not the same identifier. If they measure different things,
route one to payload instead of the shared feature."""

OLD_SUMMARY = (
    "two source fields aimed at one feature family gets the shared-feature collision "
    "question below"
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def flat(text):
    """Collapse line wraps so a phrase matches wherever the prose breaks."""
    return re.sub(r"\s+", " ", text)


def check_section(text):
    """The check, from its ⛔ head through the near-miss paragraph that follows it."""
    start = text.index(HEAD)
    end = text.index(END, start)
    stop = text.find("\n\n", end)
    return flat(text[start:stop if stop != -1 else len(text)])


# --- predicates, each true of the narrowed check and false of OLD_CHECK -----------------

def states_parsed_vs_full_exemption(s):
    return bool(
        re.search(r"(?i)exempt", s)
        and re.search(r"(?i)parsed vs\.? full NAME or ADDRESS", s)
        and re.search(r"(?i)same subject (?:in the same|and) role", s)
    )


def states_same_quantity_rename_exemption(s):
    return bool(
        re.search(r"(?i)same quantity under a different name, on a feature-specific feature", s)
        and "`DOB`" in s and "`SSN`" in s
        and "`date_of_birth`" in s and "`birth_date`" in s
    )


def says_exempt_is_recorded_not_asked(s):
    return bool(re.search(r"(?i)exempt\W+recorded, not asked", s))


def keeps_the_still_asked_cases(s):
    return bool(
        re.search(r"(?i)asked\W+every other pair", s)
        and re.search(r"(?i)feature-generic", s)
        and re.search(r"(?i)different quantities", s)
        and re.search(r"(?i)subject or role differs or is unclear", s)
        and re.search(r"(?i)any pair the guide cannot show is the same quantity", s)
        # the near-miss examples the check exists for
        and "year established" in s and "incorporation filing date" in s
        and "`BID`" in s and "`EFX_ID`" in s
    )


def bundles_one_question_per_source(s):
    return bool(
        re.search(r"(?i)one\*{0,2} 👉 question per source", s)
        and re.search(r"(?i)list each pair with its feature", s)
        and re.search(r"(?i)name any pair that doesn't", s)
        and re.search(r"(?i)record the answer per pair", s)
        and "INV-251" in s
    )


def states_the_recording_rule(s):
    return bool(
        re.search(r"(?i)one line in that source's `docs/mapping/` write-up", s)
        and re.search(r"(?i)both verbose and concise `mapping_verbosity`", s)
        and re.search(r"(?i)verbose mode the line also goes in the mapping table's rationale column", s)
        and re.search(r"(?i)exempt pair produces no chat output", s)
    )


def handles_only_exempt_and_repeat_cases(s):
    return bool(
        re.search(r"(?i)only exempt pairs asks nothing", s)
        and re.search(r"(?i)not asked again when a later source is mapped \(INV-006\)", s)
    )


def uses_the_old_unconditional_trigger(s):
    return bool(re.search(r"(?i)Ask one 👉 question naming both fields", s))


PREDICATES = (
    states_parsed_vs_full_exemption,
    states_same_quantity_rename_exemption,
    says_exempt_is_recorded_not_asked,
    keeps_the_still_asked_cases,
    bundles_one_question_per_source,
    states_the_recording_rule,
    handles_only_exempt_and_repeat_cases,
)


class TheCollisionCheckIsNarrowed(unittest.TestCase):
    def setUp(self):
        self.section = check_section(read(PHASE2))

    def test_parsed_vs_full_name_or_address_is_exempt(self):
        self.assertTrue(states_parsed_vs_full_exemption(self.section),
                        "the parsed-vs-full exemption, with its same-subject-and-role "
                        "condition, is missing")

    def test_same_quantity_rename_on_a_feature_specific_feature_is_exempt(self):
        self.assertTrue(states_same_quantity_rename_exemption(self.section))

    def test_an_exempt_pair_is_recorded_not_asked(self):
        self.assertTrue(says_exempt_is_recorded_not_asked(self.section))

    def test_the_near_miss_cases_are_still_asked(self):
        self.assertTrue(keeps_the_still_asked_cases(self.section),
                        "feature-generic, different-quantity, mismatched-role and "
                        "cannot-show pairs must still be asked, with the date and "
                        "identifier examples kept")

    def test_one_question_per_source_lists_every_asked_pair(self):
        self.assertTrue(bundles_one_question_per_source(self.section))

    def test_an_exempt_pair_is_recorded_in_the_write_up_in_both_modes(self):
        self.assertTrue(states_the_recording_rule(self.section))

    def test_only_exempt_pairs_ask_nothing_and_answers_are_not_reasked(self):
        self.assertTrue(handles_only_exempt_and_repeat_cases(self.section))

    def test_the_old_one_question_per_collision_trigger_is_gone(self):
        self.assertFalse(uses_the_old_unconditional_trigger(self.section))

    def test_the_hard_rule_cites_its_invariants_at_the_line(self):
        head_line = read(PHASE2)[read(PHASE2).index(HEAD):].split("\n\n", 1)[0]
        for inv in ("INV-012", "INV-251", "INV-006"):
            self.assertIn(inv, head_line)


class TheStepThreeSummaryPointsAtTheNarrowedTrigger(unittest.TestCase):
    def test_the_summary_no_longer_restates_the_unconditional_trigger(self):
        self.assertNotIn(OLD_SUMMARY, flat(read(PHASE2)))

    def test_the_summary_says_the_question_is_conditional(self):
        self.assertRegex(
            flat(read(PHASE2)),
            r"(?i)shared-feature collision check below asks only about the cross-source pairs "
            r"its exemptions leave",
        )


class NegativeControls(unittest.TestCase):
    """Every predicate rejects the pre-#336 check, so none of them passes vacuously."""

    def test_each_predicate_fails_on_the_old_check(self):
        old = check_section(OLD_CHECK)
        for predicate in PREDICATES:
            with self.subTest(predicate=predicate.__name__):
                self.assertFalse(predicate(old))

    def test_the_old_trigger_is_detected_on_the_old_check(self):
        self.assertTrue(uses_the_old_unconditional_trigger(check_section(OLD_CHECK)))


if __name__ == "__main__":
    unittest.main()
