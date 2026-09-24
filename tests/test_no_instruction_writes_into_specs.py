"""No maintainer instruction tells anyone to bring a new file into existence under `specs/`.

`specs/` froze on 2026-09-15 (INV-307) and `tests/test_specs_are_frozen.py` rejects a new
`specs/*.md`. ⛔ **That guard catches a file LANDING; it cannot catch prose telling a maintainer
to create one.** The two failures are a long way apart: the instruction is written once and read
much later, and the person who finally follows it is the one who gets the red suite.

⛔ **That is not hypothetical.** `/compact-dev-environment`'s renumbering procedure required
shipping a `specs/RENUMBERING.md` map. It survived the cutover by **nine days** and was found by
a production-readiness audit reading the procedure, not by any guard — because nobody had
renumbered, so nobody had tried to follow it. A documented procedure that turns the suite red is
a procedure that cannot be executed, and it reads as authoritative right up until someone needs
it (#142).

⚠️ **The matcher is derived from the CLAIM, not from the phrasings that prompted it** (INV-282).
The claim is *"an instruction to bring a file into existence at a path under `specs/`"*. Keying
on `Ship a ...` and `Write nothing under ...` — the two constructions visible on the day this was
written — is the trap this repository keeps recording: a guard repaired from the instances in
front of you passes on them forever and misses the next one. So the verbs are a set, the path
shape is matched generically, and `FIXTURES_THAT_MUST_FLAG` pins constructions nobody has
written yet.

⚠️ **What this does NOT establish.** That an instruction naming an *existing* frozen spec is
fine — it is, and those are deliberately not flagged. That the live exceptions are the right
ones; INV-307 and `docs/FAMILY_WORKFLOW.md` §8 decide that, and this guard reads the exception
list rather than restating it. Nor does it reach a natural-language instruction that names no
path at all ("record it in the archive"), which no regex resolves.

Source issue: #142.

Stdlib only; the tree is read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Where maintainer instructions live. ⛔ `tests/` is excluded deliberately: this very file
#: quotes the offending construction, and a guard that flags its own fixtures is one that gets
#: deleted. `specs/` is excluded because the archive describes itself.
INSTRUCTION_ROOTS = (".claude", "docs")

#: Files whose whole subject is the freeze, and which therefore quote what must not be done.
#: ⚠️ Kept to two named files rather than a pattern -- an exemption that grows by glob is how a
#: guard stops covering the thing it was written for.
QUOTING_THE_RULE = {
    "docs/FAMILY_WORKFLOW.md",
    ".claude/commands/delegate-to-mcp-server.md",
}

#: The live exceptions, read from the rule rather than restated here (INV-308: one definition
#: every consumer reads). An instruction may legitimately say "append to specs/IMPLEMENTED.md".
FREEZE_NOTICE = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"

#: Bringing a file into existence. ⛔ A SET derived from the claim, not the two verbs observed:
#: "ship", "write" and "create" are what the corpus happens to use today, and the others are
#: here because they are how the same instruction would be phrased by someone else.
CREATION_VERB = (r"ship|creat|writ|add|produc|generat|emit|place|put|save|output|author|"
                 r"maintain|record")

#: `<verb> ... specs/<name>.<ext>` within one sentence. The path is matched generically -- any
#: name, any extension -- because pinning `.md` would miss the exact evasion the
#: `.jsonl` justification relied on.
INSTRUCTION = re.compile(
    r"\b(?:%s)\w*\b[^.;\n]{0,80}?`?specs/([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)`?" % CREATION_VERB,
    re.IGNORECASE)

#: ⛔ Constructions the matcher MUST flag, including ones nobody has written. A guard whose
#: fixtures are only the instances it was built from proves it can find what it already found.
FIXTURES_THAT_MUST_FLAG = [
    "Ship a permanent, machine-readable `specs/RENUMBERING.md` map",
    "create specs/audit-log.md when the run finishes",
    "The run writes `specs/findings.yaml` before reporting",
    "generate a specs/coverage.txt summary",
    "and save specs/notes.json alongside it",
]

#: ⛔ Constructions it must NOT flag. Every one of these is legitimate today, and a guard that
#: flags correct prose is relaxed rather than fixed (INV-282).
FIXTURES_THAT_MUST_NOT_FLAG = [
    "see `specs/no-license-path-environment-variable.md`, in the frozen archive",
    "append the outcome to `specs/IMPLEMENTED.md`",
    "record the decision in specs/DECLINED.md with a revisit condition",
    "`specs/INVARIANTS.md` is append-only",
    "read specs/mcp-coverage.jsonl before filing",
    "the spec at specs/todo.md is frozen with the rest of the archive",
]


def live_exceptions():
    """The filenames §8 lists as still written to, read from the page itself."""
    text = FREEZE_NOTICE.read_text(encoding="utf-8")
    start = text.find("## 8.")
    if start == -1:
        return set()
    end = text.find("\n## ", start + 1)
    section = text[start:end if end != -1 else len(text)]
    return set(re.findall(r"`specs/([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)`", section))


def offenders():
    """[(path, line_no, text)] for each instruction to create a file under `specs/`."""
    allowed = live_exceptions()
    out = []
    for root in INSTRUCTION_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".py", ".sh"}:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in QUOTING_THE_RULE:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for n, line in enumerate(lines, 1):
                for m in INSTRUCTION.finditer(line):
                    if m.group(1) not in allowed:
                        out.append((rel, n, line.strip()[:110]))
    return out


class TheScanCanRun(unittest.TestCase):
    """INV-265 -- an empty corpus or an empty exception list satisfies the check trivially."""

    def test_the_instruction_roots_exist(self):
        missing = [r for r in INSTRUCTION_ROOTS if not (REPO_ROOT / r).is_dir()]
        self.assertEqual([], missing, "instruction root(s) absent: %s" % ", ".join(missing))

    def test_the_live_exceptions_were_read(self):
        found = live_exceptions()
        self.assertIn(
            "IMPLEMENTED.md", found,
            "§8 of %s did not parse into a list of live exceptions (%s). Without it every "
            "legitimate 'append to the ledger' instruction reads as a violation"
            % (FREEZE_NOTICE, sorted(found)))


class TheMatcherIsDerivedFromTheClaim(unittest.TestCase):
    """⛔ INV-282 -- pinned in both directions, including phrasings nobody has written."""

    def test_it_flags_every_creation_construction(self):
        allowed = live_exceptions()
        missed = [f for f in FIXTURES_THAT_MUST_FLAG
                  if not [m for m in INSTRUCTION.finditer(f) if m.group(1) not in allowed]]
        self.assertEqual(
            [], missed,
            "the matcher does not see instruction(s) to create a file under specs/: %s. It has "
            "been narrowed to the phrasings already observed, which is the defect INV-282 names"
            % "; ".join(missed))

    def test_it_flags_none_of_the_legitimate_ones(self):
        allowed = live_exceptions()
        wrong = [f for f in FIXTURES_THAT_MUST_NOT_FLAG
                 if [m for m in INSTRUCTION.finditer(f) if m.group(1) not in allowed]]
        self.assertEqual(
            [], wrong,
            "the matcher flags correct prose: %s. A guard that fires on legitimate text is "
            "relaxed rather than fixed, and this one would train its reader to ignore it"
            % "; ".join(wrong))


class NoInstructionCreatesASpecFile(unittest.TestCase):
    def test_no_instruction_directs_a_write_into_specs(self):
        found = offenders()
        self.assertEqual(
            [], found,
            "instruction(s) direct a file to be created under `specs/`, which INV-307 freezes "
            "and tests/test_specs_are_frozen.py rejects. Following them turns the suite red, so "
            "the procedure cannot be executed as documented:\n  %s"
            % "\n  ".join("%s:%d  %s" % row for row in found))
