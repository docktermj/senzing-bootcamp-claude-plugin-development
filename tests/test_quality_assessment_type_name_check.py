"""Module 5 finds PERSON-typed records named like organizations, before mapping.

The Entity Specification says `RECORD_TYPE` "prevents records of different types from
resolving". A CORD ICIJ download typed its `NODE_TYPE: OFFICER` records `PERSON` regardless of
name: 26 of 31 PERSON-typed records in one sample ended `LLP`, `LP`, `PLC` or `LIMITED`, and that
one conflict held apart 17 of 50 cross-source possible-match pairs. Every per-type guard in
the quality assessment trusted the type, so nothing saw it until Query, Visualize and Discover
explained a near-miss (2026-09-25).

What this pins:

* **The check, stated once** in Step 6 (INV-300): PERSON-typed records, the name's final whole
  token, case-insensitive, trailing punctuation removed, against a list that includes the four
  observed suffixes and is labeled at its site as the plugin's own heuristic (INV-080).
* **The Step 5a gate**: the check runs after the coverage check and before the fast-path offer,
  one or more candidates means no offer, and the routing statement names the count. A CORD source
  otherwise skips the step where the retype is applied (INV-198).
* **The report and the decision**: count out of the PERSON-typed total, sample names, called
  candidates; retype or keep, with the rule or the cost, written to the source's mapper notes.
* **The handoff to Phase 2**: steps 10 and 11 read the section before they advance workflow
  steps 2 and 3, step 13 applies the rule in the transform, and step 18 keeps the section.
  Without it the decision is made in Phase 1 and nothing carries it to the mapping. Until #220
  only step 13 read it, two module steps after workflow step 3 had declared the names, so the
  retype never reached the mapping (#220). On Retype, step 11 declares the name once with a
  computed `derived` `RECORD_TYPE` (`source` and `justification`) and gives no
  `type_discriminator.field_overrides` instruction; step 13 describes no step 3 rejection. The
  Phase 2 checks look for structure (the section name, the `derived` keys, the INV-300
  pointer) and pin no server wording (INV-219).
* **Zero is reported**: Step 7 records the count for every source, zero included.
* **The retyped name and its citations agree with INV-336** (#283): the template maps a retyped
  name as `NAME_ORG` only and says how the value is built; the retype sites in Phase 2 cite
  INV-336, not INV-136 (which governs required parameters and enumerated values); a joined
  `NAME_ORG` is the value the verbatim check flags, not the exempt `RECORD_TYPE`; and step 10
  takes only the enum-valid `record_type` half of the mixed-type rule.

The suffix list and the documented edge cases are also run against each other: the list is parsed
from the file and applied, as written, to the names the file uses as examples.

Negative controls run inside the suite: each check is applied to a copy of the text with its
rule removed and must report a problem.

Enforces **INV-343** (Phase 2 emits no `type_discriminator` by default, only for step 3's NAME_ORG
rejection): it asserts that step 10 states the rule and does not cite INV-136 for it, and does **not**
establish that a live run follows it.

Source issues: #158, #220, #283.

Run:  python3 -m unittest discover -s tests

INV-335 (the Phase 1 type/name check, its fast-path gate and the recorded decision) and INV-336 (Phase 2
reads that decision before workflow steps 2 and 3) are the invariants this module enforces. It pins
the text; it cannot establish that a live run performs the check or reads the decision in time.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping")
PHASE1 = MODULE / "phase1-quality-assessment.md"
PHASE2 = MODULE / "phase2-data-mapping.md"

REQUIRED_SUFFIXES = ("LLP", "LP", "PLC", "LIMITED")


def squash(value):
    return re.sub(r"\s+", " ", value.replace("**", ""))


def between(text, start, end):
    """The text from `start` up to `end`, or None if either marker is missing."""
    i = text.find(start)
    if i < 0:
        return None
    j = text.find(end, i + len(start))
    return text[i:j] if j >= 0 else None


def step5a(text):
    return between(text, "## 5a. Senzing-readiness check", "## 6. Assess data quality")


def step6(text):
    return between(text, "## 6. Assess data quality", "## 7. Summarize findings")


def step7(text):
    return between(text, "## 7. Summarize findings", "### Quality gate")


def the_check(text):
    """Step 6's canonical block, from its heading to the step's checkpoint."""
    block = step6(text)
    if block is None:
        return None
    return between(block, "### Type/name check", "**Checkpoint:** write step 6.")


def suffix_list(check):
    """The suffix list: the one line in the check made only of backticked upper-case tokens."""
    for line in check.splitlines():
        tokens = re.findall(r"`([^`]+)`", line)
        rest = re.sub(r"`[^`]+`", "", line).replace(",", "").strip()
        if len(tokens) >= 4 and not rest and all(re.fullmatch(r"[A-Z]+", t) for t in tokens):
            return tokens
    return []


def is_candidate(name, suffixes):
    """The documented test, applied as written: final whole token, trailing punctuation off."""
    tokens = name.split()
    if not tokens:
        return False
    final = re.sub(r"[^\w]+$", "", tokens[-1]).upper()
    return final in {s.upper() for s in suffixes}


# --- the checks, each returning its problems so a negative control can run it on a mutant ---

def problems_in_the_check(text):
    check = the_check(text)
    if check is None:
        return ["Step 6 has no 'Type/name check' block"]
    flat = squash(check)
    out = []
    for claim, pattern in (
        ("canonical statement, cited", r"canonical statement of the type/name check"),
        ("INV-300 at the canonical claim", r"\(INV-300\) This is the canonical statement"),
        ("PERSON-typed records are tested", r"RECORD_TYPE` is `PERSON`"),
        ("final whole token", r"final whole token"),
        ("trailing punctuation removed", r"trailing punctuation removed"),
        ("case-insensitive", r"case-insensitive"),
        ("every record, not a sample", r"every record of each source, not a sample"),
        ("all three name forms", r"`NAME_FULL`, `NAME_ORG`, or the parsed person fields"),
    ):
        if not re.search(pattern, flat):
            out.append("the check does not state: " + claim)
    suffixes = suffix_list(check)
    if not suffixes:
        out.append("the check carries no suffix list")
    for s in REQUIRED_SUFFIXES:
        if s not in suffixes:
            out.append("the suffix list lacks " + s)
    return out


def problems_in_the_label(text):
    """The heuristic label must sit at the list, not somewhere else in the step."""
    check = the_check(text) or ""
    suffixes = suffix_list(check)
    if not suffixes:
        return ["no suffix list to label"]
    at = check.find("`" + "`, `".join(suffixes) + "`")
    near = squash(check[max(0, at - 200):at + 900])
    out = []
    if not re.search(r"plugin's own heuristic, not a Senzing fact \(INV-080\)", near):
        out.append("the suffix list is not labeled at its site as the plugin's own heuristic")
    if "No MCP route serves one" not in near:
        out.append("the label does not say why the plugin writes the list itself")
    return out


def problems_in_the_5a_gate(text):
    block = step5a(text)
    if block is None:
        return ["step 5a's boundaries moved"]
    flat = squash(block)
    out = []
    gate = flat.find("Perform the type/name check")
    coverage = flat.find("Perform the coverage check")
    offer = flat.find("👉 Your CORD source")
    if gate < 0:
        return ["step 5a does not run the type/name check"]
    if not coverage < gate < offer:
        out.append("the type/name check must run after the coverage check and before the offer")
    if "Step 6's type/name check" not in flat[gate:gate + 400]:
        out.append("step 5a restates the check instead of pointing at Step 6")
    if not re.search(r"One or more candidates means no fast-path offer", flat):
        out.append("step 5a does not withhold the offer on one or more candidates")
    if not re.search(r"\(INV-198\) One or more candidates", flat):
        out.append("the no-fast-path rule does not cite INV-198 at its line")
    sub5 = between(flat, "5. If structurally loadable, fully mapped AND free of type/name candidates",
                   "👉 Your CORD source") or ""
    if not re.search(r"zero type/name candidates", sub5):
        out.append("the offer (sub-step 5) is not gated on zero candidates")
    sub6 = between(flat, "6. If structurally loadable but NOT fully mapped", "7. If NOT") or ""
    if not re.search(r"sub-step 3a held back", sub6):
        out.append("the routing statement (sub-step 6) does not take a held-back source")
    if not re.search(r"\[N\] of its \[M\] PERSON-typed records", sub6):
        out.append("the routing statement does not name the candidate count")
    return out


def problems_in_the_report_and_decision(text):
    flat = squash(the_check(text) or "")
    out = []
    for claim, pattern in (
        ("count out of the PERSON-typed total", r"\[N\] of \[M\] PERSON-typed records"),
        ("sample candidate names", r"up to ten candidate names"),
        ("called candidates, not errors", r"candidates from a suffix test, not confirmed errors"),
        ("zero is reported and nothing asked", r"report the zero and ask nothing"),
        ("a pinned question", r"👉 How should the mapping type the \[N\] candidate records"),
        ("option: retype", r"1\. Retype them to ORGANIZATION"),
        ("option: keep", r"2\. Keep them as PERSON"),
        ("retype takes exceptions", r"except any you name as a real person"),
        ("written to the mapper notes", r"docs/mapping/\{source_name\}_mapper\.md"),
        ("the section heading", r"## Record Type Check"),
        ("the retype rule", r"Rule \(retype\):"),
        ("the keep cost", r"Cost \(keep\): these \[N\] records stay `PERSON`, so they cannot merge"),
        ("retyped names are not parsed person fields", r"never as parsed person fields"),
        ("non-blocking", r"\(INV-048\) The check reports and asks; it never blocks"),
        ("never undo the retype for a gate", r"\(INV-173\) Never undo the Bootcamper's retype"),
        ("a retyped name is NAME_ORG only", r"mapped as `NAME_ORG` only"),
        ("a retyped name is never NAME_FULL", r"never as `NAME_FULL`"),
        ("how the retyped NAME_ORG is built",
         r"single name field's value as-is, or the parsed person fields joined with single spaces"),
        ("the verbatim check flags a joined NAME_ORG",
         r"verbatim check flags a retyped record's `NAME_ORG` joined from parsed name fields"),
    ):
        if not re.search(pattern, flat):
            out.append("the check does not state: " + claim)
    if re.search(r"`NAME_ORG` or `NAME_FULL`", flat):
        out.append("the retype rule offers NAME_FULL for a retyped name (INV-336: NAME_ORG only)")
    if re.search(r"flags a retyped `RECORD_TYPE` value", flat):
        out.append("the INV-173 note names RECORD_TYPE, which the verbatim check exempts")
    return out


def problems_in_step7(text):
    block = step7(text)
    if block is None:
        return ["step 7's boundaries moved"]
    flat = squash(block)
    out = []
    if not re.search(r"Record type check: \[N\] of \[M\] PERSON-typed records", flat):
        out.append("the step 7 template has no per-source record type check line")
    if not re.search(r"for every source, zero included", flat):
        out.append("step 7 does not require the line for every source, zero included")
    if not re.search(r"Retype / Keep as-is / none needed", flat):
        out.append("the step 7 line does not record the decision")
    return out


def plan_and_map_steps(flat):
    """Module steps 10 (Plan) and 11 (Map), each up to the next step heading."""
    s10 = between(flat, "### 10. Plan", "### 11. Map") or ""
    s11 = between(flat, "### 11. Map", "### 12. Generate starter code") or ""
    return s10, s11


def retype_block(s11):
    """Step 11's Record Type Check handling, up to the unconditional-advance paragraph."""
    return between(s11, "Read the source's Record Type Check before you advance workflow step 3",
                   "This advance is unconditional") or ""


def sentences(text):
    return [s for s in re.split(r"(?<=[.:;])\s+", text) if s.strip()]


def problems_in_phase2_plan_and_map(text):
    """Steps 10 and 11 carry the retype into the plan and the mapping (#220)."""
    flat = squash(text)
    s10, s11 = plan_and_map_steps(flat)
    out = []
    for name, step, advance in (("step 10", s10, "workflow step 2"),
                                ("step 11", s11, "workflow step 3")):
        read = re.search(r"Read the source's Record Type Check before you advance " + advance, step)
        if not read:
            out.append("Phase 2 %s does not read the Record Type Check before %s" % (name, advance))
            continue
        after = step[read.start():read.start() + 700]
        if "## Record Type Check" not in after:
            out.append("Phase 2 %s does not name the `## Record Type Check` section" % name)
        if not re.search(r"Phase 1 Step 6's \"Type/name check\"", after):
            out.append("Phase 2 %s does not name Phase 1 Step 6 as the canonical statement" % name)
        if "INV-300" not in step[read.start() - 20:read.start() + 700]:
            out.append("Phase 2 %s does not cite INV-300 at its pointer" % name)
    for name, step in (("step 10", s10), ("step 11", s11)):
        for token in ("`LLP`", "`GMBH`", "final whole token"):
            if token in step:
                out.append("Phase 2 %s restates the rule (%s) instead of pointing at it" %
                           (name, token))
    if s10 and not re.search(r"predominant type after the retype", s10):
        out.append("step 10 does not send the predominant post-retype record_type")
    if s10 and not re.search(r"never `MIXED`", s10):
        out.append("step 10 does not rule out MIXED for a retyped source")
    if s10 and not re.search(r"now carries PERSON and ORGANIZATION records", s10):
        out.append("step 10's plan summary does not say the source is now mixed-type")
    block = retype_block(s11)
    if not block:
        out.append("step 11 has no Retype block before its advance")
        return out
    for key in ('"disposition": "derived"', '"derived_as": "RECORD_TYPE"', '"source"',
                '"justification"'):
        if key not in block:
            out.append("step 11's computed RECORD_TYPE does not carry %s" % key)
    if not re.search(r"declare the name once", block, re.IGNORECASE):
        out.append("step 11 does not declare the name once on Retype")
    if not re.search(r"no `NAME_ORG` entry and no `type_discriminator`", block):
        out.append("step 11 does not rule out a NAME_ORG entry and a type_discriminator")
    if not re.search(r"Parsed person name fields.*`NAME_ORG` for a retyped.*parsed parts for a "
                     r"PERSON record, branched on `RECORD_TYPE`", block):
        out.append("step 11 does not branch the parsed-name case on RECORD_TYPE")
    if not re.search(r"One name field.*once as `NAME_FULL`.*`NAME_ORG` for a retyped.*`NAME_FULL` "
                     r"for a PERSON record, branched on `RECORD_TYPE`", block):
        out.append("step 11 does not branch the single-name case on RECORD_TYPE")
    if not re.search(r"server \d+\.\d+\.\d+, \d{4}-\d{2}-\d{2}", block):
        out.append("step 11's declaration carries no server version and date")
    if "NAME_ORG cannot co-exist" not in block:
        out.append("step 11 does not name the NAME_ORG rejection by its message")
    for sentence in sentences(block):
        if "field_overrides" in sentence and not re.search(r"\bnot\b|\bno\b", sentence):
            out.append("step 11's Retype block routes the reader to field_overrides: " +
                       sentence[:80])
    return out


def order_problems(text):
    """The section is read before workflow step 3 is advanced (#220).

    Step 10's read precedes step 11, and step 11's read precedes step 11's advance paragraph
    and step 13's transform.
    """
    flat = squash(text)
    out = []
    read10 = flat.find("Read the source's Record Type Check before you advance workflow step 2")
    read11 = flat.find("Read the source's Record Type Check before you advance workflow step 3")
    map11 = flat.find("### 11. Map")
    advance11 = flat.find("This advance is unconditional", map11)
    s13 = flat.find("### 13. Build the transformation program")
    if min(read10, read11, map11, advance11, s13) < 0:
        return ["a marker of the Phase 2 read order is missing"]
    if not read10 < map11:
        out.append("step 10's read is not inside step 10")
    if not map11 < read11 < advance11 < s13:
        out.append("step 11 does not read the section before its advance")
    return out


def problems_in_the_name_citations(text):
    """Each retype and name-declaration rule cites the invariant that governs it (#283).

    INV-136 governs a tool's required parameters and enumerated values. None of these rules
    states either, so none of them cites it.
    """
    flat = squash(text)
    s10, s11 = plan_and_map_steps(flat)
    out = []
    if "(INV-300, INV-336) Read the source's Record Type Check before you advance workflow step 3" \
            not in s11:
        out.append("step 11's Record Type Check read does not cite (INV-300, INV-336)")
    if "no `NAME_ORG` entry and no `type_discriminator` (INV-336)" not in s11:
        out.append("step 11's no-NAME_ORG, no-type_discriminator rule does not cite INV-336")
    if "INV-136" in retype_block(s11):
        out.append("step 11's Retype block cites INV-136")
    rejection = re.search(r"\(([^()]*)\) Step 3 rejects a source that declares BOTH", s10)
    if not rejection:
        out.append("step 10's NAME_ORG rejection block has no citation")
    else:
        if "INV-136" in rejection.group(1):
            out.append("step 10's NAME_ORG rejection block cites INV-136")
        if "INV-125" not in rejection.group(1):
            out.append("step 10's NAME_ORG rejection block does not cite INV-125")
    at = s10.find("Do not pre-emptively emit a `type_discriminator` on every source")
    if at < 0:
        out.append("step 10 no longer says not to emit a type_discriminator pre-emptively")
    elif "INV-136" in s10[max(0, at - 20):at]:
        out.append("the pre-emptive type_discriminator rule cites INV-136")
    retype10 = between(s10, "With Retype, the source now carries both types",
                       "Declare nothing else here") or ""
    if "per the mixed-type rule below" in retype10:
        out.append("step 10 defers to the whole mixed-type rule, type_discriminator included")
    if not re.search(r"enum-valid `record_type` half of the mixed-type rule", retype10):
        out.append("step 10 does not take only the mixed-type rule's enum-valid record_type half")
    if not re.search(r"`type_discriminator`, does not apply to a suffix retype; step 11", retype10):
        out.append("step 10 does not rule out the type_discriminator half and name step 11")
    what_to_do = between(flat, "What to do — in this order:", "Four further limitations") or ""
    if not re.search(r"or a `NAME_ORG` joined from parsed name fields", what_to_do):
        out.append("the exemption procedure does not name a joined NAME_ORG as a reason")
    return out


def problems_in_phase2(text):
    flat = squash(text)
    out = problems_in_phase2_plan_and_map(text) + order_problems(text)
    s13 = between(flat, "### 13. Build the transformation program", "### 14. Test") or ""
    if not re.search(r"Apply a retype decision from Phase 1", s13):
        out.append("Phase 2 step 13 does not apply the Phase 1 retype decision")
    if "RECORD_TYPE` `ORGANIZATION`" not in s13:
        out.append("Phase 2 step 13 does not say what the retype emits")
    if not re.search(r"do not restate them here \(INV-300\)", s13):
        out.append("Phase 2 step 13 does not point at the canonical statement")
    if re.search(r"(?i)step 3 rejects|step-10 rejection|rejects its name declarations", s13):
        out.append("Phase 2 step 13 still describes a workflow step 3 rejection")
    if not re.search(r"parsed fields joined in the order Phase 1 Step 6 reads them", s13):
        out.append("Phase 2 step 13 does not say how a retyped parsed name is joined")
    s18 = between(flat, "### 18. Save and document", "### 18a.") or ""
    if "## Record Type Check" not in s18:
        out.append("the step 18 mapper template has no Record Type Check section")
    if not re.search(r"Keep the `## Record Type Check` section Phase 1 wrote", s18):
        out.append("step 18 does not keep the section Phase 1 wrote")
    return out


class TheCheckIsSpecifiedOnceInStep6(unittest.TestCase):
    def test_it_is_specified(self):
        self.assertEqual([], problems_in_the_check(PHASE1.read_text(encoding="utf-8")))

    def test_the_list_is_labeled_as_the_plugins_own_heuristic(self):
        self.assertEqual([], problems_in_the_label(PHASE1.read_text(encoding="utf-8")))


class TheListAndTheExamplesAgree(unittest.TestCase):
    """The documented list, applied as documented, to the names the file itself uses."""

    def setUp(self):
        self.suffixes = suffix_list(the_check(PHASE1.read_text(encoding="utf-8")) or "")

    def test_the_observed_suffixes_are_candidates(self):
        for name in ("SMITH & JONES LLP", "Harbor Partners LP", "acme holdings plc",
                     "Northwind Trading Limited."):
            with self.subTest(name=name):
                self.assertTrue(is_candidate(name, self.suffixes))

    def test_the_documented_non_candidates_are_not(self):
        flat = squash(the_check(PHASE1.read_text(encoding="utf-8")) or "")
        for name in ("LIMITED EDITIONS SMITH", "PHILIP"):
            with self.subTest(name=name):
                self.assertIn("`%s`" % name, flat, "the edge case is no longer documented")
                self.assertFalse(is_candidate(name, self.suffixes))


class TheFastPathIsWithheldOnCandidates(unittest.TestCase):
    def test_step_5a_gates_the_offer(self):
        self.assertEqual([], problems_in_the_5a_gate(PHASE1.read_text(encoding="utf-8")))


class TheBootcamperDecidesAndTheDecisionIsKept(unittest.TestCase):
    def test_the_report_and_the_two_options(self):
        self.assertEqual([], problems_in_the_report_and_decision(
            PHASE1.read_text(encoding="utf-8")))

    def test_step_7_records_every_count_including_zero(self):
        self.assertEqual([], problems_in_step7(PHASE1.read_text(encoding="utf-8")))

    def test_phase_2_applies_and_keeps_the_decision(self):
        self.assertEqual([], problems_in_phase2(PHASE2.read_text(encoding="utf-8")))

    def test_the_retype_rules_cite_the_invariant_that_governs_them(self):
        self.assertEqual([], problems_in_the_name_citations(PHASE2.read_text(encoding="utf-8")))


class NegativeControls(unittest.TestCase):
    """Each check must fail on a copy of the text with its rule taken out."""

    def setUp(self):
        self.text = PHASE1.read_text(encoding="utf-8")

    def test_removing_the_step_5a_gate_fails(self):
        start = self.text.index("3a. **Perform the type/name check")
        end = self.text.index("4. **Record the result:**")
        mutant = self.text[:start] + self.text[end:]
        self.assertTrue(problems_in_the_5a_gate(mutant))

    def test_ungating_the_offer_fails(self):
        mutant = self.text.replace("when sub-step 3a also found **zero** type/name candidates",
                                   "when sub-step 3a has run")
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(problems_in_the_5a_gate(mutant))

    def test_dropping_a_required_suffix_fails(self):
        mutant = self.text.replace("`LLP`, `LP`, `PLC`, `LIMITED`, ", "`LLP`, `PLC`, `LIMITED`, ")
        self.assertNotEqual(mutant, self.text)
        self.assertIn("the suffix list lacks LP", problems_in_the_check(mutant))

    def test_removing_the_heuristic_label_fails(self):
        mutant = self.text.replace("plugin's own heuristic, not a Senzing fact", "suffix list")
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(problems_in_the_label(mutant))

    def test_removing_the_keep_option_fails(self):
        mutant = self.text.replace("2. Keep them as PERSON.", "")
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(problems_in_the_report_and_decision(mutant))

    def test_dropping_the_zero_count_fails(self):
        mutant = self.text.replace("for every source, zero included", "for each source")
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(problems_in_step7(mutant))

    def test_offering_name_full_for_a_retyped_name_fails(self):
        old = "mapped as `NAME_ORG` only, never as parsed"
        mutant = self.text.replace(old, "mapped as `NAME_ORG` or `NAME_FULL`, never as parsed")
        self.assertNotEqual(mutant, self.text)
        self.assertIn("the retype rule offers NAME_FULL for a retyped name (INV-336: NAME_ORG only)",
                      problems_in_the_report_and_decision(mutant))

    def test_dropping_how_the_retyped_name_is_built_fails(self):
        mutant = self.text.replace("joined with single spaces", "joined")
        self.assertNotEqual(mutant, self.text)
        self.assertIn("the check does not state: how the retyped NAME_ORG is built",
                      problems_in_the_report_and_decision(mutant))

    def test_the_inv_173_note_naming_record_type_fails(self):
        mutant = self.text.replace(
            "flags a retyped record's `NAME_ORG` joined from parsed name fields,",
            "flags a retyped `RECORD_TYPE` value,")
        self.assertNotEqual(mutant, self.text)
        self.assertIn("the INV-173 note names RECORD_TYPE, which the verbatim check exempts",
                      problems_in_the_report_and_decision(mutant))

    def test_dropping_the_phase_2_handoff_fails(self):
        text = PHASE2.read_text(encoding="utf-8")
        mutant = text.replace("**Apply a retype decision from Phase 1.**", "")
        self.assertNotEqual(mutant, text)
        self.assertTrue(problems_in_phase2(mutant))


class Phase2NegativeControls(unittest.TestCase):
    """Each #220 check must fail on a copy of phase2-data-mapping.md with its rule taken out."""

    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")

    def mutate(self, old, new=""):
        mutant = self.text.replace(old, new)
        self.assertNotEqual(mutant, self.text, "the control's target text moved: %r" % old)
        return mutant

    def test_step_10_not_reading_the_section_fails(self):
        mutant = self.mutate("Read the source's Record Type Check before you advance workflow step 2",
                             "Consider the plan")
        self.assertTrue(problems_in_phase2(mutant))

    def test_step_11_not_reading_the_section_fails(self):
        mutant = self.mutate("Read the source's Record Type Check before you advance workflow step 3",
                             "Consider the mapping")
        self.assertTrue(problems_in_phase2(mutant))

    def test_step_11_without_the_inv_300_pointer_fails(self):
        mutant = self.mutate("(INV-300, INV-336) Read the source's Record Type Check",
                             "(INV-336) Read the source's Record Type Check")
        self.assertIn("Phase 2 step 11 does not cite INV-300 at its pointer",
                      problems_in_phase2(mutant))

    def test_step_10_mixed_record_type_fails(self):
        mutant = self.mutate("It\n  stays enum-valid and is never `MIXED`", "It is `MIXED`")
        self.assertTrue(problems_in_phase2_plan_and_map(mutant))

    def test_the_derived_record_type_without_justification_fails(self):
        mutant = self.mutate(' "justification": "<the Phase 1 rule and its exceptions>"}', "}")
        self.assertIn('step 11\'s computed RECORD_TYPE does not carry "justification"',
                      problems_in_phase2(mutant))

    def test_a_field_overrides_instruction_in_step_11_fails(self):
        mutant = self.mutate("computed `RECORD_TYPE`. Declare no `NAME_ORG` entry",
                             "computed `RECORD_TYPE`. Declare the names through "
                             "`type_discriminator.field_overrides`. Declare no `NAME_ORG` entry")
        self.assertTrue(any("routes the reader to field_overrides" in p
                            for p in problems_in_phase2(mutant)))

    def test_restating_the_suffix_list_in_step_11_fails(self):
        mutant = self.mutate("Declare no `NAME_ORG` entry",
                             "The suffixes are `LLP` and `GMBH`. Declare no `NAME_ORG` entry")
        self.assertTrue(any("restates the rule" in p for p in problems_in_phase2(mutant)))

    def test_moving_the_step_11_read_after_the_advance_fails(self):
        start = self.text.index("⛔ **(INV-300, INV-336) Read the source's Record Type Check")
        end = self.text.index("⚠️ **This advance is unconditional")
        block = self.text[start:end]
        rest = self.text[:start] + self.text[end:]
        at = rest.index("### 12. Generate starter code")
        mutant = rest[:at] + block + rest[at:]
        self.assertTrue(order_problems(mutant))

    def test_restoring_the_step_13_rejection_sentence_fails(self):
        mutant = self.mutate("With **Keep as-is**, or no such section, change nothing.",
                             "If `mapping_workflow` step 3 rejects its name declarations, that is "
                             "the step-10 rejection above. With **Keep as-is**, or no such "
                             "section, change nothing.")
        self.assertIn("Phase 2 step 13 still describes a workflow step 3 rejection",
                      problems_in_phase2(mutant))

    def test_citing_inv_136_at_the_step_11_read_fails(self):
        mutant = self.mutate("(INV-300, INV-336) Read the source's Record Type Check",
                             "(INV-300, INV-136) Read the source's Record Type Check")
        self.assertIn("step 11's Record Type Check read does not cite (INV-300, INV-336)",
                      problems_in_the_name_citations(mutant))

    def test_citing_inv_136_at_the_declare_once_rule_fails(self):
        mutant = self.mutate("no `type_discriminator` (INV-336):", "no `type_discriminator` (INV-136):")
        problems = problems_in_the_name_citations(mutant)
        self.assertIn("step 11's no-NAME_ORG, no-type_discriminator rule does not cite INV-336",
                      problems)
        self.assertIn("step 11's Retype block cites INV-136", problems)

    def test_citing_inv_136_at_the_rejection_block_fails(self):
        mutant = self.mutate("(INV-125) Step 3 rejects a source",
                             "(INV-136, INV-125) Step 3 rejects a source")
        self.assertIn("step 10's NAME_ORG rejection block cites INV-136",
                      problems_in_the_name_citations(mutant))

    def test_citing_inv_136_at_the_pre_emptive_rule_fails(self):
        mutant = self.mutate("**(INV-343) Do not pre-emptively emit a `type_discriminator`",
                             "**(INV-136) Do not pre-emptively emit a `type_discriminator`")
        self.assertIn("the pre-emptive type_discriminator rule cites INV-136",
                      problems_in_the_name_citations(mutant))

    def test_step_10_deferring_to_the_whole_mixed_type_rule_fails(self):
        start = self.text.index("never `MIXED`: that is the enum-valid")
        end = self.text.index("step 11 declares how each record is typed.", start)
        end += len("step 11 declares how each record is typed.")
        mutant = self.text[:start] + "never `MIXED`, per the mixed-type rule below." + \
            self.text[end:]
        problems = problems_in_the_name_citations(mutant)
        self.assertIn("step 10 defers to the whole mixed-type rule, type_discriminator included",
                      problems)
        self.assertIn("step 10 does not rule out the type_discriminator half and name step 11",
                      problems)

    def test_dropping_the_joined_name_org_reason_fails(self):
        mutant = self.mutate(
            ", or a\n   `NAME_ORG` joined from parsed name fields, which equals no single source value)",
            ")")
        self.assertIn("the exemption procedure does not name a joined NAME_ORG as a reason",
                      problems_in_the_name_citations(mutant))

    def test_dropping_the_joined_name_order_fails(self):
        mutant = self.mutate("parsed fields joined in the order Phase 1 Step 6 reads them",
                             "parsed fields")
        self.assertTrue(problems_in_phase2(mutant))


if __name__ == "__main__":
    unittest.main()
