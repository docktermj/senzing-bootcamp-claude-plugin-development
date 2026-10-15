#!/usr/bin/env python3
"""Check a recorded bootcamp transcript against the plugin's interaction invariants.

Deterministic and offline: no model, no judgment, no flake. Reads the
newline-delimited JSON that ``claude -p --output-format stream-json`` writes and
asserts the mechanically checkable half of
``.claude/skills/dry-run/phase3-conversational.md``'s watch list.

Why a linter rather than a judge
--------------------------------
Most of that watch list is countable, not debatable: "exactly one 👉 per turn",
"no `Module 4` in bootcamper-visible text", "no `or` joining numbered choices".
Asking a model whether a transcript "looked right" would turn those into opinions
and reintroduce the flake that makes a 3×/day suite unreadable. Every check here is
a count or a regex over text the Bootcamper actually saw.

⛔ What this does NOT establish
------------------------------
A clean lint is **not** a passed phase 3. ``phase3-conversational.md`` is explicit
that a walk can only show following the files *can* produce correct behavior, and
that an assistant's own compliance is not evidence. This tool inherits that limit
exactly: **findings are trustworthy; a clean run is weak evidence.** It is a
regression net for changes that break a rule outright, not an audit.

Usage:
    transcript_lint.py TRANSCRIPT.jsonl [--phase preparation|module0|content]
    transcript_lint.py --selftest
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

BREAKING, WATCH, INFO = "BREAKING", "WATCH", "INFO"

# Apparatus that content modules must show and the two apparatus-exempt stretches
# must not (INV-075, INV-078 vs INV-028..031, INV-096).
#
# Each pattern matches the plugin's own renderings (#658): the guide heads the
# journey map "Your journey" and marks modules ✅/🔄/⬜, writes "⏱️ Roughly 20–45
# minutes" or "hard to estimate", and may render the label "Before → After". The
# same patterns raise BREAKING INV-075 in the exempt phases, so the journey map
# needs a heading line or a run of two or more status lines: a single status line
# such as "✅ Bootcamp preparation complete" is not a journey map.
_STATUS = "[✅🔄⬜]"
APPARATUS = {
    "journey map": re.compile(
        r"(?im)journey map"
        r"|^[^\w\n]*your journey[^\w\n]*$"
        rf"|^[ \t]*{_STATUS}[^\n]*\n[ \t]*{_STATUS}"),
    "before/after": re.compile(r"(?i)\bbefore\s*(?:/|and|→|->)\s*after\b"),
    "step overview": re.compile(r"(?i)step overview|what we'?ll (?:do|cover)"),
    "time estimate": re.compile(
        r"(?im)^[^\w\n]*⏱"
        r"|\b(?:roughly|about|takes|approx\w*)\s+\d+(?:\s*(?:-|–|to)\s*\d+)?\s*minutes?\b"
        r"|\bhard to estimate\b"),
    "model nudge": re.compile(r"(?i)\b(?:opus|sonnet|haiku)\s*5?\b.*\beffort\b|switch (?:to|the) model"),
}

POINTER = "\U0001f449"  # 👉


def load(path):
    """Assistant turns, in order, as the text a Bootcamper would have seen."""
    turns = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        blocks = (event.get("message") or {}).get("content") or []
        text = "".join(b.get("text", "") for b in blocks
                       if isinstance(b, dict) and b.get("type") == "text")
        if text.strip():
            turns.append(text)
    return turns


def _finding(sev, code, turn, message):
    return {"severity": sev, "code": code, "turn": turn, "message": message}


def check_one_pointer_per_turn(turns):
    """INV-251: a turn MUST NOT contain two or more 👉; INV-225 forbids ending on none.

    ⚠️ Was labeled INV-005 until 2026-08-15. INV-005 is the 👉 *marker* rule in full
    ("Each question to the Bootcamper is preceded by 👉") and says nothing about count,
    so every finding this emitted pointed the maintainer at the wrong invariant. The
    counting logic is unchanged; only the label and the finding code moved.
    (`specs/the-one-question-per-turn-rule-is-registered-nowhere.md`)
    """
    out = []
    for index, text in enumerate(turns, 1):
        count = text.count(POINTER)
        if count > 1:
            out.append(_finding(BREAKING, "INV-251-multi-question", index,
                                f"{count} 👉 in one turn; exactly one is allowed"))
        if count == 1:
            body = _prose_after_question(text)
            if len(body) > 120:
                out.append(_finding(
                    WATCH, "INV-005-not-turn-final", index,
                    f"{len(body)} characters of prose follow the 👉 question and its "
                    f"options; it should end the turn: {body[:70]!r}"))
    return out


def _prose_after_question(text):
    """Substantive prose after the 👉 question, excluding its options list.

    The sanctioned shape is a neutral lead question followed by numbered choices
    (INV-051), so the turn ends on the *list*, not literally on the question mark.
    An earlier version of this check flagged every well-formed choice question in a
    real transcript — the options were the thing it was counting as trailing prose.
    Only text that is neither an option row nor the trailing parenthetical counts.
    """
    tail = text[text.rindex(POINTER):]
    lines = tail.splitlines()[1:]          # drop the question line itself
    keep = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(?:[-*+]|\d+[.)])\s", stripped):      # an option row
            continue
        if re.match(r"^\**\d+\**[.)]?\s*\**", stripped) and len(stripped) < 200:
            continue                                          # **1.** styled option
        if re.match(r"(?i)^\(?respond\b", stripped):          # trailing parenthetical
            continue
        if re.match(r"^[>|`~_\-=]", stripped):                # quote/code/rule
            continue
        keep.append(stripped)
    return " ".join(keep).strip()


def check_module_numbers(turns):
    """INV-079: names, not numbers, in anything the Bootcamper reads."""
    out = []
    pattern = re.compile(r"\bModule\s+\d+\b")
    for index, text in enumerate(turns, 1):
        for hit in set(pattern.findall(text)):
            out.append(_finding(BREAKING, "INV-079-module-number", index,
                                f"{hit!r} shown to the Bootcamper; use the name"))
    return out


def check_or_joined_choices(turns):
    """INV-051: numbered lists, never choices joined by `or`."""
    out = []
    # "Would you like X or Y?" in a question line, excluding the one sanctioned
    # trailing form "(respond yes or no)".
    question = re.compile(r"[^\n]*\?\s*$")
    sanctioned = re.compile(r"(?i)\(respond\s+\w+\s+or\s+\w+\)")
    for index, text in enumerate(turns, 1):
        for line in text.splitlines():
            if POINTER not in line and not question.search(line):
                continue
            stripped = sanctioned.sub("", line)
            if re.search(r"(?i)\b\w+\s+or\s+\w+\s*\?", stripped):
                out.append(_finding(WATCH, "INV-051-or-joined", index,
                                    f"choices joined by `or`: {line.strip()[:90]!r}"))
    return out


def check_apparatus(turns, phase):
    """INV-075/078 exempt preparation and Module 0; content modules require it."""
    out = []
    joined = "\n".join(turns)
    if phase in ("preparation", "module0"):
        for name, pattern in APPARATUS.items():
            match = pattern.search(joined)
            if match:
                out.append(_finding(
                    BREAKING, "INV-075-apparatus-in-exempt-phase", 0,
                    f"{name} shown during {phase}, which is apparatus-exempt: "
                    f"{match.group(0)[:60]!r}"))
    elif phase == "content":
        for name, pattern in APPARATUS.items():
            if not pattern.search(joined):
                out.append(_finding(WATCH, "INV-028-apparatus-missing", 0,
                                    f"content module showed no {name}"))
    return out


def check_internal_markers(turns):
    """Internal directives must never be rendered (ground-rules.md)."""
    out = []
    for index, text in enumerate(turns, 1):
        for marker in ("⛔", "\U0001f6d1"):  # ⛔ 🛑
            if marker in text:
                out.append(_finding(
                    BREAKING, "internal-marker-leaked", index,
                    f"{marker} rendered to the Bootcamper; it is an internal "
                    "directive and must not appear"))
        if "(Internal:" in text:
            out.append(_finding(BREAKING, "internal-marker-leaked", index,
                                "'(Internal:' stage direction rendered"))
    return out


def check_repeat_questions(turns):
    """INV-006: nothing re-asked unless the Bootcamper asked for a repeat."""
    out = []
    seen = {}
    for index, text in enumerate(turns, 1):
        for line in text.splitlines():
            if POINTER not in line:
                continue
            key = re.sub(r"[^a-z ]", "", line.lower()).strip()
            key = " ".join(key.split()[:12])
            if len(key) < 20:
                continue
            if key in seen:
                out.append(_finding(
                    WATCH, "INV-006-re-asked", index,
                    f"question repeats turn {seen[key]}: {line.strip()[:80]!r}"))
            else:
                seen[key] = index
    return out


CHECKS = (check_one_pointer_per_turn, check_module_numbers, check_or_joined_choices,
          check_internal_markers, check_repeat_questions)


def lint(turns, phase=None):
    findings = []
    for check in CHECKS:
        findings.extend(check(turns))
    if phase:
        findings.extend(check_apparatus(turns, phase))
    return findings


def render(findings, turn_count):
    if not findings:
        print(f"transcript: clean across {turn_count} assistant turns "
              "(a clean lint is not a passed phase 3 — see this file's docstring)")
        return
    order = {BREAKING: 0, WATCH: 1, INFO: 2}
    for f in sorted(findings, key=lambda x: (order.get(x["severity"], 9), x["turn"])):
        where = f"turn {f['turn']}" if f["turn"] else "whole walk"
        print(f"[{f['severity']:8}] {f['code']:34} {where:>11}  {f['message']}")
    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))


# ---------------------------------------------------------------------- selftest


_GOOD = ["Nice — a fraud team is exactly the case this is built for.\n\n"
         "\U0001f449 **Which data source would you like to start with?**\n"]
_BAD = [
    "Welcome. \U0001f449 First question?\n\nAnd \U0001f449 a second one?",
    "We'll cover Module 4 next. ⛔ Do not render this.",
    "\U0001f449 Would you like verbose or concise?",
    "\U0001f449 **Which data source would you like to start with?**",
    # Same question again, so the ask-once check has something to catch.
    "\U0001f449 **Which data source would you like to start with?**",
]

# The plugin's own wording for each apparatus item: ground-rules.md's estimate
# example and its no-number form, graduation's en-dash range, the guide's heading,
# status list and arrow label from the 2026-10-14 walk.
_APPARATUS_RENDERINGS = (
    ("time estimate", "⏱️ Roughly 15-30 minutes, depending on download/install speed."),
    ("time estimate", "⏱️ Roughly 20–45 minutes. It varies with your machine."),
    ("time estimate", "This is hard to estimate for this module."),
    ("journey map", "**Your journey**"),
    ("journey map", "✅ Bootcamp preparation\n🔄 **SDK setup**\n⬜ System verification"),
    ("before/after", "**Before → After:** You have a project directory but no SDK."),
)

# Preparation-phase text that must not raise INV-075: the preparation close is one
# status line, not a journey map (bootcamp-preparation/SKILL.md).
_EXEMPT_PHASE_TEXT = (
    "✅ Bootcamp preparation complete",
    "✅ Bootcamp preparation complete — Path: Core (all 11 modules) — "
    "Detail level: minimal → Next: Entity Resolution Concepts",
)


def selftest():
    """Negative control: every check must fire on a transcript built to break it.

    A guard whose docstring claims more than its assertion checks is worse than no
    guard, so this asserts each rule fires on bad input *and* stays silent on good
    input.
    """
    failures = []
    clean = lint(_GOOD)
    if clean:
        failures.append(f"clean transcript produced findings: {clean}")

    expected = {"INV-251-multi-question", "INV-079-module-number",
                "INV-051-or-joined", "internal-marker-leaked", "INV-006-re-asked"}
    codes = {f["code"] for f in lint(_BAD)}
    for code in sorted(expected - codes):
        failures.append(f"{code} did not fire on input designed to break it")

    apparatus = lint(["This module takes about 20 minutes."], phase="preparation")
    if not any(f["code"] == "INV-075-apparatus-in-exempt-phase" for f in apparatus):
        failures.append("apparatus check did not fire in an exempt phase")

    # The plugin's own renderings of the apparatus (#658). Each must be recognized,
    # or a content module that shows it is reported as missing it.
    for name, sample in _APPARATUS_RENDERINGS:
        if not APPARATUS[name].search(sample):
            failures.append(f"{name} pattern missed the plugin's rendering {sample!r}")
    missing = {f["message"] for f in lint(["Starting the module now."], phase="content")
               if f["code"] == "INV-028-apparatus-missing"}
    for name in ("journey map", "before/after", "time estimate"):
        if f"content module showed no {name}" not in missing:
            failures.append(f"a content turn with no {name} was not flagged")
    # A single status line is not a journey map, so the preparation close stays clean.
    for line in _EXEMPT_PHASE_TEXT:
        hits = [f for f in lint([line], phase="preparation")
                if f["code"] == "INV-075-apparatus-in-exempt-phase"]
        if hits:
            failures.append(f"exempt-phase text raised INV-075: {hits[0]['message']}")

    # The turn-final rule was relaxed to let an options list follow the question,
    # because the strict version flagged every well-formed choice question in a real
    # transcript. These two pin the relaxation to exactly that: options are fine,
    # trailing prose is still caught.
    well_formed = ["\U0001f449 **Which track would you like?**\n\n"
                   "1. **Core bootcamp** *(recommended)* — every module, in order\n"
                   "2. **Fast path** — skip the concept modules\n\n"
                   "(respond with a number)"]
    if lint(well_formed):
        failures.append("a well-formed 👉 question with numbered options was flagged")

    trailing = ["\U0001f449 **Which track would you like?**\n\n"
                "1. Core bootcamp\n2. Fast path\n\n"
                "While you think about that, let me explain how entity resolution "
                "works under the hood, because it will matter a great deal later on "
                "and most people find the mental model genuinely surprising at first."]
    if not any(f["code"] == "INV-005-not-turn-final" for f in lint(trailing)):
        failures.append("trailing prose after the options list was not caught")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 1
    checks = (len(expected) + 4 + len(_APPARATUS_RENDERINGS) + 3
              + len(_EXEMPT_PHASE_TEXT))
    print(f"selftest: all {checks} checks behave — each fires on bad "
          "input and stays silent on good input")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", nargs="?")
    ap.add_argument("--phase", choices=("preparation", "module0", "content"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.transcript:
        ap.error("a transcript path is required (or --selftest)")

    turns = load(args.transcript)
    if not turns:
        print(f"no assistant turns found in {args.transcript} — did the walk run?",
              file=sys.stderr)
        return 2
    findings = lint(turns, args.phase)
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        render(findings, len(turns))
    return 1 if any(f["severity"] == BREAKING for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
