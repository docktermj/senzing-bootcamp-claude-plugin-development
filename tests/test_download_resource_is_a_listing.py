"""`download_resource` returns a URL listing, and `inline` is permitted for it alone.

MCP-NEGATIVE-SCAN: ignore-file — this file quotes the `MCP-NEGATIVE:` token as a LOCATOR, to
find the declared-schemas marker in `ground-rules.md` and assert its parameter list and stamp.
Those string literals are matchers, not dated claims. The absence claims below (neither
sibling declares `inline`) are the ones that marker already carries, and it is the marker, not
this test, that sits on the re-ask worklist.

Three MCP tools answer a content request with metadata plus a URL rather than the bytes:
`find_examples` file retrieval, `generate_scaffold`, and `download_resource`. Verified on
server 1.32.9, 2026-08-14, `download_resource(filename='senzing_entity_specification.md')`
returns `mode: "url"` with a `size_bytes` figure and no content at all.

What separates the three is the escape hatch, and the rule that decides it is INV-136 —
only parameters the live schema declares may be passed:

* `generate_scaffold` declares `language`, `version`, `workflow`;
* `find_examples` declares `query`, `repo`, `file_path`, `list_files`, `language`,
  `max_lines`;
* `download_resource` declares `inline` among its parameters. The full list moves (it gained
  `offset` by server 1.37.14), so it is read from the sites and the `MCP-NEGATIVE` comment's
  server version and date, never pinned here.

So the two siblings inherit a prohibition and `download_resource` inherits a permission.
Stated per-tool as "never pass `inline`" the rule generalizes wrongly, and a guide that
internalized it that way refuses the one call where `inline` is the documented remedy —
stranding a firewalled bootcamper on the step whose `on_failure` text exists for them.

These tests pin three things: that every `download_resource` call site accounts for the
listing shape, that the permission is scoped to `download_resource` alone, and that the
two sibling prohibitions are untouched.

**The inline reply is chunked (#225).** Re-verified on server 1.37.15, 2026-09-29: an
`inline=true` reply carries a large resource in bounded chunks, each with `truncated`,
`next_offset` and `total_chars`, and a batch lists a file too large for one chunk under
`oversize`. `ChunkedInlineReply` pins the plugin's side of that (INV-219: structure, never the
server's wording): both sites that describe the inline route list `offset` among the declared
parameters and name the three reply fields, or cite the central statement; neither says the
whole resource arrives in one response; the `MCP-NEGATIVE` comment lists `offset` and carries a
server version and date; and Module 5 Step 3, the one step that assembles a file, states the
procedure once, in order, while `ground-rules.md` points at it rather than restating it
(INV-300).

Enforces **INV-234** — the listing shape must be stated at every call site, or cite the one
central statement of it.

Enforces **INV-240** too — a prohibition derived from a general rule must state the general
rule and the property that triggers it, never only the forbidden token. That clause began
inside INV-234 and was split out on maintainer review, because it governs any derived
prohibition rather than this tool family; `ThePermissionIsScopedToOneTool` is the part of
this file that holds the line.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
GROUND_RULES = PLUGIN / "skills" / "bootcamp-onboarding" / "ground-rules.md"
PHASE1 = PLUGIN / "skills" / "module-05-data-quality-mapping" / "phase1-quality-assessment.md"
SCAFFOLD_SITE = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"

#: The one tool whose schema declares `inline`, so the one tool it may be passed to.
INLINE_PERMITTED_FOR = "download_resource"
#: The tools whose schemas do not declare it. Passing it is a call that cannot work.
INLINE_FORBIDDEN_FOR = ("generate_scaffold", "find_examples")

#: An actual call, not a prose mention of the tool's name. `download_resource with this
#: filename` inside the inline-fallback sentence is deliberately not a call site.
CALL = re.compile(r"download_resource\s*\(")
#: How far either side of a call the accountability must appear. A call site is accounted
#: for AT THE SITE — checking the whole file instead let an unrelated OFAC field name
#: ("Listing Date (EO 14024 Directive N)") satisfy the sweep for a stripped call site,
#: which is the assert-a-token-appears-somewhere failure this repo keeps re-learning.
WINDOW = 420
#: Naming the shape: the response is a listing / carries a URL rather than bytes.
NAMES_THE_SHAPE = re.compile(r"(?i)listing|mode:\s*.?url")
#: ...and saying what that means for the caller. Both halves are required, so the word
#: "listing" on its own — in any sense — cannot discharge the obligation.
NAMES_THE_CONSEQUENCE = re.compile(
    r"(?i)not the (?:document|scripts|specification)|no content|second fetch"
    r"|fetch(?:ing)? (?:each|its|the) `?url"
)
#: Or the site simply points at the one place that states it for all three tools.
CITES_CENTRAL = re.compile(r"(?i)ground-rules\.md.{0,40}Working examples")


def accounted_for(window):
    """True when this call site states the listing shape, or cites the central rule."""
    if CITES_CENTRAL.search(window):
        return True
    return bool(NAMES_THE_SHAPE.search(window) and NAMES_THE_CONSEQUENCE.search(window))


def flat(path):
    """Whitespace-collapsed text with blockquote markers stripped."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text)


def shipped_markdown():
    """Every shipped instruction file a call site could sit in."""
    return sorted(p for p in PLUGIN.rglob("*.md") if p.is_file())


def call_sites():
    """[(relpath, window)] for every actual `download_resource(` call in shipped text."""
    sites = []
    for path in shipped_markdown():
        text = flat(path)
        for m in CALL.finditer(text):
            window = text[max(0, m.start() - WINDOW):m.end() + WINDOW]
            sites.append((str(path.relative_to(REPO_ROOT)), window))
    return sites


class EveryCallSiteAccountsForTheListing(unittest.TestCase):
    """Criterion 4 — the sweep. A new call site must not silently read as returning content."""

    def test_the_known_call_sites_are_all_found(self):
        # Pinned so the sweep cannot pass vacuously: if a call site moves or the tool is
        # renamed, this fails rather than the sweep quietly covering nothing. Re-derive by
        # running the extractor, never by editing the number to match. 4 since #225: the
        # chunk-assembly procedure in Module 5 Step 3 calls it with `inline=true`.
        self.assertEqual(4, len(call_sites()), [s[0] for s in call_sites()])

    def test_each_call_site_describes_the_listing_or_cites_the_central_statement(self):
        for rel, window in call_sites():
            with self.subTest(file=rel):
                self.assertTrue(
                    accounted_for(window),
                    "a download_resource( call in %s neither states the URL-listing shape "
                    "(a listing, and what that means for the caller) nor cites "
                    "ground-rules.md -> 'Working examples'" % rel,
                )


class Phase1DescribesTheTwoStepRetrieval(unittest.TestCase):
    """Criteria 1-2 — the step that consumes the specification, stated in full."""

    def test_it_says_the_response_carries_no_content(self):
        self.assertRegex(flat(PHASE1), r"(?i)listing, not the document")

    def test_it_names_mode_url_and_size_bytes(self):
        text = flat(PHASE1)
        self.assertIn("`mode: \"url\"`", text)
        self.assertIn("size_bytes", text)

    def test_it_requires_the_saved_size_to_be_checked(self):
        # The check, not merely the number: a step that prints a size without comparing
        # it has the fact and not the gate.
        self.assertRegex(
            flat(PHASE1),
            r"(?i)check the saved file's size against the response's `size_bytes`",
        )

    def test_it_compares_with_this_response_and_pins_no_size(self):
        """Rescoped by #225 from `test_it_states_the_size_that_was_measured`.

        That test asserted the byte count measured on 2026-08-14. By server 1.37.14 the file
        had grown past it, so the test was guarding a stale MCP-content figure, which
        INV-219 forbids a test to pin and INV-080 forbids shipped prose to carry. What it was
        really for is that the check compares against a real figure; that figure is the one in
        the response, so this asserts the step says so and writes no byte count of its own.
        """
        text = flat(PHASE1)
        self.assertRegex(text, r"(?i)figure in \*\*this\*\* response")
        self.assertNotRegex(text, r"\b\d{1,3}(?:,\d{3})+ bytes\b|\b\d+\s*KB\b")

    def test_it_names_inline_true_as_the_fallback_with_its_reason_and_cost(self):
        text = flat(PHASE1)
        self.assertRegex(text, r"(?i)`inline=true` is the sanctioned fallback")
        self.assertIn("INV-136", text)
        self.assertRegex(text, r"(?i)cost context")

    def test_the_fetch_is_not_hard_coded_to_curl(self):
        # INV-001/INV-002: the fetch belongs to the bootcamper's language and must run on
        # all three platforms, so a bare curl recipe here would be a violation.
        text = flat(PHASE1)
        self.assertRegex(text, r"(?i)not a hard-coded `curl`")


class TheCentralStatementIsPhrasedAsTheSchemaRule(unittest.TestCase):
    """Criterion 3 — stated once, as INV-136's consequence rather than a banned word."""

    def test_ground_rules_names_all_three_tools_together(self):
        text = flat(GROUND_RULES)
        for tool in INLINE_FORBIDDEN_FOR + (INLINE_PERMITTED_FOR,):
            with self.subTest(tool=tool):
                self.assertIn(tool, text)

    def test_it_cites_inv136_as_the_governing_rule(self):
        self.assertIn("INV-136", flat(GROUND_RULES))

    def test_it_warns_against_reading_the_rule_as_a_ban_on_the_word(self):
        self.assertRegex(
            flat(GROUND_RULES), r"(?i)never as a ban on the word `inline`"
        )

    def test_it_says_the_content_is_a_second_fetch(self):
        self.assertRegex(flat(GROUND_RULES), r"(?i)second\*{0,2} fetch")


class ThePermissionIsScopedToOneTool(unittest.TestCase):
    """Criterion 5 — negative-controlled by widening the permission to all three."""

    def test_download_resource_is_the_only_tool_inline_is_permitted_for(self):
        # Every shipped sentence that permits `inline` must be about download_resource.
        # Widening the permission to a sibling is the mutation this catches.
        for path in shipped_markdown():
            text = flat(path)
            for m in re.finditer(
                r"[^.]*\b(?:permit(?:s|ted)?|sanctioned|allowed|is declared)\b[^.]*"
                r"`?inline`?[^.]*\.",
                text,
            ):
                sentence = m.group(0)
                with self.subTest(file=str(path.relative_to(REPO_ROOT)),
                                  sentence=sentence[:90]):
                    for tool in INLINE_FORBIDDEN_FOR:
                        self.assertNotIn(
                            tool, sentence,
                            "a sentence permitting `inline` names %s, whose schema does "
                            "not declare it" % tool,
                        )

    def test_the_generate_scaffold_prohibition_is_unchanged(self):
        text = flat(SCAFFOLD_SITE)
        self.assertRegex(text, r"Never pass `inline=true` to `generate_scaffold`")
        self.assertRegex(text, r"(?i)declared schema has no `inline` parameter at all")

    def test_the_find_examples_prohibition_is_unchanged(self):
        self.assertRegex(
            flat(GROUND_RULES),
            r"(?i)Do not take the `inline` route the response's step 3 describes",
        )
        self.assertRegex(
            flat(GROUND_RULES),
            r"(?i)`inline` is still not\s+declared in the live `find_examples` schema",
        )


#: A sentence naming `download_resource`'s declared parameters: it says "declared" and lists
#: `filenames`, which only that tool has.
DECLARED_LIST = re.compile(r"[^.]*\bdeclared\b[^.]*`filenames`[^.]*\.|[^.]*`filenames`[^.]*\bdeclared\b[^.]*\.")
#: The three fields of a truncated inline reply.
REPLY_FIELDS = ("`truncated", "`next_offset`", "`total_chars`")
#: The claim #225 retired: the whole resource arriving in one response.
WHOLE_IN_ONE = re.compile(
    r"(?i)(?:whole|full|entire)\b[^.]{0,40}\b(?:arrives?|comes? back|is returned)\b[^.]{0,20}"
    r"\b(?:inside|in) (?:the|one|a single) (?:response|reply)")
#: The central statement, cited by name.
CITES_INV234 = re.compile(r"INV-234")
#: Module 5 Step 3's assembly procedure: from its ⛔ heading to the next paragraph that is
#: not a numbered step.
PROCEDURE = re.compile(
    r"⛔ \*\*\(INV-234\) The inline reply carries the file in bounded chunks.*?(?=\n\n(?!\d\. |   ))",
    re.S)


def inline_sites():
    """The two places that describe the inline route: the central bullet and Module 5."""
    return {"ground-rules.md": GROUND_RULES, "phase1-quality-assessment.md": PHASE1}


def procedure_text():
    m = PROCEDURE.search(PHASE1.read_text(encoding="utf-8"))
    return re.sub(r"\s+", " ", m.group(0)) if m else ""


class ChunkedInlineReply(unittest.TestCase):
    """#225 — the inline route as the live schema serves it, and one statement of assembly."""

    def test_each_site_lists_offset_among_the_declared_parameters(self):
        for name, path in inline_sites().items():
            with self.subTest(site=name):
                lists = [m.group(0) for m in DECLARED_LIST.finditer(flat(path))
                         if "`inline`" in m.group(0)]
                self.assertTrue(lists, "%s names no declared-parameter list" % name)
                self.assertTrue(any("`offset`" in l for l in lists),
                                "%s lists the declared parameters without `offset`" % name)

    def test_each_site_describes_the_chunked_reply(self):
        for name, path in inline_sites().items():
            text = flat(path)
            with self.subTest(site=name):
                self.assertTrue(
                    all(f in text for f in REPLY_FIELDS) or (
                        CITES_INV234.search(text) and CITES_CENTRAL.search(text)),
                    "%s neither names %s nor cites the central statement" % (name, REPLY_FIELDS))
                self.assertIn("`offset`", text)

    def test_no_site_says_the_whole_resource_arrives_in_one_response(self):
        for path in shipped_markdown():
            with self.subTest(file=str(path.relative_to(REPO_ROOT))):
                self.assertNotRegex(flat(path), WHOLE_IN_ONE)

    def test_the_central_statement_names_the_batch_oversize_rule(self):
        text = flat(GROUND_RULES)
        self.assertIn("`oversize`", text)
        self.assertRegex(text, r"(?i)on its own, with `filename`")

    def test_the_mcp_negative_comment_lists_offset_and_is_dated(self):
        comment = re.search(r"<!-- MCP-NEGATIVE: the declared schemas of find_examples.*?-->",
                            GROUND_RULES.read_text(encoding="utf-8"), re.S)
        self.assertIsNotNone(comment, "the declared-schemas MCP-NEGATIVE comment is gone")
        m = re.search(r"download_resource's schema \(([^)]*)\)", comment.group(0))
        self.assertIsNotNone(m, "the comment must give download_resource's parameters in parentheses")
        self.assertIn("offset", m.group(1))
        self.assertIn("inline", m.group(1))
        self.assertRegex(comment.group(0), r"server \d+\.\d+\.\d+, \d{4}-\d{2}-\d{2} -->$")

    def test_module5_states_the_assembly_procedure_in_order(self):
        text = procedure_text()
        self.assertTrue(text, "Module 5 Step 3 has no INV-234 chunk-assembly procedure")
        steps = [
            ("the inline call", r"download_resource\(filename=[^)]*inline=true\)"),
            ("the canonical path", r"docs/reference/senzing_entity_specification\.md"),
            ("the loop on next_offset", r"`offset` set to its `next_offset`"),
            ("append, in order", r"(?i)\*\*append\*\*[^.]*in order"),
            ("the stop condition", r"`truncated: false`"),
            ("the total_chars check", r"(?i)check the assembled file against `total_chars`"),
        ]
        at = -1
        for label, pattern in steps:
            with self.subTest(step=label):
                m = re.compile(pattern).search(text, at + 1)
                self.assertIsNotNone(m, "the procedure lacks %s after the step before it" % label)
                at = m.start()

    def test_module5_says_to_ignore_the_suggested_dest(self):
        text = procedure_text()
        self.assertRegex(text, r"(?i)ignore the reply's `dest`")
        self.assertIn("INV-001", text)

    def test_the_url_route_keeps_its_size_bytes_check(self):
        text = flat(PHASE1)
        self.assertRegex(text, r"(?i)check the saved file's size against the response's `size_bytes`")
        self.assertRegex(procedure_text(), r"counterpart of the `size_bytes` check")

    def test_module5_names_search_docs_as_the_cheaper_single_lookup(self):
        self.assertRegex(flat(PHASE1), r"(?i)single lookup, `search_docs` is cheaper than paging")

    def test_the_procedure_is_stated_once(self):
        # INV-300: ground-rules states the reply shape and points at Module 5; it must not
        # grow a second copy of the assembly steps that could drift from the first.
        central = flat(GROUND_RULES)
        self.assertRegex(central, r"Module 5 Phase 1 Step 3 is the one step")
        self.assertNotRegex(central, r"(?i)\bappend\b[^.]{0,80}\bchunk|ignore the reply's `dest`")
        for path in shipped_markdown():
            if path == PHASE1:
                continue
            with self.subTest(file=str(path.relative_to(REPO_ROOT))):
                self.assertNotRegex(flat(path), r"(?i)check the assembled file against `total_chars`")


if __name__ == "__main__":
    unittest.main()
