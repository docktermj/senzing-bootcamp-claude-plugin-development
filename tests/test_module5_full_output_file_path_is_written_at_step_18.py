"""Module 5 points a source's `file_path` at its full output once, at step 18, where the file is written.

Since #396, step 18 always runs the transformation program on the whole source, writes
`data/senzing-ready/[name].jsonl`, and points the source's `file_path` in
`config/data_sources.yaml` at it. Step 17's registry note still said "If a transformed file was
created, update `file_path` to the `data/senzing-ready/` output", but step 17 runs before step 18
writes that file: the condition named a file that did not exist yet, and the same registry write
was stated at two sites (INV-300). Step 18's bullet pointed back at step 17's note, and the
`quality_iteration` remap block said Module 6 reloads "the `file_path` Step 17 records" (#422).

These tests pin the fix:

- step 17's registry note has no `file_path` clause, and still sets `mapping_status` to
  `complete` and sets `updated_at`;
- step 18's "Full output" bullet states the `file_path` write, with no back-pointer to step 17;
- the `quality_iteration` remap block says the `file_path` Step 18 records;
- across every Module 5 file, exactly one site instructs the `file_path` update for the full
  output, and it is inside step 18; no Module 5 text says step 17 records or updates `file_path`.

Each section runs from its `### ` heading to the next `### ` heading. Every phrase check reads
through ``match_lines`` (``tests/_wrapped_text.py``, #426), so a phrase wrapped across lines or
across `>` blockquote lines still matches. Negative controls re-insert step 17's old clause,
delete step 18's write, and restore the old back-pointer and the old remap wording, each held
verbatim below.

Upholds INV-300 (one statement of a rule) and INV-084 (the full output lives in
`data/senzing-ready/`). It asserts what the guidance *states*, and does **not** establish that a
live run writes the registry that way, which only `dry-run` phase 3 can observe.
`tests/test_quality_iteration_returns_to_step_3b.py` guards the remap block's `fast_pathed: false`
rule, which this issue leaves unchanged.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

from _wrapped_text import match_lines

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE5 = os.path.join(
    REPO_ROOT, "plugins", "senzing-bootcamp", "skills", "module-05-data-quality-mapping"
)
PHASE2 = os.path.join(MODULE5, "phase2-data-mapping.md")

STEP17_HEAD = "### 17. Iterate"
STEP18_HEAD = "### 18. Save and document"

# The text as it stood before #422, verbatim, for the negative controls.
OLD_STEP17_NOTE = (
    "> `config/data_sources.yaml` and set `updated_at`. If a transformed file was created, update\n"
    "> `file_path` to the `data/senzing-ready/` output.\n"
)
NEW_STEP17_NOTE_TAIL = "> `config/data_sources.yaml` and set `updated_at`.\n"
OLD_STEP18_LINE = "  `file_path` in `config/data_sources.yaml` at it (step 17's registry note).\n"
NEW_STEP18_LINE = "  `file_path` in `config/data_sources.yaml` at it.\n"
OLD_REMAP = "at the `file_path` Step 17 records"
NEW_REMAP = "at the `file_path` Step 18 records"
STEP18_WRITE = "Point the source's\n  `file_path` in `config/data_sources.yaml` at it."

#: Prose inside one sentence: any character that does not end it. A dot inside a path such as
#: `config/data_sources.yaml` is not a sentence end.
_IN_SENTENCE = r"(?:(?!\.(?:\s|$)).)"

#: An instruction to update or point `file_path` at the full output, within one sentence.
FULL_OUTPUT_FILE_PATH_WRITE = re.compile(
    rf"(?i)\b(?:update|point)\b{_IN_SENTENCE}{{0,120}}`file_path`{_IN_SENTENCE}{{0,120}}"
    rf"(?:senzing-ready|\bat it\b)"
)
#: Step 17's old conditional, whatever its wrap.
TRANSFORMED_FILE_CONDITION = re.compile(r"If a transformed file was created")
#: Any `file_path` mention.
FILE_PATH = re.compile(r"`file_path`")
#: The registry note's own write, which step 17 keeps.
STEP17_STATUS_WRITE = re.compile(
    r"Update the source's `mapping_status` to `complete` in `config/data_sources\.yaml` and set "
    r"`updated_at`\."
)
#: Step 18's write, as one sentence.
STEP18_FILE_PATH_WRITE = re.compile(
    r"write `data/senzing-ready/\[name\]\.jsonl`, the load-ready file Data processing loads\. "
    r"Point the source's `file_path` in `config/data_sources\.yaml` at it\."
)
#: A back-pointer to step 17's registry note.
STEP17_BACK_POINTER = re.compile(r"(?i)step 17's registry note")
#: Text saying step 17 records or updates `file_path`.
STEP17_OWNS_FILE_PATH = re.compile(
    r"(?i)`file_path` step 17 records|step 17 (?:records|updates|sets) (?:the source's )?`file_path`"
)
#: The remap block's sentence, ending on the step that records `file_path`.
REMAP_READS_STEP18 = re.compile(
    r"Module 6 reloads the remapped output at the `file_path` Step 18 records, not the original "
    r"`data/raw/` file\."
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def section(text, head):
    """One step, from its heading up to the next `### ` heading."""
    start = text.index(head)
    end = text.find("\n### ", start + len(head))
    return text[start:end if end != -1 else len(text)]


def module5_files():
    return sorted(
        os.path.join(MODULE5, name) for name in os.listdir(MODULE5) if name.endswith(".md")
    )


def step17_has_file_path_clause(step17):
    return bool(match_lines(step17, FILE_PATH) or match_lines(step17, TRANSFORMED_FILE_CONDITION))


def step17_keeps_status_write(step17):
    return bool(match_lines(step17, STEP17_STATUS_WRITE))


def step18_states_the_write(step18):
    return bool(match_lines(step18, STEP18_FILE_PATH_WRITE))


def full_output_write_sites(texts):
    """`(name, line)` of every site instructing the full output's `file_path` write."""
    return [
        (name, line)
        for name, text in texts.items()
        for line in match_lines(text, FULL_OUTPUT_FILE_PATH_WRITE)
    ]


def step_line_range(text, head):
    """The 1-based first and last line of one step's section."""
    start = text.index(head)
    end = text.find("\n### ", start + len(head))
    end = end if end != -1 else len(text)
    return text.count("\n", 0, start) + 1, text.count("\n", 0, end) + 1


def mutate(text, old, new):
    mutated = text.replace(old, new, 1)
    assert mutated != text, f"mutation did not apply: {old!r}"
    return mutated


class TestStep17HasNoFilePathClause(unittest.TestCase):
    def setUp(self):
        self.step17 = section(read(PHASE2), STEP17_HEAD)

    def test_section_ends_at_step_18(self):
        self.assertNotIn(STEP18_HEAD, self.step17)

    def test_step17_names_no_file_path(self):
        self.assertFalse(
            step17_has_file_path_clause(self.step17),
            "Step 17 runs before step 18 writes the full output; the `file_path` write is step "
            "18's alone (#422, INV-300).",
        )

    def test_step17_still_sets_mapping_status_and_updated_at(self):
        self.assertTrue(
            step17_keeps_status_write(self.step17),
            "Step 17's registry note must still set `mapping_status` to `complete` and set "
            "`updated_at` (#422).",
        )

    def test_negative_control_reinserted_clause_fails(self):
        old = mutate(self.step17, NEW_STEP17_NOTE_TAIL, OLD_STEP17_NOTE)
        self.assertTrue(step17_has_file_path_clause(old))
        # The old clause wraps across two `>` lines; it is still one match.
        self.assertEqual(len(match_lines(old, TRANSFORMED_FILE_CONDITION)), 1)
        self.assertEqual(len(match_lines(old, FULL_OUTPUT_FILE_PATH_WRITE)), 1)

    def test_negative_control_dropped_status_write_fails(self):
        without = mutate(self.step17, "and set `updated_at`", "")
        self.assertFalse(step17_keeps_status_write(without))


class TestStep18StatesTheWriteAlone(unittest.TestCase):
    def setUp(self):
        self.step18 = section(read(PHASE2), STEP18_HEAD)

    def test_step18_states_the_file_path_write(self):
        self.assertTrue(
            step18_states_the_write(self.step18),
            "Step 18's \"Full output\" bullet must point the source's `file_path` at "
            "`data/senzing-ready/[name].jsonl` (#396, #422).",
        )

    def test_step18_has_no_back_pointer_to_step17(self):
        self.assertEqual(match_lines(self.step18, STEP17_BACK_POINTER), [])

    def test_negative_control_deleted_write_fails(self):
        without = mutate(self.step18, " " + STEP18_WRITE, "")
        self.assertFalse(step18_states_the_write(without))
        self.assertEqual(match_lines(without, FULL_OUTPUT_FILE_PATH_WRITE), [])

    def test_negative_control_old_back_pointer_fails(self):
        old = mutate(self.step18, NEW_STEP18_LINE, OLD_STEP18_LINE)
        self.assertNotEqual(match_lines(old, STEP17_BACK_POINTER), [])


class TestOneSiteInModule5(unittest.TestCase):
    def setUp(self):
        self.texts = {os.path.basename(p): read(p) for p in module5_files()}
        self.phase2 = self.texts["phase2-data-mapping.md"]

    def test_scan_covers_every_module5_file(self):
        self.assertEqual(
            sorted(self.texts),
            ["SKILL.md", "phase1-quality-assessment.md", "phase2-data-mapping.md",
             "phase3-test-load.md"],
        )

    def test_exactly_one_site_and_it_is_step18(self):
        sites = full_output_write_sites(self.texts)
        first, last = step_line_range(self.phase2, STEP18_HEAD)
        self.assertEqual(len(sites), 1, f"Expected one full-output `file_path` write: {sites}")
        name, line = sites[0]
        self.assertEqual(name, "phase2-data-mapping.md")
        self.assertTrue(first <= line <= last, f"The write is at line {line}, outside step 18.")

    def test_no_module5_text_says_step17_owns_file_path(self):
        offenders = [
            (name, line)
            for name, text in self.texts.items()
            for pattern in (STEP17_OWNS_FILE_PATH, STEP17_BACK_POINTER, TRANSFORMED_FILE_CONDITION)
            for line in match_lines(text, pattern)
        ]
        self.assertEqual(offenders, [], "Step 18 records `file_path`, not step 17 (#422).")

    def test_remap_block_says_step18_records(self):
        self.assertNotEqual(
            match_lines(self.phase2, REMAP_READS_STEP18), [],
            "The `quality_iteration` remap block must say Module 6 reloads the `file_path` Step 18 "
            "records (#422).",
        )

    def test_negative_control_reinserted_step17_clause_makes_two_sites(self):
        texts = dict(self.texts)
        texts["phase2-data-mapping.md"] = mutate(self.phase2, NEW_STEP17_NOTE_TAIL, OLD_STEP17_NOTE)
        self.assertEqual(len(full_output_write_sites(texts)), 2)

    def test_negative_control_deleted_step18_write_leaves_none(self):
        texts = dict(self.texts)
        texts["phase2-data-mapping.md"] = mutate(self.phase2, " " + STEP18_WRITE, "")
        self.assertEqual(full_output_write_sites(texts), [])

    def test_negative_control_old_remap_wording_fails(self):
        old = mutate(self.phase2, NEW_REMAP, OLD_REMAP)
        self.assertEqual(match_lines(old, REMAP_READS_STEP18), [])
        self.assertNotEqual(match_lines(old, STEP17_OWNS_FILE_PATH), [])

    def test_negative_control_step17_updates_file_path_is_caught(self):
        for phrase in ("Step 17 updates `file_path`", "step 17 records the source's `file_path`",
                       "Step 17 sets\n`file_path`"):
            self.assertNotEqual(match_lines(phrase, STEP17_OWNS_FILE_PATH), [], phrase)

    def test_remap_fast_pathed_span_is_unchanged(self):
        # #392's guard matches this span byte for byte, line break and indent included.
        self.assertIn("Step 17's registry write also sets `fast_pathed:\n   false`", self.phase2)


if __name__ == "__main__":
    unittest.main()
