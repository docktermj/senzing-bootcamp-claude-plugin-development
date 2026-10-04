"""Two prerequisite gaps in SDK setup, both on paths the module recommends or predicts.

**SQLite said "no additional setup needed".** It is option 1, *recommended for learning and
evaluation*, so essentially every bootcamper takes it — and the database file is not
auto-created and its schema is not auto-applied. The step created `database/`, named the path,
and stopped. A bootcamper following it reached Step 9 with no database at all and got
`SENZ1001|Critical Database Error '(14:unable to open database file)'`. The plugin already did
this correctly for PostgreSQL, which states outright that the SDK does not auto-create the
schema; the recommended branch had no equivalent rung. Step 8a then compounded it, since its
premise is "a datastore you just schema-created" — a state the SQLite path never reached.
(`specs/sqlite-branch-says-no-additional-setup-but-the-schema-is-required.md`)

**Skipping Step 3 on an existing install skipped the env script.** Step 3 is titled "Install
Senzing SDK" and does two jobs: it installs, and it writes `src/scripts/senzing-env.sh`. Only
the first is redundant when Senzing is already installed; the second is the thing an existing
install is most likely to be missing. Step 1 itself predicts that state — its filesystem
fallback exists because the import check fails with `PYTHONPATH` unset on a working install —
and then routed past the step that would have fixed it.
(`specs/skipping-step-3-on-an-existing-install-skips-the-env-script.md`)

Both facts are the server's: `sdk_guide(topic='install', platform='linux_apt',
language='python')` returns the schema requirement in `install.platform.post_install[]` and
`install.engine_config_notes[]`, and the two environment variables in
`install.platform.env_vars` (re-verified MCP server 1.32.9, 2026-08-14).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_02 = (REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-02-sdk-setup"
             / "SKILL.md")


def read():
    return MODULE_02.read_text(encoding="utf-8")


def section(text, start_heading, end_heading):
    """The text between two headings. Scoping matters: several claims in this module are
    stated in more than one place, so a file-wide assertion can pass with the one at the
    step deleted."""
    start = text.index(start_heading)
    end = text.find(end_heading, start + len(start_heading))
    return text[start:end if end != -1 else len(text)]


def squash(text):
    """Whitespace-collapsed, with blockquote markers stripped first.

    The required-stops list is a blockquote, so a wrapped sentence inside it reads as
    "… because no > install ran …" once whitespace alone is collapsed — `>` is not
    whitespace. Strip the line-leading markers before collapsing, or every assertion
    about that list has to encode the wrapping.
    """
    return re.sub(r"\s+", " ", re.sub(r"^[ \t]*>[ \t]?", "", text, flags=re.M))


def is_marker_line(line):
    """A line that opens with a negative marker, wrapped `<!-- … -->` or not.

    Line-scoped by design (#424): INV-209 requires the marker on ONE line.

    #323 wraps Step 8's marker in an HTML comment, so the line now opens with `<!-- `; a
    bare marker still counts here, and `tests/test_shipped_negative_markers_are_html_comments.py`
    is what rejects it. The prefix is assembled rather than written out: the marker scanner
    reads `tests/` too.
    """
    s = line.lstrip()
    if s.startswith("<!-- "):
        s = s[len("<!-- "):]
    return s.startswith("MCP-" + "NEGATIVE:")


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_module_exists(self):
        self.assertTrue(MODULE_02.is_file(), "module-02 SKILL.md moved")

    def test_the_database_question_is_still_there(self):
        self.assertIn("👉 **Which database would you like to use? Reply with a number:**", read(),
                      "Step 7's database gate moved; the SQLite branch may have too")


class TheSqliteBranchStatesItsThreeRungs(unittest.TestCase):
    def setUp(self):
        self.text = read()
        self.flat = squash(self.text)

    def test_the_no_setup_claim_is_gone(self):
        self.assertNotIn("No additional setup needed: SQLite is built in", self.flat,
                         "the SQLite branch still claims it needs no setup")
        self.assertRegex(
            self.flat, r"(?i)SQLite is not \"no setup\"",
            "nothing contradicts the claim the branch used to make")

    def test_it_requires_the_schema(self):
        self.assertRegex(
            self.flat, r"(?i)\*\*Apply the Senzing schema\*\* to `database/G2C\.db`",
            "the schema rung is missing")
        self.assertRegex(
            self.flat, r"(?i)required\*?\*? when using `senzingsdk-setup`",
            "the server's condition on the schema step is not relayed, so a reader may "
            "think the poc package's behavior applies")

    def test_the_schema_path_comes_from_the_server(self):
        self.assertRegex(
            self.flat,
            r"(?i)Get the schema file's path from\s*`sdk_guide\(topic='install', platform="
            r"'<platform>'\)` rather than hardcoding it \(INV-080\)",
            "the schema path is hardcoded rather than routed through sdk_guide")

    def test_the_schema_is_applied_through_python_not_a_cli(self):
        """INV-001: Windows ships no sqlite3 binary; Python 3 is already required."""
        self.assertIn("import sqlite3,sys;", self.text,
                      "the cross-platform Python form is missing")
        self.assertRegex(
            self.flat, r"(?i)Apply it with Python, not the `sqlite3` CLI",
            "nothing says not to use the CLI the server illustrates")
        self.assertRegex(
            self.flat, r"(?i)Windows is a supported platform \(INV-001\) and\s*ships no `sqlite3`",
            "the reason the CLI is unsuitable is not given")

    def test_the_path_stays_in_the_project(self):
        """INV-200: never the server's /tmp/sqlite/G2C.db."""
        self.assertRegex(
            self.flat, r"(?i)override the path to `database/G2C\.db`",
            "the /tmp override rule was lost")
        self.assertRegex(
            self.flat, r"(?i)\*\*including in the schema command\s*above\*\*",
            "the override is not extended to the schema command, which is where the "
            "server's /tmp example would otherwise be copied")

    def test_the_connection_string_must_be_absolute(self):
        self.assertRegex(
            self.flat, r"(?i)The `SQL\.CONNECTION` path must be ABSOLUTE",
            "the absolute-path requirement is missing")
        self.assertRegex(
            self.flat, r"(?i)from any working directory, including the project root",
            "a reader could still think a cd fixes it")
        self.assertRegex(
            self.flat, r"(?i)it tries to open\s*\*\*`/G2C\.db`\*\*",
            "the mechanism is not given, so the rule reads as folklore")
        self.assertRegex(
            self.flat, r"(?i)INV-200-compatible",
            "the apparent tension with INV-200 is not resolved")

    def test_the_two_error_codes_are_distinguished(self):
        self.assertRegex(
            self.flat,
            r"(?i)SENZ7220\|No engine configuration registered in datastore",
            "the post-schema state is not named")
        self.assertRegex(
            self.flat,
            r"(?i)`SENZ1001 \(14: unable to open database file\)` means rung 2 has \*\*not\*\* "
            r"been done",
            "SENZ1001 is not tied to the missing schema, so it gets diagnosed as "
            "permissions or path")


class StepEightAAppliesToBothBranches(unittest.TestCase):
    def setUp(self):
        self.flat = squash(read())

    def test_it_says_schema_created_covers_sqlite(self):
        self.assertRegex(
            self.flat,
            r'(?i)"Schema-created" is true of BOTH database branches',
            "Step 8a's premise still only holds for PostgreSQL")
        self.assertRegex(
            self.flat, r"szcore-schema-sqlite-create\.sql",
            "the SQLite schema file is never named in the module")

    def test_it_routes_an_unschemaed_arrival_back(self):
        self.assertRegex(
            self.flat, r"(?i)this step cannot help — go back and apply it",
            "arriving at 8a without the schema is not handled, and 8a cannot fix it")


class TheEnvScriptSurvivesTheSkip(unittest.TestCase):
    def setUp(self):
        self.text = read()
        self.flat = squash(self.text)

    def test_step_1_no_longer_skips_step_3_entirely(self):
        self.assertNotIn("- Skip Steps 2 and 3 entirely.", self.text,
                         "the skip instruction still discards Step 3's environment work")

    def test_step_1_names_installation_as_what_is_skipped(self):
        self.assertRegex(
            self.flat,
            r"(?i)Skip the \*?\*?installation\*?\*? — Step 2, and Step 3's install commands",
            "the skip instruction does not say what is being skipped")
        self.assertRegex(
            self.flat, r"(?i)Not Step 3 entirely",
            "nothing contradicts the old reading")

    def test_step_1_directs_the_env_script_work(self):
        self.assertRegex(
            self.flat, r"(?i)Still do Step 3's environment-script work",
            "the skip path never reaches the env script")

    def test_the_required_stops_list_names_it(self):
        self.assertRegex(
            self.flat,
            r"(?i)\*\*Step 3's environment script\*\* \(`src/scripts/senzing-env\.sh`, or "
            r"`senzing-env\.bat` on Windows\)",
            "the required-stops list still names only Step 4 and Step 5")
        self.assertRegex(
            self.flat, r"(?i)the single most likely thing an existing install is missing",
            "the list entry does not say why it is there")

    def test_the_deferred_failure_is_named(self):
        self.assertRegex(
            self.flat, r"(?i)libSz\.so: cannot open shared object file",
            "the symptom is not named, so the cost of skipping reads as bookkeeping")
        self.assertRegex(
            self.flat, r"(?i)Step 1's own fallback predicts exactly this state",
            "the irony that Step 1 predicts the state it causes is the argument, and it "
            "is unstated")

    def test_the_values_come_from_the_server_on_the_skip_path(self):
        self.assertRegex(
            self.flat,
            r"(?i)rather than from an install transcript, because no\s*install ran \(INV-080\)",
            "the skip path does not say where the variable values come from")

    def test_it_reuses_one_implementation(self):
        self.assertRegex(
            self.flat,
            r"(?i)the zsh/bash path-resolution idiom, the fail-loudly root check, and the "
            r"empty-value guard",
            "the skip path may grow a second, weaker env-script implementation")
        self.assertRegex(self.flat, r"(?i)One implementation, not two",
                         "nothing forbids a divergent copy")

    def test_the_required_stops_still_name_steps_4_and_5(self):
        for step in (r"\*\*Step 4\*\* \(Verify Installation\)", r"\*\*Step 5\*\* \(License\)"):
            with self.subTest(step=step):
                self.assertRegex(self.flat, step,
                                 "an existing required stop was lost while adding one")


class StepFourVerifiesTheBindingNotTheEngine(unittest.TestCase):
    """Step 4 asked for an engine three to four steps before the datastore exists.

    On a healthy, current install that cannot succeed: `SzProduct.get_version()` returns the
    version while `create_engine()` raises `SENZ7426`, whose documented remediation is to go
    hunting `SUPPORTPATH`. Reproduced live on Senzing 4.3.4, 2026-08-14. The module's own
    success indicator already put the engine-class call at Step 9.
    (`specs/sdk-setup-step-4-requires-an-engine-before-the-datastore-exists.md`)
    """

    def setUp(self):
        self.text = read()
        self.flat = squash(self.text)
        self.step4 = squash(section(self.text, "## Step 4: Verify Installation",
                                   "## Step 5"))

    def test_step_4_no_longer_initializes_the_engine(self):
        self.assertNotIn(
            "The script should initialize the Senzing engine **and** print the version",
            self.flat,
            "Step 4 still pairs engine initialization with the version print")

    def test_it_says_it_is_a_binding_check(self):
        self.assertRegex(
            self.flat, r"(?i)This step verifies the BINDING, not the engine",
            "Step 4 does not say what it can actually verify")
        self.assertRegex(
            self.flat, r"(?i)\*\*Do not create an engine at this step\.\*\*",
            "nothing forbids the engine call that cannot work here")

    def test_it_defers_to_step_9_and_cites_the_success_indicator(self):
        """⛔ Asserted inside Step 4, not across the file.

        The success indicator's wording also appears at the top of the module, so a
        file-wide assertion passes with Step 4's quote deleted — which is asserting that a
        token exists somewhere rather than that the claim holds where it is made. A
        mutation removing the quote escaped exactly that way.
        """
        self.assertRegex(
            self.step4, r"(?i)an engine-class call\s*\(`SzEngine`/`SzDiagnostic`\) succeeds",
            "Step 4 does not quote the module's own success indicator, so it and Step 4 "
            "can disagree again about where the engine-class call belongs")
        self.assertRegex(
            self.step4, r"(?i)That is\s*\*\*Step 9\*\*'s bar",
            "Step 4 does not name where the engine check happens instead")

    def test_the_expected_failure_codes_are_named_as_expected(self):
        self.assertRegex(
            self.flat,
            r"(?i)`SENZ7426` and `SENZ7220` before Step 7 mean \"not configured\s*yet\"",
            "the two codes are not marked as the expected pre-Step-7 result")
        self.assertRegex(
            self.step4, r"(?i)Do \*\*not\*\* send them through this module's "
                        r"`explain_error_code`",
            "nothing keeps a healthy install out of the SENZ-code error path")
        self.assertRegex(
            self.step4, r"(?i)hunting something that does not exist",
            "the misdirection the error path causes is not stated")
        # ⛔ Where Step 4 touches the SENZ7426/SUPPORTPATH link at all, it must carry the
        # platform condition and name the tool — INV-080/INV-169, enforced across the
        # corpus by tests/test_engine_verification_and_senz2027.py. Asserted here too, so
        # a rewrite of this step cannot quietly drop it and be caught only by that file's
        # first-occurrence window.
        self.assertRegex(
            self.step4, r"sdk_guide\(topic='install', platform='macos_arm' \| 'windows'\)",
            "Step 4 mentions SUPPORTPATH without naming the tool that states the "
            "conditioned form")
        self.assertRegex(
            self.step4, r"(?i)Step 8 covers it\s*properly",
            "Step 4 should defer the real SUPPORTPATH diagnosis rather than restating it")

    def test_step_4_now_makes_one_scaffold_call(self):
        self.assertRegex(
            self.flat, r"(?i)So Step 4 needs \*\*one\*\* `generate_scaffold` call",
            "Step 4 still claims to need two calls")

    def test_the_initialize_evidence_is_preserved_and_relocated(self):
        """Criterion: keep the two-workflow fact where the snippets are actually used."""
        self.assertRegex(
            self.flat,
            r"(?i)`workflow='initialize'` alone cannot satisfy a version check",
            "the ⛔ that initialize prints no version was lost")
        self.assertRegex(
            self.flat,
            r"(?i)still needed — at \*\*Step 8a\*\*.{0,120}and \*\*Step 9\*\*",
            "the initialize call is dropped from Step 4 without saying where it is used")
        for citation in (r"workflow='initialize'\)` reaches the same code",
                         r"workflow='initialize', version='current'\)`\s*to get the current V4"):
            with self.subTest(citation=citation[:40]):
                self.assertRegex(self.flat, citation,
                                 "a downstream initialize citation was lost")


class StepEightStatesThatPlatformIsMandatory(unittest.TestCase):
    """The rule governing the call must be AT the step that makes it (INV-183).

    `sdk_guide` declares `platform` with ``"default": null`` ("Omit to get the platform decision
    tree"), so a call without it **succeeds** and returns no ``environment`` block — no
    ``engine_config`` and no ``default_paths``. Step 8's next instruction is *"Build the JSON
    from `environment.default_paths` … That response carries both"*, which is false against such
    a response, and the step offered no diagnosis: the ⛔ rule lived only in ``## Agent Behavior``,
    **269 lines later**, under a heading a guide executing Step 8 has no reason to have read.
    (`specs/step8-lacks-the-platform-mandatory-rule-that-agent-behavior-carries.md`)

    Re-verified on server **1.32.9, 2026-08-15** by making both calls:
    ``sdk_guide(topic='configure', language='python')`` returned ``code``/``anti_patterns``/
    ``next_steps`` and **no** ``environment`` key; adding ``platform='linux_apt'`` returned
    ``environment.default_paths`` and ``environment.engine_config``.

    ⛔ **Scoped to the Step 8 span, derived from its headings (INV-246).** A file-wide assertion
    would pass with the rule deleted from Step 8 and left in Agent Behavior — which is precisely
    the state this guard exists to forbid.
    """

    #: ⛔ Prose and marker are separated, and negative control is why. Asserting a phrase
    #: against the whole span passed with the PROSE deleted, because the dated negative-marker
    #: line restates the same words — the marker was certifying the sentence it documents, the
    #: same shape as a filename certifying the claim that cites it. Each assertion below now
    #: runs against the half it is actually about.
    #:
    #: The marker prefix is assembled from fragments throughout this class rather than written
    #: out: the marker scanner reads `tests/` too, and a literal here is picked up as an
    #: unparseable marker of this file's own (it turned the suite red twice).
    def setUp(self):
        raw = section(read(), "## Step 8: Create Engine Configuration", "## Step 8a:")
        marker_lines = [l for l in raw.splitlines() if is_marker_line(l)]
        prose_lines = [l for l in raw.splitlines() if not is_marker_line(l)]
        self.step8 = squash(raw)
        self.prose = squash("\n".join(prose_lines))
        self.marker = squash("\n".join(marker_lines))

    def test_the_span_is_really_step_8(self):
        """A mis-derived span would make every assertion below vacuous."""
        self.assertIn("Create Engine Configuration", self.step8)
        self.assertNotIn("Seed the default configuration", self.step8,
                         "the span ran past Step 8 into Step 8a")

    def test_step_8_says_platform_is_not_optional(self):
        self.assertRegex(
            self.prose, r"(?i)`platform` is not optional here",
            "Step 8 does not state that `platform` is mandatory, so the rule is reachable only "
            "from `## Agent Behavior` 269 lines later (INV-183)")

    def test_step_8_says_the_schema_calls_it_optional(self):
        """Without this, a future editor 'corrects' the rule against the schema and is right."""
        self.assertRegex(
            self.prose, r"(?i)even though the schema says it is",
            "Step 8 does not record that the schema declares `platform` optional — the nuance "
            "that stops the rule being read as a mistake and removed")

    def test_step_8_names_what_a_platform_less_response_looks_like(self):
        self.assertRegex(
            self.prose, r"(?i)no `environment` block",
            "Step 8 does not say what comes back when `platform` is omitted, so a guide that "
            "hits it has no local diagnosis — the half that only existed in Agent Behavior")

    def test_the_default_paths_instruction_is_conditioned_on_it(self):
        """The sentence that is FALSE against a platform-less response must carry the proviso."""
        self.assertRegex(
            self.prose, r"(?i)carries both — \*\*provided `platform` was passed\*\*",
            "the `environment.default_paths` instruction no longer states its precondition, so "
            "it again reads as unconditionally true")

    def test_the_absence_claim_carries_its_negative_marker(self):
        """A dated 'the tool does not return X' claim expires undetectably without one.

        ⛔ **The needle is assembled rather than written out**, and not for style: the marker
        scanner reads `tests/` too, so a literal here is picked up as a marker of this file's
        own — one that cannot parse, because a test assertion is not a dated claim. That
        failure is real (hit on first run). The alternative, an `ignore-file` exemption, would
        blind the scanner to this whole guard file if it ever gains a genuine negative.
        """
        marker = "MCP-" + "NEGATIVE:"
        self.assertIn(marker, self.step8,
                      "the platform-less-response claim is a dated tool-absence claim and needs "
                      "a negative marker so `coverage_reports.py negatives` re-asks it")
        self.assertIn("owner:", self.marker,
                      "the marker has no `owner:` clause, so it does not parse (INV-194)")


class StepEightBuildsValidJson(unittest.TestCase):
    """`engine_config` is not valid JSON — every brace in it is doubled.

    So "always use the exact JSON returned by sdk_guide" could not be obeyed: pasting it
    produced a config the SDK cannot parse, and repairing it looked like the manual
    construction the same sentence forbids in bold.
    (`specs/engine-config-returned-by-sdk-guide-is-not-valid-json.md`)
    """

    def setUp(self):
        self.text = read()
        self.flat = squash(self.text)

    def test_the_unfollowable_instruction_is_gone(self):
        self.assertNotIn("Always use the exact JSON", self.flat,
                         "Step 8 still tells the guide to paste a string that does not parse")
        self.assertNotIn("always use the exact JSON", self.flat,
                         "the Agent Behavior list still says it too")

    def test_the_values_are_what_must_come_from_the_server(self):
        self.assertRegex(
            self.flat, r"(?i)NEVER guess the engine-configuration VALUES",
            "the 🚨 no longer says what it is protecting")
        self.assertRegex(
            self.flat, r"(?i)and\s*the connection-string form all come from",
            "the connection-string form is not covered, though it is equally a server fact")

    def test_it_prefers_default_paths(self):
        self.assertRegex(
            self.flat,
            r"(?i)Build the JSON from `environment\.default_paths`, not from the "
            r"`engine_config` blob",
            "the robust source is not named")

    def test_both_corrections_are_named(self):
        self.assertRegex(
            self.flat, r"(?i)It needs two corrections,\s*not one",
            "the step still implies one correction")
        self.assertRegex(
            self.flat, r"(?i)Every brace in it is doubled \(`\{\{` … `\}\}`\)",
            "the brace escaping is not described")
        self.assertRegex(
            self.flat, r"(?i)`SQL\.CONNECTION` is `/tmp/sqlite/G2C\.db`\*\*, which INV-200 forbids",
            "the /tmp half of the correction is not stated at this step")

    def test_the_observation_is_dated_with_its_server_version(self):
        self.assertRegex(
            self.flat, r"(?i)Observed on \*\*MCP server 1\.32\.9, 2026-08-14\*\*",
            "a server-side rendering bug is asserted with no version or date, so a future "
            "reader cannot tell whether it is still true")
        self.assertRegex(
            self.flat, r"(?i)If it has been fixed upstream",
            "no route is given for the case where the server is repaired")

    def test_repairing_it_is_distinguished_from_manual_construction(self):
        self.assertRegex(
            self.flat, r"(?i)is \*\*not\*\* the manual construction the 🚨 forbids",
            "the contradiction that made the old wording unfollowable is not resolved")

    def test_the_senz2027_material_survives(self):
        self.assertRegex(
            self.flat, r"(?i)SENZ2027 when SUPPORTPATH is wrong",
            "the failure the 🚨 exists to prevent was lost in the rewording")


class TheTroubleshootingNoteHandlesAnAbsentScript(unittest.TestCase):
    def setUp(self):
        self.flat = squash(read())

    def test_it_checks_existence_before_sourcing(self):
        self.assertRegex(
            self.flat,
            r"(?i)\*\*First check whether\s*the script exists at all\*\*",
            "the note still asks whether an absent file was sourced")

    def test_it_says_what_to_do_when_absent(self):
        self.assertRegex(
            self.flat, r"(?i)that \*\*is\*\* the finding: write it now per Step 3's",
            "an absent script is detected but not remedied")

    def test_the_zsh_advice_survives(self):
        self.assertRegex(
            self.flat, r"(?i)a `\$\{BASH_SOURCE\[0\]\}`-based script computes the wrong root",
            "the original zsh finding was lost while adding the existence check")


if __name__ == "__main__":
    unittest.main()
