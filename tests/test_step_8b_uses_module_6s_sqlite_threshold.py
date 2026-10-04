"""Data collection Step 8b compares against Module 6 Phase A's SQLite threshold (#330).

Step 8b warns about a long SQLite load, and ends the turn on a pinned three-option question,
when the loadable total is above a threshold. It called that threshold "the load-time
threshold", and no file defined it. Three figures were available, and each gave a different
answer for a typical bootcamp dataset:

- `sdk_guide(topic='load', record_count=…)` switches from the single-threaded demo to the
  threaded loader above a record count, and Step 8b's own text called that figure "the
  record-count threshold";
- the same reply's license note cautions against its own container environment above a larger
  count;
- Module 6 Phase A's SQLite volume pre-load check, item 3, takes its threshold from
  `search_docs(query="loading", category="anti_patterns")` → "Do Not Use SQLite in Production".

On the 2026-10-01 walk (a generated scenario, SQLite, no license cap) the first reading fires the
warning and the other two stay silent, so whether a 👉 question appeared was decided by a number
nobody stated. Module 6 already uses item 3's threshold throughout, and Phase A skips its own
question when a Module 4 decision covers the same load, so Step 8b now uses item 3's threshold
too, cited by link rather than restated (INV-300), with no figure written into the step. Both
heads-ups then fire on the same loads.

Six checks, each a pure function over the text, so every negative control runs the same check
over a mutated copy, and the pre-#330 wording (kept below as fixtures) fails them:

1. Step 8b sub-step 2 cites item 3 by a link that resolves to Phase A's section heading, names
   item 3's route, writes no figure into any sentence about the threshold, and says a threshold
   the server does not return leaves the step silent (INV-080).
2. Module 4's summary line for Step 8b refers to the same threshold.
3. The `sdk_guide` sentence calls its figure the template switch, says it is not this warning's
   threshold, carries a dated MCP note, and names no figure.
4. No skill says "load-time threshold".
5. Item 3 still sources its threshold from that route, so the citation points at a real rule.
6. (#439) Step 8b no longer says that a nearby wording of the hardware-sizing query fails to
   find the Hardware Sizing FAQ. That warning was stamped on server 1.32.9 (2026-08-14), and on
   server 1.37.19, docs index 2026-10-02 18:46 UTC (2026-10-04), the longer phrasing it quoted
   returns the FAQ at rank 1. Its replacement tells the guide to use the query as written,
   because a paraphrase is unmeasured, cites INV-291, and carries no example phrasing and no
   stamp, so no measurement can make it stale. The pre-#439 sentence is kept below as a
   fixture, and restoring it fails the check.

Everything is asserted as behavior in shipped guidance, so any implementation language
satisfies it (INV-002).

Enforces **INV-331**'s 2026-10-02 note (#330, with #345): Step 8b uses the same MCP-sourced
threshold as Module 6 Phase A's pre-load check. It asserts that the guidance *states* this, and
does **not** establish that a live run fires both heads-ups on the same loads, which only
`dry-run` phase 3 can observe.

Source: GitHub issue #330, from the 2026-10-01 dry run, P3-9.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"
PHASE_A = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"

STEP_8B_HEADING = "### 8b. SQLite load-time warning (collection-time heads-up)"
STEP_9_HEADING = "### 9. "
SUB_STEP_2 = "2. **Decide whether to warn.**"
QUESTION = "👉 **Loading all collected records into SQLite"
SUMMARY_BULLET = "- **Step 8b** says nothing"
PHASE_A_SECTION = "## SQLite volume pre-load check"
ITEM_3 = "3. **Prompt only when it matters.**"
ROUTE_QUERY = 'search_docs(query="loading",'
ROUTE_CATEGORY = 'category="anti_patterns")'
ROUTE_ARTICLE = '"Do Not Use SQLite in Production"'
SDK_GUIDE = "`sdk_guide(topic='load',"
#: The end of the `sdk_guide` sentence's own stamp, which ends the passage check 3 reads (#439).
SDK_GUIDE_STAMP_END = "1.37.16, 2026-10-01)"
#: The rule that replaced the retired warning (#439): the start of its sentence.
AS_WRITTEN_RULE = "⚠️ Use the query as written"

#: A link from Module 4 to a section of Phase A, and the fragment it names.
PHASE_A_LINK = re.compile(
    r"\]\(\.\./module-06-data-processing/phaseA-build-loading\.md#([a-z0-9-]+)\)")

#: Digits that are not a figure: link targets, invariant ids, step and item numbers, server
#: versions and dates. What is left after removing these is a number in the prose.
NOT_A_FIGURE = re.compile(
    r"\]\([^)]*\)"
    r"|INV-\d+"
    r"|\b(?:item|Step|Module|sub-step|Phase)\s+\d+[a-z]?\b"
    r"|\b\d+\.\d+\.\d+\b"
    r"|\b\d{4}-\d{2}-\d{2}\b",
    re.IGNORECASE,
)
DIGIT = re.compile(r"\d")


#: The retired name for Module 6's threshold.
LOAD_TIME_THRESHOLD = re.compile(r"(?i)load-time threshold")


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def section(text, start_marker, end_marker):
    start = text.index(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    return text[start:] if end < 0 else text[start:end]


def step_8b(text):
    return section(text, STEP_8B_HEADING, "\n" + STEP_9_HEADING)


def sub_step_2(step):
    """Sub-step 2 up to its pinned question: the trigger, not the warning's own content."""
    return section(step, SUB_STEP_2, QUESTION)


def sentences(text):
    """Flattened sentences, split after a full stop that ends a clause."""
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z⛔*(_⚠👉-])", flat(text)) if s]


def figures_in(sentence):
    """The prose numbers left in a sentence once ids, steps, versions and dates are removed."""
    return DIGIT.findall(NOT_A_FIGURE.sub("", sentence))


def github_slug(heading):
    """The fragment GitHub generates for a Markdown heading."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def phase_a_fragments(text):
    """Every heading fragment in Phase A, mapped to its heading line."""
    return {github_slug(m.group(1)): m.group(0)
            for m in re.finditer(r"(?m)^#{1,6} (.+)$", text)}


def link_problems(text, phase_a_text):
    """The text must link to Phase A's SQLite volume pre-load check heading."""
    fragments = [m.group(1) for m in PHASE_A_LINK.finditer(text)]
    if not fragments:
        return ["no link to Module 6 Phase A's SQLite volume pre-load check"]
    headings = phase_a_fragments(phase_a_text)
    problems = []
    for fragment in fragments:
        heading = headings.get(fragment)
        if heading is None:
            problems.append(f"the link fragment #{fragment} names no heading in Phase A")
        elif not heading.startswith(PHASE_A_SECTION):
            problems.append(f"the link fragment #{fragment} names {heading!r}, not the SQLite "
                            "volume pre-load check")
    return problems


def threshold_problems(step, phase_a_text):
    """Check 1: sub-step 2 cites item 3's threshold and its route, and writes no figure."""
    if SUB_STEP_2 not in step or QUESTION not in step:
        return ["Step 8b has no sub-step 2 ending on its pinned question"]
    body = sub_step_2(step)
    text = flat(body)
    problems = []
    if re.search(r"(?i)load-time threshold", text):
        problems.append('sub-step 2 still says "the load-time threshold", which no file defines')
    problems += link_problems(body, phase_a_text)
    if not re.search(r"\bitem 3\b", text):
        problems.append("sub-step 2 does not name item 3, the check whose threshold it uses")
    for needle in (ROUTE_QUERY, ROUTE_CATEGORY, ROUTE_ARTICLE):
        if needle not in text:
            problems.append(f"sub-step 2 does not name item 3's route: {needle} is missing")
    if not re.search(r"(?i)one threshold for both SQLite heads-ups", text):
        problems.append("sub-step 2 does not say both heads-ups compare against one threshold")
    if not re.search(r"(?i)does not return the threshold", text):
        problems.append("sub-step 2 does not say what happens when the server does not return "
                        "the threshold")
    if not re.search(r"(?i)threshold is\s+indeterminate", text):
        problems.append("sub-step 2 does not call a threshold the server did not return "
                        "indeterminate")
    if not re.search(r"(?i)never substitute a remembered figure", text):
        problems.append("sub-step 2 does not forbid a remembered figure (INV-080)")
    for s in sentences(body):
        if re.search(r"(?i)threshold", s) and figures_in(s):
            problems.append(f"a sentence about the threshold writes a figure: {s[:120]!r}")
    return problems


def summary_problems(text, phase_a_text):
    """Check 2: the module's summary line refers to item 3's threshold."""
    lines = [m.start() for m in re.finditer(re.escape(SUMMARY_BULLET), text)]
    if len(lines) != 1:
        return [f"expected one summary bullet for Step 8b, found {len(lines)}"]
    start = lines[0]
    end = text.find("\n\n", start)
    bullet = text[start:end]
    problems = []
    if re.search(r"(?i)below its threshold", flat(bullet)):
        problems.append('the summary still says "below its threshold", naming no threshold')
    problems += link_problems(bullet, phase_a_text)
    if not re.search(r"\bitem 3\b", flat(bullet)):
        problems.append("the summary does not name item 3")
    if figures_in(flat(bullet)):
        problems.append("the summary writes a figure for the threshold")
    return problems


def sdk_guide_problems(step):
    """Check 3: the `sdk_guide` sentence calls its count the template switch, with a dated note."""
    text = flat(step)
    at = text.find(SDK_GUIDE + " record_count=…)`")
    if at < 0:
        return ["Step 8b no longer names sdk_guide(topic='load', record_count=…)"]
    end = text.find(SDK_GUIDE_STAMP_END, at, at + 800)
    passage = text[at:end + len(SDK_GUIDE_STAMP_END) if end > 0 else at + 800]
    problems = []
    if re.search(r"(?i)record-count threshold", passage):
        problems.append('the sdk_guide sentence still calls its figure "the record-count '
                        'threshold"')
    if not re.search(r"(?i)template switch", passage):
        problems.append("the sdk_guide sentence does not call its figure the template switch")
    if not re.search(r"(?i)not this warning's threshold", passage):
        problems.append("the sdk_guide sentence does not say its figure is not this warning's "
                        "threshold")
    if not re.search(r"1\.37\.16, 2026-10-01", passage):
        problems.append("the sdk_guide sentence carries no dated MCP note (server 1.37.16, "
                        "2026-10-01)")
    if figures_in(passage.replace("1.37.16", "")):
        problems.append("the sdk_guide sentence names a figure")
    return problems


#: The retired claim (#439): a wording of the query "does not find" the FAQ, or the longer
#: phrasing the old warning quoted as one that misses.
RETIRED_CLAIM = re.compile(
    r"(?i)(?:wordings?|phrasings?|paraphras\w*)\W+(?:\w+\W+){0,3}?do(?:es)?\W+(?:\*\*)?not"
    r"(?:\*\*)?\W+find\W+the\W+FAQ"
    r"|records per second load time")
#: A stamp or a measurement: a server version, a date, or the words a stamp is written with.
A_STAMP = re.compile(r"\b\d+\.\d+\.\d+\b|\b\d{4}-\d{2}-\d{2}\b|(?i:\bverified\b|\bindexed\b|"
                     r"\bre-checked\b|\bmeasured\b|\bserver\b)")
#: A quoted phrasing: text in double quotes, or a backticked or single-quoted query.
A_QUOTED_PHRASING = re.compile(r"\"[^\"]+\"|“[^”]+”|'[^']{3,}'|`[^`]+`")


def as_written_problems(step):
    """Check 6 (#439): the retired claim is gone, and its replacement cites no measurement."""
    text = flat(step)
    problems = []
    for m in RETIRED_CLAIM.finditer(text):
        problems.append(f"Step 8b says a phrasing does not find the FAQ: {m.group(0)!r}")
    at = text.find(AS_WRITTEN_RULE)
    if at < 0:
        return problems + ["Step 8b does not tell the guide to use the query as written"]
    # The rule's sentence: up to the first full stop that ends it (one followed by a space).
    # `sentences()` would run on into the `MCP-NEGATIVE` comment that follows it.
    rule = re.match(r".*?\.(?=\s|$)", text[at:]) or re.match(r".*", text[at:])
    rule = rule.group(0)
    if not re.search(r"(?i)paraphrase is unmeasured", rule):
        problems.append("the as-written rule does not say a paraphrase is unmeasured")
    if not re.search(r"(?i)not evidence about what it returns", rule):
        problems.append("the as-written rule does not say a query's words are not evidence "
                        "about what it returns")
    if "(INV-291)" not in rule:
        problems.append("the as-written rule does not cite INV-291")
    stamp = A_STAMP.search(rule)
    if stamp:
        problems.append(f"the as-written rule carries a stamp or measurement: {stamp.group(0)!r}")
    quoted = A_QUOTED_PHRASING.search(rule)
    if quoted:
        problems.append(f"the as-written rule quotes an example phrasing: {quoted.group(0)!r}")
    return problems


def item_3_problems(phase_a_text):
    """Check 5: item 3 still sources the threshold from the route Step 8b names."""
    if PHASE_A_SECTION not in phase_a_text:
        return ["Phase A has no SQLite volume pre-load check section"]
    part = section(phase_a_text, PHASE_A_SECTION, "\n## ")
    if ITEM_3 not in part:
        return ["the SQLite volume pre-load check has no item 3"]
    item = flat(section(part, ITEM_3, "\n4. "))
    problems = []
    for needle in (ROUTE_QUERY, ROUTE_CATEGORY, ROUTE_ARTICLE):
        if needle not in item:
            problems.append(f"item 3 no longer names {needle}")
    if not re.search(r"(?i)source that threshold from MCP", item):
        problems.append("item 3 no longer sources its threshold from MCP")
    return problems


#: The pre-#330 wording, kept so the negative controls test the shape the issue reported.
PRE_FIX_SUB_STEP_2 = """2. **Decide whether to warn.** Warn only when the database is SQLite **and the LOADABLE total** is
   above the load-time threshold. Otherwise (loadable at or below the threshold, any non-SQLite
   engine, or indeterminate inputs) say nothing about load time and continue to the Step 9
   transition. A 19,500-record collection under a 500-record cap therefore says **nothing**, which
   is correct: 500 records is not a long load.
"""
PRE_FIX_SUMMARY = "- **Step 8b** says nothing when the loadable total is below its threshold.\n\n"
PRE_FIX_SDK_GUIDE = """`sdk_guide(topic='load',
     record_count=…)` returns the license note and the record-count threshold but **no timing
     figures at all**, so it is the wrong route for this. ⚠️ Nearby wordings do **not** find the FAQ
"""
#: The pre-#439 warning, verbatim, kept so the negative control restores the retired claim.
PRE_439_WARNING = """⚠️ Nearby wordings do **not** find the FAQ
     — "hardware sizing capacity planning records per second load time" returns flag docs and code
     snippets instead — so use the query as written rather than paraphrasing it (verified on MCP
     server 1.32.9, docs indexed 2026-08-11 20:52 UTC, 2026-08-14)."""


class StepEightBUsesItemThreesThreshold(unittest.TestCase):

    def setUp(self):
        self.text = read(MODULE_04)
        self.step = step_8b(self.text)
        self.phase_a = read(PHASE_A)

    def test_sub_step_2_cites_item_3s_threshold_and_route(self):
        self.assertEqual(threshold_problems(self.step, self.phase_a), [])

    def test_the_summary_line_refers_to_the_same_threshold(self):
        self.assertEqual(summary_problems(self.text, self.phase_a), [])

    def test_the_sdk_guide_figure_is_the_template_switch(self):
        self.assertEqual(sdk_guide_problems(self.step), [])

    def test_no_skill_says_load_time_threshold(self):
        # Matched across line wraps (#424): "load-time\nthreshold" is still the old name.
        hits = [f"{p.relative_to(SKILLS)}:{n}"
                for p in sorted(SKILLS.rglob("*.md"))
                for n in match_lines(read(p), LOAD_TIME_THRESHOLD)]
        self.assertEqual(hits, [])

    def test_a_wrapped_old_name_is_caught_at_its_first_line(self):
        """Negative control (#424): "load-time" ends line 1 and "threshold" begins line 2."""
        wrapped = "Compare the estimate with the load-time\nthreshold in Phase A.\n"
        self.assertEqual([1], match_lines(wrapped, LOAD_TIME_THRESHOLD))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any("load-time threshold" in l.lower() for l in wrapped.split("\n")))

    def test_item_3_still_sources_the_threshold_from_that_route(self):
        self.assertEqual(item_3_problems(self.phase_a), [])

    def test_the_as_written_rule_cites_no_measurement(self):
        self.assertEqual(as_written_problems(self.step), [])

    def test_the_slug_matches_githubs_for_the_section_heading(self):
        """The fragment rule itself, pinned on the heading this link depends on."""
        self.assertEqual(
            github_slug("SQLite volume pre-load check (stop-and-confirm heads-up, not a "
                        "mandatory gate)"),
            "sqlite-volume-pre-load-check-stop-and-confirm-heads-up-not-a-mandatory-gate")


class NegativeControls(unittest.TestCase):
    """Each mutation restores a shape the guard exists to catch."""

    def setUp(self):
        self.text = read(MODULE_04)
        self.step = step_8b(self.text)
        self.phase_a = read(PHASE_A)
        self.sub_step = sub_step_2(self.step)

    def mutate(self, old, new, source=None):
        source = self.step if source is None else source
        changed = source.replace(old, new, 1)
        self.assertTrue(changed != source, f"control did not apply: {old[:60]!r}")
        return changed

    def test_the_pre_fix_sub_step_2_fails(self):
        broken = self.mutate(self.sub_step, PRE_FIX_SUB_STEP_2 + "\n   ")
        problems = threshold_problems(broken, self.phase_a)
        self.assertTrue(any("load-time threshold" in p for p in problems), problems)
        self.assertTrue(any("no link" in p for p in problems), problems)
        self.assertTrue(any("item 3" in p for p in problems), problems)
        self.assertTrue(any("indeterminate" in p for p in problems), problems)

    def test_the_pre_fix_summary_fails(self):
        start = self.text.index(SUMMARY_BULLET)
        bullet = self.text[start:self.text.index("\n\n", start) + 2]
        broken = self.mutate(bullet, PRE_FIX_SUMMARY, self.text)
        problems = summary_problems(broken, self.phase_a)
        self.assertTrue(any("below its threshold" in p for p in problems), problems)
        self.assertTrue(any("no link" in p for p in problems), problems)

    def test_the_pre_fix_sdk_guide_sentence_fails(self):
        flat_step = flat(self.step)
        at = flat_step.index(SDK_GUIDE)
        end = flat_step.index(SDK_GUIDE_STAMP_END, at) + len(SDK_GUIDE_STAMP_END)
        broken = flat_step[:at] + flat(PRE_FIX_SDK_GUIDE) + flat_step[end:]
        problems = sdk_guide_problems(broken)
        self.assertTrue(any("record-count threshold" in p for p in problems), problems)
        self.assertTrue(any("template switch" in p for p in problems), problems)
        self.assertTrue(any("dated MCP note" in p for p in problems), problems)

    def test_a_figure_written_beside_the_threshold_fails(self):
        for figure in ("about 100K records", "100,000 records", "10,000 records",
                       "500 records"):
            with self.subTest(figure=figure):
                broken = self.mutate("Ask that route at request time",
                                     f"The threshold is {figure}. Ask that route at request time")
                problems = threshold_problems(broken, self.phase_a)
                self.assertTrue(any("writes a figure" in p for p in problems), problems)

    def test_a_link_to_another_section_fails(self):
        broken = self.mutate(
            "#sqlite-volume-pre-load-check-stop-and-confirm-heads-up-not-a-mandatory-gate)",
            "#3-create-the-production-loading-program)")
        problems = threshold_problems(broken, self.phase_a)
        self.assertTrue(any("not the SQLite volume pre-load check" in p for p in problems),
                        problems)

    def test_a_dangling_fragment_fails(self):
        broken = self.mutate(
            "#sqlite-volume-pre-load-check-stop-and-confirm-heads-up-not-a-mandatory-gate)",
            "#sqlite-volume-pre-load-check)")
        problems = threshold_problems(broken, self.phase_a)
        self.assertTrue(any("names no heading" in p for p in problems), problems)

    def test_a_dropped_route_fails(self):
        broken = self.mutate(ROUTE_ARTICLE, '"SQLite guidance"')
        problems = threshold_problems(broken, self.phase_a)
        self.assertTrue(any(ROUTE_ARTICLE in p for p in problems), problems)

    def test_a_dropped_not_returned_clause_fails(self):
        start = self.step.index("   - **The server does not return the threshold")
        end = self.step.index("   - **Warn:**", start)
        broken = self.mutate(self.step[start:end], "")
        problems = threshold_problems(broken, self.phase_a)
        self.assertTrue(any("does not return the threshold" in p for p in problems), problems)
        self.assertTrue(any("remembered figure" in p for p in problems), problems)

    def test_a_figure_in_the_sdk_guide_sentence_fails(self):
        broken = self.mutate("the **template switch**, the volume above which",
                             "the **template switch**, 500 records, the volume above which")
        self.assertTrue(any("names a figure" in p for p in sdk_guide_problems(broken)))

    def as_written_rule(self):
        """The replacement sentence (#439) as it sits in the step, line breaks included."""
        at = self.step.index(AS_WRITTEN_RULE)
        return self.step[at:self.step.index("(INV-291).", at) + len("(INV-291).")]

    def test_the_pre_439_warning_fails(self):
        broken = self.mutate(self.as_written_rule(), PRE_439_WARNING)
        problems = as_written_problems(broken)
        self.assertTrue(any("does not find the FAQ" in p for p in problems), problems)
        self.assertTrue(any("records per second load time" in p for p in problems), problems)
        self.assertTrue(any("use the query as written" in p for p in problems), problems)

    def test_the_retired_claim_beside_the_rule_fails(self):
        """The old claim, reworded and wrapped, appended after a rule that is otherwise intact."""
        for claim in ("Nearby wordings do **not** find the FAQ.",
                      "A longer phrasing does not\n     find the FAQ.",
                      "Paraphrases do not find the FAQ."):
            with self.subTest(claim=claim):
                rule = self.as_written_rule()
                broken = self.mutate(rule, rule + " " + claim)
                problems = as_written_problems(broken)
                self.assertTrue(any("does not find the FAQ" in p for p in problems), problems)

    def test_a_stamp_on_the_rule_fails(self):
        for stamp in (" (verified on MCP server 1.37.19, 2026-10-04)",
                      " (docs indexed 2026-10-02 18:46 UTC)"):
            with self.subTest(stamp=stamp):
                broken = self.mutate("(INV-291).", "(INV-291)" + stamp + ".")
                problems = as_written_problems(broken)
                self.assertTrue(any("stamp or measurement" in p for p in problems), problems)

    def test_an_example_phrasing_on_the_rule_fails(self):
        broken = self.mutate("rather than paraphrasing it:",
                             'rather than paraphrasing it as "hardware sizing load time":')
        problems = as_written_problems(broken)
        self.assertTrue(any("example phrasing" in p for p in problems), problems)

    def test_a_rule_without_its_citation_or_reason_fails(self):
        broken = self.mutate("(INV-291).", ".")
        self.assertTrue(any("cite INV-291" in p for p in as_written_problems(broken)))
        broken = self.mutate("a paraphrase\n     is unmeasured", "a paraphrase is risky")
        self.assertTrue(any("unmeasured" in p for p in as_written_problems(broken)))

    def test_item_3_losing_its_route_fails(self):
        at = self.phase_a.index(ITEM_3)
        item = self.phase_a[at:]
        broken = self.phase_a[:at] + self.mutate(ROUTE_ARTICLE, '"SQLite notes"', item)
        self.assertTrue(any(ROUTE_ARTICLE in p for p in item_3_problems(broken)))


if __name__ == "__main__":
    unittest.main()
