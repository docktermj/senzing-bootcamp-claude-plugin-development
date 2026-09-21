"""A shipped comment naming a guarding test points at a file that exists and is plausible.

`capture_screenshots.py` carried a ⛔ comment above `_APPLICABILITY`, the Python mirror of the
app's `tabApplicable()`, saying "`tests/test_capture_tabs.py` asserts the two agree". It does
not. That file asserts the tab *inventory* against the contract's table and that the page
guards on applicability and presence; nothing in it compares the two rules.

The assertion the comment promised was real and strong, and lived in a **different** file:
`tests/test_capture_suppressed_tabs.py` → `test_python_rule_matches_the_apps_javascript_rule`,
which parses `tabApplicable()` out of the server and compares the gated tab set, the stats
field each gates on, and the literal thresholds.

A maintainer following the comment opened the named file, found only inventory assertions, and
would reasonably conclude the mirror was unguarded — then either duplicate the guard or edit
`_APPLICABILITY` believing nothing checked it, which is the "silent divergence" the comment
exists to prevent.

This is the mechanism **INV-184** was written from, one step milder. INV-184 records
`generate_discoveries_pdf.py` drifting *"while its own comment claimed a test asserted it"* —
there the coverage did not exist; here it does and only the pointer misdirects. A comment is
the reader's index into the suite, and a misdirecting index is trusted exactly as much as a
lying one.

Nothing detected it: `citations.py verify` resolves `INV-NNN` IDs, not test filenames, and a
plain existence check passes because `test_capture_tabs.py` does exist.

⛔ **WHAT THIS GUARD CANNOT DO.** It checks that a named test file exists and that it
*mentions* the symbol the comment is about. That a file references a symbol is **not** proof
it asserts the claimed property — a weak or vacuous assertion passes here. This catches a
pointer aimed at the wrong file; only reading catches a pointer aimed at a bad test.

Per **INV-246** the (source file → named test) pairs are derived by scanning shipped source,
never from a list — the defect was an author's belief about where an assertion lived, which is
the belief a hardcoded pair set would re-encode.

Source spec: `specs/mirror-comment-names-the-wrong-guarding-test.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
TESTS = REPO_ROOT / "tests"

#: A reference to a repo test file.
TEST_REFERENCE = re.compile(r"tests/(test_[a-z0-9_]+\.py)")

#: ⛔ A metasyntactic placeholder, not a pointer. `tests/test_x.py` inside an illustration of
#: what a path looks like is not naming a guarding test; it is a variable. Every real test file
#: here is a descriptive sentence and **none** is a single letter (measured: 0 of 299 when this
#: was widened), so the shape distinguishes them without a path allowlist that would go stale.
#:
#: ⚠️ Pinned in both directions below. Widening this scan to the whole repository surfaced
#: exactly three such placeholders and no real breakage, so the exclusion is what the widening
#: turns on — get it wrong in the strict direction and the guard fires on correct prose; wrong
#: in the loose direction and a real stale pointer named `test_q.py` escapes.
PLACEHOLDER = re.compile(r"^test_[a-z]\.py$")

#: Symbols a mirror comment is about. If the comment names one AND names a test file, that
#: test file must mention the symbol — otherwise the pointer sends the reader nowhere useful.
MIRROR_SYMBOLS = ("_APPLICABILITY", "tabApplicable", "_FALLBACK", "brand_tokens")

#: Non-vacuity floor: source known to reference a test when this guard was written. ⚠️ One per
#: root, so a root silently dropping out of the scan fails rather than shrinking the corpus.
KNOWN_REFERRERS = ("capture_screenshots.py", "test_review_invariants_queue.py",
                   "pending_invariants.py")

#: The placeholders the widening surfaced, and real pointers beside them. ⛔ INV-282: a matcher
#: pinned in one direction only gets relaxed until it stops firing.
NOT_POINTERS = ("test_x.py", "test_a.py", "test_b.py", "test_y.py")
ARE_POINTERS = ("test_capture_tabs.py", "test_review_invariants_queue.py",
                "test_one_commit_convention.py")

#: Folded in from `test_disclosure_pointers_resolve.py`, which this guard now subsumes (#96).
#: That file existed because #91 rewrote one docstring to name the guards covering each half of
#: INV-308; a version naming none would be unverifiable again, so the floor moves here rather
#: than being dropped with the file.
DISCLOSURE = REPO_ROOT / "tests" / "test_review_invariants_queue.py"


#: ⛔ Every root a maintainer reads, not just the one that ships (#96). The scan covered
#: `plugins/` alone until 2026-09-21, so a docstring under `tests/` or a skill under `.claude/`
#: could name a guard that does not exist and nothing noticed — and those are where pointers are
#: densest: 39 under `.claude/` and 83 under `tests/` against 22 under `plugins/`.
SCANNED_ROOTS = (PLUGIN, REPO_ROOT / "tests", REPO_ROOT / ".claude", REPO_ROOT / "docs")


def shipped_source():
    """Every script and Markdown file a maintainer reads, discovered rather than listed (INV-246)."""
    out = []
    for root in SCANNED_ROOTS:
        out += list(root.rglob("*.py")) + list(root.rglob("*.md"))
    return sorted(out)


def read(path):
    return path.read_text(encoding="utf-8")


def references():
    """[(shipped_path, referenced_test_name, the line)] across the whole shipped corpus."""
    out = []
    for path in shipped_source():
        if "__pycache__" in str(path):
            continue
        for n, line in enumerate(read(path).splitlines(), 1):
            for name in TEST_REFERENCE.findall(line):
                if PLACEHOLDER.match(name):
                    continue
                out.append((path, name, line, n))
    return out


class TheScanIsNotVacuous(unittest.TestCase):
    def test_shipped_source_is_actually_scanned(self):
        self.assertGreater(
            len(shipped_source()), 40,
            "the shipped-source sweep found almost nothing — this guard is inspecting an "
            "empty set and would pass forever")

    def test_the_known_referrer_is_still_found(self):
        referrers = {p.name for p, _n, _l, _i in references()}
        for known in KNOWN_REFERRERS:
            with self.subTest(file=known):
                self.assertIn(
                    known, referrers,
                    "%s no longer references a repo test, so this guard is inspecting a "
                    "smaller set than it believes" % known)


class ThePlaceholderRuleIsCalibrated(unittest.TestCase):
    """⛔ The widening turns on this: three placeholders, no real breakage (#96)."""

    def test_placeholders_are_not_treated_as_pointers(self):
        for name in NOT_POINTERS:
            with self.subTest(name=name):
                self.assertTrue(
                    PLACEHOLDER.match(name),
                    "%r is a metasyntactic placeholder used in illustrations here; treating it "
                    "as a pointer makes this guard fire on correct prose" % name)

    def test_real_test_names_are_not_treated_as_placeholders(self):
        for name in ARE_POINTERS:
            with self.subTest(name=name):
                self.assertFalse(
                    PLACEHOLDER.match(name),
                    "%r is a real guard file; excluding it would let a stale pointer to it "
                    "escape, which is the whole property" % name)


class EveryRootIsActuallyScanned(unittest.TestCase):
    """⚠️ #96 exists because a scan covered one root while its consumers assumed four."""

    def test_each_root_contributes_files(self):
        for root in SCANNED_ROOTS:
            with self.subTest(root=root.name):
                found = [f for f in shipped_source() if root in f.parents or f.parent == root]
                self.assertTrue(
                    found,
                    "no files found under %s, so pointers there are unchecked while this guard "
                    "reports clean" % root)

    def test_pointers_are_found_outside_the_shipped_plugin(self):
        """⛔ The floor that would have failed before #96: 0 pointers outside `plugins/`."""
        outside = [r for r in references() if PLUGIN not in r[0].parents]
        self.assertGreater(
            len(outside), 20,
            "fewer than 20 test pointers found outside the shipped plugin. Before #96 this scan "
            "read `plugins/` alone and would have reported 0 here while 122 pointers sat under "
            "`tests/` and `.claude/`")

    def test_the_inv308_disclosure_still_names_its_guards(self):
        """Folded in from the guard this one subsumes; a disclosure naming none is unverifiable."""
        named = {n for n in TEST_REFERENCE.findall(read(DISCLOSURE)) if not PLACEHOLDER.match(n)}
        self.assertGreaterEqual(
            len(named), 4,
            "%s names fewer than four guard files. #91 rewrote its INV-308 disclosure to name "
            "the guards covering each half; a version naming none has lost what makes it "
            "checkable rather than merely believable" % DISCLOSURE.name)


class EveryNamedTestResolves(unittest.TestCase):
    def test_every_referenced_test_file_exists(self):
        missing = []
        for path, name, _line, n in references():
            if not (TESTS / name).is_file():
                missing.append("%s:%d names tests/%s, which does not exist"
                               % (path.relative_to(REPO_ROOT), n, name))
        self.assertEqual(
            [], missing,
            "shipped source names a repo test that is not there — the reader is sent to a "
            "guard that does not exist (the INV-184 mechanism):\n  " + "\n  ".join(missing))

    def test_a_mirror_pointer_names_a_test_that_mentions_the_symbol(self):
        """The half that caught the real defect: right file, wrong file, or padding."""
        wrong = []
        for path, name, line, n in references():
            target = TESTS / name
            if not target.is_file():
                continue  # covered by the test above
            symbols = [s for s in MIRROR_SYMBOLS if s in line]
            if not symbols:
                continue
            body = read(target)
            for symbol in symbols:
                if symbol not in body:
                    wrong.append(
                        "%s:%d claims tests/%s guards %s, but that file never mentions it"
                        % (path.relative_to(REPO_ROOT), n, name, symbol))
        self.assertEqual(
            [], wrong,
            "a comment points the reader at a test that does not touch the symbol the "
            "comment is about. The reader concludes the code is unguarded and either "
            "duplicates the guard or edits freely:\n  " + "\n  ".join(wrong))


class TheRepairedPointerStaysSpecific(unittest.TestCase):
    def test_the_mirror_comment_names_the_asserting_file_and_method(self):
        text = re.sub(r"\s+", " ", read(PLUGIN / "scripts" / "capture_screenshots.py"))
        self.assertIn(
            "tests/test_capture_suppressed_tabs.py", text,
            "the _APPLICABILITY mirror comment no longer names the file that actually "
            "asserts the two rules agree")
        self.assertIn(
            "test_python_rule_matches_the_apps_javascript_rule", text,
            "the comment names the file but not the method, so the claim cannot be checked "
            "at a glance — which is what let the wrong file stand")


if __name__ == "__main__":
    unittest.main()
