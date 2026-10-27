"""The auto-test scripts `SKILL.md` runs directly are stored executable in git (#843, INV-419).

`.claude/skills/auto-test/SKILL.md` tells the maintainer to run the harness as
`.claude/skills/auto-test/autotest.py` and to refresh the baseline with
`.claude/skills/auto-test/mcp_probe.py update`. Until #843 git stored `autotest.py`,
`mcp_probe.py`, `walk.py` and `transcript_lint.py` as mode `100644`, so on a fresh
checkout each documented command failed with `Permission denied`.

⛔ **This test reads the git index, not the file on disk.** A checkout's file mode is
whatever git recorded, so the index is what every clone inherits; a local `chmod +x`
that was never staged passes an `os.access` check here and still ships `100644`. It
lists the four scripts with `git ls-files -s` and asserts mode `100755` for each.

⚠️ **Windows ignores the executable bit**, so the direct form cannot run there.
`SKILL.md` therefore keeps a `python3 .claude/skills/auto-test/…` form, and
`SkillMdKeepsAnInterpreterForm` asserts it does.

⚠️ **What a green run does NOT mean (INV-419 is not a compliance claim).** It means the four named scripts are `100755` in
the index and start with a `#!/usr/bin/env python3` line. It does not mean every script
`SKILL.md` runs directly is among the four, that the commands succeed, or that a fifth
script added later is executable.

Negative-controlled: `TheModeCheckIsNegativeControlled` sets each script back to
`100644` in a scratch repository's index, one at a time, and requires the check to name
exactly that script.

Run:  python3 -m unittest discover -s tests
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_REL = ".claude/skills/auto-test"
HARNESS = REPO_ROOT / HARNESS_REL
SKILL_MD = HARNESS / "SKILL.md"

# The scripts the auto-test harness runs, or SKILL.md invokes, directly.
SCRIPTS = ("autotest.py", "mcp_probe.py", "walk.py", "transcript_lint.py")
SHEBANG = "#!/usr/bin/env python3"
EXECUTABLE = "100755"


def index_modes(repo, paths):
    """Map each path to its mode in `repo`'s git index (`git ls-files -s`)."""
    done = subprocess.run(["git", "-C", str(repo), "ls-files", "-s", "--"] + list(paths),
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError("git ls-files -s failed in %s: %s" % (repo, done.stderr))
    modes = {}
    for line in done.stdout.splitlines():
        meta, _, path = line.partition("\t")
        if path:
            modes[path] = meta.split()[0]
    return modes


def not_executable(modes, paths):
    """The paths whose index mode is not 100755, with the mode found (None if untracked)."""
    return [(path, modes.get(path)) for path in paths if modes.get(path) != EXECUTABLE]


def has_interpreter_form(text):
    """True when the text runs an auto-test script through `python3`, the Windows form."""
    return ("python3 %s/" % HARNESS_REL) in text


@unittest.skipUnless(shutil.which("git"), "git reads the index this check asserts")
class TheScriptsAreStoredExecutable(unittest.TestCase):
    def test_each_script_is_mode_100755_in_the_index(self):
        paths = ["%s/%s" % (HARNESS_REL, name) for name in SCRIPTS]
        wrong = not_executable(index_modes(REPO_ROOT, paths), paths)
        self.assertEqual(wrong, [],
                         "auto-test scripts not stored as %s in git (path, mode): %s. "
                         "Run `git update-index --chmod=+x <path>`." % (EXECUTABLE, wrong))


class EachScriptHasAPython3Shebang(unittest.TestCase):
    def test_each_script_starts_with_the_shebang(self):
        """Line-scoped by design (#843): a shebang is the file's first line, by definition."""
        for name in SCRIPTS:
            with self.subTest(script=name):
                first = (HARNESS / name).read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first, SHEBANG,
                                 "%s must start with %r to run directly" % (name, SHEBANG))


class SkillMdKeepsAnInterpreterForm(unittest.TestCase):
    def test_skill_md_names_the_python3_form(self):
        self.assertTrue(has_interpreter_form(SKILL_MD.read_text(encoding="utf-8")),
                        "SKILL.md must keep a `python3 %s/…` form for Windows, which "
                        "ignores the executable bit" % HARNESS_REL)

    def test_the_form_check_is_negative_controlled(self):
        self.assertFalse(has_interpreter_form(
            "```console\n%s/autotest.py --walk\n```\n" % HARNESS_REL))
        self.assertTrue(has_interpreter_form("python3 %s/autotest.py\n" % HARNESS_REL))


@unittest.skipUnless(shutil.which("git"), "git builds the scratch index")
class TheModeCheckIsNegativeControlled(unittest.TestCase):
    """Set each script back to 100644 in a scratch index; the check must name it."""

    def _repo(self, tmp):
        repo = Path(tmp)
        for args in (["init", "--quiet"], ["config", "core.fileMode", "false"]):
            subprocess.run(["git", "-C", str(repo)] + args, check=True,
                           capture_output=True)
        paths = []
        for name in SCRIPTS:
            target = repo / HARNESS_REL / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(SHEBANG + "\n", encoding="utf-8")
            paths.append("%s/%s" % (HARNESS_REL, name))
        subprocess.run(["git", "-C", str(repo), "add", "--"] + paths, check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", str(repo), "update-index", "--chmod=+x", "--"] + paths,
                       check=True, capture_output=True)
        return repo, paths

    def test_all_executable_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, paths = self._repo(tmp)
            self.assertEqual(not_executable(index_modes(repo, paths), paths), [])

    def test_each_script_set_back_to_100644_is_named(self):
        for path in ["%s/%s" % (HARNESS_REL, name) for name in SCRIPTS]:
            with self.subTest(script=path), tempfile.TemporaryDirectory() as tmp:
                repo, paths = self._repo(tmp)
                subprocess.run(["git", "-C", str(repo), "update-index", "--chmod=-x", "--",
                                path], check=True, capture_output=True)
                self.assertEqual(not_executable(index_modes(repo, paths), paths),
                                 [(path, "100644")])

    def test_an_untracked_script_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, paths = self._repo(tmp)
            missing = "%s/absent.py" % HARNESS_REL
            self.assertEqual(not_executable(index_modes(repo, paths + [missing]),
                                            paths + [missing]),
                             [(missing, None)])


if __name__ == "__main__":
    unittest.main()
