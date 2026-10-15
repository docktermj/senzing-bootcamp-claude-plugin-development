"""Every maintainer skill routes an invariant change through `/review-invariants`.

Until #520 the maintainer skills told their reader two different things about how a new
invariant gets into `specs/INVARIANTS.md`. `/compact-dev-environment` wrote a block in
`specs/IMPLEMENTED.md` and sent the maintainer to `/review-invariants`. `/dry-run`,
`/production-readiness-audit` and `/auto-test` told the reader to register the invariant, or to
append a dated correction, by hand. Hand registration is the six-step job `/review-invariants`
exists to do, because on 2026-09-01 it went quietly wrong four ways (that skill's opening).
And `/compact-dev-environment` cited INV-309 for the broader rule, which INV-309 does not state:
INV-309 binds only the issue-driven development path, `/implement-github-issue`.

So this guard asserts the condition, not the wording (INV-219):

1. **No direct edit.** No `.claude/skills/*/*.md` except `review-invariants`' own tells the
   reader to register or mint an invariant, to edit or append to `specs/INVARIANTS.md`, or to
   correct an invariant in place. A prohibition ("never edit `specs/INVARIANTS.md` here") is not
   an instruction, and neither is a question to the maintainer ("ask whether to register").
2. **The route.** Every skill that tells its reader to account for an invariant (it names the
   invariant a run establishes, a `DEFERRED INVARIANT` or `PROPOSED AMENDMENT` block, or
   disclaiming one) names `/review-invariants` and points to the section that owns the block
   formats. The set is derived by scanning (INV-246), and the four skills #520 names are a floor
   the derivation must reach, so a scan that silently matched nothing cannot pass.
3. **The pointer lands.** Every link into `review-invariants/SKILL.md` with an anchor resolves
   to that file and to the heading whose section holds the block template, which is "Writing
   one" today. The heading is derived from where the template is, not hardcoded, so a renamed
   heading fails every stale pointer. Each unit that holds a pointer also names
   `/review-invariants`, so a pointer never stands without the route (INV-300: the pointing site
   carries no second copy of the formats).
4. **INV-309 is cited for what it states.** Every parenthesized citation of INV-309 under
   `.claude/skills/` sits in a sentence about `/implement-github-issue` or the issue-driven path,
   and that sentence does not also govern `specs/INVARIANTS.md`, which is the broader rule.
   Since #607 this reads Python too, because `release-cycle/cycle.py` wrote "Establishes no
   invariant (INV-309)" into a ledger entry, and tests credited INV-309 with INV-365's rule:
   every `.py` file under `.claude/skills/` (its comments and every string, since a script's
   strings are the text it writes) and every `.py` file under `tests/` (its comments and
   docstrings only: a test's other strings are fixtures, needles and messages that quote other
   files, such as the overlay heading `tests/test_hard_rule_detector_sees_mid_line_stop_signs.py`
   quotes). A sentence naming the unattended loop or a skill overlay is about the issue-driven
   path: the overlays carry that path's obligations, and
   `tests/test_unattended_loop_is_label_gated.py` credits INV-309 to "the overlay" correctly.

⚠️ **The matcher is derived from the claim, not from the sentences #520 replaced** (INV-282).
The claim is *"an instruction to change the invariant register in place"*. So the verbs are a
set, in their base (imperative) form only — "this skill never edits" and "is registered as an
invariant" describe rather than instruct — and `MUST_FLAG` holds phrasings no skill ever used.

⚠️ **Wrap-aware (INV-346).** Each Markdown block is read through `tests/_wrapped_text.py`'s
`blocks`, with whitespace collapsed, and then cut into clauses and list items. A re-wrapped copy
of the old `/auto-test` sentence is one of the negative controls.

⚠️ **What this does NOT establish.** That a live run writes the block rather than editing
`specs/INVARIANTS.md`; only a real run shows that. Nor does it reach an instruction that names
neither the file, an invariant nor an id ("update the register"). It does not read
`review-invariants`, the one skill that does edit `specs/INVARIANTS.md`, or the skill overlays,
which already route through `/review-invariants` under INV-309.

Enforces INV-365 (registered 2026-10-13 from the
`maintainer-skills-route-invariant-changes-through-review-invariants` block). It reads skill
text, and for rule 4 Python text too: it cannot establish that a live run writes the block
rather than editing the file.

Source issues: #520; rule 4's Python reading, #607.

Stdlib only; every file is read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import ast
import io
import re
import tokenize
import unittest
from pathlib import Path

from _corpus import corpus_files
from _wrapped_text import blocks

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / ".claude" / "skills"
OWNER = SKILLS / "review-invariants" / "SKILL.md"

#: The four skills #520 names. ⛔ A floor for the derived set, never the set itself (INV-246):
#: the guard reads every skill, and this only proves the derivation reached the ones known.
NAMED_BY_520 = ("dry-run", "production-readiness-audit", "auto-test", "compact-dev-environment")

#: The acts that change the register, base form only: an instruction is an imperative.
ACT = (r"register|mint|append|add|edit|rewrite|amend|correct|mark|update|change|renumber"
       r"|write|record|disclaim|insert")

#: An act whose object is the register file.
EDITS_FILE = re.compile(r"\b(?:%s)\b[^.;:|]{0,80}?\bINVARIANTS\.md\b" % ACT, re.I)
#: Registering or minting, with the object an invariant or an id.
MINTS = re.compile(r"\b(?:register|mint)\b(?:\s+[^\s.;:|]+){0,4}?\s+(?:invariants?|ids?)\b",
                   re.I)
#: Correcting an invariant in place, or writing the correction note itself.
CORRECTS = re.compile(
    r"\b(?:correct|amend|fix)\b\s+(?:an|the|a|that|this|each)\s+invariants?\b"
    r"|\b(?:add|append|write)\b\s+(?:a|the)\s+dated\s+(?:correction|note)", re.I)
#: Where each act word starts; every pattern above is tried from each one.
ACT_WORD = re.compile(r"\b(?:%s|fix)\b" % ACT, re.I)
DIRECT = (("edits specs/INVARIANTS.md", EDITS_FILE), ("registers or mints", MINTS),
          ("corrects an invariant in place", CORRECTS))

#: A prohibition, or a question to the maintainer, names the act without instructing it.
NEGATION = re.compile(r"\b(?:never|not|no|nor|neither|cannot|without|instead of|rather than"
                      r"|whether)\b|n't\b", re.I)

#: A clause ends at sentence punctuation, a table cell, or a spaced dash.
CLAUSE_END = re.compile(r"[.;:!?](?=\s|$)|\||\s—\s")
#: A sentence ends at sentence punctuation before the next sentence's first character.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[⛔A-Z(\[])")
#: A list item starts a unit of its own inside a block.
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")

#: A skill that tells its reader to account for an invariant.
DUTY = re.compile(r"\binvariant it establishes\b|\bestablishes (?:none|no (?:new )?invariant)"
                  r"|DEFERRED INVARIANT|PROPOSED AMENDMENT|\bdisclaim\w* the invariant", re.I)
ROUTE = "/review-invariants"
#: A Markdown link into the owner skill, with its anchor.
POINTER = re.compile(r"\]\(([^)\s#]*review-invariants/SKILL\.md)#([^)\s]+)\)")
#: A parenthesized citation list that includes INV-309.
CITES_309 = re.compile(r"\((?:[^()]*?\s|)INV-309\b[^()]*\)")
#: What an INV-309 sentence must be about: the issue command, the path, the loop that drives
#: it, or the skill overlays that carry its obligations (#607).
ISSUE_PATH = re.compile(r"implement-github-issue|issue-driven|unattended-issue-loop"
                        r"|\boverlays?\b", re.I)
#: What it must not also govern: the register itself is the broader, unminted rule. Before #520
#: compact-dev-environment's Step 6 hung one INV-309 on "never edit `specs/INVARIANTS.md` here,
#: and never send an invariant change to `/implement-github-issue`".
BROADER = re.compile(r"INVARIANTS\.md")

#: The sentence `/auto-test` carried before #520. ⛔ Restoring it must fail the guard (#520).
AUTO_TEST_BEFORE_520 = ("and register or explicitly disclaim the invariant in "
                        "`specs/INVARIANTS.md`.")

#: ⛔ Must flag, including phrasings no skill used (INV-282).
MUST_FLAG = [
    AUTO_TEST_BEFORE_520,
    "and register or explicitly disclaim the invariant in\n`specs/INVARIANTS.md`.",
    "Then either register the invariant it establishes or state that it establishes none.",
    "append it per `INVARIANTS.md`'s own rules — next unused ID, index entry in the same edit.",
    "Draft the invariant, get the maintainer's sign-off on the wording (never record one\n"
    "they have not agreed to), and append it per `INVARIANTS.md`'s own rules — next unused ID.",
    "6. **Correct an invariant in place when the invariant is what is wrong** — a dated note.",
    "Add a dated correction note explaining what was verified and when.",
    "Register it in `specs/INVARIANTS.md` once the maintainer agrees.",
    "Mint the next free id for the merged rule.",
    "Mark INV-012 superseded in `specs/INVARIANTS.md`.",
    "Amend the invariant so its wording matches the server.",
    "Then add it to INVARIANTS.md with an index entry.",
    "Update **`specs/INVARIANTS.md`** with the corrected wording.",
]

#: The sentence `release-cycle/cycle.py` wrote into a ledger entry before #607. ⛔ Restoring it
#: must fail the guard: it credits INV-309 with the record a maintainer run owes, INV-365's rule.
CYCLE_BEFORE_607 = '"- **Establishes no invariant** (INV-309): it records a run. The invariants the "'
CYCLE_AFTER_607 = '"- **Establishes no invariant** (INV-365): it records a run. The invariants the "'

#: ⛔ Must pass rule 4: correct INV-309 credits that a too-narrow reading of "the issue-driven
#: path" would flag (#607).
MUST_PASS_309 = [
    # tests/test_unattended_loop_is_label_gated.py: the loop overlay's invariant capture.
    "* the repository-only obligations (INV-309, INV-307, no `submit_feedback`, no declining) "
    "against\n  the overlay, where they moved;",
    "Sending one to `/implement-github-issue` *(user level)* does not help: that command cannot "
    "mint either (INV-309).",
]

#: ⛔ Must pass: correct prose a too-wide matcher would flag (INV-282).
MUST_PASS = [
    "⛔ **Route it through `/review-invariants`; never edit `specs/INVARIANTS.md` here:** write a "
    "`DEFERRED INVARIANT` block in the run's `specs/IMPLEMENTED.md` entry.",
    "⛔ **This skill never edits `specs/INVARIANTS.md` and never mints an id.**",
    "`INVARIANTS.md` is append-only; a superseded invariant is *marked* superseded.",
    "Per `INVARIANTS.md`'s own rules, propose appending a superseding note.",
    "If a run finds concision defects worth binding, **ask** whether to register a new invariant.",
    "Read `specs/INVARIANTS.md` in full.",
    "**`INVARIANTS.md` is append-only, and only `/review-invariants` writes to it.**",
    "every durable rule the plugin states is registered as an invariant",
    "Minting an id is the maintainer's alone, through `/review-invariants`.",
    "Record the outcome in `specs/IMPLEMENTED.md`, naming the issue each finding became.",
]


def read(path):
    return path.read_text(encoding="utf-8")


def units(text):
    """The paragraphs and list items of ``text``, whitespace collapsed (INV-346).

    A Markdown block is cut at each list marker, so a list item is a unit of its own.
    """
    out = []
    for block in blocks(text):
        current = []
        for _lineno, line in block:
            if LIST_ITEM.match(line) and current:
                out.append(" ".join(current))
                current = []
            current.append(line.strip())
        if current:
            out.append(" ".join(current))
    return [re.sub(r"\s+", " ", u).strip() for u in out if u.strip()]


def _plain(unit):
    return unit.replace("**", "").replace("`", "").replace("*", "")


def _prose(text):
    """``text`` with each link target dropped: `../review-invariants/SKILL.md` is a path, not
    the route, and must not satisfy a check for `/review-invariants`."""
    return re.sub(r"\]\([^)]*\)", "]", text)


def _negated(clause, m):
    """Whether the act ``m`` found in ``clause`` is prohibited or asked about, not instructed.

    The negation must govern this act: it sits in the words since the last comma before the
    act ("Do not edit, append to or rewrite …") or inside the match ("write a block rather than
    edit …"). A clause is often a comma series, and "fix the class not the instance, …, and
    register the invariant" is an instruction to register whatever its first item says.
    """
    before = clause[:m.start()].rsplit(",", 1)[-1]
    return bool(NEGATION.search(before) or NEGATION.search(m.group()))


def direct_edits(text):
    """Each clause of ``text`` that instructs a change to the invariant register in place."""
    found = []
    for unit in units(text):
        for clause in CLAUSE_END.split(_plain(unit)):
            for label, pattern in DIRECT:
                # Every act is tried, overlapping ones too: a prohibited act ("never record
                # one") must not hide the instructed act that follows it in the same span.
                for start in (v.start() for v in ACT_WORD.finditer(clause)):
                    m = pattern.match(clause, start)
                    if m and not _negated(clause, m):
                        found.append("%s: %s" % (label, clause.strip()[:140]))
                        break
    return found


def slug(heading):
    """GitHub's anchor for a Markdown heading's text."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def format_heading(owner_text):
    """The heading whose section holds the block template, read from the owner skill."""
    heading = None
    for line in owner_text.split("\n"):
        m = re.match(r"^#{2,6}\s+(.*\S)\s*$", line)
        if m:
            heading = m.group(1)
        elif "PROPOSED AMENDMENT to INV-nnn" in line and heading:
            return heading
    return None


def pointer_problems(path, text, anchor):
    """What keeps each pointer in ``text`` from landing on the owner's format heading."""
    problems = []
    for m in POINTER.finditer(text):
        target = (path.parent / m.group(1)).resolve()
        if target != OWNER.resolve():
            problems.append("%s does not resolve to %s" % (m.group(1), OWNER.name))
        if m.group(2) != anchor:
            problems.append("#%s is not the format heading's anchor #%s" % (m.group(2), anchor))
    for unit in units(text):
        if POINTER.search(unit) and ROUTE not in _prose(unit):
            problems.append("a pointer without the route: %s" % unit[:140])
    return problems


def route_problems(path, text, anchor):
    """What keeps a skill that accounts for invariants from stating the route."""
    problems = []
    if ROUTE not in _prose(text):
        problems.append("names no %s" % ROUTE)
    if not POINTER.search(text):
        problems.append("carries no pointer to review-invariants' format section")
    return problems + pointer_problems(path, text, anchor)


def misscoped_309(text):
    """Each sentence citing INV-309 that is not about the issue-driven path."""
    found = []
    for unit in units(text):
        for sentence in SENTENCE_END.split(_plain(unit)):
            if CITES_309.search(sentence) and (not ISSUE_PATH.search(sentence)
                                               or BROADER.search(sentence)):
                found.append(sentence.strip()[:160])
    return found


def _comment_text(source):
    """The comments of Python ``source``, each run of comment lines joined as one paragraph.

    A comment wraps like prose (INV-346), so a citation opened on one comment line and closed on
    the next is one citation. A line that is not a comment, or a bare ``#``, ends the paragraph.
    """
    paragraphs, current, last = [], [], None
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type != tokenize.COMMENT:
            continue
        line = re.sub(r"^#:?\s?", "", tok.string).rstrip()
        if current and (last is None or tok.start[0] != last + 1 or not line.strip()):
            paragraphs.append("\n".join(current))
            current = []
        if line.strip():
            current.append(line)
        last = tok.start[0]
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def _docstrings(tree):
    """The module, class and function docstrings of a parsed Python file."""
    nodes = [tree] + [n for n in ast.walk(tree)
                      if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
    return [d for d in (ast.get_docstring(n, clean=True) for n in nodes) if d]


def python_prose(source, every_string):
    """The prose of Python ``source``: its comments and docstrings, and with ``every_string``
    every string constant too (adjacent literals are one constant, as Python joins them)."""
    tree = ast.parse(source)
    if every_string:
        strings = [n.value for n in ast.walk(tree)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    else:
        strings = _docstrings(tree)
    return _comment_text(source) + strings


def misscoped_309_python(source, every_string):
    """``misscoped_309`` over each piece of the prose of Python ``source``."""
    found = []
    for piece in python_prose(source, every_string):
        found.extend(misscoped_309(piece))
    return found


def python_files():
    """Each `.py` file rule 4 reads, with whether every string is its prose (scripts) or only
    its docstrings (tests, whose other strings quote other files)."""
    return ([(Path(p), True) for p in corpus_files(".claude/skills", suffixes=(".py",))]
            + [(Path(p), False) for p in corpus_files("tests", suffixes=(".py",))])


def skill_markdown():
    """Every Markdown file under `.claude/skills/` except the owner skill's own."""
    owner_dir = OWNER.parent.resolve()
    return [p for p in corpus_files(".claude/skills", suffixes=(".md",))
            if Path(p).resolve().parent != owner_dir]


def skill_files():
    """Each `.claude/skills/*/SKILL.md` except the owner's."""
    return [Path(p) for p in skill_markdown() if Path(p).name == "SKILL.md"]


class TheMatcherReadsTheClaim(unittest.TestCase):
    """INV-282: fixtures beyond the sentences #520 replaced."""

    def test_it_flags_every_instruction_to_edit_the_register(self):
        for line in MUST_FLAG:
            with self.subTest(line=line):
                self.assertTrue(direct_edits(line), "not flagged: %r" % line)

    def test_it_passes_prohibitions_questions_and_descriptions(self):
        for line in MUST_PASS:
            with self.subTest(line=line):
                self.assertEqual([], direct_edits(line), "flagged: %r" % line)


class NoSkillEditsTheRegisterDirectly(unittest.TestCase):

    def test_the_corpus_was_read(self):
        names = {Path(p).parent.name for p in skill_files()}
        missing = [n for n in NAMED_BY_520 if n not in names]
        self.assertEqual([], missing, "skills #520 names were not found under .claude/skills/")
        self.assertNotIn(OWNER.parent.name, names, "the owner skill must be left out")

    def test_no_skill_tells_the_reader_to_edit_specs_invariants_md(self):
        found = []
        for path in skill_markdown():
            for hit in direct_edits(read(Path(path))):
                found.append("%s: %s" % (Path(path).relative_to(REPO_ROOT).as_posix(), hit))
        self.assertEqual(
            [], found,
            "only /review-invariants edits specs/INVARIANTS.md; a skill writes a DEFERRED "
            "INVARIANT or PROPOSED AMENDMENT block in specs/IMPLEMENTED.md and tells the "
            "maintainer to run /review-invariants instead:\n  " + "\n  ".join(found))


class EverySkillThatAccountsForAnInvariantNamesTheRoute(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.heading = format_heading(read(OWNER))
        cls.anchor = slug(cls.heading or "")
        cls.derived = [p for p in skill_files() if DUTY.search(" ".join(units(read(p))))]

    def test_the_format_section_was_found(self):
        self.assertIsNotNone(
            self.heading, "review-invariants/SKILL.md has no heading over the block template, "
            "so no pointer can be checked against it")

    def test_the_derived_set_reaches_every_site_520_names(self):
        names = {p.parent.name for p in self.derived}
        missing = [n for n in NAMED_BY_520 if n not in names]
        self.assertEqual([], missing, "the derivation missed skills #520 names: %s" % missing)

    def test_each_names_review_invariants_and_points_to_the_formats(self):
        found = []
        for path in self.derived:
            for problem in route_problems(path, read(path), self.anchor):
                found.append("%s: %s" % (path.relative_to(REPO_ROOT).as_posix(), problem))
        self.assertEqual([], found, "\n  ".join(found))

    def test_every_pointer_in_any_skill_lands_on_the_format_heading(self):
        found = []
        for path in skill_markdown():
            path = Path(path)
            for problem in pointer_problems(path, read(path), self.anchor):
                found.append("%s: %s" % (path.relative_to(REPO_ROOT).as_posix(), problem))
        self.assertEqual([], found, "\n  ".join(found))


class Inv309IsCitedForWhatItStates(unittest.TestCase):

    def test_every_inv_309_citation_is_about_the_issue_driven_path(self):
        found = []
        for path in corpus_files(".claude/skills", suffixes=(".md",)):
            for sentence in misscoped_309(read(Path(path))):
                found.append("%s: %s" % (Path(path).relative_to(REPO_ROOT).as_posix(), sentence))
        self.assertEqual(
            [], found,
            "INV-309 binds only the issue-driven development path (/implement-github-issue); "
            "these cite it for more:\n  " + "\n  ".join(found))

    def test_every_inv_309_citation_in_python_is_about_the_issue_driven_path(self):
        found = []
        for path, every_string in python_files():
            for sentence in misscoped_309_python(read(path), every_string):
                found.append("%s: %s" % (path.relative_to(REPO_ROOT).as_posix(), sentence))
        self.assertEqual(
            [], found,
            "INV-309 binds only the issue-driven development path (/implement-github-issue); "
            "the record a maintainer run owes is INV-365's. These cite INV-309 for more:\n  "
            + "\n  ".join(found))

    def test_the_python_reading_reaches_both_trees(self):
        files = python_files()
        names = {p.relative_to(REPO_ROOT).as_posix() for p, _every in files}
        for floor in (".claude/skills/release-cycle/cycle.py",
                      "tests/test_unattended_loop_is_label_gated.py",
                      "tests/test_compact_dev_environment_leaves_specs_frozen.py"):
            with self.subTest(file=floor):
                self.assertIn(floor, names)
        self.assertFalse(any(every for p, every in files if p.parts[-2] == "tests"),
                         "a test's fixture strings must not be read as its own credits")

    def test_correct_credits_pass(self):
        for line in MUST_PASS_309:
            with self.subTest(line=line):
                self.assertEqual([], misscoped_309(line))


class NegativeControls(unittest.TestCase):
    """Each mutation of the live text must turn its check red."""

    @classmethod
    def setUpClass(cls):
        cls.anchor = slug(format_heading(read(OWNER)) or "")
        cls.auto_test = SKILLS / "auto-test" / "SKILL.md"
        cls.live = read(cls.auto_test)

    def _mutate(self, old, new):
        self.assertIn(old, self.live, "the control's target is gone, so it would mutate nothing")
        mutated = self.live.replace(old, new, 1)
        self.assertNotEqual(self.live, mutated, "the control changed nothing")
        return mutated

    def test_restoring_auto_tests_pre_520_sentence_fails(self):
        live_tail = "and either queue the invariant it establishes"
        start = self.live.index(live_tail)
        end = self.live.index("(INV-300), then tell the maintainer to run `/review-invariants` "
                              "(INV-365).",
                              start)
        end = self.live.index("\n", end)
        restored = self.live[:start] + AUTO_TEST_BEFORE_520 + self.live[end:]
        self.assertTrue(direct_edits(restored), "the pre-#520 auto-test sentence passes")

    def test_the_same_sentence_re_wrapped_still_fails(self):
        mutated = self.live.replace(
            "## What to do with a finding\n",
            "## What to do with a finding\n\nThen register or explicitly disclaim the invariant\n"
            "in `specs/INVARIANTS.md`.\n", 1)
        self.assertTrue(direct_edits(mutated), "a re-wrapped direct edit passes")

    def test_a_pointer_to_a_missing_heading_fails(self):
        mutated = self._mutate("SKILL.md#%s)" % self.anchor, "SKILL.md#writing-two)")
        self.assertTrue(route_problems(self.auto_test, mutated, self.anchor))

    def test_a_pointer_to_another_real_heading_fails(self):
        mutated = self._mutate("SKILL.md#%s)" % self.anchor, "SKILL.md#the-three-verdicts)")
        self.assertTrue(route_problems(self.auto_test, mutated, self.anchor))

    def test_a_pointer_to_another_file_fails(self):
        mutated = self._mutate("../review-invariants/SKILL.md#",
                               "../dry-run/review-invariants/SKILL.md#")
        self.assertTrue(pointer_problems(self.auto_test, mutated, self.anchor))

    def test_a_skill_with_no_pointer_fails(self):
        mutated = re.sub(r"\[([^\]]*)\]\([^)]*review-invariants/SKILL\.md#[^)]*\)", r"\1",
                         self.live)
        self.assertNotEqual(self.live, mutated)
        self.assertTrue(route_problems(self.auto_test, mutated, self.anchor))

    def test_a_pointer_without_the_route_fails(self):
        mutated = self.live + (
            "\n\nSee [the formats](../review-invariants/SKILL.md#%s).\n" % self.anchor)
        self.assertTrue(pointer_problems(self.auto_test, mutated, self.anchor))

    def test_restoring_compacts_over_broad_inv_309_citation_fails(self):
        compact = read(SKILLS / "compact-dev-environment" / "SKILL.md")
        old = "never mints an id.**"
        self.assertIn(old, compact)
        mutated = compact.replace(old, "never mints an id (INV-309).**", 1)
        self.assertTrue(misscoped_309(mutated), "an INV-309 citation for the broad rule passes")

    def test_restoring_compacts_step_6_citation_fails(self):
        compact = read(SKILLS / "compact-dev-environment" / "SKILL.md")
        old = ("  ⛔ **Never edit `specs/INVARIANTS.md` here.** (INV-365)\n"
               "  ⛔ (INV-309) Never send an invariant change to")
        self.assertIn(old, compact)
        mutated = compact.replace(
            old, "  ⛔ (INV-309) Never edit `specs/INVARIANTS.md` here, and never send an "
            "invariant change to", 1)
        self.assertTrue(misscoped_309(mutated),
                        "one INV-309 over the register and /implement-github-issue passes")

    def test_restoring_cycles_pre_607_credit_fails(self):
        cycle = read(SKILLS / "release-cycle" / "cycle.py")
        self.assertIn(CYCLE_AFTER_607, cycle, "the control's target is gone")
        self.assertEqual([], misscoped_309_python(cycle, True))
        mutated = cycle.replace(CYCLE_AFTER_607, CYCLE_BEFORE_607, 1)
        self.assertTrue(misscoped_309_python(mutated, True),
                        "cycle.py's pre-#607 'Establishes no invariant (INV-309)' passes")

    def test_restoring_a_wrapped_comment_credit_in_a_test_fails(self):
        path = REPO_ROOT / "tests" / "test_compact_dev_environment_leaves_specs_frozen.py"
        live = read(path)
        old = "in place (INV-365: it changes only through\n#: `/review-invariants`)."
        self.assertIn(old, live, "the control's target is gone")
        self.assertEqual([], misscoped_309_python(live, False))
        mutated = live.replace(old, old.replace("INV-365", "INV-309"), 1)
        self.assertTrue(misscoped_309_python(mutated, False),
                        "an INV-309 credit wrapped across two comment lines passes")

    def test_restoring_a_docstring_credit_in_a_test_fails(self):
        path = REPO_ROOT / "tests" / "test_compact_dev_environment_leaves_specs_frozen.py"
        live = read(path)
        old = "blocks in `specs/IMPLEMENTED.md` (INV-365)."
        self.assertIn(old, live, "the control's target is gone")
        mutated = live.replace(old, "blocks in `specs/IMPLEMENTED.md` (INV-309).", 1)
        self.assertTrue(misscoped_309_python(mutated, False),
                        "an INV-309 credit in a test's docstring passes")

    def test_a_tests_fixture_string_is_not_its_credit(self):
        source = 'FIXTURE = "## ⛔ (INV-309) Invariant capture is a gate on closing"\n'
        self.assertEqual([], misscoped_309_python(source, False))
        self.assertTrue(misscoped_309_python(source, True),
                        "a script's string is the text it writes, so it is read")

    def test_a_renamed_format_heading_fails_the_pointers(self):
        heading = format_heading(read(OWNER))
        self.assertIsNotNone(heading)
        owner = re.sub(r"(?m)^(#{2,6}) %s$" % re.escape(heading), r"\1 Renamed", read(OWNER), 1)
        self.assertNotEqual(read(OWNER), owner, "the control changed nothing")
        self.assertNotEqual(slug(format_heading(owner) or ""), self.anchor)


if __name__ == "__main__":
    unittest.main()
