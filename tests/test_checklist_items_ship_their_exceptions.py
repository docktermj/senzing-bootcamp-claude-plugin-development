"""A checklist item the Bootcamper works through unattended carries its own exception.

Enforces **INV-287** — where the SBCP ships a rule into an artifact the Bootcamper acts on
without the guide present, and that rule has a known site where following it is wrong, the
exception ships in the **same item** as the rule.

The instance: graduation writes `production/MIGRATION_CHECKLIST.md`, whose Performance
section tells the Bootcamper to replace ``*_DEFAULT_FLAGS`` composites in
``production/src/`` with explicit flags. On the **export call** a replacement assembled from
``SZ_ENTITY_INCLUDE_*`` members is the composition Module 6 observed returning rows with no
``RELATED_ENTITIES`` key at all and no error — a graph with nodes and no edges.

⚠️ **The qualification changed shape on 2026-11-10 (#904); what it must do did not.** Until
then the item exempted the export call outright and named ``SZ_ENTITY_DEFAULT_FLAGS`` as its
flag. But ``SZ_EXPORT_DEFAULT_FLAGS`` is itself a composite containing
``SZ_ENTITY_DEFAULT_FLAGS`` (``get_sdk_reference(topic='flags',
filter='SZ_EXPORT_DEFAULT_FLAGS')``, server 1.46.0), so the exemption kept a DEFAULT composite
in production code, against the server's production caution. The item now covers the export
call too and carries the qualification instead: a replacement there can drop output with no
error, so the team verifies every field and relationship its code reads before adopting one,
and leaves the item unchecked until it has. The tests below therefore fail if the export call
is exempted again, if the qualification leaves the quoted item, or if the item prescribes one
explicit flag set nobody has verified.

⚠️ **What makes this checkable is WHERE the qualification sits, not whether it exists.** The
guidance around the item is instruction to the guide and never travels; only the quoted
item text is copied into the Bootcamper's checklist. A qualification in the surrounding prose
satisfies a reader of this file and reaches nobody ticking the box, which is exactly the
failure INV-287 names — so the assertions read the QUOTED ITEM, and the negative control
that matters moves the qualification out of the quote into the prose beside it.

⚠️ **This guard asserts the INSTANCE, not the class.** INV-287 binds any unattended
artifact carrying a rule with a known wrong site; which rules have such a site is not
mechanically derivable, so no scan can enumerate them. The item itself is located by
scanning rather than by line number, so it survives being moved or renumbered.

Registered 2026-09-02 with no enforcer, which the invariant said outright. This closes
that, and it was not going to resurface on its own: `coverage_reports.py invariants`
counts any test mentioning an id as coverage, and a comment in
`test_invariant_enforcer_citations.py` names INV-287 to explain why it adds no pair — so
the one invariant with no guard was the one the gap report did not list.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRADUATION = REPO / "plugins" / "senzing-bootcamp" / "skills" / "graduation" / "SKILL.md"

#: The quoted text of a MIGRATION_CHECKLIST item — the part copied into the Bootcamper's
#: file. Everything outside the quotes is guidance to the guide and does not travel.
# ⚠️ ``re.S`` is load-bearing: the item is hand-wrapped across several lines, so a pattern
# without it matches nothing and every assertion below goes vacuous behind a green run.
QUOTED_ITEM = re.compile(r'\*"(.+?)"\*', re.S)

#: A concrete SZ_ flag name. A wildcard family (``SZ_*``, ``SZ_ENTITY_INCLUDE_*``) names no
#: set, so it does not match: the name must end in a letter or digit with no ``_`` or ``*``
#: after it.
CONCRETE_FLAG = re.compile(r"\bSZ_[A-Z0-9_]*[A-Z0-9](?![A-Z0-9_*])")

#: The sentences that make up the qualification. Each must be inside the quote.
QUALIFICATION = (
    r"(?i)including the export call",
    r"(?i)before you adopt a replacement",
    r"(?i)every field and relationship your code reads",
    r"(?i)leave this item unchecked",
)


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def default_flags_item(text=None):
    """The quoted checklist item about DEFAULT composites, located by scanning.

    Returns (quoted_text, surrounding_bullet). Hardcoding a line number would make this
    guard follow the file's shape rather than its content (INV-246).
    """
    if text is None:
        text = GRADUATION.read_text(encoding="utf-8")
    for m in QUOTED_ITEM.finditer(text):
        quoted = flat(m.group(1))
        if "_DEFAULT_FLAGS" in quoted and "production/src/" in quoted:
            start = text.rfind("\n  - ", 0, m.start())
            end = text.find("\n  - ", m.end())
            return quoted, flat(text[start: end if end != -1 else len(text)])
    return None, None


def item_problems(text):
    """Every way the quoted DEFAULT-flags item fails INV-287, as readable strings."""
    quoted, _ = default_flags_item(text)
    if quoted is None:
        return ["no quoted MIGRATION_CHECKLIST item about replacing *_DEFAULT_FLAGS in "
                "production/src/ was found"]
    problems = []
    if not re.search(r"(?i)replace `?\*_DEFAULT_FLAGS", quoted):
        problems.append("the item no longer states the general rule it qualifies")
    if re.search(r"(?i)except(?:ing)? (?:for )?the export call", quoted):
        problems.append("the item exempts the export call")
    for pattern in QUALIFICATION:
        if not re.search(pattern, quoted):
            problems.append(f"the quoted item lacks {pattern[4:]!r}")
    if not re.search(r"(?i)RELATED_ENTITIES", quoted):
        problems.append("the item does not name RELATED_ENTITIES as what a replacement can drop")
    if not re.search(r"(?i)with no error|no error is raised|silently", quoted):
        problems.append("the item does not say the failure is silent")
    concrete = CONCRETE_FLAG.findall(quoted)
    if concrete:
        problems.append(f"the item prescribes concrete flags {concrete}")
    return problems


class TheChecklistItemShipsItsException(unittest.TestCase):
    def setUp(self):
        self.text = GRADUATION.read_text(encoding="utf-8")
        self.quoted, self.bullet = default_flags_item(self.text)

    def test_the_item_is_found(self):
        """A scan matching nothing would make every assertion below vacuous."""
        self.assertIsNotNone(
            self.quoted,
            "no quoted MIGRATION_CHECKLIST item about replacing *_DEFAULT_FLAGS in "
            "production/src/ was found in graduation/SKILL.md. Either the item was removed "
            "— which INV-287's site would then no longer exist — or its shape changed and "
            "this guard has stopped reading it.",
        )

    def test_the_export_call_is_not_exempted(self):
        """The export call is reviewed with every other call, never carved out (#904)."""
        self.assertRegex(
            self.quoted, r"(?i)including the export call",
            "the quoted item must say the review covers the export call. "
            "SZ_EXPORT_DEFAULT_FLAGS contains SZ_ENTITY_DEFAULT_FLAGS, so exempting the "
            "export call keeps a DEFAULT composite in production code.",
        )
        self.assertNotRegex(
            self.quoted, r"(?i)except(?:ing)? (?:for )?the export call",
            "the quoted item exempts the export call again. Keep the export call in the "
            "review and qualify it with the verification step instead (#904).",
        )

    def test_the_qualification_is_inside_the_quoted_item(self):
        """⛔ The assertion INV-287 is actually about.

        Not "does the file mention the export call" — the file plainly does, in the ⛔
        beneath. The question is whether the Bootcamper, who receives only the quoted text,
        gets it.
        """
        for pattern in QUALIFICATION:
            with self.subTest(pattern=pattern):
                self.assertRegex(
                    self.quoted, pattern,
                    "the export-call qualification is not inside the quoted checklist item. "
                    "Only the quote is copied into production/MIGRATION_CHECKLIST.md; "
                    "guidance around it reaches the guide and never the Bootcamper ticking "
                    "the box. A qualification recorded beside the item is not shipped with "
                    "it (INV-287).",
                )

    def test_the_exception_names_the_consequence_not_just_the_carve_out(self):
        """A qualification with no reason is one a later editor tidies away as noise."""
        self.assertRegex(
            self.quoted, r"(?i)RELATED_ENTITIES",
            "the qualification must say what a replacement can cost on the export call — "
            "dropping RELATED_ENTITIES entirely. A bare 'verify first' gives a reader "
            "nothing to check for.",
        )

    def test_the_exception_says_the_failure_is_silent(self):
        self.assertRegex(
            self.quoted, r"(?i)with no error|no error is raised|silently",
            "the qualification must say the failure is SILENT. A Bootcamper who expects an "
            "error will read an empty graph as empty data, which is the whole reason this "
            "cannot be left to be discovered at runtime.",
        )

    def test_the_item_still_states_the_general_rule_it_excepts(self):
        """The qualification must qualify the rule, not replace it."""
        self.assertRegex(
            self.quoted, r"(?i)replace `?\*_DEFAULT_FLAGS",
            "the item must still carry the general instruction. An item reduced to its "
            "qualification no longer tells the Bootcamper what to do everywhere else.",
        )

    def test_the_item_prescribes_no_explicit_flag_set(self):
        """No universal replacement set has been verified, so the item names none.

        Wildcard families (``SZ_*``, ``SZ_ENTITY_INCLUDE_*``) describe; a concrete name such
        as ``SZ_ENTITY_DEFAULT_FLAGS`` or ``SZ_EXPORT_INCLUDE_ALL_ENTITIES`` prescribes.
        """
        self.assertEqual(
            [], CONCRETE_FLAG.findall(self.quoted),
            "the quoted item names concrete SZ_ flags. Which flags carry the output a "
            "project consumes is the team's to verify; a set written here is a guess the "
            "checklist would present as the answer (#904).",
        )

    def test_the_wildcard_pattern_tells_families_from_names(self):
        """CONCRETE_FLAG must not go vacuous by matching nothing, or everything."""
        self.assertEqual(["SZ_ENTITY_DEFAULT_FLAGS"],
                         CONCRETE_FLAG.findall("pass `SZ_ENTITY_DEFAULT_FLAGS` here"))
        self.assertEqual([], CONCRETE_FLAG.findall("`SZ_*` and `SZ_ENTITY_INCLUDE_*` members"))


class TheGuardCatchesEachRegression(unittest.TestCase):
    """Negative controls: each mutation of the shipped text must be reported."""

    def setUp(self):
        self.text = GRADUATION.read_text(encoding="utf-8")
        self.quoted, _ = default_flags_item(self.text)

    def mutate(self, old, new):
        self.assertIn(old, self.text, "the control's anchor is gone; re-anchor it")
        return self.text.replace(old, new, 1)

    def test_the_shipped_text_is_clean(self):
        self.assertEqual([], item_problems(self.text))

    def test_an_export_exemption_is_reported(self):
        text = self.mutate("**including the export call**",
                           "**except the export call**, where `SZ_ENTITY_DEFAULT_FLAGS` is "
                           "the documented choice")
        problems = item_problems(text)
        self.assertTrue(any("exempts the export call" in p for p in problems), problems)
        self.assertTrue(any("concrete flags" in p for p in problems), problems)

    def test_the_qualification_moved_out_of_the_quote_is_reported(self):
        """The control that matters: the words survive in the file, outside the quote."""
        sentence = ("Until you have, keep the\n    current flags and leave this item "
                    "unchecked.\"*")
        text = self.mutate(sentence, "\"*\n    Until you have, keep the current flags and "
                                     "leave this item unchecked.")
        self.assertIn("leave this item unchecked", flat(text))
        self.assertTrue(any("leave this item unchecked" in p for p in item_problems(text)))

    def test_dropping_the_verification_is_reported(self):
        start = self.text.index("Before you adopt a replacement there")
        end = self.text.index("leave this item unchecked.", start) + len(
            "leave this item unchecked.")
        text = self.text[:start] + self.text[end:]
        problems = item_problems(text)
        self.assertGreaterEqual(len(problems), 2, problems)

    def test_a_prescribed_flag_set_is_reported(self):
        text = self.mutate("with the explicit `SZ_*` flags",
                           "with `SZ_EXPORT_INCLUDE_ALL_ENTITIES | SZ_ENTITY_INCLUDE_ENTITY_NAME`")
        self.assertTrue(any("concrete flags" in p for p in item_problems(text)))


if __name__ == "__main__":
    unittest.main()
