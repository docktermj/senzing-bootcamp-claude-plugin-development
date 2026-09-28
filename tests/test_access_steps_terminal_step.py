"""Once `raw_url` and `git clone` have both failed, the example is reported unreachable.

`find_examples` file retrieval and `generate_scaffold` both answer with an ordered
`access_steps` array instead of the file's bytes: fetch `raw_url`, else `git clone`, else an
`inline` step that only a client forwarding undeclared arguments can take (INV-136). On MCP
server 1.37.14, 2026-09-28, step 3's note in both tools ends by telling a schema-validating
client to "report the content as unreachable rather than retrying". The plugin quoted an
older wording of that note ("cannot use this step; prefer fetching raw_url or cloning") and
never said what to do once both routes had failed, so a guide was left to retry, reach for
`inline`, or fill the gap from memory (INV-080). Issue #197.

These tests pin the behavior, not the server's sentence (INV-219):

* `ground-rules.md` states the terminal step once, as a ⛔ line citing INV-160, naming both
  tools, and saying to report the example as unreachable, not to retry, and not to
  reconstruct it from memory;
* no shipped file carries the retired "cannot use this step" wording;
* INV-160 carries the 2026-09-28 dated note that records the unreachable step.

Enforces the 2026-09-28 note on **INV-160**.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"

#: The retired step-3 wording, which the server replaced by 1.37.14 (2026-09-28).
OLD_WORDING = "cannot use this step"

#: The ⛔ lead that states the terminal step, and the paragraph it governs. The paragraph
#: runs to the next ⛔ or the next list item, so a clause moved out of it no longer counts.
TERMINAL_LEAD = re.compile(r"⛔ \*\*[^*]*\bunreachable\b[^*]*\*\*")
PARAGRAPH_END = re.compile(r"⛔|\n\s*- ")


def flat(text):
    return re.sub(r"\s+", " ", text)


def terminal_steps(text):
    """Every ⛔ paragraph whose bold lead says to report something as unreachable."""
    found = []
    for m in TERMINAL_LEAD.finditer(text):
        end = PARAGRAPH_END.search(text, m.end())
        found.append(text[m.start(): end.start() if end else len(text)])
    return found


def inv160(text):
    m = re.search(r"^- \*\*INV-160\*\* —.*$", text, re.MULTILINE)
    return m.group(0) if m else None


class GroundRulesStatesTheTerminalStep(unittest.TestCase):
    """Negative-controlled by deleting the ⛔ paragraph, and by dropping each clause."""

    @classmethod
    def setUpClass(cls):
        cls.steps = terminal_steps(GROUND_RULES.read_text(encoding="utf-8"))

    def step(self):
        self.assertEqual(
            1, len(self.steps),
            "ground-rules.md must state the access_steps terminal step exactly once, as a ⛔ "
            "line whose bold lead says to report the example as unreachable; found %d"
            % len(self.steps),
        )
        return flat(self.steps[0])

    def test_it_is_a_hard_rule_citing_inv_160(self):
        lead = TERMINAL_LEAD.search(self.step()).group(0)
        self.assertIn("(INV-160)", lead)
        self.assertRegex(lead, r"`raw_url`.*`git clone`.*both failed")

    def test_it_covers_both_tools(self):
        step = self.step()
        for tool in ("find_examples", "generate_scaffold"):
            with self.subTest(tool=tool):
                self.assertIn(f"`{tool}`", step)

    def test_it_names_the_file_and_what_was_tried(self):
        step = self.step()
        self.assertRegex(step, r"(?i)which example could not be reached")
        self.assertRegex(step, r"(?i)what was tried")

    def test_it_forbids_retrying_and_inline(self):
        step = self.step()
        self.assertRegex(step, r"(?i)do not retry either step")
        self.assertRegex(step, r"(?i)do not pass `inline`, which neither schema declares")

    def test_it_forbids_reconstructing_from_memory(self):
        self.assertRegex(self.step(), r"(?i)never reconstruct[^.]*from memory")

    def test_the_calling_step_keeps_its_own_fallback(self):
        self.assertRegex(self.step(), r"(?i)continues on its own fallback")


class TheRetiredWordingIsGone(unittest.TestCase):
    """Negative-controlled by restoring the old quote to ground-rules.md."""

    def test_no_shipped_file_quotes_the_old_step_3_note(self):
        offenders = []
        for path in sorted(PLUGIN.rglob("*")):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if OLD_WORDING in flat(text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            [], offenders,
            "these shipped files quote the step-3 note the server has reworded; quote the "
            "current wording, dated, or none (INV-160's 2026-09-28 note)",
        )


class Inv160RecordsTheUnreachableStep(unittest.TestCase):
    """Negative-controlled by deleting the 2026-09-28 note from INV-160."""

    def test_the_dated_note_names_the_unreachable_step(self):
        body = inv160(INVARIANTS.read_text(encoding="utf-8"))
        self.assertIsNotNone(body, "INV-160 is missing from specs/INVARIANTS.md")
        m = re.search(r"Dated note, 2026-09-28.*?(?=\(Source:|$)", body)
        self.assertIsNotNone(m, "INV-160 carries no 2026-09-28 dated note")
        note = m.group(0)
        self.assertRegex(note, r"MUST report the example as unreachable")
        self.assertRegex(note, r"MUST NOT retry either step")
        self.assertIn("`find_examples`", note)
        self.assertIn("`generate_scaffold`", note)


if __name__ == "__main__":
    unittest.main()
