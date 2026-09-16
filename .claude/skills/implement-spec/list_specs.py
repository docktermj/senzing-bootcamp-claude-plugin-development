#!/usr/bin/env python3
"""Compute the unimplemented-spec candidate set: candidates − implemented − declined.

`implement-spec`'s Step 3 has always stated this correctly, including why the declined set must
be subtracted — *"Omitting the declined set re-offers a spec the maintainer has already ruled
out, every run."* It was still done by hand, four prose steps at a time, and on 2026-08-13 a
run subtracted only `IMPLEMENTED.md`: it reported a **declined** spec as open, recommended it
to the maintainer, and implemented it. `tests/test_declined_ledger.py` caught the contradiction
after the fact; nothing caught the listing.

So this exists for the same reason `citations.py verify` does — the repo's own conclusion that
where care is the only safeguard, care eventually fails (INV-207). Prose explains *why* the
declined set is subtracted; this does the subtracting.

Two states are terminal and both are subtracted:

``IMPLEMENTED.md``
    The spec was built. Its ledger entry is the record of what was done.

``DECLINED.md``
    The maintainer ruled it out. The spec file stays, because its analysis is usually still
    worth reading — which is exactly what makes it dangerous to re-offer: the file argues *for*
    the change and only the ledger records the argument against.

Also reports the one condition a hand count hides: **in both ledgers** — a spec implemented *and*
declined. That is never a clean subtraction; it means one of the two records is wrong. Reported
separately rather than silently subtracted twice.

⚠️ A ledger heading with **no spec file** is deliberately NOT reported. It is the normal shape
for an audit or dry run recorded straight into `IMPLEMENTED.md` (23 of them here:
`deep-dive-audit-*`, `production-readiness-audit-*`, `dry-run-*`), which is why
`coverage_reports.py` skips the same case with the comment "audits recorded with no spec". A
first draft flagged them as probable renames and produced 23 false alarms on a clean repo — and a
guard that cries wolf on correct data trains its reader to skim past the one line that matters.

Read-only, stdlib-only, platform-independent (INV-052/INV-108). Exit status is 0 whatever it
finds when listing; ``--check`` exits 2 if a spec is in both ledgers, for use in a pipeline.

    python3 .claude/skills/implement-spec/list_specs.py
    python3 .claude/skills/implement-spec/list_specs.py --repo /path/to/repo
    python3 .claude/skills/implement-spec/list_specs.py --check
"""
import argparse
import os
import re
import sys

#: Meta files under `specs/` that are not specs. `README` joined them when `specs/` was
#: frozen (#52): it is the freeze notice, and without it here the notice reports itself as
#: the one open spec candidate in an archive that is closed to new work.
META = {"IMPLEMENTED", "INVARIANTS", "DECLINED", "todo", "README"}
#: A ledger entry heading: `## <spec-name>`, one token, no spaces.
LEDGER_HEAD = re.compile(r"^## (\S+)\s*$", re.M)


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _headings(repo, name):
    """The `## <name>` headings in a ledger, minus template placeholders.

    The scaffold in both ledgers carries a literal `## <spec-name>` example. Angle brackets are
    the tell, and dropping them keeps the counts honest — a placeholder counted as an entry
    inflates 'implemented' and hides a real gap by one.
    """
    text = _read(os.path.join(repo, "specs", name))
    return {h for h in LEDGER_HEAD.findall(text) if "<" not in h and ">" not in h}


def candidates(repo):
    """Spec names under `specs/`, excluding the meta files."""
    specs_dir = os.path.join(repo, "specs")
    if not os.path.isdir(specs_dir):
        return set()
    out = set()
    for name in sorted(os.listdir(specs_dir)):
        if name.endswith(".md"):
            stem = name[:-3]
            if stem not in META:
                out.add(stem)
    return out


def compute(repo):
    """(open, implemented, declined, both) — every set the listing needs.

    Intersected with `cand` throughout, so ledger entries with no spec file (audits, dry runs)
    are excluded from the counts rather than inflating them.
    """
    cand = candidates(repo)
    impl = _headings(repo, "IMPLEMENTED.md")
    decl = _headings(repo, "DECLINED.md")
    both = sorted((impl & decl) & cand)
    open_ = sorted(cand - impl - decl)
    return open_, sorted(impl & cand), sorted(decl & cand), both


def report(repo):
    open_, impl, decl, both = compute(repo)
    print("== Unimplemented specs (candidates - implemented - declined) ==")
    print("specs: %d   implemented: %d   declined: %d   open: %d"
          % (len(candidates(repo)), len(impl), len(decl), len(open_)))
    print()
    if both:
        print("⛔ IN BOTH LEDGERS — one of the two records is wrong, and this is NOT a clean")
        print("   subtraction. Resolve before treating the open set as trustworthy:")
        for name in both:
            print("     %s" % name)
        print()
    if not open_:
        print("  (none open — every spec has reached a terminal state)")
    else:
        for name in open_:
            print("  %s" % name)
    print()
    print("⛔ A DECLINED spec is not a candidate. Its file stays because the analysis is usually")
    print("   still worth reading — which is what makes re-offering it easy: the spec argues FOR")
    print("   the change and only the ledger records the argument against. Check DECLINED.md's")
    print("   `Revisit if:` clause before reopening one, and re-verify the condition rather than")
    print("   trusting the spec's original citations.")
    return both


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.getcwd(), help="repo root (default: current directory)")
    ap.add_argument("--check", action="store_true",
                    help="exit 2 if any spec is in both ledgers")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, "specs")):
        sys.stderr.write("no specs/ under %s — pass --repo\n" % repo)
        return 2
    both = report(repo)
    return 2 if (args.check and both) else 0


if __name__ == "__main__":
    sys.exit(main())
