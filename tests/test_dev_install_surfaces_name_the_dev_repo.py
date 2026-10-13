"""The dev repository's install surfaces name the dev repository, never the public one (#522).

This repository has three install surfaces: the root `README.md` (the Claude Desktop route and
the example recap PDF link), `docs/README.md` (the Claude Code CLI route) and `docs/index.html`
(the GitHub Pages quick-start site). In this tree each MUST name the development repository,
`docktermj/senzing-bootcamp-claude-plugin-development`; `propagate.sh` rewrites that slug to the
public one, `Senzing/senzing-bootcamp-claude-plugin`, on the way out.

**Why this module exists.** Commit 6e973b15 (#451) brought the public README's new Desktop
steps across and kept their public slug, so dev's Desktop route installed the published plugin
rather than the one under development. Only `docs/index.html` was checked
(`tests/test_propagate_publishes_the_pages_site.py`), and INV-348 compares that page's
`claude plugin …` commands with `docs/README.md`, not its Desktop route.

What it asserts, for each surface: the dev slug is present, the public slug is absent, and a
failure names the file. For `README.md` it also asserts the dev slug at the two sites #522
restored, the Desktop marketplace URL and the raw-content recap PDF link. Matching is on bytes:
the public slug is not a substring of the dev slug, so the two checks never overlap. Negative
controls put the public slug back at each README site and drop the dev slug from a surface,
and show each fails naming the file.

⚠️ **What a green run does not establish.** It reads the dev tree only. The published tree
carries the public slug at the same sites, and `tests/test_propagate_publishes_the_pages_site.py`
(INV-350) checks that no published file holds the dev slug. The surfaces are stated rather than
derived: a fourth install surface added later is not checked until it is added to `SURFACES`.
Owner names are matched in the case written here; a differently cased public slug is not caught.

Source issue: #522. The rule is drafted as a DEFERRED INVARIANT in the #522 entry of
`specs/IMPLEMENTED.md` for `/review-invariants`; this module is its enforcer.

Stdlib only (INV-108); three files read as bytes, no network.

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEV_SLUG = b"docktermj/senzing-bootcamp-claude-plugin-development"
PUBLIC_SLUG = b"Senzing/senzing-bootcamp-claude-plugin"

#: The install surfaces, stated rather than derived: the set is the subject.
SURFACES = ("README.md", "docs/README.md", "docs/index.html")

#: The two root-README sites #522 restored, each as its dev form and its public form.
README_SITES = (
    ("the Claude Desktop marketplace URL",
     b"https://github.com/" + DEV_SLUG + b"\n",
     b"https://github.com/" + PUBLIC_SLUG + b"\n"),
    ("the example recap PDF link",
     b"https://raw.githubusercontent.com/" + DEV_SLUG + b"/refs/heads/main/",
     b"https://raw.githubusercontent.com/" + PUBLIC_SLUG + b"/refs/heads/main/"),
)


def _read(rel):
    return (REPO_ROOT / rel).read_bytes()


def surface_problems(rel, data):
    """The problems with one surface's bytes, each naming the file; empty when it is right."""
    problems = []
    if DEV_SLUG not in data:
        problems.append("%s does not name the dev repository (%s)"
                        % (rel, DEV_SLUG.decode()))
    if PUBLIC_SLUG in data:
        line = data.count(b"\n", 0, data.find(PUBLIC_SLUG)) + 1
        problems.append("%s:%d names the public repository (%s); the dev tree must name %s"
                        % (rel, line, PUBLIC_SLUG.decode(), DEV_SLUG.decode()))
    return problems


def readme_site_problems(data):
    """The restored root-README sites that no longer carry the dev slug, naming the file."""
    return ["README.md: %s does not name the dev repository" % name
            for name, dev, _public in README_SITES if dev not in data]


class TheSlugsAreDistinct(unittest.TestCase):
    """The precondition the byte matching relies on."""

    def test_the_public_slug_is_not_inside_the_dev_slug(self):
        self.assertNotIn(PUBLIC_SLUG, DEV_SLUG)
        self.assertNotIn(DEV_SLUG, PUBLIC_SLUG)


class EveryInstallSurfaceNamesTheDevRepo(unittest.TestCase):
    """The real files."""

    def test_every_surface_exists(self):
        for rel in SURFACES:
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), "%s is missing" % rel)

    def test_every_surface_names_the_dev_repo_and_not_the_public_one(self):
        for rel in SURFACES:
            with self.subTest(path=rel):
                problems = surface_problems(rel, _read(rel))
                if problems:
                    self.fail("; ".join(problems))

    def test_the_restored_readme_sites_name_the_dev_repo(self):
        problems = readme_site_problems(_read("README.md"))
        if problems:
            self.fail("; ".join(problems))


class TheCheckCatchesThePublicSlug(unittest.TestCase):
    """Negative controls on copies of the real files."""

    def test_each_readme_site_put_back_to_the_public_slug_fails_naming_the_file(self):
        data = _read("README.md")
        for name, dev, public in README_SITES:
            with self.subTest(site=name):
                self.assertTrue(dev in data, "the control has nothing to mutate at %s" % name)
                mutated = data.replace(dev, public)
                problems = surface_problems("README.md", mutated)
                self.assertTrue(problems, "the public slug at %s passed" % name)
                self.assertTrue(all(p.startswith("README.md") for p in problems), problems)
                self.assertTrue(any("names the public repository" in p for p in problems))
                self.assertEqual(readme_site_problems(mutated),
                                 ["README.md: %s does not name the dev repository" % name])

    def test_a_surface_without_the_dev_slug_fails_naming_the_file(self):
        for rel in SURFACES:
            with self.subTest(path=rel):
                mutated = _read(rel).replace(DEV_SLUG, b"someone/some-other-repo")
                problems = surface_problems(rel, mutated)
                self.assertEqual(len(problems), 1, problems)
                self.assertIn(rel, problems[0])
                self.assertIn("does not name the dev repository", problems[0])

    def test_the_public_slug_on_the_page_fails_naming_the_page(self):
        rel = "docs/index.html"
        mutated = _read(rel) + b"\n<!-- " + PUBLIC_SLUG + b" -->\n"
        problems = surface_problems(rel, mutated)
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith(rel + ":"), problems)


if __name__ == "__main__":
    unittest.main()
