# Issue template

Write this structure into a file and pass it to `gh issue create --body-file`. Keep it
terse and developer-facing, matching the issues already in the tracker. Delete guidance in
angle brackets.

⛔ **The title is not part of the body.** GitHub takes it from `--title`, so the body starts
at `## Problem` — a leading `# <Title>` renders as a duplicate heading inside the issue.

```markdown
## Problem

<What the bootcamper experienced. Include the verbatim error/output when the
feedback provided one — it is the clearest repro signal.>

## Root cause

<The confirmed cause, grounded in code, citing file:line. If unconfirmed, write
"Unverified — needs investigation" and list what to check.>

<Where the item involves Senzing behavior, state what the LIVE MCP server returned
at triage time and how it bears on the cause: the tool and parameters, a quote of
the result, the server version and the date. Where the server and the feedback
disagree, give both with their conditions (flag set, SDK version, binding,
platform) and say which governs — never flatten them into one absolute (INV-169).
Mark anything the server cannot reach as observation-only (INV-080/INV-149).>

## Proposed change

<Concrete change(s). For a fix: what to change and why it resolves the root
cause. For a feature: what to add and where it fits the module/flow.>

## Acceptance criteria

- [ ] <Observable, testable outcome that proves the item is resolved.>
- [ ] <Any additional outcome.>
- [ ] Holds on Linux, macOS, and Windows and stays language-agnostic (per @INVARIANTS.md).

## Affected files

- `path/to/file` — <what changes and why>

## Source

- Feedback: `<feedback file path>` → "<entry title>" (<date>, Module <n>; `Source: <bootcamper-reported | self-observed (assistant retrospective)>`)
- Priority: <High | Medium | Low | pending>
- MCP re-check: <server version + date, and the outcome — still reproduces | fixed upstream | server now contradicts the plugin | server does not cover it | n/a (no Senzing fact) | unverified (MCP unreachable). Name the tools called. For `server does not cover it` — or any wording asserting the server lacks something — ALSO add `owner-checked: <the route that would CARRY this fact> — <what it returned>`.>
- Upstream: <not applicable | already sent <date> (per the entry) | sent <date> via `submit_feedback` (`<category>`, anonymous) | declined by the maintainer | submission blocked: <reason> — consented but not sendable (e.g. a `/dry-run`, which forbids `submit_feedback`); the report is STILL OWED>
- Related issues: <#<n>, or "none"> <a closed one counts: it records a decision this may be reopening>
- Invariants: <the INV-NNN conditions this must maintain — `specs/INVARIANTS.md` is live and still governs, whatever the archive's status>
```

Carry the entry's `Source:` value through into the `## Source` block. It records
who noticed the problem — a human who hit real friction, or the graduation
retrospective catching something a bootcamper structurally could not report (e.g.
output that renders blank instead of erroring). Omit the parenthetical only when
the feedback entry itself carries no `Source:` line.

## ⛔ Asserting the server LACKS something requires `owner-checked:`

Any issue whose diagnosis rests on the server not having a fact — "returns no X", "does not
cover", "no MCP tool answers this", "nothing surfaced for these" — MUST name, on the
`MCP re-check` line, the route that would **carry** that fact and what it returned:

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

⚠️ **INV-213 was written when this skill produced specs, and its wording says "a spec".**
The obligation is the same whatever the output format is called — an absence claim is the
input to implementation either way — so it is carried here deliberately rather than allowed
to lapse with the format change. A `DEFERRED INVARIANT` block records that for sign-off.

Exempt: a line declaring `n/a (no Senzing fact)`. With no Senzing fact there is no absence
claim about the server to substantiate.

⛔ **Care is not the remedy.** The second instance of this error in one session was caught only
because the author had made the first one hours earlier and went looking. `tests/test_spec_absence_claims_name_their_owner.py`
enforces the clause so attention is not what stands between a wrong route and a shipped invariant.
