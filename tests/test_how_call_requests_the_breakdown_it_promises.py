"""A how call that names MATCH_KEY_DETAILS must request the flag that populates it.

Step 4c told the guide to call `how_entity` with `SZ_INCLUDE_FEATURE_SCORES` -- which the server
confirms IS the method's default -- while step 4b, ninety lines earlier in the same file, offered
`how_entity`'s `MATCH_KEY_DETAILS.CONFIRMATIONS[]` as the reason the how side is worth reaching
for. Followed literally the two did not meet: on **SDK 4.3.4** with that flag alone, `MATCH_INFO`
carried `['CANDIDATE_KEYS', 'ERRULE_CODE', 'FEATURE_SCORES', 'MATCH_KEY']` and `MATCH_KEY_DETAILS`
was **absent** -- not present-and-empty, which is a third state step 4b is careful to distinguish.

⛔ **This is the why-side defect one method over.** The ⛔ that forbade
`SZ_INCLUDE_MATCH_KEY_DETAILS` on why calls was withdrawn by
`specs/why-key-details-needs-the-flag-the-plugin-forbids.md`, whose criteria were scoped to **why**
calls throughout -- so the how call was never in its blast radius and kept the pre-correction flag
set. The lesson this guard encodes: sweep over the **claim** (which flags a breakdown needs), never
over the method that happened to surface it.

⚠️ **The server says four things about where this field lands, and one still disagrees with the
rest** -- and this guard requires all four to be recorded with none presented as governing
(INV-169):

  * `SZ_INCLUDE_MATCH_KEY_DETAILS.applies_to` **includes** `how_entity_by_entity_id`;
  * the how `response_schemas` document
    `HOW_RESULTS.RESOLUTION_STEPS[].MATCH_INFO.MATCH_KEY_DETAILS.CONFIRMATIONS[]` in full;
  * that same schema marks those paths `requires_flags: ["SZ_INCLUDE_MATCH_KEY_DETAILS"]` -- the
    documented requirement, added as the fourth statement by #591 (server 1.38.2, 2026-10-14);
  * the flag entry's `response_paths` are `RELATED_ENTITIES[].MATCH_KEY_DETAILS` only, and its
    description attributes the object to *related entities* -- a shape `how_entity` never returns.

⚠️ **Corrected 2026-10-14 (#591).** Through server 1.33.0 this docstring quoted the flag entry's
`response_paths` as `RELATED_ENTITIES[]` and `RESOLVED_ENTITY.*`, and its relations dependency as
a `depends_on` field. On 1.38.2 the entry has neither: the paths narrowed to the related-entity
object, and the dependency is stated only in its description. The rules above still bind.

The last statement is a coverage gap on the server's side, so the plugin must treat the breakdown
as CONDITIONAL rather than promised. A guard that demanded the plugin pick a side would be
requiring it to invent a Senzing fact (INV-080).

⛔ **The field spellings must NOT be harmonized.** `why_*` returns `WHY_KEY_DETAILS`; `how_entity`
returns `MATCH_KEY_DETAILS`. Both are correct on their own method, and merging them would
reintroduce the defect `specs/why-response-carries-why-key-details-not-match-key-details.md` fixed.

Stdlib only; shipped markdown read as text (INV-108).

Source spec: `specs/how-side-flag-instruction-contradicts-its-own-confirmations-observation.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"

DETAILS_FLAG = "SZ_INCLUDE_MATCH_KEY_DETAILS"
SCORES_FLAG = "SZ_INCLUDE_FEATURE_SCORES"

#: A step or endpoint that PRESCRIBES the flags for a how call. Matched on the instruction shape
#: rather than on a path, so a third site inherits this guard (INV-246). This scan is what found
#: the contract's `/api/how` endpoint and Module 7's own flag paragraph, neither of which the
#: source spec named as defective.
HOW_CALL_PRESCRIPTION = re.compile(
    r"(?i)(?:generate the `how_entity` call"
    r"|Backed by `how_entity_by_entity_id`)")

#: Wide enough to contain the whole prescribing block. Step 4c's block runs past 6,000
#: characters, and at 2,600 its later half -- the observations table, the FEATURE_SCORES
#: fallback, the field-spelling split -- fell outside the window, so four assertions failed
#: against text that was present in the file.
WINDOW = 9000


def flat(text):
    return " ".join(text.split())


def shipped():
    return sorted(SKILLS.glob("**/*.md"))


def how_call_sites():
    """(path, window) for each shipped site prescribing a how call's flags."""
    out = []
    for path in shipped():
        text = flat(path.read_text(encoding="utf-8"))
        for match in HOW_CALL_PRESCRIPTION.finditer(text):
            out.append((path, text[match.start():match.start() + WINDOW]))
    return out



class Base(unittest.TestCase):
    """Assertions that report the finding, not the haystack.

    `assertRegex`/`assertIn` embed the entire searched window in the failure message; these
    windows run to 9,000 characters, which buries the one line that matters.
    """

    def has(self, text, pattern, msg):
        self.assertTrue(re.search(pattern, text), msg)

    def lacks(self, text, pattern, msg):
        self.assertIsNone(re.search(pattern, text), msg)


class TheScanFindsThePrescribingSites(Base):
    def test_both_known_prescribing_sites_are_found(self):
        found = how_call_sites()
        self.assertGreaterEqual(
            len(found), 2,
            "fewer than the two shipped sites that prescribe a how call's flags -- Module 7 step "
            f"4c and the contract's /api/how endpoint (found {len(found)}). The scan has drifted, "
            "so the assertions below check less than they appear to",
        )


class NoHowCallRequestsScoresAloneWhileNamingTheBreakdown(Base):
    """Criterion 1, stated as the claim rather than as a path."""

    def test_every_prescribing_site_names_the_details_flag(self):
        for path, window in how_call_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.has(window, re.escape(DETAILS_FLAG),
                         f"{path.name} prescribes a how call without naming {DETAILS_FLAG}, so a "
                         "step that shows the match-key breakdown requests only the method's "
                         "default and renders nothing")

    def test_every_prescribing_site_pairs_it_with_a_relations_flag(self):
        """Its documented relations dependency holds regardless of the response_paths tension.

        ⛔ Scoped to the 300 characters following the flag's FIRST mention, not the whole
        window. "relations flag" occurs all over these files, so a window-wide search stayed
        true after the pairing was deleted from the prescription -- the assertion passed on
        the defect. The pairing has to be stated where the flag is prescribed, or a reader
        following the prescription does not see it.
        """
        for path, window in how_call_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                at = window.find(DETAILS_FLAG)
                self.assertNotEqual(-1, at, f"{path.name} does not prescribe {DETAILS_FLAG}")
                near = window[at:at + 300]
                self.has(near, r"(?i)relations flag|SZ_ENTITY_INCLUDE_ALL_RELATIONS",
                         f"{path.name} prescribes the details flag without its relations flag "
                         "beside it, so it is accepted and adds nothing -- which reads as absent "
                         "data rather than a missing flag")

    def test_no_site_claims_the_default_is_sufficient(self):
        for path, window in how_call_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.lacks(window,
                           r"(?i)`?SZ_HOW_ENTITY_DEFAULT_FLAGS`? (?:is|are) (?:enough|sufficient)",
                           f"{path.name} claims the how default suffices for the breakdown; the "
                           f"server returns that composite as {SCORES_FLAG} alone")


class TheStepTreatsTheBreakdownAsConditional(Base):
    """The server's own statements disagree, so the plugin must not promise the field."""

    def setUp(self):
        self.step = None
        for path, window in how_call_sites():
            if "phase2-discover.md" in str(path):
                self.step = window
        self.assertIsNotNone(self.step, "Module 7 step 4c no longer prescribes the how call")

    def test_it_states_the_fallback_to_feature_scores(self):
        self.has(self.step, r"(?i)render `?FEATURE_SCORES`? instead|fall back to `?FEATURE_SCORES`?",
                 "step 4c does not name the FEATURE_SCORES fallback, so an absent breakdown leaves "
                 "the demonstration with nothing to show")

    def test_it_forbids_an_empty_section(self):
        self.has(self.step, r"(?i)[Nn]ever render an empty section",
                 "step 4c does not forbid an empty section, which is indistinguishable from a "
                 "feature the engine lacks")

    def test_it_forbids_a_no_value_returned_rendering(self):
        self.has(self.step, r'(?i)never print "no value returned"',
                 'step 4c does not forbid a "no value returned" rendering, which reads as a '
                 "failure rather than as a conditional field")

    def test_it_records_both_engine_observations_with_their_conditions(self):
        self.has(self.step, r"2026-08-18", "the earlier observation is not recorded")
        self.has(self.step, r"2026-08-24", "the later observation is not recorded")

    def test_the_unrecorded_flag_set_is_marked_unrecorded(self):
        """Otherwise the row reads as evidence the breakdown appears without the flag."""
        self.has(self.step, r"(?i)not recorded",
                 "the 2026-08-18 row's flag set is not marked unrecorded, so it reads as evidence "
                 "that the breakdown appears without the flag -- which it is not")

    def test_it_asserts_no_version_or_flag_floor(self):
        self.has(self.step, r"(?i)[Dd]o not\s+write a version floor or a flag floor",
                 "step 4c does not forbid writing a floor from a matrix that never varied the "
                 "relevant term -- the error the why-side correction documents")

    def test_it_marks_the_engine_observations_observation_only(self):
        self.has(self.step, r"observation-only",
                 "the engine observations are not marked observation-only (INV-080/INV-149)")

    def test_it_keeps_the_dump_before_parse_instruction(self):
        """INV-115 — what turned this absence into a finding rather than a blank section."""
        self.has(self.step, r"(?i)dump `?MATCH_INFO`?'?s? keys|dump `MATCH_INFO`",
                 "step 4c no longer tells the guide to dump MATCH_INFO's keys before parsing")


class TheServersFourStatementsAreAllRecorded(Base):
    """INV-169 — record all four, reconcile none. Checked wherever the tension is discussed.

    Was `TheServersThreeStatementsAreAllRecorded`; #591 added the how schema's
    `requires_flags` as the fourth, documented statement (server 1.38.2, 2026-10-14).
    """

    def _tension_sites(self):
        out = []
        for path in shipped():
            text = flat(path.read_text(encoding="utf-8"))
            if "coverage gap on the server's side" in text:
                out.append((path, text))
        return out

    def test_the_tension_is_stated_somewhere(self):
        self.assertTrue(
            self._tension_sites(),
            "no shipped file records that the server's statements about MATCH_KEY_DETAILS on a how "
            "response disagree, so a later reader resolves it by picking one -- which is how the "
            "flag came to be excluded from how calls",
        )

    def test_each_site_records_all_four_statements(self):
        for path, text in self._tension_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.has(text, r"`applies_to` \*\*includes\*\* `how_entity_by_entity_id`",
                         f"{path.name}: the applies_to statement is missing")
                self.has(text, r"RELATED_ENTITIES\[\]\.MATCH_KEY_DETAILS",
                         f"{path.name}: the response_paths statement is missing")
                self.has(text,
                         r"HOW_RESULTS\.RESOLUTION_STEPS\[\]\.MATCH_INFO\.MATCH_KEY_DETAILS",
                         f"{path.name}: the how response_schemas path is missing")
                self.has(text, r'requires_flags: \["SZ_INCLUDE_MATCH_KEY_DETAILS"\]',
                         f"{path.name}: the how schema's requires_flags is missing -- the one "
                         "statement that documents the requirement")

    def test_each_site_refuses_to_reconcile_them(self):
        for path, text in self._tension_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.has(text, r"(?i)[Rr]ecord all four.{0,40}reconcile none",
                         f"{path.name} records the four statements without saying none governs "
                         "the others, which invites the next reader to resolve it by choosing")

    def test_each_site_carries_route_version_and_date(self):
        """INV-080 — a Senzing fact carries the call that established it."""
        for path, text in self._tension_sites():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.has(text, r"get_sdk_reference\(topic='flags'",
                         f"{path.name}: no route named")
                self.has(text, r"topic='response_schemas', filter='how_entity'",
                         f"{path.name}: the requires_flags route is not named")
                self.has(text, r"server \*\*1\.\d+\.\d+\*\*|server 1\.\d+\.\d+",
                         f"{path.name}: no server version")
                self.has(text, r"\d{4}-\d{2}-\d{2}", f"{path.name}: no verification date")


class TheFlagEntryIsDescribedAsTheServerReturnsIt(Base):
    """#591 — `SZ_INCLUDE_MATCH_KEY_DETAILS`'s entry, as served on 1.38.2 (2026-10-14).

    `get_sdk_reference(topic='flags', filter='SZ_INCLUDE_MATCH_KEY_DETAILS')` returns no
    `depends_on` field (the dependency is in its description), `response_paths` is
    `RELATED_ENTITIES[].MATCH_KEY_DETAILS` alone, and the `SZ_ENTITY_INCLUDE_ALL_RELATIONS`
    filter no longer returns the flag. A shipped sentence saying otherwise sends a maintainer
    to look for something the server does not return.

    ⚠️ `depends_on` stays legitimate as a generic flag-entry field: the
    `SZ_ENTITY_INCLUDE_RELATED_*` flags carry one. So this checks the SENTENCE that names
    this flag, never the bare word.
    """

    @staticmethod
    def sentences(text):
        return re.split(r"(?<=[.;])\s+", text)

    def test_no_sentence_gives_the_flag_a_depends_on_field(self):
        for path in shipped():
            for sentence in self.sentences(flat(path.read_text(encoding="utf-8"))):
                if DETAILS_FLAG in sentence and "depends_on" in sentence:
                    self.fail(f"{path.relative_to(REPO_ROOT)} writes `depends_on` as a field of "
                              f"{DETAILS_FLAG}'s entry, which has none on 1.38.2: {sentence[:200]}")

    def test_no_site_quotes_the_retired_response_paths(self):
        for path in shipped():
            text = flat(path.read_text(encoding="utf-8"))
            self.lacks(text, r"`RELATED_ENTITIES\[\]` and `RESOLVED_ENTITY\.\*`",
                       f"{path.relative_to(REPO_ROOT)} quotes {DETAILS_FLAG}'s response_paths as "
                       "`RELATED_ENTITIES[]` and `RESOLVED_ENTITY.*`; it is "
                       "`RELATED_ENTITIES[].MATCH_KEY_DETAILS` alone")

    def test_no_site_says_the_relations_filter_returns_it(self):
        for path in shipped():
            text = flat(path.read_text(encoding="utf-8"))
            self.lacks(text, r"(?i)exception in that same reply|returned by the "
                             r"`SZ_ENTITY_INCLUDE_ALL_RELATIONS` filter",
                       f"{path.relative_to(REPO_ROOT)} says the relations filter returns "
                       f"{DETAILS_FLAG}; on 1.38.2 it does not")

    def test_the_sentence_scan_is_not_vacuous(self):
        bad = f"`{DETAILS_FLAG}` `depends_on` a relations flag, so pass it."
        self.assertTrue(any(DETAILS_FLAG in x and "depends_on" in x
                            for x in self.sentences(bad)))


class TheTwoFieldSpellingsStayApart(Base):
    """Criterion 5 — a test fails if either spelling is used on the other method."""

    def test_no_shipped_file_reads_match_key_details_off_a_why_response(self):
        bad = re.compile(r"WHY_RESULTS\[\][^ ]{0,40}MATCH_KEY_DETAILS")
        for path in shipped():
            text = flat(path.read_text(encoding="utf-8"))
            for match in bad.finditer(text):
                window = text[max(0, match.start() - 200):match.end() + 120]
                if re.search(r"(?i)never from a|not from a|rather than", window):
                    continue  # the correction that forbids exactly this
                self.fail(f"{path.relative_to(REPO_ROOT)} reads MATCH_KEY_DETAILS off a why "
                          "response; the why side's field is WHY_KEY_DETAILS")

    def test_no_shipped_file_reads_why_key_details_off_a_how_response(self):
        bad = re.compile(r"HOW_RESULTS[^ ]{0,60}WHY_KEY_DETAILS")
        for path in shipped():
            text = flat(path.read_text(encoding="utf-8"))
            self.assertIsNone(
                bad.search(text),
                f"{path.relative_to(REPO_ROOT)} reads WHY_KEY_DETAILS off a how response; the "
                "how side's field is MATCH_KEY_DETAILS",
            )

    def test_the_split_is_stated_where_the_how_call_is_prescribed(self):
        for path, window in how_call_sites():
            if "phase2-discover.md" not in str(path):
                continue
            self.has(window,
                     r"(?i)`MATCH_KEY_DETAILS` on the how side and `WHY_KEY_DETAILS` on the why",
                     "step 4c prescribes the how call without stating which spelling belongs to "
                     "it, so a parser carried over from the why side silently yields nothing")

    def test_the_anti_harmonization_warning_survives(self):
        for path, window in how_call_sites():
            if "phase2-discover.md" not in str(path):
                continue
            self.has(window, r"(?i)do not harmonize them",
                     "step 4c no longer warns against harmonizing the two spellings")


if __name__ == "__main__":
    unittest.main()
