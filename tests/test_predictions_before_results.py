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
- **The introduction (#747)**, also in the shared section: before a site's first 👉 the guide says
  once, in its own words, why the Bootcamper is asked, what agreeing means and what differing
  means. The rule states what it covers and fixes no wording, so `rule_problems` requires each of
  the three, the once-per-site clause and the no-repeat-on-resume clause, and `intro_problems`
  fails the bullet if it carries a grading word (`GRADING_WORDS`: "correct", a score, a tally, a
  grade). Its lead phrase and its agreement clause are `RULE_ONLY`, so a site that carries its own
  copy of the introduction is reported as restating the rule (INV-300); each site reaches it
  through its existing "This is a prediction point:" pointer.
- **At every pointer, derived** (`pointer_citation_problems`, #519): every shipped sentence that
  points at "Predictions before results", found by scan rather than from the three sites above
  (INV-246), cites INV-357, so a reader at the pointer can name the rule as well as the
  single-statement discipline. Since #519 that is six sentences: the three sites' pointers, the
  Questions & Responses rule in `module-completion.md`, and System verification's two statements
  that the prediction is asked before the engine decides (its `SKILL.md`, and the opening of
  `phase1-verification.md`), which make no single-statement claim and so cite INV-357 without
  INV-300.

**No route to the answer before the 👉 (#507).** A site can show its result without stating it: the
visualization app's entity view renders each record's match key and the why verdict, which is
exactly what step 4b item 1a asks the Bootcamper to predict, and an entity the bootcamp already
resolved on screen has had its answer shown. So two more checks:

- **No app route** (`app_route_problems`, run by `point_problems` on the text before each site's
  👉, and on step 4b item 1 before item 1a): no `m7_visualizations`, no URL, no port, and no
  local address (`localhost`, `127.0.0.1`, `http://`, `https://`). Item 1a must state that its
  records are shown as text only. The markers are single tokens, so a line wrap cannot split one
  (INV-346).
- **Already-shown entities, stated once** (`already_shown_problems`, INV-300). One named section
  of `phase2-discover.md`, "Already-shown entities", states which entities are excluded (the
  headline entity and the entity that holds Module 6's `midpoint_record`), how the latter is
  located (`get_entity_by_record_id` on the record), and the `"none"`/absent cases. Step 4a-pairs
  item 1 and step 4b item 1 each point there, name both exclusions, carry no copy of the section,
  and state what they do with an excluded entity: unavailable for any pair, or preferred against
  with item 1a skipped. `midpoint_checkpoint_problems` checks that Module 6 step 9's checkpoint
  records `midpoint_record`.

The checks are pure functions over a file's text, so each one also runs on a mutated copy as its
negative control. `TheChecksCatchARegression` runs nine regressions against every site: the reveal
stated before the 👉, the skip removed, a second 👉 added, the options unnumbered, the grading
guard deleted, the skip recording deleted, the citation dropped, an app route added before the
👉 (each marker alone, and two together), and a copy of the introduction put before the 👉 (#747). The grading guard and the skip recording also run against the shared section.
`TheAlreadyShownEntities` drops each exclusion, case, pointer and site consequence in turn.
Each must make the check report the problem it targets, not merely some problem.

⚠️ **What the derived scan cannot see** (`tests/_pointer_sites.py` says how it reads): a pointer
that names the section in other words, with neither the quoted name "Predictions before results"
nor the `ground-rules.md#predictions-before-results` anchor; a pointer outside `plugins/` or
outside Markdown; the owner's own cross-references inside `ground-rules.md`, which are excluded;
whether INV-357 is the right invariant for what the sentence says; and a sentence cut early at an
abbreviation.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line by
construction; counting lines that *start* with `👉 **` keeps prose that mentions the marker
("the next 👉") from being counted. Phrase checks use `_wrapped_text.match_lines`, which matches
across a wrap.

⛔ **What this cannot establish:** that a live guide holds the result back, asks before loading, or
never grades. Those are properties of a conversation; only `dry-run` phase 3 observes them. This
pins that the skill files STATE them. INV-357 names this file as its enforcer; the grading pattern
requires its citation, and passing it is no evidence that a live run obeys it.

Stdlib only; shipped markdown read as text (INV-108).

Source issues: #479 (part of #465); #507 (the app route and the already-shown entities); #519
(the citation at every pointer); #747 (the introduction before a site's first 👉).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _pointer_sites
import _wrapped_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"
M3_PHASE1 = SKILLS / "module-03-system-verification" / "phase1-verification.md"
M3_PHASE2 = SKILLS / "module-03-system-verification" / "phase2-report-close.md"
DISCOVER = SKILLS / "module-07-query-visualize-discover" / "phase2-discover.md"
MODULE_6_B = SKILLS / "module-06-data-processing" / "phaseB-load-first-source.md"

RULE_HEADING = "## Predictions before results"
MARI_HEADING = "### Step 7a: The Mari Prediction"
PAIRS_HEADING = "### Step 4a-pairs: Same entity or not?"
STEP_4B_HEADING = "### Step 4b: Why Analysis introduction"
OWN_ITEM = "1a. **Own-entity prediction (Truth Set alumni only).**"
OWN_ITEM_END = "\n2. **SDK method introduction:**"
SELECTION_ITEM = "1. **Entity selection:**"
PAIRS_ITEM_1 = "1. **Choose 3 pairs from step 4a's entities.**"
PAIRS_ITEM_2 = "\n2. **Show one pair per turn, then ask.**"

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

#: The pointer every site carries instead of a copy (INV-300), citing the rule (INV-357).
CITATION = (r'stated once in\s+`\.\./bootcamp-onboarding/ground-rules\.md` → "Predictions before '
            r'results"; follow them there\s+rather than a copy here \(INV-300, INV-357\)')
#: The section every pointer names, its anchor, and the invariant each pointer cites (#519).
SECTION, ANCHOR, INVARIANT = ("Predictions before results", "predictions-before-results",
                              "INV-357")
M3_SKILL = SKILLS / "module-03-system-verification" / "SKILL.md"
#: What that pointer must name, so a site cannot quietly drop a clause it defers to.
POINTER_NAMES = {
    "the grading guard": '"informs, never grades"',
    "the skip recording": "the Questions & Responses line",
}

#: What routes the Bootcamper to the visualization app (#507): the checkpoint key that records its
#: port, a URL, a port, or a local address (`localhost`, `127.0.0.1`, `http://`, `https://`). Each
#: is one token, so a wrap cannot split it (INV-346).
APP_ROUTE = re.compile(r"m7_visualizations|\bURL\b|https?://|\blocalhost\b|127\.0\.0\.1|\bport\b",
                       re.IGNORECASE)

#: The one statement of which entities the Discover predictions exclude (#507, INV-300).
SHOWN_ANCHOR = '<a id="already-shown-entities"></a>'
SHOWN_HEADING = "### Already-shown entities"
SHOWN_LINK = "[Already-shown entities](#already-shown-entities)"
#: What the section must state; each key is the problem's wording.
SHOWN_REQUIRED = {
    "the headline entity is excluded": r"\*\*The headline entity:\*\* the entity ID recorded as "
                                       r"`module_7_query\.headline_entity`",
    "the entity holding midpoint_record is excluded": r"\*\*The entity that now holds "
                                                      r"`midpoint_record`:\*\*",
    "the midpoint entity is located by its record": r"Locate its entity with "
                                                    r"`get_entity_by_record_id` on that data source "
                                                    r"and record ID",
    "a none or absent headline_entity excludes nothing": r'When it is `"none"`[^.]* or absent, '
                                                         r"there is no headline exclusion",
    "a none or absent midpoint_record excludes nothing": r'When `midpoint_record` is `"none"` or '
                                                         r"absent[^.]*there is no midpoint "
                                                         r"exclusion",
    "the midpoint entity is never re-derived": r"Do not re-derive it from Module 6's selection "
                                               r"rule",
    "an overlap is one exclusion": r"that is one exclusion, not two",
    "it is the one statement (INV-300)": r"This is the one statement of which entities that "
                                         r"excludes;[^.]*\(INV-300\)",
    "it serves INV-357": r"already seen \(INV-357\)",
}
#: Phrases only that section may carry; a site that holds one has forked it (INV-300).
SHOWN_ONLY = (r"Do not re-derive", r"one exclusion, not two", r"there is no (?:headline|midpoint) "
              r"exclusion", r"Locate its entity with")
#: What each pointing site must state of its own, beside the pointer.
PAIRS_EXCLUSION = {
    "no excluded entity is used for any pair": r"no record of theirs is used for any pair",
    "its limited-data fallback covers what remains": r"the fallback when step 4a cannot supply 3, "
                                                     r"apply to what remains",
}
SELECTION_EXCLUSION = {
    "it prefers an entity that is not excluded": r"Prefer one that is not excluded",
    "item 1a is skipped when only excluded entities qualify": r"When only excluded entities "
                                                              r"qualify, demonstrate one of them "
                                                              r"anyway, and item 1a is skipped",
    "the exclusion is a preference only outside the alumni": r"the exclusion is a preference only",
}

#: Phrases only the shared rule may carry; a site that holds one has forked it (INV-300).
RULE_ONLY = (r"(?i)never say \"correct\"", r"(?i)keep a score", r"\(agreed\)`, or `\(differed\)",
             r"skipped → \{engine's call\}", r"(?i)Introduce it once", r"(?i)agreeing confirms their read")

#: The introduction's bullet in the shared rule (#747), from its bold lead to the next bullet.
INTRO_LEAD = "- **Introduce it once, before the site's first 👉.**"

#: Words that grade a prediction; the introduction carries none of them (#747, INV-357).
GRADING_WORDS = re.compile(r"(?i)\b(?:in)?correct\w*|\bscor(?:e|es|ed|ing)\b|\btall(?:y|ies)\b|"
                           r"\bgrad(?:e|es|ed|ing)\b")


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
        problems.append("%s does not point at the shared rule with INV-300 and %s"
                        % (where, INVARIANT))
    flat = squash(site)
    start = flat.find("This is a prediction point:")
    pointer = flat[start:flat.find("(INV-300", start)] if start >= 0 else ""
    for what, phrase in POINTER_NAMES.items():
        if phrase not in pointer:
            problems.append("%s's pointer does not name %s (%s)" % (where, what, phrase))
    for phrase in RULE_ONLY:
        if match_lines(site, phrase):
            problems.append("%s restates the shared rule (%s)" % (where, phrase))
    return problems


def pointer_citation_problems(texts):
    """Every derived pointer to "Predictions before results" cites INV-357 in its own sentence."""
    return _pointer_sites.uncited_pointers(texts, SECTION, ANCHOR, INVARIANT)


def app_route_problems(where, before):
    """``before`` (the text ahead of a site's 👉) names no route to the visualization app (#507)."""
    found = sorted({m.group(0) for m in APP_ROUTE.finditer(before)}, key=str.lower)
    if found:
        return ["%s routes to the visualization app before its 👉 (%s)" % (where, ", ".join(found))]
    return []


def point_problems(where, step, question, reveal, multi_select=False):
    """The per-site clauses every prediction point shares.

    One 👉 (INV-251), a numbered list of choices beneath it (INV-051), a skip (the last option
    on a single choice, a clause of the 👉 line on a multi-select), the 👉 before the reveal, and
    no route to the visualization app before the 👉 (#507).
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
    problems += app_route_problems(where, step[:ask] if ask >= 0 else step)
    return problems


# --------------------------------------------------------------------------------------------
# The shared rule
# --------------------------------------------------------------------------------------------

def intro_bullet(rule):
    """The introduction's bullet in the shared rule ('' when absent), up to the next bullet."""
    return section(rule, INTRO_LEAD, ("\n- ", "\n\n"))


def intro_problems(rule):
    """The introduction says nothing that grades a prediction (#747)."""
    found = sorted({m.group(0) for m in GRADING_WORDS.finditer(intro_bullet(rule))}, key=str.lower)
    if found:
        return ["the introduction uses a grading word (%s)" % ", ".join(found)]
    return []


def rule_problems(ground_rules):
    rule = section(ground_rules, RULE_HEADING, ("\n## ",))
    if not rule:
        return ["the ground rules have no %r section" % RULE_HEADING]
    problems = []
    required = {
        "the prediction comes before the result": r"⛔ \*\*\(INV-357\) The prediction is asked before the "
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
        "it is never graded": r"⛔ \*\*\(INV-357\) A prediction informs; it is never graded\.\*\*",
        "it is never graded (no correct/incorrect)": r"never say \"correct\" or \"incorrect\"",
        "it is never graded (no score)": r"never keep a score or a tally",
        "it is never graded (no re-ask)": r"and never re-ask\.",
        "the guide does not predict": r"\*\*The guide does not predict\.\*\*",
        "no result means no prediction": r"\*\*No result, no prediction\.\*\*",
        "the Q&R line format": r"`- \*\*\{the 👉 question\}\*\* — \{prediction\} → "
                               r"\{engine's call\}\s*\(agreed\)`, or `\(differed\)`",
        "the skipped line format": r"`- \*\*\{the 👉 question\}\*\* — skipped → \{engine's call\}`",
        "a site is introduced once, before its first 👉": r"\*\*Introduce it once, before the "
                                                          r"site's first 👉\.\*\*",
        "the introduction says why it is asked": r"to commit to an expectation, then compare it "
                                                 r"with the engine's call",
        "the introduction says what agreeing means": r"that agreeing confirms their read",
        "the introduction says what differing means": r"that differing is not a mistake but is "
                                                      r"where the engine's\s+one-line reason is "
                                                      r"most worth reading",
        "the introduction goes ahead of the first 👉": r"It sits ahead of the site's first "
                                                      r"prediction 👉",
        "the introduction is said once per site": r"Say it once per site, not before each pair "
                                                  r"or item",
        "the introduction is not repeated on resume": r"a\s+site resumed after one of its "
                                                      r"predictions is recorded does not repeat it",
        "the introduction hints at no answer": r"it hints at no answer, never says how many "
                                               r"pairs resolved together",
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
    problems += intro_problems(rule)
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
    if step.find(SELECTION_ITEM) > at:
        problems.append("item 1a comes before the entity it predicts about is chosen")
    problems += app_route_problems("step 4b item 1", step[:at])
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
        "its records are shown as text only": r"Show the entity's records before any `why_\*` "
                                              r"call, as text only",
        "the two records are shown as text, feature by feature": r"Show the two records item 1 "
                                                                 r"named as text, feature by "
                                                                 r"feature",
        "it is skipped when item 1 used an excluded entity": r"Skip it as well when item 1 had to "
                                                             r"use an excluded entity",
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
# Discover, the already-shown entities (#507)
# --------------------------------------------------------------------------------------------

def shown_section(discover):
    return section(discover, SHOWN_HEADING, ("\n### ",))


def pairs_item_1(discover):
    return section(pairs_step(discover), PAIRS_ITEM_1, (PAIRS_ITEM_2,))


def selection_item(discover):
    return section(section(discover, STEP_4B_HEADING, ("### Step 4c",)), SELECTION_ITEM,
                   (OWN_ITEM,))


def pointer_site_problems(where, site, own):
    """A site points at the section, names both exclusions, states ``own``, and copies nothing."""
    if not site:
        return ["%s is missing" % where]
    problems = []
    if not match_lines(site, re.escape(SHOWN_LINK) + r" states once \(INV-300\)"):
        problems.append("%s does not point at the already-shown section with INV-300" % where)
    if not match_lines(site, r"\(`headline_entity`\)"):
        problems.append("%s does not name the headline exclusion (headline_entity)" % where)
    if not match_lines(site, r"the entity that holds `midpoint_record`"):
        problems.append("%s does not name the midpoint exclusion (midpoint_record)" % where)
    for what, pattern in own.items():
        if not match_lines(site, pattern):
            problems.append("%s does not state that %s" % (where, what))
    for phrase in SHOWN_ONLY:
        if match_lines(site, phrase):
            problems.append("%s restates the already-shown section (%s)" % (where, phrase))
    return problems


def already_shown_problems(discover):
    """The exclusion is stated once and both Discover predictions point at it (#507, INV-300)."""
    problems = []
    shown = shown_section(discover)
    if not shown:
        problems.append("phase2-discover.md has no %r section" % SHOWN_HEADING)
    else:
        if (SHOWN_ANCHOR + "\n\n" + SHOWN_HEADING) not in discover:
            problems.append("the already-shown section is not anchored for its pointers")
        step_4a = discover.find("### Step 4a: Data pattern analysis")
        at, pairs = discover.find(SHOWN_HEADING), discover.find(PAIRS_HEADING)
        if not 0 <= step_4a < at < pairs:
            problems.append("the already-shown section is not between step 4a and step 4a-pairs")
        for what, pattern in SHOWN_REQUIRED.items():
            if not match_lines(shown, pattern):
                problems.append("the already-shown section does not state that %s" % what)
        if questions(shown):
            problems.append("the already-shown section asks a 👉 question")
    problems += pointer_site_problems("Step 4a-pairs item 1", pairs_item_1(discover),
                                      PAIRS_EXCLUSION)
    problems += pointer_site_problems("step 4b item 1", selection_item(discover),
                                      SELECTION_EXCLUSION)
    for phrase in SHOWN_ONLY:
        if match_lines(own_item(discover), phrase):
            problems.append("step 4b item 1a restates the already-shown section (%s)" % phrase)
    return problems


def midpoint_checkpoint(module_6_b):
    step_9 = section(module_6_b, "## 9. Process redo records", ("\n## 10.",))
    return section(step_9, "**Checkpoint:** write step 9", ("\n\n",))


def midpoint_checkpoint_problems(module_6_b):
    """Module 6 step 9's checkpoint records the midpoint entity by one of its records (#507)."""
    checkpoint = midpoint_checkpoint(module_6_b)
    if not checkpoint:
        return ["Module 6 step 9 has no checkpoint"]
    required = {
        "it records midpoint_record": r"record `midpoint_record` in `config/bootcamp_progress\.json`",
        "the value is one record of the entity": r'the `"<DATA_SOURCE>:<RECORD_ID>"` of the '
                                                 r"midpoint entity's record with the lowest "
                                                 r"`RECORD_ID`",
        "it is none when no entity was shown": r'or `"none"` when this step showed no entity',
        "a record, not an entity ID, identifies it": r"A record identifies the entity across later "
                                                     r"loads, and an entity ID does not",
        "it points at the reader": r"phase2-discover\.md#already-shown-entities",
    }
    return ["Module 6 step 9's checkpoint does not state that %s" % what
            for what, pattern in required.items() if not match_lines(checkpoint, pattern)]


# --------------------------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------------------------

class TheFilesExist(unittest.TestCase):
    def test_every_file_exists(self):
        for path in (GROUND_RULES, COMPLETION, M3_PHASE1, M3_PHASE2, DISCOVER, MODULE_6_B):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path)


class TheRuleIsStatedOnce(unittest.TestCase):
    def test_the_rule_states_every_clause(self):
        self.assertEqual(rule_problems(read(GROUND_RULES)), [])

    def test_the_q_and_r_rule_points_at_it(self):
        flat = squash(read(COMPLETION))
        self.assertRegex(
            flat, r'its format is stated once in `ground-rules\.md` → "Predictions before '
                  r'results" \(INV-300, INV-357\)',
            "module-completion's Questions & Responses rule does not point at the line format")

    def test_negative_control_a_removed_clause_is_reported(self):
        text = read(GROUND_RULES).replace("hold its outcome back", "show it")
        self.assertIn("the rule does not state that an already-run result is held back",
                      rule_problems(text))


class EveryPointerCitesTheRule(unittest.TestCase):
    """The pointer sites are derived by scan (INV-246), so a later one without INV-357 fails."""

    def test_every_pointer_cites_inv_357(self):
        self.assertEqual([], pointer_citation_problems(_pointer_sites.shipped_texts()))

    def test_the_scan_finds_every_known_site(self):
        """Not vacuous: the derived set holds each file whose pointer this guard knows."""
        found = [path for path, _, _ in _pointer_sites.pointers(
            _pointer_sites.shipped_texts(), SECTION, ANCHOR)]
        for path, count in ((M3_SKILL, 1), (M3_PHASE1, 2), (DISCOVER, 2), (COMPLETION, 1)):
            with self.subTest(path=path.name):
                self.assertGreaterEqual(found.count(path), count)

    def test_system_verification_cites_only_the_rule(self):
        """Its two statements make no single-statement claim, so INV-300 is not added (#519)."""
        for path, pattern in (
                (M3_SKILL, r'decides \(the ground rules\' "Predictions before results", '
                           r'INV-357\)\.'),
                (M3_PHASE1, r'predicts nothing \(the ground rules\' "Predictions before results", '
                            r'INV-357\)\.')):
            with self.subTest(path=path.name):
                self.assertTrue(match_lines(read(path), pattern))
                self.assertFalse(match_lines(read(path), r'"Predictions before results", '
                                                         r'INV-300'))

    def test_negative_control_each_derived_pointer_loses_its_citation(self):
        """Every shipped pointer (six since #519), in turn, is reported when it drops INV-357."""
        shipped = _pointer_sites.shipped_texts()
        sites = _pointer_sites.pointers(shipped, SECTION, ANCHOR)
        self.assertGreaterEqual(len(sites), 6, "the scan went blind")
        for path, line, _ in sites:
            with self.subTest(site="%s:%d" % (path.name, line)):
                problems = pointer_citation_problems(
                    _pointer_sites.without_citation(shipped, path, line, INVARIANT))
                where = "%s:%d" % (path.relative_to(REPO_ROOT).as_posix(), line)
                self.assertTrue(any(where in p for p in problems), problems)

    def test_negative_control_a_new_pointer_site_without_the_citation(self):
        """A site no list names: the scan finds it by the section's name, wrapped (INV-346)."""
        texts = _pointer_sites.shipped_texts()
        texts[SKILLS / "graduation" / "new-step.md"] = (
            "This is a prediction point, stated once in `ground-rules.md` → \"Predictions\n"
            "before results\"; follow them there rather than a copy here (INV-300).\n")
        self.assertTrue(any("graduation/new-step.md:1" in p
                            for p in pointer_citation_problems(texts)))


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

    def test_negative_control_the_old_app_route_restored(self):
        """The route #507 removed, put back word for word, is reported, and so is losing "text only"."""
        item = own_item(self.discover)
        start = item.index("   - **Show the entity's records")
        end = item.index("   - **The options are")
        old = ("   - **Show the entity's records before any `why_*` call.** When step 3c built the "
               "visualization app\n     and its server is still running (`m7_visualizations` records "
               "a port), give its URL and the\n     entity ID to open there. Otherwise show the two "
               "records item 1 named as text, feature by\n     feature.\n")
        problems = own_entity_problems(self.discover.replace(item, item[:start] + old + item[end:]))
        self.assertIn("step 4b item 1a routes to the visualization app before its 👉 "
                      "(m7_visualizations, port, URL)", problems)
        self.assertIn("item 1a does not state that its records are shown as text only", problems)

    def test_negative_control_a_route_in_item_1(self):
        """Item 1 sits before item 1a's 👉, so a route there leaks the answer too."""
        item = selection_item(self.discover)
        mutated = item.replace("State what you are using:",
                               "Give the Bootcamper the app's URL for it. State what you are using:")
        self.assertNotEqual(mutated, item)
        self.assertIn("step 4b item 1 routes to the visualization app before its 👉 (URL)",
                      own_entity_problems(self.discover.replace(item, mutated)))


class TheAlreadyShownEntities(unittest.TestCase):
    """#507: the exclusion is stated once, both predictions point at it, Module 6 records it.

    In the style of `TheChecksCatchARegression`: each control mutates one clause and asserts the
    problem that clause's check reports, not merely some problem.
    """

    def setUp(self):
        self.discover = read(DISCOVER)
        self.module_6_b = read(MODULE_6_B)

    def test_the_exclusion_is_stated_once_and_both_sites_point_at_it(self):
        self.assertEqual(already_shown_problems(self.discover), [])

    def test_module_6_step_9_records_midpoint_record(self):
        self.assertEqual(midpoint_checkpoint_problems(self.module_6_b), [])

    def assertCaught(self, cut, old, new, expected, problems_of=already_shown_problems, text=None):
        text = self.discover if text is None else text
        part = cut(text)
        self.assertTrue(part, "the section the control mutates is missing")
        mutated = re.sub(old, new, part, count=1)
        self.assertNotEqual(mutated, part, "the mutation did not change it: %r" % old)
        problems = problems_of(text.replace(part, mutated))
        self.assertTrue(any(p.startswith(expected) for p in problems),
                        "%r went unnoticed: %r" % (expected, problems))

    def test_the_headline_exclusion_dropped_from_the_section(self):
        self.assertCaught(shown_section, r"`module_7_query\.headline_entity`", "the entity",
                          "the already-shown section does not state that the headline entity is "
                          "excluded")

    def test_the_midpoint_exclusion_dropped_from_the_section(self):
        self.assertCaught(shown_section, _loose("**The entity that now holds `midpoint_record`:**"),
                          "**Another entity:**",
                          "the already-shown section does not state that the entity holding "
                          "midpoint_record is excluded")

    def test_the_lookup_by_record_dropped(self):
        self.assertCaught(shown_section, _loose("Locate its entity with `get_entity_by_record_id`"),
                          "Reuse its entity ID",
                          "the already-shown section does not state that the midpoint entity is "
                          "located by its record")

    def test_the_none_cases_dropped(self):
        for old, wanted in (("there is no headline\nexclusion", "a none or absent headline_entity"),
                            ("there is no midpoint exclusion", "a none or absent midpoint_record")):
            with self.subTest(case=wanted):
                self.assertCaught(shown_section, _loose(old), "exclude it anyway",
                                  "the already-shown section does not state that %s" % wanted)

    def test_the_re_derivation_allowed(self):
        self.assertCaught(shown_section, _loose("Do not re-derive it from Module 6's selection rule."),
                          "Re-derive it from Module 6's selection rule.",
                          "the already-shown section does not state that the midpoint entity is "
                          "never re-derived")

    def test_the_overlap_counted_twice(self):
        self.assertCaught(shown_section, _loose("that is one exclusion, not two"),
                          "that is two exclusions",
                          "the already-shown section does not state that an overlap is one "
                          "exclusion")

    SITES = (("Step 4a-pairs item 1", pairs_item_1), ("step 4b item 1", selection_item))

    def test_a_pointer_dropped(self):
        for where, cut in self.SITES:
            with self.subTest(site=where):
                self.assertCaught(cut, _loose(SHOWN_LINK + " states once (INV-300)"), "this",
                                  "%s does not point at the already-shown section" % where)

    def test_an_exclusion_dropped_at_a_site(self):
        for where, cut in self.SITES:
            for old, wanted in (("(`headline_entity`)", "the headline exclusion"),
                                ("the entity that holds `midpoint_record`", "the midpoint exclusion")):
                with self.subTest(site=where, exclusion=wanted):
                    self.assertCaught(cut, _loose(old), "another entity",
                                      "%s does not name %s" % (where, wanted))

    def test_a_site_restates_the_section(self):
        for where, cut in self.SITES:
            with self.subTest(site=where):
                self.assertCaught(cut, _loose("states once (INV-300)"),
                                  "states once (INV-300). Do not re-derive it",
                                  "%s restates the already-shown section" % where)

    def test_the_pairs_consequence_dropped(self):
        self.assertCaught(pairs_item_1, _loose("no record of theirs is used for any pair"),
                          "avoid them where you can",
                          "Step 4a-pairs item 1 does not state that no excluded entity is used")

    def test_the_selection_preference_dropped(self):
        self.assertCaught(selection_item, _loose("Prefer one that is not excluded"),
                          "Any will do",
                          "step 4b item 1 does not state that it prefers an entity that is not "
                          "excluded")

    def test_the_item_1a_skip_dropped(self):
        self.assertCaught(selection_item, _loose("and item 1a is skipped"), "",
                          "step 4b item 1 does not state that item 1a is skipped")
        self.assertCaught(own_item, _loose("**Skip it as well when item 1 had to use an excluded "
                                           "entity**"), "**Keep it**",
                          "item 1a does not state that it is skipped when item 1 used an excluded "
                          "entity", problems_of=own_entity_problems)

    def test_the_section_removed(self):
        text = self.discover.replace(shown_section(self.discover), "")
        self.assertIn("phase2-discover.md has no %r section" % SHOWN_HEADING,
                      already_shown_problems(text))

    def test_the_checkpoint_forgets_midpoint_record(self):
        for old, wanted in (("record `midpoint_record`", "it records midpoint_record"),
                            ('`"none"` when this step', "it is none when no entity was shown"),
                            ("lowest `RECORD_ID`", "the value is one record of the entity")):
            with self.subTest(clause=wanted):
                self.assertCaught(midpoint_checkpoint, _loose(old), "something",
                                  "Module 6 step 9's checkpoint does not state that %s" % wanted,
                                  problems_of=midpoint_checkpoint_problems, text=self.module_6_b)


def _loose(phrase):
    """``phrase`` as a regex that matches across a line wrap."""
    return r"\s+".join(re.escape(word) for word in phrase.split())


class TheChecksCatchARegression(unittest.TestCase):
    """Nine regressions, each run against every site; each must report the problem it targets.

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
        self.check(lambda s, q, r: s.replace("(INV-300, INV-357)", ""),
                   " does not point at the shared rule with INV-300")

    def test_the_rule_citation_dropped(self):
        self.check(lambda s, q, r: s.replace("(INV-300, INV-357)", "(INV-300)"),
                   " does not point at the shared rule with INV-300 and INV-357")

    #: (a route to the visualization app, the markers it must be reported by). Each form but the
    #: last carries one marker alone, so a marker dropped from `APP_ROUTE` fails its own subtest.
    ROUTES = (
        ("Open it in the app recorded in `m7_visualizations`.", "m7_visualizations"),
        ("Give its URL and the entity ID to open there.", "URL"),
        ("The app is on the port step 3c recorded.", "port"),
        ("Open localhost in a browser and find the entity.", "localhost"),
        ("Open 127.0.0.1 in a browser and find the entity.", "127.0.0.1"),
        ("Open http://viz.example and find the entity.", "http://"),
        ("Open https://viz.example and find the entity.", "https://"),
        ("Open http://localhost:8080 to see it.", "http://, localhost"),
    )

    def test_an_app_route_added_before_the_question(self):
        """#507: each marker of a route to the visualization app, put ahead of each site's 👉."""
        for route, markers in self.ROUTES:
            with self.subTest(route=route):
                self.check(lambda s, q, r: s.replace(q, "%s\n\n%s" % (route, q), 1),
                           " routes to the visualization app before its 👉 (%s)" % markers)

    def _rule_check(self, pattern, expected):
        text = read(GROUND_RULES)
        self.assertEqual(rule_problems(text), [], "the shared rule fails before the mutation")
        mutated = re.sub(pattern, "", text, count=1, flags=re.S)
        self.assertNotEqual(mutated, text, "the mutation did not change the shared rule")
        problems = rule_problems(mutated)
        self.assertTrue(any(p.startswith(expected) for p in problems),
                        "%r went unnoticed: %r" % (expected, problems))

    def test_the_grading_guard_removed_from_the_shared_rule(self):
        self._rule_check(r"- ⛔ \*\*\(INV-357\) A prediction informs; it is never graded\.\*\*.*?(?=\n- )",
                         "the rule does not state that it is never graded")

    def test_the_grading_guard_softened_in_the_shared_rule(self):
        self._rule_check(r"never keep a score or a tally, ",
                         "the rule does not state that it is never graded (no score)")

    def test_the_skip_recording_removed_from_the_shared_rule(self):
        self._rule_check(r";\s+a skip is `- \*\*\{the 👉 question\}\*\* — skipped → [^`]*`",
                         "the rule does not state that the skipped line format")

    def test_a_site_carries_its_own_copy_of_the_introduction(self):
        """#747: the introduction is stated once; a site-local copy is a fork (INV-300)."""
        rule = section(read(GROUND_RULES), RULE_HEADING, ("\n## ",))
        copy = intro_bullet(rule).strip()
        self.assertTrue(copy, "the shared rule has no introduction, so the control would be vacuous")
        self.check(lambda s, q, r: s.replace(q, "%s\n\n%s" % (copy, q), 1),
                   " restates the shared rule (")


class TheIntroduction(unittest.TestCase):
    """#747: the shared rule requires a one-time introduction before a site's first 👉."""

    def setUp(self):
        self.text = read(GROUND_RULES)
        self.rule = section(self.text, RULE_HEADING, ("\n## ",))

    def test_the_rule_carries_the_introduction(self):
        self.assertTrue(intro_bullet(self.rule), "the shared rule has no introduction bullet")
        self.assertEqual(intro_problems(self.rule), [])

    def test_the_bullet_stops_at_the_next_one(self):
        """Anti-vacuity: the cut holds the whole bullet and none of the grading guard after it."""
        bullet = intro_bullet(self.rule)
        self.assertIn("next bullet", squash(bullet))
        self.assertNotIn("A numbered choice", bullet)
        self.assertNotIn('never say "correct"', bullet)

    def test_the_grading_words_are_caught(self):
        """Each grading word the introduction must not carry is reported, not merely some."""
        for word in ("correct", "incorrect", "score", "scored", "tally", "graded"):
            with self.subTest(word=word):
                mutated = self.text.replace(
                    "that agreeing confirms their read",
                    "that agreeing means they are %s" % word, 1)
                self.assertNotEqual(mutated, self.text)
                problems = rule_problems(mutated)
                self.assertTrue(any(p.startswith("the introduction uses a grading word (%s"
                                                 % word) for p in problems),
                                "%r went unnoticed: %r" % (word, problems))

    def test_negative_control_the_introduction_removed(self):
        mutated = self.text.replace(intro_bullet(self.rule), "", 1)
        self.assertNotEqual(mutated, self.text)
        self.assertIn("the rule does not state that a site is introduced once, before its first 👉",
                      rule_problems(mutated))

    def test_negative_control_each_clause_removed(self):
        for phrase, wanted in (
                ("to commit to an expectation, then compare it with the engine's call",
                 "the introduction says why it is asked"),
                ("that agreeing confirms their read", "the introduction says what agreeing means"),
                ("that differing is not a mistake", "the introduction says what differing means"),
                ("Say it once per site, not before each pair or item",
                 "the introduction is said once per site"),
                ("does not repeat it", "the introduction is not repeated on resume")):
            with self.subTest(clause=wanted):
                mutated = re.sub(_loose(phrase), "something", self.text, count=1)
                self.assertNotEqual(mutated, self.text)
                self.assertIn("the rule does not state that %s" % wanted, rule_problems(mutated))


if __name__ == "__main__":
    unittest.main()
