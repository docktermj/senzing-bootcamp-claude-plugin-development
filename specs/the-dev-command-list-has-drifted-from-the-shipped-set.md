# The development command list in docs/development.md has drifted from the shipped set

Maintain the invariant conditions in @INVARIANTS.md and fix the following issue:

## Problem

`docs/development.md`'s "Claude development skills" list (`:112-127`) is the only index of the
maintainer's slash commands. It disagrees with what exists, **in both directions**, and nothing
compares them.

**Documented but not runnable:**

- `:119` — ``/compact-dev-development``. **No skill and no command answers to that name.** The
  skill is `compact-dev-environment`; the correct spelling appears in the same file at `:82`,
  but only as a file path, never as the command. A maintainer typing the documented name gets
  nothing.
- `:118` — ``/delegate-to-mcp-server``. The skill exists; `.claude/commands/delegate-to-mcp-server.md`
  does not (open issue #23). The list presents it as a command to type.

**Shipped but documented nowhere:**

- `review-invariants` and `unattended-spec-loop` are real skills under `.claude/skills/`.
  Neither appears anywhere in `docs/` or `README.md` — verified by `grep -rl` across both.

**Convention applied to some sites and not others:**

- `:125` ``/retrofit-from-public`` and `:126` ``/propagate-to-public`` carry **no description**,
  while every other entry in the list does. Issue #21 fixed exactly this defect one line above
  them — its commit message reads *"docs/development.md listed /auto-test under Publish with a
  dangling dash and no description, unlike every other entry in that list; it now carries one"* —
  and left the two entries directly beneath it untouched. This is Step 7 class 1, a rule applied
  to some of the sites it binds, with the fix itself as the evidence the rule was known.

⚠️ One instance of this class was already fixed during this session (``/production-ready-review``
→ ``/production-readiness-audit``, issue #22). That fix is why the rest were found; it is not a
claim that the list is now correct.

## Root cause

**The guard exists for one surface and was never extended to the other.**

`tests/test_documented_commands_match_the_shipped_set.py` pins exactly this contract for the
**bootcamper** surface: it derives `plugins/senzing-bootcamp/commands/*.md` and the table in
`docs/README.md`, compares them as sets in both directions, and asserts neither side is empty
(INV-265). Its docstring records that the class already recurred once because an earlier fix
*"wrote the missing rows instead of pinning the set"*.

The **maintainer** surface — `.claude/commands/*.md` against the list in `docs/development.md`
— has no equivalent. `tests/test_dev_commands_name_a_real_skill.py` covers a different edge
(command file → skill directory) and explicitly declines the reverse direction:

> ⛔ The reverse direction — every skill has a command — is deliberately NOT asserted here.
> Most maintainer skills currently have no command file, and each is being added under its own
> issue. … When the set is complete, that assertion belongs here.

That deferral is correct for *commands*, but it left the *documentation* direction uncovered by
anything, which is where the drift accumulated. Nothing reads `docs/development.md` at all.

## Proposed change

1. Correct the four drifted entries: fix the ``/compact-dev-development`` name, give
   ``/retrofit-from-public`` and ``/propagate-to-public`` descriptions in the list's existing
   voice, and either add `review-invariants` and `unattended-spec-loop` to the list or record
   why they are deliberately absent.
2. Decide how ``/delegate-to-mcp-server`` should read while its command is unbuilt — dropped
   until #23 lands, or marked as not yet available. A list of runnable commands should not
   silently include one that is not.
3. **Pin the set rather than the rows**, following `test_documented_commands_match_the_shipped_set.py`
   exactly: derive both sides, compare in both directions, assert neither is empty, and assert
   no count appears in prose. ⛔ Writing the missing rows without a guard reproduces the defect
   this file's own docstring says recurred for that reason.
4. ⚠️ The guard's timing interacts with open issues #23–#27, each adding a command. Either land
   it after that series, or scope it to the documentation direction only (every listed command
   resolves to a real skill or command) so it does not fail on every issue until the last one
   lands — the failure mode the sibling test's docstring warns trains its reader to expect red.

## Acceptance criteria

- [ ] No entry in `docs/development.md`'s command list names a skill or command that does not exist.
- [ ] Every entry carries a description, or the list's convention is explicitly stated to be optional.
- [ ] Every skill under `.claude/skills/` with a `SKILL.md` is either listed or recorded as deliberately unlisted.
- [ ] A test derives both sets and compares them, asserting neither side is empty (INV-265) and pinning no count.
- [ ] The test is negative-controlled: reintroduce each defect, confirm it fails, revert.
- [ ] Holds on Linux, macOS, and Windows and stays language-agnostic (per @INVARIANTS.md).

## Affected files

- `docs/development.md` — `:112-127`, the four drifted entries
- `tests/test_documented_dev_commands_match_the_shipped_set.py` — new guard, modeled on the sibling
- `specs/INVARIANTS.md` — an invariant for the dev-command contract, if the maintainer registers one

## Source

- Feedback: self-observed (assistant retrospective) — `production-readiness-audit`, 2026-09-14
- Priority: Medium
- MCP re-check: n/a (no Senzing fact) — internal consistency only; no route was called and none is owed (INV-080).
- Upstream: not applicable
- Related specs: `specs/the-github-issue-path-ships-guarantees-with-no-invariant.md`,
  `specs/the-documented-command-set-has-drifted-from-the-shipped-one.md` (the shipped-surface sibling, implemented)
