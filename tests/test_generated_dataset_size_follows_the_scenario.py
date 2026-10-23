"""How many records Data collection generates follows the scenario, never the license limit.

**The history this guard replaces.** A guide on the synthesized-scenario path (plugin 0.5.1)
sized a generated dataset **down from 538 records to 466** to stay under the built-in evaluation
license's limit, reasoning that an absent `license_record_limit` meant no custom license was
configured. It then reached Step 8a, measured as instructed, and found the workstation carried a
custom EVAL license with `recordLimit: 0`, no cap at all. The downsizing was unnecessary and was
withdrawn. The 2026-08-17 change
(`generated-dataset-is-sized-before-anything-measures-the-license`) read
the incident as "the guide sized before it measured", made choosing how many records to generate
a LICENSE-CAPACITY decision routed through *License limit and dataset size (canonical framing)*,
and pinned that in `tests/test_generated_dataset_size_is_a_license_decision.py`.

INV-277, registered 2026-08-28, read the same harm the other way: the generated size MUST NOT be
tied to license capacity, which nothing has measured at that point. #603 then stated, beside the
old directive, that a scenario larger than the limit is generated whole with nothing asked. So
Module 4 told the guide both things, and option 5 ("generate it for me") routed only to the stale
one. The 538→466 run is still the reason, kept in the module as INV-277's: an absent limit means
never measured (INV-244), and under-generating leaves Modules 6 and 7 too little overlap to show
cross-source resolution (INV-150).

**The rule now (#779).** One count rule at the head of Step 2's `provenance: synthesized` branch
(`#generated-record-count`): the source's `scenario_record_count`, else the count
`docs/business_problem.md` records for it, else INV-277's default of about 10,000 records. It
reads no license field; capacity is Step 8a's, from the collected total. The canonical framing,
the generation directives, the over-limit rule, option 5 and the Scenario source fields note all
point at it, and none states a second count.

What this file pins:

1. **No Module 4 sentence ties the generated count to the license.** Every sentence pairing a
   generated count or size with a license, capacity or `recordLimit` term must carry one of the
   denials the rule uses, or be the recorded 538→466 incident. Negative controls: each sentence
   the old rule shipped (`:574`'s directive, the framing's trigger, the `recordLimit: 0`
   paragraph, option 5's sizing) fails when restored.
2. **The head rule states the three-step chain**, in order, inside the synthesized branch and
   before any generation directive, cites INV-277 on its ⛔ line, and reads no license field.
3. **Option 5's entry points at it** and states no count of its own.
4. **The other sites point at it** rather than restating it.

Phrase checks run on whitespace-collapsed text (INV-346). Stdlib only; the skill is read as text.

Source issue: #779. Invariants applied: INV-277, INV-244, INV-300.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" /
         "module-04-data-collection" / "SKILL.md")

ANCHOR = '<a id="generated-record-count"></a>'
LINK = "(#generated-record-count)"
BRANCH_LEAD = "- **`provenance: synthesized`** → **generate the source files.**"

#: A sentence about how many records a generation step writes.
COUNT = re.compile(
    r"(?i)(how many records[^.]{0,40}generat|records to generate"
    r"|\bsiz(?:e|es|ed|ing) the (?:generated )?data\b"
    r"|generat\w*[^.]{0,60}\b(?:counts?|sizes?|sized|sizing|downsiz\w*|shrink)\b"
    r"|\b(?:counts?|sizes?|sized|sizing|downsiz\w*|shrink)\b[^.]{0,60}generat)")
#: A license, capacity or limit term.
LICENSE = re.compile(r"(?i)licen[cs]e|capacity|recordlimit|record_limit")
#: The denials the rule and its pointers use. A pairing carrying one says the count is NOT tied.
DENIALS = (
    "is not one of these decisions",
    "never the license limit",
    "is not a license decision",
    "is not tied to license capacity",
)
#: Pairings allowed without a denial, each with its reason.
EXEMPT = (
    ("down from 538 records to 466",
     "the recorded incident, quoted as the reason INV-277 forbids tying the size to the limit"),
)


def body():
    return SKILL.read_text(encoding="utf-8")


def squash(text):
    """Collapse whitespace and drop blockquote markers, so wrapped phrases match."""
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M)).strip()


def sentences(text):
    for para in re.split(r"\n\s*\n", text):
        for sentence in re.split(r"(?<=[.!?])\s+|(?<=[.!?]\*\*)\s+", squash(para)):
            if sentence:
                yield sentence


def license_tied_sentences(text):
    """Every sentence that pairs the generated count with a license term and denies nothing."""
    found = []
    for sentence in sentences(text):
        if not (COUNT.search(sentence) and LICENSE.search(sentence)):
            continue
        low = sentence.lower()
        if any(d in low for d in DENIALS):
            continue
        if any(phrase in sentence for phrase, _ in EXEMPT):
            continue
        found.append(sentence)
    return found


def head_rule(text=None):
    """The count rule, from its anchor to the generation branch's next ⛔ directive."""
    text = body() if text is None else text
    i = text.index(ANCHOR)
    return text[i:text.index("⛔ **Ask nothing, recommend no CORD alternative", i)]


def head_rule_problems(text):
    problems = []
    if text.count(ANCHOR) != 1:
        return ["the count rule's anchor is missing or doubled"]
    branch = text.index(BRANCH_LEAD)
    anchor = text.index(ANCHOR)
    if not branch < anchor < text.index("Generate the SHAPE differences the scenario promised"):
        problems.append("the count rule is not at the head of the synthesized branch")
    rule = squash(head_rule(text))
    if not rule.startswith(ANCHOR + "⛔ **(INV-277) The generated record count follows the "
                           "scenario, never the license limit.**"):
        problems.append("the count rule's ⛔ line does not cite INV-277 or name the rule")
    steps = (
        "1. the source's `scenario_record_count`;",
        "2. otherwise the count `docs/business_problem.md` records for the source",
        "3. otherwise INV-277's default of about 10,000 records",
    )
    at = []
    for step in steps:
        if step not in rule:
            problems.append("the count rule does not state %r" % step)
        else:
            at.append(rule.index(step))
    if len(at) == len(steps) and at != sorted(at):
        problems.append("the count rule's three steps are out of order")
    for phrase, why in (
        ("Before any file is written", "does not apply before any file is written"),
        ("This rule reads no license field, `license_record_limit` included",
         "does not say it reads no license field"),
        ("means never measured (INV-244) and is no reason to downsize",
         "does not say an absent limit is no reason to downsize"),
        ("Capacity is decided after collection, at Step 8a, from the real total",
         "does not leave capacity to Step 8a"),
        ("falls through to here", "does not say an unreadable count falls through"),
    ):
        if phrase not in rule:
            problems.append("the count rule %s" % why)
    return problems


def option_5(text=None):
    """Option 5's entry under Handling each answer, to the next entry."""
    text = squash(body() if text is None else text)
    i = text.index('- **5, "I don\'t have my own data":**')
    return text[i:text.index('- **Secondary offer, "Synthesized test data":**', i)]


def option_5_problems(entry):
    problems = []
    if LINK not in entry:
        problems.append("option 5 does not point at the count rule")
    if "states no record count of its own" not in entry:
        problems.append("option 5 does not say it states no count of its own")
    if "License limit and dataset size" in entry:
        problems.append("option 5 still sizes by the license framing")
    if re.search(r"\d[\d,]{2,}", re.sub(r"INV-\d+", "", entry)):
        problems.append("option 5 states a record count")
    return problems


class NoSentenceTiesTheGeneratedCountToTheLicense(unittest.TestCase):

    def test_module_4_ties_nothing(self):
        self.assertEqual(license_tied_sentences(body()), [])

    def test_the_scan_reads_the_pairings(self):
        """Liveness: the pairing sentences are found, then cleared by their denials."""
        paired = [s for s in sentences(body()) if COUNT.search(s) and LICENSE.search(s)]
        self.assertGreaterEqual(len(paired), 4)

    def test_negative_controls_the_old_rule_restored(self):
        text = body()
        for old in (
            "⛔ **How many records to generate is a LICENSE-CAPACITY decision — do not choose it "
            "before the limit is measured.** (INV-244)",
            "Before any license-based capacity or sampling decision — ⛔ **and \"choosing how "
            "many records to GENERATE\" is one of them, not only \"sampling an existing dataset "
            "down\"** — read it.",
            "**On a measured `recordLimit: 0`, size the generated data by what the SCENARIO "
            "needs** — and not by any cap.",
            "It sizes the data by *License limit and dataset size (canonical framing)* "
            "(INV-244), so this step chooses no record count of its own.",
        ):
            with self.subTest(old=old[:50]):
                self.assertNotEqual(license_tied_sentences(text + "\n\n" + old + "\n"), [])

    def test_the_exemption_is_the_incident_only(self):
        self.assertIn("down from 538 records to 466", squash(body()))
        self.assertEqual(len(EXEMPT), 1)

    def test_the_incident_is_kept_as_inv_277s_reason(self):
        """Carried from the old guard: the figures, the forbidden inference and its cost."""
        text = squash(body())
        i = text.index("**Why INV-277 forbids tying the size to the limit.**")
        reason = text[i:text.index("**When the effective limit is below", i)]
        for phrase in ("down from 538 records to 466", "`recordLimit: 0` — no record cap at all",
                       "means **never measured**, never \"no custom license\"", "INV-244",
                       "too little overlap to demonstrate cross-source resolution (INV-150)"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reason)


class TheHeadRuleStatesTheChain(unittest.TestCase):

    def test_the_rule(self):
        self.assertEqual(head_rule_problems(body()), [])

    def test_negative_controls(self):
        text = body()
        for mutant, why in (
            (text.replace("INV-277's default of about 10,000 records", "a sensible size"),
             "default dropped"),
            (text.replace("otherwise the count `docs/business_problem.md` records", "otherwise "),
             "second step dropped"),
            (text.replace("This rule reads no license field", "This rule reads the license"),
             "license read"),
            (text.replace("⛔ **(INV-277) The generated record count", "⛔ **The generated record count"),
             "citation dropped"),
            (text.replace(ANCHOR, ""), "anchor dropped"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(mutant, text)
                self.assertNotEqual(head_rule_problems(mutant), [], why)

    def test_the_rule_states_no_license_figure(self):
        rule = re.sub(r"INV-\d+|10,000", "", squash(head_rule()))
        self.assertIsNone(re.search(r"\d[\d,]{2,}", rule))


class Option5PointsAtTheRule(unittest.TestCase):

    def test_option_5(self):
        self.assertEqual(option_5_problems(option_5()), [])

    def test_negative_controls(self):
        entry = option_5()
        for mutant, why in (
            (entry.replace(LINK, ""), "pointer dropped"),
            (entry + " It sizes the data by *License limit and dataset size (canonical framing)*.",
             "license framing restored"),
            (entry + " Generate about 10,000 records.", "count stated"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(option_5_problems(mutant), [], why)


class TheOtherSitesPointAtTheRule(unittest.TestCase):

    def test_each_site_links_the_rule(self):
        text = squash(body())
        for lead in (
            "⛔ **(INV-277) How many records to GENERATE is not one of these decisions:**",
            "⛔ **(INV-277) The record count is not a license decision:",
            "**When the effective limit is below the record count the scenario calls for",
            "An entry with no `scenario_record_count` was written before the field existed",
        ):
            with self.subTest(site=lead[:40]):
                self.assertIn(lead, text)
                i = text.index(lead)
                self.assertIn(LINK, text[i:i + 400])

    def test_the_framing_site_is_in_the_framing_block(self):
        text = squash(body())
        site = text.index("How many records to GENERATE is not one of")
        self.assertLess(text.index("## License limit and dataset size (canonical framing)"), site)
        self.assertLess(site, text.index("## Workflow"))

    def test_the_chain_is_stated_once(self):
        self.assertEqual(squash(body()).count("INV-277's default of about 10,000 records"), 1)


if __name__ == "__main__":
    unittest.main()
