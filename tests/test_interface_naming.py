"""Every reference to a Claude user interface names which one (INV-158).

Claude Code — which this plugin plugs into — runs in more than one interface, and
Claude Desktop runs Claude Code too. So "Claude Code" does not distinguish the terminal
from the desktop application, and "the Claude app" distinguishes nothing at all: a
bootcamper told to "set it with your Claude app's model and effort controls" has to guess
which controls are meant. The install instructions had the same problem from the other
side, offering "Claude Desktop (desktop)" beside "Claude Code (command line)" as though
they were different products.

`tests/test_retired_vocabulary.py` owns the negative half — "Claude app" may appear only
on a line that frames it as retired. This file owns the positive half, which a ban cannot
express: that both interfaces are actually documented, that the model/effort nudge names
each interface it adapts to, and that the two install paths point at each other with links
that resolve. The cross-document link is pinned because renaming a heading silently breaks
an anchor: nothing in a Markdown repo fails when `#using-claude-code` no longer exists.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
README = os.path.join(REPO_ROOT, "README.md")
CLI_DOC = os.path.join(REPO_ROOT, "docs", "README.md")
GROUND_RULES = os.path.join(PLUGIN, "skills", "bootcamp-onboarding", "ground-rules.md")
GRADUATION = os.path.join(PLUGIN, "skills", "graduation", "SKILL.md")
MODEL_SELECTION = os.path.join(PLUGIN, "docs", "model-selection.md")

# The canonical name of each interface the plugin can run in.
DESKTOP = "Claude Desktop"
CLI = "Claude Code CLI"
WEB = "Claude web app"
IDE = "Claude IDE extension"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def flat(path):
    """`read` with whitespace collapsed, so a re-wrapped paragraph still matches."""
    return re.sub(r"\s+", " ", read(path))


def anchor(heading):
    """A Markdown heading's GitHub anchor."""
    slug = heading.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"\s+", "-", slug)


class InstallDocsNameBothInterfaces(unittest.TestCase):
    def test_readme_offers_both_by_name(self):
        text = flat(README)
        self.assertIn(DESKTOP, text)
        self.assertIn(CLI, text)

    def test_readme_says_which_one_its_walkthrough_covers(self):
        """A reader must know, before step 1, which interface they are following."""
        self.assertRegex(read(README), re.compile(r"^#+\s+Using Claude Desktop\s*$", re.M))

    def test_the_cli_doc_says_which_one_it_covers(self):
        self.assertRegex(
            read(CLI_DOC), re.compile(r"^#+\s+Using the Claude Code CLI\s*$", re.M)
        )

    def test_the_readme_link_to_the_cli_doc_resolves(self):
        """Renaming a heading silently breaks the anchor; nothing else catches it."""
        link = re.search(r"\]:\s*docs/README\.md#([\w-]+)", read(README))
        self.assertIsNotNone(link, "README no longer links to the CLI install doc")
        headings = {anchor(m) for m in re.findall(r"^#+\s+(.*)$", read(CLI_DOC), re.M)}
        self.assertIn(
            link.group(1),
            headings,
            f"README links to docs/README.md#{link.group(1)}, which is not a heading there",
        )

    def test_the_cli_doc_links_back_to_the_desktop_path(self):
        link = re.search(r"\.\./README\.md#([\w-]+)", read(CLI_DOC))
        self.assertIsNotNone(link, "the CLI doc should point at the Desktop path")
        headings = {anchor(m) for m in re.findall(r"^#+\s+(.*)$", read(README), re.M)}
        self.assertIn(link.group(1), headings)

    def test_no_internal_readme_anchor_dangles(self):
        """Both install docs, every in-page anchor — the renamed troubleshooting
        heading is exactly the case that would break silently."""
        for path in (README, CLI_DOC):
            text = read(path)
            headings = {anchor(m) for m in re.findall(r"^#+\s+(.*)$", text, re.M)}
            for target in re.findall(r"\]\(#([\w-]+)\)", text):
                with self.subTest(path=os.path.basename(path), anchor=target):
                    self.assertIn(target, headings)


class TheNudgeNamesEveryInterfaceItAdaptsTo(unittest.TestCase):
    """INV-098 adapts to four interfaces; INV-158 requires each to be named."""

    def test_ground_rules_names_all_four(self):
        text = flat(GROUND_RULES)
        for name in (CLI, DESKTOP, WEB, IDE):
            with self.subTest(interface=name):
                self.assertIn(name, text)

    def test_graduation_takes_the_interface_wording_from_ground_rules(self):
        """Graduation's nudge is ground-rules' nudge since #293, so the four names live there.

        Graduation carried its own copy of the switch question and its interface-adapted
        wording until then, and this test required that copy to name all four interfaces.
        It now points to ground-rules instead, and `test_ground_rules_names_all_four` holds
        the one copy to the same requirement. What is asserted here is that graduation did
        not fork the interface wording back in, and that its pointer reaches the copy that
        names them.
        """
        text = flat(GRADUATION)
        self.assertNotIn("Would you like to switch to", text)
        self.assertIn('`../bootcamp-onboarding/ground-rules.md` → "Module start banners and '
                      'transitions"', text)

    def test_the_model_table_note_names_the_cli_by_its_full_name(self):
        """Both copies of the table carry the note; INV-114 keeps them in sync."""
        for path in (GROUND_RULES, MODEL_SELECTION):
            with self.subTest(path=os.path.basename(path)):
                self.assertIn(CLI, flat(path))

    def test_the_unknown_interface_fallback_is_the_only_vague_wording(self):
        """"Your Claude interface" is honest when the interface is unknown, and a
        shortcut everywhere else — so it must appear only alongside that condition."""
        text = flat(GROUND_RULES)
        for match in re.finditer(r"your Claude interface", text):
            window = text[max(0, match.start() - 260) : match.end() + 120]
            self.assertRegex(
                window,
                r"cannot be determined|cannot tell|undeterminable|unknown interface",
                "vague interface wording outside the unknown-interface fallback",
            )


class TheDesktopPathIsNotDescribedAsSomethingElse(unittest.TestCase):
    def test_readme_does_not_oppose_desktop_to_claude_code(self):
        """The original defect: two interfaces of one product offered as rivals."""
        text = flat(README)
        self.assertNotRegex(text, r"\*\*Claude Code\*\*\s*\(command line\)")

    def test_readme_states_that_desktop_runs_claude_code(self):
        self.assertRegex(
            flat(README),
            r"Claude Code plugin, and Claude Code has two interfaces"
            r"|Claude Code inside the desktop",
            "the README should say why both entries are the same plugin",
        )


if __name__ == "__main__":
    unittest.main()
