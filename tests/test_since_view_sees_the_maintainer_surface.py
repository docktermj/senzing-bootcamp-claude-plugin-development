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

⛔ **The consumer gate `tests/test_new_hard_rules_are_cited_or_deferred.py` CHECKS the
maintainer surface (#233)**, with the same cited-or-deferred predicate as the shipped corpus.
It first left `.claude/` unchecked: command files were taken to restate their skill's rules and
cite nothing, and checking them was measured here at ~49 failing restatements (at `7b43eee`).
#233 re-measured at `f81e890`: command files carried 39 `INV-` ids, and a restatement-aware
rule would have cleared 0 of the 16 uncited lines the 2026-09-28 audit found. `since` reports
only lines added or edited in the range, so a long-standing restatement never reaches the gate.
A restatement gets no special treatment; it cites at its own line or is deferred.

⛔ **Scoped out is not the same as dropped, and for a year it was dropped.** The consumer keyed
its parser on `plugins/`, so the lines this view reports under `.claude/` fell out between the
two files: 112 of them at ref `7b43eee`, after which the gate skipped as "nothing added". #74
rebuilt that parser to read `SCAN_ROOTS` and to report its breakdown on every run, and #233
then checked every root it places rather than counting the `.claude/` ones.

⚠️ **What a green run means.** The `since` view's diff reaches every `.claude/` root in
`SCAN_ROOTS`. That the rules it reports are accounted for is the consumer gate's claim, not this
file's; `test_reverse_contract_flags_the_maintainer_surface.py` proves the gate flags an uncited
`.claude/` rule whatever the live range holds.

⚠️ **Dated note, 2026-09-30 (#262): `.claude/commands` left `SCAN_ROOTS`.** #262 deleted the ten
same-name command files, since `/<name>` runs the skill (measured 2026-09-29, Claude Code
2.1.284, #241), so the maintainer surface this view must diff is `.claude/skills` and
`.claude/skill-overlays`. The command directory is required again the moment a command ships
there, read from `tests/_maintainer_surface.py`.

Stdlib only; `conformance.py` is run as a subprocess and its source read as text (INV-108).

Source issue: #38 (`the-github-issue-path-ships-guarantees-with-no-invariant`).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

import _maintainer_surface as surface

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude" / "skills" / "production-readiness-audit" / "conformance.py"

#: The `git diff -- <pathspec>` list the `since` view passes. Read from source rather than
#: inferred from output, because an empty range prints nothing and would pass vacuously.
#:
#: ⚠️ The pathspecs moved out of the call and into the module-level `SCAN_ROOTS` under #74, so
#: the consumer that parses this view's output could read the same list instead of keeping a
#: private copy of it. This reads the constant and separately checks that the call still
#: expands it -- a constant nothing passes to git would satisfy the assertions below while the
#: view scanned whatever the call named instead.
#: ⚠️ The revision argument is matched as a NAME rather than as the literal `ref`: #76 moved
#: this call into a shared helper that takes either a single revision or a range, and the
#: parameter is spelled differently there. Pinning the old spelling made this assertion fail on
#: a call that was still correct -- which is the right failure direction, but the thing being
#: asserted is that git receives the shared root list, not what the variable beside it is called.
DIFF_CALL = re.compile(
    r'"git",\s*"diff",\s*"--unified=0",\s*"--no-color",\s*[a-z_]+,\s*"--",\s*(.*?)\]', re.S)


def conformance_module():
    spec = importlib.util.spec_from_file_location("conformance_surface", CONFORMANCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["conformance_surface"] = module
    spec.loader.exec_module(module)
    return module


def diff_pathspecs():
    try:
        roots = getattr(conformance_module(), "SCAN_ROOTS", None)
    except Exception:
        return None
    return None if roots is None else set(roots)


def call_expands_the_constant():
    m = DIFF_CALL.search(CONFORMANCE.read_text(encoding="utf-8"))
    return m is not None and "SCAN_ROOTS" in m.group(1)


class TheScanIsNotVacuous(unittest.TestCase):
    """INV-265 -- a membership assertion passes trivially when the thing scanned is missing."""

    def test_conformance_is_where_this_test_expects(self):
        self.assertTrue(
            CONFORMANCE.is_file(),
            "%s is gone; re-anchor this test rather than letting it pass on a missing file"
            % CONFORMANCE)

    def test_the_root_list_was_found(self):
        specs = diff_pathspecs()
        self.assertTrue(
            specs,
            "the `since` view's scanned-root list is missing or empty (%r); every membership "
            "assertion below would pass on an empty set or fail for the wrong reason" % specs)

    def test_the_diff_call_still_expands_the_root_list(self):
        """⛔ A constant git is never handed is a list of roots nothing scans."""
        self.assertTrue(
            call_expands_the_constant(),
            "the `since` view's git-diff call no longer expands the shared root list, so the "
            "constant this test reads and the pathspecs git actually receives are two "
            "different things again -- which is the drift #74 removed")


class TheSinceViewReachesTheMaintainerSurface(unittest.TestCase):
    def test_the_shipped_corpus_is_still_scanned(self):
        """Widening must ADD a surface, never trade one away."""
        self.assertIn(
            "plugins/senzing-bootcamp", diff_pathspecs(),
            "the `since` view no longer diffs the shipped corpus; widening to `.claude/` "
            "must add the maintainer surface, not replace the one that ships")

    def test_the_maintainer_surface_is_scanned(self):
        specs = diff_pathspecs()
        surface_roots = {".claude/skills", ".claude/skill-overlays"}
        if surface.command_files():
            surface_roots.add(".claude/commands")
        missing = sorted(surface_roots - specs)
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
