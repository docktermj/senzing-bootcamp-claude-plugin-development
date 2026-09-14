"""`conformance.py`'s per-rule and since views see a rule the section-scoped count cannot.

`conformance.py rules` is the mechanical half of the audit's reverse contract, and
`implement-spec` Step 5 tells a run to check it before writing a ledger entry. Its unit is
the **enclosing section**, so a brand-new unregistered rule passes the moment it lands
anywhere near an unrelated `INV-nnn` -- and it passes more reliably as citations get denser.

⚠️ **Measured, not argued.** On 2026-08-21 a run added 26 hard-rule lines to shipped markdown
(net +25; one rule was reworded, so it counts as both an addition and a removal) and the
section-scoped count held at **1**, its session baseline, while three of those rules were on
subjects `INVARIANTS.md` covers nowhere. The audit report and two specs said **37**; the
mechanical count against the session's base commit says 26 added / 25 net, and the mechanical
count governs. That correction is itself the defect class this file guards -- a figure carried
as prose with nothing re-measuring it.

The negative control is the whole point and it is structural: a hard rule is added **beside an
unrelated citation**, and the test asserts the section-scoped count does NOT move while the
per-rule view DOES report it. A guard that only checked the per-rule view would pass against a
per-rule view that had silently become section-scoped too.

Runs `conformance.py` as a subprocess against a synthetic repo, so it asserts the shipped
behavior of the script rather than a reimplementation of its regex (stdlib only, INV-108).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude/skills/production-readiness-audit/conformance.py"


def shipped_hard_rule_pattern():
    """The script's OWN classifier, loaded rather than copied.

    A copy here would be a second definition of "hard rule" -- the exact duplication the
    acceptance criterion forbids across the three views, reintroduced by the test that checks
    it. The first draft of this file did copy it, and the copy's escaping was wrong, so the
    test reported a line starting with a stop sign as "not a hard rule". Loading the module is
    stdlib-only and reaches nothing under `plugins/` (INV-108).
    """
    spec = importlib.util.spec_from_file_location("_conformance", CONFORMANCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # classify(), not the anchored pattern: `since` reports mid-line rules too, and pinning
    # ANCHORED_RULE here made this test reject the very lines the detector fix made visible.
    return mod.classify


HARD_RULE_SHAPE = shipped_hard_rule_pattern()   # a callable: line -> kind or None

#: The roots the `since` view diffs, read from `conformance.py`'s own `git diff` pathspec
#: rather than restated here. Restating them is what let this file's parser go stale when
#: #38 widened the view to the `.claude/` maintainer surface.
_DIFF_CALL = re.compile(
    r'"git",\s*"diff",\s*"--unified=0",\s*"--no-color",\s*ref,\s*"--",\s*(.*?)\]', re.S)


def since_roots():
    match = _DIFF_CALL.search(CONFORMANCE.read_text(encoding="utf-8"))
    return tuple(re.findall(r'"([^"]+)"', match.group(1))) if match else ()


SINCE_ROOTS = since_roots()

# A section that cites an invariant for a reason unrelated to the rule added below it. This is
# the shape that hides a new rule: the citation is correct, present, and about something else.
SECTION = """# A module step

## Step 7: create the datastore

Place the file under the project root (INV-200) and source the path from the server (INV-080).

Some ordinary prose that is not a hard rule at all.
"""

# The rule under test. Bolded MUST, no citation on its own line or either neighbor.
NEW_RULE = "⛔ **The datastore's filesystem MUST be measured before the file is created.**\n"


def make_repo(root, body):
    d = root / "plugins" / "senzing-bootcamp" / "skills" / "module-02-sdk-setup"
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    (root / "specs").mkdir(parents=True, exist_ok=True)
    (root / "specs" / "INVARIANTS.md").write_text("- **INV-200** — placement.\n",
                                                  encoding="utf-8")
    return root


def run_conformance(repo, *argv):
    proc = subprocess.run([sys.executable, str(CONFORMANCE), "--repo", str(repo)] + list(argv),
                          capture_output=True, text=True)
    return proc


class TheScriptShipsBothViews(unittest.TestCase):
    def test_per_rule_and_since_are_invocable(self):
        for argv in (["per-rule"], ["per-rule", "--uncited"], ["since", "--ref", "HEAD"]):
            with tempfile.TemporaryDirectory() as td:
                repo = make_repo(Path(td), SECTION)
                proc = run_conformance(repo, *argv)
                # `since` needs a git repo; exit 2 with a named git failure is a correct
                # refusal, not a missing subcommand. What must not happen is argparse
                # rejecting the subcommand itself.
                self.assertNotIn("invalid choice", proc.stderr,
                                 "conformance.py does not ship %r: %s" % (argv, proc.stderr))


class ARuleBesideAnUnrelatedCitation(unittest.TestCase):
    """The negative control, run in both directions in one test so they cannot drift apart."""

    def counts(self, body):
        with tempfile.TemporaryDirectory() as td:
            repo = make_repo(Path(td), body)
            sec = run_conformance(repo, "rules")
            self.assertEqual(0, sec.returncode, sec.stderr)
            # Tolerant of the anchored/mid-line split `rules` grew on 2026-08-21: the
            # parenthetical is optional here so this test asserts the SEMANTICS (does the
            # section count move) rather than the exact headline format. The first version
            # pinned the old wording and broke the hour the format changed.
            m = re.search(r"(\d+) hard-rule lines(?: \([^)]*\))?, (\d+) in a section "
                          r"citing no invariant", sec.stdout)
            self.assertIsNotNone(m, "`rules` output did not parse:\n%s" % sec.stdout)
            per = run_conformance(repo, "per-rule", "--uncited")
            self.assertEqual(0, per.returncode, per.stderr)
            p = re.search(r"(\d+) hard-rule lines, (\d+) citing no invariant at the rule itself",
                          per.stdout)
            self.assertIsNotNone(p, "`per-rule` output did not parse:\n%s" % per.stdout)
            return {"section_total": int(m.group(1)), "section_uncited": int(m.group(2)),
                    "per_total": int(p.group(1)), "per_uncited": int(p.group(2)),
                    "per_out": per.stdout}

    def test_the_section_count_is_blind_and_the_per_rule_view_is_not(self):
        before = self.counts(SECTION)
        after = self.counts(SECTION + "\n" + NEW_RULE)

        # Direction 1: the section-scoped count cannot see it. If this ever starts moving,
        # `rules` has changed unit and this file's premise -- and the spec's -- needs revisiting.
        self.assertEqual(
            before["section_uncited"], after["section_uncited"],
            "the section-scoped count MOVED for a rule added beside an unrelated citation "
            "(%d -> %d). That is a better script than the one this test was written against; "
            "re-read `conformance-rules-cannot-see-a-new-rule-beside-an-old-citation.md` "
            "before relaxing anything here."
            % (before["section_uncited"], after["section_uncited"]))
        self.assertEqual(0, after["section_uncited"],
                         "expected the citation to cover the whole section:\n%s" % after)

        # Direction 2: the per-rule view does see it, and says where.
        self.assertEqual(
            before["per_uncited"] + 1, after["per_uncited"],
            "the per-rule view did NOT report a hard rule citing no invariant at itself "
            "(%d -> %d). It has widened back toward the section scope, which reintroduces "
            "exactly the blind spot it exists to remove."
            % (before["per_uncited"], after["per_uncited"]))
        self.assertIn("module-02-sdk-setup/SKILL.md", after["per_out"],
                      "the per-rule view must name the file:line of each rule:\n%s"
                      % after["per_out"])

    def test_a_citation_on_the_rules_own_line_is_credited(self):
        """The per-rule view is narrow, not blind: a citation AT the rule counts."""
        cited = NEW_RULE.rstrip("\n").rstrip("*") + " (INV-200)**\n"
        after = self.counts(SECTION + "\n" + cited)
        before = self.counts(SECTION)
        self.assertEqual(
            before["per_uncited"], after["per_uncited"],
            "a rule citing an invariant on its own line was still counted as uncited; the "
            "per-rule window is too narrow to be usable.")
        self.assertEqual(before["per_total"] + 1, after["per_total"],
                         "the rule was not recognized as a hard rule at all")

    def test_the_adjacent_sentence_counts_but_the_section_does_not(self):
        """The window is the rule plus one non-blank line either side -- and stops there."""
        adjacent = self.counts(SECTION + "\n" + NEW_RULE + "This is required by INV-200.\n")
        distant = self.counts(SECTION + "\n" + NEW_RULE
                              + "\nUnrelated prose.\n\nMore prose.\n\nSee INV-200.\n")
        self.assertEqual(0, adjacent["per_uncited"] - self.counts(SECTION)["per_uncited"],
                         "a citation in the sentence immediately after the rule was not "
                         "credited:\n%s" % adjacent["per_out"])
        self.assertEqual(1, distant["per_uncited"] - self.counts(SECTION)["per_uncited"],
                         "a citation three paragraphs away WAS credited -- the window has "
                         "widened into section scope:\n%s" % distant["per_out"])


class TheSinceViewFiltersByRef(unittest.TestCase):
    """Asserts the PROPERTY, not a count.

    ⛔ **An earlier version of this class asserted `since --ref HEAD` reports 0**, which is only
    true when the working tree has no uncommitted change under `plugins/`. It failed within the
    hour, on the commit that reflowed two capture blocks — so it would fail for any maintainer
    with work in progress, and its message would blame the diff parse. A test whose result
    depends on uncommitted work is not a guard; the count semantics are covered below against a
    synthetic repo where the tree is controlled.
    """

    def test_the_since_roots_were_parsed(self):
        """INV-265 -- with no roots parsed, every heading below is unrecognized."""
        self.assertGreaterEqual(
            len(SINCE_ROOTS), 1,
            "no pathspec was parsed out of conformance.py's `since` diff call; the heading "
            "parser below would treat every reported rule as headingless")

    def test_it_reports_only_hard_rules_and_only_from_shipped_markdown(self):
        proc = run_conformance(REPO_ROOT, "since", "--ref", "HEAD")
        self.assertEqual(0, proc.returncode, proc.stderr)
        m = re.search(r"(\d+) hard-rule line\(s\) added since HEAD", proc.stdout)
        self.assertIsNotNone(m, "`since` output did not parse:\n%s" % proc.stdout)

        reported, current = [], None
        for line in proc.stdout.splitlines():
            stripped = line.strip()
            # ⛔ The `since` view's pathspec was widened to `.claude/commands` and
            # `.claude/skills` by #38, and this parser was not. It kept passing only while
            # nobody had an uncommitted hard-rule line under `.claude/` -- the first such
            # working tree reported a rule under a heading this loop never recognized, and
            # the failure blamed "a reported rule has no file heading above it" rather than
            # the parser. Both roots are read from the script's own pathspec below so the
            # next widening cannot desynchronize them again.
            if any(stripped.startswith(root) for root in SINCE_ROOTS):
                current = stripped
            elif stripped.startswith("+ "):
                reported.append((current, stripped[2:]))
        self.assertEqual(
            int(m.group(1)), len(reported),
            "the printed total disagrees with the lines printed:\n%s" % proc.stdout)
        for path, body in reported:
            self.assertIsNotNone(path, "a reported rule has no file heading above it")
            self.assertTrue(path.endswith(".md"),
                            "reported a non-markdown file %r: the .md filter is not applied" % path)
            self.assertTrue(
                HARD_RULE_SHAPE(self._source_line(path, body)) is not None,
                "reported a line that is not a hard rule (%r from %s); the diff parse is "
                "picking up context or removed lines" % (body[:80], path))

    @staticmethod
    def _source_line(path, body):
        """The full source line behind a reported one.

        ⚠️ `since` truncates its display at 110 characters, and `classify()` needs the whole
        line — a rule whose ⛔ sits past that cut classifies as None from the display string
        alone. This test therefore passed only while every reported line was short enough to
        survive truncation; a 638-character bullet in `module-completion.md` was the first to
        expose it, and it read as "conformance reported a non-rule" when conformance was
        right and this assertion was looking at a prefix.
        """
        candidate = (REPO_ROOT / path).read_text(encoding="utf-8") if (REPO_ROOT / path).exists() else ""
        for line in candidate.split("\n"):
            if line.startswith(body) or line == body:
                return line
        return body                                  # not truncated, or file moved

    def test_it_counts_only_ADDED_lines_in_a_repo_it_controls(self):
        """The count semantics, on a tree this test owns rather than the maintainer's.

        ⚠️ **Two fixture flaws had to be fixed before this test could fail.** The first draft
        created the non-markdown file without `git add`, so it was untracked and never reached
        `git diff` at all -- removing the `.md` filter changed nothing and the test still passed.
        The second removed an ordinary prose line rather than a hard rule, so dropping the
        added-lines-only filter also changed nothing. Both mutants now fail this test. A fixture
        that cannot reach the code path under test is indistinguishable from a correct
        implementation, which is the whole reason the mutation is run.
        """
        old_rule = "⛔ **The old rule MUST be removed by this change.**\n"
        new_rule = "⛔ **The new rule MUST be added by this change.**\n"
        with tempfile.TemporaryDirectory() as td:
            repo = make_repo(Path(td), SECTION + "\n" + old_rule)
            skill = repo / "plugins/senzing-bootcamp/skills/module-02-sdk-setup/SKILL.md"

            def git(*a):
                return subprocess.run(["git"] + list(a), cwd=str(repo),
                                      capture_output=True, text=True)

            git("init", "-q")
            git("config", "user.email", "t@example.com")
            git("config", "user.name", "t")
            git("add", "-A")
            git("commit", "-q", "-m", "base")
            base = git("rev-parse", "HEAD").stdout.strip()
            self.assertTrue(base, "the synthetic repo has no HEAD; git init/commit failed")

            # Remove a HARD RULE (not ordinary prose) and add a different one, so a parse that
            # counted removed lines would report 2 instead of 1.
            skill.write_text(SECTION + "\n" + new_rule, encoding="utf-8")
            # A hard rule in a NON-markdown file, and `git add`ed so it is actually in the diff.
            (skill.parent / "notes.txt").write_text(new_rule, encoding="utf-8")
            git("add", "-A")

            diff = git("diff", base, "--", "plugins/senzing-bootcamp").stdout
            self.assertIn("notes.txt", diff,
                          "fixture broken: the non-markdown file is not in the diff, so the "
                          ".md filter is not being exercised at all")

            proc = run_conformance(repo, "since", "--ref", base)
            self.assertEqual(0, proc.returncode, proc.stderr)
            m = re.search(r"(\d+) hard-rule line\(s\) added since", proc.stdout)
            self.assertIsNotNone(m, proc.stdout)
            self.assertEqual(
                1, int(m.group(1)),
                "expected exactly the one added markdown hard rule -- not the REMOVED rule, "
                "not the .txt file:\n%s" % proc.stdout)
            self.assertNotIn("notes.txt", proc.stdout,
                             "a non-markdown file was reported:\n%s" % proc.stdout)
            self.assertNotIn("old rule", proc.stdout,
                             "a REMOVED hard rule was reported as added:\n%s" % proc.stdout)

    def test_a_bad_ref_fails_loudly_rather_than_reporting_zero(self):
        proc = run_conformance(REPO_ROOT, "since", "--ref", "no-such-ref-exists-here")
        self.assertEqual(2, proc.returncode,
                         "a nonexistent ref must exit non-zero: '0 rules added' and 'the ref "
                         "was wrong' are indistinguishable otherwise (INV-110/INV-115)")
        self.assertIn("no-such-ref-exists-here", proc.stderr)


if __name__ == "__main__":
    unittest.main()
