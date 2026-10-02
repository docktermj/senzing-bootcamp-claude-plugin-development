"""The model/effort switch trigger compares against the live session, never stage-to-stage.

`ground-rules.md` states the rule with two ⛔ markers and a worked example: compare the stage's
recommendation against **what the bootcamper is running right now**, because comparing it against
the *previous stage's recommendation* would find "unchanged" for someone demonstrably on a
stronger model and never offer them the switch — "silently defeating the purpose of the invariant
this superseded" (INV-138, superseding INV-137's trigger).

`bootcamp-preparation/SKILL.md` Step 3a summarized that as "when the recommendation changes …
when it is unchanged", which is the stage-to-stage comparison the ⛔ forbids by name.

This was not hypothetical. The stage table recommends Sonnet 5.5 at medium effort for four
consecutive stages — Onboarding, Bootcamp preparation, Entity Resolution Concepts and Discover
the Business Problem — so on a live walk (2026-08-12) the two files produced different behavior
at the same moment: reading `ground-rules.md`, a bootcamper on Opus 5.5 was asked to switch;
reading the summary, the recommendation was "unchanged" and no question was asked. For the first
four stages of every Core run the summary suppressed the question entirely.

The summary was the dangerous half precisely because it was the readable half: short, declarative,
and sitting at the end of the step whose whole purpose is "ask nothing here", with no signal that
its one clause compressed a 17-line rule with a per-dial resolution procedure.

Both sentences were individually well-formed prose, which is why no test caught the divergence.
What is guarded here is the *direction* of the comparison, wherever it is described.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
PREP = PLUGIN / "skills" / "bootcamp-preparation" / "SKILL.md"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"

#: Phrasings that describe the trigger as a stage-to-stage change in the recommendation.
PARAPHRASE = re.compile(
    r"(?i)recommendation changes|when it is unchanged|recommendation is unchanged|"
    r"previous stage'?s recommendation"
)

#: Vocabulary confirming the passage is about the model/effort nudge at all.
NUDGE_VOCAB = re.compile(r"(?i)switch question|model/effort|model and effort|reasoning effort|recommendation")

#: A passage may name the wrong comparison in order to FORBID it — which is exactly what
#: `ground-rules.md` and `docs/model-selection.md` do. Only negated mentions are exempt.
NEGATED = re.compile(r"(?i)(?:not|never|rather than|instead of)\s+(?:from|against|the|comparing)")

WINDOW = 260
NEGATION_REACH = 160


def shipped_markdown():
    """Skill and command prose — everything a guide reads at runtime."""
    return sorted(PLUGIN.rglob("*.md"))


def offenses():
    found = []
    for path in shipped_markdown():
        flat = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for match in PARAPHRASE.finditer(flat):
            window = flat[max(0, match.start() - WINDOW):match.end() + WINDOW]
            if not NUDGE_VOCAB.search(window):
                continue
            near = flat[max(0, match.start() - NEGATION_REACH):match.end() + NEGATION_REACH]
            if NEGATED.search(near):
                continue
            found.append("%s: %s" % (path.relative_to(REPO_ROOT), window[:220]))
    return found


class TheTriggerIsSessionRelativeEverywhere(unittest.TestCase):
    def test_the_scan_reaches_the_shipped_prose(self):
        files = shipped_markdown()
        self.assertGreater(len(files), 30, "the shipped markdown corpus was not found")
        corpus = " ".join(p.read_text(encoding="utf-8") for p in files)
        self.assertRegex(corpus, NUDGE_VOCAB, "no nudge vocabulary found — scan is vacuous")

    def test_no_file_describes_the_trigger_as_a_stage_to_stage_change(self):
        found = offenses()
        self.assertEqual(
            [],
            found,
            "A shipped file describes the model/effort switch trigger as a change in the "
            "RECOMMENDATION between stages. Four consecutive stages share one recommendation, "
            "so that reading suppresses the question through the opening of every Core run "
            "(INV-138). Compare against what the bootcamper is running now:\n  "
            + "\n  ".join(found),
        )


class PreparationDefersRatherThanParaphrases(unittest.TestCase):
    def flat(self):
        return re.sub(r"\s+", " ", PREP.read_text(encoding="utf-8"))

    def test_it_states_the_session_relative_trigger(self):
        self.assertRegex(
            self.flat(),
            r"(?i)differs from what the bootcamper is running right now",
            "Step 3a must state the comparison against the live session",
        )

    def test_it_names_the_forbidden_direction_as_forbidden(self):
        self.assertRegex(
            self.flat(),
            r"(?i)never against the previous stage'?s recommendation",
        )

    def test_it_defers_to_the_authoritative_clause(self):
        flat = self.flat()
        self.assertRegex(flat, r"(?i)ground-rules\.md")
        self.assertRegex(flat, r"(?i)authoritative")

    def test_it_does_not_restate_the_per_dial_procedure(self):
        """Two copies is how this drifted; the summary carries direction only."""
        flat = self.flat()
        self.assertRegex(flat, r"(?i)do not restate that procedure here")
        self.assertNotRegex(
            flat,
            r"(?i)exposed nowhere",
            "that is ground-rules.md's per-dial reasoning — deferring means not copying it",
        )


class TheAuthoritativeClauseIsUntouched(unittest.TestCase):
    """The spec's instruction: make the summary agree, do not re-litigate the rule."""

    def test_ground_rules_still_states_the_rule_with_its_worked_example(self):
        flat = re.sub(r"\s+", " ", GROUND_RULES.read_text(encoding="utf-8"))
        self.assertRegex(flat, r"(?i)not against the previous stage'?s recommendation")
        self.assertRegex(flat, r"(?i)silently defeating the purpose of the invariant")


if __name__ == "__main__":
    unittest.main()
