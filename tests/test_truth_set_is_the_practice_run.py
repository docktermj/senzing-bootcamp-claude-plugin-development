"""The Truth Set is the practice run; the "wow moment" is the Bootcamper's own data.

The two-act analysis (#465, senzing-bootcamp-design#8) found the Act 1 curtain staged as the peak:
nine sites called the Truth Set app the bootcamp's "wow moment", and its close never said it was
practice. #486 changes three things, pinned here:

1. **The curtain line.** The Truth Set close says, as a statement immediately before the
   transition 👉 and never as a second question, that it was practice data built to contain
   matches, and points to the Bootcamper's own problem, named in one clause from
   `docs/business_problem.md` ("your own data" when that file is missing).
2. **"Wow moment" moves.** None of the nine sites carries the phrase; Module 7's skill files do,
   for its results app.
3. **The rendering contract's reason changes, not its requirements.** It covers both apps and
   names Module 7's results app as the moment the bootcamp builds to; every requirement sentence
   it carried still stands.

The curtain and 👉 checks are pure functions over the step's text, so each also runs on a mutated
copy as its negative control.

⚠️ **The 👉 counts read single lines on purpose (INV-346).** A 👉 question is its own line by
construction; counting lines that *start* with `👉 **` keeps prose mentioning the marker from
counting. Phrase checks collapse whitespace, so they match across a wrap.

⛔ **What this cannot establish:** that a live guide says the curtain line, or quotes the right
clause. That is a property of a run, observed by `dry-run` phase 3. This pins that the skill files
STATE it.

Stdlib only; shipped files read as text (INV-108).

Source issue: #486.

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
TRUTHSET = SKILLS / "module-03b-truthset-visualization"
CLOSE = TRUTHSET / "phase2-close.md"
CONTRACT = TRUTHSET / "visualization-api-reference.md"
MODULE_7 = SKILLS / "module-07-query-visualize-discover"

#: The nine sites #486 names, by file. Each file is checked whole: a phrase moved a few lines
#: within the same file would otherwise pass.
WOW_SITES = (
    TRUTHSET / "SKILL.md",                       # :3 description, :92 approval rationale
    TRUTHSET / "phase1-visualization.md",        # :7 purpose, :51 Before/After (INV-030)
    CONTRACT,                                    # :871 contract intro, :953 modal chrome
    SKILLS / "module-03-system-verification" / "phase1-verification.md",  # :43
    PLUGIN / "scripts" / "senzing_viz_server.py",  # :7 docstring, :1109 CSS comment
)

TRANSITION_QUESTION = "👉 **Are you ready to move on to the next module: {next module name}?**"
CURTAIN = "That was practice data, built to contain matches."


def flat(text):
    return " ".join(text.split())


def section(text, start, end_markers):
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i:]
    cut = [rest.find(m, len(start)) for m in end_markers]
    cut = [c for c in cut if c > 0]
    return rest[:min(cut)] if cut else rest


def questions(text):
    return [line.strip() for line in text.splitlines() if line.strip().startswith("👉 **")]


def module_close(text):
    return section(text, "## Step 5: Module Close", ("\n## ",))


def curtain_problems(text):
    step = module_close(text)
    if not step:
        return ["Step 5: Module Close is missing"]
    problems = []
    if questions(step) != [TRANSITION_QUESTION]:
        problems.append("Step 5's 👉 questions are %r, not the one transition question"
                        % questions(step))
    item_4 = section(step, "4. **Transition to the next module.**", (TRANSITION_QUESTION,))
    if not item_4:
        return problems + ["item 4 does not lead to the transition 👉"]
    f = flat(item_4)
    for what, phrase in {
        "the name": "curtain line",
        "a statement": "a statement immediately before the transition 👉",
        "no second question": "never a second question",
        "the practice framing": CURTAIN,
        "the problem's source": "`docs/business_problem.md`",
        "one clause": "one clause",
        "the problem's section": '"Problem Description"',
        "the missing-file fallback": "When `docs/business_problem.md` is missing, it says \"your own data\"",
        "the INV-251 citation": "one 👉 ends the turn, INV-251",
    }.items():
        if phrase not in f:
            problems.append("item 4 lacks %s (%r)" % (what, phrase))
    if item_4.count(CURTAIN) != 2:
        problems.append("item 4 should carry the curtain line in both forms (with and without "
                        "the problem); found %d" % item_4.count(CURTAIN))
    curtain_at = step.find(CURTAIN)
    question_at = step.find(TRANSITION_QUESTION)
    ask_at = step.find("Then ask the single transition question")
    if not (0 <= curtain_at < ask_at < question_at):
        problems.append("the curtain line does not come immediately before the transition 👉")
    return problems


class TheCurtainLine(unittest.TestCase):
    TEXT = CLOSE.read_text(encoding="utf-8")

    def test_the_close_says_it_was_practice(self):
        self.assertEqual([], curtain_problems(self.TEXT))

    def test_control_a_second_question_is_reported(self):
        mutated = self.TEXT.replace(
            "   Then ask the single transition question",
            "   👉 **Ready for your own data?**\n\n   Then ask the single transition question")
        self.assertTrue(any("👉" in p for p in curtain_problems(mutated)))

    def test_control_a_missing_fallback_is_reported(self):
        mutated = self.TEXT.replace("it says \"your own data\"", "it says nothing")
        self.assertTrue(curtain_problems(mutated))

    def test_control_the_curtain_after_the_question_is_reported(self):
        step = module_close(self.TEXT)
        item_4 = section(step, "4. **Transition to the next module.**",
                         ("   Then ask the single transition question",))
        moved = self.TEXT.replace(item_4, "4. **Transition to the next module.** ")
        moved = moved.replace("*(Internal: end the turn on this question and wait.)*",
                              item_4 + "\n*(Internal: end the turn on this question and wait.)*", 1)
        self.assertTrue(curtain_problems(moved))


class TheWowMomentMoves(unittest.TestCase):

    def test_none_of_the_nine_sites_carries_it(self):
        for path in WOW_SITES:
            with self.subTest(path=path.name):
                self.assertNotIn("wow moment", path.read_text(encoding="utf-8").lower())

    def test_module_7_carries_it_for_the_results_app(self):
        skill = flat((MODULE_7 / "SKILL.md").read_text(encoding="utf-8"))
        phase1 = flat((MODULE_7 / "phase1-query-visualize.md").read_text(encoding="utf-8"))
        self.assertIn('This module carries the bootcamp\'s "wow moment"', skill)
        step_3c = section(phase1, "### 3c. Visualization offer", ("Pin the offer verbatim",))
        self.assertIn('This app is the bootcamp\'s "wow moment":', step_3c)
        self.assertIn("The Truth Set app was the practice run", step_3c)


class TheRenderingContractKeepsItsRequirements(unittest.TestCase):
    TEXT = flat(CONTRACT.read_text(encoding="utf-8"))

    def test_the_stated_reason_covers_both_apps(self):
        intro = section(self.TEXT, "## Rendering contract", ("### Escaping",))
        self.assertIn("They cover both apps built from this contract", intro)
        self.assertIn("Module 7's results app", intro)
        self.assertIn("../module-07-query-visualize-discover/SKILL.md", intro)

    def test_every_requirement_sentence_still_stands(self):
        """The requirements, not their reason: these are the sentences #486 must not move."""
        for sentence in (
            "These are requirements, not suggestions.",
            "the quality bar below is the **default every implementation ships**, not something "
            "a bootcamper has to ask for one improvement at a time.",
            "get the same visual care as the headline tabs: a real header bar (title plus a close "
            "control) visually separated from the body, deliberate spacing and typographic "
            "hierarchy, and a subtle entrance transition.",
            "the brand tokens apply *inside* the modal, not only to the app shell.",
            "A functionally-correct but visually plain dialog undersells the moment.",
        ):
            with self.subTest(sentence=sentence[:40]):
                self.assertIn(sentence, self.TEXT)

    def test_modal_chrome_names_both_apps(self):
        modal = section(self.TEXT, "### Modal chrome", ("### ",))
        self.assertIn("are a primary surface in both apps", modal)


if __name__ == "__main__":
    unittest.main()
