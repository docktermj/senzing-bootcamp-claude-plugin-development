"""An instruction to end the turn on a question must resolve to a question that exists.

`phase2-data-mapping.md`'s INV-205 carve-out overrides `mapping_workflow`'s "do not ask the
user" directive at the entity-plan advance and routes the decision to the bootcamper's
mapping-verbosity choice: in the guided mode, "present the plan and end the turn on ... 👉
before advancing". For seven weeks there was no such question. Step 10 contained the advance
instruction, the `embedded_master` check, a checkpoint and a presentation block — and no 👉.

The guide could not resolve that on its own, because both available moves are forbidden by
something else in the same module: inventing a gate question breaches INV-056 (which pins every
gate question's wording so it cannot drift at runtime), and advancing without asking breaches
the carve-out and silently breaks the promise the verbosity offer made one step earlier. Nor is
it an edge case — any single-schema plan clears the tool's 0.80 confidence bar trivially, so the
tool's fast path applies and the carve-out is supposed to override it.

The general rule this pins: **wherever shipped guidance says to end the turn on a question, a
pinned 👉 must exist in the section that owns it** — the same section, or, when the instruction
names another step, that step's section. That resolution rule is what makes a cross-reference
safe: the carve-out may state the rule while step 10 owns the wording (INV-183), but the wording
has to be there.

Enforces **INV-233** — an instruction to end the turn on a question must resolve to a pinned
question in the section that owns it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import blocks, match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PHASE2 = PLUGIN / "skills" / "module-05-data-quality-mapping" / "phase2-data-mapping.md"

#: Any heading level 2 or deeper. Step sections in this module are `### 10. Plan`.
HEADING = re.compile(r"(?m)^(#{2,})\s+(.*)$")
#: The instruction, in both the "end the turn on" and "ending the turn on" forms.
END_TURN = re.compile(r"end(?:ing)? the turn on")
#: A cross-reference to another step, e.g. "at **step 10**" or "at step 18a".
NAMES_STEP = re.compile(r"(?i)step \*{0,2}(\d+[a-z]?)")
QUESTION_MARK = "👉"


def sections(text):
    """[(title, body)] for every heading-delimited section, plus any preamble."""
    marks = [(m.start(), m.group(2).strip()) for m in HEADING.finditer(text)]
    if not marks:
        return [("(whole file)", text)]
    out = []
    if marks[0][0] > 0:
        out.append(("(preamble)", text[:marks[0][0]]))
    for i, (start, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((title, text[start:end]))
    return out


def section_for_step(text, number):
    """The body of the `### <number>. Title` section, or None when there is no such step."""
    for title, body in sections(text):
        if re.match(r"^%s\.\s" % re.escape(number), title):
            return body
    return None


def enclosing_section(text, index):
    for title, body in sections(text):
        start = text.index(body)
        if start <= index < start + len(body):
            return title, body
    return "(whole file)", text


def end_turn_instructions(text):
    """[(lineno, tail)] for each end-the-turn instruction in ``text``, across line wraps.

    ⚠️ **Matched across line wraps (#424).** ``END_TURN`` searched the raw text, whose line
    breaks its literal spaces cannot match, so five instructions wrapped as "end the\nturn on"
    were never checked. The lines come from ``match_lines``; each tail is the 120 characters
    from the instruction, from the same blocks collapsed the same way (every run of whitespace
    to one space, trimmed) and searched in the same order, so the two lists line up. A tail
    is no longer cut at the end of the physical line, so a step named after a wrap is read.
    """
    tails = []
    for block in blocks(text):
        flat = " ".join(" ".join(line for _n, line in block).split())
        tails += [flat[m.start():m.start() + 120] for m in END_TURN.finditer(flat)]
    lines = match_lines(text, END_TURN)
    assert len(lines) == len(tails), "match_lines and the block scan disagree"
    return list(zip(lines, tails))


def line_offset(text, lineno):
    """The character offset where 1-based line ``lineno`` starts."""
    return sum(len(line) + 1 for line in text.split("\n")[:lineno - 1])


def obligations():
    """[(relpath, section title, resolved target body)] for every end-the-turn instruction."""
    found = []
    for path in sorted(PLUGIN.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for lineno, tail in end_turn_instructions(text):
            title, body = enclosing_section(text, line_offset(text, lineno))
            # Resolve a cross-reference before falling back to the enclosing section: the
            # carve-out deliberately states the rule where it applies and keeps the wording
            # at the step that owns it.
            named = NAMES_STEP.search(tail)
            target = body
            if named:
                referenced = section_for_step(text, named.group(1))
                if referenced is not None:
                    target = referenced
            found.append((str(path.relative_to(REPO_ROOT)), title, target))
    return found


class EveryEndTheTurnInstructionResolvesToAQuestion(unittest.TestCase):
    """Criterion 5 — the general rule, over every shipped instruction file."""

    def test_there_are_obligations_to_check(self):
        # Without this the sweep would pass silently if the phrasing were reworded away.
        self.assertGreater(len(obligations()), 5, "found almost no end-the-turn instructions")

    def test_each_one_has_a_pinned_question_in_the_owning_section(self):
        for rel, title, target in obligations():
            with self.subTest(file=rel, section=title[:60]):
                self.assertIn(
                    QUESTION_MARK, target,
                    "'end the turn on' in %s (section %r) resolves to a section with no 👉 "
                    "question, so the guide is told to stop on a question that does not "
                    "exist" % (rel, title),
                )


class TheInstructionIsReadAcrossLineWraps(unittest.TestCase):
    """Negative controls for the #424 conversion."""

    WRAPPED = ("### 4. Pick a source\n\nList them, then end the\nturn on the question at\n"
               "**step\n9**.\n\n### 9. Choose\n\n👉 **Which source first?**\n")

    def test_a_wrapped_instruction_is_found_at_its_first_line(self):
        found = end_turn_instructions(self.WRAPPED)
        self.assertEqual([3], [n for n, _tail in found])
        # The old raw-text search, kept only to show the fixture is the hard case.
        self.assertIsNone(END_TURN.search(self.WRAPPED))

    def test_its_wrapped_step_reference_resolves_to_the_owning_section(self):
        (_n, tail), = end_turn_instructions(self.WRAPPED)
        self.assertEqual("9", NAMES_STEP.search(tail).group(1))
        self.assertIn(QUESTION_MARK, section_for_step(self.WRAPPED, "9"))


class Step10CarriesThePinnedEntityPlanQuestion(unittest.TestCase):
    """Criteria 1-2 — the question itself, and the routing that uses it."""

    def setUp(self):
        self.step10 = section_for_step(PHASE2.read_text(encoding="utf-8"), "10")
        self.assertIsNotNone(self.step10, "phase2 has no '### 10.' section")

    def test_it_has_a_pinned_question(self):
        self.assertIn(QUESTION_MARK, self.step10)

    def test_the_lead_is_neutral_and_asks_for_a_number(self):
        # INV-051: the lead question must not steer, and must not join choices with "or".
        self.assertRegex(
            self.step10,
            r"👉 \*\*Here's the entity plan for \{source\}\. How would you like to proceed\? "
            r"Reply with a number:\*\*",
        )

    def test_it_offers_accept_change_type_and_change_record_id(self):
        # A confirmation gate whose only answer is "yes" is the pointless question INV-012
        # forbids, so the three substantive options are the requirement — not decoration.
        self.assertRegex(self.step10, r"1\. \*\*Looks right — map the fields\.\*\*")
        self.assertRegex(self.step10, r"2\. \*\*Change the entity type\*\* \(currently \{record_type\}\)")
        self.assertRegex(
            self.step10,
            r"3\. \*\*Change which field identifies each record\*\* \(currently \{record_id_source\}\)",
        )

    def test_it_says_to_end_the_turn_and_wait(self):
        self.assertRegex(self.step10, r"(?i)end the turn on this question and wait")

    def test_the_verbose_branch_gates_and_the_concise_branch_does_not(self):
        self.assertRegex(self.step10, r"(?i)\*\*Verbose:\*\*.{0,200}end the turn on the pinned question")
        self.assertRegex(self.step10, r"(?i)\*\*Concise:\*\*.{0,200}same turn\*\*, with \*\*no\*\* question")

    def test_it_does_not_re_ask_settled_parts(self):
        self.assertIn("INV-006", self.step10)

    def test_it_cites_inv056_for_the_pinned_wording(self):
        self.assertIn("INV-056", self.step10)


class TheCarveOutPointsAtStep10WithoutRestatingIt(unittest.TestCase):
    """Criterion 3 — the rule is stated where it applies, the wording lives at step 10."""

    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")
        self.carve_out = next(
            body for title, body in sections(self.text)
            if "The tool's responses instruct" in title
        )

    def test_it_names_step_10(self):
        self.assertRegex(self.carve_out, r"(?i)pinned question at \*\*step 10\*\*")

    def test_it_no_longer_refers_to_an_undefined_question(self):
        self.assertNotRegex(self.carve_out, r"(?i)this module's own 👉")

    def test_it_does_not_restate_the_question(self):
        # One wording, one home (INV-183). A second copy is what drifts.
        self.assertNotIn("How would you like to proceed", self.carve_out)
        self.assertNotIn("Looks right", self.carve_out)

    def test_the_tools_non_conversational_authority_is_unchanged(self):
        # Criterion 6: the carve-out is about conversation only, and says so.
        self.assertRegex(self.carve_out, r"(?i)This carve-out is about \*conversation only\*")
        self.assertIn("INV-080", self.carve_out)
        self.assertRegex(self.carve_out, r"(?i)opaque `state` echo")


class TheSiblingAdvancesSayWhetherTheyGate(unittest.TestCase):
    """Criterion 4 — steps 11 and 15 state their advance is unconditional, and why."""

    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")

    def test_step_11_states_its_advance_is_unconditional(self):
        step11 = section_for_step(self.text, "11")
        self.assertRegex(step11, r"(?i)advance is unconditional in both modes")
        self.assertRegex(step11, r"(?i)deliberate")

    def test_step_15_states_its_advance_is_unconditional(self):
        step15 = section_for_step(self.text, "15")
        self.assertRegex(step15, r"(?i)advance is unconditional in both modes")

    def test_step_15_says_why_the_verdict_is_not_the_bootcampers(self):
        step15 = section_for_step(self.text, "15")
        self.assertRegex(step15, r"(?i)not a preference")


if __name__ == "__main__":
    unittest.main()
