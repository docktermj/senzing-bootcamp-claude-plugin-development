"""Every deliverable INV-050's tree says a Bootcamper gets is named where they read it (#699).

INV-050's layout tree is the one place that records, per artifact, whether the Bootcamper
always gets it. Two entries carry such a statement today:

* `docs/bootcamp_data_discoveries.md` -- "Always produced in Module 7 (both .md and .pdf)"
* `docs/bootcamp_recap.mp4` -- "Graduation video, rendered only on a yes (INV-340)"

Until #699 neither was named on any surface a prospective Bootcamper reads. The root
`README.md`'s "What you finish with" named `src/`, `data/`, `database/`, the recap PDF and the
`production/` starter; `docs/README.md` and `docs/index.html` named no deliverable set at all,
only the `/graduate` row's recap PDF and `production/` starter. Nothing said the list was
exhaustive, but the heading reads as the full set, and the two it omitted are the two most
shareable things the bootcamp makes.

**The rule.**

⛔ **Every deliverable INV-050's tree annotates as always produced MUST be named on at least one
user-facing surface, and a deliverable it annotates as produced only on the Bootcamper's yes MUST
be named there as an offer rather than as something they finish with.**

INV-340 gives graduation a real "no" path, so "you finish with a video" is false for every
Bootcamper who declines, while INV-050 says the data-discoveries document is produced on every
path and it can be stated flatly. Getting that distinction backwards in either direction is the
defect here -- a deliverable left unmentioned, or a promise the product does not keep.

**Both sets are derived, never listed (INV-246).**

* The deliverables come from INV-050's fenced tree, read with `extract_tree()` from
  `tests/test_invariant_layout_tree.py`, so the tree has one parser rather than two. The tier is
  read from the entry's own comment column, and a comment that extends its statement to a
  sibling ("both .md and .pdf") brings that sibling in when the tree has an entry for it.
* The surfaces come from what `propagate.sh` publishes for a bootcamper to read:
  `propagated_paths()` gives the mirror's sources, `parsed_excludes()` gives the `docs/` pages it
  withholds as maintainer-only, and a surface is a `.md` or `.html` page sitting directly in a
  published root. Today those are `README.md`, `docs/README.md` and `docs/index.html`; a page
  added beside them is read without editing this file, while `docs/development.md` and
  `docs/FAMILY_WORKFLOW.md` drop out because the mirror withholds them, and everything under
  `plugins/` drops out because it sits deeper than a published root's own pages.

**Measured before narrowing, 2026-10-17 (#699).** The tree held 58 leaf entries, 47 of them with
a comment. A predicate that read every annotation as a promise would match all 47 and demand the
README name `config/session_log.jsonl`, which is annotated `(reserved)`. The predicates here read
what a comment says about production instead: "always produced" matched one entry, which its own
comment extends to two files, and "only on a yes" matched one. The annotations left out say
something else -- `(reserved)`, `(future)`, `(legacy)`, "written in Module 4", "not copied at
graduation", and the two graduation PDFs' "(best-effort)", which INV-050's own prose calls
"**best-effort**, not always-produced" because their absence is conforming.

**Reading the surfaces (INV-346).** The rule is about a sentence, so the Markdown surfaces are
read through `collapsed_blocks()`, which joins a phrase across a line wrap and still reports the
line a match starts on. One surface is HTML, where a Markdown-shaped read finds tags rather than
prose and would leave this guard passing on two surfaces out of three. `docs/index.html` is
therefore read with `html.parser` into the same `(flat, origin)` pairs: the text a reader sees,
cut into blocks at each block-level tag, with `<script>` and `<style>` contents and HTML comments
left out, entities unescaped and whitespace collapsed. One matcher then reads both kinds.

Negative controls: each deliverable's names are struck from every surface and the check reports
that deliverable alone, naming it; the offer wording is struck and the video is reported by file
and line; synthetic trees and surfaces exercise both tiers; and the HTML read is pinned on
entities, comments, scripts and a sentence wrapped across source lines.

⚠️ **What a green run does not establish.** It establishes that each deliverable is named on at
least ONE surface, not that the three agree: #699 put both on all three, and nothing here would
notice two of them losing it. It says nothing about `docs/REVISIT_BOOTCAMP.md` or
`docs/bootcamp_recap.pdf`, which their own steps produce unconditionally while the tree annotates
neither as always produced -- the scan reads the annotation, and `specs/` is a frozen archive
(INV-307), so adding one is `/review-invariants`' work rather than this guard's.

Stdlib only (INV-108); the repository's files are listed through `tests/_corpus.py` (INV-367) and
read as text, no network.

Source issue: #699.

Run:  python3 -m unittest discover -s tests
"""
import html.parser
import re
import unittest
from pathlib import Path

from _corpus import corpus_files
from _wrapped_text import collapsed_blocks, line_of
from test_invariant_layout_tree import extract_tree
from test_maintainer_docs_stay_out_of_public import parsed_excludes
from test_maintainer_tooling_stays_out_of_public import propagated_paths

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The comment column says production is unconditional: the Bootcamper always gets it.
ALWAYS = re.compile(r"always\s+produced", re.I)

#: The comment column says production waits on the Bootcamper's yes (INV-340).
ONLY_ON_A_YES = re.compile(r"only\s+on\s+a\s+yes", re.I)

#: "(both .md and .pdf)" -- the comment extends its statement to the entry's siblings.
SIBLING_SUFFIXES = re.compile(r"both\s+((?:\.\w+)(?:\s*(?:,|and|or)\s*\.\w+)+)", re.I)
SUFFIX = re.compile(r"\.\w+")

#: The vocabulary that marks a deliverable as offered rather than promised. Derived from the
#: CLAIM -- "the Bootcamper is asked, and may decline" -- rather than from the phrasings that
#: happen to ship (INV-282); the shipped ones are pinned as fixtures in `ShippedProseIsAccepted`.
OFFERED = re.compile(
    r"offer(?:s|ed|ing)?|optional(?:ly)?|if you (?:want|say yes|accept)|only on a yes"
    r"|say(?:ing)? no|decline|choose to|can ask for", re.I)

#: HTML elements that end a block of visible text. A block is the unit the offer rule reads.
BLOCK_TAGS = frozenset(
    "address article aside blockquote br dd div dl dt fieldset figcaption figure footer form"
    " h1 h2 h3 h4 h5 h6 header hr li main nav ol p pre section table tbody td tfoot th thead"
    " tr ul".split())

#: Elements whose contents are code for the browser, never prose for the reader.
SKIPPED_TAGS = frozenset(("script", "style"))


class Deliverable:
    """One tree entry that says when the Bootcamper gets it, with the names a surface may use."""

    def __init__(self, tier, entry, names):
        #: "always" (unconditional) or "offered" (only on a yes).
        self.tier = tier
        self.path = entry.path
        self.line = entry.line_number
        self.comment = entry.comment.strip()
        #: The file names that count as naming it, the entry's own first.
        self.names = names

    def __repr__(self):
        return "%s (%s, INVARIANTS.md:%d)" % (self.path, self.tier, self.line)


def _sibling_names(entry, by_path):
    """The entry's file name, plus the siblings its own comment extends the statement to."""
    names = [entry.name]
    found = SIBLING_SUFFIXES.search(entry.comment)
    if not found or "." not in entry.name:
        return names
    stem = entry.path[:entry.path.rindex(".")]
    for suffix in SUFFIX.findall(found.group(1)):
        sibling = stem + suffix
        name = sibling.rsplit("/", 1)[-1]
        if sibling in by_path and name not in names:
            names.append(name)
    return names


def deliverables(text=None):
    """Every INV-050 tree entry whose comment states when the Bootcamper gets the artifact."""
    _root, entries, _continuations = extract_tree(text)
    by_path = {entry.path: entry for entry in entries}
    found = []
    for entry in entries:
        if entry.is_dir:
            continue
        if ALWAYS.search(entry.comment):
            tier = "always"
        elif ONLY_ON_A_YES.search(entry.comment):
            tier = "offered"
        else:
            continue
        found.append(Deliverable(tier, entry, _sibling_names(entry, by_path)))
    return found


def surfaces(root=REPO_ROOT):
    """The pages a prospective Bootcamper reads: the mirror's own published pages, derived.

    A surface is a `.md` or `.html` file sitting directly in a path `propagate.sh` publishes,
    minus the `docs/` pages that script withholds as maintainer-only.
    """
    published = propagated_paths()
    withheld = {name.lstrip("/") for name in parsed_excludes()}
    found = []
    for path in corpus_files(*sorted(published), root=Path(root),
                             suffixes={".md", ".html"}):
        parts = path.relative_to(root).parts
        if len(parts) == 1 and parts[0] in published:
            found.append(path)
        elif len(parts) == 2 and parts[0] in published and parts[1] not in withheld:
            found.append(path)
    return found


class _VisibleText(html.parser.HTMLParser):
    """The text an HTML page shows a reader, cut into blocks at each block-level tag.

    HTML comments and the contents of `<script>` and `<style>` never reach `handle_data` here,
    so the page's own maintenance comment cannot satisfy a rule about what a reader sees.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._chunks = []
        self._skipping = 0

    def _flush(self):
        if self._chunks:
            self.blocks.append(self._chunks)
            self._chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIPPED_TAGS:
            self._skipping += 1
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        if tag in SKIPPED_TAGS and self._skipping:
            self._skipping -= 1
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if self._skipping:
            return
        if not data.strip() and not self._chunks:
            return          # whitespace before a block opens is not part of any block
        self._chunks.append((self.getpos()[0], data))

    def close(self):
        super().close()
        self._flush()


def _collapse(chunks):
    """One block's text with whitespace collapsed, and the source line of each character.

    Nothing is inserted between two chunks: `(<code>x</code>)` renders as `(x)`, so an inline
    element boundary is not whitespace and must not become a space.
    """
    text, origin = [], []
    in_space = False
    for first_line, data in chunks:
        line = first_line
        for char in data:
            if char.isspace():
                if not in_space and text:
                    text.append(" ")
                    origin.append(line)
                in_space = True
                if char == "\n":
                    line += 1
                continue
            text.append(char)
            origin.append(line)
            in_space = False
    while text and text[-1] == " ":
        text.pop()
        origin.pop()
    return "".join(text), origin


def visible_blocks(text):
    """`(flat, origin)` for each block of visible text in an HTML page, as `collapsed_blocks`."""
    parser = _VisibleText()
    parser.feed(text)
    parser.close()
    for chunks in parser.blocks:
        flat, origin = _collapse(chunks)
        if flat:
            yield flat, origin


def read_surface(path, text=None):
    """`(rel, blocks)` for one surface, read HTML-aware or Markdown-aware by its suffix."""
    rel = Path(path).relative_to(REPO_ROOT).as_posix() if Path(path).is_absolute() else str(path)
    if text is None:
        text = Path(path).read_text(encoding="utf-8")
    reader = visible_blocks if str(path).endswith(".html") else collapsed_blocks
    return rel, list(reader(text))


def read_surfaces(paths=None):
    """Every surface read into `(rel, blocks)` pairs."""
    return [read_surface(path) for path in (surfaces() if paths is None else paths)]


def sites(deliverable, read):
    """Every `(rel, line, flat)` where a surface names the deliverable."""
    found = []
    for rel, blocks in read:
        for flat, origin in blocks:
            for name in deliverable.names:
                index = flat.find(name)
                if index != -1:
                    found.append((rel, line_of(origin, index), flat))
                    break
    return found


def problems(found, read):
    """Every deliverable no surface names, and every offered one named as a promise."""
    out = []
    for deliverable in found:
        named = sites(deliverable, read)
        if not named:
            out.append(
                "%s is named on no user-facing surface (%s), though INV-050's tree says "
                "\"%s\" at specs/INVARIANTS.md:%d. A Bootcamper reading %s never learns they "
                "get it" % (deliverable.path, " / ".join(deliverable.names),
                            deliverable.comment, deliverable.line,
                            ", ".join(rel for rel, _blocks in read) or "any surface"))
            continue
        if deliverable.tier != "offered":
            continue
        for rel, line, flat in named:
            if not OFFERED.search(flat):
                out.append(
                    "%s:%d states %s as something the Bootcamper finishes with, but INV-050's "
                    "tree says \"%s\" -- it must read as an offer, because graduation takes a "
                    "no (INV-340): %s" % (rel, line, deliverable.path, deliverable.comment,
                                          flat[:140]))
    return out


class TheDerivationIsNotVacuous(unittest.TestCase):
    """INV-265 -- every assertion below passes on an empty set, so the sets are measured."""

    def test_both_tiers_are_populated(self):
        tiers = sorted({d.tier for d in deliverables()})
        self.assertEqual(
            ["always", "offered"], tiers,
            "INV-050's tree no longer states both kinds of promise (found %s). Either the "
            "annotations were reworded, or the predicates here stopped matching them, and the "
            "checks below would pass over an empty set" % (tiers or "none"))

    def test_the_surfaces_are_the_pages_the_mirror_publishes(self):
        """Anchored on pages that predate this guard, so it cannot pass tautologically."""
        found = {path.relative_to(REPO_ROOT).as_posix() for path in surfaces()}
        for expected in ("README.md", "docs/README.md", "docs/index.html"):
            self.assertIn(expected, found,
                          "%s is not among the derived user-facing surfaces %s; either the "
                          "mirror stopped publishing it or the derivation is wrong"
                          % (expected, sorted(found)))
        for maintainer in ("docs/development.md", "docs/FAMILY_WORKFLOW.md"):
            self.assertNotIn(maintainer, found,
                             "%s is a maintainer page propagate.sh withholds; a rule about what "
                             "a bootcamper reads must not be satisfiable there" % maintainer)

    def test_every_surface_yields_blocks(self):
        for rel, blocks in read_surfaces():
            with self.subTest(surface=rel):
                self.assertTrue(blocks, "%s was read as no blocks at all; the reader for its "
                                        "format broke and nothing can be found in it" % rel)

    def test_the_docstring_names_every_derived_surface(self):
        for path in surfaces():
            rel = path.relative_to(REPO_ROOT).as_posix()
            with self.subTest(surface=rel):
                self.assertIn("`%s`" % rel, __doc__,
                              "%s is a user-facing surface this guard reads, and the docstring "
                              "does not name it" % rel)


class EveryPromisedDeliverableIsNamed(unittest.TestCase):
    """The real files."""

    def test_each_deliverable_is_named_and_the_offered_one_reads_as_an_offer(self):
        found = problems(deliverables(), read_surfaces())
        if found:
            self.fail("\n".join(found))


class ShippedProseIsAccepted(unittest.TestCase):
    """INV-282 -- the phrasings that ship are pinned, so a later tightening cannot flag them."""

    #: What the surfaces say about the offered video today, quoted from the shipped text: the
    #: two READMEs' sentence, and the Pages site's list item.
    SHIPPED_OFFERS = (
        "At graduation you are also offered a narrated 2-minute graduation video "
        "(`docs/bootcamp_recap.mp4`); say no and nothing is rendered.",
        "Optional A narrated 2-minute graduation video (docs/bootcamp_recap.mp4). "
        "Graduation offers it once; say no and nothing is rendered.",
    )

    #: Correct prose the offer rule must NOT be asked about: the always-produced deliverable is
    #: stated flatly, and nothing requires an offer word beside it.
    FLAT_STATEMENTS = (
        "a write-up of what Senzing found in your data (`docs/bootcamp_data_discoveries.md`)",
        "You end with working Senzing code and data in your project",
    )

    def test_every_shipped_offer_phrasing_matches(self):
        for phrasing in self.SHIPPED_OFFERS:
            with self.subTest(phrasing=phrasing):
                self.assertTrue(OFFERED.search(phrasing),
                                "shipped prose reads as an offer and the matcher does not see "
                                "it; relax the matcher rather than the prose (INV-282)")

    def test_every_pinned_phrasing_is_still_shipped(self):
        """A fixture that no surface carries pins nothing (INV-265)."""
        flats = [flat for _rel, blocks in read_surfaces() for flat, _origin in blocks]
        for phrasing in self.SHIPPED_OFFERS:
            with self.subTest(phrasing=phrasing[:60]):
                self.assertTrue(any(phrasing in flat for flat in flats),
                                "no surface carries this phrasing any more; re-quote it from "
                                "the text that ships rather than deleting the pin")

    def test_a_flat_promise_does_not_match(self):
        for phrasing in self.FLAT_STATEMENTS:
            with self.subTest(phrasing=phrasing):
                self.assertIsNone(OFFERED.search(phrasing))

    def test_the_offer_rule_only_asks_about_the_offered_tier(self):
        """A flat statement of the always-produced deliverable is never reported."""
        tree = _synthetic_tree()
        read = [("surface.md", list(collapsed_blocks(
            "You finish with discoveries.md. You are offered video.mp4.")))]
        self.assertEqual([], problems(deliverables(tree), read))


def _synthetic_tree(always="# Always produced in Module 7 (both .md and .pdf)",
                    offered="# Graduation video, rendered only on a yes (INV-340)"):
    """A minimal INV-050 section, so the predicates can be exercised without the real tree."""
    return ("## INV-050: Project layout\n\n```text\n"
            "project/\n"
            "└── docs/\n"
            "    ├── discoveries.md                %s\n"
            "    ├── discoveries.pdf\n"
            "    ├── notes.md                      # (reserved)\n"
            "    └── video.mp4                     %s\n"
            "```\n" % (always, offered))


class TheTreeIsReadByItsOwnWords(unittest.TestCase):
    """Synthetic trees: which entries the two predicates pick up, and which they leave."""

    def test_both_tiers_and_nothing_else(self):
        found = {d.path: d for d in deliverables(_synthetic_tree())}
        self.assertEqual({"docs/discoveries.md", "docs/video.mp4"}, set(found))
        self.assertEqual("always", found["docs/discoveries.md"].tier)
        self.assertEqual("offered", found["docs/video.mp4"].tier)

    def test_a_sibling_the_comment_names_is_carried_in(self):
        found = {d.path: d for d in deliverables(_synthetic_tree())}
        self.assertEqual(["discoveries.md", "discoveries.pdf"],
                         found["docs/discoveries.md"].names)

    def test_a_sibling_the_tree_does_not_hold_is_not_invented(self):
        tree = _synthetic_tree(always="# Always produced (both .md and .mp3)")
        found = {d.path: d for d in deliverables(tree)}
        self.assertEqual(["discoveries.md"], found["docs/discoveries.md"].names)

    def test_the_real_tree_states_both_promises(self):
        found = {d.path: d.tier for d in deliverables()}
        self.assertEqual("always", found.get("docs/bootcamp_data_discoveries.md"))
        self.assertEqual("offered", found.get("docs/bootcamp_recap.mp4"))

    def test_the_real_always_produced_deliverable_covers_both_its_files(self):
        found = {d.path: d for d in deliverables()}
        self.assertEqual(["bootcamp_data_discoveries.md", "bootcamp_data_discoveries.pdf"],
                         found["docs/bootcamp_data_discoveries.md"].names)


class TheHtmlReadIsWhatAReaderSees(unittest.TestCase):
    """The HTML half, pinned: a Markdown-shaped read would find none of this."""

    def test_a_sentence_wrapped_across_source_lines_is_one_block(self):
        page = "<p>You are offered\n  a short recap video\n  (<code>docs/x.mp4</code>).</p>"
        blocks = list(visible_blocks(page))
        self.assertEqual(1, len(blocks))
        flat, origin = blocks[0]
        self.assertEqual("You are offered a short recap video (docs/x.mp4).", flat)
        self.assertEqual(1, line_of(origin, flat.index("You")))
        self.assertEqual(3, line_of(origin, flat.index("docs/x.mp4")))

    def test_entities_are_unescaped(self):
        self.assertEqual([("a &amp b", [1] * 8)], list(visible_blocks("<p>a &amp;amp b</p>")))

    def test_a_comment_is_not_what_a_reader_sees(self):
        self.assertEqual([], list(visible_blocks("<!-- docs/x.mp4 -->")))

    def test_script_and_style_contents_are_not_prose(self):
        page = "<script>var a = 'docs/x.mp4';</script><style>.a{content:'docs/x.mp4'}</style>"
        self.assertEqual([], list(visible_blocks(page)))

    def test_two_list_items_are_two_blocks(self):
        page = "<ul><li>docs/x.mp4 offered</li><li>docs/y.pdf</li></ul>"
        self.assertEqual(["docs/x.mp4 offered", "docs/y.pdf"],
                         [flat for flat, _origin in visible_blocks(page)])


class TheCheckCatchesWhatItIsFor(unittest.TestCase):
    """Negative controls, on in-memory copies of the real surfaces."""

    def setUp(self):
        self.texts = [(path, path.read_text(encoding="utf-8")) for path in surfaces()]

    def _read(self, mutate):
        return [read_surface(path, mutate(text)) for path, text in self.texts]

    def test_striking_each_deliverable_from_every_surface_reports_it_alone(self):
        for deliverable in deliverables():
            with self.subTest(deliverable=deliverable.path):
                def mutate(text, names=deliverable.names):
                    for name in names:
                        text = text.replace(name, "struck-out")
                    return text
                read = self._read(mutate)
                found = problems(deliverables(), read)
                self.assertEqual(
                    1, len(found),
                    "striking %s from every surface should report exactly that deliverable; "
                    "got %s" % (deliverable.path, found))
                self.assertIn(deliverable.path, found[0])
                self.assertIn("named on no user-facing surface", found[0])

    def test_striking_the_offer_wording_reports_the_video_by_file_and_line(self):
        read = self._read(lambda text: OFFERED.sub("hand you", text))
        found = problems(deliverables(), read)
        self.assertTrue(found, "the video read as a promise on every surface and nothing failed")
        for problem in found:
            self.assertIn("docs/bootcamp_recap.mp4", problem)
            self.assertIn("must read as an offer", problem)
            self.assertRegex(problem, r"^(README\.md|docs/[\w.]+):\d+ ")

    def test_an_unnamed_deliverable_in_a_synthetic_tree_is_reported(self):
        read = [("surface.md", list(collapsed_blocks("You finish with nothing in particular.")))]
        found = problems(deliverables(_synthetic_tree()), read)
        self.assertEqual(2, len(found))
        self.assertTrue(all("named on no user-facing surface" in p for p in found), found)

    def test_a_promise_in_a_synthetic_html_surface_is_reported(self):
        read = [("surface.html", list(visible_blocks(
            "<ul>\n<li>discoveries.md</li>\n<li>You finish with video.mp4.</li>\n</ul>")))]
        found = problems(deliverables(_synthetic_tree()), read)
        self.assertEqual(1, len(found))
        self.assertIn("surface.html:3", found[0])
        self.assertIn("docs/video.mp4", found[0])


if __name__ == "__main__":
    unittest.main()
