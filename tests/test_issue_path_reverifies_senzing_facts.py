"""The issue-driven path re-asks the live MCP server, and knows how to decline.

`/implement-github-issue` became the repository's development path in #50, and `specs/` froze
in #52 — but the obligations that made the **spec** path safe stayed behind in
`/implement-spec`, which #60 is retiring. Measured before this shipped: grepping both
`.claude/commands/implement-github-issue.md` and its `SKILL.md` for any MCP re-verification
returned **zero matches**.

⛔ **That is a capability, not a formality.** `implement-spec` Step 3.3 was the only place in
the repository telling an implementer to re-ask the server before changing code.
`/feedback-to-issues` re-verifies at **triage** — weeks earlier, against a report that may
since have been fixed, contradicted, or resolved upstream. Retiring `implement-spec` without
this transfer would have left the development loop with **no** re-verification at
implementation time at all, and nothing would have failed to say so.

⚠️ **Three separate rules travel together here, and each fails differently.**

1. **(INV-080) Re-ask the server.** Without it a stale Senzing fact ships with a citation on
   it, which reads as evidence.
2. **(INV-213) An absence claim is a blocker until it names the owning route.** The tools you
   asked and found empty are evidence about *those tools*. This one has already failed in
   production of a registered invariant plus a guard enforcing it, with the offline suite
   certifying both — so it is pinned as a **blocker**, not as advice.
3. **(INV-217) Declining writes to `specs/DECLINED.md`,** whose absence claims carry the
   `MCP-NEGATIVE` marker. That file is **the only Senzing claim in the repo with no
   re-verification path**: a declined item is never implemented, so nothing re-asks it later.

⛔ **This asserts what the command INSTRUCTS, never what a run does.** No offline test can
observe a run calling the MCP server, so nothing here establishes that re-verification
happened — only that the obligation is stated, in terms a later editor cannot quietly drop.
`tests/test_spec_absence_claims_name_their_owner.py` checks the artifacts that result.

⚠️ **A near-identical decline section still exists in `implement-spec/SKILL.md`** while #60 is
blocked on an INV-216 amendment. That duplication is temporary and deliberate; this guard
reads the issue-path copy, and `tests/test_declined_ledger.py` still reads the other.

Stdlib only; the command is read as text (INV-108).

Source issue: #60 (retire `/implement-spec` — the transfer half).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMAND = REPO_ROOT / ".claude" / "commands" / "implement-github-issue.md"


def text():
    return COMMAND.read_text(encoding="utf-8")


def flat(s):
    return re.sub(r"\s+", " ", s).lower()


def section(body, title):
    """The named `## ` section, fence-aware — the decline block quotes `## <issue-slug>`."""
    out, inside, fenced = [], False, False
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            inside = line[3:].strip().startswith(title)
        if inside:
            out.append(line)
    return "\n".join(out)


class TheCommandExists(unittest.TestCase):
    """Anti-vacuity: every assertion below reads this file."""

    def test_the_command_file_exists(self):
        self.assertTrue(
            COMMAND.is_file(),
            "%s does not exist, so every assertion in this module would pass on an empty "
            "read" % COMMAND)


class TheServerIsReAskedBeforeCodeChanges(unittest.TestCase):
    """INV-080 at implementation time, not only at triage."""

    def test_the_obligation_is_stated(self):
        f = flat(text())
        self.assertRegex(
            f, r"re-?verify every senzing fact against the live|re-ask (?:the server|before)",
            "the command no longer tells a run to re-ask the live MCP server before changing "
            "code. Triage re-verifies weeks earlier against a report that may since have been "
            "fixed; without this the loop re-verifies nowhere")

    def test_the_outcome_is_recorded(self):
        f = flat(text())
        self.assertIn(
            "mcp re-check", f,
            "the command never names the `MCP re-check` line, so the re-verification leaves "
            "no trace in the ledger entry and cannot be audited afterwards")

    def test_the_no_senzing_fact_answer_survives(self):
        """Most repo-apparatus work asserts nothing about Senzing; that must stay sayable."""
        self.assertIn(
            "n/a (no senzing fact)", flat(text()),
            "the command dropped `n/a (no Senzing fact)` as a permitted outcome. Without it a "
            "run implementing repo apparatus must either invent a Senzing claim or omit the "
            "line, and omitting it is indistinguishable from never having checked")


class AnAbsenceClaimIsABlocker(unittest.TestCase):
    """INV-213 — the failure that once produced a registered invariant and its guard."""

    def test_owner_checked_is_required(self):
        self.assertIn(
            "owner-checked:", text(),
            "the command no longer requires `owner-checked:` on an absence claim (INV-213). "
            "An empty result from the wrong route reads exactly like evidence of absence")

    def test_it_is_stated_as_a_blocker(self):
        f = flat(text())
        self.assertRegex(
            f, r"blocker",
            "the absence-claim rule is no longer stated as a **blocker**. INV-213 requires a "
            "missing clause to stop implementation and force re-diagnosis — as advice it is "
            "the version that already failed")


class DecliningHasAHome(unittest.TestCase):
    """INV-217 — DECLINED.md is the one Senzing claim nothing re-verifies later."""

    def test_the_decline_section_exists(self):
        self.assertTrue(
            section(text(), "Declining an issue"),
            "the decline section is gone from the issue command. Declining is how a decision "
            "not to build something is recorded; without it the subject returns and the "
            "reasoning against it is lost")

    def test_it_shows_the_marker_form(self):
        s = section(text(), "Declining an issue")
        self.assertIn(
            "MCP-NEGATIVE", s,
            "the decline section no longer shows the `MCP-NEGATIVE` marker form, so the next "
            "entry is written without one — and nothing re-verifies DECLINED.md afterwards")
        self.assertIn("Revisit if", s)

    def test_declining_is_never_unilateral(self):
        s = flat(section(text(), "Declining an issue"))
        self.assertRegex(
            s, r"never decline on your own initiative|maintainer",
            "the decline section no longer reserves the decision to the maintainer. Deciding "
            "NOT to build something is theirs; a run that may decline can retire work nobody "
            "ruled on")

    def test_declined_md_is_marked_live(self):
        """`specs/` is frozen (INV-307) but this file must stay writable."""
        s = flat(section(text(), "Declining an issue"))
        self.assertRegex(
            s, r"declined\.md.{0,80}(?:live|writable)|stays live and writable",
            "the decline section does not say `specs/DECLINED.md` stays live. A reader who "
            "knows only that `specs/` is a read-only archive (INV-307) will not write the "
            "entry at all")


if __name__ == "__main__":
    unittest.main()
