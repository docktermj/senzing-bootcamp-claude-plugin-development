"""Module 5 Phase 3's offer to go back to SDK setup is a pinned question with a detour behind it.

Phase 3 offered SDK setup twice in prose: "Before starting Phase 3" said "complete SDK setup first
and return here", and step 21 said, when detection fails, "offer to skip this source's test load
or return to Module 2". Neither was a pinned question (INV-051, INV-056), and the return had no
handling: nothing said which Module 2 steps ran, that Module 2 must not complete again, or where
the flow came back (INV-284). #530 (part of #504) makes it one pinned repair-or-skip question.

The repair is a **detour, not a Module 2 run**, and it reuses SDK setup's existing "Receiving a
`setup_detour`" section (#528) by adding an `sdk_repair` row: Module 2 Step 1, which moves past
whatever is already in place, through Step 9. The receiving section is the one statement of a
detour (INV-300), so it already says a detour shows no banner, writes no Module 2 checkpoint and
completes no module.

Strategy B: the question and its handling are stated **once**, at "Before starting Phase 3", and
step 21 points to it (INV-300) instead of carrying a copy.

The checks:

* the single statement: the pinned 👉 question with its two numbered options, a handler for each
  answer that names where the flow resumes, the `setup_detour` record it writes, and the re-ask
  after a repeat detection failure as a new state, not an INV-006 repeat (INV-284);
* step 21 points to that statement, names where each answer resumes, and carries no second copy
  of the question;
* "Leaving Phase 3" has one row for the repair exit, resuming at Phase 3 step 21, and says it
  stays inside Phase 2's per-source loop (INV-344);
* SDK setup's receiving section has an `sdk_repair` row whose steps are every Module 2 step from
  Step 1 to Step 9, derived from the file's own `## Step` headings, and still states the
  no-completion rule; there is still exactly one receiving section;
* Module 5's **First:** clause sends an interrupted repair to that section;
* the places a reader passes on the way to the repair point to it by link and restate nothing
  (INV-300): Phase 3's entry note, "Phase 3 session resume", and Phase 2's step 18a and its step
  map's Phase 3 row (grafted from strategy A);
* the retired prose offers are gone;
* (#606) the two return-contract clauses it pins cite "(INV-366)" alone, each with its ⛔, so a
  clause reverted to the old "(INV-284, INV-366)" co-citation no longer matches;
* (#598, INV-364) Module 2 Step 7's Option 4, "Switch to SQLite", waits for the finish on a
  `setup_detour`: an `sdk_repair` continues to SQLite through it, and before #598 it rewrote
  `database_type` at once, so a repair that then failed had already changed it.

⛔ **Each check is a function of the file text, so the negative controls run the SAME check on a
mutated copy** (INV-265). Prose is matched with whitespace collapsed (INV-346), and a re-wrap
control re-flows every site to a narrow column and asserts the checks still pass. The tests
assert that the skill files *state* these rules and **cannot** establish that a live run follows
them, which only `dry-run` phase 3 can observe.

Source issue: #530 (part of #504). Invariants: INV-006, INV-051, INV-056, INV-284, INV-300,
INV-344.

Also enforces INV-366 (the cross-module return contract, registered 2026-10-13) for the `setup_detour` (the SDK repair):
it asserts the skill files *state* the contract and cannot establish that a live run follows it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from test_database_switch_detours_through_sdk_setup import (
    between, first_clause, flat, loose, missing, receiving_branch, rewrap)

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
M5 = SKILLS / "module-05-data-quality-mapping" / "SKILL.md"
PHASE3 = SKILLS / "module-05-data-quality-mapping" / "phase3-test-load.md"
PHASE2 = SKILLS / "module-05-data-quality-mapping" / "phase2-data-mapping.md"
PREPARATION = SKILLS / "bootcamp-preparation" / "SKILL.md"

QUESTION = ("👉 **Phase 3's test load needs a working Senzing SDK. What would you like to do? "
            "Reply with a number:**")
OPTION_1 = "1. Repair the SDK setup, then come back to this test load."
OPTION_2 = ("2. Skip the test load for this source and carry on mapping (the real load happens in "
            "Data processing).")
ANCHOR = '<a id="the-sdk-repair-question"></a>'
LINK = "#the-sdk-repair-question"
#: Phase 2's link to the statement, from the file beside it.
PHASE2_LINK = "phase3-test-load.md#the-sdk-repair-question"
RECEIVING_LINK = "../module-02-sdk-setup/SKILL.md#receiving-a-setup-detour"
RECEIVING_HEADING = "## Receiving a `setup_detour`"
#: The prose offers #530 replaces, matched with whitespace collapsed.
RETIRED = re.compile(r"(?i)complete SDK setup first and return here|or return to Module 2")


def before_block(p3):
    return between(p3, "**Before starting Phase 3:**", "## Workflow")


def step_21(p3):
    return between(p3, "### 21. SDK environment detection", "### 21a.")


def leaving(p3):
    return between(p3, "## Leaving Phase 3", "\n## ")


def entry_note(p3):
    block = between(p3, "**Entry from the Step 5", "\n\n")
    # The note is a blockquote: drop its markers so a wrap inside it never hides a phrase.
    return None if block is None else re.sub(r"(?m)^\s*>\s?", "", block)


def session_resume(p3):
    return between(p3, "## Phase 3 session resume", "\n## ")


def step_18a(p2):
    return between(p2, "### 18a.", "### 19.")


def step_map_row(p2):
    # Line-scoped by design (#530): a table row is one line.
    rows = [r for r in p2.splitlines() if r.startswith("| Phase 3 (21-25) |")]
    return rows[0] if len(rows) == 1 else None


# ---------------------------------------------------------------------------------- checks


def statement_problems(p3):
    """The one statement: the pinned question, both handlers, the record and the re-ask."""
    block = before_block(p3)
    if block is None:
        return ["Phase 3 has no 'Before starting Phase 3' block"]
    problems = []
    start = loose("**Before starting Phase 3:**").search(p3).start()
    if ANCHOR not in p3 or p3.index(ANCHOR) > start:
        problems.append("the SDK repair question has no anchor at 'Before starting Phase 3'")
    if block.count("👉") != 1:
        problems.append("'Before starting Phase 3' does not end on exactly one 👉 question")
    # INV-056 pins the wording verbatim; matched with whitespace collapsed (INV-346).
    for needle, what in ((QUESTION, "the pinned question"), (OPTION_1, "option 1, repair"),
                         (OPTION_2, "option 2, skip")):
        if flat(needle) not in flat(block):
            problems.append("'Before starting Phase 3' does not carry %s verbatim" % what)
    problems += missing(block, (
        "This is the one statement of that question and its handling (INV-300)",
        "step 21 asks it too, when detection fails, and points here",
        "*(Internal: end the turn on this question and wait.)*",
        "Handling each answer (INV-284)",
        "1, repair → a detour through SDK setup, not a run of it: Module 2 Step 1 (\"Check for "
        "Existing Installation\"), which moves past whatever is already in place, through Step 9 "
        "(\"Test Database Connection\")",
        "The flow resumes at step 21 for this source.",
        "Start it in one quiet write",
        "set `current_step` to `21`",
        "`purpose: \"sdk_repair\"`",
        "`return_to: {\"module\": \"data_quality_mapping\", \"resume\": \"21:<DATA_SOURCE>\", "
        "\"reask\": \"the-sdk-repair-question\"}`",
        "⛔ (INV-366) `current_module` is not changed",
        "resume without asking this question again",
        "That branch is the one statement of which steps run, that the detour completes no "
        "module, and how it ends (INV-300)",
        "When it finishes, run step 21 for the source `return_to.resume` names",
        "(INV-284) If detection fails again, ask this question again: that is a new state, NOT "
        "an INV-006 repeat",
        "the earlier answer does not suppress it",
        "When it cannot finish, name the failure in one line, then ask this question again",
        "2, skip → leave by the skip exit",
        "`test_load_status: skipped` for this source only, then Phase 2 step 19",
    ), "the SDK repair question's statement")
    if RECEIVING_LINK not in block:
        problems.append("the repair handler does not link SDK setup's receiving section")
    if '"setup_detour": {' in p3:
        problems.append("Phase 3 restates the setup_detour record instead of pointing to it")
    return problems


def step_21_problems(p3):
    """Step 21 points to the statement, names where each answer resumes, and copies nothing."""
    s21 = step_21(p3)
    if s21 is None:
        return ["Phase 3 has no step 21"]
    problems = missing(s21, (
        "If detection fails, say so in one line, then ask [the SDK repair question]",
        "which states the question and its handling once (INV-300)",
        "Its repair resumes at this step for this source",
        "skip this source's test load leaves by the skip exit",
        "for this source only, then Phase 2 step 19",
    ), "step 21")
    if LINK not in s21:
        problems.append("step 21 does not link the SDK repair question")
    if "👉" in s21 or "Reply with a number" in s21:
        problems.append("step 21 carries a second copy of the SDK repair question")
    for option in (OPTION_1[3:], OPTION_2[3:]):
        if flat(option) in flat(s21):
            problems.append("step 21 restates an option of the SDK repair question")
    return problems


def leaving_problems(p3):
    """One row for the repair exit, resuming at Phase 3 step 21, inside the per-source loop."""
    block = leaving(p3)
    if block is None:
        return ["Phase 3 has no Leaving Phase 3 section"]
    problems = missing(block, (
        "(INV-344) Every exit from Phase 3 returns to Phase 2's per-source loop.",
        "The SDK repair exit leaves for SDK setup and comes back to step 21 for this source only",
        "so it never leaves the loop: Phase 2's step 19 is still ahead of it",
        "A detour that cannot finish comes back to [the SDK repair question]",
    ), "Leaving Phase 3")
    # Line-scoped by design (#530): a table row is one line.
    rows = [r for r in block.splitlines() if r.startswith("| ") and "SDK repair" in r]
    if len(rows) != 1:
        problems.append("Leaving Phase 3 has %d rows for the SDK repair exit, not 1" % len(rows))
    else:
        cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        if len(cells) != 3:
            problems.append("the SDK repair row does not have three cells")
        else:
            if cells[2] != "Phase 3 step 21":
                problems.append("the SDK repair exit resumes at %r, not Phase 3 step 21"
                                % cells[2])
            if cells[1] != "unchanged":
                problems.append("the SDK repair exit writes this source's registry entry")
            problems += missing(cells[0], ("Before starting Phase 3", "step 21's detection "
                                           "failure", "the detour through SDK setup finishes"),
                                "the SDK repair row")
    return problems


def module_2_steps(m2):
    """Module 2's step ids from Step 1 to Step 9, in file order, from its own headings."""
    # Line-scoped by design (#530): a heading is one line.
    ids = re.findall(r"(?m)^## Step (\d+[a-z]?):", m2)
    if "1" not in ids or "9" not in ids:
        return []
    return ids[ids.index("1"):ids.index("9") + 1]


def receiving_problems(m2):
    """SDK setup's one receiving section gains the sdk_repair row, and says it completes nothing."""
    problems = []
    if m2.count(RECEIVING_HEADING) != 1 or m2.count('<a id="receiving-a-setup-detour"></a>') != 1:
        problems.append("SDK setup does not have exactly one 'Receiving a setup_detour' section")
    block = receiving_branch(m2)
    if block is None:
        return problems + ["SDK setup has no 'Receiving a setup_detour' section"]
    problems += missing(block, (
        "show no start banner, journey map or overview, write no Module 2 checkpoint",
        "⛔ (INV-366) A detour completes no module: no Module Completion, no second Module 2 recap "
        "section, no progress update, no transition question, and `sdk_setup` is not added to "
        "`modules_completed` again",
        "A new detour adds a row to the table below, never a branch of its own",
        "For `sdk_repair`:",
        "A step its path moves past",
        "is added to `completed` without running",
        "Step 1's \"Mark Module 2 as complete only after Step 9's engine-class check passes\" does "
        "not apply: a detour completes no module",
        "Step 7 runs as it states, from its database question",
        "Its instruction 1 waits for the finish",
        "\"Switch to SQLite\", is an answer here and not a stop",
        "on a `database_switch`, with Step 7's option 4",
    ), "SDK setup's receiving section")
    # Line-scoped by design (#530): a table row is one line.
    row = [line for line in block.splitlines() if line.startswith("| `sdk_repair` |")]
    if len(row) != 1:
        return problems + ["the detour table has no single sdk_repair row"]
    cells = [c.strip() for c in row[0].strip().strip("|").split("|")]
    if len(cells) != 5:
        return problems + ["the sdk_repair row does not have five cells"]
    ids = re.findall(r"`([0-9a-z-]+)`:", cells[1])
    expected = module_2_steps(m2)
    if not expected:
        problems.append("Module 2's Step 1 and Step 9 headings were not found")
    elif ids != expected:
        problems.append("the sdk_repair steps %r are not Module 2's Step 1 to Step 9, %r"
                        % (ids, expected))
    problems += missing(cells[1], ("[Step 1](#step-1-check-for-existing-installation-must-do-"
                                   "first), which moves past whatever is already in place",
                                   "[Step 9](#step-9-test-database-connection)"),
                        "the sdk_repair row's steps")
    problems += missing(cells[2], ("Write `database_type` by Step 7's instruction 1",),
                        "the sdk_repair row's finish")
    problems += missing(cells[3], ("`database_type` was never rewritten",),
                        "the sdk_repair row's unfinished end")
    problems += missing(cells[4], ("Data Quality, Mapping, and Transformation Phase 3's SDK repair "
                                   "question", "step 21 when detection fails"),
                        "the sdk_repair row's offering site")
    return problems


def first_clause_problems(m5):
    """An interrupted repair resumes from its key: Module 5's First: routes it to SDK setup."""
    clause = first_clause(m5)
    if clause is None:
        return ["Module 5 has no First: paragraph"]
    problems = missing(clause, (
        "When it carries a `setup_detour`, none of this runs either",
        "Phase 3's SDK repair is part-way through",
        "returns to Phase 3",
    ), "Module 5's First:")
    if RECEIVING_LINK not in clause:
        problems.append("Module 5's First: does not link SDK setup's receiving section")
    return problems


def restates(block):
    """True when a pointer carries the question or an option instead of linking it (INV-300)."""
    f = flat(block)
    return any(flat(n) in f for n in (QUESTION, OPTION_1[3:], OPTION_2[3:]))


def pointer_problems(p3, p2):
    """The places a reader passes on the way to the repair point to it by link (grafted from A)."""
    problems = []
    sites = (
        ("Phase 3's entry note", entry_note(p3), "#leaving-phase-3",
         ("every way out of it returns to Phase 2, or, for an SDK repair, to step 21 for this "
          "source",)),
        ("Phase 3 session resume", session_resume(p3), LINK,
         ("A progress file carrying a `setup_detour` does not reach this section first",
          "sends it to SDK setup, which finishes [the SDK repair](#the-sdk-repair-question) and "
          "returns to step 21")),
        ("Phase 2 step 18a", step_18a(p2), PHASE2_LINK,
         ("is a detour through SDK setup that comes back to Phase 3 step 21 for the same source",
          "so it leaves this loop no more than the test load itself does")),
        ("Phase 2's step map", step_map_row(p2), PHASE2_LINK,
         ("comes back to step 21",)),
    )
    for where, block, link, needles in sites:
        if block is None:
            problems.append("%s was not found" % where)
            continue
        problems += missing(block, needles, where)
        if link not in block:
            problems.append("%s does not link %s" % (where, link))
        if restates(block):
            problems.append("%s restates the SDK repair question instead of linking it" % where)
    return problems


def retired_problems(p3):
    m = RETIRED.search(flat(p3))
    return ["Phase 3 still carries the retired offer %r" % m.group(0)] if m else []


def option_4(m2):
    return between(m2, "**Option 4 — Switch to SQLite:**", "**Handling each answer (INV-284).**")


def option_4_problems(m2):
    """#598: Option 4's rewrite of `database_type` waits for a detour's finish (INV-364)."""
    block = option_4(m2)
    if block is None:
        return ["Module 2 Step 7 has no Option 4"]
    problems = missing(block, (
        "(INV-364) On a `setup_detour`, this waits for the finish",
        "writes `database_type` only when every step is done",
        "An `sdk_repair` that continues to SQLite and then cannot finish leaves `database_type` "
        "as it was",
    ), "Step 7's Option 4")
    if "(#receiving-a-setup-detour)" not in block:
        problems.append("Step 7's Option 4 does not link the receiving section")
    return problems


def all_problems(f):
    return (statement_problems(f["phase3"]) + step_21_problems(f["phase3"])
            + leaving_problems(f["phase3"]) + receiving_problems(f["module-02"])
            + first_clause_problems(f["module-05"]) + retired_problems(f["phase3"])
            + pointer_problems(f["phase3"], f["phase2"]) + option_4_problems(f["module-02"]))


def read_all():
    return {"phase3": PHASE3.read_text(encoding="utf-8"),
            "phase2": PHASE2.read_text(encoding="utf-8"),
            "module-02": M2.read_text(encoding="utf-8"),
            "module-05": M5.read_text(encoding="utf-8")}


# ----------------------------------------------------------------------------------- tests


class TheLiveFilesMeetEveryCriterion(unittest.TestCase):
    def setUp(self):
        self.f = read_all()

    def test_the_sites_are_found(self):
        """⛔ INV-265: a scan of a moved site certifies nothing."""
        self.assertIsNotNone(before_block(self.f["phase3"]))
        self.assertIsNotNone(step_21(self.f["phase3"]))
        self.assertIsNotNone(leaving(self.f["phase3"]))
        self.assertIsNotNone(receiving_branch(self.f["module-02"]))
        self.assertIsNotNone(entry_note(self.f["phase3"]))
        self.assertIsNotNone(session_resume(self.f["phase3"]))
        self.assertIsNotNone(step_18a(self.f["phase2"]))
        self.assertIsNotNone(step_map_row(self.f["phase2"]))
        self.assertGreaterEqual(len(module_2_steps(self.f["module-02"])), 9,
                                "Module 2's step headings moved; the row check certifies nothing")

    def test_before_phase_3_is_the_one_statement_of_the_question(self):
        self.assertEqual([], statement_problems(self.f["phase3"]))

    def test_step_21_points_to_it(self):
        self.assertEqual([], step_21_problems(self.f["phase3"]))

    def test_leaving_phase_3_has_the_repair_row(self):
        self.assertEqual([], leaving_problems(self.f["phase3"]))

    def test_sdk_setup_receives_the_repair_by_a_row(self):
        self.assertEqual([], receiving_problems(self.f["module-02"]))

    def test_an_interrupted_repair_resumes_from_its_key(self):
        self.assertEqual([], first_clause_problems(self.f["module-05"]))

    def test_the_ways_to_the_repair_point_to_it(self):
        self.assertEqual([], pointer_problems(self.f["phase3"], self.f["phase2"]))

    def test_option_4_waits_for_the_finish_on_a_detour(self):
        self.assertIsNotNone(option_4(self.f["module-02"]))
        self.assertEqual([], option_4_problems(self.f["module-02"]))

    def test_the_prose_offers_are_retired(self):
        self.assertEqual([], retired_problems(self.f["phase3"]))

    def test_the_return_module_is_a_real_module_key(self):
        keys = set(re.findall(r"^\| \d+ \| [^|]+ \| [^|]+ \| `([a-z_0-9]+)` \|",
                              PREPARATION.read_text(encoding="utf-8"), re.M))
        self.assertIn("sdk_setup", keys, "the module table moved; this check certifies nothing")
        self.assertIn("data_quality_mapping", keys)

    def test_the_question_is_asked_from_two_sites_and_stated_once(self):
        """INV-300: the pinned wording appears once in Phase 3, at its owner."""
        self.assertEqual(1, self.f["phase3"].count(QUESTION))


class EachCheckFailsWhenItsSiteIsBroken(unittest.TestCase):
    """Negative controls: the same checks, run on mutated copies, must each report a problem."""

    def setUp(self):
        self.f = read_all()

    def mutate(self, name, old, new=""):
        self.assertIn(old, self.f[name], "negative control is stale: %r is gone" % old[:60])
        return dict(self.f, **{name: self.f[name].replace(old, new, 1)})

    def assertCaught(self, f):
        self.assertNotEqual([], all_problems(f))
        self.assertNotEqual([], all_problems({k: rewrap(v) for k, v in f.items()}),
                            "a re-wrapped regression was missed")

    def test_the_question_removed(self):
        self.assertCaught(self.mutate("phase3", QUESTION + "\n", ""))

    def test_the_question_as_prose(self):
        self.assertCaught(self.mutate("phase3", QUESTION, "Ask whether to repair or skip."))

    def test_the_options_joined_with_or(self):
        self.assertCaught(self.mutate("phase3", OPTION_1 + "\n" + OPTION_2,
                                      "1. Repair the SDK setup or skip the test load."))

    def test_the_retired_prose_offer_restored(self):
        self.assertCaught(self.mutate("phase3", "say so in one line, then pin the SDK repair "
                                      "question below.", "inform the bootcamper they can skip, or "
                                      "complete SDK setup first and return here."))

    def test_step_21_copies_the_question(self):
        self.assertCaught(self.mutate("phase3", "**Checkpoint:** write step 21 to",
                                      QUESTION + "\n\n**Checkpoint:** write step 21 to"))

    def test_step_21_loses_its_pointer(self):
        self.assertCaught(self.mutate("phase3", "then ask [the SDK repair question]"
                                      "(#the-sdk-repair-question)", "then offer to return to "
                                      "Module 2"))

    def test_the_repair_resumes_elsewhere(self):
        self.assertCaught(self.mutate("phase3", '"resume": "21:<DATA_SOURCE>"', '"resume": "19"'))

    def test_the_repair_loses_its_reask(self):
        self.assertCaught(self.mutate("phase3", ', "reask": "the-sdk-repair-question"', ""))

    def test_a_repeat_failure_suppressed_as_a_repeat(self):
        self.assertCaught(self.mutate("phase3", "that is a new state, NOT an INV-006 repeat",
                                      "do not ask it again (INV-006)"))

    def test_the_repair_changes_current_module(self):
        self.assertCaught(self.mutate("phase3", "⛔ **(INV-366) `current_module` is not changed:**",
                                      "Set `current_module` to `sdk_setup`:"))

    def test_the_repair_clause_reverted_to_its_old_citation(self):
        """#606: the pin carries its ⛔, so the pre-#606 co-citation no longer matches."""
        self.assertCaught(self.mutate("phase3", "⛔ **(INV-366) `current_module` is not changed:**",
                                      "⛔ **(INV-284, INV-366) `current_module` is not changed:**"))

    def test_the_record_restated_in_phase_3(self):
        self.assertCaught(self.mutate("phase3", "**Checkpoint:** write step 21 to",
                                      '```json\n"setup_detour": {\n}\n```\n\n'
                                      "**Checkpoint:** write step 21 to"))

    def test_the_leaving_row_dropped(self):
        row = next(r for r in self.f["phase3"].splitlines() if r.startswith("| SDK repair"))
        self.assertCaught(self.mutate("phase3", row + "\n"))

    def test_the_leaving_row_retargeted(self):
        self.assertCaught(self.mutate("phase3", "| unchanged | Phase 3 step 21 |",
                                      "| unchanged | Data processing |"))

    def test_the_leaving_row_writes_the_registry(self):
        self.assertCaught(self.mutate("phase3", "| unchanged | Phase 3 step 21 |",
                                      "| `test_load_status: repaired` | Phase 3 step 21 |"))

    def test_the_sdk_repair_row_removed(self):
        row = next(r for r in self.f["module-02"].splitlines() if r.startswith("| `sdk_repair` |"))
        self.assertCaught(self.mutate("module-02", row + "\n"))

    def test_the_sdk_repair_row_skips_a_step(self):
        self.assertCaught(self.mutate("module-02", " `8a`: Step 8a. `9`: [Step 9]",
                                      " `9`: [Step 9]"))

    def test_a_second_receiving_branch(self):
        self.assertCaught(self.mutate("module-02", "## Step 1: Check for Existing Installation",
                                      RECEIVING_HEADING + " (from Phase 3)\n\nRun Steps 1 to 9.\n\n"
                                      "## Step 1: Check for Existing Installation"))

    def test_the_repair_completes_module_2(self):
        self.assertCaught(self.mutate("module-02", "⛔ **(INV-366) A detour completes no module:**",
                                      "**Then run Module Completion for SDK setup:**"))

    def test_the_no_completion_clause_reverted_to_its_old_citation(self):
        """#606: the pin carries its ⛔, so the pre-#606 co-citation no longer matches."""
        self.assertCaught(self.mutate("module-02", "⛔ **(INV-366) A detour completes no module:**",
                                      "⛔ **(INV-284, INV-366) A detour completes no module:**"))

    def test_step_1_marks_module_2_complete(self):
        self.assertCaught(self.mutate("module-02", 'Step 1\'s "Mark Module 2 as complete\n  only '
                                      'after Step 9\'s engine-class check passes" does not apply: a '
                                      "detour completes no module.", "Step 1 marks Module 2 complete."))

    def test_option_4_stops_a_repair(self):
        self.assertCaught(self.mutate("module-02", "or, on a `database_switch`, with Step 7's "
                                      "option 4.", "or with Step 7's option 4."))

    def test_option_4_rewrites_at_once_on_a_repair(self):
        """#598: the pre-fix Option 4, with no detour carve-out."""
        block = option_4(self.f["module-02"])
        start = block.index(" ⛔ **(INV-364) On a `setup_detour`")
        self.assertCaught(self.mutate("module-02", block[start:], "\n\n"))

    def test_option_4_carve_out_without_the_failure_clause(self):
        self.assertCaught(self.mutate("module-02", "An `sdk_repair` that continues to SQLite and "
                                      "then cannot finish leaves\n`database_type` as it was.", ""))

    def test_the_entry_note_pointer_dropped(self):
        self.assertCaught(self.mutate("phase3", ", or, for an SDK\n> repair, to step 21 for this "
                                      "source", ""))

    def test_the_session_resume_pointer_dropped(self):
        self.assertCaught(self.mutate("phase3", "A progress file carrying a `setup_detour` does "
                                      "not reach this section first", "A progress file reaches "
                                      "this section"))

    def test_the_session_resume_pointer_unlinked(self):
        self.assertCaught(self.mutate("phase3", "[the SDK repair](#the-sdk-repair-question) and "
                                      "returns", "the SDK repair and returns"))

    def test_the_session_resume_pointer_restates_the_question(self):
        self.assertCaught(self.mutate("phase3", "and returns to step 21.\n",
                                      "and returns to step 21.\n\n" + QUESTION + "\n"))

    def test_the_step_18a_pointer_dropped(self):
        self.assertCaught(self.mutate("phase2", "Its [SDK repair](phase3-test-load.md#the-sdk-"
                                      "repair-question) is a detour", "Its SDK repair is"))

    def test_the_step_18a_pointer_restates_an_option(self):
        self.assertCaught(self.mutate("phase2", "**Checkpoint:** write step 18a.",
                                      OPTION_1 + "\n\n**Checkpoint:** write step 18a."))

    def test_the_step_map_pointer_dropped(self):
        self.assertCaught(self.mutate("phase2", ", and an [SDK repair](phase3-test-load.md#the-"
                                      "sdk-repair-question) comes back to step 21 |", " |"))

    def test_the_first_clause_dropped(self):
        clause = first_clause(self.f["module-05"])
        start = clause.index("**(INV-366) When it carries a `setup_detour`")
        self.assertCaught(self.mutate("module-05", clause[start:]))


class TheChecksSurviveARewrap(unittest.TestCase):
    """INV-346: a phrase split by a line wrap is still found."""

    def test_every_site_rewrapped_still_passes(self):
        f = read_all()
        wrapped = {k: rewrap(v) for k, v in f.items()}
        self.assertNotEqual(f["phase3"], wrapped["phase3"], "the re-wrap changed nothing")
        self.assertEqual([], all_problems(wrapped))


if __name__ == "__main__":
    unittest.main()
