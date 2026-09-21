"""`sites` says what it scanned on every run, not only when it finds nothing.

`pending_invariants.py sites <n>` prints candidate lines a citation may need to reach. Its
candidate corpus is `shipped_files()`, which walks the plugin alone; `resolve()` — the other
half of the same command — reads `RESOLUTION_ROOTS`, widened to the repository root by #59. So
one command resolves a **named** site anywhere and scans for unnamed ones in one root, and
⛔ **it said so only on the two branches where the scan found nothing.**

A non-empty candidate list is the output that reads as *the* set. Measured on this repository
when #77 was filed: the scan covers **63 of 950** `.md`/`.py` files, 6.6%, and the maintainer was
told none of that on the branch where it mattered.

⛔ **The scope is COUNTED, never listed.** The obvious version names `tests/`, `.claude/` and
`specs/` in prose — the shape the comment above `RESOLUTION_ROOTS` rejects in its own words: a
list goes stale as the repo grows, and going stale here is silent. A directory that appears
tomorrow enters the count on its own.

⚠️ **The scan is NOT widened, by decision (#77).** Widening to `.claude/` — where INV-307,
INV-308 and INV-309 actually ship — would recompute the rarity weighting over a larger corpus,
and with **no pending block in the queue** there is nothing real to measure the effect against.
Widening a lead generator blind is how a worklist fills with noise. So for an invariant shipping
outside the plugin the candidate list stays empty, and the run now says so in a number rather
than implying a measured absence.

⛔ **These fixtures are fabricated, and that is a real limit.** The live queue is empty
(`pending: 0`), so nothing here exercises the command against a block a maintainer actually
wrote. The assertions establish what the command prints for a block of the right *shape*; they
do not establish that the shape matches every block the ledger has held.

Stdlib only; the helper is loaded by path and its module-level roots are pointed at a temporary
tree, since it takes no `--repo` argument (INV-108).

Source issue: #77.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"
SKILL = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "review-invariants.md"

#: A block in the shape `parse()` reads: a rule bullet naming its site, then drafted wording.
#: ⚠️ The wording matters to the scan — its rare 6+-character words are the search terms — so a
#: fixture whose wording does not parse produces an empty candidate list for the wrong reason,
#: which is how the first draft of this file "passed".
LEDGER = """# Implemented Specs

## a-demo-spec

- **DEFERRED INVARIANT — awaiting the maintainer's sign-off; NOT minted.**
    - ⛔ **Never ship a provenance claim without its supplier.** — in `skills/demo/SKILL.md`

  **INV-NNN** — every provenance claim names the supplier that provided it.
"""

NAMED_RULE = "- ⛔ **Never ship a provenance claim without its supplier.**\n"
CANDIDATE_RULE = "intro\n- ⛔ **Every provenance claim names its supplier.**\n"


def load():
    spec = importlib.util.spec_from_file_location("pending_invariants_under_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pending_invariants_under_test"] = module
    spec.loader.exec_module(module)
    return module


def build(tmp, with_candidate):
    """A repository tree with one deferral, one named site, and files outside the scan."""
    root = Path(tmp)
    (root / "specs").mkdir()
    (root / "tests").mkdir()
    (root / ".claude").mkdir()
    plugin = root / "plugins" / "senzing-bootcamp" / "skills" / "demo"
    plugin.mkdir(parents=True)
    (plugin / "SKILL.md").write_text(NAMED_RULE, encoding="utf-8")
    if with_candidate:
        (plugin / "OTHER.md").write_text(CANDIDATE_RULE, encoding="utf-8")
    (root / "tests" / "test_demo.py").write_text("# a file the scan never opens\n",
                                                 encoding="utf-8")
    (root / ".claude" / "note.md").write_text("# another one\n", encoding="utf-8")
    (root / "specs" / "IMPLEMENTED.md").write_text(LEDGER, encoding="utf-8")
    # ⛔ Two files under `specs/`, and the split between them is the whole of #92: one is pinned
    # by the manifest and therefore ineligible; the other is a live record that a `specs/` prefix
    # test would wrongly sweep in with it.
    (root / "specs" / "an-archived-spec.md").write_text("# frozen\n", encoding="utf-8")
    (root / "specs" / "FROZEN-MANIFEST.txt").write_text(
        "# the pinned set\nan-archived-spec.md\n", encoding="utf-8")
    return root


def sites_output(root):
    """`sites 1` against `root`, with the helper's module-level roots pointed at it."""
    module = load()
    module.REPO = root
    module.LEDGER = root / "specs" / "IMPLEMENTED.md"
    module.SPECS = root / "specs"
    module.PLUGIN = root / "plugins" / "senzing-bootcamp"
    module.RESOLUTION_ROOTS = (module.PLUGIN / "skills", module.PLUGIN / "scripts",
                               module.PLUGIN, root)
    module.FROZEN_MANIFEST = root / "specs" / "FROZEN-MANIFEST.txt"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        module.cmd_sites(1)
    return out.getvalue()


class TheFixtureExercisesWhatTheseAssertionsClaim(unittest.TestCase):
    """⛔ INV-265 — a fixture whose candidate list is empty for the wrong reason proves nothing."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sites-scope-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_helper_is_where_this_test_expects(self):
        self.assertTrue(HELPER.is_file(),
                        "%s is gone; re-anchor this test rather than letting it pass" % HELPER)

    def test_the_candidate_fixture_really_produces_a_candidate(self):
        """The whole point is the branch that FINDS something; it must actually find it."""
        out = sites_output(build(self.tmp, with_candidate=True))
        self.assertIn(
            "skills/demo/OTHER.md", out,
            "the fixture produced no candidate, so the assertions about the found-candidates "
            "branch would be measuring the empty branch instead:\n%s" % out)

    def test_the_empty_fixture_really_produces_none(self):
        out = sites_output(build(self.tmp, with_candidate=False))
        self.assertIn("(none found)", out,
                      "the no-candidate fixture found one; the two branches are not being "
                      "exercised separately:\n%s" % out)


class TheScopeIsStatedOnEveryBranch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sites-scope-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_scope_is_stated_when_candidates_were_found(self):
        """⛔ The defect: this is the branch that reads as an answer, and it said nothing."""
        out = sites_output(build(self.tmp, with_candidate=True))
        self.assertIn(
            "SCANNED", out,
            "a run that found candidates printed no statement of what it scanned. That list "
            "reads as THE set, and 887 of this repository's 950 candidate files were never "
            "opened:\n%s" % out)
        self.assertIn("NOT SCANNED", out, out)

    def test_the_scope_is_stated_when_nothing_was_found(self):
        out = sites_output(build(self.tmp, with_candidate=False))
        self.assertIn("SCANNED", out, out)
        self.assertIn("NOT SCANNED", out, out)

    def test_the_scanned_root_is_named(self):
        out = sites_output(build(self.tmp, with_candidate=True))
        self.assertIn(
            "plugins/senzing-bootcamp", out,
            "the output does not name the corpus it read, so a reader cannot tell what the "
            "candidate list covers:\n%s" % out)

    def test_both_counts_are_real_numbers(self):
        out = sites_output(build(self.tmp, with_candidate=True))
        scanned = re.search(r"SCANNED \S+: (\d+) file", out)
        unscanned = re.search(r"NOT SCANNED (\d+) file", out)
        self.assertIsNotNone(scanned, "no scanned count:\n%s" % out)
        self.assertIsNotNone(unscanned, "no unscanned count:\n%s" % out)
        self.assertEqual(
            2, int(scanned.group(1)),
            "the fixture ships two files under the scanned root; a different number means "
            "the count is not measuring the corpus the scan reads:\n%s" % out)
        self.assertEqual(
            3, int(unscanned.group(1)),
            "the fixture holds three candidate-suffixed files outside the scanned root "
            "(a test, a .claude note, and the ledger); the unscanned count must be measured "
            "over the same suffixes, not guessed:\n%s" % out)

    def test_the_unscanned_directories_are_derived_not_listed(self):
        """⛔ A hardcoded list goes stale silently — the reason RESOLUTION_ROOTS is a root."""
        out = sites_output(build(self.tmp, with_candidate=True))
        self.assertRegex(
            out, r"(tests|specs|\.claude)/ \d+",
            "the unscanned directories are not reported with their counts, so the statement "
            "cannot be checked against the tree it describes:\n%s" % out)
        body = HELPER.read_text(encoding="utf-8")
        scope = body[body.index("def scan_scope"):body.index("def cmd_list")]
        for literal in ('"tests"', '"specs"', '".claude"'):
            with self.subTest(literal=literal):
                self.assertNotIn(
                    literal, scope,
                    "the scope report names %s as a literal. A directory list goes stale as "
                    "the repository grows and going stale here is silent, which is why "
                    "RESOLUTION_ROOTS is a root rather than an allowlist" % literal)

    def test_it_says_a_named_site_still_resolves_anywhere(self):
        """Without this, the scope line reads as 'sites outside the plugin do not count'."""
        out = sites_output(build(self.tmp, with_candidate=True))
        self.assertRegex(
            out.lower(), r"named in the block still\s+resolves",
            "the scope statement does not say that a NAMED site still resolves outside the "
            "scanned root. The two halves differ deliberately, and a reader told only about "
            "the narrow half will think a site elsewhere cannot be cited:\n%s" % out)


class IneligibleFilesAreCountedApart(unittest.TestCase):
    """⚠️ "Not scanned" and "could be a site" are different sets (#92).

    Reporting them as one overstated the gap by more than half on the real repository: of 889
    unscanned files, 523 were the frozen archive, which INV-307 makes read-only so a citation can
    never land there. ⛔ A figure a reader checks once and finds mostly irrelevant is a figure
    they learn to discount — and the eligible remainder is inside it.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sites-scope-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_frozen_file_is_excluded_not_counted_as_unscanned(self):
        out = sites_output(build(self.tmp, with_candidate=True))
        self.assertRegex(
            out, r"EXCLUDED 1 frozen file\(s\)",
            "the file pinned by the archive manifest is not reported as excluded, so it is "
            "inflating the count of files that could hold a site:\n%s" % out)

    def test_a_live_record_under_specs_is_still_eligible(self):
        """⛔ The trap a `specs/` prefix test falls into, and why the manifest is read instead."""
        out = sites_output(build(self.tmp, with_candidate=True))
        m = re.search(r"NOT SCANNED (\d+) file", out)
        self.assertIsNotNone(m, out)
        self.assertEqual(
            3, int(m.group(1)),
            "the eligible count is not 3. The fixture holds a test file, a `.claude/` note and "
            "a LIVE record under `specs/` that the manifest does NOT pin -- excluding it by "
            "path prefix would sweep in the very records the freeze exempts:\n%s" % out)

    def test_the_excluded_count_prints_when_it_is_zero(self):
        """⚠️ Same precedent as the count beside it: zero is a measurement, not silence."""
        root = build(self.tmp, with_candidate=True)
        (root / "specs" / "FROZEN-MANIFEST.txt").write_text("# nothing pinned\n", encoding="utf-8")
        out = sites_output(root)
        self.assertRegex(
            out, r"EXCLUDED 0 frozen file\(s\)",
            "the excluded count vanishes at zero, so its absence has to be interpreted:\n%s" % out)

    def test_the_exclusion_is_read_from_the_manifest_not_a_path_literal(self):
        """⛔ A prefix is a second definition of the freeze; the manifest is the first."""
        body = HELPER.read_text(encoding="utf-8")
        scope = body[body.index("def frozen_names"):body.index("def print_scan_scope")]
        self.assertIn(
            "FROZEN_MANIFEST", scope,
            "the ineligible set is no longer derived from the archive manifest; if it now tests "
            "for a path prefix, it disagrees with the freeze about the live records")
        self.assertNotIn(
            '"specs"', scope,
            "the scope computation names `specs` as a literal. The manifest already says what "
            "the freeze covers, and a second spelling of it goes stale silently")


class TheDocumentsCarryTheCaveat(unittest.TestCase):
    """⛔ The output fix alone leaves the wrong instruction standing."""

    def test_the_skill_does_not_tell_the_maintainer_to_derive_the_set_from_a_partial_scan(self):
        text = re.sub(r"\s+", " ", SKILL.read_text(encoding="utf-8"))
        self.assertIn(
            "Derive the site set from `sites` and from scanning", text,
            "the instruction this caveat attaches to has been reworded; re-anchor rather than "
            "letting the assertion below pass on absent text")
        self.assertRegex(
            text.lower(), r"scan (?:covers|reads) (?:one root|the plugin)",
            "SKILL.md tells the maintainer to derive the site set from `sites` without saying "
            "that its candidate scan reads one root. For an invariant shipping in `.claude/` "
            "or `tests/` that instruction points at a scan covering none of it")

    def test_the_command_says_which_corpus_the_candidates_come_from(self):
        text = re.sub(r"\s+", " ", COMMAND.read_text(encoding="utf-8"))
        self.assertRegex(
            text.lower(), r"scan (?:covers|reads) (?:one root|the plugin)",
            "the command describes the three groups without saying that the candidates come "
            "from one root, so a reader takes the group as complete")


if __name__ == "__main__":
    unittest.main()
