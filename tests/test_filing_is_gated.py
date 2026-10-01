"""Every surface that INSTRUCTS an outward act states the gate beside the instruction.

An outward act creates a record outside this repository: a GitHub issue, a comment, a pull
request, an upstream message. It is **outward-facing and irreversible**: the record is visible
the moment it exists, its notifications have gone out, and it can be edited or closed but never
un-created. This module covers the four acts the maintainer commands can instruct:
`gh issue create`, `gh issue comment`, `gh pr create`, and maintainer-side `submit_feedback`.

⛔ **The hard half is telling an INSTRUCTION from a PROHIBITION**, and a first scan got it
wrong. Searching for `gh issue create` returns several files, and some of them name it only to
forbid or template the act. The three pinned as negatives:

* the `--repo` prohibition the `/feedback-to-issues` command file carried, kept verbatim here;
* `.claude/skills/feedback-to-issues/issue-template.md` — a body template;
* `.claude/skills/delegate-to-mcp-server/issue-template.md` — a body template.

⚠️ **Dated note, 2026-09-30 (#262): the first negative is a pinned text, not a file.** The
command file that carried it was deleted by #262, since `/<name>` runs the skill (measured
2026-09-29, Claude Code 2.1.284, #241). Its sentence is kept verbatim as `RETIRED_PROHIBITION`,
so the negative set stays at three rather than shrinking toward vacuity (INV-265). The
`dry-run` command also left the unattended set; the `dry-run` skill is still in it.

⚠️ **Re-pointed 2026-09-28 (#215).** The third negative was
`.claude/skills/unattended-issue-loop/SKILL.md` (*"An unattended audit FILES NOTHING."*). That
file is gone (#239), and the loop that runs has no audit cycle. The delegate template replaces
it so the negative set does not shrink toward vacuity (INV-265).

A guard that cannot tell them apart demands a gate on the rule that forbids filing, which is the
same "satisfied by something adjacent" defect this repository keeps finding -- committed inside
the guard written to prevent it.

⛔ **For the three `gh` commands the discriminator is the fence.** A command inside a fenced
code block is one the reader is told to run; one in inline backticks is prose *about* it.
Measured 2026-09-29 over the 8 files that name `gh issue create`, it split them **5 and 3**,
exactly along the instruction/prohibition line (7 files and **5 and 2** after #262, plus the
pinned text). `ProhibitionsAreNotInstructions` pins the three
negatives. ⛔ **`submit_feedback` is an MCP call and is never fenced**, so its instruction is
the call shape `submit_feedback(category=…)`; prose naming the tool is not one.

⚠️ **The gate is required NEAR the instruction, not anywhere in the file.** A file-wide search
would let a gate in one section vouch for an instruction in another. Measured 2026-09-29: 2 to
7 lines for the five `gh issue create` sites, and 1 and 3 for the two `submit_feedback` sites,
on both sides of the instruction.

⛔ **Which records need a per-record yes is INV-314's scope note (#216), applied 2026-09-30.**
Applying `unattended-ok` is assent, given in advance, to a closed list of acts on that issue
only, and invoking `/implement-github-issue <n>` is assent to five comments on `<n>`. The two
overlays under `.claude/skill-overlays/` state the list and cite the note. So a `gh issue
comment` or `gh pr create` instruction may sit beside that citation instead of a yes. A new
issue and `submit_feedback` are never on the list, and only a yes vouches for them.

⛔ **The unattended surfaces instruct only acts from the list.** They are discovered, not
listed: the loop's overlay, the Step 8.1 mapping row for a finding with no entry, and every
branch opened by a bold *Unattended* or *No maintainer present* label. None may instruct a new
issue, a `submit_feedback` call or adding `unattended-ok`. No `.claude/` or `tests/` file may
say that nothing leaves the machine unattended, or that the loop files an issue itself.

⚠️ **`gh issue comment` and `gh pr create` have no fenced site in this repository today.** Both
live only in the governing copies under `~/.claude/skills/`, which this module cannot read and
CI never has (INV-308). For those two the check runs over the whole corpus, and the synthetic
controls in `TheCheckersAreNotVacuous` keep it from passing by finding nothing.

⚠️ **What this does NOT establish.** It pins that each instruction and its gate **sit together
in the shipped text**. It cannot establish that a run actually asks, that a maintainer actually
answered, that an unattended run kept to the list, or which issue a comment was posted on --
those are properties of a live turn, and only `dry-run` phase 3 observes one. An act named in
prose rather than a fence or a call shape is outside the finders (`/dry-run`'s outbound rule is
pinned by `tests/test_dry_run_files_issues.py` instead), and so is a `gh` verb that is not one
of the four acts. A green run means the rule is *written* everywhere it should be, not that it
was *obeyed*.

⛔ **Enforces INV-314** — a maintainer command creating a record outside this repository
presents the exact text and gets the maintainer's assent first, each record separately;
unattended, it creates nothing and writes the drafted text where the maintainer will find it.

Source issues: #106, #216.

Stdlib only; the surfaces are discovered rather than listed (INV-246).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE = REPO_ROOT / ".claude"
TESTS = REPO_ROOT / "tests"

#: A fenced block, indented or not. ⛔ `[ \t]*` is load-bearing: two of the instructions sit
#: inside list items, so their fences are indented and a column-0 pattern missed them -- which
#: made the first measurement report those surfaces as ungated.
FENCE = re.compile(r"^[ \t]*```.*?^[ \t]*```", re.M | re.S)

#: The act this module was first written for.
FILING = "gh issue create"

#: The three `gh` acts, each an instruction only inside a fence.
GH_ACTS = (FILING, "gh issue comment", "gh pr create")

#: `submit_feedback` as a call. The prose that names the tool, forbids it or records a value
#: from it has no `(category=` after the name.
SUBMIT = "submit_feedback"
SUBMIT_CALL = re.compile(r"\bsubmit_feedback\(\s*category\s*=")

#: The gate, matched on the CLAIM rather than one phrasing (INV-282). The shipped wordings are
#: "get a yes first", "get a yes, before filing", "get a yes, then file" and, at both
#: `submit_feedback` sites, "get an explicit yes".
GATE = re.compile(r"(?i)\bget an? (?:explicit )?yes\b")

#: A citation of INV-314's scope note, as both overlays write it.
SCOPE_NOTE = re.compile(r"INV-314, as amended by its 2026-09-30 scope note\b[^\n]*#216")

#: What may stand beside each act. Only a yes vouches for a new issue or `submit_feedback`,
#: because neither is on the scope note's list.
ACCEPTED = {
    FILING: (GATE,),
    "gh issue comment": (GATE, SCOPE_NOTE),
    "gh pr create": (GATE, SCOPE_NOTE),
    SUBMIT: (GATE,),
}

#: How far from the instruction the gate may sit. Measured 2026-09-29: at most 7 lines. The
#: bound is deliberately small -- a file-wide search would let a gate in one section vouch for
#: an instruction in another.
GATE_WINDOW = 25

#: The label that opens a surface's unattended branch. Both wordings the corpus uses are bold.
UNATTENDED_BRANCH = re.compile(r"\*\*(?i:unattended|no maintainer present)(?![\w-])")

#: The two unattended surfaces with no such label: the loop's overlay, which describes nothing
#: else, and the Step 8.1 mapping row for a finding with no entry.
LOOP_OVERLAY = "skill-overlays/unattended-issue-loop.md"
NO_ENTRY_ROW = ("skills/feedback-to-issues/SKILL.md", re.compile(r"^[ \t]*\| \*\(no entry:", re.M))

#: Adding `unattended-ok`, which no run may do (INV-318 for a filed issue; the scope note for any).
ADDS_THE_LABEL = re.compile(r"--add-label[\s=]+[\"']?unattended-ok")

#: The two claims the scope note contradicts. An unattended run creates the listed acts, so
#: something does leave the machine; and it files no issue, so no finding is one it files itself.
STALE_CLAIM = re.compile(
    r"(?i)nothing leaves the machine unattended|\bfiles itself\b"
    r"|\bunattended (?:loop|run) files (?:an? |its own )?issues?\b")


def line_of(text, offset):
    return text[:offset].count("\n") + 1


def surfaces():
    """Every markdown file under `.claude/`, other worktrees' checkouts excepted."""
    return sorted(p for p in CLAUDE.rglob("*.md")
                  if "worktrees" not in p.relative_to(CLAUDE).parts)


def instruction_lines(text, act=FILING):
    """Line numbers where `text` tells the reader to RUN `act`.

    A `gh` act is an instruction inside a fenced block and prose in inline backticks.
    `submit_feedback` is an instruction in its call shape.
    """
    if act == SUBMIT:
        return [line_of(text, m.start()) for m in SUBMIT_CALL.finditer(text)]
    return [line_of(text, m.start()) for m in FENCE.finditer(text) if act in m.group(0)]


def ungated_lines(text, act):
    """Instructions of `act` with nothing `ACCEPTED` for it within `GATE_WINDOW` lines."""
    marks = [line_of(text, m.start()) for p in ACCEPTED[act] for m in p.finditer(text)]
    return [n for n in instruction_lines(text, act)
            if not any(abs(g - n) <= GATE_WINDOW for g in marks)]


def off_list_acts(text):
    """The acts `text` instructs that an unattended run never takes."""
    found = ["%s at +%d" % (FILING, n - 1) for n in instruction_lines(text, FILING)]
    found += ["%s at +%d" % (SUBMIT, n - 1) for n in instruction_lines(text, SUBMIT)]
    found += ["--add-label unattended-ok at +%d" % (line_of(text, m.start()) - 1)
              for f in FENCE.finditer(text) for m in ADDS_THE_LABEL.finditer(f.group(0))]
    found += ["%r at +%d" % (m.group(0), line_of(text, m.start()) - 1)
              for m in STALE_CLAIM.finditer(text)]
    return found


def branch_region(text, start):
    """From `start` to the end of its list item, table row or paragraph."""
    first = text.rfind("\n", 0, start) + 1
    head = text[first:].split("\n", 1)[0]
    if head.lstrip().startswith("|"):
        return text[start:first + len(head)]
    indent = len(head) - len(head.lstrip())
    end = first + len(head)
    for line in text[end + 1:].split("\n"):
        stripped = line.lstrip()
        if (not stripped or stripped.startswith("#") or
                (len(line) - len(stripped) <= indent and re.match(r"(?:[-*]|\d+\.)\s", stripped))):
            break
        end += 1 + len(line)
    return text[start:end]


def unattended_regions():
    """`(label, text)` for every surface that describes an unattended run."""
    out = []
    overlay = CLAUDE / LOOP_OVERLAY
    if overlay.is_file():
        out.append((LOOP_OVERLAY, overlay.read_text(encoding="utf-8")))
    rel, row = NO_ENTRY_ROW
    if (CLAUDE / rel).is_file():
        text = (CLAUDE / rel).read_text(encoding="utf-8")
        out += [("%s:%d" % (rel, line_of(text, m.start())), branch_region(text, m.start()))
                for m in row.finditer(text)]
    for p in surfaces():
        text = p.read_text(encoding="utf-8")
        out += [("%s:%d" % (p.relative_to(CLAUDE).as_posix(), line_of(text, m.start())),
                 branch_region(text, m.start()))
                for m in UNATTENDED_BRANCH.finditer(text)]
    return out


def claim_corpus():
    """Every `.claude/` and `tests/` file a stale claim could be written in, this one excepted."""
    files = [p for p in CLAUDE.rglob("*") if p.suffix in (".md", ".py") and p.is_file()
             and "worktrees" not in p.relative_to(CLAUDE).parts]
    files += [p for p in TESTS.rglob("*") if p.suffix in (".md", ".py") and p.is_file()]
    return sorted(p for p in files if p.resolve() != Path(__file__).resolve())


def read(p):
    return p.read_text(encoding="utf-8")


class TheCorpusIsNotEmpty(unittest.TestCase):
    """INV-265 -- every assertion below is satisfied trivially by an empty set."""

    def test_surfaces_were_found(self):
        self.assertGreaterEqual(len(surfaces()), 10,
                                "fewer than ten markdown surfaces under %s; the glob has drifted"
                                % CLAUDE)

    def test_at_least_three_instructions_to_file(self):
        found = sum(len(instruction_lines(read(p), FILING)) for p in surfaces())
        self.assertGreaterEqual(
            found, 3,
            "fewer than three fenced `%s` instructions (%d). Either the fence pattern has "
            "drifted or the commands stopped filing; either way the gate check below is vacuous"
            % (FILING, found))

    def test_at_least_two_calls_to_submit_feedback(self):
        found = sum(len(instruction_lines(read(p), SUBMIT)) for p in surfaces())
        self.assertGreaterEqual(
            found, 2,
            "fewer than two call-shaped `%s(category=…)` instructions (%d); the call-shape "
            "finder has drifted, or the gate check below reads nothing" % (SUBMIT, found))

    def test_the_unattended_set_holds_each_named_surface(self):
        labels = [label for label, _ in unattended_regions()]
        for rel in (LOOP_OVERLAY, "skills/production-readiness-audit/SKILL.md",
                    "skills/dry-run/SKILL.md", NO_ENTRY_ROW[0]):
            with self.subTest(surface=rel):
                self.assertTrue(
                    any(label.split(":")[0] == rel for label in labels),
                    "%s is not in the unattended set (%s). Its branch label or anchor has "
                    "drifted, so the off-list check below no longer reads it"
                    % (rel, ", ".join(labels)))


class EveryInstructionCarriesTheGate(unittest.TestCase):
    def test_the_gate_is_stated_beside_each_instruction(self):
        ungated = []
        for p in surfaces():
            text = read(p)
            for act in ACCEPTED:
                ungated += ["%s:%d (%s)" % (p.relative_to(REPO_ROOT), n, act)
                            for n in ungated_lines(text, act)]
        self.assertEqual(
            [], ungated,
            "surface(s) instruct an outward act with no gate within %d lines: %s. The record "
            "exists, and its notifications have gone out, the moment the command runs. Put "
            "'get a yes' beside it, or, for a comment or a PR on the scope note's list, cite "
            "INV-314, as amended by its 2026-09-30 scope note (#216)" % (GATE_WINDOW, ", ".join(ungated)))


class UnattendedSurfacesInstructOnlyListedActs(unittest.TestCase):
    """⛔ An unattended run creates only the scope note's list, on the issue it works."""

    def test_no_unattended_surface_instructs_an_off_list_act(self):
        for label, text in unattended_regions():
            with self.subTest(surface=label):
                self.assertEqual(
                    [], off_list_acts(text),
                    "%s describes an unattended run and instructs an act outside the scope "
                    "note's list. Unattended, a new issue, a `submit_feedback` call and "
                    "adding `unattended-ok` are drafted in the handoff, never taken" % label)

    def test_no_file_says_nothing_leaves_or_the_loop_files(self):
        stale = ["%s:%d" % (p.relative_to(REPO_ROOT), line_of(read(p), m.start()))
                 for p in claim_corpus() for m in STALE_CLAIM.finditer(read(p))]
        self.assertEqual(
            [], stale,
            "file(s) say nothing leaves the machine unattended, or that the unattended loop "
            "files an issue: %s. An unattended run posts its listed comments and PR, and it "
            "files no issue" % ", ".join(stale))


class EachOverlayStatesItsPartOfTheList(unittest.TestCase):
    """Each overlay cites INV-314's scope note and states its part of the note's list."""

    PARTS = {
        LOOP_OVERLAY: ("four `/implement-github-issue` *(user level)* log comments", "one blocked comment",
                       "opening its PR", "`--no-merge`", "no new issue"),
        "skill-overlays/implement-github-issue.md": ("five comments", "escape-hatch comment",
                                                     "per-record yes"),
    }

    def test_each_overlay_cites_the_scope_note_and_states_its_acts(self):
        for rel, parts in self.PARTS.items():
            text = re.sub(r"\s+", " ", read(CLAUDE / rel))
            with self.subTest(overlay=rel):
                self.assertRegex(text, SCOPE_NOTE, "%s no longer cites INV-314 as amended by "
                                 "its 2026-09-30 scope note (#216), so the list it states "
                                 "cites nothing" % rel)
                for part in parts:
                    self.assertIn(part, text, "%s no longer states %r" % (rel, part))


class ProhibitionsAreNotInstructions(unittest.TestCase):
    """⛔ The three negatives, pinned beside the positives (INV-282)."""

    #: Each names `gh issue create` only to forbid or template it.
    NEGATIVES = (
        "skills/feedback-to-issues/issue-template.md",
        "skills/delegate-to-mcp-server/issue-template.md",
    )

    #: The prohibition the `/feedback-to-issues` command file carried until #262 deleted it,
    #: verbatim. It names `gh issue create` only to forbid a flag on it.
    RETIRED_PROHIBITION = (
        "routing is owned exclusively by `/escalate-to-parent`; in this repo — the parent —\n"
        "parent-to-child change travels by **parity**, so the parent never files into children at\n"
        "all. ⚠️ A `--repo` argument to `gh issue create`, or any other way of naming a repository,\n"
        "is a violation of this rule rather than a convenience.\n")

    def test_the_retired_prohibition_is_not_read_as_instructing(self):
        self.assertIn(FILING, self.RETIRED_PROHIBITION)
        self.assertEqual([], instruction_lines(self.RETIRED_PROHIBITION),
                         "a prohibition naming `%s` in inline backticks is read as an "
                         "instruction to file" % FILING)

    def test_none_of_them_is_read_as_instructing(self):
        for rel in self.NEGATIVES:
            p = CLAUDE / rel
            with self.subTest(surface=rel):
                self.assertTrue(p.is_file(), "%s no longer exists; re-derive the negatives" % rel)
                self.assertIn(FILING, read(p),
                              "%s no longer mentions %r, so it exercises nothing" % (rel, FILING))
                self.assertEqual(
                    [], instruction_lines(read(p)),
                    "%s is read as instructing filing. It names `%s` only to forbid or template "
                    "it, and flagging it would demand a gate on the rule that forbids the act"
                    % (rel, FILING))


class TheFenceIsWhatDistinguishes(unittest.TestCase):
    """The discriminator itself, pinned so a later edit cannot quietly widen it."""

    def test_a_fenced_command_is_an_instruction(self):
        self.assertEqual([1], instruction_lines("```bash\n%s --title x\n```" % FILING))

    def test_an_indented_fence_still_counts(self):
        """Two of the instructions sit in list items; a column-0 pattern missed them."""
        self.assertEqual([1], instruction_lines("   ```bash\n   %s --title x\n   ```" % FILING))

    def test_inline_backticks_are_not_an_instruction(self):
        self.assertEqual([], instruction_lines("a `%s` mention in prose" % FILING))

    def test_naming_submit_feedback_is_not_a_call(self):
        self.assertEqual([], instruction_lines("⛔ Never call `submit_feedback`.", SUBMIT))


class TheCheckersAreNotVacuous(unittest.TestCase):
    """Negative controls, run on every suite: each mutation must fail the check it targets."""

    SYNTHETIC = "Post the comment.\n\n```bash\n%s 12 --body-file f\n```\n"

    def _site(self, rel, act):
        text = read(CLAUDE / rel)
        self.assertTrue(instruction_lines(text, act), "%s no longer instructs %s" % (rel, act))
        self.assertEqual([], ungated_lines(text, act), "%s is ungated as shipped" % rel)
        return text

    def test_removing_the_gate_at_a_real_filing_site_fails(self):
        text = self._site("skills/feedback-to-issues/SKILL.md", FILING)
        self.assertTrue(ungated_lines(GATE.sub("", text), FILING))

    def test_removing_the_gate_at_a_real_submit_feedback_site_fails(self):
        text = self._site("skills/delegate-to-mcp-server/SKILL.md", SUBMIT)
        self.assertTrue(ungated_lines(GATE.sub("", text), SUBMIT))

    def test_an_ungated_comment_or_pr_fails_and_a_gate_or_citation_passes(self):
        for act in ("gh issue comment", "gh pr create"):
            with self.subTest(act=act):
                bare = self.SYNTHETIC % act
                self.assertEqual([3], ungated_lines(bare, act))
                self.assertEqual([], ungated_lines("Get a yes first.\n" + bare, act))
                self.assertEqual([], ungated_lines(
                    "(INV-314, as amended by its 2026-09-30 scope note, #216)\n" + bare, act))

    def test_the_citation_never_vouches_for_a_new_issue(self):
        text = ("(INV-314, as amended by its 2026-09-30 scope note, #216)\n"
                + self.SYNTHETIC % FILING)
        self.assertEqual([4], ungated_lines(text, FILING))

    def test_an_off_list_act_in_any_unattended_surface_fails(self):
        injected = ("\n```bash\n%s --title x\n```\n" % FILING,
                    "\nThen call `submit_feedback(category='bug', message='m')`.\n",
                    "\n```bash\ngh issue edit 12 --add-label unattended-ok\n```\n",
                    " Nothing leaves the machine unattended.",
                    " A finding the unattended loop files itself.")
        for label, text in unattended_regions():
            for extra in injected:
                with self.subTest(surface=label, act=extra.strip()[:30]):
                    self.assertTrue(off_list_acts(text + extra))

    def test_listed_acts_in_an_unattended_surface_pass(self):
        text = "```bash\ngh issue comment 12 --body-file f\ngh pr create --fill\n" \
               "gh issue edit 12 --remove-label unattended-ok\n```\n"
        self.assertEqual([], off_list_acts(text))


if __name__ == "__main__":
    unittest.main()
