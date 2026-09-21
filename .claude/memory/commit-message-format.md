---
name: commit-message-format
description: Every commit in this repo is Conventional Commits with an `issue: #<n>` trailer — one convention, no bypass
metadata:
  type: feedback
---

Every commit in this repository uses **Conventional Commits** for the subject and carries
the issue reference in a trailer, never in the subject:

```
test(citations): pin the statement of what verify does not check

issue: #97

<body explaining what the defect was and what the fix does>

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Why the trailer rather than a subject prefix:** GitHub scans the whole commit message
for `#<number>`, so a trailer collates the commit with its issue just as a subject prefix did —
while the subject stays scannable by type. Keep the `#` (`issue: #42`, not `issue: 42`), or it
links nothing.

**How to apply:** follow the `commit` skill. ⛔ **No bypass is needed.** The
`SKIP_GIT_CONVENTIONS=1` escape exists for genuinely non-conforming commits and is not part of
any normal path here — if a documented path seems to need it, that path is the defect.

**Why this replaced the previous rule (#56, 2026-09-21):** this memory used to require an
issue-number prefix on the commit title for "the `implement-spec` skill, or any change made
while processing a spec under `specs/`", deliberately *not* Conventional Commits, with the hook
bypassed. `specs/` froze at the 2026-09-15 cutover (INV-307) and `/implement-spec` was retired
under #60, so that scope stopped describing anything and issue work fell in the gap.

⚠️ **The rule was stale before it was noticed.** Commits kept being written as Conventional
Commits with an `issue:` trailer — correctly, per the `commit` skill — while this file said
otherwise. Guidance and behavior diverged silently, which is why the rule now names the
convention rather than a skill or directory that can be retired out from under it.

⚠️ #56 proposed a `Refs: #n` footer. `issue: #n` was already shipping and is what the `commit`
skill mandates, so that is what this repo writes; both link identically on GitHub, and a second
trailer form would have split the history for nothing.
