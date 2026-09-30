# order-github-issues: this repository's overlay

**The governing copy is `~/.claude/skills/order-github-issues/SKILL.md`** (INV-337), the user-level
skill. This file is the **repo overlay**: the place this repository's obligations for that
skill would live. ⚠️ **The governing copy has no overlay hook**, so nothing here is read by it.

⚠️ **The governing copy is not checked in CI.** It lives under `~/.claude/skills/`, outside
this repository, and a CI runner checks out only the repository. The tests here assert this
overlay; nothing here establishes what the governing copy says on any machine (INV-308).

**This repository adds no obligations to the skill.** The file exists so that
`/order-github-issues` *(user level)* resolves to something this repository can check
(INV-316, #294).
