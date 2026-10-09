"""A generated scenario's data supports every success criterion its business case states.

Filed by the graduation retrospective (`Source: self-observed (assistant retrospective)`):
a generated Customer 360 scenario promised households and related parties in its success
criteria, and nothing connected those criteria to what Data collection generated. The data held
no different people related through shared features, so Query, Visualize and Discover's step 4d
fell back to "no 2+ degree pair" and reported it as a property of the Bootcamper's data.

The fix, as a conditional entry in Module 4 Step 2's existing list of what a synthesized
scenario must carry:

1. **The criterion-coverage lead** (Module 4): the generated data supports every success
   criterion; walk `docs/business_problem.md` first; a criterion Module 4 cannot generate is
   named in the generation summary, never invented for or dropped. It leads the list.
2. **The conditional entry** (Module 4): when a criterion names households or related parties,
   households (2–4 different people sharing a surname and a street address, optional landline,
   distinct first names and dates of birth) and chains (one person linking two households by a
   shared phone, 2 degrees), at least 100 and 5 on the default ~10,000-record scenario; every
   shared phone declared under `quality_intent.shared_features`; households kept outside the
   name-sharing budget (#458) because they share a surname, not a name.
3. **The self-check** (Module 4): in the band self-check's pass, criterion coverage, with the
   household and chain counts written to `relationship_intent` by the self-check and a
   regeneration on a shortfall before anything loads or scores. The collection-return bullet
   re-measures them.
4. **The record**: the sample `quality_intent` carries `relationship_intent` with intended and
   measured counts, and a declared phone share for the chain.
5. **Module 1 Step 4a**: each generated success criterion is one the generated data can
   demonstrate.
6. **Module 7 `phase2b-discover.md`**: on a synthesized source whose `quality_intent` carries
   `relationship_intent`, **or** whose scenario's success criteria in `docs/business_problem.md`
   name households or related parties (a scenario generated before the key existed), step 4d's
   "no 2+ degree pair" fallback and step 7's "no relationships" fallback are reported as a
   bootcamp generation defect, pointing to `/bootcamp-feedback`; the CORD and own-data wording is
   unchanged. The criteria trigger was carried over from the losing race approach by the judging
   (issue comment 3) and has its own negative control against the record-only trigger.
7. **Every reader is scoped** (INV-246): each shipped Markdown block naming
   `relationship_intent` outside Module 4 names `provenance: synthesized` too.

Each predicate is negative-controlled against the text with its clause removed. Phrase checks
run on whitespace-collapsed text or on ``_wrapped_text.blocks`` (INV-346), so a wrapped phrase
still matches.

Extends **INV-239** (generated data carries the flaws it should and none it should not); the
amendment is drafted, not applied, in the `specs/IMPLEMENTED.md` entry for #459.

Source issue: #459.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wrapped_text import blocks  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
COLLECTION = SKILLS / "module-04-data-collection" / "SKILL.md"
DISCOVERY = SKILLS / "module-01-business-problem" / "phase1-discovery.md"
DISCOVER = SKILLS / "module-07-query-visualize-discover" / "phase2b-discover.md"

LEAD_HEAD = "⛔ **Generate against the success criteria, too (INV-239).**"
ENTRY_HEAD = ("- ⛔ **(INV-239) households and chains, when a success criterion names households "
              "or related parties**")
CHECK_HEAD = "⛔ **In the same pass, check criterion coverage (INV-239)**"
NAME_CHECK_HEAD = "⛔ **In the same pass, count name sharing (INV-239)**"
RETURN_HEAD = "⛔ **(INV-239) Both self-checks in this step apply to the regeneration:**"
BUDGET_HEAD = "⛔ **Keep name sharing inside one budget (INV-239).**"
M7_HEAD = ("⛔ **(INV-239) On a generated scenario that promised households, this fallback is a "
           "bootcamp defect.**")
M7_STEP7_HEAD = "- ⛔ **(INV-239) On a generated scenario that promised households**"
LANGUAGE = (r"(?i)\b(?:python|java|csharp|rust|typescript|node|pandas|faker|bash|powershell|"
            r"uuid4)\b|\.py\b")


def squash(text):
    return re.sub(r"\s+", " ", text)


def collection():
    return squash(COLLECTION.read_text(encoding="utf-8"))


def synthesized_branch():
    """Step 2's `provenance: synthesized` bullet — the scope #343's and #458's guards read."""
    body = collection()
    start = body.index("**`provenance: synthesized`**")
    end = body.index("⚠️ **Both are bootcamp-generated", start)
    return body[start:end]


def lead(branch):
    i = branch.index(LEAD_HEAD)
    return branch[i:branch.index("- **missing values in non-key fields**", i)]


def entry(branch):
    i = branch.index(ENTRY_HEAD)
    return branch[i:branch.index("**State the intent when you generate", i)]


def self_check(branch):
    i = branch.index(CHECK_HEAD)
    return branch[i:branch.index("- **off-pattern values", i)]


def return_bullet():
    body = collection()
    i = body.index(RETURN_HEAD)
    return body[i:body.index("⛔ **(INV-243) Repoint", i)]


def cut(text, part):
    """``text`` with ``part`` removed — a negative control's input."""
    assert part in text
    return text.replace(part, "")


def sample_yaml():
    """The `quality_intent` sample for MERIDIAN_CRM, raw (indentation kept)."""
    text = COLLECTION.read_text(encoding="utf-8")
    i = text.index("- name: MERIDIAN_CRM")
    return text[i:text.index("```", i)]


def step_4a():
    body = squash(DISCOVERY.read_text(encoding="utf-8"))
    i = body.index("### 4a. Business Case Offer")
    return body[i:body.index("### 4b.", i)]


def discover():
    return squash(DISCOVER.read_text(encoding="utf-8"))


def m7_paragraph(text):
    i = text.index(M7_HEAD)
    return text[i:text.index("Show the shortest path of relationships", i)]


def m7_step7_bullet(text):
    i = text.index(M7_STEP7_HEAD)
    return text[i:text.index("- State: \"Your data doesn't contain", i)]


# --- Predicates on the criterion-coverage lead. ---

def supports_every_criterion(t):
    return bool(re.search(r"(?i)generated data must support every success criterion the "
                          r"generated business case states", t))


def walks_the_criteria_first(t):
    return bool(re.search(r"(?i)Walk the criteria in `docs/business_problem\.md` before "
                          r"generating", t))


def names_an_ungeneratable_criterion(t):
    return bool(re.search(r"(?i)does not know how to generate", t)
                and re.search(r"(?i)\*\*named in the generation summary\*\*", t)
                and re.search(r"(?i)never invent data for it, and never drop it silently", t))


def leads_into_the_conditional_entry(t):
    return bool(re.search(r"(?i)the last of them only when a criterion asks for it:", t))


# --- Predicates on the conditional entry. ---

def is_conditional(t):
    return bool(re.search(r"(?i)when a success criterion names households or related parties", t)
                and re.search(r"(?i)when no criterion does, generate neither and omit "
                              r"`relationship_intent`", t))


def specifies_households(t):
    return bool(re.search(r"(?i)\*\*households:\*\* 2–4 \*different\* invented people sharing a "
                          r"surname and a street address", t)
                and re.search(r"(?i)optionally also a home landline", t)
                and re.search(r"(?i)each with a distinct first name and date of birth", t))


def specifies_chains(t):
    return bool(re.search(r"(?i)\*\*chains:\*\* a person who belongs to one household and also "
                          r"shares a phone with a member of a second household", t)
                and re.search(r"(?i)connect only through that person", t)
                and re.search(r"(?i)2 degrees apart", t)
                and re.search(r"(?i)step 4d", t))


def sets_the_minimums(t):
    return bool(re.search(r"(?i)\*\*at least 100 households and at least 5 chains\*\* on the "
                          r"default ~10,000-record scenario", t))


def declares_every_shared_phone(t):
    return bool(re.search(r"(?i)\*\*Declare every shared phone under "
                          r"`quality_intent\.shared_features` with its reason\*\*", t)
                and re.search(r"(?i)household landline and the chain's phone as separate "
                              r"entries", t)
                and re.search(r"(?i)identifier-collision self-check above counts it", t))


def stays_outside_the_name_budget(t):
    return bool(re.search(r"(?i)\*\*A household shares a surname, not a name\*\*", t)
                and re.search(r"\]\(#name-sharing-budget\)", t)
                and re.search(r"(?i)add nothing to `measured_entities`", t)
                and re.search(r"(?i)never hard-negative pairs toward `declared_pairs`", t))


def excludes_a_suffix_only_pair(t):
    return bool(re.search(r"(?i)`Sr\.`/`Jr\.` normalize to one name", t)
                and re.search(r"(?i)not a household here and would count against that budget",
                              t))


def records_the_intent(t):
    return bool(re.search(r"(?i)Record the intended counts as `relationship_intent` in the "
                          r"source's `quality_intent`", t))


# --- Predicates on the self-check. ---

def checks_coverage(t):
    return bool(re.search(r"(?i)every success criterion walked above has generated records "
                          r"behind it, or is named in the generation summary", t))


def writes_the_measured_counts(t):
    return bool(re.search(r"(?i)`measured_households` and `measured_chains`", t)
                and re.search(r"(?i)the self-check writes both, never by hand", t))


def regenerates_on_a_shortfall(t):
    return bool(re.search(r"(?i)\*\*Regenerate before anything loads or scores\*\* when either "
                          r"count falls short of its intended figure", t)
                and re.search(r"(?i)never patch the recorded counts", t))


def runs_every_generation(t):
    return bool(re.search(r"(?i)this runs on every generation and rewrites both measured counts",
                          t))


# --- Predicates on Module 7. ---

def m7_conditions_on_the_record(t):
    return bool(re.search(r"(?i)records `provenance: synthesized` and its `quality_intent` "
                          r"carries a `relationship_intent`", t))


def m7_reports_a_bootcamp_defect(t):
    return bool(re.search(r"(?i)bootcamp's generated data is missing what its scenario promised, "
                          r"not that the Bootcamper's data lacks it", t)
                and re.search(r"(?i)defect in the data the bootcamp generated, not anything about "
                              r"your data", t))


def m7_points_to_feedback(t):
    return "`/bootcamp-feedback`" in t


def m7_covers_both_fallbacks(t):
    return bool(re.search(r"(?i)Reaching this fallback, or step 7's", t))


def m7_conditions_on_the_criteria(t):
    """The widened trigger: success criteria naming households fire it with no record, too."""
    return bool(re.search(r"(?i), or when a loaded source records `provenance: synthesized` and "
                          r"the scenario's success criteria in `docs/business_problem.md` name "
                          r"households or related parties", t)
                and re.search(r"(?i)covers a scenario generated before `relationship_intent` "
                              r"existed", t))


def m7_keeps_other_wording(t):
    return bool(re.search(r"(?i)On a CORD source, the Bootcamper's own data, or a generated "
                          r"scenario with no `relationship_intent` and no success criterion naming "
                          r"households or related parties, the fallback's wording stands as "
                          r"written", t))


def step7_reports_a_defect(t):
    return bool(re.search(r"(?i)generated data is missing the relationships its scenario "
                          r"promised", t)
                and re.search(r"(?i)bootcamp defect rather than a property of the Bootcamper's "
                              r"data", t)
                and "`/bootcamp-feedback`" in t
                and re.search(r"(?i)the condition in step 4's generated-scenario paragraph", t))


def step7_covers_the_criteria(t):
    return bool(re.search(r"(?i)including a scenario whose success criteria name households or "
                          r"related parties", t))


# The race's winning patch (b) as first written: the record-only trigger the judging widened.
# Kept verbatim (squashed) as the negative control for the widened trigger.
RECORD_ONLY_PARAGRAPH = squash("""
   ⛔ **(INV-239) On a generated scenario that promised households, this fallback is a bootcamp
   defect.** The scenario promised them when a loaded source's entry in `config/data_sources.yaml`
   records `provenance: synthesized` and its `quality_intent` carries a `relationship_intent`: Data
   collection then generated households and the chains between them, which give a path of 2 or more
   degrees. Reaching this fallback, or step 7's, on such a scenario means the bootcamp's generated
   data is missing what its scenario promised, not that the Bootcamper's data lacks it. Say so
   plainly with the fallback, and suggest `/bootcamp-feedback`: "This scenario promised households
   and related people, so there should be a path of 2 or more degrees here. It's missing because of
   a defect in the data the bootcamp generated, not anything about your data. You can report it with
   `/bootcamp-feedback`." On a CORD source, the Bootcamper's own data, or a generated scenario with
   no `relationship_intent`, the fallback's wording stands as written.
""")
RECORD_ONLY_STEP7_BULLET = squash("""
   - ⛔ **(INV-239) On a generated scenario that promised households** (the condition in step 4's
     generated-scenario paragraph), first say that the bootcamp's generated data is missing the
     relationships its scenario promised, that this is a bootcamp defect rather than a property of
     the Bootcamper's data, and suggest `/bootcamp-feedback`. Then continue below.
""")


# --- The sample, read without a YAML library. ---

def relationship_intent(yaml_text):
    """{key: (value, comment)} for `relationship_intent:` nested under `quality_intent:`."""
    m = re.search(r"(?m)^(\s*)quality_intent:\n((?:\1\s+.*\n?)+)", yaml_text)
    if not m:
        return None
    qi = m.group(2)
    r = re.search(r"(?m)^(\s+)relationship_intent:.*\n((?:\1\s+.*\n?)+)", qi)
    if not r:
        return None
    out = {}
    for line in r.group(2).splitlines():
        kv = re.match(r"\s+(\w+):\s*([^#]*?)\s*(?:#\s*(.*))?$", line)
        if kv:
            out[kv.group(1)] = (kv.group(2), kv.group(3) or "")
    return out


def sample_problems(yaml_text):
    ri = relationship_intent(yaml_text)
    if ri is None:
        return ["no relationship_intent under quality_intent"]
    problems = []
    keys = ("criterion", "households", "chains", "measured_households", "measured_chains")
    for k in keys:
        if k not in ri:
            problems.append("missing " + k)
    if problems:
        return problems
    if not re.fullmatch(r'"[^"]+"', ri["criterion"][0]):
        problems.append("criterion is not a quoted, non-empty string")
    h, c = int(ri["households"][0]), int(ri["chains"][0])
    mh, mc = int(ri["measured_households"][0]), int(ri["measured_chains"][0])
    if h < 100:
        problems.append("households below the minimum of 100")
    if c < 5:
        problems.append("chains below the minimum of 5")
    if mh < h or mc < c:
        problems.append("a measured count falls short of its intended figure")
    for k in ("measured_households", "measured_chains"):
        if "written by the self-check, never by hand" not in ri[k][1]:
            problems.append(k + " is not marked as written by the self-check")
    phones = re.findall(r'(?m)^\s+- feature: phone\n\s+reason: "([^"]+)"', yaml_text)
    if not any(re.search(r"(?i)chain", r) for r in phones):
        problems.append("no declared phone share for a chain")
    return problems


class TheCriterionCoverageLeadsTheList(unittest.TestCase):

    CASES = (
        ("every success criterion", supports_every_criterion),
        ("walk business_problem.md first", walks_the_criteria_first),
        ("an ungeneratable criterion is named, never invented or dropped",
         names_an_ungeneratable_criterion),
        ("it leads into the conditional entry", leads_into_the_conditional_entry),
    )

    def test_it_leads_the_list_after_the_quality_gaps_rule(self):
        branch = synthesized_branch()
        gaps = branch.index("⛔ **Generate realistic quality gaps too, not only structural "
                            "complexity (INV-239).**")
        lead_at = branch.index(LEAD_HEAD)
        first_entry = branch.index("- **missing values in non-key fields**")
        self.assertLess(gaps, lead_at)
        self.assertLess(lead_at, first_entry)

    def test_each_clause_is_in_the_lead(self):
        text = lead(synthesized_branch())
        for name, predicate in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(predicate(text))

    def test_negative_control_each_clause_fails_without_the_lead(self):
        branch = synthesized_branch()
        stripped = cut(branch, lead(branch))
        for name, predicate in self.CASES:
            with self.subTest(clause=name):
                self.assertFalse(predicate(stripped))


class TheHouseholdEntryIsConditionalAndComplete(unittest.TestCase):

    CASES = (
        ("conditional on a criterion", is_conditional),
        ("households", specifies_households),
        ("chains", specifies_chains),
        ("minimums", sets_the_minimums),
        ("every shared phone declared", declares_every_shared_phone),
        ("outside the name-sharing budget", stays_outside_the_name_budget),
        ("a Sr./Jr. pair is not a household", excludes_a_suffix_only_pair),
        ("recorded as relationship_intent", records_the_intent),
    )

    def test_it_is_the_last_entry_of_the_list(self):
        branch = synthesized_branch()
        structural = branch.index("the structural complexity above, unchanged — the two are "
                                  "additive, not alternatives.")
        entry_at = branch.index(ENTRY_HEAD)
        intent = branch.index("**State the intent when you generate")
        self.assertLess(structural, entry_at)
        self.assertLess(entry_at, intent)

    def test_each_clause_is_in_the_entry(self):
        text = entry(synthesized_branch())
        for name, predicate in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(predicate(text))

    def test_negative_control_each_clause_fails_without_the_entry(self):
        branch = synthesized_branch()
        stripped = cut(branch, entry(branch))
        for name, predicate in self.CASES:
            with self.subTest(clause=name):
                self.assertFalse(predicate(stripped))

    def test_the_budget_still_ignores_suffixes(self):
        """The Sr./Jr. clause is true only while the budget's normalization drops suffixes; if
        that rule changes, this entry must be revisited with it."""
        branch = synthesized_branch()
        i = branch.index(BUDGET_HEAD)
        budget = branch[i:branch.index("**Record the intended band per source**", i)]
        self.assertRegex(budget, r"first name plus last name, after lowercasing, trimming, "
                                 r"collapsing whitespace and stripping punctuation, ignoring "
                                 r"middle names and suffixes")


class TheSelfCheckMeasuresAndRegenerates(unittest.TestCase):

    CASES = (
        ("checks coverage", checks_coverage),
        ("writes measured_households and measured_chains", writes_the_measured_counts),
        ("regenerates on a shortfall, never patches", regenerates_on_a_shortfall),
        ("runs on every generation", runs_every_generation),
    )

    def test_it_follows_the_name_sharing_check_inside_the_band_self_check(self):
        branch = synthesized_branch()
        band = branch.index("⛔ **Verify the generated data against the band before this module")
        names = branch.index(NAME_CHECK_HEAD)
        check = branch.index(CHECK_HEAD)
        offpattern = branch.index("**off-pattern values in at least one field per source**")
        self.assertLess(band, names)
        self.assertLess(names, check)
        self.assertLess(check, offpattern)

    def test_each_clause_is_in_the_self_check(self):
        text = self_check(synthesized_branch())
        for name, predicate in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(predicate(text))

    def test_negative_control_each_clause_fails_without_the_self_check(self):
        branch = synthesized_branch()
        stripped = cut(branch, self_check(branch))
        for name, predicate in self.CASES:
            with self.subTest(clause=name):
                self.assertFalse(predicate(stripped))

    def test_the_collection_return_bullet_re_measures(self):
        self.assertRegex(return_bullet(), r"Where the source records a `relationship_intent`, "
                                          r"re-measure its households and chains in the same pass")

    def test_negative_control_the_458_return_bullet_fails(self):
        old = ("⛔ **(INV-239) Both self-checks in this step apply to the regeneration:** verify it "
               "against the band, and count collisions in the same pass: identifier collisions "
               "and name sharing ([the name-sharing budget](#name-sharing-budget)).")
        self.assertNotRegex(old, r"re-measure its households and chains")


class TheSampleRecordsTheIntent(unittest.TestCase):

    def test_the_sample_carries_relationship_intent(self):
        self.assertEqual(sample_problems(sample_yaml()), [])

    def test_negative_control_without_it(self):
        y = re.sub(r"(?m)^\s+relationship_intent:.*\n(?:\s+(?:criterion|households|chains|"
                   r"measured_households|measured_chains):.*\n)+", "", sample_yaml())
        self.assertNotEqual(sample_problems(y), [])

    def test_negative_control_below_the_minimums(self):
        y = re.sub(r"(?m)^(\s+households:)\s*\d+", r"\1 50", sample_yaml())
        self.assertIn("households below the minimum of 100", sample_problems(y))

    def test_negative_control_a_shortfall_recorded_as_measured(self):
        y = re.sub(r"(?m)^(\s+measured_chains:)\s*\d+", r"\1 2", sample_yaml())
        self.assertIn("a measured count falls short of its intended figure", sample_problems(y))

    def test_negative_control_a_hand_written_measured_count(self):
        y = re.sub(r"(?m)^(\s+measured_households:\s*\d+).*$", r"\1", sample_yaml())
        self.assertIn("measured_households is not marked as written by the self-check",
                      sample_problems(y))

    def test_negative_control_outside_quality_intent(self):
        y = ("- name: X\n  provenance: synthesized\n  relationship_intent:\n"
             "    households: 120\n")
        self.assertNotEqual(sample_problems(y), [])

    def test_negative_control_no_chain_phone_declared(self):
        y = re.sub(r'(?m)^\s+- feature: phone\n\s+reason: "chain[^"]*"\n', "", sample_yaml())
        self.assertIn("no declared phone share for a chain", sample_problems(y))

    def test_the_rest_of_the_sample_is_unchanged(self):
        y = sample_yaml()
        self.assertIn('target_band: "70-79"', y)
        self.assertIn("measured_score: 78.0", y)
        self.assertIn('reason: "household landline shared by the two adults at one address"', y)


class Module1AsksForDemonstrableCriteria(unittest.TestCase):

    SENTENCE = ("Write each success criterion as one the generated data can demonstrate, because "
                "Data collection generates the data against these criteria.")

    def test_step_4a_states_it_in_the_accepted_branch(self):
        text = step_4a()
        accepted = text[text.index("**Accepted:**"):text.index("**Declined:**")]
        self.assertIn(self.SENTENCE, accepted)

    def test_negative_control_without_it(self):
        self.assertNotIn(self.SENTENCE, cut(step_4a(), self.SENTENCE))

    def test_no_new_field_is_added(self):
        self.assertNotIn("relationship_intent", step_4a())


class Module7ReportsAGenerationDefect(unittest.TestCase):

    CASES = (
        ("conditioned on synthesized + relationship_intent", m7_conditions_on_the_record),
        ("or on success criteria naming households", m7_conditions_on_the_criteria),
        ("a bootcamp defect, not the Bootcamper's data", m7_reports_a_bootcamp_defect),
        ("points to /bootcamp-feedback", m7_points_to_feedback),
        ("covers step 4d's and step 7's fallbacks", m7_covers_both_fallbacks),
        ("CORD and own-data wording unchanged", m7_keeps_other_wording),
    )

    def test_it_follows_the_step_4d_fallback(self):
        text = discover()
        fallback = text.index("**If no 2+ degree pair is found after three hubs,**")
        self.assertLess(fallback, text.index(M7_HEAD))
        self.assertLess(text.index(M7_HEAD), text.index("Show the shortest path of relationships"))

    def test_each_clause_is_in_the_paragraph(self):
        text = m7_paragraph(discover())
        for name, predicate in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(predicate(text))

    def test_negative_control_each_clause_fails_without_the_paragraph(self):
        text = discover()
        stripped = cut(text, m7_paragraph(text))
        for name, predicate in self.CASES:
            if predicate is m7_points_to_feedback:
                continue  # step 7's bullet names it too; its own control is below
            with self.subTest(clause=name):
                self.assertFalse(predicate(stripped))

    def test_step_7_reports_it_before_its_explanation(self):
        text = discover()
        self.assertTrue(step7_reports_a_defect(m7_step7_bullet(text)))
        graceful = text.index("7. **Graceful fallback (no relationships in data):**")
        self.assertLess(graceful, text.index(M7_STEP7_HEAD))

    def test_negative_control_step_7_without_the_bullet(self):
        text = discover()
        self.assertFalse(step7_reports_a_defect(cut(text, m7_step7_bullet(text))))

    def test_step_7_covers_the_criteria_trigger(self):
        text = discover()
        self.assertTrue(step7_covers_the_criteria(m7_step7_bullet(text)))
        self.assertFalse(step7_covers_the_criteria(cut(text, m7_step7_bullet(text))))

    def test_negative_control_the_record_only_trigger_fails(self):
        """The judging widened b's trigger: the record-only paragraph and bullet must fail the
        criteria clauses (and the record-only exemption must fail the unchanged-wording clause,
        because it would exempt a criteria-only scenario), while still passing the clauses
        that did not change."""
        self.assertTrue(m7_conditions_on_the_record(RECORD_ONLY_PARAGRAPH))
        self.assertTrue(m7_reports_a_bootcamp_defect(RECORD_ONLY_PARAGRAPH))
        self.assertFalse(m7_conditions_on_the_criteria(RECORD_ONLY_PARAGRAPH))
        self.assertFalse(m7_keeps_other_wording(RECORD_ONLY_PARAGRAPH))
        self.assertTrue(step7_reports_a_defect(RECORD_ONLY_STEP7_BULLET))
        self.assertFalse(step7_covers_the_criteria(RECORD_ONLY_STEP7_BULLET))

    def test_the_existing_fallback_wording_is_unchanged(self):
        text = discover()
        self.assertIn("\"In your data, every pair I checked is directly connected, so there's no "
                      "path of 2 or more degrees to show. Here is `find_path` on a direct "
                      "connection instead.\"", text)
        self.assertIn("State: \"Your data doesn't contain disclosed relationships, so I'll explain "
                      "what this would look like with connected data.\"", text)
        self.assertIn("{\"status\": \"skipped\", \"reason\": \"no_relationships\"}", text)


def unscoped_readers(rel, text):
    """`file:line` for each prose block naming `relationship_intent` without naming the
    `provenance: synthesized` it applies to. Fenced code is skipped (the sample is Module 4's)."""
    bad = []
    for block in blocks(text):
        if block and re.match(r"^[ \t]*(`{3,}|~{3,})", block[0][1]):
            continue
        flat = squash(" ".join(line for _, line in block))
        if "`relationship_intent`" in flat and "provenance: synthesized" not in flat:
            bad.append("%s:%d" % (rel, block[0][0]))
    return bad


class EveryReaderIsScopedToASynthesizedSource(unittest.TestCase):
    """INV-246: readers are found by scanning. Module 4 is the rule's home and is exempt: the
    whole branch is the `provenance: synthesized` branch."""

    def test_every_reader_outside_module_4_names_the_provenance(self):
        bad, readers = [], 0
        for path in sorted(PLUGIN.rglob("*.md")):
            if path == COLLECTION:
                continue
            text = path.read_text(encoding="utf-8")
            if "relationship_intent" in text:
                readers += 1
            bad += unscoped_readers(path.relative_to(REPO_ROOT), text)
        self.assertEqual(bad, [], "a block reads `relationship_intent` without scoping it to "
                                  "`provenance: synthesized`")
        self.assertGreaterEqual(readers, 1, "the scan found no reader; is it vacuous?")

    def test_negative_control_an_unscoped_reader_is_caught(self):
        text = ("Intro.\n\nWhen the source carries a `relationship_intent`, report a\n"
                "defect.\n\nOutro.\n")
        self.assertEqual(unscoped_readers("x.md", text), ["x.md:3"])

    def test_negative_control_a_wrapped_scope_is_accepted(self):
        text = ("Intro.\n\nWhen a source records `provenance:\nsynthesized` and carries a "
                "`relationship_intent`, report it.\n")
        self.assertEqual(unscoped_readers("x.md", text), [])


class ItStaysLanguageAgnostic(unittest.TestCase):

    def test_the_new_text_names_no_language_or_tool(self):
        branch = synthesized_branch()
        text = (lead(branch) + entry(branch) + self_check(branch) + m7_paragraph(discover())
                + m7_step7_bullet(discover()))
        self.assertNotRegex(text, LANGUAGE, "the rule must state the property, not an "
                                            "implementation (language-agnostic, per INVARIANTS.md)")


if __name__ == "__main__":
    unittest.main()
