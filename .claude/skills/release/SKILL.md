---
name: release
description: 'Cut a release of the Senzing Bootcamp plugin: bump the version everywhere it is asserted, write the CHANGELOG entry, commit and create the git tag — as one operation, with no path that moves one without the others. Use when the maintainer wants to release, cut a release, bump the version, tag a version, or prepare a version for the downstream repos to port from. Stops short of publishing; /propagate-to-public is the next step. Maintainer tool — not part of the bootcamper experience.'
---

# Release

A **maintainer** tool for developing the Senzing Bootcamp Claude Plugin (SBCP).
Never invoked during a bootcamp. It is the step *before*
[`propagate-to-public`](../propagate-to-public/SKILL.md): this skill decides and
records **which version exists**; that one publishes it.

The work is done by [`release.py`](release.py) in this skill's directory, for the
same reason `propagate-to-public` fronts `propagate.sh` — the operation has to be
all-or-nothing, and a procedure a model follows step by step is exactly a procedure
that can stop after step two. Here the steps are one function call.

## The defect this exists to prevent

The sibling repo `Senzing/senzing-bootcamp-kiro-power` carries a CHANGELOG entry
reading `[0.5.3] - 2026-09-10` while its newest git tag is still `0.5.1`. The
changelog moved; the tag did not.

⛔ **That is not tidiness.** Under the porting model, the downstream development
repositories (Kiro, ChatGPT, Copilot) port from a **tagged release** of Claude
rather than from HEAD. A version that was never tagged is invisible to the
mechanism that governs the whole system: *a port cannot target a release that was
never tagged.*

Of the three things a release moves, two were already guarded here and one was not:

| Moves | Guarded before this skill? |
|---|---|
| `plugins/senzing-bootcamp/.claude-plugin/plugin.json` | — |
| the shipped example recap's `**Plugin version:**` row | ✅ `tests/test_example_recap_sync.py` pins it to the manifest |
| the git tag | ⛔ **nothing related a version to a tag at all** |

So a release could bump both files, pass the whole suite, and ship untagged. That
is the kiro-power shape, and it is what `release.py` and
`tests/test_release_bumps_version_changelog_and_tag_together.py` make impossible.

## What it does, in one unit

1. Rewrites every entry in `VERSION_SITES` (the two files above).
2. Creates `CHANGELOG.md` if absent — **seeded from the tags that already exist**,
   one entry each, newest first — and prepends the new entry thereafter.
3. Commits those files, and **only** those files.
4. Tags **that commit**, annotated.

⛔ **The commit comes before the tag, and that ordering is load-bearing.** Edit the
files and then run `git tag` and you tag **HEAD** — the commit *before* the bump. The
tag exists, the name is right, and checking it out gives you the previous release
under the new name. The test reads the three files *out of the tag* for exactly this
reason; asserting only that a tag exists passes against the broken version.

⛔ **There is no flag that performs part of a release.** No `--no-tag`, no
`--changelog-only`. Any such flag reintroduces the defect, and a test asserts the
interface offers none.

## How to run it

```console
.claude/skills/release/release.py --minor          # preview (writes nothing)
.claude/skills/release/release.py --patch --apply  # do it
.claude/skills/release/release.py 0.6.0 --apply    # explicit target
```

⛔ **Dry run is the default; `--apply` is what writes.** This script is fronted by a
slash command, so it can be run by a model. Git tags are **repository-global** — a
tag is not scoped to a worktree, and once anyone has fetched it, it cannot be taken
back. A destructive default is not acceptable under those conditions. `--dry-run` is
accepted explicitly so a caller can state the intent rather than depend on a default
staying what it is.

**Always show the maintainer the dry run and let them approve it before `--apply`.**
The dry run prints the exact diff of both version sites, the changelog entry it would
write, and the three git commands — that is what approval is given on.

### The refusals

The script exits non-zero and changes nothing when:

| Refusal | Why |
|---|---|
| the working tree is dirty | the release commit must carry the bump and nothing else, and the tree is what `propagate.sh` mirrors — an uncommitted file is either swept into the release commit or published untracked |
| the version does not advance | past the manifest **and** past the newest tag; a version that is not strictly newer stops being a key |
| the tag already exists | re-pointing a tag rewrites what a downstream repo may already have fetched |
| the manifest and the newest tag disagree | the kiro-power split as a *starting* state — releasing from it buries the inconsistency one version deeper. `--allow-divergent-base` exists but only after you have decided which of the two is right |
| a version site is missing, or stops matching | releasing now would advance the other site and leave this one stale — the exact split the tool exists to prevent |
| the branch is not `main` | a tag made on a feature branch survives a squash-merge as a pointer to a commit that never lands on `main`, so a downstream repo porting from it gets a tree `main` does not contain. `--allow-branch` if you mean it |

⚠️ **The dirty-tree refusal has no override, deliberately.** The acceptance criterion
is that it refuses; a flag to proceed anyway is the path that makes it advisory.

## CHANGELOG.md

`CHANGELOG.md` did not exist in this repo before this skill, so the first `--apply`
**creates** it, reconstructing one entry per existing tag from the commit subjects
between tags. Two things about that seed are deliberate:

- ⚠️ **It is labeled as reconstructed, and the label names the versions it covers**
  ("entries *X.Y.Z and earlier*"), not "entries below". Written positionally, the
  sentence is true the day the file is seeded and false the next release, because a
  prepended entry lands between the note and the entries it describes.
- The **earliest** tag is not itemized. Everything before the first release would
  otherwise land in it, which is noise rather than history.

⚠️ **Seeded entries are commit subjects, not release notes.** They are honest about
what happened and say nothing about why. Curating them is a fine thing to do by hand;
just never edit an entry's `## [version] - date` heading, because the version, the
file and the tag were written together on purpose.

⚠️ **Tag dates are read off the commit, not off the tag object.** The seven tags this
repo already carries are lightweight and have no date of their own. New tags are
annotated, so both shapes keep working.

## After it runs

⛔ **`/release` does not publish, and must not.** It does not push and it does not
invoke `/propagate-to-public`. Report the new version, the commit and the tag, then
name the next steps and stop:

1. Run the suite — `python3 -m unittest discover -s tests` — against the release
   commit. Nothing in `release.py` runs it, and a red release is worth catching before
   it is published rather than after.
2. `/propagate-to-public` to mirror the shippable plugin into the public access repo.
3. Push the branch **and the tag**. ⚠️ `git push` alone does not send tags; an unpushed
   tag is invisible to the downstream repositories that port from it, which is the
   original defect wearing a different hat.

Steps 2 and 3 are the maintainer's to run. Do not run them as part of a release unless
asked.

## Guardrails

- **Never run the script without showing the dry run first.** Approval is given on the
  diff, not on the intent.
- **Never push.** Not the branch, not the tag.
- **Never hand-edit one of the three things.** Bumping `plugin.json` by hand, or adding
  a changelog entry by hand, is how the two repos drifted in the first place. If the
  script refuses, fix what it refused on — do not do its job manually.
- **Never invent the version.** Ask the maintainer for the bump size (or the explicit
  version) if they did not say; `release.py` refuses a bare invocation for the same
  reason, so a defaulted patch bump cannot slip through.
- If a **new** file starts asserting the version, add it to `VERSION_SITES` in
  `release.py`. `tests/test_release_covers_every_version_site.py` scans the tracked
  files and fails on the commit that introduces an unlisted one, so this is caught
  before a release ships it stale rather than after.

⚠️ **If `tag.gpgsign` is set in the maintainer's git config, the tag is signed** and
git may prompt for a passphrase. The script does not override that setting — a
maintainer's signing policy is not a release tool's to switch off — so an unattended
run can block there. Say so rather than retrying.

## Scope note

⛔ **This skill is development-repo only and must NOT be propagated to the public
plugin repo.** `.claude/` is not in `propagate.sh`'s manifest (it mirrors `plugins/`,
`.claude-plugin/`, `docs/` and `README.md` only), and
`tests/test_maintainer_tooling_stays_out_of_public.py` asserts that no rsync source
reaches into `.claude/`, so this is enforced rather than remembered.
