#!/usr/bin/env python3
"""Each module's start banner, read from its skill files, and the analysis slice of a walk.

Phase 3 helper for a **simulated** walk (``phase3-conversational.md`` → "A simulated
Bootcamper"). Two jobs, both offline and zero-token:

* ``banner N`` prints the start banner of module ``N`` in the module table, for
  ``autotest.py --walk --stop-at-banner``. The walk then stops ``--turns`` turns after it.
* ``slice TRANSCRIPT N --out FILE`` cuts a saved walk transcript at module ``N``'s banner
  and writes the part the analysis covers, so ``transcript_lint.py`` grades from the chosen
  module onward and never the fast-forward before it. It prints where the slice starts and
  ends, the modules the walk reached, and the walk's own ``walk_stop`` event.

⛔ **No banner text is written here.** The module list is the table in
``bootcamp-preparation/SKILL.md`` (INV-079), and each banner comes from that module's skill
files: the first banner line in its ``SKILL.md``; else ``MODULE: <TITLE>`` from a
``# Module <id>: <title>`` heading (INV-028 as superseded by INV-079); else the first banner
line in its other files. A hard-coded list would go stale the day a module is renamed, and
the walk would then run to ``--max-turns`` looking for a banner no turn shows.

The analysis for Bootcamp preparation begins at the first turn, so it includes the onboarding
preface. The apparatus-exempt modules (Bootcamp preparation, Entity Resolution Concepts) end
their slice at the next module's banner, because ``transcript_lint.py``'s ``check_apparatus``
reads its whole input as one phase. Graduation is linted with no phase: it is not a numbered
content module, so the content apparatus check does not apply to it.

Usage:
    module_banners.py list
    module_banners.py banner N
    module_banners.py slice TRANSCRIPT.jsonl N --out SLICE.jsonl

Exit codes: ``slice`` exits 3 when the walk never showed module ``N``'s banner, after
printing the modules it did reach; the walk stalled before the analysis began.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
PREPARATION = SKILLS / "bootcamp-preparation" / "SKILL.md"

sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / "auto-test"))
from walk import banner_seen, visible_text  # noqa: E402  (one matcher for stop and slice)

# Three of one non-ASCII glyph, the text, the same three: "🚀🚀🚀  MODULE: X  🚀🚀🚀".
BANNER_LINE = re.compile(r"^\s*([^\x00-\x7f])\1\1\s+(.+?)\s+\1\1\1\s*$")
MODULE_HEADING = re.compile(r"^# Module \w+: (.+?)\s*$")
TABLE_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*`([a-z_]+)`\s*\|\s*([^|]+?)\s*\|")

# Lint phase by state token: identifiers, not banner text.
EXEMPT_PHASES = {"bootcamp_preparation": "preparation",
                 "entity_resolution_concepts": "module0"}
NO_PHASE = {"graduation"}


def _first_banner_line(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        match = BANNER_LINE.match(line)
        if match:
            return match.group(2).strip()
    return None


def banner_from_skill(skill_dir):
    """The start banner a module's skill files define, or None."""
    skill = skill_dir / "SKILL.md"
    found = _first_banner_line(skill)
    if found:
        return found
    for line in skill.read_text(encoding="utf-8").splitlines():
        match = MODULE_HEADING.match(line)
        if match:
            return "MODULE: " + match.group(1).upper()
    for other in sorted(skill_dir.glob("*.md")):
        if other.name != "SKILL.md":
            found = _first_banner_line(other)
            if found:
                return found
    return None


def modules():
    """The module table, in order, each with its skill directory and banner."""
    out = []
    for line in PREPARATION.read_text(encoding="utf-8").splitlines():
        match = TABLE_ROW.match(line)
        if not match:
            continue
        number, name, token, maps_to = match.groups()
        skill_dir = PREPARATION.parent if maps_to == "this module" else SKILLS / maps_to.strip("`")
        out.append({"number": int(number), "name": name, "token": token,
                    "skill_dir": str(skill_dir.relative_to(REPO_ROOT)),
                    "banner": banner_from_skill(skill_dir),
                    "lint_phase": (None if token in NO_PHASE
                                   else EXEMPT_PHASES.get(token, "content"))})
    return out


def module(number):
    for entry in modules():
        if entry["number"] == number:
            return entry
    raise SystemExit(f"no module {number} in {PREPARATION.relative_to(REPO_ROOT)}'s table")


def slice_transcript(lines, number):
    """Cut the walk at module ``number``: (kept lines, summary)."""
    chosen, table = module(number), modules()
    shown = [visible_text(line) for line in lines]
    reached, start, end = [], None, None
    for index, text in enumerate(shown):
        for entry in table:
            if entry["banner"] and banner_seen(entry["banner"], text):
                if entry["name"] not in reached:
                    reached.append(entry["name"])
                if start is None and entry["number"] == number:
                    start = index
                elif (start is not None and end is None and entry["number"] != number
                      and chosen["lint_phase"] in ("preparation", "module0")):
                    end = index
    if chosen["token"] == "bootcamp_preparation":
        start = 0  # analysis from the first turn, onboarding preface included
    stop = None
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "walk_stop":
            stop = event
            break
    summary = {"module": chosen["name"], "banner": chosen["banner"],
               "lint_phase": chosen["lint_phase"], "start_found": start is not None,
               "start_event": start, "end_event": end,
               "modules_reached": reached, "last_module_reached": reached[-1] if reached else None,
               "walk_stop": stop}
    kept = [] if start is None else lines[start:end]
    return kept, summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    one = sub.add_parser("banner")
    one.add_argument("number", type=int)
    cut = sub.add_parser("slice")
    cut.add_argument("transcript", type=Path)
    cut.add_argument("number", type=int)
    cut.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        print(json.dumps(modules(), indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "banner":
        banner = module(args.number)["banner"]
        if not banner:
            print(f"module {args.number}'s skill files define no banner", file=sys.stderr)
            return 2
        print(banner)
        return 0
    lines = [line for line in args.transcript.read_text(
        encoding="utf-8", errors="replace").splitlines() if line.strip()]
    kept, summary = slice_transcript(lines, args.number)
    args.out.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["start_found"] else 3


if __name__ == "__main__":
    sys.exit(main())
