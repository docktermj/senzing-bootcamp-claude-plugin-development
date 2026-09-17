"""The INV-282 reverse check never reports clean over lines it could not reach.

The check has two halves that read different corpora: `since` diffs `SCAN_ROOTS`, and
`per-rule` reads `shipped_markdown()` — the plugin alone. The procedure in
`unattended-issue-loop/SKILL.md` took every line from the first and tested membership against
the second, so ⛔ **a rule added under the maintainer surface could never appear in the result.**
Measured against `7b43eee`: 112 lines in, **0** reported, 0 occurrences of `.claude/` in a 43 KB
`--uncited` corpus. 93 of those 112 cite nothing. The set difference reported clean over rules
it could not see.

⚠️ **A second defect in the same script, found while fixing the first.** Its comparison key
stripped the stop sign from the whole line while `per-rule` prints the line with it, so a rule
whose ⛔ sits mid-line stopped matching: **44 of 333** such lines were missed inside the corpus
the script did cover. The gate in `test_new_hard_rules_are_cited_or_deferred.py` had already hit
this and strips the sign from **both** sides; the loop's copy never got that fix. Both defects
are gone because the view asks each line's own file whether an invariant is cited at it, rather
than matching one report's rendered text against another's.

⛔ **The fix is NOT to widen `per-rule`.** Its corpus carries ~165 restatement lines under the
maintainer surface — command files restate the rules of the skills they front, by design — and
adding them to a worklist whose own skill warns these are leads would bury the real ones. What
was wrong is a check spanning two corpora *silently*.

⚠️ **So `UNTESTED` is not a failure state and must not be read as one.** It is the honest name
for a span the check does not cover, and the reason the word `clean` is reserved for a run that
tested everything it reported.

Built on throwaway git repositories: this repository's own history cannot produce a range with
an uncited plugin rule, an untested maintainer-surface rule and a clean range on demand.

Stdlib only; the maintainer script is loaded by path, never imported as a package (INV-108).

Source issue: #80.

Run:  python3 -m unittest discover -s tests
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude/skills/production-readiness-audit/conformance.py"
LOOP_SKILL = REPO_ROOT / ".claude/skills/unattended-issue-loop/SKILL.md"
LOOP_COMMAND = REPO_ROOT / ".claude/commands/unattended-issue-loop.md"
AUDIT_SKILL = REPO_ROOT / ".claude/skills/production-readiness-audit/SKILL.md"

CITED = "- ⛔ **Never ship a rule with no invariant.** (INV-183)\n"
UNCITED = "- ⛔ **Never ship a rule that cites nothing at its own line.**\n"


def git(repo, *args):
    done = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError("git %s failed in fixture: %s" % (" ".join(args), done.stderr))
    return done.stdout.strip()


def build(tmp, plugin_lines="", surface_lines=""):
    """A repo with one commit to diff against, then the given rules added on top."""
    repo = Path(tmp)
    git(repo, "init", "--quiet", "--initial-branch", "main")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "fixture")
    git(repo, "config", "commit.gpgsign", "false")
    plugin = repo / "plugins" / "senzing-bootcamp" / "skills" / "demo"
    plugin.mkdir(parents=True)
    (plugin / "SKILL.md").write_text("# demo\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "chore: baseline")
    base = git(repo, "rev-parse", "--short", "HEAD")
    if plugin_lines:
        (plugin / "SKILL.md").write_text("# demo\n\n" + plugin_lines, encoding="utf-8")
    if surface_lines:
        surface = repo / ".claude" / "commands"
        surface.mkdir(parents=True)
        (surface / "demo.md").write_text("# demo command\n\n" + surface_lines, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "-m", "feat: the rules under test")
    return repo, base


def check(repo, base):
    done = subprocess.run(
        [sys.executable, str(CONFORMANCE), "--repo", str(repo), "reverse-check", "--ref", base],
        capture_output=True, text=True, cwd=str(repo))
    if done.returncode != 0:
        raise AssertionError("reverse-check exited %d: %s" % (done.returncode, done.stderr))
    return done.stdout


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class LinesOutsideTheTestedCorpusAreCounted(unittest.TestCase):
    """⛔ The defect: they were neither tested nor counted, and the result read as clean."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reverse-check-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_an_uncited_maintainer_surface_rule_is_named_as_untested(self):
        repo, base = build(self.tmp, surface_lines=UNCITED)
        out = check(repo, base)
        self.assertRegex(
            out, r"UNTESTED 1 line\(s\)",
            "a hard rule added under the maintainer surface was not counted as untested. The "
            "old procedure could not match it at all and reported nothing:\n%s" % out)
        self.assertIn(
            ".claude/commands/demo.md", out,
            "the untested line's file is not named, so a reader cannot go and read it:\n%s" % out)

    def test_a_run_with_untested_lines_is_not_clean(self):
        """⛔ The whole issue: 'no output' read as 'nothing wrong' over 93 uncited rules."""
        repo, base = build(self.tmp, surface_lines=UNCITED)
        out = check(repo, base)
        self.assertIn(
            "VERDICT: NOT CLEAN", out,
            "a run that could not test a reported line still called itself clean:\n%s" % out)

    def test_the_untested_count_prints_when_it_is_zero(self):
        """⚠️ A figure shown only when non-zero makes its absence ambiguous."""
        repo, base = build(self.tmp, plugin_lines=CITED)
        out = check(repo, base)
        self.assertRegex(
            out, r"UNTESTED 0 line\(s\)",
            "the untested count vanishes when it is zero, so its absence has to be "
            "interpreted:\n%s" % out)


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class TheTestedHalfStillDecides(unittest.TestCase):
    """Counting the untested half is worthless if the tested half stopped working."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reverse-check-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_an_uncited_plugin_rule_is_reported(self):
        repo, base = build(self.tmp, plugin_lines=UNCITED)
        out = check(repo, base)
        self.assertIn("UNCITED", out,
                      "a hard rule added to the plugin with no invariant at its line was not "
                      "reported:\n%s" % out)
        self.assertIn("VERDICT: NOT CLEAN", out, out)

    def test_a_cited_plugin_rule_is_not_reported(self):
        """⛔ A check that flags correct prose is relaxed rather than fixed (INV-282)."""
        repo, base = build(self.tmp, plugin_lines=CITED)
        out = check(repo, base)
        self.assertNotIn("UNCITED", out,
                         "a rule citing an invariant at its own line was reported as "
                         "uncited:\n%s" % out)
        self.assertIn("VERDICT: clean", out,
                      "every added line was tested and cited, which is the one state in which "
                      "the word clean applies:\n%s" % out)

    def test_a_mid_line_rule_is_decided_rather_than_missed(self):
        """⚠️ The second defect: the old key dropped the stop sign, the report kept it."""
        repo, base = build(
            self.tmp,
            plugin_lines="Some prose leading in. ⛔ **Never lose a rule to its own stop sign.**\n")
        out = check(repo, base)
        self.assertRegex(
            out, r"TESTED\s+1 line",
            "a mid-line hard rule was not tested at all:\n%s" % out)
        self.assertIn("UNCITED", out,
                      "a mid-line rule citing nothing was not reported. The old comparison key "
                      "stripped the stop sign while `per-rule` printed it, which silently lost "
                      "44 of 333 such lines:\n%s" % out)


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class TheCorporaAreReadFromTheViewsThemselves(unittest.TestCase):
    """INV-308 — the scope a tool resolves against has one definition every consumer reads."""

    def test_the_tested_corpus_is_named_in_the_output(self):
        tmp = tempfile.mkdtemp(prefix="reverse-check-")
        try:
            repo, base = build(tmp, plugin_lines=CITED)
            out = check(repo, base)
            self.assertIn(
                "plugins/senzing-bootcamp", out,
                "the output does not say which corpus was tested, so a reader cannot tell what "
                "the verdict covers:\n%s" % out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_view_does_not_restate_the_corpus_as_a_literal(self):
        """⛔ A second spelling of the corpus is the defect this view reports, one level up."""
        src = CONFORMANCE.read_text(encoding="utf-8")
        body = src[src.index("def cmd_reverse_check"):src.index("def cmd_duplication")]
        self.assertIn(
            "shipped_markdown(plugin)", body,
            "the reverse check no longer derives the tested corpus from the same call `per-rule` "
            "makes; if it now carries its own path literal, the two can disagree silently")
        self.assertNotIn(
            '"plugins/senzing-bootcamp"', body,
            "the reverse check hardcodes the corpus path. It must come from `paths()`, or this "
            "view and the view it decides about can drift apart")


class TheDocumentsCallTheViewRatherThanCarryingTheScript(unittest.TestCase):
    """⚠️ Three documents describe this check; a fix reaching one of them is the same drift."""

    def test_the_loop_skill_calls_the_view(self):
        text = LOOP_SKILL.read_text(encoding="utf-8")
        self.assertIn(
            "conformance.py reverse-check --since-last-audit", text,
            "the unattended loop does not run the reverse check, so an unattended run has no "
            "stated way to answer the question INV-282 requires it to answer")

    def test_the_loop_skill_no_longer_carries_the_broken_comparison(self):
        """The script could not match a maintainer-surface line at all; keeping it invites use."""
        text = LOOP_SKILL.read_text(encoding="utf-8")
        self.assertNotRegex(
            text, r'unc\s*=\s*re\.sub',
            "the loop still embeds the old membership script. It compared two views reading "
            "different corpora and reported clean over 93 uncited rules (#80)")

    def test_the_command_and_the_audit_skill_name_the_view_too(self):
        for label, path in (("the loop's command", LOOP_COMMAND),
                            ("the audit skill", AUDIT_SKILL)):
            with self.subTest(document=label):
                self.assertIn(
                    "reverse-check", path.read_text(encoding="utf-8"),
                    "%s still describes the check without naming the view that performs it" % label)


if __name__ == "__main__":
    unittest.main()
