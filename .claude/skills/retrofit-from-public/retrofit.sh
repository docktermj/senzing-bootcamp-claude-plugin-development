#!/usr/bin/env bash
set -euo pipefail
# Report what changed in the PUBLIC access repo (Senzing/senzing-bootcamp-claude-plugin)
# since it last received a propagation from this DEVELOPMENT repo. Report only -- this
# writes nothing into the dev tree and never commits or pushes. See SKILL.md.
#
# It compares public against a BASELINE: the last-propagated dev tag, rebuilt by running
# that tag's own propagate.sh into a throwaway destination (#202). Comparing against dev's
# current tree instead made every unpropagated dev change, and every file carrying the dev
# slug, read as a public edit.
#
# Usage: retrofit.sh [--base <dev-tag>] [path-to-public-repo]
#   Default public repo: ~/senzing.git/senzing-bootcamp-claude-plugin
#   Default baseline:    the dev tag named like public's newest tag. --base names it
#                        instead, for the window after a propagation is committed in
#                        public but before public is tagged.

usage="Usage: retrofit.sh [--base <dev-tag>] [path-to-public-repo]"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # dev repo root
default_src="$HOME/senzing.git/senzing-bootcamp-claude-plugin"
base_tag=""
src=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --base)
      [ "$#" -ge 2 ] && [ -n "$2" ] || { echo "--base needs a dev tag. $usage" >&2; exit 2; }
      base_tag="$2"; shift 2 ;;
    --base=*)
      base_tag="${1#--base=}"
      [ -n "$base_tag" ] || { echo "--base needs a dev tag. $usage" >&2; exit 2; }
      shift ;;
    -h|--help) echo "$usage"; exit 0 ;;
    --) shift; [ "$#" -eq 0 ] || { src="$1"; shift; }
        [ "$#" -eq 0 ] || { echo "Too many arguments. $usage" >&2; exit 2; }
        break ;;
    -*) echo "Unknown option '$1'. $usage" >&2; exit 2 ;;
    *) [ -z "$src" ] || { echo "Too many arguments. $usage" >&2; exit 2; }
       src="$1"; shift ;;
  esac
done
src="${src:-$default_src}"

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

# --- Choose the baseline tag (#202) ---------------------------------------- #
# ⚠️ Every way of having no baseline aborts HERE, before anything is printed, so a run
# never shows half a report taken against nothing. Each message names the tag and --base.
public_tag="$(git -C "$src" describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$base_tag" ]; then
  tag="$base_tag"; chosen="named by --base"
else
  [ -n "$public_tag" ] || {
    echo "No baseline: public repo '$src' has no tag, so there is no last-propagated dev tag" >&2
    echo "to compare it against. Name that dev tag with --base <dev-tag>." >&2; exit 1; }
  tag="$public_tag"; chosen="public's newest tag"
fi
if ! git -C "$here" rev-parse -q --verify "refs/tags/$tag^{commit}" >/dev/null 2>&1; then
  if [ -n "$base_tag" ]; then
    echo "No baseline: --base names '$tag', which is not a tag in the dev repo ($here)." >&2
    echo "Pass an existing dev tag (see git tag -l) with --base <dev-tag>." >&2
  else
    echo "No baseline: public's newest tag is '$tag', but the dev repo has no tag of that name." >&2
    echo "Name the last-propagated dev tag with --base <dev-tag>." >&2
  fi
  exit 1
fi
propagate_rel=".claude/skills/propagate-to-public/propagate.sh"
git -C "$here" cat-file -e "refs/tags/$tag:$propagate_rel" 2>/dev/null || {
  echo "No baseline: dev tag '$tag' carries no $propagate_rel, so what it propagated" >&2
  echo "cannot be rebuilt. Name a later dev tag with --base <dev-tag>." >&2; exit 1; }

# --- Build the baseline: the tag as ITS OWN propagate.sh publishes it ------- #
# ⛔ (INV-300) Neither script copies the other's rewrite or `docs/` exclusions: the tag's own
# propagate.sh applies them, so the paths, exclusions and slug rewrite are exactly what that
# release published -- including any an older release lacked. Its tool check stands in for
# one here, so a missing mirror tool or python3 aborts through it, before any comparison.
# ⛔ (INV-312) Everything is built under a `mktemp -d` directory outside the dev tree: the tag
# comes out through `git archive`, never a checkout, and the trap removes the directory on
# every exit, an abort included.
tmp="$(mktemp -d "${TMPDIR:-/tmp}/retrofit-baseline.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir "$tmp/tag" "$tmp/baseline"
if ! { git -C "$here" archive --format=tar "refs/tags/$tag" | tar -x -f - -C "$tmp/tag"; } 2>"$tmp/err"; then
  echo "No baseline: dev tag '$tag' could not be extracted:" >&2
  sed 's/^/  /' "$tmp/err" >&2
  echo "Name another dev tag with --base <dev-tag>." >&2; exit 1
fi
# The destination passes propagate.sh's guards: a git repo whose origin names the public slug.
base="$tmp/baseline"
git -c init.defaultBranch=baseline init -q "$base" 2>"$tmp/err" \
  && git -C "$base" remote add origin "https://github.com/Senzing/senzing-bootcamp-claude-plugin.git" 2>>"$tmp/err" || {
  echo "No baseline: the throwaway destination for dev tag '$tag' could not be created:" >&2
  sed 's/^/  /' "$tmp/err" >&2; exit 1; }
# Its normal output is suppressed; only a failure, with its stderr, reaches the maintainer.
if ! bash "$tmp/tag/$propagate_rel" "$base" >/dev/null 2>"$tmp/err"; then
  echo "No baseline: the propagate.sh in dev tag '$tag' failed, so its propagation could not be rebuilt:" >&2
  sed 's/^/  /' "$tmp/err" >&2
  echo "Fix what it reports, or name another dev tag with --base <dev-tag>." >&2; exit 1
fi

echo "Source (public): $src"
echo "Public origin:   $origin"
echo "Public branch:   $(git -C "$src" branch --show-current 2>/dev/null || echo '(detached)')"
echo "Dest (dev):      $here"
echo "Baseline:        dev tag $tag ($chosen), as that tag's propagate.sh publishes it"
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
# No deletions and no writes at all. A baseline file missing from public is reported, never
# removed from dev. Governance files (.github/, LICENSE, .vscode/, .gitignore, public
# .claude/settings.json) stay out of scope by construction -- they are never read from the
# source.
differs=0
errors=0
report_path() {
  # $1 = relative path under public and the baseline. Prints a per-file diff summary; writes
  # nothing. ⚠️ The comparison is against "$base", never "$here": dev's current tree holds
  # every change made since the tag, and that is /propagate-to-public's report, not this one.
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
  diff -rq "$src/$rel" "$base/$rel" >/dev/null 2>&1 || status=$?
  case "$status" in
    0) echo "  same                    $rel"
       return 0 ;;
    1) echo "  DIFFERS                 $rel"
       differs=$((differs + 1)) ;;
    *) echo "  ERROR                   $rel   (diff could not compare it: exit $status)"
       errors=$((errors + 1)) ;;
  esac
  diff -rq "$src/$rel" "$base/$rel" 2>&1 | sed 's/^/      /' | head -40 || true
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
# The comparison above does not show slug-only differences. The baseline has already been
# through propagate.sh's forward rewrite, so a file differs only where public changed it.

echo "=== In the last propagation but not in public (NOT deleted — review manually) ==="
# Every file the baseline holds under the propagated paths. The baseline repo has no commits,
# so `--others` lists them all; without `--exclude-standard` no ignore rule hides one.
missing=0
while IFS= read -r -d '' rel; do
  if [ ! -e "$src/$rel" ] && [ ! -L "$src/$rel" ]; then
    echo "  $rel"
    missing=$((missing + 1))
  fi
done < <(git -C "$base" ls-files -z --others -- plugins .claude-plugin docs README.md)
[ "$missing" -eq 0 ] && echo "  (none)"

# --- Report only (#54): nothing was copied, applied, committed or pushed --- #
echo
echo "This was a report. Public was compared against dev tag $tag as propagated; the dev"
echo "working tree was not changed, and nothing was committed or pushed. A filed issue"
echo "carries any change into this repo."

if [ "$errors" -gt 0 ]; then
  echo "$errors propagated path(s) could not be compared; the report above is incomplete." >&2
  exit 1
fi
exit 0
