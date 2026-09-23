#!/usr/bin/env python3
"""Compare the SHARED-RULES block between this repository's skills and their user-level twins.

⛔ **Why this exists.** `implement-github-issue` has two `SKILL.md` files -- one here, one under
`~/.claude/skills/` used across the maintainer's other repositories -- and on 2026-09-23 they
were found two amendments apart. #119 and #124 edited only the user-level copy while the
repository's copy, the one that ships to the child ports, sat at its original text. Nothing
detected it, and the repository copy carried a note asserting it governed, which was false.

⚠️ **This reduces the window; it does not close it.** Two blind spots, both reported on every
run rather than left for the reader to infer (INV-308):

* a commit made in a terminal outside a Claude Code session triggers no hook here;
* an edit to a **user-level** copy produces no repository event at all, so nothing in this
  repository can observe it until something runs this.

⚠️ **Only the delimited block is compared.** Everything outside `SHARED-RULES` may legitimately
differ: this repository's copy cites `docs/FAMILY_WORKFLOW.md` and `specs/INVARIANTS.md`, which
do not exist in the repositories the user-level copy serves. Requiring the files to be identical
would either break the user-level copy elsewhere or strip the citations that make the rule
enforceable here.

Usage:
    python3 .claude/skills/check-skill-drift/skill_drift.py           # report, exit 0 unless drift
    python3 .claude/skills/check-skill-drift/skill_drift.py --quiet   # print only on drift

Exit codes:  0 = no drift found (or nothing comparable)   1 = the blocks differ
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
USER_SKILLS = Path.home() / ".claude" / "skills"

#: The delimited span. ⛔ Non-greedy and DOTALL: the block spans many lines and a greedy match
#: over a file with two blocks would swallow everything between them.
BLOCK = re.compile(r"<!-- SHARED-RULES:BEGIN.*?<!-- SHARED-RULES:END -->", re.S)


def shared_block(path):
    """The SHARED-RULES span of `path`, or None when the file or the block is absent."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = BLOCK.search(text)
    return m.group(0) if m else None


def paired_skills():
    """[(name, repo_path, user_path)] for every repo skill that has a user-level twin by name."""
    out = []
    repo_skills = REPO_ROOT / ".claude" / "skills"
    for d in sorted(p for p in repo_skills.iterdir() if p.is_dir()):
        repo_file = d / "SKILL.md"
        user_file = USER_SKILLS / d.name / "SKILL.md"
        if repo_file.is_file() and user_file.is_file():
            out.append((d.name, repo_file, user_file))
    return out


def compare():
    """(drifted, checked, unpaired) -- unpaired is what could NOT be compared, and why."""
    drifted, checked, unpaired = [], [], []
    for name, repo_file, user_file in paired_skills():
        a, b = shared_block(repo_file), shared_block(user_file)
        if a is None or b is None:
            which = " and ".join(w for w, v in (("this repo's copy", a), ("the user-level copy", b))
                                 if v is None)
            unpaired.append((name, "no SHARED-RULES block in %s" % which))
            continue
        checked.append(name)
        if a != b:
            drifted.append((name, hashlib.md5(a.encode()).hexdigest()[:8],
                            hashlib.md5(b.encode()).hexdigest()[:8]))
    return drifted, checked, unpaired


def blind_spots():
    """Print what the run could not see.

    ⛔ Called on EVERY non-quiet path, including the one where nothing was compared at all.
    The first version returned early when `~/.claude/skills` was absent and printed this
    nowhere -- omitting the disclosure exactly on the machine that checked nothing, which is
    the INV-308 failure this script exists to avoid. CI caught it; the local run could not,
    because that directory exists there (#128).
    """
    print("\n⚠️  What this run could NOT see, stated rather than implied:")
    print("   · a commit made outside a Claude Code session triggers no hook here;")
    print("   · an edit to a user-level copy produces no repository event at all.")
    print("   This narrows the window. It does not close it.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quiet", action="store_true", help="print only when drift is found")
    args = ap.parse_args(argv)

    if not USER_SKILLS.is_dir():
        if not args.quiet:
            print("⚠️  %s does not exist on this machine, so NOTHING was compared." % USER_SKILLS)
            print("   That is 'could not check', not 'nothing to check' — a CI runner sees this.")
            blind_spots()
        return 0

    drifted, checked, unpaired = compare()

    if drifted:
        print("⛔ SHARED-RULES drift, %d skill(s):" % len(drifted))
        for name, a, b in drifted:
            print("   %-28s repo %s  !=  user-level %s" % (name, a, b))
        print("   Edit one, carry it across by hand, and re-run. The block is meant to be")
        print("   byte-identical; everything outside it may legitimately differ.")
    elif not args.quiet:
        print("✅ SHARED-RULES identical in %d paired skill(s): %s"
              % (len(checked), ", ".join(checked) or "—"))

    if unpaired and not args.quiet:
        print("⚠️  %d paired skill(s) carry no SHARED-RULES block and were NOT compared:"
              % len(unpaired))
        for name, why in unpaired:
            print("   %-28s %s" % (name, why))

    if not args.quiet:
        blind_spots()

    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
