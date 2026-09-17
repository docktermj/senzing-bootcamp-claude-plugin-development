"""An audit record advances `--since-last-audit`, and must say what that retires.

`last_audit_ref` starts the range at the newest audit entry's `Commit:`. The record advances
the boundary **whether or not the rules inside the previous range were ever looked at**, so
rules nobody examined leave scope permanently the moment the next audit lands, and nothing said
so.

⛔ **`SUSPECT-REF` does not cover this, and correctly.** That guard fires when the recorded ref
*carries shipped work*, because the range would then begin at the work. A clean ledger-only
record is exactly what it is built to accept — so the one boundary that matters here is the one
it stays silent about. On 2026-09-17 such a record retired 112 hard-rule lines that the gate
consuming this view had never seen (#74, fixed in #75 — but fixing the parser does not bring
the retired lines back), with no line of output at the boundary.

⛔ **What is measured is what was RETIRED. "Unexamined" is not claimed anywhere.** Nothing in
this repository records that a rule was read, so a count of unexamined rules would be an
assertion the tool cannot support — the failure INV-308 names. It reports the half it can
measure and says where the other half is not recorded.

⚠️ **The boundary prints on every resolution, including zero**, so its absence never has to be
interpreted. A test that only checked the non-zero case would pass on a build that printed
nothing when the count was 0, which is the one reading a maintainer would take as reassurance.

⚠️ **The output is parsed by two consumers**, so its shape is asserted, not assumed:
`tests/test_new_hard_rules_are_cited_or_deferred.py` keys on file headings and `+ ` lines, and
the set-difference script in `.claude/skills/unattended-issue-loop/SKILL.md` keys on a five-space
`+` prefix. A boundary line either of them mistook for a rule would corrupt the very check this
view feeds.

Built on throwaway git repositories rather than on this one, so each case is exercised directly
instead of waiting for it to recur here — and because this repo's own boundary is a single fixed
history that cannot exhibit the zero case and the first-range case at once.

Stdlib only; the maintainer script is loaded by path, never imported as a package (INV-108).

Source issue: #76 (`--since-last-audit` retires unexamined rules when the next audit record
lands).

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude" / "skills" / "production-readiness-audit" / "conformance.py"
LOOP_SKILL = REPO_ROOT / ".claude" / "skills" / "unattended-issue-loop" / "SKILL.md"

#: A ledger with two audit records, newest first. `%s` are the two recorded commits.
TWO_RECORDS = """# Implemented Specs

<!-- New entries go directly below this line. -->

## production-readiness-audit-2026-01-09

- **Implemented:** 2026-01-09 (**0 findings; no file modified by this audit**)
- **Summary:** the newer record, whose commit starts the current range.
- **Commit:** %s

## production-readiness-audit-2026-01-02

- **Implemented:** 2026-01-02 (**0 findings; no file modified by this audit**)
- **Summary:** the older record, which the boundary measures back to.
- **Commit:** %s
"""

ONE_RECORD = """# Implemented Specs

<!-- New entries go directly below this line. -->

## production-readiness-audit-2026-01-09

- **Implemented:** 2026-01-09 (**0 findings; no file modified by this audit**)
- **Summary:** the only record in this ledger.
- **Commit:** %s
"""


def load():
    spec = importlib.util.spec_from_file_location("conformance_boundary", CONFORMANCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["conformance_boundary"] = module
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    done = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError("git %s failed in fixture: %s" % (" ".join(args), done.stderr))
    return done.stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class TheBoundaryIsReported(unittest.TestCase):
    """Two audit records with hard rules committed between them."""

    @classmethod
    def setUpClass(cls):
        cls.module = load()
        cls.tmp = tempfile.mkdtemp(prefix="boundary-")
        repo = Path(cls.tmp)
        cls.repo = repo
        git(repo, "init", "--quiet", "--initial-branch", "main")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "fixture")
        git(repo, "config", "commit.gpgsign", "false")

        (repo / "specs").mkdir()
        (repo / "specs" / "IMPLEMENTED.md").write_text(ONE_RECORD % "uncommitted",
                                                       encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "docs(specs): the older audit record")
        cls.older = git(repo, "rev-parse", "--short", "HEAD")

        # Three rules between the records: two under the shipped corpus, one under the
        # maintainer surface, so a boundary that measured only `plugins/` would report 2.
        shipped = repo / "plugins" / "senzing-bootcamp" / "skills" / "demo"
        shipped.mkdir(parents=True)
        (shipped / "SKILL.md").write_text(
            "- ⛔ **Never ship a rule the boundary cannot count.**\n"
            "- ⛔ **Always measure what a range retires.**\n", encoding="utf-8")
        surface = repo / ".claude" / "commands"
        surface.mkdir(parents=True)
        (surface / "demo.md").write_text(
            "- ⛔ **A rule on the maintainer surface, retired just the same.**\n",
            encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "feat(demo): three hard rules")
        cls.work = git(repo, "rev-parse", "--short", "HEAD")

        (repo / "specs" / "note.md").write_text("the newer audit record's own change\n",
                                                encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "docs(specs): the newer audit record")
        cls.newer = git(repo, "rev-parse", "--short", "HEAD")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def resolve(self, ledger):
        (self.repo / "specs" / "IMPLEMENTED.md").write_text(ledger, encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ref = self.module.last_audit_ref(self.repo)
        return ref, out.getvalue()

    def test_the_fixture_really_carries_rules_between_the_records(self):
        """⛔ INV-265 — a fixture with no rules in the retired range proves nothing."""
        added = self.module.added_rule_lines(self.repo, self.older, self.newer)
        self.assertIsNotNone(added, "the fixture range could not be diffed")
        self.assertEqual(
            3, sum(len(rows) for rows in added.values()),
            "the fixture does not carry three hard rules between its two audit records, so "
            "every count asserted below would be measuring the wrong thing")

    def test_the_retired_count_is_reported(self):
        ref, out = self.resolve(TWO_RECORDS % (self.newer, self.older))
        self.assertEqual(self.newer, ref)
        self.assertIn("BOUNDARY", out,
                      "the resolver advanced the range past three hard rules and said nothing "
                      "about the boundary:\n%s" % out)
        self.assertRegex(
            out, r"carrying 3 hard-rule line\(s\)",
            "the boundary did not report the 3 rules the retired range carried:\n%s" % out)

    def test_the_boundary_names_both_ends_of_what_it_retired(self):
        _ref, out = self.resolve(TWO_RECORDS % (self.newer, self.older))
        self.assertIn(
            "%s..%s" % (self.older, self.newer), out,
            "the boundary does not name the range it retired, so a reader cannot go and look "
            "at it:\n%s" % out)

    def test_it_refuses_to_claim_the_rules_were_examined(self):
        """⛔ Nothing records that a rule was read; a tool saying otherwise is guessing."""
        _ref, out = self.resolve(TWO_RECORDS % (self.newer, self.older))
        self.assertRegex(
            out.lower(), r"examined is recorded nowhere|cannot say",
            "the boundary reports a count without stating that whether those rules were "
            "examined is unrecorded. A bare count reads as an audit result:\n%s" % out)

    def test_zero_is_reported_rather_than_omitted(self):
        """⚠️ A figure printed only when non-zero makes its absence ambiguous."""
        ledger = TWO_RECORDS % (self.newer, self.work)
        _ref, out = self.resolve(ledger)
        self.assertRegex(
            out, r"carrying 0 hard-rule line\(s\)",
            "an empty retired range printed no boundary line at all. Silence there is "
            "indistinguishable from a boundary the tool stopped measuring:\n%s" % out)
        self.assertRegex(
            out, r"0 here means the retired range was EMPTY",
            "the zero is reported with no statement of what it means, and the one reading a "
            "maintainer would take from it -- 'checked, nothing found' -- is the wrong one")

    def test_a_first_range_is_not_reported_as_a_measured_zero(self):
        """One record: there is no earlier boundary, which is not the same as an empty one."""
        _ref, out = self.resolve(ONE_RECORD % self.newer)
        self.assertIn("BOUNDARY", out, "a first range says nothing at all:\n%s" % out)
        self.assertNotRegex(
            out, r"carrying \d+ hard-rule line\(s\)",
            "a ledger with one audit record reported a measured retired count. There is no "
            "earlier record to measure back to, so any number here is invented:\n%s" % out)


@unittest.skipUnless(shutil.which("git"), "git is required to build the fixture repository")
class TheBoundaryLinesCannotBeMisreadAsRules(unittest.TestCase):
    """⚠️ Two consumers parse this view's stdout; a boundary line one of them took for a rule
    would corrupt the reverse-contract check this view exists to feed."""

    def setUp(self):
        self.module = load()
        self.tmp = tempfile.mkdtemp(prefix="boundary-shape-")
        repo = Path(self.tmp)
        git(repo, "init", "--quiet", "--initial-branch", "main")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "fixture")
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "specs").mkdir()
        (repo / "specs" / "IMPLEMENTED.md").write_text(ONE_RECORD % "uncommitted",
                                                       encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "docs(specs): older record")
        older = git(repo, "rev-parse", "--short", "HEAD")
        shipped = repo / "plugins" / "senzing-bootcamp"
        shipped.mkdir(parents=True)
        (shipped / "SKILL.md").write_text("- ⛔ **A retired rule.**\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "feat: a rule")
        (repo / "specs" / "note.md").write_text("newer record\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "docs(specs): newer record")
        newer = git(repo, "rev-parse", "--short", "HEAD")
        (repo / "specs" / "IMPLEMENTED.md").write_text(TWO_RECORDS % (newer, older),
                                                       encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.module.last_audit_ref(repo)
        self.boundary = [l for l in out.getvalue().splitlines() if "BOUNDARY" in l
                         or l.startswith("     ")]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_boundary_produced_lines_to_check(self):
        """INV-265 — the shape assertions below pass trivially over no lines."""
        self.assertTrue(
            self.boundary,
            "no boundary output was produced, so the two shape assertions below check nothing")

    def test_no_boundary_line_looks_like_a_rule_to_the_loop_script(self):
        """The set-difference script takes every line starting with five spaces and a `+`."""
        offenders = [l for l in self.boundary if l.startswith("     +")]
        self.assertEqual(
            [], offenders,
            "a boundary line would be read as an added hard rule by the INV-282 set-difference "
            "script in the unattended loop, which would then test it for a citation: %r"
            % offenders)

    def test_no_boundary_line_looks_like_a_heading_or_a_rule_to_the_gate(self):
        """The gate keys on a bare path ending `.md`, then on `+ ` lines beneath it."""
        for line in self.boundary:
            stripped = line.strip()
            with self.subTest(line=stripped[:60]):
                self.assertFalse(
                    stripped.endswith(".md") and " " not in stripped,
                    "a boundary line parses as a file heading in "
                    "tests/test_new_hard_rules_are_cited_or_deferred.py")
                self.assertFalse(
                    stripped.startswith("+ "),
                    "a boundary line parses as an added rule in "
                    "tests/test_new_hard_rules_are_cited_or_deferred.py")

    def test_the_consumers_still_key_on_what_this_test_assumes(self):
        """⛔ Asserting a shape against a consumer that changed proves nothing.

        Both keys are read from the consumers' own source, so this fails loudly if either one
        starts parsing differently rather than silently guarding the wrong shape.
        """
        gate = (REPO_ROOT / "tests" / "test_new_hard_rules_are_cited_or_deferred.py").read_text(
            encoding="utf-8")
        self.assertIn(
            'stripped.startswith("+ ")', gate,
            "the gate no longer keys added rules on a `+ ` prefix; the shape asserted above is "
            "not the shape it parses")
        self.assertIn(
            '.endswith(".md")', gate,
            "the gate no longer keys file headings on a `.md` suffix")
        self.assertTrue(LOOP_SKILL.is_file(), "%s is gone" % LOOP_SKILL)
        self.assertIn(
            'l.startswith("     +")', LOOP_SKILL.read_text(encoding="utf-8"),
            "the unattended loop's set-difference script no longer keys on a five-space `+` "
            "prefix, so the assertion above guards a shape nothing parses")


if __name__ == "__main__":
    unittest.main()
