"""`/package-bootcamp` produces an archive that is safe to hand to someone else.

Also enforces **INV-388**, registered by the maintainer 2026-10-20, in its scripted half:
`--dry-run` names every candidate root absent from the project, so the conversation layer can
say what the quoted size did not measure. ⚠️ It drives the packager over fixtures; it
**cannot** establish that a live flow substitutes the disclosure clause.

A bootcamper who finished the bootcamp had no way to archive the work or hand it on. Graduation
frames the recap PDF as "a keepsake to revisit and share with their team", and INV-094's revisit
bundle was built for the resume story -- but written **in place**, so it only helped on the machine
that produced it. Nothing gathered the artifacts, nothing said what to open first, and nothing
decided what must **not** travel.

That last one is what these tests are mostly about. An archive is a distribution channel: the
things it must never carry are the point, and every one of them is asserted over a fixture project
tree rather than reasoned about.

⛔ **`.git/` is excluded on purpose** -- the archive is a snapshot, not a clone, and git history can
carry secrets that no longer exist in the tree. `OPEN_ME_FIRST.md` has to say so, or a bootcamper
who wants history silently gets a package that cannot give it.

⚠️ **The `share` profile is the one handed to people who should NOT see the inputs**, so it carries
no database, no `data/raw/`, no credentials, and no `docs/mapping/` (which describes the
bootcamper's own source schema).

⛔ **The fixture puts the bootcamper's rows UNDER `production/`, and that is the point.** Until
#672 every exclusion rule naming a directory under `data/` was anchored at the project root, while
`production/` is packaged **recursively** and graduation copies `data/senzing-ready/**` into
`production/data/senzing-ready/` (INV-186). So `share` excluded the mapped rows at
`data/senzing-ready/` and packaged the identical rows one directory deeper, inside the generated
tree it exists to carry -- with `OPEN_ME_FIRST.md` telling the recipient that no source data had
traveled. A fixture whose only inputs sit at the root cannot see that: it is satisfied by the rule
that was already there. The fast-path variant is here too (`production/data/raw/`), because a CORD
fast-pathed source's loader reads straight from `data/raw/` with no mapping, so "the inputs" is not
one directory.

⛔ **The secret-scan fixtures below include a `.pem` and an extensionless key file, and that is
the point.** Until 2026-08-26 the scan was gated on an extension allowlist and this suite's only
secret fixture was a `.py`, so it passed while `server.pem` and `id_rsa` were packaged. A guard
whose fixture shares the defect's blind spot certifies nothing. A genuine PNG is asserted to still
travel, because the fix must not exclude the visualizations `share` exists to carry.

Offline; stdlib only; no network and no Senzing engine.

No phrase-level pattern (#692): the line-at-a-time reads here are of the packager's own
stderr report and of archive member names, never of shipped prose. A line IS the unit
there -- `size:`, `excluded:` and `absent:` are lines the conversation layer reads back
one at a time -- so there is no phrase for a wrap-aware read to find (INV-346).

Source spec: `specs/the-bootcamp-cannot-leave-the-machine-it-was-built-on.md`.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts"
PACKAGER = SCRIPTS / "package_bootcamp.py"
DATE = "20260826"


def load():
    spec = importlib.util.spec_from_file_location("packager_under_test", PACKAGER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PKG = load()


class Project:
    """A fixture project carrying one of everything, including what must not travel."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        for d in ("docs/visualizations", "docs/mapping", "production",
                  "production/data/senzing-ready", "production/data/raw", "production/src/load",
                  "data/exports/neo4j", "production/data/exports/neo4j",
                  "config", "data/raw",
                  "data/temp", "logs", "licenses", "src", "backups/revisit/database",
                  "backups/revisit/state", ".git", "__pycache__", "database", ".venv"):
            (root / d).mkdir(parents=True, exist_ok=True)
        write = lambda rel, text: (root / rel).write_text(text, encoding="utf-8")
        write("docs/bootcamp_recap.pdf", "recap")
        write("docs/business_problem.md",
              "# Business Problem Statement\n\n## Problem Description\nDedupe vendors.\n")
        write("docs/bootcamp_notes.md", "notes")
        write("docs/REVISIT_BOOTCAMP.md", "restore steps")
        write("docs/visualizations/results_visualization-entity-graph.png", "png")
        write("docs/mapping/customers.json", '{"map":1}')
        write("production/README.md", "prod")
        # ⛔ The #672 regression fixtures: the bootcamper's own rows, nested inside the
        # generated tree graduation copies them into. Synthetic -- no real personal data.
        write("production/data/senzing-ready/people.jsonl",
              '{"DATA_SOURCE":"PEOPLE","RECORD_ID":"1","NAME_FULL":"Ada Lovelace",'
              '"ADDR_FULL":"12 Mapped Row Lane"}\n')
        write("production/data/raw/customers.csv", "id,name\n1,Ada Lovelace\n")
        write("production/src/load/load_records.py", "print('load')\n")
        write("config/bootcamp_progress.json",
              '{"modules_completed":["system_verification","query_visualize_discover"]}')
        write("config/engine_config.json", '{"connection":"sqlite3://na:na@/tmp/G2C.db"}')
        write("config/license.json", '{"key":"x"}')
        write(".env", "SECRET=abc")
        write("licenses/g2.lic", "AQAAAD" + "A" * 30)
        write("data/raw/customers.csv", "raw,data")
        write("data/temp/scratch.txt", "tmp")
        # ⛔ #686: Module 7 step 4e's export, the one tree under `data/` that `share` reaches.
        # The step hands these files over as its deliverable, and graduation copies the tree to
        # `production/data/exports/` at the same project-relative path (INV-186), so BOTH copies
        # must travel. Synthetic rows -- the export is the bootcamp's own output, not source data.
        write("data/exports/neo4j/nodes.csv", "id:ID,name\n1,Entity One\n")
        write("data/exports/neo4j/edges.csv", ":START_ID,:END_ID,matchKey\n1,2,+NAME+ADDRESS\n")
        write("production/data/exports/neo4j/nodes.csv", "id:ID,name\n1,Entity One\n")
        write("logs/run.log", "log")
        write("database/G2C.db", "live-db")
        write("backups/revisit/database/G2C.db", "db-backup")
        write("backups/revisit/RESUME_STATE.json", '{"resume":true}')
        write("backups/revisit/state/prefs.yaml", "name: x")
        write(".git/config", "gitobj")
        write("__pycache__/x.pyc", "cache")
        write(".venv/pyvenv.cfg", "venv")
        # A source file that legitimately contains a private key -> excluded and named.
        write("src/loader.py", 'KEY = """-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n"""\n')
        write("src/clean.py", "print('ok')\n")
        # ⛔ The file types the old extension allowlist skipped. These are the regression
        # fixtures for `the-packager-secret-scan-skips-the-files-most-likely-to-be-secrets`.
        (root / "src" / "keys").mkdir(parents=True, exist_ok=True)
        write("src/keys/server.pem",
              "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n"
              "-----END RSA PRIVATE KEY-----\n")
        write("src/keys/id_rsa",          # no extension at all
              "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg\n-----END PRIVATE KEY-----\n")
        write("src/keys/aws.crt", "AKIAIOSFODNN7EXAMPLE\n")
        # A real PNG, which must STILL travel: the fix must not exclude every binary.
        tiny_png(root / "docs" / "visualizations" / "graph.png")
        # A key pasted into a PNG -- still a key, so still excluded.
        (root / "docs" / "visualizations" / "sneaky.png").write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n")
        # A symlink escaping the project root -> skipped and named.
        try:
            (root / "docs" / "escape.md").symlink_to("/etc/hostname")
            self.symlinks = True
        except OSError:  # pragma: no cover - Windows without privilege
            self.symlinks = False
        self.root = root
        return self

    def dry_run(self, profile):
        result = subprocess.run(
            [sys.executable, str(PACKAGER), "--profile", profile,
             "--project-root", str(self.root), "--date", DATE, "--dry-run"],
            capture_output=True, text=True)
        return result, json.loads(result.stdout)

    def write_archive(self, profile):
        result = subprocess.run(
            [sys.executable, str(PACKAGER), "--profile", profile,
             "--project-root", str(self.root), "--date", DATE],
            capture_output=True, text=True)
        path = (self.root / "backups" / "packages"
                / ("senzing-bootcamp-%s-%s.zip" % (profile, DATE)))
        return result, path

    def __exit__(self, *exc):
        self.tmp.cleanup()


def tiny_png(path):
    """A real 4x1 PNG. Binary, so it must survive the secret scan and still be packaged."""
    ihdr = struct.pack(">IIBBBBB", 4, 1, 8, 2, 0, 0, 0)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data)))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                     + chunk(b"IDAT", zlib.compress(b"\x00" + b"\xff\x00\x00" * 4))
                     + chunk(b"IEND", b""))


def members(path):
    with zipfile.ZipFile(path) as archive:
        return archive.namelist()


def manifest_of(path):
    with zipfile.ZipFile(path) as archive:
        root = archive.namelist()[0].split("/")[0]
        return json.loads(archive.read("%s/PACKAGE_MANIFEST.json" % root))


class TheDryRunWritesNothing(unittest.TestCase):
    """The consent question quotes its size, so the measurement must precede any write."""

    def test_it_reports_a_size_and_creates_no_archive(self):
        with Project() as p:
            result, manifest = p.dry_run("share")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("DRY RUN: nothing was written.", result.stderr)
            self.assertIn("size:", result.stderr)
            self.assertGreater(manifest["total_uncompressed_bytes"], 0)
            self.assertFalse((p.root / "backups" / "packages").exists(),
                             "the dry run created the output directory")

    def test_the_two_profiles_report_different_sizes(self):
        """INV-265 anti-vacuity: if they matched, the question's numbers would be meaningless."""
        with Project() as p:
            _, share = p.dry_run("share")
            _, transfer = p.dry_run("transfer")
            self.assertLess(share["total_uncompressed_bytes"],
                            transfer["total_uncompressed_bytes"])


class TheShareProfileCarriesNoInputs(unittest.TestCase):
    """The profile handed to someone who should see results but not the data."""

    def setUp(self):
        self.project = Project().__enter__()
        _, self.path = self.project.write_archive("share")
        self.names = members(self.path)

    def tearDown(self):
        self.project.__exit__()

    def test_the_archive_was_written(self):
        self.assertTrue(self.path.exists())
        self.assertGreater(len(self.names), 3)

    def test_it_carries_no_database_file(self):
        for name in self.names:
            with self.subTest(name=name):
                self.assertFalse(name.endswith((".db", ".sqlite", ".sqlite3")))

    def test_it_carries_none_of_the_forbidden_paths(self):
        forbidden = ("data/raw", "data/temp", "data/senzing-ready", ".env", "licenses/",
                     "config/license.json", "logs/", ".git/", "__pycache__", ".venv", "backups/")
        for name in self.names:
            for bad in forbidden:
                with self.subTest(name=name, forbidden=bad):
                    self.assertNotIn(bad, name)

    def test_it_carries_no_mapping_layer(self):
        """Transfer-only: it describes the bootcamper's own source schema."""
        self.assertFalse([n for n in self.names if "docs/mapping" in n])

    def test_it_does_carry_the_results(self):
        """Anti-vacuity: the exclusions above are worthless if nothing is included."""
        joined = "\n".join(self.names)
        for expected in ("docs/bootcamp_recap.pdf", "docs/visualizations/", "production/"):
            with self.subTest(expected=expected):
                self.assertIn(expected, joined)

    def test_it_carries_the_module_7_exports(self):
        """⛔ #686: step 4e hands these over as its deliverable, so `share` must reach them.

        Both copies: the one the export program writes under `data/exports/`, and the one
        graduation copies to `production/data/exports/` at the same project-relative path, which
        is what keeps the verbatim-copied program's own output path true (INV-186). Before #686
        the step wrote into `data/temp/`, so the archive carried neither.
        """
        joined = "\n".join(self.names)
        for expected in ("data/exports/neo4j/nodes.csv", "data/exports/neo4j/edges.csv",
                         "production/data/exports/neo4j/nodes.csv"):
            with self.subTest(expected=expected):
                self.assertIn(expected, joined)


def root_anchored(relpath, rule):
    """The pre-#672 matcher, kept as the control: a rule anchored at the project root.

    ⛔ **It is here so the fixture cannot drift back into testing the rule that already
    existed.** A nested-input case that this function also catches is a root case wearing a
    longer path, and the guard below would pass without the change. Expressed as code rather
    than asserted in prose, because the claim "a root-path check does not see this" is exactly
    the claim the issue says a fixture must stop taking on trust.
    """
    parts, rule_parts = relpath.split("/"), rule.split("/")
    return parts[:len(rule_parts)] == rule_parts


class TheShareProfileCarriesNoLoaderInputsAtAnyDepth(unittest.TestCase):
    """#672 — the no-source-data promise, kept rather than softened.

    The share profile promises a recipient that no source data travels. `production/` is
    packaged recursively and graduation copies the bootcamper's mapped rows into
    `production/data/senzing-ready/`, so the promise was false for every graduated project.
    These cases read the **ZIP's members**, not the collector's view and not a root-path
    check: an archive is what was handed over.
    """

    MAPPED = "production/data/senzing-ready/people.jsonl"
    RAW = "production/data/raw/customers.csv"

    def setUp(self):
        self.project = Project().__enter__()
        _, self.path = self.project.write_archive("share")
        self.names = members(self.path)
        self.manifest = manifest_of(self.path)

    def tearDown(self):
        self.project.__exit__()

    def test_the_fixture_really_holds_the_inputs_on_disk(self):
        """Anti-vacuity: absent from the archive means nothing if it was never written."""
        for rel in (self.MAPPED, self.RAW):
            with self.subTest(path=rel):
                self.assertTrue((self.project.root / rel).exists())

    def test_the_fixture_is_nested_rather_than_at_the_root(self):
        """The control: a root-anchored rule does NOT see these, so the guard has teeth."""
        for rel, rule in ((self.MAPPED, "data/senzing-ready"), (self.RAW, "data/raw")):
            with self.subTest(path=rel):
                self.assertFalse(
                    root_anchored(rel, rule),
                    "%s is caught by a root-anchored `%s`, so this fixture re-tests the rule "
                    "that was already there instead of the nested case #672 reported"
                    % (rel, rule))

    def test_the_mapped_input_is_absent_from_the_share_zip_members(self):
        """⛔ The regression. Members of the written archive, not a root-path check."""
        self.assertEqual(
            [], [n for n in self.names if "data/senzing-ready" in n],
            "the share archive carries the bootcamper's mapped loader inputs; the profile "
            "promises a recipient that no source data travels")

    def test_the_fast_pathed_raw_input_is_absent_too(self):
        """A CORD fast-pathed source loads straight from `data/raw/`, mapping nothing."""
        self.assertEqual([], [n for n in self.names if "data/raw" in n])

    def test_the_manifest_names_each_exclusion_with_its_rule(self):
        """⛔ Excluded is not enough: a recipient must be able to tell what is missing."""
        reasons = {e["path"]: e["reason"] for e in self.manifest["excluded"]}
        for prefix, rule in (("production/data/senzing-ready", "data/senzing-ready"),
                             ("production/data/raw", "data/raw")):
            with self.subTest(rule=rule):
                named = [p for p in reasons if p.startswith(prefix)]
                self.assertTrue(named, "%s is excluded but unnamed in the manifest" % prefix)
                for path in named:
                    self.assertIn(rule, reasons[path])

    def test_the_rule_is_declared_among_the_share_only_rules(self):
        self.assertIn("data/senzing-ready",
                      self.manifest["exclusion_rules_applied"]["share_only"])

    def test_the_promise_in_open_me_first_is_now_true(self):
        """The issue's narrowed criterion: agree by EXCLUDING, never by disclosing."""
        root = "senzing-bootcamp-share-%s" % DATE
        with zipfile.ZipFile(self.path) as archive:
            text = archive.read("%s/OPEN_ME_FIRST.md" % root).decode("utf-8")
        self.assertIn("no database, no source data and no credentials", text)
        self.assertIn("data/senzing-ready/", text,
                      "the share package never names the mapped inputs among what it leaves "
                      "out, so a recipient cannot tell they were withheld")
        self.assertNotIn("data/senzing-ready",
                         "\n".join(e["path"] for e in self.manifest["included"]))

    def test_the_safe_production_artifacts_still_travel(self):
        """Anti-vacuity: excluding the inputs must not empty the project it carries."""
        joined = "\n".join(self.names)
        for expected in ("production/README.md", "production/src/load/load_records.py",
                         "docs/bootcamp_recap.pdf", "docs/visualizations/graph.png"):
            with self.subTest(expected=expected):
                self.assertIn(expected, joined)

    def test_the_transfer_profile_still_carries_the_mapped_input(self):
        """Documented transfer behavior is preserved: the copied loader reads from there."""
        _, path = self.project.write_archive("transfer")
        self.assertTrue([n for n in members(path) if n.endswith(self.MAPPED)],
                        "the transfer profile dropped the loader's input, so the project it "
                        "hands to the next machine has nothing to load")


class TheTransferProfileCanResumeElsewhere(unittest.TestCase):
    def setUp(self):
        self.project = Project().__enter__()
        _, self.path = self.project.write_archive("transfer")
        self.names = members(self.path)

    def tearDown(self):
        self.project.__exit__()

    def test_it_carries_the_revisit_state_snapshot_and_database_backup(self):
        joined = "\n".join(self.names)
        self.assertIn("backups/revisit/RESUME_STATE.json", joined)
        self.assertIn("backups/revisit/state/prefs.yaml", joined)
        self.assertIn("backups/revisit/database/G2C.db", joined,
                      "the transfer profile carries no database backup, so it cannot resume")

    def test_it_carries_config_and_mappings(self):
        joined = "\n".join(self.names)
        self.assertIn("config/bootcamp_progress.json", joined)
        self.assertIn("docs/mapping/customers.json", joined)

    def test_it_carries_the_module_7_exports_too(self):
        """⛔ #686: one `SHARE_INCLUDE` entry covers both profiles, because `TRANSFER` composes
        from `SHARE_INCLUDE` plus `TRANSFER_EXTRA` -- asserted rather than reasoned about."""
        joined = "\n".join(self.names)
        self.assertIn("data/exports/neo4j/nodes.csv", joined)
        self.assertIn("production/data/exports/neo4j/nodes.csv", joined)

    def test_it_still_carries_no_credentials_or_source_data(self):
        for name in self.names:
            for bad in ("data/raw", ".env", "licenses/", "config/license.json", ".git/"):
                with self.subTest(name=name, forbidden=bad):
                    self.assertNotIn(bad, name)

    def test_its_open_me_first_keeps_the_raw_only_source_data_wording(self):
        """`transfer` carries the mapped inputs on purpose, so its bullet names `data/raw/`."""
        with zipfile.ZipFile(self.path) as archive:
            root = archive.namelist()[0].split("/")[0]
            text = archive.read("%s/OPEN_ME_FIRST.md" % root).decode("utf-8")
        self.assertIn("\n".join(PKG.TRANSFER_SOURCE_DATA_BULLET), text)
        self.assertNotIn("never packaged by this profile", text)

    def test_it_does_not_carry_the_live_database(self):
        """The backup travels; the working repository does not."""
        self.assertFalse([n for n in self.names if n.endswith("database/G2C.db")
                          and "backups" not in n])

    def test_open_me_first_points_at_the_restore_guide(self):
        with zipfile.ZipFile(self.path) as archive:
            root = archive.namelist()[0].split("/")[0]
            text = archive.read("%s/OPEN_ME_FIRST.md" % root).decode("utf-8")
        self.assertIn("docs/REVISIT_BOOTCAMP.md", text)


class SecretsAndSymlinksAreExcludedAndNamed(unittest.TestCase):
    def setUp(self):
        self.project = Project().__enter__()
        _, self.path = self.project.write_archive("transfer")
        self.names = members(self.path)
        self.manifest = manifest_of(self.path)

    def tearDown(self):
        self.project.__exit__()

    def test_a_member_matching_a_secret_pattern_is_excluded(self):
        self.assertFalse([n for n in self.names if n.endswith("src/loader.py")],
                         "a file containing a PEM private key was packaged")

    def test_the_excluded_secret_is_named_in_the_manifest(self):
        """⛔ Excluded is not enough -- a recipient must be able to tell what is missing."""
        reasons = {e["path"]: e["reason"] for e in self.manifest["excluded"]}
        self.assertIn("src/loader.py", reasons)
        self.assertIn("secret pattern", reasons["src/loader.py"])
        self.assertIn("PEM private key", reasons["src/loader.py"])

    def test_the_manifest_does_not_echo_the_secret(self):
        self.assertNotIn("MIIabc", json.dumps(self.manifest))

    def test_a_clean_sibling_is_still_packaged(self):
        """Exclusion is per-file, not per-directory: one bad file must not drop src/."""
        self.assertTrue([n for n in self.names if n.endswith("src/clean.py")])

    def test_a_secret_is_excluded_whatever_the_extension(self):
        """⛔ The regression. The old allowlist skipped exactly these three."""
        for tail in ("src/keys/server.pem", "src/keys/id_rsa", "src/keys/aws.crt"):
            with self.subTest(path=tail):
                self.assertFalse(
                    [n for n in self.names if n.endswith(tail)],
                    "%s carries a secret and was packaged; the scan is gated on an extension "
                    "allowlist again, which skips the file types whose purpose is to hold a "
                    "credential" % tail)

    def test_each_of_those_is_named_in_the_manifest(self):
        reasons = {e["path"]: e["reason"] for e in self.manifest["excluded"]}
        for rel in ("src/keys/server.pem", "src/keys/id_rsa", "src/keys/aws.crt"):
            with self.subTest(path=rel):
                self.assertIn(rel, reasons)
                self.assertIn("secret pattern", reasons[rel])

    def test_a_secret_pasted_into_a_binary_is_still_caught(self):
        """A credential does not stop being one because of the file it was pasted into."""
        self.assertFalse([n for n in self.names if n.endswith("sneaky.png")])

    def test_a_secret_straddling_a_scan_block_boundary_is_caught(self):
        """The scan reads in blocks; a pattern split across two must still be found.

        ⛔ Added because a negative control escaped: dropping the block overlap changed nothing
        any test could see, since every fixture was smaller than one block. A guard that claims
        boundary-safe scanning and exercises only sub-block files certifies nothing.
        """
        armor = "-----BEGIN RSA PRIVATE KEY-----"
        block = PKG.SCAN_BLOCK_BYTES
        with Project() as p:
            # Straddle the boundary: the first half of the armor ends block 1, the rest opens 2.
            split = len(armor) // 2
            filler = "A" * (block - split)
            (p.root / "src" / "big.txt").write_text(filler + armor + "\nMII\n", encoding="utf-8")
            _, manifest = p.dry_run("transfer")
            reasons = {e["path"]: e["reason"] for e in manifest["excluded"]}
            self.assertIn(
                "src/big.txt", reasons,
                "a secret split across a scan-block boundary was not detected; the block "
                "overlap is what makes the chunked read safe")
            self.assertIn("secret pattern", reasons["src/big.txt"])

    def test_an_unreadable_member_is_excluded_and_named(self):
        """The third outcome: not scanned must never be reported as clean.

        ⛔ Added because two negative controls escaped -- collapsing UNEXAMINED into None, and
        including an unexamined member -- and neither was visible to any fixture, because no
        fixture had a member that could not be read.
        """
        with Project() as p:
            secret_file = p.root / "src" / "unreadable.txt"
            secret_file.write_text("harmless\n", encoding="utf-8")
            secret_file.chmod(0o000)
            try:
                readable = secret_file.read_text(encoding="utf-8")
            except OSError:
                readable = None
            if readable is not None:  # running as root, or a permissive filesystem
                secret_file.chmod(0o644)
                self.skipTest("cannot make a file unreadable in this environment")
            try:
                _, manifest = p.dry_run("transfer")
                names = {f["path"] for f in manifest["included"]}
                reasons = {e["path"]: e["reason"] for e in manifest["excluded"]}
                self.assertNotIn(
                    "src/unreadable.txt", names,
                    "an unreadable member was PACKAGED unexamined; 'could not scan it' must not "
                    "be treated as 'nothing found'")
                self.assertIn("src/unreadable.txt", reasons)
                self.assertRegex(reasons["src/unreadable.txt"], r"(?i)could not be read|NOT scanned")
            finally:
                secret_file.chmod(0o644)

    def test_a_genuine_binary_still_travels(self):
        """The fix must not exclude the visualizations the archive exists to carry."""
        self.assertTrue(
            [n for n in self.names if n.endswith("docs/visualizations/graph.png")],
            "a real PNG was excluded; scanning every member must not mean excluding every "
            "binary member")

    def test_a_symlink_resolving_outside_the_project_is_skipped_and_named(self):
        if not self.project.symlinks:
            self.skipTest("symlink creation unavailable on this platform")
        self.assertFalse([n for n in self.names if n.endswith("docs/escape.md")])
        reasons = {e["path"]: e["reason"] for e in self.manifest["excluded"]}
        self.assertIn("docs/escape.md", reasons)
        self.assertIn("outside the project root", reasons["docs/escape.md"])


class TheArchiveIsSelfDescribingAndSelfExcluding(unittest.TestCase):
    def test_it_extracts_into_exactly_one_directory(self):
        with Project() as p:
            _, path = p.write_archive("share")
            tops = {name.split("/")[0] for name in members(path)}
            self.assertEqual({"senzing-bootcamp-share-%s" % DATE}, tops)

    def test_the_root_carries_both_orientation_files(self):
        with Project() as p:
            _, path = p.write_archive("share")
            root = "senzing-bootcamp-share-%s" % DATE
            names = members(path)
            self.assertIn("%s/OPEN_ME_FIRST.md" % root, names)
            self.assertIn("%s/PACKAGE_MANIFEST.json" % root, names)

    def test_the_manifest_records_what_the_spec_requires(self):
        with Project() as p:
            _, path = p.write_archive("share")
            manifest = manifest_of(path)
            self.assertEqual("share", manifest["profile"])
            self.assertTrue(manifest["plugin_version"])
            self.assertIn("query_visualize_discover", manifest["modules_completed"])
            self.assertTrue(manifest["included"])
            for entry in manifest["included"]:
                self.assertEqual(64, len(entry["sha256"]))
                self.assertIn("size_bytes", entry)
            self.assertTrue(manifest["exclusion_rules_applied"]["always"])

    def test_open_me_first_explains_the_git_exclusion(self):
        """A snapshot, not a clone -- said out loud, or the recipient cannot know."""
        with Project() as p:
            _, path = p.write_archive("share")
            root = "senzing-bootcamp-share-%s" % DATE
            with zipfile.ZipFile(path) as archive:
                text = archive.read("%s/OPEN_ME_FIRST.md" % root).decode("utf-8")
            self.assertIn("snapshot, not a clone", text)
            self.assertIn("push the repository", text)

    def test_a_second_archive_does_not_contain_the_first(self):
        """`backups/packages/` is excluded from its own output."""
        with Project() as p:
            _, first = p.write_archive("share")
            self.assertTrue(first.exists())
            result = subprocess.run(
                [sys.executable, str(PACKAGER), "--profile", "share",
                 "--project-root", str(p.root), "--date", "20260827"],
                capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            second = p.root / "backups" / "packages" / "senzing-bootcamp-share-20260827.zip"
            names = members(second)
            self.assertFalse([n for n in names if n.endswith(".zip") or "packages" in n],
                             "the second archive contains the first")


class TheArchiveIsVerifiedBeforeItIsAnnounced(unittest.TestCase):
    """INV-067's discipline: never report an artifact you have not re-opened."""

    def test_it_writes_a_sha256_sidecar_and_reports_the_digest(self):
        with Project() as p:
            result, path = p.write_archive("share")
            sidecar = path.with_suffix(path.suffix + ".sha256")
            self.assertTrue(sidecar.exists(), "no .sha256 sidecar was written")
            digest = sidecar.read_text(encoding="utf-8").split()[0]
            self.assertEqual(64, len(digest))
            self.assertIn(digest, result.stdout,
                          "the digest is not reported, so the bootcamper cannot check it")
            self.assertEqual(digest, PKG.sha256_of(path))

    def test_it_says_it_re_opened_the_archive(self):
        with Project() as p:
            result, _ = p.write_archive("share")
            self.assertIn("verified:", result.stdout)

    def test_it_says_the_plugin_transmits_nothing(self):
        """INV-135 — the flow ends by naming a local path, not by sending anything."""
        with Project() as p:
            result, _ = p.write_archive("share")
            self.assertIn("does not transmit it anywhere", result.stdout)


class ItDegradesHonestlyOnAnEmptyProject(unittest.TestCase):
    def test_a_project_with_no_artifacts_reports_rather_than_writing_an_empty_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(PACKAGER), "--profile", "share",
                 "--project-root", tmp, "--date", DATE],
                capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertIn("nothing to package", result.stderr)
            self.assertFalse(list(Path(tmp).glob("backups/packages/*.zip")))


class TheExclusionMatcherMatchesSegmentsNotSubstrings(unittest.TestCase):
    """A directory named `logs` is excluded; a file named `changelogs.md` is not."""

    def test_a_similarly_named_file_is_not_excluded(self):
        self.assertIsNone(PKG.is_excluded("docs/changelogs.md", "share"))
        self.assertIsNone(PKG.is_excluded("docs/target_state.md", "share"))
        self.assertIsNone(PKG.is_excluded("docs/environment.md", "share"))

    def test_the_real_paths_are_excluded(self):
        for rel in ("logs/run.log", ".env", "licenses/g2.lic", "config/license.json",
                    "data/raw/x.csv", ".git/config", "backups/packages/a.zip"):
            with self.subTest(rel=rel):
                self.assertIsNotNone(PKG.is_excluded(rel, "share"))

    def test_share_only_rules_do_not_apply_to_transfer(self):
        self.assertIsNotNone(PKG.is_excluded("backups/revisit/db.db", "share"))
        self.assertIsNone(PKG.is_excluded("backups/revisit/state/x.yaml", "transfer"))

    def test_a_rule_matches_wherever_its_segments_sit(self):
        """#672 — a rule anchored at the root describes one copy of a tree, not the archive."""
        self.assertEqual("data/senzing-ready",
                         PKG.is_excluded("production/data/senzing-ready/people.jsonl", "share"))
        self.assertEqual("data/raw",
                         PKG.is_excluded("production/data/raw/customers.csv", "share"))
        self.assertEqual("data/raw",
                         PKG.is_excluded("production/data/raw/customers.csv", "transfer"))
        self.assertEqual("config/license.json",
                         PKG.is_excluded("production/config/license.json", "share"))

    def test_the_mapped_inputs_are_a_share_rule_only(self):
        """`transfer` carries them: `src/load/**` reads its input from that path (INV-084)."""
        self.assertIsNone(
            PKG.is_excluded("production/data/senzing-ready/people.jsonl", "transfer"))

    def test_a_deeper_match_is_still_segment_wise(self):
        """Wherever, not however: the segments must match whole, at any depth."""
        for rel in ("production/data/senzing-readyX/people.jsonl",
                    "docs/senzing-ready-notes.md",
                    "production/metadata/raw_counts.md"):
            with self.subTest(rel=rel):
                self.assertIsNone(PKG.is_excluded(rel, "share"))


class TheDryRunNamesWhatItCouldNotMeasure(unittest.TestCase):
    """#692 — a measured size has to say what the walk never saw.

    ⛔ **The packaging flow's Step 3 creates `backups/revisit/` AFTER the question that quotes
    the transfer size.** So on any pre-graduation run -- which is the whole point of an any-time
    flow -- the figure is measured over a tree with no database backup in it, the component this
    script's own 2 GB warning calls the reason the profile is large. The figure was honest about
    having been measured and silent about what it measured.

    ⚠️ **Every absent root, never `backups/revisit` alone.** `config` and `src` are missing on an
    early run too, and a report naming one of the three would be the same partial measurement one
    level down. The conversation layer then has the fact to relay rather than having to infer it.

    Each case runs the real script as a subprocess over a fixture tree, so the report is checked
    as a Bootcamper's guide would read it, not as a function's return value.
    """

    def drop(self, project, *relatives):
        for rel in relatives:
            shutil.rmtree(project.root / rel)
            self.assertFalse((project.root / rel).exists(),
                             "the fixture still holds %s, so this case measures nothing" % rel)

    def absent_line(self, stderr):
        lines = [line for line in stderr.splitlines() if line.startswith("absent:")]
        self.assertEqual(1, len(lines),
                         "expected exactly one `absent:` line; stderr was:\n%s" % stderr)
        return lines[0]

    def test_a_complete_project_prints_no_absent_line(self):
        """⛔ Conditional, not standing text: after graduation there is nothing to disclose.

        The fixture holds every candidate root, which is the post-graduation state. A report
        that announced an omission here would train its reader to skip the line on the runs
        where it is true.
        """
        with Project() as p:
            result, _ = p.dry_run("transfer")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertNotIn("absent:", result.stderr,
                             "a complete project is told something was missing from the "
                             "measurement, which is false")

    def test_a_pre_graduation_project_names_the_missing_revisit_bundle(self):
        with Project() as p:
            self.drop(p, "backups/revisit")
            result, _ = p.dry_run("transfer")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("backups/revisit", self.absent_line(result.stderr))

    def test_it_names_every_absent_root_and_not_only_the_backup(self):
        """An early run is missing `config` and `src` as well, and the report says all three."""
        with Project() as p:
            self.drop(p, "backups/revisit", "config", "src")
            result, _ = p.dry_run("transfer")
            line = self.absent_line(result.stderr)
            for root in ("backups/revisit", "config", "src"):
                with self.subTest(root=root):
                    self.assertIn(root, line)

    def test_the_backup_absence_carries_the_fact_the_guide_relays(self):
        """⛔ The guide must not have to infer which absence matters; the script says so."""
        with Project() as p:
            self.drop(p, "backups/revisit")
            result, _ = p.dry_run("transfer")
        self.assertIn("largest part of a transfer package", result.stderr)
        self.assertIn("after this measurement", result.stderr)

    def test_the_share_profile_reports_its_own_absences_only(self):
        """`share` never walks `TRANSFER_EXTRA`, so naming it absent there would be noise."""
        with Project() as p:
            self.drop(p, "backups/revisit", "config", "src", "data/exports")
            result, _ = p.dry_run("share")
            line = self.absent_line(result.stderr)
            self.assertIn("data/exports", line)
            for root in ("backups/revisit", "config", "src"):
                with self.subTest(root=root):
                    self.assertNotIn(root, line)

    def test_the_helper_reads_the_collectors_own_record(self):
        """The absent set comes out of `skipped`, so it cannot disagree with the manifest."""
        with Project() as p:
            self.drop(p, "backups/revisit", "config")
            _members, skipped = PKG.collect(p.root, "transfer")
            self.assertEqual(["backups/revisit", "config"], PKG.absent_roots(skipped))

    def test_the_manifest_records_the_same_absences(self):
        with Project() as p:
            self.drop(p, "backups/revisit")
            _result, manifest = p.dry_run("transfer")
        named = [e["path"] for e in manifest["excluded"] if e["reason"] == PKG.NOT_PRESENT]
        self.assertEqual(["backups/revisit"], named)

    def test_the_quoted_figure_really_grows_once_the_backup_exists(self):
        """⛔ (INV-265) Anti-vacuity: the line claims a real omission, so measure it.

        Without this the report could name an absence that costs nothing, and the disclosure
        the conversation layer builds on it would be ceremony.
        """
        with Project() as p:
            _result, complete = p.dry_run("transfer")
            self.drop(p, "backups/revisit")
            _result, without = p.dry_run("transfer")
        self.assertLess(
            without["total_uncompressed_bytes"], complete["total_uncompressed_bytes"],
            "the transfer figure is the same with and without the revisit bundle, so the "
            "absence the report names changes nothing the Bootcamper was told")


if __name__ == "__main__":
    unittest.main()
