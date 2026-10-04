"""No shipped `search_docs(` reference pairs `category=` with no `query=`.

`search_docs` declares `query` as its **only required parameter**. Verified against the live
schema, MCP server **1.33.0**, 2026-08-23:

    {"properties": {"category": ..., "max_results": ..., "query": {"type": "string"},
                    "version": ...},
     "required": ["query"]}

Nine shipped references passed a category and no query. Three were **instructions** --
`module-02-sdk-setup/SKILL.md`'s TypeScript-port recovery flow, and two mapping steps --
and a client that validates arguments against the declared schema **cannot make that call at
all**. It is not a call returning something unhelpful; it is a call that cannot be constructed.
The guide then either invents a query (unsourced, and the outcome depends on what it invented)
or reports the tool as unavailable. ⚠️ The first of those sites is in a **recovery flow**, reached
after something has already failed, which is the worst place for a second failure.

The other six were **citations**: a fact attributed to `search_docs(category='data_mapping')`
with a server version and date but no query. Honest about *where* the answer was found and silent
about *how*, so the next reader cannot re-run the check. That cost is not hypothetical -- on
2026-08-21 a re-verification of a dated negative reconstructed a route instead of reading one,
asked a different query with a filter, and concluded a correct claim was false.

⛔ **This is INV-212's subject, not a typo.** A bare category is the strategy-free form that
invariant exists to forbid: a step retrieving bootcamper-facing content must say what vocabulary
to query with. The three instruction sites now cite it.

⚠️ **The spec's enumeration was incomplete, which is why the site set is SCANNED (INV-246).**
It named nine sites by line number; scanning found **ten**, and `phase2-data-mapping.md`'s
single-name-field authority block was the one nobody had listed. A guard given the spec's list
would have certified nine fixes and been blind to the tenth.

**The one exemption is declared in the content, not here.** `phaseA-build-loading.md` names
`search_docs(category='sdk')` to describe *what that category indexes* -- it instructs no call and
needs no query. It carries a `SEARCH-DOCS-CATEGORY-PROSE:` marker on the line above, so the
exemption is a property of the site rather than a path hardcoded in this file, and a second such
site is covered without editing the guard.

Source spec: `specs/search-docs-instructions-omit-the-required-query-parameter.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"

#: Any `search_docs(...)` reference. `re.S` because a reference may wrap across lines once its
#: query is spelled out -- a line-scoped scan silently misses those, which is how a wrapped
#: reference would become an invisible offender.
REFERENCE = re.compile(r"search_docs\((?P<args>[^)]*)\)", re.S)

#: The marker a site uses to declare itself prose-about-a-category rather than a call.
EXEMPTION_MARKER = "SEARCH-DOCS-CATEGORY-PROSE:"

#: How far above a reference the marker may sit. Kept tight on purpose: a marker further away
#: could be governing something else entirely.
MARKER_LOOKBEHIND_LINES = 4

#: Sites whose reference is an INSTRUCTION rather than an attribution, and which must therefore
#: cite the invariant requiring the retrieval strategy. Identified by the imperative wording
#: around them, not by path (INV-246).
#:
#: ⚠️ **Matched against WHITESPACE-FLATTENED text.** A first version scanned the raw window and
#: silently recognized only two of the three instruction sites: "Confirm the attribute's expected
#: form" wraps after "the", so the phrase never appears contiguously in the file. The
#: anti-vacuity test below is what surfaced it -- without that floor, this class would have
#: quietly checked two sites while reading as though it checked all of them.
INSTRUCTION_CUE = re.compile(
    r"(?i)\b(use the Senzing MCP server|Confirm the attribute|Re-confirm that statement)\b")


def flatten(text):
    return re.sub(r"\s+", " ", text)


def shipped_markdown():
    return sorted(SKILLS.glob("**/*.md"))


def references():
    """(path, line, args, exempt) for every `search_docs(` reference in shipped prose.

    The reference is matched on the whole text (``REFERENCE`` is DOTALL), so a wrapped call is
    read whole. Line-scoped by design (#424): only the exemption is found by line, and it is
    one token (``EXEMPTION_MARKER``) in a window of lines above the reference.
    """
    for path in shipped_markdown():
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        for match in REFERENCE.finditer(text):
            line_no = text[:match.start()].count("\n") + 1
            window = lines[max(0, line_no - 1 - MARKER_LOOKBEHIND_LINES):line_no]
            exempt = any(EXEMPTION_MARKER in l for l in window)
            yield path, line_no, match.group("args"), exempt


def bare_category(args):
    return "category=" in args and "query=" not in args


class TheScanFindsSomethingToCheck(unittest.TestCase):
    def test_references_are_found_at_all(self):
        found = list(references())
        self.assertGreater(
            len(found), 10,
            "fewer than eleven `search_docs(` references found in shipped prose (%d). The scan "
            "is reading almost nothing and would pass forever" % len(found))

    def test_at_least_one_reference_passes_a_query(self):
        """Guards against a regex that matches the token but never captures arguments."""
        with_query = [r for r in references() if "query=" in r[2]]
        self.assertGreater(
            len(with_query), 5,
            "almost no reference parses as carrying a `query=` argument, which means the "
            "argument capture is broken rather than the corpus being wrong")


class NoReferencePairsACategoryWithNoQuery(unittest.TestCase):
    def test_every_call_can_actually_be_constructed(self):
        offenders = [
            "%s:%d %s" % (p.relative_to(SKILLS), n, " ".join(a.split())[:60])
            for p, n, a, exempt in references() if bare_category(a) and not exempt]
        self.assertEqual(
            [], offenders,
            "a shipped `search_docs(` reference passes `category=` with no `query=`: %s. `query` "
            "is the tool's ONLY required parameter, so a schema-respecting client cannot "
            "construct this call — it is unexecutable, not merely unhelpful. Give it the "
            "vocabulary that reaches the material (INV-212), or, if it is prose describing a "
            "category rather than a call, declare that with a `%s` marker on the line above"
            % (offenders, EXEMPTION_MARKER))


class TheExemptionIsNarrowAndDeclared(unittest.TestCase):
    #: Deliberate friction. The exemption is SELF-DECLARED, so nothing stops someone silencing a
    #: real offender by writing the marker above it -- a negative control did exactly that and
    #: escaped when the cap was 2. Pinning it to the single legitimate site means any new
    #: exemption fails here and has to be argued for rather than added in passing. Raising this
    #: number is the review step.
    MAX_EXEMPT_SITES = 1

    def test_the_exemption_is_used_sparingly(self):
        exempt = [(p, n) for p, n, a, e in references() if e]
        self.assertLessEqual(
            len(exempt), self.MAX_EXEMPT_SITES,
            "%d references claim the prose-about-a-category exemption; %d is the reviewed "
            "count. The exemption is self-declared, so an extra marker is indistinguishable "
            "from silencing a real offender — which is what it did when this cap was looser. "
            "If a new site genuinely names a category without calling it, raise "
            "MAX_EXEMPT_SITES in this file as part of that change: %s"
            % (len(exempt), self.MAX_EXEMPT_SITES,
               [(str(p.name), n) for p, n in exempt]))

    def test_the_exempt_marker_names_the_category_it_governs(self):
        """A marker must be about the reference under it, not a generic silencer.

        The escaped control's marker read simply "bogus". Requiring it to name the same category
        the reference passes makes a copied-around marker fail on the next site.
        """
        for path, line_no, args, exempt in references():
            if not exempt:
                continue
            lines = path.read_text(encoding="utf-8").split("\n")
            window = " ".join(
                lines[max(0, line_no - 1 - MARKER_LOOKBEHIND_LINES):line_no])
            category = re.search(r"category=['\"]([a-z_]+)['\"]", args)
            with self.subTest(site="%s:%d" % (path.name, line_no)):
                self.assertIsNotNone(
                    category,
                    "an exempt reference passes no readable category, so the marker cannot be "
                    "checked against it")
                self.assertIn(
                    category.group(1), window,
                    "the %s marker above %s:%d does not name the `%s` category the reference "
                    "passes. A marker that does not identify its own subject is a generic "
                    "silencer" % (EXEMPTION_MARKER, path.name, line_no, category.group(1)))

    def test_an_exempt_reference_really_carries_no_query(self):
        """A marker on a reference that already has a query is a stale marker."""
        for path, line_no, args, exempt in references():
            if exempt and "query=" in args:
                self.fail(
                    "%s:%d carries the %s marker AND a `query=` argument. The marker is stale — "
                    "remove it, or the next genuinely bare reference beside it inherits an "
                    "exemption nobody reviewed" % (path.name, line_no, EXEMPTION_MARKER))

    def test_every_marker_governs_a_reference(self):
        """A marker with no reference under it is dead text that reads as coverage."""
        for path in shipped_markdown():
            lines = path.read_text(encoding="utf-8").split("\n")
            for i, line in enumerate(lines):
                if EXEMPTION_MARKER not in line:
                    continue
                following = "\n".join(lines[i:i + 1 + MARKER_LOOKBEHIND_LINES])
                with self.subTest(site="%s:%d" % (path.name, i + 1)):
                    self.assertRegex(
                        following, r"search_docs\(",
                        "a %s marker sits above no `search_docs(` reference, so it exempts "
                        "nothing while looking like a reviewed decision" % EXEMPTION_MARKER)


class EveryInstructionCitesTheRetrievalInvariant(unittest.TestCase):
    """INV-212 requires the strategy AT the step; the three instruction sites now say why."""

    def test_each_instruction_site_cites_inv_212(self):
        missing = []
        for path in shipped_markdown():
            text = path.read_text(encoding="utf-8")
            for match in REFERENCE.finditer(text):
                if "query=" not in match.group("args"):
                    continue
                window = flatten(text[max(0, match.start() - 400):match.end() + 700])
                if INSTRUCTION_CUE.search(window) and "INV-212" not in window:
                    line_no = text[:match.start()].count("\n") + 1
                    missing.append("%s:%d" % (path.relative_to(SKILLS), line_no))
        self.assertEqual(
            [], missing,
            "an instruction to call `search_docs` carries no INV-212 citation: %s. Without it "
            "the next editor cannot look up why a bare category is unacceptable, and abbreviates "
            "it again" % missing)

    def test_at_least_one_instruction_site_is_recognized(self):
        """Anti-vacuity for the cue above: if it matches nothing, the check is empty."""
        found = 0
        for path in shipped_markdown():
            text = path.read_text(encoding="utf-8")
            for match in REFERENCE.finditer(text):
                window = flatten(text[max(0, match.start() - 400):match.end() + 700])
                if INSTRUCTION_CUE.search(window):
                    found += 1
        self.assertGreaterEqual(
            found, 3,
            "the instruction cue matches %d references; it was written against three known "
            "instruction sites, so a lower count means the wording moved and this class is "
            "no longer being checked" % found)


class TheRequiredParameterIsStatedWhereItMatters(unittest.TestCase):
    """The recovery-flow site is the one whose second failure costs most."""

    def test_the_recovery_flow_says_query_is_required(self):
        text = (SKILLS / "module-02-sdk-setup" / "SKILL.md").read_text(encoding="utf-8")
        flat = re.sub(r"\s+", " ", text)
        self.assertRegex(
            flat, r"(?i)`query` is `search_docs`' only REQUIRED parameter",
            "the TypeScript recovery flow does not say `query` is required, so an editor "
            "trimming the call has nothing telling them the short form is unexecutable")


if __name__ == "__main__":
    unittest.main()
