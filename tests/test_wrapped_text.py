"""The shared wrap-aware matcher, `tests/_wrapped_text.py`, reads Markdown blocks as #426 defines.

`match_lines(text, pattern)` returns the 1-based line where each match starts. These tests pin
each acceptance case of #426: a wrapped match is found at its start line; every block boundary
(blank line, fence line, table row, heading, front matter) stops a phrase; a pattern that could
cross a boundary matches only within one block; blockquote markers are stripped; indented and
`~~~` fences are fences; a `#` line inside a fence is content; two matches are reported at their
own lines, in order.

⚠️ Each "not matched across a boundary" test has a positive twin with the boundary removed, so a
matcher that matched nothing at all would fail here rather than pass every negative.

Stdlib only (INV-108).

Source issue: #426.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest

from _wrapped_text import match_lines

PHRASE = re.compile(r"no flag is documented")


class AWrappedMatchIsFoundAtItsStart(unittest.TestCase):
    def test_a_match_wrapped_across_two_lines_is_reported_at_its_start_line(self):
        self.assertEqual([2], match_lines("intro line\nsays no flag\nis documented here.", PHRASE))

    def test_a_match_at_the_start_of_a_block_is_reported_at_its_first_non_blank_line(self):
        self.assertEqual([3], match_lines("before\n\n   no flag is\ndocumented.", PHRASE))

    def test_two_matches_are_reported_at_their_own_lines_in_order(self):
        text = "a no flag is\ndocumented b\n\nc\nd no flag is documented e"
        self.assertEqual([1, 5], match_lines(text, PHRASE))

    def test_two_matches_in_one_block_are_both_reported(self):
        text = "no flag is documented, and\nagain no flag\nis documented."
        self.assertEqual([1, 2], match_lines(text, PHRASE))

    def test_no_match_is_an_empty_list(self):
        self.assertEqual([], match_lines("nothing to see\nhere", PHRASE))

    def test_carriage_returns_are_whitespace(self):
        self.assertEqual([1], match_lines("no flag\r\nis documented\r\n", PHRASE))


class ABlockBoundaryStopsAPhrase(unittest.TestCase):
    """Each boundary, with its control: the same phrase without the boundary matches."""

    def assert_split_only_by(self, joined, split):
        self.assertEqual([1], match_lines(joined, PHRASE), "control: the joined text matches")
        self.assertEqual([], match_lines(split, PHRASE))

    def test_a_blank_line(self):
        self.assert_split_only_by("no flag\nis documented", "no flag\n\nis documented")

    def test_a_blank_line_holding_only_whitespace(self):
        self.assert_split_only_by("no flag\nis documented", "no flag\n   \t\nis documented")

    def test_a_code_fence_line(self):
        self.assert_split_only_by("no flag\nis documented",
                                  "no flag\n```\nis documented\n```")

    def test_a_fenced_block_never_joins_the_prose_after_it(self):
        self.assertEqual([], match_lines("```\nno flag\n```\nis documented", PHRASE))

    def test_a_table_row_boundary(self):
        self.assert_split_only_by("no flag\nis documented",
                                  "| no flag |\n| is documented |")

    def test_a_table_row_does_not_join_the_prose_before_it(self):
        self.assertEqual([], match_lines("no flag\n| is documented |", PHRASE))

    def test_a_heading_line(self):
        self.assert_split_only_by("no flag\nis documented", "no flag\n## is documented")

    def test_a_heading_is_a_block_of_its_own(self):
        self.assertEqual([], match_lines("## no flag\nis documented", PHRASE))
        self.assertEqual([1], match_lines("## no flag is documented\nmore", PHRASE))

    def test_the_front_matter_boundary(self):
        self.assert_split_only_by("no flag\nis documented",
                                  "---\ntitle: no flag\n---\nis documented")

    def test_the_front_matter_is_matched_inside_itself(self):
        self.assertEqual([2], match_lines("---\nnote: no flag\n  is documented\n---\nbody", PHRASE))

    def test_a_dash_line_after_the_first_line_is_not_front_matter(self):
        """A thematic break is not a boundary by itself; the blank lines around it are."""
        self.assertEqual([1], match_lines("no flag\n---\nis documented", re.compile(
            r"no flag --- is documented")))
        self.assertEqual([], match_lines("intro\n\n---\nno flag\n---\n\nis documented", PHRASE))

    def test_an_unclosed_opening_dash_line_is_not_front_matter(self):
        self.assertEqual([2], match_lines("---\nno flag\nis documented", PHRASE))


class APatternRunsOnOneBlockAtATime(unittest.TestCase):
    def test_a_pattern_that_could_cross_a_boundary_matches_only_within_one_block(self):
        greedy = re.compile(r"a[\s\S]*b")
        self.assertEqual([], match_lines("a\n\nb", greedy))
        self.assertEqual([1], match_lines("a\nb", greedy))
        self.assertEqual([1, 4], match_lines("a b\n\nc\na\nb", greedy))

    def test_anchors_bind_at_block_edges(self):
        anchored = re.compile(r"^no flag is documented$")
        self.assertEqual([3], match_lines("before\n\nno flag is\n  documented  \n\nafter", anchored))
        self.assertEqual([], match_lines("before\nno flag is documented", anchored))


class BlockquoteMarkersAreStripped(unittest.TestCase):
    def test_a_phrase_wrapped_across_two_blockquote_lines_is_matched_at_its_start(self):
        self.assertEqual([2], match_lines("> intro\n> no flag\n> is documented", PHRASE))

    def test_nested_markers_are_stripped(self):
        self.assertEqual([1], match_lines("> > no flag\n> > is documented", PHRASE))

    def test_entering_a_blockquote_is_not_a_boundary(self):
        self.assertEqual([1], match_lines("no flag\n> is documented", PHRASE))

    def test_a_marker_only_line_is_a_blank_line(self):
        self.assertEqual([], match_lines("> no flag\n>\n> is documented", PHRASE))


class FencesAreRecognized(unittest.TestCase):
    def test_a_fence_indented_inside_a_list_item_is_a_fence(self):
        text = "- item says no flag\n   ```bash\n   is documented\n   ```"
        self.assertEqual([], match_lines(text, PHRASE))
        self.assertEqual([1], match_lines("- item says no flag\n   is documented", PHRASE))

    def test_a_tilde_fence_is_a_fence(self):
        self.assertEqual([], match_lines("no flag\n~~~\nis documented\n~~~", PHRASE))

    def test_a_backtick_line_inside_a_tilde_fence_is_content(self):
        text = "~~~\n```\nno flag\nis documented\n```\n~~~"
        self.assertEqual([3], match_lines(text, PHRASE))

    def test_a_hash_line_inside_a_fence_is_not_a_heading(self):
        text = "```bash\nno flag\n# is documented\n```"
        self.assertEqual([2], match_lines(text, re.compile(r"no flag # is documented")))
        self.assertEqual([], match_lines("no flag\n# is documented", re.compile(
            r"no flag # is documented")), "control: outside a fence the line is a heading")

    def test_table_and_dash_lines_inside_a_fence_are_content(self):
        self.assertEqual([2], match_lines("```\nno flag\n| is documented\n```", re.compile(
            r"no flag \| is documented")))
        self.assertEqual([2], match_lines("```\nno flag\n---\n```", re.compile(r"no flag ---")))

    def test_inside_a_fence_a_blank_line_ends_a_block(self):
        self.assertEqual([], match_lines("```\nno flag\n\nis documented\n```", PHRASE))

    def test_prose_after_a_closed_fence_is_matched(self):
        self.assertEqual([4], match_lines("```\ncode\n```\nno flag\nis documented", PHRASE))


class ListItemsJoinIntoOneBlock(unittest.TestCase):
    def test_lines_of_one_list_with_no_blank_line_are_one_block(self):
        """Accepted (#426 edge case): a phrase across two items can match."""
        self.assertEqual([1], match_lines("- no flag\n- is documented", re.compile(
            r"no flag - is documented")))


if __name__ == "__main__":
    unittest.main()
