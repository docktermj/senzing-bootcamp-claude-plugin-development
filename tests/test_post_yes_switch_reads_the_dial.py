"""After a yes to the switch question, the reply is composed from the live dial.

The module-start nudge names the literal CLI command in its question — "Would you like to
switch to `/effort medium` for this module?" — which invites the Bootcamper to run it before
answering. That is the natural response to being shown a command, not an edge case. The
post-yes branch had exactly one shape, so it assumed they had *not* run it yet.

Observed 2026-08-14 at a module start: the Bootcamper replied yes and ran `/effort xhigh` —
up, not down — in the same turn. Following the flow as written then required emitting

    Switching to `/effort medium` — run `/effort medium` in the Claude Code CLI.

which is wrong twice: it instructs a command already run, and it names a value the Bootcamper
had just deliberately rejected in favor of a higher one. The pinned gate that follows,
"Are you done modifying the model and effort?", then asked a question the transcript had
already answered.

Enforces **INV-236** — the reply after a yes is composed from what the dial is actually set
to, and never re-instructs a value the Bootcamper has moved past.

⛔ The sweep is the load-bearing part. This flow used to be mirrored in `ground-rules.md` and
`graduation/SKILL.md`, and fixing one copy while the other regresses is the exact shape that
left INV-097 unimplemented for seven weeks (a criterion naming a second consumer, only the
first built). So every file carrying a pinned switch question is held to all three shapes,
rather than known files being spot-checked by name.

Since #293 the flow is stated once, in `ground-rules.md`; graduation points to it and keeps only
where its own flow resumes. The sweep stays a scan, so a copy pasted back anywhere is found and
held to all three shapes — and `test_model_switch_rule_is_stated_once.py` fails on it outright.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"
MODEL_SELECTION = PLUGIN / "docs" / "model-selection.md"

#: The pinned switch question, in either the CLI or the intent-based form.
SWITCH_QUESTION = re.compile(r"👉 \*\*Would you like to switch to")
#: An example transcript is a record of a past run, not an instruction file.
NOT_AN_INSTRUCTION = ("docs/examples/",)

#: Shape 2 and shape 3 both continue in the same turn with no gate; shape 1 keeps the gate.
READS_THE_DIAL = re.compile(
    r"(?i)read what the dial is actually set to before you\s+compose the reply"
)
SHAPE_ALREADY_RECOMMENDED = re.compile(r"(?i)already at the recommended value")
SHAPE_DIFFERENT_VALUE = re.compile(r"(?i)already at a different value")
NEVER_REINSTRUCT = re.compile(
    r"(?i)Never\s+re-instruct the recommended command once the bootcamper has (?:set|chosen) a\s+different value"
)
RUNNING_HIGHER_IS_FINE = re.compile(r"(?i)running higher is fine")
COSTS_MORE = re.compile(r"(?i)simply\s+costs more")


def flat(path):
    """Whitespace-collapsed text; blockquote markers kept, since pinned questions use them."""
    return re.sub(r"[ \t]+", " ", path.read_text(encoding="utf-8"))


def squashed(path):
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def shape_three(path, span=900):
    """Shape 3's own text — from its heading forward — or None if it is absent."""
    text = squashed(path)
    found = SHAPE_DIFFERENT_VALUE.search(text)
    if not found:
        return None
    return text[found.start():found.start() + span]


#: The example sentence shape 3 tells the guide to say. Asserting against THIS, rather than
#: against shape 3's whole block, is deliberate: the block also *quotes* the two phrases in a
#: note explaining that the vocabulary is shared, so deleting the real sentence leaves the
#: quotation behind and a block-level assertion still passes. Verified by negative control —
#: that mutation escaped twice before the assertion was narrowed to the sentence itself.
SHAPE_THREE_SENTENCE = re.compile(r'leave it there: "(?P<said>[^"]+)"')


def shape_three_sentence(path):
    """The words shape 3 puts in the guide's mouth, or None."""
    block = shape_three(path)
    if block is None:
        return None
    found = SHAPE_THREE_SENTENCE.search(block)
    return found.group("said") if found else None


def switch_question_files():
    """Every shipped instruction file carrying a pinned switch question."""
    out = []
    for path in sorted(PLUGIN.rglob("*.md")):
        rel = path.relative_to(PLUGIN).as_posix()
        if any(skip in rel for skip in NOT_AN_INSTRUCTION):
            continue
        if SWITCH_QUESTION.search(path.read_text(encoding="utf-8")):
            out.append(path)
    return out


class EveryCopyOfTheFlowCarriesAllThreeShapes(unittest.TestCase):
    """Criterion 4 — the sweep, so one copy cannot be fixed while the other regresses."""

    def test_the_one_copy_is_found(self):
        """Non-vacuity, and the count: ground-rules is the only file pinning the question.

        It was two (ground-rules and graduation) until #293 replaced graduation's copy with a
        pointer. Pinned at one: a new copy of this flow must not appear at all, and if one ever
        must, it is brought under the sweep deliberately.
        """
        found = switch_question_files()
        self.assertEqual([GROUND_RULES], found, [str(p.relative_to(PLUGIN)) for p in found])

    def test_each_copy_reads_the_dial_before_replying(self):
        for path in switch_question_files():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                self.assertRegex(
                    flat(path), READS_THE_DIAL,
                    "this copy composes the post-yes reply without reading the live "
                    "setting, so a bootcamper who ran the command first is instructed to "
                    "run it again (INV-236)",
                )

    def test_each_copy_has_the_already_recommended_shape(self):
        for path in switch_question_files():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                self.assertRegex(squashed(path), SHAPE_ALREADY_RECOMMENDED)

    def test_each_copy_has_the_different_value_shape(self):
        for path in switch_question_files():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                self.assertRegex(squashed(path), SHAPE_DIFFERENT_VALUE)

    def test_each_copy_forbids_re_instructing_the_recommendation(self):
        """The half that produced the contradictory output, so it is pinned per copy."""
        for path in switch_question_files():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                self.assertRegex(flat(path), NEVER_REINSTRUCT)

    def test_each_copy_reuses_the_above_the_table_vocabulary(self):
        """Shape 3 says the same thing as the above-the-table exemption; same words.

        ⛔ Checked **inside shape 3**, not across the file. `ground-rules.md` already
        contains both phrases in the above-the-table exemption, so a whole-file assertion
        passes with shape 3's copy deleted — verified by negative control, where exactly
        that mutation escaped. Asserting a phrase appears *somewhere* is not asserting the
        claim holds *where it is made*.
        """
        for path in switch_question_files():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                said = shape_three_sentence(path)
                self.assertIsNotNone(
                    said,
                    "shape 3 gives the guide no example sentence to say, so the shared "
                    "vocabulary cannot be checked and will drift",
                )
                self.assertRegex(said, RUNNING_HIGHER_IS_FINE)
                self.assertRegex(said, COSTS_MORE)

    def test_each_copy_cites_the_invariant(self):
        for path in switch_question_files():
            with self.subTest(file=str(path.relative_to(PLUGIN))):
                self.assertIn("INV-236", path.read_text(encoding="utf-8"))


class TheGateIsScopedToTheShapeThatNeedsIt(unittest.TestCase):
    """Criteria 1-3 — shape 1 keeps the gate; shapes 2 and 3 continue in the same turn."""

    def test_ground_rules_says_the_gate_follows_only_a_yes_that_needs_one(self):
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)gate follows a \*\*yes that still needs one\*\* — shape 1 above — and nothing else",
            "the old 'a yes and nothing else' rule now contradicts shapes 2 and 3",
        )

    def test_graduation_takes_the_gate_from_ground_rules(self):
        """Graduation no longer states the gate rule; it follows ground-rules' (#293).

        It carried its own copy of this sentence until then. What it must keep is the pointer
        to the one copy and where its own flow resumes on the paths that skip the gate.
        """
        text = squashed(GRADUATION)
        self.assertIn('`../bootcamp-onboarding/ground-rules.md` → "Module start banners and '
                      'transitions"', text)
        self.assertRegex(text, r"(?i)after a yes whose dial is already set")

    def test_ground_rules_says_the_gate_is_skipped_where_the_dial_is_already_set(self):
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)never in shapes 2 and 3",
            "nothing states that the already-set cases skip the gate, so a reader "
            "may keep gating and ask what the transcript answered",
        )

    def test_shape_1_still_ends_on_the_pinned_gate(self):
        """Criterion 1: the unchanged path stays unchanged."""
        self.assertIn(
            "👉 **Are you done modifying the model and effort?** (Reply yes once "
            "you've set your model and effort; reply no if you need more time.)",
            GROUND_RULES.read_text(encoding="utf-8"),
            "the pinned confirmation gate's wording moved (INV-056)",
        )

    def test_the_non_cli_interface_gets_the_same_shapes(self):
        """Criterion 6: a Desktop/web/IDE bootcamper can also set it before replying."""
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)shapes 2 and 3 name the \*\*setting\*\* rather than a command",
        )
        self.assertIn("INV-158", GROUND_RULES.read_text(encoding="utf-8"))


class TheSwitchQuestionItselfIsUnchanged(unittest.TestCase):
    """Criterion 5 — the scope note: only the reply turn moved."""

    def test_the_cli_switch_question_is_still_pinned_verbatim(self):
        """`for {this module | graduation}` since #293, so graduation still asks "…for graduation?"."""
        self.assertIn(
            "👉 **Would you like to switch to `/model {model}` + `/effort {effort}` for "
            "{this module | graduation}?** (Recommended for best value; reply no to keep your "
            "current {dial}.)",
            GROUND_RULES.read_text(encoding="utf-8"),
        )

    def test_the_dial_substitution_survives(self):
        text = squashed(GROUND_RULES)
        self.assertIn("{dial}", text)
        self.assertRegex(text, r"(?i)\{dial\}.{0,120}resolves\s+to \"model\", \"effort\", or \"model and effort\"")

    def test_the_per_dial_comparison_is_untouched(self):
        # INV-138 governs this rule but is cited at `docs/model-selection.md` and
        # `module-03b`, not here — so the anchor is the rule's own wording in this file.
        self.assertRegex(squashed(GROUND_RULES), r"(?i)Name only the dial that differs")

    def test_the_comparison_is_still_against_what_they_are_running(self):
        """INV-138's substance: compare to the live setting, not the previous stage's."""
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)The recommendation matches what they are already running",
        )

    def test_the_above_the_table_exemption_is_untouched(self):
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)One dial is exempt from the comparison before it starts",
        )

    def test_the_step_down_clause_is_untouched(self):
        self.assertRegex(
            squashed(GROUND_RULES),
            r"(?i)When the recommendation sits \*below\* the current setting, say so in the question itself",
        )


class TheDerivedTableAgrees(unittest.TestCase):
    """`model-selection.md` is derived from ground-rules; a stale row re-teaches the defect."""

    def test_the_differs_row_describes_reading_the_dial(self):
        row = squashed(MODEL_SELECTION)
        self.assertIn("INV-236", row)
        self.assertRegex(row, r"(?i)the reply reads the dial first")
        self.assertRegex(row, r"(?i)never re-instructing a value they have already moved past")


if __name__ == "__main__":
    unittest.main()
