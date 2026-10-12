"""Module 6 Phase D's "Iterate now" runs the quality-iteration route and comes back to Phase D.

Phase D's iterate-vs-proceed gate offered "Iterate now to improve the results before moving on"
with nothing to execute: no step named the sources, wrote a key or entered a route, and the <80%
branch stated a recommendation to go back to Module 5 and then asked only the transition question.
Three more lines said "revisit Module 5" and described a destination with no step. INV-284 calls
that an unsatisfiable option.

The fix reuses the one route that already exists. Module 7 step 3b → "The quality-iteration route"
is still its only statement (INV-300). It now names two return points, records the one in use as
`return_to`, and states the iteration record's shape once for both: Module 7 appends it to
`module_7_query.quality_iterations`, Module 6 to `module_6_processing.quality_iterations`. Phase D
points at it and restates neither. The checks:

* the gate: one pinned question (INV-056), a neutral lead and a numbered list (INV-051), asked on
  the 80–89% branch and on the <80% branch, where option 1 is marked recommended. ⛔ The 👉 line is
  matched word for word, its lead "Most tests pass but there are gaps." included: "asks the same
  pinned question" (#526) leaves the pinned wording as it was, and rewording it is the
  maintainer's call, so a moved or reworded lead fails;
* the handling: "Iterate now" asks no second confirmation (INV-006), names the sources (ask nothing
  with one, one pinned numbered question with two or more), explains, and enters the route with the
  Module 6 return point; "Move forward" completes Module 6 once;
* the three "revisit Module 5" lines point at the gate and the route;
* the route names Module 6 Phase D as a return point, and its resume re-runs Phase D in full as a
  new state (INV-284), records `after`, and leaves an interrupted return to the key;
* both receiving branches hand back to the key's return point, and Module 6's **First:** routes an
  interrupted return by `stage`;
* Phase D's recap reports the iteration record.

⛔ **Each check is a function of the file text, so the negative controls run the SAME check on a
mutated copy** (INV-265). ⛔ **Every phrase is matched across line wraps (INV-346):** the texts are
flattened before matching, and `ReWrapping` re-flows every file to one word per line and asserts
the checks still pass, and still fail on a re-wrapped regression.

The checks assert that the skill files *state* these rules; they **cannot** establish that a live
guide follows them. `dry-run` phase 3 observes that.

Source issue: #526 (part of #504). Invariants: INV-006, INV-051, INV-056, INV-284, INV-300,
INV-346.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M5 = SKILLS / "module-05-data-quality-mapping"
M6 = SKILLS / "module-06-data-processing"
M7 = SKILLS / "module-07-query-visualize-discover"
FILES = {
    "phase_d": M6 / "phaseD-validation.md",
    "phase_b": M6 / "phaseB-load-first-source.md",
    "m6_skill": M6 / "SKILL.md",
    "m5_phase2": M5 / "phase2-data-mapping.md",
    "phase1": M7 / "phase1-query-visualize.md",
}

GATE_ANCHOR = '<a id="iterate-vs-proceed-decision-gate"></a>'
GATE_HEADING = "## Iterate vs. proceed decision gate"
ROUTE_ANCHOR = '<a id="the-quality-iteration-route"></a>'
ROUTE_LINK = "phase1-query-visualize.md#the-quality-iteration-route"
GATE_LINK = "#iterate-vs-proceed-decision-gate"
GATE_QUESTION = ("👉 Most tests pass but there are gaps. What would you like to do? Reply with a "
                 "number:")
OPTION_1 = "1. Iterate now to improve the results before moving on."
OPTION_2 = "2. Move forward to the next module."
SOURCE_QUESTION = "👉 Which sources should I remap and reload? Reply with one or more numbers:"


def plain(text):
    """Bold markers removed, so a phrase matches whether or not part of it is bold."""
    return text.replace("**", "")


def flat(text):
    return re.sub(r"\s+", " ", plain(text)).strip()


def find(text, phrase, start=0):
    """The first match of `phrase` in `text` at or after `start`, across line wraps (INV-346)."""
    words = phrase.split()
    return re.compile(r"\s+".join(re.escape(w) for w in words)).search(text, start)


def span(text, start, end):
    """`text` from `start` to the next `end` (or to the end), wrap-tolerant; None when absent."""
    text = plain(text)
    m = find(text, start)
    if m is None:
        return None
    if not end.strip():
        # A paragraph break is matched literally: re-wrapping never makes or removes one.
        j = text.find(end, m.end())
        return text[m.start():j if j != -1 else len(text)]
    e = find(text, end, m.end())
    return text[m.start():e.start() if e else len(text)]


def missing(block, needles, where):
    f = flat(block)
    return ["%s does not say %r" % (where, n) for n in needles if flat(n) not in f]


def present(block, needles, where):
    f = flat(block)
    return ["%s still says %r" % (where, n) for n in needles if flat(n) in f]


# ---------------------------------------------------------------------------------- checks


def gate_problems(phase_d):
    """The 80–89% and <80% branches ask one pinned question; <80% marks option 1 recommended."""
    gate = span(phase_d, GATE_HEADING, "## Stakeholder summary")
    if gate is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    problems = []
    if not re.search(re.escape(GATE_ANCHOR) + r"\s*\n\s*" + re.escape(GATE_HEADING), phase_d):
        problems.append("the gate heading has no %s anchor" % GATE_ANCHOR)
    asks = flat(gate).count(flat(GATE_QUESTION))
    if asks != 1:
        problems.append("the gate question is pinned %d times, not once" % asks)
    question = span(gate, GATE_QUESTION, "Handling each answer")
    if question is None or OPTION_1 not in flat(question) or OPTION_2 not in flat(question):
        problems.append("the gate question does not list both pinned options")
    mixed = span(gate, "- UAT 80–89%:", "- UAT <80%:")
    if mixed is None:
        problems.append("the gate has no 80–89% branch")
    else:
        problems += missing(mixed, ("ask the gate question below",), "the 80–89% branch")
    low = span(gate, "- UAT <80%:", "The gate question")
    if low is None:
        problems.append("the gate has no <80% branch")
    else:
        problems += missing(low, (
            "ask the same gate question below",
            "with option 1 marked *(recommended)*",
            "(INV-284) This branch asks",
        ), "the <80% branch")
        problems += present(low, ("proceed to the transition question",), "the <80% branch")
    problems += missing(gate, (
        "asked word for word on both of those branches",
        "On the <80% branch, option 1 ends with *(recommended)*",
        "nothing else in the question changes, the lead included",
    ), "the gate")
    return problems


def handling_problems(phase_d):
    """Both options have a handling step; "Iterate now" names sources and enters the route."""
    handling = span(phase_d, "Handling each answer (INV-284).", "## Stakeholder summary")
    if handling is None:
        return ["Phase D's gate has no handling step"]
    problems = missing(handling, (
        '2, "Move forward":',
        "Module 6 is completed once",
        '1, "Iterate now":',
        "(INV-006) The pinned question's answer IS the go-ahead, so ask no second confirmation",
        "`load_status` is `loaded`",
        "With one, ask nothing and use it",
        "With two or more, end the turn on this single question, one numbered line per loaded "
        "source",
        SOURCE_QUESTION,
        "it is not a second confirmation",
        "Explain, as a statement",
        "It asks nothing",
        ROUTE_LINK,
        '`return_to: "module_6_phase_d"`',
        "(`uat_80_89` or `uat_below_80`)",
        "`module_6_processing.quality_iterations`",
        "step 3b → \"The quality-iteration route\" (INV-300)",
        "Phase D runs again in full, from step 21",
        "this gate is asked again on the new results",
    ), "the gate's handling step")
    # INV-300: Phase D points at the key and the record; it states neither.
    if '"quality_iteration": {' in phase_d:
        problems.append("Phase D restates the quality_iteration key")
    if flat('{"return_to", "sources"') in flat(phase_d):
        problems.append("Phase D restates the iteration record's shape")
    return problems


def revisit_problems(phase_d):
    """The three "revisit Module 5" lines point at the gate and the route."""
    problems = present(phase_d, (
        "revisit data quality (Module 5) or mapping before proceeding",
        "revisit Module 5 mapping",
        "the review's last bullet, back to Module 5",
    ), "Phase D")
    step21 = span(phase_d, "A difference they want to act on", "- \"You pick\"")
    if step21 is None or 'to the gate\'s "Iterate now"' not in flat(step21):
        problems.append("step 21's difference line does not go to the gate's \"Iterate now\"")
    for start, where in (("- If match accuracy is poor", "step 21's review bullet"),
                         ("If accuracy is poor", "step 24")):
        line = span(phase_d, start, "\n\n")
        if line is None:
            problems.append("%s moved" % where)
            continue
        for target in (GATE_LINK, ROUTE_LINK):
            if target not in line:
                problems.append("%s does not point at %s" % (where, target))
    rerun = span(phase_d, "Run again after a quality iteration.", "## Single-source validation")
    if rerun is None:
        problems.append("Phase D does not say it runs again after a quality iteration")
    else:
        problems += missing(rerun, (
            "item 3 (INV-300)",
            "`directing_steps.data_processing` is already set",
        ), "Phase D's re-run note")
    return problems


def route_problems(phase1):
    """Step 3b's route names Module 6 Phase D as a return point and resumes there."""
    loop = span(phase1, ROUTE_ANCHOR, "### 3c.")
    if loop is None:
        return ["step 3b has no quality-iteration route"]
    problems = []
    if '"return_to": "module_7_step_3b | module_6_phase_d"' not in loop:
        problems.append("the key does not record return_to with both return points")
    if '"from_verdict": "poor | marginal | uat_below_80 | uat_80_89"' not in loop:
        problems.append("the key's from_verdict does not carry the Phase D bands")
    problems += missing(loop, (
        "Two steps offer it, and each is a return point",
        "phaseD-validation.md" + GATE_LINK,
        "From Module 6 Phase D, leave `current_step` as Phase D's last checkpoint wrote it",
        '{"return_to", "sources", "from_verdict", "started_at", "before"}',
        "(INV-300) This is the one statement of the record's shape, for both return points",
        "`module_7_query.quality_iterations`",
        "`module_6_processing.quality_iterations`",
        "the UAT %, the per-record match accuracy, and the match-key and how-state audit outcomes",
        "the Bootcamper stays in the offering module",
    ), "step 3b's route")
    resume = span(loop, "On a Module 6 Phase D return", "4. An interrupted return")
    if resume is None:
        problems.append("the resume does not hand a Module 6 return back to Phase D")
    else:
        problems += missing(resume, (
            'clear `quality_iteration` and set `current_step` to `21` in one write',
            "re-run Phase D in full on the reloaded data: steps 21–28, the match-key and "
            "how-state audits, then the gate",
            "(INV-284) That too is a new state, NOT an INV-006 repeat",
            "the return may be offered again with no cap",
            "record its indicators as `after` on the latest "
            "`module_6_processing.quality_iterations` entry",
        ), "the Module 6 resume")
    interrupted = span(loop, "4. An interrupted return", "5. The recap.")
    if interrupted is None:
        problems.append("the route does not say how an interrupted return resumes")
    else:
        problems += missing(interrupted, (
            "resumes from the key",
            "From Module 6 Phase D",
            "Module 6's `SKILL.md` First: routes by `stage`",
            "do not re-present Phase D's gate or its source question",
        ), "the interrupted-return step")
    recap = span(loop, "5. The recap.", "Outcomes 2 and 3")
    if recap is None or flat("Module 6's, as Phase D's \"Module completion and transition to "
                             "Module 7\" says") not in flat(recap):
        problems.append("the route's recap item does not name Module 6's recap")
    return problems


def receiving_problems(m5_phase2, phase_b):
    """Both receiving branches hand back to the key's return point, not always to step 3b."""
    problems = []
    m5 = span(m5_phase2, '<a id="receiving-a-quality-iteration"></a>', "## Skip fast-pathed")
    if m5 is None:
        problems.append("Module 5 has no receiving branch")
    else:
        problems += missing(m5, (
            "at Module 6 Phase D's gate (the key's `return_to` says which)",
            "or as Module 6 Phase D left them on a Phase D return",
            "where the flow resumes at each return point",
        ), "Module 5's receiving branch")
    m6 = span(phase_b, '<a id="receiving-a-quality-iteration"></a>', "## 5. ")
    if m6 is None:
        problems.append("Module 6 Phase B has no receiving branch")
    else:
        problems += missing(m6, (
            "at this module's Phase D gate (the key's `return_to` says which)",
            "or as Phase D left them on a Phase D return",
            "hand back to the key's `return_to` by the route's resume",
            "this module's Phase D, from step 21, on `module_6_phase_d`",
            "Phase D run again in full",
        ), "Module 6's receiving branch")
        problems += present(m6, ("Then return to Module 7 step 3b's resume",),
                            "Module 6's receiving branch")
    return problems


def first_clause_problems(m6_skill):
    """An interrupted Module 6 return routes by `stage` from Module 6's **First:**."""
    clause = span(m6_skill, "First:", "\n\n")
    if clause is None:
        return ["Module 6 SKILL.md has no First: paragraph"]
    return missing(clause, (
        "When it carries a `quality_iteration`, none of this runs: route by its `stage`",
        "`reload` goes straight to Phase B",
        "phaseB-load-first-source.md#receiving-a-quality-iteration",
        "goes to Module 5's",
        "phase2-data-mapping.md#receiving-a-quality-iteration",
        "Do not re-present Phase D's gate or its source question",
        "(INV-300)",
    ), "Module 6 First:")


def recap_problems(phase_d):
    """Module 6's recap reports its iteration records; Module 6 completes once."""
    completion = span(phase_d, "## Module completion and transition to Module 7",
                      "👉 Are you ready")
    if completion is None:
        return ["Phase D's Module completion section moved"]
    return missing(completion, (
        "The Module 6 recap section records every quality iteration",
        "`module_6_processing.quality_iterations`",
        ROUTE_LINK,
        "states once, INV-300",
        "the indicators before and after",
        "(INV-284) This section is the only record of it",
        "Module 6 itself is completed once, here",
    ), "Phase D's Module completion")


CHECKS = {
    "gate": (gate_problems, ("phase_d",)),
    "handling": (handling_problems, ("phase_d",)),
    "revisit": (revisit_problems, ("phase_d",)),
    "route": (route_problems, ("phase1",)),
    "receiving": (receiving_problems, ("m5_phase2", "phase_b")),
    "first": (first_clause_problems, ("m6_skill",)),
    "recap": (recap_problems, ("phase_d",)),
}


def run(name, texts):
    fn, keys = CHECKS[name]
    return fn(*(texts[k] for k in keys))


def read_all():
    return {k: p.read_text(encoding="utf-8") for k, p in FILES.items()}


def rewrap(text):
    """One word per line for every prose line; headings, anchors, tables and fences are kept."""
    out = []
    fenced = False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fenced = not fenced
        if fenced or stripped.startswith(("#", "|", "<a ", "```")) or not stripped:
            out.append(line)
            continue
        indent = line[:len(line) - len(stripped)]
        out.append(("\n" + indent).join([indent + stripped.split(" ")[0]] +
                                        stripped.split(" ")[1:]))
    return "\n".join(out)


# ----------------------------------------------------------------------------------- tests


class TheLiveFilesMeetEveryCriterion(unittest.TestCase):
    def setUp(self):
        self.texts = read_all()

    def test_the_files_are_found(self):
        """⛔ INV-265: a scan of a moved file certifies nothing."""
        self.assertIn(GATE_ANCHOR, self.texts["phase_d"])
        self.assertIn(ROUTE_ANCHOR, self.texts["phase1"])

    def test_the_gate_asks_one_pinned_question_on_both_branches(self):
        self.assertEqual([], run("gate", self.texts))

    def test_iterate_now_names_sources_and_enters_the_route(self):
        self.assertEqual([], run("handling", self.texts))

    def test_the_revisit_lines_point_at_the_route(self):
        self.assertEqual([], run("revisit", self.texts))

    def test_the_route_names_phase_d_as_a_return_point(self):
        self.assertEqual([], run("route", self.texts))

    def test_the_receiving_branches_hand_back_to_the_return_point(self):
        self.assertEqual([], run("receiving", self.texts))

    def test_module_6_first_routes_an_interrupted_return(self):
        self.assertEqual([], run("first", self.texts))

    def test_module_6_recap_reports_the_iterations(self):
        self.assertEqual([], run("recap", self.texts))

    def test_the_source_question_is_pinned_once(self):
        """INV-056: one pinned copy, in Phase D's handling step."""
        hits = sum(flat(p.read_text(encoding="utf-8")).count(flat(SOURCE_QUESTION))
                   for p in SKILLS.rglob("*.md"))
        self.assertEqual(1, hits)


class EachCheckFailsWhenItsSiteIsRemoved(unittest.TestCase):
    """Negative controls: the same checks, run on mutated copies, must each report a problem."""

    def setUp(self):
        self.texts = read_all()

    def mutated(self, key, old, new=""):
        self.assertIn(old, self.texts[key], "negative control is stale: %r is gone" % old[:60])
        texts = dict(self.texts)
        texts[key] = texts[key].replace(old, new, 1)
        return texts

    def test_the_old_low_branch_statement_fails(self):
        texts = self.mutated(
            "phase_d", "and ask the same gate question below,\n  with option 1 marked "
            "*(recommended)*.",
            "and proceed to the transition question.")
        self.assertTrue(run("gate", texts))

    def test_a_second_copy_of_the_gate_question_fails(self):
        texts = self.mutated("phase_d", "\n\n**Handling each answer (INV-284).**",
                             "\n\n👉 **Most tests pass but there are gaps. What would you "
                             "like to do? Reply with a number:**"
                             "\n\n**Handling each answer (INV-284).**")
        self.assertTrue(run("gate", texts))

    def test_moving_the_lead_out_of_the_pinned_line_fails(self):
        """The pinned 👉 line keeps its lead (INV-056); moving it into a branch's statement fails."""
        texts = self.mutated("phase_d", "👉 **Most tests pass but there are gaps. What would you",
                             "👉 **What would you")
        self.assertTrue(run("gate", texts))

    def test_rewording_the_pinned_lead_fails(self):
        texts = self.mutated("phase_d", "👉 **Most tests pass but there are gaps.",
                             "👉 **Results are mixed.")
        self.assertTrue(run("gate", texts))

    def test_rewording_a_pinned_option_fails(self):
        texts = self.mutated("phase_d", "1. Iterate now to improve the results before moving on.",
                             "1. Iterate now.")
        self.assertTrue(run("gate", texts))

    def test_dropping_the_gate_anchor_fails(self):
        self.assertTrue(run("gate", self.mutated("phase_d", GATE_ANCHOR)))

    def test_a_second_confirmation_fails(self):
        texts = self.mutated("phase_d", "so ask no\n  second confirmation",
                             "so confirm once\n  more before starting")
        self.assertTrue(run("handling", texts))

    def test_asking_with_one_source_fails(self):
        texts = self.mutated("phase_d", "With one, ask nothing and use it.",
                             "With one, ask whether to use it.")
        self.assertTrue(run("handling", texts))

    def test_entering_the_route_without_the_return_point_fails(self):
        texts = self.mutated("phase_d", 'with `return_to: "module_6_phase_d"` and ', "with ")
        self.assertTrue(run("handling", texts))

    def test_restating_the_key_in_phase_d_fails(self):
        texts = self.mutated("phase_d", "**Handling each answer (INV-284).**",
                             '```json\n"quality_iteration": {\n}\n```\n\n'
                             "**Handling each answer (INV-284).**")
        self.assertTrue(run("handling", texts))

    def test_restoring_a_revisit_line_fails(self):
        texts = self.mutated("phase_d", "- If match accuracy is poor, say so and carry it",
                             "- If match accuracy is poor, revisit data quality (Module 5) or "
                             "mapping before proceeding\n- If match accuracy is poor, say so "
                             "and carry it")
        self.assertTrue(run("revisit", texts))

    def test_a_step_24_line_without_the_route_fails(self):
        texts = self.mutated("phase_d", 'whose "Iterate now" enters\n[the quality-iteration '
                             "route](../module-07-query-visualize-discover/phase1-query-"
                             "visualize.md#the-quality-iteration-route).", "below.")
        self.assertTrue(run("revisit", texts))

    def test_a_key_without_the_phase_d_return_point_fails(self):
        texts = self.mutated("phase1", '"return_to": "module_7_step_3b | module_6_phase_d"',
                             '"return_to": "module_7_step_3b"')
        self.assertTrue(run("route", texts))

    def test_a_resume_that_skips_the_audits_fails(self):
        texts = self.mutated("phase1", "steps 21–28, the match-key and how-state\n   audits, "
                             "then the gate.", "the gate only.")
        self.assertTrue(run("route", texts))

    def test_a_resume_without_the_inv_284_clause_fails(self):
        texts = self.mutated("phase1", "⛔ **(INV-284) That too is a new state, NOT an INV-006 "
                             "repeat**, so present", "Present")
        self.assertTrue(run("route", texts))

    def test_an_interrupted_return_that_re_presents_the_gate_fails(self):
        texts = self.mutated("phase1", "do not re-present Phase D's gate or its source question",
                             "re-present Phase D's gate")
        self.assertTrue(run("route", texts))

    def test_a_reload_that_always_returns_to_step_3b_fails(self):
        texts = self.mutated("phase_b", "Then hand back to the\nkey's `return_to`",
                             "Then return to Module 7 step 3b's resume, ignoring the\nkey's "
                             "`return_to`")
        self.assertTrue(run("receiving", texts))

    def test_a_remap_branch_naming_only_module_7_fails(self):
        texts = self.mutated("m5_phase2", "or at Module 6 Phase D's gate (the key's\n`return_to` "
                             "says which)", "only")
        self.assertTrue(run("receiving", texts))

    def test_the_old_module_6_first_clause_fails(self):
        texts = self.mutated("m6_skill", "route by its `stage`, at the first\nsource not listed "
                             "in `completed`. `reload` goes straight to Phase B",
                             "go straight to Phase B")
        self.assertTrue(run("first", texts))

    def test_removing_the_module_6_recap_record_fails(self):
        para = span(self.texts["phase_d"], "The Module 6 recap section records every quality "
                    "iteration.", "\n\n")
        self.assertIsNotNone(para)
        texts = dict(self.texts)
        texts["phase_d"] = plain(texts["phase_d"]).replace(para, "", 1)
        self.assertTrue(run("recap", texts))


class ReWrapping(unittest.TestCase):
    """INV-346: re-flowed to one word per line, the live text passes and a regression fails."""

    def setUp(self):
        self.texts = {k: rewrap(v) for k, v in read_all().items()}

    def test_every_check_passes_on_rewrapped_text(self):
        for name in CHECKS:
            with self.subTest(check=name):
                self.assertEqual([], run(name, self.texts))

    def test_a_rewrapped_regression_is_still_caught(self):
        texts = dict(self.texts)
        texts["phase_d"] = re.sub(r"ask\s+no\s+second\s+confirmation",
                                  "confirm\nonce\nmore", texts["phase_d"], count=1)
        self.assertNotEqual(texts["phase_d"], self.texts["phase_d"])
        self.assertTrue(run("handling", texts))


if __name__ == "__main__":
    unittest.main()
