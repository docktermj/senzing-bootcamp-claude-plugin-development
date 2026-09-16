---
name: spec-commit-message-format
description: Commit titles for spec work must be prefixed with #<issue-number> so GitHub links the commit to the issue
metadata:
  type: feedback
---

When committing implementation work (`/implement-github-issue`, or any change
made while processing a spec under `specs/`), the commit **title** must be prefixed
with `#<issue-number> ` followed by a plain description — e.g.
`#1 port shell hooks to Python exec-form`. The issue number comes from the working
branch (e.g. branch `1-docktermj-1` → issue **#1**).

**Why:** the `#n` reference makes GitHub collate the commit with its issue. The
maintainer's own commits already follow this (`#1 doc-consistency-audit`,
`#1 module-step-overview`, `#1 interaction-or-questions`).

**How to apply:** use `#n <description>` as the subject — a plain description, NOT
Conventional Commits (`type(scope): …`). This intentionally does not match the repo's
Conventional-Commits reminder hook, so prefix the commit command with
`SKIP_GIT_CONVENTIONS=1` to bypass that reminder when committing spec work. Non-spec
or direct-request commits may still use Conventional Commits.
