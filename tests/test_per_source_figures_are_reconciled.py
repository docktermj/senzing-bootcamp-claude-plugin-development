"""Every site that persists or presents a per-source figure carries the reconciliation rule.

INV-243 requires a per-source figure shown to the Bootcamper to be reconciled against that
source's own input count before it is shown; INV-245 requires a value that failed its own
check not to be presented as a result. Both were registered on 2026-08-14 and both were
cited in exactly one place — `phaseC-multi-source.md` step 17.

Phase C is **conditional**: its own gate skips the entire file unless the Bootcamper has two
or more sources. So the invariants reached a path many Bootcampers never take, while the
paths everyone takes were uncovered:

    phaseB step 7   writes record_count as "the actual loaded count" into durable state
    phaseC step 12  reads that value straight back out and presents it in a summary table
    phaseD step 27  writes per-source statistics into docs/loading_strategy.md

A count written unreconciled at the first and displayed at the second has exactly the shape
INV-243 exists for — plausible, monotonic, summing correctly — and the audit trail ends at a
registry field nobody compared to an input file.

⛔ **The site set is derived, not listed (INV-246).** Hardcoding three paths would encode the
belief that these are the sites, which is the belief that was wrong when this defect was
created: INV-243 was cited where its defect was *discovered* rather than where it *governs*.
A derived guard fails on a fourth site nobody thought of, which is the only way the class
stays fixed rather than the instance.

`coverage_reports.py shipped` structurally cannot do this job: it reports invariants cited by
**no** shipped file, so one citation scores as covered. It answers "mentioned anywhere?",
never "mentioned everywhere it binds?".

Enforces **INV-243** and **INV-245** across their full binding surface.

Source spec: `specs/inv243-reconciliation-binds-more-sites-than-it-reaches.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"

#: A block that PERSISTS a per-source figure into the registry: the literal field, the
#: registry file, and a write verb. Deliberately narrow. `record count` in prose is
#: overloaded — `phase2-discover.md` uses it for an entity's record count and Module 4 for a
#: license limit — and a guard that sweeps those fails on correct content, which is worse
#: than one that misses. The registry write is the action INV-243 actually triggers on.
FIELD = "`record_count`"
REGISTRY = "data_sources.yaml"
WRITE = re.compile(r"\b(update|Record|record it|write|set)\b")

#: Coverage is the invariant ID, not prose: the ID is what a later editor can look up
#: (INV-183). INV-228 counts too — it is the acquisition-stage statement of the same
#: discipline, and Module 4's registry entry predates INV-243 while implementing it.
COVERAGE = re.compile(r"INV-243|INV-245|INV-228")


def squash(text):
    return re.sub(r"\s+", " ", text)


def persist_sites():
    """Every block that writes a per-source count into the registry.

    ⛔ **Derived, never listed (INV-246).** Hardcoding the paths would encode the belief
    that these are the sites — the belief that was wrong when INV-243 was cited only where
    its defect was discovered. A new module writing `record_count` to the registry is
    caught the moment it does so, without this file naming it.
    """
    sites = []
    for path in sorted(SKILLS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for block in re.split(r"\n\s*\n", text):
            flat = squash(block)
            if FIELD in flat and REGISTRY in flat and WRITE.search(flat):
                # The coverage window runs past the block, because the house idiom puts a
                # ⛔ qualifier in the block *after* the instruction it qualifies. Bounded
                # rather than whole-file: a citation 400 lines away is not "in reach".
                start = text.index(block)
                sites.append((path, block, squash(text[start:start + len(block) + 1400])))
    return sites


#: The second way a per-source figure becomes durable: written into a deliverable rather
#: than the registry. A distinct signal because it has a distinct failure mode — nothing
#: downstream re-derives a number in `docs/loading_strategy.md`, so it is the hardest of
#: the sites to correct once wrong.
DELIVERABLE = "per-source statistics"


def deliverable_sites():
    """Every block writing per-source figures into a document (derived, INV-246)."""
    sites = []
    for path in sorted(SKILLS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for block in re.split(r"\n\s*\n", text):
            if DELIVERABLE in squash(block):
                start = text.index(block)
                sites.append((path, squash(text[start:start + len(block) + 1400])))
    return sites


class EveryDeliverableSiteCarriesTheRule(unittest.TestCase):
    """Added after a mutation escaped: reverting Phase D passed every other test here.

    The persist predicate keys on the registry field, and Phase D writes into
    `docs/loading_strategy.md` instead — so it was outside the derived set entirely and
    criterion 3 was unguarded. Two durable destinations, two signals.
    """

    def test_the_deliverable_site_is_discovered(self):
        names = {path.name for path, _ in deliverable_sites()}
        self.assertIn("phaseD-validation.md", names, sorted(names))

    def test_each_deliverable_site_cites_the_rule(self):
        uncovered = [
            path.name for path, window in deliverable_sites()
            if not COVERAGE.search(window)
        ]
        self.assertEqual(
            [], uncovered,
            "per-source statistics written to a deliverable with no reconciliation rule "
            "in reach: %s" % uncovered,
        )


class TheSweepIsNotVacuous(unittest.TestCase):
    """A derived sweep that finds nothing passes every other test in this file."""

    def test_the_known_persist_sites_are_discovered(self):
        names = {path.name for path, _, _ in persist_sites()}
        self.assertIn("phaseB-load-first-source.md", names)
        self.assertIn("SKILL.md", names)  # module-04-data-collection, both registry blocks
        self.assertGreaterEqual(len(persist_sites()), 3, names)


class EveryPersistSiteCarriesTheRule(unittest.TestCase):
    """The criterion: the rule is reachable where the number is written down."""

    def test_each_persist_site_cites_the_reconciliation_invariants(self):
        uncovered = [
            "%s :: %s" % (path.name, flat[:90])
            for path, _, flat in persist_sites()
            if not COVERAGE.search(flat)
        ]
        self.assertEqual(
            [], uncovered,
            "a per-source count is written to the registry with no reconciliation rule in "
            "reach:\n  " + "\n  ".join(uncovered),
        )


class TheLoadBearingSiteStatesTheWholeRule(unittest.TestCase):
    """Phase B is where the figure enters durable state; everything later reads it."""

    def setUp(self):
        self.text = squash(
            (SKILLS / "module-06-data-processing" / "phaseB-load-first-source.md")
            .read_text(encoding="utf-8")
        )

    def test_it_requires_the_comparison_against_the_recorded_baseline(self):
        """Stronger than the spec asked: the baseline is the value being overwritten.

        Phase B writes the loaded count into `record_count` — the same field Data
        collection used for the count it measured in the collected file. So the figure the
        reconciliation needs is destroyed by the very write it is meant to check, unless
        the comparison happens first. The spec said "compare against the input file"; the
        registry already holds that number, and reusing it keeps one source of truth.
        """
        self.assertIn("the value you are about to overwrite is the baseline", self.text)
        # #157: the single-baseline sentence ("Compare the loader's success count against
        # that existing `record_count` first") filed every sampled source as a delta. The
        # load is now checked first against what the loader was GIVEN, and `record_count`
        # is the second, collected baseline — still read, never overwritten.
        self.assertNotIn("against that existing `record_count` first", self.text)
        self.assertIn("Compare the loader's success count against the **load input** first",
                      self.text)
        self.assertIn("the load input against the collected `record_count`", self.text)

    def test_the_outcome_is_recorded_in_the_registrys_own_idiom(self):
        """Consistency: Data collection already records `record_count_matches_expected`."""
        self.assertIn("load_count_matches_source", self.text)
        self.assertIn("validation_checks", self.text)

    def test_a_mismatch_does_not_overwrite_the_baseline(self):
        self.assertIn("leave the existing `record_count` in place", self.text)

    def test_it_says_why_this_site_is_the_one_that_matters(self):
        """Without the reason, a later editor moves the check downstream."""
        self.assertIn("never checked at all", self.text)

    def test_a_disagreement_is_written_rather_than_the_count(self):
        self.assertIn("write the discrepancy rather than the count", self.text)
        self.assertIn("INV-245", self.text)

    def test_the_aggregate_does_not_discharge_it(self):
        """The defect produces figures that sum correctly; that is the trap."""
        self.assertIn("plausible and sum correctly", self.text)


class ThePresentationSiteIsCovered(unittest.TestCase):
    """Phase C step 12 displays what Phase B wrote — INV-243's literal trigger."""

    def test_step_12_states_the_table_carries_the_requirement(self):
        text = (SKILLS / "module-06-data-processing" / "phaseC-multi-source.md").read_text(
            encoding="utf-8")
        start = text.index("## 12. Inventory all data sources")
        step12 = squash(text[start:text.index("## 13.", start)])
        self.assertIn("INV-243", step12)
        self.assertIn("unverified", step12)


if __name__ == "__main__":
    unittest.main()
