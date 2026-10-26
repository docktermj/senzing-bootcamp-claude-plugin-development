"""Prose must not call an amendment pending once `INVARIANTS.md` carries the note.

Enforces **INV-386**, registered by the maintainer 2026-10-20. ⚠️ It **cannot** establish that a docstring left alone describes its amendment correctly, only that it does not call a registered one pending. (**Complements INV-308**, which binds a tool's report of what it could not verify rather than a docstring's account of a rule's status; **complements INV-365**, which binds who may write the registry and is satisfied either way; **complements INV-300**, which binds where a rule is stated rather than whether a statement of its status has gone stale.

`/review-invariants`' Register path resolves the deferral block it registers
(`.claude/skills/review-invariants/SKILL.md`, step 6), and applying a `PROPOSED AMENDMENT`
marks its bullet `applied YYYY-MM-DD` so it leaves the queue. Both act on the **ledger**.
Nothing acted on the prose elsewhere that had already described the same amendment as waiting,
so a guard's own docstring kept telling its reader that the rule the guard enforces is not yet
binding — INV-308's failure shape pointed inward, where the prose says less than the code does.
`tests/test_deferral_freshness.py` checks plugin *porting* deferrals only and never saw it.

⛔ **(INV-246) The site set is DERIVED BY SCANNING, never listed.** The discriminating fact —
whether INV-nnn's registered text already carries the note that #mmm proposed — is read out of
`specs/INVARIANTS.md` itself, so the guard finds a site nobody thought of. That is not
decoration here: #691 was filed naming **five** files, and scanning found **nine**. The four it
missed (`test_generated_data_supports_its_success_criteria.py`,
`test_license_env_var_absent.py`, `test_synthesized_name_sharing_has_a_budget.py`,
`test_truthset_viz_no_live_server_completes.py`) say the same thing in four other phrasings.

**The rule, stated as this file enforces it.** In a scanned file, a block that claims an
amendment is still awaiting the maintainer MUST NOT name an (invariant id, note marker) pair
that `specs/INVARIANTS.md` already carries as a dated note.

⚠️ **Scope: every file outside `specs/` (#796), stated with its reason (INV-246).** INV-386 binds
prose outside `specs/`, and until #796 this guard read only `tests/` and `.claude/`, so
`BLUEPRINT.md`'s decision log went on calling twenty-three registered amendments queued. Two
things stay out, each for a reason, not because a scan of it came back quiet:

- `specs/`: `specs/IMPLEMENTED.md` is the queue itself. A block there is *meant* to say "awaiting
  the maintainer's sign-off; NOT applied" until it is applied, and its resolution is the
  `applied YYYY-MM-DD` marker that `pending_invariants.py` writes and
  `tests/test_amendments_are_queued.py` pins. Sweeping it here would report the queue's own
  vocabulary and would put a second owner on one rule (INV-300). `specs/INVARIANTS.md` is the
  registry, which only `/review-invariants` writes (INV-365), and `specs/` is a read-only
  archive whose entries record history verbatim (INV-307).
- The generated `invariant-manifest.json`, whose path is read from `invariant_manifest.py`'s own
  `MANIFEST` (INV-384) and kept in ``EXEMPT``, which ``TheExemptionsAreDerivedAndAlive`` checks
  against the listing: it copies every registered statement verbatim into one JSON document, so
  ids and markers sit together in it by construction rather than by a claim.

⚠️ **The unit is one list item, or one block where there is no list (#796).** `BLUEPRINT.md`'s
decision log is one list of hundreds of items with no blank line between them, so read as one
block every id in it paired with every claim. ``_wrapped_text.collapsed_items`` reads each item on
its own. Within a unit, a claim pairs with the issue markers of **its own sentence** when that
sentence carries any ("a correction is queued as a `PROPOSED AMENDMENT` block … (#520)" is about
#520, not a #572 two sentences earlier), and with every marker in the unit otherwise, because a
claim may name its subject a sentence earlier ("Source issue: #512. Enforces the … amendment …
queued in …"; INV-282).

⚠️ **Wrap-aware (INV-346).** The claim is a sentence, and Markdown wraps a sentence wherever
the column runs out, so the scan reads through ``_wrapped_text.collapsed_blocks`` and reports
the line each claim started on. The registry side is read one invariant entry at a time, with
the entry's whitespace collapsed: an entry is the unit a dated note belongs to, and
``collapsed_blocks`` would join consecutive entries into one block and lose that attribution.

⚠️ **The vocabulary is the sign-off claim, not the block's name, and it was measured before it
was narrowed (INV-282).** A first reading took `PROPOSED AMENDMENT` and a bare "pending" as
triggers too: 287 blocks repository-wide, 11 of them in `tests/` naming a registered pair, and
**three of those eleven were correct prose** — `tests/test_invariant_layout_tree.py`'s two-state
pin, which describes a `PROPOSED AMENDMENT` block `/review-invariants` applied on 2026-09-30
and a second one that is genuinely queued. The reason is in the skill's own "Writing one"
section: a block keeps the words `PROPOSED AMENDMENT` after it is applied, and only the bullet's
marker changes. So the block's name is not a claim about today; the sign-off claim is. Narrowing
to the claim dropped all three, and — because a claim-derived matcher is wider in the other
direction — caught `test_license_env_var_absent.py`, whose "queued in #654" neither the issue's
list nor the first vocabulary had reached.

⛔ **A legitimately pending amendment MUST still be sayable**, which is why the discriminator is
the registry and not the words. A `DEFERRED INVARIANT` writes `INV-NNN` and names no existing
id; a queued `PROPOSED AMENDMENT` names an id whose registered text does **not** yet carry that
marker. Both are pinned below as must-not-flag fixtures, with the registered counterpart of the
second pinned beside them so the pair, not the phrasing, is what decides.

⚠️ **Past tense is matched too, deliberately**, which is where this differs from
`tests/test_no_stale_blocked_claim.py`'s present-tense-only rule. There the subject is a claim
about the repository that stays sayable as history; here the reader's mistake *is* the
ambiguity — a sentence naming a registered pair beside "was awaiting the maintainer's sign-off"
reads to a skimming maintainer exactly like one that still is. So a file that needs to narrate
the history writes it without the claim's words ("an amendment the maintainer had yet to rule
on"), as `tests/test_dev_install_surfaces_name_the_dev_repo.py` now does. The one file that
must quote the phrasings verbatim is this one, and it is scanned out below.

⛔ **This file scans itself out.** It MUST hold the pre-#691 phrasings as fixtures — that is
what calibrates the check — so a scan including it would report its own controls. The exclusion
is one path, resolved from ``__file__`` rather than written down, and stated rather than
achieved by a pattern that happens to miss them, which would also miss the real thing.

⚠️ **What this cannot establish:** that a docstring left alone describes its amendment
*correctly*, only that it does not call a registered one pending. It says nothing about an
amendment whose note was never written, and nothing about whether applying one was wise.

Stdlib only; every file is read as text, never imported (INV-108).

Source issue: #691.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files  # noqa: E402
from _wrapped_text import collapsed_items, line_of  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
REVIEW_SKILL = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "SKILL.md"
MANIFEST_TOOL = REPO_ROOT / ".claude" / "skills" / "review-invariants" / "invariant_manifest.py"

#: The one top-level tree not scanned; see the scope note above. Everything else is (#796).
UNSCANNED_ROOT = "specs"


def generated_files():
    """The generated invariant manifest's repo-relative path, read from its generator (INV-384).

    ``None`` when the generator cannot be read, never a fallback literal (INV-308):
    ``TheExemptionsAreDerivedAndAlive`` then says so rather than letting the scan widen quietly.
    """
    try:
        spec = importlib.util.spec_from_file_location("invariant_manifest_for_386", MANIFEST_TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return frozenset({Path(module.MANIFEST).resolve().relative_to(REPO_ROOT).as_posix()})
    except Exception:
        return None


#: Generated files outside `specs/` the scan excuses: the manifest copies every registered
#: statement verbatim into one JSON document, so ids and markers co-occur in it by construction.
GENERATED = generated_files()

#: ⛔ Every path exemption this guard applies, in ONE registry, so each is checked for life.
EXEMPT = {"GENERATED": GENERATED or frozenset()}

#: One invariant entry: "- **INV-nnn** — body", to the next entry or the next heading. The same
#: shape `tests/test_invariant_enforcer_citations.py` splits the registry with (INV-300).
ENTRY = re.compile(r"^- \*\*(INV-\d{3})\*\* — (.+?)(?=\n- \*\*INV-|\n##|\Z)", re.M | re.S)

#: A dated note inside one entry: its date and the issue marker it was written for, as
#: `INVARIANTS.md` writes them — "**Dated note, 2026-10-12 (#505):**", "**Dated correction,
#: 2026-10-04 (#419):**", "**Dated clarification, …**", "**Dated scope note, …**".
REGISTERED_NOTE = re.compile(r"\*\*Dated [^*]{0,160}?(\d{4}-\d{2}-\d{2})[^*]{0,160}?\(#(\d+)\)")

#: The sign-off claim: prose asserting the registry has not taken the amendment yet. ⛔ Derived
#: from the CLAIM, not from the phrasings at the sites (INV-282) — see the measurement above.
#: ``(?:is|are|was|were) queued`` was added by #796, when the scan reached `BLUEPRINT.md`, whose
#: decision log says "a `PROPOSED AMENDMENT to INV-nnn` is queued" of amendments long registered.
PENDING_CLAIM = re.compile(
    r"(?i)await(?:s|ing)\s+(?:the\s+maintainer|sign-?off)"
    r"|queued\s+(?:for\s+the\s+maintainer|for\s+sign-?off|in\b)"
    r"|\b(?:is|are|was|were)\s+queued\b"
    r"|(?:not|never)\s+(?:yet\s+)?(?:applied|registered|signed[\s-]?off)")

#: Where one sentence ends inside a unit: terminal punctuation, any closing marks, then space.
SENTENCE_END = re.compile(r"[.!?][*_)`'\"]*\s+")

INVARIANT_ID = re.compile(r"INV-(\d{3})")
ISSUE_MARKER = re.compile(r"#(\d+)")


def registered_notes(text):
    """``{(invariant id, '#marker'): date}`` for every dated note the registry carries.

    A pure function over `INVARIANTS.md`'s text, read one entry at a time with the entry's
    whitespace collapsed, so a note whose header wraps is still found (INV-346).
    """
    notes = {}
    for invariant, body in ENTRY.findall(text):
        flat = " ".join(body.split())
        for date, marker in REGISTERED_NOTE.findall(flat):
            notes.setdefault((invariant, "#" + marker), date)
    return notes


def pending_claims(text, notes):
    """Every block of ``text`` that calls an amendment ``notes`` already carries pending.

    A pure function over one file's text, so each negative control runs this same check over a
    mutated copy (INV-265). Each problem reads ``line N: …`` and names the pair it found.
    """
    problems = []
    for flat, origin in collapsed_items(text):
        ids = {"INV-" + n for n in INVARIANT_ID.findall(flat)}
        named, claim = [], None
        for claim in PENDING_CLAIM.finditer(flat):
            markers = claimed_markers(flat, claim.start())
            named = sorted((i, m, notes[(i, m)]) for i in ids for m in markers if (i, m) in notes)
            if named:
                break
        if not named:
            continue
        problems.append(
            "line %d calls %s pending (%r), but it is registered: %s"
            % (line_of(origin, claim.start()), " and ".join(i for i, _m, _d in named),
               claim.group(0),
               "; ".join("%s's %s note (%s)" % (i, d, m) for i, m, d in named)))
    return problems


def claimed_markers(flat, at):
    """The issue markers a claim at ``at`` can be about (#796).

    The markers of the claim's own sentence when it carries any: "a correction is queued as a
    `PROPOSED AMENDMENT` block (#520)" is about #520, not about a #572 two sentences earlier in
    the same paragraph. Otherwise every marker in the unit, because a claim may name its subject
    in an earlier sentence ("Source issue: #512. Enforces the amendment … queued in …"; INV-282).
    """
    start = 0
    for end in SENTENCE_END.finditer(flat):
        if end.end() > at:
            sentence = flat[start:end.start() + 1]
            break
        start = end.end()
    else:
        sentence = flat[start:]
    own = {"#" + n for n in ISSUE_MARKER.findall(sentence)}
    return own or {"#" + n for n in ISSUE_MARKER.findall(flat)}


def exempted():
    """Every repo-relative path the registry excuses, flattened."""
    return {rel for paths in EXEMPT.values() for rel in paths}


def scanned_files():
    """The files this guard reads: every file outside `specs/`, by SCANNING (INV-246, #796),
    minus this one and the registry's exemptions."""
    here, exempt = Path(__file__).resolve(), exempted()
    out = []
    for path in corpus_files(root=REPO_ROOT):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if PurePosixPath(rel).parts[0] == UNSCANNED_ROOT or rel in exempt:
            continue
        if path.resolve() != here:
            out.append(path)
    return out


def scanned_texts():
    """``(repo-relative path, text)`` for every readable scanned file."""
    for path in scanned_files():
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield Path(path).relative_to(REPO_ROOT).as_posix(), text


def mutate(test, text, old, new):
    """Replace ``old`` once; fail the control if the anchor text has gone."""
    test.assertIn(old, text, "the control's anchor text is gone; update the control")
    return text.replace(old, new, 1)


def shipped(relative):
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


#: The nine sites #691 corrected, as ``(path, as it reads now, as it read before)``. ⛔ This is a
#: list of CONTROLS, never the guard's site set — the site set is scanned. Each control puts one
#: pre-#691 phrasing back and asserts the check reports it.
PRE_691 = (
    ("tests/test_windows_powershell_guidance.py",
     "`$NAME` in a shipped PowerShell fence, which INV-167 carries as its registered 2026-10-12\n"
     "note (#505).",
     "`$NAME` in a shipped PowerShell fence; the INV-167 amendment naming it is drafted in "
     "#505's\n`specs/IMPLEMENTED.md` entry, awaiting the maintainer's sign-off."),
    ("tests/test_skills_state_their_commands_argument_handling.py",
     "INV-333 names that module in its\nregistered 2026-10-15 note (#610).",
     "a dated note naming that module\nis a `PROPOSED AMENDMENT` to INV-333 awaiting the "
     "maintainer's sign-off (#610)."),
    ("tests/test_skipped_mapping_status.py",
     "Step 16's new condition is what INV-344's registered 2026-10-12 note (#527) states.",
     "Step 16's new condition is what INV-344's proposed #527 amendment states (queued for the\n"
     "maintainer's sign-off)."),
    ("tests/test_gate_options_have_handling_steps.py",
     "(INV-345's registered 2026-10-12\nnote)",
     "(INV-345's 2026-10-12 note, queued for\nthe maintainer's sign-off)"),
    ("tests/test_dev_install_surfaces_name_the_dev_repo.py",
     "was added by #610 and is binding:\nINV-360's base text names three, and its registered "
     "2026-10-15 note (#610) widens it to four.\n`SURFACES` below lists all four, which is the "
     "count this docstring and INV-360 both state.",
     "was added by #610; INV-360 names\nthree, and the dated note that widens it to four is a "
     "`PROPOSED AMENDMENT` awaiting the\nmaintainer's sign-off in #610's "
     "`specs/IMPLEMENTED.md` entry."),
    ("tests/test_generated_data_supports_its_success_criteria.py",
     "and none it should not), as\nINV-239's registered 2026-10-09 note (#459) states.",
     "and none it should not); the\namendment is drafted, not applied, in the "
     "`specs/IMPLEMENTED.md` entry for #459."),
    ("tests/test_synthesized_name_sharing_has_a_budget.py",
     "and none it should not), as\nINV-239's registered 2026-10-09 note (#458) states.",
     "and none it should not); the\namendment is drafted, not applied, in the "
     "`specs/IMPLEMENTED.md` entry for #458."),
    ("tests/test_truthset_viz_no_live_server_completes.py",
     "Source issue: #512. Enforces INV-130's registered 2026-10-12 note (#512).",
     "Source issue: #512. Enforces the PROPOSED AMENDMENT to INV-130 queued in "
     "`specs/IMPLEMENTED.md`."),
    ("tests/test_license_env_var_absent.py",
     "Enforces **INV-208**, as amended by its registered 2026-10-15 note (#654).",
     "Enforces **INV-208** (as amended by the 2026-10-15 note queued in #654)."),
)

#: A `DEFERRED INVARIANT` block, in the shape `review-invariants` documents. It writes `INV-NNN`
#: and names no existing id, so no pair can form however many real ids and markers sit beside
#: it, and its pending wording is correct. MUST NOT be flagged.
DEFERRAL_FIXTURE = """- **DEFERRED INVARIANT — awaiting the maintainer's sign-off; NOT minted.**
  **INV-NNN** — the drafted wording, in full; it extends INV-246 and INV-308 (#691)."""

#: Prose about an amendment the registry does NOT carry. MUST NOT be flagged.
#:
#: ⚠️ **This marker is synthetic, and that is a deliberate change made 2026-10-19.** It named
#: #686 until then, a genuinely queued `PROPOSED AMENDMENT to INV-050`. The 2026-10-19
#: `/review-invariants` session applied every queued amendment in the ledger — twelve of them —
#: so no real queued pair was left to point at, and the previous design's own failure message
#: ("move the fixture to a block that is still queued") had nowhere to send it. Re-pointing it at
#: the next queued amendment would only restart that clock. A marker no issue will carry keeps
#: the property under test — *the registry decides whether prose is stale, not the phrasing* —
#: without the fixture expiring every time the maintainer clears the queue.
#:
#: `test_a_queued_amendment_is_not_flagged` asserts the pair really is absent before relying on
#: it, so if #999686 ever becomes real the guard says so rather than passing vacuously.
QUEUED_MARKER = "#999686"
QUEUED_FIXTURE = (
    "Enforces the `PROPOSED AMENDMENT to INV-050` drafted in %s's `specs/IMPLEMENTED.md`\n"
    "entry, which is awaiting the maintainer's sign-off." % QUEUED_MARKER)

#: The same sentence with the marker swapped for one INV-050 already carries. MUST be flagged:
#: the registry decides, not the phrasing.
APPLIED_FIXTURE = QUEUED_FIXTURE.replace(QUEUED_MARKER, "#286")


class NoScannedFileCallsARegisteredAmendmentPending(unittest.TestCase):
    """Every file outside `specs/`, derived by scanning (INV-246, #796)."""

    @classmethod
    def setUpClass(cls):
        cls.notes = registered_notes(INVARIANTS.read_text(encoding="utf-8"))
        cls.corpus = list(scanned_texts())

    def test_every_scanned_file_is_clean(self):
        for relative, text in self.corpus:
            if "INV-" not in text:
                continue
            with self.subTest(site=relative):
                self.assertEqual(
                    [], pending_claims(text, self.notes),
                    "%s describes an amendment as still awaiting the maintainer, but "
                    "`specs/INVARIANTS.md` already carries it as a dated note. State it as "
                    "registered, with the note's date." % relative)

    def test_the_registry_derivation_read_the_registry(self):
        """⛔ (INV-265) An empty derivation would make every file above pass vacuously."""
        self.assertGreater(
            len(self.notes), 50,
            "fewer than 50 dated notes were derived from `specs/INVARIANTS.md`; the entry or "
            "note pattern has stopped matching and every check above passes for free")
        self.assertGreater(
            len({invariant for invariant, _marker in self.notes}), 20,
            "the derived notes cluster on too few invariants; the entry split is broken")
        for anchor in (("INV-167", "#505"), ("INV-360", "#610"), ("INV-344", "#527")):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, self.notes,
                              "%s is not derived from the registry, so the discriminator is "
                              "not reading what it claims to" % (anchor,))

    def test_the_scan_read_the_corpus_it_claims_to(self):
        """⛔ (INV-265) An empty corpus is an unrun check, never a pass."""
        self.assertGreater(len(self.corpus), 200,
                           "the scan found almost no files; it is not scanning")
        relatives = {relative for relative, _text in self.corpus}
        self.assertIn(".claude/skills/review-invariants/SKILL.md", relatives,
                      "the scan is not reaching `.claude/`")
        for outside in ("BLUEPRINT.md", "README.md"):
            self.assertIn(outside, relatives, "#796: the scan is not reaching %s" % outside)
        self.assertTrue(any(r.startswith("plugins/") for r in relatives),
                        "#796: the scan is not reaching `plugins/`")
        self.assertFalse(any(r.startswith("specs/") for r in relatives),
                         "a file under `specs/` is in the scanned set; see the scope note")
        self.assertFalse(relatives & exempted(), "an exempted file is in the scanned set")
        self.assertNotIn("tests/" + Path(__file__).name, relatives,
                         "this file scans itself, so its own controls would be reported")
        self.assertNotIn("specs/INVARIANTS.md", relatives,
                         "the registry is in the scanned set; see the scope note")


class TheExemptionsAreDerivedAndAlive(unittest.TestCase):
    """⛔ INV-384: the one exemption is read from its generator and names a listed file."""

    def test_the_generated_exemption_is_derived(self):
        self.assertIsNotNone(GENERATED, "%s could not be read, so the manifest is not exempted "
                                        "and its verbatim copies would be scanned" % MANIFEST_TOOL)
        self.assertTrue(exempted(), "the exemption registry is empty")

    def test_every_exemption_names_a_listed_file(self):
        listed = {p.relative_to(REPO_ROOT).as_posix() for p in corpus_files(root=REPO_ROOT)}
        dead = sorted(exempted() - listed)
        self.assertEqual([], dead, "an exemption names no file the repository has: %s" % dead)

    def test_without_the_exemption_the_manifest_would_be_reported(self):
        """The exemption is load-bearing, not decoration: the manifest trips the claim as text."""
        (manifest,) = sorted(GENERATED)
        text = (REPO_ROOT / manifest).read_text(encoding="utf-8")
        notes = registered_notes(INVARIANTS.read_text(encoding="utf-8"))
        self.assertTrue(pending_claims(text, notes))


#: `BLUEPRINT.md`'s #574 decision-log item as it read before #796: the site the scan now reaches.
BLUEPRINT_574 = (
    "- #573: `/release-cycle` runs the release cycle as stages 0 to 6.\n"
    "- #574: two `PROPOSED AMENDMENT` blocks are queued in the ledger for\n"
    "  `/review-invariants`, one letting a single yes cover several records shown\n"
    "  whole in one numbered message (INV-314, `submit_feedback` and unattended\n"
    "  runs unchanged) and one saying a label applied through\n"
    "  `/refine-github-issue` is the maintainer choosing (INV-318)\n"
    "- #575: the sites reworded.\n")


class TheWideningOf796(unittest.TestCase):
    """#796: `BLUEPRINT.md` and the rest outside `specs/` are scanned, item by item."""

    @classmethod
    def setUpClass(cls):
        cls.notes = registered_notes(INVARIANTS.read_text(encoding="utf-8"))
        cls.blueprint = shipped("BLUEPRINT.md")

    def test_the_shipped_blueprint_is_clean(self):
        self.assertEqual([], pending_claims(self.blueprint, self.notes))

    def test_the_574_item_as_it_read_is_reported(self):
        """The negative control: the BLUEPRINT site, as it shipped, reported at its line."""
        self.assertIn(("INV-314", "#574"), self.notes)
        problems = pending_claims(BLUEPRINT_574, self.notes)
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(problems[0].startswith("line 2 "), problems)
        self.assertIn("INV-314", problems[0])

    def test_the_574_item_put_back_into_the_blueprint_is_reported(self):
        now = "- #574: two 2026-10-13 notes are registered, one letting"
        before = "- #574: two `PROPOSED AMENDMENT` blocks are queued in the ledger for\n  one letting"
        mutated = mutate(self, self.blueprint, now, before)
        self.assertTrue(any("INV-314" in p for p in pending_claims(mutated, self.notes)))

    def test_is_queued_is_a_claim(self):
        for verb in ("is", "are", "was", "were"):
            with self.subTest(verb=verb):
                text = "- #517: a `PROPOSED AMENDMENT to INV-356` %s queued (closed lists)" % verb
                self.assertTrue(pending_claims(text, self.notes))

    def test_a_claim_and_a_pair_in_different_items_do_not_pair(self):
        text = ("- #517: a `PROPOSED AMENDMENT to INV-356` landed.\n"
                "- #999686: an amendment to INV-050 is queued for `/review-invariants`\n")
        self.assertEqual([], pending_claims(text, self.notes))
        self.assertTrue(pending_claims(text.replace("#999686", "#286"), self.notes))

    def test_a_claim_sentence_with_its_own_marker_pairs_only_with_it(self):
        """Must-not-flag (INV-282): the BLUEPRINT dry-run paragraph's procedural sentence."""
        text = ("Run it as #572 says. Findings are drafted into a ledger entry (INV-317) in the "
                "issue-template shape; a new rule or a correction is queued as a `DEFERRED "
                "INVARIANT` or `PROPOSED AMENDMENT` block for `/review-invariants` (#520).")
        self.assertIn(("INV-317", "#572"), self.notes)
        self.assertEqual([], pending_claims(text, self.notes))
        self.assertTrue(pending_claims(text.replace(" (#520)", ""), self.notes),
                        "without its own marker the sentence pairs with the paragraph's")


class TheControlsPutEachCorrectedSiteBack(unittest.TestCase):
    """⛔ (INV-265) Each control runs ``pending_claims`` over the shipped text, mutated."""

    @classmethod
    def setUpClass(cls):
        cls.notes = registered_notes(INVARIANTS.read_text(encoding="utf-8"))

    def test_the_shipped_text_of_each_corrected_site_is_clean(self):
        for relative, _now, _before in PRE_691:
            with self.subTest(site=relative):
                self.assertEqual([], pending_claims(shipped(relative), self.notes))

    def test_each_pre_691_wording_is_reported(self):
        for relative, now, before in PRE_691:
            with self.subTest(site=relative):
                mutated = mutate(self, shipped(relative), now, before)
                self.assertTrue(
                    pending_claims(mutated, self.notes),
                    "putting %s's pre-#691 wording back is not reported, so the check does not "
                    "cover the defect it was written for" % relative)

    def test_the_whole_pre_691_corpus_is_reported_at_every_site(self):
        """The negative control the issue asks for: the text as every site read before #691."""
        reported = set()
        for relative, now, before in PRE_691:
            if pending_claims(mutate(self, shipped(relative), now, before), self.notes):
                reported.add(relative)
        self.assertEqual({relative for relative, _now, _before in PRE_691}, reported,
                         "the pre-#691 text of some corrected file is not reported")


class LegitimatelyPendingProseIsNotFlagged(unittest.TestCase):
    """⚠️ (INV-282) A guard that reports correct prose is relaxed, not worked around."""

    @classmethod
    def setUpClass(cls):
        cls.notes = registered_notes(INVARIANTS.read_text(encoding="utf-8"))

    def test_a_deferral_block_is_not_flagged(self):
        self.assertEqual([], pending_claims(DEFERRAL_FIXTURE, self.notes))

    def test_a_queued_amendment_is_not_flagged(self):
        self.assertNotIn(("INV-050", QUEUED_MARKER), self.notes,
                         "%s has become a real INV-050 note; the fixture's premise is gone, so "
                         "pick a marker the registry does not carry" % QUEUED_MARKER)
        self.assertEqual([], pending_claims(QUEUED_FIXTURE, self.notes))

    def test_the_same_block_with_a_registered_marker_is_flagged(self):
        """⛔ The pair decides, not the phrasing: one marker apart, the same words fail."""
        self.assertIn(("INV-050", "#286"), self.notes)
        self.assertTrue(pending_claims(APPLIED_FIXTURE, self.notes))

    def test_a_two_state_pin_is_not_flagged(self):
        """The live must-not-flag case: prose about an amendment that was applied."""
        text = shipped("tests/test_invariant_layout_tree.py")
        self.assertIn("PROPOSED AMENDMENT to INV-050", text,
                      "the two-state pin's wording has gone; this fixture measures nothing")
        self.assertEqual([], pending_claims(text, self.notes))


class TheAmendPathResolvesTheProseToo(unittest.TestCase):
    """`/review-invariants`' Amend path states the step whose absence let this ship."""

    @classmethod
    def setUpClass(cls):
        cls.text = REVIEW_SKILL.read_text(encoding="utf-8")

    def amend_section(self):
        start = self.text.index("\n### Amend\n")
        end = self.text.index("\n## ", start + 1)
        return self.text[start:end]

    def test_the_amend_section_states_the_resolve_the_prose_step(self):
        section = " ".join(self.amend_section().split())
        for phrase in ("resolve the prose", "scanning", "INV-246",
                       "tests/test_registered_amendments_are_not_called_pending.py"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section,
                              "the Amend path does not state the resolve-the-prose step")

    def test_the_register_path_still_resolves_its_block(self):
        """The step the Amend path is modeled on; if it moves, the model moves with it."""
        self.assertIn("**Resolve the block** in `IMPLEMENTED.md`", self.text)


if __name__ == "__main__":
    unittest.main()
