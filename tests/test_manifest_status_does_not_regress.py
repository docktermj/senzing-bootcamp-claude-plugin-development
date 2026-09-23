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
* an id may **leave** once #112 has resolved its prose so it is no longer `unclear`.

⚠️ **The permit and the condition retire together, and the order matters.** Removing an id from
this set while the manifest still reports it `unclear` fails -- correctly: that withdraws the
permission without fixing anything. A negative control pins that distinction, because the
looser reading ("shrinkage is always safe") is the one a later editor will reach for.

⚠️ **A stale permit -- an id pinned here that is no longer `unclear` -- only ever permits and
never forbids, so it does not fail.** But a pin naming an id the register no longer **defines**
does fail, because that means the set was never re-read.

⚠️ **What this does NOT establish:** that the 33 pinned entries are correctly classified, that
their prose is ambiguous for good reason, or that `status_of()` reads any of them the way a human
would. #112 is chartered to decide those. This holds the line while that work is pending.

Source issue: #122.

Stdlib only; the manifest is read as JSON (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "invariant-manifest.json"

#: The invariants whose supersession status the prose genuinely leaves undecidable, as of
#: 2026-09-23. ⛔ Entries may be REMOVED as #112 resolves them; adding one is a deliberate act
#: and must be justified in the commit that does it.
KNOWN_UNCLEAR = frozenset({
    "INV-050", "INV-073", "INV-075", "INV-076", "INV-077", "INV-078",
    "INV-082", "INV-083", "INV-087", "INV-091", "INV-097", "INV-103",
    "INV-104", "INV-107", "INV-114", "INV-138", "INV-155", "INV-161",
    "INV-164", "INV-181", "INV-198", "INV-202", "INV-228", "INV-234",
    "INV-235", "INV-243", "INV-244", "INV-250", "INV-263", "INV-270",
    "INV-278", "INV-295", "INV-300",
})


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

    def test_the_pin_is_not_empty(self):
        self.assertTrue(
            KNOWN_UNCLEAR,
            "KNOWN_UNCLEAR is empty. If #112 cleared every entry that is worth celebrating, but "
            "an empty pin also means this guard now forbids ALL unclear entries -- confirm that "
            "is intended rather than leaving it implied")


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
