"""INV-197: Module 4 recommends a data catalog it does not own, so it must say what that
catalog currently supports — at every place it recommends it.

The ICIJ Offshore Leaks sample is the one entry in `docktermj/senzing-bootcamp-free-data`
whose distinguishing value is *disclosed relationships* — the `REL_ANCHOR`/`REL_POINTER`
family. Its four files were sliced independently (the head of each) rather than from a
connected subgraph, so `relationships-sample.csv` references ids that appear in none of the
node files. Verified against the repository 2026-08-11: not one of its 10 rows has even a
single endpoint present, and every row is `rel_type=registered_address`.

Two properties this pins, because each failed once already:

* **The caveat lives at BOTH recommendation sites.** The catalog is recommended twice — in
  the secondary-options offer and again in the Agent behavior hierarchy — and a bootcamper
  routed through the second one is exactly as able to pick ICIJ as one routed through the
  first. A note at one site reads as covered while leaving the other silent (INV-182).
* **The plugin never repairs the data.** Module 4 recommends this catalog; it does not own
  it. Re-slicing or vendoring the files creates a second, divergent copy and hides the
  upstream defect — the reasoning INV-173 applies to forking an MCP-delivered validator.

⏳ **This whole file is retirable.** It pins a dated upstream condition, not a Senzing rule.
When `senzing-bootcamp-free-data` re-slices the samples from a connected subgraph, the note
in Module 4 is retired outright and this file goes with it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

# ⚠️ **Matches the ROUTE, not the exact argument string.** These assertions pinned the literal
# `search_docs(category='data_mapping')`, which stopped matching when
# `specs/search-docs-instructions-omit-the-required-query-parameter.md` gave every shipped
# reference the `query` the tool actually requires -- so the guards failed on the correction they
# should have welcomed, the pattern `specs/guards-pinning-a-dated-negative-outlive-it.md`
# describes. What they exist to assert is that the claim names its route; the route is still named.
ROUTE_DATA_MAPPING = re.compile(
    r"search_docs\([^)]*?category='data_mapping'\)")

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
MODULE_04 = PLUGIN / "skills" / "module-04-data-collection" / "SKILL.md"

CATALOG = "senzing-bootcamp-free-data"
# How far past a recommendation the caveat may sit and still be found by a reader
# following that recommendation.
#
# ⚠️ **Raised 40 -> 55 on 2026-08-23.** A fixed-line window is brittle to any edit inside it:
# giving the REL_ANCHOR/REL_POINTER citation at `module-04-data-collection/SKILL.md:504` the
# `query` that `search_docs` actually requires added three lines, which pushed
# "upstream condition" from offset 40 to exactly the boundary and failed a guard that had nothing
# to do with the change. The headroom is deliberate; if a future edit pushes it out again, widen
# it rather than trimming the caveat to fit a test.
WINDOW = 55


def text():
    return MODULE_04.read_text(encoding="utf-8")


def flat(chunk):
    return re.sub(r"\s+", " ", chunk.replace("**", ""))


def recommendation_sites():
    """Each place the catalog is recommended by URL, paired with the lines that follow it.

    Keyed on the URL rather than on line numbers: the spec cited `:190` and `:664`, and both
    had already drifted by the time it was implemented.

    Line-scoped by design (#424): the anchor is a URL, one token with no space in it, and the
    window that follows it is collapsed (``flat``) before any phrase is matched."""
    lines = text().splitlines()
    sites = {}
    for i, line in enumerate(lines):
        if f"https://github.com/docktermj/{CATALOG}" in line:
            sites[i + 1] = "\n".join(lines[i : i + WINDOW])
    return sites


class TheCatalogIsRecommendedInMoreThanOnePlace(unittest.TestCase):
    """The premise of every test below. If this stops holding, the windowing is wrong,
    not the plugin."""

    def test_two_sites_recommend_it_by_url(self):
        sites = recommendation_sites()
        self.assertEqual(
            2, len(sites), f"expected two recommendation sites, found {sorted(sites)}"
        )


class EveryRecommendationCarriesTheIcijCaveat(unittest.TestCase):
    def setUp(self):
        self.sites = recommendation_sites()

    def subtests(self):
        for line_no, chunk in sorted(self.sites.items()):
            yield line_no, flat(chunk)

    def test_each_site_names_the_sample_the_caveat_is_about(self):
        for line_no, chunk in self.subtests():
            with self.subTest(site=line_no):
                self.assertIn("ICIJ Offshore Leaks", chunk)

    def test_each_site_says_the_files_do_not_join(self):
        for line_no, chunk in self.subtests():
            with self.subTest(site=line_no):
                self.assertIn("do not join", chunk)
                self.assertRegex(
                    chunk,
                    r"[Nn]ot one of (its|the) 10 rows has even a single endpoint present"
                    r"|[Nn]ot one of the 10 rows in `relationships-sample\.csv` has an "
                    r"endpoint present",
                    "the join failure must be stated concretely, not as a vague warning",
                )

    def test_each_site_says_the_relationship_exercise_is_unavailable(self):
        for line_no, chunk in self.subtests():
            with self.subTest(site=line_no):
                self.assertIn("unavailable", chunk)
                self.assertIn("REL_ANCHOR", chunk)
                self.assertIn("REL_POINTER", chunk)

    def test_each_site_offers_service_provider_as_the_way_forward(self):
        """A warning with no path turns a usable source into a dead end."""
        for line_no, chunk in self.subtests():
            with self.subTest(site=line_no):
                self.assertIn("service_provider", chunk)
                self.assertIn("nodes-entities-sample.csv", chunk)

    def test_each_site_excludes_the_address_file_from_loadable_records(self):
        for line_no, chunk in self.subtests():
            with self.subTest(site=line_no):
                self.assertIn("nodes-addresses-sample.csv", chunk)
                self.assertIn("0% populated", chunk)
                self.assertIn("address nodes, not entities", chunk)

    def test_each_site_dates_the_finding_and_marks_it_for_re_check(self):
        """An undated claim about someone else's repository becomes a permanent lie the
        moment they fix it."""
        for line_no, chunk in self.subtests():
            with self.subTest(site=line_no):
                self.assertIn("2026-08-11", chunk)
                self.assertIn("upstream condition", chunk)
                self.assertIn("re-check", chunk)

    def test_neither_site_calls_the_sample_broken(self):
        """Three of the four files are fine and the entity mapping exercise works."""
        for line_no, chunk in self.subtests():
            with self.subTest(site=line_no):
                self.assertNotRegex(
                    chunk,
                    r"(?<!not call it )(?<!not call the sample )broken(?! )",
                    "only the do-not-call-it-broken instruction may use the word",
                )
                self.assertIn("do not call", chunk.lower())


class TheSenzingFactCarriesItsProvenance(unittest.TestCase):
    """INV-080: the disclosed-relationship feature family is the MCP server's fact, not the
    plugin's, and not the spec's — it was re-confirmed the day this shipped."""

    def test_the_feature_family_is_attributed_to_the_entity_specification(self):
        chunk = flat(text())
        self.assertIn("Senzing Entity Specification", chunk)
        self.assertIn("Feature: REL_ANCHOR", chunk)
        self.assertIn("Feature: REL_POINTER", chunk)

    def test_the_attribute_names_are_the_ones_the_specification_defines(self):
        chunk = flat(text())
        for attribute in (
            "REL_ANCHOR_DOMAIN", "REL_ANCHOR_KEY",
            "REL_POINTER_DOMAIN", "REL_POINTER_KEY", "REL_POINTER_ROLE",
        ):
            with self.subTest(attribute=attribute):
                self.assertIn(attribute, chunk)

    def test_the_lookup_that_established_it_is_named_with_its_server_version(self):
        chunk = flat(text())
        self.assertRegex(chunk, ROUTE_DATA_MAPPING)
        self.assertRegex(chunk, r"MCP server 1\.\d+\.\d+")


class ThePluginNeverRepairsTheData(unittest.TestCase):
    def test_the_prohibition_is_stated_where_the_data_is_recommended(self):
        chunk = flat(text())
        self.assertIn("Never re-slice, repair, or vendor this data", chunk)
        self.assertIn("INV-173", chunk)

    def test_the_fix_is_routed_to_the_repository_that_owns_the_data(self):
        chunk = flat(text())
        self.assertIn(f"The fix belongs in `{CATALOG}`", chunk)

    def test_no_sample_data_is_vendored_into_this_repository(self):
        """The check the prose cannot make: a later 'helpful' commit adding a fixed copy."""
        vendored = [
            p for p in REPO_ROOT.rglob("*.csv")
            if ".git" not in p.parts and "node_modules" not in p.parts
        ]
        self.assertEqual(
            [], vendored, f"sample data must not be copied into this repo: {vendored}"
        )


if __name__ == "__main__":
    unittest.main()
