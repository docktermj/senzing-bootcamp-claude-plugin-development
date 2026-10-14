#!/usr/bin/env python3
"""The mechanical half of `/release-cycle`: its run state, the stage-1 merge, and its ledger entry.

`SKILL.md` beside this file is the procedure; this helper owns everything a session would
otherwise do by hand and could do twice: which step comes next, what each step runs, which
drafts are one finding, which record a "yes except 3, 7" strikes, which skill files next, and
the run's one `specs/IMPLEMENTED.md` entry. `tests/test_release_cycle.py` exercises it offline.

⛔ **(INV-300) The drafts manifest belongs to `drafts.py`.** This helper reads it through
`drafts.py`'s own `load()` and `open_records()`, rewrites a draft only through its `Locked`,
`split_draft()` and `render()`, and moves a status only by running `drafts.py set` or
`drafts.py record-filed`, so its transition rules apply. Nothing here parses the format itself.

The run directory
=================

`.claude/release-cycle/runs/<run>/`, gitignored, so the run's own state never dirties the tree.
Where a run writes, stage by stage, is stated once, in `SKILL.md` ("Stopping, and the ledger
entry"), and this helper restates none of it (INV-300). It holds `state.json` (this helper's), the stage-1 drafts (`drafts/`, the finding
skills' `--draft <run-dir>`), and the stage-4 drafts in `exercise/drafts/`: `/dry-run` drafts
against a fresh baseline SHA, and a manifest has one baseline, so stage 4 has its own.

The steps
=========

`STEPS` is the order. ``next`` names the first unfinished step, and a step is finished when it
is `done`, `clean` or `skipped`. A finished step is never marked again, so a resumed run never
repeats one: ``mark`` refuses (exit 3). `clean` is a draft step that found nothing; it skips
that stage's build pass (`CLEAN_SKIPS`).

Filing is resumable at the record level as well as the step: `drafts.py` never files a record
that carries an issue number, and ``file-next`` prints a tracker search for each approved,
unfiled record of a skill whose `--file` was started and not finished, because a stop between
`gh issue create` and `drafts.py record-filed` leaves an issue with no number written back.

The merge
=========

``merge-drafts`` groups the `pending` issue records that cite exactly the same `path:line`
sites (``dedupe_key``). The record whose skill comes first in `drafts.SKILLS` (then the lowest
id) is the **primary**; the rest are its **riders**. The primary's body gains one "Found by"
line naming every source, once. A rider stays `pending` until its primary is filed, then
``file-next`` sets it `approved` and records the primary's number on it, so its own skill's
`--file` skips it and its after-filing line names the issue that tracks it. A struck primary
strikes its riders. Groups are kept in `state.json`, so a second ``merge-drafts`` merges
nothing twice. Records whose keys differ but share a line are printed as `OVERLAP` for the
maintainer to settle; same-skill records with one key are merged like any other.

The checkpoint list is numbered once, in `drafts.SKILLS` order then id, and stored with a hash of
each draft. ``verdicts --strike 3,7`` (or ``--strike none``) approves every listed item but
those, and refuses when a draft changed after it was listed or a pending record was not listed:
one yes covers only the records shown in that message (INV-314, 2026-10-13 note).

The held after-filing steps
===========================

Two after-filing steps write tracked files (`AFTER_FILING`): `/feedback-to-issues` Step 9
archives under `feedback/`, and `/delegate-to-mcp-server` Step 9 appends to
`specs/mcp-coverage.jsonl`. Run inside the skill's `--file` at checkpoint A, either would leave
the tree dirty for stage 3's preflight and change `specs/` before it. So ``file-next`` tells the
session to file that skill's records and stop before its after-filing step, and records the hold
in `state.json` (`held`, per stage and skill). Stage 5's `after-filing` step, which comes before
`/review-invariants`, prints for each held step ``drafts.py after <drafts> --skill <skill>`` and
the step to run with its lines; ``after-filed`` records each one as run and refuses it a second
time, so a resumed run never repeats one, and finishes the step once none is left. ``mark``
refuses to finish `after-filing` while a held step has not run.

The ledger entry
================

``ledger`` renders the run's dated entry from `state.json` and both manifests: each step's
outcome, every draft still unresolved, marked **not filed** or **not sent** (INV-317), and every
held after-filing step not yet run, with its lines.
``--write`` puts it below the ledger's format comment, or replaces this run's entry in place,
so a run has one entry however often it stops. ``--withdraw`` removes it when it is exactly what
was written and not yet committed: a resumed run starts with a clean tree, because
`unattended-issue-loop` *(user level)* stops on a dirty one, and `state.json` still holds
everything the entry said.

Usage::

    cycle.py kickoff <runs-root>
    cycle.py init <run-dir> --simulated yes|no [--persona P --module M] --merge yes|no
                  --threshold P [--sha SHA]
    cycle.py next <run-dir>
    cycle.py status <run-dir>
    cycle.py args <run-dir> <step> [--head SHA] [--blueprint PATH]
    cycle.py mark <run-dir> <step> started|done|clean|stopped [--note TEXT] [--sha SHA]
    cycle.py merge-drafts <run-dir> [--stage find|exercise]
    cycle.py verdicts <run-dir> [--stage find|exercise] --strike N,M|none
    cycle.py file-next <run-dir> [--stage find|exercise]
    cycle.py filed <run-dir> <skill> [--stage find|exercise]
    cycle.py after-filed <run-dir> <skill> [--stage find|exercise]
    cycle.py redraft <run-dir> --sha SHA
    cycle.py ledger <run-dir> [--write LEDGER | --withdraw LEDGER]

Exit codes: 0 success, 1 bad input, 3 a refused step or transition, 4 a baseline-SHA mismatch.

Stdlib only; no network and no `gh`. The one git call is ``git show HEAD:`` in ``--withdraw``.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFTS_PY = HERE.parent / "feedback-to-issues" / "drafts.py"


def _load_drafts():
    spec = importlib.util.spec_from_file_location("release_cycle_drafts", DRAFTS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


drafts = _load_drafts()

#: The maintainer's standing refine threshold, chosen 2026-10-13. Shown at kickoff, never assumed.
STANDING_THRESHOLD = 0.7

#: Where a run directory must sit, so it is gitignored (`.gitignore`, #572).
RUNS_PARENT = (".claude", "release-cycle", "runs")

STAGES = ("Kickoff", "Find", "Refine", "Build", "Exercise", "Settle", "Ship")

#: (step, stage number, checkpoint letter or None), in run order.
STEPS = (
    ("kickoff", 0, None),
    ("find-draft", 1, None),
    ("find-merge", 1, None),
    ("checkpoint-a", 1, "A"),
    ("find-file", 1, None),
    ("refine", 2, "B"),
    ("build-loop", 3, None),
    ("build-leftovers", 3, None),
    ("exercise-draft", 4, None),
    ("exercise-merge", 4, None),
    ("checkpoint-c", 4, "C"),
    ("exercise-file", 4, None),
    ("exercise-refine", 4, "B"),
    ("exercise-build-loop", 4, None),
    ("exercise-build-leftovers", 4, None),
    ("after-filing", 5, None),
    ("checkpoint-d", 5, "D"),
    ("blueprint", 5, None),
    ("release", 6, "E"),
    ("manual-test", 6, "E"),
    ("propagate", 6, "E"),
)
STEP_NAMES = tuple(s for s, _, _ in STEPS)
FINISHED = ("done", "clean", "skipped")
OUTCOMES = ("started", "done", "clean", "stopped")

#: A draft step that found nothing skips its stage's build pass.
CLEAN_SKIPS = {
    "find-draft": ("find-merge", "checkpoint-a", "find-file", "refine", "build-loop",
                   "build-leftovers"),
    "exercise-draft": ("exercise-merge", "checkpoint-c", "exercise-file", "exercise-refine",
                       "exercise-build-loop", "exercise-build-leftovers"),
}

#: Steps only their own command may finish, because it checks what finishing means.
OWNED = {
    "find-merge": "merge-drafts", "exercise-merge": "merge-drafts --stage exercise",
    "checkpoint-a": "verdicts", "checkpoint-c": "verdicts --stage exercise",
    "find-file": "filed", "exercise-file": "filed --stage exercise",
}

#: Per stage: (its drafts directory under the run, its draft, merge, checkpoint, file steps).
DRAFT_STAGES = {
    "find": ("", "find-draft", "find-merge", "checkpoint-a", "find-file"),
    "exercise": ("exercise", "exercise-draft", "exercise-merge", "checkpoint-c", "exercise-file"),
}

#: The finding skills stage 1 runs, each in a subagent (stage 4 runs `/dry-run`).
FIND_SKILLS = tuple(s for s in drafts.SKILLS if s != "dry-run")

#: The after-filing steps that write tracked files (`drafts.py` filing step 4 names both): each is
#: held from its skill's `--file` until stage 5, so the tree stays clean for stage 3's preflight.
AFTER_FILING = {
    "feedback-to-issues": "Step 9, `feedback_ledger.py commit` with these lines as its "
                          "`--disposition` arguments, which archives under `feedback/`",
    "delegate-to-mcp-server": "Step 9, `record` once per line, which appends to "
                              "`specs/mcp-coverage.jsonl`",
}

#: The three slash-only skills, followed from their files in the main session.
FOLLOWED = {
    "refine": "refine-github-issue",
    "loop": "unattended-issue-loop",
    "implement": "implement-github-issue",
}

MERGED_MARK = "<!-- release-cycle merged: %s -->"
BLUEPRINT_HEADER = re.compile(r"<!-- blueprint: sha=([0-9a-f]{7,40})\b")


class Refused(Exception):
    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------- state

def state_path(run_dir):
    return Path(run_dir) / "state.json"


def load_state(run_dir):
    path = state_path(run_dir)
    if not path.is_file():
        raise Refused("no run at %s: start one with `cycle.py init`" % run_dir)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") != 1:
        raise Refused("%s is not a format-1 state file" % path)
    return data


def save_state(run_dir, data):
    path = state_path(run_dir)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def outcome(state, step):
    return (state["steps"].get(step) or {}).get("outcome")


def first_unfinished(state):
    for step in STEP_NAMES:
        if outcome(state, step) not in FINISHED:
            return step
    return None


def stage_of(step):
    for name, number, letter in STEPS:
        if name == step:
            return number, letter
    raise Refused("no step %r; the steps are: %s" % (step, ", ".join(STEP_NAMES)))


def label(step):
    number, letter = stage_of(step)
    return "stage %d %s, step %s%s" % (number, STAGES[number], step,
                                       " (checkpoint %s)" % letter if letter else "")


def set_step(state, step, result, note=None, **extra):
    record = {"outcome": result, "at": now()}
    if note:
        record["note"] = note
    record.update({k: v for k, v in extra.items() if v is not None})
    history = state["steps"].get(step, {}).get("history", [])
    previous = state["steps"].get(step)
    if previous:
        history = history + [{k: v for k, v in previous.items() if k != "history"}]
    if history:
        record["history"] = history
    state["steps"][step] = record


def require_turn(state, step):
    """`step` is the first unfinished step, so nothing is skipped and nothing repeated."""
    if outcome(state, step) in FINISHED:
        raise Refused("refused: %s is already %s and is never run again" % (step, outcome(state, step)), 3)
    turn = first_unfinished(state)
    if turn != step:
        raise Refused("refused: %s comes before %s; finish it first (`cycle.py next`)" % (turn, step), 3)


def git_head():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Refused("cannot read HEAD (pass --sha): %s" % exc)
    return out.stdout.strip()


def check_run_dir(run_dir):
    parts = Path(os.path.abspath(run_dir)).parts
    if len(parts) < 4 or tuple(parts[-4:-1]) != RUNS_PARENT:
        raise Refused("a run directory is %s/<run>, which .gitignore covers; got %s"
                      % ("/".join(RUNS_PARENT), run_dir))


# ---------------------------------------------------------------------------- drafts

def stage_dir(run_dir, stage):
    sub = DRAFT_STAGES[stage][0]
    return Path(run_dir) / sub if sub else Path(run_dir)


def manifest(run_dir, stage):
    return drafts.load(stage_dir(run_dir, stage))


def run_drafts(*args):
    result = subprocess.run([sys.executable, str(DRAFTS_PY), *[str(a) for a in args]],
                            capture_output=True, text=True)
    if result.returncode:
        raise Refused("drafts.py %s refused: %s" % (" ".join(str(a) for a in args),
                                                    result.stderr.strip()), 3)
    return result.stdout


def draft_hash(directory, rec):
    return hashlib.sha256((Path(directory) / rec["draft"]).read_bytes()).hexdigest()


def parse_site(site):
    m = drafts.SITE.match(site)
    start = int(m.group("start"))
    return m.group("path"), start, int(m.group("end") or start)


def shared_lines(key_a, key_b):
    """The sites of `key_a` that share a line with a site of `key_b`."""
    out = []
    for a in key_a:
        pa, sa, ea = parse_site(a)
        for b in key_b:
            pb, sb, eb = parse_site(b)
            if pa == pb and sa <= eb and sb <= ea:
                out.append("%s ~ %s" % (a, b))
    return out


def skill_rank(rec):
    return (drafts.SKILLS.index(rec["skill"]), rec["id"])


def groups_of(state, stage):
    return state.setdefault("merges", {}).setdefault(stage, {})


def rider_ids(state, stage):
    return {r: p for p, riders in groups_of(state, stage).items() for r in riders}


STAGE_TITLES = {"find": "stage 1", "exercise": "stage 4"}


def held_of(state, stage):
    return state.setdefault("held", {}).setdefault(stage, {})


def pending_holds(state):
    """(stage, skill) for each held after-filing step not yet run, in stage then `SKILLS` order."""
    out = []
    for stage in DRAFT_STAGES:
        held = (state.get("held") or {}).get(stage) or {}
        out += [(stage, s) for s in drafts.SKILLS if s in held and not held[s].get("run")]
    return out


def add_found_by(directory, primary_id, members):
    """Append the one "Found by" line to the primary's body, once (idempotent by its marker)."""
    ids = ", ".join(m["id"] for m in members)
    mark = MERGED_MARK % ids
    with drafts.Locked(directory):
        data = drafts.load(directory)
        rec = drafts.find(data, primary_id)
        path = Path(directory) / rec["draft"]
        title, body = drafts.split_draft(path.read_text(encoding="utf-8"))
        body = re.sub(r"\n*<!-- release-cycle merged: [^>]*-->\n\*\*Found by:\*\*[^\n]*\n?", "\n", body)
        sources = "; ".join("`/%s` (%s, `%s`)" % (m["skill"], m["source"], m["id"]) for m in members)
        body = body.rstrip("\n") + "\n\n%s\n**Found by:** %s.\n" % (mark, sources)
        path.write_text(drafts.render(rec, body), encoding="utf-8")


def listing(state, data, stage):
    """The numbered checkpoint items: primaries, unmerged issue records and ledger records."""
    riders = rider_ids(state, stage)
    items = [r for r in data["records"] if r["kind"] in ("issue", "ledger") and r["id"] not in riders]
    return sorted(items, key=skill_rank)


# ---------------------------------------------------------------------------- commands

def cmd_kickoff(args):
    root = Path(args.runs_root)
    runs = sorted(p for p in root.glob("*/state.json")) if root.is_dir() else []
    print("standing refine threshold: %s (the maintainer's choice, 2026-10-13); confirm or change it"
          % STANDING_THRESHOLD)
    last = None
    for path in runs:
        state = json.loads(path.read_text(encoding="utf-8"))
        turn = first_unfinished(state)
        print("run %s: %s" % (path.parent.name, "finished" if turn is None else "unfinished, next " + label(turn)))
        last = state
    if last is None:
        print("no earlier run; no start module to recommend past")
    else:
        k = last["kickoff"]
        print("last run's walk: %s" % ("simulated, persona %s, from module %s" % (k["persona"], k["module"])
                                       if k["simulated"] else "not run"))
    return 0


def cmd_init(args):
    check_run_dir(args.run_dir)
    if state_path(args.run_dir).exists():
        raise Refused("refused: %s already has a run; resume it with `cycle.py next`" % args.run_dir, 3)
    simulated = args.simulated == "yes"
    if simulated and not (args.persona and args.module):
        raise Refused("a simulated walk needs --persona and --module: both are the maintainer's answers (INV-333)")
    if not simulated and (args.persona or args.module):
        raise Refused("--persona and --module answer the simulated walk, which --simulated no declines")
    text = args.threshold.strip()
    p = float(text[:-1]) / 100 if text.endswith("%") else float(text)
    if not 0.5 < p <= 1.0:
        raise Refused("the refine threshold is above 0.5 and at most 1.0; got %s" % args.threshold)
    sha = (args.sha or git_head()).strip().lower()
    if not drafts.SHA.match(sha):
        raise Refused("not a commit SHA: %r" % sha)
    Path(args.run_dir).mkdir(parents=True, exist_ok=True)
    state = {
        "format": 1,
        "run": Path(args.run_dir).name,
        "started": now(),
        "baseline_sha": {"find": sha},
        "kickoff": {"simulated": simulated, "persona": args.persona, "module": args.module,
                    "merge": args.merge == "yes", "threshold": p},
        "steps": {},
        "merges": {},
        "listings": {},
        "filing": {},
        "held": {},
        "ledger": None,
    }
    set_step(state, "kickoff", "done", note="answers given at kickoff")
    save_state(args.run_dir, state)
    print("run %s: baseline %s; next %s" % (state["run"], sha, label(first_unfinished(state))))
    return 0


def cmd_next(args):
    state = load_state(args.run_dir)
    led = state.get("ledger")
    turn = first_unfinished(state)
    if turn and led and led.get("written") and not led.get("withdrawn") and not led.get("committed"):
        print("WITHDRAW the entry written at the last stop first: cycle.py ledger %s --withdraw %s"
              % (args.run_dir, led["path"]))
    if turn is None:
        print("FINISHED: every step is done; write the ledger entry if it is not written")
        return 0
    rec = state["steps"].get(turn)
    how = ""
    if rec and rec.get("outcome") == "started":
        how = " (started %s, not finished)" % rec["at"]
    elif rec and rec.get("outcome") == "stopped":
        how = " (stopped %s: %s)" % (rec["at"], rec.get("note") or "no reason recorded")
    print("NEXT %s%s" % (label(turn), how))
    for line in step_args(state, args.run_dir, turn):
        print(line)
    return 0


def cmd_status(args):
    state = load_state(args.run_dir)
    for step in STEP_NAMES:
        rec = state["steps"].get(step) or {}
        print("%-26s %-8s %s" % (step, rec.get("outcome") or "-", rec.get("note") or ""))
    return 0


def follow(key, arguments):
    name = FOLLOWED[key]
    return "FOLLOW ~/.claude/skills/%s/SKILL.md in this session, as /%s %s" % (
        name, name, arguments) if arguments else \
        "FOLLOW ~/.claude/skills/%s/SKILL.md in this session, as /%s with no argument" % (name, name)


def filed_numbers(run_dir, stage):
    data = manifest(run_dir, stage)
    return sorted({r["issue"] for r in data["records"] if r.get("issue")})


def blueprint_line(head, blueprint):
    path = Path(blueprint)
    if not path.is_file():
        return "SKIP: no BLUEPRINT.md at %s" % path
    m = BLUEPRINT_HEADER.search(path.read_text(encoding="utf-8")[:2000])
    if not m:
        return "INVOKE update-blueprint (user level): BLUEPRINT.md has no header SHA"
    sha = m.group(1)
    if head and drafts.same_commit(sha, head):
        return "SKIP: BLUEPRINT.md's header SHA %s is main's head; mark blueprint done" % sha
    return "INVOKE update-blueprint (user level): BLUEPRINT.md's header SHA %s is behind main (%s)" % (
        sha, head or "unknown")


def step_args(state, run_dir, step, head=None, blueprint="BLUEPRINT.md"):
    """What `step` runs, derived from the kickoff answers and the manifests alone."""
    k = state["kickoff"]
    rd = shlex.quote(str(run_dir))
    ex = shlex.quote(str(stage_dir(run_dir, "exercise")))
    me = "python3 .claude/skills/release-cycle/cycle.py"
    loop = follow("loop", "" if k["merge"] else "--no-merge")
    leftovers = follow("implement", "<n>") + ", once per issue the loop's handoff leaves open"
    if step == "kickoff":
        return ["DONE at init: the kickoff answers are in state.json"]
    if step == "find-draft":
        return ["SUBAGENT /%s --draft %s" % (s, rd) for s in FIND_SKILLS] + [
            "then: %s mark %s find-draft done" % (me, rd)]
    if step in ("find-merge", "exercise-merge"):
        return ["RUN %s merge-drafts %s%s" % (me, rd, "" if step == "find-merge" else " --stage exercise")]
    if step in ("checkpoint-a", "checkpoint-c"):
        extra = "" if step == "checkpoint-a" else " --stage exercise"
        return ["SHOW the list `merge-drafts%s` printed, in one message; then" % extra,
                "RUN %s verdicts %s%s --strike <numbers the maintainer struck, or none>" % (me, rd, extra)]
    if step in ("find-file", "exercise-file"):
        extra = "" if step == "find-file" else " --stage exercise"
        return ["RUN %s file-next %s%s, then the skill it names with --file, then `filed`" % (me, rd, extra)]
    if step == "refine":
        return [follow("refine", "--batch --threshold %s" % k["threshold"])]
    if step == "exercise-refine":
        numbers = filed_numbers(run_dir, "exercise")
        if not numbers:
            return ["SKIP: stage 4 filed nothing; mark exercise-refine done"]
        return [follow("refine", "--batch %s --threshold %s" % (" ".join(map(str, numbers)), k["threshold"]))]
    if step in ("build-loop", "exercise-build-loop"):
        return ["CHECK `git status --porcelain` is empty, else mark %s stopped naming the files" % step, loop]
    if step in ("build-leftovers", "exercise-build-leftovers"):
        return [leftovers]
    if step == "exercise-draft":
        if k["simulated"]:
            call = "/dry-run all %s --simulated %s --draft %s" % (k["module"], k["persona"], ex)
        else:
            call = "/dry-run 1,2 --draft %s" % ex
        return ["SUBAGENT %s" % call,
                "then: %s mark %s exercise-draft done --sha <the fresh baseline SHA>" % (me, rd)]
    if step == "after-filing":
        holds = pending_holds(state)
        if not holds:
            return ["SKIP: no after-filing step is held; mark after-filing done"]
        out = []
        for stage, skill in holds:
            extra = "" if stage == "find" else " --stage exercise"
            out += ["RUN python3 .claude/skills/feedback-to-issues/drafts.py after %s --skill %s"
                    % (shlex.quote(str(stage_dir(run_dir, stage))), skill),
                    "THEN /%s's held after-filing step, %s, with the lines it printed"
                    % (skill, AFTER_FILING[skill]),
                    "then: %s after-filed %s %s%s" % (me, rd, skill, extra)]
        return out + ["after these, the next step is checkpoint D: /review-invariants"]
    if step == "checkpoint-d":
        return ["INVOKE /review-invariants"]
    if step == "blueprint":
        return [blueprint_line(head, blueprint)]
    if step == "release":
        return ["INVOKE /release with no argument: it asks the maintainer for the bump"]
    if step == "manual-test":
        return ["ASK the maintainer to run the manual test, and mark its outcome"]
    if step == "propagate":
        return ["INVOKE /propagate-to-public: it stops at the public working tree; the maintainer "
                "commits and pushes it"]
    raise Refused("no step %r" % step)


def cmd_args(args):
    state = load_state(args.run_dir)
    stage_of(args.step)
    head = args.head
    if args.step == "blueprint" and not head:
        try:
            head = subprocess.run(["git", "rev-parse", "main"], capture_output=True, text=True,
                                  check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            head = None
    for line in step_args(state, args.run_dir, args.step, head=head, blueprint=args.blueprint):
        print(line)
    return 0


def cmd_mark(args):
    state = load_state(args.run_dir)
    step, result = args.step, args.outcome
    stage_of(step)
    require_turn(state, step)
    if result in ("done", "clean") and step in OWNED:
        raise Refused("refused: %s is finished by `cycle.py %s`, which checks it" % (step, OWNED[step]), 3)
    if step == "after-filing" and result == "done" and pending_holds(state):
        raise Refused("refused: the held after-filing step of %s has not run; record each with "
                      "`cycle.py after-filed`" % ", ".join("/%s (%s)" % (s, STAGE_TITLES[g])
                                                          for g, s in pending_holds(state)), 3)
    if result == "clean" and step not in CLEAN_SKIPS:
        raise Refused("refused: only a draft step (%s) can be clean" % ", ".join(CLEAN_SKIPS), 3)
    sha = None
    if step in CLEAN_SKIPS and result in ("done", "clean"):
        stage = "find" if step == "find-draft" else "exercise"
        if stage == "exercise":
            if not args.sha:
                raise Refused("exercise-draft needs --sha: stage 4 drafts against a fresh baseline")
            sha = args.sha.strip().lower()
            state["baseline_sha"]["exercise"] = sha
        data = manifest(args.run_dir, stage)
        base = data.get("baseline_sha")
        want = state["baseline_sha"][stage]
        if base and not drafts.same_commit(base, want):
            raise Refused("baseline SHA mismatch: the drafts were made at %s and the run's baseline is %s"
                          % (base, want), 4)
        if not data["records"]:
            result = "clean"
        elif result == "clean":
            raise Refused("refused: %s has %d draft(s), so it is not clean" % (step, len(data["records"])), 3)
    set_step(state, step, result, note=args.note, sha=sha)
    if result == "clean":
        for skipped in CLEAN_SKIPS[step]:
            set_step(state, skipped, "skipped", note="%s found nothing" % step)
    save_state(args.run_dir, state)
    print("%s %s%s" % (step, result, "; skipped " + ", ".join(CLEAN_SKIPS[step]) if result == "clean" else ""))
    turn = first_unfinished(state)
    print("next: %s" % (label(turn) if turn else "nothing; the run is finished"))
    return 0


def cmd_merge_drafts(args):
    state = load_state(args.run_dir)
    stage = args.stage
    _, draft_step, merge_step, check_step, _ = DRAFT_STAGES[stage]
    if outcome(state, draft_step) not in FINISHED:
        raise Refused("refused: %s is not finished, so the drafts are not all in" % draft_step, 3)
    if outcome(state, merge_step) == "skipped":
        raise Refused("refused: %s was skipped (%s)" % (merge_step, state["steps"][merge_step].get("note")), 3)
    directory = stage_dir(args.run_dir, stage)
    groups = groups_of(state, stage)
    data = drafts.load(directory)
    by_id = {r["id"]: r for r in data["records"]}
    grouped = set(groups) | {r for riders in groups.values() for r in riders}
    keyed = {}
    for rec in sorted(data["records"], key=skill_rank):
        if rec["kind"] == "issue" and rec["dedupe_key"]:
            keyed.setdefault(tuple(rec["dedupe_key"]), []).append(rec)
    merged_now = []
    for key, recs in keyed.items():
        primary = next((r for r in recs if r["id"] in groups), None)
        fresh = [r for r in recs if r["id"] not in grouped and r["status"] == "pending"]
        if primary is None:
            if len(fresh) < 2:
                continue
            primary, fresh = fresh[0], fresh[1:]
            groups[primary["id"]] = []
        if not fresh:
            continue
        groups[primary["id"]].extend(r["id"] for r in fresh)
        members = [primary] + [by_id[i] for i in groups[primary["id"]]]
        add_found_by(directory, primary["id"], members)
        merged_now.append(primary["id"])
    data = drafts.load(directory)
    items = listing(state, data, stage)
    state["listings"][stage] = [{"n": n, "id": r["id"], "sha256": draft_hash(directory, r)}
                                for n, r in enumerate(items, 1)]
    if outcome(state, merge_step) not in FINISHED:
        set_step(state, merge_step, "done", note="%d merged group(s)" % len(groups))
    save_state(args.run_dir, state)
    by_id = {r["id"]: r for r in data["records"]}
    print("baseline %s; %d item(s) for checkpoint %s" % (data.get("baseline_sha"), len(items),
                                                          stage_of(check_step)[1]))
    for n, rec in enumerate(items, 1):
        also = groups.get(rec["id"], [])
        found = ", ".join(["/" + rec["skill"]] + ["/" + by_id[i]["skill"] for i in also])
        print("%d. [%s] %s %s: %s" % (n, rec["status"], rec["kind"], rec["id"], rec.get("title") or rec.get("after")))
        print("   found by %s; sites %s; draft %s" % (found, "; ".join(rec["dedupe_key"]) or "(none)",
                                                    Path(directory) / rec["draft"]))
        if also:
            print("   merged: %s ride on it and take its verdict and its issue number" % ", ".join(also))
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if a["dedupe_key"] != b["dedupe_key"]:
                shared = shared_lines(a["dedupe_key"], b["dedupe_key"])
                if shared:
                    print("OVERLAP %s and %s: keys differ but share %s; settle at the checkpoint"
                          % (a["id"], b["id"], ", ".join(shared)))
    for rec in data["records"]:
        if rec["kind"] == "upstream":
            print("UPSTREAM %s [%s]: not on the list; the cycle never sends it" % (rec["id"], rec["status"]))
    if merged_now:
        print("merged now: %s" % ", ".join(merged_now))
    return 0


def parse_numbers(text, count):
    if text.strip().lower() == "none":
        return set()
    out = set()
    for part in re.split(r"[\s,]+", text.strip()):
        if not part:
            continue
        if not part.isdigit() or not 1 <= int(part) <= count:
            raise Refused("not an item number on the list of %d: %r" % (count, part))
        out.add(int(part))
    return out


def cmd_verdicts(args):
    state = load_state(args.run_dir)
    stage = args.stage
    _, _, merge_step, check_step, _ = DRAFT_STAGES[stage]
    require_turn(state, check_step)
    shown = state["listings"].get(stage)
    if shown is None:
        raise Refused("refused: no list was shown; run `cycle.py merge-drafts` and show it first", 3)
    directory = stage_dir(args.run_dir, stage)
    data = drafts.load(directory)
    by_id = {r["id"]: r for r in data["records"]}
    changed = [s["id"] for s in shown if draft_hash(directory, by_id[s["id"]]) != s["sha256"]]
    if changed:
        raise Refused("refused: %s changed after the list was shown, so the yes does not cover it; "
                      "run merge-drafts and show the list again" % ", ".join(changed), 3)
    listed = {s["id"] for s in shown} | set(rider_ids(state, stage))
    unlisted = [r["id"] for r in data["records"]
                if r["kind"] != "upstream" and r["status"] == "pending" and r["id"] not in listed]
    if unlisted:
        raise Refused("refused: %s %s not on the list the maintainer saw; run merge-drafts and show "
                      "it again" % (", ".join(unlisted), "is" if len(unlisted) == 1 else "are"), 3)
    struck = parse_numbers(args.strike, len(shown))
    groups = groups_of(state, stage)
    approved, rejected = [], []
    for item in shown:
        rec = by_id[item["id"]]
        verdict = "struck" if item["n"] in struck else "approved"
        if rec["status"] == "filed":
            continue
        run_drafts("set", directory, rec["id"], verdict, "--note", "checkpoint %s, item %d"
                   % (stage_of(check_step)[1], item["n"]))
        (rejected if verdict == "struck" else approved).append(rec["id"])
        if verdict == "struck":
            for rider in groups.get(rec["id"], []):
                if by_id[rider]["status"] != "filed":
                    run_drafts("set", directory, rider, "struck", "--note", "merged into %s, struck" % rec["id"])
    note = "approved %d, struck %d%s" % (len(approved), len(rejected), " (item %s)" % ", ".join(
        str(n) for n in sorted(struck)) if struck else "")
    set_step(state, check_step, "done", note=note)
    save_state(args.run_dir, state)
    print("checkpoint %s: %s" % (stage_of(check_step)[1], note))
    return 0


def sync_riders(state, directory, stage):
    """Each rider of a filed primary is approved and given the primary's number, once."""
    data = drafts.load(directory)
    by_id = {r["id"]: r for r in data["records"]}
    out = []
    for primary, riders in groups_of(state, stage).items():
        p = by_id[primary]
        for rider in riders:
            r = by_id[rider]
            if p["status"] == "filed" and r["status"] == "pending":
                run_drafts("set", directory, rider, "approved", "--note", "merged into %s" % primary)
                run_drafts("record-filed", directory, rider, p["issue"])
                out.append("RIDER %s: recorded as #%d, the issue %s was filed as" % (rider, p["issue"], primary))
    return out


def cmd_file_next(args):
    state = load_state(args.run_dir)
    stage = args.stage
    _, _, _, check_step, file_step = DRAFT_STAGES[stage]
    require_turn(state, file_step)
    directory = stage_dir(args.run_dir, stage)
    for line in sync_riders(state, directory, stage):
        print(line)
    data = drafts.load(directory)
    filing = state["filing"].setdefault(stage, {})
    skills = [s for s in drafts.SKILLS if any(r["skill"] == s for r in data["records"])]
    waiting = [s for s in skills if filing.get(s, {}).get("done") is None]
    if not waiting:
        print("DONE: every skill with drafts has filed; mark it with `cycle.py filed`")
        return 0
    by_id = {r["id"]: r for r in data["records"]}
    riders = rider_ids(state, stage)

    def blocked(skill):
        return [by_id[p]["skill"] for r, p in riders.items()
                if by_id[r]["skill"] == skill and by_id[p]["skill"] != skill
                and by_id[p]["skill"] in waiting and by_id[r]["status"] == "pending"]

    skill = next((s for s in waiting if not blocked(s)), waiting[0])
    entry = filing.setdefault(skill, {})
    unfiled = [r for r in data["records"] if r["skill"] == skill and r["kind"] == "issue"
               and r["status"] == "approved" and not r.get("issue")]
    if entry.get("started"):
        for r in unfiled:
            print("CHECK %s: its --file was started %s; before filing again, search the tracker and "
                  "record-filed a match: gh issue list --state all --search %s --json number,title"
                  % (r["id"], entry["started"], shlex.quote("%s in:title" % r["title"])))
    else:
        entry["started"] = now()
    hold = skill in AFTER_FILING
    if hold:
        held_of(state, stage).setdefault(skill, {"held": now()})
    save_state(args.run_dir, state)
    same = [r for r, p in riders.items() if by_id[r]["skill"] == skill and by_id[p]["skill"] == skill
            and by_id[r]["status"] == "pending"]
    print("FILE /%s --file %s" % (skill, shlex.quote(str(directory))))
    if hold:
        print("HOLD /%s's after-filing step (%s): file its records, then stop before it; it runs at "
              "stage 5, where `cycle.py next` prints it" % (skill, AFTER_FILING[skill].split(",")[0]))
    if same:
        print("NOTE %s ride on a record of the same skill: `filed` records them with its number, so "
              "this --file runs once" % ", ".join(same))
    print("then: cycle.py filed %s %s%s" % (args.run_dir, skill, "" if stage == "find" else " --stage exercise"))
    return 0


def cmd_filed(args):
    state = load_state(args.run_dir)
    stage = args.stage
    file_step = DRAFT_STAGES[stage][4]
    require_turn(state, file_step)
    directory = stage_dir(args.run_dir, stage)
    for line in sync_riders(state, directory, stage):
        print(line)
    data = drafts.load(directory)
    recs = [r for r in data["records"] if r["skill"] == args.skill]
    if not recs:
        raise Refused("no drafts from %s in this stage" % args.skill)
    waiting = drafts.open_records(recs)
    if waiting:
        raise Refused("refused: %s still pending or unfiled; /%s --file is not finished"
                      % (", ".join(r["id"] for r in waiting), args.skill), 3)
    filing = state["filing"].setdefault(stage, {})
    filing.setdefault(args.skill, {})["done"] = now()
    skills = {r["skill"] for r in data["records"]}
    left = sorted(s for s in skills if not filing.get(s, {}).get("done"))
    if not left:
        numbers = sorted({r["issue"] for r in data["records"] if r.get("issue")})
        set_step(state, file_step, "done", note="filed %s" % (", ".join("#%d" % n for n in numbers) or "nothing"))
    save_state(args.run_dir, state)
    print("%s filed%s" % (args.skill, "; %s done" % file_step if not left else "; still to file: " + ", ".join(left)))
    return 0


def cmd_after_filed(args):
    state = load_state(args.run_dir)
    require_turn(state, "after-filing")
    rec = held_of(state, args.stage).get(args.skill)
    if rec is None:
        raise Refused("no after-filing step of /%s is held in %s" % (args.skill, STAGE_TITLES[args.stage]))
    if rec.get("run"):
        raise Refused("refused: the held after-filing step of /%s (%s) ran %s and is never run again"
                      % (args.skill, STAGE_TITLES[args.stage], rec["run"]), 3)
    run_drafts("after", stage_dir(args.run_dir, args.stage), "--skill", args.skill)
    rec["run"] = now()
    left = pending_holds(state)
    if not left:
        ran = ["/%s (%s)" % (s, STAGE_TITLES[g]) for g in DRAFT_STAGES for s in drafts.SKILLS
               if s in (state["held"].get(g) or {})]
        set_step(state, "after-filing", "done", note="ran the held after-filing step of " + ", ".join(ran))
    save_state(args.run_dir, state)
    print("/%s's held after-filing step (%s) recorded as run%s" % (
        args.skill, STAGE_TITLES[args.stage], "; after-filing done" if not left else
        "; still held: " + ", ".join("/%s (%s)" % (s, STAGE_TITLES[g]) for g, s in left)))
    return 0


def cmd_redraft(args):
    state = load_state(args.run_dir)
    directory = stage_dir(args.run_dir, "find")
    data = drafts.load(directory)
    filed = [r["id"] for r in data["records"] if r.get("issue")]
    if filed:
        raise Refused("refused: %s already filed against %s; finish filing at that commit instead"
                      % (", ".join(filed), state["baseline_sha"]["find"]), 3)
    if outcome(state, "find-file") in FINISHED:
        raise Refused("refused: stage 1 has filed; nothing to re-draft", 3)
    sha = args.sha.strip().lower()
    old = state["baseline_sha"]["find"]
    src = directory / "drafts"
    if src.is_dir():
        src.rename(directory / ("drafts.superseded-%s" % old[:12]))
    for step in ("find-draft", "find-merge", "checkpoint-a", "find-file"):
        if step in state["steps"]:
            set_step(state, step, "stopped", note="re-drafting: main moved from %s to %s" % (old, sha))
    state["baseline_sha"]["find"] = sha
    state["merges"].pop("find", None)
    state["listings"].pop("find", None)
    state["filing"].pop("find", None)
    state.setdefault("held", {}).pop("find", None)
    save_state(args.run_dir, state)
    print("stage 1 re-drafts at %s; the old drafts are in drafts.superseded-%s" % (sha, old[:12]))
    return 0


# ---------------------------------------------------------------------------- ledger

def entry_heading(state):
    return "## release-cycle-%s" % state["run"]


def quote_body(body):
    return "\n".join("    > " + line if line.strip() else "    >" for line in body.rstrip("\n").splitlines())


def unresolved(run_dir, stage, state):
    directory = stage_dir(run_dir, stage)
    data = drafts.load(directory)
    riders = rider_ids(state, stage)
    out = []
    for rec in data["records"]:
        if rec["kind"] == "upstream":
            if rec["status"] == "upstream-pending":
                out.append((rec, "**not sent** — needs maintainer approval"))
        elif rec in drafts.open_records(data["records"]):
            what = "rides on %s; **not filed**" % riders[rec["id"]] if rec["id"] in riders else "**not filed**"
            out.append((rec, "%s, %s" % (rec["status"], what)))
    return [(rec, why, directory) for rec, why in out]


def render_entry(state, run_dir):
    k = state["kickoff"]
    turn = first_unfinished(state)
    date = state["started"][:10]
    ending = "finished" if turn is None else "stopped at %s" % label(turn)
    walk = ("a simulated walk, persona `%s`, from module %s" % (k["persona"], k["module"])
            if k["simulated"] else "no simulated walk (`/dry-run` phases 1 and 2)")
    lines = [
        entry_heading(state),
        "",
        "- **Implemented:** %s (**Not a spec**: a dated record of one `/release-cycle` run, `%s`, "
        "from `main` at `%s`; written when the run %s.)" % (date, state["run"], state["baseline_sha"]["find"][:8], ending),
        "- **Commit:** uncommitted",
        "- **Files changed:** `specs/IMPLEMENTED.md` (this entry). Each record the run created was "
        "created by the skill that owns it, under that skill's gate, and is recorded there.",
        "- **MCP re-check:** n/a (no Senzing fact): this entry records a run's stages; each skill "
        "the run invoked re-asks its own Senzing facts.",
        "- **Kickoff:** %s; %s; refine threshold %s." % (
            walk, "the loop merges" if k["merge"] else "the loop runs with `--no-merge`", k["threshold"]),
        "- **Stages:**",
    ]
    for number, name in enumerate(STAGES):
        parts = []
        for step, n, letter in STEPS:
            if n != number:
                continue
            rec = state["steps"].get(step) or {}
            text = rec.get("outcome") or "not reached"
            if rec.get("note"):
                text += " (%s)" % rec["note"]
            parts.append("%s%s: %s" % (step, " [%s]" % letter if letter else "", text))
        lines.append("  - %d %s: %s." % (number, name, "; ".join(parts)))
    for stage, title in (("find", "stage 1"), ("exercise", "stage 4")):
        data = drafts.load(stage_dir(run_dir, stage))
        filed = {}
        for r in data["records"]:
            if r.get("issue"):
                filed.setdefault(r["issue"], []).append("`%s`" % r["id"])
        struck = [r for r in data["records"] if r["status"] == "struck"]
        if filed or struck:
            lines.append("- **Filed in %s:** %s. **Struck at the checkpoint:** %s." % (
                title, ", ".join("#%d (%s)" % (n, ", ".join(ids)) for n, ids in sorted(filed.items()))
                or "none", ", ".join("`%s`" % r["id"] for r in struck) or "none"))
    pending = unresolved(run_dir, "find", state) + unresolved(run_dir, "exercise", state)
    lines.append("- **Drafts still unresolved** (INV-317's 2026-10-13 note): %s" % (
        "none." if not pending else "%d, each below, its draft kept in the gitignored `%s`." % (len(pending), run_dir)))
    for rec, why, directory in pending:
        title = rec.get("title") or rec.get("after") or rec["source"]
        lines.append("  - `%s` (%s, from %s): %s — %s. Sites: %s." % (
            rec["id"], rec["kind"], rec["source"], title, why, "; ".join(rec["dedupe_key"]) or "none"))
        if rec["kind"] in ("issue", "upstream"):
            _, body = drafts.split_draft((Path(directory) / rec["draft"]).read_text(encoding="utf-8"))
            if body.strip():
                lines.append(quote_body(body))
    holds = pending_holds(state)
    lines.append("- **After-filing steps held for stage 5, not yet run:** %s" % (
        "none." if not holds else "%d, each below with the lines `drafts.py after` prints for it." % len(holds)))
    for stage, skill in holds:
        directory = stage_dir(run_dir, stage)
        try:
            after = run_drafts("after", directory, "--skill", skill)
        except Refused:
            after = None
        lines.append("  - `/%s` (%s): %s; `drafts.py after %s --skill %s`%s." % (
            skill, STAGE_TITLES[stage], AFTER_FILING[skill], directory, skill,
            " still refuses, because a record of the skill is unresolved" if after is None else ""))
        if after and after.strip():
            lines.append(quote_body(after))
    lines.append("- **Establishes no invariant** (INV-309): it records a run. The invariants the "
                 "run's work raised are decided by `/review-invariants` at checkpoint D and recorded "
                 "in that skill's own entry.")
    return "\n".join(lines) + "\n"


def find_entry(text, heading):
    m = re.search(r"^%s\n" % re.escape(heading), text, re.M)
    if not m:
        return None
    nxt = re.search(r"^## (?=\S)", text[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(text)
    return m.start(), end


def insert_entry(text, entry, heading):
    span = find_entry(text, heading)
    if span:
        start, end = span
        return text[:start] + entry + "\n" + text[end:]
    m = re.search(r"^-->\n", text, re.M)
    if not m:
        raise Refused("the ledger has no format comment closing `-->` to write below")
    return text[:m.end()] + "\n" + entry + text[m.end():]


def committed(ledger, heading):
    """Whether HEAD's copy of the ledger already carries this run's entry."""
    path = Path(ledger).resolve()
    try:
        out = subprocess.run(["git", "-C", str(path.parent), "show", "HEAD:./%s" % path.name],
                             capture_output=True, text=True)
    except OSError:
        return False
    return out.returncode == 0 and find_entry(out.stdout, heading) is not None


def cmd_ledger(args):
    state = load_state(args.run_dir)
    heading = entry_heading(state)
    if args.withdraw:
        path = Path(args.withdraw)
        text = path.read_text(encoding="utf-8")
        span = find_entry(text, heading)
        led = state.get("ledger") or {}
        if span is None:
            raise Refused("refused: %s carries no %s" % (path, heading), 3)
        chunk = text[span[0]:span[1]]
        if hashlib.sha256(chunk.encode("utf-8")).hexdigest() != led.get("sha256"):
            raise Refused("refused: %s's entry is not the text this run wrote (edited since?); "
                          "leave it to the maintainer" % path, 3)
        if committed(path, heading):
            led["committed"] = True
            save_state(args.run_dir, state)
            raise Refused("refused: the entry is committed; it stays, and is replaced at the next stop", 3)
        path.write_text(text[:span[0]] + text[span[1]:], encoding="utf-8")
        led.update({"withdrawn": now()})
        state["ledger"] = led
        save_state(args.run_dir, state)
        print("withdrew %s from %s; state.json still holds it" % (heading, path))
        return 0
    entry = render_entry(state, args.run_dir)
    if not args.write:
        sys.stdout.write(entry)
        return 0
    path = Path(args.write)
    text = insert_entry(path.read_text(encoding="utf-8"), entry, heading)
    path.write_text(text, encoding="utf-8")
    span = find_entry(text, heading)
    state["ledger"] = {"path": str(args.write), "written": now(),
                       "sha256": hashlib.sha256(text[span[0]:span[1]].encode("utf-8")).hexdigest()}
    save_state(args.run_dir, state)
    print("wrote %s to %s, uncommitted (INV-310)" % (heading, path))
    return 0


# ---------------------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("kickoff", help="earlier runs, the last walk and the standing threshold")
    p.add_argument("runs_root")
    p.set_defaults(func=cmd_kickoff)

    p = sub.add_parser("init", help="start a run from the kickoff answers")
    p.add_argument("run_dir")
    p.add_argument("--simulated", required=True, choices=("yes", "no"))
    p.add_argument("--persona")
    p.add_argument("--module")
    p.add_argument("--merge", required=True, choices=("yes", "no"))
    p.add_argument("--threshold", required=True)
    p.add_argument("--sha")
    p.set_defaults(func=cmd_init)

    for name, func in (("next", cmd_next), ("status", cmd_status)):
        p = sub.add_parser(name)
        p.add_argument("run_dir")
        p.set_defaults(func=func)

    p = sub.add_parser("args", help="what a step runs")
    p.add_argument("run_dir")
    p.add_argument("step", choices=STEP_NAMES)
    p.add_argument("--head")
    p.add_argument("--blueprint", default="BLUEPRINT.md")
    p.set_defaults(func=cmd_args)

    p = sub.add_parser("mark", help="record a step's outcome")
    p.add_argument("run_dir")
    p.add_argument("step", choices=STEP_NAMES)
    p.add_argument("outcome", choices=OUTCOMES)
    p.add_argument("--note")
    p.add_argument("--sha")
    p.set_defaults(func=cmd_mark)

    for name, func in (("merge-drafts", cmd_merge_drafts), ("verdicts", cmd_verdicts),
                       ("file-next", cmd_file_next)):
        p = sub.add_parser(name)
        p.add_argument("run_dir")
        p.add_argument("--stage", choices=tuple(DRAFT_STAGES), default="find")
        if name == "verdicts":
            p.add_argument("--strike", required=True)
        p.set_defaults(func=func)

    p = sub.add_parser("filed", help="a skill's --file is finished")
    p.add_argument("run_dir")
    p.add_argument("skill", choices=drafts.SKILLS)
    p.add_argument("--stage", choices=tuple(DRAFT_STAGES), default="find")
    p.set_defaults(func=cmd_filed)

    p = sub.add_parser("after-filed", help="a held after-filing step has run, at stage 5")
    p.add_argument("run_dir")
    p.add_argument("skill", choices=tuple(AFTER_FILING))
    p.add_argument("--stage", choices=tuple(DRAFT_STAGES), default="find")
    p.set_defaults(func=cmd_after_filed)

    p = sub.add_parser("redraft", help="main moved before stage 1 filed: draft again")
    p.add_argument("run_dir")
    p.add_argument("--sha", required=True)
    p.set_defaults(func=cmd_redraft)

    p = sub.add_parser("ledger", help="render, write or withdraw the run's ledger entry")
    p.add_argument("run_dir")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--write")
    g.add_argument("--withdraw")
    p.set_defaults(func=cmd_ledger)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Refused as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except drafts.Refused as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except (OSError, ValueError, KeyError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
