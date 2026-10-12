"""A source skipped at Module 5's validator-rejection gate has one meaning, and every step uses it (#527).

Module 5 Phase 2 step 11 asks a pinned 👉 question after `mapping_workflow`'s step-3 validation
rejects a source twice without an actionable reason. Only its option 1 (write the mapper against
the Senzing Entity Specification) had a handling step. Option 2 ("Try the mapping workflow once
more") and option 3 ("Skip this source") had none (INV-284), and a skipped source kept a
`mapping_status` that was not `complete`, so step 16 kept proposing it as `{next}`, step 20 ("Once
all sources are mapped") never arrived, and Module 6's treatment of it was undefined (#504 item 2).

#527 adds the handlers and a fourth `mapping_status` value, `skipped`:

- **The value is defined once**, in Module 4 Step 2's registry schema, where every
  `mapping_status` value is listed (anchor `mapping-status-values`). What `skipped` means is
  stated there and nowhere else (INV-300).
- **Each consumer points there and states only its own action:** Module 5's fast-path skip and
  checkpoint resume, step 16 (an unmapped source is neither `complete` nor `skipped`), step 19
  (the mapping-spec check does not apply), step 20 (complete once every source is `complete` or
  `skipped`, and the recap names each skipped source and why), Module 6 Phase A step 2 and
  Phase C's gate (not loaded), and graduation (the projection leaves it out; the README names it).
- **The gate.** Option 2 runs `mapping_workflow` once more in full. A second unactionable
  rejection is recorded and the gate is asked again without option 2 (a new state, not an INV-006
  repeat). Option 3 writes `skipped` and continues at step 19. Option 3 is left out when no other
  source is `complete`. When only option 1 remains, there is one sensible answer, so the step
  says what it will do in one line and asks nothing, with no 👉 (#488's settled rule). The
  question's wording is unchanged (INV-056).

Step 16's new condition is what INV-344's proposed #527 amendment states (queued for the
maintainer's sign-off). These tests assert that the skill files *state* the rules, with negative
controls, and **cannot** establish that a live run follows them, which only `dry-run` phase 3 can
observe. Every phrase check reads whitespace-collapsed text with blockquote markers stripped, so
a re-wrap neither hides a phrase nor fails a correct one (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE4 = SKILLS / "module-04-data-collection" / "SKILL.md"
MODULE5 = SKILLS / "module-05-data-quality-mapping" / "SKILL.md"
PHASE2 = SKILLS / "module-05-data-quality-mapping" / "phase2-data-mapping.md"
PHASE_A = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"
PHASE_C = SKILLS / "module-06-data-processing" / "phaseC-multi-source.md"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

ANCHOR_ID = "mapping-status-values"
ANCHOR = '<a id="%s"></a>' % ANCHOR_ID
#: The pointer every consumer carries: a link to the one statement of what `skipped` means.
POINTER = "(../module-04-data-collection/SKILL.md#%s)" % ANCHOR_ID
LINK = "[what `skipped` means]" + POINTER

QUESTION = ("👉 **The mapping validator rejected this source twice without saying why. How would "
            "you like to proceed? Reply with a number:**")
OPTIONS = (
    "1. **Write the mapper against the Senzing Entity Specification** *(recommended)* — all "
    "three quality gates still run.",
    "2. **Try the mapping workflow once more** — it may succeed with a different payload.",
    "3. **Skip this source** — continue with the sources that mapped successfully.",
)

#: Phrases only the definition says. A consumer that carries one restates the meaning (INV-300).
DEFINITION_ONLY = (
    "It is not an unmapped source.",
    "It is not a mapped source.",
    "It is named wherever it is left out:",
    "is kept, and never resumed.",
)


def flat(text):
    """Blockquote markers stripped and whitespace collapsed, so a phrase survives a re-wrap."""
    text = re.sub(r"(?m)^[ \t]*(?:>[ \t]?)+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def between(text, start, end):
    """The text from ``start`` to ``end``, or None when either has moved."""
    a = text.find(start)
    if a < 0:
        return None
    b = text.find(end, a + len(start))
    return None if b < 0 else text[a:b]


def missing(section, needles, where):
    """One problem per needle the collapsed section does not carry."""
    if section is None:
        return ["%s moved" % where]
    f = flat(section)
    return ["%s does not state %r" % (where, n) for n in needles if flat(n) not in f]


def restatements(section, where):
    """One problem per definition-only phrase a consumer copies."""
    if section is None:
        return []
    f = flat(section)
    return ["%s restates the definition: %r" % (where, p) for p in DEFINITION_ONLY if p in f]


# --- The one statement -------------------------------------------------------------------------

def definition_problems(module4):
    problems = []
    if module4.count(ANCHOR) != 1:
        return ["Module 4 does not carry the %s anchor exactly once" % ANCHOR_ID]
    schema = between(module4, "> **Data Source Registry:**", "> **Data File Validation:**")
    if schema is None:
        return ["Module 4 Step 2's registry schema moved"]
    if ANCHOR not in schema:
        problems.append("the anchor is not in Step 2's registry schema")
    problems += missing(schema, (
        "`mapping_status: pending`",
        "`mapping_status` (`pending` | `in_progress` | `complete` | `skipped`)",
        "`skipped` only when the Bootcamper chooses to skip the source at Phase 2 step 11's "
        "validator-rejection gate",
        "What `skipped` means is stated here once (INV-300), and every step that reads "
        "`mapping_status` points here and states only what it does with it.",
        "A `skipped` source has no mapper and no Senzing-ready file",
        "It is not an unmapped source.",
        "Nothing maps it next, offers it as the next source, or waits for it before Module 5 "
        "completes.",
        "It is not a mapped source.",
        "Nothing loads it, and the production configuration leaves it out.",
        "in Module 5's recap, with why it was skipped, and in the production README, as not mapped",
        "Its `config/mapping_state_[datasource].json` is kept, and never resumed.",
        "the source's only copy of `validation_rejections`",
    ), "Module 4's definition")
    return problems


def single_statement_problems(corpus):
    """Each definition-only phrase is in Module 4 alone (INV-300). ``corpus`` maps path -> text."""
    problems = []
    for phrase in DEFINITION_ONLY:
        holders = sorted(p for p, text in corpus.items() if phrase in flat(text))
        if holders != ["module-04-data-collection/SKILL.md"]:
            problems.append("%r is stated in %s, not in Module 4 alone" % (phrase, holders))
    return problems


def pointer_problems(corpus):
    """Every link to the anchor resolves to Module 4's one statement."""
    problems = []
    links = 0
    for rel, text in corpus.items():
        for target in re.findall(r"\(([^()\s]*#%s)\)" % ANCHOR_ID, text):
            links += 1
            path = (SKILLS / rel).parent / target.split("#")[0]
            if path.resolve() != MODULE4.resolve():
                problems.append("%s links %s, not Module 4's SKILL.md" % (rel, target))
    if links == 0:
        problems.append("no skill file links the definition")
    return problems


# --- The gate ----------------------------------------------------------------------------------

def rejection_section(phase2):
    return between(phase2, "When `mapping_workflow`'s step-3 validation rejects the payload",
                   "These gates are structural, not semantic")


def gate_problems(phase2):
    section = rejection_section(phase2)
    if section is None:
        return ["the validator-rejection block moved"]
    problems = []
    if section.count(QUESTION) != 1:
        return ["the pinned question is not kept verbatim once (INV-056)"]
    q = section.index(QUESTION)
    after_q = section[q:]
    for option in OPTIONS:
        if option not in after_q.split("\n\n   *(Internal")[0]:
            problems.append("the pinned option is not kept verbatim: %r" % option[:50])
    asks = len(re.findall(r"👉\s*\*\*", section))
    if asks != 1:
        # The pinned question is the block's only 👉 question; every other case asks nothing.
        problems.append("the block asks %d 👉 questions, not 1" % asks)

    offered = between(section, "**Which options are offered.**", "\n\n")
    problems += missing(offered, (
        "Leave option 3 out when no other source in `config/data_sources.yaml` has "
        "`mapping_status: complete`: skipping would leave nothing to load.",
        "Leave option 2 out when the gate is asked again after option 2's own rejection (item 7).",
        "Number the options that remain from 1, in the order above, and keep the question's "
        "wording (INV-056).",
        "**When only option 1 remains**, there is one sensible answer, so ask nothing:",
        "say in one line",
        "then continue with item 4, with no 👉.",
    ), "the gate's \"Which options are offered\"")
    if offered is not None and re.search(r"👉\s*\*\*", offered):
        problems.append("the one-option case asks a 👉 question")
    if "options that \"Which options are offered\", below, leaves in" not in flat(section):
        problems.append("item 3's lead does not defer to \"Which options are offered\"")

    opt2 = between(section, "6. **On option 2,", "\n7. ")
    problems += missing(opt2, (
        "**On option 2, run `mapping_workflow` once more for this source, in full.**",
        "`action='start'` as step 8 does",
        "submit a new step-3 payload",
        "If it passes, continue step 11 as normal.",
    ), "option 2's handler")
    again = between(section, "7. **If option 2's run is rejected", "\n8. ")
    problems += missing(again, (
        "**If option 2's run is rejected without an actionable reason too**",
        "append the rejection text to `validation_rejections` (item 2)",
        "ask item 3's question again **without option 2**",
        "this is a new state, not an INV-006 repeat (INV-284)",
    ), "option 2's second-rejection handler")
    opt3 = between(section, "8. **On option 3,", "\n\n")
    problems += missing(opt3, (
        "**On option 3, skip the source.**",
        "Set its `mapping_status` to `skipped` and set `updated_at` in `config/data_sources.yaml`",
        "keep its `config/mapping_state_[datasource].json`",
        POINTER,
        "continue at step 19 with the next source",
    ), "option 3's handler")
    problems += restatements(section, "the gate")
    for handler in ("6. **On option 2,", "8. **On option 3,"):
        if handler in section and not q < section.index(handler):
            problems.append("%r sits before the question" % handler)
    return problems


# --- The consumers -----------------------------------------------------------------------------

def phase2_consumer_problems(phase2):
    problems = []
    fast = between(phase2, "## Skip fast-pathed sources", "## Mapping verbosity check")
    problems += missing(fast, ("A source whose `mapping_status` is `skipped` is passed over the "
                               "same way, and its mapping is not restarted", POINTER),
                        "\"Skip fast-pathed sources\"")
    resume = between(phase2, "## Mapping state checkpointing", "## File placement")
    problems += missing(resume, ("A `skipped` source's checkpoint is kept and is not resumed",
                                 POINTER), "\"Mapping state checkpointing\"")

    s16 = between(phase2, "### 16. Review", "### 17. Iterate")
    problems += missing(s16, (
        "a source other than this one whose `mapping_status` is neither `complete` nor `skipped`",
        "a `skipped` source is never mapped next",
        POINTER,
        "so neither counts and neither is offered as `{next}`",
    ), "step 16")
    if s16 is not None and "whose `mapping_status` is not `complete`" in flat(s16):
        problems.append("step 16 still counts a skipped source as unmapped")

    s19 = between(phase2, "### 19. Repeat", "### 20. Module completion")
    problems += missing(s19, (
        "**A `skipped` source** (" + LINK + ")",
        "the mapping-spec gate and the per-source completion checkpoint above do not apply to it",
        "Expect no `docs/mapping/{source_name}_mapper.md` for it, and keep its checkpoint.",
        "The next source is the next unmapped one, as step 16 defines it",
    ), "step 19")

    s20 = between(phase2, "### 20. Module completion", "**Checkpoint:** write step 20.")
    problems += missing(s20, (
        "Once every source's `mapping_status` is `complete` or `skipped` (" + LINK
        + "), **complete the module**",
        "**The recap names each `skipped` source.**",
        "In the Module 5 recap section's **Actions Taken**, name each source whose "
        "`mapping_status` is `skipped` and why it was skipped",
    ), "step 20")
    if s20 is not None and "Once all sources are mapped" in s20:
        problems.append("step 20 still waits for every source to be mapped")
    if s20 is not None and "**The recap names" in s20 and "👉" in s20:
        if not s20.index("**The recap names") < s20.index("👉"):
            problems.append("step 20's recap rule comes after the turn's 👉")
    for where, sec in (("\"Skip fast-pathed sources\"", fast), ("checkpointing", resume),
                       ("step 16", s16), ("step 19", s19), ("step 20", s20)):
        problems += restatements(sec, where)
    return problems


def module5_skill_problems(module5):
    """Module 5's own SKILL.md: its error-handling summary and its "Resuming" section."""
    problems = []
    errors = between(module5, "step-3 validation rejects the payload with no actionable reason",
                     "## Phases")
    problems += missing(errors, ("offer the pinned question with the options Phase 2 step 11 "
                                 "leaves in",), "Module 5's error handling")
    if errors is not None and "three-option question" in flat(errors):
        problems.append("Module 5's error handling still promises all three options")
    resume = between(module5, "## Resuming", "**A progress file that recorded Module 5")
    problems += missing(resume, ("A `skipped` source's checkpoint is not resumed", POINTER),
                        "Module 5's \"Resuming\"")
    problems += restatements(errors, "Module 5's error handling")
    problems += restatements(resume, "Module 5's \"Resuming\"")
    return problems


def module6_problems(phase_a, phase_c):
    problems = []
    a2 = between(phase_a, "## 2. Identify the input data", "## 3.")
    problems += missing(a2, ("A source whose `mapping_status` is `skipped` is not loaded: leave "
                             "it out here and in every later step of this module", POINTER),
                        "Module 6 Phase A step 2")
    gate = between(phase_c, "**Conditional gate.**", "## 12.")
    problems += missing(gate, ("count sources with `mapping_status: complete`",
                               "A source whose `mapping_status` is `skipped` is not loaded: it "
                               "is not counted here", "lists it as skipped and not loaded",
                               POINTER), "Module 6 Phase C's conditional gate")
    problems += restatements(a2, "Phase A step 2") + restatements(gate, "Phase C's gate")
    return problems


def graduation_problems(graduation):
    problems = []
    sources = between(graduation, "- **Sources:** every source", "- **Why `load_subset:` goes:**")
    problems += missing(sources, ("Omit a source whose `mapping_status` is `skipped` too",
                                  "Step 4's README names it", POINTER),
                        "graduation's projection")
    readme = between(graduation, "## Step 4: Production README",
                     "- **`production/MIGRATION_CHECKLIST.md`:**")
    problems += missing(readme, (
        "**Configuration names each source that is not mapped.**",
        "For each source whose bootcamp registry entry has `mapping_status: skipped`",
        POINTER,
        "say that it is not mapped",
        "No such source → omit that sentence.",
    ), "graduation's README")
    problems += restatements(sources, "the projection") + restatements(readme, "the README")
    return problems


def read(path):
    return path.read_text(encoding="utf-8")


def skill_corpus():
    return {str(p.relative_to(SKILLS)): read(p) for p in sorted(SKILLS.rglob("*.md"))}


class TheMeaningIsStatedOnce(unittest.TestCase):
    def setUp(self):
        self.module4 = read(MODULE4)
        self.corpus = skill_corpus()

    def test_module_4_defines_skipped(self):
        self.assertEqual([], definition_problems(self.module4))

    def test_no_other_skill_file_restates_it(self):
        self.assertEqual([], single_statement_problems(self.corpus))

    def test_every_pointer_resolves(self):
        self.assertEqual([], pointer_problems(self.corpus))

    def test_negative_controls(self):
        m4 = self.module4
        mutants = {
            "anchor dropped": m4.replace(ANCHOR, "", 1),
            "skipped not listed": m4.replace("`complete` |\n> `skipped`)", "`complete`)", 1),
            "kept checkpoint dropped": m4.replace("is kept, and never resumed.", "is deleted.", 1),
            "not-loaded bullet dropped": m4.replace("Nothing loads it, and", "Module 6 decides, and",
                                                    1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(m4, mutant, "the mutation no longer applies")
                self.assertNotEqual([], definition_problems(mutant))

    def test_a_restatement_is_reported(self):
        corpus = dict(self.corpus)
        key = "graduation/SKILL.md"
        corpus[key] = corpus[key] + "\n\nIt is not a mapped source.\n"
        self.assertNotEqual([], single_statement_problems(corpus))

    def test_a_pointer_to_the_wrong_file_is_reported(self):
        corpus = dict(self.corpus)
        key = "graduation/SKILL.md"
        corpus[key] = corpus[key].replace("(../module-04-data-collection/SKILL.md#" + ANCHOR_ID,
                                          "(../module-05-data-quality-mapping/SKILL.md#"
                                          + ANCHOR_ID, 1)
        self.assertNotEqual(self.corpus[key], corpus[key], "the mutation no longer applies")
        self.assertNotEqual([], pointer_problems(corpus))


class TheGateHandlesEveryOption(unittest.TestCase):
    def setUp(self):
        self.phase2 = read(PHASE2)

    def test_the_gate(self):
        self.assertEqual([], gate_problems(self.phase2))

    def test_negative_controls(self):
        p2 = self.phase2
        mutants = {
            "question reworded": p2.replace("rejected this source twice", "rejected this source", 1),
            "option 3 always offered": p2.replace("Leave option 3 out when no other source", "Offer "
                                                  "option 3 even when no other source", 1),
            "option 2 kept on the re-ask": p2.replace("again **without option 2**",
                                                      "again with every option", 1),
            "one-option case asks": p2.replace(
                "Senzing Entity Specification, then continue with item 4, with no 👉.",
                "Senzing Entity Specification.\n\n   👉 **Shall I write the mapper?**", 1),
            "option 2 handler dropped": p2.replace("6. **On option 2, run", "6. **Retry, run", 1),
            "skip not written": p2.replace("Set its `mapping_status` to `skipped`",
                                           "Set its `mapping_status` to `pending`", 1),
            "skip resumes elsewhere": p2.replace("continue at step 19 with the next source",
                                                 "continue at step 16", 1),
            "checkpoint deleted on skip": p2.replace(
                "and keep its `config/mapping_state_[datasource].json`",
                "and delete its `config/mapping_state_[datasource].json`", 1),
            "definition restated at the gate": p2.replace(
                "Steps\n   12–18a do not run for it.",
                "It is not a mapped source. Steps\n   12–18a do not run for it.", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(p2, mutant, "the mutation no longer applies")
                self.assertNotEqual([], gate_problems(mutant))

    def test_a_rewrap_still_passes(self):
        """INV-346: the phrase checks read whitespace-collapsed text."""
        mutant = self.phase2.replace("Leave option 3 out when no other source in\n",
                                     "Leave option 3 out when no other\nsource in ", 1)
        self.assertNotEqual(self.phase2, mutant, "the re-wrap no longer applies")
        self.assertEqual([], gate_problems(mutant))


class EveryConsumerPointsToTheDefinition(unittest.TestCase):
    def setUp(self):
        self.module5 = read(MODULE5)
        self.phase2 = read(PHASE2)
        self.phase_a = read(PHASE_A)
        self.phase_c = read(PHASE_C)
        self.graduation = read(GRADUATION)

    def test_module_5(self):
        self.assertEqual([], phase2_consumer_problems(self.phase2))

    def test_module_5_skill(self):
        self.assertEqual([], module5_skill_problems(self.module5))

    def test_module_5_skill_negative_controls(self):
        m5 = self.module5
        mutants = {
            "three options promised": m5.replace(
                "the pinned question with the options Phase 2 step 11 leaves in",
                "the pinned three-option question", 1),
            "skipped checkpoint resumed": m5.replace(
                "A `skipped` source's checkpoint is not resumed", "Every checkpoint is resumed",
                1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(m5, mutant, "the mutation no longer applies")
                self.assertNotEqual([], module5_skill_problems(mutant))

    def test_module_6(self):
        self.assertEqual([], module6_problems(self.phase_a, self.phase_c))

    def test_graduation(self):
        self.assertEqual([], graduation_problems(self.graduation))

    def test_module_5_negative_controls(self):
        p2 = self.phase2
        mutants = {
            "step 16 back to not complete": p2.replace(
                "neither `complete` nor `skipped`", "not `complete`", 1),
            "step 16 pointer dropped": p2.replace(
                "never mapped next\n(" + LINK + ")", "never mapped next\n(see Module 4)", 1),
            "step 19 gate still applies": p2.replace(
                "do not apply to it, because it has no mapper", "apply to it as well", 1),
            "step 20 waits for every source": p2.replace(
                "Once every source's `mapping_status` is `complete` or `skipped`",
                "Once all sources are mapped", 1),
            "recap rule dropped": p2.replace("**The recap names each `skipped` source.**",
                                             "**The recap.**", 1),
            "checkpoint resumed": p2.replace("is kept and is not resumed", "is resumed", 1),
            "step 19 restates the definition": p2.replace(
                "Expect no\n`docs/mapping/", "It is not a mapped source. Expect no\n`docs/mapping/",
                1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(p2, mutant, "the mutation no longer applies")
                self.assertNotEqual([], phase2_consumer_problems(mutant))

    def test_module_6_and_graduation_negative_controls(self):
        cases = {
            "Phase A loads it": (module6_problems, (
                self.phase_a.replace("`skipped` is not loaded: leave it out",
                                     "`skipped` is loaded from its raw file", 1), self.phase_c)),
            "Phase C counts it": (module6_problems, (
                self.phase_a, self.phase_c.replace("it is not counted here", "it is counted", 1))),
            "projection keeps it": (graduation_problems, (
                self.graduation.replace("`mapping_status` is `skipped` too: it has no mapper",
                                        "`mapping_status` is `pending` too: it has no mapper",
                                        1),)),
            "README silent": (graduation_problems, (
                self.graduation.replace("**Configuration names each source that is not mapped.**",
                                        "**Configuration.**", 1),)),
        }
        originals = {module6_problems: (self.phase_a, self.phase_c),
                     graduation_problems: (self.graduation,)}
        for name, (check, args) in cases.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(originals[check], args, "the mutation no longer applies")
                self.assertNotEqual([], check(*args))

    def test_a_rewrap_still_passes(self):
        """INV-346: a consumer's phrase moved across a line break still matches."""
        mutant = self.phase_a.replace("leave it out here and in every later\nstep",
                                      "leave it out here and in every\nlater step", 1)
        self.assertNotEqual(self.phase_a, mutant, "the re-wrap no longer applies")
        self.assertEqual([], module6_problems(mutant, self.phase_c))


if __name__ == "__main__":
    unittest.main()
