"""Step 1.1 must download the Truth Set, not save the preview `get_sample_data` returns.

Enforces **INV-378**, registered by the maintainer 2026-10-20: a platform-injected reply a
tool's own manifest documents is an outcome of its own in a taxonomy, and the branch for it
neither retries nor falls through to `unavailable`, and does not block the module. ⚠️ This
file asserts that the shipped branch **states** each clause; it **cannot** establish that a
live run classifies a real `Denied.` reply correctly -- only a Bootcamper reaching the server
through the Connectors Directory observes that -- and it asserts nothing about the server,
the suite being offline (INV-108).

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

⚠️ **Widened 2026-10-23 (#805) from Module 3b to every step that classifies the reply.** The
guard read Step 1.1 alone, while Module 1 Step 4b sorted the same tool's replies into fit / none
fit / timeout and Module 4 called it with no outcome at all. It now finds its sites by scanning
every `get_sample_data` mention in shipped Markdown (INV-246). The unit is the step: a mention
whose section names no `denied` outcome, and links none, is reported, and every mention that
classifies nothing is on ``EXEMPT``, keyed by file, section heading and a quote from its own
paragraph, each with a reason. A file that states the outcome once at an anchor (Module 4) is
held tighter: each of its classifying mentions links that anchor, so a second call added to
the same long step is caught too. Module 1 and Module 4 point at Module 3b's remedy and never
carry a copy of the server's sentence (INV-300). The same limit holds: these are statements
about the text, not about a live run.

Source spec: `specs/truthset-step-saves-a-five-record-preview-not-the-truth-set.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from collections import namedtuple
from pathlib import Path

from _corpus import corpus_files

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
    if not re.search(r"(?i)\u26d4 \*\*(?:\(INV-\d+\) )?It never blocks the module", region):
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
            classification(), "\u26d4 **(INV-378) It never blocks the module",
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


# ---------------------------------------------------------------------------------------------
# #805 — every step that classifies a `get_sample_data` reply carries the `denied` outcome.
# ---------------------------------------------------------------------------------------------

#: Shipped Markdown, repo-relative with ``/`` separators so the keys below read the same on
#: Linux, macOS and Windows.
def shipped_corpus():
    return {path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8")
            for path in corpus_files("plugins", suffixes={".md"})}


M01_DISCOVERY = "plugins/senzing-bootcamp/skills/module-01-business-problem/phase1-discovery.md"
M03B_PHASE1 = "plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/phase1-visualization.md"
M03B_SKILL = "plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/SKILL.md"
M04_SKILL = "plugins/senzing-bootcamp/skills/module-04-data-collection/SKILL.md"
M05_PHASE1 = "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase1-quality-assessment.md"

STEP_4B = "4b. CORD sourcing for the generated scenario (via MCP — NON-YIELDING)"
M04_STEP_2 = "2. For each data source, collect the data"

#: A block STATES the outcome when it names the bare reply and calls it an outcome of its own.
STATEMENT = re.compile(r"(?i)\bits own outcome\b|\boutcome of its own\b")

#: The pointer to Module 3b's remedy, the one statement INV-378's remedy has (INV-300).
REMEDY_POINTER = re.compile(
    r'→ "A `Denied\.` reply is a platform-layer filter, not an unavailable Truth Set"')

#: Words a step uses when it sorts a reply into outcomes. An exempted mention whose block
#: carries one of them is classifying after all, and may not be exempted.
OUTCOME_WORDS = re.compile(
    r"(?i)`Denied\.`|\bunavailable\b|\bnone fit\b|\bno fit\b|\btime(?:d )?out\b|\bClassify\b")

#: The sections every scan must find classifying (INV-265 floor), as (file, heading).
REQUIRED_SITES = (
    (M01_DISCOVERY, STEP_4B),
    (M03B_PHASE1, "1.1 Acquire the Truth Set (MCP-first, sanctioned fallback)"),
    (M03B_SKILL, "Truth Set source"),
    (M04_SKILL, M04_STEP_2),
)

#: Every mention that does not classify a reply, keyed (file, section heading, a quote from
#: the mention's own paragraph) — text, never a line number, so an edit above it moves
#: nothing — each with the reason it classifies nothing. A mention in a section that carries
#: the outcome needs no entry, except in a file that states it once at an anchor, where every
#: mention either links that anchor or is listed here.
EXEMPT = {
    ("plugins/senzing-bootcamp/skills/bootcamp-onboarding/ground-rules.md",
     "MCP-first invariant (absolute precedence)",
     "sample data -> `get_sample_data`"):
        "a tool-routing list: names which tool answers which question, makes no call",
    ("plugins/senzing-bootcamp/skills/bootcamp-onboarding/ground-rules.md",
     "Naming Senzing datasets (INV-230)",
     "`get_sample_data`'s dataset key `truthset`"):
        "an identifier note: the spelling of a dataset key, not a call",
    ("plugins/senzing-bootcamp/skills/module-01-business-problem/phase2-document-confirm.md",
     "11. Create the problem statement document",
     "retrieve via MCP (`get_sample_data`,"):
        "a rule about where CORD facts come from; Step 4b makes and classifies the call",
    (M03B_PHASE1, "2.2 Always produce the standalone snapshot first (the guarantee)",
     "acquired here via `get_sample_data(dataset='truthset')` (server 1.32.2"):
        "a dated illustration of where the Truth Set came from, for the snapshot's wording",
    (M03B_PHASE1, "2.4a Check the encoding, then capture screenshots (against the running server)",
     "`get_sample_data(dataset='truthset', source='list')`, server 1.33.0"):
        "a dated illustration of the Truth Set's sources, for the encoding verdict",
    ("plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/"
     "visualization-api-reference.md",
     "The encoding self-check (required — behavior, in every language)",
     "(`get_sample_data(dataset='truthset', source='list')` → CUSTOMERS, REFERENCE, WATCHLIST"):
        "a dated illustration of the Truth Set's sources, for the encoding verdict",
    (M04_SKILL, M04_STEP_2, "I can pull CORD datasets using the `get_sample_data` tool"):
        "a recommendation that names the tool without calling it",
    (M04_SKILL, M04_STEP_2, "`get_sample_data`'s own contract requires it of every caller"):
        "quotes the tool's real-data disclosure contract; no reply is read",
    (M04_SKILL, M04_STEP_2, "**What `truncated: true` means.**"):
        "reads a field of a listing that arrived; check 2's call, which draws it, links the "
        "outcome",
    (M04_SKILL, M04_STEP_2, "Illustration only, dated, never a constant"):
        "a dated illustration of a truncated source",
    (M04_SKILL, M04_STEP_2, "the dataset and the source as `get_sample_data` names them"):
        "a registry note: the meaning of `cord_dataset` and `cord_source`",
    (M04_SKILL, M04_STEP_2, "after CORD data has been downloaded via `get_sample_data`"):
        "a provenance note: runs after a download that succeeded",
    (M04_SKILL, M04_STEP_2, "`cord`: source obtained via the `get_sample_data` MCP tool"):
        "a provenance value's definition",
    (M04_SKILL, "Agent behavior", "recommend CORD data first via the `get_sample_data` MCP tool"):
        "a recommendation that names the tool without calling it; it is the order the "
        "outcome continues down",
    (M05_PHASE1, "5a. Senzing-readiness check and fast-path offer (CORD sources only)",
     "a source obtained via the `get_sample_data` MCP tool in Module 4"):
        "a provenance note: which sources the step reads",
    (M05_PHASE1, "5a. Senzing-readiness check and fast-path offer (CORD sources only)",
     "**CORD ships both, so neither may be assumed.** Verified live"):
        "a dated illustration of two CORD record shapes",
    (M05_PHASE1, "5a. Senzing-readiness check and fast-path offer (CORD sources only)",
     "**The worked case, measured live.**"):
        "a dated illustration of one CORD source's arrays",
    (M05_PHASE1, "5a. Senzing-readiness check and fast-path offer (CORD sources only)",
     "This is not hypothetical: `get_sample_data(dataset='las-vegas',"):
        "a dated illustration of one CORD source's arrays",
    (M05_PHASE1, "7b. Return to Data collection — when nothing mechanical is left to fix",
     "one from `get_sample_data` and one from the free-data catalog"):
        "a provenance note: why a fixed dataset offers no return",
    ("plugins/senzing-bootcamp/skills/module-06-data-processing/phaseA-build-loading.md",
     "Pre-load data freshness check (advisory only)",
     "(downloaded via `get_sample_data`)"):
        "a provenance note: runs after a download that succeeded",
}

BlockAt = namedtuple("BlockAt", "file section heading line raw flat")


def blocks_of(relpath, text):
    """Every paragraph-level block of a Markdown file, with the heading of its section.

    A heading starts a section; a blank line (a bare ``>`` counts as blank) ends a block, and
    so does a list item, which starts the next one: a long list is one Markdown paragraph, and
    read whole it would let one item's outcome words speak for another. Lines inside a fenced
    code block are never headings and never end a block.
    """
    out, heading, section, current, start, fenced = [], "", 0, [], 0, False

    def flush():
        if current:
            raw = "\n".join(current)
            out.append(BlockAt(relpath, section, heading, start, raw, squash(raw)))

    for number, line in enumerate(text.split("\n"), 1):
        bare = re.sub(r"^[ \t]*(?:>[ \t]?)*", "", line)
        if bare.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        if not fenced and re.match(r"#{1,6}\s", line):
            flush()
            current, heading, section = [], line.lstrip("#").strip(), section + 1
            continue
        if not fenced and not bare.strip():
            flush()
            current = []
            continue
        if not fenced and re.match(r"\s*(?:[-*+]|\d+\.)\s", bare):
            flush()
            current = []
        if not current:
            start = number
        current.append(line)
    flush()
    return out


def is_statement(block):
    return "`Denied.`" in block.flat and bool(STATEMENT.search(block.flat))


def statement_anchors(blocks):
    """Anchors (``<a id>`` blocks) placed directly above a block that states the outcome."""
    anchors = set()
    for before, after in zip(blocks, blocks[1:]):
        found = re.fullmatch(r'<a id="([a-z0-9-]+)"></a>', before.flat)
        if found and is_statement(after):
            anchors.add(found.group(1))
    return anchors


def links_anchor(block, anchors):
    return any(re.search(r"\]\([^)\s#]*#%s\)" % re.escape(a), block.flat) for a in anchors)


def exemption_for(block, exempt):
    for (file, heading, quote), reason in exempt.items():
        if block.file == file and block.heading == heading and quote in block.flat:
            return (file, heading, quote)
    return None


def scan(corpus, exempt=None):
    """Read every `get_sample_data` mention; return (problems, classifying sections, mentions)."""
    exempt = EXEMPT if exempt is None else exempt
    problems, classifying, mentions, used = [], set(), 0, set()
    all_anchors = set()
    per_file = {}
    for relpath in sorted(corpus):
        blocks = blocks_of(relpath, corpus[relpath])
        per_file[relpath] = blocks
        all_anchors |= statement_anchors(blocks)
    for relpath, blocks in per_file.items():
        own_anchors = statement_anchors(blocks)
        carried = {b.section for b in blocks
                   if is_statement(b) or links_anchor(b, all_anchors)
                   or REMEDY_POINTER.search(b.flat)}
        for block in blocks:
            if "get_sample_data" not in block.raw:
                continue
            mentions += 1
            where = "%s › %s › %r" % (relpath, block.heading, block.flat[:70])
            key = exemption_for(block, exempt)
            if key is not None:
                used.add(key)
                if OUTCOME_WORDS.search(block.flat):
                    problems.append("a classifying mention is exempted: %s" % where)
                continue
            classifying.add((relpath, block.heading))
            if block.section not in carried:
                problems.append("a classifying mention whose step carries no `denied` "
                                "outcome and no pointer to one: %s" % where)
            elif own_anchors and not is_statement(block) and not links_anchor(block, own_anchors):
                problems.append("a mention in a file that states the outcome once does not "
                                "link that statement: %s" % where)
    for key in sorted(set(exempt) - used):
        problems.append("an exemption matches no mention (stale): %s › %s › %r" % key)
    return problems, classifying, mentions


def restatements(corpus):
    """Files that point at Module 3b's remedy and carry a copy of the server's sentence."""
    return sorted((relpath, piece[:30])
                  for relpath in (M01_DISCOVERY, M04_SKILL, M03B_SKILL)
                  for piece in SERVER_REMEDY if piece in squash(corpus[relpath]))


def section_text(text, heading):
    """The raw text of the section under ``heading`` (to the next heading of any level)."""
    blocks = [b for b in blocks_of("", text) if b.heading == heading]
    return "\n\n".join(b.raw for b in blocks)


def step_4b_problems(text):
    """Module 1 Step 4b's `denied` outcome, clause by clause (criterion 1)."""
    section = section_text(text, STEP_4B)
    if "**Timeout/unreachable after one retry:**" not in section:
        return ["the region is not Step 4b's outcome list"]
    found = re.search(r"(?ms)^- \*\*`Denied\.` reply\*\*.*?(?=^- \*\*|^\s*$|\Z)", section)
    if not found:
        return ["Step 4b has no `denied` outcome beside fit / none fit / timeout"]
    bullet = squash(found.group(0))
    problems = []
    for needle, why in (
            ("the bare string `Denied.`", "the reply is not named"),
            ("its own outcome", "the outcome is not its own"),
            ("the listing included", "the listing call is not covered"),
            ("report the reply and the call that drew it", "the reply and its call are not stated"),
            ("Do not retry it", "the reply is retried"),
            ("do not report it as a timeout or as CORD being unavailable",
             "the reply may be reported as a timeout or as CORD unavailable"),
            ("In this same turn", "the outcome is not handled in the same turn"),
            ("never a 👉", "the outcome may ask a question"),
            ("provenance `synthesized`", "the outcome does not continue to `synthesized`"),
            ("say that the denied reply is why", "the reason for `synthesized` is not given"),
            ("`../module-03b-truthset-visualization/phase1-visualization.md` → \"A `Denied.` "
             "reply is a platform-layer filter, not an unavailable Truth Set\"",
             "the remedy is not pointed at"),
            ("(INV-300)", "the pointer cites no single-statement authority")):
        if needle not in bullet:
            problems.append(why)
    if "retry once on a timeout, never on a `Denied.` reply" not in squash(section):
        problems.append("the call's retry clause reaches a `Denied.` reply")
    if "👉" in bullet.replace("never a 👉", ""):
        problems.append("the outcome asks a question")
    if re.search(r"(?m)^[ \t>]*👉", section):
        problems.append("the non-yielding step asks a question")
    return problems


def module_4_problems(text):
    """Module 4's one `denied` statement and the calls that link it (criterion 2)."""
    start = text.find('<a id="cord-denied-reply"></a>')
    if start < 0:
        return ["Module 4 states no `denied` outcome at an anchor"]
    end = text.find("<a id=", start + 1)
    region = squash(text[start:end])
    problems = []
    for needle, why in (
            ("is an outcome of its own", "the outcome is not its own"),
            ("does not mean CORD is unavailable", "the reply may read as CORD unavailable"),
            ("Do not retry it", "the reply is retried"),
            ("report the reply and the call that drew it", "the reply and its call are not stated"),
            ("`../module-03b-truthset-visualization/phase1-visualization.md` → \"A `Denied.` "
             "reply is a platform-layer filter, not an unavailable Truth Set\"",
             "the remedy is not pointed at"),
            ("(INV-247) Ask no new question about it", "the outcome may add a question"),
            ("continue down the data recommendation hierarchy** in [Agent behavior]"
             "(#agent-behavior), to its next path after CORD",
             "the outcome does not continue down the recommendation order"),
            ("resume CORD on whichever route the Bootcamper opens",
             "CORD is not resumed on the route the Bootcamper opens")):
        if needle not in region:
            problems.append(why)
    if "👉" in region:
        problems.append("the outcome asks a question")
    if "follow the data recommendation hierarchy" not in squash(section_text(text, "Agent behavior")):
        problems.append("the recommendation order the outcome points at is gone")
    flat = squash(text)
    for call in ("Use `get_sample_data(dataset='list')` to show available CORD datasets; a `Denied.` "
                 "reply to it is [a denied reply](#cord-denied-reply)",
                 "source='list')` returns `record_count` per source, and a `Denied.` reply to "
                 "that call carries no count: it is [a denied reply](#cord-denied-reply)",
                 "A `Denied.` reply to the `get_sample_data` call for it is "
                 "[a denied reply](#cord-denied-reply)"):
        if call not in flat:
            problems.append("a classifying call does not link the statement: %r" % call[:50])
    return problems


class EveryClassifyingSampleDataCallCarriesTheDeniedOutcome(unittest.TestCase):
    """#805 — the sites are found by scanning, not read from a list (INV-246, INV-378)."""

    def setUp(self):
        self.corpus = shipped_corpus()

    def test_the_scan_is_clean(self):
        problems, _, _ = scan(self.corpus)
        self.assertEqual([], problems, "\n".join(problems))

    def test_the_scan_finds_the_known_sites(self):
        """⛔ Anti-vacuity (INV-265): the known classifying steps are a floor."""
        _, classifying, mentions = scan(self.corpus)
        self.assertGreaterEqual(mentions, 25, "the scan reads almost nothing")
        for site in REQUIRED_SITES:
            with self.subTest(site=site[1]):
                self.assertIn(site, classifying)

    def test_every_exemption_carries_a_reason(self):
        for key, reason in EXEMPT.items():
            with self.subTest(key=key[2][:40]):
                self.assertGreater(len(reason.split()), 3, "an exemption with no reason")

    def test_module_1_step_4b_has_the_outcome(self):
        self.assertEqual([], step_4b_problems(self.corpus[M01_DISCOVERY]))

    def test_module_4_has_the_outcome(self):
        self.assertEqual([], module_4_problems(self.corpus[M04_SKILL]))

    def test_no_pointing_site_restates_the_remedy(self):
        """INV-300 — Module 3b's sentence is pointed at from Modules 1 and 4, never copied."""
        self.assertEqual([], restatements(self.corpus))

    def test_module_4_states_the_outcome_once(self):
        blocks = blocks_of(M04_SKILL, self.corpus[M04_SKILL])
        self.assertEqual(1, sum(1 for b in blocks if is_statement(b)))


class TheScanSeesWhatItWasWrittenFor(unittest.TestCase):
    """⛔ Negative controls (INV-282), each on a mutated in-memory copy of the corpus."""

    def setUp(self):
        self.corpus = shipped_corpus()

    def mutated(self, relpath, old, new):
        corpus = dict(self.corpus)
        self.assertIn(old, corpus[relpath], "the control's anchor text is gone; update it")
        corpus[relpath] = corpus[relpath].replace(old, new, 1)
        return corpus

    def assertReported(self, corpus, fragment, exempt=None):
        problems, _, _ = scan(corpus, exempt)
        self.assertTrue(any(fragment in p for p in problems), "\n".join(problems) or "clean")

    def test_removing_the_outcome_from_module_1_is_reported(self):
        text = self.corpus[M01_DISCOVERY]
        bullet = re.search(r"(?ms)^- \*\*`Denied\.` reply\*\*.*?(?=^\s*$)", text).group(0)
        corpus = self.mutated(M01_DISCOVERY, bullet, "")
        self.assertReported(corpus, "carries no `denied` outcome and no pointer to one: "
                            + M01_DISCOVERY)
        self.assertTrue(step_4b_problems(corpus[M01_DISCOVERY]))

    def test_removing_the_outcome_from_module_4_is_reported(self):
        text = self.corpus[M04_SKILL]
        start = text.index('<a id="cord-denied-reply"></a>')
        end = text.index('<a id="truncated-cord-source"></a>')
        corpus = self.mutated(M04_SKILL, text[start:end], "")
        self.assertReported(corpus, "carries no `denied` outcome and no pointer to one: "
                            + M04_SKILL)
        self.assertTrue(module_4_problems(corpus[M04_SKILL]))

    def test_a_module_4_call_that_stops_linking_is_reported(self):
        corpus = self.mutated(
            M04_SKILL, "; a `Denied.` reply to it is\n[a denied reply](#cord-denied-reply), "
            "not an empty catalog.", ".")
        self.assertReported(corpus, "does not link that statement: " + M04_SKILL)

    def test_a_new_classifying_call_in_a_new_step_is_reported(self):
        corpus = self.mutated(
            M05_PHASE1, "\n## 5a. ",
            "\n## 4z. Check a second dataset\n\nCall `get_sample_data(dataset='london', "
            "source='list')` and classify the reply: available, or unavailable.\n\n## 5a. ")
        self.assertReported(corpus, "carries no `denied` outcome and no pointer to one: "
                            + M05_PHASE1 + " › 4z.")

    def test_a_new_classifying_call_in_module_4_step_2_is_reported(self):
        corpus = self.mutated(
            M04_SKILL, "\n<a id=\"truncated-cord-source\"></a>",
            "\nRetry `get_sample_data(dataset='london', source='list')` once; if it still "
            "returns nothing, CORD is unavailable.\n\n<a id=\"truncated-cord-source\"></a>")
        self.assertReported(corpus, "does not link that statement: " + M04_SKILL)

    def test_exempting_a_classifying_mention_is_reported(self):
        exempt = dict(EXEMPT)
        exempt[(M01_DISCOVERY, STEP_4B, "Wait up to 30s")] = "a deliberately wrong exemption"
        self.assertReported(self.corpus, "a classifying mention is exempted", exempt)

    def test_an_exemption_that_drifted_is_reported(self):
        corpus = self.mutated(
            M04_SKILL, "Illustration only, dated, never a constant",
            "Illustration only, dated, and never a constant")
        self.assertReported(corpus, "stale")
        self.assertReported(corpus, "does not link that statement")

    def test_module_1_clauses_are_each_checked(self):
        for old, new, why in (
                ("Do not retry it, and do not report", "Retry it once, and do not report",
                 "retried"),
                ("Then back the\n  scenario with synthetic data", "Then ask 👉 whether to back "
                 "the\n  scenario with synthetic data", "asks a question"),
                ("provenance `synthesized`, and say", "provenance `cord`, and say",
                 "`synthesized`"),
                ("give the remedy by pointer to\n  `../module-03b",
                 "give the remedy by pointer to\n  `../module-03c", "not pointed at"),
                ("retry once on a timeout, never on a `Denied.` reply", "retry once",
                 "retry clause")):
            with self.subTest(why=why):
                corpus = self.mutated(M01_DISCOVERY, old, new)
                self.assertTrue(any(why in p for p in step_4b_problems(corpus[M01_DISCOVERY])),
                                step_4b_problems(corpus[M01_DISCOVERY]))

    def test_module_4_clauses_are_each_checked(self):
        for old, new, why in (
                ("⛔ **(INV-378) Do not retry it.**", "⛔ **(INV-378) Retry it once.**", "retried"),
                ("⛔ **(INV-247) Ask no new question about it.**",
                 "👉 **Ask whether to try the free-data catalog.**", "question"),
                ("**Then continue down the data recommendation hierarchy**",
                 "**Then stop the module**", "recommendation order")):
            with self.subTest(why=why):
                corpus = self.mutated(M04_SKILL, old, new)
                self.assertTrue(any(why in p for p in module_4_problems(corpus[M04_SKILL])),
                                module_4_problems(corpus[M04_SKILL]))

    def test_a_restated_remedy_is_reported(self):
        corpus = self.mutated(M01_DISCOVERY, "which states it; it is not restated\n  here",
                              "which says: " + SERVER_REMEDY[2])
        self.assertIn((M01_DISCOVERY, SERVER_REMEDY[2][:30]), restatements(corpus))

    def test_an_empty_corpus_finds_no_site(self):
        _, classifying, mentions = scan({})
        self.assertEqual(0, mentions)
        self.assertFalse(set(REQUIRED_SITES) <= classifying)

    def test_the_scan_survives_a_reflow(self):
        """INV-346 — one word per line inside every block changes no verdict.

        A list marker keeps its first word, as any re-wrap of Markdown does: alone on a line
        it would no longer be a list item.
        """
        corpus = {}
        for relpath, text in self.corpus.items():
            lines, fenced = [], False
            for line in text.split("\n"):
                bare = re.sub(r"^[ \t]*(?:>[ \t]?)*", "", line)
                if bare.lstrip().startswith(("```", "~~~")):
                    fenced = not fenced
                if fenced or not bare.strip() or re.match(r"#{1,6}\s|[ \t]*<", line):
                    lines.append(line)
                    continue
                prefix = line[:len(line) - len(bare)]
                words = bare.split()
                if re.match(r"\s*(?:[-*+]|\d+\.)\s", bare) and len(words) > 1:
                    words[:2] = [" ".join(words[:2])]
                lines.extend(prefix + word for word in words)
            corpus[relpath] = "\n".join(lines)
        problems, classifying, mentions = scan(corpus)
        self.assertEqual([], problems, "\n".join(problems))
        self.assertEqual(scan(self.corpus)[2], mentions)


if __name__ == "__main__":
    unittest.main()
