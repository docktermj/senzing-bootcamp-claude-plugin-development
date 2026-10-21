"""SDK setup Step 7's SQLite "is the schema already applied?" probe finds `SYS_CFG` (#748).

Enforces **INV-393** at its SQLite site: the probe must ask whether the schema is applied, so it
must answer True on a datastore the shipped schema DDL created. ⚠️ It runs the shipped command; it
**cannot** establish that a live guide runs it, only that the command, as shipped, answers right.

Step 7's instruction 3 shipped the SQLite probe as `... AND name='sys_cfg'`, carried over from the
PostgreSQL query when #684 added the branch. SQLite keeps a table name in `sqlite_master` exactly as
its DDL declares it, and `=` compares with BINARY collation, while the SQLite DDL that ships with
the SDK declares the table in upper case — `/opt/senzing/er/resources/schema/
szcore-schema-sqlite-create.sql` has `CREATE TABLE SYS_CFG (...)` (SDK 4.4.2.26272, observed
2026-10-21; a local observation of the shipped file, not an MCP fact, INV-080). So the probe
printed False on a datastore whose schema was applied, and pointed the next step at re-applying the
DDL. The PostgreSQL probe is correct as written, because PostgreSQL folds an unquoted name to lower
case, and this test does not touch it.

The test reads the probe out of the shipped fence (INV-108: the skill is read as text) and runs it,
argument for argument, with this interpreter in place of `python3`, against a temporary datastore:

* built from a stand-in DDL that declares `SYS_CFG` in upper case — True;
* with the table declared in lower case — True, since the question is the table, not its case;
* holding no Senzing table — False;
* absent — False, and the file is still absent afterwards: the `os.path.exists` guard keeps
  `sqlite3.connect` from creating an empty one;
* built from the installed `szcore-schema-sqlite-create.sql` — True. That case is **skipped where
  the file is absent**, as on a CI runner, which has no Senzing install; the stand-in carries the
  check there.

The negative control runs the SAME check over the module with the probe restored to its pre-#748
case-sensitive form, which must fail (INV-265). Python's `sqlite3` module is the only dependency,
as it is for the shipped probe.

Run:  python3 -m unittest discover -s tests
"""
import shlex
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_02 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-02-sdk-setup" / "SKILL.md"
#: Step 7's instruction 3, which owns the probe, and the paragraph after it.
INSTRUCTION_3 = "3. ⛔ **(INV-393) When the datastore already exists"
HANDLING = "**Handling each answer (INV-284).**"
#: The datastore path the shipped probe names, which the test points at a temporary one.
DATASTORE = "database/G2C.db"
#: The SQLite DDL the SDK installs; read when present, never required.
INSTALLED_DDL = Path("/opt/senzing/er/resources/schema/szcore-schema-sqlite-create.sql")
#: A stand-in for the shipped DDL: the table the probe asks about, declared in upper case.
UPPER_DDL = ("CREATE TABLE SYS_CFG (CONFIG_DATA_ID BIGINT NOT NULL, CONFIG_DATA CLOB NOT NULL, "
             "PRIMARY KEY(CONFIG_DATA_ID));\nCREATE TABLE SYS_VARS (VAR_GROUP VARCHAR(50));\n")
LOWER_DDL = "CREATE TABLE sys_cfg (config_data_id BIGINT NOT NULL);\n"
NO_SCHEMA_DDL = "CREATE TABLE OTHER (X INT);\n"
#: The pre-#748 comparison and its fix, for the negative control.
FIXED = "name='SYS_CFG' COLLATE NOCASE"
CASE_SENSITIVE = "name='sys_cfg'"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def instruction_3(m2):
    begin = m2.index(INSTRUCTION_3)
    return m2[begin:m2.index(HANDLING, begin)]


def sqlite_probe(m2):
    """The shipped SQLite probe's argv, or a problem string when there is not exactly one."""
    # Line-scoped by design (#748): the probe is one shell command on one fenced line, which the
    # test runs as written; it is not a prose phrase that could wrap (INV-346).
    lines =[line.strip() for line in instruction_3(m2).splitlines()
             if line.strip().startswith("python3 -c") and "sqlite_master" in line]
    if len(lines) != 1:
        return f"Step 7's instruction 3 carries {len(lines)} SQLite probes; it needs one"
    argv = shlex.split(lines[0])
    if len(argv) != 4 or argv[:2] != ["python3", "-c"] or argv[3] != DATASTORE:
        return f"the SQLite probe is not `python3 -c \"...\" {DATASTORE}`: {argv!r}"
    return argv


def run_probe(argv, datastore):
    """Run the shipped probe with this interpreter against `datastore`; return what it prints."""
    result = subprocess.run([sys.executable, "-c", argv[2], str(datastore)],
                            capture_output=True, text=True, timeout=60, check=False)
    if result.returncode != 0:
        return f"exit {result.returncode}: {result.stderr.strip()}"
    return result.stdout.strip()


def build(datastore, ddl):
    connection = sqlite3.connect(datastore)
    try:
        connection.executescript(ddl)
        connection.commit()
    finally:
        connection.close()


# --- check: returns a list of problems ----------------------------------------------------------


def probe_problems(m2, cases):
    """Run the shipped probe on each `(label, ddl or None, expected)`; None means no file."""
    argv = sqlite_probe(m2)
    if isinstance(argv, str):
        return [argv]
    problems = []
    with tempfile.TemporaryDirectory() as scratch:
        for index, (label, ddl, expected) in enumerate(cases):
            datastore = Path(scratch) / f"case-{index}" / "G2C.db"
            datastore.parent.mkdir()
            if ddl is not None:
                build(datastore, ddl)
            printed = run_probe(argv, datastore)
            if printed != str(expected):
                problems.append(f"on a datastore {label}, the shipped SQLite probe printed "
                                f"{printed!r}; it must print {expected}")
            if ddl is None and datastore.exists():
                # `sqlite3.connect` creates the file it is given, so an unguarded probe leaves
                # an empty G2C.db behind for the next step to find.
                problems.append(f"on a datastore {label}, the shipped SQLite probe created "
                                f"{DATASTORE}; its os.path.exists guard must stop that")
    return problems


STAND_IN_CASES = (
    ("built from a DDL that declares SYS_CFG in upper case", UPPER_DDL, True),
    ("whose table is declared sys_cfg in lower case", LOWER_DDL, True),
    ("holding no Senzing table", NO_SCHEMA_DDL, False),
    ("that does not exist", None, False),
)


class TheSqliteProbeFindsTheDeclaredTable(unittest.TestCase):

    def setUp(self):
        self.m2 = read(MODULE_02)

    def test_the_probe_answers_on_the_stand_in_datastores(self):
        self.assertEqual(probe_problems(self.m2, STAND_IN_CASES), [])

    @unittest.skipUnless(INSTALLED_DDL.is_file(), f"{INSTALLED_DDL} is not installed here")
    def test_the_probe_answers_true_on_the_installed_ddl(self):
        ddl = INSTALLED_DDL.read_text(encoding="utf-8")
        self.assertEqual(probe_problems(self.m2, (
            (f"built from {INSTALLED_DDL.name}", ddl, True),)), [])

    def test_the_postgresql_probe_is_left_as_written(self):
        # Out of scope for #748, and correct: PostgreSQL folds an unquoted name to lower case.
        self.assertIn("SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'sys_cfg')",
                      instruction_3(self.m2))


class NegativeControls(unittest.TestCase):
    """Each mutation restores a broken shape, which the check must report."""

    def setUp(self):
        self.m2 = read(MODULE_02)

    def test_the_pre_748_case_sensitive_probe_fails(self):
        broken = self.m2.replace(FIXED, CASE_SENSITIVE, 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        problems = probe_problems(broken, STAND_IN_CASES)
        self.assertTrue(any("in upper case" in p for p in problems), problems)

    def test_a_probe_without_its_existence_guard_fails(self):
        broken = self.m2.replace("os.path.exists(p) and ", "", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        problems = probe_problems(broken, STAND_IN_CASES)
        self.assertTrue(any("guard must stop that" in p for p in problems), problems)

    def test_a_missing_probe_fails(self):
        broken = self.m2.replace("sqlite_master", "sqlite_schema_gone", 1)
        self.assertNotEqual(broken, self.m2, "control did not apply")
        self.assertTrue(any("0 SQLite probes" in p
                            for p in probe_problems(broken, STAND_IN_CASES)))


if __name__ == "__main__":
    unittest.main()
