"""Tests that the per-stage model/effort recommendation stays consistent.

The INV-063 module-start nudge names a recommended model in two places that must
agree: the operational table in `skills/bootcamp-onboarding/ground-rules.md` (the
file the guide actually loads at module start) and the maintainer reference in
`docs/model-selection.md`. `ground-rules.md` even carries a "keep in sync"
instruction — but nothing enforced it, and the pair drifted a full model
generation behind before a bootcamper reported it.

These tests are the enforcement:

1. No superseded model name or ID survives anywhere in the shipped plugin.
2. The two per-stage tables agree row for row.

Enforces **INV-114** (bootcamper-facing model/effort guidance names only current models
and IDs, with `ground-rules.md` authoritative and `docs/model-selection.md` derived) and
**INV-140** (every stage the bootcamp can run has exactly one row in the per-stage table,
including the apparatus-exempt setup stages). Both name this file as their enforcer.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
GROUND_RULES = os.path.join(PLUGIN, "skills", "bootcamp-onboarding", "ground-rules.md")
MODEL_SELECTION = os.path.join(PLUGIN, "docs", "model-selection.md")

# Model names/IDs that have been superseded. A hit means the recommendation would
# tell a bootcamper to switch *down* from the current model — the defect this
# guards. Add a row whenever a model is superseded; the last element of each pair
# is the current replacement, quoted in the failure message.
SUPERSEDED = [
    ("Opus 4.8", "Opus 5.5"),
    ("claude-opus-4-8", "claude-opus-5-5"),
    ("Opus 5", "Opus 5.5"),
    ("Sonnet 5", "Sonnet 5.5"),
    ("Fable 5", "Fable 5.1"),
    ("claude-opus-5", "claude-opus-5-5"),
    ("claude-sonnet-5", "claude-sonnet-5-5"),
    ("claude-fable-5", "claude-fable-5-1"),
]


def superseded_pattern(stale):
    """Match `stale` only where it ends at a version boundary.

    A plain substring test cannot hold a row like ("Opus 5", "Opus 5.5"): the stale
    name is a prefix of its own replacement, as `claude-opus-5` is of
    `claude-opus-5-5`. So a display name must not be followed by `.<digit>` or a
    digit ("Opus 5" is not "Opus 5.5", but is "Opus 5," "Opus 5 /" and a
    sentence-final "Opus 5."), and an ID must not be followed by `-<digit>` or a
    digit (`claude-opus-5` is not `claude-opus-5-5`, but is `claude-opus-5[1m]`).
    """
    if stale.startswith("claude-"):
        return re.compile(r"(?<![\w-])" + re.escape(stale) + r"(?!-?\d)")
    return re.compile(r"\b" + re.escape(stale) + r"(?!\.?\d)")


# The one block allowed to name a superseded model: the staleness note in
# docs/model-selection.md deliberately cites the prior models to explain the
# supersession. Only that blockquote is exempt, never the rest of the file: a
# whole-file exemption is how that file's tier table kept naming Fable 5, Opus 5
# and Sonnet 5 after they were superseded.
STALENESS_NOTE_FILE = os.path.join(PLUGIN, "docs", "model-selection.md")
STALENESS_NOTE_MARKER = "> **Point-in-time data"


def without_staleness_note(text):
    """`text` with the staleness-note blockquote removed, and nothing else.

    The block is the run of `>` lines that starts at STALENESS_NOTE_MARKER. With
    no marker nothing is removed, so a missing note exempts nothing.
    """
    lines = text.splitlines(keepends=True)
    kept, in_note = [], False
    for line in lines:
        if line.startswith(STALENESS_NOTE_MARKER):
            in_note = True
        elif in_note and not line.startswith(">"):
            in_note = False
        if not in_note:
            kept.append(line)
    return "".join(kept)


def superseded_offenders(rel, text, exempt_note=False):
    """Every superseded name or ID in `text`, as failure-message lines."""
    if exempt_note:
        text = without_staleness_note(text)
    return [
        f"{rel}: '{stale}' should be '{current}'"
        for stale, current in SUPERSEDED
        if superseded_pattern(stale).search(text)
    ]


TABLE_HEADER = "| Stage | Recommended | CLI commands |"


# Repo-level user-facing docs. Included because a rename or model refresh that
# lands only inside plugins/ leaves these contradicting it — the exact
# "renamed in one place" defect. `specs/`, `SENZING_BOOTCAMP_PLUGIN_FEEDBACK_*.md`,
# and `specs/IMPLEMENTED.md` are deliberately NOT scanned: they are historical
# records and must keep naming what was true when written.
REPO_DOCS = [
    os.path.join(REPO_ROOT, "README.md"),
    os.path.join(REPO_ROOT, "docs", "README.md"),
]


def shipped_markdown():
    """Every Markdown file under the shipped plugin, plus repo-level user docs."""
    for dirpath, dirnames, filenames in os.walk(PLUGIN):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)
    for path in REPO_DOCS:
        if os.path.exists(path):
            yield path


def stage_table(path):
    """Extract the per-stage recommendation table as a list of cell-tuples.

    Tolerates leading indentation: the ground-rules copy is nested inside a
    bullet, the model-selection copy sits at column zero.
    """
    with open(path, encoding="utf-8") as fh:
        lines = [line.strip() for line in fh]
    if TABLE_HEADER not in lines:
        raise AssertionError(f"per-stage table header not found in {path}")
    start = lines.index(TABLE_HEADER)
    rows = []
    for line in lines[start + 2:]:  # skip header + separator
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        if set("".join(cells)) <= {"-", ":"}:  # a second separator row
            continue
        rows.append(tuple(cells))
    if not rows:
        raise AssertionError(f"per-stage table in {path} has no rows")
    return rows


class NoSupersededModelReferences(unittest.TestCase):
    """A superseded model name would recommend downgrading — never ship one."""

    def test_no_superseded_names_or_ids(self):
        offenders = []
        for path in shipped_markdown():
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            rel = os.path.relpath(path, REPO_ROOT)
            offenders += superseded_offenders(
                rel, text, exempt_note=(path == STALENESS_NOTE_FILE)
            )
        self.assertEqual(
            offenders, [], "superseded model references found:\n  " + "\n  ".join(offenders)
        )

    def test_the_staleness_note_is_found_and_names_what_it_supersedes(self):
        """The exemption is earned: the note exists and is what explains the supersession."""
        with open(STALENESS_NOTE_FILE, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn(STALENESS_NOTE_MARKER, text)
        removed = len(text) - len(without_staleness_note(text))
        self.assertGreater(removed, 0, "the staleness-note block was not found")
        self.assertNotEqual(
            superseded_offenders("note", text), [],
            "the staleness note no longer names the superseded models, so the "
            "exemption is not exercised",
        )

    def test_switch_command_names_a_current_model(self):
        # The copy-pasteable switch command is a functional string: if the display
        # name moves without the ID, the pasted command selects the old model.
        with open(MODEL_SELECTION, encoding="utf-8") as fh:
            text = fh.read()
        for match in re.finditer(r"/model (claude-[a-z0-9-]+)", text):
            model_id = match.group(1)
            stale_ids = [stale for stale, _ in SUPERSEDED if stale == model_id]
            self.assertEqual(
                stale_ids, [], f"/model {model_id} names a superseded model"
            )


class SupersededMatcherRespectsVersionBoundaries(unittest.TestCase):
    """Negative controls for the matcher and the exemption, on synthetic text.

    Both directions are proven: the current names must pass, and each stale name
    must fail in every position a sentence can put it. A plain `stale in text`
    check fails the first half ("Opus 5" is inside "Opus 5.5"); a whole-file
    exemption fails the second half for model-selection.md.
    """

    def hits(self, text):
        return [stale for stale, _ in SUPERSEDED if superseded_pattern(stale).search(text)]

    def test_current_names_and_ids_do_not_match(self):
        for text in (
            "Opus 5.5, high effort", "Sonnet 5.5 / medium", "Fable 5.1 sits above",
            "`claude-opus-5-5`", "/model claude-sonnet-5-5", "claude-fable-5-1",
            "claude-opus-5-5[1m]", "anthropic.claude-opus-5-5",
        ):
            with self.subTest(text=text):
                self.assertEqual([], self.hits(text))

    def test_stale_display_names_match_at_every_boundary(self):
        for name in ("Opus 5", "Sonnet 5", "Fable 5"):
            for text in (f"{name}, high", f"{name} / high", f"run {name}.",
                         f"on {name}\n", f"**{name}**", f"({name})"):
                with self.subTest(text=text):
                    self.assertIn(name, self.hits(text))

    def test_stale_ids_match_at_every_boundary(self):
        for model_id in ("claude-opus-5", "claude-sonnet-5", "claude-fable-5"):
            for text in (f"`{model_id}`", f"/model {model_id} ", f"{model_id}[1m]",
                         f"--model {model_id}\n", f"{model_id}."):
                with self.subTest(text=text):
                    self.assertIn(model_id, self.hits(text))

    def test_the_old_substring_check_could_not_hold_the_new_rows(self):
        """Why the matcher changed: the substring test flags the current names."""
        current = "Opus 5.5 and Sonnet 5.5, `claude-opus-5-5`, Fable 5.1"
        self.assertTrue(any(stale in current for stale, _ in SUPERSEDED))
        self.assertEqual([], self.hits(current))

    def test_older_rows_still_match(self):
        self.assertIn("Opus 4.8", self.hits("Opus 4.8 at high"))
        self.assertIn("claude-opus-4-8", self.hits("`claude-opus-4-8`"))

    def test_the_exemption_covers_only_the_staleness_note(self):
        note = (
            f"{STALENESS_NOTE_MARKER} — re-verify.** Opus 5.5 superseded Opus 5\n"
            "> (`claude-opus-5`), now legacy.\n"
        )
        clean = "| Opus 5.5 (`claude-opus-5-5`) | High |\n\n" + note + "\nAfter the note.\n"
        self.assertEqual([], superseded_offenders("m.md", clean, exempt_note=True))
        for stale in ("Opus 5", "`claude-sonnet-5`"):
            for where in ("before", "after"):
                text = (f"{stale} row\n\n" + note) if where == "before" else (note + f"\n{stale} row\n")
                with self.subTest(stale=stale, where=where):
                    self.assertNotEqual(
                        [], superseded_offenders("m.md", text, exempt_note=True),
                        "a superseded name outside the staleness note must fail the guard",
                    )

    def test_a_missing_note_exempts_nothing(self):
        text = "> Opus 5 is mentioned in some other quote.\n"
        self.assertNotEqual([], superseded_offenders("m.md", text, exempt_note=True))

    def test_the_live_model_selection_file_fails_with_a_stale_tier_row(self):
        """The real file, with one superseded row put back into its tier table."""
        with open(MODEL_SELECTION, encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual([], superseded_offenders("m.md", text, exempt_note=True))
        stale = text.replace("| Opus 5.5 (`claude-opus-5-5`) |", "| Opus 5 (`claude-opus-5`) |", 1)
        self.assertNotEqual(stale, text, "the tier-table row was not found")
        self.assertNotEqual([], superseded_offenders("m.md", stale, exempt_note=True))


class StageTablesAgree(unittest.TestCase):
    """The operational table and the maintainer reference must not drift."""

    def test_tables_are_identical(self):
        self.assertEqual(
            stage_table(GROUND_RULES),
            stage_table(MODEL_SELECTION),
            "the per-stage model/effort tables in ground-rules.md and "
            "docs/model-selection.md have drifted — update both",
        )

    def test_every_row_names_a_model_and_an_effort(self):
        for stage, recommended, commands in stage_table(GROUND_RULES):
            self.assertTrue(stage, "a stage row has an empty stage name")
            self.assertIn("effort", recommended, f"{stage!r}: no effort named")
            self.assertIn("/model", commands, f"{stage!r}: no /model command")
            self.assertIn("/effort", commands, f"{stage!r}: no /effort command")


class EveryStageHasExactlyOneRecommendation(unittest.TestCase):
    """Total coverage, single-valued cells.

    Change detection compares this stage's recommendation against what the
    Bootcamper is running; where the current setting is undeterminable it falls
    back to the previous stage's row. Both need a value on each side, so a stage
    missing from the table leaves the comparison undefined — Entity Resolution
    Concepts was absent this way. And a cell offering two answers ("Sonnet 5.5,
    high effort (Opus if bespoke load code)") cannot be pinned into a verbatim
    switch question (INV-056) nor compared against a single current setting.
    """

    def setUp(self):
        self.rows = stage_table(GROUND_RULES)
        self.stages = [stage for stage, _, _ in self.rows]

    def test_every_canonical_module_has_a_row(self):
        # Parsed from bootcamp-preparation's module table — the one place display
        # names are canonical (INV-079) — so adding a module fails this until it
        # is rated.
        prep = os.path.join(PLUGIN, "skills", "bootcamp-preparation", "SKILL.md")
        with open(prep, encoding="utf-8") as fh:
            canonical = [
                m.group(1).strip()
                for m in re.finditer(
                    r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*[^|]+?\s*\|\s*`[a-z_]+`", fh.read(), re.M
                )
            ]
        self.assertTrue(canonical, "could not parse the canonical module table")
        missing = [name for name in canonical if name not in self.stages]
        self.assertEqual(
            [],
            missing,
            f"module(s) with no model/effort row: {missing}. Every stage the bootcamp "
            "can run needs one, including apparatus-exempt stages, so change "
            "detection always has a value to compare against.",
        )

    def test_onboarding_is_rated_too(self):
        """Not in the prep table, but it is a stage the nudge compares against."""
        self.assertIn("Onboarding", self.stages)

    def test_no_row_offers_a_conditional_recommendation(self):
        offenders = [
            f"{stage}: {recommended!r}"
            for stage, recommended, _ in self.rows
            if "(" in recommended or re.search(r"\bif\b|\bor\b", recommended)
        ]
        self.assertEqual(
            [],
            offenders,
            f"conditional recommendation(s): {offenders}. A row must name exactly one "
            "model and one effort — the nudge cannot resolve a condition at module "
            "start, and INV-056 requires the question be pinnable.",
        )

    def test_one_stage_per_row(self):
        """Grouped rows hid the sequence; the order is now readable down the column."""
        offenders = [stage for stage in self.stages if ";" in stage]
        self.assertEqual(
            [], offenders, f"row(s) still group several stages: {offenders}"
        )


class StalenessNotePresent(unittest.TestCase):
    """Point-in-time data must say so, with the date it was checked."""

    def test_note_carries_a_verification_date(self):
        with open(MODEL_SELECTION, encoding="utf-8") as fh:
            text = fh.read()
        self.assertRegex(
            text,
            r"last verified \d{4}-\d{2}-\d{2}",
            "docs/model-selection.md must carry a dated 'last verified' note",
        )


if __name__ == "__main__":
    unittest.main()
