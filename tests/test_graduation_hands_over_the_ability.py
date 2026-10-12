"""Graduation hands over the ability, not only the things (#481).

Graduation used to summarize artifacts: a recap PDF and a `production/` project. It never drew
on the decisions the Bootcamper recorded, and it never named how to start the next build with an
AI assistant and the Senzing MCP server, without the bootcamp's script. #481 adds a step right
after the Step 0 retrospective that shows "Decisions you made" and "How you got it built", asks for
a one-line takeaway and then a "Next time" request in turns of their own, folds all four into the
recap inside a `BOOTCAMP-HANDOVER` fence, carries them into `docs/REVISIT_BOOTCAMP.md`, and closes
by stating there is no script from here and repeating the request.

These are **static** checks on shipped prose, plus one cross-check that the fence the skill
tells the guide to write is the fence the generator lifts. Whether a live turn draws the lists
only from the recorded recap is a conversational property that only `dry-run` phase 3 can judge
(INV-108 keeps this suite offline). The renderer's half is `tests/test_recap_handover_section.py`.

The checks read whitespace-collapsed sections, so a phrase that wraps still matches (INV-346).

Source issue: #481 (part of #465). INV-358 names this file as its enforcer; the three Step 0b ⛔
assertions require its citation, and passing them is no evidence that a live graduation draws only
from the record or keeps the Bootcamper's words.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"
GRADUATE_COMMAND = PLUGIN / "commands" / "graduate.md"
PHASE_A = PLUGIN / "skills" / "module-06-data-processing" / "phaseA-build-loading.md"
SCRIPT = PLUGIN / "scripts" / "generate_recap_pdf.py"

TAKEAWAY_QUESTION = (
    '👉 **In one line, what will you take away from this bootcamp?** '
    '(Reply "skip" to leave it out.)')
NEXT_TIME_QUESTION = (
    "👉 **Next time there is no bootcamp script: what one request would you give an AI "
    "assistant with the Senzing MCP server to start a build on a new source of your own "
    "data?**")
CLOSING_QUESTION = "👉 **Is there anything else you would like to explore?**"
PINNED_QUESTION = re.compile(r"(?m)^> 👉 \*\*.*$")


def load_generator():
    spec = importlib.util.spec_from_file_location("recap_gen_for_handover_prose", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["recap_gen_for_handover_prose"] = module
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text).strip()


def section(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


TEXT = read(GRADUATION)
STEP_0B = section(TEXT, "## Step 0b:", "\n## Step 1:")
FLAT_0B = squash(STEP_0B)
STEP_1A = section(TEXT, "### 1a. Reconcile the recap", "### 1b. Render the PDF")
STEP_6C = section(TEXT, "### 6c. Return guide", "## Step 7:")
CLOSING = section(TEXT, "## Mandatory closing step", "4. **Terminal banner")
CLOSING_INSTRUCTION = CLOSING[:CLOSING.index("Example (list only what exists)")]
CLOSING_EXAMPLE = CLOSING[CLOSING.index("Example (list only what exists)"):]


class TheStepSitsRightAfterStepZero(unittest.TestCase):

    def test_step_0b_is_between_step_0_and_step_1(self):
        self.assertLess(TEXT.index("## Step 0: Session retrospective"), TEXT.index("## Step 0b:"))
        self.assertLess(TEXT.index("## Step 0b:"), TEXT.index("## Step 1: Finalize the recap"))

    def test_the_section_is_not_vacuous(self):
        self.assertGreater(len(STEP_0B), 2000, "Step 0b collapsed to a stub")

    def test_both_answers_are_asked_before_the_pdf_is_rendered(self):
        self.assertIn("before** Step 1 renders the recap PDF", FLAT_0B)
        self.assertLess(TEXT.index(NEXT_TIME_QUESTION), TEXT.index("### 1b. Render the PDF"))

    def test_the_preface_overview_names_it_in_order(self):
        preface = squash(section(TEXT, "## Bootcamp graduation preface",
                                 "## Best-value model/effort prompt"))
        overview = preface[preface.index("**What we'll do.**"):
                           preface.index("**Estimated time.**")]
        step = overview.index("(2) look back at the decisions you made and how you got it built")
        self.assertIn("one-line takeaway", overview)
        self.assertIn("the one request you would give an AI assistant next time", overview)
        self.assertLess(overview.index("(1) note anything that tripped us up"), step)
        self.assertLess(step, overview.index("(3) normalize the `docs/` Markdown"))
        self.assertIn("(6) close with the END OF SENZING BOOTCAMP banner", overview)

    def test_the_graduate_command_names_it(self):
        flat = squash(read(GRADUATE_COMMAND))
        self.assertIn("show the decisions the bootcamper made and how they got it built", flat)
        self.assertIn('"Next time" request', flat)


class TheTwoListsComeFromTheRecordOnly(unittest.TestCase):

    def test_decisions_come_from_questions_and_responses(self):
        decisions = FLAT_0B[FLAT_0B.index("**Decisions you made:**"):
                            FLAT_0B.index("**How you got it built:**")]
        self.assertIn("**Questions & Responses**", decisions)
        self.assertIn("module-completion.md", decisions)
        self.assertIn("**chose something**", decisions)
        self.assertIn("a menu choice", decisions)
        self.assertIn("an open answer that set a direction", decisions)

    def test_readiness_teardown_and_consent_gates_are_left_out(self):
        self.assertIn("⛔ **(INV-358) Readiness, teardown and consent gates are not decisions.**", FLAT_0B)

    def test_how_it_got_built_is_one_line_per_module_from_both_subsections(self):
        built = FLAT_0B[FLAT_0B.index("**How you got it built:**"):
                        FLAT_0B.index("⛔ **(INV-358) Readiness")]
        self.assertIn("one line per module", built)
        self.assertIn("with the Senzing MCP server", built)
        self.assertIn("**Questions & Responses**", built)
        self.assertIn("**Actions Taken**", built)
        self.assertIn("A module with neither adds no line.", built)

    def test_nothing_is_invented_and_an_empty_list_is_left_out(self):
        self.assertIn("⛔ **(INV-358) Both lists come from the recorded recap and nothing else.**", FLAT_0B)
        self.assertIn("Never invent a decision", FLAT_0B)
        self.assertIn('A list with no supporting entries is left out: no heading, no "(none)".',
                      FLAT_0B)


class EachQuestionHasATurnOfItsOwn(unittest.TestCase):
    """INV-251 — exactly one 👉 ends each yielding turn; both questions pinned (INV-056)."""

    def test_step_0b_pins_exactly_the_two_questions(self):
        pinned = PINNED_QUESTION.findall(STEP_0B)
        self.assertEqual(2, len(pinned), pinned)
        self.assertEqual("> " + TAKEAWAY_QUESTION, pinned[0])
        self.assertTrue(pinned[1].startswith("> " + NEXT_TIME_QUESTION), pinned[1])

    def test_the_takeaway_ends_the_turn_that_shows_the_lists(self):
        turn = FLAT_0B[FLAT_0B.index("**The takeaway turn.**"):
                       FLAT_0B.index('**The "Next time" turn.**')]
        self.assertIn("Show both lists", turn)
        self.assertIn("end the turn on exactly one 👉 question (INV-251)", turn)
        self.assertEqual(1, turn.count("> 👉"))

    def test_next_time_is_asked_in_the_next_turn(self):
        turn = FLAT_0B[FLAT_0B.index('**The "Next time" turn.**'):]
        self.assertIn("In the next turn, end on exactly one 👉 question (INV-251)", turn)
        self.assertEqual(1, turn.count("> 👉"))

    def test_the_next_time_question_asks_for_their_own_data(self):
        self.assertIn("a new source of your own data", NEXT_TIME_QUESTION)
        self.assertIn("(Name the data or domain.", FLAT_0B)

    def test_the_draft_is_a_statement_and_the_step_continues(self):
        self.assertIn("Offering it is a statement, not a question", FLAT_0B)
        self.assertIn("Then continue to Step 1 in the same turn.", FLAT_0B)


class TheAnswersStayTheBootcampers(unittest.TestCase):

    def test_the_takeaway_is_recorded_in_their_words(self):
        self.assertIn("Record the answer in the Bootcamper's words, as given", FLAT_0B)

    def test_no_takeaway_means_no_line_never_na(self):
        self.assertIn('the line is left out, never written as "N/A"', FLAT_0B)

    def test_a_pass_gets_one_draft_from_their_data_labeled_as_the_guides(self):
        self.assertIn("offer **one** draft request drawn from their data", FLAT_0B)
        self.assertIn("`docs/business_problem.md`", FLAT_0B)
        self.assertIn("`config/data_sources.yaml`", FLAT_0B)
        self.assertIn("⛔ **(INV-358) The guide's draft is labeled as the guide's, wherever it is recorded.**",
                      FLAT_0B)
        self.assertIn("`**The guide's draft (you passed):** {the draft}`", FLAT_0B)
        self.assertIn("never as their words", FLAT_0B)

    def test_a_re_run_does_not_re_ask(self):
        self.assertIn("is not asked again (INV-006)", FLAT_0B)


class StepOneAFoldsItBehindItsOwnFence(unittest.TestCase):

    def setUp(self):
        self.flat = squash(STEP_1A)
        block = re.search(r"```markdown\n(<!-- BOOTCAMP-HANDOVER:START -->.*?)```", STEP_1A, re.S)
        self.assertIsNotNone(block, "Step 1a carries no handover fence template")
        self.template = block.group(1)

    def test_the_markers_are_the_generators(self):
        """The fence the skill writes is the fence the generator lifts — one pair, two files."""
        self.assertTrue(self.template.startswith(GEN.BOOTCAMP_HANDOVER_START))
        self.assertTrue(self.template.rstrip().endswith(GEN.BOOTCAMP_HANDOVER_END))
        self.assertIn("## " + GEN.BOOTCAMP_HANDOVER_TITLE + "\n", self.template)

    def test_the_template_parses_as_a_handover_and_never_as_a_module(self):
        recap = GEN.parse_recap(
            "# Senzing Bootcamp Recap\n\n## Data processing — 2026-10-11\n\n"
            "### Actions Taken\n\n- Loaded both sources.\n\n" + self.template)
        self.assertEqual(["Data processing"], [m.title for m in recap.modules])
        self.assertEqual(
            ["Decisions you made", "How you got it built", "Your takeaway", "Next time"],
            [h for h, _ in recap.handover.parts])

    def test_the_fold_follows_the_notes_fold_and_precedes_normalize(self):
        notes = STEP_1A.index("<!-- BOOTCAMP-NOTES:START -->")
        handover = STEP_1A.index(GEN.BOOTCAMP_HANDOVER_START)
        normalize = STEP_1A.index("**Normalize the Markdown (once, before rendering).**")
        self.assertLess(notes, handover)
        self.assertLess(handover, normalize)
        self.assertIn("after the notes block", self.flat)

    def test_it_cites_the_fence_rule_and_the_renderer_contract(self):
        self.assertIn("⛔ **(INV-258) The fence keeps the handover out of the modules, not its "
                      "heading.**", self.flat)
        self.assertIn("prints it as its own page", self.flat)
        self.assertIn("`--check` never counts it as a module", self.flat)

    def test_a_re_run_replaces_and_never_appends(self):
        self.assertIn("**Replace, never append (INV-085).**", self.flat)
        self.assertIn("never write a second block", self.flat)

    def test_nothing_recorded_means_no_fence(self):
        self.assertIn("⛔ **When all four are absent, write no fence (INV-258)**", self.flat)
        self.assertIn('no heading and no "(none)" page', self.flat)


class TheReturnGuideCarriesThem(unittest.TestCase):

    def test_revisit_carries_both_lists_and_the_request(self):
        flat = squash(STEP_6C)
        self.assertIn("**Decisions you made** and **How you got it built**", flat)
        self.assertIn("**Next time**", flat)
        self.assertIn("labeled as the guide's draft when it is one", flat)


class TheClosingHandsItOver(unittest.TestCase):

    def test_the_instruction_states_no_script_and_repeats_the_request(self):
        flat = squash(CLOSING_INSTRUCTION)
        self.assertIn('**State that from here there is no script, and repeat the "Next time" '
                      'request.**', flat)
        self.assertIn("as statements", flat)
        self.assertIn("⛔ **(INV-251) Neither sentence is a question, and neither adds a 👉.**",
                      flat)

    def test_the_example_models_both_statements_without_a_question(self):
        example = squash(CLOSING_EXAMPLE[:CLOSING_EXAMPLE.index("\n\n", CLOSING_EXAMPLE.index(">"))])
        tail = example[example.index("From here there is no script"):]
        self.assertIn("Next time, start with your own request", tail)
        self.assertNotIn("?", tail, "the no-script statement reads as a question")
        self.assertNotIn("👉", tail)

    def test_the_closing_question_is_unchanged_and_still_the_only_one(self):
        pinned = PINNED_QUESTION.findall(CLOSING)
        self.assertEqual(["> " + CLOSING_QUESTION], pinned)
        self.assertIn("The turn still ends on the unchanged closing question in item 3.",
                      squash(CLOSING_INSTRUCTION))


class YoursMeansTheDecisionsToo(unittest.TestCase):

    def test_phase_a_points_yours_at_the_decisions(self):
        flat = squash(read(PHASE_A).replace("\n> ", "\n"))
        self.assertIn("This program is yours to take home, and so are the decisions behind it, "
                      "starting with this one.", flat)


class StaysLanguageAgnostic(unittest.TestCase):
    """The new prose names no language, runtime or shell (INVARIANTS.md cross-cutting)."""

    def test_the_new_prose_names_no_language(self):
        closing = CLOSING_INSTRUCTION[CLOSING_INSTRUCTION.index("**State that from here"):]
        closing = closing[:closing.index("**Also name the two keepsake documents")]
        fold = STEP_1A[STEP_1A.index("**Fold the handover into the recap"):
                       STEP_1A.index("**Normalize the Markdown")]
        new_prose = " ".join((STEP_0B, fold, closing))
        for word in ("python", "java", "c#", "typescript", "bash", "powershell", ".py"):
            with self.subTest(word=word):
                self.assertNotIn(word, new_prose.lower())


if __name__ == "__main__":
    unittest.main()
