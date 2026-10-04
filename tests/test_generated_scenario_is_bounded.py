"""A generated scenario has a default size ceiling, and going over it costs a warning.

Module 1's Business Case Offer validated a generated scenario's **shape** — category,
source count, cross-source mapping divergence, quality variation — and never its **size**.
On 2026-08-25 a Bootcamper was offered a 3-source, ~7,081-record scenario, said it "doesn't
seem enough", and was given a 5-source **~93,999-record** scenario with no statement that
loading and resolving it would take substantially longer.

⛔ **The cost is not paid where the choice is made.** Module 1 generates; Data collection,
Data processing and Query/Visualize/Discover absorb the volume. By the time the wait is
visible the decision is many steps behind and expensive to reverse, and the Bootcamper who
made it was never told there was a trade-off.

⚠️ **The ceiling is a default, not a cap.** The Bootcamper's own words were *"keep it at 10k
max if they go over send them a warning just that it will take them longer"* — so the larger
scenario is still generated. The point is that it is chosen rather than drifted into. That
is why this guard checks for the warning **and** for the absence of a refusal.

⚠️ **Two things are asserted absent on purpose.** No wall-clock figure, because load time
depends on the workstation, database and language that Module 1 does not know — a number
invented here is one the run contradicts. And no licensing tie, because nothing has measured
the license at this point and INV-093 forbids a license prompt in Module 1; the ceiling is
about bootcamp duration, which is knowable, not capacity, which is not.

⚠️ What this does NOT establish: that a live run honors the ceiling. That is a runtime
property of a conversational step, which no offline suite can assert (INV-108) — it needs a
`dry-run` phase-3 walk through Module 1's generated-scenario path.

Enforces **INV-277** — a step that GENERATES a dataset or scenario bounds its default size and states the downstream
time cost before generating anything larger; the bound is a default, never a gate.

Source spec: `specs/scenario-generation-has-no-size-cap-or-load-time-warning.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins"
#: A wall-clock claim the step cannot know. Matched near a load/scenario word so the many
#: legitimate timeouts elsewhere in the corpus are not flagged.
WALL_CLOCK = re.compile(
    r"\b\d+\s*(?:-|\s)?(?:minute|min|hour|hr)s?\b[^.\n]{0,80}\b(?:load|scenario|generat)|"
    r"\b(?:load|scenario|generat)[^.\n]{0,80}\b\d+\s*(?:-|\s)?(?:minute|min|hour|hr)s?\b",
    re.I)


def flatten(text):
    return re.sub(r"\s+", " ", text).lower()


def scenario_files():
    """Shipped files that generate a business-case scenario — derived, not hardcoded.

    INV-246: a second generation path added later must satisfy this too, and a guard
    naming one file could not notice it.
    """
    out = []
    for p in sorted(PLUGIN.rglob("*.md")):
        if "__pycache__" in p.parts:
            continue
        flat = flatten(p.read_text(encoding="utf-8"))
        if "business case offer" in flat and "generate a complete scenario" in flat:
            out.append(p)
    return out


class EveryScenarioGeneratorIsBounded(unittest.TestCase):
    def test_a_generation_site_is_found(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        self.assertTrue(
            scenario_files(),
            "no shipped file generates a business-case scenario any more; the scan broke or "
            "the vocabulary moved. Re-derive it rather than deleting this guard")

    def test_each_generation_site_states_a_default_ceiling(self):
        bad = []
        for p in scenario_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            if "10,000 records" not in flat and "10000 records" not in flat:
                bad.append(str(p.relative_to(REPO_ROOT)))
        self.assertEqual(
            [], bad,
            "a scenario-generation site states no default size ceiling, so an unbounded "
            "scenario is the default rather than a choice:\n  " + "\n  ".join(bad))

    def test_going_over_the_ceiling_costs_a_warning_naming_the_modules(self):
        for p in scenario_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("noticeably longer", flat,
                              "no time-cost statement for an over-ceiling scenario")
                self.assertIn("data collection", flat,
                              "the warning does not name a module that absorbs the cost")
                self.assertIn("data processing", flat,
                              "the warning does not name a module that absorbs the cost")

    def test_the_warning_is_not_a_gate(self):
        """⛔ The Bootcamper's choice stands — they are owed the trade-off, not a refusal."""
        for p in scenario_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertRegex(
                    flat, r"statement, not a 👉 question|then generate what they asked for",
                    "the ceiling reads as a gate rather than a default; INV-006 forbids "
                    "re-asking a settled choice and INV-251 caps a turn at one 👉 question")

    def test_no_wall_clock_figure_is_stated(self):
        """A minutes/hours figure invented here is one the run contradicts."""
        bad = []
        for p in scenario_files():
            # Matched across line wraps (#424): "30\nminutes" or a figure whose load word is
            # on the next line was invisible to a line-at-a-time read.
            text = p.read_text(encoding="utf-8")
            lines = text.split("\n")
            for n in match_lines(text, WALL_CLOCK):
                bad.append(f"{p.relative_to(REPO_ROOT)}:{n}  {lines[n - 1].strip()[:90]}")
        self.assertEqual(
            [], bad,
            "a scenario-generation site states a wall-clock load figure it cannot know — "
            "load time depends on the workstation, database and language:\n  "
            + "\n  ".join(bad))

    def test_the_ceiling_is_not_tied_to_the_license(self):
        """INV-093 — nothing has measured the license, and Module 1 asks nothing about it."""
        for p in scenario_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            i = flat.find("size the generated scenario")
            self.assertNotEqual(-1, i, "the ceiling bullet is gone")
            window = flat[i:i + 1400]
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("inv-093", window,
                              "the ceiling bullet does not cite INV-093, so a later editor "
                              "cannot see why capacity is deliberately out of scope here")
                self.assertRegex(
                    window, r"do not tie the ceiling to the license",
                    "the ceiling must say plainly that it is about duration, not capacity")

    def test_a_wrapped_figure_is_caught_at_its_first_line(self):
        """Negative control (#424): "about 30" ends line 1 and "minutes" begins line 2."""
        wrapped = "Generating it and running the load takes about 30\nminutes on a laptop.\n"
        self.assertEqual([1], match_lines(wrapped, WALL_CLOCK))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(WALL_CLOCK.search(l) for l in wrapped.split("\n")))

    def test_the_scan_is_not_vacuous(self):
        """⛔ INV-265 — prove the matchers still detect what they exist for."""
        self.assertTrue(WALL_CLOCK.search("the load will take about 30 minutes"),
                        "the wall-clock matcher no longer detects a figure")
        self.assertFalse(WALL_CLOCK.search("enforce a 120-second timeout for all build commands"),
                         "the wall-clock matcher flags an unrelated timeout, which would push "
                         "an editor into deleting a correct instruction")


if __name__ == "__main__":
    unittest.main()
