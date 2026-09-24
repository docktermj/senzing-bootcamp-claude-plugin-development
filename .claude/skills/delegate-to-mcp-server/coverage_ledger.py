#!/usr/bin/env python3
"""Ledger and inventory for the `delegate-to-mcp-server` sweep.

The sweep asks one question of every Senzing fact the SBCP holds: does the live MCP
server serve this now? Two things about that question make a ledger necessary rather
than nice.

**Most answers are "keep".** A site the server cannot serve, or can serve but should
not, is a real result that costs real calls to establish. A run that records only the
specs it produced throws that away, and the next run pays for it again — so every
verdict is recorded, keeps included.

**Answers expire when the server moves — on either of its two axes.** A verdict is
stamped with the ``server_version`` from ``get_capabilities`` *and* the ``index_built``
timestamp from a ``search_docs`` response, because those version different things and
move independently:

* ``server_version`` (e.g. ``1.32.2``) versions the MCP server software — its tools and
  their schemas;
* ``index_built`` (e.g. ``2026-07-29 11:11 UTC``) versions the **documentation corpus**
  those tools answer from.

Senzing can rebuild the index — new content, corrected content — and ship no server
release, so ``search_docs`` starts returning a different answer while ``server_version``
stays exactly where it was. A sweep that expired verdicts on the server version alone
would report "nothing to re-ask" for precisely the rows a re-index changed. Expiry is
therefore defined against **either** axis differing, and not against elapsed time: a run
on a server that has moved on neither axis has nothing to re-ask, which is what keeps
periodic runs cheap.

``index_built`` is optional on both ``record`` and ``stale``, because a caller may not
have a ``search_docs`` response to hand. When it is missing the index axis simply cannot
be checked — so every output path says so rather than reporting a clean bill (INV-163: a
check that did not run is reported as skipped, never described as verified).

Rows are keyed by a **stable slug describing the claim**, never by path or line. Files
get reorganized and line numbers churn constantly; a decision keyed to a location is
lost the first time someone moves a section, and the sweep silently re-litigates it.

The ledger is ``specs/mcp-coverage.jsonl`` — one JSON object per verdict, append-only
and read **last-wins**, so a verdict is revised by appending a superseding row with the
same key rather than by rewriting history.

Usage::

    coverage_ledger.py inventory [--repo <dir>] [--category <name>]
    coverage_ledger.py stale --server <version> [--index "<index_built>"] [--repo <dir>]
    coverage_ledger.py record --key <slug> --verdict <v> --server <version>
                             [--index "<index_built>"] [...]
    coverage_ledger.py summary [--repo <dir>]

``inventory`` greps the plugin for Senzing-fact leads and prints them grouped by
category; it writes nothing and is a lead generator, not a verdict — regex cannot tell a
cached authority from a worked illustration. ``stale`` lists the keys whose verdict was
reached against a different server version. ``record`` appends one verdict. ``summary``
reports counts by verdict and the newest server version seen.

Exit codes: 0 success, 1 bad input, 3 nothing to do (``stale`` found no expired rows).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

LEDGER = Path("specs") / "mcp-coverage.jsonl"
PLUGIN = Path("plugins") / "senzing-bootcamp"
INVARIANTS = Path("specs") / "INVARIANTS.md"

VERDICTS = (
    "delegate",
    "contradicted",
    "retire-workaround",
    "keep-server-lacks-it",
    "keep-by-design",
    "not-a-senzing-fact",
)

# A keep whose reason is not recorded is indistinguishable from "nobody looked", so the
# next sweep re-litigates it — which is the cost this ledger exists to avoid.
REASON_REQUIRED = ("keep-by-design",)

# Lead patterns per category. Deliberately over-broad: a missed site is invisible, a
# false lead costs one read. The owning MCP tool is carried here so the report can name
# it without the caller re-deriving the routing table from SKILL.md.
PATTERNS = (
    ("attributes", r"\b(?:NAME_ORG|NAME_FULL|RECORD_TYPE|DATA_SOURCE|RECORD_ID)\b",
     "search_docs(category='data_mapping')"),
    ("flags", r"\bSZ_[A-Z][A-Z0-9_]{4,}\b",
     "get_sdk_reference(topic='flags')"),
    ("error-codes", r"\bSENZ-?\d{4}\b",
     "explain_error_code"),
    ("sdk-shapes", r"\b(?:search_by_attributes|get_entity_by_entity_id|find_network_by_entity_id|"
                   r"add_record|export_json_entity_report|why_entities|how_entity_by_entity_id|"
                   r"register_data_source|init_default_config)\b",
     "get_sdk_reference(topic='parameters', language=…)"),
    ("install-config", r"SENZING_[A-Z_]+|senzingsdk-[a-z]+|apt\.senzing\.com|\bSUPPORTPATH\b",
     "sdk_guide(topic='install' | 'configure')"),
    ("dated-claims", r"(?:MCP )?server \d+\.\d+\.\d+|verified \d{4}-\d{2}-\d{2}",
     "whichever tool owns the claim"),
)

# An invariant that asserts a server *limitation* is the highest-risk category: tests pin
# it, specs cite it, and it shapes future work — so when the server gains the ability, the
# false premise is load-bearing in a way ordinary stale prose is not.
LIMITATION_PATTERN = re.compile(
    r"\b(?:cannot|can not|does not|doesn't|no longer|never returns|is not able|unobtainable|"
    r"not documented|empty|fails|rejects)\b",
    re.IGNORECASE,
)


def read_ledger(repo: Path) -> dict:
    """Every key's current verdict, last-wins. Malformed lines are skipped, not fatal:
    a hand-edited ledger must still answer for the rows that are intact."""
    path = repo / LEDGER
    rows: dict = {}
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        key = row.get("key")
        if key:
            rows[key] = row
    return rows


def iter_markdown(repo: Path):
    """The maintained Senzing-guidance surface, plus INVARIANTS.md.

    `docs/examples/` is excluded on purpose: the example recap is a rendered record of
    one past run, not a claim the plugin asserts. Its Senzing content describes what a
    Bootcamper was told on a particular day, so "the server serves this now" is not a
    reason to touch it — and it is dense enough with attribute names to bury the real
    work-list. Other `specs/*.md` are excluded for the same reason: history, not
    shipped guidance. `INVARIANTS.md` is the exception, because an invariant asserting a
    server limitation is load-bearing (tests pin it, specs cite it) in a way an archived
    spec is not.
    """
    base = repo / PLUGIN
    if base.is_dir():
        for path in sorted(base.rglob("*.md")):
            if "__pycache__" in path.parts or "pytest_cache" in path.parts:
                continue
            if "examples" in path.relative_to(base).parts:
                continue
            yield path
    invariants = repo / INVARIANTS
    if invariants.is_file():
        yield invariants


def inventory(repo: Path, only: str = None) -> list:
    """Grep the plugin and specs for Senzing-fact leads."""
    compiled = [(name, re.compile(pat), tool) for name, pat, tool in PATTERNS]
    hits = []
    for path in iter_markdown(repo):
        rel = path.relative_to(repo).as_posix()
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        is_invariants = rel == INVARIANTS.as_posix()
        for number, line in enumerate(lines, 1):
            for name, pattern, tool in compiled:
                if only and name != only:
                    continue
                match = pattern.search(line)
                if match:
                    hits.append({
                        "category": name,
                        "where": "%s:%d" % (rel, number),
                        "match": match.group(0),
                        "tool": tool,
                        "line": line.strip()[:160],
                    })
                    break
            else:
                # Only reached when no pattern matched: an invariant asserting a server
                # limitation carries no Senzing token of its own, so it needs its own pass.
                if is_invariants and only in (None, "server-limitation"):
                    if line.lstrip().startswith("- **INV-") and LIMITATION_PATTERN.search(line):
                        label = re.search(r"INV-\d{3}", line)
                        hits.append({
                            "category": "server-limitation",
                            "where": "%s:%d" % (rel, number),
                            "match": label.group(0) if label else "INV-???",
                            "tool": "whichever tool owns the claim",
                            "line": line.strip()[:160],
                        })
    return hits


def cmd_inventory(args) -> int:
    repo = Path(args.repo).resolve()
    known = read_ledger(repo)
    hits = inventory(repo, args.category)
    if not hits:
        print("no leads found — check --category, or the globs have drifted")
        return 1
    by_category: dict = {}
    for hit in hits:
        by_category.setdefault(hit["category"], []).append(hit)
    sites = {(h["category"], h["where"].rsplit(":", 1)[0]) for h in hits}
    print("%d leads in %d files across %d categories (ledger holds %d keys)\n"
          % (len(hits), len({s[1] for s in sites}), len(by_category), len(known)))
    for name in sorted(by_category):
        rows = by_category[name]
        print("== %s (%d leads) — owning tool: %s" % (name, len(rows), rows[0]["tool"]))
        # Grouped per file: one site to read, not one line per mention. A file naming
        # the same attribute nine times is one decision, not nine.
        per_file: dict = {}
        for hit in rows:
            per_file.setdefault(hit["where"].rsplit(":", 1)[0], []).append(hit)
        for path in sorted(per_file):
            group = per_file[path]
            tokens = sorted({h["match"] for h in group})
            shown = ", ".join(tokens[:6]) + ("…" if len(tokens) > 6 else "")
            print("   %-72s %2d  %s" % (path, len(group), shown))
            if args.verbose:
                for hit in group:
                    print("        %s  %s" % (hit["where"], hit["line"]))
        print()
    print("Leads, not verdicts: read each site before classifying it.\n"
          "Line-level detail: --verbose. One category: --category <name>.")
    return 0


def expiry_reason(row: dict, server: str, index: str = None) -> str:
    """Why this row needs re-asking, or "" if it does not.

    Two axes, checked independently. The index axis is skipped entirely when the caller
    has no `index_built` to compare against — but a row that predates index stamping
    cannot be *proved* current once one is supplied, so it expires rather than passing
    by default. Unknown provenance is a reason to look, not a reason to skip.
    """
    if row.get("server_version") != server:
        return "server %s -> %s" % (row.get("server_version", "?"), server)
    if index:
        recorded = row.get("index_built")
        if not recorded:
            return "index build not recorded when this verdict was reached"
        if recorded != index:
            return "docs re-indexed %s -> %s" % (recorded, index)
    return ""


def produced_by(row):
    """What this verdict produced, whichever era recorded it.

    ⚠️ Two field names, one meaning. Rows written before #114 carry `spec` (a path under
    the now-frozen archive); rows written since carry `issue` (a number). ⛔ **A row is
    never migrated** — the ledger is append-only and read last-wins, so rewriting history
    is the one thing its shape forbids. Returns None where the verdict produced neither,
    which is the normal case for a `keep-*` row.
    """
    if row.get("issue"):
        return "#%s" % row["issue"]
    if row.get("spec"):
        return "%s (pre-#114 spec)" % row["spec"]
    return None


def cmd_stale(args) -> int:
    repo = Path(args.repo).resolve()
    rows = read_ledger(repo)
    index = (args.index or "").strip() or None
    # INV-163: a check that could not run is reported as skipped, never as passed.
    caveat = ("" if index else
              "\n⚠  --index not supplied: the documentation corpus is versioned separately\n"
              "   from the server (search_docs -> metadata.index_built) and moves without a\n"
              "   server release. The index axis was NOT checked; this is a partial result.")
    if not rows:
        print("ledger is empty — every site is unexamined; start from `inventory`" + caveat)
        return 3
    stale = []
    for row in rows.values():
        reason = expiry_reason(row, args.server, index)
        if reason:
            stale.append((row, reason))
    if not stale:
        if index:
            print("all %d ledger rows were decided against server %s and docs indexed %s —\n"
                  "nothing expired. A server that has moved on neither axis cannot have started\n"
                  "serving anything new; this run is limited to sites with no ledger row at all."
                  % (len(rows), args.server, index))
        else:
            print("all %d ledger rows were decided against server %s — nothing expired on the\n"
                  "one axis that was checked. Sites with no ledger row at all still need work."
                  % (len(rows), args.server) + caveat)
        return 3
    # A gap the plugin is paying to fill is the most valuable thing to re-ask, so it leads.
    order = {"keep-server-lacks-it": 0, "keep-by-design": 1, "retire-workaround": 2}
    stale.sort(key=lambda pair: (order.get(pair[0].get("verdict"), 9), pair[0].get("key", "")))
    print("%d of %d rows need re-asking (now server %s%s):\n"
          % (len(stale), len(rows), args.server,
             ", docs indexed %s" % index if index else ""))
    for row, reason in stale:
        print("  %-28s %-22s decided %s" % (row.get("key", "?"), row.get("verdict", "?"),
                                            row.get("checked", "?")))
        print("      expired: %s" % reason)
        if row.get("claim"):
            print("      claim:   %s" % row["claim"])
        produced = produced_by(row)
        if produced:
            print("      produced: %s" % produced)
    print(caveat.lstrip("\n") if caveat else "", end="\n" if caveat else "")
    return 0


def cmd_record(args) -> int:
    repo = Path(args.repo).resolve()
    if args.verdict not in VERDICTS:
        print("unknown verdict %r; expected one of: %s" % (args.verdict, ", ".join(VERDICTS)),
              file=sys.stderr)
        return 1
    if args.verdict in REASON_REQUIRED and not args.reason:
        print("verdict %r requires --reason: an unreasoned keep is indistinguishable from\n"
              "'nobody looked', and the next sweep will re-litigate it." % args.verdict,
              file=sys.stderr)
        return 1
    row = {
        "key": args.key,
        "verdict": args.verdict,
        "server_version": args.server,
        "checked": args.checked or date.today().isoformat(),
    }
    index = (getattr(args, "index", None) or "").strip()
    if index:
        row["index_built"] = index
    for name in ("where", "claim", "reason", "tool", "upstream"):
        value = getattr(args, name, None)
        if value:
            row[name] = value
    # ⛔ `spec` is READ but never written (#114). This skill files GitHub issues now, and
    # 29 historical rows carry `spec` from the runs before that. Rewriting them would edit
    # an append-only ledger, so they keep their provenance and `produced_by()` reads both.
    if getattr(args, "issue", None):
        row["issue"] = args.issue
    path = repo / LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_ledger(repo).get(args.key)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    if existing:
        print("recorded %s = %s (supersedes %s at server %s)"
              % (args.key, args.verdict, existing.get("verdict"),
                 existing.get("server_version")))
    else:
        print("recorded %s = %s" % (args.key, args.verdict))
    if not index:
        print("  note: no --index recorded, so this verdict cannot be proved current\n"
              "  against a later docs re-index and will expire on the next check that\n"
              "  supplies one (search_docs -> metadata.index_built).")
    return 0


def cmd_summary(args) -> int:
    repo = Path(args.repo).resolve()
    rows = read_ledger(repo)
    if not rows:
        print("ledger is empty (%s not written yet)" % LEDGER.as_posix())
        return 0
    counts: dict = {}
    versions: dict = {}
    indexes: dict = {}
    for row in rows.values():
        counts[row.get("verdict", "?")] = counts.get(row.get("verdict", "?"), 0) + 1
        version = row.get("server_version", "?")
        versions[version] = versions.get(version, 0) + 1
        built = row.get("index_built", "(not recorded)")
        indexes[built] = indexes.get(built, 0) + 1
    print("%d keys in %s\n" % (len(rows), LEDGER.as_posix()))
    for verdict in VERDICTS:
        if verdict in counts:
            print("  %-22s %d" % (verdict, counts[verdict]))
    for verdict, count in sorted(counts.items()):
        if verdict not in VERDICTS:
            print("  %-22s %d  (unrecognized)" % (verdict, count))
    print("\nserver versions represented:")
    for version in sorted(versions):
        print("  %-10s %d row(s)" % (version, versions[version]))
    print("\ndocs index builds represented:")
    for built in sorted(indexes):
        print("  %-24s %d row(s)" % (built, indexes[built]))
    if "(not recorded)" in indexes:
        print("  ^ these expire on the next check that supplies --index: a verdict with no\n"
              "    index provenance cannot be proved current against a docs re-index.")
    gaps = [r for r in rows.values() if r.get("verdict") == "keep-server-lacks-it"]
    if gaps:
        print("\n%d open coverage gap(s) — the plugin is paying to fill these:" % len(gaps))
        for row in sorted(gaps, key=lambda r: r.get("key", "")):
            sent = row.get("upstream")
            print("  %-28s %s" % (row.get("key", "?"), sent or "not reported upstream"))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("inventory", help="grep the plugin for Senzing-fact leads")
    inv.add_argument("--category", help="limit to one category")
    inv.add_argument("--verbose", action="store_true", help="every matching line, not per-file counts")
    inv.set_defaults(func=cmd_inventory)

    old = sub.add_parser("stale", help="rows decided against a different server or docs index")
    old.add_argument("--server", required=True, help="current get_capabilities server_version")
    old.add_argument("--index", help="current search_docs metadata.index_built; omitting it "
                                     "leaves the index axis unchecked and says so")
    old.set_defaults(func=cmd_stale)

    rec = sub.add_parser("record", help="append one verdict")
    rec.add_argument("--key", required=True, help="stable slug describing the claim")
    rec.add_argument("--verdict", required=True, choices=VERDICTS)
    rec.add_argument("--server", required=True, help="server_version this was decided against")
    rec.add_argument("--index", help="search_docs metadata.index_built at decision time")
    rec.add_argument("--where", help="path (orientation only; keys are not paths)")
    rec.add_argument("--claim", help="one line: what the SBCP asserts or holds")
    rec.add_argument("--reason", help="required for keep-by-design: the Step 6 test that failed")
    rec.add_argument("--tool", help="the MCP call that established the verdict")
    rec.add_argument("--issue", type=int,
                     help="GitHub issue number this produced, e.g. 142")
    rec.add_argument("--upstream", help="e.g. 'feature sent 2026-07-30'")
    rec.add_argument("--checked", help="ISO date (default: today)")
    rec.set_defaults(func=cmd_record)

    tot = sub.add_parser("summary", help="counts by verdict, versions, and open gaps")
    tot.set_defaults(func=cmd_summary)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
