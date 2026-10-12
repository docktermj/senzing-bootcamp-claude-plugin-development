"""The verbatim check cannot express a non-string source value, and the plugin must say so.

MCP-NEGATIVE-SCAN: ignore-file — this file asserts *about* the markers in
`phase2-data-mapping.md` (that the field-count negative carries one, and that it names the
owning route), so the token appears here as an assertion string rather than as a claim of
its own. The claims themselves live in the shipped file, where the scanner reads them.

`sz_verbatim_check.py` is delivered by the MCP server as a workflow resource. Verified
against the current resource (server 1.32.1, 2026-07-28):

* `collect_strings()` builds the allowed set under `isinstance(obj, str)` only — it
  recurses through lists and dicts but captures no other primitive;
* the test is whole-value membership, `if v.strip() not in allowed`;
* the only waiver is key-based — `EXEMPT_KEYS = {"DATA_SOURCE", "RECORD_ID"}` plus any
  attribute ending `_TYPE` — so a *value* cannot be exempted at all, and
  `REL_POINTER_KEY` is not covered.

So where a source stores a value as a JSON number, **both** emissions are reported:
emit it as a number and the checker cannot see it, emit it as a string and it is not in
`allowed`. The gate is unsatisfiable rather than strict, and it fired on all 53,321
relationship rows of a real run. The tempting way out — changing the emitted value to
turn the gate green — does not even work, and distorts the data.

The upstream defect was reported to Senzing on 2026-07-28. These tests pin the
plugin-side mitigation that has to hold until (and whether or not) it is fixed there.

#521 brought the "known reachings" table up to date (``TheReachingsTableIsCurrent``): server 1.32.2
fixed the numeric case, so it has no numeric row; it has the boolean and joined-`NAME_ORG` rows; no
row points at "this entry"; and its heading's count matches its rows. Each reaching was re-run
against the script server 1.37.27 delivers, 2026-10-12. The same issue merged the two near-duplicate
no-fork paragraphs into one, which ``no_fork_problems`` reads.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

# ⚠️ **Matches the ROUTE, not the exact argument string.** These assertions pinned the literal
# `search_docs(category='data_mapping')`, which stopped matching when
# `specs/search-docs-instructions-omit-the-required-query-parameter.md` gave every shipped
# reference the `query` the tool actually requires -- so the guards failed on the correction they
# should have welcomed, the pattern `specs/guards-pinning-a-dated-negative-outlive-it.md`
# describes. What they exist to assert is that the claim names its route; the route is still named.
ROUTE_DATA_MAPPING = re.compile(
    r"search_docs\([^)]*?category='data_mapping'\)")

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PHASE2 = PLUGIN / "skills" / "module-05-data-quality-mapping" / "phase2-data-mapping.md"
PHASE_D = PLUGIN / "skills" / "module-06-data-processing" / "phaseD-validation.md"


def flat(path):
    """Whitespace-collapsed text with blockquote markers stripped."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


class TheLimitationIsStated(unittest.TestCase):
    def test_phase2_says_the_gate_is_unsatisfiable_not_strict(self):
        self.assertRegex(flat(PHASE2), r"(?i)unsatisfiable — not strict|unsatisfiable rather than strict")

    def test_it_names_the_value_only_harvesting(self):
        """Repointed 2026-07-29: `collect_strings()` is no longer string-only.

        It flattens every string AND every int/float (stringified via `str(obj)`), skipping only
        `bool`. What survives is the *shape* of the limitation — the allowed set is built from
        source VALUES — so that is what this pins, rather than the superseded implementation
        detail `isinstance(obj, str)`.
        """
        text = flat(PHASE2)
        self.assertIn("collect_strings()", text)
        self.assertRegex(text, r"(?i)harvests source \*values\* only")
        self.assertRegex(
            text,
            r"(?i)int/float",
            "the current branch set must be stated, or the text drifts back to string-only",
        )

    def test_it_names_the_membership_test(self):
        self.assertIn("v.strip() not in allowed", flat(PHASE2))

    def test_it_names_what_cannot_be_harvested(self):
        """Replaces `test_it_states_both_emissions_are_reported` (2026-07-29).

        That test pinned "emit it as a number / emit it as a string" — the symmetry argument for
        the NUMERIC case, which server 1.32.2 fixed. Two causes remain, and naming them is what
        keeps a bootcamper from recording an exemption for a gate that is now green.
        """
        text = flat(PHASE2)
        self.assertRegex(text, r"(?i)\*\*A boolean\.\*\*|a \*\*boolean\*\*")
        self.assertRegex(text, r"(?i)derived from a source field NAME|source \*\*field NAME\*\*")

    def test_the_numeric_case_is_recorded_as_FIXED_not_as_a_limitation(self):
        """The defect this repointing exists to prevent: guidance for a superseded server.

        The plugin pins no MCP server version, so every bootcamper is on the current server. Text
        describing 1.32.1's behavior can only mislead — here into recording a spurious exemption.
        """
        text = flat(PHASE2)
        self.assertRegex(
            text,
            r"(?i)Numbers are NOT in that list any more|numeric source value now enters the allowed set",
        )
        self.assertRegex(
            text,
            r"(?i)do \*\*not\*\* record a numeric-value exemption|do not record a numeric-value exemption",
        )
        self.assertNotRegex(
            text,
            r"(?i)where a source stores a value as a JSON \*\*number\*\* .{0,80}never enters the allowed set",
            "the superseded claim is back in shipped guidance",
        )

    def test_it_records_the_key_only_waiver(self):
        text = flat(PHASE2)
        self.assertIn('EXEMPT_KEYS = {"DATA_SOURCE", "RECORD_ID"}', text)
        self.assertRegex(text, r"(?i)a \*value\* cannot be exempted")

    def test_the_facts_carry_their_provenance(self):
        """INV-080: a Senzing/resource fact in shipped text says how it was established.

        Repointed 2026-07-29 from `server 1.32.1, 2026-07-28`: the claim was re-established
        against 1.32.2, and the provenance must move with the fact it attests.
        """
        self.assertRegex(flat(PHASE2), r"(?i)server \*\*1\.32\.2\*\*, \*\*2026-07-29\*\*")


class TheMappingIsNotPresumedWrong(unittest.TestCase):
    def test_it_says_not_to_conclude_the_mapping_is_wrong(self):
        self.assertRegex(flat(PHASE2), r"(?i)[Dd]o not conclude the mapping is wrong")

    def test_it_attributes_the_finding_to_the_checker(self):
        self.assertRegex(
            flat(PHASE2),
            r"(?i)limitation of the checker|checker limitation",
        )

    def test_phase_d_carries_the_same_caveat(self):
        """A violation list arriving unresolved must not read as a mapping defect.

        Repointed 2026-07-29: phase D carried its own copy of the string-only claim
        ("cannot express a non-string source value ... reports every emission of a numeric source
        value as a violation"). Two files stating one Senzing fact is two places for it to go
        stale, and both had.
        """
        text = flat(PHASE_D)
        self.assertRegex(text, r"(?i)harvests source \*values\* only")
        self.assertRegex(text, r"(?i)checker limitation and not a mapping error")
        self.assertRegex(
            text,
            r"(?i)Numeric source values used to fail this way and \*\*no longer do\*\*",
            "phase D must not send a bootcamper to record a numeric exemption either",
        )


class TheDataIsNeverAlteredToPassTheGate(unittest.TestCase):
    def test_altering_a_source_value_is_forbidden(self):
        self.assertRegex(flat(PHASE2), r"(?i)[Nn]ever change a source value to satisfy the tool")

    def test_it_says_why_the_workaround_does_not_even_work(self):
        """Repointed 2026-07-29 to the general reason, not the numeric example.

        The old assertion pinned "stringifying a numeric identifier still fails" — true through
        1.32.1, false now. The reason it was citing is unchanged for the causes that remain: the
        allowed set was built without the value, so no re-emission of it can be found there.
        """
        self.assertRegex(
            flat(PHASE2),
            r"(?i)the allowed set was built without it, under either emission",
        )


class TheFlowIsNotBlocked(unittest.TestCase):
    def test_the_guidance_says_to_proceed(self):
        self.assertRegex(flat(PHASE2), r"(?i)then \*\*proceed\*\*|and \*\*proceed\*\*")

    def test_it_forbids_an_iterate_forever_loop(self):
        self.assertRegex(
            flat(PHASE2),
            r"(?i)MUST NOT become an iterate-forever loop or a blocked module",
        )

    def test_it_cites_the_non_blocking_invariant(self):
        self.assertIn("INV-048", flat(PHASE2))


def no_fork_problems(text):
    """The no-fork paragraph (INV-173) names the checker and INV-080, read from ``flat`` text."""
    match = re.search(
        r"(?i)do not ship a patched copy of any of these scripts\.\*\*(.*?)(?=⛔|\*\*One "
        r"mechanism)", text)
    if match is None:
        return ["the no-fork rule (INV-173) is gone"]
    return [problem for needle, problem in (
        ("`sz_verbatim_check.py`", "the no-fork rule no longer names the verbatim checker"),
        ("INV-080", "the no-fork rule no longer cites INV-080"),
    ) if needle not in match.group(1)]


class TheResourceIsNotForked(unittest.TestCase):
    """INV-080: the checker comes from the MCP server; a fork would mask the fix."""

    def test_the_guidance_forbids_shipping_a_patched_copy(self):
        """#521 merged the checker's own no-fork paragraph into the all-scripts one.

        So the rule is read from that one paragraph, which must still name the checker and the
        invariant that delivers it (INV-080), whatever its wrap.
        """
        self.assertEqual([], no_fork_problems(flat(PHASE2)))

    def test_no_fork_negative_controls(self):
        text = flat(PHASE2)
        for name, mutant in {
            "rule dropped": text.replace("Do not ship a patched copy of any of these scripts.",
                                         "Patch these scripts as needed.", 1),
            "checker unnamed": text.replace("The numeric case in `sz_verbatim_check.py` is",
                                            "The numeric case is", 1),
        }.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], no_fork_problems(mutant))

    def test_the_plugin_ships_no_copy_of_the_checker(self):
        matches = list(PLUGIN.rglob("sz_verbatim_check*.py"))
        self.assertEqual([], matches, "the checker must come from the MCP server")

    def test_the_upstream_report_is_referenced(self):
        self.assertRegex(flat(PHASE2), r"(?i)reported 2026-07-28")


class TheEmissionChoiceIsSpecDriven(unittest.TestCase):
    """The Entity Specification decides the form, not what the checker can see."""

    def test_it_routes_the_type_question_to_the_specification(self):
        self.assertRegex(flat(PHASE2), ROUTE_DATA_MAPPING)

    def test_it_reports_that_the_spec_mandates_no_type(self):
        text = flat(PHASE2)
        self.assertRegex(text, r"(?i)does not\s+mandate a type")

    def test_it_does_not_assert_an_unverified_engine_behavior(self):
        """The reporter's live-engine finding is not repeatable here; it must not be
        stated as fact in shipped guidance (INV-080)."""
        text = flat(PHASE2)
        self.assertNotRegex(
            text,
            r"(?i)Senzing links disclosed relationships for both",
            "a live-engine observation must not be shipped as an assertion",
        )


#: Number words the reachings heading may use, so its count can be read back as an int.
NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}


def reachings_problems(text):
    """#521: the "known reachings" table is current, and its heading counts its rows.

    Read from ``flat`` text (whitespace collapsed) for the prose, and from the raw rows for the
    table, so a re-wrap of the heading paragraph does not move the check (INV-346).
    """
    flat_text = re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", text))
    head = re.search(r"\*\*One mechanism, (\w+) known reachings — recognize the (\w+) on sight",
                     flat_text)
    if head is None:
        return ["the reachings heading is gone"]
    start = text.index("| The emitted value is derived from…")
    end = text.index("Any value the mapper computes rather than copies", start)
    rows = [line for line in text[start:end].splitlines()
            if line.startswith("| ") and not line.startswith("| The emitted")]
    problems = []
    count = NUMBER_WORDS.get(head.group(1))
    if count != len(rows):
        problems.append("the heading says %s reachings and the table has %d rows"
                        % (head.group(1), len(rows)))
    if ordinal(head.group(2)) != (count or 0) + 1:
        problems.append("the heading's next reaching (%s) does not follow its count"
                        % head.group(2))
    table = "\n".join(rows)
    if re.search(r"(?i)JSON number|numeric", table):
        problems.append("the table still lists the numeric case, fixed in 1.32.2")
    if "**boolean**" not in table:
        problems.append("the table has no boolean row")
    if not re.search(r"`NAME_ORG` \*\*joined\*\* from parsed name fields", table):
        problems.append("the table has no joined-NAME_ORG row")
    if re.search(r"\| this entry \|", table):
        problems.append("a row points at 'this entry', which is not the entry it means")
    if not re.search(r"server 1\.\d+\.\d+, \d{4}-\d{2}-\d{2}\): every row's emitted value is "
                     r"reported", flat_text):
        problems.append("the reachings are not re-checked against a dated server version")
    if len(re.findall(r"(?i)do not ship a patched copy", flat_text)) != 1:
        problems.append("the no-fork rule is stated more than once (the merged paragraphs split)")
    return problems


def ordinal(word):
    return {"third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7}.get(word)


class TheReachingsTableIsCurrent(unittest.TestCase):
    """#521: no numeric row, boolean and joined-NAME_ORG rows, a heading that counts its rows."""

    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")

    def test_the_table(self):
        self.assertEqual([], reachings_problems(self.text))

    def test_negative_controls(self):
        text = self.text
        boolean_row = next(line for line in text.splitlines()
                           if line.startswith("| a source **boolean**"))
        mutants = {
            "numeric row restored": text.replace(
                boolean_row, boolean_row + "\n| a source value stored as a **JSON number** "
                "(non-string) | the non-string-values entry above |", 1),
            "boolean row dropped": text.replace(boolean_row + "\n", "", 1),
            "joined row dropped": text.replace("`NAME_ORG` **joined** from", "`NAME_ORG` from", 1),
            "self-reference restored": text.replace("| the field-name entry directly below |",
                                                    "| this entry |", 1),
            "count off by one": text.replace("One mechanism, four known reachings",
                                             "One mechanism, three known reachings", 1),
            "duplicate no-fork paragraph restored": text.replace(
                "**One mechanism,", "Do not ship a patched copy of `sz_verbatim_check.py`.\n\n"
                "**One mechanism,", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(text, mutant, "the mutation no longer applies")
                self.assertNotEqual([], reachings_problems(mutant))


if __name__ == "__main__":
    unittest.main()


class ThreeFurtherGateLimitationsAreDocumented(unittest.TestCase):
    """The gate rejects two mechanisms the same server prescribes, and crashes on CSV.

    Reported 2026-07-27 across four sources mapped end to end. All three are a *different* kind of
    limitation from the two harvesting gaps above them: here the harvester works and something else
    does not — the equality test's shape (`extract`), the key waiver's coverage (`REL_*`), and the
    input format (CSV). Keeping them in a separate block is why the harvesting section can still
    truthfully say "that is the whole of the harvesting limitation".

    These assert the *requirement*, not phrasing: that a mapper meeting one of the three finds it
    named, learns why, and is routed to INV-173's exemption path rather than to changing the data.
    """

    def setUp(self):
        self.text = flat(PHASE2)

    def test_the_extract_disposition_limitation_is_named(self):
        # The *claim*, not words near it. An earlier version asserted that "`extract`",
        # "allowed_values()" and "a.k.a." each appeared somewhere — all true even after the
        # sentence stating that extract output is rejected was deleted, because `extract` is a
        # documented disposition named elsewhere in this file and the rest of the paragraph
        # survived. Assert the statement that makes it a limitation.
        self.assertRegex(
            self.text, r"(?i)`extract` output is rejected",
            "the text never states that correct `extract` output fails the gate — without that "
            "claim the surrounding detail explains nothing",
        )
        self.assertRegex(self.text, r"(?i)allowed_values\(\)",
                         "the cause — whole value / delimiter segment / whitespace token — is absent")
        self.assertRegex(self.text, r"(?i)a\.k\.a\.",
                         "the worked repro that makes the failure concrete is absent")

    def test_the_relationship_scaffolding_limitation_is_named(self):
        for attribute in ("REL_ANCHOR_DOMAIN", "REL_POINTER_DOMAIN", "REL_POINTER_ROLE"):
            with self.subTest(attribute=attribute):
                self.assertIn(attribute, self.text)

    def test_it_says_which_relationship_attributes_pass(self):
        """`REL_*_KEY` passing is what identifies the cause as the waiver, not the harvester."""
        self.assertRegex(self.text, r"(?i)REL_ANCHOR_KEY.{0,80}REL_POINTER_KEY.{0,60}pass")

    def test_the_csv_limitation_is_named_with_its_error(self):
        self.assertRegex(self.text, r"(?i)load_jsonl")
        self.assertRegex(self.text, r"json\.decoder\.JSONDecodeError")

    def test_the_csv_limitation_appears_at_the_gate_presentation(self):
        """INV-183: the rule belongs where the artifact is produced, not one section away.

        A crash reads as environment trouble unless the step that runs the script says otherwise,
        and that step is where the reader is when it happens.
        """
        gate = self.text[:self.text.find("harvests source *values* only")]
        self.assertIn("JSONDecodeError", gate,
                      "the CSV crash is documented only in the limitations block, not at the gate")
        self.assertRegex(gate, r"(?i)tool limitation, not an environment problem")

    def test_all_three_are_dated_and_their_freshness_is_stated_per_limitation(self):
        """INV-080/INV-169: every entry carries a date, and none claims to be current
        behavior without saying how that was checked.

        ⚠️ **Rescoped 2026-08-14.** Until then this asserted the blanket caveat — that *none*
        of the three had been re-run — which made the guard hold the old freshness state in
        place after it expired: limitations 1 and 3 have since been re-confirmed against
        server 1.32.9 by reading the scripts the server delivers, so requiring the plugin to
        say they were never re-run would have required it to be wrong. That is the same
        failure this repo already recorded once, in
        `tests/test_engine_verification_and_senz2027.py`: a guard written to pin a caveat
        will pin it after the caveat stops being true, because nothing dates the premise.

        What remains required is the part that does not expire: the original observation
        date and SDK, and an explicit per-limitation freshness statement rather than a
        silent claim of currency.
        """
        self.assertRegex(self.text, r"(?i)First observed 2026-07-27",
                         "the original observation date must survive")
        self.assertRegex(self.text, r"(?i)4\.3\.3\.26191")
        self.assertRegex(
            self.text, r"(?i)Freshness, per limitation",
            "freshness must be stated per limitation, not as one blanket caveat")
        self.assertRegex(
            self.text, r"(?i)all \w+ are CURRENT behavior",
            "the freshness of each entry must be stated; limitation 2 was confirmed end to "
            "end on 2026-08-18, so pinning it as un-re-run would assert a disproved claim")
        self.assertRegex(
            self.text, r"(?i)does not depend on re-running a mapping",
            "a re-check must disclose what kind of check it was, or 'CONFIRMED CURRENT' "
            "overstates it")

    def test_the_prescriptions_carry_current_mcp_provenance(self):
        """What *was* re-verified: that the server still prescribes both mechanisms."""
        self.assertRegex(self.text, r"(?i)1\.32\.3")
        self.assertRegex(self.text, r"(?i)Feature: REL_ANCHOR",
                         "the Entity Specification sections that prescribe REL_* are not cited")

    def test_handling_routes_to_the_existing_exemption_path(self):
        self.assertRegex(self.text, r"(?i)Handling is the same for all \w+")
        self.assertIn("INV-173", self.text)

    def test_it_forbids_forking_the_scripts(self):
        self.assertRegex(self.text, r"(?i)Do not ship a patched copy",
                         "INV-173's no-fork rule must survive next to a workaround")

    def test_the_harvesting_section_no_longer_claims_to_be_exhaustive(self):
        """It said "they are the whole of this limitation", which three more entries falsify."""
        self.assertNotRegex(
            self.text, r"(?i)they are the whole of this limitation",
            "the harvesting block still claims to cover every limitation",
        )


class Step1ProfilerLimitationsAreDocumentedAtTheirSteps(unittest.TestCase):
    """Three `mapping_workflow` step-1 defects, each of which yields a wrong artifact silently.

    Reported 2026-07-27 across four sources on SDK 4.3.3.26191 and sent upstream 2026-07-31. They
    share a delivery channel and a failure signature — a plausible, well-formed output that is
    wrong — but they fire at *different* steps, so INV-183 puts each where it happens: the two
    profiler defects at `### 9. Profile`, the counter at `### 11. Map`. A limitations list one
    section away is unreachable at the moment it bites.

    These assert placement as well as presence, because presence alone was satisfied by the
    limitations block already in this file.
    """

    @staticmethod
    def _flatten(text):
        """Same normalization as `flat()`, applied to a slice rather than a whole file.

        These are wrapped prose sections, so a phrase assertion on raw text is really an
        assertion about where the line breaks fall — which is how the first version of
        `test_the_multi_file_output_collision_is_at_the_profile_step` failed on correct text.
        """
        return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", text))

    def setUp(self):
        raw = PHASE2.read_text(encoding="utf-8")
        self.profile = self._flatten(raw[raw.index("### 9. Profile"):raw.index("### 10. Plan")])
        self.mapping = self._flatten(raw[raw.index("### 11. Map"):raw.index("### 12.")])
        self.all = flat(PHASE2)

    def test_the_conditional_profile_report_filename_is_at_the_profile_step(self):
        """⚠️ **Rewritten 2026-08-23: this asserted a limitation that no longer exists.**

        It required the profile step to document a shared `-o` path, "only the second file's
        profile survives", and a concatenate-them workaround. On server 1.33.0 a multi-file
        `mapping_workflow(action='start')` emits one profiler invocation per input, each writing
        `profile_report_<stem>.md` — so the collision is fixed, and the workaround this test
        demanded would **reintroduce** it by collapsing the per-file reports back into one.

        A guard that pins a fixed upstream defect keeps the workaround shipped. What the profile
        step must document now is the conditional filename, which is what this asserts. See
        `specs/profile-report-filename-is-conditional-on-file-count.md`.
        """
        self.assertRegex(
            self.profile, r"(?i)filename depends on how many files you pass",
            "the profile step does not document that the report's name is conditional on the "
            "input count, which is the current behavior a reader needs")
        self.assertRegex(
            self.profile, r"profile_report_<stem>\.md",
            "the suffixed filename a multi-file start produces is not named at the step where "
            "the profiler runs")
        self.assertNotRegex(
            self.profile, r"(?i)only the second file's profile survives",
            "the retired collision claim is back at the profile step; on 1.33.0 the server "
            "writes one report per input")
        self.assertNotRegex(
            self.profile, r"(?i)profile_report_<stem>\.md`\) and\s+concatenate",
            "the concatenate workaround is back — it recreates the single-schema file the "
            "retired entry existed to prevent")

    def test_the_headerless_csv_limitation_is_at_the_profile_step(self):
        self.assertRegex(self.profile, r"(?i)headerless CSV")
        self.assertRegex(self.profile, r"(?i)one record disappears",
                         "the lost record is the part that matters and is not stated")
        self.assertRegex(self.profile, r"(?i)headered copy for profiling only",
                         "the workaround is not given")

    def test_the_sentinel_caveat_is_where_population_is_reported(self):
        """INV-128 one layer up: a sentinel is a value, so population != information."""
        self.assertRegex(self.profile, r"(?i)sentinel")
        self.assertRegex(self.profile, r"(?i)100% population")
        self.assertIn("INV-128", self.profile)

    def test_the_field_count_warning_is_at_the_mapping_step(self):
        self.assertRegex(self.mapping, r"(?i)field-count warning",
                         "the counter is not documented where step 3 fires it")
        self.assertRegex(self.mapping, r"(?i)wrong in both directions",
                         "the double error is what makes it unfixable by eye; state it")
        self.assertRegex(self.mapping, r"type_discriminator\.field_overrides",
                         "the excluded half of the miscount is not named")

    def test_the_warning_guidance_does_not_teach_ignoring_warnings(self):
        """A step whose other warnings are real must not be written off wholesale."""
        self.assertRegex(
            self.mapping, r"(?i)Do not\s+start ignoring this step's warnings generally",
            "the guidance must protect the step's other warnings",
        )

    def test_each_defect_is_marked_upstream_owned_and_dated(self):
        """So a later run can retire one, the way the numeric-value entry was retired."""
        for section, label in ((self.profile, "profile step"), (self.mapping, "mapping step")):
            with self.subTest(section=label):
                self.assertRegex(section, r"(?i)reported upstream 2026-07-31")
                self.assertRegex(
                    section, r"(?i)(not re-run|CONFIRMED CURRENT|CONFIRMED END TO END|"
                            r"is confirmed, not un-re-run)",
                    "must state the observation's freshness either way — un-re-run, or "
                    "confirmed with its date. Silence reads as a currency claim.")

    def test_the_prescriptions_carry_current_mcp_provenance(self):
        """What *was* re-verified: the schema still declares derived and type_discriminator."""
        self.assertRegex(self.mapping, r"(?i)1\.32\.3")
        self.assertRegex(self.mapping, r"(?i)derived_as")

    def test_the_field_count_block_leads_with_the_split_re_check(self):
        """Updated 2026-08-21: the counter is half fixed, and the block must say which half.

        Was "the warning no longer fires" (1.32.9, 2026-08-14) — true of the `derived` half and
        never tested on the other, because that walk had no per-record type field. A 1.33.0 run
        with a `type_discriminator` whose `field_overrides` declared a source field DID fire, so
        a flat "no longer fires" now understates it in the one configuration that reaches it.
        The block must lead with the split rather than with either half alone.
        """
        self.assertRegex(self.mapping, r"(?i)field-count warning is half fixed")
        self.assertRegex(self.mapping, r"(?i)1\.33\.0, 2026-08-21")
        self.assertRegex(
            self.mapping, r"(?i)derived=2 are synthesized and not source fields",
            "the server's own arithmetic is what proves the derived half is fixed rather "
            "than merely quiet — quote it")
        self.assertNotRegex(
            self.mapping,
            r"(?i)on \*\*every\*\* mapping that uses `derived` entries",
            "the falsified universal quantifier is back",
        )

    def test_the_type_discriminator_half_is_marked_confirmed(self):
        """Inverted 2026-08-21: the experiment the old text asked for was run.

        It named exactly what would settle the open half — *a source with a per-record
        entity-type field, mapped with a `type_discriminator` whose `field_overrides` declare
        at least one source field* — and that mapping fired the warning on server 1.33.0. The
        block must record the confirmation, and must not still call the half un-re-run.
        """
        self.assertRegex(self.mapping, r"(?i)is confirmed, not un-re-run")
        self.assertRegex(self.mapping, r"(?i)field_overrides` declare at least one\s*source field")
        self.assertNotRegex(
            self.mapping, r"(?i)Only the `derived` half was re-run",
            "the block still calls the type_discriminator half un-re-run, which a 1.33.0 "
            "run disproved")

    def test_the_disposition_counts_are_marked_server_derived(self):
        """So a later reader does not 'fix' the plugin by sending them."""
        self.assertRegex(
            self.mapping,
            r"(?i)Do not send `feature_count`, `payload_count` or `ignored_count`",
        )
        self.assertRegex(self.mapping, r"(?i)the server derives them")

    def test_the_retired_negative_is_replaced_by_the_affirmative(self):
        """Retired 2026-08-21: the server stopped being silent, so the negative expired.

        The marker recorded that a step-3 advance carrying three `derived` entries produced no
        field-count warning (1.32.9, 2026-08-14) — a correctly-owned absence negative at the
        time. On 1.33.0 the counter states the same fact affirmatively in its own warning text
        (`derived=N are synthesized and not source fields`), so there is no absence left to
        mark. A dated negative kept past the point the server answers it is exactly the shape
        `guards-pinning-a-dated-negative-outlive-it` was written about.
        """
        self.assertNotRegex(
            self.mapping, r"owner: the step-3 advance response is the only route",
            "the retired absence negative is back; the server now answers it affirmatively")
        self.assertRegex(
            self.mapping, r"(?i)derived=2 are synthesized and not source fields",
            "the affirmative that replaced the negative must be quoted, or the retirement "
            "leaves nothing asserting the derived half is handled correctly")

    def test_it_forbids_forking_the_profiler(self):
        self.assertRegex(self.profile, r"(?i)do not ship a patched profiler")
        self.assertIn("INV-173", self.profile)
