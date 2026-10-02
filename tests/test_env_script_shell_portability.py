"""A sourced env script must locate itself in the shell the bootcamper actually has.

Module 2 mandates a project-local ``src/scripts/senzing-env.sh`` and documents *sourcing*
it into the interactive shell that launches the JVM. The idiom anyone reaches for to make
a script find itself — ``${BASH_SOURCE[0]}`` — is a bash array that expands to **empty**
under zsh, which is macOS's default shell. The script keeps running, resolves the project
root to the wrong directory, exports nothing useful, and the failure surfaces much later.

The reported symptom was ``Unable to get settings``, described in the spec as an SDK error.
Re-verification against MCP server 1.32.1 (2026-07-28) says otherwise: that string carries
no SENZ code because it is not an engine error at all — it is the null-check in Senzing's
own official snippets (``senzing/code-snippets-v4``, e.g.
``java/snippets/information/GetVersion.java`` and the C# equivalents), which print
``Unable to get settings.`` and throw when ``SENZING_ENGINE_CONFIGURATION_JSON`` is unset.
That guard tests for **unset**, not empty, which is why the guidance forbids exporting an
empty value: an empty export sails past the SDK's own check and fails deeper.

So these tests do two different jobs. Most assert the guidance is stated where a reader
meets it. The ones in ``TheDocumentedIdiomActuallyWorks`` **extract the fenced block from
the skill and run it**, because a path-resolution idiom that is merely present but wrong
is exactly the defect being fixed. The zsh half of that is skipped where zsh is not
installed and says so rather than passing quietly.

#328 moved the root marker. The script is written at Step 3 and sourced from Step 4 on, but
its guard demanded ``config/engine_config.json``, which only Step 8 writes, so every earlier
source failed with a message blaming path resolution for what was step order. The guard now
checks ``config/bootcamp_progress.json`` (project setup creates it), and while the engine
configuration is absent the script skips only that one export, with a one-line notice.
``TheScriptLoadsBeforeStep8`` runs those cases in every installed shell, with a sentinel export
inserted at the template's platform-exports placeholder to prove that section still runs, and
``NegativeControls`` runs the same checks against the pre-#328 template and against mutants.

Enforces **INV-175** (a sourced script resolves itself in the default shell, verifies the path it
computed, and never exits the bootcamper's shell) and its 2026-10-02 note (#328: the root marker
and the pre-Step-8 branch). It executes the shipped template in bash, and in zsh only where zsh is
installed, skipping with a reason otherwise; it does **not** establish behavior in a live session.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_02 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
PHASE_1 = SKILLS / "module-03-system-verification" / "phase1-verification.md"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
ONBOARDING_FLOW = SKILLS / "bootcamp-onboarding" / "onboarding-flow.md"

ANCHOR = '<a id="env-script-path-resolution"></a>'
SETTINGS_VAR = "SENZING_ENGINE_CONFIGURATION_JSON"
ROOT_MARKER = "config/bootcamp_progress.json"
#: The template's placeholder for the platform exports (filled from sdk_guide at run time).
PLACEHOLDER = "# Platform-specific exports"
#: Stands in for those exports: if it is exported, the platform section ran.
SENTINEL = "SZ_TEST_PLATFORM_SECTION"


def flat(path):
    """Collapse whitespace and strip blockquote markers so prose assertions survive wrapping."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


def documented_idiom():
    """The first ```bash block after the anchor — the snippet a bootcamper would copy."""
    text = MODULE_02.read_text(encoding="utf-8")
    start = text.index(ANCHOR)
    match = re.search(r"```bash\n(.*?)\n```", text[start:], re.S)
    assert match, "no fenced bash block follows the path-resolution anchor"
    return match.group(1)


def root_guard_markers(idiom):
    """The files the fail-loudly root guard tests: every `[ ! -f "$_sz_root/<file>" ]`
    whose branch reports a path-resolution fault."""
    markers = []
    for m in re.finditer(r'if \[ ! -f "\$_sz_root/([^"]+)" \]; then\n(.*?)\n(?:fi|elif|else)',
                         idiom, re.S):
        if "path-resolution fault" in m.group(2):
            markers.append(m.group(1))
    return markers


def with_sentinel(idiom):
    """The idiom with a sentinel export inserted at the platform-exports placeholder."""
    lines = idiom.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(PLACEHOLDER)]
    assert len(hits) == 1, "expected one %r placeholder, found %d" % (PLACEHOLDER, len(hits))
    lines.insert(hits[0], "export %s=ran" % SENTINEL)
    return "\n".join(lines)


#: The template exactly as it shipped before #328 (comments trimmed; the code is verbatim),
#: kept so the negative controls below run against the defect itself, not a paraphrase of it.
PRE_328_IDIOM = r"""if [ -n "${ZSH_VERSION:-}" ]; then
  _sz_self=${(%):-%x}
else
  _sz_self=${BASH_SOURCE[0]:-$0}
fi
_sz_root=$(cd -- "$(dirname -- "$_sz_self")/../.." && pwd)
if [ ! -f "$_sz_root/config/engine_config.json" ]; then
  printf 'senzing-env.sh: resolved project root has no config/engine_config.json\n' >&2
  printf 'senzing-env.sh:   resolved root: %s\n' "$_sz_root" >&2
  printf 'senzing-env.sh:   this is a path-resolution fault, not your Senzing install\n' >&2
  unset _sz_self _sz_root
  return 1 2>/dev/null || exit 1
fi
_sz_settings=$(cat -- "$_sz_root/config/engine_config.json")
if [ -z "$_sz_settings" ]; then
  printf 'senzing-env.sh: %s is empty — refusing to export an empty configuration\n' \
    "$_sz_root/config/engine_config.json" >&2
  unset _sz_self _sz_root _sz_settings
  return 1 2>/dev/null || exit 1
fi
export SENZING_PROJECT_ROOT="$_sz_root"
export SENZING_ENGINE_CONFIGURATION_JSON="$_sz_settings"
# Platform-specific exports (SENZING_ROOT, DYLD_LIBRARY_PATH / LD_LIBRARY_PATH, jar
unset _sz_self _sz_root _sz_settings"""


class ProjectFixture:
    """A throwaway project tree with the documented idiom installed as senzing-env.sh.

    `progress` writes the root marker, config/bootcamp_progress.json, which project setup
    creates before Module 2; `progress=False` is a wrong root. `settings=None` is a project
    before Step 8, which has not written config/engine_config.json yet.
    """

    def __init__(self, settings='{"PIPELINE": {}}', progress=True, idiom=None):
        self.dir = Path(tempfile.mkdtemp(prefix="szenv-"))
        # realpath: macOS /var is a symlink to /private/var, and `cd && pwd` resolves it.
        self.root = Path(os.path.realpath(self.dir)) / "proj"
        (self.root / "src" / "scripts").mkdir(parents=True)
        (self.root / "config").mkdir()
        if progress:
            (self.root / ROOT_MARKER).write_text("{}\n", encoding="utf-8")
        if settings is not None:
            (self.root / "config" / "engine_config.json").write_text(settings, encoding="utf-8")
        self.script = self.root / "src" / "scripts" / "senzing-env.sh"
        body = documented_idiom() if idiom is None else idiom
        self.script.write_text(body + "\n", encoding="utf-8")

    def source(self, shell, cwd=None):
        """Source the script from `shell` and report what it exported.

        The probe reports after a failed source too, so "nothing exported" is observable,
        and it exits with the source's status. SETTINGS_STATE is `set` only when the
        variable is set at all, which is how unset is told apart from empty.
        """
        program = (
            '. "$1"; _rc=$?; '
            'printf "ROOT=%%s\\n" "$SENZING_PROJECT_ROOT"; '
            'printf "SETTINGS=%%s\\n" "$%(v)s"; '
            'printf "SETTINGS_STATE=%%s\\n" "${%(v)s+set}"; '
            'printf "SENTINEL=%%s\\n" "$%(s)s"; '
            'exit $_rc' % {"v": SETTINGS_VAR, "s": SENTINEL}
        )
        # Scrub inherited values, or a maintainer's own exported settings would read as the
        # script having set them.
        env = {k: v for k, v in os.environ.items()
               if k not in (SETTINGS_VAR, "SENZING_PROJECT_ROOT", SENTINEL)}
        return subprocess.run(
            [shell, "-c", program, "probe", str(self.script)],
            capture_output=True,
            text=True,
            cwd=str(cwd or self.dir),
            env=env,
        )

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class TheDocumentedIdiomActuallyWorks(unittest.TestCase):
    """Running the snippet, not just finding it — the defect was a snippet-shaped mistake."""

    def setUp(self):
        self.fx = ProjectFixture()
        self.addCleanup(self.fx.cleanup)

    def test_bash_resolves_the_project_root(self):
        got = self.fx.source("bash")
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertIn("ROOT=%s" % self.fx.root, got.stdout)

    def test_bash_exports_the_engine_configuration(self):
        got = self.fx.source("bash")
        self.assertIn('SETTINGS={"PIPELINE": {}}', got.stdout)

    def test_the_root_does_not_depend_on_the_working_directory(self):
        """The original bug resolved against the caller's cwd instead of the script."""
        elsewhere = self.fx.root / "config"
        got = self.fx.source("bash", cwd=elsewhere)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertIn("ROOT=%s" % self.fx.root, got.stdout)

    def test_zsh_resolves_the_same_root_as_bash(self):
        zsh = shutil.which("zsh")
        if not zsh:
            self.skipTest("zsh is not installed here — the zsh branch is NOT runtime-verified")
        from_bash = self.fx.source("bash")
        from_zsh = self.fx.source(zsh)
        self.assertEqual(from_zsh.returncode, 0, from_zsh.stderr)
        self.assertIn("ROOT=%s" % self.fx.root, from_zsh.stdout)
        self.assertEqual(
            re.search(r"ROOT=(.*)", from_zsh.stdout).group(1),
            re.search(r"ROOT=(.*)", from_bash.stdout).group(1),
        )

    def test_bash_tolerates_the_zsh_only_expansion_in_the_untaken_branch(self):
        """If bash choked parsing ${(%):-%x}, the branch would break the shell it fixes."""
        self.assertIn("${(%):-%x}", documented_idiom())
        got = self.fx.source("bash")
        self.assertNotIn("bad substitution", got.stderr.lower())
        self.assertNotIn("syntax error", got.stderr.lower())


class AMisresolvedRootFailsLoudly(unittest.TestCase):
    """INV-111: name the path you computed rather than exporting a wrong one."""

    def test_a_missing_marker_file_fails_and_prints_the_resolved_root(self):
        fx = ProjectFixture(progress=False)
        self.addCleanup(fx.cleanup)
        got = fx.source("bash")
        self.assertNotEqual(got.returncode, 0, "a wrong root must not succeed silently")
        self.assertIn("resolved root:", got.stderr)
        self.assertIn(str(fx.root), got.stderr, "the message must name the path it computed")

    def test_it_points_at_the_script_not_at_the_senzing_install(self):
        fx = ProjectFixture(progress=False)
        self.addCleanup(fx.cleanup)
        self.assertRegex(
            fx.source("bash").stderr, r"(?i)path-resolution fault, not your Senzing install"
        )

    def test_an_empty_configuration_is_refused_rather_than_exported(self):
        """The SDK snippets' own guard tests for unset, so an empty export defeats it."""
        fx = ProjectFixture(settings="")
        self.addCleanup(fx.cleanup)
        got = fx.source("bash")
        self.assertNotEqual(got.returncode, 0)
        self.assertRegex(got.stderr, r"(?i)refusing to export an empty configuration")
        self.assertNotIn('SETTINGS=""', got.stdout)

    def test_it_returns_instead_of_exiting_so_sourcing_cannot_kill_the_shell(self):
        fx = ProjectFixture(progress=False)
        self.addCleanup(fx.cleanup)
        got = subprocess.run(
            ["bash", "-c", '. "$1" ; printf "SHELL_SURVIVED\\n"', "sh", str(fx.script)],
            capture_output=True,
            text=True,
        )
        self.assertIn("SHELL_SURVIVED", got.stdout, "a sourced script must return, never exit")

    def test_the_guidance_says_return_not_exit(self):
        text = flat(MODULE_02)
        self.assertRegex(text, r"(?i)`return 1`, never `exit 1`")
        self.assertRegex(text, r"(?i)`set -e` leaks into their session|`set -e` leaks")


def probe(idiom, shell, **fixture):
    """Source `idiom` (sentinel inserted) in a fresh project; return (fixture root, result,
    {name: value} parsed from the probe's report)."""
    fx = ProjectFixture(idiom=with_sentinel(idiom), **fixture)
    try:
        got = fx.source(shell)
    finally:
        fx.cleanup()
    report = dict(re.findall(r"(?m)^(ROOT|SETTINGS|SETTINGS_STATE|SENTINEL)=(.*)$", got.stdout))
    return fx.root, got, report


def before_step8_problems(idiom, shell):
    """A project with the root marker and no config/engine_config.json yet (Steps 4-7)."""
    root, got, report = probe(idiom, shell, settings=None)
    problems = []
    if got.returncode != 0:
        problems.append("returns %d before Step 8" % got.returncode)
    if report.get("ROOT") != str(root):
        problems.append("does not export SENZING_PROJECT_ROOT before Step 8")
    if report.get("SENTINEL") != "ran":
        problems.append("skips the platform exports before Step 8")
    if report.get("SETTINGS_STATE") == "set":
        problems.append("sets %s with no engine configuration" % SETTINGS_VAR)
    notice = [line for line in got.stderr.splitlines() if line.strip()]
    if len(notice) != 1:
        problems.append("prints %d lines, not a one-line notice" % len(notice))
    if not re.search(r"(?i)not written yet", got.stderr):
        problems.append("the notice does not say the engine configuration is not written yet")
    if not re.search(r"(?i)source this script again after Step 8", got.stderr):
        problems.append("the notice does not say to source the script again after Step 8")
    return problems


def wrong_root_problems(idiom, shell):
    """No root marker at the computed root; engine_config.json present, so it cannot pass."""
    root, got, report = probe(idiom, shell, progress=False)
    problems = []
    if got.returncode == 0:
        problems.append("a wrong root returns 0")
    if str(root) not in got.stderr:
        problems.append("the message does not name the computed root")
    if not re.search(r"(?i)path-resolution fault", got.stderr):
        problems.append("the message does not call it a path-resolution fault")
    if "engine_config.json" in got.stderr:
        problems.append("the message names engine_config.json as the marker")
    if report.get("ROOT") or report.get("SETTINGS_STATE") == "set":
        problems.append("a wrong root exports something")
    return problems


def empty_config_problems(idiom, shell):
    """An engine_config.json that exists but is empty is refused, and nothing is exported."""
    _, got, report = probe(idiom, shell, settings="")
    problems = []
    if got.returncode == 0:
        problems.append("an empty configuration returns 0")
    if not re.search(r"(?i)refusing to export an empty configuration", got.stderr):
        problems.append("an empty configuration is not refused by name")
    if report.get("SETTINGS_STATE") == "set":
        problems.append("an empty configuration is exported")
    if report.get("ROOT"):
        problems.append("an empty configuration still exports SENZING_PROJECT_ROOT")
    return problems


def both_present_problems(idiom, shell):
    """After Step 8: both variables exported and the platform section run, return 0."""
    root, got, report = probe(idiom, shell)
    problems = []
    if got.returncode != 0:
        problems.append("returns %d with both files present" % got.returncode)
    if report.get("ROOT") != str(root):
        problems.append("does not export SENZING_PROJECT_ROOT after Step 8")
    if report.get("SETTINGS") != '{"PIPELINE": {}}':
        problems.append("does not export %s after Step 8" % SETTINGS_VAR)
    if report.get("SENTINEL") != "ran":
        problems.append("skips the platform exports after Step 8")
    if got.stderr.strip():
        problems.append("prints a notice after Step 8: %r" % got.stderr.strip())
    return problems


CASES = (before_step8_problems, wrong_root_problems, empty_config_problems,
         both_present_problems)


class _EveryStepInOneShell:
    """#328's four cases against the shipped template, in the shell named by `shell`."""

    shell = "bash"

    def check(self, case):
        self.assertEqual([], case(documented_idiom(), self.shell))

    def test_it_loads_before_step8_writes_the_engine_configuration(self):
        self.check(before_step8_problems)

    def test_a_wrong_root_still_fails_loudly_on_the_new_marker(self):
        self.check(wrong_root_problems)

    def test_an_empty_configuration_is_still_refused(self):
        self.check(empty_config_problems)

    def test_both_files_present_is_unchanged(self):
        self.check(both_present_problems)


class TheScriptLoadsBeforeStep8InBash(_EveryStepInOneShell, unittest.TestCase):
    shell = "bash"


class TheScriptLoadsBeforeStep8InZsh(_EveryStepInOneShell, unittest.TestCase):
    def setUp(self):
        zsh = shutil.which("zsh")
        if not zsh:
            self.skipTest("zsh is not installed here — the zsh branch is NOT runtime-verified")
        self.shell = zsh


class NegativeControls(unittest.TestCase):
    """Each check fails on the defect it exists for: the pre-#328 template, and mutants of
    the shipped one that break exactly one case."""

    def test_the_pre_328_template_is_caught_before_step8(self):
        problems = before_step8_problems(PRE_328_IDIOM, "bash")
        for expected in ("returns 1 before Step 8",
                         "does not export SENZING_PROJECT_ROOT before Step 8",
                         "skips the platform exports before Step 8",
                         "the notice does not say the engine configuration is not written yet",
                         "the notice does not say to source the script again after Step 8"):
            with self.subTest(expected=expected):
                self.assertIn(expected, problems)

    def test_the_pre_328_template_passes_a_wrong_root_holding_engine_config(self):
        problems = wrong_root_problems(PRE_328_IDIOM, "bash")
        self.assertIn("a wrong root returns 0", problems)
        self.assertIn("a wrong root exports something", problems)

    def test_the_pre_328_marker_is_caught_by_the_marker_check(self):
        self.assertEqual(["config/engine_config.json"], root_guard_markers(PRE_328_IDIOM))

    def test_the_pre_328_wrong_root_message_names_engine_config(self):
        broken = PRE_328_IDIOM.replace('"$_sz_root/config/engine_config.json" ]',
                                       '"$_sz_root/%s" ]' % ROOT_MARKER, 1)
        self.assertNotEqual(broken, PRE_328_IDIOM, "the control did not change the template")
        self.assertIn("the message names engine_config.json as the marker",
                      wrong_root_problems(broken, "bash"))

    def test_an_early_return_in_the_absent_branch_is_caught(self):
        """The skip must fall through: returning early skips the platform exports."""
        idiom = documented_idiom()
        at = idiom.index("source this script again after Step 8")
        eol = idiom.index("\n", at)
        broken = idiom[:eol + 1] + "  return 0\n" + idiom[eol + 1:]
        problems = before_step8_problems(broken, "bash")
        self.assertIn("skips the platform exports before Step 8", problems)

    def test_an_empty_export_in_the_absent_branch_is_caught(self):
        """Unset, not empty: the SDK snippets' guard tests for unset."""
        idiom = documented_idiom()
        at = idiom.index("source this script again after Step 8")
        eol = idiom.index("\n", at)
        broken = idiom[:eol + 1] + '  export %s=""\n' % SETTINGS_VAR + idiom[eol + 1:]
        self.assertIn("sets %s with no engine configuration" % SETTINGS_VAR,
                      before_step8_problems(broken, "bash"))

    def test_a_multi_line_notice_is_caught(self):
        idiom = documented_idiom()
        at = idiom.index("source this script again after Step 8")
        eol = idiom.index("\n", at)
        broken = idiom[:eol + 1] + "  printf 'second line\\n' >&2\n" + idiom[eol + 1:]
        self.assertIn("prints 2 lines, not a one-line notice", before_step8_problems(broken, "bash"))

    def test_exporting_the_root_before_the_refusal_is_caught(self):
        idiom = documented_idiom()
        line = 'export SENZING_PROJECT_ROOT="$_sz_root"\n'
        self.assertEqual(1, idiom.count(line))
        broken = idiom.replace(line, "")
        at = broken.index("# --- engine configuration")
        broken = broken[:at] + line + broken[at:]
        self.assertIn("an empty configuration still exports SENZING_PROJECT_ROOT",
                      empty_config_problems(broken, "bash"))

    def test_a_dropped_settings_export_is_caught(self):
        idiom = documented_idiom()
        broken = re.sub(r"(?m)^\s*export %s=.*\n" % SETTINGS_VAR, "", idiom)
        self.assertNotEqual(broken, idiom, "the control did not change the template")
        self.assertIn("does not export %s after Step 8" % SETTINGS_VAR,
                      both_present_problems(broken, "bash"))


class TheRequirementIsStatedWhereTheScriptIsSpecified(unittest.TestCase):
    def test_the_canonical_rule_is_anchored(self):
        self.assertIn(ANCHOR, MODULE_02.read_text(encoding="utf-8"))

    def test_it_declares_itself_canonical(self):
        self.assertRegex(flat(MODULE_02), r"(?i)canonical statement of the rule")

    def test_it_names_the_default_shell_requirement(self):
        self.assertRegex(
            flat(MODULE_02),
            r"(?i)MUST resolve its own path in the platform's \*default\* shell, not only in bash",
        )

    def test_it_names_zsh_as_the_macos_default(self):
        self.assertRegex(flat(MODULE_02), r"(?i)on macOS that is \*\*zsh\*\*")

    def test_bash_source_is_never_recommended_unqualified(self):
        """BASH_SOURCE may appear only where it is being warned about or branched on."""
        text = MODULE_02.read_text(encoding="utf-8")
        for match in re.finditer(r"BASH_SOURCE", text):
            window = text[max(0, match.start() - 400) : match.end() + 400]
            with self.subTest(pos=match.start()):
                self.assertRegex(
                    window,
                    r"(?i)bash-only|empty under zsh|ZSH_VERSION|wrong project root|wrong root",
                    "BASH_SOURCE must never appear as an unqualified recommendation",
                )


class GroundRulesCarriesTheRuleBesideTheWindowsOne(unittest.TestCase):
    """Both supported platforms' shell semantics belong in one place."""

    def test_the_section_exists(self):
        self.assertIn("## Sourced scripts and the default shell", GROUND_RULES.read_text(encoding="utf-8"))

    def test_it_sits_with_the_windows_shell_guidance(self):
        text = GROUND_RULES.read_text(encoding="utf-8")
        self.assertLess(
            text.index("## Windows and PowerShell"),
            text.index("## Sourced scripts and the default shell"),
        )

    def test_it_links_the_canonical_idiom_rather_than_restating_it(self):
        text = flat(GROUND_RULES)
        self.assertIn("SKILL.md#env-script-path-resolution", text)
        self.assertRegex(text, r"(?i)Do not restate it; link to it")

    def test_it_states_the_no_exit_rule(self):
        self.assertRegex(
            flat(GROUND_RULES), r"(?i)sourced script must never `exit` or `set -e`"
        )


class TheSymptomIsNamedWhereItLands(unittest.TestCase):
    def test_module_2_troubleshooting_connects_the_symptom_to_the_script(self):
        text = flat(MODULE_02)
        self.assertRegex(text, r"(?i)`Unable to get settings`, or an empty `%s`" % SETTINGS_VAR)
        self.assertRegex(text, r"(?i)env script's path resolution, not Senzing")

    def test_it_says_the_symptom_carries_no_senz_code(self):
        """Routing a non-engine error through explain_error_code wastes the lookup."""
        for path in (MODULE_02, PHASE_1):
            with self.subTest(file=path.name):
                self.assertRegex(flat(path), r"(?i)no SENZ code")

    def test_it_attributes_the_string_to_the_snippet_guard_not_the_engine(self):
        """The re-check's finding: this is the sample program's own null-check."""
        for path in (MODULE_02, PHASE_1):
            with self.subTest(file=path.name):
                text = flat(path)
                self.assertRegex(text, r"(?i)null-check in Senzing's own official snippets")
                self.assertRegex(text, r"(?i)is \*\*unset\*\*|when `%s` is unset" % SETTINGS_VAR)

    def test_the_snippet_finding_carries_its_provenance(self):
        """INV-080: server version and date, and the tool that established it."""
        for path in (MODULE_02, PHASE_1):
            with self.subTest(file=path.name):
                self.assertRegex(
                    flat(path), r"(?i)`search_docs`.{0,60}1\.32\.1, 2026-07-28|1\.32\.1, 2026-07-28"
                )

    def test_verification_checks_it_before_reaching_for_explain_error_code(self):
        text = PHASE_1.read_text(encoding="utf-8")
        self.assertLess(
            text.index("If the failure names no SENZ code at all"),
            text.index('Call `explain_error_code(error_code="<code>"'),
        )

    def test_step_1a_list_numbering_stays_contiguous(self):
        """A stale '3.' after inserting an item renders as a restarted list."""
        text = PHASE_1.read_text(encoding="utf-8")
        block = text[text.index("### Step 1a"): text.index("### Step 2:")]
        markers = re.findall(r"(?m)^(\d+)\. ", block)
        self.assertEqual(markers, ["1", "2", "3", "4"], "Step 1a's ordered list must be 1-4")


class TheSourcingRuleIsNotRelaxed(unittest.TestCase):
    """This spec adds portability; it does not loosen the same-shell requirement."""

    def test_the_same_shell_sentence_is_unchanged(self):
        self.assertRegex(
            flat(MODULE_02),
            r"\*\*That is why `senzing-env\.sh` must be sourced in the same shell that launches "
            r"the JVM\*\* — not merely created\.",
        )

    def test_windows_keeps_its_own_script_and_idiom(self):
        text = flat(MODULE_02)
        self.assertRegex(text, r"(?i)Windows keeps its own script")
        self.assertIn("%~dp0", text)

    def test_no_zsh_material_is_imposed_on_windows(self):
        self.assertRegex(flat(MODULE_02), r"(?i)none of the zsh material applies there")


class TheSnippetStaysLanguageAgnostic(unittest.TestCase):
    """INV-001/INV-052: the fix concerns the shell, not the bootcamper's language."""

    def test_the_idiom_mentions_no_programming_language(self):
        idiom = documented_idiom().lower()
        for lang in ("python", "java", "csharp", "c#", "rust", "typescript", "node"):
            with self.subTest(language=lang):
                self.assertNotIn(lang, idiom)

    def test_platform_specific_paths_are_deferred_to_mcp(self):
        """No hardcoded DYLD/LD values — sdk_guide owns those (INV-080)."""
        idiom = documented_idiom()
        self.assertRegex(idiom, r"sdk_guide\(topic='install'")
        self.assertNotRegex(idiom, r"(?m)^\s*export (DYLD|LD)_LIBRARY_PATH=")


class TheEnvVarNameIsTheDocumentedOne(unittest.TestCase):
    """Re-confirmed via search_docs(category='configuration') on 1.32.1, 2026-07-28."""

    def test_the_idiom_exports_the_documented_variable(self):
        self.assertIn("export %s=" % SETTINGS_VAR, documented_idiom())

    def test_the_config_path_matches_what_module_2_creates(self):
        """The settings come from the file Step 8 writes; the root guard checks the file
        project setup writes, which exists at every step the script is sourced from (#328)."""
        idiom = documented_idiom()
        self.assertIn("config/engine_config.json", idiom)
        self.assertIn("config/engine_config.json", flat(MODULE_02))
        self.assertEqual(
            [ROOT_MARKER], root_guard_markers(idiom),
            "the root guard must test %s, not a file a later step writes" % ROOT_MARKER,
        )
        self.assertIn("Create `%s`" % ROOT_MARKER, flat(ONBOARDING_FLOW),
                      "project setup must still create the root marker the guard tests")


if __name__ == "__main__":
    unittest.main()
