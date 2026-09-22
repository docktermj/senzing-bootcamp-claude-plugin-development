"""Every repository path named in `specs/INVARIANTS.md` resolves.

**INV-216** named `list_specs.py` by its full path and said it **MUST remain** there. Nothing
checked that the path existed. It could have been moved or deleted with the invariant still
asserting the old location, `citations.py verify` still clean, and every other guard green --
because none of them reads paths out of invariant prose. #113 is the case: the file did move,
by the maintainer's decision, and the only thing that would have caught a stale INV-216 was a
person re-reading it.

⛔ **Scope: paths naming files in THIS repository**, under `.claude/`, `tests/`, `plugins/` or
`specs/`. ⚠️ **`INVARIANTS.md` names many paths that are NOT ours** -- `config/bootcamp_progress.json`,
`docs/bootcamp_recap.md` and 34 others live in the **bootcamper's** project and cannot resolve
here. Requiring those would make the rule unkeepable, and a rule nobody can keep gets waived
rather than fixed. Measured 2026-09-22: 124 paths are ours, 36 are the bootcamper's.

⚠️ **A leading dot is matched deliberately.** The first draft of this pattern began
`[A-Za-z0-9_]`, which silently skipped **every** `.claude/` path -- three of them, including the
one this guard exists for. It reported a clean scan over a corpus with the subject removed,
which is the defect this repository keeps finding; `DotPathsAreNotSkipped` pins it.

⛔ **Append-only forces one exemption, and it is built so it cannot outlive its reason.**
INV-216's **2026-09-16** correction -- written before the move and uneditable, because
`INVARIANTS.md` never rewrites history -- quotes the old location as a backticked path. That
text cannot be changed, so the path cannot be made to resolve. `SUPERSEDED` lists it, and
`TheExemptionIsStillEarned` asserts **both** halves of its justification: the path is still
present in the register (a stale exemption fails) and it still does not resolve (an exemption
for a path that came back fails). An entry that stops being true stops being allowed.

⚠️ **A NEW correction must describe a superseded path, never quote it.** The 2026-09-22
correction says so in its own text and names the retired skill in prose instead. That keeps the
exemption list at one entry rather than growing one per move.

⚠️ **What this does NOT establish:** that the file at the path is the right file, that it does
what the invariant says, or that the invariant is still true. It establishes only that the
invariant is not pointing at nothing.

Source issue: #113.

Stdlib only; the register is read as text (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"

#: A backticked path with a file extension. ⛔ The leading `\.?` is load-bearing -- see above.
PATH = re.compile(r"`(\.?[A-Za-z0-9_][\w./-]*\.(?:py|md|sh|json|yaml|yml|txt|jsonl))`")

#: The roots this repository owns. Anything else named in the register belongs to the
#: bootcamper's project or to a sibling repository and cannot be resolved from here.
OURS = (".claude/", "tests/", "plugins/", "specs/")

#: Paths that CANNOT resolve and are allowed not to, each with the reason. ⛔ Only superseded
#: locations quoted inside a dated correction written BEFORE the move belong here -- that text
#: is uneditable under the register's append-only rule. Every entry is re-justified on each run
#: by `TheExemptionIsStillEarned`; none is taken on trust.
SUPERSEDED = {
    ".claude/skills/implement-spec/list_specs.py":
        "INV-216's 2026-09-16 correction, written before #113 moved the script to "
        "tests/list_specs.py; superseded by the 2026-09-22 correction beneath it",
}


def named_paths():
    return sorted(set(PATH.findall(INVARIANTS.read_text(encoding="utf-8"))))


def ours():
    return [p for p in named_paths() if p.startswith(OURS)]


class TheScanIsNotVacuous(unittest.TestCase):
    """INV-265 -- an empty corpus satisfies the resolution check trivially."""

    def test_paths_were_found_at_all(self):
        self.assertGreaterEqual(
            len(named_paths()), 50,
            "fewer than fifty paths parsed from %s; the pattern has drifted from the file and "
            "the check below proves nothing" % INVARIANTS)

    def test_our_own_paths_were_found(self):
        self.assertGreaterEqual(
            len(ours()), 50,
            "fewer than fifty of the paths named in %s are ours; the root list has drifted"
            % INVARIANTS)


class DotPathsAreNotSkipped(unittest.TestCase):
    """⛔ The first draft skipped every `.claude/` path and reported clean."""

    def test_a_dot_prefixed_path_is_matched(self):
        self.assertEqual(
            [".claude/commands/release.md"],
            PATH.findall("see `.claude/commands/release.md` for the rule"),
            "a path beginning with a dot was not matched, so the entire .claude/ surface is "
            "invisible to this guard")

    def test_the_register_actually_contains_dot_paths(self):
        """Pinning the pattern proves nothing if the corpus has none to find."""
        self.assertTrue(
            [p for p in ours() if p.startswith(".claude/")],
            "no .claude/ path is named in %s, so DotPathsAreNotSkipped tests a case the corpus "
            "does not contain and the guard's hardest half is unexercised" % INVARIANTS)


class EveryPathWeOwnResolves(unittest.TestCase):
    def test_no_invariant_names_a_file_that_is_not_there(self):
        missing = [p for p in ours()
                   if not (REPO_ROOT / p).exists() and p not in SUPERSEDED]
        self.assertEqual(
            [], missing,
            "specs/INVARIANTS.md names repository path(s) that do not exist: %s. Either the file "
            "moved and the invariant was not corrected, or the invariant is pointing at nothing. "
            "⛔ A superseded location must be DESCRIBED in a dated correction, never reproduced "
            "as a backticked path -- quoting it here makes this rule unkeepable"
            % ", ".join(missing))


class TheExemptionIsStillEarned(unittest.TestCase):
    """⛔ Each `SUPERSEDED` entry re-justifies itself, or it fails."""

    def test_every_exempted_path_is_still_in_the_register(self):
        named = set(named_paths())
        stale = sorted(p for p in SUPERSEDED if p not in named)
        self.assertEqual(
            [], stale,
            "path(s) are exempted that %s no longer names: %s. The correction quoting them is "
            "gone, so the exemption outlived its reason and is now hiding whatever else it "
            "matches" % (INVARIANTS, ", ".join(stale)))

    def test_no_exempted_path_has_come_back(self):
        back = sorted(p for p in SUPERSEDED if (REPO_ROOT / p).exists())
        self.assertEqual(
            [], back,
            "path(s) are exempted from resolving that DO resolve: %s. The file returned to its "
            "old location and the exemption is now excusing a path that needs no excuse"
            % ", ".join(back))


class TheBootcampersPathsAreNotOurs(unittest.TestCase):
    """The constructions that must NOT be required to resolve, pinned beside those that must."""

    def test_a_bootcamper_artifact_is_out_of_scope(self):
        for p in ("config/bootcamp_progress.json", "docs/bootcamp_recap.md"):
            with self.subTest(path=p):
                self.assertFalse(
                    p.startswith(OURS),
                    "%s is a file in the bootcamper's project; requiring it to resolve in this "
                    "repository would make the rule unkeepable" % p)

    def test_one_is_actually_named_in_the_register(self):
        self.assertTrue(
            [p for p in named_paths() if not p.startswith(OURS)],
            "the register names no out-of-scope path, so the exclusion above is untested")


if __name__ == "__main__":
    unittest.main()
