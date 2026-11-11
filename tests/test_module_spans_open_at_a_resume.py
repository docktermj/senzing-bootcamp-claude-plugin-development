"""A walk that resumes partway into a module gets that module judged (#913).

`transcript_lint.module_spans` opened a span only on a turn showing a module's banner. #855's
pinned walk (`--seed mid`) resumes at Data Quality, Mapping, and Transformation step 11, which
shows the resume line ("Where you left off: {module name}, step {N}.", `bootcamp-onboarding`
SKILL.md step 2) and no banner, so the 2026-11-10 walk finished that module and no check
graded it. The resume line now opens a span too, for the module whose table name it carries
(`module_banners.modules()`, the one table `module_spans` reads; INV-300).

The fixture is shaped on that walk's opening turns, shortened. The banners are read from the
skills through `module_banners`, so a banner change cannot leave the fixture stale.

What this does not establish: that a live walk resumes with this line; only `auto-test`
observes that.

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT_DIR = REPO_ROOT / ".claude" / "skills" / "auto-test"
LINT = LINT_DIR / "transcript_lint.py"
sys.path.insert(0, str(LINT_DIR))

import transcript_lint  # noqa: E402

POINTER = "\U0001f449"


def banner(token):
    entry = next(m for m in transcript_lint.module_table() if m["token"] == token)
    return entry["banner"]


def resume(name, step=11):
    return ("Your bootcamp is in progress, so I'll pick up where you left off.\n\n"
            "Where you left off: %s, step %d.\n\n"
            "%s **Shall we resume %s at step %d?**" % (name, step, POINTER, name, step))


TRANSITION_TO_6 = "%s **Are you ready to move on to the next module: Data processing?**" % POINTER
TRANSITION_TO_7 = ("%s **Are you ready to move on to the next module: Query, Visualize and "
                   "Discover?**" % POINTER)

#: The 2026-11-10 walk's shape: resume into Module 5, finish it, then Modules 6 and 7.
WALK = [
    resume("Data Quality, Mapping, and Transformation"),
    "Generating the CUSTOMERS mapper.\n\n%s **Shall I run the analyzer on it?**" % POINTER,
    "**Module complete**\n\n" + TRANSITION_TO_6,
    banner("data_processing") + "\n\nStep 1.",
    "Loading.\n\n" + TRANSITION_TO_7,
    banner("query_visualize_discover") + "\n\nStep 1.",
]


def spans(turns):
    return [(s["token"], s["start"], s["end"]) for s in transcript_lint.module_spans(turns)]


class AResumeOpensASpan(unittest.TestCase):

    def test_the_resumed_module_is_spanned_to_its_transition(self):
        self.assertEqual([("data_quality_mapping", 1, 3), ("data_processing", 4, 5),
                          ("query_visualize_discover", 6, None)], spans(WALK))

    def test_the_banner_spans_are_unchanged(self):
        self.assertEqual([("data_processing", 1, 2), ("query_visualize_discover", 3, None)],
                         spans(WALK[3:]))

    def test_a_banner_for_the_resumed_module_opens_no_second_span(self):
        turns = [resume("Data Quality, Mapping, and Transformation"),
                 banner("data_quality_mapping") + "\n\nStep 11.", "**Module complete**\n\n"
                 + TRANSITION_TO_6]
        self.assertEqual([("data_quality_mapping", 1, 3)], spans(turns))

    def test_a_name_not_in_the_table_opens_nothing(self):
        self.assertEqual([], spans([resume("Module 5"), "**Module complete**\n\n"
                                    + TRANSITION_TO_6]))

    def test_a_resumed_module_is_graded(self):
        found = transcript_lint.check_directing_steps(WALK)
        self.assertTrue(any(f["code"] == "INV-354-directing-step-missing" and f["turn"] == 3
                            for f in found),
                        "the resumed Module 5 ended without its directing question and was "
                        "not graded: %s" % found)


class NegativeControl(unittest.TestCase):

    def test_without_the_resume_case_module_5_has_no_span(self):
        source = LINT.read_text(encoding="utf-8")
        cut = re.sub(r"\n        if shown is None:\n            resumed = RESUME\.search\(text\)\n"
                     r"            shown = [^\n]+\n", "\n", source)
        self.assertNotEqual(source, cut, "the resume case moved; update the control")
        namespace = {"__file__": str(LINT), "__name__": "transcript_lint_mutant"}
        exec(compile(cut, str(LINT), "exec"), namespace)  # noqa: S102 - the repo's own file
        mutant = [(s["token"], s["start"]) for s in namespace["module_spans"](WALK)]
        self.assertNotIn(("data_quality_mapping", 1), mutant)

    def test_the_name_is_matched_through_the_one_table(self):
        source = LINT.read_text(encoding="utf-8")
        self.assertIn('by_name = {m["name"]: m for m in all_modules}', source)
        self.assertNotIn("Data Quality, Mapping, and Transformation", source.split(
            "def module_spans", 1)[1].split("\ndef ", 1)[0], "a second copy of a name")


if __name__ == "__main__":
    unittest.main()
