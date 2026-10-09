"""A generated scenario's name sharing stays inside one declared, measured budget.

#343 made shared names between distinct invented entities the intended hard negatives and set
no rate. Observed on a 2026-10-05 run (plugin 0.6.0): about 5,500 people drawn from 129 first
names and 135 last names left 76.5% of full names unique, and after loading 32.7% of entities
had a possible match, every one on `+NAME` alone. Resolution was clean (precision 100%, no false
merges), yet Query, Visualize and Discover's step 3b showed the Poor band (> 15%) by
construction of the data, and every current rule was met.

The fix is a sibling of #343's identifier rule in Module 4 Step 2's `provenance: synthesized`
branch, under its own anchor (`#name-sharing-budget`), with its own self-check beside the
identifier-collision self-check, and a top-level `scenario_intent.name_collisions` block in
`config/data_sources.yaml`. Module 7 step 3b reports the measured figure on an all-synthesized
scenario that carries the block, and keeps today's wording otherwise.

What this file pins:

1. **The budget** (Module 4): below 5% of invented entities, deliberate and chance together; a
   declared minimum of at least one hard-negative pair inside it; the name pool sized to the
   population; the person and organization normalization rule; the lower-bound caveat; the
   entity as the unit; the anti-pattern with the 2026-10-05 figures.
2. **The record**: the YAML sample puts `scenario_intent` at the top level beside `version`
   and `sources:`, with `declared_pairs` >= 1, a `reason`, and the two measured fields marked
   as written by the self-check; the Data Source Registry schema note names the block.
3. **The self-check**: counts name-sharing entities and pairs in the band self-check's pass,
   writes the measured fields, regenerates before anything loads or scores on
   `measured_share` >= 0.05 or fewer pairs than `declared_pairs`, never patches afterwards, and
   applies to a regeneration after Module 5's gate (the collection-return bullet says so too).
4. **Module 7 step 3b**: bands on the raw possible-match rate, unchanged thresholds; reports
   `measured_entities` beside the possible-match count on a Marginal or Poor verdict only when
   every loaded source is `synthesized` and the block is present; cites the figure under outcome
   2 when it is more than half of the entities with a possible match; keeps "the plugin built
   that pool" otherwise. Both example sentences keep the two units apart: `measured_entities`
   counts invented entities, not resolved entities with a possible match, so neither sentence
   may read it as "N of the M entities with a possible match".
5. **Every reader links the rule** (INV-246, INV-300): each prose block in shipped Markdown
   naming `scenario_intent` or `measured_share`, outside the rule itself, links the anchor.

Each predicate is negative-controlled against the text with its clause removed. Phrase checks
run on whitespace-collapsed text or on ``_wrapped_text.blocks`` (INV-346), so a wrapped phrase
still matches.

Extends **INV-239** (generated data carries the flaws it should and none it should not); the
amendment is drafted, not applied, in the `specs/IMPLEMENTED.md` entry for #458.

Source issue: #458.

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
COLLECTION = PLUGIN / "skills" / "module-04-data-collection" / "SKILL.md"
QUERY = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"

ANCHOR = '<a id="name-sharing-budget"></a>'
RULE_HEAD = "⛔ **Keep name sharing inside one budget (INV-239).**"
IDENTIFIER_HEAD = "⛔ **Give each invented entity its own identifiers (INV-239).**"
SELF_CHECK_HEAD = "⛔ **In the same pass, count name sharing (INV-239)**"
ID_SELF_CHECK_HEAD = "⛔ **In the same pass, count identifier collisions (INV-239)**"
RETURN_HEAD = "⛔ **(INV-239) Both self-checks in this step apply to the regeneration:**"
M7_ANCHOR = '<a id="measured-name-sharing"></a>'
M7_HEAD = "⛔ **(INV-239, INV-264) On a generated scenario, report the name sharing it measured.**"
OUTCOME_2_HEAD = "**Name-only collisions** in small or synthetic datasets"


def squash(text):
    return re.sub(r"\s+", " ", text)


def collection():
    return squash(COLLECTION.read_text(encoding="utf-8"))


def query():
    return squash(QUERY.read_text(encoding="utf-8"))


def synthesized_branch():
    """Step 2's `provenance: synthesized` bullet — the scope #343's guard reads too."""
    body = collection()
    start = body.index("**`provenance: synthesized`**")
    end = body.index("⚠️ **Both are bootcamp-generated", start)
    return body[start:end]


def rule(branch):
    """The budget rule, from its head through its anti-pattern note, to the band sample."""
    i = branch.index(RULE_HEAD)
    return branch[i:branch.index("**Record the intended band per source**", i)]


def self_check(branch):
    """The name-sharing self-check, to the next sibling bullet."""
    i = branch.index(SELF_CHECK_HEAD)
    return branch[i:branch.index("- **off-pattern values", i)]


def return_bullet():
    body = collection()
    i = body.index(RETURN_HEAD)
    return body[i:body.index("⛔ **(INV-243) Repoint", i)]


def registry_note():
    body = collection()
    i = body.index("`scenario_intent` (optional, top level")
    return body[i:body.index("> **Data File Validation:**", i)].replace(" > ", " ")


def m7_paragraph(text):
    i = text.index(M7_HEAD)
    return text[i:text.index("Based on the assessment", i)]


def outcome_2(text):
    i = text.index(OUTCOME_2_HEAD)
    return text[i:text.index("3. **Could not determine**", i)]


def sample_yaml():
    """The `scenario_intent` sample, raw (indentation kept), with its fence indent removed."""
    raw = COLLECTION.read_text(encoding="utf-8")
    i = raw.index(RULE_HEAD)
    start = raw.index("```yaml\n", i) + len("```yaml\n")
    block = raw[start:raw.index("```", start)]
    lines = block.splitlines()
    indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    return "\n".join(l[indent:] for l in lines) + "\n"


# --- Predicates on the budget rule. Each takes text and says whether the clause is there. ---

def states_the_budget(t):
    return bool(re.search(r"(?i)deliberate and chance together", t)
                and re.search(r"(?i)\*\*below 5% of all invented entities\*\*", t)
                and re.search(r"(?i)Acceptable\*\* possible-match threshold", t))


def declares_a_minimum_of_one_pair(t):
    return bool(re.search(r"(?i)declared \*\*minimum of at least one pair\*\* inside that budget",
                          t))


def sizes_the_pool_to_the_population(t):
    return bool(re.search(r"(?i)Size the name pool to the population", t)
                and re.search(r"(?i)enough first and last names, or a long-tailed surname "
                              r"distribution", t))


def normalizes_person_names(t):
    return bool(re.search(r"(?i)first name plus last name, after lowercasing, trimming, "
                          r"collapsing whitespace and stripping punctuation, ignoring middle "
                          r"names and suffixes", t))


def normalizes_organization_names(t):
    return bool(re.search(r"(?i)organization: the organization name, normalized the same way", t))


def states_the_lower_bound(t):
    return bool(re.search(r"(?i)Nicknames and typo variants", t)
                and re.search(r"(?i)are not counted, so the count is a \*\*lower bound\*\*", t))


def counts_entities_not_records(t):
    return bool(re.search(r"(?i)\*\*The unit is the entity", t)
                and re.search(r"(?i)deliberate name variants of one person\)? are never a "
                              r"collision", t))


def records_it_at_the_top_level(t):
    return bool(re.search(r"(?i)top-level `scenario_intent:` block in `config/data_sources.yaml`, "
                          r"beside `version` and `sources:`", t))


def names_the_anti_pattern_with_its_figures(t):
    return all(s in t for s in ("129 first names", "135 last names", "about 5,500 people",
                                "76.5%", "32.7%", "**Poor**"))


# --- Predicates on the self-check. ---

def counts_name_sharing(t):
    return bool(re.search(r"(?i)count name sharing", t)
                and re.search(r"(?i)the name-sharing pairs among them", t))


def writes_the_measured_fields(t):
    return bool(re.search(r"(?i)`scenario_intent\.name_collisions` as `measured_entities`", t)
                and re.search(r"(?i)as `measured_share`", t)
                and re.search(r"(?i)the self-check writes both, never by hand", t))


def regenerates_on_the_share(t):
    return bool(re.search(r"(?i)\*\*Regenerate names before anything loads or scores\*\* when "
                          r"`measured_share` is 0\.05 or more", t))


def regenerates_on_lost_hard_negatives(t):
    return bool(re.search(r"(?i)fewer name-sharing pairs exist than `declared_pairs`", t))


def never_patches(t):
    """Case-sensitive: the identifier self-check's "— never patch …" must not satisfy it."""
    return bool(re.search(r"Never patch the ground truth, the scores or the results afterward\.",
                          t))


def covers_a_regeneration_after_the_gate(t):
    return bool(re.search(r"(?i)a regeneration after Module 5's gate included", t)
                and re.search(r"(?i)rewrites both measured fields", t))


# --- Predicates on Module 7. ---

def bands_on_the_raw_rate(t):
    return bool(re.search(r"(?i)computed on the \*\*raw\*\* possible-match rate", t)
                and re.search(r"(?i)explains a band, never moves it", t))


def requires_all_synthesized_and_the_block(t):
    return bool(re.search(r"(?i)every loaded source's entry .{0,60}`provenance: synthesized`", t)
                and re.search(r"(?i)top-level `scenario_intent\.name_collisions` block", t))


def reports_the_measured_figure(t):
    return bool(re.search(r"(?i)on a \*\*Marginal\*\* or \*\*Poor\*\* verdict, report "
                          r"`measured_entities` beside the count of entities with a possible "
                          r"match", t)
                and re.search(r"(?i)a lower bound", t))


def falls_back_without_the_block(t):
    return bool(re.search(r"(?i)When the block is absent", t)
                and re.search(r"(?i)any loaded source is not `synthesized`", t)
                and re.search(r"(?i)report no measured figure", t))


def cites_the_figure_over_half(t):
    return bool(re.search(r"\[the measured name sharing\]\(#measured-name-sharing\)", t)
                and re.search(r"(?i)\*\*more than half\*\* of the entities with a possible match",
                              t)
                and re.search(r"(?i)cite that figure here instead of the pool", t))


SUBSET_WORDING = re.compile(r"(?i)(?:\d+|\[measured_entities\]) of the (?:\d+|\[n\]) entities "
                            r"with a possible match")


def keeps_the_units_apart_in_the_example(t):
    """Step 3b's example: the possible-match count and the measured figure, as separate units."""
    return bool(re.search(r"(?i)keeping the two units apart \(the measured figure counts invented "
                          r"entities, not resolved entities with a possible match\)", t)
                and re.search(r"\"\d+ entities have a possible match; Data collection measured \d+ "
                              r"invented entities that share a name with a different invented "
                              r"person — a lower bound, because nicknames and typo variants are "
                              r"not counted\.\"", t)
                and not SUBSET_WORDING.search(t))


def keeps_the_units_apart_in_outcome_2(t):
    """Outcome 2's citation: the same two units, kept apart, with the lower-bound caveat."""
    return bool(re.search(r"\"\[n\] entities have a possible match; Data collection measured, "
                          r"before loading, \[measured_entities\] invented entities that share a "
                          r"name with a different invented person — a lower bound, because "
                          r"nicknames and typo variants are not counted\.\"", t)
                and not SUBSET_WORDING.search(t))


def keeps_todays_wording(t):
    return bool(re.search(r"(?i)On a generated scenario the plugin built that pool\.", t)
                and re.search(r"(?i)Otherwise keep the sentence before this one", t))


# --- The YAML sample, read without a YAML library (INV-108). ---

def scenario_intent_keys(yaml_text):
    """{key: value} under a column-0 `scenario_intent:` → `name_collisions:`, else None."""
    m = re.search(r"(?m)^scenario_intent:\n((?:[ ]+.*\n)+)", yaml_text)
    if not m:
        return None
    body = m.group(1)
    nc = re.search(r"(?m)^(\s+)name_collisions:\n((?:\1\s+.*\n?)+)", body)
    if not nc:
        return None
    keys = {}
    for line in nc.group(2).splitlines():
        km = re.match(r"\s+(\w+):\s*(.*?)\s*$", line)
        if km:
            keys[km.group(1)] = km.group(2)
    return keys


def sample_is_valid(yaml_text):
    keys = scenario_intent_keys(yaml_text)
    if not keys:
        return False
    if set(keys) != {"declared_pairs", "reason", "measured_entities", "measured_share"}:
        return False
    pairs = re.match(r"(\d+)", keys["declared_pairs"])
    share = re.match(r"(0\.\d+)", keys["measured_share"])
    if not (pairs and int(pairs.group(1)) >= 1 and share and float(share.group(1)) < 0.05):
        return False
    if not re.match(r'"[^"]+"', keys["reason"]):
        return False
    return bool(re.search(r"(?m)^version: ", yaml_text) and re.search(r"(?m)^sources:", yaml_text))


class TheRuleSitsBesideTheIdentifierRule(unittest.TestCase):

    def test_it_is_an_anchored_hard_rule_in_the_synthesized_branch(self):
        branch = synthesized_branch()
        self.assertIn(ANCHOR + " " + RULE_HEAD, branch, "the anchor directly precedes the rule")
        self.assertEqual(COLLECTION.read_text(encoding="utf-8").count(ANCHOR), 1)

    def test_it_follows_the_identifier_rule_and_precedes_the_band_sample(self):
        branch = synthesized_branch()
        ident = branch.index(IDENTIFIER_HEAD)
        budget = branch.index(RULE_HEAD)
        sample = branch.index("**Record the intended band per source**")
        self.assertLess(ident, budget)
        self.assertLess(budget, sample)
        between = branch[ident:budget]
        self.assertNotIn("⛔", between[len(IDENTIFIER_HEAD):],
                         "no other hard rule sits between the identifier rule and its sibling")

    def test_names_may_repeat_points_to_it(self):
        branch = synthesized_branch()
        ident = branch[branch.index(IDENTIFIER_HEAD):branch.index(ANCHOR)]
        self.assertRegex(ident, r"\*\*Names may repeat\*\* across distinct entities — they are the "
                                r"intended \*\*hard negatives\*\*, held inside \[the name-sharing "
                                r"budget\]\(#name-sharing-budget\) below")

    def test_negative_control_an_unlinked_names_sentence_fails(self):
        branch = synthesized_branch().replace(
            ", held inside [the name-sharing budget](#name-sharing-budget) below", "")
        ident = branch[branch.index(IDENTIFIER_HEAD):branch.index(ANCHOR)]
        self.assertNotIn("](#name-sharing-budget)", ident)


class TheRuleStatesOneBudget(unittest.TestCase):
    """Scope items 1 and 2, each against the rule and against the branch without it."""

    CASES = (
        ("below 5% of invented entities, deliberate and chance together", states_the_budget),
        ("a declared minimum of at least one pair", declares_a_minimum_of_one_pair),
        ("the name pool sized to the population", sizes_the_pool_to_the_population),
        ("person normalization", normalizes_person_names),
        ("organization normalization", normalizes_organization_names),
        ("nicknames and typos uncounted, so a lower bound", states_the_lower_bound),
        ("the entity, not the record, is the unit", counts_entities_not_records),
        ("a top-level scenario_intent block", records_it_at_the_top_level),
        ("the anti-pattern with the 2026-10-05 figures", names_the_anti_pattern_with_its_figures),
    )

    def test_each_clause_is_in_the_rule(self):
        text = rule(synthesized_branch())
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(holds(text), "the name-sharing budget lost: %s" % name)

    def test_negative_control_each_clause_fails_without_the_rule(self):
        branch = synthesized_branch()
        stripped = branch.replace(rule(branch), "")
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertFalse(
                    holds(stripped),
                    "predicate for %r matched the branch with the rule removed, so it is "
                    "checking surrounding text, not the rule" % name)

    def test_the_budget_is_modules_7s_acceptable_threshold(self):
        """The 5% is not a second threshold: it is Module 7's Acceptable bound."""
        self.assertIn("**Acceptable** (proceed): ratio is reasonable, possible matches < 5%",
                      query())


class TheSampleRecordsTheWholeScenario(unittest.TestCase):

    def test_the_sample_is_top_level_with_the_four_keys(self):
        self.assertTrue(sample_is_valid(sample_yaml()), sample_yaml())

    def test_the_measured_fields_are_written_by_the_self_check(self):
        y = sample_yaml()
        for key in ("measured_entities", "measured_share"):
            with self.subTest(key=key):
                line = next(l for l in y.splitlines() if l.strip().startswith(key + ":"))
                self.assertRegex(line, r"(?:written by the self-check, never by hand|"
                                       r"measured_entities / invented entities)")
        self.assertRegex(y, r"measured_entities: \d+\s+# written by the self-check, never by hand")

    def test_negative_control_nested_under_a_source_fails(self):
        nested = "sources:\n  - name: X\n" + "".join(
            "    " + l + "\n" for l in sample_yaml().splitlines() if l and
            not l.startswith(("version", "sources", "  #")))
        self.assertFalse(sample_is_valid(nested))

    def test_negative_control_zero_declared_pairs_fails(self):
        self.assertFalse(sample_is_valid(
            re.sub(r"declared_pairs: \d+", "declared_pairs: 0", sample_yaml())))

    def test_negative_control_a_share_over_the_budget_fails(self):
        self.assertFalse(sample_is_valid(
            re.sub(r"measured_share: [\d.]+", "measured_share: 0.050", sample_yaml())))

    def test_negative_control_a_missing_key_fails(self):
        self.assertFalse(sample_is_valid(re.sub(r"(?m)^\s+reason: .*\n", "", sample_yaml())))

    def test_the_registry_schema_note_names_the_block(self):
        note = registry_note()
        self.assertIn("top level beside `version` and `sources:`, never inside a source entry",
                      note)
        self.assertIn("`scenario_intent: {name_collisions: {declared_pairs, reason, "
                      "measured_entities, measured_share}}`", note)
        self.assertIn("[the name-sharing budget](#name-sharing-budget)", note)
        self.assertRegex(note, r"written by Step 2's self-check, never by hand")


class TheSelfCheckRegeneratesNeverPatches(unittest.TestCase):

    CASES = (
        ("counts name-sharing entities and pairs", counts_name_sharing),
        ("writes measured_entities and measured_share", writes_the_measured_fields),
        ("regenerates on measured_share >= 0.05", regenerates_on_the_share),
        ("regenerates when the hard negatives were lost", regenerates_on_lost_hard_negatives),
        ("never patches afterwards", never_patches),
        ("applies to a regeneration after Module 5's gate", covers_a_regeneration_after_the_gate),
    )

    def test_it_sits_in_the_band_self_check_after_the_identifier_check(self):
        branch = synthesized_branch()
        band = branch.index("⛔ **Verify the generated data against the band before this module")
        ident = branch.index(ID_SELF_CHECK_HEAD)
        check = branch.index(SELF_CHECK_HEAD)
        offpattern = branch.index("**off-pattern values in at least one field per source**")
        self.assertLess(band, ident)
        self.assertLess(ident, check)
        self.assertLess(check, offpattern)

    def test_each_clause_is_in_the_self_check(self):
        text = self_check(synthesized_branch())
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(holds(text), "the name-sharing self-check lost: %s" % name)

    def test_negative_control_each_clause_fails_without_the_self_check(self):
        branch = synthesized_branch()
        stripped = branch.replace(self_check(branch), "")
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertFalse(holds(stripped))

    def test_it_links_the_rule_it_counts_against(self):
        self.assertIn("[the name-sharing budget](#name-sharing-budget)",
                      self_check(synthesized_branch()))

    def test_the_collection_return_bullet_runs_it(self):
        bullet = return_bullet()
        self.assertRegex(bullet, r"identifier collisions \(on any count above zero, regenerate "
                                 r"the affected values\) and name sharing, rewriting "
                                 r"`scenario_intent\.name_collisions` from the new count")
        self.assertRegex(bullet, r"on a share of 0\.05 or more, or fewer pairs than "
                                 r"`declared_pairs`, regenerate names")

    def test_negative_control_the_old_return_bullet_fails(self):
        old = ("⛔ **(INV-239) Both self-checks in this step apply to the regeneration:** verify it "
               "against the band (if it misses `>=80`, narrow the gaps further and regenerate; "
               "never adjust a score), and count identifier collisions (on any count above zero, "
               "regenerate the affected values).")
        self.assertNotRegex(old, r"name sharing, rewriting `scenario_intent\.name_collisions`")


class Module7ReportsTheMeasuredFigure(unittest.TestCase):

    CASES = (
        ("the band stays on the raw rate", bands_on_the_raw_rate),
        ("only on an all-synthesized scenario with the block", requires_all_synthesized_and_the_block),
        ("measured_entities beside the possible-match count, on Marginal or Poor",
         reports_the_measured_figure),
        ("no figure without the block or on a mixed scenario", falls_back_without_the_block),
        ("the example keeps the two units apart", keeps_the_units_apart_in_the_example),
    )

    def test_it_is_an_anchored_hard_rule_before_the_verdict_wording(self):
        text = query()
        self.assertIn(M7_ANCHOR + " " + M7_HEAD, text)
        sample = text.index("⛔ **Before stating any of the three verdicts, sample and show.**")
        self.assertLess(sample, text.index(M7_HEAD))
        self.assertLess(text.index(M7_HEAD), text.index("Based on the assessment"))

    def test_each_clause_is_in_the_paragraph(self):
        text = m7_paragraph(query())
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertTrue(holds(text), "Module 7's measured-figure rule lost: %s" % name)

    def test_negative_control_each_clause_fails_without_the_paragraph(self):
        text = query()
        stripped = text.replace(m7_paragraph(text), "")
        for name, holds in self.CASES:
            with self.subTest(clause=name):
                self.assertFalse(holds(stripped))

    def test_the_band_thresholds_are_unchanged(self):
        text = query()
        self.assertIn("possible matches < 5%", text)
        self.assertIn("**Marginal** (review): possible matches 5–15%", text)
        self.assertIn("**Poor** (iterate): possible matches > 15%", text)

    def test_outcome_2_cites_the_figure_over_half_and_keeps_todays_wording(self):
        bullet = outcome_2(query())
        self.assertTrue(cites_the_figure_over_half(bullet))
        self.assertTrue(keeps_todays_wording(bullet))
        self.assertTrue(keeps_the_units_apart_in_outcome_2(bullet))

    def test_negative_control_a_subset_example_fails(self):
        """The issue's example read invented entities as a subset of possible-match entities."""
        para = m7_paragraph(query())
        subset = re.sub(r"\"\d+ entities have a possible match; Data collection measured (\d+) "
                        r"invented entities that share",
                        r'"\1 of the 300 entities with a possible match share', para)
        self.assertNotEqual(subset, para, "the substitution must reach the example")
        self.assertFalse(keeps_the_units_apart_in_the_example(subset))
        self.assertFalse(keeps_the_units_apart_in_the_example(
            '"112 of the 300 entities with a possible match share a name with a different '
            'invented person — a lower bound, because nicknames and typo variants are not '
            'counted."'))

    def test_negative_control_a_subset_outcome_2_citation_fails(self):
        bullet = outcome_2(query())
        subset = bullet.replace(
            '"[n] entities have a possible match; Data collection measured, before loading, '
            '[measured_entities] invented entities that share',
            '"[measured_entities] of the [n] entities with a possible match share')
        self.assertNotEqual(subset, bullet, "the substitution must reach the citation")
        self.assertFalse(keeps_the_units_apart_in_outcome_2(subset))
        self.assertFalse(keeps_the_units_apart_in_outcome_2(
            '"[measured_entities] of the [n] entities with a possible match share a name with a '
            'different invented person, as the scenario measured before loading."'))

    def test_negative_control_the_old_outcome_2_bullet_fails(self):
        old = ("**Name-only collisions** in small or synthetic datasets, from a limited name pool. "
               "On a generated scenario the plugin built that pool.")
        self.assertFalse(cites_the_figure_over_half(old))
        self.assertFalse(keeps_todays_wording(old))

    def test_the_link_to_module_4_resolves(self):
        self.assertIn("[the name-sharing budget](../module-04-data-collection/SKILL.md"
                      "#name-sharing-budget)", m7_paragraph(query()))
        self.assertTrue(COLLECTION.is_file())
        self.assertIn(ANCHOR, COLLECTION.read_text(encoding="utf-8"))


def without_fences(text):
    """``text`` with every fenced code line blanked, so line numbers are kept."""
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^[ \t>]*(`{3,}|~{3,})", line)
        if m and (fence is None or m.group(1)[0] == fence):
            fence = None if fence else m.group(1)[0]
            out.append("")
        else:
            out.append("" if fence else line)
    return "\n".join(out)


READER = re.compile(r"`(?:scenario_intent[^`]*|[^`]*measured_share[^`]*)`")
LINKED = re.compile(r"\]\((?:[\w./-]*module-04-data-collection/SKILL\.md)?#name-sharing-budget\)")


def unlinked_readers(path, text):
    """``path:line`` for each prose block naming the block or its share without the anchor link.

    A block is one Markdown block as ``_wrapped_text.blocks`` cuts it, read collapsed
    (INV-346), so a link wrapped across lines still counts. Fenced code is blanked first: a
    YAML sample is not a reader. The rule's own block (the one holding ``RULE_HEAD``) defines
    the block, so it is not a reader either.
    """
    bad = []
    for block in blocks(without_fences(text)):
        flat = squash(" ".join(line for _, line in block)).strip()
        if READER.search(flat) and RULE_HEAD not in flat and not LINKED.search(flat):
            bad.append("%s:%d" % (path, block[0][0]))
    return bad


class EveryReaderLinksTheRule(unittest.TestCase):
    """INV-246: the readers are found by scanning, not listed; INV-300: they point, not restate."""

    def shipped(self):
        return sorted(p for p in PLUGIN.rglob("*.md"))

    def test_every_reader_of_scenario_intent_links_the_rule(self):
        bad, readers = [], 0
        for path in self.shipped():
            text = path.read_text(encoding="utf-8")
            if READER.search(text):
                readers += 1
            bad += unlinked_readers(path.relative_to(REPO_ROOT), text)
        self.assertEqual(bad, [], "a block names `scenario_intent` or `measured_share` without "
                                  "linking the name-sharing budget")
        self.assertGreaterEqual(readers, 2, "the scan found too few readers; is it vacuous?")

    def test_negative_control_an_unlinked_reader_is_caught(self):
        text = ("Intro.\n\nOn a generated scenario read `scenario_intent.name_collisions` and\n"
                "report its `measured_share`.\n\nOutro.\n")
        self.assertEqual(unlinked_readers("x.md", text), ["x.md:3"])

    def test_negative_control_a_wrapped_link_is_not_flagged(self):
        text = ("Intro.\n\nRead `scenario_intent.name_collisions` as [the name-sharing\n"
                "budget](../module-04-data-collection/SKILL.md#name-sharing-budget) says.\n")
        self.assertEqual(unlinked_readers("x.md", text), [])

    def test_negative_control_each_shipped_reader_is_caught_without_its_link(self):
        for path in (COLLECTION, QUERY):
            text = path.read_text(encoding="utf-8")
            stripped = re.sub(r"\]\((?:\.\./module-04-data-collection/SKILL\.md)?"
                              r"#name-sharing-budget\)", "](#elsewhere)", text)
            with self.subTest(path=path.name):
                self.assertNotEqual(unlinked_readers(path.name, stripped), [])


class ItStaysLanguageAgnostic(unittest.TestCase):

    def test_the_rule_and_its_checks_name_no_language_or_tool(self):
        branch = synthesized_branch()
        text = rule(branch) + self_check(branch) + m7_paragraph(query())
        self.assertNotRegex(
            text, r"(?i)\b(?:python|java|csharp|rust|typescript|node|pandas|faker|bash|"
                  r"powershell|uuid4)\b|\.py\b",
            "the rule must state the property, not an implementation (language-agnostic, per "
            "INVARIANTS.md)")


if __name__ == "__main__":
    unittest.main()
