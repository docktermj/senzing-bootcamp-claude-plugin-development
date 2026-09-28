"""An already-installed V4 SDK gets a version check and an update offer, per platform.

Step 1 detected an existing install, compared it against the **V4.0 floor**, and stopped:
"No need to reinstall, skipping straight to configuration verification." That answers "is it
new enough to work", not "is it the newest available" — and a Bootcamper on an older 4.x
build was never told a newer release existed. The only upgrade branch was for `<V4.0`.

⚠️ **The spec this implements got the platform story wrong, and these tests pin the corrected
version.** It concluded that availability is Linux-only and that macOS/Windows must report the
check skipped. That came from asking `sdk_guide(platform='macos_arm', language='python')` —
which returns nothing *because the Python SDK is Linux-only*. A language dead end, not a
platform one. Asked with `language='java'`, both macOS and Windows return full install paths
with their own package managers, and those package managers are the availability oracle:

    linux_apt   dpkg-query / apt-cache policy   + direct_download for version-exact
    linux_yum   rpm -q / yum check-update       (dnf on RHEL 8+/Fedora)
    macos_arm   brew outdated --cask / brew info   + brew update, brew upgrade --cask (search_docs)
    windows     scoop status / scoop info          + scoop update senzingsdk (search_docs)
    docker      nothing in place — the image tag IS the version

That is the INV-194 lesson a third time: one tool-and-parameters answering nothing is not the
server answering nothing.

What these tests pin, all verified against server 1.32.2 on 2026-07-31:

* the version comparison, including the one-character trap — `szBuildVersion.json` writes
  `4.3.3.26191` with a **dot** where every package manager writes `4.3.3-26191` with a
  **hyphen**, and Step 1's filesystem fallback reads exactly that file
* a distinct mechanism named for each platform family, not one generalized command
* the offer is a single 👉 question, declining is safe and not re-asked (INV-006/INV-012)
* macOS's zero-exit-code trap, which makes post-update verification mandatory not advisory
* the per-platform EULA variable, where a wrong name or value is silently ignored
* that a 4.x→4.y update is routed to the target version's release notes (the 4.4.0
  "Migration & Action Required" section, via `category='release_notes'`), and "undocumented"
  survives only for a target whose notes do not cover the installed version (#194)
* nothing blocks (INV-048), and an undeterminable version reports skipped (INV-163)

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
MODULE2 = os.path.join(PLUGIN, "skills", "module-02-sdk-setup", "SKILL.md")


def read():
    with open(MODULE2, encoding="utf-8") as handle:
        return handle.read()


def flat():
    return re.sub(r"\s+", " ", read())


def step_1b():
    text = read()
    start = text.index("## Step 1b:")
    return text[start : text.index("\n## ", start + 10)]


class TheStepExistsAndIsReachable(unittest.TestCase):

    def test_step_1b_exists(self):
        self.assertIn("## Step 1b:", read())

    def test_the_v4_branch_routes_into_it(self):
        """An unreachable step is not an implemented step."""
        text = read()
        branch = text[text.index("**If the SDK is found and version is V4.0+:**") :][:900]
        self.assertRegex(
            re.sub(r"\s+", " ", branch),
            r"(?i)run \*\*Step 1b\*\*",
            "the V4.0+ branch must send the reader to the new step",
        )

    def test_it_says_why_the_floor_check_is_not_enough(self):
        """Without this, a future editor reads Step 1b as duplicate work."""
        self.assertRegex(
            re.sub(r"\s+", " ", step_1b()),
            r"(?i)is it new enough to work.{0,40}not.{0,40}newest available",
        )


class EachPlatformFamilyHasItsOwnMechanism(unittest.TestCase):
    """One generalized command would be wrong on three platforms out of four."""

    def setUp(self):
        self.section = step_1b()
        self.flat = re.sub(r"\s+", " ", self.section)

    def test_apt_commands_are_named(self):
        for probe in ("dpkg-query", "apt-cache policy", "senzingsdk-runtime"):
            with self.subTest(probe=probe):
                self.assertIn(probe, self.section)

    def test_yum_commands_are_named_including_dnf(self):
        for probe in ("rpm -q", "yum check-update"):
            with self.subTest(probe=probe):
                self.assertIn(probe, self.section)
        self.assertRegex(self.flat, r"(?i)`dnf` on RHEL 8\+/Fedora")

    def test_macos_uses_brew_not_a_generic_command(self):
        for probe in ("brew outdated --cask", "brew info --cask", "brew upgrade --cask"):
            with self.subTest(probe=probe):
                self.assertIn(probe, self.section)

    def test_windows_uses_scoop(self):
        for probe in ("scoop status", "scoop info", "scoop update"):
            with self.subTest(probe=probe):
                self.assertIn(probe, self.section)

    def test_docker_has_no_in_place_update(self):
        self.assertRegex(self.flat, r"(?i)image tag is the version")

    def test_the_package_manager_is_the_authority_not_the_mcp_server(self):
        """`senzing_version` is the string "current" — it cannot answer this."""
        self.assertRegex(
            self.flat, r"(?i)package manager that installed Senzing is the authority"
        )
        self.assertRegex(self.flat, r'(?i)`senzing_version` as the string `"current"`')

    def test_direct_download_is_not_offered_on_yum(self):
        """`sdk_guide(platform='linux_yum')` returns .deb packages with apt commands."""
        self.assertRegex(self.flat, r"(?i)Do not use `direct_download` on yum")
        self.assertRegex(self.flat, r"(?i)wrong for an rpm system")


class CommandOwnershipIsDistinguished(unittest.TestCase):
    """Half of Step 1b's commands are on loan from the server; half are not.

    The preamble used to say "Get the platform's commands from sdk_guide(...) and use the
    ones below" — two instructions, no precedence, over a list where only the *install*
    command is server-documented. Verified 2026-07-31 against server 1.32.2 by reading all
    four platform responses: `sdk_guide` returns install commands and *presence* checks
    (`ls libSz.so`, `Test-Path Sz.dll`) and documents **no version query and no update
    check on any platform**.

    ⚠️ The *update* command has a second route. On apt and yum it is the same `sdk_guide`
    install command. On macOS and Windows `sdk_guide` carries no update command, but
    `search_docs` serves the official tap and bucket READMEs, whose "Upgrade" and "Update"
    sections are the update commands (server 1.37.14, docs index 2026-09-28 03:23 UTC,
    2026-09-28, #194). Until #194 Step 1b called them plugin-owned.

    Why it matters: an agent that fetches from `sdk_guide`, fails to find
    `brew outdated --cask`, and substitutes the install command it *did* find would run
    `brew install --cask` where a check was intended — performing the update before the
    bootcamper has been asked.
    """

    def setUp(self):
        self.section = step_1b()
        self.flat = re.sub(r"\s+", " ", self.section)

    def test_the_two_owners_are_named_with_precedence(self):
        self.assertRegex(self.flat, r"(?i)Two kinds of command follow, and they have different owners")
        self.assertRegex(self.flat, r"(?i)the\s+\*?\*?response wins")

    def test_server_documented_commands_are_marked_as_on_loan(self):
        self.assertRegex(self.flat, r"(?i)on loan — re-read it, do not trust the copy below")
        self.assertRegex(self.flat, r"(?i)dated illustration")

    def test_plugin_owned_commands_are_marked_as_having_nothing_to_re_ask(self):
        self.assertRegex(self.flat, r"(?i)there is nothing to re-ask")

    def test_it_says_a_missing_command_in_the_response_is_expected(self):
        """The failure mode: a reader concludes the inlined list is wrong."""
        self.assertRegex(self.flat, r"(?i)that is expected, not an error")

    def test_the_server_documents_no_version_query_or_update_check(self):
        self.assertRegex(
            self.flat,
            r"(?i)no version\s+query and no update check on any of the four platforms",
        )

    def test_the_macos_and_windows_update_command_is_server_documented_through_search_docs(self):
        r"""Inverted by #194: the update command moved from plugin-owned to `search_docs`.

        This was `test_the_macos_and_windows_update_command_is_plugin_owned`, which corrected
        the original spec's table (it listed brew upgrade as documented when `sdk_guide` did not
        carry it). Since then the tap and bucket READMEs entered the `search_docs` corpus, so the
        command IS server-documented, on a different route from the install command.

        (Raw docstring, deliberately: it quotes shipped prose containing backslash-escaped
        backticks, which are not valid Python escapes. An r-prefix preserves the quoted claim
        byte-for-byte rather than rewording a deliberate record of a pin that was removed --
        see INV-219. Without it this file emitted a SyntaxWarning that bytecode caching then
        hid from every subsequent run.)

        ⚠️ **Asserts the ownership distinction, not the sentence that carries it (INV-219).**
        This used to also pin `never \`brew upgrade --cask\` or \`scoop update\`` — the verbatim
        wording of a dated claim about `sdk_guide`'s content. The pin was removed before it
        broke, and #194 is the case it anticipated: the server started serving the update
        command (through `search_docs`, server 1.37.14, 2026-09-28), and the sentence could be
        corrected without a guard asserting the retired wording. The dated claim itself lives in
        the `MCP-NEGATIVE` marker beside it, now a routing negative, which is the artifact built
        to carry it and to be re-asked.

        Rescoped, not deleted — the property that must hold is that Step 1b tells the reader
        **which route owns the update command on each platform**: `search_docs` on macOS and
        Windows, the `sdk_guide` install command on apt/yum. That is what a reader needs, and it
        is the ownership distinction, not the wording of a dated claim.
        """
        self.assertRegex(
            self.flat,
            r"(?i)On macOS and Windows the update command is server-documented through\s+"
            r"`search_docs`",
        )
        self.assertNotRegex(
            self.flat, r"(?i)update command is plugin-owned",
            "the macOS/Windows update command is server-documented now; do not call it plugin-owned",
        )
        # Each update command sits next to the search_docs route that serves it.
        for query, command in (
            ("homebrew-senzingsdk upgrade cask brew upgrade senzingsdk",
             "brew upgrade --cask senzingsdk"),
            ("scoop-senzingsdk update scoop update senzingsdk", "scoop update senzingsdk"),
        ):
            with self.subTest(command=command):
                self.assertIn("search_docs(query='%s')" % query, self.section)
                self.assertIn(command, self.section)
        self.assertRegex(
            self.flat, r"(?i)Only on apt and yum is the update command the same"
        )

    def test_the_preamble_names_both_server_routes(self):
        """The "Server-documented" bullet must name search_docs as well as sdk_guide (#194)."""
        text = self.section
        bullet = text[text.index("- **Server-documented"):text.index("- **Plugin-owned")]
        flat = re.sub(r"\s+", " ", bullet)
        self.assertIn("sdk_guide(topic='install'", flat)
        self.assertRegex(flat, r"(?i)\*update\* command comes from `search_docs`")

    def test_the_scoop_update_form_is_the_readme_form(self):
        """The bucket README's `scoop update senzingsdk`, not the bucket-qualified form (#194).

        `scoop info senzingsdk/senzingsdk` stays: it is a plugin-owned check command.
        """
        self.assertNotIn("scoop update senzingsdk/senzingsdk", self.section)
        self.assertIn("scoop update senzingsdk", self.section)
        self.assertIn("scoop info senzingsdk/senzingsdk", self.section)

    def test_only_apt_and_yum_update_via_the_documented_command(self):
        self.assertRegex(
            self.flat, r"(?i)Only on apt and yum is the update command the same"
        )

    def test_the_labels_are_inside_the_command_blocks_not_only_the_preamble(self):
        """A reader who skims to the code fence must still see which kind it is.

        ⚠️ **Pins the ownership LABEL, not the absence claim beside it.** Two of these markers
        used to be pinned in full — "documents brew tap / trust / install --cask only" and
        "documents scoop bucket add / scoop install only" — which made this guard enforce the
        wording of a claim about `sdk_guide`'s content. On 2026-08-13 that claim was found
        imprecise (server 1.32.9 also documents `brew uninstall --cask`, `untap`, `install`/`link
        libpq` and `--prefix`, and `scoop config`), and correcting it failed this test with a
        message telling the fixer the opposite of what the server says. That is the failure mode
        `tests/test_dated_negatives_are_marked.py` exists to prevent: a guard that pins a
        retraction outlives the retraction, and is consulted precisely by the person trying to
        fix it. Rescoped, not deleted — the label is what a skimming reader needs, and it is what
        stays true when the server moves.
        """
        for fence_marker in (
            "# plugin-owned — sdk_guide documents neither of these",
            "# server-documented — re-read from sdk_guide",
            "# plugin-owned — the server documents no brew version check",
            "# plugin-owned — the server documents no scoop version check",
            "# server-documented — re-read from search_docs; this form is a dated illustration",
        ):
            with self.subTest(marker=fence_marker[:46]):
                self.assertIn(fence_marker, self.section)

    def test_the_macos_and_windows_fences_split_ownership(self):
        """#194: each fence's check commands are plugin-owned and its update command is not.

        The label order is the property: the plugin-owned label comes before the check
        commands, and the search_docs label before the update command.
        """
        for check, update in (
            ("brew info --cask senzingsdk", "brew upgrade --cask senzingsdk"),
            ("scoop info senzingsdk/senzingsdk", "scoop update senzingsdk"),
        ):
            with self.subTest(update=update):
                owned = self.section.rindex("# plugin-owned", 0, self.section.index(check))
                served = self.section.index("# server-documented — re-read from search_docs", owned)
                self.assertLess(self.section.index(check), served)
                self.assertLess(served, self.section.index(update, served))

    def test_the_yum_prose_form_is_labeled_too(self):
        """It is prose rather than a fence, so it needs its own marking."""
        self.assertRegex(self.flat, r"(?i)\*?plugin-owned\*?\s+—\s+`rpm -q")
        self.assertRegex(self.flat, r"(?i)\*?Server-documented\*?\s+—\s+`sudo yum install")

    def test_no_inlined_command_was_deleted(self):
        """The plugin-owned half has no other source; removing it breaks the step.

        The update commands are server-documented now (#194), but their dated illustration
        stays inline so the shape is visible without a round trip, as for the install command.
        """
        for command in (
            "dpkg-query -W", "apt-cache policy", "rpm -q", "yum check-update",
            "brew outdated --cask", "brew info --cask", "brew update", "brew upgrade --cask",
            "scoop status", "scoop info", "scoop update",
        ):
            with self.subTest(command=command):
                self.assertIn(command, self.section)

    def test_the_plugin_owned_half_says_it_is_linux_exercised_only(self):
        """INV-163's discipline applied to a command: say what was not verified.

        The brew and scoop forms are standard usage but no test here has run them — this
        repo's suite is Linux. The actionable consequence is to read the command's output
        rather than trust its exit status, which is what the text says.
        """
        self.assertRegex(self.flat, r"(?i)plugin-owned commands are exercised on Linux only")
        self.assertRegex(self.flat, r"(?i)no test\s+here has ever executed")
        self.assertRegex(self.flat, r"(?i)Treat their \*?output\*? as the thing to check")
        self.assertIn("INV-163", self.section)

    def test_the_asymmetry_is_tied_to_the_upstream_report(self):
        """The server documenting installing-but-not-updating is the filed gap, now partly closed.

        #194: the update commands are served through `search_docs`; the version queries,
        status checks and version-exact pins are not. The sentence must say both halves.
        """
        self.assertRegex(self.flat, r"(?i)coverage gap reported upstream on 2026-08-13")
        self.assertRegex(self.flat, r"(?i)\*\*partly closed\*\*")
        self.assertRegex(self.flat, r"(?i)still absent")


class TheVersionComparisonTrapIsStated(unittest.TestCase):
    """The one-character difference Step 1's own fallback walks into."""

    def setUp(self):
        self.flat = re.sub(r"\s+", " ", step_1b())

    def test_both_forms_are_shown(self):
        self.assertIn("4.3.3-26191", self.flat)
        self.assertIn("4.3.3.26191", self.flat)

    def test_the_dot_versus_hyphen_is_called_out(self):
        self.assertRegex(self.flat, r"(?i)dot\*?\*? where every package manager uses a \*?\*?hyphen")

    def test_it_says_which_source_to_prefer(self):
        """⚠️ Asserts a resolution for BOTH causes, not the one unconditional sentence.

        This pinned *"Prefer the package manager's version string"* — the rule as originally
        written. On 2026-09-01 that rule was found wrong for an install the package manager
        does not own (`dpkg-query` 4.3.4-26210 against an on-disk 4.4.0.26242), so the section
        now resolves by cause: separator artifact -> package manager, genuine difference ->
        `szBuildVersion.json`. The claim this test makes — the reader is told which source
        wins — is unchanged and now has two answers instead of one.
        """
        self.assertRegex(self.flat, r"(?i)normalize the separator")
        self.assertRegex(
            self.flat, r"(?i)the package manager's string is the one to report",
            "the separator case must still resolve to the package manager's string")
        self.assertRegex(
            self.flat, r"(?i)describes what will actually \*\*load\*\*, so it wins",
            "a genuine difference must resolve to the file that describes the loading library")

    def test_the_windows_json_location_differs(self):
        """On Windows szBuildVersion.json is a sibling of er, not under SENZING_DIR."""
        self.assertRegex(self.flat, r"(?i)sibling\*?\*? `?data`? directory")

    def test_the_observation_is_marked_as_an_observation(self):
        """INV-080: a local install reading is not an MCP-sourced fact."""
        self.assertRegex(
            self.flat, r"(?i)environment observation, not an MCP-sourced fact"
        )


class TheOfferIsOneQuestionAndDecliningIsSafe(unittest.TestCase):

    def setUp(self):
        self.flat = re.sub(r"\s+", " ", step_1b())

    def test_exactly_one_pinned_question_in_the_step(self):
        """INV-251: a turn carries no more than one 👉. More than one asked here would break it.

        Counts 👉 at the start of a line (optionally inside a blockquote), which is the
        form an *asked* question takes. A bare `👉` mid-sentence is prose describing the
        rule — "One 👉 question, its own turn" — and counting those made this assert 2
        against correct content.
        """
        asked = re.findall(r"(?m)^\s*>?\s*👉", step_1b())
        self.assertEqual(1, len(asked), "the offer must be a single asked 👉 question")

    def test_the_offer_is_conditional_on_a_newer_version(self):
        self.assertRegex(self.flat, r"(?i)Only when a newer version is genuinely available")

    def test_declining_keeps_the_install_and_is_not_re_asked(self):
        self.assertRegex(self.flat, r"(?i)Keeping \[installed\]")
        self.assertRegex(self.flat, r"(?i)do not ask again")
        self.assertIn("INV-006", self.flat)

    def test_declining_is_not_recorded_as_a_failure(self):
        self.assertRegex(self.flat, r"(?i)Nothing recorded as a failure")

    def test_a_named_version_is_supported_where_documented(self):
        self.assertRegex(self.flat, r"(?i)or name a specific version")
        self.assertRegex(self.flat, r"(?i)versioned `direct_download` URL")

    def test_it_refuses_to_invent_a_pin_where_undocumented(self):
        """Homebrew casks and Scoop: the server documents no version-exact install."""
        self.assertRegex(
            self.flat,
            r"(?i)version-exact install is \*?\*?not documented by the server",
        )
        self.assertRegex(self.flat, r"(?i)rather than inventing a pin")


class TheSilentFailureModesAreGuarded(unittest.TestCase):
    """Two ways this feature could ship a lie: a no-op install, or a wrong EULA var."""

    def setUp(self):
        self.section = step_1b()
        self.flat = re.sub(r"\s+", " ", self.section)

    def test_the_macos_zero_exit_trap_is_stated(self):
        self.assertRegex(
            self.flat, r"(?i)ZERO EXIT CODE FROM `brew` DOES NOT MEAN IT INSTALLED"
        )
        self.assertRegex(self.flat, r"(?i)reads as success while installing nothing")

    def test_the_macos_artifact_probe_is_given(self):
        self.assertIn("libSz.dylib", self.section)
        self.assertIn("TransRules.sz", self.section)

    def test_the_windows_artifact_probe_is_given(self):
        self.assertIn(r"Test-Path", self.section)
        self.assertIn("Sz.dll", self.section)

    def test_all_three_eula_variables_are_tabulated(self):
        """A wrong name or value is IGNORED and the install silently does nothing."""
        self.assertIn("HOMEBREW_SENZING_ACCEPT_EULA", self.section)
        self.assertIn("i_accept_the_senzing_eula", self.section)
        self.assertIn("SENZING_ACCEPT_EULA", self.section)
        self.assertIn("I_ACCEPT_THE_SENZING_EULA", self.section)

    def test_the_macos_variable_is_marked_lowercase(self):
        """The one detail most likely to be normalized away by a later editor."""
        self.assertRegex(self.flat, r"(?i)i_accept_the_senzing_eula.{0,40}lowercase")

    def test_the_eula_question_is_reused_not_duplicated(self):
        self.assertRegex(self.flat, r"(?i)reuse the existing wording in Step 3")
        self.assertRegex(self.flat, r"(?i)An update is an install")

    def test_verification_after_update_is_mandatory(self):
        """⚠️ Cites INV-218, not INV-129 (corrected 2026-08-13).

        This asserted `INV-129` until an audit read what that invariant actually says: its subject
        is a rendered **deliverable** — "PDF, PNG, HTML artifact" — with remedies like "rasterize
        the page, open the image". An SDK install is none of those, so the citation sent a reader to
        a rule about PDFs. INV-218 registers the install case and names INV-129 as the sibling it is
        distinguished from. Pinning the wrong ID here is what kept the wrong citation alive, so the
        pair is now also guarded directly by
        `tests/test_install_verification_citation.py`.
        """
        self.assertRegex(self.flat, r"(?i)Re-run Step 4")
        self.assertRegex(self.flat, r"(?i)exit 0 is not evidence")
        self.assertIn("INV-218", self.section)

    def test_a_failed_update_names_the_working_version(self):
        self.assertRegex(self.flat, r"(?i)name\*?\*? the version that was working")
        self.assertRegex(self.flat, r"(?i)do \*?\*?not\*?\*? mark Module 2 complete")


class StepTwoRelaysThePreviewStatus(unittest.TestCase):
    """#194: the tap and bucket READMEs open with "Preview Release — Unsupported".

    `search_docs` serves the warning for both (server 1.37.14, docs index 2026-09-28 03:23 UTC,
    2026-09-28), and Step 2 recommends both routes, so Step 2 relays it for both, with the query
    that serves it. It is relayed as a fact, not as advice against the route: rules 3 and 4 still
    resolve to `macos_arm` and `windows`.
    """

    def setUp(self):
        text = read()
        start = text.index("## Step 2:")
        self.section = text[start : text.index("\n## ", start + 10)]
        self.flat = re.sub(r"\s+", " ", self.section)

    def test_the_warning_is_relayed_for_both_platforms(self):
        self.assertIn("Preview Release — Unsupported", self.section)
        for query in (
            "homebrew-senzingsdk preview release unsupported tap install cask",
            "scoop-senzingsdk update scoop update senzingsdk",
        ):
            with self.subTest(query=query):
                self.assertIn("search_docs(query='%s')" % query, self.flat)
        self.assertRegex(self.flat, r"(?i)docs index 2026-09-28 03:23 UTC")

    def test_the_routing_rules_still_resolve_natively_and_point_at_the_relay(self):
        self.assertRegex(self.flat, r"(?i)not as advice\s+against it")
        self.assertRegex(self.flat, r"(?i)\*\*`platform='macos_arm'`\*\*\. Relay the tap's preview")
        self.assertRegex(self.flat, r"(?i)\*\*`platform='windows'`\*\*, and relay the bucket's preview")


class ItNeitherBlocksNorOverclaims(unittest.TestCase):

    def setUp(self):
        self.section = step_1b()
        self.flat = re.sub(r"\s+", " ", self.section)

    def test_it_is_non_blocking(self):
        self.assertIn("INV-048", self.section)
        self.assertRegex(self.flat, r"(?i)Non-blocking, start to finish")

    def test_an_undeterminable_version_reports_skipped(self):
        """INV-163: "no data" must never render as "up to date"."""
        self.assertIn("INV-163", self.section)
        self.assertRegex(self.flat, r'(?i)"No data" is never "up to date"')

    def test_a_point_release_is_routed_to_the_target_release_notes(self):
        """#194: the 4.x->4.y answer is the target version's release notes, not "undocumented".

        Rescoped from `test_it_states_that_no_point_release_procedure_is_documented`. The
        v4.4.0 "Migration & Action Required" notes are served under `category='release_notes'`
        (server 1.37.14, docs index 2026-09-28 03:23 UTC, 2026-09-28), so the blanket negative
        was false. "Undocumented, not known to be unnecessary" survives, scoped to a target
        whose notes do not cover the installed version.
        """
        self.assertNotRegex(self.flat, r"(?i)documents no 4\.x → 4\.y update procedure")
        self.assertIn(
            "search_docs(query='upgrading to 4.4.0 from v4.0.0 through v4.3.x no schema change "
            "required migration action required', category='release_notes')",
            self.flat,
        )
        self.assertRegex(self.flat, r"(?i)read past the first hit")
        self.assertRegex(self.flat, r"(?i)No schema change required\*\* when upgrading from any v4")
        self.assertRegex(
            self.flat,
            r"(?i)Only when the target's notes do not cover it is the step "
            r"\*\*undocumented, not known to be unnecessary",
        )

    def test_the_conditional_4_4_0_items_are_conditional(self):
        """SQL Server collation and the discontinued installers apply only in their cases."""
        self.assertRegex(self.flat, r"(?i)Relay it only when the datastore is SQL Server")
        self.assertRegex(
            self.flat, r"(?i)Relay it only when the installed version is 4\.2\.x or earlier"
        )

    def test_a_populated_repository_hears_about_reprocessing(self):
        self.assertRegex(self.flat, r"(?i)touches the SDK and\s+not their data")
        self.assertRegex(self.flat, r"(?i)apply to already-loaded\s+data only after reprocessing")

    def test_another_target_carries_a_re_query_rule(self):
        """The templated query was never executed for a later target, so its section must say
        what to do on a miss. `tests/test_prescribed_search_queries.py` enforces this for every
        unverified literal; this pins that the template is one of them.
        """
        text = read()
        at = text.index("search_docs(query='upgrading to <target version>")
        start = text.rindex("\n### ", 0, at)
        end = text.index("\n## ", at)
        section = re.sub(r"\s+", " ", text[start:end])
        self.assertRegex(section, r"(?i)re-query")

    def test_it_does_not_claim_apt_version_pinning(self):
        """`apt install pkg=version` is not documented by the server."""
        self.assertNotRegex(
            self.section,
            r"apt install\s+senzingsdk-runtime=",
            "apt version pinning is not server-documented; the versioned .deb is",
        )

    def test_the_outcome_is_checkpointed_so_a_resume_does_not_re_offer(self):
        for outcome in ("up-to-date", "update-declined", "updated-to-", "check-skipped-"):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, self.section)

    def test_the_senzing_facts_carry_their_provenance(self):
        """INV-080: server version and date on every claim written into the plugin."""
        self.assertRegex(self.flat, r"(?i)server 1\.32\.2")
        self.assertIn("2026-07-31", self.section)

    def test_the_scan_is_not_vacuous(self):
        self.assertTrue(os.path.isfile(MODULE2))
        self.assertGreater(len(step_1b()), 3000, "Step 1b must actually have content")


if __name__ == "__main__":
    unittest.main()
