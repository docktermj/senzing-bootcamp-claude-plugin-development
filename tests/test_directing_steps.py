"""One step per hands-on module is handed to the Bootcamper to direct (#485).

Before #485 every hands-on step was directed by the guide: the 👉 questions collected choices
and approvals, and the Bootcamper never said, in their own words, what a step should build. #485
hands one step in each hands-on module to them:

1. **Data Quality, Mapping, and Transformation, step 11.** What each column `mapping_workflow`
   did not recognize becomes, and what they expect the mapped record to show. Checked at step 12,
   whose sample record is shown beside their words.
2. **Data processing, step 21.** Which records to look up, what they expect Senzing to have done
   with them, and why. Checked by the lookup, as text.
3. **Query, Visualize and Discover, step 1.** #478's open question is the directing 👉. Checked at
   step 3a, which shows each answer beside the question they posed.

**One shared rule, cited (INV-300).** What a directing step is (the open 👉, the result beside the
expectation with every difference named, the "you pick" fallback with no re-ask, once per module
on the first applicable source, and the `You directed:` recap line) is stated once, in
`ground-rules.md` → "Directing steps". Each site points there and carries only its own pinned 👉
(INV-247) and what is particular to it.

So the clauses are checked where they live:

- **In the shared section** (`rule_problems`): every rule-only clause, the site table, and the
  three recap forms.
- **Per site** (`m5_problems`, `m6_problems`, `m7_problems`): the pinned 👉, exactly one per
  module (INV-251), open (no numbered options and no "or" between choices, INV-051), the pointer
  to the shared rule with INV-300 and INV-354, no copy of a rule-only clause, and the site's own
  content.
- **At every pointer, derived** (`pointer_citation_problems`, #519): every shipped sentence that
  points at "Directing steps", found by scan rather than from the sites named here (INV-246),
  cites INV-354, so a reader at the pointer can name the rule as well as the single-statement
  discipline. Since #519 that is six sentences: steps 11 and 12 of Module 5, step 21 of Module 6,
  steps 1 and 3a of Module 7, and the `You directed:` line in `module-completion.md`.
- **The recap** (`completion_problems` and `RecapGeneratorIsUnchanged`): the `You directed:` line
  is stated where the recap is written, and the generator's `--check` passes a recap carrying it
  with its three required blocks unchanged.

The checks are pure functions over a file's text, so each also runs on a mutated copy as its
negative control (`TheChecksCatchARegression`). Each mutation must make the check report the
problem it targets, not merely some problem.

⚠️ **What the derived scan cannot see** (`tests/_pointer_sites.py` says how it reads): a pointer
that names the section in other words, with neither the quoted name "Directing steps" nor the
`ground-rules.md#directing-steps` anchor; a pointer outside `plugins/` or outside Markdown; the
owner's own cross-references inside `ground-rules.md`, which are excluded; whether INV-354 is
the right invariant for what the sentence says; and a sentence cut early at an abbreviation.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line by
construction; counting lines that *start* with `👉 **` keeps prose that mentions the marker ("the
next 👉") from being counted. Phrase checks use `_wrapped_text.match_lines`, which matches across
a wrap.

⛔ **What this cannot establish:** that a live guide asks the question, builds what was asked,
compares honestly, or writes the recap line. Those are properties of a conversation; only `dry-run`
phase 3 observes them. This pins that the skill files STATE them. INV-354 names this file as its
enforcer; the ⛔ pattern requires its citation, and passing it is no evidence that a live run obeys
it.

#521 closed a Module 5 gap: step 11 now names its record, `directing_steps.data_quality_mapping`,
and says a value already set means the step has run, as Modules 6 and 7 do; its checkpoint writes
the record; and it says Phase 1 named the columns at Step 5a (sub-steps 4 and 6), not Step 6.
`m5_problems` pins all three, with negative controls and a re-wrap control.

Stdlib only; shipped markdown read as text (INV-108).

Source issue: #485 (part of #465); Module 5's record, #521; the citation at every pointer, #519.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _pointer_sites
import _wrapped_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
SCRIPT = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_recap_pdf.py"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"
M5_DIR = SKILLS / "module-05-data-quality-mapping"
M5_PHASE2 = M5_DIR / "phase2-data-mapping.md"
M6_DIR = SKILLS / "module-06-data-processing"
M6_PHASED = M6_DIR / "phaseD-validation.md"
M7_DIR = SKILLS / "module-07-query-visualize-discover"
M7_PHASE1 = M7_DIR / "phase1-query-visualize.md"

RULE_HEADING = "## Directing steps"

M5_QUESTION = ("👉 **What should each of these columns become in {source}'s mapped record? Say it "
               "in your own words, with what you expect the record to show for each one.**")
M6_QUESTION = ("👉 **Which of your records should I look up to check how Senzing resolved them? "
               "Name them in your own words, with what you expect Senzing to have done with them "
               "and why.**")
#: #478's open question, which #485 makes Module 7's directing 👉 without rewording it.
M7_QUESTION = "👉 **What do you want to find out about your data?**"
#: Step 3a's one 👉 since #483, which ends 3a's turn; it is a recall question, not a directing one.
M7_RECALL_QUESTION = "👉 **What does that tell you about entity {ENTITY_ID}? Reply with a number:**"

#: The pointer every site carries instead of a copy (INV-300), citing the rule (INV-354).
CITATION = (r'stated once in\s+`\.\./bootcamp-onboarding/ground-rules\.md` → "Directing steps";\s+'
            r'follow them\s+there rather than a copy here \(INV-300, INV-354\)')
#: The section every pointer names, its anchor, and the invariant each pointer cites (#519).
SECTION, ANCHOR, INVARIANT = "Directing steps", "directing-steps", "INV-354"
#: What that pointer must name, so a site cannot quietly drop a clause it defers to.
POINTER_NAMES = ("the result beside the expectation", '"you pick" fallback', "once per module",
                 "`You directed:`")

#: Phrases only the shared rule may carry; a site that holds one has forked it (INV-300).
RULE_ONLY = (r"set to `directed`, `guide_chose` or `none`", r"You caught: \{each",
             r"\*\*You directed:\*\* nothing this module\.", r"A difference is a finding, not a grade")


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


def numbered_after(text, question):
    """True when a numbered option list sits directly beneath ``question``."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == question:
            for later in lines[i + 1:]:
                s = later.strip()
                if not s or s.startswith("*(Internal"):
                    continue
                return bool(re.match(r"\d+\. ", s))
    return False


def open_question_problems(where, question):
    """The pinned 👉 is open: one question, no menu, no choices joined with "or" (INV-051)."""
    problems = []
    body = question[len("👉 **"):]
    if re.search(r"\bor\b", body):
        problems.append("%s's 👉 joins choices with 'or' (INV-051)" % where)
    if re.search(r"(?i)reply with a number", body):
        problems.append("%s's 👉 asks for a number: it is a menu, not an open question" % where)
    if re.search(r"(?i)\b(write|edit|paste)\b.*\bcode\b|\bcode\b", body):
        problems.append("%s's 👉 asks the Bootcamper about writing code" % where)
    return problems


def citation_problems(site, where):
    """A site points at the shared rule, names what it defers to, and carries no copy of it."""
    problems = []
    if not match_lines(site, CITATION):
        problems.append("%s does not point at the shared rule with INV-300 and %s"
                        % (where, INVARIANT))
    flat = squash(site)
    start = flat.find("directing step")
    pointer = flat[start:flat.find("(INV-300", start)] if start >= 0 else ""
    for phrase in POINTER_NAMES:
        if phrase not in pointer:
            problems.append("%s's pointer does not name %s" % (where, phrase))
    for phrase in RULE_ONLY:
        if match_lines(site, phrase):
            problems.append("%s restates the shared rule (%s)" % (where, phrase))
    return problems


# --------------------------------------------------------------------------------------------
# The shared rule
# --------------------------------------------------------------------------------------------

RULE_REQUIRED = {
    "the hands-on modules are named": r"the hands-on modules are Data Quality, Mapping, and "
                                      r"Transformation, Data processing, and Query, Visualize "
                                      r"and Discover",
    "it is the one statement": r"This section is the one\s+statement of how every directing step",
    "the 👉 is pinned at its site (INV-247)": r"One open 👉, pinned at its site \(INV-247\)",
    "it asks what to build and what they expect": r"asks what to build and what they expect as "
                                                  r"one\s+question",
    "it is open, with no menu": r"with no numbered options and no menu",
    "the guide offers no recommendation first": r"offers no\s+recommendation of its own unless "
                                                 r"asked to choose",
    "one 👉 per turn (INV-251)": r"only 👉 \(INV-251\)",
    "the guide writes every line of code": r"⛔ \*\*\(INV-354\) The Bootcamper directs in words; the guide "
                                           r"writes every line of code\.\*\*",
    "the Bootcamper is never asked for code": r"Never ask them to\s+write, edit or paste code",
    "the code comes from the MCP tools (INV-080)": r"the code comes from the MCP\s+tools exactly "
                                                   r"as it does elsewhere \(INV-080\)",
    "attribute names come from mapping_workflow": r"attribute names from `mapping_workflow`",
    "the result is shown beside their words": r"\*\*The result beside the expectation\.\*\*",
    "it is marked matches or differs": r"`matches` or `differs`",
    "every difference is named": r"Name every difference in one line",
    "the evidence is the tools' own output": r"The evidence comes from the tool's or the engine's "
                                             r"own output",
    "the comparison is non-yielding (INV-225)": r"so it is non-yielding \(INV-225\)",
    "a difference is not graded": r"\*\*A difference is a finding, not a grade\.\*\*",
    "the comparison asks nothing of its own": r"The comparison adds no question of its own",
    "it is not a prediction": r"\*\*Not a prediction\.\*\*",
    "the you-pick fallback": r"\*\*\"You pick\" and \"I don't know\"\.\*\*",
    "the fallback is the step as before": r"gets what the step did\s+before directing steps "
                                          r"existed",
    "there is no re-ask (INV-006)": r"Do not ask the directing question again\s+\(INV-006\)",
    "nothing is marked as theirs": r"mark nothing as theirs",
    "once per module": r"\*\*Once per module, on the first source it applies to\.\*\*",
    "later sources get the step as before": r"Every later\s+source, and every later pass",
    "the progress record": r"`directing_steps\.<module name token>`, set to `directed`, "
                           r"`guide_chose` or `none`",
    "no site means no stand-in": r"no other step stands in\s+for it",
    "the You directed line": r"one `\*\*You directed:\*\*`\s+line, inline, after "
                             r"`\*\*Why it matters:\*\*`",
    "the generator needs nothing new": r"the recap generator and its `--check` need nothing\s+new",
    "the directed form": r"directed: `\*\*You directed:\*\* \{what they asked for, in their "
                         r"words\}\. You caught:",
    "the handed-back form": r"handed back: `\*\*You directed:\*\* nothing this module\. You asked "
                            r"me to choose",
    "the no-site form": r"no site: `\*\*You directed:\*\* nothing this module\. \{Why the step "
                        r"did not arise\}",
}


def rule_problems(ground_rules):
    rule = section(ground_rules, RULE_HEADING, ("\n## ",))
    if not rule:
        return ["the ground rules have no %r section" % RULE_HEADING]
    problems = []
    if '<a id="directing-steps"></a>' not in ground_rules:
        problems.append("the ground rules do not anchor the section")
    for what, pattern in RULE_REQUIRED.items():
        if not match_lines(rule, pattern):
            problems.append("the rule does not state that %s" % what)
    for site in ("phase2-data-mapping.md` step 11", "phaseD-validation.md` step 21",
                 "phase1-query-visualize.md` step 1"):
        if site not in rule:
            problems.append("the rule's site table does not list %s" % site)
    if questions(rule):
        problems.append("the rule itself asks a 👉 question")
    return problems


# --------------------------------------------------------------------------------------------
# Data Quality, Mapping, and Transformation: step 11, checked at step 12
# --------------------------------------------------------------------------------------------

def m5_step(phase2, number, next_number):
    return section(phase2, "### %s. " % number, ("### %s. " % next_number,))


def m5_problems(phase2, module_files=()):
    problems = []
    step11 = m5_step(phase2, "11", "12")
    step12 = m5_step(phase2, "12", "13")
    if not step11 or not step12:
        return ["Module 5 has no step 11 or step 12"]
    directing = section(step11, "**The directing step (once per module).**",
                        ("⛔ **Before accepting the plan",))
    if not directing:
        return ["step 11 does not carry the directing step"]
    asked = questions(directing)
    if asked != [M5_QUESTION]:
        problems.append("step 11's directing step does not ask exactly the pinned 👉 (%r)"
                        % asked)
    if numbered_after(directing, M5_QUESTION):
        problems.append("step 11's directing 👉 is followed by a numbered menu")
    problems += open_question_problems("step 11", M5_QUESTION)
    required = {
        "which columns: those mapping_workflow did not recognize":
            r"with at least one column\s+`mapping_workflow` did not recognize",
        "a recognized column is a feature at 0.80 or above":
            r"does not send to a feature at\s+confidence 0\.80 or above",
        "the record-ID column is excluded": r"other than the column that\s+supplies `RECORD_ID`",
        "the tool's own reference says the rest is payload or ignore":
            r"anything outside its feature catalog \"is\s+payload or ignore\"",
        "both mapping modes": r"verbose and concise mode alike",
        "no unrecognized column passes it on": r"passes the directing step to the\s+next source "
                                               r"that has one",
        "no source with one means no directing step": r"Module 5 has no directing step",
        "no recommendation before the 👉": r"Offer no\s+recommendation",
        "it stands in for the per-field question": r"stands in for the `QUESTION FORMAT` "
                                                   r"question",
        "attribute names still come from the tool": r"the\s+family and attribute come from "
                                                    r"`mapping_workflow`'s reference, never from "
                                                    r"their wording",
        "a feature with no family is built as payload and named":
            r"map the column as payload, which keeps its value on the record",
        "the other checks still run": r"Every check below still runs on the result",
        "you pick: the step's own call, no re-ask (INV-006)":
            r"rather than asking it: the column was just asked about \(INV-006\)",
        "the check is at step 12": r"\*\*The check is at step 12\*\*",
        "the old unconditional sentence is gone": r"no general guided-mode gate before this "
                                                  r"advance, in either mode",
        # #521: the record, named as Modules 6 and 7 name theirs, and what a set value means.
        "the progress record": r"Record `directing_steps\.data_quality_mapping` in step 11's "
                               r"checkpoint",
        "an existing record means it has run": r"`directing_steps\.data_quality_mapping` is "
                                               r"already set, it has run",
        "a set record gets no second directing 👉": r"remap, map the columns as the rest of this "
                                                    r"step says, with no directing 👉",
        "the checkpoint writes the record": r"\*\*Checkpoint:\*\* write step 11, with "
                                            r"`directing_steps\.data_quality_mapping`",
        # #521: Phase 1 names the columns at Step 5a (sub-steps 4 and 6), not at Step 6.
        "Phase 1 Step 5a named the columns": r"Phase 1 Step 5a has already named them "
                                             r"\(`unmapped_fields`, recorded at its sub-step 4 "
                                             r"and named to the Bootcamper at its sub-step 6\)",
    }
    for what, pattern in required.items():
        if not match_lines(step11, pattern):
            problems.append("step 11 does not state %s" % what)
    if match_lines(step11, r"Phase 1 Step 6 has already named them"):
        problems.append("step 11 says Phase 1 Step 6 named the columns (it is Step 5a)")
    if match_lines(step11, r"(?i)advance is unconditional in both modes"):
        problems.append("step 11 still says its advance is unconditional (contradicts the "
                        "directing question)")
    problems += citation_problems(directing, "step 11")
    check = {
        "the sample record is shown in both modes": r"show one sample record in both modes",
        "their words beside where each column landed": r"their words, where the column landed in\s+"
                                                       r"the record",
        "matches or differs": r"`matches` or `differs`",
        "every difference named": r"with every\s+difference named",
        "the way back is step 16's gate": r"step 16's gate offers the way back to step 17",
        "step 12 asks nothing (INV-225)": r"this step asks nothing \(INV-225\)",
        "it points at the shared rule (INV-300, INV-354)": r"\"Directing steps\", INV-300, "
                                                           r"INV-354\)",
    }
    for what, pattern in check.items():
        if not match_lines(step12, pattern):
            problems.append("step 12 does not state %s" % what)
    if questions(step12):
        problems.append("step 12 asks a 👉 question")
    # Exactly one directing step in the whole module.
    hits = sum(read_text.count("This is Module 5's directing step") for read_text in module_files)
    pins = sum(questions(read_text).count(M5_QUESTION) for read_text in module_files)
    if module_files and (hits != 1 or pins != 1):
        problems.append("Module 5 has %d directing steps and %d copies of its 👉, not one of each"
                        % (hits, pins))
    return problems


# --------------------------------------------------------------------------------------------
# Data processing: step 21
# --------------------------------------------------------------------------------------------

def m6_problems(phase_d, module_files=()):
    problems = []
    step21 = section(phase_d, "## 21. Validate match accuracy", ("## 22. ",))
    if not step21:
        return ["Phase D has no step 21"]
    asked = questions(step21)
    if asked != [M6_QUESTION]:
        problems.append("step 21 does not ask exactly the pinned 👉 (%r)" % asked)
    if numbered_after(step21, M6_QUESTION):
        problems.append("step 21's directing 👉 is followed by a numbered menu")
    problems += open_question_problems("step 21", M6_QUESTION)
    ask = step21.find(M6_QUESTION)
    review = step21.find("Review the entity resolution results:")
    build = step21.find("**Building from the answer.**")
    if min(ask, review, build) < 0 or not ask < build < review:
        problems.append("step 21 does not ask, then build the lookup, then run the review, in "
                        "that order")
    required = {
        "it runs the first time Phase D reaches step 21":
            r"The first time Phase D reaches step 21, before any sample is queried",
        "an existing record means it has run": r"`directing_steps\.data_processing` is already "
                                               r"set, it has run",
        "records are found by ID or by their details": r"by `DATA_SOURCE` and record ID where\s+"
                                                       r"they gave one, otherwise by searching",
        "the lookup is get_entity_by_record_id, never SQL":
            r"`get_entity_by_record_id` through the generated query code below, never with SQL",
        "the result is shown as text beside their words": r"Show the result\s+as text, beside "
                                                          r"their words",
        "matches or differs": r"`matches` or `differs`",
        "the evidence is the engine's own output": r"the evidence is the engine's own output",
        "a missing record is a named difference, not a re-ask":
            r"A record that cannot be found is a difference,\s+named in one line; do not ask for "
            r"another",
        "it stays text (no visualization)": r"This is text only",
        "you pick, including CORD or generated data": r"which is the expected answer on CORD or "
                                                      r"generated data",
        "you pick runs the review as it stands": r"run the review below as it stands",
    }
    for what, pattern in required.items():
        if not match_lines(step21, pattern):
            problems.append("step 21 does not state %s" % what)
    problems += citation_problems(step21, "step 21")
    # The amended non-yielding pointer (was "Steps 21–24 ask nothing").
    if not match_lines(phase_d, r"⛔ \(INV-225\) \*\*Steps 21–24 ask nothing unless step 21's "
                                r"directing question is due"):
        problems.append("Phase D's non-yielding pointer does not allow step 21's directing "
                        "question")
    if "Steps 21–24 ask nothing, so" in squash(phase_d):
        problems.append("Phase D still says steps 21–24 ask nothing, unconditionally")
    hits = sum(t.count("This is Module 6's directing step") for t in module_files)
    pins = sum(questions(t).count(M6_QUESTION) for t in module_files)
    if module_files and (hits != 1 or pins != 1):
        problems.append("Module 6 has %d directing steps and %d copies of its 👉, not one of each"
                        % (hits, pins))
    return problems


# --------------------------------------------------------------------------------------------
# Query, Visualize and Discover: step 1's question, checked at step 3a
# --------------------------------------------------------------------------------------------

def m7_problems(phase1):
    problems = []
    step1 = section(phase1, "## 1. Define query requirements", ("## 2. ",))
    step3a = section(phase1, "### 3a. Present query results", ("### 3b.",))
    if not step1 or not step3a:
        return ["Module 7 has no step 1 or step 3a"]
    if questions(step1).count(M7_QUESTION) != 1:
        problems.append("step 1 does not ask #478's open question exactly once")
    pointer = section(step1, "**This is Module 7's directing step.**", ("\n\n",))
    if not pointer:
        problems.append("step 1 does not say it is Module 7's directing step")
    else:
        problems += citation_problems(pointer, "step 1")
        for what, pattern in {
            "the check is step 3a": r"the\s+check is step 3a",
            "I don't know is the handed-back case": r"\"I don't know\" is the handed-back case",
            "the progress record": r"Record\s+`directing_steps\.query_visualize_discover`",
        }.items():
            if not match_lines(pointer, pattern):
                problems.append("step 1's pointer does not state %s" % what)
    first = step3a.find("**Their questions first, each beside its answer.**")
    zero = step3a.find("**If entity resolution found zero or very few matches:**")
    if first < 0 or zero < 0 or not first < zero:
        problems.append("step 3a does not present their questions first")
    for what, pattern in {
        "it is the directing step's check (INV-300, INV-354)": r"\"Directing steps\", "
                                                               r"INV-300, INV-354\)",
        "their question is quoted": r"the question they\s+posed in step 1, quoted \(\"You asked: "
                                    r"'…'\"\)",
        "matches or differs": r"`matches` when the\s+answer addresses what they asked, or "
                              r"`differs`",
        "every difference named, from the query's own output":
            r"Name each\s+difference in one line: what is missing, and why, from the query's own "
            r"output",
        "derived requirements are not listed as theirs": r"\*\*\(not asked for\)\*\* in step 1 "
                                                         r"follow, and are not listed as theirs",
        "a guide-chosen list has no comparison": r"present the results as below with no "
                                                 r"comparison",
        # #486's headline entity is shown at the end of step 1 as the guide's pick; it must not
        # be compared as if the Bootcamper had asked for it.
        "the headline entity is not compared": r"\[headline entity\]\(#headline-entity\) step 1 "
                                               r"showed is not one of these answers and is not "
                                               r"compared",
    }.items():
        if not match_lines(step3a, pattern):
            problems.append("step 3a does not state %s" % what)
    # #483: step 3a's one 👉 is its recall question, pinned in test_module7_recall_question.py.
    if [q for q in questions(step3a) if q != M7_RECALL_QUESTION]:
        problems.append("step 3a asks a 👉 question other than its recall question (INV-251)")
    return problems


# --------------------------------------------------------------------------------------------
# The recap line
# --------------------------------------------------------------------------------------------

def completion_problems(completion):
    problems = []
    template = section(completion, "### End-of-Module Summary\n**What you accomplished:**",
                       ("```",))
    if "**You directed:**" not in template:
        problems.append("the recap template has no `**You directed:**` line")
    elif template.find("**You directed:**") < template.find("**Why it matters:**"):
        problems.append("the template's `You directed:` line is not after `Why it matters:`")
    for what, pattern in {
        "the line is for the three hands-on modules only":
            r"The `You directed:` line, in Data Quality, Mapping, and Transformation, Data "
            r"processing, and Query, Visualize and Discover only",
        "its forms are stated once in the ground rules (INV-300, INV-354)":
            r"stated once in `ground-rules\.md` → \"Directing steps\" \(INV-300, INV-354\)",
        "an unset record means the no-site form": r"is still unset at this point had no "
                                                  r"directing step",
        "it is not a fourth block": r"It is not a fourth block",
    }.items():
        if not match_lines(completion, pattern):
            problems.append("module-completion.md does not state %s" % what)
    return problems


def pointer_citation_problems(texts):
    """Every derived pointer to "Directing steps" cites INV-354 in its own sentence (#519)."""
    return _pointer_sites.uncited_pointers(texts, SECTION, ANCHOR, INVARIANT)


# --------------------------------------------------------------------------------------------
# Tests on the shipped files
# --------------------------------------------------------------------------------------------

def module_texts(directory):
    return [read(p) for p in sorted(directory.glob("*.md"))]


class TheSharedRuleIsStatedOnce(unittest.TestCase):
    def test_the_rule_states_every_clause(self):
        self.assertEqual([], rule_problems(read(GROUND_RULES)))

    def test_the_rule_follows_predictions_before_results(self):
        text = read(GROUND_RULES)
        self.assertLess(text.find("## Predictions before results"), text.find(RULE_HEADING))


class EachModuleHasOneDirectingStep(unittest.TestCase):
    def test_data_quality_mapping_step_11(self):
        self.assertEqual([], m5_problems(read(M5_PHASE2), module_texts(M5_DIR)))

    def test_data_processing_step_21(self):
        self.assertEqual([], m6_problems(read(M6_PHASED), module_texts(M6_DIR)))

    def test_query_visualize_discover_step_1_and_3a(self):
        self.assertEqual([], m7_problems(read(M7_PHASE1)))

    def test_module_7_adds_no_directing_question_of_its_own(self):
        """#478 owns the opening question; #485 adds only the check and the credit."""
        asked = [q for t in module_texts(M7_DIR) for q in questions(t)]
        self.assertNotIn(M5_QUESTION, asked)
        self.assertNotIn(M6_QUESTION, asked)
        self.assertEqual(1, asked.count(M7_QUESTION))


class EveryPointerCitesTheRule(unittest.TestCase):
    """The pointer sites are derived by scan (INV-246), so a later one without INV-354 fails."""

    def test_every_pointer_cites_inv_354(self):
        self.assertEqual([], pointer_citation_problems(_pointer_sites.shipped_texts()))

    def test_the_scan_finds_every_known_site(self):
        """Not vacuous: the derived set holds each file this guard already checks."""
        found = [path for path, _, _ in _pointer_sites.pointers(
            _pointer_sites.shipped_texts(), SECTION, ANCHOR)]
        for path, count in ((M5_PHASE2, 2), (M6_PHASED, 1), (M7_PHASE1, 2), (COMPLETION, 1)):
            with self.subTest(path=path.name):
                self.assertGreaterEqual(found.count(path), count)


class TheRecapCarriesTheLine(unittest.TestCase):
    def test_module_completion_states_the_line(self):
        self.assertEqual([], completion_problems(read(COMPLETION)))


def run_generator(markdown, *args):
    workdir = tempfile.mkdtemp()
    src = os.path.join(workdir, "recap.md")
    with open(src, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", src, "--output",
         os.path.join(workdir, "recap.pdf"), *args],
        capture_output=True, text=True, cwd=workdir,
    )
    return proc.returncode, proc.stdout, proc.stderr


RECAP_WITH_LINE = """# Senzing Bootcamp Recap

**Bootcamper:** Ada Lovelace
**Started:** 2026-10-11

## Data processing — 2026-10-11T15:10:00-05:00

### Information Shared

Loading with the SDK, the redo queue, and how resolution results are validated.

### Questions & Responses

- **Q:** Which of your records should I look up to check how Senzing resolved them?
    - **R:** CUSTOMERS 1001 and CRM 77 should merge: same person, same phone.

### Actions Taken

- Loaded all sources and looked up the two records named.

### End-of-Module Summary

**What you accomplished:**
- Loaded every source and validated resolution.

**Files produced:**
- `src/load/loader.py` — the loader

**Why it matters:** The resolved entities are what the next module explores.
**You directed:** CUSTOMERS 1001 and CRM 77 should merge. You caught: they stayed apart, because CRM 77's phone was never mapped.
"""


class RecapGeneratorIsUnchanged(unittest.TestCase):
    """The recap keeps four subsections and three blocks; the line needs no generator change."""

    def test_check_passes_a_recap_carrying_the_line(self):
        code, stdout, stderr = run_generator(RECAP_WITH_LINE, "--check")
        self.assertEqual(0, code, stderr)
        self.assertIn("Recap complete", stdout)

    def test_the_required_blocks_are_still_three(self):
        spec = importlib.util.spec_from_file_location("recap_gen_directing", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules["recap_gen_directing"] = module
        spec.loader.exec_module(module)
        self.assertEqual(["What you accomplished", "Files produced", "Why it matters"],
                         module.END_SUMMARY_BLOCKS)
        self.assertNotIn("You directed", module.END_SUMMARY_BLOCKS)

    def test_the_stdlib_renderer_keeps_the_line(self):
        """The fallback renderer runs without fpdf2, so this holds on both CI legs."""
        spec = importlib.util.spec_from_file_location("recap_gen_directing2", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules["recap_gen_directing2"] = module
        spec.loader.exec_module(module)
        out = Path(tempfile.mkdtemp()) / "stdlib.pdf"
        self.assertTrue(module.render_with_stdlib(module.parse_recap(RECAP_WITH_LINE), out))
        self.assertIn(b"You directed", out.read_bytes().replace(b"\\", b""))


# --------------------------------------------------------------------------------------------
# Negative controls
# --------------------------------------------------------------------------------------------

class TheChecksCatchARegression(unittest.TestCase):
    """Each mutation must produce the problem it targets."""

    def assertReports(self, problems, needle):
        self.assertTrue(any(needle in p for p in problems),
                        "expected a problem containing %r, got %r" % (needle, problems))

    # --- the shared rule ---------------------------------------------------------------------

    def test_rule_without_the_fallback(self):
        text = read(GROUND_RULES).replace("Do not ask the directing question again",
                                          "Ask the directing question again")
        self.assertReports(rule_problems(text), "there is no re-ask")

    def test_rule_without_the_handed_back_form(self):
        text = read(GROUND_RULES).replace("handed back: `**You directed:**", "handed back: `")
        self.assertReports(rule_problems(text), "the handed-back form")

    def test_rule_without_the_code_guard(self):
        text = read(GROUND_RULES).replace("Never ask them to\n  write, edit or paste code", "")
        self.assertReports(rule_problems(text), "never asked for code")

    def test_rule_that_asks_a_question(self):
        text = read(GROUND_RULES).replace("## Directing steps\n",
                                          "## Directing steps\n\n👉 **Ready?**\n")
        self.assertReports(rule_problems(text), "the rule itself asks")

    # --- Module 5 ----------------------------------------------------------------------------

    def test_m5_second_question(self):
        text = read(M5_PHASE2).replace(M5_QUESTION, M5_QUESTION + "\n\n👉 **Anything else?**")
        self.assertReports(m5_problems(text), "does not ask exactly the pinned 👉")

    def test_m5_menu_under_the_question(self):
        text = read(M5_PHASE2).replace(M5_QUESTION, M5_QUESTION + "\n\n1. Feature\n2. Payload")
        self.assertReports(m5_problems(text), "numbered menu")

    def test_m5_choices_joined_with_or(self):
        bad = M5_QUESTION.replace("become in", "become: feature, payload or ignore, in")
        text = read(M5_PHASE2).replace(M5_QUESTION, bad)
        problems = m5_problems(text) + open_question_problems("step 11", bad)
        self.assertReports(problems, "joins choices with 'or'")

    def test_m5_attribute_names_from_their_words(self):
        text = read(M5_PHASE2).replace("never from their wording", "from their wording")
        self.assertReports(m5_problems(text), "attribute names still come from the tool")

    def test_m5_both_modes_dropped(self):
        text = read(M5_PHASE2).replace("verbose and concise mode alike", "verbose mode only")
        self.assertReports(m5_problems(text), "both mapping modes")

    def test_m5_unconditional_restored(self):
        text = read(M5_PHASE2).replace(
            "⚠️ **There is no general guided-mode gate",
            "⚠️ **This advance is unconditional in both modes. There is no general guided-mode gate")
        self.assertReports(m5_problems(text), "still says its advance is unconditional")

    def test_m5_pointer_dropped(self):
        text = read(M5_PHASE2).replace("(INV-300, INV-354). Only what is particular to step 11",
                                       ". Only what is particular to step 11")
        self.assertReports(m5_problems(text), "does not point at the shared rule")

    def test_m5_rule_restated_at_the_site(self):
        text = read(M5_PHASE2).replace(
            "- **The check is at step 12**",
            "- A difference is a finding, not a grade.\n- **The check is at step 12**")
        self.assertReports(m5_problems(text), "restates the shared rule")

    def test_m5_step_12_check_dropped(self):
        text = read(M5_PHASE2).replace("show one sample record in both modes", "show the path")
        self.assertReports(m5_problems(text), "the sample record is shown in both modes")

    def test_m5_record_not_named(self):
        text = read(M5_PHASE2).replace("Record `directing_steps.data_quality_mapping` in step 11's",
                                       "Record it in step 11's")
        self.assertReports(m5_problems(text), "the progress record")

    def test_m5_set_record_not_treated_as_run(self):
        text = read(M5_PHASE2).replace("`directing_steps.data_quality_mapping` is already set, "
                                       "it has run", "the step may run again")
        self.assertReports(m5_problems(text), "an existing record means it has run")

    def test_m5_checkpoint_drops_the_record(self):
        text = read(M5_PHASE2).replace(
            "**Checkpoint:** write step 11, with `directing_steps.data_quality_mapping` on the "
            "source the\ndirecting step ran on.", "**Checkpoint:** write step 11.")
        self.assertReports(m5_problems(text), "the checkpoint writes the record")

    def test_m5_step_6_reference_restored(self):
        text = read(M5_PHASE2).replace("Phase 1 Step 5a has already named them",
                                       "Phase 1 Step 6 has already named them")
        problems = m5_problems(text)
        self.assertReports(problems, "Phase 1 Step 5a named the columns")
        self.assertReports(problems, "it is Step 5a")

    def test_m5_record_rewrapped_still_passes(self):
        """INV-346: the phrase checks hold when the paragraph is wrapped differently."""
        text = read(M5_PHASE2).replace("When `directing_steps.data_quality_mapping` is already set",
                                       "When\n  `directing_steps.data_quality_mapping` is\n  already "
                                       "set")
        self.assertNotEqual(read(M5_PHASE2), text, "the re-wrap no longer applies")
        self.assertEqual([], m5_problems(text, module_texts(M5_DIR)))

    def test_m5_second_directing_step_elsewhere(self):
        texts = module_texts(M5_DIR) + ["This is Module 5's directing step.\n\n" + M5_QUESTION]
        self.assertReports(m5_problems(read(M5_PHASE2), texts), "not one of each")

    # --- Module 6 ----------------------------------------------------------------------------

    def test_m6_question_after_the_review(self):
        text = read(M6_PHASED)
        text = text.replace(M6_QUESTION + "\n", "")
        text = text.replace("**Checkpoint:** write step 21.",
                            M6_QUESTION + "\n\n**Checkpoint:** write step 21.")
        self.assertReports(m6_problems(text), "in that order")

    def test_m6_visualization_offered(self):
        text = read(M6_PHASED).replace("This is text only", "Offer a chart")
        self.assertReports(m6_problems(text), "it stays text")

    def test_m6_reask_on_a_missing_record(self):
        text = read(M6_PHASED).replace("do not ask for another", "ask for another")
        self.assertReports(m6_problems(text), "a missing record is a named difference")

    def test_m6_unconditional_pointer_restored(self):
        text = read(M6_PHASED).replace(
            "⛔ (INV-225) **Steps 21–24 ask nothing unless step 21's directing question is due; "
            "when it is not,\nthis turn does not end here**",
            "⛔ **Steps 21–24 ask nothing, so this turn does not end here**")
        problems = m6_problems(text)
        self.assertReports(problems, "does not allow step 21's directing question")
        self.assertReports(problems, "unconditionally")

    def test_m6_you_pick_dropped(self):
        text = read(M6_PHASED).replace("run the review below as it stands", "ask again")
        self.assertReports(m6_problems(text), "you pick runs the review as it stands")

    # --- Module 7 ----------------------------------------------------------------------------

    def test_m7_answers_before_their_questions(self):
        text = read(M7_PHASE1)
        block = section(text, "**Their questions first, each beside its answer.**",
                        ("**If entity resolution found zero",))
        text = text.replace(block, "")
        text = text.replace("**One recall question, last",
                            block + "**One recall question, last")
        self.assertReports(m7_problems(text), "does not present their questions first")

    def test_m7_derived_listed_as_theirs(self):
        text = read(M7_PHASE1).replace("and are not listed as theirs", "and are listed as theirs")
        self.assertReports(m7_problems(text), "derived requirements are not listed as theirs")

    def test_m7_question_in_3a(self):
        text = read(M7_PHASE1).replace(
            "**If entity resolution found zero or very few matches:**",
            "👉 **Did that answer your question?**\n\n"
            "**If entity resolution found zero or very few matches:**")
        self.assertReports(m7_problems(text), "step 3a asks a 👉 question other than its recall")

    def test_m7_pointer_dropped(self):
        text = read(M7_PHASE1).replace("**This is Module 7's directing step.**", "**Note.**")
        self.assertReports(m7_problems(text), "does not say it is Module 7's directing step")

    def test_m7_headline_entity_compared(self):
        text = read(M7_PHASE1).replace("is not one of these answers and is not compared",
                                       "is the first of these answers")
        self.assertReports(m7_problems(text), "the headline entity is not compared")

    # --- the recap ---------------------------------------------------------------------------

    def test_template_line_dropped(self):
        text = re.sub(r"\*\*You directed:\*\* \{the three[^\n]*\n", "", read(COMPLETION))
        self.assertReports(completion_problems(text), "no `**You directed:**` line")

    def test_completion_pointer_dropped(self):
        text = read(COMPLETION).replace('"Directing steps" (INV-300, INV-354)', '"Directing steps"')
        self.assertReports(completion_problems(text), "stated once in the ground rules")

    # --- the derived pointer sites (#519) ----------------------------------------------------

    def test_m5_pointer_without_inv_354(self):
        text = read(M5_PHASE2).replace("(INV-300, INV-354). Only what is particular to step 11",
                                       "(INV-300). Only what is particular to step 11")
        self.assertReports(m5_problems(text), "does not point at the shared rule")

    def test_m7_check_without_inv_354(self):
        text = read(M7_PHASE1).replace('"Directing steps", INV-300, INV-354). Present',
                                       '"Directing steps", INV-300). Present')
        self.assertReports(m7_problems(text), "it is the directing step's check")

    def test_each_derived_pointer_loses_its_citation(self):
        """Every shipped pointer (six since #519), in turn, is reported when it drops INV-354."""
        shipped = _pointer_sites.shipped_texts()
        sites = _pointer_sites.pointers(shipped, SECTION, ANCHOR)
        self.assertGreaterEqual(len(sites), 6, "the scan went blind")
        for path, line, _ in sites:
            with self.subTest(site="%s:%d" % (path.name, line)):
                texts = _pointer_sites.without_citation(shipped, path, line, INVARIANT)
                self.assertReports(pointer_citation_problems(texts),
                                   "%s:%d" % (path.relative_to(REPO_ROOT).as_posix(), line))

    def test_a_new_pointer_site_without_the_citation(self):
        """A site no list names: the scan finds it because it points at the section."""
        texts = _pointer_sites.shipped_texts()
        texts[SKILLS / "graduation" / "new-step.md"] = (
            "Its shape is stated once in `../bootcamp-onboarding/ground-rules.md` → \"Directing\n"
            "steps\"; follow them there rather than a copy here (INV-300).\n")
        self.assertReports(pointer_citation_problems(texts), "graduation/new-step.md:1")

    def test_a_rewrapped_citation_still_passes(self):
        """INV-346: the name and the citation may each wrap; the sentence is still one unit."""
        texts = {SKILLS / "graduation" / "new-step.md":
                 "Stated once in `ground-rules.md` → \"Directing\nsteps\" (INV-300,\nINV-354).\n"}
        self.assertEqual([], pointer_citation_problems(texts))


if __name__ == "__main__":
    unittest.main()
