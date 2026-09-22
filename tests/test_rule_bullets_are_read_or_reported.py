"""Every rule bullet is read as a rule, read as a description, or reported as unparsed.

`parse()` read a bullet by taking the first `**…**` on the line. That is right for the shape
the parser was written against -- ``- ⛔ **Rule.** — in `path` `` -- and wrong for the older
shape, where the path leads, the rule is plain prose, and the only bold is an editorial
parenthetical:

    - `skills/graduation/SKILL.md` Step 6a — ⛔ follow `database-backup.md` *(covered by …)*.

⛔ **The held block ships 9 such bullets. `parse()` presented 4**, and all four were annotation
fragments -- *"was uncovered"*, *"relocated"* -- each located as `(same section as the rule
above)` because `LOC` wants a trailing path. The other five vanished. `check` reported
`1 checked, 0 mismatched, 0 unresolved, 4 no-prose-site`, which reads clean: a parse failure
had been filed under the category that means *nothing is owed* (#110).

⛔ **(INV-308) The two shapes are not interchangeable, and the fix is not one more pattern
feeding the same verifier.** A modern bullet's bold is a **verbatim quote** that `check`
compares against the source. The older bullet's prose is a **description** of the rule at that
location: measured 2026-09-22, 9 of 9 resolve their path and **0 of 9** appear verbatim in the
file they name. Checking them as quotes would print nine mismatches, every one false. So a
rule carries a `kind`, `check` verifies only `quoted`, and `described` is counted apart --
never folded into `no-prose-site`, which is the mistake being fixed.

⚠️ **`DESCRIBED` is tried BEFORE `QUOTE`.** It is the more specific shape, and an older bullet
whose annotation holds the only bold matches `QUOTE` perfectly well -- which is exactly how
the four fragments were produced. `OrderOfShapesMatters` pins it, because the ordering is the
whole defect and a later edit could reverse it without any other test noticing.

⚠️ **What this does NOT establish:** that a described rule's summary is faithful to the rule it
describes. Nothing checks that, by construction -- it is prose about prose. `show` labels such
rules unverified rather than implying otherwise.

Source issue: #110.

Stdlib only; the helper is loaded by path, since it takes no `--repo` argument (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import io
import contextlib
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"
LEDGER = REPO_ROOT / "specs" / "IMPLEMENTED.md"

#: The block that exposed this. Held, so nothing is decided from it today -- which is why the
#: loss went unnoticed, and why the numbers below are pinned rather than left to the next reader.
HELD_BLOCK = "bootcamp-cannot-leave"

#: The modern shape: the bold IS the rule, and the path trails it.
QUOTED_BULLET = "    - ⛔ **The script writes nothing.** — in `.claude/skills/x/SKILL.md`"

#: The older shape: the path leads, the rule is prose, the bold is an annotation.
#: ⛔ This line is the regression fixture -- under the old ordering its `**was uncovered**`
#: became the rule and the actual rule was discarded.
DESCRIBED_BULLET = ("    - `skills/demo/packaging.md:25` — ⛔ run the dry run first; the question "
                    "quotes a measured size *(**was uncovered**; now in the draft)*.")

#: Neither shape: a ⛔ bullet with no bold and no leading path.
UNPARSABLE_BULLET = "    - ⛔ something nobody wrote in either shape"


def helper():
    spec = importlib.util.spec_from_file_location("pending_invariants", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_bullets(*lines):
    return helper().parse({"text": "\n".join(lines), "line": 0, "spec": "s"})


def live(name):
    mod = helper()
    return mod, mod.parse([b for b in mod.blocks() if name in b["spec"]][0])


class TheOlderShapeIsRead(unittest.TestCase):
    def test_a_described_bullet_becomes_a_rule(self):
        r = parse_bullets(DESCRIBED_BULLET)["rules"]
        self.assertEqual(1, len(r), "the older bullet shape was not read at all")
        self.assertEqual("described", r[0]["kind"])
        self.assertIn("run the dry run first", r[0]["text"])

    def test_the_annotation_is_not_the_rule(self):
        """The exact regression: the bold parenthetical must not become the rule."""
        r = parse_bullets(DESCRIBED_BULLET)["rules"][0]
        self.assertNotIn("was uncovered", r["text"],
                         "the editorial annotation was presented as the rule -- this is the "
                         "defect #110 reported, reproduced")

    def test_a_line_suffix_is_not_part_of_the_filename(self):
        r = parse_bullets(DESCRIBED_BULLET)["rules"][0]
        self.assertEqual("skills/demo/packaging.md", r["site"])
        self.assertEqual("skills/demo/packaging.md:25", r["where"],
                         "the maintainer should still read the line number")


class OrderOfShapesMatters(unittest.TestCase):
    """⛔ DESCRIBED is the more specific shape and must be tried first."""

    def test_a_described_bullet_is_never_classified_quoted(self):
        kinds = {r["kind"] for r in parse_bullets(DESCRIBED_BULLET)["rules"]}
        self.assertEqual({"described"}, kinds,
                         "a bullet in the older shape was classified as quoted, so its "
                         "annotation will be verbatim-checked against the file it names")

    def test_the_modern_shape_is_still_quoted(self):
        r = parse_bullets(QUOTED_BULLET)["rules"]
        self.assertEqual(1, len(r))
        self.assertEqual("quoted", r[0]["kind"])
        self.assertEqual("The script writes nothing.", r[0]["text"])
        self.assertEqual(".claude/skills/x/SKILL.md", r[0]["site"])

    def test_both_shapes_together_keep_their_kinds(self):
        rules = parse_bullets(QUOTED_BULLET, DESCRIBED_BULLET)["rules"]
        self.assertEqual(["quoted", "described"], [r["kind"] for r in rules])


class NothingIsDropped(unittest.TestCase):
    """⛔ (INV-308) A bullet matching neither shape is reported, never skipped."""

    def test_an_unparsable_bullet_is_recorded(self):
        p = parse_bullets(UNPARSABLE_BULLET)
        self.assertEqual([], p["rules"])
        self.assertEqual(1, len(p["unparsed"]),
                         "a bullet matching neither shape was dropped silently, which is "
                         "indistinguishable from a block that had no bullets")

    def test_an_unparsable_bullet_does_not_suppress_its_neighbors(self):
        p = parse_bullets(QUOTED_BULLET, UNPARSABLE_BULLET, DESCRIBED_BULLET)
        self.assertEqual(2, len(p["rules"]))
        self.assertEqual(1, len(p["unparsed"]))


class CheckCountsThemApart(unittest.TestCase):
    """The category that hid the failure must no longer absorb it."""

    def report(self):
        mod = helper()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.cmd_check()
        return buf.getvalue()

    def counts(self):
        """The reported numbers, not merely the labels. ⛔ Asserting the label matches is
        satisfied by a counter wired to the wrong variable printing zero -- which a negative
        control caught this test doing, and which is the very defect #110 reports."""
        out = self.report()
        return {k: int(v) for v, k in re.findall(
            r"(\d+) (checked|mismatched|unresolved|no-prose-site|described-not-quoted|unparsed)",
            out.replace("rule quotes checked", "checked"))}

    def parsed_kinds(self):
        mod = helper()
        n = {"described": 0, "quoted": 0}
        for b in mod.blocks():
            for r in mod.parse(b)["rules"]:
                n[r["kind"]] += 1
        return n

    def test_described_rules_have_their_own_count(self):
        reported = self.counts().get("described-not-quoted")
        self.assertEqual(
            self.parsed_kinds()["described"], reported,
            "`check` reports %r described-not-quoted while the parser sees %d. The counter is "
            "wired to a different category, so those rules are being absorbed by it"
            % (reported, self.parsed_kinds()["described"]))
        self.assertGreater(
            reported, 0,
            "no described rule was counted, so this assertion is vacuous (INV-265): the ledger "
            "no longer exercises the older bullet shape and the branch is untested")

    def test_check_reports_no_mismatch(self):
        """Verbatim-checking a described rule produces mismatches that mean nothing."""
        self.assertEqual(
            0, self.counts().get("mismatched"),
            "`check` reports mismatches. If described rules are being compared verbatim, every "
            "one is a false accusation -- their text summarizes a rule and never quoted it")

    def test_the_unparsed_count_is_reported(self):
        self.assertIn("unparsed", self.counts())

    def test_described_rules_are_not_counted_as_no_prose_site(self):
        """The precise misfiling #110 reported: a parse failure inside 'nothing is owed'."""
        mod, p = live(HELD_BLOCK)
        described = [r for r in p["rules"] if r["kind"] == "described"]
        self.assertTrue(described, "the held block parsed no described rules; fixture drifted")
        for r in described:
            self.assertIsNotNone(
                r["site"],
                "a described rule carries no site, so `check` will count it as no-prose-site "
                "-- the category that means nothing is owed")

    def test_no_described_rule_is_verbatim_checked(self):
        """All nine would mismatch, and every mismatch would be a false accusation."""
        mod, p = live(HELD_BLOCK)
        for r in (r for r in p["rules"] if r["kind"] == "described"):
            f = mod.resolve(r["site"])
            self.assertIsNotNone(f, "fixture drifted: %s no longer resolves" % r["site"])
            self.assertNotIn(
                r["text"], mod.flat(f.read_text(encoding="utf-8")),
                "a described rule DOES appear verbatim in its file (%s). That is fine, but it "
                "means this test no longer demonstrates why described rules must not be "
                "verbatim-checked -- re-derive the claim before trusting it" % r["site"])


class TheLiveBlockIsFullyRead(unittest.TestCase):
    """INV-265 -- and the numbers #110 measured, pinned so a regression is loud."""

    def test_every_bullet_in_the_held_block_is_accounted_for(self):
        mod, p = live(HELD_BLOCK)
        text = mod.BOILER.sub("", [b for b in mod.blocks() if HELD_BLOCK in b["spec"]][0]["text"])
        bullets = [l for l in text.split("\n") if mod.BULLET.match(l)]
        self.assertGreaterEqual(len(bullets), 5,
                                "the held block parsed almost no bullets; fixture drifted and "
                                "the comparison below proves nothing")
        self.assertEqual(
            len(bullets), len(p["rules"]) + len(p["unparsed"]),
            "%d rule bullet(s) are neither a rule nor reported as unparsed -- they vanished, "
            "which is the defect this module exists to prevent"
            % (len(bullets) - len(p["rules"]) - len(p["unparsed"])))

    def test_the_block_now_offers_sites_to_cite(self):
        """It offered none. Step 2 calls an empty site list where the misses have been."""
        mod, p = live(HELD_BLOCK)
        self.assertGreaterEqual(
            len(set(p["sites"])), 2,
            "the held block yields fewer than two distinct sites, so a maintainer registering "
            "it would have almost nothing to cite")


class TheTwoParsersAgree(unittest.TestCase):
    """One corpus, two readers. #59's lesson was three copies of the resolution roots."""

    def test_every_quoted_rule_is_one_the_quote_guard_also_sees(self):
        mod = helper()
        guard = re.compile(r"⛔ \*\*(.+?)\*\*.*?—\s*in `([^`]+)`")
        seen = {m.group(1) for m in
                (guard.search(l) for l in LEDGER.read_text(encoding="utf-8").splitlines())
                if m}
        mine = {r["text"] for b in mod.blocks() for r in mod.parse(b)["rules"]
                if r["kind"] == "quoted"}
        missed = sorted(q for q in mine if not any(mod.flat(s) == q for s in seen))
        self.assertEqual(
            [], missed,
            "pending_invariants.py classifies rule(s) as QUOTED that "
            "tests/test_deferral_quotes_match_their_source.py's own scanner does not see: %s. "
            "The two readers have drifted, and one of them is verifying nothing"
            % ", ".join(m[:60] for m in missed))


if __name__ == "__main__":
    unittest.main()
