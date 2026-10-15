"""Module 7 step 2's working rules sit beside its action, before the flag guidance.

The governing rule must be findable at the moment of use. In `phase1-query-visualize.md`,
step 2's scaffold call and save path came first, and "CRITICAL, file placement", the
iterate-over-records rule and the record-key fold came about 270 lines later, after the
whole flag reconciliation. A guide reached the action before the constraints that govern
it (#611).

This checks the order: the save path, then the scaffold call, then file placement,
iteration and the fold, and only then the flag sub-section, all before step 2's checkpoint.
It also checks that the flag guidance is still there in full, so the move cannot pass by
deleting it.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE1 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-07-query-visualize-discover" / "phase1-query-visualize.md")

STEP_2 = "## 2. Create query programs"
STEP_3 = "## 3. Run exploratory queries"

#: In the order a guide must meet them.
ORDER = (
    ("save path", "save it as the program\n`[query_name]` in `src/query`"),
    ("scaffold call", "Use `generate_scaffold` with `workflow='query'`"),
    ("file placement", "**CRITICAL, file placement:**"),
    ("iteration", "**Iterate over records, not entity IDs.**"),
    ("record-key fold", "One file row is NOT one record: fold on `(data_source, record_id)`"),
    ("flag sub-section", "### Flags and response shapes for the query programs"),
    ("flag guidance", "**Flags:** when generated query code calls SDK methods"),
    ("checkpoint", "**Checkpoint:** write step 2."),
)

#: Paragraph heads that belong to the flag sub-section and must still be in it.
FLAG_GUIDANCE = (
    "⛔ **(INV-169) Do NOT restrict this flag",
    "⚠️ **The server cautions that DEFAULT composites are not for production code",
    "⛔ **A method's own default-flags composite is NOT `SZ_ENTITY_DEFAULT_FLAGS`",
    "⛔ **(INV-268) Confirm a composite's *representation*",
    "⛔ **Response shapes (INV-115).**",
    "**Defensive parsing.**",
    "⛔ **This whole class fails silently",
)


def step_2():
    text = PHASE1.read_text(encoding="utf-8")
    start = text.index(STEP_2)
    return text[start:text.index(STEP_3, start)]


class StepTwoRulesComeBeforeTheFlagGuidance(unittest.TestCase):
    def test_each_marker_is_in_step_2_once(self):
        body = step_2()
        for name, marker in ORDER:
            with self.subTest(marker=name):
                self.assertEqual(1, body.count(marker),
                                 "%s is missing from step 2, or appears twice" % name)

    def test_the_markers_appear_in_order(self):
        body = step_2()
        positions = [(name, body.index(marker)) for name, marker in ORDER]
        for (before, at_before), (after, at_after) in zip(positions, positions[1:]):
            with self.subTest(pair="%s before %s" % (before, after)):
                self.assertLess(at_before, at_after,
                                "%s must come before %s in step 2" % (before, after))

    def test_nothing_but_the_working_rules_sits_between_the_scaffold_call_and_the_fold(self):
        """The flag guidance must not drift back between the action and its rules."""
        body = step_2()
        span = body[body.index("Use `generate_scaffold` with `workflow='query'`"):
                    body.index("### Flags and response shapes for the query programs")]
        self.assertNotIn("**Flags:**", span)
        self.assertNotIn("composite_members", span)

    def test_the_flag_guidance_is_kept_in_the_sub_section(self):
        """Moving it must not cut it ("Never cut rationale")."""
        body = step_2()
        sub = body[body.index("### Flags and response shapes for the query programs"):]
        for head in FLAG_GUIDANCE:
            with self.subTest(head=head[:40]):
                self.assertIn(head, sub)


if __name__ == "__main__":
    unittest.main()
