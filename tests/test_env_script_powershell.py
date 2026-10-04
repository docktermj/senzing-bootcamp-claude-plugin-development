"""On Windows the env script is a dot-sourced ``senzing-env.ps1``, never a ``.bat`` (#419).

The ground rules assume Windows PowerShell 5.1. Module 2 used to write
``src\\scripts\\senzing-env.bat``, and every Windows site told the Bootcamper to run it. Run from
PowerShell, a ``.bat`` runs in a child ``cmd.exe``: the variables it sets never reach the
PowerShell window, and nothing reports it. The next program fails later, or finds the wrong
library. Module 2 now writes ``src\\scripts\\senzing-env.ps1``, and every site dot-sources it:
``. .\\src\\scripts\\senzing-env.ps1``.

These tests do three jobs:

1. **The sites (INV-246).** They are found by scanning every file under ``plugins/``, never from a
   list: no shipped file names ``senzing-env.bat`` except where it says an old project's ``.bat``
   is replaced; every prose block that names the ``.ps1`` says its Windows form is unverified on
   Windows PowerShell 5.1 here (INV-163); every block that gives the Linux/macOS load command and
   mentions Windows gives the ``.ps1`` too; and no site tells the Bootcamper to run the ``.ps1``
   without the leading ``. ``.
2. **The snippet's rules (INV-175, INV-166, INV-199).** Each rule the issue lists is pinned on the
   fenced ``powershell`` block after Module 2's ``env-script-windows`` anchor, and each pin has a
   negative control that breaks exactly that rule in an in-memory copy.
3. **Running it (INV-175: the shipped snippet MUST be executed by a test).**
   ``ThePs1RunsUnderPwsh`` installs the snippet in a throwaway project and dot-sources it under
   ``pwsh -NoProfile -Command``, then reads the variables the session holds afterwards. It covers
   before Step 8, after Step 8, an empty configuration, a wrong root, a run without dot-sourcing,
   and a working directory outside the project. ⚠️ **Where ``pwsh`` is not on ``PATH`` the class
   is skipped and names itself (INV-163).** GitHub's ``ubuntu-latest`` runner ships ``pwsh``, so CI
   runs it there. It is PowerShell 7 on Linux: nothing here runs the script on Windows or under
   Windows PowerShell 5.1, which is why each site says so.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _wrapped_text import blocks

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE_02 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"

ANCHOR = '<a id="env-script-windows"></a>'
SCRIPT = "senzing-env.ps1"
DOT_SOURCE = ". .\\src\\scripts\\senzing-env.ps1"
OLD_BAT = "senzing-env.bat"
#: The one wording a block naming the old `.bat` may use: it describes an old project.
OLD_BAT_CONTEXT = "only the old `senzing-env.bat`"
UNVERIFIED = "unverified on Windows PowerShell 5.1"
SETTINGS_VAR = "SENZING_ENGINE_CONFIGURATION_JSON"
ROOT_MARKER = "bootcamp_progress.json"
#: The snippet's placeholder for the platform settings (filled from sdk_guide at run time).
PLACEHOLDER = "# Platform-specific settings"
#: Stands in for those settings: if it is set, the platform section ran.
SENTINEL = "SZ_TEST_PLATFORM_SECTION"
SKIP_REASON = ("pwsh is not on PATH -- test_env_script_powershell.ThePs1RunsUnderPwsh is "
               "SKIPPED: the shipped senzing-env.ps1 is NOT executed here (INV-163)")

_FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def shipped_files():
    """Every UTF-8 text file under the plugin."""
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file():
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue


def prose_blocks(text):
    """(first line, collapsed text) for each Markdown block outside a code fence."""
    inside = False
    for block in blocks(text):
        if len(block) == 1 and _FENCE.match(block[0][1]):
            inside = not inside
            continue
        if inside:
            continue
        yield block[0][0], " ".join(" ".join(line for _, line in block).split())


def shipped_prose_blocks():
    for path, text in shipped_files():
        for lineno, flat in prose_blocks(text):
            yield "%s:%d" % (path.relative_to(REPO_ROOT), lineno), flat


def documented_snippet(text=None):
    """The first ```powershell block after the Windows anchor: the script Module 2 ships."""
    text = MODULE_02.read_text(encoding="utf-8") if text is None else text
    start = text.index(ANCHOR)
    match = re.search(r"```powershell\n(.*?)\n```", text[start:], re.S)
    assert match, "no fenced powershell block follows the env-script-windows anchor"
    return match.group(1)


def code_lines(snippet):
    """The snippet's lines with comments removed, for checks about what it runs."""
    out = []
    for line in snippet.split("\n"):
        code = line.split("#", 1)[0] if line.lstrip().startswith("#") else line
        out.append(code)
    return out


def snippet_problems(snippet):
    """Each rule #419 lists, checked on the snippet's text. Empty means every rule holds."""
    problems = []
    code = "\n".join(code_lines(snippet))
    if "$PSScriptRoot" not in code:
        problems.append("does not resolve its location from $PSScriptRoot")
    if not re.search(r"\$MyInvocation\.InvocationName\s+-ne\s+'\.'", code):
        problems.append("does not check that it was dot-sourced")
    if DOT_SOURCE not in code:
        problems.append("does not print the dot-sourced command")
    if (not re.search(r"Test-Path\b[^\n]*\$_sz_progress", code)
            or not re.search(r"Join-Path\b[^\n]*'%s'" % re.escape(ROOT_MARKER), code)):
        problems.append("does not check the root for config/bootcamp_progress.json")
    if "resolved root: $_sz_root" not in code:
        problems.append("the root failure does not name the resolved path")
    if not re.search(r"Get-Content\b[^\n]*-Raw\b[^\n]*-Encoding utf8", code):
        problems.append("does not read the configuration with an explicit UTF-8 encoding")
    if "IsNullOrWhiteSpace" not in code or "refusing to set an empty configuration" not in code:
        problems.append("does not refuse an empty configuration")
    if "not written yet, so %s is not set" % SETTINGS_VAR not in code:
        problems.append("has no pre-Step-8 notice naming the variable it leaves unset")
    if "dot-source this script again after Step 8" not in code:
        problems.append("the notice does not say to dot-source it again after Step 8")
    if re.search(r"(?im)^\s*exit\b|[;{]\s*exit\b", code):
        problems.append("calls exit, which INV-175 forbids in a sourced script")
    if code.count("return") < 3:
        problems.append("does not return from each refusal")
    if re.search(r"(?i)\bsetx\b", code):
        problems.append("runs setx, which writes the global environment (INV-199)")
    if "&&" in code or "||" in code:
        problems.append("uses bash chaining, a parser error on PowerShell 5.1 (INV-167)")
    if any(ord(ch) > 127 for ch in snippet):
        problems.append("is not ASCII; 5.1 reads a BOM-less .ps1 in the ANSI codepage")
    if "sdk_guide(topic='install', platform='windows'" not in snippet:
        problems.append("does not route the Windows variable set to sdk_guide (INV-080)")
    if sum(1 for line in snippet.split("\n") if line.startswith(PLACEHOLDER)) != 1:
        problems.append("has no single %r placeholder line" % PLACEHOLDER)
    return problems


class TheSnippetIsPinned(unittest.TestCase):
    """Every rule the issue lists for the `.ps1`, on the snippet Module 2 ships."""

    def test_the_shipped_snippet_meets_every_rule(self):
        self.assertEqual([], snippet_problems(documented_snippet()))

    def test_it_names_no_programming_language(self):
        """INV-002: the script concerns the shell; the language's variables come from sdk_guide."""
        snippet = documented_snippet().lower()
        for lang in ("python", "java", "csharp", "c#", "rust", "typescript", "node"):
            with self.subTest(language=lang):
                self.assertNotRegex(snippet, r"\b%s\b" % re.escape(lang))

    def test_there_is_one_windows_script_and_no_bat_template(self):
        text = MODULE_02.read_text(encoding="utf-8")
        self.assertEqual(1, text.count(ANCHOR))
        self.assertNotRegex(text, r"```(?:bat|batch|cmd)\b")


#: (rule broken, how) -- each mutant breaks exactly one rule in an in-memory copy.
MUTANTS = (
    ("does not resolve its location from $PSScriptRoot",
     lambda s: s.replace("$PSScriptRoot", "(Get-Location).Path")),
    ("does not check that it was dot-sourced",
     lambda s: s.replace("$MyInvocation.InvocationName -ne '.'", "$false")),
    ("does not print the dot-sourced command",
     lambda s: s.replace("'  . .\\src\\scripts\\senzing-env.ps1'", "'  senzing-env.ps1'")),
    ("does not check the root for config/bootcamp_progress.json",
     lambda s: s.replace("'bootcamp_progress.json'", "'engine_config.json'")),
    ("the root failure does not name the resolved path",
     lambda s: s.replace("resolved root: $_sz_root", "resolved root unknown")),
    ("does not read the configuration with an explicit UTF-8 encoding",
     lambda s: s.replace(" -Encoding utf8", "")),
    ("does not refuse an empty configuration",
     lambda s: s.replace("[string]::IsNullOrWhiteSpace($_sz_settings)", "$false")),
    ("calls exit, which INV-175 forbids in a sourced script",
     lambda s: s.replace("ErrorAction SilentlyContinue\n  return\n}",
                         "ErrorAction SilentlyContinue\n  exit 1\n}", 1)),
    ("runs setx, which writes the global environment (INV-199)",
     lambda s: s.replace("$env:SENZING_PROJECT_ROOT = $_sz_root",
                         "setx SENZING_PROJECT_ROOT $_sz_root")),
    ("is not ASCII; 5.1 reads a BOM-less .ps1 in the ANSI codepage",
     lambda s: s.replace("is empty - refusing", "is empty — refusing")),
)


class SnippetNegativeControls(unittest.TestCase):
    """Each pin fails on the defect it exists for."""

    def test_each_mutant_is_caught_by_its_own_check(self):
        shipped = documented_snippet()
        for expected, mutate in MUTANTS:
            with self.subTest(rule=expected):
                mutant = mutate(shipped)
                self.assertNotEqual(mutant, shipped, "the control did not change the snippet")
                self.assertIn(expected, snippet_problems(mutant))


def bat_sites():
    """Every shipped block naming the `.bat` outside the one allowed wording."""
    bad = []
    for path, text in shipped_files():
        for block in blocks(text):
            flat = " ".join(" ".join(line for _, line in block).split())
            if OLD_BAT in flat and not (OLD_BAT_CONTEXT in flat and SCRIPT in flat):
                bad.append("%s:%d" % (path.relative_to(REPO_ROOT), block[0][0]))
    return bad


class TheSitesAreFoundByScanning(unittest.TestCase):
    """INV-246: the site set is derived from the corpus, never listed here."""

    def test_no_shipped_file_names_the_bat_except_as_an_old_project(self):
        self.assertEqual([], bat_sites())

    def test_the_scan_sees_the_one_allowed_mention(self):
        """The old-project rule ("script absent") must still be found, or the scan is blind."""
        hits = [loc for loc, flat in shipped_prose_blocks() if OLD_BAT_CONTEXT in flat]
        self.assertEqual(1, len(hits), hits)
        self.assertIn("module-02-sdk-setup/SKILL.md", hits[0])

    def test_every_block_naming_the_ps1_says_it_is_unverified_on_5_1(self):
        sites = [(loc, flat) for loc, flat in shipped_prose_blocks() if SCRIPT in flat]
        self.assertGreaterEqual(len(sites), 6, "the scan found too few sites to be credible")
        missing = [loc for loc, flat in sites if UNVERIFIED not in flat]
        self.assertEqual([], missing)

    def test_every_load_command_with_a_windows_form_dot_sources_the_ps1(self):
        """A block that gives the bash load command and mentions Windows gives the .ps1 too."""
        sites = [(loc, flat) for loc, flat in shipped_prose_blocks()
                 if re.search(r"(?i)source `?src/scripts/senzing-env\.sh", flat) and "Windows" in flat]
        self.assertGreaterEqual(len(sites), 3, "the scan found too few sites to be credible")
        missing = [loc for loc, flat in sites if DOT_SOURCE not in flat]
        self.assertEqual([], missing)

    def test_no_site_runs_the_ps1_without_the_leading_dot(self):
        """`.\\src\\scripts\\senzing-env.ps1` alone runs it in its own scope."""
        bare = re.compile(r"(?<!\. )`?\.\\src\\scripts\\senzing-env\.ps1")
        bad = [loc for loc, flat in shipped_prose_blocks()
               if bare.search(flat) and "without the leading" not in flat]
        self.assertEqual([], bad)

    def test_the_scan_catches_a_planted_bat_site(self):
        """Negative control: a new site naming the `.bat` is found without being listed."""
        planted = "Run `src\\scripts\\senzing-env.bat` on Windows first.\n"
        flat = " ".join(planted.split())
        self.assertIn(OLD_BAT, flat)
        self.assertFalse(OLD_BAT_CONTEXT in flat and SCRIPT in flat)


class Module2SaysWhatToDo(unittest.TestCase):
    def setUp(self):
        self.flat = " ".join(re.sub(r"(?m)^\s*>\s?", "", MODULE_02.read_text(encoding="utf-8")).split())

    def test_the_execution_policy_fallback_is_process_scoped(self):
        """INV-199: the fallback changes only the current window."""
        self.assertIn("running scripts is disabled on this system", self.flat)
        self.assertIn("`Set-ExecutionPolicy -Scope Process Bypass`", self.flat)
        self.assertIn("then dot-source `%s` again" % DOT_SOURCE, self.flat)
        self.assertIn("It lasts only for that PowerShell window and changes no global "
                      "configuration (INV-199)", self.flat)
        self.assertNotRegex(self.flat, r"Set-ExecutionPolicy[^`]*-Scope (?:CurrentUser|LocalMachine) Bypass")

    def test_the_script_absent_rule_treats_an_old_bat_project_as_missing(self):
        self.assertIn("a project made before the `.ps1` that has only the old `senzing-env.bat` "
                      "counts as not there: write the `.ps1`", self.flat)
        self.assertIn("do not tell them to run the `.bat`", self.flat)

    def test_step_8_re_sources_the_ps1(self):
        self.assertIn("on Windows, dot-source `%s` again" % DOT_SOURCE, self.flat)

    def test_it_says_why_the_bat_was_replaced(self):
        self.assertIn("A `.bat` file run from PowerShell runs in a child `cmd.exe`, so the "
                      "variables it sets never reach the PowerShell window", self.flat)


def ps_quote(path):
    return "'%s'" % str(path).replace("'", "''")


class Project:
    """A throwaway project with the shipped snippet installed as src/scripts/senzing-env.ps1.

    `progress=False` is a wrong root. `settings=None` is a project before Step 8.
    """

    def __init__(self, settings='{"PIPELINE": {}}', progress=True, snippet=None):
        self.dir = Path(tempfile.mkdtemp(prefix="szps1-"))
        self.root = Path(os.path.realpath(self.dir)) / "proj"
        (self.root / "src" / "scripts").mkdir(parents=True)
        (self.root / "config").mkdir()
        if progress:
            (self.root / "config" / ROOT_MARKER).write_text("{}\n", encoding="utf-8")
        if settings is not None:
            (self.root / "config" / "engine_config.json").write_text(settings, encoding="utf-8")
        body = documented_snippet() if snippet is None else snippet
        lines = body.split("\n")
        at = [i for i, line in enumerate(lines) if line.startswith(PLACEHOLDER)]
        assert len(at) == 1, "expected one %r placeholder" % PLACEHOLDER
        lines.insert(at[0], "$env:%s = 'ran'" % SENTINEL)
        self.script = self.root / "src" / "scripts" / SCRIPT
        # UTF-8 with no BOM, as the Bootcamp writes every file (INV-166).
        self.script.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))

    def run(self, pwsh, call=".", cwd=None):
        """Load the script with `call` ('.' to dot-source, '&' to run it), then report the
        session's variables. Returns (result, {name: value})."""
        program = "\n".join([
            "%s %s" % (call, ps_quote(self.script)),
            "'ROOT=' + $env:SENZING_PROJECT_ROOT",
            "'SETTINGS=' + $env:%s" % SETTINGS_VAR,
            "if (Test-Path Env:%s) { 'SETTINGS_STATE=set' } else { 'SETTINGS_STATE=' }" % SETTINGS_VAR,
            "'SENTINEL=' + $env:%s" % SENTINEL,
            "'LEAKED=' + ((Get-Variable -Name '_sz_*' -ErrorAction SilentlyContinue "
            "| ForEach-Object { $_.Name }) -join ',')",
            "'SESSION_SURVIVED'",
        ])
        env = {k: v for k, v in os.environ.items()
               if k not in (SETTINGS_VAR, "SENZING_PROJECT_ROOT", SENTINEL)}
        got = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-Command", program],
                             capture_output=True, text=True, cwd=str(cwd or self.dir), env=env,
                             timeout=120)
        report = dict(re.findall(r"(?m)^(ROOT|SETTINGS|SETTINGS_STATE|SENTINEL|LEAKED)=(.*)$",
                                 got.stdout))
        return got, report

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def notices(got):
    """The script's own messages, from either stream (Write-Host reaches stdout under pwsh)."""
    return [line for line in (got.stdout + "\n" + got.stderr).splitlines()
            if line.startswith("senzing-env.ps1:")]


class ThePs1RunsUnderPwsh(unittest.TestCase):
    """The shipped snippet, dot-sourced under pwsh in a throwaway project (INV-175)."""

    @classmethod
    def setUpClass(cls):
        cls.pwsh = shutil.which("pwsh")
        if not cls.pwsh:
            raise unittest.SkipTest(SKIP_REASON)

    def project(self, **kw):
        fx = Project(**kw)
        self.addCleanup(fx.cleanup)
        return fx

    def assertSurvived(self, got):
        self.assertIn("SESSION_SURVIVED", got.stdout,
                      "the session did not survive: %s\n%s" % (got.stdout, got.stderr))

    def test_after_step_8_it_sets_everything(self):
        fx = self.project()
        got, report = fx.run(self.pwsh)
        self.assertSurvived(got)
        self.assertEqual(str(fx.root), report.get("ROOT"))
        self.assertEqual('{"PIPELINE": {}}', report.get("SETTINGS"))
        self.assertEqual("ran", report.get("SENTINEL"))
        self.assertEqual([], notices(got))
        self.assertEqual("", report.get("LEAKED"), "the script leaves its helper variables behind")

    def test_before_step_8_it_prints_one_notice_and_sets_the_rest(self):
        fx = self.project(settings=None)
        got, report = fx.run(self.pwsh)
        self.assertSurvived(got)
        self.assertEqual(str(fx.root), report.get("ROOT"))
        self.assertEqual("ran", report.get("SENTINEL"), "the platform section was skipped")
        self.assertEqual("", report.get("SETTINGS_STATE"), "%s was set" % SETTINGS_VAR)
        said = notices(got)
        self.assertEqual(1, len(said), said)
        self.assertIn("not written yet", said[0])
        self.assertIn("dot-source this script again after Step 8", said[0])
        self.assertEqual("", report.get("LEAKED"))

    def test_an_empty_configuration_is_refused_and_nothing_is_set(self):
        fx = self.project(settings="")
        got, report = fx.run(self.pwsh)
        self.assertSurvived(got)
        self.assertTrue(any("refusing to set an empty configuration" in n for n in notices(got)))
        self.assertEqual("", report.get("ROOT"))
        self.assertEqual("", report.get("SETTINGS_STATE"))
        self.assertEqual("", report.get("SENTINEL"))
        self.assertEqual("", report.get("LEAKED"))

    def test_a_wrong_root_names_the_resolved_path_and_the_session_survives(self):
        fx = self.project(progress=False)
        got, report = fx.run(self.pwsh)
        self.assertSurvived(got)
        said = " ".join(notices(got))
        self.assertIn("resolved root: %s" % fx.root, said)
        self.assertIn("path-resolution fault, not your Senzing install", said)
        self.assertEqual("", report.get("ROOT"))
        self.assertEqual("", report.get("SETTINGS_STATE"))
        self.assertEqual("", report.get("SENTINEL"))
        self.assertEqual("", report.get("LEAKED"))

    def test_run_without_dot_sourcing_it_prints_the_command_and_sets_nothing(self):
        fx = self.project()
        got, report = fx.run(self.pwsh, call="&")
        self.assertSurvived(got)
        self.assertIn(DOT_SOURCE, " ".join(notices(got)) + got.stdout)
        self.assertEqual("", report.get("ROOT"))
        self.assertEqual("", report.get("SETTINGS_STATE"))
        self.assertEqual("", report.get("SENTINEL"))

    def test_the_root_does_not_depend_on_the_working_directory(self):
        fx = self.project()
        got, report = fx.run(self.pwsh, cwd=fx.root / "config")
        self.assertSurvived(got)
        self.assertEqual(str(fx.root), report.get("ROOT"))

    def test_negative_control_a_dead_session_is_seen(self):
        """The survival check has teeth: a wrong-root branch that ends the process is caught.

        It ends the process with `[Environment]::Exit(1)`, not `exit`. The first CI run of this
        class (PR #432) measured that a dot-sourced `exit 1` under `pwsh -Command` ends only the
        script, and the caller's next statement still runs, so `exit` cannot serve as the control.
        `exit` stays forbidden by the static pin above, because INV-175 forbids it.
        """
        mutant = documented_snippet().replace(
            "ErrorAction SilentlyContinue\n  return\n}",
            "ErrorAction SilentlyContinue\n  [Environment]::Exit(1)\n}", 1)
        self.assertNotEqual(mutant, documented_snippet())
        fx = self.project(progress=False, snippet=mutant)
        got, _ = fx.run(self.pwsh)
        self.assertNotIn("SESSION_SURVIVED", got.stdout)


if __name__ == "__main__":
    unittest.main()
