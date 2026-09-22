"""A spec asserting the server LACKS something must name the route that owns the fact.

INV-209 made this mechanical for `MCP-NEGATIVE` markers -- negatives that ship inside plugin
prose. It does not reach where two of the three known instances actually lived: a **spec's own
diagnosis**. A spec is the worse place for the error, because a spec is the *input* to
implementation.

Three wrong-route absence conclusions in one session (2026-08-13), all the same mechanism -- a
real tool, real parameters, a real empty result, an honest date, and the wrong tool asked:

1. `no-license-path-environment-variable` concluded "Senzing reads no license-path environment
   variable" from `configure`, `install` and `search_docs`. It lives in
   `sdk_guide(topic='load', record_count=<above the limit>)`. This one **shipped**: INV-208 plus
   a guard that banned the correct variable name, with the offline suite certifying both because
   guard and claim shared a premise.
2. `pattern-gallery-asks-for-more-than-mcp-can-supply` concluded the server covers 4 of 10
   use-case categories, from two broad queries. Sector vocabulary reaches nearly all of them.
   Caught pre-implementation -- but only because INV-194 was deliberately re-applied.
3. The marker convention itself (INV-209).

So the rule: an absence outcome on a spec's `MCP re-check` line must carry
`owner-checked: <route that would CARRY the fact> -- <what it returned>`.

⛔ **This file validates with SYNTHETIC fixtures, deliberately.** Both offending specs have since
been corrected, so `specs/` can no longer demonstrate the shape -- and a guard that only asserts
"`specs/` is clean" passes because the answer is already empty. That is the same vacuity that let
a stubbed detector pass earlier in the same session: a check which only ever reads the repo's
current state cannot detect its own mechanism being disabled.

Exempt: `n/a (no Senzing fact)`. With no Senzing fact there is no absence claim about the server
to substantiate. Measured before designing this: across 274 specs exactly one line matched the
absence vocabulary, and it was such an `n/a` line -- so the carve-out is required, and
retroactivity is otherwise a non-issue.

Enforces **INV-213**.

Run:  python3 -m unittest discover -s tests
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS = REPO_ROOT / "specs"
TEMPLATE = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "issue-template.md"
FEEDBACK_SKILL = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md"
IMPLEMENT_SKILL = REPO_ROOT / ".claude" / "commands" / "implement-github-issue.md"

META = {"IMPLEMENTED.md", "INVARIANTS.md", "DECLINED.md", "todo.md"}

#: Specs dated before this are grandfathered, matching how test_spec_ledger_invariants.py
#: handles retroactivity. Nothing before it needs changing -- see the measurement above.
CUTOFF = "2026-08-13"

#: Wording that asserts the server lacks something. Deliberately narrow: this runs against one
#: line per spec, where a false positive costs real trust in the message.
ABSENCE = re.compile(
    r"(?i)does not cover|returns no |return no |no MCP tool|none returns|"
    r"nothing (?:surfaced|for the rest)|not served|does not answer|never returns|"
    r"server does not"
)
#: The exemption: no Senzing fact means no absence claim about the server.
NOT_APPLICABLE = re.compile(r"(?i)n/a \(no Senzing fact\)")
OWNER_CLAUSE = re.compile(r"owner-checked:")
RECHECK_LINE = re.compile(r"^- MCP re-check:.*$", re.M)
IMPLEMENTED_DATE = re.compile(r"^- \*\*Implemented:\*\*\s*(\d{4}-\d{2}-\d{2})", re.M)


def recheck_line(text):
    m = RECHECK_LINE.search(text)
    return m.group(0) if m else None


def offending(text):
    """True when this spec text records an absence outcome with no owner clause."""
    line = recheck_line(text)
    if line is None:
        return False
    if NOT_APPLICABLE.search(line):
        return False
    return bool(ABSENCE.search(line)) and not OWNER_CLAUSE.search(line)


def spec_date(text):
    """The date a spec was worked, from its ledger-style stamp if present."""
    m = IMPLEMENTED_DATE.search(text)
    return m.group(1) if m else None


class TheDetectorWorksOnSyntheticFixtures(unittest.TestCase):
    """The mechanism, not the repo's current state — which is already clean."""

    ABSENCE_NO_OWNER = (
        "- MCP re-check: server 1.32.9, 2026-08-13 — called sdk_guide(topic='configure') and "
        "search_docs. None returns any license environment variable."
    )
    ABSENCE_WITH_OWNER = (
        "- MCP re-check: server 1.32.9, 2026-08-13 — server does not cover it. "
        "owner-checked: sdk_guide(topic='load', record_count=1000) — returns it in "
        "compatibility_notes."
    )
    NOT_APPLICABLE_LINE = (
        "- MCP re-check: **n/a (no Senzing fact).** File placement is plugin-internal; no MCP "
        "tool owns it."
    )
    POSITIVE_OUTCOME = (
        "- MCP re-check: server 1.32.9, 2026-08-13 — still reproduces. Called "
        "mapping_workflow(action='start')."
    )

    def test_an_absence_claim_without_an_owner_clause_is_flagged(self):
        self.assertTrue(
            offending(self.ABSENCE_NO_OWNER),
            "this is instance 1's original wording — the shape that shipped a false invariant",
        )

    def test_the_same_claim_with_an_owner_clause_passes(self):
        self.assertFalse(
            offending(self.ABSENCE_WITH_OWNER),
            "naming the owning route is exactly what makes the negative supportable",
        )

    def test_an_n_a_no_senzing_fact_line_is_exempt(self):
        self.assertFalse(
            offending(self.NOT_APPLICABLE_LINE),
            "the exemption is required: this is real existing wording in "
            "specs/inv017-root-readme-exception-missing.md, and it matches the absence "
            "vocabulary while making no claim about the server at all",
        )

    def test_a_positive_outcome_is_not_flagged(self):
        self.assertFalse(
            offending(self.POSITIVE_OUTCOME),
            "'still reproduces' asserts presence, not absence — flagging it would make the "
            "guard cry wolf on the common case",
        )

    def test_a_spec_with_no_recheck_line_is_not_flagged(self):
        self.assertFalse(offending("# Title\n\nno Source block at all\n"))


class SpecsInScopeCarryTheClause(unittest.TestCase):
    def test_every_spec_on_or_after_the_cutoff_names_its_owner(self):
        bad = []
        for path in sorted(SPECS.glob("*.md")):
            if path.name in META:
                continue
            text = path.read_text(encoding="utf-8")
            date = spec_date(text)
            if date is not None and date < CUTOFF:
                continue
            if offending(text):
                bad.append(f"{path.name}: {recheck_line(text)[:150]}")
        self.assertEqual(
            [], bad,
            "a spec asserts the server lacks something without naming the route that would "
            "carry it. Add `owner-checked: <route> — <what it returned>` to the MCP re-check "
            "line, and re-ask that route before trusting the diagnosis (INV-194):\n  "
            + "\n  ".join(bad),
        )

    def test_the_scan_reaches_a_useful_number_of_specs(self):
        """Non-vacuity: if the glob or the line format broke, this would silently pass.

        Measured 2026-08-13: 273 specs, of which **85** carry an `- MCP re-check:` line. The
        field is not universal — 188 specs predate its addition to the template — and the
        format that does exist is uniform (all 85 use exactly that prefix, no variants). The
        threshold below is set from that measurement rather than from an assumption; an earlier
        draft asserted "almost every spec carries one", which was never true and failed on
        correct data. The guard's forward reach is those 85 plus every spec written from the
        template hereafter.
        """
        seen = [p for p in SPECS.glob("*.md") if p.name not in META]
        self.assertGreater(
            len(seen), 200,
            "the spec scan found suspiciously few files — check the glob before trusting a "
            "clean result",
        )
        with_recheck = [p for p in seen if recheck_line(p.read_text(encoding="utf-8"))]
        self.assertGreater(
            len(with_recheck), 50,
            "far fewer specs carry an `- MCP re-check:` line than the 85 measured on "
            "2026-08-13, which means the line's format changed and this guard is now reading "
            "almost nothing. Re-derive the format before relaxing this number.",
        )


class TheRuleIsDocumentedWhereSpecsAreWrittenAndRead(unittest.TestCase):
    def test_the_template_documents_the_outcome_and_the_clause(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("server does not cover it", text,
                      "the outcome vocabulary must include an absence value, or an absence gets "
                      "recorded as though it were one of the positive outcomes")
        self.assertIn("owner-checked:", text)
        self.assertIn("INV-194", text, "the template must cite the rule this derives from")
        self.assertRegex(text, r"(?i)n/a \(no Senzing fact\)",
                         "the template must state the exemption")

    def test_feedback_to_specs_states_the_authoring_requirement(self):
        text = FEEDBACK_SKILL.read_text(encoding="utf-8")
        self.assertIn("owner-checked:", text)
        self.assertIn("INV-194", text)

    def test_implement_spec_treats_a_missing_clause_as_a_blocker(self):
        """Scoped to the owner-checked paragraph, not the whole file.

        A whole-file `blocker` regex passed while the clause had been demoted to "worth
        noting", because `blocker` occurs elsewhere in this skill (at line ~223, about a
        different check that explicitly is *not* one). Caught by negative control -- the fourth
        instance today of an assertion satisfied by text adjacent to the thing under test.
        """
        text = IMPLEMENT_SKILL.read_text(encoding="utf-8")
        self.assertIn("owner-checked:", text)
        # ⛔ Anchor on INV-213's own section, NOT on the first `owner-checked:` in the file.
        # #119 added a second mention -- R8's rule that an owner-checked line asserts NON-
        # dependence and must never be read as a dependency edge -- and it sits EARLIER in the
        # command, so `index()` began reading a paragraph about a different subject entirely.
        # The docstring above records this assertion being scoped once already for the same
        # class of reason; a first-match anchor is the same defect one level down.
        anchor = text.find("(INV-213)")
        self.assertNotEqual(
            -1, anchor,
            "INV-213's section is no longer identifiable in %s, so this assertion cannot tell "
            "which `owner-checked:` paragraph it is reading" % IMPLEMENT_SKILL)
        start = text.index("owner-checked:", anchor)
        para = text[max(0, start - 400):start + 900]
        # ⛔ The DISPOSITION, not the word. `blocker` occurs TWICE in this window -- once in
        # INV-213's heading and once in the sentence that dispositions a missing clause -- so a
        # bare `blocker` regex stays green while the disposition is demoted to "worth noting",
        # which is precisely the demotion this assertion exists to catch. Found by force-checking
        # the guard after #119 re-anchored it; the weakness predates that change. Matched on the
        # claim rather than the phrasing (INV-282), so a reworded disposition still passes.
        self.assertRegex(
            para, r"(?is)missing\s+clause.{0,120}blocker",
            "implement-spec must treat a missing owner clause on an absence claim as a blocker "
            "rather than a note — a note gets read past, and this is the step where the second "
            f"instance was actually caught.\nParagraph read:\n{para[:400]}",
        )


if __name__ == "__main__":
    unittest.main()
