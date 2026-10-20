"""The four clauses #690 re-cited keep the invariant that governs them, and the siblings stay.

Enforces **INV-396**, registered by the maintainer 2026-10-20: a clause's citation names the
invariant whose registered statement makes the claim, and a clause making more than one claim
cites each. ⚠️ This file is a SITE PIN, not class coverage: it holds the clauses one run
corrected and **cannot** establish that no other clause in the repository cites the wrong rule.
A corpus-wide guard was built and abandoned on measurement (#690); see INV-396's own text.

`/production-readiness-audit` (2026-10-16, sweep A — reverse invariant contract) found four
clauses citing a neighboring invariant where the governing one is registered and is cited at
every sibling site. Each id resolves, so `citations.py verify` and `conformance.py rules` both
read the line as covered; only reading the invariant's registered text shows the citation is
wrong. #690 moved them — citations only, no registered text touched:

| Site | Clause | Was | Now |
|---|---|---|---|
| `feedback-to-issues/SKILL.md` guardrail | the `owner-checked:` requirement on an issue | INV-194 | INV-213 |
| `scripts/feedback-capture.py` docstring | feedback, notes and verbosity taken at any time | INV-010 | INV-010 / INV-254 / INV-011 |
| `hooks/README.md` hook table | the same three, as the row's Gate | INV-010 | INV-010 / INV-254 / INV-011 |
| `phaseD-validation.md` reversed-decision append | "never blocking" | INV-012 | INV-012 silent, INV-373 non-blocking |
| `ground-rules.md` build-and-run section | POSIX shell and PowerShell alike | INV-002 | INV-001 |

INV-213 registers the `owner-checked:` requirement on an input to implementation verbatim,
while INV-194 governs the reasoning beside it (an empty field in one tool is not evidence the
server lacks the fact) and says nothing about the issue body's field; INV-010 is feedback
alone, the notes half is INV-254 and the verbosity half INV-011; INV-012 is point of view and
output suppression, while the reversed-decision append's non-blocking clause is INV-373; and
INV-002 is language agnosticism, while a command running unchanged in a POSIX shell and in
PowerShell is platform, which is INV-001.

⚠️ **Site-anchored, and it claims nothing wider.** Each row finds its clause by a phrase unique
to that clause, with the citations captured inside the match, so no other citation anywhere can
trip it. The same ids are correct elsewhere — several in these very files — and those sites are
pinned below too, so a sweep that "finishes" #690 by replacing every INV-012 or INV-002 in a
file fails as well. ⛔ **(INV-246) This is a regression pin, NOT coverage of the defect class.**
Read the next block before treating a green run here as the class being guarded.

⛔ **(INV-246) The repository-wide version of this check was measured and NOT built, and the
measurement is the reason.** The issue proposed it: for a small set of high-traffic
one-sentence invariants, assert that a citing clause's subject words overlap the invariant's
own. It was derived and run against the pre-fix tree, with no hand-written id list anywhere:

- **The invariant set, derived.** Each registered invariant's *statement* is its text with every
  trailing balanced parenthetical note stripped; an invariant joins the set when that statement
  is at most 160 characters. That is a cliff in the data, not a knob: 47 invariants land at or
  below it and the next one is at 161. The set holds INV-001, INV-002, INV-010, INV-011 and
  INV-012, the five the issue names.
- **The subject words, derived.** A statement's words of four letters or more, lightly stemmed,
  keeping only those appearing in exactly one statement in the set — so "bootcamper", "module"
  and "must" fall out on their own and no stopword list is written.
- **The sites, derived.** Every sentence of every `.md` and `.py` file under `plugins/`, read
  through `_corpus.corpus_files` and `_wrapped_text.collapsed_blocks` so a clause wrapped across
  lines is still one sentence (INV-346): 64 files, 18,964 sentences, of which **252** cite a
  member of the set.
- **What it reported.** **196** of those 252 sentences carry no subject word of the id they
  cite. All four in-scope sites are among them — `hooks/README.md:30`,
  `scripts/feedback-capture.py:7`, `ground-rules.md:869` and `phaseD-validation.md:558` — so the
  negative control does fire. **The other 192 are correct prose.** INV-012 fails at 64 of its 68
  citing sentences and INV-002 at 25 of 26, because shipped text states these rules in its own
  words ("No banners, no 👉 question, no announcement (INV-012)") far more often than it echoes
  the registered wording.
- **Every narrowing tried made it worse, not better.** Widening the window from the sentence to
  the Markdown block drops it to 142 flags but *loses* `phaseD-validation.md:558`, which passes
  by accident on the word "important" elsewhere in its block — a wider read is quieter and less
  true. Running it the other way round, flagging a sentence that carries a sibling invariant's
  distinctive word without citing it, gives 360 flags raw; filtering that word to one appearing
  in at most 80 corpus sentences gives 26, of which 2 are real; at 40 it gives 9, of which none
  is real. No setting separates the four from the prose.

So the only way to make the derived guard green is to exempt the ~192 correct sites one by one,
and that exemption list is the hardcoded site list INV-246 exists to forbid, wearing a different
hat. A guard like that is worse than none, because it reads as coverage. Acceptance criterion 3
allows recording why it was not built, and this is that record.

⚠️ **Two of the five rows are outside what the derived scan could have seen in any case**, which
is worth stating so the scope is not re-derived: the `feedback-to-issues/SKILL.md` rows sit under
`.claude/`, the maintainer surface, not in the `plugins/` corpus — and INV-194 and INV-213, whose
statements run 1,761 and 3,274 characters, are nowhere near the one-sentence set.

Stdlib only; nothing under `plugins/` is imported (INV-108). Each file is read with its
whitespace collapsed, so an anchor survives the prose being re-wrapped (INV-346).

Source issue: #690.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"

FEEDBACK_TO_ISSUES = ".claude/skills/feedback-to-issues/SKILL.md"
ONBOARDING = "plugins/senzing-bootcamp/skills/bootcamp-onboarding/"
GROUND_RULES = ONBOARDING + "ground-rules.md"
FEEDBACK_MD = ONBOARDING + "feedback.md"
NOTES_MD = ONBOARDING + "notes.md"
HOOKS_README = "plugins/senzing-bootcamp/hooks/README.md"
CAPTURE_PY = "plugins/senzing-bootcamp/scripts/feedback-capture.py"
PHASE_D = "plugins/senzing-bootcamp/skills/module-06-data-processing/phaseD-validation.md"
DATABASE_BACKUP = "plugins/senzing-bootcamp/skills/graduation/database-backup.md"

#: A citation slot inside an anchor. Every id the match holds is read back out of it.
SLOT = r"INV-\d{3}"
#: Any id, for reading the ids back out of a match.
ID = re.compile(r"INV-\d{3}")

#: (file, anchor whose match holds the citations, ids it MUST cite, ids it must NOT cite).
#: `must_not` is the mis-citation #690 corrected, so a revert is caught by name rather than by
#: the bare absence of the right id.
RECITED = [
    (FEEDBACK_TO_ISSUES,
     r"the `MCP re-check` line MUST also carry `owner-checked: [^`]*` "
     r"\(\*\*" + SLOT + r"\*\*; see `issue-template\.md`\)",
     {"INV-213"}, {"INV-194"}),
    (CAPTURE_PY,
     r"are taken at any time from onboarding on — feedback \(" + SLOT + r"\), "
     r"notes \(" + SLOT + r"\) and verbosity \(" + SLOT + r"\)",
     {"INV-010", "INV-254", "INV-011"}, set()),
    (HOOKS_README,
     r"Existence: feedback \(" + SLOT + r"\), notes \(" + SLOT + r"\) and verbosity changes "
     r"\(" + SLOT + r"\) are taken from onboarding on",
     {"INV-010", "INV-254", "INV-011"}, set()),
    (PHASE_D,
     r"No banner, no question \(" + SLOT + r"\), never blocking \(" + SLOT + r"\)",
     {"INV-012", "INV-373"}, set()),
    (GROUND_RULES,
     r"they run unchanged in a POSIX shell and in PowerShell \(" + SLOT + r"\)",
     {"INV-001"}, {"INV-002"}),
]

#: (file, anchor, ids it MUST keep) — the sibling sites that were already right, including
#: correct uses of the very ids the rows above moved away from.
KEPT = [
    # The reasoning sentence beside row 1 keeps INV-194: it is a different claim.
    (FEEDBACK_TO_ISSUES,
     r"no evidence for the negative \(\*\*" + SLOT + r"\*\*\):", {"INV-194"}),
    (FEEDBACK_TO_ISSUES,
     r"⛔ \*\*Carry the `owner-checked:` clause on any absence claim\*\* \(" + SLOT + r"\)",
     {"INV-213"}),
    # hooks/README.md cites INV-010 alone for feedback alone, two paragraphs above the row.
    (HOOKS_README,
     r"write project files and take feedback, so the three hooks that serve them gate on "
     r"existence on purpose, not on `bootcamp_active\(\)` \(" + SLOT + r", " + SLOT + r"\)",
     {"INV-227", "INV-010"}),
    # The two owning sites of the reversed-decision append already split silent from blocking.
    (FEEDBACK_MD,
     r"no line in the bootcamper-facing output \(" + SLOT + r"\)", {"INV-012"}),
    (FEEDBACK_MD, r"⛔ \*\*\(" + SLOT + r"\) Never blocks\.\*\*", {"INV-373"}),
    (GROUND_RULES,
     r"No banners, no 👉 question, no announcement \(" + SLOT + r"\)", {"INV-012"}),
    (GROUND_RULES, r"\*\*\(" + SLOT + r"\) Non-blocking\.\*\*", {"INV-373"}),
    # INV-002 is still right in the same file, for a language claim.
    (GROUND_RULES,
     r"The framing is ownership, not a Python idiom \(" + SLOT + r"\)", {"INV-002"}),
    # INV-001 is already the platform id the repository reaches for, in the same voice.
    (DATABASE_BACKUP,
     r"⛔ \*\*\(" + SLOT + r", " + SLOT + r"\) Never write the dump with a `>` redirection\*\*",
     {"INV-166", "INV-001"}),
    (NOTES_MD,
     r"onboarding, any module, or graduation \(" + SLOT + r"\)", {"INV-254"}),
]


def flat(text):
    """Collapse whitespace so an anchor survives the prose being re-wrapped (INV-346)."""
    return " ".join(text.split())


def read(rel):
    return flat((REPO_ROOT / rel).read_text(encoding="utf-8"))


def problems(texts, rows):
    """One line per row whose clause is missing, duplicated, or citing the wrong invariant."""
    out = []
    for rel, pattern, *ids in rows:
        must = ids[0]
        must_not = ids[1] if len(ids) == 2 else set()
        found = re.findall(pattern, texts[rel])
        if len(found) != 1:
            out.append("%s: clause anchor /%s/ matched %d times, expected once; re-anchor this "
                       "row on the clause's current wording rather than deleting it"
                       % (rel, pattern, len(found)))
            continue
        cited = set(ID.findall(re.search(pattern, texts[rel]).group(0)))
        back = sorted(cited & must_not)
        if back:
            out.append("%s: /%s/ cites %s again, the mis-citation #690 corrected; it cites %s"
                       % (rel, pattern, ", ".join(back), ", ".join(sorted(must))))
        missing = sorted(must - cited)
        if missing:
            out.append("%s: /%s/ does not cite %s; a clause that makes two claims cites both "
                       "invariants, never the dominant one"
                       % (rel, pattern, ", ".join(missing)))
    return out


def all_texts():
    return {rel: read(rel) for rel in {row[0] for row in RECITED + KEPT}}


class TheRecitedClausesKeepTheirInvariant(unittest.TestCase):
    def setUp(self):
        self.texts = all_texts()

    def test_no_corrected_mis_citation_has_returned(self):
        self.assertEqual([], problems(self.texts, RECITED))

    def test_the_correct_citations_of_the_same_ids_survive(self):
        self.assertEqual([], problems(self.texts, KEPT))

    def test_every_id_these_rows_name_is_registered(self):
        """⚠️ A pin that names an unregistered id would send a reader nowhere.

        The registered set is read from `specs/INVARIANTS.md`, so a row naming a number nobody
        minted fails here rather than passing quietly and turning `citations.py verify` red.
        """
        registered = set(re.findall(r"^- \*\*(INV-\d{3})\*\* — ",
                                    INVARIANTS.read_text(encoding="utf-8"), re.MULTILINE))
        self.assertTrue(registered, "no invariant parsed out of specs/INVARIANTS.md")
        named = set()
        for row in RECITED + KEPT:
            for ids in row[2:]:
                named |= ids
        self.assertEqual(set(), named - registered,
                         "these rows name ids that are not registered: %s"
                         % ", ".join(sorted(named - registered)))


class MisCitationNegativeControls(unittest.TestCase):
    """Each row fails on the citation #690 replaced, and on its clause's anchor going missing."""

    def setUp(self):
        self.texts = all_texts()

    def _mutated(self, rel, old, new):
        self.assertIn(old, self.texts[rel], "negative control is stale: %r is gone" % old)
        texts = dict(self.texts)
        texts[rel] = texts[rel].replace(old, new, 1)
        return texts

    def test_each_corrected_citation_is_caught_when_it_reverts(self):
        for rel, pattern, must, must_not in RECITED:
            with self.subTest(rel=rel, pattern=pattern):
                match = re.search(pattern, self.texts[rel]).group(0)
                # Revert to the id #690 replaced where there was one, and otherwise collapse the
                # extra citations back onto the one id the clause used to carry.
                wrong = sorted(must_not)[0] if must_not else sorted(must)[0]
                reverted = match
                for want in sorted(must):
                    if want != wrong:
                        reverted = reverted.replace(want, wrong)
                self.assertNotEqual(match, reverted, "control would change nothing")
                found = problems(self._mutated(rel, match, reverted), [(rel, pattern, must,
                                                                        must_not)])
                self.assertTrue(found, "reverting %s to %s went unreported" % (rel, wrong))

    def test_a_swept_kept_citation_is_caught(self):
        for rel, pattern, must in KEPT:
            with self.subTest(rel=rel, pattern=pattern):
                match = re.search(pattern, self.texts[rel]).group(0)
                keep = sorted(must)[0]
                # Swept to a registered id the mechanical "fix" would write, so the control never
                # cites an invariant that does not exist.
                other = "INV-012" if keep != "INV-012" else "INV-373"
                swept = match.replace(keep, other, 1)
                self.assertTrue(problems(self._mutated(rel, match, swept), [(rel, pattern, must)]))

    def test_a_missing_anchor_is_a_failure_not_a_pass(self):
        rel, pattern, must, must_not = RECITED[3]
        texts = self._mutated(rel, "No banner, no question (INV-012), never blocking (INV-373)",
                              "No banner, no question")
        self.assertIn("matched 0 times", problems(texts, [(rel, pattern, must, must_not)])[0])


if __name__ == "__main__":
    unittest.main()
