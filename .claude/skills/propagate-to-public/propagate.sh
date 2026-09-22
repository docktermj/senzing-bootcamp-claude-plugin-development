#!/usr/bin/env bash
set -euo pipefail
# Propagate the shippable plugin from this DEVELOPMENT repo into the PUBLIC
# access repo (Senzing/senzing-bootcamp-claude-plugin). Files only — this never
# commits or pushes. See .claude/skills/propagate-to-public/SKILL.md for the
# manifest and rationale.
#
# Usage: propagate.sh [path-to-public-repo]
#   Default public repo: ~/senzing.git/senzing-bootcamp-claude-plugin

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # dev repo root
default_dest="$HOME/senzing.git/senzing-bootcamp-claude-plugin"
dest="${1:-$default_dest}"

# --- Safety guards --------------------------------------------------------- #
[ -d "$here/plugins/senzing-bootcamp" ] || {
  echo "Source doesn't look like the dev repo: $here" >&2; exit 1; }
[ -d "$dest/.git" ] || {
  echo "Public repo not found (or not a git repo): $dest" >&2; exit 1; }

# Refuse to sync into anything but the intended public repo. This is the guard
# that keeps a mistyped path from clobbering the wrong tree.
origin="$(git -C "$dest" remote get-url origin 2>/dev/null || true)"
case "$origin" in
  *Senzing/senzing-bootcamp-claude-plugin*) : ;;
  *) echo "Refusing: '$dest' origin is '$origin', not Senzing/senzing-bootcamp-claude-plugin." >&2
     exit 1 ;;
esac

# Never sync into the dev repo itself.
if [ "$(cd "$here" && pwd)" = "$(cd "$dest" && pwd)" ]; then
  echo "Refusing: source and destination are the same directory." >&2; exit 1
fi

command -v rsync >/dev/null 2>&1 || { echo "rsync is required but not found." >&2; exit 1; }

echo "Source (dev):    $here"
echo "Dest (public):   $dest"
echo "Public origin:   $origin"
echo "Public branch:   $(git -C "$dest" branch --show-current 2>/dev/null || echo '(detached)')"
echo

# --- Propagate the allowlisted paths (mirror, incl. deletions, scoped) ------ #
# rsync -a --delete makes each destination path an exact mirror of its source,
# so files removed in dev are removed in public. Deletion is scoped to these
# paths ONLY — the public repo's .github/, .claude/, .vscode/, LICENSE, and
# .gitignore are never in scope and are left exactly as they are.
# `.pytest_cache/` matters as much as `__pycache__/`: pytest writes a self-ignoring
# `.pytest_cache/.gitignore` containing `*`, so a copied cache never shows up in the
# public repo's `git status` — which is the review step below. Excluding it here is the
# only place it can be caught.
excludes=(--exclude='__pycache__/' --exclude='*.pyc' --exclude='.pytest_cache/')

echo "=== Mirroring plugins/ (minus __pycache__ / *.pyc / .pytest_cache) ==="
rsync -a --delete "${excludes[@]}" "$here/plugins/" "$dest/plugins/"

echo "=== Mirroring .claude-plugin/ (marketplace.json) ==="
rsync -a --delete "$here/.claude-plugin/" "$dest/.claude-plugin/"

# `docs/` is mirrored as a USER-FACING directory, but the dev repo keeps TWO
# maintainer-only files in it: `docs/FAMILY_WORKFLOW.md`, the family-wide normative
# workflow (#111) — which names private development repositories a bootcamper has no
# access to — and `docs/development.md`, the development-loop index
# (`/feedback-to-issues`, `/implement-github-issue`, `/dry-run`, `/propagate-to-public`, …).
# Every skill it names is excluded from this mirror, so publishing it hands users a
# list of commands their install does not have. It reached the public working tree
# once (2026-08-16) precisely because "docs/ is user-facing" was a convention stated
# in the manifest rather than a rule enforced here.
echo "=== Mirroring docs/ (user-facing install docs, minus the maintainer pages) ==="
# The leading slash anchors each pattern to the transfer root, so these exclude exactly
# `docs/development.md` and `docs/FAMILY_WORKFLOW.md`, not some future `docs/*/development.md`.
# ⛔ Both exclusions are pinned by `tests/test_maintainer_docs_stay_out_of_public.py`: until
# #111 nothing asserted either of them, and the sibling guard says in its own docstring that
# it does not cover "the exclusions inside the propagated roots".
# ⛔ Keep this invocation on ONE line. `tests/test_maintainer_tooling_stays_out_of_public.py`
# parses the mirror's sources with `[^\n]*?`, which refuses to cross a newline, so wrapping it
# for readability makes that guard stop seeing this root -- it fails loudly, which is the right
# direction, but the fix is to keep the line rather than to widen the parser.
rsync -a --delete --exclude='/development.md' --exclude='/FAMILY_WORKFLOW.md' "$here/docs/" "$dest/docs/"

echo "=== Copying README.md ==="
rsync -a "$here/README.md" "$dest/README.md"

# --- Rewrite self-references (dev slug -> public slug) --------------------- #
# Only this plugin repo's own slug and the marketplace owner name are rewritten,
# so the published files point users at the Senzing repo. The two slugs differ in
# BOTH owner and name: the dev repo carries a `-development` suffix the public one
# does not, so SLUG_OLD MUST stay the suffixed string. Left unsuffixed it still
# matches -- as a PREFIX -- and publishes the broken Senzing/...-development. The
# separate docktermj/senzing-bootcamp-free-data repo is intentionally left
# untouched (different repo name, so its slug never matches). Idempotent: rsync
# re-copies the docktermj-flavored source each run, then this pass rewrites it
# again.
echo
echo "=== Rewriting self-references (docktermj/...-development -> Senzing) ==="
python3 - "$dest" <<'PY'
import os, sys
dest = sys.argv[1]
SLUG_OLD = "docktermj/senzing-bootcamp-claude-plugin-development"
SLUG_NEW = "Senzing/senzing-bootcamp-claude-plugin"

targets = [os.path.join(dest, "README.md")]
for sub in ("plugins", ".claude-plugin", "docs"):
    root = os.path.join(dest, sub)
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.endswith((".md", ".json")):
                targets.append(os.path.join(dp, fn))

changed = 0
for f in targets:
    if not os.path.isfile(f):
        continue
    with open(f, encoding="utf-8") as fh:
        s = fh.read()
    t = s.replace(SLUG_OLD, SLUG_NEW)
    if os.path.basename(f) == "marketplace.json":
        t = t.replace('"name": "docktermj"', '"name": "Senzing"')
    if t != s:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(t)
        changed += 1
        print("  rewrote", os.path.relpath(f, dest))
print(f"  ({changed} file(s) rewritten)")
PY

# --- Report (no commit, no push) ------------------------------------------- #
echo
echo "=== Public repo status (review before committing) ==="
git -C "$dest" status --short
echo
echo "Files synced. Nothing committed or pushed — review the diff in:"
echo "  $dest"
echo "then commit/push manually."
