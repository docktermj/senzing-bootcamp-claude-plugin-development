"""The CI workflow keeps both fpdf2 cells, pins its actions, and cannot lie about a green run.

This repo had no CI at all until #33. The workflow it added is load-bearing in a way that is
easy to lose: the `absent` matrix cell is the ONLY thing that catches a new fpdf2-dependent test
landing without a `@requires_fpdf2` guard, because that omission is invisible to anyone whose
machine has fpdf2 installed. Delete that cell -- or "simplify" the matrix away -- and CI still
runs, still reports green, and #30's regression returns one test at a time.

⚠️ **The pipefail trap is the reason several assertions here exist.** GitHub's default `run:`
shell on Linux is `bash -e {0}`, *without* `pipefail`. A step written as

    python -m unittest discover -s tests 2>&1 | tee suite.log

reports **tee's** exit status under that default, so a failing suite reports success and the
whole workflow becomes decorative. Declaring `shell: bash` switches to
`bash --noprofile --norc -eo pipefail {0}`. Nothing in GitHub's UI flags the difference, and a
workflow that is wrong this way looks exactly like one that is right.

⛔ **Stdlib only (INV-108), so the workflow is read as TEXT, not parsed as YAML.** PyYAML is a
third-party package and may not import in a dev environment. The assertions below are therefore
substring and regex checks over the file. That is weaker than a parse -- it cannot prove the
YAML is well-formed -- and the `lint-workflows` job added alongside covers that direction on
the runner.

⚠️ **What a green run means.** The workflow file still says what it is supposed to say. It does
not mean GitHub accepts it, that the matrix expands, or that the jobs pass -- none of which is
observable from a unit test, and all of which the pipeline itself reports.

Source issue: #33.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
TEST_WORKFLOW = WORKFLOWS / "test-suite.yaml"
PROPAGATE_SH = REPO_ROOT / ".claude" / "skills" / "propagate-to-public" / "propagate.sh"

#: A third-party action reference: `uses: owner/repo@<ref>`, with an optional trailing comment.
USES = re.compile(r"^\s*uses:\s*(\S+)@(\S+)(?:\s*#\s*(.+))?$", re.M)

#: A 40-character hex commit SHA.
SHA = re.compile(r"^[0-9a-f]{40}$")

#: An rsync source inside propagate.sh: `"$here/<path>"`.
RSYNC_SOURCE = re.compile(r'rsync\s[^\n]*?"\$here/([^"]*)"')


def workflow_text():
    return TEST_WORKFLOW.read_text(encoding="utf-8")


def steps():
    """The workflow's step blocks, split on the `- name:` that begins each one."""
    body = workflow_text()
    parts = re.split(r"\n\s+- name:", body)
    return parts[1:]


class TheWorkflowExists(unittest.TestCase):
    """INV-265 -- every check below passes vacuously against a missing or empty file."""

    def test_the_workflow_file_is_present(self):
        self.assertTrue(
            TEST_WORKFLOW.is_file(),
            "%s is gone. Nothing runs the suite on a pull request, and the fpdf2 matrix that "
            "protects #30 does not exist" % TEST_WORKFLOW)

    def test_it_has_steps_this_test_can_see(self):
        found = steps()
        self.assertGreaterEqual(
            len(found), 4,
            "parsed %d steps from %s; the file's shape changed and the checks below prove "
            "nothing" % (len(found), TEST_WORKFLOW.name))


class BothMatrixCellsSurvive(unittest.TestCase):
    def test_the_matrix_declares_present_and_absent(self):
        text = workflow_text()
        for cell in ("present", "absent"):
            self.assertRegex(
                text, r"fpdf2:\s*\[[^\]]*\b%s\b" % cell,
                "the fpdf2 matrix no longer declares the %r cell. Both renderer paths ship; "
                "dropping a cell leaves one of them untested while CI still reports green"
                % cell)

    def test_the_absent_cell_has_a_negative_control(self):
        """Without it, a transitively-installed fpdf2 makes 'absent' a copy of 'present'."""
        self.assertIn(
            'python -c "import fpdf"', workflow_text(),
            "the 'absent' job no longer proves fpdf2 is actually absent. If something installs "
            "it transitively, that job silently stops testing the stdlib fallback and still "
            "passes")

    def test_the_absent_cell_requires_a_nonzero_skip_count(self):
        self.assertIn(
            "OK \\(skipped=[1-9][0-9]*\\)", workflow_text(),
            "the 'absent' job no longer requires a non-zero skip count. A run where the guards "
            "have stopped being applied would report green with zero skips -- the #30 "
            "regression arriving quietly")

    def test_the_absent_cell_requires_the_notice(self):
        self.assertIn(
            "fpdf2 is not installed", workflow_text(),
            "the 'absent' job no longer checks for the notice naming the missing package. That "
            "notice is the user-facing half of #30")


class PipedStepsCannotSwallowAFailure(unittest.TestCase):
    """The single most likely way this workflow is quietly wrong."""

    def test_every_piping_step_declares_bash(self):
        offenders = [
            s.splitlines()[0].strip() for s in steps()
            if "|" in s and re.search(r"\|\s*(tee|grep|head|tail|xargs)\b", s)
            and "shell: bash" not in s]
        self.assertEqual(
            [], offenders,
            "step(s) %s pipe a command without declaring `shell: bash`. GitHub's default "
            "run-shell on Linux is `bash -e {0}` with NO pipefail, so the step reports the LAST "
            "command's status -- a failing test suite piped into tee reports success"
            % offenders)


class ActionsAreSupplyChainPinned(unittest.TestCase):
    def test_third_party_actions_are_pinned_to_a_sha(self):
        unpinned = []
        for text in (workflow_text(),):
            for owner_repo, ref, _comment in USES.findall(text):
                if owner_repo.startswith("senzing-factory/"):
                    continue          # org-owned reusable workflows are referenced by tag
                if not SHA.match(ref):
                    unpinned.append("%s@%s" % (owner_repo, ref))
        self.assertEqual(
            [], unpinned,
            "action(s) %s are referenced by tag rather than a commit SHA. A tag can be moved "
            "to different code after review; the rest of the org pins these" % unpinned)

    def test_pinned_actions_name_their_version_in_a_comment(self):
        """A bare SHA is unreadable; every pin in this org carries `# vX.Y.Z`."""
        naked = [
            "%s@%s" % (o, r) for o, r, c in USES.findall(workflow_text())
            if SHA.match(r) and not c]
        self.assertEqual(
            [], naked,
            "pinned action(s) %s carry no `# vX.Y.Z` comment, so no reader can tell what "
            "version the SHA is without looking it up" % naked)


class TheDocumentedRunnerIsUsed(unittest.TestCase):
    def test_ci_runs_unittest_discover(self):
        """INV-108 names the runner; CI should enforce the contract, not a convenience."""
        self.assertIn(
            "unittest discover -s tests", workflow_text(),
            "CI no longer runs `unittest discover -s tests`. INV-108 names it as the suite's "
            "runner and 250 test docstrings repeat it; pytest passing is not the same promise")


class CiIsNotPropagated(unittest.TestCase):
    """This change created `.github/` for the first time; it must stay in development."""

    def test_no_propagate_source_reaches_dot_github(self):
        sources = {p.rstrip("/") for p in RSYNC_SOURCE.findall(
            PROPAGATE_SH.read_text(encoding="utf-8"))}
        self.assertTrue(sources, "parsed no rsync sources from %s" % PROPAGATE_SH)
        leaked = sorted(p for p in sources if p.split("/")[0] == ".github")
        self.assertEqual(
            [], leaked,
            "propagate.sh names %s as a mirror source. The public repo owns its own .github/ "
            "governance layer; mirroring this repo's CI over it would replace workflows that "
            "are not ours to manage" % leaked)


if __name__ == "__main__":
    unittest.main()
