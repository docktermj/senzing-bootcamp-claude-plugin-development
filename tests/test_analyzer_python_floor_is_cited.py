"""Module 5's analyzer gate says where the mapping scripts run and which Python the analyzer needs.

`sz_json_analyzer.py`, the primary validator `mapping_workflow` delivers, uses a `match`
statement, so it does not parse on Python 3.9. On a 2026-10-05 run (macOS, whose system
`python3` is 3.9) the gate ran it on the host and the Bootcamper's first sight of it was a
`SyntaxError` in Senzing-provided code, which reads as a broken download. The gate said which
scripts to run and how to degrade, but not where, or with which interpreter (#462).

This guard pins the two pieces the fix added, following
`tests/test_verbatim_check_limitations_freshness.py`:

* **The gate** (`> **Availability-aware mapping validation:**`) states that all four scripts run
  where the SDK runs (container on `docker`, host on a native route); the analyzer's floor and that
  the other three carry none; a `python3 --version` check before the analyzer's first run; one
  pinned 👉 offer to install when it is below 3.10; and the decline path (skip, say why, record,
  continue, never re-ask in the session, INV-006).
* **The ⛔ entry directly after the gate** records the floor with its evidence (the `match`
  statement and its line), the server version and the date (INV-080), and says to update or remove
  it when upstream lowers or documents a different floor.

⚠️ **The measurement this pins, so a reader can repeat it.** `download_resource(filenames=
['sz_json_analyzer.py'])` on server 1.37.26, 2026-10-09, delivered a 72,786-byte script whose line
370 is `match family:`; `py_compile` failed under Python 3.9.25 at that line and passed under
3.10.19. `sz_schema_generator.py`, `sz_verbatim_check.py` and `sz_routing_report.py` compiled under
3.8.20 and 3.9.25. The script's docstring now says "Requires Python 3.10 or newer" (it did not on
1.37.19, 2026-10-05, when the `match` sat at line 367). A re-measurement that moves any of these is
an edit to the entry AND to the constants below, together.

⛔ **(INV-346) Every phrase is matched on collapsed text**: blockquote markers stripped and every
run of whitespace made one space, so a phrase wrapped across lines still matches.

Each check is a function over the file's text, so the negative controls at the bottom run the
same predicate against a copy with the pinned part removed or changed and confirm it fails.

Source issue: #462.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE2 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping" / "phase2-data-mapping.md")

#: The measured facts. Changing one means re-measuring, then editing the entry and this together.
FLOOR = "3.10"
SERVER = "1.37.26"
MEASURED_ON = "2026-10-09"
EVIDENCE_LINE = "370"
OTHER_THREE = ("sz_schema_generator.py", "sz_verbatim_check.py", "sz_routing_report.py")

GATE_START = "> **Availability-aware mapping validation:**"
ENTRY_START = "⛔ **(INV-080) `sz_json_analyzer.py` needs Python 3.10 or newer"
NEXT_BLOCK = "⛔ **The verbatim check harvests source *values* only"
GATE_CLOSING = "> In short: check the analyzer's Python first"


def squash(text):
    return re.sub(r"\s+", " ", re.sub(r"(?m)^[ \t]*>[ \t]?", "", text)).strip()


def regions(text):
    """(gate, between, entry) as raw text, or None when a locator is missing."""
    g = text.find(GATE_START)
    e = text.find(ENTRY_START, g if g >= 0 else 0)
    n = text.find(NEXT_BLOCK, e if e >= 0 else 0)
    if min(g, e, n) < 0:
        return None
    # The gate is a run of blockquotes: the 👉 question stands in a quote of its own, so the
    # gate's numbered scripts are not read as that question's options (INV-211). Its closing
    # "In short" paragraph ends it; anything from there to the entry stands between them.
    closing = text.find(GATE_CLOSING, g)
    gate_end = text.find("\n\n", closing) if closing >= 0 else -1
    if gate_end < 0 or gate_end > e:
        return None
    return text[g:gate_end], text[gate_end:e], text[e:n]


def gate_problems(text):
    """Every acceptance criterion the gate fails, as messages (empty when it passes)."""
    found = regions(text)
    if found is None:
        return ["the gate or the floor entry was not found"]
    gate = squash(found[0])
    out = []
    for script in ("sz_json_analyzer.py",) + OTHER_THREE:
        if script not in gate:
            out.append("the gate does not name %s among the scripts it places" % script)
    if not re.search(r"All four scripts `mapping_workflow` delivers", gate):
        out.append("the gate does not say the placement covers all four scripts")
    if not re.search(r"run where the bootcamp's SDK runs: \*\*inside the container on the "
                     r"`docker` route, on the host on a native route\*\*", gate):
        out.append("the gate does not say where the scripts run on each route")
    if not re.search(r"\*\*`sz_json_analyzer\.py` needs Python 3\.10 or newer; the other three "
                     r"carry no measured floor\*\*", gate):
        out.append("the gate does not state the analyzer's floor and that the others have none")
    if not re.search(r"whatever language the Bootcamper chose", gate):
        out.append("the gate does not say the scripts are Python tools in every language")
    check = gate.find("Check the analyzer's Python before its first run")
    item1 = gate.find("1. **`sz_json_analyzer.py` (primary validation):**")
    if check < 0:
        out.append("the gate has no version check before the analyzer's first run")
    elif item1 < 0 or check > item1:
        out.append("the version check does not come before the analyzer's run instruction")
    if not re.search(r"Run `python3 --version` where the analyzer will run: inside the container "
                     r"on the `docker` route .{0,120}on the host on a native route", gate):
        out.append("the check does not run `python3 --version` where the analyzer runs")
    if "run the check rather than assume it" not in gate:
        out.append("the docker route's check may be assumed rather than run")
    if not re.search(r"On Windows the command name is `python3` too", gate):
        out.append("the check does not name the Windows command")
    if not re.search(r"a bare `SyntaxError` is never the first thing the Bootcamper sees", gate):
        out.append("the gate does not rule out a bare SyntaxError as the first sight")
    questions = re.findall(r"👉 \*\*(.*?)\*\*", gate)
    if len(questions) != 1:
        out.append("the gate should pin exactly one 👉 question, found %d" % len(questions))
    elif not (re.search(r"needs Python 3\.10 or newer", questions[0])
              and re.search(r"install a newer Python", questions[0])):
        out.append("the pinned question does not state the floor and offer the install")
    if "(respond yes or no)" not in gate:
        out.append("the pinned question has no yes/no answer hint (INV-008)")
    if not re.search(r"end the turn on this one question", gate):
        out.append("the gate does not end the turn on the question")
    if not re.search(r"alongside the existing `python3`, never replacing it", gate):
        out.append("the install path may replace the system python3")
    if not re.search(r"If the install fails, take the \*\*no\*\* path", gate):
        out.append("a failed install has no handling")
    no_path = [
        (r"tell the Bootcamper the analyzer is being skipped because the Python here is older "
         r"than 3\.10", "the no path does not say why the analyzer is skipped"),
        (r"record the skip and its reason in the source's mapping notes",
         "the no path does not record the skip"),
        (r"continue with items 2 and 3 below under their optional/best-effort handling",
         "the no path does not continue with the remaining checks"),
        (r"do not ask again \(INV-006\)", "the no path may re-ask the question"),
        (r"step 14's `analyze_record` run", "the skip does not cover step 14's analyzer run"),
        (r"names the analyzer as a check that did not run \(INV-163\)",
         "the closing summary does not name the skipped check"),
        (r"Once the check has passed, a `SyntaxError` from the analyzer is not the version floor",
         "a post-check SyntaxError may be misread as the version floor"),
    ]
    for pattern, message in no_path:
        if not re.search(pattern, gate):
            out.append(message)
    return out


def entry_problems(text):
    """Every way the ⛔ floor entry fails its criteria, as messages (empty when it passes)."""
    found = regions(text)
    if found is None:
        return ["the gate or the floor entry was not found"]
    _gate, between, raw_entry = found
    out = []
    if between.strip():
        out.append("the floor entry is not directly after the gate: %r stands between"
                   % squash(between)[:80])
    entry = squash(raw_entry)
    head = "needs Python %s or newer: measured on server %s, %s" % (FLOOR, SERVER, MEASURED_ON)
    if head not in entry:
        out.append("the entry's floor, server version or date is missing or changed")
    if "download_resource(filenames=['sz_json_analyzer.py'])" not in entry:
        out.append("the entry does not name the route that measures the floor")
    if not re.search(r"answers with a listing, not the script", entry):
        out.append("the entry does not say the route answers with a listing (INV-234)")
    if not re.search(r"\*\*line %s is a `match` statement\*\* \(`match family:`\)"
                     % EVIDENCE_LINE, entry):
        out.append("the entry does not cite the match statement and its line")
    if not re.search(r"fails under Python 3\.9\.25 .{0,60}and passes under 3\.10\.19", entry):
        out.append("the entry does not record both sides of the measurement")
    for script in OTHER_THREE:
        if script not in entry:
            out.append("the entry does not say %s was measured" % script)
    if "so no floor is stated for them" not in entry:
        out.append("the entry does not say the other three carry no floor")
    if not re.search(r"First measured on server 1\.37\.19, 2026-10-05", entry):
        out.append("the entry lost the first measurement")
    if not re.search(r"upstream now documents the floor", entry):
        out.append("the entry does not record that upstream documents the floor")
    if not re.search(r"\*\*If upstream lowers the floor, or documents a different one, update or "
                     r"remove this entry and the gate's check with it\*\*", entry):
        out.append("the entry does not say when to update or remove it")
    if "INV-080" not in entry:
        out.append("the entry does not cite INV-080 at its line")
    return out


class TheRegionsAreLocatable(unittest.TestCase):
    def test_the_file_exists(self):
        self.assertTrue(PHASE2.is_file(), "phase2-data-mapping.md moved")

    def test_gate_and_entry_are_found(self):
        self.assertIsNotNone(regions(PHASE2.read_text(encoding="utf-8")),
                             "the gate, the floor entry or the verbatim block was not found")


class TheGateStatesWhereAndWithWhichPython(unittest.TestCase):
    def test_every_gate_criterion_holds(self):
        problems = gate_problems(PHASE2.read_text(encoding="utf-8"))
        self.assertEqual([], problems, "; ".join(problems))


class TheFloorIsCitedDirectlyAfterTheGate(unittest.TestCase):
    def test_every_entry_criterion_holds(self):
        problems = entry_problems(PHASE2.read_text(encoding="utf-8"))
        self.assertEqual([], problems, "; ".join(problems))

    def test_gate_and_entry_state_the_same_floor(self):
        gate, _between, entry = regions(PHASE2.read_text(encoding="utf-8"))
        floors = set(re.findall(r"Python (\d+\.\d+) or newer", squash(gate) + squash(entry)))
        self.assertEqual({FLOOR}, floors, "the gate and the entry disagree on the floor")


class NegativeControls(unittest.TestCase):
    """The predicates fail on text that lacks what they pin."""

    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")

    def test_without_the_entry_the_locator_fails(self):
        start = self.text.index(ENTRY_START)
        end = self.text.index(NEXT_BLOCK)
        cut = self.text[:start] + self.text[end:]
        self.assertTrue(entry_problems(cut))
        self.assertTrue(gate_problems(cut))

    def test_a_changed_server_version_or_date_fails(self):
        for old, new in ((SERVER, "1.37.19"), (MEASURED_ON, "2026-10-05"),
                         ("Python 3.10 or newer: measured", "Python 3.9 or newer: measured")):
            with self.subTest(changed=old):
                start = self.text.index(ENTRY_START)
                mutated = self.text[:start] + self.text[start:].replace(old, new, 1)
                self.assertTrue(entry_problems(mutated))

    def test_the_evidence_line_is_pinned(self):
        mutated = self.text.replace("**line 370 is a", "**line 999 is a", 1)
        self.assertTrue(entry_problems(mutated))

    def test_text_between_gate_and_entry_fails(self):
        start = self.text.index(ENTRY_START)
        mutated = self.text[:start] + "An interloper paragraph.\n\n" + self.text[start:]
        self.assertIn("directly after the gate", " ".join(entry_problems(mutated)))

    def test_without_the_check_the_gate_fails(self):
        mutated = self.text.replace("Check the analyzer's Python before its first run", "", 1)
        self.assertTrue(gate_problems(mutated))

    def test_a_second_question_fails(self):
        g = self.text.index(GATE_START)
        anchor = self.text.index("> 1. **`sz_json_analyzer.py` (primary validation):**", g)
        mutated = (self.text[:anchor] + "> 👉 **Shall I also re-run the profiler?**\n>\n"
                   + self.text[anchor:])
        self.assertIn("exactly one 👉 question", " ".join(gate_problems(mutated)))

    def test_without_the_no_re_ask_rule_the_gate_fails(self):
        mutated = self.text.replace("do not ask again (INV-006)", "ask again next source", 1)
        self.assertIn("may re-ask", " ".join(gate_problems(mutated)))

    def test_the_pre_change_gate_fails(self):
        """The gate as it shipped before #462: no placement, no floor, no check, no entry."""
        start = self.text.index("> **Where the scripts run, and with which Python.**")
        end = self.text.index("> 1. **`sz_json_analyzer.py` (primary validation):**")
        old = self.text[:start] + self.text[end:]
        old = old[:old.index(ENTRY_START)] + old[old.index(NEXT_BLOCK):]
        self.assertGreaterEqual(len(gate_problems(old)), 1)
        self.assertGreaterEqual(len(entry_problems(old)), 1)


if __name__ == "__main__":
    unittest.main()
