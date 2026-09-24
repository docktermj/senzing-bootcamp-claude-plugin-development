---
name: unattended-issue-loop
description: 'Work the GitHub issues labeled unattended-ok while the maintainer is away, then audit, then work whatever the audit files — alternating /implement-github-issue and /production-readiness-audit, up to a maximum of five cycles. Encodes what an unattended run may decide for itself and what it must never decide, and leaves a handoff the maintainer can read cold. Maintainer tool for developing the Senzing Bootcamp Claude Plugin (SBCP) — never invoked during a bootcamp.'
---

# Unattended issue loop

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It is never invoked during a bootcamp.

It runs two existing skills in a loop with nobody watching:

```
cycle N:  /implement-github-issue — implement and commit one labeled issue at a time
          /production-readiness-audit  — audit the result; it reports, it does not fix
          nothing new filed?  -> stop, report
          new findings?       -> cycle N+1
stop at 5 cycles regardless
```

## ⛔ It works only issues carrying the `unattended-ok` label

```bash
gh issue list --state open --label unattended-ok
```

⛔ **No label, no work. An unlabeled backlog is a no-op, and that is the correct
outcome** — the loop stops and says so rather than guessing which issues are safe.

⚠️ **Why a label rather than "every open issue".** Running autonomously across the whole
backlog would mean working parity deltas, escalations and customer-derived feedback
without the maintainer choosing any of it — and every one of those needs judgment this
skill explicitly does not have. **The label is how the maintainer says what is safe to run
unattended**, one issue at a time. An issue nobody labeled has not been declined; it has
not been *offered*.

⛔ **Never add the label yourself, and never work an issue without it** — not even one that
looks obviously safe. Selecting the work is the maintainer's decision, and this whole skill
exists because an unattended run converts unasked questions into defaults nobody chose.

The maintainer creates the label once:

```bash
gh label create unattended-ok --description "Safe for /unattended-issue-loop to work unattended"
```

⚠️ **Until it exists, every run of this loop is a no-op.** That is deliberate: the safe
direction for a missing gate is "do nothing", never "assume everything".

⛔ **This skill adds no new authority. It only decides what to do when the two skills it
drives say "ask the maintainer" and there is no maintainer.** Everything else — how to
implement an issue, how to re-verify a Senzing fact, how to audit — stays with
`../implement-github-issue/SKILL.md` and `../production-readiness-audit/SKILL.md`, which are the
authority and must be read, not summarized from here.

## Why this needs writing down

An unattended run is not a normal run with the questions removed. The questions are
where the judgment was, and deleting them silently converts judgment into a default
nobody chose. This repo has the scar: on **2026-08-17** an unattended implement run
produced a reverse-contract defect — hard rules shipped into the plugin with no invariant
registered — and the audit that caught it added the `implement-spec` guardrail (that command retired under #60; the guardrail moved with the obligation) that now
governs this situation. The failure was not carelessness. It was the *safe-looking* move:
"do not record an invariant the maintainer has not agreed to", which quietly shipped the
rule and registered nothing.

So the rule this whole skill turns on:

> ⛔ **Unattended means fewer decisions, not quieter ones.** Every question that would
> have been asked is answered in writing — on the issue, in the ledger, or in the handoff —
> never by silence.

## Before the maintainer leaves

Ask these while they are still here. They are short, and each changes what the run does.

1. ⛔ **Push policy.** Commit locally only, push each cycle, or push once at the end?
   Committing is not publishing; pushing unreviewed unattended work is. Default to
   **local only** if they are already gone.
2. **Any labeled issue needing a judgment call.** Run
   `gh issue list --state open --label unattended-ok`,
   read each one's acceptance criteria, and flag any whose criteria are
   conditional on the maintainer's choice ("if the maintainer chooses…", an unset
   priority, two viable designs). Ask about those specifically — they are the ones an
   unattended run would otherwise decide by accident.
3. **How long "a while" is**, if they offer it. It changes nothing about correctness,
   only how much of the cap is worth attempting.

⚠️ **Do not ask which labeled issues to implement.** The label already answered that;
re-asking wastes the one turn they are still present for.

## The autonomy contract

### Decide these yourself

- **Which labeled issue to take next.** Highest priority first; ties broken by whichever is most
  self-contained. Order is not a maintainer decision.
- **How to implement**, within the issue's acceptance criteria.
- **Skipping an issue that turns out to be unimplementable unattended** — see "blocked"
  below. Skipping is not declining.
- **Reverting your own work** when the suite cannot be brought green.

### Never decide these

- ⛔ **Never sign off an invariant.** `/implement-github-issue` requires the maintainer's approval
  of the wording, and it is permanent and binds every future change. **But declining to
  mint it does not decline to ship the rule** — that is the 2026-08-17 defect exactly. So
  when an implementation ships a hard rule (a ⛔, a bolded MUST/NEVER, anything
  `conformance.py rules` would count), take the sanctioned path in
  `.claude/commands/implement-github-issue.md` (INV-309): ship the rule, and write an **explicit deferral in the ledger
  entry** naming the rule, the site, and why it was not registered. Draft the exact
  `INV-NNN — <statement>` wording in the entry so the maintainer's return costs one yes.
  Never `_None yet._`, never silence.

  ⚠️ Check with `conformance.py since --since-last-audit` and `per-rule --uncited`
  **before** writing the entry, not after. `rules` alone cannot answer this.

  ⛔ **(INV-282) Run the check; never grep `per-rule` for phrases you expect.** A grep can only
  confirm lines you already thought of, and the uncited ones are by construction the ones you
  did not: that is what the check is *for*. This produced a wrong ledger claim **twice** — on
  2026-08-28 an entry stated "all four hard-rule lines cite one of those at the line" when two
  did not, three cycles after an audit had recorded the same spot-check method as unsound.

  ```bash
  python3 .claude/skills/production-readiness-audit/conformance.py reverse-check --since-last-audit
  ```

  ⚠️ **This replaced a script written out here, and the replacement is the point.** The script
  took every line `since` reported and tested membership in `per-rule --uncited` — two views
  that read **different corpora**, so a rule added under `.claude/` could never appear in the
  result. Measured against `7b43eee`: 112 lines in, **0** reported, and 93 of those 112 cite
  nothing. It also dropped its stop sign when building the comparison key, which silently missed
  **44 of 333** mid-line rules inside the corpus it did cover. Both are gone because the view
  asks each line's own file whether an invariant is cited at it, rather than matching one
  report's text against another's. (#80)

  ⛔ **(INV-308) Read the VERDICT line, not the absence of output.** It says `clean` only when every added
  line was tested **and** cited; a run with untested lines is `NOT CLEAN` and says how many, so
  a corpus the check cannot reach can never again read as a clean result.

  Each line it prints is then **either** cited at the line **or** named in a `DEFERRED INVARIANT`
  block — those are the only two legitimate states, and silence is neither.

- ⛔ **Never call `submit_feedback`.** Any `mcp-server`-routed finding gets an issue whose
  `Upstream:` line reads **"not yet sent — needs maintainer approval"**, with the exact
  message drafted in the issue ready to send. Nothing leaves the machine unattended.
- ⛔ **Never decline.** `/implement-github-issue` reserves that for the maintainer alone. A
  issue you cannot implement is **blocked**, not declined, and blocked is a state you
  record — never a file you edit into `DECLINED.md`.
- ⛔ **Never relax an assertion, delete a test, or narrow a guard to reach green.** If a
  test fails, either the change is wrong or the test pinned a wrong premise; both are
  findings. A suite made green by weakening it is the one outcome worse than a red suite,
  because it reads as success.
- ⛔ **Never rewrite history, force-push, or amend a commit from a previous cycle.**
- ⛔ **Never write into `specs/`** — it is a read-only archive (INV-307). Filing a finding over existing work has
  happened here; check whether the file exists before writing, and read it if it does.

## Preflight

Do all of this before the first issue, and record the results — the handoff needs the
baseline to be meaningful.

```bash
git status --short                       # must be clean; stop if not
git rev-parse HEAD                       # the run's start commit — record it
python3 -m unittest discover -s tests    # must be green; stop if not
python3 .claude/skills/compact-dev-environment/citations.py verify
gh issue list --state open --label unattended-ok   # the backlog; empty means stop
```

⛔ **A red or dirty baseline stops the run before it starts.** You cannot attribute a
failure you inherited, and an unattended run that "fixes" a pre-existing problem it did
not diagnose is how unrelated changes get buried in a batch nobody reviewed.

## Per issue

1. **Invoke `/implement-github-issue <issue>`** and follow it. It is the authority — including
   Step 3.3's re-verification of every Senzing fact against the live MCP server, which an
   unattended run does **not** get to skip for speed. A fact laundered out of an issue is
   the defect class that skill exists to prevent.
2. **Negative-control every new test.** Reintroduce the defect, confirm the test fails,
   revert. ⛔ Then `find . -name __pycache__ -type d -exec rm -rf {} +` — a same-size
   revert with a same-second mtime lets Python reuse bytecode compiled from the mutated
   source, and the suite then fails on already-correct code. This bites hardest in a loop,
   where nobody is watching to notice the failure is stale.
3. **Full suite green**, then `citations.py verify` clean.
4. **Commit** — one issue, one commit, conventional-commit subject, body saying what the
   defect was and what the fix does. End with the `Co-Authored-By` trailer.
5. **Record the hash** in the ledger entry's `Commit:` field and commit that as
   `chore(state): record the <issue> commit hash`, matching the repo's existing pattern.

### When an issue is blocked

An issue is blocked when its acceptance criteria are ambiguous, when it needs a decision
reserved above, or when the MCP server is unreachable and the issue rests on a Senzing
fact. Then:

- **Leave the working tree clean** — revert any partial work for that issue.
- ⛔ **Comment on the issue** saying what stopped it and the exact question that would
  unblock it, then **remove the `unattended-ok` label** so the next run does not retry it
  blindly. ⚠️ This step used to write a dated blocked-section into the spec file — the
  instruction is deliberately not reproduced here, since a line quoting it is itself an
  instruction to write into the archive, and INV-307 forbids that outright. The issue is where
  the next reader looks; a note only in the handoff dies with the conversation.
- **Move to the next labeled issue.** One blocked issue does not stop the loop.

## Per cycle

After the open set is empty or every remainder is blocked, invoke
`/production-readiness-audit` and follow it.

⛔ **(INV-314) An unattended audit FILES NOTHING.** Fixed in #69: the audit records each finding in
its dated `specs/IMPLEMENTED.md` entry and lists it in the handoff marked **not filed**,
rather than calling `gh issue create`.

⚠️ **This is the same rule as the attended gate, not a second one (#106).** Three skills
require a yes before filing; unattended there is nobody to ask, so the answer is *do not file*.
Both reduce to one statement — **an issue is created only on an explicit yes** — and the
drafted invariant in `specs/IMPLEMENTED.md` covers both halves rather than leaving this one to
be read as an exception. ⛔ **Do not restate the attended gate here**: a fourth copy of a rule
that already disagrees with itself in three places is what the deferral exists to stop. ⚠️ **That is this contract, not an exception to
it** — filing leaves the machine, and nothing leaves the machine unattended. The
maintainer files what survives their read. ⛔ **Never file the audit's findings yourself
at the end of a run**, and never label anything `unattended-ok`.

⚠️ **The audit reports; it does not fix in place.** That is its own rule
("present findings and let the maintainer choose what to fix"), and here it is also what
makes the loop work — the next `/implement-github-issue` pass is the fixing half. Do not collapse
the two.

⛔ **Read the newest `## production-readiness-audit-*` ledger entries before auditing**
(`grep -n '^## \(production-readiness-audit\|deep-dive-audit\)' specs/IMPLEMENTED.md | tail -8`).
The skill says the newest entry matters most after an unattended run, and this is that
case: it is where a previous unattended run's characteristic defect was written down.

Record the audit itself as a dated `## production-readiness-audit-<date>` ledger entry
marked **Not a spec**, whatever it found — including "found nothing", which is the result
that ends the loop and therefore the one most worth being able to verify later.

⛔ **The audit record is committed on its own, before the next cycle's implementations.** Its
hash becomes the next cycle's `--since-last-audit` range start, so a record sharing a commit
with implementation work makes that range begin at the work and report `0 hard-rule lines
added` — and this guard's consumer, `tests/test_new_hard_rules_are_cited_or_deferred`, **skips**
on "nothing added", so it goes green by not running. Nobody is watching for that in a loop.
The resolver now warns (`⛔ SUSPECT-REF`) and widens to the parent; read the line rather than
relying on it. (Source: `since-last-audit-reports-zero-when-the-audit-record-shares-the-work-commit`, 2026-09-03.)

### Stopping

Stop and write the handoff when any of these is true:

- an audit **records no new findings** — the success condition;
- **five cycles** have run;
- the suite cannot be brought green and reverting to the last green commit is the only
  way forward — stop there, do not keep going on a broken base;
- every remaining labeled issue is blocked;
- the MCP server is unreachable and every remaining labeled issue asserts a Senzing fact.

## The handoff

The maintainer reads this cold, possibly days later, and the conversation will not be
there. ⛔ **State lives in git, the issue tracker and `IMPLEMENTED.md` — never in the conversation.**
A long unattended run *will* be compacted; anything held only in context is already gone.

The closing message says, in this order:

1. **What is committed** — issue numbers against commit hashes, and the start commit so the
   whole run is one `git log <start>..HEAD`.
2. **What needs a yes** — every deferred invariant with its drafted wording, and every
   drafted upstream message awaiting approval. This is the maintainer's actual worklist
   and it goes near the top.
3. **What is blocked**, and the question that unblocks each.
4. **The audit verdict per cycle** — the four properties separately, not a single
   pass/fail. ⛔ **(INV-308) For the reverse check, quote its COUNTS, never the verdict word
   alone.** `NOT CLEAN` is the ordinary result for maintainer-surface work — the span outside
   `per-rule`'s corpus is untested by construction, whatever its state — so a handoff carrying
   only that word tells the maintainer nothing they can act on, and a reader who sees it every
   time stops reading it. Give the tested count, the uncited count, the untested count and its
   citation rate, and carry the view's own caveat that a cited invariant is not a governing
   one (#83).
5. **Suite and tree state** — final counts, and whether the tree is clean and unpushed.
6. ⛔ **What you got wrong.** Reverted work, a probe that misread, an issue re-derived that
   was already recorded. An unattended run is trusted on its self-report or not at all.

## Scope note

`.claude/` is not propagated to the public repo (`propagate.sh` mirrors `plugins/`,
`.claude-plugin/`, `docs/` and `README.md` only), so this skill never ships to bootcampers.
