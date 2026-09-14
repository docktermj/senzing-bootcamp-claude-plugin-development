"""`conformance.py since` reads the `.claude/` maintainer surface, not only `plugins/`.

Four durable guarantees shipped between 2026-09-03 and 2026-09-14 -- the dev-command contract,
the propagation boundary, the fpdf2 CI matrix and the optional-dependency declaration -- each
enforced by a new test, none registered as an invariant and none carrying a deferral. The
reverse-contract sweep that exists to catch exactly that reported **0 hard-rule lines added**,
correctly by its own definition: it diffed `plugins/senzing-bootcamp` alone, and every one of
those guarantees landed under `.claude/`.

⛔ **Only the `since` view is widened, and that asymmetry is the point.** `.claude/` carries
roughly 165 hard-rule lines against the shipped corpus's ~672. Nearly all are deliberate
restatements of rules that already live in the skills the command files front, so widening
`rules` or `per-rule` would add that many permanent false leads to a worklist whose own skill
warns these are leads and not verdicts. `since` asks a different question -- *what appeared
since the last audit?* -- where a restatement that has been there all along does not appear at
all, and a genuinely new rule does.

⚠️ **The consumer gate `tests/test_new_hard_rules_are_cited_or_deferred.py` was deliberately NOT
widened with it**, and this file does not assert that it was. That test requires every added
rule to be cited at its line or named in a deferral; command files restate their skill's rules
by design and cite nothing, so widening it turns ~49 restatement lines into failures. The
honest options are a restatement-aware comparison or leaving the gate scoped, and neither is
"weaken the assertion until it passes". Measured rather than assumed: widening the filter
produced a red suite, which is why the change was reverted rather than shipped.

⚠️ **What a green run means.** The `since` view's diff reaches `.claude/commands` and
`.claude/skills`. It does not mean anything consumes that output, nor that the rules it reports
are accounted for -- those are the scoped-out half above.

Stdlib only; `conformance.py` is run as a subprocess and its source read as text (INV-108).

Source issue: #38 (`the-github-issue-path-ships-guarantees-with-no-invariant`).

Run:  python3 -m unittest discover -s tests
"""
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude" / "skills" / "production-readiness-audit" / "conformance.py"

#: The `git diff -- <pathspec>` list the `since` view passes. Read from source rather than
#: inferred from output, because an empty range prints nothing and would pass vacuously.
DIFF_CALL = re.compile(
    r'"git",\s*"diff",\s*"--unified=0",\s*"--no-color",\s*ref,\s*"--",\s*(.*?)\]', re.S)


def diff_pathspecs():
    src = CONFORMANCE.read_text(encoding="utf-8")
    m = DIFF_CALL.search(src)
    if m is None:
        return None
    return set(re.findall(r'"([^"]+)"', m.group(1)))


class TheScanIsNotVacuous(unittest.TestCase):
    """INV-265 -- a membership assertion passes trivially when the thing scanned is missing."""

    def test_conformance_is_where_this_test_expects(self):
        self.assertTrue(
            CONFORMANCE.is_file(),
            "%s is gone; re-anchor this test rather than letting it pass on a missing file"
            % CONFORMANCE)

    def test_the_diff_call_was_found(self):
        self.assertIsNotNone(
            diff_pathspecs(),
            "the `since` view's git-diff pathspec list did not parse; the call has been "
            "rewritten and the assertions below prove nothing")


class TheSinceViewReachesTheMaintainerSurface(unittest.TestCase):
    def test_the_shipped_corpus_is_still_scanned(self):
        """Widening must ADD a surface, never trade one away."""
        self.assertIn(
            "plugins/senzing-bootcamp", diff_pathspecs(),
            "the `since` view no longer diffs the shipped corpus; widening to `.claude/` "
            "must add the maintainer surface, not replace the one that ships")

    def test_the_maintainer_surface_is_scanned(self):
        specs = diff_pathspecs()
        missing = sorted({".claude/commands", ".claude/skills"} - specs)
        self.assertEqual(
            [], missing,
            "the `since` view does not diff %s, so a durable rule landing there is invisible "
            "to the reverse-contract sweep -- the defect this test exists for, where four "
            "guarantees shipped and the sweep reported 0 lines added" % ", ".join(missing))

    def test_the_view_still_runs(self):
        """A pathspec that git rejects would make the whole view exit non-zero."""
        proc = subprocess.run(
            ["python3", str(CONFORMANCE), "since", "--ref", "HEAD"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=180)
        self.assertEqual(
            0, proc.returncode,
            "`since --ref HEAD` exited %d after the pathspec widening; git rejected one of "
            "%s.\nstderr: %s" % (proc.returncode, sorted(diff_pathspecs()), proc.stderr.strip()))


class TheOtherViewsStayScoped(unittest.TestCase):
    """⛔ The asymmetry is deliberate and load-bearing; a later widening should fail here."""

    def test_the_corpus_helper_still_reads_plugins_only(self):
        src = CONFORMANCE.read_text(encoding="utf-8")
        self.assertIn(
            'repo / "plugins" / "senzing-bootcamp"', src,
            "the corpus helper no longer resolves to plugins/senzing-bootcamp; if `rules` and "
            "`per-rule` now scan `.claude/`, roughly 165 restatement lines have entered the "
            "uncited worklist as permanent false leads -- read this file's docstring before "
            "deciding that is wanted")


if __name__ == "__main__":
    unittest.main()
