"""The verbatim-check limitations must say, per limitation, how fresh each one is.

`phase2-data-mapping.md` recorded three limitations of `sz_verbatim_check.py` and honestly
labeled all three as "**not** re-run against the current server … treat them as 'expect this,
and check'". Two have now been re-confirmed and one has not, so a single blanket caveat is no
longer the truth: it invites a reader to re-derive behavior that is known, while giving the same
weight to the one entry that really is unverified.

⛔ **What was re-verified here is the MECHANISM, from the scripts the server itself delivers** —
`download_resource(filenames=['sz_verbatim_check.py', 'sz_routing_report.py'])` and the live
`mapping_workflow` step-3 payload schema, MCP server 1.32.9, 2026-08-14 — not a re-run of a
mapping:

* `check_verbatim()` tests `if v.strip() not in allowed`, and `allowed_values()` builds only whole
  stripped values, `|`/`;` segments and whitespace tokens. The script's own docstring says
  "Equality against this set (not substring)". So a multi-word extraction is unreachable **by
  construction** — limitation 1.
* Both scripts define `load_jsonl(path)` as `json.loads(ln)` over non-blank lines, with no CSV
  branch and no `try` around the parse, and both are documented `<source.jsonl> <output.jsonl>` —
  limitation 3. The `JSONDecodeError` text therefore depends on the CSV's first line, which is why
  quoting one message invites "different message, different problem".
* `is_exempt()` is still `attr in {"DATA_SOURCE", "RECORD_ID"} or attr.endswith("_TYPE")`, so
  limitation 2's attributes remain outside the waiver — limitation 2.

**Updated 2026-08-21: limitation 2 is no longer caveated, and the caveat's own condition is why.**
This file used to assert that limitation 2 stayed flagged as un-re-run because verifying it needed
a source with **disclosed relationships** that was not available. A 2026-08-18 run had one. The
rejection fired, and it **widened** the entry: `REL_ANCHOR_KEY` and `REL_POINTER_KEY` fail too
whenever `record_id_source` is the `RECORD_HASH` sentinel, because the key then mirrors a derived
hash that is not a value anywhere in the source. The three assertions that pinned the caveat were
inverted rather than deleted — a guard that keeps asserting a claim its own trigger condition
disproved is worse than no guard, and the new assertions cover the refinement instead.

Source specs: `specs/reverify-the-three-verbatim-check-limitations.md`,
`specs/rel-key-attributes-fail-the-verbatim-gate-too-whenever-record-id-is-a-hash.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE2 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
          / "module-05-data-quality-mapping" / "phase2-data-mapping.md")


def squash(text):
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M))


#: ⚠️ The block names its own length ("Three further limitations", "…for all three"), so a
#: hardcoded locator breaks the moment a limitation is added — which is exactly what happened
#: when a fourth was documented on 2026-09-01, taking 19 tests down as ERRORS rather than
#: failures. The COUNT is data; the block and its shared handling procedure are the claim, so
#: the locators match any count and the assertions below still check what they always did.
_BLOCK_START = re.compile(r"⛔ \*\*\w+ further limitations")
_BLOCK_END = re.compile(r"\*\*Handling is the same for all \w+")


def limitations_block():
    text = PHASE2.read_text(encoding="utf-8")
    start = _BLOCK_START.search(text)
    assert start, "the further-limitations block was not found — has it been renamed?"
    end = _BLOCK_END.search(text, start.start())
    assert end, "the shared handling line was not found after the limitations block"
    return squash(text[start.start():end.start()])


def map_step():
    text = PHASE2.read_text(encoding="utf-8")
    start = text.index("### 11. Map")
    end = _BLOCK_START.search(text, start).start()
    return squash(text[start:end])


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_file_exists(self):
        self.assertTrue(PHASE2.is_file(), "phase2-data-mapping.md moved")

    def test_both_regions_are_locatable(self):
        self.assertIn("REL_ANCHOR_DOMAIN", limitations_block(),
                      "the limitations block was not located")
        self.assertIn("disposition", map_step(), "the Map step was not located")


class TheBlanketCaveatIsReplacedByPerLimitationFreshness(unittest.TestCase):
    def setUp(self):
        self.block = limitations_block()

    def test_the_blanket_not_re_run_claim_is_gone(self):
        self.assertNotRegex(
            self.block,
            r"(?i)They were \*\*not\*\* re-run against the\s*current server",
            "all three limitations are still caveated together, so two known-current "
            "behaviors still invite re-derivation")

    def test_freshness_is_stated_per_limitation(self):
        self.assertRegex(
            self.block,
            r"(?i)Freshness, per limitation — all \w+ are CURRENT behavior",
            "the block does not say which entries are current")

    def test_the_re_verification_route_is_named(self):
        """A claim of freshness has to say how it was checked."""
        self.assertIn(
            "download_resource(filenames=['sz_verbatim_check.py',", self.block,
            "the re-check names no route, so a reader cannot repeat it")
        self.assertRegex(
            self.block, r"(?i)MCP server 1\.32\.9, 2026-08-14",
            "the re-check carries no server version and date")

    def test_it_says_what_kind_of_check_it_was(self):
        self.assertRegex(
            self.block,
            r"(?i)a check of the\s*\*\*mechanism\*\*, which is what these entries assert, and it "
            r"does not depend on re-running a mapping",
            "the re-check does not disclose that it verified the mechanism rather than "
            "re-running a mapping — which would overstate it")

    def test_limitations_1_and_3_are_marked_confirmed(self):
        for number, label in ((1, "Any correct `extract` output is rejected"),
                              (3, "Neither script runs on a CSV source")):
            with self.subTest(limitation=number):
                self.assertRegex(
                    self.block,
                    r"%s\. CONFIRMED CURRENT — server 1\.32\.9, 2026-08-14" % re.escape(label),
                    "limitation %d is not marked as confirmed current" % number)

    def test_limitation_2_is_marked_confirmed_end_to_end(self):
        """Inverted 2026-08-21: the condition this test used to wait for was met.

        It previously asserted limitation 2 was flagged as the one entry NOT re-run, and
        that the block named what would settle it — *a source carrying disclosed
        relationships*. A 2026-08-18 run had one, the rejection fired, and the entry is now
        confirmed. Asserting the old caveat would pin a claim the run disproved.
        """
        self.assertRegex(
            self.block,
            r"(?i)CONFIRMED END TO END — 2026-08-18",
            "limitation 2 is not marked as confirmed end to end, so a reader cannot tell "
            "it apart from an entry that is still only predicted")
        self.assertNotRegex(
            self.block,
            r"(?i)This is the one entry still NOT re-run",
            "limitation 2 is still flagged as un-re-run, which a 2026-08-18 run disproved")

    def test_the_key_attributes_are_never_called_an_unconditional_pass(self):
        """The refinement the confirming run produced, and the reason it matters.

        The block used to say `REL_ANCHOR_KEY` and `REL_POINTER_KEY` **pass**, full stop,
        "because those do carry source values". That holds only when `record_id_source` names
        a source field. On the `RECORD_HASH` sentinel — the normal case for an
        `embedded_master`, which is the disposition that produces REL_* scaffolding at all —
        the key is a derived hash and both KEY attributes fail with the others. A reader
        following the old text would read their failure as a mapping defect and iterate on
        correct code, which is what INV-173 exists to prevent.
        """
        self.assertRegex(
            self.block,
            r"(?i)pass only when `record_id_source` names a source\s*field",
            "the KEY attributes are not stated conditionally, so their failure on a hashed "
            "RECORD_ID reads as a mapping defect")
        self.assertRegex(
            self.block, r"(?i)RECORD_HASH",
            "the condition under which the KEY attributes fail is not named")

    def test_limitation_2_records_what_was_checkable(self):
        """Verification stated with its evidence, not asserted.

        The `is_exempt()` re-read still stands and is still the mechanism. What replaced the
        old "unverified end to end" disclosure is the offender-count reconciliation — the
        check a reader can run on their own mapping to tell this limitation from a real
        defect, which is strictly more useful than being told it was never confirmed.
        """
        self.assertRegex(
            self.block,
            r"(?i)`is_exempt\(\)` is still `attr in \{\"DATA_SOURCE\", \"RECORD_ID\"\} or",
            "the waiver mechanism was re-read and that is not recorded")
        self.assertRegex(
            self.block,
            r"(?i)reconciles to `records × REL_\* attributes per record`",
            "the offender-count reconciliation is missing, so a reader has no way to tell "
            "this limitation from a mapping defect of their own")
        self.assertIn(
            "83,338", self.block,
            "the measured offender count on a RECORD_HASH embedded master is not recorded")


class TheEvidenceForTheMechanismIsQuoted(unittest.TestCase):
    def setUp(self):
        self.block = limitations_block()

    def test_limitation_1_quotes_the_comparison(self):
        self.assertRegex(
            self.block,
            r"(?i)`check_verbatim\(\)` tests\s*`if v\.strip\(\) not in allowed`",
            "the mechanism is asserted without the line that implements it")
        self.assertRegex(
            self.block, r"(?i)Equality against this set \(not substring\)",
            "the script's own docstring — the strongest available evidence — is not quoted")

    def test_limitation_1_says_the_gate_rejects_by_construction(self):
        self.assertRegex(
            self.block,
            r"(?i)offers a disposition its own\s*step-4 gate rejects \*\*by construction\*\*",
            "the collision is described without saying it is structural")

    def test_limitation_3_generalizes_the_json_error(self):
        self.assertRegex(
            self.block,
            r"(?i)its message text depends on the CSV's first line\*\*,\s*so do not match on the "
            r"wording",
            "the JSONDecodeError text is still presented as a single quotable message")
        for observed in ("Extra data: line 1 column 5 (char 4)",
                         "Expecting value: line 1 column 1 (char 0)"):
            with self.subTest(message=observed):
                self.assertIn(observed, self.block,
                              "both observed messages should be shown as the same crash")

    def test_limitation_3_names_the_missing_csv_handling(self):
        self.assertRegex(
            self.block,
            r"(?i)no\*\*? CSV branch and \*\*no\*\* `try` around the parse",
            "the reason a CSV crashes is not stated, only that it does")


class TheExtractWarningArrivesBeforeTheGate(unittest.TestCase):
    """Criterion: the exemption guidance must be reachable before step 4 runs."""

    def setUp(self):
        self.step = map_step()

    def test_the_warning_is_in_the_map_step(self):
        self.assertRegex(
            self.step,
            r"(?i)Heads-up before you map anything with `disposition: extract` — read this now, "
            r"not after the\s*gate fails",
            "the extract collision is only documented ~450 lines below, under the block "
            "that defuses it")

    def test_it_states_the_mechanism_and_its_date(self):
        self.assertRegex(
            self.step,
            r"(?i)compares\s*whole values, `\|`/`;` segments and single whitespace tokens by "
            r"equality, never substrings",
            "the warning does not say why a correct extraction fails")
        self.assertRegex(
            self.step, r"(?i)confirmed on server 1\.32\.9, 2026-08-14",
            "the warning carries no provenance")

    def test_it_gives_the_three_part_action(self):
        self.assertRegex(self.step, r"(?i)do not iterate on the mapper",
                         "the warning does not forbid the iterate-forever loop")
        self.assertRegex(self.step, r"(?i)record the exemption and\s*its reason",
                         "the warning does not say to record the exemption")
        self.assertRegex(self.step, r"(?i)and \*\*proceed\*\*",
                         "the warning does not say to proceed")

    def test_it_names_the_trap_in_the_gates_own_wording(self):
        self.assertRegex(
            self.step,
            r"(?i)a code bug: fix the mapper … Do NOT proceed until it passes",
            "the gate's own wording is what sends the guide at their correct code, and "
            "the warning does not quote it")

    def test_it_says_extract_is_not_exotic(self):
        self.assertRegex(
            self.step,
            r"(?i)any prose field with an embedded address, date of birth\s*or identifier reaches "
            r"it",
            "without this the reader may assume the case is rare and skip the warning")

    def test_it_points_at_the_full_procedure(self):
        self.assertRegex(
            self.step, r"(?i)\w+ further limitations.{0,40}full procedure",
            "the pointer duplicates the guidance instead of routing to it, which is how "
            "the two drift apart")


class TheSurroundingRulesSurvive(unittest.TestCase):
    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")

    def test_the_do_not_fork_rule_is_intact(self):
        self.assertIn("Do not ship a patched copy of any of these scripts.", self.text,
                      "the no-fork rule (INV-173) was lost")

    def test_the_numeric_retirement_example_is_intact(self):
        """It is the proof that these do get fixed upstream, which is why dating matters."""
        self.assertRegex(
            squash(self.text), r"(?i)Numbers are NOT in that list any more",
            "the worked example of a retired limitation was lost")

    def test_the_four_step_handling_is_intact(self):
        self.assertRegex(
            self.text, r"Handling is the same for all \w+: the four steps above\.",
            "the shared handling procedure was lost")


if __name__ == "__main__":
    unittest.main()
