"""The audit skill's reading step returns the NEWEST ledger entries, not the oldest.

`production-readiness-audit` Step 1.2 tells the auditor to read *"the newest five or so"*
audit entries and gives the command to get them. Until 2026-09-02 that command ended
`| tail -8`, and `specs/IMPLEMENTED.md` is newest-first — its own header says so — so it
returned the OLDEST eight. A run that day was handed `production-readiness-audit-2026-08-11`
plus seven July `deep-dive-audit-*` entries; the five from the previous day never appeared.

⚠️ **The failure is silent, which is the severity argument.** A plausible list of real audit
entries comes back either way. The run that found it noticed only because the previous
audit's date was independently known.

⚠️ **And the skill's own prose is the argument against its command.** Two paragraphs below
Step 1.2 it warns that *"a reading list fixed at the oldest six routed around exactly
that"* — the defect the ⚠️ describes, produced by the command rather than by a hardcoded
list.

This guards the direction, not the wording: any command extracting audit headings from a
newest-first ledger must take from the head.

⛔ (INV-246) The commands are found by SCANNING the skill for the ledger-reading pattern,
not by a pinned line number — the step has been renumbered before.

Stdlib only; nothing under ``plugins/`` is imported (INV-108). `.claude/` does not ship
(`propagate.sh` mirrors `plugins/`, `.claude-plugin/`, `docs/` and `README.md`), so this
guards a maintainer-side file, as `test_dry_run_states_no_hook_count.py` already does.
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "production-readiness-audit" / "SKILL.md"
LEDGER = REPO / "specs" / "IMPLEMENTED.md"

#: A shell line that greps audit headings out of the ledger, however it is worded.
#: Line-scoped by design (#425): the command sits in a fence, where a newline ends it.
#: ⚠️ Matched LINE-wise, not with a pipe-excluding character class: the grep pattern
#: itself contains an escaped `\|` alternation, so `[^|]*` stops inside the quotes and
#: the scan finds nothing — which looks identical to a skill with no such command.
def ledger_reading_commands():
    return [
        line for line in SKILL.read_text(encoding="utf-8").splitlines()
        if "grep" in line and "IMPLEMENTED.md" in line
        and ("production-readiness-audit" in line or "deep-dive-audit" in line)
    ]


class TheReadingStepTakesFromTheNewestEnd(unittest.TestCase):
    def test_the_scan_finds_the_command(self):
        """A scan matching nothing would make the assertion below vacuous."""
        self.assertTrue(
            ledger_reading_commands(),
            "no ledger-reading command found in the audit skill. Step 1.2's instruction to "
            "read the newest entries is unactionable without one, or the command's shape "
            "changed and this guard has stopped reading it.",
        )

    def test_the_ledger_really_is_newest_first(self):
        """The premise. If the ledger were oldest-first, `tail` would be correct.

        Checked by reading the two most recent dated headings rather than trusting the
        file's own header sentence — the header is prose and could itself go stale.
        """
        dates = re.findall(r"^## (?:production-readiness-audit|deep-dive-audit)-(\d{4}-\d{2}-\d{2})",
                           LEDGER.read_text(encoding="utf-8"), re.M)
        self.assertGreaterEqual(len(dates), 2, "fewer than two dated audit entries")
        self.assertGreaterEqual(
            dates[0], dates[-1],
            "specs/IMPLEMENTED.md is not newest-first — the first dated audit heading is "
            f"{dates[0]} and the last is {dates[-1]}. If the file's order has genuinely "
            "been reversed, this whole guard is inverted and the skill's command should "
            "change with it.",
        )

    def test_no_reading_command_takes_from_the_oldest_end(self):
        offenders = [c for c in ledger_reading_commands() if re.search(r"\|\s*tail\b", c)]
        self.assertEqual(
            [], offenders,
            "a ledger-reading command pipes to `tail`, which on a newest-first file returns "
            f"the OLDEST entries: {offenders}. The skill asks for the newest, and the run "
            "that hit this was handed a reading list from six weeks earlier.",
        )

    def test_a_reading_command_takes_from_the_newest_end(self):
        """Negative form: banning `tail` is not the same as getting `head`."""
        self.assertTrue(
            any(re.search(r"\|\s*head\b", c) for c in ledger_reading_commands()),
            "no ledger-reading command pipes to `head`. Removing `tail` without adding "
            "`head` leaves the auditor reading every audit entry ever written, which is "
            "the instruction going unfollowed by a different route.",
        )
