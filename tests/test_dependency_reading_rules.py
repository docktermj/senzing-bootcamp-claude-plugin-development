"""The dependency report's reading rules ship, and the constructions that mislead it are pinned.

Amended R8 (#119) requires `implement-github-issue`, invoked with no argument, to review the
open issues for dependencies and report them before the maintainer chooses. ⛔ **The obvious
implementations of that are worse than not doing it**, which is why the rules are stated in the
rule rather than left to whoever writes the report.

Measured over the seven issues open in this repository on 2026-09-22:

* **Counting cross-references inverted the strongest signal.** Two issues named two others
  inside their `owner-checked:` lines -- *"the open backlog at that date was #106, #105, #79,
  #55, #53, none of which touch `conformance.py`'s corpus"*. That is an INV-213 absence claim
  asserting the issues are **unrelated**; read as an edge it reports the exact opposite.
* **Shared-file coupling made five of seven look ordered**, because five name
  `specs/INVARIANTS.md`. A hub establishes merge risk, not sequence.
* **The one real relation was visible to neither method** -- an issue quoting a figure a later
  change had already altered -- and only by reading content.

So this module does not test a dependency algorithm; there is none, and R8's report is a
procedure an agent follows. It tests that **the reading rules are stated where the procedure
will meet them**, and it pins the two constructions that produced the wrong answers, so a later
edit cannot quietly drop the lesson while leaving the feature.

⚠️ **The user-global skill carries the same rules and is NOT checked here.**
`~/.claude/skills/implement-github-issue/SKILL.md` lives outside this repository; CI checks out
only the repo, so asserting on it would fail there and pass only on a maintainer's machine. It
is unguarded, deliberately and with the gap recorded rather than hidden behind a test that
cannot run (INV-308).

⚠️ **What this does NOT establish:** that any particular run's dependency report is correct,
complete, or useful. No offline check reaches that. It establishes that the rules a correct
report must follow are present and have not been silently removed.

Source issue: #119.

Stdlib only; both surfaces are read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMAND = REPO_ROOT / ".claude" / "commands" / "implement-github-issue.md"
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"

#: The surfaces that must carry the rules. Both are in-repo; the global skill is not (see above).
SURFACES = {"the command": COMMAND, "family rule R8": FAMILY}

#: ⛔ The rules are looked for in the REGION THAT STATES THEM, never in the whole file. Scanning
#: the file was the first version of this module and three negative controls walked straight
#: through it: deleting `merge risk` from R8 left the phrase in §10's amendment log quoting R8,
#: and deleting `owner-checked` from the command left it in the command's INV-213 section. A
#: keyword present *somewhere* is not the rule being stated *here* -- the same defect this
#: repository keeps finding, in the test written to prevent it.
REGION = {
    COMMAND: ("- If `$ARGUMENTS` is **empty**", "- If `$ARGUMENTS` **names an issue**"),
    FAMILY: ("**R8 —", "\n---\n"),
}


def rule_region(path):
    """The span of `path` that states R8's rules, so a keyword elsewhere cannot satisfy them."""
    text = path.read_text(encoding="utf-8")
    start_marker, end_marker = REGION[path]
    i = text.find(start_marker)
    assert i != -1, "the rule region's start marker is gone from %s" % path
    j = text.find(end_marker, i)
    return text[i:j if j != -1 else len(text)]

#: Each rule amended R8 requires, with a pattern that recognizes it however it is worded.
#: ⛔ Keyed on the CLAIM rather than on one phrasing (INV-282): a surface may say "merge risk"
#: or "risk of conflict", and the rule is the same rule.
REQUIRED_RULES = {
    "evidence must be cited": r"(?i)evidence",
    "non-dependence is never an edge": r"(?i)non-?dependence|none of which touch",
    "owner-checked lines are named as the trap": r"owner-checked",
    "shared files are merge risk, not order": r"(?i)merge risk",
    "independence implies no order": r"(?i)impl(?:y|ies) no order",
    # ⛔ Whitespace-tolerant for the same reason as the sibling guard: both surfaces wrap these
    # clauses mid-sentence, and literal spaces matched neither (#105, fifth instance).
    "approval is required before acting":
        r"(?is)never\s+begins?\s+work|has\s+not\s+approved|may\s+not\s+start",
    "the report names a suggestion":
        r"(?is)names?\s+the\s+issue\s+it\s+suggests|name\s+the\s+issue\s+you\s+suggest"
        r"|naming\s+one\s+issue",
}

#: A reference that ASSERTS NON-DEPENDENCE. Must never be read as a dependency edge.
NOT_A_DEPENDENCY = [
    "owner-checked: the open backlog at that date was #106, #105, #79, #55, #53, none of which "
    "touch `conformance.py`'s corpus.",
    "the open backlog at that date was #79, #55, #53, none of which touch filing.",
]

#: A reference that IS a dependency. Pinned beside the ones that are not, so the distinction is
#: exercised in both directions rather than only refused in one (INV-282).
IS_A_DEPENDENCY = [
    "This cannot land until #117 removes the stale denominator it measures against.",
    "Blocked by #108: its acceptance criterion measures the corpus this one changes.",
]

#: How a reading rule distinguishes them: the absence-claim construction, not the `#n` itself.
ABSENCE_CLAIM = re.compile(r"(?i)owner-checked|none of which|does not touch|unrelated to")


class EverySurfaceCarriesEveryRule(unittest.TestCase):
    def test_each_surface_states_each_rule(self):
        for surface, path in sorted(SURFACES.items()):
            text = rule_region(path)
            for rule, pattern in sorted(REQUIRED_RULES.items()):
                with self.subTest(surface=surface, rule=rule):
                    self.assertRegex(
                        text, pattern,
                        "%s (%s) does not state the rule %r that amended R8 requires. A report "
                        "written from this text would not know to apply it" % (surface, path, rule))

    def test_the_rule_regions_were_found_and_are_small(self):
        """INV-265, and a bound: a region that swallowed the file proves nothing either."""
        for surface, path in sorted(SURFACES.items()):
            with self.subTest(surface=surface):
                region = rule_region(path)
                self.assertGreater(
                    len(region), 300,
                    "the rule region in %s (%s) is empty or nearly so; the assertions above "
                    "prove nothing" % (surface, path))
                self.assertLess(
                    len(region), len(path.read_text(encoding="utf-8")) * 0.9,
                    "the rule region in %s is almost the whole file, so scoping bought nothing "
                    "and a keyword anywhere still satisfies the rules" % surface)


def normative_text(path):
    """A surface's text with its amendment log removed.

    ⛔ §10 exists to quote the wording each amendment replaced -- that is the rule #117 shipped
    -- so the log necessarily contains clauses the document no longer imposes. Scanning it for
    stale rules would flag the amendment record for doing its job, and the fix would be to stop
    quoting the old wording, which is the one thing a child holding an earlier copy needs.
    """
    text = path.read_text(encoding="utf-8")
    i = text.find("## 10. Amendments")
    return text[:i] if i != -1 else text


class TheRecommendationBanIsGone(unittest.TestCase):
    """R8 dropped it at #119. A surface still imposing it contradicts the rule it implements."""

    def test_no_surface_still_forbids_recommending(self):
        for surface, path in sorted(SURFACES.items()):
            with self.subTest(surface=surface):
                stale = [l for l in normative_text(path).splitlines()
                         if re.search(r"(?i)does not recommend|do not recommend", l)]
                self.assertEqual(
                    [], stale,
                    "%s still forbids recommending in its normative text. R8 removed that "
                    "clause at #119; a surface keeping it tells the operation to do the "
                    "opposite of the rule it cites: %s" % (surface, stale[:1]))

    def test_the_amendment_log_is_what_was_excluded(self):
        """The exclusion must remove the LOG, not the rules -- otherwise it hides everything."""
        body = normative_text(FAMILY)
        self.assertNotIn("## 10. Amendments", body)
        self.assertIn("**R8 —", body,
                      "trimming the amendment log also removed the rules, so the scan above "
                      "runs over a fragment and proves nothing")


class AbsenceClaimsAreNotEdges(unittest.TestCase):
    """⛔ The measured inversion, pinned in both directions."""

    def test_a_non_dependence_reference_is_recognized_as_one(self):
        for line in NOT_A_DEPENDENCY:
            with self.subTest(line=line[:48]):
                self.assertTrue(
                    ABSENCE_CLAIM.search(line),
                    "a reference that asserts NON-dependence was not recognized as one, so a "
                    "reader counting `#n` would take it as a dependency edge -- the exact "
                    "inversion measured on 2026-09-22")

    def test_a_real_dependency_is_not_mistaken_for_one(self):
        for line in IS_A_DEPENDENCY:
            with self.subTest(line=line[:48]):
                self.assertFalse(
                    ABSENCE_CLAIM.search(line),
                    "a genuine dependency was classified as an absence claim; the rule would "
                    "then discard the relations it exists to find")

    def test_both_fixture_sets_are_populated(self):
        """INV-265 -- one empty side makes the distinction untested in that direction."""
        self.assertTrue(NOT_A_DEPENDENCY)
        self.assertTrue(IS_A_DEPENDENCY)


if __name__ == "__main__":
    unittest.main()
