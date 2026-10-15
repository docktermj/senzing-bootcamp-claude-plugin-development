"""On a why response the whole `MATCH_*` family is renamed `WHY_*` — not just the details object.

Module 7 warned, twice and correctly, that the match-key breakdown is `WHY_KEY_DETAILS` and not
`MATCH_KEY_DETAILS`. By naming only the *details object* as differently named, those warnings
implicitly reassured the reader that its neighbors were not. They are:

    WHY_RESULTS[].MATCH_INFO.MATCH_LEVEL_CODE   (string)
    WHY_RESULTS[].MATCH_INFO.WHY_ERRULE_CODE    (string)
    WHY_RESULTS[].MATCH_INFO.WHY_KEY            (string)
    WHY_RESULTS[].MATCH_INFO.WHY_KEY_DETAILS    (object)

`MATCH_KEY` and `ERRULE_CODE` are real names on the **entity** side — `RESOLVED_ENTITY.RECORDS[]` and
`RELATED_ENTITIES[]` — and appear nowhere under `WHY_RESULTS[]`. Confirmed from the route that owns
the shape: `get_sdk_reference(topic='response_schemas', filter='why_entities', language='python')`,
the document shared by `why_entities`, `why_records` and `why_record_in_entity`, **server 1.33.0,
2026-08-21**.

A `why_explain` program was written with `MATCH_KEY`/`ERRULE_CODE` out of entity-side habit and
caught only because Module 7 separately mandates reading `response_schemas` before parsing (INV-115).
Uncaught, all three fields render blank with no error — the silent failure the surrounding guidance
exists to prevent, one field over from where it pointed.

⚠️ **The rule this file enforces is a co-occurrence rule, not a spelling rule.** Anywhere shipped
prose introduces `WHY_KEY_DETAILS` *as the why-side name*, it must also name the two sibling scalars —
otherwise the reader is told the family diverges and shown one member of it. Sites that merely
reference the object in passing are exempt; the trigger is the naming/contrast context.

Source spec: `specs/why-match-info-scalars-are-why-key-and-why-errule-code.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

#: The two files that warn, and that a parser gets written from.
PHASE1 = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
PHASE2 = PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase2-discover.md"

#: A site is "naming the divergence" when it contrasts the why-side name with the entity-side one.
CONTRAST = re.compile(r"(?i)MATCH_KEY_DETAILS|entity-side|`MATCH_\*` family")


def squash(p):
    return re.sub(r"\s+", " ", p.read_text(encoding="utf-8"))


def region(path, start_marker, end_marker):
    """The specific warning block, not the whole file.

    ⛔ **Scoped deliberately, and the first version of this file was not.** A file-wide
    ``assertIn("`WHY_ERRULE_CODE`", text)`` passed with the token deleted from the warning,
    because ``phase2-discover.md`` also lists it among the raw ``MATCH_INFO`` keys observed on
    a flag probe further down. The mutation test caught the guard, not the prose — which is the
    whole reason to run one. Assert against the block that has to carry the names.
    """
    text = path.read_text(encoding="utf-8")
    i = text.index(start_marker)
    j = text.index(end_marker, i)
    return re.sub(r"\s+", " ", text[i:j])


#: The step-4b.3 field enumeration: the one full statement of the rename (INV-300).
#:
#: ⚠️ Until #611 this also held Module 7 step 3a's ⛔ in `phase1-query-visualize.md`, which
#: carried a second full copy with its own route and stamp. That copy is now a pointer to
#: step 4b.3, and `ThePhase1SiteIsAPointer` below checks it as one.
REGIONS = {
    "phase2-discover.md": lambda: region(
        PHASE2,
        "**The why-key breakdown is `WHY_KEY_DETAILS`.**",
        "⛔ **`WHY_KEY_DETAILS` may need"),
}


def phase1_pointer():
    """Module 7 step 3a's ⛔ about the rename, which points at step 4b.3 (#611)."""
    return region(
        PHASE1,
        "⛔ **(INV-115) And the rename is the whole `MATCH_*` family",
        '<a id="recall-question"></a>')


class TheScanIsNotVacuous(unittest.TestCase):
    def test_both_files_exist(self):
        for p in (PHASE1, PHASE2):
            with self.subTest(file=p.name):
                self.assertTrue(p.is_file(), "%s moved" % p.name)

    def test_both_files_still_name_the_details_object(self):
        """If they stopped mentioning it, every co-occurrence check below passes trivially."""
        for p in (PHASE1, PHASE2):
            with self.subTest(file=p.name):
                self.assertIn("WHY_KEY_DETAILS", squash(p),
                              "%s no longer mentions WHY_KEY_DETAILS, so this scan asserts "
                              "nothing" % p.name)


class BothWarningsNameTheSiblingScalars(unittest.TestCase):
    """Negative-controlled 2026-08-21, and the first two attempts are worth recording.

    Attempt 1 mutated the prose and this file still passed, because it scanned whole files and
    ``phase2-discover.md`` names ``WHY_ERRULE_CODE`` again further down, among the raw
    ``MATCH_INFO`` keys from a flag probe. Scoping to the block fixed the guard.

    Attempt 2 then *also* passed — because the same block names the scalar **twice** (once in the
    bullet header, once in the field enumeration) and the mutation removed only one. That is the
    guard behaving correctly: the block still carried the fact. Removing both occurrences fails it,
    as does removing the entity-side contrast from ``phase1``. Two attempts that pass for two
    different reasons is exactly why "I wrote a mutation test" is not the same claim as "the
    mutation landed".
    """

    def test_each_warning_names_why_key_and_why_errule_code(self):
        for name, get in REGIONS.items():
            with self.subTest(file=name):
                text = get()
                # Match the FIELD, however it is qualified: bare `WHY_KEY` or the fully
                # qualified `WHY_RESULTS[].MATCH_INFO.WHY_KEY`. The trailing backtick is what
                # keeps this from matching `WHY_KEY_DETAILS`. Other guards in this repo require
                # the full dotted path at these sites, so pinning the bare form would put two
                # guards in direct conflict over the same sentence.
                self.assertRegex(
                    text, r"WHY_KEY`",
                    "%s names WHY_KEY_DETAILS as the why-side name without naming WHY_KEY in the "
                    "same block, so a reader is told the family diverges and shown one member "
                    "of it" % name)
                self.assertRegex(
                    text, r"WHY_ERRULE_CODE`",
                    "%s does not name WHY_ERRULE_CODE, the second renamed scalar" % name)

    def test_each_warning_names_the_entity_side_names_that_are_absent(self):
        """Naming the trap is what makes the habit visible; the fix alone does not."""
        for name, get in REGIONS.items():
            with self.subTest(file=name):
                text = get()
                self.assertIn(
                    "`MATCH_KEY`", text,
                    "%s does not name MATCH_KEY as the entity-side counterpart, so the reader "
                    "cannot see which habit produces the error" % name)
                self.assertIn(
                    "`ERRULE_CODE`", text,
                    "%s does not name ERRULE_CODE as the entity-side counterpart" % name)

    def test_each_carries_its_route_version_and_date(self):
        """A field-set claim is not the plugin's to assert (INV-080)."""
        for name, get in REGIONS.items():
            with self.subTest(file=name):
                text = get()
                self.assertIn(
                    "topic='response_schemas', filter='why_entities'", text,
                    "%s asserts the why-side field set without naming the route that "
                    "establishes it" % name)
                self.assertRegex(
                    text, r"1\.33\.0,\s*\*?\*?2026-08-21",
                    "%s carries no server version and date for the field set" % name)

    def test_the_divergence_is_stated_as_the_whole_family(self):
        """The defect was scope: one member documented, the family not.

        The phase1 pointer still names the subject in these words, so a reader of step 3a
        is not told the rename is about the details object alone (#611).
        """
        for name, text in (("phase2-discover.md", REGIONS["phase2-discover.md"]()),
                           ("phase1-query-visualize.md", phase1_pointer())):
            with self.subTest(file=name):
                self.assertRegex(
                    text,
                    r"(?i)rename is the whole `MATCH_\*` family, not just th(?:at|e) details "
                    r"object",
                    "%s frames the rename as being about the details object alone" % name)


class ThePhase1SiteIsAPointer(unittest.TestCase):
    """#611: step 3a points at step 4b.3's one statement instead of carrying a copy (INV-300).

    The copy it replaced carried its own route and stamp, and its WHY_KEY_DETAILS half had
    drifted to a different stamp from step 4b.3's. A pointer that restates the field set
    would start that drift again, so the field names and the stamp must not come back here.
    """

    def test_it_names_the_owning_step_and_the_invariant(self):
        text = phase1_pointer()
        self.assertIn("`phase2-discover.md` step 4b.3", text)
        self.assertIn("INV-300", text)

    def test_it_carries_no_second_copy(self):
        text = phase1_pointer()
        for token in ("`WHY_ERRULE_CODE`", "`ERRULE_CODE`", "`MATCH_KEY`", "requires_flags",
                      "2026-08-21", "MCP-NEGATIVE"):
            with self.subTest(token=token):
                self.assertNotIn(token, text,
                                 "the step 3a pointer restates %s, a part of the rule step "
                                 "4b.3 states once" % token)

    def test_the_moved_negative_marker_sits_with_the_statement(self):
        """The MCP-NEGATIVE comment that explains the rename moved with it."""
        self.assertIn("no MATCH_KEY, ERRULE_CODE or MATCH_KEY_DETAILS field appears under "
                      "WHY_RESULTS[]", REGIONS["phase2-discover.md"]())
        self.assertNotIn("no MATCH_KEY, ERRULE_CODE or MATCH_KEY_DETAILS field appears",
                         squash(PHASE1))


class NoThirdSiteRepeatsTheRule(unittest.TestCase):
    """INV-179's state-it-once discipline, which the surrounding flag caveat already follows."""

    def test_only_the_two_warning_sites_contrast_the_names(self):
        offenders = []
        for p in sorted(PLUGIN.rglob("*.md")):
            if p in (PHASE1, PHASE2):
                continue
            text = squash(p)
            if "WHY_KEY_DETAILS" in text and "`WHY_ERRULE_CODE`" in text and CONTRAST.search(text):
                offenders.append(str(p.relative_to(REPO_ROOT)))
        self.assertEqual(
            [], offenders,
            "a third shipped site now states the why-side rename contrast: %s. The rule is "
            "stated once, at the two places a parser gets written; a third copy is what drifts "
            "(INV-179)." % offenders)


if __name__ == "__main__":
    unittest.main()
