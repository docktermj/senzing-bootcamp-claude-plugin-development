#!/usr/bin/env python3
"""Citation census and referential-integrity check for the SBCP dev environment.

`compact-dev-environment` merges invariants, archives specs and prunes feedback. Every
one of those operations can break a reference, and the references here are dense enough
that eyeballing them is not a plan: on 2026-08-12 this repo held **6,265** live
`INV-NNN` citations across shipped plugin text, specs, tests and skills — plus 990 more
in commit messages, which cannot be edited and are therefore outside anything this script
can protect.

Both figures are a **dated illustration of scale, not a fact to quote**: run ``census`` and
use what it prints. This paragraph previously claimed **5,210** and 753 for 2026-07-30, and
the first of those was wrong on the day it was written — this script reported 4,587 that
day. The skill's own header records the same error in its table and tells the reader to
re-measure; the docstring of the tool it says to run *first* went on stating the discredited
number as measured fact until 2026-08-12. A number in prose beside an append-only corpus has
nothing coupling it to that corpus, so it drifts silently and is then believed.

Two commands, and the second is the one that matters:

* ``census`` — what cites what. Every invariant with its citation count by area, every
  spec against its ``IMPLEMENTED.md`` heading, every feedback archive against
  ``PROCESSED.jsonl``. Read it before proposing a change.
* ``verify`` — referential integrity. Every cited invariant exists, every spec named as
  an invariant's ``Source:`` is resolvable, every ledger heading has a spec file or is a
  recorded non-spec entry, every archived feedback file is in the ledger. Run it after
  **every** change and require it to stay clean.

The asymmetry worth knowing: a *dangling* reference (pointing at nothing) is what this
script finds. A *wrong* reference — pointing at something real but different, which is
what renumbering produces in unedited history — is undetectable here and is why the skill
defaults to not renumbering.

Usage::

    citations.py census [--repo <dir>] [--area invariants|specs|feedback]
    citations.py verify [--repo <dir>]

``verify`` exits 0 when clean, 2 when something dangles, 1 on bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

INV = re.compile(r"INV-\d{3}")
INV_DEF = re.compile(r"^- \*\*(INV-\d{3})\*\*", re.MULTILINE)
# `(Source: `spec-name`, YYYY-MM-DD.)` — how an invariant records what produced it.
SOURCE = re.compile(r"\(Source: `([^`]+)`")
LEDGER_HEADING = re.compile(r"^## (.+)$", re.MULTILINE)

META_SPECS = {"INVARIANTS", "todo", "IMPLEMENTED", "DECLINED", "RENUMBERING"}

# A file may opt out of the citation scan by carrying this marker. It exists for exactly
# one situation: a file whose *subject* is invariant identifiers, and which therefore
# contains fixture IDs that are not real citations. Without it the census reports its own
# test fixtures as dangling references and `verify` never goes clean. Use it sparingly —
# a file that opts out is invisible to every check here, so a real citation hidden inside
# one will not be protected when an invariant is merged.
#
# Note this module carries the marker by construction: the constant's own value appears in
# it, so the scanner never scans itself. That is intended (a scanner reading its own regex
# examples proves nothing), but do not rely on the accident — keep literal example IDs out
# of this file regardless, so the exclusion is a convenience rather than a load-bearing
# trick.
IGNORE_MARKER = "citations.py: ignore-file"

AREAS = (
    ("plugin", Path("plugins") / "senzing-bootcamp"),
    ("specs", Path("specs")),
    ("tests", Path("tests")),
    ("skills", Path(".claude") / "skills"),
)


def _iter_files(root: Path):
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in (".md", ".py", ".json", ".jsonl", ".sh"):
            continue
        if "__pycache__" in path.parts or "pytest_cache" in path.parts:
            continue
        yield path


def defined_invariants(repo: Path) -> list:
    path = repo / "specs" / "INVARIANTS.md"
    if not path.is_file():
        return []
    return INV_DEF.findall(path.read_text(encoding="utf-8"))


def citations_by_area(repo: Path) -> dict:
    """{INV-NNN: {area: count}} across every readable file, INVARIANTS.md excluded.

    The definition file is excluded on purpose: it cites nearly every ID in its own
    cross-references, which would drown the signal this is here to give — who *outside*
    the ruleset depends on this rule.
    """
    found: dict = {}
    for area, rel in AREAS:
        for path in _iter_files(repo / rel):
            if path == repo / "specs" / "INVARIANTS.md":
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if IGNORE_MARKER in text:
                continue
            for ident in INV.findall(text):
                found.setdefault(ident, {}).setdefault(area, 0)
                found[ident][area] += 1
    return found


def spec_names(repo: Path) -> set:
    out = set()
    for path in (repo / "specs").glob("*.md"):
        if path.stem not in META_SPECS:
            out.add(path.stem)
    archive = repo / "specs" / "archive"
    if archive.is_dir():
        for path in archive.glob("*.md"):
            out.add(path.stem)
    return out


def declined_headings(repo: Path) -> set:
    """Spec names the maintainer decided not to build (`specs/DECLINED.md`).

    The second terminal state a spec can reach. Without it, a settled decision reads as
    outstanding work in every count that subtracts only `IMPLEMENTED.md` — which is how
    `implement-spec` came to re-offer a declined spec on every run before this existed.
    Absent file is not an error: the ledger is created on first use.
    """
    path = repo / "specs" / "DECLINED.md"
    if not path.is_file():
        return set()
    return {h.strip() for h in LEDGER_HEADING.findall(path.read_text(encoding="utf-8"))
            if not h.strip().startswith("<")}


def ledger_headings(repo: Path) -> set:
    path = repo / "specs" / "IMPLEMENTED.md"
    if not path.is_file():
        return set()
    return {h.strip() for h in LEDGER_HEADING.findall(path.read_text(encoding="utf-8"))
            if h.strip() != "<spec-name>"}


def invariant_sources(repo: Path) -> dict:
    """{INV-NNN: [spec names it cites as Source]}."""
    path = repo / "specs" / "INVARIANTS.md"
    if not path.is_file():
        return {}
    out: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = INV_DEF.match(line)
        if match:
            out[match.group(1)] = SOURCE.findall(line)
    return out


def feedback_state(repo: Path) -> tuple:
    """Archives, the ledger collapsed last-wins, and the raw line count.

    `PROCESSED.jsonl` is append-only and read **last-wins** — a disposition is
    corrected by appending a superseding line for the same `entry_id`, never by
    editing (see `feedback-to-issues/feedback_ledger.py`, which documents this and
    provides `annotate` to do it). So a reader that treats every line as a distinct
    entry reports the *superseded* value alongside the current one.

    That is not hypothetical: on 2026-07-31 this function returned raw lines, and
    `census` consequently reported one entry as having no disposition when the very
    next line in the ledger already carried the right spec. The compaction run chased
    the phantom and "fixed" it with a redundant no-op append. Collapse here, once, so
    no caller can make that mistake again.
    """
    base = repo / "feedback"
    archives = sorted(p.name for p in base.glob("*.md")) if base.is_dir() else []
    archives = [a for a in archives if a != "README.md"]
    ledger = base / "PROCESSED.jsonl"
    collapsed = {}
    lines = 0
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            lines += 1
            # Later lines win. An entry with no id cannot be superseded, so key it
            # by its own identity rather than dropping it.
            collapsed[record.get("entry_id") or ("\x00line%d" % lines)] = record
    return archives, list(collapsed.values()), lines


def cmd_census(args) -> int:
    repo = Path(args.repo).resolve()
    area = args.area
    defined = defined_invariants(repo)
    cited = citations_by_area(repo)

    if area in (None, "invariants"):
        print("== invariants: %d defined in specs/INVARIANTS.md\n" % len(defined))
        total = 0
        uncited = []
        for ident in defined:
            counts = cited.get(ident, {})
            n = sum(counts.values())
            total += n
            if n == 0:
                uncited.append(ident)
            elif args.verbose:
                where = ", ".join("%s:%d" % (a, c) for a, c in sorted(counts.items()))
                print("   %s  %3d  (%s)" % (ident, n, where))
        by_area: dict = {}
        for counts in cited.values():
            for a, c in counts.items():
                by_area[a] = by_area.get(a, 0) + c
        print("   live citations: %d" % total)
        for a in ("plugin", "specs", "tests", "skills"):
            if a in by_area:
                print("     %-8s %d" % (a, by_area[a]))
        print("\n   cited nowhere outside INVARIANTS.md: %d" % len(uncited))
        if uncited:
            print("     " + "  ".join(uncited))
            print("   ^ a prompt, not a verdict — see the skill's Step 2. An invariant may")
            print("     be enforced by a test that never names it, or be unenforceable by")
            print("     construction and still be the thing that stops the next mistake.")
        print("\n   NOT protected by this script: citations in commit messages "
              "(git history is immutable).")
        print()

    if area in (None, "specs"):
        specs = spec_names(repo)
        headings = ledger_headings(repo)
        declined = declined_headings(repo)
        # A spec has TWO terminal states. Counting a declined spec as unimplemented
        # reports settled work as outstanding, which is the same misreport `implement-spec`
        # Step 1 avoids by subtracting both ledgers.
        outstanding = specs - headings - declined
        print("== specs: %d files, %d ledger headings" % (len(specs), len(headings)))
        print("   headings with no spec file : %d" % len(headings - specs))
        print("   spec files not in ledger   : %d" % len(specs - headings))
        print("   declined (decided not to build): %d" % len(declined))
        print("   genuinely unimplemented    : %d" % len(outstanding))
        if args.verbose:
            for name in sorted(outstanding):
                print("     unimplemented: %s" % name)
            for name in sorted(declined):
                print("     declined:      %s" % name)
        print()

    if area in (None, "feedback"):
        archives, entries, lines = feedback_state(repo)
        superseded = lines - len(entries)
        print("== feedback: %d archived file(s), %d ledger entries%s"
              % (len(archives), len(entries),
                 " (%d lines; %d superseded by a later correction)" % (lines, superseded)
                 if superseded else ""))
        undisposed = [e for e in entries if not e.get("disposition")
                      or e.get("disposition") == "unrecorded"]
        print("   entries with no disposition: %d" % len(undisposed))
        for entry in undisposed:
            print("     %s  %s" % ((entry.get("entry_id") or "?")[:16],
                                   (entry.get("title") or "")[:58]))
        size = sum((repo / "feedback" / a).stat().st_size for a in archives) if archives else 0
        print("   archive size: %.1f KB" % (size / 1024.0))
        if size < 512 * 1024:
            print("   ^ below any sensible pruning threshold; report 'no action' rather")
            print("     than inventing work (skill Step 5).")
        print()
    return 0


def cmd_verify(args) -> int:
    repo = Path(args.repo).resolve()
    defined = set(defined_invariants(repo))
    problems = []

    # 1. Every cited invariant is defined. A citation of a non-existent ID is the
    #    signature of a botched merge or a half-finished renumber.
    for ident, counts in sorted(citations_by_area(repo).items()):
        if ident not in defined:
            where = ", ".join("%s:%d" % (a, c) for a, c in sorted(counts.items()))
            problems.append("undefined invariant %s cited in %s" % (ident, where))

    # 2. Every spec an invariant names as its Source resolves to a file.
    specs = spec_names(repo)
    for ident, sources in sorted(invariant_sources(repo).items()):
        for name in sources:
            if name not in specs and name not in ledger_headings(repo):
                problems.append("%s cites Source `%s`, which is neither a spec file nor a "
                                "ledger entry" % (ident, name))

    # 3. Duplicate invariant IDs — two definitions of one address.
    ids = defined_invariants(repo)
    seen = set()
    for ident in ids:
        if ident in seen:
            problems.append("duplicate definition of %s" % ident)
        seen.add(ident)

    # 4. Every archived feedback file has at least one ledger entry naming it.
    archives, entries, _lines = feedback_state(repo)
    archived_in_ledger = {e.get("archive") for e in entries if e.get("archive")}
    for name in archives:
        if name not in archived_in_ledger:
            problems.append("feedback archive %s has no PROCESSED.jsonl entry — pruning it "
                            "would lose the record that it was processed" % name)

    if problems:
        print("%d referential problem(s):\n" % len(problems))
        for line in problems:
            print("  - %s" % line)
        print("\nFix these before compacting further; a dangling reference now becomes an "
              "invisible one after the next move.")
        return 2
    print("clean: %d invariants defined, every citation resolves, every Source resolves, "
          "every feedback archive is in the ledger." % len(defined))
    print("Reminder: commit-message citations are outside this check and cannot be fixed.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    cen = sub.add_parser("census", help="what cites what")
    cen.add_argument("--area", choices=("invariants", "specs", "feedback"),
                     help="limit to one asset class")
    cen.add_argument("--verbose", action="store_true", help="per-invariant detail")
    cen.set_defaults(func=cmd_census)

    ver = sub.add_parser("verify", help="referential integrity; exit 2 if anything dangles")
    ver.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
