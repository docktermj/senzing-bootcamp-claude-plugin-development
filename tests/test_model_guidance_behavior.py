"""Model/effort guidance is unconditional — no question, no preference, no modes.

Renamed from `test_model_guidance_modes.py` on 2026-07-26, because the modes it was
written to protect are gone and a test file named after them would mislead.

**This design has now swung five times**, every swing a deliberate decision:

| | Behavior |
|---|---|
| INV-062 | non-blocking suggestion |
| INV-063 | blocking switch question when the recommendation changes |
| INV-069 | plus a second confirmation gate |
| INV-119/INV-120 | all of it conditional on an `advisory`/`off`/`prompt` preference |
| INV-137 | unconditional again; the preference and its question retired |
| **2026-07-26** | the trigger becomes the Bootcamper's *current setting*, not the previous stage |

So the risk this file guards is specific and has materialized before: a future edit
quietly reinstating one of the retired shapes, or a stale `model_guidance` read
surviving in a file nobody thought to check. What must hold now:

1. The capture question exists **nowhere**.
2. No shipped skill instructs the guide to read, honor or persist `model_guidance`.
3. The done-modifying gate lives in exactly one file, `ground-rules.md`, and is scoped to
   **no** mode. (Two files until #293: graduation carried its own copy, and now points to
   ground-rules instead.)
4. The requirements INV-137 explicitly retains from INV-120 — separate dials,
   changeable at any time, a below-current recommendation flagged as a downgrade —
   still appear. The downgrade flagging now applies to **both** branches: the pause
   is symmetric, so a step down is asked, and an unexplained downgrade prompt reads
   as being asked to accept a worse experience.
5. The switch fires only when the recommendation differs from what the Bootcamper is
   **running**, so someone already on the recommended setting is never asked, and
   only the dial that actually differs is named.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
GROUND_RULES = os.path.join(PLUGIN, "skills", "bootcamp-onboarding", "ground-rules.md")
GRADUATION = os.path.join(PLUGIN, "skills", "graduation", "SKILL.md")
PREPARATION = os.path.join(PLUGIN, "skills", "bootcamp-preparation", "SKILL.md")
MODEL_SELECTION = os.path.join(PLUGIN, "docs", "model-selection.md")

QUESTION = "How would you like model guidance handled?"
DONE_GATE = "Are you done modifying the model and effort?"
SWITCH_QUESTION = "Would you like to switch to"

# Phrasings that would mean a file is treating the retired preference as live.
LIVE_PREFERENCE_USE = re.compile(
    r"(Read|read|honou?r|Honou?r|persist|Persist|carry)\s+[^.\n]{0,40}`model_guidance`"
    r"|`model_guidance`[^.\n]{0,30}(from|to)\s+`config/bootcamp_preferences\.yaml`",
)

# Mode-gated phrasings retired by INV-137.
RETIRED_MODE_PHRASINGS = (
    "belongs to `prompt` alone",
    "Under `advisory`",
    "treat as `advisory`",
    "`advisory` (the default)",
    "absent-means-`advisory`",
    "The three modes",
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def flat(path):
    """`read`, with runs of whitespace collapsed to single spaces.

    These files are wrapped prose. A phrase assertion against the raw text is
    really an assertion about where the line breaks fall, so re-flowing a
    paragraph — an edit with no meaning — fails it. Use this for any check about
    what a file *says*; use `read` only when layout genuinely matters.
    """
    return re.sub(r"\s+", " ", read(path))


def shipped_markdown():
    for dirpath, dirnames, filenames in os.walk(PLUGIN):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


def skill_markdown():
    root = os.path.join(PLUGIN, "skills")
    return [p for p in shipped_markdown() if os.path.abspath(p).startswith(os.path.abspath(root))]


class TestTheQuestionIsGone(unittest.TestCase):

    def test_no_shipped_file_asks_it(self):
        offenders = [
            os.path.relpath(p, REPO_ROOT) for p in shipped_markdown() if QUESTION in read(p)
        ]
        self.assertEqual(
            [],
            offenders,
            f"the retired model-guidance question is asked in: {offenders}. INV-137 "
            "removes it entirely — the choice is not the Bootcamper's to make.",
        )

    def test_preparation_records_that_it_is_retired(self):
        """A note in its place, so a future edit does not silently re-add it."""
        text = read(PREPARATION)
        self.assertRegex(
            text,
            r"no `model_guidance` preference|model[- ]guidance question.{0,40}retired"
            r"|retired.{0,60}model.guidance",
            "Bootcamp preparation should state that the question is retired, so the "
            "absence is deliberate rather than looking like an omission.",
        )

    def test_the_consolidated_write_does_not_persist_it(self):
        text = read(PREPARATION)
        write_step = text[text.index("## 6.") : text.index("## 7.")]
        self.assertNotRegex(
            write_step,
            r"`model_guidance`\s*\(",
            "Step 6 must not persist model_guidance — the key is retired (INV-137)",
        )


class TestNoFileTreatsThePreferenceAsLive(unittest.TestCase):

    def test_no_skill_reads_or_honors_it(self):
        offenders = []
        for path in skill_markdown():
            for n, line in enumerate(read(path).splitlines(), 1):
                if LIVE_PREFERENCE_USE.search(line):
                    offenders.append(f"{os.path.relpath(path, REPO_ROOT)}:{n}")
        self.assertEqual(
            [],
            offenders,
            f"file(s) still instruct reading/honoring `model_guidance`: {offenders}. "
            "INV-137 retires the key; a stale value must not be honored.",
        )

    def test_no_retired_mode_phrasing_survives(self):
        offenders = []
        for path in shipped_markdown():
            text = read(path)
            for phrase in RETIRED_MODE_PHRASINGS:
                if phrase in text:
                    offenders.append(f"{os.path.relpath(path, REPO_ROOT)}: {phrase!r}")
        self.assertEqual(
            [],
            offenders,
            f"mode-gated phrasing retired by INV-137 survives: {offenders}",
        )

    def test_no_file_counts_it_among_the_capture_questions(self):
        """Preparation's Step 0 said the preferences rule covers all capture questions,
        "not just model guidance", as though that were still one of them (#234).

        Matched on flattened text, so a line break inside the phrase cannot hide it.
        Negative-controlled by restoring the phrase to bootcamp-preparation/SKILL.md.
        """
        offenders = [
            os.path.relpath(p, REPO_ROOT) for p in shipped_markdown()
            if re.search(r"(?i)not just model guidance", flat(p))
        ]
        self.assertEqual(
            [],
            offenders,
            f"these files count model guidance among the capture questions: {offenders}. "
            "INV-137 retires the question, so no preference rule is scoped against it.",
        )


class TestTheUnconditionalFlowIsIntact(unittest.TestCase):
    """The behavior INV-137 restores must actually be described."""

    def test_ground_rules_carries_the_switch_question(self):
        self.assertIn(SWITCH_QUESTION, read(GROUND_RULES))

    def test_graduation_points_to_it_instead_of_copying_it(self):
        """Graduation reads the nudge through ground-rules since #293."""
        text = flat(GRADUATION)
        self.assertNotIn(SWITCH_QUESTION, text)
        self.assertIn('`../bootcamp-onboarding/ground-rules.md` → "Module start banners and '
                      'transitions"', text)

    def test_the_gate_lives_only_in_ground_rules(self):
        expected = {os.path.abspath(GROUND_RULES)}
        found = {os.path.abspath(p) for p in skill_markdown() if DONE_GATE in read(p)}
        self.assertEqual(
            expected,
            found,
            "the done-modifying gate must live only in ground-rules.md; graduation and "
            "every other skill point to it (#293)",
        )

    def test_the_gate_follows_a_yes_and_nothing_else(self):
        """The gate follows a yes that still needs one, and nothing else (INV-137/INV-236).

        The wording narrowed on 2026-08-14: INV-236 added two post-yes shapes in which the
        Bootcamper has *already* set the dial, and gating those asks what the transcript has
        answered. So "follows a **yes** to the switch and nothing else" became "a **yes that
        still needs one**". The guarantee this test exists for is unchanged and is now pinned
        in **both** halves rather than one — the gate never follows a decline, and never
        follows a yes whose dial is already set.
        """
        text = read(GROUND_RULES)
        self.assertRegex(
            text,
            r"follows a \*\*yes that still needs one\*\*",
            "ground-rules must state which yes the confirmation gate follows "
            "(INV-137/INV-236)",
        )
        self.assertRegex(
            text,
            r"(?i)never after a\s+decline",
            "the gate must never follow a decline (INV-137)",
        )

    def test_ground_rules_states_it_is_unconditional(self):
        self.assertRegex(
            read(GROUND_RULES),
            r"unconditional",
            "ground-rules must say the behavior is unconditional, since the previous "
            "design made it conditional and the distinction is the whole change",
        )


class TestRetainedInv120Content(unittest.TestCase):
    """INV-137 keeps these requirements; only their host sentence moved."""

    def setUp(self):
        self.text = flat(GROUND_RULES)

    def test_separate_dials(self):
        self.assertRegex(self.text, r"separate dials|independent dials")

    def test_changeable_at_any_time(self):
        self.assertIn("changed at any time", self.text)

    def test_a_downgrade_is_flagged(self):
        self.assertIn("advice to downgrade", self.text)


class TestTheTriggerIsTheCurrentSetting(unittest.TestCase):
    """Ask because a change is needed — not because the table moved.

    The trigger used to be "did the recommendation change from the stage just
    completed", which asks a Bootcamper already running Opus 5 / high to switch
    to Opus 5 / high. Running one model throughout is a supported choice, so that
    was the common case: six questions on the full path, none of which needed
    asking (INV-006, INV-012).
    """

    def test_the_nudge_compares_against_the_current_setting(self):
        """Stated once, in ground-rules; graduation follows it there (#293)."""
        self.assertRegex(
            flat(GROUND_RULES),
            r"running right now|currently running|what the bootcamper is running",
            "the nudge must compare the recommendation against what the "
            "Bootcamper is running, not against the previous stage",
        )

    def test_the_previous_stage_is_only_a_fallback(self):
        """The fallback is now scoped PER DIAL, not to "the current setting" as a whole.

        Reworded 2026-07-29 (source: `dry-run-phase3-interaction-prose-defects` item 8). The
        original phrasing — "only when the current setting cannot be determined" — treated model
        and effort as one thing to determine or not. In a live session they differ: the model is
        knowable, the reasoning effort is exposed nowhere. Read all-or-nothing, the fallback would
        compare a determinable Opus 5 against the previous stage's Sonnet 5, find it unchanged, and
        suppress the switch offer entirely. The intent this test guards is unchanged — the previous
        stage is a fallback, never the primary rule — so only the wording moved.
        """
        self.assertRegex(
            flat(GROUND_RULES),
            r"[Oo]nly for a dial whose current value cannot be determined",
            "comparing against the previous stage is the fallback for an "
            "undeterminable dial — not the primary rule",
        )

    def test_the_fallback_is_resolved_per_dial(self):
        """The half the original wording left unsanctioned, and which the walk relied on."""
        self.assertRegex(
            flat(GROUND_RULES),
            r"(?i)PER DIAL, not for the setting as a whole",
            "a determinable model must be compared directly even when effort is not",
        )

    def test_only_the_differing_dial_is_named(self):
        self.assertRegex(
            flat(GROUND_RULES),
            r"[Nn]ame only the dial that differs",
            "model and effort are separate dials: a Bootcamper already on the "
            "recommended model must not be told to re-set it",
        )

    def test_graduation_does_not_assume_it_is_always_a_step_up(self):
        """Graduation shares Opus 5 / high with Module 7, so it usually is not."""
        text = flat(GRADUATION)
        self.assertNotRegex(
            text,
            r"switch\s+question below always applies|always\s+steps up",
            "graduation must derive its behavior from the table like every other "
            "stage; it no longer steps up from Query, Visualize and Discover",
        )
        self.assertRegex(
            text,
            r"already there|already matched|already running",
            "graduation must say what to do when the Bootcamper is already on "
            "Opus 5 at high effort",
        )


class TestTheDowngradeIsFramedWhereItHappens(unittest.TestCase):
    """A step down is asked, so it must be explained in the question.

    The pause is symmetric (maintainer decision, 2026-07-26): downgrades ask
    exactly as upgrades do. The below-current flagging previously lived only on
    the recommendation-matches branch — the one case where a downgrade cannot
    arise — so every real downgrade prompt shipped unexplained.
    """

    def test_the_switch_question_flags_a_step_down(self):
        text = flat(GROUND_RULES)
        self.assertRegex(
            text,
            r"sits \*below\* the current setting, say so in the question itself"
            r"|step down.{0,200}in the question",
            "the switch question itself must name a below-current recommendation "
            "as a step down",
        )

    def test_it_says_declining_costs_nothing(self):
        self.assertRegex(
            flat(GROUND_RULES),
            r"cost saving, not a capability|staying put (is fine|costs)",
            "a downgrade prompt must state that the recommendation is about cost "
            "rather than capability, so declining reads as free",
        )

    def test_the_pause_is_symmetric(self):
        self.assertRegex(
            flat(GROUND_RULES),
            r"in \*\*either\*\* direction|either direction",
            "a differing recommendation asks whether it is higher or lower — "
            "there is no direction-based asymmetry",
        )


class TestMaintainerDocMatches(unittest.TestCase):

    def test_it_documents_the_unconditional_behavior(self):
        text = read(MODEL_SELECTION)
        self.assertRegex(
            text,
            r"not configurable|unconditional",
            "docs/model-selection.md must describe guidance as unconditional (INV-137)",
        )
        self.assertIn("INV-137", text)

    def test_it_does_not_present_the_modes_as_live(self):
        text = read(MODEL_SELECTION)
        self.assertNotRegex(
            text,
            r"\| `advisory` \*\(default\)\*",
            "the three-mode table is retired; keep only the historical note",
        )


if __name__ == "__main__":
    unittest.main()
