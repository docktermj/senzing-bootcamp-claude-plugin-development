"""A disclosure naming the guards that cover a rule points at test files that exist.

`tests/test_review_invariants_queue.py` carried, from #59 until 2026-09-21, the claim that
**nothing** asserts INV-308 of this repository's other verification tools. Five guards landed
across #74, #76, #77, #80 and #83 and the sentence was never swept, so it **understated** coverage
— the direction that costs work, because it sends the next reader to build what already exists
(#91).

The fix names the guards that closed each half. ⛔ **That trades one staleness risk for another**:
a prose pointer to `tests/x.py` is the audit skill's defect class 6 — *a comment claiming a test
exists that does not* — which has a real instance on record, where `capture_screenshots.py` named
a file whose assertions were somewhere else entirely.

⚠️ **`tests/test_comment_test_pointers_resolve.py` already guards this class, for `plugins/`
only.** It globs `PLUGIN.rglob`, so a docstring under `tests/` naming a missing file is
unguarded. Widening that scan is the general fix and is deliberately **not** done here: it is the
same narrow-scan class as #77 and #92 and deserves its own issue rather than riding along in a
docstring correction.

⛔ **This asserts existence and nothing more.** That a named file *exists* does not establish that
it asserts what the disclosure says it asserts — only reading does. The pointer guard this
complements makes the same distinction, and the stronger claim is not available to a test.

Stdlib only; the disclosure is read as text (INV-108).

Source issue: #91.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS = REPO_ROOT / "tests"

#: The docstring that names guards. Scoped to the one disclosure #91 rewrote rather than to every
#: file under `tests/` — a wider scan is the right fix and is a separate decision, so this does
#: not quietly half-do it.
DISCLOSURE = TESTS / "test_review_invariants_queue.py"

#: Any `tests/<name>.py` named in prose.
POINTER = re.compile(r"`tests/(test_[a-z0-9_]+\.py)`")


def named_files():
    return sorted(set(POINTER.findall(DISCLOSURE.read_text(encoding="utf-8"))))


class TheDisclosureNamesRealFiles(unittest.TestCase):
    def test_the_disclosure_is_where_this_test_expects(self):
        """INV-265 — every assertion below reads this file, so it must be the real one."""
        self.assertTrue(
            DISCLOSURE.is_file(),
            "%s is gone; re-anchor this test rather than letting it pass on a missing file"
            % DISCLOSURE)

    def test_it_names_some_guards_at_all(self):
        """⛔ An empty pointer list would make the assertion below pass over nothing."""
        self.assertGreaterEqual(
            len(named_files()), 4,
            "fewer than four guard files are named in %s. #91 rewrote its INV-308 disclosure to "
            "name the guards that closed each half; a version naming none has lost the thing "
            "that makes it checkable rather than merely believable" % DISCLOSURE.name)

    def test_every_named_guard_exists(self):
        missing = [n for n in named_files() if not (TESTS / n).is_file()]
        self.assertEqual(
            [], missing,
            "a disclosure names guard file(s) that do not exist: %s. A reader following the "
            "pointer finds nothing and reasonably concludes the rule is unguarded -- then "
            "duplicates the guard or edits the rule. That is the recorded failure of this class"
            % ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
