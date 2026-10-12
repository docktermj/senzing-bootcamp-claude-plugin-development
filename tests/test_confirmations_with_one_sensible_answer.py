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
   route, iterate the no route, with no 👉 at step 25.

The kept gates (candidates 3, 4, 5, 7 and 8) are pinned by their own tests; ``KeptGates`` checks
only that each still stands at its site, so a later "tidy" of this issue's kind cannot take one.

⛔ Each check is a pure function of the file text, so the negative controls run the SAME check on
a mutated copy (INV-265): restoring either removed question, or dropping candidate 6's condition,
must make it report a problem.

These assert that the skill files STATE the rules; they cannot establish that a live run follows
them, which only `dry-run` phase 3 can observe. Stdlib only; nothing under ``plugins/`` is
imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
M7 = SKILLS / "module-07-query-visualize-discover"
M5 = SKILLS / "module-05-data-quality-mapping"
PHASE2B = M7 / "phase2b-discover.md"
M7_PHASE1 = M7 / "phase1-query-visualize.md"
M5_PHASE2 = M5 / "phase2-data-mapping.md"
M5_PHASE3 = M5 / "phase3-test-load.md"

RETIRED_DISCOVER = "Would you like to continue to module completion now?"
RETIRED_PAYLOAD = "Shall I store it as `{KEY}_PAYLOAD` instead"
STEP25_QUESTION = "👉 **Are you ready to proceed?** (respond yes or no)"
TEARDOWN = "## Visualization server teardown (its own turn)"
GRADUATION_OFFER = "👉 **Would you like to graduate now and generate your production project and recap?**"


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
        "then to the Query Completeness Gate in `phase1-query-visualize.md`",
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
                "then to the Query Completeness Gate in", "then wait before", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], discover_problems(mutant))


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
