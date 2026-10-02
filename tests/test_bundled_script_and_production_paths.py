"""A path a step tells the guide to run must resolve where that step actually runs.

`deep-dive-audit-2026-07-30b`. Three path defects of one shape (a fourth, #325, is item 4),
none of which any existing test could see, because each is a *string in prose* that is only
wrong relative to a working directory no test had modeled.

1. **A bundled script invoked by a bare project-relative path.** Module 7 said:

       python3 scripts/generate_discoveries_pdf.py

   Every other bundled-script invocation in the plugin resolves as
   `${CLAUDE_PLUGIN_ROOT}/scripts/…` with a skill-relative fallback, because the script ships
   *inside the plugin* while the command runs in the *bootcamp project* — and the project
   layout (INV-050) has no top-level `scripts/`, only `src/scripts/`. Run from a project root
   the command exits 2, `can't open file`. It was the only invocation of that generator, and
   the discoveries deliverable is produced on every path, so the realistic outcome was a
   guaranteed deliverable silently reported missing (the surrounding text is explicitly
   "report exactly what failed and continue").

2. **A production copy that flattened a path its own copied code depends on.** Graduation
   copied `data/senzing-ready/**` to `production/data/` while copying `src/load/**`
   *verbatim* to `production/src/load/`. The loading code reads `data/senzing-ready/`
   (INV-084), so the handover project's loader pointed at a directory that did not exist.

3. **An install doc covering two of three supported platforms.** The Claude Code CLI section
   installed on "macOS or Linux" only, with no Windows route and no line sending a Windows
   reader to the Desktop path — while INV-001 makes Windows supported and INV-158 makes the
   CLI one of the two interfaces the install docs must document.

4. **A production copy that left out the registry its own copied code reads (#325).** Module 6
   Phase C step 17 has the orchestrator read each source's entry in `config/data_sources.yaml`
   when it runs (INV-320), and graduation copied `src/load/**` verbatim while copying nothing
   from `config/`. Step 2 now writes a projection of the registry to the same path under
   `production/` (INV-186), keeping only `version`, `name`, `file_path` and `format`, so no
   evaluation-only `load_subset:` limit reaches production.

Written as sweeps, not as three assertions about three lines, so the next one is caught too.

Enforces **INV-185** (a command run against a bundled script resolves it inside the plugin
via `${CLAUDE_PLUGIN_ROOT}`, never by a bare project-relative path -- the script ships in
the plugin while the command runs in the Bootcamper's project), which names this file.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
COMMANDS = PLUGIN / "commands"
SCRIPTS = PLUGIN / "scripts"
GRADUATION = SKILLS / "graduation" / "SKILL.md"
PHASE_C = SKILLS / "module-06-data-processing" / "phaseC-multi-source.md"
CLI_INSTALL_DOC = REPO_ROOT / "docs" / "README.md"

# The scripts that ship inside the plugin. A step that runs one of these is running a file
# that is NOT in the bootcamper's project, so the path has to be resolved, never assumed.
BUNDLED_SCRIPTS = sorted(p.name for p in SCRIPTS.glob("*.py"))

# How a resolved invocation is allowed to look. Either the env var the harness substitutes,
# or the explicit skill-relative fallback the plugin documents beside it, or a placeholder
# the surrounding prose resolves (module 3b's `<viz-server-path>`).
RESOLVED = (
    "${CLAUDE_PLUGIN_ROOT}",
    "<this-skill-dir>",
    "../../scripts/",
    "<helper>",
    "<viz-server-path>",
)


def prose_files():
    """Every file that can instruct the guide to run a command."""
    return sorted(SKILLS.rglob("*.md")) + sorted(COMMANDS.rglob("*.md"))


def invocation_lines():
    """(path, lineno, line) for each line invoking a bundled script with an interpreter."""
    out = []
    runner = re.compile(r"(?:^|\s)(?:python3?|py -3|[\w./\\-]*/(?:python3?|bin/python))\s")
    for path in prose_files():
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not runner.search(line):
                continue
            if any(name in line for name in BUNDLED_SCRIPTS):
                out.append((path, i, line.strip()))
    return out


#: Flags that belong to bundled helpers and to nothing else the guide runs. An instruction that
#: supplies these is parameterizing a bundled tool, whether or not it names one.
#:
#: ⚠️ **This exists because the sweep above cannot see the worse failure.** `invocation_lines()`
#: discovers invocations BY SCRIPT NAME, so it catches a *wrong* resolution and is blind to a
#: *missing* one. On 2026-08-18 both steps that require screenshot capture supplied `--url`,
#: `--tabs`, `--name` and `--query` and named no executable, deferring the identity to another
#: file — and a guide concluded capture was impossible "because browser automation was
#: unavailable" without ever looking for the tool the plugin ships. Twelve recap images were
#: lost, one module's unrecoverably, and the same script then captured 6 of 6 tabs first try.
#: The guard was built for a wrong path; the defect was no path at all.
HELPER_ONLY_FLAGS = ("--tabs", "--single", "--out-dir")

#: A line is exempt when it resolves a bundled script by any documented route, or is prose about
#: the flags rather than an instruction to run them.
RESOLVED_MARKERS = ("${CLAUDE_PLUGIN_ROOT}", "../../scripts/", "<helper>")


#: Distinguishes a COMMAND from PROSE ABOUT a command. Without this the sweep fires on
#: `module-completion.md`'s own explanation of what `--single` does, and on any sentence that
#: mentions a flag in backticks — five false positives on first run, all of them documentation
#: doing its job. A line is an instruction to run something when it sits in a fenced block or
#: carries an interpreter token; prose may discuss flags freely.
_RUNNER = re.compile(r"(?:^|\s)(?:python3?|py -3|[\w./\\-]*/(?:python3?|bin/python))\s")


def parameterized_without_a_script():
    """(path, lineno, line) for COMMANDS using helper-only flags with no resolved script path."""
    out = []
    for path in prose_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        in_fence = False
        for i, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if not any(f in line for f in HELPER_ONLY_FLAGS):
                continue
            if not (in_fence or _RUNNER.search(line)):
                continue  # prose about the flags, not an instruction to run them
            # A fenced invocation commonly names the script on a preceding continuation line.
            window = "\n".join(lines[max(0, i - 8):i + 3])
            if any(m in window for m in RESOLVED_MARKERS):
                continue
            if any(n in window for n in BUNDLED_SCRIPTS):
                continue
            out.append((path, i, line.strip()))
    return out


class AParameterizedInvocationNamesItsScript(unittest.TestCase):
    """INV-185's blind spot: flags supplied, executable never identified.

    Negative-controlled 2026-08-21 by deleting the script name from Module 3b's invocation and
    confirming this fails, then restoring it.
    """

    def test_the_flag_vocabulary_is_still_present_somewhere(self):
        """Non-vacuity: if no shipped step uses these flags, the check asserts nothing."""
        users = [
            (p, i) for p in prose_files()
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if any(f in line for f in HELPER_ONLY_FLAGS)
        ]
        self.assertTrue(
            users,
            "no shipped file uses %s, so this sweep is vacuous — either the flags were renamed "
            "or the capture instructions were removed" % (HELPER_ONLY_FLAGS,))

    def test_no_step_parameterizes_a_helper_without_naming_it(self):
        found = parameterized_without_a_script()
        self.assertEqual(
            [], ["%s:%d  %s" % (p.relative_to(REPO_ROOT), i, line) for p, i, line in found],
            "a step supplies bundled-helper flags without naming a resolved script. The flags "
            "then read as 'what the procedure will need' rather than 'what this bundled tool "
            "accepts', and a guide can conclude the capability is unavailable without ever "
            "looking for it — which is how twelve recap images were lost on 2026-08-18, one "
            "module's unrecoverably. Name the script with ${CLAUDE_PLUGIN_ROOT} and its "
            "skill-relative fallback (INV-185, INV-252) at the point of use.")


class BundledScriptsAreInvokedByAResolvedPath(unittest.TestCase):
    def test_the_sweep_finds_the_known_invocations(self):
        """A sweep that matches nothing would pass forever."""
        found = invocation_lines()
        self.assertGreaterEqual(
            len(found),
            5,
            "the invocation sweep matched almost nothing — its regex or the "
            "BUNDLED_SCRIPTS list has drifted, and it is no longer testing anything",
        )
        names = {n for _, _, line in found for n in BUNDLED_SCRIPTS if n in line}
        self.assertIn("generate_recap_pdf.py", names)
        self.assertIn("generate_discoveries_pdf.py", names)

    def test_no_step_runs_a_bundled_script_by_an_unresolved_path(self):
        problems = []
        for path, lineno, line in invocation_lines():
            if not any(marker in line for marker in RESOLVED):
                problems.append(f"{path.relative_to(REPO_ROOT)}:{lineno}  {line}")
        self.assertEqual(
            [],
            problems,
            "a bundled script is invoked by a path that does not resolve from the "
            "bootcamp project (the plugin's scripts/ is not the project's):\n  "
            + "\n  ".join(problems),
        )

    def test_the_discoveries_generator_is_reachable(self):
        """The one that was broken, named explicitly so a regression is unambiguous."""
        text = (
            SKILLS
            / "module-07-query-visualize-discover"
            / "phase1-query-visualize.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '"${CLAUDE_PLUGIN_ROOT}/scripts/generate_discoveries_pdf.py"',
            text,
            "Module 7 must resolve the discoveries generator inside the plugin",
        )
        self.assertNotRegex(
            text,
            r"(?m)^\s*python3 scripts/generate_discoveries_pdf\.py\s*$",
            "the bare project-relative invocation is back; it exits 2 from a project root",
        )


def copy_table_rows(text):
    """(source, destination) for each row of graduation's Step 2 copy table."""
    rows = []
    for line in text.splitlines():
        if line.startswith("| `") and "production/" in line:
            cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
            if len(cells) >= 2:
                rows.append((cells[0], cells[1]))
    return rows


def graduation_step(text, number):
    """Graduation's `## Step <number>:` section, up to the next `## ` heading."""
    start = text.index("\n## Step %s:" % number)
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def step17_registry_paths(phase_c):
    """The `config/` files Phase C step 17 tells the orchestrator to read when it runs."""
    paragraphs = [p for p in re.split(r"\n\s*\n", phase_c)
                  if "(INV-320) Then the orchestrator loads" in p]
    return {path for p in paragraphs
            for path in re.findall(r"`(config/[^`]+)`", p)}


def registry_rows_missing(phase_c, graduation):
    """Each registry step 17 reads that Step 2 does not land at its own path under production/."""
    rows = dict(copy_table_rows(graduation))
    return sorted(path for path in step17_registry_paths(phase_c)
                  if rows.get(path) != "production/" + path)


def projection_bullet(graduation, label):
    """The backticked items of Step 2's `- **<label>:**` projection bullet, or None."""
    m = re.search(r"(?ms)^- \*\*%s:\*\*(.*?)(?=^- \*\*|^\s*$)" % re.escape(label),
                  graduation_step(graduation, 2))
    return None if m is None else re.findall(r"`([^`]+)`", m.group(1))


#: The projection's allowlist (#325): what production's orchestrator needs and nothing more.
PROJECTION_KEEPS = {"version", "sources:", "name", "file_path", "format"}


def projection_problems(graduation):
    """Why Step 2's projection would carry an evaluation-only field, or [] when it would not."""
    keep, strip = (projection_bullet(graduation, "Keep only"),
                   projection_bullet(graduation, "Strip"))
    if keep is None or strip is None:
        return ["Step 2 has no **Keep only:** / **Strip:** projection bullet"]
    problems = []
    if set(keep) != PROJECTION_KEEPS:
        problems.append("Keep only names %s, not %s" % (sorted(keep), sorted(PROJECTION_KEEPS)))
    for field in ("load_subset:", "sample:"):
        if field not in strip:
            problems.append("Strip does not name %s" % field)
    return problems


def readme_names_the_registry(graduation):
    """Step 4's Configuration bullet names the registry and the subset sources' full load."""
    flat = " ".join(graduation_step(graduation, 4).split())
    m = re.search(r"\*\*Configuration names the registry\.\*\*(.*?)(?= - \*\*|$)", flat)
    return bool(m) and all(
        needle in m.group(1)
        for needle in ("`config/data_sources.yaml`", "`load_subset:`", "whole `file_path`"))


def report_lists_the_projection(graduation):
    """Step 5's files-generated table lists the projection."""
    flat = " ".join(graduation_step(graduation, 5).split())
    return "files-generated table (it lists `production/config/data_sources.yaml`" in flat


class ProductionCopyPreservesThePathsItsCodeUses(unittest.TestCase):
    """Copied code is not rewritten, so its inputs must land where it looks for them."""

    def _copy_table_rows(self):
        return copy_table_rows(GRADUATION.read_text(encoding="utf-8"))

    def test_the_copy_table_is_readable(self):
        rows = self._copy_table_rows()
        self.assertGreaterEqual(
            len(rows), 5, "graduation's Step 2 copy table no longer parses"
        )

    def test_senzing_ready_keeps_its_directory(self):
        rows = dict(self._copy_table_rows())
        dest = rows.get("data/senzing-ready/**")
        self.assertIsNotNone(dest, "the Senzing-ready copy row disappeared from Step 2")
        self.assertEqual(
            "production/data/senzing-ready/",
            dest,
            "the loading code is copied verbatim and reads data/senzing-ready/ "
            "(INV-084); flattening it to production/data/ ships a project whose "
            "loader points at a directory that does not exist",
        )

    def test_every_src_row_preserves_its_subdirectory(self):
        for source, dest in self._copy_table_rows():
            if source.startswith("src/"):
                self.assertEqual(
                    "production/" + source.replace("**", ""),
                    dest,
                    f"{source} must keep its path under production/ — copied code is "
                    "not rewritten, so a moved directory breaks its imports",
                )

    def test_the_excluded_raw_input_is_disclosed(self):
        """data/raw/ is excluded by design; a fast-pathed source's loader then has no input.

        Asserted per *paragraph* rather than by character distance: the disclosure is
        several wrapped sentences, and a proximity window either misses it or would pass
        on an unrelated mention elsewhere in an 850-line file.
        """
        text = GRADUATION.read_text(encoding="utf-8")
        self.assertIn("data/raw/", text, "the exclusion list lost data/raw/")

        paragraphs = [
            re.sub(r"\s+", " ", p)
            for p in re.split(r"\n\s*\n", text)
            if "fast-pathed source" in p
        ]
        self.assertTrue(
            paragraphs,
            "graduation no longer says what happens to a fast-pathed source's input, "
            "which data/raw/'s exclusion leaves out of production/",
        )
        disclosing = [
            p
            for p in paragraphs
            if "data/raw/" in p
            and "files-excluded" in p
            and "README" in p
        ]
        self.assertTrue(
            disclosing,
            "the fast-pathed paragraph must name data/raw/ as the excluded input AND "
            "route the disclosure to both the graduation report's files-excluded table "
            "and production/README.md — otherwise the missing input is silent.\n"
            "Paragraphs found:\n  " + "\n  ".join(paragraphs),
        )


    # -- #325: the registry the Phase C orchestrator reads ------------------------------

    def test_step17_still_names_the_registry_it_reads(self):
        """Not vacuous: the paragraph parser finds the registry, or the next test checks nothing."""
        self.assertEqual(
            {"config/data_sources.yaml"},
            step17_registry_paths(PHASE_C.read_text(encoding="utf-8")),
            "Phase C step 17's (INV-320) paragraph no longer parses, or reads another file",
        )

    def test_the_registry_step17_reads_keeps_its_path(self):
        """INV-186: the orchestrator is copied verbatim, so its registry lands where it looks."""
        missing = registry_rows_missing(PHASE_C.read_text(encoding="utf-8"),
                                        GRADUATION.read_text(encoding="utf-8"))
        self.assertEqual(
            [], missing,
            "Phase C step 17 tells the orchestrator to read these at run time, and graduation "
            "Step 2 does not write them to the same path under production/, so the copied "
            "loader stops at its registry lookup: %s" % missing,
        )

    def test_the_projection_carries_no_evaluation_only_field(self):
        self.assertEqual([], projection_problems(GRADUATION.read_text(encoding="utf-8")))

    def test_the_readme_configuration_names_the_registry(self):
        self.assertTrue(
            readme_names_the_registry(GRADUATION.read_text(encoding="utf-8")),
            "Step 4's **Configuration names the registry.** bullet must name "
            "`config/data_sources.yaml`, the sources that had a `load_subset:` block, and that "
            "production loads each one's whole `file_path`",
        )

    def test_the_report_lists_the_projection(self):
        self.assertTrue(
            report_lists_the_projection(GRADUATION.read_text(encoding="utf-8")),
            "Step 5's files-generated table must list production/config/data_sources.yaml",
        )

    def test_negative_controls(self):
        """Each check above fails on the defect it exists for."""
        graduation = GRADUATION.read_text(encoding="utf-8")
        phase_c = PHASE_C.read_text(encoding="utf-8")
        row = ("| `config/data_sources.yaml` | `production/config/data_sources.yaml` |")
        self.assertIn(row, graduation, "the control's copy-table row moved")

        # 1. The pre-#325 copy table: no registry row.
        without_row = "\n".join(l for l in graduation.splitlines() if not l.startswith(row))
        self.assertEqual(["config/data_sources.yaml"],
                         registry_rows_missing(phase_c, without_row))
        # 2. The registry flattened out of config/.
        flattened = graduation.replace(row, row.replace("production/config/", "production/"), 1)
        self.assertEqual(["config/data_sources.yaml"],
                         registry_rows_missing(phase_c, flattened))
        # 3. load_subset: kept, so production inherits the evaluation's cap.
        keep = "- **Keep only:** `version`,"
        self.assertIn(keep, graduation, "the control's Keep only bullet moved")
        leaky = graduation.replace(keep, "- **Keep only:** `load_subset:`, `version`,", 1)
        self.assertTrue(projection_problems(leaky))
        # 4. load_subset: dropped from the Strip list.
        unstripped = graduation.replace("including `load_subset:`, ", "including ", 1)
        self.assertNotEqual(graduation, unstripped, "the control's Strip entry moved")
        self.assertIn("Strip does not name load_subset:", projection_problems(unstripped))
        # 5. The README bullet gone.
        bullet = "**Configuration names the registry.**"
        self.assertFalse(readme_names_the_registry(graduation.replace(bullet, "", 1)))
        # 6. The report no longer lists the projection.
        listed = "(it lists\n`production/config/data_sources.yaml`"
        self.assertIn(listed, graduation, "the control's Step 5 wording moved")
        self.assertFalse(report_lists_the_projection(graduation.replace(listed, "(", 1)))


class InstallDocsCoverEverySupportedPlatform(unittest.TestCase):
    """INV-001 makes Windows supported; INV-158 makes the CLI a documented interface."""

    def test_the_cli_section_has_a_windows_route(self):
        text = CLI_INSTALL_DOC.read_text(encoding="utf-8")
        self.assertIn(
            "install.ps1",
            text,
            "the Claude Code CLI install section gives no Windows command "
            "(verified against the official setup docs: `irm https://claude.ai/install.ps1 | iex`)",
        )
        self.assertIn(
            "install.sh",
            text,
            "the macOS/Linux install command disappeared",
        )

    def test_no_install_step_claims_two_platforms_are_the_set(self):
        """'on macOS or Linux' with no Windows line is how the gap read as complete."""
        flat = re.sub(r"\s+", " ", CLI_INSTALL_DOC.read_text(encoding="utf-8"))
        self.assertNotIn(
            "Claude Code CLI on macOS or Linux",
            flat,
            "this phrasing presents two platforms as the whole supported set",
        )

    def test_the_windows_command_is_powershell_shaped(self):
        """INV-167: a PowerShell command must not carry bash chaining operators."""
        for line in CLI_INSTALL_DOC.read_text(encoding="utf-8").splitlines():
            if "install.ps1" in line:
                self.assertNotIn("&&", line, "bash chaining in a PowerShell command")
                self.assertNotIn("||", line, "bash chaining in a PowerShell command")


class TheProseSweepIsNotVacuous(unittest.TestCase):
    """`prose_files()` is skills + commands. If either half stops matching, the path
    checks pass over a smaller corpus and report clean."""

    def test_both_halves_contribute(self):
        found = prose_files()
        self.assertGreater(len(found), 20, "corpus shrank to %d files" % len(found))
        self.assertTrue(any("skills" in p.parts for p in found), "no skill .md found")
        self.assertTrue(any("commands" in p.parts for p in found), "no command .md found")


if __name__ == "__main__":
    unittest.main()
