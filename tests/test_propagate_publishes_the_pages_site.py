"""The propagate mirror publishes the GitHub Pages site, and no dev slug with it (#452).

The quick-start site under `docs/` (`index.html`, `index.css`, `images/`, `.nojekyll`) was
added directly in the public access repo. `propagate.sh` mirrors `docs/` with
`rsync --delete`, so until dev owned the site, every propagation would have deleted it. Dev
owns it now, with the dev slug and the dev install ID in `docs/index.html`, and the rewrite
pass turns them back into the public ones on the way out.

⛔ **A suffix left off the rewrite pass publishes the dev slug.** The pass read only `.md`
and `.json` until #452 added `.html` and `.css`. So this module runs `propagate.sh` against
this repository into a throwaway destination, and checks that all six site paths land and
that no propagated file of **any** type still holds
`docktermj/senzing-bootcamp-claude-plugin-development`. It reads every file as bytes, so the
site's PNGs are scanned without being decoded. Its negative control drops `.html` from the
script's suffixes and shows the slug survives in `docs/index.html` and is caught.

⚠️ **What a green run does not establish.** It does not compare the published page with the
public repo's copy: that was a one-time manual check, recorded in #452's pull request. Nor
does it check that the page's `claude plugin …` commands match `docs/README.md`.

⚠️ **Where `bash`, `git`, `rsync` or `python3` is absent, the module SKIPS and says so**
(INV-308), as its sibling `tests/test_propagate_publishes_the_published_marketplace_name.py`
does. The propagate helpers are imported from that sibling, so the two run the script the
same way.

Source issue: #452.

Stdlib only; no network, no second checkout.

Run:  python3 -m unittest discover -s tests
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_propagate_publishes_the_published_marketplace_name as sibling  # noqa: E402

REPO_ROOT = sibling.REPO_ROOT
SCRIPT = sibling.SCRIPT
PROPAGATE_REL = sibling.PROPAGATE_REL

DEV_SLUG = b"docktermj/senzing-bootcamp-claude-plugin-development"
PUBLIC_SLUG = b"Senzing/senzing-bootcamp-claude-plugin"

#: The site, as #452 brought it across. Stated rather than derived: the set is the subject.
SITE = (
    "docs/.nojekyll",
    "docs/images/apple-touch-icon.png",
    "docs/images/favicon-32.png",
    "docs/images/senzing-logo.png",
    "docs/index.css",
    "docs/index.html",
)

#: The suffix tuple as `propagate.sh` writes it, mutated by the negative control.
SUFFIXES_LINE = 'REWRITTEN_SUFFIXES = (".md", ".json", ".html", ".css")\n'


def _dev_slug_sites(root):
    """`path:line` for every occurrence of the dev slug under `root`, any file type."""
    sites = []
    for rel in sibling._files(root):
        data = (root / rel).read_bytes()
        start = data.find(DEV_SLUG)
        while start != -1:
            sites.append("%s:%d" % (rel, data.count(b"\n", 0, start) + 1))
            start = data.find(DEV_SLUG, start + 1)
    return sites


class TheDevRepoHoldsTheSite(unittest.TestCase):
    """The source side: the six paths exist, in their dev form."""

    def test_every_site_path_exists(self):
        for rel in SITE:
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), "%s is missing from dev" % rel)

    def test_the_page_carries_the_dev_slug_and_install_id(self):
        page = (REPO_ROOT / "docs" / "index.html").read_bytes()
        self.assertIn(DEV_SLUG, page)
        self.assertNotIn(PUBLIC_SLUG, page, "the page still carries the public slug; the "
                         "inverse transform was not applied")
        self.assertIn(b"senzing-bootcamp@senzing-bootcamp-dev", page)

    def test_the_rewrite_pass_reads_html_and_css(self):
        self.assertEqual(SCRIPT.read_text("utf-8").count(SUFFIXES_LINE), 1,
                         "propagate.sh's REWRITTEN_SUFFIXES no longer reads .md, .json, .html "
                         "and .css")


@unittest.skipUnless(sibling.HAVE_TOOLS, sibling.SKIP_REASON)
class ThePropagatedTreeCarriesTheSite(unittest.TestCase):
    """This repository, as propagate.sh publishes it."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dest = sibling._public_checkout(Path(cls._tmp.name) / "public")
        cls.done = sibling._propagate(SCRIPT, cls.dest)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        self.assertEqual(self.done.returncode, 0,
                         "propagate.sh failed" + sibling._report(self.done))

    def test_every_site_path_lands(self):
        for rel in SITE:
            with self.subTest(path=rel):
                self.assertTrue((self.dest / rel).is_file(),
                                "%s did not reach the public tree" % rel)

    def test_the_binaries_land_byte_for_byte(self):
        for rel in SITE:
            if rel.endswith(".png"):
                with self.subTest(path=rel):
                    self.assertEqual((self.dest / rel).read_bytes(),
                                     (REPO_ROOT / rel).read_bytes())

    def test_no_dev_slug_survives_anywhere(self):
        self.assertEqual(_dev_slug_sites(self.dest), [],
                         "the dev slug reached the public tree")

    def test_the_published_page_names_the_public_repo(self):
        page = (self.dest / "docs" / "index.html").read_bytes()
        self.assertIn(b"claude plugin marketplace add " + PUBLIC_SLUG, page)
        self.assertIn(b"claude plugin install senzing-bootcamp@senzing-bootcamp<", page)


@unittest.skipUnless(sibling.HAVE_TOOLS, sibling.SKIP_REASON)
class TheSlugCheckCatchesALeftover(unittest.TestCase):
    """Negative control: with `.html` off the suffix list, the page publishes the dev slug."""

    def test_dropping_html_from_the_suffixes_leaves_the_slug_in_the_page(self):
        text = SCRIPT.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        self.assertEqual(text.count(SUFFIXES_LINE), 1,
                         "propagate.sh no longer carries the suffix line; the control mutates "
                         "nothing")
        text = text.replace(SUFFIXES_LINE, 'REWRITTEN_SUFFIXES = (".md", ".json", ".css")\n')
        with tempfile.TemporaryDirectory() as tmp:
            dev = Path(tmp) / "dev"
            (dev / "plugins" / "senzing-bootcamp").mkdir(parents=True)
            (dev / ".claude-plugin").mkdir()
            (dev / ".claude-plugin" / "marketplace.json").write_text("{}\n", "utf-8")
            (dev / "README.md").write_text("readme\n", "utf-8")
            (dev / "docs").mkdir()
            (dev / "docs" / "index.html").write_bytes(
                (REPO_ROOT / "docs" / "index.html").read_bytes())
            (dev / PROPAGATE_REL).parent.mkdir(parents=True)
            (dev / PROPAGATE_REL).write_bytes(text.encode("utf-8"))
            dest = sibling._public_checkout(Path(tmp) / "public")
            done = sibling._propagate(dev / PROPAGATE_REL, dest)
            self.assertEqual(done.returncode, 0, sibling._report(done))
            sites = _dev_slug_sites(dest)
        self.assertTrue(any(s.startswith("docs/index.html:") for s in sites),
                        "the dev slug did not survive with .html off the list: %s" % sites)


if __name__ == "__main__":
    unittest.main()
