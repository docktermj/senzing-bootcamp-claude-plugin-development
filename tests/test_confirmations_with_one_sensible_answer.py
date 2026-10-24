"""Confirmations with only one sensible answer are removed, so a "yes" carries a decision (#488).

The same yes/no form served trivial and irreversible gates alike, and each confirmation with one
sensible answer trained the automatic "yes" that lets meaning drift at the gates that matter.
#488 settled eight candidates. These tests pin the three that changed:

1. **Candidate 1, Discover's "Would you like to continue to module completion now?"** Both answers
   took the same route. Since #487 it sat at the end of step 4e (the export), so step 4e now closes
   with no question: the turn that settles the last offer runs on to Discover phase completion and
   the Query Completeness Gate, and ends on the visualization server teardown 👉, or on the
   graduation offer when no server was started. Every Discover exit still runs step 4e.
2. **Candidate 2, Module 5's "Shall I store it as `{KEY}_PAYLOAD` instead…?"** The Bootcamper had
   already answered "payload"; only the key name was wrong. The guide renames the key, says so in
   one line, records it in the mapping table's reasoning column, and asks nothing.
3. **Candidate 6, Module 5 step 25's "Are you ready to proceed?"** It is asked only when step
   24d's gate was not presented. When it was, step 25 follows that answer: accept takes the yes
   route, iterate the no route, with no 👉 at step 25. INV-344's 2026-10-11 dated note names this
   file as its enforcer: these tests pin that step 25 states the rule, and do NOT establish that a
   live run follows step 24d's answer or keeps step 25 silent.

#517 swept the Module 5 Phase 3 text that still described the behavior #488 removed
(``Phase3SaysWhereIterateGoes``): the SCHEMA finding resolves a collision as step 11 does (rename
the key and say so, never "offer the rename"); step 24d's "If rejected" keeps the baseline and
says iterate returns to Phase 2 step 17, with re-entry to Phase 3 needing **test_load** at step
18a again (never "Inform the bootcamper they can return"); and step 25 points to that statement
rather than restating it (INV-300), naming the same step 17 on its **no** route (never "Step 24d
already told the Bootcamper they can return to Phase 2"). Those checks read
the text through `tests/_wrapped_text.py` (INV-346), so a re-wrap neither hides a retired phrase
nor fails a correct one; the negative controls include re-wrapped and reworded variants.

Candidate 1's close is also what INV-356's proposed #517 amendment states: each export offer is
its own turn, and the turn that settles the last one ends on the next 👉 the flow already has.

#521 makes candidate 6 survive an interruption: step 24d writes its answer (`accept` or
`iterate`) as its checkpoint, and "Phase 3 session resume" follows a recorded answer at step 25
without asking either question again, falling back to step 25 when there is no record (a first
test load, or a progress file written before #521). The record is stated once, at step 24d's
checkpoint, and resume points to it rather than restating it (INV-300; grafted from #521's losing
strategy B). ``Step24dAnswerSurvivesAnInterruption`` pins both sites, the pointer, and that resume
carries no copy of the record, again only that the file STATES them.

The kept gates (candidates 3, 4, 5, 7 and 8) are pinned by their own tests; ``KeptGates`` checks
only that each still stands at its site, so a later "tidy" of this issue's kind cannot take one.

⛔ Each check is a pure function of the file text, so the negative controls run the SAME check on
a mutated copy (INV-265): restoring either removed question, or dropping candidate 6's condition,
must make it report a problem. For #517 the controls also run re-wrapped copies, which must
report the same thing as the text they re-wrap.

#781 carries candidate 1's close through to its end. The Query Completeness Gate's item 6 still
asked "Ready to proceed?" after step 4e's no-question close, and the Discover exits named the gate
but not the deliverable before it. ``Issue781GateRoutesOnUnasked`` pins that item 6, the gate's last
item, asks nothing (no 👉, no question mark) and routes to the visualization server teardown or,
when no server was started, to module completion; that every sentence in a Discover file naming
the Query Completeness Gate names "Data-discoveries deliverable" before it (the exits in
`phase2-discover.md` and `phase2b-discover.md`, and Phase 1's step-4e convergence pointer); that
the exit option no longer says "Proceed to module completion"; and that the module overview names
the teardown turn. Its negative controls put back a question in item 6, an exit that names the
gate without the deliverable, the retired label, and an overview without the teardown.

These assert that the skill files STATE the rules; they cannot establish that a live run follows
them, which only `dry-run` phase 3 can observe. Stdlib only; nothing under ``plugins/`` is
imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
M7 = SKILLS / "module-07-query-visualize-discover"
M5 = SKILLS / "module-05-data-quality-mapping"
PHASE2B = M7 / "phase2b-discover.md"
M7_PHASE1 = M7 / "phase1-query-visualize.md"
M5_PHASE2 = M5 / "phase2-data-mapping.md"
M5_PHASE3 = M5 / "phase3-test-load.md"
PHASE2A = M7 / "phase2-discover.md"
M7_SKILL = M7 / "SKILL.md"

RETIRED_DISCOVER = "Would you like to continue to module completion now?"
RETIRED_PAYLOAD = "Shall I store it as `{KEY}_PAYLOAD` instead"
STEP25_QUESTION = "👉 **Are you ready to proceed?** (respond yes or no)"
TEARDOWN = "## Visualization server teardown (its own turn)"
GRADUATION_OFFER = "👉 **Would you like to graduate now and generate your production project and recap?**"
#: Retired by #517: step 11 renames the key and says so, and asks nothing (#488).
RETIRED_RENAME_OFFER = "offer the rename"
#: Retired by #517: step 25 routes iterate to Phase 2 step 17 itself (#488), so this is not optional.
RETIRED_RETURN_NOTICE = "Inform the bootcamper they can return"
#: Retired by #517: step 25 leaned on step 24d's optional wording; it now points to 24d's statement.
RETIRED_STEP25_TOLD = "Step 24d already told the Bootcamper they can return to Phase 2"


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    """Whitespace-collapsed, so an assertion survives a re-wrap of the paragraph."""
    return re.sub(r"\s+", " ", text)


def between(text, start, end):
    """The text from ``start`` up to (not including) ``end``, or None when either is absent."""
    i = text.find(start)
    if i == -1:
        return None
    j = text.find(end, i + len(start))
    return None if j == -1 else text[i:j]


def says(text, pattern):
    """True when ``pattern`` matches inside one Markdown block of ``text``, across any wrap (INV-346)."""
    return bool(match_lines(text, re.compile(pattern)))


def need(block, needles, where):
    f = flat(block)
    return ["%s does not say %r" % (where, n) for n in needles if flat(n) not in f]


# ------------------------------------------------------------------------------------- checks


def discover_problems(text):
    """Candidate 1, inside `phase2b-discover.md`."""
    problems = []
    if RETIRED_DISCOVER in flat(text):
        problems.append("the retired 'continue to module completion now?' question is back")
    step_4d = between(text, "### Step 4d:", "### Step 4e:")
    if step_4d is None:
        return problems + ["step 4d or step 4e moved"]
    problems += need(step_4d, ("continue to step 4e below", "Ask no transition question here"),
                     "step 4d's transition")
    close = between(text, "**Close: no transition question.**", "**Checkpoint:** write step 4e")
    if close is None:
        return problems + ["step 4e has no close before its checkpoint"]
    if re.search(r"👉\s*\*\*", close):
        problems.append("step 4e's close asks a 👉 question of its own")
    problems += need(close, (
        "ask no question about moving on",
        "Both answers to one would take the same route",
        "In the same turn that settles the last offer, continue to Discover phase completion below",
        "then to `phase1-query-visualize.md` → \"Data-discoveries deliverable\" and its Query "
        "Completeness Gate",
        "End that turn on the next 👉 the flow already has, never on a new one (INV-251)",
        "the visualization server teardown question",
        "when no server was started, the graduation offer",
        "Each offer above still ends its own turn",
        "or from a Discover exit",
    ), "step 4e's close")
    return problems


def payload_problems(text):
    """Candidate 2, inside `phase2-data-mapping.md`."""
    problems = []
    if RETIRED_PAYLOAD in flat(text):
        problems.append("the retired {KEY}_PAYLOAD question is back")
    block = between(text, "**On a collision, do NOT silently re-route or override the answer",
                    "⚠️ **A list-valued field routed to `payload`")
    if block is None:
        return problems + ["the collision paragraph moved"]
    if re.search(r"👉\s*\*\*", block):
        problems.append("the collision paragraph asks a 👉 question")
    problems += need(block, (
        "**Emit `{KEY}_PAYLOAD`** in place of `{KEY}`",
        "**Say so in one line, as a statement**, naming the field and why",
        "`{KEY}` is a registered Senzing feature attribute",
        "at the record root Senzing will resolve on it anyway",
        "**Record the rename in the mapping table's reasoning column**",
        "**Ask no question for it.** The turn continues to the step's next question",
        "they can say so at any time, and the mapping is changed back",
    ), "the collision paragraph")
    return problems


def step25_problems(text):
    """Candidate 6, inside `phase3-test-load.md`."""
    problems = []
    s25 = between(text, "### 25.", '<a id="leaving-phase-3"></a>')
    if s25 is None:
        return ["step 25 moved"]
    not_presented = "**Step 24d's gate was not presented**"
    presented = "**Step 24d's gate was presented:**"
    for label in (not_presented, presented):
        if s25.count(label) != 1:
            problems.append("step 25 does not name the case %r once" % label)
    if s25.count(STEP25_QUESTION) != 1:
        problems.append("step 25's pinned question is not kept verbatim once")
    if s25.count("👉") != 1:
        problems.append("step 25 carries a second 👉")
    if not problems and not (s25.index(not_presented) < s25.index(STEP25_QUESTION)
                             < s25.index(presented)):
        problems.append("step 25's question is not inside the not-presented case")
    if presented in s25:
        case = s25[s25.index(presented):s25.index("**Data source registry:**")]
        problems += need(case, (
            "its answer already settled accept or iterate, so ask nothing here",
            "**accept** (its option 1) takes the **yes** route below",
            "**iterate** (its option 2) takes the **no** route",
            "do not repeat that offer as a question",
        ), "step 25's presented case")
    problems += need(s25, ("Handling (INV-284)", "**yes** → Phase 2 step 19",
                           "**no** → Phase 2 step 17"), "step 25")
    return problems


def phase3_exit_problems(text):
    """#517, inside `phase3-test-load.md`: the text #488 left stale says what the steps now do."""
    problems = []
    for phrase in (RETIRED_RENAME_OFFER, RETIRED_RETURN_NOTICE, RETIRED_STEP25_TOLD):
        if says(text, r"(?i)" + re.escape(phrase)):
            problems.append("the retired phrase %r is back" % phrase)
    if not says(text, r"as step 11 prescribes\b[^.]*\brename the key and say so\b[^.]*"
                      r"\bnever silently re-route\b"):
        problems.append("the SCHEMA finding does not resolve a collision as step 11 does "
                        "(rename the key and say so, never silently re-route)")
    s24d = between(text, "#### 24d.", "### 25.")
    case = between(text, "**Step 24d's gate was presented:**", "**Data source registry:**")
    if s24d is None or case is None:
        return problems + ["step 24d or step 25's presented case moved"]
    rejected = re.search(r"\*\*If rejected:\*\*(.*?)(?=\n\S|\Z)", s24d, re.S)
    if rejected is None:
        return problems + ["step 24d has no **If rejected:** item"]
    rejected = rejected.group(0)
    if not says(rejected, r"Keep the existing baseline unchanged\."):
        problems.append("step 24d's If rejected does not keep the baseline unchanged")
    if not says(rejected, r"\b[Ii]terate\b[^.]*\breturns to Phase 2 step \d+"):
        problems.append("step 24d's If rejected does not say where iterate returns")
    if not says(rejected, r"\bRe-entering Phase 3\b[^.]*\*\*test_load\*\* at step 18a again"):
        problems.append("step 24d does not say re-entering Phase 3 needs test_load at step 18a")
    if not says(case, r"\bStep 24d's \*\*If rejected\*\* line already states where iterate goes\b"):
        problems.append("step 25's presented case does not point to step 24d's statement")
    if says(case, r"\bPhase 2\b"):
        problems.append("step 25's presented case restates where iterate goes (INV-300)")
    # Both sites must name ONE destination: step 24d's statement and step 25's **no** route.
    told = re.search(r"returns to Phase 2 step (\d+)", flat(rejected))
    routed = re.search(r"\*\*no\*\* → Phase 2 step (\d+)", flat(text))
    if told and routed and told.group(1) != routed.group(1):
        problems.append("step 24d sends iterate to step %s, step 25's no route to step %s"
                        % (told.group(1), routed.group(1)))
    return problems


STEP24D_CHECKPOINT = ("**Checkpoint:** when this gate was presented, write step 24d to "
                      "`config/bootcamp_progress.json` with its answer, `accept` or `iterate`.")


def step24d_checkpoint_problems(text):
    """#521: step 24d records its answer, so an interruption before step 25 does not lose it."""
    s24d = between(text, "#### 24d.", "### 25.")
    if s24d is None:
        return ["step 24d moved"]
    problems = need(s24d, (STEP24D_CHECKPOINT,
                           "On a first test load it was not presented, so there is nothing to "
                           "record."), "step 24d")
    if not problems and flat(s24d).find(flat(STEP24D_CHECKPOINT)) < flat(s24d).find(
            "*(Internal: end the turn on this question and wait.)*"):
        problems.append("step 24d's checkpoint comes before its question is answered")
    return problems


def resume_problems(text):
    """#521: "Phase 3 session resume" follows a recorded step 24d answer at step 25, unasked."""
    resume = between(text, "## Phase 3 session resume", "## Rules")
    if resume is None:
        return ["Phase 3 session resume moved"]
    problems = need(resume, (
        "When step 24d's answer is recorded (the record is stated once, at step 24d's "
        "**Checkpoint**; INV-300), that answer already settled step 25",
        "present the Phase 3 results again as statements, ask nothing, and follow the recorded "
        "answer, `accept` by the **yes** route and `iterate` by the **no** route",
        "Ask neither step 24d's question nor step 25's again (INV-006)",
        "With no step 24d record (a first test load, or a progress file written before step 24d "
        "recorded its answer), resume from step 25 as above",
    ), "Phase 3 session resume")
    if "👉" in resume:
        problems.append("Phase 3 session resume asks a 👉 question")
    # INV-300: what the record holds, and where it is written, is stated at step 24d only.
    for copy in ("write step 24d", "with its answer, `accept` or `iterate`",
                 "records step 24d with its answer"):
        if copy in flat(resume):
            problems.append("Phase 3 session resume restates step 24d's record (%r) instead of "
                            "pointing to its checkpoint" % copy)
    s24d = between(text, "#### 24d.", "### 25.")
    if s24d is None or "**Checkpoint:** when this gate was presented, write step 24d" not in s24d:
        problems.append("Phase 3 session resume points to a step 24d checkpoint that is not there")
    return problems


#: #781: the Discover exit option's retired label, which skipped step 4e, the deliverable,
#: the gate and the teardown.
RETIRED_EXIT_LABEL = "Proceed to module completion"
EXIT_LABEL = "2. Wrap up: the export offer, your discoveries document, then module completion."
GATE_NAME = "Query Completeness Gate"
DELIVERABLE = "Data-discoveries deliverable"
#: Every Discover exit plus Phase 1's step-4e convergence pointer: three in each Discover file,
#: one in Phase 1 (INV-265: a scan that finds fewer has stopped reading the files).
MIN_EXIT_SENTENCES = 7


def gate_item6_problems(text):
    """#781: the gate's item 6 asks nothing and routes on, found by its number, not its label."""
    gate = between(text, "## Query Completeness Gate", TEARDOWN)
    if gate is None:
        return ["the Query Completeness Gate or the teardown section moved"]
    found = re.search(r"^6\. ", gate, re.M)
    if found is None:
        return ["the gate has no item 6"]
    item = gate[found.start():]
    problems = []
    if re.search(r"^\d+\. ", item[3:], re.M):
        problems.append("item 6 is not the gate's last item")
    if "👉" in item:
        problems.append("item 6 carries a 👉")
    if "?" in item:
        problems.append("item 6 asks a question")
    problems += need(item, (
        "asks the Bootcamper nothing and adds no question of its own (INV-251)",
        'continue to "Visualization server teardown" below',
        "when no server was started, straight to module completion and its graduation offer",
    ), "item 6")
    return problems


def sentences(text):
    """Each sentence of each blank-line-separated block, whitespace collapsed (wrap-proof)."""
    out = []
    for block in re.split(r"\n\s*\n", text):
        out += re.split(r"(?<=[.!?])\s+(?=[A-Z(*⛔👉\"])", flat(block).strip())
    return out


def discover_exit_problems(texts):
    """#781: every sentence naming the gate in a Discover file names the deliverable first.

    ``texts`` maps a name to the text scanned: the two Discover files whole, and Phase 1's
    "Next: Discover phase (step 4)" section, which holds the step-4e convergence pointer.
    """
    problems, seen = [], 0
    for name, text in texts.items():
        if text is None:
            problems.append("%s: the section moved" % name)
            continue
        for sentence in sentences(text):
            if GATE_NAME not in sentence:
                continue
            seen += 1
            at = sentence.find(DELIVERABLE)
            if at < 0 or at > sentence.find(GATE_NAME):
                problems.append("%s: names the gate without the deliverable before it: %r"
                                % (name, sentence[:120]))
    if seen < MIN_EXIT_SENTENCES:
        problems.append("found %d exit sentences naming the gate, fewer than %d"
                        % (seen, MIN_EXIT_SENTENCES))
    return problems


def discover_texts(phase2a, phase2b, phase1):
    return {"phase2-discover.md": phase2a, "phase2b-discover.md": phase2b,
            "phase1-query-visualize.md step 4": between(
                phase1, "## Next: Discover phase (step 4)", "## Success criteria")}


def exit_label_problems(phase2a, skill):
    """#781: the exit option and the module overview name the steps that actually follow."""
    problems = []
    if RETIRED_EXIT_LABEL.lower() in flat(phase2a).lower():
        problems.append("the retired %r label is back" % RETIRED_EXIT_LABEL)
    if phase2a.count(EXIT_LABEL) != 2:
        problems.append("the two Discover exits do not both offer %r" % EXIT_LABEL)
    if phase2a.count('- **2, "Wrap up":** the exit above.') != 2:
        problems.append("the two exits' handling lines do not both name option 2 \"Wrap up\"")
    position = between(skill, "## Module position", "⛔ **Bootcamp graduation always follows")
    if position is None:
        return problems + ["SKILL.md's Module position moved"]
    problems += need(position, (
        "the visualization server teardown runs as its own turn when a server was started, then "
        "module completion and the graduation offer",), "SKILL.md's Module position")
    return problems


# -------------------------------------------------------------------------------------- tests


class Candidate1DiscoverClosesWithoutAQuestion(unittest.TestCase):

    def test_the_close(self):
        self.assertEqual([], discover_problems(read(PHASE2B)))

    def test_the_question_is_gone_from_the_whole_plugin(self):
        hits = [str(p.relative_to(REPO)) for p in sorted(PLUGIN.rglob("*.md"))
                if RETIRED_DISCOVER in flat(read(p))]
        self.assertEqual([], hits)

    def test_the_turn_ends_on_a_question_the_flow_already_has(self):
        """The teardown 👉, or the graduation offer when no server ran."""
        phase1 = read(M7_PHASE1)
        self.assertEqual(1, phase1.count(TEARDOWN))
        self.assertIn("**Skip this step silently if no server was started**", phase1)
        self.assertEqual(1, phase1.count(GRADUATION_OFFER))
        self.assertLess(phase1.index("## Query Completeness Gate"), phase1.index(TEARDOWN))
        self.assertLess(phase1.index(TEARDOWN), phase1.index(GRADUATION_OFFER))

    def test_negative_controls(self):
        text = read(PHASE2B)
        close = "**Close: no transition question.**"
        mutants = {
            "question restored after the offers": text.replace(
                "**Checkpoint:** write step 4e",
                "👉 **%s**\n\n**Checkpoint:** write step 4e" % RETIRED_DISCOVER, 1),
            "question restored in step 4d": text.replace(
                "### Step 4e:", "👉 **%s**\n\n### Step 4e:" % RETIRED_DISCOVER, 1),
            "close dropped": text.replace(close, "**Transition.**", 1),
            "close stops before the gate": text.replace(
                "and its Query Completeness Gate. End that turn", "and wait. End that turn", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], discover_problems(mutant))


class Issue781GateRoutesOnUnasked(unittest.TestCase):
    """#781: after step 4e's close, the turn runs through the deliverable and the gate unasked."""

    def setUp(self):
        self.phase1 = read(M7_PHASE1)
        self.phase2a = read(PHASE2A)
        self.phase2b = read(PHASE2B)
        self.skill = read(M7_SKILL)

    def test_item_6_asks_nothing_and_routes_on(self):
        self.assertEqual([], gate_item6_problems(self.phase1))

    def test_every_exit_returns_to_the_deliverable_first(self):
        self.assertEqual([], discover_exit_problems(
            discover_texts(self.phase2a, self.phase2b, self.phase1)))

    def test_the_exit_label_and_overview_name_what_follows(self):
        self.assertEqual([], exit_label_problems(self.phase2a, self.skill))

    def mutate(self, text, old, new):
        mutant = text.replace(old, new, 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies: %r" % old)
        return mutant

    def test_negative_controls_item_6(self):
        label = "6. **Route on in the same turn.**"
        mutants = {
            "the retired question restored": (label, "6. **Ready to proceed?** On a yes, continue."),
            "a 👉 added to item 6": (label, label + "\n\n   👉 **Shall I stop the server now**\n"),
            "the teardown route dropped": ('continue to\n   "Visualization server teardown" below',
                                           "continue"),
            "an item 7 after it": ("\n## Visualization server teardown",
                                   "7. **Anything else.**\n\n## Visualization server teardown"),
        }
        for name, (old, new) in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual([], gate_item6_problems(self.mutate(self.phase1, old, new)))

    def test_negative_controls_exits(self):
        old_exit = "and then return to `phase1-query-visualize.md` for the Query Completeness Gate."
        mutants = {
            "phase2-discover.md opt-in decline": ("phase2a", (
                'and then return to `phase1-query-visualize.md` → "Data-discoveries deliverable", '
                "then\n  its Query Completeness Gate.", old_exit)),
            "phase2-discover.md early exit, re-wrapped": ("phase2a", (
                'return to `phase1-query-visualize.md` →\n   "Data-discoveries deliverable", then '
                "its Query Completeness Gate.",
                "return to `phase1-query-visualize.md` for\n   the Query Completeness Gate.")),
            "phase2b-discover.md load note": ("phase2b", (
                'return to `phase1-query-visualize.md` → "Data-discoveries deliverable", then its '
                "Query\nCompleteness Gate.",
                "return to `phase1-query-visualize.md` for the Query\nCompleteness Gate.")),
            "phase2b-discover.md close": ("phase2b", (
                '`phase1-query-visualize.md` →\n"Data-discoveries deliverable" and its Query '
                "Completeness Gate.", "the Query Completeness Gate.")),
            "phase1 step-4e pointer": ("phase1", (
                'return here for "Data-discoveries deliverable" below, then the\nQuery '
                "Completeness Gate.", "return here for the Query Completeness Gate.")),
            "deliverable named after the gate": ("phase2b", (
                'After updating the `discover_phase` status, return to `phase1-query-visualize.md` '
                '→\n"Data-discoveries deliverable", then its Query Completeness Gate.',
                "After updating the `discover_phase` status, return to the Query Completeness "
                'Gate, then "Data-discoveries deliverable".')),
        }
        for name, (which, (old, new)) in mutants.items():
            with self.subTest(mutant=name):
                texts = {"phase1": self.phase1, "phase2a": self.phase2a, "phase2b": self.phase2b}
                texts[which] = self.mutate(texts[which], old, new)
                self.assertNotEqual([], discover_exit_problems(
                    discover_texts(texts["phase2a"], texts["phase2b"], texts["phase1"])))

    def test_negative_controls_label_and_overview(self):
        with self.subTest(mutant="the retired label restored"):
            mutant = self.mutate(self.phase2a, EXIT_LABEL, "2. %s." % RETIRED_EXIT_LABEL)
            self.assertNotEqual([], exit_label_problems(mutant, self.skill))
        with self.subTest(mutant="the overview drops the teardown"):
            mutant = self.mutate(
                self.skill, "the visualization server teardown runs as its own turn when a "
                "server was started, then\nmodule completion and the graduation offer",
                "run module completion and offer graduation")
            self.assertNotEqual([], exit_label_problems(self.phase2a, mutant))


class Candidate2RenamesThePayloadKey(unittest.TestCase):

    def test_the_rename(self):
        self.assertEqual([], payload_problems(read(M5_PHASE2)))

    def test_negative_controls(self):
        text = read(M5_PHASE2)
        anchor = "⚠️ **A list-valued field routed to `payload`"
        question = ("> 👉 **`{field}` is routed to payload, but `{KEY}` is a registered Senzing "
                    "feature attribute — at the record root Senzing will resolve on it anyway. "
                    "%s, so it rides along without matching?** (respond yes or no)\n\n"
                    % RETIRED_PAYLOAD)
        mutants = {
            "question restored": text.replace(anchor, question + anchor, 1),
            "any 👉 at the collision": text.replace(
                anchor, "👉 **Is that rename all right?**\n\n" + anchor, 1),
            "rename not recorded": text.replace(
                "**Record the rename in the mapping table's reasoning column**", "Note it", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], payload_problems(mutant))


class Candidate6Step25AsksOnlyWhenStep24dDidNot(unittest.TestCase):

    def test_the_condition(self):
        self.assertEqual([], step25_problems(read(M5_PHASE3)))

    def test_the_exit_table_names_step_24d_answers(self):
        text = read(M5_PHASE3)
        self.assertIn("| Step 25 **yes**, or step 24d's **accept** |", text)
        self.assertIn("| Step 25 **no**, or step 24d's **iterate** |", text)

    def test_negative_controls(self):
        text = read(M5_PHASE3)
        mutants = {
            "condition dropped": text.replace("**Step 24d's gate was presented:**",
                                              "**Otherwise:**", 1),
            "step 25 asks after step 24d": text.replace(
                "so ask nothing\n  here.", "so ask:\n\n👉 **Ready?**\n\n  here.", 1),
            "iterate re-offered as a question": text.replace(
                "do not repeat that offer as a question", "repeat that offer", 1),
            "accept route lost": text.replace(
                "**accept** (its option 1) takes\n  the **yes** route below", "accept moves on", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], step25_problems(mutant))


class Phase3SaysWhereIterateGoes(unittest.TestCase):
    """#517: step 24d, step 25 and the SCHEMA finding describe Phase 3's exits as they behave."""

    #: Re-wraps of the shipped text that change no word. Each must still report nothing.
    REWRAPS = {
        "step 24d's destination": ("Iterate returns to Phase 2 step 17 to\n  adjust",
                                   "Iterate returns to Phase 2\n  step 17 to adjust"),
        "step 24d's re-entry": ("**test_load** at\n  step 18a again",
                                "**test_load**\n  at step 18a again"),
        "step 25's pointer": ("Step 24d's\n  **If rejected** line already states where iterate goes",
                              "Step 24d's **If rejected**\n  line already states where\n  iterate goes"),
        "the SCHEMA finding": ("rename the key and say so, never silently re-route",
                               "rename the key\nand say so, never silently\nre-route"),
    }

    def setUp(self):
        self.text = read(M5_PHASE3)

    def mutate(self, old, new):
        mutant = self.text.replace(old, new, 1)
        self.assertNotEqual(self.text, mutant, "the mutation no longer applies: %r" % old)
        return mutant

    def test_the_exits(self):
        self.assertEqual([], phase3_exit_problems(self.text))

    def test_a_rewrap_changes_nothing(self):
        for name, (old, new) in self.REWRAPS.items():
            with self.subTest(rewrap=name):
                self.assertEqual([], phase3_exit_problems(self.mutate(old, new)))

    def test_negative_controls(self):
        rejected_now = between(self.text, "- **If rejected:**", "\n\n")
        retired_24d = ("- **If rejected:** Keep the existing baseline unchanged. Inform the "
                       "bootcamper they can return\n  to Phase 2 to adjust their mapping and "
                       "re-run Phase 3 to see updated results.")
        mutants = {
            "rename offer restored": (
                "rename the key and say so, never silently re-route",
                "offer the rename, never silently re-route"),
            "rename offer beside the rename, re-wrapped": (
                "never silently re-route — rather than",
                "never silently re-route, or offer the\nrename — rather than"),
            "rename offer restored, capitalized": (
                "prescribes — rename the key and say so, never",
                "prescribes — Offer the rename and say so, never"),
            "step 24d's retired wording restored": (rejected_now, retired_24d),
            "return notice restored, re-wrapped": (
                "say so as a statement.",
                "Inform the bootcamper they\n  can return to Phase 2 later."),
            "step 24d names no destination": (
                "Iterate returns to Phase 2 step 17 to\n  adjust",
                "Iterate goes back to the mapping to\n  adjust"),
            "step 24d and step 25 disagree": (
                "Iterate returns to Phase 2 step 17 to", "Iterate returns to Phase 2 step 16 to"),
            "re-entry by step 18a dropped": (
                "needs the bootcamper's explicit **test_load** at\n  step 18a again",
                "is the bootcamper's call"),
            "baseline no longer kept": (
                "**If rejected:** Keep the existing baseline unchanged.",
                "**If rejected:** Restore the previous baseline."),
            "step 25 points nowhere": (
                "Step 24d's\n  **If rejected** line already states where iterate goes",
                "Step 24d already\n  offered this"),
            "step 25 restates the destination": (
                "  The turn ends on the next question the route reaches (INV-251).",
                "  Iterate returns to Phase 2 step 17. The turn ends on the next question the "
                "route reaches (INV-251)."),
        }
        for name, (old, new) in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual([], phase3_exit_problems(self.mutate(old, new)))

    def test_the_old_step_25_sentence_is_reported_by_name(self):
        """Restoring step 25's pre-#517 sentence, wrapped as it shipped, reports that phrase itself.

        Asserting the message, not just a non-empty list, keeps this control honest: the restored
        sentence also names "Phase 2", which another check reports on its own.
        """
        mutants = {
            "as it shipped": "Step 24d already\n  told the Bootcamper they can return to Phase 2",
            "re-wrapped, lower case": "step 24d already told the\n  Bootcamper they can return to "
                                      "Phase\n  2",
        }
        for name, sentence in mutants.items():
            with self.subTest(mutant=name):
                mutant = self.mutate(
                    "Step 24d's\n  **If rejected** line already states where iterate goes",
                    sentence)
                self.assertIn("the retired phrase %r is back" % RETIRED_STEP25_TOLD,
                              phase3_exit_problems(mutant))


class Step24dAnswerSurvivesAnInterruption(unittest.TestCase):
    """#521: the 24d answer is checkpointed, and resume follows it at step 25 without asking."""

    def test_step_24d_checkpoints_its_answer(self):
        self.assertEqual([], step24d_checkpoint_problems(read(M5_PHASE3)))

    def test_resume_follows_the_recorded_answer(self):
        self.assertEqual([], resume_problems(read(M5_PHASE3)))

    def test_the_rules_hold_through_a_rewrap(self):
        """INV-346: a different wrap of the same words still passes."""
        text = read(M5_PHASE3)
        mutant = text.replace("ask nothing, and follow the recorded answer, `accept` by\nthe **yes** route",
                              "ask\nnothing, and follow the recorded answer, `accept` by the **yes** route", 1)
        mutant = mutant.replace("(the record is stated once, at step 24d's **Checkpoint**;\nINV-300), that",
                                "(the record is\nstated once, at step 24d's **Checkpoint**; INV-300), that", 1)
        mutant = mutant.replace("with\nits answer, `accept`", "with its\nanswer, `accept`", 1)
        self.assertNotEqual(text, mutant, "the re-wrap no longer applies")
        self.assertEqual([], step24d_checkpoint_problems(mutant))
        self.assertEqual([], resume_problems(mutant))

    def test_negative_controls(self):
        text = read(M5_PHASE3)
        checkpoint = {
            "checkpoint dropped": text.replace(
                "**Checkpoint:** when this gate was presented, write step 24d", "Then", 1),
            "answer not recorded": text.replace("with\nits answer, `accept` or `iterate`.",
                                                "and move on.", 1),
        }
        resume = {
            "resume asks again": text.replace(
                "Ask neither step 24d's question nor step 25's\nagain (INV-006).",
                "Ask step 25's question again:\n\n👉 **Ready?**", 1),
            "iterate route lost": text.replace("`iterate` by the **no** route",
                                               "`iterate` by the **yes**\nroute", 1),
            "pointer to step 24d's checkpoint dropped": text.replace(
                "When step 24d's answer is recorded (the record is stated once, at step 24d's "
                "**Checkpoint**;\nINV-300), that", "When step 24d was answered, that", 1),
            "the pointer's target is gone": text.replace(
                "**Checkpoint:** when this gate was presented, write step 24d", "Then", 1),
            "old progress file not handled": text.replace(
                "or a progress file written before step\n24d recorded its answer", "only", 1),
        }
        # The pointer kept, and the record restated beside it: reported as a restatement.
        restated = text.replace(
            "Ask neither step 24d's question nor step 25's\nagain (INV-006).",
            "Step 24d wrote `config/bootcamp_progress.json` with its answer, `accept` or\n"
            "`iterate`. Ask neither step 24d's question nor step 25's again (INV-006).", 1)
        with self.subTest(mutant="record restated beside the pointer"):
            self.assertNotEqual(text, restated, "the mutation no longer applies")
            self.assertTrue(any("restates step 24d's record" in p
                                for p in resume_problems(restated)), resume_problems(restated))
        for name, mutant in checkpoint.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], step24d_checkpoint_problems(mutant))
        for name, mutant in resume.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], resume_problems(mutant))


class KeptGates(unittest.TestCase):
    """Candidates 3, 4, 5, 7 and 8 are kept; their reasons are in the #488 ledger entry."""

    KEPT = {
        "3, the next-module transition": (
            SKILLS / "bootcamp-onboarding" / "module-completion.md",
            "Are you ready to move on to the next module"),
        "4, graduation (Module Completion)": (
            SKILLS / "bootcamp-onboarding" / "module-completion.md", GRADUATION_OFFER),
        "4, graduation (Module 7)": (M7_PHASE1, GRADUATION_OFFER),
        "5, Module 3b's pause to explore": (
            SKILLS / "module-03b-truthset-visualization" / "phase1-visualization.md",
            "👉 **Are you ready to continue?**"),
        "6, step 25 on a first test load": (M5_PHASE3, STEP25_QUESTION),
        "7, Module 6's generated-path question": (
            SKILLS / "module-06-data-processing" / "phaseC-multi-source.md",
            "shall I proceed on both?** (respond yes or no)"),
        "8, the model and effort wait": (
            SKILLS / "bootcamp-onboarding" / "ground-rules.md",
            "👉 **Are you done modifying the model and effort?**"),
    }

    def test_each_kept_gate_still_stands(self):
        for name, (path, wording) in self.KEPT.items():
            with self.subTest(candidate=name):
                self.assertIn(flat(wording), flat(read(path)))


if __name__ == "__main__":
    unittest.main()
