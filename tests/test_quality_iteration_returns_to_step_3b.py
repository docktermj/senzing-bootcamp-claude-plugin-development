"""Module 7 step 3b's return to Data Quality, Mapping, and Transformation has a receiving side.

Step 3b asked "Would you like to return to the Data Quality, Mapping, and Transformation module
to refine your data mapping?" and, on yes, wrote a `quality_iteration` key, moved
`current_module` to Module 5 and promised "after remapping, they'll reload the affected sources
and re-evaluate here". No file read the key, and neither Module 5 nor Module 6 had a branch that
returned to step 3b: an option with nothing to execute, which INV-284 calls unsatisfiable.

The fix follows the `collection_return` precedent (#346). The route is stated **once**, in step
3b → "The quality-iteration route" (INV-300), and the other sites receive or cite it:

* step 3b's accepted branch writes the key and `current_step: "3b"`, leaves `current_module`
  alone and asks no second confirmation (INV-006); Marginal's "iterate" enters the same route;
* Module 7's, Module 5's and Module 6's `SKILL.md` **First:** clauses say what happens when the
  key is present (Module 7 routes by `stage`);
* Module 5 Phase 2 and Module 6 Phase B each carry a "Receiving a `quality_iteration`" branch;
* the resume clears the key in one write and re-runs step 3b as a new state;
* Module 7's own recap section is where the iteration is recorded.

⛔ **Each check is a function of the file text, so the negative controls run the SAME check on a
mutated copy** (INV-265): restoring the old `current_module` write, removing a First: clause or a
receiving branch, skipping a fast-pathed named source, or dropping the delete, the INV-327
sentence or the one-write resume must each make it report a problem.

Source issue: #392. Invariants: INV-006, INV-177, INV-284, INV-300, INV-327.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M5 = SKILLS / "module-05-data-quality-mapping"
M6 = SKILLS / "module-06-data-processing"
M7 = SKILLS / "module-07-query-visualize-discover"
M7_PHASE1 = M7 / "phase1-query-visualize.md"
M5_PHASE2 = M5 / "phase2-data-mapping.md"
M6_PHASEB = M6 / "phaseB-load-first-source.md"

ANCHOR = '<a id="receiving-a-quality-iteration"></a>'
ROUTE_ANCHOR = '<a id="the-quality-iteration-route"></a>'
FEEDBACK = "**Module 5 feedback loop"
STEP_3C = "### 3c."
RECEIVING_END = "\n## "
KEY_FIELDS = ('"sources"', '"from_verdict"', '"stage"', '"completed"', '"started_at"')


def flat(text):
    return re.sub(r"\s+", " ", text).replace("**", "")


def between(text, start, end):
    """The text from `start` to the next `end`, or None when `start` is absent."""
    if start not in text:
        return None
    i = text.index(start)
    j = text.find(end, i + len(start))
    return text[i:j if j != -1 else len(text)]


def first_clause(skill):
    """The **First:** paragraph of a module SKILL.md."""
    return between(skill, "**First:**", "\n\n")


def missing(block, needles, where):
    f = flat(block).lower()
    return ["%s does not say %r" % (where, n) for n in needles if flat(n).lower() not in f]


# ---------------------------------------------------------------------------------- checks


def step_3b_problems(phase1):
    """Criteria 1, 2, 6 and 7: the accepted branch, Marginal's iterate, the resume."""
    loop = between(phase1, FEEDBACK, STEP_3C)
    if loop is None:
        return ["Module 7 step 3b's Module 5 feedback loop is missing"]
    problems = []
    if re.search(r"Set `current_module` to `data_quality_mapping`", loop):
        problems.append("step 3b still moves current_module to Module 5")
    if ROUTE_ANCHOR not in loop:
        return problems + ["step 3b has no quality-iteration route"]
    json_block = re.search(r'```json\n\s*"quality_iteration": \{(.*?)\}\n\s*```', loop, re.S)
    if not json_block:
        problems.append("the route does not write a quality_iteration key")
    else:
        for field in KEY_FIELDS:
            if field not in json_block.group(1):
                problems.append("the quality_iteration key lacks %s" % field)
    problems += missing(loop, (
        "Record the return in one quiet write",
        'set `current_step` to `"3b"`',
        "`current_module` is not changed",
        "(INV-006) The pinned question's yes IS the route's go-ahead, so ask no second "
        "confirmation",
        "Marginal's \"iterate\"",
        '`from_verdict: "marginal"`',
        "The Module 5 question above is not asked as well",
        "(INV-300) This is the canonical statement of the route",
        "set `stage` to `reload` and `completed` to `[]` in one write",
        "No module is completed on a return",
        "nothing added to `modules_completed` again",
        "no recap section for either",
    ), "step 3b's route")
    resume = between(loop, "**Resume here.**", "\n\n4. ")
    if resume is None:
        problems.append("the route has no resume step")
    else:
        problems += missing(resume, (
            'clear `quality_iteration` and set `current_step` to `"3b"` in one write',
            "re-run step 3b in full",
            "NOT an INV-006 repeat",
            "The return may be offered again",
        ), "the resume")
    interrupted = between(loop, "**An interrupted return**", "\n\n5. ")
    if interrupted is None:
        problems.append("the route does not say how an interrupted return resumes")
    else:
        problems += missing(interrupted, (
            "routes by `stage` to the first source not listed in `completed`",
            "Do not re-present the step-3b question",
        ), "the interrupted-return step")
    for target in ("phase2-data-mapping.md#receiving-a-quality-iteration",
                   "phaseB-load-first-source.md#receiving-a-quality-iteration"):
        if target not in loop:
            problems.append("the route does not point at %s" % target)
    return problems


def marginal_problems(phase1):
    """Criterion 2: the Marginal bullet hands "iterate" to the route."""
    bullet = between(phase1, "- **Marginal:**", "- **Poor:**")
    if bullet is None:
        return ["the Marginal bullet moved"]
    if "#the-quality-iteration-route" not in bullet:
        return ["the Marginal bullet does not send \"iterate\" to the quality-iteration route"]
    return []


def first_clause_problems(skills):
    """Criterion 3: three First: clauses say what happens when the key is present."""
    problems = []
    for name, skill in skills.items():
        clause = first_clause(skill)
        if clause is None:
            problems.append("%s has no **First:** paragraph" % name)
            continue
        if "When it carries a `quality_iteration`, none of this runs" not in clause.replace(
                "**", ""):
            problems.append("%s **First:** does not skip the start apparatus on a "
                            "quality_iteration" % name)
            continue
        if name == "module-07":
            for needle in ("Route by its `stage`", "`remap` goes to Module 5",
                           "`reload` goes to Module 6",
                           "phase2-data-mapping.md#receiving-a-quality-iteration",
                           "phaseB-load-first-source.md#receiving-a-quality-iteration",
                           "Do not re-present the step-3b question"):
                if flat(needle) not in flat(clause):
                    problems.append("Module 7 **First:** does not say %r" % needle)
        else:
            if "#receiving-a-quality-iteration" not in clause:
                problems.append("%s **First:** does not point at its receiving branch" % name)
    return problems


def m5_receiving_problems(phase2):
    """Criterion 4: Module 5 Phase 2's receiving branch."""
    block = between(phase2, ANCHOR, "## Skip fast-pathed sources")
    if block is None:
        return ["Module 5 Phase 2 has no 'Receiving a quality_iteration' branch"]
    problems = missing(block, (
        "Receiving a `quality_iteration`",
        "whose `stage` is `remap`",
        "write no Module 5 checkpoint",
        "leave `current_module` and `current_step` as Module 7 set them",
        "Run Steps 8–18 for this source",
        "full `mapping_workflow` run",
        "(INV-177) Step 19's relocation guard runs between sources",
        "Phase 1, Phase 3 and Step 20 do not run",
        "`data_quality_mapping` is not added to `modules_completed` again",
        "set `stage` to `reload` and `completed` to `[]` in one write",
        "_loaded_record_ids.txt",
        "A named source with `fast_pathed: true` is remapped too",
        "\"Skip fast-pathed sources\" below does not apply to a source the key names",
        "also sets `fast_pathed: false`",
        "INV-300",
    ), "Module 5's receiving branch")
    if "phaseB-load-first-source.md#receiving-a-quality-iteration" not in block:
        problems.append("Module 5's receiving branch does not continue into Module 6's")
    return problems


def m6_receiving_problems(phaseb):
    """Criterion 5: Module 6 Phase B's receiving branch."""
    block = between(phaseb, ANCHOR, "## 5. ")
    if block is None:
        return ["Module 6 Phase B has no 'Receiving a quality_iteration' branch"]
    problems = missing(block, (
        "Receiving a `quality_iteration`",
        "whose `stage` is `reload`",
        "write no Module 6 checkpoint",
        "leave `current_module` and `current_step` as Module 7 set them",
        "Phase A runs only when the source's input path changed",
        "Compare the RECORD_ID sets before the reload",
        "Delete the records whose RECORD_IDs no longer appear",
        "never one from memory",
        "sdk_guide(topic='delete', language='<chosen_language>')",
        "get_sdk_reference(topic='parameters', filter='delete_record', "
        "language='<chosen_language>')",
        "Data Source Records (DSRs) Explained",
        "`phaseB-load-first-source.md` Step 7 (below) on a single-source run",
        "`phaseC-multi-source.md` Step 19 for this source alone",
        "`load_status`",
        "process redo once",
        "Step 9 below",
        "Step 20",
        "(INV-327) This deliberate replacement by record key is not the first-source reload "
        "INV-327 forbids",
        "Phase D and Module 6's completion step do not run",
        "`data_processing` is not added to `modules_completed` again",
        "INV-300",
    ), "Module 6's receiving branch")
    return problems


def recap_problems(phase1):
    """Criterion 8: Module 7's own recap section records the iteration."""
    completion = between(phase1, "## Module completion", "👉")
    if completion is None:
        return ["Module 7's Module completion section moved"]
    return missing(completion, (
        "The Module 7 recap section records every quality iteration",
        "module_7_query.quality_iterations",
        "before and after",
        "(INV-284) This section is the only record of it",
    ), "Module 7's Module completion")


# ----------------------------------------------------------------------------------- tests


def read_all():
    return {
        "phase1": M7_PHASE1.read_text(encoding="utf-8"),
        "phase2": M5_PHASE2.read_text(encoding="utf-8"),
        "phaseb": M6_PHASEB.read_text(encoding="utf-8"),
        "skills": {
            "module-05": (M5 / "SKILL.md").read_text(encoding="utf-8"),
            "module-06": (M6 / "SKILL.md").read_text(encoding="utf-8"),
            "module-07": (M7 / "SKILL.md").read_text(encoding="utf-8"),
        },
    }


class TheLiveFilesMeetEveryCriterion(unittest.TestCase):
    def setUp(self):
        self.f = read_all()

    def test_the_files_are_found(self):
        """⛔ INV-265: a scan of a moved file certifies nothing."""
        self.assertIn(ROUTE_ANCHOR, self.f["phase1"])
        self.assertIn(ANCHOR, self.f["phase2"])
        self.assertIn(ANCHOR, self.f["phaseb"])

    def test_step_3b_writes_the_key_and_resumes_in_one_write(self):
        self.assertEqual([], step_3b_problems(self.f["phase1"]))

    def test_marginal_iterate_enters_the_route(self):
        self.assertEqual([], marginal_problems(self.f["phase1"]))

    def test_three_first_clauses_handle_the_key(self):
        self.assertEqual([], first_clause_problems(self.f["skills"]))

    def test_module_5_receives_the_remap(self):
        self.assertEqual([], m5_receiving_problems(self.f["phase2"]))

    def test_module_6_receives_the_reload(self):
        self.assertEqual([], m6_receiving_problems(self.f["phaseb"]))

    def test_module_7_recap_records_the_iteration(self):
        self.assertEqual([], recap_problems(self.f["phase1"]))

    def test_the_route_is_stated_once(self):
        """INV-300: the key's JSON shape appears in step 3b and nowhere else."""
        hits = sorted(p.name for p in SKILLS.rglob("*.md")
                      if '"quality_iteration": {' in p.read_text(encoding="utf-8"))
        self.assertEqual(["phase1-query-visualize.md"], hits)


class EachCheckFailsWhenItsSiteIsRemoved(unittest.TestCase):
    """Negative controls: the same checks, run on mutated copies, must each report a problem."""

    def setUp(self):
        self.f = read_all()

    def mutate(self, text, old, new=""):
        self.assertIn(old, text, "negative control is stale: %r is gone" % old[:60])
        return text.replace(old, new, 1)

    def test_restoring_the_old_current_module_write_fails(self):
        mutated = self.mutate(self.f["phase1"], "1. **Record the return in one quiet write**",
                              "1. Set `current_module` to `data_quality_mapping` and "
                              "`current_step` to the Phase 2 start step.\n\n"
                              "1. **Record the return in one quiet write**")
        self.assertTrue(step_3b_problems(mutated))

    def test_dropping_a_key_field_fails(self):
        mutated = self.mutate(self.f["phase1"], '     "completed": [],\n')
        self.assertTrue(any("completed" in p for p in step_3b_problems(mutated)))

    def test_a_second_confirmation_fails(self):
        mutated = self.mutate(self.f["phase1"], "so ask no second confirmation",
                              "so confirm once more before starting")
        self.assertTrue(step_3b_problems(mutated))

    def test_a_two_write_resume_fails(self):
        mutated = self.mutate(self.f["phase1"],
                              'clear `quality_iteration` and set `current_step`\n   to `"3b"` in '
                              'one write.',
                              'clear `quality_iteration`, then set `current_step` to `"3b"`.')
        self.assertTrue(step_3b_problems(mutated))

    def test_a_marginal_bullet_that_asks_again_fails(self):
        mutated = self.mutate(self.f["phase1"], "[the quality-iteration route]"
                              "(#the-quality-iteration-route) below",
                              "the Module 5 question below")
        self.assertTrue(marginal_problems(mutated))

    def test_removing_a_first_clause_fails(self):
        for name in ("module-05", "module-06", "module-07"):
            skills = dict(self.f["skills"])
            skills[name] = self.mutate(skills[name],
                                       "**When it carries a `quality_iteration`, none of this "
                                       "runs:**", "")
            self.assertTrue(first_clause_problems(skills), name)

    def test_removing_the_module_5_branch_fails(self):
        block = between(self.f["phase2"], ANCHOR, "## Skip fast-pathed sources")
        self.assertTrue(m5_receiving_problems(self.mutate(self.f["phase2"], block)))

    def test_a_module_5_branch_without_the_relocation_guard_fails(self):
        mutated = self.mutate(self.f["phase2"], "(INV-177) Step 19's relocation guard runs "
                              "between sources", "(INV-177) relocation is optional")
        self.assertTrue(m5_receiving_problems(mutated))

    def test_a_module_5_branch_that_skips_a_fast_pathed_source_fails(self):
        """A fast-pathed named source must be remapped, not silently skipped (#392)."""
        mutated = self.mutate(self.f["phase2"], "**A named source with `fast_pathed: true` is "
                              "remapped too:**", "**A named source with `fast_pathed: true` is "
                              "skipped:**")
        self.assertTrue(m5_receiving_problems(mutated))

    def test_a_remap_that_leaves_fast_pathed_set_fails(self):
        mutated = self.mutate(self.f["phase2"], "Step 17's registry write also sets "
                              "`fast_pathed:\n   false`", "Step 17's registry write leaves "
                              "the flags")
        self.assertTrue(m5_receiving_problems(mutated))

    def test_removing_the_module_6_branch_fails(self):
        block = between(self.f["phaseb"], ANCHOR, "## 5. ")
        self.assertTrue(m6_receiving_problems(self.mutate(self.f["phaseb"], block)))

    def test_a_reload_without_the_delete_fails(self):
        mutated = self.mutate(self.f["phaseb"], "3. **Delete the records whose RECORD_IDs no "
                              "longer appear,**", "3. **Keep every loaded record,**")
        self.assertTrue(m6_receiving_problems(mutated))

    def test_dropping_the_inv_327_sentence_fails(self):
        mutated = self.mutate(self.f["phaseb"], "This deliberate replacement by record key is "
                              "not the first-source reload INV-327\nforbids.", "")
        self.assertTrue(m6_receiving_problems(mutated))

    def test_a_reload_that_runs_phase_d_fails(self):
        mutated = self.mutate(self.f["phaseb"], "**Phase D and Module 6's completion step do "
                              "not run.**", "**Then run Phase D and complete the module.**")
        self.assertTrue(m6_receiving_problems(mutated))

    def test_removing_the_recap_record_fails(self):
        para = between(self.f["phase1"], "**The Module 7 recap section records every quality "
                       "iteration.**", "\n\n")
        self.assertTrue(recap_problems(self.mutate(self.f["phase1"], para)))


if __name__ == "__main__":
    unittest.main()
