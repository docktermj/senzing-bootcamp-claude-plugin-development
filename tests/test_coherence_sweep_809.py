"""Pointer and wording fixes from the 2026-10-22 production-readiness audit (#809, part of #798).

Each item was a pointer that landed on the wrong section, or a sibling statement that disagreed
with the one it restated. Four items are guarded beside the rule they serve, each with its own
negative control:

- INV-389's bare `scripts/<name>.py` spellings: ``test_bundled_script_and_production_paths.py``
  (``bare_paths_in``);
- INV-373's restatement in ``ground-rules.md``: ``test_reversed_decision_capture.py``
  (``TheGroundRulesPointAtTheOneStatement``);
- INV-227's missing "not a JSON object" case in ``/start-bootcamp``:
  ``test_resume_requires_a_recorded_module.py`` (``start_command_case_problems``);
- INV-400's unlinked accuracy figure in Phase D steps 21 and 24:
  ``test_phase_d_gate_routes_on_both_metrics.py`` (``step_link_problems``).

This file holds the rest, one check per item:

1. **Step 2b.** Graduation Step 0b reads each module's **Questions & Responses**, which
   ``module-completion.md`` Step 2b writes (Step 2a only creates the recap's header).
2. **Why it matters.** Graduation's backfill draws it from the module's own **Before/After**
   line, not from ``onboarding-flow.md``, which lists module names and no purposes.
3. **The SQLite pointer.** Graduation's Pre-checks point at Module 4's section by its heading,
   "8b. SQLite load-time warning", not at "the SQLite volume warning", which names no section.
4. **The content check.** Step 1b's content check is required after every render and
   non-blocking, as "Verify the artifact" says; it is no longer called optional.
5. **The banner.** Graduation's banner is "BOOTCAMP GRADUATION"; nothing calls it "the
   GRADUATION banner" (read from the banner's own fence, so a renamed banner is followed).
6. **Module 0's departures.** Module 0 skips module-completion Step 3 and replaces Step 4's
   transition question with its own readiness gate; it names both.
7. **The error-handling block.** Every module whose error-handling step 1 calls
   ``explain_error_code`` says "If it returns nothing, continue to step 2." Modules 3 and 3b
   did not.

Every check is a pure function over a file's text that returns a list of problems, so each one
also runs on a mutated copy of the shipped text as its negative control: the control puts the
audited defect back and asserts the check reports it.

⚠️ **Phrase checks collapse whitespace (INV-346)**, so a phrase wrapped across lines still
matches.

⛔ **What this cannot establish:** that a live guide follows any of these passages. It pins that
the skill files STATE them; ``dry-run`` phase 3 observes a run.

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issue: #809.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _pointer_sites import section_pointer_problems, section_pointers

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"

GRADUATION = SKILLS / "graduation" / "SKILL.md"
GRADUATE_COMMAND = PLUGIN / "commands" / "graduate.md"
MODULE_COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"
MODULE_0 = SKILLS / "module-00-entity-resolution-concepts" / "SKILL.md"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"

RETURNS_NOTHING = "If it returns nothing, continue to step 2."


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def section(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


# --- Item 1: Questions & Responses is written by Step 2b ----------------------------------------

def substep(text, label):
    """``module-completion.md``'s ``### <label>.`` substep, up to the next substep or Step.

    The substep's recap template is a fenced block holding its own ``##``/``###`` headings, so
    the end is the next ``### 2x.`` substep or ``## Step`` heading, not any heading.
    """
    lines = text.split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith("### %s. " % label))
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r"### 2[a-z]\. |## Step ", lines[i])), len(lines))
    return "\n".join(lines[start:end])


def step_2b_problems(graduation, completion):
    """The Step 0b pointer names the substep whose template carries Questions & Responses."""
    m = re.search(r"\*\*Questions & Responses\*\* \(the record "
                  r"`\.\./bootcamp-onboarding/module-completion\.md` Step (2[a-e]) writes\)",
                  flat(graduation))
    if m is None:
        return ["graduation Step 0b's Questions & Responses pointer moved"]
    if "### Questions & Responses" not in substep(completion, m.group(1)):
        return ["graduation names module-completion Step %s, which does not write Questions & "
                "Responses" % m.group(1)]
    return []


# --- Item 2: Why it matters comes from the module's Before/After line ---------------------------

def why_it_matters_problems(graduation):
    backfill = flat(section(graduation, "**Backfill the End-of-Module Summary blocks",
                            "**Write each block in its required shape.**"))
    problems = []
    if "onboarding-flow.md" in backfill:
        problems.append("the backfill still draws from onboarding-flow.md")
    if "**Before/After** line gives **Why it matters**" not in backfill:
        problems.append("the backfill does not draw Why it matters from the Before/After line")
    if "Entity Resolution Concepts has no Before/After line" not in backfill:
        problems.append("the backfill does not say where Module 0's Why it matters comes from")
    return problems


def before_after_sources():
    """Each module skill directory with the file holding its Before/After line, or None."""
    out = {}
    for skill in sorted(SKILLS.glob("module-*")):
        holders = [p for p in sorted(skill.glob("*.md")) if "**Before/After" in read(p)]
        out[skill.name] = holders[0].name if holders else None
    return out


# --- Item 3: the SQLite pointer names Module 4's section ----------------------------------------

def sqlite_pointer_problems(graduation):
    prechecks = section(graduation, "## Pre-checks", "## Step 0:")
    if "the SQLite volume warning" in flat(prechecks):
        return ["graduation still points at \"the SQLite volume warning\", which names no section"]
    targets = [(target, name) for _, target, name in section_pointers(GRADUATION, prechecks)
               if target == "../module-04-data-collection/SKILL.md"]
    if ("../module-04-data-collection/SKILL.md", "8b. SQLite load-time warning") not in targets:
        return ["graduation's Pre-checks do not point at Module 4 → \"8b. SQLite load-time "
                "warning\""]
    return section_pointer_problems(GRADUATION, prechecks)


# --- Item 4: the content check is required after every render ------------------------------------

def content_check_problems(graduation):
    m = re.search(r"- \*\*Content check \(([^)]*)\):\*\*", graduation)
    if m is None:
        return ["Step 1b's content check bullet moved"]
    problems = []
    qualifier = m.group(1)
    if "optional" in qualifier:
        problems.append("the content check is still called optional")
    if "required after every render" not in qualifier or "non-blocking" not in qualifier:
        problems.append("the content check is not required after every render and non-blocking")
    if 'Re-run `--check --expect-modules "…"` after every render' not in flat(graduation):
        problems.append("\"Verify the artifact\" no longer requires the re-run after every render")
    return problems


# --- Item 5: the banner's name ----------------------------------------------------------------

def banner_name(graduation):
    """The name the graduation banner's own fence shows, e.g. "BOOTCAMP GRADUATION"."""
    fence = section(graduation, "## Bootcamp graduation banner", "## Bootcamp graduation preface")
    m = re.search(r"🎓+\s+([A-Z][A-Z ]*[A-Z])\s+🎓+", fence)
    return m.group(1) if m else None


def banner_problems(name, texts):
    """Each `<words> banner` naming the graduation banner by anything but its full name."""
    if name is None:
        return ["the graduation banner's fence moved"]
    last = name.split()[-1]
    problems = []
    for label, text in texts.items():
        for m in re.finditer(r"((?:[A-Z]+ )*%s) banner" % re.escape(last), flat(text)):
            if m.group(1) != name:
                problems.append("%s calls it \"the %s banner\", not \"the %s banner\""
                                % (label, m.group(1), name))
    return problems


# --- Item 6: Module 0 names both departures -----------------------------------------------------

def module_0_problems(text):
    body = flat(text)
    problems = []
    if "ONLY module-completion" in body:
        problems.append("Module 0 still says it skips only one module-completion Step")
    if "it **skips** Step 3" not in body:
        problems.append("Module 0 does not say it skips Step 3")
    if ("it **replaces** Step 4's transition question with its own readiness gate"
            not in body):
        problems.append("Module 0 does not say its readiness gate replaces Step 4's question")
    return problems


# --- Item 7: every error-handling block continues to step 2 --------------------------------------

def error_block_problems(texts):
    """Each module whose error-handling step 1 calls explain_error_code without the fall-through."""
    problems = []
    for label, text in sorted(texts.items()):
        if "## Error handling" not in text:
            continue
        block = text[text.index("## Error handling"):]
        m = re.search(r"\n1\. \*\*SENZ error code\*\*(.*?)\n2\. ", block, re.S)
        if m is None:
            continue
        if "explain_error_code" in m.group(1) and RETURNS_NOTHING not in flat(m.group(1)):
            problems.append("%s: step 1 calls explain_error_code with no fall-through" % label)
    return problems


def module_skills():
    return {p.parent.name: read(p) for p in sorted(SKILLS.glob("module-*/SKILL.md"))}


class Item1TheRecapRecordIsStep2b(unittest.TestCase):

    def test_the_shipped_pointer_names_step_2b(self):
        self.assertEqual([], step_2b_problems(read(GRADUATION), read(MODULE_COMPLETION)))

    def test_negative_control_step_2a_is_reported(self):
        text = read(GRADUATION)
        mutant = text.replace("module-completion.md` Step 2b writes)",
                              "module-completion.md` Step 2a writes)", 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertEqual(1, len(step_2b_problems(mutant, read(MODULE_COMPLETION))))


class Item2WhyItMattersComesFromBeforeAfter(unittest.TestCase):

    def test_the_backfill_names_the_before_after_line(self):
        self.assertEqual([], why_it_matters_problems(read(GRADUATION)))

    def test_every_module_but_module_0_has_a_before_after_line(self):
        """The source the backfill names exists, and Module 0 is the one exception it states."""
        sources = before_after_sources()
        self.assertGreaterEqual(len(sources), 9)
        self.assertEqual(["module-00-entity-resolution-concepts"],
                         [name for name, holder in sources.items() if holder is None])
        self.assertEqual("phase1-visualization.md",
                         sources["module-03b-truthset-visualization"])
        self.assertEqual("SKILL.md", sources["module-04-data-collection"])

    def test_negative_control_the_onboarding_flow_source_is_reported(self):
        text = read(GRADUATION)
        old = ("the module's own\n**Before/After** line gives **Why it matters**, taken from its "
               "own `SKILL.md`")
        self.assertIn(old, text, "the negative control is stale")
        mutant = text.replace(old, "the module's purpose in\n`../bootcamp-onboarding/"
                              "onboarding-flow.md` gives **Why it matters**, taken from its own "
                              "`SKILL.md`", 1)
        self.assertEqual(2, len(why_it_matters_problems(mutant)), why_it_matters_problems(mutant))


class Item3TheSqlitePointerNamesASection(unittest.TestCase):

    def test_the_shipped_pointer_lands_on_the_heading(self):
        self.assertEqual([], sqlite_pointer_problems(read(GRADUATION)))
        self.assertIn("### 8b. SQLite load-time warning", read(MODULE_4))

    def test_negative_control_the_unnamed_section_is_reported(self):
        text = read(GRADUATION)
        new = '(`../module-04-data-collection/SKILL.md` → "8b. SQLite load-time warning")'
        self.assertIn(new, text, "the negative control is stale")
        mutant = text.replace(new, "(`../module-04-data-collection/SKILL.md` → the SQLite volume "
                              "warning)", 1)
        self.assertEqual(1, len(sqlite_pointer_problems(mutant)))

    def test_negative_control_a_wrong_heading_is_reported(self):
        text = read(GRADUATION)
        mutant = text.replace('→ "8b. SQLite load-time warning"', '→ "8b. SQLite volume warning"',
                              1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertEqual(1, len(sqlite_pointer_problems(mutant)))


class Item4TheContentCheckIsRequired(unittest.TestCase):

    def test_the_two_statements_agree(self):
        self.assertEqual([], content_check_problems(read(GRADUATION)))

    def test_negative_control_optional_is_reported(self):
        text = read(GRADUATION)
        mutant = text.replace("**Content check (required after every render, non-blocking):**",
                              "**Content check (optional, non-blocking):**", 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertEqual(2, len(content_check_problems(mutant)), content_check_problems(mutant))


class Item5TheBannerIsNamedInFull(unittest.TestCase):

    def texts(self):
        return {"graduation/SKILL.md": read(GRADUATION), "commands/graduate.md":
                read(GRADUATE_COMMAND)}

    def test_the_banner_name_is_read_from_its_fence(self):
        self.assertEqual("BOOTCAMP GRADUATION", banner_name(read(GRADUATION)))

    def test_no_site_shortens_the_name(self):
        texts = self.texts()
        self.assertEqual([], banner_problems(banner_name(texts["graduation/SKILL.md"]), texts))
        for label, text in texts.items():
            with self.subTest(file=label):
                self.assertNotIn("the GRADUATION banner", flat(text))
                self.assertIn("the BOOTCAMP GRADUATION banner", flat(text))

    def test_negative_control_each_shortened_site_is_reported(self):
        texts = self.texts()
        for label in texts:
            with self.subTest(file=label):
                mutant = dict(texts)
                mutant[label] = texts[label].replace("BOOTCAMP GRADUATION banner",
                                                     "GRADUATION banner", 1)
                self.assertNotEqual(texts[label], mutant[label], "the mutation no longer applies")
                self.assertEqual(1, len(banner_problems("BOOTCAMP GRADUATION", mutant)))


class Item6Module0NamesBothDepartures(unittest.TestCase):

    def test_the_shipped_sentence_names_steps_3_and_4(self):
        self.assertEqual([], module_0_problems(read(MODULE_0)))

    def test_the_readiness_gate_and_both_steps_exist(self):
        """The steps the sentence names are module-completion's Steps 3 and 4, and the gate is
        Module 0's own Step 1 item 5."""
        completion = read(MODULE_COMPLETION)
        self.assertIn("## Step 3: End-of-module summary", completion)
        self.assertIn("## Step 4: Transition question", completion)
        self.assertIn("5. End on the mandatory exploration gate", read(MODULE_0))

    def test_negative_control_the_old_sentence_is_reported(self):
        text = read(MODULE_0)
        new = ("Module 0 runs module-completion Step 2 whole and departs from it at two **Steps** "
               "only:\n   it **skips** Step 3, so it does **not** present the bootcamper-facing "
               "end-of-module summary,\n   and it **replaces** Step 4's transition question with "
               "its own readiness gate (Step 1, item 5\n   above).")
        self.assertIn(new, text, "the negative control is stale")
        mutant = text.replace(new, "This is the ONLY module-completion **Step** Module 0 skips "
                              "out of — it runs Step 2 whole\n   and does **not** present the "
                              "bootcamper-facing end-of-module summary (Step 3).", 1)
        self.assertEqual(3, len(module_0_problems(mutant)), module_0_problems(mutant))


class Item7EveryErrorBlockFallsThrough(unittest.TestCase):

    def test_every_module_block_says_it(self):
        self.assertEqual([], error_block_problems(module_skills()))

    def test_the_scan_reads_every_module_with_a_block(self):
        """⛔ INV-265: a scan that matched no block would pass forever."""
        texts = module_skills()
        with_block = [name for name, text in texts.items()
                      if re.search(r"\n1\. \*\*SENZ error code\*\*", text)]
        self.assertGreaterEqual(len(with_block), 8)
        for name in ("module-03-system-verification", "module-03b-truthset-visualization"):
            self.assertIn(name, with_block)

    def test_negative_control_modules_3_and_3b_are_reported(self):
        texts = module_skills()
        for name in ("module-03-system-verification", "module-03b-truthset-visualization"):
            with self.subTest(module=name):
                mutant = dict(texts)
                mutant[name] = texts[name].replace(" " + RETURNS_NOTHING, "", 1)
                self.assertNotEqual(texts[name], mutant[name], "the mutation no longer applies")
                self.assertEqual(1, len(error_block_problems(mutant)))


if __name__ == "__main__":
    unittest.main()
