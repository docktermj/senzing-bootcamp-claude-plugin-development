"""The checked-in invariant manifest matches `specs/INVARIANTS.md`, and says what it could not derive.

Downstream ports each owe an **invariant-disposition register** — every `INV-NNN` resolving to
exactly one disposition in the port. Building that mechanically needs an authoritative list of the
ids; without one, each child writes its own parser of a 398 KB prose file written for human
authority, and ⛔ **each parses it differently, which defeats the uniformity the register exists
for** (#88).

⚠️ **The prose remains the source of truth.** The manifest is derived and must never drift from
it, which is what this guard is for — the same discipline `tests/test_invariants_index.py` applies
to the index.

⛔ **Two fields #88 asked for are not derivable from the prose, and the manifest reports rather
than invents them.** Measured across 309 entries:

* **`summary`** — the median first sentence is 249 characters and **113 of 309 exceed 300**. A
  summary is emitted only under the threshold; otherwise `null`. ⚠️ **Null means *not derivable*,
  never *no rule*** — `statement` always carries the full text, and a child treating null as
  absence would under-count its own register.
* **`status`** — supersession is written six ways in the prose, and the same word marks an entry
  that supersedes another as well as one that was superseded. Only an explicit *superseded by
  INV-nnn* is read as `superseded`; **33 entries are `unclear`** and counted, never guessed.

⚠️ **`index_group` and `section` are separate keys on purpose.** 33 entries — the foundational and
whole-Bootcamp invariants — appear in no *Index by subject* group at all; they are grouped by
heading. One key meaning two things would be a defect in a schema other repositories pin to.

⛔ **This asserts the manifest matches the prose, never that the prose is right.** Whether an
invariant's text is correct is what `/review-invariants` decides; this only holds the derived copy
to it.

Stdlib only; the generator is loaded by path (INV-108).

Source issue: #88.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "invariant_manifest.py"
MANIFEST = REPO_ROOT / "invariant-manifest.json"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"


def generator():
    spec = importlib.util.spec_from_file_location("invariant_manifest_under_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules["invariant_manifest_under_test"] = module
    spec.loader.exec_module(module)
    return module


class TheManifestIsPresentAndParses(unittest.TestCase):
    """INV-265 — every assertion below reads these, so they must be real."""

    def test_the_generator_and_manifest_exist(self):
        for name, path in (("generator", GENERATOR), ("manifest", MANIFEST)):
            with self.subTest(what=name):
                self.assertTrue(path.is_file(), "%s is missing at %s" % (name, path))

    def test_the_manifest_is_json_with_entries(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertGreater(
            len(data.get("invariants", [])), 200,
            "fewer than 200 invariants in the manifest; the generator has stopped parsing the "
            "prose and every assertion below would pass over a stub")


class ItDoesNotDriftFromTheProse(unittest.TestCase):
    def test_the_checked_in_file_matches_a_fresh_generation(self):
        """⛔ The whole point: a derived file nobody regenerates is a second source of truth."""
        fresh = generator().render(generator().build())
        self.assertEqual(
            fresh, MANIFEST.read_text(encoding="utf-8"),
            "invariant-manifest.json does not match specs/INVARIANTS.md. Regenerate it:\n"
            "  python3 .claude/skills/review-invariants/invariant_manifest.py")

    def test_every_invariant_in_the_prose_is_in_the_manifest(self):
        """A parser that silently drops entries produces a register with holes."""
        prose = set(re.findall(r"(?m)^- \*\*(INV-\d{3})\*\*\s*—", INVARIANTS.read_text(encoding="utf-8")))
        listed = {e["id"] for e in json.loads(MANIFEST.read_text(encoding="utf-8"))["invariants"]}
        self.assertEqual(
            set(), prose - listed,
            "invariant(s) defined in the prose and absent from the manifest: %s. A child "
            "building its register from this would never know they exist"
            % sorted(prose - listed))
        self.assertEqual(
            set(), listed - prose,
            "invariant(s) in the manifest that the prose does not define: %s"
            % sorted(listed - prose))

    def test_the_count_field_agrees_with_the_entries(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            data["count"], len(data["invariants"]),
            "the manifest's own count disagrees with the entries it carries -- a figure a child "
            "would check its register against")


class WhatCouldNotBeDerivedIsReported(unittest.TestCase):
    """⛔ INV-308 — a derived artifact must say what it could not derive."""

    def test_a_null_summary_is_explained_in_the_manifest_itself(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertRegex(
            data.get("note", ""), r"null.*(?:NOT DERIVABLE|not derivable)",
            "the manifest does not explain that a null summary means undetermined rather than "
            "absent. A child treating null as 'no rule' would under-count its own register, and "
            "the file travels without this docstring")

    def test_status_is_only_ever_one_of_the_three_stated_values(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        allowed = {"active", "superseded", "unclear"}
        seen = {e["status"] for e in data["invariants"]}
        self.assertEqual(
            set(), seen - allowed,
            "unexpected status value(s) %s. The vocabulary is a contract other repositories pin "
            "to; adding a value silently changes what their registers must handle"
            % sorted(seen - allowed))

    def test_unclear_is_used_rather_than_guessing(self):
        """⚠️ The prose writes supersession six ways; guessing would be worse than admitting."""
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        unclear = [e["id"] for e in data["invariants"] if e["status"] == "unclear"]
        self.assertTrue(
            unclear,
            "no entry is marked `unclear`, although the prose carries several supersession "
            "spellings. Either the vocabulary was normalized -- in which case say so here -- or "
            "the generator has started guessing a status it cannot determine")

    def test_a_superseded_entry_names_what_superseded_it(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        bad = [e["id"] for e in data["invariants"]
               if e["status"] == "superseded" and not e["superseded_by"]]
        self.assertEqual(
            [], bad,
            "entr(ies) marked superseded with no successor named: %s. `superseded` is only "
            "assigned from an explicit 'superseded by INV-nnn', so a missing successor means "
            "the status was reached another way" % bad)


class TheTwoGroupingsStaySeparate(unittest.TestCase):
    """⚠️ One key meaning two things is a defect in a schema children pin to."""

    def test_every_entry_has_a_section(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        missing = [e["id"] for e in data["invariants"] if not e["section"]]
        self.assertEqual([], missing, "entr(ies) under no heading: %s" % missing)

    def test_the_section_is_not_the_subject_index_subheading(self):
        """⛔ Found by reading the emitted JSON: 259 of 309 had the wrong parent heading."""
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        wrong = [e["id"] for e in data["invariants"] if e["section"] == "Index by subject"]
        self.assertEqual(
            [], wrong,
            "%d entr(ies) report the subject index as their section. It is a sub-heading of the "
            "section that actually contains them, so taking the nearest heading of any level "
            "gives the wrong parent" % len(wrong))

    def test_entries_outside_the_subject_index_are_still_grouped(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        ungrouped = [e for e in data["invariants"] if not e["index_group"]]
        self.assertTrue(
            ungrouped,
            "every entry now has an index group. If the index genuinely grew to cover the "
            "foundational invariants, this assertion should be replaced rather than deleted")
        self.assertTrue(
            all(e["section"] for e in ungrouped),
            "an entry in no index group also has no section, so it is ungrouped in both "
            "dimensions and a child has nothing to file it under")


if __name__ == "__main__":
    unittest.main()
