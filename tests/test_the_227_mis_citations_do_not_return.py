"""The seven sites #227 re-cited keep the invariant that governs them, and two correct ones stay.

`/production-readiness-audit` (2026-09-28, forward invariant sweep) found rules citing an
invariant whose subject is not the claim beside it. Each ID resolves, so `citations.py verify`
and `conformance.py rules` both read the line as covered; only reading the invariant shows the
citation is wrong. #227 swapped them:

| Site | Rule | Was | Now |
|---|---|---|---|
| `invariant_manifest.py` docstring, `status` | prose is not read as supersession evidence | INV-311 | INV-313 |
| `invariant_manifest.py` docstring, `partly_superseded_by` | a partial supersession is not a third state | INV-311 | INV-313 |
| `invariant_manifest.py` `partly_superseded_by` comment | kept separate from `superseded_by` | INV-311 | INV-313 |
| `phaseB-load-first-source.md` first-source line | a statement, not a 👉 question | INV-012 | INV-225 |
| `phaseD-validation.md` how-state audit, No finding | never "no finding" unless N equals M | INV-115 | INV-163 |
| `phaseD-validation.md` how-state audit, Could not measure | never collapse a partial run | INV-115 | INV-163 |
| `phaseD-validation.md` how-state audit, record it | including zero: "0 unsettled" | INV-115 | INV-265 |

INV-313's own text says INV-311 "is NOT the governing rule here"; INV-012 is point of view and
output suppression, while a step with no 👉 being non-yielding is INV-225; INV-115 is the
look-up-the-response-schema rule, not the rule that an unrun check never reads as clean
(INV-163) or that an absent result never reads as a clean one (INV-265).

⚠️ **Site-anchored, never a repository-wide phrase scan.** Each row finds its rule by a phrase
unique to that rule, with the citation's slot captured beside it, so no other citation anywhere
can trip it. The same IDs are correct elsewhere, and two of them sit in these very files:
`invariant_manifest.py`'s "The prose stays the source of truth" is INV-311's subject, and the
audit's "Dump ONE `how_entity` response" is INV-115's. Those are pinned here too, so a sweep that
"finishes" #227 by replacing every INV-311 or INV-115 in the file fails as well.

⚠️ **A site whose anchor is gone is a failure, not a pass (INV-265).** A reworded rule leaves
nothing to match, and a guard that matched nothing would pass while guarding nothing; the message
says to re-anchor the row on the rule's new wording. `MisCitationNegativeControls` shows each row
fails on the citation it replaced.

Stdlib only; nothing under `plugins/` is imported (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PY = ".claude/skills/review-invariants/invariant_manifest.py"
MODULE_06 = "plugins/senzing-bootcamp/skills/module-06-data-processing/"
PHASE_B = MODULE_06 + "phaseB-load-first-source.md"
PHASE_D = MODULE_06 + "phaseD-validation.md"

#: The captured citation slot. Every pattern below has exactly one.
ID = r"\(INV-(\d{3})\)"

#: (file, pattern anchoring the rule with its citation slot, the id it replaced, the id it cites)
RECITED = [
    (MANIFEST_PY,
     r"every other entry is `active`\. ⛔ \*\*" + ID + r"\*\* Prose is \*\*not\*\* read",
     "INV-311", "INV-313"),
    (MANIFEST_PY,
     r"bullet\. ⛔ \*\*" + ID + r"\*\* Such an entry stays `active`",
     "INV-311", "INV-313"),
    (MANIFEST_PY,
     r"# ⛔ \*\*" + ID + r" \(#143\) Separate from `superseded_by`",
     "INV-311", "INV-313"),
    (PHASE_B,
     r"This is a statement, not a 👉 question " + ID + r"\.",
     "INV-012", "INV-225"),
    (PHASE_D,
     ID + r' Never report "no finding" unless N equals M',
     "INV-115", "INV-163"),
    (PHASE_D,
     r'Never collapse a partial run into "no finding" ' + ID,
     "INV-115", "INV-163"),
    (PHASE_D,
     ID + r' including zero: write "0 unsettled" rather than omitting the section',
     "INV-115", "INV-265"),
]

#: (file, pattern, the id it must keep) — correct citations of the same ids, in the same files.
KEPT = [
    (MANIFEST_PY, r"⚠️ \*\*" + ID + r" The prose stays the source of truth\.", "INV-311"),
    (PHASE_D, r"⛔ \*\*" + ID + r" Dump ONE `how_entity` response", "INV-115"),
]


def flat(text):
    """Collapse whitespace so an anchor survives the prose being re-wrapped."""
    return " ".join(text.split())


def read(rel):
    return flat((REPO_ROOT / rel).read_text(encoding="utf-8"))


def cited(text, pattern):
    """The ids cited in the slot of every match of `pattern` in `text`."""
    return ["INV-" + m.group(1) for m in re.finditer(pattern, text)]


def problems(texts, rows):
    """One line per row whose rule is not found exactly once citing the id it must cite."""
    out = []
    for rel, pattern, *ids in rows:
        want = ids[-1]
        was = ids[0] if len(ids) == 2 else None
        found = cited(texts[rel], pattern)
        if len(found) != 1:
            out.append("%s: rule anchor /%s/ matched %d times, expected once; re-anchor this "
                       "row on the rule's current wording rather than deleting it"
                       % (rel, pattern, len(found)))
        elif found[0] == was:
            out.append("%s: /%s/ cites %s again, the mis-citation #227 corrected; it cites %s"
                       % (rel, pattern, was, want))
        elif found[0] != want:
            out.append("%s: /%s/ cites %s; it must cite %s" % (rel, pattern, found[0], want))
    return out


def all_texts():
    return {rel: read(rel) for rel in {row[0] for row in RECITED + KEPT}}


class TheRecitedSitesKeepTheirInvariant(unittest.TestCase):
    def setUp(self):
        self.texts = all_texts()

    def test_no_corrected_mis_citation_has_returned(self):
        self.assertEqual([], problems(self.texts, RECITED))

    def test_the_correct_citations_of_the_same_ids_survive(self):
        self.assertEqual([], problems(self.texts, KEPT))


class MisCitationNegativeControls(unittest.TestCase):
    """Each row fails on the citation #227 replaced, and on its rule's anchor going missing."""

    def setUp(self):
        self.texts = all_texts()

    def _mutated(self, rel, old, new):
        self.assertIn(old, self.texts[rel], "negative control is stale: %r is gone" % old)
        texts = dict(self.texts)
        texts[rel] = texts[rel].replace(old, new, 1)
        return texts

    def test_each_old_citation_is_caught(self):
        for row in RECITED:
            rel, pattern, was, want = row
            with self.subTest(rel=rel, pattern=pattern):
                match = re.search(pattern, self.texts[rel])
                self.assertIsNotNone(match)
                reverted = match.group(0).replace("(%s)" % want, "(%s)" % was, 1)
                texts = self._mutated(rel, match.group(0), reverted)
                found = problems(texts, [row])
                self.assertEqual(1, len(found))
                self.assertIn("mis-citation #227 corrected", found[0])

    def test_a_swept_kept_citation_is_caught(self):
        for row in KEPT:
            rel, pattern, keep = row
            with self.subTest(rel=rel, pattern=pattern):
                match = re.search(pattern, self.texts[rel])
                self.assertIsNotNone(match)
                # Swept to the id the mechanical "fix" would write; a registered id, so the
                # control does not cite an invariant that does not exist.
                other = {"INV-311": "INV-313", "INV-115": "INV-163"}[keep]
                swept = match.group(0).replace("(%s)" % keep, "(%s)" % other, 1)
                self.assertTrue(problems(self._mutated(rel, match.group(0), swept), [row]))

    def test_a_missing_anchor_is_a_failure_not_a_pass(self):
        rel, pattern, _was, _want = RECITED[3]
        texts = self._mutated(rel, "This is a statement, not a 👉 question",
                              "This is a statement")
        self.assertIn("matched 0 times", problems(texts, [RECITED[3]])[0])


if __name__ == "__main__":
    unittest.main()
