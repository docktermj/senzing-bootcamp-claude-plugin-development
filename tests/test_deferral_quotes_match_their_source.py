"""A `DEFERRED INVARIANT` block quotes its rules verbatim from the shipping file.

The blocks are what the maintainer approves an invariant FROM. They are written by
copying the rule out of the file it ships in, and on 2026-09-01 seven of them had been
copied through something that truncates at ~110 characters -- the same cut
`conformance.py since` applies to its own display. What landed in the ledger read as a
complete rule and stopped mid-sentence:

    "The `_measured_at` marker is not bookkeeping -- it is what lets a later step tell a
     complete -- in `module-02-sdk-setup/SKILL.md`, Step 5a sub-step 3."

with the bold left unterminated, so the markdown after it rendered wrong too. One was
worse than truncated: the `get_license()` bullet had "resolves the license **against the
engine configuration**", a phrase that appears nowhere in the source, which says "from
the settings it is handed, and the settings here do not yet carry `CONFIGPATH`". A
paraphrase in a quotation slot is the failure this guards -- the maintainer approving
from it would be approving wording the plugin does not ship.

⚠️ This checks the QUOTE against the SOURCE, not the drafted invariant wording against
anything. The drafted wording is new text and has nothing to be verbatim against.

⛔ (INV-315) The rules are read by `pending_invariants.parse()`, over every deferral block,
resolved ones included (#236). Only a quotation is compared. A description is sorted apart
and never reported as mismatched, and a bullet no shape matches, or a location nothing
resolves, fails this guard by name.

⚠️ Reading through `parse()` does NOT establish that the quote it reads is the rule. `QUOTE`
takes a bullet's first bold span, so a bullet that opens with a bold label has its LABEL
checked. One such bullet exists (a resolved block's `6d (desired outcome).`). A change to how
bullets are classified belongs in the parser, where the review queue gets it too, not here.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import importlib.util
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "senzing-bootcamp"
LEDGER = REPO / "specs" / "IMPLEMENTED.md"
HELPER = REPO / ".claude" / "skills" / "review-invariants" / "pending_invariants.py"


def _helper():
    """Import `pending_invariants.py` so its resolution roots are used, not copied.

    ⛔ **This file kept a THIRD copy of `resolve()` until #59** -- the skill's helper had
    one, `cmd_check` inlined a second, and this guard reimplemented a third. A widening
    that reached two of the three would leave this guard disagreeing with the tool it
    guards, which is exactly how `conformance.py`'s 2026-09-14 widening shipped a stale
    second copy that passed only because nothing had yet used the new scope.

    ⚠️ **The trade is real and is accepted deliberately:** importing the module under test
    means this guard can no longer catch the resolver itself being wrong -- if `resolve`
    goes blind, both sides go blind together. That is the right trade here because this
    guard's subject is the **ledger's quotes**, not the resolver; `tests/test_review_invariants_queue.py`
    exercises the helper's reported counts from the outside, which is where a broken
    resolver now surfaces (as `unresolved`, which it asserts is zero).

    Stdlib only (INV-108): `importlib` loads a file in this repository, not a package.
    """
    spec = importlib.util.spec_from_file_location("pending_invariants", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_HELPER_MOD = _helper()
#: The one definition, imported rather than restated.
resolve = _HELPER_MOD.resolve
RESOLUTION_ROOTS = _HELPER_MOD.RESOLUTION_ROOTS
#: ⛔ **(INV-315) The rules are READ by the primary verifier's parser, never by a pattern here.**
#: Until #236 this file classified rule bullets with a regex of its own. It had no notion of a
#: rule's kind, so a description in the quoted shape would have been compared as a quotation;
#: its unparsed count saw only the shape it expected; and a location `resolve()` could not
#: resolve was dropped without a word. None of the three occurred in the ledger, so each was a
#: failure waiting for its first bullet. `parse()` carries the kind and reports what it cannot
#: read, so this guard inherits both instead of keeping a second reader of the same corpus.
parse = _HELPER_MOD.parse
#: `include_resolved=True` because a registered block's quotes still name shipping rules. The
#: review queue never shows those blocks, and the helper keeps their boundaries in one place.
blocks = _HELPER_MOD.blocks

#: A rule gains `(INV-NNN)` at its line when the deferral is approved, so the shipped text
#: legitimately differs from the quote by exactly that. Normalize it off BOTH sides rather
#: than re-editing every quote at mint time -- ten deferrals are still pending.
CITATION = re.compile(r"\(INV-\d{3}\)\s*")


def flat(s):
    """Collapse whitespace and drop `(INV-NNN)` citations, so a minted rule still matches.

    The source wraps these rules across lines and the ledger does not, and an approved rule
    carries a citation the deferral's quote predates. Neither difference is a misquote.
    """
    return CITATION.sub("", re.sub(r"\s+", " ", s)).strip()


def sort_rules(deferrals):
    """Sort every rule `parse()` reads out of `deferrals` by what this guard does with it.

    * ``quoted``      -- compared against the file it names: (where, quote, location, path, resolved)
    * ``no_site``     -- a quotation naming no location. Skipped and counted apart, as `cmd_check`
                         counts `no_site`: the rule is stated in the no-prose-site form, so
                         nothing is owed and nothing is wrong.
    * ``described``   -- one author's summary of the rule at a location. ⛔ (INV-315) Never
                         compared, so never reported as mismatched: it was never a quote.
    * ``unresolved``  -- a location was named and resolves under no root. ⛔ (INV-308) A failure.
    * ``unparsed``    -- a rule bullet matching no known shape. ⛔ (INV-315) A failure.
    """
    out = {k: [] for k in ("quoted", "no_site", "described", "unresolved", "unparsed")}
    for b in deferrals:
        p = parse(b)
        where = f"IMPLEMENTED.md:{b['line']} ({b['spec']})"
        out["unparsed"].extend((where, line) for line in p["unparsed"])
        for r in p["rules"]:
            if r["kind"] != "quoted":
                out["described"].append((where, r["text"], r["where"]))
            elif r["site"] is None:
                out["no_site"].append((where, r["text"]))
            elif resolve(r["site"]) is None:
                out["unresolved"].append((where, r["text"], r["site"]))
            else:
                out["quoted"].append((where, flat(r["text"]), r["site"], resolve(r["site"]),
                                      b.get("resolved", False)))
    return out


def ledger_rules():
    """Every rule in every deferral block of the ledger, resolved blocks included."""
    return sort_rules(blocks(include_resolved=True))


def fake_block(*bullets):
    """A one-block ledger holding `bullets`, for testing how a shape is sorted."""
    return [{"spec": "fixture", "line": 0, "text": "\n".join(bullets), "resolved": False}]


class DeferralQuotesAreVerbatim(unittest.TestCase):
    def setUp(self):
        self.cache = {}
        self.rules = ledger_rules()

    def source(self, path):
        if path not in self.cache:
            self.cache[path] = flat(path.read_text(encoding="utf-8"))
        return self.cache[path]

    def test_the_scan_finds_the_quotes(self):
        """A guard that silently matches nothing certifies nothing."""
        self.assertGreaterEqual(
            len(self.rules["quoted"]), 10,
            "the parser read almost no quoted rules out of the deferral blocks — the ledger's "
            "deferral shape has changed and this guard is no longer reading it.",
        )

    def test_resolved_blocks_are_read_too(self):
        """A registered block's quotes name shipping rules; the queue alone drops them all."""
        self.assertTrue(
            any(q[4] for q in self.rules["quoted"]),
            "no quoted rule came from a resolved deferral block, so every registered block's "
            "quotes are unchecked. Read the ledger with `blocks(include_resolved=True)`.",
        )

    def test_every_queued_block_is_read(self):
        """Enumerating the resolved blocks must not cost a pending or held one."""
        every = {b["line"]: b["text"] for b in blocks(include_resolved=True)}
        lost = [f"IMPLEMENTED.md:{b['line']} ({b['spec']})" for b in blocks()
                if every.get(b["line"]) != b["text"]]
        self.assertEqual([], lost, "the review queue holds block(s) this guard does not read")

    def test_no_rule_bullet_is_unparsed(self):
        """⛔ (INV-315) A bullet no shape matches is unchecked, so this guard is not clean."""
        self.assertEqual(
            [], [f"{w}: {line[:150]}" for w, line in self.rules["unparsed"]],
            "rule bullet(s) in a deferral block match no shape `pending_invariants.parse()` "
            "knows, so their quotes are unchecked while this guard would report a clean run.",
        )

    def test_every_named_location_resolves(self):
        """⛔ (INV-308) A location that resolves nowhere leaves its quote unverified."""
        self.assertEqual(
            [], [f"{w}: names `{loc}` for: {q[:100]}" for w, q, loc in self.rules["unresolved"]],
            "rule(s) name a location that resolves under no root in RESOLUTION_ROOTS, so the "
            "quote behind that location is unverified. Fix the path, or state the rule in the "
            "no-prose-site form.",
        )

    def test_every_quoted_rule_appears_verbatim_in_the_file_it_names(self):
        wrong = []
        for where, quote, loc, path, _ in self.rules["quoted"]:
            if quote not in self.source(path):
                wrong.append(f"{where} quotes {loc} as:\n      {quote[:150]}")
        self.assertEqual(
            [], wrong,
            "a DEFERRED INVARIANT block quotes a rule that its named file does not contain "
            "verbatim — the quote is truncated, paraphrased, or the rule has since been "
            "reworded:\n  " + "\n  ".join(wrong),
        )

    def test_no_quoted_rule_leaves_its_bold_unterminated(self):
        """The truncation's visible symptom, caught even if the text were to match."""
        odd = [
            f"IMPLEMENTED.md:{i}"
            for i, line in enumerate(LEDGER.read_text(encoding="utf-8").splitlines(), 1)
            if line.lstrip().startswith("- ⛔ **") and line.count("**") % 2
        ]
        self.assertEqual(
            [], odd,
            f"a rule bullet opens bold and never closes it: {odd}. That is the signature of "
            "a quote cut off mid-sentence, and it corrupts the markdown after it.",
        )


class RuleKindsAreSortedApart(unittest.TestCase):
    """What the guard does with each shape `parse()` can return, on bullets built here."""

    REAL = "skills/module-01-business-problem/phase1-discovery.md"

    def test_a_described_rule_is_never_compared(self):
        """⛔ (INV-315) Prose that quotes nothing is not a mismatch -- even beside a quote span."""
        r = sort_rules(fake_block(
            f"    - `{self.REAL}` — ⛔ prose appearing nowhere in the file, "
            f"⛔ **Invented** — in `{self.REAL}`"))
        self.assertEqual(1, len(r["described"]))
        self.assertEqual([], r["quoted"], "a described rule was queued for a verbatim comparison")

    def test_a_quote_naming_no_location_is_counted_apart(self):
        r = sort_rules(fake_block("    - ⛔ **A rule stated in the no-prose-site form.**"))
        self.assertEqual(1, len(r["no_site"]))
        self.assertEqual([], r["quoted"] + r["unresolved"] + r["unparsed"])

    def test_an_unresolvable_location_is_reported(self):
        r = sort_rules(fake_block("    - ⛔ **A rule.** — in `no/such/file.md`"))
        self.assertEqual("no/such/file.md", r["unresolved"][0][2])
        self.assertEqual([], r["quoted"], "a quote was checked against a file that does not exist")

    def test_an_unparsable_bullet_is_reported(self):
        r = sort_rules(fake_block("    - ⛔ a bullet in neither shape"))
        self.assertEqual(1, len(r["unparsed"]))


if __name__ == "__main__":
    unittest.main()
