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
        self.assertIn("search_docs(query='C# .NET SDK Senzing.Sdk NuGet package')", self.flat,
                      "C#'s route to its SDK reference is gone")
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

CSHARP_INSTALL_CALL = "sdk_guide(topic='install', platform='<platform>', language='csharp')"
CSHARP_REFERENCE = "search_docs(query='C# .NET SDK Senzing.Sdk NuGet package')"


def csharp_bullet(text):
    """Module 2 Step 3 Phase 3's C# bullet, up to the Rust bullet."""
    start = text.index("   - **C#:**")
    return text[start:text.index("   - **Rust:**", start)]


def routes_to_the_install_reply_first(bullet):
    flat = squash(bullet)
    return (CSHARP_INSTALL_CALL in flat and CSHARP_REFERENCE in flat
            and flat.index(CSHARP_INSTALL_CALL) < flat.index(CSHARP_REFERENCE)
            and re.search(r"follow\s+its `gotchas`", flat) is not None)


def quotes_the_windows_reply_dated_and_attributed(bullet):
    flat = squash(bullet)
    return (re.search(r"On server 1\.37\.16 \(2026-10-01\) the \*\*`windows`\*\* reply's gotcha",
                      flat) is not None
            and "NOT published to nuget.org" in flat
            and "present it to a Windows bootcamper only (INV-283)" in flat)


def falls_back_in_order(bullet):
    flat = squash(bullet)
    steps = ["1. **The C# SDK reference:** `" + CSHARP_REFERENCE + "`",
             "2. **What this machine's install holds:**",
             "3. **Neither:**"]
    if not all(step in flat for step in steps):
        return False
    positions = [flat.index(step) for step in steps]
    return (positions == sorted(positions)
            and "tell the bootcamper which step it was" in flat
            and flat.index("tell the bootcamper which step it was") < positions[0])


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


def narrows_the_marker(bullet):
    # Line-scoped by design (#424): INV-209 requires an MCP-NEGATIVE marker on ONE line.
    lines = [line for line in bullet.splitlines() if MARKER_TOKEN in line]
    if len(lines) != 1:
        return False
    claim, _, rest = lines[0].partition(" — owner: ")
    return (all(p in claim for p in ("platform='linux_apt'", "platform='linux_yum'",
                                     "platform='macos_arm'"))
            and "platform='windows'" not in claim
            and "its windows reply names it" in rest
            and "not a claim that no platform's reply names it" in rest
            and rest.rstrip().endswith("— server 1.37.16, 2026-10-01 -->"))


CSHARP_PREDICATES = (routes_to_the_install_reply_first, quotes_the_windows_reply_dated_and_attributed,
                     falls_back_in_order, labels_the_observation, forbids_a_public_feed,
                     narrows_the_marker)


class TheCSharpBulletRoutesToTheInstallReplyFirst(unittest.TestCase):
    """#320: the `windows` install reply names the `Senzing.Sdk` source, so C# asks it first.

    Until #320 the bullet routed only to `search_docs` and said to "name no package source",
    on a negative asked of `linux_apt` alone. On server 1.37.16 (2026-10-01)
    `sdk_guide(topic='install', platform='windows', language='csharp')` names the local
    `sdk\\dotnet` source in its `gotchas`, while the `linux_apt`, `linux_yum` and `macos_arm`
    replies have no C# line. Each predicate is checked on the shipped bullet, on a mutant that
    breaks only it, and on the pre-#320 bullet.
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

    def test_the_old_instruction_is_gone(self):
        self.assertNotIn("name no package source", squash(self.bullet),
                         "the bullet still says to name no package source, which the "
                         "windows install reply contradicts")

    def mutants(self):
        b = self.bullet
        # Each mutant breaks one predicate; the replacement must actually change the text.
        yield routes_to_the_install_reply_first, b.replace(CSHARP_INSTALL_CALL, "sdk_guide()")
        yield routes_to_the_install_reply_first, b.replace("follow\n     its `gotchas`",
                                                           "read\n     its reply")
        yield quotes_the_windows_reply_dated_and_attributed, b.replace(
            "the **`windows`** reply's gotcha", "the reply's gotcha")
        yield quotes_the_windows_reply_dated_and_attributed, b.replace(
            "present it to a Windows bootcamper only (INV-283)", "present it")
        yield falls_back_in_order, b.replace(
            "1. **The C# SDK reference:**", "2. **The C# SDK reference:**").replace(
            "2. **What this machine's install holds:**", "1. **What this machine's install holds:**")
        yield falls_back_in_order, b.replace("tell the bootcamper which step it was", "go on")
        yield labels_the_observation, b.replace(
            "**observed in their install, not named by the MCP server**", "available")
        yield labels_the_observation, b.replace("never from another platform's reply",
                                                "or from any platform's reply")
        yield forbids_a_public_feed, "\n".join(
            line for line in b.splitlines() if "⛔ **Never add a public NuGet feed" not in line)
        yield forbids_a_public_feed, b.replace("on your own (INV-222).", "on your own.")
        yield narrows_the_marker, b.replace(", the same call with platform='linux_yum' and with "
                                            "platform='macos_arm'", "")
        yield narrows_the_marker, b.replace("so the claim is scoped to the platforms asked and "
                                            "is not a claim that no platform's reply names it",
                                            "so no platform's reply names it")

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
