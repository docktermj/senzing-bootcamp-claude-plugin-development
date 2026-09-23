"""The drift detector compares the right span, and says what it could not compare.

`implement-github-issue` has two `SKILL.md` files -- one here, one under `~/.claude/skills/`
that the maintainer uses in other repositories. On 2026-09-23 they were found **two amendments
apart**: #119 and #124 edited only the user-level copy while this repository's copy, the one
that ships to the four child ports, sat at its original text. Nothing detected it, and the
repository copy carried a note claiming it governed -- which measurement disproved.

⛔ **The detector's subject is the DELIMITED block, not the files.** Everything outside
`SHARED-RULES` may legitimately differ: this repository's copy cites `docs/FAMILY_WORKFLOW.md`
and `specs/INVARIANTS.md`, which do not exist in the repositories the other copy serves.
Requiring the files to be identical would either break that copy elsewhere or strip the
citations that make the rule enforceable here. `OnlyTheBlockIsCompared` pins that distinction,
because "make them the same" is the fix a later reader will reach for.

⚠️ **The live comparison SKIPS where `~/.claude/skills/` is absent**, which is every CI runner.
A test that read a path outside the repository would fail there and pass only on one machine --
the trap INV-308 names, and one this repository has already hit. So the detector's *logic* is
tested against fixtures, which run everywhere, and the live check is reported as skipped with
its reason rather than quietly not running.

⚠️ **What this does NOT establish:** that the two copies are in fact in sync on any given
machine, that a commit outside a Claude Code session was seen, or that a user-level edit was
noticed. The detector prints those limits on every run; this module only checks that it does.

Source issue: #128.

Stdlib only.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import io
import contextlib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DETECTOR = REPO_ROOT / ".claude" / "skills" / "check-skill-drift" / "skill_drift.py"
SKILL = REPO_ROOT / ".claude" / "skills" / "implement-github-issue" / "SKILL.md"
USER_SKILLS = Path.home() / ".claude" / "skills"

BEGIN = "<!-- SHARED-RULES:BEGIN"
END = "<!-- SHARED-RULES:END -->"


def detector():
    spec = importlib.util.spec_from_file_location("skill_drift", DETECTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(tmp, text):
    tmp.write_text(text, encoding="utf-8")
    return tmp


class TheBlockPatternReadsWhatItShould(unittest.TestCase):
    def test_it_extracts_a_delimited_block(self):
        mod = detector()
        p = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "S.md"
        write(p, "before\n%s -->\nrules\n%s\nafter\n" % (BEGIN, END))
        got = mod.shared_block(p)
        self.assertIsNotNone(got)
        self.assertIn("rules", got)
        self.assertNotIn("before", got, "the block must not swallow text ahead of the marker")
        self.assertNotIn("after", got, "the block must not swallow text past the end marker")

    def test_a_file_without_the_block_reads_as_none(self):
        mod = detector()
        p = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "S.md"
        write(p, "a skill with no shared block at all\n")
        self.assertIsNone(mod.shared_block(p))

    def test_a_missing_file_reads_as_none_rather_than_raising(self):
        mod = detector()
        self.assertIsNone(mod.shared_block(Path("/nonexistent/SKILL.md")))

    def test_two_blocks_do_not_merge_into_one(self):
        """⛔ A greedy match would swallow everything between two blocks and compare noise."""
        mod = detector()
        p = Path(self.enterContext(__import__("tempfile").TemporaryDirectory())) / "S.md"
        write(p, "%s -->\nfirst\n%s\nMIDDLE\n%s -->\nsecond\n%s\n" % (BEGIN, END, BEGIN, END))
        got = mod.shared_block(p)
        self.assertNotIn("MIDDLE", got,
                         "the pattern is greedy and merged two blocks; it would then compare "
                         "text that is not the shared rules at all")


class OnlyTheBlockIsCompared(unittest.TestCase):
    """⛔ The repo copy MUST be free to cite files the other copy's repositories lack."""

    def test_the_repo_copy_cites_files_outside_the_shared_block(self):
        text = SKILL.read_text(encoding="utf-8")
        block = detector().shared_block(SKILL)
        self.assertIsNotNone(block, "the repo skill has no SHARED-RULES block")
        for citation in ("docs/FAMILY_WORKFLOW.md", "specs/INVARIANTS.md"):
            with self.subTest(citation=citation):
                self.assertIn(citation, text,
                              "%s should be cited by this repository's copy" % citation)
                self.assertNotIn(
                    citation, block,
                    "%s is INSIDE the shared block. The other copy serves repositories that do "
                    "not have that file, so the block could never be byte-identical and the "
                    "detector would report permanent drift" % citation)


class ItSaysWhatItCouldNotCompare(unittest.TestCase):
    """INV-308 — the two blind spots are printed, not left for the reader to infer."""

    def report(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            detector().main([])
        return buf.getvalue()

    def test_the_report_names_both_blind_spots(self):
        out = self.report()
        for phrase in ("outside a Claude Code session", "no repository event"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, out,
                              "the detector's output does not state the limit %r, so a clean "
                              "result reads as coverage it does not have" % phrase)

    def test_it_does_not_claim_to_close_the_window(self):
        self.assertIn("does not close it", self.report())


class TheLiveComparison(unittest.TestCase):
    def test_the_two_copies_agree_on_this_machine(self):
        if not USER_SKILLS.is_dir():
            self.skipTest(
                "%s does not exist here, so the live comparison COULD NOT RUN -- distinct from "
                "having run and found nothing (INV-308). Every CI runner takes this path, which "
                "is why the detector's logic is tested against fixtures above" % USER_SKILLS)
        mod = detector()
        drifted, checked, _ = mod.compare()
        self.assertTrue(checked, "no skill pair carried a SHARED-RULES block, so nothing was "
                                 "compared and this assertion is vacuous (INV-265)")
        self.assertEqual([], [d[0] for d in drifted],
                         "SHARED-RULES has drifted for: %s" % ", ".join(d[0] for d in drifted))


if __name__ == "__main__":
    unittest.main()
