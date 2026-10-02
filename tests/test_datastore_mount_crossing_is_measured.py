"""The datastore's location is measured before it is created, not assumed.

Enforces **INV-262** — where the SDK runs in a Linux environment while the project resides on
a mounted host filesystem, the datastore's placement MUST be measured before it is created,
using the diagnostic the server prescribes, and the measurement MUST be reported. Registered
2026-08-21 at the maintainer's sign-off, after the 2026-08-21 audit found the rule shipped and
unregistered; the wording was narrowed at sign-off so the relocation clause could not read as
authorizing what INV-200 forbids.

`database/G2C.db` inside the project directory is right on every platform except one: when the SDK
runs in a Linux environment while the project lives on the host's filesystem, the database is
reached over a translation layer. The signature cases are WSL2 with the project under `/mnt/` and a
Docker bind mount. Nothing errors — it is one to two orders of magnitude slower, and a Bootcamper
has no reason to suspect storage.

Measured on one workstation (Windows 11 + WSL2 Ubuntu, SDK 4.3.4, SQLite, 2026-08-18):
`check_repository_performance(5)` reported 1,112 inserts on `/mnt/c/...` against 326,606 on a
WSL-native path, and end-to-end throughput moved from 3 records/second to 138-180 — about 7.5 hours
down to about 9 minutes for 83,338 records, same code and data and machine.

⚠️ **What this file guards is the instrument, not the number.** The figures above are one machine's
and are recorded as observation-only; what has to be in the shipped text is the *measurement* — the
`check_repository_performance` call, which before this change had **zero** occurrences anywhere in
the plugin, despite Senzing's own anti-patterns saying to run it before a large load and the module
already calling `search_docs(category='anti_patterns')` at the step that installs the SDK.

**Scope: this is a partial implementation, deliberately.** The spec also proposed offering to
relocate the datastore out of the project directory, which needs an INV-200 carve-out and a
write-gate change. The maintainer held that half for review, so the tests below assert the
detect-and-measure half AND that the relocation is *not* applied unilaterally.

Source spec: `specs/datastore-goes-in-the-project-directory-which-on-wsl2-is-the-slow-one.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE2 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"


def sqlite_branch():
    """Step 7's SQLite branch, up to the schema rungs."""
    text = MODULE2.read_text(encoding="utf-8")
    start = text.index("**For SQLite** (recommended for bootcamp):")
    end = text.index('⛔ **SQLite is not "no setup"', start)
    return re.sub(r"\s+", " ", text[start:end])


class TheScanIsNotVacuous(unittest.TestCase):
    def test_the_branch_is_locatable(self):
        self.assertIn("datastore", sqlite_branch(),
                      "Step 7's SQLite branch was not located; every check below is vacuous")


class TheCrossingIsDetectedBeforeTheDatastoreExists(unittest.TestCase):
    def setUp(self):
        self.branch = sqlite_branch()

    def test_it_names_the_mounted_filesystem_cases(self):
        self.assertIn("/mnt/", self.branch,
                      "the WSL2 case is not named, so the check cannot fire on it")
        self.assertRegex(self.branch, r"(?i)bind mount",
                         "the Docker bind-mount case is not named")

    def test_it_says_nothing_fails(self):
        """The whole difficulty: no error, so nobody looks."""
        self.assertRegex(
            self.branch, r"(?i)Nothing fails",
            "the branch does not say the failure is silent, which is why a Bootcamper "
            "experiences it as the bootcamp being slow rather than as a storage problem")

    def test_the_check_precedes_creation(self):
        text = MODULE2.read_text(encoding="utf-8")
        crossing = text.index("check whether the project sits on a mounted host filesystem")
        mkdir = text.index("**Create the database directory:**")
        self.assertLess(
            crossing, mkdir,
            "the crossing check appears after the datastore is created, so the Bootcamper "
            "learns the cost only once the slow file exists")


class TheMeasurementIsNamedAndNonBlocking(unittest.TestCase):
    def setUp(self):
        self.branch = sqlite_branch()

    def test_check_repository_performance_is_named(self):
        self.assertIn(
            "check_repository_performance", self.branch,
            "the measurement is not named. Senzing's anti-patterns prescribe it before a large "
            "load, and it had zero occurrences in the plugin before this change")

    def test_it_names_the_owning_class_rather_than_the_engine(self):
        self.assertRegex(
            self.branch, r"(?i)SzDiagnostic",
            "the call is attributed to no class; it is a diagnostic-hub call, and a reader "
            "looking for it on SzEngine will not find it")

    def test_it_defers_the_signature_to_the_server(self):
        """INV-080: the call shape is not the plugin's to assert."""
        self.assertRegex(
            self.branch, r"(?i)from the server at the point of use rather than from this file",
            "the branch hardcodes the call instead of sourcing it at the point of use")

    def test_a_failed_measurement_does_not_block(self):
        self.assertRegex(
            self.branch, r"(?i)Non-blocking",
            "a measurement that cannot run would stall setup (INV-048)")

    def test_senzings_own_anti_patterns_are_cited_with_version_and_date(self):
        self.assertIn("category='anti_patterns'", self.branch,
                      "the anti-pattern route is not named")
        # Re-measured for #383 (was 1.33.0, 2026-08-21): the prose stamp follows the
        # VERIFIED_QUERIES record in tests/test_prescribed_search_queries.py.
        self.assertRegex(self.branch,
                         r"1\.37\.19\*\*, docs index 2026-10-02 18:46\s+UTC, \*\*2026-10-02",
                         "the anti-pattern citation carries no server version and date")


class TheFiguresAreObservationOnly(unittest.TestCase):
    def setUp(self):
        self.branch = sqlite_branch()

    def test_the_throughput_numbers_are_marked_observation_only(self):
        self.assertRegex(
            self.branch, r"(?i)Observation-only",
            "the measured figures read as a general rule rather than as one machine's")

    def test_they_carry_their_conditions(self):
        for token in ("4.3.4", "2026-08-18", "83,338"):
            with self.subTest(token=token):
                self.assertIn(token, self.branch,
                              "the observation does not carry %s, so it cannot be re-checked "
                              "against comparable conditions" % token)


class TheRelocationIsNotAppliedUnilaterally(unittest.TestCase):
    """The held half. INV-200 is not carved out here, so nothing may move the datastore."""

    def test_the_default_stays_in_the_project_directory(self):
        branch = sqlite_branch()
        self.assertRegex(
            branch, r"(?i)Do not relocate the datastore out of the project directory",
            "nothing forbids relocating the datastore, but INV-200 has no carve-out for it "
            "and the write gate has not been changed — so a relocation would violate both")
        self.assertRegex(
            branch, r"(?i)the default\s*stays `database/G2C\.db`",
            "the branch does not state that the default is unchanged")

    def test_inv200_has_no_relocation_carve_out_yet(self):
        """Pins the boundary of the partial implementation, so the halves cannot drift."""
        invariants = (REPO_ROOT / "specs" / "INVARIANTS.md").read_text(encoding="utf-8")
        m = re.search(r"(?m)^- \*\*INV-200\*\*.*?(?=\n- \*\*INV-)", invariants, re.S)
        self.assertIsNotNone(m, "INV-200 not found")
        self.assertNotRegex(
            m.group(0), r"(?i)relocat",
            "INV-200 now mentions relocation. If the carve-out landed, this test and the "
            "'do not relocate' rule above both need revisiting together")


if __name__ == "__main__":
    unittest.main()
