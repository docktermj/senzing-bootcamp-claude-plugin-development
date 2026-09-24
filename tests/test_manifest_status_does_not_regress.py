"""No invariant newly becomes `status: unclear` in the published manifest.

`invariant-manifest.json` is what downstream ports read for dual-evaluation, and
`docs/development.md` states what `unclear` means to them: a child **cannot tell whether an
invariant it inherited is still in force**. So an invariant sliding from `active` to `unclear`
degrades a published artifact four repositories consume.

⛔ **That happened, and nothing caught it (#122).** #113's dated correction under INV-216 wrote
*"a superseded location quoted as a path"* -- where *superseded location* meant the script's old
file path and said nothing about the invariant's status. `SUPERSESSION_WORDS` matched
`supersede` inside it, no `superseded by INV-nnn` was present, and `status_of()` returned
`unclear`. **The function is right to refuse to guess**; the defect was in the prose it read.
INV-216 -- active, binding and freshly amended -- read to every child as undecidable, and the
count went 33 to 34.

⚠️ **`invariant_manifest.py --check` passed throughout**, correctly: it verifies the manifest
**matches the prose**, and the prose really did contain that word. It has no notion of a status
getting *worse*. Nothing else looked, so a regression in a published field was invisible to
every guard in the repository.

⛔ **A SET, not a count.** This repository refuses counts in prose because they go stale silently
while reading authoritative (`NoCountIsStated`, and INV-302's guards). A pinned set names *which*
invariants are undecidable, so a diff means something:

* no id may **join** it without a deliberate, named edit to this file;
* an id may **leave** once its prose is resolved so it is no longer `unclear`.

⚠️ **The permit and the condition retire together, and the order matters.** Removing an id from
this set while the manifest still reports it `unclear` fails -- correctly: that withdraws the
permission without fixing anything. A negative control pins that distinction, because the
looser reading ("shrinkage is always safe") is the one a later editor will reach for.

⛔ **The set is now EMPTY, and clearing it is what re-armed this guard (#141).** #112 resolved
all 33 entries and did not clear the pin, so every one became a **stale permit** -- and a stale
permit, as this docstring already said, *only ever permits and never forbids, so it does not
fail*. The arithmetic: `unclear_ids()` returned the empty set while `KNOWN_UNCLEAR` still held
33 ids, so `unclear_ids() - KNOWN_UNCLEAR` was empty **whatever happened to those 33**. Any of
them could have regressed to `unclear` with the suite green. ⚠️ **This is the shape a successful
fix leaves behind:** nothing failed, nothing looked wrong, and the guard protecting a published
field had been disarmed by the very work it was holding the line for.

⚠️ **A pin naming an id the register no longer defines still fails**, because that means the set
was never re-read. With the set empty that check is vacuous, and it is kept for the moment an id
is added back rather than deleted as dead.

⚠️ **What this does NOT establish:** that `status_of()` reads any invariant the way a human
would, nor that an `active` classification is *correct* -- only that no invariant has become
undecidable since the pin was cleared. The manifest agreeing with the prose is
`invariant_manifest.py --check`'s job, and it has no notion of a status getting worse.

Source issues: #122 (original), #141 (the pin cleared and the guard re-armed).

Stdlib only; the manifest is read as JSON (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "invariant-manifest.json"

#: The invariants whose supersession status the prose genuinely leaves undecidable.
#:
#: ⛔ **EMPTY, and that is the enforced state (#141).** #112 resolved all 33 entries this set
#: was created to permit, so every one of them is now `active` or `superseded` in the manifest.
#: An empty pin makes the check below forbid `unclear` outright, which is the strongest form it
#: has ever had -- NOT a vacuous one. Adding an id back re-permits an invariant a child cannot
#: evaluate; it is a deliberate act, must be justified in the commit that does it, and must
#: also update `test_an_empty_pin_is_the_intended_state`, which exists so the addition cannot
#: be quiet.
KNOWN_UNCLEAR = frozenset()


def entries():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["invariants"]


def unclear_ids():
    return {e["id"] for e in entries() if e["status"] == "unclear"}


class TheManifestWasRead(unittest.TestCase):
    """INV-265 -- an empty or unparsed manifest satisfies every comparison below trivially."""

    def test_the_manifest_carries_entries(self):
        self.assertGreaterEqual(
            len(entries()), 300,
            "fewer than three hundred invariants parsed from %s; the manifest is truncated or "
            "its shape moved, and the checks below prove nothing" % MANIFEST)

    def test_every_entry_carries_a_known_status(self):
        bad = sorted({e["status"] for e in entries()} - {"active", "superseded", "unclear"})
        self.assertEqual([], bad, "unexpected status value(s) in the manifest: %s" % bad)

    def test_an_empty_pin_is_the_intended_state(self):
        """The confirmation the previous assertion asked for, recorded rather than implied.

        ⛔ **This replaced `test_the_pin_is_not_empty`, which pointed the wrong way.** That
        assertion required the set to be NON-empty, on the INV-265 reasoning that an empty
        corpus satisfies comparisons trivially. For a permit list the logic inverts: empty is
        the STRICTEST state, because `unclear_ids() - KNOWN_UNCLEAR` then forbids every
        undecidable invariant. Emptiness here is the goal, not the hazard -- the INV-265 risk
        lives in the manifest, and `test_the_manifest_carries_entries` holds it.

        ⚠️ Its message had already anticipated this moment -- *"If #112 cleared every entry
        that is worth celebrating, but an empty pin also means this guard now forbids ALL
        unclear entries -- confirm that is intended rather than leaving it implied."* This is
        that confirmation, as an assertion instead of a sentence.
        """
        self.assertEqual(
            frozenset(), KNOWN_UNCLEAR,
            "KNOWN_UNCLEAR is non-empty: %s. Every id here is an invariant a child reading the "
            "published manifest cannot evaluate. If the addition is deliberate, say why in the "
            "commit and amend this assertion -- it is written to make re-permitting an "
            "undecidable invariant a visible act rather than a quiet one"
            % ", ".join(sorted(KNOWN_UNCLEAR)))


class NoInvariantNewlyBecomesUnclear(unittest.TestCase):
    def test_nothing_joined_the_undecidable_set(self):
        joined = sorted(unclear_ids() - KNOWN_UNCLEAR)
        self.assertEqual(
            [], joined,
            "invariant(s) became `status: unclear` in the published manifest: %s. A child "
            "reading it cannot tell whether they are still in force. Usually this is "
            "supersession vocabulary used in a NON-supersession sense -- #113 wrote 'a "
            "superseded location' about a file path and flipped INV-216. Reword the prose, or "
            "add the id to KNOWN_UNCLEAR deliberately and say why" % ", ".join(joined))


class ThePinIsStillAboutRealInvariants(unittest.TestCase):
    """A pin naming an id the register no longer defines was never re-read."""

    def test_every_pinned_id_exists(self):
        known = {e["id"] for e in entries()}
        missing = sorted(KNOWN_UNCLEAR - known)
        self.assertEqual(
            [], missing,
            "KNOWN_UNCLEAR names invariant(s) the manifest does not define: %s. The register "
            "moved and this set was not re-read" % ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
