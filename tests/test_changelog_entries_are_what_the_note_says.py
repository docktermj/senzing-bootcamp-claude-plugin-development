"""`CHANGELOG.md`'s entries are what its own seed note tells a reader they are.

The note at the top of the file says:

    Entries **0.5.3 and earlier** were reconstructed from git history when this file was
    first created. They were not authored at release time, so they list commit subjects
    rather than curated release notes.

Read either way round that is a claim about **both** halves of the file: the entries it
names are commit subjects, and the entries above them are curated release notes. The file's
own header tells a downstream porter that the Kiro, ChatGPT and Copilot repositories port
from these tagged entries, so the note sets an expectation at the one place a porter looks.
When #698 was filed it was not met: every entry was raw commit subjects, `[0.7.0]` carried
the bare bullet `- Savepoint`, and `[0.6.1]` opened with four more.

⛔ **The entries were curated up to the note; the note was NOT rewritten down to the
entries.** The downstream repositories port from these entries, so the curation has real
value and redefining them as raw subjects would throw it away. Curation is three mechanical
operations and nothing else — drop the subjects that describe no change, keep every
remaining subject's own wording verbatim, and group the kept ones under headings derived
from the subjects' own conventional-commit types — so no bullet's description is ever
invented. `.claude/skills/release/release.py` performs the same three operations on every
entry it writes from now on.

**The two halves this file asserts** (the issue's acceptance criteria 1, 2 and 4):

1. The seed note is present, version-anchored, and the version it names is an entry the
   file really has.
2. No entry **newer than** that version carries a bullet with no change description.

⛔ **The boundary and the entry set are derived by SCANNING the file (INV-246)**, never from
a list of versions written here. A list of version numbers in a guard goes stale on the next
release, silently, and this guard's whole subject is a claim that goes stale silently.

**Scope, and why it is exactly the note's own boundary.** Entries at or below the boundary
are left alone, and a contentless bullet in one of them is **not** reported. That is not an
exemption: the note states plainly that those entries are reconstructed commit subjects, so
`- #1 Savepoint` in `[0.5.3]` is the file keeping its word. Rewriting them would destroy the
honest record of what those releases contained, and reporting them would demand a fix the
note says must not happen. `test_the_reconstructed_entries_keep_their_contentless_bullets`
pins that direction, so narrowing the scope to the note's boundary cannot quietly become
narrowing it to nothing.

**The predicate was measured before it was narrowed, and the measurement is here rather than
only in the ledger (INV-282).** Three readings over `CHANGELOG.md` as it stood on 2026-10-17,
1560 bullets in 10 entries:

1. **Any short bullet** — fewer than four words — reports 30. Most are real release notes:
   `docs: add BLUEPRINT.md`, `docs(invariants): register INV-316`, `#451 Update
   instructions`. A guard on this reading would report correct entries and get waived.
2. **The subject's own text, with its bookkeeping removed** — strip a leading `#456` issue
   reference and a conventional-commit `type(scope):` prefix, then require two words —
   reports **21 of 1560**, and every one of them is genuine: `Savepoint` (6, with and
   without an issue number), `Improve` (8), `Update` (2), `Rename`, `Retrofit`, `3-Cs`,
   `name-the-claude-interface`, `#1 Update`. Of those 21, **7 are in entries the note
   promises are curated** and 14 are in the reconstructed entries, where they belong.
   Nothing with a verb and an object is reported: the two-word subjects that sit beside
   them (`add BLUEPRINT.md`, `Update instructions`, `Fix heading`) all survive.
3. **The literal word `Savepoint`** reports 7. That is a word list wearing a predicate's
   clothes: it would miss `Update`, `Improve` and `#17 Rename`, which are the same defect,
   and it would teach the next reader to add a word rather than state a rule.

So reading 2 is the predicate, and it lives in `release.py` rather than here — the tool that
writes an entry and the guard that reads one must agree, and two copies of a predicate are
two predicates. ⚠️ **The trade is accepted deliberately:** importing it means a predicate
that goes blind takes this guard with it, so `ThePredicateIsTheOneReleasePyApplies` pins
both directions of it against literal subjects.

⚠️ **Line-scoped by design (#698), and only for the file's STRUCTURE.** An entry heading, a
group heading and a bullet are each exactly one line by construction — `release.py` writes
them as `"## [%s] - %s"`, `"### %s"` and `"- %s"`, and a git commit subject contains no line
break — so there is no wrap for a structural read to cross. The one piece of **prose** here,
the seed note, wraps across three lines and is read wrap-aware through `_wrapped_text`
(INV-346), as is every sentence this guard reads out of `.claude/skills/release/SKILL.md`.

⛔ **Every negative control runs the SAME check over a mutated copy of the shipped text
(INV-265)**, putting the pre-#698 defect back, and the anti-vacuity tests assert the scan
read something: an empty entry set would otherwise pass every check below in silence.

**What this cannot establish.** (a) That a kept bullet's wording is a *good* release note —
it checks that a change is described, not that the description is apt. (b) That the git tag
for an entry exists or points anywhere in particular; that is
`tests/test_release_bumps_version_changelog_and_tag_together.py`. (c) That a future release
actually ran `release.py` rather than hand-writing its entry, which the file cannot tell.

Stdlib only; `release.py` is loaded from this repository by path and nothing under
`plugins/` is imported (INV-108).

Source issue: #698.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _wrapped_text import collapsed_blocks, line_of, match_lines  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
RELEASE_PY = REPO_ROOT / ".claude" / "skills" / "release" / "release.py"
RELEASE_SKILL = REPO_ROOT / ".claude" / "skills" / "release" / "SKILL.md"

#: An entry heading, exactly as `release.py` writes one.
ENTRY_HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})\s*$")
#: A group heading inside a curated entry.
GROUP_HEADING = re.compile(r"^### (\S.*?)\s*$")
#: A bullet. The whole line after the marker is the commit subject, verbatim.
BULLET = re.compile(r"^- (\S.*?)\s*$")


def release_module():
    """Load `release.py` so its curation rules are used here, never restated.

    ⛔ (INV-246) The seed note's own template comes from this module too, so the pattern
    below cannot drift from the note the script writes.
    """
    spec = importlib.util.spec_from_file_location("release_under_test", RELEASE_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RELEASE = release_module()


def flat(text):
    """Collapse whitespace and strip blockquote markers, as `_wrapped_text` reads a quote."""
    return re.sub(r"\s+", " ", re.sub(r"(?m)^[ \t]*>[ \t]?", "", text)).strip()


def note_pattern():
    """The seed note as a pattern, built from `release.py`'s own template.

    Wrap-aware by construction (INV-346): both sides are collapsed, so the note matches
    however the file happens to wrap it.
    """
    head, marker, tail = RELEASE.SEED_NOTE.partition("%s")
    if not marker:
        raise AssertionError(
            "release.py's SEED_NOTE no longer carries a version placeholder, so the note "
            "cannot be version-anchored and every check below is meaningless")
    return re.compile(re.escape(flat(head)) + r"\s*(\d+\.\d+\.\d+)\s*"
                      + re.escape(flat(tail)))


def seed_boundary(text):
    """`(version, line)` for the seed note, or `(None, None)` when the file carries none."""
    pattern = note_pattern()
    for block, origin in collapsed_blocks(text):
        found = pattern.search(block)
        if found:
            return found.group(1), line_of(origin, found.start())
    return None, None


def entries(text):
    """Every entry in the file, by scanning (INV-246). Newest first, as the file is written.

    Each entry is `{version, date, line, groups, bullets}`, where `bullets` holds
    `(line, subject, group)` and `group` is the `###` heading in force, or `None`.
    """
    found, current, group = [], None, None
    for number, line in enumerate(text.split("\n"), 1):
        heading = ENTRY_HEADING.match(line)
        if heading:
            current = {"version": heading.group(1), "date": heading.group(2),
                       "line": number, "groups": [], "bullets": []}
            found.append(current)
            group = None
            continue
        if current is None:
            continue
        inner = GROUP_HEADING.match(line)
        if inner:
            group = inner.group(1)
            current["groups"].append((number, group))
            continue
        bullet = BULLET.match(line)
        if bullet:
            current["bullets"].append((number, bullet.group(1), group))
    return found


def split_at_boundary(text):
    """`(curated, reconstructed)` — the entries above the note's boundary, and the rest."""
    mark, _line = seed_boundary(text)
    if mark is None:
        return [], entries(text)
    limit = RELEASE.semver(mark)
    curated, reconstructed = [], []
    for entry in entries(text):
        key = RELEASE.semver(entry["version"])
        (curated if key and key > limit else reconstructed).append(entry)
    return curated, reconstructed


def note_problems(text):
    """Half one: the file carries the seed note, and the note describes entries it has."""
    mark, line = seed_boundary(text)
    if mark is None:
        return ["CHANGELOG.md carries no seed note in the shape release.py writes, so "
                "nothing in the file says what its entries are"]
    versions = [entry["version"] for entry in entries(text)]
    if mark not in versions:
        return ["CHANGELOG.md:%d: the seed note names %s as its boundary and the file has "
                "no [%s] entry, so the note describes entries that are not here"
                % (line, mark, mark)]
    return []


def contentless_bullets(text):
    """Half two: every bullet in a curated entry that carries no change description."""
    problems = []
    for entry in split_at_boundary(text)[0]:
        for number, subject, _group in entry["bullets"]:
            why = RELEASE.describes_no_change(subject)
            if why:
                problems.append(
                    "CHANGELOG.md:%d: [%s] `- %s` %s — the seed note promises this entry is "
                    "a curated release note" % (number, entry["version"], subject, why))
    return problems


def ungrouped_bullets(text):
    """Every bullet in a curated entry that is not under its own type's heading."""
    problems = []
    for entry in split_at_boundary(text)[0]:
        for number, subject, group in entry["bullets"]:
            want = RELEASE.commit_group(subject)
            if group is None:
                problems.append(
                    "CHANGELOG.md:%d: [%s] `- %s` sits under no `### ` heading; a curated "
                    "entry groups its bullets by the subjects' own types"
                    % (number, entry["version"], subject))
            elif group != want:
                problems.append(
                    "CHANGELOG.md:%d: [%s] `- %s` sits under `### %s` and its own type is "
                    "`%s`" % (number, entry["version"], subject, group, want))
    return problems


def grouped_reconstructed(text):
    """A reconstructed entry carrying group headings — the note says it lists subjects."""
    return ["CHANGELOG.md:%d: [%s] carries `### %s`, but the seed note says this entry "
            "lists commit subjects rather than curated release notes"
            % (number, entry["version"], group)
            for entry in split_at_boundary(text)[1]
            for number, group in entry["groups"]]


def shipped():
    return CHANGELOG.read_text(encoding="utf-8")


def mutate(test, text, old, new):
    """Replace `old` once; fail the control if its anchor text has gone."""
    test.assertIn(old, text, "the control's anchor text is gone; update the control")
    return text.replace(old, new, 1)


def flatten_newest_entry(test, text):
    """The newest entry with its `### ` headings taken out — the pre-#698 shape."""
    found = entries(text)
    test.assertTrue(found, "no entry to flatten; the control cannot run")
    newest = found[0]
    lines = text.split("\n")
    end = found[1]["line"] - 1 if len(found) > 1 else len(lines)
    body, blank_before = [], False
    for line in lines[newest["line"]:end]:
        if GROUP_HEADING.match(line):
            continue
        blank = not line.strip()
        if blank and blank_before:
            continue
        body.append(line)
        blank_before = blank
    return "\n".join(lines[:newest["line"]] + body + lines[end:])


class TheSeedNoteSaysWhatTheEntriesAre(unittest.TestCase):
    """Acceptance criterion 1, and the boundary every other check is scoped by."""

    def setUp(self):
        self.text = shipped()

    def test_the_file_carries_the_note_release_py_writes(self):
        self.assertEqual([], note_problems(self.text))

    def test_the_note_is_version_anchored_rather_than_positional(self):
        """⛔ 'Entries below' stops being true the moment an entry is prepended above."""
        mark, line = seed_boundary(self.text)
        self.assertIsNotNone(mark, "no version-anchored seed note found")
        self.assertIsNotNone(RELEASE.semver(mark),
                             "the seed note's boundary %r is not a version" % (mark,))
        self.assertGreater(line, 0)

    def test_the_boundary_has_entries_on_both_sides(self):
        """⛔ (INV-265) One empty side would make half of this file vacuous."""
        curated, reconstructed = split_at_boundary(self.text)
        self.assertGreaterEqual(
            len(curated), 1,
            "no entry is newer than the seed note's boundary, so the note promises nothing "
            "and the curated half of this guard checks nothing")
        self.assertGreaterEqual(
            len(reconstructed), 1,
            "no entry is at or below the boundary, so the note describes nothing")

    def test_the_scan_read_the_file_it_claims_to(self):
        """⛔ (INV-265) An empty entry set passes every check below in silence."""
        found = entries(self.text)
        self.assertGreaterEqual(len(found), 8,
                                "the scan found %d entries in CHANGELOG.md" % len(found))
        self.assertGreaterEqual(sum(len(entry["bullets"]) for entry in found), 1000,
                                "the scan found almost no bullets; it is not reading the file")


class NoCuratedEntryCarriesABulletWithNoChangeDescription(unittest.TestCase):
    """Acceptance criterion 2, scoped to the entries the note promises are curated."""

    def setUp(self):
        self.text = shipped()

    def test_the_shipped_file_is_clean(self):
        problems = contentless_bullets(self.text)
        self.assertEqual(
            [], problems,
            "entries newer than the seed note's boundary carry bullet(s) that describe no "
            "change, so the note promises a downstream porter something the file does not "
            "deliver:\n  " + "\n  ".join(problems))

    def test_every_curated_bullet_sits_under_its_own_type(self):
        problems = ungrouped_bullets(self.text)
        self.assertEqual(
            [], problems,
            "a curated entry's bullets are not grouped by the subjects' own conventional-"
            "commit types:\n  " + "\n  ".join(problems))

    def test_the_curated_entries_were_actually_read(self):
        """⛔ (INV-265) A clean result over zero bullets is an unrun check."""
        curated = split_at_boundary(self.text)[0]
        self.assertGreaterEqual(sum(len(entry["bullets"]) for entry in curated), 100,
                                "the curated half holds almost no bullets")


class TheReconstructedEntriesAreLeftAsCommitSubjects(unittest.TestCase):
    """The other half of the note, and the reason this guard's scope stops where it does."""

    def setUp(self):
        self.text = shipped()

    def test_they_carry_no_group_headings(self):
        problems = grouped_reconstructed(self.text)
        self.assertEqual([], problems, "\n  ".join(problems))

    def test_the_reconstructed_entries_keep_their_contentless_bullets(self):
        """⛔ The scope is the note's boundary, and this is what makes that a real limit.

        14 of these were measured on 2026-10-17 (`#1 Savepoint`, `Improve` eight times,
        `#1 Update` twice, `#1 3-Cs`, `#1 name-the-claude-interface`, `#1 Retrofit`). They
        are not defects: the note says these entries list commit subjects, so a subject that
        describes no change is the file being honest about a badly named commit. A guard
        that reported them would demand a rewrite the note forbids — and one that found
        none here would mean the predicate had gone blind, not that the history had
        improved, since these entries never change.
        """
        found = [subject
                 for entry in split_at_boundary(self.text)[1]
                 for _line, subject, _group in entry["bullets"]
                 if RELEASE.describes_no_change(subject)]
        self.assertGreaterEqual(
            len(found), 10,
            "the reconstructed entries report %d bullets with no change description; 14 "
            "were measured on 2026-10-17 and those entries are frozen history, so a lower "
            "count means the predicate stopped seeing them" % len(found))
        self.assertEqual([], contentless_bullets(self.text),
                         "those bullets are below the boundary and must not be reported")


class ThePredicateIsTheOneReleasePyApplies(unittest.TestCase):
    """⛔ (INV-265) The guard imports the writer's predicate, so both directions are pinned.

    Acceptance criterion 3 in its structural form: the tool that writes an entry and the
    guard that reads one cannot disagree, because there is one predicate.
    """

    def test_a_bare_subject_is_reported(self):
        for subject in ("Savepoint", "#456 Savepoint", "Update", "#17 Rename", "Improve",
                        "Merge pull request #670 from docktermj/669-docktermj-1"):
            with self.subTest(subject=subject):
                self.assertIsNotNone(RELEASE.describes_no_change(subject))

    def test_a_subject_that_names_a_change_is_not_reported(self):
        """The width control: a predicate reporting these would be reported itself."""
        for subject in ("docs: add BLUEPRINT.md", "#451 Update instructions",
                        "#1 Fix heading", "fix(release): drop a contentless bullet",
                        "docs(invariants): register INV-316"):
            with self.subTest(subject=subject):
                self.assertIsNone(RELEASE.describes_no_change(subject))

    def test_a_subject_is_grouped_under_its_own_type(self):
        self.assertEqual("fix", RELEASE.commit_group("fix(release): drop a bullet"))
        self.assertEqual("docs", RELEASE.commit_group("docs: add BLUEPRINT.md"))
        self.assertEqual("feat", RELEASE.commit_group("#451 feat: something"))

    def test_an_untyped_subject_is_kept_rather_than_dropped(self):
        """⛔ An unconventional name is still a real change; dropping it would lose it."""
        self.assertEqual(RELEASE.UNTYPED_GROUP,
                         RELEASE.commit_group("#451 Update instructions"))
        self.assertIsNone(RELEASE.describes_no_change("#451 Update instructions"))

    def test_a_curated_entry_keeps_every_kept_subject_verbatim(self):
        subjects = ["fix(a): one thing", "Savepoint", "#451 Update instructions"]
        block, dropped = RELEASE.curated_entry("9.9.9", "2026-10-17", subjects)
        self.assertIn("- fix(a): one thing", block)
        self.assertIn("- #451 Update instructions", block)
        self.assertNotIn("Savepoint", block)
        self.assertEqual(["Savepoint"], [subject for subject, _why in dropped])
        self.assertIn("### fix", block)
        self.assertIn("### %s" % RELEASE.UNTYPED_GROUP, block)

    def test_the_entry_release_py_writes_passes_this_guard(self):
        """The two halves meet: a fresh entry is clean against the checks above."""
        block, _dropped = RELEASE.curated_entry(
            "9.9.9", "2026-10-17", ["fix(a): one thing", "Savepoint", "#451 Update it now"])
        text = mutate(self, shipped(), "## [", block + "\n## [")
        self.assertEqual([], contentless_bullets(text))
        self.assertEqual([], ungrouped_bullets(text))


class ReleasePyReportsWhatItDrops(unittest.TestCase):
    """Acceptance criterion 3: a dropped subject reaches the maintainer, never a silent filter."""

    def test_the_script_has_a_report_for_them(self):
        self.assertTrue(callable(getattr(RELEASE, "report_dropped", None)),
                        "release.py has no report_dropped, so a dropped subject is invisible")

    def test_the_preview_calls_it(self):
        """Read out of the source, so a report that stops being printed fails here."""
        source = RELEASE_PY.read_text(encoding="utf-8")
        self.assertIn("report_dropped(dropped)", source,
                      "nothing in release.py prints the dropped subjects, so the maintainer "
                      "never learns a commit was named `Savepoint`")

    def test_the_skill_says_the_entry_is_curated_and_the_rest_reported(self):
        """⚠️ Wrap-aware (INV-346): each of these is a sentence, and the file wraps them."""
        text = RELEASE_SKILL.read_text(encoding="utf-8")
        for phrase in (r"curates each entry it writes, in three mechanical operations",
                       r"No bullet's description is ever written here\.",
                       r"What it drops, it reports: the dry run prints every subject",
                       r"Keep every remaining subject's own wording verbatim"):
            with self.subTest(phrase=phrase):
                self.assertTrue(
                    match_lines(text, re.compile(phrase)),
                    "%s does not state: %s" % (RELEASE_SKILL.name, phrase))

    def test_the_skill_names_the_script_s_own_default_group(self):
        text = RELEASE_SKILL.read_text(encoding="utf-8")
        self.assertTrue(
            match_lines(text, re.compile(r"`### %s`" % re.escape(RELEASE.UNTYPED_GROUP))),
            "the skill does not name `### %s`, the heading release.py actually writes for "
            "an untyped subject" % RELEASE.UNTYPED_GROUP)


class TheControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs the checks above over the shipped text, mutated."""

    def setUp(self):
        self.text = shipped()

    def test_the_shipped_file_is_clean(self):
        self.assertEqual([], note_problems(self.text))
        self.assertEqual([], contentless_bullets(self.text))
        self.assertEqual([], ungrouped_bullets(self.text))
        self.assertEqual([], grouped_reconstructed(self.text))

    def test_a_savepoint_bullet_in_the_newest_entry_is_reported(self):
        """The negative control the issue asks for: the bullet `[0.7.0]` shipped with."""
        newest = entries(self.text)[0]
        anchor = "## [%s] - %s" % (newest["version"], newest["date"])
        reported = contentless_bullets(
            mutate(self, self.text, anchor, anchor + "\n\n### other\n\n- Savepoint"))
        self.assertTrue(reported, "a `- Savepoint` bullet in the newest entry is not "
                                  "reported, so this guard does not cover the defect")
        self.assertIn("Savepoint", " ".join(reported))
        self.assertIn(newest["version"], " ".join(reported))

    def test_the_same_bullet_below_the_boundary_is_not_reported(self):
        """⛔ The scope follows the note, so the control proves the boundary is read."""
        oldest_curated = split_at_boundary(self.text)[1][0]
        anchor = "## [%s] - %s" % (oldest_curated["version"], oldest_curated["date"])
        text = mutate(self, self.text, anchor, anchor + "\n\n- Savepoint")
        self.assertEqual(
            [], contentless_bullets(text),
            "a contentless bullet in a reconstructed entry is reported, so this guard "
            "demands a rewrite of history the seed note says is correct as it stands")

    def test_moving_the_boundary_up_reports_what_was_below_it(self):
        """⛔ The scope is derived from the note, not written here: move it and the set moves."""
        mark, _line = seed_boundary(self.text)
        below = split_at_boundary(self.text)[1]
        self.assertTrue(below, "nothing is below the boundary; the control cannot run")
        moved = mutate(self, self.text, "**%s and earlier**" % mark,
                       "**%s and earlier**" % below[-1]["version"])
        reported = contentless_bullets(moved)
        self.assertTrue(
            reported,
            "moving the note's boundary down to the oldest entry reports nothing, so this "
            "guard is not reading its scope out of the note")

    def test_a_flattened_entry_is_reported(self):
        """The rest of the pre-#698 shape: raw subjects under no heading at all."""
        reported = ungrouped_bullets(flatten_newest_entry(self, self.text))
        self.assertTrue(reported, "an entry with its group headings removed is not "
                                  "reported, so the grouping half checks nothing")
        self.assertIn("sits under no", " ".join(reported))

    def test_the_file_as_it_read_before_698_is_reported_on_both_halves(self):
        """Both defects together, as `[0.7.0]` actually shipped: flat, with `- Savepoint`."""
        newest = entries(self.text)[0]
        anchor = "## [%s] - %s" % (newest["version"], newest["date"])
        before = mutate(self, flatten_newest_entry(self, self.text),
                        anchor, anchor + "\n\n- Savepoint")
        self.assertTrue(contentless_bullets(before))
        self.assertTrue(ungrouped_bullets(before))

    def test_a_group_heading_below_the_boundary_is_reported(self):
        """The reconstructed entries are commit subjects; grouping one would make the note false."""
        oldest = split_at_boundary(self.text)[1][0]
        anchor = "## [%s] - %s" % (oldest["version"], oldest["date"])
        reported = grouped_reconstructed(
            mutate(self, self.text, anchor, anchor + "\n\n### fix"))
        self.assertTrue(reported)
        self.assertIn(oldest["version"], " ".join(reported))

    def test_removing_the_seed_note_is_reported(self):
        """With no note the file says nothing about its entries, which is the whole defect."""
        mark, _line = seed_boundary(self.text)
        stripped = mutate(self, self.text, "**%s and earlier**" % mark, "**below**")
        self.assertTrue(note_problems(stripped),
                        "a file whose note is no longer version-anchored passes, so half "
                        "one of this guard checks nothing")

    def test_a_note_naming_a_version_the_file_lacks_is_reported(self):
        mark, _line = seed_boundary(self.text)
        wrong = mutate(self, self.text, "**%s and earlier**" % mark, "**9.9.9 and earlier**")
        self.assertTrue(note_problems(wrong))

    def test_the_note_is_read_across_its_line_wraps(self):
        """⚠️ (INV-346) The note is prose and wraps; rewrapping it must not hide it."""
        mark, _line = seed_boundary(self.text)
        rewrapped = mutate(
            self, self.text,
            "> Entries **%s and earlier** were reconstructed from git history when this file was\n"
            "> first created." % mark,
            "> Entries\n> **%s and earlier**\n> were reconstructed from git history\n"
            "> when this file was first created." % mark)
        self.assertEqual((mark, seed_boundary(self.text)[1]),
                         (seed_boundary(rewrapped)[0], seed_boundary(rewrapped)[1]),
                         "the seed note is no longer found once it is rewrapped, so this "
                         "guard reads it one line at a time")


if __name__ == "__main__":
    unittest.main()
