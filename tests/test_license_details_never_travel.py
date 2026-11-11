"""No package carries a `license.json`, at any depth, in either profile (#895).

A bootcamper built the `transfer` package after graduation and found `config/license.json`
excluded, as `packaging.md` promises, and its copy at `backups/revisit/state/license.json`
packaged. Graduation Step 6b had snapshotted the file under the same basename, and the rule
`config/license.json` matches only a path with a `config` segment before it (INV-410). The
content scan could not catch the copy either: the file is the SDK's `get_license` response,
which names the license's customer, contract and billing terms and carries no license payload.

Graduation's half enforces INV-094's 2026-11-10 note (#895, registered by the maintainer
2026-11-10): Step 6b's `RESUME_STATE` snapshot leaves `config/license.json` out. These tests read
the text and run the packager; they cannot establish that a live guide skips the copy, which only
`dry-run` phase 3 observes.

The fix is two halves, and each is pinned here:

- the packager's single-segment rule `license.json`, which drops the file at any depth in both
  profiles and names each copy in the manifest under that rule;
- graduation Step 6b no longer snapshots the file, and `RESUME_STATE.json` records it as
  regenerated on restore by Module 4 Step 8a sub-step 7, which Step 6c's "License" bullet names
  for re-measuring.

⛔ **Every fixture `license.json` here holds placeholder fields only, never a real license.**

⚠️ The anti-vacuity control removes the new rule from the module and collects again: the copy
is then packaged, which proves the fixture reproduces the leak and that the content scan does
not catch it on its own. Without that control a fixture the scan happened to flag would pass
every assertion below with the rule deleted.

These read the members of archives built from fixtures and the shipped prose; they do not
establish that a live graduation stops writing the copy, which only `dry-run` observes.

Offline; stdlib only (INV-108).

Source issue: #895.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import unittest
import zipfile
from pathlib import Path

from test_package_bootcamp import PKG, Project, manifest_of, members

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
GRADUATION = SKILLS / "graduation" / "SKILL.md"
PACKAGING = SKILLS / "bootcamp-onboarding" / "packaging.md"

RULE = "license.json"

#: Placeholder fields shaped like the `get_license` response. Not a license.
PLACEHOLDER = json.dumps({
    "customer": "PLACEHOLDER CUSTOMER",
    "contract": "PLACEHOLDER CONTRACT",
    "billing": "PLACEHOLDER BILLING",
    "licenseType": "PLACEHOLDER",
    "recordLimit": 0,
})

#: The graduation copy that leaked, and copies at other depths under roots both profiles reach.
GRADUATION_COPY = "backups/revisit/state/license.json"
DEEP_COPIES = ("docs/keepsakes/license.json", "production/license.json",
               "production/archive/old/license.json")

#: What `ALWAYS_EXCLUDE` and `SHARE_EXCLUDE` held before #895. `share` must still drop all of it.
ALWAYS_BEFORE = (".env", ".env.production", "licenses", "config/license.json", "data/raw",
                 "data/temp", "logs", ".git", "__pycache__", ".venv", "venv", "node_modules",
                 "target", "backups/packages")
SHARE_BEFORE = ("backups", "docs/mapping", "data/senzing-ready")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


def with_copies(project):
    for rel in (GRADUATION_COPY,) + DEEP_COPIES:
        path = project.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(PLACEHOLDER, encoding="utf-8")
    return project


def open_me_first(path):
    with zipfile.ZipFile(path) as archive:
        root = archive.namelist()[0].split("/")[0]
        return archive.read("%s/OPEN_ME_FIRST.md" % root).decode("utf-8")


class TheFixtureReproducesTheLeak(unittest.TestCase):
    """Anti-vacuity: without the new rule, the copy travels and the content scan passes it."""

    def test_without_the_rule_the_graduation_copy_is_packaged(self):
        with Project() as p:
            with_copies(p)
            saved = PKG.ALWAYS_EXCLUDE
            PKG.ALWAYS_EXCLUDE = tuple(r for r in saved if r != RULE)
            try:
                included, _ = PKG.collect(p.root, "transfer")
            finally:
                PKG.ALWAYS_EXCLUDE = saved
            rels = [rel for _, rel in included]
            self.assertIn(GRADUATION_COPY, rels,
                          "the fixture copy is caught without the `license.json` rule, so the "
                          "tests below would pass with the rule deleted")

    def test_the_placeholder_holds_no_secret_pattern(self):
        self.assertIsNone(PKG.find_secret(PLACEHOLDER))


class TheTransferPackageCarriesNoLicenseDetails(unittest.TestCase):
    def setUp(self):
        self.project = with_copies(Project().__enter__())
        _, self.path = self.project.write_archive("transfer")
        self.names = members(self.path)
        self.manifest = manifest_of(self.path)

    def tearDown(self):
        self.project.__exit__()

    def test_no_member_is_named_license_json(self):
        self.assertEqual([], [n for n in self.names if n.split("/")[-1] == RULE])

    def test_the_rest_of_the_revisit_bundle_still_travels(self):
        joined = "\n".join(self.names)
        for expected in ("backups/revisit/RESUME_STATE.json", "backups/revisit/state/prefs.yaml",
                         "production/README.md", "config/bootcamp_progress.json"):
            with self.subTest(expected=expected):
                self.assertIn(expected, joined)

    def test_the_manifest_names_each_copy_under_the_new_rule(self):
        reasons = {e["path"]: e["reason"] for e in self.manifest["excluded"]}
        for rel in (GRADUATION_COPY,) + DEEP_COPIES:
            with self.subTest(path=rel):
                self.assertEqual("excluded by rule: %s" % RULE, reasons.get(rel))

    def test_the_home_path_keeps_its_own_rule(self):
        reasons = {e["path"]: e["reason"] for e in self.manifest["excluded"]}
        self.assertEqual("excluded by rule: config/license.json",
                         reasons.get("config/license.json"))

    def test_the_rule_is_declared_among_the_always_rules(self):
        self.assertIn(RULE, self.manifest["exclusion_rules_applied"]["always"])

    def test_open_me_first_names_any_copy(self):
        text = flat(open_me_first(self.path))
        self.assertIn("`config/license.json` and any `license.json` copy wherever it sits", text)


class TheSharePackageDropsEverythingItDidAndTheCopies(unittest.TestCase):
    def setUp(self):
        self.project = with_copies(Project().__enter__())
        _, self.path = self.project.write_archive("share")
        self.names = members(self.path)
        self.manifest = manifest_of(self.path)

    def tearDown(self):
        self.project.__exit__()

    def test_no_member_is_named_license_json(self):
        self.assertEqual([], [n for n in self.names if n.split("/")[-1] == RULE])

    def test_the_copies_under_its_own_roots_are_named_under_the_new_rule(self):
        reasons = {e["path"]: e["reason"] for e in self.manifest["excluded"]}
        for rel in DEEP_COPIES:
            with self.subTest(path=rel):
                self.assertEqual("excluded by rule: %s" % RULE, reasons.get(rel))

    def test_every_earlier_rule_still_applies(self):
        rules = self.manifest["exclusion_rules_applied"]
        for rule in ALWAYS_BEFORE + (RULE,):
            with self.subTest(rule=rule):
                self.assertIn(rule, rules["always"])
        for rule in SHARE_BEFORE:
            with self.subTest(rule=rule):
                self.assertIn(rule, rules["share_only"])

    def test_every_earlier_exclusion_still_holds(self):
        for name in self.names:
            for bad in ("data/raw", "data/temp", "data/senzing-ready", ".env", "licenses/",
                        "config/license.json", "logs/", ".git/", "__pycache__", ".venv",
                        "backups/", "docs/mapping"):
                with self.subTest(name=name, forbidden=bad):
                    self.assertNotIn(bad, name)
            with self.subTest(name=name, forbidden="database file"):
                self.assertFalse(name.endswith((".db", ".sqlite", ".sqlite3")))

    def test_the_results_still_travel(self):
        joined = "\n".join(self.names)
        for expected in ("docs/bootcamp_recap.pdf", "docs/visualizations/graph.png",
                         "production/README.md"):
            with self.subTest(expected=expected):
                self.assertIn(expected, joined)


class TheRuleMatchesTheExactNameOnly(unittest.TestCase):
    """Whole segments, case-sensitive, like every other rule."""

    def test_the_name_is_matched_at_any_depth_in_both_profiles(self):
        for profile in ("share", "transfer"):
            for rel in (GRADUATION_COPY,) + DEEP_COPIES:
                with self.subTest(profile=profile, path=rel):
                    self.assertIsNotNone(PKG.is_excluded(rel, profile))

    def test_the_transfer_copy_is_excluded_by_the_new_rule(self):
        self.assertEqual(RULE, PKG.is_excluded(GRADUATION_COPY, "transfer"))

    def test_other_names_are_not_matched(self):
        for rel in ("docs/License.json", "docs/LICENSE.json", "docs/licensed.json",
                    "docs/license.json.bak", "src/my_license.json"):
            with self.subTest(path=rel):
                self.assertIsNone(PKG.is_excluded(rel, "transfer"))


class GraduationStopsMakingTheCopy(unittest.TestCase):
    def setUp(self):
        text = GRADUATION.read_text(encoding="utf-8")
        self.step_6b = flat(between(text, "### 6b. RESUME_STATE manifest", "### 6c. Return guide"))
        self.license_bullet = flat(between(text, "- **License** — where the license lives",
                                           "- **Where things are**"))

    def test_the_snapshot_list_no_longer_names_the_license_file(self):
        snapshot = between(self.step_6b, "Snapshot the resume-critical state", "Then write")
        self.assertNotIn("config/license.json", snapshot)
        self.assertIn("`config/engine_config.json`, and `docs/mapping/`", snapshot)

    def test_resume_state_records_it_as_regenerated_on_restore(self):
        self.assertIn("Do not snapshot `config/license.json`.", self.step_6b)
        match = re.search(r'`("regenerated_on_restore": \[.*?\])`', self.step_6b)
        self.assertIsNotNone(match, "Step 6b names no `regenerated_on_restore` entry")
        entry = json.loads("{%s}" % match.group(1))
        self.assertEqual(
            {"regenerated_on_restore": [{"path": "config/license.json",
                                         "by": "Module 4 Step 8a sub-step 7"}]},
            entry)

    def test_the_license_bullet_points_at_the_measuring_step(self):
        self.assertIn("re-measure the license by Module 4 Step 8a sub-step 7",
                      self.license_bullet)


class ThePackagingProseAgreesWithTheScript(unittest.TestCase):
    def test_the_never_packaged_bullet_names_any_copy(self):
        text = flat(PACKAGING.read_text(encoding="utf-8"))
        bullet = between(text, "- **Never packaged, either profile:**",
                         "- **Never packaged on `share`")
        self.assertIn("`config/license.json` and any `license.json` copy wherever it sits",
                      bullet)
        for rule in ("config/license.json", RULE):
            with self.subTest(rule=rule):
                self.assertIn(rule, PKG.ALWAYS_EXCLUDE)


if __name__ == "__main__":
    unittest.main()
