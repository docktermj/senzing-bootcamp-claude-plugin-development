"""A rule restated in two shipped files must not carry two different authorities.

One rule stated in two places under two **disjoint** sets of invariant ids means at least
one of them is wrong — and it is invisible to every existing check, because both lines carry
an id: ``conformance.py rules`` and ``per-rule`` ask whether a rule cites *an* invariant, and
``citations.py verify`` proves the id *resolves*. Neither asks whether it is the *right* one.

Found this way on 2026-09-03: the macOS SIP / ``DYLD_*`` direct-child rule was stated in
``module-07-query-visualize-discover/phase1-query-visualize.md`` under **INV-179** — an
invariant entirely about SDK response flags — while its canonical statement in
``module-03b-truthset-visualization/visualization-api-reference.md`` cited **INV-001,
INV-002**. Ten INV-179 citations were wrong in total, of two kinds.

⛔ **What this guard does NOT establish, stated because its predecessor's over-claim is the
reason yesterday's audit had to retract a finding:**

- It sees a rule restated in **similar words**. Of the three sites in that macOS group it
  reports **one pair**; ``module-03b-truthset-visualization/phase1-visualization.md`` states
  the same rule differently enough to fall under the floor. Reading found the rest.
- It cannot see a citation that is wrong for any reason **other** than disagreeing with a near
  copy. The seven sites of the other kind — a no-fork rule cited to INV-179 instead of INV-183
  — are entirely out of its reach; nothing about them is duplicated.
- It compares **single lines** in shipped markdown only. A rule broken across a line break, or
  stated in a bundled script's comment, is invisible to it. **Line-scoped by design (#424):**
  the unit compared is one cited rule line, and ``FLOOR`` was measured over lines; comparing
  whitespace-collapsed blocks instead would hold paragraphs to a floor calibrated on lines, so
  a block unit needs its own re-measured floor, not this one.

So a green run means "no restated rule disagrees with its twin", never "every citation is
correct". The general near-duplicate scan this was narrowed from is **deliberately not** here:
at a 0.82 floor over all hard-rule lines it reports 18 pairs of which 15 are phase-header
boilerplate, and a guard with that precision trains its reader to skip it.

Stdlib only; shipped files are read as text, never imported from ``plugins/`` (INV-108).

Source spec: ``specs/inv-179-is-cited-as-a-state-it-once-rule-it-does-not-contain.md``.

Run:  python3 -m unittest discover -s tests
"""

import difflib
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")

#: A line is a candidate only if it states a rule AND names an authority for it.
MARKER = re.compile(r"⛔|🛑|\bMUST\b|\bNEVER\b|\bNever\b")
CITATION = re.compile(r"INV-\d+")

#: Similarity floor. Measured 2026-09-03 over the 201 cited rule lines then shipping:
#: 0.68 yields exactly one pair and no false positives. Lowering it pulls in the
#: phase-header boilerplate the module docstring describes.
FLOOR = 0.68

#: ⚠️ Legitimate disjoint pairs go here as two distinctive phrase fragments, NOT as line
#: numbers, which move with every edit above them. Empty today, and an addition needs the
#: reason on the entry: two statements of one rule under two authorities is the defect, so
#: an exemption is a claim that the two rules only LOOK alike.
EXEMPT_PAIRS = ()

#: A floor on the corpus so a broken extractor cannot pass this file vacuously. The count
#: was 201 when the guard was written; it grows with the plugin, so the assertion is a floor
#: rather than a pin.
MIN_CITED_RULES = 120


def cited_rule_lines():
    """[(relpath, lineno, {ids}, normalized, raw)] for every cited rule line shipped."""
    out = []
    for dirpath, _dirs, files in os.walk(SHIPPED):
        if "__pycache__" in dirpath or os.sep + "vendor" in dirpath:
            continue
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as handle:
                for lineno, line in enumerate(handle, 1):
                    ids = set(CITATION.findall(line))
                    if not ids or not MARKER.search(line):
                        continue
                    text = normalize(line)
                    if len(text.split()) < 7:
                        continue
                    out.append(
                        (os.path.relpath(path, REPO_ROOT), lineno, ids, text, line.strip())
                    )
    return out


def normalize(line):
    """The rule text with its citations and markup removed — what is compared."""
    text = CITATION.sub("", line)
    text = re.sub(r"[`*_⛔🛑⚠️👉→—–:;,.()\[\]{}\"'/]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def disagreeing_pairs(rows, floor=FLOOR):
    """Pairs of near-identical rules in different files whose citation sets are disjoint."""
    found = []
    for i in range(len(rows)):
        path_a, line_a, ids_a, text_a, raw_a = rows[i]
        for j in range(i + 1, len(rows)):
            path_b, line_b, ids_b, text_b, raw_b = rows[j]
            if path_a == path_b or ids_a & ids_b:
                continue
            if abs(len(text_a) - len(text_b)) > max(len(text_a), len(text_b)) * 0.4:
                continue
            if difflib.SequenceMatcher(None, text_a, text_b).ratio() < floor:
                continue
            if any(
                frag_a in raw_a and frag_b in raw_b or frag_a in raw_b and frag_b in raw_a
                for frag_a, frag_b in EXEMPT_PAIRS
            ):
                continue
            found.append(((path_a, line_a, ids_a, raw_a), (path_b, line_b, ids_b, raw_b)))
    return found


class TheScanCanSeeTheCorpus(unittest.TestCase):
    """A scan finding nothing would pass the class below without checking anything."""

    def test_the_corpus_is_not_empty(self):
        rows = cited_rule_lines()
        self.assertGreaterEqual(
            len(rows), MIN_CITED_RULES,
            "expected at least %d cited rule lines in shipped markdown, found %d. A drop "
            "this large means the extractor has stopped seeing them — check MARKER and "
            "CITATION before believing a green run." % (MIN_CITED_RULES, len(rows)),
        )

    def test_the_detector_reports_a_planted_disagreement(self):
        """The negative control, run in-process so it cannot rot out of sync with the code.

        Two files stating one rule under disjoint ids is exactly the shape; if this stops
        firing, the class below is green for the wrong reason.
        """
        rule = "the server must be started as a direct child of the shell that sourced it"
        planted = [
            ("a.md", 1, {"INV-179"}, normalize(rule), "⛔ **(INV-179) " + rule),
            ("b.md", 1, {"INV-001", "INV-002"}, normalize(rule), "⛔ **(INV-001, INV-002) " + rule),
            ("c.md", 1, {"INV-183"}, normalize("an unrelated rule about writing the recap"),
             "⛔ **(INV-183) an unrelated rule about writing the recap"),
        ]
        pairs = disagreeing_pairs(planted)
        self.assertEqual(
            1, len(pairs),
            "the detector must report the planted pair (and only it); got: %r" % (pairs,),
        )
        self.assertEqual({"a.md", "b.md"}, {pairs[0][0][0], pairs[0][1][0]})


#: INV-179's whole subject is a field an SDK response did not populate. Every citation of it
#: must therefore sit in a passage about flags — checked over a WINDOW rather than the line,
#: because a rule is routinely and correctly cited at its bullet head several lines up.
#: Line-scoped by design (#424): the anchor is the single token ``INV-179``, which cannot
#: wrap, and the window spans lines; every term below is one word or token, so no phrase in
#: it can be split by a line break.
FLAG_VOCABULARY = re.compile(
    r"\bflag|composite|SZ_[A-Z_]+|blank|absent|response_schemas|field\b", re.I
)
FLAG_WINDOW = 8


class EveryRemainingInv179CitationIsAboutFlags(unittest.TestCase):
    """The other half of the 2026-09-03 sweep: it must not have over-reached.

    Eleven INV-179 citations are correct and were left in place. This asserts the property
    that distinguishes them from the ten that were wrong — the passage is about flags — so a
    later pass can neither re-add a state-it-once citation to INV-179 nor quietly delete the
    correct ones and leave the guarantee unstated.

    ⚠️ **Recall measured against the defect it was written for: 6 of the 10 removed
    mis-citations, no false positives.** The four it misses are passages that mention "flag"
    or "field" incidentally — a JVM `-Djava.library.path` discussion, a license *field* branch
    — which is the cost of asking about a window instead of a line, and the line is worse: two
    of the eleven correct citations carry no flag vocabulary on the line itself. All eleven pass
    today. So this narrows where a wrong INV-179 citation can hide; it does not close it.
    """

    def test_each_citation_sits_in_a_passage_about_flags(self):
        offenders = []
        for dirpath, _dirs, files in os.walk(SHIPPED):
            if "__pycache__" in dirpath or os.sep + "vendor" in dirpath:
                continue
            for name in sorted(files):
                if not name.endswith((".md", ".py")):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as handle:
                    lines = handle.read().split("\n")
                for index, line in enumerate(lines):
                    if "INV-179" not in line:
                        continue
                    window = "\n".join(
                        lines[max(0, index - FLAG_WINDOW):index + FLAG_WINDOW + 1]
                    )
                    if FLAG_VOCABULARY.search(window):
                        continue
                    offenders.append(
                        "  %s:%d — %s"
                        % (os.path.relpath(path, REPO_ROOT), index + 1, line.strip()[:180])
                    )
        self.assertEqual(
            [], offenders,
            "INV-179 governs a field the flags in force did not populate — nothing else. A "
            "citation of it in a passage that never mentions flags, fields or a blank value "
            "is naming the wrong authority; the no-fork rule is INV-183 and the macOS "
            "direct-child rule is INV-001/INV-002:\n" + "\n".join(offenders),
        )

    def test_the_correct_citations_were_not_swept_away(self):
        """Over-reach is the other failure: the rule must still be cited where it governs."""
        found = [
            (path, lineno)
            for path, lineno, ids, _text, _raw in cited_rule_lines()
            if "INV-179" in ids
        ]
        self.assertTrue(
            found,
            "no shipped rule line cites INV-179 any more. It governs the three causes of a "
            "blank SDK field and is stated at several steps; a sweep that removed all of them "
            "left those rules with no authority at all.",
        )


class NoRestatedRuleCarriesTwoAuthorities(unittest.TestCase):
    def test_every_near_duplicate_rule_agrees_on_its_invariant(self):
        pairs = disagreeing_pairs(cited_rule_lines())
        if not pairs:
            return
        report = []
        for (path_a, line_a, ids_a, raw_a), (path_b, line_b, ids_b, raw_b) in pairs:
            report.append(
                "  %s:%d  cites %s\n    %s\n  %s:%d  cites %s\n    %s"
                % (path_a, line_a, ",".join(sorted(ids_a)), raw_a[:200],
                   path_b, line_b, ",".join(sorted(ids_b)), raw_b[:200])
            )
        self.fail(
            "one rule is stated in two files under two different authorities, so at least "
            "one citation names an invariant that does not govern it. Read both invariants "
            "against the rule and make the citations agree — or, if the two rules only look "
            "alike, add the pair to EXEMPT_PAIRS with the reason:\n" + "\n\n".join(report)
        )


if __name__ == "__main__":
    unittest.main()
