"""#286: every `data/<dir>/` Module 6 names is copied at graduation, or excluded on purpose.

Module 6 wrote subset files under `data/subsets/`, and graduation's Step 2 neither copied the
directory nor named it on its **Exclude** list, so nothing said whether leaving it out of
`production/` was deliberate. This fails when a Module 6 skill file names a `data/<dir>/`
path that is neither a Source row of graduation's copy table nor an **Exclude** entry.

Scoped to Module 6 on purpose (#286): `data/mapping/`, `data/temp/` and `data/backups/`,
which other modules name, are a follow-up issue.

Stdlib-only and no `plugins/` import (INV-108): the files are read as text.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE6 = SKILLS / "module-06-data-processing"
GRADUATION = SKILLS / "graduation" / "SKILL.md"

STEP2 = "## Step 2: Build the production project"
EXCLUDE = "**Exclude (never copy):**"

#: A project-relative `data/<dir>/` path. The lookbehind keeps `production/data/…` out.
DATA_DIR = re.compile(r"(?<![\w./-])data/([A-Za-z0-9_-]+)/")
BACKTICKED = re.compile(r"`([^`]+)`")


def step2(text):
    """Graduation's Step 2, up to the next `## ` heading."""
    start = text.index(STEP2)
    end = text.find("\n## ", start + len(STEP2))
    return text[start:] if end == -1 else text[start:end]


def copied_dirs(text):
    """The `data/<dir>/` of each Source cell in Step 2's copy table."""
    dirs = set()
    for line in step2(text).splitlines():
        if not line.startswith("| `"):
            continue
        source = line.split("|")[1]
        for path in BACKTICKED.findall(source):
            dirs.update("data/%s/" % d for d in DATA_DIR.findall(path))
    return dirs


def excluded(text):
    """The backticked entries of Step 2's **Exclude** list, up to its closing blank line."""
    section = step2(text)
    start = section.index(EXCLUDE) + len(EXCLUDE)
    end = section.find("\n\n", start)
    return set(BACKTICKED.findall(section[start:end]))


def module6_dirs():
    """Each `data/<dir>/` any Module 6 skill file names, with the files naming it."""
    found = {}
    for path in sorted(MODULE6.glob("*.md")):
        for d in DATA_DIR.findall(path.read_text(encoding="utf-8")):
            found.setdefault("data/%s/" % d, set()).add(path.name)
    return found


def unaccounted(named, text):
    """The named `data/<dir>/` paths graduation neither copies nor excludes."""
    accounted = copied_dirs(text) | excluded(text)
    return sorted(d for d in named if d not in accounted)


class Module6DataDirsAreCopiedOrExcluded(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graduation = GRADUATION.read_text(encoding="utf-8")
        cls.named = module6_dirs()

    def test_the_scans_are_not_vacuous(self):
        """Each parser finds what it must, or every other assertion here checks nothing."""
        self.assertIn("data/subsets/", self.named, "Module 6 no longer names data/subsets/")
        self.assertIn("data/senzing-ready/", self.named)
        self.assertIn("data/senzing-ready/", copied_dirs(self.graduation),
                      "the copy table's Source column no longer parses")
        self.assertIn("data/raw/", excluded(self.graduation),
                      "graduation's Exclude list no longer parses")
        self.assertIn("docs/feedback/", excluded(self.graduation),
                      "the Exclude list was cut short: its last entry is missing")

    def test_every_module6_data_dir_is_copied_or_excluded(self):
        missing = unaccounted(self.named, self.graduation)
        self.assertEqual(
            [], missing,
            "Module 6 names data director(ies) that graduation's Step 2 neither copies nor "
            "excludes:\n  "
            + "\n  ".join("%s (named in %s)" % (d, ", ".join(sorted(self.named[d])))
                          for d in missing)
            + "\nAdd each to the copy table or to the **Exclude** list, with its reason, so "
            "leaving it out of production/ is a decision rather than an omission.")

    def test_data_subsets_is_excluded_with_its_reason(self):
        self.assertIn("data/subsets/", excluded(self.graduation))
        flat = " ".join(step2(self.graduation).split())
        self.assertIn(
            "`data/subsets/` is excluded because a subset is the evaluation's license-capped "
            "or volume-capped slice (Module 6), not the data production loads.", flat)

    def test_the_negative_control(self):
        """Taking `data/subsets/` off the Exclude list turns the check red."""
        entry = "`data/subsets/`, "
        self.assertIn(entry, self.graduation, "the control's Exclude entry moved")
        without = self.graduation.replace(entry, "", 1)
        self.assertEqual(["data/subsets/"], unaccounted(self.named, without))

    def test_a_production_path_is_not_a_project_data_dir(self):
        """The lookbehind: `production/data/…` names production's tree, not the project's."""
        self.assertEqual([], DATA_DIR.findall("copied to `production/data/senzing-ready/`"))
        self.assertEqual(["raw"], DATA_DIR.findall("from `data/raw/` as received"))


if __name__ == "__main__":
    unittest.main()
