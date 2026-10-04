"""Bootcamp preparation's Step 7 recap template obeys the rules its own file states.

Two defects, both hit by executing the module as written on a `--fresh` walk (2026-08-12), and
both invisible to the suite because nothing rendered the template:

1. The template labeled the value `• Language:`, while the same file says 100 lines earlier:
   *"Always say **programming language**, never the bare word 'language' (avoids confusion
   with spoken languages)."* An absolute rule, stated with its rationale, contradicted by a
   pinned-looking template in bootcamper-facing text. A guide cannot satisfy both.

2. The module list was comma-separated, and **two display names contain commas** — "Data
   Quality, Mapping, and Transformation" and "Query, Visualize and Discover" — so a Core run's
   list reads as fourteen modules instead of eleven. The plugin had already solved this for
   `generate_recap_pdf.py --check --expect-modules`, which takes a semicolon-separated list for
   exactly this reason; the fix stayed in the script because the script *parses* the names while
   Step 7 merely *displays* them — and display is where a human has to disambiguate.

The comma check here is deliberately written against **any** display name containing a comma,
read from the module table, rather than against the two that do today. A future module named
"Load, Resolve and Report" must not silently reintroduce this.

Nothing breaks in either case. The cost is that an instruction which cannot be followed as
written teaches the guide to read the surrounding instructions as advisory — and what surrounds
this one are the pinned gates where paraphrase is the documented failure mode (INV-056).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREP = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "bootcamp-preparation" / "SKILL.md"


def text():
    return PREP.read_text(encoding="utf-8")


def display_names():
    """Module display names from the table that is their source of truth (INV-079).

    Line-scoped by design (#424): a table row is one line.
    """
    names = []
    for line in text().splitlines():
        m = re.match(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            names.append(m.group(1))
    return names


def recap_template():
    """The fenced block the guide prints in Step 7.

    Line-scoped by design (#424): it is a ```text template printed as written, so each line
    is one printed line, and a label is the text before the colon on its own line.
    """
    blocks = re.findall(r"```text\n(.*?)```", text(), re.DOTALL)
    for block in blocks:
        if "Bootcamp preparation complete" in block:
            return block
    raise AssertionError("the Step 7 recap template was not found")


class TheTemplateIsFound(unittest.TestCase):
    def test_the_table_parses(self):
        names = display_names()
        self.assertGreaterEqual(len(names), 11, "the module table did not parse")
        self.assertIn("Bootcamp graduation", names)

    def test_the_template_parses(self):
        self.assertIn("• Modules:", recap_template())


class TheProgrammingLanguageRuleIsHonored(unittest.TestCase):
    def test_the_rule_is_still_stated(self):
        """If the rule goes, this test should be deleted deliberately, not pass vacuously."""
        self.assertRegex(
            re.sub(r"\s+", " ", text()),
            r"(?i)Always say .{0,4}programming language.{0,4}, never the bare word",
        )

    def test_the_recap_label_is_not_the_bare_word(self):
        """Any recap label mentioning a language must qualify it as the programming one."""
        for line in recap_template().splitlines():
            if ":" not in line:
                continue
            label = line.split(":")[0]
            if not re.search(r"(?i)language", label):
                continue
            self.assertRegex(
                label,
                r"(?i)programming language",
                "the recap template labels a line with the bare word 'language', which this "
                "file forbids ('avoids confusion with spoken languages'): %r" % line,
            )

    def test_the_recap_label_says_programming_language(self):
        self.assertRegex(recap_template(), r"(?i)•\s*Programming language:")


class TheModuleListIsUnambiguous(unittest.TestCase):
    def test_a_name_with_a_comma_forces_a_non_comma_separator(self):
        """Written against the property, not against today's two offending names."""
        commas = [n for n in display_names() if "," in n]
        if not commas:
            self.skipTest("no display name contains a comma — the hazard does not apply")
        modules_line = [l for l in recap_template().splitlines() if l.startswith("• Modules:")]
        self.assertEqual(1, len(modules_line), "expected exactly one Modules: line")
        line = modules_line[0]
        self.assertRegex(
            line,
            r"(?i)semicolon|;",
            "%d module display name(s) contain commas (%s), so a comma-separated list is "
            "ambiguous — a Core run reads as more modules than it has. Separate with "
            "semicolons, as generate_recap_pdf.py --expect-modules already does: %r"
            % (len(commas), "; ".join(commas), line),
        )

    def test_the_reason_is_recorded_inline(self):
        """Without the reason, the next editor tidies the semicolons back to commas."""
        flat = re.sub(r"\s+", " ", text())
        self.assertRegex(flat, r"(?i)semicolons, not commas")
        self.assertRegex(flat, r"(?i)reads as \*\*fourteen\*\* modules instead of eleven")
        self.assertIn("--expect-modules", flat)

    def test_the_display_names_were_not_renamed_to_dodge_the_problem(self):
        """INV-079 requires these verbatim; renaming is not an available fix."""
        names = display_names()
        self.assertIn("Data Quality, Mapping, and Transformation", names)
        self.assertIn("Query, Visualize and Discover", names)


class TheTemplateStillWorksUnderMinimal(unittest.TestCase):
    def test_the_single_line_rule_survives(self):
        self.assertRegex(
            re.sub(r"\s+", " ", text()),
            r"(?i)keep it to a single line under `minimal`",
            "the separator fix was chosen over a one-per-line list precisely because minimal "
            "verbosity requires a single line — that requirement must still be stated",
        )


if __name__ == "__main__":
    unittest.main()
