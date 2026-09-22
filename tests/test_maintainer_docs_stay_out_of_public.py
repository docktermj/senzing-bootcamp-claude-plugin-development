"""The maintainer pages in `docs/` are unreachable by the propagate mirror.

`docs/` is mirrored to the public access repo because it holds the install documentation a
bootcamper reads. Two files in it are **not** for bootcampers:

* `docs/development.md` -- the development-loop command index. Publishing it hands a user a
  list of commands their install does not have. It reached the public working tree once, on
  2026-08-16, precisely because "docs/ is user-facing" was a convention rather than a rule
  enforced anywhere.
* `docs/FAMILY_WORKFLOW.md` -- the family-wide normative workflow (#111). It names private
  development repositories a bootcamper cannot open and describes maintainer operations that
  ship in none of the public mirrors.

⛔ **Until #111 neither exclusion was asserted by anything.** `propagate.sh` carried them and
the sibling guard `tests/test_maintainer_tooling_stays_out_of_public.py` says in its own
docstring that a green run "does not mean ... that the exclusions inside the propagated roots
are right" -- so the second maintainer page was added to a mirror rule that nothing checked.

⚠️ **The pattern is parsed AND exercised.** Asserting that the string `--exclude='/x.md'`
appears in the script proves the author's intent, not the mirror's behavior: a leading slash
that anchors to the transfer root, a stray quote, or a pattern placed after the source
argument all read plausibly and mirror differently. `TheExclusionsActuallyExclude` runs the
parsed patterns through `rsync` over a temporary tree and checks what lands.

⚠️ **Where `rsync` is absent the behavioral half SKIPS and says so** (INV-308) -- it is a
declared dependency of `propagate.sh`, which exits if it is missing, so its absence here is a
property of the test machine and not of the mirror. The parse half still runs.

Source issue: #111.

Stdlib only; no network, no second checkout.

Run:  python3 -m unittest discover -s tests
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".claude" / "skills" / "propagate-to-public" / "propagate.sh"
DOCS = REPO_ROOT / "docs"

#: The maintainer pages, and why each is withheld. The set is the subject of this module, so it
#: is stated here rather than derived -- deriving it from the script is what it checks.
MAINTAINER_PAGES = {
    "development.md": "the development-loop command index",
    "FAMILY_WORKFLOW.md": "the family-wide normative workflow",
}

#: The `rsync` invocation that mirrors `docs/`, with its options, across a line continuation.
DOCS_RSYNC = re.compile(r"^rsync\s+(?P<opts>.*?)\"\$here/docs/\"", re.M | re.S)


def docs_rsync_options():
    m = DOCS_RSYNC.search(SCRIPT.read_text(encoding="utf-8"))
    return m.group("opts") if m else None


def parsed_excludes():
    opts = docs_rsync_options() or ""
    return set(re.findall(r"--exclude='([^']+)'", opts))


class TheMirrorLineWasFound(unittest.TestCase):
    """INV-265 -- every assertion below is vacuous if the line did not parse."""

    def test_the_docs_rsync_line_parses(self):
        self.assertIsNotNone(
            docs_rsync_options(),
            "no `rsync ... \"$here/docs/\"` invocation was found in %s. The script's shape has "
            "changed and this guard is checking nothing" % SCRIPT)

    def test_both_maintainer_pages_exist(self):
        missing = sorted(n for n in MAINTAINER_PAGES if not (DOCS / n).is_file())
        self.assertEqual([], missing,
                         "maintainer page(s) named by this guard do not exist: %s. An exclusion "
                         "for a file that is not there excludes nothing" % ", ".join(missing))


class EveryMaintainerPageIsExcluded(unittest.TestCase):
    def test_each_page_has_an_anchored_exclude(self):
        excludes = parsed_excludes()
        for name, why in sorted(MAINTAINER_PAGES.items()):
            with self.subTest(page=name):
                self.assertIn(
                    "/" + name, excludes,
                    "docs/%s (%s) is not excluded from the docs mirror in %s. Publishing it "
                    "puts a maintainer document in the repository bootcampers install from"
                    % (name, why, SCRIPT))

    def test_the_exclude_is_anchored_to_the_transfer_root(self):
        """An unanchored pattern also matches `docs/*/development.md`, which is a different rule."""
        for name in sorted(MAINTAINER_PAGES):
            with self.subTest(page=name):
                self.assertNotIn(
                    name, parsed_excludes(),
                    "the exclusion for %s is written without a leading slash, so it is not "
                    "anchored to the transfer root" % name)


class TheExclusionsActuallyExclude(unittest.TestCase):
    """Intent is not behavior. Run the parsed patterns and see what lands."""

    def test_running_rsync_with_them_withholds_the_pages(self):
        if shutil.which("rsync") is None:
            self.skipTest(
                "rsync is not installed on this machine, so the behavioral half of this guard "
                "COULD NOT RUN -- distinct from having run and found nothing (INV-308). "
                "propagate.sh declares rsync a hard dependency and exits without it, so this "
                "is a property of the test environment. The parse assertions above still ran")
        excludes = sorted(parsed_excludes())
        self.assertTrue(excludes, "no --exclude patterns parsed; nothing to exercise")
        with tempfile.TemporaryDirectory() as tmp:
            src, dest = Path(tmp) / "src", Path(tmp) / "dest"
            src.mkdir()
            for name in MAINTAINER_PAGES:
                (src / name).write_text("maintainer\n", encoding="utf-8")
            (src / "README.md").write_text("bootcamper\n", encoding="utf-8")
            (src / "nested").mkdir()
            (src / "nested" / "development.md").write_text("nested\n", encoding="utf-8")
            dest.mkdir()
            subprocess.run(
                ["rsync", "-a", "--delete", *[f"--exclude={p}" for p in excludes],
                 str(src) + "/", str(dest) + "/"],
                check=True, capture_output=True)
            for name in sorted(MAINTAINER_PAGES):
                self.assertFalse(
                    (dest / name).exists(),
                    "docs/%s survived the mirror despite its --exclude pattern" % name)
            self.assertTrue((dest / "README.md").exists(),
                            "the exclusions removed a user-facing file; they are too broad")
            self.assertTrue(
                (dest / "nested" / "development.md").exists(),
                "a nested development.md was excluded too, so the pattern is not anchored to "
                "the transfer root -- that is a different and wider rule than the one intended")


if __name__ == "__main__":
    unittest.main()
