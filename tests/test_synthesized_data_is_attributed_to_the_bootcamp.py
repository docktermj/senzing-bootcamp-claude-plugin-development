"""Guidance that attributes loaded data names synthesized data the bootcamp's (#694).

Enforces **INV-399**, registered by the maintainer 2026-10-20. ⚠️ It asserts what the shipped
text SAYS: that every block attributing loaded data names synthesized data the bootcamp's. It
**cannot** establish that a live turn uses the wording -- only ``dry-run`` phase 3 observes
that -- nor that the guide actually read ``provenance`` from ``config/data_sources.yaml``,
which is a runtime act no offline suite can see. An ``Enforced by`` clause naming this file is
therefore not a claim that any bootcamper was ever addressed correctly.

``module-07-query-visualize-discover/phase2-discover.md`` states a general rule: when a
loaded source records ``provenance: synthesized``, the data is the bootcamp's, not the
Bootcamper's -- say "the data the bootcamp generated", never "your data". When it shipped no
registered invariant stated it, and it cited **INV-239**, which governs what
bootcamp-generated source data must CONTAIN and says nothing about how the guide names
whose data it is. Its `DEFERRED INVARIANT` block was registered as INV-399 by the maintainer
2026-10-20.

⚠️ **Scope, measured rather than taken from the issue's wording.** Acceptance criterion 4
asks for a guard over "steps that branch on ``provenance: synthesized``". Measured over the
shipped subtree: **13** blocks branch on it and only **2** say anything about whose data it
is. The other 11 are Module 4 and Module 5 steps about *regenerating* synthesized data,
which this rule has nothing to say about -- so requiring the attribution at all 13 would
report 11 correct sentences, and a guard that reports correct prose is one its reader learns
to discount (INV-282).

So the site set is: a block that branches on ``provenance: synthesized`` **and** attributes
the loaded data to someone. Each such block must name the data the bootcamp's.

⚠️ This asserts what the shipped text SAYS. It **cannot** establish that a live turn uses
the wording -- only ``dry-run`` phase 3 observes that (INV-308).

**Widened by #753 to three sites the sweep above cannot see** -- registered as INV-399's dated
note of 2026-10-21, applied by the maintainer 2026-10-22. The sweep reads ``.md`` blocks that
name ``provenance: synthesized`` and an attribution phrase, so it saw none of these:

- **The Module 7 invocation of ``generate_discoveries_pdf.py``.** The script's cover subtitle
  defaults to ``COVER_SUBTITLE``, "What Senzing found in your data", and Module 7 called it with
  no flag, so a generated scenario's keepsake contradicted its own first paragraph. The guard
  now requires the three-case branch (all synthesized / some / none) in the block directly
  before that fence, and each case's subtitle exactly; the "none" row must quote the script's
  default as the script states it, so the two cannot drift apart. The default itself stays
  "your data", which ``tests/test_discoveries_pdf.py`` pins.
- **The script's default, ``COVER_SUBTITLE``.** Read from the script by ``ast``, not copied
  here, and each row's flag is run through the script to confirm its cover carries it.
- **The results app's Match Keys copy in ``senzing_viz_server.py``.** The same server shows
  Module 3b's Truth Set, which is not the Bootcamper's data either, and the static page has no
  provenance input, so the copy is provenance-neutral: "across the loaded data". No line of the
  server outside a comment may say "your data".

⛔ (INV-300) The table before the invocation is the one statement of the two generated-case
subtitles (a check grafted from #753's race approach B): neither may be quoted in any other
shipped Markdown block, so a second copy cannot drift from the mapping. A prose sentence that
needs the mapping links ``#discoveries-cover-subtitle`` instead. The default is not in that
scan: it is the script's own ``COVER_SUBTITLE``, and graduation quotes it, correctly, as
``generate_document_pdf.py``'s default.

**Widened by #790 to every quoted or pinned "your data".** The sweep above sees a line only when
its block already branches on ``provenance: synthesized``, so Module 7 step 5's summary, step
7's fallback, Module 5's quality gate and Module 6 Phase C's dependency question said "your
data" on every provenance with nothing to report it. ``attribution_problems`` reads every
"your data" in shipped Markdown (``_corpus.corpus_files``) that is inside double quotes, on a
``>`` line, inside a 👉 question's bold text, or anywhere in sample output under
``docs/examples/``. Each passes only if its step reads ``provenance`` **and** names the
generated case (INV-399's names, Module 5's "The generated data's quality", or a link to
``#discoveries-cover-subtitle``), or if it is on ``EXEMPT``, keyed by file and phrase with a
reason. Reading ``provenance`` alone is not enough: Module 5 read it for the INV-345 disclosure
and still said "Your data quality" on every band, which is the defect. "Its step" is decided by
``step_of``: the nearest enclosing numbered step, else the nearest ``**Step N`` label, else the
heading-delimited section, and never a sibling's read.

Module 5's and Phase C's ``synthesized`` variants are pinned verbatim here (INV-056). ⚠️ As
above, this asserts what the shipped text says; that a live guide reads ``provenance`` before
choosing the wording is observable only in ``dry-run`` phase 3 (INV-308).
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks, line_of

#: A step branching on the provenance value the rule is about.
_SYNTHESIZED = re.compile(r"provenance:?\s*`?synthesized")

#: The block says whose data it is. Without this the sweep reaches the 11 regeneration
#: steps, which attribute nothing.
_ATTRIBUTES = re.compile(
    r"(?i)\byour data\b|\bthe Bootcamper's data\b|data the bootcamp generated|the data is the bootcamp")

#: What such a block must carry: the data named as the bootcamp's.
#:
#: ⚠️ A bare "generated data" is deliberately NOT accepted. Both shipped sites say it for a
#: different reason -- naming a defect in the data -- several sentences after the attribution,
#: so accepting it let a block pass with the attribution removed. The control caught that: it
#: mutated the rule away and the guard still reported nothing.
_NAMES_THE_BOOTCAMP = re.compile(
    r"(?i)data the bootcamp generated|the data is the bootcamp")


def sites(paths):
    """``(path, line, flat)`` for every block that branches on synthesized AND attributes."""
    found = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "synthesized" not in text:
            continue
        for flat, origin in collapsed_blocks(text):
            hit = _SYNTHESIZED.search(flat)
            if hit and _ATTRIBUTES.search(flat):
                found.append((path, line_of(origin, hit.start()), flat))
    return found


def offenders(paths):
    return [(p, n) for p, n, flat in sites(paths) if not _NAMES_THE_BOOTCAMP.search(flat)]


class SynthesizedDataIsNamedTheBootcampsWhereverDataIsAttributed(unittest.TestCase):
    def setUp(self):
        self.shipped = corpus_files("plugins", suffixes=(".md",))

    def test_the_sweep_finds_the_sites_it_is_written_for(self):
        """⛔ (INV-265) A floor: an empty match must not read as a clean result."""
        found = sites(self.shipped)
        self.assertGreaterEqual(
            len(found), 2,
            "the sweep found %d attributing blocks; it is written for at least the general "
            "rule and its narrow sibling, so a smaller number means the scan broke" % len(found))
        names = {p.name for p, _, _ in found}
        self.assertIn("phase2-discover.md", names)

    def test_the_sweep_is_narrower_than_every_synthesized_branch(self):
        """The measurement that set the scope, pinned so a later widening is deliberate."""
        branching = 0
        for path in self.shipped:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "synthesized" not in text:
                continue
            branching += sum(1 for flat, _ in collapsed_blocks(text) if _SYNTHESIZED.search(flat))
        attributing = len(sites(self.shipped))
        self.assertLess(
            attributing, branching,
            "every block branching on provenance: synthesized now attributes data; if that is "
            "real the scope note in this file's docstring needs rewriting, not the assertion")

    def test_no_attributing_block_leaves_the_data_the_bootcampers(self):
        found = offenders(self.shipped)
        self.assertEqual(
            [], found,
            "shipped guidance attributes loaded data without naming synthesized data the "
            "bootcamp's:\n" + "\n".join("  %s:%d" % (p, n) for p, n in found))


class TheControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs the SAME function over mutated shipped text."""

    def setUp(self):
        self.path = (Path(__file__).resolve().parent.parent / "plugins" / "senzing-bootcamp"
                     / "skills" / "module-07-query-visualize-discover" / "phase2-discover.md")

    def _reported(self, text):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d) / "phase2-discover.md"
            tmp.write_text(text, encoding="utf-8")
            return offenders([tmp])

    def test_dropping_the_attribution_is_reported(self):
        """The defect this guard exists for: the rule's own site, attribution removed."""
        text = self.path.read_text(encoding="utf-8")
        stripped = text.replace(
            'the data is the\n   bootcamp\'s, not the Bootcamper\'s.** Say "the data the bootcamp '
            'generated", never "your data".',
            "this is your data.**", 1)
        self.assertNotEqual(stripped, text, "the rule's wording was not found to mutate")
        self.assertTrue(
            self._reported(stripped),
            "dropping the attribution is not reported; the control is vacuous")

    def test_the_shipped_text_is_not_reported(self):
        self.assertEqual([], self._reported(self.path.read_text(encoding="utf-8")))


_PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "senzing-bootcamp"
PHASE1 = _PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
GENERATOR = _PLUGIN / "scripts" / "generate_discoveries_pdf.py"
VIZ_SERVER = _PLUGIN / "scripts" / "senzing_viz_server.py"

#: The subtitle each provenance case passes (#753, spec revision 1).
ALL_SYNTHESIZED = "What Senzing found in the data the bootcamp generated"
SOME_SYNTHESIZED = "What Senzing found in the loaded data"

#: The fence line that runs the generator, the one INV-185 resolves through the plugin root.
_INVOCATION = '"${CLAUDE_PLUGIN_ROOT}/scripts/generate_discoveries_pdf.py"'


def script_default():
    """``COVER_SUBTITLE`` as the generator states it, read by ``ast`` rather than copied."""
    import ast
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and any(getattr(t, "id", "") == "COVER_SUBTITLE" for t in node.targets)):
            return node.value.value
    raise AssertionError("generate_discoveries_pdf.py states no COVER_SUBTITLE")


def _mapping_span(lines):
    """``(start, at)``: the 0-based first line of the block directly before the invocation
    fence, and the invocation's own line; ``None`` when no invocation is found."""
    at = next((i for i, line in enumerate(lines) if _INVOCATION in line), None)
    if at is None:
        return None
    start = at - 1  # the fence's opening line
    while start > 0 and (not lines[start - 1].strip() or lines[start - 1].lstrip().startswith("|")):
        start -= 1
    return start, at


def restatements(paths):
    """``(path, line)`` for each generated-case subtitle in shipped Markdown outside the mapping.

    ⛔ (INV-300) The mapping is the table directly before the invocation in ``PHASE1``; a
    subtitle quoted anywhere else is a second copy that can drift from it. Only the two
    generated-case lines are owned by the mapping alone: the default is ``COVER_SUBTITLE``, the
    script's own, and graduation quotes it for a different script on purpose. Read through
    ``collapsed_blocks``, so a subtitle wrapped across two lines is still found (INV-346).
    Grafted from #753's race approach B, adapted to the table's location.
    """
    found = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        mapping = range(0)
        if path.name == PHASE1.name:
            span = _mapping_span(text.splitlines())
            if span is not None:
                mapping = range(span[0] + 1, span[1])  # 1-based lines of the table block
        for flat, origin in collapsed_blocks(text):
            for subtitle in (ALL_SYNTHESIZED, SOME_SYNTHESIZED):
                at = flat.find(subtitle)
                while at >= 0:
                    line = line_of(origin, at)
                    if line not in mapping:
                        found.append((path, line))
                    at = flat.find(subtitle, at + 1)
    return found


def cover_rows(text):
    """``{case: pass cell}`` from the table directly before the invocation fence.

    "Directly before" means only blank lines and table rows lie between the table and the
    fence's opening line, so a table moved elsewhere in the file, or left behind when the
    invocation moves, is not read as the branch.
    """
    lines = text.splitlines()
    span = _mapping_span(lines)
    if span is None:
        return None, None
    start, at = span
    rows = {}
    for line in lines[start:at - 1]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and len(cells) == 2:
            case = cells[0].split()[0].lower() if cells[0] else ""
            if case in ("all", "some", "none") and "synthesized" in cells[0]:
                rows[case] = cells[1]
    return rows, lines[at]


def cover_branch_problems(text, default):
    rows, invocation = cover_rows(text)
    if rows is None:
        return ["no %s invocation found" % _INVOCATION]
    problems = []
    for case, subtitle in (("all", ALL_SYNTHESIZED), ("some", SOME_SYNTHESIZED)):
        cell = rows.get(case)
        if cell is None:
            problems.append("no '%s synthesized' row before the invocation" % case)
        elif '--subtitle "%s"' % subtitle not in cell:
            problems.append("the '%s synthesized' row does not pass --subtitle \"%s\""
                            % (case, subtitle))
    none = rows.get("none")
    if none is None:
        problems.append("no 'none synthesized' row before the invocation")
    elif '--subtitle "' in none or '"%s"' % default not in none:
        problems.append("the 'none synthesized' row must pass no subtitle and quote the "
                        "script's default \"%s\"" % default)
    if "--subtitle" not in invocation:
        problems.append("the invocation line passes no --subtitle")
    return problems


def viz_copy_problems(text):
    """Lines of the results app that call the loaded data the Bootcamper's, outside a comment."""
    problems = []
    for number, line in enumerate(text.splitlines(), 1):
        code = line.strip()
        if code.startswith(("#", "//")):
            continue
        if re.search(r"(?i)\byour data\b", code):
            problems.append("line %d says \"your data\"" % number)
    copy = re.search(r'async function drawMatchKeys\(\).*?append\("p"\)\.html\("([^"]*)"\)', text, re.S)
    if not copy or "across the loaded data" not in copy.group(1):
        problems.append("the Match Keys copy does not say \"across the loaded data\"")
    return problems


class TheDiscoveriesCoverFollowsProvenance(unittest.TestCase):
    """#753: the Module 7 invocation branches the cover subtitle on provenance."""

    def test_the_default_still_names_the_bootcampers_data(self):
        """Why the branch is required: the script's own default says "your data"."""
        self.assertRegex(script_default(), r"(?i)\byour data\b")

    def test_the_invocation_carries_the_three_case_branch(self):
        problems = cover_branch_problems(PHASE1.read_text(encoding="utf-8"), script_default())
        self.assertEqual([], problems, "\n".join(problems))

    def test_no_subtitle_is_restated_outside_the_mapping(self):
        """⛔ (INV-300) The table is the one statement of each cover subtitle."""
        found = restatements(corpus_files("plugins", suffixes=(".md",)))
        self.assertEqual(
            [], found,
            "a generated-case cover subtitle is restated outside the table before the invocation in %s; "
            "link #discoveries-cover-subtitle instead (INV-300):\n" % PHASE1.name
            + "\n".join("  %s:%d" % (p, n) for p, n in found))

    def test_each_rows_subtitle_reaches_the_cover(self):
        """The flag each row names, run through the script: the cover carries it."""
        import shlex
        import tempfile
        from test_discoveries_pdf import GOOD_DOC, pdf_text, run, write_doc
        rows, _ = cover_rows(PHASE1.read_text(encoding="utf-8"))
        expected = {"all": ALL_SYNTHESIZED, "some": SOME_SYNTHESIZED, "none": script_default()}
        for case, subtitle in expected.items():
            with self.subTest(case=case):
                flag = re.search(r'--subtitle "[^"]*"', rows[case])
                args = shlex.split(flag.group(0)) if flag else []
                with tempfile.TemporaryDirectory() as tmp:
                    write_doc(tmp, GOOD_DOC)
                    out = str(Path("docs") / "d.pdf")
                    result = run(args + ["--output", out], tmp)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertIn(subtitle, pdf_text(str(Path(tmp) / out)))

    def test_the_match_keys_copy_is_provenance_neutral(self):
        problems = viz_copy_problems(VIZ_SERVER.read_text(encoding="utf-8"))
        self.assertEqual([], problems, "\n".join(problems))


class TheCoverControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs the SAME function over mutated shipped text."""

    def setUp(self):
        self.text = PHASE1.read_text(encoding="utf-8")
        self.default = script_default()

    def _mutated(self, old, new=""):
        mutated = self.text.replace(old, new, 1)
        self.assertNotEqual(mutated, self.text, "%r was not found to mutate" % old)
        return cover_branch_problems(mutated, self.default)

    def test_removing_the_branch_is_reported(self):
        rows = [line for line in self.text.splitlines(keepends=True)
                if line.startswith("| All `synthesized`") or line.startswith("| Some `")
                or line.startswith("| None `") or line.startswith("| Loaded sources")
                or line.startswith("|---|---|\n")]
        self.assertGreaterEqual(len(rows), 4, "the branch table was not found to remove")
        mutated = self.text
        for row in rows:
            mutated = mutated.replace(row, "", 1)
        self.assertTrue(cover_branch_problems(mutated, self.default),
                        "removing the branch is not reported; the control is vacuous")

    def test_each_case_is_required(self):
        for case in ("| All `synthesized`", "| Some `synthesized`", "| None `synthesized`"):
            with self.subTest(case=case):
                row = next(line for line in self.text.splitlines(keepends=True)
                           if line.startswith(case))
                self.assertTrue(self._mutated(row), "dropping %r is not reported" % case)

    def test_the_old_flagless_invocation_is_reported(self):
        self.assertTrue(self._mutated(' --subtitle "<the table\'s subtitle>"'))

    def test_the_all_case_saying_your_data_is_reported(self):
        self.assertTrue(self._mutated(
            '`--subtitle "%s"`' % ALL_SYNTHESIZED, '`--subtitle "%s"`' % self.default))

    def test_a_table_away_from_the_invocation_is_not_read_as_the_branch(self):
        fence = self.text.index("```bash\n" + 'python3 ' + _INVOCATION)
        moved = self.text[:fence] + "A paragraph between the table and the fence.\n\n" + self.text[fence:]
        self.assertTrue(cover_branch_problems(moved, self.default))

    def test_a_drifted_default_is_reported(self):
        self.assertTrue(cover_branch_problems(self.text, "What Senzing found in the records"))

    def test_a_restated_subtitle_is_reported(self):
        """The shipped file with one subtitle quoted again, wrapped mid-phrase, below the fence."""
        import tempfile
        restated = self.text + '\nPass `--subtitle "What Senzing found in the\nloaded data"`.\n'
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d) / PHASE1.name
            copy.write_text(restated, encoding="utf-8")
            self.assertEqual([(copy, len(self.text.splitlines()) + 2)],
                             restatements([copy]))
            other = Path(d) / "elsewhere.md"
            other.write_text('A generated cover says "%s".\n' % ALL_SYNTHESIZED, encoding="utf-8")
            self.assertEqual([(other, 1)], restatements([other]))
            copy.write_text(self.text, encoding="utf-8")
            self.assertEqual([], restatements([copy]),
                             "the mapping itself must not be reported")

    def test_the_old_match_keys_copy_is_reported(self):
        text = VIZ_SERVER.read_text(encoding="utf-8")
        old = text.replace("across the loaded data", "across your data", 1)
        self.assertNotEqual(old, text, "the Match Keys copy was not found to mutate")
        self.assertTrue(viz_copy_problems(old))

    def test_a_comment_quoting_your_data_is_not_reported(self):
        self.assertEqual(
            ["the Match Keys copy does not say \"across the loaded data\""],
            viz_copy_problems('# nothing in your data has that name\n  // your data\n'))


# --- #790: every quoted or pinned "your data" line in shipped Markdown -----------------------

#: The phrase INV-399 forbids for synthesized data.
_YOUR_DATA = re.compile(r"(?i)\byour data\b")
#: A double-quoted span inside one collapsed block, straight or curly.
_QUOTED = re.compile(r'"[^"]*"|“[^”]*”')
#: A pinned question: the bold text after a 👉.
_PINNED = re.compile(r"👉\s*\*\*.*?\*\*")
#: Sample output under ``docs/examples/``: every line of it is text a Bootcamper reads.
_SAMPLE_OUTPUT = "docs/examples/"
#: The unit reads the registry field the wording turns on ...
_READS_PROVENANCE = re.compile(r"`provenance\b")
#: ... and names the generated case: one of INV-399's names for it, Module 5's pinned "The
#: generated data's quality", or a link to the table that maps the three cases.
_NAMES_THE_GENERATED_CASE = re.compile(
    r"(?i)\bthe bootcamp generated\b|\bthe generated data's\b|\bthe data is the bootcamp|"
    r"#discoveries-cover-subtitle")

_NUMBERED_STEP = re.compile(r"^([ \t]*)\d+[.)][ \t]")
_STEP_LABEL = re.compile(r"^\*\*Step \d+[a-z]?\b")
_HEADING_LINE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
_FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")

#: ⛔ (INV-399) The reviewed exemptions: ``(file under the plugin root, phrase, reason)``. A
#: phrase exempts a "your data" only in its own file and only where the phrase covers it, so a
#: key is text, never a line number, and a copy elsewhere is still reported.
EXEMPT = (
    ("skills/module-01-business-problem/phase2-document-confirm.md",
     "diagrams of your data architecture",
     "the Bootcamper's own systems: their architecture, not the loaded data"),
    ("skills/graduation/SKILL.md", "I'll draft one from your data",
     "future data: the Next-time question asks what they build next on their own data"),
    ("skills/module-02-sdk-setup/SKILL.md", "where your data volume is known",
     "future data: the sentence opens \"If your own data later exceeds the evaluation limit\"; "
     "#790 leaves this line out of scope, and it sits inside a quoted statement, so the scan "
     "sees it"),
    ("skills/module-05-data-quality-mapping/phase1-quality-assessment.md",
     '"Your data is fine, shall we continue?"',
     "a quoted counter-example: the question the ≥80% branch must not invent"),
    ("skills/module-05-data-quality-mapping/phase2-data-mapping.md", '"your data is wrong"',
     "a quoted counter-example: the reading the step rejects"),
    ("skills/module-07-query-visualize-discover/phase1-query-visualize.md",
     'never as "not in your data"', "a quoted counter-example: the report the step forbids"),
    ("skills/graduation/SKILL.md", 'the discoveries line, "What Senzing found in your data"',
     "a quoted counter-example: the default subtitle that is wrong on these documents"),
    ("skills/module-07-query-visualize-discover/phase1-query-visualize.md",
     "refine your data mapping",
     "the Bootcamper's own mapping work, theirs even on a generated scenario"),
    ("skills/module-07-query-visualize-discover/phase1-query-visualize.md",
     'the default, "What Senzing found in your data"',
     "the cover table's default cell: a run with no synthesized source"),
    ("docs/examples/bootcamp_recap.example.md", "No entity in your data spans more sources",
     "a run with no synthesized source: sample output of a CORD-backed run"),
    ("docs/examples/bootcamp_recap.example.md",
     "the offline interactive app pointed at your data",
     "a run with no synthesized source: sample output of a CORD-backed run"),
    ("skills/module-07-query-visualize-discover/phase1-query-visualize.md",
     "What do you want to find out about your data?", "the pinned Discover question"),
    ("docs/examples/bootcamp_recap.example.md",
     "What do you want to find out about your data?",
     "the pinned Discover question, quoted in the sample recap"),
)


def _content_lines(lines):
    """A flag per line: True for a line inside a fenced code block, the fence lines excluded."""
    out, opener = [], None
    for line in lines:
        fence = _FENCE_LINE.match(line)
        if opener is None:
            out.append(False)
            if fence:
                opener = fence.group(1)[0]
        elif fence and fence.group(1)[0] == opener:
            out.append(False)
            opener = None
        else:
            out.append(True)
    return out


def _indent(line):
    return len(line) - len(line.lstrip())


def step_of(lines, index):
    """``(first, last)``, 0-based and inclusive: the unit that decides whether the line at
    ``index`` sits in a step that reads ``provenance``.

    1. **The nearest enclosing numbered step**: the ``N.`` list item that holds the line, from
       its marker to the next line at its indent or less (a sibling, a dedent) or a heading.
       Its sub-items and indented paragraphs are inside it; a sibling step is not.
    2. Otherwise, **the nearest bold step label** above it in its section (a line opening with
       ``**Step N``), up to the next label or heading.
    3. Otherwise, **its heading-delimited section**: the nearest heading above it (any level)
       to the line before the next heading.

    ⚠️ The nearest unit is decided strictly: a step that does not read ``provenance`` never
    borrows the read of its sibling or of the section around it. That is what makes the
    restored "your data" at Module 7 step 5 a failure while step 6 reads ``provenance``.
    """
    fenced = _content_lines(lines)

    def heading(i):
        return not fenced[i] and _HEADING_LINE.match(lines[i])

    def item_end(start):
        last, ind = start, _indent(lines[start])
        for j in range(start + 1, len(lines)):
            if not lines[j].strip():
                continue
            if not fenced[j] and (heading(j) or _indent(lines[j]) <= ind):
                break
            last = j
        return last

    at = index
    while at > 0 and fenced[at]:
        at -= 1  # a line of a fenced block is placed by its opening fence
    limit = None
    for i in range(at, -1, -1):
        if not lines[i].strip() or fenced[i]:
            continue
        if heading(i):
            break
        ind = _indent(lines[i])
        if limit is None or ind < limit:
            if _NUMBERED_STEP.match(lines[i]):
                return i, item_end(i)
            limit = ind
            if limit == 0 and i != at:
                break
    top = next((i for i in range(at, -1, -1) if heading(i)), -1)
    bottom = next((i for i in range(at + 1, len(lines)) if heading(i)), len(lines))
    label = next((i for i in range(at, top, -1)
                  if not fenced[i] and _STEP_LABEL.match(lines[i])), None)
    if label is not None:
        end = next((i for i in range(label + 1, bottom)
                    if not fenced[i] and _STEP_LABEL.match(lines[i])), bottom)
        return label, end - 1
    return max(top, 0), bottom - 1


def _inside(pattern, flat, at):
    return any(m.start() <= at < m.end() for m in pattern.finditer(flat))


def candidates(rel, text):
    """``(line, flat, at)`` for each quoted or pinned "your data" in one shipped file.

    Quoted or pinned means: inside a double-quoted span, on a ``>`` blockquote line, inside a
    👉 question's bold text, or anywhere in sample output under ``docs/examples/``. Read
    through ``collapsed_blocks``, so a phrase or a quote wrapped across lines is still seen
    (INV-346).
    """
    raw = text.splitlines()
    sample = rel.startswith(_SAMPLE_OUTPUT)
    found = []
    for flat, origin in collapsed_blocks(text):
        for m in _YOUR_DATA.finditer(flat):
            line = line_of(origin, m.start())
            if (sample or _inside(_QUOTED, flat, m.start()) or _inside(_PINNED, flat, m.start())
                    or raw[line - 1].lstrip().startswith(">")):
                found.append((line, flat, m.start()))
    return found


def exemption_for(rel, flat, at, exempt=EXEMPT):
    """The ``EXEMPT`` entry whose phrase covers ``flat[at]`` in file ``rel``, or None."""
    for entry in exempt:
        path, phrase, _ = entry
        if path != rel:
            continue
        i = flat.find(phrase)
        while i >= 0:
            if i <= at < i + len(phrase):
                return entry
            i = flat.find(phrase, i + 1)
    return None


def attribution_problems(paths, root=_PLUGIN, exempt=EXEMPT):
    """``(problems, used)``: each ``(rel, line)`` whose quoted or pinned "your data" is neither
    exempt nor in a step that reads ``provenance`` and names the generated case; and the
    exemptions that matched something."""
    problems, used = [], set()
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not _YOUR_DATA.search(text):
            continue
        rel = path.relative_to(root).as_posix()
        lines = text.splitlines()
        for line, flat, at in candidates(rel, text):
            entry = exemption_for(rel, flat, at, exempt)
            if entry is not None:
                used.add(entry)
                continue
            first, last = step_of(lines, line - 1)
            unit = " ".join(" ".join(lines[first:last + 1]).split())
            if _READS_PROVENANCE.search(unit) and _NAMES_THE_GENERATED_CASE.search(unit):
                continue
            problems.append((rel, line))
    return problems, used


def _shipped():
    return corpus_files("plugins/senzing-bootcamp", suffixes=(".md",))


MODULE5 = _PLUGIN / "skills" / "module-05-data-quality-mapping" / "phase1-quality-assessment.md"
PHASE_C = _PLUGIN / "skills" / "module-06-data-processing" / "phaseC-multi-source.md"
DISCOVER = _PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase2-discover.md"
DISCOVER_B = _PLUGIN / "skills" / "module-07-query-visualize-discover" / "phase2b-discover.md"


class EveryQuotedYourDataFollowsProvenance(unittest.TestCase):
    """#790: the guard reads every quoted or pinned "your data", not only branched blocks."""

    def test_the_shipped_tree_passes_with_only_the_reviewed_exemptions(self):
        problems, _ = attribution_problems(_shipped())
        self.assertEqual(
            [], problems,
            "a quoted or pinned \"your data\" sits in a step that does not read `provenance` "
            "and name the generated case (INV-399); give it the subtitle table's row or a "
            "provenance-selected variant, or, if the data really is the Bootcamper's, add it to "
            "EXEMPT with a reason:\n" + "\n".join("  %s:%d" % p for p in problems))

    def test_every_exemption_still_matches_a_line(self):
        """A stale exemption is reported, so the list cannot outlive the text it reviewed."""
        _, used = attribution_problems(_shipped())
        self.assertEqual([], [e[:2] for e in EXEMPT if e not in used])

    def test_every_exemption_names_a_phrase_and_a_reason(self):
        for path, phrase, reason in EXEMPT:
            with self.subTest(path=path, phrase=phrase):
                self.assertRegex(phrase, _YOUR_DATA)
                self.assertTrue(reason.strip())
                self.assertTrue((_PLUGIN / path).is_file(), path)

    def test_the_scan_reaches_the_steps_it_is_written_for(self):
        """⛔ (INV-265) A floor: the provenance-reading steps are among the candidates."""
        seen = set()
        for path in (MODULE5, PHASE_C, DISCOVER, DISCOVER_B):
            rel = path.relative_to(_PLUGIN).as_posix()
            if candidates(rel, path.read_text(encoding="utf-8")):
                seen.add(path.name)
        self.assertEqual({MODULE5.name, PHASE_C.name, DISCOVER.name, DISCOVER_B.name}, seen)
        total = sum(len(candidates(p.relative_to(_PLUGIN).as_posix(),
                                   p.read_text(encoding="utf-8"))) for p in _shipped())
        self.assertGreaterEqual(total, 25, "the scan found %d candidates; it broke" % total)


class TheWidenedGuardsControls(unittest.TestCase):
    """⛔ (INV-265) Each control runs ``attribution_problems`` over mutated shipped text."""

    def _problems(self, path, text):
        import tempfile
        rel = path.relative_to(_PLUGIN)
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d).joinpath(*rel.parts)
            copy.parent.mkdir(parents=True)
            copy.write_text(text, encoding="utf-8")
            return attribution_problems([copy], root=Path(d))[0]

    def _cut(self, path, start, end):
        text = path.read_text(encoding="utf-8")
        i = text.index(start)
        return text[:i] + text[text.index(end, i):]

    def test_the_shipped_files_are_not_reported(self):
        for path in (MODULE5, PHASE_C, DISCOVER, DISCOVER_B):
            with self.subTest(path=path.name):
                self.assertEqual([], self._problems(path, path.read_text(encoding="utf-8")))

    def test_your_data_restored_at_module_7_step_5_is_reported(self):
        """Step 6 reads `provenance`; step 5 does not, and must not borrow its sibling's read."""
        text = DISCOVER.read_text(encoding="utf-8")
        restored = re.sub(r'relationships in \[the data\]\."[\s\S]*?\(INV-399\)\. List',
                          'relationships in your data." List', text, count=1)
        self.assertNotEqual(text, restored, "step 5's summary was not found to mutate")
        line = restored[:restored.index('in your data." List')].count("\n") + 1
        self.assertEqual([(DISCOVER.relative_to(_PLUGIN).as_posix(), line)],
                         self._problems(DISCOVER, restored))

    def test_removing_module_5_step_7s_variant_is_reported(self):
        mutated = self._cut(MODULE5, "**`provenance` selects each band's wording",
                            "*(Internal: in the two gating branches")
        lines = mutated.splitlines()
        gate = next(i for i, l in enumerate(lines) if l.startswith("### Quality gate")) + 1
        step7a = next(i for i, l in enumerate(lines) if l.startswith("### 7a.")) + 1
        found = self._problems(MODULE5, mutated)
        self.assertTrue(found, "removing Step 7's synthesized variant is not reported")
        self.assertTrue(all(gate < n < step7a for _, n in found), found)

    def test_removing_module_5_step_7bs_variant_is_reported(self):
        mutated = self._cut(MODULE5, "**On a `synthesized` source, the band's form is its",
                            "*(Internal: end the turn on the applicable question and wait.)*")
        lines = mutated.splitlines()
        step7b = next(i for i, l in enumerate(lines) if l.startswith("### 7b.")) + 1
        found = self._problems(MODULE5, mutated)
        self.assertTrue(found, "removing Step 7b's synthesized variant is not reported")
        self.assertTrue(all(n > step7b for _, n in found), found)

    def test_removing_phase_cs_variants_is_reported(self):
        mutated = self._cut(PHASE_C, "Only when some sources being loaded are `synthesized`",
                            "*(Internal: end the turn on this question and wait.)* On **yes**")
        self.assertTrue(self._problems(PHASE_C, mutated))

    def test_a_new_quoted_line_is_reported_and_an_exemption_is_keyed_by_file(self):
        import tempfile
        fixture = ("# A step\n\nSay: \"Senzing found 3 matches in your\ndata.\"\n\n"
                   "> What do you want to find out about your data?\n\n"
                   "👉 **Shall we look at your data?**\n\n"
                   "Prose that says your data, unquoted, is not read.\n")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "skills" / "elsewhere.md"
            path.parent.mkdir()
            path.write_text(fixture, encoding="utf-8")
            problems, used = attribution_problems([path], root=Path(d))
        self.assertEqual([("skills/elsewhere.md", 3), ("skills/elsewhere.md", 6),
                          ("skills/elsewhere.md", 8)], problems)
        self.assertEqual(set(), used, "an exemption leaked to a file it does not name")

    def test_the_unit_is_the_nearest_step_then_the_section(self):
        lines = ("# Section\n\nIntro reads `provenance`.\n\n"
                 "1. **First:** \"in your data\"\n"
                 "   continued.\n\n"
                 "   - a sub-bullet\n\n"
                 "     indented under it.\n"
                 "2. **Second** reads `provenance`.\n\n"
                 "After the list.\n\n"
                 "**Step 3:** a bold label\n\nits text.\n\n"
                 "**Step 4:** the next label\n\n"
                 "## Next\n").splitlines()
        self.assertEqual((4, 9), step_of(lines, 4))
        self.assertEqual((4, 9), step_of(lines, 9))
        self.assertEqual((10, 10), step_of(lines, 10))
        self.assertEqual((0, 19), step_of(lines, 12))
        self.assertEqual((14, 17), step_of(lines, 16))
        self.assertEqual((18, 19), step_of(lines, 18))


class TheGeneratedDataVariantsArePinned(unittest.TestCase):
    """#790: Module 5's `synthesized` variants and Module 6 Phase C's, verbatim (INV-056)."""

    STEP7 = (
        '"The generated data\'s quality is strong. Let\'s continue to mapping."',
        '"The generated data\'s quality is acceptable but has some gaps. You can continue to '
        'mapping now, or improve the weakest fields first."',
        "👉 **The generated data's quality is acceptable but has some gaps. What would you like "
        "to do? Reply with a number:**",
        '"The generated data\'s quality needs attention before mapping will produce good '
        "results. I'd recommend focusing on [specific issues: e.g., filling missing phone "
        'numbers, standardizing address formats]."',
        "👉 **The generated data's quality needs attention before mapping will produce good "
        "results. What would you like to do? Reply with a number:**",
    )
    STEP7B = (
        '"The generated data\'s quality is acceptable but has some gaps. What is left is '
        "missing values, which this module cannot fill; a better export, or a regeneration of "
        'generated data, can."',
        "👉 **The generated data's quality is acceptable but has some gaps. What would you like "
        "to do? Reply with a number:**",
        '"The generated data\'s quality needs attention before mapping will produce good '
        "results. What is left is missing values, which this module cannot fill; a better "
        'export, or a regeneration of generated data, can."',
        "👉 **The generated data's quality needs attention before mapping will produce good "
        "results. What would you like to do? Reply with a number:**",
    )
    PHASE_C = (
        "👉 **Are there load-order dependencies between your data sources?**",
        "👉 **Are there load-order dependencies between the loaded data sources?**",
        "👉 **Are there load-order dependencies between the data sources the bootcamp "
        "generated?**",
    )

    def setUp(self):
        text = MODULE5.read_text(encoding="utf-8")
        gate = text.index("### Quality gate")
        step7b = text.index("### 7b.")
        self.step7 = text[gate:text.index("### 7a.", gate)]
        self.step7b = text[step7b:text.index("<a id=\"the-return-route\"></a>", step7b)]
        phase_c = PHASE_C.read_text(encoding="utf-8")
        i = phase_c.index("## 13. ")
        self.step13 = phase_c[i:phase_c.index("## 14. ", i)]

    @staticmethod
    def _flat(text):
        return " ".join(text.split())

    def test_each_variant_is_pinned_where_its_band_is(self):
        for name, block, variants in (("Step 7", self.step7, self.STEP7),
                                      ("Step 7b", self.step7b, self.STEP7B),
                                      ("Phase C step 13", self.step13, self.PHASE_C)):
            for variant in variants:
                with self.subTest(block=name, variant=variant[:60]):
                    self.assertIn(variant, self._flat(block))

    def test_each_variant_is_its_band_with_only_the_owner_changed(self):
        """The existing pinned text stays, for every other provenance."""
        for block, variants in ((self.step7, self.STEP7), (self.step7b, self.STEP7B)):
            for variant in variants:
                with self.subTest(variant=variant[:60]):
                    existing = variant.replace("The generated data's quality", "Your data quality")
                    self.assertIn(existing, self._flat(block))
                    self.assertLess(self._flat(block).index(existing),
                                    self._flat(block).index(variant),
                                    "the existing pinned text no longer stands first")

    def test_each_synthesized_question_keeps_its_bands_options(self):
        from test_no_progress_gate_returns_to_data_collection import options_after
        for block in (self.step7, self.step7b):
            for variant in (v for v in self.STEP7 if v.startswith("👉")):
                existing = variant.replace("The generated data's quality", "Your data quality")
                with self.subTest(variant=variant[:60]):
                    mine = options_after(block, variant)
                    theirs = options_after(block, existing)
                    self.assertEqual(1, len(mine))
                    self.assertEqual(theirs, mine)

    def test_each_selection_states_its_default(self):
        """A missing `provenance` or an unreadable registry counts as not synthesized."""
        for name, block in (("Step 7", self.step7), ("Step 7b", self.step7b),
                            ("Phase C step 13", self.step13)):
            with self.subTest(block=name):
                flat = self._flat(block)
                self.assertIn("no recorded `provenance`", flat)
                self.assertIn("an unreadable `config/data_sources.yaml`", flat)
                self.assertIn("INV-399", flat)

    def test_a_drifted_variant_fails_the_pin(self):
        """⛔ (INV-265) The pin reads the same flat text a one-word drift changes."""
        drifted = self._flat(self.step7).replace("is strong. Let's", "is great. Let's")
        self.assertNotIn(self.STEP7[0], drifted)


if __name__ == "__main__":
    unittest.main()
