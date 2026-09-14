"""`/release` edits every file in the repo that asserts the plugin version.

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
``version`` followed by ``:`` or ``=`` and then the number, so documentation that happens
to write ``version: <the current version>`` as a worked example trips it. That is a loud,
easily-read failure, and loosening the pattern to dodge it would blind the guard to the
real case, which has exactly the same shape.

No count is asserted anywhere here. A test pinning "two version sites" fails the day a
legitimate third one is added and teaches its reader to bump a number, which is the defect
living inside the guard.

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

#: An ASSERTION, not a mention: ``version`` then ``:``/``=`` then the number, tolerating
#: the quotes of JSON and the asterisks of a Markdown meta row
#: (``**Plugin version:** 0.0.0``). Prose such as "bumped the version from 0.0.0" has no
#: ``:`` or ``=`` in that position and does not match.
ASSERTION = re.compile(r"""(?i)version["'*]*\s*[:=]\s*["'*]*\s*(\d+\.\d+\.\d+)""")


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


def is_scanned(relpath):
    parts = PurePosixPath(relpath).parts
    if parts and parts[0] in SKIP_ROOTS:
        return False
    return not relpath.lower().endswith(SKIP_SUFFIXES)


def current_version():
    return json.loads((REPO_ROOT / MANIFEST_REL).read_text(encoding="utf-8"))["version"]


def files_asserting(version):
    """{relpath: [(line number, line)]} for every tracked, scanned file stating `version`."""
    found = {}
    for relpath in tracked_files():
        if not is_scanned(relpath):
            continue
        path = REPO_ROOT / relpath
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = [(number, line.strip()[:100])
                for number, line in enumerate(text.splitlines(), 1)
                for match in ASSERTION.finditer(line) if match.group(1) == version]
        if hits:
            found[relpath] = hits
    return found


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
        """⛔ Anti-vacuity the other way: a pattern matching everything proves nothing."""
        for prose in ("bumped the version from 1.2.3 to 1.3.0",
                      "see the 1.2.3 release notes",
                      "Python version is checked at 3.12.3 by a different rule"):
            matches = [m.group(1) for m in ASSERTION.finditer(prose)]
            self.assertNotIn(
                "1.2.3", matches,
                "the assertion pattern matched prose (%r); it is finding mentions rather "
                "than assertions and its findings cannot be trusted" % prose)


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


if __name__ == "__main__":
    unittest.main()
