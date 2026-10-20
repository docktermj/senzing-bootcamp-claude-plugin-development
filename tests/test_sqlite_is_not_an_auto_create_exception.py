"""No shipped file says the SDK auto-creates a SQLite database or its schema (#743).

Module 2 Step 7's PostgreSQL branch said the SDK does not auto-create the schema
"(unlike SQLite)". The live Senzing MCP server retracts that in so many words --
"SQLite is **not** a special case -- it needs its schema applied first, exactly like
PostgreSQL, MySQL and MSSQL", verified against SDK 4.4.2.26272 and re-asked on server
1.39.1, 2026-10-20 -- and Step 7's own SQLite branch, 138 lines earlier in the same
file, already said the same thing. A Bootcamper whose guide read the later sentence
skips the schema and fails at Step 9 with SENZ1001 (14: unable to open database file),
which reads as a path or permissions fault.

The claim is about SQLite, so this guard is about SQLite: it looks for a sentence that
exempts SQLite from a not-auto-created rule, or asserts the SDK creates the file or its
schema. The one genuine exception the server names -- ``senzingsdk-poc``'s
``sz_create_project``, which does all three rungs -- is allowed, by name, because the
server names it; a sentence that claims the exception for the SDK itself is not.

⚠️ This asserts what the shipped text SAYS. It **cannot** establish that a live run
applies the schema, which only an execution test or ``dry-run`` phase 2 observes, and it
asserts nothing about Senzing: the suite is offline (INV-108) and the server is the
authority on the fact (INV-080).
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks, line_of

#: Sentences that exempt SQLite from the schema rule, or hand the creation to the SDK.
#: Derived from the claim (INV-282): the defect is an EXEMPTION for SQLite, so the match
#: needs SQLite plus an exempting or auto-creating verb in the same collapsed block.
_SQLITE = re.compile(r"(?i)\bsqlite\b")
_EXEMPTS = re.compile(
    r"(?i)unlike sqlite"
    r"|sqlite (?:is|was) (?:an? )?(?:exception|special case)"
    r"|except (?:for )?sqlite"
    r"|sqlite,? which (?:is|does) auto"
)
_AUTO_CREATES = re.compile(
    r"(?i)(?:sdk|engine|configuration step|config step) [^.]{0,80}"
    r"(?:auto-?creat|creates and (?:initiali[sz]es|populates))[^.]{0,60}sqlite"
    r"|sqlite [^.]{0,60}(?:is |are )?auto-?created by the (?:sdk|engine)"
)

#: The server's one named exception, so a sentence stating it is not a defect.
_POC_EXCEPTION = re.compile(r"(?i)senzingsdk-poc|sz_create_project")


def _offenders(paths):
    out = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not _SQLITE.search(text):
            continue
        for flat, origin in collapsed_blocks(text):
            for pattern in (_EXEMPTS, _AUTO_CREATES):
                hit = pattern.search(flat)
                if hit and not _POC_EXCEPTION.search(flat):
                    out.append((path, line_of(origin, hit.start()), hit.group(0)[:60]))
                    break
    return out


class NoShippedFileExemptsSqlite(unittest.TestCase):
    def setUp(self):
        self.shipped = corpus_files("plugins", suffixes=(".md", ".py"))

    def test_the_scan_reaches_the_file_the_defect_was_in(self):
        """A floor, so a clean result cannot come from an empty corpus (INV-265)."""
        names = {p.name for p in self.shipped}
        self.assertIn("SKILL.md", names)
        self.assertGreater(len(self.shipped), 30, "the shipped scan collapsed to almost nothing")

    def test_no_shipped_file_exempts_sqlite(self):
        found = _offenders(self.shipped)
        self.assertEqual(
            [], found,
            "a shipped file exempts SQLite from the schema rule the server says applies to it "
            "equally (INV-080):\n"
            + "\n".join("  %s:%d  %s" % (p, n, t) for p, n, t in found))


class TheControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs the SAME function over mutated shipped text."""

    def setUp(self):
        self.path = (Path(__file__).resolve().parent.parent / "plugins" / "senzing-bootcamp"
                     / "skills" / "module-02-sdk-setup" / "SKILL.md")

    def _reported(self, text, tmp):
        tmp.write_text(text, encoding="utf-8")
        return _offenders([tmp])

    def test_the_pre_743_wording_is_reported(self):
        """The exact sentence this issue removes must fail the guard."""
        import tempfile
        text = self.path.read_text(encoding="utf-8")
        pre = text.replace(
            "the SDK does NOT auto-create it.",
            "the SDK does NOT auto-create it\n   (unlike SQLite).", 1)
        self.assertNotEqual(pre, text, "the corrected sentence was not found to mutate")
        with tempfile.TemporaryDirectory() as d:
            found = self._reported(pre, Path(d) / "SKILL.md")
        self.assertTrue(found, "the pre-#743 wording is not reported; the control is vacuous")

    def test_the_servers_named_exception_is_not_reported(self):
        """`senzingsdk-poc`'s sz_create_project IS the exception; it must not flag."""
        import tempfile
        allowed = ("The `senzingsdk-poc` package's `sz_create_project` would do all three rungs, "
                   "so SQLite is an exception there and only there.")
        with tempfile.TemporaryDirectory() as d:
            found = self._reported(allowed, Path(d) / "note.md")
        self.assertEqual([], found, "the server's own named exception was reported as a defect")

    def test_the_shipped_sqlite_rule_is_not_reported(self):
        """Step 7's correct statement must not flag -- it says the opposite."""
        import tempfile
        correct = ("⛔ **SQLite is not \"no setup\". The database file is not auto-created and its "
                   "schema is not auto-applied** — the same as PostgreSQL, and for the same reason.")
        with tempfile.TemporaryDirectory() as d:
            found = self._reported(correct, Path(d) / "note.md")
        self.assertEqual([], found, "the correct shipped rule was reported as a defect")


if __name__ == "__main__":
    unittest.main()
