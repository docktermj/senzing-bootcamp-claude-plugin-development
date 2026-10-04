"""A "do not ask" branch must not sit above the only pinned question on the page.

On a bootcamp-generated scenario the guide asked the UAT stakeholder question that the
same step explicitly forbids on that path — at the end of a long session, asking the
Bootcamper to convene business users for a business case the bootcamp itself invented.

⛔ **The cause is a layout, not carelessness.** The correct path terminated in prose while
the incorrect path terminated in the only 👉 on the page — bold, pinned, verbatim, and at
the section's outer level rather than inside the branch that owned it. A guide assembling
the turn reaches for the pinned text because pinned text is what INV-056 trains it to
reach for. The prohibition was twelve lines up.

⚠️ **So the site set here is derived by SCANNING for the shape (INV-246), never from the
one reported instance.** A section qualifies when a suppression instruction ("do not ask",
"do not offer", …) appears **before** an outer-level `👉` line and close enough to read as
governing it. Every qualifying site must then make the question unreachable from the
suppressed path in one of the two ways the plugin already uses correctly:

* **Per-branch sub-headings** — `### 9a.` / `### 9b.`, so the question is structurally
  inside the branch that asks it (`module-01-business-problem/phase2-document-confirm.md`).
* **A self-contained precondition immediately above the question** — "Fallback only — when
  detection is genuinely unavailable…" (`module-02-sdk-setup/SKILL.md`), "Only when the
  source has **no** recorded provenance…" (`module-04-data-collection/SKILL.md`).

⛔ **"Otherwise" does not count, and that is the whole finding.** It is a *relative*
condition: it means nothing without the paragraph above it, which is exactly the paragraph
a guide arriving at the pinned question has not re-read. The failing step said
"Otherwise (a real business problem with stakeholders)" and read, in isolation, as an
unconditional pinned question.

⚠️ **The suppressed branch is NOT given a question to balance the shape.** It correctly ends
without one and proceeds to a self-directed spot-check; manufacturing a question there
would breach INV-006 in the opposite direction.

Source spec: `specs/the-forbidden-question-is-the-most-prominent-text-in-the-step-that-forbids-it.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp"

UAT_STEP = SKILLS / "skills" / "module-06-data-processing" / "phaseD-validation.md"
UAT_QUESTION = ("👉 **Would you like to involve business users in testing the "
                "cross-source results?** (respond yes or no)")

#: Instructions that suppress a question on one branch.
#:
#: ⚠️ Widened 2026-08-16 beyond the "do not ask" phrasings of the reported instance. A step
#: that suppresses its question by saying it "asks nothing", or forbids a *re*-ask because
#: an earlier step already decided, carries exactly the same exposure — the suppressed path
#: ends in prose and the alternative path ends in the only pinned question on the page. The
#: Phase C merge produced one of each on the day this guard was written, and the original
#: pattern saw neither.
SUPPRESS = re.compile(
    r"do not ask|do NOT ask|don't ask|do not offer|do NOT offer|never ask|MUST NOT ask|"
    r"do not re-?ask|asks? nothing|ask nothing",
    re.I)

#: How close a suppression must be to count as governing the question below it. Beyond
#: this the two are unrelated prose in a long section — verified against the tree: the
#: excluded pairs sit 85, 218 and 719 lines apart.
PROXIMITY = 25

#: A condition a reader meets AT the question, without the paragraph above it.
SELF_CONTAINED = re.compile(
    r"only when|only if|fallback only|when detection|\(when |if it carries|"
    r"only for|applies only", re.I)

#: ⛔ The shape this spec exists to remove: a condition that cannot be read alone.
RELATIVE_ONLY = re.compile(r"^\s*(?:\*\*)?otherwise\b", re.I)


def shipped_markdown():
    for path in sorted(SKILLS.rglob("*.md")):
        yield path


def sections(lines):
    """Yield (heading, start_index, end_index) for each ``## `` section."""
    bounds = [i for i, l in enumerate(lines) if l.startswith("## ")]
    bounds.append(len(lines))
    for k in range(len(bounds) - 1):
        yield lines[bounds[k]].strip(), bounds[k], bounds[k + 1]


def qualifying_sites():
    """Every (path, heading, question_line_no, lines) matching the risky shape.

    Derived by scanning, so a step that grows this shape later is caught without anyone
    remembering to add it here.
    """
    found = []
    for path in shipped_markdown():
        lines = path.read_text(encoding="utf-8").splitlines()
        for heading, start, end in sections(lines):
            block = range(start, end)
            suppress_at = suppressions(lines, start, end)
            if not suppress_at:
                continue
            for i in block:
                if not lines[i].startswith("👉"):
                    continue
                governing = [s for s in suppress_at if 0 < i - s <= PROXIMITY]
                if governing:
                    found.append((path, heading, i, lines))
    return found


def suppressions(lines, start, end):
    """Indexes in ``lines[start:end]`` where a suppression instruction starts.

    ⚠️ **Matched across line wraps (#424).** "do not\nask" is still an instruction, and a
    line-at-a-time read never saw it, so its question was never checked.

    Line-scoped by design otherwise: a question is found by the 👉 that opens its line.
    """
    return [start + n - 1 for n in match_lines("\n".join(lines[start:end]), SUPPRESS)]


def stated_condition(context):
    """True when the paragraph above a question states a self-contained condition.

    Read in order with whitespace collapsed (#424), so a condition that wraps ("only\nwhen")
    is seen; ``preceding_context`` collects the lines bottom-up.
    """
    return bool(SELF_CONTAINED.search(" ".join(" ".join(reversed(context)).split())))


def preceding_context(lines, index):
    """The single paragraph directly above `index` — the prose introducing the question.

    ⛔ **A paragraph, not a fixed line count, and the difference is load-bearing.** A
    self-contained precondition is prose and wraps, so a 3-line window missed a real
    4-line one; widening to 5 lines then let the ORIGINAL defect pass, because the window
    reached back into the *suppressed* branch, whose own text ("If it carries the
    bootcamp-generated marker…") matched the self-contained pattern. The guard was
    reading one branch's condition as though it governed the other branch's question —
    the exact confusion this whole spec is about. Stopping at the blank line cannot do
    that: it is the prose a reader meets between the question and the paragraph break
    above it, however that prose happens to wrap.
    """
    out = []
    j = index - 1
    while j >= 0 and not lines[j].strip():   # skip blank lines just above the question
        j -= 1
    while j >= 0 and lines[j].strip():       # collect the contiguous paragraph
        out.append(lines[j])
        j -= 1
    return out


def enclosing_subheading(lines, index, start):
    """The nearest ``### `` heading above `index` within the section, or None."""
    for j in range(index - 1, start, -1):
        if lines[j].startswith("### "):
            return lines[j].strip()
        if lines[j].startswith("## "):
            break
    return None


class TheUatStepBranchesBeforeItAsks(unittest.TestCase):
    """The reported instance, asserted directly."""

    def setUp(self):
        self.text = UAT_STEP.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def test_the_step_still_asks_the_question_verbatim(self):
        """INV-056 — the fix must not have reworded it."""
        self.assertIn(UAT_QUESTION, self.text,
                      "the pinned question's wording changed; INV-056 pins it verbatim")

    def test_the_generated_branch_carries_no_pinned_question(self):
        """⛔ The half that was actually broken: the suppressed path asks nothing."""
        start = next(i for i, l in enumerate(self.lines)
                     if l.startswith("### 25a."))
        end = next(i for i, l in enumerate(self.lines)
                   if i > start and l.startswith(("### ", "## ")))
        branch = self.lines[start:end]
        # Line-scoped by design (#424): a 👉 that opens a line opens a question.
        posed = [l for l in branch if l.lstrip().startswith("👉")]
        self.assertEqual([], posed,
                         "the bootcamp-generated branch poses a question; it must "
                         "proceed to the self-directed spot-check and ask nothing "
                         "(INV-006/INV-012)")

    def test_the_question_is_structurally_inside_the_stakeholder_branch(self):
        index = next(i for i, l in enumerate(self.lines) if l.startswith(UAT_QUESTION[:20]))
        section_start = next(i for i, l in enumerate(self.lines)
                             if l.startswith("## 25."))
        heading = enclosing_subheading(self.lines, index, section_start)
        self.assertIsNotNone(heading, "the question sits at the step's outer level again")
        self.assertTrue(heading.startswith("### 25b."),
                        f"the question is under {heading!r}, not the real-stakeholders "
                        "branch")

    def test_the_generated_branch_is_told_not_to_borrow_the_question(self):
        """Manufacturing a question here would breach INV-006 in the other direction."""
        flat = " ".join(self.text.split())
        self.assertIn("correctly ends with NO 👉 question", flat)


class NoSuppressedBranchLeavesAPinnedQuestionUnguarded(unittest.TestCase):
    """The class, over every shipped step that grows the shape."""

    def test_the_scan_finds_something(self):
        """Not-vacuous: if the scan matches nothing, the class test below is empty."""
        self.assertGreater(
            len(qualifying_sites()), 1,
            "the shape scan matched nothing — the class assertion below is vacuous")

    def test_every_such_question_is_reachable_only_under_a_stated_condition(self):
        offenders = []
        for path, heading, index, lines in qualifying_sites():
            section_start = max(
                (i for i in range(index, -1, -1) if lines[i].startswith("## ")),
                default=0)
            context = preceding_context(lines, index)
            sub = enclosing_subheading(lines, index, section_start)
            scoped_by_subheading = sub is not None
            stated = stated_condition(context)
            relative_only = (any(RELATIVE_ONLY.search(l) for l in context)
                             and not stated)
            if scoped_by_subheading or stated:
                if relative_only and not scoped_by_subheading:
                    offenders.append(
                        f"{path.relative_to(REPO_ROOT)}:{index + 1} — {heading} — the "
                        "question's only condition is a relative 'Otherwise'")
                continue
            offenders.append(
                f"{path.relative_to(REPO_ROOT)}:{index + 1} — {heading} — a suppression "
                "instruction governs this pinned question, but the question is neither "
                "inside a per-branch '### ' sub-heading nor preceded by a self-contained "
                "condition")
        self.assertEqual(
            [], offenders,
            "a 'do not ask' branch sits above a pinned question a guide can reach "
            "without re-reading the branch:\n  " + "\n  ".join(offenders))

    def test_a_wrapped_suppression_still_governs_the_question_below_it(self):
        """Negative control (#424): "do not" ends line 2 and "ask" begins line 3."""
        lines = ["## 9. Confirm", "", "If the source was generated, do not",
                 "ask; go on to the spot-check.", "", "👉 **Shall we involve your team?**"]
        self.assertEqual([2], suppressions(lines, 0, len(lines)))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(SUPPRESS.search(l) for l in lines))

    def test_a_wrapped_self_contained_condition_is_stated(self):
        """Must-not-flag (INV-282): "Only\nwhen" wrapped above the question still states it."""
        context = preceding_context(["**Only", "when the source has real stakeholders** — offer it:",
                                     "", "👉 **Shall we involve your team?**"], 3)
        self.assertTrue(stated_condition(context))
        self.assertFalse(any(SELF_CONTAINED.search(l) for l in context))

    def test_a_relative_otherwise_condition_is_rejected(self):
        """Negative control for the discriminator, on the exact shape that failed.

        'Otherwise' means nothing without the paragraph above it — which is the paragraph
        a guide arriving at the pinned question has not re-read.
        """
        self.assertTrue(RELATIVE_ONLY.search(
            "Otherwise (a real business problem with stakeholders), offer to involve"))
        self.assertFalse(SELF_CONTAINED.search(
            "Otherwise (a real business problem with stakeholders), offer to involve"))
        self.assertTrue(SELF_CONTAINED.search(
            "**Only when the source has no recorded provenance** — ask how they want"))


if __name__ == "__main__":
    unittest.main()
