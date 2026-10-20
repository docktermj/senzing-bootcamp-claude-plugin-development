"""Every value a data-source registry status field documents is handled by the step that reads it.

Enforces **INV-391**, registered by the maintainer 2026-10-20: a step reading a registry status
field states what it does with every documented value, including the one the schema writes at
creation. ⚠️ It reads the shipped step prose; it **cannot** establish that a live run takes the
branch it states.

Module 4's registry schema documents `validation_status` as `pending` | `passed` | `failed`, and
writes `pending` at creation. Step 7 — the step the schema itself names as the field's reader —
said only *"Confirm every source shows `validation_status: passed`. If any source shows
`validation_status: failed`, revisit that data source and resolve the failing checks"*. It
confirmed one terminal value, remedied one other, and said nothing about the third.

⛔ **The third value is reachable by design, not by accident.** Option B's inaccessible branch
("requires credentials, VPN, etc.") documents the access method and downloads nothing, and the
Data File Validation step runs only *"After each file is saved to `data/raw/`"* — so a
documented-location-only source keeps the `pending` the schema wrote at creation forever. The same
module blesses that outcome twice: the Success indicator accepts "files in `data/raw/` OR
documented locations", and the schema's own `record_count` note says null is right "when no file
was collected, e.g. a documented-location-only source". Graduation's registry projection agrees a
third time, omitting "a source whose `file_path` is null, such as a documented-location-only
source". Step 7 was the outlier, so Step 7 is what moved: a step contradicting its own module,
the same shape as a gate option with no handling step (#504, INV-284).

**What is derived, and from where (INV-246).** Neither half is written into this test:

* The **status fields** come from the registry schema block's own creation sentence — every
  ``field_name: value`` it writes whose name ends in `_status`. No field list is hardcoded.
* Their **value sets** come from the same block's value-set statements,
  ``` `field` (`a` | `b` | `c`) ```, read wrap-aware (INV-346) because the `mapping_status` set is
  wrapped in the shipped file and a line-at-a-time read sees only half of it.
* The **reader** comes from the schema's own sentence naming it — *"read back by Step 7"*. The
  schema states the contract (*"Step 7 cannot confirm what this entry never recorded"*), so the
  step that must be complete is the one the schema points at, found by scanning rather than named
  here.
* The **handling** comes from the shipped step's prose: the value must be named beside the field,
  in one Markdown block of that step's section.

**Scope, with its reason (INV-282).** This sweeps the **data-source registry in
`module-04-data-collection/SKILL.md`** and no other status-shaped field in the plugin.

* A field whose reader is **not** a step of this module is out of scope, and the test asserts that
  no step of this module names it outside the schema block, so the exclusion is verified rather
  than assumed. `mapping_status` is the live case: Module 5 and later write and read it, and the
  schema's own note (INV-300) says every step that reads it "points here and states only what it
  does with it" — a step that deliberately acts on one value is **correct prose**, and a guard
  that reported it would be waived. Requiring each of those readers to speak for every value is a
  decision about what the flow should do, not a missing branch, and this guard does not make it.
* A field the schema writes but documents **no** value set for is out of scope for the same
  reason in reverse: there is no documented set to be complete against. `load_status` is that
  case here — this module writes `not_loaded` and Module 6 owns the rest. If either field later
  gains a reader step in this module, or `load_status` gains a documented set beside a reader,
  this guard fails and asks for the handling rather than staying silent.

**What this cannot establish (INV-308).** It establishes that the reading step **names** each
documented value beside the field. It does not establish that the handling is right, that a live
guide follows it, or that the documented set is the correct set — only `dry-run` phase 3 can
observe the first two, and the value set is the module's own decision. A step that handles a value
without naming it is invisible here, which is deliberate: an unnamed branch is one a reader cannot
follow either.

Enforces the reader side of INV-039 (the collected sources are the ones later modules work from),
with the sites derived on every run (INV-246), the prose read across line wraps (INV-346) and the
scan asserted non-empty (INV-265).

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Source issue: #687.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from collections import namedtuple

from _corpus import REPO_ROOT, corpus_files
from _wrapped_text import collapsed_blocks, line_of

#: The module whose registry this sweeps, by its last two path segments. The file is reached
#: through the corpus listing, never by a hand-built path, so a move or a rename fails here.
MODULE_TAIL = ("module-04-data-collection", "SKILL.md")

#: The registry schema block opens with this bold label, inside a blockquote.
REGISTRY_OPENER = "**Data Source Registry:**"

#: A status field the schema writes at creation: `` `mapping_status: pending` ``. The `_status`
#: suffix is the registry's own naming for a field whose value is one of a set.
CREATED = re.compile(r"`(?P<field>[a-z][a-z_]*_status):\s*(?P<value>[a-z_]+)`")
#: A documented value set: `` `validation_status` (`pending` | `passed` | `failed`) ``.
VALUE_SET = re.compile(
    r"`(?P<field>[a-z][a-z_]*_status)`\s*\((?P<values>`[a-z_]+`(?:\s*\|\s*`[a-z_]+`)+)\)")
#: One backticked value inside such a set.
VALUE = re.compile(r"`([a-z_]+)`")
#: The schema naming the step that reads the field back: "read back by Step 7", "read by Step 3".
READER = re.compile(r"\bread(?:\s+back)?\s+by\s+Step\s+(?P<step>\d+[a-z]?)\b")
#: A numbered workflow step's heading: `### 7. Verify data quality at a glance`, `### 8a. …`.
STEP_HEADING = re.compile(r"^###\s+(?P<num>\d+[a-z]?)\.\s+(?P<title>\S.*?)\s*$")
#: Any ATX heading, and a code-fence line. Both are line-delimited by construction, which is why
#: the section scan below reads lines (INV-346): a heading inside a fence is not a heading, and
#: Module 4's Step 4 ships a fenced ```markdown template whose `##` lines would end it.
HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")

#: Floors (INV-265). Measured at #687: three status fields written at creation, two of them with a
#: documented value set, one of those naming a reader step in this module. Each floor sits at the
#: measured figure, because a registry that stops documenting one of them is the failure this
#: guard exists to see, not a change it should accept quietly.
MIN_STATUS_FIELDS = 3
MIN_VALUE_SETS = 2
MIN_READERS = 1

#: A gap: the reading step never names ``values`` beside ``field``.
Gap = namedtuple("Gap", "field step line values")
#: A status field the schema writes: its value set (possibly empty) and its reader step, if any.
Field = namedtuple("Field", "name line values reader")


def module_path():
    """The module file, found in the corpus listing rather than built from a hardcoded path."""
    hits = [p for p in corpus_files("plugins", suffixes={".md"})
            if p.parts[-len(MODULE_TAIL):] == MODULE_TAIL]
    if len(hits) != 1:
        raise AssertionError(
            f"expected exactly one {'/'.join(MODULE_TAIL)} in the corpus, found {len(hits)}: "
            f"{[str(p) for p in hits]}")
    return hits[0]


def registry_range(text):
    """``(first, last)`` 1-based lines of the registry schema blockquote.

    Line-anchored on purpose (INV-346): a Markdown blockquote is delimited by whole lines — the
    run of lines whose first non-blank character is ``>`` — so finding one is a line-level read.
    The prose inside it is read wrap-aware, through ``collapsed_blocks``.
    """
    lines = text.split("\n")
    first = None
    for lineno, line in enumerate(lines, 1):
        if line.lstrip().startswith(">") and REGISTRY_OPENER in line:
            first = lineno
            break
    if first is None:
        raise AssertionError(
            f"no blockquote opens with {REGISTRY_OPENER!r}: the registry schema block cannot be "
            "found, so nothing was scanned (INV-265)")
    last = first
    while last < len(lines) and lines[last].lstrip().startswith(">"):
        last += 1
    return first, last


def blocks_in(text, first, last):
    """``(flat, origin)`` for each collapsed block that starts inside lines ``first..last``."""
    for flat, origin in collapsed_blocks(text):
        if first <= origin[0] <= last:
            yield flat, origin


def step_sections(text):
    """``{step number: (first, last)}`` for every numbered workflow step, fence-aware."""
    lines = text.split("\n")
    sections, open_num, open_first, fence = {}, None, 0, None
    for lineno, line in enumerate(lines, 1):
        opener = FENCE.match(line)
        if opener and (fence is None or opener.group(1)[0] == fence):
            fence = None if fence else opener.group(1)[0]
            continue
        if fence or not HEADING.match(line):
            continue
        if open_num is not None:
            sections[open_num] = (open_first, lineno - 1)
            open_num = None
        heading = STEP_HEADING.match(line)
        if heading:
            open_num, open_first = heading.group("num"), lineno
    if open_num is not None:
        sections[open_num] = (open_first, len(lines))
    return sections


def status_fields(text):
    """Every status field the registry schema writes, with its value set and its reader step."""
    first, last = registry_range(text)
    found = {}
    for flat, origin in blocks_in(text, first, last):
        for match in CREATED.finditer(flat):
            found.setdefault(match.group("field"),
                             Field(match.group("field"), line_of(origin, match.start()), (), None))
    for flat, origin in blocks_in(text, first, last):
        reader = READER.search(flat)
        for match in VALUE_SET.finditer(flat):
            name = match.group("field")
            if name not in found:
                continue
            found[name] = Field(name, line_of(origin, match.start()),
                                tuple(VALUE.findall(match.group("values"))),
                                reader.group("step") if reader else None)
    return [found[name] for name in sorted(found)]


def unnamed_values(text, field, values, first, last):
    """The documented values the prose in lines ``first..last`` never names beside ``field``."""
    named = set()
    for flat, _ in blocks_in(text, first, last):
        if field not in flat:
            continue
        for value in values:
            if re.search(r"`(?:" + re.escape(field) + r":\s*)?" + re.escape(value) + r"`", flat):
                named.add(value)
    return tuple(value for value in values if value not in named)


def gaps(text):
    """Every documented value the step that reads its field never names, in order."""
    sections = step_sections(text)
    found = []
    for field in status_fields(text):
        if not field.values or field.reader is None:
            continue
        if field.reader not in sections:
            raise AssertionError(
                f"the registry schema says `{field.name}` is read by Step {field.reader}, and "
                f"this module has no such step: {sorted(sections)}")
        first, last = sections[field.reader]
        missing = unnamed_values(text, field.name, field.values, first, last)
        if missing:
            found.append(Gap(field.name, field.reader, first, missing))
    return found


def describe(gap, path):
    """One line per gap, in the ``file:line`` shape every other guard here reports."""
    return (f"{path}:{gap.line} Step {gap.step} reads `{gap.field}` and says nothing about "
            + ", ".join(f"`{value}`" for value in gap.values))


class RegistryStatusValuesAreHandled(unittest.TestCase):
    """The sweep, over the shipped module."""

    @classmethod
    def setUpClass(cls):
        cls.path = module_path()
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.rel = cls.path.relative_to(REPO_ROOT)

    def test_the_scan_read_something(self):
        """⛔ (INV-265) An emptied scan passes every assertion below without checking anything."""
        fields = status_fields(self.text)
        self.assertGreaterEqual(
            len(fields), MIN_STATUS_FIELDS,
            f"the registry schema block writes {len(fields)} `*_status` fields at creation, under "
            f"the floor of {MIN_STATUS_FIELDS}: the creation sentence was reworded and this scan "
            "is reading nothing")
        with_values = [f for f in fields if f.values]
        self.assertGreaterEqual(
            len(with_values), MIN_VALUE_SETS,
            f"only {len(with_values)} status fields document a value set, under the floor of "
            f"{MIN_VALUE_SETS}: the `field` (`a` | `b`) shape was reworded")
        readers = [f for f in with_values if f.reader is not None]
        self.assertGreaterEqual(
            len(readers), MIN_READERS,
            f"no status field names a reading step in this module ({len(readers)} < "
            f"{MIN_READERS}): the schema's own \"read back by Step N\" sentence was reworded, so "
            "every field would be excluded and the sweep would pass vacuously")
        self.assertTrue(step_sections(self.text),
                        "no numbered workflow step was found, so no step prose was read")

    def test_every_documented_value_is_handled_by_the_step_that_reads_it(self):
        found = gaps(self.text)
        self.assertEqual(
            [], [describe(gap, self.rel) for gap in found],
            "a registry status field documents a value the step that reads it never names, so a "
            "source carrying that value leaves the step with nothing to do (#687)")

    def test_a_field_whose_reader_is_not_a_step_here_is_out_of_scope_for_a_stated_reason(self):
        """⛔ The exclusion is verified by scanning, never taken on trust.

        A field the schema documents a value set for but names no reading step for is left to the
        module that reads it. That is only honest while no step of **this** module reads it: if
        one does, the field is in scope and its handling must be complete here.
        """
        sections = step_sections(self.text)
        first, last = registry_range(self.text)
        for field in status_fields(self.text):
            if field.reader is not None:
                continue
            with self.subTest(field=field.name):
                reading = []
                for num, (start, end) in sections.items():
                    for flat, origin in blocks_in(self.text, start, end):
                        if first <= origin[0] <= last or field.name not in flat:
                            continue
                        reading.append(f"Step {num} (line {origin[0]})")
                self.assertEqual(
                    [], reading,
                    f"`{field.name}` names no reading step in the registry schema, so this guard "
                    f"excludes it as another module's field — but {', '.join(reading)} of this "
                    "module names it, which makes the exclusion wrong rather than scoped")


class TheCheckMeasuresTheProse(unittest.TestCase):
    """Controls: what the check must report, and what it must not (INV-282)."""

    @classmethod
    def setUpClass(cls):
        cls.path = module_path()
        cls.text = cls.path.read_text(encoding="utf-8")

    #: Step 7 exactly as it shipped before #687 — the negative control, run inside the suite over
    #: a mutated copy of the shipped text so it measures this check rather than a second
    #: implementation of it (INV-265).
    PRE_687 = ("Each file was already validated in step 2 and the results are stored in the "
               "registry. Review\n`config/data_sources.yaml` and check the `validation_status` "
               "and `validation_checks` fields for\neach data source entry. Confirm every source "
               "shows `validation_status: passed`. If any source\nshows `validation_status: "
               "failed`, revisit that data source and resolve the failing checks\nbefore "
               "proceeding.\n")

    def step_7(self):
        """The shipped Step 7 section's text, to mutate."""
        first, last = step_sections(self.text)["7"]
        return "\n".join(self.text.split("\n")[first - 1:last])

    def test_the_pre_687_step_7_is_reported(self):
        """The one site the scan reported before the fix, and nothing else."""
        mutated = self.text.replace(self.step_7(), "### 7. Verify data quality at a glance\n\n"
                                    + self.PRE_687 + "\n**Checkpoint:** write step 7 to "
                                    "`config/bootcamp_progress.json`.\n")
        self.assertNotEqual(mutated, self.text,
                            "Step 7's section could not be replaced, so nothing was mutated and "
                            "this control proves nothing (INV-265)")
        found = gaps(mutated)
        self.assertEqual([("validation_status", "7", ("pending",))],
                         [(gap.field, gap.step, gap.values) for gap in found],
                         "Step 7 without its `pending` branch is exactly what #687 reported, and "
                         "this check no longer sees it")

    def test_the_pending_branch_is_found_however_it_wraps(self):
        """(INV-346) The branch is prose, so a different wrap must not change the result."""
        rewrapped = self.text.replace(self.step_7(), " ".join(self.step_7().split()))
        self.assertNotEqual(rewrapped, self.text, "Step 7 was already on one line, so this "
                                                  "control did not re-wrap anything")
        self.assertEqual([], gaps(rewrapped),
                         "Step 7 collapsed onto one line is reported, so the check is reading "
                         "lines rather than blocks")

    def test_the_step_that_writes_the_field_is_not_reported(self):
        """⛔ A writer sets the values it can set; it is not required to speak for the rest.

        The Data File Validation note sets `validation_status` to `passed` or `failed` and never
        to `pending`, which the schema already wrote at creation. It sits inside Step 2's section,
        so a check that swept every step naming the field would report it — correct prose, and a
        guard that flags correct prose is relaxed rather than fixed (INV-282).
        """
        self.assertIn("set that source's `validation_status` to `passed` or `failed`", self.text,
                      "the writer sentence this control is pinned to has been reworded; re-pin it "
                      "rather than deleting the control")
        self.assertEqual([], [gap.step for gap in gaps(self.text) if gap.step == "2"],
                         "Step 2's Data File Validation note is reported, although writing two of "
                         "three values is exactly what it is for")

    def test_a_value_named_only_elsewhere_in_the_module_is_still_reported(self):
        """Scoping is per step: the reader must name the value, not a neighbor.

        The value is renamed inside Step 7 **only**, so the schema block two steps up still
        documents it and Step 2 still writes beside it. A check reading the file as a whole would
        satisfy itself from either and report nothing.
        """
        renamed = (self.step_7().replace("`validation_status: pending`", "`FIELD: GONE`")
                   .replace("`pending`", "`GONE`"))
        moved = self.text.replace(self.step_7(), renamed)
        self.assertNotEqual(moved, self.text, "Step 7 names no `pending`, so the fix is missing")
        self.assertIn("`pending`", moved,
                      "`pending` is now named nowhere in the module, so this control cannot show "
                      "that the check is scoped to the reading step")
        self.assertEqual([("validation_status", ("pending",))],
                         [(gap.field, gap.values) for gap in gaps(moved)],
                         "a value the reading step no longer names is not reported, so the check "
                         "is matching somewhere other than the step")


class Step7HandlesEveryValidationStatus(unittest.TestCase):
    """#687's own criteria, on the shipped Step 7."""

    @classmethod
    def setUpClass(cls):
        cls.path = module_path()
        cls.text = cls.path.read_text(encoding="utf-8")
        first, last = step_sections(cls.text)["7"]
        cls.step = "\n".join(cls.text.split("\n")[first - 1:last])
        cls.flat = [flat for flat, _ in collapsed_blocks(cls.step)]

    def pending_block(self):
        for flat in self.flat:
            if "`pending`" in flat or "`validation_status: pending`" in flat:
                return flat
        self.fail("Step 7 has no block naming `pending`, so the third value has no branch (#687)")

    def test_it_still_confirms_passed_and_remedies_failed(self):
        """The two branches that already shipped are unchanged in substance."""
        self.assertIn("Confirm every source shows `validation_status: passed`", self.step)
        self.assertRegex(
            self.step,
            r"`validation_status: failed`[\s\S]*revisit that data source and resolve the failing",
            "the `failed` remedy no longer sends the bootcamper back to that data source")

    def test_pending_means_there_was_nothing_to_validate(self):
        block = self.pending_block()
        self.assertRegex(
            block, r"no file was collected|no file is collected",
            "the `pending` branch does not say why the value is there — that no file was "
            "collected — so a reader cannot tell it from a validation nobody ran")
        self.assertIn("nothing to validate", block,
                      "the `pending` branch does not say there is nothing to validate")

    def test_a_documented_location_only_source_is_expected_to_carry_it(self):
        block = self.pending_block()
        self.assertIn("documented-location-only", block,
                      "the `pending` branch does not name the source that carries it, so it reads "
                      "as an edge case rather than the expected outcome of Option B")
        self.assertRegex(block, r"\bexpected\b",
                         "the `pending` branch does not say the value is expected there")

    def test_it_does_not_block_the_step(self):
        block = self.pending_block()
        self.assertRegex(
            block, r"does not block|never blocks|not a blocker",
            "the `pending` branch does not say the source may proceed, which is the whole defect: "
            "Step 7's confirmation was unsatisfiable for a source that never had a file")

    def test_the_schema_value_set_is_untouched(self):
        """⛔ #687 is a missing branch, not a missing value.

        A distinct value (`not_applicable`) would read better at Step 7 and would have to move
        every other reader of the field with it, so the branch was added and the set left alone.
        """
        fields = {field.name: field.values for field in status_fields(self.text)}
        self.assertEqual(("pending", "passed", "failed"), fields["validation_status"],
                         "the documented value set changed; every reader of `validation_status` "
                         "has to move with it, which #687 deliberately did not do")
        self.assertNotIn("not_applicable", self.text,
                         "a value outside the documented set appears in the module")
