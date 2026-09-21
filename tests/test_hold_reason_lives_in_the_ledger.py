"""A hold records its reason in the deferral block, so a deferral with no spec file can be held.

`/review-invariants` offers three verdicts and insists two of them are not "no". For a deferral
that came from a **GitHub issue rather than a spec file**, one of the three could not be carried
out: `hold_reason()` opened `specs/<spec>.md` and returned `None` when there was no file, and
`specs/` is frozen under INV-307 so one cannot be created. ⛔ **The only reachable held state for
such a block was the generic string "spec requires approval before implementation"** — a property
of the work, not the maintainer's decision, and carrying no revisit condition.

⛔ **Both failure outcomes were silent.** Either the reason went into the ledger where nothing
read it and the block reported as **pending** on the next run — re-offering a decision already
made, the exact 2026-09-01 defect the skill was built to stop — or it went nowhere durable and
died with the conversation.

⚠️ **One route, not two.** The spec-file route was used by exactly **one** file of the 519-file
archive, and that block was migrated into the ledger on 2026-09-21. Two mechanisms for one fact is
how the old fallback came to report something other than a reason. The frozen spec file still
carries the same paragraph and is no longer read by anything; it cannot be edited to say so
(INV-307), which is why the ledger copy records the move.

⛔ **The `HELD` paragraph must sit INSIDE the deferral bullet.** The queue reads a block
bullet-by-bullet, so one written as its own top-level bullet terminates the block and is invisible
— found while implementing this: the first placement reported the migrated block as held by the
**generic fallback**, not by the maintainer's reason, and looked correct at a glance.

⚠️ **The generic `HELD_IN_BLOCK` state is kept deliberately.** *"Spec requires approval before
implementation"* is a property of the work; a maintainer's hold is a decision. Collapsing them is
what made the old fallback misleading.

Stdlib only; the helper is loaded by path and its module-level roots point at a temporary tree,
since it takes no `--repo` argument (INV-108).

Source issue: #58.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"
SKILL = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "SKILL.md"
COMMAND = REPO_ROOT / ".claude" / "commands" / "review-invariants.md"
LEDGER = REPO_ROOT / "specs" / "IMPLEMENTED.md"

DEFERRAL = """# Implemented Specs

## an-issue-driven-spec

- **DEFERRED INVARIANT — awaiting the maintainer's sign-off; NOT minted.**
    - ⛔ **Never ship a provenance claim without its supplier.** — in `skills/demo/SKILL.md`

  **INV-NNN** — provenance and supplier must both appear.
%s
- **Commit:** uncommitted
"""

#: The hold, written INSIDE the deferral bullet as the skill instructs.
HELD_INSIDE = """
  **HELD 2026-09-21:** the rule is right but the wording is still moving.
  Revisit after the next audit has measured it.
"""

#: The same text written BESIDE the block, as its own top-level bullet. ⛔ This is the placement
#: that looks correct and is not: it terminates the block, so the queue never sees it.
HELD_BESIDE = """
- **HELD 2026-09-21:** the rule is right but the wording is still moving.
  Revisit after the next audit has measured it.
"""


def load(root):
    spec = importlib.util.spec_from_file_location("pending_invariants_hold", HELPER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pending_invariants_hold"] = module
    spec.loader.exec_module(module)
    module.REPO = root
    module.LEDGER = root / "specs" / "IMPLEMENTED.md"
    module.SPECS = root / "specs"
    module.PLUGIN = root / "plugins" / "senzing-bootcamp"
    return module


def build(tmp, hold):
    root = Path(tmp)
    (root / "specs").mkdir()
    (root / "specs" / "IMPLEMENTED.md").write_text(DEFERRAL % hold, encoding="utf-8")
    return root


def listing(root):
    module = load(root)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        module.cmd_list()
    return out.getvalue()


class AHoldWithNoSpecFileIsRecorded(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hold-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_fixture_has_no_spec_file(self):
        """⛔ INV-265 — the whole point is a deferral the old route could not hold."""
        root = build(self.tmp, HELD_INSIDE)
        self.assertFalse(
            (root / "specs" / "an-issue-driven-spec.md").exists(),
            "the fixture created a spec file, so it exercises the route this issue is about "
            "replacing rather than the one that had no home")

    def test_a_held_block_is_not_reported_as_pending(self):
        out = listing(build(self.tmp, HELD_INSIDE))
        self.assertIn("pending: 0", out,
                      "a block the maintainer held is still counted as pending, so the next run "
                      "re-offers a decision already made:\n%s" % out)
        self.assertIn("held: 1", out, out)

    def test_the_maintainers_revisit_condition_is_surfaced(self):
        """⚠️ A hold is worth as much as its revisit condition — so that is what is shown."""
        out = listing(build(self.tmp, HELD_INSIDE))
        self.assertIn(
            "Revisit after the next audit has measured it.", out,
            "the listing does not surface the recorded revisit condition, which is the part a "
            "later run can act on:\n%s" % out)

    def test_a_block_with_no_hold_stays_pending(self):
        """⛔ Over-correcting into 'everything is held' would empty the queue silently."""
        out = listing(build(self.tmp, ""))
        self.assertIn("pending: 1", out,
                      "a block nobody held was reported as held, so it will never be "
                      "presented:\n%s" % out)

    def test_a_hold_written_beside_the_block_does_not_count_as_held(self):
        """⛔ The placement that looks right and is not — found while implementing #58.

        The queue reads a block bullet-by-bullet, so a `HELD` paragraph written as its own
        top-level bullet ends the block. This asserts the failure is visible as *pending* rather
        than silently held by the generic fallback.
        """
        out = listing(build(self.tmp, HELD_BESIDE))
        self.assertIn(
            "pending: 1", out,
            "a HELD paragraph written outside the deferral bullet was treated as a hold. It is "
            "not inside the block the queue reads, so the reason would be invisible while the "
            "block looked decided:\n%s" % out)


class TheSpecFileRouteIsGone(unittest.TestCase):
    """⚠️ One fact, one mechanism — the old fallback's lesson."""

    def test_the_helper_no_longer_reads_a_spec_file_for_the_hold(self):
        src = HELPER.read_text(encoding="utf-8")
        body = src[src.index("def hold_reason"):src.index("def parse(")]
        self.assertNotIn(
            "SPECS /", body,
            "hold_reason still opens a spec file. An issue-driven deferral has none and `specs/` "
            "is frozen (INV-307), so that route can only ever return None for them")

    def test_the_migrated_block_is_still_held_in_this_repository(self):
        """⛔ Dropping the old route without migrating would re-offer a twice-made decision."""
        module = load(REPO_ROOT)
        _pending, held = module.queue()
        names = [p["spec"] for p in held]
        self.assertIn(
            "the-bootcamp-cannot-leave-the-machine-it-was-built-on", names,
            "the one block that used the spec-file route is no longer held. Its hold was "
            "recorded on 2026-08-27 and reaffirmed since; reporting it as pending asks the "
            "maintainer to re-derive it. Held blocks seen: %s" % names)

    def test_the_migrated_reason_is_the_maintainers_own_wording(self):
        module = load(REPO_ROOT)
        _pending, held = module.queue()
        entry = next(p for p in held
                     if p["spec"] == "the-bootcamp-cannot-leave-the-machine-it-was-built-on")
        self.assertIn(
            "dry-run", entry["held"],
            "the migrated hold no longer carries the recorded revisit condition. It was moved "
            "verbatim for a reason: summarizing a recorded decision makes a new decision nobody "
            "took. Got: %r" % entry["held"])


class TheDocumentsNameTheNewLocation(unittest.TestCase):
    def test_both_files_say_the_hold_goes_in_the_block(self):
        for name, path in (("SKILL.md", SKILL), ("command", COMMAND)):
            text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            with self.subTest(file=name):
                self.assertIn(
                    "HELD <date>", text,
                    "%s does not name the `HELD <date>:` form, so a maintainer holding a block "
                    "has no stated way to record the reason where the queue reads it" % name)

    def test_neither_file_still_sends_the_reason_to_the_spec_file(self):
        for name, path in (("SKILL.md", SKILL), ("command", COMMAND)):
            text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            with self.subTest(file=name):
                self.assertNotRegex(
                    text, r"revisit condition \*\*in the spec file\*\*",
                    "%s still sends the hold reason to the spec file. An issue-driven deferral "
                    "has none and one cannot be created (INV-307)" % name)

    def test_the_skill_warns_about_the_placement(self):
        text = re.sub(r"\s+", " ", SKILL.read_text(encoding="utf-8"))
        self.assertRegex(
            text, r"[Ii]nside the block, not beside it",
            "the skill does not warn that a HELD paragraph written as its own bullet ends the "
            "block and is never read. That placement looks correct and silently reports the "
            "block as pending")


if __name__ == "__main__":
    unittest.main()
