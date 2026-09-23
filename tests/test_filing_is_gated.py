"""Every surface that INSTRUCTS filing a GitHub issue states the gate beside the instruction.

Filing is the one act in this repository that is both **outward-facing and irreversible**: the
issue is visible the moment it exists, its notifications have gone out, and it can be edited or
closed but never un-filed. Three skills say so in their own words. ⛔ **No invariant registers
it** (#106), so the rule lives as three independent restatements that a later edit can weaken
one at a time with nothing noticing.

This module is the mechanical half. The rule itself is drafted as a `DEFERRED INVARIANT` in
`specs/IMPLEMENTED.md`, because minting an id is the maintainer's alone.

⛔ **The hard half is telling an INSTRUCTION from a PROHIBITION**, and a first scan got it
wrong. Searching for `gh issue create` returns **six** files, and three of them name it only to
forbid the act:

* `.claude/commands/feedback-to-issues.md` — forbids a `--repo` argument;
* `.claude/skills/feedback-to-issues/issue-template.md` — a body template;
* `.claude/skills/unattended-issue-loop/SKILL.md` — ⛔ *"An unattended audit FILES NOTHING."*

A guard that cannot tell them apart demands a gate on the rule that forbids filing, which is the
same "satisfied by something adjacent" defect this repository keeps finding -- committed inside
the guard written to prevent it.

⛔ **The discriminator is the fence.** A `gh issue create` inside a fenced code block is a
command the reader is told to run; one in inline backticks is prose *about* the command.
Measured 2026-09-23: that splits the six **3 and 3**, exactly along the instruction/prohibition
line. `ProhibitionsAreNotInstructions` pins all three negatives.

⚠️ **The gate is required NEAR the instruction, not anywhere in the file.** A file-wide search
would let a gate in one section vouch for an instruction in another -- and two of these files
are long enough for that to happen silently. Measured distances today: 7, 3 and 2 lines, on
both sides of the instruction.

⚠️ **What this does NOT establish:** that a run actually asks, or that a maintainer actually
answered. No offline check reaches conversational behavior; only `dry-run` phase 3 can observe
it. This pins that the instruction is present where a reader will meet it.

Source issue: #106.

Stdlib only; the surfaces are discovered rather than listed (INV-246).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE = REPO_ROOT / ".claude"

#: A fenced block, indented or not. ⛔ `[ \t]*` is load-bearing: two of the three instructions
#: sit inside list items, so their fences are indented and a column-0 pattern missed them --
#: which made the first measurement report those surfaces as ungated.
FENCE = re.compile(r"^[ \t]*```.*?^[ \t]*```", re.M | re.S)

#: The act this rule governs.
FILING = "gh issue create"

#: The gate, matched on the CLAIM rather than one phrasing (INV-282). All three shipped
#: wordings differ -- "get a yes first", "get a yes, before filing", "get a yes, then file".
GATE = re.compile(r"(?i)get a yes")

#: How far from the instruction the gate may sit. Measured 2026-09-23: 7, 3 and 2 lines. The
#: bound is deliberately small -- a file-wide search would let a gate in one section vouch for
#: an instruction in another.
GATE_WINDOW = 25


def surfaces():
    return sorted(CLAUDE.rglob("*.md"))


def instruction_lines(path):
    """Line numbers where `path` tells the reader to RUN `gh issue create`.

    A fenced block is a command to execute; inline backticks are prose about one.
    """
    text = path.read_text(encoding="utf-8")
    return [text[:m.start()].count("\n") + 1
            for m in FENCE.finditer(text) if FILING in m.group(0)]


def gate_lines(path):
    text = path.read_text(encoding="utf-8")
    return [text[:m.start()].count("\n") + 1 for m in GATE.finditer(text)]


def instructing_surfaces():
    return [p for p in surfaces() if instruction_lines(p)]


class TheCorpusIsNotEmpty(unittest.TestCase):
    """INV-265 -- every assertion below is satisfied trivially by an empty set."""

    def test_surfaces_were_found(self):
        self.assertGreaterEqual(len(surfaces()), 10,
                                "fewer than ten markdown surfaces under %s; the glob has drifted"
                                % CLAUDE)

    def test_at_least_three_surfaces_instruct_filing(self):
        found = instructing_surfaces()
        self.assertGreaterEqual(
            len(found), 3,
            "fewer than three surfaces instruct filing (%s). Either the fence pattern has "
            "drifted or the commands stopped filing; either way the gate check below is vacuous"
            % ", ".join(p.name for p in found))


class EveryInstructionCarriesTheGate(unittest.TestCase):
    def test_the_gate_is_stated_beside_each_instruction(self):
        ungated = []
        for p in instructing_surfaces():
            gates = gate_lines(p)
            for line in instruction_lines(p):
                if not any(abs(g - line) <= GATE_WINDOW for g in gates):
                    ungated.append("%s:%d" % (p.relative_to(REPO_ROOT), line))
        self.assertEqual(
            [], ungated,
            "surface(s) instruct running `%s` with no gate within %d lines: %s. Filing is "
            "outward-facing and irreversible -- the issue exists, and its notifications have "
            "gone out, the moment the command runs"
            % (FILING, GATE_WINDOW, ", ".join(ungated)))


class ProhibitionsAreNotInstructions(unittest.TestCase):
    """⛔ The three negatives, pinned beside the positives (INV-282)."""

    #: Each names `gh issue create` only to forbid or template it.
    NEGATIVES = (
        "commands/feedback-to-issues.md",
        "skills/feedback-to-issues/issue-template.md",
        "skills/unattended-issue-loop/SKILL.md",
    )

    def test_none_of_them_is_read_as_instructing(self):
        for rel in self.NEGATIVES:
            p = CLAUDE / rel
            with self.subTest(surface=rel):
                self.assertTrue(p.is_file(), "%s no longer exists; re-derive the negatives" % rel)
                self.assertIn(FILING, p.read_text(encoding="utf-8"),
                              "%s no longer mentions %r, so it exercises nothing" % (rel, FILING))
                self.assertEqual(
                    [], instruction_lines(p),
                    "%s is read as instructing filing. It names `%s` only to forbid or template "
                    "it, and flagging it would demand a gate on the rule that forbids the act"
                    % (rel, FILING))

    def test_the_unattended_loop_still_forbids_filing(self):
        """The complement: if that prohibition goes, this negative stops being a negative."""
        text = (CLAUDE / "skills/unattended-issue-loop/SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(
            text, r"(?i)FILES NOTHING",
            "unattended-issue-loop no longer forbids filing, so its mention of `%s` may now be "
            "an instruction -- and it carries no gate" % FILING)


class TheFenceIsWhatDistinguishes(unittest.TestCase):
    """The discriminator itself, pinned so a later edit cannot quietly widen it."""

    def test_a_fenced_command_is_an_instruction(self):
        self.assertTrue(FENCE.search("```bash\n%s --title x\n```" % FILING))

    def test_an_indented_fence_still_counts(self):
        """Two of the three instructions sit in list items; a column-0 pattern missed them."""
        self.assertTrue(FENCE.search("   ```bash\n   %s --title x\n   ```" % FILING))

    def test_inline_backticks_are_not_an_instruction(self):
        blocks = [m for m in FENCE.finditer("a `%s` mention in prose" % FILING)
                  if FILING in m.group(0)]
        self.assertEqual([], blocks)


if __name__ == "__main__":
    unittest.main()
