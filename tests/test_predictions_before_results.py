"""The Bootcamper predicts before the engine's result is shown, at three points.

Before #479 the guide made every prediction the engine was checked against (*"it compares the
engine against a prediction the guide made"*, System verification's SKILL.md), and the
Bootcamper never committed to an expectation before a result appeared. #479 adds three
prediction points:

1. **System verification, Step 7a.** One `Mari` record, a copy of a Marisol record with only the
   first name changed, is shown before it is loaded: "will it join Marisol's entity?". It sits
   between Step 7 and Step 8, outside Step 7's checks and the `synthetic_data` expectations.
2. **Discover, Step 4a-pairs.** Three record pairs from step 4a's entities, one per turn, before
   step 4b: "same entity or not?".
3. **Discover, step 4b item 1a.** Truth Set alumni pick the features that joined one of their own
   cross-source entities before `why_records` is shown.

**One shared rule, cited (INV-300).** The skip, the reveal's shape, "informs, never grades" and
the Questions & Responses line are stated once, in `ground-rules.md` → "Predictions before
results". Each site points there and carries only what it predicts and how the engine answers.

So the clauses are checked where they live:

- **Per site** (`point_problems`, run on each of the three): exactly one 👉 (INV-251), a numbered
  list of choices (INV-051), a skip, the 👉 before the reveal, and a pointer that names the
  grading guard and the skip recording it defers to.
- **In the shared section** (`rule_problems`): the rule-only clauses, among them the grading guard
  and the skipped line format.

The checks are pure functions over a file's text, so each one also runs on a mutated copy as its
negative control. `TheChecksCatchARegression` runs six regressions against every site: the reveal
stated before the 👉, the skip removed, a second 👉 added, the options unnumbered, the grading
guard deleted, and the skip recording deleted. The last two also run against the shared section.
Each must make the check report the problem it targets, not merely some problem.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line by
construction; counting lines that *start* with `👉 **` keeps prose that mentions the marker
("the next 👉") from being counted. Phrase checks use `_wrapped_text.match_lines`, which matches
across a wrap.

⛔ **What this cannot establish:** that a live guide holds the result back, asks before loading,
or never grades. Those are properties of a conversation; `dry-run` phase 3 and `auto-test`'s
transcript linter observe them. This pins that the skill files STATE them.

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #479 (part of #465).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _wrapped_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"
M3_PHASE1 = SKILLS / "module-03-system-verification" / "phase1-verification.md"
M3_PHASE2 = SKILLS / "module-03-system-verification" / "phase2-report-close.md"
DISCOVER = SKILLS / "module-07-query-visualize-discover" / "phase2-discover.md"

RULE_HEADING = "## Predictions before results"
MARI_HEADING = "### Step 7a: The Mari Prediction"
PAIRS_HEADING = "### Step 4a-pairs: Same entity or not?"
STEP_4B_HEADING = "### Step 4b: Why Analysis introduction"
OWN_ITEM = "1a. **Own-entity prediction (Truth Set alumni only).**"
OWN_ITEM_END = "\n2. **SDK method introduction:**"

MARI_QUESTION = "👉 **Will this `Mari` record join Marisol's entity? Reply with a number:**"
PAIR_QUESTION = ("👉 **Are these two records the same entity? Reply with a number, and add a few "
                 "words on why if you like:**")
OWN_QUESTION = ('👉 **Which features do you think joined these records? Reply with the numbers, '
                'comma-separated — reply "skip" to just see the engine\'s answer.**')
#: The skip on a single-choice prediction: its last numbered option.
SKIP_OPTION = "Just show me the engine's answer."
#: The skip on a multi-select prediction: a clause of the 👉 line itself.
SKIP_CLAUSE = '— reply "skip" to just see the engine\'s answer.'

#: Where each site's result starts; the 👉 must come first.
MARI_REVEAL = "**Reveal the engine's live call beside the prediction"
PAIRS_REVEAL = "**Reveal it in the same turn as the next 👉.**"
OWN_REVEAL = "**The reveal is items 2–5**"

#: The pointer every site carries instead of a copy (INV-300).
CITATION = (r'stated once in\s+`\.\./bootcamp-onboarding/ground-rules\.md` → "Predictions before '
            r'results"; follow them there\s+rather than a copy here \(INV-300\)')
#: What that pointer must name, so a site cannot quietly drop a clause it defers to.
POINTER_NAMES = {
    "the grading guard": '"informs, never grades"',
    "the skip recording": "the Questions & Responses line",
}

#: Phrases only the shared rule may carry; a site that holds one has forked it (INV-300).
RULE_ONLY = (r"(?i)never say \"correct\"", r"(?i)keep a score", r"\(agreed\)`, or `\(differed\)",
             r"skipped → \{engine's call\}")


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def match_lines(text, pattern):
    """`_wrapped_text.match_lines` with ``pattern`` given as a string."""
    return _wrapped_text.match_lines(text, re.compile(pattern))


def section(text, start, end_markers):
    """Text from ``start`` up to the first of ``end_markers`` after it ('' when absent)."""
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i:]
    cut = [rest.find(m, len(start)) for m in end_markers]
    cut = [c for c in cut if c > 0]
    return rest[:min(cut)] if cut else rest


def questions(text):
    """The 👉 question lines, in order (see the module docstring for why lines)."""
    return [line.strip() for line in text.splitlines() if line.strip().startswith("👉 **")]


def options_after(text, question):
    """The numbered option lines directly beneath ``question``."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == question:
            opts = []
            for later in lines[i + 1:]:
                s = later.strip()
                if not s and not opts:
                    continue
                if re.match(r"\d+\. ", s):
                    opts.append(s)
                    continue
                break
            return opts
    return []


def citation_problems(site, where):
    """A site points at the shared rule, names what it defers to, and carries no copy of it."""
    problems = []
    if not match_lines(site, CITATION):
        problems.append("%s does not point at the shared rule with INV-300" % where)
    flat = squash(site)
    start = flat.find("This is a prediction point:")
    pointer = flat[start:flat.find("(INV-300)", start)] if start >= 0 else ""
    for what, phrase in POINTER_NAMES.items():
        if phrase not in pointer:
            problems.append("%s's pointer does not name %s (%s)" % (where, what, phrase))
    for phrase in RULE_ONLY:
        if match_lines(site, phrase):
            problems.append("%s restates the shared rule (%s)" % (where, phrase))
    return problems


def point_problems(where, step, question, reveal, multi_select=False):
    """The per-site clauses every prediction point shares.

    One 👉 (INV-251), a numbered list of choices beneath it (INV-051), a skip (the last option
    on a single choice, a clause of the 👉 line on a multi-select), and the 👉 before the reveal.
    """
    problems = []
    asked = questions(step)
    if len(asked) != 1:
        problems.append("%s asks %d 👉 questions, not exactly one (INV-251)" % (where, len(asked)))
    if question not in asked:
        problems.append("%s does not ask %r" % (where, question))
    first = asked[0] if asked else question
    opts = options_after(step, first)
    if len(opts) < 2:
        problems.append("%s's 👉 is not followed by a numbered list of choices (INV-051)" % where)
    if multi_select:
        has_skip = SKIP_CLAUSE in first
    else:
        has_skip = bool(opts) and opts[-1].endswith(SKIP_OPTION)
    if not has_skip:
        problems.append("%s offers no skip (options %r)" % (where, opts))
    ask, shown = step.find(first), step.find(reveal)
    if shown < 0:
        problems.append("%s has no reveal (%r)" % (where, reveal))
    elif ask < 0 or shown < ask:
        problems.append("%s shows its result before its 👉" % where)
    return problems


# --------------------------------------------------------------------------------------------
# The shared rule
# --------------------------------------------------------------------------------------------

def rule_problems(ground_rules):
    rule = section(ground_rules, RULE_HEADING, ("\n## ",))
    if not rule:
        return ["the ground rules have no %r section" % RULE_HEADING]
    problems = []
    required = {
        "the prediction comes before the result": r"⛔ \*\*The prediction is asked before the "
                                                  r"result exists in the conversation\.\*\*",
        "an already-run result is held back": r"hold its outcome back",
        "the result arrives on the next turn": r"the result arrives in the next turn",
        "it is a numbered choice (INV-051)": r"A numbered choice \(INV-051\)",
        "the single-choice skip is the last option": r"it is the last numbered option, \"Just "
                                                     r"show me the\s*engine's answer\.\"",
        "the multi-select skip is its own clause": r"on a multi-select it is its own clause",
        "a 'why' is optional": r"it is optional and never re-asked",
        "one 👉 per turn (INV-251)": r"One 👉 per turn \(INV-251\)",
        "the reveal is non-yielding (INV-225)": r"so it is non-yielding \(INV-225\)",
        "the reveal shows both with agreed/differed": r"`agreed` or `differed`",
        "one line from the engine's own output": r"\*\*one line\*\* on what the engine used",
        "it is never graded": r"⛔ \*\*A prediction informs; it is never graded\.\*\*",
        "it is never graded (no correct/incorrect)": r"never say \"correct\" or \"incorrect\"",
        "it is never graded (no score)": r"never keep a score or a tally",
        "it is never graded (no re-ask)": r"and never re-ask\.",
        "the guide does not predict": r"\*\*The guide does not predict\.\*\*",
        "no result means no prediction": r"\*\*No result, no prediction\.\*\*",
        "the Q&R line format": r"`- \*\*\{the 👉 question\}\*\* — \{prediction\} → "
                               r"\{engine's call\}\s*\(agreed\)`, or `\(differed\)`",
        "the skipped line format": r"`- \*\*\{the 👉 question\}\*\* — skipped → \{engine's call\}`",
    }
    if '<a id="predictions-before-results"></a>' not in ground_rules:
        problems.append("the ground rules do not anchor the section")
    for what, pattern in required.items():
        if not match_lines(rule, pattern):
            problems.append("the rule does not state that %s" % what)
    for site in ("Step 7a", "Step 4a-pairs", "item 1a"):
        if site not in rule:
            problems.append("the rule's site table does not list %s" % site)
    if questions(rule):
        problems.append("the rule itself asks a 👉 question")
    return problems


# --------------------------------------------------------------------------------------------
# System verification, Step 7a
# --------------------------------------------------------------------------------------------

def mari_step(phase1):
    return section(phase1, MARI_HEADING, ("### Step 8",))


def mari_problems(phase1):
    problems = []
    step_7 = phase1.find("### Step 7: Deterministic Results Validation")
    step_7a = phase1.find(MARI_HEADING)
    step_8 = phase1.find("### Step 8: Database Operations")
    if min(step_7, step_7a, step_8) < 0 or not step_7 < step_7a < step_8:
        return ["Step 7a is not between Step 7 and Step 8"]
    step = phase1[step_7a:step_8]
    problems += point_problems("Step 7a", step, MARI_QUESTION, MARI_REVEAL)
    if len(options_after(step, MARI_QUESTION)) != 3:
        problems.append("the Mari question does not offer joins / stays separate / the skip")
    ask = step.find(MARI_QUESTION)
    load = step.find("Load `mari_record.jsonl`")
    reveal = step.find(MARI_REVEAL)
    if ask < 0 or load < 0 or reveal < 0 or not ask < load < reveal:
        problems.append("Step 7a does not ask, then load, then reveal, in that order")
    if not match_lines(step, r"Load nothing yet"):
        problems.append("Step 7a does not say nothing is loaded before the answer")
    if not match_lines(step, r"change only\s+`NAME_FIRST`, to `Mari`"):
        problems.append("the Mari record is not a Marisol copy with only the first name changed")
    if not match_lines(step, r"Keep `DATA_SOURCE` `VERIFY`"):
        problems.append("the Mari record does not keep DATA_SOURCE VERIFY")
    if not match_lines(step, r"`verification_data\.jsonl` is unchanged"):
        problems.append("Step 7a does not keep the Mari record out of verification_data.jsonl")
    if not match_lines(step, r"outside `checks`"):
        problems.append("the Mari checkpoint is not kept outside the verification checks")
    if not match_lines(step, r"does not predict this outcome and does not validate it"):
        problems.append("Step 7a does not say the guide neither predicts nor validates it")
    if not match_lines(step, r"Continue in the same turn to Step 8"):
        problems.append("the reveal is not followed in the same turn by Step 8")
    if not match_lines(step, r"no result, no prediction"):
        problems.append("Step 7a has no no-Marisol-entity path")
    problems += citation_problems(step, "Step 7a")
    return problems


def mari_exclusion_problems(phase1, phase2):
    """Step 7 and `synthetic_data` exclude the record; the purge removes it."""
    problems = []
    step_2 = section(phase1, "### Step 2: Generate Synthetic Verification Records",
                     ("### Step 3",))
    if not match_lines(step_2, r"first name `Marisol`"):
        problems.append("Step 2 does not name the merge cluster's person Marisol")
    if not match_lines(step_2, r"never counted in the expected outcome below, so Step 7 never "
                               r"checks it"):
        problems.append("Step 2 does not exclude the Mari record from the expectations")
    step_8 = section(phase1, "### Step 8: Database Operations", ("**Checkpoint:**",))
    if not match_lines(step_8, r"plus one when Step 7a loaded the `Mari` record"):
        problems.append("Step 8's write count does not allow for the Mari record")
    purge = section(phase2, "## Step 10: Cleanup", ("## Step 11",))
    if not match_lines(purge, r"includes Step 7a's `Mari` record"):
        problems.append("the VERIFY purge does not name the Mari record")
    return problems


# --------------------------------------------------------------------------------------------
# Discover, Step 4a-pairs and step 4b item 1a
# --------------------------------------------------------------------------------------------

def pairs_step(discover):
    return section(discover, PAIRS_HEADING, (STEP_4B_HEADING,))


def pairs_problems(discover):
    problems = []
    step_4a = discover.find("### Step 4a: Data pattern analysis")
    pairs = discover.find(PAIRS_HEADING)
    step_4b = discover.find(STEP_4B_HEADING)
    if min(step_4a, pairs, step_4b) < 0 or not step_4a < pairs < step_4b:
        return ["Step 4a-pairs is not between step 4a and step 4b"]
    step = discover[pairs:step_4b]
    problems += point_problems("Step 4a-pairs", step, PAIR_QUESTION, PAIRS_REVEAL)
    if len(options_after(step, PAIR_QUESTION)) != 3:
        problems.append("the pair question does not offer same / different / the skip")
    required = {
        "3 pairs by default": r"Choose 3 pairs from step 4a's entities",
        "the answers are held back": r"Hold them back",
        "at least one pair that resolved together": r"At least one pair that resolved together",
        "at least one pair that did not": r"At least one pair that did not",
        "one pair per turn": r"Show one pair per turn, then ask",
        "nothing shown hints at the answer": r"Show no entity ID, match key",
        "limited data shows as many as it can": r"show as\s+many as it can",
        "no pairs is said in one line": r"say so in one line and\s+continue to step 4b",
        "the last reveal goes with step 4b's first 👉": r"After the last pair it is step 4b's\s+"
                                                        r"first 👉",
        "a resume lands on the next pair": r"a resume lands on the next pair",
    }
    for what, pattern in required.items():
        if not match_lines(step, pattern):
            problems.append("Step 4a-pairs does not state %s" % what)
    problems += citation_problems(step, "Step 4a-pairs")
    return problems


def own_item(discover):
    return section(section(discover, STEP_4B_HEADING, ("### Step 4c",)), OWN_ITEM, (OWN_ITEM_END,))


def own_entity_problems(discover):
    step = section(discover, STEP_4B_HEADING, ("### Step 4c",))
    item_1a = section(step, OWN_ITEM, (OWN_ITEM_END,))
    if not item_1a:
        return ["step 4b has no item 1a own-entity prediction"]
    problems = []
    at = step.find(item_1a)
    first_call = step.find("3. **SDK flags and response shape:**")
    explanation = step.find("4. **Plain-language explanation of the output:**")
    if not at < first_call < explanation:
        problems.append("item 1a does not come before step 4b's why_records call")
    if step.find("1. **Entity selection:**") > at:
        problems.append("item 1a comes before the entity it predicts about is chosen")
    problems += point_problems("step 4b item 1a", item_1a, OWN_QUESTION, OWN_REVEAL,
                               multi_select=True)
    if questions(step)[:1] != [OWN_QUESTION]:
        problems.append("the own-entity question is not step 4b's first 👉")
    required = {
        "it runs only for Truth Set alumni": r"only when\s+`truthset_visualization` is in "
                                             r"`modules_completed`",
        "otherwise step 4b runs as before": r"Otherwise go straight to item 2, as before",
        "records are shown before any why call": r"Show the entity's records before any "
                                                 r"`why_\*` call",
        "the app is used when step 3c built it": r"When step 3c built the visualization app",
        "text is the fallback": r"Otherwise show the two\s+records item 1 named as text",
        "the options are the entity's feature types": r"The options are this entity's feature "
                                                      r"types",
        "the reveal is why_records' output": r"The reveal is items 2–5",
        "picks sit beside the why key": r"beside the `\+FEATURE` components of `WHY_KEY`",
    }
    for what, pattern in required.items():
        if not match_lines(item_1a, pattern):
            problems.append("item 1a does not state that %s" % what)
    problems += citation_problems(item_1a, "step 4b item 1a")
    return problems


# --------------------------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------------------------

class TheFilesExist(unittest.TestCase):
    def test_every_file_exists(self):
        for path in (GROUND_RULES, COMPLETION, M3_PHASE1, M3_PHASE2, DISCOVER):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path)


class TheRuleIsStatedOnce(unittest.TestCase):
    def test_the_rule_states_every_clause(self):
        self.assertEqual(rule_problems(read(GROUND_RULES)), [])

    def test_the_q_and_r_rule_points_at_it(self):
        flat = squash(read(COMPLETION))
        self.assertRegex(
            flat, r'its format is stated once in `ground-rules\.md` → "Predictions before '
                  r'results" \(INV-300\)',
            "module-completion's Questions & Responses rule does not point at the line format")

    def test_negative_control_a_removed_clause_is_reported(self):
        text = read(GROUND_RULES).replace("hold its outcome back", "show it")
        self.assertIn("the rule does not state that an already-run result is held back",
                      rule_problems(text))


class TheMariPrediction(unittest.TestCase):
    def setUp(self):
        self.phase1 = read(M3_PHASE1)

    def test_it_asks_before_it_loads(self):
        self.assertEqual(mari_problems(self.phase1), [])

    def test_step_7_and_the_expectations_exclude_it_and_the_purge_removes_it(self):
        self.assertEqual(mari_exclusion_problems(self.phase1, read(M3_PHASE2)), [])

    def test_negative_control_loading_before_asking(self):
        step = mari_step(self.phase1)
        moved = step.replace(
            "2. **Show it, then ask. Load nothing yet.**",
            "2. Load `mari_record.jsonl` first. **Show it, then ask. Load nothing yet.**")
        self.assertIn("Step 7a does not ask, then load, then reveal, in that order",
                      mari_problems(self.phase1.replace(step, moved)))

    def test_negative_control_the_site_restates_the_rule(self):
        text = self.phase1.replace(
            "Load nothing yet.**", "Load nothing yet.** Never say \"correct\".")
        self.assertTrue(any(p.startswith("Step 7a restates the shared rule")
                            for p in mari_problems(text)))

    def test_negative_control_the_purge_forgets_it(self):
        phase2 = read(M3_PHASE2).replace("That includes Step 7a's `Mari` record", "That is all")
        self.assertIn("the VERIFY purge does not name the Mari record",
                      mari_exclusion_problems(self.phase1, phase2))


class TheRecordPairs(unittest.TestCase):
    def setUp(self):
        self.discover = read(DISCOVER)

    def test_they_ask_before_they_reveal(self):
        self.assertEqual(pairs_problems(self.discover), [])

    def test_negative_control_pairs_after_step_4b(self):
        step = pairs_step(self.discover)
        text = self.discover.replace(step, "")
        text = text.replace("### Step 4c: How Analysis introduction",
                            step + "### Step 4c: How Analysis introduction")
        self.assertEqual(pairs_problems(text),
                         ["Step 4a-pairs is not between step 4a and step 4b"])


class TheOwnEntityPrediction(unittest.TestCase):
    def setUp(self):
        self.discover = read(DISCOVER)

    def test_it_opens_step_4b_before_why_records(self):
        self.assertEqual(own_entity_problems(self.discover), [])

    def test_negative_control_after_the_why_call(self):
        item = own_item(self.discover)
        text = self.discover.replace(item, "")
        text = text.replace("4. **Plain-language explanation of the output:**",
                            item.lstrip("\n") + "\n4. **Plain-language explanation of the output:**")
        self.assertIn("item 1a does not come before step 4b's why_records call",
                      own_entity_problems(text))

    def test_negative_control_not_gated_on_the_truth_set(self):
        text = self.discover.replace("only when\n   `truthset_visualization` is in",
                                     "always, whatever is in")
        self.assertIn("item 1a does not state that it runs only for Truth Set alumni",
                      own_entity_problems(text))


def _loose(phrase):
    """``phrase`` as a regex that matches across a line wrap."""
    return r"\s+".join(re.escape(word) for word in phrase.split())


class TheChecksCatchARegression(unittest.TestCase):
    """Six regressions, each run against every site; each must report the problem it targets.

    Carried over from #479's approach A, adapted to the shared rule: the per-site clauses (one
    👉, numbered options with a skip, the reveal after the 👉) are mutated at each site, and the
    rule-only clauses (the grading guard, the skip recording) are mutated both in the shared
    section and in each site's pointer to it. The assertion is on the targeted problem, not on
    "some problem", so a mutation that trips an unrelated check does not pass for a real catch.
    """

    #: (where, file, the site's section, its check, its 👉, where its result starts)
    SITES = (
        ("Step 7a", M3_PHASE1, mari_step, mari_problems, MARI_QUESTION, MARI_REVEAL),
        ("Step 4a-pairs", DISCOVER, pairs_step, pairs_problems, PAIR_QUESTION, PAIRS_REVEAL),
        ("step 4b item 1a", DISCOVER, own_item, own_entity_problems, OWN_QUESTION, OWN_REVEAL),
    )

    def check(self, mutate, expected):
        """Mutate each site's section in place; its check must report ``where`` + ``expected``."""
        for where, path, cut, problems_of, question, reveal in self.SITES:
            with self.subTest(site=where):
                text = read(path)
                site = cut(text)
                self.assertTrue(site, "%s is missing, so the control would be vacuous" % where)
                self.assertEqual(problems_of(text), [], "%s fails before the mutation" % where)
                mutated = mutate(site, question, reveal)
                self.assertNotEqual(mutated, site, "the mutation did not change %s" % where)
                problems = problems_of(text.replace(site, mutated))
                wanted = "%s%s" % (where, expected)
                self.assertTrue(any(p.startswith(wanted) for p in problems),
                                "%r went unnoticed: %r" % (wanted, problems))

    def test_the_reveal_stated_before_the_question(self):
        self.check(lambda s, q, r: s.replace(q, "%s\n\n%s" % (r, q), 1),
                   " shows its result before its 👉")

    def test_the_skip_removed(self):
        self.check(lambda s, q, r: s.replace(SKIP_OPTION, "Not sure.").replace(" " + SKIP_CLAUSE, ""),
                   " offers no skip")

    def test_a_second_question_added(self):
        self.check(lambda s, q, r: s.rstrip("\n") + "\n\n👉 **Anything else?**\n",
                   " asks 2 👉 questions, not exactly one (INV-251)")

    def test_the_options_unnumbered(self):
        self.check(lambda s, q, r: re.sub(r"(?m)^(\s*)\d+\. ", r"\1- ", s),
                   "'s 👉 is not followed by a numbered list of choices (INV-051)")

    def test_the_grading_guard_removed_from_a_site(self):
        self.check(lambda s, q, r: re.sub(_loose('"informs, never grades" and'), "and", s),
                   "'s pointer does not name the grading guard")

    def test_the_skip_recording_removed_from_a_site(self):
        self.check(lambda s, q, r: re.sub(_loose("and the Questions & Responses line"), "", s),
                   "'s pointer does not name the skip recording")

    def test_the_citation_dropped(self):
        self.check(lambda s, q, r: s.replace("(INV-300)", ""),
                   " does not point at the shared rule with INV-300")

    def _rule_check(self, pattern, expected):
        text = read(GROUND_RULES)
        self.assertEqual(rule_problems(text), [], "the shared rule fails before the mutation")
        mutated = re.sub(pattern, "", text, count=1, flags=re.S)
        self.assertNotEqual(mutated, text, "the mutation did not change the shared rule")
        problems = rule_problems(mutated)
        self.assertTrue(any(p.startswith(expected) for p in problems),
                        "%r went unnoticed: %r" % (expected, problems))

    def test_the_grading_guard_removed_from_the_shared_rule(self):
        self._rule_check(r"- ⛔ \*\*A prediction informs; it is never graded\.\*\*.*?(?=\n- )",
                         "the rule does not state that it is never graded")

    def test_the_grading_guard_softened_in_the_shared_rule(self):
        self._rule_check(r"never keep a score or a tally, ",
                         "the rule does not state that it is never graded (no score)")

    def test_the_skip_recording_removed_from_the_shared_rule(self):
        self._rule_check(r";\s+a skip is `- \*\*\{the 👉 question\}\*\* — skipped → [^`]*`",
                         "the rule does not state that the skipped line format")


if __name__ == "__main__":
    unittest.main()
