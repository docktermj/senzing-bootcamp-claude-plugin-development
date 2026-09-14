# The /implement-github-issue path ships durable guarantees with no invariant and no deferral

Maintain the invariant conditions in @INVARIANTS.md and fix the following issue:

## Problem

Four durable guarantees landed between the last audit (`7b43eee`, 2026-09-03) and
2026-09-14. Each is mechanically enforced by a new test. **None is registered as an
invariant, none carries a `DEFERRED INVARIANT` block, and none is named anywhere in
`specs/IMPLEMENTED.md`.**

| Guard added | The durable rule it enforces |
|---|---|
| `tests/test_dev_commands_name_a_real_skill.py` | every `.claude/commands/*.md` MUST name a skill that exists, and none may be silent about the skill it fronts |
| `tests/test_maintainer_tooling_stays_out_of_public.py` | no `rsync` source in `propagate.sh` may reach into `.claude/` |
| `tests/test_ci_workflow_guards_the_fpdf2_matrix.py` | the CI matrix MUST keep both fpdf2 jobs, and third-party actions MUST stay SHA-pinned |
| `tests/test_fpdf2_dependency_is_declared.py` | `fpdf2` MUST be declared in `requirements-dev.txt` |

This is the reverse-contract state this repo already recognizes and names: a prior audit
recorded *"each ships a rule that is guarded by a test and registered nowhere, which is the
reverse-contract state this skill exists to surface"*, and the established response is a
`DEFERRED INVARIANT` block queued for the maintainer's sign-off. Thirty-six such blocks exist.
These four got none.

The consequence is the INV-155 shape: the guarantee exists in the product and nowhere in the
ruleset, so nothing binds future work to it and nothing notices when a later change
contradicts it. A contributor who deletes `test_maintainer_tooling_stays_out_of_public.py` as
redundant removes the only thing standing between `propagate.sh` and publishing the entire
maintainer surface — and no invariant would record that a rule had been lost.

## Root cause

**The work was routed through `/implement-github-issue`, which has no reverse-contract step.**

`.claude/skills/implement-spec/SKILL.md` records every implementation in
`specs/IMPLEMENTED.md` and requires each to register the invariant it establishes or state
that it establishes none — `tests/test_spec_ledger_invariants.py` enforces that pairing, and
`tests/test_new_hard_rules_are_cited_or_deferred.py` backs it with a diff-based scan.

`/implement-github-issue` has neither step. Its phases run branch → assess → clarify →
approach → implement → test → CI mirror → push → PR, and end at "PR open for review". Nothing
in it reads `INVARIANTS.md`, writes to `specs/IMPLEMENTED.md`, or asks whether the change
shipped a rule. Issues #18, #19, #20, #21, #22, #30 and #33 all landed through it.

**Two mechanical blind spots let it pass unnoticed:**

1. `conformance.py` scans `plugins/senzing-bootcamp/**/*.md` only
   (`.claude/skills/production-readiness-audit/conformance.py:100`), and its `since` view diffs
   `-- plugins/senzing-bootcamp` (`:385`). The `.claude/` surface is invisible to it. This half
   is **already on record** in a prior ledger entry — *"lives in `.claude/skills/dry-run/`,
   which does not ship … and which `conformance.py` does not scan"* — so it is context here,
   not a new finding.
2. `tests/test_new_hard_rules_are_cited_or_deferred.py:132` filters to paths beginning
   `plugins/`, so it inherits the same blindness and reports green by not running.

What is new is that a **development surface has since appeared inside that blind spot**:
`.claude/commands/` did not exist at the last audit and now holds seven files and 17 hard-rule
lines, governed by no invariant — `grep -in 'command' specs/INVARIANTS.md` returns 17 hits and
every one is about bootcamper-facing commands (`/model`, `/effort`, SDK and shell commands).

⚠️ **Self-reported:** this audit's own session added the seventh command file
(`.claude/commands/production-readiness-audit.md`, issue #22) through that same path, and did
not register an invariant either. The finding is not about someone else's run.

## Proposed change

Not a code fix. Two decisions belong to the maintainer, and this spec exists so neither is
lost:

1. **Decide whether the four guarantees above should be registered as invariants.** Draft
   wording for each, next unused ID, index entry in the same edit, per `INVARIANTS.md`'s own
   rules. ⛔ Do not register any of them without the maintainer's sign-off on the wording.
   `INVARIANTS.md` is append-only; nothing here proposes deleting or renumbering anything.
2. **Close the process gap so the class stops recurring.** The cheapest option is a
   reverse-contract step in `/implement-github-issue` mirroring `/implement-spec`'s: before
   Gate 2, ask whether the change ships a durable rule, and if so register it or record a
   `DEFERRED INVARIANT` block. Widening `conformance.py` to scan `.claude/` is the more
   thorough option and a larger change — it would put the whole maintainer surface under the
   same contract as shipped text.

## Acceptance criteria

- [ ] Each of the four guarantees is either registered as an invariant (with the maintainer's
      sign-off on the wording) or explicitly recorded as establishing none, with the reason.
- [ ] `/implement-github-issue` gains a reverse-contract step, or the maintainer records a
      decision that the dev surface is deliberately exempt and why.
- [ ] A ledger entry records the outcome, so the next audit does not re-derive this.
- [ ] Holds on Linux, macOS, and Windows and stays language-agnostic (per @INVARIANTS.md).

## Affected files

- `specs/INVARIANTS.md` — up to four new invariants, appended with index entries, pending sign-off
- `~/.claude/skills/implement-github-issue/SKILL.md` — a reverse-contract step before Gate 2
- `.claude/skills/production-readiness-audit/conformance.py` — optionally widen the scanned corpus
- `tests/test_new_hard_rules_are_cited_or_deferred.py` — optionally widen the path filter at `:132`
- `specs/IMPLEMENTED.md` — record the outcome

## Source

- Feedback: self-observed (assistant retrospective) — `production-readiness-audit`, 2026-09-14
- Priority: Medium
- MCP re-check: n/a (no Senzing fact) — this is an internal consistency finding and asserts
  nothing about Senzing behavior, so no route was called and none is owed (INV-080).
- Upstream: not applicable
- Related specs: `specs/the-dev-command-list-has-drifted-from-the-shipped-set.md`
