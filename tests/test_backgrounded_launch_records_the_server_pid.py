"""A backgrounded launch whose pid is captured must not be chained with `&&`.

Truth Set visualization records the visualization server's pid at launch (Phase 1, 2.3) and uses
it at teardown (Phase 2, Step 4) as "the only unambiguous handle on the server". On a phase-3
walk (2026-08-22) the recorded pid was **not** the server's: `kill <recorded pid>` returned
success, the process disappeared, and port 8080 stayed bound by the still-running server.

The cause is composition, not either instruction. Step 2 requires the project env sourced before
anything that touches the Senzing library, and 2.3 gives the launch as a bare backgrounded
command whose `$!` is therefore the server. Composed the obvious way --
`. src/scripts/senzing-env.sh && python3 <server> … &` -- the `&` binds to the whole `&&` list,
so the shell backgrounds a **subshell**, `$!` names that subshell, and the server is its child
with a different pid. Killing the recorded pid orphans a running server holding the port.

Measured on bash while implementing: composed with `&&`, the recorded `$!` and the server's pid
differed; written as separate statements they were the same number.

⛔ **A silently wrong pid is worse than a missing one.** `phase2-close.md`'s port-based fallback
triggered on **absence**, and this failure presents as **presence** -- a handle that looks
recorded, kills something, and reports success. What contained it was already in the file and
worked exactly as designed: the mandatory port poll ("the port being free is the exit
condition", INV-223). `ThePortPollStaysMandatory` pins that, because it is the check that turned
a silent orphan into a visible failure.

Per **INV-246** the launch sites are derived by scanning every shipped markdown file for a
backgrounded command whose pid is captured, never by listing paths -- a launch example added to
another module later is covered without editing this file.

Source spec: `specs/recorded-server-pid-is-the-subshell-not-the-server.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_03B = SKILLS / "module-03b-truthset-visualization"
PHASE1 = MODULE_03B / "phase1-visualization.md"
PHASE2_CLOSE = MODULE_03B / "phase2-close.md"
API_REFERENCE = MODULE_03B / "visualization-api-reference.md"

#: A fenced shell block. `sh` and `console` included so a future example in either is scanned.
FENCE = re.compile(r"```(?:bash|sh|shell|console)\n(.*?)```", re.S)

#: The capture that makes a backgrounded command's pid load-bearing.
CAPTURES_PID = re.compile(r"=\s*\$!")


def logical_lines(block):
    """Shell lines with backslash continuations joined, so a wrapped command is one unit.

    Line-scoped by design (#424): the text is a fenced shell block, where a newline ends a
    command unless a backslash continues it, so a logical line is the unit the shell runs.
    """
    joined, buffer = [], ""
    for raw in block.split("\n"):
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1].strip() + " "
            continue
        joined.append(buffer + stripped.strip())
        buffer = ""
    if buffer:
        joined.append(buffer)
    return [line for line in joined if line]


def backgrounded(line):
    """True when the line ends by backgrounding a command (a lone trailing `&`)."""
    return line.endswith("&") and not line.endswith("&&")


def launch_blocks():
    """(path, block) for every shipped shell block that backgrounds AND captures a pid."""
    for path in sorted(SKILLS.glob("**/*.md")):
        text = path.read_text(encoding="utf-8")
        for block in FENCE.findall(text):
            if CAPTURES_PID.search(block) and any(
                    backgrounded(line) for line in logical_lines(block)):
                yield path, block


def read(path):
    return path.read_text(encoding="utf-8")


def flat(path):
    return re.sub(r"\s+", " ", read(path))


class TheScanFindsSomethingToCheck(unittest.TestCase):
    def test_at_least_one_launch_block_is_found(self):
        found = list(launch_blocks())
        self.assertGreater(
            len(found), 0,
            "no shipped shell block both backgrounds a command and captures its pid — the "
            "launch example moved or changed shape, and this guard is inspecting nothing")

    def test_the_truth_set_launch_is_among_them(self):
        paths = {p for p, _ in launch_blocks()}
        self.assertIn(
            PHASE1, paths,
            "phase1-visualization.md 2.3 no longer contains a backgrounded launch that "
            "captures a pid; it is the site this guard exists for")


class NoCapturedPidComesFromAChainedLaunch(unittest.TestCase):
    def test_no_backgrounded_launch_is_chained_with_and(self):
        offenders = []
        for path, block in launch_blocks():
            for line in logical_lines(block):
                if backgrounded(line) and "&&" in line:
                    offenders.append("%s: %s" % (path.name, line[:90]))
        self.assertEqual(
            [], offenders,
            "a shell block captures `$!` from a command chained with `&&`: %s. The `&` binds "
            "to the whole list, so `$!` is the subshell and the server is its child with a "
            "different pid — `kill` then exits 0 while the port stays bound. Put the "
            "prerequisite on its own line and background only the server" % offenders)

    def test_the_env_source_is_a_separate_statement_in_the_launch_block(self):
        """The specific composition the bootcamp's own Step 2 requirement invites."""
        blocks = [b for p, b in launch_blocks() if p == PHASE1]
        self.assertTrue(blocks, "no launch block found in phase1-visualization.md")
        for block in blocks:
            lines = logical_lines(block)
            sourcing = [line for line in lines
                        if re.match(r"(?:\.|source)\s+\S*senzing-env", line)]
            with self.subTest(block=block[:40]):
                self.assertTrue(
                    sourcing,
                    "2.3's launch block does not source the project env at all, so a reader "
                    "supplies the composition themselves — which is how the defect arose")
                for line in sourcing:
                    self.assertFalse(
                        backgrounded(line) or "&&" in line,
                        "the env sourcing shares a line with the backgrounded launch: %r"
                        % line)


class TheHazardIsStatedWhereTheLaunchIs(unittest.TestCase):
    def test_phase_one_states_the_subshell_hazard(self):
        self.assertRegex(
            flat(PHASE1), r"(?i)`A && B &`.{0,80}subshell",
            "2.3 does not state that `A && B &` makes `$!` the subshell, so the launch shape "
            "reads as style rather than as the thing that makes the pid correct")

    def test_phase_one_says_a_wrong_pid_is_worse_than_a_missing_one(self):
        self.assertRegex(
            flat(PHASE1), r"(?i)presents as \*\*presence\*\*|presents as presence",
            "2.3 does not say why a silently wrong pid is worse than a missing one — the "
            "fallback triggers on absence, and this failure looks like presence")

    def test_the_canonical_contract_carries_it_too(self):
        self.assertRegex(
            flat(API_REFERENCE), r"(?i)sole\W{0,2} backgrounded command",
            "the canonical 'Identifying the server process' rule does not scope `$!` to a "
            "sole backgrounded command, so the parallel sites can drift from 2.3")

    def test_powershell_is_recorded_as_unaffected(self):
        for path in (PHASE1, API_REFERENCE):
            with self.subTest(file=path.name):
                self.assertRegex(
                    flat(path),
                    r"(?i)PassThru.{0,160}(?:unaffected|does not have this hazard)"
                    r"|(?:unaffected|does not have this hazard).{0,160}PassThru",
                    "%s does not record that PowerShell is unaffected, inviting a needless "
                    "change to the one launch shape that was always correct" % path.name)


class TheFallbackCoversAWrongPidNotOnlyAMissingOne(unittest.TestCase):
    def test_phase_two_close_covers_a_dead_pid_with_a_bound_port(self):
        self.assertRegex(
            flat(PHASE2_CLOSE),
            r"(?i)recorded pid is gone but the port still answers"
            r"|pid does not stop the server",
            "Step 4's port fallback still reads as triggering only on a MISSING pid. The case "
            "that occurred is a pid that is present, whose kill exits 0, and whose port stays "
            "bound")

    def test_the_canonical_contract_covers_both_cases(self):
        self.assertRegex(
            flat(API_REFERENCE), r"(?i)covers \*\*two\*\* cases|covers two cases",
            "the canonical fallback rule does not say it covers both a missing and a wrong "
            "pid, so a reader implementing from it reproduces the absence-only fallback")


class ThePortPollStaysMandatory(unittest.TestCase):
    """Criterion 4. This poll is what turned a silent orphan into a visible failure."""

    def test_the_port_must_be_confirmed_free_before_the_purge(self):
        text = flat(PHASE2_CLOSE)
        self.assertRegex(
            text, r"(?i)Confirm the port is free",
            "Step 4 no longer requires confirming the port is free")
        self.assertRegex(
            text, r"(?i)Do not start step 4 until the port is confirmed free",
            "the gate that keeps the irreversible purge behind a confirmed-free port is gone "
            "— it is the check that detected the wrong pid in the first place")

    def test_the_kills_exit_status_is_not_evidence(self):
        self.assertRegex(
            flat(API_REFERENCE),
            r"(?i)exit condition is the port|not evidence the server stopped",
            "the contract no longer says the port rather than the kill's exit status is the "
            "exit condition — the exact inference that made the wrong pid look like success")


if __name__ == "__main__":
    unittest.main()
