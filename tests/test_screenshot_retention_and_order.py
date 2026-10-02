"""Every captured tab reaches the recap, in the app's tab order.

Two bootcamper-reported defects in one instruction block.

**The count cap outlived its reason.** When `capture_screenshots.py` produced
three *viewport variants of one tab*, "keep the 2-3 most representative (delete
the rest)" was sound — two of the three were redundant. `INV-122` replaced that
with one image per tab, which makes every capture a distinct view, but only the
caption half of that sentence was rewritten. The count half survived and could
then only delete unique content: a six-tab app shipped three tabs, the same three
in both visualization sections, and the three that were dropped — Merge
Statistics, Match Keys, Feature Scores — are the analytical ones, because
"representative" pulls toward the visually striking.

**Nothing specified an order**, so images landed in filename-discovery order.
The recap is a walkthrough of the app, and its images ran Entity Graph →
Cross-Source → Search/Probe → Merge Statistics → Match Keys → Feature Scores
against an interface whose tabs run in a different order.

The tab table in `visualization-api-reference.md` is the single source for both
the tab set and their order; these tests assert both call sites defer to it.

Run:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp")
MODULE_COMPLETION = os.path.join(
    PLUGIN, "skills", "bootcamp-onboarding", "module-completion.md"
)
GRADUATION = os.path.join(PLUGIN, "skills", "graduation", "SKILL.md")
CONTRACT = os.path.join(
    PLUGIN, "skills", "module-03b-truthset-visualization", "visualization-api-reference.md"
)
EXAMPLE_RECAP = os.path.join(PLUGIN, "docs", "examples", "bootcamp_recap.example.md")

# The two files that decide which screenshots reach the recap and in what order.
#: Non-vacuity FLOOR, not the site set (INV-246).
KNOWN_CALL_SITES = (MODULE_COMPLETION, GRADUATION)


def call_sites():
    """Every shipped file invoking capture_screenshots — discovered, never listed.

    INV-246: the constant this replaces named two files under a comment claiming "both
    call sites", so a third would have left this guard green.
    """
    found = []
    for root, _dirs, files in os.walk(PLUGIN):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                if "capture_screenshots" in fh.read():
                    found.append(path)
    return tuple(sorted(found))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def flat(path):
    """Whitespace-collapsed text — these are wrapped prose, so a phrase
    assertion on the raw text is really an assertion about line breaks."""
    return re.sub(r"\s+", " ", read(path))


def shipped_markdown():
    for dirpath, dirnames, filenames in os.walk(PLUGIN):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


class TheDerivedCallSiteSetIsNotVacuous(unittest.TestCase):
    """INV-246: the call-site set is scanned, so a third invoker is covered on sight."""

    def test_the_known_call_sites_are_still_found(self):
        found = call_sites()
        for known in KNOWN_CALL_SITES:
            with self.subTest(file=os.path.basename(known)):
                self.assertIn(known, found,
                              "%s no longer invokes capture_screenshots, so this scan is "
                              "inspecting a smaller set than it believes"
                              % os.path.basename(known))


class NoCountCapSurvives(unittest.TestCase):

    def test_no_shipped_file_asks_for_the_most_representative(self):
        offenders = [
            os.path.relpath(p, REPO_ROOT)
            for p in shipped_markdown()
            if "most representative" in read(p)
        ]
        self.assertEqual(
            [], offenders,
            f"'most representative' selection survives in: {offenders}. Every capture "
            "is a distinct tab (INV-122), so selecting among them can only drop unique "
            "content — and it drops the analytical tabs first.",
        )

    def test_no_shipped_file_caps_the_number_kept(self):
        # Scoped by shape, not by the exact adjective, and swept across EVERY
        # shipped file rather than the two call sites.
        #
        # Both narrowings let real caps ship. The adjective list ("most"|"best")
        # missed `module-completion.md`'s surviving "embedding the 2-3 **curated**
        # screenshots is required" — in the very file whose ⛔ block says keep every
        # tab. The two-file scope missed the operative instruction at each capture
        # point: `module-03b/phase1-visualization.md` ("keep the 2-3 best") and
        # `module-07/phase1-query-visualize.md` ("embed the 2-3 best"), which is what
        # the agent actually reads when the screenshots are taken.
        pattern = re.compile(r"\b\d\s*-\s*\d\b\s+\w+\s+(?:screenshots?|images?)"
                             r"|\b\d\s*-\s*\d\b\s+(?:most|best|curated)"
                             r"|delete the rest")
        offenders = []
        for path in shipped_markdown():
            hit = pattern.search(flat(path))
            if hit:
                offenders.append(f"{os.path.relpath(path, REPO_ROOT)}: {hit.group(0)!r}")
        self.assertEqual(
            [], offenders,
            "a count cap deletes unique content now that capture is per-tab "
            f"(INV-146): {offenders}",
        )

    def test_module_completion_says_keep_every_tab(self):
        self.assertRegex(
            flat(MODULE_COMPLETION),
            r"[Kk]eep every captured tab",
            "the instruction must be to retain, not to select",
        )

    def test_graduation_backfills_all_not_a_best_few(self):
        self.assertRegex(
            flat(GRADUATION),
            r"\*\*all\*\* of them, not a \"best\" few|all of them, not a best few",
            "the backfill is the safety net for a missed embed — capping it means it "
            "cannot restore what the capture step dropped",
        )

    def test_the_example_recap_does_not_model_pruning(self):
        """A sample deliverable is guidance by demonstration."""
        self.assertNotIn("most representative", read(EXAMPLE_RECAP))


class OmittingAnInertCaptureIsNotAnOption(unittest.TestCase):
    """INV-146 permits deleting only a true same-tab duplicate; nothing may offer omission.

    INV-123 used to read "the caption MUST say so **or the image MUST be omitted**" for a
    Search / Probe tab captured from the static snapshot, and `module-completion.md` shipped
    that disjunction verbatim. It conflicted with INV-146, and — found 2026-07-31 — it did not
    even lose the image: graduation's backfill embeds every PNG the recap does not already
    reference and captions from the tab slug alone, so an omitted capture came back with a bare
    "Search / Probe" caption and nothing saying the search box is inert. That is the exact
    outcome INV-123 exists to prevent, reached by following INV-123.

    So the property is not "the image survives" — the backfill already guaranteed that. It is
    that **no shipped file offers omission as a remedy**, and that both sites requiring a
    caption say what the caption must disclose.
    """

    #: Omission offered as an *alternative* remedy, with an image-ish object. Deliberately
    #: narrow: a first attempt matched any "omit|drop|skip" near an image word and flagged
    #: legitimate prose — the recap PDF "reports every one it drops" is required by INV-162,
    #: and "the optional ones are yours to include or skip" is about modules. A guard that
    #: fires on the rule it is protecting gets deleted rather than fixed.
    #: The third branch catches an offer whose object is the *tab* the capture shows: Module 3b
    #: shipped "either omit the Search / Probe tab or caption it" until 2026-10-02 (#382), which
    #: the image-word branches could not see. Up to three words may name the tab.
    OMISSION_OF_AN_IMAGE = re.compile(
        r"\bor\s+(?:omit|drop)\s+(?:it|the\s+)?(?:image|screenshot|capture|png)\b"
        r"|\bor\s+the\s+(?:image|screenshot|capture)\s+(?:MUST\s+)?be\s+omitted"
        r"|\b(?:either|or)\s+(?:omit|drop)\s+the\s+(?:[\w/]+\s+){0,3}?tabs?\b",
        re.I,
    )
    #: In the two call sites the referent of a bare "or omit it" is always the capture, so the
    #: looser form is checked there. This is the exact wording that shipped until 2026-07-31.
    BARE_OMISSION_OFFER = re.compile(r"\bor\s+(?:omit|drop)\s+it\b", re.I)

    def test_no_shipped_file_offers_to_omit_an_image(self):
        offenders = []
        for path in shipped_markdown():
            for match in self.OMISSION_OF_AN_IMAGE.finditer(flat(path)):
                offenders.append("%s: %r" % (os.path.basename(path), match.group(0)))
        self.assertEqual(
            [], offenders,
            "shipped guidance offers omitting a captured image; INV-146 permits deleting only "
            "a true same-tab duplicate:\n  " + "\n  ".join(offenders),
        )

    def test_neither_call_site_offers_a_bare_omission(self):
        offenders = []
        for path in call_sites():
            for match in self.BARE_OMISSION_OFFER.finditer(flat(path)):
                offenders.append("%s: %r" % (os.path.basename(path), match.group(0)))
        self.assertEqual([], offenders, "\n  ".join(offenders))

    def test_both_patterns_catch_the_wording_that_shipped(self):
        """Positive controls, so neither guard can go vacuous after a rewording."""
        self.assertRegex("caption it explicitly as the empty/inactive state or omit it",
                         self.BARE_OMISSION_OFFER)
        self.assertRegex("the caption MUST say so or the image MUST be omitted",
                         self.OMISSION_OF_AN_IMAGE)
        self.assertRegex("either omit the Search / Probe tab or caption it as the inactive state",
                         self.OMISSION_OF_AN_IMAGE)

    def test_the_patterns_do_not_fire_on_the_rules_they_protect(self):
        """Negative controls for the false positives the first version produced."""
        for benign in (
            "omit this whole line if the bootcamper gave no takeaway",
            "the graduation PDF reports every one it drops, naming it on stderr",
            "a count cap can only delete unique content",
            "the optional ones are yours to include or skip",
        ):
            with self.subTest(benign=benign[:40]):
                self.assertNotRegex(benign, self.OMISSION_OF_AN_IMAGE)
                self.assertNotRegex(benign, self.BARE_OMISSION_OFFER)

    def test_the_capture_site_requires_the_inert_caption(self):
        text = flat(MODULE_COMPLETION)
        self.assertRegex(text, r"(?i)inert")
        self.assertRegex(text, r"(?i)caption it explicitly as the empty/inactive state")

    def test_the_capture_site_states_the_prohibition_as_a_gate(self):
        """Absence of the old wording is not the same as presence of the rule.

        A mutation that downgraded the ⛔ block to a plain note escaped every other check
        here: nothing offered omission, so the absence tests passed, while the instruction
        that omission is forbidden had lost the marker `ground-rules.md` makes mandatory.
        """
        text = flat(MODULE_COMPLETION)
        self.assertRegex(
            text, r"⛔ \*\*Omitting the image is not an alternative",
            "the no-omission rule must be a ⛔ gate, not a note — a reader skimming to the "
            "code fence sees markers, not prose",
        )
        self.assertIn("INV-146", text,
                      "the block must name the invariant that makes omission unavailable")

    def test_the_backfill_also_discloses_an_inert_search_state(self):
        """The backfill runs precisely when the capture step's own caption never happened, so
        a slug-only caption there reproduces the defect one step later.

        Asserts the *instruction*, not the noun: an earlier version accepted the phrase
        "inert search box" alone, so deleting "say so in the caption" — the only actionable
        half — left the test green.
        """
        text = flat(GRADUATION)
        self.assertRegex(text, r"(?i)search\s*/\s*probe")
        self.assertRegex(text, r"(?i)empty or inactive search state, say so in the caption",
                         "the backfill must be told to disclose it, not merely told it exists")

    def test_both_sites_still_forbid_implying_an_uncaptured_result_set(self):
        for path in call_sites():
            with self.subTest(site=os.path.basename(path)):
                self.assertRegex(
                    flat(path), r"(?i)(never|not) imply a result set|implies a result set",
                    "the INV-123 requirement itself must survive the edit",
                )


class TabOrderIsSpecifiedAndSourcedFromTheContract(unittest.TestCase):

    def test_the_contract_declares_its_row_order_is_the_embed_order(self):
        self.assertRegex(
            flat(CONTRACT),
            r"row order below is also the order the app presents its tabs",
            "the tab table must state that it is the ordering authority, or the two "
            "call sites have nothing to cite",
        )

    def test_both_call_sites_require_tab_order(self):
        for path in call_sites():
            with self.subTest(file=os.path.basename(path)):
                self.assertRegex(
                    flat(path),
                    r"tab order",
                    "capture-time embedding and graduation's backfill both need the rule "
                    "— the backfill appends by directory scan without it",
                )

    def test_both_call_sites_forbid_append_or_discovery_order(self):
        for path in call_sites():
            with self.subTest(file=os.path.basename(path)):
                self.assertRegex(
                    flat(path),
                    r"never in capture or append order|not in filename-discovery order",
                    "naming the wrong orders explicitly is what makes the rule checkable",
                )

    def test_neither_call_site_restates_the_tab_list(self):
        """Restating it forks the order; both must cite the table instead."""
        for path in call_sites():
            with self.subTest(file=os.path.basename(path)):
                text = flat(path)
                self.assertIn("visualization-api-reference.md", text)
                self.assertNotRegex(
                    text,
                    r"Entity Graph, Merge Statistics, Match Keys, Feature Scores, "
                    r"Cross-Source, Search ?/ ?Probe",
                    "the ordered tab list is restated here; cite the contract table so "
                    "a tab change updates one file",
                )


class TheAnalyticalTabsAreNamedAsWhatWasLost(unittest.TestCase):
    """Without the reason recorded, a future edit re-adds the cap as a tidy-up."""

    def test_module_completion_records_which_tabs_the_cap_dropped(self):
        text = flat(MODULE_COMPLETION)
        for tab in ("Merge Statistics", "Match Keys", "Feature Scores"):
            with self.subTest(tab=tab):
                self.assertIn(tab, text)


if __name__ == "__main__":
    unittest.main()
