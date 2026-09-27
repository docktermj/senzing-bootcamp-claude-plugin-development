"""Anything meant to inform an answer is written BEFORE its 👉 question, never after.

Two reasons, the first mechanical: nothing may follow the 👉, because it ends the turn — so
text placed after it is either never delivered or delivered a turn late. The second is that a
caveat arriving after the answer cannot inform the choice it exists to inform.

Bootcamp preparation Step 3 states this correctly and gives the reason. Two other sites did
not, and both were resolved only by a guide importing the reasoning from a different file:

1. **Module 1 Phase 2 Step 10a** printed `Reassure: "We'll develop everything locally first…"`
   *after* the pinned deployment-target question AND after `*(Internal: end the turn and
   wait.)*`. That reassurance is what makes "4. Not sure yet" a comfortable answer rather than
   a guess.
2. **The visualization teardown gate** said "Tell the bootcamper what they are consenting to
   **before they answer**" — in a paragraph placed *below* the gate. Found by sweeping for this
   spec rather than by the walk that motivated it, and it is the worse of the two: the consent
   authorizes an irreversible teardown, and the file's own next sentence is "A yes given
   without that is not an informed yes."

The general guard here keys on that second shape, because it is **self-contradicting in its own
words** and therefore mechanically decidable: an instruction saying to do something *before they
answer*, positioned after the question, cannot be followed as written. A broader "no prose after
a 👉" sweep is not viable — these are skill files written for the guide, so answer-handling
instructions ("on yes, …") legitimately and frequently follow a question. Surveyed before
writing this: five speech-cue lines follow a 👉 across all skills, and three are legitimate
answer handling. Guarding the decidable shape beats a broad rule with three standing exceptions.

A second guard bounds the check to the **question block**, where the file itself marks the end:
the question's own numbered options. Data processing Step 1 pinned its volume question with the
explanation between the 👉 and the options, and a "Not sure yet?" line after them, so a guide
could not honor the verbatim rule (INV-056) and the placement rules at once (#162). The scan
covers every shipped 👉 question under ``plugins/`` (INV-246) and fails on prose between a 👉
line and its first option, or after an option, inside the same block. How a block is delimited:

- **Blockquoted** (``> 👉 …``): the run of consecutive ``>`` lines, up to the next 👉 question.
  Framing above the 👉 inside the quote is correct and is not read.
- **Not blockquoted**: the numbered list that starts at the first non-blank line after the 👉,
  up to the first paragraph that is not part of it. Markdown gives no other end marker, so prose
  directly after an unquoted 👉 means the question has no pinned options (the
  programming-language gate generates its list at runtime), and prose after the list is
  answer handling ("*(Internal: …)* Then act on the choice:") — both outside the block.

``*(Internal: …)*`` directives are exempt anywhere in a block: they belong to the question.

Enforces **INV-211**. The question-block guard also enforces **INV-224** (options directly
beneath the 👉), which ``test_answer_options_render_below_the_question.py`` states for the
programming-language gate.

Run:  python3 -m unittest discover -s tests
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS = REPO_ROOT / "plugins"
SKILLS = PLUGINS / "senzing-bootcamp" / "skills"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
STEP_10A = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
TEARDOWN = SKILLS / "module-03b-truthset-visualization" / "visualization-api-reference.md"
PREP = SKILLS / "bootcamp-preparation" / "SKILL.md"
VOLUME = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"

POINTER = "\U0001f449"
#: Self-contradicting when it appears after a 👉: an instruction to act before the answer.
BEFORE_ANSWERING = re.compile(r"(?i)before (?:they|you) answer|before answering|before the answer")
#: A shipped 👉 question: the pointer, then its bold question text. A 👉 in running prose ("the 👉
#: protocol", "one 👉 per turn") names the symbol and asks nothing.
QUESTION = re.compile(POINTER + r"\s*\*\*")
#: A numbered answer option; group 1 is its indentation, which its continuation lines exceed.
OPTION = re.compile(r"^(\s*)\d+[.)]\s")
QUOTED = re.compile(r"^\s*>")
#: An internal directive belongs to the question (ground rules), so it is exempt in a block.
INTERNAL_OPEN = re.compile(r"^\s*[*_]\(Internal:")
INTERNAL_CLOSE = re.compile(r"\)[*_]")


def sections(text):
    """[(heading, [lines])] — split on Markdown headings, which bound a step."""
    out, head, buf = [], "(top)", []
    for line in text.splitlines():
        if line.startswith("#"):
            out.append((head, buf))
            head, buf = line.strip(), []
        else:
            buf.append(line)
    out.append((head, buf))
    return out


def misplaced_before_answer_instructions():
    """[(relpath, heading, line)] for a 'before they answer' cue following a 👉 in one section."""
    bad = []
    for path in sorted(SKILLS.rglob("*.md")):
        for head, lines in sections(path.read_text(encoding="utf-8")):
            seen_pointer = False
            for line in lines:
                if POINTER in line:
                    seen_pointer = True
                    continue
                if seen_pointer and BEFORE_ANSWERING.search(line):
                    bad.append((str(path.relative_to(REPO_ROOT)), head, line.strip()[:120]))
    return bad


def indent(line):
    return len(line) - len(line.lstrip())


def block_after(lines, i):
    """The lines of the question block that follow the 👉 line ``lines[i]``.

    Blockquoted: the rest of the quote, with its ``>`` markers removed. Not blockquoted: the
    numbered list starting at the first non-blank line after the 👉, or nothing when that line
    is not an option. Either way the block stops at the next 👉 question.
    """
    out = []
    if QUOTED.match(lines[i]):
        for line in lines[i + 1:]:
            if not QUOTED.match(line) or QUESTION.search(line):
                break
            out.append(re.sub(r"^\s*>\s?", "", line))
        return out
    marker, blanks = None, []
    for line in lines[i + 1:]:
        if QUESTION.search(line):
            break
        if not line.strip():
            blanks.append(line)
            continue
        option = OPTION.match(line)
        if marker is None:
            if not option:
                break
            marker = len(option.group(1))
        elif not (option and len(option.group(1)) == marker) and indent(line) <= marker and blanks:
            break
        out.extend(blanks)
        blanks = []
        out.append(line)
    return out


def misplaced_in_block(body):
    """[(placement, line)] for prose in a block's body, or [] when the block has no options."""
    options = [k for k, line in enumerate(body) if OPTION.match(line)]
    if not options:
        return []
    bad, internal, marker = [], False, None
    for k, line in enumerate(body):
        option = OPTION.match(line)
        if option:
            marker = len(option.group(1))
            continue
        if internal or INTERNAL_OPEN.match(line):
            internal = not INTERNAL_CLOSE.search(line)
            continue
        if not line.strip() or (marker is not None and indent(line) > marker):
            continue
        placement = "before its first option" if k < options[0] else "after an option"
        bad.append((placement, line.strip()))
    return bad


def question_blocks():
    """[(relpath, lineno, question, body)] for every shipped 👉 question under ``plugins/``."""
    out = []
    for path in sorted(PLUGINS.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if QUESTION.search(line):
                out.append((str(path.relative_to(REPO_ROOT)), i + 1, line.strip(),
                            block_after(lines, i)))
    return out


def index_of(lines, predicate):
    for i, line in enumerate(lines):
        if predicate(line):
            return i
    return -1


class TheRuleIsStatedOnce(unittest.TestCase):
    def test_ground_rules_states_the_ordering_rule_in_the_pointer_protocol(self):
        text = GROUND_RULES.read_text(encoding="utf-8")
        start = text.index("## Conversation protocol")
        end = text.index("\n## ", start)
        protocol = text[start:end]
        self.assertRegex(
            protocol,
            r"(?i)before the .?\U0001f449|goes BEFORE",
            "ground-rules' 👉 protocol must state that anything informing the answer precedes "
            "the question. Stated only inside one step, it did not propagate to two others.",
        )
        self.assertRegex(
            protocol,
            r"(?i)ends the turn|nothing may follow",
            "the rule must carry its mechanical reason — nothing may follow the 👉 — or it "
            "reads as a style preference and gets 'tidied' back.",
        )
        self.assertRegex(
            protocol,
            r"(?i)answer.handling|on yes",
            "the rule must carve out answer-handling instructions, which legitimately follow "
            "a question; without that it over-reaches and will be ignored.",
        )


class NoInstructionSaysBeforeTheAnswerAfterTheQuestion(unittest.TestCase):
    def test_no_skill_places_a_before_they_answer_cue_after_its_pointer(self):
        bad = misplaced_before_answer_instructions()
        self.assertEqual(
            [], bad,
            "an instruction to do something 'before they answer' is positioned AFTER the 👉, "
            "which cannot be followed as written — nothing may follow the 👉:\n  "
            + "\n  ".join(f"{p} [{h}] {ln}" for p, h, ln in bad),
        )

    def test_the_detector_finds_the_shape_it_guards(self):
        """Non-vacuity: the scan must fire on the historical arrangement."""
        historical = [
            "- teardown gate. → \U0001f449 **Ready for me to stop the server?**",
            "",
            "Tell the bootcamper what they are consenting to before they answer: the URL dies.",
        ]
        seen, hits = False, []
        for line in historical:
            if POINTER in line:
                seen = True
                continue
            if seen and BEFORE_ANSWERING.search(line):
                hits.append(line)
        self.assertEqual(1, len(hits), "the detector must fire on the shape it was built for")

    def test_the_detector_ignores_answer_handling_that_follows_a_question(self):
        """Answer handling after a 👉 is correct and must not be flagged."""
        ok = [
            "\U0001f449 **Will your results interface with other software?**",
            "",
            "On **yes**, ask one follow-up on the next turn and hold the named systems.",
            "If the bootcamper skips, default to verbose, persist it, and say so.",
        ]
        seen, hits = False, []
        for line in ok:
            if POINTER in line:
                seen = True
                continue
            if seen and BEFORE_ANSWERING.search(line):
                hits.append(line)
        self.assertEqual([], hits, "answer-handling instructions must not trip the scan")


class NothingButOptionsFollowsAQuestionInsideItsBlock(unittest.TestCase):
    """#162: framing precedes the 👉, options sit directly beneath it, and nothing follows them."""

    #: Data processing Step 1 as it shipped before #162 — the shape this guard exists to catch.
    HISTORICAL = [
        "> \U0001f449 **How many records do you expect to load? Reply with a number:**",
        ">",
        "> This is about the system you're ultimately building, not the dataset here.",
        ">",
        "> 1. 500 or fewer — demo/evaluation",
        "> 2. More than 500 — production",
        ">",
        "> Not sure yet? Give your best estimate — we'll build for that.",
    ]

    def test_no_shipped_question_has_prose_between_or_after_its_options(self):
        bad = [(p, n, placement, text)
               for p, n, _, body in question_blocks()
               for placement, text in misplaced_in_block(body)]
        self.assertEqual(
            [], bad,
            "prose sits inside a 👉 question block, between the question and its options or "
            "after them. Framing goes BEFORE the 👉 and the options sit DIRECTLY BENEATH it "
            "(ground rules, INV-211); a pinned block in this shape cannot be presented "
            "verbatim (INV-056) and compliantly at once:\n  "
            + "\n  ".join(f"{p}:{n} [{pl}] {tx[:100]}" for p, n, pl, tx in bad),
        )

    def test_the_scan_sees_the_question_population(self):
        """Non-vacuity (INV-246): the site set is derived, so check the scan still finds it."""
        blocks = question_blocks()
        with_options = [b for b in blocks if any(OPTION.match(l) for l in b[3])]
        quoted = [b for b in with_options if b[2].startswith(">")]
        self.assertGreaterEqual(
            len(with_options), 30,
            "fewer than 30 option-bearing 👉 questions found under plugins/ (about 40 ship); "
            "fix the scan rather than trusting an empty offender list")
        self.assertGreaterEqual(len(quoted), 8, "the scan stopped seeing blockquoted questions")
        self.assertGreaterEqual(len(with_options) - len(quoted), 8,
                                "the scan stopped seeing questions outside a blockquote")
        self.assertTrue(
            any(p.endswith("phaseA-build-loading.md") and "how many records do you expect" in q
                and any(OPTION.match(l) for l in body)
                for p, _, q, body in blocks),
            "the scan no longer sees Data processing Step 1's options — the site #162 fixed")

    def test_the_detector_finds_both_historical_placements(self):
        hits = misplaced_in_block(block_after(self.HISTORICAL, 0))
        self.assertEqual(
            ["before its first option", "after an option"], [p for p, _ in hits],
            "the detector must fire once for each placement in the shape it was built for")

    def test_the_detector_reaches_a_question_outside_a_blockquote(self):
        """Unquoted, the list ends at a blank line; a line directly beneath an option is in it."""
        unquoted = [
            "\U0001f449 **How would you like to proceed? Reply with a number:**",
            "",
            "1. Proceed on SQLite.",
            "2. Migrate to PostgreSQL.",
            "Not sure? Pick one — it can be revisited.",
        ]
        self.assertEqual(["after an option"],
                         [p for p, _ in misplaced_in_block(block_after(unquoted, 0))])

    def test_the_detector_ignores_internal_directives_and_answer_handling(self):
        quoted = [
            "> Framing inside the quote, above the question, is where it belongs.",
            ">",
            "> \U0001f449 **Which one? Reply with a number:**",
            ">",
            "> 1. **First** — a label that wraps",
            ">    onto a continuation line.",
            "> 2. **Second**",
            "",
            "*(Internal: end the turn on this question and wait.)* On **2**, re-ask.",
        ]
        unquoted = [
            "   \U0001f449 **How would you like to proceed? Reply with a number:**",
            "",
            "   1. Proceed on SQLite.",
            "   2. Migrate to PostgreSQL.",
            "",
            "   *(Internal: end the turn on this question and wait.)* Then act on the choice:",
            "",
            "   - **Proceed:** continue.",
        ]
        generated = [
            "  \U0001f449 **Which programming language? Reply with a number:**",
            "",
            "- This is a gate whose wording is pinned; wait for the real choice.",
            "",
            "1. **The dial is not yet set** — answer handling that happens to be numbered.",
        ]
        for name, lines in (("quoted", quoted), ("unquoted", unquoted), ("generated", generated)):
            with self.subTest(shape=name):
                i = index_of(lines, lambda l: QUESTION.search(l))
                self.assertEqual([], misplaced_in_block(block_after(lines, i)),
                                 "a compliant question must not be flagged")


class TheVolumeQuestionIsCompliantAsWritten(unittest.TestCase):
    """#162: Data processing Step 1's pinned block, and the one hint that asks for an option."""

    def setUp(self):
        self.lines = VOLUME.read_text(encoding="utf-8").splitlines()
        self.q = index_of(self.lines,
                          lambda l: POINTER in l and "how many records do you expect" in l)
        self.assertNotEqual(-1, self.q, "the volume question moved — retarget this test")

    def test_the_hint_asks_for_the_option_number(self):
        self.assertIn(
            "Reply with the option number:**", self.lines[self.q],
            "the question asks about a count over a numbered list, so 'Reply with a number' "
            "gives a reply like '4' two readings; the hint must ask for the option number")

    def test_the_framing_precedes_the_question(self):
        framing = index_of(self.lines, lambda l: "fifty-million-record loader" in l)
        unsure = index_of(self.lines, lambda l: "pick the range your best estimate falls in" in l)
        self.assertNotEqual(-1, framing, "the explanation paragraph must be present")
        self.assertNotEqual(-1, unsure, "the 'not sure' framing must ask for a range")
        self.assertLess(framing, self.q, "the explanation must precede the 👉")
        self.assertLess(unsure, self.q, "the 'not sure' framing must precede the 👉")

    def test_no_line_invites_a_bare_number_estimate(self):
        text = " ".join(self.lines)
        self.assertNotRegex(
            text, r"(?i)give your best estimate",
            "an invitation to give a bare estimate collides with the option numbers: the "
            "classifier reads a bare 1-4 as an option")

    def test_the_lead_in_says_the_explanation_precedes_the_question(self):
        lead = " ".join(self.lines[max(0, self.q - 25):self.q])
        self.assertRegex(
            lead, r"(?i)explanation, which \*\*precedes\*\* the\s+\U0001f449",
            "the lead-in must say the explanation comes before the question, or 'verbatim, "
            "including the explanation' reads as license for the old order")


class TheTwoFixedSitesStayFixed(unittest.TestCase):
    def test_step_10a_reassurance_precedes_the_deployment_question(self):
        lines = STEP_10A.read_text(encoding="utf-8").splitlines()
        q = index_of(lines, lambda l: POINTER in l and "Where do you plan to deploy" in l)
        r = index_of(lines, lambda l: "Reassure them first" in l)
        self.assertNotEqual(-1, q, "the deployment-target question moved — retarget this test")
        self.assertNotEqual(-1, r, "Step 10a must reassure before asking")
        self.assertLess(
            r, q,
            "the reassurance must appear BEFORE the deployment-target question; it is what "
            "makes 'Not sure yet' a comfortable answer rather than a guess",
        )

    def test_the_teardown_consent_disclosure_precedes_the_gate(self):
        lines = TEARDOWN.read_text(encoding="utf-8").splitlines()
        gate = index_of(lines, lambda l: POINTER in l and "stop the visualization server" in l)
        disclosure = index_of(lines, lambda l: "state what they are consenting to" in l)
        self.assertNotEqual(-1, gate, "the teardown gate moved — retarget this test")
        self.assertNotEqual(-1, disclosure, "the consent disclosure must be present")
        self.assertLess(
            disclosure, gate,
            "the consent disclosure must precede the teardown gate — the consent authorizes "
            "an irreversible teardown, so a disclosure after the answer is worth nothing",
        )

    def test_bootcamp_preparation_step_3_still_models_the_pattern(self):
        """The one site that always had it right — keep it as the reference example."""
        lines = PREP.read_text(encoding="utf-8").splitlines()
        q = index_of(lines, lambda l: POINTER in l and "How much detail" in l)
        r = index_of(lines, lambda l: "tell them the choice is not permanent" in l)
        self.assertNotEqual(-1, q)
        self.assertNotEqual(-1, r)
        self.assertLess(r, q)


if __name__ == "__main__":
    unittest.main()
