"""A why demonstration must parse the field a why response actually carries.

Module 7 step 4b.3 told the guide to pass `SZ_INCLUDE_MATCH_KEY_DETAILS` and explained it as
"the match key Senzing used to decide these records belong together". A why response carries
no `MATCH_KEY_DETAILS`. The breakdown of the why key lives at

    WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS

confirmed on MCP server 1.32.9 (2026-08-14) via
`get_sdk_reference(topic='response_schemas', filter='why_records')`.

The flag names a different surface. `topic='flags'` reports `SZ_INCLUDE_MATCH_KEY_DETAILS`
with `response_paths: RELATED_ENTITIES[]` and `depends_on` one of the five relations flags, so
what it *documentedly* populates is a `MATCH_KEY_DETAILS` object on each *related entity*.
(⚠️ **Dated note, 2026-10-14 (#591): on server 1.38.2 the entry has no `depends_on` field** —
the relations dependency is stated only in its description — and `response_paths` reads
`RELATED_ENTITIES[].MATCH_KEY_DETAILS`. The related-entity surface is unchanged, so the
reasoning below still binds; the guards ask for the dependency in prose, not as a field name.)

That is the silent-blank failure `ground-rules.md` → "Defensive parsing" exists for: a parser
written for the wrong field name yields None and renders as empty text, with no error raised.
The step's own prose was what pointed at the wrong name.

⛔ **CORRECTED 2026-08-17 — this file previously enforced a claim that was wrong.** From the
above it concluded *"on a why call it has nothing to attach to"* and asserted a ⛔ forbidding
the flag on why calls. That inference was never measured: the 2026-08-14 table it rested on
passed the flag in **both** arms, so the flag's contribution was never varied. On **SDK 4.3.4**
`WHY_KEY_DETAILS` was **absent** with `SZ_INCLUDE_FEATURE_SCORES` alone and **present** once
`SZ_INCLUDE_MATCH_KEY_DETAILS | SZ_ENTITY_INCLUDE_ALL_RELATIONS` was added; on **4.3.2** absent
without it. Following the ban produced a why demonstration with no match-key breakdown at all —
and because every other field rendered, it read as *"this SDK doesn't provide that detail"*.

⚠️ **What the server says is unchanged and still narrow:** re-verified on **1.32.9,
2026-08-17**, 29 flags apply to `why_records` and **none** names `WHY_KEY_DETAILS` in its
`response_paths`. So the field is documented and attributed to no flag; server position and
engine observation are held apart (INV-169), and no version floor is written from a matrix that
never varied the relevant term.

So this file asserts the step names the real path, that the flag is prescribed **with** its
relations dependency and its conditions, that every mention of it carries a qualifier, that the
composite-vs-member type hazard is stated, and that the pre-existing
`response_schemas`-before-parsing instruction survived. The field-name correction —
`WHY_KEY_DETAILS`, never `MATCH_KEY_DETAILS`, on a why response — is untouched by the reversal.

Source specs: `specs/why-response-carries-why-key-details-not-match-key-details.md` (the field
name), and `specs/why-key-details-needs-the-flag-the-plugin-forbids.md` (this correction).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE2 = (
    REPO_ROOT
    / "plugins"
    / "senzing-bootcamp"
    / "skills"
    / "module-07-query-visualize-discover"
    / "phase2-discover.md"
)


def read():
    return PHASE2.read_text(encoding="utf-8")


def squash(text):
    """Collapse newlines and runs of spaces so wrapped prose matches as one line."""
    return re.sub(r"\s+", " ", text)


def enclosing_block(text, offset):
    """The paragraph or list item containing ``offset``.

    Bounded by a blank line either side rather than by a fixed window: the prose that
    qualifies a flag mention sits at the head of its own block, and a fixed window is
    the wrong length by construction — too short and it misses a qualifier three
    sentences up (which produced a false positive here), too long and it borrows a
    qualifier from an unrelated neighboring block.
    """
    start = text.rfind("\n\n", 0, offset)
    end = text.find("\n\n", offset)
    return text[(0 if start < 0 else start): (len(text) if end < 0 else end)]


def step_4b3(text):
    """The body of step 4b.3, where the flag guidance lives."""
    start = text.index("3. **SDK flags and response shape:**")
    end = text.index("4. **Plain-language explanation", start)
    return text[start:end]


def flag_guidance(text):
    """The bullet that governs `SZ_INCLUDE_MATCH_KEY_DETAILS` on a why call.

    ⚠️ **This used to be `prohibition_bullet()`, anchored on "⛔ Do not reach for".** That
    ban was **withdrawn on 2026-08-17**: it rested on a measurement whose two arms both
    passed the flag, so the flag's contribution was never varied and "already there without
    it" was never tested. On SDK 4.3.4 `WHY_KEY_DETAILS` was absent without the flag and
    present with it; on 4.3.2 absent without it. Following the ban produced a why
    demonstration with no match-key breakdown at all, silently.

    Spans from its ⛔ marker to the next sibling bullet, so guidance that drifts out of this
    block falls outside it — the same span technique, applied to the corrected rule.
    """
    body = step_4b3(text)
    start = body.index("⛔ **`WHY_KEY_DETAILS` may need")
    nxt = re.search(r"\n   - ", body[start:])
    return body[start:start + nxt.start()] if nxt else body[start:]


class WhyKeyDetailsIsTheParsedField(unittest.TestCase):
    def test_step_4b3_names_the_full_why_key_details_path(self):
        """Naming the leaf alone would let a parser guess the wrong parent."""
        self.assertIn(
            "WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS", squash(step_4b3(read()))
        )

    def test_the_why_key_details_shape_is_described_for_the_parser(self):
        """CONFIRMATIONS[] is what the step goes on to present; the schema names it."""
        body = squash(step_4b3(read()))
        self.assertIn("CONFIRMATIONS[]", body)
        for field in ("FTYPE_CODE", "TOKEN", "SCORE_BUCKET"):
            self.assertIn(field, body, f"{field} missing from the WHY_KEY_DETAILS shape")

    def test_step_5_reads_the_why_key_from_its_documented_path(self):
        """Step 5 presents the key; an unnamed 'match-key string' is the guessable part."""
        text = read()
        start = text.index("5. **Match-key breakdown:**")
        step5 = squash(text[start:text.index("6. **Practical use cases:**", start)])
        self.assertIn("WHY_RESULTS[].MATCH_INFO.WHY_KEY", step5)
        self.assertIn("WHY_KEY_DETAILS", step5)


class TheFlagIsPrescribedWithItsConditions(unittest.TestCase):
    """⚠️ Was `MatchKeyDetailsIsNotPrescribedForAWhyCall`; its premise was withdrawn.

    The old class asserted that every `MATCH_KEY_DETAILS` mention sat inside a ⛔ forbidding
    the flag on why calls. That ban is retracted (see `flag_guidance`), so what is asserted
    now is the corrected rule: the flag is **prescribed with a relations flag**, the server
    position and the engine observation are kept apart (INV-169), and no version floor is
    written. What survives unchanged from the old file is the field-name correction —
    `WHY_KEY_DETAILS`, never `MATCH_KEY_DETAILS`, is what a why response carries — and that
    is asserted in `WhyKeyDetailsIsTheParsedField` above and below.
    """

    def test_the_flag_is_prescribed_together_with_a_relations_flag(self):
        guidance = squash(flag_guidance(read()))
        self.assertIn("pass `SZ_INCLUDE_MATCH_KEY_DETAILS` together with a relations flag",
                      guidance)

    def test_the_dependency_that_makes_it_checkable_survives(self):
        """The half of the old ban that was always true, and still is.

        ⚠️ Asked for `depends_on` until #591: on server 1.38.2 the flag's entry has no such
        field, so the dependency is required as the entry's description states it.
        """
        guidance = squash(flag_guidance(read()))
        self.assertIn("relations dependency", guidance)
        self.assertIn("relations flag", guidance)
        self.assertNotIn("`depends_on`", guidance)

    def test_the_flags_documented_surface_is_still_named(self):
        """It populates MATCH_KEY_DETAILS on RELATED_ENTITIES[] — also still true."""
        guidance = squash(flag_guidance(read()))
        self.assertIn("RELATED_ENTITIES[]", guidance)

    def test_the_server_position_and_the_observation_are_separate(self):
        """INV-169 — neither presented as governing the other."""
        guidance = squash(flag_guidance(read()))
        # ⚠️ The server's position is now that the requirement IS documented —
        # `requires_flags: ["SZ_INCLUDE_MATCH_KEY_DETAILS"]` in `response_schemas`
        # (1.35.3, 2026-09-01). The separation this asserts is unchanged: the documented
        # requirement and the engine observation are stated as different kinds of claim.
        self.assertIn("requires_flags", guidance)
        self.assertIn("observation-only", guidance)
        self.assertIn("INV-080/INV-149", guidance)

    def test_no_version_floor_is_asserted(self):
        """⛔ Writing one would repeat the error this correction exists for."""
        guidance = squash(flag_guidance(read()))
        self.assertIn("NOT a version floor", guidance)
        self.assertIn("never run on 4.3.2", guidance)

    def test_the_withdrawn_ban_is_gone_from_the_step(self):
        self.assertNotIn("Do not reach for `SZ_INCLUDE_MATCH_KEY_DETAILS`", read())

    def test_the_correction_says_what_it_corrects(self):
        """A silent reversal leaves the next editor free to restore the ban."""
        guidance = squash(flag_guidance(read()))
        self.assertIn("corrects a directive that used to forbid the flag here", guidance)
        self.assertIn("both passed the flag", guidance)


class NoOtherSiteInTheModulePrescribesIt(unittest.TestCase):
    """The criterion named one file; the defect was in two.

    `phase1-query-visualize.md` step 3a carried the same instruction — "ensure the query
    was called with SZ_INCLUDE_FEATURE_SCORES and/or SZ_INCLUDE_MATCH_KEY_DETAILS" for
    the why_* methods — and was invisible to a guard scoped to `phase2-discover.md`.
    So this sweeps the module: a fix applied to one file is not a fix.
    """

    #: What makes a mention of the flag checkable rather than a bare prescription.
    #:
    #: ⚠️ Rewritten 2026-08-17 with the ban's withdrawal. The rule is unchanged in spirit —
    #: every mention states the reason it can silently do nothing — but "it has no surface
    #: on a why call" was false, so that qualifier is replaced by the two that are true: the
    #: relations dependency, and the conditioned observation about when the field appears.
    QUALIFIERS = (
        "relations dependency",        # the documented dependency (its description, #591)
        "relations flag",              # the same, in prose
        "RELATED_ENTITIES[]",          # the surface the flag documentedly populates
        "no flag is documented as populating it",   # the server's silence, stated
        "observation-only",            # the conditioned engine result
        "not from a `MATCH_KEY_DETAILS`",   # the surviving field-name correction
        "never from a `MATCH_KEY_DETAILS`",
    )

    def test_the_flag_is_never_mentioned_without_a_qualifier(self):
        """Every mention carries what makes it checkable.

        The flag is legitimate for the methods that return related entities — a network
        visualization renders exactly the `RELATED_ENTITIES[]` it populates — so a blanket
        ban would be wrong, and one was written and had to be withdrawn. What is never
        optional is the reason it can silently do nothing: it needs a relations flag, and
        whether it is required for `WHY_KEY_DETAILS` is an observation rather than a
        documented guarantee. A mention carrying neither is the shape that produced this
        defect twice in one module.
        """
        for path in sorted(PHASE2.parent.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"SZ_INCLUDE_MATCH_KEY_DETAILS", text):
                with self.subTest(file=path.name, offset=match.start()):
                    block = squash(enclosing_block(text, match.start()))
                    self.assertTrue(
                        any(q in block for q in self.QUALIFIERS),
                        "%s mentions SZ_INCLUDE_MATCH_KEY_DETAILS at offset %d with none "
                        "of its qualifying conditions in the same block"
                        % (path.name, match.start()),
                    )

    def test_phase1_names_the_why_key_details_path(self):
        """The reader of step 3a needs the right field, not merely the ban."""
        phase1 = squash((PHASE2.parent / "phase1-query-visualize.md").read_text(encoding="utf-8"))
        self.assertIn("WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS", phase1)
        self.assertIn("INV-179", phase1)

    def test_phase1_still_prescribes_feature_scores(self):
        """The correct half of the original instruction must survive the correction."""
        phase1 = squash((PHASE2.parent / "phase1-query-visualize.md").read_text(encoding="utf-8"))
        self.assertIn("SZ_INCLUDE_FEATURE_SCORES", phase1)


class Phase1PointsAtTheOneStatement(unittest.TestCase):
    """#611: the WHY_KEY_DETAILS rule is stated in full once, in step 4b.3 (INV-300).

    `phase1-query-visualize.md` carried two more full copies, in step 2's composite-flags
    guidance and in step 3a, and each said it was stated once. Their stamps had drifted
    apart (1.35.3 in one, 1.37.19 in the other). Both sites are now pointers; this checks
    that each names the owner and the invariant, and that the parts of the rule which drift
    (the routes, the stamps, the engine-side observation) are not copied back into them.
    """

    PHASE1 = PHASE2.parent / "phase1-query-visualize.md"

    #: Each pointer site, from a marker at its head to the end of its block.
    SITES = {
        "step 2": "⛔ **Add `SZ_INCLUDE_MATCH_KEY_DETAILS` together",
        "step 3a": "⛔ **(INV-115) And the rename is the whole `MATCH_*` family",
    }

    #: What the full statement carries and a pointer must not.
    COPY_MARKERS = ("requires_flags", "4.3.4", "4.3.2", "1.35.3", "1.37.19",
                    "dependent on using one of the following flags", "observation-only")

    def pointer(self, marker):
        text = self.PHASE1.read_text(encoding="utf-8")
        start = text.index(marker)
        end = text.find("\n\n", start)
        return squash(text[start:end])

    def test_each_site_names_step_4b3_and_inv_300(self):
        for site, marker in self.SITES.items():
            with self.subTest(site=site):
                text = self.pointer(marker)
                self.assertIn("`phase2-discover.md` step 4b.3", text)
                self.assertIn("INV-300", text)
                self.assertIn("stated once", text)

    def test_no_site_carries_a_second_copy(self):
        for site, marker in self.SITES.items():
            for token in self.COPY_MARKERS:
                with self.subTest(site=site, token=token):
                    self.assertNotIn(token, self.pointer(marker))

    def test_the_one_statement_carries_one_stamp(self):
        """The server half of step 4b.3's rule carries exactly one server stamp."""
        guidance = flag_guidance(read())
        server_half = guidance[guidance.index("**What the server documents**"):
                               guidance.index("⚠️ **What was observed, engine-side")]
        self.assertEqual(1, len(re.findall(r"server \*\*\d+\.\d+\.\d+\*\*", server_half)))


class FlagTypesAreConfirmedNotOnlyNames(unittest.TestCase):
    def test_the_composite_member_hazard_is_stated_in_the_flag_guidance(self):
        """A composite need not share the element type of a flag *collection* argument."""
        body = squash(step_4b3(read()))
        self.assertIn("composite_members", body)
        self.assertIn("topic='parameters'", body)

    def test_the_hazard_is_stated_once(self):
        """'Stated once' is the acceptance criterion; twice is drift waiting to disagree."""
        self.assertEqual(1, squash(read()).count("composite_members"))


class ThePreExistingSchemaInstructionSurvived(unittest.TestCase):
    def test_response_schemas_is_still_consulted_before_parsing(self):
        """Following this instruction is what surfaces the wrong field name (INV-115)."""
        body = squash(step_4b3(read()))
        self.assertIn("topic='response_schemas', filter='why_records'", body)
        self.assertIn("INV-115", body)

    def test_feature_scores_is_still_prescribed_with_its_explanation(self):
        """The other half of the original 'BOTH flags' pair is correct and must remain."""
        body = squash(step_4b3(read()))
        self.assertIn("SZ_INCLUDE_FEATURE_SCORES", body)
        self.assertIn("numeric similarity scores", body)


if __name__ == "__main__":
    unittest.main()
