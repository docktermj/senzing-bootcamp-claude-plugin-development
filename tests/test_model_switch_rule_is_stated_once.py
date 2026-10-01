"""The model/effort switch rule is stated once, in ground-rules, and nowhere else.

`graduation/SKILL.md` used to carry its own copy of the module-start model/effort nudge: the
pinned 👉 switch question, the three post-yes shapes and the pinned "Are you done modifying the
model and effort?" gate. The two copies drifted. By 2026-09-30 graduation lacked five things
ground-rules had: the above-the-table exemption (a bootcamper on `/effort xhigh` or `max` was
asked a step-down question at graduation), the per-dial fallback and the readable-`/effort`
clause, the step-down question's "a cost saving, not a capability" clause, the INV-247 limit,
and the one-dial CLI substitution (graduation pinned `/model opus` + `/effort high` as fixed
text). One rule written in two places is how the next divergence ships
(`production-readiness-audit-2026-09-30`, finding D-F9; issue #293).

So graduation now points to ground-rules and keeps only what is specific to graduation: where
its flow resumes (INV-284), the note that it shares Query, Visualize and Discover's
recommendation, and the "correctness-critical" rationale. Ground-rules' pinned question reads
`for {this module | graduation}`, so the bootcamper still sees "…for graduation?".

⛔ The guard is a scan (INV-246): it reads every shipped Markdown file for the pinned switch
question and the pinned gate, never a list of the files expected to carry them. A copy pasted
back into graduation, or into any other file, fails it. The negative controls below paste one in
and check that the scan reports it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"

#: The pinned switch question, in the CLI or the intent-based form. A recap transcript entry
#: (`- **Q:** Would you like to switch to …` in the example recap) is a record, not a pin.
PINNED_SWITCH = re.compile("\U0001F449" + r"\s*\*\*Would you like to switch to")
#: The pinned confirmation gate. Prose naming the gate in quotes is a reference, not a pin.
PINNED_GATE = re.compile(
    "\U0001F449" + r"\s*\*\*Are you done modifying the model and effort\?\*\*")

#: Graduation's section, by heading. Step 1c refers back to it by name ("graduation's
#: best-value model/effort prompt"), so the heading stays.
SECTION_START = "## Best-value model/effort prompt\n"
SECTION_END = "## Pre-checks\n"

#: The pointer acceptance criterion 1 names.
POINTER = '`../bootcamp-onboarding/ground-rules.md` → "Module start banners and transitions"'

#: Anything that would restate the recommended value rather than read it from the table row:
#: a model name, a CLI command (in backticks, so "model/effort" and `model-selection.md` do
#: not count), or an effort level.
RESTATED_VALUE = re.compile(r"Opus|Sonnet|`/model|`/effort|\bx?high\b|\bmedium\b|\bmax\b")

#: The old graduation copy, pasted back, for the negative controls.
OLD_CLI_QUESTION = (
    "> 👉 **Would you like to switch to `/model opus` + `/effort high` for graduation?** "
    "(Recommended for best value; reply no to keep your current {dial}.)\n")
OLD_INTENT_QUESTION = (
    "> 👉 **Would you like to switch to Opus 5 at high reasoning effort for graduation?** "
    "(Recommended for best value; set it with the model and effort controls in {Claude Desktop "
    "| the Claude web app | your Claude IDE extension}; reply no to keep your current {dial}.)\n")
OLD_GATE = (
    "   > 👉 **Are you done modifying the model and effort?** (Reply yes once you've set your "
    "model and effort; reply no if you need more time.)\n")


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def shipped_corpus():
    """Every shipped Markdown file, keyed by its path — derived, never listed (INV-246)."""
    return {path: read(path) for path in sorted(PLUGIN.rglob("*.md"))}


def pinning_sites(corpus, pattern):
    """The files in `corpus` that pin `pattern`."""
    return [path for path, text in corpus.items() if pattern.search(text)]


def graduation_section(text):
    start = text.index(SECTION_START)
    return text[start:text.index(SECTION_END, start)]


def with_pasted(corpus, path, block):
    """`corpus` with `block` pasted into `path`'s model/effort section."""
    mutated = dict(corpus)
    text = mutated[path]
    if SECTION_START in text and SECTION_END in text:
        cut = text.index(SECTION_END)
    else:
        cut = len(text)
    mutated[path] = text[:cut] + "\n" + block + "\n" + text[cut:]
    return mutated


def rel(paths):
    return [str(p.relative_to(PLUGIN)) for p in paths]


class GroundRulesIsTheOnlyCopy(unittest.TestCase):

    def test_the_corpus_is_not_vacuous(self):
        corpus = shipped_corpus()
        self.assertIn(GROUND_RULES, corpus)
        self.assertIn(GRADUATION, corpus)
        self.assertGreater(len(corpus), 20, "the scan read almost nothing")

    def test_only_ground_rules_pins_the_switch_question(self):
        sites = pinning_sites(shipped_corpus(), PINNED_SWITCH)
        self.assertEqual(
            [GROUND_RULES], sites,
            "the pinned switch question is copied outside ground-rules: %s. Point to "
            "ground-rules.md → \"Module start banners and transitions\" instead (#293)."
            % rel(sites))

    def test_only_ground_rules_pins_the_confirmation_gate(self):
        sites = pinning_sites(shipped_corpus(), PINNED_GATE)
        self.assertEqual(
            [GROUND_RULES], sites,
            "the pinned \"Are you done modifying the model and effort?\" gate is copied "
            "outside ground-rules: %s (#293)" % rel(sites))

    def test_ground_rules_pins_both_forms_for_graduation_too(self):
        """Acceptance criterion 3: the bootcamper still sees "…for graduation?"."""
        questions = [line for line in read(GROUND_RULES).splitlines()
                     if PINNED_SWITCH.search(line)]
        self.assertEqual(2, len(questions), "expected the CLI and the intent-based form")
        for line in questions:
            with self.subTest(line=line[:70]):
                self.assertIn("for {this module | graduation}?**", line)
                self.assertNotIn("for this module?**", line)


class GraduationKeepsOnlyWhatIsSpecificToIt(unittest.TestCase):

    def setUp(self):
        self.section = squash(graduation_section(read(GRADUATION)))

    def test_it_points_to_the_one_copy(self):
        self.assertIn(POINTER, self.section)

    def test_it_states_where_its_flow_resumes(self):
        """INV-284: the gate's handling step lives in the skill that resumes."""
        self.assertIn("INV-284", self.section)
        self.assertRegex(
            self.section,
            r'Wherever ground-rules says to present "Step 1", graduation runs the Pre-checks '
            r"and then its first step, Step 0")
        self.assertIn("on the turn after the bootcamper confirms the switch", self.section)

    def test_it_keeps_the_shared_recommendation_note(self):
        self.assertIn("shares its recommendation with Query, Visualize and Discover",
                      self.section)
        self.assertIn("usually **already there**", self.section)
        self.assertIn("are not asked", self.section)

    def test_it_keeps_its_rationale(self):
        """No rationale sentence from graduation's copy is lost (acceptance criterion 6)."""
        for sentence in (
                "Bootcamp graduation is correctness-critical",
                "Do not assume graduation is always a step up — it is not, and asking a "
                "bootcamper to switch to the model they are already running is the pointless "
                "question INV-006 and INV-012 forbid"):
            with self.subTest(sentence=sentence[:50]):
                self.assertIn(sentence, self.section)

    def test_it_does_not_restate_the_recommended_value(self):
        """The value is the "Bootcamp graduation" row of the ground-rules table."""
        self.assertIn('"Bootcamp graduation" row', self.section)
        self.assertIn("| Bootcamp graduation |", read(GROUND_RULES))
        self.assertEqual([], RESTATED_VALUE.findall(self.section))

    def test_step_1c_can_still_find_the_section_it_names(self):
        """Step 1c's heads-up follows only a no to "that switch question" (#300)."""
        text = read(GRADUATION)
        self.assertIn(SECTION_START, text)
        self.assertIn("graduation's best-value model/effort prompt already covers it",
                      squash(text))


class TheRationaleGraduationDroppedLivesInGroundRules(unittest.TestCase):
    """Each "why" graduation's copy carried is still stated, in the one copy."""

    def test_each_reason_is_in_ground_rules(self):
        text = squash(read(GROUND_RULES))
        for reason in (
                "that is the natural response to being shown a command",
                "the table is a recommended floor for value, not a ceiling",
                "That is why the switch is offered as a question rather than performed",
                "the gate would ask what the transcript has answered",
                "Nothing is left to confirm",
                "there is no preference to read and no mode to choose (INV-137)"):
            with self.subTest(reason=reason[:50]):
                self.assertIn(reason, text)


class NegativeControls(unittest.TestCase):
    """Paste a copy back and check the scan reports it."""

    def test_a_switch_question_pasted_into_graduation_is_reported(self):
        for block in (OLD_CLI_QUESTION, OLD_INTENT_QUESTION):
            with self.subTest(block=block[:60]):
                corpus = with_pasted(shipped_corpus(), GRADUATION, block)
                self.assertEqual({GRADUATION, GROUND_RULES},
                                 set(pinning_sites(corpus, PINNED_SWITCH)))

    def test_the_gate_pasted_into_graduation_is_reported(self):
        corpus = with_pasted(shipped_corpus(), GRADUATION, OLD_GATE)
        self.assertEqual({GRADUATION, GROUND_RULES},
                         set(pinning_sites(corpus, PINNED_GATE)))

    def test_a_copy_pasted_into_another_skill_is_reported(self):
        """Any skill, not only graduation: the site set is scanned."""
        other = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"
        corpus = with_pasted(shipped_corpus(), other, OLD_CLI_QUESTION + OLD_GATE)
        self.assertIn(other, pinning_sites(corpus, PINNED_SWITCH))
        self.assertIn(other, pinning_sites(corpus, PINNED_GATE))

    def test_a_restated_value_is_reported(self):
        section = graduation_section(read(GRADUATION))
        pasted = section + "Bootcamp graduation is correctness-critical: **Opus 5 + high effort**."
        self.assertNotEqual([], RESTATED_VALUE.findall(squash(pasted)))

    def test_a_reference_in_quotes_is_not_a_pin(self):
        """Prose that names the gate, as bootcamp-preparation does, is not a copy."""
        corpus = {GRADUATION: 'the pinned "Are you done modifying the model and effort?" gate'}
        self.assertEqual([], pinning_sites(corpus, PINNED_GATE))


if __name__ == "__main__":
    unittest.main()
