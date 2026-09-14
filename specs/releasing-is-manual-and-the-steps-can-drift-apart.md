# Releasing is manual and the steps can drift apart

Maintain the invariant conditions in @INVARIANTS.md and implement the following improvement:

## Problem

A release asserts one version in several independent records — the plugin manifest, the example
recap, a CHANGELOG entry and a git tag — and nothing performs them as a unit. A concrete
instance in a sibling repo: `Senzing/senzing-bootcamp-kiro-power` carries a CHANGELOG entry
reading `[0.5.3] - 2026-09-10` while its newest git tag is still `0.5.1`. The changelog moved;
the tag did not.

That matters beyond tidiness. Under the porting model, downstream development repositories
(Kiro, ChatGPT, Copilot) pull from a **tagged release** rather than from HEAD, so an untagged
version is invisible to the mechanism that governs the whole system — **a port cannot target a
release that was never tagged.**

## Root cause

No tooling exists. `tests/test_example_recap_sync.py:507` already pins the example recap's
`**Plugin version:**` row to `plugins/senzing-bootcamp/.claude-plugin/plugin.json`, so those two
cannot disagree. **The git tag is the only unguarded record**, and it is the one that came loose
in the sibling repo.

## Proposed change

A `release` skill and a `/release` command that perform the bump, the changelog entry, the
commit and the tag as one operation, refusing before writing when any precondition fails.
⛔ It stops short of publishing: `/propagate-to-public` remains a separate, deliberate step,
because publishing is the outward-facing action and coupling it to an irreversible local one
removes the gate between them.

## Acceptance criteria

- [ ] The version, changelog and tag move together, with no path that updates one without the others.
- [ ] The command refuses, with an actionable message, on a dirty working tree or a
      non-advancing version.
- [ ] The tag it produces is one a downstream repository could target.
- [ ] Holds on Linux, macOS, and Windows and stays language-agnostic (per @INVARIANTS.md).

## Affected files

- `.claude/skills/release/SKILL.md`, `.claude/skills/release/release.py` — new
- `.claude/commands/release.md` — new
- `docs/development.md` — the `/release` entry
- `tests/` — guards for the mutation and the version-site coverage
- `specs/IMPLEMENTED.md` — the record

## Source

- Feedback: GitHub issue #27 (`Source: self-observed (assistant retrospective)`)
- Priority: Medium
- MCP re-check: n/a (no Senzing fact) — release mechanics assert nothing about Senzing, so no
  route was called and none is owed (INV-080).
- Upstream: not applicable
- Related specs: none
