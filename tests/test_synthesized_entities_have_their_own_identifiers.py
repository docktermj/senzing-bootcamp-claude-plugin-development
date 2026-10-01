"""Two different invented people must not share an email, a phone or an identifier number.

Module 4 Step 2's `provenance: synthesized` branch required the record key to be unique ("the
duplication is in the entity, never in the key") and said nothing about the identifying
features of distinct entities. Observed on a 2026-10-01 walk: the generated scenario built
emails from first name, last name and a number from 1 to 99, so 7,000 people drawn from 1,197
distinct names gave 53 pairs of different people the same name and the same email. Every pair
resolved together on that evidence, the scenario's own ground truth called each merge false,
and one appeared as the how-analysis example in Query, Visualize and Discover — the bootcamp's
accuracy figures made a correct result look like an error.

The rule sits beside the record-key block; its self-check sits inside the existing band
self-check, with the same regenerate-never-patch discipline; the sample `quality_intent` shows
how deliberate sharing is recorded.

Extends **INV-239** (generated data carries the flaws it should and none it should not). Each
predicate is negative-controlled: it is run against the branch with the clause removed and must
fail there, so a predicate that matches surrounding text instead of the rule is caught.

Source issue: #343.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COLLECTION = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
              / "module-04-data-collection" / "SKILL.md")

RULE_HEAD = "⛔ **Give each invented entity its own identifiers"
SELF_CHECK_HEAD = "⛔ **In the same pass, count identifier collisions"


def squash(text):
    return re.sub(r"\s+", " ", text)


def synthesized_branch():
    """Step 2's `provenance: synthesized` bullet — the same scope as its quality-gaps guard."""
    body = squash(COLLECTION.read_text(encoding="utf-8"))
    start = body.index("**`provenance: synthesized`**")
    end = body.index("⚠️ **Both are bootcamp-generated", start)
    return body[start:end]


def paragraph(branch, head):
    """The paragraph opening at ``head``, to the next ⛔/⚠️ marker or bold paragraph lead."""
    i = branch.index(head)
    nxt = re.search(r" (?:⛔|⚠️ \*\*Check|\*\*Record the intended band)", branch[i + len(head):])
    return branch[i:i + len(head) + nxt.start()] if nxt else branch[i:]


def without(branch, head):
    """The branch with the paragraph at ``head`` cut out — the negative control's input."""
    p = paragraph(branch, head)
    return branch.replace(p, "")


def sample_yaml():
    """The sample `quality_intent` block shown in Step 2, raw (indentation kept)."""
    text = COLLECTION.read_text(encoding="utf-8")
    i = text.index("- name: MERIDIAN_CRM")
    return text[i:text.index("```", i)]


# --- Predicates. Each takes text and says whether the clause is there. ---

def covers_the_identifier_features(t):
    return all(re.search(p, t) for p in (
        r"(?i)\*\*email\*\*", r"(?i)\*\*phone\*\*", r"(?i)\*\*identifier number\*\*",
        r"(?i)SSN, passport, driver's license, account or loyalty number",
        r"(?i)exactly\s+one invented entity, person or organization",
    ))


def declares_sharing_under_quality_intent(t):
    return bool(re.search(r"`quality_intent\.shared_features` with the reason", t)
                and re.search(r"(?i)an unlisted share is a collision", t))


def scopes_each_entry_to_its_reason(t):
    """A `shared_features` entry names a feature, so without this clause one entry for `phone`
    would excuse every phone collision in the source — the defect again, declared."""
    return bool(re.search(r"(?i)an entry covers only the shares its reason describes, never "
                          r"every value of that feature", t))


def keeps_same_entity_features(t):
    return bool(re.search(r"(?i)\*\*entity, not the record\*\*", t)
                and re.search(r"(?i)per-campaign duplicates and the cross-source overlap", t)
                and re.search(r"(?i)keep that entity's features", t))


def allows_shared_names_as_hard_negatives(t):
    return bool(re.search(r"(?i)\*\*Names may repeat\*\*", t)
                and re.search(r"(?i)intended \*\*hard negatives\*\*", t))


def leaves_address_and_dob_uncovered(t):
    return bool(re.search(r"(?i)so may an address or a date of birth", t))


def names_the_anti_pattern(t):
    return bool(re.search(r"(?i)name plus a small\s+number", t)
                and "first.last<1-99>@" in t
                and re.search(r"(?i)name pool is smaller than the population", t))


def requires_the_collision_self_check(t):
    return bool(re.search(r"(?i)count identifier collisions", t)
                and re.search(r"(?i)no `shared_features` entry declares", t)
                and re.search(r"(?i)regenerate the affected values or the source before "
                              r"anything loads or scores it", t)
                and re.search(r"(?i)never patch the ground truth, the scores or the results", t))


def shows_a_shared_feature_with_reason(yaml_text):
    """`shared_features:` under `quality_intent`, with a `feature:` and a non-empty `reason:`."""
    m = re.search(r"(?m)^(\s*)quality_intent:\n((?:\1\s+.*\n?)+)", yaml_text)
    if not m:
        return False
    block = m.group(2)
    return bool(re.search(r"(?m)^\s+shared_features:", block)
                and re.search(r"(?m)^\s+- feature: \w+", block)
                and re.search(r'(?m)^\s+reason: "[^"]+"', block))


class TheRuleSitsBesideTheRecordKeyBlock(unittest.TestCase):

    def test_it_is_a_hard_rule_in_the_synthesized_branch(self):
        self.assertIn(RULE_HEAD, synthesized_branch())

    def test_it_follows_the_record_key_block(self):
        branch = synthesized_branch()
        key = branch.index("Never put a gap in a record key")
        rule = branch.index(RULE_HEAD)
        sample = branch.index("**Record the intended band per source**")
        self.assertLess(key, rule, "the rule belongs beside the record-key block (#343)")
        self.assertLess(rule, sample)

    def test_it_cites_the_invariant_it_extends_at_its_own_line(self):
        self.assertIn(RULE_HEAD + " (INV-239)", synthesized_branch())


class TheRuleSaysWhatIsUniqueAndWhatIsNot(unittest.TestCase):
    """Criteria 1-3 and 6, each against the rule paragraph and against its absence."""

    CASES = (
        ("email, phone and identifier numbers, people and organizations",
         covers_the_identifier_features),
        ("deliberate sharing recorded under quality_intent.shared_features",
         declares_sharing_under_quality_intent),
        ("a shared_features entry excuses only the shares its reason describes",
         scopes_each_entry_to_its_reason),
        ("records of the same entity keep its features", keeps_same_entity_features),
        ("shared names allowed, as hard negatives", allows_shared_names_as_hard_negatives),
        ("address and date of birth may repeat", leaves_address_and_dob_uncovered),
        ("the name-plus-small-number anti-pattern", names_the_anti_pattern),
    )

    def test_each_clause_is_in_the_rule(self):
        rule = paragraph(synthesized_branch(), RULE_HEAD)
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(holds(rule), "the identifier rule lost: %s" % name)

    def test_negative_control_each_clause_fails_without_the_rule(self):
        stripped = without(synthesized_branch(), RULE_HEAD)
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertFalse(
                    holds(stripped),
                    "predicate for %r matched the branch with the rule removed, so it is "
                    "checking surrounding text, not the rule" % name)


class TheSelfCheckRegeneratesNeverPatches(unittest.TestCase):
    """Criterion 5 — folded into the band self-check, with its discipline."""

    def test_it_is_a_hard_rule_inside_the_band_self_check(self):
        branch = synthesized_branch()
        band = branch.index("⛔ **Verify the generated data against the band before this module")
        check = branch.index(SELF_CHECK_HEAD)
        offpattern = branch.index("**off-pattern values in at least one field per source**")
        self.assertLess(band, check)
        self.assertLess(check, offpattern, "the collision count belongs in the band self-check")
        self.assertIn(SELF_CHECK_HEAD + " (INV-239)**", branch)

    def test_it_counts_and_regenerates(self):
        self.assertTrue(requires_the_collision_self_check(synthesized_branch()))

    def test_negative_control_it_fails_without_the_self_check(self):
        branch = synthesized_branch()
        i = branch.index(SELF_CHECK_HEAD)
        j = branch.index("afterward.", i) + len("afterward.")
        self.assertFalse(requires_the_collision_self_check(branch[:i] + branch[j:]))

    def test_the_band_self_check_is_unchanged(self):
        branch = synthesized_branch()
        self.assertRegex(branch, r"\*\*widen the gaps and regenerate\*\* — never adjust a score")
        self.assertRegex(branch, r"correcting the data before anything scores it is this "
                                 r"generator's own job")


class TheSampleShowsDeliberateSharing(unittest.TestCase):
    """Criterion 4."""

    def test_the_sample_quality_intent_shows_a_shared_feature_with_a_reason(self):
        self.assertTrue(shows_a_shared_feature_with_reason(sample_yaml()))

    def test_negative_control_a_sample_without_it_fails(self):
        y = sample_yaml()
        self.assertFalse(shows_a_shared_feature_with_reason(
            re.sub(r"(?m)^\s+shared_features:.*\n(?:\s+(?:- feature|reason):.*\n)+", "", y)))

    def test_negative_control_a_reasonless_entry_fails(self):
        y = re.sub(r'(?m)^(\s+)reason: "[^"]+"\n', "", sample_yaml())
        self.assertFalse(shows_a_shared_feature_with_reason(y))

    def test_negative_control_shared_features_outside_quality_intent_fails(self):
        y = ("- name: X\n  provenance: synthesized\n  shared_features:\n"
             "    - feature: phone\n      reason: \"household\"\n")
        self.assertFalse(shows_a_shared_feature_with_reason(y))

    def test_the_rest_of_the_sample_is_unchanged(self):
        y = sample_yaml()
        self.assertIn('target_band: "70-79"', y)
        self.assertIn("measured_score: 78.0", y)


class TheRecordKeyRuleIsUntouched(unittest.TestCase):

    def test_the_key_rule_still_reads_as_before(self):
        branch = synthesized_branch()
        self.assertIn("`DATA_SOURCE` and `RECORD_ID` stay present and unique", branch)
        self.assertIn("the duplication is in the entity, never in the key.", branch)


class ItStaysLanguageAgnostic(unittest.TestCase):

    def test_the_rule_and_its_check_name_no_language_or_tool(self):
        branch = synthesized_branch()
        text = paragraph(branch, RULE_HEAD) + paragraph(branch, SELF_CHECK_HEAD)
        self.assertNotRegex(
            text, r"(?i)\b(?:python|java|csharp|rust|typescript|node|pandas|faker|bash|"
                  r"powershell|uuid4)\b|\.py\b",
            "the rule must state the property, not an implementation (language-agnostic, per INVARIANTS.md)")


if __name__ == "__main__":
    unittest.main()
