"""Data collection Step 8b's decision marker has a location, and Module 6 matches it one way (#345).

Step 8b ends its SQLite load-time warning with "Record the decision": it wrote "a load-decision
marker capturing the choice … keyed to the collected dataset identity", with no file, key or
fields. Module 6 read it under two other names, neither of which said where to look: Phase A's
SQLite volume pre-load check, item 2, skipped its prompt when "an applicable Module 4 SQLite
load-time decision covers this same load", and Phase B Step 7 read "the Module 4 Step 8b load
decision". So whether Module 6 found the decision depended on what the guide happened to write,
and a marker keyed to the collected dataset could not be matched against the load Module 6 is
about to run (INV-006).

The two loadable totals are not the same figure, so they cannot be compared directly. Step 8b's
is `min(collected_total, effective_limit)`, from the registry and the license state, before
mapping. Module 6's item 1 counts the mapped files in `data/senzing-ready/` with no license cap,
and mapping can raise that count (embedded masters turned 3,488 input records into 3,727).

The fix gives the marker a name, `sqlite_load_time_prompt`, a file and fields, and makes Module 6
recompute Step 8b's formula from the current registry and license state and match on the
recorded `loadable`. Five checks, each a pure function over the text, so every negative control
runs the same check over a mutated copy, and the pre-#345 wording (kept below as fixtures) fails
them:

1. Step 8b sub-step 4 names the marker, its file and its five fields, defines each field, cites
   item 2 for the matching rule, and no longer keys the marker to the collected dataset.
2. Item 2 states the matching rule: recompute by sub-step 1's rules, match on `loadable`, a
   marker with no `loadable` does not match, and an unreadable registry or license state is
   indeterminate, so the marker does not match. That last clause overrides sub-step 1's
   "treat an unreadable license state as unbounded", and says so.
3. Item 2 maps each Step 8b choice onto Module 6's behavior, and an absent marker is "not asked"
   (INV-244).
4. Phase B Step 7 names the marker and cites item 2 rather than restating the rule (INV-300).
5. No skill names the old, undefined decision, and every link the fix adds resolves.

Everything is asserted as behavior in shipped guidance, so any implementation language
satisfies it (INV-002). The checks pin the text and cannot observe a live prompt.

Source: GitHub issue #345.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"
MODULE_06 = SKILLS / "module-06-data-processing"
PHASE_A = MODULE_06 / "phaseA-build-loading.md"
PHASE_B = MODULE_06 / "phaseB-load-first-source.md"

MARKER = "`sqlite_load_time_prompt`"
PREFERENCES = "`config/bootcamp_preferences.yaml`"
FIELDS = "`{decided: true, choice, loadable, collected_total, effective_limit}`"
FORMULA = "`min(collected_total, effective_limit)`"

STEP_8B_HEADING = "### 8b. SQLite load-time warning (collection-time heads-up)"
SUB_STEP_4 = "4. **Record the decision.**"
STEP_8B_END = "Refer to the Senzing MCP server by name only"
PHASE_A_SECTION = "## SQLite volume pre-load check"
ITEM_2 = "2. **Decide whether it was already decided.**"
ITEM_3 = "3. **Prompt only when it matters.**"
STEP_7_NOTE = "**⚠️ SQLite performance note"
STEP_7_GATE = "Only when the database is SQLite"

PHASE_A_FRAGMENT = "sqlite-volume-pre-load-check-stop-and-confirm-heads-up-not-a-mandatory-gate"
STEP_8B_FRAGMENT = "8b-sqlite-load-time-warning-collection-time-heads-up"

#: The old names for the decision, which said nothing about where it lives.
OLD_NAMES = re.compile(r"applicable Module 4|Step 8b load decision")


def read(path):
    return path.read_text(encoding="utf-8")


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def section(text, start_marker, end_marker):
    start = text.index(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    return text[start:] if end < 0 else text[start:end]


def sub_step_4(module_04_text):
    return section(section(module_04_text, STEP_8B_HEADING, "\n### 9. "), SUB_STEP_4,
                   STEP_8B_END)


def item_2(phase_a_text):
    return section(section(phase_a_text, PHASE_A_SECTION, "\n## "), ITEM_2, ITEM_3)


def step_7_check(phase_b_text):
    """Phase B Step 7's already-decided paragraph, up to the start-smaller gate."""
    return section(section(phase_b_text, STEP_7_NOTE, "**Checkpoint:** write step 7."),
                   "Check first whether this was already decided", STEP_7_GATE)


def choice_bullet(item, choice):
    """The bullet in item 2 that maps one Step 8b choice, flattened; empty if there is none."""
    text = flat(item)
    at = text.find(f"- `{choice}`:")
    if at < 0:
        return ""
    ends = [i for i in (text.find(" - `", at + 1), text.find(" 4. **", at + 1)) if i > 0]
    return text[at:min(ends)] if ends else text[at:]


def github_slug(heading):
    """The fragment GitHub generates for a Markdown heading."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def fragments(text):
    return {github_slug(m.group(1)) for m in re.finditer(r"(?m)^#{1,6} (.+)$", text)}


def marker_problems(step):
    """Check 1: sub-step 4 defines the marker's key, file and fields, and cites item 2."""
    text = flat(step)
    problems = []
    if re.search(r"(?i)collected dataset identity", text):
        problems.append('sub-step 4 still keys the marker "to the collected dataset identity"')
    if MARKER not in text:
        problems.append("sub-step 4 does not name sqlite_load_time_prompt")
    if PREFERENCES not in text:
        problems.append("sub-step 4 does not name config/bootcamp_preferences.yaml")
    if FIELDS not in text:
        problems.append(f"sub-step 4 does not give the fields {FIELDS}")
    if "`choice` is `proceed`, `sample` or `switch_db`" not in text:
        problems.append("sub-step 4 does not give choice's three values")
    if not re.search(r"`collected_total` is the registry total the formula used: each "
                     r"source's `sample:` `record_count` where .*?otherwise its `record_count`",
                     text):
        problems.append("sub-step 4 does not define collected_total from the sample: block")
    if not re.search(r"`effective_limit` is the limit sub-step 1 resolved, `0` when unbounded",
                     text):
        problems.append("sub-step 4 does not define effective_limit, 0 when unbounded")
    if f"`loadable` is {FORMULA}, with `0` read as unbounded" not in text:
        problems.append("sub-step 4 does not define loadable as the formula")
    if not re.search(r"item 2 of Module 6 Phase A's", text):
        problems.append("sub-step 4 does not cite item 2 for the matching rule")
    if f"#{PHASE_A_FRAGMENT})" not in text:
        problems.append("sub-step 4 does not link Phase A's SQLite volume pre-load check")
    return problems


def matching_problems(item):
    """Check 2: item 2 states the matching rule, including the indeterminate case."""
    text = flat(item)
    problems = []
    if MARKER not in text:
        problems.append("item 2 does not name sqlite_load_time_prompt")
    if f"Recompute {FORMULA} from the current `config/data_sources.yaml` and license state by " \
       "Step 8b sub-step 1's rules" not in text:
        problems.append("item 2 does not recompute Step 8b's formula from the current registry "
                        "and license state by sub-step 1's rules")
    if "only when that figure equals its `loadable`" not in text:
        problems.append("item 2 does not match on the marker's loadable")
    if text.count("A marker with no `loadable` does not match") < 1:
        problems.append("item 2 does not say a Module 4 marker with no loadable does not match")
    if "the recomputation reads the registry and not `data/senzing-ready/`" not in text:
        problems.append("item 2 does not say why mapping does not affect the match")
    if not re.search(r"An unreadable registry or license state is indeterminate, so the marker "
                     r"does not match", text):
        problems.append("item 2 does not make an unreadable registry or license state "
                        "indeterminate")
    if not re.search(r'overrides Step 8b sub-step 1\'s "treat an unreadable license state as '
                     r'unbounded"', text):
        problems.append("item 2 does not say it overrides sub-step 1's unbounded fallback")
    if not re.search(r"one statement of how Module 6 matches it; Phase B Step 7 cites them "
                     r"\(INV-300\)", text):
        problems.append("item 2 does not declare itself the one statement of the rule")
    if f"#{STEP_8B_FRAGMENT})" not in text:
        problems.append("item 2 does not link data collection Step 8b")
    return problems


def mapping_problems(item):
    """Check 3: item 2 maps each Step 8b choice, and an absent marker is not an answer."""
    problems = []
    proceed = choice_bullet(item, "proceed")
    if not proceed:
        problems.append("item 2 does not map proceed")
    else:
        if "**Proceed on SQLite**" not in proceed:
            problems.append("proceed is not mapped onto this check's own Proceed on SQLite")
        if "serialized-writer line (INV-296)" not in proceed:
            problems.append("proceed does not keep the INV-296 serialized-writer line")
        if "applying the writer reduction if step 3 did not" not in proceed:
            problems.append("proceed does not apply the writer reduction step 3 missed")
    sample = choice_bullet(item, "sample")
    if not sample:
        problems.append("item 2 does not map sample")
    elif not sample.startswith("- `sample`: covers the load"):
        problems.append("sample does not cover the load")
    switch = choice_bullet(item, "switch_db")
    if not switch:
        problems.append("item 2 does not map switch_db")
    else:
        if "only when `database_type` is no longer `sqlite`" not in switch:
            problems.append("switch_db is not conditional on database_type leaving sqlite")
        if "the switch chosen at data collection was not applied" not in switch:
            problems.append("switch_db on sqlite does not say the switch was not applied")
        if "evaluate the load on item 3's trigger" not in switch:
            problems.append("switch_db on sqlite does not hand the load to item 3")
    if 'An absent marker is "not asked", never "answered" (INV-244)' not in flat(item):
        problems.append("item 2 does not say an absent Module 4 marker is not an answer")
    return problems


def phase_b_problems(check):
    """Check 4: Step 7 names the marker and cites item 2 without restating the rule."""
    text = flat(check)
    problems = []
    if OLD_NAMES.search(text):
        problems.append('Step 7 still reads "the Module 4 Step 8b load decision"')
    if MARKER not in text:
        problems.append("Step 7 does not name sqlite_load_time_prompt")
    if not re.search(r"covers this load only as item 2 of Phase A's \[pre-load check\]\("
                     r"phaseA-build-loading\.md#" + PHASE_A_FRAGMENT + r"\) matches it "
                     r"\(INV-300\)", text):
        problems.append("Step 7 does not cite item 2 of Phase A's pre-load check by link")
    for restated in ("collected_total", "effective_limit", "min(", "Recompute"):
        if restated in text:
            problems.append(f"Step 7 restates the matching rule ({restated!r})")
    return problems


#: The pre-#345 wording, kept so the negative controls test the shape the issue reported.
PRE_FIX_SUB_STEP_4 = """4. **Record the decision.** Write a load-decision marker capturing the choice
   (`proceed`, `sample`, or `switch_db`) keyed to the collected dataset identity, so the
   Module 6 SQLite heads-up does not redundantly re-ask about this same load.

"""
PRE_FIX_ITEM_2 = """2. **Decide whether it was already decided.** If a `sqlite_volume_prompt` marker in preferences
   is `decided: true` and its `loadable` matches the current loadable total for this same load (or
   an applicable Module 4 SQLite load-time decision covers this same load), skip the prompt and
   proceed. (INV-331) `tier`/`raw_value` do not decide the match; a marker with no `loadable` (written before
   the field existed) does not match, so re-evaluate on the loadable total.
"""
PRE_FIX_STEP_7 = """Check first whether this was already decided, and say nothing if it was.** Read the
`sqlite_volume_prompt` marker in `config/bootcamp_preferences.yaml` (Phase A's pre-load check) and
the Module 4 Step 8b load decision. If either records a choice for this same load — `proceed`,
`subset`, `sample`, or a database switch — **honor it silently and load what it says**.

"""


class TheMarkerIsDefinedAndMatched(unittest.TestCase):

    def setUp(self):
        self.module_04 = read(MODULE_04)
        self.phase_a = read(PHASE_A)
        self.phase_b = read(PHASE_B)
        self.sub_step = sub_step_4(self.module_04)
        self.item = item_2(self.phase_a)

    def test_sub_step_4_defines_the_marker(self):
        self.assertEqual(marker_problems(self.sub_step), [])

    def test_item_2_states_the_matching_rule(self):
        self.assertEqual(matching_problems(self.item), [])

    def test_item_2_maps_each_choice(self):
        self.assertEqual(mapping_problems(self.item), [])

    def test_phase_b_step_7_cites_item_2(self):
        self.assertEqual(phase_b_problems(step_7_check(self.phase_b)), [])

    def test_no_skill_names_the_old_decision(self):
        hits = [f"{p.relative_to(SKILLS)}:{n}"
                for p in sorted(SKILLS.rglob("*.md"))
                for n, line in enumerate(read(p).splitlines(), 1)
                if OLD_NAMES.search(line)]
        self.assertEqual(hits, [])

    def test_the_links_resolve(self):
        self.assertIn(PHASE_A_FRAGMENT, fragments(self.phase_a))
        self.assertIn(STEP_8B_FRAGMENT, fragments(self.module_04))
        self.assertEqual(github_slug(STEP_8B_HEADING.lstrip("# ")), STEP_8B_FRAGMENT)

    def test_the_marker_is_defined_once(self):
        """INV-300: the fields are given at Step 8b only; item 2 points there for them."""
        homes = [p.relative_to(SKILLS).as_posix() for p in sorted(SKILLS.rglob("*.md"))
                 if FIELDS in flat(read(p))]
        self.assertEqual(homes, ["module-04-data-collection/SKILL.md"])
        self.assertIn("sub-step 4, which gives its fields", flat(self.item))


class NegativeControls(unittest.TestCase):
    """Each mutation restores a shape the guard exists to catch."""

    def setUp(self):
        self.sub_step = sub_step_4(read(MODULE_04))
        self.item = item_2(read(PHASE_A))
        self.check = step_7_check(read(PHASE_B))

    def mutate(self, source, old, new):
        changed = source.replace(old, new, 1)
        self.assertTrue(changed != source, f"control did not apply: {old[:60]!r}")
        return changed

    def test_the_pre_fix_sub_step_4_fails(self):
        problems = marker_problems(PRE_FIX_SUB_STEP_4)
        self.assertTrue(any("collected dataset identity" in p for p in problems), problems)
        self.assertTrue(any("does not name sqlite_load_time_prompt" in p for p in problems))
        self.assertTrue(any("fields" in p for p in problems), problems)

    def test_the_pre_fix_item_2_fails(self):
        problems = matching_problems(PRE_FIX_ITEM_2) + mapping_problems(PRE_FIX_ITEM_2)
        self.assertTrue(any("does not name sqlite_load_time_prompt" in p for p in problems))
        self.assertTrue(any("recompute" in p for p in problems), problems)
        self.assertTrue(any("indeterminate" in p for p in problems), problems)
        for choice in ("proceed", "sample", "switch_db"):
            self.assertTrue(any(f"does not map {choice}" in p for p in problems), problems)

    def test_the_pre_fix_step_7_fails(self):
        problems = phase_b_problems(PRE_FIX_STEP_7)
        self.assertTrue(any("Step 8b load decision" in p for p in problems), problems)
        self.assertTrue(any("cite item 2" in p for p in problems), problems)

    def test_a_dropped_field_fails(self):
        broken = self.mutate(self.sub_step, ", collected_total, effective_limit}`", "}`")
        self.assertTrue(any("fields" in p for p in marker_problems(broken)))

    def test_an_unbounded_fallback_fails(self):
        """The indeterminate exception is the rule's point: restoring the fallback fails."""
        start = self.item.index("   2. **An unreadable registry")
        end = self.item.index("   3. **A matching marker")
        broken = self.mutate(self.item, self.item[start:end],
                             "   2. **Treat an unreadable license state as unbounded.**\n")
        problems = matching_problems(broken)
        self.assertTrue(any("indeterminate" in p for p in problems), problems)
        self.assertTrue(any("overrides" in p for p in problems), problems)

    def test_matching_on_the_mapped_total_fails(self):
        broken = self.mutate(self.item, "only when that figure equals its `loadable`",
                             "only when item 1's loadable total equals its `loadable`")
        self.assertTrue(any("loadable" in p for p in matching_problems(broken)))

    def test_an_unconditional_switch_fails(self):
        broken = self.mutate(self.item, "covers the load only when `database_type` is no longer "
                             "`sqlite`", "covers the load")
        self.assertTrue(any("conditional" in p for p in mapping_problems(broken)))

    def test_a_proceed_without_the_writer_line_fails(self):
        broken = self.mutate(self.item, "serialized-writer line (INV-296)", "line")
        self.assertTrue(any("INV-296" in p for p in mapping_problems(broken)))

    def test_step_7_restating_the_rule_fails(self):
        broken = self.mutate(self.check, "matches it (INV-300).",
                             "matches it (INV-300): recompute `min(collected_total, "
                             "effective_limit)` and compare it with `loadable`.")
        problems = phase_b_problems(broken)
        self.assertTrue(any("restates" in p for p in problems), problems)

    def test_a_dangling_fragment_fails(self):
        broken = self.mutate(self.item, f"#{STEP_8B_FRAGMENT})", "#8b-sqlite-load-time-warning)")
        self.assertTrue(any("link" in p for p in matching_problems(broken)))


if __name__ == "__main__":
    unittest.main()
