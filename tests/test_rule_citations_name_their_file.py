"""A cross-file rule citation names its file and subject, never a bare ordinal.

Two shipped sites cited their authority as "Agent Rule N" -- a bare ordinal into a numbered
list defined in a third file, under a heading whose preamble reads "The following rules are
mandatory for the agent executing **this module**":

  module-03b-truthset-visualization/phase1-visualization.md -- "(Agent Rule 5)" for where to
      save TRUTH SET load artifacts. Rule 5 governs *verification* artifacts, Module 3's; and
      that list's Rule 1 says System Verification "MUST NOT acquire, load, or visualize the
      Senzing Truth Set". So module-03b derived its instruction from a ruleset that explicitly
      disclaims jurisdiction over what module-03b does.
  module-03-system-verification/SKILL.md -- "(Agent Rule 9)". Same module, so resolvable in
      principle, but still positional.

The placement both sentences prescribe is CORRECT -- INV-050's layout tree puts the Truth Set's
load artifacts under ``src/system_verification/``, and the list's own Rule 8 says so citing
INV-050 by ID. What was wrong is the authority cited, and two structural properties made it
worse than a one-off:

1. **Positional references are silently re-pointed by any edit to the list.** Not hypothetical:
   `specs/module3-synthetic-verification-data.md` records rewriting this exact list when Module
   3 moved from Truth Set to synthetic data. Both external citations survived still resolving
   to plausible rules -- by luck. Nothing re-checked them and nothing would have failed.
2. **A bare ordinal is unreachable at the point of use** (INV-183): a guide executing
   `phase1-visualization.md` has no way to look up "Agent Rule 5".

`citations.py verify` structurally cannot see this -- it resolves ``INV-NNN`` IDs, and
"Agent Rule 5" is not one.

Per **INV-246** the site set is derived by scanning every shipped Markdown file for the
citation shape, never from a hardcoded path list -- the defect is precisely that an author
enumerated where they noticed a pattern, so a listed guard would repeat the mistake.

⛔ **This guard checks that a citation is RESOLVABLE, not that it is CORRECT.** It cannot tell
that Rule 5 was the wrong rule for a Truth Set sentence; only reading does that. A clean run
means no bare ordinals remain, not that every citation points at the rule that governs.

Source spec: `specs/agent-rule-citations-are-positional-and-cross-a-module-boundary.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
RULES_LIST = (PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md")

#: A citation naming a numbered rule by ordinal alone: "(Agent Rule 5)", "per Rule 9".
#: Deliberately narrow -- a hit is worth reading, a miss is weak evidence (paraphrase evades it).
BARE_ORDINAL = re.compile(r"(?i)\((?:agent )?rule\s+\d+\)|per (?:agent )?rule\s+\d+")

#: A file that DEFINES a numbered rule list can cite it by ordinal freely — the reader has the
#: list in front of them. Matched as a heading or bold intro whose subject is "rules".
DEFINES_A_RULE_LIST = re.compile(r"(?im)^#{2,4} .*\brules\b.*$|\*\*[^*]*\brules\b[^*]*:\*\*")

#: A citing file that names some other Markdown file can be resolved by following it.
NAMES_A_FILE = re.compile(r"[\w./-]+\.md")


def shipped_markdown():
    """Every shipped Markdown file, discovered rather than listed (INV-246)."""
    return sorted(PLUGIN.rglob("*.md"))


def read(path):
    return path.read_text(encoding="utf-8")


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_corpus_is_actually_scanned(self):
        self.assertGreater(
            len(shipped_markdown()), 20,
            "the shipped Markdown sweep found almost nothing — this guard is inspecting an "
            "empty set and would pass forever")

    def test_the_rules_list_it_protects_still_exists(self):
        self.assertTrue(RULES_LIST.is_file(), "%s moved" % RULES_LIST)
        self.assertRegex(
            read(RULES_LIST), r"(?m)^## Agent Rules$",
            "the Agent Rules heading is gone; if the list was renamed, this guard's premise "
            "and the citations pointing at it both need revisiting")


class NoShippedFileCitesARuleByBareOrdinal(unittest.TestCase):
    def test_every_numbered_rule_citation_is_resolvable_from_its_file(self):
        """A citation resolves if the file defines the list, or names a file that might.

        ⚠️ This is FILE-level resolvability, not line-level: a file that both defines its own
        rules and cites another module's would pass here while still carrying one ambiguous
        ordinal. Intra-file ordinals are deliberately permitted — `phase1-verification.md`
        cites its own Agent Rules from inside the file that defines them, and a reader there
        has the list in front of them. The defect is the CROSS-file ordinal.
        """
        offenders = []
        for path in shipped_markdown():
            text = read(path)
            if DEFINES_A_RULE_LIST.search(text) or NAMES_A_FILE.search(text):
                continue
            # Matched across line wraps (#424): "per agent\nrule 3" is one citation.
            for n in match_lines(text, BARE_ORDINAL):
                offenders.append("%s:%d: %s" % (path.relative_to(REPO_ROOT), n,
                                                text.split("\n")[n - 1].strip()[:140]))
        self.assertEqual(
            [], offenders,
            "a shipped file cites a numbered rule by ordinal and neither defines that list nor "
            "names any file that could. The ordinal is re-pointed silently by any edit to the "
            "list, and a guide cannot resolve it at the step where it must act (INV-183):\n  "
            + "\n  ".join(offenders))

    def test_a_wrapped_bare_ordinal_is_caught_at_its_first_line(self):
        """Negative control (#424): "per agent" ends line 1 and "rule 3" begins line 2."""
        wrapped = "Stop here and ask, per agent\nrule 3, before writing anything.\n"
        self.assertEqual([1], match_lines(wrapped, BARE_ORDINAL))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(BARE_ORDINAL.search(l) for l in wrapped.split("\n")))

    def test_the_cross_module_routing_citation_names_the_file_it_indexes(self):
        """Pinned: bootcamp-preparation indexes a list that lives in Module 2."""
        text = re.sub(r"\s+", " ", read(PLUGIN / "skills" / "bootcamp-preparation" / "SKILL.md"))
        self.assertIn(
            "../module-02-sdk-setup/SKILL.md", text,
            "bootcamp-preparation cites the Module 2 routing rules by ordinal without naming "
            "the file that defines them, so the numbers cannot be checked from where they are "
            "read")
        self.assertRegex(
            text, r"(?i)Routing rules \(apply in order\)",
            "the pointer does not name the list's own heading, so a reader must guess which "
            "numbered list in that file is meant")


class TheTwoRepairedSitesStaySpecific(unittest.TestCase):
    """Pinned individually: these are the sites whose citation was wrong, not merely bare."""

    def test_the_truthset_artifact_sentence_cites_the_rule_that_governs(self):
        """Scoped to the passage, not the file.

        ⚠️ An earlier version asserted `"INV-087" in text` file-wide and a mutation dropping it
        from this sentence ESCAPED — the ID appears elsewhere in the file. Asserting a token
        appears *somewhere* rather than that the claim holds *where it is made* is this repo's
        recurring escape; the bound is the fix.
        """
        flat = re.sub(r"\s+", " ", read(
            PLUGIN / "skills" / "module-03b-truthset-visualization" / "phase1-visualization.md"))
        m = re.search(r"Save the load artifacts under.{0,520}", flat)
        self.assertIsNotNone(
            m, "the Truth Set artifact-placement sentence is gone; this guard's subject moved")
        passage = m.group(0)
        self.assertRegex(
            passage, r"src/system_verification/` — that is where INV-050",
            "the artifact-placement sentence no longer cites INV-050, the layout rule that "
            "actually governs where those artifacts go")
        self.assertIn(
            "INV-087", passage,
            "the sentence does not cite INV-087, which is why one module's artifacts "
            "legitimately sit in a directory named for another")

    def test_the_no_web_service_line_cites_the_registered_rule(self):
        text = re.sub(r"\s+", " ", read(
            PLUGIN / "skills" / "module-03-system-verification" / "SKILL.md"))
        self.assertRegex(
            text, r"starts \*\*no\*\* web service \(INV-087",
            "the no-web-service line no longer cites INV-087, the registered invariant that "
            "separates the two modules' web services")


if __name__ == "__main__":
    unittest.main()
