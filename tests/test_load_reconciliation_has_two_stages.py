"""The load count is reconciled in two stages, and the sample it was loaded from is on record.

Phase B Step 7 compared the loader's success count against the source's `record_count` — the
count Data collection measured in the **collected** file — and nothing else. But Data collection
itself directs a working sample whenever the scenario is sized below the collected volume
(INV-277's ~10,000-record default), and Modules 5 and 6 map and load that sample. So every sampled
source differed from `record_count` by design:

    GLEIF   7,386 loaded of a 7,386-record load file   record_count 63,863
    ICIJ    2,367 loaded                                record_count 19,232

The explained branch named only mapping dispositions, so a guide either stretched it to cover a
sample or — reading it strictly — filed a complete, error-free load as `failed`, the outcome
INV-245's own text calls the worst. And the rule never compared against the one count that can
verify a load: the records the loader was actually given. Observed during a /dry-run phase-3
walk, Data processing Phase B, 2026-09-25 (issue #157).

⛔ **The sample was also recorded nowhere Module 6 could cite.** Module 4's registry schema had no
field for it — Step 6 said "document it in the registry" and Step 8b wrote a "sample manifest"
with no location — and Module 5 repoints `file_path` at its own output, so by Module 6 the trail
back to the sample was gone. A stage-2 rule that may cite a sample is only testable together with
the record it cites, which is why both halves are guarded here.

What is asserted:

1. **Step 7 (the owner, INV-300)** names the load input as the stage-1 baseline, lets only stage
   1 record `failed`, names the `sample:` block as a citable stage-2 cause, and routes an uncited
   stage-2 gap to `unexplained_delta`. Its old single-baseline sentence is gone.
2. **Module 6's reader sites are derived, never listed (INV-246):** every step outside Step 7 that
   carries the reconciliation invariant (INV-243) points at Step 7 rather than restating a
   baseline, and every step that presents the outcomes presents `unexplained_delta` as unverified.
3. **Module 4's schema defines `sample: {file_path, record_count, strategy, reason}`**, and every
   step that writes a sample file (derived by scanning, again INV-246) writes that block with a
   measured count and leaves `record_count` / `expected_record_count` untouched (INV-243).

Everything is asserted as behavior in shipped guidance, never as a helper, so any implementation
language satisfies it (INV-002). Stdlib only; shipped files are read as text (INV-108).

Enforces: **INV-243**, **INV-245**, **INV-246**, **INV-300** at the sites this issue touched.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE4 = SKILLS / "module-04-data-collection" / "SKILL.md"
MODULE6 = SKILLS / "module-06-data-processing"
PHASE_B = MODULE6 / "phaseB-load-first-source.md"

#: The single-baseline sentence #157 removed. Restoring it is this guard's negative control.
OLD_BASELINE = "against that existing `record_count` first"

#: What makes a Module 6 step a READER of the reconciled figure: it carries the invariant that
#: governs it. Keyed on the id, not on prose, because the id is what a later editor adds when a
#: new site presents a per-source count (INV-183). ⚠️ Keyed on **INV-243 alone**, deliberately:
#: INV-243 is the per-source reconciliation requirement itself, while INV-245 "generalizes
#: beyond per-source counts to any verified value" (its own text) — so a step citing only
#: INV-245 disposes of some OTHER verified value. Phase D's How-state audit (#154) is that case:
#: it cites INV-245 for an entity's record count against its construction history, which is
#: not a load count and has nothing to point at Step 7 for. Every load-count reader (Phase C
#: Steps 12 and 17, Phase D Step 27) cites INV-243, and the non-vacuity test below pins that.
READER = re.compile(r"INV-243\b")

#: A step that presents the OUTCOMES, rather than only reconciling its own figures.
PRESENTS_OUTCOMES = "`expected_delta`"

#: Baselines and counts the two-stage rule replaced. A reader still carrying one is a fork.
STALE = ("own input record count", "three-way reconciliation", "three reconciliation outcomes",
         OLD_BASELINE)

#: A step that WRITES a sample file: a write verb shortly before the samples directory.
SAMPLE_WRITE = re.compile(r"(?i)\b(save|write)\b[^.\n]{0,40}`data/samples/")


def squash(text):
    return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", text))


def sections(path):
    """[(heading, body)] split on `##`/`###` headings, outside fenced code blocks."""
    out, heading, body, fenced = [], "", [], False
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        if not fenced and re.match(r"#{2,3} ", line):
            out.append((heading, "\n".join(body)))
            heading, body = line.strip(), []
        else:
            body.append(line)
    out.append((heading, "\n".join(body)))
    return out


def step_7():
    for heading, body in sections(PHASE_B):
        if heading.startswith("## 7."):
            return squash(body)
    raise AssertionError("phaseB-load-first-source.md has no `## 7.` step")


def reader_sites():
    """Every Module 6 step, other than the owner, that carries INV-243 (INV-246)."""
    sites = []
    for path in sorted(MODULE6.glob("*.md")):
        for heading, body in sections(path):
            if path == PHASE_B and heading.startswith("## 7."):
                continue
            if READER.search(body):
                sites.append(("%s %s" % (path.name, heading), squash(body)))
    return sites


def sample_writers():
    """Every skill step that writes a file under `data/samples/` (derived, INV-246)."""
    sites = []
    for path in sorted(SKILLS.rglob("*.md")):
        for heading, body in sections(path):
            if SAMPLE_WRITE.search(squash(body)):
                sites.append(("%s %s" % (path.relative_to(SKILLS), heading), squash(body)))
    return sites


def stage_rows(text):
    """The reconciliation table's rows as (stage, outcome, load_status, record)."""
    rows = []
    for match in re.finditer(r"\| ([12]) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", text):
        rows.append(tuple(cell.strip() for cell in match.groups()))
    return rows


class StageOneIsTheLoadInput(unittest.TestCase):

    def setUp(self):
        self.text = step_7()

    def test_the_single_baseline_sentence_is_gone(self):
        """⛔ The negative control for #157: restoring this sentence must fail here."""
        self.assertNotIn(OLD_BASELINE, self.text)

    def test_stage_one_compares_against_the_load_input(self):
        self.assertIn("Stage 1 — the loaded count against the load input", self.text)
        self.assertIn("Compare the loader's success count against the **load input** first",
                      self.text)
        self.assertIn("the records the loader was actually given", self.text)

    def test_a_recorded_subset_limit_is_part_of_the_load_input(self):
        self.assertIn("**recorded subset limit**", self.text)
        self.assertIn("`sqlite_volume_prompt`", self.text)

    def test_only_stage_one_can_record_failed(self):
        self.assertIn("stage 1 is the only stage that can record `failed`", self.text)
        rows = stage_rows(self.text)
        self.assertGreaterEqual(len(rows), 4, rows)
        failing = [row for row in rows if "`failed`" in row[2]]
        self.assertEqual(["1"], [row[0] for row in failing], rows)
        for stage, outcome, status, _ in rows:
            if stage == "2":
                with self.subTest(outcome=outcome):
                    self.assertEqual("`loaded`", status)

    def test_stage_one_has_no_explained_branch(self):
        self.assertIn("It has no explained branch", self.text)


class StageTwoCitesTheSample(unittest.TestCase):

    def setUp(self):
        self.text = step_7()

    def test_stage_two_relates_the_load_input_to_the_collected_count(self):
        self.assertIn("Stage 2 — the load input against the collected `record_count`", self.text)

    def test_the_sample_block_is_a_citable_cause(self):
        self.assertIn("**the `sample:` block** Module 4 wrote into this source's registry "
                      "entry (collected → sample)", self.text)

    def test_the_mapping_citations_survive(self):
        self.assertIn("the source's own mapping specification", self.text)

    def test_an_uncited_gap_routes_to_unexplained_delta(self):
        self.assertIn("No citation → `unexplained_delta`", self.text)
        outcomes = {row[1].split("**")[1]: row for row in stage_rows(self.text)
                    if row[1].startswith("**")}
        self.assertIn("Unexplained delta", outcomes, outcomes)
        self.assertIn("load_count_matches_source: unexplained_delta",
                      outcomes["Unexplained delta"][3])
        self.assertIn("`issues` entry", outcomes["Unexplained delta"][3])

    def test_nothing_is_inferred_without_a_sample_block(self):
        self.assertIn("**No `sample:` block**", self.text)
        self.assertIn("Nothing is inferred from a file's name or location", self.text)

    def test_a_sample_plus_mapping_cites_both_in_order(self):
        self.assertIn("collected → sample → mapped", self.text)

    def test_the_observed_sampled_case_reconciles_as_expected_delta(self):
        self.assertIn("**7,386** of 7,386 with zero errors", self.text)
        self.assertIn("**63,863**", self.text)

    def test_step_7_declares_itself_the_owner(self):
        """INV-300 owner side: the pointers below need something to point at."""
        self.assertIn("This is the canonical statement of the two-stage load reconciliation",
                      self.text)
        self.assertIn("(INV-300)", self.text)


class EveryReaderPointsAtStepSeven(unittest.TestCase):
    """Module 6's reader sites, derived by scanning — never a list of three (INV-246)."""

    def test_the_sweep_is_not_vacuous(self):
        names = " | ".join(name for name, _ in reader_sites())
        for expected in ("phaseC-multi-source.md ## 12.", "phaseC-multi-source.md ## 17.",
                         "phaseD-validation.md ## 27."):
            self.assertIn(expected, names)

    def test_each_reader_points_at_the_owner(self):
        unpointed = [name for name, body in reader_sites()
                     if "`phaseB-load-first-source.md` Step 7" not in body
                     or "INV-300" not in body]
        self.assertEqual([], unpointed,
                         "a Module 6 step carries the reconciliation invariant (INV-243) without "
                         "pointing at Phase B Step 7 (INV-300)")

    def test_no_reader_keeps_a_replaced_baseline(self):
        for name, body in reader_sites():
            for stale in STALE:
                with self.subTest(site=name, stale=stale):
                    self.assertNotIn(stale, body)

    def test_each_outcome_presenter_shows_unexplained_delta_as_unverified(self):
        presenters = [(name, body) for name, body in reader_sites()
                      if PRESENTS_OUTCOMES in body]
        self.assertGreaterEqual(len(presenters), 2, [name for name, _ in presenters])
        for name, body in presenters:
            with self.subTest(site=name):
                self.assertRegex(body, r"`unexplained_delta`.{0,200}unverified|"
                                       r"unverified.{0,200}`unexplained_delta`")

    def test_step_17_reconciles_against_the_load_input(self):
        body = dict(reader_sites())
        step17 = next(text for name, text in body.items()
                      if name.startswith("phaseC-multi-source.md ## 17."))
        self.assertIn("that source's load input", step17)


class ModuleFourRecordsTheSample(unittest.TestCase):

    def setUp(self):
        self.text = squash(MODULE4.read_text(encoding="utf-8"))

    def test_the_schema_defines_the_sample_block(self):
        self.assertIn("`sample: {file_path, record_count, strategy, reason}`", self.text)

    def test_the_schema_count_is_measured_from_the_written_file(self):
        self.assertIn("record count **measured** from that written file", self.text)

    def test_the_schema_keeps_the_collected_baseline(self):
        self.assertIn("Writing it never touches the source's top-level `record_count` or "
                      "`expected_record_count`", self.text)

    def test_a_substitute_dataset_gets_no_sample_block(self):
        self.assertIn("write no `sample:` block", self.text)

    def test_the_unlocated_manifest_is_gone(self):
        self.assertNotIn("sample manifest", self.text)


class EverySampleWriterWritesTheBlock(unittest.TestCase):
    """Every step that writes a sample file records it (derived, INV-246)."""

    def test_the_sweep_is_not_vacuous(self):
        names = " | ".join(name for name, _ in sample_writers())
        self.assertIn("### 6.", names)
        self.assertIn("### 8b.", names)

    def test_each_writer_records_a_measured_sample_block(self):
        for name, body in sample_writers():
            with self.subTest(site=name):
                self.assertIn("`sample:` block", body)
                self.assertRegex(body, r"`record_count` \*\*measured\*\* from the written file")
                self.assertIn("`record_count` and `expected_record_count` untouched", body)


if __name__ == "__main__":
    unittest.main()
