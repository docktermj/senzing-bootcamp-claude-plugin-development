"""A rate-limited CORD download was saved as the source's data file.

Fetching the four sources of a generated `las-vegas` scenario back to back trips a rate
limit on the download endpoint, and the limit message arrives **as the response body** —
43 bytes of English prose written into the file being saved. Reproduced live twice in one
four-source fetch (server 1.32.9, 2026-08-12): `OPEN-OWNERSHIP` and `US-LABOR-VIOLATIONS`
each landed as a one-line file whose single line is prose, while `PPP_LOANS` and `GLEIF`
came back whole.

Two facts make the fix what it is, and both were established against the live server
rather than taken from the spec:

- The throttled response **does** carry HTTP **429**. It is machine-readable, so a status
  check is the decisive test — but `curl -sS -o file url` exits 0 and writes the prose body
  anyway, so it is caught only by asking for the status.
- `download_url` caps at `download_url_max_records`, so a bare equality check against
  `record_count` would fail every source larger than the cap for no reason; the expected count
  is `min(record_count, cap)` for a `download_url` fetch and `record_count` exactly for a
  `source_download_url` fetch. **The cap is read from the response, never pinned here** (#448):
  it was 10,000 on server 1.32.9 (2026-08-12) and 250,000 on 1.37.19 (2026-10-04), and the plugin
  stated the old figure for weeks after it changed.
- A `source='list'` entry can carry `truncated: true` (#448; `EQUIFAX` and `OPENDATA` on 1.37.19,
  2026-10-04). Its `record_count` is itself capped, so an uncapped fetch of that source must hold
  **at least** `record_count` records, not exactly that many. Module 4 states that once, under the
  `truncated-cord-source` anchor, and every shipped reader of `expected_record_count` links it.

The condition itself needs the network, which no offline test has. What is pinned here is
the *instruction*: the count comparison, the 429/backoff handling, and the staging rule that
keeps an unverified fetch out of `data/raw/` under the source's final name.

Enforces **INV-203** (a fetched source reaches `data/raw/` under its final name only after
**both** a 2xx status and a measured record count equal to the expected one, with a
throttled response retried rather than saved as data), which names this file. The truncated-source
floor is INV-203's drafted 2026-10-04 correction (#448), queued for `/review-invariants`.

Prose guards read through `match_lines` from `tests/_wrapped_text.py`, so a phrase wrapped across
lines is still one match (INV-346). The readers of `expected_record_count` are found by scanning
every shipped file (INV-246), not listed.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wrapped_text import match_lines  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE_04 = PLUGIN / "skills" / "module-04-data-collection" / "SKILL.md"

ANCHOR = '<a id="cord-fetch-integrity"></a>'
TRUNCATED_ANCHOR = '<a id="truncated-cord-source"></a>'
TRUNCATED_FRAGMENT = "#truncated-cord-source"
#: The link every reader of `expected_record_count` carries to the one definition (INV-300).
POINTER_TEXT = "[the truncated-source rule]"
FIELD = "`expected_record_count`"


def flat(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


def canonical_block():
    """The fetch-integrity block alone, so language-agnostic checks are scoped to it."""
    text = MODULE_04.read_text(encoding="utf-8")
    start = text.index(ANCHOR)
    end = text.index("**If the bootcamper declines CORD data**", start)
    return re.sub(r"\s+", " ", text[start:end])


class TheRuleHasOneCanonicalHome(unittest.TestCase):
    """This repo's convention: one anchored statement, referenced rather than restated."""

    def test_the_canonical_block_has_an_anchor(self):
        self.assertIn(ANCHOR, MODULE_04.read_text(encoding="utf-8"))

    def test_it_declares_itself_canonical(self):
        self.assertIn("canonical statement; do not restate it elsewhere", flat(MODULE_04))

    def test_the_consumers_reference_it_rather_than_restate(self):
        text = MODULE_04.read_text(encoding="utf-8")
        refs = text.count("(#cord-fetch-integrity)")
        self.assertGreaterEqual(
            refs,
            3,
            "the generated-scenario fetch path, the registry schema and Data File Validation must all link it",
        )


class TheRateLimitCaseIsNamedAndHandled(unittest.TestCase):
    """The plugin had no rate-limit awareness at all before this."""

    def test_the_throttled_body_is_quoted_verbatim(self):
        self.assertIn("Rate limit exceeded. Try again in 1 second.", flat(MODULE_04))

    def test_the_response_is_named_as_arriving_as_the_body(self):
        self.assertRegex(flat(MODULE_04), r"(?i)comes back \*\*as the response body\*\*")

    def test_the_429_status_is_the_decisive_check(self):
        block = canonical_block()
        self.assertRegex(block, r"HTTP \*\*429\*\*")
        self.assertRegex(block, r"(?i)Anything outside 2xx is a \*\*failed fetch\*\*")

    def test_the_silent_curl_trap_is_called_out(self):
        """A status check is only decisive if the reader knows it must be requested."""
        block = canonical_block()
        self.assertRegex(block, r"(?i)exits \*\*0\*\* and")
        self.assertRegex(block, r"--fail")

    def test_retry_with_backoff_is_instructed(self):
        self.assertRegex(canonical_block(), r"(?i)retry with a short backoff")

    def test_sequential_fetches_are_spaced(self):
        self.assertRegex(canonical_block(), r"(?i)pause between sequential source fetches")


class TheCountComparisonIsPrescribed(unittest.TestCase):
    """"Plausible record count" was a judgment; the decisive figure was already in hand."""

    def test_the_expected_count_comes_from_the_mcp_source_listing(self):
        self.assertRegex(canonical_block(), r"source='list'\)` returns `record_count` per source")

    def test_a_mismatch_fails_the_collection_rather_than_warning(self):
        self.assertRegex(canonical_block(), r"\*\*failed collection, not a warning\*\*")

    def test_the_capped_case_uses_min_rather_than_bare_equality(self):
        """A bare equality check would fail 6 of 11 las-vegas sources."""
        block = canonical_block()
        self.assertIn("min(record_count, download_url_max_records)", block)
        self.assertRegex(block, r"(?i)expect exactly `record_count`")

    def test_plausibility_is_explicitly_rejected(self):
        self.assertRegex(canonical_block(), r"(?i)\"plausible record count\" is a judgment")

    def test_data_file_validation_requires_a_match_not_a_plausibility_call(self):
        self.assertRegex(flat(MODULE_04), r"(?i)a record count that \*\*matches\*\* it rather than one that merely looks plausible")


class AnUnverifiedFetchNeverReachesItsFinalName(unittest.TestCase):
    def test_it_stages_inside_the_project(self):
        block = canonical_block()
        self.assertIn("data/temp/<source>.jsonl", block)
        self.assertIn("INV-200", block)

    def test_the_move_is_gated_on_the_checks(self):
        self.assertRegex(canonical_block(), r"(?i)only once checks 1 and 2 pass")

    def test_system_temp_is_refused(self):
        self.assertRegex(canonical_block(), r"(?i)never uses system temp")


class BothCountsAreRecorded(unittest.TestCase):
    """Step 7 can only confirm what the registry entry recorded."""

    def test_the_registry_schema_carries_the_expected_count(self):
        self.assertIn("`expected_record_count`", flat(MODULE_04))

    def test_the_measured_count_is_no_longer_optional(self):
        text = flat(MODULE_04)
        self.assertNotIn("`record_count` (if known, else null)", text)
        self.assertRegex(text, r"(?i)`record_count` \(the count you \*\*measured\*\*")

    def test_both_checks_are_named_for_validation_checks(self):
        block = canonical_block()
        self.assertIn("http_status_ok", block)
        self.assertIn("record_count_matches_expected", block)


class TheDownloadCapIsNotMisdescribed(unittest.TestCase):
    """`download_url` was presented as "the full JSONL file"; it is a slice sized by its cap."""

    def test_the_two_urls_are_distinguished(self):
        text = flat(MODULE_04)
        self.assertIn("`download_url_max_records`", text)
        self.assertIn("`source_download_url`", text)

    def test_the_cap_is_named_by_its_field_and_read_from_the_response(self):
        """#448: the cap is a response field, not a constant the plugin states."""
        text = flat(MODULE_04)
        self.assertIn("at most `download_url_max_records` records per request", text)
        self.assertRegex(
            text,
            r"Read the cap from that field in the response; never state it as a fixed number\*\* \(INV-080\)",
        )

    def test_download_url_is_not_called_the_full_file(self):
        text = flat(MODULE_04)
        self.assertNotIn("so the bootcamper can download the full JSONL file", text)
        self.assertIn('is **not** "the full file"', text)

    def test_the_cap_and_truncation_are_illustrated_once_with_a_date(self):
        """One dated illustration (#448 scope), stamped with the call, server and date."""
        text = flat(MODULE_04)
        self.assertRegex(
            text,
            r"Illustration only, dated, never a constant: `get_sample_data\(dataset='las-vegas', source='list'\)` "
            r"listed `EQUIFAX` and `OPENDATA` with `\"record_count\": 250000, \"truncated\": true`",
        )
        self.assertRegex(text, r"`download_url_max_records: 250000` \(server 1\.37\.19, 2026-10-04\)")


# --- #448: the cap is read from the response, and a truncated source is a floor ---------------

#: A cap or a source size stated as a fixed figure. Each alternative is a shape that shipped
#: before #448: the cap beside its field or a "serves up to" note, a "N-record slice", the
#: count of sources over the cap, and `EQUIFAX`'s size.
FIXED_CAP = re.compile(
    r"(?i)(?:`download_url_max_records`|download_url serves up to)[^.;]{0,40}?\b10,?000\b"
    r"|\b10,?000-record (?:slice|preview)"
    r"|\b\d+ (?:of the \d+ `?las-vegas`? sources|exceed it)\b"
    r"|\bfail \d+ of the \d+\b"
    r"|\b72,?799\b"
)
#: A dated stamp: a server version and an ISO date, as INV-080 requires of a Senzing fact.
STAMP = re.compile(r"\b1\.\d+\.\d+\b.*?\b\d{4}-\d{2}-\d{2}\b|\b\d{4}-\d{2}-\d{2}\b.*?\b1\.\d+\.\d+\b")
CAP_FIGURE = re.compile(r"\b250,?000\b")
#: Block starts of blocks that name the figure, and of those that also carry a dated stamp.
NAMES_CAP_FIGURE = re.compile(r"^.*?" + CAP_FIGURE.pattern)
NAMES_DATED_CAP_FIGURE = re.compile(r"^(?=.*?" + CAP_FIGURE.pattern + r")(?=.*?(?:" + STAMP.pattern + r"))")
#: The block start of a block that names the field; `^` anchors at a block (see _wrapped_text).
NAMES_FIELD = re.compile(r"^.*?" + re.escape(FIELD))


def shipped_markdown():
    return sorted(PLUGIN.rglob("*.md"))


def pointer_target(path):
    """The link target a reader in ``path`` must use to reach the anchor."""
    if path == MODULE_04:
        return TRUNCATED_FRAGMENT
    rel = os.path.relpath(MODULE_04, path.parent).replace(os.sep, "/")
    return rel + TRUNCATED_FRAGMENT


def without_the_definition(path, text):
    """Module 4 minus the anchored definition itself, which is what the readers point at."""
    if path != MODULE_04 or TRUNCATED_ANCHOR not in text:
        return text
    start = text.index(TRUNCATED_ANCHOR)
    end = text.index(ANCHOR, start)
    return text[:start] + text[end:]


def readers_missing_the_pointer(path, text):
    """Lines of each block in ``text`` that names the field but does not link the anchor.

    Wrap-aware (INV-346): both patterns run on whole collapsed blocks through `match_lines`.
    """
    text = without_the_definition(path, text)
    pointer = re.compile(r"^.*?" + re.escape(POINTER_TEXT + "(" + pointer_target(path) + ")"))
    readers = match_lines(text, NAMES_FIELD)
    linked = set(match_lines(text, pointer))
    return [line for line in readers if line not in linked]


def truncated_definition():
    text = MODULE_04.read_text(encoding="utf-8")
    start = text.index(TRUNCATED_ANCHOR)
    end = text.index(ANCHOR, start)
    return re.sub(r"\s+", " ", text[start:end])


class NoFixedCapOrSourceSizeShips(unittest.TestCase):
    """#448: 10,000 shipped as the cap for weeks after the server raised it."""

    def test_no_shipped_markdown_states_a_fixed_cap_or_source_size(self):
        offenders = []
        for path in shipped_markdown():
            for line in match_lines(path.read_text(encoding="utf-8"), FIXED_CAP):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{line}")
        self.assertEqual([], offenders, "a fixed cap or source size ships; read it from the response")

    def test_the_pattern_catches_every_shape_that_shipped(self):
        """Negative control: the pre-#448 sentences, verbatim and with their line breaks."""
        shipped_before = [
            "- **`download_url`** serves at most `download_url_max_records` records per request — **10,000** —\n  and needs only",
            "So `download_url` is **not** \"the full file\": of the 11\n`las-vegas` sources **6 exceed it**, `EQUIFAX` alone having 72,799 records.",
            "say\nplainly that it is a 10,000-record slice.",
            "against the full `record_count` would\n     fail 6 of the 11 `las-vegas` sources for no reason.",
            "*\"Showing N of 17\n   records (preview). To get more: download_url serves up to 10000 records per request",
            "downloaded 10,000-record preview batches from each source",
            "four fields on a\n72,799-record source were marked",
        ]
        for sample in shipped_before:
            with self.subTest(sample=sample[:40]):
                self.assertTrue(match_lines(sample, FIXED_CAP), "the guard misses a shape that shipped")

    def test_the_pattern_leaves_unrelated_figures_alone(self):
        for sample in (
            "Size the generated scenario to about 10,000 records",
            "More than 500,000, up to 10,000,000 — medium production",
            "`nodes-entities-sample.csv` 10000001-10000010",
        ):
            with self.subTest(sample=sample):
                self.assertEqual([], match_lines(sample, FIXED_CAP))

    def test_every_shipped_cap_figure_is_a_dated_quote(self):
        """The one figure allowed is the dated illustration or quote, never a bare constant."""
        undated = []
        for path in shipped_markdown():
            text = path.read_text(encoding="utf-8")
            figures = set(match_lines(text, NAMES_CAP_FIGURE))
            stamped = set(match_lines(text, NAMES_DATED_CAP_FIGURE))
            undated += [f"{path.relative_to(REPO_ROOT)}:{n}" for n in sorted(figures - stamped)]
        self.assertEqual([], undated, "a cap figure ships without a server version and date")
        found = [p for p in shipped_markdown() if CAP_FIGURE.search(p.read_text(encoding="utf-8"))]
        self.assertTrue(found, "no dated illustration of the cap ships, so the scan is vacuous")

    def test_an_undated_cap_figure_is_caught(self):
        """Negative control for the check above."""
        sample = "`download_url` serves at most\n250,000 records per request."
        self.assertEqual([1], match_lines(sample, NAMES_CAP_FIGURE))
        self.assertEqual([], match_lines(sample, NAMES_DATED_CAP_FIGURE))
        dated = sample + " (server 1.37.19,\n2026-10-04)"
        self.assertEqual([1], match_lines(dated, NAMES_DATED_CAP_FIGURE))


class TheTruncatedSourceRuleIsDefinedOnce(unittest.TestCase):
    """One anchored statement in Module 4 (INV-300); INV-203's drafted 2026-10-04 correction."""

    def test_the_anchor_exists_once_in_the_plugin(self):
        hits = [p for p in shipped_markdown() if TRUNCATED_ANCHOR in p.read_text(encoding="utf-8")]
        self.assertEqual([MODULE_04], hits)
        self.assertEqual(1, MODULE_04.read_text(encoding="utf-8").count(TRUNCATED_ANCHOR))

    def test_it_is_a_cited_hard_rule_and_declares_itself_canonical(self):
        block = truncated_definition()
        self.assertIn("**⛔ (INV-203) A truncated source: its listed `record_count` is a cap, not its size.**", block)
        self.assertIn("canonical statement of the truncated-source rule", block)
        self.assertIn("rather than restating it (INV-300)", block)

    def test_it_says_what_truncated_means(self):
        block = truncated_definition()
        self.assertIn("`truncated: true` reports a `record_count` that is **itself capped**", block)
        self.assertRegex(block, r"`download_url` serves a slice of it")

    def test_it_says_what_the_registry_records(self):
        self.assertRegex(
            truncated_definition(),
            r"records `expected_record_count` as that capped figure, with \*\*`truncated: true`\*\* beside it",
        )

    def test_it_makes_the_uncapped_fetch_a_floor_and_keeps_the_capped_fetch_exact(self):
        block = truncated_definition()
        self.assertRegex(block, r"via \*\*`source_download_url`\*\* \(uncapped\) → the figure is a \*\*floor\*\*")
        self.assertIn("**at least** `record_count` records passes, and one with fewer is a failed collection", block)
        self.assertRegex(block, r"via \*\*`download_url`\*\* \(capped\) → exact, `min\(record_count, download_url_max_records\)`")

    def test_it_binds_every_later_reader(self):
        self.assertRegex(
            truncated_definition(),
            r"\*\*Every later reader\*\* of `expected_record_count` treats it as a floor on the collected "
            r"file's size when the entry carries `truncated: true`",
        )

    def test_the_floor_is_stated_nowhere_else(self):
        """State it once (INV-300): readers link the rule, they do not restate it."""
        floor = re.compile(r"(?i)\bat least\b[^.]{0,40}`record_count`")
        elsewhere = []
        for path in shipped_markdown():
            text = without_the_definition(path, path.read_text(encoding="utf-8"))
            elsewhere += [f"{path.relative_to(REPO_ROOT)}:{n}" for n in match_lines(text, floor)]
        self.assertEqual([], elsewhere)
        self.assertTrue(match_lines(truncated_definition(), floor), "the floor pattern matches nothing")


class EveryReaderLinksTheTruncatedSourceRule(unittest.TestCase):
    """#448: every site that reads `expected_record_count` treats it as a floor when truncated.

    The readers are found by scanning every shipped file (INV-246), not from a list.
    """

    def test_the_scan_is_not_vacuous(self):
        files = {p for p in shipped_markdown() if FIELD in p.read_text(encoding="utf-8")}
        names = {p.relative_to(PLUGIN).as_posix() for p in files}
        for expected in (
            "skills/module-04-data-collection/SKILL.md",
            "skills/module-05-data-quality-mapping/phase1-quality-assessment.md",
            "skills/module-06-data-processing/phaseB-load-first-source.md",
            "skills/graduation/SKILL.md",
        ):
            self.assertIn(expected, names)
        readers = sum(
            len(match_lines(without_the_definition(p, p.read_text(encoding="utf-8")), NAMES_FIELD))
            for p in files
        )
        self.assertGreaterEqual(readers, 10, "fewer readers than #448 counted; the scan has gone blind")

    def test_every_shipped_reader_links_the_rule(self):
        missing = []
        for path in shipped_markdown():
            text = path.read_text(encoding="utf-8")
            missing += [f"{path.relative_to(REPO_ROOT)}:{n}" for n in readers_missing_the_pointer(path, text)]
        self.assertEqual(
            [], missing,
            "a block names `expected_record_count` without linking "
            f"{POINTER_TEXT}(...{TRUNCATED_FRAGMENT}), so it may read a capped figure as exact",
        )

    def test_no_other_shipped_file_reads_the_field(self):
        """A script or config that reads it would need the floor too; none does today."""
        others = [
            p.relative_to(REPO_ROOT).as_posix()
            for p in PLUGIN.rglob("*")
            if p.is_file() and p.suffix != ".md" and FIELD.strip("`") in p.read_text(encoding="utf-8", errors="ignore")
        ]
        self.assertEqual([], others, "a non-Markdown file reads `expected_record_count`; extend this guard to it")

    def test_check_2_and_the_registry_write_link_the_rule(self):
        block = canonical_block()
        self.assertIn(
            "expect exactly `record_count`, unless the source is truncated, as "
            "[the truncated-source rule](#truncated-cord-source) defines",
            block,
        )
        self.assertIn(
            "`expected_record_count` (what the server stated, with `truncated: true` beside it as "
            "[the truncated-source rule](#truncated-cord-source) defines)",
            block,
        )

    def test_data_file_validation_links_the_rule(self):
        self.assertIn(
            "or meets it for a truncated source, as [the truncated-source rule](#truncated-cord-source) defines",
            flat(MODULE_04),
        )

    def test_a_reader_whose_link_is_removed_is_caught(self):
        """Negative control: strip each reader's link in memory, one at a time."""
        checked = 0
        for path in shipped_markdown():
            text = path.read_text(encoding="utf-8")
            link = POINTER_TEXT + "(" + pointer_target(path) + ")"
            if link not in text:
                continue
            start = 0
            while True:
                i = text.find(link, start)
                if i < 0:
                    break
                mutated = text[:i] + "the rule" + text[i + len(link):]
                # A link in a block that names no `expected_record_count` (check 2, Data File
                # Validation, the presentation sentence) is pinned by name above instead.
                if set(readers_missing_the_pointer(path, mutated)) - set(readers_missing_the_pointer(path, text)):
                    checked += 1
                start = i + len(link)
        readers = sum(
            len(match_lines(without_the_definition(p, p.read_text(encoding="utf-8")), NAMES_FIELD))
            for p in shipped_markdown()
        )
        self.assertEqual(readers, checked, "removing a reader's link was not caught at every reader")

    def test_a_new_reader_without_the_link_is_caught(self):
        sample = "Para one.\n\nCompare the loaded count against\n`expected_record_count` and stop.\n"
        path = PLUGIN / "skills" / "module-06-data-processing" / "phaseB-load-first-source.md"
        self.assertEqual([3], readers_missing_the_pointer(path, sample))

    def test_a_link_with_the_wrong_path_is_caught(self):
        """From another skill the bare fragment points at that file, not at Module 4."""
        path = PLUGIN / "skills" / "graduation" / "SKILL.md"
        wrong = "Strip `expected_record_count` (as [the truncated-source rule](#truncated-cord-source) defines)."
        right = wrong.replace("(#truncated", "(../module-04-data-collection/SKILL.md#truncated")
        self.assertEqual([1], readers_missing_the_pointer(path, wrong))
        self.assertEqual([], readers_missing_the_pointer(path, right))

    def test_a_link_wrapped_across_lines_still_counts(self):
        """INV-346: the link text and the field may sit on different lines of one block."""
        path = MODULE_04
        sample = "Leave `expected_record_count` untouched, with `truncated` as\n[the truncated-source rule](#truncated-cord-source) defines.\n"
        self.assertEqual([], readers_missing_the_pointer(path, sample))


class TheCheckStaysLanguageAgnostic(unittest.TestCase):
    """INVARIANTS.md: language-agnostic. A count is not a shell idiom."""

    def test_no_shell_line_count_pipeline_is_prescribed(self):
        block = canonical_block()
        for idiom in ("wc -l", "wc -c", "| grep -c"):
            self.assertNotIn(idiom, block, f"{idiom} would make the count check shell-only")

    def test_it_says_the_count_is_language_neutral(self):
        self.assertRegex(canonical_block(), r"(?i)in whatever language the Bootcamper chose")

    def test_windows_is_covered_alongside_the_posix_route(self):
        self.assertIn("Invoke-WebRequest", canonical_block())


class TheProvenanceIsStamped(unittest.TestCase):
    """Any Senzing fact written into the plugin carries tool, version and date (INV-080)."""

    def test_the_server_version_and_date_accompany_the_facts(self):
        block = canonical_block()
        self.assertIn("1.32.9", block)
        self.assertIn("2026-08-12", block)

    def test_the_establishing_call_is_named_for_the_two_urls(self):
        self.assertRegex(flat(MODULE_04), r"get_sample_data\(dataset='las-vegas', source='GLEIF', limit=1\)")


if __name__ == "__main__":
    unittest.main()
