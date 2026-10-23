"""When nothing mechanical is left to fix, Module 5's gate offers a return, never a dead option.

On a 2026-10-01 walk, STORE_POS (synthesized, deliberately gappy) scored 73.5. "Improve the
weakest fields first" normalized formats to 79.0, and the Bootcamper chose it twice more. Nothing
was fixable, so Step 7a re-presented the same pinned gate, whose option 1 was the same dead
improvement. Step 7a step 6 said to stop looping, which the pinned gate made impossible. The only
way out was a one-line mention of "a return to that module", with no wording, no handling step,
and nothing in Data collection to receive it. The <70% gate has the same shape.

The fix states the route **once**, in `phase1-quality-assessment.md` Step 7b, and every other site
cites it (INV-300):

* the pinned **no-progress variant** of both gating bands, whose option 1 IS the return question
  (INV-056, INV-006);
* the `cord` / `free_data` statement that a fixed dataset's completeness cannot change, with no 👉;
* the return's handling step: the `collection_return` key, the Module 4 steps per provenance, and
  the Module 5 resume step (INV-284);
* Module 4 Step 2's receiving branch (`synthesized`, `own`, `unknown`) and Step 9 not running.

⛔ **Each check is a function of the file text, so the negative controls run the SAME check on a
mutated copy** (INV-265): removing the variant, the handling step or the receiving branch, or
offering a `free_data` source a return, must each make it report a problem.

Source issue: #337. Invariants: INV-006, INV-050, INV-056, INV-239, INV-243, INV-284, INV-300.

Also enforces INV-366 (the cross-module return contract, registered 2026-10-13) for the `collection_return` route:
it asserts the skill files *state* the contract and cannot establish that a live run follows it.

#598 adds what an interrupted return needs to resume as INV-366 says:

* every offering module's **First:** routes every return it offers, Module 5's `collection_return`
  among them, to the step that continues it. The offers are derived from the files (the record each
  module writes), never listed, so a new offer without a route fails here;
* the `collection_return` record carries `completed`, Module 4's receiving branch adds each finished
  step to it in place of the step's checkpoint, and Step 7b item 4 resumes at the first step not
  listed there, reading a record without the key as empty.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

import _corpus

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE5 = SKILLS / "module-05-data-quality-mapping"
PHASE1 = MODULE5 / "phase1-quality-assessment.md"
MODULE4 = SKILLS / "module-04-data-collection" / "SKILL.md"
MODULE5_SKILL = MODULE5 / "SKILL.md"
ROUTE_ANCHOR = '<a id="the-return-route"></a>'
ROUTE_LINK = "phase1-quality-assessment.md#the-return-route"
#: How a module's files start each return, so the offers are derived rather than listed. Matched
#: with whitespace collapsed and bold markers dropped (`flat`), so a wrap never hides an offer.
OFFERS = {
    "collection_return": re.compile(r'"collection_return": \{'),
    "setup_detour": re.compile(r"add the `setup_detour` record"),
    "quality_iteration": re.compile(r'"quality_iteration": \{|Enter \[the quality-iteration route\]'),
}

STEP_7B = "### 7b."
GATE = "### Quality gate"
STEP_7A = "### 7a."
END_OF_PHASE = "**Success indicator:**"
ANCHOR = '<a id="receiving-a-collection-return"></a>'
MARKER_GUARD = "⛔ **First check whether Module 1"

#: The band question lines, which the variant keeps (the criterion: "its question line stays the
#: band's existing 👉 line").
BANDS = {
    "70-79": "👉 **Your data quality is acceptable but has some gaps. What would you like to do? "
             "Reply with a number:**",
    "<70": "👉 **Your data quality needs attention before mapping will produce good results. "
           "What would you like to do? Reply with a number:**",
}
#: The same lines on a `synthesized` source (#790): "Your data quality" becomes "The generated
#: data's quality" and nothing else changes, pinned verbatim (INV-056, INV-399).
SYNTHESIZED_BANDS = {
    "70-79": "👉 **The generated data's quality is acceptable but has some gaps. What would you "
             "like to do? Reply with a number:**",
    "<70": "👉 **The generated data's quality needs attention before mapping will produce good "
           "results. What would you like to do? Reply with a number:**",
}
VARIANT_OPTIONS = {
    "70-79": ["Return to Data collection for this source.", "Continue to mapping now."],
    "<70": ["Return to Data collection for this source.",
            "Proceed anyway, knowing the results may be limited."],
}
#: An option proposing the improvement that cannot happen here (the dead choice).
IMPROVE = re.compile(r"(?i)\bimprov|\bwork on\b|\biterat")
OPTION = re.compile(r"^\s*(\d)\.\s+(.*\S)\s*$")
PROVENANCES = re.compile(r"`(synthesized|own|unknown|cord|free_data)`")


def flat(text):
    return re.sub(r"\s+", " ", text).replace("**", "")


def between(text, start, end):
    """The text from `start` to the next `end`, or None when `start` is absent."""
    if start not in text:
        return None
    i = text.index(start)
    j = text.find(end, i + len(start))
    return text[i:j if j != -1 else len(text)]


def options_after(text, question):
    """The numbered options directly below each occurrence of `question`.

    Line-scoped by design (#424): each option opens on its own numbered line.
    """
    out = []
    for m in re.finditer(re.escape(question), text):
        opts = []
        for line in text[m.end():].split("\n")[1:]:
            if not line.strip():
                if opts:
                    break
                continue
            o = OPTION.match(line)
            if not o:
                break
            opts.append(o.group(2))
        out.append(opts)
    return out


# ---------------------------------------------------------------------------------- checks


def variant_problems(phase1):
    """Criteria 1-4: both bands' pinned no-progress variants, in Step 7b."""
    step = between(phase1, STEP_7B, END_OF_PHASE)
    if step is None:
        return ["Step 7b is missing"]
    problems = []
    for band, question in list(BANDS.items()) + list(SYNTHESIZED_BANDS.items()):
        lists = options_after(step, question)
        if VARIANT_OPTIONS[band] not in lists:
            problems.append("the %s no-progress variant (%r with options %r) "
                            "is not in Step 7b" % (band, question, VARIANT_OPTIONS[band]))
        for opts in lists:
            dead = [o for o in opts if IMPROVE.search(o)]
            if dead:
                problems.append("Step 7b offers an improvement option, the dead choice: %r"
                                % dead)
    f = flat(step)
    for needle, why in (
            ("format_consistency` at 100%", "the condition names format_consistency at 100%"),
            ("(DATA_SOURCE, RECORD_ID)", "the condition names the repeated key pair"),
            ("the first time", "the check runs at the first presentation"),
            ("fixed everything", "the check runs after a pass that fixed everything"),
            ("found nothing", "the check runs after a pass that found nothing"),
            ("score is unchanged", "a no-change pass identifies the score as unchanged")):
        if needle not in f:
            problems.append("Step 7b: " + why)
    if not re.search(r"Option 1 IS the return route's pinned question", f):
        problems.append("Step 7b does not say option 1 IS the return question")
    if not re.search(r"(?i)ask no second confirmation", f):
        problems.append("Step 7b does not forbid a second confirmation")
    return problems


def provenance_lead(step, arrow_target):
    """The provenances named in the bold lead line `**`a`, `b` … → <arrow_target>`.

    Line-scoped by design (#424): the lead is one line of backticked tokens and an arrow, and
    a lead that wrapped would return None and fail the check rather than pass it.
    """
    for line in step.split("\n"):
        if line.startswith("**`") and "→" in line and arrow_target in line:
            return set(PROVENANCES.findall(line.split("→")[0]))
    return None


def fixed_dataset_problems(phase1):
    """Criterion 5: `cord` and `free_data` get no return, a statement and no 👉."""
    step = between(phase1, STEP_7B, END_OF_PHASE)
    if step is None:
        return ["Step 7b is missing"]
    problems = []
    variant = provenance_lead(step, "no-progress variant")
    if variant != {"synthesized", "own", "unknown"}:
        problems.append("the no-progress variant (with its return) is offered to %r; it must be "
                        "exactly synthesized, own and unknown" % (sorted(variant or ()),))
    fixed = provenance_lead(step, "no return")
    if fixed != {"cord", "free_data"}:
        problems.append("the no-return statement covers %r; it must be cord and free_data"
                        % (sorted(fixed or ()),))
    block = between(step, "**`cord` or `free_data` →", "**Handling each answer")
    if block is None:
        problems.append("Step 7b has no fixed-dataset block")
    else:
        f = flat(block)
        for needle in ("completeness cannot change", "no 👉", "continue into Phase 2",
                       "in the same turn", "results may be limited"):
            if needle not in f:
                problems.append("the fixed-dataset block does not say %r" % needle)
        if re.search(r"👉\s*\*\*", block):
            problems.append("the fixed-dataset block carries a 👉 question")
    table = between(step, "| `provenance` |", "\n\n")
    # Line-scoped by design (#424): a table row is one line.
    if table is not None:
        rows = set(PROVENANCES.findall(" ".join(
            l.strip().strip("|").split("|")[0] for l in table.split("\n")[2:]
            if l.strip().startswith("|"))))
        if rows & {"cord", "free_data"}:
            problems.append("the return table routes a fixed dataset: %r"
                            % sorted(rows & {"cord", "free_data"}))
    return problems


def handling_problems(phase1):
    """Criteria 6 and 8: the handling step names Module 4's steps and Module 5's resume step."""
    step = between(phase1, STEP_7B, END_OF_PHASE)
    if step is None:
        return ["Step 7b is missing"]
    route = between(step, "**The return route", END_OF_PHASE)
    if route is None:
        return ["Step 7b has no return-route handling step (INV-284)"]
    problems = []
    f = flat(route)
    for needle in ('"collection_return"', '"source"', '"resume_step"',
                   "current_module is not changed", "receiving-a-collection-return"):
        if needle not in route.replace("`", "") and needle not in f.replace("`", ""):
            problems.append("the return route does not carry %r" % needle)
    rows = {}
    # Line-scoped by design (#424): a table row is one line.
    for line in route.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and PROVENANCES.fullmatch(cells[0]):
            rows[cells[0].strip("`")] = cells
    expected = {
        "synthesized": (("Step 2",), "Step 6"),
        "own": (("Step 2", "Step 3", "Step 8", "Step 8a"), "Step 4"),
        "unknown": (("as `own`",), "Step 4"),
    }
    for prov, (m4_steps, resume) in expected.items():
        if prov not in rows:
            problems.append("the return table has no %s row" % prov)
            continue
        _, runs, resumes = rows[prov]
        for s in m4_steps:
            if s not in runs:
                problems.append("%s: the Module 4 steps do not include %s" % (prov, s))
        if resume not in resumes:
            problems.append("%s: Module 5 does not resume at %s" % (prov, resume))
    if "regenerating this source only to `>=80`" not in route:
        problems.append("the synthesized row does not target >=80")
    step9 = re.search(r"Step 9 does not run at all on a return:?\*?\*? no Module Completion, no "
                      r"second Module 4 recap section, no progress update and no transition "
                      r"question", re.sub(r"\s+", " ", route))
    if not step9:
        problems.append("the route does not say Module 4's Step 9 does not run at all")
    if not re.search(r"(?i)NOT an INV-006 repeat", f):
        problems.append("the resume does not sanction re-presenting the gate (INV-284)")
    return problems


def citing_sites_problems(phase1):
    """INV-300: the gate, the disclosure and Step 7a cite Step 7b instead of restating it."""
    problems = []
    gate = between(phase1, GATE, STEP_7A)
    if gate is None:
        return ["the Quality gate section moved"]
    for band in ("**Quality 70-79%**", "**Quality <70%**"):
        bullet = between(gate, band, "👉")
        if bullet is None or "Step 7b" not in bullet:
            problems.append("the %s gate does not point at Step 7b's variant" % band)
    disclosure = between(gate, "Then present the", "⛔ **Never")
    if disclosure is None or "applicable pinned question" not in flat(disclosure) \
            or "Step 7b" not in disclosure:
        problems.append("the synthesized-source disclosure does not say the applicable pinned "
                        "question (the band's, or Step 7b's variant)")
    step7a = between(phase1, STEP_7A, STEP_7B)
    if step7a is None:
        return problems + ["Step 7a moved"]
    two = between(step7a, "Not fixable here", "\n3. ")
    if two is None or "Step 7b" not in two or re.search(r"(?i)offer a return to that module", two):
        problems.append("Step 7a step 2 restates the return instead of citing Step 7b")
    six = between(step7a, "6. **When nothing was fixable", "\n\n")
    if six is None or "Step 7b" not in six:
        problems.append("Step 7a step 6 does not hand over to Step 7b")
    step = between(phase1, STEP_7B, END_OF_PHASE) or ""
    if not re.search(r"INV-300\)? This is the canonical statement", flat(step)):
        problems.append("Step 7b does not declare itself the canonical statement (INV-300)")
    return problems


def receiving_problems(module4):
    """Criteria 7 and 9: Module 4 Step 2 receives a `collection_return`."""
    block = between(module4, ANCHOR, MARKER_GUARD)
    if block is None:
        return ["Module 4 Step 2 has no 'Receiving a collection_return' branch"]
    step2 = between(module4, "### 2. ", "### 3. ") or ""
    if ANCHOR not in step2:
        return ["the receiving branch is not inside Module 4 Step 2"]
    problems = []
    f = flat(block)
    for needle in ("Receiving a `collection_return`", "provenance: synthesized` →",
                   "provenance: own` or `unknown` →", "handled exactly as `own`",
                   "Step 7b", "INV-300", ">=80", "-regenerated.", "same `RECORD_ID`s",
                   "previous `file_path`", "Step 7a step 4", "identifier collisions",
                   "never adjust a score", "no off-pattern values",
                   # A return writes no Module 4 checkpoint, so Module 5's progress survives.
                   "leave `current_module` and `current_step` as Module 5 set them",
                   # An own/unknown re-export never overwrites what was collected (INV-050).
                   "beside the original under a new name, never over it (INV-050)"):
        if needle.lower() not in f.lower():
            problems.append("the receiving branch does not say %r" % needle)
    yaml = re.search(r"```yaml\n(.*?)```", block, re.S)
    if not yaml:
        problems.append("the receiving branch has no quality_intent record of the regeneration")
    else:
        for key in ('target_band: ">=80"', "regenerated:", "from_band:", "reason:"):
            if key not in yaml.group(1):
                problems.append("the regeneration record lacks %r" % key)
    if "Return to Data collection for this source." in block:
        problems.append("the receiving branch restates Step 7b's pinned options (INV-300)")
    precondition = re.search(r"Only when the source has \*\*no\*\* recorded provenance.{0,300}?"
                             r"ask how they want to provide it", module4, re.S)
    if not precondition or "collection_return" not in precondition.group(0):
        problems.append("the provision question's precondition does not admit an own/unknown "
                        "collection_return")
    return problems


def step9_problems(module4):
    """Criterion 8: Step 9 opens by not running on a return."""
    step9 = between(module4, "### 9. Module completion", "\n## ")
    if step9 is None:
        return ["Module 4 Step 9 moved"]
    body = step9.split("\n", 1)[1].lstrip()
    if not body.startswith("**Not on a `collection_return`.**"):
        return ["Module 4 Step 9 does not open with 'Not on a collection_return'"]
    opener = flat(body.split("\n\n", 1)[0])
    problems = []
    for needle in ("does not run at all", "no Module Completion", "no second Module 4 recap",
                   "no progress update", "no transition question", "Step 7b"):
        if needle not in opener:
            problems.append("Step 9's opener does not say %r" % needle)
    return problems


def offered_returns(module_texts):
    """{module dir: the return keys its files start}, from each module's own files."""
    return {module: {key for key, pattern in OFFERS.items()
                     if any(pattern.search(flat(text)) for text in texts)}
            for module, texts in module_texts.items()}


def first_clause(skill):
    """The **First:** paragraph of a module's SKILL.md, or None."""
    return between(skill, "**First:**", "\n\n")


def routing_problems(module_texts, skills):
    """#598: every offering module's First: routes every return it offers (INV-366)."""
    problems = []
    for module, keys in sorted(offered_returns(module_texts).items()):
        for key in sorted(keys):
            clause = first_clause(skills.get(module, ""))
            if clause is None or ("When it carries a `%s`, none of this runs" % key) not in flat(
                    clause):
                problems.append("%s offers a %s but its First: does not route it"
                                % (module, key))
    return problems


def module5_first_problems(m5):
    """#598: Module 5's First: sends a collection_return to Step 7b item 4, before any apparatus."""
    clause = first_clause(m5)
    if clause is None:
        return ["Module 5 has no First: paragraph"]
    problems = []
    for needle in ("(INV-366) When it carries a `collection_return`, none of this runs",
                   "item 4", "does not re-present the gate",
                   "`current_module` stays this module"):
        if flat(needle) not in flat(clause):
            problems.append("Module 5's First: does not say %r" % needle)
    if ROUTE_LINK not in clause:
        problems.append("Module 5's First: does not link Step 7b's return route")
    return problems


def progress_problems(phase1, module4):
    """#598: the return records which Module 4 steps finished, and the resume reads it."""
    step = between(phase1, STEP_7B, END_OF_PHASE)
    if step is None:
        return ["Step 7b is missing"]
    problems = []
    if ROUTE_ANCHOR + "\n\n**The return route" not in step:
        problems.append("the return route has no anchor for Module 5's First: to link")
    record = re.search(r'```json\n\s*"collection_return": \{(.*?)\n\s*\}\n\s*```', step, re.S)
    if not record or '"completed": []' not in record.group(1):
        problems.append("the collection_return record has no completed list")
    four = between(step, "4. **(INV-366) An interrupted return", END_OF_PHASE)
    if four is None:
        problems.append("Step 7b has no item 4 for an interrupted return")
    else:
        f = flat(four)
        for needle in ("that is not listed in `completed`", "reads as `completed: []`",
                       "restarts at the row's first step", "do not re-present the gate"):
            if needle not in f:
                problems.append("Step 7b item 4 does not say %r" % needle)
        if "not yet done" in f:
            problems.append("Step 7b item 4 resumes from an unrecorded 'not yet done'")
    block = between(module4, ANCHOR, MARKER_GUARD)
    if block is None:
        return problems + ["Module 4 Step 2 has no receiving branch"]
    f = flat(block)
    for needle in ("(INV-366) In place of each step's Checkpoint:, add that step's number to the "
                   "record's `completed` in one quiet write",
                   '"Running it"', "Step 8a is added without running",
                   "resumes at the first step not listed there"):
        if needle not in f:
            problems.append("Module 4's receiving branch does not say %r" % needle)
    return problems


def module_texts():
    """{module dir: [text of each .md under it]} for every module, from the corpus (#598)."""
    out = {}
    for path in _corpus.corpus_files("plugins", suffixes={".md"}):
        parts = path.relative_to(SKILLS).parts if SKILLS in path.parents else ()
        if parts and parts[0].startswith("module-"):
            out.setdefault(parts[0], []).append(path.read_text(encoding="utf-8"))
    return out


def module_skills():
    return {d: (SKILLS / d / "SKILL.md").read_text(encoding="utf-8")
            for d in module_texts() if (SKILLS / d / "SKILL.md").is_file()}


# ----------------------------------------------------------------------------------- tests


class TheLiveFilesMeetEveryCriterion(unittest.TestCase):
    def setUp(self):
        self.phase1 = PHASE1.read_text(encoding="utf-8")
        self.module4 = MODULE4.read_text(encoding="utf-8")

    def test_the_files_are_found(self):
        """⛔ INV-265: a scan of a moved file certifies nothing."""
        self.assertIn(STEP_7B, self.phase1)
        self.assertIn(ANCHOR, self.module4)

    def test_both_bands_have_the_pinned_no_progress_variant(self):
        self.assertEqual([], variant_problems(self.phase1))

    def test_a_fixed_dataset_gets_no_return(self):
        self.assertEqual([], fixed_dataset_problems(self.phase1))

    def test_the_return_route_has_a_handling_step(self):
        self.assertEqual([], handling_problems(self.phase1))

    def test_the_other_sites_cite_step_7b(self):
        self.assertEqual([], citing_sites_problems(self.phase1))

    def test_module_4_receives_the_return(self):
        self.assertEqual([], receiving_problems(self.module4))

    def test_module_4_step_9_does_not_run_on_a_return(self):
        self.assertEqual([], step9_problems(self.module4))

    def test_the_variant_is_stated_once(self):
        """INV-300: the pinned return option appears in Step 7b and nowhere else.

        Four times there since #790: each band's question in its existing form and in its
        `synthesized` form, each carrying its own options.
        """
        option = "Return to Data collection for this source."
        hits = []
        for path in sorted(SKILLS.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            count = text.count(option)
            if count:
                hits.append((path.name, count))
        self.assertEqual([("phase1-quality-assessment.md", 4)], hits,
                         "the variant's return option is stated outside Step 7b, or not in it")
        self.assertEqual(4, between(self.phase1, STEP_7B, END_OF_PHASE).count(option),
                         "the return option is stated in Module 5 outside Step 7b")

    def test_every_offered_return_is_routed_by_its_offering_module(self):
        """#598: an offer is found from the files, and each offering module's First: routes it."""
        offers = offered_returns(module_texts())
        self.assertIn("collection_return", offers.get("module-05-data-quality-mapping", set()),
                      "the offer scan found no collection_return; it certifies nothing")
        self.assertGreaterEqual(sum(1 for keys in offers.values() if keys), 4,
                                "the offer scan found too few offering modules")
        self.assertEqual([], routing_problems(module_texts(), module_skills()))

    def test_module_5_first_sends_a_collection_return_to_item_4(self):
        self.assertEqual([], module5_first_problems(MODULE5_SKILL.read_text(encoding="utf-8")))

    def test_the_return_records_its_progress_and_resumes_from_it(self):
        self.assertEqual([], progress_problems(self.phase1, self.module4))

    def test_the_bands_original_questions_are_unchanged(self):
        """Blast radius: where mechanical work remains, the band's question stands as it was."""
        gate = between(self.phase1, GATE, STEP_7A)
        self.assertIn(["Improve the weakest fields first.", "Continue to mapping now."],
                      options_after(gate, BANDS["70-79"]))
        self.assertIn(["Work on improving the data first.",
                       "Proceed anyway, knowing the results may be limited."],
                      options_after(gate, BANDS["<70"]))


class EachCheckFailsWhenItsSiteIsRemoved(unittest.TestCase):
    """Negative controls: the same checks, run on mutated copies, must each report a problem."""

    def setUp(self):
        self.phase1 = PHASE1.read_text(encoding="utf-8")
        self.module4 = MODULE4.read_text(encoding="utf-8")
        self.step = between(self.phase1, STEP_7B, END_OF_PHASE)

    def mutate(self, old, new, text=None):
        text = self.phase1 if text is None else text
        self.assertIn(old, text, "negative control is stale: %r is gone" % old[:60])
        return text.replace(old, new, 1)

    def test_removing_the_variant_fails(self):
        variant = between(self.step, "- **Quality 70-79%:**", "- **Quality <70%:**")
        self.assertTrue(variant_problems(self.mutate(variant, "")))

    def test_an_improvement_option_in_the_variant_fails(self):
        mutated = self.mutate("  1. Return to Data collection for this source.\n"
                              "  2. Continue to mapping now.",
                              "  1. Improve the weakest fields first.\n"
                              "  2. Continue to mapping now.")
        self.assertTrue(any("dead choice" in p or "70-79" in p
                            for p in variant_problems(mutated)))

    def test_removing_the_return_handling_step_fails(self):
        route = between(self.step, "**The return route", END_OF_PHASE)
        self.assertTrue(handling_problems(self.mutate(route, "")))

    def test_a_wrong_resume_step_fails(self):
        mutated = self.mutate("| **Step 6** (re-score)", "| **Step 4** (re-score)")
        self.assertTrue(handling_problems(mutated))

    def test_removing_the_module_4_receiving_branch_fails(self):
        block = between(self.module4, ANCHOR, MARKER_GUARD)
        self.assertTrue(receiving_problems(self.module4.replace(block, "", 1)))

    def test_a_free_data_source_offered_a_return_fails(self):
        mutated = self.mutate("**`synthesized`, `own` or `unknown` → the pinned no-progress",
                              "**`synthesized`, `own`, `free_data` or `unknown` → the pinned "
                              "no-progress")
        mutated = mutated.replace("**`cord` or `free_data` → no return",
                                  "**`cord` → no return", 1)
        self.assertTrue(fixed_dataset_problems(mutated))

    def test_a_free_data_row_in_the_return_table_fails(self):
        mutated = self.mutate("   | `unknown` |",
                              "   | `free_data` | exactly as `own` | **Step 4** |\n"
                              "   | `unknown` |")
        self.assertTrue(fixed_dataset_problems(mutated))

    def test_restoring_the_old_step_7a_wording_fails(self):
        old = between(self.phase1, "Name it, and say it", "(INV-300).")
        mutated = self.mutate(old + "(INV-300).",
                              "offer a return to that module for this source, and say the "
                              "bootcamp will pick up here with the new file.")
        self.assertTrue(citing_sites_problems(mutated))

    def test_a_return_that_writes_module_4_checkpoints_fails(self):
        mutated = self.mutate("write no Module 4\ncheckpoint (leave `current_module` and "
                              "`current_step` as Module 5 set them, so its progress is not\n"
                              "overwritten),", "write Module 4 checkpoints as usual,",
                              self.module4)
        self.assertTrue(receiving_problems(mutated))

    def test_an_own_re_export_saved_over_the_original_fails(self):
        mutated = self.mutate("Save the new export beside the\n  original under a new name, "
                              "never over it (INV-050),", "Save the new export over the original,",
                              self.module4)
        self.assertTrue(receiving_problems(mutated))

    def test_dropping_module_5s_collection_return_route_fails(self):
        m5 = MODULE5_SKILL.read_text(encoding="utf-8")
        clause = first_clause(m5)
        start = clause.index("**(INV-366) When it carries a `collection_return`")
        mutated = m5.replace(clause[start:], "", 1)
        self.assertTrue(module5_first_problems(mutated))
        skills = dict(module_skills(), **{"module-05-data-quality-mapping": mutated})
        self.assertTrue(routing_problems(module_texts(), skills))

    def test_an_offer_without_a_route_fails(self):
        """A module that starts a return its First: does not route is caught (derived offers)."""
        texts = module_texts()
        texts["module-07-query-visualize-discover"].append(
            '```json\n"collection_return": {\n}\n```')
        self.assertTrue(any("module-07" in p and "collection_return" in p
                            for p in routing_problems(texts, module_skills())))

    def test_a_record_without_completed_fails(self):
        mutated = self.mutate('     "completed": [],\n', "")
        self.assertTrue(progress_problems(mutated, self.module4))

    def test_the_old_resume_clause_fails(self):
        four = between(self.phase1, "4. **(INV-366) An interrupted return", END_OF_PHASE)
        old = ('4. **(INV-366) An interrupted return** resumes from `current_step: "7b"` with '
               "`collection_return` present:\n   continue the return for the named source from "
               "the first Module 4 step not yet done, and do not\n   re-present the gate, whose "
               "answer is already recorded.\n\n")
        self.assertTrue(progress_problems(self.mutate(four, old), self.module4))

    def test_a_receiving_branch_that_records_no_progress_fails(self):
        sentence = between(self.module4, "⛔ **(INV-366) In place of each step's",
                           "Which steps run and where Module 5")
        mutated = self.mutate(sentence, "", self.module4)
        self.assertTrue(progress_problems(self.phase1, mutated))

    def test_removing_the_route_anchor_fails(self):
        self.assertTrue(progress_problems(self.mutate(ROUTE_ANCHOR + "\n\n", ""), self.module4))

    def test_removing_the_step_9_opener_fails(self):
        opener = between(self.module4, "**Not on a `collection_return`.**", "Run the standard")
        self.assertTrue(step9_problems(self.module4.replace(opener, "", 1)))


if __name__ == "__main__":
    unittest.main()
