---
description: Retrofit changes made in the public access repo back into this development repo, stopping at its working tree (maintainer tool).
argument-hint: "[path to the public repo] (omit for ~/senzing.git/senzing-bootcamp-claude-plugin)"
---

Maintainer request: retrofit changes made in the public access repo back into this
development repo.

Invoke the `retrofit-from-public` skill and follow it end to end.

Source public repo: $ARGUMENTS

- If `$ARGUMENTS` is **empty**, use the skill's default checkout,
  `~/senzing.git/senzing-bootcamp-claude-plugin`.
- If `$ARGUMENTS` is **given**, treat it as the path to the public repo's working
  tree and pass it to `retrofit.sh` as its source.
- If the source does not exist, is not a git repo, or its `origin` is not
  `Senzing/senzing-bootcamp-claude-plugin`, **ask rather than retrofitting from
  somewhere uncertain** — the script aborts on each of these, and a guessed source
  writes an unrelated tree's content over development.

This is the **return path** of the release loop: `propagate-to-public` is
authoritative dev → public, and this brings back the edits that happen downstream —
PR fixes, spelling corrections, direct changes — so the two repos do not drift. Run
the copy through `retrofit.sh`; the file operations live in that script on purpose,
because the reverse slug rewrite is narrow and hand-running it poisons the dev repo's
identity with Senzing URLs.

Retrofit is **not** a mirror image of propagate, and the asymmetries are the whole
risk surface:

- **Never delete.** A dev file absent from public may be a dev addition not yet
  propagated, not a downstream deletion. The script is add/update only and *reports*
  the difference — work that list per file with the maintainer; never delete for them.
- **Never pull governance.** `.github/`, `LICENSE`, `.vscode/`, `.gitignore` and the
  public `.claude/settings.json` are owned by the public repo. Dev keeps its own setup.
- **Apply the inverse transform, scoped.** Only the repo slug and `marketplace.json`'s
  owner name. `plugin.json`'s `author` is the *company* and stays `Senzing`; product
  mentions of "Senzing" and the `docktermj/senzing-bootcamp-free-data` links are not
  touched. Because the rewrite is a clean inverse, an in-sync pair retrofits to an
  empty diff — that is success, not a failure to find anything.

⛔ **Run `python3 -m pytest -q` and reconcile every test the retrofit desynced.** This
is not a formality and no guard replaces it. `tests/` is not in the public mirror and
cannot come back, so a prose edit made downstream lands in a shipped file while the
dev-only test pinning that sentence verbatim still asserts the old wording. Reconcile
by **updating the assertion to the retrofitted wording** — the public edit is the
correction — and regenerate any artifact pinned to a retrofitted file. **Never report a
retrofit as done on an unrun suite.**

Finish by reporting the script's summary, including its "In dev but not in public" list
and the `git status --short` block, then the suite result and anything reconciled.
**Stop at the working tree** — do not commit or push unless the maintainer explicitly
asks.
