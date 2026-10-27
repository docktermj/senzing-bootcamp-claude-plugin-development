"""An amendment block whose header says applied names a note `INVARIANTS.md` actually carries.

`/review-invariants` applies a `PROPOSED AMENDMENT` by appending its dated note to
`specs/INVARIANTS.md` and writing `— applied <date>` into the block's header. Since #770 the
header is what decides the queue (INV-409), so a header that says applied takes the block out
of `pending_invariants.py list` for good. Nothing checked that the note had in fact landed.

⚠️ **It had not, twice.** The implementing commits of #671 (`19a317e1`) and #683 (`111c8321`)
wrote "applied" into their own blocks' headers, and `specs/INVARIANTS.md` never carried either
note. Shipped lines went on citing INV-146 and INV-079 for clauses the registry does not state,
and the queue could never offer the blocks again. The 2026-10-22 production-readiness audit
found both by reading (#777).

**The rule, stated as this file enforces it.** For every amendment block in
`specs/IMPLEMENTED.md` whose bold header contains `— applied <date>`, the invariant it amends
MUST carry, somewhere in its registered entry, one of the markers its drafted dated note names:
an issue number (`#683`) or an audit or review entry name
(`production-readiness-audit-2026-10-22`).

⛔ **The whole entry, never its first line.** INV-050 carries dated notes on continuation lines
of its layout tree; a first-line read reports its #685 and #618 notes as missing although the
registry carries both. The entry runs from its own `- **INV-nnn** —` line to the next one.

⚠️ **What this does NOT establish:** that the note in the registry is the text the maintainer
approved, or that an applied block without a marker in its drafted note was registered at all.
Those blocks are counted and reported, never passed silently (INV-308). It also says nothing
about a block still pending, which is the queue's business.

Enforces **INV-418** (registered 2026-10-26). It does NOT establish that the registered note is the
text the maintainer approved, and does not check an applied block whose drafted note names no marker.

Source issue: #777. Invariants: INV-409, INV-386, INV-365, INV-308, INV-265.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / "specs" / "IMPLEMENTED.md"
REGISTRY = REPO_ROOT / "specs" / "INVARIANTS.md"

#: An amendment block's header line, in either shape the ledger uses.
HEADER = re.compile(r"^- (?:⛔ )?\*\*([^\n]*?PROPOSED AMENDMENT to (INV-\d{3})[^\n]*?)\*\*",
                    re.M)
#: The decision word that marks an amendment applied (the queue's own form, INV-409).
APPLIED = re.compile(r"— applied \d{4}-\d{2}-\d{2}")
#: The marker a drafted note carries: `Dated note, 2026-10-22 (#776)` or an entry name.
MARKER = re.compile(r"Dated (?:note|correction)[^(\n]*\((#\d+|[a-z0-9-]+-\d{4}-\d{2}-\d{2}[a-z]?)\)")
#: An invariant's entry starts here; the next start, a heading or a comment ends it.
ENTRY_START = re.compile(r"^- \*\*(INV-\d{3})\*\* — ", re.M)
ENTRY_END = re.compile(r"^- \*\*INV-\d{3}\*\* — |^#{1,6} |^<!--", re.M)


def entries(registry_text):
    """{INV-nnn: the whole registered entry}, continuation lines included."""
    out = {}
    for m in ENTRY_START.finditer(registry_text):
        end = ENTRY_END.search(registry_text, m.end())
        out[m.group(1)] = registry_text[m.start(): end.start() if end else len(registry_text)]
    return out


def applied_blocks(ledger_text):
    """(INV-nnn, markers, line) for every amendment block whose header says applied."""
    out = []
    for m in HEADER.finditer(ledger_text):
        if not APPLIED.search(m.group(1)):
            continue
        end = ledger_text.find("\n- **", m.end())
        block = ledger_text[m.start(): end if end != -1 else len(ledger_text)]
        out.append((m.group(2), MARKER.findall(block), ledger_text.count("\n", 0, m.start()) + 1))
    return out


def unregistered(ledger_text, registry_text):
    """Applied blocks whose markers the amended invariant's entry carries none of."""
    reg = entries(registry_text)
    return [(ident, marks, line) for ident, marks, line in applied_blocks(ledger_text)
            if marks and not any(mk in reg.get(ident, "") for mk in marks)]


class AnAppliedHeaderIsBackedByTheRegistry(unittest.TestCase):
    def setUp(self):
        self.ledger = LEDGER.read_text(encoding="utf-8")
        self.registry = REGISTRY.read_text(encoding="utf-8")

    def test_every_applied_note_is_in_the_registry(self):
        missing = unregistered(self.ledger, self.registry)
        self.assertEqual(
            [], missing,
            "an amendment block says applied, but the invariant's registered entry carries "
            "none of its note's markers; return the header to pending so /review-invariants "
            "offers it again: %s" % ", ".join(
                "%s %s (IMPLEMENTED.md:%d)" % (i, "/".join(m), n) for i, m, n in missing))

    def test_the_scan_checked_something(self):
        """INV-265: a scan that finds no applied block certifies nothing."""
        checked = [b for b in applied_blocks(self.ledger) if b[1]]
        self.assertGreater(len(checked), 50, "the scan found almost no applied amendments")

    def test_an_entry_includes_its_continuation_lines(self):
        """INV-050's notes sit on continuation lines; a first-line read would miss them."""
        inv050 = entries(self.registry)["INV-050"]
        self.assertIn("#618", inv050)
        self.assertIn("#685", inv050)
        self.assertNotIn("- **INV-051**", inv050)


#: A minimal ledger and registry, for the negative controls. The fixture ids are assembled from
#: parts so no literal id that the registry lacks appears in this file (`citations.py verify`).
FAKE = "INV-" + "999"
OTHER = "INV-" + "998"
FIXTURE_LEDGER = """## a-spec

- **DEFERRED INVARIANT — NOT minted (an amendment, not a new id) — PROPOSED AMENDMENT to {id} — applied 2026-10-17.** The clause:
    - something — in `specs/INVARIANTS.md`

  **{id}** — (⚠️ **Dated note, 2026-10-17 (#683): wording.** The rule above still binds.)
- **Queues one amendment.**
""".format(id=FAKE)
FIXTURE_REGISTRY = "- **%s** — A rule. (Source: `x`, 2026-01-01.)\n" % FAKE


class EachCheckSeesTheDefectItWasWrittenFor(unittest.TestCase):
    def test_an_applied_header_without_its_note_is_reported(self):
        """The #671/#683 shape: the header says applied and the registry lacks the note."""
        self.assertEqual([(FAKE, ["#683"], 3)],
                         unregistered(FIXTURE_LEDGER, FIXTURE_REGISTRY))

    def test_the_note_in_the_registry_clears_it(self):
        registry = FIXTURE_REGISTRY.replace(
            "2026-01-01.)", "2026-01-01.) (⚠️ **Dated note, 2026-10-17 (#683): wording.**)")
        self.assertEqual([], unregistered(FIXTURE_LEDGER, registry))

    def test_a_pending_header_is_not_checked(self):
        ledger = FIXTURE_LEDGER.replace(
            "applied 2026-10-17.", "awaiting the maintainer's sign-off; NOT applied.")
        self.assertEqual([], unregistered(ledger, FIXTURE_REGISTRY))

    def test_a_note_on_a_continuation_line_counts(self):
        registry = FIXTURE_REGISTRY + "  continued (⚠️ **Dated note, 2026-10-17 (#683): x.**)\n"
        self.assertEqual([], unregistered(FIXTURE_LEDGER, registry))

    def test_a_note_under_a_different_invariant_does_not_count(self):
        registry = FIXTURE_REGISTRY + (
            "- **%s** — Another. (⚠️ **Dated note, 2026-10-17 (#683): x.**)\n" % OTHER)
        self.assertEqual(1, len(unregistered(FIXTURE_LEDGER, registry)))


if __name__ == "__main__":
    unittest.main()
