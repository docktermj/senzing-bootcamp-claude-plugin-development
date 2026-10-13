"""Windows is a supported platform, so PowerShell's semantics must be documented.

Two classes of failure, both from one Windows session, both previously undocumented:

1. **Silent encoding corruption.** On PowerShell 5.1 `-Encoding utf8` writes a BOM, so a
   generated JSONL's first record failed to parse (158 of 159 fine — it reads as one bad
   source record, not an encoding fault). And `Get-Content` without `-Encoding` decodes as
   the system ANSI codepage, so `Add-Content -Value (Get-Content $src -Raw)` read a UTF-8
   file as Windows-1252 and wrote the mojibake back as UTF-8: 25 em dashes became `a<TM>"`.
   That second one passes every obvious check — valid UTF-8, no U+FFFD, zero BOMs — and is
   simply wrong.

2. **Bash-shaped commands that 5.1 cannot parse:** `&&`/`||`, `if` as an expression,
   inline `python -c`, `Start-Process` argument splitting, heredocs.

The plugin dual-writes bash and PowerShell blocks in several modules, which is what makes
this reachable: the PowerShell halves were offered without their semantics.

These tests pin the guidance and the mojibake detector. Mojibake fixtures are built by
round-tripping rather than pasted, so this file stays ASCII and readable in any editor.

Enforces **INV-167** (a PowerShell counterpart carries no bash-shaped constructs -- `&&`
and `||` chaining above all -- because each is a *parser* error on Windows PowerShell 5.1,
so the message points at syntax rather than at the real cause), which names this file.

`NoBareEnvironmentVariablesInPowerShellBlocks` (#505) adds one more bash-shaped construct:
an environment variable read as `$NAME` instead of `$env:NAME`. In PowerShell `$SENZING_DIR`
is an unset *PowerShell* variable, so `Test-Path -Path "$SENZING_DIR\\data"` tested `\\data` on
the current drive and reported a false "not found". The guard flags any bare all-caps
`$NAME` in a shipped PowerShell fence; the INV-167 amendment naming it is drafted in #505's
`specs/IMPLEMENTED.md` entry, awaiting the maintainer's sign-off.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
NORMALIZER = PLUGIN / "scripts" / "normalize_docs_markdown.py"
PHASE3_TEST_LOAD = PLUGIN / "skills" / "module-05-data-quality-mapping" / "phase3-test-load.md"

POWERSHELL_LANGS = {"powershell", "ps1", "pwsh"}


def load_normalizer():
    spec = importlib.util.spec_from_file_location("normalizer_under_test", NORMALIZER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NORM = load_normalizer()


def mojibake(text):
    """The exact corruption `Get-Content`-without-`-Encoding` produces.

    UTF-8 bytes decoded as Windows-1252 — which is what lands in the file once those
    characters are written back out as UTF-8.
    """
    return text.encode("utf-8").decode("cp1252")


def powershell_blocks(path):
    """Yield (line_number, line) for every line inside a PowerShell fence.

    Line-scoped by design (#424): a fenced PowerShell line is one command.
    """
    inside = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            lang = stripped[3:].strip().lower()
            if not inside and lang in POWERSHELL_LANGS:
                inside = True
            elif inside:
                inside = False
            continue
        if inside:
            yield number, line


class MojibakeIsDetected(unittest.TestCase):
    """The failure no other check can see."""

    def test_detects_a_double_encoded_em_dash(self):
        corrupted = mojibake("Senzing Bootcamp — a recap")
        self.assertEqual([1], NORM.mojibake_lines(corrupted))

    def test_detects_double_encoded_curly_quotes_and_ellipsis(self):
        # Each of these has UTF-8 bytes that all map to *defined* cp1252 code points, so
        # the corruption is representable — which is the case that reaches a file.
        for original in ("He said “yes", "waiting…", "café — open"):
            with self.subTest(original=original):
                self.assertEqual([1], NORM.mojibake_lines(mojibake(original)))

    def test_undecodable_byte_sequences_are_out_of_scope(self):
        """Not every corruption is representable, and that is a real limit.

        A right curly quote (U+201D) is UTF-8 `E2 80 9D`, and `0x9D` is undefined in
        cp1252 — so that byte cannot survive an ANSI read as a character, and the
        round-trip cannot reconstruct it. The detector catches the representable cases,
        which is what the reported failure (25 em dashes) was made of.
        """
        with self.assertRaises(UnicodeDecodeError):
            mojibake("He said ”")

    def test_reports_the_right_line_numbers(self):
        text = "clean line\n" + mojibake("bad — line") + "\nanother clean\n" + mojibake("also … bad")
        self.assertEqual([2, 4], NORM.mojibake_lines(text))

    def test_the_corruption_is_valid_utf8_with_no_replacement_chars(self):
        """Why this check has to exist: nothing else flags it."""
        corrupted = mojibake("Senzing Bootcamp — a recap")
        corrupted.encode("utf-8").decode("utf-8")  # round-trips cleanly
        self.assertNotIn("�", corrupted)
        self.assertFalse(corrupted.encode("utf-8").startswith(b"\xef\xbb\xbf"))


class CleanTextIsNotFlagged(unittest.TestCase):
    """A false positive would send graduation to 'fix' a correct document."""

    def test_ascii_is_clean(self):
        self.assertEqual([], NORM.mojibake_lines("# Recap\n\nPlain ASCII only.\n"))

    def test_correct_typography_is_clean(self):
        text = "Senzing Bootcamp — a recap\n“Quoted” and … done\n"
        self.assertEqual([], NORM.mojibake_lines(text))

    def test_ordinary_accented_prose_is_clean(self):
        for line in (
            "café naïve façade",
            "£20 for the résumé",
            "João Österreich",
            "© 2026 Senzing",
            "temperature 20°C ± 2",
        ):
            with self.subTest(line=line):
                self.assertEqual([], NORM.mojibake_lines(line))

    def test_cjk_and_emoji_are_clean(self):
        for line in ("李明", "\U0001f393 graduation", "Дана"):
            with self.subTest(line=line):
                self.assertEqual([], NORM.mojibake_lines(line))

    def test_the_shipped_example_recap_is_clean(self):
        example = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"
        if example.is_file():
            self.assertEqual([], NORM.mojibake_lines(example.read_text(encoding="utf-8")))


class DetectionIsReportedNotRepaired(unittest.TestCase):
    """A cosmetic pass must not silently rewrite content (its own contract)."""

    def test_normalizer_warns_on_stderr(self):
        text = NORMALIZER.read_text(encoding="utf-8")
        self.assertIn("mojibake", text)
        self.assertRegex(text, r"WARNING:[^\n]*mojibake|mojibake[^\n]*WARNING")

    def test_normalize_text_does_not_alter_mojibake(self):
        """Reporting only: the corrupted characters are left exactly as found."""
        corrupted = mojibake("Recap — done")
        self.assertIn(corrupted, NORM.normalize_text(corrupted))


class GroundRulesDocumentPowerShell(unittest.TestCase):
    def setUp(self):
        self.text = GROUND_RULES.read_text(encoding="utf-8")

    def test_has_a_windows_powershell_section(self):
        self.assertRegex(self.text, r"(?im)^##\s+.*PowerShell")

    def test_names_the_bom_trap_and_its_fix(self):
        self.assertRegex(self.text, r"(?i)-Encoding utf8[^\n]*BOM|BOM[^\n]*-Encoding utf8")
        self.assertIn("UTF8Encoding($false)", self.text)

    def test_names_the_get_content_ansi_trap_and_its_fix(self):
        self.assertRegex(self.text, r"(?i)Get-Content[^\n]*(?:ANSI|codepage)")
        self.assertIn("[System.IO.File]::ReadAllText", self.text)

    def test_states_the_version_assumption(self):
        self.assertRegex(self.text, r"(?i)powershell\.exe[^\n]*5\.1|5\.1[^\n]*powershell\.exe")
        self.assertRegex(self.text, r"(?i)pwsh[^\n]*7")

    def test_names_every_syntax_trap(self):
        for pattern, label in (
            (r"if \(\$\?\)", "&& replacement"),
            (r"(?i)ternary", "no ternary"),
            (r"python -c", "inline -c"),
            (r"(?i)Start-Process", "argument splitting"),
            (r"(?i)here-string|heredoc", "heredocs"),
        ):
            with self.subTest(trap=label):
                self.assertRegex(self.text, pattern)

    def test_states_the_prefer_a_file_rule(self):
        self.assertRegex(
            self.text, r"(?i)script file|write generated files|run the file"
        )

    def test_cross_referenced_from_the_input_bom_note(self):
        self.assertRegex(
            PHASE3_TEST_LOAD.read_text(encoding="utf-8"),
            r"(?i)ground.rules|Windows and PowerShell",
        )


class NoBashChainingInPowerShellBlocks(unittest.TestCase):
    """A regression guard: the PowerShell halves must stay PowerShell."""

    def test_no_powershell_block_uses_and_or_chaining(self):
        offenders = []
        for path in sorted(PLUGIN.rglob("*.md")):
            for number, line in powershell_blocks(path):
                if "&&" in line or "||" in line:
                    offenders.append(
                        "%s:%d: %s" % (path.relative_to(REPO_ROOT), number, line.strip())
                    )
        self.assertEqual(
            [],
            offenders,
            "PowerShell 5.1 has no && / || — use `A; if ($?) { B }`:\n  "
            + "\n  ".join(offenders),
        )

    def test_the_sweep_actually_inspects_powershell_blocks(self):
        """Guard the guard: if no blocks are found, the test above proves nothing."""
        seen = sum(
            1 for path in PLUGIN.rglob("*.md") for _ in powershell_blocks(path)
        )
        self.assertGreater(seen, 0, "found no PowerShell block lines to check")


# PowerShell automatic variables a reader may write in capitals. PowerShell variable names
# are case-insensitive, so `$HOME` IS the automatic `$HOME` and reads no environment
# variable by mistake. Only names that are automatic variables belong here.
POWERSHELL_AUTOMATIC_VARIABLES = {
    "ARGS", "ERROR", "FALSE", "HOME", "HOST", "INPUT", "LASTEXITCODE", "MATCHES", "NULL",
    "PID", "PROFILE", "PSHOME", "PSVERSIONTABLE", "PWD", "TRUE",
}

# `$NAME` with NAME in capitals (two or more characters), braced or not, and not escaped
# with a backtick. `$env:NAME`, `$Env:NAME` and `${env:NAME}` never match, because `env`
# is not all capitals; `$ENV:NAME` matches `ENV` and is excluded below as the scope.
BARE_CAPS_VARIABLE = re.compile(r"(?<![\w`])\$\{?([A-Z][A-Z0-9_]+)\b(:?)")


def bare_caps_variables(line):
    """The all-caps `$NAME`s in one PowerShell line that read no `env:` scope."""
    found = []
    for match in BARE_CAPS_VARIABLE.finditer(line):
        name, colon = match.group(1), match.group(2)
        if name == "ENV" and colon:
            continue
        if name in POWERSHELL_AUTOMATIC_VARIABLES:
            continue
        found.append(name)
    return found


def bare_caps_offenders(paths):
    offenders = []
    for path in paths:
        for number, line in powershell_blocks(path):
            for name in bare_caps_variables(line):
                offenders.append("%s:%d: $%s in %s" % (path, number, name, line.strip()))
    return offenders


class NoBareEnvironmentVariablesInPowerShellBlocks(unittest.TestCase):
    """INV-167, #505: an environment variable is read as `$env:NAME`, never `$NAME`."""

    OLD_LINES = (
        'Test-Path -Path "$SENZING_DIR\\data"',
        'Test-Path -Path "$SENZING_DIR\\..\\data"',
    )

    def test_no_shipped_powershell_fence_reads_a_bare_caps_variable(self):
        offenders = bare_caps_offenders(sorted(PLUGIN.rglob("*.md")))
        self.assertEqual(
            [],
            offenders,
            "In PowerShell `$NAME` is an unset PowerShell variable; read the environment "
            "variable as `$env:NAME`:\n  " + "\n  ".join(offenders),
        )

    def test_negative_control_the_old_step_8_lines_are_caught(self):
        for line in self.OLD_LINES:
            with self.subTest(line=line):
                self.assertEqual(["SENZING_DIR"], bare_caps_variables(line))

    def test_negative_control_the_sweep_catches_the_old_line_in_a_fence(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            for lang in sorted(POWERSHELL_LANGS):
                with self.subTest(lang=lang):
                    doc = Path(tmp) / ("step8-%s.md" % lang)
                    doc.write_text(
                        "2. Check:\n\n   ```%s\n   %s\n   ```\n" % (lang, self.OLD_LINES[0]),
                        encoding="utf-8",
                    )
                    self.assertEqual(1, len(bare_caps_offenders([doc])))

    def test_a_bash_fence_is_not_swept(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "bash.md"
            doc.write_text('```bash\ntest -d "$SENZING_DIR/data"\n```\n', encoding="utf-8")
            self.assertEqual([], bare_caps_offenders([doc]))

    def test_env_scoped_and_automatic_variables_pass(self):
        for line in (
            'Test-Path "$env:SENZING_DIR\\lib\\Sz.dll"',
            'Test-Path "$Env:SENZING_DIR\\lib\\Sz.dll"',
            'Test-Path "$ENV:SENZING_DIR\\lib\\Sz.dll"',
            'Test-Path "${env:SENZING_DIR}\\lib\\Sz.dll"',
            "if ($LASTEXITCODE -ne 0) { Write-Output $PWD }",
            'Join-Path $HOME "x"; $PID',
            "Write-Output \"`$SENZING_DIR is literal here\"",
            "$supportPath = $SupportDir",
        ):
            with self.subTest(line=line):
                self.assertEqual([], bare_caps_variables(line))

    def test_a_caps_name_outside_the_allowlist_is_still_caught(self):
        self.assertEqual(["SENZING_ROOT"], bare_caps_variables('Join-Path ${SENZING_ROOT} "data"'))
        self.assertEqual(["PATH"], bare_caps_variables('Write-Output "$PATH"'))


if __name__ == "__main__":
    unittest.main()
