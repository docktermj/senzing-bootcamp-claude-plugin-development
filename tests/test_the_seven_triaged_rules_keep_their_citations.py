"""The seven rules triaged on 2026-08-21 keep naming the invariants that govern them.

Fixing the hard-rule detector's line anchoring took `conformance.py rules` from **1** uncited
section to **7**: six rules had been in shipped prose all along, invisible to every view because
their stop sign was not first on its line. Triaging them found **no unregistered rule** — all
six, plus the one long-standing hit, were governed by an invariant the text did not name:

| Rule | Governing invariant |
|---|---|
| `${BASH_SOURCE[0]}` is bash-only, empty under zsh | INV-175 |
| a sourced script must never `exit` or `set -e` | INV-175 |
| a reachability probe must not be a document search | INV-204 |
| the source qualifier is required, not tidiness | INV-177 |
| `workspace_dir` is required on `analyze_record` | INV-136 (+ INV-200 for the location) |
| the test load cannot run before Phase B step 5 | INV-089 |
| Phase B is the earliest point the test load can run | INV-089 |

⚠️ **Why a guard.** INV-183 requires a rule binding a step to be nameable **at** that step, and a
`⛔` with no ID is one a later editor cannot look up and will "tidy" away. These seven were
uncited for weeks precisely because nothing could see them; a guard is what keeps the fix from
depending on the detector staying fixed.

⛔ **Asserts the structural property, not the prose (INV-219).** Each rule's wording is free to
change; what must not regress is that the paragraph stating it names its governing ID, and that
the invariant's own text still says the thing the citation promises.

No phrase-level pattern (#438): its only line read is of entries in `specs/INVARIANTS.md`; it reads
`plugins/` by blank-line paragraphs, in presence checks that fail closed, as #424 recorded
(INV-346).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"

# (file, a phrase unique to the rule, the invariant(s) that must be named in its paragraph)
TRIAGED = [
    ("bootcamp-onboarding/ground-rules.md",
     "is bash-only and expands to", ["INV-175"]),
    ("bootcamp-onboarding/ground-rules.md",
     "must never `exit` or `set -e`", ["INV-175"]),
    ("module-03-system-verification/phase1-verification.md",
     "A reachability probe must", ["INV-204"]),
    ("module-05-data-quality-mapping/phase2-data-mapping.md",
     "The source qualifier is required", ["INV-177"]),
    ("module-05-data-quality-mapping/phase2-data-mapping.md",
     "is a **required** parameter on", ["INV-136", "INV-200"]),
    ("module-06-data-processing/phaseA-build-loading.md",
     "Do not run it here", ["INV-089"]),
    ("module-06-data-processing/phaseB-load-first-source.md",
     "earliest point the test load can run", ["INV-089"]),
]

# What each citation promises, so a citation cannot survive the invariant changing under it.
PROMISES = {
    "INV-175": ["BASH_SOURCE", "zsh", "set -e"],
    "INV-204": ["get_capabilities", "search_docs"],
    "INV-177": ["source-qualified", "workspace"],
    "INV-136": ["analyze_record", "workspace_dir"],
    "INV-200": ["workspace_dir", "project"],
    "INV-089": ["SENZ2207", "before"],
}


def paragraph_containing(path, needle):
    """The blank-line-delimited block stating a rule, or None when the rule is gone."""
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        if needle in block:
            return block
    return None


def invariant_text(inv_id):
    for line in INVARIANTS.read_text(encoding="utf-8").splitlines():
        if line.startswith("- **%s**" % inv_id):
            return line
    return None


class EachTriagedRuleNamesItsInvariant(unittest.TestCase):
    def test_the_citation_is_in_the_paragraph_that_states_the_rule(self):
        for rel, needle, invs in TRIAGED:
            with self.subTest(rule=needle, file=rel):
                path = SKILLS / rel
                block = paragraph_containing(path, needle)
                self.assertIsNotNone(
                    block,
                    "the rule %r is gone from %s. If it was deliberately removed, remove its row "
                    "here too; if it moved, this test should follow it." % (needle, rel))
                for inv in invs:
                    self.assertIn(
                        inv, block,
                        "%s states %r without naming %s, which governs it. INV-183 requires the "
                        "rule to be nameable AT the step; this rule was uncited for weeks because "
                        "the detector could not see it.\n---\n%s" % (rel, needle, inv, block))


class EachCitedInvariantStillPromisesWhatIsClaimed(unittest.TestCase):
    """A citation that resolves to an ID is not the same as a citation that is right."""

    def test_the_invariant_text_still_covers_the_rule(self):
        for inv, cues in PROMISES.items():
            with self.subTest(invariant=inv):
                text = invariant_text(inv)
                self.assertIsNotNone(text, "%s is not defined in INVARIANTS.md" % inv)
                missing = [c for c in cues if c.lower() not in text.lower()]
                self.assertEqual(
                    [], missing,
                    "%s no longer mentions %s, so the rules citing it may now be citing the wrong "
                    "invariant -- the INV-134/INV-076 shape. Re-triage rather than editing this "
                    "list." % (inv, missing))


class NoRuleIsLeftInAnUncitedSection(unittest.TestCase):
    """The measured outcome of the triage, asserted so a regression is loud.

    ⚠️ Deliberately asserts **zero**, which is stricter than the historical baseline of 1. The
    triage cleared every hit, so any new one is either a genuinely new rule needing an invariant
    or a citation someone dropped -- both worth a failure. If a future run adds a rule it cannot
    yet register, the honest move is a recorded deferral in the ledger entry, not relaxing this.
    """

    def test_conformance_rules_reports_no_uncited_section(self):
        import subprocess
        import sys
        conf = REPO_ROOT / ".claude/skills/production-readiness-audit/conformance.py"
        proc = subprocess.run([sys.executable, str(conf), "rules"],
                              capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(0, proc.returncode, proc.stderr)
        m = re.search(r"(\d+) in a section citing no invariant", proc.stdout)
        self.assertIsNotNone(m, "`rules` output did not parse:\n%s" % proc.stdout)
        self.assertEqual(
            0, int(m.group(1)),
            "a hard rule sits in a section citing no invariant. Either register the rule (with "
            "the maintainer's sign-off on the wording) or cite the invariant that governs it:\n%s"
            % proc.stdout)


if __name__ == "__main__":
    unittest.main()
