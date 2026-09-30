"""Every Module 6 SQLite start-smaller note reads the recorded decision; Phase C carries none.

Data processing asks the SQLite volume question once and records it: Phase A's pre-load check
writes `sqlite_volume_prompt`, and Phase B Step 7's start-smaller note is guarded — it reads that
marker and the Module 4 Step 8b load decision, and says nothing if either records a choice.

Phase C Step 19 carried an **unguarded** copy: *"SQLite note: if total records exceed 1,000,
recommend loading a subset first…"*. It read no marker, so a guide following it recommended a
subset to a Bootcamper who had already chosen to proceed on SQLite with the full dataset — a third
ask on a settled question (INV-006), pushing a smaller dataset than the one chosen (INV-150).
Observed during a /dry-run phase-3 walk, 2026-09-25: `sqlite_volume_prompt` recorded `proceed`,
and Step 19's note would have recommended a subset of the 2,610 remaining records.

Its threshold was also unsourced. The server's own SQLite guidance is `search_docs(query='loading',
category='anti_patterns')` -> "Do Not Use SQLite in Production", *"under 100K records"*, the figure
Phase A sources at runtime (re-checked live on server 1.37.13, 2026-09-26); Step 19 hardcoded
1,000. Step 19's first line, *"Run on the complete dataset"*, also overrode a recorded choice to
load a subset.

The fix removes the note rather than guarding it: once Phase A prompts on the loadable total of
every mapped source, by Step 19 either a decision is recorded or the whole load is below the
threshold, so a guarded copy could never fire. Three assertions pin the result:

1. every paragraph in `module-06-data-processing/*.md` that mentions SQLite **and** recommends
   loading a subset or starting smaller names `sqlite_volume_prompt`;
2. `phaseC-multi-source.md` carries no numeric record threshold beside "SQLite";
3. Step 19 no longer says "Run on the complete dataset" unconditionally — it loads the dataset
   the recorded decision names, and says which.

#259 re-pointed Step 19's SQLite paragraph. As #164 left it, it said to *"load what
`sqlite_volume_prompt` or the Module 4 Step 8b load decision records"*. Since #237 and #238 each
source loads from its own `load_subset:` block, Phase B Step 7's one subset record (INV-325), and
an asked-once marker records only that the question was answered, never N. #221 made Step 8b's
decision a sample, cited through the `sample:` block (INV-326), not a subset limit. The paragraph
now names the block and points at Phase B's `#load-subset-record` definition, and a negative
control fails if it again names the marker or a Step 8b load decision as what is loaded.

Everything is asserted as behavior in shipped guidance, so any implementation language satisfies
it (INV-002). Phase B Step 7's note itself is pinned by
`test_sqlite_preload_check_reads_the_loadable_total.py`.

Source: GitHub issues #164 and #259.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE6 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
           "module-06-data-processing")
PHASE_C = MODULE6 / "phaseC-multi-source.md"

MARKER = "`sqlite_volume_prompt`"

SQLITE = re.compile(r"sqlite", re.IGNORECASE)

# A recommendation to load less than the whole dataset. Anchored on loading, so a paragraph
# that merely uses the word "subset" (Phase D: "the usable subset is its `Validation:`
# patterns") is not read as advice about load size.
START_SMALLER = re.compile(
    r"\bload(?:ing)?\s+(?:a\s+|the\s+)?(?:smaller\s+)?subset\b"
    r"|\bsubset\s+first\b"
    r"|\bstart(?:ing)?\s+(?:with\s+)?(?:a\s+)?smaller\b"
    r"|\bstart\s+with\s+the\s+first\b"
    r"|\bsample\s+down\b",
    re.IGNORECASE,
)

# A record-count threshold: a count of records, a comparison against a number, or a figure of
# a thousand or more. `INV-300` and "step 7" are neither.
THRESHOLD = re.compile(
    r"\b\d[\d,.]*\s*[KkMm]?\s+records\b"
    r"|\b(?:exceeds?|exceeding|above|over|more\s+than|under|below|greater\s+than|at\s+least)"
    r"\s+[\d,.]+\s*[KkMm]?\b"
    r"|\b\d{1,3}(?:,\d{3})+\b"
    r"|(?<![-\d])\b\d{4,}\b"
    r"|\b\d+(?:\.\d+)?\s*[KkMm]\b",
    re.IGNORECASE,
)


def flat(text):
    return " ".join(text.split())


def paragraphs(path):
    """Blank-line-separated blocks, whitespace-collapsed."""
    return [flat(block) for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8"))
            if block.strip()]


def step(text, number):
    start = text.index("## %d. " % number)
    return text[start:text.index("## %d. " % (number + 1), start)]


def sqlite_paragraph(section):
    """The one Step 19 paragraph about the SQLite volume question (whitespace-collapsed)."""
    hits = [flat(block) for block in re.split(r"\n\s*\n", section)
            if "SQLite volume question" in block]
    if len(hits) != 1:
        raise AssertionError("expected one SQLite volume paragraph in Step 19, found %d"
                             % len(hits))
    return hits[0]


# The stale load source #259 removed: an asked-once marker, or a Step 8b "load decision", named
# as what a Step 19 load loads.
STALE_LOAD_SOURCE = re.compile(
    r"\bload\s+what\s+`sqlite_volume_prompt`"
    r"|Step\s+8b\s+load\s+decision",
    re.IGNORECASE,
)


class EverySqliteSubsetNoteReadsTheRecordedDecision(unittest.TestCase):
    """Assertion 1: a SQLite start-smaller paragraph names `sqlite_volume_prompt`."""

    def setUp(self):
        self.files = sorted(MODULE6.glob("*.md"))
        self.assertTrue(self.files, "no Module 6 guidance found at %s" % MODULE6)
        self.notes = [(path.name, para)
                      for path in self.files for para in paragraphs(path)
                      if SQLITE.search(para) and START_SMALLER.search(para)]

    def test_the_scan_finds_phase_bs_guarded_note(self):
        """Keeps the scan live: Phase B Step 7's note is a SQLite start-smaller paragraph."""
        self.assertIn(
            "phaseB-load-first-source.md", [name for name, _ in self.notes],
            "the scan no longer finds Phase B Step 7's start-smaller note, so it can no longer "
            "see an unguarded copy either — widen START_SMALLER rather than accept a vacuous pass",
        )

    def test_every_note_names_the_marker(self):
        unguarded = ["%s: %s" % (name, para[:160]) for name, para in self.notes
                     if MARKER not in para]
        self.assertEqual(
            [], unguarded,
            "a SQLite note that recommends loading a subset must read the recorded decision "
            "(%s) first; an unguarded copy re-asks a settled question (INV-006)" % MARKER,
        )


class PhaseCCarriesNoSqliteThreshold(unittest.TestCase):
    """Assertion 2: no numeric record threshold beside "SQLite" in Phase C."""

    def test_no_sqlite_paragraph_carries_a_number(self):
        hits = []
        for para in paragraphs(PHASE_C):
            if not SQLITE.search(para):
                continue
            for match in THRESHOLD.finditer(para):
                hits.append("%r in: %s" % (match.group(0), para[:160]))
        self.assertEqual(
            [], hits,
            "Phase C must carry no SQLite record threshold; the threshold is MCP-sourced at "
            "runtime by Phase A's pre-load check, never hardcoded (INV-080)",
        )


class StepNineteenLoadsTheRecordedDataset(unittest.TestCase):
    """Assertion 3: Step 19 loads what the recorded decision names, and says which."""

    def setUp(self):
        self.step = step(flat(PHASE_C.read_text(encoding="utf-8")), 19)

    def test_it_no_longer_runs_the_complete_dataset_unconditionally(self):
        self.assertNotIn(
            "Run on the complete dataset.", self.step,
            "an unconditional complete-dataset run overrides a recorded choice to load a subset",
        )

    def test_it_runs_the_dataset_the_recorded_decision_names(self):
        self.assertIn("Run on the dataset the recorded load decision names", self.step)
        self.assertIn("the complete dataset unless a subset was chosen", self.step)

    def test_it_says_which_dataset_is_being_loaded(self):
        self.assertIn("tell the bootcamper which one is being loaded", self.step)
        self.assertIn("When it is a subset, say so and that the full dataset can be loaded "
                      "afterwards", self.step)

    def test_it_points_at_the_recorded_decision_without_restating_it(self):
        self.assertIn("add nothing about it here (INV-006)", self.step)
        self.assertIn("Each source loads what its own `load_subset:` block records", self.step)
        self.assertIn("(phaseB-load-first-source.md#load-subset-record)", self.step)
        self.assertIn("Phase B step 7 (`phaseB-load-first-source.md`)", self.step)
        self.assertIn("(INV-300)", self.step)

    def test_an_absent_block_is_the_full_load_input_with_no_remark(self):
        self.assertIn("No block recorded means none was needed: the source loads its full load "
                      "input, the complete dataset unless Module 4 sampled it, with no SQLite "
                      "remark (INV-244)", self.step)

    def test_a_sampled_source_cites_its_sample_block_not_a_subset(self):
        self.assertIn("that input is its sample file, and its reconciliation cites the "
                      "`sample:` block (INV-326), never a subset", self.step)


class StepNineteenNamesNoStaleLoadSource(unittest.TestCase):
    """#259: Step 19 loads each source's `load_subset:` block, never a marker or Step 8b.

    ⛔ Negative control: restoring #164's sentence, *"load what `sqlite_volume_prompt` or the
    Module 4 Step 8b load decision records"*, fails both tests below.
    """

    def setUp(self):
        self.step = step(PHASE_C.read_text(encoding="utf-8"), 19)
        self.paragraph = sqlite_paragraph(self.step)

    def test_the_sqlite_paragraph_names_no_marker_and_no_step_8b(self):
        """INV-325: an asked-once marker records that a question was answered, never N."""
        self.assertIn("`load_subset:` block", self.paragraph)
        self.assertNotIn(MARKER, self.paragraph)
        self.assertNotIn("Step 8b", self.paragraph)

    def test_step_19_names_no_stale_load_source(self):
        """The marker may be re-read before the run (the cap re-check); it is never loaded."""
        self.assertIsNone(STALE_LOAD_SOURCE.search(flat(self.step)), flat(self.step)[:400])


if __name__ == "__main__":
    unittest.main()
