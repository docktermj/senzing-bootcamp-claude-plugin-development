"""Module 7 and graduation coherence items from the 2026-10-14 production-readiness audit (#614).

Each item was a pair of sibling statements that disagreed. Item 1 (the handover takeaway) is
guarded in ``test_graduation_hands_over_the_ability.py``, which now asserts what its docstring
claims. This file holds the rest, one class per item:

2. **Abort.** Step 2's Abort promises to leave ``production/`` untouched, so Step 5 writes the
   report to ``docs/GRADUATION_REPORT.md`` and Step 5a is skipped.
3. **Graduation offer.** Module 7 keeps its 👉 offer line, and its reply handling is a pointer to
   ``module-completion.md`` → "Reaching graduation" (INV-272, INV-300) rather than a copy that
   dropped the acknowledge-first line.
4. **Teardown skip.** Module 7's teardown keys on no pid and no port recorded, which covers the
   container-route decline and a failed identity check, not only ``"accepted": false``.
5. **Missing pieces.** ``steps["4a-pairs"]`` in the full checkpoint structure; the discoveries
   deliverable and gate item 5 in the success criteria and success indicator; INV-363 cited where
   the projection drops skipped sources; the normalizer's mojibake warning relayed (INV-166).

Every check is a pure function over a file's text that returns a list of problems, so each one
also runs on a mutated copy of the shipped text as its negative control: the control puts the
audited defect back and asserts the check reports it.

⚠️ **Phrase checks collapse whitespace (INV-346)**, so a phrase wrapped across lines still
matches.

⛔ **What this cannot establish:** that a live guide follows any of these passages. It pins that
the skill files STATE them; ``dry-run`` phase 3 observes a run.

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issue: #614.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"

GRADUATION = SKILLS / "graduation" / "SKILL.md"
NORMALIZER = PLUGIN / "scripts" / "normalize_docs_markdown.py"
MODULE_7 = SKILLS / "module-07-query-visualize-discover"
MODULE_7_SKILL = MODULE_7 / "SKILL.md"
MODULE_7_P1 = MODULE_7 / "phase1-query-visualize.md"
DISCOVER_A = MODULE_7 / "phase2-discover.md"
DISCOVER_B = MODULE_7 / "phase2b-discover.md"

OFFER = "👉 **Would you like to graduate now and generate your production project and recap?**"


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def section(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


# --- Item 2: Abort leaves production/ untouched -----------------------------------------------

def abort_problems(text):
    problems = []
    step2 = flat(section(text, "## Step 2: Build the production project", "## Step 3:"))
    step5 = flat(section(text, "## Step 5: Graduation report", "## Step 5a:"))
    step5a = flat(section(text, "## Step 5a:", "## Step 5b:"))
    closing = flat(section(text, "## Mandatory closing step", "Example (list only what exists)"))
    if "write the graduation report to `docs/` instead" not in step2:
        problems.append("Step 2's Abort option does not say the report goes to docs/")
    if ("Nothing under `production/` is written or normalized after an Abort: Step 5 writes the "
            "report to `docs/GRADUATION_REPORT.md`, and Step 5a is skipped.") not in step2:
        problems.append("Step 2's Abort handling does not say where the report goes")
    if ("except after Step 2's Abort, when it goes to `docs/GRADUATION_REPORT.md` instead"
            not in step5):
        problems.append("Step 5's 'Always generate' line does not name the Abort destination")
    for clause in ("skip Step 5a", "Leave an earlier `production/GRADUATION_REPORT.md` as it is.",
                   "hand-format this report to the house rules"):
        if clause not in step5:
            problems.append("Step 5's Abort paragraph lacks: %s" % clause)
    if "**Skip this step after Step 2's Abort.**" not in step5a:
        problems.append("Step 5a is not skipped after an Abort")
    if ("after Step 2's Abort, name `docs/GRADUATION_REPORT.md` instead and none of "
            "`production/`'s files") not in closing:
        problems.append("the closing announcement still names production/ after an Abort")
    return problems


class AbortLeavesProductionUntouched(unittest.TestCase):

    def test_the_shipped_skill_routes_the_report_to_docs(self):
        self.assertEqual([], abort_problems(read(GRADUATION)))

    def test_negative_control_the_audited_defect_is_reported(self):
        mutant = read(GRADUATION).replace(
            "except after Step 2's Abort, when it goes to `docs/GRADUATION_REPORT.md` instead",
            "", 1).replace("**Skip this step after Step 2's Abort.**", "", 1)
        self.assertEqual(2, len(abort_problems(mutant)), abort_problems(mutant))


# --- Item 3: Module 7's graduation offer points at "Reaching graduation" ----------------------

def offer_problems(text):
    problems = []
    completion = section(text, "## Module completion", "## Integration patterns")
    if OFFER not in completion:
        problems.append("Module 7 lost its graduation 👉 offer line")
        return problems
    after = flat(completion[completion.index(OFFER):])
    if ("`../bootcamp-onboarding/module-completion.md` → \"Reaching graduation\" states it"
            not in after):
        problems.append("the reply handling is not a pointer to \"Reaching graduation\"")
    for inv in ("INV-272", "INV-300"):
        if inv not in after:
            problems.append("the pointer does not cite %s" % inv)
    if "**Affirmative:** invoke the `graduation` skill" in after:
        problems.append("Module 7 still carries its own copy of the affirmative handling")
    return problems


class TheOfferHandlingIsAPointer(unittest.TestCase):

    def test_the_shipped_module_points_at_the_one_statement(self):
        self.assertEqual([], offer_problems(read(MODULE_7_P1)))

    def test_negative_control_a_restored_copy_is_reported(self):
        text = read(MODULE_7_P1)
        mutant = text.replace(
            "Handle the reply as",
            "- **Affirmative:** invoke the `graduation` skill (GRADUATION banner).\n\nHandle the "
            "reply as", 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertEqual(1, len(offer_problems(mutant)), offer_problems(mutant))


# --- Item 4: teardown keys on no pid and no port ----------------------------------------------

def teardown_problems(text):
    problems = []
    step = flat(section(text, "## Visualization server teardown", "## Module completion"))
    skip = step[:step.index("Otherwise, this is the one place")]
    if "`m7_visualizations` records no `pid` and no `port`" not in skip:
        problems.append("the teardown skip does not key on no pid and no port")
    for case in ("declined to recreate the SDK container", "an identity check that disagreed"):
        if case not in skip:
            problems.append("the teardown skip does not name: %s" % case)
    return problems


class TheTeardownSkipKeysOnNoServer(unittest.TestCase):

    def test_the_shipped_skip_covers_every_no_server_case(self):
        self.assertEqual([], teardown_problems(read(MODULE_7_P1)))

    def test_the_skip_matches_the_checkpoint_it_reads(self):
        """Step 3c records the pid and port only while the server is up."""
        self.assertIn("while the server is up — the port and pid it was started on",
                      flat(read(MODULE_7_P1)))

    def test_negative_control_an_accepted_false_key_is_reported(self):
        text = read(MODULE_7_P1)
        mutant = text.replace("`m7_visualizations` records no `pid` and\nno `port`",
                              "`m7_visualizations` records `\"accepted\": false`", 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertEqual(1, len(teardown_problems(mutant)), teardown_problems(mutant))


# --- Item 5: the missing pieces ---------------------------------------------------------------

def checkpoint_structure(text):
    block = section(text, "The full checkpoint structure", "\n```\n\n")
    return json.loads(block[block.index("```json") + len("```json"):])


class TheMissingPiecesArePresent(unittest.TestCase):

    def test_the_full_checkpoint_structure_names_4a_pairs(self):
        steps = checkpoint_structure(read(DISCOVER_B))["module_7_query"]["steps"]
        self.assertIn("4a-pairs", steps)
        self.assertEqual(["4a", "4a-pairs", "4b"], list(steps)[:3])
        self.assertEqual({"status", "pairs"}, set(steps["4a-pairs"]))
        self.assertEqual({"records", "prediction", "engine", "agreement"},
                         set(steps["4a-pairs"]["pairs"][0]))

    def test_4a_pairs_is_the_key_step_4a_pairs_writes(self):
        self.assertIn('`module_7_query.steps["4a-pairs"]`', read(DISCOVER_A))

    def test_the_success_criteria_name_the_deliverable_and_gate_item_5(self):
        criteria = flat(section(read(MODULE_7_P1), "## Success criteria",
                                "## Data-discoveries deliverable"))
        self.assertIn("Data-discoveries deliverable produced on every path", criteria)
        self.assertIn("`docs/bootcamp_data_discoveries.md`", criteria)
        self.assertIn("the Query Completeness Gate's item 5", criteria)

    def test_the_success_indicator_names_them_too(self):
        indicator = flat(section(read(MODULE_7_SKILL), "**Success indicator:**", "\n## "))
        self.assertIn("the data-discoveries deliverable (`docs/bootcamp_data_discoveries.md` "
                      "and `.pdf`) produced on every path", indicator)
        self.assertIn("the Query Completeness Gate's item 5", indicator)

    def test_the_gate_still_has_the_item_5_both_cite(self):
        gate = flat(section(read(MODULE_7_P1), "## Query Completeness Gate",
                            "## Visualization server teardown"))
        self.assertIn("5. **Their question answered?**", gate)
        self.assertIn("4. **Data-discoveries deliverable produced?**", gate)

    def test_the_projection_cites_inv_363_where_it_drops_skipped_sources(self):
        text = flat(read(GRADUATION))
        drop = text[text.index("Omit a source whose `mapping_status` is `skipped` too"):]
        drop = drop[:drop.index("**Why `load_subset:` goes:**")]
        self.assertIn("INV-363", drop)


def mojibake_problems(text):
    problems = []
    step = flat(section(text, "**Normalize the Markdown (once, before rendering).**",
                        "### 1b. Render the PDF"))
    if "⛔ **(INV-166) Relay the normalizer's mojibake warning; never repair it.**" not in step:
        problems.append("Step 1a does not relay the mojibake warning")
        return problems
    for clause in ("WARNING: N line(s) look like Windows-1252 mojibake", "still exits 0",
                   "Read its stderr.", "Do not edit the file to repair it",
                   "The warning is a statement, not a 👉 question"):
        if clause not in step:
            problems.append("the mojibake relay lacks: %s" % clause)
    return problems


class TheMojibakeWarningIsRelayed(unittest.TestCase):

    def test_graduation_relays_it(self):
        self.assertEqual([], mojibake_problems(read(GRADUATION)))

    def test_the_quoted_line_is_the_one_the_normalizer_writes(self):
        self.assertIn("WARNING: {len(suspect)} line(s) look like Windows-1252 mojibake",
                      read(NORMALIZER))

    def test_ground_rules_points_at_graduation_for_it(self):
        ground_rules = flat(read(SKILLS / "bootcamp-onboarding" / "ground-rules.md"))
        self.assertIn("The docs normalizer flags this class before the recap renders; see "
                      "`../graduation/SKILL.md`.", ground_rules)

    def test_negative_control_a_removed_relay_is_reported(self):
        text = read(GRADUATION)
        mutant = re.sub(r"⛔ \*\*\(INV-166\) Relay the normalizer's mojibake warning.*?\n\n", "",
                        text, count=1, flags=re.S)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertEqual(1, len(mojibake_problems(mutant)))


if __name__ == "__main__":
    unittest.main()
