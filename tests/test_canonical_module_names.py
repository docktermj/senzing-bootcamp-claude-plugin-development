"""Module display names come from one table, and no file invents a variant.

INV-079 makes the module NAME the Bootcamper-facing identifier — banners, journey maps,
transition questions, completion lines. That only works if there is one spelling per
module. There wasn't. The 2026-07-26 audit found four inventions in the public-facing
README alone ("SDK Installation and Configuration", "Identify and Collect Data Sources",
an Oxford-comma "Query, Visualize, and Discover", and a prose description standing in for
"Truth Set visualization"), plus "Data quality & mapping" and "Query/Visualize/Discover"
in the Required-modules list the agent reads aloud during Bootcamp preparation and in the
shipped example recap.

The README also omitted **Bootcamp preparation** — the first *mandatory* module — from its
list of what the bootcamp covers, which is a completeness defect rather than a naming one
and is checked here too, since both come from the same table.

A number is not a name either (#612). The example recap and two Bootcamper-facing quotes, the
CORD quote in Data collection and the software-integration statement in Discover the Business
Problem, named modules as "Module 5" or "Module 7", and the recap wrote "System Verification".
Those texts are checked for `Modules? \\d` and "System Verification". Each quote is located by
its opening words, and a quote that cannot be located fails the check by name.

The source of truth is the module table in `bootcamp-preparation/SKILL.md`, which already
declares itself as such ("source of truth for selection and the journey map") and carries
the State token column. This test parses that table rather than hardcoding names, so
renaming a module is a one-place edit that this test then enforces everywhere.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PREP = PLUGIN / "skills" / "bootcamp-preparation" / "SKILL.md"
README = REPO_ROOT / "README.md"

# Off-canon spellings found in the field. A variant stays listed after it is fixed —
# that is what stops it coming back.
#
# Out of scope deliberately: case-only differences in a skill's own H1 ("System
# Verification" for "System verification"), which is ordinary title casing rather than a
# different name. A different NAME is the defect — modules 2 and 4 were titled "SDK
# Installation and Configuration" and "Identify and Collect Data Sources", the spellings
# the agent reads immediately before announcing the module in its banner.
BANNED_VARIANTS = (
    "Data quality & mapping",
    "Data Quality & Mapping",
    "Query/Visualize/Discover",
    "SDK Installation and Configuration",
    "Identify and Collect Data Sources",
    "Query, Visualize, and Discover",
    "Data Quality, Mapping and Transformation",  # missing the serial comma
)


def variant_lines(text, variant):
    """1-based lines where ``variant`` starts, matched across line wraps (#424).

    A module name is several words, and prose wraps wherever the column runs out, so a
    line-at-a-time ``in`` check missed a banned name split across two lines.
    """
    return match_lines(text, re.compile(re.escape(variant)))


#: A banned variant wrapped mid-name, for the negative control.
WRAPPED_VARIANT = "Next up is the module called SDK Installation\nand Configuration, in Module 2.\n"


#: The example recap a Bootcamper reads as the model of their own recap (#612).
RECAP = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"

#: Text that names a module by number, or by the title-cased "System Verification" (#612).
#: "Module" followed by a non-digit ("the Data collection module") is allowed.
NUMBERED_OR_RETIRED = (
    re.compile(r"\bModules? \d"),
    re.compile(r"System Verification"),
)

#: Bootcamper-facing quoted spans the ban covers, each located by its opening words (#612).
#: A span runs from its opening words to the next closing quotation mark. Out of scope on
#: purpose: a general detector over every quoted string, since most `>` blockquotes in the
#: skills are agent-facing.
NAMED_SPANS = (
    ("Module 4's CORD quote",
     PLUGIN / "skills" / "module-04-data-collection" / "SKILL.md",
     "Senzing provides **CORD (Collections Of Relatable Data)**:"),
    ("Module 1's software-integration statement",
     PLUGIN / "skills" / "module-01-business-problem" / "phase2-document-confirm.md",
     "If you name a system,"),
)


def locate_span(text, opening):
    """The span that starts with ``opening`` and ends at the next ``"``, or None.

    The returned text keeps the file's line numbering: everything before the span becomes
    the same number of empty lines, so a match inside it reports its line in the file.
    The opening words match across a line wrap, including a wrap inside a blockquote.
    """
    words = [re.escape(w) for w in opening.split()]
    m = re.search(r"[\s>]+".join(words), text)
    if not m:
        return None
    end = text.find('"', m.end())
    if end < 0:
        return None
    return "\n" * text.count("\n", 0, m.start()) + text[m.start():end]


def numbered_or_retired_lines(text):
    """``(line, matched text)`` for each module number or retired spelling, across wraps."""
    hits = []
    for pattern in NUMBERED_OR_RETIRED:
        for n in match_lines(text, pattern):
            hits.append((n, pattern.pattern))
    return sorted(hits)


def span_offenders(name, text, opening):
    """Offender lines for one named span; a span that cannot be located is an offender too."""
    span = locate_span(text, opening)
    if span is None:
        return [f"{name}: not located by its opening words {opening!r}"]
    return [f"{name}:{n} matches /{p}/" for n, p in numbered_or_retired_lines(span)]


def canonical_names():
    """Display names from the Bootcamp preparation module table, in order.

    Line-scoped by design (#424): a table row is one line.
    """
    rows = []
    for line in PREP.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`", line)
        if m:
            rows.append((m.group(2), m.group(4)))
    return rows


def shipped_and_public_files():
    """Everything a Bootcamper or prospective user reads."""
    for root, suffixes in ((PLUGIN, (".md",)), (REPO_ROOT / "docs", (".md",))):
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if "pytest_cache" in path.parts:
                continue
            yield path
    yield README


class TestTableIsParseable(unittest.TestCase):
    """If the table stops parsing, every other assertion here goes vacuous."""

    def test_all_eleven_modules_parse(self):
        rows = canonical_names()
        self.assertEqual(
            11, len(rows), f"expected 11 modules in the prep table, parsed {len(rows)}"
        )
        for name, token in rows:
            with self.subTest(module=name):
                self.assertTrue(name.strip())
                self.assertRegex(token, r"^[a-z_]+$", "State tokens are snake_case")

    def test_the_two_comma_bearing_names_are_present(self):
        """These two are why several files reach for an abbreviation."""
        names = [n for n, _ in canonical_names()]
        self.assertIn("Data Quality, Mapping, and Transformation", names)
        self.assertIn("Query, Visualize and Discover", names)


class TestNoInventedVariants(unittest.TestCase):

    def test_no_shipped_or_public_file_uses_a_banned_variant(self):
        offenders = []
        for path in shipped_and_public_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for variant in BANNED_VARIANTS:
                for n in variant_lines(text, variant):
                    offenders.append(
                        f"{path.relative_to(REPO_ROOT)}:{n} uses '{variant}'"
                    )
        self.assertEqual(
            [],
            offenders,
            "Off-canon module name(s); use the spelling in bootcamp-preparation's "
            "module table (INV-079):\n  " + "\n  ".join(offenders),
        )

    def test_a_wrapped_variant_is_caught_at_its_first_line(self):
        """Negative control (#424): "Installation" ends line 1 and "and" begins line 2."""
        self.assertEqual([1], variant_lines(WRAPPED_VARIANT, "SDK Installation and Configuration"))
        # The old line-at-a-time check, kept only to show the fixture is the hard case.
        self.assertFalse(any("SDK Installation and Configuration" in line
                             for line in WRAPPED_VARIANT.split("\n")))

    def test_a_wrapped_canonical_name_is_not_a_variant(self):
        """Must-not-flag (INV-282): the canonical name, wrapped, trips no banned variant."""
        text = "Then comes Data Quality, Mapping,\nand Transformation, and after it Query,\nVisualize and Discover.\n"
        for variant in BANNED_VARIANTS:
            with self.subTest(variant=variant):
                self.assertEqual([], variant_lines(text, variant))

    def test_banned_variants_do_not_collide_with_canonical_names(self):
        """A banned string that is a substring of a canonical name would be unfixable."""
        names = [n for n, _ in canonical_names()]
        for variant in BANNED_VARIANTS:
            with self.subTest(variant=variant):
                self.assertNotIn(
                    variant,
                    " | ".join(names),
                    "banned variant appears inside a canonical name",
                )


class TestBootcamperTextNamesNoModuleByNumber(unittest.TestCase):
    """The example recap and the named Bootcamper-facing spans name modules by name (#612).

    INV-079 makes the name the Bootcamper-facing identifier, so "Module 5" in a sentence the
    Bootcamper reads, or the title-cased "System Verification", is the same defect as an
    invented variant. Agent-facing text that names modules by number is out of scope.
    """

    def test_the_example_recap_names_no_module_by_number(self):
        hits = numbered_or_retired_lines(RECAP.read_text(encoding="utf-8"))
        self.assertEqual(
            [], hits,
            f"{RECAP.relative_to(REPO_ROOT)} names a module by number or writes "
            f"\"System Verification\"; use the module table's name (INV-079): {hits}")

    def test_each_named_span_names_no_module_by_number(self):
        for name, path, opening in NAMED_SPANS:
            with self.subTest(span=name):
                self.assertEqual(
                    [], span_offenders(name, path.read_text(encoding="utf-8"), opening),
                    f"{path.relative_to(REPO_ROOT)}: fix the span, or, if its opening words "
                    "changed, update NAMED_SPANS (INV-079)")

    # Negative controls: each check fails on the text #612 fixed, put back into a copy.

    def test_the_old_cord_quote_is_caught(self):
        name, path, opening = NAMED_SPANS[0]
        text = path.read_text(encoding="utf-8")
        broken = text.replace("> the Data Quality, Mapping, and Transformation module checks",
                              "> Module 5 checks", 1)
        self.assertNotEqual(broken, text, "control did not apply")
        self.assertTrue(span_offenders(name, broken, opening))

    def test_the_old_module_1_statement_is_caught(self):
        name, path, opening = NAMED_SPANS[1]
        text = path.read_text(encoding="utf-8")
        broken = text.replace("If you name a system, the Query,\nVisualize and Discover module",
                              "If you name a system, Module\n7", 1)
        self.assertNotEqual(broken, text, "control did not apply")
        offenders = span_offenders(name, broken, opening)
        self.assertEqual(1, len(offenders))
        self.assertIn("Modules?", offenders[0])

    def test_the_old_recap_lines_are_caught(self):
        text = RECAP.read_text(encoding="utf-8")
        for fixed, old in (
            ("- Ran the System verification checks:", "- Ran the System Verification checks:"),
            ("recorded in Discover the Business Problem,", "recorded in Module 1,"),
            ("no warning was presented; Data processing will use",
             "no warning was presented; Module 6 will use"),
            ("against the Data collection snapshot", "against the Module 4 snapshot"),
        ):
            with self.subTest(old=old):
                broken = text.replace(fixed, old, 1)
                self.assertNotEqual(broken, text, "control did not apply")
                self.assertEqual(1, len(numbered_or_retired_lines(broken)))

    def test_a_span_whose_opening_words_changed_fails_by_name(self):
        name, path, opening = NAMED_SPANS[0]
        text = path.read_text(encoding="utf-8")
        broken = text.replace(opening, "Senzing offers **CORD**:", 1)
        self.assertNotEqual(broken, text, "control did not apply")
        offenders = span_offenders(name, broken, opening)
        self.assertEqual(1, len(offenders))
        self.assertTrue(offenders[0].startswith(f"{name}: not located"))

    def test_a_module_named_by_name_is_allowed(self):
        """Must-not-flag (INV-282): "Module" before a non-digit is not a number."""
        text = 'say: "Then the Data collection module, and Modules\nfor mapping, run next."'
        self.assertEqual([], span_offenders("fixture", text, "Then the"))

    def test_a_wrapped_module_number_is_caught(self):
        """The number ban matches across a wrap inside a blockquote (INV-346)."""
        text = 'Intro.\n\n> "Your data goes to Module\n> 5 next."\n'
        offenders = span_offenders("fixture", text, "Your data")
        self.assertEqual(1, len(offenders))
        self.assertTrue(offenders[0].startswith("fixture:3 "), offenders)


class TestReadmeListsEveryModule(unittest.TestCase):
    """The public README's coverage list must not omit a module — mandatory or optional."""

    def test_readme_names_every_module(self):
        text = README.read_text(encoding="utf-8")
        missing = [name for name, _ in canonical_names() if name not in text]
        self.assertEqual(
            [],
            missing,
            "README.md omits module(s) from what the bootcamp covers — Bootcamp "
            f"preparation, the first mandatory module, was omitted this way: {missing}",
        )


if __name__ == "__main__":
    unittest.main()
