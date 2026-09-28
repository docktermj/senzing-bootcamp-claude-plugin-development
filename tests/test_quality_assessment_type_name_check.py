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
* **The handoff to Phase 2**: step 13 applies the rule, step 18 keeps the section. Without it the
  decision is made in Phase 1 and nothing carries it to the transform.
* **Zero is reported**: Step 7 records the count for every source, zero included.

The suffix list and the documented edge cases are also run against each other: the list is parsed
from the file and applied, as written, to the names the file uses as examples.

Negative controls run inside the suite: each check is applied to a copy of the text with its
rule removed and must report a problem.

Source issue: #158.

Run:  python3 -m unittest discover -s tests
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
    sub5 = between(flat, "5. If structurally loadable AND fully mapped", "👉 Your CORD source") or ""
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
    ):
        if not re.search(pattern, flat):
            out.append("the check does not state: " + claim)
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


def problems_in_phase2(text):
    flat = squash(text)
    out = []
    s13 = between(flat, "### 13. Build the transformation program", "### 14. Test") or ""
    if not re.search(r"Apply a retype decision from Phase 1", s13):
        out.append("Phase 2 step 13 does not apply the Phase 1 retype decision")
    if "RECORD_TYPE` `ORGANIZATION`" not in s13:
        out.append("Phase 2 step 13 does not say what the retype emits")
    if not re.search(r"do not restate them here \(INV-300\)", s13):
        out.append("Phase 2 step 13 does not point at the canonical statement")
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

    def test_dropping_the_phase_2_handoff_fails(self):
        text = PHASE2.read_text(encoding="utf-8")
        mutant = text.replace("**Apply a retype decision from Phase 1.**", "")
        self.assertNotEqual(mutant, text)
        self.assertTrue(problems_in_phase2(mutant))


if __name__ == "__main__":
    unittest.main()
