# Spec template — delegation specs

Copy this structure into each generated `specs/<kebab-case-title>.md`. It is the
`feedback-to-issues` template adapted to this skill's subject: the problem is never
"a Bootcamper hit something", it is "the plugin owns a fact it no longer needs to".
Keep it terse and developer-facing, matching the existing specs. Delete guidance in
angle brackets.

```markdown
# <Title — name the fact, not the file>

Maintain the invariant conditions in @INVARIANTS.md and implement the following improvement:

## Problem

<What the SBCP holds today, quoted, with file:line. Then what the live server returns
for the same question, quoted, with the tool, parameters, server version and date.
State which of the six verdicts this is and why.

For `contradicted`, lead with the fact that the plugin is shipping a wrong Senzing fact
today, and say what a Bootcamper following it would get. Apply INV-169 first: if the
plugin's claim holds under a flag set, binding, SDK version or platform the server's
generic answer does not cover, this is not a contradiction and the spec should not exist.

For `retire-workaround`, describe the original defect, and state how the fix was proved
rather than inferred — which failing conditions were reproduced, and what happened.>

## Root cause

<Why the plugin holds it. Usually: the server did not serve this when the text was
written, so the plugin filled the gap correctly, and nothing since has re-checked.
Name the spec, invariant or audit that put it there when you can find it — this is
also the record of whether the gap-filling was ever right.>

## Proposed change

<The call that replaces the text: tool, exact parameters, and **what to extract from
the response**. A spec that says "ask the MCP server" without these is a regression,
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
- MCP evidence: <tool(parameters)> on server <version>, <date> — <what it returned, quoted>
- Priority: <High for contradicted | Medium | Low>
- Upstream: <not applicable | feature request sent <date> via `submit_feedback` (anonymous) | declined by the maintainer>
- Related specs: <specs/<file>.md, or "none">
```

Two notes on filling this in.

**The evidence is the spec.** A delegation spec whose reader cannot tell the server's
words from the author's is unimplementable — `implement-spec` re-verifies every Senzing
fact before touching code (its Step 3.3), and it needs to know exactly what answer to
expect. Quote; never paraphrase.

**One spec per coherent change.** Group sites that share a fix — five files repeating
one attribute rule are one spec. Keep unrelated sites apart, even when the same run
found them, because they will be implemented and reverted independently.
