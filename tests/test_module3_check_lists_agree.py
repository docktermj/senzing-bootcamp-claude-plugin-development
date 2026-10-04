"""Module 3's check lists all name the checks Phase 1 actually records, and only the
installation checks are required to pass.

Before #282, Module 3 gave three definitions of success. `SKILL.md`'s success indicator named
**7 installation checks** and left out `database_operations`. `phase1-verification.md`'s Success
criteria and `phase2-report-close.md` Step 9 named **8** checkpoint entries, left out
`engine_initialization`, and counted `results_validation` among the checks that must pass. The
example recap said "all 8" and then named nine, "all passed". Every one of these lists was
written by hand, so each could drop a different check without anything noticing.

⛔ **The source of truth is Phase 1's `**Checkpoint:**` blocks**, because those are what write
`module_3_verification.checks`. Everything else is a list of them. This guard reads the keys
from those blocks and compares each list to them:

* `SKILL.md`'s success indicator names the installation checks (every key except
  `results_validation`), and its count is that number;
* `phase1-verification.md`'s Success criteria requires exactly the installation checks to pass;
* `phase2-report-close.md` Step 9 item 1 compiles every key, with the installation checks listed
  apart from `results_validation`;
* the persisted-report JSON in Step 9 item 5 has one entry per key.

⛔ **`results_validation` is never in a pass requirement** (INV-229). It compares the engine
against a prediction the guide made, so an `expectation_mismatch` means the install works and
the prediction was wrong. A success rule that needs it to be "passed" tells a bootcamper with a
working install that verification failed.

⚠️ **The count is stated once, in `SKILL.md`.** Every other site says "the installation
checks" with no numeral, so adding or removing a check changes one number and this guard
checks that number. The example recap follows the same rule and reports results validation in
its own clause, not inside an "all passed" count.

Enforces **INV-229**'s separation of results validation from the installation checks. Source
issue: #282.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
M3 = PLUGIN / "skills" / "module-03-system-verification"
PHASE1 = M3 / "phase1-verification.md"
PHASE2 = M3 / "phase2-report-close.md"
SKILL = M3 / "SKILL.md"
RECAP = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"

RESULTS = "results_validation"

#: A `**Checkpoint:**` block that writes one check as JSON: `"checks": { "<key>": ...`.
JSON_CHECK = re.compile(r'"checks":\s*\{\s*"([a-z_]+)"\s*:')
#: Step 1a's block is prose: "record `engine_initialization` alongside `mcp_connectivity`".
PROSE_CHECK = re.compile(r"record `([a-z_]+)` alongside")
#: Step 2's block writes a data-prep marker, and says so. It is not a verification check.
NOT_A_CHECK = "not one of the report's verification checks"
#: A backticked checkpoint-shaped key. The lists under test name keys this way.
KEY = re.compile(r"`([a-z]+(?:_[a-z]+)+)`")
#: Keys that sit near these lists and belong elsewhere: the Truth Set visualization module's
#: checks, and a results-validation status value.
NOT_M3_KEYS = {"web_service", "web_page", "expectation_mismatch"}

#: A numeral or number word directly before "installation checks", "install checks" or
#: "System Verification checks": a stated count.
COUNTED = re.compile(
    r"(?i)\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\*{0,2}\s+"
    r"(?:installation|install|System Verification)\s+check")
#: "all 8 ... checks passed" / "All 8 System Verification checks passed".
ALL_N_PASSED = re.compile(r"(?i)\ball\s+\d+\b[^.;\n]*?\bchecks?\b[^.;\n]*?\bpassed")
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10}


def squash(text):
    return re.sub(r"\s+", " ", text)


def read(path):
    return path.read_text(encoding="utf-8")


def between(text, start, end):
    i = text.index(start)
    j = text.find(end, i + len(start))
    return text[i:j if j != -1 else len(text)]


def keys_in(text):
    return {k for k in KEY.findall(text) if k not in NOT_M3_KEYS}


def checkpoint_keys(phase1_text):
    """The check keys Phase 1's `**Checkpoint:**` blocks write, in Steps 1 to 8.

    Every block must yield exactly one key or say it is a data-prep marker, so a block
    written in a new shape fails here instead of silently dropping out of the set.
    """
    steps = between(phase1_text, "### Step 1:", "## Success Criteria")
    found, unread = [], []
    for block in steps.split("**Checkpoint:**")[1:]:
        block = re.split(r"\n#{2,3} ", block, maxsplit=1)[0]
        if NOT_A_CHECK in squash(block):
            continue
        keys = JSON_CHECK.findall(block) + PROSE_CHECK.findall(block)
        if len(keys) != 1:
            unread.append(squash(block)[:80])
            continue
        found.append(keys[0])
    return found, unread


def skill_indicator(skill_text):
    return squash(between(skill_text, "**Success indicator:**", "\n\n"))


def skill_pass_list(indicator):
    """The keys the success indicator requires to be "passed": up to where results validation
    is set apart."""
    return keys_in(between(indicator, 'report "passed"', "results validation"))


def phase1_pass_requirements(phase1_text):
    """Every Success-criteria bullet that requires checkpoint entries to report "passed"."""
    section = between(phase1_text, "## Success Criteria", "\n## ")
    bullets = re.split(r"\n- ", section)
    return [squash(b) for b in bullets if re.search(r'reports? "passed" status', squash(b))]


def step9_item1(phase2_text):
    return squash(between(phase2_text, "1. Compile the results", "2. For each check"))


def step9_json_keys(phase2_text):
    item5 = between(phase2_text, "5. **Persist the report**", "```\n\n")
    body = item5[item5.index("```json") + len("```json"):]
    # The schema's placeholders are strings already, so the block is valid JSON as written.
    return list(json.loads(body)["module_3_verification"]["checks"])


def recap_verification_line(recap_text):
    """The example recap's System Verification bullet.

    Line-scoped by design (#424): the example recap writes each bullet as one unwrapped line,
    as a generated recap does, and the checks below split that line at "all passed"; a bullet
    that wrapped there would fail them rather than pass.
    """
    lines = [ln for ln in recap_text.splitlines()
             if ln.startswith("- ") and "System Verification checks" in ln]
    return lines


class TheSourceOfTruthIsRead(unittest.TestCase):
    """Non-vacuity: an empty or partial key set would make every comparison below agree."""

    def setUp(self):
        self.keys, self.unread = checkpoint_keys(read(PHASE1))

    def test_every_checkpoint_block_is_read(self):
        self.assertEqual(
            self.unread, [],
            "a Phase 1 **Checkpoint:** block names no check in a shape this guard reads, so "
            "its key is missing from the source of truth")

    def test_no_key_is_written_twice(self):
        self.assertEqual(len(self.keys), len(set(self.keys)),
                         "two Phase 1 checkpoints write the same check key")

    def test_the_keys_include_the_ones_the_old_lists_dropped(self):
        for key in ("engine_initialization", "database_operations", RESULTS):
            with self.subTest(key=key):
                self.assertIn(key, self.keys, "the checkpoint parser lost a known check")

    def test_the_data_prep_marker_is_not_a_check(self):
        self.assertNotIn("synthetic_data", self.keys,
                         "Step 2's data-prep marker was read as a verification check")


class EveryListMatchesPhase1(unittest.TestCase):
    def setUp(self):
        keys, _ = checkpoint_keys(read(PHASE1))
        self.all = set(keys)
        self.install = self.all - {RESULTS}

    def test_skill_success_indicator_names_the_installation_checks(self):
        indicator = skill_indicator(read(SKILL))
        self.assertEqual(skill_pass_list(indicator), self.install,
                         "SKILL.md's success indicator names a different set of installation "
                         "checks than Phase 1 records")
        self.assertIn("`%s`" % RESULTS, indicator,
                      "SKILL.md's success indicator does not name results validation's key")

    def test_skill_states_the_count_phase1_records(self):
        indicator = skill_indicator(read(SKILL))
        m = re.search(r"\*\*(\d+) installation checks\*\*", indicator)
        self.assertIsNotNone(m, "SKILL.md's success indicator states no installation-check count")
        self.assertEqual(int(m.group(1)), len(self.install),
                         "SKILL.md's count differs from the installation checks Phase 1 records")

    def test_phase1_success_criteria_require_the_installation_checks(self):
        reqs = phase1_pass_requirements(read(PHASE1))
        self.assertEqual(len(reqs), 1,
                         "expected one Success-criteria bullet requiring checks to pass")
        self.assertEqual(keys_in(reqs[0]), self.install,
                         "the Success criteria require a different set of checks than the "
                         "installation checks Phase 1 records")

    def test_phase1_success_criteria_name_results_validation_apart(self):
        section = between(read(PHASE1), "## Success Criteria", "\n## ")
        self.assertIn("`%s`" % RESULTS, section,
                      "the Success criteria no longer say how results validation is reported")

    def test_step9_compiles_every_key(self):
        item1 = step9_item1(read(PHASE2))
        self.assertEqual(keys_in(item1), self.all,
                         "Step 9 item 1 compiles a different set of checks than Phase 1 records")
        install_part = between(item1, "the installation checks", "reported separately")
        self.assertEqual(keys_in(install_part), self.install,
                         "Step 9 item 1's installation list differs from Phase 1's")

    def test_step9_persisted_report_has_every_key(self):
        keys = step9_json_keys(read(PHASE2))
        self.assertEqual(len(keys), len(set(keys)), "the persisted report repeats a key")
        self.assertEqual(set(keys), self.all,
                         "the persisted-report JSON has a different set of checks than Phase 1 "
                         "records")


class ResultsValidationIsNeverRequiredToPass(unittest.TestCase):
    def test_not_in_the_skill_pass_list(self):
        self.assertNotIn(RESULTS, skill_pass_list(skill_indicator(read(SKILL))),
                         "SKILL.md requires results validation to pass (INV-229)")

    def test_not_in_a_phase1_pass_requirement(self):
        for req in phase1_pass_requirements(read(PHASE1)):
            with self.subTest(bullet=req[:60]):
                self.assertNotIn(RESULTS, req,
                                 "a Success criterion requires results validation to be "
                                 "\"passed\" (INV-229)")

    def test_step9_lists_it_apart(self):
        item1 = step9_item1(read(PHASE2))
        install_part = between(item1, "the installation checks", "reported separately")
        self.assertNotIn(RESULTS, install_part,
                         "Step 9 lists results validation among the installation checks")


class TheCountIsStatedOnce(unittest.TestCase):
    FILES = (SKILL, PHASE1, PHASE2, RECAP)

    def test_only_skill_states_a_count(self):
        for path in self.FILES:
            text = squash(read(path))
            hits = COUNTED.findall(text)
            with self.subTest(file=path.name):
                if path == SKILL:
                    self.assertEqual(len(hits), 1,
                                     "SKILL.md must state the installation-check count once")
                else:
                    self.assertEqual(hits, [], "a second site states a check count")

    def test_no_numbered_all_passed_claim(self):
        for path in self.FILES:
            with self.subTest(file=path.name):
                self.assertIsNone(ALL_N_PASSED.search(squash(read(path))),
                                  "an \"all N checks passed\" claim remains")

    def test_no_other_seven(self):
        for path in self.FILES:
            with self.subTest(file=path.name):
                self.assertNotRegex(squash(read(path)), r"(?i)\bother (?:seven|eight|\d+)\b",
                                    "a site counts the other checks")


class TheExampleRecapReportsResultsValidationApart(unittest.TestCase):
    def setUp(self):
        self.lines = recap_verification_line(read(RECAP))

    def test_the_line_is_found(self):
        self.assertEqual(len(self.lines), 1,
                         "the example recap's System Verification line was not located")

    def test_results_validation_is_outside_the_all_passed_clause(self):
        line = self.lines[0]
        head, sep, tail = line.partition("all passed")
        self.assertTrue(sep, "the recap line no longer says the installation checks passed")
        self.assertNotIn("results validation", head.lower(),
                         "results validation is counted inside the \"all passed\" clause")
        self.assertIn("results validation", tail.lower(),
                      "the recap line does not report results validation in its own clause")

    def test_the_passed_clause_names_the_dropped_checks(self):
        head = self.lines[0].partition("all passed")[0].lower()
        for name in ("engine initialization", "database operations"):
            with self.subTest(check=name):
                self.assertIn(name, head, "the recap's passed list drops an installation check")


class TheGuardCatchesDivergence(unittest.TestCase):
    """In-suite negative controls: each helper fails on a copy with the old defect put back."""

    def setUp(self):
        self.phase1 = read(PHASE1)
        self.phase2 = read(PHASE2)
        self.skill = read(SKILL)
        keys, _ = checkpoint_keys(self.phase1)
        self.all = set(keys)
        self.install = self.all - {RESULTS}

    def test_a_dropped_skill_check_is_seen(self):
        broken = self.skill.replace(" and database operations\n(`database_operations`)", "", 1)
        self.assertNotEqual(broken, self.skill, "control did not apply")
        self.assertNotEqual(skill_pass_list(skill_indicator(broken)), self.install)

    def test_results_validation_in_the_phase1_requirement_is_seen(self):
        broken = self.phase1.replace("`data_loading`, `database_operations`).",
                                     "`data_loading`, `results_validation`, "
                                     "`database_operations`).", 1)
        self.assertNotEqual(broken, self.phase1, "control did not apply")
        self.assertIn(RESULTS, phase1_pass_requirements(broken)[0])

    def test_a_dropped_json_key_is_seen(self):
        broken = self.phase2.replace(
            '         "engine_initialization": {"status": "passed|failed"},\n', "", 1)
        self.assertNotEqual(broken, self.phase2, "control did not apply")
        self.assertNotEqual(set(step9_json_keys(broken)), self.all)

    def test_a_new_checkpoint_shape_is_reported_not_dropped(self):
        broken = self.phase1.replace(
            "**Checkpoint:** record `engine_initialization` alongside",
            "**Checkpoint:** also store `engine_initialization` next to", 1)
        self.assertNotEqual(broken, self.phase1, "control did not apply")
        _, unread = checkpoint_keys(broken)
        self.assertEqual(len(unread), 1)

    def test_a_restored_count_is_seen(self):
        self.assertTrue(COUNTED.search("for the **seven installation checks**;"))
        self.assertTrue(ALL_N_PASSED.search("All 8 System Verification checks passed"))
        self.assertTrue(ALL_N_PASSED.search("Ran all 8 System Verification checks: a, b — all passed"))


if __name__ == "__main__":
    unittest.main()
