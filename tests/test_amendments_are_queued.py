"""A proposed change to an invariant ALREADY REGISTERED reaches the maintainer's queue.

`pending_invariants.py` built its queue from two markers, `AWAITING` and `HELD_IN_BLOCK`, and
**both describe an invariant that does not exist yet**. A change to the wording of an invariant
already in force had no marker, no block shape and therefore no queue: `list` could not show it,
`show` could not print it, `sites` could not scan it, `check` could not verify its quote. The
concept appeared nowhere in the module -- `grep -ci amend` returned **0** (#79).

⛔ **The act is routine.** **11 of 311** invariants carry a dated correction, **13** markers in
all. Not one was ever queued: the wording reached the maintainer through a pull-request body and
the conversation, while `list` reported `pending: 0` throughout -- true to its own definition and
misleading as a worklist.

⛔ **The precedent that decided the shape.** INV-207's correction claimed its pinned site had
**moved** to another file, and the content it pins was never written there. A test caught it days
later; review did not, because nothing scanned the claim. So an amendment carries the same three
things a deferral does -- the proposed text, the sites it affects, and why -- and is scanned the
same way. A lighter shape was considered and rejected for exactly that reason.

⚠️ **Fixtures, not the live ledger (#79's own criterion 4).** No amendment is pending today, so a
test written against `specs/IMPLEMENTED.md` would assert over an empty set and pass without
exercising anything (INV-265). Every behavior below is driven by a constructed block; the live
ledger is used only to assert the module still reads it unchanged.

⚠️ **What this does NOT establish:** that a queued amendment is correct, that its site claim is
true, or that applying it is wise. `sites` makes the claim *checkable*; a maintainer still checks
it.

Source issue: #79.

Stdlib only; the helper is loaded by path (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import io
import contextlib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"
SKILL = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "SKILL.md"

#: A proposed amendment, in the shape the skill documents.
AMENDMENT_BLOCK = """- **PROPOSED AMENDMENT to INV-216 — awaiting the maintainer's sign-off; NOT applied.**
    - ⛔ **The unimplemented-spec candidate set MUST be computed.** — in `specs/INVARIANTS.md`

  The wording binds a path that moved.

  **INV-216** — the proposed dated correction, in full."""

#: The same amendment once carried out. ⛔ It must leave the queue, exactly as a registered
#: deferral does: re-offering a decision already made asks the maintainer to re-derive it.
APPLIED_BLOCK = AMENDMENT_BLOCK.replace(
    "awaiting the maintainer's sign-off; NOT applied",
    "applied 2026-09-23")

#: A deferral, for contrast: the queue must keep telling the two apart.
DEFERRAL_BLOCK = """- **DEFERRED INVARIANT — awaiting the maintainer's sign-off; NOT minted.**
    - ⛔ **A rule that ships with no id.** — in `docs/development.md`

  **INV-NNN** — the drafted wording."""

#: ⛔ Prose ABOUT amendments, which must NOT be queued. The same overcount this module's own
#: comments record for `DEFERRED INVARIANT` -- a phrase in a summary matched and reported 25
#: pending against a true 9 -- applies here identically.
PROSE_ABOUT = """- **Summary:** the run wrote a PROPOSED AMENDMENT into the ledger and the
  maintainer applied it the same day."""


def helper():
    spec = importlib.util.spec_from_file_location("pending_invariants", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parsed(block):
    return helper().parse({"text": block, "line": 0, "spec": "fixture"})


class TheModuleKnowsWhatAnAmendmentIs(unittest.TestCase):
    def test_it_names_the_invariant_being_changed(self):
        self.assertEqual("INV-216", parsed(AMENDMENT_BLOCK)["amends"])

    def test_a_deferral_names_none(self):
        self.assertIsNone(parsed(DEFERRAL_BLOCK)["amends"],
                          "a deferral was read as amending an existing invariant; the two "
                          "decisions differ and the queue must keep them apart")

    def test_an_amendment_carries_its_sites_like_any_block(self):
        """The INV-207 precedent: the site claim must be scannable, not just readable."""
        p = parsed(AMENDMENT_BLOCK)
        self.assertEqual(1, len(p["rules"]))
        self.assertEqual(["specs/INVARIANTS.md"], p["sites"])

    def test_the_proposed_text_is_read_although_it_names_a_real_id(self):
        """⚠️ An amendment writes `INV-216`, not `INV-NNN` -- the invariant exists."""
        self.assertIn("proposed dated correction", parsed(AMENDMENT_BLOCK)["wording"])


class MembershipIsDecidedByTheMarker(unittest.TestCase):
    """⛔ Never by the phrase appearing in prose -- the overcount this module already suffered."""

    def kept(self, body, tmp):
        mod = helper()
        ledger = tmp / "IMPLEMENTED.md"
        ledger.write_text("# Implemented\n\n## a-spec\n\n%s\n" % body, encoding="utf-8")
        mod.LEDGER = ledger
        return mod.blocks()

    def setUp(self):
        self.tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))

    def test_an_awaiting_amendment_is_queued(self):
        self.assertEqual(1, len(self.kept(AMENDMENT_BLOCK, self.tmp)))

    def test_an_applied_amendment_is_not(self):
        self.assertEqual(
            [], self.kept(APPLIED_BLOCK, self.tmp),
            "an amendment already applied is still queued. Re-offering a decision the "
            "maintainer has made asks them to re-derive it")

    def test_prose_about_an_amendment_is_not(self):
        self.assertEqual(
            [], self.kept(PROSE_ABOUT, self.tmp),
            "a ledger summary mentioning the phrase was queued as a pending amendment -- the "
            "same overcount this module was written to prevent, reproduced for the new marker")


class TheViewsDistinguishTheTwo(unittest.TestCase):
    def report(self, block):
        mod = helper()
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        ledger = tmp / "IMPLEMENTED.md"
        ledger.write_text("# Implemented\n\n## a-spec\n\n%s\n" % block, encoding="utf-8")
        mod.LEDGER = ledger
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.cmd_list()
        return buf.getvalue()

    def test_list_says_an_amendment_amends(self):
        out = self.report(AMENDMENT_BLOCK)
        self.assertIn("AMENDS INV-216", out)
        self.assertIn("already registered", out)

    def test_list_says_a_deferral_is_a_new_invariant(self):
        self.assertIn("new invariant", self.report(DEFERRAL_BLOCK))


class TheSkillDocumentsTheShape(unittest.TestCase):
    """A block shape nobody wrote down is one nobody will write correctly."""

    def test_the_skill_explains_both_kinds(self):
        text = SKILL.read_text(encoding="utf-8")
        for phrase in ("PROPOSED AMENDMENT", "already in force", "append-only"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_it_says_to_write_the_real_id(self):
        self.assertRegex(SKILL.read_text(encoding="utf-8"),
                         r"(?is)write the real id, not `INV-NNN`")


class TheLiveLedgerStillReads(unittest.TestCase):
    """INV-265 -- and a check that this change did not disturb the three pending deferrals."""

    def test_the_live_queue_still_parses(self):
        mod = helper()
        pending, held = mod.queue()
        self.assertGreaterEqual(
            len(pending) + len(held), 1,
            "the live ledger yields no blocks at all; the queue has stopped reading it")
        for p in pending + held:
            with self.subTest(spec=p["spec"]):
                self.assertIn("amends", p, "every parsed block carries the amends field")


if __name__ == "__main__":
    unittest.main()
