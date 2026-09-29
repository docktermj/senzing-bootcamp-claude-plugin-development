"""A reachability probe uses `get_capabilities`, never a content-returning tool.

`onboarding-flow.md` reasoned its way off `search_docs` as a liveness probe and wrote the
reasoning down: the probe's only output is "did the server answer at all", so a document
search pays for a multi-kilobyte retrieval that is then discarded. `get_capabilities` is the
natural probe because `ground-rules.md` → "Session start" already requires it once before any
other Senzing MCP call, so the probe is a call the guide has to make anyway.

Module 3's Step 1 kept the `search_docs` probe for weeks afterwards. Nothing caught it,
because the correction was written in the first person of the file that made it — *"It was
specified **here** as…"* — so it read as a local fix rather than a plugin-wide rule, and no
test knew the rule existed.

That is this plugin's recurring defect shape rather than a one-off: a lesson learned in one
module and never carried across a skill boundary. The 2026-08-12 dry run found **three**
instances in a single walk (this one, `step14-value-proposition-query-is-bm25-hostile-with-no-
fallback`, and `preparation-summarizes-the-model-nudge-trigger-as-the-forbidden-comparison`).
A guard is what converts one module's reasoning into a property of the whole plugin.

Note what this does NOT forbid: `search_docs` itself, which is the right tool wherever content
is actually wanted, and the sentence in `onboarding-flow.md` that names the anti-pattern in
order to ban it.

Enforces **INV-204** (a reachability or liveness probe uses `get_capabilities`, never a
content-returning tool whose retrieval is then discarded), which names this file.

**Widened 2026-09-29 (GitHub issue #235).** The tool list was a hardcoded five, so a probe
through `explain_error_code` or `generate_scaffold` passed. It is now every tool in
`MCP_TOOLS` (`test_mcp_call_contracts.py`, the suite's one copy of the server's tool list)
except `get_capabilities`, so a new server tool is covered as soon as that set is updated.

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

# The suite's one copy of the server's tool list. Imported, never copied: a copy here is the
# hardcoded list this guard used to have. An unreadable MCP_TOOLS is an import error, so the
# guard fails loudly rather than scanning for nothing (INV-265).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_mcp_call_contracts as contracts  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

#: The one probe tool. Every other tool returns content — wasteful as a boolean liveness test.
PROBE_TOOL = "get_capabilities"
CONTENT_TOOLS = tuple(sorted(contracts.MCP_TOOLS - {PROBE_TOOL}))

#: Vocabulary that marks a passage as a reachability test rather than a content lookup.
PROBE_VOCAB = re.compile(
    r"(?i)connectivity check|MCP connectivity|reachability probe|liveness|health check|"
    r"probe with|server (?:is )?(?:reachable|responding)|did the server answer"
)

#: The ban itself has to name the anti-pattern to forbid it — both `onboarding-flow.md`'s
#: "Do **not** probe with `search_docs`" and Module 3's "do not restore a `search_docs` probe".
#: So a negated mention is exempt, and the negation must sit CLOSE to the tool (see
#: PROHIBITION_REACH): searched across the whole 260-char window, any unrelated "do not"
#: elsewhere in the paragraph would exempt a real offense.
PROHIBITION = re.compile(
    r"(?i)(?:do\s+[*_`]{0,2}not[*_`]{0,2}|must\s+[*_`]{0,2}not[*_`]{0,2}|never|avoid)\s+"
    r"(?:probe|use|restore|be|specify)"
)

WINDOW = 260

# ⚠️ Widened from 120 on 2026-08-21, because at 120 this guard FAILED when the rule it protects
# gained the citation INV-183 requires. Adding "(INV-204)" -- ten characters -- pushed the
# `search_docs` mention in the rule's own explanation past the reach, so the prohibition stopped
# being seen and correct, newly-compliant prose was reported as an offense. A guard that
# penalizes satisfying another invariant is measuring distance, not correctness. 200 leaves room
# for a citation and a short clause without reaching into a neighboring paragraph.
PROHIBITION_REACH = 200


def shipped_markdown():
    return sorted(PLUGIN.rglob("*.md"))


def offenses():
    found = []
    tools = re.compile(r"(?i)(%s)" % "|".join(map(re.escape, CONTENT_TOOLS)))
    for path in shipped_markdown():
        flat = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for match in tools.finditer(flat):
            window = flat[max(0, match.start() - WINDOW):match.end() + WINDOW]
            if not PROBE_VOCAB.search(window):
                continue
            near = flat[max(0, match.start() - PROHIBITION_REACH):match.end() + PROHIBITION_REACH]
            if PROHIBITION.search(near):
                continue
            found.append("%s: %s" % (path.relative_to(REPO_ROOT), window[:200]))
    return found


class NoProbeIsADocumentSearch(unittest.TestCase):
    def test_the_tool_list_is_every_server_tool_but_the_probe(self):
        """Derived, not hardcoded: a subset is how `explain_error_code` probes passed."""
        self.assertIn(PROBE_TOOL, contracts.MCP_TOOLS, "MCP_TOOLS lost get_capabilities")
        self.assertEqual(set(CONTENT_TOOLS), contracts.MCP_TOOLS - {PROBE_TOOL})
        self.assertGreater(len(CONTENT_TOOLS), 5, "MCP_TOOLS read as near-empty — scan is vacuous")
        for tool in ("explain_error_code", "generate_scaffold"):
            with self.subTest(tool=tool):
                self.assertIn(tool, CONTENT_TOOLS)

    def test_the_scan_reaches_the_shipped_prose(self):
        files = shipped_markdown()
        self.assertGreater(len(files), 30, "the shipped markdown corpus was not found")
        corpus = " ".join(p.read_text(encoding="utf-8") for p in files)
        self.assertRegex(corpus, PROBE_VOCAB, "no probe vocabulary found — scan is vacuous")

    def test_no_liveness_probe_uses_a_content_returning_tool(self):
        found = offenses()
        self.assertEqual(
            [],
            found,
            "A reachability probe is paired with a content-returning tool. The probe keeps "
            "only 'did the server answer', so the retrieval is discarded — use "
            "get_capabilities, which Session start already requires (see "
            "bootcamp-onboarding/onboarding-flow.md -> MCP health check):\n  "
            + "\n  ".join(found),
        )


class ModuleThreeProbesWithGetCapabilities(unittest.TestCase):
    PHASE1 = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"

    def flat(self):
        return re.sub(r"\s+", " ", self.PHASE1.read_text(encoding="utf-8"))

    def test_step_1_calls_get_capabilities(self):
        self.assertRegex(self.flat(), r"(?i)Call `get_capabilities` with a 10-second timeout")

    def test_the_retry_uses_the_same_call(self):
        """A half-migrated step — probe changed, retry not — would still cost the search."""
        self.assertRegex(self.flat(), r"(?i)retry `get_capabilities` once with the same 10-second")

    def test_the_step_contract_is_unchanged(self):
        """Only the call was meant to change; these are the parts that had to survive."""
        flat = self.flat()
        self.assertIn("MCP connectivity confirmed", flat)
        self.assertRegex(flat, r"(?i)Proceed silently; do not display connectivity status")
        self.assertRegex(flat, r"(?i)Verify DNS resolution")
        self.assertRegex(flat, r"(?i)until the bootcamper says \"retry\"")
        self.assertIn("mcp_connectivity", flat)

    def test_it_cites_the_reasoning_instead_of_restating_it(self):
        self.assertRegex(self.flat(), r"(?i)onboarding-flow\.md")


if __name__ == "__main__":
    unittest.main()
