"""Guidance that attributes loaded data names synthesized data the bootcamp's (#694).

``module-07-query-visualize-discover/phase2-discover.md`` states a general rule: when a
loaded source records ``provenance: synthesized``, the data is the bootcamp's, not the
Bootcamper's -- say "the data the bootcamp generated", never "your data". It ships today
and no registered invariant states it; it cites **INV-239**, which governs what
bootcamp-generated source data must CONTAIN and says nothing about how the guide names
whose data it is. The rule's own `DEFERRED INVARIANT` block is in this run's
``specs/IMPLEMENTED.md`` entry, awaiting the maintainer's sign-off.

⚠️ **Scope, measured rather than taken from the issue's wording.** Acceptance criterion 4
asks for a guard over "steps that branch on ``provenance: synthesized``". Measured over the
shipped subtree: **13** blocks branch on it and only **2** say anything about whose data it
is. The other 11 are Module 4 and Module 5 steps about *regenerating* synthesized data,
which this rule has nothing to say about -- so requiring the attribution at all 13 would
report 11 correct sentences, and a guard that reports correct prose is one its reader learns
to discount (INV-282).

So the site set is: a block that branches on ``provenance: synthesized`` **and** attributes
the loaded data to someone. Each such block must name the data the bootcamp's.

⚠️ This asserts what the shipped text SAYS. It **cannot** establish that a live turn uses
the wording -- only ``dry-run`` phase 3 observes that (INV-308).
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks, line_of

#: A step branching on the provenance value the rule is about.
_SYNTHESIZED = re.compile(r"provenance:?\s*`?synthesized")

#: The block says whose data it is. Without this the sweep reaches the 11 regeneration
#: steps, which attribute nothing.
_ATTRIBUTES = re.compile(
    r"(?i)\byour data\b|\bthe Bootcamper's data\b|data the bootcamp generated|the data is the bootcamp")

#: What such a block must carry: the data named as the bootcamp's.
#:
#: ⚠️ A bare "generated data" is deliberately NOT accepted. Both shipped sites say it for a
#: different reason -- naming a defect in the data -- several sentences after the attribution,
#: so accepting it let a block pass with the attribution removed. The control caught that: it
#: mutated the rule away and the guard still reported nothing.
_NAMES_THE_BOOTCAMP = re.compile(
    r"(?i)data the bootcamp generated|the data is the bootcamp")


def sites(paths):
    """``(path, line, flat)`` for every block that branches on synthesized AND attributes."""
    found = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "synthesized" not in text:
            continue
        for flat, origin in collapsed_blocks(text):
            hit = _SYNTHESIZED.search(flat)
            if hit and _ATTRIBUTES.search(flat):
                found.append((path, line_of(origin, hit.start()), flat))
    return found


def offenders(paths):
    return [(p, n) for p, n, flat in sites(paths) if not _NAMES_THE_BOOTCAMP.search(flat)]


class SynthesizedDataIsNamedTheBootcampsWhereverDataIsAttributed(unittest.TestCase):
    def setUp(self):
        self.shipped = corpus_files("plugins", suffixes=(".md",))

    def test_the_sweep_finds_the_sites_it_is_written_for(self):
        """⛔ (INV-265) A floor: an empty match must not read as a clean result."""
        found = sites(self.shipped)
        self.assertGreaterEqual(
            len(found), 2,
            "the sweep found %d attributing blocks; it is written for at least the general "
            "rule and its narrow sibling, so a smaller number means the scan broke" % len(found))
        names = {p.name for p, _, _ in found}
        self.assertIn("phase2-discover.md", names)

    def test_the_sweep_is_narrower_than_every_synthesized_branch(self):
        """The measurement that set the scope, pinned so a later widening is deliberate."""
        branching = 0
        for path in self.shipped:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "synthesized" not in text:
                continue
            branching += sum(1 for flat, _ in collapsed_blocks(text) if _SYNTHESIZED.search(flat))
        attributing = len(sites(self.shipped))
        self.assertLess(
            attributing, branching,
            "every block branching on provenance: synthesized now attributes data; if that is "
            "real the scope note in this file's docstring needs rewriting, not the assertion")

    def test_no_attributing_block_leaves_the_data_the_bootcampers(self):
        found = offenders(self.shipped)
        self.assertEqual(
            [], found,
            "shipped guidance attributes loaded data without naming synthesized data the "
            "bootcamp's:\n" + "\n".join("  %s:%d" % (p, n) for p, n in found))


class TheControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs the SAME function over mutated shipped text."""

    def setUp(self):
        self.path = (Path(__file__).resolve().parent.parent / "plugins" / "senzing-bootcamp"
                     / "skills" / "module-07-query-visualize-discover" / "phase2-discover.md")

    def _reported(self, text):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d) / "phase2-discover.md"
            tmp.write_text(text, encoding="utf-8")
            return offenders([tmp])

    def test_dropping_the_attribution_is_reported(self):
        """The defect this guard exists for: the rule's own site, attribution removed."""
        text = self.path.read_text(encoding="utf-8")
        stripped = text.replace(
            'the data is the\n   bootcamp\'s, not the Bootcamper\'s.** Say "the data the bootcamp '
            'generated", never "your data".',
            "this is your data.**", 1)
        self.assertNotEqual(stripped, text, "the rule's wording was not found to mutate")
        self.assertTrue(
            self._reported(stripped),
            "dropping the attribution is not reported; the control is vacuous")

    def test_the_shipped_text_is_not_reported(self):
        self.assertEqual([], self._reported(self.path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
