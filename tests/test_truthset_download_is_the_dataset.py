"""Step 1.1 must download the Truth Set, not save the preview `get_sample_data` returns.

The step said "save the MCP records to `src/system_verification/truthset_data.jsonl`".
`get_sample_data` does not return the records — it returns a **preview plus URLs**. Following the
step as written saved **15 of 159** records and built the module's mandatory artifact (INV-077),
the bootcamp's showpiece, on nine percent of the data. Nothing caught it: the step already
retrieved the true per-source counts one line above and never compared anything against them. A
sparse graph is not an error state — it renders, it looks plausible.

Re-verified on **MCP server 1.32.9, 2026-08-14**: `dataset='truthset', source='list'` returns
`records: []` with `total_available: 159` and three sources (CUSTOMERS 120, REFERENCE 22,
WATCHLIST 17); a per-source call returns a preview whose `citation.note` names both URLs and says
`download_url` needs only `mcp.senzing.com` while `source_download_url` needs
`raw.githubusercontent.com`.

Three things the fix has to carry, and each is a distinct failure:

* **The download**, from a URL in the response.
* **The count check**, because a rate-limited fetch writes `Rate limit exceeded. Try again in 1
  second.` — 43 bytes, HTTP 429 — *into* the JSONL when fetched with `curl -sS -o file`, leaving
  one line of English prose in the middle of the dataset. The count check is the only thing that
  turns preview-only, rate-limited and truncated fetches alike into a visible error.
* **The egress host, per dataset.** Module 4's "needs egress to `senzing.com`" is true for CORD and
  false for the Truth Set, whose `source_download_url` is on `raw.githubusercontent.com`.

⚠️ And one trap the spec did not record, found while re-verifying: the **same field name means
different hosts** in the two responses. `source='list'` returns
`available_sources[].download_url` on the origin host; a per-source call returns
`citation.download_url` on `mcp.senzing.com`.

Enforces **INV-228** — a step writing a server-obtained dataset verifies the written count against the reported count and stops on a mismatch.

Source spec: `specs/truthset-step-saves-a-five-record-preview-not-the-truth-set.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
PHASE1 = SKILLS / "module-03b-truthset-visualization" / "phase1-visualization.md"
MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"


def squash(text):
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M))


def step_1_1():
    text = PHASE1.read_text(encoding="utf-8")
    start = text.index("2. **Available (primary path):**")
    end = text.index("### 1.2", start)
    return squash(text[start:end])


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_files_exist(self):
        for path in (PHASE1, MODULE_04):
            with self.subTest(file=path.name):
                self.assertTrue(path.is_file(), "%s moved" % path)

    def test_the_step_is_locatable(self):
        self.assertIn("truthset_data.jsonl", step_1_1(),
                      "the located section is not Step 1.1's primary path")


class ThePreviewIsNamedAsAPreview(unittest.TestCase):
    def setUp(self):
        self.step = step_1_1()

    def test_it_says_get_sample_data_returns_a_preview(self):
        # The call is named WITH its required parameter, per INV-136 — a bare
        # `get_sample_data` fails, and tests/test_truthset_acquisition_call.py enforces
        # that any mention sits beside `dataset=`.
        self.assertRegex(
            self.step,
            r"(?i)`get_sample_data\(dataset='truthset', source='<CODE>'\)` returns\s*"
            r"a PREVIEW plus URLs — not the\s*dataset",
            "the step still treats get_sample_data as returning the dataset, or names it "
            "without its required parameter")

    def test_it_names_the_silent_failure(self):
        self.assertRegex(
            self.step, r"(?i)the graph renders, looks plausible",
            "the step does not say why the failure goes unnoticed, which is the reason "
            "the count check below is mandatory rather than advisory")

    def test_it_does_not_hardcode_the_preview_size(self):
        """The response states it; a number here goes stale silently."""
        self.assertRegex(
            self.step, r"(?i)`citation\.note` says how many of how\s*many",
            "the step should read the preview size from the response")

    def test_the_provenance_and_target_file_survive(self):
        self.assertIn("provenance `mcp_primary`", self.step,
                      "the provenance recorded for this path was lost")
        self.assertIn("src/system_verification/truthset_data.jsonl", self.step,
                      "the target file was lost")


class TheRecordsAreDownloaded(unittest.TestCase):
    def setUp(self):
        self.step = step_1_1()

    def test_the_url_comes_from_the_response(self):
        self.assertRegex(
            self.step,
            r"(?i)Fetch each source from a URL in the response, never a hardcoded one",
            "the download URL is not required to come from the response (INV-080)")
        self.assertIn("citation.download_url", self.step)
        self.assertIn("citation.source_download_url", self.step)

    def test_the_same_name_different_host_trap_is_recorded(self):
        self.assertRegex(
            self.step,
            r"(?i)The two responses use the name `download_url` for different hosts",
            "the list-vs-per-source host difference is unrecorded, so reading the field "
            "name instead of the URL sends a firewalled bootcamper to the wrong host")

    def test_the_egress_host_is_per_dataset_and_not_senzing_com(self):
        self.assertRegex(
            self.step, r"(?i)Name the egress host from the URL you chose, per dataset",
            "the egress host is not tied to the URL in hand")
        self.assertIn("raw.githubusercontent.com", self.step,
                      "the Truth Set's actual egress host is not named")
        self.assertRegex(
            self.step, r"(?i)\*not\*? `senzing\.com`|not\*?\*? `senzing\.com`",
            "nothing contradicts Module 4's CORD-specific sentence, which is what a "
            "reader would otherwise carry over")


class TheRateLimitCannotBecomeData(unittest.TestCase):
    def setUp(self):
        self.step = step_1_1()

    def test_it_retries_with_backoff_on_429(self):
        self.assertRegex(
            self.step, r"(?i)Retry with backoff on HTTP 429",
            "a rate-limited fetch is not retried")

    def test_it_names_the_curl_trap_specifically(self):
        self.assertRegex(
            self.step, r"(?i)`curl -sS -o file` writes that sentence",
            "the specific way the rate-limit body becomes data is not named, so the "
            "obvious fetch command still corrupts the file")
        self.assertRegex(
            self.step, r"(?i)`-sS` only silences the\s*progress meter",
            "the reason -sS does not help is unstated")

    def test_it_gives_a_working_alternative(self):
        self.assertRegex(
            self.step, r"(?i)--fail-with-body|use `-f`",
            "no safe fetch form is offered, only a prohibition")


class TheCountCheckIsMandatory(unittest.TestCase):
    def setUp(self):
        self.step = step_1_1()

    def test_it_compares_against_the_per_source_counts(self):
        self.assertRegex(
            self.step,
            r"(?i)Compare the written line count against the per-source `record_count` "
            r"values",
            "nothing compares the written file against the counts already retrieved")

    def test_it_stops_on_a_mismatch(self):
        self.assertRegex(self.step, r"(?i)STOP on a mismatch",
                         "a mismatch does not halt the module")
        self.assertRegex(
            self.step, r"(?i)Do not\s*proceed to 1\.2 on a mismatch",
            "the step does not say which step must not run")

    def test_it_states_the_expected_count_per_route(self):
        self.assertRegex(
            self.step,
            r"(?i)Expect exactly `record_count` from\s*`source_download_url`",
            "the uncapped route's expectation is unstated")
        self.assertRegex(
            self.step,
            r"(?i)`min\(record_count, download_url_max_records\)` from `download_url`",
            "the capped route's expectation is unstated, so a capped slice reads "
            "as a mismatch")

    def test_it_says_what_the_check_is_for(self):
        self.assertRegex(
            self.step, r"(?i)preview-only, rate-limited, truncated",
            "the check is stated without its scope, so a later editor may treat it as "
            "belt-and-braces and drop it")


class ModuleFourNoLongerStatesOneEgressHost(unittest.TestCase):
    def setUp(self):
        self.flat = squash(MODULE_04.read_text(encoding="utf-8"))

    def test_the_general_rule_is_gone(self):
        self.assertNotRegex(
            self.flat,
            r"\*\*`source_download_url`\*\* is the complete uncapped file, and needs egress "
            r"to `senzing\.com`\.",
            "Module 4 still states a single egress host as a general rule")

    def test_the_host_comes_from_the_url(self):
        self.assertRegex(
            self.flat,
            r"(?i)needs egress to \*\*whatever host that\s*URL actually names — read it from "
            r"the response\.?\*\*",
            "the corrected rule is missing")

    def test_it_names_both_the_cord_case_and_the_truth_set_case(self):
        self.assertRegex(self.flat, r"(?i)For the CORD collections that is `senzing\.com`",
                         "the CORD case — which was correct — was lost")
        self.assertRegex(
            self.flat,
            r"(?i)the Truth Set's `source_download_url` is on\s*\*\*`raw\.githubusercontent\.com`",
            "the counterexample that makes the rule necessary is not given")

    def test_the_capped_download_rule_survives(self):
        self.assertRegex(
            self.flat, r"(?i)serves at most `download_url_max_records` records per request",
            "the capped-download rule was lost")


if __name__ == "__main__":
    unittest.main()
