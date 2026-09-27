"""Three Module 7 instructions state what to do instead of leaving the guide to guess (#166).

Each was a judgment call on the 2026-09-25 phase-3 walk of Query, Visualize and Discover:

1. **Where the teardown question goes.** "👉 Ready for me to stop the visualization server?" sat
   inside step 3c, so it read as step 3c's closing question. The walk nearly ended 3c on it, which
   would have put two 👉 questions in one turn next to the Discover opt-in (INV-251). It now has one
   labeled step of its own, after the Query Completeness Gate and before module completion.
2. **"Relationship clusters" in step 4a.** The step asked for "K relationship clusters" but counted
   entities with one or more relationships, so the checkpoint's `relationships` figure (559 on the
   walk) was entities, not clusters. It also counted disclosed relationships only, while step 4d
   demonstrates discovered ones too, so data with only discovered links skipped step 4d.
3. **A 2-degree path with no method.** Step 4d asked for a `find_path` pair "2+ degrees apart if
   available" and gave no way to find one. On address-dense data almost every pair is directly
   linked; the walk tried seven pairs before finding one through a hub's neighbors.

⛔ The negative control for (1) is to put the teardown question back in step 3c: the test must fail.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
M7 = REPO / "plugins" / "senzing-bootcamp" / "skills" / "module-07-query-visualize-discover"
PHASE1 = M7 / "phase1-query-visualize.md"
PHASE2 = M7 / "phase2-discover.md"
PHASE2B = M7 / "phase2b-discover.md"

TEARDOWN_QUESTION = "> 👉 **Ready for me to stop the visualization server?**"
TEARDOWN_HEADING = "## Visualization server teardown"
GATE_HEADING = "## Query Completeness Gate"
STEP_3C_HEADING = "### 3c. Visualization offer"
COMPLETION_TEXT = re.compile(r"run the standard \*\*Module Completion\*\*\s+process")


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    """Whitespace-collapsed, so an assertion survives a re-wrap of the paragraph."""
    return re.sub(r"\s+", " ", text)


def section(text, heading, level="## "):
    """The text from ``heading`` to the next heading of the same or a higher level."""
    start = text.index(heading)
    stops = ["\n" + "#" * n + " " for n in range(1, level.count("#") + 1)]
    ends = [text.find(stop, start + len(heading)) for stop in stops]
    ends = [e for e in ends if e != -1]
    return text[start:min(ends)] if ends else text[start:]


class TheScanIsNotVacuous(unittest.TestCase):
    def test_every_file_and_anchor_exists(self):
        for path in (PHASE1, PHASE2, PHASE2B):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path.relative_to(REPO))
        text = read(PHASE1)
        for anchor in (GATE_HEADING, STEP_3C_HEADING, TEARDOWN_HEADING):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, text, "the anchor %r moved — retarget this test" % anchor)
        self.assertRegex(text, COMPLETION_TEXT, "the Module Completion text moved")


class TheTeardownQuestionHasOnePlace(unittest.TestCase):
    """(1) After the Completeness Gate, before module completion, and never in step 3c."""

    def setUp(self):
        self.text = read(PHASE1)

    def test_it_is_asked_exactly_once(self):
        self.assertEqual(
            1, self.text.count("stop the visualization server"),
            "the teardown question must appear exactly once in phase1-query-visualize.md; a "
            "second copy is a second place the guide may ask it")
        self.assertEqual(1, self.text.count(TEARDOWN_QUESTION))

    def test_it_sits_after_the_gate_and_before_module_completion(self):
        question = self.text.index(TEARDOWN_QUESTION)
        gate = self.text.index(GATE_HEADING)
        completion = COMPLETION_TEXT.search(self.text).start()
        self.assertLess(
            gate, question,
            "the teardown question must come after the Query Completeness Gate heading; asked "
            "earlier it collides with the Discover opt-in or the gate (INV-251)")
        self.assertLess(
            question, completion,
            "the teardown question must come before the Module Completion process, whose last "
            "act is the graduation offer")

    def test_it_lives_in_its_own_labeled_step(self):
        self.assertIn(
            TEARDOWN_QUESTION, section(self.text, TEARDOWN_HEADING),
            "the teardown question must sit under its own labeled step")

    def test_step_3c_no_longer_asks_it(self):
        step_3c = section(self.text, STEP_3C_HEADING, level="### ")
        self.assertNotIn(
            "stop the visualization server", step_3c,
            "step 3c must not ask the teardown question: it reads as step 3c's closing "
            "question and ends the turn next to the Discover opt-in")

    def test_step_3c_points_forward_to_the_new_step(self):
        step_3c = flat(section(self.text, STEP_3C_HEADING, level="### "))
        self.assertIn("with the server still running", step_3c,
                      "step 3c must keep the leave-it-running hand-off")
        self.assertIn(
            '"Visualization server teardown"', step_3c,
            "step 3c must point forward to the step that asks the question, so a reader of 3c "
            "knows the question exists and where it is")


class TheTeardownStepIsItsOwnTurn(unittest.TestCase):
    """(1) continued: the step's own rules, and what moved with the question."""

    def setUp(self):
        self.step = section(read(PHASE1), TEARDOWN_HEADING)
        self.flat = flat(self.step)

    def test_it_says_the_question_is_its_own_turn(self):
        self.assertRegex(self.flat, r"(?i)this question is its own turn")
        self.assertRegex(
            self.flat, r"(?i)do not combine it with the graduation offer or any other 👉 question",
            "the step must forbid combining the question with the graduation offer or any other "
            "👉 question")
        self.assertIn("INV-251", self.flat)

    def test_it_is_skipped_when_no_server_was_started(self):
        self.assertRegex(
            self.flat, r"(?i)skip this step silently if no server was started",
            "a Bootcamper who declined the visualization has no server to stop and must not be "
            "asked about one")

    def test_the_wording_is_pinned_verbatim(self):
        self.assertIn(TEARDOWN_QUESTION + "\n", self.step,
                      "the pinned wording (INV-056) must be unchanged and on a line of its own")
        self.assertIn("INV-056", self.flat)

    def test_the_no_purge_disclosure_moved_with_it_and_precedes_it(self):
        disclosure = self.step.find("nothing here is\npurged")
        if disclosure == -1:
            disclosure = self.step.find("nothing here is purged")
        self.assertNotEqual(-1, disclosure, "the no-purge disclosure must move with the question")
        question = self.step.find(TEARDOWN_QUESTION)
        self.assertNotEqual(-1, question, "the teardown question is missing from its step")
        self.assertLess(
            disclosure, question,
            "the disclosure informs the answer, so it must precede the question (INV-211)")
        self.assertRegex(self.flat, r"(?i)snapshot keeps every tab except the live")

    def test_the_not_yet_handling_moved_with_it(self):
        self.assertRegex(self.flat, r'(?i)no or not yet')
        self.assertRegex(self.flat, r"(?i)do not re-ask on a loop")
        self.assertRegex(self.flat, r"(?i)say plainly that it is still running and how to stop it")
        self.assertRegex(
            self.flat, r"(?i)no second teardown question is asked",
            "keeping exploring after the graduation offer must not produce a second teardown "
            "question (INV-006)")


class StepFourACountsEntitiesWithRelationships(unittest.TestCase):
    """(2) The wording, the count and the checkpoint all describe the same thing."""

    def test_relationship_clusters_is_gone_from_module_7(self):
        for path in sorted(M7.glob("*.md")):
            with self.subTest(file=path.name):
                self.assertNotRegex(
                    flat(read(path)), r"(?i)relationship clusters?",
                    "step 4a counts entities with relationships; calling them clusters makes "
                    "the checkpoint's figure mean something it does not count")

    def setUp(self):
        text = read(PHASE2)
        start = text.index("### Step 4a")
        self.step_4a = flat(text[start:text.index("### Step 4b", start)])

    def test_it_counts_disclosed_and_discovered_relationships(self):
        self.assertRegex(self.step_4a, r"(?i)entities with relationships")
        self.assertRegex(
            self.step_4a, r"(?i)disclosed or discovered",
            "step 4a must count both kinds: step 4d demonstrates both, and data with only "
            "discovered links would otherwise skip step 4d")
        self.assertIn("INV-115", self.step_4a,
                      "the relationship fields' shape must be read before counting")

    def test_the_checkpoint_keeps_its_key_and_says_it_counts_entities(self):
        self.assertIn('"relationships": K', self.step_4a,
                      "the `relationships` key must keep its name so older progress files match")
        self.assertRegex(
            self.step_4a, r"(?i)K is a count of \*\*entities\*\*, not of clusters",
            "the checkpoint text must say that `relationships` is a count of entities")


class StepFourDGivesAMethodForATwoDegreePath(unittest.TestCase):
    """(3) The hub method, bounded at three hubs, and the 1-degree fallback."""

    def setUp(self):
        text = read(PHASE2B)
        start = text.index("4. **find_path demonstration:**")
        self.item = flat(text[start:text.index("5. **Network structure explanation:**", start)])

    def test_it_names_the_hub_method(self):
        for pattern, why in (
            (r"(?i)entity with the most relationships from step 4a", "the hub is the most-related entity"),
            (r"(?i)two of its neighbors that are \*\*not related to each other\*\*",
             "the pair is two neighbors not related to each other"),
            (r"(?i)confirm with `find_path`", "find_path confirms the pair"),
            (r"(?i)stop after three hubs", "the search is bounded at three hubs"),
        ):
            with self.subTest(rule=why):
                self.assertRegex(self.item, pattern, "step 4d must say: %s" % why)

    def test_the_degree_limit_comes_from_the_reference(self):
        self.assertRegex(
            self.item, r"(?i)degree limit high enough to return a 2-degree path",
            "a degree limit of 1 cannot return the path the method looks for")
        self.assertIn("get_sdk_reference", self.item)

    def test_it_gives_the_one_degree_fallback_and_says_so_plainly(self):
        self.assertRegex(
            self.item, r"(?i)if no 2\+ degree pair is found after three hubs",
            "step 4d must say what to do when the method finds nothing")
        self.assertRegex(self.item, r"(?i)directly linked \(1-degree\) pair")
        self.assertRegex(
            self.item, r"(?i)say plainly that this data has no path of 2\+ degrees to show",
            "a 1-degree demonstration must not pass itself off as a multi-hop path")


if __name__ == "__main__":
    unittest.main()
