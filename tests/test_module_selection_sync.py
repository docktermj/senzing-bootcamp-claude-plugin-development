"""Tests for the Core path's module enumeration in Bootcamp preparation.

A Core run is documented as "every module, in order", but the Core branch used to say
only that — leaving the agent to translate eleven display names into eleven state
tokens with no canonical list to copy. That derivation dropped
`entity_resolution_concepts`, so the primer never ran and nothing told the bootcamper a
module had been skipped (INV-014 permits only *requested* skips).

`bootcamp-preparation/SKILL.md` is the single source of truth for the list — no other
skill enumerates it — so these tests pin it there:

* The module table carries a State token for every module, and those tokens are exactly
  the ones the Core list writes.
* The Core branch enumerates all eleven tokens, in module order, including all three
  deselectable ones.
* Nothing reintroduces "present only if selected" phrasing that reads as
  exclude-by-default for a module Core always includes.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills", "bootcamp-preparation", "SKILL.md"
)

# Module order is the bootcamp's order (INV-013/INV-076); the tokens are what
# `selected_modules` and `modules_completed` carry.
EXPECTED_ORDER = [
    "bootcamp_preparation",
    "entity_resolution_concepts",
    "business_problem",
    "sdk_setup",
    "system_verification",
    "truthset_visualization",
    "data_collection",
    "data_quality_mapping",
    "data_processing",
    "query_visualize_discover",
    "graduation",
]

# The three modules Customized may drop. Core includes all of them.
DESELECTABLE = ("entity_resolution_concepts", "system_verification", "truthset_visualization")


def skill_text():
    with open(SKILL, encoding="utf-8") as handle:
        return handle.read()


def core_branch_tokens(text):
    """The ordered tokens in the Core branch's `selected_modules` block (Step 1)."""
    start = text.index("## 1. Choose the bootcamp path")
    end = text.index("## 2. Select modules")
    block = re.search(r"selected_modules:\n((?:\s*-\s*\w+\n)+)", text[start:end])
    if not block:
        return []
    return re.findall(r"-\s*(\w+)", block.group(1))


def table_tokens(text):
    """State tokens from the module-list table, in row order.

    Line-scoped by design (#424): a table row is one line.
    """
    tokens = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---") or "State token" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4 and cells[0].isdigit():
            tokens.append(cells[3].strip("`"))
    return tokens


class TestModuleTable(unittest.TestCase):
    def test_table_carries_a_state_token_column(self):
        self.assertIn("State token", skill_text(), "the module table must name the token column")

    def test_table_tokens_are_the_expected_modules_in_order(self):
        self.assertEqual(EXPECTED_ORDER, table_tokens(skill_text()))


class TestCorePathEnumeration(unittest.TestCase):
    def setUp(self):
        self.text = skill_text()
        self.tokens = core_branch_tokens(self.text)

    def test_core_branch_enumerates_the_list_literally(self):
        self.assertTrue(
            self.tokens,
            "Step 1's Core branch must contain a literal selected_modules list to copy, "
            "not prose telling the agent to derive one",
        )

    def test_core_includes_every_module_in_order(self):
        self.assertEqual(EXPECTED_ORDER, self.tokens)

    def test_core_includes_all_three_deselectable_modules(self):
        for token in DESELECTABLE:
            with self.subTest(token=token):
                self.assertIn(
                    token, self.tokens, f"Core must include {token} — 'optional' is not 'omitted'"
                )

    def test_core_list_matches_the_table(self):
        """One drifting away from the other is how the original defect became possible."""
        self.assertEqual(table_tokens(self.text), self.tokens)


class TestOptionalWordingIsNotExcludeByDefault(unittest.TestCase):
    def test_no_present_only_if_selected_annotation(self):
        """That phrasing reads as exclude-unless-chosen, which is wrong for Core."""
        self.assertNotIn(
            "present only if selected",
            skill_text(),
            "annotate optional modules as 'always in Core', not as excluded by default",
        )

    def test_core_states_that_optional_modules_are_included(self):
        text = skill_text()
        start = text.index("## 1. Choose the bootcamp path")
        end = text.index("## 2. Select modules")
        self.assertRegex(
            text[start:end],
            r"(?s)Optional.{0,120}(never means Core omits|what Customized may drop)",
            "the Core branch must say explicitly that 'optional' does not mean omitted",
        )


class TestPreHandoffSelfCheck(unittest.TestCase):
    def test_step_six_verifies_the_list_before_handoff(self):
        text = skill_text()
        start = text.index("selected_modules:     # ordered")
        end = text.index("## 7. Recap the setup")
        section = text[start:end]
        self.assertIn("eleven", section, "the self-check must state the Core count")
        self.assertRegex(
            section,
            r"(?i)correct it",
            "the self-check must say to correct a missing module before the handoff",
        )


if __name__ == "__main__":
    unittest.main()
