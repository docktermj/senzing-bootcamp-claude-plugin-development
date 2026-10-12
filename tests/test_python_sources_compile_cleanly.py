"""Every Python file in the repo compiles from SOURCE with no warning.

`tests/test_sdk_update_offer.py:175` carried an invalid escape sequence -- ``\\```` inside a
docstring -- for an unknown length of time. Today that is a ``SyntaxWarning``; Python has
scheduled it to become a ``SyntaxError``, at which point the file stops importing and the
suite stops running.

⛔ **THE SUITE WAS GREEN OVER IT, AND THAT IS THE POINT OF THIS FILE.** A ``SyntaxWarning``
fires when a module is **compiled**, not when a cached one is **imported**. Once
``__pycache__`` holds a ``.pyc``, every later run is silent. The warning surfaced only when an
unrelated one-line docstring edit (`d35046d`) invalidated the cached bytecode and forced a
recompile -- so the defect was found by accident, on a run that happened to touch the file.

⛔ **THIS GUARD MUST COMPILE SOURCE TEXT, NEVER IMPORT.** Importing is exactly what hid the
defect: an import prefers cached bytecode and emits nothing. If a later change "simplifies"
this into an import check, or into ``py_compile`` without ``doraise``/cache invalidation, the
blind spot returns intact and this file will report success while saying nothing.

Why it matters beyond one test file: `plugins/senzing-bootcamp/scripts/*.py` **ship to
bootcampers** and run under whatever Python they have, hooks are Python 3 exec-form
(**INV-052**) and the offline suite is stdlib Python (**INV-108**). A latent ``SyntaxError``
in a shipped script is a broken deliverable, which makes this **INV-004** (production-ready).

Nothing else in the repo could see this class: the suite imports, and `conformance.py`,
`citations.py` and `coverage_reports.py` all read files as text.
(`specs/bytecode-caching-hides-a-latent-syntax-error-from-the-suite.md`)

⛔ **WHAT THIS GUARD CANNOT SEE.** It proves the files *compile* cleanly under the Python
running the suite. It does not prove they run correctly, and it cannot prove behavior under
a future Python that has already promoted the warning to an error -- it only ensures the repo
is clean when that lands. A clean run is a statement about syntax, not about correctness.

Run:  python3 -m unittest discover -s tests
"""
import unittest
import warnings
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Roots scanned, derived by walking each rather than listing files (INV-246). A file added
#: to any of these tomorrow is covered without anyone remembering to add it here.
ROOTS = ("tests", "plugins", ".claude", "scripts")

#: Compile-time categories that indicate a real defect. `DeprecationWarning` is included
#: because it is the other diagnostic Python raises at compile time for constructs it has
#: scheduled for removal.
FATAL = (SyntaxWarning, DeprecationWarning)


def python_sources():
    """Every `.py` under the scanned roots, discovered rather than listed (INV-246)."""
    found = []
    for root in ROOTS:
        found.extend(corpus_files(root, suffixes={".py"}))
    return found


def compile_from_source(path):
    """Compile `path` from its TEXT, returning any compile-time diagnostics.

    Reads and compiles rather than importing, so `__pycache__` cannot mask the result --
    see this module's docstring for why that distinction is the whole guard.
    """
    source = path.read_text(encoding="utf-8", errors="replace")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            compile(source, str(path), "exec")
        except SyntaxError as exc:
            return ["SyntaxError: %s (line %s)" % (exc.msg, exc.lineno)]
        return ["%s: %s (line %s)" % (w.category.__name__, w.message, w.lineno)
                for w in caught if issubclass(w.category, FATAL)]


class EveryPythonSourceCompilesCleanly(unittest.TestCase):
    def test_the_scan_reaches_a_meaningful_number_of_files(self):
        """Membership floor: an empty or collapsed scan would pass the check below vacuously."""
        sources = python_sources()
        self.assertGreater(
            len(sources), 100,
            "the Python-source scan collapsed (%d files); the compile check below would "
            "pass without compiling anything" % len(sources))

    def test_the_python_bearing_roots_all_contribute(self):
        """A floor per root that actually holds Python, so a moved root cannot drop out silently.

        ⚠️ `scripts/` is deliberately NOT floored: at the repo root it holds only shell
        (`sync-check.sh`) today. It stays in `ROOTS` so a `.py` added there tomorrow is
        scanned — flooring it would assert something currently false, and a guard that
        asserts a falsehood gets "fixed" by deleting the assertion.
        """
        sources = python_sources()
        for root in ("tests", "plugins", ".claude"):
            base = REPO_ROOT / root
            with self.subTest(root=root):
                self.assertTrue(base.exists(), "%s/ moved" % root)
                self.assertTrue(
                    any(p.is_relative_to(base) for p in sources),
                    "no Python files found under %s/ — the root moved or the scan broke" % root)

    def test_scripts_is_scanned_even_though_it_holds_no_python_today(self):
        """If that changes, this test is the record that the coverage was intentional."""
        self.assertIn("scripts", ROOTS,
                      "scripts/ dropped out of the scanned roots; a .py added there would "
                      "compile unchecked")

    def test_no_source_emits_a_compile_time_diagnostic(self):
        offenders = []
        for path in python_sources():
            for problem in compile_from_source(path):
                offenders.append("%s — %s" % (path.relative_to(REPO_ROOT), problem))
        self.assertEqual(
            [], offenders,
            "these files do not compile cleanly from source. A SyntaxWarning today is a "
            "SyntaxError in a future Python, and bytecode caching means the rest of the "
            "suite will not tell you:\n  " + "\n  ".join(offenders))


class TheGuardCompilesRatherThanImports(unittest.TestCase):
    """Its own mechanism is asserted, because the mechanism IS the guard.

    An import-based version of this file would pass on a repo containing the very defect it
    exists to catch. That is not a hypothetical: it is what every other check in this repo
    did, for as long as the escape sat in `test_sdk_update_offer.py`.
    """

    def setUp(self):
        self.doc = " ".join((__doc__ or "").split())

    def test_the_detector_catches_a_synthetic_bad_source(self):
        """Exercised on synthetic text, not the repo: the repo is now clean, so asserting
        that the scan finds offenders would be asserting the defect still exists."""
        bad = REPO_ROOT / "tests" / "__does_not_exist__.py"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            compile('x = "\\d"\n', str(bad), "exec")
            self.assertTrue(
                any(issubclass(w.category, FATAL) for w in caught),
                "compiling an invalid escape from source no longer raises a diagnostic — "
                "this guard's detection mechanism has stopped working")

    def test_the_import_blind_spot_is_disclosed(self):
        self.assertRegex(
            self.doc, r"(?i)MUST COMPILE SOURCE TEXT, NEVER IMPORT",
            "the docstring no longer warns against turning this into an import check, which "
            "is the change that would silently restore the blind spot")

    def test_the_scope_limit_is_disclosed(self):
        self.assertRegex(
            self.doc, r"(?i)a statement about syntax, not about correctness",
            "the docstring no longer bounds what a clean run means")


if __name__ == "__main__":
    unittest.main()
