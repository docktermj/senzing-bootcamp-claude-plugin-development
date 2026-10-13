"""The Senzing SDK is not a pip package, and no shipped file may say otherwise.

Module 2 Phase 3 Step 3 instructed `python3 -m pip install senzing`. The live server flags
exactly that as an **error-severity** anti-pattern: `senzing` and `senzing_core` ship *inside*
`senzingsdk-runtime`, and the PyPI packages of those names are "for unsupported community
projects only" (`generate_scaffold(language='python', workflow=…)` → `anti_patterns[]`, and
`sdk_guide(topic='install', platform='linux_apt', language='python')` →
`install.platform.gotchas[]`; both re-verified on MCP server 1.32.9, 2026-08-14).

Two things made it survive three audits. It **succeeds** — so Module 2 reported a clean
install while the PyPI packages shadowed the SDK-shipped ones, and the failure surfaced a
module later as `libSz.so: cannot open shared object file`, reading as an environment fault.
And it was **correct about a different question**: INV-066 requires an explicit `python3 -m pip`
over a bare `pip`, with a PEP 668 virtualenv fallback, and Step 3 satisfied that precisely. A
reviewer checking Step 3 against INV-066 found it compliant.

So this guard bans the instruction across the whole shipped tree, and separately asserts that
Module 2 states the shadowing hazard with its detection check — a ban with no replacement
leaves the reader to invent one.

Prohibitions and historical records are allowed: the plugin's own example recap documents this
defect hitting a real run, and Module 2 now quotes the command in order to forbid it. Those are
distinguished by a nearby prohibition marker, not by file.

Stdlib only, no `plugins/` import (INV-108).

Enforces **INV-222** — the Senzing SDK's language packages come by the route the server names for each
language and never from a public registry that route does not name (its 2026-09-30 scope note; for
Python they ship inside the runtime, by path), and INV-066's pip rules govern the plugin's own
tooling only.

Source spec: `specs/senzing-python-sdk-must-not-be-pip-installed.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins"
MODULE_02 = (PLUGIN / "senzing-bootcamp" / "skills" / "module-02-sdk-setup" / "SKILL.md")

#: Any spelling of the install: bare `pip`, `python3 -m pip`, `<venv>/bin/python -m pip`,
#: and either package name with a hyphen or an underscore.
PIP_INSTALL = re.compile(
    r"pip\s+install\s+(?:--?[\w-]+\s+)*senzing(?:[-_]core)?\b", re.IGNORECASE)

#: Words near an occurrence that make it a prohibition or a record rather than an instruction.
FORBIDDING = re.compile(
    r"(?i)⛔|do\s+not|don't|never|must not|anti-?pattern|shadow|unsupported|"
    r"error-severity|uninstall|was\s+installed|were\s+installed|instead")

#: How far back to look for that framing. One long sentence.
REACH = 420

SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def shipped_files():
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file() or SKIP_DIRS & set(path.parts):
            continue
        yield path


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def squash(text):
    return re.sub(r"\s+", " ", text)


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_corpus_is_real(self):
        files = list(shipped_files())
        self.assertGreater(len(files), 20, "the shipped corpus was not found")

    def test_the_pattern_matches_every_spelling_that_shipped_or_could(self):
        for sample in (
            "use `python3 -m pip install senzing`, and if an",
            "pip install senzing",
            "<dir>/bin/python -m pip install senzing",
            "python3 -m pip install senzing-core",
            "python3 -m pip install senzing_core",
            "python3 -m pip install --user senzing",
        ):
            with self.subTest(sample=sample):
                self.assertIsNotNone(
                    PIP_INSTALL.search(sample),
                    "the scanner misses a spelling of the install it exists to ban")

    def test_the_pattern_does_not_catch_the_plugin_s_own_tooling_installs(self):
        """INV-066 still governs these, and they are legitimate."""
        for sample in ("python3 -m pip install fpdf2",
                       "python3 -m pip install playwright",
                       "python3 -m pip install --upgrade pip"):
            with self.subTest(sample=sample):
                self.assertIsNone(PIP_INSTALL.search(sample),
                                  "the ban would reach the plugin's own tooling installs")


class NoShippedFileInstructsIt(unittest.TestCase):
    def test_every_occurrence_is_a_prohibition_or_a_record(self):
        offenses = []
        for path in shipped_files():
            flat = squash(read(path))
            for match in PIP_INSTALL.finditer(flat):
                window = flat[max(0, match.start() - REACH):match.end() + 120]
                if FORBIDDING.search(window):
                    continue
                offenses.append("%s: …%s…"
                                % (path.relative_to(REPO_ROOT),
                                   flat[max(0, match.start() - 90):match.end() + 60]))
        self.assertEqual(
            [], offenses,
            "a shipped file instructs a pip install of the Senzing SDK. The senzing and "
            "senzing_core packages ship inside senzingsdk-runtime; the PyPI packages "
            "shadow them and the failure surfaces a module later as a library-load "
            "error:\n  " + "\n  ".join(offenses))

    def test_module_2_step_3_no_longer_installs_it(self):
        """Named explicitly, so a corpus scan cannot pass by the file being renamed."""
        flat = squash(read(MODULE_02))
        self.assertNotIn("use `python3 -m pip install senzing`", flat,
                         "Module 2 still instructs the pip install")


class ModuleTwoSaysWhatToDoInstead(unittest.TestCase):
    """A ban with no replacement leaves the reader to invent one."""

    def setUp(self):
        self.text = read(MODULE_02)
        self.flat = squash(self.text)

    def test_it_says_the_packages_ship_with_the_runtime(self):
        self.assertRegex(
            self.flat,
            r"(?i)`senzing` and `senzing_core` packages \*\*ship inside `senzingsdk-runtime`",
            "Module 2 does not say where the packages actually come from")

    def test_the_paths_come_from_the_server_not_the_file(self):
        self.assertIn("sdk_guide(topic='install', platform='<platform>', language='python')",
                      self.flat,
                      "the PYTHONPATH value is not routed through sdk_guide (INV-080)")
        self.assertRegex(
            self.flat, r"(?i)Take the paths from the server, never from this file",
            "nothing forbids hardcoding the paths, which is the INV-080 violation this "
            "spec is a case of")

    def test_it_names_the_severity_and_the_scope(self):
        self.assertRegex(self.flat, r"(?i)error-severity\s*anti-pattern",
                         "the server's severity is not relayed")
        self.assertRegex(
            self.flat, r"(?i)for \*\*every\*\* workflow it scaffolds",
            "the anti-pattern's scope (every scaffold workflow) is not stated")

    def test_it_explains_that_the_command_succeeds(self):
        self.assertRegex(
            self.flat, r"(?i)Why this matters more than most wrong commands: it succeeds",
            "the hazard is stated as a rule without the reason it is dangerous")
        self.assertRegex(
            self.flat, r"(?i)libSz\.so: cannot open shared object file",
            "the deferred symptom is not named, so a reader cannot connect the Module 3 "
            "failure to this instruction")

    def test_it_gives_the_detection_check_and_a_remedy(self):
        self.assertIn('python3 -c "import senzing, sys; print(senzing.__file__)"', self.text,
                      "the shadowing detection check is missing")
        self.assertRegex(
            self.flat, r"(?i)python3 -m pip uninstall -y senzing senzing_core",
            "no remedy is given for a machine already in the shadowed state")
        self.assertRegex(
            self.flat, r"(?i)Report which was done",
            "the remedy has two branches and neither is required to be reported")

    def test_it_states_the_linux_only_asymmetry(self):
        self.assertRegex(
            self.flat, r"(?i)Python SDK is\s*\*\*only\*\* supported on Linux",
            "the platform_note's Linux-only restriction is not relayed, so a macOS "
            "bootcamper is left with no route")
        self.assertRegex(
            self.flat, r"(?i)Docker/WSL2",
            "the macOS/Windows alternatives are not named")

    def test_it_scopes_inv_066_rather_than_contradicting_it(self):
        self.assertRegex(
            self.flat, r"(?i)plugin's \*\*own\*\* tooling installs \(`fpdf2`",
            "INV-066's scope is not stated here, so a future reader can conclude that "
            "`python3 -m pip install senzing` is compliant with it")
        self.assertRegex(
            self.flat, r"(?i)never authorizes pip for the Senzing SDK",
            "the carve-out is implied rather than stated")

    def test_the_other_languages_are_unchanged(self):
        """Their bindings defer to the server's route, never to an unnamed public registry.

        Until #287 this pinned "Maven/Gradle), C# (NuGet)" — an instruction to use each
        ecosystem's package manager "as normal", which the server contradicts for Java,
        TypeScript and Rust. It now pins the route rule and the routes, not a server claim's
        wording.
        """
        self.assertRegex(
            self.flat,
            r"(?i)\*\*by the route the Senzing MCP server names for that language, never from a "
            r"public package registry that route does not name",
            "Phase 3 no longer sends the non-Python languages to the server's route")
        self.assertNotRegex(
            self.flat, r"(?i)package manager as normal",
            "Phase 3 again says the bindings come from the ecosystem's package manager as "
            "normal, which the server contradicts for Java, TypeScript and Rust (#287)")
        self.assertIn(
            "sdk_guide(topic='install', platform='<platform>', language='<language>')",
            self.flat, "Phase 3 does not send every language to sdk_guide first")
        for language in ("rust", "typescript"):
            with self.subTest(language=language):
                self.assertIn(
                    "sdk_guide(topic='install', platform='<platform>', language='%s')"
                    % language, self.flat,
                    "Phase 3 does not route %s through sdk_guide" % language)
        self.assertIn("search_docs(query='Java SDK sz-sdk.jar Maven Usage local Maven "
                      "repository')", self.flat, "Java's route to its SDK reference is gone")
        self.assertIn("sz-napi", self.text,
                      "the TypeScript build-from-source warning was lost")



#: The C# bullet as it stood before #320 (commit af4e442), without its marker line. It is the
#: whole-bullet negative control: every predicate below must fail on it.
PRE_320_CSHARP_BULLET = """   - **C#:** the route is the C# SDK reference: `search_docs(query='C# .NET SDK Senzing.Sdk NuGet
     package')`. On server 1.37.16 (2026-09-30) it said "After adding the `Senzing.Sdk` NuGet
     package to your project dependencies" and did not say where that package comes from. So
     name no package source: if the route still names none, tell the bootcamper that, and do
     not add a public NuGet feed on your own.
"""

#: Built by concatenation so this file carries no marker token of its own (the negatives scan
#: reads `tests/`).
MARKER_TOKEN = "MCP-NEGATIVE" + ":"

#: The C# bullet as it stood before #566 (main at c9a39b42), its marker line included. It is the
#: second whole-bullet negative control: every predicate #566 added must fail on it. Raw, because
#: the `windows` quote carries backslashes.
PRE_566_CSHARP_BULLET = (r"""   - **C#:** call `sdk_guide(topic='install', platform='<platform>', language='csharp')` and follow
     its `gotchas`: where the reply has a C# line, that line names the package source. On server
     1.37.16 (2026-10-01) the **`windows`** reply's gotcha said "C# / .NET: the Senzing.Sdk NuGet
     package is included in the SDK install (`sdk\dotnet\`), NOT published to nuget.org. Use:
     `dotnet nuget add source "$env:SENZING_DIR\sdk\dotnet" --name SenzingLocal; dotnet add
     package Senzing.Sdk --source SenzingLocal`". That is the `windows` reply's form, with the
     Windows install variable in its path, so present it to a Windows bootcamper only (INV-283).
     On the same date the `linux_apt`, `linux_yum` and `macos_arm` replies had no C# line, and
     `docker` follows `linux_apt`. When the reply names no source, go down this list in order,
     stop at the first step that gives an answer, and tell the bootcamper which step it was:
     1. **The C# SDK reference:** `search_docs(query='C# .NET SDK Senzing.Sdk NuGet package')`.
        On server 1.37.16 (2026-10-01) it said "After adding the `Senzing.Sdk` NuGet package to
        your project dependencies" and did not say where that package comes from.
     2. **What this machine's install holds:** look for a `Senzing.Sdk.*.nupkg` file in the
        `dotnet/` directory of the install's `sdk/` directory. Locate that `sdk/` directory from
        this platform's own install reply (the directory its `PYTHONPATH` or `sz-sdk.jar` path
        sits in), never from another platform's reply. If the file is there, use that `dotnet/`
        directory as a local NuGet source (`dotnet nuget add source <that directory> --name
        SenzingLocal`, then `dotnet add package Senzing.Sdk --source SenzingLocal`), and tell the
        bootcamper the source was **observed in their install, not named by the MCP server**
        (INV-283). No directory, or a directory with no `Senzing.Sdk.*.nupkg`, means nothing
        was observed.
     3. **Neither:** tell the bootcamper that no MCP route names the package source for their
        platform, and that nothing in their install supplied one.

     ⛔ **Never add a public NuGet feed for `Senzing.Sdk` (nuget.org or any other) on your own (INV-222).**
""" + "     <!-- " + MARKER_TOKEN + " " + r"""sdk_guide(topic='install', platform='linux_apt', language='csharp'), the same call with platform='linux_yum' and with platform='macos_arm', and search_docs(query='C# .NET SDK Senzing.Sdk NuGet package') — on linux_apt, linux_yum and macos_arm no reply says where the Senzing.Sdk NuGet package comes from: the install replies carry no C# line in their gotchas, and the reference says only "After adding the Senzing.Sdk NuGet package to your project dependencies" — owner: sdk_guide(topic='install', platform=<platform>) IS the route that carries the package source per platform, and its windows reply names it in its gotchas ("included in the SDK install (sdk\dotnet\), NOT published to nuget.org"), so the claim is scoped to the platforms asked and is not a claim that no platform's reply names it; search_docs carries the C# SDK reference ("Senzing.Sdk for C#", the top hit) and states no source (absence negative) — server 1.37.16, 2026-10-01 -->
""")

CSHARP_INSTALL_CALL = "sdk_guide(topic='install', platform='<platform>', language='csharp')"

#: A platform's own `dotnet nuget add source` command: anything but the fallback's placeholder.
PLATFORM_COMMAND = re.compile(r"dotnet nuget add source (?!<that directory>)")

#: The stale claim #566 retired: a reply that had, or replies that have, no C# line. The
#: fallback's conditional "When the reply has no C# line" is not a claim, so it is not matched.
NO_CSHARP_LINE_CLAIM = re.compile(r"(?i)repl(?:y|ies) had no C# line|replies have no C# line")

#: The source path each platform's reply named on server 1.37.28, 2026-10-13.
PLATFORM_PATHS = ("`/opt/senzing/er/sdk/dotnet` on `linux_apt` and `linux_yum`",
                  "`${SENZING_ROOT}/sdk/dotnet` on `macos_arm`",
                  "the `$env:SENZING_DIR\\sdk\\dotnet` form on `windows`")


def csharp_bullet(text):
    """Module 2 Step 3 Phase 3's C# bullet, up to the Rust bullet."""
    start = text.index("   - **C#:**")
    return text[start:text.index("   - **Rust:**", start)]


def routes_to_the_install_reply_first(bullet):
    flat = squash(bullet)
    return (CSHARP_INSTALL_CALL in flat
            and re.search(r"follow\s+its `gotchas`", flat) is not None
            and "search_docs(" not in flat)


def dates_each_platforms_source(bullet):
    flat = squash(bullet)
    return (re.search(r"On server 1\.37\.28 \(2026-10-13\) every platform's reply carried a C# "
                      r"line naming a local source", flat) is not None
            and all(path in flat for path in PLATFORM_PATHS)
            and "a `docker` bootcamper takes the Linux form from that reply" in flat)


def presents_each_form_to_its_own_platform(bullet):
    flat = squash(bullet)
    return ("Take the command from the bootcamper's own platform reply (INV-080)" in flat
            and "present that platform's form to that platform's bootcamper only (INV-283)" in flat
            and PLATFORM_COMMAND.search(flat) is None)


def falls_back_in_two_steps(bullet):
    flat = squash(bullet)
    steps = ["1. **What this machine's install holds:**", "2. **Neither:**"]
    if not all(step in flat for step in steps) or "3. **" in flat:
        return False
    positions = [flat.index(step) for step in steps]
    return (positions == sorted(positions)
            and "tell the bootcamper which step it was" in flat
            and flat.index("tell the bootcamper which step it was") < positions[0])


def states_no_stale_absence(bullet):
    # Line-scoped for the marker, as INV-209 puts a marker on ONE line.
    flat = squash(bullet)
    return ("When the reply has no C# line, go down this list" in flat
            and NO_CSHARP_LINE_CLAIM.search(flat) is None
            and not any(MARKER_TOKEN in line for line in bullet.splitlines()))


def labels_the_observation(bullet):
    flat = squash(bullet)
    return ("`Senzing.Sdk.*.nupkg`" in flat
            and "never from another platform's reply" in flat
            and "**observed in their install, not named by the MCP server**" in flat
            and "means nothing was observed" in flat)


def forbids_a_public_feed(bullet):
    # Line-scoped by design (#424): a ⛔ rule opens its own line and cites its invariant there,
    # which is the line ``conformance.py`` reads as the rule.
    return any(line.strip().startswith("⛔ **Never add a public NuGet feed")
               and "(INV-222)" in line for line in bullet.splitlines())


#: The predicates #566 added. Each fails on both negative controls.
NEW_CSHARP_PREDICATES = (routes_to_the_install_reply_first, dates_each_platforms_source,
                         presents_each_form_to_its_own_platform, falls_back_in_two_steps,
                         states_no_stale_absence)

#: The predicates #320 added that #566 kept: they hold on the pre-#566 bullet by design, and
#: fail on the pre-#320 one.
KEPT_CSHARP_PREDICATES = (labels_the_observation, forbids_a_public_feed)

CSHARP_PREDICATES = NEW_CSHARP_PREDICATES + KEPT_CSHARP_PREDICATES


class TheCSharpBulletFollowsEachPlatformsOwnReply(unittest.TestCase):
    """#566: every platform's install reply names the `Senzing.Sdk` source, so C# follows it.

    #320 (server 1.37.16, 2026-10-01) found the source in the `windows` reply only and built a
    three-step fallback for the `linux_apt`, `linux_yum` and `macos_arm` replies, starting from
    the `search_docs` C# reference. On server 1.37.28 (2026-10-13) each of those replies names
    its own local `sdk/dotnet` source in its `gotchas`, and `docker` takes the `linux_apt` one.
    The bullet now follows the reply's C# line, gives each platform's path in one dated note,
    quotes no platform's command, and keeps a two-step fallback for a reply without the line.
    Each predicate is checked on the shipped bullet, on a mutant that breaks only it, and on the
    pre-#320 bullet; each predicate #566 added is also checked on the pre-#566 bullet.
    """

    def setUp(self):
        self.bullet = csharp_bullet(read(MODULE_02))

    def test_every_predicate_holds_on_the_shipped_bullet(self):
        for predicate in CSHARP_PREDICATES:
            with self.subTest(predicate=predicate.__name__):
                self.assertTrue(predicate(self.bullet),
                                "Module 2's C# bullet fails %s" % predicate.__name__)

    def test_every_predicate_fails_on_the_pre_320_bullet(self):
        for predicate in CSHARP_PREDICATES:
            with self.subTest(predicate=predicate.__name__):
                self.assertFalse(predicate(PRE_320_CSHARP_BULLET),
                                 "%s passes on the bullet #320 replaced, so it cannot fail"
                                 % predicate.__name__)

    def test_every_new_predicate_fails_on_the_pre_566_bullet(self):
        for predicate in NEW_CSHARP_PREDICATES:
            with self.subTest(predicate=predicate.__name__):
                self.assertFalse(predicate(PRE_566_CSHARP_BULLET),
                                 "%s passes on the bullet #566 replaced, so it cannot fail"
                                 % predicate.__name__)

    def test_the_pre_566_control_is_the_bullet_it_claims_to_be(self):
        flat = squash(PRE_566_CSHARP_BULLET)
        self.assertRegex(flat, NO_CSHARP_LINE_CLAIM)
        self.assertIn("1. **The C# SDK reference:**", flat)
        self.assertEqual(1, sum(MARKER_TOKEN in line
                                for line in PRE_566_CSHARP_BULLET.splitlines()))
        for predicate in KEPT_CSHARP_PREDICATES:
            with self.subTest(predicate=predicate.__name__):
                self.assertTrue(predicate(PRE_566_CSHARP_BULLET),
                                "%s was kept from #320 but fails on the pre-#566 bullet"
                                % predicate.__name__)

    def test_the_old_instruction_is_gone(self):
        self.assertNotIn("name no package source", squash(self.bullet),
                         "the bullet still says to name no package source, which every "
                         "platform's install reply contradicts")

    def mutants(self):
        b = self.bullet
        # Each mutant breaks one predicate; the replacement must actually change the text.
        yield routes_to_the_install_reply_first, b.replace(CSHARP_INSTALL_CALL, "sdk_guide()")
        yield routes_to_the_install_reply_first, b.replace("follow\n     its `gotchas`",
                                                           "read\n     its reply")
        yield routes_to_the_install_reply_first, b.replace(
            "1. **What this machine's install holds:**",
            "1. **What this machine's install holds:** after "
            "`search_docs(query='C# .NET SDK Senzing.Sdk NuGet package')`,")
        yield dates_each_platforms_source, b.replace("On server 1.37.28 (2026-10-13)",
                                                     "On server 1.37.16 (2026-10-01)")
        yield dates_each_platforms_source, b.replace("`${SENZING_ROOT}/sdk/dotnet` on `macos_arm`",
                                                     "another path on `macos_arm`")
        yield dates_each_platforms_source, b.replace(
            "a `docker`\n     bootcamper takes the Linux form from that reply",
            "a `docker`\n     bootcamper is on their own")
        yield presents_each_form_to_its_own_platform, b.replace(
            "present that platform's form\n     to that platform's bootcamper only (INV-283)",
            "present every platform's form\n     to every bootcamper")
        yield presents_each_form_to_its_own_platform, b.replace(
            "form on `windows`.",
            "form on `windows` (`dotnet nuget add source /opt/senzing/er/sdk/dotnet "
            "--name SenzingLocal` on Linux).")
        yield falls_back_in_two_steps, b.replace("2. **Neither:**", "3. **Neither:**")
        yield falls_back_in_two_steps, b.replace("tell the bootcamper which\n     step it was",
                                                 "go\n     on")
        yield states_no_stale_absence, b.replace(
            "`docker` follows `linux_apt`:",
            "The `linux_yum` reply had no C# line, and `docker` follows `linux_apt`:")
        yield states_no_stale_absence, b.replace(
            "     ⛔ **Never add a public NuGet feed",
            "     <!-- " + MARKER_TOKEN + " x -->\n     ⛔ **Never add a public NuGet feed")
        yield states_no_stale_absence, b.replace("When the reply has no C# line, go down this",
                                                 "When the reply names no source, go down this")
        yield labels_the_observation, b.replace(
            "**observed in their install, not named by the MCP server**", "available")
        yield labels_the_observation, b.replace("never from another platform's reply",
                                                "or from any platform's reply")
        yield forbids_a_public_feed, "\n".join(
            line for line in b.splitlines() if "⛔ **Never add a public NuGet feed" not in line)
        yield forbids_a_public_feed, b.replace("on your own (INV-222).", "on your own.")

    def test_each_mutant_fails_only_its_predicate(self):
        for predicate, mutant in self.mutants():
            with self.subTest(predicate=predicate.__name__, mutant=mutant[-60:]):
                self.assertTrue(self.bullet != mutant,
                                "the mutation did not apply; the bullet's wording moved")
                self.assertFalse(predicate(mutant),
                                 "%s does not catch the mutation built to break it"
                                 % predicate.__name__)
                for other in CSHARP_PREDICATES:
                    if other is not predicate:
                        self.assertTrue(other(mutant), "the mutant for %s also breaks %s"
                                        % (predicate.__name__, other.__name__))

    def test_the_bullet_names_no_public_feed_as_the_source(self):
        flat = squash(self.bullet).lower()
        self.assertNotIn("api.nuget.org", flat, "the bullet names the public NuGet feed")
        self.assertNotRegex(flat, r"dotnet add package senzing\.sdk(?! --source)",
                            "the bullet adds the package with no local source")

if __name__ == "__main__":
    unittest.main()
