"""Module 5 writes each source's sample output to `data/mapping/`, never to `data/senzing-ready/`.

Three rules read `data/senzing-ready/` as a directory of full, load-ready outputs, one per mapped
source: Phase A's loadable total counts every source's file there, Phase B keeps subset files out
because that total "counts every file there", and Module 5's step 19 gate wants one
`docs/mapping/{source_name}_mapper.md` for every file there. Step 18 used to save the sample as
`data/senzing-ready/[name]_sample.jsonl` (and step 14's concise example named the same place), so a
literal reading counted the sampled records twice and asked for a mapper doc per sample (#338).
Module 5's own file-placement rule already sent the per-source sample to `data/mapping/`.

These tests pin the fix:

- step 18 places the sample at `data/mapping/[name]_sample.jsonl`;
- no file under `plugins/senzing-bootcamp/` names a `data/senzing-ready/` path ending in
  `_sample.jsonl`;
- the directory-based definitions that make this load-bearing still read as directory listings,
  so a later reword that drops them is noticed here rather than by a double-counted load.

The first two predicates are negative-controlled against the pre-#338 lines, held below.

A file-name pattern cannot tell a partial file from a full one, so #396 adds section-scoped checks
(each section runs from its `### ` heading to the next `### ` heading):

- step 14 writes its test run to `data/mapping/{source}_sample.jsonl`, in the instruction itself;
- step 15 writes its test run to `data/mapping/{source}_quality.jsonl`, passes that path as the
  workflow-step-4 `output_path`, and keeps it there even when the run covers every record;
- neither section names `data/senzing-ready/` at all, whatever the file name;
- step 18 runs the transformation program on the whole source into
  `data/senzing-ready/[name].jsonl`, so the folder Data processing loads from is still filled.

These are negative-controlled against the pre-#396 step 14 and 15 openings, held below, and
against a `data/senzing-ready/` path of any name injected into either section.

Enforces **INV-084**'s 2026-10-02 note (#338): `data/senzing-ready/` holds only each mapped
source's full, load-ready output. It asserts what the guidance *states*, and does **not** establish
that a live run writes no partial file there, which only `dry-run` phase 3 can observe.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
SKILLS = os.path.join(PLUGIN, "skills")
PHASE2 = os.path.join(SKILLS, "module-05-data-quality-mapping", "phase2-data-mapping.md")
PHASE_A = os.path.join(SKILLS, "module-06-data-processing", "phaseA-build-loading.md")
PHASE_B = os.path.join(SKILLS, "module-06-data-processing", "phaseB-load-first-source.md")

STEP14_HEAD = "### 14. Test"
STEP15_HEAD = "### 15. Quality analysis"
STEP18_HEAD = "### 18. Save and document"

# The lines as they stood before #338, verbatim, for the negative controls.
OLD_STEP18_LINE = "- Sample output in `data/senzing-ready/[name]_sample.jsonl`."
OLD_STEP14_EXAMPLE = (
    '>   data/senzing-ready/customers_sample.jsonl").'
)

# The step 14 and 15 openings as they stood before #396, verbatim, for the negative controls.
OLD_STEP14_OPENING = "Run on 10-100 records from `data/samples/`. Validate with"
OLD_STEP15_OPENING = (
    "Run on 1000+ records. Evaluate feature distribution, coverage, quality scores. This is "
    "workflow\nstep 4's single advance: `action='advance'`, carrying `verdict` in `data` — "
    "`approve`,\n`rework_mapping`, or `rework_code` — plus `output_path` and `records_output`. "
    "A `rework_*` verdict"
)

STEP14_OUTPUT = "`data/mapping/{source}_sample.jsonl`"
STEP15_OUTPUT = "`data/mapping/{source}_quality.jsonl`"
STEP18_FULL_OUTPUT = "`data/senzing-ready/[name].jsonl`"

# A `data/senzing-ready/` path (either separator) whose file name ends in `_sample.jsonl`.
SAMPLE_IN_SENZING_READY = re.compile(
    r"data[/\\]senzing-ready[/\\][^\s`'\"()]*_sample\.jsonl"
)

TEXT_SUFFIXES = (".md", ".py", ".sh", ".ps1", ".json", ".yaml", ".yml", ".txt", ".toml")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def flat(text):
    """Collapse line wraps so a phrase matches wherever the prose breaks."""
    return re.sub(r"\s+", " ", text)


def section(text, head):
    """One step, from its heading up to the next `### ` heading."""
    start = text.index(head)
    end = text.find("\n### ", start + len(head))
    return text[start:end if end != -1 else len(text)]


def step18_section(text):
    return section(text, STEP18_HEAD)


def instruction_text(section_text):
    """The section without its `>` presentation blocks, so an example cannot stand in for the rule.

    Line-scoped by design (#424): a `>` marker opens each line of a blockquote; the rest is
    flattened before anything is matched.
    """
    return flat("\n".join(
        line for line in section_text.splitlines() if not line.lstrip().startswith(">")
    ))


def names_senzing_ready(section_text):
    """Any mention of the load-ready folder, whatever file name follows it (#396)."""
    return re.search(r"senzing-ready", section_text) is not None


def step14_writes_to_mapping(section_text):
    return STEP14_OUTPUT in instruction_text(section_text)


def step15_writes_to_mapping(section_text):
    body = instruction_text(section_text)
    return (
        f"write its output to {STEP15_OUTPUT}" in body
        and f"`output_path` ({STEP15_OUTPUT})" in body
        and "even when the run covers every record" in body
    )


def step18_writes_full_output(section_text):
    body = flat(section_text)
    return (
        "run the transformation program on the whole source and write "
        f"{STEP18_FULL_OUTPUT}" in body
    )


def places_sample_in_mapping(section):
    return "Sample output in `data/mapping/[name]_sample.jsonl`" in section


def names_sample_in_senzing_ready(text):
    return SAMPLE_IN_SENZING_READY.search(text) is not None


def plugin_text_files():
    for root, _dirs, files in os.walk(PLUGIN):
        for name in sorted(files):
            if name.endswith(TEXT_SUFFIXES):
                yield os.path.join(root, name)


class TestStep18PlacesTheSampleInDataMapping(unittest.TestCase):
    def test_step18_names_data_mapping_for_the_sample(self):
        section = step18_section(read(PHASE2))
        self.assertTrue(
            places_sample_in_mapping(section),
            "Step 18 must save the sample as `data/mapping/[name]_sample.jsonl` (#338).",
        )
        self.assertFalse(names_sample_in_senzing_ready(section))

    def test_negative_control_rejects_the_old_step18_line(self):
        old = step18_section(read(PHASE2)).replace(
            "- Sample output in `data/mapping/[name]_sample.jsonl`.", OLD_STEP18_LINE
        )
        self.assertNotEqual(old, step18_section(read(PHASE2)))
        self.assertFalse(places_sample_in_mapping(old))
        self.assertTrue(names_sample_in_senzing_ready(old))


class TestNoSampleIsDirectedIntoSenzingReady(unittest.TestCase):
    def test_no_plugin_file_names_a_sample_in_senzing_ready(self):
        # Line-scoped by design (#424): the pattern is one path with no whitespace in it.
        offenders = []
        for path in plugin_text_files():
            try:
                text = read(path)
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if names_sample_in_senzing_ready(line):
                    offenders.append(f"{os.path.relpath(path, REPO_ROOT)}:{number}: {line.strip()}")
        self.assertEqual(
            offenders, [],
            "A `*_sample.jsonl` belongs in `data/mapping/`; `data/senzing-ready/` holds only full, "
            "load-ready outputs, which the loadable total and the mapper-doc gate count (#338).",
        )

    def test_scan_covers_the_module5_skill(self):
        self.assertIn(PHASE2, list(plugin_text_files()))

    def test_negative_control_rejects_the_old_lines(self):
        self.assertTrue(names_sample_in_senzing_ready(OLD_STEP18_LINE))
        self.assertTrue(names_sample_in_senzing_ready(OLD_STEP14_EXAMPLE))
        self.assertTrue(names_sample_in_senzing_ready(r"data\senzing-ready\x_sample.jsonl"))

    def test_scan_spares_a_full_output_and_a_mapping_sample(self):
        self.assertFalse(names_sample_in_senzing_ready("`data/senzing-ready/customers.jsonl`"))
        self.assertFalse(names_sample_in_senzing_ready("`data/mapping/customers_sample.jsonl`"))
        self.assertFalse(names_sample_in_senzing_ready("`data/senzing-ready/*.jsonl`"))


class TestTestRunsStayInDataMapping(unittest.TestCase):
    """Steps 14 and 15 are test runs: they write to `data/mapping/` only (#396, INV-084)."""

    def setUp(self):
        self.text = read(PHASE2)
        self.s14 = section(self.text, STEP14_HEAD)
        self.s15 = section(self.text, STEP15_HEAD)

    def test_sections_end_at_the_next_step(self):
        self.assertNotIn(STEP15_HEAD, self.s14)
        self.assertNotIn("### 16.", self.s15)

    def test_step14_names_its_sample_output_in_the_instruction(self):
        self.assertTrue(step14_writes_to_mapping(self.s14),
                        f"Step 14 must write its test run to {STEP14_OUTPUT} (#396).")
        self.assertFalse(names_senzing_ready(self.s14),
                         "Step 14 is a test run and must name no `data/senzing-ready/` path.")

    def test_step15_names_its_output_and_output_path(self):
        self.assertTrue(
            step15_writes_to_mapping(self.s15),
            f"Step 15 must write to {STEP15_OUTPUT}, pass it as `output_path`, and keep it there "
            "even when the run covers every record (#396).",
        )
        self.assertFalse(names_senzing_ready(self.s15),
                         "Step 15 is a test run and must name no `data/senzing-ready/` path.")

    def test_steps_14_and_15_write_different_files(self):
        self.assertNotIn(STEP15_OUTPUT, self.s14)
        self.assertNotIn(STEP14_OUTPUT, self.s15)

    def test_negative_control_rejects_the_old_openings(self):
        new14 = self.s14[self.s14.index("Run the transformation program"):
                         self.s14.index("Validate with") + len("Validate with")]
        old14 = self.s14.replace(new14, OLD_STEP14_OPENING)
        self.assertNotEqual(old14, self.s14)
        self.assertFalse(step14_writes_to_mapping(old14))

        new15 = self.s15[self.s15.index("Run the transformation program"):
                         self.s15.index("A `rework_*` verdict") + len("A `rework_*` verdict")]
        old15 = self.s15.replace(new15, OLD_STEP15_OPENING)
        self.assertNotEqual(old15, self.s15)
        self.assertFalse(step15_writes_to_mapping(old15))

    def test_negative_control_an_example_alone_does_not_count(self):
        only_example = self.s14.replace(
            f"write its output to\n{STEP14_OUTPUT}", "write its output somewhere"
        )
        self.assertNotEqual(only_example, self.s14)
        self.assertIn("data/mapping/customers_sample.jsonl", only_example)
        self.assertFalse(step14_writes_to_mapping(only_example))

    def test_negative_control_rejects_any_senzing_ready_path(self):
        for name in ("customers.jsonl", "customers_partial.jsonl", "x_subset.jsonl", ""):
            for sec in (self.s14, self.s15):
                for sep in ("/", "\\"):
                    injected = sec + f"\nWrite the run to `data{sep}senzing-ready{sep}{name}`.\n"
                    self.assertTrue(names_senzing_ready(injected), (name, sep))


class TestStep18WritesTheFullOutput(unittest.TestCase):
    """The load-ready file comes from step 18 alone, so `data/senzing-ready/` is still filled (#396)."""

    def test_step18_runs_the_whole_source_into_senzing_ready(self):
        self.assertTrue(
            step18_writes_full_output(step18_section(read(PHASE2))),
            f"Step 18 must run the transformation program on the whole source into {STEP18_FULL_OUTPUT}.",
        )

    def test_full_output_matches_step12_example(self):
        self.assertIn("data/senzing-ready/customers.jsonl", section(read(PHASE2), "### 12."))

    def test_negative_control_rejects_step18_without_the_line(self):
        s18 = step18_section(read(PHASE2))
        start = s18.index("- Full output:")
        end = s18.index("\n- ", start + 1)
        without = s18[:start] + s18[end + 1:]
        self.assertNotEqual(without, s18)
        self.assertFalse(step18_writes_full_output(without))


class TestDirectoryBasedDefinitionsStayDirectoryListings(unittest.TestCase):
    """Why the sample must stay out: these rules count or gate on every file in the directory."""

    def test_phase_a_loadable_total_counts_every_mapped_file(self):
        self.assertIn(
            "source's file in `data/senzing-ready/` together", flat(read(PHASE_A))
        )

    def test_phase_b_subset_reason_counts_every_file_there(self):
        self.assertIn(
            "Phase A's loadable total counts every file there, so a subset file inside it would "
            "count its source twice",
            flat(read(PHASE_B)),
        )

    def test_step19_gate_lists_every_file(self):
        self.assertIn(
            "list ALL files in `data/senzing-ready/` and verify that EACH has a corresponding "
            "`docs/mapping/{source_name}_mapper.md`",
            flat(read(PHASE2)).replace("> ", ""),
        )

    def test_file_placement_rule_sends_the_sample_to_data_mapping(self):
        self.assertIn(
            "the per-source `{source}_sample.jsonl`, intermediate analyzer JSONL) → `data/mapping/`",
            flat(read(PHASE2)),
        )


if __name__ == "__main__":
    unittest.main()
