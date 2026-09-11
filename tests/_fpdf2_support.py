"""Shared detection of the optional ``fpdf2`` renderer, and a single notice when it is absent.

The shipped PDF generators (``generate_recap_pdf.py``, ``generate_discoveries_pdf.py``) tier
their renderers: ``fpdf2`` when importable, a stdlib fallback otherwise. **That tiering is
deliberate product behavior** -- a bootcamper without ``fpdf2`` still gets a PDF -- and nothing
here is trying to change it.

What was wrong is how the *tests* reported its absence. Tests that measure the fpdf2 renderer's
output ran anyway against the fallback, which lays out pages differently, and failed as domain
assertions about certificate names, grid alignment and label wrapping. 41 of them, of which only
6 named the missing package anywhere in their traceback. The suite read as 41 product defects
when the only defect was an unstated prerequisite.

⛔ **Only guard tests that genuinely need the fpdf2 renderer.** Several files in this suite
deliberately exercise the *stdlib fallback* -- that path ships too, and is the one most
bootcampers hit. Decorating those with ``@requires_fpdf2`` would silently delete the coverage
that matters most. The guards were applied against a measured list of failing test ids, not
file by file.

⚠️ **Why this is a module and not a ``conftest.py``.** INV-108 requires dev-only tests to rely
only on the standard library and to run via ``python3 -m unittest discover -s tests``, and 250
test docstrings repeat that runner. ``conftest.py`` is a pytest concept: under the documented
runner it is never loaded, so the "report once" guarantee would quietly not hold for anyone
following ``tests/README.md``. A module's top level runs once per process under both runners.

The notice deliberately carries **no test count**. A hardcoded number rots on the next
legitimate addition and teaches its reader to bump it -- the habit
``test_documented_commands_match_the_shipped_set.py`` refuses by name. The condition and its
consequence are stated; counting skips is the runner's job.

Stdlib only (INV-108): availability is probed with ``importlib.util.find_spec``, which does not
import the package.

Source issue: #30.
"""
import importlib.util
import os
import sys
import unittest

#: Set this to any non-empty value to suppress the notice (for tooling that parses output).
SILENCE_ENV_VAR = "SBCP_QUIET_FPDF2_NOTICE"

#: How to get the renderer, named once so the notice and the docs cannot drift apart.
INSTALL_HINT = "python3 -m pip install -r requirements-dev.txt"


def have_fpdf2():
    """True when ``fpdf2`` is importable by the interpreter running the tests.

    ``find_spec`` rather than a ``try: import`` so a probe never pulls the package into memory
    for the many tests that do not need it.
    """
    return importlib.util.find_spec("fpdf") is not None


def _notice():
    return (
        "\n"
        + "=" * 78 + "\n"
        + "fpdf2 is not installed for %s\n" % sys.executable
        + "\n"
        + "The tests that measure the fpdf2-rendered PDF will be SKIPPED. They are not\n"
        + "failing: the stdlib fallback renderer lays out pages differently, so their\n"
        + "assertions do not describe it. The fallback's own tests still run.\n"
        + "\n"
        + "    %s\n" % INSTALL_HINT
        + "=" * 78 + "\n"
    )


def _announce_once():
    """Write the notice to stderr, once per process, when fpdf2 is absent."""
    if have_fpdf2() or os.environ.get(SILENCE_ENV_VAR):
        return
    sys.stderr.write(_notice())
    sys.stderr.flush()


_announce_once()


#: Decorator for a test (or TestCase) that measures the fpdf2 renderer specifically.
#:
#: Do NOT apply this to a test of the stdlib fallback -- that path ships and must keep running
#: without fpdf2 installed.
requires_fpdf2 = unittest.skipUnless(
    have_fpdf2(),
    "fpdf2 is not installed; this test measures the fpdf2 renderer, not the stdlib fallback "
    "(%s)" % INSTALL_HINT,
)
