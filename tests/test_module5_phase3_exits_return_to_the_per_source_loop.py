"""Module 5's Phase 3 is a per-source detour: every exit returns to Phase 2's per-source loop.

Phase 2 step 18a keeps an explicit `test_load` choice "at any source", which enters Phase 3 for
that source. Phase 3 then ended on step 25's "👉 Are you ready to proceed?" and a step 26 that
began "After all sources have completed (or skipped) Phase 3": nothing between them returned to
Phase 2 step 19 while sources remained unmapped, so a test load chosen on source 1 of 3 had no
path to source 2. That is the situation INV-344 was registered for, reached by a second route.
Step 26 also offered a "shortcut path" past Data processing, a Required module (INV-076), and
recorded it under a catalog-number key (`"modules_skipped": {"6": …}`) that nothing read. Phase
3's other exits had the same break: the "SDK not set up" skip marked **every** source skipped
and proceeded to Data processing, step 21's detection-failure skip went nowhere stated, and step
25's "no" had no handling at all (INV-284).

#384 retired step 26:

* step 25's "yes" always continues to Phase 2 step 19, which starts the next unmapped source or,
  when none remains, continues to step 20; its "no" goes to step 17 to iterate on this source;
* the SDK-not-set-up skip and step 21's skip mark **this source only** and resume at step 19;
* a "Leaving Phase 3" section names every exit and where it resumes, with step 26's registry
  note kept there; its advisory baseline-status summary moved to Phase 2 step 20;
* Phase 2 step 20 is Module 5's only Module Completion site;
* a progress file that recorded Module 5 at the old step 26 resumes as "Module 5 complete": only
  step 20's transition question, with no second Module Completion (the one place the number may
  still appear, in Module 5's `SKILL.md`).

⛔ **Each check is a pure function of the file text, so the negative controls run the SAME check
on a mutated copy** (INV-265): restoring step 26, the shortcut JSON, an all-sources skip, a skip
that proceeds to Data processing, a step 25 with no handling, a second completion site, or a
resume rule that re-runs Module Completion must each make it report a problem.

Enforces INV-344 (with INV-076 and INV-284). It asserts that the skill files *state* the routes,
and does **not** establish that a live run follows them, which only `dry-run` phase 3 can observe.

Source issue: #384. Related: #333 (`tests/test_module5_step16_asks_about_loading_only_after_the_last_source.py`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS = REPO_ROOT / "plugins"
MODULE = PLUGINS / "senzing-bootcamp" / "skills" / "module-05-data-quality-mapping"
SKILL = MODULE / "SKILL.md"
PHASE2 = MODULE / "phase2-data-mapping.md"
PHASE3 = MODULE / "phase3-test-load.md"

STEP25_QUESTION = "👉 **Are you ready to proceed?** (respond yes or no)"
LEAVING = "## Leaving Phase 3"
LEAVING_ANCHOR = '<a id="leaving-phase-3"></a>'
COMPLETION_RUN = "Run the standard **Module Completion** process"
#: The same instruction in any case and across a line break, so a wrapped copy is still counted.
RUNS_COMPLETION = re.compile(r"(?i)run\s+the\s+standard\s+\*\*Module\s+Completion\*\*\s+process")
#: How a retired step 26 or the old step range is named.
STEP_26 = re.compile(r"(?i)\bsteps?\s*26\b|\b21\s*[–-]\s*26\b|###\s*26\.")
#: Wording that sends the flow from Phase 3 straight to the next module.
TO_DATA_PROCESSING = re.compile(r"(?i)(?:proceed|continue|go)\s+(?:directly\s+)?to\s+Data processing")
SHORTCUT = re.compile(r"(?i)modules_skipped|shortcut_path|shortcut path|Which path would you like")


def flat(text):
    return re.sub(r"\s+", " ", text)


def between(text, start, end):
    """The text from `start` to the next `end` (or to the end), or None when `start` is absent."""
    if start not in text:
        return None
    i = text.index(start)
    j = text.find(end, i + len(start))
    return text[i:j if j != -1 else len(text)]


def need(block, needles, where):
    f = flat(block)
    return [f"{where} does not say {n!r}" for n in needles if flat(n) not in f]


# ------------------------------------------------------------------------------------- checks


def phase3_problems(text):
    """Criteria 1, 2, 3, 5 and step 26's retirement, inside `phase3-test-load.md`."""
    problems = []
    if STEP_26.search(text):
        problems.append("phase3 still names step 26 or steps 21–26")
    # Line-scoped by design (#424): the title is the file's first line, an ATX heading.
    if "(steps 21–25)" not in text.splitlines()[0]:
        problems.append("phase3's title does not give the steps as 21–25")
    # Matched across line wraps (#424): both carry literal spaces, which a line break defeats.
    if match_lines(text, SHORTCUT):
        problems.append("phase3 still carries the shortcut path or modules_skipped")
    if match_lines(text, TO_DATA_PROCESSING):
        problems.append("phase3 still sends an exit straight to Data processing")
    if "module-completion.md" in text or RUNS_COMPLETION.search(text):
        problems.append("phase3 still runs Module Completion")

    before = between(text, "**Before starting Phase 3:**", "## Workflow")
    if before is None:
        problems.append("the SDK-not-set-up paragraph is missing")
    else:
        if re.search(r"(?i)for each source|every source|all sources", before):
            problems.append("the SDK-not-set-up skip marks sources other than this one")
        problems += need(before, ("**this source only**", "Phase 2 step 19",
                                  "#leaving-phase-3"), "the SDK-not-set-up skip")

    s21 = between(text, "### 21. SDK environment detection", "### 21a.")
    if s21 is None:
        problems.append("step 21 is missing")
    else:
        problems += need(s21, ("skip this source's test load", "**this source only**",
                               "Phase 2 step 19"), "step 21's detection-failure skip")

    s25 = between(text, "### 25.", LEAVING_ANCHOR)
    if s25 is None:
        problems.append("step 25 is missing, or is not followed by Leaving Phase 3")
    else:
        if s25.count(STEP25_QUESTION) != 1:
            problems.append("step 25's pinned question is not kept verbatim once")
        if s25.count("👉") != 1:
            problems.append("step 25 asks a second 👉 question")
        problems += need(s25, (
            "Handling (INV-284)",
            "**yes** → Phase 2 step 19",
            "starts the next unmapped source's own `mapping_workflow` run",
            "when no unmapped source remains, continues to step 20",
            "Ask no question about the whole run here (INV-344)",
            "**no** → Phase 2 step 17",
            "explicit **test_load** at step 18a again",
            "`test_load_status` to `complete`",
        ), "step 25")

    leaving = between(text, LEAVING, "\n## ")
    if leaving is None or LEAVING_ANCHOR not in text:
        problems.append("there is no anchored Leaving Phase 3 section")
    else:
        problems += need(leaving, (
            "⛔ **(INV-344) Every exit from Phase 3 returns to Phase 2's per-source loop.**",
            "none asks a question about the whole run",
            "none proceeds to Data processing directly",
            "none writes the registry entry of any source other than this one",
            "**Data source registry (skip exit):**",
            "Update **this source's** `test_load_status` to `skipped`",
            "Leave every other source's entry as it is",
            "⛔ **(INV-076) Phase 3 offers no route past Data processing.**",
            "Phase 2 step 20",
            "Phase 3 never runs Module Completion",
        ), "Leaving Phase 3")
        # Line-scoped by design (#424): a table row is one line.
        rows = [r for r in leaving.splitlines() if r.startswith("| ") and "---" not in r][1:]
        exits = {"SDK not set up": "Phase 2 step 19", "detection fails": "Phase 2 step 19",
                 "Step 25 **yes**": "Phase 2 step 19", "Step 25 **no**": "Phase 2 step 17"}
        for name, target in exits.items():
            row = [r for r in rows if name in r]
            if len(row) != 1:
                problems.append(f"Leaving Phase 3 has no single row for the exit {name!r}")
            elif not row[0].rstrip(" |").endswith(target):
                problems.append(f"the exit {name!r} does not resume at {target}")
        if len(rows) != len(exits):
            problems.append("Leaving Phase 3 lists an exit the issue does not name")

    resume = between(text, "## Phase 3 session resume", "\n## ")
    if resume is None:
        problems.append("the Phase 3 session-resume section is missing")
    else:
        problems += need(resume, ("(21–25)", "Step 25 is Phase 3's last gate",
                                  "resume from step 25", "`SKILL.md` → \"Resuming\""),
                         "the Phase 3 session resume")
    success = between(text, "## Success criteria", "\n## ")
    if success is None or "Step 25 answered, and the flow returned to Phase 2" not in success:
        problems.append("the success criteria do not end on the return to Phase 2")
    return problems


def phase2_problems(text):
    """Step 18a, step 20 and the step map in `phase2-data-mapping.md`."""
    problems = []
    if STEP_26.search(text):
        problems.append("phase2 still names Module 5's step 26 or steps 21–26")
    if "| Phase 3 (21-25) |" not in text:
        problems.append("phase2's step map does not give Phase 3 as 21-25")
    s18a = between(text, "### 18a.", "### 19.")
    if s18a is None:
        problems.append("step 18a is missing")
    else:
        problems += need(s18a, (
            "every exit from it returns here",
            "its step 25 \"yes\" and its skip exits resume at step 19",
            "its step 25 \"no\" at step 17",
            "continues to the next unmapped source, with no question about the whole run",
        ), "step 18a")
    s20 = between(text, "### 20. Module completion and transition", "\n## ")
    if s20 is None:
        problems.append("step 20 is missing")
    else:
        problems += need(s20, (
            "Module 5's only completion site",
            "Phase 3 returns to step 19 and never completes the module",
            "**Optional: baseline status summary (advisory, non-blocking):**",
            "never creates, modifies, or deletes a baseline",
            "**Run Module Completion exactly once,** here: Phase 3 never runs it.",
            "`SKILL.md` → \"Resuming\"",
        ), "step 20")
    return problems


def skill_problems(text):
    """Module 5's `SKILL.md`: the phase list and the step-26 resume rule (criterion 6)."""
    problems = []
    if "(steps 21–25): `phase3-test-load.md`" not in text:
        problems.append("SKILL.md does not list Phase 3 as steps 21–25")
    if re.search(r"\b21\s*[–-]\s*26\b", text):
        problems.append("SKILL.md still names steps 21–26")
    first = between(text, "**First:**", "\n\n")
    if first is None or "retired step 26, none of this runs either" not in flat(first):
        problems.append("the First: clause does not send a recorded step 26 to Resuming")
    resuming = between(text, "## Resuming", "\n## ")
    rule = None if resuming is None else between(
        resuming, "**A progress file that recorded Module 5 at step 26.**", "\n\n")
    if rule is None:
        return problems + ["SKILL.md has no Resuming rule for a recorded step 26"]
    problems += need(rule, (
        "ran Module Completion and then wrote its checkpoint",
        "means Module 5 is already complete",
        "present only Phase 2 step 20's pinned transition 👉 question",
        "naming the next selected module from `selected_modules`",
        "Do not run Module Completion again",
        "no second Module 5 recap section",
        "no second end-of-module summary",
    ), "the step-26 resume rule")
    if re.search(r"(?i)\b(?:re-?run|run) (?:the standard )?\*?\*?Module Completion\*?\*? (?:process|first)",
                 rule):
        problems.append("the step-26 resume rule runs Module Completion")
    return problems


def corpus_problems(files):
    """Plugin-wide: nothing writes `modules_skipped`; Module 5 has one completion site.

    `files` maps a path relative to `plugins/` to its text. "step 26" is checked only inside
    Module 5's directory, because Module 6 has a step 26 of its own.
    """
    problems = []
    module5 = "senzing-bootcamp/skills/module-05-data-quality-mapping/"
    for rel, text in files.items():
        if re.search(r"modules_skipped|shortcut_path", text):
            problems.append(f"{rel} still writes modules_skipped or shortcut_path")
        if re.search(r"\b21\s*[–-]\s*26\b", text):
            problems.append(f"{rel} still names steps 21–26")
        if rel.startswith(module5) and rel != module5 + "SKILL.md" and STEP_26.search(text):
            problems.append(f"{rel} still names Module 5's step 26")
    sites = [rel for rel, text in files.items()
             if rel.startswith(module5) and RUNS_COMPLETION.search(text)]
    if sites != [module5 + "phase2-data-mapping.md"]:
        problems.append(f"Module 5's Module Completion sites are {sites}, not phase2 step 20 alone")
    return problems


def read_corpus():
    return {str(p.relative_to(PLUGINS)): p.read_text(encoding="utf-8")
            for p in sorted(PLUGINS.rglob("*")) if p.suffix in (".md", ".json", ".py", ".yaml")
            and p.is_file()}


# -------------------------------------------------------------------------------------- tests


class Phase3ExitsReturnToThePerSourceLoop(unittest.TestCase):
    def setUp(self):
        self.p3 = PHASE3.read_text(encoding="utf-8")
        self.p2 = PHASE2.read_text(encoding="utf-8")
        self.skill = SKILL.read_text(encoding="utf-8")

    def test_phase3(self):
        self.assertEqual([], phase3_problems(self.p3))

    def test_phase2(self):
        self.assertEqual([], phase2_problems(self.p2))

    def test_skill(self):
        self.assertEqual([], skill_problems(self.skill))

    def test_corpus(self):
        self.assertEqual([], corpus_problems(read_corpus()))

    def mutate(self, text, old, new):
        self.assertIn(old, text, "the negative control no longer applies")
        return text.replace(old, new, 1)

    def test_negative_controls_phase3(self):
        """Each mutation reintroduces a defect #384 fixed; each must be reported."""
        p3 = self.p3
        mutants = {
            "step 26 restored": self.mutate(p3, LEAVING_ANCHOR,
                                            "### 26. Module completion and shortcut path decision\n\n"
                                            + LEAVING_ANCHOR),
            "shortcut JSON restored": self.mutate(
                p3, LEAVING_ANCHOR,
                '```json\n{"modules_skipped": {"6": {"reason": "shortcut_path"}}}\n```\n\n'
                + LEAVING_ANCHOR),
            "SDK skip marks every source": self.mutate(
                p3, "`test_load_status: skipped` for **this source\nonly**",
                "`test_load_status: skipped` for each source"),
            "SDK skip proceeds to Data processing": self.mutate(
                p3, "then Phase 2 step 19.\n\n## Workflow",
                "then proceed to Data processing.\n\n## Workflow"),
            "step 21 skip unrouted": self.mutate(
                p3, "source only**, then Phase 2 step 19. (Pass", "source only**. (Pass"),
            "step 25 yes asks a whole-run question": self.mutate(
                p3, "**Checkpoint:** write step 25.",
                "👉 **Which path would you like to take?**\n\n**Checkpoint:** write step 25."),
            "step 25 no unhandled": self.mutate(p3, "- **no** → Phase 2 step 17", "- **no** →"),
            "step 25 yes goes to Data processing": self.mutate(
                p3, "- **yes** → Phase 2 step 19 (", "- **yes** → continue to Data processing ("),
            "an exit row dropped": self.mutate(
                p3, "| Step 21 detection fails, and the bootcamper skips | `test_load_status: "
                    "skipped` | Phase 2 step 19 |\n", ""),
            "an exit row retargeted": self.mutate(
                p3, "| as step 25's registry note left it | Phase 2 step 17 |",
                "| as step 25's registry note left it | Data processing |"),
            "Phase 3 runs Module Completion": self.mutate(
                p3, "**Checkpoint:** write step 25.",
                COMPLETION_RUN + " in `../bootcamp-onboarding/module-completion.md`.\n\n"
                "**Checkpoint:** write step 25."),
            "skip registry note marks others": self.mutate(
                p3, "Leave every other source's entry as it is", "Mark every unmapped source too"),
            "resume points at step 26": self.mutate(p3, "which Phase 3 steps (21–25) completed",
                                                    "which Phase 3 steps (21–26) completed"),
            "title keeps 21–26": self.mutate(p3, "(steps 21–25)", "(steps 21–26)"),
            # #424: the same two defects, wrapped inside the phrase.
            "SDK skip proceeds to Data processing, wrapped": self.mutate(
                p3, "then Phase 2 step 19.\n\n## Workflow",
                "then proceed to Data\nprocessing.\n\n## Workflow"),
            "step 25 yes asks a whole-run question, wrapped": self.mutate(
                p3, "**Checkpoint:** write step 25.",
                "👉 **Which path would\nyou like to take?**\n\n**Checkpoint:** write step 25."),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual([], phase3_problems(mutant))

    def test_the_wrapped_mutants_are_the_hard_case(self):
        """#424: a raw-text search for either phrase misses the wrapped form."""
        self.assertIsNone(TO_DATA_PROCESSING.search("then proceed to Data\nprocessing."))
        self.assertIsNone(SHORTCUT.search("👉 **Which path would\nyou like to take?**"))

    def test_negative_controls_phase2(self):
        p2 = self.p2
        mutants = {
            "18a's return dropped": self.mutate(p2, "every exit from it returns here", "it ends"),
            "step 20 shares completion": self.mutate(p2, "Module 5's only completion site",
                                                     "Module 5's completion site"),
            "baseline summary lost": self.mutate(
                p2, "**Optional: baseline status summary (advisory, non-blocking):**", "**Note:**"),
            "step 26 named again": self.mutate(p2, "here: Phase 3 never runs it.",
                                               "unless Phase 3's step 26 already completed it."),
            "step map keeps 21-26": self.mutate(p2, "| Phase 3 (21-25) |", "| Phase 3 (21-26) |"),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual([], phase2_problems(mutant))

    def test_negative_controls_skill(self):
        s = self.skill
        mutants = {
            "resume re-runs completion": self.mutate(
                s, "Do not run Module Completion again: no second Module 5 recap section, no second\n"
                   "end-of-module summary",
                "Run the standard Module Completion process first"),
            "resume rule dropped": self.mutate(
                s, "**A progress file that recorded Module 5 at step 26.**", "**Older files.**"),
            "resume asks the Phase 3 question": self.mutate(
                s, "present only Phase 2 step 20's pinned\ntransition 👉 question",
                "present Phase 3's step 25 question"),
            "First: pointer dropped": self.mutate(
                s, "retired step 26, none of this runs either", "retired step 26, run as usual"),
            "phase list keeps 21–26": self.mutate(s, "(steps 21–25): `phase3-test-load.md`",
                                                  "(steps 21–26): `phase3-test-load.md`"),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual([], skill_problems(mutant))

    def test_negative_controls_corpus(self):
        files = read_corpus()
        p3 = "senzing-bootcamp/skills/module-05-data-quality-mapping/phase3-test-load.md"
        p2 = "senzing-bootcamp/skills/module-05-data-quality-mapping/phase2-data-mapping.md"
        m6 = "senzing-bootcamp/skills/module-06-data-processing/phaseD-validation.md"
        self.assertTrue(STEP_26.search(files[m6]), "Module 6's own step 26 moved; re-aim the control")
        cases = {
            "modules_skipped elsewhere": {**files, "senzing-bootcamp/x.md": '"modules_skipped": {}'},
            "second completion site": {**files, p3: files[p3] + "\n" + COMPLETION_RUN + "\n"},
            "no completion site": {**files, p2: files[p2].replace(COMPLETION_RUN, "Run it")},
            "step 26 in Module 5": {**files, p3: files[p3] + "\nSee step 26.\n"},
        }
        for name, corpus in cases.items():
            with self.subTest(mutant=name):
                self.assertNotEqual([], corpus_problems(corpus))
        # Module 6's own step 26 is not Module 5's, and must not be reported.
        self.assertEqual([], corpus_problems(files))


if __name__ == "__main__":
    unittest.main()
