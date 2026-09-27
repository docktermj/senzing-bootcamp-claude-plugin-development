# Phase 3 — The conversational layer

Walk the bootcamp with the **maintainer answering as the Bootcamper**. This is the
only phase that tests what the plugin actually is: a conversation. Phases 1 and 2
test its dependencies.

## Why this cannot be self-played

⛔ **The assistant must not play both roles.** Two independent reasons, and both are
disqualifying:

1. `ground-rules.md` forbids fabricating the Bootcamper's response, and INV-007 says
   the plugin "cannot answer questions nor assume answers". Simulating the answers
   violates the thing under test.
2. Even if it were permitted, an assistant that knows it is being graded on
   one-👉-per-turn discipline will comply. The behavior under test is *whether the
   files produce that discipline*, which self-play cannot distinguish from the
   assistant simply being careful.

If the maintainer is not available, report phase 3 as **untested**. Do not
approximate it, and do not describe a self-played walkthrough as a dry run.

## Where the analysis starts — ask before scaffolding anything

⛔ **The first thing this phase does is ask the maintainer which module the analysis
starts at.** List the modules in order, numbered, and ask for one number. Do not
scaffold, do not begin the walk, and do not assume the top of the bootcamp.

**Why.** The bootcamp is cheap to walk; the *analysis* is what fills the context
window — the test-notes blocks, the pinned-wording comparisons, the invariant lookups,
the ledger drafts written mid-walk. A run that analyzes from the onboarding preface
exhausts its context somewhere around Discover the Business Problem and stops there. That is
why every walk to date has re-covered the same opening stretch, and why Data
processing, Query/Visualize/Discover and graduation have never been walked at all.
Choosing where the analysis begins is the only way the later modules get exercised.

The list is the module table in `bootcamp-preparation/SKILL.md` — **read it rather
than trusting the copy below**, which is a convenience and can go stale:

1. Bootcamp preparation — includes the onboarding preface; analysis from the first turn
2. Entity Resolution Concepts
3. Discover the Business Problem
4. SDK setup
5. System verification
6. Truth Set visualization
7. Data collection
8. Data Quality, Mapping, and Transformation
9. Data processing
10. Query, Visualize and Discover
11. Bootcamp graduation

Numbering the list here is fine — INV-079 governs what the *Bootcamper* reads, and the
maintainer is not the Bootcamper. Inside the walk itself, names only.

⛔ **Mark the environment's ceiling on the list when you present it.** The fast-forward
has to genuinely reach the chosen module, and from **SDK setup** onward that means a
real Senzing install, a database, and a license. Use the environment check from the
SKILL's "Before you start" step 3 and say plainly which of the eleven are reachable
today, so the maintainer picks knowing where the walk would stall. A choice past the
ceiling is still the maintainer's to make — just do not let them make it blind.

Recommend a module **later than the last run analyzed**, and name that module when you
recommend it. Nothing in the repo records it, so the previous run's report is the only
memory this rotation has.

### The fast-forward stretch — everything before the chosen module

Run the bootcamp exactly as a Bootcamper would see it, and nothing else.

- **Follow the skill files as written.** The fast-forward is what puts the project into
  the state the chosen module reads, so improvising through it invalidates the analysis
  that follows. This is not a skim.
- **The maintainer still answers.** ⛔ The no-fabrication rule above is not relaxed here.
  Fast-forward is the same walk with the *notes* turned off, not a simulation.
- **No analysis.** No test-notes blocks, no invariant lookups, no character-for-character
  gate comparisons, no ledger drafts. If something looks off, let it go — those modules are what
  earlier runs covered and what a later run can start at.
- **One exception: a blocker.** If the guide cannot proceed — an unsatisfiable
  instruction, a missing file, a failed tool call — that is the walk failing, not an
  observation. Draft it into the run's ledger entry, then continue if you can. It costs
  context and is worth it.
- **Do not narrate the fast-forward.** No inter-module summaries, no progress
  announcements, no "still fast-forwarding". Module-completion output the Bootcamper
  would see is bootcamp output and stays.

To shorten it: scaffold with `--seeded` and keep `verbosity: minimal`, which makes
Bootcamp preparation ask nothing at all. Prefer that whenever the analysis starts past
Bootcamp preparation — a short fast-forward leaves more context for the part being tested.

⚠️ **The fast-forward is not free.** It still reads each module's `SKILL.md` in full,
which is a real share of the window. What it removes is the analysis on top of that.

### The analysis stretch — from the chosen module on

Everything else in this file switches on the moment the chosen module starts: the
two-channel discipline, the watch list, draft-on-sight. Tell the maintainer in one line
that the analysis starts here, so they know which channel they are reading.

Before its first turn, read that module's own `SKILL.md` and the invariants it cites.
The watch list below is what breaks most often *anywhere*; it is not the list for any
particular module.

## Setup

Every walk starts from a fresh project — the fast-forward is what advances it — so the
choice here is only which preference fixture it starts with.

**If the analysis starts at Bootcamp preparation,** scaffold **empty** (no
`bootcamp_progress.json` content, no preferences) to test the fresh-start path:

```bash
python3 .claude/skills/dry-run/scaffold_project.py "$HOME/senzing-bootcamp-phase3" --fresh
```

**Then do a second, short walk with `--seeded`.** It pre-fills exactly the preferences
INV-133 makes honorable (`path`, `verbosity: minimal`, `programming_language: Java`), so
Bootcamp preparation must **skip** Steps 1, 3 and 4 and mark each line
"from your saved preferences" in its Step 7 recap:

```bash
python3 .claude/skills/dry-run/scaffold_project.py "$HOME/senzing-bootcamp-phase3" --seeded
```

Both directions are needed and the first run only proves one of them. A walk where
everything was asked exercises the honor path **only in its inert direction** — it shows
the rule does not fire when it shouldn't, and says nothing about whether it fires when it
should. The seeded walk is short: preparation should ask nothing at all and hand straight
off, which is also the fastest way to catch a step that asks anyway.

**If the analysis starts anywhere later,** scaffold with `--seeded` and skip the
second walk. Both fixtures differ only in what Bootcamp preparation does, which is
now fast-forwarded rather than analyzed, so the pair proves nothing here — and
`--seeded` is the shorter fast-forward. Say in the report that the INV-133 pair was
not run, so a later run knows it is still owed.

**How far the walk can go.** **Onboarding preface → Bootcamp preparation → Module 0 →
Module 1** needs MCP access and nothing else, and covers the densest concentration of
interaction invariants in the plugin. From **SDK setup** onward the walk needs a real
install, a database and a license — which is the ceiling to state when presenting the
module list, and the thing that stops the fast-forward if the environment lacks them.

Tell the maintainer up front where the analysis starts, how far you expect to get, and
that they should answer as themselves throughout — including the fast-forward.

## How to run it

Follow the skill files **as written**, not from memory of what they should say. Read
`onboarding-flow.md`, then `bootcamp-preparation/SKILL.md`, and execute their
numbered steps in order. The point is to find where following them faithfully
produces something wrong — which cannot happen if you are improvising a good
bootcamp instead.

Keep the two channels separate — **in the analysis stretch**; the fast-forward has only
the first of them:

- **The bootcamp output** — exactly what a Bootcamper would see. Nothing else.
- **A collapsed test-notes block** after it, clearly marked ignorable, holding your
  observations. Do not narrate findings inside the bootcamp text; it changes what is
  being tested.

⛔ **The test-notes blocks are working notes, not the record.** They live in the conversation
and die with it. The moment an observation firms up into a finding, draft it into the run's
ledger entry — the SKILL's "The finding lifecycle", step 1. Do this *during* the walk, not at
the end: this phase stops on whatever turn the maintainer stops it, so "I'll write it up when
we finish" is a bet that there is a finish. A walk that reached eight turns holding four
findings in conversation alone is why this paragraph exists. ⛔ **Drafting is mid-walk; filing
is not.** The lifecycle asks its filing question only when the walk pauses or ends, so no
bootcamp turn ever carries it.

## What to watch for

Interaction invariants, in rough order of how often they break:

- **INV-251 / one 👉 per turn.** Exactly one, ending the turn. **Two or more breaches
  INV-251; zero breaches INV-225** — including a stray question inside an
  acknowledgment. (Not INV-005, which is the 👉 *marker* rule and says nothing about
  count; relabeled 2026-08-15.)
- **INV-133 / saved preferences.** A preference already in
  `config/bootcamp_preferences.yaml` must be honored and its question **not asked**.
  Pre-seed one (e.g. `verbosity: minimal`) on a second run and see whether it is
  asked anyway. Only `model_guidance` implements the read-first check today.
- **INV-006 / ask-once.** Nothing re-asked unless the Bootcamper requested a repeat.
- **INV-058 / one consolidated write.** Bootcamp preparation must show the maintainer
  **one** config diff, not one per gate. Count the diffs.
- **Apparatus exemptions.** Bootcamp preparation and Module 0 must show *no* journey
  map, before/after, step overview, time estimate, or model/effort nudge (INV-075,
  INV-078). Content modules must show all of them (INV-028–031, INV-096).
- **INV-079 / names not numbers.** No "Module 4" in anything the Bootcamper reads,
  including casual acknowledgments.
- **INV-051 / no "or" joining choices.** Numbered lists, neutral lead question. The
  only sanctioned "or" is a trailing `(respond yes or no)`.
- **INV-112 / the quiz offer.** Module 0 must present it verbatim every run;
  "optional" describes the answer, not whether it is asked.
- **INV-005 pinned wording.** Compare each ⛔ gate question against the pinned text
  character for character (INV-056). Paraphrase is the failure mode.

## The finding class unique to this phase

Phases 1 and 2 find things that are *wrong*. Phase 3 also finds rules that are
**unsatisfiable** — instructions the guide is told it must follow and provably
cannot. The originating run hit one immediately: `ground-rules.md` requires every
acknowledgment to reference "at least one specific thing they said" and forbids a
bare "Got it", but the answer to "any questions before we get started?" is often just
"no", where there is nothing specific to reference and no carve-out exists.

These are worth reporting even at low severity, because an instruction that cannot be
followed trains the model to treat the surrounding instructions as advisory.

## What this walk cannot test — say so rather than implying coverage

The walk is an assistant following the skill files in a normal session, which leaves real
gaps. Name them in the report; a phase-3 run that lists findings without listing these
reads as broader coverage than it had.

- ⛔ **Every fast-forwarded module.** *Walked* is not *tested*. The stretch before the
  chosen module ran with the analysis off, so it produced no evidence about itself — a
  report that lists findings from Data processing without saying the seven modules
  before it were fast-forwarded reads as a full-bootcamp walk. Name the start module and
  name what that leaves uncovered.
- **Administrative write noise.** INV-012 wants config writes unnarrated, and
  `hooks/README.md` records that no harness mechanism suppresses Write/Edit diffs — so the
  plugin minimizes write *frequency* instead (INV-058's single consolidated write). During
  a walk you will likely write config with `Bash`, which renders as tool output rather than
  an inline diff, so **the walk cannot tell you whether the noise INV-058 exists to reduce
  is actually reduced**. What it *can* check is the count: one write per file at Bootcamp
  preparation, not one per gate.
- **The hooks do not fire.** They are installed globally with the plugin, not by running
  these files, so `SessionStart` / `Stop` / `UserPromptSubmit` stay silent in a walk. In
  particular the `Stop` hook's closing-question safety net is untested here — phase 2
  executes every hook entry directly instead.
- **Anything past the SDK.** The walk stops where a real Senzing install is needed, so the
  loads, the live visualization server, and graduation's deliverables are out of reach.
- **The assistant's own compliance is not evidence.** A walk shows that following the files
  *can* produce correct behavior. It cannot show that a different assistant, or the same
  one without a maintainer watching, would land the same way. Findings are trustworthy;
  clean stretches are weaker evidence than they feel.

## Graduation's upstream offer — present it, never send on the in-character yes

⛔ **Graduation Step 0 will offer to forward `mcp-server`-routed findings and send on a yes, and the
yes it gets is given in character — the Bootcamper's, never the maintainer's (INV-314's scope
note). Present the offer anyway; do not send.** Skipping the gate silently is worse: its wording,
its batching and its INV-065 stripping are module behavior under test, and a walk that quietly
omits a step corrupts the thing phase 3 exists to observe.

⚠️ **This fires on every phase-3 walk that reaches graduation with at least one `mcp-server`
finding, which is close to guaranteed** — Step 0 says so itself: retrospective findings skew toward
`mcp-server`, because a tool behaving differently than documented is the defect class a bootcamper
cannot report. It had simply never been hit before 2026-08-27, when no phase-3 walk had reached
graduation.

**Break character to say so, in roughly these words**, rather than improvising it mid-walk:

> This is a dry run, so I can present this gate but I can't send on your answer here: a dry run
> never sends on the Bootcamper's answer, so nothing reaches Senzing's real queue from inside the
> walk. I'm recording your answer and the drafted message; whether it goes is the maintainer's
> decision afterwards.

Then:

- **Record `submission blocked: dry run — a dry run never sends on an in-character yes; the
  maintainer decides after the walk`** in the entry's `Upstream:` field
  (`../../plugins/senzing-bootcamp/skills/bootcamp-onboarding/feedback.md` Step 3). ⛔ **Never
  `offered, declined`** — the maintainer answering in character said *yes*, and writing down a
  refusal is false about the one thing the field exists to record.
- **Draft the exact message into the run's ledger entry** so the send costs one approval later. A
  blocked send with no drafted text is a finding nobody can forward without redoing the work.
- **After the walk**, an `mcp-server` finding may be offered to the maintainer, out of character,
  under the SKILL's outbound rule ("Absolute rules"; "The finding lifecycle", step 5).

## Stopping

Stop wherever the maintainer stops — a partial walk is still evidence, and the
findings do not depend on reaching graduation. Then clean up the project and report,
naming **both ends of the analysis** — the module it started at and how far it got — so
the untested remainder on either side is visible, and so the next run knows which module
to start later than.

⛔ **Before stopping, confirm every finding is drafted in the run's ledger entry.** The stop is
not yours to schedule, so treat each turn as potentially the last: an observation that has
firmed up and is still only in a test-notes block is one message away from being lost. A
partial walk whose findings are written down is a contribution; a partial walk whose findings
are not is a conversation. The pause is where the lifecycle's filing step happens (the SKILL's
"The finding lifecycle", step 3), so a stop is also the moment to put each draft to the
maintainer.
