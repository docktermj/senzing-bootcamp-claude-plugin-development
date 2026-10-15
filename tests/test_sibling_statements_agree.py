"""Sibling statements in Modules 0, 1 and 4 and the onboarding files agree (#617).

The production-readiness audit of 2026-10-14 (sweep C1) found six pairs of sibling statements
that disagreed. Each was fixed in place; this file holds each pair together so neither side
drifts back:

1. Module 0's single batched close-out write carries `step_history["entity_resolution_concepts"]`,
   the field `module-completion.md` Step 1 and `ground-rules.md` "Progress and state" require.
2. Module 1's Desired Output `**Format**` line lists the 6d options, ending in the Bootcamper's
   words for "Something else", and Step 6c (an open question) is not called an option reply.
3. The transition summary in `ground-rules.md` defers to the three post-yes shapes (INV-236):
   the "Are you done modifying the model and effort?" gate only when the dial is not yet set.
4. The onboarding preface detects OS/architecture; it persists nothing (Bootcamp preparation's
   consolidated write does).
5. Module 4 Step 8b sub-step 1 computes the collected total with sub-step 4's sample-aware
   definition, the one Module 6 recomputes.
6. Module 4 names no CORD dataset in its own text; the names come from `get_sample_data`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE_0 = SKILLS / "module-00-entity-resolution-concepts" / "SKILL.md"
MODULE_COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"
PHASE1_DISCOVERY = SKILLS / "module-01-business-problem" / "phase1-discovery.md"
PHASE2_CONFIRM = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
GROUND_RULES = SKILLS / "bootcamp-onboarding" / "ground-rules.md"
ONBOARDING_SKILL = SKILLS / "bootcamp-onboarding" / "SKILL.md"
MODULE_4 = SKILLS / "module-04-data-collection" / "SKILL.md"

#: The CORD dataset names `get_sample_data(dataset='list')` serves (server 1.38.2, 2026-10-15).
CORD_NAMES = ("Las Vegas", "London", "Moscow")


def _read(path):
    return path.read_text(encoding="utf-8")


def _flat(text):
    """Collapse whitespace so a phrase wrapped across lines still matches."""
    return re.sub(r"\s+", " ", text)


def _section(text, start, end):
    """Text from the first line matching `start` up to the next line matching `end`."""
    match = re.search(start, text, re.M)
    if not match:
        raise AssertionError(f"no section matches {start!r}")
    rest = text[match.end():]
    stop = re.search(end, rest, re.M)
    return rest[: stop.start()] if stop else rest


class ModuleZeroWritesStepHistory(unittest.TestCase):
    def test_module_completion_still_requires_the_field(self):
        self.assertIn('step_history["<module>"]', _read(MODULE_COMPLETION))

    def test_the_single_batched_write_carries_step_history(self):
        write = _section(
            _read(MODULE_0), r"^1\. In `config/bootcamp_progress\.json` \(a single batched write\)", r"^2\. "
        )
        flat = _flat(write)
        self.assertIn('step_history["entity_resolution_concepts"]', flat)
        self.assertIn('"last_completed_step"', flat)
        self.assertIn('"updated_at": "<ISO 8601>"', flat)


class ModuleOneFormatMatchesTheOptions(unittest.TestCase):
    def test_format_line_lists_the_6d_options(self):
        sixd = _section(_read(PHASE1_DISCOVERY), r"^- \*\*6d \(desired outcome\)\.\*\*", r"^\*\(Internal")
        options = re.findall(r"^  > \d\. \*\*(.+?)\*\*", sixd, re.M)
        self.assertEqual(
            options, ["A clean master list", "An API", "Reports", "Something else"],
            "the 6d options changed; update the Desired Output Format line to match",
        )
        fmt = re.search(r"^\*\*Format\*\*: \[(.+)\]$", _read(PHASE2_CONFIRM), re.M)
        self.assertIsNotNone(fmt, "the Desired Output template has no **Format** line")
        self.assertIn(
            "Master list / API / Reports / <the Bootcamper's words for \"Something else\">", fmt.group(1)
        )
        self.assertNotIn("Export", fmt.group(1))

    def test_6c_is_not_called_an_option_reply(self):
        flat = _flat(_read(PHASE2_CONFIRM))
        self.assertNotIn("option replies at Steps 6b–6d", flat)
        self.assertIn("the Step 6c answer for source count", flat)


class TransitionSummaryDefersToTheThreeShapes(unittest.TestCase):
    def test_summary_shows_the_gate_only_when_the_dial_is_not_yet_set(self):
        summary = _flat(
            _section(_read(GROUND_RULES), r"^- After an affirmative module-transition", r"^## ")
        )
        self.assertIn("three shapes above", summary)
        self.assertIn("INV-236", summary)
        self.assertRegex(summary, r"when the dial is not yet set, .*Are you done modifying the model and effort")
        self.assertRegex(summary, r"when the dial is already set, .*no gate")


class PrefaceDetectsButDoesNotPersist(unittest.TestCase):
    def test_prerequisite_bullet_does_not_persist(self):
        bullet = re.search(r"^- \*\*Prerequisite check\*\* - (.+?)(?=^- |\Z)", _read(ONBOARDING_SKILL), re.M | re.S)
        self.assertIsNotNone(bullet, "the onboarding sequence has no Prerequisite check bullet")
        text = _flat(bullet.group(1))
        self.assertNotRegex(text, r"(?i)detect and persist")
        self.assertIn("Bootcamp preparation persists", text)


class ModuleFourHasOneCollectedTotal(unittest.TestCase):
    DEFINITION = "each source's `sample:` `record_count` where it has a `sample:` block"

    def test_sub_step_1_uses_sub_step_4_definition(self):
        step = _section(_read(MODULE_4), r"^1\. \*\*Read the persisted inputs\.\*\*", r"^   - ")
        flat = _flat(step)
        self.assertIn("sub-step 4 records as `collected_total`", flat)
        self.assertIn(self.DEFINITION, flat)

    def test_sub_step_4_still_states_it(self):
        self.assertIn(self.DEFINITION, _flat(_read(MODULE_4)))


class ModuleFourNamesNoCordDataset(unittest.TestCase):
    def test_no_hardcoded_dataset_name(self):
        text = _read(MODULE_4)
        for name in CORD_NAMES:
            with self.subTest(name=name):
                self.assertNotIn(name, text, f"Module 4 hardcodes the CORD dataset name {name!r}")
        self.assertIn("`get_sample_data`", text)


if __name__ == "__main__":
    unittest.main()
