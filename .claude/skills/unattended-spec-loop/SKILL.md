---
name: unattended-spec-loop
description: 'Work the specs/ backlog to empty while the maintainer is away, then audit, then work whatever the audit files — alternating /implement-github-issue and /production-readiness-audit until an audit produces no new specs, up to a maximum of five cycles. Encodes what an unattended run may decide for itself and what it must never decide, and leaves a handoff the maintainer can read cold. Maintainer tool for developing the Senzing Bootcamp Claude Plugin (SBCP) — never invoked during a bootcamp.'
---

# Unattended spec loop

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It is never invoked during a bootcamp.

It runs two existing skills in a loop with nobody watching:

```
cycle N:  /implement-github-issue — implement and commit one issue at a time
          /production-readiness-audit  — audit the result; it files specs, it does not fix
          no new specs?  -> stop, report
          new specs?     -> cycle N+1
stop at 5 cycles regardless
```

⛔ **This skill adds no new authority. It only decides what to do when the two skills it
drives say "ask the maintainer" and there is no maintainer.** Everything else — how to
implement a spec, how to re-verify a Senzing fact, how to audit — stays with
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
> have been asked is answered in writing — in a spec, in the ledger, or in the handoff —
> never by silence.

## Before the maintainer leaves

Ask these while they are still here. They are short, and each changes what the run does.

1. ⛔ **Push policy.** Commit locally only, push each cycle, or push once at the end?
   Committing is not publishing; pushing unreviewed unattended work is. Default to
   **local only** if they are already gone.
2. **Any spec needing a judgment call.** Run `python3 ../implement-spec/list_specs.py` (the script is kept: INV-216's first clause still binds it, though `specs/` is frozen and it now reports `open: 0`),
   read each open spec's `## Acceptance criteria`, and flag any whose criteria are
   conditional on the maintainer's choice ("if the maintainer chooses…", an unset
   priority, two viable designs). Ask about those specifically — they are the ones an
   unattended run would otherwise decide by accident.
3. **How long "a while" is**, if they offer it. It changes nothing about correctness,
   only how much of the cap is worth attempting.

⚠️ **Do not ask which specs to implement.** "As many as you can" is the whole instruction;
re-asking wastes the one turn they are still present for.

## The autonomy contract

### Decide these yourself

- **Which spec to take next.** Highest priority first; ties broken by whichever is most
  self-contained. Order is not a maintainer decision.
- **How to implement**, within the spec's acceptance criteria.
- **Skipping a spec that turns out to be unimplementable unattended** — see "blocked"
  below. Skipping is not declining.
- **Reverting your own work** when the suite cannot be brought green.

### Never decide these

- ⛔ **Never sign off an invariant.** `/implement-github-issue` requires the maintainer's approval
  of the wording, and it is permanent and binds every future spec. **But declining to
  mint it does not decline to ship the rule** — that is the 2026-08-17 defect exactly. So
  when an implementation ships a hard rule (a ⛔, a bolded MUST/NEVER, anything
  `conformance.py rules` would count), take the sanctioned path in
  `.claude/commands/implement-github-issue.md` (INV-309): ship the rule, and write an **explicit deferral in the ledger
  entry** naming the rule, the site, and why it was not registered. Draft the exact
  `INV-NNN — <statement>` wording in the entry so the maintainer's return costs one yes.
  Never `_None yet._`, never silence.

  ⚠️ Check with `conformance.py since --since-last-audit` and `per-rule --uncited`
  **before** writing the entry, not after. `rules` alone cannot answer this.

  ⛔ **(INV-282) The check is a SET DIFFERENCE between the two outputs — never a grep of `per-rule` for
  phrases you expect.** A grep can only confirm lines you already thought of, and the uncited
  ones are by construction the ones you did not: that is what the check is *for*. This has now
  produced a wrong ledger claim **twice** — on 2026-08-28 an entry stated "all four hard-rule
  lines cite one of those at the line" when two did not, three cycles after an audit had
  recorded the same spot-check method as unsound. Take every `+` line `since` reports, normalize
  it, and test membership against `per-rule --uncited`:

  ```bash
  python3 - <<'EOF'
  import subprocess, re
  R = ".claude/skills/production-readiness-audit/conformance.py"
  run = lambda *a: subprocess.run(["python3", R, *a], capture_output=True, text=True).stdout
  added = [l[7:].strip() for l in run("since", "--since-last-audit").splitlines()
           if l.startswith("     +")]
  unc = re.sub(r"\s+", " ", run("per-rule", "--uncited"))
  key = lambda s: re.sub(r"\s+", " ", re.sub(r"^[-\d.\s]*", "", s).replace("⛔", "").strip())[:60]
  for a in added:
      if key(a) and key(a) in unc:
          print("UNCITED:", a[:100])
  EOF
  ```

  Each line it prints is then **either** cited at the line **or** named in a `DEFERRED INVARIANT`
  block — those are the only two legitimate states, and silence is neither.

- ⛔ **Never call `submit_feedback`.** Any `mcp-server`-routed finding gets a spec whose
  `Upstream:` line reads **"not yet sent — needs maintainer approval"**, with the exact
  message drafted in the spec ready to send. Nothing leaves the machine unattended.
- ⛔ **Never decline.** `/implement-github-issue` reserves that for the maintainer alone. A
  spec you cannot implement is **blocked**, not declined, and blocked is a state you
  record — never a file you edit into `DECLINED.md`.
- ⛔ **Never relax an assertion, delete a test, or narrow a guard to reach green.** If a
  test fails, either the change is wrong or the test pinned a wrong premise; both are
  findings. A suite made green by weakening it is the one outcome worse than a red suite,
  because it reads as success.
- ⛔ **Never rewrite history, force-push, or amend a commit from a previous cycle.**
- ⛔ **Never delete or overwrite a spec file.** Filing a finding over an existing spec has
  happened here; check whether the file exists before writing, and read it if it does.

## Preflight

Do all of this before the first spec, and record the results — the handoff needs the
baseline to be meaningful.

```bash
git status --short                       # must be clean; stop if not
git rev-parse HEAD                       # the run's start commit — record it
python3 -m unittest discover -s tests    # must be green; stop if not
python3 .claude/skills/compact-dev-environment/citations.py verify
python3 .claude/skills/implement-spec/list_specs.py
```

⛔ **A red or dirty baseline stops the run before it starts.** You cannot attribute a
failure you inherited, and an unattended run that "fixes" a pre-existing problem it did
not diagnose is how unrelated changes get buried in a batch nobody reviewed.

## Per spec

1. **Invoke `/implement-github-issue <issue>`** and follow it. It is the authority — including
   Step 3.3's re-verification of every Senzing fact against the live MCP server, which an
   unattended run does **not** get to skip for speed. A fact laundered out of a spec is
   the defect class that skill exists to prevent.
2. **Negative-control every new test.** Reintroduce the defect, confirm the test fails,
   revert. ⛔ Then `find . -name __pycache__ -type d -exec rm -rf {} +` — a same-size
   revert with a same-second mtime lets Python reuse bytecode compiled from the mutated
   source, and the suite then fails on already-correct code. This bites hardest in a loop,
   where nobody is watching to notice the failure is stale.
3. **Full suite green**, then `citations.py verify` clean.
4. **Commit** — one spec, one commit, conventional-commit subject, body saying what the
   defect was and what the fix does. End with the `Co-Authored-By` trailer.
5. **Record the hash** in the ledger entry's `Commit:` field and commit that as
   `chore(specs): record the <spec> commit hash`, matching the repo's existing pattern.

### When a spec is blocked

A spec is blocked when its acceptance criteria are ambiguous, when it needs a decision
reserved above, or when the MCP server is unreachable and the spec rests on a Senzing
fact. Then:

- **Leave the working tree clean** — revert any partial work for that spec.
- **Append a `## Blocked (unattended run YYYY-MM-DD)` section to the spec file** saying
  what stopped it and the exact question that would unblock it. The spec file is where
  the next reader looks; a note only in the handoff dies with the conversation.
- **Move to the next spec.** One blocked spec does not stop the loop.

## Per cycle

After the open set is empty or every remainder is blocked, invoke
`/production-readiness-audit` and follow it.

⚠️ **The audit reports and files specs; it does not fix in place.** That is its own rule
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

- an audit produces **no new specs** — the success condition;
- **five cycles** have run;
- the suite cannot be brought green and reverting to the last green commit is the only
  way forward — stop there, do not keep going on a broken base;
- every remaining spec is blocked;
- the MCP server is unreachable and every remaining spec asserts a Senzing fact.

## The handoff

The maintainer reads this cold, possibly days later, and the conversation will not be
there. ⛔ **State lives in git, `specs/` and `IMPLEMENTED.md` — never in the conversation.**
A long unattended run *will* be compacted; anything held only in context is already gone.

The closing message says, in this order:

1. **What is committed** — spec names against commit hashes, and the start commit so the
   whole run is one `git log <start>..HEAD`.
2. **What needs a yes** — every deferred invariant with its drafted wording, and every
   drafted upstream message awaiting approval. This is the maintainer's actual worklist
   and it goes near the top.
3. **What is blocked**, and the question that unblocks each.
4. **The audit verdict per cycle** — the four properties separately, not a single
   pass/fail.
5. **Suite and tree state** — final counts, and whether the tree is clean and unpushed.
6. ⛔ **What you got wrong.** Reverted work, a probe that misread, a spec re-derived that
   was already recorded. An unattended run is trusted on its self-report or not at all.

## Scope note

`.claude/` is not propagated to the public repo (`propagate.sh` mirrors `plugins/`,
`.claude-plugin/`, `docs/` and `README.md` only), so this skill never ships to bootcampers.
