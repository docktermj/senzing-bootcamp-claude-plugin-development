"""A sentence that credits `auto-test`'s transcript linter names a function the linter runs.

Six invariants (INV-352, INV-353, INV-354, INV-355, INV-357, INV-359) and eight test docstrings
credited `auto-test`'s transcript linter, beside `dry-run` phase 3, with seeing behaviors the
linter has no function for: whether a worked steer is shown, whether requirement rows are faithful,
whether a comparison is honest, whether the right entity is shown, whether a result waits for a
prediction (#514). The #465 sub-issues reused one sentence template, and nobody read the linter's
`CHECKS`. The claim made a gap that only `dry-run` phase 3 can close look closed (defect class 6:
a comment claiming a check that does not exist). The linter cannot grow those functions: its own
docstring says every one is "a count or a regex over text the Bootcamper actually saw", with "no
model, no judgment", and faithful rows, an honest comparison and the right entity are judgments.

So the rule this file enforces is mechanical. **A claim** is one sentence that matches both
``LINTER`` (the linter's two-word name or its module's name, in any case) and ``VERB`` (observe,
observes, check, checks, checked or catches). Whitespace is collapsed first, so a sentence
that wraps across lines is still one sentence. A sentence that says only `dry-run` phase 3
observes the behavior is the correction itself and is not a claim, even where it goes on to name
the linter.

**A claim passes** when it names at least one ``check_*`` function and every one it names is a
function the linter runs: the members of ``CHECKS``, plus each ``check_*`` function ``lint()``
calls itself (``check_apparatus``, run when ``--phase`` is given). The names are read from the
module, imported the way ``tests/test_auto_test_harness.py`` imports it, never from a copied list.

**What is scanned:** the repository's own files under ``tests/`` and ``.claude/skills/``, listed by
``tests/_corpus.py``, and ``specs/INVARIANTS.md``. In a Python file only string literals and
comments are read, so code that imports or runs the linter is not prose. Out of scope, as #514
sets it: ``specs/IMPLEMENTED.md`` (its historical drafts are a dated record), the generated
``invariant-manifest.json``, ``BLUEPRINT.md``, the other frozen files under ``specs/``, and scratch
under ``.claude/worktrees/`` (which ``_corpus`` never lists).

**`INVARIANTS.md` is append-only**, so its false sentences stay for good, and the guard never asks
them to disappear. An entry with a failing claim passes while either holds:

- a later ``Dated note`` in the same entry names a function the linter runs, or says only
  `dry-run` phase 3 observes the behavior; or
- `specs/IMPLEMENTED.md` holds a pending ``PROPOSED AMENDMENT`` block for the entry's id, as
  ``pending_invariants.py`` computes the queue (a held block is not pending).

``test_the_queued_notes_close_the_gap_once_applied`` appends each pending amendment's drafted note
to its entry and checks the file still passes with no block pending, so the guard holds both
before and after `/review-invariants` applies them.

⛔ **What this cannot establish:** that a function the claim names really observes the behavior
the sentence attributes to it. The guard proves the name is real, which is what makes the claim
checkable by a reader; it does not read the function. Nor does it see a claim phrased without
the linter's name ("auto-test catches this") or without one of the six verbs.

Stdlib only (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import io
import re
import sys
import tokenize
import unittest
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / ".claude" / "skills" / "auto-test"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
PENDING_HELPER = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"

sys.path.insert(0, str(HARNESS))

#: Generated files inside the scanned subtrees (#514's out-of-scope list), repo-relative.
GENERATED = frozenset({".claude/skills/review-invariants/invariant-manifest.json"})

#: The linter's name. ``\s+`` because a sentence may wrap between the two words.
LINTER = re.compile(r"(?i)\btranscript\s+linter\b|transcript_lint")
#: A verb of checking, as a whole word (``check_x`` is a name, not the verb).
VERB = re.compile(r"(?i)\b(?:observes?|checks?|checked|catches)\b")
#: The correction #514 asks for. A sentence carrying it denies the credit rather than giving it.
ONLY_DRY_RUN = re.compile(r"(?i)\bonly\s+`?dry-run`?\s+phase\s+3\s+observes?\b")
#: A function the sentence names. Only ``check_*`` names count; ``\b`` keeps ``_check_x`` out.
NAMED = re.compile(r"\bcheck_\w+")
#: Where one sentence ends: terminal punctuation (with any closing emphasis, quote or bracket)
#: before whitespace, a blank line, or a new Markdown block (list item, table row, heading, quote).
BOUNDARY = re.compile(
    r"[.!?][*_)`'\"]*\s+"
    r"|\n[ \t]*\n\s*"
    r"|\n[ \t]*(?=(?:[-*+>|]|#{1,6}|\d+[.)])\s)")
#: Where one registered invariant ends: the next entry, a heading, a blank line, or the end.
ENTRY_END = r"(?=\n(?:- \*\*INV-\d{3}\*\*|#|[ \t]*\n)|\Z)"
#: One registered invariant, from its header to ``ENTRY_END``.
ENTRY = re.compile(r"^- \*\*(INV-\d{3})\*\*.*?" + ENTRY_END, re.M | re.S)
#: A dated note appended to an entry.
DATED_NOTE = re.compile(r"\*\*Dated note, \d{4}-\d{2}-\d{2}")


def _load_linter():
    import transcript_lint
    return transcript_lint


def runs(module=None):
    """The ``check_*`` functions the linter runs: ``CHECKS``, and those ``lint()`` calls itself."""
    module = module or _load_linter()
    names = {f.__name__ for f in module.CHECKS}
    names.update(n for n in module.lint.__code__.co_names
                 if n.startswith("check_") and callable(getattr(module, n, None)))
    return frozenset(names)


def pending_amendments():
    """Parsed pending ``PROPOSED AMENDMENT`` blocks, from `pending_invariants.py`'s own queue."""
    spec = importlib.util.spec_from_file_location("pending_invariants", PENDING_HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pending, _held = mod.queue()
    return [p for p in pending if p["amends"]]


def sentences(text):
    """``(offset, raw)`` for each sentence of ``text``; ``offset`` indexes ``text``."""
    pos = 0
    for m in BOUNDARY.finditer(text):
        yield pos, text[pos:m.start()]
        pos = m.end()
    yield pos, text[pos:]


def claims(text):
    """``(offset, sentence, claimed)`` for each claim; ``offset`` is the linter's mention."""
    for offset, raw in sentences(text):
        flat = " ".join(raw.split())
        mention = LINTER.search(raw)
        if mention and VERB.search(flat) and not ONLY_DRY_RUN.search(flat):
            yield offset + mention.start(), flat, sorted(set(NAMED.findall(flat)))


def failing(claimed, run):
    """True when a claim names no function, or names one the linter does not run."""
    return not claimed or any(name not in run for name in claimed)


def describe(where, line, claimed, run):
    named = ", ".join(f"`{n}`" for n in claimed) if claimed else "none named"
    return (f"{where}:{line}: credits the transcript linter; function named: {named}; "
            f"the linter runs: {', '.join(sorted(run))}")


def python_prose(source):
    """``(first_line, text)`` for each string literal and each run of comment lines."""
    middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    out, comment, comment_start, last_row = [], [], None, None
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return [(1, source)]
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            if comment and tok.start[0] != last_row + 1:
                out.append((comment_start, "\n".join(comment)))
                comment = []
            if not comment:
                comment_start = tok.start[0]
            comment.append(tok.string.lstrip("#"))
            last_row = tok.start[0]
        elif tok.type in (tokenize.STRING, middle):
            out.append((tok.start[0], tok.string))
    if comment:
        out.append((comment_start, "\n".join(comment)))
    return out


def text_problems(where, text, run, first_line=1):
    """Problems in plain prose: every claim must name a function the linter runs."""
    problems = []
    for offset, _flat, claimed in claims(text):
        if failing(claimed, run):
            line = first_line + text.count("\n", 0, offset)
            problems.append(describe(where, line, claimed, run))
    return problems


def file_problems(where, text, run):
    if where.endswith(".py"):
        problems = []
        for first_line, prose in python_prose(text):
            problems.extend(text_problems(where, prose, run, first_line))
        return problems
    return text_problems(where, text, run)


def note_settles(note, run):
    """A dated note settles a claim when it names a run function or says only phase 3 observes."""
    flat = " ".join(note.split())
    return bool(ONLY_DRY_RUN.search(flat) or any(re.search(rf"\b{n}\b", flat) for n in run))


def invariants_problems(text, run, pending_ids, where="specs/INVARIANTS.md"):
    """Problems in `INVARIANTS.md`, with the entry-level allowances #514 sets."""
    problems, covered = [], []
    for entry in ENTRY.finditer(text):
        covered.append((entry.start(), entry.end()))
        inv, body = entry.group(1), entry.group(0)
        notes = list(DATED_NOTE.finditer(body))
        for offset, _flat, claimed in claims(body):
            if not failing(claimed, run) or inv in pending_ids:
                continue
            later = [m for m in notes if m.start() > offset]
            settled = False
            for i, m in enumerate(later):
                end = later[i + 1].start() if i + 1 < len(later) else len(body)
                if note_settles(body[m.start():end], run):
                    settled = True
                    break
            if not settled:
                line = 1 + text.count("\n", 0, entry.start() + offset)
                problems.append(describe(where, line, claimed, run)
                                + f"; {inv} carries no later dated note naming one, or saying "
                                  "only `dry-run` phase 3 observes it, and no pending PROPOSED "
                                  "AMENDMENT block")
    # Text outside every entry (the preamble, the index) has no note mechanism: strict.
    outside, pos = [], 0
    for start, end in covered:
        outside.append(text[pos:start] + "\n" * text.count("\n", start, end))
        pos = end
    outside.append(text[pos:])
    problems.extend(text_problems(where, "".join(outside), run))
    return problems


def scanned_files():
    files = []
    for path in corpus_files("tests", ".claude/skills"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in GENERATED:
            continue
        if rel.startswith("tests/") and path.suffix != ".py":
            continue
        files.append((rel, path))
    return files


def applied(text, amendments):
    """``text`` with each amendment's drafted dated note appended to its entry."""
    for p in amendments:
        at = p["wording"].find("(⚠️ **Dated note")
        if at < 0:
            continue
        note = p["wording"][at:]
        entry = re.search(rf"^- \*\*{p['amends']}\*\*.*?" + ENTRY_END, text, re.M | re.S)
        if entry:
            text = text[:entry.end()] + " " + note + text[entry.end():]
    return text


class TheRunSetIsReadFromTheLinter(unittest.TestCase):
    def test_the_run_set_holds_checks_and_check_apparatus(self):
        run = runs()
        linter = _load_linter()
        for f in linter.CHECKS:
            self.assertIn(f.__name__, run)
        self.assertIn("check_apparatus", run,
                      "lint() no longer runs check_apparatus itself, or this reader missed it")

    def test_a_function_the_linter_does_not_run_is_not_in_the_set(self):
        self.assertNotIn("_prose_after_question", runs())
        self.assertNotIn("check_grading", runs())


class EveryClaimNamesARunFunction(unittest.TestCase):
    def test_tests_and_dev_skills(self):
        run = runs()
        files = scanned_files()
        self.assertTrue(any(rel.startswith("tests/") for rel, _ in files))
        self.assertTrue(any(rel.startswith(".claude/skills/") for rel, _ in files))
        problems = []
        for rel, path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            problems.extend(file_problems(rel, text, run))
        self.assertEqual([], problems, "\n" + "\n".join(problems))

    def test_invariants(self):
        pending_ids = {p["amends"] for p in pending_amendments()}
        problems = invariants_problems(INVARIANTS.read_text(encoding="utf-8"), runs(), pending_ids)
        self.assertEqual([], problems, "\n" + "\n".join(problems))

    def test_the_queued_notes_close_the_gap_once_applied(self):
        """After `/review-invariants` applies every pending note, nothing pending is needed."""
        text = applied(INVARIANTS.read_text(encoding="utf-8"), pending_amendments())
        problems = invariants_problems(text, runs(), pending_ids=set())
        self.assertEqual([], problems, "\n" + "\n".join(problems))


#: Built from parts, so this file's own prose holds no claim (it is scanned too).
NAME = "transcript" + " linter"
MODULE = "transcript" + "_lint"
#: Fixture ids, built from parts so `citations.py verify` does not read them as citations.
FAKE, OTHER = "INV-" + "900", "INV-" + "901"
RUN = frozenset({"check_one_pointer_per_turn", "check_repeat_questions", "check_apparatus"})


class Controls(unittest.TestCase):
    def test_a_claim_naming_a_function_the_linter_does_not_run_fails(self):
        text = f"Only a run shows it; the {NAME} observes it with `check_grading`."
        problems = text_problems("x.md", text, RUN)
        self.assertEqual(1, len(problems))
        self.assertIn("`check_grading`", problems[0])
        self.assertIn("check_one_pointer_per_turn", problems[0])

    def test_a_claim_naming_one_real_and_one_unreal_function_fails(self):
        text = f"The {NAME} checks it with `check_repeat_questions` and `check_grading`."
        self.assertEqual(1, len(text_problems("x.md", text, RUN)))

    def test_a_bare_claim_fails(self):
        text = f"Those are properties of a run; `dry-run` phase 3 and the {NAME} observe them."
        problems = text_problems("x.md", text, RUN)
        self.assertEqual(1, len(problems))
        self.assertIn("none named", problems[0])
        self.assertIn("x.md:1:", problems[0])

    def test_a_claim_wrapped_across_two_lines_fails_at_its_line(self):
        text = ("Intro line.\nThose are properties of a run; `dry-run` phase 3 and `auto-test`'s\n"
                + NAME.replace(" ", "\n") + " observe\nthem. Next sentence.")
        problems = text_problems("x.md", text, RUN)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("x.md:3:", problems[0])

    def test_the_module_spelling_counts_as_the_linter(self):
        text = "The only mechanism that checks it is " + "transcript" + "_lint.py."
        self.assertEqual(1, len(text_problems("x.md", text, RUN)))

    def test_a_claim_naming_a_real_check_passes(self):
        text = (f"Checked at runtime by the {NAME}'s\n`check_one_pointer_per_turn`, against "
                "real transcripts.")
        self.assertEqual([], text_problems("x.md", text, RUN))

    def test_the_correction_is_not_a_claim(self):
        text = (f"Those are properties of a run; only `dry-run` phase 3 observes them, and the "
                f"{NAME} has no check for them.")
        self.assertEqual([], text_problems("x.md", text, RUN))

    def test_a_mention_without_a_verb_is_not_a_claim(self):
        self.assertEqual([], text_problems("x.md", f"The {NAME} moved.", RUN))

    def test_python_code_is_not_prose_but_its_strings_and_comments_are(self):
        source = ("import transcript_lint as lint\n"
                  "lint.check_one_pointer_per_turn(turns)  # " + f"the {NAME} checks this\n"
                  "x = 1\n")
        problems = file_problems("t.py", source, RUN)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("t.py:2:", problems[0])
        doc = '"""Docstring.\n\nThe ' + NAME + ' observes\nit."""\nimport ' + MODULE + '\n'
        problems = file_problems("t.py", doc, RUN)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("t.py:3:", problems[0])


class InvariantsControls(unittest.TestCase):
    CLAIM = (f"- **{FAKE}** — A rule. Enforced by `tests/x.py`; `dry-run` phase 3 and "
             f"`auto-test`'s {NAME} observe that. (Source: `x`, 2026-10-11.)")

    def test_an_entry_with_a_claim_and_no_note_or_block_fails(self):
        problems = invariants_problems("# Head\n\n" + self.CLAIM + "\n", RUN, set())
        self.assertEqual(1, len(problems), problems)
        self.assertIn("specs/INVARIANTS.md:3:", problems[0])
        self.assertIn(FAKE, problems[0])

    def test_a_pending_block_for_the_id_passes(self):
        self.assertEqual([], invariants_problems(self.CLAIM, RUN, {FAKE}))

    def test_a_pending_block_for_another_id_does_not(self):
        self.assertEqual(1, len(invariants_problems(self.CLAIM, RUN, {OTHER})))

    def test_a_later_note_saying_only_phase_3_observes_passes(self):
        text = self.CLAIM + (" (⚠️ **Dated note, 2026-10-12 (#514): only `dry-run` phase 3 "
                             "observes that.** The rules above still bind.)")
        self.assertEqual([], invariants_problems(text, RUN, set()))

    def test_a_later_note_naming_a_run_function_passes(self):
        text = self.CLAIM + (" (⚠️ **Dated note, 2026-10-12 (#514): the function is "
                             "`check_repeat_questions`.**)")
        self.assertEqual([], invariants_problems(text, RUN, set()))

    def test_a_note_that_settles_nothing_fails(self):
        text = self.CLAIM + " (⚠️ **Dated note, 2026-10-12 (#514): an unrelated change.**)"
        self.assertEqual(1, len(invariants_problems(text, RUN, set())))

    def test_a_note_before_the_claim_does_not_settle_it(self):
        text = (f"- **{FAKE}** — A rule. (⚠️ **Dated note, 2026-10-01 (#1): only `dry-run` "
                f"phase 3 observes it.**) Later text: the {NAME} checks it. (Source: `x`.)")
        self.assertEqual(1, len(invariants_problems(text, RUN, set())))

    def test_the_original_sentence_may_stay(self):
        """Append-only: the false sentence is still there after the note, and that passes."""
        text = self.CLAIM + (" (⚠️ **Dated note, 2026-10-12 (#514): only `dry-run` phase 3 "
                             "observes that.**)")
        self.assertIn(f"{NAME} observe that", text)
        self.assertEqual([], invariants_problems(text, RUN, set()))

    def test_a_claim_outside_every_entry_is_strict(self):
        text = f"# Head\n\nThe {NAME} checks every rule.\n\n" + self.CLAIM
        problems = invariants_problems(text, RUN, {FAKE})
        self.assertEqual(1, len(problems), problems)
        self.assertIn("specs/INVARIANTS.md:3:", problems[0])

    def test_applying_a_drafted_note_closes_the_entry(self):
        block = {"amends": FAKE, "wording": "… (⚠️ **Dated note, 2026-10-12 (#514): only "
                 "`dry-run` phase 3 observes that.** The rules above still bind.)"}
        self.assertEqual([], invariants_problems(applied(self.CLAIM, [block]), RUN, set()))


if __name__ == "__main__":
    unittest.main()
