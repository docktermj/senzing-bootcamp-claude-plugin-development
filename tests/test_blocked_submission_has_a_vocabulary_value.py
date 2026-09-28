"""A consented-but-forbidden upstream send has its own `Upstream:` value, everywhere.

Two rules, each correct alone, collided on 2026-08-27. **Graduation Step 0** offers to forward
`mcp-server`-routed findings and send on a yes. **`/dry-run`** forbids calling `submit_feedback`
under any category, so a dry run never files into Senzing's real queue. On the first phase-3
walk ever to reach graduation, the maintainer answered "yes" in character and the walk had to
break character to explain the send could not happen.

⚠️ **Reworded 2026-09-26 (#153).** `/dry-run` no longer bans `submit_feedback` outright: its
outbound rule lets the maintainer, out of character, approve sending a certain `mcp-server`
finding. What still blocks the send at graduation is that the *yes* was given in character, so the
disclosure the walk reads out now says a dry run never sends on the Bootcamper's answer, and the
pinned regex below follows it. The collision, and the value it needs, are unchanged.

⛔ **The vocabulary had no value for that outcome.** `feedback.md` Step 3 offered
`not applicable | offered, declined | submitted YYYY-MM-DD | submission failed: reason`, and the
nearest legal value — `offered, declined` — is **false about the one thing the field records**:
the bootcamper agreed. `submission failed:` is wrong too; nothing failed and no retry will
succeed. So `submission blocked: <reason>` was added.

⚠️ **What the harm is, stated accurately.** `feedback-to-issues` Step 1 skips a finding only when
the field says it was already *sent*, so a `declined` entry is not silently dropped from spec
filing — the spec that prompted this fix reasoned it would be, and that part is overstated. The
real cost is narrower and still worth fixing: the field is the record of what happened, and
`offered, declined` records the opposite of what happened, reading as "considered and rejected"
to anyone later deciding whether the report is still owed.

⚠️ What this does NOT establish: that a walk actually records the new value. That is a runtime
property of a phase-3 run (INV-108). It asserts the value exists wherever the vocabulary is
enumerated, so the two enumerations cannot drift.

Enforces **INV-281** — the `Upstream:` outcome vocabulary is a closed set stated identically at every site, and a
consented-but-blocked send carries its own value distinct from a decline.

**`offer pending` (#167).** Graduation Step 0, the bootcamper-driven flow (Step 3 -> 3c) and the
silent in-run append all save an `mcp-server`/`both` entry before its upstream question is
answered, so between the append and the answer no value was correct. A 2026-09-25 walk wrote an
ad-hoc `pending (offer below)`. `offer pending` is that value. It must be listed at every
entry-side enumeration, and `/feedback-to-issues` must read it as still owed, as it does
`submission blocked`.

⚠️ **The spec-side line is exempt for `offer pending`, and only for it.** `issue-template.md`'s
`Upstream:` records the ISSUE's field, not the entry's: the maintainer's decision on a pending
entry lands in its existing values (`sent <date>`, `declined by the maintainer`), so `offer
pending` never needs to be written there (the issue's out-of-scope list; maintainer decision on
#167). `submission blocked` is still required on every line, that one included.

Source spec: `specs/graduation-upstream-offer-collides-with-the-dry-run-no-send-rule.md`.
Source issue: #167 (`offer pending`).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins"
DRY_RUN = REPO_ROOT / ".claude" / "skills" / "dry-run" / "phase3-conversational.md"
#: Maintainer-side skills that state the same vocabulary. `.claude/` does not ship, so a
#: corpus of `plugins/` alone is structurally blind to it — which is exactly how the value
#: added on 2026-08-28 reached two of the vocabulary's three sites and not the third.
MAINTAINER_SIDE = REPO_ROOT / ".claude" / "skills"
VALUE = "submission blocked"
#: The value for an entry saved before its upstream question was answered (#167).
PENDING = "offer pending"
#: The other values, used to find every place the vocabulary is enumerated.
SIBLINGS = ("offered, declined", "submission failed")
#: The spec-side vocabulary uses its own spelling for the same closed set.
SPEC_SIDE_SIBLINGS = ("already sent", "declined by the maintainer")


def shipped_markdown():
    return sorted(p for p in PLUGIN.rglob("*.md") if "__pycache__" not in p.parts)


def vocabulary_corpus():
    """Shipped prose **and** the maintainer-side skills, because this vocabulary spans both.

    ⚠️ Scanning `plugins/` alone is the right default for a rule about shipped prose, and
    it is wrong here: `feedback-to-issues` states the same closed set from the spec side,
    and a guard that cannot see it cannot notice the two halves disagreeing. This is the
    site-set-is-larger-than-the-shipped-tree case of INV-246.
    """
    out = list(shipped_markdown())
    if MAINTAINER_SIDE.is_dir():
        out += [p for p in MAINTAINER_SIDE.rglob("*.md") if "__pycache__" not in p.parts]
    return sorted(out)


def flatten(text):
    return re.sub(r"\s+", " ", text).lower()


def enumeration_lines():
    """Every LINE in shipped markdown that lists the `Upstream:` outcome vocabulary.

    Derived by looking for the sibling values rather than by naming files (INV-246): the
    spec predicted two sites, and a hardcoded pair cannot notice a third appearing.

    ⛔ **Line-level, not file-level, and that distinction is load-bearing.** A file-level
    version of this passed its own negative control: removing the value from the entry
    template still left it elsewhere in the same file, so the drift the guard exists to
    catch was invisible to it. The vocabulary drifts one enumeration at a time.
    """
    out = []
    for p in vocabulary_corpus():
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            if all(s in low for s in SIBLINGS) or all(s in low for s in SPEC_SIDE_SIBLINGS):
                out.append((p, i, line))
    return out


class TheVocabularyCarriesABlockedValue(unittest.TestCase):
    def test_the_enumerations_are_found(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        self.assertTrue(
            enumeration_lines(),
            "no shipped line enumerates the `Upstream:` outcome vocabulary any more; the scan "
            "broke or the vocabulary moved. Re-derive SIBLINGS rather than deleting this guard")

    def test_every_enumeration_includes_the_blocked_value(self):
        missing = [f"{p.relative_to(REPO_ROOT)}:{n}  {line.strip()[:90]}"
                   for p, n, line in enumeration_lines() if VALUE not in line.lower()]
        self.assertEqual(
            [], missing,
            f"an `Upstream:` vocabulary enumeration omits `{VALUE}:`, so the copies have "
            "drifted and a consented-but-forbidden send has no legal value there:\n  "
            + "\n  ".join(missing))

    def test_both_trees_state_the_value(self):
        """⛔ The finding this widening exists for: present in one tree, absent in the other.

        On 2026-08-28 the value reached `plugins/`'s two enumerations and not
        `feedback-to-issues`'s, and the guard could not see it because its corpus stopped at
        the shipped tree. A count per tree is what makes that visible.
        """
        trees = {"plugins": 0, ".claude": 0}
        for path, _, line in enumeration_lines():
            if VALUE in line.lower():
                key = "plugins" if "plugins" in path.parts else ".claude"
                trees[key] += 1
        for tree, n in trees.items():
            with self.subTest(tree=tree):
                self.assertGreater(
                    n, 0,
                    f"no enumeration under {tree}/ states `{VALUE}:`. The vocabulary spans "
                    "both trees, so a value in one and not the other is the drift this "
                    "guard exists to catch")

    def test_the_spec_side_says_the_report_is_still_owed(self):
        """`submission blocked` is the one outcome that does NOT end the obligation."""
        skill = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md"
        flat = flatten(skill.read_text(encoding="utf-8"))
        self.assertIn(VALUE, flat,
                      "feedback-to-issues Step 1 never mentions the blocked value, so it "
                      "triages a consented-but-unsent finding as though it were declined")
        self.assertIn("still owed", flat,
                      "Step 1 does not say a blocked entry still owes a report — the whole "
                      "reason the value is distinct from a decline")

    def test_graduation_points_at_the_blocked_value(self):
        """Step 0 is where the collision fires, so the rule must be reachable there (INV-183)."""
        grad = PLUGIN / "senzing-bootcamp" / "skills" / "graduation" / "SKILL.md"
        flat = flatten(grad.read_text(encoding="utf-8"))
        self.assertIn(VALUE, flat,
                      "graduation Step 0 offers the forward but never names the value to record "
                      "when the session is forbidden to send")
        self.assertIn("never", flat[flat.index(VALUE):flat.index(VALUE) + 400],
                      "graduation names the blocked value without ruling out `offered, declined`, "
                      "which is the wrong value a runner would otherwise reach for")

    def test_the_blocked_value_is_distinguished_from_declined(self):
        """⛔ The whole point: it must not become a synonym for the other three."""
        fb = PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding" / "feedback.md"
        flat = flatten(fb.read_text(encoding="utf-8"))
        self.assertIn(VALUE, flat)
        window = flat[flat.index(f"⛔ **`{VALUE}"): flat.index(f"⛔ **`{VALUE}") + 900] \
            if f"⛔ **`{VALUE}" in flat else flat
        self.assertIn("not a synonym", window,
                      "feedback.md lists the blocked value without saying it is not a synonym "
                      "for declined/failed — which is how it becomes one")
        self.assertIn("offered, declined", window,
                      "the guidance does not name the wrong value it exists to displace")

    def test_the_dry_run_skill_names_the_gate_and_the_wording(self):
        """Maintainer-side, so it never ships — but it is where the runner reads."""
        self.assertTrue(DRY_RUN.is_file(), "dry-run phase3 doc is missing")
        flat = flatten(DRY_RUN.read_text(encoding="utf-8"))
        self.assertIn("graduation", flat)
        self.assertIn(VALUE, flat,
                      "the dry-run phase-3 doc does not tell the runner which value to record")
        self.assertIn("present the offer", flat,
                      "the doc must say the offer is PRESENTED — skipping the gate silently "
                      "corrupts the thing phase 3 exists to observe")
        # `(?:> )?` -- the disclosure is a blockquote, and its line break leaves a `>` behind.
        self.assertRegex(
            flat, r"this is a dry run, so i can present this gate but i can't send on your "
                  r"answer here: a dry run (?:> )?never sends on the bootcamper's answer",
            "the disclosure wording is gone, so a runner has to improvise it mid-walk — which "
            "is the situation this instruction exists to remove")


def entry_side_enumeration_lines():
    """The enumerations of the ENTRY's `Upstream:` field: the spec-side line is left out.

    Matched on the entry-side siblings only, so the spec-side line (which carries
    `SPEC_SIDE_SIBLINGS` and not `SIBLINGS`) drops out by the same rule that finds it.
    """
    return [(p, n, line) for p, n, line in enumeration_lines()
            if all(s in line.lower() for s in SIBLINGS)]


def missing_pending(lines):
    return [f"{p.relative_to(REPO_ROOT)}:{n}  {line.strip()[:90]}"
            for p, n, line in lines if PENDING not in line.lower()]


class TheVocabularyCarriesAPendingValue(unittest.TestCase):
    """#167: an entry saved before its upstream answer has a value of its own."""

    def test_the_entry_side_enumerations_are_found(self):
        """⛔ INV-265 — both entry-side lists in `feedback.md`, at least."""
        self.assertGreaterEqual(len(entry_side_enumeration_lines()), 2)

    def test_every_entry_side_enumeration_includes_offer_pending(self):
        missing = missing_pending(entry_side_enumeration_lines())
        self.assertEqual(
            [], missing,
            f"an entry-side `Upstream:` enumeration omits `{PENDING}`, so an entry saved "
            "before its upstream answer has no legal value there:\n  " + "\n  ".join(missing))

    def test_the_append_sites_write_it(self):
        """Every path that appends before asking writes `offer pending`, and replaces it."""
        fb = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
                      / "feedback.md").read_text(encoding="utf-8"))
        grad = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "graduation"
                        / "SKILL.md").read_text(encoding="utf-8"))
        step3 = fb[fb.index("## step 3: append the entry"):fb.index("## step 3b:")]
        self.assertIn("write `**upstream:**` as `offer pending` when step 2b's verdict is "
                      "`mcp-server` or `both`", step3)
        self.assertIn("replacing `offer pending`", fb)
        self.assertIn("never leave `offer pending` once an answer exists", fb)
        silent = fb[fb.index("## silent in-run append"):]
        self.assertIn("`offer pending` when step 2b says `mcp-server`/`both`", silent)
        self.assertIn("append the entry as `offer pending`", grad)
        self.assertIn("replaces every `offer pending` value in the same turn", grad)
        self.assertIn("entries already reading `offer pending` from the silent in-run append",
                      grad)

    def test_a_resumed_session_re_presents_the_offer_once(self):
        fb = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
                      / "feedback.md").read_text(encoding="utf-8"))
        self.assertIn("### unanswered offer on resume", fb)
        block = fb[fb.index("### unanswered offer on resume"):fb.index("## step 4:")]
        self.assertIn("present the unanswered offer once more, then never again", block)
        self.assertIn("(inv-006)", block)
        self.assertIn("(inv-251) **the offer is its own turn.**", block)
        self.assertIn("replace every `offer pending` value with the outcome", block)
        onboarding = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
                              / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn('follow `feedback.md` → "unanswered offer on resume"', onboarding,
                      "the resume branch does not point at the rule, so a resumed session "
                      "never finds the unanswered offer")

    def test_the_spec_side_says_offer_pending_is_still_owed(self):
        skill = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md"
        flat = flatten(skill.read_text(encoding="utf-8"))
        self.assertIn(f"`{PENDING}` is still owed too", flat,
                      "feedback-to-issues does not treat an unanswered offer as still owed, so "
                      "the report stops being anyone's job")


class TheNegativeControlsForThePendingValue(unittest.TestCase):
    """Removing `offer pending` from any one enumeration must fail the guard."""

    def test_removing_it_from_each_enumeration_fails(self):
        lines = entry_side_enumeration_lines()
        self.assertTrue(lines)
        for i, (p, n, line) in enumerate(lines):
            with self.subTest(site=f"{p.name}:{n}"):
                mutant = list(lines)
                mutant[i] = (p, n, re.sub(r"`?offer pending`?( \|)?,? ?", "", line))
                self.assertNotIn(PENDING, mutant[i][2].lower())
                self.assertTrue(missing_pending(mutant))


if __name__ == "__main__":
    unittest.main()
