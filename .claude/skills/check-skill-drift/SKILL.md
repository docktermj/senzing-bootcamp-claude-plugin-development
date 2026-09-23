---
name: check-skill-drift
description: Compare the SHARED-RULES block between this repository's skills and their user-level twins under ~/.claude/skills/, and report any that have drifted apart. Maintainer tool — not part of the bootcamper experience.
disable-model-invocation: true
user-invocable: true
---

# Check skill drift

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin (SBCP). It is
never invoked during a bootcamp.

Run it:

```console
python3 .claude/skills/check-skill-drift/skill_drift.py
```

## Why this exists

`implement-github-issue` has **two** `SKILL.md` files — one in this repository, one under
`~/.claude/skills/` that the maintainer uses across other repositories. On **2026-09-23** they
were found **two amendments apart**: #119 and #124 edited only the user-level copy, while this
repository's copy — ⛔ **the one that ships to the four child ports** — still carried its
original text.

⛔ **The repository's copy asserted that it governed.** It does not: measured 2026-09-23 by
reading the skill body Claude Code injected on invocation against marker strings unique to each
file, **the user-level copy is what loads**, even with a project copy present. That false
sentence is why the divergence survived two runs.

⚠️ **This is INV-300 —** *a rule with two homes is a rule that will disagree with itself* **—**
happening to R8, the rule `docs/FAMILY_WORKFLOW.md` cites INV-300 to justify children linking to
rather than restating.

## What is compared, and what is not

Only the span delimited by `<!-- SHARED-RULES:BEGIN -->` … `<!-- SHARED-RULES:END -->`, which is
meant to be **byte-identical** in both copies.

⛔ **Everything outside it may legitimately differ, and must.** This repository's copy cites
`docs/FAMILY_WORKFLOW.md` and `specs/INVARIANTS.md`; the repositories the user-level copy serves
have neither. Requiring the files to be identical would either break that copy elsewhere or
strip the citations that make the rule enforceable here. **Behaving the same is the goal;
being identical is not.**

## ⛔ What it cannot see

Both limits are printed on every run rather than left for the reader to infer (INV-308):

- **A commit made outside a Claude Code session triggers no hook here.** The pre-commit hook in
  `.claude/settings.json` fires on the Bash tool, so a terminal commit bypasses it.
- **An edit to a user-level copy produces no repository event at all.** Nothing here can observe
  it until something runs this check.

⚠️ **So this narrows the window; it does not close it.** A report that claimed otherwise would be
worse than none — the reader would stop looking.

⚠️ **On a machine with no `~/.claude/skills/`** — a CI runner, for instance — the script compares
**nothing** and says so, distinguishing *could not check* from *nothing to check*. It exits 0,
because absence of the other copy is not drift.

## Scope note

`.claude/` is not propagated to the public repo (`propagate.sh` mirrors `plugins/`,
`.claude-plugin/`, `docs/` and `README.md` only), so this skill never ships to bootcampers.
