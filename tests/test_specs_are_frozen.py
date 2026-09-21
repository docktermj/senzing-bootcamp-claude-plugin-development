"""`specs/` is a read-only archive; nothing new lands there and nothing quietly leaves.

GitHub issues replaced `specs/` as the tracking mechanism at the **2026-09-15 cutover**
(issue #52). The directory stays as the historical record of why the plugin reads as it
does -- 519 files that `INVARIANTS.md` cites by slug -- but it is closed to new work.

⛔ **A freeze stated only in prose is a convention, not a guarantee.** One maintainer command
still writes spec files -- `/delegate-to-mcp-server`, which has no issue yet -- so running it
produces a file this guard rejects. That failure is the intended signal, which is why every
message below names the freeze and points at `specs/README.md` rather than reporting a bare set
difference.

⚠️ Every other command that wrote here has been reworked: `/feedback-to-issues` files GitHub
issues (#49), `/implement-spec` was retired (#50, #60), `/unattended-issue-loop` is label-gated
and forbids writing here outright (#51, #69), and `/production-readiness-audit` files issues when
attended and records findings in the ledger when not (#69). ⛔ **This paragraph said the audit
half was blocked until 2026-09-21** -- five days after #69 cleared it -- which is the class #90
records: a fix that lands without sweeping the prose describing the old world.

⚠️ **Both directions matter, and they fail differently.**

1. **Nothing new lands** -- a `specs/*.md` that is neither in the manifest nor a live
   record. This is the freeze being breached: work is being tracked where nobody is
   looking for it, and it will not appear in any issue query.
2. **Nothing quietly leaves** -- a manifest name whose file has gone. This is worse and
   quieter: `INVARIANTS.md` cites specs by slug, and `tests/test_spec_ledger_invariants.py`
   accepts *either* a file under `specs/` *or* an `IMPLEMENTED.md` entry. So deleting a
   spec that happens to be ledgered breaks no existing test while destroying the reasoning
   an invariant points at. Six citations already resolve through the ledger alone
   (`deep-dive-audit-2026-07-28` and five others); thinning the archive silently grows that
   number.

⛔ **No count is asserted anywhere in this file, deliberately** -- the habit
`test_documented_dev_commands_match_the_shipped_set.py` refuses by name. A test pinning
"519 specs" fails on the next legitimate archive operation and teaches whoever fixes it to
bump a number, reproducing the defect inside the guard. The two sets are derived and
compared; their size is not the subject. The anti-vacuity floor below is not a count of the
archive -- it is a check that the glob and the parser both found *something*, without which
a set comparison is satisfied trivially (INV-265).

⚠️ **The live records are exempt and must stay that way.** `IMPLEMENTED.md`, `DECLINED.md`
and `INVARIANTS.md` are historical record and live rules, not transient work items; the
ledger in particular is what six invariant citations resolve through. Freezing them would
break `/review-invariants`, which appends to `INVARIANTS.md` by design.

⚠️ **Enforces INV-307.** It asserts the set in both directions, that the live records exist
and stay out of the frozen set, and that the cutover date is stated in `specs/README.md` rather
than only here.

⛔ It does **NOT** establish that the archive's *contents* are unchanged. The manifest pins
**filenames**, so a frozen spec whose text is rewritten in place passes every assertion below --
the reasoning an invariant cites could be silently replaced and nothing here would notice. Only
review of the diff catches that. It likewise does not establish that a maintainer command
*refrains* from writing a spec: it detects the file after it lands, which is a report rather
than a prevention, and nothing offline can observe a command declining to run.

Stdlib only; the directory is globbed and the manifest read as text (INV-108).

Source issue: #52 (freeze `specs/`, set the cutover date).

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS = REPO_ROOT / "specs"
MANIFEST = SPECS / "FROZEN-MANIFEST.txt"
FREEZE_README = SPECS / "README.md"

#: The cutover this freeze records. Stated in `specs/README.md` and asserted below, so the
#: date cannot be dropped from the directory the issue required it to be stated in.
CUTOVER = "2026-09-15"

#: Not frozen. Historical record and live rules -- see the module docstring.
LIVE_RECORDS = {"IMPLEMENTED.md", "DECLINED.md", "INVARIANTS.md", "README.md"}

#: Pointer used in every failure message, so the guard explains the freeze it enforces.
POINTER = "specs/ is frozen (cutover %s); see specs/README.md" % CUTOVER


def manifest_names():
    """The pinned set: every non-comment, non-blank line of the manifest."""
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines
            if line.strip() and not line.lstrip().startswith("#")}


def spec_files():
    """Every `*.md` in specs/ that is not one of the live records."""
    return {p.name for p in SPECS.glob("*.md") if p.name not in LIVE_RECORDS}


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
            "because they are still written to -- the ledger is what six INVARIANTS.md "
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
