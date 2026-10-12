"""Module 5 step 18 validates the load-ready file it writes, and the success indicator matches the gate.

Step 18 writes `data/senzing-ready/[name].jsonl`, the file Data processing loads. Before #521 nothing
counted or parsed that file: step 15 analyzes a separate quality run, which for a source over 1000
records is not the full output, so a transformation program that dropped or broke records at scale
reached Data processing unchecked (INV-043: the code transforms the raw data to Senzing-ready data).
And `SKILL.md`'s success indicator said "quality >70%", while step 16's gate lets the Bootcamper
proceed below 70%.

These tests pin the fix:

- step 18 runs the MCP-delivered `sz_json_analyzer.py` (step 14's `analyze_record` route, no new
  bundled script) on `data/senzing-ready/[name].jsonl`;
- it compares the report's record count with the source's count minus the records the
  transformation lineage records as filtered on purpose;
- it reads both checks from the report, not the exit code: on server 1.37.27 (2026-10-12) a
  malformed line is reported as `JSON error line N` and `N JSON parse error(s)`, dropped from the
  count, and the run still exits 0;
- a clean result is one line and the step continues; a parse error or an unexplained count
  difference is a transformation defect that goes to step 17 with no 👉, as step 15's `rework_*`
  verdict does;
- when the analyzer was skipped for the session (the **No** path of step 11's Python check,
  INV-347), step 18's check is skipped with it, asks nothing, and is named in the module's closing
  summary as a check that did not run (INV-163) — grafted from #521's losing strategy B;
- `SKILL.md`'s success indicator carries no 70% bar and says the quality score is reported at
  step 16.

Each check is a pure function of the file text, so the negative controls run the same function on
a mutated copy. Phrase checks read whitespace-collapsed text, so they hold through a re-wrap
(INV-346).

These assert what the guidance *states*; they do **not** establish that a live run counts the file
or stops on a parse error, which only `dry-run` phase 3 can observe. Stdlib only; nothing under
``plugins/`` is imported (INV-108).

Source issue: #521.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE5 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-05-data-quality-mapping"
PHASE2 = MODULE5 / "phase2-data-mapping.md"
SKILL = MODULE5 / "SKILL.md"

STEP18_HEAD = "### 18. Save and document"
CHECK_HEAD = "**Validate the full output (INV-043).**"

#: What step 18's check must state, each matched on whitespace-collapsed text.
REQUIRED = {
    "the analyzer runs on the load-ready file":
        "Run the MCP-delivered `sz_json_analyzer.py` that step 14 uses (same `analyze_record` "
        "route, same `data/mapping/` workspace) on `data/senzing-ready/[name].jsonl`",
    "the expected count is the source's minus the lineage's filters":
        "with the source's record count minus the records the transformation lineage above "
        "records as filtered on purpose",
    "the report is read, not the exit code": "Read both checks from the report, not from the "
                                             "exit code",
    "a parse error is reported and still exits 0, with a dated server":
        "and still exits 0 (measured on server 1.37.27, 2026-10-12)",
    "clean and matching is one line": "**Analyzer clean and counts match:** say so in one line "
                                      "and continue with this step.",
    "a failure is a program defect, not a preference": "this is a defect in the transformation "
                                                       "program, not a preference",
    "it names which check failed": "Say which check failed (the analyzer's parse errors, or the "
                                   "expected and actual counts)",
    "it goes to step 17 with no 👉, as step 15's rework does":
        "go to step 17 to fix the program, with no 👉, as step 15's `rework_*` verdict does",
    "it is skipped with an analyzer skipped for the session":
        "**The analyzer was skipped for the session** (the **No** path of step 11's Python check, "
        "above, INV-347): this check is skipped with it.",
    "a skipped check asks nothing": "Do not run it and ask nothing (INV-006)",
    "the closing summary names a skipped check": "the module's closing summary names it, with the "
                                                 "analyzer, as a check that did not run (INV-163)",
}

#: Step 11's Python check, whose **No** path step 18's skipped case points to.
PYTHON_NO_PATH = "**No:** tell the Bootcamper the analyzer is being skipped"

INDICATOR = re.compile(r"\*\*Success indicator:\*\*(.*?)(?:\n\n|$)", re.S)


def flat(text):
    return re.sub(r"\s+", " ", text)


def sub(text, phrase, replacement):
    """Replace the first ``phrase`` in ``text`` however it is wrapped (a mutation helper)."""
    pattern = r"\s+".join(re.escape(word) for word in phrase.split(" "))
    return re.sub(pattern, lambda _: replacement, text, count=1)


def step18(text):
    start = text.find(STEP18_HEAD)
    if start < 0:
        return ""
    end = text.find("\n### ", start + len(STEP18_HEAD))
    return text[start:end if end != -1 else len(text)]


def step18_problems(phase2):
    s18 = step18(phase2)
    if not s18:
        return ["step 18 moved"]
    if CHECK_HEAD not in s18:
        return ["step 18 does not validate its full output"]
    problems = []
    check = flat(s18[s18.index(CHECK_HEAD):])
    for what, needle in REQUIRED.items():
        if flat(needle) not in check:
            problems.append("step 18's check does not state that %s" % what)
    if "👉" in check.replace("with no 👉", ""):
        problems.append("step 18's check asks a 👉 question")
    lineage = flat(s18).find("**Transformation lineage:**")
    if lineage < 0 or not lineage < flat(s18).find(CHECK_HEAD):
        problems.append("step 18's check runs before the lineage it reads is written")
    if s18.index(CHECK_HEAD) > s18.index("**Checkpoint:** write step 18."):
        problems.append("step 18's check comes after its checkpoint")
    no_path = phase2.find(PYTHON_NO_PATH)
    if no_path < 0 or not no_path < phase2.find(STEP18_HEAD):
        problems.append("step 18's skipped case points to a Python-check No path that is not "
                        "above it")
    return problems


def indicator_problems(skill):
    match = INDICATOR.search(skill)
    if match is None:
        return ["SKILL.md has no success indicator"]
    text = flat(match.group(1))
    problems = []
    if re.search(r"70\s*%|>\s*70", text):
        problems.append("the success indicator still sets a 70% bar the step-16 gate does not")
    if "quality score reported at step 16" not in text:
        problems.append("the success indicator does not say the quality score is reported at "
                        "step 16")
    if "output validated" not in text:
        problems.append("the success indicator no longer requires the output to be validated")
    return problems


class Step18ValidatesTheFullOutput(unittest.TestCase):
    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")

    def test_the_check(self):
        self.assertEqual([], step18_problems(self.text))

    def test_it_uses_no_bundled_script(self):
        """The analyzer is MCP-delivered (INV-080); the plugin ships no copy of it."""
        plugin = REPO_ROOT / "plugins" / "senzing-bootcamp"
        self.assertEqual([], [p.name for p in plugin.rglob("sz_json_analyzer*.py")])

    def test_a_rewrap_still_passes(self):
        mutant = sub(self.text, "Read both checks from the report, not from the exit code",
                     "Read both checks\nfrom the report, not from\nthe exit code")
        mutant = sub(mutant, "the module's closing summary names it, with the analyzer, as a check",
                     "the module's\n  closing summary names it, with the\n  analyzer, as a check")
        self.assertTrue(self.text != mutant, "the re-wrap no longer applies")
        self.assertEqual([], step18_problems(mutant))

    def test_negative_controls(self):
        text = self.text
        mutants = {
            "check dropped": text.replace(CHECK_HEAD, "**Notes.**", 1),
            "exit code trusted": sub(text, "Read both checks from the report, not",
                                     "Read both checks from the exit code, not"),
            "lineage filters ignored": sub(text, "minus the records the", "plus the records the"),
            "a 👉 at the failure": sub(text, "with no 👉, as step 15's",
                                       "after asking 👉 **Shall I fix it?**, as step 15's"),
            "failure treated as a preference": sub(text, "transformation program, not a preference",
                                                   "transformation program, or a preference"),
            "server version dropped": sub(text, "(measured on server 1.37.27, 2026-10-12)",
                                          "(measured)"),
            "skipped-analyzer case dropped": sub(
                text, "**The analyzer was skipped for the session**", "**Otherwise**"),
            "check run although the analyzer was skipped": sub(
                text, "this check is skipped with it.", "run this check anyway."),
            "skipped check not named at closing": sub(
                text, "the module's closing summary names it, with the analyzer, as a check that "
                      "did not run (INV-163)", "nothing more is said"),
            "Python-check No path gone": text.replace(PYTHON_NO_PATH, "**No:** carry on", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertTrue(text != mutant, "the mutation no longer applies")
                self.assertNotEqual([], step18_problems(mutant))


class TheSuccessIndicatorMatchesTheGate(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_the_indicator(self):
        self.assertEqual([], indicator_problems(self.text))

    def test_negative_controls(self):
        text = self.text
        mutants = {
            "70% bar restored": text.replace("output validated; quality score reported at step 16.",
                                             "output validated with quality >70%.", 1),
            "step 16 dropped": text.replace("quality score reported at step 16",
                                            "quality score reported", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertTrue(text != mutant, "the mutation no longer applies")
                self.assertNotEqual([], indicator_problems(mutant))


if __name__ == "__main__":
    unittest.main()
