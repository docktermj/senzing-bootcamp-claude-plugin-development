#!/usr/bin/env bash
# Warn, before a commit, when a skill's SHARED-RULES block has drifted from its user-level twin.
#
# ⛔ This does NOT block the commit. The drift it detects is a documentation defect, not a
# correctness one, and a hook that refuses commits over prose teaches people to bypass it.
# It prints and gets out of the way.
#
# ⚠️ It fires only on `git commit` issued through Claude Code's Bash tool. A commit made in a
# terminal outside a session never reaches this, and an edit to a user-level copy produces no
# repository event at all -- the script itself prints both limits (#128).
set -uo pipefail

payload="$(cat)"
command_line="$(printf '%s' "$payload" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null || true)"

case "$command_line" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

repo="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo .)}"
detector="$repo/.claude/skills/check-skill-drift/skill_drift.py"
[ -f "$detector" ] || exit 0

if ! python3 "$detector" --quiet; then
  echo "⚠️  Committing anyway: SHARED-RULES drift is a documentation defect, not a correctness" >&2
  echo "   one. Run /check-skill-drift for the full report." >&2
fi
exit 0
