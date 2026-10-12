"""Switching to PostgreSQL at Data collection or Data processing is a detour through SDK setup.

Module 6 Phase A's SQLite volume pre-load check offered "Migrate to PostgreSQL" and handed off to
"the database-migration guidance … see the graduation migration checklist", and Module 4 Step 8b's
"Switch to an alternative database like PostgreSQL" (recorded as `switch_db`) routed to the
unported Kiro `DATABASE_MIGRATION.md`. Neither guidance exists at that point, and neither said
whether or where the flow resumed (INV-284). #528 routes both through Module 2's PostgreSQL setup
as a detour and back.

The detour is generic (strategy B): SDK setup carries one "Receiving a `setup_detour`" branch
keyed on a record that names its steps and its return point, with one table row per kind of
detour. The database switch is its first row; a later detour (#530's SDK repair from Module 5
Phase 3) adds a row, not a branch. The branch is the one statement of the detour (INV-300), and
the two offering options name the steps and where the flow resumes.

The checks, one per acceptance criterion:

* both options name the Module 2 steps the detour runs and where the flow resumes;
* the detour completes no module and writes no Module 2 checkpoint, and an interrupted detour
  resumes from its key (the three **First:** clauses route to the branch);
* after a Module 6 switch the loader gets its PostgreSQL worker count before Phase B (INV-296);
* a detour that cannot finish leaves `database_type: sqlite` and asks the original question
  again, naming the failure, as a new state (INV-284), never an INV-006 repeat;
* neither file still points at migration guidance that does not exist.

⛔ **Each check is a function of the file text, so the negative controls run the SAME check on a
mutated copy** (INV-265). Prose is matched with whitespace collapsed (INV-346), and a re-wrap
control re-flows every site to a narrow column and asserts the checks still pass.

Source issue: #528 (part of #504). Invariants: INV-006, INV-089, INV-284, INV-296, INV-300,
INV-349.

Run:  python3 -m unittest discover -s tests
"""
import re
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
M4 = SKILLS / "module-04-data-collection" / "SKILL.md"
M6 = SKILLS / "module-06-data-processing" / "SKILL.md"
M6_PHASE_A = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"
PREPARATION = SKILLS / "bootcamp-preparation" / "SKILL.md"

ANCHOR = '<a id="receiving-a-setup-detour"></a>'
LINK = "#receiving-a-setup-detour"
STEPS = ["7-postgresql", "8", "8a", "9", "register-sources"]
RECORD_FIELDS = ('"purpose"', '"steps"', '"completed"', '"return_to"', '"module"', '"resume"',
                 '"reask"', '"started_at"')


def flat(text):
    """Whitespace collapsed and bold markers dropped, so a line wrap never hides a phrase."""
    return re.sub(r"\s+", " ", text).replace("**", "")


def loose(phrase):
    """A pattern for `phrase` that matches across a line wrap (INV-346)."""
    if phrase.startswith("\n"):
        return re.compile(re.escape(phrase))
    return re.compile(r"\s+".join(re.escape(w) for w in phrase.split()))


def between(text, start, end):
    """The text from `start` to the next `end`, or None when `start` is absent.

    Both are matched across a line wrap, so a re-flowed site is still found.
    """
    m = loose(start).search(text)
    if m is None:
        return None
    n = loose(end).search(text, m.end())
    return text[m.start():n.start() if n else len(text)]


def missing(block, needles, where):
    f = flat(block)
    return ["%s does not say %r" % (where, n) for n in needles if flat(n) not in f]


def first_clause(skill):
    return between(skill, "**First:**", "\n\n")


def receiving_branch(m2):
    return between(m2, ANCHOR, "\n## Step 1:")


def m4_switch_bullet(m4):
    return between(m4, "- **Switch to an alternative database (e.g. PostgreSQL):**",
                   "4. **Record the decision.**")


def m6_migrate_bullet(phase_a):
    return between(phase_a, "- **Migrate to PostgreSQL:**", "   In both branches")


# ---------------------------------------------------------------------------------- checks


def receiving_problems(m2):
    """The one branch: the record, the row, how it runs, finishes, hands back and resumes."""
    block = receiving_branch(m2)
    if block is None:
        return ["SDK setup has no 'Receiving a setup_detour' branch"]
    problems = []
    record = re.search(r'```json\n"setup_detour": \{(.*?)\n\}\n```', block, re.S)
    if not record:
        problems.append("the branch does not define the setup_detour record")
    else:
        body = record.group(1)
        problems += ["the record lacks %s" % f for f in RECORD_FIELDS if f not in body]
        steps = re.search(r'"steps": \[(.*?)\]', body)
        if not steps or re.findall(r'"([^"]+)"', steps.group(1)) != STEPS:
            problems.append("the record's steps are not the database switch's, in order")
    row = next((line for line in block.splitlines()
                if line.startswith("| `database_switch` |")), None)
    if row is None:
        problems.append("the detour table has no database_switch row")
    else:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) != 5:
            problems.append("the database_switch row does not have five cells")
        else:
            ids = re.findall(r"`([0-9a-z-]+)`:", cells[1])
            if ids != STEPS:
                problems.append("the row's steps %r are not %r" % (ids, STEPS))
            problems += missing(cells[1], (
                "Step 7](#step-7-configure-database)'s PostgreSQL branch, from its \"How would "
                "you like to run PostgreSQL?\" question",
                "`8`: Step 8.", "`8a`: Step 8a.", "`9`: Step 9.",
                "every source's `DATA_SOURCE` code registered in the new datastore",
            ), "the row's steps")
            problems += missing(cells[2], ("Write `database_type: postgresql`",
                                           "delete `config/engine_config.sqlite.json`"),
                                "the row's finish")
            problems += missing(cells[3], ("Restore `config/engine_config.json` from "
                                           "`config/engine_config.sqlite.json`",
                                           "it is still `sqlite`"), "the row's unfinished end")
            problems += missing(cells[4], ("Data collection Step 8b",
                                           "Data processing Phase A's SQLite volume pre-load "
                                           "check"), "the row's offering sites")
    problems += missing(block, (
        "(INV-284) Check for it before anything else in this module.",
        "show no start banner, journey map or overview, write no Module 2 checkpoint",
        "leave `current_module` and `current_step` as the offering module set them",
        "run only the steps the record names",
        "(INV-284) A detour completes no module: no Module Completion, no second Module 2 recap "
        "section, no progress update, no transition question, and `sdk_setup` is not added to "
        "`modules_completed` again",
        "This is the one statement of the detour (INV-300)",
        "A new detour adds a row to the table below, never a branch of its own",
        "add it to `completed` in one quiet write in place of that step's Checkpoint:",
        "The Step 7 database question is not asked",
        "(INV-284) Step 7's instruction 1 is not applied here: `database_type` stays `sqlite` "
        "until the "
        "detour finishes",
        "(INV-349)",
        "Option 4, \"Switch to SQLite\", ends the detour as one that cannot finish",
        "copy the SQLite one to `config/engine_config.sqlite.json`",
        "(INV-089)",
        "phaseA-build-loading.md#4a-register-the-data-source-codes-before-loading",
        "clear `setup_detour` in one write and return to `return_to.module` at "
        "`return_to.resume`",
        "Ask no question of your own here.",
        "never remove it",
        "say what failed in one line, then ask the `return_to.reask` step's question again",
        "(INV-284) That is a new state, NOT an INV-006 repeat",
        "the new answer replaces that record",
        "Continue at the first step in `steps` not listed in `completed`",
        "do not ask the offering module's question again",
    ), "SDK setup's receiving branch")
    return problems


def step_7_problems(m2):
    """Step 7's instruction 1 points at the branch, so a reader there knows the write waits."""
    step7 = between(m2, "## Step 7: Configure Database", "**For SQLite**")
    if step7 is None:
        return ["SDK setup's Step 7 moved"]
    problems = missing(step7, ("On a `setup_detour`, this write waits for the detour to finish",),
                       "Step 7's instruction 1")
    if LINK not in step7:
        problems.append("Step 7's instruction 1 does not link the receiving branch")
    return problems


def first_clause_problems(skills):
    """An interrupted detour resumes from its key: each First: clause routes to the branch."""
    problems = []
    for name, skill in skills.items():
        clause = first_clause(skill)
        if clause is None:
            problems.append("%s has no First: paragraph" % name)
            continue
        if "When it carries a `setup_detour`, none of this runs" not in flat(clause):
            problems.append("%s First: does not skip its start apparatus on a setup_detour"
                            % name)
        if LINK not in clause:
            problems.append("%s First: does not route a setup_detour to SDK setup's branch"
                            % name)
    return problems


def sender_problems(bullet, where, module, resume, reask, resumes_at):
    """Both options: the steps by name, the resume point, the record, and both endings."""
    if bullet is None:
        return ["%s has no switch option" % where]
    problems = missing(bullet, (
        "run the switch as a detour through SDK setup: Module 2 Step 7's PostgreSQL branch, "
        "then Steps 8, 8a and 9, then every source's `DATA_SOURCE` code registered in the new "
        "datastore",
        resumes_at,
        "Start it in one quiet write",
        "`purpose: \"database_switch\"`",
        "`return_to: {\"module\": \"%s\", \"resume\": \"%s\", \"reask\": \"%s\"}`"
        % (module, resume, reask),
        "(INV-284) `current_module` is not changed",
        "When it finishes, `database_type` is `postgresql`",
        "When it cannot finish, `database_type` is still `sqlite`: name the failure in one line",
    ), where)
    if "../module-02-sdk-setup/SKILL.md" + LINK not in bullet:
        problems.append("%s does not link SDK setup's receiving branch" % where)
    return problems


def m4_problems(m4):
    bullet = m4_switch_bullet(m4)
    problems = sender_problems(bullet, "Module 4 Step 8b's switch option", "data_collection",
                               "9", "8b", "The flow resumes at Step 9.")
    if bullet is None:
        return problems
    f = flat(bullet)
    record = f.find("record the decision (sub-step 4)")
    start = f.find("Start it in one quiet write")
    if record == -1 or start == -1 or record > start:
        problems.append("Step 8b does not record switch_db before the detour starts")
    problems += missing(bullet, (
        "set `current_step` to `\"8b\"`",
        "continue to Step 9",
        "ask sub-step 2's question again",
        "The answer replaces the `switch_db` marker",
    ), "Module 4 Step 8b's switch option")
    return problems


def m6_problems(phase_a):
    bullet = m6_migrate_bullet(phase_a)
    problems = sender_problems(bullet, "Module 6 Phase A's migrate option", "data_processing",
                               "phase-b", "sqlite-volume-check", "The flow resumes at Phase B.")
    if bullet is None:
        return problems
    if '`{decided: true, choice: "migrate", loadable, tier, raw_value}`' not in flat(bullet):
        problems.append("the migrate option no longer records sqlite_volume_prompt")
    problems += missing(bullet, (
        "(INV-296) Before the Phase B load, give the loader its PostgreSQL worker count.",
        "its `postgresql` bullet now governs, so take the tier's full concurrency",
        "rewrite the code comment that explained the reduction",
        "rebuild the loader if the language is compiled",
        "Then continue to Phase B.",
        "present item 4's question again",
        "Item 2 does not skip it on the recorded `migrate`",
        "the answer replaces that marker",
    ), "Module 6 Phase A's migrate option")
    return problems


#: The two stale hand-offs #528 removes, matched with whitespace collapsed.
STALE = (
    ("module-04", re.compile(r"DATABASE_MIGRATION\.md|database-migration guide", re.I)),
    ("phaseA", re.compile(r"database-migration guidance|migration guide are later porting"
                          r"|graduation migration checklist for PostgreSQL migration", re.I)),
)


def stale_problems(texts):
    """Neither file points at migration guidance that does not exist."""
    return ["%s still hands off to %r" % (name, m.group(0))
            for name, pattern in STALE
            for m in [pattern.search(flat(texts[name]))] if m]


def module_keys():
    """The module keys `modules_completed` uses, from Bootcamp preparation's module table."""
    return set(re.findall(r"^\| \d+ \| [^|]+ \| [^|]+ \| `([a-z_0-9]+)` \|",
                          PREPARATION.read_text(encoding="utf-8"), re.M))


# ----------------------------------------------------------------------------------- tests


def read_all():
    return {
        "module-02": M2.read_text(encoding="utf-8"),
        "module-04": M4.read_text(encoding="utf-8"),
        "module-06": M6.read_text(encoding="utf-8"),
        "phaseA": M6_PHASE_A.read_text(encoding="utf-8"),
    }


def skills_of(f):
    return {k: f[k] for k in ("module-02", "module-04", "module-06")}


class TheLiveFilesMeetEveryCriterion(unittest.TestCase):
    def setUp(self):
        self.f = read_all()

    def test_the_sites_are_found(self):
        """⛔ INV-265: a scan of a moved site certifies nothing."""
        self.assertIsNotNone(receiving_branch(self.f["module-02"]))
        self.assertIsNotNone(m4_switch_bullet(self.f["module-04"]))
        self.assertIsNotNone(m6_migrate_bullet(self.f["phaseA"]))

    def test_sdk_setup_receives_the_detour(self):
        self.assertEqual([], receiving_problems(self.f["module-02"]))

    def test_step_7_says_the_database_type_write_waits(self):
        self.assertEqual([], step_7_problems(self.f["module-02"]))

    def test_an_interrupted_detour_resumes_from_its_key(self):
        self.assertEqual([], first_clause_problems(skills_of(self.f)))

    def test_module_4_names_the_steps_and_resumes_at_step_9(self):
        self.assertEqual([], m4_problems(self.f["module-04"]))

    def test_module_6_names_the_steps_and_tunes_the_loader_before_phase_b(self):
        self.assertEqual([], m6_problems(self.f["phaseA"]))

    def test_no_stale_migration_hand_off_remains(self):
        self.assertEqual([], stale_problems(self.f))

    def test_the_record_is_defined_once(self):
        """INV-300: the record's JSON shape appears in SDK setup and nowhere else."""
        hits = sorted(str(p.relative_to(SKILLS)) for p in SKILLS.rglob("*.md")
                      if '"setup_detour": {' in p.read_text(encoding="utf-8"))
        self.assertEqual(["module-02-sdk-setup/SKILL.md"], hits)

    def test_the_return_modules_are_real_module_keys(self):
        keys = module_keys()
        self.assertIn("sdk_setup", keys, "the module table moved; this check certifies nothing")
        for module in ("data_collection", "data_processing"):
            self.assertIn(module, keys)


class EachCheckFailsWhenItsSiteIsBroken(unittest.TestCase):
    """Negative controls: the same checks, run on mutated copies, must each report a problem."""

    def setUp(self):
        self.f = read_all()

    def mutate(self, text, old, new=""):
        self.assertIn(old, text, "negative control is stale: %r is gone" % old[:60])
        return text.replace(old, new, 1)

    def test_removing_the_branch_fails(self):
        block = receiving_branch(self.f["module-02"])
        self.assertTrue(receiving_problems(self.mutate(self.f["module-02"], block)))

    def test_a_detour_that_completes_module_2_fails(self):
        mutated = self.mutate(self.f["module-02"], "⛔ **(INV-284) A detour completes no module:**",
                              "**Then run Module Completion for SDK setup:**")
        self.assertTrue(receiving_problems(mutated))

    def test_a_detour_that_writes_database_type_up_front_fails(self):
        mutated = self.mutate(self.f["module-02"], "⛔ **(INV-284) Step 7's\n  instruction 1 is "
                              "not applied here:**", "**Step 7's instruction 1 is applied first:**")
        self.assertTrue(receiving_problems(mutated))

    def test_a_record_missing_its_return_point_fails(self):
        mutated = self.mutate(self.f["module-02"], '    "reask": ')
        self.assertTrue(any("reask" in p for p in receiving_problems(mutated)))

    def test_a_row_that_drops_registration_fails(self):
        mutated = self.mutate(self.f["module-02"], " `register-sources`: every source's "
                              "`DATA_SOURCE` code registered in the new datastore", "")
        self.assertTrue(receiving_problems(mutated))

    def test_a_failure_that_asks_its_own_question_fails(self):
        mutated = self.mutate(self.f["module-02"], "Ask no question of your own here.",
                              "Ask whether to retry.")
        self.assertTrue(receiving_problems(mutated))

    def test_a_reask_suppressed_as_a_repeat_fails(self):
        mutated = self.mutate(self.f["module-02"], "That is a new state, NOT an INV-006 repeat",
                              "Do not repeat the question (INV-006)")
        self.assertTrue(receiving_problems(mutated))

    def test_an_interrupted_detour_that_asks_again_fails(self):
        mutated = self.mutate(self.f["module-02"], "and do not ask the offering\nmodule's question "
                              "again", "and ask the offering module's question again")
        self.assertTrue(receiving_problems(mutated))

    def test_removing_the_step_7_pointer_fails(self):
        para = between(self.f["module-02"], "   **On a `setup_detour`, this write waits",
                       "\n\n")
        self.assertTrue(step_7_problems(self.mutate(self.f["module-02"], para)))

    def test_removing_a_first_clause_fails(self):
        for name in ("module-02", "module-04", "module-06"):
            skills = skills_of(self.f)
            clause = first_clause(skills[name])
            start = loose("**When it carries a `setup_detour`").search(clause).start()
            skills[name] = self.mutate(skills[name], clause[start:])
            self.assertTrue(first_clause_problems(skills), name)

    def test_restoring_the_module_4_hand_off_fails(self):
        bullet = m4_switch_bullet(self.f["module-04"])
        old = ("- **Switch to an alternative database (e.g. PostgreSQL):** route the bootcamper "
               "to the\n     database-migration guide (the Kiro `docs/guides/DATABASE_MIGRATION.md`"
               " guide is a later\n     porting phase). Then record the decision (sub-step 4).\n\n")
        mutated = self.mutate(self.f["module-04"], bullet, old)
        self.assertTrue(m4_problems(mutated))
        self.assertTrue(stale_problems(dict(self.f, **{"module-04": mutated})))

    def test_module_4_starting_the_detour_before_recording_fails(self):
        mutated = self.mutate(self.f["module-04"], "record the decision (sub-step 4),\n     then "
                              "run the switch", "run the switch")
        mutated = self.mutate(mutated, "The answer replaces the `switch_db` marker.",
                              "The answer replaces the `switch_db` marker. Then record the "
                              "decision (sub-step 4).")
        self.assertTrue(m4_problems(mutated))

    def test_module_4_resuming_elsewhere_fails(self):
        mutated = self.mutate(self.f["module-04"], '"resume": "9"', '"resume": "8b"')
        self.assertTrue(m4_problems(mutated))

    def test_restoring_the_module_6_hand_off_fails(self):
        bullet = m6_migrate_bullet(self.f["phaseA"])
        old = ("- **Migrate to PostgreSQL:** record `sqlite_volume_prompt` = `{decided: true, "
               "choice:\n     \"migrate\", loadable, tier, raw_value}` in preferences, then hand "
               "off to the database-migration\n     guidance (PostgreSQL migration is a "
               "production follow-up; see the graduation migration checklist).\n\n")
        mutated = self.mutate(self.f["phaseA"], bullet, old)
        self.assertTrue(m6_problems(mutated))
        self.assertTrue(stale_problems(dict(self.f, phaseA=mutated)))

    def test_a_module_6_return_without_the_worker_count_fails(self):
        para = between(self.f["phaseA"], "⛔ **(INV-296) Before the Phase B load",
                       "Then continue to Phase B.")
        self.assertTrue(m6_problems(self.mutate(self.f["phaseA"], para)))

    def test_a_module_6_reask_that_item_2_skips_fails(self):
        mutated = self.mutate(self.f["phaseA"], "Item 2 does not skip it on the recorded "
                              "`migrate`,", "Item 2 skips it on the recorded `migrate`,")
        self.assertTrue(m6_problems(mutated))

    def test_a_failed_detour_that_keeps_postgresql_fails(self):
        for name, check in (("module-04", m4_problems), ("phaseA", m6_problems)):
            mutated = self.mutate(self.f[name], "**When it cannot finish,** `database_type` is "
                                  "still `sqlite`", "**When it cannot finish,** `database_type` "
                                  "is `postgresql`")
            self.assertTrue(check(mutated), name)

    def test_restoring_the_porting_note_fails(self):
        mutated = self.mutate(self.f["phaseA"], "`load_time_warning.py` are later porting",
                              "`load_time_warning.py`, and the migration\nguide are later porting")
        self.assertTrue(stale_problems(dict(self.f, phaseA=mutated)))

    def test_a_second_copy_of_the_record_is_caught(self):
        """The record-once check reads files on disk, so assert its predicate directly."""
        self.assertIn('"setup_detour": {', self.f["module-02"])
        self.assertNotIn('"setup_detour": {', self.f["phaseA"])


def rewrap(text, width=24):
    """Re-flow every prose line to a narrow column; fences, tables, headings and anchors stay."""
    out, fenced = [], False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fenced = not fenced
        if fenced or stripped.startswith(("```", "|", "#", "<a ", "<!--")) or not stripped:
            out.append(line)
            continue
        indent = line[:len(line) - len(stripped)]
        lead = re.match(r"(?:[-*] |\d+\. |> )*", stripped).group(0)
        out.append(textwrap.fill(stripped, width=width, initial_indent=indent,
                                 subsequent_indent=indent + " " * len(lead),
                                 break_long_words=False, break_on_hyphens=False))
    return "\n".join(out) + "\n"


class TheChecksSurviveARewrap(unittest.TestCase):
    """INV-346: a phrase split by a line wrap is still found."""

    def test_every_site_rewrapped_still_passes(self):
        f = {k: rewrap(v) for k, v in read_all().items()}
        self.assertNotEqual(read_all()["module-02"], f["module-02"], "the re-wrap changed nothing")
        self.assertEqual([], receiving_problems(f["module-02"]))
        self.assertEqual([], step_7_problems(f["module-02"]))
        self.assertEqual([], first_clause_problems(skills_of(f)))
        self.assertEqual([], m4_problems(f["module-04"]))
        self.assertEqual([], m6_problems(f["phaseA"]))
        self.assertEqual([], stale_problems(f))

    def test_a_rewrapped_regression_is_still_caught(self):
        f = read_all()
        mutated = f["module-02"].replace("Ask no question of your own here.",
                                         "Ask whether to retry.", 1)
        self.assertTrue(receiving_problems(rewrap(mutated)))


if __name__ == "__main__":
    unittest.main()
