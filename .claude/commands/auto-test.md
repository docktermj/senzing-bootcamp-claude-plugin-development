---
description: Run the sandboxed automated test — MCP-server drift probe, optionally a simulated bootcamp walk (maintainer tool).
argument-hint: "[walk] [persona: terse|verbose|confused|impatient|offscript] [turns]"
---

Maintainer request: run the automated, sandboxed test of the Senzing Bootcamp plugin.

Invoke the `auto-test` skill and follow it end to end.

Runs to include: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, present the two halves and ask which to run. They cost
  very different things and answer different questions, so the choice is the
  maintainer's:
  1. **MCP probe** — zero tokens, seconds. Drift, conformance, server quality, and
     the static-contract audit against `tests/test_mcp_call_contracts.py`.
  2. **+ simulated walk** — spends tokens. Two OS processes run the bootcamp and
     answer as the Bootcamper, then `transcript_lint.py` grades the saved transcript.
- If `$ARGUMENTS` **names a walk**, take that as the answer and run both. A trailing
  persona and turn count answer the walk's own parameters; otherwise the defaults
  (`terse`, 12) stand.
- **The probe runs either way, and it runs first.** It is the half that justifies a
  schedule — the plugin only changes when the maintainer changes it, and the repo's
  own suite already covers that, while the server moves on its own — and a walk
  against a server that has drifted underneath it produces findings no one can
  attribute.

⛔ **The walk is never inferred from silence.** It is asked about, not assumed.

**Rotate `--persona` across runs.** A single cooperative persona is the main reason an
automated walk is weaker than a human one, and rotation is the cheapest partial
mitigation there is. If the maintainer names no persona on a walk they have run
recently, say which one the last run used.

Let the skill's own flags do the enforcing. `submit_feedback` and `download_resource`
are blocked by `NEVER_CALL` in the probe and `--disallowedTools` in the walk —
enforced by flag, not by instruction, precisely because an unattended run cannot be
trusted to remember a rule. Do not hand-run the pieces around `autotest.py`, and do
not tell the process running the bootcamp that it is under test; that destroys the
only thing the walk measures.

⛔ **Never report a clean run as a passed audit.** The asymmetry is structural — a
simulated Bootcamper never gets confused and never asks "wait, why?" — so:

> **Findings are trustworthy. A clean run is weak evidence.**

Report it as "no regression detected", never as "the bootcamp works". Phase 3 of
`/dry-run`, with a human answering, still has to happen.

Finish by reporting the findings in severity order — BREAKING, WATCH, INFO — naming
the sandbox the run used and whether the walk was included. For a **plugin-side**
finding, follow `dry-run`'s rules unchanged: fix the class not the instance, write a
repo-level test, negative-control it, record it in `specs/IMPLEMENTED.md`, and
register or explicitly disclaim the invariant in `specs/INVARIANTS.md`. For a
**server-side** finding (`doc-incomplete`, `silent-accept`, `doc-wrong`) the fix is
not in this repo: note it, work around it in the plugin if it can mislead a
bootcamper, and ⛔ do not report it upstream via `submit_feedback` from an automated
run.

If a server change is deliberately accepted, refresh the baseline with
`mcp_probe.py update` and say that `baseline/mcp-snapshot.json` needs committing —
without it the offline conformance suite silently covers nothing.
