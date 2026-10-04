"""Feedback is triaged to the component that OWNS it, recorded locally either way, and
only forwarded upstream on an explicit yes.

⚠️ **Not "plugin-vs-MCP-server" -- that framing was the defect.** Until 2026-08-15 both this
docstring and the shipped taxonomy assumed a two-component world, so a defect in the Claude
Code harness had nowhere to go: it survives a perfect plugin AND a perfect server, which the
two-question test mapped to `both` ("the plugin repeated or failed to guard an **upstream**
defect") when no upstream Senzing defect exists. Two bootcamper reports on 2026-08-15 hit it,
and each wrote in its own `Routing:` field that the option set could not express the case. The
`host` verdict exists for that class (`specs/feedback-routing-has-no-verdict-for-a-defect-
neither-component-owns.md`).

Enforces **INV-248** (the closed five-verdict set, stated identically at every site) and
**INV-249** (only `mcp-server`/`both` may be offered upstream, and the shipped rule says why
`host` cannot be -- `submit_feedback` reaches Senzing, which does not ship the harness).

A bootcamper reports a symptom; identifying which component owns it is the plugin's job.
Two of the defects filed during development were upstream — `mapping_workflow` returning a
truncated validation error, `get_sdk_reference` not covering parameter shapes — and a report
that sits only in the local file reaches the wrong maintainer and gets fixed nowhere.

Three properties this pins, because getting any of them wrong is worse than not triaging:

* **Local capture is unconditional (INV-015).** The routing verdict decides whether an
  *additional* upstream submission is offered — never whether the entry is saved. Routing
  exclusively would breach INV-015 and would also lose the bootcamper their own record.
* **Nothing leaves the machine without an explicit yes.** `submit_feedback` publishes
  externally and its own contract requires showing the exact message and confirming first;
  submissions are anonymous, so a bootcamper who says yes gets no reply channel and must be
  told that before answering.
* **The bootcamper's data never leaves as part of a bug report.** Entity names and record
  IDs are theirs (INV-321) — an upstream message describes the shape of a problem, never the
  content of their records.

Enforces **INV-321** (a defect report sent off the machine carries no identifier and none of the
Bootcamper's data) in `BootcamperDataNeverLeaves`. ⚠️ It pins the stripping list and the citation
in the forward step and cannot establish that a live submission is stripped.

Run:  python3 -m unittest discover -s tests
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
FEEDBACK = PLUGIN / "skills" / "bootcamp-onboarding" / "feedback.md"
COMMAND = PLUGIN / "commands" / "bootcamp-feedback.md"
HOOK = PLUGIN / "scripts" / "feedback-capture.py"
GRADUATION = PLUGIN / "skills" / "graduation" / "SKILL.md"
ONBOARDING = PLUGIN / "skills" / "bootcamp-onboarding" / "onboarding-flow.md"

FEEDBACK_PATH = "docs/feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK.md"
#: The closed verdict set. `host` was added 2026-08-15; see the module docstring.
VERDICTS = ("plugin", "mcp-server", "both", "host", "unclear")

#: Verdicts whose entries may be OFFERED for upstream submission. `submit_feedback` reaches
#: Senzing, so this set is exactly the ones Senzing owns -- `host` is excluded by definition,
#: not by preference: Senzing does not ship the Claude Code harness.
UPSTREAM_ELIGIBLE = ("mcp-server", "both")


def verdict_set_sites():
    """Every shipped line stating the verdict set, DERIVED not listed (INV-246).

    A hardcoded list certifies the sites the author already thought of; the site added later
    is the only one that matters. Membership floor below keeps the scan honest.

    ⚠️ **An enumeration site is a pipe-separated series naming `mcp-server`** — the two shapes
    the plugin actually uses, ``[plugin | mcp-server | …]`` and ``` `plugin` | `mcp-server` | … ```.
    Markdown table rows are excluded (they start with a pipe and define one verdict per row, not
    the series).

    Three earlier versions of this scan were wrong, all caught self-auditing the commits that
    introduced them — recorded because the sequence is the point, not the destination:

    * Keying on ``Routing:`` reached the entry template and graduation's copy but missed
      `feedback.md`'s sanctioned-external-path rule — a narrower site set than the rule's reach,
      the exact INV-246 defect this guard enforces against.
    * Keying on "three or more backticked verdicts" over-reached onto local-only subset lines
      **and** still missed the entry template, which uses no backticks.
    * Keying on "names an eligible verdict and a non-eligible one" matched ordinary prose:
      ``both``, ``plugin`` and ``host`` are common English words, so *"Yes to the middle two →
      **both** (the plugin repeated…)"* scored as an enumeration.

    Local-only subset lines are a **different** claim and are checked separately by
    ``LocalOnlyVerdictsAreNamedWhereverTheRuleIsStated`` — requiring all five there would fail
    correct content.

    ⛔ **What this scan CANNOT see, stated because INV-248 says "every shipped site".** It
    recognizes the pipe-separated series and nothing else. A site that enumerated the taxonomy as
    a bulleted list, a comma series, or prose would escape it entirely — so a clean run means "no
    *pipe-separated* site has drifted", never "the taxonomy is stated identically everywhere". The
    shape is checked rather than the meaning because "is this line enumerating the taxonomy?" is a
    semantic judgment, and the two looser rules tried first both failed (above). If a third shape
    ever ships, extend this — do not read a green run as proof it did not.

    Line-scoped by design (#424): each series ships as one bracketed or backticked list on one
    line, and a whitespace-collapsed block is coarser than a series, so a verdict named in
    prose beside a series would stand in for the one missing from it.
    """
    hits = []
    for path in sorted(PLUGIN.rglob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("|"):
                continue                      # a table row defines one verdict, not the series
            if "mcp-server" in line and line.count("|") >= 3:
                hits.append((path, line))
    return hits


def local_only_rule_lines():
    """Lines stating which verdicts stay on the machine, DERIVED not listed (INV-246).

    Separate from the enumeration sites because the claim is different: these name a *subset*
    deliberately. They matter most, though — each one is a place a verdict could silently become
    upstream-eligible by omission.
    """
    hits = []
    for path in sorted(PLUGIN.rglob("*.md")):
        hits += [(path, line) for line in local_only_rule_lines_in(path.read_text(encoding="utf-8"))]
    return hits


#: The phrases that state the local-only rule. Matched by ``match_lines`` across line wraps
#: (#424), so "skip this step\nentirely" is still a site.
LOCAL_ONLY_MARKERS = re.compile(r"skip this step entirely|stays local")


def local_only_rule_lines_in(text):
    """The line on which each local-only marker starts.

    The marker is found across line wraps; the verdicts are still asserted on the line where
    it starts, as before #424, which is where this rule's sites name them.
    """
    lines = text.split("\n")
    return [lines[n - 1] for n in sorted(set(match_lines(text, LOCAL_ONLY_MARKERS)))]


def read(path):
    return Path(path).read_text()


def plain(text):
    return re.sub(r"\s+", " ", text.replace("**", ""))


def onboarding_overview():
    """Step 3 of the preface — the WELCOME banner and the overview every bootcamper reads
    first, ending where the 'any questions' gate begins."""
    t = read(ONBOARDING)
    return t[t.index("## 3. Welcome and overview") : t.index("## 4. Any questions")]


def triage_step():
    t = read(FEEDBACK)
    return t[t.index("## Step 2b: Triage") : t.index("## Step 3: Append")]


def forward_step():
    t = read(FEEDBACK)
    return t[t.index("## Step 3c: Offer to forward") : t.index("## Step 4: Confirm")]


def hook_context(prompt, active=True):
    """Run the UserPromptSubmit hook. It is deliberately inert outside an active bootcamp,
    so the activation marker must exist for it to fire at all."""
    cwd = tempfile.mkdtemp()
    if active:
        os.makedirs(os.path.join(cwd, "config"), exist_ok=True)
        with open(os.path.join(cwd, "config", "bootcamp_progress.json"), "w") as fh:
            fh.write("{}")
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps({"prompt": prompt}),
        capture_output=True, text=True, cwd=cwd,
    )
    if not proc.stdout.strip():
        return ""
    return json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]


class TheTriggerIsTaughtBeforeItCanBeUsed(unittest.TestCase):
    """INV-196: the preface teaches the feedback trigger before the first content module.

    A control nobody is told about is reachable only by people who were told out of band.

    The phrase used to appear in four files: the workflow itself, the guide's own ground rules,
    one mid-bootcamp module, and graduation — i.e. everywhere except the one place every
    bootcamper reads before the first module. Feedback arriving only from those who already knew
    the phrase skews every entry the project receives, so the mention must live in
    bootcamper-facing overview text, not in developer-only prose that reads as if it did.
    """

    def setUp(self):
        self.overview = onboarding_overview()

    def test_the_overview_names_the_trigger_phrase(self):
        self.assertIn("bootcamp feedback:", self.overview)

    def test_the_mention_is_bootcamper_facing_overview_content(self):
        """A bullet in the overview is spoken to the bootcamper; surrounding agent prose is not.
        Asserting only on the file would pass again if the line were demoted to an instruction."""
        bullets, current = [], None
        for line in self.overview.splitlines():
            if line.startswith("- "):
                current = [line]
                bullets.append(current)
            elif current is not None and line.startswith("  ") and line.strip():
                current.append(line)          # wrapped continuation of the same bullet
            else:
                current = None
        teaching = [b for b in bullets if "bootcamp feedback:" in " ".join(b).lower()]
        self.assertTrue(
            teaching, "the trigger must be taught in an overview bullet, not only in agent prose"
        )

    def test_it_is_taught_before_the_first_content_module(self):
        """Step 3 precedes the Bootcamp preparation handoff, which precedes every module."""
        t = read(ONBOARDING)
        self.assertLess(
            t.index("bootcamp feedback:"),
            t.index("## 5. Hand off to the Bootcamp preparation module"),
            "the trigger must be taught in the preface, not after the handoff",
        )

    def test_it_promises_the_bootcamper_keeps_their_place(self):
        """That is the barrier — raising something must not read as abandoning the module
        (INV-074 brackets the flow and restores the pending question)."""
        squashed = plain(self.overview)
        self.assertIn("You do not lose your place", squashed)
        self.assertIn("comes straight back", squashed)

    def test_it_is_a_statement_not_a_question(self):
        # Line-scoped by design (#424): a 👉 that opens a line opens a question, and a
        # question opens on one line however it wraps after that.
        posed = [l for l in self.overview.splitlines() if l.lstrip().startswith("👉")]
        self.assertEqual([], posed, "the preface overview must not pose a 👉 question")
        self.assertIn("never make it a 👉 question", plain(self.overview))

    def test_it_is_verbosity_aware(self):
        """Explanatory output: suppressed under `minimal`, one line under `concise`
        (INV-011/INV-012), the treatment INV-096 gives the time estimate."""
        squashed = plain(self.overview)
        self.assertIn("verbosity-aware", squashed)
        self.assertIn("under `minimal`, suppress it", squashed)
        self.assertIn("under `concise`, one line", squashed)

    def test_it_is_not_repeated_at_every_module_start(self):
        """An always-available control repeated at every boundary is the noise INV-012 suppresses."""
        self.assertIn("Do not repeat it at every module start", plain(self.overview))

    def test_the_graduation_invitation_is_still_there(self):
        """Late is not useless — it is a last invitation with the whole run in view. Teaching the
        phrase early must not trade one gap for another."""
        self.assertIn(
            'Say \\"bootcamp feedback\\" anytime if you\'d like to share your experience.',
            read(GRADUATION),
        )


class TriageStepExists(unittest.TestCase):
    def test_workflow_has_a_triage_step(self):
        self.assertIn("## Step 2b: Triage", read(FEEDBACK))

    def test_every_verdict_is_defined(self):
        step = triage_step()
        for verdict in VERDICTS:
            with self.subTest(verdict=verdict):
                self.assertIn(f"`{verdict}`", step)

    def test_triage_is_silent_not_a_question(self):
        """The bootcamper reported a symptom; naming the component is not their job."""
        step = triage_step()
        self.assertIn("no 👉 question", step)
        # Line-scoped by design (#424): a 👉 that opens a line opens a question.
        posed = [l for l in step.splitlines() if l.lstrip().startswith("👉")]
        self.assertEqual([], posed, "triage must not pose a question to the bootcamper")

    def test_the_discriminating_test_is_stated_both_ways(self):
        squashed = plain(triage_step())
        self.assertIn("Would this still happen if the bootcamp plugin were perfect?", squashed)
        self.assertIn("Would this still happen if the Senzing MCP server were perfect?", squashed)

    def test_the_test_asks_about_the_host_too(self):
        """Two questions alone route a harness defect to `both`, which is wrong.

        A Claude Code harness defect survives a perfect plugin AND a perfect server. Without a
        third question the stated rule yields `both` — "the plugin repeated or failed to guard
        an upstream defect" — and `both` is upstream-eligible, so the wrong verdict would offer
        to send a harness report to Senzing.
        """
        squashed = plain(triage_step())
        self.assertIn(
            "Would this still happen with a perfect bootcamp plugin and a perfect Senzing MCP "
            "server?", squashed,
            "the triage test no longer asks whether NEITHER component owns the defect, so a "
            "harness report falls through to `both` or `unclear`")

    def test_host_is_defined_as_owned_by_the_claude_interface(self):
        #: ⛔ Anchored to the TABLE ROW, not to tokens anywhere in the step. Line-scoped by
        #: design (#424): a table row is one line. A mutation escaped
        #: during negative-control: deleting the `host` row still passed, because both "`host`"
        #: and "Claude interface" also appear in the discriminating question above the table.
        #: Every verdict needs a row — the table is where a triaging guide actually looks.
        rows = [l for l in triage_step().splitlines()
                if l.startswith("| `host`")]
        self.assertEqual(
            1, len(rows),
            "the verdict table has no `host` row; the discriminating question can name a "
            "verdict the table never defines, which is how a guide ends up guessing")
        self.assertRegex(
            rows[0], r"(?i)Claude interface",
            "the host row does not name the Claude interface as the owner, leaving it "
            "indistinguishable from `unclear`")
        self.assertRegex(
            rows[0], r"(?i)neither the bootcamp nor Senzing",
            "the host row does not say that NEITHER component ships it — the fact that "
            "decides it is not forwarded upstream")


class HostIsNeverForwardedUpstream(unittest.TestCase):
    """`submit_feedback` reaches Senzing, which does not ship the Claude Code harness.

    This is the sharp end of the taxonomy: a verdict that is upstream-eligible by accident
    misroutes a bootcamper's report to a party that cannot act on it, anonymously, with no
    reply channel. `host` must be excluded by rule, and the rule must say why.
    """

    def test_the_forward_step_excludes_host(self):
        step = plain(forward_step())
        self.assertRegex(
            step, r"For `plugin`, `host` or `unclear`, skip this step entirely",
            "Step 3c no longer skips the forward for a `host` verdict")

    def test_only_the_eligible_verdicts_trigger_the_offer(self):
        step = plain(forward_step())
        self.assertRegex(
            step, r"Only when Step 2b's verdict is .{0,6}`mcp-server`.{0,6} or .{0,6}`both`",
            "the forward step's eligibility clause changed; verify `host` is still excluded")
        for verdict in VERDICTS:
            if verdict not in UPSTREAM_ELIGIBLE:
                with self.subTest(verdict=verdict):
                    self.assertNotRegex(
                        step, r"verdict is \*\*`%s`\*\*" % re.escape(verdict),
                        "%r is not upstream-eligible but the forward step names it as a "
                        "trigger" % verdict)

    def test_the_reason_host_cannot_be_forwarded_is_stated(self):
        """A rule with no reason gets 'helpfully' relaxed by the next editor."""
        step = plain(forward_step())
        self.assertRegex(
            step, r"(?i)submit_feedback.{0,40}reaches \*\*Senzing\*\*|reaches Senzing",
            "Step 3c no longer says WHERE submit_feedback goes, which is the whole reason a "
            "harness report must not be sent through it")


class EverySiteStatesTheSameVerdictSet(unittest.TestCase):
    """One taxonomy, stated in several places — they must not drift apart (INV-246).

    Sites are DERIVED by scanning shipped Markdown for a `Routing:` line naming the verdicts,
    never from a hardcoded path list: a listed guard certifies the files already thought of and
    is blind to a module added later.
    """

    def test_the_scan_finds_the_sites_known_today(self):
        """Membership floor — stronger than a count, which survives one site swapping for another."""
        found = {p.name for p, _ in verdict_set_sites()}
        for expected in ("feedback.md", "SKILL.md"):
            with self.subTest(site=expected):
                self.assertIn(expected, found,
                              "the verdict-set scan no longer reaches %s" % expected)

    def test_every_site_lists_every_verdict(self):
        sites = verdict_set_sites()
        self.assertGreaterEqual(len(sites), 2, "the scan matched too few sites to be meaningful")
        for path, line in sites:
            for verdict in VERDICTS:
                with self.subTest(site=path.name, verdict=verdict):
                    self.assertIn(
                        verdict, line,
                        "%s states the verdict set without %r — the taxonomy has drifted "
                        "between its sites (INV-246)" % (path.name, verdict))


class LocalOnlyVerdictsAreNamedWhereverTheRuleIsStated(unittest.TestCase):
    """Every place saying what stays local must name every non-eligible verdict (INV-249).

    These lines are where a verdict becomes upstream-eligible **by omission** — leave one out
    and the rule silently permits forwarding it. They are checked apart from the enumeration
    sites because naming a subset is correct here, so the all-five assertion would reject them.
    """

    def test_the_rule_is_stated_in_more_than_one_place(self):
        lines = local_only_rule_lines()
        self.assertGreaterEqual(
            len(lines), 2,
            "the local-only rule is stated in fewer places than expected — either it was "
            "removed, or the marker phrases this scan derives from were reworded")

    def test_a_wrapped_marker_is_still_a_site(self):
        """Negative control (#424): "skip this step" ends line 1 and "entirely" begins line 2."""
        wrapped = "For `plugin` or `unclear`, skip this step\nentirely and continue to Step 4.\n"
        self.assertEqual(["For `plugin` or `unclear`, skip this step"],
                         local_only_rule_lines_in(wrapped))
        # The old line-at-a-time scan, kept only to show the fixture is the hard case.
        self.assertFalse(any(LOCAL_ONLY_MARKERS.search(l) for l in wrapped.split("\n")))

    def test_each_names_every_non_eligible_verdict(self):
        for path, line in local_only_rule_lines():
            for verdict in VERDICTS:
                if verdict in UPSTREAM_ELIGIBLE:
                    continue
                with self.subTest(site=path.name, verdict=verdict):
                    self.assertIn(
                        "`%s`" % verdict, line,
                        "%s states which verdicts stay local without naming %r, so that "
                        "verdict is upstream-eligible by omission (INV-249): %s"
                        % (path.name, verdict, line.strip()[:80]))

    def test_each_verdict_carries_concrete_examples(self):
        """Criteria without examples get applied inconsistently."""
        step = triage_step()
        for probe in ("mapping_workflow", "get_sdk_reference", "PDF generator", "flag documented"):
            with self.subTest(probe=probe):
                self.assertIn(probe, step)

    def test_misfiling_toward_plugin_is_called_out(self):
        self.assertIn("Do not soften an", plain(triage_step()))


class LocalCaptureIsUnconditional(unittest.TestCase):
    """INV-015 has no exception clause."""

    def test_triage_step_says_the_verdict_never_changes_local_recording(self):
        squashed = plain(triage_step())
        self.assertIn("The verdict never changes whether the entry is recorded locally", squashed)
        self.assertIn("INV-015", triage_step())

    def test_entry_template_carries_routing_and_upstream_fields(self):
        t = read(FEEDBACK)
        self.assertIn("**Routing:**", t)
        self.assertIn("**Upstream:**", t)

    def test_upstream_field_can_record_every_outcome(self):
        t = read(FEEDBACK)
        for outcome in ("not applicable", "offer pending", "offered, declined", "submitted",
                        "submission failed"):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, t)

    def test_forward_step_runs_only_after_the_local_entry_is_confirmed(self):
        """Ordering matters: a failed send must never cost the bootcamper their record."""
        t = read(FEEDBACK)
        self.assertLess(
            t.index("## Step 3b: Verify it landed"),
            t.index("## Step 3c: Offer to forward"),
            "the durability check must precede any upstream offer",
        )
        self.assertIn("after Step 3b has confirmed", plain(forward_step()))

    def test_shipped_file_header_states_the_local_always_guarantee(self):
        """The artifact itself should tell the bootcamper what happened to their report."""
        t = read(FEEDBACK)
        header = t[t.index("# Senzing Bootcamp Plugin Feedback") :][:600]
        self.assertIn("Every entry is saved here", header)
        self.assertIn("only ever with your explicit yes", header)


class NothingLeavesWithoutConsent(unittest.TestCase):
    def setUp(self):
        self.step = forward_step()

    def test_offer_is_gated_on_the_verdict(self):
        squashed = plain(self.step)
        self.assertIn("Only when Step 2b's verdict is", squashed)
        # Derived from UPSTREAM_ELIGIBLE rather than pinned as a sentence, so adding a sixth
        # verdict cannot pass by leaving this assertion's literal untouched. Each non-eligible
        # verdict must appear in the skip clause; the clause's prose shape is not pinned here.
        clause = squashed[squashed.index("skip this step entirely") - 120:
                          squashed.index("skip this step entirely")]
        for verdict in VERDICTS:
            if verdict not in UPSTREAM_ELIGIBLE:
                with self.subTest(verdict=verdict):
                    self.assertIn(
                        "`%s`" % verdict, clause,
                        "%r is not upstream-eligible but the skip clause does not name it, so "
                        "the forward step may be offered for it" % verdict)

    def test_the_question_is_pinned_and_numbered(self):
        self.assertIn(
            "👉 **This looks like an issue in the Senzing MCP server rather than the bootcamp. "
            "Send the report above to Senzing? Reply with a number:**",
            self.step,
        )
        self.assertIn("1. **Yes, send it**", self.step)
        self.assertIn("2. **No, keep it local**", self.step)

    def test_exact_message_is_shown_before_asking(self):
        """The submit_feedback tool's own contract requires this."""
        squashed = plain(self.step)
        self.assertIn("Show the exact message and ask", squashed)
        self.assertIn("requires showing the", squashed)

    def test_anonymity_is_disclosed_before_the_bootcamper_answers(self):
        squashed = plain(self.step)
        self.assertIn("anonymous", squashed)
        self.assertIn("support@senzing.com", squashed)

    def test_asked_once(self):
        self.assertIn("INV-006", self.step)
        self.assertIn("do not re-offer", plain(self.step))

    def test_declining_is_free_and_failure_never_blocks(self):
        squashed = plain(self.step)
        self.assertIn("Saying no costs them nothing", squashed)
        self.assertIn("never blocks anything", squashed)

    def test_no_blanket_prohibition_remains_that_would_forbid_the_new_path(self):
        """The old rule said never submit externally; it must now point at the one sanctioned path."""
        t = read(FEEDBACK)
        self.assertNotIn(
            "Do NOT submit feedback to the Senzing MCP server or anywhere external unless", t
        )
        self.assertIn("The only sanctioned external path is Step 3c", plain(t))


class BootcamperDataNeverLeaves(unittest.TestCase):
    def test_identifying_details_must_be_stripped(self):
        squashed = plain(forward_step())
        for probe in ("hostname", "username", "IP\naddress".replace("\n", " "), "email"):
            with self.subTest(probe=probe):
                self.assertIn(probe, squashed)
        self.assertIn("INV-321", forward_step())

    def test_record_content_is_explicitly_out_of_scope(self):
        squashed = plain(forward_step())
        self.assertIn("describe the shape of the problem, never the", squashed)
        self.assertRegex(squashed, r"Entity names\s*and record IDs from their data are theirs")

    def test_message_must_be_self_contained(self):
        """The upstream reader cannot see this bootcamp."""
        squashed = plain(forward_step())
        self.assertIn("the recipient cannot see this bootcamp", squashed)
        self.assertIn("tool name", squashed)
        self.assertIn("SDK version", squashed)

    def test_category_mapping_is_specified(self):
        squashed = plain(forward_step())
        self.assertIn("`category` = `bug`", squashed.replace("**", ""))
        self.assertIn("`feature`", squashed)

    def test_server_response_is_relayed_verbatim(self):
        """It carries the anonymity notice and the only follow-up route."""
        self.assertIn("verbatim", plain(forward_step()))


def retrospective_section(text):
    """Graduation's Step 0 section, sliced at the NEXT heading rather than a char count.

    ⚠️ **Corrected 2026-08-28.** These assertions used `t[start : start + 4500]`, a magic
    number standing in for "the section". On 2026-08-28 the `**Non-blocking.**` bullet sat
    **18 characters** inside that window, so the guard was one edit away from failing on
    content it was never meant to police -- and it duly did, on an unrelated addition to the
    `Upstream:` bullet above it. Slicing at the real boundary measures the section the
    assertion is about. The floor below keeps it from becoming vacuous if the heading moves
    (INV-265).
    """
    start = text.index("## Step 0: Session retrospective")
    nxt = text.find("\n## ", start + 1)
    section = text[start:] if nxt == -1 else text[start:nxt]
    assert len(section) > 2000, (
        "the Step 0 retrospective section collapsed to %d chars -- these assertions would "
        "pass vacuously against a stub" % len(section))
    return section


class EveryEntryPointDescribesTheRouting(unittest.TestCase):
    """Three surfaces describe this flow; all must agree (INV-003)."""

    def test_slash_command_describes_triage_and_the_consent_gate(self):
        t = plain(read(COMMAND))
        self.assertIn("triage whether the issue is in this plugin or in the Senzing MCP server", t)
        self.assertIn("Every entry is recorded locally whatever the triage says", t)
        self.assertIn("never send anything external without that yes", t)

    def test_hook_injects_the_routing_instruction(self):
        ctx = hook_context("bootcamp feedback: a tool returned a truncated error")
        self.assertTrue(ctx, "the hook must recognize a feedback prompt")
        for probe in ("Triage", "Routing", "submit_feedback", "INV-015", "INV-321",
                      "showing the exact message"):
            with self.subTest(probe=probe):
                self.assertIn(probe, ctx)

    def test_hook_still_ignores_unrelated_prompts(self):
        self.assertEqual("", hook_context("what is entity resolution?"))

    def test_graduation_retrospective_triages_too(self):
        """Self-observed findings skew upstream — a tool behaving differently than documented
        is exactly what a bootcamper cannot report."""
        t = read(GRADUATION)
        section = retrospective_section(t)
        self.assertIn("**`Routing:`**", section)
        self.assertIn("**`Upstream:`**", section)
        self.assertIn("rather than defaulting it to `plugin`", plain(section))

    def test_retrospective_batches_the_offer(self):
        """One question for all findings, so the retrospective stays a single non-blocking step."""
        t = read(GRADUATION)
        self.assertIn("Batch the offer", plain(retrospective_section(t)))

    def test_retrospective_stays_non_blocking(self):
        t = read(GRADUATION)
        section = retrospective_section(t)
        self.assertIn("Non-blocking", section)
        self.assertIn("INV-015", section)


if __name__ == "__main__":
    unittest.main()
