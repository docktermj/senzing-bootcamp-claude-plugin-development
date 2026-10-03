"""`OPEN_ME_FIRST.md` says only what `PACKAGE_MANIFEST.json`'s `included` list carries.

`package_bootcamp.py --profile transfer`, run on a project with no `backups/revisit/` and no
`docs/REVISIT_BOOTCAMP.md`, wrote an archive whose `OPEN_ME_FIRST.md` said it carried "the
revisit bundle (state snapshot and database backup)" and told the recipient to open
`docs/REVISIT_BOOTCAMP.md`. Neither was in the archive; only the manifest said so. The text was
static, and every part it named is a graduation output or a packaging Step 3 output, so the
common pre-graduation package contradicted its own manifest on the machine-switch path
`transfer` exists for.

Each case below builds a fixture project, collects and manifests it the way `run()` does, and
checks the generated text. ⛔ **"Included" means listed in the manifest's `included`, never
"exists on disk"**, so one case puts every part on disk and gets each one excluded.

Every case is negative-controlled: its predicate is also run against a STATIC stand-in -- the
real function fed a complete package's `included` list, which is exactly what the text said
before #321 -- and must report a problem there.

Source issue: #321. Stdlib only (INV-108); the script is loaded the way
`tests/test_package_bootcamp.py` loads it.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGER = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "package_bootcamp.py"
DATE = "20261001"


def load():
    spec = importlib.util.spec_from_file_location("packager_open_me_first", PACKAGER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PKG = load()

#: The wording a complete package has always carried. Kept byte for byte when every part is in.
FULL_START = (
    "Open **`docs/bootcamp_recap.pdf`** first — it is the guided tour of what was built,\n"
    "in order, with the visualizations embedded.")
FULL_SHARE = (
    "Profile **`share`** — the results, for reading. It carries the keepsake documents,\n"
    "the visualizations and the generated `production/` project.")
FULL_TRANSFER = (
    "Profile **`transfer`** — everything needed to continue the bootcamp on another\n"
    "machine: the results, plus the revisit bundle (state snapshot and database backup),\n"
    "`config/`, the mappings and `src/`.\n"
    "\n"
    "**To resume:** open **`docs/REVISIT_BOOTCAMP.md`** — it carries the restore and\n"
    "re-initialization commands for this project's database and state.")

#: Every part the text can name, with a file that makes it count as included.
PARTS = {
    "recap": "docs/bootcamp_recap.pdf",
    "keepsake": "docs/business_problem.pdf",
    "visualizations": "docs/visualizations/graph.html",
    "production": "production/README.md",
    "guide": "docs/REVISIT_BOOTCAMP.md",
    "database": "backups/revisit/database/G2C.db",
    "resume_state": "backups/revisit/RESUME_STATE.json",
    "state": "backups/revisit/state/prefs.yaml",
    "config": "config/bootcamp_progress.json",
    "mappings": "docs/mapping/customers.json",
    "src": "src/loader.py",
}
FULL = tuple(PARTS)
PEM = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----\n"

#: Backticked tokens that are not archive contents: the archive's own manifest (written beside
#: OPEN_ME_FIRST.md, not listed in `included`) and the restore step's target directory.
NOT_CONTENTS = {"PACKAGE_MANIFEST.json", "database/"}


def build(root, parts, extra=()):
    """A project tree carrying exactly ``parts`` (keys of PARTS) plus ``extra`` (rel, text)."""
    files = [(PARTS[key], "x") for key in parts] + list(extra)
    files.append(("docs/notes.md", "notes"))  # so even an all-absent case packages something
    for rel, text in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def manifest_for(root, profile):
    members, skipped = PKG.collect(root, profile)
    return PKG.build_manifest(profile, members, skipped, root, DATE)


def real(manifest, root):
    return PKG.open_me_first(manifest, root)


def static(manifest, root):
    """The pre-#321 behavior: the complete package's text, whatever was included."""
    complete = dict(manifest, included=[{"path": PARTS[k]} for k in FULL])
    return PKG.open_me_first(complete, root)


def contents_sections(text):
    """Everything before the rules sections, which describe rules rather than contents."""
    return text.split("## What is NOT here")[0]


def flat(text):
    return re.sub(r"\s+", " ", text)


def carries_sentence(text):
    """What the "What this package is" block says the archive carries ("" for "none of")."""
    block = flat(contents_sections(text).split("## What this package is")[1])
    match = re.search(r"(?i)\bit carries ([^.]*)\.", block)
    if not match or match.group(1).startswith("none of"):
        return ""
    return match.group(1)


def named_but_not_included(text, manifest):
    """⛔ The issue's rule: every path the text names as content is in `included`."""
    paths = [entry["path"] for entry in manifest["included"]]
    bad = []
    for token in re.findall(r"`([^`\n]+)`", contents_sections(text)):
        if token in NOT_CONTENTS or not ("/" in token or re.search(r"\.\w+$", token)):
            continue
        hit = (any(p.startswith(token) for p in paths) if token.endswith("/")
               else token in paths)
        if not hit:
            bad.append(token)
    return bad


class Case:
    """One fixture: build it, manifest it, and render both the real and the static text."""

    def __init__(self, profile, parts, extra=(), prepare=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        build(self.root, parts, extra)
        if prepare:
            prepare(self.root)
        self.manifest = manifest_for(self.root, profile)
        self.included = {entry["path"] for entry in self.manifest["included"]}
        self.text = real(self.manifest, self.root)
        self.static_text = static(self.manifest, self.root)

    def close(self):
        self.tmp.cleanup()


class CaseTest(unittest.TestCase):
    """Each subclass names a fixture and a predicate; both halves run against it."""

    profile = "transfer"
    parts = FULL
    extra = ()

    def setUp(self):
        self.case = Case(self.profile, self.parts, self.extra)
        self.addCleanup(self.case.close)

    def problems(self, text):  # pragma: no cover - overridden
        raise NotImplementedError

    def check(self):
        self.assertEqual([], self.problems(self.case.text), self.case.text)
        self.assertEqual([], named_but_not_included(self.case.text, self.case.manifest),
                         "OPEN_ME_FIRST.md names a path that is not in `included`")

    def check_static_fails(self):
        self.assertTrue(
            self.problems(self.case.static_text)
            or named_but_not_included(self.case.static_text, self.case.manifest),
            "negative control escaped: the static pre-#321 text passes this case's predicate, "
            "so the predicate does not test the change")


class TransferWithNoBundleAndNoGuide(CaseTest):
    parts = ("recap", "keepsake", "visualizations", "production", "config", "mappings", "src")

    def problems(self, text):
        out, f = [], flat(text)
        if "revisit bundle" in f:
            out.append("names the revisit bundle")
        if "REVISIT_BOOTCAMP.md" in f:
            out.append("names docs/REVISIT_BOOTCAMP.md")
        if "no database backup and no restore guide" not in f:
            out.append("does not say there is no database backup or restore guide")
        if "redo SDK setup, the database and the load" not in f:
            out.append("does not say what to redo")
        return out

    def test_it_promises_neither_and_says_what_to_redo(self):
        self.check()

    def test_negative_control(self):
        self.check_static_fails()


class TransferWithEverything(CaseTest):
    def problems(self, text):
        return [w for w in (FULL_START, FULL_TRANSFER) if w not in text]

    def test_the_current_wording_is_kept(self):
        self.check()

    def test_the_fixture_really_carries_every_part(self):
        """Anti-vacuity: the kept wording is only right if every part is included."""
        self.assertTrue({PARTS[k] for k in FULL} <= self.case.included)


class TransferWithADatabaseBackupOnly(CaseTest):
    """The packaging Step 3 shape: `backups/revisit/database/` and nothing else of the bundle."""

    parts = ("recap", "keepsake", "visualizations", "production", "database", "config",
             "mappings", "src")

    def problems(self, text):
        out, f = [], flat(text)
        if "`backups/revisit/database/G2C.db` is a SQLite file; copy it back to `database/`" \
                not in f:
            out.append("does not name the backup's path and its restore step")
        if "state snapshot" in carries_sentence(text) or "revisit bundle" in f:
            out.append("claims a state snapshot")
        if "REVISIT_BOOTCAMP.md" in f:
            out.append("instructs opening the restore guide")
        if "No full restore guide is included" not in f:
            out.append("does not say no full restore guide is included")
        return out

    def test_it_names_the_backup_and_its_restore_step(self):
        self.check()

    def test_negative_control(self):
        self.check_static_fails()


class TheRestoreStepFollowsTheBackupsFileType(CaseTest):
    parts = ("config",)
    extra = (("backups/revisit/database/senzing.dump", "pg"),
             ("backups/revisit/database/snapshot.bak", "other"))

    def problems(self, text):
        out, f = [], flat(text)
        if ("`backups/revisit/database/senzing.dump` is a `pg_dump` file; restore it into a "
                "fresh database with `pg_restore -U <user> -d <db> <file>` (or "
                "`psql -U <user> -d <db> -f <file>` for a plain dump), never with a `<` "
                "redirection") not in f:
            out.append("the pg_dump file has no pg_restore step")
        if "**Database backup:** `backups/revisit/database/snapshot.bak`." not in f:
            out.append("a backup of another type is not named by path alone")
        return out

    def test_each_backup_gets_the_step_for_its_type(self):
        self.check()

    def test_negative_control(self):
        self.check_static_fails()


class TransferWithTheGuideButNoDatabaseBackup(CaseTest):
    parts = ("recap", "keepsake", "guide", "resume_state", "state", "config", "mappings", "src")

    def problems(self, text):
        out, f = [], flat(text)
        if "open **`docs/REVISIT_BOOTCAMP.md`**" not in f:
            out.append("does not point at the guide")
        if "carries **no database backup**" not in f:
            out.append("does not say there is no database backup")
        if "revisit bundle" in f or "database backup" in carries_sentence(text):
            out.append("claims a database backup")
        return out

    def test_it_points_at_the_guide_and_says_there_is_no_backup(self):
        self.check()

    def test_negative_control(self):
        self.check_static_fails()


def _poison(root):
    """Every part stays ON DISK; each of these gets excluded by the secret scan."""
    for key in ("recap", "guide", "database"):
        (root / PARTS[key]).write_text(PEM, encoding="utf-8")


class APartPresentButExcludedIsNotNamed(CaseTest):
    def setUp(self):
        self.case = Case(self.profile, FULL, prepare=_poison)
        self.addCleanup(self.case.close)

    def problems(self, text):
        f = flat(contents_sections(text))
        return [PARTS[k] for k in ("recap", "guide", "database") if PARTS[k] in f]

    def test_the_fixture_has_them_on_disk_and_excluded(self):
        excluded = {entry["path"] for entry in self.case.manifest["excluded"]}
        for key in ("recap", "guide", "database"):
            with self.subTest(part=key):
                self.assertTrue((self.case.root / PARTS[key]).exists())
                self.assertIn(PARTS[key], excluded)
                self.assertNotIn(PARTS[key], self.case.included)

    def test_an_excluded_part_is_not_named_as_included(self):
        self.check()
        self.assertNotIn("revisit bundle", self.case.text)

    def test_negative_control(self):
        self.check_static_fails()

    def test_an_unreadable_part_is_not_named_either(self):
        """The other exclusion route: a member that cannot be read is not packaged."""
        if os.name == "nt":
            self.skipTest("chmod cannot make a file unreadable on Windows")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            build(root, FULL)
            guide = root / PARTS["guide"]
            guide.chmod(0o000)
            try:
                try:
                    guide.read_bytes()
                    self.skipTest("cannot make a file unreadable here (running as root?)")
                except OSError:
                    pass
                manifest = manifest_for(root, "transfer")
                text = real(manifest, root)
            finally:
                guide.chmod(0o644)
        self.assertNotIn(PARTS["guide"], {e["path"] for e in manifest["included"]})
        self.assertNotIn("REVISIT_BOOTCAMP.md", text)
        self.assertEqual([], named_but_not_included(text, manifest))


class TheRecapPdfIsNamedOnlyWhenIncluded(unittest.TestCase):
    def problems(self, text):
        start = flat(text.split("## Start here")[1].split("## What this package is")[0])
        out = []
        if "docs/bootcamp_recap.pdf" in start:
            out.append("Start here names the recap PDF")
        if "written at graduation and is not in this package" not in start:
            out.append("does not say the recap PDF is a graduation output")
        if "`PACKAGE_MANIFEST.json`" not in start or "`included`" not in start:
            out.append("does not point at the manifest's included list")
        return out

    def test_both_profiles(self):
        for profile in ("share", "transfer"):
            with self.subTest(profile=profile):
                case = Case(profile, tuple(k for k in FULL if k != "recap"))
                try:
                    self.assertEqual([], self.problems(case.text), case.text)
                    self.assertTrue(self.problems(case.static_text), "negative control escaped")
                finally:
                    case.close()

    def test_when_included_the_current_wording_is_kept(self):
        for profile in ("share", "transfer"):
            with self.subTest(profile=profile):
                case = Case(profile, FULL)
                try:
                    self.assertIn(FULL_START, case.text)
                finally:
                    case.close()


class TheShareProfileNamesOnlyWhatItCarries(unittest.TestCase):
    LABELS = {
        "keepsake": "the keepsake documents",
        "visualizations": "the visualizations",
        "production": "`production/`",
    }

    def problems(self, text, present):
        carried = carries_sentence(text)
        out = []
        for key, label in self.LABELS.items():
            if (key in present) != (label in carried):
                out.append("%s: included=%s, named=%s" % (key, key in present, label in carried))
        return out

    def test_each_part_is_named_only_when_included(self):
        share_parts = ("keepsake", "visualizations", "production")
        for missing in [(k,) for k in share_parts] + [share_parts]:
            # The recap PDF is itself a keepsake, so it goes with the keepsakes.
            drop = set(missing) | ({"recap"} if "keepsake" in missing else set())
            present = [k for k in FULL if k not in drop]
            with self.subTest(missing=missing):
                case = Case("share", present)
                try:
                    self.assertEqual([], self.problems(case.text, present), case.text)
                    self.assertEqual([], named_but_not_included(case.text, case.manifest))
                    self.assertTrue(self.problems(case.static_text, present),
                                    "negative control escaped")
                finally:
                    case.close()

    def test_with_all_present_the_current_wording_is_kept(self):
        case = Case("share", FULL)
        try:
            self.assertIn(FULL_SHARE, case.text)
            self.assertIn(FULL_START, case.text)
        finally:
            case.close()


class TheWrittenArchiveCarriesTheGeneratedText(unittest.TestCase):
    """End to end: the zip `run()` writes holds the same honest text, not a stale copy."""

    def test_a_pre_graduation_transfer_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build(root, ("config", "mappings", "src"))
            result = subprocess.run(
                [sys.executable, str(PACKAGER), "--profile", "transfer",
                 "--project-root", str(root), "--date", DATE],
                capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            archive = root / "backups" / "packages" / ("senzing-bootcamp-transfer-%s.zip" % DATE)
            with zipfile.ZipFile(archive) as zf:
                prefix = "senzing-bootcamp-transfer-%s" % DATE
                text = zf.read("%s/OPEN_ME_FIRST.md" % prefix).decode("utf-8")
                manifest = json.loads(zf.read("%s/PACKAGE_MANIFEST.json" % prefix))
        self.assertNotIn("revisit bundle", text)
        self.assertNotIn("REVISIT_BOOTCAMP.md", text)
        self.assertNotIn("Open **`docs/bootcamp_recap.pdf`**", text)
        self.assertIn("no database backup and no restore guide", flat(text))
        self.assertEqual([], named_but_not_included(text, manifest))


class PartsAreMatchedOnManifestPathsOnly(unittest.TestCase):
    """`included_parts` reads posix manifest paths; nothing on disk is consulted."""

    def test_matching(self):
        parts = PKG.included_parts({"included": [
            {"path": "docs/business_problem.pdf"},
            {"path": "docs/visualizations/x/graph.png"},
            {"path": "backups/revisit/RESUME_STATE.json"},
            {"path": "backups/revisit/databaseX/G2C.db"},   # not under database/
            {"path": "docs/sub/other.pdf"},                 # not directly under docs/
        ]})
        self.assertTrue(parts["keepsakes"])
        self.assertTrue(parts["visualizations"])
        self.assertTrue(parts["state"])
        self.assertEqual([], parts["database"])
        self.assertFalse(parts["recap"])
        self.assertFalse(parts["production"])
        only_nested = PKG.included_parts({"included": [{"path": "docs/sub/other.pdf"}]})
        self.assertFalse(only_nested["keepsakes"])


if __name__ == "__main__":
    unittest.main()
