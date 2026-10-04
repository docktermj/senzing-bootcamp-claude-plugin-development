"""`compact-dev-environment` reads the frozen specs archive and never edits the invariant register.

Two invariants bind this skill, and until #386 its own text contradicted both:

- **INV-307** makes `specs/` a read-only archive. The skill still told its reader to archive
  (move) implemented specs, to append a dated note to a superseded spec and then archive it,
  and to delete a spec nobody wanted. `tests/test_specs_are_frozen.py` catches a file that
  lands, moves or changes; it cannot catch prose telling a maintainer to do it, and the person
  who follows that prose is the one who gets the red suite. The same gap was closed for the
  renumbering map by #142, at one site only.
- **INV-309** makes minting an id the maintainer's alone, through `/review-invariants`. The
  skill defined a merge as "one new invariant at the next free ID", had its `superseded`
  verdict "mark superseded" in `INVARIANTS.md` itself, and sent merges and demotions through
  a spec for `/implement-github-issue` to execute, a command that cannot mint either.

So this file pins three things, all scoped to `.claude/skills/compact-dev-environment/`:

1. No file there proposes archiving, moving, annotating or deleting a file under `specs/`.
   Writing to the live records `specs/IMPLEMENTED.md` and `specs/DECLINED.md` is allowed.

2. Step 2 and Step 6 route merges, supersessions and demotions to `/review-invariants` as
   `DEFERRED INVARIANT` / `PROPOSED AMENDMENT` blocks in `specs/IMPLEMENTED.md`, citing INV-309.

3. Neither step edits `INVARIANTS.md`, mints an id, or sends either to `/implement-github-issue`.

⚠️ **The matcher is derived from the claim, not from the lines that prompted it** (INV-282).
The claim is *"an instruction to perform an archive, move, annotate or delete action on a spec"*.
So the verbs are a set, the spec object is matched by word and by path, the passive and
modal forms are covered, a table row whose subject is a spec and whose action cell is a verb
is covered, and `MUST_FLAG` holds phrasings the skill never used. A prohibition that names the
forbidden act ("specs are read, never moved, annotated or deleted") is not an instruction, and
`MUST_PASS` pins that.

⚠️ **What this does NOT establish.** That a live run of the skill leaves `specs/` alone, or
that it writes the blocks after the maintainer's yes; only a run shows that. Nor does it reach
an instruction that names neither a spec nor a path ("tidy the archive"), which no word match
resolves. It does not widen `tests/test_no_instruction_writes_into_specs.py`, which still
guards file creation repo-wide.

Source issue: #386.

Stdlib only; the tree is read as text (INV-108).

No phrase-level pattern (#438): it is already wrap-aware: `offending_units` joins a paragraph's or a
list item's lines before it matches, and `.py` prose is read through `tokenize`, as #425 recorded
(INV-346).

Run:  python3 -m unittest discover -s tests
"""
import io
import re
import tokenize
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "compact-dev-environment"
SKILL_MD = SKILL_DIR / "SKILL.md"

#: The live records under `specs/` that a maintainer instruction may write to (INV-307 and
#: issue #386's acceptance criteria). Every other `specs/` path is the frozen archive.
LIVE_RECORDS = ("specs/IMPLEMENTED.md", "specs/DECLINED.md", "IMPLEMENTED.md", "DECLINED.md")

#: The acts INV-307 forbids on a spec, as a SET of stems (INV-282): the four the issue names,
#: plus the words someone else would use for the same act. Base, `-s` and `-ing` forms only:
#: an instruction is imperative or a gerund ("archive the spec", "archiving specs"), while an
#: `-ed` form before a noun is an adjective ("the three archived feedback files"). The `-ed`
#: forms are matched by `PASSIVE` instead, where a verb of being makes them an act.
ACT = (r"archiv(?:e|es|ing)|mov(?:e|es|ing)(?!\s+on\b)|relocat(?:e|es|ing)"
       r"|annotat(?:e|es|ing)|delet(?:e|es|ing)|remov(?:e|es|ing)"
       r"|renam(?:e|es|ing)|prun(?:e|es|ing)|retir(?:e|es|ing)"
       r"|discard(?:s|ing)?|trash(?:es|ing)?|append(?:s|ing)?\b[^,]{0,25}?\bnote")

#: A spec, by word or by path. `SPECPATH` is what a code span naming a frozen `specs/` path
#: becomes before matching (see `_normalize`).
SPEC = r"\bspecs?\b(?:\s+files?)?|\bSPECPATH\b"

#: ⚠️ The gap stops at a comma: in "prunes feedback, and reads the frozen specs archive" the
#: spec is the object of a second verb, not of the act.
ACTIVE = re.compile(r"\b(?P<act>%s)\b(?P<gap>[^|,]{0,60}?)(?:%s)" % (ACT, SPEC), re.I)
PASSIVE = re.compile(
    r"(?:%s)[^|]{0,40}?\b(?:be|is|are|get|gets|been)\s+(?:\w+\s+)?(?:archived|moved|relocated|"
    r"annotated|deleted|removed|renamed|pruned|retired|discarded|trashed)\b" % SPEC, re.I)
MODAL = re.compile(
    r"(?:%s)[^|]{0,40}?\b(?:may|can|should|must|will|could)\s+(?:(?:then|also)\s+)?"
    r"(?:move|go|archive)\b" % SPEC, re.I)

#: The act with its object left implicit -- "then archive", "delete them" -- inside a paragraph
#: or list item whose subject is a spec. The pre-#386 Step 3 said "append a dated note saying
#: what superseded it, then archive" under a bullet about specs, and named no spec in the clause.
#: Base forms only: an imperative. "the only records this skill prunes" ends a clause on a verb
#: too, and describes rather than instructs.
IMPLICIT = re.compile(
    r"\b(?P<act>archive|move|relocate|annotate|delete|remove|rename|prune|retire|discard|trash)"
    r"\b(?:\s+(?:it|them)\b|\s*$)", re.I)

#: A prohibition names the act and is not an instruction to perform it.
NEGATION = re.compile(
    r"\b(?:never|not|no|nor|neither|cannot|without|rejected|forbids?|forbidden|instead of|"
    r"rather than)\b|n't\b", re.I)

#: Words that make the next ACT word a noun ("the frozen archive", "the next move").
NOUN_BEFORE = {"a", "an", "the", "this", "that", "its", "frozen", "read-only", "feedback",
               "every", "each", "any", "whole", "next", "specs"}

#: A clause ends at sentence punctuation, a table cell, or a dash.
CLAUSE_END = re.compile(r"[.;:!?](?=\s|$)|\||\s—\s")

#: An instruction to change the invariant register in place (INV-309: it changes only through
#: `/review-invariants`).
EDITS_REGISTER = re.compile(r"\b(?:edit|rewrit|append|mark|chang|updat)\w*\b[^.;|]{0,40}?"
                            r"INVARIANTS\.md", re.I)

TABLE_ACTION_CELL = re.compile(r"^\s*(?:%s)\b" % ACT, re.I)

#: ⛔ Must flag, including phrasings the skill never used (INV-282). A guard whose fixtures
#: are only the lines it was built from proves it finds what it already found.
MUST_FLAG = [
    "archive the spec",
    "move `specs/x.md` to `specs/archive/`",
    "delete the spec",
    "Implemented and stable specs: archive them under specs/archive/ once they settle.",
    "relocate superseded specs into the archive folder",
    "append a dated note to the spec saying what replaced it",
    "Specs whose work has long landed may be archived.",
    "Spec files may move; the ledger lines never go.",
    "Then rename the stale spec file so the list reads cleanly.",
    "prune spec files nobody has opened in a month",
    "| `specs/<name>.md` | implemented, stable | archive | ledger heading unchanged |",
    "| Spec file | a record | moderate | archive (move), rarely delete |",
    "Mechanical changes may be executed here: archiving specs, pruning feedback files.",
    "annotate `specs/old-thing.md` with a pointer to its successor",
    "- Superseded → the spec now misleads. Do not delete it: append a dated note saying what "
    "superseded it, then archive.",
    "- A spec nobody wants any more: delete it once the maintainer agrees.",
]

#: ⛔ Must pass. Every one is correct prose, and a guard that flags correct prose is relaxed
#: rather than fixed (INV-282).
MUST_PASS = [
    "Specs are read, never moved, annotated or deleted (INV-307).",
    "specs are read, never moved, annotated or deleted",
    "Archiving was measured on 2026-07-30 and rejected",
    "it appends one dated entry to `specs/IMPLEMENTED.md` holding the blocks below",
    "record the decision in `specs/DECLINED.md`, the live record for it; the spec file stays",
    "Do not delete a spec to make a count smaller.",
    "Never move a spec into another directory.",
    "`specs/` froze on 2026-09-15 into a read-only archive pinned by name in "
    "`specs/FROZEN-MANIFEST.txt`",
    "Archived feedback files may be pruned once every entry is in the ledger.",
    "When the census is clean, move on to the next spec in the list.",
    "| `specs/` | frozen archive (INV-307) | leave | ledger headings resolve |",
    "This binds the feedback files, the only records this skill prunes; specs are neither "
    "moved nor deleted.",
    "The same applies to the three archived feedback files and to any spec text quoting a "
    "historical decision.",
    "Archived feedback files they point at may be pruned, and the specs they point at stay "
    "where they are (INV-307)",
    "proposes invariant merges, merges test traversals and prunes feedback, and reads the "
    "frozen specs archive without changing it",
]


def _normalize(text):
    """Collapse whitespace, drop emphasis, and turn code spans into tokens the matcher reads.

    A frozen `specs/` path becomes `SPECPATH`, a live record becomes `LIVERECORD`, and any
    other code span becomes `CODE`, so a dot inside a path is not a clause end."""
    def span(m):
        inner = m.group(1).strip()
        if inner in LIVE_RECORDS:
            return "LIVERECORD"
        if inner.startswith("specs/") or inner == "specs" or inner == "INVARIANTS.md":
            return "SPECPATH"
        return "CODE"
    text = re.sub(r"`([^`\n]*)`", span, text)
    text = text.replace("**", "").replace("*", "")
    return text


def _is_noun(clause, start):
    before = clause[:start].split()
    return bool(before) and before[-1].lower().strip("(") in NOUN_BEFORE


def clause_offends(clause, about_a_spec=False):
    """True when one clause instructs an archive / move / annotate / delete on a spec.

    `about_a_spec` says the enclosing paragraph or list item names a spec, so an act whose
    object is a pronoun or is left out refers to it."""
    if about_a_spec:
        for m in IMPLICIT.finditer(clause.strip()):
            if not _is_noun(clause.strip(), m.start("act")) and not NEGATION.search(clause):
                return True
    for m in ACTIVE.finditer(clause):
        if _is_noun(clause, m.start("act")):
            continue
        if NEGATION.search(clause[:m.end()]):
            continue
        return True
    for pattern in (PASSIVE, MODAL):
        for m in pattern.finditer(clause):
            if not NEGATION.search(clause[:m.end()]):
                return True
    return False


def row_offends(row):
    """True when a table row's subject is a spec and one of its cells is an action verb."""
    cells = [c for c in row.strip().strip("|").split("|")]
    if len(cells) < 2 or not re.search(SPEC, cells[0], re.I):
        return False
    return any(TABLE_ACTION_CELL.search(c) and not NEGATION.search(c) for c in cells[1:])


def offending_units(text):
    """[unit] for each paragraph, list item or table row in `text` that offends."""
    out = []
    units, current = [], []
    for line in text.splitlines():
        stripped = line.strip()
        starts_item = bool(re.match(r"(?:[-*+]|\d+\.)\s", stripped))
        if not stripped or stripped.startswith("|") or stripped.startswith("#") or starts_item:
            if current:
                units.append(" ".join(current))
                current = []
            if stripped.startswith("|"):
                units.append(stripped)
                continue
            if stripped.startswith("#"):
                continue
        if stripped:
            current.append(stripped)
    if current:
        units.append(" ".join(current))
    for unit in units:
        norm = _normalize(unit)
        if norm.startswith("|"):
            if row_offends(norm) or any(clause_offends(c) for c in CLAUSE_END.split(norm)):
                out.append(unit)
            continue
        about = bool(re.search(SPEC, norm, re.I))
        if any(clause_offends(c, about) for c in CLAUSE_END.split(norm)):
            out.append(unit)
    return out


def prose_of(path):
    """The text in a file that a reader takes as instruction: all of a Markdown file, and the
    docstrings and comments of a Python file (its code names `specs/archive/` as a path the
    census READS, which the issue keeps)."""
    text = path.read_text(encoding="utf-8")
    if path.suffix != ".py":
        return text
    parts = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            parts.append(tok.string.lstrip("#: "))
        elif tok.type == tokenize.STRING and tok.string.lstrip("rbuRBU").startswith(('"""', "'''")):
            parts.append(tok.string.strip("rbuRBU").strip("\"'"))
    return "\n\n".join(parts)


def skill_files():
    return sorted(p for p in SKILL_DIR.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts
                  and p.suffix in {".md", ".py", ".sh", ".txt", ".json"})


def section(text, heading_prefix):
    """The body of the `## <heading_prefix>...` section, up to the next `## ` heading."""
    m = re.search(r"^## %s.*$" % re.escape(heading_prefix), text, re.M)
    if not m:
        return ""
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


class TheScanIsNotVacuous(unittest.TestCase):
    """INV-265: an empty scan satisfies any check."""

    def test_it_reads_the_skill_and_its_tools(self):
        names = {p.name for p in skill_files()}
        for expected in ("SKILL.md", "citations.py"):
            self.assertIn(expected, names, "%s not found in %s" % (expected, SKILL_DIR))

    def test_it_sees_the_specs_the_skill_talks_about(self):
        units = [u for u in _normalize(SKILL_MD.read_text(encoding="utf-8")).split("\n\n")
                 if re.search(SPEC, u, re.I)]
        self.assertGreaterEqual(
            len(units), 5,
            "only %d paragraph(s) of SKILL.md mention a spec; the scan is reading the wrong "
            "file or the normalizer is eating the text" % len(units))

    def test_a_forbidden_line_added_to_the_real_text_is_caught(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        planted = text + "\n\n- **Superseded** → append a dated note to the spec, then archive it.\n"
        self.assertEqual([], offending_units(text))
        self.assertEqual(1, len(offending_units(planted)),
                         "a forbidden instruction appended to the real SKILL.md was not caught")

    def test_python_prose_is_extracted(self):
        prose = prose_of(SKILL_DIR / "citations.py")
        self.assertIn("frozen specs archive", prose,
                      "citations.py's docstring was not read, so the scan of .py files is empty")


class TheMatcherIsDerivedFromTheClaim(unittest.TestCase):
    """INV-282: pinned in both directions, including phrasings nobody has written yet."""

    def test_it_flags_every_forbidden_construction(self):
        missed = [f for f in MUST_FLAG if not offending_units(f)]
        self.assertEqual([], missed, "the matcher misses instruction(s) to act on a spec: %s"
                         % " ;; ".join(missed))

    def test_it_flags_none_of_the_correct_ones(self):
        wrong = [f for f in MUST_PASS if offending_units(f)]
        self.assertEqual([], wrong, "the matcher flags correct prose: %s" % " ;; ".join(wrong))


class NoFileInTheSkillActsOnASpec(unittest.TestCase):
    """INV-307: `specs/` is read-only; the skill's own text must not tell anyone otherwise."""

    def test_no_file_proposes_an_archive_move_annotate_or_delete(self):
        found = []
        for path in skill_files():
            for unit in offending_units(prose_of(path)):
                found.append("%s: %s" % (path.relative_to(REPO_ROOT).as_posix(), unit[:140]))
        self.assertEqual(
            [], found,
            "compact-dev-environment proposes acting on a frozen spec (INV-307; "
            "tests/test_specs_are_frozen.py would fail the run that follows it):\n  %s"
            % "\n  ".join(found))


class InvariantChangesGoToReviewInvariants(unittest.TestCase):
    """INV-309: minting is the maintainer's alone, through `/review-invariants`."""

    @classmethod
    def setUpClass(cls):
        text = SKILL_MD.read_text(encoding="utf-8")
        cls.step2 = section(text, "Step 2")
        cls.step6 = section(text, "Step 6")

    def test_both_sections_were_found(self):
        self.assertTrue(self.step2.strip(), "SKILL.md has no '## Step 2' section")
        self.assertTrue(self.step6.strip(), "SKILL.md has no '## Step 6' section")

    def test_step_2_routes_all_three_as_blocks_and_says_why(self):
        for needle in ("DEFERRED INVARIANT", "PROPOSED AMENDMENT", "`INV-NNN`",
                       "`specs/IMPLEMENTED.md`", "/review-invariants", "INV-309",
                       "A merge:", "A supersession:", "A demotion", "GitHub issue",
                       "Why they are routed this way"):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.step2)

    def test_step_6_routes_invariant_changes_to_review_invariants(self):
        for needle in ("/review-invariants", "INV-309", "go through a GitHub issue",
                       "deleting a test"):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.step6)
        self.assertNotIn("go through a spec", self.step6)

    def test_neither_step_edits_the_register_mints_or_hands_off_a_mint(self):
        forbidden = [
            ("edits INVARIANTS.md", EDITS_REGISTER),
            ("mints an id",
             # The finite verb only: "Minting an id is the maintainer's alone" states whose
             # act it is, and is the sentence the skill must keep.
             re.compile(r"\bnext free id\b|\bmints?\s+(?:a|an|the|one)?\s*(?:new\s+)?ids?\b",
                        re.I)),
            ("hands an invariant change to /implement-github-issue",
             re.compile(r"(?:merg|demot|supersed|mint)\w*[^.;|]{0,80}?/implement-github-issue",
                        re.I)),
        ]
        found = []
        for name, body in (("Step 2", self.step2), ("Step 6", self.step6)):
            for clause in CLAUSE_END.split(body.replace("**", "").replace("`", "")):
                for label, pattern in forbidden:
                    m = pattern.search(clause)
                    if m and not NEGATION.search(clause[:m.end()]):
                        found.append("%s %s: %s" % (name, label, clause.strip()[:120]))
        self.assertEqual([], found, "INV-309: %s" % "\n  ".join(found))

    def test_the_register_check_is_not_vacuous(self):
        planted = self.step6 + "\nThen mark both originals superseded in INVARIANTS.md.\n"
        hits = [c for c in CLAUSE_END.split(planted)
                if EDITS_REGISTER.search(c) and not NEGATION.search(c)]
        self.assertTrue(hits, "a planted edit of INVARIANTS.md was not caught")


if __name__ == "__main__":
    unittest.main()
