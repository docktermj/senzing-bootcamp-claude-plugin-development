"""`/dry-run` drafts findings into its ledger entry and files GitHub issues -- never new specs.

`specs/` has been a read-only archive since the 2026-09-15 cutover (INV-307). `/dry-run` was
missed by the rework that moved every other spec-writing command to GitHub issues, so it still
told its runner, as an absolute rule, to write each finding into `specs/<kebab-case-title>.md`.
The 2026-09-24 run did exactly that and `tests/test_specs_are_frozen.py` failed with all four
files named -- the guard worked, the instruction did not (#153).

⛔ **The rule had two homes, and both carried the old destination**: the skill and the slash
command. #153 swaps the destination in both "in the same words", so this module also pins that
the command's finding lifecycle and outbound rule are word-for-word the skill's.

Checks, each negative-controlled when written (#153):

1. no `/dry-run` surface names a new `specs/*.md` as a finding's destination; citations of
   archive files that exist are allowed;
2. the durability rule survives -- a finding held only in conversation is not recorded, and a run
   does not end with unwritten findings;
3. `submit_feedback` is permitted only for an `mcp-server` finding, gated on the maintainer's
   yes, and `license_request` stays forbidden;
4. `specs/README.md` no longer says "None is left", and lists `/dry-run` with #153;

plus the issue's "in the same words" requirement for `.claude/commands/dry-run.md`.

⚠️ **What this does NOT establish:** that a run actually drafts, searches, asks or files. Those
are properties of a live session; only a real `/dry-run` shows them. This pins that the
instructions a runner reads say so.

Enforces **INV-307** (nothing new lands in `specs/`) and **INV-314** (each outward record is shown
and approved on its own) at the `/dry-run` surfaces.

Enforces **INV-317** (a finding is recorded durably as it is found, before it is fixed, and never
held only in conversation) through `SAME_WORDS`, which pins those lifecycle words in `/dry-run`'s
command and skill. ⚠️ It does **not** read `/production-readiness-audit`, which states the same rule
in its own words, and it cannot establish that a live run records before it fixes -- only a real
`/dry-run` phase 3 observes a turn.

Enforces **INV-318** (no maintainer command applies `unattended-ok` to an issue it files) through
the same `SAME_WORDS` pin, at `/dry-run`'s command and skill. ⚠️ It cannot establish that a live run
refrains from labeling -- it pins the sentence where it is written.

Source issue: #153.

Stdlib only; every file is read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DRY_RUN = REPO_ROOT / ".claude" / "skills" / "dry-run"
SKILL = DRY_RUN / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "dry-run.md"
PHASE3 = DRY_RUN / "phase3-conversational.md"
FEEDBACK = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md"
README = REPO_ROOT / "specs" / "README.md"

#: Wordings that name `specs/` (or a spec file) as where a finding GOES. Matched on normalized
#: text (see `norm`). A match preceded closely by a negation -- "never write it into `specs/`" --
#: is a prohibition, not a destination; `test_the_patterns_tell_a_rule_from_a_ban` pins both
#: sides (INV-282). The live records (`IMPLEMENTED.md` and its siblings) are not destinations
#: this rule forbids, so the verb pattern skips them.
DESTINATION_PATTERNS = (
    r"`specs/<",                                                # a placeholder path
    r"\b(?:writ\w*|put|record\w*|draft\w*|file|filed|sav\w*)\s+(?:[\w']+\s+){0,3}?into\s+"
    r"(?:a\s+)?`specs/(?!(?:implemented|invariants|declined|readme)\.md)",
    r"`specs/` is the home",
    r"\bspec-on-sight\b",
    r"\bnaming the spec (?:file )?(?:each|from step)",
    r"\bthe spec from step 1\b",
    r"\bspecs the findings were written into\b",
    r"\bevery finding is in a spec\b",
    r"\beither in a spec or in the ledger\b",
    r"\bdraft the exact message into the spec\b",
    r"\bwrite the spec\b",
    r"\bthe specs are the run's (?:actual )?output\b",
    r"\bproduced no spec\b",
)

#: How far back a negation may sit and still make a match a prohibition.
NEGATION_WINDOW = 30
NEGATION = re.compile(r"\b(?:never|not|no|don't|do not)\b")

#: A `specs/<name>.md` citation. Allowed only when it names a file that exists -- the archive's
#: frozen specs and its live records are provenance, not destinations.
SPEC_PATH = re.compile(r"specs/([A-Za-z0-9_.-]+\.md)")

#: The finding lifecycle, as the command and the skill must both say it (#153: "the same swap,
#: in the same words"). Normalized text.
SAME_WORDS = (
    "draft each finding into the run's dated `specs/implemented.md` entry as you find it, "
    "marked not yet filed, before fixing anything",
    "never into a new file under `specs/`, which is a read-only archive (inv-307)",
    "a finding that exists only in the conversation is not recorded",
    "search open and closed issues before filing",
    "a finding already tracked points at that issue instead of opening a duplicate",
    "file at the end of phase 1 or 2, and when a phase 3 walk pauses or ends",
    "show the maintainer each title and body and get a yes, one issue at a time",
    "replace the draft's marker with the issue number",
    "no maintainer present: file nothing",
    "not filed — needs the maintainer to file it",
    "declined: recorded as declined",
    "never apply `unattended-ok` to an issue the run files",
    "the scratch project is disposable; the issues and the ledger entry are the run's actual "
    "output",
    "if a run produced no issue and no ledger entry, it produced nothing durable, however good "
    "the conversation was",
)

#: The outbound rule's bounds -- it starts at this sentence and ends at the next.
OUTBOUND_START = "⛔ **Nothing leaves the machine except two outward acts"
OUTBOUND_END = "stays forbidden."


def read(path):
    return path.read_text(encoding="utf-8")


def norm(text):
    """Lower-case, bold markers dropped, whitespace collapsed -- so wrapping and emphasis
    cannot hide a clause from the scan or invent one."""
    return re.sub(r"\s+", " ", text.replace("**", "")).lower()


def surfaces():
    """Every `/dry-run` surface: the skill's own markdown and the slash command (INV-246)."""
    return sorted(DRY_RUN.glob("*.md")) + [COMMAND]


def destination_hits(text):
    flat = norm(text)
    hits = []
    for pattern in DESTINATION_PATTERNS:
        for m in re.finditer(pattern, flat):
            if not NEGATION.search(flat[max(0, m.start() - NEGATION_WINDOW):m.start()]):
                hits.append(pattern)
                break
    return hits


def outbound_rule(path):
    """The outbound rule's text in `path`, normalized; None when the file does not state it."""
    text = read(path)
    start = text.find(OUTBOUND_START)
    if start == -1:
        return None
    end = text.find(OUTBOUND_END, start)
    return norm(text[start:end + len(OUTBOUND_END)]) if end != -1 else None


class TheInputsAreReal(unittest.TestCase):
    """INV-265 -- every assertion below is satisfied trivially by a missing file."""

    def test_every_surface_exists(self):
        for path in (SKILL, COMMAND, PHASE3, FEEDBACK, README):
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                self.assertTrue(path.is_file(), "%s is missing" % path)

    def test_the_scan_covers_more_than_the_skill(self):
        self.assertGreaterEqual(
            len(surfaces()), 5,
            "fewer than five /dry-run surfaces found; the glob has drifted and the "
            "destination scan below certifies less than it claims")


class NoSurfaceNamesANewSpecAsTheDestination(unittest.TestCase):
    """Check 1 -- ⛔ INV-307. The instruction that turned the 2026-09-24 suite red."""

    def test_no_surface_directs_a_finding_into_specs(self):
        offenders = []
        for path in surfaces():
            for pattern in destination_hits(read(path)):
                offenders.append("%s: /%s/" % (path.relative_to(REPO_ROOT), pattern))
        self.assertEqual(
            [], offenders,
            "a /dry-run surface still names `specs/` or a spec file as where a finding goes. "
            "`specs/` is a read-only archive (INV-307) and test_specs_are_frozen.py rejects any "
            "new file there; the finding is drafted into the run's IMPLEMENTED.md entry and "
            "filed as an issue:\n  " + "\n  ".join(offenders))

    def test_every_cited_spec_file_exists(self):
        """A citation of an archive file is provenance; one that resolves to nothing is a
        destination in disguise -- the file the reader is being told to create."""
        missing = []
        for path in surfaces():
            for name in SPEC_PATH.findall(read(path)):
                if not (REPO_ROOT / "specs" / name).is_file():
                    missing.append("%s: specs/%s" % (path.relative_to(REPO_ROOT), name))
        self.assertEqual(
            [], missing,
            "a /dry-run surface names a `specs/*.md` that does not exist -- which reads as a "
            "file to write, not one to read:\n  " + "\n  ".join(missing))

    def test_the_patterns_tell_a_rule_from_a_ban(self):
        """INV-282 -- the positives and the negatives pinned side by side."""
        rules = (
            "⛔ **Write it into `specs/` as you find it — before fixing anything.** "
            "- **File:** `specs/<kebab-case-title>.md`",
            "⛔ **Write each finding into `specs/` as you find it, before fixing anything.**",
            "The moment an observation firms up into a finding, write it into a\n`specs/` file",
            "**Draft the exact message into the spec** so the send costs one approval later.",
        )
        bans = (
            "⛔ **Draft each finding into the run's dated `specs/IMPLEMENTED.md` entry as you "
            "find it** — never into a new file under `specs/`, which is a read-only archive.",
            "Never write it into `specs/`: the archive is frozen.",
            "the 2026-09-24 run that followed the pre-freeze instruction turned the suite red",
        )
        for text in rules:
            with self.subTest(rule=text[:50]):
                self.assertTrue(destination_hits(text),
                                "the scan no longer recognizes an instruction #153 removed")
        for text in bans:
            with self.subTest(ban=text[:50]):
                self.assertEqual([], destination_hits(text),
                                 "the scan flags a prohibition or a live-record destination, so "
                                 "it would demand the rule that forbids writing into `specs/` "
                                 "be deleted")


class TheDurabilityRuleSurvives(unittest.TestCase):
    """Check 2 -- the part of the old instruction worth keeping, with the destination swapped."""

    def test_the_skill_says_a_conversation_is_not_a_record(self):
        flat = norm(read(SKILL))
        self.assertIn("a finding that exists only in the conversation is not recorded", flat,
                      "dry-run/SKILL.md lost the durability rule: a finding held only in "
                      "conversation dies at session end or the next compaction")
        self.assertIn("do not end a run with unwritten findings", flat,
                      "dry-run/SKILL.md lost 'do not end a run with unwritten findings'")
        self.assertIn("four findings held only in conversation", flat,
                      "the history that justifies the rule is gone, so the rule reads as taste")
        self.assertIn("it produced nothing durable", flat,
                      "dry-run/SKILL.md no longer says a run with no durable record produced "
                      "nothing")

    def test_the_command_says_it_too(self):
        self.assertIn("a finding that exists only in the conversation is not recorded",
                      norm(read(COMMAND)),
                      "the slash command dropped the durability rule while swapping the "
                      "destination -- the swap was to keep the rule, not to lose it")

    def test_phase3_keeps_draft_on_sight(self):
        flat = norm(read(PHASE3))
        self.assertIn("working notes, not the record", flat,
                      "phase 3 no longer says the test-notes blocks are not the record")
        self.assertIn("the moment an observation firms up into a finding, draft it into the "
                      "run's ledger entry", flat,
                      "phase 3's test-notes rule no longer says where a firmed-up finding goes")
        self.assertIn("confirm every finding is drafted in the run's ledger entry", flat,
                      "phase 3's stop no longer checks that every finding is written down")


class UpstreamIsMcpServerOnlyAndGated(unittest.TestCase):
    """Check 3 -- the only exceptions to 'nothing leaves the machine', and their limits."""

    def test_both_surfaces_state_the_rule_and_its_limits(self):
        for path in (SKILL, COMMAND):
            with self.subTest(surface=str(path.relative_to(REPO_ROOT))):
                rule = outbound_rule(path)
                self.assertIsNotNone(rule, "%s does not state the outbound rule" % path.name)
                self.assertIn("each under inv-314's gate: show the maintainer the exact text "
                              "and get a yes, given out of character, one record at a time",
                              rule, "the outbound rule is not gated on the maintainer's yes "
                              "for each record")
                self.assertIn("a github issue, or a comment on an existing one, in this "
                              "repository", rule, "the first permitted act is missing")
                # The whole clause, through the colon: the bare prefix still matched when a
                # later edit widened it to "`mcp-server` or `both`" (negative control, #153).
                self.assertIn("`submit_feedback`, only for a finding whose verdict is "
                              "`mcp-server`: certain that the defect is the server's and that "
                              "nothing in the senzing bootcamp needs to change", rule,
                              "the outbound rule does not limit `submit_feedback` to an "
                              "`mcp-server` finding")
                self.assertIn("a `both` finding does not qualify: it gets a github issue with "
                              "the drafted upstream message inside it", rule,
                              "the outbound rule lets a `both` finding go upstream; it gets an "
                              "issue carrying the drafted message instead")
                self.assertIn("everything identifying stripped", rule,
                              "the outbound rule does not require identifying details stripped")
                self.assertIn("never `category='license_request'`", rule,
                              "the outbound rule no longer forbids `license_request`, the path "
                              "that transmits a real name and work email")
                self.assertIn("a yes given in character, while answering as the bootcamper, "
                              "never authorizes either act", rule,
                              "the outbound rule does not rule out acting on the Bootcamper's "
                              "in-character yes -- the collision graduation Step 0 produces")

    def test_no_surface_still_states_a_blanket_ban(self):
        """The old absolute rule contradicts the new one; both cannot stand."""
        stale = (r"never send anything outside the machine",
                 r"send nothing outside the machine",
                 r"do not call `submit_feedback` under any category",
                 r"forbids (?:calling )?`submit_feedback` under any category",
                 r"sending is forbidden by the dry-run skill")
        offenders = ["%s: /%s/" % (p.relative_to(REPO_ROOT), s)
                     for p in surfaces() + [FEEDBACK] for s in stale
                     if re.search(s, norm(read(p)))]
        self.assertEqual([], offenders,
                         "a surface still bans every send outright, contradicting the gated "
                         "`mcp-server` exception:\n  " + "\n  ".join(offenders))


class TheReadmeRecordsTheRework(unittest.TestCase):
    """Check 4 -- `specs/README.md`'s claim was false for as long as `/dry-run` wrote there."""

    def test_the_readme_no_longer_says_none_is_left(self):
        self.assertNotIn("none is left", norm(read(README)),
                         "specs/README.md still claims no spec-writing command is left; "
                         "/dry-run was one until #153")

    def test_the_table_lists_dry_run_with_this_issue(self):
        rows = [line for line in read(README).splitlines()
                if line.startswith("| `/dry-run`")]
        self.assertEqual(1, len(rows), "the 'Commands that wrote here' table has no /dry-run row")
        self.assertIn("#153", rows[0], "the /dry-run row does not name #153")
        self.assertRegex(rows[0], r"(?i)files GitHub issues",
                         "the /dry-run row does not say the command files issues now")

    def test_list_specs_status_is_stated(self):
        flat = norm(read(README))
        self.assertRegex(flat, r"tests/list_specs\.py` is kept \(inv-216\)",
                         "specs/README.md does not state that list_specs.py is kept")
        self.assertIn("which it never lists", flat,
                      "specs/README.md does not say list_specs.py cannot see the GitHub issues "
                      "new findings now become")


class TheCommandSaysItInTheSameWords(unittest.TestCase):
    """#153 -- `.claude/commands/dry-run.md` gets "the same swap, in the same words".

    The pre-freeze destination survived in the command as well as the skill; a command that
    paraphrases the skill is a second wording a later edit updates one home at a time.
    """

    def test_every_lifecycle_clause_is_in_both(self):
        for path in (SKILL, COMMAND):
            flat = norm(read(path))
            missing = [c for c in SAME_WORDS if c not in flat]
            with self.subTest(surface=str(path.relative_to(REPO_ROOT))):
                self.assertEqual([], missing,
                                 "%s does not carry the finding lifecycle in the shared words: "
                                 "%s" % (path.name, missing))

    def test_the_outbound_rule_is_word_for_word(self):
        skill, command = outbound_rule(SKILL), outbound_rule(COMMAND)
        self.assertIsNotNone(skill, "dry-run/SKILL.md does not state the outbound rule")
        self.assertEqual(skill, command,
                         "the command's outbound rule is not the skill's, word for word")


if __name__ == "__main__":
    unittest.main()
