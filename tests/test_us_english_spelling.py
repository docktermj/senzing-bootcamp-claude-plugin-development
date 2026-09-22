"""US English is the only spelling written in this repository.

Enforces **INV-253**: every English word here uses its US form — shipped plugin prose,
specs, invariants, tests, code comments and identifiers alike.

⛔ **Three limitations, stated because a clean run does not mean what it looks like.**

1. **The vocabulary is a hardcoded list, and it is the one thing here that cannot be
   derived.** INV-246 requires a multi-site guard to find its *sites* by scanning, and this
   one does — it walks the whole tree. It cannot scan for its *words*: the corpus is the
   thing being judged, so there is no corpus-derived way to enumerate the British forms it
   should not contain. A clean run therefore means **no listed British form is present**,
   never that the corpus is US English. A word nobody thought of is invisible here.

2. **`analyses` is deliberately absent, and that is a real under-detection.** It is both the
   British verb (`analyses` = US `analyzes`) and the correct US plural of `analysis`. No
   matcher can tell those apart without reading the sentence, so flagging it would fail on
   correct US prose. All 7 occurrences in the tree at migration time were verbs and were
   converted by hand. This guard would not catch them coming back.

3. **Stem matching is rejected, and must stay rejected.** `organism`, `mechanism`,
   `parallelism`, `characteristic`, `equally`, `totally`, `radialLine` and
   `LabelLayoutAssertions` all contain British-looking stems and are all correct. Matching
   is on whole words only, after splitting identifiers — never on fragments.

**How a word is found.** Text is split into letter runs, each run is split again on
CamelCase boundaries, and each piece is lowercased and looked up. That is what makes all
three shapes reachable by one pass: plain prose (`behavior`), `snake_case`
(`test_the_..._limit`, since `_` is not a letter) and `CamelCase` (`NoStepBehaviorChanged`,
which a word-boundary regex cannot see). The migration found five CamelCase names only on a
second pass, so a guard built the obvious way would have shipped blind to all five.

**Exemptions are narrower than a file wherever they can be.** A file that must carry a
British form names the exact word *and how many times*, so every other British form in that
file still fails, and a waiver whose word has since gone fails as stale rather than
lingering. Two paths are exempt whole — a vendored third-party bundle and the
bootcamper-feedback archive, which is testimony this repo quotes rather than prose it
writes — and each is asserted to still contain something, for the same reason.

⛔ **None of this is reusable as a general silencer.** There is no marker a future edit can
add to a line to make it pass; every exemption is a path plus an exact word count recorded
here, in the data block below, where it shows up in a diff.

Source spec: `specs/us-english-spelling-is-unregistered-and-unguarded.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- BEGIN VOCABULARY AND EXEMPTION DATA -------------------------------------------- #
# Everything between these two sentinels is excised before this file is scanned. It is
# nothing but British spellings and the literals of the exemptions, so scanning it would
# report the guard's own data as a defect. The sentinels are honored for THIS file alone
# (see `_excised`), never as a general mechanism -- `test_the_sentinels_are_not_a_general
# _silencer` proves another file cannot use them.

BRITISH_TO_US = {
    # -our -> -or
    "behaviour": "behavior", "behaviours": "behaviors", "behavioural": "behavioral",
    "behaviourally": "behaviorally", "colour": "color", "colours": "colors",
    "coloured": "colored", "colouring": "coloring", "colourful": "colorful",
    "favour": "favor", "favours": "favors", "favoured": "favored", "favouring": "favoring",
    "favourite": "favorite", "favourites": "favorites", "favourable": "favorable",
    "favourably": "favorably", "unfavourable": "unfavorable", "honour": "honor",
    "honours": "honors", "honoured": "honored", "honouring": "honoring",
    "honourable": "honorable", "labour": "labor", "labours": "labors",
    "laboured": "labored", "labouring": "laboring", "neighbour": "neighbor",
    "neighbours": "neighbors", "neighbouring": "neighboring",
    "neighbourhood": "neighborhood", "odour": "odor", "rumour": "rumor",
    "rumours": "rumors", "savour": "savor", "splendour": "splendor", "valour": "valor",
    "vapour": "vapor", "vigour": "vigor", "harbour": "harbor", "parlour": "parlor",
    "saviour": "savior", "armour": "armor", "armoured": "armored",
    "endeavour": "endeavor", "endeavours": "endeavors", "flavour": "flavor",
    "flavours": "flavors", "flavoured": "flavored", "humour": "humor", "rigour": "rigor",
    "rigours": "rigors", "clamour": "clamor", "tumour": "tumor", "demeanour": "demeanor",
    "candour": "candor", "fervour": "fervor",
    # -re -> -er
    "centre": "center", "centres": "centers", "centred": "centered",
    "centring": "centering", "fibre": "fiber", "fibres": "fibers", "litre": "liter",
    "litres": "liters", "metre": "meter", "metres": "meters",
    "millimetre": "millimeter", "millimetres": "millimeters",
    "centimetre": "centimeter", "centimetres": "centimeters",
    "kilometre": "kilometer", "kilometres": "kilometers", "theatre": "theater",
    "theatres": "theaters", "calibre": "caliber", "sombre": "somber",
    "spectre": "specter", "lustre": "luster", "meagre": "meager", "sabre": "saber",
    "sceptre": "scepter", "manoeuvre": "maneuver", "manoeuvres": "maneuvers",
    "manoeuvred": "maneuvered", "ochre": "ocher", "titre": "titer",
    # -yse -> -yze  (NOTE: `analyses` is deliberately absent -- see limitation 2)
    "analyse": "analyze", "analysed": "analyzed", "analysing": "analyzing",
    "analyser": "analyzer", "analysers": "analyzers", "paralyse": "paralyze",
    "paralysed": "paralyzed", "catalyse": "catalyze", "catalysed": "catalyzed",
    # -ise -> -ize  (only verbs where the US form is genuinely -ize; `advertise`,
    # `exercise`, `supervise`, `comprise`, `promise` and friends are correct in both
    # and are deliberately not listed)
    "authorise": "authorize", "authorised": "authorized", "authorises": "authorizes",
    "authorising": "authorizing", "authorisation": "authorization",
    "authorisations": "authorizations", "unauthorised": "unauthorized",
    "apologise": "apologize", "apologised": "apologized", "capitalise": "capitalize",
    "capitalised": "capitalized", "capitalising": "capitalizing",
    "capitalisation": "capitalization", "categorise": "categorize",
    "categorised": "categorized", "categorising": "categorizing",
    "categorisation": "categorization", "centralise": "centralize",
    "centralised": "centralized", "characterise": "characterize",
    "characterised": "characterized", "characterising": "characterizing",
    "characterisation": "characterization", "customise": "customize",
    "customised": "customized", "customising": "customizing",
    "customisation": "customization", "customisations": "customizations",
    "digitise": "digitize", "digitised": "digitized", "emphasise": "emphasize",
    "emphasised": "emphasized", "emphasising": "emphasizing", "equalise": "equalize",
    "equalised": "equalized", "familiarise": "familiarize",
    "familiarised": "familiarized", "finalise": "finalize", "finalised": "finalized",
    "finalising": "finalizing", "formalise": "formalize", "formalised": "formalized",
    "generalise": "generalize", "generalised": "generalized",
    "generalising": "generalizing", "generalisation": "generalization",
    "generalisations": "generalizations", "harmonise": "harmonize",
    "harmonised": "harmonized", "idealise": "idealize", "initialise": "initialize",
    "initialised": "initialized", "initialising": "initializing",
    "initialisation": "initialization", "initialisations": "initializations",
    "uninitialised": "uninitialized", "itemise": "itemize", "itemised": "itemized",
    "legalise": "legalize", "localise": "localize", "localised": "localized",
    "localising": "localizing", "localisation": "localization", "maximise": "maximize",
    "maximised": "maximized", "maximising": "maximizing", "memorise": "memorize",
    "memorised": "memorized", "minimise": "minimize", "minimised": "minimized",
    "minimising": "minimizing", "mobilise": "mobilize", "mobilised": "mobilized",
    "modernise": "modernize", "modernised": "modernized", "neutralise": "neutralize",
    "neutralised": "neutralized", "normalise": "normalize", "normalised": "normalized",
    "normalises": "normalizes", "normalising": "normalizing",
    "normalisation": "normalization", "normalisations": "normalizations",
    "denormalise": "denormalize", "denormalised": "denormalized",
    "optimise": "optimize", "optimised": "optimized", "optimises": "optimizes",
    "optimising": "optimizing", "optimisation": "optimization",
    "optimisations": "optimizations", "organise": "organize", "organised": "organized",
    "organises": "organizes", "organising": "organizing",
    "organisation": "organization", "organisations": "organizations",
    "organisational": "organizational", "reorganise": "reorganize",
    "reorganised": "reorganized", "personalise": "personalize",
    "personalised": "personalized", "prioritise": "prioritize",
    "prioritised": "prioritized", "prioritising": "prioritizing",
    "prioritisation": "prioritization", "publicise": "publicize",
    "publicised": "publicized", "randomise": "randomize", "randomised": "randomized",
    "randomising": "randomizing", "rationalise": "rationalize",
    "rationalised": "rationalized", "rationalising": "rationalizing",
    "rationalisation": "rationalization", "realise": "realize", "realised": "realized",
    "realises": "realizes", "realising": "realizing", "recognise": "recognize",
    "recognised": "recognized", "recognises": "recognizes",
    "recognising": "recognizing", "recognisable": "recognizable",
    "unrecognised": "unrecognized", "unrecognisable": "unrecognizable",
    "sanitise": "sanitize", "sanitised": "sanitized", "sanitises": "sanitizes",
    "sanitising": "sanitizing", "sanitisation": "sanitization",
    "serialise": "serialize", "serialised": "serialized", "serialising": "serializing",
    "serialisation": "serialization", "deserialise": "deserialize",
    "deserialised": "deserialized", "deserialising": "deserializing",
    "specialise": "specialize", "specialised": "specialized",
    "specialising": "specializing", "specialisation": "specialization",
    "stabilise": "stabilize", "stabilised": "stabilized", "standardise": "standardize",
    "standardised": "standardized", "standardising": "standardizing",
    "standardisation": "standardization", "summarise": "summarize",
    "summarised": "summarized", "summarises": "summarizes",
    "summarising": "summarizing", "symbolise": "symbolize",
    "synchronise": "synchronize", "synchronised": "synchronized",
    "synchronising": "synchronizing", "synchronisation": "synchronization",
    "synthesise": "synthesize", "synthesised": "synthesized",
    "synthesising": "synthesizing", "utilise": "utilize", "utilised": "utilized",
    "utilising": "utilizing", "utilisation": "utilization", "visualise": "visualize",
    "visualised": "visualized", "visualises": "visualizes",
    "visualising": "visualizing", "visualisation": "visualization",
    "visualisations": "visualizations", "vocalise": "vocalize", "tokenise": "tokenize",
    "tokenised": "tokenized", "tokenising": "tokenizing",
    "parameterise": "parameterize", "parameterised": "parameterized",
    "parametrise": "parametrize", "virtualise": "virtualize",
    "virtualised": "virtualized", "containerise": "containerize",
    "containerised": "containerized", "modularise": "modularize",
    "modularised": "modularized", "sterilise": "sterilize", "civilise": "civilize",
    "colonise": "colonize", "criticise": "criticize", "criticised": "criticized",
    "criticising": "criticizing",
    # doubled -l- before a suffix
    "labelled": "labeled", "labelling": "labeling", "labeller": "labeler",
    "modelled": "modeled", "modelling": "modeling", "modeller": "modeler",
    "travelled": "traveled", "travelling": "traveling", "traveller": "traveler",
    "travellers": "travelers", "cancelled": "canceled", "cancelling": "canceling",
    "signalled": "signaled", "signalling": "signaling", "totalled": "totaled",
    "totalling": "totaling", "levelled": "leveled", "levelling": "leveling",
    "fuelled": "fueled", "fuelling": "fueling", "marvelled": "marveled",
    "counselled": "counseled", "counselling": "counseling", "counsellor": "counselor",
    "counsellors": "counselors", "equalled": "equaled", "equalling": "equaling",
    "channelled": "channeled", "channelling": "channeling", "funnelled": "funneled",
    "dialled": "dialed", "dialling": "dialing",
    # single -l where US doubles it
    "fulfil": "fulfill", "fulfils": "fulfills", "fulfilment": "fulfillment",
    "fulfilments": "fulfillments", "enrol": "enroll", "enrols": "enrolls",
    "enrolment": "enrollment", "instalment": "installment",
    "instalments": "installments", "skilful": "skillful", "skilfully": "skillfully",
    "wilful": "willful", "wilfully": "willfully", "appal": "appall",
    "appals": "appalls", "instil": "instill", "instils": "instills",
    "enthral": "enthrall",
    # -ce nouns and the British -ise/-ce verb split
    "defence": "defense", "defences": "defenses", "offence": "offense",
    "offences": "offenses", "pretence": "pretense", "licence": "license",
    "licences": "licenses", "licenced": "licensed", "licencing": "licensing",
    "practise": "practice", "practised": "practiced", "practises": "practices",
    "practising": "practicing",
    # -ogue -> -og  (`dialogue`, `monologue`, `epilogue` are standard US and are not listed)
    "catalogue": "catalog", "catalogues": "catalogs", "catalogued": "cataloged",
    "cataloguing": "cataloging", "analogue": "analog", "analogues": "analogs",
    # everything else
    "grey": "gray", "greys": "grays", "greyed": "grayed", "greying": "graying",
    "greyscale": "grayscale", "programme": "program", "programmes": "programs",
    "sceptic": "skeptic", "sceptics": "skeptics", "sceptical": "skeptical",
    "sceptically": "skeptically", "scepticism": "skepticism",
    "aluminium": "aluminum", "sulphur": "sulfur", "sulphate": "sulfate",
    "cheque": "check", "cheques": "checks", "storey": "story", "storeys": "stories",
    "tyre": "tire", "tyres": "tires", "kerb": "curb", "gaol": "jail", "plough": "plow",
    "draught": "draft", "draughts": "drafts", "mould": "mold", "moulded": "molded",
    "moulding": "molding", "moulds": "molds", "smoulder": "smolder",
    "smouldering": "smoldering", "ageing": "aging", "jewellery": "jewelry",
    "moustache": "mustache", "pyjamas": "pajamas", "aeroplane": "airplane",
    "artefact": "artifact", "artefacts": "artifacts", "artefactual": "artifactual",
    "judgement": "judgment", "judgements": "judgments", "learnt": "learned",
    "spoilt": "spoiled", "dreamt": "dreamed",
}

#: Paths exempt in full, with the reason each one earns it. Both are asserted below to
#: still contain a British form -- an exemption matching nothing is stale, and stale is
#: how an exemption outlives the thing it was written for.
WHOLE_PATH_EXEMPT = {
    "plugins/senzing-bootcamp/scripts/vendor/d3.v7.min.js":
        "Vendored third-party bundle. Its `grey`/`greys` are CSS color-name keys, not "
        "prose, and editing a vendored file to satisfy a house style corrupts it.",
    "feedback/":
        "The bootcamper-feedback archive: testimony this repo QUOTES, not prose it "
        "writes. Rewriting a bootcamper's words falsifies the record, and the text is "
        "also the content-addressed dedup key `PROCESSED.jsonl` records -- so a "
        "correction here would silently break the ledger correspondence too.",
}

#: Files that must carry a specific British form to do their job, named word by word with
#: an EXACT count. Narrower than exempting the file: every other British form in these
#: files still fails, a count that moves fails, and a waiver whose word has gone fails as
#: stale. There is no marker a future edit can add to a line to be waived -- a waiver is a
#: path and a number, recorded here, visible in a diff.
PER_FILE_WAIVERS = {
    "docs/development.md": (
        {"licence": 2, "analysed": 1, "judgement": 1, "artefact": 1, "labelled": 1,
         "behaviour": 1, "catalogue": 1, "millimetre": 1, "centre": 1, "normalise": 1,
         "colour": 1, "organisation": 1, "defence": 1, "recognise": 1, "favour": 1,
         "sanitise": 1, "honoured": 1, "summarise": 1, "grey": 1, "programme": 1},
        "The human-facing statement of INV-253. Its reference table's `British (avoid)` "
        "column is nothing but the forms it tells an author not to write.",
    ),
    "specs/us-english-spelling-is-unregistered-and-unguarded.md": (
        {"behaviour": 6, "licence": 5, "judgement": 1, "labelled": 1, "honoured": 1,
         "unrecognised": 3, "authorises": 1, "normalise": 1, "analysed": 1, "grey": 2,
         "programme": 2},
        "The source spec. It quotes the migration's own findings -- the words counted, "
        "and the test assertions the 2026-08-16 retrofit desynced -- as evidence. Its "
        "`## Deviations` section quotes two more (the German fixture, and a feedback "
        "title a sibling spec cites) while recording where the exemptions came from.",
    ),
    "specs/INVARIANTS.md": (
        {"licence": 1},
        "INV-253's own statement names the British form it forbids, so the rule can be "
        "read without a second lookup.",
    ),
    "invariant-manifest.json": (
        {"licence": 1},
        "Derived verbatim from specs/INVARIANTS.md (#88), so it inherits INV-253's own "
        "statement of the British form that rule forbids. ⛔ The waiver is here rather than "
        "the generator normalizing the text: a manifest that silently corrected the prose "
        "would no longer be the prose, and a downstream port checking its register against "
        "INVARIANTS.md would find a discrepancy with no way to tell which copy moved.",
    ),
    "specs/license-cap-branch-offers-no-way-to-apply-the-license-that-may-have-arrived.md": (
        {"licence": 2},
        "Quotes a bootcamper's feedback title verbatim in its `Source:` line. That exact "
        "string is what `feedback/PROCESSED.jsonl` records as the dedup key, so "
        "correcting it would both misquote the source and break the correspondence.",
    ),
    "specs/the-source-set-coloring-rule-is-stated-three-times-and-verified-nowhere.md": (
        {"colours": 1},
        "Quotes a bootcamper's feedback title verbatim in its `Source:` line, the same "
        "class as the license-cap spec above. That exact string is the content-addressed "
        "dedup key `feedback/PROCESSED.jsonl` records for entry ab0bf0a790067999, and the "
        "archived entry it quotes lives under the whole-path-exempt `feedback/` -- so "
        "correcting it here would misquote the source AND desync the spec from the "
        "ledger. The spec's own prose, and its filename, use `coloring`.",
    ),
    "tests/test_windows_browser_discovery.py": (
        {"programme": 3},
        "A GERMAN localized `%ProgramFiles%` fixture (`D:\\Programme`) proving "
        "environment expansion. It is not English, and rewriting it guts the test.",
    ),
    "specs/IMPLEMENTED.md": (
        {"programme": 2},
        "Records the German `D:\\Programme` fixture above -- once in the ledger entry for "
        "the spec that introduced it, and once in INV-253's own entry listing the "
        "exemptions this guard carries and why each one earns it.",
    ),
}

#: The probe words the negative controls below mutate strings with. They live in the data
#: block for the same reason the vocabulary does: they are British forms, and a fixture
#: spelled out in a test body would be indistinguishable from a defect in this file's prose.
_PROBE = "behaviour"
_PROBE_UPPER = "LICENCE"

# --- END VOCABULARY AND EXEMPTION DATA ---------------------------------------------- #

#: Defined AFTER the block so `find` locates the two comment lines above rather than these
#: two string literals -- which would excise a region ending in the wrong place.
_SENTINEL_BEGIN = "# --- BEGIN VOCABULARY AND EXEMPTION DATA "
_SENTINEL_END = "# --- END VOCABULARY AND EXEMPTION DATA "

SKIP_DIRS = frozenset((".git", "__pycache__", ".pytest_cache", "node_modules",
                       ".history", "tmp", ".venv", "venv", "backups"))

TEXT_SUFFIXES = frozenset((".md", ".py", ".json", ".yaml", ".yml", ".sh", ".ps1",
                           ".txt", ".js", ".html", ".css", ".jsonl", ".cfg", ".ini",
                           ".toml"))

#: A run of letters, then the CamelCase pieces inside it. Splitting twice is what makes
#: `snake_case` and `CamelCase` reachable by the same pass as plain prose.
_LETTER_RUN = re.compile(r"[A-Za-z]+")
_CAMEL_PIECE = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+")

#: This guard's own path, relative to the repo root. The sentinels are honored here alone.
_SELF = "tests/test_us_english_spelling.py"


def words(text):
    """Yield (lowercased word, character offset) for every whole word in `text`."""
    for run in _LETTER_RUN.finditer(text):
        base = run.start()
        for piece in _CAMEL_PIECE.finditer(run.group()):
            yield piece.group().lower(), base + piece.start()


def british_words(text):
    """Every British form in `text`, as a list of (word, line).

    ⚠️ The line number is resolved for HITS only. Resolving it for every word made this
    scan quadratic in file size -- one `count("\\n", 0, offset)` per token over a corpus
    whose largest members run to hundreds of KB -- and took the guard from ~4s to ~100s.
    Hits are rare by design, so paying O(n) per hit costs nothing.
    """
    return [(w, text.count("\n", 0, offset) + 1)
            for w, offset in words(text) if w in BRITISH_TO_US]


def _excised(rel_path, text):
    """Strip this guard's data block -- for this guard's own file and nothing else."""
    if rel_path != _SELF:
        return text
    start = text.find(_SENTINEL_BEGIN)
    end = text.find(_SENTINEL_END)
    if start == -1 or end == -1:
        return text
    return text[:start] + text[end:]


_CORPUS_CACHE = []


def corpus():
    """Every text file in the repository, as (relative path, text).

    Read once and cached: four tests walk the tree, and re-reading it each time is the
    difference between a guard that runs in seconds and one nobody wants in the suite.
    """
    if _CORPUS_CACHE:
        return _CORPUS_CACHE
    stack = [REPO_ROOT]
    while stack:
        directory = stack.pop()
        for child in sorted(directory.iterdir()):
            if child.is_dir():
                if child.name not in SKIP_DIRS:
                    stack.append(child)
            elif child.suffix.lower() in TEXT_SUFFIXES:
                rel = child.relative_to(REPO_ROOT).as_posix()
                _CORPUS_CACHE.append(
                    (rel, child.read_text(encoding="utf-8", errors="replace")))
    return _CORPUS_CACHE


def is_whole_path_exempt(rel):
    return any(rel == key or rel.startswith(key) for key in WHOLE_PATH_EXEMPT)


class TheCorpusIsUsEnglish(unittest.TestCase):

    def test_no_file_carries_an_unwaived_british_spelling(self):
        offenders = []
        for rel, text in corpus():
            if is_whole_path_exempt(rel):
                continue
            found = british_words(_excised(rel, text))
            waived = PER_FILE_WAIVERS.get(rel, ({}, ""))[0]
            counts = Counter(word for word, _ in found)
            for word, line in found:
                if counts[word] == waived.get(word):
                    continue
                offenders.append("%s:%d %s -> %s"
                                 % (rel, line, word, BRITISH_TO_US[word]))
        self.assertEqual(
            [], offenders,
            "British spellings found (INV-253 -- US English is the only spelling written "
            "in this repository):\n  " + "\n  ".join(sorted(set(offenders))))

    def test_every_waiver_still_matches_exactly_what_it_claims(self):
        """A waiver whose word has gone, or whose count moved, fails rather than lingers."""
        for rel, (waived, reason) in sorted(PER_FILE_WAIVERS.items()):
            with self.subTest(path=rel):
                path = REPO_ROOT / rel
                self.assertTrue(path.is_file(), "%s is waived but does not exist" % rel)
                actual = Counter(w for w, _ in british_words(
                    _excised(rel, path.read_text(encoding="utf-8", errors="replace"))))
                self.assertEqual(
                    waived, dict(actual),
                    "%s's waiver no longer describes the file. Waived %s, found %s. "
                    "Reason on record: %s" % (rel, waived, dict(actual), reason))

    def test_every_whole_path_exemption_still_matches_something(self):
        """An exemption matching nothing outlived its reason and must be removed."""
        for key, reason in sorted(WHOLE_PATH_EXEMPT.items()):
            with self.subTest(path=key):
                total = sum(len(british_words(text)) for rel, text in corpus()
                            if rel == key or rel.startswith(key))
                self.assertGreater(
                    total, 0,
                    "%s is exempt but now contains no British spelling at all -- the "
                    "exemption is stale. Reason on record: %s" % (key, reason))

    def test_every_exemption_carries_a_reason(self):
        for key, reason in list(WHOLE_PATH_EXEMPT.items()):
            with self.subTest(path=key):
                self.assertTrue(reason.strip(), "%s is exempt with no reason" % key)
        for rel, (_, reason) in list(PER_FILE_WAIVERS.items()):
            with self.subTest(path=rel):
                self.assertTrue(reason.strip(), "%s is waived with no reason" % rel)


class TheMatcherSeesAllThreeShapes(unittest.TestCase):
    """Negative controls. Each mutation is applied to a string, never to a tracked file."""

    def test_plain_prose_is_caught(self):
        self.assertEqual([(_PROBE, 1)],
                         british_words("The %s of the loader is odd." % _PROBE))

    def test_a_snake_case_identifier_is_caught(self):
        self.assertEqual([(_PROBE, 1)],
                         british_words("def test_the_%s_limit_is_disclosed():" % _PROBE))

    def test_a_camel_case_identifier_is_caught(self):
        """The shape a word-boundary regex cannot see; five of these were missed once."""
        self.assertEqual([(_PROBE, 1)],
                         british_words("class NoStep%sChanged(unittest.TestCase):"
                                       % _PROBE.capitalize()))

    def test_an_upper_case_run_is_caught(self):
        self.assertEqual([(_PROBE_UPPER.lower(), 1)],
                         british_words("%s_CAP = 100" % _PROBE_UPPER))

    def test_correct_us_prose_and_identifiers_are_left_alone(self):
        """The false positives stem matching would produce, asserted one at a time."""
        for safe in ("organism", "mechanism", "parallelism", "characteristic", "equally",
                     "totally", "radialLine", "LabelLayoutAssertions", "analysis",
                     "analyses", "behavior", "license", "advertise", "exercise",
                     "supervise", "comprise", "promise", "enterprise", "expertise",
                     "generalis", "dialogue", "controlled", "enrolled"):
            with self.subTest(word=safe):
                self.assertEqual([], british_words(safe))

    def test_the_line_number_reported_is_the_line_the_word_is_on(self):
        self.assertEqual([(_PROBE, 3)], british_words("one\ntwo\nthe %s\n" % _PROBE))


class TheWaiversCannotBeUsedAsASilencer(unittest.TestCase):
    """⛔ The two documents most likely to be edited on this subject stay watched."""

    def _waived_check_holds(self, rel, text):
        """Re-run the waiver assertion against `text` without touching the file."""
        waived = PER_FILE_WAIVERS[rel][0]
        actual = Counter(w for w, _ in british_words(_excised(rel, text)))
        return waived == dict(actual)

    def test_a_british_word_added_to_the_prose_of_a_waived_file_still_fails(self):
        for rel in ("docs/development.md",
                    "specs/us-english-spelling-is-unregistered-and-unguarded.md",
                    "specs/INVARIANTS.md"):
            with self.subTest(path=rel):
                text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
                self.assertTrue(self._waived_check_holds(rel, text),
                                "%s does not match its own waiver before mutation" % rel)
                self.assertFalse(
                    self._waived_check_holds(rel, text + "\nThe %s is wrong.\n" % _PROBE),
                    "%s absorbed a new British spelling without failing -- its waiver is "
                    "acting as a general silencer" % rel)

    def test_one_more_of_an_already_waived_word_still_fails(self):
        """The waiver pins a COUNT, so it cannot absorb a second instance of its own word."""
        rel = "docs/development.md"
        text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
        self.assertFalse(
            self._waived_check_holds(rel, text + "\nthe %s\n" % _PROBE_UPPER.lower()))

    def test_the_sentinels_are_not_a_general_silencer(self):
        """Another file wrapping its text in the sentinels is scanned regardless."""
        wrapped = "%s---\n%s\n%s---\n" % (_SENTINEL_BEGIN, _PROBE, _SENTINEL_END)
        self.assertEqual([(_PROBE, 2)],
                         british_words(_excised("plugins/anything.md", wrapped)))

    def test_the_guards_own_data_block_is_excised_but_its_prose_is_not(self):
        text = (REPO_ROOT / _SELF).read_text(encoding="utf-8", errors="replace")
        self.assertIn(_SENTINEL_BEGIN, text, "the data block sentinel was removed")
        self.assertIn(_SENTINEL_END, text, "the data block sentinel was removed")
        self.assertEqual([], british_words(_excised(_SELF, text)),
                         "this guard's own prose carries a British spelling")
        self.assertGreater(len(british_words(text)), 100,
                           "the data block no longer holds the vocabulary")


class TheVocabularyIsCoherent(unittest.TestCase):

    def test_no_entry_maps_a_word_to_itself(self):
        same = [b for b, us in BRITISH_TO_US.items() if b == us]
        self.assertEqual([], same, "these map to themselves: %s" % same)

    def test_no_us_form_is_itself_listed_as_british(self):
        """A pair's US form must never appear among the keys: the guard would then demand
        a replacement for the word it just told the author to write."""
        both = sorted(set(BRITISH_TO_US.values()) & set(BRITISH_TO_US))
        self.assertEqual([], both, "listed as both British and US: %s" % both)

    def test_analyses_is_deliberately_absent(self):
        """Limitation 2. If a later edit adds it, correct US prose starts failing."""
        self.assertNotIn("analyses", BRITISH_TO_US,
                         "`analyses` is also the US plural of `analysis` -- adding it "
                         "makes this guard fail on correct US prose")

    def test_the_vocabulary_is_substantial(self):
        self.assertGreater(len(BRITISH_TO_US), 300)


if __name__ == "__main__":
    unittest.main()
