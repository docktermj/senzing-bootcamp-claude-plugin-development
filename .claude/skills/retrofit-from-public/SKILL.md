---
name: retrofit-from-public
description: 'Retrofit changes made in the public access repo (Senzing/senzing-bootcamp-claude-plugin) by reporting them: it compares public against the last propagation and files GitHub issues in this development repo describing what diverged. Use when the maintainer wants to bring public-repo edits (PR fixes, typo/spelling corrections, direct changes) to development as issues. The inverse direction of propagate-to-public: it writes nothing into this repo, and the inverse slug rewrite is applied by whoever implements a filed issue. Maintainer tool — not part of the bootcamper experience.'
argument-hint: "[path to the public repo] (omit for ~/senzing.git/senzing-bootcamp-claude-plugin)"
---

# Retrofit ← Public access repo

This is a **maintainer** tool for developing the Senzing Bootcamp Claude Plugin
(SBCP). It reports changes that were made in the **public access repo**
(`Senzing/senzing-bootcamp-claude-plugin`, cloned locally at
`~/senzing.git/senzing-bootcamp-claude-plugin`) and files issues describing them in
this **development repo** (`docktermj/senzing-bootcamp-claude-plugin-development`).

It is the counterpart to `propagate-to-public`. Propagate is authoritative
(dev → public). Retrofit is the *return path* for edits that happen in public —
PR fixes, spelling corrections, or direct changes — so they aren't lost.

The work is done by [`retrofit.sh`](retrofit.sh) in this skill's directory. Take the
comparison from it, never from a hand-run diff: the baseline and the slug rewrite it
compares through are narrow, and a hand-run diff reports every dev self-reference as a
public edit.

## Retrofit is NOT a mirror image of propagate — three asymmetries

1. **The transform is inverted, narrowly.** Propagate rewrites this repo's slug
   to the public one; whatever comes back must undo it, or the dev repo's identity would be
   poisoned with Senzing URLs. Both halves are restored — the `docktermj` owner
   *and* the `-development` name suffix the public repo does not carry:
   - `Senzing/senzing-bootcamp-claude-plugin` → `docktermj/senzing-bootcamp-claude-plugin-development`
   - `marketplace.json` owner `"name": "Senzing"` → `"name": "docktermj"` (that file only)

   It is **not** a blanket `Senzing → docktermj`. `plugin.json`'s
   `"author": { "name": "Senzing" }` is the *company* (stays Senzing in both
   repos), the skill content mentions "Senzing" constantly, and the
   `docktermj/senzing-bootcamp-free-data` links are already `docktermj` — none of
   those are touched. The script applies neither direction itself: it compares
   public against a **baseline** that the last-propagated tag's own `propagate.sh`
   has already forward-rewritten (see "How to run"), so **a public repo that
   nobody edited reports every path `same`**, and a file carrying the dev slug does
   not differ for that reason alone. The inverse is applied by whoever implements a
   filed issue.

2. **It never deletes.** Propagate can mirror-with-delete because dev is the
   source of truth. Retrofit can't: a new dev file under `plugins/` not yet
   propagated would be wrongly deleted. So retrofit writes nothing and *reports*
   files the last propagation published that are absent from public; a filed issue
   says what to do about each — it never deletes them for you.

3. **Governance is one-directional.** The public repo owns a governance layer
   (`.github/`, `LICENSE`, `.vscode/cspell.json`, `.gitignore`,
   `.claude/settings.json`) that the dev repo has never had. Retrofit **does not**
   pull it in — dev keeps its own setup.

## What gets compared (the manifest)

**Compared** (public against the last propagation's baseline, read-only):

- `plugins/senzing-bootcamp/**` — the whole plugin payload, minus `__pycache__/`,
  `*.pyc` and `.pytest_cache/`.
- `.claude-plugin/marketplace.json`
- `README.md`
- `docs/`

**Never touched in dev** (dev-only — outside the compared paths, and the script
writes nothing anywhere in dev):

- `.claude/**` — dev commands, memory, skills (**including this skill and
  `propagate-to-public`**) and `settings.local.json`.
- `specs/**`, `MIGRATION.md`, `scripts/sync-check.sh`, `.sync-state.json`,
  `resources/` — development infrastructure and maintainer assets.

**Never read from public** (public-owned governance): `.github/`, `LICENSE`,
`.vscode/`, `.gitignore`, public `.claude/settings.json`.

## How to run

1. Make sure the public repo is at `~/senzing.git/senzing-bootcamp-claude-plugin`
   (or note its path), checked out at the branch/commit whose changes you want.
2. Run from the dev repo:

   ```console
   .claude/skills/retrofit-from-public/retrofit.sh
   ```

   Pass a path to override the default source:

   ```console
   .claude/skills/retrofit-from-public/retrofit.sh /path/to/public-repo
   ```

   With no argument, use the default checkout. An argument is the path to the public
   repo's working tree: pass it to `retrofit.sh` as its source.

**The baseline (#202).** Public is compared against what dev last propagated, not against
dev's current tree, so work done in dev since then never reads as a public edit. By default
the baseline is the **dev tag with the same name as public's newest tag**. The script
extracts that tag with `git archive` into a temporary directory and runs **that tag's own**
`propagate.sh` into a throwaway destination. The paths, the `docs/` exclusions and the slug
rewrite are therefore the ones that release actually published. The report header names the
tag and how it was chosen. The temporary directory is removed on every exit, and dev's
working tree is never read for the comparison, so uncommitted dev edits do not change it.

⚠️ **After a propagation is committed in public but before public is tagged**, public's
newest tag is still the previous release, and the new release would read as public edits.
Name the propagated dev tag instead:

```console
.claude/skills/retrofit-from-public/retrofit.sh --base <dev-tag> [/path/to/public-repo]
```

The script enforces safety guards and **aborts** if any fail: the destination
isn't this dev repo, the source isn't a git repo, the source's `origin` isn't
`Senzing/senzing-bootcamp-claude-plugin`, source and destination are the same
directory, or `rsync` or `python3` is missing (the tag's `propagate.sh` needs both, and
its failure aborts the run).
It also aborts, before printing any comparison, when there is **no usable baseline**:
public has no tag, no dev tag has that name, `--base` names a tag that does not exist,
the tag carries no `propagate.sh` (dev tags `0.3.5` and `0.3.6`), or that `propagate.sh`
fails. Each message names the tag and suggests `--base`.

## After it runs

⛔ **(INV-312) (#54) The script writes nothing. It compares and reports; the output of this command is
GitHub issues, not a modified working tree.**

1. Report the script's summary: the baseline tag it compared against and how it was chosen,
   which propagated paths differ from that baseline, which are absent in public, the
   "In the last propagation but not in public" list (files the baseline holds that public
   lacks), and the public commits since the newest tag. A path differs only where public
   changed after that propagation; dev work not yet propagated is `/propagate-to-public`'s
   concern and does not appear.
2. **Group the divergence into coherent changes**, one per thing a maintainer would decide about
   — a Dependabot bump, a workflow added downstream, a prose correction — not one per file.
3. ⛔ **Search the tracker before filing each one.**

   ```bash
   gh issue list --state all --search "<the public commit subject or SHA>"
   ```

   A change already absorbed, or already filed, must not get a second issue. The tracker is the
   record; this command keeps no ledger of its own, because a second list of the same fact is how
   two records come to disagree.
4. **(INV-314) Show the maintainer each title and body and get a yes**, then file:

   ```bash
   gh issue create --title "<what diverged, not the symptom>" --body-file <file>
   ```

   ⛔ **Filing is outward-facing and immediate** — the same gate `/feedback-to-issues` and
   `/production-readiness-audit` apply, for the same reason: an issue can be edited or closed
   afterwards but never un-filed.
5. ⛔ **(INV-312) Files in this repository only.** Cross-repo filing belongs exclusively to
   `/escalate-to-parent` *(children only)*; this command never files anywhere but its own
   tracker, in the parent and in every child that inherits it.
6. Each issue body carries the **public commit** (subject and SHA), the paths affected, and
   ⚠️ **the inverse slug rewrite as work still to do** — see below.

⚠️ **The inverse transform is still required; it just is not automatic.** Whoever implements a
filed issue applies it by hand to any text they bring across, or the dev repo ends up carrying
public self-references. `propagate.sh` holds the forward direction and the two must still agree.

⛔ **Why this stopped copying, which is worth keeping rather than cutting.** `tests/` is not in
the public mirror and cannot come back, so a copied prose edit landed in a shipped file while the
dev-only test quoting that sentence kept asserting the old wording — and nothing reconciled the
two. Measured 2026-08-16 on `2223961`, the British→US spelling corrections: a **correct** edit,
faithfully retrofitted, left **12 failed / 2730 passed**, ten of them that desync, plus an INV-065
pair where the example `.md` was retrofitted and the committed PDF was not. Nobody noticed until
the next full run.

That is now impossible rather than guarded against: nothing is copied, so nothing desyncs, and the
reconciliation happens deliberately inside the issue's implementation where the suite is run
anyway.

## Guardrails

- **Each filed issue states the inverse transform it owes, scoped** to the repo slug
  and `marketplace.json`'s owner name — never `plugin.json`'s `author`, product
  mentions of "Senzing", or `LICENSE`.
- **Never delete, and never add.** Report what differs and let the maintainer decide; the
  script has written nothing since #54.
- **Never pull governance** into dev.
- **Don't guess the source.** If the public repo isn't at the default path and
  none was given, or the source does not exist, is not a git repo, or its `origin` is
  not `Senzing/senzing-bootcamp-claude-plugin`, ask rather than retrofitting from
  somewhere uncertain. The script aborts on each of these, and a guessed source files
  issues about an unrelated tree's content.
- ⛔ **Don't write into the dev tree at all.** Compare, report, file issues, stop (#54).
- Keep this manifest and `retrofit.sh` in step with `propagate-to-public` — the
  two must always agree on which paths are propagated and on the transform.
