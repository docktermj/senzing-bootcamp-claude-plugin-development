"""INV-048 is the recap PDF's invariant, so no shipped file may credit it for a generic
"never blocks".

#607 ruled it once and applied it twice: INV-048 governs the recap PDF only, and an `(INV-048)`
attached to a generic never-blocks clause is to be read as **no citation**. The ruling is
registered in INV-122's and INV-335's 2026-10-15 notes. Roughly two dozen shipped sites still
credited INV-048 for a never-blocks clause about something else entirely -- a screenshot capture,
a formatting pass, a database backup, a video render, a checkpoint read -- so the ruling that
exists to stop a borrowed citation spreading was itself applied at two of the sites it binds, and
every remaining site was a model for the next one. #685 finished it and added this guard.

⛔ **(INV-246) The site set is derived by SCANNING the shipped subtree, never from a list of
paths.** A hardcoded list would encode the author's belief about where INV-048 is cited, and that
belief is exactly what is wrong when a rule is applied incompletely. This matters here beyond the
general case: #685's own issue listed the sites by a line grep, which included one line whose
clause is correctly about the recap PDF and omitted two whose clause is not -- and the audit that
wrote the list had already missed `graduation/SKILL.md`'s shortfall remedy because the sentence
wraps. A derived guard sees a site nobody thought of, including one added later.

⚠️ **Wrap-aware (INV-346).** The clause is a sentence, and Markdown wraps a sentence wherever the
column runs out, so the scan reads through ``_wrapped_text.collapsed_blocks`` and reports the line
each match started on. A line-at-a-time read of the same corpus is what missed the remedy site.

**The rule, stated as this file enforces it:** in a shipped file, a sentence that cites `INV-048`
**and states a never-blocks property** MUST name the recap. The never-blocks vocabulary is the word
"block" and its forms -- the ruling is about a *never-blocks* clause, and a wider vocabulary
("continues", "proceed") reports correct prose (INV-282). The other citations #685 corrected --
"never raises", "never fatal", "the step continues" -- are pinned by the guards that already own
those sites.

⚠️ **Scope: the shipped plugin (`plugins/`), stated with its reason (INV-246).** The acceptance
criterion is about a *shipped* file. A test's own prose explains citations rather than making them,
and `tests/test_invariant_crossreferences.py` legitimately discusses INV-048's non-blocking sense in
so many words; sweeping it here would report correct content.

⛔ **Every negative control runs the SAME check over a mutated copy of the shipped text
(INV-265)**, putting back the exact pre-#685 wording, so each control measures the check rather
than a second implementation of it. The scan also asserts it read something: an empty corpus would
otherwise pass silently.

⚠️ **What this cannot establish:** that a citation left in place is *correct*, only that a
never-blocks clause crediting INV-048 names the recap. It says nothing about `specs/INVARIANTS.md`,
whose own text still carries the same borrowed credit in several entries -- those are
`PROPOSED AMENDMENT` blocks in `specs/IMPLEMENTED.md` for `/review-invariants` to decide, because
only that command may write to the registry (INV-365).

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issue: #685 (completing #607).

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files  # noqa: E402
from _wrapped_text import collapsed_blocks, line_of  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIPPED = "plugins"

#: The sentence a citation sits in, approximated as the run between sentence terminators.
CITED_SENTENCE = re.compile(r"[^.!?]*INV-048[^.!?]*[.!?]?")
#: The never-blocks vocabulary: the word "block" and its forms, and nothing wider (see above).
NEVER_BLOCKS = re.compile(r"(?i)\b(?:un)?block(?:s|ed|ing|age)?\b")
#: Naming the recap. INV-048 is `docs/bootcamp_recap.pdf`'s invariant, so its clause says so.
NAMES_THE_RECAP = re.compile(r"(?i)recap")


def inv048_problems(text):
    """Every never-blocks clause in ``text`` that credits INV-048 without naming the recap.

    A pure function over one file's text, so each negative control runs this same check over a
    mutated copy (INV-265). Each problem reads ``line N: <the offending sentence>``.
    """
    problems = []
    for flat, origin in collapsed_blocks(text):
        for match in CITED_SENTENCE.finditer(flat):
            sentence = match.group(0).strip()
            if "INV-048" not in sentence:
                continue
            if not NEVER_BLOCKS.search(sentence):
                continue
            if NAMES_THE_RECAP.search(sentence):
                continue
            problems.append(
                "line %d credits INV-048 for a never-blocks clause that does not name the "
                "recap: %s" % (line_of(origin, match.start()), sentence))
    return problems


def shipped_texts():
    """``(repo-relative path, text)`` for every readable shipped file, by SCANNING (INV-246).

    Undecodable files are the plugin's binary assets; they carry no prose and are skipped.
    """
    for path in corpus_files(SHIPPED, root=REPO_ROOT):
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield Path(path).relative_to(REPO_ROOT).as_posix(), text


def mutate(test, text, old, new):
    """Replace ``old`` once; fail the control if the anchor text has gone."""
    test.assertIn(old, text, "the control's anchor text is gone; update the control")
    return text.replace(old, new, 1)


def shipped(relative):
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


#: The pre-#685 wording of every never-blocks clause this guard reports, one per corrected site,
#: as ``(path, shipped now, as it read before)``. The controls put each back, one at a time.
PRE_685 = (
    ("plugins/senzing-bootcamp/scripts/capture_screenshots.py",
     "never blocking graduation (INV-122).",
     "never blocking graduation (INV-048)."),
    ("plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py",
     "a formatting issue must never\nblock graduation); 1 =",
     "a formatting issue must never\nblock graduation, INV-048); 1 ="),
    ("plugins/senzing-bootcamp/scripts/normalize_docs_markdown.py",
     "# Always 0: a formatting pass must never block graduation.",
     "# Always 0: a formatting pass must never block graduation (INV-048)."),
    ("plugins/senzing-bootcamp/skills/graduation/database-backup.md",
     "non-blocking (INV-094).",
     "non-blocking (INV-048)."),
    ("plugins/senzing-bootcamp/skills/bootcamp-onboarding/module-completion.md",
     "**Non-blocking and Bootcamper-invisible (INV-012).**",
     "**Non-blocking and Bootcamper-invisible (INV-012/INV-048).**"),
    ("plugins/senzing-bootcamp/skills/module-03b-truthset-visualization/phase1-visualization.md",
     "⛔ **(INV-378) It never blocks the module.**",
     "⛔ **(INV-048) It never blocks the module.**"),
    ("plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase2-data-mapping.md",
     "an iterate-forever loop or a blocked module (INV-173).",
     "an iterate-forever loop or a blocked module (INV-048/INV-173)."),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "— nothing here blocks.",
     "— nothing here blocks (INV-048)."),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "best-effort and each non-blocking (INV-129)",
     "best-effort and each non-blocking (INV-048)"),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "never block graduation on a verification step\n(INV-129, INV-052/INV-066).",
     "never block graduation on a verification step\n(INV-048, INV-052/INV-066)."),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "still never blocks graduation (INV-163, INV-052/INV-066)",
     "still never blocks graduation (INV-048, INV-052/INV-066)"),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "⛔ **(INV-340) The video never blocks graduation.**",
     "⛔ **(INV-340) The video never blocks graduation (INV-048).**"),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "⛔ **(INV-340) This guidance is a statement, never a question, and it never blocks "
     "graduation.**",
     "⛔ **(INV-048, INV-340) This guidance is a statement, never a question, and it never "
     "blocks graduation.**"),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "**Non-blocking, like every graduation step**: if a document is absent",
     "**Non-blocking, like every graduation step** (INV-048): if a document is absent"),
    ("plugins/senzing-bootcamp/skills/graduation/SKILL.md",
     "   is **non-blocking**, so either can legitimately be absent: an absent or refused PDF "
     "is simply not\n   named, by item 1's rule that you never announce an artifact you have "
     "not confirmed exists. This",
     "   is **non-blocking**, so either can legitimately be absent: an absent or refused PDF "
     "is simply not\n   named, by item 1's rule that you never announce an artifact you have "
     "not confirmed exists\n   (INV-048). This"),
)


class NoShippedFileCreditsInv048ForAGenericNeverBlocks(unittest.TestCase):
    """The whole shipped subtree, derived by scanning (INV-246)."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = list(shipped_texts())

    def test_every_shipped_file_is_clean(self):
        for relative, text in self.corpus:
            if "INV-048" not in text:
                continue
            with self.subTest(site=relative):
                self.assertEqual(
                    [], inv048_problems(text),
                    "%s credits INV-048, which governs the recap PDF, for a never-blocks clause "
                    "about something else. Drop it where the property is the enclosing rule's "
                    "own clause, or cite the invariant that states it for that artifact "
                    "(INV-094 the revisit/resume bundle, INV-340 the video, INV-122 capture, "
                    "INV-163 a check that cannot run)." % relative)

    def test_the_scan_read_the_corpus_it_claims_to(self):
        """⛔ (INV-265) An empty match set is an unrun check, never a pass."""
        self.assertGreater(len(self.corpus), 50,
                           "the shipped subtree scan found almost no files; it is not scanning")
        citing = [relative for relative, text in self.corpus if "INV-048" in text]
        self.assertGreaterEqual(
            len(citing), 3,
            "the scan found fewer than three shipped files citing INV-048, so a clean result "
            "measures nothing; the derivation is broken")
        self.assertIn("plugins/senzing-bootcamp/scripts/generate_recap_pdf.py", citing,
                      "the recap generator is not in the scanned set, so the scan is not "
                      "reaching the shipped scripts")

    def test_the_citations_left_in_place_are_the_recaps_own(self):
        """Every surviving never-blocks credit names the recap; this records how many there are."""
        kept = [(relative, sentence)
                for relative, text in self.corpus
                for flat, _ in collapsed_blocks(text)
                for sentence in [m.group(0).strip() for m in CITED_SENTENCE.finditer(flat)]
                if "INV-048" in sentence and NEVER_BLOCKS.search(sentence)]
        self.assertTrue(kept, "no never-blocks INV-048 clause survives anywhere, so the check "
                              "above has nothing to be right about")
        for relative, sentence in kept:
            with self.subTest(site=relative):
                self.assertRegex(sentence, NAMES_THE_RECAP)


class TheControlsPutEachCorrectedSiteBack(unittest.TestCase):
    """⛔ (INV-265) Each control runs ``inv048_problems`` over the shipped text, mutated."""

    def test_the_shipped_text_of_each_corrected_site_is_clean(self):
        for relative, now, _before in PRE_685:
            with self.subTest(site=relative, clause=now[:40]):
                self.assertEqual([], inv048_problems(shipped(relative)))

    def test_each_pre_685_wording_is_reported(self):
        for relative, now, before in PRE_685:
            with self.subTest(site=relative, clause=before[:40]):
                mutated = mutate(self, shipped(relative), now, before)
                self.assertTrue(
                    inv048_problems(mutated),
                    "putting %s's pre-#685 wording back is not reported, so the check does not "
                    "cover the defect it was written for" % relative)

    def test_the_whole_pre_685_corpus_is_reported_at_every_site(self):
        """The negative control the issue asks for: the text as it read before this change."""
        reported = set()
        for relative, now, before in PRE_685:
            mutated = mutate(self, shipped(relative), now, before)
            if inv048_problems(mutated):
                reported.add(relative)
        self.assertEqual(
            {relative for relative, _now, _before in PRE_685}, reported,
            "the pre-#685 text of some corrected file is not reported by this check")

    def test_a_recap_clause_is_not_reported(self):
        """Scoped with its reason (INV-246): the recap's own never-blocks clauses are correct."""
        generator = ("plugins/senzing-bootcamp/scripts/generate_recap_pdf.py")
        self.assertEqual([], inv048_problems(shipped(generator)))
        self.assertIn("ships the recap PDF", shipped(generator),
                      "the generator no longer names the recap on its non-blocking clause, so "
                      "this check passes for the wrong reason")

    def test_a_clause_that_stops_naming_the_recap_is_reported(self):
        """⛔ The check must fail on a correct citation whose clause loses its subject."""
        mutated = mutate(self, shipped("plugins/senzing-bootcamp/scripts/generate_recap_pdf.py"),
                         "still ships the recap\n    PDF (INV-048/INV-052/INV-066)",
                         "still ships the\n    PDF (INV-048/INV-052/INV-066)")
        self.assertTrue(inv048_problems(mutated))


if __name__ == "__main__":
    unittest.main()
