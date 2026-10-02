"""Two defects in the module-start model/effort nudge, both reached by following the rules.

**The answer hint named the wrong dial.** The switch question's stem is substitutable and the
rule says to name only the dial that differs — but the trailing hint hardcoded "reply no to
keep your current *model*" outside any bracket. An effort-only switch therefore asked about
effort and told the bootcamper what declining does to the model. INV-056 pins the wording, so
the guide could not fix it at runtime. It is the common case: a bootcamper who stays on Opus 5.5
through the conversational stages meets an effort-only step-up at SDK setup.
(`specs/effort-only-switch-question-says-keep-your-current-model.md`)

**An effort above the whole table asked forever.** `/effort` offers five levels; the table
recommends only `medium` or `high`. A bootcamper on `xhigh` or `max` sits above every remaining
row, so the step-down clause fired at every module — twelve questions proposing a change they
made deliberately, none of which they could stop except by downgrading. The premise that hid it
was a third clause claiming reasoning effort "cannot be read at all", when the plugin's own
switch flow asks the bootcamper to run `/effort`, whose result lands in the transcript.
(`specs/effort-above-every-recommendation-triggers-a-step-down-question-every-module.md`)

Both live in prose, so they are pinned as requirements on that prose — in **every** file that
carries the pinned question. That made graduation in scope alongside the ground rules until #293,
which replaced graduation's copy with a pointer: `ground-rules.md` is now the only pinning file,
and `test_model_switch_rule_is_stated_once.py` fails if another one appears. The scan below still
derives the set, so a copy pasted back is held to these checks too.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
MODEL_SELECTION = PLUGIN / "docs" / "model-selection.md"

#: A pinned switch question: the 👉 form the bootcamper is asked, not a recap transcript
#: entry (`- **Q:** Would you like to switch to …` under "Questions & Responses" in the
#: example recap) and not prose describing one.
PINNED_SWITCH = re.compile("\U0001F449" + r"\s*\*\*Would you like to switch to")

#: Known pinning files — a non-vacuity FLOOR, not the site set. The scan below decides what is
#: checked (INV-246); this only stops a broken pattern degrading the guard to silence. It named
#: graduation too until #293 made ground-rules the one copy.
KNOWN_PINNING_FILES = (GROUND_RULES,)


def pinning_files():
    """Every shipped file that pins a switch question — discovered, never listed.

    INV-246: the previous constant `(GROUND_RULES, GRADUATION)` encoded where the author
    noticed the pattern, under a comment claiming "**Every** file that pins a switch
    question". A third module gaining one would have left this guard green.
    """
    return tuple(p for p in sorted(PLUGIN.rglob("*.md"))
                 if PINNED_SWITCH.search(p.read_text(encoding="utf-8")))


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def switch_questions(text):
    """Every pinned 'Would you like to switch to …' line."""
    return [line.strip() for line in text.splitlines()
            if "Would you like to switch to" in line]


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_files_exist(self):
        for path in pinning_files() + (MODEL_SELECTION,):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path)

    def test_the_pinning_file_set_is_derived_and_not_vacuous(self):
        """INV-246: the site set is scanned, so a third pinning file is covered on sight."""
        found = pinning_files()
        for known in KNOWN_PINNING_FILES:
            with self.subTest(file=known.name):
                self.assertIn(
                    known, found,
                    "%s pins a switch question but the derivation no longer finds it — the "
                    "pinned-question form changed and this guard is inspecting a smaller set "
                    "than it believes" % known.name)

    def test_both_pinned_switch_questions_are_found_in_each_file(self):
        """A pass that found no questions would prove nothing about their hints."""
        for path in pinning_files():
            with self.subTest(file=path.name):
                self.assertGreaterEqual(
                    len(switch_questions(read(path))), 2,
                    "expected both the CLI and the interface-neutral form in %s" % path.name)


class TheAnswerHintNamesTheDialTheQuestionAsksAbout(unittest.TestCase):
    def test_no_pinned_question_hardcodes_the_model_in_its_hint(self):
        for path in pinning_files():
            for line in switch_questions(read(path)):
                with self.subTest(file=path.name, line=line[:60]):
                    self.assertNotIn(
                        "keep your current model", line,
                        "the hint names the model dial unconditionally, so an "
                        "effort-only switch tells the bootcamper what declining does "
                        "to a dial the question is not touching")

    def test_every_pinned_question_uses_the_substitutable_dial(self):
        for path in pinning_files():
            for line in switch_questions(read(path)):
                with self.subTest(file=path.name, line=line[:60]):
                    self.assertIn("keep your current {dial}", line,
                                  "the hint is not dial-aware")

    def test_the_dial_placeholder_is_defined_where_it_is_used(self):
        """A bracket nothing resolves is worse than a wrong literal: it ships as-is."""
        for path in pinning_files():
            flat = squash(read(path))
            with self.subTest(file=path.name):
                self.assertRegex(
                    flat,
                    r'\{dial\}`?[^.]{0,24}?resolves to "model", "effort", or '
                    r'"model and effort"',
                    "%s uses {dial} without saying what it resolves to" % path.name)

    def test_the_name_only_the_differing_dial_rule_covers_the_hint(self):
        flat = squash(read(GROUND_RULES))
        self.assertRegex(
            flat, r"(?i)that rule covers the whole sentence, including the answer hint",
            "the rule still reads as though it governed only the question stem")

    def test_the_confirmation_gate_is_left_alone(self):
        """It says 'your model and effort', which is accurate for either dial."""
        for path in pinning_files():
            with self.subTest(file=path.name):
                self.assertIn("👉 **Are you done modifying the model and effort?**",
                              read(path), "the confirmation gate's wording moved")


class AnEffortAboveTheWholeTableIsNotAMismatch(unittest.TestCase):
    def setUp(self):
        self.flat = squash(read(GROUND_RULES))

    def test_the_exemption_exists_and_names_the_levels(self):
        self.assertRegex(
            self.flat,
            r"(?i)an effort setting ABOVE everything\s*the table ever recommends",
            "nothing exempts an effort above the table from the comparison")
        for level in ("`xhigh`", "`max`"):
            with self.subTest(level=level):
                self.assertIn(level, self.flat,
                              "the levels above the table are not named, so a reader "
                              "cannot tell which settings the exemption covers")

    def test_it_asks_nothing(self):
        self.assertRegex(self.flat, r"(?i)treat the recommendation as \*?\*?satisfied",
                         "the exemption does not say the recommendation is satisfied")
        self.assertRegex(self.flat, r"(?i)ask \*?\*?nothing",
                         "the exemption does not forbid the question")

    def test_the_step_down_clause_points_at_the_exemption(self):
        """Two clauses that each look right is how this shipped; link them."""
        self.assertRegex(
            self.flat,
            r"(?i)an effort above the whole table never reaches\s*this clause",
            "the step-down clause does not exclude the above-the-table case, so "
            "following it literally still produces the question")

    def test_the_carve_out_is_confined_to_above_the_whole_table(self):
        """A step down INSIDE the table stays a question — a maintainer decision."""
        self.assertRegex(
            self.flat, r"(?i)never to a step down \*?\*?within\*?\*? it",
            "the exemption does not say it excludes within-table step downs, which "
            "reads as license to drop every step-down question")
        self.assertIn("2026-07-26", self.flat,
                      "the maintainer decision the carve-out narrows is not cited")

    def test_the_model_dial_case_is_addressed(self):
        """#334: the model dial HAS the case — Fable 5.1 sits above the top row, Opus 5.5.

        The old answer ("no equivalent case today … Opus 5 is the table's top row, so
        nothing a bootcamper can select sits above it") was already false while Fable 5
        was listed above Opus 5.
        """
        self.assertNotRegex(
            self.flat, r"(?i)dial has no equivalent case today|nothing a bootcamper can select",
            "ground-rules still claims nothing sits above the table's top model")
        self.assertRegex(
            self.flat, r"(?i)model\*?\*? dial has the same case today",
            "the model dial's above-the-table case is not stated")
        self.assertRegex(
            self.flat, r"Fable 5\.1 sits above the table's top row, Opus 5\.5",
            "the model above the table is not named")
        self.assertRegex(
            self.flat, r"(?i)\*?\*?never\*?\*? a model question",
            "a bootcamper on Fable 5.1 could still be asked a model question")

    def test_model_selection_mirrors_the_model_dial_case(self):
        text = squash(read(MODEL_SELECTION))
        self.assertNotIn("Model has no equivalent case today", text)
        self.assertRegex(text, r"Fable 5\.1 sits above the table's top row, Opus 5\.5")


class EffortIsNotClaimedToBeUnreadable(unittest.TestCase):
    def setUp(self):
        self.flat = squash(read(GROUND_RULES))

    def test_the_false_premise_is_gone(self):
        for claim in ("exposed nowhere", "cannot be read at all"):
            with self.subTest(claim=claim):
                self.assertNotIn(
                    claim, self.flat,
                    "ground-rules still asserts reasoning effort cannot be read, which "
                    "sends the dial to the previous-stage fallback even after the "
                    "plugin's own flow has made it readable")

    def test_the_default_wording_replaces_it(self):
        self.assertRegex(self.flat, r"(?i)not exposed\s*\*?\*?by default",
                         "the corrected premise is missing")

    def test_the_effort_command_case_is_stated(self):
        self.assertRegex(
            self.flat,
            r"(?i)`/effort` invocation reports the\s*resulting level in the transcript",
            "nothing says the value becomes readable once the bootcamper runs /effort")
        self.assertRegex(
            self.flat, r"(?i)previous-stage fallback MUST NOT be used for it",
            "the fallback is not forbidden once the value is known, so the premise "
            "correction changes no behavior")

    def test_the_non_cli_path_is_kept(self):
        """INV-001/INV-098: the dial may genuinely be unreadable off the CLI."""
        self.assertRegex(
            self.flat,
            r"(?i)no such\s*command, so the dial may genuinely stay undeterminable",
            "the non-CLI interfaces lost their undeterminable path, which is real")


class TheTableIsAFloorNotACeiling(unittest.TestCase):
    def test_both_copies_say_so(self):
        for path in (GROUND_RULES, MODEL_SELECTION):
            with self.subTest(file=path.name):
                self.assertRegex(
                    squash(read(path)),
                    r"(?i)a recommended floor for value, not a ceiling",
                    "%s does not say the effort values are a floor, so a reader can "
                    "conclude xhigh is out of policy" % path.name)

    def test_the_derived_doc_carries_the_exemption_row(self):
        flat = squash(read(MODEL_SELECTION))
        self.assertRegex(flat, r"(?i)above every row.{0,40}in the table",
                         "the nudge-behavior table in the derived doc has no row for "
                         "an effort above the table, so the two copies disagree")


if __name__ == "__main__":
    unittest.main()
