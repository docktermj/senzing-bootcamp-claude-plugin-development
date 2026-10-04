"""Both statements of the install-verification rule cite INV-218, and INV-129 keeps its scope.

Module 2 states "an installer's exit code is not evidence" twice. Before 2026-08-13 one statement
cited nothing and the other cited **INV-129**, whose subject is a rendered *deliverable* — "PDF, PNG,
HTML artifact" — with remedies like "rasterize the page, open the image". An SDK install is none of
those, so the citation pointed a reader at an invariant about PDFs. INV-218 was registered for the
install case; INV-129 remains the deliverable rule and the two are siblings.

Why a guard rather than trust: the borrowed citation was invisible to
`.claude/skills/production-readiness-audit/conformance.py rules`, which reports hard rules whose
section cites **no** invariant. A wrong citation is a citation, so the scan counted that line as
accounted for. `citations.py verify` proves an ID *exists*, never that it is the right one. Only
reading found it, and only a test keeps it found.

⚠️ **Asserts what each site MUST say, not what it must not.** The rule's prose is free to be
reworded; what must not regress is that both sites name INV-218 and that INV-129's own text still
scopes itself to rendered deliverables.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_02 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
             / "module-02-sdk-setup" / "SKILL.md")
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"


ZERO_EXIT = re.compile(r"(?i)zero exit code")
NOT_EVIDENCE = re.compile(r"exit 0 is not evidence")


def lines_stating(pattern, text=None):
    """The line on which each statement of ``pattern`` starts, matched across wraps (#424).

    The citation is still asserted on that line, as before: a statement that wraps and puts
    its citation on the next line fails rather than passes.
    """
    text = MODULE_02.read_text(encoding="utf-8") if text is None else text
    lines = text.split("\n")
    return [lines[n - 1] for n in match_lines(text, pattern)]


class BothStatementsCiteTheInstallRule(unittest.TestCase):
    def test_the_brew_zero_exit_rule_cites_inv218(self):
        """The ⛔ that explains why a zero exit is not evidence."""
        hits = lines_stating(ZERO_EXIT)
        self.assertTrue(hits, "the zero-exit-code rule is gone from module 2")
        for line in hits:
            with self.subTest(line=line.strip()[:60]):
                self.assertIn(
                    "INV-218", line,
                    "the zero-exit-code rule must name the invariant that governs it; without a "
                    "citation a later editor cannot look the rule up, and conformance.py reports "
                    "it as an unregistered hard rule",
                )

    def test_the_post_update_probe_cites_inv218_not_inv129(self):
        hits = lines_stating(NOT_EVIDENCE)
        self.assertTrue(hits, "the post-update artifact probe instruction is gone")
        for line in hits:
            with self.subTest(line=line.strip()[:60]):
                self.assertIn("INV-218", line)
                self.assertNotIn(
                    "INV-129", line,
                    "INV-129 governs rendered deliverables (PDF, PNG, HTML), not an install. "
                    "Citing it here sends a reader to the wrong rule — the defect INV-218 was "
                    "registered to fix",
                )


class BothStatementsAreFoundWhenWrapped(unittest.TestCase):
    """Negative controls for the #424 conversion."""

    def test_each_wrapped_statement_is_found_at_its_first_line(self):
        for pattern, wrapped in (
                (ZERO_EXIT, "⛔ **A ZERO EXIT\nCODE FROM `brew` DOES NOT MEAN IT INSTALLED**.\n"),
                (NOT_EVIDENCE, "2. **Probe the platform artifact** — exit 0 is\nnot evidence.\n")):
            with self.subTest(pattern=pattern.pattern):
                self.assertEqual([wrapped.split("\n")[0]], lines_stating(pattern, wrapped))
                # The old line-at-a-time read, kept only to show the fixture is the hard case.
                self.assertFalse(any(pattern.search(l) for l in wrapped.split("\n")))


class TheTwoInvariantsStayDistinct(unittest.TestCase):
    """INV-129 must not be widened into the install case; that would be a meaning change."""

    def setUp(self):
        text = INVARIANTS.read_text(encoding="utf-8")
        self.inv129 = next(ln for ln in text.split("\n") if ln.startswith("- **INV-129**"))
        self.inv218 = next(ln for ln in text.split("\n") if ln.startswith("- **INV-218**"))

    def test_inv129_still_scopes_itself_to_rendered_deliverables(self):
        self.assertRegex(self.inv129, r"(?i)PDF, PNG, HTML")

    def test_inv218_covers_installing_or_updating(self):
        self.assertRegex(self.inv218, r"(?i)installs? or updates? software")

    def test_inv218_requires_a_platform_named_artifact(self):
        self.assertRegex(self.inv218, r"(?i)named for the Bootcamper's platform")

    def test_inv218_routes_an_unprobeable_case_to_inv163(self):
        self.assertRegex(self.inv218, r"(?i)undetermined")
        self.assertIn("INV-163", self.inv218)

    def test_inv218_states_the_boundary_with_inv129(self):
        """The pair is only safe while each says it is not the other."""
        self.assertIn("INV-129", self.inv218,
                      "INV-218 must name the sibling it is distinguished from, or the next "
                      "reader re-derives which one governs an install")


if __name__ == "__main__":
    unittest.main()
