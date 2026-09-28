"""An absent license limit means "never measured", not "no custom license".

Phase A and Phase B both reconcile a record-count-derived `LICENSE REQUIRED` note against
the limit the bootcamp has detected, reading `license_record_limit` from
`config/bootcamp_progress.json`. Both had the same third branch:

    Absent or null -> no custom license was detected, so the default-limit note is the
                      right assumption. Relay it.

The only writer of that field is Module 4's Step 8a gate, which is **volume-gated by
design** — it fires only when collected volume approaches the limit. A bootcamper with a
small dataset never triggers it, so the field is absent regardless of the installed
license. Absent means *not asked*.

Measured on a dry-run walk (2026-08-14), `SzProduct.getLicense()` on SDK 4.3.4 returned
`{"customer":"Senzing Internal", ..., "recordLimit":0, ...}` — the no-cap case the first
branch exists to suppress — while `license_record_limit` was absent, so the text routed to
"relay it". The guide then relays a 500-record note, and `sdk_guide`'s sampling
prescription with it, to someone whose license has no cap: the exact harm the step names
two paragraphs earlier, reached through the branch that is taken far more often.

It also contradicted a higher-precedence rule. `ground-rules.md` states that a value you
measured on this machine governs over generic guidance about that same value, and names
the license record limit explicitly (INV-012).

Both files are tested together and asserted to agree, because the spec's own closing
section is that the branch exists twice: suppressing the note in Phase A while Phase B
still warns just moves the defect one phase later.

Enforces **INV-244** — where a bootcamp state field is written only conditionally, a step branching on it does not read that field's absence as a measured finding.

Enforces **INV-246** — a guard enforcing a rule across multiple shipped sites derives its site set by scanning, never by hardcoding paths. `discover_branches()` is that derivation, and the mutation that replaces it with the original two-path list fails this file.

Source spec: `specs/license-limit-assumed-when-it-could-be-measured.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M6 = SKILLS / "module-06-data-processing"
PHASE_A = M6 / "phaseA-build-loading.md"
PHASE_B = M6 / "phaseB-load-first-source.md"


def squash(text):
    return re.sub(r"\s+", " ", text)


def absent_branch(path):
    """The absent/null branch and its sub-bullets, bounded by the next top-level block.

    Bounded so a measurement instruction elsewhere in the file cannot satisfy the branch
    that actually decides what the bootcamper is told (INV-183).
    """
    text = path.read_text(encoding="utf-8")
    start = text.index("- **Absent or null**")
    rest = text[start:]
    match = re.search(r"\n\n(?=\S)", rest)
    return squash(rest[: match.start()] if match else rest)


def discover_branches():
    """Every shipped file that branches on an absent `license_record_limit`.

    ⛔ **Derived, never listed.** The first version of this guard hardcoded Phase A and
    Phase B, because the spec that produced it closed with a section titled "The same
    branch exists twice". It existed three times: `module-04-data-collection/SKILL.md`
    carried the identical branch, upstream of both, governing the paragraph where the
    sampling decision is actually made — and a guard naming two paths could not see it.

    A spec's enumeration of its own sites is a claim like any other. Discovering the set
    is what makes this test able to fail on a site nobody thought of, including a fourth.
    """
    found = []
    for path in sorted(SKILLS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "license_record_limit" in text and "- **Absent or null**" in text:
            found.append((path.name, path))
    return found


BRANCHES = discover_branches()


class TheDiscoveredSetIsNotVacuous(unittest.TestCase):
    """A derived sweep that finds nothing passes every other test in this file."""

    def test_every_known_branch_site_is_discovered(self):
        names = {name for name, _ in BRANCHES}
        for expected in (
            "phaseA-build-loading.md",
            "phaseB-load-first-source.md",
            "SKILL.md",  # module-04-data-collection, the site a hardcoded pair missed
        ):
            self.assertIn(expected, names, "discovery missed %s" % expected)
        self.assertGreaterEqual(len(BRANCHES), 3, BRANCHES)


class TheBranchMeasuresRatherThanAssumes(unittest.TestCase):
    """Criterion 1 — and the whole point: the value is one SDK call away."""

    def test_neither_branch_relays_a_default_without_measuring(self):
        for name, path in BRANCHES:
            with self.subTest(name):
                branch = absent_branch(path)
                self.assertNotIn(
                    "the default-limit note is the right assumption", branch,
                    "%s still assumes the default limit" % name,
                )

    def test_both_branches_name_the_measurement_route(self):
        for name, path in BRANCHES:
            with self.subTest(name):
                branch = absent_branch(path)
                self.assertIn("get_license()", branch)
                self.assertIn("recordLimit", branch)

    def test_both_branches_correct_the_meaning_of_absent(self):
        """The root cause: absent was read as a finding rather than as a gap."""
        for name, path in BRANCHES:
            with self.subTest(name):
                self.assertIn('not "no custom license"', absent_branch(path))

    def test_both_branches_explain_why_the_field_is_absent(self):
        """Without the reason, a later editor restores the assumption as a simplification.

        Pins **volume-gated** — the mechanism — not merely that "Step 8a" is named. An
        earlier version asserted the latter and a mutation deleting the whole explanation
        escaped, because the branch names Step 8a again when routing to its procedure.
        Naming the writer says where the value comes from; only the mechanism says why
        its absence carries no information.
        """
        for name, path in BRANCHES:
            with self.subTest(name):
                branch = absent_branch(path)
                self.assertIn("Step 8a", branch)
                self.assertIn("volume-gated", branch)

    def test_both_branches_say_absence_implies_nothing_about_the_license(self):
        """The inference that has to die, stated as an inference."""
        for name, path in BRANCHES:
            with self.subTest(name):
                # ⛔ Emphasis-stripped and case-insensitive (INV-282). The sibling guard,
                # `test_license_limit_is_written_only_from_a_measurement.py`, was rewritten on
                # 2026-08-28 for exactly this: three sites bolded the whole phrase and one bolded
                # a word inside it, so a matcher reading raw Markdown saw three of four. This one
                # read raw text too, and a rewrite that opened the sentence with a capital and a
                # `**` put a correct site outside it.
                branch = re.sub(r"[*`]", "", absent_branch(path))
                self.assertRegex(
                    branch,
                    r"(?i)(absent no matter (what|which) license is installed"
                    r"|absence says nothing about the installed license)",
                )


class TheMeasuredValueIsPersistedAndReapplied(unittest.TestCase):
    """Criterion 2 — measuring without persisting re-measures on every later step."""

    def test_every_branch_persists_the_measured_value(self):
        """Swept, not scoped to one file.

        An earlier version asserted this of Phase A alone, and a mutation removing the
        persist instruction from Module 4 escaped. Measuring without persisting is not a
        half-fix — it re-measures at every later step and leaves the field absent for
        graduation, so the branch that reads it never settles.
        """
        for name, path in BRANCHES:
            with self.subTest(name):
                branch = absent_branch(path)
                self.assertRegex(branch, r"[Pp]ersist", "%s measures without persisting" % name)
                self.assertIn("license_record_limit", branch)

    def test_phase_a_persists_the_measured_limit(self):
        branch = absent_branch(PHASE_A)
        self.assertIn("license_record_limit", branch)
        self.assertIn("config/bootcamp_progress.json", branch)

    def test_phase_a_re_enters_the_three_branches(self):
        """Measuring and then still relaying would fix nothing."""
        branch = absent_branch(PHASE_A)
        self.assertIn("re-enter these three branches", branch)
        self.assertIn("`recordLimit: 0`", branch)

    def test_phase_b_defers_to_the_phase_a_measurement(self):
        """One measurement, not two: Phase B is reached only if Phase A did not persist."""
        self.assertIn("If Phase A already measured", absent_branch(PHASE_B))


class TheAssumptionSurvivesOnlyAsAFallback(unittest.TestCase):
    """Criterion 3 — a fallback that does not announce itself is still an assumption."""

    def test_the_default_applies_only_when_the_call_fails(self):
        for name, path in BRANCHES:
            with self.subTest(name):
                branch = absent_branch(path)
                self.assertRegex(branch, r"Only if the (call|measurement) fails")

    def test_the_fallback_is_stated_as_an_assumption(self):
        for name, path in BRANCHES:
            with self.subTest(name):
                self.assertIn("is an assumption", absent_branch(path))

    def test_phase_a_requires_naming_what_could_not_be_measured(self):
        self.assertIn("naming what could not be measured", absent_branch(PHASE_A))


class TheProcedureIsCitedNotRestated(unittest.TestCase):
    """Module 4 Step 8a already defines it; two copies drift."""

    def test_module_4_still_owns_the_measurement_procedure(self):
        m4 = squash(
            (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
             / "module-04-data-collection" / "SKILL.md").read_text(encoding="utf-8")
        )
        self.assertIn("parse `recordLimit`, and write `license_record_limit`", m4)
        self.assertIn(
            "filter='get_license')`, which documents `recordLimit` (integer)", m4)
        self.assertNotIn("no** `response_schemas` entry", m4)

    def test_phase_a_carries_the_signature_provenance(self):
        """The method is server-confirmed even though its payload is not (INV-080)."""
        branch = absent_branch(PHASE_A)
        self.assertIn("1.32.9", branch)
        self.assertIn("get_sdk_reference(topic='response_schemas'", branch)

    def test_the_unchanged_module_6_branches_are_intact(self):
        """The two correct branches must survive the rewrite of the third.

        Scoped to the Module 6 pair rather than the discovered set: Module 4 states the
        same three-way decision in its own vocabulary ("Present and greater than 0" /
        "Present and equal to 0"), which is correct there and is not this assertion's
        subject. Sweeping a wording check across sites that legitimately word it
        differently is how a guard starts failing on correct content.
        """
        for path in (PHASE_A, PHASE_B):
            with self.subTest(path.name):
                text = squash(path.read_text(encoding="utf-8"))
                self.assertIn("**`0` (no cap), or ≥ the dataset size**", text)
                self.assertIn("Positive and below the dataset size", text)

    def test_module_4_keeps_its_own_two_present_branches(self):
        """The same requirement at the third site, in that site's own vocabulary."""
        text = squash((SKILLS / "module-04-data-collection" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("Present and greater than 0", text)
        self.assertIn("Present and equal to 0", text)
        self.assertIn("confirmed via the Senzing MCP server at request time", text)


class TheInvariantScopeNoteSurvives(unittest.TestCase):
    """INV-244's carve-out is load-bearing: without it the rule reads too wide.

    `test_load_status` is also written only conditionally, and Phase A correctly reads its
    absence as "a test load is owed" — legal, because the writer of that field *is* the
    test load. Read literally and without the scope note, INV-244 forbids that too, and a
    later audit "fixing" it would restore the defect `de73e72` removed. Both branches were
    authored in the same session, which is exactly when the distinction is easiest to lose.
    """

    def setUp(self):
        text = (REPO_ROOT / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        start = text.index("- **INV-244**")
        end = text.index("\n- **INV-", start + 10)
        self.entry = squash(text[start:end])

    def test_the_scope_note_names_the_permitted_case(self):
        self.assertIn("test_load_status", self.entry)

    def test_the_scope_note_states_the_distinguishing_test(self):
        """Not 'is the write conditional' but 'what is the writer gated on'."""
        self.assertIn("same question", self.entry)
        self.assertIn("what the writer is gated on", self.entry)

    def test_the_binding_condition_is_unchanged(self):
        """The carve-out is additive; the approved sentence must remain verbatim."""
        self.assertIn(
            "a step branching on it MUST NOT read that field's absence as a measured finding",
            self.entry,
        )


if __name__ == "__main__":
    unittest.main()
