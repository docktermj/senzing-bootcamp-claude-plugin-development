"""Module 5 asks the loading question only once every source is mapped.

Phase 2 runs steps 9-19 once per data source. Step 16's quality gate used to have one set of
pinned questions, all about loading: "Quality looks strong. Ready to proceed to loading (Data
processing)?", option 1 "Yes, proceed to loading". On the 2026-10-01 walk (three person
sources, server 1.37.16) that question came after the FIRST source, so a literal "1" asked to
load while two sources were still unmapped, which step 18a ("continue to the next unmapped
source") and step 19 then contradicted. Pinned wording cannot be adapted to fit (INV-056), and
the `mapping_workflow` approve message in the same turn said "repeat mapping_workflow for each
remaining data source before proceeding".

So step 16 now has two sets of pinned questions (#333):

- **while an unmapped source remains** (`config/data_sources.yaml` has another source whose
  `mapping_status` is not `complete`), three per-source questions about mapping `{next}`;
- **when none remains**, the original three loading questions, unchanged.

Each option has a handling step (INV-284): moving on goes through 17-18a to step 19, iterating
goes to step 17.

The same issue corrected step 18a. `mapping_workflow` step 5 (`detect_environment`) takes
`decision: enum ["skip", "test_load"]` (server 1.37.16, 2026-10-01). Step 18a described "a
four-option menu" (skip / test_load / load+resolve / done), most likely the four next-step
categories in the step-4 approve message, and gave no default at the last source. It now names
the two values, and a step-16 answer that proceeds to loading settles the last source's decision
as `skip`, with no question asked.

The checks are pure functions over the text, so the negative controls below run the same
functions over mutated copies.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping")
PHASE2 = MODULE / "phase2-data-mapping.md"
PHASE3 = MODULE / "phase3-test-load.md"

#: The per-source questions, verbatim from the issue (INV-056): the 👉 line and its options.
PER_SOURCE = (
    ("👉 **Quality looks strong for {source}. Ready to map the next source, {next}? "
     "Reply with a number:**",
     ("1. Yes, map {next}.", "2. No, I'd like to iterate on {source} first.")),
    ("👉 **Quality for {source} is acceptable. What would you like to do? Reply with a number:**",
     ("1. Move on to the next source, {next}.",
      "2. Iterate to improve [specific weak areas] first.")),
    ("👉 **Quality for {source} needs improvement before loading will produce meaningful "
     "results. I'd recommend going back to address [specific issues]. What would you like to "
     "do? Reply with a number:**",
     ("1. Iterate to improve the data.",
      "2. Move on to {next} anyway, knowing results may be limited.")),
)

#: The loading questions, unchanged by #333, and now asked only when no unmapped source remains.
LOADING = (
    "👉 **Quality looks strong. Ready to proceed to loading (Data processing)? Reply with a number:**",
    "👉 **Quality is acceptable. What would you like to do? Reply with a number:**",
    "👉 **Quality needs improvement before loading will produce meaningful results. I'd "
    "recommend going back to address [specific issues]. What would you like to do? Reply with "
    "a number:**",
)
#: Options that propose loading. None may appear before the no-unmapped-source condition.
LOADING_OPTIONS = ("Yes, proceed to loading.", "Proceed to loading now.",
                   "Proceed anyway, knowing results may be limited.")

WHILE_REMAINING = "**While one or more unmapped sources remain**"
NONE_REMAINING = "**When no unmapped source remains**"


def section(body, start, end):
    a = body.index(start)
    return body[a:body.index(end, a)]


def step16(body):
    return section(body, "### 16. Review", "### 17. Iterate")


def step18a(body):
    return section(body, "### 18a.", "### 19.")


def step16_problems(s16):
    """Everything wrong with step 16's gate, as a list of strings."""
    problems = []
    flat = re.sub(r"\s+", " ", s16)
    for marker in ("config/data_sources.yaml", "mapping_status", "complete"):
        if marker not in flat:
            problems.append(f"the unmapped-source condition does not name {marker!r}")
    if WHILE_REMAINING not in s16:
        problems.append("no per-source block (\"While one or more unmapped sources remain\")")
        return problems
    if NONE_REMAINING not in s16:
        problems.append("no last-source block (\"When no unmapped source remains\")")
        return problems
    w, n = s16.index(WHILE_REMAINING), s16.index(NONE_REMAINING)
    if not w < n:
        problems.append("the last-source block comes before the per-source block")
        return problems
    per_source, last = s16[w:n], s16[n:]

    for question, options in PER_SOURCE:
        if per_source.count(question) != 1:
            problems.append(f"per-source question not pinned verbatim once: {question[:60]}...")
            continue
        after = per_source[per_source.index(question):]
        for opt in options:
            if opt not in after.split("👉", 2)[1]:
                problems.append(f"per-source option missing after its question: {opt}")
    for question in LOADING:
        if question in s16[:n]:
            problems.append(f"a loading question is reachable before the last-source "
                            f"condition: {question[:60]}...")
        if last.count(question) != 1:
            problems.append(f"loading question not kept verbatim once after the condition: "
                            f"{question[:60]}...")
    for opt in LOADING_OPTIONS:
        if opt in s16[:n]:
            problems.append(f"a loading option is offered while sources remain: {opt}")
        if opt not in last:
            problems.append(f"loading option missing from the last-source block: {opt}")

    # INV-284: every option has a handling step, stated in each block.
    handling_per_source = re.sub(r"\s+", " ", per_source)
    if "step 19" not in handling_per_source or "step 17" not in handling_per_source:
        problems.append("the per-source block does not route its options (step 19 to move "
                        "on, step 17 to iterate)")
    if "INV-284" not in handling_per_source:
        problems.append("the per-source handling does not cite INV-284")
    handling_last = re.sub(r"\s+", " ", last)
    if "skip" not in handling_last or "step 17" not in handling_last:
        problems.append("the last-source block does not route a proceed answer to 18a's skip "
                        "and an iterate answer to step 17")
    return problems


def step18a_problems(s18a):
    problems = []
    flat = re.sub(r"\s+", " ", s18a)
    if "load+resolve" in flat:
        problems.append("18a still names load+resolve, which step 5 does not accept")
    if re.search(r"(?i)four-option|four options are", flat):
        problems.append("18a still describes a four-option menu")
    if 'enum ["skip", "test_load"]' not in flat:
        problems.append("18a does not state the step-5 enum it relies on")
    if not re.search(r"server\s+1\.\d+\.\d+,\s*\d{4}-\d{2}-\d{2}", flat):
        problems.append("18a's enum carries no server version and date")
    if "The two options are:" not in flat:
        problems.append("18a does not list the two options")
    if not re.search(r"(?i)Recommended when one or more unmapped sources remain", flat):
        problems.append("18a lost the multi-source 'recommend skip' guidance")
    m = re.search(r"\*\*Last source \(no unmapped source remains\):\*\*(.*?)(?=\n\n)", s18a, re.S)
    if not m:
        problems.append("18a states no last-source rule")
    else:
        rule = re.sub(r"\s+", " ", m.group(1))
        for needed in ("≥80% option 1", "70-79% option 1", "<70% option 2", "**skip**",
                       "ask no 👉 question"):
            if needed not in rule:
                problems.append(f"18a's last-source rule does not say {needed!r}")
    if "explicitly asks for the sandbox test load" not in flat:
        problems.append("18a does not keep test_load for an explicit request")
    return problems


def phase3_entry_problems(text):
    note = section(text, "> **Entry from the Step 5", "**Before starting Phase 3:**")
    problems = []
    if "load+resolve" in note:
        problems.append("Phase 3's entry note still names load+resolve")
    if "**test_load**" not in note:
        problems.append("Phase 3's entry note no longer names test_load")
    return problems


class Step16AsksAboutLoadingOnlyAfterTheLastSource(unittest.TestCase):
    def setUp(self):
        self.s16 = step16(PHASE2.read_text(encoding="utf-8"))

    def test_the_gate_is_split_on_the_unmapped_source_condition(self):
        self.assertEqual([], step16_problems(self.s16))

    def test_negative_controls(self):
        """Each mutation reintroduces a defect #333 fixed; each must be reported."""
        s = self.s16
        before = s[:s.index(NONE_REMAINING)]
        mutants = {
            # the original single gate: per-source block removed entirely
            "per-source block removed": s.replace(before, before[:before.index(WHILE_REMAINING)]),
            # the loading question asked per source again
            "loading question asked per source": s.replace(
                PER_SOURCE[0][0], LOADING[0], 1),
            # a per-source question reworded (INV-056)
            "per-source question reworded": s.replace(
                "Ready to map the next source, {next}?", "Shall we map {next}?", 1),
            # a loading option offered while sources remain
            "loading option per source": s.replace(
                "1. Yes, map {next}.", "1. Yes, proceed to loading.", 1),
            # handling dropped
            "per-source handling dropped": s.replace("step 19, which starts", "the next step,", 1)
                                             .replace("Every iterate option goes to step 17.",
                                                      "", 1),
            # the condition no longer names the registry
            "condition unnamed": s.replace("`config/data_sources.yaml`", "the registry"),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(mutant, s, "the mutation did not apply")
                self.assertNotEqual([], step16_problems(mutant))


class Step18aNamesTheTwoValuesStep5Accepts(unittest.TestCase):
    def setUp(self):
        self.s18a = step18a(PHASE2.read_text(encoding="utf-8"))

    def test_18a_is_correct(self):
        self.assertEqual([], step18a_problems(self.s18a))

    def test_phase3_entry_names_only_test_load(self):
        self.assertEqual([], phase3_entry_problems(PHASE3.read_text(encoding="utf-8")))

    def test_negative_controls(self):
        s = self.s18a
        mutants = {
            "load+resolve restored": s.replace(
                "- **test_load:**", "- **load+resolve:** sandbox load and resolve.\n- **test_load:**", 1),
            "four-option menu restored": s.replace("The two options are:", "The four options are:", 1),
            "last-source rule dropped": s.replace("**Last source (no unmapped source remains):**",
                                                  "**Last source:**", 1),
            "last-source rule asks a question": s.replace("ask no 👉 question here",
                                                          "ask which they prefer", 1),
            "enum unstated": s.replace('enum ["skip", "test_load"]', "two values", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(mutant, s, "the mutation did not apply")
                self.assertNotEqual([], step18a_problems(mutant))
        note = PHASE3.read_text(encoding="utf-8").replace(
            "chooses **test_load** at that menu", "chooses **test_load** or **load+resolve** at that menu", 1)
        self.assertNotEqual([], phase3_entry_problems(note))


if __name__ == "__main__":
    unittest.main()
