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


if __name__ == "__main__":
    unittest.main()
