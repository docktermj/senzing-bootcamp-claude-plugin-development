"""Each Act 2 hands-on module shows one worked steer when the AI's first attempt fails (#484).

Before #484 a Bootcamper never saw the AI go wrong and get steered back: when the AI's first
attempt failed, the guide fixed it out of sight, and INV-012's suppression of output that is not
important to the Bootcamper pushed the same way. So they could not learn how to steer it. #484
adds a worked steer: at most one per module, in two lines (what went wrong and what gave it away,
then what the AI was asked to change), fired only by a named trigger. From Data processing on,
the guide first asks the Bootcamper what they would ask the AI to change.

**One shared rule, cited (INV-300).** The rule is stated once, in `ground-rules.md` → "Worked
steers". Each of the four Act 2 hands-on modules (Data collection; Data Quality, Mapping, and
Transformation; Data processing; Query, Visualize and Discover) points there from its `SKILL.md`
and holds no copy. Act 1 (up to and including Truth Set visualization) does not cite it.

So the clauses are checked where they live:

- **In the shared section** (`rule_problems`): the triggers, at most one per module, never
  staged, the two-line shape, the evidence source, the statement form before Data processing, the
  pinned ask-first 👉 and the handling of its answer, the question already due, minimal verbosity
  (INV-214) and the checkpoint note.
- **Per module** (`citation_problems`): the pointer with INV-300 and INV-352, the form that
  module uses (statement, or ask first), and no copy of a rule-only clause.
- **At every pointer, derived** (`pointer_citation_problems`, #519): every shipped sentence that
  points at "Worked steers", found by scan rather than from `ACT2` (INV-246), cites INV-352, so a
  reader at the pointer can name the rule as well as the single-statement discipline.
- **Act 1** (`act1_problems`): no mention of the rule and no copy of its question.
- **The silent-filing section** (`cross_reference_problems`): the one-line cross-reference, which
  keeps the filing silent and shows the steer.

The checks are pure functions over a file's text, so each also runs on a mutated copy as its
negative control (`TheChecksCatchARegression`). Each mutation must make the check report the
problem it targets, not merely some problem.

⚠️ **What the derived scan cannot see** (`tests/_pointer_sites.py` says how it reads): a pointer
that names the section in other words, with neither the quoted name "Worked steers" nor the
`ground-rules.md#worked-steers` anchor; a pointer outside `plugins/` or outside Markdown; the
owner's own cross-references inside `ground-rules.md`, which are excluded; whether INV-352 is
the right invariant for what the sentence says; and a sentence cut early at an abbreviation.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** The pinned question sits on its own
line inside backticks; counting lines that contain the full question keeps prose that mentions
"the ask-first 👉" from being counted. Phrase checks use `_wrapped_text.match_lines`, which matches
across a wrap.

⛔ **What this cannot establish:** that a live guide shows the steer, asks first, or writes the
checkpoint line. INV-352 names this file as its enforcer; the three ⛔ patterns above require its
citation, and passing them is no evidence that a live run obeys it. Those are properties of a
conversation; only `dry-run` phase 3 observes them. This pins that the skill files STATE them.

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #484 (part of #465); the citation at every pointer, #519.

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

RULE_HEADING = "## Worked steers"
SILENT_HEADING = "## Reversed decisions: file them when they happen (silent)"

#: The pinned ask-first question (INV-247), stated once in the shared rule.
QUESTION = "👉 **What would you ask the AI to change to fix this? Say it in your own words.**"

#: Act 2 hands-on modules, each with the form its steer takes.
STATEMENT, ASK_FIRST = "statement", "ask first"
ACT2 = {
    "module-04-data-collection": STATEMENT,
    "module-05-data-quality-mapping": STATEMENT,
    "module-06-data-processing": ASK_FIRST,
    "module-07-query-visualize-discover": ASK_FIRST,
}
#: Act 1: up to and including Truth Set visualization.
ACT1 = ("module-00-entity-resolution-concepts", "module-01-business-problem",
        "module-02-sdk-setup", "module-03-system-verification",
        "module-03b-truthset-visualization")

#: The pointer every Act 2 module carries instead of a copy (INV-300), citing the rule (INV-352).
CITATION = (r'stated once in\s+`\.\./bootcamp-onboarding/ground-rules\.md` → "Worked steers"; '
            r'follow them there rather than a copy\s+here \(INV-300, INV-352\)')
#: The section every pointer names, its anchor, and the invariant each pointer cites (#519).
SECTION, ANCHOR, INVARIANT = "Worked steers", "worked-steers", "INV-352"
#: What that pointer must name, so a module cannot quietly drop a clause it defers to.
POINTER_NAMES = ("What fires it", "its two lines", "at most one per module", "minimal verbosity",
                 "the checkpoint note")
FORM = {
    STATEMENT: r"Before Data processing it is a statement and adds no 👉",
    ASK_FIRST: r"ask first: the pinned ask-first 👉 comes before the fix, and it may end a turn "
               r"in a step\s+this module says asks nothing",
}

#: Phrases only the shared rule may carry; a module that holds one has forked it (INV-300).
RULE_ONLY = (r"What went wrong: \{", r"What the AI was asked to change: \{",
             r"Worked steer shown:", r"never stage a failure", r"The trigger is a named condition",
             re.escape(QUESTION[len("👉 **"):-2]))

RULE_REQUIRED = {
    "the Act 2 hands-on modules are named":
        r"the Act 2 hands-on modules are Data collection; Data Quality, Mapping, and "
        r"Transformation; Data processing; and Query, Visualize and Discover",
    "Act 1 shows none": r"Act 1, up to and including Truth Set visualization, keeps its first "
                        r"impressions guarded and shows none",
    "it is the one statement (INV-300)": r"This section is the one statement of how every worked "
                                         r"steer works; each of those modules points here and "
                                         r"holds no copy \(INV-300\)",
    "the trigger is a named condition": r"⛔ \*\*\(INV-352\) The trigger is a named condition, not a "
                                        r"disposition\.\*\*",
    "trigger 1: generated code fails when run": r"\*\*Code the AI generated fails when it runs:\*\* "
                                                r"a non-zero exit, an exception, or an `EMPTY` "
                                                r"line",
    "trigger 2: an engine-output audit withdraws a decision":
        r"\*\*An audit of the engine's own output withdraws a decision the AI made:\*\* any of "
        r"the three triggers under \"Reversed decisions: file them when they happen \(silent\)\"",
    "an unfixed failure is no steer": r"A failure the guide does not fix is not a steer",
    "at most one, only the first": r"\*\*At most one per module, and only the first\.\*\*",
    "later failures are fixed as before": r"every later failure in the module is fixed as before, "
                                          r"without a steer",
    "zero is allowed": r"\"At most one\" allows zero: a module with no failure shows nothing",
    "a failure is never staged": r"⛔ \*\*\(INV-352\) Never stage a failure to have one to show\.\*\*",
    "two lines": r"\*\*Two lines, after the fix\.\*\*",
    "the first line's shape": r"What went wrong: \{what failed, in plain words\} — given away by "
                              r"\{the evidence, quoted from the output",
    "the second line's shape": r"What the AI was asked to change: \{the request that fixed it\}\.",
    "the evidence is the tool's or engine's output (INV-080)":
        r"The evidence comes from the tool's or the engine's own output, never from the guide's "
        r"reasoning \(INV-080\)",
    "the steer is non-yielding (INV-225)": r"so it is non-yielding \(INV-225\)",
    "before Data processing it is a statement": r"\*\*Before Data processing\*\* \(Data "
                                                r"collection; Data Quality, Mapping, and "
                                                r"Transformation\), the steer is that statement "
                                                r"and nothing more\. It adds no 👉 question",
    "from Data processing on, ask first": r"\*\*From Data processing on\*\* \(Data processing; "
                                          r"Query, Visualize and Discover\), ask first\. Before "
                                          r"fixing the failure",
    "the question is pinned and the only 👉 (INV-247, INV-251)":
        r"pinned here \(INV-247\) and the turn's only 👉 \(INV-251\)",
    "the guide writes the code": r"⛔ \*\*\(INV-352\) The Bootcamper answers in words; the guide writes every "
                                 r"line of code\*\*",
    "a request that works is used": r"\*\*Their request would work:\*\* the AI makes that change, "
                                    r"and the steer's second line says so",
    "the used-request form": r"\{their request\}, as you asked\.",
    "otherwise the guide fixes it anyway": r"\*\*It would not, or they are not sure\*\*",
    "not sure is named": r"\(\"not sure\", \"you pick\", \"I don't know\"",
    "the differs clause": r"one clause on\s+how its request differed from theirs: `… — that "
                          r"differs from yours in \{one clause\}\.`",
    "never graded": r"A request that would not work is a finding, not a grade",
    "never asked twice (INV-006)": r"⛔ \*\*Never ask twice for the same failure\*\* \(INV-006\)",
    "the question already due": r"\*\*A question already due\.\*\* When the failure surfaces on a "
                                r"turn that would end on another 👉 question, the ask-first "
                                r"question takes that turn and the other question moves to the "
                                r"next turn",
    "an asks-nothing step may carry it": r"A step its module says \"asks nothing\" can therefore "
                                         r"carry this one 👉",
    "required output at every verbosity": r"\*\*Required output, at every verbosity\.\*\* The "
                                          r"steer is never dropped",
    "minimal merges with '; ' (INV-214)": r"Under\s+\*\*minimal\*\* its two lines merge onto one "
                                          r"line, joined with `; ` \(INV-214\)",
    "the checkpoint note": r"one line to `docs/progress/recap_checkpoint\.md`'s \*\*Actions "
                           r"Taken\*\*:\s+`- Worked steer shown: \{the steer, merged onto one "
                           r"line\}`",
    "a resume shows no second steer": r"checkpoint that already carries a `Worked steer shown:` "
                                      r"line for this\s+module means the steer was shown: show no "
                                      r"second one",
}


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


def question_lines(text):
    """Lines carrying the full pinned question (see the module docstring for why lines)."""
    return [line for line in text.splitlines() if QUESTION in line]


def all_skill_texts():
    return {p: read(p) for p in sorted(SKILLS.rglob("*.md"))}


# --------------------------------------------------------------------------------------------
# The shared rule
# --------------------------------------------------------------------------------------------

def rule_problems(ground_rules):
    rule = section(ground_rules, RULE_HEADING, ("\n## ",))
    if not rule:
        return ["the ground rules have no %r section" % RULE_HEADING]
    problems = []
    if '<a id="worked-steers"></a>' not in ground_rules:
        problems.append("the ground rules do not anchor the section")
    directing = ground_rules.find("## Directing steps")
    gates = ground_rules.find("## Mandatory gates and step order")
    here = ground_rules.find(RULE_HEADING)
    if not 0 <= directing < here < gates:
        problems.append("the section does not sit between \"Directing steps\" and \"Mandatory "
                        "gates and step order\"")
    for what, pattern in RULE_REQUIRED.items():
        if not match_lines(rule, pattern):
            problems.append("the rule does not state that %s" % what)
    if len(question_lines(rule)) != 1:
        problems.append("the rule does not pin the ask-first 👉 exactly once (%d)"
                        % len(question_lines(rule)))
    body = QUESTION[len("👉 **"):]
    if re.search(r"\bor\b", body):
        problems.append("the ask-first 👉 joins choices with 'or' (INV-051)")
    fence = section(rule, "```text\n", ("\n  ```\n",))
    if len([line for line in fence.splitlines()[1:] if line.strip()]) != 2:
        problems.append("the steer's template is not two lines")
    return problems


def question_once_problems(texts):
    """The pinned question appears in the shared rule and nowhere else (INV-300, INV-247)."""
    problems = []
    for path, text in texts.items():
        if path.name == "ground-rules.md":
            continue
        if question_lines(text):
            problems.append("%s carries a copy of the ask-first 👉" % path.relative_to(SKILLS))
    return problems


# --------------------------------------------------------------------------------------------
# The Act 2 citations and Act 1's absence
# --------------------------------------------------------------------------------------------

def citation_problems(skill, where, form):
    """A module points at the shared rule, names what it defers to, and carries no copy."""
    problems = []
    if not match_lines(skill, CITATION):
        problems.append("%s does not point at the shared rule with INV-300 and %s"
                        % (where, INVARIANT))
    flat = squash(skill)
    start = flat.find("**Worked steer.**")
    pointer = flat[start:flat.find("(INV-300", start)] if start >= 0 else ""
    for phrase in POINTER_NAMES:
        if phrase not in pointer:
            problems.append("%s's pointer does not name %s" % (where, phrase))
    if not match_lines(skill, FORM[form]):
        problems.append("%s does not state its %s form" % (where, form))
    other = ASK_FIRST if form == STATEMENT else STATEMENT
    if match_lines(skill, FORM[other]):
        problems.append("%s states the %s form, which is not its own" % (where, other))
    return problems


def copy_problems(text, where):
    return ["%s restates the shared rule (%s)" % (where, phrase)
            for phrase in RULE_ONLY if match_lines(text, "(?i)" + phrase)]


def act1_problems(text, where):
    problems = []
    if re.search(r"(?i)worked steer", text):
        problems.append("%s mentions the worked steer, which Act 1 does not show" % where)
    if question_lines(text):
        problems.append("%s carries the ask-first 👉" % where)
    return problems


def pointer_citation_problems(texts):
    """Every derived pointer to "Worked steers" cites INV-352 in its own sentence (#519)."""
    return _pointer_sites.uncited_pointers(texts, SECTION, ANCHOR, INVARIANT)


# --------------------------------------------------------------------------------------------
# The silent-filing cross-reference
# --------------------------------------------------------------------------------------------

def cross_reference_problems(ground_rules):
    silent = section(ground_rules, SILENT_HEADING, ("\n## ",))
    if not silent:
        return ["the ground rules have no silent-filing section"]
    problems = []
    if not match_lines(silent, r"\*\*The same reversal can also be the module's worked steer\*\* "
                               r"\(see \"Worked steers\" above\): the filing stays silent, and "
                               r"the steer is shown\."):
        problems.append("the silent-filing section has no cross-reference to the worked steer")
    if not match_lines(silent, r"\*\*Silent\.\*\* No banners, no 👉 question, no announcement "
                               r"\(INV-012\)"):
        problems.append("the silent-filing section no longer keeps the filing silent")
    if ground_rules.find(RULE_HEADING) > ground_rules.find(SILENT_HEADING):
        problems.append("\"Worked steers\" is not above the silent-filing section it is cited "
                        "from as \"above\"")
    return problems


# --------------------------------------------------------------------------------------------
# Tests on the shipped files
# --------------------------------------------------------------------------------------------

class TheSharedRuleIsStatedOnce(unittest.TestCase):
    def test_the_rule_states_every_clause(self):
        self.assertEqual([], rule_problems(read(GROUND_RULES)))

    def test_the_question_is_pinned_only_in_the_rule(self):
        self.assertEqual([], question_once_problems(all_skill_texts()))

    def test_no_other_skill_file_restates_the_rule(self):
        problems = []
        for path, text in all_skill_texts().items():
            if path.name != "ground-rules.md":
                problems += copy_problems(text, str(path.relative_to(SKILLS)))
        self.assertEqual([], problems)


class EachAct2ModuleCitesIt(unittest.TestCase):
    def test_each_act2_module_skill_cites_the_rule(self):
        for module, form in ACT2.items():
            with self.subTest(module=module):
                skill = read(SKILLS / module / "SKILL.md")
                self.assertEqual([], citation_problems(skill, module, form))

    def test_each_act2_module_cites_it_once(self):
        for module in ACT2:
            with self.subTest(module=module):
                count = sum(len(match_lines(read(p), CITATION))
                            for p in sorted((SKILLS / module).glob("*.md")))
                self.assertEqual(1, count)


class EveryPointerCitesTheRule(unittest.TestCase):
    """The pointer sites are derived by scan (INV-246), so a later one without INV-352 fails."""

    def test_every_pointer_cites_inv_352(self):
        self.assertEqual([], pointer_citation_problems(_pointer_sites.shipped_texts()))

    def test_the_scan_finds_every_act2_pointer(self):
        """Not vacuous: the derived set holds each module's known pointer."""
        found = {path for path, _, _ in _pointer_sites.pointers(
            _pointer_sites.shipped_texts(), SECTION, ANCHOR)}
        for module in ACT2:
            with self.subTest(module=module):
                self.assertIn(SKILLS / module / "SKILL.md", found)


class Act1KeepsItsBehavior(unittest.TestCase):
    def test_no_act1_module_cites_the_rule(self):
        problems = []
        for module in ACT1:
            files = sorted((SKILLS / module).glob("*.md"))
            self.assertTrue(files, "%s has no skill files: the scan would be vacuous" % module)
            for path in files:
                problems += act1_problems(read(path), str(path.relative_to(SKILLS)))
        self.assertEqual([], problems)

    def test_act1_and_act2_cover_every_module_directory(self):
        """A module added later must be placed in one act, or this guard silently skips it."""
        modules = {p.name for p in SKILLS.iterdir() if p.is_dir() and p.name.startswith("module-")}
        self.assertEqual(modules, set(ACT1) | set(ACT2))


class TheSilentFilingSectionCrossReferences(unittest.TestCase):
    def test_the_cross_reference(self):
        self.assertEqual([], cross_reference_problems(read(GROUND_RULES)))


# --------------------------------------------------------------------------------------------
# Negative controls
# --------------------------------------------------------------------------------------------

class TheChecksCatchARegression(unittest.TestCase):
    """Each mutation must produce the problem it targets."""

    def assertReports(self, problems, needle):
        self.assertTrue(any(needle in p for p in problems),
                        "expected a problem containing %r, got %r" % (needle, problems))

    # --- the shared rule ---------------------------------------------------------------------

    def test_rule_with_a_disposition_trigger(self):
        text = read(GROUND_RULES).replace("The trigger is a named condition, not a disposition.",
                                          "Show a steer whenever something seems off.")
        self.assertReports(rule_problems(text), "the trigger is a named condition")

    def test_rule_that_stages_a_failure(self):
        text = read(GROUND_RULES).replace("Never stage a failure to have one to show.",
                                          "Stage one if none arises.")
        self.assertReports(rule_problems(text), "a failure is never staged")

    def test_rule_dropped_under_minimal(self):
        text = read(GROUND_RULES).replace("The steer is never dropped as explanatory output.",
                                          "Under minimal the steer is dropped.")
        self.assertReports(rule_problems(text), "required output at every verbosity")

    def test_rule_without_the_checkpoint_note(self):
        text = read(GROUND_RULES).replace("`- Worked steer shown: {the steer, merged onto one "
                                          "line}`", "a note")
        self.assertReports(rule_problems(text), "the checkpoint note")

    def test_rule_asks_twice(self):
        text = read(GROUND_RULES).replace("Never ask twice for the same failure",
                                          "Ask again for the same failure")
        self.assertReports(rule_problems(text), "never asked twice")

    def test_rule_without_the_question_already_due(self):
        text = read(GROUND_RULES).replace("the ask-first question takes that turn",
                                          "both questions take that turn")
        self.assertReports(rule_problems(text), "the question already due")

    def test_rule_with_a_three_line_template(self):
        text = read(GROUND_RULES).replace(
            "  What the AI was asked to change: {the request that fixed it}.\n",
            "  What the AI was asked to change: {the request that fixed it}.\n  Lesson: {…}.\n")
        self.assertReports(rule_problems(text), "not two lines")

    def test_rule_moved_after_the_gates(self):
        text = read(GROUND_RULES)
        rule = section(text, "<a id=\"worked-steers\"></a>", ("## Mandatory gates",))
        text = text.replace(rule, "").replace("## File placement", rule + "## File placement")
        self.assertReports(rule_problems(text), "does not sit between")

    def test_question_with_or(self):
        global QUESTION
        saved = QUESTION
        try:
            QUESTION = saved.replace("to fix this?", "to fix this or skip it?")
            text = read(GROUND_RULES).replace(saved, QUESTION)
            self.assertReports(rule_problems(text), "joins choices with 'or'")
        finally:
            QUESTION = saved

    def test_question_copied_into_a_module(self):
        texts = all_skill_texts()
        target = SKILLS / "module-06-data-processing" / "SKILL.md"
        texts[target] = texts[target] + "\n" + QUESTION + "\n"
        self.assertReports(question_once_problems(texts), "carries a copy of the ask-first 👉")

    # --- the Act 2 citations -----------------------------------------------------------------

    def test_module_pointer_dropped(self):
        skill = read(SKILLS / "module-04-data-collection" / "SKILL.md").replace(
            "here (INV-300, INV-352).\n\n⚠️ **On the generated",
            "here.\n\n⚠️ **On the generated")
        self.assertReports(citation_problems(skill, "m4", STATEMENT),
                           "does not point at the shared rule")

    def test_module_pointer_without_inv_352(self):
        skill = read(SKILLS / "module-04-data-collection" / "SKILL.md").replace(
            "(INV-300, INV-352)", "(INV-300)")
        self.assertReports(citation_problems(skill, "m4", STATEMENT),
                           "does not point at the shared rule")

    # --- the derived pointer sites (#519) ----------------------------------------------------

    def test_each_derived_pointer_loses_its_citation(self):
        """Every shipped pointer (four since #519), in turn, is reported when it drops INV-352."""
        shipped = _pointer_sites.shipped_texts()
        sites = _pointer_sites.pointers(shipped, SECTION, ANCHOR)
        self.assertGreaterEqual(len(sites), 4, "the scan went blind")
        for path, line, _ in sites:
            with self.subTest(site="%s:%d" % (path.name, line)):
                texts = _pointer_sites.without_citation(shipped, path, line, INVARIANT)
                self.assertReports(pointer_citation_problems(texts),
                                   "%s:%d" % (path.relative_to(REPO_ROOT).as_posix(), line))

    def test_a_new_pointer_site_without_the_citation(self):
        """A site no list names: the scan finds it because it points at the section."""
        texts = _pointer_sites.shipped_texts()
        texts[SKILLS / "graduation" / "new-step.md"] = (
            "A later step points at `../bootcamp-onboarding/ground-rules.md` → "
            "\"Worked\nsteers\" rather than a copy here (INV-300).\n")
        self.assertReports(pointer_citation_problems(texts), "graduation/new-step.md:1")

    def test_a_new_pointer_by_anchor_without_the_citation(self):
        texts = {SKILLS / "graduation" / "new-step.md":
                 "See [the steer](../bootcamp-onboarding/ground-rules.md#worked-steers) "
                 "(INV-300).\n"}
        self.assertReports(pointer_citation_problems(texts), "without citing INV-352")

    def test_a_rewrapped_citation_still_passes(self):
        """INV-346: the name and the citation may each wrap; the sentence is still one unit."""
        texts = {SKILLS / "graduation" / "new-step.md":
                 "Stated once in `ground-rules.md` → \"Worked\nsteers\"; follow them there "
                 "(INV-300,\nINV-352).\n"}
        self.assertEqual([], pointer_citation_problems(texts))

    def test_a_citation_in_another_sentence_does_not_count(self):
        texts = {SKILLS / "graduation" / "new-step.md":
                 "This is the steer (INV-352). It is stated once in `ground-rules.md` → "
                 "\"Worked steers\" (INV-300).\n"}
        self.assertReports(pointer_citation_problems(texts), "without citing INV-352")

    def test_module_pointer_names_less(self):
        skill = read(SKILLS / "module-05-data-quality-mapping" / "SKILL.md").replace(
            "minimal verbosity and the checkpoint note", "and the rest")
        self.assertReports(citation_problems(skill, "m5", STATEMENT), "does not name minimal")

    def test_module_with_the_wrong_form(self):
        skill = read(SKILLS / "module-06-data-processing" / "SKILL.md").replace(
            "and ask first: the pinned ask-first 👉 comes before the fix, and it may end a turn "
            "in a step\nthis module says asks nothing.",
            "Before Data processing it is a statement and adds no 👉.")
        problems = citation_problems(skill, "m6", ASK_FIRST)
        self.assertReports(problems, "does not state its ask first form")
        self.assertReports(problems, "states the statement form")

    def test_module_restates_the_rule(self):
        skill = read(SKILLS / "module-07-query-visualize-discover" / "SKILL.md") + (
            "\nNever stage a failure to have one to show.\n")
        self.assertReports(copy_problems(skill, "m7"), "restates the shared rule")

    # --- Act 1 and the cross-reference -------------------------------------------------------

    def test_act1_module_citing_the_rule(self):
        text = read(SKILLS / "module-03-system-verification" / "SKILL.md") + (
            "\n**Worked steer.** See the ground rules.\n")
        self.assertReports(act1_problems(text, "m3"), "Act 1 does not show")

    def test_cross_reference_dropped(self):
        text = read(GROUND_RULES).replace("- **The same reversal can also be the module's worked "
                                          "steer**", "- **The same reversal**")
        self.assertReports(cross_reference_problems(text), "no cross-reference")

    def test_filing_made_visible(self):
        text = read(GROUND_RULES).replace("- **Silent.** No banners, no 👉 question, no "
                                          "announcement", "- **Shown.** A banner")
        self.assertReports(cross_reference_problems(text), "no longer keeps the filing silent")


if __name__ == "__main__":
    unittest.main()
