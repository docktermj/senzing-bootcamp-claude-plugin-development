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

``--project`` is the walked project directory. The apparatus check reads it for the
verbosity preset INV-096 grades the time estimate against. Without it the time
estimate is reported as ungraded rather than missing.
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

# The module-start detection `dry-run`'s slicer already uses to cut the stretch
# ``check_apparatus`` grades: the module table and each module's banner, read from the
# skill files, matched only on a line of its own (#857 reuses it rather than adding a
# second one).
sys.path.insert(0, str(SKILL_DIR.parent / "dry-run"))
from module_banners import modules as module_table  # noqa: E402
from walk import banner_seen  # noqa: E402  (module_banners puts this directory on the path)

BREAKING, WATCH, INFO = "BREAKING", "WATCH", "INFO"

# Apparatus that content modules must show and the two apparatus-exempt stretches
# must not (INV-075, INV-078 vs INV-028..031, INV-096).
#
# Each pattern matches the plugin's own renderings (#658): the guide heads the
# journey map "Your journey" and marks modules ✅/🔄/⬜, writes "⏱️ Roughly 20–45
# minutes" or "hard to estimate", and may render the label "Before → After". The
# same patterns raise BREAKING INV-075 in the exempt phases, so the journey map
# needs a heading line or a run of two or more status lines: a single status line
# such as "✅ Bootcamp preparation complete" is not a journey map. The table form
# ground-rules.md pins (#852) is matched the same way, as two consecutive table
# rows that each carry a marker, so a header row or a table with no marker (the
# Required/Optional module list Bootcamp preparation may render) is not a map.
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
        rf"|^[ \t]*{_STATUS}[^\n]*\n[ \t]*{_STATUS}"
        rf"|^[ \t]*\|[^\n]*{_STATUS}[^\n]*\n[ \t]*\|[^\n]*{_STATUS}"),
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

#: The note recital's pinned confirm question (`notes.md` Step 3). Options 2, 3 and 4
#: re-present it over a changed note, which `notes.md` says is not a re-ask under
#: INV-006, so ``check_repeat_questions`` never reports it (#842). Its test reads the
#: wording from the shipped Step 3, so a reworded recital fails there.
RECITAL_CONFIRM = "Here's your note — save it as is?"


def load(path):
    """Assistant turns, in order, as the text a Bootcamper would have seen."""
    return load_walk(path)[0]


def load_walk(path, tool_results=False):
    """``(turns, replies)``: the assistant turns, and what the Bootcamper said after each.

    ``turns`` is what ``load`` returns. ``replies[i]`` is the text of the ``bootcamper``
    events ``walk.py`` logged between turn ``i + 1`` and the next turn, joined by a
    newline, or None when the next event the Bootcamper saw was another assistant turn.
    A transcript with no ``bootcamper`` events (one the maintainer answered by hand)
    gives a list of None.

    With ``tool_results=True`` it returns ``(turns, replies, tools)``, where ``tools``
    lists the tool results in the guide's raw stream-json, which ``walk.py`` logs whole
    (#857). Each is a dict: ``after``, the number of turns before it (it falls between
    turn ``after`` and turn ``after + 1``); ``tool`` and ``command``, the name and the
    ``command`` input of the ``tool_use`` it answers (None when unknown or not a
    command); ``is_error``; and ``text``, the result's text. ``turns`` and ``replies``
    are the same either way: a tool result is never text the Bootcamper saw. A
    transcript with no tool-result events gives an empty list.
    """
    turns, replies, tools, uses = [], [], [], {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "bootcamper":
            if turns and isinstance(event.get("text"), str):
                said = event["text"]
                replies[-1] = said if replies[-1] is None else replies[-1] + "\n" + said
            continue
        blocks = (event.get("message") or {}).get("content") or []
        if not isinstance(blocks, list):
            blocks = []
        blocks = [b for b in blocks if isinstance(b, dict)]
        if event.get("type") == "user":
            for block in blocks:
                if block.get("type") == "tool_result":
                    use = uses.get(block.get("tool_use_id"), {})
                    tools.append({"after": len(turns), "tool": use.get("tool"),
                                  "command": use.get("command"),
                                  "is_error": block.get("is_error") is True,
                                  "text": _result_text(block.get("content"))})
            continue
        if event.get("type") != "assistant":
            continue
        for block in blocks:
            if block.get("type") == "tool_use":
                given = block.get("input") or {}
                command = given.get("command") if isinstance(given, dict) else None
                uses[block.get("id")] = {
                    "tool": block.get("name"),
                    "command": command if isinstance(command, str) else None}
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        if text.strip():
            turns.append(text)
            replies.append(None)
    return (turns, replies, tools) if tool_results else (turns, replies)


def _result_text(content):
    """A ``tool_result``'s text: the string itself, or its text blocks joined."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


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


def _outside_quotes_and_fences(text):
    """The lines of ``text`` that are neither blockquoted (``>``) nor in fenced code.

    A blockquote is someone's words recited, such as a note the Bootcamper dictated, and a
    fence is code or a banner; neither is a choice offered to the Bootcamper (#842).
    """
    fence = None
    for line in text.splitlines():
        stripped = line.strip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif stripped.startswith(fence[0] * len(fence)):
                fence = None
            continue
        if fence is not None or stripped.startswith(">"):
            continue
        yield line


def check_or_joined_choices(turns):
    """INV-051: numbered lists, never choices joined by `or`.

    Blockquoted lines and fenced code are skipped: the 2026-10-27 walk recited the
    Bootcamper's note "> Ask the data team: is our claims/policy feed batch or
    streaming?", their own question, and this check reported it as a choice (#842).
    """
    out = []
    # "Would you like X or Y?" in a question line, excluding the one sanctioned
    # trailing form "(respond yes or no)".
    question = re.compile(r"[^\n]*\?\s*$")
    sanctioned = re.compile(r"(?i)\(respond\s+\w+\s+or\s+\w+\)")
    for index, text in enumerate(turns, 1):
        for line in _outside_quotes_and_fences(text):
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


def _question_key(line):
    """A 👉 line's first twelve words, lowercased, letters and spaces only."""
    key = re.sub(r"[^a-z ]", "", line.lower()).strip()
    return " ".join(key.split()[:12])


def _reply_since(replies, start, stop):
    """What the Bootcamper said after turn ``start`` and before turn ``stop`` (1-based)."""
    said = [r for r in (replies or [])[start - 1:stop - 1] if r is not None]
    return "\n".join(said) if said else None


def check_repeat_questions(turns, replies=None):
    """INV-006: nothing re-asked unless the Bootcamper asked for a repeat.

    A 👉 question whose first twelve words match an earlier 👉 question is a repeat. Two
    repeats are not re-asks, and this check reports neither (#842):

    - **A pending question re-presented after a side question.** `ground-rules.md` →
      "Ask-once" says a pending, unanswered question is re-presented verbatim after a
      tangent, and that this is not a re-ask.
    - **The note recital's confirm question** (``RECITAL_CONFIRM``). `notes.md` Step 3
      re-presents it over a changed note and says that is not a re-ask under INV-006.

    **The answer rule.** ``replies`` is ``load_walk``'s second list. A repeat is reported
    only when the Bootcamper's reply to the question's previous asking was an answer, and
    a reply is an answer when it contains no ``?``. A reply that contains a ``?`` is a side
    question, after which re-presenting the pending question is sanctioned. A repeat with
    no reply in between, or with no ``replies`` given at all, is reported, as it was
    before #842: nothing shows the question was left pending by a side question.

    ⚠️ **Known limit.** A reply that both answers the question and asks something new
    ("Option 2. And what's a redo record?") contains a ``?``, so it is read as a side
    question, and a re-ask after it is not reported. A mechanical check cannot tell the
    two apart; only `dry-run` phase 3 observes that case.
    """
    out = []
    seen = {}
    for index, text in enumerate(turns, 1):
        for line in text.splitlines():
            if POINTER not in line:
                continue
            key = _question_key(line)
            if len(key) < 20 or key.startswith(_question_key(RECITAL_CONFIRM)):
                continue
            if key in seen:
                reply = _reply_since(replies, seen[key], index)
                if reply is None or "?" not in reply:
                    why = ("no reply between them" if reply is None
                           else "the reply to it, with no `?`, answered it")
                    out.append(_finding(
                        WATCH, "INV-006-re-asked", index,
                        f"question repeats turn {seen[key]} ({why}): "
                        f"{line.strip()[:80]!r}"))
            seen[key] = index
    return out


# ------------------------------------------- steps a module must not skip (#857)
#
# Required steps a low-effort guide skipped in one run with nothing to notice it (#855):
# the directing step (INV-354) and the worked steer (INV-352). Historical note: Discover's
# step 4a-pairs (INV-357) was a third until #889 removed the step and its check.
# Each check below matches the wording the plugin's own sites pin, and
# each tests/ file that pins a pattern reads it from that site, so a reworded site fails
# there rather than turning these checks silent.
#
# ⛔ A module is graded only once the walk has reached its end: the turn carrying its
# transition 👉, or the turn before the next module's banner. A walk that stops inside a
# module never reports a step it had not yet reached.

#: The pinned directing 👉 of each hands-on module, by state token (`ground-rules.md` →
#: "Directing steps"; the sites are `phase2-data-mapping.md` step 11, `phaseD-validation.md`
#: step 21 and `phase1-query-visualize.md` step 1). ``{source}`` is filled at the site.
DIRECTING_QUESTIONS = {
    "data_quality_mapping": re.compile(
        r"What should each of these columns become in .+?['’]s mapped record\?"),
    "data_processing": re.compile(
        r"How do you expect Senzing to have resolved these records\?"),
    "query_visualize_discover": re.compile(
        r"What do you want to find out about your data\?"),
}
#: The no-site form of the summary's ``**You directed:**`` line. Only Data Quality,
#: Mapping, and Transformation has a site that may never arise (#855's decision).
NO_SITE = re.compile(r"\*\*You directed:\*\*\s*nothing this module\.[^\n]*?"
                     r"so there was no step to hand over\.")
NO_SITE_MODULES = ("data_quality_mapping",)
#: The Act 2 hands-on modules a worked steer applies to (`ground-rules.md` → "Worked steers").
STEER_MODULES = ("data_collection", "data_quality_mapping", "data_processing",
                 "query_visualize_discover")
#: The first line of every worked steer, as `ground-rules.md` → "Worked steers" pins it.
STEER_LINE = "What went wrong:"
#: A module's transition 👉 (`module-completion.md` Step 4), or the graduation offer that
#: stands in for it after the last content module.
TRANSITION = re.compile(
    r"(?i)ready to move on to the next module|would you like to graduate now")
#: A command that builds or runs a program: the tools of `ground-rules.md` →
#: "Building and running a program".
_BUILDS_OR_RUNS = re.compile(r"\b(?:python3?|javac|java|dotnet|cargo|tsc|node)\b")
#: A project file under one of that section's ``src/<dir>`` program directories. The env
#: script under ``src/scripts/`` is not one: every native-Windows call dot-sources it.
_PROGRAM_PATH = re.compile(r"(?:^|[\s'\"=:;(,/\\])src[/\\](?!scripts[/\\])\w")
#: Claude Code's Bash result for a non-zero exit begins "Exit code N".
_EXIT_CODE = re.compile(r"^\s*(?:Error:\s*)?Exit code (-?\d+)")


def _pointer_lines(text):
    return [line for line in text.splitlines() if POINTER in line]


def _asks(turns, pattern):
    """Whether any 👉 line in ``turns`` matches ``pattern``."""
    return any(pattern.search(line) for text in turns for line in _pointer_lines(text))


def module_spans(turns):
    """Each module the walk entered, in order: ``token``, ``name``, ``start``, ``end``.

    ``start`` is the 1-based turn that shows the module's banner, and ``end`` is the
    module's last turn: the first later turn whose 👉 is a transition question, else the
    turn before the next module's banner, else None when the walk ended inside it. The
    banners come from ``module_banners.modules()``, matched by ``walk.banner_seen``, the
    pair `dry-run`'s slicer uses (#857 adds no second module detector).
    """
    table = [m for m in module_table() if m["banner"]]
    spans = []
    for index, text in enumerate(turns, 1):
        shown = next((m for m in table if banner_seen(m["banner"], text)), None)
        current = spans[-1] if spans else None
        if shown and (current is None or current["token"] != shown["token"]):
            if current and current["end"] is None:
                current["end"] = index - 1
            spans.append({"token": shown["token"], "name": shown["name"],
                          "start": index, "end": None})
        elif (current and current["end"] is None
              and any(TRANSITION.search(line) for line in _pointer_lines(text))):
            current["end"] = index
    return spans


def check_directing_steps(turns):
    """INV-354: each hands-on module that ends shows its pinned directing 👉.

    Data Quality, Mapping, and Transformation is excused when its turns carry the no-site
    ``**You directed:**`` form, since its site may never arise. A module the walk did not
    finish is not graded.
    """
    out = []
    for span in module_spans(turns):
        pattern = DIRECTING_QUESTIONS.get(span["token"])
        if pattern is None or span["end"] is None:
            continue
        inside = turns[span["start"] - 1:span["end"]]
        if _asks(inside, pattern):
            continue
        if span["token"] in NO_SITE_MODULES and any(NO_SITE.search(t) for t in inside):
            continue
        out.append(_finding(
            BREAKING, "INV-354-directing-step-missing", span["end"],
            f"{span['name']} (turns {span['start']}-{span['end']}) ended without its "
            f"directing 👉 ({pattern.pattern!r})"))
    return out


def _failed_program_run(tool):
    """Whether a tool result is a failed build or run of a project program."""
    command = tool.get("command") or ""
    if not (_BUILDS_OR_RUNS.search(command) and _PROGRAM_PATH.search(command)):
        return False
    exit_code = _EXIT_CODE.match(tool.get("text") or "")
    return tool.get("is_error") is True or bool(exit_code and exit_code.group(1) != "0")


def check_worked_steers(turns, tools=None):
    """INV-352: an Act 2 module's first failing program run is followed by a worked steer.

    ``tools`` is ``load_walk(path, tool_results=True)``'s third list. In each Act 2
    hands-on module the walk finished, the first tool result that is an error or a
    non-zero exit from building or running a ``src/`` program is reported when no
    later turn of the module carries ``What went wrong:``. WATCH, not BREAKING: a tool
    error is not always generated code failing, and a failure the guide reports in one
    line and does not fix owes no steer. No tool results (a transcript answered by
    hand) means nothing is graded.
    """
    if not tools:
        return []
    out = []
    for span in module_spans(turns):
        if span["token"] not in STEER_MODULES or span["end"] is None:
            continue
        failed = next((t for t in tools
                       if span["start"] <= t["after"] < span["end"]
                       and _failed_program_run(t)), None)
        if failed is None:
            continue
        if any(STEER_LINE in text for text in turns[failed["after"]:span["end"]]):
            continue
        first = (failed.get("text") or "").strip().splitlines()
        out.append(_finding(
            WATCH, "INV-352-steer-missing", failed["after"] + 1,
            f"in {span['name']}, `{failed['command'].strip()[:80]}` failed after turn "
            f"{failed['after']} ({(first[0] if first else 'no output')[:60]!r}) and no "
            f"turn through the module's end (turn {span['end']}) shows a worked steer "
            f"({STEER_LINE!r})"))
    return out


CHECKS = (check_one_pointer_per_turn, check_module_numbers, check_or_joined_choices,
          check_internal_markers, check_repeat_questions, check_directing_steps,
          check_worked_steers)


def lint(turns, phase=None, project=None, replies=None, tools=None):
    """Every check over ``turns``.

    ``replies`` is ``load_walk``'s second list and ``tools`` its third, or None.
    ``project`` is the walked project directory, or None.
    """
    findings = []
    for check in CHECKS:
        if check is check_repeat_questions:
            findings.extend(check(turns, replies))
        elif check is check_worked_steers:
            findings.extend(check(turns, tools))
        else:
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
# rendered at two module openings in the 2026-10-18 walk (#734), and the journey
# map's table form with its count line, as ground-rules.md pins it (#852).
_APPARATUS_RENDERINGS = (
    ("time estimate", "⏱️ Roughly 15-30 minutes, depending on download/install speed."),
    ("time estimate", "⏱️ Roughly 20–45 minutes. It varies with your machine."),
    ("time estimate", "This is hard to estimate for this module."),
    ("journey map", "**Your journey**"),
    ("journey map", "✅ Bootcamp preparation\n🔄 **SDK setup**\n⬜ System verification"),
    ("journey map",
     "| Module | Status |\n|---|---|\n| Bootcamp preparation | ✅ done |\n"
     "| SDK setup | 🔄 you are here |\n| System verification | ⬜ upcoming |\n\n"
     "1 of 3 modules done"),
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
    # #852: the journey map's table header alone, and a module table with no marker.
    "| Module | Status |",
    "| Module | Status |\n|---|---|\n| Bootcamp preparation | Required |\n"
    "| Entity Resolution Concepts | Optional |\n| SDK setup | Required |",
)


def _skipped_step_cases():
    """``(name, should_fire, findings)`` for each #857 check, on a built walk and its control."""
    banner = {m["token"]: m["banner"] for m in module_table()}
    ready = "\U0001f449 **Are you ready to move on to the next module: Data processing?**"
    lookup = ("\U0001f449 **How do you expect Senzing to have resolved these records? Reply "
              "with a number:**")
    processing = [banner["data_processing"], "Loading your records now."]
    collection = [banner["data_collection"], "Running the collector."]
    failed = [{"after": 1, "tool": "Bash", "command": "python3 src/collect/collect_crm.py",
               "is_error": True, "text": "Exit code 1\nKeyError: 'name'"}]
    steer = ("What went wrong: the collector stopped — given away by `KeyError: 'name'`.\n"
             "What the AI was asked to change: read the column it names.")
    cases = [
        ("directing step skipped in a finished module", True,
         check_directing_steps(processing + [ready])),
        ("directing step asked", False, check_directing_steps(processing + [lookup, ready])),
        ("directing step not yet reached", False, check_directing_steps(processing)),
        ("worked steer missing after a failed run", True,
         check_worked_steers(collection + [ready], failed)),
        ("worked steer shown after a failed run", False,
         check_worked_steers(collection + [steer, ready], failed)),
    ]
    return cases


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

    # The answer rule (#842): a repeat after a reply with no `?` is a re-ask; a repeat
    # after a side question re-presents a pending question; the note recital's
    # confirm question is never a re-ask.
    pending = "\U0001f449 **Do you have any other questions before we continue?**"
    asked_twice = [pending, pending]
    for reply, fires in (("Ready to continue.", True), ("What is a redo record?", False)):
        got = any(f["code"] == "INV-006-re-asked"
                  for f in lint(asked_twice, replies=[reply, None]))
        if got != fires:
            failures.append(f"a repeat after the reply {reply!r} was "
                            f"{'not ' if fires else ''}reported")
    recital = f"\U0001f449 **{RECITAL_CONFIRM} Reply with a number:**"
    if lint([recital, recital], replies=["2", None]):
        failures.append("the note recital's re-presented confirm question was reported")

    # A recited note and a fenced block are not choices offered to the Bootcamper.
    for quoted in ("> Ask the data team: is our feed batch or streaming?",
                   "```text\nIs our feed batch or streaming?\n```"):
        if lint([quoted]):
            failures.append(f"quoted or fenced text was read as a choice: {quoted!r}")

    # Steps a module must not skip (#857): each check fires on a module the walk finished
    # without the step, and stays silent once the step is shown, or before the module ends.
    skipped = _skipped_step_cases()
    for name, fires, found in skipped:
        if bool(found) != fires:
            failures.append(f"{name}: {'nothing was' if fires else found} reported")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 1
    checks = (len(expected) + 4 + len(_APPARATUS_RENDERINGS) + len(_ALWAYS_REQUIRED)
              + 3 + len(_EXEMPT_PHASE_TEXT) + 5 + len(skipped))
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

    turns, replies, tools = load_walk(args.transcript, tool_results=True)
    if not turns:
        print(f"no assistant turns found in {args.transcript} — did the walk run?",
              file=sys.stderr)
        return 2
    findings = lint(turns, args.phase, args.project, replies, tools)
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        render(findings, len(turns))
    return 1 if any(f["severity"] == BREAKING for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
