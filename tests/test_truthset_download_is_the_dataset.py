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

⚠️ **Widened 2026-10-16 (#681) to the step's OUTCOME LIST, which this file did not read.** The
same step classifies the acquisition call before it reaches the primary path, and the taxonomy
carried two outcomes — `available` / `unavailable` — while the server documents a third. Server
**1.39.1, 2026-10-16**, `get_capabilities()`, the `tools[]` entry named `get_sample_data`, last
sentence of its `description`: *"When called via the Anthropic public Connectors Directory,
record retrieval may be filtered at the platform layer with a 'Denied.' response. For full
record access, call this MCP server's own endpoint directly (not through the Connectors
Directory) or use the private deployment."* A guide meeting that reply had two wrong places to
land — read the absent records as `unavailable` and take the fallback the module itself calls
*"genuinely exceptional"*, or read a refusal and reach for INV-292's 403 remedy, which switches
back to a `citation.download_url` the denied reply never delivered.

⛔ **What the new checks establish and what they cannot.** They are statements about the shipped
TEXT: that the outcome exists, that it relays the server's own sentence rather than a paraphrase,
that it names the route the sentence is read from, and that it is stated once with the primary
path pointing at it. ⚠️ **No test here establishes that a live run classifies a real `Denied.`
reply correctly** — this environment does not reach the server through the Connectors Directory
and cannot produce one, which is why the issue cites the manifest rather than a reproduction. Nor
does anything here read the server: the suite is offline (INV-108), so the version, the date and
the quoted sentence are a dated record carried in prose, re-asked at implementation time and
re-askable later, never asserted by a test.

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


def classification():
    """Step 1.1 item 1 — the outcome list and the `Denied.` branch (#681).

    ⚠️ Deliberately a different region from ``step_1_1()``: the outcome is decided at the
    ``dataset='list'`` call, BEFORE the primary path is entered, so asserting it over the
    primary path's text would assert it of the wrong step. ``squash`` drops the blockquote
    markers, so the server sentence the branch relays is read here as ordinary prose.
    """
    text = PHASE1.read_text(encoding="utf-8")
    start = text.index("1. **Call `get_sample_data(dataset='list')`**")
    end = text.index("2. **Available (primary path):**", start)
    return squash(text[start:end])


#: The server's own remedy, in the three pieces the issue's re-verification clause pins it to,
#: as ``get_capabilities()`` returned them on server 1.39.1, 2026-10-16. Quoted rather than
#: paraphrased: INV-080 makes the sentence the server's, and a paraphrase is the plugin
#: reasoning about connector topology on its own account.
SERVER_REMEDY = (
    "Anthropic public Connectors Directory",
    "'Denied.' response",
    "call this MCP server's own endpoint directly (not through the Connectors Directory) "
    "or use the private deployment",
)

#: The note as ONE string, for the single-copy check below. ⚠️ The unit counted is the server's
#: sentence, not a phrase inside it: the Connectors Directory's NAME recurs legitimately,
#: because the branch also names the cause in its own words, and counting that would forbid the
#: branch from explaining itself.
SERVER_NOTE = (
    "When called via the Anthropic public Connectors Directory, record retrieval may be "
    "filtered at the platform layer with a 'Denied.' response. For full record access, call "
    "this MCP server's own endpoint directly (not through the Connectors Directory) or use "
    "the private deployment."
)


def denied_branch_problems(region):
    """Every reason the `Denied.` branch is not the branch #681 asked for, as text.

    ⛔ A list of reasons rather than a bare boolean, so the controls below can say WHICH check
    fired on each mutation instead of only that something did (INV-265).
    """
    problems = []
    if "Classify:" not in region or "`unavailable` = no such entry" not in region:
        return ["the region is not Step 1.1's outcome list"]
    if not re.search(r"`denied` = the reply is the bare string `Denied\.`", region):
        problems.append("`denied` is not a third outcome beside `available` / `unavailable`")
    if not re.search(r"(?i)never folded into either of the other two", region):
        problems.append("nothing keeps the outcome out of the other two")
    if not re.search(
            r"(?i)`get_capabilities\(\)` → the `tools\[\]` entry whose `name` is "
            r"`get_sample_data` → that entry's `description`", region):
        problems.append("the route the server's sentence is read from is not named")
    for piece in SERVER_REMEDY:
        if piece not in region:
            problems.append("the server's sentence is not relayed: %r is missing" % piece)
    if not re.search(r"MCP server 1\.\d+\.\d+, \d{4}-\d{2}-\d{2}", region):
        problems.append("the relayed sentence carries no server version and date (INV-080)")
    if not re.search(r"(?i)Do not retry it, and do not classify it as `unavailable`", region):
        problems.append("the reply is retried, or falls through to the `unavailable` path")
    if not re.search(r"(?i)platform(?:-layer)? filter|platform sitting in front of this server",
                     region):
        problems.append("the cause is not named as a filter in front of the server")
    if not re.search(r"(?i)not the refusal INV-292's 403 branch answers", region):
        problems.append("the branch is not held apart from INV-292's 403 remedy")
    if not re.search(r"(?i)\(INV-125\) The branch fires on the `Denied\.` string by itself",
                     region):
        problems.append("the branch does not fire when `get_capabilities()` is unreachable")
    # No citation: INV-048 governs the recap PDF, and the module carrying on past a denied
    # reply is this branch's own clause (#607's ruling, finished by #685).
    if not re.search(r"(?i)\u26d4 \*\*It never blocks the module", region):
        problems.append("the branch may become a dead end that blocks the module")
    return problems


def pointer_problems(primary):
    """Whether the primary path CITES the remedy instead of carrying a second copy (INV-300)."""
    problems = []
    if not re.search(r"(?i)belongs to the `denied` outcome in 1 above, not this one.{0,12}"
                     r"\(INV-300\)", primary):
        problems.append("the primary path does not route a `Denied.` reply to the outcome")
    if "sub-step 1.1" not in primary:
        problems.append("the pointer does not name the sub-step that owns the remedy")
    for piece in SERVER_REMEDY:
        if piece in primary:
            problems.append("the primary path carries a second copy of %r" % piece)
    return problems


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


class TheDeniedReplyIsItsOwnOutcome(unittest.TestCase):
    """#681 — the third branch of the step-1 taxonomy, as a statement of the shipped text."""

    def setUp(self):
        self.region = classification()

    def test_the_region_is_locatable(self):
        """⛔ Anti-vacuity (INV-265): a region that moved is a failure, never a silent pass."""
        self.assertIn("Classify:", self.region,
                      "the located section is not Step 1.1's outcome list")

    def test_the_branch_is_everything_the_issue_asked_for(self):
        self.assertEqual([], denied_branch_problems(self.region))

    def test_the_outcome_list_still_carries_the_two_it_had(self):
        """The issue adds a branch and removes nothing."""
        for outcome in ("`available` = an entry whose name matches",
                        "`unavailable` = no such entry"):
            with self.subTest(outcome=outcome[:24]):
                self.assertIn(outcome, self.region)


class TheRemedyIsStatedOnce(unittest.TestCase):
    """INV-300 — one site owns the remedy and the other sites point at it."""

    def test_the_branch_declares_itself_the_owner(self):
        self.assertIn("This is the canonical statement of its remedy", classification(),
                      "no site claims the remedy, so nothing says which copy is authoritative")

    def test_the_primary_path_points_rather_than_restates(self):
        self.assertEqual([], pointer_problems(step_1_1()))

    def test_the_servers_sentence_appears_exactly_once_in_the_file(self):
        """⛔ The check INV-300 asks for and a duplication scan cannot do: a SECOND copy that
        has drifted is no longer an exact repeat, so it is counted here while the two still
        match, which is the only moment the count is reliable."""
        whole = squash(PHASE1.read_text(encoding="utf-8"))
        for piece in (SERVER_NOTE, SERVER_REMEDY[2]):
            with self.subTest(piece=piece[:30]):
                self.assertEqual(1, whole.count(piece),
                                 "%r appears %d times; the remedy is stated once and cited "
                                 "elsewhere (INV-300)" % (piece[:60], whole.count(piece)))


class EachCheckSeesTheTextItWasWrittenFor(unittest.TestCase):
    """⛔ Negative controls (INV-282): each check is shown failing on the text it is about.

    The mutations run on copies of the shipped region, never on the file, so a control can
    never leave the corpus changed.
    """

    def mutate(self, region, old, new):
        self.assertIn(old, region, "the control's anchor text is gone; update the control")
        return region.replace(old, new, 1)

    def test_the_taxonomy_without_the_third_outcome_is_reported(self):
        """The pre-#681 outcome list, which is where the defect was."""
        region = self.mutate(
            classification(),
            "`denied` = the reply is the bare string `Denied.` instead of a dataset listing, "
            "a preview, or an error from the server — its own outcome, handled below and "
            "never folded into either of the other two.", "")
        self.assertTrue(any("third outcome" in p for p in denied_branch_problems(region)))

    def test_a_paraphrased_remedy_is_reported(self):
        region = self.mutate(
            classification(), SERVER_REMEDY[2],
            "reach the server some other way or ask your administrator")
        self.assertTrue(any("not relayed" in p for p in denied_branch_problems(region)))

    def test_losing_the_route_to_the_sentence_is_reported(self):
        region = self.mutate(
            classification(),
            "`get_capabilities()` → the `tools[]` entry whose `name` is `get_sample_data` → "
            "that entry's `description`", "the server manifest")
        self.assertTrue(any("route" in p for p in denied_branch_problems(region)))

    def test_falling_through_to_unavailable_is_reported(self):
        region = self.mutate(
            classification(), "Do not retry it, and do not classify it as `unavailable`",
            "Retry once, then classify it as `unavailable`")
        self.assertTrue(any("falls through" in p for p in denied_branch_problems(region)))

    def test_merging_the_branch_into_the_403_remedy_is_reported(self):
        region = self.mutate(
            classification(), "not the refusal INV-292's 403 branch answers",
            "the refusal INV-292's 403 branch answers")
        self.assertTrue(any("held apart" in p for p in denied_branch_problems(region)))

    def test_losing_the_unreachable_capabilities_fallback_is_reported(self):
        region = self.mutate(
            classification(), "(INV-125) The branch fires on the `Denied.` string by itself",
            "(INV-125) The branch needs `get_capabilities()` to have answered")
        self.assertTrue(any("unreachable" in p for p in denied_branch_problems(region)))

    def test_letting_the_branch_block_the_module_is_reported(self):
        region = self.mutate(
            classification(), "\u26d4 **It never blocks the module",
            "\u26d4 **Stop the module here")
        self.assertTrue(any("dead end" in p for p in denied_branch_problems(region)))

    def test_a_second_copy_on_the_primary_path_is_reported(self):
        primary = step_1_1() + " " + SERVER_REMEDY[2]
        self.assertTrue(any("second copy" in p for p in pointer_problems(primary)))

    def test_dropping_the_pointer_is_reported(self):
        primary = self.mutate(
            step_1_1(),
            "belongs to the `denied` outcome in 1 above, not this one** (INV-300)",
            "is handled somewhere**")
        self.assertTrue(any("does not route" in p for p in pointer_problems(primary)))


class ReWrapping(unittest.TestCase):
    """INV-346 — every check above reads whitespace-collapsed text, so re-flowing the shipped
    Markdown to one word per line changes no verdict."""

    def test_the_checks_survive_a_reflow(self):
        text = PHASE1.read_text(encoding="utf-8")
        start = text.index("1. **Call `get_sample_data(dataset='list')`**")
        end = text.index("2. **Available (primary path):**", start)
        reflowed = squash("\n".join(text[start:end].split()))
        self.assertEqual([], denied_branch_problems(reflowed))


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
