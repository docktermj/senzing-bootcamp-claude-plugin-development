"""Fourteen small coherence items from the 2026-10-12 production-readiness audit (#523).

Each item was a local miss: a description that kept an old rule, a pointer to the wrong section,
a rule restated where it should be pointed at, or a fixed value that should be measured. Item 5
is guarded in ``test_truth_set_is_the_practice_run.py``, item 12 in
``test_viz_defaults_at_scale.py``, item 14 in ``test_citation_census.py`` and here, and item
13(b) is a DEFERRED INVARIANT block in ``specs/IMPLEMENTED.md``, not a test. This file holds the
rest, one class per item.

Every check is a pure function over a file's text that returns a list of problems, so each one
also runs on a mutated copy of the shipped text as its negative control: the control puts the
audited defect back and asserts the check reports it.

⚠️ **Phrase checks collapse whitespace (INV-346)**, so a phrase wrapped across lines still
matches; ``flat`` is the collapse. The one structural check (item 7) reads section headings,
which are single lines by construction.

⛔ **What this cannot establish:** that a live guide follows any of these passages. It pins that
the skill files STATE them; ``dry-run`` phase 3 observes a run.

Stdlib only; shipped files are read as text, and the discoveries generator is loaded only to read
its section list (INV-108).

Source issue: #523.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"

GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
MODULE_3 = SKILLS / "module-03-system-verification"
TRUTHSET = SKILLS / "module-03b-truthset-visualization"
TRUTHSET_P1 = TRUTHSET / "phase1-visualization.md"
CONTRACT = TRUTHSET / "visualization-api-reference.md"
MODULE_5_P1 = SKILLS / "module-05-data-quality-mapping" / "phase1-quality-assessment.md"
MODULE_5_P2 = SKILLS / "module-05-data-quality-mapping" / "phase2-data-mapping.md"
MODULE_6 = SKILLS / "module-06-data-processing"
PHASE_B = MODULE_6 / "phaseB-load-first-source.md"
PHASE_D = MODULE_6 / "phaseD-validation.md"
MODULE_7 = SKILLS / "module-07-query-visualize-discover"
MODULE_7_P1 = MODULE_7 / "phase1-query-visualize.md"
DISCOVER_A = MODULE_7 / "phase2-discover.md"
DISCOVER_B = MODULE_7 / "phase2b-discover.md"
DISCOVERIES_GENERATOR = PLUGIN / "scripts" / "generate_discoveries_pdf.py"
FONT_SAFETY_TEST = REPO_ROOT / "tests" / "test_recap_pdf_font_safety.py"


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def section(text, start, end_markers):
    """From ``start`` up to the first of ``end_markers`` after it ("" when ``start`` is absent)."""
    i = text.find(start)
    if i < 0:
        return ""
    rest = text[i:]
    cut = [rest.find(m, len(start)) for m in end_markers]
    cut = [c for c in cut if c > 0]
    return rest[:min(cut)] if cut else rest


def mutate(test, text, old, new):
    """Replace ``old`` once; fail the control if the anchor text has gone."""
    test.assertIn(old, text, "the control's anchor text is gone; update the control")
    return text.replace(old, new, 1)


# --- Item 1: the write-gate is described by its current rule (INV-200) ---------------------

OLD_GATE = "enforces the temp-path and secret rules"


def write_gate_problems(text):
    problems = []
    f = flat(text)
    if OLD_GATE in f:
        problems.append("describes the write-gate by its old rule (%r)" % OLD_GATE)
    if "write-gate blocks every write outside the project" not in f:
        problems.append("does not say the write-gate blocks every write outside the project")
    if "INV-200" not in f:
        problems.append("does not cite INV-200")
    return problems


class Item1TheWriteGateIsDescribedByItsCurrentRule(unittest.TestCase):
    SITES = (GROUND_RULES, MODULE_5_P2)

    def test_both_sites_state_the_current_rule(self):
        for path in self.SITES:
            with self.subTest(site=path.name):
                self.assertEqual([], write_gate_problems(read(path)))

    def test_control_the_old_description_is_reported(self):
        text = read(MODULE_5_P2)
        mutated = mutate(self, text, "write-gate blocks every write outside the project",
                         "write-gate " + OLD_GATE)
        self.assertTrue(write_gate_problems(mutated))


# --- Item 2: no "skip silently" where the canonical exit-2 handling is pointed at -----------

SILENT = re.compile(r"skips? silently|silent-skip|skipped silently", re.I)
CAPTURE_SITES = (TRUTHSET_P1, MODULE_7_P1)


def capture_problems(text):
    problems = []
    f = flat(text)
    for m in SILENT.finditer(f):
        problems.append("says %r; module-completion.md's exit-2 handling is silent only at "
                        "minimal verbosity" % m.group(0))
    if not re.search(r"only at the `minimal` verbosity preset", f):
        problems.append("does not say the skip is silent only at the `minimal` preset")
    if not re.search(r"skip path that section states once,? \(?INV-300", f):
        problems.append("does not point at module-completion.md's skip path (INV-300)")
    return problems


class Item2NoSilentSkipAtTheCaptureSites(unittest.TestCase):

    def test_both_capture_sites_defer_to_module_completion(self):
        for path in CAPTURE_SITES:
            with self.subTest(site=path.name):
                self.assertEqual([], capture_problems(read(path)))

    def test_the_canonical_statement_still_reads_the_reason(self):
        """The pointed-at text must still say what the pointers say it says."""
        canonical = flat(read(SKILLS / "bootcamp-onboarding" / "module-completion.md"))
        self.assertIn("say nothing at the `minimal` preset", canonical)
        self.assertIn("Read which of the three reasons it gave", canonical)

    def test_control_skip_silently_is_reported(self):
        text = read(TRUTHSET_P1)
        mutated = mutate(self, text, "If the helper exits 2,",
                         "If no headless capability is available it skips silently. If the "
                         "helper exits 2,")
        self.assertTrue(any("skips silently" in p for p in capture_problems(mutated)))


# --- Item 3: the JVM-flag cross-reference points at "The launch environment" ----------------

LAUNCH_HEADING = "The launch environment (JVM languages, and macOS generally)"


def cross_reference_problems(contract, module_2):
    problems = []
    passage = section(flat(contract), "**which does not fix it**", ("- ⚠️",))
    if not passage:
        return ["the JVM-flag passage is missing from the contract"]
    if '"MCP Java scaffolds may need a JSON' in passage:
        problems.append("still cites the JSON-library section for the linker-path reason")
    if LAUNCH_HEADING not in passage:
        problems.append("does not point at %r" % LAUNCH_HEADING)
    if "### " + LAUNCH_HEADING not in module_2:
        problems.append("Module 2 has no %r heading to point at" % LAUNCH_HEADING)
    return problems


class Item3TheCrossReferenceNamesTheRightSection(unittest.TestCase):

    def test_it_points_at_the_launch_environment(self):
        self.assertEqual([], cross_reference_problems(read(CONTRACT), read(MODULE_2)))

    def test_control_the_json_library_pointer_is_reported(self):
        text = read(CONTRACT)
        mutated = mutate(self, text, '"The launch environment (JVM\n  languages, and macOS generally)"',
                         '"MCP Java scaffolds may need a JSON\n  library the install does not provide"')
        self.assertTrue(cross_reference_problems(mutated, read(MODULE_2)))


# --- Item 4: the INV-231 pointer names the section that holds the rule ----------------------

def inv_231_pointer_problems(phase1, ground_rules):
    problems = []
    m = re.search(r"connection-string rule and the scheme it forbids are stated once, in "
                  r"`\.\./bootcamp-onboarding/ground-rules\.md` → \"([^\"]+)\"", flat(phase1))
    if not m:
        return ["the INV-231 pointer is missing or names no ground-rules section"]
    named = m.group(1)
    body = section(ground_rules, "\n## " + named + "\n", ("\n## ",))
    if not body:
        problems.append("ground-rules.md has no section %r" % named)
    elif "INV-231" not in body:
        problems.append("the named section %r does not hold the INV-231 rule" % named)
    return problems


class Item4TheInv231PointerNamesFilePlacement(unittest.TestCase):

    def test_the_named_section_holds_the_rule(self):
        self.assertEqual([], inv_231_pointer_problems(read(TRUTHSET_P1), read(GROUND_RULES)))

    def test_control_the_old_section_name_is_reported(self):
        text = read(TRUTHSET_P1)
        mutated = mutate(self, text, '→ "File placement" (INV-300)',
                         '→ "Mandatory gates and step order" (INV-300)')
        self.assertTrue(inv_231_pointer_problems(mutated, read(GROUND_RULES)))


# --- Item 6: Step 7 item 4 agrees with Step 9 (INV-229) ------------------------------------

def step_7_problems(text):
    item_4 = flat(section(text, "4. ⛔ **If a check fails, this is a DIAGNOSTIC",
                          ("**Checkpoint:**",)))
    if not item_4:
        return ["Step 7 item 4 is missing"]
    problems = []
    if re.search(r"Fix the records|re-run this step", item_4):
        problems.append("asks for the records to be fixed or the step re-run (INV-229)")
    if "nothing is fixed or re-run, by you or by the bootcamper (INV-229)" not in item_4:
        problems.append("does not say nothing is fixed or re-run")
    if "Step 9: Verification Report Generation" not in item_4:
        problems.append("does not point at Step 9")
    return problems


class Item6ModuleThreeDoesNotAskForAFix(unittest.TestCase):
    TEXT = read(MODULE_3 / "phase1-verification.md")

    def test_step_7_agrees_with_step_9(self):
        self.assertEqual([], step_7_problems(self.TEXT))

    def test_control_fix_and_rerun_is_reported(self):
        mutated = mutate(self, self.TEXT, "and continue: nothing is fixed or re-run",
                         "and continue. Fix the records and re-run this step; nothing is fixed "
                         "or re-run")
        self.assertTrue(step_7_problems(mutated))


# --- Item 7: the self-check and the capture run after the server is up ----------------------

SELF_CHECK = "Run the encoding self-check against the running server"
CAPTURE = "**Capture screenshots for the recap (optional, non-blocking).**"


def step_order_problems(text):
    problems = []
    s22 = section(text, "### 2.2 ", ("\n### ",))
    s24a = section(text, "### 2.4a ", ("\n### ",))
    order = [text.find(h) for h in ("### 2.2 ", "### 2.3 ", "### 2.4 ", "### 2.4a ", "### 2.4b ")]
    if -1 in order or order != sorted(order):
        return ["sections 2.2, 2.3, 2.4, 2.4a and 2.4b are missing or out of order"]
    for what, marker in (("the encoding self-check", SELF_CHECK), ("the capture", CAPTURE),
                         ("the capture command", "capture_screenshots.py")):
        if marker in s22:
            problems.append("%s is in 2.2, before 2.3 starts the server" % what)
        if marker not in s24a:
            problems.append("%s is not in 2.4a, after 2.4 verifies the endpoints" % what)
    return problems


class Item7TheSelfCheckRunsAgainstARunningServer(unittest.TestCase):
    TEXT = read(TRUTHSET_P1)

    def test_2_2_builds_the_snapshot_only(self):
        self.assertEqual([], step_order_problems(self.TEXT))

    def test_control_the_former_order_is_reported(self):
        block = section(self.TEXT, "⛔ **(INV-270, INV-259, INV-265) " + SELF_CHECK, ("### 2.4b ",))
        self.assertTrue(block, "the moved block is gone")
        moved = self.TEXT.replace(block, "")
        moved = moved.replace("### 2.3 Start the live web app", block + "### 2.3 Start the live web app")
        self.assertTrue(step_order_problems(moved))


# --- Item 8: colors are assigned from the sources present (INV-127) ------------------------

def color_problems(text):
    entity_graph = flat(section(text, "1. **Entity Graph** (default)", ("2. **Merge Statistics:**",)))
    if not entity_graph:
        return ["the Entity Graph tab entry is missing"]
    problems = []
    if re.search(r"\bCUSTOMERS\b[^.]*\bREFERENCE\b[^.]*\bWATCHLIST\b", entity_graph):
        problems.append("lists a color per Truth Set source name, which reads as a name-keyed map")
    if "assigned from the sources present" not in entity_graph:
        problems.append("does not say colors are assigned from the sources present")
    if "INV-127" not in entity_graph:
        problems.append("does not cite INV-127")
    return problems


class Item8ColorsAreNotKeyedByName(unittest.TestCase):
    TEXT = read(TRUTHSET_P1)

    def test_the_entity_graph_entry_states_assignment(self):
        self.assertEqual([], color_problems(self.TEXT))

    def test_control_the_name_keyed_list_is_reported(self):
        mutated = mutate(self, self.TEXT, "colored by data source, with colors assigned from the sources present",
                         "colored by data source (CUSTOMERS ember/orange, REFERENCE blue, "
                         "WATCHLIST gold/amber), with colors from the sources")
        self.assertTrue(color_problems(mutated))


# --- Item 9: INV-048 is cited only for the recap PDF ----------------------------------------

def inv_048_problems(text):
    """These files never mean the recap PDF, so INV-048 has no business in them."""
    return ["line %d cites INV-048, which governs the recap PDF" % (i + 1)
            for i, line in enumerate(text.splitlines()) if "INV-048" in line]


class Item9Inv048IsNotAGenericNonBlockingRule(unittest.TestCase):
    SITES = (MODULE_2, MODULE_5_P1, PHASE_D)

    def test_no_site_cites_inv_048(self):
        for path in self.SITES:
            with self.subTest(site=path.name):
                self.assertEqual([], inv_048_problems(read(path)))

    def test_the_replacements_are_the_governing_invariants(self):
        m2 = flat(read(MODULE_2))
        self.assertIn("A check that cannot run is reported as not run (INV-163)", m2)
        self.assertIn("say so in one line and continue (INV-163)", m2)
        self.assertIn("⛔ (INV-335, INV-163) **The check reports and asks; it never blocks the module.**",
                      flat(read(MODULE_5_P1)))
        self.assertIn("never blocking (INV-012): how it is filed is stated once, in that rule",
                      flat(read(PHASE_D)))

    def test_control_a_restored_citation_is_reported(self):
        text = read(MODULE_5_P1)
        mutated = mutate(self, text, "⛔ (INV-335, INV-163) **The check reports and asks",
                         "⛔ (INV-048) **The check reports and asks")
        self.assertTrue(inv_048_problems(mutated))


# --- Item 10: Phase D computes the UAT % its gate routes on ---------------------------------

def uat_problems(text):
    f = flat(text)
    problems = []
    step_22 = flat(section(text, "## 22. ", ("\n## ",)))
    if '<a id="uat-percent"></a>' not in step_22:
        problems.append("step 22 does not anchor the UAT % definition")
    if "spot-checked entities judged correct ÷ entities checked" not in step_22:
        problems.append("step 22 does not define the UAT %")
    if "If no entity could be spot-checked, write that instead" not in step_22:
        problems.append("step 22 does not say what to write when nothing was checked")
    for branch in ("### 25a. ", "### 25b. "):
        body = flat(section(text, branch, ("\n### ", "\n## ")))
        if "(#uat-percent)" not in body or "docs/uat_results.md" not in body:
            problems.append("%s does not write the UAT % to docs/uat_results.md" % branch.strip())
    gate = flat(section(text, "## Iterate vs. proceed decision gate", ("The gate question,",)))
    if "reading the UAT % from `docs/uat_results.md`" not in gate:
        problems.append("the gate does not read the UAT % from docs/uat_results.md")
    if "never state a UAT % that was not computed" not in gate:
        problems.append("the gate may report a UAT % it did not compute")
    if "Stakeholder sign-off obtained (25b), or self-directed validation recorded (25a)" not in f:
        problems.append("the sign-off criterion cannot be met on the 25a path")
    return problems


class Item10PhaseDComputesTheUatPercent(unittest.TestCase):
    TEXT = read(PHASE_D)

    def test_phase_d_defines_writes_and_reads_it(self):
        self.assertEqual([], uat_problems(self.TEXT))

    def test_control_the_old_criterion_is_reported(self):
        mutated = mutate(self, self.TEXT,
                         "Stakeholder sign-off obtained (25b), or self-directed validation recorded (25a)",
                         "Stakeholder sign-off obtained")
        self.assertTrue(uat_problems(mutated))

    def test_control_a_gate_that_does_not_read_the_file_is_reported(self):
        mutated = mutate(self, self.TEXT, "reading the UAT % from `docs/uat_results.md`",
                         "reading the UAT")
        self.assertTrue(uat_problems(mutated))


# --- Item 11: wording ------------------------------------------------------------------------

def wording_problems(module_2, module_3_files, module_3_skill, phase_b):
    problems = []
    criteria = flat(section(module_2, "## Success Criteria", ("\n## ",)))
    if "installed natively." in criteria or "`docker` route" not in criteria:
        problems.append("Module 2's success criterion does not cover the container route")
    for name, text in module_3_files.items():
        if re.search(r"gate 3\s*(?:→|->)\s*4", text):
            problems.append("%s still names the vestigial gate 3→4" % name)
    skill = flat(module_3_skill)
    if not re.search(r"description: .*asks to run verification", skill):
        problems.append("Module 3's description does not route a request to run verification")
    if '**"Run verification":** a request to run system verification' not in skill:
        problems.append("Module 3's SKILL.md does not say a request to run verification starts it")
    step_10 = flat(section(phase_b, "## 10. Incremental loading strategy", ("\n## ",)))
    if "document the choice" in step_10:
        problems.append("Step 10 asks for a choice while steps 9–11 ask nothing")
    if "Do not ask the bootcamper to choose" not in step_10:
        problems.append("Step 10 does not say the bootcamper is not asked to choose")
    return problems


class Item11Wording(unittest.TestCase):

    def inputs(self):
        files = {p.name: read(p) for p in sorted(MODULE_3.glob("*.md"))}
        return read(MODULE_2), files, read(MODULE_3 / "SKILL.md"), read(PHASE_B)

    def test_the_wording_holds(self):
        self.assertEqual([], wording_problems(*self.inputs()))

    def test_control_the_gate_term_is_reported(self):
        m2, files, skill, phase_b = self.inputs()
        files["phase1-verification.md"] = mutate(
            self, files["phase1-verification.md"], "3. Record nothing more",
            '3. Update gate 3→4 to "skipped". Record nothing more')
        self.assertTrue(wording_problems(m2, files, skill, phase_b))

    def test_control_a_choice_in_step_10_is_reported(self):
        m2, files, skill, phase_b = self.inputs()
        phase_b = mutate(self, phase_b, "Do not ask the bootcamper to choose",
                         "Help the bootcamper document the choice")
        self.assertTrue(wording_problems(m2, files, skill, phase_b))

    def test_control_native_only_is_reported(self):
        m2, files, skill, phase_b = self.inputs()
        m2 = mutate(self, m2, "- ✅ Senzing SDK installed, natively or, on the `docker` route, inside "
                    "the SDK container.", "- ✅ Senzing SDK installed natively.")
        self.assertTrue(wording_problems(m2, files, skill, phase_b))


# --- Item 13(a): generated data is never described as the Bootcamper's (INV-239) ------------

def generation_defect_problems(passage, where):
    f = flat(passage)
    if not f:
        return ["%s is missing" % where]
    problems = []
    if "(INV-239)" not in f:
        problems.append("%s does not carry the INV-239 generation-defect framing" % where)
    if "defect in that generated data" not in f:
        problems.append("%s does not call it a defect in the generated data" % where)
    if "`/bootcamp-feedback`" not in f:
        problems.append("%s does not suggest /bootcamp-feedback" % where)
    if "step 4d" not in f or "INV-300" not in f:
        problems.append("%s does not point at step 4d's statement (INV-300)" % where)
    return problems


def step_4a_fallback(text):
    return section(text, "6. **Graceful fallback for limited data:**", ("**Checkpoint:**",))


def step_4e_zero_edges(text):
    return section(text, "⛔ **(INV-356) A zero edge count is a failure", ("10. **Hand over.**",))


class Item13aGeneratedDataIsTheBootcamps(unittest.TestCase):

    def test_step_4a_and_step_4e_use_the_framing(self):
        self.assertEqual([], generation_defect_problems(step_4a_fallback(read(DISCOVER_A)),
                                                        "step 4a's fallback"))
        self.assertEqual([], generation_defect_problems(step_4e_zero_edges(read(DISCOVER_B)),
                                                        "step 4e's zero-edge report"))

    def test_control_a_missing_framing_is_reported(self):
        text = read(DISCOVER_B)
        passage = step_4e_zero_edges(text)
        cut = passage[:passage.index("⛔ **(INV-239)")]
        self.assertTrue(generation_defect_problems(cut, "step 4e's zero-edge report"))


# --- Item 14(a): the font-safety fixture carries every required section ---------------------

def load_generator():
    """The discoveries generator, loaded once to read its section list and normalizer."""
    name = "_discoveries_generator_523"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, DISCOVERIES_GENERATOR)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module  # a dataclass resolves its module through sys.modules
        spec.loader.exec_module(module)
    return sys.modules[name]


def fixture_sections():
    """The font-safety test's ``DISCOVERIES_SECTIONS``, read as text rather than imported."""
    body = re.search(r"DISCOVERIES_SECTIONS = \((.*?)\n\)", read(FONT_SAFETY_TEST), re.S)
    return tuple(re.findall(r'"([^"]+)"', body.group(1))) if body else ()


def missing_sections(required, fixture, normalize):
    have = {normalize(s) for s in fixture}
    return [r for r in required if normalize(r) not in have]


class Item14aTheFontFixtureCarriesEverySection(unittest.TestCase):

    def test_every_required_section_is_in_the_fixture(self):
        gen = load_generator()
        fixture = fixture_sections()
        self.assertEqual([], missing_sections(gen.REQUIRED_SECTIONS, fixture, gen._normalize))
        self.assertIn("all seven required sections", read(FONT_SAFETY_TEST))

    def test_control_the_six_section_fixture_is_reported(self):
        gen = load_generator()
        fixture = fixture_sections()
        six = tuple(s for s in fixture if gen._normalize(s) != "your question answered")
        self.assertEqual(["your question answered"],
                         missing_sections(gen.REQUIRED_SECTIONS, six, gen._normalize))


if __name__ == "__main__":
    unittest.main()
