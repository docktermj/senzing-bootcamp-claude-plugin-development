"""`/release` edits every file in the repo that asserts the plugin version.

Enforces **INV-383**, registered by the maintainer 2026-10-20. ⚠️ It **cannot** establish that a version asserted in a shape no text scan reads — a rendered artifact, a value computed at run time — has been found; those are covered by their own guards.

`.claude/skills/release/release.py` carries a table, `VERSION_SITES`, naming each file
whose text states the plugin's version, and rewrites all of them in one pass. A table is
only as good as the day it was written: a third assertion site added later is released
stale, and nothing says so -- the release still "succeeds", the tag still exists, and one
shipped file quietly disagrees with the manifest about which version the bootcamper has.

Two of the three halves of the release were already guarded when this landed:

* `tests/test_example_recap_sync.py` pins the example recap's ``**Plugin version:**``
  row to `plugin.json`, so bumping one of *those two* alone is already red.
* The git tag was unguarded entirely -- see
  `tests/test_release_bumps_version_changelog_and_tag_together.py`.

⛔ **This file guards a third thing neither of those can see: a version site that does
not exist yet.** The recap-sync test names its two files literally, so a `version` field
added to, say, `.claude-plugin/marketplace.json` tomorrow is invisible to it. Here the
repo is *scanned*, so a new site fails this test on the commit that introduces it rather
than on the release that ships it stale.

⚠️ **The scan reads tracked files only** (`git ls-files`), which is what a release
publishes. An untracked file asserting a version is out of scope, and so is anything the
skip list below excludes -- each exclusion is a file that *mentions* a version rather
than *asserting* one:

* `specs/` -- audit records quoting the version observed on a given date. Rewriting them
  would falsify the record.
* `feedback/` -- raw bootcamper text; a version in it is a report, not a claim.
* `CHANGELOG.md` -- every past version appears in it by construction; `release.py`
  prepends to it rather than rewriting it.
* `MIGRATION.md` -- Kiro-Power sync infrastructure, versioned separately.

⚠️ **What a green run does NOT mean.** It means no *tracked, non-excluded* file states
the current version in an assignment-shaped line that `release.py` would miss. It does
not mean the rewrite is correct, that the two sites agree with each other (that is the
recap-sync test), or that a site asserting the version in some other shape -- a rendered
PDF, a version computed at runtime, prose saying "you are on version five point three" --
has been found. Those shapes are invisible here and always will be.

⚠️ **One false-positive shape is known and accepted.** The assertion pattern keys on
``version``, optionally followed by ``:`` or ``=``, and then the number, so documentation
that happens to write ``version: <the current version>`` as a worked example trips it.
That is a loud, easily-read failure, and tightening the pattern to dodge it would blind
the guard to the real case, which has exactly the same shape.

⛔ **The scan also looks the other way: an assertion at a version that is NOT the
current one (#697).** Reporting only assertions *equal to* the current version is the
blind spot that let the 0.7.0 release leave three sites at 0.6.1 -- a site left behind is
filtered out before it can be reported, so each release widened the gap rather than
closing it, and the same finding would have returned at 0.7.1.

⚠️ **That direction needs a narrower pattern, and the narrowing was measured rather
than guessed.** Measured against the tree on 2026-10-17, with the manifest at
0.7.0 -- written apart from the word so this paragraph is not itself a site:

* ``ASSERTION`` with the filter inverted reports **27** lines, **26** of them correct
  prose -- other products' versions (``"version": "1.39.0"`` in the MCP snapshot,
  ``**Python version:** 3.12.3``, ``SDK ... version 4.3.3``, d3 ``7.9.0``), deliberate
  test fixtures (``9.9.9``, ``1.0.0``, ``0.4.0``, ``0.5.0``), the dry-run sentinel
  ``0.0.0-dryrun``, and this module's own docstring example. One real finding.
* ``PLUGIN_ASSERTION`` -- the word *plugin* next to the number -- reports **15**, of which
  **14** are test fixtures.
* ``PLUGIN_ASSERTION`` outside ``tests/`` reports **1**: the real finding.

So the stale direction uses ``PLUGIN_ASSERTION`` and skips ``tests/``. Skipping ``tests/``
costs nothing: a test cannot state the *current* plugin version in assertion shape without
failing the forward check above, so a test can never go stale by a release -- while a test
fixture necessarily states a version that is not the current one, forever.

⚠️ **What the stale direction does NOT see.** A line-scoped scan reads one line, so a
sentence whose subject and number straddle a line wrap -- BLUEPRINT.md section 5.2's
``the version`` / ```0.7.0``` -- is invisible to it. That site is covered instead by being
listed in ``VERSION_SITES``, where ``test_the_listed_sites_all_state_the_manifest_version``
compares it directly; and a version drawn into a PDF is invisible to any text scan, which
is why ``tests/test_example_recap_sync.py`` compares the shipped PDF's extracted text.

No count is asserted anywhere here. A test pinning "two version sites" fails the day a
legitimate third one is added and teaches its reader to bump a number, which is the defect
living inside the guard.

⚠️ **Enforces INV-301's "every record that asserts the version" clause**, and only that
clause. It compares the declared version sites against the repository in both directions. It
does **NOT** establish that a release actually moved them — that is the sibling module — nor
that every site is *reachable* by the tooling: a version asserted inside a binary artifact
cannot be rewritten by a text substitution, and `bootcamp_recap.example.pdf` is one such site,
already reading a version behind the manifest at the time this was written.

Stdlib only; the tracked-file list comes from git and every file is read as text (INV-108).

Source issue: #27 (`/release`).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from pathlib import PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_PY = REPO_ROOT / ".claude" / "skills" / "release" / "release.py"
MANIFEST_REL = "plugins/senzing-bootcamp/.claude-plugin/plugin.json"

#: Top-level paths that mention a version without asserting one. Every entry is justified
#: in the module docstring; adding one without a reason there is how a real site gets
#: excused.
SKIP_ROOTS = ("specs", "feedback", "CHANGELOG.md", "MIGRATION.md")

#: Binary or rendered artifacts the scan cannot read as text.
SKIP_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".pyc", ".ico", ".woff")

#: An ASSERTION, not a mention: ``version``, then the number, tolerating the quotes of
#: JSON, the asterisks of a Markdown meta row (``**Plugin version:** 0.0.0``) and the
#: backticks of prose (``the version `0.0.0```). The ``:``/``=`` is optional (#697) so the
#: prose form ``plugin version 0.0.0`` is an assertion here too; what still separates an
#: assertion from a mention is that nothing may stand between the word and the number.
#: "bumped the version from 0.0.0", "see the 0.0.0 release notes" and "the version is
#: checked at 0.0.0" all have something in that position and do not match.
ASSERTION = re.compile(r"""(?i)version["'*`]*\s*[:=]?\s*["'*`]*\s*(\d+\.\d+\.\d+)""")

#: A PLUGIN-version assertion: the word ``plugin``, then ``version`` or a bare ``v``, then
#: the number. Deliberately narrower than ``ASSERTION`` -- it is used for the stale
#: direction, where every version in the repository that is not the current one is a
#: candidate and the repository is full of legitimately-old numbers. The module docstring
#: carries the measurement that chose it.
#:
#: The trailing ``(?![\w.-])`` drops a suffixed version: ``**Plugin version:**
#: 0.0.0-dryrun`` is the dry-run scaffold's sentinel, and the manifest's version is always
#: a bare MAJOR.MINOR.PATCH, so a suffixed number can never be a stale copy of it.
PLUGIN_ASSERTION = re.compile(
    r"""(?i)plugin\s+(?:version|v)["'*`:]*\s*["'*`]*(\d+\.\d+\.\d+)(?![\w.-])""")

#: Top-level paths the STALE scan skips on top of ``SKIP_ROOTS``. ``tests/`` is the whole
#: list, and the reason is structural rather than convenient -- see the module docstring.
STALE_SKIP_ROOTS = SKIP_ROOTS + ("tests",)


def load_release_module():
    spec = importlib.util.spec_from_file_location("release_under_test", RELEASE_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tracked_files():
    done = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files"],
                          capture_output=True, text=True)
    if done.returncode != 0:
        return []
    return [line.strip() for line in done.stdout.splitlines() if line.strip()]


def is_scanned(relpath, skip_roots=SKIP_ROOTS):
    parts = PurePosixPath(relpath).parts
    if parts and parts[0] in skip_roots:
        return False
    return not relpath.lower().endswith(SKIP_SUFFIXES)


def current_version():
    return json.loads((REPO_ROOT / MANIFEST_REL).read_text(encoding="utf-8"))["version"]


def scan(pattern, keep, skip_roots=SKIP_ROOTS):
    """{relpath: [(line number, matched version, line)]} for every tracked, scanned file.

    `keep` decides which matched version counts, so one scanner serves both directions:
    equal to the current version (the site `/release` must know about) and anything other
    than it (the site a release left behind).

    Line-scoped by design (#424): a version is one token, which a line break cannot split.
    """
    found = {}
    for relpath in tracked_files():
        if not is_scanned(relpath, skip_roots):
            continue
        path = REPO_ROOT / relpath
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = [(number, match.group(1), line.strip()[:100])
                for number, line in enumerate(text.splitlines(), 1)
                for match in pattern.finditer(line) if keep(match.group(1))]
        if hits:
            found[relpath] = hits
    return found


def files_asserting(version):
    """Every tracked, scanned file stating `version` in assertion shape."""
    return scan(ASSERTION, lambda found: found == version)


def files_asserting_another_version(version):
    """Every tracked, scanned file asserting a PLUGIN version that is not `version`."""
    return scan(PLUGIN_ASSERTION, lambda found: found != version,
                skip_roots=STALE_SKIP_ROOTS)


@unittest.skipUnless(shutil.which("git"), "git lists the tracked files this scan reads")
class NeitherSideIsEmpty(unittest.TestCase):
    """INV-265 -- a set comparison is satisfied trivially when either side is empty."""

    def test_the_release_script_is_where_this_test_thinks(self):
        self.assertTrue(
            RELEASE_PY.is_file(),
            "%s is gone; the release skill moved and this guard is reading nothing"
            % RELEASE_PY)

    def test_the_table_was_loaded_and_is_not_empty(self):
        sites = load_release_module().VERSION_SITES
        self.assertGreaterEqual(
            len(sites), 1,
            "VERSION_SITES in %s is empty, so the comparison below would accept a repo "
            "with no version site at all" % RELEASE_PY)
        for site in sites:
            self.assertIn("path", site)
            self.assertIn("why", site)
            self.assertTrue(
                site["why"].strip(),
                "version site %r carries no reason; every other rule in this repo states "
                "the failure it prevents" % site["path"])

    def test_the_repo_was_scanned(self):
        scanned = [relpath for relpath in tracked_files() if is_scanned(relpath)]
        self.assertGreaterEqual(
            len(scanned), 50,
            "only %d tracked files were scanned; the listing has drifted and every check "
            "below would pass by finding nothing" % len(scanned))

    def test_the_assertion_pattern_finds_the_manifest(self):
        """Anchored on a file that predates this guard, so it cannot pass tautologically."""
        found = files_asserting(current_version())
        self.assertIn(
            MANIFEST_REL, found,
            "the assertion pattern did not find the version in %s, the one file that "
            "certainly states it; the pattern no longer matches how a version is written"
            % MANIFEST_REL)

    def test_the_pattern_rejects_a_mere_mention(self):
        """⛔ Anti-vacuity the other way: a pattern matching everything proves nothing.

        The last three probes guard the widening (#697): dropping the requirement for a
        ``:`` or ``=`` admits the prose form ``plugin version 1.2.3``, and the line
        between an assertion and a mention becomes "nothing stands between the word and
        the number". These are the shapes that would be swept in if that line moved.
        """
        for prose in ("bumped the version from 1.2.3 to 1.3.0",
                      "see the 1.2.3 release notes",
                      "Python version is checked at 3.12.3 by a different rule",
                      "the versions 1.2.3 and later carry it",
                      "released under version control since 1.2.3",
                      "this version predates 1.2.3 entirely"):
            matches = [m.group(1) for m in ASSERTION.finditer(prose)]
            self.assertNotIn(
                "1.2.3", matches,
                "the assertion pattern matched prose (%r); it is finding mentions rather "
                "than assertions and its findings cannot be trusted" % prose)

    def test_the_pattern_finds_the_prose_shapes_it_was_widened_for(self):
        """⛔ The other half of the same anti-vacuity: a widening that widened nothing.

        Both shapes are live in BLUEPRINT.md and both were left at 0.6.1 by the 0.7.0
        release precisely because the pattern could not see them (#697).
        """
        for prose in ("run on plugin version 1.2.3: the header fields",
                      "the version `1.2.3` (the single version every other one matches)"):
            matches = [m.group(1) for m in ASSERTION.finditer(prose)]
            self.assertIn(
                "1.2.3", matches,
                "the assertion pattern no longer matches %r, the prose shape it was "
                "widened to cover; a version asserted this way is invisible again" % prose)

    def test_the_plugin_assertion_pattern_finds_the_shipped_example_row(self):
        """⛔ INV-265 on the stale scan: its pattern and its file set are both non-empty.

        Anchored on a site that predates this direction entirely -- the shipped example
        recap's meta row, which `release.py` has always rewritten -- so the stale scan
        cannot report "nothing is stale" by matching nothing anywhere.
        """
        version = current_version()
        found = scan(PLUGIN_ASSERTION, lambda hit: hit == version,
                     skip_roots=STALE_SKIP_ROOTS)
        self.assertIn(
            "plugins/senzing-bootcamp/docs/examples/bootcamp_recap.example.md", found,
            "the plugin-version pattern found no assertion of the current version %s "
            "anywhere outside tests/; it no longer matches how a plugin version is "
            "written, so reporting nothing stale would mean nothing at all" % version)

    def test_the_plugin_assertion_pattern_rejects_another_products_version(self):
        """⛔ The narrowing has to hold, or the stale scan reports 26 correct lines.

        Every probe is a real line from this repository (measured 2026-10-17).
        """
        for prose in ('"version": "1.39.0"',
                      "**Python version:** 3.12.3",
                      "The Senzing SDK was already installed (version 4.3.3, build ...)",
                      "MCP_SERVER_VERSION = \"1.32.9\"",
                      "**Plugin version:** 0.0.0-dryrun"):
            matches = [m.group(1) for m in PLUGIN_ASSERTION.finditer(prose)]
            self.assertEqual(
                [], matches,
                "the plugin-version pattern matched %r, which asserts something other "
                "than this plugin's version; the stale scan would report correct prose "
                "forever and be turned off" % prose)


@unittest.skipUnless(shutil.which("git"), "git lists the tracked files this scan reads")
class EveryVersionSiteIsInTheTable(unittest.TestCase):
    def test_no_tracked_file_asserts_a_version_release_py_would_miss(self):
        version = current_version()
        listed = {site["path"] for site in load_release_module().VERSION_SITES}
        found = files_asserting(version)
        missed = sorted(set(found) - listed)
        self.assertEqual(
            [], missed,
            "file(s) assert the plugin version %s but `/release` does not edit them: %s. "
            "A release would advance the manifest and leave these stating the old version. "
            "Either add the file to VERSION_SITES in %s, or make it read the version from "
            "%s instead of hardcoding it."
            % (version, "; ".join("%s:%d" % (path, found[path][0][0]) for path in missed),
               RELEASE_PY, MANIFEST_REL))

    def test_every_listed_site_exists_and_still_matches(self):
        """The reverse direction: a table entry pointing at nothing silently edits nothing."""
        module = load_release_module()
        broken = []
        for site in module.VERSION_SITES:
            path = REPO_ROOT / site["path"]
            if not path.is_file():
                broken.append("%s (missing)" % site["path"])
                continue
            if not site["pattern"].search(path.read_text(encoding="utf-8")):
                broken.append("%s (pattern no longer matches)" % site["path"])
        self.assertEqual(
            [], broken,
            "VERSION_SITES entr(ies) in %s no longer resolve: %s. `/release` refuses at "
            "run time rather than editing a subset, so this is a release that cannot "
            "happen at all until the table is corrected" % (RELEASE_PY, "; ".join(broken)))

    def test_the_listed_sites_all_state_the_manifest_version(self):
        """A site already stale would be released stale; the sites must agree before a bump."""
        module = load_release_module()
        version = current_version()
        disagreeing = []
        for site in module.VERSION_SITES:
            path = REPO_ROOT / site["path"]
            if not path.is_file():
                continue
            for match in site["pattern"].finditer(path.read_text(encoding="utf-8")):
                if match.group(2) != version:
                    disagreeing.append("%s states %s" % (site["path"], match.group(2)))
        self.assertEqual(
            [], disagreeing,
            "version site(s) disagree with %s (%s): %s. `/release` refuses on this, so the "
            "repo cannot be released until they are reconciled"
            % (MANIFEST_REL, version, "; ".join(disagreeing)))


@unittest.skipUnless(shutil.which("git"), "git lists the tracked files this scan reads")
class NoSiteWasLeftBehindAtAnOlderVersion(unittest.TestCase):
    """⛔ The direction the guard could not look, which is how three sites went stale.

    ``EveryVersionSiteIsInTheTable`` asks "does any file state the version `/release`
    is about to move?". It cannot ask "does any file state a version `/release` already
    moved past?", because its filter keeps only matches **equal to** the current version
    -- so a site left behind is discarded before it can be reported, and each release
    widens the gap rather than closing it (#697).
    """

    def test_no_tracked_file_asserts_a_plugin_version_other_than_the_current_one(self):
        version = current_version()
        found = files_asserting_another_version(version)
        stale = sorted("%s:%d states %s" % (path, number, stated)
                       for path, hits in found.items()
                       for number, stated, _ in hits)
        self.assertEqual(
            [], stale,
            "file(s) assert a plugin version other than %s, which %s states: %s. A "
            "release moved the manifest and left these behind. Bring each to the current "
            "version, and add it to VERSION_SITES in %s (or make it read the version "
            "from the manifest) so the next release moves it too."
            % (version, MANIFEST_REL, "; ".join(stale), RELEASE_PY))


if __name__ == "__main__":
    unittest.main()
