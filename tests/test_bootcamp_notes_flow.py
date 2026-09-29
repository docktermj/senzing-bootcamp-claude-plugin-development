"""The note flow is the bootcamper's own channel, and must never behave like feedback.

Enforces **INV-254** (the control exists at any time), **INV-255** (pinned banners with a
glyph distinct from the feedback flow's), **INV-256** (append then verify it landed) and
**INV-257** (recite for approval; the bootcamper's words stay theirs).

⛔ **The failure this file mostly guards against is convergence.** `notes.md` was written by
copying the shape of `feedback.md`, and the two flows are deliberately different in ways
that are easy to "tidy" back together: a note has no routing verdict, no `Source:` field
and no upstream offer, and its banner uses a different glyph precisely so the bootcamper
can tell at a glance which flow they are in (INV-074). An editor reconciling the two files
would remove exactly those differences, and the result — a note quietly offered to Senzing,
or two flows opening with 📝 — is invisible in review.

⚠️ These are **static** checks on shipped prose. Whether a live turn actually presents the
banner, asks one 👉, and resumes the pending question is a conversational property that
only `dry-run` phase 3 can judge (INV-108 keeps this suite offline).

Source spec: `specs/bootcamp-notes-capture-and-recap-section.md`.

Enforces **INV-322** (a file the bootcamp writes locally from context it gathers carries no
host identifier) for the notes context block only, in
`test_the_context_block_is_bound_by_the_privacy_rule`. ⚠️ No test here guards the recap's
run-environment block or the retrospective's entries, and nothing offline shows a live note is clean.

Run:  python3 -m unittest discover -s tests
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
ONBOARDING = PLUGIN / "skills" / "bootcamp-onboarding"
NOTES = ONBOARDING / "notes.md"
FEEDBACK = ONBOARDING / "feedback.md"
GROUND_RULES = ONBOARDING / "ground-rules.md"
ONBOARDING_FLOW = ONBOARDING / "onboarding-flow.md"
COMMAND = PLUGIN / "commands" / "bootcamp-note.md"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"
HOOKS_README = PLUGIN / "hooks" / "README.md"

ENTRY_BANNER = "📌📌📌  BOOTCAMP NOTE  📌📌📌"
EXIT_BANNER = "📌  NOTE SAVED — BACK TO THE BOOTCAMP  📌"
NOTES_FILE = "docs/bootcamp_notes.md"


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return " ".join(text.split())


class TheFlowShips(unittest.TestCase):

    def test_the_workflow_file_exists(self):
        self.assertTrue(NOTES.is_file(), "notes.md is missing; the hook routes to it")

    def test_the_slash_command_exists(self):
        self.assertTrue(COMMAND.is_file(), "/bootcamp-note has no command file")

    def test_the_command_points_at_the_workflow(self):
        self.assertIn("notes.md", read(COMMAND))

    def test_the_hooks_readme_purpose_still_begins_with_to(self):
        """INV-016 — and it must now name the note branch as well."""
        row = [l for l in read(HOOKS_README).splitlines()
               if "feedback-capture.py" in l]
        self.assertTrue(row, "the hook is not listed in the README Purpose table")
        purpose = row[0].split("|")[3].strip()
        self.assertTrue(purpose.startswith("to "),
                        f"the documented purpose must begin with 'to': {purpose!r}")
        self.assertIn("note", purpose.lower(),
                      "the purpose does not mention the note branch the hook now carries")


class TheBannersBracketTheFlow(unittest.TestCase):
    """INV-255. A flow the bootcamper cannot see the edges of is a flow they get lost in."""

    def setUp(self):
        self.text = read(NOTES)

    def test_both_banners_are_present_verbatim(self):
        self.assertIn(ENTRY_BANNER, self.text)
        self.assertIn(EXIT_BANNER, self.text)

    def test_the_glyph_is_distinct_from_the_feedback_flow(self):
        """⛔ INV-074's whole purpose: two flows, two glyphs, told apart at a glance."""
        self.assertIn("📝", read(FEEDBACK), "fixture check: the feedback glyph moved")
        banner_lines = [l for l in self.text.splitlines() if "BOOTCAMP NOTE" in l
                        or "NOTE SAVED" in l]
        self.assertTrue(banner_lines)
        for line in banner_lines:
            with self.subTest(line=line):
                self.assertNotIn("📝", line,
                                 "the note banner uses the feedback flow's glyph")

    def test_the_entry_banner_is_a_statement_not_a_question(self):
        self.assertNotIn("👉", ENTRY_BANNER)
        self.assertNotIn("👉", EXIT_BANNER)

    def test_the_pending_question_is_re_presented_after_the_exit_banner(self):
        flat = squash(self.text)
        self.assertIn("re-present the exact", flat)
        self.assertIn("verbatim", flat)
        self.assertIn("INV-251", flat,
                      "nothing ties the resumed question to the one-question-per-turn rule")


class ANoteIsNeverTreatedLikeFeedback(unittest.TestCase):
    """⛔ The differences an editor reconciling the two files would erase."""

    def setUp(self):
        self.text = read(NOTES)

    def test_there_is_no_upstream_submission_path(self):
        self.assertNotIn("submit_feedback(", self.text)
        self.assertIn("no upstream offer", squash(self.text).lower())

    def test_there_is_no_routing_verdict(self):
        flat = squash(self.text).lower()
        self.assertIn("no routing verdict", flat)
        for verdict in ("`plugin` |", "`mcp-server` |"):
            with self.subTest(verdict=verdict):
                self.assertNotIn(verdict, self.text,
                                 "the note flow carries a feedback routing table")

    def test_it_says_the_note_never_leaves_the_machine(self):
        flat = squash(self.text).lower()
        self.assertTrue("stays on their machine" in flat
                        or "never sent anywhere" in flat,
                        "nothing states that a note is never sent anywhere")

    def test_the_overlap_precedence_is_stated_in_the_flow_too(self):
        """"Make a note that the bootcamp is broken" is a defect report, not a note."""
        flat = squash(self.text).lower()
        self.assertIn("it is feedback", flat)


class TheNoteStaysTheBootcampersOwnWords(unittest.TestCase):
    """INV-257. This is a keepsake with their name on the certificate."""

    def setUp(self):
        self.text = read(NOTES)

    def test_the_note_is_recited_before_it_is_saved(self):
        self.assertIn("Here's your note — save it as is?", self.text)

    def test_elaboration_and_context_have_their_own_labels(self):
        self.assertIn("**Elaboration:**", self.text)
        self.assertIn("**Context:**", self.text)

    def test_merging_an_elaboration_is_forbidden_in_terms(self):
        flat = squash(self.text)
        self.assertIn("Never merge an elaboration into the note body", flat)

    def test_the_context_block_is_bound_by_the_privacy_rule(self):
        flat = squash(self.text)
        self.assertIn("INV-322", flat)
        for forbidden in ("hostname", "username", "IP address"):
            with self.subTest(field=forbidden):
                self.assertIn(forbidden, flat)

    def test_the_type_is_assigned_without_asking(self):
        flat = squash(self.text)
        self.assertIn("Do not ask for it", flat)

    def test_a_note_already_in_the_message_is_not_re_asked(self):
        """INV-006 — they already said it."""
        flat = squash(self.text)
        self.assertIn("take it from the message and do", flat)
        self.assertIn("INV-006", flat)


class TheNoteIsDurableAndNonBlocking(unittest.TestCase):
    """INV-256/INV-048."""

    def setUp(self):
        self.text = read(NOTES)

    def test_the_append_target_is_the_notes_file(self):
        self.assertIn(NOTES_FILE, self.text)

    def test_it_appends_rather_than_rewrites(self):
        flat = squash(self.text)
        self.assertIn("Append", flat)
        self.assertIn("never rewrite", flat.lower())

    def test_it_verifies_the_entry_landed_before_saying_so(self):
        flat = squash(self.text)
        self.assertIn("re-read the file and confirm the entry is present", flat)
        self.assertIn("Only continue once it is confirmed on disk", flat)

    def test_a_failed_write_warns_and_never_blocks(self):
        flat = squash(self.text)
        self.assertIn("INV-048", flat)
        self.assertIn("never a gate", flat.lower())


class TheControlIsTaught(unittest.TestCase):
    """⛔ An any-time control nobody is told about is an any-time control nobody uses."""

    def test_ground_rules_lists_it_as_an_any_time_control(self):
        text = read(GROUND_RULES)
        controls = text.split("## Any-time bootcamper controls", 1)
        self.assertEqual(2, len(controls), "the any-time controls section moved")
        section = controls[1].split("\n## ", 1)[0]
        self.assertIn("Make a note", section)
        self.assertIn("notes.md", section)
        self.assertIn(NOTES_FILE, section)

    def test_the_onboarding_preface_names_the_trigger(self):
        flat = squash(read(ONBOARDING_FLOW))
        self.assertIn('say "make a note"', flat.lower())
        self.assertIn(NOTES_FILE, flat)

    def test_the_preface_bullet_is_a_statement_not_a_question(self):
        for line in read(ONBOARDING_FLOW).splitlines():
            if "make a note" in line.lower() and line.lstrip().startswith("👉"):
                self.fail(f"the note control is posed as a question: {line!r}")


class GraduationFoldsTheNotesIntoTheKeepsake(unittest.TestCase):
    """INV-258's Markdown half — the PDF half lives in test_recap_notes_section.py."""

    def setUp(self):
        self.text = read(GRADUATION)

    def test_the_fold_uses_the_fence_markers(self):
        self.assertIn("<!-- BOOTCAMP-NOTES:START -->", self.text)
        self.assertIn("<!-- BOOTCAMP-NOTES:END -->", self.text)

    def test_the_fold_happens_before_the_normalize_pass(self):
        fold = self.text.index("<!-- BOOTCAMP-NOTES:START -->")
        normalize = self.text.index("**Normalize the Markdown (once, before rendering).**")
        self.assertLess(fold, normalize,
                        "the notes are folded after the normalize pass, so they never "
                        "get normalized and the retention figure is computed on a file "
                        "that changed afterwards")

    def test_the_fold_is_idempotent_and_append_only(self):
        flat = squash(self.text)
        self.assertIn("INV-085", flat)
        self.assertIn("must not duplicate the section", flat)

    def test_no_notes_means_nothing_is_written(self):
        flat = squash(self.text)
        self.assertIn("With no notes, write nothing", flat)

    def test_the_notes_file_is_excluded_from_production(self):
        exclude = self.text.split("**Exclude (never copy):**", 1)
        self.assertEqual(2, len(exclude), "the production exclusion list moved")
        self.assertIn(NOTES_FILE, exclude[1][:400],
                      "the bootcamper's notes would be copied into the production project")

    def test_the_notes_file_survives_graduation(self):
        flat = squash(self.text)
        self.assertIn("survives graduation intact", flat)


if __name__ == "__main__":
    unittest.main()
