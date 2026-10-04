"""A claim that a rule is owned by one place must cite the invariant behind it (INV-300).

The plugin relies everywhere on *a procedure is stated once, and every other place points at
it rather than carrying a copy*. Measured 2026-09-03: the discipline is asserted at **42**
shipped sites — *"stated once"*, *"the canonical statement"*, *"do not restate it here"*, *"so
the two cannot drift apart"* — and before INV-300 was registered, **twenty-seven of them cited
no invariant at all**, while the eight that did cited **INV-183**, whose registered scope is
*"a step that instructs the guide to generate a bootcamper-facing artifact"*. The no-fork
clause lives inside that scope, so at a server launch, an SDK error branch or a pinned
question's wording it was cited for a clause whose scope did not reach it.

⛔ **The window is the unit, not the line.** A rule is routinely and correctly cited at its
bullet head several lines above the sentence that states it, and a line-level check reports
those as uncited — the 2026-09-03 audit had to retract a finding produced exactly that way.

⛔ **INV-300 states THREE obligations; this file asserts two of them.** Mapped explicitly,
because the invariant's own `Enforced by` clause names this test and a reader takes that to
mean the whole rule is guarded:

===========================================================  ==========================
INV-300 obligation                                           status here
===========================================================  ==========================
(a) name the owning file or step                             **asserted**, for pointer
                                                             sites; owner-side
                                                             declarations are exempt by
                                                             their own wording
(b) cite the invariant that makes single-statement           **asserted**
    authoritative
(c) the pointing site carries no second copy of the rule     **NOT asserted, and not
                                                             assertable** — see below
===========================================================  ==========================

⚠️ **(c) is not a gap that better regexes would close.** INV-300 itself says why: *"the
duplication scan reports **exact** repeats, so two statements that have stopped matching are
precisely what it cannot see."* Establishing it means reading each pointer against its target
and judging whether the pointer restates the rule — 38 pairs as of 2026-09-03, and a person's
work. A similarity scan was measured on this corpus and rejected: at a 0.82 floor it reports 18
pairs of which 15 are phase-header boilerplate.

⚠️ **What this guard does NOT establish, said plainly because its vocabulary is open-ended:**

- The claim vocabulary is a **phrase list**. A site that says the same thing in new words
  ("the wording lives in step 10", "one place owns this") is invisible here. A miss is weak
  evidence; a hit is worth reading.
- It checks that *an* invariant is cited in the window, not that it is the **right** one. That
  question needs a person: `inv-179-is-cited-as-a-state-it-once-rule-it-does-not-contain`
  records ten citations that resolved, passed every scan, and named the wrong rule.
- It reads shipped **markdown** only. The same phrases appear in bundled scripts about values
  and visuals not drifting, which are not rule-ownership claims at all.

Stdlib only; shipped files are read as text, never imported (INV-108).

Source spec: ``specs/the-no-fork-discipline-is-registered-only-inside-inv-183s-artifact-scope.md``.
Enforces: **INV-300**.

Run:  python3 -m unittest discover -s tests
"""

import os
import re
import unittest

from _wrapped_text import match_lines

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")

#: The vocabulary a single-statement ownership claim is written in today.
CLAIM = re.compile(
    r"stated once|states it once|stays stated once|canonical statement|do not restate|"
    r"not restated here|rather than restating|rather than a copy here|not a copy of|"
    r"rather than re-deriving|cannot drift|point at it, do not restate|"
    r"cite it rather than|link here rather than|read it there rather than", re.I)

#: ⛔ **The authority must be THE single-statement invariant, not any nearby id.** This read
#: `INV-\d+` until its own negative control failed to fire: removing INV-300 from a claim left
#: the guard green, because a neighboring rule six lines away cited something unrelated. That
#: is proximity substituting for governance — the exact defect `conformance.py per-rule` is
#: criticized for, reproduced inside the guard written to prevent it. INV-183 is accepted
#: because it states the same clause for artifact-generating steps and continues to govern
#: there (INV-300's own text says so).
CITATION = re.compile(r"INV-(?:300|183)\b")

#: Lines above and below that count as "the passage". A rule cited at its bullet head sits
#: several lines up from the sentence stating it, which is why this is not a line check.
WINDOW = 6

#: ⛔ **Hits that are NOT ownership claims**, each with the reason. Every entry is asserted to
#: still exist below: an exemption for text that has since been reworded is a lie the next
#: reader inherits, and it silently widens as the corpus changes around it.
NOT_A_CLAIM = (
    ("restate this as a snippet count",
     "a different sense of restate — do not SUMMARIZE the scaffold inventory as a count"),
    ("Senzing owns the reason, so relay it",
     "MCP sourcing: the SERVER owns the fact, which is INV-080's subject, not this one"),
    ("rather than restating a remembered one",
     "forbids reciting a remembered figure — again INV-080, not rule ownership"),
    ("Reuse one reader across modules rather than re-deriving it",
     "code reuse; the rule it names is stated in that same list, so nothing is pointed at"),
    ("the legend and the edge styling cannot drift apart",
     "two code constructs sharing a closed value set, not two statements of one rule"),
    ("two statements of the same idea cannot drift apart",
     "an authoring note about aligned wording; it names no owner and points nowhere"),
    # The next two were found by the #424 conversion: each is wrapped in the shipped text
    # ("cannot\ndrift", "do not\nrestate"), so no line-at-a-time scan ever saw them.
    ("so it cannot drift at runtime",
     "INV-056's pinned gate wording: the drift is improvisation at runtime, not a second "
     "statement of a rule"),
    ("so do not restate them here, just follow them",
     "MCP sourcing: `explain_error_code` owns the SENZ2207 resolution steps, which is "
     "INV-080's subject (cited in the same paragraph), not this one"),
)

#: Measured at 42 on 2026-09-03. A floor, not a pin — the corpus grows.
MIN_CLAIMS = 30

#: ⛔ **An OWNER-side declaration is exempt from obligation (a), by its own wording.** A
#: passage saying *"this is the canonical statement"* names no owning file because it IS the
#: owner — the obligation reads vacuously there. Detected by the declaration itself, never by
#: a list of the three sites known today (INV-246): a fourth canonical statement must be
#: exempt on the same terms without anyone remembering to add it.
#: ⛔ **The SUBJECT is the whole distinction, and this read the phrase instead until
#: 2026-09-03.** An owner says *"**this** is the canonical statement"*; a pointer says
#: *"X …, **which** is the canonical statement"*. The earlier `(?:this\s+is|is)` alternation
#: matched the pointer form, so module 4's sample gate — *"see the sampling rule in Step 6,
#: which is the canonical statement"* — was granted the owner's exemption from obligation (a).
#: Nothing was wrong at that site (it names its owner by link and by step), but the obligation
#: held there **unasserted**, and the owner-side clause *carry the rule in full* was being
#: asserted of a pointer, where carrying the rule in full is exactly what it must not do.
#: ⚠️ **The guard's negative controls could not have caught this**: they plant a missing
#: citation and a missing owner, never a misclassified site. A control proves the assertion
#: fires; it says nothing about whether the population it fires over is the right one.
#: ⚠️ **What the tightened form cannot see:** an owner phrased another way — *"the canonical
#: statement is here"*, *"this step owns the rule"* — is treated as a pointer and asked to name
#: an owner it cannot name. The failure message for obligation (a) names that remedy, because
#: the wrong fix is to point a site at itself.
#: (Source: `the-owner-side-detector-reads-a-pointer-as-an-owner`, 2026-09-03.)
OWNER_SIDE = re.compile(r"this\s+is\s+the\s+canonical\s+statement", re.I)

#: How a passage names its owner: a file, a quoted section title, a step, or an anchor. Any
#: one is enough — the obligation is that the reader can get there, not how.
OWNER_REFERENCE = re.compile(
    r"`[^`]+\.md`|`[^`]+\.py`|→\s*[\"“]|[\"“][^\"”]{4,}[\"”]|\b[Ss]tep\s+\d|"
    r"sub-step\s+\d|#[a-z0-9-]{4,}")


def shipped_markdown():
    for dirpath, _dirs, files in os.walk(SHIPPED):
        if "__pycache__" in dirpath or os.sep + "vendor" in dirpath:
            continue
        for name in sorted(files):
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


def claims_in(text):
    """[(lineno, line, window)] for each line on which a non-exempt claim starts.

    ⚠️ **Matched across line wraps (#424).** ``match_lines`` runs ``CLAIM`` on
    whitespace-collapsed Markdown blocks, so a claim such as "stated\nonce" is found and
    reported at the line where it starts. Read one line at a time, a wrapped claim was
    invisible, and an uncited one passed. ``WRAPPED_UNCITED_CLAIM`` below is the control.
    """
    lines = text.split("\n")
    found = []
    for lineno in sorted(set(match_lines(text, CLAIM))):
        index = lineno - 1
        window = "\n".join(lines[max(0, index - WINDOW):index + WINDOW + 1])
        # An exemption phrase can wrap too, so it is looked for in the collapsed window.
        if any(phrase in " ".join(window.split()) for phrase, _why in NOT_A_CLAIM):
            continue
        found.append((lineno, lines[index].strip(), window))
    return found


def ownership_claims():
    """[(relpath, lineno, line, window)] for every claim that is not exempt."""
    found = []
    for path in shipped_markdown():
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        for lineno, line, window in claims_in(text):
            found.append((os.path.relpath(path, REPO_ROOT), lineno, line, window))
    return found


#: A claim wrapped mid-phrase, with no citation in its passage: "stated" ends line 1 and "once"
#: begins line 2. A line-at-a-time scan never saw it (#424).
WRAPPED_UNCITED_CLAIM = """Draw the sample exactly as Module 5 says. The sampling rule is stated
once, in Step 6, and every other module points there.
"""


class ClaimsAreMatchedAcrossLineWraps(unittest.TestCase):
    """Negative controls for the #424 conversion to ``match_lines``."""

    def test_a_wrapped_uncited_claim_is_reported_at_its_first_line(self):
        found = claims_in(WRAPPED_UNCITED_CLAIM)
        self.assertEqual([1], [lineno for lineno, _line, _window in found])
        self.assertIsNone(CITATION.search(found[0][2]), "the fixture must stay uncited")
        # The old line-at-a-time scan, kept only to show the fixture is the hard case.
        self.assertFalse(any(CLAIM.search(line) for line in WRAPPED_UNCITED_CLAIM.split("\n")),
                         "the fixture no longer splits the claim across lines")

    def test_the_same_claim_with_its_citation_is_not_an_offender(self):
        """Must-not-flag (INV-282): the corrected passage cites INV-300 and passes."""
        cited = WRAPPED_UNCITED_CLAIM.replace("points there.", "points there (INV-300).")
        found = claims_in(cited)
        self.assertEqual([1], [lineno for lineno, _line, _window in found])
        self.assertIsNotNone(CITATION.search(found[0][2]))

    def test_a_wrapped_owner_declaration_is_found(self):
        text = "Keep this paragraph whole. This is the\ncanonical statement of the rule.\n"
        self.assertEqual([1], match_lines(text, OWNER_SIDE))
        self.assertFalse(any(OWNER_SIDE.search(line) for line in text.split("\n")))


class TheScanSeesTheCorpus(unittest.TestCase):
    def test_enough_claims_are_found_to_be_checking_something(self):
        """⛔ A scan matching nothing would pass the class below vacuously."""
        claims = ownership_claims()
        self.assertGreaterEqual(
            len(claims), MIN_CLAIMS,
            "expected at least %d single-statement claims in shipped markdown, found %d. A "
            "drop this large means the vocabulary in CLAIM has stopped matching how the "
            "plugin writes, not that the claims are gone." % (MIN_CLAIMS, len(claims)))

    def test_every_exemption_still_matches_real_text(self):
        """An exemption for text that no longer exists silently widens as prose changes."""
        corpus = " ".join(" ".join(
            open(p, encoding="utf-8").read() for p in shipped_markdown()).split())
        for phrase, why in NOT_A_CLAIM:
            with self.subTest(phrase=phrase[:40]):
                # ⚠️ `assertIn` against the corpus prints the whole haystack on failure —
                # 1.3 MB of shipped markdown, which buries the one line that matters. Assert
                # the boolean and say what is missing instead.
                self.assertTrue(
                    phrase in corpus,
                    "this exemption matches nothing in shipped markdown any more: %r (%s). "
                    "Either the passage was reworded — re-read it and decide again — or the "
                    "exemption was wrong to begin with." % (phrase, why))


class EveryClaimNamesAnAuthority(unittest.TestCase):
    def test_each_claim_has_an_invariant_in_its_passage(self):
        offenders = []
        for relpath, lineno, line, window in ownership_claims():
            if CITATION.search(window):
                continue
            offenders.append("  %s:%d — %s" % (relpath, lineno, line[:130]))
        self.assertEqual(
            [], offenders,
            "a site claims a rule is stated once elsewhere and names no invariant for that "
            "claim (INV-300). Cite INV-300 — or INV-183 where the step generates a "
            "bootcamper-facing artifact, which is the scope INV-183 covers. Without an id, "
            "nothing binds future work to the single-statement discipline and nothing notices "
            "when a later edit forks the rule into a second copy:\n" + "\n".join(offenders))

    def test_each_pointer_side_claim_names_its_owner(self):
        """Obligation (a): a claim that points must say where the rule lives.

        ⚠️ **Measured before it was asserted**: 41 of the 42 claims already named an owner on
        2026-09-03, and the one that did not was an owner-side declaration — so this assertion
        was written from what the corpus does, not from what the invariant's sentence implies.
        """
        offenders = []
        for relpath, lineno, line, window in ownership_claims():
            if OWNER_SIDE.search(window):
                continue
            if OWNER_REFERENCE.search(window):
                continue
            offenders.append("  %s:%d — %s" % (relpath, lineno, line[:130]))
        self.assertEqual(
            [], offenders,
            "a claim says a rule is stated once elsewhere and never says WHERE (INV-300). "
            "Name the owning file, the quoted section, or the step — a pointer the reader "
            "cannot follow leaves them to re-derive the rule, which is the second copy this "
            "invariant exists to prevent. ⚠️ If a site listed here IS the canonical statement "
            "rather than a pointer to one, phrase it as \"This is the canonical statement\" and "
            "it is exempt by wording — do NOT satisfy this by pointing the site at itself:\n"
            + "\n".join(offenders))

    def test_every_owner_side_declaration_cites_this_invariant(self):
        """The owner side's own obligation (INV-300's two-sides note, 2026-09-03).

        An owner-side declaration is exempt from naming an owner — it IS the owner — but it
        owes the citation, so the discipline is reachable from either end rather than only
        from the pointer. ⚠️ Checked over the passage, not the line: `module-04:488`'s
        citation sits on the following line, moved there so it would not break the exact
        phrase two other guards pin.

        ⛔ **The other half of that clause — the owner carries the rule in full — is NOT
        asserted here and is not assertable**, for the same reason as obligation (c): judging
        whether a passage states a rule *completely* is semantic. The invariant says so too.
        """
        offenders = []
        for path in shipped_markdown():
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            lines = text.split("\n")
            for lineno in sorted(set(match_lines(text, OWNER_SIDE))):
                index = lineno - 1
                window = "\n".join(lines[max(0, index - WINDOW):index + WINDOW + 1])
                if "INV-300" in window:
                    continue
                offenders.append(
                    "  %s:%d — %s"
                    % (os.path.relpath(path, REPO_ROOT), lineno, lines[index].strip()[:130]))
        self.assertEqual(
            [], offenders,
            "a passage declares itself the canonical statement of a rule and does not cite "
            "INV-300 in its own passage. The owner side is exempt from naming an owner, not "
            "from citing the authority — without it the discipline is discoverable only from "
            "whichever sites happen to point here:\n" + "\n".join(offenders))

    def test_the_owner_side_exemption_is_not_a_path_list(self):
        """⛔ The exemption must be earned by wording, so a fourth owner site is covered too.

        Asserted against a synthetic passage rather than a shipped one: if this only checked
        the three sites that exist today it would be the hardcoded list it exists to avoid.
        """
        for owner in (
            "**This is the canonical statement; do not restate it elsewhere (INV-300).**",
            "This is the canonical statement of the rule; other modules link here (INV-300).",
        ):
            with self.subTest(owner=owner[:44]):
                self.assertRegex(owner, OWNER_SIDE,
                                 "a self-referential canonical declaration is owner-side")
        for pointer in (
            "follow it there rather than a copy here (INV-300)",
            # ⛔ The real site this classifier misread until 2026-09-03. A pointer names the
            # owner and then describes it — the subject is the owner, not this passage.
            "see the [sampling rule](#overlap-preserving-sampling) in Step 6, which "
            "is the canonical statement; do not restate it here (INV-300).",
            "Module 5's Step 6 is the canonical statement for this arithmetic.",
        ):
            with self.subTest(pointer=pointer[:44]):
                self.assertNotRegex(
                    pointer, OWNER_SIDE,
                    "a pointer must NOT be treated as owner-side, or obligation (a) stops "
                    "binding the sites it was written for")

    def test_the_classifier_discriminates_on_REAL_text_not_only_fixtures(self):
        r"""⛔ The standing control for the 2026-09-03 tightening, and the only one available.

        Obligation (a) cannot be negative-controlled by editing a site: measured three ways on
        2026-09-03, stripping a pointer's link and step leaves the guard green, because any
        bold run within the window matches a section-reference pattern and bold is everywhere.
        Markdown does not distinguish emphasis from a section name. The maintainer struck that
        criterion and kept the classifier.

        So the control is a **property over the shipped corpus**, in both directions: the
        exemption must apply to something (or it is dead code that could be deleted without
        notice), and the tightening must exclude something (or reverting to the loose
        `(?:this\s+is|is)` form would pass unnoticed, which is exactly the regression this
        change exists to prevent). ⚠️ Deliberately **not** a count of either set — a guard
        pinned to today's number would have accepted the wrong one before it, which is the
        shape `counting-the-writers-of-license-record-limit-is-the-wrong-invariant` forbids.
        """
        # ⚠️ Matched across line wraps (#424). ``match_lines`` collapses each run of
        # whitespace to one space, so "this is" before the loose phrase is exactly "this " and
        # the lookbehind tells a pointer from an owner even when the line breaks between them.
        pointer = re.compile(r"(?<!this )is\s+the\s+canonical\s+statement", re.I)
        owners, pointers = [], []
        for path in shipped_markdown():
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            rel = os.path.relpath(path, REPO_ROOT)
            owners += ["%s:%d" % (rel, n) for n in match_lines(text, OWNER_SIDE)]
            pointers += ["%s:%d" % (rel, n) for n in match_lines(text, pointer)]
        self.assertTrue(
            owners,
            "no shipped passage is classified owner-side, so the exemption applies to nothing "
            "— either the canonical declarations were reworded, or the classifier no longer "
            "matches how they are written")
        self.assertTrue(
            pointers,
            "no shipped passage that names ANOTHER location as the canonical statement is "
            "classified as a pointer. The classifier was tightened on 2026-09-03 precisely "
            "because the loose form swallowed those; an empty set here means the loose form "
            "is back and obligation (a) has stopped binding the sites it was written for. "
            "Owners found: %r" % (owners,))
        self.assertEqual(
            [], sorted(set(owners) & set(pointers)),
            "a passage cannot be both; the classifier has stopped discriminating")

    def test_the_invariant_itself_is_reachable_from_the_claims(self):
        """⛔ INV-300 must actually be cited in shipped text, not only registered.

        An invariant nobody cites is one a later editor cannot look up and will tidy away —
        the INV-134 shape. This asserts the sweep reached shipped prose rather than stopping
        at `INVARIANTS.md`.
        """
        citing = [
            os.path.relpath(p, REPO_ROOT) for p in shipped_markdown()
            if "INV-300" in open(p, encoding="utf-8").read()
        ]
        self.assertGreaterEqual(
            len(citing), 15,
            "INV-300 is cited in only %d shipped file(s). It was swept across 18 on "
            "2026-09-03; a sharp drop means citations were removed rather than the claims "
            "themselves: %r" % (len(citing), citing))


if __name__ == "__main__":
    unittest.main()
