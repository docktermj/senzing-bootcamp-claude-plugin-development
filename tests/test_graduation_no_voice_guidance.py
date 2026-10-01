"""Graduation tells the bootcamper why their video has no voice, and how to get one.

When the recap video renders with no voice, the bootcamper should never have to ask "Why is there
no sound?" (P3-20). The renderer's `Voice: none (…)` line (#339) names one of three reasons, and
graduation handles each (#340):

* **No speech engine found:** the closing announcement names the platform's engine, an install
  hint the bootcamper runs themselves, and a re-render command with resolved absolute paths.
  On Linux the hint is chosen from `/etc/os-release`: apt, dnf, pacman or zypper, with a generic
  fallback. macOS: `say` is built in, `brew install espeak-ng` is the fallback. Windows:
  System.Speech comes with Windows PowerShell 5.1, and `pwsh` alone cannot load it.
* **An engine voiced no scene:** the engine is named, with no install hint.
* **`--no-voice`:** nothing about installing.

Step 1c's status line notes only that the video has no voice, the closing announcement never
calls a voiceless video "narrated", the guide never runs `sudo` or a system package manager
(INV-066), and the guidance is a statement that never blocks graduation (INV-048, INV-340).

Each property is a function that returns its problems for a given text, so the negative
controls below run the same check over a copy of the skill with one piece removed and confirm
that it fails.

Stdlib only. These tests assert that the skill *states* the guidance; only `dry-run` phase 3 can
observe a live run following it.

Source issue: #340 (part of #331).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRADUATION = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "graduation" / "SKILL.md"
RENDERER = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "generate_recap_video.py"

NO_ENGINE = "Voice: none (no speech engine found)"
VOICED_NO_SCENE = "Voice: none (<engine> voiced no scene)"
NO_VOICE_FLAG = "Voice: none (--no-voice)"

#: The issue's four Linux install hints and the fallback, restated here as the spec the
#: skill's table is checked against.
LINUX_HINTS = {
    "apt": "sudo apt install espeak-ng",
    "dnf": "sudo dnf install espeak-ng",
    "pacman": "sudo pacman -S espeak-ng",
    "zypper": "sudo zypper install espeak-ng",
}
LINUX_FALLBACK = "install `espeak-ng` with your package manager"

#: Real `/etc/os-release` (ID, ID_LIKE) pairs, and the hint each must get.
OS_RELEASES = [
    ("ubuntu", "debian", LINUX_HINTS["apt"]),
    ("debian", "", LINUX_HINTS["apt"]),
    ("linuxmint", "ubuntu debian", LINUX_HINTS["apt"]),
    ("fedora", "", LINUX_HINTS["dnf"]),
    ("rhel", "fedora", LINUX_HINTS["dnf"]),
    ("centos", "rhel fedora", LINUX_HINTS["dnf"]),
    ("rocky", "rhel centos fedora", LINUX_HINTS["dnf"]),
    ("arch", "", LINUX_HINTS["pacman"]),
    ("manjaro", "arch", LINUX_HINTS["pacman"]),
    ("opensuse-leap", "suse opensuse", LINUX_HINTS["zypper"]),
    ("opensuse-tumbleweed", "opensuse suse", LINUX_HINTS["zypper"]),
    ("sles", "suse", LINUX_HINTS["zypper"]),
    ("alpine", "", LINUX_FALLBACK),
    ("nixos", "", LINUX_FALLBACK),
    (None, None, LINUX_FALLBACK),  # no /etc/os-release at all
]

#: Package-manager commands the guide must never run itself.
SYSTEM_INSTALLERS = re.compile(r"\b(?:sudo|apt|apt-get|dnf|yum|pacman|zypper|brew)\b")


def read():
    return GRADUATION.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def step_1c(text):
    start = text.index("### 1c.")
    return text[start:text.index("\n## Step 2:", start)]


def no_voice_section(text):
    step = step_1c(text)
    start = step.index("#### When the video has no voice")
    return step[start:]


def closing(text):
    return text[text.index("## Mandatory closing step"):]


def closing_video_rule(text):
    """The closing step's video paragraphs: from the INV-340 naming rule to the PDF note."""
    body = closing(text)
    start = body.index("**(INV-340) Also name the graduation video")
    return body[start:body.index("**If any Step 1b verification check was skipped", start)]


def no_voice_example(text):
    """The closing step's worked sentence for a video with no voice."""
    body = closing(text)
    start = body.index("When the video has no voice because no speech engine was found")
    quote = body.index("\n> ", start)
    return body[quote + 1:body.index("\n\n", quote + 1)]


def table(text, header_start):
    """Body rows of the Markdown table whose header row starts with `header_start`."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(header_start):
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append([cell.strip() for cell in row.strip().strip("|").split("|")])
            return rows
    return None


def os_release_rows(text):
    """[(names, hint)] from the Linux table: names are the backticked ids in the first cell,
    with a trailing `*` for "a name starting ...", or None for the fallback row."""
    rows = table(no_voice_section(text), "| `ID` / `ID_LIKE` names")
    if rows is None:
        return None
    out = []
    for first, hint in rows:
        names = re.findall(r"`([a-z0-9-]+)`", first)
        if "starting" in first:
            names[-1] += "*"
        hint = hint.strip()
        if hint.startswith("`") and hint.endswith("`"):
            hint = hint[1:-1]
        out.append((None if first.startswith("none of these") else names, hint))
    return out


def choose_hint(rows, os_id, id_like):
    """Apply the step's stated rule: the first row whose names appear in ID, then in ID_LIKE."""
    def matches(names, value):
        for word in (value or "").split():
            for name in names:
                if name.endswith("*") and word.startswith(name[:-1]):
                    return True
                if word == name:
                    return True
        return False
    for field in (os_id, id_like):
        for names, hint in rows:
            if names and matches(names, field):
                return hint
    return next(hint for names, hint in rows if names is None)


# --- the checks: each returns a list of problems, empty when the text is right ---------------

def problems_with_the_three_cases(text):
    problems = []
    rows = table(no_voice_section(text), "| `Voice:` line")
    if rows is None:
        return ["Step 1c has no table of the three `Voice: none (…)` cases"]
    cases = {first.strip("`"): squash(what) for first, what in rows}
    if set(cases) != {NO_ENGINE, VOICED_NO_SCENE, NO_VOICE_FLAG}:
        problems.append("the cases are %s, not the renderer's three" % sorted(cases))
    if NO_ENGINE in cases and not all(
            w in cases[NO_ENGINE] for w in ("speech engine", "install hint", "re-render command")):
        problems.append("the no-engine case must give the engine, install hint and re-render "
                        "command")
    if VOICED_NO_SCENE in cases and not (
            "names `<engine>`" in cases[VOICED_NO_SCENE]
            and "no install hint" in cases[VOICED_NO_SCENE]):
        problems.append("the voiced-no-scene case must name the engine and give no install hint")
    if NO_VOICE_FLAG in cases and "nothing about installing" not in cases[NO_VOICE_FLAG]:
        problems.append("the --no-voice case must say nothing about installing")
    return problems


def problems_with_linux(text):
    rows = os_release_rows(text)
    if rows is None:
        return ["Step 1c has no `/etc/os-release` table for the Linux install hint"]
    problems = []
    hints = [hint for _names, hint in rows]
    for manager, hint in LINUX_HINTS.items():
        if hint not in hints:
            problems.append("the %s hint `%s` is missing" % (manager, hint))
    if LINUX_FALLBACK not in hints:
        problems.append("the generic fallback is missing")
    if "`/etc/os-release`" not in no_voice_section(text):
        problems.append("the Linux hint is not chosen from `/etc/os-release`")
    if not problems:
        for os_id, id_like, expected in OS_RELEASES:
            got = choose_hint(rows, os_id, id_like)
            if got != expected:
                problems.append("ID=%s ID_LIKE=%r gets %r, not %r"
                                % (os_id, id_like, got, expected))
    return problems


def problems_with_macos_and_windows(text):
    section = squash(no_voice_section(text))
    problems = []
    for needed in ("`say` is built in to macOS, so not finding it is unusual",
                   "`brew install espeak-ng` as the fallback",
                   "the renderer tries `espeak-ng` after `say`"):
        if needed not in section:
            problems.append("macOS: missing %r" % needed)
    for needed in ("System.Speech, which comes with Windows PowerShell 5.1 (`powershell.exe`)",
                   "PowerShell 7 (`pwsh`) alone cannot load it",
                   "\"not loadable\"",
                   "There is no install command to give"):
        if needed not in section:
            problems.append("Windows: missing %r" % needed)
    return problems


def command_templates(text):
    """The two re-render command templates: (POSIX, Windows)."""
    section = no_voice_section(text)
    posix = re.search(r"\*\*Linux and macOS\*\* \(POSIX[^\n]*\n\s*`([^`\n]+)`", section)
    windows = re.search(r"\*\*Windows\*\* \(PowerShell[^\n]*\n\s*`([^`\n]+)`", section)
    return (posix.group(1) if posix else None, windows.group(1) if windows else None)


def problems_with_the_re_render_command(text):
    section = squash(no_voice_section(text))
    problems = []
    for needed in ("resolved absolute paths, so it runs as-is in the bootcamper's own terminal",
                   "`${CLAUDE_PLUGIN_ROOT}` is unset there, so never write it",
                   "**The interpreter Step 1c rendered with:**",
                   "**The renderer:** the absolute path",
                   "**The project root:** the absolute path",
                   "The storyboard is kept"):
        if needed not in section:
            problems.append("the command rule is missing %r" % needed)
    posix, windows = command_templates(text)
    if posix is None or windows is None:
        return problems + ["a POSIX or Windows command template is missing"]
    for name, cmd, sep, quote in (("POSIX", posix, "/", "'"), ("Windows", windows, "\\", '"')):
        if "${CLAUDE_PLUGIN_ROOT}" in cmd or "<this-skill-dir>" in cmd:
            problems.append("the %s command names an unresolved plugin root" % name)
        for part in ("%s<interpreter>%s" % (quote, quote), "%s<renderer>%s" % (quote, quote),
                     "--storyboard %s<project>%sdocs%svideo%sstoryboard.json%s"
                     % (quote, sep, sep, sep, quote),
                     "--output %s<project>%sdocs%sbootcamp_recap.mp4%s" % (quote, sep, sep, quote),
                     "--project-root %s<project>%s" % (quote, quote)):
            if part not in cmd:
                problems.append("the %s command lacks %r" % (name, part))
    if not windows.startswith('& "<interpreter>"'):
        problems.append("the Windows command must use PowerShell's `&` call operator")
    example = no_voice_example(text)
    paths = re.findall(r"'([^']+)'", example)
    if len(paths) != 5:
        problems.append("the worked example's command must quote five resolved paths")
    elif not all(p.startswith("/") for p in paths):
        problems.append("the worked example's command has a relative path: %s" % paths)
    if "${CLAUDE_PLUGIN_ROOT}" in example:
        problems.append("the worked example's command names ${CLAUDE_PLUGIN_ROOT}")
    return problems


def problems_with_the_status_line(text):
    step = squash(step_1c(text))
    problems = []
    if ("When the `Voice:` line is `Voice: none (…)`, that line only notes there is no voice: "
            "\"🎬 Your graduation video is at `docs/bootcamp_recap.mp4` (2:03), with no voice.\""
            not in step):
        problems.append("Step 1c's status line does not note that there is no voice")
    if "Keep the reason and any guidance for the closing announcement" not in step:
        problems.append("Step 1c's status line must leave the guidance to the closing")
    return problems


def problems_with_the_closing(text):
    rule = squash(closing_video_rule(text))
    problems = []
    for needed in ("⛔ **(INV-340) Call the video narrated only when the renderer's `Voice:` line "
                   "named an engine.**",
                   "\"with captions and music, no voice\"",
                   "\"with captions, no voice\" when the renderer printed "
                   "`Music: off (storyboard)`",
                   "for `no speech engine found`, the platform's speech engine, its install hint "
                   "and the re-render command",
                   "for `<engine> voiced no scene`, the engine that could not voice the "
                   "narration, with no install hint",
                   "for `--no-voice`, nothing more"):
        if needed not in rule:
            problems.append("the closing rule is missing %r" % needed)
    example = no_voice_example(text)
    if "narrated" in example:
        problems.append("the no-voice example calls the video narrated")
    for needed in ("with captions and music, no voice", "sudo apt install espeak-ng",
                   "--project-root"):
        if needed not in example:
            problems.append("the no-voice example lacks %r" % needed)
    if example.count("generate_recap_video.py") != 1:
        problems.append("the no-voice example must give the re-render command exactly once")
    return problems


def problems_with_installing(text):
    """The guide never runs sudo or a system package manager: the rule is stated, and no fenced
    command block in Step 1c or the closing carries one."""
    problems = []
    if ("⛔ **(INV-066, INV-340) The install hint is the bootcamper's to run.** Never run `sudo` "
            "or a system package manager" not in squash(no_voice_section(text))):
        problems.append("the never-install rule is not stated")
    for where, region in (("Step 1c", step_1c(text)), ("the closing", closing(text))):
        for block in re.findall(r"```[a-z]*\n(.*?)```", region, re.S):
            if SYSTEM_INSTALLERS.search(block):
                problems.append("a command block in %s runs a system installer" % where)
    return problems


def problems_with_blocking(text):
    problems = []
    for where, region in (("the no-voice guidance", no_voice_section(text)),
                          ("the closing's video rule", closing_video_rule(text)),
                          ("the no-voice example", no_voice_example(text))):
        if "👉" in region:
            problems.append("%s asks a 👉 question" % where)
    if ("⛔ **(INV-048, INV-340) This guidance is a statement, never a question, and it never "
            "blocks graduation.**" not in squash(no_voice_section(text))):
        problems.append("the statement-and-never-blocking rule is not stated")
    return problems


CHECKS = (problems_with_the_three_cases, problems_with_linux, problems_with_macos_and_windows,
          problems_with_the_re_render_command, problems_with_the_status_line,
          problems_with_the_closing, problems_with_installing, problems_with_blocking)


class TheGuidanceIsStated(unittest.TestCase):

    def test_the_renderer_still_prints_the_three_reasons(self):
        """The skill keys on these texts, so they must still be the renderer's own."""
        source = RENDERER.read_text(encoding="utf-8")
        for line in ('print("Voice: none (--no-voice)")',
                     'print("Voice: none (no speech engine found)")',
                     'print(f"Voice: none ({engine.name} voiced no scene)")'):
            with self.subTest(line=line):
                self.assertIn(line, source)

    def test_every_check_passes_on_the_shipped_skill(self):
        text = read()
        for check in CHECKS:
            with self.subTest(check=check.__name__):
                self.assertEqual([], check(text))

    def test_the_offer_and_install_offer_stay_the_only_questions(self):
        self.assertEqual(2, step_1c(read()).count("👉"))


class NegativeControls(unittest.TestCase):
    """Each removal must turn its check red; otherwise the check asserts nothing."""

    def assertFlags(self, check, old, new=""):
        text = read()
        self.assertIn(old, text, "the negative control's target text has moved")
        self.assertNotEqual([], check(text.replace(old, new, 1)),
                            "%s did not notice %r being removed" % (check.__name__, old))

    def test_a_missing_case(self):
        self.assertFlags(problems_with_the_three_cases,
                         "| `Voice: none (--no-voice)` | nothing about installing; graduation "
                         "never passes `--no-voice`, so this case is defensive |\n")

    def test_an_install_hint_for_the_voiced_no_scene_case(self):
        self.assertFlags(problems_with_the_three_cases, "no install hint, because the engine is "
                         "installed", "the install hint")

    def test_each_linux_hint_and_the_fallback(self):
        for hint in list(LINUX_HINTS.values()) + [LINUX_FALLBACK]:
            with self.subTest(hint=hint):
                self.assertFlags(problems_with_linux, " %s |" % hint
                                 if hint == LINUX_FALLBACK else " `%s` |" % hint, " |")

    def test_a_wrong_linux_mapping(self):
        self.assertFlags(problems_with_linux, "| `fedora`, `rhel`, `centos` |",
                         "| `rhel`, `centos` |")

    def test_the_macos_statement(self):
        self.assertFlags(problems_with_macos_and_windows, "`say` is built in to macOS")

    def test_the_macos_fallback(self):
        self.assertFlags(problems_with_macos_and_windows, "Give\n  `brew install espeak-ng` as "
                         "the fallback")

    def test_the_windows_statement(self):
        self.assertFlags(problems_with_macos_and_windows, "PowerShell 7 (`pwsh`) alone cannot "
                         "load it")

    def test_an_unresolved_plugin_root_in_the_command(self):
        self.assertFlags(problems_with_the_re_render_command, "`'<interpreter>' '<renderer>'",
                         "`'<interpreter>' '${CLAUDE_PLUGIN_ROOT}/scripts/generate_recap_video.py'")

    def test_a_relative_path_in_the_example(self):
        self.assertFlags(problems_with_the_re_render_command,
                         "--storyboard '/home/ada/projects/my-bootcamp/docs/video/storyboard.json'",
                         "--storyboard 'docs/video/storyboard.json'")

    def test_a_missing_explicit_project_root(self):
        self.assertFlags(problems_with_the_re_render_command,
                         " --project-root \"<project>\"`", "`")

    def test_the_status_line(self):
        self.assertFlags(problems_with_the_status_line, ", with no voice.\"", ".\"")

    def test_a_narrated_video_with_no_voice(self):
        self.assertFlags(problems_with_the_closing,
                         "> And your 2-minute graduation video, with captions",
                         "> And your narrated 2-minute graduation video, with captions")

    def test_the_closing_rule(self):
        self.assertFlags(problems_with_the_closing, "or \"with captions, no voice\" when the "
                         "renderer printed `Music: off (storyboard)`")

    def test_a_command_block_that_installs(self):
        self.assertFlags(problems_with_installing,
                         "python3 -m venv data/temp/recap-venv    # only if it does not exist yet",
                         "sudo apt install espeak-ng")

    def test_the_never_install_rule(self):
        self.assertFlags(problems_with_installing, "⛔ **(INV-066, INV-340) The install hint is "
                         "the bootcamper's to run.**")

    def test_a_question_in_the_guidance(self):
        self.assertFlags(problems_with_blocking, "There is no install command to give.",
                         "👉 **Shall I install it?**")


if __name__ == "__main__":
    unittest.main()
