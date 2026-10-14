#!/usr/bin/env python3
"""Two-stage drafting for the five finding skills: the manifest, its statuses and the contract.

⛔ **(INV-300) This docstring is the one statement of the `--draft <run-dir>` / `--file <run-dir>`
contract and of the manifest format.** `/feedback-to-issues`, `/retrofit-from-public`,
`/delegate-to-mcp-server`, `/production-readiness-audit` and `/dry-run` cite it and restate none
of it. Run without either argument, each of them behaves exactly as it did before (#572).
`tests/test_drafts.py` exercises this helper offline and holds the five skills to their pointer.

Why two stages: a skill that finds and files in one session leaves no point at which a caller can
collect several skills' findings, merge duplicates and get one checkpoint's approval. `--draft` is
**`/release-cycle`'s interface** (#573), which runs four of the skills in one wave against one
baseline SHA, then `/dry-run`, and files from the approved list.

Stage one: `--draft <run-dir>`
==============================

The skill runs up to its filing step, then runs `add` once per record instead of filing it, and
stops. ⛔ **(INV-368) Stage one files nothing, fixes nothing and sends nothing, and writes nothing outside
`<run-dir>`:** no `gh issue create`, no comment, no `submit_feedback`, no fix, and every ledger
and archive the skill keeps is left untouched (`feedback/`, `specs/mcp-coverage.jsonl`,
`specs/IMPLEMENTED.md`). The one write outside `<run-dir>` is the disposable scratch project a
`/dry-run` phase builds and removes, which never holds a record. A run by hand names its own
`<run-dir>`, under `.claude/release-cycle/runs/` (gitignored), e.g.
`.claude/release-cycle/runs/2026-10-13-dry-run`. A `/feedback-to-issues` candidate stays exactly where it is: Step 3's
duplicate rename and Step 9 wait for stage two or a normal run. What the skill would have written
is an `add` record instead:

* an issue it would file → ``add --kind issue`` (status `pending`);
* an upstream message it would put to the maintainer → ``add --kind upstream`` (status
  `upstream-pending`); the issue it belongs to carries its `Upstream:` value from
  `/feedback-to-issues` Step 8.1's "no maintainer is asked" column;
* a ledger line its after-filing step writes for something it files nothing for (a
  `/delegate-to-mcp-server` keep, a `/feedback-to-issues` `already-tracked` entry) →
  ``add --kind ledger`` (status `pending`), with ``--after``.

⛔ **The caller records unresolved drafts (INV-317).** `<run-dir>` is gitignored
(`.claude/release-cycle/runs/`), so a draft there is not a durable record. `/release-cycle`
records every draft still unresolved when it stops in its dated `specs/IMPLEMENTED.md` entry,
marked **not filed** (#573); the five skills gain no write of their own. Run by hand, a `--draft`
run ends with ``list <run-dir> --skill <skill>``, whose last lines warn that the drafts are not yet
a durable record and print the `--file` command.

Between the stages: the checkpoint
==================================

The caller (or the maintainer) reads the drafts, may edit a draft's body, and sets each record's
status with ``set``: `approved` or `struck` for an `issue` or `ledger` record;
`upstream-sent` or `upstream-declined` for an `upstream` record, which only its own yes moves
(#570 keeps upstream messages per record).

Stage two: `--file <run-dir>`
=============================

1. ``file-plan <run-dir> --skill <skill>`` refuses (exit 4) when HEAD is not the manifest's
   baseline SHA, naming both: a draft that cites `path:line` against a moved commit may cite the
   wrong line. Otherwise it prints one ``FILE`` line per `approved` issue record not yet filed,
   each carrying the exact `gh issue create` command, and ``SKIP`` (already filed), ``STRUCK``,
   ``PENDING`` and ``UPSTREAM`` lines for the rest, which it leaves alone.
2. ⛔ **(INV-314) Until #570's amendments are registered, show the maintainer each record's title,
   labels and body and get a yes for each before running its command.** `/retrofit-from-public`
   first repeats its tracker search, because the tracker may have changed since the draft, and
   strikes a record already tracked (``set <id> struck --note "tracked as #<n>"``).
3. After each issue is created: ``record-filed <run-dir> <id> <number>``. A record already
   carrying a number is never filed twice: ``file-plan`` skips it and ``record-filed`` refuses a
   second, different number.
4. ``after <run-dir> --skill <skill>`` prints the skill's after-filing arguments, one line per
   resolved record, with the issue numbers filled in; a struck record reads **declined by the
   maintainer**. It refuses (exit 3) while any record of the skill is `pending` or `approved` and
   unfiled, so the after-filing step runs once, on a complete set. Then run the skill's
   after-filing step with those lines (`/feedback-to-issues` Step 9, `/delegate-to-mcp-server`
   Step 9) and its report.

`--file` never sends an `upstream` record.
⛔ (INV-319) No command this helper prints passes `--repo`, and `add` refuses the `unattended-ok`
label (INV-318).

The manifest: `<run-dir>/drafts/manifest.json`
==============================================

One JSON object, written atomically under a lock (`manifest.lock`), so the skills of one wave may
append to it at once::

    {"format": 1, "baseline_sha": "<40 hex>", "records": [<record>, ...]}

Each record:

* ``id`` — ``<skill>-NN``, numbered per skill from 01; its draft is ``drafts/<id>.md``;
* ``skill`` — one of ``SKILLS``; ``source`` — the skill and its step, e.g. ``dry-run phase 2``;
* ``kind`` — ``issue`` | ``upstream`` | ``ledger``;
* ``status`` — see ``STATUSES``: `pending` → `approved` | `struck` → (`approved` only) `filed`,
  for `issue` and `ledger` records; `upstream-pending` → `upstream-sent` | `upstream-declined` for
  `upstream` records. `filed` is set only by ``record-filed`` and never changes again;
* ``title``, ``labels`` — what `gh issue create` receives (an `issue` record must have a title);
  ``category`` — `bug` or `feature`, for an `upstream` record;
* ``dedupe_key`` — the sorted `path:line` (or `path:N-M`) sites the record cites, which
  `/release-cycle` uses to merge duplicates across skills;
* ``after`` — optional: the arguments this record adds to the skill's after-filing step, where
  ``{issue}`` becomes the number filed and ``{outcome}`` becomes ``#<number>``, or **declined by
  the maintainer** for a struck record; ``after_struck`` — what a struck record prints instead
  (required when ``after`` names ``{issue}``). A struck record with neither ``after_struck`` nor
  ``{outcome}`` in its ``after`` prints nothing, and an `upstream` record never prints;
* ``issue`` — the number filed, or null; ``note`` — free text ``set --note`` adds.

The draft file `drafts/<id>.md` holds an HTML-comment header (id, skill, source, kind, baseline
SHA, dedupe key, labels), then ``# <title>``, a blank line and the exact body. The manifest owns
the title, labels and status; the draft owns the body, so a body edited at the checkpoint is the
body filed. ``file-plan`` refuses (exit 3) a draft whose ``# `` title no longer matches the
manifest's, and writes the body alone to ``drafts/<id>.body.md`` for ``--body-file``.

Usage::

    drafts.py add <run-dir> --skill S --source TEXT [--kind issue|upstream|ledger]
                  [--title T] [--label L ...] [--body-file F|-] [--site path:line ...]
                  [--category bug|feature] [--after ARGS] [--after-struck ARGS] [--sha SHA]
    drafts.py list <run-dir> [--skill S] [--status X]
    drafts.py set <run-dir> <id> <status> [--note TEXT]
    drafts.py file-plan <run-dir> --skill S [--sha SHA]
    drafts.py record-filed <run-dir> <id> <number>
    drafts.py after <run-dir> --skill S
    drafts.py check-sha <run-dir> [--sha SHA]

``--sha`` defaults to ``git rev-parse HEAD`` in the current directory. Exit codes: 0 success,
1 bad input, 2 a refused label, 3 a refused transition or an unresolved set, 4 a baseline-SHA
mismatch.

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

SKILLS = (
    "feedback-to-issues",
    "retrofit-from-public",
    "delegate-to-mcp-server",
    "production-readiness-audit",
    "dry-run",
)
KINDS = ("issue", "upstream", "ledger")

#: Status -> the statuses ``set`` may move it to. `filed` is reachable only by ``record-filed``.
STATUSES = {
    "pending": ("approved", "struck"),
    "approved": ("pending", "struck"),
    "struck": ("pending", "approved"),
    "filed": (),
    "upstream-pending": ("upstream-sent", "upstream-declined"),
    "upstream-sent": (),
    "upstream-declined": ("upstream-pending",),
}

#: INV-318: choosing work for `/unattended-issue-loop` is the maintainer's decision alone.
FORBIDDEN_LABELS = ("unattended-ok",)

DECLINED = "declined by the maintainer"
SITE = re.compile(r"^(?P<path>[^\s:]+):(?P<start>\d+)(?:-(?P<end>\d+))?$")
SHA = re.compile(r"^[0-9a-f]{7,40}$")


class Refused(Exception):
    """A refusal with an exit code."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------- storage

def drafts_dir(run_dir: Path) -> Path:
    return Path(run_dir) / "drafts"


def manifest_path(run_dir: Path) -> Path:
    return drafts_dir(run_dir) / "manifest.json"


class Locked:
    """An exclusive lock on the manifest, portable (no fcntl): O_CREAT | O_EXCL on a lock file."""

    def __init__(self, run_dir: Path, timeout: float = 30.0):
        self.path = drafts_dir(run_dir) / "manifest.lock"
        self.timeout = timeout

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                os.close(os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise Refused("manifest is locked: %s exists. If no run is writing, remove it."
                                  % self.path, 3)
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def load(run_dir: Path) -> dict:
    path = manifest_path(run_dir)
    if not path.is_file():
        return {"format": 1, "baseline_sha": None, "records": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Refused("%s is not valid JSON: %s" % (path, exc))
    if data.get("format") != 1 or not isinstance(data.get("records"), list):
        raise Refused("%s is not a format-1 manifest" % path)
    return data


def save(run_dir: Path, data: dict) -> None:
    path = manifest_path(run_dir)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def find(data: dict, rid: str) -> dict:
    for rec in data["records"]:
        if rec["id"] == rid:
            return rec
    raise Refused("no record %r in the manifest" % rid)


# ---------------------------------------------------------------------------- helpers

def head_sha() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Refused("cannot read HEAD (pass --sha): %s" % exc)
    return out.stdout.strip()


def resolve_sha(given) -> str:
    sha = (given or head_sha()).strip().lower()
    if not SHA.match(sha):
        raise Refused("not a commit SHA: %r" % sha)
    return sha


def same_commit(a: str, b: str) -> bool:
    """Equal, or one an abbreviation of the other."""
    return a.startswith(b) or b.startswith(a)


def require_baseline(data: dict, sha: str) -> None:
    base = data.get("baseline_sha")
    if base and not same_commit(base, sha):
        raise Refused("baseline SHA mismatch: the manifest was drafted against %s, and this "
                      "checkout is at %s. Its path:line citations may name the wrong lines; "
                      "re-draft against %s, or check out %s." % (base, sha, sha, base), 4)


def dedupe_key(sites) -> list:
    """The sorted, de-duplicated `path:line` sites a record cites."""
    out = set()
    for site in sites or ():
        if not SITE.match(site.strip()):
            raise Refused("not a path:line site: %r" % site)
        out.add(site.strip())
    return sorted(out, key=_site_order)


def _site_order(site: str):
    m = SITE.match(site)
    return (m.group("path"), int(m.group("start")), int(m.group("end") or m.group("start")))


def render(rec: dict, body: str) -> str:
    header = [
        "<!-- drafts.py record",
        "id: %s" % rec["id"],
        "skill: %s" % rec["skill"],
        "source: %s" % rec["source"],
        "kind: %s" % rec["kind"],
        "baseline_sha: %s" % rec["baseline_sha"],
        "dedupe_key: %s" % ("; ".join(rec["dedupe_key"]) or "(none)"),
        "labels: %s" % (", ".join(rec["labels"]) or "(none)"),
        "-->",
        "",
    ]
    title = rec.get("title") or "(%s record: no title)" % rec["kind"]
    return "\n".join(header) + "# %s\n\n%s" % (title, body.rstrip("\n") + "\n" if body else "")


def split_draft(text: str):
    """(title, body) from a draft file, or raise."""
    _, sep, rest = text.partition("\n-->\n")
    if not sep:
        raise Refused("draft has no drafts.py header")
    rest = rest.lstrip("\n")
    first, _, body = rest.partition("\n")
    if not first.startswith("# "):
        raise Refused("draft has no '# <title>' line under its header")
    return first[2:].strip(), body.lstrip("\n")


def fill(template: str, rec: dict) -> str:
    if rec["status"] == "filed":
        return template.replace("{issue}", str(rec["issue"])).replace("{outcome}", "#%d" % rec["issue"])
    if rec["status"] == "struck":
        return template.replace("{outcome}", DECLINED)
    return template


def open_records(recs) -> list:
    """Records the caller has not resolved: still pending, or approved and not yet filed."""
    return [r for r in recs if r["status"] == "pending"
            or (r["status"] == "approved" and r["kind"] == "issue")]


# ---------------------------------------------------------------------------- commands

def cmd_add(args) -> int:
    kind = args.kind
    labels = list(dict.fromkeys(l.strip() for l in args.label or () if l.strip()))
    bad = [l for l in labels if l in FORBIDDEN_LABELS]
    if bad:
        raise Refused("refused: a draft never carries %s (INV-318); choosing work for "
                      "/unattended-issue-loop is the maintainer's decision alone" % ", ".join(bad), 2)
    if kind == "issue" and not (args.title and args.title.strip()):
        raise Refused("an issue record needs --title")
    if kind in ("issue", "upstream") and not args.body_file:
        raise Refused("an %s record needs --body-file" % kind)
    if kind == "upstream" and args.category not in ("bug", "feature"):
        raise Refused("an upstream record needs --category bug or feature (never license_request, INV-135)")
    if kind == "ledger" and not args.after:
        raise Refused("a ledger record needs --after")
    if args.after and "{issue}" in args.after and not args.after_struck:
        raise Refused("--after names {issue}, which a struck record lacks: give --after-struck too")
    if args.body_file == "-":
        body = sys.stdin.read()
    else:
        body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else ""
    sha = resolve_sha(args.sha)
    key = dedupe_key(args.site)
    run_dir = Path(args.run_dir)
    with Locked(run_dir):
        data = load(run_dir)
        require_baseline(data, sha)
        data["baseline_sha"] = data.get("baseline_sha") or sha
        n = 1 + sum(1 for r in data["records"] if r["skill"] == args.skill)
        rec = {
            "id": "%s-%02d" % (args.skill, n),
            "skill": args.skill,
            "source": args.source,
            "kind": kind,
            "status": "upstream-pending" if kind == "upstream" else "pending",
            "baseline_sha": data["baseline_sha"],
            "title": (args.title or "").strip() or None,
            "labels": labels,
            "category": args.category if kind == "upstream" else None,
            "dedupe_key": key,
            "after": args.after,
            "after_struck": args.after_struck,
            "issue": None,
            "note": None,
        }
        draft = drafts_dir(run_dir) / ("%s.md" % rec["id"])
        draft.write_text(render(rec, body), encoding="utf-8")
        rec["draft"] = "drafts/%s" % draft.name
        data["records"].append(rec)
        save(run_dir, data)
    print("%s %s %s" % (rec["id"], rec["status"], rec["draft"]))
    return 0


def warning(run_dir, skills) -> list:
    lines = ["",
             "⚠️  These drafts are NOT yet a durable record: %s is not tracked by git, and "
             "nothing has filed them." % run_dir,
             "    Under /release-cycle, the caller records each unresolved draft in its dated "
             "specs/IMPLEMENTED.md entry, marked not filed (INV-317)."]
    for skill in skills:
        lines.append("    File the approved ones with: /%s --file %s" % (skill, run_dir))
    return lines


def cmd_list(args) -> int:
    data = load(Path(args.run_dir))
    recs = [r for r in data["records"]
            if (not args.skill or r["skill"] == args.skill)
            and (not args.status or r["status"] == args.status)]
    print("baseline %s, %d record(s)" % (data.get("baseline_sha") or "(none)", len(recs)))
    for r in recs:
        issue = " #%d" % r["issue"] if r.get("issue") else ""
        print("%s\t%s\t%s%s\t%s" % (r["id"], r["kind"], r["status"], issue, r.get("title") or r["source"]))
    unresolved = [r for r in recs if r in open_records(recs) or r["status"] == "upstream-pending"]
    if unresolved:
        skills = list(dict.fromkeys(r["skill"] for r in unresolved))
        print("\n".join(warning(args.run_dir, skills)))
    return 0


def cmd_set(args) -> int:
    run_dir = Path(args.run_dir)
    with Locked(run_dir):
        data = load(run_dir)
        rec = find(data, args.id)
        allowed = STATUSES.get(rec["status"], ())
        if args.status != rec["status"] and args.status not in allowed:
            raise Refused("refused: %s is %s (%s record) and cannot become %s; allowed: %s"
                          % (rec["id"], rec["status"], rec["kind"], args.status,
                             ", ".join(allowed) or "nothing"), 3)
        rec["status"] = args.status
        if args.note:
            rec["note"] = args.note
        save(run_dir, data)
    print("%s %s" % (rec["id"], rec["status"]))
    return 0


def cmd_check_sha(args) -> int:
    data = load(Path(args.run_dir))
    sha = resolve_sha(args.sha)
    require_baseline(data, sha)
    print("baseline %s matches %s" % (data.get("baseline_sha") or "(none)", sha))
    return 0


def cmd_file_plan(args) -> int:
    run_dir = Path(args.run_dir)
    data = load(run_dir)
    require_baseline(data, resolve_sha(args.sha))
    print("baseline %s matches this checkout" % data.get("baseline_sha"))
    for r in (r for r in data["records"] if r["skill"] == args.skill):
        if r["kind"] == "upstream":
            print("UPSTREAM %s: %s, never sent by --file" % (r["id"], r["status"]))
        elif r.get("issue"):
            print("SKIP %s: already filed as #%d" % (r["id"], r["issue"]))
        elif r["status"] == "struck":
            print("STRUCK %s: not filed%s" % (r["id"], " (%s)" % r["note"] if r.get("note") else ""))
        elif r["status"] == "pending":
            print("PENDING %s: left alone" % r["id"])
        elif r["kind"] == "ledger":
            print("LEDGER %s: approved, recorded by the after-filing step" % r["id"])
        else:
            bad = [l for l in r["labels"] if l in FORBIDDEN_LABELS]
            if bad:
                raise Refused("refused: %s carries %s (INV-318)" % (r["id"], ", ".join(bad)), 2)
            title, body = split_draft((run_dir / r["draft"]).read_text(encoding="utf-8"))
            if title != r["title"]:
                raise Refused("refused: %s's draft title %r no longer matches the manifest's %r; "
                              "edit both or neither" % (r["id"], title, r["title"]), 3)
            body_file = drafts_dir(run_dir) / ("%s.body.md" % r["id"])
            body_file.write_text(body, encoding="utf-8")
            cmd = ["gh", "issue", "create", "--title", r["title"]]
            for label in r["labels"]:
                cmd += ["--label", label]
            cmd += ["--body-file", str(body_file)]
            print("FILE %s: %s" % (r["id"], " ".join(shlex.quote(c) for c in cmd)))
    return 0


def cmd_record_filed(args) -> int:
    number = int(str(args.number).lstrip("#"))
    if number <= 0:
        raise Refused("not an issue number: %r" % args.number)
    run_dir = Path(args.run_dir)
    with Locked(run_dir):
        data = load(run_dir)
        rec = find(data, args.id)
        if rec.get("issue") == number:
            print("%s already filed as #%d; nothing to do" % (rec["id"], number))
            return 0
        if rec.get("issue"):
            raise Refused("refused: %s is already filed as #%d" % (rec["id"], rec["issue"]), 3)
        if rec["kind"] != "issue" or rec["status"] != "approved":
            raise Refused("refused: %s is a %s record with status %s; only an approved issue "
                          "record is filed" % (rec["id"], rec["kind"], rec["status"]), 3)
        rec["issue"] = number
        rec["status"] = "filed"
        save(run_dir, data)
    print("%s filed #%d" % (rec["id"], number))
    return 0


def cmd_after(args) -> int:
    data = load(Path(args.run_dir))
    recs = [r for r in data["records"] if r["skill"] == args.skill]
    waiting = open_records(recs)
    if waiting:
        raise Refused("refused: %s still pending or unfiled; the after-filing step runs once, on a "
                      "complete set" % ", ".join(r["id"] for r in waiting), 3)
    for r in recs:
        if r["kind"] == "upstream":
            continue
        template = r.get("after")
        if r["status"] == "struck":
            template = r.get("after_struck") or (template if "{outcome}" in (template or "") else None)
        if template:
            print(fill(template, r))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="append one record and write its draft")
    add.add_argument("run_dir")
    add.add_argument("--skill", required=True, choices=SKILLS)
    add.add_argument("--source", required=True, help="the skill and its step")
    add.add_argument("--kind", default="issue", choices=KINDS)
    add.add_argument("--title")
    add.add_argument("--label", action="append")
    add.add_argument("--body-file", help="the exact body; - reads it from stdin")
    add.add_argument("--site", action="append", help="a path:line the record cites (repeatable)")
    add.add_argument("--category", choices=("bug", "feature"))
    add.add_argument("--after", help="after-filing arguments; {issue} and {outcome} are filled in")
    add.add_argument("--after-struck", help="after-filing arguments for a struck record")
    add.add_argument("--sha", help="baseline SHA (default: git rev-parse HEAD)")
    add.set_defaults(func=cmd_add)

    lst = sub.add_parser("list", help="the records, then the not-yet-durable warning")
    lst.add_argument("run_dir")
    lst.add_argument("--skill", choices=SKILLS)
    lst.add_argument("--status", choices=tuple(STATUSES))
    lst.set_defaults(func=cmd_list)

    st = sub.add_parser("set", help="set a record's status at the checkpoint")
    st.add_argument("run_dir")
    st.add_argument("id")
    st.add_argument("status", choices=tuple(s for s in STATUSES if s != "filed"))
    st.add_argument("--note")
    st.set_defaults(func=cmd_set)

    plan = sub.add_parser("file-plan", help="what --file files, skips and leaves alone")
    plan.add_argument("run_dir")
    plan.add_argument("--skill", required=True, choices=SKILLS)
    plan.add_argument("--sha", help="this checkout's SHA (default: git rev-parse HEAD)")
    plan.set_defaults(func=cmd_file_plan)

    rf = sub.add_parser("record-filed", help="write an issue number back")
    rf.add_argument("run_dir")
    rf.add_argument("id")
    rf.add_argument("number")
    rf.set_defaults(func=cmd_record_filed)

    af = sub.add_parser("after", help="the after-filing arguments, numbers filled in")
    af.add_argument("run_dir")
    af.add_argument("--skill", required=True, choices=SKILLS)
    af.set_defaults(func=cmd_after)

    cs = sub.add_parser("check-sha", help="refuse a baseline-SHA mismatch")
    cs.add_argument("run_dir")
    cs.add_argument("--sha", help="this checkout's SHA (default: git rev-parse HEAD)")
    cs.set_defaults(func=cmd_check_sha)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Refused as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
