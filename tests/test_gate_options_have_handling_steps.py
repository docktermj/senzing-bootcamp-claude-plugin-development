"""A gate option that proposes work must have a step that does the work.

Both Module 5 quality gates offered *"improve the data first"* and **no step in the plugin
defined what the guide does when it is chosen** — no procedure, no loop-back, no re-score,
no re-entry point. The file went from the pinned question straight to *"Success indicator"*
and Phase 1 ended. Hit live on 2026-08-28: CRM_EXPORT scored **75.1**, the gate was
presented as pinned, the maintainer answered **1**, and there was nothing to execute.

⛔ **This is the unsatisfiable-instruction shape, on the ANSWER side.** INV-056 pins every
gate question's wording and INV-247 requires every 👉 to trace to a step in a shipped skill
file — both govern the *ask*. Nothing governed what happens on the *answer*, so a guide
facing a chosen option with no procedure must improvise, and improvising against a pinned
gate teaches that the surrounding ⛔ rules are advisory.

⚠️ **The spec named two gates; the scan found five options across two files.** Phase 2's
three iterate options were never mentioned in the finding and are covered here too — they
were already discharged by `### 17. Iterate`, which is exactly why the guard derives its
site set instead of hardcoding the two lines the spec listed (INV-246).

The check is deliberately narrow and positive: an option proposing REMEDIATION must have a
handling section whose heading names that action. Options that propose *proceeding* need no
step — the module flow is their handler.

Enforces **INV-284** — every option a pinned gate offers has a handling step (a section in the
same skill file, or an inline branch at the gate) saying what the guide does when it is chosen and
where the flow resumes; and where that step changes the state the gate measured, re-presenting the
gate is not an INV-006 repeat.

Also enforces **INV-345** (on a `provenance: synthesized` source, disclose the deliberate gaps
before the gate's 👉, and never regenerate the Bootcamper's data silently):
`test_a_synthesized_source_is_disclosed_before_the_question` and
`test_it_forbids_silent_regeneration`. They assert that the skill file *states* both rules, and do
**not** establish that a live turn discloses before it asks or never regenerates silently, which
only `dry-run` phase 3 can observe.

#521 extends the disclosure to Phase 2 step 16's quality gate (INV-345's 2026-10-12 note, queued for
the maintainer's sign-off): `Step16DisclosesOnASynthesizedSource` asserts that step 16 points at
Phase 1's one statement of the wording (INV-300) before the 70-79% and <70% questions of both
blocks, keeps those questions verbatim with both options, and marks no ≥80% question.

Source spec:
`specs/the-quality-gates-improve-option-has-no-procedure-and-is-incoherent-on-a-generated-scenario.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping")

#: A numbered option inside a gate's option list.
#: ⛔ Scoped to lists that FOLLOW a 👉, not to every numbered line in the module. A first
#: version matched any `1.` and flagged two things that are not gate options at all: an
#: instruction step in `SKILL.md` (matched on the word "fix") and one of the improve
#: path's own numbered steps (matched on "improved"). A guard that reports correct prose
#: is one that gets relaxed.
OPTION = re.compile(r"^\s*>?\s*(\d)\.\s+(.*\S)\s*$")
POINTER = "👉"
#: The remediation verbs a gate option offers in this corpus, matched on the option's
#: LEADING verb — the action it proposes — not on any occurrence. "Iterate to improve the
#: data" proposes *iterating*; improving is what iterating is for, and requiring an
#: "improve" section for it sends an editor to write a second handler for a step that
#: already exists. Each maps to the word its handling section's heading must contain, so
#: the guard checks the claim rather than a list of sentences already seen (INV-282).
REMEDIATION = (
    (r"\biterat", "iterate"),
    (r"\bimprov|\bwork on\b", "improve"),
)
#: The second, equally legitimate way an option is handled: an inline branch right below
#: the gate that says what happens and where it goes. Phase 3 does this ("If rejected:
#: … return to Phase 2 to adjust their mapping"), and requiring a heading there would flag
#: a gate that is correctly handled — which is how a guard gets relaxed.
INLINE_HANDLER = re.compile(
    r"\*\*If (?:accepted|rejected|they|the)\b|return to Phase|go back to|"
    r"\bre-enter\b|see \u00a7", re.I)
#: How far below an option an inline handler may sit. Sized from the real gates: phase 3's
#: sits ~200 chars below, phase 2's routing lands within its next section.
INLINE_WINDOW = 1500


def gate_files():
    """Every module file carrying a 👉 gate — derived, not listed (INV-246)."""
    return sorted(p for p in MODULE.glob("*.md")
                  if "👉" in p.read_text(encoding="utf-8"))


def headings(text):
    return [m.group(1).lower() for m in re.finditer(r"^#{2,4}\s+(.*)$", text, re.M)]


def gate_options(text):
    """(option_text, end_offset) for every numbered option belonging to a 👉 question.

    Line-scoped by design (#424): an option opens on its own numbered line, and what is
    matched is its LEADING verb, which sits on that line however the option wraps.
    """
    options = []
    offset = 0
    in_list = False
    seen_one = False
    for line in text.split("\n"):
        start = offset
        offset += len(line) + 1
        if POINTER in line:
            in_list, seen_one = True, False
            continue
        if not in_list:
            continue
        if not line.strip():
            continue                      # a blank line inside the list is fine
        match = OPTION.match(line)
        if match:
            options.append((match.group(2), start + len(line)))
            seen_one = True
        elif seen_one or not line.lstrip().startswith(">"):
            in_list = False               # the list ended
    return options


def remediation_options(text):
    """(option_text, required_word, end_offset) for every gate option proposing work."""
    found = []
    for option, end in gate_options(text):
        for pattern, word in REMEDIATION:
            if re.search(pattern, option, re.I):
                found.append((option, word, end))
                break
    return found


def is_handled(text, word, end_offset):
    """A heading naming the action, or an inline branch routing it — either discharges."""
    if any(word in head for head in headings(text)):
        return True
    return bool(INLINE_HANDLER.search(text[end_offset:end_offset + INLINE_WINDOW]))


class EveryRemediationOptionHasAHandlingStep(unittest.TestCase):
    def test_the_scan_finds_the_options(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        total = sum(len(remediation_options(p.read_text(encoding="utf-8")))
                    for p in gate_files())
        self.assertGreaterEqual(
            total, 4,
            "fewer remediation options were found than this module is known to offer; the "
            f"scan broke or the gates moved. Found {total}")

    def test_each_one_has_a_section_that_handles_it(self):
        bad = []
        for path in gate_files():
            text = path.read_text(encoding="utf-8")
            for option, word, end in remediation_options(text):
                if not is_handled(text, word, end):
                    bad.append(f"{path.name}: {option!r} needs a '{word}' section or an "
                               "inline branch saying what happens")
        self.assertEqual(
            [], bad,
            "a pinned gate offers to do work and no section in the same file says what "
            "that work is. The turn then ends on the question with nothing to run:\n  "
            + "\n  ".join(bad))


class TheImprovePathIsUsable(unittest.TestCase):
    """The three properties the improve path has to have to be executable at all."""

    def setUp(self):
        self.text = (MODULE / "phase1-quality-assessment.md").read_text(encoding="utf-8")
        start = self.text.index("### 7a.")
        end = self.text.index("**Success indicator:**", start)
        #: The improve path alone. Scoped, because the fields below appear elsewhere in the
        #: module and a whole-file search would pass on a neighbor's mention of them.
        self.improve_path = self.text[start:end]

    def test_it_separates_what_can_be_fixed_from_what_cannot(self):
        """A missing value cannot be invented, and offering to fill one invites fabrication."""
        self.assertRegex(self.text, r"cannot be invented",
                         "the improve path does not say that missing values cannot be "
                         "invented, so 'improve completeness' reads as an instruction to "
                         "fabricate data")
        self.assertIn("format_consistency", self.text)
        self.assertIn("duplicate_rate", self.text)

    def test_it_re_scores_and_re_presents_the_gate(self):
        self.assertRegex(self.text, r"[Rr]e-score",
                         "the improve path never re-scores, so nothing tells the "
                         "Bootcamper whether the work helped")
        self.assertRegex(
            self.text, r"NOT an INV-006 repeat",
            "the file does not sanction re-presenting the gate after a re-score, so a "
            "guide honoring INV-006 suppresses it and the improve path dead-ends one step "
            "later than before")

    def test_it_never_overwrites_the_collected_file(self):
        self.assertRegex(self.text, r"never overwrite|NEW file",
                         "the improve path does not protect the file as collected")

    def test_a_synthesized_source_is_disclosed_before_the_question(self):
        """⛔ Criterion 2 — the disclosure has to PRECEDE the 👉, or it cannot inform it."""
        self.assertIn("provenance: synthesized", self.text)
        self.assertIn("INV-239", self.text)
        disclosure = self.text.index("those gaps are deliberate")
        question = self.text.index(
            "👉 **Your data quality is acceptable but has some gaps.")
        self.assertLess(
            disclosure, question,
            "the synthesized-source disclosure comes after the gate question it exists to "
            "inform; anything meant to inform an answer goes before the question")

    def test_it_updates_every_registry_field_the_new_file_changes(self):
        """⛔ INV-243 — the entry is a set of claims about the file it points at.

        The first version of this step repointed `file_path` and stopped there. Resolving
        duplicates removes records, and Module 6 Phase B compares its loaded count against
        the `record_count` written here — so a stale figure reports a CORRECT load as short
        by exactly the number of duplicates this step just removed, one module downstream
        of the cause. Repointing the file without re-measuring it is what makes the entry
        wrong; the fetch-provenance fields are the opposite case, below.
        """
        # ⛔ Matched as an UPDATE BULLET, not as a token anywhere in the section. A first
        # version asserted the bare substring and **passed the mutation**: deleting the
        # whole `record_count` bullet left the word standing in the ⛔ prose that explains
        # why it matters, so the guard certified the field was updated while the
        # instruction to update it was gone. An assertion a neighbor can satisfy is not an
        # assertion about the claim (INV-282).
        for field in ("file_path", "record_count", "file_size_bytes", "quality_score",
                      "updated_at"):
            with self.subTest(field=field):
                self.assertRegex(
                    self.improve_path, r"(?m)^\s*-\s+\*\*`" + re.escape(field) + r"`\*\*\s*→",
                    f"the improve path repoints the registry without an update bullet for "
                    f"`{field}`, so that field goes on describing the file it replaced")
        self.assertIn("INV-243", self.improve_path,
                      "the rule that makes record_count load-bearing is not nameable at the "
                      "step that changes it (INV-183)")

    def test_it_leaves_the_fetch_provenance_fields_with_the_original(self):
        """The mirror: a derived file must not be described as fetched and count-verified."""
        for field in ("expected_record_count", "validation_status", "validation_checks"):
            with self.subTest(field=field):
                self.assertIn(
                    field, self.improve_path,
                    f"the improve path says nothing about `{field}`, so a reader must guess "
                    "whether a derived file inherits a fetch's checks")
        self.assertRegex(
            self.improve_path, r"ORIGINAL fetch|original fetch",
            "the improve path does not say those fields keep describing the original fetch, "
            "which is the only thing stopping them being re-pointed at a file nobody fetched")

    def test_it_names_registry_fields_that_actually_exist(self):
        """⛔ A field name the schema does not have sends an editor to invent one.

        The first version said *"point that source's `path`"*. The registry's field is
        `file_path` (`module-04-data-collection/SKILL.md`'s entry contract), and no entry
        has ever had a `path` key.
        """
        self.assertNotRegex(
            self.improve_path, r"source's `path`",
            "the improve path names a registry field that does not exist; the schema's field "
            "is `file_path`")

    def test_it_forbids_silent_regeneration(self):
        self.assertRegex(self.text, r"[Nn]ever\s+\*\*silently\s+regenerate|silently regenerate",
                         "nothing forbids answering the question by rewriting the "
                         "Bootcamper's data without telling them")


PHASE2 = MODULE / "phase2-data-mapping.md"
PHASE1 = MODULE / "phase1-quality-assessment.md"
ANCHOR = '<a id="synthesized-source-disclosure"></a>'
#: The band marker that carries the pointer to the rule paragraph into each gated band.
BAND_MARKER = "*(on a synthesized source, the disclosure above first)*:"
#: The rule paragraph's opening and its pointer, matched on whitespace-collapsed text (INV-346).
STEP16_RULE = ("⛔ **(INV-345) On a `provenance: synthesized` source, the 70-79% and <70% questions "
               "are disclosed first.**")
STEP16_POINTER = ("its wording is stated once, at Phase 1's [synthesized-source disclosure]"
                  "(phase1-quality-assessment.md#synthesized-source-disclosure); say it as written "
                  "there rather than a copy here (INV-300)")
#: Step 16's gated questions (#333), which stay verbatim (INV-056), each with its options.
GATED = (
    ("👉 **Quality for {source} is acceptable. What would you like to do? Reply with a number:**",
     ("1. Move on to the next source, {next}.",
      "2. Iterate to improve [specific weak areas] first.")),
    ("👉 **Quality for {source} needs improvement before loading will produce meaningful results. "
     "I'd recommend going back to address [specific issues]. What would you like to do? Reply with "
     "a number:**",
     ("1. Iterate to improve the data.",
      "2. Move on to {next} anyway, knowing results may be limited.")),
    ("👉 **Quality is acceptable. What would you like to do? Reply with a number:**",
     ("1. Proceed to loading now.", "2. Iterate to improve [specific weak areas] first.")),
    ("👉 **Quality needs improvement before loading will produce meaningful results. I'd recommend "
     "going back to address [specific issues]. What would you like to do? Reply with a number:**",
     ("1. Iterate to improve the data.", "2. Proceed anyway, knowing results may be limited.")),
)
UNGATED = (
    "👉 **Quality looks strong for {source}. Ready to map the next source, {next}? Reply with a "
    "number:**",
    "👉 **Quality looks strong. Ready to proceed to loading (Data processing)? Reply with a number:**",
)


def _flat(text):
    return re.sub(r"\s+", " ", text)


def step16_disclosure_problems(phase2, phase1):
    """Step 16 discloses before every 70-79% and <70% question, by pointing at Phase 1 (#521)."""
    start = phase2.find("### 16. Review")
    end = phase2.find("### 17. Iterate", start)
    if start < 0 or end < 0:
        return ["step 16 moved"]
    s16 = phase2[start:end]
    flat = _flat(s16)
    problems = []
    if ANCHOR not in phase1:
        return ["Phase 1 has no synthesized-source-disclosure anchor"]
    if not phase1.index(ANCHOR) < phase1.index("those gaps are deliberate"):
        problems.append("Phase 1's anchor does not sit on the disclosure")
    for needle, what in ((STEP16_RULE, "the INV-345 rule"),
                         (STEP16_POINTER, "the pointer to Phase 1's one statement (INV-300)"),
                         ("Then ask the band's pinned question unchanged, with both options live "
                          "(INV-056)", "the question unchanged with both options live"),
                         ("Say it even when the Bootcamper heard it at Phase 1's gate",
                          "that it is said again after Phase 1's gate"),
                         ("The ≥80% band gets no disclosure", "that the ≥80% band gets none")):
        if needle not in flat:
            problems.append("step 16 does not state %s" % what)
    if "One thing worth knowing before you choose" in s16:
        problems.append("step 16 copies Phase 1's disclosure wording (INV-300)")
    rule_at = flat.find(STEP16_RULE)
    lines = s16.split("\n")
    for question, options in GATED:
        if s16.count(question) != 1:
            problems.append("a gated question is not kept verbatim once: %s" % question[:50])
            continue
        q_line = next(i for i, line in enumerate(lines) if line.strip() == question)
        band = next((lines[i] for i in range(q_line - 1, -1, -1)
                     if lines[i].startswith("- **Quality")), "")
        if BAND_MARKER not in band:
            problems.append("the band before %r carries no disclosure marker" % question[:50])
        if rule_at < 0 or not rule_at < flat.find(_flat(question)):
            problems.append("the disclosure rule does not precede %r" % question[:50])
        after = s16[s16.index(question) + len(question):].split("👉", 1)[0]
        for option in options:
            if option not in after:
                problems.append("%r lost its option %r" % (question[:40], option))
    for question in UNGATED:
        q_line = next((i for i, line in enumerate(lines) if line.strip() == question), None)
        if q_line is None:
            problems.append("a ≥80%% question moved: %s" % question[:50])
            continue
        band = next((lines[i] for i in range(q_line - 1, -1, -1)
                     if lines[i].startswith("- **Quality")), "")
        if BAND_MARKER in band:
            problems.append("a ≥80%% band carries the disclosure marker")
    if s16.count(BAND_MARKER) != 4:
        problems.append("step 16 carries %d disclosure markers, not 4" % s16.count(BAND_MARKER))
    return problems


def _move_rule_last(phase2):
    """Step 16 with its rule paragraph moved below every question (a negative control)."""
    start = phase2.index("⛔ **(INV-345) On a `provenance: synthesized` source, the 70-79%")
    end = phase2.index("\n\n", start)
    rule = phase2[start:end]
    without = phase2[:start] + phase2[end + 2:]
    closing = "*(Internal: end the turn on the applicable question and wait.)*"
    return without.replace(closing, rule + "\n\n" + closing, 1)


class Step16DisclosesOnASynthesizedSource(unittest.TestCase):
    """#521: INV-345's disclosure also precedes step 16's 70-79% and <70% questions."""

    def setUp(self):
        self.phase2 = PHASE2.read_text(encoding="utf-8")
        self.phase1 = PHASE1.read_text(encoding="utf-8")

    def test_step_16_discloses_before_the_gated_questions(self):
        self.assertEqual([], step16_disclosure_problems(self.phase2, self.phase1))

    def test_the_link_resolves(self):
        self.assertEqual(1, self.phase1.count(ANCHOR))

    def test_negative_controls(self):
        p2, p1 = self.phase2, self.phase1
        first_gated = GATED[0][0]
        mutants = {
            "rule dropped": (p2.replace(STEP16_RULE[:40], "⛔ **(see below) Something else", 1), p1),
            "pointer dropped": (p2.replace("(phase1-quality-assessment.md#synthesized-source-"
                                           "disclosure)", "", 1), p1),
            "wording copied": (p2.replace("**While one or more unmapped sources remain**",
                                          '> "One thing worth knowing before you choose."\n\n'
                                          "**While one or more unmapped sources remain**", 1), p1),
            "a band loses its marker": (p2.replace("- **Quality 70-79%** " + BAND_MARKER,
                                                   "- **Quality 70-79%:**", 1), p1),
            "≥80% band marked": (p2.replace("- **Quality ≥80% and all critical fields mapped:**",
                                            "- **Quality ≥80% and all critical fields mapped** "
                                            + BAND_MARKER, 1), p1),
            "question reworded": (p2.replace(first_gated, first_gated.replace("acceptable",
                                                                              "fine"), 1), p1),
            "anchor dropped": (p2, p1.replace(ANCHOR, "", 1)),
            "rule moved after the questions": (_move_rule_last(p2), p1),
        }
        for name, (m2, m1) in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual((p2, p1), (m2, m1), "the mutation no longer applies")
                self.assertNotEqual([], step16_disclosure_problems(m2, m1))

    def test_a_rewrap_still_passes(self):
        """INV-346: the rule paragraph's phrase checks read whitespace-collapsed text."""
        m2 = self.phase2.replace("say it\nas written there", "say it as\nwritten there", 1)
        self.assertNotEqual(self.phase2, m2, "the re-wrap no longer applies")
        self.assertEqual([], step16_disclosure_problems(m2, self.phase1))


if __name__ == "__main__":
    unittest.main()
