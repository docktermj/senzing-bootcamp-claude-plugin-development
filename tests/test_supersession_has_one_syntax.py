"""Supersession is written one way, and prose never decides an invariant's status.

`invariant_manifest.py` used to read the WORD. It matched anywhere in an entry and emitted
`status: unclear` for **33** of 311 invariants -- and reading them, most were not supersessions
at all (#112):

* a **file** in a tree diagram -- INV-050's *"bootcamp_journal.md # (legacy; superseded by …)"*;
* a **figure** -- INV-278's *"say plainly when a recorded figure is withdrawn"*, INV-295's
  *"a superseded figure MUST be named aloud"*;
* an explicit **negative** -- INV-300's *"and supersedes nothing"*, INV-263's *"INV-089 is
  **not** superseded"*, and six *"Forward pointer — nothing here is superseded"* notes.

⛔ **That mattered downstream.** `docs/development.md` tells four child ports what `unclear`
means: *a child cannot tell whether an invariant it inherited is still in force.* Thirty-three
entries said that, and most of them were simply active. #122 was the same defect at one entry --
one word, *"superseded"*, used about a file path.

⛔ **Status now comes from a BULLET, and prose is not evidence.** An entry carrying
`- **Superseded by:** INV-nnn` is superseded; every other entry is active. There is no third
state in the manifest.

⚠️ **`Partly superseded by:` leaves an entry ACTIVE, deliberately.** Six entries say only a
*clause* of themselves was replaced -- INV-040's parenthetical, INV-079's recap heading,
INV-086's framing, INV-101's Docker-only scope, INV-104's tab enumeration, INV-137's trigger --
and the rest still binds. The two-state model has no room for that, and reporting them
`superseded` would tell a child the whole rule is obsolete. That is the **dangerous direction**:
`unclear` at least said *I do not know*, while a wrong `active`/`superseded` is confident.

⛔ **So nothing may be reclassified by omission.** Every entry whose prose still mentions
supersession, and which carries none of the three bullets, must be named in
`REVIEWED_NOT_A_SUPERSESSION` with a reason. A new entry that acquires the vocabulary fails this
guard until a human looks at it. **The permit may only shrink.**

⚠️ **What this does NOT establish:** that the 19 supersessions are correct, or that a clause
marked partial really is partial. It establishes that no entry's status was decided by prose,
and that none was reclassified without being read.

⛔ **Enforces INV-313** — supersession status is derived from an explicit marker and never
from prose; two states only; a partial supersession stays `active` and carries its successor
in a field of its own; and every marker form the register uses is named where downstream
ports read the syntax.

⚠️ **What an `Enforced by` clause here does NOT claim.** This module establishes that the
syntax, the back-links, the marker-form set and the disposition list hold **in the register
and the published manifest as they stand**. It cannot establish that a supersession recorded
is *correct*, that a clause marked partial really is partial, or that any downstream consumer
reads `partly_superseded_by` the way this rule intends — the first two are human judgments
and the third lives in another repository.

Source issue: #112.

Stdlib only.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_TOOL = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "invariant_manifest.py"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
FAMILY = REPO_ROOT / "docs" / "FAMILY_WORKFLOW.md"
MANIFEST = REPO_ROOT / "invariant-manifest.json"

#: Every entry whose prose mentions supersession while asserting none of itself. ⛔ Each was
#: READ, not pattern-matched -- the issue warned that a mechanical rewrite would invert some,
#: and it was right: INV-104 was missed on the first pass because its id sits inside `**` and
#: the pattern required `superseded by INV-nnn` contiguously.
REVIEWED_NOT_A_SUPERSESSION = {
    # -- the entry supersedes something ELSE, in part; the prose names which clause --
    "INV-082": "supersedes the Truth-Set coupling of INV-038/INV-068, not those invariants whole",
    "INV-087": "supersedes INV-086's recording-location framing only",
    "INV-103": "supersedes the 'Journal' subsection-naming clause of INV-048/085/092",
    "INV-138": "supersedes INV-137's trigger only; the rest of INV-137 still binds",
    "INV-155": "supersedes INV-104's tab enumeration only",
    "INV-198": "partly supersedes INV-040's parenthetical",
    # -- explicit NEGATIVES: the entry says it supersedes nothing, or is not superseded --
    "INV-107": "states 'Nothing here is superseded'",
    "INV-161": "forward pointer: 'nothing here is superseded'",
    "INV-164": "states the attribute rule is 'not superseded' and binds unchanged",
    "INV-228": "forward pointer: 'nothing here is superseded'",
    "INV-234": "forward pointer: 'nothing here is superseded'",
    "INV-235": "forward pointer: 'nothing here is superseded'",
    "INV-243": "forward pointer: 'nothing here is superseded'",
    "INV-244": "scope note: 'nothing above is superseded'",
    "INV-263": "states 'INV-089 is not superseded; both bind'",
    "INV-300": "states it 'supersedes nothing'",
    # -- the word is about something that is NOT an invariant --
    "INV-050": "a FILE in a tree diagram is marked legacy, not this invariant",
    "INV-114": "requires naming only 'non-superseded' MODELS",
    "INV-181": "requires correcting the 'superseded behavior' of the MCP SERVER",
    "INV-202": "'reserved/superseded/legacy/future' is an annotation vocabulary for tree entries",
    "INV-278": "a recorded FIGURE is withdrawn",
    "INV-295": "a superseded FIGURE must be named aloud when replaced",
    # -- the entry GOVERNS how supersession is recorded; it is not itself one --
    "INV-313": "states the marker-and-status rule for the published register; it is the "
               "rule ABOUT supersession, supersedes nothing and is superseded by nothing",
    # -- prose about another pair's supersession, already recorded on that pair --
    "INV-250": "notes that INV-077 superseded INV-038; INV-038 carries the bullet",
    "INV-270": "carries a dated Correction, which is not a supersession",
}


def tool():
    spec = importlib.util.spec_from_file_location("invariant_manifest", MANIFEST_TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def entries():
    mod = tool()
    return mod, dict(mod.ENTRY.findall(INVARIANTS.read_text(encoding="utf-8")))


def has_any_bullet(mod, body):
    return bool(mod.SUPERSEDED_BULLET.search(body)
                or mod.PARTLY_SUPERSEDED_BULLET.search(body)
                or mod.SUPERSEDES_BULLET.search(body))


class TheRegisterWasRead(unittest.TestCase):
    """INV-265 -- every comparison below is vacuous over an empty register."""

    def test_entries_parsed(self):
        _mod, bodies = entries()
        self.assertGreaterEqual(len(bodies), 300,
                                "fewer than 300 invariants parsed; the pattern has drifted")

    def test_some_entry_is_superseded(self):
        mod, bodies = entries()
        self.assertTrue([i for i, b in bodies.items() if mod.SUPERSEDED_BULLET.search(b)],
                        "no entry carries a Superseded-by bullet, so the syntax is unexercised")


class StatusComesFromBulletsOnly(unittest.TestCase):
    def test_unclear_is_gone(self):
        mod, bodies = entries()
        unclear = [i for i, b in bodies.items() if mod.status_of(b)[0] == "unclear"]
        self.assertEqual([], unclear,
                         "`unclear` is still emitted for %s; status must come from the bullet"
                         % ", ".join(unclear))

    def test_prose_alone_does_not_supersede(self):
        """The #122 defect, as a fixture: the word about a file path decides nothing."""
        mod = tool()
        body = "a replaced location, and a superseded location quoted as a path, decide nothing."
        self.assertEqual(("active", None), mod.status_of(body))

    def test_a_bullet_does(self):
        mod = tool()
        self.assertEqual(("superseded", "INV-312"),
                         mod.status_of("text\n  - **Superseded by:** INV-312 — the guard moved"))

    def test_a_partial_bullet_leaves_it_active(self):
        """⛔ The dangerous direction: a partly-replaced rule still binds."""
        mod = tool()
        self.assertEqual(
            ("active", None),
            mod.status_of("text\n  - **Partly superseded by:** INV-155 — the tab enumeration"),
            "a partly superseded invariant was reported superseded, which tells a child port "
            "the whole rule is obsolete")


class SupersessionIsBidirectional(unittest.TestCase):
    def test_every_superseded_by_has_a_back_link(self):
        mod, bodies = entries()
        missing = []
        for inv, body in sorted(bodies.items()):
            m = mod.SUPERSEDED_BULLET.search(body)
            if not m:
                continue
            successor = bodies.get(m.group(1), "")
            if inv not in mod.SUPERSEDES_BULLET.findall(successor):
                missing.append("%s -> %s" % (inv, m.group(1)))
        self.assertEqual(
            [], missing,
            "supersession(s) recorded in one direction only: %s. A successor that does not name "
            "what it replaced reads as a new rule, which is how six variants of this syntax came "
            "to exist" % ", ".join(missing))

    def test_every_named_successor_exists(self):
        mod, bodies = entries()
        dangling = []
        for inv, body in sorted(bodies.items()):
            for pat in (mod.SUPERSEDED_BULLET, mod.PARTLY_SUPERSEDED_BULLET, mod.SUPERSEDES_BULLET):
                for target in pat.findall(body):
                    if target not in bodies:
                        dangling.append("%s -> %s" % (inv, target))
        self.assertEqual([], dangling,
                         "supersession bullet(s) name an invariant that does not exist: %s"
                         % ", ".join(dangling))


class NothingIsReclassifiedByOmission(unittest.TestCase):
    """⛔ The safety net: prose no longer decides, so every mention must be dispositioned."""

    def test_every_vocabulary_entry_is_bulleted_or_reviewed(self):
        mod, bodies = entries()
        undisposed = [i for i, b in sorted(bodies.items())
                      if mod.SUPERSESSION_WORDS.search(b)
                      and not has_any_bullet(mod, b)
                      and i not in REVIEWED_NOT_A_SUPERSESSION]
        self.assertEqual(
            [], undisposed,
            "invariant(s) mention supersession, carry no bullet, and are not in "
            "REVIEWED_NOT_A_SUPERSESSION: %s. Since prose no longer decides status, each is "
            "now reported `active` — read it and either add a bullet or record why it is not a "
            "supersession. A wrong `active` is confident where `unclear` was honest"
            % ", ".join(undisposed))

    def test_the_permit_only_shrinks(self):
        """A reviewed entry that gained a bullet, or lost the vocabulary, must leave the list."""
        mod, bodies = entries()
        stale = []
        for inv in sorted(REVIEWED_NOT_A_SUPERSESSION):
            body = bodies.get(inv)
            if body is None or not mod.SUPERSESSION_WORDS.search(body) or has_any_bullet(mod, body):
                stale.append(inv)
        self.assertEqual(
            [], stale,
            "entr(ies) are excused that no longer need it: %s. A stale permit hides whatever "
            "else it matches" % ", ".join(stale))

    def test_every_reason_is_written(self):
        blank = sorted(k for k, v in REVIEWED_NOT_A_SUPERSESSION.items() if not v.strip())
        self.assertEqual([], blank, "reviewed without a reason: %s" % ", ".join(blank))


class EveryMarkerFormIsAccountedFor(unittest.TestCase):
    """⛔ (#143) A marker the register USES and the family page does not NAME.

    `Partly superseded by:` was in use **six** times while `docs/FAMILY_WORKFLOW.md` R12 named
    two markers and said *"Nothing else establishes supersession"*. A child implementing R12 as
    written had no form for the case, and the parent's manifest had no field for it -- all six
    published `superseded_by: null` with the successor buried in `statement`.

    ⚠️ **The set is derived from the register, never listed here.** A hardcoded list of forms is
    the same defect one level up: it would agree with the page on the day it was written and
    say nothing thereafter. INV-282 -- match the claim, not the phrasings already seen.
    """

    #: Every `- **<something> superseded...:**` bullet form the register may carry, each mapped
    #: to the R12 text that must name it. ⛔ A form appearing in `INVARIANTS.md` and absent here
    #: fails `test_no_unknown_marker_form_ships`, which is the point: adding a fourth form is a
    #: family-wide act and R12 is where a child reads it.
    KNOWN_FORMS = {
        "Superseded by": "Superseded by:",
        "Supersedes": "Supersedes:",
        "Partly superseded by": "Partly superseded by:",
    }

    #: A marker bullet, matched INSIDE an invariant's body. ⛔ Two things this had wrong on the
    #: first attempt, both worth keeping written down. (1) It required a word before
    #: `superseded`, so it matched `Fully`/`Partly` and **missed `Superseded by` and
    #: `Supersedes` entirely** -- a matcher blind to the two commonest forms, which would have
    #: read as passing. (2) Scanned whole-file, it caught `- **Fully superseded:**` from the
    #: index's *explanatory prose* about the two conceptual forms, which is not a marker at all.
    #: ⚠️ Adding that to the known set would have "fixed" the failure while leaving (1) in
    #: place -- INV-282's exact trap: a matcher repaired from the instance in front of you.
    FORM = r"^\s*- \*\*((?:[A-Za-z]+ )*[Ss]upersed[a-z]*(?: by)?):\*\*"

    def forms_in_register(self):
        import re
        _mod, bodies = entries()
        found = set()
        for body in bodies.values():
            found.update(re.findall(self.FORM, body, re.M))
        return found

    def test_the_scan_found_forms(self):
        """INV-265 -- an empty form set satisfies both comparisons below."""
        self.assertGreaterEqual(
            len(self.forms_in_register()), 2,
            "fewer than two marker forms parsed from %s; the pattern has drifted and the "
            "checks below prove nothing" % INVARIANTS)

    def test_no_unknown_marker_form_ships(self):
        unknown = sorted(self.forms_in_register() - set(self.KNOWN_FORMS))
        self.assertEqual(
            [], unknown,
            "supersession marker form(s) used in %s that this guard does not know: %s. Adding a "
            "form is a family-wide act: name it in R12 of docs/FAMILY_WORKFLOW.md with a §10 "
            "amendment, decide whether it affects `status`, and add it here"
            % (INVARIANTS, ", ".join(unknown)))

    def test_r12_names_every_form_in_use(self):
        r12 = FAMILY.read_text(encoding="utf-8")
        missing = sorted(self.KNOWN_FORMS[f] for f in self.forms_in_register()
                         if self.KNOWN_FORMS[f] not in r12)
        self.assertEqual(
            [], missing,
            "marker form(s) the register uses that R12 in %s never names: %s. Four child "
            "repositories read that page to learn the syntax; a form named nowhere is one they "
            "cannot implement" % (FAMILY, ", ".join(missing)))


class ThePartialPointerIsPublished(unittest.TestCase):
    """The relation reaches the artifact downstream ports actually parse (INV-311)."""

    def published(self):
        import json
        return {e["id"]: e for e in json.loads(MANIFEST.read_text(encoding="utf-8"))["invariants"]}

    def test_every_partial_publishes_its_successor(self):
        mod, bodies = entries()
        expected = {inv: m.group(1) for inv, body in bodies.items()
                    if (m := mod.PARTLY_SUPERSEDED_BULLET.search(body))}
        self.assertTrue(expected, "no partly-superseded entry parsed; the check is vacuous")
        published = self.published()
        wrong = ["%s: register says %s, manifest says %r"
                 % (inv, want, published.get(inv, {}).get("partly_superseded_by"))
                 for inv, want in sorted(expected.items())
                 if published.get(inv, {}).get("partly_superseded_by") != want]
        self.assertEqual(
            [], wrong,
            "the manifest does not carry the partial-supersession pointer the register "
            "records: %s. A consumer reading the field structurally sees null and concludes "
            "there is no partial supersession" % "; ".join(wrong))

    def test_a_partial_stays_active(self):
        """⛔ The direction that would be dangerous: never report a partial as superseded."""
        published = self.published()
        wrong = sorted(i for i, e in published.items()
                       if e.get("partly_superseded_by") and e["status"] != "active")
        self.assertEqual(
            [], wrong,
            "partly-superseded invariant(s) published with a non-active status: %s. Only a "
            "clause was replaced; the rule still binds, and reporting it superseded tells a "
            "child the whole thing is obsolete" % ", ".join(wrong))


if __name__ == "__main__":
    unittest.main()
