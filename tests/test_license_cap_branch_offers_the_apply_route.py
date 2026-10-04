"""The license-cap branch offers a route to the license, not just the idea of one.

At the moment the evaluation cap first bites — Data processing, Phase B step 7, immediately
before the full load — a Bootcamper with a 7,718-record dataset and a measured
`recordLimit: 500` was offered *"wait until the evaluation license is applied, then load all
7,718"*. That option names an outcome and supplies no way to reach it: no file location, no
configuration key, no verification step. Nothing mentioned that the free evaluation license
they had **already requested** two modules earlier arrives by email and may already have
landed.

⚠️ **Those three options were not in the plugin.** The branch said only *"restate that a
larger license lets the full load proceed, as a choice, not a wall"*, so the guide
**improvised** a menu — and the one option that would dissolve the constraint is the one an
improvising guide is least likely to invent, because the procedure for it lives two modules
away. Hence a pinned question (INV-056): what the Bootcamper meets must not vary by run.

⛔ **The apply procedure already existed and was simply unreachable.** Module 4 Step 8a
sub-step 5 is a complete cross-platform procedure, and sub-step 6 even contemplates applying
an emailed key *in a later session*. This is the INV-183 shape — a procedure that governs a
decision is not reachable where the decision is made — aggravated by the plugin having
written down the later-session case and never built the path back to it.

⛔ **The obvious implementation introduces a new defect, and that is the negative control
below.** Keying the reminder to `license: evaluation` is wrong: that value is written both
after a request was sent *and* when the Bootcamper **declined** to send one, so it means "no
custom key is applied" and nothing about whether anything is outstanding. A reminder keyed to
it tells someone who declined to go hunting for a license they never asked for. The request
had to become a recorded **event**.

⛔ **And it must not become a second gate.** INV-093 requires the License Key prompt at most
once, in Module 4. The decision — do you have a key, do you want to request one — is settled;
what was missing is a *procedure* and a *status readout*, which are not a gate.

Verified on MCP server **1.32.9, 2026-08-17**: `sdk_guide(topic='load', language='python',
record_count=1000)` returns `compatibility_notes` listing three remedies, of which remedy 2 is
*"Provide a license they already have"* — the option the plugin omitted. ⚠️ The server names
`SENZING_LICENSE_FILE` / `etc/`; the plugin wires `LICENSEFILE` into the engine-config
PIPELINE. Both are real, and the plugin's own procedure is the one tested in this file layout,
so the branch reuses Step 8a rather than adopting the server's wording.

Source spec: `specs/license-cap-branch-offers-no-way-to-apply-the-license-that-may-have-arrived.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE4 = SKILLS / "module-04-data-collection" / "SKILL.md"
PHASE_A = SKILLS / "module-06-data-processing" / "phaseA-build-loading.md"
PHASE_B = SKILLS / "module-06-data-processing" / "phaseB-load-first-source.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def cap_branch():
    """Phase B's `positive and below the dataset size` branch, sliced by its own content."""
    text = PHASE_B.read_text(encoding="utf-8")
    start = text.index("**Positive and below the dataset size**")
    end = text.index("- **Absent or null**", start)
    return text[start:end]


class TheRequestIsRecordedAsAnEvent(unittest.TestCase):
    """⛔ Not as the absence of a key — the two are opposite states."""

    def setUp(self):
        self.text = flat(MODULE4)

    def test_a_distinct_marker_is_persisted(self):
        self.assertIn('"license_key_requested"', self.text)

    def test_it_carries_the_channel_and_the_date(self):
        self.assertIn('"channel"', self.text)
        self.assertIn('"date"', self.text)

    def test_it_is_written_only_on_an_actual_send(self):
        self.assertIn("only on an actual send", self.text)

    def test_the_ambiguity_of_the_old_marker_is_stated(self):
        self.assertIn('`license: evaluation` means "no custom key is applied" and NOTHING '
                      "about whether a request is outstanding", self.text)

    def test_the_decline_path_is_told_not_to_write_it(self):
        """The negative control's other half, at the site that would get it wrong."""
        self.assertIn("Do not write `license_key_requested` on this path", self.text)


class ADeclinedBootcamperGetsNoEmailReminder(unittest.TestCase):
    """⛔ The failure the obvious implementation introduces."""

    def setUp(self):
        self.branch = " ".join(cap_branch().split())

    def test_the_reminder_is_gated_on_the_request_marker(self):
        self.assertIn("Read `license_key_requested` from `config/bootcamp_progress.json` first",
                      self.branch)
        self.assertIn("Only when a request is outstanding", self.branch)

    def test_the_absent_case_is_spelled_out(self):
        self.assertIn("Absent `license_key_requested` → no reminder; say nothing about email",
                      self.branch)

    def test_it_names_why_the_old_marker_cannot_gate_it(self):
        self.assertIn("declined", self.branch)
        self.assertIn("a license they never asked for", self.branch)

    def test_the_apply_option_survives_an_absent_marker(self):
        """⚠️ The marker gates the reminder, never the option — they are different things."""
        self.assertIn("Option 2 stays on the list even when `license_key_requested` is absent",
                      self.branch)


class TheApplyRouteIsPointedAtNotRestated(unittest.TestCase):

    def setUp(self):
        self.branch = " ".join(cap_branch().split())

    def test_it_names_the_owning_sub_step(self):
        self.assertIn("Module 4 Step 8a **sub-step 5**", self.branch)

    def test_it_forbids_a_second_copy(self):
        self.assertIn("Do not write a second copy of it here", self.branch)

    def test_the_platform_commands_live_in_exactly_one_place(self):
        """A platform-specific procedure duplicated is a procedure that drifts."""
        offenders = []
        for path in sorted(SKILLS.rglob("*.md")):
            body = path.read_text(encoding="utf-8")
            if "base64 --decode > licenses/g2.lic" in body:
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            ["plugins/senzing-bootcamp/skills/module-04-data-collection/SKILL.md"],
            offenders,
            "the decode-and-place commands appear somewhere other than Step 8a")

    def test_the_servers_different_mechanism_is_not_adopted(self):
        """⚠️ SENZING_LICENSE_FILE is real and is NOT the one wired into this layout."""
        self.assertIn("do not substitute a different mechanism", self.branch)
        self.assertIn("would leave the engine config pointing at nothing", self.branch)
        self.assertIn("LICENSEFILE", self.branch)


class ItReMeasuresAndReEntersTheBranches(unittest.TestCase):

    def setUp(self):
        self.branch = " ".join(cap_branch().split())

    def test_it_re_reads_the_license_and_parses_the_limit(self):
        self.assertIn("`SzProduct.get_license()`", self.branch)
        self.assertIn("parse `recordLimit`", self.branch)

    def test_it_confirms_the_limit_actually_moved(self):
        self.assertIn("confirm it actually moved", self.branch)

    def test_it_routes_again_on_the_new_value(self):
        self.assertIn("route again on the new value", self.branch)

    def test_no_capacity_or_duration_figure_is_hardcoded(self):
        """⛔ Two MCP tools have disagreed about these; they belong in a runtime lookup."""
        self.assertIn("Do **not** state the evaluation license's size or duration from "
                      "this file", self.branch)
        for figure in ("250K", "250,000", "10-day", "5-day"):
            with self.subTest(figure=figure):
                self.assertNotIn(figure, self.branch)


class TheBranchAsksOneQuestionAndIsNotASecondGate(unittest.TestCase):

    def setUp(self):
        self.branch = cap_branch()
        self.flat = " ".join(self.branch.split())

    def test_it_carries_exactly_one_pinned_question(self):
        # Line-scoped by design (#424): this counts questions by the 👉 that opens each one,
        # and a question opens on one line however it wraps after that.
        posed = [l for l in self.branch.splitlines()
                 if l.lstrip().lstrip(">").strip().startswith("👉")]
        self.assertEqual(1, len(posed),
                         f"the branch poses {len(posed)} questions; INV-251 allows one")

    def test_the_question_is_answerable_by_number(self):
        self.assertIn("Reply with a number:", self.flat)

    def test_it_offers_the_apply_option_the_branch_previously_omitted(self):
        self.assertIn("Apply a license I have", self.flat)

    def test_it_says_it_replaces_rather_than_adds(self):
        self.assertIn("replaces the improvised one", self.flat)

    def test_it_is_not_a_second_license_key_gate(self):
        self.assertIn("INV-093", self.flat)
        self.assertIn("not** a second License Key gate", self.flat)

    def test_module_six_never_asks_the_module_four_question(self):
        """INV-093 — the prompt is presented at most once, in Module 4."""
        module4_question = "Send this evaluation-license request"
        for path in (PHASE_A, PHASE_B):
            with self.subTest(path=path.name):
                self.assertNotIn(module4_question, path.read_text(encoding="utf-8"),
                                 "Module 6 re-asks the Module 4 License Key question")


class PhaseADefersToPhaseB(unittest.TestCase):
    """The mirror branch: it builds the loader, it does not decide what to load."""

    def setUp(self):
        self.text = flat(PHASE_A)

    def test_it_forbids_improvising_a_menu(self):
        self.assertIn("Do not improvise a menu of options here", self.text)

    def test_it_names_where_the_decision_belongs(self):
        self.assertIn("belongs to `phaseB-load-first-source.md` step 7, once", self.text)

    def test_it_records_the_reported_symptom_as_the_reason(self):
        self.assertIn('"wait until the evaluation license is applied"', self.text)

    def test_it_poses_no_question_of_its_own_in_this_branch(self):
        body = PHASE_A.read_text(encoding="utf-8")
        start = body.index("**Positive and below the dataset size**")
        end = body.index("- **Absent or null**", start)
        # Line-scoped by design (#424): a 👉 that opens a line opens a question.
        posed = [l for l in body[start:end].splitlines()
                 if l.lstrip().lstrip(">").strip().startswith("👉")]
        self.assertEqual([], posed, "Phase A's branch asks a question of its own")


if __name__ == "__main__":
    unittest.main()
