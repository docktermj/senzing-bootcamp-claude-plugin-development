---
description: Cut a release — bump the version, write the CHANGELOG entry and create the git tag as one unit, stopping short of publishing (maintainer tool).
argument-hint: "[major|minor|patch, or an explicit version like 0.6.0] (omit and you will be asked)"
---

Maintainer request: cut a release of the Senzing Bootcamp plugin.

Invoke the `release` skill and follow it end to end.

Bump to apply: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, run the dry run with no bump named, show the maintainer
  the current version and the newest tag, and **ask** which bump they want. ⛔ Do not
  pick one. `release.py` refuses a bare invocation for the same reason — a defaulted
  patch bump would let a bare `/release` cut a release nobody chose.
- If `$ARGUMENTS` names `major`, `minor` or `patch`, pass it as `--major`/`--minor`/`--patch`.
- If `$ARGUMENTS` is an explicit `MAJOR.MINOR.PATCH` version, pass it positionally.

This is a **release-path action**, which is why it is invoked explicitly rather than
inferred. Run the work through `release.py` — the file edits, the changelog and the tag
live in that script on purpose, because a release that does two of the three is the
defect being fixed: `Senzing/senzing-bootcamp-kiro-power` carries a CHANGELOG entry for
`0.5.3` whose tag was never created, and the downstream repos port from **tags**, so that
version cannot be targeted at all. Do not hand-run the bump, the changelog, or the tag.

**Always show the dry run and get approval before `--apply`.** A run without `--apply`
writes nothing and prints the exact diff of both version sites, the changelog entry and
the three git commands. That printout is what approval is given on — not a summary of it.

Let the script's own refusals do the enforcing, and relay them rather than working around
them. It refuses a dirty working tree, a version that does not advance past both the
manifest and the newest tag, a tag that already exists, a manifest and newest tag that
have already diverged, a version site that has stopped matching, and a branch other than
`main`. ⛔ (INV-301) If it refuses, fix what it refused on — never do its job by hand. Hand-editing
one of the three is how the two repos drifted apart in the first place.

⛔ **(INV-301) Stop short of publishing.** `/release` does not push and does **not** invoke
`/propagate-to-public`. Finish by reporting the new version, the release commit and the
tag, then name the next steps and stop:

1. Run `python3 -m unittest discover -s tests` against the release commit — nothing in
   `release.py` runs the suite, and a red release is better caught before publishing.
2. `/propagate-to-public` to mirror the shippable plugin into the public access repo.
3. Push the branch **and the tag** — ⚠️ `git push` alone does not send tags, and an
   unpushed tag is invisible to the downstream repositories that port from it, which is
   the original defect wearing a different hat.

Steps 2 and 3 are the maintainer's to run. Do not run them unless they explicitly ask.
