"""The optional `fpdf2` dependency is declared, and its absence skips rather than fails.

Without `fpdf2`, 41 tests used to fail as domain assertions -- about certificate names, grid
alignment, label wrapping -- and only 6 named the missing package anywhere in their traceback.
The suite read as 41 product defects when the only defect was an unstated prerequisite. This
guard pins the three things that fixed it, so none can rot back.

⛔ **The renderers are not the subject and must not be changed.** `fpdf2` -> stdlib tiering is
deliberate shipped behavior: a bootcamper without `fpdf2` still gets a PDF, and the fallback
path ships and is tested. The defect was that the *tests* treated a documented fallback as a
failure.

⛔ **`@requires_fpdf2` must never reach a fallback test.** Several files here deliberately
exercise the stdlib renderer -- the path most bootcampers hit. Guarding those would silently
delete the coverage that matters most, and would do it while making the suite *greener*, which
is why nothing would notice. This file therefore checks that the guard is used, never that it
is used everywhere: no count and no file list is asserted, so adding or removing a guarded test
is a normal edit rather than a number to bump here.

⚠️ **What a green run means.** The dependency is declared, the helper exposes a working guard,
and the guard is in use. It does not mean every test that needs `fpdf2` carries it -- that
direction cannot be asserted without running the suite in both environments, which is the CI
matrix's job, not a unit test's.

⚠️ **Enforces INV-306.** It asserts the declaration in `requirements-dev.txt`, that the guard is
a skip rather than a failure, that the notice names cause and remedy and states no test count,
that at least one file actually applies the guard, and that both contributor-facing documents
name the manifest.

⚠️ It does **NOT** establish that the RIGHT tests are guarded. INV-306 requires that only
genuinely-needing tests carry the guard, because several files deliberately exercise the stdlib
fallback and guarding those would delete the coverage that matters most — judging which is which
is reading, not a regex. The two-cell CI run that exercises both paths is INV-305's.

Stdlib only (INV-108); the manifest and docs are read as text.

Source issue: #30.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
REQUIREMENTS = REPO_ROOT / "requirements-dev.txt"
DEV_DOCS = REPO_ROOT / "docs" / "development.md"
TESTS_README = TESTS_DIR / "README.md"
SUPPORT = TESTS_DIR / "_fpdf2_support.py"

#: A requirement line, ignoring comments and blanks.
REQUIREMENT = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)", re.M)


def declared_requirements():
    text = "\n".join(
        line for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#"))
    return {m.lower() for m in REQUIREMENT.findall(text)}


def files_using_the_guard():
    return sorted(
        p.name for p in TESTS_DIR.glob("test_*.py")
        if "@requires_fpdf2" in p.read_text(encoding="utf-8"))


class TheDependencyIsDeclared(unittest.TestCase):
    def test_the_manifest_exists(self):
        self.assertTrue(
            REQUIREMENTS.is_file(),
            "%s is gone. Nothing declares fpdf2, so the only way to learn it is needed is to "
            "watch tests fail for reasons that do not name it" % REQUIREMENTS)

    def test_fpdf2_is_declared(self):
        self.assertIn(
            "fpdf2", declared_requirements(),
            "fpdf2 is not declared in %s (found: %s). It is the one package the full suite "
            "needs" % (REQUIREMENTS, sorted(declared_requirements())))

    def test_reportlab_is_not_declared(self):
        """It was named in the original issue and is not used anywhere -- see #30's correction."""
        self.assertNotIn(
            "reportlab", declared_requirements(),
            "reportlab is declared in %s but nothing in this repo imports it; it appears only "
            "in a prose line listing PDF tools. Declaring it makes contributors install a "
            "package that changes nothing" % REQUIREMENTS)


class TheHelperProvidesAWorkingGuard(unittest.TestCase):
    def test_the_support_module_exists(self):
        self.assertTrue(SUPPORT.is_file(), "%s is gone; the guard has no home" % SUPPORT)

    def test_detection_agrees_with_the_interpreter(self):
        """The probe must track reality, or every guard built on it is decorative."""
        import _fpdf2_support
        self.assertEqual(
            importlib.util.find_spec("fpdf") is not None, _fpdf2_support.have_fpdf2(),
            "have_fpdf2() disagrees with whether fpdf is importable here")

    def test_the_guard_is_a_skip_not_a_failure(self):
        """The whole point: absence must skip. A guard that fails is the defect restated."""
        import _fpdf2_support

        class Probe(unittest.TestCase):
            @_fpdf2_support.requires_fpdf2
            def runTest(self):
                pass

        result = unittest.TestResult()
        Probe().run(result)
        self.assertEqual([], result.failures, "the guard produced a failure, not a skip")
        self.assertEqual([], result.errors, "the guard produced an error, not a skip")
        if not _fpdf2_support.have_fpdf2():
            self.assertEqual(
                1, len(result.skipped),
                "fpdf2 is absent, so the guarded test should have skipped; it did not")

    def test_the_notice_names_the_cause_and_the_remedy(self):
        import _fpdf2_support
        notice = _fpdf2_support._notice()
        self.assertIn("fpdf2", notice, "the notice does not name the missing package")
        self.assertIn(
            _fpdf2_support.INSTALL_HINT, notice,
            "the notice does not say how to fix it; a diagnostic without a remedy is half a "
            "diagnostic")

    def test_the_notice_states_no_test_count(self):
        """A hardcoded count rots on the next edit and teaches its reader to bump a number.

        The interpreter path is interpolated into the notice and routinely carries digits
        (`/tmp/claude-1001/...`, `python3.12`), so it is excised before scanning rather than
        special-cased -- an earlier version of this test scanned the whole string and failed
        on the path, not on the prose.
        """
        import _fpdf2_support
        prose = _fpdf2_support._notice().replace(sys.executable, "<python>")
        counts = re.findall(r"\d{2,}", prose)
        self.assertEqual(
            [], counts,
            "the notice hardcodes %s; state the condition and let the runner count skips"
            % counts)


class TheGuardIsActuallyUsed(unittest.TestCase):
    """INV-265 -- the checks above pass just as well if nothing ever applies the guard."""

    def test_some_test_file_uses_the_guard(self):
        users = files_using_the_guard()
        self.assertTrue(
            users,
            "no test file applies @requires_fpdf2. The helper exists and guards nothing, so "
            "the tests that need fpdf2 still fail as domain assertions when it is absent")

    def test_the_support_module_is_not_collected_as_a_test(self):
        """`_`-prefixed so neither `unittest discover` nor pytest picks it up."""
        self.assertFalse(
            SUPPORT.name.startswith("test"),
            "%s would be collected as a test module; its import-time notice would fire as part "
            "of collection and it would report as an empty test file" % SUPPORT.name)


class TheSetupIsDocumented(unittest.TestCase):
    def test_the_dev_docs_name_the_manifest(self):
        self.assertIn(
            "requirements-dev.txt", DEV_DOCS.read_text(encoding="utf-8"),
            "%s does not mention requirements-dev.txt; the install step is discoverable only "
            "by reading the test suite" % DEV_DOCS)

    def test_the_tests_readme_names_the_manifest(self):
        self.assertIn(
            "requirements-dev.txt", TESTS_README.read_text(encoding="utf-8"),
            "%s tells the reader how to run the suite but not what to install first"
            % TESTS_README)


if __name__ == "__main__":
    unittest.main()
