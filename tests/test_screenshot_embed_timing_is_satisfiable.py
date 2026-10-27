"""The screenshot-embed rule names a moment both capturing modules can actually reach.

`module-completion.md`'s "Visualization screenshots" bullet required every captured image to
be added to the module's **Actions Taken** *"in the same turn the capture ran"*. In both
modules that capture, the capture and the recap append are separated by **two deliberate 👉
gates**:

    capture (phase1 Step 2.4)
      -> 👉 guided tour: "Are you ready to continue?"
      -> 👉 teardown consent: "Ready for me to stop the visualization server...?"
    recap section appended (phase2 close -> module completion)

At capture time the module's `## {Name}` recap section does not exist, so there is no Actions
Taken to write into. Observed live 2026-08-31: six captures written against a running server,
recap section created two gates later. No previous phase-3 walk had reached a capture.

⚠️ The *unsatisfiable-instruction* class again. The section's own next sentence already
supplied the operational answer ("record it at the step checkpoint"), so a careful reader
landed correctly — but the two clauses were in tension and the emphatic one was the impossible
one. The cost is not lost images; it is teaching that these rules are approximate.

⛔ The force of the requirement must not soften. It is emphatic because a previous run captured
images and never embedded them, and graduation had to backfill.

⚠️ **The same defect survived in the other half of the file, and was reported from a child repo
(#671, 2026-10-16; INV-146's dated note, applied 2026-10-26).** Step 2b's bullet was corrected; *"Capturing visualization screenshots"*
item 3 kept its own copy — *"as a required step, in the **same turn** — embed them all in this
module's recap `Actions Taken`"* — and that is the text the guide is actually reading when the
capture runs. Two mandatory instructions, in one file, that cannot both be followed on the
documented intervening-question path without creating or finalizing the recap section early.

So the timeline is pinned in **both** directions now: item 3 defers to Step 2b's two moments and
forbids reaching the embed early by creating the section, and every caller that restates the embed
names module close as the moment — the cross-step relationship no single-site assertion can see.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"
COMPLETION = SKILLS / "bootcamp-onboarding" / "module-completion.md"


def flat(s):
    return re.sub(r"\s+", " ", s)


def screenshot_bullet():
    text = COMPLETION.read_text(encoding="utf-8")
    start = text.index("- **Visualization screenshots:**")
    end = text.index("\n  ```markdown", start)
    return text[start:end]


def capture_section():
    """The whole "Capturing visualization screenshots" section — the text the guide reads
    at the capture step, which is a different place in the file from Step 2b's bullet."""
    text = COMPLETION.read_text(encoding="utf-8")
    start = text.index("## Capturing visualization screenshots")
    end = text.index("## Step 3:", start)
    return text[start:end]


#: The owner of the procedure, and graduation's backfill, which embeds at graduation rather
#: than at a module's close. Everything else citing the procedure is a caller restating it.
NOT_A_CALLER = {"module-completion.md", "SKILL.md"}


def capture_callers():
    """Every shipped file that cites the capture procedure — discovered, never listed.

    INV-246: a listed pair would leave the next capturing module's restatement unchecked,
    which is exactly how item 3 kept its own copy of the timing for six weeks after Step 2b
    was corrected.
    """
    found = []
    for path in sorted(SKILLS.rglob("*.md")):
        if path.name in NOT_A_CALLER:
            continue
        if "Capturing visualization screenshots" in path.read_text(encoding="utf-8"):
            found.append(path)
    return tuple(found)


#: A caller restating the embed: "embed… in this module's recap". The window before it must
#: name the capture (so Module 1's "in this module's recap section", about a diagram listed in
#: the end-of-module summary, is not swept in), and the window around it must name the moment.
RECAP_MENTION = "this module's recap"
WINDOW = 220


def embed_restatements(path):
    """(before, after) windows around every restatement of the embed in `path`."""
    flat_text = flat(path.read_text(encoding="utf-8"))
    out = []
    start = 0
    while True:
        i = flat_text.find(RECAP_MENTION, start)
        if i < 0:
            return out
        start = i + 1
        before = flat_text[max(0, i - WINDOW):i]
        if "embed" not in before.lower():
            continue
        if not any(w in before.lower() for w in ("captur", "screenshot", "image", "png", "tab")):
            continue
        out.append((before, flat_text[i:i + WINDOW]))


class TheImpossibleTimingIsGone(unittest.TestCase):
    def test_no_rule_requires_the_embed_in_the_capture_turn(self):
        """Pinned by its exact historical wording: it reads correct and cannot be obeyed."""
        self.assertNotRegex(
            flat(COMPLETION.read_text(encoding="utf-8")),
            r"(?i)in the same turn the capture ran, in the app's tab order",
            "The embed must not be required in the capture's own turn. Both capturing modules "
            "put two deliberate 👉 gates between the capture and the recap append, so at "
            "capture time there is no Actions Taken section to write into.",
        )

    def test_the_two_moments_are_named_separately(self):
        self.assertRegex(
            flat(screenshot_bullet()), r"(?i)two moments, not one",
            "The rule must separate recording from embedding. Collapsing them is what made it "
            "unsatisfiable, and a reader who notices the impossibility has no sanctioned "
            "alternative to fall back on.",
        )

    def test_the_checkpoint_is_named_as_the_carrier(self):
        """The spec's third criterion — the mechanism, not just the corrected timing."""
        self.assertRegex(
            flat(screenshot_bullet()),
            r"(?i)checkpoint is what carries the capture across",
            "The step checkpoint must be named as what carries the capture across the turn "
            "boundaries. Without the mechanism, 'embed later' is an instruction with no state "
            "behind it — and the failure it replaces was a capture recorded nowhere.",
        )

    def test_the_embed_happens_where_the_section_exists(self):
        self.assertRegex(
            flat(screenshot_bullet()),
            r"(?i)when this module's Actions Taken is written, at module close",
            "The embed must be tied to the moment the section is written. That is the first "
            "turn in which the target of the instruction exists.",
        )


class TheRequirementKeepsItsForce(unittest.TestCase):
    """⛔ Fixing the timing must not soften what the rule demands."""

    def setUp(self):
        self.bullet = flat(screenshot_bullet())

    def test_embedding_is_still_required_and_uncapped(self):
        self.assertRegex(
            self.bullet, r"(?i)embedding every screenshot it produced is required",
            "The embed must remain required, not optional (INV-146).",
        )
        self.assertRegex(
            self.bullet, r"(?i)no count cap applies",
            "The no-count-cap clause must survive — it is what stops a guide embedding two of "
            "six and calling it done.",
        )

    def test_the_backfill_history_is_kept_as_the_reason(self):
        self.assertRegex(
            self.bullet, r"(?i)graduation has to backfill",
            "The reason the rule is emphatic must survive the rewrite: a previous run captured "
            "images, embedded none, and graduation backfilled. A rule whose reason is deleted "
            "is one the next editor relaxes.",
        )

    def test_the_tab_order_requirement_survives(self):
        self.assertRegex(
            self.bullet, r"(?i)in the app's tab order",
            "Tab order must survive — it is what makes the recap's images legible as a tour "
            "rather than an unordered dump.",
        )


class TheSurroundingRulesAreUntouched(unittest.TestCase):
    """The spec says explicitly to leave the rest of the section alone."""

    def setUp(self):
        self.text = flat(COMPLETION.read_text(encoding="utf-8"))

    def test_the_relative_path_rule_survives(self):
        self.assertRegex(
            self.text, r"(?i)never `docs/visualizations/…`",
            "INV-161's relative-path rule must survive — a `docs/`-prefixed path resolves to "
            "`docs/docs/…` and drops the image from both the Markdown and the PDF.",
        )

    def test_the_own_line_block_form_survives(self):
        self.assertRegex(
            self.text, r"(?i)Each image goes on a line of its own",
            "INV-242's own-line block form must survive.",
        )

    def test_the_artifact_verification_rule_survives(self):
        self.assertRegex(
            self.text, r"(?i)verify the artifact itself, not the exit code",
            "The verify-the-artifact rule must survive — it is what catches a capture helper "
            "that exits 0 having written three images of the same tab.",
        )


class TheCaptureStepDefersToModuleClose(unittest.TestCase):
    """#671: item 3 — the text read AT the capture — must point at Step 2b, not override it."""

    def setUp(self):
        self.section = flat(capture_section())

    def test_the_embed_is_not_demanded_as_a_same_turn_step(self):
        """Pinned by the exact wording that shipped, as the Step 2b guard above is."""
        self.assertNotRegex(
            self.section, r"(?i)as a required step, in the same turn",
            "The capture step must not demand the embed in its own turn. Both capturing "
            "modules put deliberate 👉 gates between the capture and the recap append, so the "
            "Actions Taken this sentence names does not exist yet.",
        )

    def test_it_names_module_close_as_the_embed_moment(self):
        self.assertRegex(
            self.section, r"(?i)the embed is the second moment, at module close",
            "The capture step must name module close as the embed's moment, so the two "
            "directives in this one file state one timeline rather than two.",
        )

    def test_it_defers_to_step_2b_rather_than_restating_the_timeline(self):
        """INV-300: one statement of record, cited from the other site."""
        self.assertRegex(
            self.section, r"(?i)Step 2b above states the timeline once and it binds here",
            "The capture step must defer to Step 2b. A second full statement of the timing "
            "is how these two sites forked in the first place.",
        )

    def test_it_records_the_capture_before_the_turn_yields(self):
        self.assertRegex(
            self.section,
            r"(?i)record each one in this step's checkpoint, in the capture's own turn and "
            r"before the turn yields",
            "The capture paths and the tab each image shows must be durable before the turn "
            "yields — that is what carries them to module close, and a capture recorded "
            "nowhere is one graduation has to backfill.",
        )

    def test_it_forbids_reaching_the_embed_by_creating_the_section_early(self):
        """The branch a reader takes when two mandatory instructions collide.

        Without this the obedient reading of "embed in the same turn" is to CREATE the
        `## {Name}` section at capture time — which Step 2a owns, which the module-close
        append then has to reconcile, and which leaves a half-finalized recap behind if the
        module is interrupted between the two.
        """
        self.assertRegex(
            self.section,
            r"(?i)Never create or finalize this module's recap section here to embed sooner",
            "The capture step must forbid creating or finalizing the recap section early. "
            "Deferring the embed without closing that door just moves the collision.",
        )

    def test_the_requirement_still_has_its_force_here(self):
        self.assertRegex(
            self.section, r"(?i)Writing the image lines is not optional once a capture succeeded",
            "Correcting the timing must not turn the embed into an option (INV-146).",
        )
        self.assertRegex(
            self.section, r"(?i)[Kk]eep every captured tab",
            "All-tab retention must survive the rewrite (INV-146).",
        )


class EveryCallerStatesTheSameTimeline(unittest.TestCase):
    """#671: the cross-step relationship — one timeline, agreed at every site that restates it.

    The owning procedure can be perfectly coherent and still be contradicted by the module file
    the guide has open. These assertions are what a single-site check cannot make.
    """

    def test_the_sweep_finds_the_known_callers(self):
        """Non-vacuity floor (INV-246), not the site set."""
        names = {p.name for p in capture_callers()}
        for known in ("phase1-visualization.md", "phase1-query-visualize.md",
                      "phase1-quality-assessment.md", "phase2-data-mapping.md"):
            with self.subTest(file=known):
                self.assertIn(known, names,
                              "%s no longer cites the capture procedure, so this sweep is "
                              "inspecting a smaller set than it believes" % known)

    def test_the_detector_sees_the_wording_that_shipped(self):
        """Positive control: the pre-#671 Module 7 sentence is a restatement with no moment."""
        shipped = ("read the reason the helper gave; otherwise embed **every** captured tab "
                   "in this module's recap, in the app's tab order — no count cap, INV-146)")
        i = shipped.index(RECAP_MENTION)
        self.assertIn("embed", shipped[:i].lower())
        self.assertNotIn("at module close", shipped.lower())

    def test_every_restatement_names_module_close(self):
        offenders = []
        for path in capture_callers():
            for before, after in embed_restatements(path):
                if "at module close" not in (before + after).lower():
                    offenders.append("%s: %r" % (path.name, after[:110]))
        self.assertEqual(
            [], offenders,
            "a caller tells the guide to embed captures in this module's recap without "
            "naming module close, so the moment it implies is the capture's own turn:\n  "
            + "\n  ".join(offenders),
        )

    def test_every_restatement_names_the_checkpoint_that_carries_it(self):
        """"Embed later" with no state behind it is the failure the rule replaced."""
        offenders = []
        for path in capture_callers():
            for before, after in embed_restatements(path):
                if "checkpoint" not in (before + after).lower():
                    offenders.append("%s: %r" % (path.name, after[:110]))
        self.assertEqual(
            [], offenders,
            "a caller defers the embed to module close without naming the step checkpoint "
            "that carries the capture there:\n  " + "\n  ".join(offenders),
        )

    def test_no_caller_demands_the_embed_in_the_capture_turn(self):
        offenders = []
        for path in capture_callers():
            for before, after in embed_restatements(path):
                window = (before + after).lower()
                if "in the same turn" in window and "at module close" not in window:
                    offenders.append("%s: %r" % (path.name, after[:110]))
        self.assertEqual(
            [], offenders,
            "a caller requires the embed in the capture's own turn:\n  " + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
