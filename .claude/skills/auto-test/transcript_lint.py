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
                                        [--project PROJECT_DIR]
    transcript_lint.py --selftest

``--project`` is the walked project directory. Only the apparatus check reads it,
for the verbosity preset INV-096 grades the time estimate against; without it that
one item is reported as ungraded rather than missing.
"""
import argparse
import json
import re
import sys
import tempfile
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
#
# ⛔ (INV-030, INV-031) A pattern here matches the RENDERED form, never the
# maintainer's name for it. Three of the five carry a structural alternative
# beside the name-based ones, and a name-based pattern alone is what #734 is:
# "before/after framing" and "step overview" are the names ground-rules.md gives
# the apparatus, not wording the guide is required to reproduce. Unlike a ⛔ gate
# question, which INV-056 pins verbatim, this apparatus is specified by what it
# must convey. A conforming module rendered it as a present-state/end-state pair
# of run-in labels and as a short label line over a numbered list, and both
# name-based patterns reported it missing. The journey map escaped that only
# because it already carried a structural alternative, so the other two are given
# the same kind rather than more synonyms for the name.
#
# ⚠️ The structural forms are deliberately narrow, because every pattern here
# reads in BOTH directions. A loose one does not merely over-pass a content
# module: it manufactures a BREAKING INV-075 against an exempt module whose
# teaching prose happens to be a numbered list — Module 0's "**How it works, step
# by step**" over five numbered stages, in the 2026-10-18 walk. So the pair must
# sit in one paragraph, and the list must follow a short LABEL line (no comma, no
# sentence), not any line at all.
_STATUS = "[✅🔄⬜]"
#: A run-in bold label holding one of ``words``, as the guide writes "**Where you are:**".
_LABEL = r"\*\*[^*\n]{{0,44}}\b(?:{words})\b[^*\n]{{0,44}}\*\*"
#: Text that never crosses a blank line, so a label pair is read within one paragraph.
_SAME_PARAGRAPH = r"(?:[^\n]|\n(?!\s*\n)){0,600}?"
_PRESENT_STATE = (r"where you are|where you'?re starting|right now|currently|today"
                  r"|starting point|before")
_END_STATE = (r"by the end|by the time|at the end|end state|after"
              r"|(?:when|once) (?:you|we)(?:'re| are) done")
#: A short label line — "**Steps**", "## Steps" — directly over three numbered items.
_LABELED_LIST = (r"^[ \t]*(?:\*\*|\#{1,6}[ \t]*)[A-Za-z][\w' \t-]{0,22}\**:?[ \t]*\n"
                 r"[ \t]*1[.)][ \t]+\S[^\n]*\n[ \t]*2[.)][ \t]+\S[^\n]*\n[ \t]*3[.)][ \t]+\S")
APPARATUS = {
    "journey map": re.compile(
        r"(?im)journey map"
        r"|^[^\w\n]*your journey[^\w\n]*$"
        rf"|^[ \t]*{_STATUS}[^\n]*\n[ \t]*{_STATUS}"),
    "before/after": re.compile(
        r"(?i)\bbefore\s*(?:/|and|→|->)\s*after\b"
        "|" + _LABEL.format(words=_PRESENT_STATE)
        + _SAME_PARAGRAPH + _LABEL.format(words=_END_STATE)),
    "step overview": re.compile(
        r"(?im)step overview|what we'?ll (?:do|cover)"
        rf"|{_LABELED_LIST}"),
    "time estimate": re.compile(
        r"(?im)^[^\w\n]*⏱"
        r"|\b(?:roughly|about|takes|approx\w*)\s+\d+(?:\s*(?:-|–|to)\s*\d+)?\s*minutes?\b"
        r"|\bhard to estimate\b"),
    "model nudge": re.compile(r"(?i)\b(?:opus|sonnet|haiku)\s*5?\b.*\beffort\b|switch (?:to|the) model"),
}

#: Where the bootcamp keeps the preferences the guide writes, under the project directory.
PREFERENCES = Path("config") / "bootcamp_preferences.yaml"
#: ``verbosity: minimal`` or a ``verbosity:`` block with a ``preset:`` line. Read with a
#: regex rather than a YAML parser: this harness is stdlib-only, and the one value needed
#: here does not justify making PyYAML a dependency of the lint (INV-108's spirit).
_PRESET = re.compile(
    r"(?m)^verbosity:[ \t]*(?:([A-Za-z]+)[ \t]*$"
    r"|\n(?:[ \t]+[^\n]*\n)*?[ \t]+preset:[ \t]*([A-Za-z]+))")

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


def verbosity_preset(project):
    """The project's verbosity preset, lowercased, or None when it cannot be read.

    None is "unknown", never "standard": a caller that cannot tell which preset was
    in force must say so rather than grade against a guess.
    """
    if not project:
        return None
    try:
        text = (Path(project) / PREFERENCES).read_text(encoding="utf-8",
                                                       errors="replace")
    except OSError:
        return None
    match = _PRESET.search(text)
    if not match:
        return None
    return (match.group(1) or match.group(2)).lower()


def check_apparatus(turns, phase, project=None):
    """INV-075/078 exempt preparation and Module 0; content modules require it.

    ``project`` is the bootcamper's project directory, whose
    ``config/bootcamp_preferences.yaml`` carries the verbosity preset. The time
    estimate is the one apparatus item a preset can switch off: INV-096 requires it
    **suppressed entirely under ``minimal``** and kept to one line under ``concise``
    (INV-011/INV-012). Grading it without reading the preset reported a breach
    against a rule the guide was following — the seeded dry-run fixture sets
    ``minimal``, the guide suppressed the estimate, and this check called it missing
    (#734).

    ⚠️ **An unreadable preset is a coverage limit, not a pass and not a finding.**
    With no project directory the estimate's absence is reported at INFO, saying it
    was not graded and why. Three states, not two: required and absent (WATCH),
    suppressed by ``minimal`` (silent), ungraded (INFO).

    ⛔ **What this does NOT check (INV-096):** that an estimate shown under
    ``minimal`` is a breach of the same rule, which it is, nor the estimate's line
    count under ``concise``. Both are gaps, stated so that a clean content lint is
    not read as "INV-096 holds".
    """
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
        preset = verbosity_preset(project)
        for name, pattern in APPARATUS.items():
            if pattern.search(joined):
                continue
            if name == "time estimate":
                if preset == "minimal":
                    continue          # INV-096 requires its absence here.
                if preset is None:
                    where = (f"{Path(project) / PREFERENCES}" if project
                             else "no project directory was given (--project)")
                    out.append(_finding(
                        INFO, "INV-096-estimate-ungraded", 0,
                        "content module showed no time estimate and the verbosity "
                        f"preset could not be read from {where}; INV-096 suppresses "
                        "the estimate under `minimal`, so this is ungraded rather "
                        "than missing"))
                    continue
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


def lint(turns, phase=None, project=None):
    findings = []
    for check in CHECKS:
        findings.extend(check(turns))
    if phase:
        findings.extend(check_apparatus(turns, phase, project))
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
# status list and arrow label from the 2026-10-14 walk, and — carrying no apparatus
# name at all — the present-state/end-state pair and the "Steps" list the guide
# rendered at two module openings in the 2026-10-18 walk (#734).
_APPARATUS_RENDERINGS = (
    ("time estimate", "⏱️ Roughly 15-30 minutes, depending on download/install speed."),
    ("time estimate", "⏱️ Roughly 20–45 minutes. It varies with your machine."),
    ("time estimate", "This is hard to estimate for this module."),
    ("journey map", "**Your journey**"),
    ("journey map", "✅ Bootcamp preparation\n🔄 **SDK setup**\n⬜ System verification"),
    ("before/after", "**Before → After:** You have a project directory but no SDK."),
    ("before/after",
     "**Where you are:** entity resolution is proven on a few synthetic records, but "
     "you haven't seen it work visually. **By the end:** you'll have watched Senzing's "
     "Truth Set resolve in an interactive web app on your machine."),
    ("step overview",
     "**Steps**\n1. Get the Truth Set from the Senzing server.\n"
     "2. Register its data sources and load it.\n"
     "3. Build and run the visualization in Java.\n"
     "4. Explore it with a guided tour.\n"
     "5. Clean up: stop the web service and remove the Truth Set data."),
    ("step overview", "**What we'll do:**\n1. A quick data-privacy reminder."),
)

#: Apparatus a content module must show whatever the verbosity preset says. The time
#: estimate is not here: INV-096 suppresses it under `minimal`, so it is graded
#: against the project's preset instead.
_ALWAYS_REQUIRED = ("journey map", "before/after", "step overview", "model nudge")

# Text from the apparatus-exempt stretches that must NOT raise INV-075. The
# preparation close is one status line, not a journey map
# (bootcamp-preparation/SKILL.md). The last two are the shapes #734's structural
# fallbacks must not reach, both taken from the exempt stretch of the 2026-10-18
# walk: Module 0's teaching list under a sentence heading, and a 👉 question's
# numbered options. A fallback loose enough to match either would not merely
# over-pass a content module — it would report a breach against a conforming one.
_EXEMPT_PHASE_TEXT = (
    "✅ Bootcamp preparation complete",
    "✅ Bootcamp preparation complete — Path: Core (all 11 modules) — "
    "Detail level: minimal → Next: Entity Resolution Concepts",
    "**How it works, step by step**\n1. Ingestion and standardization\n"
    "2. Candidate selection (blocking or indexing)\n3. Comparison and scoring\n"
    "4. Classification: match, no match, or possible match\n5. Entity clustering",
    "\U0001f449 **What does a well-designed entity resolution system do with this "
    "record? Reply with a number:**\n\n"
    "1. Attach it to whichever of the three people looks most similar.\n"
    "2. Create a new, fourth entity for it.\n"
    "3. Mark it as ambiguous and hold it as a possible match.",
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

    # The plugin's own renderings of the apparatus (#658, #734). Each must be
    # recognized, or a content module that shows it is reported as missing it.
    for name, sample in _APPARATUS_RENDERINGS:
        if not APPARATUS[name].search(sample):
            failures.append(f"{name} pattern missed the plugin's rendering {sample!r}")
    bare = ["Starting the module now."]
    missing = {f["message"] for f in lint(bare, phase="content")
               if f["code"] == "INV-028-apparatus-missing"}
    for name in _ALWAYS_REQUIRED:
        if f"content module showed no {name}" not in missing:
            failures.append(f"a content turn with no {name} was not flagged")
    # The time estimate is graded against the project's verbosity preset (#734):
    # required under `standard`, suppressed by INV-096 under `minimal`, and ungraded
    # — neither a pass nor a finding — where no preset can be read.
    with tempfile.TemporaryDirectory() as scratch:
        for preset, code in (("standard", "INV-028-apparatus-missing"),
                             ("minimal", None),
                             (None, "INV-096-estimate-ungraded")):
            project = None
            if preset:
                project = Path(scratch) / preset
                (project / PREFERENCES.parent).mkdir(parents=True, exist_ok=True)
                (project / PREFERENCES).write_text(
                    f"path: core\nverbosity:\n  preset: {preset}\n", encoding="utf-8")
            got = sorted({f["code"] for f in check_apparatus(bare, "content", project)
                          if "time estimate" in f["message"]})
            if got != ([code] if code else []):
                failures.append(
                    f"a content turn with no time estimate, under preset {preset!r}, "
                    f"produced {got} rather than {[code] if code else []}")

    # A single status line is not a journey map, and an ordinary numbered list is not
    # a step overview, so the exempt stretches stay clean.
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
    checks = (len(expected) + 4 + len(_APPARATUS_RENDERINGS) + len(_ALWAYS_REQUIRED)
              + 3 + len(_EXEMPT_PHASE_TEXT))
    print(f"selftest: all {checks} checks behave — each fires on bad "
          "input and stays silent on good input")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", nargs="?")
    ap.add_argument("--phase", choices=("preparation", "module0", "content"))
    ap.add_argument("--project", default=None,
                    help="the walked project directory, whose "
                         "config/bootcamp_preferences.yaml holds the verbosity "
                         "preset INV-096 grades the time estimate against")
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
    findings = lint(turns, args.phase, args.project)
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        render(findings, len(turns))
    return 1 if any(f["severity"] == BREAKING for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
