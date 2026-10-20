"""A quoted measured size says what the measurement missed, and says it conditionally.

Enforces **INV-388**, registered by the maintainer 2026-10-20: an option quoting a measured
size discloses what the measurement missed, and discloses it only where it was missed. ⚠️ It
reads the shipped prose and drives the packager over fixtures; it **cannot** establish that a
live run substitutes the clause correctly, which only `dry-run` phase 3 observes.

`/package-bootcamp` Step 1 pins "⛔ **Run the dry run first. The question below quotes a measured
size, never an estimate.**" Step 2 then quotes a `transfer` figure. Step 3 -- which creates the
database backup when `backups/revisit/` does not yet exist -- runs *after* the answer. So on any
pre-graduation run, which is the whole point of an any-time flow, the figure was measured over a
tree that did not yet hold the component the same file calls the reason option 2 is large. The
figure was honest about having been **measured** and silent about what it **measured**.

**The rule, stated as this file enforces it:** where a shipped flow asks a numbered question whose
option quotes a measured size, and a later step of that same flow creates, for that option, a path
the measurement reaches, the option MUST disclose in its own text that the figure excludes it --
and the disclosure MUST be conditional, written as a `{…}` substitution span whose inclusion
condition the flow states, together with the fact that it is otherwise dropped.

⛔ **The disclosure is conditional for a reason, not for tidiness.** After graduation
`backups/revisit/` exists, the dry run walks it and the figure is complete. A line that always
said "this excludes the database backup" would be false on every post-graduation run, and a
disclosure that is always there is one the reader learns to skip past. So "present" is not the
whole check: "present and droppable" is.

⛔ **(INV-246) The site set is derived by SCANNING the shipped subtree**, and the paths a
measurement reaches are read out of `plugins/senzing-bootcamp/scripts/package_bootcamp.py` with
`ast` rather than copied here. A hand-written list of options or line numbers would stop tracking
either side the moment one changed -- and a figure that silently stops matching what the walk
covers is this issue restated.

⚠️ **Wrap-aware (INV-346).** Both halves are sentences, and the shipped option wraps mid-clause,
between "(~<n> MB{, which" and "excludes your database backup". The scan reads through
`_wrapped_text.collapsed_blocks` and reports the line each option opened on.

**The vocabulary was measured before it was narrowed, and the narrowing is stated with its reason
(INV-282).** Three readings over the live corpus, 2026-10-17:

1. **Any `~N` at all** -- 462 block matches in 140 files repo-wide, 61 in 20 under `plugins/`.
   Record counts, field-coverage percentages, model prices, tick budgets, timings. Essentially all
   correct prose: "approximately" is not "a measured size".
2. **`~N` with a size unit** -- 25 matches in 16 files repo-wide, **6 in 5 under `plugins/`**. Four
   of the six are correct prose about real file sizes (an ~80 KB PDF asset, a ~20 KB file, a ~5 KB
   article, ~8 KB of FAQ text); the remaining two are the packaging options. A guard on this
   reading would report four correct sentences and get waived.
3. **A placeholder plus a size unit** -- `<n> MB` and nothing wider -- **2 matches, both in
   `packaging.md`**, repo-wide 5 in 3 files. This is the claim's own shape: a shipped flow quotes a
   measured size by leaving a **placeholder** for the guide to substitute, so a literal figure in
   shipped prose is by construction not the thing being measured. The matcher is derived from that
   claim rather than from `~<n> MB` as written: any `<…>` token followed by a size unit counts.

⚠️ **Scope: the shipped plugin (`plugins/`), stated with its reason (INV-246).** Reading 3's other
three repo-wide matches are in `specs/` -- the frozen spec that **quotes** this question and a
ledger entry about it. `specs/` is a read-only archive (INV-307) whose copies are history, not a
flow anyone runs, so sweeping it would report a quotation for not having been corrected.

⚠️ **What this cannot establish.** (a) That a given run actually drops the clause when the backup
exists -- that is a property of the conversation, which only `dry-run` phase 3 observes. (b) That
the disclosure's wording is *true*; it checks that an exclusion is stated beside the figure, not
that the right thing is excluded. (c) A step is paired to an option through its **heading** ("For
option 2, …"); a flow that routes to a step only in running prose is invisible here. (d) A path is
recognized when written as inline code, which is how this corpus writes one.

⛔ **Every negative control runs the SAME check over a mutated copy of the shipped text
(INV-265)**, putting back the exact pre-#692 wording, and the scan asserts it read something: an
empty corpus would otherwise pass silently.

Stdlib only; shipped files are read as text and `package_bootcamp.py` is parsed, never imported
(INV-108).

Source issue: #692.

Run:  python3 -m unittest discover -s tests
"""
import ast
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files  # noqa: E402
from _wrapped_text import collapsed_blocks, line_of  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIPPED = "plugins"
PACKAGER = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "package_bootcamp.py"
FLOW = "plugins/senzing-bootcamp/skills/bootcamp-onboarding/packaging.md"

#: The packager's candidate-root tuples. Named here only so a rename is a loud failure rather than
#: a silently empty root set; their CONTENTS are never written down in this file.
ROOT_NAMES = ("SHARE_INCLUDE", "TRANSFER_EXTRA")

#: A measured size as a shipped flow quotes one: a substitution placeholder followed by a size
#: unit. Derived from the claim (INV-282) -- "the question quotes a measured size" means the file
#: carries the placeholder, because the figure itself only exists at run time.
SIZE_PLACEHOLDER = re.compile(r"<[^<>\s]{1,24}>\s*(?:[KMGT]?B|bytes?)\b")
#: A numbered option, as INV-284's gates write one.
OPTION_MARKER = re.compile(r"(?:(?<=\s)|^)(\d{1,2})\.\s")
#: A step heading that says which option it runs for.
FOR_OPTION = re.compile(r"(?i)\bfor option (\d{1,2})\b")
#: The step bringing the missed component into being, between the measurement and the write.
CREATES = re.compile(
    r"(?i)\b(?:creates?|created|writes?|written|produces?|produced|generates?|generated)\b"
    r"|\bdoes not (?:yet )?exist\b"
    r"|\bmake sure\b[^.]{0,80}\bexists?\b")
#: The disclosure itself: the figure leaves the component out.
EXCLUDES = re.compile(
    r"(?i)\bexclude[sd]?\b|\bdoes not (?:yet )?include\b|\bnot included\b|\bleaves out\b"
    r"|\b(?:did )?not measure[d]?\b|\bwithout\b")
#: The two halves of "conditional": when it goes in, and that it otherwise comes out.
CONDITION = re.compile(r"(?i)\b(?:when|where|if|unless)\b")
DROPPED = re.compile(r"(?i)\bdrop(?:s|ped|ping)?\b|\bomit(?:s|ted|ting)?\b|\bleft out\b"
                     r"|\bleave (?:it |them )?out\b")
#: The substitution span a conditional clause is written in.
CONDITIONAL_SPAN = re.compile(r"\{([^{}]*)\}")
#: Inline code, which is how this corpus writes a path.
CODE = re.compile(r"`([^`\n]+)`")
#: An ATX heading line and a code-fence line, for cutting a file into steps.
HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def measured_roots(source=None):
    """Every path a dry run walks for, read with `ast` (INV-108) and never copied into this file.

    `source` replaces the script's text, for the controls.
    """
    text = PACKAGER.read_text(encoding="utf-8") if source is None else source
    found = {}
    for node in ast.parse(text).body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        name = node.targets[0].id
        if name in ROOT_NAMES:
            found[name] = tuple(ast.literal_eval(node.value))
    missing = [name for name in ROOT_NAMES if name not in found]
    if missing:
        raise AssertionError(
            "package_bootcamp.py no longer defines %s at module level, so this guard cannot read "
            "what a dry run measures and every result below would be meaningless"
            % ", ".join(missing))
    roots = []
    for name in ROOT_NAMES:
        for root in found[name]:
            if root not in roots:
                roots.append(root)
    return tuple(roots)


def sections(text):
    """`(heading line, heading text, section text)` for each Markdown section, fences respected.

    Line-scoped by design (#692): a heading is a line, and a `#` inside a fence is a shell
    comment rather than a heading, which is why the fence state is tracked here (INV-346). The
    section's prose is handed on whole and read wrap-aware by the callers.
    """
    lines = text.splitlines()
    starts, fence = [], None
    for number, line in enumerate(lines, 1):
        fenced = FENCE.match(line)
        if fenced:
            char = fenced.group(1)[0]
            fence = char if fence is None else (None if fence == char else fence)
            continue
        if fence is None and HEADING.match(line):
            starts.append(number)
    for index, start in enumerate(starts):
        end = starts[index + 1] - 1 if index + 1 < len(starts) else len(lines)
        yield start, lines[start - 1], "\n".join(lines[start - 1:end])


def paths_under(text, roots):
    """The measured roots named by an inline-code path in `text`."""
    found = set()
    for match in CODE.finditer(text):
        raw = match.group(1).strip()
        if not raw or " " in raw or "\\" in raw or "://" in raw or ".." in raw:
            continue
        if raw.startswith(("/", ".", "~", "$", "<", "-")):
            continue
        parts = raw.rstrip("*").rstrip("/").split("/")
        for root in roots:
            segments = root.split("/")
            if parts[:len(segments)] == segments:
                found.add(root)
    return found


def size_quoting_options(text):
    """`(option number, option text, line)` for every numbered option quoting a measured size.

    Read wrap-aware (INV-346): a numbered list with no blank line inside it collapses to one
    block, so the options are split back out on their own markers rather than on line breaks.
    Only a list numbered 1..n is read as a gate's options, so a stray "2. " in prose is not one.
    """
    for flat, origin in collapsed_blocks(text):
        marks = [(m.start(), m.end(), int(m.group(1))) for m in OPTION_MARKER.finditer(flat)]
        numbers = [number for _, _, number in marks]
        if len(numbers) < 2 or numbers != list(range(1, len(numbers) + 1)):
            continue
        for index, (start, end, number) in enumerate(marks):
            stop = marks[index + 1][0] if index + 1 < len(marks) else len(flat)
            segment = flat[end:stop]
            if SIZE_PLACEHOLDER.search(segment):
                yield number, segment, line_of(origin, start)


def creation_steps(text, roots):
    """`{option number: [(heading line, [roots])]}` for each step that creates what was measured."""
    out = {}
    for line, heading, body in sections(text):
        match = FOR_OPTION.search(heading)
        if not match or not CREATES.search(body):
            continue
        reached = sorted(paths_under(body, roots))
        if reached:
            out.setdefault(int(match.group(1)), []).append((line, reached))
    return out


def conditional_rule(text, roots):
    """The line stating when the clause goes in and that it is otherwise dropped, or None."""
    for flat, origin in collapsed_blocks(text):
        if "{" not in flat or not CONDITION.search(flat) or not DROPPED.search(flat):
            continue
        if any(root in flat for root in roots):
            return line_of(origin, 0)
    return None


def disclosure_problems(text, roots):
    """Every quoted size that does not say what it missed, or says it unconditionally.

    A pure function over one file's text, so each negative control runs this same check over a
    mutated copy (INV-265).
    """
    steps = creation_steps(text, roots)
    if not steps:
        return []
    problems = []
    for number, segment, line in size_quoting_options(text):
        later = [(where, reached) for where, reached in steps.get(number, []) if where > line]
        if not later:
            continue
        missed = sorted({root for _, reached in later for root in reached})
        named = ", ".join("`%s`" % root for root in missed)
        disclosing = [span for span in CONDITIONAL_SPAN.findall(segment)
                      if EXCLUDES.search(span)]
        if not disclosing:
            if EXCLUDES.search(segment):
                problems.append(
                    "line %d: option %d discloses what the figure missed, but not inside a `{…}` "
                    "span, so it is standing text -- it would print on runs where %s already "
                    "exists and the figure is complete" % (line, number, named))
            else:
                problems.append(
                    "line %d: option %d quotes a measured size, and a later step of this flow "
                    "creates %s for that very option -- which the measurement reaches, so the "
                    "figure was taken before it existed. The option says nothing about excluding "
                    "it." % (line, number, named))
            continue
        if conditional_rule(text, missed) is None:
            problems.append(
                "line %d: option %d's disclosure is written as a `{…}` span, but nothing in this "
                "flow says when it goes in and when it is dropped, so the guide has no way to "
                "tell -- and an always-printed disclosure is false wherever %s exists"
                % (line, number, named))
    return problems


def shipped_texts():
    """`(repo-relative path, text)` for every readable shipped file, by SCANNING (INV-246)."""
    for path in corpus_files(SHIPPED, root=REPO_ROOT):
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield Path(path).relative_to(REPO_ROOT).as_posix(), text


def shipped(relative):
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def mutate(test, text, old, new):
    """Replace `old` once; fail the control if the anchor text has gone."""
    test.assertIn(old, text, "the control's anchor text is gone; update the control")
    return text.replace(old, new, 1)


#: Option 2 as it read before #692, as `(shipped now, as it read before)`. The controls put it
#: back and run the same check.
PRE_692_OPTION = (
    "machine (~<n> MB{, which\n   excludes your database backup — choosing this creates it, and "
    "it is the largest part}).",
    "machine (~<n> MB).")

#: The clause taken out of its braces -- the unconditional form decision 2 of this issue rejects.
UNCONDITIONAL = (
    "(~<n> MB{, which\n   excludes your database backup — choosing this creates it, and it is "
    "the largest part}).",
    "(~<n> MB, which\n   excludes your database backup — choosing this creates it, and it is "
    "the largest part).")


class TheMeasuredRootsAreReadFromTheScript(unittest.TestCase):
    """What a dry run walks for is read with `ast`, never restated here."""

    @classmethod
    def setUpClass(cls):
        cls.roots = measured_roots()

    def test_the_root_set_is_not_empty(self):
        """⛔ (INV-265) An empty root set would make every option below trivially clean."""
        self.assertGreaterEqual(len(self.roots), 4,
                                "the packager's candidate roots read as %r" % (self.roots,))

    def test_the_revisit_bundle_is_one_of_them(self):
        """The whole issue: the backup Step 3 creates is a tree the measurement walks for."""
        self.assertIn("backups/revisit", self.roots)

    def test_the_backup_constant_agrees_with_the_tuple(self):
        """The script spells `backups/revisit` twice on purpose; the two must not drift."""
        source = PACKAGER.read_text(encoding="utf-8")
        constant = next(
            ast.literal_eval(node.value) for node in ast.parse(source).body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "DATABASE_BACKUP_ROOT")
        self.assertIn(constant, self.roots,
                      "`DATABASE_BACKUP_ROOT` names %r, which no profile reaches, so the dry "
                      "run's disclosure line can never fire" % constant)


class EveryQuotedSizeSaysWhatItMissed(unittest.TestCase):
    """The whole shipped subtree, derived by scanning (INV-246)."""

    @classmethod
    def setUpClass(cls):
        cls.roots = measured_roots()
        cls.corpus = list(shipped_texts())

    def test_every_shipped_file_is_clean(self):
        for relative, text in self.corpus:
            with self.subTest(site=relative):
                self.assertEqual(
                    [], disclosure_problems(text, self.roots),
                    "%s quotes a measured size for an option whose own later step creates part "
                    "of what the measurement covers. Say in the option, in a `{…}` span, that "
                    "the figure excludes it, and state beside the question when that span goes "
                    "in and when it is dropped." % relative)

    def test_the_scan_read_the_corpus_it_claims_to(self):
        """⛔ (INV-265) An empty match set is an unrun check, never a pass."""
        names = [relative for relative, _text in self.corpus]
        self.assertGreater(len(self.corpus), 50,
                           "the shipped subtree scan found almost no files; it is not scanning")
        self.assertIn(FLOW, names,
                      "the packaging flow is not in the scanned set, so the scan reaches none of "
                      "the prose this guard exists for")

    def test_the_scan_found_a_quoted_size_and_a_creation_step(self):
        """The floor beneath the clean result: a vocabulary matching nothing passes silently."""
        quoted, paired = 0, 0
        for _relative, text in self.corpus:
            options = list(size_quoting_options(text))
            quoted += len(options)
            steps = creation_steps(text, self.roots)
            for number, _segment, line in options:
                paired += len([1 for where, _reached in steps.get(number, []) if where > line])
        self.assertGreaterEqual(quoted, 2,
                                "only %d shipped options quote a measured size" % quoted)
        self.assertGreaterEqual(paired, 1,
                                "no shipped option quotes a size that a later step of its own "
                                "flow adds to, so a clean result measures nothing")


class ThePairingIsDerivedFromTheFlowAndTheScript(unittest.TestCase):
    """What makes an option owe a disclosure, pinned on the live text."""

    @classmethod
    def setUpClass(cls):
        cls.roots = measured_roots()
        cls.text = shipped(FLOW)

    def test_both_options_that_quote_a_size_are_found(self):
        found = {number: line for number, _segment, line in size_quoting_options(self.text)}
        self.assertEqual([1, 2], sorted(found),
                         "the packaging question's size-quoting options read as %r" % found)

    def test_only_option_2_has_a_later_step_that_creates_what_was_measured(self):
        steps = creation_steps(self.text, self.roots)
        self.assertEqual([2], sorted(steps),
                         "the flow's option-specific steps read as %r" % steps)
        self.assertEqual([["backups/revisit"]], [reached for _where, reached in steps[2]])

    def test_option_1_owes_nothing_and_that_is_the_point(self):
        """Conditional at the site level too: option 1's `share` figure misses nothing later.

        ⚠️ Recorded because a guard that demanded a disclosure on every quoted size would make
        option 1 say it excludes a backup `share` never carries -- a false sentence added to fix
        a true one.
        """
        self.assertEqual([], [p for p in disclosure_problems(self.text, self.roots)
                              if "option 1" in p])

    def test_a_step_for_option_1_would_make_option_1_owe_one(self):
        """⛔ The requirement follows the flow, not a list of option numbers written here."""
        injected = mutate(
            self, self.text, "## Step 3: For option 2,",
            "## Step 2b: For option 1, write the exports\n\n"
            "Run the export program again, which writes `data/exports/` afresh.\n\n"
            "## Step 3: For option 2,")
        reported = disclosure_problems(injected, self.roots)
        self.assertTrue([p for p in reported if "option 1" in p],
                        "a step that creates `data/exports/` for option 1, after the question, "
                        "leaves option 1 clean -- so the pairing is not derived from the flow")

    def test_the_conditional_rule_is_found_beside_the_question(self):
        self.assertIsNotNone(conditional_rule(self.text, ["backups/revisit"]))


class TheControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs `disclosure_problems` over the shipped text, mutated."""

    @classmethod
    def setUpClass(cls):
        cls.roots = measured_roots()

    def check(self, text):
        return disclosure_problems(text, self.roots)

    def test_the_shipped_flow_is_clean(self):
        self.assertEqual([], self.check(shipped(FLOW)))

    def test_the_pre_692_wording_is_reported(self):
        """The negative control the issue asks for: the option as it read before this change."""
        reported = self.check(mutate(self, shipped(FLOW), *PRE_692_OPTION))
        self.assertTrue(
            reported,
            "putting option 2's pre-#692 wording back is not reported, so the check does not "
            "cover the defect it was written for")
        self.assertIn("backups/revisit", " ".join(reported))
        self.assertIn("option 2", " ".join(reported))

    def test_an_unconditional_disclosure_is_reported(self):
        """⛔ Decision 2 of this issue: always-on disclosure is a different defect, not the fix."""
        reported = self.check(mutate(self, shipped(FLOW), *UNCONDITIONAL))
        self.assertTrue(
            reported,
            "the same sentence outside its `{…}` span passes, so this guard checks only that a "
            "disclosure exists and not that it can be dropped")
        self.assertIn("standing text", " ".join(reported))

    def test_a_clause_with_no_stated_condition_is_reported(self):
        """The clause is only conditional if the flow says when it goes in and when it does not."""
        text = shipped(FLOW)
        start = text.index("⛔ **(INV-388) Option 2's `{…}` clause")
        end = text.index("⚠️ **Why it is conditional")
        reported = self.check(text[:start] + text[end:])
        self.assertTrue(
            reported,
            "removing the rule that states the condition leaves the flow clean, so the clause "
            "could ship as standing text inside decorative braces")
        self.assertIn("when it goes in", " ".join(reported))

    def test_the_pre_692_wording_is_reported_across_a_line_wrap(self):
        """⛔ (INV-346) The option wraps mid-clause; a line-at-a-time read would miss it."""
        text = mutate(self, shipped(FLOW), *PRE_692_OPTION)
        wrapped = mutate(self, text, "and mappings, so you can pick the bootcamp back up on "
                                     "another machine (~<n> MB).",
                         "and mappings, so you can pick the bootcamp back up on\n   another\n"
                         "   machine (~<n>\n   MB).")
        self.assertTrue(
            wrapped != text, "the wrap control did not change the text")
        self.assertTrue(
            self.check(wrapped),
            "a size placeholder broken across lines is no longer seen, so the guard has lost "
            "the wrap-awareness INV-346 requires")

    def test_the_shipped_clause_survives_a_line_wrap(self):
        """The other direction: a correct disclosure rewrapped must stay correct."""
        text = shipped(FLOW)
        wrapped = mutate(self, text, "(~<n> MB{, which\n   excludes your database backup",
                         "(~<n>\n   MB{,\n   which excludes your\n   database backup")
        self.assertEqual([], self.check(wrapped))

    def test_the_requirement_follows_the_script_not_the_prose(self):
        """⛔ Drop `backups/revisit` from what a dry run walks and nothing is owed.

        The option's figure would then genuinely not be measuring the backup's tree at all, so
        the disclosure would be about something the measurement never claimed. Pinned because it
        is what makes this a cross-check between the flow and the packager rather than a reading
        of the flow alone.
        """
        narrowed = tuple(root for root in self.roots if root != "backups/revisit")
        self.assertEqual(
            [], disclosure_problems(mutate(self, shipped(FLOW), *PRE_692_OPTION), narrowed),
            "the pre-#692 text is still reported with `backups/revisit` out of the measured "
            "roots, so this guard reads the prose and not the packaging rules")


if __name__ == "__main__":
    unittest.main()
