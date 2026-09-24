"""Module 7's query-program step points at the factory-lifetime rule, and does not copy it.

INV-152 says the Senzing factory must outlive every engine it creates. The rule shipped and
was correct, and it still did not bind: a 2026-08-18 run on plugin 0.5.1 factored engine setup
into a shared helper that built the factory in a local and returned only the engine, and the
first engine call failed with `SzSdkError - engine object has been destroyed…`.

⛔ **The rule was unreachable from where it binds.** Writing several query programs is what
makes anyone factor engine setup into one helper, and Module 7 step 2 -- "Create query
programs" -- carried no pointer to the rule at all. INV-183: a rule that names a step must be
reachable AT that step.

⚠️ **This pins a POINTER, not a copy (INV-300).** `ground-rules.md` owns the rule's wording; the
pointing site must name the owner and the invariant and carry **no second copy**. So this guard
asserts both halves -- that step 2 cites INV-152 and names the owner, *and* that the rule's own
statement still resolves in exactly one place under `plugins/`. Asserting only the first would
be satisfied by pasting the rule into module 7, which is the defect INV-300 exists to prevent.

⛔ **What this does NOT establish:** that a bootcamper reads the pointer, or that generated code
obeys it. Only a live run observes that, and `dry-run` phase 3 is the only thing that can. An
`Enforced by` clause on this test is not a compliance claim.

⚠️ **The symptom text is deliberately allowed in both files.** The `SzSdkError` string is an SDK
literal the reader must recognize, not the rule -- pinning it as single-owner would force the
pointer to describe the failure without naming it.

Stdlib only; both files are read as text (INV-108).

Source issue: #134.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_7 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"

#: The step whose readers write the helper. Bounded by the next same-level heading.
STEP_HEADING = "## 2. Create query programs"

#: The rule's own statement, owned by `ground-rules.md`. ⚠️ Matched tolerantly across
#: whitespace and inline markup: the wording wraps mid-sentence in the source, so a pattern
#: requiring it on one line would report a single owner while a second copy sat two files away.
RULE_STATEMENT = re.compile(
    r"factory\s+(?:\*\*)?must(?:\*\*)?\s+outlive\s+every\s+engine\s+it\s+creates", re.I)

#: The owner a pointer must name, and the invariant it must cite.
OWNER = "ground-rules.md"
INVARIANT = "INV-152"


def step_2():
    """The text of step 2, from its heading to the next `## ` heading."""
    text = MODULE_7.read_text(encoding="utf-8")
    start = text.find(STEP_HEADING)
    if start < 0:
        return ""
    rest = text[start + len(STEP_HEADING):]
    nxt = rest.find("\n## ")
    return rest if nxt < 0 else rest[:nxt]


def shipped_markdown():
    return sorted(p for p in SKILLS.rglob("*.md") if p.is_file())


class TheInputsAreReal(unittest.TestCase):
    """INV-265 -- both assertions below read these; a silent miss would pass vacuously."""

    def test_both_files_exist(self):
        for name, path in (("module 7 phase 1", MODULE_7), ("ground-rules", GROUND_RULES)):
            with self.subTest(what=name):
                self.assertTrue(path.is_file(), "%s is missing at %s" % (name, path))

    def test_step_2_was_located_and_is_not_empty(self):
        body = step_2()
        self.assertTrue(
            body.strip(),
            "step 2 (%r) was not found in %s, so the citation assertion would pass over an "
            "empty string. If the heading was reworded, update STEP_HEADING -- do not delete "
            "this test" % (STEP_HEADING, MODULE_7))

    def test_the_owner_really_carries_the_rule(self):
        """⛔ The single-owner assertion is meaningless if the owner does not state the rule."""
        self.assertTrue(
            RULE_STATEMENT.search(GROUND_RULES.read_text(encoding="utf-8")),
            "%s no longer states the factory-lifetime rule. The pointer in module 7 now points "
            "at nothing, and the single-owner check below would pass by finding zero copies "
            "everywhere" % GROUND_RULES)


class TheRuleIsReachableFromWhereItBinds(unittest.TestCase):
    """INV-183 -- the step whose readers write the helper must reach the rule."""

    def test_step_2_cites_the_invariant(self):
        self.assertIn(
            INVARIANT, step_2(),
            "Module 7 step 2 does not cite %s. Writing several query programs is when engine "
            "setup gets factored into a helper, and that is the move the rule governs; a "
            "reader here has no way to look it up" % INVARIANT)

    def test_step_2_names_the_owning_file(self):
        self.assertIn(
            OWNER, step_2(),
            "Module 7 step 2 cites the invariant but does not name %s, so the reader is told a "
            "rule exists and not where it is stated (INV-300)" % OWNER)

    def test_every_relative_link_in_step_2_resolves(self):
        """A pointer to a path that does not exist reads as authoritative and goes nowhere.

        ⚠️ **Deliberately unfiltered.** An earlier form checked only links whose text contained
        `ground-rules.md`, so renaming the target to `ground-rules-v2.md` removed it from the
        filter and the loop body never ran -- the assertion passed by skipping the one link it
        existed to check. Its own negative control is what exposed that.
        """
        links = set(re.findall(r"\]\((\.\./[^)]+\.md)\)", step_2()))
        self.assertTrue(
            links,
            "step 2 carries no relative Markdown link at all, so the pointer to the rule's "
            "owner has gone and this assertion would pass over an empty set")
        for rel in sorted(links):
            with self.subTest(link=rel):
                self.assertTrue(
                    (MODULE_7.parent / rel).resolve().is_file(),
                    "step 2 links %r, which does not resolve from %s"
                    % (rel, MODULE_7.parent))

    def test_a_link_in_step_2_points_at_the_owning_file(self):
        """Resolving is not enough -- one of them must be the owner named above."""
        links = set(re.findall(r"\]\((\.\./[^)]+\.md)\)", step_2()))
        self.assertTrue(
            any(Path(rel).name == OWNER for rel in links),
            "no link in step 2 points at %s; the reader is told a rule exists and given no "
            "way to reach it. Links present: %s" % (OWNER, sorted(links)))


class TheRuleStillHasOneOwner(unittest.TestCase):
    """⛔ INV-300 -- a pointing site must carry no second copy of the rule it points at."""

    def test_the_rule_statement_resolves_in_exactly_one_shipped_file(self):
        owners = [p for p in shipped_markdown()
                  if RULE_STATEMENT.search(p.read_text(encoding="utf-8"))]
        rel = sorted(str(p.relative_to(REPO_ROOT)) for p in owners)
        self.assertEqual(
            [str(GROUND_RULES.relative_to(REPO_ROOT))], rel,
            "the factory-lifetime rule is stated in %d shipped file(s): %s. It must be stated "
            "in ground-rules.md alone -- a copy that drifts is undetectable by construction, "
            "because the duplication scan reports EXACT repeats and two statements that have "
            "stopped matching are precisely what it cannot see (INV-300)" % (len(rel), rel))

    def test_step_2_does_not_restate_the_rule(self):
        """The same property at the one site most likely to acquire a copy."""
        self.assertIsNone(
            RULE_STATEMENT.search(step_2()),
            "Module 7 step 2 now states the factory-lifetime rule itself. That satisfies the "
            "citation assertions above while recreating the fork INV-300 forbids: point at "
            "ground-rules.md instead of copying it")


if __name__ == "__main__":
    unittest.main()
