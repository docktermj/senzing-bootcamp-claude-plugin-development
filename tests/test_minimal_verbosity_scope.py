"""`minimal` verbosity is defined against structured output, not only against prose.

The preset system defines `minimal` as a filter over content KINDS -- five categories at 0,
"reduces only explanatory output and NEVER suppresses required output". That is enough for prose
and silent where output has a prescribed SHAPE, and two sites in the plugin have one:

1. **The onboarding overview** (`onboarding-flow.md` step 3) is ten bullets, of which exactly two
   carried a verbosity treatment -- the version line and the feedback-trigger bullet. The other
   eight had none, and they are not uniform: the module list is orientation a bootcamper needs to
   navigate, the guided-discovery framing is encouragement. Under `minimal` one guide prints all
   eight (they are not marked for suppression), another cuts to a sentence. Both are defensible
   readings of the same file.
2. **The setup recap** (`bootcamp-preparation/SKILL.md` step 7) is a six-line template with a
   one-line budget under `minimal` AND a ⛔ requiring every honored value stated with a marker
   defined **per line**. Those collide precisely in the case the marker exists for: a returning
   bootcamper who pre-seeded `path`, `verbosity` and `programming_language` needs three markers and
   has one line. Reached in the dry-run seeded walk, and resolvable only by collapsing -- which
   nothing instructed.

Neither breaks a path, and no bootcamper-facing output was wrong. The defect is divergence, landing
on the setup recap whose stated purpose (INV-099/INV-133) is to let a returning bootcamper see what
is in force and correct it.

The fix extends the existing per-preset convention to cover FORM rather than adding a mechanism:
required elements merge onto the permitted lines and are never dropped, and per-line annotations
attach inline to the value they qualify.

Enforces **INV-214**.

Run:  python3 -m unittest discover -s tests
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
ONBOARDING = SKILLS / "bootcamp-onboarding" / "onboarding-flow.md"
PREP = SKILLS / "bootcamp-preparation" / "SKILL.md"

PRESETS = ("minimal", "concise", "standard", "detailed")


def section(text, start_marker, end_marker="\n## "):
    start = text.index(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    return text[start:end if end != -1 else len(text)]


class TheCollapseRuleIsStatedOnce(unittest.TestCase):
    def setUp(self):
        self.verbosity = section(GROUND_RULES.read_text(encoding="utf-8"), "## Verbosity")

    def test_it_says_required_elements_merge_rather_than_drop(self):
        self.assertRegex(
            self.verbosity, r"(?i)MERGE onto the permitted lines",
            "the Verbosity section must say what happens when a prescribed shape meets a smaller "
            "line budget. Without it, 'keep it to a single line' against a six-line template is "
            "resolved by guesswork.",
        )
        self.assertRegex(
            self.verbosity, r"(?i)never dropped to fit|not dropped",
            "and must say the required elements are not dropped to fit — dropping is the reading "
            "that loses a bootcamper's provenance markers",
        )

    def test_it_says_per_line_annotations_attach_inline(self):
        self.assertRegex(
            self.verbosity, r"(?i)inline to the value",
            "a marker defined per LINE has nowhere to go when lines collapse; the rule must say "
            "it attaches to the value instead",
        )

    def test_it_addresses_the_form_versus_kind_gap_explicitly(self):
        self.assertRegex(
            self.verbosity, r"(?i)says nothing about\s*\n?\s*\*?form|about \*form\*",
            "the rule must name why it exists: the explanatory/required split decides WHAT "
            "survives and is silent on FORM",
        )

    def test_it_points_at_a_worked_example(self):
        self.assertIn(
            "bootcamp-preparation", self.verbosity,
            "the rule must point at the worked example (Step 7's collapse), so a reader does not "
            "have to invent the shape",
        )


class TheOverviewHasNoUngovernedBullet(unittest.TestCase):
    def setUp(self):
        self.text = ONBOARDING.read_text(encoding="utf-8")

    def test_step_3_gives_every_bullet_a_treatment(self):
        self.assertRegex(
            self.text, r"(?i)Every bullet below has a verbosity treatment",
            "step 3 must state that no overview bullet is unconditional. Two of ten carried a "
            "treatment and eight had none, which is the divergence this fixes.",
        )

    def test_it_gives_a_per_preset_rule_for_the_group(self):
        for preset in PRESETS:
            with self.subTest(preset=preset):
                self.assertIn(
                    preset, self.text,
                    f"the group rule must say what {preset} does to the overview",
                )

    def test_minimal_keeps_orientation_and_drops_encouragement(self):
        self.assertRegex(
            self.text, r"(?i)orientation only|orientation versus encouragement",
            "the rule must name the principle it splits on, or the next editor will re-guess it",
        )
        self.assertRegex(
            self.text, r"(?i)module.{0,10}list.{0,80}how.long",
            "under minimal the module list and the how-long-it-takes bullet are what survive",
        )

    def test_it_keeps_the_fresh_bootcamp_caveat(self):
        """The reduced forms are unreachable on a fresh run; saying so prevents a false bug.

        ⚠️ **This assertion used to accept `all ten` as an alternative, and that made it a guard
        that punished its own repair.** The overview's bullet count went stale — the row said
        "all ten" over a list of eleven — and removing the literal per
        `specs/overview-bullet-count-is-stale-after-the-note-bullet.md` failed this test, because
        the surviving alternative, `correct rather than an oversight`, straddles a line break and
        `.{0,120}` does not cross newlines without `re.S`. So the only branch that could match was
        the stale count itself.

        Fixed both halves: the count is no longer an accepted spelling (blessing it here would
        let it back in past `tests/test_overview_bullets_are_not_counted.py`), and the match runs
        on whitespace-flattened text so the caveat's wrapping is not load-bearing. What is
        asserted is the caveat's *content* — a fresh run has no preset, so the unreduced overview
        is correct — which is what the test was always for.
        """
        flat = re.sub(r"\s+", " ", self.text)
        self.assertRegex(
            flat, r"(?i)\*\*fresh\*\* bootcamp no preset exists yet,.{0,120}"
                  r"correct rather than an oversight",
            "step 3 must keep the caveat that a fresh bootcamp has no preset, so the full "
            "overview is correct — otherwise the next audit reads it as a bug",
        )

    def test_it_names_every_item_with_its_own_treatment(self):
        """The version line, the feedback-trigger bullet and the make-a-note bullet (#234).

        Each has its own verbosity paragraph, so the sentence that lists them must name all
        three. It named two after the note bullet arrived, which left the note bullet's own
        treatment reading as the group rule's. Negative-controlled by restoring "Two carry
        their own" with the note bullet unnamed.
        """
        flat = re.sub(r"\s+", " ", self.text)
        m = re.search(r"(?i)(\w+) carry their own \(([^)]*)\)", flat)
        self.assertIsNotNone(m, "step 3 no longer says which items carry their own treatment")
        self.assertEqual("three", m.group(1).lower(),
                         "three items carry their own verbosity treatment, not "
                         f"{m.group(1)!r}")
        named = m.group(2)
        for item in ("version line", "feedback-trigger", "make-a-note"):
            with self.subTest(item=item):
                self.assertIn(item, named,
                              f"the own-treatment sentence does not name the {item}")
        self.assertRegex(flat, r"\*\*The note bullet is verbosity-aware",
                         "the make-a-note bullet's own treatment paragraph is gone, so naming "
                         "it here would point at nothing")


class TheSetupRecapCollapsesWithoutLosingMarkers(unittest.TestCase):
    def setUp(self):
        self.text = PREP.read_text(encoding="utf-8")

    def test_step_7_states_the_collapse_and_not_a_drop(self):
        self.assertRegex(
            self.text, r"(?i)COLLAPSE to one — they are not dropped|collapse to one",
            "Step 7 must say the six lines collapse under minimal rather than leaving 'a single "
            "line' to be reconciled with a six-line template",
        )

    def test_it_shows_the_collapsed_form_with_all_three_markers(self):
        """Show it, don't describe it: the shape is the thing that was being re-derived."""
        m = re.search(r"✅ Bootcamp preparation complete — Path:.*", self.text)
        self.assertIsNotNone(
            m, "Step 7 must show the collapsed one-line form explicitly under minimal",
        )
        line = m.group(0)
        self.assertEqual(
            3, line.count("from your saved preferences"),
            "the collapsed example must carry all three provenance markers inline — the seeded "
            f"case is exactly when three are needed and one line is allowed.\nGot: {line}",
        )
        self.assertIn("; ", line, "merged values are joined with '; '")
        self.assertIn("→ Next:", line, "the next-module pointer is required output")

    def test_it_says_the_module_list_compresses_to_a_count(self):
        self.assertRegex(
            self.text, r"(?i)compresses to a count",
            "Step 7 must say the module list becomes a count under minimal, since eleven names "
            "cannot share one line with three markers",
        )

    def test_it_records_that_a_count_is_not_a_module_number(self):
        self.assertRegex(
            self.text, r"(?i)count is not a module number",
            "compressing names to a count invites an INV-079 objection; the rule must pre-empt it "
            "rather than leaving the next reader to litigate it",
        )

    def test_the_semicolon_and_label_rules_survive(self):
        """The two pre-existing load-bearing details must not be lost to the new guidance."""
        self.assertRegex(self.text, r"(?i)separated by semicolons, not commas")
        self.assertRegex(self.text, r'(?i)"Programming language", never the bare "Language"')


if __name__ == "__main__":
    unittest.main()
