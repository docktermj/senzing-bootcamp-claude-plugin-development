"""`specs/` is a read-only archive; nothing new lands there and nothing quietly leaves.

GitHub issues replaced `specs/` as the tracking mechanism at the **2026-09-15 cutover**
(issue #52). The directory stays as the historical record of why the plugin reads as it
does -- the files `INVARIANTS.md` cites by slug -- but it is closed to new work.

⛔ **A freeze stated only in prose is a convention, not a guarantee.** Every message below
names the freeze and points at `specs/README.md` rather than reporting a bare set difference,
because the failure is meant to be read as "the freeze caught something", not as a puzzle.

⚠️ Every command that wrote here has now been reworked: `/feedback-to-issues` files GitHub
issues (#49), `/implement-spec` was retired (#50, #60), `/unattended-issue-loop` is label-gated
and forbids writing here outright (#51, #69), `/production-readiness-audit` files issues when
attended and records findings in the ledger when not (#69), and `/delegate-to-mcp-server` files
issues and writes nothing here (#114). ⛔ **This paragraph twice outlived the fact it
described** -- it said the audit half was blocked until 2026-09-21, five days after #69 cleared
it, and it named `/delegate-to-mcp-server` as having "no issue yet" for the eight days after
#114 was filed. That is the class #90 records: a fix that lands without sweeping the prose
describing the old world, and this docstring is now its own second instance.

⚠️ **No command being blocked does not retire this guard.** It never depended on one existing:
the freeze is a property of the directory, and a spec file can arrive from a hand-written
file, a reverted branch or a command reworked wrongly. A guard justified by one offender is a
guard that gets deleted when that offender is fixed.

⚠️ **Both directions matter, and they fail differently.**

1. **Nothing new lands** -- a file in `specs/`, of any type, that is neither in the manifest
   nor a live record. This is the freeze being breached: work is being tracked where nobody is
   looking for it, and it will not appear in any issue query.
2. **Nothing quietly leaves** -- a manifest name whose file has gone. This is worse and
   quieter: `INVARIANTS.md` cites specs by slug, and `tests/test_spec_ledger_invariants.py`
   accepts *either* a file under `specs/` *or* an `IMPLEMENTED.md` entry. So deleting a
   spec that happens to be ledgered breaks no existing test while destroying the reasoning
   an invariant points at. Some citations already resolve through the ledger alone
   (`deep-dive-audit-2026-07-28` among them); thinning the archive silently adds to them.

⛔ **No count is asserted anywhere in this file, deliberately** -- the habit
`test_documented_dev_commands_match_the_shipped_set.py` refuses by name. A test pinning
"519 specs" fails on the next legitimate archive operation and teaches whoever fixes it to
bump a number, reproducing the defect inside the guard. The two sets are derived and
compared; their size is not the subject. The anti-vacuity floor below is not a count of the
archive -- it is a check that the glob and the parser both found *something*, without which
a set comparison is satisfied trivially (INV-265).

⚠️ **The live records are exempt and must stay that way.** `IMPLEMENTED.md`, `DECLINED.md`
and `INVARIANTS.md` are historical record and live rules, not transient work items; the
ledger in particular is what some invariant citations resolve through. Freezing them would
break `/review-invariants`, which appends to `INVARIANTS.md` by design. `README.md` is the
freeze notice, and `mcp-coverage.jsonl` is `/delegate-to-mcp-server`'s ledger, a **named**
live exception (#142) rather than one the guard fails to reach: the guard checks **every
file** in `specs/`, not `*.md`. `FROZEN-MANIFEST.txt` is exempt **by name**, as the guard's
own input; it is not a live record. ⚠️ **The list has one home**, the "What stays live" table in
`specs/README.md`: `LIVE_RECORDS` is parsed from it, with no fallback set (#258).
`docs/development.md` and `docs/FAMILY_WORKFLOW.md` §8 each name the live records, and
`TheDocsNameTheLiveRecords` fails when either names a different set. INV-307 is the third copy:
`InvariantThreeOhSevenNamesTheList` passes only on its applied 2026-09-30 note (#226), which
names the table and the five records. Until `/review-invariants` applied that note, the check
also passed on the unapplied amendment block in the ledger; that branch is gone (#288).

⚠️ **No fourth copy, and no pinned count (#291).** Two sites had drifted from the table: a
comment that named four of the five, and an overlay that called every other file under
`specs/` frozen. `NoSecondListOfTheLiveRecords` scans the maintainer files and fails on any
block that names three or more live records unless it names exactly the table's set or names
the "What stays live" table itself, which is the sanctioned alternative to listing.
`NoInstructionPinsASpecCount` fails on an instruction that states how many specs there are,
for the reason the paragraph above gives for this file asserting none. `tests/` is outside
that second scan because test docstrings hold dated measurements.

⚠️ **Enforces INV-307.** It asserts the set in both directions, that the live records exist
and stay out of the frozen set, and that the cutover date is stated in `specs/README.md` rather
than only here.

⛔ It does **NOT** establish that the archive's *contents* are unchanged. The manifest pins
**filenames**, so a frozen spec whose text is rewritten in place passes every assertion below --
the reasoning an invariant cites could be silently replaced and nothing here would notice. Only
review of the diff catches that. It likewise does not establish that a maintainer command
*refrains* from writing a spec: it detects the file after it lands, which is a report rather
than a prevention, and nothing offline can observe a command declining to run.

Stdlib only; the directory is walked and the manifest read as text (INV-108).

Source issue: #52 (freeze `specs/`, set the cutover date).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS = REPO_ROOT / "specs"
MANIFEST = SPECS / "FROZEN-MANIFEST.txt"
FREEZE_README = SPECS / "README.md"

#: The cutover this freeze records. Stated in `specs/README.md` and asserted below, so the
#: date cannot be dropped from the directory the issue required it to be stated in.
CUTOVER = "2026-09-15"

#: A table row whose first cell names one backticked file, linked or not:
#: `| [`IMPLEMENTED.md`](IMPLEMENTED.md) | ... |` or `| `README.md` | ... |`.
TABLE_ROW = re.compile(r"^\|\s*\[?`([^`/]+)`\]?(?:\([^)]*\))?\s*\|")


def parse_live_records(text):
    """The live records named in `specs/README.md`'s "What stays live" table.

    The table is the one authoritative list (#226, #258). ⛔ There is no fallback set: a table
    that cannot be found, or parses to nothing, or names a file twice, raises -- an empty or
    guessed exemption list would let the freeze pass over anything (INV-265). Header and
    separator rows name no backticked file and are skipped.
    """
    start = text.find("\n## What stays live")
    if start == -1:
        raise ValueError("specs/README.md has no \"## What stays live\" section; the live-record "
                         "list is read from its table, and there is no fallback set")
    end = text.find("\n## ", start + 1)
    names = [m.group(1) for line in text[start:end if end != -1 else None].splitlines()
             for m in [TABLE_ROW.match(line.strip())] if m]
    if not names:
        raise ValueError("specs/README.md's \"What stays live\" table parsed to no file names; "
                         "there is no fallback set")
    duplicated = sorted({n for n in names if names.count(n) > 1})
    if duplicated:
        raise ValueError("specs/README.md's \"What stays live\" table names %s more than once"
                         % ", ".join(duplicated))
    return set(names)


#: Not frozen. Historical record and live rules -- see the module docstring. Read from the table,
#: never restated here, so the README and the guard cannot name different sets.
LIVE_RECORDS = parse_live_records(FREEZE_README.read_text(encoding="utf-8"))

#: INV-307 is the third copy of the list, in its applied 2026-09-30 note (#226).
INVARIANTS = SPECS / "INVARIANTS.md"

#: The two documents outside `specs/` that name the live records.
DEVELOPMENT_MD = REPO_ROOT / "docs" / "development.md"
FAMILY_WORKFLOW = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"

#: Pointer used in every failure message, so the guard explains the freeze it enforces.
POINTER = "specs/ is frozen (cutover %s); see specs/README.md" % CUTOVER


def manifest_names():
    """The pinned set: every non-comment, non-blank line of the manifest."""
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines
            if line.strip() and not line.lstrip().startswith("#")}


def spec_files():
    """Every file in specs/, of any type and at any depth, that is not a live record.

    `FROZEN-MANIFEST.txt` is left out by name: it is this guard's own input, not a spec.
    """
    found = {p.relative_to(SPECS).as_posix() for p in SPECS.rglob("*") if p.is_file()}
    return found - LIVE_RECORDS - {MANIFEST.name}


#: A backticked filename, with or without its `specs/` prefix.
RECORD_NAME = re.compile(r"`(?:specs/)?([A-Za-z0-9_-][A-Za-z0-9_.-]*\.[A-Za-z0-9]+)`")


def named_in_development_md(text):
    """The names in `docs/development.md`'s one sentence saying the live records are not frozen."""
    sentences = [s for s in re.split(r"(?<=\.)\s+", re.sub(r"\s+", " ", text))
                 if "**not** frozen" in s]
    return set(RECORD_NAME.findall(sentences[0])) if len(sentences) == 1 else set()


def named_in_family_workflow(text):
    """The `specs/` files `docs/FAMILY_WORKFLOW.md` §8 lists as bullets."""
    start = text.find("\n## 8.")
    end = text.find("\n## ", start + 1)
    section = text[start:end] if start != -1 else ""
    return set(re.findall(r"(?m)^- `specs/([^`]+)`", section))


class NeitherSetIsEmpty(unittest.TestCase):
    """INV-265 -- a set comparison is satisfied trivially when either side is empty."""

    def test_the_manifest_parsed(self):
        names = manifest_names()
        self.assertGreaterEqual(
            len(names), 3,
            "%s parsed to fewer than three names; the comment/blank filter has drifted and "
            "the comparisons below prove nothing" % MANIFEST)
        self.assertIn(
            "todo.md", names,
            "the manifest is missing a name certainly in it; the parser is wrong")

    def test_the_directory_globbed(self):
        found = spec_files()
        self.assertGreaterEqual(
            len(found), 3,
            "fewer than three spec files were found in %s; the glob has drifted" % SPECS)
        self.assertIn(
            "todo.md", found,
            "the spec glob is missing a file certainly present; the pattern is wrong")


class NothingNewLands(unittest.TestCase):
    """The freeze direction: a spec file appearing after the cutover."""

    def test_every_spec_file_is_in_the_manifest(self):
        unfrozen = sorted(spec_files() - manifest_names())
        self.assertEqual(
            [], unfrozen,
            "%s. New spec file(s) landed in an archive that is closed to new work: %s. "
            "Track this as a GitHub issue instead. If a maintainer command wrote it, that "
            "command's rework is issue #49/#50/#51 and it should not have been run yet."
            % (POINTER, ", ".join(unfrozen)))


class NothingQuietlyLeaves(unittest.TestCase):
    """The quieter direction: an archived spec an invariant may still cite."""

    def test_every_manifest_name_still_has_a_file(self):
        missing = sorted(manifest_names() - spec_files())
        self.assertEqual(
            [], missing,
            "%s. Manifest name(s) with no file under specs/: %s. An invariant cites specs by "
            "slug, and test_spec_ledger_invariants.py accepts a ledger entry in place of a "
            "file -- so deleting a ledgered spec breaks no other test while destroying the "
            "reasoning the invariant points at." % (POINTER, ", ".join(missing)))


class TheLiveRecordsStayLive(unittest.TestCase):
    """Freezing these would break the ledger citations and /review-invariants."""

    def test_the_live_records_exist(self):
        absent = sorted(n for n in LIVE_RECORDS if not (SPECS / n).is_file())
        self.assertEqual(
            [], absent,
            "live record(s) missing from specs/: %s. These are exempt from the freeze "
            "because they are still written to -- the ledger is what some INVARIANTS.md "
            "citations resolve through, and /review-invariants appends to INVARIANTS.md."
            % ", ".join(absent))

    def test_no_live_record_is_in_the_manifest(self):
        """A live record in the frozen set would forbid the appends that must keep working."""
        frozen_live = sorted(LIVE_RECORDS & manifest_names())
        self.assertEqual(
            [], frozen_live,
            "live record(s) appear in the frozen manifest: %s. The manifest is the set that "
            "may not change; a ledger listed there is a contradiction, because appending to "
            "it is the behavior issue #52 required to keep working." % ", ".join(frozen_live))


class TheDocsNameTheLiveRecords(unittest.TestCase):
    """Each copy of the live-record list outside `specs/` names exactly `LIVE_RECORDS`."""

    COPIES = ((DEVELOPMENT_MD, named_in_development_md),
              (FAMILY_WORKFLOW, named_in_family_workflow))

    def test_each_copy_names_the_live_records(self):
        for path, named in self.COPIES:
            with self.subTest(copy=path.name):
                found = named(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    sorted(LIVE_RECORDS), sorted(found),
                    "%s names the live records %s; the freeze guard exempts %s. A live record "
                    "is a decision (INV-307), so every site naming the set must name the same "
                    "one." % (path.relative_to(REPO_ROOT).as_posix(), sorted(found),
                              sorted(LIVE_RECORDS)))

    def test_dropping_a_name_from_either_copy_is_caught(self):
        """Negative control: each copy with one live record deleted parses to a different set."""
        for path, named in self.COPIES:
            text = path.read_text(encoding="utf-8")
            for name in sorted(LIVE_RECORDS):
                with self.subTest(copy=path.name, dropped=name):
                    thinned = re.sub(r"`(?:specs/)?%s`" % re.escape(name), "", text)
                    self.assertNotEqual(LIVE_RECORDS, named(thinned))


def inv307_text(invariants=None):
    """INV-307's entry, as registered."""
    text = invariants if invariants is not None else INVARIANTS.read_text(encoding="utf-8")
    m = re.search(r"(?ms)^- \*\*INV-307\*\* —.*?(?=^- \*\*INV-\d{3}\*\* —|\Z)", text)
    return m.group(0) if m else ""


def names_the_list(text, live):
    """The text names every live record and the table that holds them."""
    return "What stays live" in text and all("`%s`" % n in text for n in live)


def inv307_agrees(live, invariants=None):
    """INV-307's applied note names the table and every live record."""
    return names_the_list(inv307_text(invariants), live)


class TheReadmeTableIsTheList(unittest.TestCase):
    """#258: `LIVE_RECORDS` is parsed from `specs/README.md`, and a broken table fails loudly."""

    def test_the_table_names_the_five_live_records(self):
        self.assertEqual(
            {"IMPLEMENTED.md", "DECLINED.md", "INVARIANTS.md", "README.md", "mcp-coverage.jsonl"},
            LIVE_RECORDS,
            "the \"What stays live\" table in specs/README.md names %s" % sorted(LIVE_RECORDS))

    def test_a_missing_table_fails_loudly(self):
        """Negative control: the table deleted is an error naming specs/README.md, not a pass."""
        text = FREEZE_README.read_text(encoding="utf-8")
        start = text.index("\n## What stays live")
        end = text.index("\n## ", start + 1)
        for broken in (text[:start] + text[end:],
                       re.sub(r"(?m)^\|.*\|\s*$", "", text)):
            with self.subTest(case="section gone" if "What stays live" not in broken else "rows gone"):
                with self.assertRaisesRegex(ValueError, r"specs/README\.md"):
                    parse_live_records(broken)

    def test_a_duplicated_row_fails_loudly(self):
        text = FREEZE_README.read_text(encoding="utf-8")
        row = next(l for l in text.splitlines() if l.startswith("| [`DECLINED.md`]"))
        with self.assertRaisesRegex(ValueError, r"more than once"):
            parse_live_records(text.replace(row, row + "\n" + row, 1))


class InvariantThreeOhSevenNamesTheList(unittest.TestCase):
    """INV-307's copy agrees with the table, in its applied 2026-09-30 note (#226)."""

    #: Where INV-307's applied note opens; the negative control below removes it from there on.
    NOTE = "(⛔ **Dated correction, 2026-09-30 (#226)"

    def test_inv307_names_the_list(self):
        self.assertTrue(
            inv307_agrees(LIVE_RECORDS),
            "INV-307 in specs/INVARIANTS.md does not name the \"What stays live\" table and all "
            "of %s" % sorted(LIVE_RECORDS))

    def test_dropping_a_name_from_the_copy_is_caught(self):
        """Negative control: each live record removed from INV-307 fails the check."""
        invariants = INVARIANTS.read_text(encoding="utf-8")
        for name in sorted(LIVE_RECORDS):
            with self.subTest(dropped=name):
                pattern = r"`(?:specs/)?%s`" % re.escape(name)
                self.assertFalse(inv307_agrees(LIVE_RECORDS, re.sub(pattern, "", invariants)))

    def test_removing_the_applied_note_is_caught(self):
        """Negative control: INV-307 without its 2026-09-30 note fails the check."""
        invariants = INVARIANTS.read_text(encoding="utf-8")
        entry = inv307_text(invariants)
        self.assertIn(self.NOTE, entry, "negative control is stale: INV-307 no longer has the "
                      "note it removes")
        bare = entry[:entry.index(self.NOTE)].rstrip() + "\n"
        self.assertFalse(inv307_agrees(LIVE_RECORDS, invariants.replace(entry, bare)))


#: The list check's scope (#291): every maintainer file that could restate the live records.
#: `.claude/commands/` and a root `CLAUDE.md` are scanned when they exist.
LIST_SCOPE = (".claude/skills", ".claude/skill-overlays", ".claude/commands", "docs", "tests")
LIST_SUFFIXES = (".md", ".py")

#: The count check's scope (#291): instruction files only. `.claude/skills` contributes its
#: `*.md`; the other directories contribute every file. `tests/` is out, deliberately.
COUNT_SCOPE = (".claude/skill-overlays", ".claude/commands", "docs")

#: Files at the repository root that both checks read when present.
ROOT_FILES = ("CLAUDE.md",)

#: The pointer that stands in for a list: a block naming the table names the set by reference.
TABLE_POINTER = "What stays live"

#: A live record, backticked, with or without its `specs/` prefix. Built from `LIVE_RECORDS`,
#: so the check has no second copy of the set.
LIVE_NAME = re.compile(r"`(?:specs/)?(%s)`" % "|".join(re.escape(n) for n in sorted(LIVE_RECORDS)))

#: A stated number of specs ("519 specs", "1,204 specs"). "212 spec files" does not match.
SPEC_COUNT = re.compile(r"\b\d[\d,]*\s+specs\b")


def outside_worktrees(path):
    return path.relative_to(REPO_ROOT).parts[:2] != (".claude", "worktrees")


def walk(directory, suffixes=None):
    base = REPO_ROOT / directory
    if not base.is_dir():
        return []
    return [p for p in base.rglob("*") if p.is_file() and outside_worktrees(p)
            and (suffixes is None or p.suffix in suffixes)]


def root_files():
    return [REPO_ROOT / n for n in ROOT_FILES if (REPO_ROOT / n).is_file()]


def list_scope_files():
    return sorted({p for d in LIST_SCOPE for p in walk(d, LIST_SUFFIXES)} | set(root_files()))


def count_scope_files():
    found = set(walk(".claude/skills", (".md",)))
    found |= {p for d in COUNT_SCOPE for p in walk(d)}
    return sorted(found | set(root_files()))


def blocks(text):
    """Each run of non-blank lines, with the 1-based line it starts on."""
    run, start = [], 0
    for number, line in enumerate(text.splitlines() + [""], 1):
        if line.strip():
            if not run:
                start = number
            run.append(line)
        elif run:
            yield start, "\n".join(run)
            run = []


def listing_blocks(text):
    """Each block naming three or more live records, with the set of names it names."""
    for start, block in blocks(text):
        names = set(LIVE_NAME.findall(block))
        if len(names) >= 3:
            yield start, block, names


def block_agrees(block, names):
    """The block names exactly the table's set, or names the table instead of listing."""
    return names == LIVE_RECORDS or TABLE_POINTER in re.sub(r"\s+", " ", block)


def disagreeing_blocks(text):
    """(line, names) for each listing block that neither matches the table nor points at it."""
    return [(start, sorted(names)) for start, block, names in listing_blocks(text)
            if not block_agrees(block, names)]


class NoSecondListOfTheLiveRecords(unittest.TestCase):
    """#291: a site naming the live records names exactly the table's set, or points at it."""

    #: The sanctioned copies outside `specs/`, which list the set rather than point at it.
    LISTING_COPIES = (DEVELOPMENT_MD, FAMILY_WORKFLOW)

    def test_the_scan_found_files(self):
        """INV-265: an empty scan passes every block check trivially."""
        files = list_scope_files()
        self.assertGreaterEqual(len(files), 1, "the list check scanned no files")
        for copy in self.LISTING_COPIES:
            self.assertIn(copy, files, "the list check's scope no longer reaches %s"
                          % copy.relative_to(REPO_ROOT).as_posix())

    def test_every_block_names_the_set_or_the_table(self):
        offenders = ["%s:%d names %s" % (path.relative_to(REPO_ROOT).as_posix(), line, names)
                     for path in list_scope_files()
                     for line, names in disagreeing_blocks(path.read_text(encoding="utf-8"))]
        self.assertEqual(
            [], offenders,
            "a block names three or more live records but neither the table's set %s nor "
            "the \"%s\" table in specs/README.md (INV-307). Point at the table instead of "
            "listing, or name the whole set where a test checks it: %s"
            % (sorted(LIVE_RECORDS), TABLE_POINTER, "; ".join(offenders)))

    def test_the_three_sanctioned_copies_are_found(self):
        """INV-265: each sanctioned copy is a listing block the check sees, and it agrees."""
        copies = [(path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"))
                  for path in self.LISTING_COPIES]
        copies.append(("INV-307", inv307_text()))
        for label, text in copies:
            with self.subTest(copy=label):
                found = list(listing_blocks(text))
                self.assertTrue(found, "%s has no block naming three or more live records; "
                                "the list check would pass it without reading it" % label)
                self.assertTrue(all(block_agrees(block, names) for _, block, names in found))

    def test_dropping_a_name_from_a_sanctioned_copy_is_caught(self):
        """Negative control: a copy with one live record deleted fails the list check."""
        for path in self.LISTING_COPIES:
            text = path.read_text(encoding="utf-8")
            listing = [block for _, block, names in listing_blocks(text) if names == LIVE_RECORDS]
            self.assertTrue(listing, "negative control is stale: %s no longer lists the set"
                            % path.name)
            for name in sorted(LIVE_RECORDS):
                with self.subTest(copy=path.name, dropped=name):
                    pattern = r"`(?:specs/)?%s`" % re.escape(name)
                    thinned = text.replace(listing[0], re.sub(pattern, "", listing[0]))
                    self.assertTrue(disagreeing_blocks(thinned))

    def test_the_old_four_name_list_is_caught(self):
        """Negative control: the comment #291 removed from `pending_invariants.py`, put back."""
        path = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"
        text = path.read_text(encoding="utf-8")
        self.assertEqual([], disagreeing_blocks(text))
        four = ", ".join("`%s`" % n for n in sorted(LIVE_RECORDS - {"mcp-coverage.jsonl"}))
        old = "#: it already excludes the live\n#: records (%s) that a prefix test\n" % four
        self.assertTrue(disagreeing_blocks(text + "\n" + old))


class NoInstructionPinsASpecCount(unittest.TestCase):
    """#291: no instruction states how many specs the archive holds."""

    def test_the_scan_found_files(self):
        """INV-265: an empty scan finds no count trivially."""
        files = count_scope_files()
        self.assertGreaterEqual(len(files), 1, "the count check scanned no files")
        self.assertIn(REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md", files)

    def test_no_instruction_states_a_spec_count(self):
        offenders = ["%s: %r" % (path.relative_to(REPO_ROOT).as_posix(), m.group(0))
                     for path in count_scope_files()
                     for m in SPEC_COUNT.finditer(
                         path.read_text(encoding="utf-8", errors="replace"))]
        self.assertEqual(
            [], offenders,
            "an instruction pins a spec count, which goes stale on the next archive operation "
            "while reading as authoritative. State the property instead (\"every spec in it is "
            "implemented or declined\"): %s" % "; ".join(offenders))

    def test_a_pinned_count_is_caught(self):
        """Negative control: "519 specs" put back into a scanned instruction file is found."""
        path = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        self.assertIsNone(SPEC_COUNT.search(text))
        self.assertIsNotNone(SPEC_COUNT.search(text + "\nIt is an archive of 519 specs.\n"))

    def test_a_dated_file_count_is_not_a_spec_count(self):
        """The pattern leaves "spec files" and "files" measurements alone, as #291 scopes it."""
        for phrase in ("212 spec files", "519 files", "the specs"):
            with self.subTest(phrase=phrase):
                self.assertIsNone(SPEC_COUNT.search(phrase))


class TheCutoverDateIsRecorded(unittest.TestCase):
    """Issue #52 required the date to be stated in the directory itself, not only in a test."""

    def test_the_readme_states_the_cutover(self):
        self.assertIn(
            CUTOVER, FREEZE_README.read_text(encoding="utf-8"),
            "specs/README.md does not state the cutover date %s. The date is what tells a "
            "reader when the archive closed, and a freeze with no date is undatable "
            "afterwards." % CUTOVER)

    def test_the_readme_says_the_directory_is_frozen(self):
        text = FREEZE_README.read_text(encoding="utf-8").lower()
        self.assertIn(
            "frozen", text,
            "specs/README.md never says the directory is frozen; a reader landing here must "
            "learn that before reading the archive as live work")


if __name__ == "__main__":
    unittest.main()
