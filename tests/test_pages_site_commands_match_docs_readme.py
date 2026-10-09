"""The Pages site's `claude plugin …` commands match `docs/README.md`'s (#455).

`docs/index.html`, the GitHub Pages quick-start site dev owns since #452, repeats the install
commands of `docs/README.md`, and its header comment says it must follow them. Until this
module nothing checked that it did, so the two could drift silently, as the model names in
their prose already had.

⛔ **The page names exactly the `claude plugin …` commands `docs/README.md` names.** This
module extracts every `claude plugin …` command from the page (the text inside each
`<code>` element, HTML-unescaped, one command per non-blank stripped line) and from the README
(each non-blank stripped line inside its `console` fences, including the fences indented inside
list items), and asserts the two **sets** are equal. On a difference it lists the commands found
only on the page and those found only in the README.

⚠️ **Sets, deliberately.** The page shows `claude plugin update …` twice (the install step and
"Update or uninstall"), and it splits each README block that holds several commands into one
block per command (its header comment says so). Neither is drift, and comparing sets of lines
makes both invisible.

⛔ **An empty side fails, naming the file.** Without that, a broken extractor, or a page or
README that lost its commands, would compare `∅ == ∅` and pass. A negative control changes one
command on the page and shows the comparison fails.

⚠️ **What a green run does not establish.** Only `claude plugin …` commands are compared. The
page's other commands (`curl …`, `irm …`, `mkdir`, `cd`, `claude --model …`, "Start the
bootcamp"), the model names in prose, the slash-command table and the Claude Desktop route
(which follows the root `README.md`) are not checked. Nor is the propagated public tree: the
rewrite pass applies to both files alike, and
`tests/test_propagate_publishes_the_pages_site.py` checks the slug on the way out.

Source issue: #455.

Stdlib only (INV-108); both files read as text, no network.

Run:  python3 -m unittest discover -s tests
"""
import html.parser
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGE = REPO_ROOT / "docs" / "index.html"
README = REPO_ROOT / "docs" / "README.md"
PAGE_REL = "docs/index.html"
README_REL = "docs/README.md"

PREFIX = "claude plugin "

#: An opening or closing backtick fence, at any indent, with its info string.
FENCE = re.compile(r"^\s*(`{3,})\s*([^`\s]*)\s*$")


class _CodeText(html.parser.HTMLParser):
    """Collects the text of every `<code>` element, entities already unescaped."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "code":
            if self.depth == 0:
                self.blocks.append("")
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == "code" and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.blocks[-1] += data


def _commands(lines):
    """The `claude plugin …` commands among `lines`, each stripped, as a set."""
    return {s for s in (line.strip() for line in lines) if s.startswith(PREFIX)}


def page_commands(text):
    """Every `claude plugin …` command inside a `<code>` element of the page."""
    parser = _CodeText()
    parser.feed(text)
    parser.close()
    return _commands(line for block in parser.blocks for line in block.splitlines())


def readme_commands(text):
    """Every `claude plugin …` command inside a `console` fence, indented or not."""
    # Line-scoped by design (#455): in a console fence each non-blank line is one command,
    # and a fence is never reflowed, so a line is the unit the comparison is about.
    lines, fence = [], None
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence is None:
            if match and match.group(2):
                fence = (match.group(1), match.group(2))
            continue
        if match and not match.group(2) and len(match.group(1)) >= len(fence[0]):
            fence = None
            continue
        if fence[1] == "console":
            lines.append(line)
    return _commands(lines)


def drift(page_text, readme_text):
    """None when the two sets match; otherwise the failure message, naming the side."""
    page, readme = page_commands(page_text), readme_commands(readme_text)
    empty = ["%s yields no `claude plugin …` command %s: the extractor or the file broke"
             % (rel, where) for rel, found, where in (
                 (PAGE_REL, page, "inside <code>"),
                 (README_REL, readme, "inside a console fence"),
             ) if not found]
    if empty:
        return "; ".join(empty)
    if page == readme:
        return None
    return ("the page's `claude plugin …` commands differ from docs/README.md's\n"
            "  only in %s:\n%s\n  only in %s:\n%s" % (
                PAGE_REL, "\n".join("    " + c for c in sorted(page - readme)) or "    (none)",
                README_REL, "\n".join("    " + c for c in sorted(readme - page)) or "    (none)"))


class ThePageFollowsTheReadme(unittest.TestCase):
    """The real files: the page and the README name the same `claude plugin …` commands."""

    def test_the_two_sets_are_equal(self):
        problem = drift(PAGE.read_text("utf-8"), README.read_text("utf-8"))
        if problem:
            self.fail(problem)

    def test_both_sides_yield_commands(self):
        self.assertTrue(page_commands(PAGE.read_text("utf-8")),
                        "%s yields no `claude plugin …` command" % PAGE_REL)
        self.assertTrue(readme_commands(README.read_text("utf-8")),
                        "%s yields no `claude plugin …` command" % README_REL)


class TheExtractorsReadWhatTheSpecSays(unittest.TestCase):
    """Synthetic inputs for the extraction rules."""

    def test_page_code_is_unescaped_and_stripped(self):
        page = "<p><code>  claude plugin install a&#64;b  </code> and <code>ls</code></p>"
        self.assertEqual(page_commands(page), {"claude plugin install a@b"})

    def test_text_outside_code_is_ignored(self):
        self.assertEqual(page_commands("<p>claude plugin install a@b</p>"), set())

    def test_indented_console_fences_count_line_by_line(self):
        readme = ("1. Install.\n\n"
                  "    ```console\n"
                  "    claude plugin marketplace add o/r\n"
                  "\n"
                  "    claude plugin install a@b\n"
                  "    ```\n")
        self.assertEqual(readme_commands(readme),
                         {"claude plugin marketplace add o/r", "claude plugin install a@b"})

    def test_other_fences_and_prose_are_ignored(self):
        readme = ("claude plugin install prose@x\n\n"
                  "```bash\nclaude plugin install bash@x\n```\n\n"
                  "```console\nclaude plugin install console@x\n```\n")
        self.assertEqual(readme_commands(readme), {"claude plugin install console@x"})

    def test_duplicates_and_splitting_are_not_drift(self):
        page = ("<pre><code>claude plugin install a@b</code></pre>"
                "<pre><code>claude plugin update a@b</code></pre>"
                "<pre><code>claude plugin update a@b</code></pre>")
        readme = "```console\nclaude plugin install a@b\nclaude plugin update a@b\n```\n"
        self.assertIsNone(drift(page, readme))


class TheCheckCatchesDrift(unittest.TestCase):
    """Negative controls: a changed command and an empty side both fail, saying where."""

    def setUp(self):
        self.page = PAGE.read_text("utf-8")
        self.readme = README.read_text("utf-8")

    def test_changing_one_command_on_the_page_fails(self):
        before = sorted(page_commands(self.page))[0]
        after = before + "-drifted"
        mutated = self.page.replace(before, after)
        self.assertNotEqual(mutated, self.page, "the control mutated nothing")
        problem = drift(mutated, self.readme)
        self.assertIsNotNone(problem, "a changed page command passed the comparison")
        self.assertIn("only in %s:\n    %s" % (PAGE_REL, after), problem)
        self.assertIn("only in %s:\n    %s" % (README_REL, before), problem)

    def test_an_empty_page_fails_naming_the_page(self):
        problem = drift(self.page.replace("<code>", "<span>").replace("</code>", "</span>"),
                        self.readme)
        self.assertIsNotNone(problem)
        self.assertIn(PAGE_REL, problem)
        self.assertNotIn(README_REL, problem)

    def test_an_empty_readme_fails_naming_the_readme(self):
        problem = drift(self.page, self.readme.replace("```console", "```text"))
        self.assertIsNotNone(problem)
        self.assertIn(README_REL, problem)
        self.assertNotIn(PAGE_REL, problem)


if __name__ == "__main__":
    unittest.main()
