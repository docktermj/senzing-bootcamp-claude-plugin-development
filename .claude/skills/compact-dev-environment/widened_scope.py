#!/usr/bin/env python3
"""Report invariants whose scope a later invariant widened without a pointer back.

`INVARIANTS.md` normally annotates the **earlier** rule when a later one widens its scope —
INV-083 carries "See INV-089 before implementing", INV-101 carries "Read INV-195 first". That
matters because the narrower rule is the one an implementer reaches first: it names the
concrete files, constants or artifacts, so a widening recorded only on the wider rule is
unreachable from where the work actually starts. INV-107 was the sharp case — it enumerated
two generators, and that exact wording is what let a third drift out of scope until INV-184
was needed.

⚠️ **This shortlists; it does not decide. Read every hit before counting one.**

On 2026-08-12 this reported **17** candidates, of which **15 were false positives** — sentences
naming an ID precisely to record that it is *unchanged* ("INV-041's and INV-042's exemptions
are unaffected", "INV-070/INV-071 still apply", "the guarantee remains INV-077"). A directional
verb near an ID means the sentence is *about* the relationship, not that the relationship is a
defect. Relaying this list as findings is how a clean result gets reported as a backlog.

⚠️ **It also has false NEGATIVES, and one of them was the case that mattered most.** This
scan would **not** have found INV-107 → INV-184, the sharper of the two 2026-08-12 findings.
It keys on a scope verb near an ID, and INV-184 states the widening without one: *"INV-107
named two generators; the property belongs to the pattern, and the third … drifted out of
scope unnoticed."* No "supersedes", no "generalizes" — so nothing matched, and that pair was
found by reading INV-184, not by running this. Treat a clean run as "nothing matched these
verbs", never as "no instance exists"; a widening described in plain prose is invisible here.

Why it is a report and not a test: the false-positive rate makes it unassertable, and a
genuinely one-way link is often correct — "extends INV-115 to profiling" leaves INV-115 wholly
true in its own domain, so no back-pointer is owed. Only a **scope widening** owes one, and
telling the two apart requires reading the sentence.

Its standing use is the revisit trigger for the stop-marker held on 2026-08-12 (see
`specs/generalized-invariants-leave-no-pointer-on-the-narrower-rule.md`): at a **third**
genuine instance, the candidate rule should become an invariant. Run it after
`/review-invariants` registers or amends an invariant that supersedes or generalizes another,
since that skill is the only writer of `specs/INVARIANTS.md` (INV-365).

Usage::

    widened_scope.py [--repo <dir>] [--all-verbs]

`--all-verbs` widens the scan to "extends"/"hardens"/"complements" as well, which is much
noisier and almost never what you want; the default is scope-changing verbs only.

Exits 0 always — it is a report, and a hit is not a defect.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# One entry: "- **INV-nnn** — body", body running to the next entry or heading.
ENTRY = re.compile(r"^- \*\*(INV-\d{3})\*\* — (.+?)(?=\n- \*\*INV-|\n##|\Z)", re.M | re.S)
IDENT = re.compile(r"INV-\d{3}")

# Verbs that mean "this invariant changes how you must read that one". Deliberately excludes
# "extends"/"hardens"/"complements": those leave the earlier rule true in its own domain, so
# no forward pointer is owed and including them buries the signal.
SCOPE_VERBS = ("supersed", "generalis", "generaliz", "amends", "restates",
               "replaces", "reverses", "retiring", "retires", "widens", "widened")
EXTRA_VERBS = ("extends", "hardens", "complements", "constrains", "corrects")


def entries(repo: Path) -> dict:
    path = repo / "specs" / "INVARIANTS.md"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    return {k: re.sub(r"\s+", " ", v.replace("**", "")) for k, v in ENTRY.findall(text)}


def one_way_links(bodies: dict, verbs: tuple) -> list:
    """(earlier, later, the sentence that names it) where `earlier` never names `later`."""
    out, seen = [], set()
    for later, body in bodies.items():
        for sentence in re.split(r"(?<=[.)]) ", body):
            if not any(v in sentence.lower() for v in verbs):
                continue
            for earlier in sorted(set(IDENT.findall(sentence))):
                if earlier == later or earlier not in bodies:
                    continue
                if later in bodies[earlier] or (earlier, later) in seen:
                    continue
                seen.add((earlier, later))
                out.append((earlier, later, sentence.strip()))
    return sorted(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root (default: cwd)")
    parser.add_argument("--all-verbs", action="store_true",
                        help="also scan extends/hardens/complements (much noisier)")
    args = parser.parse_args(argv)

    bodies = entries(Path(args.repo).resolve())
    if not bodies:
        print("no invariants parsed — is --repo the repository root?")
        return 0

    verbs = SCOPE_VERBS + EXTRA_VERBS if args.all_verbs else SCOPE_VERBS
    rows = one_way_links(bodies, verbs)

    print("== %d invariants scanned; %d candidate one-way link(s) ==\n"
          % (len(bodies), len(rows)))
    for earlier, later, sentence in rows:
        print("  %s  <-- named by %s" % (earlier, later))
        print("      %s\n" % (sentence[:200] + ("…" if len(sentence) > 200 else "")))

    print("^ CANDIDATES, not findings. Most are sentences naming an ID to say it is")
    print("  UNCHANGED — 15 of 17 were exactly that on 2026-08-12. Open each one and read")
    print("  it; count a hit only where the earlier rule, read alone, would now be")
    print("  implemented too narrowly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
