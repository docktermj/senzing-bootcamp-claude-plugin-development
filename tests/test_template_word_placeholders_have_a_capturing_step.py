"""A template placeholder that asks for the Bootcamper's words for a pinned option has a step
that captures them.

Discover the Business Problem Step 11 writes `docs/business_problem.md` from a template whose
**Desired Output** line reads
``**Format**: [every option they chose, comma-separated — Master list / API / Reports /
<the Bootcamper's words for "Something else">]``. Step 6d's option 4 was pinned as a bare
``> 4. **Something else**`` and handled with the single word ``recorded.`` — nothing asked what
the something else was, and nothing kept it. A guide filling the template therefore had a slot
with no producing step, and could only leave the literal placeholder in the shipped document or
invent a phrase for it.

⛔ **A selection cannot produce prose unless its step asks for prose.** That is the whole class:
the template quotes an option *by name* and asks for the Bootcamper's own words for it, so the
option has to carry the ask and its handling has to keep the answer. The plugin's sibling
multi-select already ships the shape — `module-05-data-quality-mapping/phase2-data-mapping.md`
pins ``> 4. **Something else** — tell me what to adjust.`` and handles it with *"revise the plan
as they describe and re-present it"* — so this guard measures Module 1 against a shape the
plugin already has rather than one invented here.

**What is derived, and from where (INV-246).** Neither half is written into this test:

* The **sites** come from the shipped prose: every bracketed placeholder, in any file under
  `plugins/`, that names the Bootcamper's words *and* quotes a subject. No path and no
  placeholder is listed here.
* The **producing option** comes from the shipped option lists: the pinned ``N. **<subject>**``
  line whose bold label is the subject the placeholder quoted, searched inside the skill
  directory the placeholder lives in.
* The **handling** comes from that option's ``**N, "<subject>":**`` entry, the marker idiom
  INV-284's 2026-10-12 note already requires of every pinned gate — so this guard reads the
  index the plugin maintains rather than a second one of its own.

**Scope, with its reason (INV-282).** The vocabulary is deliberately narrow: a placeholder
counts only when it **quotes the subject** whose words it wants.

* The wider reading — any bracketed placeholder naming anyone's words — was measured over the
  same corpus while this guard was written (#688) and reported **7** sites, **6** of them
  correct prose: five ``[Their own words, verbatim]`` quote lines in Step 11's own template and
  one ``<their question, in their own words>`` in Module 7's saved query requirements. Each of
  those names no subject because it does not need one — the surrounding section *is* the
  subject, and the interview prose that fills it is produced by the open question that section
  came from. A guard reporting them would be reporting correct prose and would be relaxed
  rather than fixed, which is the waiver INV-282 exists to prevent. Both constructions are
  pinned below as text the matcher must **not** flag.
* The quoted subject is what makes the claim checkable: it names one pinned option, so the
  producing step is findable by scanning instead of by judgment.
* ⚠️ **The scan is deliberately wider than the rule's own framing.** The rule is about document
  templates, and every site found today does sit inside one; the scan still reads all of
  `plugins/`, because a guard that first had to recognize a template would be blind to a
  template shape it failed to recognize — and a placeholder asking for words nobody collected is
  a defect wherever it is written.
* **The option is searched in the placeholder's own skill directory**, not the whole plugin:
  ``**Something else**`` is a label two different modules use for two different gates, and the
  template's producing step is the one in its own module. Matching across modules would let a
  correct option in Module 5 certify a missing one in Module 1.

**The sweep this guard did not turn into an assertion (#688).** Every pinned option list in the
plugin was swept for an open option whose handling records nothing while a downstream template
needs its content. Step 6d option 4 was the only one. The other short handling entries —
`feedback.md`'s High/Medium/Low, Bootcamp preparation's platform list, Module 6's record-count
bands — all map a **closed vocabulary** to a documented value, which is what their templates
read; requiring prose from them would be a decision about what the flow should do, not a missing
capture, and this guard does not make it. They stay out of the site set because no template asks
for the Bootcamper's words for them, so the exclusion is derived rather than listed.

**What this cannot establish (INV-308).** It establishes that the option **asks** for the words
and that its handling **names the Bootcamper** as the source of what is recorded. It cannot
establish that a live guide then writes them into `docs/business_problem.md`; only `dry-run`
phase 3 observes that.

Scanned sites are asserted non-empty (INV-265), prose is read across line wraps (INV-346), and
the files are reached through the shared corpus listing (`_corpus`) rather than a built path.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).

Source issue: #688.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from collections import namedtuple

from _corpus import REPO_ROOT, corpus_files
from _wrapped_text import blocks, collapsed_blocks, line_of

#: A bracketed placeholder inside a template or a saved structure: ``[…]`` or ``<…>``. Read on a
#: collapsed block, which holds no newlines, so a placeholder wrapped in the shipped file is one
#: span (INV-346). Neither form nests inside itself, so the innermost span is what matches.
PLACEHOLDER = re.compile(r"<[^<>]{1,200}>|\[[^\[\]]{1,200}\]")
#: The placeholder names the Bootcamper's words. Derived from the claim — *whose* words — rather
#: than from the phrasings observed at the site this guard was written for (INV-282).
NAMES_WORDS = re.compile(r"\b(?:bootcamper|bootcamper's|their|theirs|they|them)\b[^<>\[\]]{0,60}?"
                         r"\bwords\b", re.I)
#: The subject whose words are wanted, quoted inside the placeholder: ``for "Something else"``.
SUBJECT = re.compile(r"[\"“]([^\"”]{1,80})[\"”]")

#: A pinned option line: ``4. **Something else** — tell me what to adjust.`` Blockquote markers
#: are already stripped by ``blocks``.
OPTION = re.compile(r"^(?P<num>\d+[a-z]?)\.\s+\*\*(?P<label>[^*]+)\*\*(?P<ask>.*)$")
#: Its handling entry, in the marker idiom INV-284 requires: ``- **4, "Something else":** …``.
HANDLING = re.compile(r"^-\s+\*\*(?P<num>\d+[a-z]?),\s*[\"“](?P<label>[^\"”]+)[\"”]"
                      r"\s*:?\*\*:?\s*(?P<body>.*)$")
#: A line that opens a list item, so a wrapped option or handling entry is read as one string.
ITEM = re.compile(r"^\s*(?:[-*+]|\d+[a-z]?\.)\s")
#: Punctuation an ask clause may open with: ``— tell me what to adjust.``
ASK_LEAD = re.compile(r"^[\s—–:;,.\-]+")
#: The handling names the Bootcamper as the source of what it records. Same derivation as
#: ``NAMES_WORDS``: the claim is *whose* answer is kept, not the verb used to keep it.
NAMES_BOOTCAMPER = re.compile(r"\b(?:bootcamper|bootcamper's|their|theirs|they|them)\b", re.I)

#: Floor (INV-265). Measured at #688: one placeholder in the shipped plugin names the
#: Bootcamper's words for a quoted option. The floor sits at the measured figure, because a
#: corpus that stops carrying one means the scan broke, not that the class went away.
MIN_SITES = 1

#: A placeholder asking for the Bootcamper's words for a named option.
Site = namedtuple("Site", "path line subject text")
#: A pinned option and the handling entry that discharges it.
Option = namedtuple("Option", "path line num label ask body body_line")


def logical_lines(text):
    """``(lineno, flat)`` per logical line: list items joined across their wrapped continuations.

    Read through ``blocks``, so blockquote markers are stripped and fenced content never joins
    the prose around it. Within a block a line opening a list item starts a new logical line and
    every following line joins it, which is how a wrapped option or handling entry is matched as
    one string while still reporting the line it started on (INV-346).
    """
    for block in blocks(text):
        lineno, parts = None, []
        for n, line in block:
            if ITEM.match(line) or lineno is None:
                if parts:
                    yield lineno, " ".join(parts)
                lineno, parts = n, [line.strip()]
            else:
                parts.append(line.strip())
        if parts:
            yield lineno, " ".join(parts)


def placeholder_sites(paths):
    """Every placeholder naming the Bootcamper's words for a quoted subject, across ``paths``."""
    found, seen = [], set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for flat, origin in collapsed_blocks(text):
            for match in PLACEHOLDER.finditer(flat):
                span = match.group(0)
                if not NAMES_WORDS.search(span):
                    continue
                subject = SUBJECT.search(span)
                if not subject:
                    continue
                line = line_of(origin, match.start())
                key = (path, line, subject.group(1))
                if key in seen:
                    continue
                seen.add(key)
                found.append(Site(path, line, subject.group(1).strip(), span))
    return found


def options_labeled(paths, label):
    """Every pinned option in ``paths`` whose bold label is ``label``, with its handling body."""
    out = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        items = list(logical_lines(text))
        handling = {}
        for lineno, flat in items:
            hit = HANDLING.match(flat)
            if hit and hit.group("label").strip() == label:
                handling[hit.group("num")] = (hit.group("body").strip(), lineno)
        for lineno, flat in items:
            hit = OPTION.match(flat)
            if not hit or hit.group("label").strip() != label:
                continue
            body, body_line = handling.get(hit.group("num"), (None, None))
            out.append(Option(path, lineno, hit.group("num"), label,
                              ASK_LEAD.sub("", hit.group("ask")).strip(), body, body_line))
    return out


def plugin_files():
    return [p for p in corpus_files("plugins", suffixes={".md"})]


def rel(path):
    return path.relative_to(REPO_ROOT)


class TemplatePlaceholdersHaveACapturingStep(unittest.TestCase):
    """Every placeholder asking for the Bootcamper's words for an option has a step behind it."""

    @classmethod
    def setUpClass(cls):
        cls.files = plugin_files()
        cls.sites = placeholder_sites(cls.files)

    def test_the_scan_found_the_sites_it_is_written_against(self):
        """INV-265: a guard that silently scans nothing certifies nothing."""
        self.assertTrue(self.files, "the corpus listing returned no files under plugins/")
        self.assertGreaterEqual(
            len(self.sites), MIN_SITES,
            "no placeholder names the Bootcamper's words for a quoted option; the scan, the "
            "placeholder vocabulary or the corpus listing broke")

    def test_every_placeholder_has_an_option_that_asks_and_handling_that_records(self):
        gaps = []
        for site in self.sites:
            skill_dir = site.path.parent
            kin = [p for p in self.files if p.parent == skill_dir]
            options = options_labeled(kin, site.subject)
            if not options:
                gaps.append(
                    f"{rel(site.path)}:{site.line} wants the Bootcamper's words for "
                    f'"{site.subject}", and no option in {rel(skill_dir)} is labeled that')
                continue
            for option in options:
                if not option.ask:
                    gaps.append(
                        f"{rel(option.path)}:{option.line} pins option {option.num}, "
                        f'"{option.label}", with no ask clause, while '
                        f"{rel(site.path)}:{site.line} renders the Bootcamper's words for it")
                if option.body is None:
                    gaps.append(
                        f"{rel(option.path)}:{option.line} option {option.num}, "
                        f'"{option.label}", has no `**{option.num}, "{option.label}":**` '
                        f"handling entry (INV-284)")
                elif not NAMES_BOOTCAMPER.search(option.body):
                    gaps.append(
                        f"{rel(option.path)}:{option.body_line} handles option {option.num}, "
                        f'"{option.label}", as {option.body!r}, which records nothing of the '
                        f"Bootcamper's, while {rel(site.path)}:{site.line} renders their words "
                        f"for it")
        self.assertEqual([], gaps, "\n".join(["placeholders with no producing step:"] + gaps))


class MatcherFixtures(unittest.TestCase):
    """INV-282: every phrasing that ships is pinned, and so is every one that must not flag."""

    def test_shipped_placeholders_without_a_quoted_subject_are_not_sites(self):
        for text in ("[Their own words, verbatim]", "<their question, in their own words>"):
            with self.subTest(text=text):
                self.assertIsNotNone(NAMES_WORDS.search(text), "the wide reading matches it")
                self.assertIsNone(SUBJECT.search(text),
                                  "it names no subject, so it is not this guard's business")

    def test_a_shipped_placeholder_naming_no_words_is_not_a_site(self):
        text = "[every option they chose, comma-separated]"
        self.assertIsNone(NAMES_WORDS.search(text),
                          "it renders selections, so it asks for no prose at all")

    def test_a_placeholder_naming_a_quoted_subject_is_a_site(self):
        text = '<the Bootcamper\'s words for "Something else">'
        self.assertIsNotNone(NAMES_WORDS.search(text))
        self.assertEqual("Something else", SUBJECT.search(text).group(1))

    def test_shipped_option_lines_read_as_asked_or_bare(self):
        asked = OPTION.match("4. **Something else** — tell me what to adjust.")
        self.assertEqual("tell me what to adjust.", ASK_LEAD.sub("", asked.group("ask")).strip())
        bare = OPTION.match("4. **Something else**")
        self.assertEqual("", ASK_LEAD.sub("", bare.group("ask")).strip())

    def test_shipped_handling_bodies_read_as_recording_or_not(self):
        recorded = HANDLING.match(
            '- **4, "Something else":** revise the plan as they describe and re-present it.')
        self.assertIsNotNone(NAMES_BOOTCAMPER.search(recorded.group("body")))
        for body in ('- **4, "Something else":** recorded.',
                     '- **1, "High":** recorded as High.',
                     '- **4, "Not sure yet":** `undecided`.'):
            with self.subTest(body=body):
                hit = HANDLING.match(body)
                self.assertIsNotNone(hit, "the handling marker idiom is read")
                self.assertIsNone(NAMES_BOOTCAMPER.search(hit.group("body")),
                                  "a closed-vocabulary handling records nothing of theirs")

    def test_a_wrapped_option_is_read_as_one_logical_line(self):
        text = "> 1. **Alpha**\n> 4. **Something else** — tell me\n>    what to adjust.\n"
        items = dict((flat.split(".")[0], flat) for _, flat in logical_lines(text))
        self.assertIn("tell me what to adjust.", items["4"])


if __name__ == "__main__":
    unittest.main()
