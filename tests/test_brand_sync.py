"""Guard against silent drift between brand_tokens.py and the fallback palettes

Enforces **INV-395**, registered by the maintainer 2026-10-20: a shipped script's inlined
fallback copy of a value another module owns stays equal to its source, lives in one named
constant, and is asserted with the source importable. ⚠️ It **cannot** establish that a fallback
is ever reached at runtime, only that the copy equals its source when the source imports.
inlined into the shipped generators that carry a copy of one.

⛔ **(INV-377) No prose states how many carriers exist (INV-246).** Which generators those are is
discovered below rather than written down, and `NoProseStatesHowManyCarriersThereAre`
holds the shipped tree and these guards to the same rule: a number that is right the day
it is written is exactly the thing that goes stale unread (#700).

Enforces **INV-377**, registered by the maintainer 2026-10-19. ⚠️ INV-377 binds **every**
derived set; this file reaches only the brand-palette carriers and the prose about them, so
it **cannot** establish that any other derived set's prose states a property rather than a
size. The maintainer registered the broader wording knowing that, so a later guard over
another derived set discharges more of the invariant rather than widening it. It also
cannot establish that a sentence naming some carriers and not others is complete --
`TheBrandTokensDocstringNamesEveryCarrierOrNone` covers the one place that defect occurred.

This file discharges **INV-184** — "every shipped generator that inlines a fallback copy
of the brand palette" — not only **INV-107**, which enumerates the first two. INV-107 is
the narrower, older statement and remains binding; INV-184 is the one that puts the third
and fourth generators in scope, so a new generator with an inlined palette belongs here
on sight.

Each script keeps a hardcoded copy of the brand palette so it still renders if
brand_tokens.py is unavailable. The runtime prefers the imported values whenever
brand_tokens loads, so a stale fallback is never exercised in practice — and would
drift undetected. Here brand_tokens IS importable, so the live module globals are
the brand_tokens-derived values; asserting they equal the named fallback copies
proves the fallbacks are in sync with the source of truth.

The same shape, and the same sweep, cover the recap video's inlined copies of the recap
PDF's **certificate strings** (#693): a fallback is a fallback whether it carries colors or
words, and that one drifted precisely because the sweep's name pattern could not see it.

Run:  python3 -m unittest discover -s tests
"""
import ast
import glob
import importlib.util
import os
import re
import sys
import types
import unittest

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks, line_of

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "plugins", "senzing-bootcamp", "scripts")
sys.path.insert(0, SCRIPTS)

#: A module-level inlined fallback constant. INV-184 binds "every shipped generator" that
#: inlines the brand palette, so the set is DISCOVERED here rather than listed (INV-246).
#:
#: ⛔ **(INV-395, INV-246)** The word FALLBACK is matched ANYWHERE in the name, not only as a prefix. The earlier
#: `^_?FALLBACK_[A-Z_]+` matched a prefix-named constant only, so `_CERT_TEXT_FALLBACK` in
#: `generate_recap_video.py` was invisible to this sweep while its citation copy drifted from
#: the recap PDF's wording (#693). INV-246 asks for the PATTERN to be widened, never for the
#: missed name to be added: a name added by hand is the author's belief about where the rule
#: applies, which is the belief that was wrong.
FALLBACK_CONSTANT = re.compile(r"^[A-Z0-9_]*FALLBACK[A-Z0-9_]*\s*=", re.M)

#: Carriers known to be covered when this sweep was written. A floor, not the site set:
#: the scan decides what must be covered, this only stops the scan degrading to silence.
KNOWN_CARRIERS = frozenset({
    "brand_tokens", "senzing_viz_server", "generate_recap_pdf", "generate_discoveries_pdf",
    "generate_recap_video",
})


def fallback_carriers():
    """Every shipped script inlining a fallback constant, by module name."""
    found = set()
    for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
        with open(path, encoding="utf-8") as fh:
            if FALLBACK_CONSTANT.search(fh.read()):
                found.add(os.path.splitext(os.path.basename(path))[0])
    return found


#: Whether a module imports `brand_tokens`, which is what makes its inlined fallback a COPY
#: of the palette rather than a default of its own.
IMPORTS_BRAND_TOKENS = re.compile(r"^\s*(?:import brand_tokens\b|from brand_tokens import)", re.M)


def palette_carriers():
    """The discovered carriers whose inlined constants copy the brand palette.

    Narrower than `fallback_carriers()`, which finds every module holding a FALLBACK-named
    constant whether or not the palette is what it carries — and narrower by a margin that
    MOVES: #693 widened the name pattern, `docker_lifecycle` joined the scan, and the two
    sets stopped agreeing. Both are computed here precisely so that nothing anywhere has to
    know which of their sizes is current (#700).
    """
    found = set()
    for name in fallback_carriers():
        if name == "brand_tokens":
            continue  # the source of truth, not a copy of it
        with open(os.path.join(SCRIPTS, name + ".py"), encoding="utf-8") as fh:
            if IMPORTS_BRAND_TOKENS.search(fh.read()):
                found.add(name)
    return found


#: A count attached to a carrier noun — "two generators", "both consumers", "four shipped
#: scripts". The count may be a word or a bare number; `INV-184`, `#693` and `3.8` are not
#: bare numbers, which is what the lookbehind and lookahead are for.
_COUNT_WORD = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|both"
_COUNT = r"(?:\b(?:%s)\b|(?<![\w#.\u00a7-])\d{1,3}(?![\w.]))" % _COUNT_WORD
_ADJECTIVE = r"(?:shipped|bundled|other|further|remaining|known|more|new|additional)"
_CARRIER_NOUN = r"(?:generators?|carriers?|scripts?|modules?|consumers?)"
STATED_COUNT = re.compile(r"%s\s+(?:%s\s+)?%s" % (_COUNT, _ADJECTIVE, _CARRIER_NOUN), re.I)

#: What makes a counted noun a count of THIS set rather than of some other group of scripts.
#: ⛔ **Narrowing measured before it was chosen (#700).** Over every tracked file, a count word
#: or digit within 40 characters of a file-ish noun matches 7515 lines; carrier-shaped nouns
#: alone leave 3641; requiring this subject in the same block leaves 19, of which 15 are in
#: `specs/` or in `invariant-manifest.json` (both regenerated records of history, never edited
#: by a run) and one is the audit skill narrating the original defect. The four that remain are
#: the findings this issue fixed. Bare `fallback` was dropped from this pattern because it also
#: matches a persisted-answers docstring whose own count is of unrelated consumers of a key.
PALETTE_SUBJECT = re.compile(r"palette|brand_tokens|inlined cop(?:y|ies)", re.I)

#: The prose this rule binds: the shipped plugin tree, and the guards that describe it.
#: `specs/` is the frozen archive and the register (INV-307), `invariant-manifest.json` is
#: regenerated from it, and `BLUEPRINT.md` and `CHANGELOG.md` are dated records of what each
#: issue changed — a count in any of those is a fact about a date and stays true. ⚠️ **What
#: this therefore does NOT cover (INV-308):** `.claude/`, where the audit skill's "One
#: generator's comment claimed ..." is correct prose about the original defect and where a
#: stale count would go unreported.
PROSE_SUBTREES = ("plugins/senzing-bootcamp", "tests")
PROSE_SUFFIXES = (".py", ".md", ".json", ".js")


def stated_carrier_counts():
    """Every place the shipped tree or its guards says how many carriers there are.

    Read wrap-aware (INV-346): the sentence that started this wrapped across two lines in one
    file and three in another, so a line-at-a-time read would have found neither.
    """
    found = []
    for path in corpus_files(*PROSE_SUBTREES, suffixes=PROSE_SUFFIXES):
        text = path.read_text(encoding="utf-8", errors="replace")
        for flat, origin in collapsed_blocks(text):
            if not PALETTE_SUBJECT.search(flat):
                continue
            for hit in STATED_COUNT.finditer(flat):
                where = os.path.relpath(str(path), REPO_ROOT).replace(os.sep, "/")
                found.append("%s:%d: %r in %r" % (
                    where, line_of(origin, hit.start()), hit.group(0),
                    flat[max(0, hit.start() - 70):hit.end() + 70]))
    return sorted(found)


def load_viz_with_brand_tokens_unavailable():
    """A fresh `senzing_viz_server` whose brand_tokens import failed.

    ⛔ Without this, an "inline fallback matches the helper" test compares the helper to
    **itself**: brand_tokens imports fine under test, so `viz.color_for_sources` IS
    `brand_tokens.color_for_sources` and the inline copy is never executed. That vacuity
    was demonstrated — a mutation gutting the inline copy's encoding space escaped the
    assertion entirely.

    Blocking the import is done by planting a module whose attribute access raises, so the
    script's own `except Exception` fallback branch runs exactly as it would in the wild.
    """
    blocker = types.ModuleType("brand_tokens")

    def _unavailable(name):
        raise AttributeError("brand_tokens is unavailable in this test")

    blocker.__getattr__ = _unavailable
    saved = sys.modules.get("brand_tokens")
    sys.modules["brand_tokens"] = blocker
    try:
        spec = importlib.util.spec_from_file_location(
            "viz_without_brand_tokens", os.path.join(SCRIPTS, "senzing_viz_server.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if saved is None:
            del sys.modules["brand_tokens"]
        else:
            sys.modules["brand_tokens"] = saved


class TheCarrierSetIsDerived(unittest.TestCase):
    """INV-246: the set of generators this file must cover is scanned, never listed.

    INV-184 exists *because* this exact guard once enumerated its sites. INV-107 named two
    generators; `generate_discoveries_pdf.py` drifted out of scope unnoticed while its own
    comment claimed a test asserted it, and the remedy then was to add the third BY HAND.
    A hardcoded list would repeat that history the day a fourth generator ships, so the
    carrier set is discovered from the corpus and a carrier this file does not exercise is
    a failure rather than a silence.

    ⛔ This sweep proves a carrier is EXERCISED here, not that its assertions are adequate.
    It catches a generator nobody added; only reading catches a generator added weakly.
    """

    def test_the_scan_is_not_vacuous(self):
        found = fallback_carriers()
        self.assertGreaterEqual(
            len(found), len(KNOWN_CARRIERS),
            "the fallback-constant scan found fewer carriers than were known to exist "
            "(%s vs %s) — the constant naming convention changed and this sweep is now "
            "inspecting a set it cannot see" % (sorted(found), sorted(KNOWN_CARRIERS)))

    def test_every_discovered_carrier_is_exercised_by_this_file(self):
        source = open(os.path.abspath(__file__), encoding="utf-8").read()
        uncovered = sorted(m for m in fallback_carriers()
                           if not re.search(r"\b%s\b" % re.escape(m), source))
        self.assertEqual(
            [], uncovered,
            "a shipped script inlines a fallback constant and this file never mentions "
            "it, so its copy can drift from its source of truth undetected — the failure "
            "INV-184 was written from, and the one that hid the recap video's certificate "
            "strings for weeks (#693). Add its assertions here: %s"
            % uncovered)


class BrandTokenSync(unittest.TestCase):
    def test_brand_tokens_importable(self):
        import brand_tokens  # noqa: F401  (fixture: the whole suite assumes this)

    def test_viz_server_fallback_in_sync(self):
        import senzing_viz_server as viz
        self.assertEqual(viz._BRAND, viz._FALLBACK_BRAND)
        self.assertEqual(viz.SOURCE_COLORS, viz._FALLBACK_SOURCE_COLORS)
        self.assertEqual(viz.FALLBACK_COLORS, viz._FALLBACK_COLORS)

    def test_recap_pdf_fallback_in_sync(self):
        import generate_recap_pdf as recap
        for name, rgb in recap._FALLBACK_RGB.items():
            self.assertEqual(getattr(recap, name), rgb,
                             f"{name} fallback diverged from brand_tokens.py")

    def test_source_stroke_fallback_in_sync(self):
        import senzing_viz_server as viz
        self.assertEqual(viz.SOURCE_STROKES, viz._FALLBACK_STROKES)

    def test_the_further_encoding_channels_are_also_in_sync(self):
        """Stroke width and fill shading are channels too, so they drift the same way."""
        import senzing_viz_server as viz
        self.assertEqual(viz.SOURCE_STROKE_WIDTHS, viz._FALLBACK_STROKE_WIDTHS)
        self.assertEqual(viz.SOURCE_FILL_SHADES, viz._FALLBACK_FILL_SHADES)

    def test_discoveries_pdf_fallback_in_sync(self):
        """The third generator with an inlined fallback — previously unguarded.

        INV-107 names `senzing_viz_server.py` and `generate_recap_pdf.py` only, so this
        one's copies could drift silently. They happened to be in sync when the
        2026-07-30 sweep checked them, and the script's own comment already claimed
        "tests/test_brand_sync.py asserts it" — which was not true until now. The literals
        also used to appear twice, once per `except` branch; they are one named dict now.

        **INV-184** is the invariant this test discharges: it generalized INV-107 from those
        two files to the pattern, which is what makes this third generator in scope at all.
        """
        import generate_discoveries_pdf as disc
        for name, rgb in disc._FALLBACK_RGB.items():
            self.assertEqual(
                getattr(disc, name), rgb,
                f"{name} fallback diverged from brand_tokens.py",
            )


    def test_recap_video_fallback_in_sync(self):
        """The recap-video renderer (#299) inlines a fallback too, so INV-184 binds it on sight.

        Its palette is keyed by the video's own names (``EMBER_END`` for brand_tokens'
        ``EMBER_GRAD_END``, and so on), mapped once in ``_TOKEN_NAMES``; the check is that the
        palette it resolved from brand_tokens equals the inlined copy, entry for entry.
        """
        import generate_recap_video as video
        self.assertEqual(set(video._FALLBACK_RGB), set(video._TOKEN_NAMES))
        for name, rgb in video._FALLBACK_RGB.items():
            self.assertEqual(video.PALETTE[name], rgb,
                             f"{name} fallback diverged from brand_tokens.py")


class TheCertificateTextIsOneSourceOfTruth(unittest.TestCase):
    """The recap video's inlined certificate strings must equal the recap PDF's (#693).

    `generate_recap_video.py` draws its Certificate of Completion frame from
    `generate_recap_pdf`'s own constants, "so the two certificates cannot disagree", and
    falls back to inlined copies only when that module cannot be imported. Nothing held the
    copies equal, and one had already drifted: the video printed "for successfully completing
    the Senzing Bootcamp." where the recap PDF prints the full no-modules citation naming
    Senzing's guided path.

    The fallback is kept rather than deleted — it is what renders when `generate_recap_pdf`
    is unimportable, and removing it would turn that case into a blank certificate — so the
    copies are held equal here, the way the palette is held to `brand_tokens.py` above.

    ⛔ **(INV-395, INV-265) This comparison is meaningful only with `generate_recap_pdf` IMPORTABLE.**
    Skipping the import would compare nothing and pass. `generate_recap_pdf` imports its fpdf2
    dependency inside the renderer, not at module scope, so it imports in BOTH suite legs —
    fpdf2 present and absent — and these tests therefore FAIL rather than skip when the module
    they compare against cannot be loaded. Nothing here is conditional on fpdf2.
    """

    def setUp(self):
        import generate_recap_pdf
        import generate_recap_video
        self.pdf = generate_recap_pdf
        self.video = generate_recap_video

    def test_the_comparison_has_two_non_empty_sides(self):
        """The anti-vacuity floor: an emptied constant must not read as agreement."""
        self.assertTrue(self.video._CERT_TEXT_FALLBACK, "the video's label copies are empty")
        self.assertTrue(self.video._CERT_CITATION_FALLBACK, "the citation copy is empty")
        self.assertTrue(self.pdf._CERT_CITATION_NO_MODULES, "the recap PDF's citation is empty")

    def test_every_inlined_label_has_a_named_source(self):
        """A key with no source could never be compared, so it could never be caught."""
        self.assertEqual(set(self.video._CERT_TEXT_SOURCES),
                         set(self.video._CERT_TEXT_FALLBACK),
                         "a fallback label and the recap PDF constant it copies disagree on "
                         "which keys exist, so one of them is unchecked")

    def test_the_inlined_labels_equal_the_recap_pdfs(self):
        for key, attr in sorted(self.video._CERT_TEXT_SOURCES.items()):
            with self.subTest(label=key):
                self.assertEqual(getattr(self.pdf, attr),
                                 self.video._CERT_TEXT_FALLBACK[key],
                                 f"the video's {key!r} fallback diverged from the recap "
                                 f"PDF's {attr}; the recap PDF is the source of truth")

    def test_the_inlined_citation_equals_the_recap_pdfs(self):
        """The copy that had actually drifted, and the one acceptance criterion 2 names."""
        self.assertEqual(self.pdf._CERT_CITATION_NO_MODULES,
                         self.video._CERT_CITATION_FALLBACK,
                         "the video's fallback citation diverged from the recap PDF's "
                         "_CERT_CITATION_NO_MODULES; the recap PDF is the source of truth")

    def test_the_citation_copied_is_the_one_the_recap_pdf_actually_prints(self):
        """Equality with the constant is worth nothing if the renderer prints another one.

        The fallback path has no module list, so `_cert_citation([])` is what the recap PDF
        prints in the same situation — that is the string the video must match.
        """
        self.assertEqual(self.pdf._cert_citation([]), self.video._CERT_CITATION_FALLBACK)


class TheOtherConstantsTheWidenedSweepFinds(unittest.TestCase):
    """What the widened pattern newly discovered, and what holds for each (#693).

    Widening the name pattern brought the recap video's certificate strings
    (`_CERT_TEXT_FALLBACK` and `_CERT_CITATION_FALLBACK`),
    `generate_discoveries_pdf.COVER_TITLE_FALLBACK` and `docker_lifecycle.SLUG_FALLBACK` into
    the sweep. ⚠️ **This sentence used to say how many constants that was, and it said three
    where the scan finds four** — it had dropped `_CERT_CITATION_FALLBACK`, the one copy that
    had actually drifted (#700). Only the certificate strings are COPIES of a value another
    module owns, so only they can drift from a source of truth; the class above holds them.
    The rest are defaults with no twin anywhere — `doc.title or COVER_TITLE_FALLBACK` and
    `slug or SLUG_FALLBACK` — so there is nothing for them to diverge from, and what has to
    hold instead is that the default is itself usable.

    `docker_lifecycle` is a carrier this file would otherwise never mention, so the property
    its fallback must keep is asserted here rather than left to the coverage sweep to demand
    and nobody to supply.
    """

    def test_the_slug_fallback_is_a_legal_container_name_component(self):
        """It is substituted into a derived container name, so it must be inside the charset
        docker and podman enforce: an empty or punctuation-led default would build a name the
        runtime rejects, on the path where the project directory has no usable basename."""
        import docker_lifecycle
        self.assertTrue(docker_lifecycle.SLUG_FALLBACK, "the slug fallback is empty")
        self.assertTrue(
            docker_lifecycle.NAME_CHARSET.match(docker_lifecycle.SLUG_FALLBACK),
            "the slug fallback is outside the container-name charset, so a project whose "
            "basename sanitizes to nothing would build an unusable container name")
        nothing_survives = os.path.join(os.path.dirname(os.path.abspath(__file__)), "!!!")
        self.assertEqual(docker_lifecycle.SLUG_FALLBACK,
                         docker_lifecycle.project_slug(nothing_survives),
                         "the fallback constant is not what project_slug actually falls "
                         "back to, so asserting on it proves nothing")


def module_docstring(path):
    """A script's module docstring, parsed rather than imported (INV-108 keeps this cheap)."""
    with open(path, encoding="utf-8") as fh:
        return ast.get_docstring(ast.parse(fh.read())) or ""


class NoProseStatesHowManyCarriersThereAre(unittest.TestCase):
    """#700: the carrier set is discovered, so no shipped comment may state its size.

    `secret_patterns.py` held `brand_tokens.py` up as the model for an inlined fallback and
    said the palette was inlined into a named number of generators. That number was right when
    it was written and wrong by the time it was read, in the file whose whole point is to be
    the model for the pattern. Its twin docstring in `tests/test_secret_patterns_are_shared.py`
    carried the same sentence; this guard's own docstring carried a later number for the same
    set; and `brand_tokens.py` named a pair of importers where the scan now finds more.

    ⚠️ **The issue reporting this demonstrated its own thesis.** It was filed naming one number
    and built on a day the discovery returned another, because #693 widened the name pattern in
    between — an argument for stating the property rather than the count, carrying a count that
    went stale between its filing and its build. So nothing is written down here: the carriers
    are scanned out of the corpus, the claims are scanned out of the prose (INV-246).

    ⛔ This proves no count is stated. It cannot prove that a sentence naming some carriers and
    not others is complete — `TheBrandTokensDocstringNamesEveryCarrierOrNone` covers the one
    place that defect actually occurred.
    """

    def test_no_shipped_prose_states_a_carrier_count(self):
        self.assertEqual(
            [], stated_carrier_counts(),
            "a comment says how many generators carry the palette, where this file discovers "
            "them instead. The sentence goes stale the day a carrier is added or the sweep is "
            "widened, and it reached the shipped tree twice that way (#700). State the "
            "property — every generator that carries a fallback copy, discovered here — "
            "rather than a number.")

    def test_the_scan_reports_a_count_when_one_is_there(self):
        """The anti-vacuity floor: a predicate that matches nothing passes in silence.

        ⛔ The control sentence is ASSEMBLED rather than spelled out, so this file does not
        carry the very shape it reports. Scanning this file out instead would leave the
        docstrings above unchecked, and an exemption is where the next stale count would hide.
        """
        planted = " ".join(("whose", "palette", "is", "inlined", "into", "four", "generators"))
        self.assertTrue(STATED_COUNT.search(planted),
                        "the count pattern no longer sees a stated count")
        self.assertTrue(PALETTE_SUBJECT.search(planted),
                        "the subject pattern no longer sees what the count is about")
        property_wording = " ".join(("whose", "palette", "is", "inlined", "into", "every",
                                     "generator", "that", "carries", "a", "copy"))
        self.assertIsNone(STATED_COUNT.search(property_wording),
                          "the wording this rule asks for would itself be reported")

    def test_the_table_classification_pair_is_not_reported(self):
        """`generate_recap_pdf.py`'s INV-142 comment is about a different and correct pair.

        It says the recap writer and the discoveries writer classify a table identically, which
        is true and has nothing to do with the brand colors. The count pattern DOES fire on it;
        the subject test is what keeps it out. Asserting both is what shows the narrowing is
        doing the work, rather than the pattern happening to miss.
        """
        with open(os.path.join(SCRIPTS, "generate_recap_pdf.py"), encoding="utf-8") as fh:
            source = fh.read()
        matched = [flat for flat, _ in collapsed_blocks(source)
                   if "classify a table identically" in flat]
        self.assertEqual(1, len(matched),
                         "the INV-142 comment this control reads has moved or changed")
        self.assertTrue(STATED_COUNT.search(matched[0]),
                        "the control is vacuous: the count pattern does not fire here at all, "
                        "so excluding it proves nothing about the narrowing")
        self.assertIsNone(PALETTE_SUBJECT.search(matched[0]),
                          "the subject pattern now matches a comment about table layout, so it "
                          "is too wide and will report correct prose")
        self.assertEqual([], [h for h in stated_carrier_counts()
                              if "generate_recap_pdf.py" in h])

    def test_the_corpus_reaches_the_files_this_rule_is_about(self):
        """A corpus that missed them would report clean for the wrong reason.

        A floor, not the site set: the scan decides what is reported, and these are the files
        the defect was found in, so a corpus that stops reaching them is a regression.
        """
        scanned = {os.path.relpath(str(path), REPO_ROOT).replace(os.sep, "/")
                   for path in corpus_files(*PROSE_SUBTREES, suffixes=PROSE_SUFFIXES)}
        here = os.path.relpath(os.path.abspath(__file__), REPO_ROOT).replace(os.sep, "/")
        for name in ("plugins/senzing-bootcamp/scripts/secret_patterns.py",
                     "plugins/senzing-bootcamp/scripts/brand_tokens.py",
                     "tests/test_secret_patterns_are_shared.py", here):
            self.assertIn(name, scanned, "%s is outside the scanned corpus" % name)

    def test_the_derived_sets_are_not_assumed_to_agree(self):
        """The narrower set is genuinely narrower, and neither is empty.

        Nothing here asserts a size. What it asserts is that the sweep's set and the
        palette-copying set are distinct, because the moment they coincide a reader is tempted
        to write a single number down for the pair — the sentence this class deletes.
        """
        wide, narrow = fallback_carriers(), palette_carriers()
        self.assertTrue(narrow, "no shipped module both imports brand_tokens and inlines a "
                                "fallback constant, so the palette-copy set is empty")
        self.assertLess(narrow, wide,
                        "the sweep's set and the palette-copying set are no longer distinct "
                        "(%s vs %s)" % (sorted(narrow), sorted(wide)))


class TheBrandTokensDocstringNamesEveryCarrierOrNone(unittest.TestCase):
    """`brand_tokens.py` must not name some of the modules that copy its palette and not others.

    Its docstring named the visualization server and the recap PDF, written when those were all
    there was, and the discoveries PDF and the recap video arrived without reaching it. A count
    guard alone would never have seen it: the sentence named them, it did not number them. So
    the rule here is all or nothing, and "all" is derived.
    """

    def test_it_names_every_palette_carrier_or_none_of_them(self):
        doc = module_docstring(os.path.join(SCRIPTS, "brand_tokens.py"))
        carriers = palette_carriers()
        named = {name for name in carriers
                 if re.search(r"\b%s\b" % re.escape(name), doc)}
        self.assertTrue(
            not named or named == carriers,
            "brand_tokens.py's docstring names %s and leaves out %s, so a reader is told which "
            "generators copy the palette by a list that is already short. Name every one the "
            "scan finds, or state the property and name none." % (sorted(named),
                                                                  sorted(carriers - named)))

    def test_the_check_would_see_a_short_list(self):
        """The anti-vacuity floor: an empty carrier set would make the check unfailable."""
        carriers = palette_carriers()
        self.assertGreater(len(carriers), 1,
                           "fewer than a pair of palette carriers exist, so 'names some and "
                           "not others' has no referent and this guard cannot fail")


class SourceColorsComeFromTheData(unittest.TestCase):
    """`SOURCE_COLORS` names the Truth Set's sources, and no bootcamper uses those names
    for their own data — so a name-keyed lookup dropped every real source to one identical
    fallback color, in the module where cross-source structure is the point. Colors must be
    assigned from the sources actually present."""

    def setUp(self):
        import brand_tokens
        self.bt = brand_tokens
        self.assign = brand_tokens.color_for_sources

    def fills(self, sources):
        m = self.assign(sources)
        return [m[s]["fill"] for s in sorted(sources)]

    def test_the_reported_case_gets_distinct_colors(self):
        sources = ["PPP_LOANS", "EQUIFAX", "NOMINO-RISK"]
        fills = self.fills(sources)
        self.assertEqual(len(sources), len(set(fills)), f"sources collapsed to {set(fills)}")

    def test_truth_set_keeps_its_preferred_assignment(self):
        """The Truth Set visualization must not regress."""
        m = self.assign(["CUSTOMERS", "REFERENCE", "WATCHLIST"])
        for code, expected in self.bt.SOURCE_COLORS.items():
            with self.subTest(code=code):
                self.assertEqual(expected, m[code]["fill"])

    def test_mixed_model_never_reuses_a_preferred_color(self):
        m = self.assign(["CUSTOMERS", "PPP_LOANS", "EQUIFAX"])
        fills = [v["fill"] for v in m.values()]
        self.assertEqual(3, len(set(fills)))
        self.assertEqual(self.bt.SOURCE_COLORS["CUSTOMERS"], m["CUSTOMERS"]["fill"])

    def test_assignment_is_deterministic(self):
        """A rebuilt snapshot must match the screenshot the recap already describes."""
        self.assertEqual(self.assign(["C", "A", "B"]), self.assign(["B", "C", "A"]))

    @staticmethod
    def rendered(entry):
        """The key the browser actually draws.

        A stroke appears only when a stroke width is set, so `stroke` alone overstates the
        space: a source with no stroke still carries a stroke *color* in the returned dict.
        This mirrors the served JS exactly — `srcStrokeW(src) ? srcStroke(src) : null` for
        the color, `srcStrokeW(src) || null` for the width — which is the whole point:
        asserting on the returned tuple instead is what certified 6×3 combinations while
        the canvas had 6×4.
        """
        return (entry["fill"],
                entry["stroke"] if entry["stroke_width"] else None,
                entry["stroke_width"])

    def test_more_sources_than_colors_stay_distinguishable(self):
        """The reported case: one wrap past the palette. Kept, and still correct."""
        sources = [f"SRC{i}" for i in range(len(self.bt.FALLBACK_COLORS) + 3)]
        m = self.assign(sources)
        keys = {self.rendered(v) for v in m.values()}
        self.assertEqual(len(sources), len(keys),
                         "a second channel must distinguish the repeat")

    def test_every_size_up_to_capacity_stays_distinct_as_rendered(self):
        """The assertion the old guard should have been.

        It stopped at `len(FALLBACK_COLORS) + 3` = 9, which never approaches the encoding
        space, and it compared `(fill, stroke)`, which at n=9 agrees with the rendered key
        only by accident — no source has reached the wrap where a no-stroke entry and a
        stroked entry share a stroke color. Both under-scopings hid the same defect: the
        25th source rendered identically to the 7th.
        """
        capacity = self.bt.SOURCE_ENCODING_CAPACITY
        self.assertGreaterEqual(capacity, 64,
                                "capacity must be tested past 64; a smaller ceiling needs "
                                "to be stated in INV-127 rather than merely reached")
        for n in (2, 6, 7, 24, 25, 42, 64, capacity):
            with self.subTest(sources=n):
                m = self.assign([f"SRC_{i:04d}" for i in range(n)])
                keys = {self.rendered(v) for v in m.values()}
                if len(keys) != n:
                    seen, collided = {}, []
                    for code, v in sorted(m.items()):
                        key = self.rendered(v)
                        if key in seen:
                            collided.append(f"{seen[key]} == {code} as {key}")
                        seen[key] = code
                    self.fail(f"n={n}: {n - len(keys)} collision(s) as RENDERED — "
                              + "; ".join(collided[:4]))

    def test_the_first_size_past_capacity_warns_rather_than_colliding_silently(self):
        """An acknowledged ceiling is defensible; an invisible one is not."""
        over = self.bt.SOURCE_ENCODING_CAPACITY + 1
        with self.assertWarns(UserWarning) as caught:
            self.assign([f"SRC_{i:04d}" for i in range(over)])
        self.assertIn(str(self.bt.SOURCE_ENCODING_CAPACITY), str(caught.warning))

    def test_capacity_at_or_below_does_not_warn(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assign([f"SRC_{i:04d}"
                         for i in range(self.bt.SOURCE_ENCODING_CAPACITY)])

    def test_the_rendered_appearance_is_unchanged_where_it_was_already_correct(self):
        """Up to 24 sources the old encoding was right, so nothing may move there.

        Re-derives the pre-fix rendering — stroke drawn only when the wrap counter is
        non-zero, color `SOURCE_STROKES[cycle % 3]`, width always 1.5 — and requires the
        new code to agree with it exactly. Without this, widening the space is free to
        recolor every existing bootcamp's graph.
        """
        strokes = self.bt.SOURCE_STROKES
        for n in (2, 3, 6, 7, 12, 18, 24):
            with self.subTest(sources=n):
                codes = [f"SRC_{i:04d}" for i in range(n)]
                m = self.assign(codes)
                for i, code in enumerate(sorted(codes)):
                    cycle = i // len(self.bt.FALLBACK_COLORS)
                    expected = (self.bt.FALLBACK_COLORS[i % len(self.bt.FALLBACK_COLORS)],
                                strokes[cycle % len(strokes)] if cycle else None,
                                1.5 if cycle else None)
                    self.assertEqual(expected, self.rendered(m[code]),
                                     f"n={n} {code} changed appearance")

    def test_stroke_width_is_the_property_a_renderer_keys_on(self):
        """`cycle` must not be what decides visibility — that was the defect."""
        m = self.assign([f"SRC_{i:04d}" for i in range(50)])
        by_cycle = {}
        for v in m.values():
            by_cycle.setdefault(v["cycle"], set()).add(v["stroke_width"])
        self.assertIn(None, by_cycle[0], "cycle 0 must draw no stroke")
        widths = {w for widths in by_cycle.values() for w in widths if w}
        self.assertGreater(len(widths), 1,
                           "stroke width never varies, so it is not a channel")

    def test_signal_green_is_never_a_source_color(self):
        m = self.assign([f"S{i}" for i in range(30)])
        self.assertNotIn(self.bt.SIGNAL_GREEN, {v["fill"] for v in m.values()})

    def test_empty_and_blank_inputs_are_safe(self):
        self.assertEqual({}, self.assign([]))
        self.assertEqual({}, self.assign(None))
        self.assertEqual({}, self.assign(["", "  "]))

    def test_viz_server_inline_fallback_matches_the_token_helper(self):
        """The import-failure path must behave identically, not merely exist.

        Loaded with brand_tokens blocked, so this really runs the inline copy — see
        `load_viz_with_brand_tokens_unavailable`.
        """
        viz = load_viz_with_brand_tokens_unavailable()
        self.assertIsNot(viz.color_for_sources, self.assign,
                         "the inline copy was not reached; this compares the helper to "
                         "itself and proves nothing")
        sources = ["CUSTOMERS", "PPP_LOANS", "EQUIFAX", "NOMINO-RISK"]
        self.assertEqual(self.assign(sources), viz.color_for_sources(sources))

    def test_the_inline_fallback_matches_past_the_palette_too(self):
        """A four-source comparison agrees on both sides of the defect this fixed.

        The inline copy is only reached when brand_tokens fails to import, so a version
        that silently kept the 24-source ceiling would never be exercised in a test that
        never passes 24 sources.
        """
        viz = load_viz_with_brand_tokens_unavailable()
        for n in (7, 25, 60, self.bt.SOURCE_ENCODING_CAPACITY):
            with self.subTest(sources=n):
                sources = [f"SRC_{i:04d}" for i in range(n)]
                self.assertEqual(self.assign(sources), viz.color_for_sources(sources))


class VizServerUsesTheAssignedColors(unittest.TestCase):
    def setUp(self):
        import senzing_viz_server as viz
        self.viz = viz

    def test_rendered_page_carries_a_per_source_map(self):
        import re
        page = self.viz.render_page("T", sources=["PPP_LOANS", "EQUIFAX", "NOMINO-RISK"])
        payload = re.search(r"const SRC_COLORS=(\{.*?\});", page).group(1)
        for code in ("PPP_LOANS", "EQUIFAX", "NOMINO-RISK"):
            with self.subTest(code=code):
                self.assertIn(code, payload)
        self.assertIn('"fill"', payload)
        self.assertIn('"stroke"', payload)

    def test_no_hardcoded_single_fallback_remains(self):
        """`SRC_COLORS[src]||"#8b5cf6"` is what made every source one color."""
        page = self.viz.render_page("T", sources=["A", "B"])
        self.assertNotIn('SRC_COLORS[src]||"#8b5cf6"', page)

    def test_unassigned_source_is_visually_distinct_from_assigned_ones(self):
        """"Unassigned" must not masquerade as a real category."""
        page = self.viz.render_page("T", sources=["A", "B", "C"])
        self.assertIn("UNKNOWN_SRC", page)
        self.assertNotIn(f'UNKNOWN_SRC="{self.viz.FALLBACK_COLORS[0]}"', page)

    def test_fallback_colors_are_actually_consumed(self):
        """The palette existed but was dead code; the defect was that nothing used it."""
        page = self.viz.render_page("T", sources=["ONE", "TWO"])
        self.assertIn(self.viz.FALLBACK_COLORS[0], page)

    def test_the_page_carries_the_stroke_width_channel(self):
        """A widened assignment the renderer ignores changes nothing on screen."""
        page = self.viz.render_page("T", sources=[f"SRC_{i:04d}" for i in range(30)])
        self.assertIn('"stroke_width"', page,
                      "the per-source map does not carry the width channel")
        self.assertIn("function srcStrokeW(", page,
                      "nothing in the page can read the width channel")

    def test_no_draw_site_keys_on_the_wrap_counter(self):
        """`cycle` does not reach the canvas; keying on it is what capped the space at 24."""
        page = self.viz.render_page("T", sources=["A", "B"])
        self.assertNotIn("srcCycle", page,
                         "a draw site still decides stroke visibility from the wrap "
                         "counter, so widths and shades never render")

    def test_the_legend_and_the_node_use_the_same_expression(self):
        """Criterion: swatch and mark must agree for the same key above 24 sources.

        ⚠️ The node's expression changed on 2026-08-17 from `d.data_sources[0]` to
        `srcKeyOf(d)` — a node is colored by its whole source COMBINATION, not by whichever
        of its sources sorts first. The criterion is unchanged: both sides still resolve
        through `srcStyle`, so a swatch and the marks it describes cannot disagree. For a
        single-source entity `srcKeyOf(d)` degenerates to that source code, which is why
        the single-source legend rows still key on `s`.
        """
        page = self.viz.render_page("T", sources=["A", "B"])
        node = 'var k=srcKeyOf(d);return srcStrokeW(k)?srcStroke(k):null;'
        legend = 'srcStrokeW(s)?("inset 0 0 0 "+srcStrokeW(s)+"px "+srcStroke(s)):null'
        self.assertIn(node, page, "the node stroke is not derived from the width channel")
        self.assertIn(legend, page,
                      "the legend swatch does not mirror the node's stroke and width, so "
                      "the two can describe different appearances for one key")

    def test_model_reports_its_data_sources_sorted(self):
        model = self.viz.Model()
        model.entities = {
            1: {"data_sources": ["WATCHLIST", "CUSTOMERS"]},
            2: {"data_sources": ["CUSTOMERS", ""]},
        }
        self.assertEqual(["CUSTOMERS", "WATCHLIST"], model.data_sources())


if __name__ == "__main__":
    unittest.main()
