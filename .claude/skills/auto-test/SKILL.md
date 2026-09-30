---
name: auto-test
description: 'Run an automated, sandboxed test of the Senzing Bootcamp plugin. Probes the live Senzing MCP server for drift and for inaccurate or misleading information, checks every MCP call the plugin makes against what the server actually accepts, and optionally walks the bootcamp with a simulated Bootcamper and lints the transcript against the interaction invariants. Each run gets its own sandbox, so it is safe to run many times a day and concurrently. Use when the maintainer wants to auto-test, smoke-test on a schedule, watch for MCP server drift, or check the plugin without sitting through a dry run. Maintainer tool — not part of the bootcamper experience.'
argument-hint: "[walk] [persona: terse|verbose|confused|impatient|offscript] [turns]"
---

# Auto Test

A **maintainer** tool for developing the Senzing Bootcamp Claude Plugin (SBCP).
Never invoked during a bootcamp. It is the unattended counterpart to
[`dry-run`](../dry-run/SKILL.md): dry-run is a careful session with a human,
auto-test is a cheap one you can run three times a day.

## What it is for, and what it cannot do

Two questions, and they deserve different amounts of trust.

**"Has the MCP server changed under us?"** — answered completely and for free. The
server is the plugin's hard dependency (INV-080 routes every Senzing fact through
it) and it changes with no notice. `mcp_probe.py` talks JSON-RPC straight to
`https://mcp.senzing.com/mcp` with **no Claude process and no tokens**, so this half
runs in seconds. This is the part that actually justifies a schedule.

**"Does the bootcamp still behave?"** — answered partially, and the limit is
structural. `phase3-conversational.md` forbids self-play for two reasons; the walk
here answers one and a half:

1. *ground-rules.md forbids fabricating the Bootcamper's response* — **answered.**
   Two OS processes: A runs the bootcamp, B answers as the Bootcamper. A fabricates
   nothing.
2. *an assistant that knows it is graded will comply* — **answered only by
   discipline.** A is never told it is under test, and grading happens afterwards on
   the saved transcript. Put an invariant in A's prompt and you are measuring the
   model's carefulness instead of the plugin's files.

⛔ **What stays unanswered:** a simulated Bootcamper is more cooperative than a real
one — it answers in format, never gets confused, never asks "wait, why?". So this
inherits phase 3's asymmetry rather than fixing it:

> **Findings are trustworthy. A clean run is weak evidence.**

Report a clean auto-test as "no regression detected", never as "the bootcamp works".
Phase 3 with a human still has to happen.

## Running it

```console
.claude/skills/auto-test/autotest.py                  # MCP only — seconds, free
.claude/skills/auto-test/autotest.py --walk           # + a simulated walk
.claude/skills/auto-test/autotest.py --walk --persona confused --turns 16
.claude/skills/auto-test/autotest.py --walk --keep    # keep the sandbox to inspect
```

**The argument chooses the runs** (`[walk] [persona] [turns]`):

- **No argument: present the two halves and ask which to run.** They cost very different
  things and answer different questions, so the choice is the maintainer's:
  1. **MCP probe** — zero tokens, seconds. Drift, conformance, server quality, and the
     static-contract audit against `tests/test_mcp_call_contracts.py`.
  2. **+ simulated walk** — spends tokens. Two OS processes run the bootcamp and answer as
     the Bootcamper, then `transcript_lint.py` grades the saved transcript.
- **An argument naming a walk** is the answer: run both. A trailing persona and turn count
  answer the walk's own parameters (`--persona`, `--turns`); otherwise the defaults
  (`terse`, 12) stand.
- **The probe runs either way, and it runs first.** A walk against a server that has
  drifted underneath it produces findings no one can attribute.

⛔ **The walk is never inferred from silence.** (INV-333) It is asked about, not assumed.

Exit code is 1 if anything BREAKING was found, 0 otherwise, so it drops into cron or
CI unchanged. `--json` prints the machine-readable report; every run also writes
`report.json` into its sandbox.

To refresh the baseline after deliberately accepting a server change:

```console
.claude/skills/auto-test/mcp_probe.py update
```

Commit the resulting `baseline/mcp-snapshot.json` — the offline suite reads it.

## The sandbox, and why each layer is there

Each run builds `~/senzing-autotest/runs/<timestamp>-<persona>/`.

| Layer | Why |
|---|---|
| Project dir under `$HOME` | `write-gate.py` blocks `/tmp`, `/var/tmp`, `/private/tmp` — a sandbox there tests the gate, not the bootcamp |
| **git worktree pinned to a SHA** | you will edit the repo while runs execute; an unpinned run tests half-saved files and its findings are unattributable |
| Per-run `mcp.json` + `--strict-mcp-config` | the run sees Senzing and nothing else — none of your authenticated claude.ai connectors |
| Distinct `--session-id` | concurrent runs never share history |
| `--isolate-config` (opt-in) | own `CLAUDE_CONFIG_DIR`; isolates state but **not credentials**, so it needs `ANTHROPIC_API_KEY` |

The sandbox is removed at the end unless `--keep`.

## The pieces

| File | Does | Costs |
|---|---|---|
| [`mcp_probe.py`](mcp_probe.py) | drift, conformance, server-quality, static-contract audit | zero tokens |
| [`transcript_lint.py`](transcript_lint.py) | interaction invariants over a recorded walk | zero tokens |
| [`walk.py`](walk.py) | drives the two-process bootcamp walk | tokens |
| [`autotest.py`](autotest.py) | sandbox + orchestration + report | — |
| `baseline/mcp-snapshot.json` | the committed contract the offline suite checks against | — |

## What made this hard, and what you must preserve

**The server declares no JSON-Schema enums.** All 13 tools have zero `enum` keys.
Every closed value set — `mapping_workflow`'s actions, `search_docs`'s categories,
the languages `generate_scaffold` takes — lives only in description prose. A checker
that reads `inputSchema.enum` finds nothing and reports clean forever.

**So the accepted set is discovered by probing, not by reading.** Sending
`sdk_guide(topic='zzz_probe_invalid')` comes back *"Valid topics: install, configure,
load, …"*. `PROBE_MATRIX` does that once per parameter. Every entry must stay
side-effect free — `mapping_workflow` qualifies only because an unknown action fails
deserialization before the handler runs.

⛔ **Never infer a rejection. Send the value.** This rule cost three false positives
while the tool was being built, each one a confident BREAKING finding against
correct plugin text:

- `get_sample_data(dataset='list')` is absent from every list the server publishes
  and works perfectly — an undocumented discovery sentinel.
- `sdk_guide(language='c#')` is absent from the rejection message and works — the
  rejection list is a *display* list, not the acceptance set.
- `generate_scaffold(language='typescript')` works despite a description naming only
  four languages.

`verify_literal()` settles a suspicion with an actual call; `record_verified_extras()`
persists the verdict into the baseline so the offline suite inherits it.

⛔ **`submit_feedback` and `download_resource` are blocked by flag, not by
instruction.** `NEVER_CALL` in the probe, `--disallowedTools` in the walk. An
unattended run cannot be trusted to remember a rule.

## Reading the output

Severities mean specific things:

- **BREAKING** — a documented path is broken now. A tool vanished, a parameter
  became required, a value the plugin uses is rejected, or the static contract in
  `tests/test_mcp_call_contracts.py` no longer holds.
- **WATCH** — the server changed in a way that needs a human to re-read it, or it
  carries misleading information (`doc-incomplete`, `silent-accept`).
- **INFO** — context, not action.

Report the findings in that order — BREAKING, WATCH, INFO — naming the sandbox the run used
and whether the walk was included.

Two WATCH findings were live as of 2026-07-27 and are about the **server**, not the
plugin: `generate_scaffold.language` accepts `typescript` while documenting four
languages, and `search_docs.category` accepts any string without error, so a typo
returns plausible but wrongly-scoped results.

## Scheduling

The MCP half is the part worth running often — your plugin only changes when you
change it, and 515 tests already cover that, while the server moves on its own.

```console
0 */4 * * *  cd /path/to/repo && .claude/skills/auto-test/autotest.py --json >> ~/autotest.log 2>&1
0 3 * * *    cd /path/to/repo && .claude/skills/auto-test/autotest.py --walk --persona confused --turns 20
```

Rotate `--persona` across runs (`terse`, `verbose`, `confused`, `impatient`,
`offscript`). A single cooperative persona is the main reason an automated walk is
weaker than a human one, and rotation is the cheapest partial mitigation. If the maintainer
names no persona on a walk they have run recently, say which one the last run used.

## What to do with a finding

Follow [`dry-run`](../dry-run/SKILL.md)'s rules — they apply unchanged: fix the class
not the instance, write a repo-level test, ⛔ **negative-control it**, record it in
`specs/IMPLEMENTED.md`, and register or explicitly disclaim the invariant in
`specs/INVARIANTS.md`.

For a **server-side** finding (`doc-incomplete`, `silent-accept`, `doc-wrong`) the
fix is not in this repo. Note it, work around it in the plugin if it can mislead a
bootcamper, and consider reporting it upstream — but ⛔ **not** via `submit_feedback`
from an automated run.

## Guardrails

- **Never send anything outside the machine.** No `submit_feedback`, no
  `download_resource`. Enforced by flag in both the probe and the walk. Let the flags do
  the enforcing: do not hand-run the pieces around `autotest.py`.
- **Never tell process A it is under test.** It destroys the only thing the walk
  measures.
- **Never report a clean run as a passed audit.** State the coverage limits; the
  report carries them for you.
- **Never put the sandbox under `/tmp`.**
- **Keep `baseline/mcp-snapshot.json` committed.** Without it the offline
  conformance test silently covers nothing — `tests/test_auto_test_harness.py`
  asserts it is present for exactly that reason.

## Scope note

`.claude/` is **not** propagated to the public repo (`propagate.sh` mirrors
`plugins/`, `.claude-plugin/`, `docs/` and `README.md` only), so this skill never
ships to bootcampers.
