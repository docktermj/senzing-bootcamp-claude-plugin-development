"""Module 2 Step 8 states one procedure for `config/engine_config.json`, and its Windows
SUPPORTPATH check tests the path the server returned (#505).

Two defects, one step:

1. **Two procedures.** Step 8 said the file is built from `environment.default_paths` and the
   `engine_config` blob "must NOT be written to disk as-is", and later said "Save the
   MCP-returned JSON directly to `config/engine_config.json`; do not modify the paths" -- while
   its own Windows and macOS checks then modified SUPPORTPATH.
2. **A Windows check that tested the wrong directory.** `Test-Path -Path "$SENZING_DIR\\data"`
   read an unset PowerShell variable (the environment variable is `$env:SENZING_DIR`), so it
   tested `\\data` on the current drive, then fell back to `$SENZING_DIR\\..\\data` and wrote
   that unexpanded string into SUPPORTPATH. `sdk_guide(topic='configure', platform='windows',
   language='csharp')` returns `support_path` = `%SENZING_DIR%\\..\\data`, the sibling
   directory itself, with all three `default_paths` carrying a literal `%SENZING_DIR%`
   (re-checked on MCP server 1.37.28, 2026-10-12, INV-080).

Each check is a function returning its problems, so a negative control can feed it a
mutated copy of the step and watch it fail. The bare-`$NAME` sweep over every shipped
PowerShell fence lives in `test_windows_powershell_guidance.py` (INV-167). The Windows block
is disclosed as unverified on Windows PowerShell 5.1 (INV-163); nothing here establishes
that it runs there.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_02 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-02-sdk-setup" / "SKILL.md"

STEP_START = "## Step 8: Create Engine Configuration"
STEP_END = "## Step 8a:"
WINDOWS_START = "**On Windows, verify the `SUPPORTPATH` the server returned"
MACOS_START = "**On macOS, the same check with the Homebrew paths:**"
LINUX_START = "⚠️ **Linux was not re-checked for this layout**"


def step_8(text):
    start = text.index(STEP_START)
    return text[start:text.index(STEP_END, start)]


def flat(text):
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


def windows_block(step):
    start = step.find(WINDOWS_START)
    if start < 0:
        return ""
    end = step.find("> **Why the Scoop layout differs:**", start)
    return step[start:end if end > start else len(step)]


def one_procedure_problems(step):
    problems = []
    text = flat(step)
    if re.search(r"(?i)Save the MCP-returned JSON directly", text):
        problems.append("the 'Save the MCP-returned JSON directly' sentence is back")
    if re.search(r"(?i)do not modify the paths", text):
        problems.append("'do not modify the paths' is back")
    if "MCP-returned JSON" in text or "MCP-returned configuration" in text:
        problems.append("a check still refers to 'the MCP-returned JSON/configuration'")
    if "Write `config/engine_config.json` from `environment.default_paths`" not in text:
        problems.append("the one-procedure statement is missing")
    return problems


def expansion_problems(step):
    problems = []
    text = flat(step)
    if not re.search(r"`config_path`, `resource_path` and `support_path`", text):
        problems.append("the three default_paths values are not all named")
    if "Expand every path value to an absolute path before writing it." not in text:
        problems.append("the expand-to-absolute rule is missing")
    if not re.search(r"never write a value that still contains `%SENZING_DIR%`, `\$SENZING_DIR`", text):
        problems.append("the never-write-a-variable rule is missing")
    if re.search(r"update SUPPORTPATH[^.]*to use `\$SENZING_DIR", text):
        problems.append("an instruction writes $SENZING_DIR into SUPPORTPATH")
    return problems


def windows_check_problems(step):
    block = windows_block(step)
    if not block:
        return ["the Windows check is missing"]
    problems = []
    text = flat(block)
    if "unverified on Windows PowerShell 5.1 here, INV-163" not in text:
        problems.append("the Windows block is not disclosed as unverified (INV-163)")
    if not re.search(r"If `\$env:SENZING_DIR` is empty, stop", text):
        problems.append("it does not stop on an unset $env:SENZING_DIR")
    if "test and write no path" not in text:
        problems.append("it does not forbid testing or writing a path when unset")
    if "if (-not $env:SENZING_DIR)" not in block:
        problems.append("the unset check is not in the block")
    if not re.search(r"ExpandEnvironmentVariables\('<support_path>'\)", block):
        problems.append("it does not expand the returned support_path")
    if "Test-Path -Path $supportPath -PathType Container" not in block:
        problems.append("it does not test the expanded directory")
    if not re.search(r'Test-Path -Path \(Join-Path \$supportPath "\*TransRules\.sz"\)', block):
        problems.append("it does not test the *TransRules.sz content")
    if "report the expanded path that was tested, and do not guess another one" not in text:
        problems.append("the failure branch does not report the tested path")
    if not re.search(r"wrong `SUPPORTPATH` \(`SENZ7426`\), not as a broken install", text):
        problems.append("missing *TransRules.sz is not reported as a wrong SUPPORTPATH")
    if re.search(r"\$SENZING_DIR\\(?:\.\.\\)?data", block):
        problems.append("the $SENZING_DIR\\data / ..\\data two-path probe is back")
    return problems


def scoop_note_problems(step):
    start = step.find("> **Why the Scoop layout differs:**")
    if start < 0:
        return ["the Scoop note is missing"]
    note = flat(step[start:step.index(MACOS_START)])
    problems = []
    if re.search(r"(?i)fall ?back to `\$SENZING_DIR", note) or "fallback to `$SENZING_DIR" in note:
        problems.append("the Scoop note still describes a $SENZING_DIR fallback")
    if "The server's `support_path` is that sibling directory itself" not in note:
        problems.append("the Scoop note does not say support_path is the sibling itself")
    return problems


# The macOS check's logic and the Linux text are out of scope (#505): pinned verbatim
# (whitespace-flattened), so an edit to either is a deliberate change to this test.
MACOS_LOGIC = (
    "`test -d \"$(brew --prefix)/opt/senzing/data\"`, and that it holds the transliteration "
    "modules: `ls \"$(brew --prefix)/opt/senzing/data\"/*TransRules.sz`.",
    "2. If it does not, the cask's own `etc/sz_engine_config.ini` is the likely source: its "
    "`SUPPORTPATH` does not resolve to a directory holding `*TransRules.sz`, whatever its literal.",
    "set `SUPPORTPATH` to `$(brew --prefix)/opt/senzing/data`, the `support_path` `sdk_guide` "
    "already returns.",
    "3. If neither path exists, report both that were tried rather than guessing a third.",
)
LINUX_TEXT = (
    "⚠️ **Linux was not re-checked for this layout** (verified 2026-07-31: `sdk_guide` was asked "
    "for `macos_arm` and `windows` only). Use the MCP-returned paths on Linux without "
    "modification, and if a Linux install ever produces `SENZ7426`, ask "
    "`sdk_guide(topic='install', platform='linux_apt' | 'linux_yum')` before assuming this case "
    "applies — do not widen it by inference."
)


def unchanged_problems(step):
    text = flat(step)
    problems = []
    for clause in MACOS_LOGIC:
        if clause not in text:
            problems.append("macOS logic changed: %s" % clause[:50])
    if LINUX_TEXT not in text:
        problems.append("the Linux text changed")
    if "1. Confirm the `SUPPORTPATH` in the JSON built from `default_paths` exists —" not in text:
        problems.append("macOS item 1 does not refer to the JSON built from default_paths")
    return problems


class Step8StatesOneProcedure(unittest.TestCase):
    def setUp(self):
        self.step = step_8(MODULE_02.read_text(encoding="utf-8"))

    def test_one_procedure(self):
        self.assertEqual([], one_procedure_problems(self.step))

    def test_every_default_path_is_expanded_before_writing(self):
        self.assertEqual([], expansion_problems(self.step))

    def test_windows_check_tests_the_returned_support_path(self):
        self.assertEqual([], windows_check_problems(self.step))

    def test_scoop_note_describes_no_fallback(self):
        self.assertEqual([], scoop_note_problems(self.step))

    def test_linux_text_and_macos_logic_are_unchanged(self):
        self.assertEqual([], unchanged_problems(self.step))


OLD_WINDOWS_PROBE = """Use `sdk_guide` with `topic='configure'` to generate the correct engine configuration JSON for
the user's platform and database choice. Save the MCP-returned JSON directly to
`config/engine_config.json`; do not modify the paths.

**On Windows, verify the `SUPPORTPATH` the server returned before saving the configuration**
(the same check the macOS one below makes; unverified on Windows PowerShell 5.1 here, INV-163):

1. Extract the SUPPORTPATH value from the MCP-returned configuration JSON.

   ```powershell
   Test-Path -Path "$SENZING_DIR\\data"
   ```

4. If the parent-level path exists, update SUPPORTPATH in the configuration JSON to use
   `$SENZING_DIR\\..\\data` before saving to `config/engine_config.json`.

> **Why the Scoop layout differs:** This is why the fallback to `$SENZING_DIR\\..\\data` is
> needed for Scoop installs.

"""


class NegativeControls(unittest.TestCase):
    """Each check fails on the defect it exists to catch."""

    def setUp(self):
        self.step = step_8(MODULE_02.read_text(encoding="utf-8"))

    def test_the_old_sentence_is_caught(self):
        mutated = self.step.replace(
            "**Write `config/engine_config.json`",
            "Save the MCP-returned JSON directly to `config/engine_config.json`; do not modify "
            "the paths.\n\n**Write `config/engine_config.json`",
        )
        problems = one_procedure_problems(mutated)
        self.assertIn("the 'Save the MCP-returned JSON directly' sentence is back", problems)
        self.assertIn("'do not modify the paths' is back", problems)

    def test_the_old_windows_block_is_caught(self):
        start = self.step.index(WINDOWS_START)
        end = self.step.index(MACOS_START)
        old = self.step[:start] + OLD_WINDOWS_PROBE + "\n" + self.step[end:]
        self.assertIn("the $SENZING_DIR\\data / ..\\data two-path probe is back",
                      windows_check_problems(old))
        self.assertIn("it does not stop on an unset $env:SENZING_DIR", windows_check_problems(old))
        self.assertTrue(one_procedure_problems(old))
        self.assertIn("an instruction writes $SENZING_DIR into SUPPORTPATH", expansion_problems(old))
        self.assertIn("the Scoop note still describes a $SENZING_DIR fallback",
                      scoop_note_problems(old))

    def test_dropping_the_trans_rules_check_is_caught(self):
        mutated = self.step.replace(
            'Test-Path -Path (Join-Path $supportPath "*TransRules.sz")', ""
        )
        self.assertIn("it does not test the *TransRules.sz content",
                      windows_check_problems(mutated))

    def test_dropping_the_unset_stop_is_caught(self):
        mutated = self.step.replace("If `$env:SENZING_DIR` is empty, stop", "If it is empty, go on")
        self.assertIn("it does not stop on an unset $env:SENZING_DIR",
                      windows_check_problems(mutated))

    def test_dropping_the_disclosure_is_caught(self):
        mutated = self.step.replace("unverified on Windows PowerShell 5.1 here, INV-163", "")
        self.assertIn("the Windows block is not disclosed as unverified (INV-163)",
                      windows_check_problems(mutated))

    def test_an_edit_to_the_macos_logic_or_linux_text_is_caught(self):
        mutated = self.step.replace("rather than guessing a third", "and guess a third")
        self.assertTrue(unchanged_problems(mutated))
        mutated = self.step.replace("do not widen it by inference", "widen it")
        self.assertIn("the Linux text changed", unchanged_problems(mutated))


if __name__ == "__main__":
    unittest.main()
