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


if __name__ == "__main__":
    unittest.main()
