"""A negative marker's rationale must not rest on a count, or on an enumerated name-list.

MCP-NEGATIVE-SCAN: ignore-file — the marker strings below are synthetic scratch-tree
fixtures for the reporter, not claims about any server. They are written as concatenated
Python literals, so the token lands on a line whose `owner:` clause is on the next one, and
the scanner correctly reads that as a MALFORMED marker — which is how this was found, by
the very guard the fixtures exercise. Same route as `tests/test_coverage_reports.py`.

An ``MCP-NEGATIVE`` marker has two halves that age at different rates: the **claim**
("tool X does not contain Y"), which `/dry-run` phase 1 re-asks, and the **rationale** --
the ``owner:`` clause plus the detail saying why the claim is the answer rather than a
miss. Nothing re-asks the rationale, so it can quietly stop describing the response while
the claim above it stays true and the date certifies the whole comment as checked.

On 2026-08-31 all 25 DUE claims still held and **three rationales did not reproduce**. Two
of the three had pinned a **count** -- "all four hits are …" (ten hits by then) and an
exhaustive field list (a field had since been added). A count is never the discriminating
fact; it is a stand-in for one. "No field names a binding type" says what the census was
standing in for, and does not expire when the index is rebuilt.

⚠️ This guard asserts the DETECTOR discriminates, not merely that it matches something:
census fixtures must be flagged AND property-shaped fixtures must not. A detector that
flags everything would satisfy a one-sided test while making the report useless.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import ast
import importlib.util
import io
import re
import shutil
import subprocess
import tokenize
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / ".claude" / "skills" / "dry-run" / "coverage_reports.py"


def load_reports():
    spec = importlib.util.spec_from_file_location("coverage_reports", REPORTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(claim, owner="whatever route (routing negative)"):
    """A find_negatives()-shaped row: (key, version, date, claim, owner, path, lineno)."""
    return ((1, 35, 3), "1.35.3", "2026-09-01", claim, owner, "fixture.md", 1)


#: ⛔ Every fixture this module presents as a QUOTE goes through `quoted()`, and nowhere else.
#: Until #151 the census fixtures were paraphrases described as shipped text -- "all six hits"
#: stood in for a marker that said "every hit" -- so the test certified the paraphrase while
#: the marker it was written about was invisible to the detector. `FixtureProvenanceIsChecked`
#: below holds the line: a quote with no commit must be in `find_negatives()` output today; a
#: quote with a commit must be on the named line of the named file at that commit; and a test
#: whose docstring or comments call its fixture verbatim or shipped must take it from here.
QUOTES = []


def quoted(text, source, commit=None):
    """Return `text`, registered as a word-for-word quote of `source` (``path:line``).

    ``commit=None`` -- the text ships NOW, and must be a substring of some marker's parsed
    claim or owner. ``commit="<sha>"`` -- HISTORICAL: copied from that line as it stood at that
    commit, which is what a fixture must say once the marker it quotes has been rewritten.
    """
    QUOTES.append((text, source, commit))
    return text


_SKILL_02 = "plugins/senzing-bootcamp/skills/module-02-sdk-setup/SKILL.md"
#: ⚠️ (INV-219) Every quote below is pinned HISTORICAL, including the ones whose marker is
#: unchanged today. A quote with no commit would make `test_every_live_quote_is_in_a_shipped_marker`
#: fail whoever next corrects that marker's claim when the server moves -- a test pinning the
#: verbatim wording of a claim about an MCP tool's content. Resolved through git at the commit,
#: the fixture still cannot be a paraphrase, and a marker correction fails nothing here.
#: `_BASE` is the `main` commit #151 branched from; each quoted line is unchanged there.
_BASE = "d3d5e5e"

#: The pre-#151 rationales of the two markers the widened census branch caught. Both are
#: positive universals over the result set, and `:387`'s was falsified on server 1.37.13,
#: 2026-09-24 by hits 8 and 10 of the query it names, while its claim still held.
PRE_151_SZBUILDVERSION = quoted(
    "no indexed document gives that file's path on any platform; every hit is a "
    "version-READING example or a build/packaging document, none stating where the file lives",
    _SKILL_02 + ":127", commit="bc4be70",
)
PRE_151_UPGRADE = quoted(
    "no 4.x-to-4.y update procedure anywhere; every hit is V3-to-V4 migration material "
    "(sz_dbupgrade, sz_configupgrade, breaking-changes, Migration.md) and the topic list "
    "carries no upgrade entry",
    _SKILL_02 + ":387", commit="bc4be70",
)
#: The enumeration that drifted undetected on 2026-09-02, as it stood before the restamp
#: corrected it. The owner clause in full -- the pre-#151 fixture cut it off mid-sentence.
PRE_RESTAMP_MAPPING_IDENTIFIERS = quoted(
    "search_docs over the Entity Specification IS the route that would carry such a "
    "precedence rule, and it returned the *Payload attributes (optional)* and "
    "*Mapping identifiers* sections, which establish that payload and registered features "
    "are distinct categories and that choosing between them is a mapping decision, but state "
    "no precedence for a colliding root-level key (absence negative)",
    "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase2-data-mapping.md:719",
    commit="d5826b5",
)
BOTH_DOCUMENT_AS_A_VERB = quoted(
    "IS the route that would carry an update command for each package manager, and both "
    "document installing only (absence negative)",
    _SKILL_02 + ":225", commit=_BASE,
)
BREW_COMMAND_LIST = quoted(
    "no brew outdated, brew info or brew upgrade anywhere in the response; the brew "
    "commands it does carry are tap, trust, install --cask, uninstall --cask, untap, "
    "install/link libpq, and --prefix",
    _SKILL_02 + ":252", commit=_BASE,
)
SCOOP_COMMAND_LIST = quoted(
    "no scoop status, scoop info or scoop update anywhere in the response; the scoop "
    "commands it does carry are bucket add, install, and config (for the EULA variable)",
    _SKILL_02 + ":278", commit=_BASE,
)
SNIPPET_FIELD_LIST = quoted(
    "its snippets[] carry file_path, source_url, repo, raw_url, size_bytes and "
    "line_count with no content field at all",
    "plugins/senzing-bootcamp/skills/module-03-system-verification/phase1-verification.md:251",
    commit=_BASE,
)
#: Quantifiers that ship today over something OTHER than the result set (#151's must-not-flag).
EVERY_BINDING = quoted(
    "returns flags as Set<SzFlag> for Java plus a warning naming every binding that differs",
    "plugins/senzing-bootcamp/skills/module-07-query-visualize-discover/"
    "phase1-query-visualize.md:228", commit=_BASE,
)
EACH_TOOLS_SCHEMA = quoted(
    "each tool's declared schema as the server advertises it in the tool manifest is the "
    "authority on what that tool accepts",
    "plugins/senzing-bootcamp/skills/bootcamp-onboarding/ground-rules.md:294", commit=_BASE,
)
NONE_OF_THE_CODES = quoted(
    "none of the three supplied codes appears anywhere in the response",
    "plugins/senzing-bootcamp/skills/module-06-data-processing/phaseA-build-loading.md:354",
    commit=_BASE,
)


class TheDetectorFlagsACensus(unittest.TestCase):
    """Each census SHAPE is pinned here -- a numeral, `both`, and a positive universal.

    ⚠️ The first test's fixtures are paraphrases, and say so: they pin shapes, not text. The
    pre-#151 docstring here claimed otherwise, and "all six hits" passed for a marker that
    read "every hit" -- a shape the detector could not see. Text copied from a marker lives
    in the `quoted()` registry, which `FixtureProvenanceIsChecked` resolves.
    """

    def setUp(self):
        self.reports = load_reports()

    def test_the_historical_phrasings_are_flagged(self):
        paraphrases = [
            "no indexed document gives that file's path; all four hits are get_version() examples",
            "no 4.x-to-4.y procedure anywhere; all six hits are V3-to-V4",
            "returns no globalization content at all, all five hits being repo template files",
            "the corpus returns 10 hits and none of them names the file",
            "both results are SDK examples",
        ]
        for claim in paraphrases:
            with self.subTest(claim=claim[:48]):
                self.assertTrue(
                    self.reports.find_census_rationales([row(claim)]),
                    "A rationale pinning a count must be flagged for re-description. This is "
                    "the shape that stopped reproducing twice on 2026-08-31 while the claim "
                    "beside it stayed true.",
                )

    def test_a_census_in_the_owner_clause_is_flagged_too(self):
        """The owner clause is a rationale as well, and is the load-bearing half."""
        self.assertTrue(
            self.reports.find_census_rationales(
                [row("no such field", owner="the parameters topic, whose three rows all differ")]
            ),
            "A count in the `owner:` clause must be flagged. The owner clause is what a later "
            "reader acts on when deciding whether a routing conclusion still stands, so a stale "
            "census there costs more than one in the claim.",
        )

    def test_the_universal_rationales_that_shipped_are_flagged(self):
        """`module-02-sdk-setup/SKILL.md:127` and `:387`, verbatim as of commit bc4be70.

        ⛔ Both passed the pre-#151 detector, which exempted `every` as a property word. On
        server 1.37.13, 2026-09-24 `:387`'s query returned ten hits and two of them (the Python
        SDK's `szengine` reference and a tRPC client file) were not V3-to-V4 material, so
        "every hit is V3-to-V4" had expired exactly as "all six hits" had before it.
        """
        for claim in (PRE_151_SZBUILDVERSION, PRE_151_UPGRADE):
            with self.subTest(claim=claim[:48]):
                self.assertEqual(
                    ["every hit"],
                    [phrase for _p, _l, phrase in self.reports.find_census_rationales(
                        [row(claim)])],
                    "A positive universal over the result set must be flagged as a census: one "
                    "new hit that is not X falsifies 'every hit is X', the same event that "
                    "falsifies a count. If this is empty, CENSUS_SHAPED lost its universal branch.",
                )

    def test_every_positive_universal_over_the_results_is_flagged(self):
        """#151's must-flag list: a positive quantifier, then a result noun."""
        for claim in (
            "every hit is a code example",
            "each result is a migration guide",
            "all hits are V3-to-V4 material",
            "all the hits are repository templates",
            "all of the results name the V3 API",
            "every one of the hits is a FAQ entry",
            "every document is a release note",
            "every match is a snippet",
            "each entry is an SDK method",
            "all of the documents describe V3",
        ):
            with self.subTest(claim=claim):
                self.assertTrue(
                    self.reports.find_census_rationales([row(claim)]),
                    "A universal over what came back expires the moment the index returns "
                    "something new. It must be flagged the same way a numeral is.",
                )


class TheDetectorLeavesAPropertyAlone(unittest.TestCase):
    """⚠️ The other half of the discrimination -- a detector that flags everything is noise.

    INV-282's lesson applied to this matcher: every construction it must NOT flag is
    pinned beside the ones it must, so a later widening that starts flagging correct
    rationales fails here rather than being absorbed as a louder report.
    """

    def setUp(self):
        self.reports = load_reports()

    def test_property_shaped_rationales_are_not_flagged(self):
        # ⚠️ The pre-#151 list carried "every hit is a version-READING example or a build
        # document, …" here, as a property. It is a census, and its source marker is now pinned
        # as must-flag in `TheDetectorFlagsACensus` (`PRE_151_SZBUILDVERSION`).
        good = [
            "no field on any returned row names a binding or its argument types",
            "the same document carries the renamed trio at WHY_RESULTS[].MATCH_INFO",
            "returns it, as \"Address matching examples > CJK+English cross-script matching\"",
            "the topic list carries no upgrade entry",
            "the response is byte-identical with and without the language argument",
        ]
        for claim in good:
            with self.subTest(claim=claim[:48]):
                self.assertFalse(
                    self.reports.find_census_rationales([row(claim)]),
                    "A rationale stating a discriminating PROPERTY must not be flagged. "
                    "Flagging correct prose trains the reader to skip the report, which "
                    "costs more than the census it was meant to catch.",
                )

    def test_document_as_a_verb_is_not_a_census(self):
        """A shipped marker says "both document installing only …" -- two routes, one verb.

        ⚠️ Found by negative control, not by review: the detector's first version flagged
        `module-02-sdk-setup/SKILL.md:225` (then `:207`) because `both\\s+documents?` matched
        a verb. The same verb/noun collision had to be corrected in two other guards this
        session, so it is pinned here rather than left to the next author to rediscover.
        """
        self.assertFalse(
            self.reports.find_census_rationales(
                [row("no such command", owner=BOTH_DOCUMENT_AS_A_VERB)]
            ),
            "`document` is a verb here. A matcher that reads it as a result noun flags "
            "correct prose, and a report that cries wolf is one nobody opens.",
        )

    def test_a_floating_quantifier_before_a_verb_is_not_a_census(self):
        """`all` and `each` can float before a verb exactly as `both` does (#151).

        The universal branch reads `all …` only before a PLURAL noun and leaves `document`
        and `match` out after `each`, so the verb reading never matches.
        """
        for claim in ("the routes all document it", "the hits all match the query",
                      "they each document it", "they each match it"):
            with self.subTest(claim=claim):
                self.assertFalse(
                    self.reports.find_census_rationales([row(claim)]),
                    "A verb after a floating quantifier is not a result noun. Reading it as "
                    "one flags correct prose.",
                )

    def test_a_quantifier_over_something_else_is_not_a_census(self):
        """#151's must-not-flag list: three shipped at d3d5e5e, verbatim, over no result set.

        A binding, a tool's schema and a set of supplied codes are not what the index
        returned, so a new hit cannot falsify them.
        """
        for text in (EVERY_BINDING, EACH_TOOLS_SCHEMA, NONE_OF_THE_CODES):
            with self.subTest(text=text[:48]):
                self.assertFalse(
                    self.reports.find_census_rationales([row(text)]),
                    "The census branch is scoped to a quantifier over RESULT nouns. Flagging a "
                    "universal over bindings, schemas or supplied codes flags correct prose.",
                )

    def test_a_negative_universal_over_the_results_is_not_a_census(self):
        """Out of scope by decision, and pinned so a later widening cannot absorb it quietly.

        "none of the hits names …" is the shape of an absence CLAIM, which phase 1 re-asks.
        Flagging it would flag claims rather than rationales.
        """
        for claim in ("none of the hits names the file",
                      "no hit carries a 4.x-to-4.y procedure",
                      "its top hits are all Guide sections"):
            with self.subTest(claim=claim):
                self.assertFalse(
                    self.reports.find_census_rationales([row(claim)]),
                    "Negative universals and ranking scope are outside #151's census branch; "
                    "widening to them is a separate decision, not a side effect.",
                )

    def test_a_version_number_is_not_a_census(self):
        """`server 1.35.3` and `SDK 4.4` carry digits and enumerate nothing."""
        self.assertFalse(
            self.reports.find_census_rationales(
                [row("no 4.x-to-4.y update procedure exists in the 4 corpus")]
            ),
            "A version number is not an enumeration of results. Matching bare digits would "
            "flag every marker, since each carries a server version by construction.",
        )


class NoShippedMarkerPinsACount(unittest.TestCase):
    """The state this change establishes, asserted against the tree rather than a fixture.

    ⚠️ Scoped to ``plugins/`` deliberately. ``specs/DECLINED.md`` also carries a marker,
    and it is a RECORD of a decision already taken -- rewriting its evidence is the
    maintainer's call, not a guard's. The report still lists it; this test does not.
    """

    def test_no_marker_under_plugins_rests_on_a_count(self):
        reports = load_reports()
        found = [r for r in reports.find_negatives(str(REPO)) if r[5].startswith("plugins")]
        self.assertTrue(found, "No markers found under plugins/ -- has the scan broken?")
        flagged = reports.find_census_rationales(found)
        self.assertEqual(
            [], flagged,
            "A shipped marker's rationale pins a count. Re-ask the owning route and replace "
            "the census with the property it stands in for -- do NOT simply re-date it, which "
            "certifies text nobody re-read.",
        )


class TheEnumerationDetectorFlagsANameList(unittest.TestCase):
    """The shape a numeral cannot express, and which `find_census_rationales` cannot see.

    An enumerated name-list expires for exactly the reason a count does -- a rename, a drop
    or an addition falsifies it server-side, silently, because phase 1 re-asks the CLAIM and
    never the rationale. It was named as an observed drift cause in the detector's own comment
    on 2026-08-31 and left unimplemented; on 2026-09-02 it drifted again undetected.
    """

    def setUp(self):
        self.reports = load_reports()

    def test_the_shipped_drifted_phrasing_is_flagged(self):
        """`phase2-data-mapping.md:719`, verbatim as of commit d5826b5 -- historical text.

        The instance that went undetected. On server 1.36.0, 2026-09-02 that route returns
        *Payload attributes (optional)*, *Attributes for the record key* and *Attribute
        reference*. There is no *Mapping identifiers* section in the response at all. The
        restamp in the next commit (97c4d0b) rewrote this owner clause, so it is quoted from
        the commit before it; the pre-#151 fixture here also cut it off mid-sentence.
        """
        self.assertTrue(
            self.reports.find_enumeration_rationales(
                [row("no such rule", owner=PRE_RESTAMP_MAPPING_IDENTIFIERS)]),
            "A rationale naming the sections the route returned must be flagged. This exact "
            "text cited a section the server does not return, while the claim above it stayed "
            "true and the date certified the whole comment as checked.",
        )

    def test_the_property_shaped_rewrite_is_not_flagged(self):
        """What the correction must look like -- and why re-listing is not a fix.

        Replacing one section name with the currently-returned three would leave the rationale
        flagged, correctly: the next server-side rename breaks it again. The discriminating
        property is what the enumeration was standing in for.
        """
        owner = (
            "search_docs over the Entity Specification IS the route that would carry such a "
            "precedence rule; its payload and feature-attribute sections establish that the "
            "two are distinct categories and that choosing between them is a mapping "
            "decision, but none states a precedence for a colliding root-level key "
            "(absence negative)"
        )
        self.assertFalse(
            self.reports.find_enumeration_rationales([row("no such rule", owner=owner)]),
            "A rationale stating the PROPERTY the list stood in for must not be flagged -- "
            "otherwise the report gives the fixer nowhere to land.",
        )

    def test_a_corrected_enumeration_is_still_flagged(self):
        """Re-listing the current sections is a re-date in disguise, and must still report."""
        owner = (
            "search_docs IS the route, and it returned the *Payload attributes (optional)*, "
            "*Attributes for the record key* and *Attribute reference* sections "
            "(absence negative)"
        )
        self.assertTrue(
            self.reports.find_enumeration_rationales([row("no such rule", owner=owner)]),
            "Swapping today's section names in keeps the liability: the rationale is still "
            "falsified by the next rename. The report must not go quiet on it.",
        )

    def test_the_noun_may_govern_from_either_side(self):
        for owner in (
            "the response carries the fields `file_path` and `raw_url` (routing negative)",
            "it returned the *Alpha* and *Beta* sections (absence negative)",
        ):
            with self.subTest(owner=owner[:40]):
                self.assertTrue(
                    self.reports.find_enumeration_rationales([row("x", owner=owner)]),
                    "Both phrasings ship; a matcher that reads only one direction misses half.",
                )


class TheEnumerationDetectorLeavesLegitimateListsAlone(unittest.TestCase):
    """⛔ Three of the four enumerations in the corpus on 2026-09-02 were LEGITIMATE.

    An exhaustive list IS the discriminating fact of an absence claim -- "no `brew upgrade`
    anywhere; what it does carry is ..." -- so this half of the discrimination carries more
    weight here than for the count matcher. INV-282's lesson: every construction the detector
    must NOT flag is pinned beside the ones it must, so a later widening fails here rather
    than being absorbed as a louder report.
    """

    def setUp(self):
        self.reports = load_reports()

    def test_a_property_with_examples_is_not_flagged(self):
        """`module-02-sdk-setup/SKILL.md:387`, verbatim as of commit bc4be70 -- historical text.

        The spec for this detector named it must-not-flag, and for THIS detector it still is.
        ⚠️ It has the verb, and a coordinated snake_case run, and an element noun in the
        clause -- so a presence-in-clause test flags it, which the first implementation did.
        `entry` governs `upgrade`, in a different conjunct; the run is examples under the
        property word `material`. That is why `_governing_noun` tests the gap for a
        coordinator rather than only its width.

        ⛔ It is NOT a durable property, which this docstring used to say: "every hit is …" is a
        census, falsified on 2026-09-24 by two new hits (#151). The census detector claims it,
        asserted below, so the two reporters' division of this shape is explicit.
        """
        self.assertFalse(
            self.reports.find_enumeration_rationales([row(PRE_151_UPGRADE)]),
            "The run is examples under a property word, not a list of response elements. The "
            "enumeration report must not claim it -- it belongs under the census label.",
        )
        self.assertTrue(
            self.reports.find_census_rationales([row(PRE_151_UPGRADE)]),
            "The census report must claim 'every hit is V3-to-V4 material': a positive "
            "universal over the result set expires when one new hit is not V3-to-V4.",
        )

    def test_the_exhaustive_command_lists_are_not_flagged(self):
        """`SKILL.md:252` (brew) and `:278` (scoop), verbatim as of d3d5e5e -- the legitimate use.

        The list is the discriminating fact of the absence: no version-management command
        anywhere, and here is what the response does carry instead. Both reproduced exactly
        on server 1.36.0, 2026-09-02.
        """
        for claim in (BREW_COMMAND_LIST, SCOOP_COMMAND_LIST):
            with self.subTest(claim=claim[:48]):
                self.assertFalse(
                    self.reports.find_enumeration_rationales([row(claim)]),
                    "An exhaustive list of bare command words is the fact itself. Flagging "
                    "it trains the reader to skip the report.",
                )

    def test_a_trailing_field_noun_is_not_treated_as_governing(self):
        """`phase1-verification.md:251`, verbatim as of d3d5e5e -- the detector's known blind spot.

        ⚠️ This one is honestly uncomfortable: it IS an exhaustive field list, the shape the
        comment names as a 2026-08-31 drift cause, and it reproduced exactly on 1.36.0. It is
        left unflagged because `field` trails in a separate conjunct, the same structure that
        keeps `:387` out. The trade is stated in `find_enumeration_rationales`' docstring
        rather than left for a reader to infer from silence.
        """
        self.assertFalse(
            self.reports.find_enumeration_rationales([row(SNIPPET_FIELD_LIST)]),
            "Pinned as the CURRENT behavior, not as an endorsement. If this phrasing drifts, "
            "widen _governing_noun -- do not drop the coordinator test.",
        )

    def test_a_tool_calls_own_parameters_are_not_an_enumeration(self):
        """⚠️ The claim half INCLUDES the invocation, so this would flag nearly every marker.

        `search_docs(query='...', category='data_mapping')` hands the matcher two snake_case
        tokens and, with a `section` noun anywhere nearby, a hit -- for free, on every marker
        that happens to be a `search_docs` negative. Found while designing the matcher; the
        report would have been useless on its first run.
        """
        claim = (
            "search_docs(query='payload attribute precedence', category='data_mapping') "
            "— no indexed section states what happens at the record root"
        )
        self.assertFalse(
            self.reports.find_enumeration_rationales([row(claim)]),
            "A call's own parameters enumerate nothing about the response.",
        )

    def test_all_caps_prose_is_not_a_pair_of_named_elements(self):
        self.assertFalse(
            self.reports.find_enumeration_rationales(
                [row("the response MUST and NEVER carry a section key", owner="whatever")]
            ),
            "ALL-CAPS prose words are not response elements; counting them manufactures a "
            "coordinated pair out of emphasis.",
        )


class TheTwoReportersStayDistinct(unittest.TestCase):
    """Neither block may absorb the other's hits, or the report double-counts."""

    def setUp(self):
        self.reports = load_reports()

    def test_a_count_is_not_reported_as_an_enumeration(self):
        self.assertFalse(
            self.reports.find_enumeration_rationales([row("both results are SDK examples")]),
            "A count belongs under the census label, which prescribes a different fix.",
        )

    def test_an_enumeration_is_not_reported_as_a_count(self):
        owner = "it returned the *Alpha* and *Beta* sections (absence negative)"
        self.assertFalse(
            self.reports.find_census_rationales([row("x", owner=owner)]),
            "An enumeration carries no numeral; if the census matcher claims it, the count "
            "report stops meaning what its own preamble says.",
        )


class TheReportSeparatesTheTwoShapes(unittest.TestCase):
    """Criterion 3, asserted against real output on a SYNTHETIC tree.

    ⚠️ Driven from fixtures rather than the live repo on purpose. The first version of this
    class read the live tree, which made it assert a CONTINGENT fact -- that hits exist --
    so it would have failed the moment `restamp-27-mcp-negatives-to-server-1-36-0` corrected
    the last enumeration, for a good reason and with a bad message. "Both labels appear when
    both shapes are present" is the durable property; "the tree currently has a hit" is a
    separate claim, below, and is marked as expected to invert.
    """

    MARKERS = (
        "<!-- MCP-NEGATIVE: search_docs(query='a') — no such thing; both results are SDK "
        "examples — owner: search_docs IS the route (absence negative) — server 1.36.0, "
        "2026-09-02 -->\n"
        "<!-- MCP-NEGATIVE: search_docs(query='b') — no such rule — owner: search_docs IS "
        "the route, and it returned the *Alpha* and *Beta* sections (absence negative) — "
        "server 1.36.0, 2026-09-02 -->\n"
    )

    def _report(self, text):
        import contextlib
        import io
        import tempfile

        reports = load_reports()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "plugins"
            root.mkdir()
            (root / "fixture.md").write_text(text, encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                reports.report_negatives(tmp, None)
            return buf.getvalue()

    def test_both_labels_and_both_judgment_notes_are_printed(self):
        out = self._report(self.MARKERS)
        self.assertIn("CENSUS-SHAPED rationales", out)
        self.assertIn("ENUMERATION-SHAPED rationales", out)
        self.assertEqual(
            2, out.count("A hit needs judgment"),
            "Each block carries its own judgment note. One shared note lets a reader apply "
            "the count block's reasoning to an enumeration, where the legitimate-use rate "
            "is much higher -- three of four in the corpus on 2026-09-02.",
        )

    def test_each_shape_is_listed_under_its_own_label_only(self):
        """A hit under the wrong label prescribes the wrong fix: re-describe vs re-ask."""
        out = self._report(self.MARKERS)
        census = out.split("CENSUS-SHAPED rationales", 1)[1].split("ENUMERATION-SHAPED", 1)[0]
        # ⚠️ Bound the tail at the marker listing. Without this the block runs to end of
        # output and picks up both markers' full text from the listing below, which
        # made this assertion pass-by-accident in one direction and fail in the other.
        enumerated = out.split("ENUMERATION-SHAPED rationales", 1)[1].split("\nmarkers:", 1)[0]
        self.assertIn("'both results'", census)
        self.assertNotIn("Alpha", census)
        self.assertIn("*Alpha* and *Beta*", enumerated)
        self.assertNotIn("both results", enumerated)

    def test_the_report_stays_quiet_when_no_rationale_has_either_shape(self):
        """Neither block may print on a clean tree, or the labels stop carrying information."""
        clean = (
            "<!-- MCP-NEGATIVE: search_docs(query='c') — the topic list carries no upgrade "
            "entry — owner: search_docs IS the corpus route and it is empty (absence "
            "negative) — server 1.36.0, 2026-09-02 -->\n"
        )
        out = self._report(clean)
        self.assertNotIn("CENSUS-SHAPED", out)
        self.assertNotIn("ENUMERATION-SHAPED", out)


class NoShippedMarkerPinsAnEnumeration(unittest.TestCase):
    """The state `restamp-27-mcp-negatives-to-server-1-36-0` established, asserted against the tree.

    ⛔ **This class REPLACED an inverted one, and the replacement is the point.** While the drift
    was live, `TheDriftedSiteIsFlaggedUntilItIsCorrected` asserted that
    `phase2-data-mapping.md:719` WAS flagged -- criterion 1's first half. Its failure message named
    the two causes a later silence could have (rationale corrected, or matcher regressed) and said
    to flip it once the first applied. On 2026-09-02 the restamp corrected that rationale, the guard
    failed with exactly that message, and the detector returned an empty list while all twenty
    fixture-driven assertions still passed -- which is what distinguished (a) from (b). Flipped.

    ⚠️ Scoped to ``plugins/`` for the same reason `NoShippedMarkerPinsACount` is: ``specs/DECLINED.md``
    carries a marker and is a RECORD of a decision already taken, so rewriting its evidence is the
    maintainer's call rather than a guard's. Its census WAS corrected in the same change and it is
    clean today; the report still lists it, and this test still does not.
    """

    def test_no_marker_under_plugins_pins_an_enumeration(self):
        reports = load_reports()
        found = [r for r in reports.find_negatives(str(REPO)) if r[5].startswith("plugins")]
        self.assertTrue(found, "No markers found under plugins/ -- has the scan broken?")
        flagged = reports.find_enumeration_rationales(found)
        self.assertEqual(
            [], flagged,
            "A shipped marker's rationale enumerates named response elements as what the route "
            "returned. Re-ask the owning route and replace the list with the PROPERTY it stands "
            "in for -- re-listing today's names is a re-date in disguise and keeps the liability, "
            "because the next server-side rename falsifies it again:\n  "
            + "\n  ".join("%s:%d — %r" % f for f in flagged),
        )


#: The words that make a provenance claim about a fixture. A docstring or comment using one
#: promises the fixture IS the text, so the fixture must come from the `quoted()` registry.
_PROVENANCE_WORD = re.compile(r"\b(?:verbatim|shipped)\b", re.IGNORECASE)
#: A string literal this short is a placeholder ("no such rule", "every hit"), never a
#: rationale someone could mistake for a quote. Anything longer is a fixture.
_PLACEHOLDER_MAX = 20
#: How many leading positional arguments each assertion takes before its message.
_ASSERT_ARITY = {
    "assertTrue": 1, "assertFalse": 1, "assertIsNone": 1, "assertIsNotNone": 1,
    "assertEqual": 2, "assertNotEqual": 2, "assertIn": 2, "assertNotIn": 2,
}
_SHA = re.compile(r"[0-9a-f]{7,40}")


def _provenance_violations(source, quote_names, exempt=()):
    """[(test, detail)] for tests that call a fixture verbatim/shipped but do not quote it.

    A test's provenance text is its own docstring and comments plus its class's docstring.
    If that text uses a provenance word, the test must reference at least one registered
    quote, and may carry no string literal longer than a placeholder outside its docstring
    and its assertions' messages -- a literal there is a fixture no guard can resolve.
    """
    tree = ast.parse(source)
    comments = {}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            comments[tok.start[0]] = tok.string
    violations = []
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        if cls.name in exempt:
            continue
        for fn in (n for n in cls.body if isinstance(n, ast.FunctionDef)):
            said = " ".join(filter(None, [ast.get_docstring(cls), ast.get_docstring(fn)]
                                   + [c for line, c in comments.items()
                                      if fn.lineno <= line <= fn.end_lineno]))
            if not _PROVENANCE_WORD.search(said):
                continue
            name = "%s.%s" % (cls.name, fn.name)
            skip = set()
            if ast.get_docstring(fn) is not None:
                skip.add(id(fn.body[0].value))
            for call in (n for n in ast.walk(fn) if isinstance(n, ast.Call)):
                attr = getattr(call.func, "attr", None)
                if attr in _ASSERT_ARITY:
                    message = call.args[_ASSERT_ARITY[attr]:] + [
                        k.value for k in call.keywords if k.arg == "msg"]
                    skip.update(id(n) for m in message for n in ast.walk(m))
            used = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
            if not used & set(quote_names):
                violations.append((name, "uses no quoted() fixture"))
            for node in ast.walk(fn):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and id(node) not in skip and len(node.value) > _PLACEHOLDER_MAX):
                    violations.append((name, "unquoted literal %r" % node.value[:48]))
    return violations


def _quote_names(source):
    """Module-level names bound to a `quoted(...)` call."""
    return {t.id for n in ast.parse(source).body if isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", "") == "quoted"
            for t in n.targets if isinstance(t, ast.Name)}


def _unresolved_live_quotes(quotes, found):
    """Quotes claiming to ship NOW that no parsed marker's claim or owner contains."""
    halves = [h for r in found for h in (r[3], r[4])]
    return [(text, source) for text, source, commit in quotes
            if commit is None and not any(text in h for h in halves)]


class FixtureProvenanceIsChecked(unittest.TestCase):
    """⛔ A paraphrase must not be able to pass as a quote again (#151).

    The census fixtures were described as the phrasings that had shipped, and one read "all
    six hits" where the marker read "every hit". The test passed; the marker was invisible to
    the detector it certified. Three checks close that: live quotes resolve against
    `find_negatives()`, historical quotes resolve against git at their commit, and a test
    that makes a provenance claim must take its fixture from the registry. Each check is
    also run against a planted violation, so the guard is shown to fail, not assumed to.
    """

    SOURCE = Path(__file__).read_text(encoding="utf-8")

    def test_every_live_quote_is_in_a_shipped_marker(self):
        found = load_reports().find_negatives(str(REPO))
        self.assertTrue(found, "No markers found -- has the scan broken?")
        self.assertEqual(
            [], _unresolved_live_quotes(QUOTES, found),
            "A fixture registered as current text is not in any marker's claim or owner. If the "
            "marker was rewritten, pass commit=<the sha it was copied from> and call it "
            "historical; if it never matched, it is a paraphrase and must not be quoted.",
        )

    def test_every_historical_quote_names_a_commit(self):
        for text, source, commit in QUOTES:
            if commit is not None:
                with self.subTest(source=source):
                    self.assertRegex(commit, _SHA, "A historical quote needs a commit sha.")
                    self.assertRegex(source, r"^[^:]+:\d+$", "Source must be path:line.")

    def test_every_historical_quote_is_on_its_line_at_its_commit(self):
        """Resolved with git, so a real sha beside a paraphrase still fails.

        Skipped rather than failed when history is unavailable (no git, shallow clone), as
        `test_spec_ledger_invariants.py` does. CI checks out full history (fetch-depth: 0).
        """
        if shutil.which("git") is None or subprocess.run(
                ["git", "-C", str(REPO), "rev-parse", "--is-inside-work-tree"],
                capture_output=True, text=True).returncode != 0:
            self.skipTest("not a git work tree")
        if subprocess.run(["git", "-C", str(REPO), "rev-parse", "--is-shallow-repository"],
                          capture_output=True, text=True).stdout.strip() == "true":
            self.skipTest("shallow clone -- the quoted commits are not present")
        for text, source, commit in QUOTES:
            if commit is None:
                continue
            path, lineno = source.rsplit(":", 1)
            with self.subTest(source=source, commit=commit):
                shown = subprocess.run(
                    ["git", "-C", str(REPO), "show", "%s:%s" % (commit, path)],
                    capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(0, shown.returncode, shown.stderr)
                lines = shown.stdout.splitlines()
                self.assertIn(
                    text, lines[int(lineno) - 1] if int(lineno) <= len(lines) else "",
                    "A historical quote is not on the line it names at the commit it names. "
                    "Copy the text word for word, or stop calling it a quote.",
                )

    def test_a_provenance_claim_takes_its_fixture_from_the_registry(self):
        self.assertEqual(
            [], _provenance_violations(self.SOURCE, _quote_names(self.SOURCE),
                                       exempt={type(self).__name__}),
            "A test whose docstring or comments call its fixture verbatim or shipped carries "
            "text the registry cannot resolve. Route it through quoted(), or reword the "
            "docstring to say it is a paraphrase.",
        )

    def test_the_guard_fails_on_a_planted_paraphrase(self):
        """The negative control, kept: each check must report a violation it is handed."""
        planted = (
            "class Planted(unittest.TestCase):\n"
            "    def test_x(self):\n"
            '        """`SKILL.md:387`, verbatim."""\n'
            '        claim = "no procedure anywhere; all six hits are V3-to-V4"\n'
            "        self.assertTrue(claim, 'a message long enough to be skipped here')\n"
        )
        self.assertEqual(2, len(_provenance_violations(planted, {"PRE_151_UPGRADE"})),
                         "A verbatim-labeled paraphrase must fail both the registry-use and "
                         "the unquoted-literal checks.")
        quoting = planted.replace(
            'claim = "no procedure anywhere; all six hits are V3-to-V4"', "claim = PRE_151_UPGRADE")
        self.assertEqual([], _provenance_violations(quoting, {"PRE_151_UPGRADE"}),
                         "A test that quotes through the registry must pass.")
        self.assertEqual(
            1, len(_unresolved_live_quotes(
                [("no 4.x-to-4.y procedure anywhere; all six hits are V3-to-V4", "x:1", None)],
                load_reports().find_negatives(str(REPO)))),
            "A paraphrase registered as current text must not resolve against the tree.",
        )


if __name__ == "__main__":
    unittest.main()
