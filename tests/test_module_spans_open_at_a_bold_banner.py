"""A module whose banner the guide shows in bold still gets judged (#923).

`walk.banner_seen` matched a banner line as it stands or with one tripled-glyph frame
stripped. In the 2026-11-11 15:15 and 2026-11-12 08:39 walks the guide wrote each banner
as a bold line with no frame, "**MODULE: DATA PROCESSING**", so `transcript_lint.module_spans`
opened no span for Data processing or for Query, Visualize and Discover. No check graded
either module, and the walk's report said nothing about them (#855's
`auto-test-walk-2026-11-12` entry). `banner_seen` now strips one `**…**` wrapping the whole
line or the whole framed text first. `module_spans`, `walk.py`'s `--stop-at-banner` and
`dry-run`'s slicer (`module_banners`) all share it.

The fixture is shaped on the 08:39 walk: its resume, banner and transition lines, copied
from the transcript, sit at their turn numbers, and every other turn is filler. The
banners are read from the skills through `module_banners`, so a banner change cannot leave
the fixture stale. `test_dry_run_simulated_phase3.py` holds the line-level cases.

What this does not establish: which banner form a live guide writes; only `auto-test`
observes that.

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT_DIR = REPO_ROOT / ".claude" / "skills" / "auto-test"
WALK_PY = LINT_DIR / "walk.py"
sys.path.insert(0, str(LINT_DIR))

import transcript_lint  # noqa: E402
import walk  # noqa: E402

POINTER = "\U0001f449"


def bold_banner(token):
    entry = next(m for m in transcript_lint.module_table() if m["token"] == token)
    return "**%s**" % entry["banner"]


#: The 2026-11-12 08:39 walk (report `20261112-083943-terse`), at its turn numbers.
SHOWN = {
    4: ("Welcome back. Where you left off: Data Quality, Mapping, and Transformation, "
        "step 11.\n\n%s **Would you like to resume Data Quality, Mapping, and "
        "Transformation at step 11?**" % POINTER),
    35: "%s **Are you ready to move on to the next module: Data Processing?**" % POINTER,
    37: bold_banner("data_processing") + "\n\n- ⬜ Graduation",
    96: ("%s **Are you ready to move on to the next module: Query, Visualize and "
         "Discover?**" % POINTER),
    99: (bold_banner("query_visualize_discover") + "\n\n- ⬜ Graduation\n\n"
         "%s **What do you want to find out about your data?**" % POINTER),
    138: ("Next: Bootcamp graduation — generates your production project and the recap.\n\n"
          "%s **Would you like to graduate now and generate your production project and "
          "recap?**" % POINTER),
    140: (bold_banner("graduation") + "\n\n- 🔄 **Bootcamp Graduation** (current, final)"),
}
WALK = [SHOWN.get(turn, "Working on it.") for turn in range(1, 141)]

EXPECTED = [("data_quality_mapping", 4, 35), ("data_processing", 37, 96),
            ("query_visualize_discover", 99, 138), ("graduation", 140, None)]


def spans(turns):
    return [(s["token"], s["start"], s["end"]) for s in transcript_lint.module_spans(turns)]


class ABoldBannerOpensASpan(unittest.TestCase):

    def test_the_walks_modules_get_their_spans(self):
        self.assertEqual(EXPECTED, spans(WALK))

    def test_a_module_behind_a_bold_banner_is_graded(self):
        # Data processing shows no directing question in the fixture, so it must be reported.
        found = transcript_lint.check_directing_steps(WALK)
        self.assertTrue(any(f["code"] == "INV-354-directing-step-missing" and f["turn"] == 96
                            for f in found),
                        "Data processing ended without its directing question and was not "
                        "graded: %s" % found)

    def test_a_bold_banner_after_a_resume_for_the_same_module_opens_no_second_span(self):
        turns = [SHOWN[4], bold_banner("data_quality_mapping") + "\n\nStep 11.", SHOWN[35]]
        self.assertEqual([("data_quality_mapping", 1, 3)], spans(turns))

    def test_the_walk_stops_at_a_bold_banner(self):
        # `walk.py --stop-at-banner` reads the same matcher.
        self.assertTrue(walk.banner_seen("MODULE: DATA PROCESSING", SHOWN[37]))


class NegativeControl(unittest.TestCase):

    def test_without_the_bold_case_the_later_modules_have_no_span(self):
        source = WALK_PY.read_text(encoding="utf-8")
        cut = re.sub(r"\n    bold = BOLD\.match\(text\)\n    return [^\n]+\n",
                     "\n    return text\n", source)
        self.assertNotEqual(source, cut, "the bold case moved; update the control")
        namespace = {"__file__": str(WALK_PY), "__name__": "walk_mutant"}
        exec(compile(cut, str(WALK_PY), "exec"), namespace)  # noqa: S102 - the repo's own file
        original = transcript_lint.banner_seen
        transcript_lint.banner_seen = namespace["banner_seen"]
        try:
            mutant = spans(WALK)
        finally:
            transcript_lint.banner_seen = original
        self.assertEqual([("data_quality_mapping", 4, 35)], mutant)


if __name__ == "__main__":
    unittest.main()
