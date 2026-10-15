"""The PDF generators' Usage blocks name every flag their parsers define (#616).

A script's module docstring is what a reader of the file sees first, and its ``Usage:``
block reads as the full command line. Both generators had grown flags their Usage block
never named (``--require-sections``, ``--subtitle``, ``--no-section-check``;
``--preferences``, ``--expect-modules``, ``--progress``, ``--expect-visualizations``), so
the block claimed a smaller interface than the one that ships.

The flags are read from the parser itself (every ``add_argument("--…")`` call), so a flag
added later fails here until the Usage block names it. The help text of
``--require-sections`` explains its semicolons by section names that contain commas; that
claim is pinned against the names it cites, which must contain a comma.

Run:  python3 -m unittest discover -s tests
"""
import ast
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts")

#: The scripts #616 brought into line. Each has a ``Usage:`` block and an argparse parser.
COVERED = ("generate_discoveries_pdf.py", "generate_recap_pdf.py")

USAGE_BLOCK = re.compile(r"^Usage:\n((?:[ \t]+\S.*\n)+)", re.M)


def _tree(name):
    with open(os.path.join(SCRIPTS, name), encoding="utf-8") as fh:
        return ast.parse(fh.read())


def parser_flags(tree):
    """Every long option passed to an ``add_argument`` call."""
    flags = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_argument":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and str(arg.value).startswith("--"):
                    flags.add(arg.value)
    return flags


def usage_block(tree):
    match = USAGE_BLOCK.search(ast.get_docstring(tree) or "")
    return match.group(1) if match else None


def names_flag(block, flag):
    return re.search(re.escape(flag) + r"(?![\w-])", block) is not None


class UsageNamesEveryFlag(unittest.TestCase):
    def test_each_usage_block_names_every_parser_flag(self):
        for name in COVERED:
            with self.subTest(script=name):
                tree = _tree(name)
                flags = parser_flags(tree)
                self.assertGreater(len(flags), 1, "the parser scan found no flags")
                block = usage_block(tree)
                self.assertIsNotNone(block, "%s has no Usage: block" % name)
                missing = sorted(f for f in flags if not names_flag(block, f))
                self.assertEqual([], missing,
                                 "%s's Usage block omits flags its parser defines" % name)

    def test_a_missing_flag_is_caught(self):
        """Negative control: a Usage block without one of the flags fails the check."""
        block = "    python3 x.py [--input A]\n                 [--check]\n"
        self.assertTrue(names_flag(block, "--check"))
        self.assertFalse(names_flag(block, "--output"))
        # A flag that is a prefix of another is not satisfied by the longer one.
        self.assertFalse(names_flag("    python3 x.py [--expect-modules X]\n", "--expect"))


class CommaExamplesContainCommas(unittest.TestCase):
    def test_require_sections_help_cites_names_with_commas(self):
        with open(os.path.join(SCRIPTS, "generate_discoveries_pdf.py"), encoding="utf-8") as fh:
            source = fh.read()
        sentence = re.search(r"section names \"\s*\"contain commas \((.*?)\)", source, re.S)
        self.assertIsNotNone(sentence, "the --require-sections help no longer cites examples")
        examples = re.findall(r"'([^']+)'", sentence.group(1))
        self.assertTrue(examples, "the --require-sections help cites no quoted names")
        for example in examples:
            self.assertIn(",", example,
                          "a name cited as containing a comma has none: %r" % example)


if __name__ == "__main__":
    unittest.main()
