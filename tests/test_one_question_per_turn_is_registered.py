"""The one-👉-per-turn rule is registered, and nothing cites the wrong invariant for it.

For the plugin's whole history until 2026-08-15 the rule `ground-rules.md` calls **"the #1
bootcamper complaint"** was stated in 13 shipped places, enforced with zero-tolerance
framing, checked at runtime by `auto-test`'s transcript linter (`check_one_pointer_per_turn`)
— and registered in no invariant. Six sites cited an authority and every one was wrong:

* **INV-005** is the 👉 *marker* rule in full — *"Each question to the Bootcamper is preceded
  by 👉."* A turn ending on three 👉-prefixed questions satisfies it completely.
* **INV-008** governs ambiguity ("not ambiguous with respect to a Yes or No answer").
* **INV-009** governs complexity ("not 'complex'. The use of 'or' is discouraged").

All 249 invariant entries were parsed and searched: four mentioned a per-turn count and all
four were **scoped** — INV-063 (model/effort switch), INV-064 (accepted-switch continuation),
INV-135 (license-request flow), INV-225 (an observation). None stated the general rule.
(`specs/the-one-question-per-turn-rule-is-registered-nowhere.md`)

Enforces **INV-251**. Its companion is **INV-225**, which forbids the *zero* case; the two
together fix the count at exactly one, and INV-251 deliberately does not restate INV-225's
clause — duplicating a clause across two IDs is how they drift apart.

⛔ **WHAT THIS GUARD CANNOT SEE — TWO LIMITS, both stated because one disclosure reads as all
of them.**

1. **The behavior.** Whether a guide actually ends a turn on one question is a live-turn
   property. Reading files cannot establish it, and an offline suite (INV-108) never will.
   The only mechanism that checks it is `.claude/skills/auto-test/transcript_lint.py`'s
   `check_one_pointer_per_turn`, against real transcripts; `dry-run` phase 3 judges a live
   turn. A clean run here means the rule is *registered and correctly cited* — never that it
   is obeyed.
2. **Its own reach is a heuristic.** ``states_the_count`` fires on a line carrying the 👉
   marker, a mention of a *turn*, and a quantity word. That is broader than the phrase list it
   replaced — which shipped green over six wrong citations — but it is still a guess about how
   the corpus phrases things. A claim about the count that omits the 👉 character, or speaks of
   "a reply" rather than a "turn", passes unseen. **A clean run means no line matching this
   shape is misattributed; it does not mean no misattribution exists.**

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
LINTER = REPO_ROOT / ".claude" / "skills" / "auto-test" / "transcript_lint.py"

#: Invariants that are ABOUT questions but do not govern the count. Citing one of these on a
#: line that states the count is the defect this guard exists for.
NOT_THE_COUNT = ("INV-005", "INV-008", "INV-009")

#: ⛔ **Matched on a CONJUNCTION, not a phrase list.** The first version of this guard
#: enumerated the phrasings its author had seen — and shipped green while SIX sites still
#: cited INV-005 for the count, in wordings it did not list: "end the turn on this **single**
#: 👉 question", "**One 👉 question, its own turn**", "INV-005 requires the 👉 question to end
#: the turn", "would end with **zero** 👉". A phrase list is a site set by another name, and
#: INV-246's reasoning about hardcoded paths applies to hardcoded wordings the same way.
#: (`specs/inv251-relabel-missed-six-sites-its-own-guard-cannot-see.md`)
#:
#: The durable signal is that a line mentions the 👉 marker, says something about a **turn**,
#: and quantifies it. Any line doing all three is making a claim about the count.
POINTER = "\U0001F449"
TURN = re.compile(r"(?i)\bturns?\b")
QUANTITY = re.compile(r"(?i)\b(one|single|two|zero|none|exactly|only)\b")

#: ⚠️ A turn-shape claim need not carry a number. "the 👉 question ends the turn, so
#: nothing can follow it" is INV-251's second clause stated with no quantity word, and
#: requiring one let that site escape negative control after two earlier unit changes
#: had already fixed the rest.
ENDS_THE_TURN = re.compile(r"(?i)\bends?\s+(?:the|that|each)\s+turn\b")


#: How far either side of a citation to look. Wide enough for a wrapped sentence,
#: narrow enough not to span adjacent bullets — the two failure modes above.
WINDOW = 140

#: Text that names these invariants while SAYING they are not the count. Without this a
#: correction explaining the distinction would itself trip the guard.
EXEMPT = re.compile(r"(?i)(not the count|marker rule|marker\b|at the time|"
                    r"says nothing about\s*count|not\s+INV-0\d\d|"
                    r"rather than\s+INV-0\d\d|relabeled)")


def states_the_count(line):
    """Text claiming how many 👉 a turn carries, or that one ends it."""
    if POINTER not in line or TURN.search(line) is None:
        return False
    return QUANTITY.search(line) is not None or ENDS_THE_TURN.search(line) is not None


def squash(text):
    return re.sub(r"\s+", " ", text)


def shipped_markdown():
    """Every shipped Markdown file, discovered rather than listed (INV-246)."""
    return sorted(PLUGIN.rglob("*.md"))


def paragraphs(text):
    """Runs of consecutive non-blank lines, with the line number each run starts on.

    ⛔ **The unit is a PARAGRAPH, not a line, and that distinction is the whole guard.**
    Line-based scanning escaped three of eight negative controls: this corpus wraps prose, so
    a citation and the 👉 it refers to routinely sit on different physical lines —
    "…INV-005 requires the\n👉 question to end the turn", "(INV-005), evaluating…" whose 👉 is
    on the line above. Each looked like an unrelated line to a per-line matcher and passed.
    """
    run, start = [], 1
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if not run:
                start = i
            run.append(line)
        elif run:
            yield start, " ".join(run)
            run = []
    if run:
        yield start, " ".join(run)


def misattributed_count_claims():
    """Every passage that states the count AND cites an invariant that is not the count.

    ⛔ **The unit is a WINDOW AROUND THE CITATION, and both neighbors of that choice were
    wrong when tried.** Negative control drove this, site by site:

    * **Per line** — escaped 3 of 8. This corpus wraps prose, so a citation and the 👉 it
      refers to routinely sit on different physical lines ("…INV-005 requires the\n👉 question
      to end the turn"). Each half looked innocent alone.
    * **Per paragraph** — over-reached onto 4 false positives. Consecutive non-blank lines
      merge a whole bullet list, so a correct INV-251 count bullet and an unrelated INV-008
      citation three bullets later scored as one misattribution.

    So: join the paragraph (to survive wrapping), then judge each citation on the text
    immediately around it (to avoid pairing distant, unrelated statements).
    """
    hits = []
    for root, suffixes in ((PLUGIN, (".md",)),
                           (REPO_ROOT / "tests", (".py",)),
                           (REPO_ROOT / ".claude", (".py", ".md"))):
        for path in corpus_files(root.relative_to(REPO_ROOT).as_posix(), suffixes=suffixes):
            if path.name == "test_one_question_per_turn_is_registered.py":
                continue          # this file quotes every wording deliberately
            text = path.read_text(encoding="utf-8", errors="replace")
            for start, block in paragraphs(text):
                for m in re.finditer(r"INV-00[589]", block):
                    lo = max(0, m.start() - WINDOW)
                    window = block[lo:m.end() + WINDOW]
                    if not states_the_count(window):
                        continue
                    if EXEMPT.search(window):
                        continue
                    hits.append((path, start, m.group(0), window))
    return hits


class TheInvariantIsRegistered(unittest.TestCase):
    def setUp(self):
        self.text = INVARIANTS.read_text(encoding="utf-8")

    def test_inv251_states_the_two_or_more_prohibition(self):
        self.assertRegex(
            squash(self.text),
            r"\*\*INV-251\*\* — A turn presented to the Bootcamper MUST NOT contain "
            r"\*\*two or more\*\* 👉 questions",
            "INV-251 no longer states the prohibition that was registered nowhere until "
            "2026-08-15")

    def test_inv251_is_in_the_index(self):
        """INVARIANTS.md rule 3: the index entry ships in the same edit as the invariant."""
        start = self.text.index("### Index by subject")
        end = self.text.index("<!-- New invariants", start)
        index = self.text[start:end]
        self.assertGreater(len(index), 500,
                           "the index slice collapsed; this assertion would pass vacuously")
        self.assertIn("INV-251", index,
                      "INV-251 is defined but missing from the subject index (rule 3)")

    def test_inv251_defers_the_zero_case_to_inv225(self):
        """The two must not both state the zero clause, or they can drift apart."""
        #: Sliced to the INV-251 ENTRY rather than distance-matched across the whole file:
        #: a bounded `.{0,3000}` regex over a 250-entry document is a coin toss about
        #: formatting, not an assertion about INV-251.
        entry = self.text[self.text.index("**INV-251**"):]
        entry = entry[:entry.index("(Source:") + 60]
        self.assertIn(
            "The zero case is INV-225", entry,
            "INV-251 no longer points at INV-225 for the zero case, so a reader cannot tell "
            "the two rules compose into 'exactly one'")


class ThisGuardDisclosesWhatItCannotSee(unittest.TestCase):
    """Both limits are asserted, because one disclosure reads as all of them.

    ⛔ Asserted against the module ``__doc__``, never this file's source: the reach limit's
    own vocabulary appears in the code below, so a source-text check would match its own
    identifiers and pass with the disclosure deleted.
    """

    def setUp(self):
        self.doc = squash(__doc__ or "")

    def test_the_behavior_limit_is_disclosed(self):
        self.assertRegex(
            self.doc, r"(?i)never that it is obeyed",
            "the docstring no longer says a clean run proves the rule is cited, not obeyed")

    def test_the_reach_limit_is_disclosed(self):
        """The limit that actually bit: the first guard's phrase list shipped green over six
        wrong citations, and its docstring disclosed only the runtime limit."""
        self.assertRegex(
            self.doc, r"(?i)its own reach is a heuristic",
            "the docstring no longer discloses that the guard's matching is a phrasing "
            "heuristic — the limit that let six wrong citations pass a green guard")
        self.assertRegex(
            self.doc, r"(?i)does not mean no misattribution exists",
            "the docstring no longer says what a clean run does NOT mean, which is the half "
            "a reader relies on")


class NoSiteCitesTheWrongInvariantForTheCount(unittest.TestCase):
    """The wrong-citation half, swept across shipped Markdown rather than a path list."""

    def test_the_corpus_is_actually_scanned(self):
        self.assertGreater(len(shipped_markdown()), 20,
                           "the shipped-Markdown scan collapsed; assertions below would "
                           "pass vacuously")

    def test_the_detector_is_not_vacuous(self):
        """If `states_the_count` stopped matching, the sweep below would pass on nothing.

        Exercised on synthetic text rather than the repo, deliberately: the repo is now clean,
        so asserting "the scan finds offenders" would be asserting the defect still exists.
        """
        self.assertTrue(
            states_the_count("exactly one 👉 ends the turn"),
            "the count detector no longer fires on a plain statement of the rule")
        self.assertTrue(
            states_the_count("end the turn on this single 👉 question"),
            "the detector misses the wording that escaped the first guard")
        self.assertFalse(
            states_the_count("the module banner is presented once"),
            "the detector fires on text that says nothing about 👉 in a turn")

    def test_no_count_claim_cites_a_question_invariant_that_is_not_the_count(self):
        offenders = ["%s:%d cites %s — %s"
                     % (p.relative_to(REPO_ROOT), i, iid, w.strip()[:90])
                     for p, i, iid, w in misattributed_count_claims()]
        self.assertEqual(
            [], offenders,
            "INV-005 is the 👉 marker rule, INV-008 governs ambiguity and INV-009 "
            "complexity — none states the per-turn count, which is INV-251 (zero is "
            "INV-225):\n  " + "\n  ".join(offenders))

    def test_the_canonical_statement_carries_the_id(self):
        """ground-rules.md's own 'One question per turn' bullet is where a reader looks first."""
        gr = (PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md").read_text(
            encoding="utf-8")
        self.assertRegex(
            squash(gr), r"\*\*One question per turn \(INV-251\)\.\*\*",
            "the canonical statement of the rule ships without its invariant ID, so a later "
            "editor cannot look it up (INV-183)")


class TheRuntimeCheckIsLabeledCorrectly(unittest.TestCase):
    """`auto-test`'s linter is the only thing that checks the BEHAVIOR; its label must be right.

    Its finding code is what a maintainer reads in an auto-test report. While it was
    ``INV-005-multi-question`` every caught breach pointed at a one-line marker rule.
    """

    def setUp(self):
        self.text = LINTER.read_text(encoding="utf-8")

    def test_the_linter_exists(self):
        self.assertTrue(LINTER.is_file(),
                        "the transcript linter moved; this guard's premise is stale")

    def test_the_finding_code_names_the_right_invariant(self):
        self.assertIn('"INV-251-multi-question"', self.text,
                      "the multi-question finding code no longer names INV-251")
        self.assertNotIn('"INV-005-multi-question"', self.text,
                         "the finding code still names INV-005, so every auto-test report "
                         "points the maintainer at the 👉 marker rule instead of the count")

    def test_the_counting_logic_is_unchanged(self):
        """The check was always correct — only its label was wrong. Guard against a 'fix'
        that rewrites the logic while relabeling it."""
        self.assertRegex(
            squash(self.text), r"count = text\.count\(POINTER\).{0,80}if count > 1",
            "the per-turn counting logic changed; the 2026-08-15 correction was a RELABEL "
            "and must not have altered what the check counts")


if __name__ == "__main__":
    unittest.main()
