"""SDK verification must exercise an engine, and SENZ7426 must not be tied to SUPPORTPATH.

Module 2's Step 9 said "engine initializes and connects without errors" but never pinned
which SDK class the check must touch, so a probe that only proves the SDK imports and
reports its version satisfied the wording. That matters because the libraries and their
support data can be present independently — the Senzing FAQ, verified on MCP server
1.32.1 (2026-07-28):

    I get SENZ2027 Plugin initialization error GNR data files failed to load — You are
    missing the senzingsdk-runtime data directory. The libraries are present but the GNR
    data files (in resources/data/) are not deployed.

So a wrong SUPPORTPATH can pass a version query and fail at the first real engine call,
several steps later.

⛔ These tests also pin a RETRACTION. The feedback entry behind this work claimed the
failing code is SENZ7426 rather than the documented SENZ2027, and the first version of
the spec asked for the plugin's symptom code to be broadened accordingly. Re-verified
2026-07-28: explain_error_code('SENZ7426') returns EAS_ERR_XLITERATOR_FAILED
(Transliteration failed) with input-data causes, and nothing in any MCP source connects
it to SUPPORTPATH — while SENZ2027 (EAS_ERR_PLUGIN_INIT) IS the documented
missing-support-data symptom. Implementing the original claim would have written a false
Senzing fact into the plugin (INV-080/INV-169), so `test_senz7426_is_never_tied_to_supportpath`
exists to stop it being reintroduced.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE_02 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"
PHASE1 = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"
SKILLS = PLUGIN / "skills"


def flat(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


def has_inv_169_warning(block):
    """Step 3b's guard against restating the SUPPORTPATH link as an unconditioned rule."""
    return bool(re.search(r"⛔ Never restate this as an unconditioned rule \(INV-169\)", block))


def unconditioned_er_data(text, window):
    """Offsets of each `er/data` with no 4.4.x condition within `window` characters."""
    return [
        match.start() for match in re.finditer(r"er/data", text)
        if not re.search(r"4\.4\.x",
                         text[max(0, match.start() - window):match.end() + window])
    ]


def owner_block():
    """Module 2 Step 8's two-tool SENZ7426 block, from its title to the next ⚠️ paragraph."""
    match = re.search(
        re.escape(TheModule03Senz7426BranchIsAPointer.OWNER_TITLE) + r".*?(?=⚠️)",
        flat(MODULE_02),
    )
    assert match, "Module 2 Step 8's two-tool SENZ7426 block was not found"
    return match.group(0)


def says_test_the_path(block):
    """The block tells the reader to test whether SUPPORTPATH resolves, not match a string."""
    return bool(re.search(
        r"(?i)test whether `SUPPORTPATH` resolves rather than compare it to a string", block
    ))


class VerificationExercisesAnEngine(unittest.TestCase):
    def test_step_9_requires_an_engine_class_call(self):
        self.assertRegex(
            flat(MODULE_02),
            r"(?i)MUST create and use an `SzEngine` \(or `SzDiagnostic`\) — not only `SzProduct`",
        )

    def test_it_says_why_a_version_query_is_insufficient(self):
        text = flat(MODULE_02)
        self.assertRegex(text, r"(?i)version query proves the library loaded")
        self.assertRegex(text, r"(?i)present independently")

    def test_both_success_indicators_exclude_a_version_probe(self):
        text = flat(MODULE_02)
        self.assertRegex(text, r"(?i)a version query alone does not qualify")
        self.assertRegex(
            text, r"(?i)proven by an `SzEngine`/`SzDiagnostic` call rather than a version query"
        )

    def test_the_code_still_comes_from_mcp(self):
        """INV-080: constrain the class touched, not where the code comes from."""
        text = flat(MODULE_02)
        self.assertRegex(text, r"generate_scaffold\(workflow='initialize'\)")
        self.assertRegex(text, r"(?i)[Dd]o not hand-write it")

    def test_module_03_checks_engine_initialization_before_loading(self):
        text = PHASE1.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^### Step 1a: Engine Initialization Check")
        self.assertLess(text.index("Step 1a: Engine Initialization"),
                        text.index("Step 2: Generate Synthetic Verification Records"))

    def test_module_03_stops_rather_than_loading_on_failure(self):
        self.assertRegex(
            flat(PHASE1), r"(?i)stop here rather than proceeding to generation or loading"
        )

    def test_module_03_check_is_not_a_bootcamper_question(self):
        """INV-012: agent-side apparatus, reported only on failure."""
        self.assertRegex(flat(PHASE1), r"(?i)This is a check, not a 👉 question")


class TheSenz2027DiagnosticIsNamed(unittest.TestCase):
    def test_the_data_directory_cause_is_stated(self):
        self.assertRegex(
            flat(MODULE_02),
            r"(?i)missing the senzingsdk-runtime data directory",
        )

    def test_the_quote_carries_its_provenance(self):
        """#513: the provenance is a measured route, not a bare tool name and a date.

        The 2026-07-30 stamp named `search_docs` and no query, so the next reader could not
        re-run it (INV-291). The route below returns the FAQ as its top hit on the stamped
        index; its record is in `test_prescribed_search_queries.py`.
        """
        text = flat(MODULE_02)
        self.assertIn(
            "search_docs(query='SENZ2027 Plugin initialization error GNR data files failed to "
            "load')", text)
        self.assertRegex(text, r"server 1\.37\.27, docs index 2026-10-11 18:43 UTC, 2026-10-12")
        self.assertNotRegex(text, r"(?i)verified 2026-07-30 on MCP server 1\.32\.2",
                            "the stale stamp with no query is back (#513)")

    def test_explain_error_code_is_still_first(self):
        self.assertRegex(flat(MODULE_02), r"explain_error_code\('SENZ2027'\)")

    def test_it_points_at_the_supportpath_check(self):
        self.assertRegex(flat(MODULE_02), r"(?i)`Test-Path` check")

    def test_module_03_routes_senz2027_to_the_supportpath_check(self):
        text = flat(PHASE1)
        self.assertIn("SENZ2027", text)
        self.assertRegex(text, r"(?i)data directory\*\* is not where the configuration points")


class TheRetractedClaimStaysRetracted(unittest.TestCase):
    """SENZ7426 must never be an *unconditioned* SUPPORTPATH symptom.

    History, because it decides what this class may and may not permit. On 2026-07-28 the
    absolute claim "SENZ7426 is the symptom of a wrong SUPPORTPATH" was retracted, on the
    grounds that `explain_error_code('SENZ7426')` returned only generic causes and made no
    SUPPORTPATH connection (re-verified 2026-07-31). A blanket ban on the two appearing
    together was the right guard at the time.

    **That premise is retired — do not restore it.** On server 1.32.9, 2026-08-12,
    `explain_error_code('7426')` ranks "SUPPORTPATH points at a directory with no
    transliteration modules … a configuration error, NOT a broken install" as
    `common_causes[0]` and "Check SUPPORTPATH FIRST" as `resolution_steps[0]`, and carries
    both the macOS-cask and Windows-Scoop cases. The two tools now AGREE, so the plugin no
    longer withholds the tool's output, and the `denial` exemption this class used to grant
    (any window whose text said explain_error_code was "generic"/"makes no connection" skipped
    the check) has been removed with the sentences it protected — an exemption for the safety
    text becomes an exemption for a false claim the moment the claim goes stale, which is how
    a correct fix gets reverted by a passing suite.

    It is now too broad. `sdk_guide(topic='install', platform='windows')` (server 1.32.2)
    states the **conditioned** form: on Scoop, `%SENZING_DIR%\\data` resolves to a directory
    that does not exist, and then every SzEngine/SzDiagnostic call fails with SENZ7426 while
    SzProduct keeps working. That is not a contradiction of `explain_error_code` — a missing
    data directory means no transliteration modules, so a transliteration failure is exactly
    what you would expect. It is the same INV-169 distinction that forced the original
    retraction, applied the other way: the conditioned claim is supported, the absolute is
    not.

    So the guard now polices the absolute. A SENZ7426/SUPPORTPATH pairing is permitted only
    where the surrounding text carries **both** the platform condition and the tool that
    actually states it.

    **Updated 2026-07-31: the server documents a second platform, and this guard was narrower
    than the property it enforces.** `sdk_guide(topic='install', platform='macos_arm')` on
    server 1.32.3 states the same conditioned claim for the Homebrew cask — its shipped
    `etc/sz_engine_config.ini` points `SUPPORTPATH` at a directory that does not exist while the
    real support data sits one level up — so the macOS pairing is as well-founded as the Scoop
    one. (On cask 4.4.x and earlier that directory is `er/data`; the literal has since drifted,
    so `TheMacosSupportpathLiteralIsVersionScoped` below keeps the plugin from pinning it.)
    The condition regex accepted only `scoop|windows`, so it rejected a correct macOS claim.
    The *requirement* is unchanged — a pairing must carry a platform condition **and** the tool
    — only the set of platforms the server documents has grown. Widening the regex rather than
    the rule is the point: an unconditioned pairing is still an offense.
    """

    def test_senz7426_is_never_tied_to_supportpath_unconditionally(self):
        offenders = []
        for path in sorted(SKILLS.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            if "SENZ7426" not in text:
                continue
            flat_text = re.sub(r"\s+", " ", text)
            for match in re.finditer(r"SENZ7426", flat_text):
                window = flat_text[max(0, match.start() - 400):match.end() + 400]
                if not re.search(r"(?i)SUPPORTPATH", window):
                    continue
                # No `denial` exemption: as of 1.32.9 (2026-08-12) explain_error_code names
                # SUPPORTPATH first, so a sentence denying the link is no longer safety text
                # — it is a stale claim, and exempting it would let one be reintroduced.
                # Any platform the server documents this for, not just the first one found.
                conditioned = re.search(
                    r"(?i)scoop|windows|macos|macos_arm|homebrew|brew|cask", window
                )
                attributed = re.search(r"(?i)sdk_guide", window)
                if not (conditioned and attributed):
                    offenders.append(
                        "%s: %s" % (path.relative_to(REPO_ROOT), window[:170])
                    )
        self.assertEqual(
            [],
            offenders,
            "SENZ7426 tied to SUPPORTPATH without the condition that makes it true. Both "
            "explain_error_code('7426') and sdk_guide(topic='install') state the CONDITIONED "
            "form (server 1.32.9, 2026-08-12), and explain_error_code still lists a genuine "
            "record-level encoding cause — so the absolute remains an over-generalization. "
            "Name the platform AND the tool, or do not make the link (INV-080/INV-169):\n  "
            + "\n  ".join(offenders),
        )

    def test_the_supported_form_names_the_tool_that_states_it(self):
        """Rescoped 2026-08-12: name a tool, and stop denying the other one.

        Until today this asserted the opposite — that module 2 MUST say
        `explain_error_code` makes no SUPPORTPATH connection — so the guard *required* the
        claim it existed to keep honest, and correcting the prose failed the suite. That is
        the failure mode worth naming: a guard written to hold a retraction in place will
        hold it in place after the retraction expires, because nothing dates the premise.

        Both tools now state the conditioned form (server 1.32.9, 2026-08-12), so the
        requirement is **attribution** — name the tool that states it — plus the absence of
        the retired denial. INV-169's ban on the unconditioned absolute is unchanged and is
        enforced by `test_senz7426_is_never_tied_to_supportpath_unconditionally` above.
        """
        text = re.sub(r"\s+", " ", MODULE_02.read_text(encoding="utf-8"))
        if "SENZ7426" not in text:
            self.skipTest("module 2 no longer mentions SENZ7426")
        window = text[max(0, text.index("SENZ7426") - 600):text.index("SENZ7426") + 900]
        self.assertRegex(
            window,
            r"(?i)sdk_guide",
            "where module 2 makes the SUPPORTPATH link it must name the tool that states "
            "it, so the next reader can re-ask rather than re-derive",
        )
        self.assertNotRegex(
            text,
            r"(?i)explain_error_code[^.]{0,200}(?:only generic|no connection|makes no)",
            "the retired claim must not be restated: explain_error_code('7426') ranks "
            "SUPPORTPATH as common_causes[0] as of server 1.32.9, 2026-08-12",
        )

    def test_the_szproduct_masking_claim_carries_its_source(self):
        """The masking claim is no longer unverified — but it still needs attributing.

        This asserted, until 2026-07-31, that the plugin must NOT state the per-class
        masking behavior, because no MCP source did. One now does:
        `sdk_guide(topic='install', platform='windows')` says a wrong SUPPORTPATH makes
        every SzEngine/SzDiagnostic call fail "while SzProduct keeps working — so the
        install looks healthy". Banning the claim would now suppress a sourced fact, so
        the guard checks provenance instead of forbidding the statement.
        """
        pattern = re.compile(
            r"(?i)SzProduct[^.]{0,90}(?:keep|keeps|still)\s+(?:succeed|work)", re.DOTALL
        )
        for path in sorted(SKILLS.rglob("*.md")):
            flat_text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            for match in pattern.finditer(flat_text):
                window = flat_text[max(0, match.start() - 400):match.end() + 400]
                with self.subTest(file=path.name):
                    self.assertRegex(
                        window, r"(?i)sdk_guide",
                        "the SzProduct-masking claim appears without naming the tool that "
                        "states it. It was retracted as unverified on 2026-07-28 and is "
                        "supported only by sdk_guide(topic='install', platform='windows') "
                        "— an unattributed version is the retracted claim again (INV-080).",
                    )


class TheSweepIsNotVacuous(unittest.TestCase):
    """Both checks above assert an empty offender list over `SKILLS.rglob("*.md")`.

    If that glob stops matching — a directory rename, a move — they pass forever while
    checking nothing, and an empty result is indistinguishable from a clean one.
    """

    def test_skill_markdown_is_actually_being_scanned(self):
        found = list(SKILLS.rglob("*.md"))
        self.assertGreater(
            len(found), 20,
            "only %d skill .md files found; the glob has drifted and the SENZ7426 / "
            "SzProduct-masking sweeps are now vacuous" % len(found),
        )


if __name__ == "__main__":
    unittest.main()


class TheSupportpathCheckIsNotGatedToOnePlatform(unittest.TestCase):
    """The check is about a *layout*, not a platform, and gating it re-creates the defect.

    Module 2's SUPPORTPATH verification closed with "This SUPPORTPATH verification applies to
    Windows only. On Linux and macOS, use the MCP-returned paths without modification." That was
    reasoned from Scoop, where SENZING_DIR points at `er` and `data` sits beside it — and the
    Homebrew cask has the identical shape, documented by `sdk_guide(topic='install',
    platform='macos_arm')` on server 1.32.3.

    So a macOS bootcamper hitting SENZ7426 was sent (via Module 3) to a check that told them it
    did not apply to them. Worse, Module 3's routing fired only on SENZ2027, so SENZ7426 reached
    no diagnostic at all and `explain_error_code` sent them to validate input data for a failure
    that happens before any record is submitted.
    """

    def test_the_check_is_not_declared_windows_only(self):
        self.assertNotRegex(
            flat(MODULE_02), r"(?i)SUPPORTPATH verification applies to Windows only",
            "the check is gated to one platform again; the macOS cask has the same layout",
        )

    def test_macos_carries_the_check_with_its_own_paths(self):
        text = flat(MODULE_02)
        self.assertRegex(text, r"(?i)brew --prefix.{0,40}opt/senzing/data",
                         "the macOS support-data path is missing")
        self.assertRegex(text, r"(?i)TransRules\.sz",
                         "the macOS verification command is missing")

    def test_the_macos_cause_names_the_shipped_ini(self):
        self.assertRegex(flat(MODULE_02), r"(?i)sz_engine_config\.ini")

    def test_the_scoop_app_folder_is_the_installed_package(self):
        """The Scoop app folder is named for the package the server installs (#234).

        `sdk_guide(topic='install', platform='windows')` installs `senzingsdk/senzingsdk`
        (server 1.37.15, 2026-09-28), so Scoop's app folder is `apps\\senzingsdk`. The example
        path said `apps\\senzing`, which is not the installed package's name. Negative-
        controlled by restoring it.
        """
        offenders = []
        for path in sorted(PLUGIN.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if re.search(r"(?i)scoop[\\/]+apps[\\/]+senzing[\\/]", text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual([], offenders,
                         "these shipped files name a Scoop app folder `apps\\senzing\\`; the "
                         "package is `senzingsdk`, so the folder is `apps\\senzingsdk\\`")
        self.assertRegex(MODULE_02.read_text(encoding="utf-8"),
                         r"scoop\\apps\\senzingsdk\\current\\er",
                         "Module 2's Scoop layout note no longer shows the app folder")

    def test_linux_is_marked_not_re_checked_rather_than_widened(self):
        """Widening by inference is what this spec exists to stop doing."""
        self.assertRegex(flat(MODULE_02), r"(?i)Linux was not re-checked")

    def test_module_03_routes_senz7426_to_the_check(self):
        """The criterion that names a second consumer, checked against that consumer (INV-182).

        Asserts the routing *condition*, not the mere presence of the string. An earlier version
        matched `SENZ7426.{0,400}SUPPORTPATH` anywhere, which the paragraph's own denial sentence
        ("names no connection to `SUPPORTPATH`") satisfied — so renaming the routing rule's code
        to SENZ9999 left the test green while nothing routed.
        """
        text = flat(PHASE1)
        self.assertRegex(
            text, r"(?i)If the code is `SENZ7426`",
            "Module 3 has no branch keyed on SENZ7426, so it reaches no diagnostic at all — "
            "step 4 sends it to explain_error_code, which names no SUPPORTPATH cause",
        )
        # `Step 8` specifically, not `Step 8|SUPPORTPATH`: the branch *explains* the cause using
        # the word SUPPORTPATH, so the alternation was satisfied even after the routing sentence
        # was deleted. The property is that it routes, and Step 8 is where it routes to.
        self.assertRegex(text, r"(?i)If the code is `SENZ7426`.{0,300}Step 8",
                         "the SENZ7426 branch does not route to Module 2's Step 8 check")

    def test_module_03_relays_the_explanation_and_conditions_it(self):
        """Module 3 relays; Module 2 Step 8 owns the analysis of what it relays (#219).

        Inverted 2026-08-12: `explain_error_code('7426')` ranks SUPPORTPATH first, so
        relaying is required, and this asserted the opposite until then — that Module 3 MUST
        say "do not relay" — which pinned the suppression instruction in place.

        Until #219 Module 3 also carried its own copy of the tool's ranking: the encoding
        cause ranked last, and the failure firing at engine construction. That copy drifted
        from Module 2 Step 8 (it still said the tools agree, while Step 8 recorded that they
        differ on the macOS literal), which is the failure INV-300 describes. So the copy is
        gone. Module 3 still conditions what it relays, in one clause about the macOS
        literal, and the two ranking facts are asserted where they now live: Module 2's
        "`SENZ7426` still fires at `getEngine()`" paragraph.

        (Dated note, 2026-10-13, #568: on server 1.37.28 `explain_error_code('7426')` no
        longer quotes the 4.4.x literal, and both tools say to test whether `SUPPORTPATH`
        resolves, so the tools have converged. Step 3b's macOS-literal clause is gone; what
        travels with the relay is Step 8's `*TransRules.sz` content test, asserted below.)
        """
        text = flat(PHASE1)
        self.assertRegex(
            text, r"(?i)relay what `explain_error_code` returned",
            "Module 3 must relay what the tool returns for SENZ7426 — it names SUPPORTPATH "
            "first (INV-080)",
        )
        self.assertRegex(
            text, r"(?i)If the code is `SENZ7426`.{0,700}Step 8's `\*TransRules\.sz` content test",
            "Module 3's SENZ7426 relay no longer names Step 8's `*TransRules.sz` content test, "
            "the check that holds whatever literal the ini carries",
        )
        module_02 = flat(MODULE_02)
        self.assertRegex(
            module_02, r"(?i)`explain_error_code` now ranks that cause last",
            "relaying is only safe alongside the tool's own ranking: the encoding cause is "
            "last and conditioned on the engine having initialized",
        )
        self.assertRegex(
            module_02,
            r"(?i)`SENZ7426` still fires at `getEngine\(\)`, \*\*before any record is submitted",
            "the pre-record nature of this failure is why the encoding cause does not apply",
        )


class TheModule03Senz7426BranchIsAPointer(unittest.TestCase):
    """Module 3 step 3b points at Module 2 Step 8's two-tool block and carries no copy (#219).

    Step 3b held its own analysis of `explain_error_code('7426')`, stamped server 1.32.9. It
    said the tool "now agrees with Step 8" and that Step 8 "is corroboration rather than a
    correction". #199 re-verified on server 1.37.14 (2026-09-28) that the tools agree on the
    diagnosis and the fix but not on the macOS literal, and fixed Module 2 only. The copy in
    Module 3 kept telling the guide the tools agree. Re-checked for #219 on server 1.37.14,
    2026-09-28: `explain_error_code('7426')` still quotes the 4.4.x `er/data` literal, and
    `sdk_guide(topic='install', platform='macos_arm', language='java')` still says "Do not
    pin the literal".

    The claim guarded is "the pointer carries no second copy of the comparison" (INV-300),
    so the checks come from that claim, not from the sentences removed: no agreement verb at
    all outside the quoted owner title, no ranking vocabulary, and no version stamp.

    (Dated note, 2026-10-13, #568: re-checked on server 1.37.28, `explain_error_code('7426')`
    no longer quotes the 4.4.x `er/data` literal, and `sdk_guide(topic='install',
    platform='macos_arm', language='csharp')` says to test whether the path resolves. The
    tools have converged, the owner block's title says so, and step 3b drops its clause
    about the tool's literal. The claims above are unchanged, and step 3b keeps its INV-169
    warning.)
    """

    OWNER_TITLE = "Both tools agree on the diagnosis, the fix and the path test"

    def step_3b(self):
        match = re.search(
            r"3b\. \*\*If the code is `SENZ7426`\*\*.*?(?= 4\. )", flat(PHASE1)
        )
        self.assertIsNotNone(match, "Module 3 step 3b (SENZ7426) was not found")
        return match.group(0)

    def test_the_owner_block_exists_in_module_02(self):
        """A pointer to a title that no longer exists points nowhere."""
        self.assertIn(self.OWNER_TITLE, flat(MODULE_02))

    def test_step_3b_names_the_owner_and_cites_inv_300(self):
        block = self.step_3b()
        self.assertIn(self.OWNER_TITLE, block,
                      "step 3b no longer names Module 2 Step 8's two-tool block")
        self.assertRegex(block, r"module-02-sdk-setup/SKILL\.md",
                         "step 3b no longer names the owning file")
        self.assertRegex(block, r"Module 2 Step 8", "step 3b no longer names the owning step")
        self.assertRegex(block, r"INV-300\b", "step 3b no longer cites INV-300")

    def test_step_3b_does_not_say_the_tools_agree(self):
        remainder = self.step_3b().replace(self.OWNER_TITLE, "")
        self.assertNotRegex(
            remainder, r"(?i)\bagree",
            "step 3b says the tools agree. Module 2 Step 8 owns that comparison (re-verified "
            "on server 1.37.28, 2026-10-13), so name it rather than summarize it",
        )
        self.assertNotRegex(
            flat(PHASE1), r"(?i)corroboration rather than a correction|agrees with Step 8",
            "the retired 'agree' wording is back in Module 3",
        )

    def test_step_3b_carries_no_copy_of_the_tool_analysis(self):
        block = self.step_3b()
        for pattern in (r"common_causes", r"resolution_steps", r"(?i)\branked?\b",
                        r"(?i)MCP server \d+\.\d+"):
            with self.subTest(pattern=pattern):
                self.assertNotRegex(
                    block, pattern,
                    "step 3b carries part of Module 2 Step 8's tool-content analysis again; "
                    "a second copy is how it drifted (INV-300)",
                )

    def test_step_3b_no_longer_says_the_tool_quotes_a_literal(self):
        """Server 1.37.28 (2026-10-13): `explain_error_code('7426')` quotes no literal."""
        self.assertNotRegex(
            self.step_3b(), r"(?i)cask cause quotes|literal that holds for cask 4\.4\.x",
            "step 3b says explain_error_code quotes a 4.4.x literal; it no longer does",
        )

    def test_step_3b_keeps_the_inv_169_warning(self):
        self.assertTrue(has_inv_169_warning(self.step_3b()),
                        "step 3b lost its INV-169 'never restate this as an unconditioned "
                        "rule' warning")

    def test_the_inv_169_warning_check_catches_its_removal(self):
        """Negative control: step 3b with the warning cut out must fail the check."""
        block = self.step_3b()
        stripped = re.sub(r"⛔ Never restate this as an unconditioned rule \(INV-169\)[^⛔]*",
                          "", block)
        self.assertNotEqual(block, stripped, "the warning to strip was not found")
        self.assertFalse(has_inv_169_warning(stripped),
                         "the check passes step 3b with its INV-169 warning removed")

    def test_module_03_quotes_no_er_data_literal(self):
        folder = PHASE1.parent
        for path in sorted(folder.rglob("*.md")):
            with self.subTest(path=path.name):
                self.assertNotIn(
                    "er/data", path.read_text(encoding="utf-8"),
                    "Module 3 quotes the macOS er/data literal; it holds for cask 4.4.x only",
                )


class TheMacosSupportpathLiteralIsVersionScoped(unittest.TestCase):
    """The macOS diagnosis tests the directory's content, never a pinned literal (#199).

    Module 2 quoted the cask's shipped `SUPPORTPATH=${INSTALLPATH}/senzing/er/data` as what
    the ini says, and said `sdk_guide` carries that gotcha "verbatim". On MCP server 1.37.14
    (2026-09-28) `sdk_guide(topic='install', platform='macos_arm', language='java')` says
    "Do not pin the literal: it has already drifted once" — 4.4.x shipped `er/data`, and
    4.5.0.26245 ships a Linux path that equally does not exist on a Homebrew install. A
    Bootcamper told to look for `er/data` on 4.5.0 finds a different string and concludes
    the diagnosis does not apply, when it does.

    `explain_error_code('7426')` still quotes the 4.4.x literal on the same date, so the
    two tools agree on the diagnosis and the fix but not on the literal. The guard below
    keeps every surviving `er/data` inside a 4.4.x condition (INV-169: record the version an
    observation holds for) and keeps the tool that owns the platform detail named.

    (Dated note, 2026-10-13, #568: on server 1.37.28 `explain_error_code('7426')` no longer
    quotes the 4.4.x literal; both tools say to test whether `SUPPORTPATH` resolves rather
    than compare it to a string, so the tools have converged. The guard is unchanged: the
    literal is still never pinned, and the owner block now says so in both tools' words.)
    """

    WINDOW = 300

    def test_er_data_appears_only_under_a_4_4_x_condition(self):
        text = flat(MODULE_02)
        self.assertTrue(re.search(r"er/data", text),
                        "Module 2 no longer mentions er/data; retire this test")
        self.assertEqual(
            [], unconditioned_er_data(text, self.WINDOW),
            "`er/data` appears without a 4.4.x condition in the same window. The "
            "literal holds for cask 4.4.x and earlier only; sdk_guide(topic='install', "
            "platform='macos_arm') says it has drifted (server 1.37.14, 2026-09-28)",
        )

    def test_the_owner_block_says_to_test_the_path_not_the_string(self):
        self.assertTrue(says_test_the_path(owner_block()),
                        "the owner block no longer says to test whether SUPPORTPATH resolves "
                        "rather than compare it to a string")

    def test_the_pinned_literal_checks_catch_a_regression(self):
        """Negative controls: pinning the macOS literal must make a check report it."""
        text = flat(MODULE_02)
        pinned = text + (" Tell the Bootcamper their ini says "
                         "`SUPPORTPATH=${INSTALLPATH}/senzing/er/data`.")
        self.assertTrue(unconditioned_er_data(pinned, self.WINDOW),
                        "the er/data check passes a literal pinned without a 4.4.x condition")
        block = owner_block()
        unpinned = block.replace("rather than compare it to a string", "and compare it")
        self.assertNotEqual(block, unpinned, "the path-test phrase to strip was not found")
        self.assertFalse(says_test_the_path(unpinned),
                         "the path-test check passes an owner block that no longer forbids "
                         "comparing SUPPORTPATH to a string")

    def test_module_02_no_longer_says_the_tool_quotes_the_literal(self):
        self.assertNotRegex(
            flat(MODULE_02),
            r"(?i)macOS cause still quotes|differ on what the shipped ini says",
            "Module 2 says explain_error_code quotes the macOS literal; on server 1.37.28 "
            "(2026-10-13) it does not",
        )

    def test_sdk_guide_is_not_said_to_carry_the_gotcha_verbatim(self):
        text = flat(MODULE_02)
        self.assertNotRegex(
            text, r"(?i)gotcha[^.]{0,60}\bverbatim\b",
            "sdk_guide no longer states the macOS literal Module 2 quotes; 'verbatim' is false",
        )
        self.assertNotRegex(
            text, r"(?i)platform='macos_arm'[^.]{0,200}\bverbatim\b",
            "Module 2 again claims the macos_arm response carries its text verbatim",
        )

    def test_either_tool_is_not_relayed_for_the_macos_literal(self):
        text = flat(MODULE_02)
        self.assertNotRegex(
            text, r"(?i)So relay either one\.",
            "sdk_guide owns the platform detail, so name it rather than either tool",
        )
        self.assertRegex(
            text, r"(?i)relay `sdk_guide` for the platform detail",
            "Module 2 must name sdk_guide as the tool to relay for the macOS platform detail",
        )

    def test_the_diagnosis_tests_the_directory_content(self):
        """"Resolves on disk" is not enough: the path can exist and hold no modules."""
        self.assertRegex(
            flat(MODULE_02),
            r"(?i)does not resolve to a directory holding `\*TransRules\.sz`, whatever its "
            r"literal",
        )

    def test_the_4_5_0_config_and_resource_paths_are_named_without_a_literal(self):
        text = flat(MODULE_02)
        match = re.search(
            r"(?i)cask 4\.5\.0[^.]{0,120}`CONFIGPATH`[^.]{0,20}`RESOURCEPATH`[^.]{0,20}"
            r"Linux paths too", text,
        )
        self.assertIsNotNone(
            match, "the 4.5.0 CONFIGPATH / RESOURCEPATH clause is missing from Step 8"
        )
        self.assertNotRegex(
            match.group(0), r"(?i)(?:CONFIGPATH|RESOURCEPATH)=",
            "the 4.5.0 clause must name no literal; the server says not to pin it",
        )
