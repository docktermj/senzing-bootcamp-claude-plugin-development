"""#618: Module 6 names the repository for both engines, and six smaller sibling fixes hold.

**The repository branch (item 2).** Module 6 named `database/G2C.db` as *the* repository at
fifteen sites, on a run whose `database_type` may be `postgresql`: "back up `database/G2C.db`",
"override paths to `database/G2C.db`", "restore from the `database/G2C.db` backup". On
PostgreSQL there is no such file, so the backup step had nothing to copy and the recovery step
deleted nothing that mattered. `SKILL.md` → "The repository, on either engine" now states the
branch once: the file `database/G2C.db` on SQLite, the connection in `config/engine_config.json`
on PostgreSQL, with backup and restore through `graduation/database-backup.md` to
`data/backups/` (INV-050's reserved data-backup directory, INV-300's one statement). Every
other site names both engines in a clause and links to it.

The guard is **paragraph-level and derived, not a site list**: every paragraph (a block between
blank lines, or one list item) of every `module-06-data-processing/*.md` file that names
`G2C.db` must also name PostgreSQL or `database_type`, and must link to the statement. A new
site written later without the branch fails at once, wherever it lands.

The rest of #618, each asserted against the shipped text:

* item 1, Module 3 Step 3's `MCP-NEGATIVE` names the live `access_steps` order;
* item 3, every Module 6 `generate_scaffold` call and Module 3 Step 1a cite ground-rules.md →
  "Follow each response's own `access_steps`, in the order it gives them" (INV-160, INV-300);
* item 4, Truth Set teardown's "no" branch conditions the URL on `web_service`, and the
  fallback record says it carries one `reason`;
* item 6, `module_6_processing.midpoint_record` at its writer and its reader;
* item 7, Module 2's NuGet source goes to the project's `nuget.config` (INV-199).

Item 5 (INV-275's enforcer) needed no change and is not asserted here.

Every predicate returns a list of problems, and the negative controls at the bottom run each
one on a mutant of the shipped text.

Stdlib only; shipped markdown read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_06 = SKILLS / "module-06-data-processing"
MODULE_06_SKILL = MODULE_06 / "SKILL.md"
PHASE_B = MODULE_06 / "phaseB-load-first-source.md"
PHASE_D = MODULE_06 / "phaseD-validation.md"
BACKUP = SKILLS / "graduation" / "database-backup.md"
MODULE_02 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
MODULE_03 = SKILLS / "module-03-system-verification" / "phase1-verification.md"
TRUTHSET_CLOSE = SKILLS / "module-03b-truthset-visualization" / "phase2-close.md"
TRUTHSET_VIZ = SKILLS / "module-03b-truthset-visualization" / "phase1-visualization.md"
DISCOVER = SKILLS / "module-07-query-visualize-discover" / "phase2-discover.md"

STATEMENT_ANCHOR = '<a id="the-repository"></a>'
STATEMENT_LEAD = "**The repository, on either engine.**"
#: A link to the statement, from SKILL.md itself or from a phase file beside it.
STATEMENT_LINK = re.compile(r"\]\((?:SKILL\.md)?#the-repository\)")
#: The one paragraph that names `G2C.db` and predates the statement: it already names both
#: engines, and the issue leaves it out of scope.
PREREQUISITES = "**Prerequisites:**"
ENGINE_BRANCH = re.compile(r"PostgreSQL|`database_type`")
#: Text only `database-backup.md` may carry: the procedure itself.
PROCEDURE = re.compile(r"pg_dump|pg_restore|cp database/G2C\.db|backups/revisit")

ROUTE_POINTER = ("`../bootcamp-onboarding/ground-rules.md` → \"Follow each response's own "
                 "`access_steps`, in the order it gives them\" says (INV-160, INV-300)")
#: A `generate_scaffold` call a step makes, as opposed to the tool named in passing.
SCAFFOLD_CALL = re.compile(r"generate_scaffold\(\w+=|Call `generate_scaffold` with")
MIDPOINT_KEY = "`module_6_processing.midpoint_record`"
#: Built by concatenation so this file carries no marker token of its own (the negatives scan
#: reads `tests/`).
MARKER_TOKEN = "MCP-NEGATIVE" + ":"
SCAFFOLD_MARKER = ("<!-- " + MARKER_TOKEN
                   + " generate_scaffold(language='python', workflow='initialize')")


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    return re.sub(r"\s+", " ", text)


def paragraphs(text):
    """Each block between blank lines, split again at every list item; comments removed."""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    units = []
    for block in re.split(r"\n\s*\n", text):
        units.extend(u for u in re.split(r"\n(?=\s*(?:[-*]|\d+\.) )", block) if u.strip())
    return units


def module6_texts():
    return {path.name: read(path) for path in sorted(MODULE_06.glob("*.md"))}


# --- Item 2: the repository follows `database_type`. ---------------------------------------


def branch_problems(texts):
    """Each paragraph naming `G2C.db` names the other engine and links to the statement."""
    problems = []
    for name, text in texts.items():
        for unit in paragraphs(text):
            if "G2C.db" not in unit:
                continue
            where = "%s: %r" % (name, flat(unit)[:90])
            if not ENGINE_BRANCH.search(unit):
                problems.append("%s names G2C.db and neither PostgreSQL nor database_type"
                                % where)
            if (STATEMENT_ANCHOR not in unit and PREREQUISITES not in unit
                    and not STATEMENT_LINK.search(unit)):
                problems.append("%s names G2C.db without linking to the repository statement "
                                "(INV-300)" % where)
    return problems


def statement_problems(skill):
    """SKILL.md states the branch once, with the backup route and destination."""
    units = [u for u in paragraphs(skill) if STATEMENT_ANCHOR in u]
    if len(units) != 1:
        return ["SKILL.md must state the repository once, under %s; found %d"
                % (STATEMENT_ANCHOR, len(units))]
    body = flat(units[0])
    problems = []
    for what, pattern in (
        ("its lead", re.escape(STATEMENT_LEAD)),
        ("that it is the one statement (INV-300)", r"one statement.*\(INV-300\)"),
        ("the key it reads", r"Read `database_type` from `config/bootcamp_preferences\.yaml`"),
        ("the SQLite repository", r"On SQLite the repository is the file `database/G2C\.db`"),
        ("the PostgreSQL repository", r"on PostgreSQL it is the Senzing database named by the "
                                      r"connection in `config/engine_config\.json`"),
        ("the never-guess rule", r"absent or indeterminate.*never guess"),
        ("the one backup implementation", r"go through `\.\./graduation/database-backup\.md`"),
        ("the destination", r"destination `data/backups/`"),
        ("the SQLite copy", r"`data/backups/G2C\.db\.pre-load` on SQLite"),
        ("the PostgreSQL dump", r"`data/backups/senzing\.dump\.pre-load` on PostgreSQL"),
        ("the warn-and-continue path", r"\(warn and continue\) applies here"),
    ):
        if not re.search(pattern, body):
            problems.append("the repository statement does not state %s" % what)
    return problems


def procedure_copy_problems(texts):
    """No Module 6 file restates database-backup.md's procedure (INV-300)."""
    return ["%s restates the backup procedure (%s); cite database-backup.md instead"
            % (name, m.group(0))
            for name, text in texts.items() for m in PROCEDURE.finditer(text)]


def backup_file_problems(text):
    """database-backup.md takes Module 6 as a caller and keeps its callers' destination."""
    body = flat(text)
    problems = []
    for what, needle in (
        ("Module 6 as a caller", "`../module-06-data-processing/SKILL.md` → \"The repository, "
                                 "on either engine\""),
        ("three callers", "Three callers cite it"),
        ("Module 6's SQLite copy", "`data/backups/G2C.db.pre-load` on SQLite"),
        ("Module 6's PostgreSQL dump", "`data/backups/senzing.dump.pre-load` on PostgreSQL"),
        ("the existing callers' destination", "Graduation and packaging write "
                                              "`backups/revisit/database/`"),
        ("the existing callers' dump command",
         "`pg_dump -U <user> -d <db> -Fc -f backups/revisit/database/senzing.dump`"),
        ("Module 6's restore", "Module 6's Phase D recovery restores from its own destination"),
    ):
        if needle not in body:
            problems.append("database-backup.md does not state %s" % what)
    return problems


def recovery_problems(phase_d):
    """Phase D's recovery restores by database-backup.md and branches with no backup."""
    start = phase_d.find("## Recovery from failed load")
    if start == -1:
        return ["Phase D has no recovery section"]
    end = phase_d.find("\n### ", start)
    body = flat(phase_d[start:end])
    problems = []
    for what, needle in (
        ("the restore route", "by `../graduation/database-backup.md` → \"Restore\""),
        ("the SQLite restore", "`data/backups/G2C.db.pre-load` back to `database/G2C.db` on "
                               "SQLite"),
        ("the PostgreSQL restore", "`data/backups/senzing.dump.pre-load` into a fresh database on "
                                   "PostgreSQL"),
        ("the no-backup branch", "If there is no backup, branch on `database_type`"),
        ("the SQLite rebuild", "on SQLite, delete `database/G2C.db` and re-run the Module 2 "
                               "config"),
        ("the PostgreSQL rebuild", "on PostgreSQL, recreate the Senzing database, apply the schema "
                                   "again"),
        ("the schema step it reuses", "Step 7, Option 1 steps 3–4"),
    ):
        if needle not in body:
            problems.append("Phase D recovery does not state %s" % what)
    return problems


# --- Item 3: fetching steps cite the access_steps route. -----------------------------------


def route_citation_problems(texts):
    """Every Module 6 paragraph making a generate_scaffold call cites the route paragraph."""
    problems = []
    for name, text in texts.items():
        for unit in paragraphs(text):
            if SCAFFOLD_CALL.search(unit) and ROUTE_POINTER not in flat(unit):
                problems.append("%s calls generate_scaffold without citing the access_steps "
                                "route: %r" % (name, flat(unit)[:90]))
    return problems


def module3_problems(text):
    problems = []
    start = text.index("### Step 1a: Engine Initialization Check")
    step_1a = flat(text[start:text.index("\n### ", start + 1)])
    if ROUTE_POINTER not in step_1a:
        problems.append("Module 3 Step 1a re-obtains the scaffold without citing the "
                        "access_steps route")
    markers = re.findall(re.escape(SCAFFOLD_MARKER) + r".*?-->", text, flags=re.S)
    if len(markers) != 1:
        return problems + ["Module 3 Step 3's generate_scaffold marker is missing"]
    marker = markers[0]
    for what, needle in (
        ("the hosted url first", "each item's url, served by the MCP server, or its raw_url "
                                 "if that fails"),
        ("the hash check", "sha256sum of the saved file must print the item's hash"),
        ("the clone after the fetch", "then git_clone, then the final inline step"),
    ):
        if needle not in marker:
            problems.append("Module 3 Step 3's marker does not name %s" % what)
    if "fetch raw_url, else git clone" in marker:
        problems.append("Module 3 Step 3's marker still names the retired two-step route")
    if not re.search(r"server 1\.(?:3[89]|[4-9]\d)\.\d+, 2026-1\d-\d\d -->$", marker):
        problems.append("Module 3 Step 3's marker is not stamped with the re-check's server "
                        "and date")
    return problems


# --- Item 4: Truth Set teardown wording. ---------------------------------------------------


def teardown_problems(close, viz):
    problems = []
    start = close.index("**On \"no\" or \"not yet\":**")
    no_branch = flat(close[start:close.index("\n\n", start)])
    if "When `web_service.status` is `\"passed\"`, tell the bootcamper the server is still at " \
       "its URL" not in no_branch:
        problems.append("the teardown's no branch does not condition the URL on web_service")
    if "when it is `\"unavailable\"`, no server ran" not in no_branch:
        problems.append("the teardown's no branch does not say what to tell on unavailable")
    if "The record carries one `reason`, on `web_service` alone" not in flat(viz):
        problems.append("the Fallback's closing record does not say it carries one reason")
    return problems


# --- Item 6: midpoint_record's key path. ---------------------------------------------------


def midpoint_problems(phase_b, discover):
    problems = []
    start = phase_b.index("**Checkpoint:** write step 9")
    if MIDPOINT_KEY not in flat(phase_b[start:phase_b.index("\n\n", start)]):
        problems.append("Module 6 step 9's checkpoint does not name %s" % MIDPOINT_KEY)
    start = discover.index("**The entity that now holds `midpoint_record`:**")
    if MIDPOINT_KEY not in flat(discover[start:start + 400]):
        problems.append("Module 7's Discover phase does not read %s" % MIDPOINT_KEY)
    return problems


# --- Item 7: the NuGet source is project-local. --------------------------------------------


def csharp_bullet(text):
    start = text.index("   - **C#:**")
    return text[start:text.index("   - **Rust:**", start)]


def nuget_problems(module_02):
    bullet = flat(csharp_bullet(module_02))
    problems = []
    for m in re.finditer(r"`dotnet nuget add source [^`]*`", bullet):
        if "--configfile nuget.config" not in m.group(0):
            problems.append("%s writes the user-level NuGet.Config (INV-199)" % m.group(0))
    for what, needle in (
        ("the INV-199 rule", "⛔ **(INV-199) The source goes into the project's `nuget.config`, "
                             "never the user-level `NuGet.Config`.**"),
        ("the file's creation", "run `dotnet new nugetconfig` when `nuget.config` is absent"),
        ("the `<clear/>` disclosure", "the new file starts with `<clear/>` and re-adds nuget.org"),
        ("an existing file kept", "When `nuget.config` already exists, leave it"),
        ("the flag on the reply's command", "give whichever command adds the source, the reply's "
                                            "own or the one above, `--configfile nuget.config`"),
    ):
        if needle not in bullet:
            problems.append("Module 2's C# bullet does not state %s" % what)
    return problems


# --- The shipped files hold. ---------------------------------------------------------------


class Module6NamesTheRepositoryForBothEngines(unittest.TestCase):
    def setUp(self):
        self.texts = module6_texts()

    def test_every_g2c_paragraph_branches_and_cites_the_statement(self):
        self.assertEqual(branch_problems(self.texts), [])

    def test_the_scan_is_not_vacuous(self):
        """INV-265: a scan that finds no G2C.db paragraph proves nothing."""
        found = [u for t in self.texts.values() for u in paragraphs(t) if "G2C.db" in u]
        self.assertGreaterEqual(len(found), 15, "the paragraph scan found almost nothing")

    def test_the_statement_is_stated_once(self):
        self.assertEqual(statement_problems(self.texts["SKILL.md"]), [])

    def test_no_module_6_file_restates_the_procedure(self):
        self.assertEqual(procedure_copy_problems(self.texts), [])

    def test_the_backup_file_takes_module_6_as_its_third_caller(self):
        self.assertEqual(backup_file_problems(read(BACKUP)), [])

    def test_the_recovery_restores_by_the_backup_file(self):
        self.assertEqual(recovery_problems(read(PHASE_D)), [])


class TheSiblingItemsHold(unittest.TestCase):
    def test_module_6_scaffold_calls_cite_the_route(self):
        self.assertEqual(route_citation_problems(module6_texts()), [])

    def test_the_route_scan_is_not_vacuous(self):
        calls = [u for t in module6_texts().values() for u in paragraphs(t)
                 if SCAFFOLD_CALL.search(u)]
        self.assertGreaterEqual(len(calls), 6, "the scaffold-call scan found almost nothing")

    def test_module_3_cites_the_route_and_stamps_the_marker(self):
        self.assertEqual(module3_problems(read(MODULE_03)), [])

    def test_the_teardown_wording(self):
        self.assertEqual(teardown_problems(read(TRUTHSET_CLOSE), read(TRUTHSET_VIZ)), [])

    def test_midpoint_record_has_its_key_path(self):
        self.assertEqual(midpoint_problems(read(PHASE_B), read(DISCOVER)), [])

    def test_the_nuget_source_is_project_local(self):
        self.assertEqual(nuget_problems(read(MODULE_02)), [])


# --- Negative controls: each predicate fails on a mutant. ----------------------------------


def _replace(text, old, new):
    assert old in text, "the mutation's anchor is gone: %r" % old[:60]
    return text.replace(old, new, 1)


class NegativeControls(unittest.TestCase):
    def setUp(self):
        self.texts = module6_texts()

    def mutate(self, name, old, new):
        texts = dict(self.texts)
        texts[name] = _replace(texts[name], old, new)
        return texts

    def test_a_site_that_drops_the_postgresql_clause_is_caught(self):
        texts = self.mutate(
            "phaseB-load-first-source.md",
            "on SQLite (`database/G2C.db`) or PostgreSQL alike. The",
            "(`database/G2C.db`). The")
        self.assertTrue(any("neither PostgreSQL" in p for p in branch_problems(texts)))

    def test_a_new_site_without_the_branch_is_caught(self):
        texts = dict(self.texts)
        texts["phaseC-multi-source.md"] += "\n\nBack up `database/G2C.db` before step 19.\n"
        problems = branch_problems(texts)
        self.assertTrue(any("neither PostgreSQL" in p for p in problems))
        self.assertTrue(any("without linking" in p for p in problems))

    def test_a_list_item_does_not_borrow_its_siblings_branch(self):
        """The unit is one list item, so a sibling's PostgreSQL clause does not cover it."""
        texts = self.mutate(
            "SKILL.md",
            "- **No direct SQL.** Never generate SQL against [the repository](#the-repository) "
            "(`database/G2C.db`\n  on SQLite, the Senzing database on PostgreSQL) or its "
            "internal tables.",
            "- **No direct SQL.** Never generate SQL against [the repository](#the-repository) "
            "(`database/G2C.db`) or its internal tables.")
        self.assertTrue(any("neither PostgreSQL" in p for p in branch_problems(texts)))

    def test_a_site_that_drops_its_link_is_caught(self):
        texts = self.mutate(
            "phaseD-validation.md",
            "restore [the repository](SKILL.md#the-repository) from its",
            "restore the repository from its")
        self.assertTrue(any("without linking" in p for p in branch_problems(texts)))

    def test_the_statement_losing_its_postgresql_half_is_caught(self):
        skill = _replace(self.texts["SKILL.md"], "on\nPostgreSQL it is the Senzing database",
                         "on\nPostgreSQL it is some database")
        self.assertTrue(statement_problems(skill))

    def test_a_restated_procedure_is_caught(self):
        texts = dict(self.texts)
        texts["phaseD-validation.md"] += "\n\nRun `pg_dump -U <user> -d <db> -Fc -f x`.\n"
        self.assertTrue(procedure_copy_problems(texts))

    def test_the_backup_file_without_module_6_is_caught(self):
        text = _replace(read(BACKUP), "- `../module-06-data-processing/SKILL.md`", "- a module")
        self.assertTrue(backup_file_problems(text))

    def test_the_old_recovery_is_caught(self):
        text = _replace(read(PHASE_D), "If there is no backup, branch on `database_type`:",
                        "If no backup,")
        self.assertTrue(recovery_problems(text))

    def test_a_scaffold_call_without_the_route_is_caught(self):
        texts = dict(self.texts)
        texts["phaseD-validation.md"] += (
            "\n\nUse `generate_scaffold(language='java', workflow='delete')` to delete.\n")
        self.assertTrue(route_citation_problems(texts))

    def test_the_old_module_3_marker_is_caught(self):
        text = read(MODULE_03)
        start = text.index(SCAFFOLD_MARKER)
        end = text.index("-->", start) + 3
        old = (SCAFFOLD_MARKER + " — its snippets[] carry file_path, source_url, repo, "
               "raw_url, size_bytes and line_count with no content field at all — owner: "
               "generate_scaffold IS the route that would return source text, and it returns a "
               "listing plus an ordered "
               "access_steps (fetch raw_url, else git clone) instead, so fetching raw_url is the "
               "documented route (routing negative) — server 1.36.0, 2026-09-02 -->")
        problems = module3_problems(text[:start] + old + text[end:])
        self.assertTrue(any("retired two-step route" in p for p in problems))
        self.assertTrue(any("stamped" in p for p in problems))

    def test_module_3_step_1a_without_the_route_is_caught(self):
        text = _replace(read(MODULE_03), ", fetching each file by the\nresponse's own "
                        "`access_steps`, as `../bootcamp-onboarding/ground-rules.md` → \"Follow "
                        "each\nresponse's own `access_steps`, in the order it gives them\" says "
                        "(INV-160, INV-300)", "")
        self.assertTrue(any("Step 1a" in p for p in module3_problems(text)))

    def test_the_old_teardown_wording_is_caught(self):
        close = read(TRUTHSET_CLOSE)
        start = close.index("**On \"no\" or \"not yet\":**")
        end = close.index("\n\n", start)
        old = ("**On \"no\" or \"not yet\":** leave the server running and the data in place, "
               "tell the bootcamper it is\nstill at its URL, and wait for their go-ahead. Do not "
               "re-ask on a loop.")
        viz = _replace(read(TRUTHSET_VIZ), "The record carries one `reason`, on `web_service` "
                       "alone;\n`web_page` takes none. ", "")
        problems = teardown_problems(close[:start] + old + close[end:], viz)
        self.assertEqual(3, len(problems), problems)

    def test_a_bare_midpoint_record_is_caught(self):
        phase_b = _replace(read(PHASE_B), ", at the\nkey path "
                           "`module_6_processing.midpoint_record`:", ":")
        discover = _replace(read(DISCOVER), "recorded as `module_6_processing.midpoint_record` in",
                            "recorded in")
        self.assertEqual(2, len(midpoint_problems(phase_b, discover)))

    def test_a_user_level_nuget_write_is_caught(self):
        text = _replace(read(MODULE_02), " --name\n        SenzingLocal --configfile nuget.config`",
                        " --name\n        SenzingLocal`")
        self.assertTrue(any("user-level" in p for p in nuget_problems(text)))

    def test_a_dropped_clear_disclosure_is_caught(self):
        text = _replace(read(MODULE_02), "the new\n     file starts with `<clear/>` and re-adds "
                        "nuget.org", "the new\n     file exists")
        self.assertTrue(nuget_problems(text))


if __name__ == "__main__":
    unittest.main()
