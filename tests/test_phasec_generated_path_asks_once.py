"""On the generated path, Phase C steps 13–15 pose one question, not two.

A Bootcamper on a bootcamp-generated scenario was asked two consecutive yes/no questions,
each of which stated its own answer before asking:

    👉 The generated sources have no load-order dependencies — shall I proceed with none?
    👉 I recommend the Sequential loading strategy for this generated dataset — shall I use it?

They interrupted at the second to say it *"slows the flow with pointless confirmations"*.
Both facts followed from the same provenance check, established before either was asked,
and nothing between them could have changed either answer — so as two gates they are
consecutive rubber stamps.

⛔ **Neither question could simply be deleted, and the spec says so explicitly.** INV-007 —
*the plugin cannot answer questions nor assume answers* — is why a confirm exists at all on
this path, so "just proceed without asking" was **not** available and was not adopted.
Merging the two into one satisfies both invariants at once: INV-012 loses the redundant
turn, INV-007 keeps the decision with the Bootcamper.

⚠️ **Step 14 asks nothing**, so 13 and 15 are adjacent in the Bootcamper's experience while
being two steps apart in the file. That is why the guard counts across the whole step range
rather than per step: each gate was individually compliant with a per-step budget of one
question, and the pair is what was actually experienced.

Source spec: `specs/phasec-fires-two-self-answered-confirmations-back-to-back.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE_C = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
           "module-06-data-processing" / "phaseC-multi-source.md")

MERGED = ("👉 **The generated sources have no load-order dependencies, and I recommend "
          "the Sequential loading strategy for this dataset — shall I proceed on both?** "
          "(respond yes or no)")

#: The line that opens each step's bootcamper-supplied branch. Everything before it in a
#: step belongs to the generated path.
SUPPLIED_MARKER = r"^\*\*Only when some source being loaded is bootcamper-supplied\*\*"

#: The generated path is selected by these markers; the supplied path by `provenance: own`.
GENERATED_MARKERS = ("provenance: cord", "synthesized",
                     "> 🤖 Bootcamp-generated business case")


def text():
    return PHASE_C.read_text(encoding="utf-8")


def step_range(start_heading, end_heading):
    """The lines of the file between two ``## `` headings.

    Line-scoped by design (#424): a heading is one line, and the questions in the range are
    counted by the 👉 that opens each one, which opens on one line however it wraps.
    """
    lines = text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(start_heading))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith(end_heading))
    return lines[start:end]


class TheGeneratedPathPosesOneQuestionAcrossStepsThirteenToFifteen(unittest.TestCase):

    def test_the_merged_question_is_pinned_verbatim(self):
        """INV-056/INV-005 — pinned, and 👉-prefixed."""
        self.assertIn(MERGED, text(),
                      "the merged question's wording changed; it is pinned verbatim")

    def test_it_covers_both_decisions(self):
        self.assertIn("load-order dependencies", MERGED)
        self.assertIn("Sequential loading strategy", MERGED)

    def test_it_is_answerable_yes_or_no(self):
        """INV-008 — unambiguous with respect to yes/no."""
        self.assertTrue(MERGED.rstrip().endswith("(respond yes or no)"))

    def test_it_is_not_complex(self):
        """INV-009 — the use of "or" to join alternatives is discouraged.

        The trailing "(respond yes or no)" names the two replies rather than joining two
        choices, which is the form every other pinned yes/no question in the plugin uses.
        """
        body = MERGED.replace("(respond yes or no)", "")
        self.assertNotIn(" or ", body,
                         "the merged question joins alternatives with 'or' (INV-009)")

    def test_step_fifteen_does_not_re_ask_on_the_generated_path(self):
        block = step_range("## 15. Select loading strategy", "## 16.")
        joined = "\n".join(block)
        head = joined.split("**Only when some source being loaded is bootcamper-supplied**")[0]
        posed = [l for l in head.splitlines() if l.lstrip().startswith("👉")]
        self.assertEqual(
            [], posed,
            "step 15's generated branch poses a question again; the strategy was decided "
            "at step 13 and re-confirming it is the second of the two rubber stamps")
        self.assertIn("already decided at step 13", joined)

    def test_exactly_one_pinned_question_on_the_generated_path(self):
        """The property the Bootcamper actually experiences, counted across the range.

        Both branches' questions live in the same file, so this counts only the ones a
        generated-path run reaches: the merged confirm, plus nothing from step 15's
        generated branch. The supplied-path questions are excluded by their own headings.
        """
        questions = []
        for start, end in (("## 13. Analyze dependencies", "## 14."),
                           ("## 14. Determine load order", "## 15."),
                           ("## 15. Select loading strategy", "## 16.")):
            # Within each step, the generated branch is everything BEFORE the
            # supplied-path marker — which runs to that step's own end, so the two
            # branches must be separated per step rather than across the whole range.
            joined = "\n".join(step_range(start, end))
            generated = re.split(SUPPLIED_MARKER, joined, maxsplit=1, flags=re.M)[0]
            questions += [l for l in generated.splitlines()
                          if l.lstrip().startswith("👉")]
        self.assertEqual(
            1, len(questions),
            "the generated path poses %d pinned questions across steps 13–15; it must "
            "pose exactly one:\n  %s" % (len(questions), "\n  ".join(questions)))

    def test_a_no_still_reaches_both_overrides(self):
        """INV-007/INV-051 — merging the confirms must not merge away the overrides."""
        block = "\n".join(step_range("## 13. Analyze dependencies", "## 14."))
        flat = " ".join(block.split())
        self.assertIn("describe the dependencies they see and capture the dependency map",
                      flat, "the dependency-map override was lost in the merge")
        self.assertIn("numbered strategy menu", flat,
                      "the strategy-menu override was lost in the merge")
        self.assertIn("Neither override is skipped", flat)

    def test_the_decision_is_still_the_bootcampers(self):
        """⛔ INV-007 — 'proceed without asking' was not adopted, and says so."""
        flat = " ".join(text().split())
        self.assertIn("INV-007", flat)
        self.assertIn("Proceeding without asking at all is NOT the alternative", flat)


class TheSuppliedPathIsUntouched(unittest.TestCase):
    """⛔ These ask genuinely open questions of the only person who knows the answers."""

    def test_step_thirteen_still_asks_the_open_dependency_question(self):
        self.assertIn("👉 **Are there load-order dependencies between your data sources?**",
                      text())

    def test_step_fifteen_still_offers_the_full_numbered_menu(self):
        body = text()
        self.assertIn("👉 **Which loading strategy would you like? Reply with a number:**",
                      body)
        for option in ("**Sequential**", "**Parallel**", "**Hybrid**"):
            with self.subTest(option=option):
                self.assertIn(option, body)


class TheCrossStepShapeIsRecorded(unittest.TestCase):
    """A path can accumulate rubber stamps one defensible step at a time."""

    def test_the_step_warns_against_regrowing_the_pair(self):
        flat = " ".join(text().split())
        self.assertIn("must not be split back into two", flat)

    def test_it_says_to_weigh_a_new_confirm_against_the_ones_already_there(self):
        flat = " ".join(text().split())
        self.assertIn("nothing counted questions **across** steps", flat)
        self.assertIn("not only against itself", flat)


if __name__ == "__main__":
    unittest.main()
