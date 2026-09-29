"""An option reply to Data processing's volume question saves a tier, not a record count.

Phase A Step 1 asks how many records the production system will load and accepts a bare option
number (1-4). It then persisted `production_volume` (`tier` and `raw_value`), and Steps 3 and 4
passed `raw_value` to `sdk_guide(topic='load', ...)` as `record_count`. After an option reply the
only "raw value" is the option itself, so a Bootcamper who picked **3 - medium production** got
`record_count=3`, and `sdk_guide` returned the single-threaded demo loader for a medium tier.

Measured on the live server (1.37.13, 2026-09-26), `sdk_guide(topic='load', language='java', ...)`:
`record_count=3` and `record_count=500` return `java/snippets/loading/LoadRecords.java` (demo);
`record_count` omitted returns `java/snippets/loading/LoadViaFutures.java` (threaded). The tool's
own `record_count` contract says the same: null or above 500 is threaded, at or below 500 is the
single-threaded demo.

⛔ **The fix is `raw_value: null` plus a null branch at every site that reads it.** An option
reply, and the unparseable-twice `demo` default, persist `raw_value: null`. `small`/`medium`/
`large` then omit `record_count` (threaded), and `demo` passes the demo cutover read from
`sdk_guide`'s contract at call time, never from the file (INV-080).

⚠️ **The site set is SCANNED, not hardcoded (INV-246).** Every `record_count=<raw_value>` call in
the shipped plugin must carry its null branch before the next bullet or heading, so a new call
site added later without one fails here rather than reintroducing the defect.

The SQLite pre-load check is not asserted here. After #163 its trigger is the loadable total and
`raw_value` decides nothing there (`test_sqlite_preload_check_reads_the_loadable_total.py`).

Source: GitHub issue #155.

Enforces **INV-328** (a reply that selects a category persists the category and a null, never
the option's number, and every tool call branches on the null). ⚠️ It pins Phase A's text and
cannot observe a live `sdk_guide` call.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PHASE_A = (PLUGIN / "skills" / "module-06-data-processing" / "phaseA-build-loading.md")

RAW_CALL = "record_count=<raw_value>)"
# Bold, so it matches the branch itself rather than the code-comment clause that follows it.
NULL_BRANCH = "**When `raw_value` is null**"
# The end of the bullet or step a call sits in: the next bullet (at any indent) or heading.
SEGMENT_END = re.compile(r"\n\s*- \*\*|\n#+ ")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


def segment_after(text, index):
    """The text from `index` to the end of the bullet or step that contains it."""
    match = SEGMENT_END.search(text, index)
    return text[index:match.start() if match else len(text)]


class PhaseA(unittest.TestCase):

    def setUp(self):
        self.raw = PHASE_A.read_text(encoding="utf-8")
        self.text = flat(self.raw)
        self.step1 = between(self.text, "**Classify and persist the tier.**",
                             "**License framing (default + expansion paths).**")
        self.step3 = between(self.text, "## 3. Create the production loading program",
                             "## 4. Use MCP tools for code generation")
        self.step4 = between(self.text, "## 4. Use MCP tools for code generation",
                             "## 4a. Register the data source codes")
        self.production = between(self.step3, "- **`small`, `medium`, or `large`:**",
                                  "- **`demo`:**")
        self.demo = between(self.step3, "- **`demo`:**", "- **Missing or unreadable:**")


class StepOneSavesNoCountForAnOption(PhaseA):
    """Assertions 1 and 2: Step 1 persists null for an option and says so in the echo."""

    def test_an_option_reply_persists_a_null_raw_value(self):
        self.assertRegex(
            self.step1,
            r"bare option number \(1–4\), select that tier directly and persist `raw_value: null`",
            "an option picks a range, so it saves the tier and a null raw_value",
        )

    def test_the_option_number_is_never_stored_as_raw_value(self):
        self.assertIn("the option number is never stored in `raw_value`", self.step1)

    def test_a_free_text_reply_still_stores_the_parsed_number(self):
        self.assertIn("store the parsed number as `raw_value`", self.step1)

    def test_the_unparseable_default_persists_a_null_raw_value(self):
        self.assertRegex(
            self.step1,
            r"default to `demo`, persist `raw_value: null`",
            "the unparseable-twice default has no count either",
        )

    def test_null_is_a_recorded_answer_not_a_missing_value(self):
        """A reader that took null as "missing" would fall into an indeterminate branch."""
        self.assertIn("is a recorded answer", self.step1)
        self.assertIn("not a missing or unreadable value", self.step1)

    def test_the_echo_says_no_count_was_given(self):
        echo = between(self.text, "⛔ **Echo the consequence back before generating any code.**",
                       "**License framing (default + expansion paths).**")
        self.assertRegex(
            echo,
            r"When `raw_value` is null, also say that no count was given",
            "the Bootcamper must hear that the build follows the range they picked",
        )
        self.assertIn("you picked a range rather than a count", echo)


class StepsThreeAndFourBranchOnNull(PhaseA):
    """Assertion 3: each tier has a null branch in Step 3 and in Step 4."""

    def test_step_3_production_tiers_omit_record_count_when_null(self):
        self.assertIn(NULL_BRANCH, self.production)
        self.assertRegex(
            self.production,
            r"When `raw_value` is null\*\* \(the tier came from an option, so no count was "
            r"given\), call `sdk_guide\(topic='load', language='<chosen_language>'\)` "
            r"\*\*without\*\* `record_count`",
            "omitting record_count is what returns the threaded pattern",
        )
        self.assertIn("the comment also says the tier came from a range and no count was given",
                      self.production)

    def test_step_3_demo_passes_the_cutover_read_from_the_contract(self):
        self.assertIn(NULL_BRANCH, self.demo)
        self.assertRegex(
            self.demo,
            r"pass the \*\*demo cutover\*\* as `record_count`: the top of the single-threaded "
            r"range, as `sdk_guide`'s own `record_count` contract states it \*\*at call time\*\*",
        )
        self.assertIn("never from this file (INV-080)", self.demo)
        self.assertIn("the count is the tier's upper bound, not the Bootcamper's figure",
                      self.demo)

    def test_step_3_demo_falls_back_when_the_contract_cannot_be_read(self):
        self.assertRegex(
            self.demo,
            r"If the contract can't be read .{0,60}take the \"Missing or unreadable\" branch",
        )
        self.assertIn("the demo loader couldn't be selected", self.demo)

    def test_step_3_demo_null_branch_carries_no_literal_cutover(self):
        """INV-080: the figure comes from the server at call time, not from this bullet."""
        self.assertIn(NULL_BRANCH, self.demo)
        null_branch = self.demo[self.demo.index(NULL_BRANCH):]
        self.assertNotRegex(null_branch, r"\b500\b",
                            "the demo cutover is read from the contract, never written here")

    def test_step_4_gives_both_null_branches(self):
        self.assertIn(NULL_BRANCH, self.step4)
        self.assertRegex(
            self.step4,
            r"for `small`, `medium` or `large`, omit `record_count`; for `demo`, pass the demo "
            r"cutover read from `sdk_guide`'s `record_count` contract at call time",
        )


class NoCountIsInvented(PhaseA):
    """Assertion 4: no instruction passes an option number, or a null, as `record_count`."""

    def test_production_tiers_and_step_4_forbid_it(self):
        rule = "Never pass the null, or an option number, as `record_count`"
        self.assertIn(rule, self.production)
        self.assertIn(rule, self.step4)

    def test_no_shipped_call_passes_an_option_or_a_null(self):
        pattern = re.compile(r"record_count\s*=\s*(?:null|None|nil|<option)", re.IGNORECASE)
        hits = [str(p.relative_to(REPO_ROOT)) for p in sorted(PLUGIN.rglob("*.md"))
                if pattern.search(p.read_text(encoding="utf-8"))]
        self.assertEqual(hits, [], "no call passes a null or an option number as record_count")

    def test_every_raw_value_call_carries_its_null_branch(self):
        """INV-246: scan every call site, so a new one without the branch fails here."""
        sites = []
        for path in sorted(PLUGIN.rglob("*.md")):
            raw = path.read_text(encoding="utf-8")
            for match in re.finditer(re.escape(RAW_CALL), raw):
                sites.append((path, raw, match.start()))
        self.assertGreaterEqual(
            len(sites), 3,
            "liveness: Step 3's two tier bullets and Step 4 each pass raw_value to sdk_guide",
        )
        for path, raw, index in sites:
            with self.subTest(path=str(path.relative_to(REPO_ROOT)), offset=index):
                self.assertIn(
                    NULL_BRANCH, flat(segment_after(raw, index)),
                    "a call passing raw_value as record_count needs a null branch in the same "
                    "bullet or step, or an option reply sends the option number as the count",
                )


if __name__ == "__main__":
    unittest.main()
