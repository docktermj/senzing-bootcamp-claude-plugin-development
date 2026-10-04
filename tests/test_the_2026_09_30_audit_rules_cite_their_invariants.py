"""Seven hard rules the 2026-09-30 audit found uncited, or mis-cited, keep naming their invariant.

`production-readiness-audit-2026-09-30` (findings B-F5, B-F6, B-F7 and B-F10, issue #290) found
seven `⛔` rules that cited no invariant, or the wrong one, although a registered invariant
governs each:

| Rule | Governing invariant |
|---|---|
| `submission blocked:` is an outcome where the report is still owed | INV-281 |
| `pending_invariants.blocks()` keeps the block boundaries the ONE definition | INV-308 (was INV-315) |
| `invariant-manifest.json` lives at the repository root, not in `specs/` | INV-307 |
| the loading scaffold's counters are process-global | INV-243 |
| the discoveries-PDF generator ships inside the plugin | INV-185 |
| `generate_scaffold` returns a listing, not code | INV-234 |
| on a mixed-type source, send an enum-valid `record_type` | INV-280 |

⚠️ **Why a guard.** INV-183 requires a rule binding a step to be nameable **at** that step, and
a `⛔` with no ID is one a later editor cannot look up. Each citation is asserted **in the window
`conformance.py` reads** (the rule's own line plus the next non-blank line on either side), by
calling the script's own `own_citations`, so this guard and the audit cannot disagree about what
"at the line" means.

⛔ **Asserts the structural property, not the prose (INV-219).** Each rule's wording is free to
change; what must not regress is that its window names the governing ID, and that the
invariant's own text still says the thing the citation promises.

Stdlib only; `conformance.py` is loaded by path and nothing under `plugins/` is imported
(INV-108).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = "plugins/senzing-bootcamp/skills/"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
CONFORMANCE = REPO_ROOT / ".claude/skills/production-readiness-audit/conformance.py"

# (file, a phrase unique to the rule's own line, the invariant its window must cite)
RULES = [
    (".claude/skills/feedback-to-issues/SKILL.md",
     "is an outcome where the report is STILL OWED", "INV-281"),
    (".claude/skills/review-invariants/pending_invariants.py",
     "It exists so the block boundaries below stay the ONE definition", "INV-308"),
    (".claude/skills/review-invariants/invariant_manifest.py",
     "At the repository root, NOT in `specs/`", "INV-307"),
    (SKILLS + "module-06-data-processing/phaseC-multi-source.md",
     "The loading scaffold's counters are process-global", "INV-243"),
    (SKILLS + "module-07-query-visualize-discover/phase1-query-visualize.md",
     "It ships inside the plugin, not in the", "INV-185"),
    (SKILLS + "module-03-system-verification/phase1-verification.md",
     "`generate_scaffold` returns a **listing**, not code", "INV-234"),
    (SKILLS + "module-05-data-quality-mapping/phase2-data-mapping.md",
     "On a mixed-type source, send an enum-valid `record_type`", "INV-280"),
]

# What each citation promises, so a citation cannot survive the invariant changing under it.
PROMISES = {
    "INV-281": ["submission blocked", "still owed"],
    "INV-308": ["one definition"],
    "INV-307": ["read-only archive", "invariant-manifest.json"],
    "INV-243": ["per-source", "process-global"],
    "INV-185": ["CLAUDE_PLUGIN_ROOT", "bundled"],
    "INV-234": ["listing", "generate_scaffold"],
    "INV-280": ["declared schema", "parameters it accepts"],
}


def _load_conformance():
    """`conformance.py` as a module, so the window is the script's, never a copy."""
    spec = importlib.util.spec_from_file_location("_conformance_290", CONFORMANCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def invariant_text(inv_id):
    for line in INVARIANTS.read_text(encoding="utf-8").splitlines():
        if line.startswith("- **%s**" % inv_id):
            return line
    return None


class EachRuleCitesItsInvariantAtItsLine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conformance = _load_conformance()

    def window_citations(self, rel, needle):
        # Line-scoped by design (#424): ``own_citations`` is conformance.py's line-indexed
        # window (the rule's line and one non-blank line either side), and a needle that
        # wrapped would be found zero times and fail the count, never pass it.
        lines = (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
        hits = [i for i, line in enumerate(lines) if needle in line]
        self.assertEqual(
            1, len(hits),
            "expected the rule %r exactly once in %s, found %d. If it was reworded, move this "
            "row's phrase with it; if it was removed, remove the row." % (needle, rel, len(hits)))
        return self.conformance.own_citations(lines, hits[0])

    def test_the_governing_invariant_is_cited_in_the_rules_window(self):
        for rel, needle, inv in RULES:
            with self.subTest(rule=needle, file=rel):
                cited = self.window_citations(rel, needle)
                self.assertIn(
                    inv, cited,
                    "%s states %r without naming %s at its line, which governs it (INV-183). "
                    "The window conformance.py reads cites only %s." % (rel, needle, inv, cited))

    def test_the_one_definition_rule_no_longer_cites_inv_315(self):
        """Row 2 replaces INV-315: the sentence states INV-308's one-definition rule."""
        rel, needle, _inv = RULES[1]
        self.assertNotIn("INV-315", self.window_citations(rel, needle))


class EachCitedInvariantStillPromisesWhatIsClaimed(unittest.TestCase):
    """A citation that resolves to an ID is not the same as a citation that is right."""

    def test_every_row_has_a_promise(self):
        self.assertEqual(sorted({inv for _r, _n, inv in RULES}), sorted(PROMISES))

    def test_the_invariant_text_still_covers_the_rule(self):
        for inv, cues in PROMISES.items():
            with self.subTest(invariant=inv):
                text = invariant_text(inv)
                self.assertIsNotNone(text, "%s is not defined in INVARIANTS.md" % inv)
                missing = [c for c in cues if c.lower() not in text.lower()]
                self.assertEqual(
                    [], missing,
                    "%s no longer mentions %s, so the rule citing it may now cite the wrong "
                    "invariant. Re-read the rule against the invariant rather than editing this "
                    "list." % (inv, missing))


if __name__ == "__main__":
    unittest.main()
