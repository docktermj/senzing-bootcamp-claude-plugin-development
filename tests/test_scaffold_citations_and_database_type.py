"""Three seam defects a phase-3 dry-run walk found that reading the plugin cannot.

All three are cases where a step's own instruction cannot produce what the step asks for, and
where nothing downstream notices:

1. **Module 2 Step 4 cited one `generate_scaffold` workflow for two different needs.** It asked
   for a script that initializes the engine *and* prints the version, naming only
   `workflow='initialize'`. That workflow's snippets are factory/engine lifecycle plus
   configuration helpers, and **none prints the version**; the version snippet
   (`information/get_version.py`, calling `SzProduct.get_version()`) lives only under
   `workflow='information'`. The same file already carries this warning at Step 8a for a different
   need and cites the workflow correctly at Step 9, so the plugin had one correct use, one fixed
   use, and one still-broken use of the same workflow — the lesson had been recorded as a fact
   about seeding rather than as a rule.

   **Evidence refreshed 2026-08-12 (server 1.32.9), and deliberately de-quantified.** This
   docstring used to say the workflow returns "ten snippets, all under `initialization/`
   (server 1.32.2, 2026-07-29)". Both clauses have since gone false — Python now returns 14 across
   `python/initialization/` and `python/configuration/` — while the conclusion never wavered. The
   inventory varies on two axes, time *and* language (Java returns a smaller set under
   `java/snippets/…`), so no count can be right everywhere for long. What is asserted below is the
   absence of a version printer, which is the load-bearing fact, and
   `NoCountRestatesTheSnippetInventory` now keeps the shipped ⛔ from reacquiring a number.

2. **`generate_scaffold` never inlines code, and its own response advertises a parameter its
   schema does not declare.** The response is a listing (`file_path`, `raw_url`, `size_bytes`,
   `line_count`) with no source text, yet several steps said "save the generated code" as though
   code arrived. Worse, `access_steps` step 3 says verbatim *"call again with … inline=true"* while
   the tool's declared schema has only `language`, `version` and `workflow`. That is INV-160's
   trap — recorded there for `find_examples` — recurring unrecorded in a sibling tool. An
   undeclared parameter is not a fallback; it is a call that cannot work.

3. **`database_type` was read by two modules and written by none.** Module 4 Step 8b's SQLite
   load-time warning and Module 6's Phase A heads-up both read the key from
   `config/bootcamp_preferences.yaml`; grepping the whole skills tree found those two reads and no
   writer. Both steps treat a missing value as "indeterminate → say nothing", so the warnings could
   never fire, for any database or dataset size. Module 2 Step 7 — where the engine is actually
   chosen — checkpointed to `bootcamp_progress.json` with no specified shape, so there was not even
   a differently-named value to fall back to.

These are asserted against the skill text because that text *is* the deliverable: the guide follows
it literally, and a wrong workflow name or an unwritten key produces no error at the point of use.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"

MODULE_02 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
MODULE_03 = SKILLS / "module-03-system-verification" / "phase1-verification.md"
MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"
MODULE_06 = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"
PREPARATION = SKILLS / "bootcamp-preparation" / "SKILL.md"

# The key both readers use and Module 2 Step 7 must write. One spelling, asserted in one place,
# so a rename cannot drift the writer away from the readers again.
DATABASE_TYPE_KEY = "database_type"
DATABASE_TYPE_VALUES = ("sqlite", "postgresql")


def read(path):
    return path.read_text(encoding="utf-8")


def flat(path):
    """Whitespace-collapsed text with blockquote markers stripped, for phrase matching."""
    text = re.sub(r"(?m)^\s*>\s?", "", read(path))
    return re.sub(r"\s+", " ", text)


def section(path, heading, stop_pattern):
    """The text of one step, from `heading` up to the next matching boundary."""
    text = read(path)
    start = text.index(heading)
    rest = text[start + len(heading):]
    match = re.search(stop_pattern, rest)
    return rest[: match.start()] if match else rest


class Step4CitesTheWorkflowThatCarriesTheVersionSnippet(unittest.TestCase):
    """Item 10: the version print lives under `information`, not `initialize`."""

    def setUp(self):
        self.step4 = section(MODULE_02, "## Step 4: Verify Installation", r"\n## Step 5:")

    def test_it_names_the_information_workflow(self):
        self.assertIn(
            "workflow='information'",
            self.step4,
            "Module 2 Step 4 asks for a version print but never names "
            "generate_scaffold(workflow='information'), the only workflow whose snippets "
            "contain one. Verified live: workflow='initialize' returns initialization/* only.",
        )

    def test_it_still_names_initialize_for_the_engine_half(self):
        """Both halves are needed — this must not become a swap."""
        self.assertIn("workflow='initialize'", self.step4)

    def test_it_says_initialize_alone_is_insufficient(self):
        flat_step = re.sub(r"\s+", " ", self.step4)
        self.assertRegex(
            flat_step,
            r"(?i)workflow='initialize'.{0,120}(cannot satisfy|does not|none of them prints)",
            "Step 4 names both workflows but never says why 'initialize' alone is not enough, "
            "so a future edit could drop the second call as redundant:\n" + flat_step[:400],
        )

    def test_the_version_method_is_reachable_from_the_named_snippet(self):
        """The step must point at something that actually prints a version."""
        self.assertRegex(
            re.sub(r"\s+", " ", self.step4),
            r"get_version",
            "Step 4 should name the version call (SzProduct.get_version / get_version.py) so a "
            "guide can tell whether the snippet it fetched is the right one",
        )


class NoCountRestatesTheSnippetInventory(unittest.TestCase):
    """A count is the half that goes stale while the conclusion stays true.

    Added 2026-08-12 from `refresh-the-initialize-workflow-snippet-count-in-step4`. Step 4's ⛔
    said "ten snippets, every one under `initialization/`" (verified 1.32.2, 2026-07-29). By
    1.32.9 Python returned 14 across two directories, so an editor re-checking the citation —
    which this repo's discipline actively invites — would find the evidence wrong and could
    reasonably infer the warning was obsolete, deleting a ⛔ whose conclusion still holds.

    The inventory is unstable on two axes: it grows over time, and it differs per language in
    both size and path. So the shipped text must describe the snippets' *character* and the
    absence of a version printer, never a number.
    """

    def setUp(self):
        self.step4 = re.sub(
            r"\s+", " ", section(MODULE_02, "## Step 4: Verify Installation", r"\n## Step 5:")
        )

    def test_the_warning_states_no_snippet_count(self):
        self.assertNotRegex(
            self.step4,
            r"(?i)(?:returns|it returns)\s+(?:\*\*)?(?:\d+|one|two|three|four|five|six|seven|"
            r"eight|nine|ten|eleven|twelve|thirteen|fourteen)(?:\*\*)?\s+snippets",
            "Step 4's warning states a snippet count. The set grows over time and differs per "
            "language, so the number is wrong somewhere as soon as it is written — describe the "
            "snippets' character and the absence of a version printer instead",
        )

    def test_the_absence_is_named_as_the_load_bearing_fact(self):
        self.assertRegex(self.step4, r"(?i)none of them prints the version")
        self.assertRegex(self.step4, r"(?i)\*\*absence\*\* is the load-bearing fact")

    def test_the_stamp_is_present_so_the_claim_stays_re_checkable(self):
        """De-quantified is not undated: a reader must know when this was last asked."""
        self.assertRegex(self.step4, r"server 1\.32\.\d+, 20\d\d-\d\d-\d\d")

    def test_the_instability_is_explained_so_a_count_is_not_helpfully_restored(self):
        self.assertRegex(self.step4, r"(?i)differs per language")
        self.assertRegex(self.step4, r"(?i)widened over time")


class NoSkillAdoptsAnUndeclaredScaffoldParameter(unittest.TestCase):
    """Item 11 / INV-160: an undeclared parameter is not a fallback.

    `generate_scaffold`'s declared schema is `language`, `version`, `workflow`. Its own
    `access_steps` advertises `inline=true` anyway. No skill may adopt it — and the ones that
    save scaffold output must say the response is a listing needing a fetch.
    """

    SCAFFOLD_SKILLS = (MODULE_02, MODULE_03)

    def test_no_skill_instructs_passing_inline_true(self):
        for path in (*self.SCAFFOLD_SKILLS, MODULE_04, MODULE_06, PREPARATION):
            with self.subTest(skill=path.name):
                text = flat(path)
                for offender in re.finditer(r"inline\s*=\s*true", text, re.I):
                    window = text[max(0, offender.start() - 200): offender.end() + 60]
                    self.assertRegex(
                        window,
                        r"(?i)(never|not|no such|undeclared|cannot work|forbid)",
                        f"{path.name} mentions inline=true without marking it forbidden. The "
                        "parameter is undeclared in generate_scaffold's schema (INV-160), so a "
                        f"bare mention reads as permission:\n...{window}...",
                    )

    def test_steps_that_save_scaffold_output_say_it_must_be_fetched(self):
        for path in self.SCAFFOLD_SKILLS:
            with self.subTest(skill=path.name):
                text = flat(path)
                self.assertRegex(
                    text,
                    r"(?i)(returns a \*\*listing\*\*|returns a listing)",
                    f"{path.name} calls generate_scaffold and saves the result, but never says "
                    "the response is a listing with no source text — so a guide waits for code "
                    "that never arrives, or reconstructs it from memory (INV-080).",
                )
                # #565: the hosted `url` now leads `access_steps`, so a site names both URL
                # fields and fetches by the response's own steps rather than by `raw_url`.
                self.assertRegex(
                    text,
                    r"`url`, `raw_url`",
                    f"{path.name} should name the hosted `url` beside `raw_url` in the listing",
                )
                self.assertRegex(
                    text,
                    r"(?i)by the response's own `access_steps`",
                    f"{path.name} should fetch by the response's own access_steps (#565)",
                )


class TheFullPipelineFileChoiceIsSpecified(unittest.TestCase):
    """Item 11b: `full_pipeline` returns many files and the wrong pick breaks a LATER step.

    Verified live (server 1.32.2, 2026-07-29): 18 snippets for Python, including both
    `loading/add_records.py` (records hardcoded in source) and `loading/add_records_loop.py`
    (reads an input file). Both satisfy Step 4's structural checks; only the second can satisfy
    Step 6, which executes the file "pointing it at" a data path.
    """

    def setUp(self):
        self.step4 = section(MODULE_03, "### Step 4: Code Generation", r"\n\*\*Checkpoint:\*\*")

    def test_it_says_the_response_holds_many_files(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.step4),
            r"(?i)(MANY files|18 of them|not \"the\" generated script)",
            "Step 4 says 'save the generated code' as though full_pipeline returned one file",
        )

    def test_it_requires_the_file_reading_snippet(self):
        flat_step = re.sub(r"\s+", " ", self.step4)
        self.assertRegex(
            flat_step,
            r"(?i)READS AN INPUT FILE|reads its records from an external file",
            "Step 4 must require the loader that reads an input file, since Step 6 points the "
            "script at a data path and the hardcoded demo has no file argument",
        )
        self.assertIn("add_records_loop", flat_step)
        self.assertIn("add_records.py", flat_step)

    def test_it_warns_the_structural_checks_cannot_tell_them_apart(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.step4),
            r"(?i)satisfied by \*?any\*? file|any file in the returned set",
            "Without this, the three structural checks read as sufficient — they are what let "
            "the wrong file through",
        )

    def test_it_says_to_override_the_hardcoded_input_path(self):
        self.assertRegex(
            re.sub(r"\s+", " ", self.step4),
            r"(?i)INPUT_FILE|hardcoded input path",
            "The snippet ships a path that does not exist in a bootcamp project; Step 6 crashes "
            "unless it is overridden",
        )


class DatabaseTypeHasAWriterAndBothReadersAgree(unittest.TestCase):
    """Item 13: one key, one spelling, written where it is chosen and read where it is needed."""

    READERS = (MODULE_04, MODULE_06)

    def test_module_2_step_7_writes_the_key(self):
        step7 = section(MODULE_02, "## Step 7:", r"\n## Step 8:")
        self.assertIn(
            DATABASE_TYPE_KEY,
            step7,
            "Module 2 Step 7 is where the engine is chosen and the only place that can record "
            f"it, but it never writes {DATABASE_TYPE_KEY!r} — leaving both readers with nothing, "
            "which silently disables two SQLite warnings entirely.",
        )
        self.assertIn(
            "bootcamp_preferences.yaml",
            step7,
            "the key must be written to the file the readers actually read",
        )

    def test_the_write_names_both_values(self):
        step7 = section(MODULE_02, "## Step 7:", r"\n## Step 8:")
        for value in DATABASE_TYPE_VALUES:
            with self.subTest(value=value):
                self.assertIn(
                    value,
                    step7,
                    f"Step 7 must state the {value!r} spelling; the readers compare against it",
                )

    def test_both_readers_use_the_same_key_name(self):
        for path in self.READERS:
            with self.subTest(reader=path.name):
                self.assertIn(DATABASE_TYPE_KEY, read(path))

    def test_the_key_appears_nowhere_under_a_variant_spelling(self):
        """A near-miss rename is the same failure as no writer at all."""
        variants = (r"database-type", r"databaseType", r"db_type", r"database_engine")
        for path in (MODULE_02, *self.READERS):
            for variant in variants:
                with self.subTest(file=path.name, variant=variant):
                    self.assertNotRegex(
                        read(path),
                        variant,
                        f"{path.name} uses {variant!r} alongside {DATABASE_TYPE_KEY!r}; the "
                        "writer and readers must agree on exactly one spelling",
                    )

    def test_both_readers_treat_an_absent_key_as_a_defect_not_an_answer(self):
        """"Missing" must not silently mean "not SQLite" — that is how the warning vanished."""
        for path in self.READERS:
            with self.subTest(reader=path.name):
                self.assertRegex(
                    flat(path),
                    r"(?i)absent `?database_type`? is a recording failure|"
                    r"If `?database_type`? is absent, say so",
                    f"{path.name} falls through to 'say nothing' when the key is missing, which "
                    "is indistinguishable from a non-SQLite engine",
                )


class TheLanguageLookupGoesToTheToolThatCarriesIt(unittest.TestCase):
    """Item 2: `sdk_guide` returns install detail and no language list; `get_capabilities` does."""

    def test_preparation_names_get_capabilities(self):
        self.assertRegex(
            flat(PREPARATION),
            r"(?i)Call \*\*`get_capabilities`\*\* on the Senzing MCP server for the supported "
            r"programming languages",
            "Bootcamp preparation must route the supported-languages lookup to get_capabilities",
        )

    def test_it_no_longer_routes_that_lookup_to_sdk_guide(self):
        self.assertNotRegex(
            flat(PREPARATION),
            r"(?i)`get_capabilities` or `sdk_guide`.{0,80}supported programming languages",
            "the lookup is still offered to sdk_guide, which carries no language list",
        )

    def test_it_says_the_language_set_is_platform_independent(self):
        self.assertRegex(
            flat(PREPARATION),
            r"(?i)platform-independent",
            "'on that platform' mis-framed the fact: there is no per-platform language list",
        )

    def test_the_per_platform_annotation_rules_are_preserved(self):
        """The spec requires the surrounding rules stay unchanged."""
        text = flat(PREPARATION)
        self.assertRegex(text, r"(?i)Present the MCP-returned options as a \*\*numbered list\*\*")
        self.assertRegex(text, r"(?i)Always say \"\*\*programming language\*\*\"")


if __name__ == "__main__":
    unittest.main()
