"""Module 2 Step 7 records `database_type` where every path through the step reads it (#329).

Step 7 asks which database to use and then splits into two branches, `**For SQLite**` and
`**For PostgreSQL**`. The ⛔ instruction that writes `database_type` to
`config/bootcamp_preferences.yaml` said it applied to "whichever option was taken", but it sat
after the PostgreSQL branch's last option, and the step-7 checkpoint sat after it. A guide on the
SQLite branch reads to the end of that branch, skips the branch it did not take, and moves on to
Step 8, past both. On the 2026-10-01 dry-run walk the key was absent for the whole bootcamp, and
every reader of it ran on a fallback.

So the write and the checkpoint instruction are stated once, at the head of Step 7, before
`**For SQLite**`. The checkpoint is stated there but run when the chosen branch's setup is
finished: written as the step starts, it would mark the step done before the database exists, and
a resume would skip the setup. PostgreSQL's Option 4 (switch to SQLite) points back to the head
instruction to rewrite the key, rather than carrying a second copy of the rule.

The checks are pure functions over the text, so each negative control below runs the same check
over a mutated copy: moving the write back after Option 4 must fail it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_02 = SKILLS / "module-02-sdk-setup" / "SKILL.md"

STEP7_HEADING = "## Step 7:"
STEP8_HEADING = "\n## Step 8:"
SQLITE_BRANCH = "**For SQLite**"
WRITE_MARKER = "⛔ **Record the choice where later modules read it.**"
YAML_LINE = "database_type: sqlite   # or: postgresql"
CHECKPOINT = "**Checkpoint:** write step 7"
OPTION_4 = "**Option 4 — Switch to SQLite:**"

#: Each reader of the key, as the rationale must name it: the path relative to Module 2's
#: directory, the section label the rationale uses, and the heading that label stands for in the
#: reader's own file, so a renamed section turns this guard red instead of leaving a stale name.
READERS = (
    ("../module-04-data-collection/SKILL.md", "Step 8b", "### 8b."),
    ("../module-06-data-processing/phaseA-build-loading.md", "§3", "## 3."),
    ("../module-06-data-processing/phaseA-build-loading.md", "SQLite volume pre-load check",
     "## SQLite volume pre-load check"),
    ("../graduation/SKILL.md", "`## Pre-checks`", "## Pre-checks"),
    ("../graduation/SKILL.md", "Step 3", "## Step 3:"),
    ("../graduation/database-backup.md", None, None),
)

#: A count of readers ("two later steps") goes stale the moment a reader is added.
READER_COUNT = re.compile(
    r"(?i)\b(?:one|two|three|four|five|six|seven|eight|\d+) (?:later )?(?:steps|readers|modules)"
    r" (?:depend|read)")
#: A line number (`SKILL.md:1087`, `:254-255`) goes stale the moment the reader is edited.
LINE_NUMBER = re.compile(r"\.md:\d+|`:\d+")


def read(path):
    return path.read_text(encoding="utf-8")


def step7(text):
    start = text.index(STEP7_HEADING)
    end = text.index(STEP8_HEADING, start)
    return text[start:end]


def paragraph_at(text, needle):
    """The blank-line-delimited paragraph that starts at `needle`."""
    start = text.index(needle)
    end = text.find("\n\n", start)
    return text[start:] if end < 0 else text[start:end]


def write_instruction(step):
    """The head instruction's text: from the ⛔ marker up to the checkpoint instruction."""
    start = step.index(WRITE_MARKER)
    end = step.find(CHECKPOINT, start)
    return step[start:] if end < 0 else step[start:end]


def placement_problems(step):
    """Why the write or the checkpoint is not where every path through Step 7 reads it."""
    problems = []
    branch = step.find(SQLITE_BRANCH)
    if branch < 0:
        return [f"Step 7 has no {SQLITE_BRANCH} branch for this guard to anchor on"]
    for label, needle in (("write instruction", WRITE_MARKER), ("yaml example", YAML_LINE),
                          ("checkpoint instruction", CHECKPOINT)):
        count = step.count(needle)
        if count != 1:
            problems.append(f"the {label} appears {count} times in Step 7; it must appear once")
        elif step.index(needle) > branch:
            problems.append(f"the {label} sits after {SQLITE_BRANCH}, inside a branch a guide "
                            "on the other path skips")
    if step.count(CHECKPOINT) == 1:
        flat = re.sub(r"\s+", " ", paragraph_at(step, CHECKPOINT))
        if not re.search(r"(?i)when the chosen branch's setup is finished", flat):
            problems.append("the checkpoint does not say to write it when the chosen branch's "
                            "setup is finished")
        if not re.search(r"(?i)\bnot now\b", flat):
            problems.append("the checkpoint does not say not to write it as Step 7 starts")
    return problems


def option4_problems(step):
    """Option 4 must rewrite the key by pointing at the head instruction, with no second copy."""
    if step.count(OPTION_4) != 1:
        return [f"Step 7 carries {step.count(OPTION_4)} copies of {OPTION_4}"]
    flat = re.sub(r"\s+", " ", paragraph_at(step, OPTION_4))
    problems = []
    if not re.search(r"rewrite `database_type` to `sqlite`", flat):
        problems.append("Option 4 does not rewrite database_type to sqlite, so a Bootcamper "
                        "who switches keeps the postgresql value the head instruction wrote")
    if not re.search(r"(?i)instruction 1 at the head of this step", flat):
        problems.append("Option 4 does not point to the head instruction")
    if "bootcamp_preferences.yaml" in flat or "Record the choice" in flat:
        problems.append("Option 4 restates the rule instead of pointing to it")
    return problems


def rationale_problems(step):
    """The rationale names every reader by file and section, with no count and no line number."""
    if WRITE_MARKER not in step:
        return ["Step 7 has no write instruction"]
    text = write_instruction(step)
    flat = re.sub(r"\s+", " ", text)
    problems = []
    if READER_COUNT.search(flat):
        problems.append(f"the rationale counts its readers: {READER_COUNT.search(flat).group(0)!r}")
    if LINE_NUMBER.search(text):
        problems.append(f"the rationale cites a line number: {LINE_NUMBER.search(text).group(0)!r}")
    if re.search(r"(?i)nothing reads it from there", flat):
        problems.append("the rationale still says nothing reads bootcamp_progress.json, but two "
                        "readers fall back to it")
    for path, label, _ in READERS:
        if f"`{path}`" not in text:
            problems.append(f"the rationale does not name {path}")
        if label and label not in text:
            problems.append(f"the rationale does not name {path}'s section {label!r}")
    return problems


class TheWriteAndTheCheckpointPrecedeTheBranches(unittest.TestCase):

    def setUp(self):
        self.text = read(MODULE_02)
        self.step = step7(self.text)

    def test_the_write_and_the_checkpoint_are_stated_once_before_the_sqlite_branch(self):
        self.assertEqual(placement_problems(self.step), [])

    def test_option_4_points_back_to_the_head_instruction(self):
        self.assertEqual(option4_problems(self.step), [])

    def test_the_rationale_names_every_reader_by_file_and_section(self):
        self.assertEqual(rationale_problems(self.step), [])

    def test_every_named_reader_exists_and_reads_the_key(self):
        base = MODULE_02.parent
        for path, label, heading in READERS:
            with self.subTest(reader=path, section=label):
                reader = (base / path).resolve()
                self.assertTrue(reader.is_file(), f"{path} does not resolve from Module 2")
                body = read(reader)
                self.assertIn("database_type", body, f"{path} no longer reads the key")
                if heading:
                    self.assertRegex(body, rf"(?m)^{re.escape(heading)}",
                                     f"{path} has no {heading!r} section; the name is stale")


class NegativeControls(unittest.TestCase):
    """Each mutation restores a shape the guard exists to catch."""

    def setUp(self):
        self.step = step7(read(MODULE_02))
        start = self.step.index("1. " + WRITE_MARKER)
        end = self.step.index("2. " + CHECKPOINT)
        self.write_block = self.step[start:end]
        self.option4 = paragraph_at(self.step, OPTION_4)

    def test_moving_the_write_back_after_option_4_fails(self):
        moved = self.step.replace(self.write_block, "", 1)
        moved = moved.replace(self.option4, self.option4 + "\n\n" + self.write_block, 1)
        self.assertNotEqual(moved, self.step, "control did not apply")
        problems = placement_problems(moved)
        self.assertTrue(any("write instruction sits after" in p for p in problems), problems)
        self.assertTrue(any("yaml example sits after" in p for p in problems), problems)

    def test_moving_the_checkpoint_back_to_the_end_fails(self):
        checkpoint = paragraph_at(self.step, "2. " + CHECKPOINT)
        moved = self.step.replace(checkpoint, "", 1) + "\n" + CHECKPOINT + " to x.\n"
        self.assertNotEqual(moved, self.step, "control did not apply")
        self.assertTrue(any("checkpoint instruction sits after" in p
                            for p in placement_problems(moved)))

    def test_a_checkpoint_written_when_the_step_starts_fails(self):
        checkpoint = paragraph_at(self.step, "2. " + CHECKPOINT)
        broken = self.step.replace(checkpoint, "2. " + CHECKPOINT + " now.", 1)
        self.assertNotEqual(broken, self.step, "control did not apply")
        self.assertEqual(len(placement_problems(broken)), 2)

    def test_a_second_copy_of_the_rule_fails(self):
        broken = self.step.replace(self.option4, self.option4 + "\n\n" + self.write_block, 1)
        problems = placement_problems(broken)
        self.assertTrue(any("appears 2 times" in p for p in problems), problems)

    def test_option_4_that_only_proceeds_fails(self):
        broken = self.step.replace(
            self.option4, OPTION_4 + " proceed with the SQLite setup above.", 1)
        self.assertNotEqual(broken, self.step, "control did not apply")
        self.assertEqual(len(option4_problems(broken)), 2)

    def test_option_4_that_restates_the_rule_fails(self):
        broken = self.step.replace(
            self.option4, self.option4 + " Write it to `config/bootcamp_preferences.yaml`.", 1)
        self.assertTrue(any("restates" in p for p in option4_problems(broken)))

    def test_a_reader_count_fails(self):
        broken = self.step.replace(
            "These read\n", "Two later steps depend on the answer. These read\n", 1)
        self.assertNotEqual(broken, self.step, "control did not apply")
        self.assertTrue(any("counts its readers" in p for p in rationale_problems(broken)))

    def test_a_line_number_fails(self):
        broken = self.step.replace("`../graduation/database-backup.md`",
                                   "`../graduation/database-backup.md:21`", 1)
        self.assertNotEqual(broken, self.step, "control did not apply")
        self.assertTrue(any("line number" in p for p in rationale_problems(broken)))

    def test_the_stale_nothing_reads_it_claim_fails(self):
        broken = self.step.replace("the readers look there only after\n",
                                   "nothing reads it from there, and\n", 1)
        self.assertNotEqual(broken, self.step, "control did not apply")
        self.assertTrue(any("nothing reads" in p for p in rationale_problems(broken)))

    def test_a_dropped_reader_fails(self):
        broken = self.step.replace("`../graduation/database-backup.md`", "the backup", 1)
        self.assertNotEqual(broken, self.step, "control did not apply")
        self.assertTrue(any("database-backup.md" in p for p in rationale_problems(broken)))


if __name__ == "__main__":
    unittest.main()
