---
description: Propagate the shippable plugin into the public access repo, stopping at its working tree (maintainer tool).
argument-hint: "[path to the public repo] (omit for ~/senzing.git/senzing-bootcamp-claude-plugin)"
---

Maintainer request: propagate the shippable plugin from this development repo into
the public access repo.

Invoke the `propagate-to-public` skill and follow it end to end.

Destination public repo: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, use the skill's default checkout,
  `~/senzing.git/senzing-bootcamp-claude-plugin`.
- If `$ARGUMENTS` is **given**, treat it as the path to the public repo's working
  tree and pass it to `propagate.sh` as its destination.
- If the destination does not exist, is not a git repo, or its `origin` is not
  `Senzing/senzing-bootcamp-claude-plugin`, **ask rather than syncing somewhere
  uncertain** — the script aborts on each of these, and guessing a destination is
  how a mirror lands in the wrong tree.

This is a **release-path action**, which is why it is invoked explicitly rather
than inferred. Run the mirror through `propagate.sh` — the file operations live in
that script on purpose, because a wrong `--delete` scope would destroy the public
repo's governance files. Do not hand-run the copies.

Mirror only the manifest the skill defines, rewrite this repo's self-references to
the public slug, and leave the public repo's own governance files
(`.github/`, `LICENSE`, `.claude/settings.json`, `.vscode/cspell.json`,
`.gitignore`) untouched — they are owned by the public repo, not by this mirror.
Propagate nothing on the excluded list even if asked to copy everything; the public
repo ships a participant runtime, not maintainer tooling.

Finish by reporting the script's summary, including the `git status --short` block
it prints for the public repo, and point the maintainer at the diff to review.
**Stop at the working tree** — do not commit, push, or open a pull request unless
the maintainer explicitly asks. Publishing the public repo is a separate,
deliberate step.
