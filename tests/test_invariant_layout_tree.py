"""INV-202: INV-050's layout tree must stay reachable — every entry produced, or annotated.

INV-050 states "The generated Bootcamp project MUST follow this layout" followed by a
fenced tree in `specs/INVARIANTS.md`. The tree is **correct today**, with every entry
accounted for (how many it holds is `EXPECTED_*` below, the INV-265 floor, not a claim made
here), and until this file nothing checked that it stays correct. No test parsed the tree; `tests/test_bundled_script_and_production_paths.py:14`
mentions INV-050 only in a docstring about `src/scripts/`.

The rule enforced here is **INV-202**: every leaf entry is either **referenced** somewhere
under `plugins/`, or **annotated** in its own comment as `reserved | superseded | legacy |
future`, and an unproduced entry gains the annotation rather than being deleted.
⚠️ **"Referenced" means by project-relative path** (#226): each entry's path is rebuilt from
the tree's indentation and that is what is probed, so `docs/README.md` no longer resolves on
every `README.md` the plugin mentions, as it did when the probe was the leaf name. It fails
on a future entry added without an annotation, and on an existing entry that quietly loses
its producer.

⚠️ **What this file must never assert.** A previous spec
(`specs/inv050-layout-tree-names-three-artifacts-nothing-produces.md`) claimed
`config/session_log.jsonl`, `config/visualization_tracker.json` and
`docs/completion_summary.md` were unproduced *and* unannotated, and therefore a defect.
That claim is false — all three carry `(reserved)`, added deliberately on 2026-07-17 via
`specs/layout-tree-reconciliation.md` (commit `cc46a55`). Those entries are **correctly
accounted for**, and a test encoding the opposite would re-enshrine the false claim.

That spec went wrong by running `line.split("#")[0]` before matching, which discards the
comment column — the only place the annotation lives. So the comment column is
**load-bearing data**, and `test_the_predicate_requires_the_comment_column` pins it
directly on the predicate rather than trusting the extractor to be read correctly.

Four parsing hazards are live in the current tree; each has its own test, because a
later simplification that drops one would otherwise pass silently:

1. The comment column must be kept (above).
2. `backups/` carries a **two-line** comment; the second line has no filename and must not
   become an entry.
3. `docs/stakeholder_summary_module{n}.md` is a **placeholder** — it never appears verbatim
   under `plugins/` (the real files are `stakeholder_summary_module1.md` and
   `_module6.md`), so it resolves on the prefix before `{`.
4. The path is rebuilt from indentation, so `data/backups/` and the top-level `backups/` get
   distinct paths, and the `backups/` continuation line must not break the path of
   `backups/packages/` beneath it.

⚠️ **Two leaves have no producer and are pinned by their dated annotation** (#226):
`docs/README.md` is named once, by a line saying to skip it, and `src/utils/` only by
graduation's copy table, which copies it if present. Each passes only when INV-050's tree
carries its annotation with a date, as `/review-invariants` applied it on 2026-09-30. Until
then the pin also passed while a pending `PROPOSED AMENDMENT to INV-050` block carried the
annotated tree line; that branch is gone (#288).

⚠️ **One entry the tree omitted is pinned in two states** (#286): Module 6 writes
subset files under `data/subsets/`, which the tree did not name. The pin passes when the
tree has an entry at `data/subsets/`, or while a pending `PROPOSED AMENDMENT to INV-050` block
carries its tree line byte for byte. `/review-invariants` applied that block on 2026-09-30,
inserting the entry and bumping `EXPECTED_DIR_ENTRIES` from 31 to 32 in the same edit.

Stdlib-only and no `plugins/` import (INV-108). The extraction is pure text over
`specs/INVARIANTS.md` and the corpus is read with `pathlib`, so nothing shells out to
`grep` and nothing depends on the platform's path separator — the `/` inside a probed
path is the tree's own textual convention, matched against file *content*, not a filesystem
path.

Source: `specs/inv050-tree-has-no-reachability-guard.md`.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
PLUGINS = REPO_ROOT / "plugins"
LEDGER_HELPER = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"

TREE_HEADING = "## INV-050: Project layout"

# Box-drawing and whitespace that prefixes a tree entry's name.
BOX_CHARS = " \t│├└─"

# An entry the tree says is deliberately not produced.
ANNOTATION = re.compile(r"reserved|superseded|legacy|future", re.IGNORECASE)

#: The tree's indentation step: `├── ` and `│   ` are each four columns wide.
INDENT = 4

#: #226: the two leaves nothing produces, and the annotation each carries. Pinned by
#: `TheUnproducedLeavesCarryADatedAnnotation`.
UNPRODUCED_LEAVES = {"docs/README.md": "future", "src/utils/": "reserved"}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

#: #286: entries the tree omits, each with the tree line a pending INV-050 amendment inserts,
#: byte for byte. Pinned in two states by `TheOmittedEntriesArePinnedInTwoStates`.
TWO_STATE_ADDITIONS = {
    "data/subsets/": "  │   ├── subsets/                       # License- or volume-capped "
                     "load subsets (Module 6; not copied at graduation)",
}

# Derived 2026-08-11 by running extract_tree() against the tree as it then stood, NOT
# copied from any spec -- two specs disagree on this count (one says "53 entries / 23
# files") because they differ on what to include. What these numbers count:
#   * the root line (`senzing-bootcamp/`) is EXCLUDED -- it is the tree's root, not an entry
#   * continuation lines (comment-only, no name) are EXCLUDED from both, counted separately
#   * the placeholder entry `stakeholder_summary_module{n}.md` IS counted, as one file
EXPECTED_FILE_ENTRIES = 24
#: 30 -> 31 on 2026-08-26: `backups/packages/` was added as its own leaf when
#: `/package-bootcamp` began writing transferable archives there
#: (`specs/the-bootcamp-cannot-leave-the-machine-it-was-built-on.md`). Given its own entry rather
#: than a comment on `backups/` because a comment-only continuation line is not an entry and this
#: is a real directory the plugin writes to -- which is also what keeps INV-202 satisfiable for it.
#: 31 -> 32 on 2026-09-30: `data/subsets/` was added when `/review-invariants` applied #286's
#: INV-050 amendment. Module 6 already wrote subset files there; only the tree omitted it.
EXPECTED_DIR_ENTRIES = 32
EXPECTED_CONTINUATION_LINES = 1


class Entry:
    """One leaf of the tree, with its comment column intact."""

    def __init__(self, name, comment, line_number, path=None, depth=None, left=""):
        self.name = name
        self.comment = comment
        self.line_number = line_number
        #: The project-relative path, rebuilt from the tree's indentation. Defaults to the
        #: name, which is the path of a top-level entry.
        self.path = name if path is None else path
        self.depth = depth
        #: The line up to its comment, box-drawing included: what identifies it byte for byte.
        self.left = left
        self.is_dir = name.endswith("/")

    @property
    def probe(self):
        """The literal string to look for under `plugins/`: the project-relative path.

        A placeholder entry (`stakeholder_summary_module{n}.md`) never appears verbatim,
        so it resolves on the prefix before the brace.
        """
        return self.path.split("{")[0]

    def __repr__(self):
        return "%s (INVARIANTS.md:%d)" % (self.path, self.line_number)


def extract_tree(text=None):
    """Return (root_name, entries, continuation_line_count) from INV-050's fenced tree.

    Entries keep their comment. Names are NOT unique -- `data/backups/` and the
    top-level `backups/` both reduce to `backups/` -- so this returns a list and callers
    must never key a dict by name. Paths are unique: each is the chain of enclosing
    directories, found by column, plus the name. `text` replaces `specs/INVARIANTS.md`'s
    text, for the #286 controls.
    """
    if text is None:
        text = INVARIANTS.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        heading = next(i for i, l in enumerate(lines) if l.strip() == TREE_HEADING)
    except StopIteration:
        raise AssertionError(
            "%r not found in specs/INVARIANTS.md — INV-050's section was renamed and this "
            "guard can no longer find its tree" % TREE_HEADING
        )
    opening = next(
        i for i in range(heading, len(lines)) if lines[i].strip().startswith("```text")
    )
    closing = next(i for i in range(opening + 1, len(lines)) if lines[i].strip() == "```")

    root, root_column, parents, entries, continuations = None, 0, [], [], 0
    for offset, line in enumerate(lines[opening + 1 : closing]):
        left, _, comment = line.partition("#")
        name = left.strip(BOX_CHARS).strip()
        if not name:
            # A comment-only continuation line (see `backups/`): no entry here, and it
            # touches no path.
            continuations += 1
            continue
        column = left.index(name)
        if offset == 0:
            root, root_column = name, column
            continue
        # The enclosing directories are the open ones to the left of this column.
        while parents and parents[-1][0] >= column:
            parents.pop()
        path = "".join(parent for _, parent in parents) + name
        entries.append(Entry(name, comment, opening + 2 + offset, path=path,
                             depth=(column - root_column) // INDENT, left=left))
        if name.endswith("/"):
            parents.append((column, name))
    return root, entries, continuations


def plugin_corpus():
    """Every shipped plugin file's text, joined. Read, not grepped (INV-108)."""
    texts = []
    for path in sorted(PLUGINS.rglob("*")):
        if not path.is_file() or "pytest_cache" in path.parts:
            continue
        try:
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(texts)


def is_annotated(entry):
    """The comment column says the entry is deliberately not produced."""
    return ANNOTATION.search(entry.comment) is not None


def is_accounted_for(entry, corpus):
    """Referenced under plugins/ by path, OR annotated. Either arm satisfies INV-050."""
    return is_annotated(entry) or entry.probe in corpus


def pending_amendments(target, ledger=None):
    """Texts of the pending `PROPOSED AMENDMENT to <target>` blocks, as the queue reads them.

    Read through `pending_invariants.py`, never a second parser of the ledger (INV-315): an
    applied block leaves the queue there, so it leaves this list too. `ledger` replaces the
    ledger's text, for the negative controls.
    """
    spec = importlib.util.spec_from_file_location("pending_invariants", LEDGER_HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    if ledger is not None:
        helper.LEDGER = _Text(ledger)
    return [b["text"] for b in helper.blocks() if helper.parse(b)["amends"] == target]


class _Text:
    """A stand-in for the ledger's path: only `read_text` is called on it."""

    def __init__(self, text):
        self.text = text

    def read_text(self, encoding=None):
        return self.text


def is_pinned(entry, word):
    """The tree carries `word` with a date in the entry's comment column."""
    return bool(re.search(word, entry.comment, re.I) and DATE.search(entry.comment))


def is_added(path, tree_line, entries, blocks):
    """The tree has an entry at `path`, or a pending INV-050 block carries `tree_line` exactly."""
    in_tree = any(e.path == path for e in entries)
    return in_tree or any(tree_line in block.splitlines() for block in blocks)


class TreeExtraction(unittest.TestCase):
    """The extractor itself, before anything is concluded from it."""

    def test_the_extraction_found_the_expected_number_of_entries(self):
        """Not vacuous: a parser that silently stops matching passes every other test."""
        _, entries, _ = extract_tree()
        files = [e for e in entries if not e.is_dir]
        dirs = [e for e in entries if e.is_dir]
        self.assertEqual(
            (EXPECTED_FILE_ENTRIES, EXPECTED_DIR_ENTRIES),
            (len(files), len(dirs)),
            "INV-050's tree no longer extracts to the pinned counts. If entries were "
            "genuinely added or removed, update the constants AND the comment saying what "
            "they count. If not, the parser has drifted and every other test in this file "
            "is now checking a shorter list than the tree actually holds.",
        )

    def test_the_root_line_is_not_an_entry(self):
        root, entries, _ = extract_tree()
        self.assertEqual("senzing-bootcamp/", root)
        self.assertNotIn(root, [e.name for e in entries])

    def test_the_continuation_line_is_not_an_entry(self):
        """Hazard 2: `backups/` has a two-line comment; line two has no filename.

        Counted, not merely skipped — if the tree gains a second wrapped comment the
        count changes and this fails, which is the prompt to look.
        """
        _, entries, continuations = extract_tree()
        self.assertEqual(
            EXPECTED_CONTINUATION_LINES,
            continuations,
            "the number of comment-only continuation lines in INV-050's tree changed",
        )
        self.assertEqual(
            [],
            [e for e in entries if "graduation revisit" in e.name],
            "a continuation line was parsed as an entry — its comment text became a name",
        )

    def test_entry_names_are_not_unique(self):
        """`data/backups/` and the top-level `backups/` share a name.

        Pinned so nobody 'simplifies' the extractor into a dict keyed by name: that would
        silently drop one of the two, and the two differ in exactly the way that matters —
        one is annotated `(reserved)`, the other is a real produced directory.
        """
        _, entries, _ = extract_tree()
        names = [e.name for e in entries]
        self.assertNotEqual(
            len(names), len(set(names)),
            "tree entry names are now unique; if that is a real change, this guard can be "
            "relaxed — but a name-keyed dict is still wrong if duplicates ever return",
        )

    def test_entry_paths_are_unique(self):
        """Hazard 4: the two `backups/` get distinct paths, so a path names one entry."""
        _, entries, _ = extract_tree()
        paths = [e.path for e in entries]
        self.assertEqual(
            len(paths), len(set(paths)),
            "two tree entries rebuilt to the same project-relative path; the indentation "
            "walk has lost a parent, and one of them is now probed as the other",
        )

    def test_each_path_matches_its_depth_in_the_tree(self):
        """Hazard 4: every entry has one path component per level of indentation.

        Derived from the column alone, independently of the parent walk, so a continuation
        line that broke the walk (`backups/packages/` read as top level) fails here.
        """
        _, entries, _ = extract_tree()
        wrong = [(e.path, e.depth) for e in entries
                 if not e.path.endswith(e.name)
                 or len(e.path.rstrip("/").split("/")) != e.depth]
        self.assertEqual(
            [], wrong,
            "entry path(s) disagree with their indentation in INV-050's tree",
        )


class AccountedForPredicate(unittest.TestCase):
    """The rule itself, unit-tested on synthetic entries.

    Deliberately independent of what the real tree currently holds, so these keep working
    whatever happens to any particular entry — and so the comment column's role is pinned
    without asserting anything about `session_log.jsonl` and friends.
    """

    def test_the_predicate_requires_the_comment_column(self):
        """Hazard 1: dropping the comment turns an annotated entry into a false defect.

        This is the exact error that produced a spec claiming three correctly-annotated
        entries were a defect: its scan ran `line.split("#")[0]` first.
        """
        corpus = "nothing here mentions the probe"
        unannotated = Entry("zzz_fictional_artifact.json", "", 0)
        annotated = Entry("zzz_fictional_artifact.json", " (reserved)", 0)
        self.assertFalse(
            is_accounted_for(unannotated, corpus),
            "an entry that is neither referenced nor annotated must NOT be accounted for, "
            "or the guard cannot fail on the case it exists for",
        )
        self.assertTrue(
            is_accounted_for(annotated, corpus),
            "an annotated entry must be accounted for even though nothing references it — "
            "if this fails, the comment column is being discarded",
        )

    def test_the_referenced_arm_works_without_an_annotation(self):
        entry = Entry("zzz_fictional_artifact.json", "", 0)
        self.assertTrue(is_accounted_for(entry, "see zzz_fictional_artifact.json here"))

    def test_the_probe_is_the_path_not_the_leaf_name(self):
        """#226: a leaf name mentioned only under another path does not resolve the entry."""
        entry = Entry("README.md", "", 0, path="zzz_fictional_dir/README.md")
        self.assertEqual("zzz_fictional_dir/README.md", entry.probe)
        self.assertFalse(
            is_accounted_for(entry, "see README.md, and other_dir/README.md"),
            "an entry resolved on its leaf name alone; the probe is no longer its path",
        )

    def test_a_placeholder_resolves_on_its_prefix(self):
        """Hazard 3: the literal name with `{n}` matches nothing."""
        entry = Entry("stakeholder_summary_module{n}.md", "", 0)
        self.assertEqual("stakeholder_summary_module", entry.probe)
        self.assertTrue(
            is_accounted_for(entry, "writes stakeholder_summary_module1.md at the end"),
            "a placeholder entry must resolve via its prefix; probing the literal name "
            "reports it unaccounted and invents a defect",
        )


class TreeIsFullyAccountedFor(unittest.TestCase):
    """INV-050 against what ships."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = plugin_corpus()
        cls.entry_list = extract_tree()[1]

    def test_the_corpus_scan_is_not_vacuous(self):
        """An empty corpus would make every entry look unreferenced (or vice versa)."""
        self.assertGreater(
            len(self.corpus), 500_000,
            "the plugin corpus came back far too small; the glob has drifted and the "
            "referenced-arm of every check below is meaningless",
        )

    def test_every_entry_is_referenced_or_annotated(self):
        unaccounted = [
            e for e in self.entry_list if not is_accounted_for(e, self.corpus)
        ]
        self.assertEqual(
            [],
            unaccounted,
            "INV-050 lists artifact(s) that nothing under plugins/ produces or reads, and "
            "that carry no annotation saying so:\n  "
            + "\n  ".join(repr(e) for e in unaccounted)
            + "\nEither produce it, or annotate it in the tree with a dated reason "
            "(`# … (reserved)`) the way the existing unproduced entries are. Do not "
            "delete the entry: INV-050 is cited widely and quoted in audits.",
        )

    def test_a_leaf_name_under_another_path_is_unaccounted(self):
        """Negative control on the real corpus (#226): the name is there, the path is not."""
        entry = Entry("README.md", "", 0, path="zzz_fictional_dir/README.md")
        self.assertIn(entry.name, self.corpus, "the control's leaf name must be in the corpus")
        self.assertNotIn(entry.path, self.corpus, "the control's path must not be")
        self.assertFalse(
            is_accounted_for(entry, self.corpus),
            "an unannotated entry resolved because its leaf name appears under a different "
            "path; INV-202's 'referenced' is by project-relative path",
        )

    def test_the_placeholder_entry_is_still_a_placeholder(self):
        """Guard the guard: if the tree stops using `{n}`, hazard 3's test is theater."""
        placeholders = [e for e in self.entry_list if "{" in e.name]
        self.assertTrue(
            placeholders,
            "no placeholder entry remains in the tree; "
            "test_a_placeholder_resolves_on_its_prefix now proves nothing about it",
        )
        for entry in placeholders:
            with self.subTest(entry=entry.name):
                self.assertNotIn(
                    entry.name, self.corpus,
                    "the literal placeholder name now appears under plugins/, so the "
                    "prefix probe is no longer what makes this entry resolve",
                )
                self.assertIn(entry.probe, self.corpus)


class TheUnproducedLeavesCarryADatedAnnotation(unittest.TestCase):
    """#226: each of `UNPRODUCED_LEAVES` carries its annotation, with a date, in the tree.

    `/review-invariants` applied the annotations on 2026-09-30. Until then this class also
    passed on a pending `PROPOSED AMENDMENT to INV-050` block carrying the annotated line;
    that branch is gone (#288).
    """

    @classmethod
    def setUpClass(cls):
        cls.by_path = {e.path: e for e in extract_tree()[1]}  # paths are unique; names are not

    def leaf(self, path):
        self.assertIn(path, self.by_path, "INV-050's tree no longer has an entry at %s" % path)
        return self.by_path[path]

    def test_each_leaf_carries_its_dated_annotation_in_the_tree(self):
        for path, word in UNPRODUCED_LEAVES.items():
            with self.subTest(leaf=path):
                self.assertTrue(
                    is_pinned(self.leaf(path), word),
                    "%s carries no dated `%s` annotation in INV-050's tree. Nothing produces "
                    "it, so the annotation is what accounts for it (#226)." % (path, word))

    def test_the_negative_controls(self):
        """The real tree with each leaf's annotation, or only its date, removed fails."""
        lines = INVARIANTS.read_text(encoding="utf-8").splitlines()
        for path, word in UNPRODUCED_LEAVES.items():
            real = self.leaf(path)
            at = real.line_number - 1
            left, _, comment = lines[at].partition("#")
            self.assertEqual(real.left, left, "the entry's line number no longer finds its line")
            cases = {
                "annotation removed": re.sub(r"\s*\(%s;[^)]*\)" % word, "", comment, flags=re.I),
                "date removed": DATE.sub("", comment),
            }
            for case, mutated in cases.items():
                with self.subTest(leaf=path, case=case):
                    self.assertNotEqual(comment, mutated, "negative control is stale")
                    copy = lines[:at] + [left + "#" + mutated] + lines[at + 1:]
                    bare = next(e for e in extract_tree("\n".join(copy))[1] if e.path == path)
                    self.assertFalse(is_pinned(bare, word))


class TheOmittedEntriesArePinnedInTwoStates(unittest.TestCase):
    """#286: each of `TWO_STATE_ADDITIONS` is in the tree, or about to be.

    It passes while a pending `PROPOSED AMENDMENT to INV-050` block carries the entry's tree
    line byte for byte, and after `/review-invariants` inserts that line and marks the block
    applied. It fails between the two: the block gone or applied while the tree still lacks
    the entry.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = INVARIANTS.read_text(encoding="utf-8")
        cls.entries = extract_tree()[1]

    def test_each_entry_is_in_the_tree_or_in_a_pending_amendment(self):
        blocks = pending_amendments("INV-050")
        for path, line in TWO_STATE_ADDITIONS.items():
            with self.subTest(entry=path):
                self.assertTrue(
                    is_added(path, line, self.entries, blocks),
                    "INV-050's tree has no entry at %s, and no pending PROPOSED AMENDMENT to "
                    "INV-050 in specs/IMPLEMENTED.md carries its tree line byte for byte. "
                    "Applying the block inserts the line; removing it, or marking it applied "
                    "without the insert, leaves the entry out of the tree." % path)

    def test_the_line_lands_at_its_path_when_inserted(self):
        """The drafted line, inserted where the block says, is one more directory at `path`.

        So applying the block and bumping `EXPECTED_DIR_ENTRIES` by one is the whole edit, and
        the tree arm of the pin then holds on the entry the line creates.
        """
        anchor = "  │   ├── senzing-ready/ "
        for path, line in TWO_STATE_ADDITIONS.items():
            with self.subTest(entry=path):
                lines = self.text.splitlines()
                at = next(i for i, l in enumerate(lines) if l.startswith(anchor))
                lines.insert(at + 1, line)
                entries = extract_tree("\n".join(lines))[1]
                self.assertIn(path, [e.path for e in entries])
                self.assertEqual(
                    EXPECTED_DIR_ENTRIES + 1, len([e for e in entries if e.is_dir]))
                self.assertEqual(
                    self.text.splitlines()[at].index("#"), line.index("#"),
                    "the drafted line's comment column is not aligned with its neighbors")

    def fixture(self, line, marker):
        """A one-block ledger that carries `line` in its fenced tree."""
        return ("## fixture\n\n- **DEFERRED INVARIANT — PROPOSED AMENDMENT to INV-050 — %s.**\n"
                "  ```text\n%s\n  ```\n" % (marker, line))

    def test_the_negative_controls(self):
        """Each arm through the real queue parser, on a tree that lacks each entry."""
        spec = importlib.util.spec_from_file_location("pending_invariants", LEDGER_HELPER)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        awaiting = helper.AMENDMENT_AWAITING
        for path, line in TWO_STATE_ADDITIONS.items():
            bare = [e for e in self.entries if e.path != path]
            name = path.rstrip("/").rsplit("/", 1)[-1] + "/"
            cases = {
                "pending block, exact line": (self.fixture(line, awaiting), True),
                "(a) block removed": ("## fixture\n", False),
                "(a) block marked applied": (self.fixture(line, "applied 2026-10-01"), False),
                "(b) line changed": (self.fixture(line.replace("Module 6", "Module 5"),
                                                  awaiting), False),
            }
            for case, (ledger, expected) in cases.items():
                with self.subTest(entry=path, case=case):
                    blocks = pending_amendments("INV-050", ledger=ledger)
                    self.assertIs(expected, is_added(path, line, bare, blocks))
            with self.subTest(entry=path, case="in the tree"):
                added = bare + [Entry(name, "", 0, path=path)]
                self.assertTrue(is_added(path, line, added, []))
            with self.subTest(entry=path, case="same name at another path"):
                elsewhere = bare + [Entry(name, "", 0, path="zzz_fictional_dir/" + name)]
                self.assertFalse(is_added(path, line, elsewhere, []))


if __name__ == "__main__":
    unittest.main()
