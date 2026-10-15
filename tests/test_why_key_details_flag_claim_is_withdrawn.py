"""No shipped file claims the why-key breakdown appears without the flag.

A guide followed the module's explicit ⛔ — *"Do not reach for
`SZ_INCLUDE_MATCH_KEY_DETAILS` here … The CONFIRMATIONS and DENIALS named above are already
there without it"* — and its why-analysis renderer produced **no match-key breakdown at
all**. Probing the same record pair on **Senzing SDK 4.3.4**:

    SZ_INCLUDE_FEATURE_SCORES                                        WHY_KEY_DETAILS absent
    + SZ_ENTITY_INCLUDE_ENTITY_NAME                                  WHY_KEY_DETAILS absent
    + SZ_INCLUDE_MATCH_KEY_DETAILS | SZ_ENTITY_INCLUDE_ALL_RELATIONS WHY_KEY_DETAILS present

⛔ **The claim was inferred from a measurement whose two arms BOTH passed the flag.** The
2026-08-14 table varied the *relations* flags, not `SZ_INCLUDE_MATCH_KEY_DETAILS` — so the
flag's contribution was never observed, and the conclusion was nonetheless stated in the
strongest available form and shipped as a ⛔. A negative about a flag is only supported by an
arm in which that flag is **absent**; where no such arm was run the honest form is "not
measured", not "not needed". That is INV-194's reasoning applied to a flag matrix.

⚠️ **The failure was silent and the directive made it look correct.** Every other analytical
field rendered, so a guide obeying the ⛔ faithfully concluded *"this SDK doesn't provide that
detail"* rather than *"a flag is missing"* — INV-179's shape, reached by following the same
file's own instruction.

⛔ **What must NOT be written either.** That the flag is *documented* to populate
`WHY_KEY_DETAILS`: it is not. Re-verified on server **1.32.9, 2026-08-17** —
`get_sdk_reference(topic='flags', filter='why_records')` returns 29 flags applying to
`why_records` and **none** names `WHY_KEY_DETAILS` in its `response_paths`;
`SZ_INCLUDE_MATCH_KEY_DETAILS`' own documented effect is a `MATCH_KEY_DETAILS` object on each
**related entity**; and `SZ_WHY_RECORDS_DEFAULT_FLAGS` is `SZ_INCLUDE_FEATURE_SCORES` alone.
Server position and engine observation are stated separately, neither governing the other
(INV-169).

⛔ **And no version floor.** Both builds were observed *without* the flag; only 4.3.4 was
observed *with* it. The evidence is equally consistent with "required on both" and says
nothing about a boundary — writing a floor would repeat the original error exactly.

Source spec: `specs/why-key-details-needs-the-flag-the-plugin-forbids.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
PHASE1 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
PHASE2 = SKILLS / "module-07-query-visualize-discover" / "phase2-discover.md"
API_REFERENCE = (SKILLS / "module-03b-truthset-visualization" /
                 "visualization-api-reference.md")


def flat(path):
    """Flattened text, with Markdown blockquote markers stripped first.

    ⚠️ Without stripping `> `, a sentence wrapped inside a blockquote flattens with the
    marker welded into its middle — which reported a present sentence as absent.
    """
    text = path.read_text(encoding="utf-8")
    return " ".join(re.sub(r"(?m)^\s*>\s?", "", text).split())


class TheWithdrawnWordingIsGoneEverywhere(unittest.TestCase):
    """⛔ Derived by scanning every shipped file, not from the spec's list of three."""

    #: Phrasings that assert the breakdown needs no flag. Each is the claim, not a synonym.
    WITHDRAWN = (
        "already there without it",
        "on a why call it adds nothing",
        "it has nothing to attach to",
        "Do not reach for `SZ_INCLUDE_MATCH_KEY_DETAILS` here",
        "not by adding `SZ_INCLUDE_MATCH_KEY_DETAILS`",
    )

    #: Words that mark a mention as a QUOTATION of the retracted claim rather than a use of
    #: it. The correction has to be able to say what it corrects — the same carve-out
    #: `MCP-NEGATIVE-SCAN: quoted-history` exists for elsewhere in this repo.
    RETRACTION_MARKERS = ("that was wrong", "on the grounds that", "used to forbid",
                          "briefly forbade", "previously removed", "corrects a directive")

    def test_no_shipped_file_carries_any_withdrawn_phrasing(self):
        offenders = []
        for path in sorted((REPO_ROOT / "plugins").rglob("*.md")):
            text = " ".join(
                re.sub(r"(?m)^\s*>\s?", "", path.read_text(encoding="utf-8")).split())
            for phrase in self.WITHDRAWN:
                start = 0
                while True:
                    found = text.find(phrase, start)
                    if found == -1:
                        break
                    start = found + 1
                    window = text[max(0, found - 240):found + 240]
                    if any(mark in window for mark in self.RETRACTION_MARKERS):
                        continue
                    offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase!r}")
        self.assertEqual(
            [], offenders,
            "a withdrawn claim is ASSERTED (not quoted as retracted) — following it "
            "produces a why demonstration with no match-key breakdown, silently:\n  "
            + "\n  ".join(offenders))

    def test_the_scan_would_catch_a_reintroduction(self):
        """Not-vacuous: a bare assertion, with no retraction nearby, must be reported."""
        window = "The CONFIRMATIONS and DENIALS are already there without it, so omit it."
        self.assertFalse(any(mark in window for mark in self.RETRACTION_MARKERS))

    def test_the_retraction_carve_out_is_actually_exercised(self):
        """It must be doing real work — otherwise it is silently permissive."""
        text = flat(PHASE2)
        self.assertIn("already there without it", text,
                      "the step no longer quotes the claim it corrects, so the carve-out "
                      "is untested and could hide a genuine reintroduction")
        self.assertIn("on the grounds that", text)


class TheStepTellsTheGuideToPassTheFlag(unittest.TestCase):

    def setUp(self):
        self.text = flat(PHASE2)

    def test_it_says_to_pass_it_with_a_relations_flag(self):
        self.assertIn("pass `SZ_INCLUDE_MATCH_KEY_DETAILS` together with a relations flag",
                      self.text)

    def test_the_relations_dependency_survives(self):
        """Was `test_the_depends_on_requirement_survives`, pinning "its documented `depends_on`
        still holds". On server 1.38.2 the flag's entry has no `depends_on` field; the
        dependency is in its description, so the step states it that way (#591)."""
        self.assertIn("the relations dependency its own row documents still holds", self.text)

    def test_the_java_composite_caution_survives(self):
        """A composite constant may not belong to a Set<SzFlag> element type."""
        self.assertIn("composite_members", self.text)
        # The caution must route the reader to the topic that reports a binding type.
        self.assertIn("topic='parameters'", self.text)

    def test_the_java_composite_is_named_a_set_not_a_long(self):
        """Corrected 2026-08-26 against the installed sz-sdk.jar.

        This assertion previously pinned "`long` bitmask, which will not compile into
        that argument", which describes the *plural* class `SzFlags` and sent the reader
        to the class that does not fit a `Set<SzFlag>` parameter. Verified with javap and
        javac: `SzFlag.SZ_ENTITY_INCLUDE_ALL_RELATIONS` is a `Set<SzFlag>` static field on
        the enum class and is not an enum constant, so it merges with `addAll` and cannot
        appear in `EnumSet.of`; `SzFlags.SZ_ENTITY_INCLUDE_ALL_RELATIONS` is a `long` (960).
        """
        self.assertIn("`Set<SzFlag>` static field", self.text)
        self.assertIn("merged with `addAll` rather than listed in `EnumSet.of`", self.text)
        # The trap is that both shapes exist under one name; the plural class must be named.
        self.assertIn("class `SzFlags`", self.text)

    def test_the_superseded_long_bitmask_claim_is_only_quoted_history(self):
        """The retracted wording may appear only as quoted history, never as guidance.

        The phrase "`long` bitmask" is legitimately current when it describes `SzFlags`,
        the plural class. What must never stand alone is the retracted *attribution* —
        that the composite you pass is a long — which is the claim that sent the reader
        to the wrong class. It survives only inside the sentence withdrawing it.
        """
        retracted = "the composite is a `long` bitmask"
        self.assertIn(retracted, self.text,
                      "the correction must still quote what it corrects, or the carve-out "
                      "is untested and could hide a genuine reintroduction")
        idx = self.text.find(retracted)
        while idx != -1:
            self.assertIn("previously said", self.text[max(0, idx - 60):idx],
                          "the retracted attribution appears outside the retraction that "
                          "withdraws it, so the wrong claim reads as current guidance")
            idx = self.text.find(retracted, idx + 1)


class TheServerPositionAndTheObservationAreSeparate(unittest.TestCase):
    """INV-169 — two known things, neither presented as governing the other."""

    def setUp(self):
        self.text = flat(PHASE2)

    def test_the_server_position_is_stated_with_its_route(self):
        """⚠️ The server's POSITION changed; the requirement that it be stated did not.

        This pinned the sentence *"no flag is documented as populating it"* against
        `server 1.32.9, 2026-08-17`, which was the server's position when written. On
        **1.35.3, 2026-09-01** `get_sdk_reference(topic='response_schemas',
        filter='why_entities')` carries `requires_flags: ["SZ_INCLUDE_MATCH_KEY_DETAILS"]`
        on the why-side path, so the sentence is now false. The class's claim — the server
        position is stated, with the route that establishes it — is unchanged, and is what
        this asserts instead of the retired wording (INV-282: pin the claim, not the
        phrasing that happened to carry it).

        ⚠️ Asked for a ``1.35.x`` version anywhere in the file until #611. Step 4b.3 is now
        the one full statement of the rule (INV-300) and carries one stamp, from the live
        re-check (1.38.2, 2026-10-15), so this asks for a dated server stamp on the
        "What the server documents" line itself rather than for one version.
        """
        self.assertIn("requires_flags", self.text)
        self.assertIn("filter='why_entities'", self.text)
        self.assertRegex(
            self.text,
            r"\*\*What the server documents\*\* \(server \*\*1\.\d+\.\d+\*\*, "
            r"20\d\d-\d\d-\d\d\)")

    def test_the_flags_documented_effect_is_named_correctly(self):
        """The flags topic still attributes only the RELATED_ENTITIES path to this flag.

        That half is unchanged on 1.35.3 and is why both topics must be read: a reader
        who checks only `flags` still finds the why-side field unattributed.
        """
        self.assertIn("RELATED_ENTITIES[].MATCH_KEY_DETAILS", self.text)

    def test_the_engine_result_is_marked_observation_only(self):
        self.assertIn("observation-only, not an MCP claim", self.text)
        self.assertIn("INV-080/INV-149", self.text)

    def test_both_sdk_builds_are_recorded(self):
        self.assertIn("Senzing SDK 4.3.4", self.text)
        self.assertIn("SDK 4.3.2", self.text)

    def test_the_observed_values_are_recorded(self):
        self.assertIn("+NAME score 95 (CLOSE)", self.text)


class NoVersionFloorIsWritten(unittest.TestCase):
    """⛔ Writing one would repeat the exact error this spec corrects."""

    def setUp(self):
        self.text = flat(PHASE2)

    def test_it_states_explicitly_that_this_is_not_a_floor(self):
        self.assertIn("This is NOT a version floor", self.text)

    def test_it_says_why_the_matrix_cannot_support_one(self):
        self.assertIn("the with-flag arm was never run on 4.3.2", self.text)

    def test_it_forbids_writing_one(self):
        self.assertIn("Do not write one", self.text)


class TheRemedyIsStatedAtTheStep(unittest.TestCase):

    def setUp(self):
        self.text = flat(PHASE2)

    def test_it_requires_dumping_match_info_keys_first(self):
        self.assertIn("Dump `MATCH_INFO`'s top-level keys before writing the parser",
                      self.text)

    def test_it_forbids_an_empty_section(self):
        self.assertIn("never render an empty section", self.text)

    def test_it_prescribes_an_explicit_not_returned_line(self):
        self.assertIn("match-key breakdown not returned by this SDK for these flags",
                      self.text)

    def test_it_names_the_fallback(self):
        self.assertIn("fall back to `FEATURE_SCORES`", self.text)

    def test_it_says_why_an_omission_is_worse_than_a_statement(self):
        self.assertIn("indistinguishable from a feature the engine does not have", self.text)


class TheFieldNameCorrectionSurvives(unittest.TestCase):
    """⛔ The prior spec's central finding must not be undone by this change."""

    def test_the_why_field_is_still_why_key_details(self):
        for path in (PHASE1, PHASE2):
            with self.subTest(path=path.name):
                self.assertIn("`WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS`", flat(path))

    def test_no_file_reads_match_key_details_from_a_why_response(self):
        self.assertIn("never from a `MATCH_KEY_DETAILS` field", flat(PHASE1))

    def test_the_how_versus_why_key_asymmetry_is_intact(self):
        text = flat(API_REFERENCE)
        self.assertIn("`why_*` puts a **`WHY_KEY_DETAILS`** object inside `MATCH_INFO`", text)
        self.assertIn("`how_entity_by_entity_id` puts a **`MATCH_KEY_DETAILS`** object", text)


class TheApiReferenceRecordsThatItWasRight(unittest.TestCase):
    """The plugin held two contradictory statements; this file's was the correct one."""

    def setUp(self):
        self.text = flat(API_REFERENCE)

    def test_it_notes_the_with_the_flag_wording_is_load_bearing(self):
        self.assertIn('The "with the flag" in that sentence is load-bearing', self.text)

    def test_it_records_the_observation_with_its_conditions(self):
        """⚠️ Same correction: the observation stays, the server's position moved.

        The retired half asserted *"no flag is *documented* to populate it"*. The server
        documents it as of 1.35.3, so this now pins the observation marker plus the route
        that carries the requirement.
        """
        self.assertIn("observation-only", self.text)
        self.assertIn("requires_flags", self.text)


if __name__ == "__main__":
    unittest.main()
