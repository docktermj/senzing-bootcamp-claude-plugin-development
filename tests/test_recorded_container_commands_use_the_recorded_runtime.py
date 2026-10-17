"""A command on a container the bootcamp has recorded runs through that container's recorded runtime.

SDK setup records each container it starts in `docker_containers` in
`config/bootcamp_progress.json`, with the `runtime` that started it: `docker`, `podman` or Apple's
`container` (INV-195). The hooks dispatch on that record, but several guide-run commands did not:
the database backup's dump and restore, Module 2 Option 1's resume, ready check and schema load,
and Module 3b's container-route teardown all hardcoded `docker exec`, `docker cp` or `docker start`,
so a Bootcamper on podman or Apple `container` was handed commands that fail (#613).

What these tests pin:

1. **No shipped skill says `docker exec`, `docker cp` or `docker start`** outside ``EXEMPT``, which
   is empty. Matching is wrap-aware (INV-346), so `docker` at a line end and `exec` on the next line
   is still caught. The route name "the `docker` path" and Module 2 Option 1's creation
   (`docker run`, `--runtime docker`) are not commands on a recorded container and do not match.
2. **Each site that was fixed names the record it dispatches on** and cites INV-195:
   `graduation/database-backup.md`'s dump and restore, Module 2 Option 1, and both Module 3b
   teardown statements.
3. **The backup probes for `cp` first**: `<runtime> cp --help` comes before the dump, and a runtime
   with no `cp` takes the existing "If the backup cannot be produced" path (INV-094).
4. **Option 1's creation is unchanged**: it still runs `docker run` and names its container with
   `--runtime docker`, since no runtime is recorded before the container exists.

Negative controls: a planted `docker exec` line, and one wrapped across two lines, fail the scan;
each site with its old `docker` command put back fails its own check.

**Cannot establish** that the commands work under podman or Apple `container`: no test runs a
container runtime, and the `cp --help` probe is read as text. The regexes and file reads are
platform-neutral (UTF-8, `pathlib`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _corpus import REPO_ROOT, corpus_files
from _wrapped_text import match_lines

SKILLS_SUBTREE = "plugins/senzing-bootcamp/skills"
SKILLS = REPO_ROOT / SKILLS_SUBTREE
BACKUP = SKILLS / "graduation" / "database-backup.md"
MODULE_2 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
VIZ_REFERENCE = SKILLS / "module-03b-truthset-visualization" / "visualization-api-reference.md"
PHASE2_CLOSE = SKILLS / "module-03b-truthset-visualization" / "phase2-close.md"

#: A container command that names Docker where the container's recorded runtime applies.
HARDCODED = re.compile(r"\bdocker\s+(?:exec|cp|start)\b")

#: Repo-relative path → reason. Empty: every hit on main was a site #613 fixed.
EXEMPT = {}

#: Suffixes read as text; anything else under the skills tree is not prose or a command.
TEXT_SUFFIXES = (".md", ".py", ".sh", ".ps1", ".json", ".yaml", ".yml", ".txt")


def read(path):
    return Path(path).read_text(encoding="utf-8")


def flat(text):
    return " ".join(text.split())


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


def skill_files():
    return corpus_files(SKILLS_SUBTREE, suffixes=TEXT_SUFFIXES)


def hardcoded_hits(text):
    return match_lines(text, HARDCODED)


def scan(files=None, texts=None):
    """`(repo-relative path, line)` for each hardcoded command outside ``EXEMPT``."""
    texts = texts if texts is not None else {
        path.relative_to(REPO_ROOT).as_posix(): read(path) for path in (files or skill_files())}
    return [(name, line) for name, text in sorted(texts.items()) if name not in EXEMPT
            for line in hardcoded_hits(text)]


def backup_problems(text):
    problems = []
    try:
        dump = between(text, "When the database runs in a container", "**If the backup cannot")
        restore = text[text.index("## Restore"):]
    except ValueError:
        return ["the container dump or the restore section not found"]
    body = flat(dump)
    for what, needle in (
        ("the record", "`<container>` and `<runtime>` are the PostgreSQL container's recorded "
                       "`name` and `runtime` in `docker_containers`"),
        ("INV-195", "(INV-195)"),
        ("the no-runtime default", "an entry with no `runtime` means `docker`"),
        ("the cp probe", "`<runtime> cp --help`"),
        ("the dump", "`<runtime> exec <container> pg_dump -U <user> -d <db> -Fc -f /tmp/senzing.dump`"),
        ("the copy out", "`<runtime> cp <container>:/tmp/senzing.dump "
                         "backups/revisit/database/senzing.dump`"),
        ("the cleanup", "`<runtime> exec <container> rm /tmp/senzing.dump`"),
        ("a failed cp", "a failed `<runtime> cp`"),
    ):
        if needle not in body:
            problems.append("backup: %s" % what)
    if "`<runtime> cp --help`" in body and "pg_dump -U <user> -d <db> -Fc -f /tmp" in body:
        if body.index("`<runtime> cp --help`") > body.index("pg_dump -U <user> -d <db> -Fc -f /tmp"):
            problems.append("backup: the cp probe comes after the dump")
    if not re.search(r"cp --help`: if it fails, the backup cannot be produced \(below\)", body):
        problems.append("backup: no cp sends nowhere")
    cannot = flat(between(text, "**If the backup cannot be produced**", "## Restore"))
    # INV-094 states that every part of the revisit bundle warns-and-continues; INV-048 is
    # the recap PDF's (#607, finished by #685).
    if "a container runtime with no `cp`" not in cannot or "(INV-094)" not in cannot:
        problems.append("backup: the cannot-be-produced path does not name the no-cp case")
    restore = flat(restore)
    for what, needle in (
        ("the record", "`<runtime>` and `<container>` from the PostgreSQL container's "
                       "`docker_containers` entry, as in the backup (INV-195)"),
        ("the copy in", "`<runtime> cp <file> <container>:/tmp/senzing.dump`"),
        ("pg_restore", "`<runtime> exec <container> pg_restore -U <user> -d <db> /tmp/senzing.dump`"),
        ("psql", "`<runtime> exec <container> psql -U <user> -d <db> -f /tmp/senzing.dump`"),
    ):
        if needle not in restore:
            problems.append("restore: %s" % what)
    return problems


def option_1_problems(text):
    try:
        option = between(text, "**Option 1 — PostgreSQL in a Docker container:**", "**Option 2")
    except ValueError:
        return ["Option 1 not found"]
    problems = []
    body = flat(option)
    for what, needle in (
        ("the resume", "restart the recorded container with `<pg-runtime> start <pg-container>`"),
        ("the resume's record", "where `<pg-runtime>` is the `runtime` its `docker_containers` "
                                "entry records (INV-195; an entry with no `runtime` means `docker`)"),
        ("the record after step 2", "From here on, `<pg-runtime>` is that recorded `runtime` "
                                    "(INV-195)"),
        ("the ready check", "`<pg-runtime> exec <pg-container> pg_isready`"),
        ("the container route's psql", "<pg-runtime> exec -i <pg-container> psql -U senzing -d G2 "
                                       "< database/szcore-schema-postgresql-create.sql"),
        ("the native route's psql", "<pg-runtime> exec -i <pg-container> psql -U senzing -d G2 "
                                    "< \"<schema path from MCP>\""),
        ("the creation", "docker run -d --name <pg-container>"),
        ("the creation's name", "container-name bootcamp-postgres --runtime docker"),
        ("the SDK container's copy", "<runtime> cp \"<sdk-container>:<schema path from MCP>\""),
    ):
        if needle not in body:
            problems.append("Option 1: %s" % what)
    return problems


def teardown_problems(reference, close):
    problems = []
    try:
        section = flat(between(reference, "### Identifying the server process",
                               "**The teardown gate.**"))
    except ValueError:
        return ["\"Identifying the server process\" not found"]
    for what, needle in (
        ("the record", "`<runtime>` and `<container>` below are the SDK container's recorded "
                       "`runtime` and `name` in `docker_containers`, the same record \"Serving "
                       "from the SDK container\" launches with (INV-195)"),
        ("the kill", "`<runtime> exec <container> sh -c 'kill <pid>'`"),
        ("the probe", "`<runtime> exec <container> python3 -c …`"),
        ("the named form", "name the `<runtime> exec` form that was tried"),
    ):
        if needle not in section:
            problems.append("visualization-api-reference.md: %s" % what)
    close = flat(close)
    if ("`<runtime> exec <container> sh -c 'kill <pid>'`, with `<runtime>` and `<container>` the "
            "SDK container's recorded `runtime` and `name` in `docker_containers`, INV-195") not in close:
        problems.append("phase2-close.md: the kill does not dispatch on the recorded runtime")
    return problems


class NoShippedSkillHardcodesDocker(unittest.TestCase):
    def test_no_hit_outside_the_exemptions(self):
        self.assertEqual(scan(), [], "dispatch on the container's recorded `runtime` from "
                                     "`docker_containers` (INV-195): `<runtime> exec`, "
                                     "`<runtime> cp`, `<runtime> start`")

    def test_the_exemption_list_is_empty(self):
        self.assertEqual(EXEMPT, {})

    def test_the_scan_reads_the_fixed_sites(self):
        """Guard the guard: the listing holds the skills tree, the four files included."""
        names = {path.relative_to(REPO_ROOT).as_posix() for path in skill_files()}
        self.assertGreater(len(names), 30)
        for path in (BACKUP, MODULE_2, VIZ_REFERENCE, PHASE2_CLOSE):
            with self.subTest(path=path.name):
                self.assertIn(path.relative_to(REPO_ROOT).as_posix(), names)

    def test_negative_control_a_planted_line_fails(self):
        text = read(BACKUP) + "\n\nThen run `docker exec <container> pg_isready`.\n"
        self.assertEqual(len(scan(texts={"planted.md": text})), 1)

    def test_negative_control_a_wrapped_command_fails(self):
        for verb in ("exec", "cp", "start"):
            with self.subTest(verb=verb):
                text = "Restart it with `docker\n%s <pg-container>` on resume.\n" % verb
                self.assertEqual(scan(texts={"planted.md": text}), [("planted.md", 1)])

    def test_route_names_and_creation_are_not_commands_on_a_recorded_container(self):
        for line in ("On SDK setup's container route (the `docker` path), the DDL exists",
                     "docker run -d --name <pg-container> \\",
                     "container-name bootcamp-postgres --runtime docker",
                     "`<runtime> exec <container> sh -c 'kill <pid>'`",
                     "a dockerfile pattern, `docker started` in prose"):
            with self.subTest(line=line):
                self.assertEqual(hardcoded_hits(line), [])


class TheBackupDispatchesOnTheRecordedRuntime(unittest.TestCase):
    def test_the_backup_and_restore(self):
        self.assertEqual(backup_problems(read(BACKUP)), [])

    def test_negative_control_the_old_dump(self):
        text = read(BACKUP).replace("`<runtime> exec <container> pg_dump",
                                    "`docker exec <container> pg_dump")
        self.assertIn("backup: the dump", backup_problems(text))

    def test_negative_control_the_old_restore(self):
        text = read(BACKUP).replace("`<runtime> cp <file> <container>:",
                                    "`docker cp <file> <container>:")
        self.assertIn("restore: the copy in", backup_problems(text))

    def test_negative_control_no_probe(self):
        text = read(BACKUP).replace("`<runtime> cp --help`", "`<runtime> version`")
        self.assertIn("backup: the cp probe", backup_problems(text))

    def test_negative_control_the_probe_after_the_dump(self):
        text = read(BACKUP)
        probe = ("First\n  check that the runtime has a `cp` with `<runtime> cp --help`: if it fails, "
                 "the backup cannot be\n  produced (below), and no dump is started.\n")
        self.assertIn(probe, text)
        moved = text.replace(probe, "\n").replace(
            "  3. `<runtime> exec <container> rm /tmp/senzing.dump`\n",
            "  3. `<runtime> exec <container> rm /tmp/senzing.dump`\n  " + probe.replace("\n  ", " "))
        self.assertIn("backup: the cp probe comes after the dump", backup_problems(moved))


class Option1DispatchesOnTheRecordedRuntime(unittest.TestCase):
    def test_option_1(self):
        self.assertEqual(option_1_problems(read(MODULE_2)), [])

    def test_negative_control_the_old_resume(self):
        text = read(MODULE_2).replace("`<pg-runtime> start <pg-container>`",
                                      "`docker start <pg-container>`")
        self.assertIn("Option 1: the resume", option_1_problems(text))

    def test_negative_control_the_old_schema_load(self):
        text = read(MODULE_2).replace("<pg-runtime> exec -i <pg-container> psql",
                                      "docker exec -i <pg-container> psql")
        problems = option_1_problems(text)
        self.assertIn("Option 1: the container route's psql", problems)
        self.assertIn("Option 1: the native route's psql", problems)

    def test_negative_control_the_creation_changed(self):
        text = read(MODULE_2).replace("docker run -d --name <pg-container>",
                                      "<pg-runtime> run -d --name <pg-container>")
        self.assertIn("Option 1: the creation", option_1_problems(text))


class TheTeardownDispatchesOnTheRecordedRuntime(unittest.TestCase):
    def test_the_teardown(self):
        self.assertEqual(teardown_problems(read(VIZ_REFERENCE), read(PHASE2_CLOSE)), [])

    def test_negative_control_the_old_kill(self):
        reference = read(VIZ_REFERENCE).replace("`<runtime> exec <container> sh -c 'kill <pid>'`",
                                                "`docker exec <container> sh -c 'kill <pid>'`")
        close = read(PHASE2_CLOSE).replace("(`<runtime> exec <container> sh -c 'kill <pid>'`",
                                           "(`docker exec <container> sh -c 'kill <pid>'`")
        problems = teardown_problems(reference, close)
        self.assertIn("visualization-api-reference.md: the kill", problems)
        self.assertIn("phase2-close.md: the kill does not dispatch on the recorded runtime",
                      problems)


if __name__ == "__main__":
    unittest.main()
