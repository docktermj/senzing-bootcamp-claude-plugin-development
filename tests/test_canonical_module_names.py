"""Module display names come from one table, and no file invents a variant.

INV-079 makes the module NAME the Bootcamper-facing identifier — banners, journey maps,
transition questions, completion lines. That only works if there is one spelling per
module. There wasn't. The 2026-07-26 audit found four inventions in the public-facing
README alone ("SDK Installation and Configuration", "Identify and Collect Data Sources",
an Oxford-comma "Query, Visualize, and Discover", and a prose description standing in for
"Truth Set visualization"), plus "Data quality & mapping" and "Query/Visualize/Discover"
in the Required-modules list the agent reads aloud during Bootcamp preparation and in the
shipped example recap.

The README also omitted **Bootcamp preparation** — the first *mandatory* module — from its
list of what the bootcamp covers, which is a completeness defect rather than a naming one
and is checked here too, since both come from the same table.

A number is not a name either (#612). The example recap and two Bootcamper-facing quotes, the
CORD quote in Data collection and the software-integration statement in Discover the Business
Problem, named modules as "Module 5" or "Module 7", and the recap wrote "System Verification".
Those texts are checked for `Modules? \\d` and "System Verification". Each quote is located by
its opening words, and a quote that cannot be located fails the check by name.

#612 fixed instances; the class survived. INV-079 bans a module number from *anything the
bootcamper reads*, and four more sat in Query, Visualize and Discover — one of them written into
`docs/bootcamp_data_discoveries.md` and its PDF, where it cannot be corrected afterwards — with
two more in the mapping specification Data Quality, Mapping, and Transformation writes into
`docs/mapping/`. So the number ban is also swept over every shipped Markdown file under
`plugins/`, with the sites derived by scanning rather than named (INV-246): pinned 👉 questions,
the quoted and backticked spans a guide renders, and the fenced templates a module writes a
document from. Internal prose that INV-079 keeps — prerequisites, section headings, `config/*`
keys, and quotations of agent-facing instructions — is exempted span by span in `EXEMPT_SPANS`,
each with its reason, and a stale exemption fails by name (#683).

The source of truth is the module table in `bootcamp-preparation/SKILL.md`, which already
declares itself as such ("source of truth for selection and the journey map") and carries
the State token column. This test parses that table rather than hardcoding names, so
renaming a module is a one-place edit that this test then enforces everywhere.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks, line_of, match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PREP = PLUGIN / "skills" / "bootcamp-preparation" / "SKILL.md"
README = REPO_ROOT / "README.md"

#: The files #683's sweep found, kept here only for its negative controls.
MODULE_5 = PLUGIN / "skills" / "module-05-data-quality-mapping"
MODULE_5_PHASE_1 = MODULE_5 / "phase1-quality-assessment.md"
MODULE_5_PHASE_2 = MODULE_5 / "phase2-data-mapping.md"
MODULE_7 = PLUGIN / "skills" / "module-07-query-visualize-discover"
MODULE_7_PHASE_1 = MODULE_7 / "phase1-query-visualize.md"
MODULE_7_PHASE_2B = MODULE_7 / "phase2b-discover.md"

# Off-canon spellings found in the field. A variant stays listed after it is fixed —
# that is what stops it coming back.
#
# Out of scope deliberately: case-only differences in a skill's own H1 ("System
# Verification" for "System verification"), which is ordinary title casing rather than a
# different name. A different NAME is the defect — modules 2 and 4 were titled "SDK
# Installation and Configuration" and "Identify and Collect Data Sources", the spellings
# the agent reads immediately before announcing the module in its banner.
BANNED_VARIANTS = (
    "Data quality & mapping",
    "Data Quality & Mapping",
    "Query/Visualize/Discover",
    "SDK Installation and Configuration",
    "Identify and Collect Data Sources",
    "Query, Visualize, and Discover",
    "Data Quality, Mapping and Transformation",  # missing the serial comma
)


def variant_lines(text, variant):
    """1-based lines where ``variant`` starts, matched across line wraps (#424).

    A module name is several words, and prose wraps wherever the column runs out, so a
    line-at-a-time ``in`` check missed a banned name split across two lines.
    """
    return match_lines(text, re.compile(re.escape(variant)))


#: A banned variant wrapped mid-name, for the negative control.
WRAPPED_VARIANT = "Next up is the module called SDK Installation\nand Configuration, in Module 2.\n"


#: The example recap a Bootcamper reads as the model of their own recap (#612).
RECAP = PLUGIN / "docs" / "examples" / "bootcamp_recap.example.md"

#: Text that names a module by number, or by the title-cased "System Verification" (#612).
#: "Module" followed by a non-digit ("the Data collection module") is allowed.
NUMBERED_OR_RETIRED = (
    re.compile(r"\bModules? \d"),
    re.compile(r"System Verification"),
)

#: Bootcamper-facing quoted spans the ban covers, each located by its opening words (#612).
#: A span runs from its opening words to the next closing quotation mark. These two are kept
#: as they were: the general detector over every quoted span now lives below (#683), and these
#: pin that these particular quotes stay findable by their opening words.
NAMED_SPANS = (
    ("Module 4's CORD quote",
     PLUGIN / "skills" / "module-04-data-collection" / "SKILL.md",
     "Senzing provides **CORD (Collections Of Relatable Data)**:"),
    ("Module 1's software-integration statement",
     PLUGIN / "skills" / "module-01-business-problem" / "phase2-document-confirm.md",
     "If you name a system,"),
)


def locate_span(text, opening):
    """The span that starts with ``opening`` and ends at the next ``"``, or None.

    The returned text keeps the file's line numbering: everything before the span becomes
    the same number of empty lines, so a match inside it reports its line in the file.
    The opening words match across a line wrap, including a wrap inside a blockquote.
    """
    words = [re.escape(w) for w in opening.split()]
    m = re.search(r"[\s>]+".join(words), text)
    if not m:
        return None
    end = text.find('"', m.end())
    if end < 0:
        return None
    return "\n" * text.count("\n", 0, m.start()) + text[m.start():end]


def numbered_or_retired_lines(text):
    """``(line, matched text)`` for each module number or retired spelling, across wraps."""
    hits = []
    for pattern in NUMBERED_OR_RETIRED:
        for n in match_lines(text, pattern):
            hits.append((n, pattern.pattern))
    return sorted(hits)


def span_offenders(name, text, opening):
    """Offender lines for one named span; a span that cannot be located is an offender too."""
    span = locate_span(text, opening)
    if span is None:
        return [f"{name}: not located by its opening words {opening!r}"]
    return [f"{name}:{n} matches /{p}/" for n, p in numbered_or_retired_lines(span)]


def canonical_names():
    """Display names from the Bootcamp preparation module table, in order.

    Line-scoped by design (#424): a table row is one line.
    """
    rows = []
    for line in PREP.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`", line)
        if m:
            rows.append((m.group(2), m.group(4)))
    return rows


def shipped_and_public_files():
    """Everything a Bootcamper or prospective user reads."""
    for root, suffixes in ((PLUGIN, (".md",)), (REPO_ROOT / "docs", (".md",))):
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if "pytest_cache" in path.parts:
                continue
            yield path
    yield README


class TestTableIsParseable(unittest.TestCase):
    """If the table stops parsing, every other assertion here goes vacuous."""

    def test_all_eleven_modules_parse(self):
        rows = canonical_names()
        self.assertEqual(
            11, len(rows), f"expected 11 modules in the prep table, parsed {len(rows)}"
        )
        for name, token in rows:
            with self.subTest(module=name):
                self.assertTrue(name.strip())
                self.assertRegex(token, r"^[a-z_]+$", "State tokens are snake_case")

    def test_the_two_comma_bearing_names_are_present(self):
        """These two are why several files reach for an abbreviation."""
        names = [n for n, _ in canonical_names()]
        self.assertIn("Data Quality, Mapping, and Transformation", names)
        self.assertIn("Query, Visualize and Discover", names)


class TestNoInventedVariants(unittest.TestCase):

    def test_no_shipped_or_public_file_uses_a_banned_variant(self):
        offenders = []
        for path in shipped_and_public_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            for variant in BANNED_VARIANTS:
                for n in variant_lines(text, variant):
                    offenders.append(
                        f"{path.relative_to(REPO_ROOT)}:{n} uses '{variant}'"
                    )
        self.assertEqual(
            [],
            offenders,
            "Off-canon module name(s); use the spelling in bootcamp-preparation's "
            "module table (INV-079):\n  " + "\n  ".join(offenders),
        )

    def test_a_wrapped_variant_is_caught_at_its_first_line(self):
        """Negative control (#424): "Installation" ends line 1 and "and" begins line 2."""
        self.assertEqual([1], variant_lines(WRAPPED_VARIANT, "SDK Installation and Configuration"))
        # The old line-at-a-time check, kept only to show the fixture is the hard case.
        self.assertFalse(any("SDK Installation and Configuration" in line
                             for line in WRAPPED_VARIANT.split("\n")))

    def test_a_wrapped_canonical_name_is_not_a_variant(self):
        """Must-not-flag (INV-282): the canonical name, wrapped, trips no banned variant."""
        text = "Then comes Data Quality, Mapping,\nand Transformation, and after it Query,\nVisualize and Discover.\n"
        for variant in BANNED_VARIANTS:
            with self.subTest(variant=variant):
                self.assertEqual([], variant_lines(text, variant))

    def test_banned_variants_do_not_collide_with_canonical_names(self):
        """A banned string that is a substring of a canonical name would be unfixable."""
        names = [n for n, _ in canonical_names()]
        for variant in BANNED_VARIANTS:
            with self.subTest(variant=variant):
                self.assertNotIn(
                    variant,
                    " | ".join(names),
                    "banned variant appears inside a canonical name",
                )


class TestBootcamperTextNamesNoModuleByNumber(unittest.TestCase):
    """The example recap and the named Bootcamper-facing spans name modules by name (#612).

    INV-079 makes the name the Bootcamper-facing identifier, so "Module 5" in a sentence the
    Bootcamper reads, or the title-cased "System Verification", is the same defect as an
    invented variant. Agent-facing text that names modules by number is out of scope.
    """

    def test_the_example_recap_names_no_module_by_number(self):
        hits = numbered_or_retired_lines(RECAP.read_text(encoding="utf-8"))
        self.assertEqual(
            [], hits,
            f"{RECAP.relative_to(REPO_ROOT)} names a module by number or writes "
            f"\"System Verification\"; use the module table's name (INV-079): {hits}")

    def test_each_named_span_names_no_module_by_number(self):
        for name, path, opening in NAMED_SPANS:
            with self.subTest(span=name):
                self.assertEqual(
                    [], span_offenders(name, path.read_text(encoding="utf-8"), opening),
                    f"{path.relative_to(REPO_ROOT)}: fix the span, or, if its opening words "
                    "changed, update NAMED_SPANS (INV-079)")

    # Negative controls: each check fails on the text #612 fixed, put back into a copy.

    def test_the_old_cord_quote_is_caught(self):
        name, path, opening = NAMED_SPANS[0]
        text = path.read_text(encoding="utf-8")
        broken = text.replace("> the Data Quality, Mapping, and Transformation module checks",
                              "> Module 5 checks", 1)
        self.assertNotEqual(broken, text, "control did not apply")
        self.assertTrue(span_offenders(name, broken, opening))

    def test_the_old_module_1_statement_is_caught(self):
        name, path, opening = NAMED_SPANS[1]
        text = path.read_text(encoding="utf-8")
        broken = text.replace("If you name a system, the Query,\nVisualize and Discover module",
                              "If you name a system, Module\n7", 1)
        self.assertNotEqual(broken, text, "control did not apply")
        offenders = span_offenders(name, broken, opening)
        self.assertEqual(1, len(offenders))
        self.assertIn("Modules?", offenders[0])

    def test_the_old_recap_lines_are_caught(self):
        text = RECAP.read_text(encoding="utf-8")
        for fixed, old in (
            ("- Ran the System verification checks:", "- Ran the System Verification checks:"),
            ("recorded in Discover the Business Problem,", "recorded in Module 1,"),
            ("no warning was presented; Data processing will use",
             "no warning was presented; Module 6 will use"),
            ("against the Data collection snapshot", "against the Module 4 snapshot"),
        ):
            with self.subTest(old=old):
                broken = text.replace(fixed, old, 1)
                self.assertNotEqual(broken, text, "control did not apply")
                self.assertEqual(1, len(numbered_or_retired_lines(broken)))

    def test_a_span_whose_opening_words_changed_fails_by_name(self):
        name, path, opening = NAMED_SPANS[0]
        text = path.read_text(encoding="utf-8")
        broken = text.replace(opening, "Senzing offers **CORD**:", 1)
        self.assertNotEqual(broken, text, "control did not apply")
        offenders = span_offenders(name, broken, opening)
        self.assertEqual(1, len(offenders))
        self.assertTrue(offenders[0].startswith(f"{name}: not located"))

    def test_a_module_named_by_name_is_allowed(self):
        """Must-not-flag (INV-282): "Module" before a non-digit is not a number."""
        text = 'say: "Then the Data collection module, and Modules\nfor mapping, run next."'
        self.assertEqual([], span_offenders("fixture", text, "Then the"))

    def test_a_wrapped_module_number_is_caught(self):
        """The number ban matches across a wrap inside a blockquote (INV-346)."""
        text = 'Intro.\n\n> "Your data goes to Module\n> 5 next."\n'
        offenders = span_offenders("fixture", text, "Your data")
        self.assertEqual(1, len(offenders))
        self.assertTrue(offenders[0].startswith("fixture:3 "), offenders)


# ---------------------------------------------------------------------------
# The sweep over Bootcamper-facing text (#683)
# ---------------------------------------------------------------------------

#: A module named by number, anywhere. "Module" before a non-digit ("the Data collection
#: module", "Modules for mapping") is a name, not a number, and is not matched.
MODULE_NUMBER = re.compile(r"\bModules?\s+\d")

#: The quoted or backticked spans a module's text is rendered from: straight quotes, curly
#: quotes, and inline code. Run on a collapsed block, so each span is already one line, and
#: non-overlapping left to right, so the outermost span wins where they nest
#: (``"… files in `data/raw/`"`` is one double-quoted span, not two).
RENDERED_SPAN = re.compile(r'"[^"]*"|“[^”]*”|`[^`]+`')

#: A sentence end inside a collapsed block, for a hit that sits in no span at all.
SENTENCE_END = re.compile(r'(?<=[.!?])["”\'*`)\]]*\s')

#: A code fence line, as ``_wrapped_text`` reads one: three backticks or three tildes first
#: on the line, after any blockquote markers. **Line-scoped by design (#683):** a fence
#: delimiter is a line, and nothing about it can wrap.
FENCE_LINE = re.compile(r"^[ \t]*(?:>[ ]?[ \t]*)*(`{3,}|~{3,})")

#: The marker that opens a pinned question (INV-251).
PIN = "\U0001f449"

#: Spans the sweep finds that the Bootcamper never reads, each with the reason it is internal.
#: INV-079 keeps module numbers for skill directory names, prerequisites, section headings and
#: `config/*` keys; every entry here is one of those, or a quotation of agent-facing text.
#: ⚠️ Keyed by the span's own text, never by a path, so the sweep still fails on a site nobody
#: thought of (INV-246) and an exemption follows its text when the text moves. A span whose
#: wording changes fails `test_every_exemption_is_still_found` by name rather than going quiet.
EXEMPT_SPANS = {
    "Module 1":
        "the banned form itself, quoted by the three rules that ban it — ground-rules.md's "
        "INV-079 paragraph, Bootcamp preparation's handoff and Module 0's handoff each write "
        "never \"Module 1\"",
    "Record the recap, then hand off to Module 1":
        "a section heading in module-00-entity-resolution-concepts/SKILL.md, cited as a "
        "pointer; INV-079 keeps section headings internal",
    "Module completion and transition to Module 7":
        "a section heading in Module 6 Phase D, cited as a pointer from Phase D itself and "
        "from Module 7 step 3b",
    "Mark Module 2 as complete only after Step 9's engine-class check passes":
        "Module 2 Step 1's own instruction to the guide, quoted by the sdk_repair detour "
        "table; agent-facing on both sides",
    "the Module 6 loading program works as a template":
        "Module 6 step 16's instruction to the guide, quoted by an agent-facing INV-243 note "
        "about process-global counters",
    "Module 4 complete (data sources collected, files in `data/raw/`)":
        "Module 5 Phase 1's prerequisite line; INV-079 keeps prerequisites internal",
    "Bootcamper chose the return route at Module 5's no-progress gate":
        "a config/data_sources.yaml value in a yaml fence; INV-079 keeps `config/*` keys "
        "internal",
    "you already told me this in Module 1.":
        "a hypothetical Bootcamper line inside an agent-facing note on why Module 4 asks no "
        "provision question per source; nothing instructs the guide to say it",
}


def _blank(lines, start, end):
    """Blank ``lines[start:end]`` in place, so every later line keeps its number."""
    for i in range(start, end):
        lines[i] = ""


def prose_and_templates(text):
    """``(prose, templates)``: ``text`` cut in two, each keeping every line number.

    ``prose`` is what the file says, with the front matter and every fenced region blanked.
    ``templates`` is the fenced regions alone — the documents a module writes into the
    Bootcamper's ``docs/`` are written from these, and `config/*` and code fences land here
    too. Both halves are read block by block afterwards, so a phrase that wraps is still one
    phrase (INV-346).

    **Line-scoped by design (#683):** front-matter delimiters and fence delimiters are lines.
    """
    lines = text.split("\n")
    prose, templates = list(lines), [""] * len(lines)
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                _blank(prose, 0, i + 1)
                break
    fence = None
    start = 0
    for i, line in enumerate(prose):
        opener = FENCE_LINE.match(line)
        if opener and (fence is None or opener.group(1)[0] == fence):
            if fence:
                templates[start:i] = prose[start:i]
                _blank(prose, start - 1, i + 1)
                fence = None
            else:
                fence, start = opener.group(1)[0], i + 1
    if fence:  # an unclosed fence: everything after it is template text
        templates[start:] = prose[start:]
        _blank(prose, start - 1, len(prose))
    return "\n".join(prose), "\n".join(templates)


def sentence_at(flat, index):
    """The sentence of ``flat`` holding ``index``, for a hit that sits in no quoted span."""
    start = 0
    for m in SENTENCE_END.finditer(flat[:index]):
        start = m.end()
    after = SENTENCE_END.search(flat, index)
    return flat[start:after.start() + 1 if after else len(flat)].strip()


def numbered_module_spans(text):
    """``(line, kind, span)`` for every module number in text a Bootcamper reads.

    The three kinds are derived from the file's own shape, never from a list of sites
    (INV-246), and each is a different way a module puts words in front of the Bootcamper:

    - **rendered span** — a quoted or backticked span of the file's prose. A guide renders
      these verbatim: the labels it writes beside a quote and the statements it is told to
      make. Prose OUTSIDE such a span is the guidance itself, which INV-079 lets name modules
      by number, so a number there is not a hit.
    - **pinned question** — a block that opens with 👉. All of it is read aloud, quoted or not
      (INV-251, INV-056).
    - **template** — a fenced region. The documents a module writes into the Bootcamper's
      ``docs/`` are written from these, and so is the mapping specification; `config/*` and
      code fences land here too and are exempted by span where they carry a number.

    Front matter is skipped: it is the skill's description, read by the harness that routes to
    the skill and never by the Bootcamper.
    """
    prose, templates = prose_and_templates(text)
    found = []
    for flat, origin in collapsed_blocks(prose):
        if flat.startswith(PIN):
            for m in MODULE_NUMBER.finditer(flat):
                found.append((line_of(origin, m.start()), "pinned question",
                              sentence_at(flat, m.start())))
            continue
        for span in RENDERED_SPAN.finditer(flat):
            if MODULE_NUMBER.search(span.group(0)):
                found.append((line_of(origin, span.start()), "rendered span",
                              span.group(0)[1:-1].strip()))
    for flat, origin in collapsed_blocks(templates):
        for m in MODULE_NUMBER.finditer(flat):
            span = next((s for s in RENDERED_SPAN.finditer(flat)
                         if s.start() <= m.start() < s.end()), None)
            found.append((line_of(origin, m.start()), "template",
                          span.group(0)[1:-1].strip() if span
                          else sentence_at(flat, m.start())))
    return sorted(set(found))


def bootcamper_facing_offenders():
    """``file:line (kind) span`` for every un-exempt module number in shipped Markdown."""
    offenders = []
    for path in corpus_files("plugins", suffixes=(".md",)):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line, kind, span in numbered_module_spans(text):
            if span not in EXEMPT_SPANS:
                offenders.append(
                    f"{path.relative_to(REPO_ROOT)}:{line} ({kind}) {span!r}")
    return offenders


class TestBootcamperFacingTextNamesNoModuleByNumber(unittest.TestCase):
    """INV-079's ban, swept over every shipped Markdown file rather than a named few (#683).

    #612 fixed the example recap and two located quotes, and nothing swept the rest: Module 7
    kept four, one of them written into `docs/bootcamp_data_discoveries.md` and its PDF, and
    Module 5's mapping-specification template kept two more. The sites here are derived by
    scanning (INV-246), so a site nobody thought of fails too.

    ⛔ **What this cannot establish:** that a span the sweep calls internal really is — the
    exemptions below are judgments, each with its reason. Nor does it read anything but
    Markdown under `plugins/`: a module number in a bundled script's string, in `README.md`
    or under `docs/` is out of its scope (the scripts' hits are stderr addressed to the
    guide, and the public docs name no module by number today). Nor does it see a module
    number the guide invents at runtime; only `dry-run` phase 3 observes that.
    """

    def test_no_shipped_markdown_renders_a_module_number(self):
        offenders = bootcamper_facing_offenders()
        self.assertEqual(
            [], offenders,
            "Module number(s) in text the Bootcamper reads; name the module as "
            "bootcamp-preparation's module table spells it (INV-079), or, if the span really "
            "is internal, add it to EXEMPT_SPANS with its reason:\n  " + "\n  ".join(offenders))

    def test_the_sweep_reads_the_whole_shipped_corpus(self):
        """Anti-vacuity (INV-265): a scan that reads nothing would pass the check above."""
        paths = corpus_files("plugins", suffixes=(".md",))
        self.assertGreater(len(paths), 30, "the shipped Markdown corpus did not resolve")
        self.assertTrue(any(MODULE_NUMBER.search(p.read_text(encoding="utf-8")) for p in paths),
                        "no shipped file names a module by number at all")

    def test_every_exemption_is_still_found(self):
        """A stale exemption fails by name, so the list cannot outlive the text it excuses."""
        seen = set()
        for path in corpus_files("plugins", suffixes=(".md",)):
            for _, _, span in numbered_module_spans(path.read_text(encoding="utf-8")):
                seen.add(span)
        missing = sorted(set(EXEMPT_SPANS) - seen)
        self.assertEqual([], missing,
                         f"EXEMPT_SPANS names span(s) no shipped file carries: {missing}")

    # Negative controls: each wording #683 replaced, put back into a copy of its file.

    def _assertCaught(self, path, fixed, old, kind):
        text = path.read_text(encoding="utf-8")
        broken = text.replace(fixed, old, 1)
        self.assertNotEqual(broken, text, "control did not apply")
        hits = [(line, k, span) for line, k, span in numbered_module_spans(broken)
                if span not in EXEMPT_SPANS]
        self.assertEqual(1, len(hits), hits)
        self.assertEqual(kind, hits[0][1])

    def test_the_old_rendered_label_is_caught(self):
        self._assertCaught(MODULE_7_PHASE_1,
                           '"Your words in Discover the Business Problem:"',
                           '"Your words in Module 1:"', "rendered span")

    def test_the_old_label_restatement_is_caught(self):
        self._assertCaught(MODULE_7_PHASE_1,
                           '"Your words in Discover the\nBusiness Problem"',
                           '"Your words in Module 1"', "rendered span")

    def test_the_old_discoveries_line_is_caught(self):
        """The worst of the four: it is written into `docs/bootcamp_data_discoveries.md`."""
        self._assertCaught(MODULE_7_PHASE_1,
                           "`No query requirements were confirmed in Query, Visualize and "
                           "Discover step 1.`",
                           "`No query requirements were confirmed in Module 7 step 1.`", "rendered span")

    def test_the_old_export_statement_is_caught(self):
        self._assertCaught(MODULE_7_PHASE_2B,
                           '"In Discover the Business Problem you didn\'t\n   name a system',
                           '"In Module 1 you didn\'t name a system', "rendered span")

    def test_the_old_mapping_spec_candidates_line_is_caught(self):
        """A template: it is written into `docs/mapping/{source_name}_mapper.md`."""
        self._assertCaught(MODULE_5_PHASE_1,
                           "(suffix heuristic, from Phase 1 step 6 of\n     the Data Quality, "
                           "Mapping, and Transformation module)",
                           "(suffix heuristic, Module 5 Phase 1 step 6)", "template")

    def test_the_old_mapping_spec_name_rule_is_caught(self):
        self._assertCaught(MODULE_5_PHASE_1,
                           "in the order Phase 1 Step 6\n     sub-step 2 of the Data Quality, "
                           "Mapping, and Transformation module reads them",
                           "in the order Module 5 Phase 1\n     Step 6 sub-step 2 reads them",
                           "template")

    def test_the_old_phase_2_candidates_line_is_caught(self):
        self._assertCaught(MODULE_5_PHASE_2,
                           "(suffix heuristic, from Phase 1 step 6 of the\n    Data Quality, "
                           "Mapping, and Transformation module)",
                           "(suffix heuristic, Module 5 Phase 1 step 6)", "template")

    # Must-not-flag controls (INV-282): correct text trips nothing.

    def test_a_module_named_by_its_table_name_is_not_flagged(self):
        text = ('Say: "In Discover the Business Problem you named a system." Then the Data\n'
                'collection module runs, and Modules for mapping follow.\n')
        self.assertEqual([], numbered_module_spans(text))

    def test_a_number_in_the_front_matter_is_not_flagged(self):
        text = '---\ndescription: "Bootcamp Module 4: Data collection."\n---\n\nBody.\n'
        self.assertEqual([], numbered_module_spans(text))

    def test_a_wrapped_number_in_a_rendered_label_is_caught_at_its_first_line(self):
        """The ban matches across a wrap, inside a blockquote (INV-346)."""
        text = 'Intro.\n\n> Say: "Your data goes to Module\n> 5 next."\n'
        self.assertEqual([(3, "rendered span", "Your data goes to Module 5 next.")],
                         numbered_module_spans(text))

    def test_a_pinned_question_is_reported_as_one(self):
        text = "\U0001f449 **Shall we move on from Module 5?**\n"
        self.assertEqual("pinned question", numbered_module_spans(text)[0][1])

    def test_a_fenced_template_is_reported_as_one(self):
        text = "Write this file:\n\n```markdown\n## Notes\n\n- From Module 5 step 6\n```\n"
        self.assertEqual([(6, "template", "- From Module 5 step 6")],
                         numbered_module_spans(text))

    def test_an_exempt_span_is_matched_whole_not_by_substring(self):
        """`Module 1` excuses the quoted prohibition, never a sentence that contains it."""
        text = 'Say: "In Module 1 you did not name a system."\n'
        self.assertEqual([(1, "rendered span", "In Module 1 you did not name a system.")],
                         numbered_module_spans(text))
        self.assertNotIn(numbered_module_spans(text)[0][2], EXEMPT_SPANS)


class TestReadmeListsEveryModule(unittest.TestCase):
    """The public README's coverage list must not omit a module — mandatory or optional."""

    def test_readme_names_every_module(self):
        text = README.read_text(encoding="utf-8")
        missing = [name for name, _ in canonical_names() if name not in text]
        self.assertEqual(
            [],
            missing,
            "README.md omits module(s) from what the bootcamp covers — Bootcamp "
            f"preparation, the first mandatory module, was omitted this way: {missing}",
        )


if __name__ == "__main__":
    unittest.main()
