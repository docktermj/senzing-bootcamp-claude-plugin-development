"""The hard-rule detector sees a stop sign that is not first on its line.

`HARD_RULE` anchored `⛔` to the start of a line (optionally behind `>` or a single `-`), and
that anchor was the definition of "hard rule" for the whole reverse contract — `rules`,
`per-rule`, `since`, and `implement-spec` Step 5's pre-entry check all inherited it. Measured
2026-08-21 across shipped markdown: **191 lines** carried a `⛔` that was not first on its line,
and **none** was caught by the bolded-MUST alternatives either, because a rule like
`⛔ **Strip everything identifying.**` has no MUST inside its bold span.

Three shapes recurred and two are ordinary house style: a numbered-list item (`2. ⛔ **…**` —
the anchor admitted `-` but not `1.`), a rule appended to a list item's prose, and a rule
continuing a sentence. Ordered lists are how this repo writes procedures, which is exactly
where hard rules live.

⚠️ **Found by the tooling failing on its author's own rules.** Two `⛔` rules citing INV-122
were added to the capture blocks the same day; `since --ref HEAD` reported **0 added** with both
sitting in the tree. Fixing the detector took the section-scoped uncited count from **1 to 7** —
six rules that had been invisible to every view.

⛔ **The fix is not "drop the anchor".** That would add real rules and real noise together, and
a count nobody trusts is the defect `rules` already had. The discriminator is what FOLLOWS the
stop sign: a bolded span, a capitalized word, or an imperative. A stop sign used as a noun
("a `⛔` gate", "the old ⛔"), one that survives only inside a code span, and one at end-of-line
are all excluded.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude/skills/production-readiness-audit/conformance.py"
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"


def load():
    spec = importlib.util.spec_from_file_location("_conformance", CONFORMANCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CONF = load()

# The three shapes the anchor missed, verbatim in form from the corpus.
MISSED_SHAPES = {
    "numbered-list item":
        "2. ⛔ **Strip everything identifying.** No hostname, username, or file path.",
    "appended to a list item's prose":
        "- **`Upstream:`** `not applicable` unless Step 2b says `mcp-server`. ⛔ **Do not offer it.**",
    "continuing a sentence":
        'read from `plugin.json`, else "Unknown". ⛔ never found by searching the filesystem',
}

# Prose ABOUT the convention, which must stay out. Each is a real corpus line.
NOUN_USES = {
    "parenthetical listing conventions":
        "For a protocol-heavy (⛔ gates, INV-056 pinned wording, one-👉-per-turn),",
    "a gate referred to as a thing":
        "This is a ⛔ gate: wait for the real choice, do not assume one (INV-007).",
    "an instruction about skipping gates":
        "- Steps marked `⛔` are mandatory gates. NEVER skip a ⛔ gate or a numbered 👉 step",
    "the glyph discussed in a code span":
        "Follow the ground rules throughout: `🛑`/`⛔` are internal, never rendered;",
    "a trailing stop sign wrapping to the next line":
        "needs an arm in which that flag is absent. Following the old ⛔",
}


class TheMissedShapesAreNowSeen(unittest.TestCase):
    def test_each_shape_classifies_as_a_rule(self):
        for name, line in MISSED_SHAPES.items():
            with self.subTest(shape=name):
                self.assertEqual(
                    "mid-line", CONF.classify(line),
                    "%s is not recognized as a hard rule. This is one of the three shapes the "
                    "line-start anchor missed; 191 corpus lines were invisible because of it."
                    % name)

    def test_the_anchored_shape_still_classifies_as_anchored(self):
        """Anchored hits must keep their label, because past figures counted only those."""
        self.assertEqual("anchored", CONF.classify("⛔ **Never do the thing.**"))
        self.assertEqual("anchored", CONF.classify("> ⛔ **Never do the thing.**"))
        self.assertEqual("anchored", CONF.classify("Some prose that **MUST** hold."))
        # ⚠️ A DASH before the stop sign was never anchored either. The spec said the pattern
        # "admits `-` but not `1.`"; measured, it admits NEITHER -- the optional `-` belongs to
        # the bolded-MUST alternative, not the stop-sign one. So `- ⛔ …` list items were in the
        # missed population all along, which widens the finding rather than narrowing it.
        self.assertEqual("mid-line", CONF.classify("- ⛔ **Never do the thing.**"))
        self.assertEqual("mid-line", CONF.classify("2. ⛔ **Never do the thing.**"))


class NounUsesStayOut(unittest.TestCase):
    def test_prose_about_the_convention_is_not_a_rule(self):
        for name, line in NOUN_USES.items():
            with self.subTest(usage=name):
                self.assertIsNone(
                    CONF.classify(line),
                    "%s was classified as a hard rule (%r). Dropping the anchor without a "
                    "discriminator adds noise with the signal, and a count nobody trusts is the "
                    "defect this replaced." % (name, CONF.classify(line)))

    def test_the_corpus_fixture_the_spec_named_is_still_excluded(self):
        """`model-selection.md`'s conventions parenthetical — named in the spec as the fixture.

        Line-scoped by design (#424): ``conformance.py`` classifies one line at a time, and this
        asserts what that classifier does with the line.
        """
        path = PLUGIN / "docs" / "model-selection.md"
        self.assertTrue(path.is_file(), "fixture file moved: %s" % path)
        offenders = [
            (i, line.strip()) for i, line in
            enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if "⛔ gates" in line and CONF.classify(line) is not None]
        self.assertEqual([], offenders,
                         "the conventions parenthetical is being counted as a rule: %s" % offenders)


class EveryViewInheritsOneDefinition(unittest.TestCase):
    """⛔ Three views with three copies of a pattern is how one silently stops matching."""

    def test_no_view_matches_hard_rules_with_its_own_pattern(self):
        source = CONFORMANCE.read_text(encoding="utf-8")
        bodies = re.split(r"(?m)^def ", source)
        for body in bodies:
            name = body.split("(")[0].strip()
            if not name.startswith(("cmd_", "rule_rows")):
                continue
            with self.subTest(view=name):
                self.assertNotIn(
                    "ANCHORED_RULE.search", body,
                    "%s reaches past classify() to the anchored pattern, so it will not see "
                    "mid-line rules." % name)
                self.assertNotRegex(
                    body, r"re\.compile\([^)]*⛔",
                    "%s compiles its own stop-sign pattern instead of calling classify()" % name)

    def test_all_three_views_report_the_same_total(self):
        import subprocess
        import sys

        def total(argv, pattern):
            out = subprocess.run([sys.executable, str(CONFORMANCE)] + argv,
                                 capture_output=True, text=True, cwd=str(REPO_ROOT))
            self.assertEqual(0, out.returncode, out.stderr)
            m = re.search(pattern, out.stdout)
            self.assertIsNotNone(m, "could not parse %r:\n%s" % (argv, out.stdout))
            return int(m.group(1))

        self.assertEqual(
            total(["rules"], r"(\d+) hard-rule lines \("),
            total(["per-rule"], r"(\d+) hard-rule lines, \d+ citing"),
            "`rules` and `per-rule` disagree on how many hard rules exist, so they are not "
            "using the same definition.")


class TheOutputSeparatesThePopulations(unittest.TestCase):
    def test_rules_reports_anchored_and_mid_line_separately(self):
        import subprocess
        import sys
        out = subprocess.run([sys.executable, str(CONFORMANCE), "rules"],
                             capture_output=True, text=True, cwd=str(REPO_ROOT)).stdout
        m = re.search(r"(\d+) hard-rule lines \((\d+) line-anchored \+ (\d+) mid-line\)", out)
        self.assertIsNotNone(
            m, "`rules` does not split the two populations. Folding 134 newly-visible lines "
               "into one headline would make every figure in past ledger entries -- which "
               "counted only the anchored population -- look like a regression:\n%s" % out)
        total, anchored, midline = (int(g) for g in m.groups())
        self.assertEqual(total, anchored + midline, "the split does not sum to the total")
        self.assertGreater(midline, 0,
                           "no mid-line rules reported; the detector has re-anchored")
        self.assertIn("LINE-ANCHORED number", out,
                      "the output does not tell a reader which figure past entries compare to")

    def test_the_residual_limitation_is_stated_where_the_count_is_printed(self):
        import subprocess
        import sys
        out = subprocess.run([sys.executable, str(CONFORMANCE), "per-rule"],
                             capture_output=True, text=True, cwd=str(REPO_ROOT)).stdout
        self.assertIn("Residual limitation", out)
        self.assertIn("16 to 202", out,
                      "the residual limitation should name why bare prose 'must' is excluded, "
                      "so the exclusion reads as a decision rather than an oversight")


if __name__ == "__main__":
    unittest.main()
