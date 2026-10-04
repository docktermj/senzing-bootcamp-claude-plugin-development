"""A "later porting phase" note must still be describing something that is missing.

The plugin carries ~37 honest deferrals — Kiro helpers and reference docs not yet ported,
each with an inline workaround so the flow never depends on the missing thing. Those are
fine. The failure mode is the *inverse*: the deferred thing lands, and the note saying it
hasn't stays behind, now telling the agent that something which exists does not.

That shipped. `module-07-query-visualize-discover/phase1-query-visualize.md` routed the
return-to-mapping path with "Load the Module 5 skill and begin at its Phase 2. (Module 5
port is a later phase; when it lands, route to its Phase 2 entry point.)" —
`module-05-data-quality-mapping/` had long since shipped with three phase files. The
agent was told its own destination did not exist, on the one path a Bootcamper reaches by
asking to go back and fix their mapping.

A deferral is self-invalidating evidence, which makes it cheap to check: whatever path it
names should NOT resolve. If it does, the note is stale. Two forms are checked — a named
file path, and a claim that a numbered module is unported when its skill directory is
right there.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

DEFERRAL = re.compile(
    r"later porting phase|later phase|is a later|not yet ported|when it lands|when .{1,40} is ported",
    re.IGNORECASE,
)

# Backticked tokens that look like a path rather than a bare identifier.
PATHISH = re.compile(r"`([A-Za-z0-9_./\-]+(?:/[A-Za-z0-9_.\-]+)+|[A-Za-z0-9_\-]+\.(?:py|md|sh|json|yaml))`")

# "Module 5 port is a later phase", "the Module 3 port is a later porting phase", ...
MODULE_PORT = re.compile(r"Module (\d)\b[^.]{0,40}?port\b", re.IGNORECASE)


def skill_files():
    for path in sorted((PLUGIN / "skills").rglob("*.md")):
        if "pytest_cache" in path.parts:
            continue
        yield path
    for path in sorted((PLUGIN / "commands").rglob("*.md")):
        yield path


def deferrals_in(text):
    """[(lineno, window)] for each deferral marker in ``text``, at the line it starts on.

    ⚠️ **The marker is matched across line wraps (#424).** ``match_lines`` runs ``DEFERRAL``
    on whitespace-collapsed Markdown blocks, so "a later\nphase" is found; read one line at a
    time it was not, and thirteen markers in shipped skills wrapped that way. The window is the
    start line with the line before it and the line after it: notes wrap, so a path can sit on
    the line above the marker, and a wrapped marker ends on the line below.
    """
    lines = text.split("\n")
    out = []
    for n in sorted(set(match_lines(text, DEFERRAL))):
        out.append((n, " ".join(lines[max(0, n - 2):n + 1])))
    return out


def deferral_lines():
    """Yield (path, lineno, text) for each deferral marker in the shipped skills."""
    for path in skill_files():
        for n, window in deferrals_in(path.read_text(encoding="utf-8", errors="replace")):
            yield path, n, window


class TestDeferralsStillDescribeSomethingMissing(unittest.TestCase):

    def test_no_deferral_names_a_path_that_now_exists(self):
        stale = []
        for path, lineno, text in deferral_lines():
            for ref in PATHISH.findall(text):
                # Deferral notes name plugin-root-relative or Kiro-relative paths.
                candidates = [PLUGIN / ref, PLUGIN / "scripts" / Path(ref).name]
                found = next((c for c in candidates if c.is_file()), None)
                if found is not None:
                    stale.append(
                        f"{path.relative_to(REPO_ROOT)}:{lineno} defers `{ref}`, but "
                        f"{found.relative_to(REPO_ROOT)} exists — the note is stale"
                    )
        self.assertEqual(
            [],
            stale,
            "Deferral note(s) describing something that has since shipped:\n  "
            + "\n  ".join(stale),
        )

    def test_no_deferral_claims_a_shipped_module_is_unported(self):
        stale = []
        for path, lineno, text in deferral_lines():
            for digit in MODULE_PORT.findall(text):
                shipped = sorted((PLUGIN / "skills").glob(f"module-0{digit}-*"))
                if shipped:
                    names = ", ".join(p.name for p in shipped)
                    stale.append(
                        f"{path.relative_to(REPO_ROOT)}:{lineno} says Module {digit} is "
                        f"not yet ported, but {names} ships"
                    )
        self.assertEqual(
            [],
            stale,
            "Deferral note(s) claiming a shipped module is unported — the defect that "
            "told the agent Module 5 did not exist:\n  " + "\n  ".join(stale),
        )

    def test_the_check_is_actually_scanning_deferrals(self):
        """If the marker regex stops matching, both tests pass vacuously."""
        found = list(deferral_lines())
        self.assertGreaterEqual(
            len(found),
            20,
            f"only {len(found)} deferral notes matched; DEFERRAL has probably drifted "
            "and these tests are now vacuous",
        )

    def test_a_wrapped_deferral_is_found_with_its_module(self):
        """Negative control (#424): "a later" ends line 2 and "phase" begins line 3."""
        wrapped = ("Return to mapping.\nLoad the Module 5 skill (the Module 5 port comes in a later\n"
                   "phase; route to its Phase 2 entry point once it ships).\n")
        found = deferrals_in(wrapped)
        self.assertEqual([2], [n for n, _window in found])
        self.assertEqual(["5"], MODULE_PORT.findall(found[0][1]))
        # The old line-at-a-time scan, kept only to show the fixture is the hard case.
        self.assertFalse(any(DEFERRAL.search(l) for l in wrapped.split("\n")))

    def test_the_known_regression_would_be_caught(self):
        """Self-check on the exact sentence that shipped."""
        regression = "(Module 5 port is a later phase; when it lands, route to its Phase 2 entry point.)"
        self.assertTrue(DEFERRAL.search(regression))
        self.assertEqual(["5"], MODULE_PORT.findall(regression))
        self.assertTrue(
            sorted((PLUGIN / "skills").glob("module-05-*")),
            "module-05 skill missing, so the regression check proves nothing",
        )


if __name__ == "__main__":
    unittest.main()
