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
4. **Module 4 Step 8b's `sample` decision holds exactly one chain role in Step 7: the sample
   step** (#221). #157 also listed it as a recorded subset limit, in the stage-1 sentence and the
   stage-2 subset bullet, so one decision could be cited as two chain steps, and stage 1 compared
   against "first N" of a file that was already the sample. Neither subset site names Step 8b;
   the stage-2 sample bullet does.
5. **Every subset Phase B chooses is recorded once, in `load_subset:`, and cited from it** (#237).
   License-cap options 1 and 3 and the SQLite first-1,000 choice loaded fewer records than the
   load input and recorded nothing Step 7 could cite, so a clean capped load read as `failed` or
   `unexplained_delta`. Step 7 now defines the record once (the `load-subset-record` anchor):
   the `load_subset:` fields, `data/subsets/`, the `license_cap_prompt` marker, the
   `sqlite_volume_prompt` `choice: "subset"` value, and the remaining cap. The subset-choosing
   options are **derived from the text**, never listed: every numbered option of Step 7's pinned
   license question whose label loads fewer records, and every "start with the first N records"
   suggestion. Each must write `load_subset:` by pointing at the definition, with values that
   match its own label or N. Stage 1 and the stage-2 subset bullet cite `load_subset:` and not
   `sqlite_volume_prompt`.

Everything is asserted as behavior in shipped guidance, never as a helper, so any implementation
language satisfies it (INV-002). Stdlib only; shipped files are read as text (INV-108).

Enforces: **INV-243**, **INV-245**, **INV-246**, **INV-300** at the sites this issue touched, and
(#237) the **INV-006** and **INV-244** citations the subset record carries.

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


def chain_part(text, start, end):
    """The squashed Step 7 text from `start` up to (not including) `end`."""
    match = re.search(re.escape(start) + r"(.*?)" + re.escape(end), text)
    if match is None:
        raise AssertionError("Step 7 has no text between %r and %r" % (start, end))
    return start + match.group(1)


def stage_one(text):
    return chain_part(text, "1. **Stage 1 —", "2. **Stage 2 —")


def sample_bullet(text):
    return chain_part(text, "- **the `sample:` block**", "- **a mapping disposition**")


def subset_bullet(text):
    return chain_part(text, "- **the `load_subset:` block**",
                      "⛔ **Four outcomes across two stages")


#: Module 4 Step 8b, named in any form ("Step 8b", "Module 4 Step 8b", "the Step 8b load ...").
STEP_8B = re.compile(r"\b8b\b")


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
        part = stage_one(self.text)
        self.assertIn("**recorded subset limit**", part)
        self.assertIn("`load_subset:` block", part)

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


class StepEightBHasOneChainRole(unittest.TestCase):
    """#221: Step 8b's `sample` decision is the sample step, never also a subset limit."""

    def setUp(self):
        self.text = step_7()

    def test_the_stage_one_subset_limit_does_not_name_step_8b(self):
        """⛔ Negative control: restoring "or Module 4 Step 8b's `sample` load decision" fails."""
        part = stage_one(self.text)
        self.assertIn("**recorded subset limit**", part)
        self.assertIn("`load_subset:`", part)
        self.assertIsNone(STEP_8B.search(part), part)

    def test_the_stage_two_subset_bullet_does_not_name_step_8b(self):
        """⛔ Negative control: restoring "or the Step 8b load decision that set it" fails."""
        part = subset_bullet(self.text)
        self.assertIn("`load_subset:` block", part)
        self.assertIsNone(STEP_8B.search(part), part)

    def test_the_sample_bullet_names_step_8b_as_a_writer_of_the_block(self):
        part = sample_bullet(self.text)
        self.assertIn("Step 8b's `sample` load decision", part)
        self.assertIn("Step 6's sample files", part)

    def test_step_8b_appears_in_the_chain_only_in_the_sample_bullet(self):
        chain = chain_part(self.text, "1. **Stage 1 —", "⛔ **Four outcomes across two stages")
        self.assertEqual(len(STEP_8B.findall(sample_bullet(self.text))),
                         len(STEP_8B.findall(chain)), chain)


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


#: The one definition (#237), and the pointer every subset-choosing site carries to it.
SUBSET_ANCHOR = '<a id="load-subset-record"></a>'
POINTER = "as [the subset record](#load-subset-record) defines"
SUBSET_SCHEMA = "`load_subset: {strategy, limit, file_path, record_count, reason}`"
LICENSE_MARKER_SCHEMA = "`{decided: true, choice, license_record_limit}`"

#: A numbered option in a pinned question: `> 1. **Label** — gloss`.
OPTION = re.compile(r"^\s*>\s*(\d+)\.\s+\*\*(.+?)\*\*", re.MULTILINE)
#: An option label that loads fewer records than the load input.
LOADS_LESS = re.compile(r"(?i)\bsubset\b|\bfirst\b[^.]*\brecords\b")
#: A start-smaller suggestion that names its N.
FIRST_N_SUGGESTION = re.compile(r"start with the first ([\d,]+) records")


def step_7_raw():
    text = PHASE_B.read_text(encoding="utf-8")
    start = text.index("## 7. ")
    return text[start:text.index("\n## 8. ", start)]


def subset_definition():
    """The squashed definition: from its anchor to the next paragraph Step 7 opens in bold."""
    text = step_7_raw()
    start = text.index(SUBSET_ANCHOR)
    return squash(text[start:text.index("**Data source registry.**", start)])


def license_cap_options():
    """[(number, label)] of Step 7's pinned license-cap question, read from the text."""
    text = step_7_raw()
    start = text.index("**Positive and below the dataset size**")
    branch = text[start:text.index("- **Absent or null**", start)]
    return OPTION.findall(branch), squash(branch)


def follow_up(branch, number):
    """The squashed `On **n**,` instruction for option `number`, up to the next `On **`."""
    match = re.search(r"On \*\*%s\*\*,(.*?)(?=On \*\*\d+\*\*,|$)" % number, branch)
    if match is None:
        raise AssertionError("option %s has no `On **%s**,` follow-up" % (number, number))
    return match.group(1)


def paragraphs_of_step_7():
    return [squash(block) for block in re.split(r"\n\s*\n", step_7_raw()) if block.strip()]


class TheSubsetRecordIsDefinedOnce(unittest.TestCase):
    """#237: one definition, in Step 7, that every subset-choosing site points at (INV-300)."""

    def setUp(self):
        self.text = subset_definition()

    def test_the_anchor_is_unique(self):
        self.assertEqual(1, PHASE_B.read_text(encoding="utf-8").count(SUBSET_ANCHOR))

    def test_it_declares_itself_the_one_definition(self):
        self.assertIn("This is the one definition of what a subset choice in this step records",
                      self.text)
        self.assertIn("(INV-300)", self.text)

    def test_it_defines_every_load_subset_field(self):
        self.assertIn(SUBSET_SCHEMA, self.text)
        for field in ("`strategy`: `first_n` or `overlap_preserving`",
                      "`limit` (for `first_n`)",
                      "`file_path` and `record_count` (for `overlap_preserving`)",
                      "`reason`: `license_cap` or `sqlite_volume`",
                      "`config/data_sources.yaml`"):
            with self.subTest(field=field):
                self.assertIn(field, self.text)

    def test_the_subset_file_count_is_measured_from_the_written_file(self):
        self.assertIn("the record count **measured from the written file**", self.text)

    def test_a_source_selected_to_nothing_still_gets_a_block(self):
        self.assertIn("measured `record_count: 0`", self.text)

    def test_subset_files_stay_out_of_the_loadable_total(self):
        self.assertIn("**Subset files live under `data/subsets/`, never in "
                      "`data/senzing-ready/`.**", self.text)

    def test_it_defines_the_license_cap_marker(self):
        self.assertIn("**`license_cap_prompt`**", self.text)
        self.assertIn("`config/bootcamp_preferences.yaml`", self.text)
        self.assertIn(LICENSE_MARKER_SCHEMA, self.text)
        self.assertIn("`overlap_preserving` (option 1) or `first_n` (option 3)", self.text)
        self.assertIn("(INV-006)", self.text)

    def test_it_defines_the_sqlite_subset_choice(self):
        self.assertIn('`{decided: true, choice: "subset", loadable}`', self.text)

    def test_neither_marker_is_the_subset_citation(self):
        self.assertIn("**Neither marker records N or a subset file.**", self.text)
        self.assertIn("the only subset record the reconciliation cites", self.text)

    def test_it_defines_the_remaining_cap_from_an_sdk_count(self):
        self.assertIn("**The remaining cap** is `license_record_limit` minus the number of "
                      "records already in the repository", self.text)
        self.assertIn("⛔ **That count is measured through the SDK at this step, never summed "
                      "from the registry.**", self.text)
        self.assertIn("Module 5 Step 24a", self.text)
        self.assertIn("Records a test load left in the repository count against the cap",
                      self.text)

    def test_an_unmeasurable_count_leaves_the_cap_indeterminate(self):
        self.assertIn("the remaining cap is indeterminate. Offer no subset size", self.text)
        self.assertIn("never substitute a remembered or estimated one", self.text)
        self.assertIn("(INV-244)", self.text)

    def test_a_non_positive_cap_loads_nothing(self):
        self.assertIn("**Zero or less:**", self.text)
        self.assertIn("Load nothing and say so", self.text)

    def test_each_schema_is_written_once_in_module_6(self):
        """Defined once: no Module 6 file restates the field list or the marker shape."""
        for schema in (SUBSET_SCHEMA, LICENSE_MARKER_SCHEMA):
            count = sum(path.read_text(encoding="utf-8").count(schema)
                        for path in MODULE6.glob("*.md"))
            with self.subTest(schema=schema):
                self.assertEqual(1, count)


class TheDatasetSizeIsTheWholeLoad(unittest.TestCase):

    def test_the_license_branches_compare_against_the_loadable_total(self):
        text = squash(step_7_raw())
        self.assertIn('**"The dataset size" in these branches is the whole load, not this '
                      'source.**', text)
        self.assertIn("the loadable total across **every** mapped source", text)
        self.assertIn("It is not the first source alone", text)


class EverySubsetChoicePointsAtTheDefinition(unittest.TestCase):
    """Derived from the text (INV-246): adding a subset option without its record fails here."""

    def test_the_license_option_sweep_is_not_vacuous(self):
        options, _ = license_cap_options()
        chosen = [number for number, label in options if LOADS_LESS.search(label)]
        self.assertEqual(3, len(options), options)
        self.assertGreaterEqual(len(chosen), 2, options)
        self.assertNotIn("2", chosen, "the apply-a-license option loads everything")

    def test_each_license_subset_option_writes_its_record(self):
        options, branch = license_cap_options()
        for number, label in options:
            if not LOADS_LESS.search(label):
                continue
            strategy = ("overlap_preserving" if "overlap-preserving" in label.lower()
                        else "first_n")
            body = follow_up(branch, number)
            with self.subTest(option=number, label=label):
                self.assertIn("`load_subset:`", body)
                self.assertIn("`license_cap_prompt`", body)
                self.assertIn(POINTER, body)
                self.assertIn("`choice: %s`" % strategy, body)
                self.assertIn("strategy: %s" % strategy, body)
                self.assertIn("reason: license_cap", body)

    def test_option_1_selects_across_every_mapped_source_into_data_subsets(self):
        _, branch = license_cap_options()
        body = follow_up(branch, 1)
        self.assertIn("**once, across every mapped source** in `data/senzing-ready/`, within "
                      "the remaining cap", body)
        self.assertIn("`data/subsets/`", body)
        self.assertIn("the measured `record_count`", body)
        self.assertIn("module-04-data-collection/SKILL.md#overlap-preserving-sampling", body)
        self.assertIn("With a **single source**", body)

    def test_option_3_loads_exactly_the_remaining_cap_on_purpose(self):
        _, branch = license_cap_options()
        body = follow_up(branch, 3)
        self.assertIn("`load_subset: {strategy: first_n, limit: N, reason: license_cap}`", body)
        self.assertIn("N = the remaining cap", body)
        self.assertIn("**before** the load", body)
        self.assertIn("stopping there on purpose, not at the license error", body)
        self.assertIn("later sources get only what is left of the cap, possibly nothing", body)

    def test_both_options_start_from_the_remaining_cap(self):
        _, branch = license_cap_options()
        self.assertIn("Options **1** and **3** load a subset. For either, measure the "
                      "**remaining cap** first", branch)

    def test_every_first_n_suggestion_writes_its_record(self):
        found = []
        for para in paragraphs_of_step_7():
            for match in FIRST_N_SUGGESTION.finditer(para):
                limit = match.group(1).replace(",", "")
                found.append(limit)
                with self.subTest(limit=limit):
                    self.assertIn(POINTER, para)
                    self.assertIn("`sqlite_volume_prompt` with `choice: \"subset\"`", para)
                    self.assertIn("`load_subset: {strategy: first_n, limit: %s, reason: "
                                  "sqlite_volume}`" % limit, para)
        self.assertTrue(found, "the scan finds no first-N suggestion; widen FIRST_N_SUGGESTION")


class StepSevenCitesTheSubsetRecord(unittest.TestCase):

    def setUp(self):
        self.text = step_7()

    def test_neither_subset_site_cites_the_sqlite_marker(self):
        """⛔ Negative control: restoring "cited from the `sqlite_volume_prompt` marker" fails."""
        for name, part in (("stage 1", stage_one(self.text)),
                           ("stage-2 subset bullet", subset_bullet(self.text))):
            with self.subTest(site=name):
                self.assertIn("`load_subset:`", part)
                self.assertIn("#load-subset-record", part)
                self.assertNotIn("sqlite_volume_prompt", part)

    def test_the_subset_is_the_last_chain_step(self):
        self.assertIn("collected → sample → mapped → subset", self.text)
        self.assertIn("(mapped → subset)", subset_bullet(self.text))

    def test_an_explained_delta_names_the_block(self):
        self.assertIn("the `sample:` block, the `load_subset:` block, or the mapping artifact",
                      self.text)

    def test_no_block_means_unexplained(self):
        self.assertIn("**No `load_subset:` block**", self.text)
        self.assertIn("a gap only a subset could explain is **unexplained**", self.text)


class TheSqliteHeadsUpHonorsASubset(unittest.TestCase):

    def test_it_honors_subset_and_reads_n_from_the_block(self):
        text = squash(step_7_raw())
        note = chain_part(text, "Check first whether this was already decided",
                          "Only when the database is SQLite")
        self.assertIn("`proceed`, `subset`, `sample`, or a database switch", note)
        self.assertIn("For `subset`, take N from the source's `load_subset:` block", note)


if __name__ == "__main__":
    unittest.main()
