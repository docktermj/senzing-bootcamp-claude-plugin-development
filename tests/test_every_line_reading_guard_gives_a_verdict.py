"""Every test that reads a corpus one line at a time gives an INV-346 verdict.

INV-346: a guard whose rule is about a phrase or a sentence in Markdown prose matches it across a
line wrap, and a guard that reads single lines on purpose says why. #424, #425 and #418 gave every
line-reading test a verdict by hand, but nothing stopped the next one from landing without one:
`tests/test_env_script_powershell.py` did, added by #419 after #424's sweep (#438).

**The scan.** `line_reading_candidates()` is the candidate scan recorded in the
`shared-wrap-aware-matcher-and-the-387-guard-moves-onto-it` entry of `specs/IMPLEMENTED.md`
("The command, verbatim", #426), copied here as code. That command stays a dated record; this
test neither reads nor runs it. A candidate is a `tests/*.py` file, parsed with `ast`, that both

- reads text one line at a time: it names `.splitlines`, `.readlines` or `.readline`; calls
  `.split` with a newline as its first argument; or iterates an `open(…)` / `StringIO(…)` call
  or a name bound to one; and
- reads a corpus: a string literal outside its docstrings names `plugins/`, `.claude/skills/`,
  `docs/` or the root `README.md` (or the file imports `_maintainer_surface`).

Every candidate is checked, the three precedent guards the ledger's partitions set aside
included. The scan errs wide, so a candidate is a file owed a verdict, not a file known wrong.

**The verdicts.** A candidate passes when its source shows one of:

1. a wrap-aware read: an import from `_wrapped_text` (which covers `match_lines` and `blocks`),
   `re.sub(r"\\s+", " ", …)`, or `" ".join(….split())`, each found in the code by `ast`;
2. a `Line-scoped by design (#NNN…):` marker, saying why the rule is about a line;
3. a `No phrase-level pattern (#NNN…):` marker, saying the line read is of a non-prose or
   out-of-scope corpus, the third verdict #424 and #425 recorded.

The two markers are found by searching the source text, comments included, because a reason
"at the read" is often a comment that `ast` drops. Each must name an issue number.

**What this cannot establish.** The check is per file: a verdict anywhere in a candidate passes
the whole file. It does not establish that each line read in a file is the one its verdict
covers, that a collapse is applied to the text the line read reads, or that a stated reason is
true. Those are a reviewer's call, as they were for #424 and #425.

The negative controls run on in-memory fixture sources, never on files under `tests/`, so a
control cannot add a candidate to the scan.

Enforces **INV-346** (its verdict coverage), with the scan derived on every run (INV-246).

Stdlib only (INV-108).

Source issue: #438.

Run:  python3 -m unittest discover -s tests
"""
import ast
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS = REPO_ROOT / "tests"

# --- The scan, copied from the #426 ledger entry's command (its logic, unchanged) -------------

NEWLINE = {"\n", "\r\n", r"\n", r"\r\n", r"\r?\n"}


def _opens(node):
    return isinstance(node, ast.Call) and (
        getattr(node.func, "id", None) == "open"
        or getattr(node.func, "attr", None) in ("open", "StringIO"))


def reads_line_by_line(tree):
    """True when the module's code reads some text one line at a time (the ledger's `linewise`)."""
    handles = {item.optional_vars.id for node in ast.walk(tree)
               if isinstance(node, (ast.With, ast.AsyncWith))
               for item in node.items
               if _opens(item.context_expr) and isinstance(item.optional_vars, ast.Name)}
    handles |= {target.id for node in ast.walk(tree)
                if isinstance(node, ast.Assign) and _opens(node.value)
                for target in node.targets if isinstance(target, ast.Name)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ("splitlines", "readlines", "readline"):
            return True
        if (isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "split" and node.args
                and isinstance(node.args[0], ast.Constant) and node.args[0].value in NEWLINE):
            return True
        if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            iterated = node.iter
            if (isinstance(iterated, ast.Call) and getattr(iterated.func, "id", None) == "enumerate"
                    and iterated.args):
                iterated = iterated.args[0]
            if _opens(iterated) or (isinstance(iterated, ast.Name) and iterated.id in handles):
                return True
    return False


def corpora_read(tree):
    """The in-scope corpora a module's non-docstring string literals name (the ledger's `corpora`)."""
    docstrings = {id(body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                  for body in [node.body]
                  if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)}
    literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)
                and isinstance(node.value, str) and id(node) not in docstrings]
    segments = [literal.strip("/").split("/") for literal in literals]
    modules = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
               for alias in node.names}
    modules |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    found = set()
    if any("plugins" in parts for parts in segments):
        found.add("plugins/")
    if (any(".claude/skills" in literal for literal in literals)
            or {".claude", "skills"} <= set(literals) or "_maintainer_surface" in modules):
        found.add(".claude/skills/")
    if any("docs" in parts for parts in segments):
        found.add("docs/")
    if any(literal in ("README.md", "./README.md") for literal in literals):
        found.add("README.md")
    return found


def candidate_corpora(source):
    """The corpora a candidate reads, or an empty set when the source is not a candidate."""
    tree = ast.parse(source)
    found = corpora_read(tree)
    return found if found and reads_line_by_line(tree) else set()


def line_reading_candidates():
    """{`tests/<name>.py`: sorted corpora} for every candidate under `tests/`, precedents included."""
    found = {}
    for path in sorted(TESTS.glob("*.py")):
        corpora = candidate_corpora(path.read_text(encoding="utf-8"))
        if corpora:
            found[path.relative_to(REPO_ROOT).as_posix()] = sorted(corpora)
    return found


# --- The verdicts -----------------------------------------------------------------------------

LINE_SCOPED = re.compile(r"Line-scoped by design \(#\d+[^)\n]*\):")
NO_PHRASE_LEVEL_PATTERN = re.compile(r"No phrase-level pattern \(#\d+[^)\n]*\):")
WHITESPACE_RUN = r"\s+"

ACCEPTED = (
    "a wrap-aware read (an import from `_wrapped_text`, `re.sub(r\"\\s+\", \" \", …)`, or "
    "`\" \".join(….split())`); a \"Line-scoped by design (#NNN): <reason>\" marker; or a "
    "\"No phrase-level pattern (#NNN): <reason>\" marker, in the docstring or at the read")


def _is_whitespace_collapse(node):
    """`re.sub(r"\\s+", " ", …)`: a call to `sub` on `re` whose pattern and replacement are those."""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "sub" and getattr(node.func.value, "id", None) == "re"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Constant) and node.args[0].value == WHITESPACE_RUN
            and isinstance(node.args[1], ast.Constant) and node.args[1].value == " ")


def _is_join_of_split(node):
    """`" ".join(….split())`: a join on one space of an argument-free `split()`."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join" and isinstance(node.func.value, ast.Constant)
            and node.func.value.value == " " and len(node.args) == 1):
        return False
    inner = node.args[0]
    return (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "split" and not inner.args and not inner.keywords)


def wrap_aware_reads(tree):
    """The wrap-aware reads a module's code makes, by name; empty when it makes none."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "_wrapped_text":
            found.add("_wrapped_text import")
        elif isinstance(node, ast.Import) and any(a.name == "_wrapped_text" for a in node.names):
            found.add("_wrapped_text import")
        elif _is_whitespace_collapse(node):
            found.add("re.sub collapse")
        elif _is_join_of_split(node):
            found.add("join-of-split collapse")
    return found


def verdicts(source):
    """Every verdict a source shows: its wrap-aware reads, plus each marker it carries."""
    found = wrap_aware_reads(ast.parse(source))
    if LINE_SCOPED.search(source):
        found.add("Line-scoped by design")
    if NO_PHRASE_LEVEL_PATTERN.search(source):
        found.add("No phrase-level pattern")
    return found


def offenders(sources):
    """[(name, corpora)] for every candidate in {name: source} that shows no verdict."""
    missing = []
    for name, source in sorted(sources.items()):
        corpora = candidate_corpora(source)
        if corpora and not verdicts(source):
            missing.append((name, sorted(corpora)))
    return missing


def report(missing):
    rows = "".join("\n  %s  [%s]" % (name, ", ".join(corpora)) for name, corpora in missing)
    return ("%d test file(s) read a corpus one line at a time and give no INV-346 verdict:%s\n"
            "Give each one of: %s." % (len(missing), rows, ACCEPTED))


# --- Fixtures for the controls: in-memory sources, never files under tests/ --------------------

BARE = (
    'from pathlib import Path\n'
    'TEXT = Path("plugins/x/SKILL.md").read_text()\n'
    'def hits():\n'
    '    return [line for line in TEXT.splitlines() if "no flag" in line]\n')

WITH_WRAPPED_TEXT_IMPORT = "from _wrapped_text import match_lines\n" + BARE
WITH_RE_SUB_COLLAPSE = BARE + 'import re\nFLAT = re.sub(r"\\s+", " ", TEXT)\n'
WITH_JOIN_COLLAPSE = BARE + 'FLAT = " ".join(TEXT.split())\n'
# The markers are assembled at run time, so this module's own text carries neither: were it ever a
# candidate, a fixture could not pass it.
ISSUE = "(#" + "999):"
WITH_LINE_SCOPED_MARKER = BARE.replace(
    "def hits():\n",
    "def hits():\n    # Line-scoped by design " + ISSUE + " a table row is one line.\n")
WITH_NO_PHRASE_MARKER = '"""No phrase-level pattern ' + ISSUE + ' reads script output."""\n' + BARE

FORMS = {
    "_wrapped_text import": WITH_WRAPPED_TEXT_IMPORT,
    "re.sub collapse": WITH_RE_SUB_COLLAPSE,
    "join-of-split collapse": WITH_JOIN_COLLAPSE,
    "Line-scoped by design": WITH_LINE_SCOPED_MARKER,
    "No phrase-level pattern": WITH_NO_PHRASE_MARKER,
}


class EveryCandidateGivesAVerdict(unittest.TestCase):
    def test_the_scan_finds_candidates(self):
        # Vacuity floor: a scan that matched nothing would pass the coverage check below.
        # 138 candidates at 25c6bc0 (#438's ledger entry); the floor sits well under that.
        self.assertGreater(len(line_reading_candidates()), 100)

    def test_every_line_reading_test_gives_a_verdict(self):
        sources = {name: (REPO_ROOT / name).read_text(encoding="utf-8")
                   for name in line_reading_candidates()}
        missing = offenders(sources)
        self.assertEqual([], missing, report(missing))

    def test_the_precedent_guards_are_checked_too(self):
        # #387's guard is matched by the scan and reads through `_wrapped_text`; #390's is matched
        # and carries its marker. #381's is not matched (it reads no single lines), so it owes
        # nothing here. None of the three is set aside.
        candidates = line_reading_candidates()
        for name in ("tests/test_why_key_details_flag_is_cited_not_guessed.py",
                     "tests/test_bundled_script_and_production_paths.py"):
            self.assertIn(name, candidates)
            self.assertTrue(verdicts((REPO_ROOT / name).read_text(encoding="utf-8")), name)
        self.assertNotIn("tests/test_existing_install_still_runs_the_env_script.py", candidates)


class TheControlsShowEachVerdict(unittest.TestCase):
    def test_the_bare_fixture_is_a_candidate(self):
        self.assertEqual({"plugins/"}, candidate_corpora(BARE))

    def test_a_candidate_with_no_verdict_fails(self):
        missing = offenders({"fixture_bare.py": BARE})
        self.assertEqual([("fixture_bare.py", ["plugins/"])], missing)
        message = report(missing)
        self.assertIn("fixture_bare.py  [plugins/]", message)
        for verdict in ("_wrapped_text", "Line-scoped by design", "No phrase-level pattern"):
            self.assertIn(verdict, message)

    def test_each_accepted_form_passes_on_its_own(self):
        for form, source in FORMS.items():
            with self.subTest(form=form):
                self.assertTrue(candidate_corpora(source), "the fixture is still a candidate")
                self.assertEqual({form}, verdicts(source))
                self.assertEqual([], offenders({"fixture.py": source}))

    def test_a_marker_without_an_issue_number_is_no_verdict(self):
        for marker in ("# Line-scoped by design: a table row is one line.\n",
                       "# No phrase-level pattern: reads script output.\n"):
            with self.subTest(marker=marker):
                source = marker + BARE
                self.assertEqual(set(), verdicts(source))
                self.assertEqual(1, len(offenders({"fixture.py": source})))

    def test_a_collapse_named_only_in_a_string_is_no_verdict(self):
        # A wrap-aware read is found in the code, so a fixture that spells one out in a string
        # literal, as this module's own fixtures do, does not pass on that alone.
        spelled_out = 'from _wrapped_text import match_lines; re.sub(r"\\s+", " ", t); " ".join(t.split())'
        source = BARE + "EXAMPLE = " + repr(spelled_out) + "\n"
        self.assertEqual(set(), verdicts(source))

    def test_a_non_candidate_owes_nothing(self):
        not_line_by_line = 'from pathlib import Path\nTEXT = Path("plugins/x/SKILL.md").read_text()\n'
        no_corpus = 'TEXT = "a\\nb"\nLINES = TEXT.splitlines()\n'
        self.assertEqual([], offenders({"a.py": not_line_by_line, "b.py": no_corpus}))


if __name__ == "__main__":
    unittest.main()
