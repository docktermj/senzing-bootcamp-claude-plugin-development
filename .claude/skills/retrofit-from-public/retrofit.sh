#!/usr/bin/env bash
set -euo pipefail
# Retrofit changes made in the PUBLIC access repo (Senzing/senzing-bootcamp-claude-plugin)
# back into this DEVELOPMENT repo. Files only — this never commits or pushes.
#
# It is the inverse of propagate-to-public: it copies the propagated content back
# and applies the INVERSE owner rewrite (Senzing -> docktermj). Because the
# rewrite is a clean inverse, running this when the repos are already in sync
# produces NO change in the dev tree. See SKILL.md for the manifest and rationale.
#
# Usage: retrofit.sh [path-to-public-repo]
#   Default public repo: ~/senzing.git/senzing-bootcamp-claude-plugin

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # dev repo root (destination)
default_src="$HOME/senzing.git/senzing-bootcamp-claude-plugin"
src="${1:-$default_src}"

# --- Safety guards --------------------------------------------------------- #
[ -d "$here/plugins/senzing-bootcamp" ] || {
  echo "This doesn't look like the dev repo: $here" >&2; exit 1; }
[ -d "$src/.git" ] || {
  echo "Public repo not found (or not a git repo): $src" >&2; exit 1; }

# Refuse to retrofit from anything but the intended public repo.
origin="$(git -C "$src" remote get-url origin 2>/dev/null || true)"
case "$origin" in
  *Senzing/senzing-bootcamp-claude-plugin*) : ;;
  *) echo "Refusing: source '$src' origin is '$origin', not Senzing/senzing-bootcamp-claude-plugin." >&2
     exit 1 ;;
esac

# Never retrofit from the dev repo into itself.
if [ "$(cd "$here" && pwd)" = "$(cd "$src" && pwd)" ]; then
  echo "Refusing: source and destination are the same directory." >&2; exit 1
fi


# Warn on a dirty dev tree: its uncommitted edits show up in the comparison below.
if ! git -C "$here" diff --quiet -- plugins .claude-plugin docs README.md \
   || ! git -C "$here" diff --cached --quiet -- plugins .claude-plugin docs README.md; then
  echo "WARNING: dev working tree has uncommitted changes in the compared paths;" >&2
  echo "         they are compared as they stand, so the report includes them." >&2
fi

echo "Source (public): $src"
echo "Public origin:   $origin"
echo "Public branch:   $(git -C "$src" branch --show-current 2>/dev/null || echo '(detached)')"
echo "Dest (dev):      $here"
echo

# --- REPORT the allowlisted paths; never write into the dev tree ------------ #
# ⛔ (INV-312) This script COPIED until #54. It now compares and reports, writing nothing:
# under the issue-driven workflow a public-repo change becomes a GitHub issue the
# maintainer reads, not an edit that arrives in the working tree.
#
# ⚠️ That also removes the hazard the old step 5 existed for. `tests/` is not in the
# public mirror and cannot come back, so a retrofitted prose edit landed in a shipped
# file while the dev-only test quoting that sentence kept asserting the old wording.
# Measured 2026-08-16 on `2223961`, the British->US spelling corrections: a CORRECT
# edit, faithfully copied, left 12 failed / 2730 passed -- ten of them that desync.
# Nothing is copied now, so nothing desyncs; the reconciliation is done deliberately
# by whoever implements the filed issue.
#
# NO --delete and no writes at all. A dev file missing from public is reported, never
# removed: it may be a dev addition not yet propagated. Governance files (.github/,
# LICENSE, .vscode/, .gitignore, public .claude/settings.json) stay out of scope by
# construction -- they are never read from the source.
differs=0
errors=0
report_path() {
  # $1 = relative path under both repos. Prints a per-file diff summary; writes nothing.
  #
  # ⚠️ (#191) `diff` exits 0 when the trees match, 1 when they differ, and 2 or more when it
  # could not compare them. Under `set -euo pipefail` a bare non-zero `diff`, or a listing
  # pipeline that carries its status, ENDS THE SCRIPT: until #191 the first differing path was
  # the last one reported, so the report only finished when there was nothing to report.
  # Capture the status with `|| status=$?`, and end the listing with `|| true`, which also
  # covers `head` closing the pipe on a long listing. Neither may be dropped.
  local rel="$1" status=0
  if [ ! -e "$src/$rel" ]; then
    echo "  (absent in public)      $rel"
    return 0
  fi
  diff -rq "$src/$rel" "$here/$rel" >/dev/null 2>&1 || status=$?
  case "$status" in
    0) echo "  same                    $rel"
       return 0 ;;
    1) echo "  DIFFERS                 $rel"
       differs=$((differs + 1)) ;;
    *) echo "  ERROR                   $rel   (diff could not compare it: exit $status)"
       errors=$((errors + 1)) ;;
  esac
  diff -rq "$src/$rel" "$here/$rel" 2>&1 | sed 's/^/      /' | head -40 || true
}

echo "=== Comparing the propagated paths (read-only) ==="
for rel in plugins .claude-plugin docs README.md; do
  report_path "$rel"
done
echo
echo "=== Public commits since the newest tag, which is what a filed issue describes ==="
git -C "$src" log --oneline "$(git -C "$src" describe --tags --abbrev=0 2>/dev/null || echo HEAD)"..HEAD 2>/dev/null | sed 's/^/  /' || true

echo
# The stop sign is written as its UTF-8 bytes: plain `echo` expands no escapes, so the
# old `\u` form printed literally (#191), and octal `printf` works in bash 3.2 too.
stop_sign=$(printf '\342\233\224')
if [ "$errors" -gt 0 ]; then
  echo "$differs propagated path(s) differ; $errors could not be compared (ERROR above). $stop_sign NOTHING WAS WRITTEN."
else
  echo "$differs propagated path(s) differ. $stop_sign NOTHING WAS WRITTEN."
fi
echo "File one issue per coherent change (see SKILL.md); search the tracker first so a"
echo "change already absorbed or already filed does not get a second issue."

# --- The inverse slug rewrite is NOT applied here any more ------------------ #
# ⛔ Until #54 this rewrote `Senzing/senzing-bootcamp-claude-plugin` back to
# `docktermj/senzing-bootcamp-claude-plugin-development` across the copied files --
# a write into the dev tree, and the last one this script performed.
#
# ⚠️ The transform itself is unchanged and still REQUIRED: whoever implements a filed
# issue must apply it by hand to any text they bring across, or the dev repo ends up
# carrying public self-references. `propagate.sh` holds the forward direction and the
# two must still agree. What changed is only WHO applies it and WHEN -- deliberately,
# in the issue's implementation, rather than automatically in a sync.
#
# The comparison above therefore reports files as DIFFERING when the only difference is
# the slug. That is correct and not noise: it is the change a filed issue must describe.

echo "=== In dev but not in public (NOT deleted — review manually) ==="
missing=0
while IFS= read -r rel; do
  case "$rel" in */__pycache__/*|*.pyc) continue ;; esac
  if [ ! -e "$src/$rel" ]; then
    echo "  $rel"
    missing=$((missing + 1))
  fi
done < <(cd "$here" && git ls-files plugins .claude-plugin docs README.md)
[ "$missing" -eq 0 ] && echo "  (none)"

# --- Report only (#54): nothing was copied, applied, committed or pushed --- #
echo
echo "This was a report. The dev working tree was compared, not changed, and nothing was"
echo "committed or pushed; a filed issue carries any change into this repo."

if [ "$errors" -gt 0 ]; then
  echo "$errors propagated path(s) could not be compared; the report above is incomplete." >&2
  exit 1
fi
exit 0
