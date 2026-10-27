"""Module completion's Step 1 sets `current_module` unconditionally and lists every field it writes.

`bootcamp-onboarding/module-completion.md` Step 1 said: "Set `current_module` to the next module
in `selected_modules` (or leave it on this module if the bootcamper has not yet chosen to
advance)". Step 1 runs immediately **before** the module's transition 👉 question (Step 4), so at
Step 1 the Bootcamper has never chosen, and nothing else advances `current_module`. Read
literally, a finished module stayed `current_module`: the journey map showed it 🔄 and resume
landed on it. Modules 0, 3 and 3b already set it unconditionally at their own close.

Step 2b's End-of-Module Summary rule also said that a directing module whose
`directing_steps` entry is still unset records `none` "in Step 1's write", while Step 1's field
list never named `directing_steps`.

What this file pins, in Step 1 of `module-completion.md` (the text from its `## Step 1:` heading
to the next `## ` heading):

1. **`current_module` is set with no condition on the Bootcamper's answer.** Step 1 has one
   bullet that sets `current_module`; it names the next module in `selected_modules`, says
   "unconditionally", and carries no clause that leaves the module in place, waits on a choice
   to advance, or depends on how the Bootcamper answers.
2. **Step 1's list names `directing_steps`.** One bullet names it, limits it to the three
   directing modules (Data Quality, Mapping, and Transformation; Data processing; Query,
   Visualize and Discover), sets an unset entry to `none`, and never overwrites a recorded value.
3. **Step 1 stays one batched write** (INV-012), and Step 2b's "record `none` in Step 1's
   write" sentence is still there, now matched by Step 1's list.

Negative controls: the old "leave it on this module" parenthetical put back fails; a condition
reworded onto the answer ("once the Bootcamper has chosen to advance") fails; the
`directing_steps` bullet removed fails; the bullet without its never-overwrite clause fails.

The file reads one named plugin file and walks no root, so it takes no list from
`tests/_corpus.py`.

Enforces **INV-413** (registered 2026-10-26): Step 1 advances `current_module` with no condition
on the answer and names every field it writes, `directing_steps` included. It reads Step 1's
text and does NOT establish that a live guide performs the write; only a real walk shows that.

Source issue: #782. Invariants applied: INV-012 (one quiet batched write), INV-029 (the journey
map shows the current module), INV-092 (Module 0's unconditional write is the precedent), INV-227
(`current_module` is what records a bootcamp in progress).

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_COMPLETION = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
                     / "bootcamp-onboarding" / "module-completion.md")

#: Wording that makes the `current_module` write wait on, or depend on, the Bootcamper's answer.
CONDITION_ON_THE_ANSWER = re.compile(
    r"leave\s+it\s+on\s+this\s+module"
    r"|stays?\s+on\s+this\s+module"
    r"|(?:not\s+yet|has|have|once\s+(?:the\s+)?bootcamper\s+has)\s+chosen"
    r"|chosen\s+to\s+advance"
    r"|\b(?:if|once|when|after|unless|until)\s+the\s+bootcamper\s+"
    r"(?:has\s+)?(?:answer|answers|answered|choose|chooses|chose|confirm|confirms|confirmed"
    r"|agree|agrees|agreed|say|says|said|reply|replies|replied)"
    r"|on\s+an\s+affirmative",
    re.IGNORECASE)

DIRECTING_MODULES = (
    "Data Quality, Mapping, and Transformation",
    "Data processing",
    "Query, Visualize and Discover",
)


def read():
    return MODULE_COMPLETION.read_text(encoding="utf-8")


def step1(text):
    """The text of Step 1, from its heading to the next `## ` heading."""
    match = re.search(r"^## Step 1:.*?(?=^## )", text, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else ""


def bullets(section):
    """Each top-level `- ` bullet of a section, continuation lines joined."""
    items, current = [], None
    for line in section.splitlines():
        if line.startswith("- "):
            if current is not None:
                items.append(current)
            current = line[2:]
        elif current is not None and line.startswith("  ") and line.strip():
            current += " " + line.strip()
        elif current is not None:
            items.append(current)
            current = None
    if current is not None:
        items.append(current)
    return items


def current_module_problems(text):
    """What is wrong with Step 1's `current_module` write; empty when it is right."""
    section = step1(text)
    if not section:
        return ["no `## Step 1:` section"]
    setters = [b for b in bullets(section) if re.search(r"\bSet\s+`current_module`", b)]
    if len(setters) != 1:
        return [f"{len(setters)} bullets set `current_module`; expected exactly one"]
    bullet = setters[0]
    problems = []
    if "next module in `selected_modules`" not in bullet:
        problems.append("does not name the next module in `selected_modules`")
    if "unconditionally" not in bullet:
        problems.append("does not say the write is unconditional")
    for match in CONDITION_ON_THE_ANSWER.finditer(section):
        problems.append(f"conditions the write on the answer: {match.group(0)!r}")
    return problems


def directing_steps_problems(text):
    """What is wrong with Step 1's `directing_steps` entry; empty when it is right."""
    section = step1(text)
    entries = [b for b in bullets(section) if "`directing_steps" in b]
    if len(entries) != 1:
        return [f"{len(entries)} Step 1 bullets name `directing_steps`; expected exactly one"]
    bullet = re.sub(r"\s+", " ", entries[0])
    problems = []
    for module in DIRECTING_MODULES:
        if module not in bullet:
            problems.append(f"does not name {module!r}")
    if not re.search(r"\bonly\b", bullet):
        problems.append("does not limit the write to the three directing modules")
    if not re.search(r"still unset, set it to `none`", bullet):
        problems.append("does not set an unset entry to `none`")
    if not re.search(r"Never overwrite a value a directing step", bullet):
        problems.append("does not forbid overwriting a recorded value")
    return problems


class Step1SetsCurrentModuleUnconditionally(unittest.TestCase):

    def test_the_shipped_step_1(self):
        self.assertEqual(current_module_problems(read()), [])

    def test_the_old_parenthetical_fails(self):
        text = read().replace(
            "in `selected_modules`, unconditionally,",
            "in `selected_modules` (or leave it on this module if the bootcamper has not yet "
            "chosen to advance),", 1)
        self.assertNotEqual(text, read())
        problems = current_module_problems(text)
        self.assertTrue(any("leave it on this module" in p for p in problems), problems)

    def test_the_issue_text_as_it_shipped_fails(self):
        text = re.sub(
            r"- Set `current_module` to the next module in `selected_modules`, unconditionally,"
            r"[^\n]*",
            "- Set `current_module` to the next module in `selected_modules` (or leave it on "
            "this module if the bootcamper has not yet chosen to advance).",
            read(), count=1)
        self.assertNotEqual(text, read())
        self.assertNotEqual(current_module_problems(text), [])

    def test_a_reworded_condition_fails(self):
        text = read().replace(
            "in `selected_modules`, unconditionally,",
            "in `selected_modules` once the Bootcamper has chosen to advance,", 1)
        self.assertNotEqual(text, read())
        self.assertNotEqual(current_module_problems(text), [])

    def test_a_condition_on_the_reply_fails(self):
        text = read().replace(
            "in `selected_modules`, unconditionally,",
            "in `selected_modules` when the bootcamper answers yes,", 1)
        self.assertNotEqual(text, read())
        self.assertNotEqual(current_module_problems(text), [])


class Step1ListsDirectingSteps(unittest.TestCase):

    def test_the_shipped_step_1(self):
        self.assertEqual(directing_steps_problems(read()), [])

    def test_removing_the_bullet_fails(self):
        text = re.sub(r"^- \*\*`directing_steps`[^\n]*\n", "", read(), count=1,
                      flags=re.MULTILINE)
        self.assertNotEqual(text, read())
        problems = directing_steps_problems(text)
        self.assertTrue(any("0 Step 1 bullets" in p for p in problems), problems)

    def test_dropping_the_never_overwrite_clause_fails(self):
        text = re.sub(r"Never overwrite a value a directing step already recorded[^.]*\. ",
                      "", read(), count=1)
        self.assertNotEqual(text, read())
        self.assertNotEqual(directing_steps_problems(text), [])

    def test_step_2b_still_points_at_step_1s_write(self):
        self.assertIn("record `none` in Step 1's write", read())


class Step1StaysOneBatchedWrite(unittest.TestCase):

    def test_single_batched_quiet_write(self):
        section = re.sub(r"\s+", " ", step1(read()))
        self.assertIn("as a **single** batched write", section)
        self.assertIn("done quietly (INV-012", section)

    def test_every_field_step_1_writes_is_a_bullet(self):
        listed = " ".join(bullets(step1(read())))
        for field in ("modules_completed", "current_module", "current_step", "step_history",
                      "directing_steps"):
            self.assertIn(f"`{field}", listed, field)


if __name__ == "__main__":
    unittest.main()
