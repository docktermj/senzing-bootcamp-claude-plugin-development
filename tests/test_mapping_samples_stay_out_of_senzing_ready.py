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

STEP18_HEAD = "### 18. Save and document"

# The lines as they stood before #338, verbatim, for the negative controls.
OLD_STEP18_LINE = "- Sample output in `data/senzing-ready/[name]_sample.jsonl`."
OLD_STEP14_EXAMPLE = (
    '>   data/senzing-ready/customers_sample.jsonl").'
)

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


def step18_section(text):
    """Step 18, from its heading up to the next `### ` heading."""
    start = text.index(STEP18_HEAD)
    end = text.find("\n### ", start + len(STEP18_HEAD))
    return text[start:end if end != -1 else len(text)]


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
