---
name: propagate-to-public
description: 'Propagate the shippable Senzing Bootcamp plugin from this development repo into the public access repo (Senzing/senzing-bootcamp-claude-plugin). Use when the maintainer wants to publish, release, sync, or push the plugin to the public repo. Mirrors only what a user needs to install and use, rewrites development self-references to the public Senzing slug, and stops at the working tree (no commit, no push). Maintainer tool — not part of the bootcamper experience.'
---

# Propagate → Public access repo

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It copies the *shippable* subset of this development repo
(`docktermj/senzing-bootcamp-claude-plugin-development`) into the **public
access repo** (`Senzing/senzing-bootcamp-claude-plugin`, cloned locally at
`~/senzing.git/senzing-bootcamp-claude-plugin`).

The public repo holds **only what a user needs to install and use the plugin**.
Development-only assets stay in this repo. The public repo also has its **own**
Senzing-org governance files (`.github/`, `LICENSE`, `.claude/settings.json`,
`.vscode/cspell.json`, `.gitignore`) that this tool **must never touch** — it is
a scoped mirror, not a wholesale copy.

The work is done by [`propagate.sh`](propagate.sh) in this skill's directory. It
is deterministic on purpose: a wrong `--delete` scope could destroy the public
repo's governance files, so the file operations live in a vetted script rather
than being hand-run each time.

## What gets propagated (the manifest)

**Propagated** (mirrored into the public repo, deletions included):

- `plugins/senzing-bootcamp/**` — the whole plugin payload (skills, commands,
  hooks, scripts, `docs/`, `docs/examples/`, `.mcp.json`, `plugin.json`), minus
  `__pycache__/`, `*.pyc` and `.pytest_cache/`.
- `.claude-plugin/marketplace.json` — required for `claude plugin marketplace add`.
- `README.md` — user-facing (Claude Desktop install instructions).
- `docs/` — user-facing (`docs/README.md`, Claude Code CLI install). Treated as
  a **user-facing** directory and mirrored wholesale **except `docs/development.md`**
  (see Excluded); do **not** put maintainer-only notes here.

**Excluded** (development-only — never propagated):

- `.claude/**` — dev commands, memory, skills (including *this* skill), and
  `settings.local.json`. (The plugin's own `plugins/senzing-bootcamp/skills/`
  *is* the bootcamp payload and **is** propagated — do not confuse the two.)
- `specs/**` — spec-driven development artifacts.
- `docs/development.md` — the development-loop index (`/feedback-to-issues`,
  `/implement-github-issue`, `/dry-run`, `/propagate-to-public`, …). ⚠️ **The one exception
  inside an otherwise user-facing directory.** Every skill it names is excluded from
  this mirror, so publishing it hands users a list of commands their install does not
  have. It reached the public working tree on 2026-08-16 because "`docs/` is
  user-facing" was a convention stated here rather than a rule enforced in
  `propagate.sh`; it is now an `rsync --exclude`.
- `feedback/**` — the processed-feedback archive and its ledger. Carries raw bootcamper
  text (usernames, workstation details, dataset names), so it is **never** mirrored to a
  public repo. Committed in this repo for durability; excluded here for privacy.
- `MIGRATION.md`, `scripts/sync-check.sh` (all of top-level `scripts/`),
  `.sync-state.json` — Kiro-Power → Claude-plugin sync infrastructure.
- `resources/` — maintainer-only brand assets
  (`senzing-style-reference.pdf` is explicitly *not shipped*; the plugin's
  `brand_tokens.py` inlines everything it needs, so this is safe to exclude).
- `.history/`, `__pycache__/`, `*.pyc`, `.pytest_cache/` — editor/build/test cruft.
  `.pytest_cache/` needs the explicit exclude even though it looks self-managing: pytest
  writes a `.pytest_cache/.gitignore` containing `*`, so a copied cache is invisible to the
  public repo's `git status` and therefore to this skill's review step.
- The dev `.gitignore` — the public repo keeps its own tailored version.

**Preserved** (owned by the public repo — the tool never reads, writes, or
deletes these): `.github/**`, `LICENSE`, `.claude/settings.json`,
`.vscode/cspell.json`, `.gitignore`.

## Transform applied during propagation

This repo's **self-references are rewritten to the public slug** so the published
files point users at the Senzing repo:

- `docktermj/senzing-bootcamp-claude-plugin-development` → `Senzing/senzing-bootcamp-claude-plugin`
  wherever it appears (README marketplace URL and raw-content PDF link,
  `docs/README.md` `marketplace add` command, `plugin.json` homepage/repository).
- `marketplace.json` owner `"name": "docktermj"` → `"name": "Senzing"`.

⛔ **The two slugs differ in owner *and* name.** The development repo carries a
`-development` suffix the public repo does not, so `SLUG_OLD` in `propagate.sh`
MUST stay the suffixed string. Left unsuffixed it still matches — as a
*prefix* — and publishes the broken
`Senzing/senzing-bootcamp-claude-plugin-development`. For the same reason a
dev-tree file still carrying the old unsuffixed slug is not matched at all, and
ships a `docktermj/…` link to the public repo.

The separate `docktermj/senzing-bootcamp-free-data` links (in Module 4) are a
**different repo** and are intentionally left unchanged.

## How to run

1. Confirm the public repo is checked out at
   `~/senzing.git/senzing-bootcamp-claude-plugin` (or note its path). Ideally its
   working tree is clean so the resulting diff is easy to review.
2. Run the script from the dev repo:

   ```console
   .claude/skills/propagate-to-public/propagate.sh
   ```

   Pass a path to override the default destination:

   ```console
   .claude/skills/propagate-to-public/propagate.sh /path/to/public-repo
   ```

The script enforces its own safety guards and **aborts** if any fail:

- the source doesn't look like this dev repo,
- the destination isn't a git repo,
- the destination's `origin` isn't `Senzing/senzing-bootcamp-claude-plugin`
  (prevents syncing into the wrong tree),
- source and destination are the same directory,
- `rsync` is unavailable.

## After it runs

The script **only updates the public working tree** — by design it does not
commit or push (this matches how releases are reviewed here).

1. Report the script's summary to the maintainer, including the `git status
   --short` block it prints for the public repo.
2. Point them at the public repo to review the diff, e.g.
   `git -C ~/senzing.git/senzing-bootcamp-claude-plugin diff`.
3. Do **not** commit, push, or open a PR unless the maintainer explicitly asks —
   committing/publishing the public repo is a separate, deliberate step. If they
   do ask, remember commit subjects in these repos start with `#<issue-number>`.

## Guardrails

- **Never** modify the public repo's governance files (`.github/`, `LICENSE`,
  `.claude/settings.json`, `.vscode/cspell.json`, `.gitignore`). They are out of
  scope; the mirror is path-scoped precisely so it can't reach them.
- **Never** propagate anything on the excluded list above, even if asked to "copy
  everything" — the public repo is deliberately install-and-use only.
- **Don't guess the destination.** If the public repo isn't at the default path
  and none was given, ask for it rather than syncing somewhere uncertain.
- **Don't commit or push** as part of propagation. Sync files, report, stop.
- If the manifest needs to change (a new shippable path, or a new dev-only path
  to exclude), update both this manifest **and** `propagate.sh` together so they
  never drift.
