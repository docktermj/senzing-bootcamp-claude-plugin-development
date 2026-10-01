"""Every `MCP-NEGATIVE` marker in shipped Markdown is an HTML comment, never body text.

MCP-NEGATIVE-SCAN: ignore-file — the marker strings below are synthetic fixtures for the
wrapper check, not claims about any server. `coverage_reports.py` scans `tests/`, and would
otherwise count them as live or malformed markers. Same route as
`tests/test_mcp_negative_rationale_shape.py`.

A marker is dated maintainer metadata: the call asked, what was absent, the owning route and
the server version and date a dry run re-asks (INV-209). It is written for `/dry-run`, not for
the Bootcamper. Every marker in `plugins/` was an `<!-- MCP-NEGATIVE: … -->` comment except
two, which were bare paragraphs — so the metadata rendered as prose inside skills the guide
executes, and in the public mirror. Nothing noticed, because `coverage_reports.MCP_NEGATIVE`
is not anchored and parses a marker the same whether it is wrapped or not (#323).

The rules, stated in the issue:

- **A marker** is any line matching `coverage_reports.MCP_NEGATIVE_TOKEN` (colon included),
  loaded from there rather than redefined, so this guard and the `negatives` report share one
  definition. A colon-less mention ("its dated `MCP-NEGATIVE` marker") is not a marker, and
  `MCP-NEGATIVE-SCAN:` annotations do not match the token.
- **Inside a comment** means between a `<!--` and the next `-->`, tracked across lines, so a
  marker inside a multi-line comment passes.
- **No other exemptions.** The token in backticks or in a fenced code block renders visibly,
  so it is flagged.

⚠️ The detector is negative-controlled in this file with synthetic fixtures — it must flag the
unwrapped cases AND pass the wrapped ones — so a detector that flagged nothing, or
everything, fails here rather than certifying the tree.

Files are read as UTF-8 and split with `splitlines()`, so `\\r\\n` endings hold on Windows.
Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGINS = REPO / "plugins"
REPORTS = REPO / ".claude" / "skills" / "dry-run" / "coverage_reports.py"

OPEN, CLOSE = "<!--", "-->"


def load_reports():
    spec = importlib.util.spec_from_file_location("coverage_reports", REPORTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOKEN = load_reports().MCP_NEGATIVE_TOKEN


def unwrapped_markers(text):
    """Line numbers (1-based) of every marker in `text` that is not inside an HTML comment.

    The comment state is carried across lines, and within a line each `<!--`, `-->` and token
    is taken in order, so a marker after a comment closes on the same line is still flagged.
    """
    flagged = []
    inside = False
    for lineno, line in enumerate(text.splitlines(), 1):
        events = []
        for needle in (OPEN, CLOSE):
            start = line.find(needle)
            while start != -1:
                events.append((start, needle))
                start = line.find(needle, start + len(needle))
        events.extend((m.start(), "token") for m in TOKEN.finditer(line))
        for _, kind in sorted(events):
            if kind == OPEN:
                inside = True
            elif kind == CLOSE:
                inside = False
            elif not inside and lineno not in flagged:
                flagged.append(lineno)
    return flagged


def shipped_markdown(root=PLUGINS):
    return sorted(root.rglob("*.md"))


def offenders(root=PLUGINS, base=REPO):
    """`path:line` (relative to `base`) for every unwrapped marker in Markdown under `root`."""
    found = []
    for path in shipped_markdown(root):
        text = path.read_text(encoding="utf-8")
        for lineno in unwrapped_markers(text):
            found.append(f"{path.relative_to(base).as_posix()}:{lineno}")
    return found


STAMP = "— owner: fixture route (absence negative) — server 1.0.0, 2026-01-01"
MARKER = "MCP-NEGATIVE: fixture_tool(query='x') — returns no x " + STAMP


class TheShippedTreeIsClean(unittest.TestCase):

    def test_every_shipped_marker_is_inside_an_html_comment(self):
        bad = offenders()
        self.assertEqual(
            [], bad,
            "MCP-NEGATIVE markers outside an HTML comment render as body text; wrap each in "
            "`<!-- … -->` with its text unchanged:\n  " + "\n  ".join(bad))

    def test_the_scan_is_not_vacuous(self):
        """The scan must reach the markers it guards, or a clean result means nothing."""
        files = shipped_markdown()
        self.assertTrue(files, "no shipped Markdown found under plugins/")
        markers = sum(len(TOKEN.findall(p.read_text(encoding="utf-8"))) for p in files)
        self.assertGreater(markers, 0, "no MCP-NEGATIVE marker found under plugins/")

    def test_the_token_is_the_reports_own(self):
        """One definition: the guard and `coverage_reports.py negatives` agree on a marker."""
        self.assertEqual("MCP-NEGATIVE:", TOKEN.pattern)


class TheDetectorDiscriminates(unittest.TestCase):
    """Negative control: unwrapped cases are flagged, wrapped cases and mentions pass."""

    def test_an_unwrapped_marker_is_flagged(self):
        self.assertEqual([3], unwrapped_markers("# Title\n\n" + MARKER + "\n\nProse.\n"))

    def test_a_marker_in_a_single_line_comment_passes(self):
        self.assertEqual([], unwrapped_markers("Prose.\n\n<!-- " + MARKER + " -->\n"))

    def test_a_marker_in_a_multi_line_comment_passes(self):
        text = "Prose.\n\n<!-- Context for the dry run.\n" + MARKER + "\n   more -->\nProse.\n"
        self.assertEqual([], unwrapped_markers(text))

    def test_a_colon_less_mention_passes(self):
        self.assertEqual([], unwrapped_markers("Re-ask its dated `MCP-NEGATIVE` marker.\n"))

    def test_a_scan_annotation_passes(self):
        self.assertEqual([], unwrapped_markers(
            "MCP-NEGATIVE-SCAN: not-a-tool-claim — a fact about the data.\n"))

    def test_the_token_in_backticks_is_flagged(self):
        self.assertEqual([1], unwrapped_markers("Write `" + MARKER + "` here.\n"))

    def test_the_token_in_a_fenced_code_block_is_flagged(self):
        self.assertEqual([2], unwrapped_markers("```text\n" + MARKER + "\n```\n"))

    def test_a_marker_after_a_comment_closes_is_flagged(self):
        self.assertEqual([1], unwrapped_markers("<!-- note --> " + MARKER + "\n"))

    def test_a_marker_after_a_multi_line_comment_closes_is_flagged(self):
        self.assertEqual([3], unwrapped_markers("<!-- one\ntwo -->\n" + MARKER + "\n"))

    def test_crlf_line_endings_keep_the_comment_state_and_line_numbers(self):
        wrapped = "Prose.\r\n<!-- note\r\n" + MARKER + "\r\n-->\r\n"
        self.assertEqual([], unwrapped_markers(wrapped))
        self.assertEqual([2], unwrapped_markers("Prose.\r\n" + MARKER + "\r\n"))

    def test_the_failure_names_each_file_and_line(self):
        """Read from disk as UTF-8 with `\\r\\n` endings, as a Windows checkout has them."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skill = base / "plugins" / "x" / "skills" / "m" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_bytes(("é\r\n<!-- " + MARKER + " -->\r\n\r\n" + MARKER + "\r\n")
                              .encode("utf-8"))
            (base / "plugins" / "x" / "clean.md").write_text("<!-- " + MARKER + " -->\n",
                                                             encoding="utf-8")
            self.assertEqual(["plugins/x/skills/m/SKILL.md:4"],
                             offenders(base / "plugins", base))


if __name__ == "__main__":
    unittest.main()
