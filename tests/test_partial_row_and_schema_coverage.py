"""A lookup that succeeds but stops short, and the half-populated row it causes.

INV-115 sends the guide to `get_sdk_reference(topic='response_schemas')` before
parsing. For the graph methods that lookup **succeeds and is still not enough**:
verified 2026-07-26, `filter='find_network'` returns an entry documenting
`ENTITY_PATHS[]`, `ENTITIES[]` and `ENTITY_NETWORK_LINKS[]` — and nothing about
the fields inside a link element. `get_stats` returns an empty `data` array
outright (re-verified on MCP server 1.37.14, 2026-09-28; `get_version` and
`get_license`, the earlier examples, are now documented — INV-149's dated note,
#198). Neither case is a failed call, and a reader who treats it as one retries
instead of dumping the response.

The failure that follows is the nastier half. A reported session parsed link
endpoints under the `ENTITY_ID` / `RELATED_ENTITY_ID` names used elsewhere and
got `None` for both, while `MATCH_KEY` rendered correctly — a row that reads as a
relationship Senzing could not fully describe rather than as a parsing bug. An
all-blank row invites suspicion; a half-populated one does not, because the
fields that did populate signal the parse worked.

The endpoint keys were first confirmed by a live dump on SDK 4.3.3 (2026-07-28):
`MIN_ENTITY_ID` / `MAX_ENTITY_ID`, alongside `MATCH_LEVEL_CODE`, `MATCH_KEY`,
`ERRULE_CODE`, `IS_DISCLOSED`, `IS_AMBIGUOUS`.

**Those keys are now MCP-sourced, and this docstring said otherwise until
2026-07-29.** When first recorded they were dump-only, so the contract carried
them as an unverified caution rather than as names to code against — INV-080
forbids shipping an unverified Senzing fact as the name to code against, and this
repo has twice had to retract an over-generalized claim (`SZ_EXPORT_ALL_FLAGS does
not exist`, and phase D's export/`RELATED_ENTITIES` absolute — INV-169). The
contract and the assertions below were corrected in place under INV-149 once
`get_sdk_reference(topic='response_schemas', filter='find_network')` began
returning the element fields itself; re-confirmed on server 1.32.2, 2026-07-29,
which returns all seven. This prose lagged that correction and contradicted
`test_the_keys_are_no_longer_marked_unconfirmable` in the same file — the small,
ordinary way a stale premise survives its own fix.

What has NOT changed is the discipline the tests actually pin: run the lookup,
then dump the element before parsing. The keys tell a reader what to *expect*;
the dump still decides.

What these tests assert is therefore both halves: the *discipline* (dump the
element, treat a blank field as a wrong name, never present an unconfirmed name as
authoritative) and the *record* (the dump-marked key list, and the `JSON_DATA`
trap where the authoritative reference is itself what misleads).

Enforces **INV-191** (a dated provenance stamp is never advanced for a claim that pass did
not re-verify, and a claim this environment cannot re-check keeps its stamp and is recorded
as skipped rather than restamped), which names this file as its enforcer.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
CONTRACT = os.path.join(
    PLUGIN, "skills", "module-03b-truthset-visualization", "visualization-api-reference.md"
)
DISCOVER = os.path.join(
    PLUGIN, "skills", "module-07-query-visualize-discover", "phase2b-discover.md"
)
COLLECTION = os.path.join(PLUGIN, "skills", "module-04-data-collection", "SKILL.md")
SDK_SETUP = os.path.join(PLUGIN, "skills", "module-02-sdk-setup", "SKILL.md")
GROUND_RULES = os.path.join(PLUGIN, "skills", "bootcamp-onboarding", "ground-rules.md")


def flat(path):
    """Whitespace-collapsed text, with Markdown blockquote markers stripped.

    Most of the response-shape guidance lives inside a `>` blockquote, so a
    wrapped sentence carries a `>` at each line start. Collapsing whitespace
    alone leaves those markers mid-phrase ("Dump one raw link > element"), which
    fails a phrase assertion for a purely typographic reason.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


class AnEmptyOrShallowLookupIsExpectedNotAFailure(unittest.TestCase):

    def test_the_contract_still_requires_the_lookup_and_the_dump(self):
        """The rule survives the server's coverage improving.

        This test used to require the contract say the `find_network` entry carries "no
        element fields". That was true on 2026-07-26 and is false on 1.32.1 — the entry now
        documents them (INV-149, corrected in place 2026-07-29) — so the old assertion
        pinned a stale premise and made it load-bearing. What must hold is the discipline,
        not the observation: run the lookup, then dump before parsing.
        """
        text = flat(CONTRACT)
        self.assertRegex(text, r"(?i)Run the lookup anyway|Do the lookup anyway")
        self.assertRegex(text, r"(?i)dump one element and use what is actually there")

    def test_both_call_sites_send_the_reader_to_a_raw_dump(self):
        for path in (CONTRACT, DISCOVER):
            with self.subTest(file=os.path.basename(path)):
                self.assertRegex(
                    flat(path),
                    r"[Dd]ump one raw link element",
                    "the fallback must be stated where the lookup is performed",
                )

    def test_an_empty_result_is_not_treated_as_a_failed_call(self):
        """`COLLECTION` left this sweep in #198 (maintainer decision recorded on the issue).

        Its only match was Module 4's claim that `get_license` has no `response_schemas`
        entry, which the server now contradicts; that step now cites the documented
        `recordLimit` instead, which `test_the_license_step_cites_the_documented_field`
        pins.
        """
        for path in (CONTRACT, DISCOVER):
            with self.subTest(file=os.path.basename(path)):
                self.assertRegex(
                    flat(path),
                    r"not (an error to retry|a failed (call|lookup))|"
                    r"expected (outcome|result) for those|That is coverage, not a failed call",
                    "an absent entry is coverage, not an error — otherwise the reader "
                    "retries a call that will never return more",
                )

    def test_get_stats_is_the_empty_schema_example(self):
        """The example must be a method the server still serves no schema for (INV-149).

        Until #198 this pinned "`get_version` and `get_license`", which the server now
        documents (MCP server 1.37.14, 2026-09-28) — the test was holding a stale example
        in place.
        """
        text = flat(CONTRACT)
        self.assertRegex(text, r"filter='get_stats'\)` returns an empty `data` array")
        self.assertRegex(text, r"`get_stats\(\) -> str`; MCP server 1\.37\.14, 2026-09-28")

    def test_no_documented_method_is_named_as_empty_schema(self):
        """Neither retired example may survive as a current claim at any site that gave one."""
        stale = re.compile(
            r"`get_version` and `get_license` return an\s*empty"
            r"|`get_license` has \*\*no\*\* `response_schemas` entry"
            r"|filter='get_version'`? returned it alongside an \*empty\*")
        for path in (CONTRACT, COLLECTION, SDK_SETUP, GROUND_RULES):
            with self.subTest(file=os.path.relpath(path, REPO_ROOT)):
                self.assertIsNone(stale.search(flat(path)))

    def test_the_license_step_cites_the_documented_field(self):
        """Both license-measurement steps look the shape up, and keep the dump as fallback."""
        for path in (COLLECTION, SDK_SETUP):
            with self.subTest(file=os.path.relpath(path, REPO_ROOT)):
                text = flat(path)
                self.assertRegex(
                    text,
                    r"get_sdk_reference\(topic='response_schemas', filter='get_license'\)`"
                    r"[^.]*?documents `recordLimit` \(integer\)")
                self.assertRegex(
                    text, r"Only if `recordLimit` is absent from the saved[^.]*?\(INV-115\)")
                self.assertRegex(
                    text,
                    r"empty or shallow result from that lookup is coverage, not a failed call"
                    r"[^.]*?do not retry it[^.]*?\(INV-149\)",
                    "a step that requires the lookup states what an empty result means (INV-149)",
                )

    def test_the_ground_rules_signature_example_uses_get_stats(self):
        self.assertRegex(
            flat(GROUND_RULES),
            r"`topic='response_schemas', filter='get_stats'` returned it alongside an \*empty\*",
        )


class ThePartialRowRuleIsStated(unittest.TestCase):

    def test_both_call_sites_carry_the_partial_row_rule(self):
        for path in (CONTRACT, DISCOVER):
            with self.subTest(file=os.path.basename(path)):
                self.assertRegex(
                    flat(path),
                    r"partially populated row is a wrong field name|"
                    r"suspect the blank ones' names",
                    "INV-115 covers a blank field; the partial case needs saying because "
                    "the populated fields make the row look real",
                )

    def test_the_reason_is_recorded_not_just_the_rule(self):
        self.assertRegex(
            flat(CONTRACT),
            r"[Aa]n all-blank row invites suspicion; a half-populated one does not",
            "without the reason, a future edit trims this as redundant with INV-115",
        )


class NoUnverifiedFieldNameIsShipped(unittest.TestCase):
    """INV-080: the endpoint keys are a session observation, not a Senzing fact."""

    def test_the_endpoint_keys_carry_their_current_provenance(self):
        """They are MCP-confirmed now; the requirement is accurate provenance, not caution.

        INV-080 forbids shipping a Senzing fact without saying where it came from — it does
        not require understating what the server confirms. Once `response_schemas` returned
        these fields, "not MCP-confirmable" became the false claim.
        """
        text = flat(CONTRACT)
        self.assertIn("MIN_ENTITY_ID", text)
        self.assertRegex(text, r"(?i)now (documented by|MCP-confirmed)")
        self.assertRegex(text, r"1\.32\.2, 2026-07-30")
        self.assertNotRegex(
            text,
            r"(?i)(still )?not MCP-confirmable",
            "response_schemas documents these fields as of 1.32.1 — the negative claim is stale",
        )

    def test_the_wrong_pairing_is_still_named_as_the_trap(self):
        """The durable half: endpoints may not use the pairing you expect.

        Reworded 2026-07-29. The contract no longer frames the keys as "a warning about
        where to look" — `response_schemas` documents them, so they are names to use. What
        must survive is the trap itself: `ENTITY_ID` / `RELATED_ENTITY_ID` is the pairing a
        reader reaches for, and it yields two blank endpoints while `MATCH_KEY` renders
        (INV-148).
        """
        text = flat(CONTRACT)
        self.assertRegex(text, r"ENTITY_ID` / `RELATED_ENTITY_ID")
        self.assertRegex(text, r"(?i)yields `None` for \*\*both\*\* endpoints|blank")

    def test_the_reader_is_told_to_use_what_is_actually_there(self):
        self.assertRegex(flat(CONTRACT), r"use what is actually there")




class TheDumpConfirmedLinkKeysAreRecorded(unittest.TestCase):
    """Closing the criterion `network-link-fields-...` deliberately left open.

    That spec shipped the defense without the datum, because its implementation
    environment had no loaded engine, and said so: "someone with a loaded engine
    should dump one link element, confirm the keys, and promote the caution to a
    documented field list marked verified-when." That dump has now happened.
    """

    def test_the_element_key_set_is_documented(self):
        text = flat(CONTRACT)
        for key in (
            "MIN_ENTITY_ID",
            "MAX_ENTITY_ID",
            "MATCH_LEVEL_CODE",
            "MATCH_KEY",
            "ERRULE_CODE",
            "IS_DISCLOSED",
            "IS_AMBIGUOUS",
        ):
            with self.subTest(key=key):
                self.assertIn(key, text)

    def test_the_keys_carry_both_sources_with_dates(self):
        """Provenance must name what established the fact, and when — INV-080.

        Both are kept deliberately: `response_schemas` is now the authority, and the
        2026-07-28 dump on SDK 4.3.3 is corroboration. Dropping the dump would lose the
        record of how the names were found before the server documented them.
        """
        text = flat(CONTRACT)
        self.assertRegex(text, r"dump on SDK 4\.3\.3, 2026-07-28|dump-confirmed on SDK 4\.3\.3")
        self.assertRegex(text, r"MCP server 1\.32\.2, 2026-07-30")

    def test_the_keys_are_no_longer_marked_unconfirmable(self):
        """The negative claim went stale when the server started documenting them.

        Reversed on 2026-07-29 (dry run, phase 1). It previously asserted the contract keep
        saying "NOT in `response_schemas`" — which the live server contradicts, so the test
        was holding a false premise in place. INV-080 requires accurate provenance, not
        permanent caution.
        """
        self.assertNotRegex(
            flat(CONTRACT),
            r"NOT in `response_schemas`|not MCP-confirmable",
            "response_schemas documents these fields on 1.32.1",
        )

    def test_the_dump_requirement_survives_the_documentation(self):
        """Documented keys are an expectation to check, not a license to skip the dump."""
        self.assertRegex(
            flat(CONTRACT), r"(?i)dump one element and use what is actually there"
        )

    def test_a_mismatch_is_reported_rather_than_coded_around(self):
        self.assertRegex(flat(CONTRACT), r"the table is stale|report it rather than coding")

    def test_the_discover_step_points_at_the_recorded_keys(self):
        text = flat(DISCOVER)
        self.assertIn("MIN_ENTITY_ID", text)
        self.assertRegex(text, r"(?i)MCP-confirmed names rather than an unverified caution")
        self.assertRegex(text, r"(?i)Run the lookup and dump anyway")


class TheJsonDataFlagRequirementIsRecorded(unittest.TestCase):
    """`JSON_DATA` on an entity call needs its flag, and the default composite omits it.

    Through server 1.32.2 `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA` reported
    `applies_to: ["get_record"]`, and the contract recorded that as a trap: the get_entity
    schema listed `RECORDS[].JSON_DATA.*` paths no entity-family flag could produce. The server
    has since widened the flag's `applies_to` to the entity family (re-verified on MCP server
    1.37.14, 2026-09-28, #193), so the trap became a wrong fact that sent readers to a per-record
    `get_record` they did not need. What holds now, and is pinned here, is the flag requirement:
    OR the flag in, because `SZ_ENTITY_DEFAULT_FLAGS` omits it.
    """

    def test_the_contract_states_the_flag_requirement(self):
        text = flat(CONTRACT)
        self.assertRegex(
            text,
            r"`JSON_DATA` needs `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA` OR-ed in, and\s*"
            r"`SZ_ENTITY_DEFAULT_FLAGS` omits it",
            "the flag requirement must be stated where a reader looks up response shapes",
        )

    def test_the_contract_sends_the_reader_to_applies_to(self):
        self.assertRegex(
            flat(CONTRACT),
            r"filter='SZ_ENTITY_INCLUDE_RECORD_JSON_DATA'\)` lists the entity family in that "
            r"flag's `applies_to`",
            "the contract must name the route that owns the fact rather than restate a list",
        )

    def test_a_blank_json_data_is_read_as_a_missing_flag(self):
        self.assertRegex(
            flat(CONTRACT),
            r"a blank `JSON_DATA` means the flag is missing, not that the route is\s*wrong",
        )

    def test_both_single_call_routes_are_named_with_their_flags(self):
        text = flat(CONTRACT)
        self.assertRegex(text, r"RECORDS\[\]\.JSON_DATA")
        self.assertRegex(text, r"RECORDS\[\]\.FEATURES\.<TYPE>\[\]\.ATTRIBUTES")
        self.assertIn("SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS", text)
        self.assertRegex(text, r"one entity-family call is enough")

    def test_the_alternative_is_not_claimed_to_be_identical_to_json_data(self):
        """ATTRIBUTES are mapped feature values; JSON_DATA is the raw loaded record."""
        self.assertRegex(
            flat(CONTRACT),
            r"mapped\*\* attributes per feature, not the raw record as loaded",
        )

    def test_neither_file_claims_json_data_is_get_record_only(self):
        """The retired fact must not survive at either site that stated it."""
        stale = re.compile(
            r"`JSON_DATA` is `get_record`-only|is `get_record`-only, so those paths"
            r"|the only place `JSON_DATA` is obtainable|no entity-family flag produces them"
            r"|one extra SDK call \*\*per record\*\*|one extra call per record")
        for path in (CONTRACT, DISCOVER):
            with self.subTest(path=os.path.relpath(path, REPO_ROOT)):
                self.assertIsNone(stale.search(flat(path)))

    def test_the_discover_step_carries_the_flag_requirement(self):
        text = flat(DISCOVER)
        self.assertRegex(
            text,
            r"`RECORDS\[\]\.JSON_DATA` needs `SZ_ENTITY_INCLUDE_RECORD_JSON_DATA`, which\s*"
            r"`SZ_ENTITY_DEFAULT_FLAGS` omits",
        )
        self.assertRegex(text, r"the fix\s*is the flag, not a switch to `get_record`")
        self.assertIn("SZ_ENTITY_INCLUDE_RECORD_FEATURE_DETAILS", text)


class TheTwoGraphMethodsAreNotInterchangeable(unittest.TestCase):
    """The link array is the one key that differs — and the only one a shared parser misses.

    Verified on MCP server 1.32.2, docs indexed 2026-07-29 11:11 UTC, 2026-07-31:
    `get_sdk_reference(topic='response_schemas', filter='find_path')` returns
    `ENTITY_PATH_LINKS[]` where `filter='find_network'` returns
    `ENTITY_NETWORK_LINKS[]`. **Every other key in the two documents is the same** —
    `ENTITIES[]`, `ENTITY_PATHS[]`, and the same seven link-element fields — so the
    array name is the single difference, and it is the one a reader is least likely
    to look for after carrying working code across.

    `find_network` returning `ENTITY_PATHS[]` is what makes it bite: the network
    response contains the word PATH, which reads as license to expect
    `ENTITY_PATH_LINKS[]` in it.

    The reported failure was the half-populated row again (INV-148): a valid 2-degree
    path whose entity names rendered while every edge printed
    `(link detail not returned)`. Both the flags and the array name were wrong at
    once, and nothing raised.

    Two files are pinned because step 4d delegates its key list to the reference:
    the reference's "Confirmed paths" table listed `find_path_*` as
    `ENTITY_PATHS[]`, `ENTITIES[]` and omitted the links array altogether, so a
    reader who followed the pointer got confirmation that the array they needed did
    not exist.
    """

    def test_step_4d_names_both_link_arrays(self):
        """Neither name may be lost — the divergence is unstatable with only one."""
        text = flat(DISCOVER)
        for array in ("ENTITY_PATH_LINKS[]", "ENTITY_NETWORK_LINKS[]"):
            with self.subTest(array=array):
                self.assertIn(
                    array,
                    text,
                    "step 4d teaches find_path and find_network minutes apart; naming "
                    "only one array name is what lets a parser be carried across",
                )

    def test_step_4d_says_which_method_returns_which(self):
        """Both names present is not enough — a reader needs the pairing."""
        text = flat(DISCOVER)
        self.assertRegex(
            text,
            r"`find_path`[^.]*?`ENTITY_PATH_LINKS\[\]`",
            "the array must be attributed to find_path, not merely mentioned nearby",
        )
        self.assertRegex(text, r"`find_network` returns them under[^.]*?ENTITY_NETWORK_LINKS")

    def test_step_4d_states_the_element_fields_are_identical(self):
        """The reason the array name is the *only* thing a shared parser misses.

        Without this, "the names differ" reads as "the responses differ", and a
        reader reasonably re-derives the whole element shape instead of changing one
        key — or assumes the element fields differ too and distrusts the reference.
        """
        self.assertRegex(
            flat(DISCOVER),
            r"(?i)both link elements carry the same seven\s+fields|"
            r"element fields are identical",
        )

    def test_step_4d_states_the_matching_info_flags_are_not_shared(self):
        """Flags were the other half of the reported failure, not a footnote."""
        text = flat(DISCOVER)
        self.assertIn("SZ_FIND_NETWORK_INCLUDE_MATCHING_INFO", text)
        self.assertIn("SZ_FIND_PATH_INCLUDE_MATCHING_INFO", text)
        self.assertRegex(
            text,
            r"(?i)paired, not shared",
            "naming both flags without saying they are exclusive leaves a reader free "
            "to OR in whichever one they already have",
        )

    def test_step_4d_states_the_consequence(self):
        """A rule with no named symptom is not recognizable in the wild (INV-148)."""
        self.assertRegex(
            flat(DISCOVER),
            r"(?i)neither the flags nor the parser can be carried",
        )

    def test_the_reference_table_gives_find_path_its_links_array(self):
        """The pointer's destination must not confirm the opposite of the rule."""
        text = flat(CONTRACT)
        self.assertRegex(
            text,
            r"`find_path_\*` \| `ENTITY_PATHS\[\]`, `ENTITIES\[\]`,[^|]*ENTITY_PATH_LINKS",
            "the find_path row of the Confirmed paths table must name the links array; "
            "omitting it reads as confirmation that find_path has no such array",
        )

    def test_the_existing_endpoint_key_warning_survives(self):
        """This spec extended that warning; it must not have replaced it."""
        text = flat(DISCOVER)
        self.assertIn("MIN_ENTITY_ID", text)
        self.assertRegex(text, r"ENTITY_ID` / `RELATED_ENTITY_ID")
        self.assertRegex(text, r"(?i)Run the lookup and dump anyway")

    def test_the_scan_is_not_vacuous(self):
        """Both pinned files must exist and be non-trivial, or every assertion above
        passes against nothing."""
        for path in (DISCOVER, CONTRACT):
            with self.subTest(file=os.path.basename(path)):
                self.assertTrue(os.path.isfile(path))
                self.assertGreater(len(flat(path)), 2000)


if __name__ == "__main__":
    unittest.main()
