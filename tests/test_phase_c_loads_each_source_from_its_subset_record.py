"""Every source Phase C loads under a whole-load cap loads from its own `load_subset:` block.

#237 made Phase B Step 7 record every subset choice once, in a per-source `load_subset:` block
(the `load-subset-record` anchor), beside two whole-load markers: `license_cap_prompt` and
`sqlite_volume_prompt` with `choice: "subset"`. But Phase B loads only the first source, and
both limits cover the whole load: the license cap counts every record in the repository, and
the SQLite first-N choice is recorded once. Phase C Steps 12, 17 and 19 said nothing about how
the remaining budget is split across the later sources, or that each writes its own block, and
had no license-capacity check at all. A later source then loaded with no subset record, and its
reconciliation reached `failed` (a license error mid-load) or `unexplained_delta` (a gap only a
subset could explain, with none recorded). Issue #238.

The shape Phase C now has:

- **Step 17 computes the per-source budget table** (source, fill order, limit) from the two
  markers and the remaining cap, before the orchestrator is written, so the plan is fixed before
  the run. It points at #237's one definition rather than restating it (INV-300), and asks
  Phase B's license-cap question only when no matching marker exists, once, by pointer (INV-006).
- **Step 19 re-reads the markers and re-measures the remaining cap** after Step 18's test load,
  then writes every remaining source's block from its row **before the run starts**, in Step
  14's load order, under every loading strategy. No block is written once a load has started.
- **Step 18 test-loads no source whose row is not loaded**, so the test load spends none of a
  cap that has nothing left for it.
- **The orchestrator (Step 17) reads each source's block** and loads exactly the input it names;
  stage 1 compares against that input.
- **Step 12 shows the block.**

What is asserted, and how the sites are found:

1. **The load paths are derived, never listed (INV-246).** They are the numbered options of
   Step 15's strategy menu; each must have a Step 19 bullet that writes every row's
   `load_subset:` block first, then starts or launches the loads, which read them. A bullet that
   writes any block after its loads start fails, Sequential included: that interleaving is what
   the race's first draft shipped, and the issue's first criterion says every block is written
   before the run starts, for every strategy. Adding a fourth strategy to the menu without
   saying how its blocks are written fails here too.
2. **The license-cap choices are derived from #237's definition**: every `choice` value the
   `license_cap_prompt` definition names must have its own Step 17 budget rule.
3. Step 17 reads both markers and the remaining cap by pointer; its orchestrator loads from the
   block, never writes one, and stage 1 compares against it. Step 19 re-reads both markers and
   re-measures.
4. No Phase C text copies Phase B's pinned license-cap question or the schemas (INV-300).

Asserted as behavior in shipped guidance, never as a helper, so any language satisfies it
(INV-002). Stdlib only; shipped files are read as text (INV-108).

Enforces: **INV-006**, **INV-244**, **INV-246**, **INV-300** at the sites #238 touched.

Enforces **INV-320** (Phase C fixes every later source's limit before the run and writes each
`load_subset:` block before any load starts, under every strategy). ⚠️ It pins Steps 17 to 19's
text and cannot establish that a live loader honors the limits -- only a real load shows that.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE6 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-06-data-processing"
PHASE_B = MODULE6 / "phaseB-load-first-source.md"
PHASE_C = MODULE6 / "phaseC-multi-source.md"

POINTER = "phaseB-load-first-source.md#load-subset-record"
BLOCK = "`load_subset:`"
MARKERS = ("`license_cap_prompt`", "`sqlite_volume_prompt`")
PREFERENCES = "`config/bootcamp_preferences.yaml`"

#: A numbered strategy in Step 15's pinned menu: `1. **Sequential** — ...`.
STRATEGY = re.compile(r"^\d+\.\s+\*\*(\w+)\*\*", re.MULTILINE)
#: The license-cap choices, read from #237's definition of the marker.
LICENSE_CHOICES = re.compile(r"`choice` is `(\w+)` \(option \d\) or `(\w+)` \(option \d\)")
#: What starts a load in a Step 19 strategy bullet.
LAUNCH = re.compile(r"\b(start|launch)\b")
#: A write verb, in any form ("write", "writes", "written", "writing").
WRITE = re.compile(r"\bwrit(e|es|ten|ing)\b", re.IGNORECASE)


def squash(text):
    return re.sub(r"\s+", " ", text)


def step(number, path=PHASE_C):
    text = path.read_text(encoding="utf-8")
    start = text.index("\n## %d. " % number)
    return text[start:text.index("\n## %d. " % (number + 1), start)]


def strategies():
    """Step 15's loading strategies, read from its numbered menu (INV-246)."""
    return STRATEGY.findall(step(15))


def strategy_bullet(name):
    """Step 19's `- **<name>:**` bullet, squashed, up to the next bullet or paragraph."""
    match = re.search(r"^- \*\*%s:\*\*(.*?)(?=^- \*\*|^\s*$)" % re.escape(name), step(19),
                      re.MULTILINE | re.DOTALL)
    return squash(match.group(1)) if match else None


def license_choices():
    match = LICENSE_CHOICES.search(squash(PHASE_B.read_text(encoding="utf-8")))
    if match is None:
        raise AssertionError("Phase B Step 7 no longer defines the `license_cap_prompt` choices")
    return match.groups()


def budget_table():
    """Step 17's budget-table text: from its heading sentence to the orchestrator paragraph."""
    text = squash(step(17))
    start = text.index("**First, compute the per-source budget table")
    return text[start:text.index("**(INV-320) Then the orchestrator loads each source", start)]


class EveryLoadPathWritesThenReadsTheBlock(unittest.TestCase):
    """Criterion 8 (first half): derived from Step 15's menu, never a list of three."""

    def test_the_menu_is_not_vacuous(self):
        self.assertGreaterEqual(len(strategies()), 3, strategies())

    def test_each_strategy_writes_every_block_before_its_loads_start(self):
        for name in strategies():
            with self.subTest(strategy=name):
                bullet = strategy_bullet(name)
                self.assertIsNotNone(bullet, "Step 19 has no `- **%s:**` bullet saying how "
                                             "its sources' blocks are written" % name)
                launch = LAUNCH.search(bullet)
                self.assertIsNotNone(launch, bullet)
                before, after = bullet[:launch.start()], bullet[launch.end():]
                self.assertIn("write every row's %s block first" % BLOCK, before, bullet)
                self.assertIn("read", after, bullet)

    def test_no_strategy_writes_a_block_after_its_loads_start(self):
        """Criterion 1: written before the run starts, for every strategy. A write verb after
        the bullet's first start or launch is a block written mid-run."""
        for name in strategies():
            with self.subTest(strategy=name):
                bullet = strategy_bullet(name)
                self.assertIsNotNone(bullet, name)
                launch = LAUNCH.search(bullet)
                self.assertIsNotNone(launch, bullet)
                late = WRITE.search(bullet, launch.end())
                self.assertIsNone(late, "the %s bullet writes after its loads start: %r"
                                  % (name, bullet))

    def test_step_19_writes_every_block_before_the_run(self):
        text = squash(step(19))
        self.assertIn("**(INV-320) Every remaining source's `load_subset:` block is written before the "
                      "run starts, in Step 14's load order, for every loading strategy, and the "
                      "loader reads it**", text)
        self.assertIn("`config/data_sources.yaml`", text)
        self.assertIn("A **full** row writes none", text)
        self.assertIn("No block is written once any load has started", text)
        self.assertLess(text.index("The table is then fixed for the run"),
                        text.index("**(INV-320) Every remaining source's `load_subset:` block is written"),
                        "the blocks must be written from the fixed table, after the re-measure")


class StepNineteenReadsTheWholeLoadMarkers(unittest.TestCase):
    """Criterion 8 (second half): the marker read, and the re-measure after Step 18."""

    def setUp(self):
        self.text = squash(step(19))

    def test_it_re_reads_both_markers(self):
        for marker in MARKERS:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)
        self.assertIn("Re-read `license_cap_prompt` and `sqlite_volume_prompt` in "
                      + PREFERENCES, self.text)

    def test_it_re_measures_the_remaining_cap_by_pointer(self):
        self.assertIn("re-measure the remaining cap", self.text)
        self.assertIn(POINTER, self.text)
        self.assertIn("Step 18's test load", self.text)

    def test_the_table_is_fixed_before_the_run(self):
        self.assertIn("**Before the run starts", self.text)
        self.assertIn("The table is then fixed for the run", self.text)

    def test_an_exhausted_budget_starts_no_load_and_is_named(self):
        self.assertIn("**(INV-320) A not-loaded row starts no load.**", self.text)
        self.assertIn("Leave its `load_status` unchanged, never `failed`", self.text)
        self.assertIn("not loaded because license capacity ran out", self.text)


class StepSeventeenFixesThePlan(unittest.TestCase):
    """Step 17 computes and shows the table, from the markers, by pointer (INV-300)."""

    def setUp(self):
        self.text = budget_table()

    def test_it_reads_both_markers_from_preferences(self):
        for marker in MARKERS:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)
        self.assertIn(PREFERENCES, self.text)

    def test_it_points_at_the_one_definition(self):
        self.assertIn(POINTER, self.text)
        self.assertIn("do not restate it here (INV-300)", self.text)

    def test_it_shows_source_fill_order_and_limit(self):
        for column in ("**source**", "**fill order** (Step 14's load order)", "**limit**"):
            with self.subTest(column=column):
                self.assertIn(column, self.text)

    def test_every_license_choice_has_its_own_rule(self):
        choices = license_choices()
        self.assertEqual(("overlap_preserving", "first_n"), choices)
        for choice in choices:
            with self.subTest(choice=choice):
                self.assertIn("- **`license_cap_prompt.choice: %s`**" % choice, self.text)

    def test_overlap_preserving_computes_no_new_budget(self):
        self.assertIn("Each row takes its source's block, and no new budget is computed",
                      self.text)
        self.assertIn("`data/subsets/`", self.text)
        self.assertIn("A block with `record_count: 0` is a **not loaded** row", self.text)

    def test_first_n_fills_the_remaining_cap_in_load_order(self):
        self.assertIn("the budget is the remaining cap", self.text)
        self.assertIn("Fill it in Step 14's load order", self.text)
        self.assertIn("N = min(its load-input count, the budget left)", self.text)
        self.assertIn("`load_subset: {strategy: first_n, limit: N, reason: license_cap}`",
                      self.text)
        self.assertIn("A row whose N equals its load input is **full** and gets no block",
                      self.text)

    def test_the_sqlite_subset_is_per_source(self):
        self.assertIn("`sqlite_volume_prompt` with `choice: \"subset\"`", self.text)
        self.assertIn("a limit **per source**, never a total split across the sources",
                      self.text)
        self.assertIn("`reason: sqlite_volume`", self.text)
        self.assertIn("a row's limit is the smaller of the two, and its `reason` names the "
                      "limit that bound it", self.text)

    def test_no_marker_asks_phase_bs_question_once_by_pointer(self):
        self.assertIn("put Phase B Step 7's license-cap question **once, for all the remaining "
                      "sources together** (INV-006)", self.text)
        self.assertIn("point at them and do not copy them (INV-300)", self.text)
        self.assertIn("module-04-data-collection/SKILL.md#overlap-preserving-sampling",
                      self.text)
        self.assertIn("When the remaining loads fit under the cap, ask nothing", self.text)

    def test_a_marker_under_a_different_limit_does_not_match(self):
        self.assertIn("one recorded under a different `license_record_limit`", self.text)

    def test_an_unmeasurable_cap_is_indeterminate(self):
        self.assertIn("⛔ **A remaining cap that cannot be measured is indeterminate, never "
                      "estimated (INV-244).**", self.text)
        self.assertIn("Say the figure is currently unavailable", self.text)


class TheOrchestratorLoadsFromTheBlock(unittest.TestCase):
    """Criterion 6: the loader reads the block, stops on purpose, and stage 1 compares to it."""

    def setUp(self):
        self.text = squash(step(17))

    def test_it_reads_each_sources_block_when_its_load_starts(self):
        self.assertIn("**(INV-320) Then the orchestrator loads each source from its `load_subset:` "
                      "block.**", self.text)
        self.assertIn("read that source's block from `config/data_sources.yaml`", self.text)

    def test_it_loads_the_input_the_block_names(self):
        self.assertIn("for `overlap_preserving`, the subset file at the block's `file_path`",
                      self.text)
        self.assertIn("the first `limit` records of the registry `file_path`, stopping there on "
                      "purpose, not at the license error", self.text)

    def test_stage_one_compares_against_that_input(self):
        self.assertIn("its stage-1 reconciliation below compares against", self.text)
        self.assertIn("including one the license error stops, is a stage-1 mismatch", self.text)
        self.assertIn("the input its `load_subset:` block names when it has one", self.text)

    def test_the_must_handle_list_names_it(self):
        self.assertIn("loading each source from its `load_subset:` block", self.text)

    def test_the_orchestrator_reads_the_block_and_never_writes_one(self):
        """A loader that wrote its own block would write it after the run started."""
        start = self.text.index("**(INV-320) Then the orchestrator loads each source")
        paragraph = self.text[start:self.text.index("Must handle:", start)]
        self.assertIsNone(WRITE.search(paragraph), paragraph)


class StepEighteenSkipsANotLoadedSource(unittest.TestCase):
    """A test load for a source with no budget spends a cap that has nothing left for it."""

    def test_a_not_loaded_row_gets_no_test_load(self):
        text = squash(step(18))
        self.assertIn("A source whose Step 17 budget-table row is **not loaded** gets no test "
                      "load either", text)
        self.assertIn("would count against a remaining cap", text)


class StepTwelveShowsTheBlock(unittest.TestCase):
    """Criterion 7."""

    def test_it_shows_the_block_for_loaded_and_unloaded_sources(self):
        text = squash(step(12))
        self.assertIn("**Show a source's `load_subset:` block when it has one.**", text)
        self.assertIn(POINTER, text)
        self.assertIn("\"→ subset\" step of that source's reconciliation chain", text)
        self.assertIn("the subset that source will load", text)


class NothingIsCopiedFromPhaseB(unittest.TestCase):
    """INV-300: the pinned question and its options stay Phase B's."""

    def test_phase_c_carries_no_copy_of_the_license_question(self):
        text = PHASE_C.read_text(encoding="utf-8")
        question = re.search(r"👉 \*\*(Your dataset is larger than this license allows[^*]*)\*\*",
                             PHASE_B.read_text(encoding="utf-8"))
        self.assertIsNotNone(question, "Phase B's pinned license-cap question moved")
        self.assertNotIn(question.group(1), text)
        for label in ("Load an overlap-preserving subset now", "Apply a license I have",
                      "Load the first records as they come"):
            with self.subTest(label=label):
                self.assertNotIn(label, text)


if __name__ == "__main__":
    unittest.main()
