"""On a generated scenario, Module 1 cannot close without the registry, and Module 4 repairs it.

Discover the Business Problem's generated-scenario path writes each scenario source into
`config/data_sources.yaml` at Phase 2 Step 11. Before #749 that write was one bullet in Step 11's
"Generated scenario … plus:" list, nothing checked it was done, and a walk closed Module 1 with no
registry: the file appeared only at System verification. Every later module reads it, and Module 4
Step 2's marker guard read "the source's entry" for its `provenance` as though it must exist.

What this file pins:

1. **Step 11's registry write is its own named line**, `**Registry write (generated scenario):**`,
   opening its own paragraph, and no item of the generated-scenario list names the registry file.
2. **Step 17's Registry check confirms it before Module Completion**, on the generated-scenario
   path only: a paragraph of its own, `**Registry check (generated-scenario path only), before
   Module Completion:**`, sits ahead of the Module Completion run and the transition 👉; the
   registry holds one entry under `sources:` per scenario source `docs/business_problem.md` lists,
   a source with no entry is named in one line and its entry written by Step 11's **Registry
   write** (pointed at, the field list not restated, INV-300) before the module continues, and a
   bootcamper-described case is exempt. Step 11's write points forward at the check, and the
   success indicator names the registry and points at the check rather than restating it
   (INV-300). The check paragraph was grafted from the race's approach B.
3. **Module 4 Step 2 repairs a missing entry**: inside the marker guard, after the marker is read
   and before any provenance branch, a source with no entry has its `name`, `provenance` and
   `entity_type` rebuilt from `docs/business_problem.md`, a missing `scenario_record_count` is
   handled by the `provenance: synthesized` branch's existing fallback (pointed at, not restated),
   the rebuild is said in one line, and an existing entry is never overwritten.

Each predicate is negative-controlled against the shipped text with its clause removed, and the
pre-#749 shape of each site is asserted to fail. `tests/test_scenario_registry_fields_agree.py`
keeps pinning which fields the write names (#604).

Phrase checks run on whitespace-collapsed text, so a wrapped phrase still matches (INV-346).

Source issue: #749. Invariants applied: INV-300 (one statement, pointers name it), INV-243
(`record_count` stays measured, unchanged here).

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
PHASE_2 = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
COLLECTION = SKILLS / "module-04-data-collection" / "SKILL.md"

LABEL = "**Registry write (generated scenario):**"
POINTER = "Step 11's **Registry write**"
CHECK_LABEL = "**Registry check (generated-scenario path only), before Module Completion:**"
CHECK_POINTER = "Step 17's **Registry check**"
COMPLETION = "Run the standard **Module Completion** process"
TRANSITION = "👉 **Are you ready to move on to the next module"
REGISTRY = "`config/data_sources.yaml`"
LIST_HEAD = "**Generated scenario (Business Case Offer accepted):**"

#: Fields the schema lists; naming any of them in Step 17 would restate Step 11's write.
FIELD_LIST = ("`provenance`", "`entity_type`", "`shape_quirks`", "`cord_dataset`",
              "`scenario_record_count`")


def squash(text):
    """Collapse whitespace and drop blockquote markers, so wrapped phrases match."""
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M))


def cut(text, phrase, replacement):
    """Replace `phrase` in raw text however it wraps, for a negative control's mutant."""
    pattern = r"\s+".join(re.escape(word) for word in phrase.split())
    return re.sub(pattern, lambda _m: replacement, text)


def phase_2():
    return PHASE_2.read_text(encoding="utf-8")


def section(text, number):
    """One `## N.` step of the phase file, raw, to the next numbered step.

    Only a numbered heading ends it: Step 11's template carries `## ` headings of its own.
    """
    i = text.index("\n## %d. " % number)
    nxt = re.compile(r"\n## \d+\. ").search(text, i + 1)
    return text[i:] if nxt is None else text[i:nxt.start()]


def generated_list(step_11_text):
    """The items of Step 11's "Generated scenario … plus:" list, each raw."""
    i = step_11_text.index(LIST_HEAD)
    body = step_11_text[i:].split("\n\n", 2)[1]
    return [item for item in re.split(r"\n(?=- )", body) if item.startswith("- ")]


def step_11_problems(step_11_text):
    problems = []
    if not re.search(r"^%s\s+record\s+each\s+distinct\s+scenario\s+source\s+into\s+%s"
                     % (re.escape(LABEL), re.escape(REGISTRY)), step_11_text, re.M):
        problems.append("Step 11 has no named line opening its own paragraph for the registry write")
    elif step_11_text.count(LABEL) != 1:
        problems.append("Step 11 names the registry write more than once")
    if CHECK_POINTER not in squash(step_11_text):
        problems.append("Step 11's registry write does not point at Step 17's Registry check")
    for item in generated_list(step_11_text):
        if REGISTRY in item:
            problems.append("an item of the generated-scenario list writes the registry: %r"
                            % squash(item)[:80])
    return problems


def success_indicator(step_17_text):
    i = step_17_text.index("**Success indicator:**")
    return squash(step_17_text[i:].split("\n\n", 1)[0])


def registry_check(step_17_text):
    """Step 17's **Registry check** paragraph, squashed, or None when it is not one of its own."""
    m = re.search(r"^%s" % re.escape(CHECK_LABEL), step_17_text, re.M)
    if m is None:
        return None
    return squash(step_17_text[m.start():].split("\n\n", 1)[0])


def check_problems(step_17_text):
    """The check exists, precedes Module Completion and the 👉, and says what it checks."""
    check = registry_check(step_17_text)
    if check is None:
        return ["Step 17 has no Registry check paragraph of its own"]
    problems = []
    at = step_17_text.index(CHECK_LABEL)
    for anchor, what in ((COMPLETION, "Module Completion"), (TRANSITION, "the transition question")):
        where = step_17_text.find(anchor)
        if where == -1 or at > where:
            problems.append("the Registry check does not come before %s" % what)
    for phrase, why in (
        ("%s must exist with one entry under `sources:` for each scenario source "
         "`docs/business_problem.md` lists" % REGISTRY,
         "does not require one entry per scenario source"),
        ("say in one line which source was missing", "does not name a missing source"),
        ("write its entry by %s, and only then continue" % POINTER,
         "does not write a missing entry by Step 11's Registry write before continuing"),
        ("bootcamper-described case has no such check",
         "does not exempt a bootcamper-described case"),
    ):
        if phrase not in check:
            problems.append("the Registry check %s" % why)
    for field in FIELD_LIST:
        if field in check:
            problems.append("the Registry check restates the field %s (INV-300)" % field)
    return problems


def indicator_problems(text):
    """The success indicator names the registry and points at the check, restating nothing."""
    problems = []
    for phrase, why in (
        ("on the generated-scenario path only, %s with one entry per scenario source" % REGISTRY,
         "does not name the registry on the generated path only"),
        ("(the **Registry check** above)", "does not point at the Registry check"),
    ):
        if phrase not in text:
            problems.append("Step 17's success indicator %s" % why)
    for phrase in ("before the transition question", "name it", "write the entry", POINTER):
        if phrase in text:
            problems.append("Step 17's success indicator restates the Registry check: %r (INV-300)"
                            % phrase)
    for field in FIELD_LIST:
        if field in text:
            problems.append("Step 17's success indicator restates the field %s (INV-300)" % field)
    return problems


def guard(body=None):
    """Module 4 Step 2's marker guard lead, to its first provenance branch."""
    body = squash(COLLECTION.read_text(encoding="utf-8")) if body is None else body
    i = body.index("**The signal is the MARKER; the provenance selects the ACTION.**")
    return body[i:body.index("- **`provenance: cord`**", i)]


def repair_problems(text):
    problems = []
    marker = text.find("`🤖 Bootcamp-generated business case` marker")
    repair = text.find("**If the source has no entry**")
    if repair == -1:
        return ["the marker guard does not say what happens when the source has no entry"]
    if marker == -1 or marker > repair:
        problems.append("the repair is not gated on the generated marker")
    tail = text[repair:]
    for phrase, why in (
        ("Module 1 Step 11's registry write was skipped", "does not name the skipped write"),
        ("rebuild the entry's `name`, `provenance` and `entity_type` from that source in "
         "`docs/business_problem.md`", "does not rebuild name, provenance and entity_type "
                                       "from the problem statement"),
        ("treat its missing `scenario_record_count` as the `provenance: synthesized` branch below "
         "does", "does not point a missing scenario_record_count at the existing fallback"),
        ("say in one line that you rebuilt it", "does not say the rebuild in one line"),
        ("an existing one is never overwritten", "does not protect an existing entry"),
    ):
        if phrase not in tail:
            problems.append("the repair %s" % why)
    if "take the count from" in text:
        problems.append("the guard restates the scenario_record_count fallback (INV-300)")
    return problems


class Step11NamesTheRegistryWrite(unittest.TestCase):
    def test_the_list_is_read(self):
        """Liveness: the list reader finds the marker item, so an empty read cannot pass."""
        items = generated_list(section(phase_2(), 11))
        self.assertGreaterEqual(len(items), 3)
        self.assertIn("generated marker", items[0])

    def test_the_write_is_its_own_named_line(self):
        self.assertEqual(step_11_problems(section(phase_2(), 11)), [])

    def test_negative_control_the_pre_749_bullet(self):
        """The write folded back into the list, as it shipped before #749, fails."""
        text = section(phase_2(), 11)
        mutant = text.replace("at runtime.\n\n" + LABEL + " record", "at runtime.\n- Record")
        self.assertNotEqual(mutant, text)
        problems = step_11_problems(mutant)
        self.assertIn("Step 11 has no named line opening its own paragraph for the registry write",
                      problems)
        self.assertTrue(any("generated-scenario list writes the registry" in p for p in problems))

    def test_negative_control_the_label_mid_paragraph(self):
        text = section(phase_2(), 11)
        mutant = text.replace("\n\n" + LABEL, " " + LABEL)
        self.assertNotEqual(step_11_problems(mutant), [])


class Step17ChecksTheRegistry(unittest.TestCase):
    def test_the_registry_check_precedes_module_completion(self):
        self.assertEqual(check_problems(section(phase_2(), 17)), [])

    def test_the_success_indicator_points_at_the_check(self):
        self.assertEqual(indicator_problems(success_indicator(section(phase_2(), 17))), [])

    def test_the_pointers_resolve(self):
        """Each label is stated once, in its own step, and the other step points at it."""
        text = phase_2()
        self.assertEqual(text.count(LABEL), 1)
        self.assertIn(LABEL, section(text, 11))
        self.assertEqual(text.count(CHECK_LABEL), 1)
        self.assertIn(CHECK_LABEL, section(text, 17))
        self.assertIn(CHECK_POINTER, squash(section(text, 11)))
        self.assertIn(POINTER, registry_check(section(text, 17)))

    def test_negative_controls_the_check(self):
        text = section(phase_2(), 17)
        paragraph = text[text.index(CHECK_LABEL):text.index(COMPLETION)]
        for mutant, why in (
            (text.replace(paragraph, ""), "the check dropped (the pre-#749 Step 17)"),
            (text.replace(paragraph, "").replace(TRANSITION, paragraph + TRANSITION),
             "the check moved after Module Completion"),
            (text.replace(paragraph, "").replace("**Success indicator:**",
                                                  paragraph + "**Success indicator:**"),
             "the check moved below the transition question"),
            (text.replace("\n" + CHECK_LABEL, " " + CHECK_LABEL), "the label mid-paragraph"),
            (cut(text, "one entry under `sources:` for each scenario source", "entries"),
             "one entry per source dropped"),
            (cut(text, "say in one line which source was missing,", ""),
             "the missing source not named"),
            (cut(text, "by Step 11's **Registry write**", "by hand"),
             "the pointer at Step 11 dropped"),
            (cut(text, "has no such check", "is checked too"), "the exemption dropped"),
            (cut(text, "lists. For each", "lists, each with `provenance`. For each"),
             "a field restated"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(mutant, text, why)
                self.assertNotEqual(check_problems(mutant), [], why)

    def test_negative_controls_the_indicator(self):
        text = success_indicator(section(phase_2(), 17))
        pre_749 = ("**Success indicator:** ✅ Clear problem statement + identified data sources + "
                   "defined success metrics + bootcamper confirmation + `docs/business_problem.md` "
                   "created + Module 1 recap section appended.")
        #: Race approach A's indicator before the graft: it restated the check in the indicator.
        restated = text.replace(
            "(the **Registry check** above).",
            "in `docs/business_problem.md`. Check that last one before the transition question: "
            "for each source with no entry, name it and write the entry by Step 11's **Registry "
            "write**, then ask.")
        for mutant, why in (
            (pre_749, "the pre-#749 indicator"),
            (restated, "the check restated in the indicator (pre-graft)"),
            (text.replace("on the generated-scenario path only, ", ""), "path scope dropped"),
            (text.replace("(the **Registry check** above)", ""), "pointer dropped"),
            (text.replace("+ on the generated", "with `provenance` + on the generated"),
             "field list restated"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(mutant, text, why)
                self.assertNotEqual(indicator_problems(mutant), [], why)

    def test_negative_control_step_11_points_nowhere(self):
        """Step 11's forward pointer is what ties the write to the check."""
        text = section(phase_2(), 11)
        mutant = cut(text, CHECK_POINTER, "Step 17")
        self.assertNotEqual(mutant, text)
        self.assertIn("Step 11's registry write does not point at Step 17's Registry check",
                      step_11_problems(mutant))


class Module4RepairsAMissingEntry(unittest.TestCase):
    def test_the_guard_states_the_repair(self):
        self.assertEqual(repair_problems(guard()), [])

    def test_negative_controls(self):
        text = guard()
        pre_749 = text[:text.index(" **If the source has no entry**")]
        for mutant, why in (
            (pre_749, "the pre-#749 guard"),
            (text.replace("`name`, `provenance` and `entity_type`", "fields"), "fields dropped"),
            (text.replace("an existing one is never overwritten", "rebuild every entry"),
             "overwrite allowed"),
            (text.replace("say in one line that you rebuilt it", "carry on"), "silent rebuild"),
            (text.replace("as the `provenance: synthesized` branch below does",
                          "and take the count from `docs/business_problem.md`"),
             "fallback restated"),
        ):
            with self.subTest(why=why):
                self.assertNotEqual(repair_problems(mutant), [], why)


if __name__ == "__main__":
    unittest.main()
