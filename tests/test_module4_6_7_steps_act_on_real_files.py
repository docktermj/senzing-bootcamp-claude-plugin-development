"""#810: Module 4's steps act on the Bootcamper's files, the engine fallback reads a value that
is written, and Module 7's snapshot is named and checked.

Five defects, one shape: a step acted on something that is not there.

- **Module 4 Step 3** ran `head -5` on the example names `customer_crm.csv` and
  `vendor_api.json`, which no Bootcamper has. It now runs on each registry `file_path` in
  `config/data_sources.yaml`.
- **Module 4 Step 4** created the data collection checklist and then guided the Bootcamper "to
  fill in one row per source and complete the checklist before Module 5", on a path that never
  stops for them, beside its own "no question (INV-012)". The guide now fills it from the
  registry and Step 3, and announces it in Step 9's "Files produced".
- **The engine fallback** at Module 4 Step 8b and Module 6 Phase A, for an absent
  `database_type`, read "the engine recorded by Module 2 in `config/bootcamp_progress.json`".
  Nothing writes one there. Module 2 Step 8 does write `SQL.CONNECTION` in
  `config/engine_config.json`, whose scheme names the engine.
- **Module 7 step 3c** wrote its snapshot "under `docs/visualizations/`" and never checked it,
  while `:1195` and `:1246` already called it `results_visualization.html` (INV-129).
- **Module 7's tab-order embed rule** restated INV-147's rule without citing it.

⛔ **Single statement (INV-300).** The engine fallback is stated once, at Phase A's SQLite
volume pre-load check, which already owns the SQLite threshold Step 8b defers to. Step 8b and
Module 2's reader list point at it and carry no copy of its scheme map. Module 7's snapshot check
points at Module 3b's (`phase2-close.md` → "Pre-advancement verification") and names only what
differs: the file and the Bootcamper's loaded data. So this guard asserts both halves of each
pointer: the pointing site names the owner, and the owner still says what the pointer relies
on. A copy pasted into the pointing site fails, because that is how two statements drift.

Every check is a pure function over text, so each negative control below runs the same check
over a mutated in-memory copy (INV-265: each control asserts its mutation applied).

⚠️ **What this does NOT establish:** that a live guide runs `head` on the right files, fills
the checklist faithfully, reads the scheme, or rebuilds a blank snapshot. Those are turn-level
behavior that only `dry-run` phase 3 observes (INV-108).

Stdlib only; shipped markdown read as text.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SKILLS = PLUGIN / "skills"
MODULE_02 = SKILLS / "module-02-sdk-setup" / "SKILL.md"
MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"
PHASE_A = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"
MODULE_07 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
CLOSE_3B = SKILLS / "module-03b-truthset-visualization" / "phase2-close.md"

STEP_3 = "### 3. Verify data was received"
STEP_4 = "### 4. Document data source locations"
STEP_8B = "### 8b. SQLite load-time warning"
STEP_3C = "### 3c. Visualization offer (single gate)"
REGISTRY_LEAD = "> **Data Source Registry:**"
PRE_LOAD_CHECK = "## SQLite volume pre-load check"
CHECKLIST_LEAD = "**Data Collection Checklist:**"

#: The one statement of the engine fallback, and the anchor its pointers link to.
FALLBACK_ANCHOR = "engine-fallback-from-the-connection-scheme"
FALLBACK_LEAD = "⛔ **An absent `database_type` is a recording failure"
STEP_8B_LEAD = "⛔ **If `database_type` is absent"
SOURCE = "`SQL.CONNECTION` in `config/engine_config.json`"
#: The scheme map: stated only at the owner. A pointer carrying it is a second copy.
SCHEMES = ("sqlite3://", "postgresql://")
#: The old fallback, in any wording: an engine read from the progress file.
PROGRESS_ENGINE = re.compile(
    r"engine\b[^.]{0,80}?`config/bootcamp_progress\.json`|"
    r"falls?\s+back\s+to\s+`config/bootcamp_progress\.json`")

SNAPSHOT = "docs/visualizations/results_visualization.html"
CHECK_ANCHOR = '<a id="snapshot-check"></a>'
CHECK_LEAD = "⛔ **(INV-129) Check the snapshot before handing it over.**"
HAND_OVER = "Your visualization is running at"
CLOSE_3B_SECTION = '"Pre-advancement verification"'
#: Module 3b's two checks Module 7 points at, by their bold lead, and the property each states.
CLOSE_3B_ITEMS = (
    ("The visualization artifact actually exists on disk", "is present and non-empty"),
    ("The snapshot reflects the loaded Truth Set, not an empty template", "non-empty record"),
)
#: Module 3b's own detail: a pointer that carries it has copied the rule.
CLOSE_3B_DETAIL = ("records_total", "truthset_verification.html", "build-only")
TAB_ORDER_LEAD = "Embed in the app's own tab order"


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    return re.sub(r"\s+", " ", text)


def section(text, heading):
    """The body under `heading`, up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    start = text.index(heading) + len(heading)
    stop = re.compile(r"^#{1,%d} " % level, re.M).search(text, start)
    return text[start:stop.start() if stop else len(text)]


def paragraph_at(text, needle):
    """The blank-line-delimited paragraph (or list item) holding `needle`."""
    at = text.index(needle)
    start = text.rfind("\n\n", 0, at)
    start = 0 if start < 0 else start + 2
    end = text.find("\n\n", at)
    return text[start:end if end >= 0 else len(text)]


def list_item_at(text, needle):
    """The list item holding `needle`: up to the next item at the same indent or a blank line."""
    at = text.index(needle)
    start = text.rfind("\n", 0, at) + 1
    while not re.match(r"\s*(?:-|\d+\.) ", text[start:]) and start > 0:
        start = text.rfind("\n", 0, start - 1) + 1
    indent = len(text[start:]) - len(text[start:].lstrip(" "))
    stop = re.compile(r"^ {0,%d}(?:-|\d+\.) |^\s*$" % indent, re.M).search(text, at)
    return text[start:stop.start() if stop else len(text)]


# --- Module 4 Step 3 ---------------------------------------------------------------------------

def step3_problems(module_04):
    step = section(module_04, STEP_3)
    blocks = re.findall(r"```bash\n(.*?)```", step, re.S)
    if len(blocks) != 1:
        return [f"Step 3 carries {len(blocks)} bash blocks, not one"]
    block = blocks[0]
    problems = []
    heads = re.findall(r"^head -5 (.+)$", block, re.M)
    if heads != ['"<file_path>"']:
        problems.append(f"Step 3's head lines are {heads!r}, not one on the `<file_path>` "
                        "placeholder")
    for example in ("customer_crm", "vendor_api"):
        if example in step:
            problems.append(f"Step 3 names the example file {example!r}")
    if re.search(r"data/raw/[\w.-]+\.\w+", block):
        problems.append("Step 3's block names a literal file under data/raw/")
    prose = flat(step.split("```bash", 1)[0])
    for needed in ("`config/data_sources.yaml`", "`file_path`", "once per source"):
        if needed not in prose:
            problems.append(f"Step 3 does not say to run it {needed!r}")
    if "[guide-run blocks]" not in step:
        problems.append("Step 3 lost its guide-run note")
    return problems


# --- Module 4 Step 4 ---------------------------------------------------------------------------

def registry_fields(module_04):
    """Every backticked field the Data Source Registry blockquote defines."""
    start = module_04.index(REGISTRY_LEAD)
    end = re.compile(r"^(?!>)", re.M).search(module_04, start).start()
    return set(re.findall(r"`([a-z_]+)`", module_04[start:end]))


def step4_problems(module_04):
    step = section(module_04, STEP_4)
    if CHECKLIST_LEAD not in step:
        return ["Step 4 has no Data Collection Checklist"]
    lead = step.index(CHECKLIST_LEAD)
    stop = step.index("Also create or update", lead)
    checklist = step[lead:stop]
    text = flat(checklist)
    problems = []
    if "`docs/data_collection_checklist.md`" not in text:
        problems.append("Step 4 does not name docs/data_collection_checklist.md")
    if "no question (INV-012)" not in text:
        problems.append("Step 4 no longer says the checklist takes no question (INV-012)")
    if re.search(r"(?i)bootcamper to (?:fill|complete)|complete the checklist before", text):
        problems.append("Step 4 asks the Bootcamper to fill in or complete the checklist")
    if re.search(r"👉|\?", checklist):
        problems.append("Step 4's checklist paragraph asks a question")
    if not re.search(r"(?i)fill it\s+in yourself|filled from", text):
        problems.append("Step 4 does not say the guide fills the checklist")
    if "Bootcamper fills in nothing" not in text:
        problems.append("Step 4 does not say the Bootcamper fills in nothing")
    if "`config/data_sources.yaml`" not in text:
        problems.append("Step 4 does not fill the checklist from the registry")
    if "Step 3" not in text:
        problems.append("Step 4's Validation Checklist is not filled from Step 3")
    named = set(re.findall(r"`([a-z_]+)`", checklist))
    for field in ("file_path", "record_count", "validation_status", "validation_checks"):
        if field not in named:
            problems.append(f"Step 4 does not fill from the registry's {field!r}")
    defined = registry_fields(module_04)
    for field in sorted(named - defined):
        problems.append(f"Step 4 names `{field}`, which Module 4's registry does not define")
    if not re.search(r'Step 9 end-of-module summary\'s "Files produced"', text):
        problems.append("Step 4 does not announce the file in Step 9's \"Files produced\"")
    return problems


# --- The engine fallback -----------------------------------------------------------------------

def engine_fallback_problems(module_02, module_04, phase_a):
    problems = []
    check = section(phase_a, PRE_LOAD_CHECK)
    if f'<a id="{FALLBACK_ANCHOR}"></a>' not in check:
        problems.append("Phase A's pre-load check lost the engine fallback's anchor")
    if FALLBACK_LEAD not in check:
        return problems + ["Phase A's pre-load check lost its absent-database_type rule"]
    owner = flat(list_item_at(check, FALLBACK_LEAD))
    if SOURCE not in owner:
        problems.append("Phase A's fallback does not read SQL.CONNECTION in engine_config.json")
    for scheme in SCHEMES:
        if f"`{scheme}`" not in owner:
            problems.append(f"Phase A's fallback does not map the scheme {scheme}")
    if "module-02-sdk-setup/SKILL.md` Step 8 writes" not in owner:
        problems.append("Phase A's fallback does not name the step that writes the file")
    if not re.search(r"stated once, here.*INV-300", owner):
        problems.append("Phase A's fallback does not claim the single statement (INV-300)")
    if "bootcamp_progress.json" in owner:
        problems.append("Phase A's fallback still reads the progress file")

    step = section(module_04, STEP_8B)
    if STEP_8B_LEAD not in step:
        return problems + ["Step 8b lost its absent-database_type rule"]
    pointer = flat(list_item_at(step, STEP_8B_LEAD))
    if f"phaseA-build-loading.md#{FALLBACK_ANCHOR})" not in pointer:
        problems.append("Step 8b does not link Phase A's engine fallback")
    if SOURCE not in pointer:
        problems.append("Step 8b does not fall back to SQL.CONNECTION in engine_config.json")
    if "INV-300" not in pointer:
        problems.append("Step 8b's pointer does not cite INV-300")
    if "bootcamp_progress.json" in pointer:
        problems.append("Step 8b still reads an engine from the progress file")
    for scheme in SCHEMES:
        if scheme in pointer:
            problems.append(f"Step 8b restates the scheme map ({scheme}) instead of pointing")

    for reader in ("**Step 8b**, the SQLite load-time", "**SQLite volume pre-load check**"):
        if reader not in module_02:
            problems.append(f"Module 2's reader list lost {reader!r}")
            continue
        item = flat(list_item_at(module_02, reader))
        if SOURCE not in item or "bootcamp_progress.json" in item:
            problems.append(f"Module 2 describes {reader!r} with the wrong fallback")

    step8 = section(module_02, "## Step 8: Create Engine Configuration")
    if "`config/engine_config.json`" not in step8 or "`SQL.CONNECTION`" not in step8:
        problems.append("Module 2 Step 8 no longer writes SQL.CONNECTION in engine_config.json; "
                        "the fallback reads a value nothing writes")
    for scheme in SCHEMES:
        if scheme not in module_02:
            problems.append(f"Module 2 no longer writes a {scheme} connection")
    return problems


def progress_file_engine_reads(files):
    """Every shipped sentence that takes an engine from config/bootcamp_progress.json."""
    hits = []
    for path, text in files:
        for m in PROGRESS_ENGINE.finditer(flat(text)):
            hits.append(f"{path}: ...{m.group(0)[:100]}...")
    return hits


def shipped_markdown():
    return [(str(p.relative_to(REPO_ROOT)), read(p)) for p in sorted(PLUGIN.rglob("*.md"))]


# --- Module 7 ----------------------------------------------------------------------------------

def snapshot_problems(module_07, close_3b):
    step = section(module_07, STEP_3C)
    problems = []
    if f"standalone HTML snapshot to\n  `{SNAPSHOT}`" not in step:
        problems.append("step 3c does not name the snapshot file where it writes it")
    if "docs/visualizations/<file>.html" in step:
        problems.append("step 3c's checkpoint still names a placeholder file")
    if CHECK_LEAD not in step:
        return problems + ["step 3c does not check the snapshot before the hand-over"]
    check = paragraph_at(step, CHECK_LEAD)
    text = flat(check)
    if CHECK_ANCHOR not in check:
        problems.append("the snapshot check lost its anchor")
    if step.index(CHECK_LEAD) > step.index(HAND_OVER):
        problems.append("the snapshot check comes after the hand-over")
    if "](#snapshot-check)" not in step[:step.index(CHECK_LEAD)]:
        problems.append("the no-live-server branch keeps the snapshot without the check")
    if not ("phase2-close.md` →" in text and CLOSE_3B_SECTION in text and "INV-300" in text):
        problems.append("the check does not point at Module 3b's pre-advancement "
                        "verification (INV-300)")
    if f"`{SNAPSHOT}`" not in text:
        problems.append("the check does not name the file it checks")
    if "loaded data" not in text:
        problems.append("the check does not name the Bootcamper's loaded data")
    for detail in CLOSE_3B_DETAIL:
        if detail in text:
            problems.append(f"the check restates Module 3b's detail {detail!r}")
    if "👉" in check:
        problems.append("the check asks the Bootcamper a question")
    owner = flat(close_3b)
    if "Pre-advancement verification" not in owner:
        problems.append("Module 3b's pre-advancement verification is gone")
    for item, states in CLOSE_3B_ITEMS:
        if f'"{item}"' not in text:
            problems.append(f"the check does not name Module 3b's item {item!r}")
        lead = f"**{item}"
        if lead not in owner:
            problems.append(f"Module 3b no longer has the item {item!r}")
            continue
        body = owner[owner.index(lead):][:600]
        if states not in body:
            problems.append(f"Module 3b's item {item!r} no longer says {states!r}")
    return problems


def tab_order_problems(module_07):
    lines = [ln for ln in module_07.splitlines() if TAB_ORDER_LEAD in ln and "⛔" in ln]
    if len(lines) != 1:
        return [f"Module 7 has {len(lines)} tab-order embed rules, not one"]
    if "⛔ **(INV-147)" not in lines[0]:
        return ["Module 7's tab-order embed rule does not cite INV-147 at its line"]
    return []


# --- Tests -------------------------------------------------------------------------------------

class TheStepsActOnRealFilesAndValues(unittest.TestCase):
    def setUp(self):
        self.m02, self.m04 = read(MODULE_02), read(MODULE_04)
        self.phase_a, self.m07, self.close = read(PHASE_A), read(MODULE_07), read(CLOSE_3B)

    def test_step_3_runs_on_each_registry_file_path(self):
        self.assertEqual(step3_problems(self.m04), [])

    def test_step_4_is_filled_by_the_guide_and_asks_nothing(self):
        self.assertEqual(step4_problems(self.m04), [])

    def test_the_registry_definition_is_read(self):
        """INV-265: an empty field set would let every Step 4 name pass the subset check."""
        fields = registry_fields(self.m04)
        for field in ("name", "file_path", "record_count", "validation_status",
                      "validation_checks"):
            self.assertIn(field, fields)

    def test_the_engine_fallback_is_stated_once_and_pointed_at(self):
        self.assertEqual(engine_fallback_problems(self.m02, self.m04, self.phase_a), [])

    def test_no_shipped_file_takes_an_engine_from_the_progress_file(self):
        files = shipped_markdown()
        self.assertGreater(len(files), 30, "the scan reached too few files")
        self.assertIn(str(MODULE_04.relative_to(REPO_ROOT)), [path for path, _ in files])
        self.assertEqual(progress_file_engine_reads(files), [])

    def test_module_7_names_and_checks_its_snapshot(self):
        self.assertEqual(snapshot_problems(self.m07, self.close), [])

    def test_module_7_tab_order_rule_cites_inv_147(self):
        self.assertEqual(tab_order_problems(self.m07), [])


class NegativeControls(unittest.TestCase):
    """Each control restores a shipped defect, or a second copy, in an in-memory copy."""

    def setUp(self):
        self.m02, self.m04 = read(MODULE_02), read(MODULE_04)
        self.phase_a, self.m07, self.close = read(PHASE_A), read(MODULE_07), read(CLOSE_3B)

    def mutate(self, text, old, new):
        self.assertIn(old, text, "control did not apply")
        return text.replace(old, new, 1)

    def test_the_old_step_3_block_fails(self):
        broken = self.mutate(self.m04, 'head -5 "<file_path>"\n',
                             "head -5 data/raw/customer_crm.csv\n"
                             "head -5 data/raw/vendor_api.json\n")
        problems = step3_problems(broken)
        self.assertTrue(any("customer_crm" in p for p in problems), problems)
        self.assertTrue(any("literal file" in p for p in problems), problems)

    def test_the_old_step_4_instruction_fails(self):
        broken = self.mutate(
            self.m04, "The Bootcamper fills in nothing and is asked nothing about it.",
            "Guide the bootcamper to fill in one row per source and complete the checklist "
            "before Module 5.")
        problems = step4_problems(broken)
        self.assertTrue(any("asks the Bootcamper to fill" in p for p in problems), problems)
        self.assertTrue(any("fills in nothing" in p for p in problems), problems)

    def test_a_step_4_field_the_registry_does_not_define_fails(self):
        broken = self.mutate(self.m04, "`format` and `record_count`;",
                             "`format` and `row_total`;")
        problems = step4_problems(broken)
        self.assertTrue(any("`row_total`" in p for p in problems), problems)

    def test_a_step_4_without_files_produced_fails(self):
        broken = self.mutate(self.m04, "the Step 9 end-of-module summary's \"Files produced\" "
                                       "list (INV-032).", "the recap (INV-032).")
        self.assertTrue(any("Files produced" in p for p in step4_problems(broken)))

    def test_the_old_step_8b_fallback_fails(self):
        start = self.m04.index("     fall back to the scheme of `SQL.CONNECTION`")
        end = self.m04.index("(INV-300).", start) + len("(INV-300).")
        broken = (self.m04[:start] + "     fall back to the engine recorded by Module 2 in "
                  "`config/bootcamp_progress.json` before giving\n     up on the check."
                  + self.m04[end:])
        problems = engine_fallback_problems(self.m02, broken, self.phase_a)
        self.assertTrue(any("progress file" in p for p in problems), problems)
        self.assertTrue(any("does not link" in p for p in problems), problems)
        self.assertTrue(progress_file_engine_reads([("module-04", broken)]))

    def test_the_old_phase_a_fallback_fails(self):
        start = self.phase_a.index("take the engine from the scheme of")
        end = self.phase_a.index("Note the gap internally", start)
        broken = (self.phase_a[:start] + "fall back to the engine Module 2\n     recorded in "
                  "`config/bootcamp_progress.json`, and " + self.phase_a[end:])
        problems = engine_fallback_problems(self.m02, self.m04, broken)
        self.assertTrue(any("progress file" in p for p in problems), problems)
        self.assertTrue(any("SQL.CONNECTION" in p for p in problems), problems)
        self.assertTrue(progress_file_engine_reads([("phaseA", broken)]))

    def test_a_scheme_map_copied_into_step_8b_fails(self):
        broken = self.mutate(self.m04, "which is stated once there (INV-300).",
                             "which is stated once there (INV-300): `sqlite3://` is SQLite.")
        problems = engine_fallback_problems(self.m02, broken, self.phase_a)
        self.assertTrue(any("restates the scheme map" in p for p in problems), problems)

    def test_the_old_module_2_reader_list_fails(self):
        broken = self.mutate(
            self.m02, "falls back to the scheme of `SQL.CONNECTION` in\n     "
                      "`config/engine_config.json`, by Module 6's engine fallback below.",
            "falls back to the engine recorded in\n     `config/bootcamp_progress.json`.")
        problems = engine_fallback_problems(broken, self.m04, self.phase_a)
        self.assertTrue(any("wrong fallback" in p for p in problems), problems)

    def test_a_dropped_anchor_fails(self):
        broken = self.mutate(self.phase_a, f'<a id="{FALLBACK_ANCHOR}"></a>', "")
        problems = engine_fallback_problems(self.m02, self.m04, broken)
        self.assertTrue(any("anchor" in p for p in problems), problems)

    def test_a_removed_snapshot_check_fails(self):
        check = paragraph_at(self.m07, CHECK_LEAD)
        broken = self.mutate(self.m07, check + "\n\n", "")
        problems = snapshot_problems(broken, self.close)
        self.assertTrue(any("does not check the snapshot" in p for p in problems), problems)

    def test_an_unnamed_snapshot_fails(self):
        broken = self.mutate(self.m07, f"standalone HTML snapshot to\n  `{SNAPSHOT}` (INV-070)",
                             "standalone HTML snapshot under `docs/visualizations/` (INV-070)")
        problems = snapshot_problems(broken, self.close)
        self.assertTrue(any("does not name the snapshot file" in p for p in problems), problems)

    def test_a_check_after_the_hand_over_fails(self):
        check = paragraph_at(self.m07, CHECK_LEAD)
        moved = self.mutate(self.m07, check + "\n\n", "")
        at = moved.index("Let them explore at their own pace")
        moved = moved[:at] + check + "\n\n" + moved[at:]
        problems = snapshot_problems(moved, self.close)
        self.assertTrue(any("after the hand-over" in p for p in problems), problems)

    def test_a_copied_module_3b_check_fails(self):
        broken = self.mutate(self.m07, "not the Truth Set. If either fails",
                             "not the Truth Set, with `records_total > 0`. If either fails")
        problems = snapshot_problems(broken, self.close)
        self.assertTrue(any("restates" in p for p in problems), problems)

    def test_a_renamed_module_3b_item_fails(self):
        broken = self.mutate(self.close, "**The visualization artifact actually exists on disk",
                             "**The artifact is on disk")
        problems = snapshot_problems(self.m07, broken)
        self.assertTrue(any("no longer has the item" in p for p in problems), problems)

    def test_an_uncited_tab_order_rule_fails(self):
        broken = self.mutate(self.m07, "⛔ **(INV-147) Embed in", "⛔ **Embed in")
        self.assertEqual(len(tab_order_problems(broken)), 1)


if __name__ == "__main__":
    unittest.main()
