"""Interaction-layer defects a phase-3 dry-run walk found that static analysis cannot.

None of these is detectable by reading the plugin against itself — each needed an actual
conversational turn, which is why 937 tests and four static audits missed them. What they share is
prose written without the one-👉-per-turn constraint in view, or a rule whose text does not survive
the situation it governs:

* **Duration (item 1).** *"Do you have any questions before we get started?"* is the preface's only
  question, making "how long will this take?" close to the most likely thing a Bootcamper says at
  that point — and the plugin had no answer. No per-module figures exist to sum, so a guide had to
  improvise a total at exactly the moment INV-096 exists to stop it inventing one.
* **The re-present (item 3).** Module 0 said answer the question "then re-present" a 👉 whose wording
  INV-056 fixes verbatim — so the Bootcamper gets the identical string back immediately after asking
  something, which reads as though their question did not register. The preface solves the same
  moment with "other questions"; Module 0 could not, without paraphrasing a pinned string.
* **Order (item 4).** Step 3 said "wait for the answer, then … tell them they can change it any
  time" — a reassurance that cannot inform the choice once the choice is made, and that cannot
  follow the 👉 either, because INV-251 requires the question to end the turn.
* **The knowledge check (items 5, 6).** The rules specified difficulty, sourcing, count and the
  exit path, and
  said only "evaluating the bootcamper's answer" — nothing about what to do when it is **wrong**,
  the highest-value moment in a module whose purpose is to reinforce concepts. Nor what shape an
  answer takes, leaving open-ended items permitted by silence and outside INV-051/INV-008.
* **BM25 (item 7).** A missed `search_docs` query is indistinguishable from documentation that does
  not cover the topic — and "the docs are silent" is what tempts a training-data fallback.
* **Per-dial resolution (item 8).** INV-138 treated "the current setting" as one thing to determine
  or not. Model and effort are separate dials in different epistemic states: the model is knowable,
  the effort is not. Read all-or-nothing, the fallback would compare a determinable Opus 5.5 against
  the previous stage's Sonnet 5.5, find it unchanged, and suppress the switch offer entirely.
* **Write batching (item 9).** Step 10a persisted per answer where Bootcamp preparation holds and
  writes once (INV-058) — two or three diffs to one file inside one step.

Item 4 is asserted only weakly on purpose: a test that pins prose *order* precisely would break on
any rewording. Its assertion checks the reassurance precedes the question, nothing finer.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"

ONBOARDING = SKILLS / "bootcamp-onboarding" / "onboarding-flow.md"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
PREPARATION = SKILLS / "bootcamp-preparation" / "SKILL.md"
CONCEPTS = SKILLS / "module-00-entity-resolution-concepts" / "concepts.md"
MODULE_00 = SKILLS / "module-00-entity-resolution-concepts" / "SKILL.md"
MODULE_01 = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"

FIRST_ASK = "Do you have any questions about entity resolution before we continue?"
FOLLOW_UP = "Do you have any other questions about entity resolution before we continue?"


def read(path):
    return path.read_text(encoding="utf-8")


def flat(path):
    text = re.sub(r"(?m)^\s*>\s?", "", read(path))
    return re.sub(r"\s+", " ", text)


class ThePrefaceCanAnswerHowLongThisTakes(unittest.TestCase):
    """Item 1: the most likely question at the preface's only gate."""

    def test_the_overview_states_the_shape_of_the_answer(self):
        text = flat(ONBOARDING)
        for expected in ("module-sized", "its own time estimate", "Core or Customized"):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_the_overview_says_progress_survives_a_stop(self):
        self.assertRegex(
            flat(ONBOARDING),
            r"(?i)do not have to finish in one sitting|progress is saved",
            "the genuinely useful part of a duration answer is that it can be resumed "
            "(INV-059/INV-094)",
        )

    def test_step_4_forbids_inventing_a_total(self):
        text = flat(ONBOARDING)
        self.assertRegex(
            text,
            r"(?i)NEVER invent a total|Do not offer a figure",
            "Step 4 must forbid a fabricated total explicitly — INV-096's rule is per-module and "
            "module-start-only, so nothing else covers the preface",
        )
        self.assertIn("INV-096", text)

    def test_no_concrete_total_leaked_into_the_guidance(self):
        """A worked example like "4-6 hours" would become the number guides quote."""
        prose = flat(ONBOARDING)
        for offender in re.finditer(r"\b\d+\s*(?:-|to|–)\s*\d+\s*hours?\b", prose, re.I):
            window = prose[max(0, offender.start() - 160): offender.end() + 60]
            self.assertRegex(
                window,
                r"(?i)(do not|never|not with|forbid)",
                f"onboarding-flow.md contains an hours figure that is not marked forbidden — a "
                f"guide will quote it as the answer:\n...{window}...",
            )


class ModuleZeroHasAPinnedFollowUpVariant(unittest.TestCase):
    """Item 3: satisfy the re-present without repeating the first-ask verbatim."""

    def test_concepts_pins_both_wordings(self):
        text = flat(CONCEPTS)
        self.assertIn(FIRST_ASK, text, "the first-ask wording must be unchanged (INV-056)")
        self.assertIn(FOLLOW_UP, text, "a pinned follow-up variant must exist")

    def test_the_follow_up_is_required_after_an_answer(self):
        self.assertRegex(
            flat(CONCEPTS),
            r"(?i)Use the follow-up wording every time after the first answer",
            "without this the re-present still defaults to the first-ask string",
        )

    def test_the_skill_names_the_follow_up_not_the_first_ask_for_the_represent(self):
        text = flat(MODULE_00)
        self.assertRegex(
            text,
            r"(?i)pinned\s+\*\*follow-up variant\*\*|follow-up variant",
            "module-00/SKILL.md's re-present instruction must name the follow-up variant",
        )
        self.assertRegex(
            text,
            r"(?i)never by repeating the first-ask",
            "the instruction must rule out repeating the first-ask wording",
        )

    def test_the_gate_still_does_not_reissue_the_invitation(self):
        """The spec requires concepts.md's bounding of the loop to be preserved."""
        self.assertRegex(
            flat(CONCEPTS),
            r"(?i)do not re-issue this same \"?any questions\??\"? invitation",
            "the readiness gate must still not re-issue the invitation",
        )


class TheKnowledgeCheckOffersABenefitNotAnAssessment(unittest.TestCase):
    """INV-112 guarantees this question to every Bootcamper, so its framing is universal.

    The offer used to read "Would you like to test your knowledge of entity resolution with a
    short quiz?" — an offer to be assessed, put to someone who has just met the material and
    has no evidence they absorbed it. A Bootcamper reported that "quiz", "test" and
    "evaluation" make people recoil. The module's own prose two paragraphs above already says
    the exercise "reinforces the concepts and drives curiosity"; that was the pitch, and the
    Bootcamper never saw it.

    Reworded 2026-08-11 (`reframe-the-quiz-as-a-knowledge-check`, maintainer-chosen wording).
    The mechanism is untouched — count, difficulty, sourcing and the wrong-answer handling
    pinned by `TheKnowledgeCheckDefinesWrongAnswersAndAnswerShape` all still hold. Per
    INV-181 this pins the **requirement** (a benefit frame, unambiguous, no "or") alongside
    the current string, so a future rewording fails on the string it must update rather than
    on a rule it did not know about.
    """

    OFFER = "Would you like a few quick questions to help the concepts stick?"

    def test_the_offer_is_pinned_verbatim_in_concepts(self):
        """INV-056: exactly one authoritative place, not left to the model to improvise."""
        self.assertIn(f"👉 **{self.OFFER}**", CONCEPTS.read_text(encoding="utf-8"))

    def test_the_offer_names_the_gain_rather_than_the_measurement(self):
        self.assertRegex(self.OFFER, r"(?i)help the concepts stick")
        for assessment_word in ("quiz", "test your", "evaluat", "exam", "score", "grade"):
            with self.subTest(word=assessment_word):
                self.assertNotIn(assessment_word, self.OFFER.lower())

    def test_the_offer_is_a_single_unambiguous_yes_no(self):
        """INV-008, and INV-009/INV-051 on the absence of an "or"-joined choice."""
        self.assertTrue(self.OFFER.startswith("Would you like"))
        self.assertEqual(1, self.OFFER.count("?"))
        self.assertNotRegex(self.OFFER, r"\bor\b")

    def test_the_module_no_longer_frames_the_exercise_as_a_test(self):
        """Heading and prose, not just the pinned line — the frame is the whole section."""
        text = CONCEPTS.read_text(encoding="utf-8")
        self.assertIn("## Optional knowledge check (offer before the readiness gate)", text)
        uses = [
            line for line in text.splitlines()
            if "quiz" in line.lower() and "The words" not in line
        ]
        self.assertEqual(
            [], uses,
            "the only surviving mention may be the rule naming the words to avoid",
        )

    def test_the_reason_is_recorded_where_the_wording_lives(self):
        """Otherwise the next editor restores "quiz" as a harmless simplification."""
        text = flat(CONCEPTS)
        self.assertRegex(text, r"(?i)Offer the benefit, never the assessment")
        self.assertRegex(text, r"(?i)make\s+people recoil")

    def test_it_is_not_softened_into_ambiguity_or_made_conditional(self):
        text = flat(CONCEPTS)
        self.assertRegex(text, r"(?i)Do not soften it further into\s+ambiguity")
        self.assertRegex(text, r"(?i)INV-112 pins one sentence for every run")

    def test_the_progress_keys_are_deliberately_unchanged(self):
        """Internal state, not Bootcamper-facing text: renaming them was out of scope."""
        skill = MODULE_00.read_text(encoding="utf-8")
        self.assertIn("`quiz_offered`", skill)
        self.assertIn("`quiz_taken`", skill)


class TheChangeabilityNotePrecedesItsQuestion(unittest.TestCase):
    """Item 4: asserted coarsely on purpose — see the module docstring."""

    def test_the_reassurance_comes_before_the_verbosity_question(self):
        text = read(PREPARATION)
        step3 = text[text.index("## 3. Level of detail"): text.index("## 3a.")]
        reassure = step3.lower().index("change it any time")
        question = step3.index("👉 **How much detail")
        self.assertLess(
            reassure,
            question,
            "the can-change-it-any-time reassurance still follows the question, where it cannot "
            "inform the choice and cannot legally follow the 👉 either (INV-251)",
        )

    def test_it_says_why_the_order_matters(self):
        self.assertRegex(
            flat(PREPARATION),
            r"(?i)cannot inform the choice",
            "state the reason, or a later edit will move it back",
        )


class TheKnowledgeCheckDefinesWrongAnswersAndAnswerShape(unittest.TestCase):
    """Items 5 and 6."""

    def setUp(self):
        self.text = flat(CONCEPTS)

    def test_it_requires_numbered_multiple_choice_items(self):
        self.assertRegex(
            self.text,
            r"(?i)Ask every item as a numbered multiple-choice question",
            "the answer shape was undefined, leaving open-ended items permitted by silence",
        )
        self.assertRegex(self.text, r"INV-051")

    def test_it_rules_out_open_ended_items(self):
        self.assertRegex(
            self.text,
            r"(?i)Do \*\*not\*\* pose open-ended items|do not pose open-ended items",
            "an open-ended item fits neither INV-051's numbered shape nor INV-008",
        )

    def test_it_names_the_answer_as_incorrect_without_false_praise(self):
        self.assertRegex(
            self.text,
            r"(?i)Name it as incorrect",
            "nothing said what to do when an answer is wrong",
        )
        self.assertRegex(
            self.text,
            r"(?i)Never \"?good thinking!?\"? over a wrong answer|never let the correction be so soft",
            "false praise over a wrong answer is the failure mode a learning module can least "
            "afford",
        )

    def test_it_requires_re_teaching_not_just_the_right_letter(self):
        self.assertRegex(
            self.text,
            r"(?i)re-teach the concept",
            "giving only the correct option teaches nothing",
        )

    def test_it_says_whether_to_move_on_or_re_ask(self):
        self.assertRegex(
            self.text,
            r"(?i)do not re-ask the same one",
            "undefined: whether a miss re-asks or moves on",
        )

    def test_it_says_a_miss_does_not_change_difficulty(self):
        self.assertRegex(
            self.text,
            r"(?i)a miss is not a reason to get easier",
            "undefined: whether a miss should change the difficulty of what follows",
        )

    def test_the_reteaching_stays_mcp_sourced(self):
        self.assertRegex(self.text, r"(?i)never patch a wrong answer from training data")


class MissedQueriesAreDistinguishedFromThinDocumentation(unittest.TestCase):
    """Item 7: a query that misses looks exactly like a topic the docs do not cover."""

    def setUp(self):
        self.text = flat(CONCEPTS)

    def test_it_says_to_prefer_the_suggested_queries(self):
        self.assertRegex(self.text, r"(?i)Prefer these queries")

    def test_it_requires_a_requery_before_concluding_the_docs_are_silent(self):
        self.assertRegex(
            self.text,
            r"(?i)RE-QUERY with the documentation's own phrasing before concluding",
            "without this, an empty result reads as a documentation gap and invites a "
            "training-data fallback (INV-080)",
        )

    def test_it_explains_that_bm25_phrasing_decides_the_result(self):
        self.assertRegex(self.text, r"(?i)BM25")

    def test_it_names_the_failure_shape(self):
        self.assertRegex(
            self.text,
            r"(?i)looks exactly like\s+\*?\*?documentation that does not cover",
            "the hazard is the failure's shape, not the extra call",
        )


class Inv138ResolvesTheFallbackPerDial(unittest.TestCase):
    """Item 8: model and effort sit in different epistemic states at the same moment."""

    def setUp(self):
        self.text = flat(GROUND_RULES)

    def test_it_says_per_dial_explicitly(self):
        self.assertRegex(
            self.text,
            r"(?i)Resolve \"?cannot be determined\"? PER DIAL, not for the setting as a whole",
            "read all-or-nothing, the fallback suppresses a switch offer for a Bootcamper "
            "demonstrably on a different model",
        )

    def test_the_fallback_is_scoped_to_the_undeterminable_dial(self):
        self.assertRegex(
            self.text,
            r"(?i)Only for a dial whose current value cannot be determined",
            "the fallback must apply per dial, not to the whole setting",
        )

    def test_it_names_the_failure_the_clause_prevents(self):
        self.assertRegex(
            self.text,
            r"(?i)Applying the previous-stage row to a dial that \*?was\*? determinable",
            "state the concrete failure, or the clause reads as pedantry and gets simplified away",
        )

    def test_it_keeps_the_separate_dials_principle_visible(self):
        self.assertIn("INV-137", self.text)


class Step10aBatchesItsPreferenceWrites(unittest.TestCase):
    """Item 9: the decision was to batch, matching INV-058's reasoning."""

    def setUp(self):
        self.text = flat(MODULE_01)

    def test_it_requires_one_write_at_the_checkpoint(self):
        self.assertRegex(
            self.text,
            r"(?i)Hold every answer and write `?config/bootcamp_preferences\.yaml`? ONCE",
            "Step 10a wrote per answer, which is one diff per gate inside a single step",
        )

    def test_it_cites_the_reasoning_it_inherits(self):
        self.assertIn("INV-058", self.text)
        self.assertRegex(
            self.text,
            r"(?i)scope gap rather than a violation",
            "INV-058 names Bootcamp preparation specifically; say why the reasoning transfers",
        )

    def test_the_integration_answer_is_held_not_written(self):
        self.assertRegex(
            self.text,
            r"(?i)\*\*hold\*\* the named systems",
            "the first answer must be held, not persisted immediately",
        )
        self.assertRegex(self.text, r"(?i)Either way, do not write yet")

    def test_both_answers_are_written_together(self):
        self.assertRegex(
            self.text,
            r"(?i)Now write both answers together",
            "the single write must be explicit at the end of the step",
        )


if __name__ == "__main__":
    unittest.main()
