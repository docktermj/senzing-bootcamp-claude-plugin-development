# Issue template — delegation issues

Write this structure into a file and pass it to `gh issue create --body-file`. It is the
`feedback-to-issues` template adapted to this skill's subject: the problem is never
"a Bootcamper hit something", it is "the plugin owns a fact it no longer needs to".
Keep it terse and developer-facing, matching the issues already in the tracker. Delete
guidance in angle brackets.

⛔ **The title is not part of the body.** GitHub takes it from `--title`, so the body starts
at `## Problem` — a leading `# <Title>` renders as a duplicate heading inside the issue.

⛔ **Write the title as the fact, not the file** — *"Module 6 hardcodes the redo-drain
termination condition the server now documents"*, never *"module 6 is stale"*. It is what a
reader scans in a list of thirty.

```markdown
## Problem

<What the SBCP holds today, quoted, with file:line. Then what the live server returns
for the same question, quoted, with the tool, parameters, server version and date.
State which of the six verdicts this is and why.

For `contradicted`, lead with the fact that the plugin is shipping a wrong Senzing fact
today, and say what a Bootcamper following it would get. Apply INV-169 first: if the
plugin's claim holds under a flag set, binding, SDK version or platform the server's
generic answer does not cover, this is not a contradiction and the issue should not exist.

For `retire-workaround`, describe the original defect, and state how the fix was proved
rather than inferred — which failing conditions were reproduced, and what happened.>

## Root cause

<Why the plugin holds it. Usually: the server did not serve this when the text was
written, so the plugin filled the gap correctly, and nothing since has re-checked.
Name the spec, invariant or audit that put it there when you can find it — this is
also the record of whether the gap-filling was ever right.>

## Proposed change

<The call that replaces the text: tool, exact parameters, and **what to extract from
the response**. An issue that says "ask the MCP server" without these is a regression,
not a cleanup.

Say what STAYS. Delegation rarely removes a whole section — the step still needs its
orientation sentence and its instruction for what to do with the answer. Be explicit,
or this will be implemented as "delete lines 40-60".

State the fallback when the call fails (INV-125): the step now depends on it.

Where full delegation failed Step 6 but the text is a cached authority, propose the
intermediate form instead — a dated, explicitly partial illustration that tells the
reader to re-ask, in the shape
`module-05-data-quality-mapping/phase1-quality-assessment.md` already uses.>

## Acceptance criteria

- [ ] <The plugin no longer asserts <fact> as its own; the step calls <tool(params)> and uses <field>.>
- [ ] <Re-verification clause: implementing this requires <tool(params)> to still return <answer>. If it does not, the change is wrong — re-triage instead of implementing.>
- [ ] <Named test that pins the removed text, and what it should assert instead.>
- [ ] <For retire-workaround: INV-### carries a dated superseding note; it is NOT deleted or renumbered.>
- [ ] Holds on Linux, macOS, and Windows and stays language-agnostic (per @INVARIANTS.md).

## Affected files

- `path/to/file` — <what changes and why>
- `tests/test_*.py` — <the assertion that must change with it>

## Source

- Sweep: `delegate-to-mcp-server`, <date>, ledger key `<stable-slug>`
- Verdict: <delegate | contradicted | retire-workaround>
- MCP evidence: <tool(parameters)> on server <version>, docs index <index_built>, <date> — <what it returned, quoted>
- Priority: <High for contradicted | Medium | Low>
- Upstream: <not applicable | feature request sent <date> via `submit_feedback` (anonymous) | declined by the maintainer>
- Related issues: <#<n>, or "none"> <a closed one counts: it records a decision this may be reopening>
- Invariants: <the INV-NNN conditions this must maintain>
```

Three notes on filling this in.

**The evidence is the issue.** A delegation issue whose reader cannot tell the server's
words from the author's is unimplementable — `/implement-github-issue` re-verifies every
Senzing fact before touching code, and it needs to know exactly what answer to expect.
Quote; never paraphrase.

**One issue per coherent change.** Group sites that share a fix — five files repeating
one attribute rule are one issue. Keep unrelated sites apart, even when the same run
found them, because they will be implemented and reverted independently.

## ⛔ Asserting the server LACKS something requires `owner-checked:`

Any issue whose diagnosis rests on the server not having a fact — "returns no X", "does not
cover", "no MCP tool answers this" — MUST name, on the `MCP evidence` line, the route that
would **carry** that fact and what it returned:

```text
owner-checked: sdk_guide(topic='load', language=…, record_count=<above the limit>) — returns it
```

**The tools you asked and found empty are not evidence for the negative.** They are true
statements about those tools. "`sdk_guide(topic='configure')` returns no license variable" is
correct and worthless as support for "no license variable exists" — the variable lives in
`sdk_guide(topic='load', record_count=<above the limit>)`. This is **INV-194** applied to the
issue format, and it is required because an issue is the *input* to implementation: an absence
concluded from the wrong route has already, once, become an invariant plus a guard enforcing
it, with the offline suite certifying both (see
`specs/no-license-path-environment-variable.md`, in the frozen archive).

⚠️ **This binds harder here than in `feedback-to-issues`.** That skill files what a Bootcamper
hit, where an absence claim is one line of a diagnosis. **This skill's entire subject is what
the server does and does not cover** — a `keep-server-lacks-it` verdict *is* an absence claim,
and the ones that go upstream in Step 8 are absence claims sent to Senzing. An absence
concluded from the wrong route here becomes an instruction deleted from the plugin and from
four child ports.

⚠️ **INV-213's wording says "a spec"**, because it was written when this skill and
`feedback-to-issues` both produced spec files. The obligation is unchanged by the format —
an absence claim is the input to implementation either way — so it is carried here
deliberately rather than allowed to lapse with the format change (#114).

Exempt: a line declaring `n/a (no Senzing fact)`. With no Senzing fact there is no absence
claim about the server to substantiate.

⛔ **Care is not the remedy.** `tests/test_spec_absence_claims_name_their_owner.py` enforces
the clause so attention is not what stands between a wrong route and a shipped invariant.
