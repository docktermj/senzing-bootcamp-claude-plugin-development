"""SDK setup Step 7 and Step 8a state what they do on a datastore that already exists (#684).

Enforces **INV-393**, registered by the maintainer 2026-10-20: a step whose precondition can
already be satisfied states the branch for that case rather than leaving it to the guide. ⚠️ It
reads the shipped step prose; it **cannot** establish that a live run takes the stated branch.

Both steps were written for a datastore that does not yet exist, and the module documents two
paths that re-enter them on one that does:

* a **resume**, because Step 7's instruction 2 holds the step-7 checkpoint back until the chosen
  branch's setup is finished, so a session interrupted between creating the datastore and the
  checkpoint runs the whole of Step 7 again; and
* the **`sdk_repair` detour**, whose row runs Step 1 through Step 9 and is offered from Data
  Quality, Mapping, and Transformation Phase 3 — after that module has already set the datastore
  up and registered its sources.

Neither step said anything about that state, while both of the MCP routes they use do. The
server's *Senzing Anti-Patterns: Database Initialization and Container Setup* article guards its
DDL behind a `sys_cfg` existence check and its `create_config_from_template()` behind
`get_default_config_id()`, and names "application code calls `create_config_from_template()` on
every startup, which fails when a config already exists" as a symptom. The seeding snippet Step 8a
sends the guide to fetch, `python/configuration/init_default_config.py`, carries the check as an
**interactive prompt** — "A configuration exists in the repository, replace it with a template
configuration? (y/n)", `sys.exit(1)` on anything else — which in an agent-driven run is a hang or
an exit 1 that reads as a failed step, while answering `y` replaces the registered default config
and drops every `DATA_SOURCE` code in it. (Re-verified on MCP server 1.39.1, 2026-10-17.)

So each branch is stated **once** (INV-300) and pointed at from everywhere else:

* Step 7's **instruction 3**, at the head of the step where both engines pass, owns the
  already-applied-schema branch; the SQLite branch's rung 2 and the PostgreSQL branch's DDL step
  point at it.
* **Step 8a**'s already-seeded block owns the already-registered-config branch, names the prompt,
  and forbids answering it blind.
* The **`sdk_repair` detour** cites both and restates neither, and states that it needs no
  `register-sources` step of its own — Data Quality, Mapping, and Transformation step 21a
  re-registers the `DATA_SOURCE` codes before the step 22 test load (INV-089), so a re-seed on the
  repair path is already covered — so the omission reads as a decision, not an oversight.

Each check is a function of the file text, and every negative control runs the SAME check over a
mutated copy that restores the pre-#684 shape (INV-265). Prose is matched wrap-aware (INV-346) and
shipped files are read as text, never imported (INV-108).

⚠️ **What these tests cannot establish:** that a live guide runs the probe, reads the id before
seeding, or skips rather than re-applies. They assert that the skill *states* the branches; only a
dry run against a real datastore can observe the behavior.

Enforces **INV-080**, **INV-089** and **INV-300** at these sites.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines as _match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_02 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
PHASE3 = SKILLS / "module-05-data-quality-mapping" / "phase3-test-load.md"

#: Step 7's instruction 3 and the sites that point at it.
INSTRUCTION_3 = "3. ⛔ **(INV-393) When the datastore already exists"
HANDLING = "**Handling each answer (INV-284).**"
SQLITE_BRANCH = "**For SQLite**"
RUNG_2 = "2. **Apply the Senzing schema**"
RUNG_3 = "3. **Seed the Senzing configuration**"
PG_DDL = "4. Apply the Senzing PostgreSQL schema DDL"
PG_WIRE = "5. Wire the connection into the engine config"
#: Step 8a's already-seeded branch and the paragraph it sits in front of.
SEED_BRANCH = "⛔ **(INV-393) When a default configuration is already registered"
SEED_FETCH = "`sdk_guide(topic='configure')`'s primary `RegisterDataSources` snippet"
#: The detour section and the `sdk_repair` running notes inside it.
DETOUR_ANCHOR = '<a id="receiving-a-setup-detour"></a>'
SDK_REPAIR_NOTES = "For `sdk_repair`:"
DETOUR_FINISH = "**When every step is done,**"
#: Data Quality, Mapping, and Transformation's register-before-load step, which the detour cites
#: as its reason for having no `register-sources` step of its own.
STEP_21A_HEADING = "### 21a. Register the data source code (before the test load)"
STEP_21A_LINK = "../module-05-data-quality-mapping/phase3-test-load.md"
#: The one phrase that says which question the probe asks, on either engine.
SYS_CFG = "sys_cfg"
#: The prompt the fetched seeding snippet raises, as the server returns it.
PROMPT = "A configuration exists in the repository, replace it with a template configuration?"
#: A server version and a date, so a Senzing fact in shipped text carries its provenance.
PROVENANCE = r"MCP server 1\.\d+\.\d+, \d{4}-\d{2}-\d{2}"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


def match(text, pattern):
    """Wrap-aware (INV-346): does `pattern` appear anywhere in `text`?"""
    return bool(_match_lines(text, re.compile(pattern)))


def missing(text, patterns, where):
    return [f"{where} does not say {p!r}" for p in patterns if not match(text, p)]


def step7(m2):
    return between(m2, "## Step 7:", "\n## Step 8:")


def step8a(m2):
    return between(m2, "## Step 8a:", "\n## Step 9:")


def instruction_3(m2):
    return between(step7(m2), INSTRUCTION_3, HANDLING)


def seed_branch(m2):
    return between(step8a(m2), SEED_BRANCH, SEED_FETCH)


def repair_notes(m2):
    return between(between(m2, DETOUR_ANCHOR, "\n## Step 1:"), SDK_REPAIR_NOTES, DETOUR_FINISH)


def anchor(heading):
    """The GitHub anchor a Markdown heading gets, so a link cannot drift from its target."""
    slug = heading.lstrip("#").strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"[\s]+", "-", slug)


# --- checks: each returns a list of problems -------------------------------------------------


def instruction_3_problems(m2):
    """Step 7 states the already-applied branch once, at the head, for both engines."""
    step = step7(m2)
    if step.count(INSTRUCTION_3) != 1:
        return [f"Step 7 carries {step.count(INSTRUCTION_3)} copies of instruction 3; it needs one"]
    if step.index(INSTRUCTION_3) > step.index(SQLITE_BRANCH):
        return ["instruction 3 sits after the branches, where a guide on one path never reads it"]
    text = instruction_3(m2)
    problems = missing(text, (
        r"(?i)when the datastore already exists",
        r"(?i)skip it and say so",
        r"(?i)for \*\*both\*\* engines",
        r"(?i)resume",
        r"(?i)`sdk_repair` detour",
        r"(?i)whether the Senzing schema is applied",
        SYS_CFG,
        r"(?i)\*\*Not applied:\*\* apply it",
        r"(?i)could not be run",
        PROVENANCE,
        r"INV-300",
    ), "Step 7's instruction 3")
    if not match(text, r"(?i)not whether a file or a database exists"):
        problems.append("instruction 3 does not say the question is the schema, not the file: a "
                        "datastore can exist with no schema in it, and the two answers differ")
    return problems


def pointer_problems(m2):
    """Both engines' schema steps point at instruction 3 and carry no second copy of it."""
    step = step7(m2)
    problems = []
    for label, text in (("the SQLite branch's rung 2", between(step, RUNG_2, RUNG_3)),
                        ("the PostgreSQL branch's DDL step", between(step, PG_DDL, PG_WIRE))):
        problems += missing(text, (r"instruction 3 at the head of Step 7", r"INV-300"), label)
        for copy in (SYS_CFG, r"(?i)skip it and say so"):
            if match(text, copy):
                problems.append(f"{label} carries a second copy of the branch ({copy!r}); it must "
                                "point at instruction 3, not restate it (INV-300)")
    return problems


def seed_branch_problems(m2):
    """Step 8a states the already-seeded branch, and names the prompt in the fetched snippet."""
    step = step8a(m2)
    if step.count(SEED_BRANCH) != 1:
        return [f"Step 8a carries {step.count(SEED_BRANCH)} copies of the already-seeded branch; "
                "it needs one"]
    if step.index(SEED_BRANCH) > step.index(SEED_FETCH):
        return ["the already-seeded branch sits after the seeding instructions, so a guide reads "
                "it only once it has already re-seeded"]
    problems = missing(seed_branch(m2), (
        r"(?i)do not re-seed",
        r"get_default_config_id\(\)",
        r"(?i)before anything else",
        r"(?i)already seeded",
        r"(?i)without seeding",
    ), "Step 8a's already-seeded branch")
    prompt = between(step, SEED_BRANCH, SEED_FETCH)
    problems += missing(prompt, (
        r"init_default_config",
        re.escape(PROMPT),
        r"(?i)must\s+not answer it blind",
        r"(?i)exiting `1`",
        r"(?i)hangs",
        PROVENANCE,
        r"INV-300",
    ), "Step 8a's note on the fetched snippet")
    return problems


def detour_problems(m2):
    """The `sdk_repair` detour cites both branches, restates neither, and owns its omission."""
    notes = repair_notes(m2)
    problems = missing(notes, (
        r"Step 7's instruction 3",
        r"(?i)Step 8a's already-seeded branch",
        r"(?i)does not restate it \(INV-300\)",
        r"(?i)No `register-sources` step",
        r"(?i)a decision rather than an omission",
        r"\[step 21a\]\(" + re.escape(STEP_21A_LINK),
        r"(?i)before the step 22 test load",
        r"INV-089",
    ), "the `sdk_repair` running notes")
    for copy in (SYS_CFG, re.escape(PROMPT)):
        if match(notes, copy):
            problems.append(f"the `sdk_repair` notes restate the branch ({copy!r}) instead of "
                            "pointing at it (INV-300)")
    row = [line for line in m2.splitlines() if line.startswith("| `sdk_repair` |")]
    if len(row) != 1:
        problems.append("the detour table has no single `sdk_repair` row")
    elif "register-sources" in row[0]:
        problems.append("the `sdk_repair` row carries a `register-sources` step, which #684 "
                        "decided against; the notes say why it has none")
    return problems


def citation_problems(m2, phase3):
    """The step the detour's reason rests on exists, under the heading the link resolves to."""
    problems = []
    if STEP_21A_HEADING not in phase3:
        return [f"{STEP_21A_HEADING!r} is not in phase3-test-load.md; the detour's reason for "
                "having no `register-sources` step rests on it"]
    expected = f"{STEP_21A_LINK}#{anchor(STEP_21A_HEADING)}"
    if expected not in m2:
        problems.append(f"the detour does not link {expected!r}; the anchor has drifted from the "
                        "heading it points at")
    step = between(phase3, STEP_21A_HEADING, "### 22.")
    problems += missing(step, (r"(?i)registered in the Senzing\s+engine config", r"INV-089"),
                        "step 21a")
    if not match(phase3, r"### 22\. Test data loading"):
        problems.append("phase3-test-load.md has no step 22, so 'before the test load' is stale")
    return problems


class TheExistingDatastoreBranchIsStated(unittest.TestCase):

    def setUp(self):
        self.m2 = read(MODULE_02)
        self.phase3 = read(PHASE3)

    def test_step_7_states_it_once_for_both_engines(self):
        self.assertEqual(instruction_3_problems(self.m2), [])

    def test_both_schema_steps_point_at_it(self):
        self.assertEqual(pointer_problems(self.m2), [])

    def test_step_8a_states_the_already_seeded_branch_and_names_the_prompt(self):
        self.assertEqual(seed_branch_problems(self.m2), [])

    def test_the_sdk_repair_detour_cites_both_and_owns_its_omission(self):
        self.assertEqual(detour_problems(self.m2), [])

    def test_the_reason_the_detour_rests_on_still_exists(self):
        self.assertEqual(citation_problems(self.m2, self.phase3), [])


class NegativeControls(unittest.TestCase):
    """Each mutation restores the pre-#684 shape, which every check must report."""

    def setUp(self):
        self.m2 = read(MODULE_02)
        self.phase3 = read(PHASE3)

    def drop(self, start, end):
        """The module with the passage from `start` up to `end` removed."""
        cut = between(self.m2, start, end)
        mutated = self.m2.replace(cut, "", 1)
        self.assertNotEqual(mutated, self.m2, "control did not apply")
        return mutated

    def test_step_7_with_no_instruction_3_fails(self):
        self.assertTrue(instruction_3_problems(self.drop(INSTRUCTION_3, HANDLING)))

    def test_instruction_3_placed_after_the_branches_fails(self):
        passage = between(self.m2, INSTRUCTION_3, HANDLING)
        moved = self.m2.replace(passage, "", 1).replace(
            "SQLite remains the default recommendation", passage + "SQLite remains the default "
            "recommendation", 1)
        self.assertNotEqual(moved, self.m2, "control did not apply")
        self.assertTrue(any("sits after the branches" in p
                            for p in instruction_3_problems(moved)))

    def test_a_probe_on_the_file_rather_than_the_schema_fails(self):
        broken = self.m2.replace("not whether a file or a database exists",
                                 "which is whether the file is there", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("not the file" in p for p in instruction_3_problems(broken)))

    def test_a_schema_step_that_does_not_point_at_it_fails(self):
        broken = self.m2.replace(
            """2. **Apply the Senzing schema** to `database/G2C.db` — **unless it is already applied**, which
   instruction 3 at the head of Step 7 decides, for both engines (INV-300); this rung is its
   "not applied" path.""",
            "2. **Apply the Senzing schema** to `database/G2C.db`.", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("rung 2" in p for p in pointer_problems(broken)))

    def test_a_schema_step_that_restates_the_branch_fails(self):
        broken = self.m2.replace(
            "3. **Seed the Senzing configuration**",
            "   Check for a `sys_cfg` table first and skip it and say so when it is there.\n"
            "3. **Seed the Senzing configuration**", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("second copy" in p for p in pointer_problems(broken)))

    def test_step_8a_with_no_already_seeded_branch_fails(self):
        self.assertTrue(seed_branch_problems(self.drop(SEED_BRANCH, SEED_FETCH)))

    def test_step_8a_that_does_not_name_the_prompt_fails(self):
        # The quoted prompt wraps in the file, so the mutation takes the part on one line.
        broken = self.m2.replace("A configuration exists in the repository, replace it with a template",
                                 "whether to replace the configuration", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("fetched snippet" in p for p in seed_branch_problems(broken)))

    def test_a_detour_that_restates_a_branch_fails(self):
        broken = self.m2.replace(
            "- **`8a`.** Likewise for the configuration:",
            "- **`8a`.** Read the default config id and skip the seed when a `sys_cfg` row holds "
            "one:", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("restate" in p for p in detour_problems(broken)))

    def test_a_detour_that_does_not_own_its_omission_fails(self):
        self.assertTrue(detour_problems(self.drop(
            "- **No `register-sources` step", "\n**When every step is done,**")))

    def test_a_register_sources_step_added_to_the_row_fails(self):
        row = next(r for r in self.m2.splitlines() if r.startswith("| `sdk_repair` |"))
        broken = self.m2.replace(row, row.replace(
            "`9`: [Step 9]", "`register-sources`: every code registered again. `9`: [Step 9]", 1), 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("decided against" in p for p in detour_problems(broken)))

    def test_a_drifted_anchor_fails(self):
        broken = self.m2.replace("#21a-register-the-data-source-code-before-the-test-load",
                                 "#21a-register-the-data-source-code", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("anchor has drifted" in p
                            for p in citation_problems(broken, self.phase3)))


if __name__ == "__main__":
    unittest.main()
