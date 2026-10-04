"""No 👉 question offers a session- or host-level control, and the rule that says so ships.

Twice on 2026-08-15, a bootcamper on plugin 0.5.0 was interrupted during the onboarding
preface -- with `👉 Do you have any questions before we get started?` pending and unanswered --
by the Claude Code host prompt "Set up auto mode for your environment?", the harness's own
dialog offering "Set it up" / "Not now" / "Don't show again".

⚠️ **That prompt is HOST-RENDERED, and this docstring said otherwise until 2026-08-15.** It
read "a bootcamper was asked about auto-mode", which frames it as the guide putting a question
to them. The second report quoted the dialog with its three native options -- UI chrome a model
cannot emit -- establishing that the guide originated nothing. No run has yet shown a guide
improvising a host-control question. INV-247 is prophylaxis against a hazard the reports
demonstrate (a bootcamper cannot tell an interface question from bootcamp content), not a
repair of an observed guide defect, and this file must not imply otherwise
(`specs/host-rendered-control-prompt-interrupts-a-pending-question.md`).

The rule is still worth having, and nothing on the books forbade the improvised case: the 👉
protocol governed a question's count (INV-251 since 2026-08-15; INV-005 at the time), shape (INV-008/INV-009/INV-051), placement
(INV-211/INV-224) and, for pinned gates, verbatim wording (INV-056) -- never its provenance. A
repo-wide search for `auto-mode`, `auto mode`, `auto-accept`, `permission mode`, `plan mode`,
`fast mode` and `bypass permissions` across `plugins/`, `.claude/` and `tests/` still returns
matches only in the rule text and this guard.

One thing also made such a question look native. The bootcamp already asks the bootcamper to
operate `/model` and `/effort` at module start (INV-063/INV-098/INV-158/INV-236) and named no
boundary, so a bootcamper who has been asked *"Would you like to switch to `/model …` +
`/effort …` for this module?"* had no way to tell an "auto-mode?" question from bootcamp
content.

Enforces **INV-247** — every 👉 question traces to a step in a shipped skill file, and no
session- or host-level control other than the model/effort switch is presented as a bootcamp
question.

⛔ **THIS GUARD HAS TWO LIMITS. BOTH ARE STATED HERE BECAUSE ONE DISCLOSURE READS AS ALL OF
THEM**, and a guard whose caveat looks complete is the pattern
`specs/coverage-reports-count-known-non-defects-as-hits.md` exists to stop.

1. **It cannot detect a runtime-improvised question.** The reported defect was a question that
   exists in **no file**; this test reads files. A clean run is not evidence the bootcamp can
   no longer ask about auto mode — that half is unreachable from a static check and belongs to
   `dry-run` phase 3.
2. **Its vocabulary check is a closed, dated list.** ``HOST_CONTROL`` matches eight literals
   naming the Claude Code CLI's affordances **as of 2026-08-15**. A control phrased in words
   absent from that list passes it. The CLI ships independently of this plugin and an offline
   suite (INV-108) cannot notice a new one, so the list is a snapshot to extend, never a
   guarantee.

``test_no_pinned_question_offers_an_unsanctioned_slash_command`` exists because of limit 2 and
does not share it: it matches slash commands **structurally** and allows only ``/model`` and
``/effort``, so a future ``/thinking`` or ``/verbose`` offered in a pinned question fails
without anyone having added it to a list. It is the assertion to prefer; the vocabulary check
survives only to catch non-slash phrasings ("auto mode", "permission mode").

Per **INV-246** the site set is derived by scanning every shipped Markdown file under
`plugins/senzing-bootcamp/`, never from a hardcoded list — a listed guard would certify the
files the author already thought of and miss a module added later, which is the only site
that matters.

Source spec: `specs/a-question-with-no-origin-in-a-skill-file-reached-the-bootcamper.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import blocks, match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"

# A pinned 👉 question: the pointer immediately followed by the bold question text. Prose that
# *talks about* 👉 questions (including the rule below) does not match, because there the
# pointer sits inside a sentence rather than ahead of a bolded question.
PINNED_QUESTION = re.compile("\U0001F449" + r"\s*\*\*")

# A slash command offered inside a pinned question. Structural, so it needs no vocabulary and
# does not expire: any new host command the CLI ships is caught the day it appears in a
# question. This is the assertion that actually enforces INV-247's class.
SLASH_COMMAND = re.compile(r"(?<![\w/])/([a-z][a-z0-9-]{1,20})\b")

#: The only Claude-interface controls the bootcamp asks the bootcamper to operate (INV-247,
#: via INV-063/INV-098/INV-158/INV-236).
SANCTIONED_SLASH = frozenset({"model", "effort"})

# Session- or host-level controls: the bootcamper's Claude interface, not the bootcamp's to
# offer. `/model` and `/effort` are deliberately absent — they are the sole exception.
#
# ⚠️ SNAPSHOT, NOT A CLOSED SET — dated 2026-08-15, the Claude Code CLI's affordances at that
# date. The CLI ships independently of this plugin, so this list expires silently and an
# offline suite cannot notice. EXTEND it when a new control appears, and do not read a pass
# here as "no host control is offered" — SLASH_COMMAND above is the check that generalizes.
HOST_CONTROL = re.compile(
    r"(?i)auto[-\s]?mode"
    r"|auto[-\s]?accept"
    r"|permission[-\s]mode"
    r"|plan[-\s]mode"
    r"|fast[-\s]mode"
    r"|bypass[-\s]permission"
    r"|background[-\s]task"
    r"|/compact\b"
    r"|/loop\b"
)

# An affirmative claim that the plugin removes a host control. It cannot: a plugin ships
# skills, hooks and commands, and none of those reach the host's own affordances. Writing the
# claim anyway would paper over the scope change this spec had to make.
SUPPRESSION_CLAIM = re.compile(
    r"(?i)\b(?:the\s+)?(?:bootcamp|plugin|we)\s+(?:can\s+)?"
    r"(?:suppress(?:es)?|disable[sd]?|turn(?:s)?\s+off|hide[sd]?|override[sd]?)\s+"
    r"(?:the\s+)?(?:auto|permission|plan|fast|host)"
)


def shipped_markdown():
    """Every shipped Markdown file, discovered rather than listed (INV-246)."""
    return sorted(PLUGIN.rglob("*.md"))


def read(path):
    return path.read_text(encoding="utf-8")


def squash(text):
    return re.sub(r"\s+", " ", text)


def pinned_questions(text):
    """[(lineno, question)] for each pinned 👉 question, read across line wraps (#424).

    A question runs from its 👉 to the next 👉 in its Markdown block, or to the end of the
    block, with whitespace collapsed, and is reported at the line its 👉 is on. The line that
    holds the 👉 is added whole, as before #424, so nothing the line check saw is lost; what a
    wrap adds is the rest of a question that runs onto the next line.
    """
    spans = []
    for block in blocks(text):
        flat = " ".join(" ".join(line for _n, line in block).split())
        starts = [m.start() for m in PINNED_QUESTION.finditer(flat)]
        for a, b in zip(starts, starts[1:] + [len(flat)]):
            nxt = flat.find("\U0001F449", a + 1)
            spans.append(flat[a:nxt if a < nxt < b else b])
    lines = match_lines(text, PINNED_QUESTION)
    assert len(lines) == len(spans), "match_lines and the block scan disagree"
    raw = text.split("\n")
    return [(n, raw[n - 1] + " " + span) for n, span in zip(lines, spans)]


def section(text, heading):
    """The body of one `## ` section, so a rule can be required WHERE it binds."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == heading:
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    return squash("\n".join(lines[i:j]))
            return squash("\n".join(lines[i:]))
    raise AssertionError("heading not found in ground-rules.md: %r" % heading)


class NoShippedQuestionOffersAHostControl(unittest.TestCase):
    def test_the_corpus_is_actually_being_scanned(self):
        """A guard that silently matched nothing would pass forever."""
        files = shipped_markdown()
        self.assertGreater(len(files), 20,
                           "the shipped Markdown sweep found almost nothing — the corpus "
                           "moved and this guard is now inspecting an empty set")
        questions = [(p, n, line)
                     for p in files
                     for n, line in enumerate(read(p).splitlines(), 1)
                     if PINNED_QUESTION.search(line)]
        self.assertGreater(len(questions), 50,
                           "the pinned-question pattern matched almost nothing — the 👉 "
                           "question form changed and this guard no longer sees questions")

    def test_no_pinned_question_names_a_session_or_host_control(self):
        offenders = []
        for path in shipped_markdown():
            for n, question in pinned_questions(read(path)):
                if HOST_CONTROL.search(question):
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append("%s:%d: %s" % (rel, n, question.strip()[:140]))
        self.assertEqual(
            [], offenders,
            "a 👉 question offers a control that belongs to the bootcamper's Claude session, "
            "not to the bootcamp (INV-247). The model/effort switch is the only "
            "Claude-interface control the bootcamp asks them to operate:\n  "
            + "\n  ".join(offenders))

    def test_no_pinned_question_offers_an_unsanctioned_slash_command(self):
        """The open-ended half of INV-247 — no vocabulary list, so it does not expire.

        INV-247 governs a CLASS ("a session- or host-level control"); a literal list can only
        ever be a snapshot of a CLI that ships separately from this plugin. Slash commands are
        that class's structural signature, so allow the two sanctioned dials and reject the
        rest — a control this repo has never heard of fails the day it appears in a question.
        """
        offenders = []
        for path in shipped_markdown():
            for n, question in pinned_questions(read(path)):
                # The question from its 👉 on, as before #424: text ahead of the 👉 on its line
                # is not the question.
                question = question[PINNED_QUESTION.search(question).start():]
                for cmd in SLASH_COMMAND.findall(question):
                    if cmd not in SANCTIONED_SLASH:
                        offenders.append(
                            "%s:%d: /%s — %s"
                            % (path.relative_to(REPO_ROOT), n, cmd, question.strip()[:110]))
        self.assertEqual(
            [], offenders,
            "a 👉 question offers a slash command that is not `/model` or `/effort`. Those two "
            "are the only Claude-interface controls the bootcamp asks the bootcamper to "
            "operate (INV-247); everything else belongs to their session:\n  "
            + "\n  ".join(offenders))

    def test_the_model_effort_switch_is_still_asked_as_a_question(self):
        """The exception must survive — otherwise this guard passes by deleting the rule's subject.

        Line-scoped by design (#424): a presence check fails closed. A wrap can hide a
        question from the line read and so make this fail, never pass one that is missing.
        """
        asked = [line
                 for path in shipped_markdown()
                 for line in read(path).splitlines()
                 if PINNED_QUESTION.search(line) and re.search(r"/model|/effort|reasoning effort", line)]
        self.assertTrue(asked,
                        "no 👉 question offers the model/effort switch any more; INV-247 names "
                        "it as the sole exception, so its disappearance means the exception or "
                        "the question form changed")

    def test_a_wrapped_question_offering_a_host_control_is_caught(self):
        """Negative control (#424): the control is named on the line the question wraps onto."""
        wrapped = ("👉 **Before we load, would you like to switch on\nauto mode, or "
                   "run `/compact` first?**\n")
        (n, question), = pinned_questions(wrapped)
        self.assertEqual(1, n)
        self.assertTrue(HOST_CONTROL.search(question))
        self.assertIn("compact", SLASH_COMMAND.findall(question))
        # The old line-at-a-time check, kept only to show the fixture is the hard case.
        first = wrapped.split("\n")[0]
        self.assertFalse(HOST_CONTROL.search(first))
        self.assertEqual([], SLASH_COMMAND.findall(first))

    def test_a_question_followed_by_prose_about_the_host_is_not_flagged(self):
        """Must-not-flag (INV-282): the next block is not the question."""
        text = ("👉 **Shall we load the sample now?**\n\n"
                "(Auto mode belongs to your Claude session; the bootcamp never offers it.)\n")
        self.assertEqual([], [n for n, q in pinned_questions(text) if HOST_CONTROL.search(q)])

    def test_a_wrapped_suppression_claim_is_caught(self):
        """Negative control (#424): "the plugin" ends line 1 and "disables auto" begins line 2."""
        wrapped = "During the bootcamp the plugin\ndisables auto mode for you.\n"
        self.assertEqual([1], match_lines(wrapped, SUPPRESSION_CLAIM))
        self.assertFalse(any(SUPPRESSION_CLAIM.search(l) for l in wrapped.split("\n")))

    def test_no_shipped_file_claims_the_plugin_suppresses_a_host_control(self):
        offenders = []
        for path in shipped_markdown():
            text = read(path)
            for n in match_lines(text, SUPPRESSION_CLAIM):
                rel = path.relative_to(REPO_ROOT)
                offenders.append("%s:%d: %s" % (rel, n, text.split("\n")[n - 1].strip()[:140]))
        self.assertEqual(
            [], offenders,
            "a shipped file claims the bootcamp removes a host control. It cannot — a plugin "
            "ships skills, hooks and commands, none of which reach the host's own "
            "affordances — and the claim would hide the scope this spec had to narrow to:\n  "
            + "\n  ".join(offenders))


class ThisGuardDisclosesWhatItCannotSee(unittest.TestCase):
    """A guard that over-claims certifies what it never tested.

    Both limits are asserted because the file previously stated one of them emphatically and
    was silent on the other, which reads as completeness — the reader meets a ⛔ caveat and
    reasonably concludes it is *the* caveat.
    """

    #: ⛔ Assert against the module DOCSTRING, never this file's source text.
    #:
    #: An earlier version read `Path(__file__)` and three mutations ESCAPED: each assertion's
    #: own regex literal lives in that source, so every check matched its own pattern string
    #: and passed with the docstring gutted. A guard that greps the file it is written in
    #: certifies itself. `__doc__` contains the prose and not the patterns, so the needle can
    #: only come from the disclosure. The snapshot-date check below still reads source — it
    #: must, since that marker is a `#` comment — but its pattern uses `\d{4}` escapes and so
    #: cannot match itself.
    def setUp(self):
        self.doc = __doc__ or ""

    def test_the_runtime_limit_is_disclosed(self):
        self.assertRegex(
            self.doc, r"(?i)cannot detect a runtime-improvised question",
            "the docstring no longer says this guard cannot see a question improvised at "
            "runtime — the reported defect existed in no file, so a clean run would read as "
            "proof of something never tested")

    def test_the_vocabulary_limit_is_disclosed(self):
        self.assertRegex(
            self.doc, r"(?i)vocabulary check is a closed, dated list",
            "the docstring no longer says the HOST_CONTROL match is a closed list, so a "
            "control phrased outside it passes while the guard reads as enforcing the class "
            "INV-247 actually governs")

    def test_the_snapshot_list_carries_its_date(self):
        self.assertRegex(
            read(Path(__file__)), r"SNAPSHOT, NOT A CLOSED SET — dated \d{4}-\d{2}-\d{2}",
            "HOST_CONTROL lost its dated snapshot marker; an undated list of a third party's "
            "vocabulary cannot be told from a complete one")

    def test_the_open_ended_check_is_named_as_the_one_to_prefer(self):
        self.assertRegex(
            self.doc, r"(?i)It is the assertion to prefer",
            "the docstring no longer points the reader from the expiring vocabulary check to "
            "the structural one, so a maintainer extending the list would not learn there is "
            "a check that needs no extending")


class TheRuleShipsWhereItBinds(unittest.TestCase):
    def setUp(self):
        self.text = read(GROUND_RULES)

    def test_the_protocol_closes_the_question_set(self):
        protocol = section(self.text, "## Conversation protocol (the 👉 rules)")
        self.assertRegex(
            protocol, r"(?i)traces to a step in a shipped skill file",
            "the 👉 protocol still governs only a question's count, shape and placement — "
            "nothing requires a question to come from a step in a skill file (INV-247)")
        self.assertRegex(
            protocol, r"(?i)never present a session- or host-level control as a bootcamp question",
            "the protocol does not name the class of question that produced this defect")
        self.assertRegex(
            protocol, r"INV-247",
            "the closed-question-set rule ships without its invariant ID, so a later editor "
            "cannot look up why it is there (INV-183)")

    def test_the_protocol_says_answering_a_bootcamper_question_is_not_originating_one(self):
        protocol = section(self.text, "## Conversation protocol (the 👉 rules)")
        self.assertRegex(
            protocol, r"(?i)answering a question the bootcamper asks is not originating one",
            "the rule reads as forbidding the guide to respond when a bootcamper raises a "
            "host control, which would strand them at a pending gate")

    def test_the_two_turn_shapes_are_stated_as_alternatives(self):
        """One sentence said re-present, the next called a counter-question the turn's single 👉.

        Nothing said they were alternatives, so following both ends the turn on TWO 👉 — the
        violation this file itself calls the #1 bootcamper complaint, fourteen lines above.
        """
        protocol = section(self.text, "## Conversation protocol (the 👉 rules)")
        self.assertRegex(
            protocol, r"(?i)ends one of \*\*two\*\* ways, never both",
            "the host-control handling clause does not state that re-presenting the pending "
            "question and asking a clarifying counter-question are alternatives, so a guide "
            "following both ends the turn on two 👉 (INV-251)")
        self.assertRegex(
            protocol, r"(?i)doing both ends the turn on two .{0,4}, which INV-251 forbids",
            "the clause does not name the consequence of doing both, so the alternation reads "
            "as a stylistic preference rather than a rule")
        self.assertRegex(
            protocol, r"(?i)the pending question waits for the turn \*\*after\*\* it",
            "nothing says where the pending question goes when a counter-question takes the "
            "turn's 👉 — a deferral with no destination is a deletion (INV-007)")

    def test_the_any_time_controls_preamble_does_not_read_as_an_INV_005_exemption(self):
        """"Never count against the one-question-per-turn rule" compounded the ambiguity."""
        controls = section(self.text, "## Any-time bootcamper controls")
        self.assertRegex(
            controls, r"(?i)invoking\*\* one is not a bootcamp question",
            "the preamble does not distinguish the bootcamper INVOKING a control from the "
            "turn's 👉 budget, so it reads as a blanket exemption from INV-251's count")
        self.assertRegex(
            controls, r"(?i)the turn still ends on \*\*exactly one\*\*",
            "the preamble does not restate that INV-251 still binds, which is the reading that "
            "let a host-control detour carry a second 👉")

    def test_the_sole_exception_is_stated_where_the_precedent_is_set(self):
        """A limit stated only in the protocol is read by nobody writing a new nudge."""
        banners = section(self.text, "## Module start banners and transitions")
        self.assertRegex(
            banners, r"(?i)ONLY Claude-interface control the bootcamp asks the bootcamper to operate",
            "the model/effort section does not say it is the only Claude-interface control "
            "the bootcamp offers, so a reader adding a second one never meets the limit "
            "(INV-247)")
        self.assertRegex(
            banners, r"INV-247",
            "the sole-exception line ships without its invariant ID")

    def test_a_bootcamper_question_about_a_host_control_has_a_stated_answer(self):
        controls = section(self.text, "## Any-time bootcamper controls")
        self.assertRegex(
            controls, r"(?i)a host control the bootcamper raises",
            "the any-time controls have no entry for a bootcamper raising a host "
            "control, which is what happened here — at a pending gate (INV-247)")
        self.assertRegex(
            controls, r"(?i)one sentence",
            "the handling line does not bound the answer, so a session setting can grow into "
            "a detour of its own")
        self.assertRegex(
            controls, r"(?i)re-present the pending .{0,4} question verbatim",
            "the handling line does not return the bootcamper to the pending question, which "
            "is the half the reported run actually lost")

    def test_the_entry_fires_when_a_host_prompt_merely_APPEARS(self):
        """The reported runs were not a bootcamper ASKING — a dialog appeared at them.

        Scoped `if the bootcamper asks`, the entry misses the case that actually happened
        twice on 2026-08-15: the host drew its own prompt over a pending 👉 and nobody asked
        anything (`specs/host-rendered-control-prompt-interrupts-a-pending-question.md`).
        """
        controls = section(self.text, "## Any-time bootcamper controls")
        self.assertRegex(
            controls, r"(?i)prompt for one appeared over the bootcamp",
            "the host-control entry still fires only when the bootcamper ASKS about a "
            "control; a host-rendered prompt appearing unbidden — the observed case — "
            "reaches no branch (INV-247)")

    def test_the_answer_does_not_name_a_dismissal_affordance(self):
        """Maintainer decision, 2026-08-15: the answer stays silent on how to dismiss.

        The dialog offers "Don't show again". Naming it would direct the bootcamper to
        operate a SECOND Claude-interface control, and the model/effort switch is the only
        one INV-247 allows. The prohibition must ship, not merely be honored today.
        """
        controls = section(self.text, "## Any-time bootcamper controls")
        self.assertRegex(
            controls, r"(?i)do not name a dismissal affordance",
            "the handling line no longer forbids naming a dismissal control, so a guide may "
            "point the bootcamper at “Don't show again” — a second interface control "
            "the bootcamp is not permitted to direct (INV-247)")

    def test_the_interruption_list_names_a_host_rendered_prompt(self):
        """A four-item list of conversational interruptions is read as the set.

        The recovery rule says "any interruption", then enumerates a compaction, a session
        boundary, the feedback detour and a tangent — all conversational, all visible to the
        guide. A host dialog is neither, and INV-205's own maintenance note records what
        happens to an enumeration generalized from the instances its author had seen.
        """
        controls = section(self.text, "## Any-time bootcamper controls")
        self.assertRegex(
            controls, r"(?i)host-rendered prompt from their Claude interface",
            "the interruption list does not name a host-rendered prompt, leaving the observed "
            "case to a reader's generalization from four conversational examples (INV-007)")

    def test_no_shipped_text_claims_the_GUIDE_asked_about_auto_mode(self):
        """No run has shown that. INV-247 is prophylaxis, not a repair of an observed defect.

        Both 2026-08-15 reports describe a host-rendered dialog; the second quoted its three
        native options, which a model cannot emit. Text implying the guide asked overstates
        the evidence for a rule that stands perfectly well without it.
        """
        self.assertNotRegex(
            squash(self.text), r"(?i)bootcamper was asked about .{0,4}auto.?mode",
            "ground-rules.md again states that a bootcamper WAS ASKED about auto mode, "
            "implying the guide originated it — the prompt is host-rendered "
            "(`specs/host-rendered-control-prompt-interrupts-a-pending-question.md`)")
        self.assertRegex(
            squash(self.text), r"(?i)that prompt is host-rendered",
            "ground-rules.md no longer records that the observed prompt was host-rendered, "
            "so the next editor re-derives it as a guide defect")


class TheCorrectedAttributionIsDisclosed(unittest.TestCase):
    """This guard asserted the wrong attribution for hours; the correction must stick.

    Asserted against the module ``__doc__`` for the reason the sibling disclosure class
    documents at length: this file's own regex literals live in its source, so a check that
    read ``Path(__file__)`` would match its own pattern and pass with the prose gutted.
    """

    #: Squashed, unlike the sibling class: these needles are phrases rather than single
    #: tokens, so a rewrap of the docstring would otherwise break the assertion without
    #: the disclosure having changed at all.
    def setUp(self):
        self.doc = squash(__doc__ or "")

    def test_the_docstring_records_the_prompt_as_host_rendered(self):
        #: ⛔ Anchored to the CLAIM ("that prompt is host-rendered"), not the bare token.
        #: A mutation escaped this assertion during negative-control: the docstring also
        #: cites `specs/host-rendered-control-prompt-…md`, so `host-rendered` alone still
        #: matched with the claim gutted — the filename certified the sentence.
        self.assertRegex(
            self.doc, r"(?i)that prompt is host-rendered",
            "the docstring no longer says the observed prompt was host-rendered — it "
            "previously read “a bootcamper was asked”, which frames a harness dialog "
            "as a question the guide put to them")

    def test_the_docstring_says_no_guide_defect_has_been_OBSERVED(self):
        self.assertRegex(
            self.doc, r"(?i)no run has yet shown a guide improvising",
            "the docstring no longer distinguishes the rule (prophylaxis against a real "
            "hazard) from an observed guide defect (none recorded), which is the "
            "over-claim `coverage-reports-count-known-non-defects-as-hits` exists to stop")


if __name__ == "__main__":
    unittest.main()
