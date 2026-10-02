"""Both of `model-selection.md`'s tables cover every shipped skill, and they agree.

The file carries two model/effort tables cut differently — one by skill (Workload / Best value /
Rationale) and one by stage (Recommended / CLI commands). INV-140 binds the **per-stage** table and
was satisfied, so the per-skill table could sit one row short without contradicting any invariant:
`bootcamp-preparation` shipped as a skill (INV-075 relocated the verbosity and language questions
into it), gained its per-stage row and a mention in INV-140's own parenthetical, and was never added
to the per-skill table.

That table is the only record of *why* a stage gets its model. Its absence is invisible until a
re-assessment tries to re-read the reasoning and finds none — and the file's own header says the last
re-assessment happened precisely because rows "had gone stale" unread.

So this guard checks the property no invariant does: every skill directory appears in **both**
tables. It compares against the filesystem rather than a pinned list, so adding a skill fails until
both tables know about it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODEL_SELECTION = REPO_ROOT / "plugins" / "senzing-bootcamp" / "docs" / "model-selection.md"

#: A per-skill row leads with the skill's directory name in backticks.
SKILL_ROW = re.compile(r"^\|\s*`([a-z0-9][a-z0-9-]*)`\s*\|", re.M)
#: A per-stage row leads with a prose stage name and carries a `/model` CLI command.
STAGE_ROW = re.compile(r"^\|\s*([^|`][^|]*?)\s*\|[^|]*\|[^|]*`/model\s", re.M)

#: Stage-table row name for each skill directory. The two tables are deliberately cut
#: differently — by file and by bootcamp stage — so the mapping is stated rather than derived.
SKILL_TO_STAGE = {
    "bootcamp-onboarding": "Onboarding",
    "bootcamp-preparation": "Bootcamp preparation",
    "module-00-entity-resolution-concepts": "Entity Resolution Concepts",
    "module-01-business-problem": "Discover the Business Problem",
    "module-02-sdk-setup": "SDK setup",
    "module-03-system-verification": "System verification",
    "module-03b-truthset-visualization": "Truth Set visualization",
    "module-04-data-collection": "Data collection",
    "module-05-data-quality-mapping": "Data Quality, Mapping, and Transformation",
    "module-06-data-processing": "Data processing",
    "module-07-query-visualize-discover": "Query, Visualize and Discover",
    "graduation": "Bootcamp graduation",
}


def shipped_skills():
    return sorted(p.name for p in SKILLS_DIR.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


def text():
    return MODEL_SELECTION.read_text(encoding="utf-8")


class BothTablesCoverEverySkill(unittest.TestCase):
    def test_the_scan_is_not_vacuous(self):
        skills = shipped_skills()
        self.assertGreaterEqual(len(skills), 10, "far fewer skills found than ship")
        self.assertTrue(SKILL_ROW.findall(text()), "no per-skill rows parsed")
        self.assertTrue(STAGE_ROW.findall(text()), "no per-stage rows parsed")

    def test_every_shipped_skill_has_a_per_skill_row(self):
        rows = set(SKILL_ROW.findall(text()))
        missing = [s for s in shipped_skills() if s not in rows]
        self.assertEqual(
            [], missing,
            "shipped skill(s) with no row in model-selection.md's per-skill table, so the "
            "reasoning behind their model choice is unrecorded and a re-assessment cannot "
            "re-read it: %s" % missing,
        )

    def test_every_shipped_skill_has_a_per_stage_row(self):
        """INV-140, checked against the filesystem rather than the invariant's own list."""
        rows = " | ".join(STAGE_ROW.findall(text()))
        missing = [s for s in shipped_skills()
                   if SKILL_TO_STAGE.get(s, s) not in rows]
        self.assertEqual(
            [], missing,
            "shipped skill(s) with no row in the per-stage table (INV-140 requires exactly one "
            "per stage): %s" % missing,
        )

    def test_the_mapping_covers_every_shipped_skill(self):
        """Otherwise a new skill silently falls back to matching on its directory name."""
        unmapped = [s for s in shipped_skills() if s not in SKILL_TO_STAGE]
        self.assertEqual([], unmapped,
                         "SKILL_TO_STAGE has no stage name for: %s — add it in the same edit "
                         "that adds the skill" % unmapped)

    def test_bootcamp_preparation_matches_the_stage_table_recommendation(self):
        """The two tables must not disagree about the same stage's recommendation."""
        flat = " ".join(text().split())
        self.assertRegex(flat, r"`bootcamp-preparation`[^|]*\|[^|]*\|\s*Sonnet 5\.5, medium\s*\|")
        self.assertRegex(flat, r"\| Bootcamp preparation \| Sonnet 5\.5, medium effort \|")


if __name__ == "__main__":
    unittest.main()
