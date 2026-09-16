#!/usr/bin/env python3
"""Per-entry duplicate detection and archiving for bootcamp feedback files.

Feedback files arrive from **multiple bootcampers at multiple times**, so the realistic
collision is not "the identical file twice" — it is a file that *overlaps* a previous
one. A bootcamper's project accumulates entries during a run; a later copy dropped into
the repo holds the earlier entries **plus** new ones. Comparing whole files handles that
wrongly in both directions: a byte-compare calls it new and every entry is re-specced,
and a whole-file duplicate verdict would discard the genuinely new entries.

So identity here is **per entry**, and it is content-addressed:

* an entry is one ``## Improvement: <title>`` block (heading through the line before the
  next ``##`` heading, or EOF);
* its id is ``sha256`` of the entry's **normalized** text, first 16 hex chars.

Normalization matters as much as the hash. A file re-saved on Windows can gain a UTF-8
BOM or CRLF line endings without any content change, and PowerShell can double-encode it
outright — all of which change bytes. Normalizing first is what stops "same feedback,
different bytes" from reading as new work. The rules are fixed here, in code, rather than
described in prose, because a later run that normalized even slightly differently would
produce different ids and silently re-process everything.

The ledger is ``feedback/PROCESSED.jsonl`` — one JSON object per processed entry,
append-only and read **last-wins**, so a disposition can be corrected by appending a
superseding line (``annotate``) without ever rewriting history. It answers "has this been processed?" in one read, and also answers the
question nothing else can today: **which spec came from this entry?**

Usage::

    feedback_ledger.py check <candidate.md> [--repo <dir>]
    feedback_ledger.py commit <candidate.md> [--repo <dir>] [--disposition title=spec ...]

``check`` classifies every entry and exits 0 (some entries are new), 3 (every entry has
been processed — a full duplicate) or 1 (bad input). It writes nothing.

``commit`` archives the candidate to
``feedback/SENZING_BOOTCAMP_PLUGIN_FEEDBACK_<unixtime>.md`` and appends one ledger line
per entry. For a full duplicate it instead renames the candidate in place to
``…_<unixtime-of-the-file-it-duplicates>_DUPLICATE.md`` and appends nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

LEDGER_NAME = "PROCESSED.jsonl"
ARCHIVE_DIR = "feedback"
ARCHIVE_STEM = "SENZING_BOOTCAMP_PLUGIN_FEEDBACK"

# An entry starts at a `## ` heading. The feedback template uses
# `## Improvement: <title>`, but bootcampers do not always follow it, so any H2 that is
# not one of the file's own scaffold headings counts as an entry.
_ENTRY_HEADING = re.compile(r"(?m)^##\s+(?P<title>\S.*?)\s*$")

# Scaffold headings that are part of the file, not feedback: skipped so an empty
# "Your Feedback" placeholder never becomes a processed entry.
_SCAFFOLD_TITLES = {
    "your feedback",
    "feedback",
    "senzing bootcamp plugin feedback",
}


def normalize(text: str) -> str:
    """Content-only form of a document or entry, stable across trivial re-saves.

    Strips a UTF-8 BOM, normalizes CRLF/CR to LF, right-strips every line, collapses
    runs of blank lines to one, and strips leading/trailing blank lines. Deliberately
    does NOT touch case or interior spacing: a reworded entry is a different entry.
    """
    text = text.lstrip("﻿")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    out: list = []
    for line in lines:
        if not line and out and not out[-1]:
            continue
        out.append(line)
    return "\n".join(out).strip("\n")


def entry_id(entry_text: str) -> str:
    """Content-addressed id for one entry: sha256 of its normalized text, 16 hex chars."""
    return hashlib.sha256(normalize(entry_text).encode("utf-8")).hexdigest()[:16]


def split_entries(text: str) -> list:
    """Split a feedback document into [(title, entry_text)], scaffold headings dropped."""
    normalized = normalize(text)
    matches = list(_ENTRY_HEADING.finditer(normalized))
    entries = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        title = match.group("title").strip()
        body = normalized[start:end].strip("\n")
        # A heading with no content under it is a placeholder, not an entry.
        content = body[len(match.group(0)):].strip()
        if title.strip().lower().rstrip(":") in _SCAFFOLD_TITLES or not content:
            continue
        entries.append((title, body))
    return entries


def read_ledger(repo: Path) -> dict:
    """{entry_id: record} from feedback/PROCESSED.jsonl; {} when absent."""
    path = repo / ARCHIVE_DIR / LEDGER_NAME
    seen = {}
    if not path.is_file():
        return seen
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue  # a malformed line must not hide the rest of the ledger
            if record.get("entry_id"):
                seen[record["entry_id"]] = record
    return seen


def classify(candidate: Path, repo: Path) -> dict:
    text = candidate.read_text(encoding="utf-8", errors="replace")
    entries = split_entries(text)
    seen = read_ledger(repo)
    new, known = [], []
    for title, body in entries:
        eid = entry_id(body)
        (known if eid in seen else new).append(
            {"entry_id": eid, "title": title, "record": seen.get(eid)}
        )
    return {
        "candidate": str(candidate),
        "file_id": entry_id(text),
        "entries_total": len(entries),
        "new": new,
        "known": known,
    }


def _archive_unixtime_of(known: list) -> str:
    """The archive timestamp a fully-duplicate candidate duplicates."""
    stamps = []
    for item in known:
        record = item.get("record") or {}
        stamp = record.get("archive_unixtime")
        if stamp:
            stamps.append(str(stamp))
    if not stamps:
        return str(int(time.time()))
    # Every entry should trace to one archive; if several, name the earliest.
    return sorted(stamps)[0]


def cmd_check(args) -> int:
    repo = Path(args.repo).resolve()
    candidate = Path(args.candidate)
    if not candidate.is_file():
        sys.stderr.write(f"No such feedback file: {candidate}\n")
        return 1
    result = classify(candidate, repo)
    if result["entries_total"] == 0:
        sys.stderr.write(
            f"{candidate}: no feedback entries found (only scaffold/placeholder headings). "
            "Nothing to process.\n"
        )
        return 1
    print(json.dumps(result, indent=2))
    if not result["new"]:
        print(
            f"\nVERDICT: DUPLICATE — all {result['entries_total']} entries are already in "
            f"{ARCHIVE_DIR}/{LEDGER_NAME}. Duplicates the archive at unixtime "
            f"{_archive_unixtime_of(result['known'])}.",
            file=sys.stderr,
        )
        return 3
    if result["known"]:
        print(
            f"\nVERDICT: PARTIAL — {len(result['new'])} new entr(y/ies), "
            f"{len(result['known'])} already processed. Triage ONLY the new ones.",
            file=sys.stderr,
        )
    else:
        print(
            f"\nVERDICT: NEW — all {result['entries_total']} entries are unprocessed.",
            file=sys.stderr,
        )
    return 0


def cmd_commit(args) -> int:
    repo = Path(args.repo).resolve()
    candidate = Path(args.candidate)
    if not candidate.is_file():
        sys.stderr.write(f"No such feedback file: {candidate}\n")
        return 1
    result = classify(candidate, repo)
    if result["entries_total"] == 0:
        sys.stderr.write(f"{candidate}: no entries; refusing to archive.\n")
        return 1

    archive_dir = repo / ARCHIVE_DIR
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Full duplicate: rename in place, name the archive it duplicates, append nothing.
    if not result["new"]:
        stamp = _archive_unixtime_of(result["known"])
        target = candidate.with_name(f"{ARCHIVE_STEM}_{stamp}_DUPLICATE.md")
        suffix = 2
        while target.exists():
            target = candidate.with_name(f"{ARCHIVE_STEM}_{stamp}_DUPLICATE-{suffix}.md")
            suffix += 1
        candidate.rename(target)
        print(f"DUPLICATE: {candidate} -> {target} (nothing processed, ledger unchanged)")
        return 3

    stamp = str(int(time.time()))
    target = archive_dir / f"{ARCHIVE_STEM}_{stamp}.md"
    suffix = 2
    while target.exists():
        target = archive_dir / f"{ARCHIVE_STEM}_{stamp}-{suffix}.md"
        suffix += 1

    # rpartition, not partition: an entry title legitimately contains "=" — e.g.
    # "sdk_guide(topic='configure') snippet fails …" — and splitting on the FIRST "="
    # truncated the key and silently dropped the disposition. A spec path never
    # contains "=", so the last one is the separator. An entry_id is accepted as the
    # key too, for a title that is awkward to quote on a command line.
    dispositions = {}
    for pair in args.disposition or []:
        key, sep, value = pair.rpartition("=")
        if not sep:
            sys.stderr.write(f"ignoring --disposition without '=': {pair!r}\n")
            continue
        if key.strip():
            dispositions[key.strip()] = value.strip()

    processed_on = time.strftime("%Y-%m-%d", time.gmtime())
    lines = []
    for item in result["new"]:
        lines.append(
            json.dumps(
                {
                    "entry_id": item["entry_id"],
                    "title": item["title"],
                    "archive": target.name,
                    "archive_unixtime": stamp,
                    "processed": processed_on,
                    "disposition": dispositions.get(
                        item["title"], dispositions.get(item["entry_id"], "unrecorded")
                    ),
                },
                sort_keys=True,
            )
        )
    ledger = archive_dir / LEDGER_NAME
    with ledger.open("a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line + "\n")

    candidate.rename(target)
    print(f"ARCHIVED: {candidate} -> {target}")
    print(f"LEDGER:   +{len(lines)} entr(y/ies) in {ledger}")
    if result["known"]:
        print(
            f"NOTE:     {len(result['known'])} entr(y/ies) in this file were already "
            "processed and were not re-recorded."
        )
    unrecorded = [line for line in lines if '"disposition": "unrecorded"' in line]
    if unrecorded:
        print(
            f"WARNING:  {len(unrecorded)} entr(y/ies) recorded with disposition "
            '"unrecorded" — pass --disposition "<title>=<spec-or-outcome>" so the ledger '
            "says which spec each entry produced.",
            file=sys.stderr,
        )
    return 0


def cmd_annotate(args) -> int:
    """Append a superseding record for one entry, to set or correct its disposition.

    The ledger is append-only and read **last-wins**, so a correction is a new line
    rather than an edit: history stays intact and the current answer is the latest line
    for that ``entry_id``.
    """
    repo = Path(args.repo).resolve()
    seen = read_ledger(repo)
    record = seen.get(args.entry_id)
    if record is None:
        sys.stderr.write(
            f"No ledger record for entry_id {args.entry_id!r}. Run `check` on the source "
            "file to list ids.\n"
        )
        return 1
    updated = dict(record)
    updated["disposition"] = args.disposition
    updated["annotated"] = time.strftime("%Y-%m-%d", time.gmtime())
    ledger = repo / ARCHIVE_DIR / LEDGER_NAME
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(updated, sort_keys=True) + "\n")
    print(
        f"ANNOTATED: {args.entry_id} disposition -> {args.disposition!r} "
        "(appended; the ledger reads last-wins)"
    )
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="classify a candidate's entries; writes nothing")
    check.add_argument("candidate")
    check.set_defaults(func=cmd_check)

    commit = sub.add_parser("commit", help="archive the candidate and record its entries")
    commit.add_argument("candidate")
    commit.add_argument(
        "--disposition",
        action="append",
        metavar="TITLE=SPEC",
        help="what an entry produced, e.g. \"Screenshot capture fails=specs/foo.md\" or "
             "\"Vague thing=needs-clarification\". Repeatable.",
    )
    commit.set_defaults(func=cmd_commit)

    annotate = sub.add_parser(
        "annotate", help="append a superseding line to set/correct one entry's disposition"
    )
    annotate.add_argument("entry_id")
    annotate.add_argument("disposition")
    annotate.set_defaults(func=cmd_annotate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
