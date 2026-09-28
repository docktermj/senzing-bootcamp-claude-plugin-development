"""The plugin never tells the guide to withhold an MCP tool's output.

Twice now the plugin has carried a *negative* claim about a tool's content — "this tool
does not cover X" — routed around the tool on that basis, and written the routing down
with a date and a version so it read as verified. Both times the server later gained the
coverage and nothing re-asked, because a negative about a tool's content cannot go stale
detectably without calling the tool, which INV-108 forbids the suite from doing:

- `senz7221-now-names-its-own-remedy` (2026-07-30) — the plugin said the explanation named
  no remedy; the server had gained one.
- `explain-error-code-now-owns-senz7426` (2026-08-12) — the plugin instructed the guide to
  **not relay** `explain_error_code('SENZ7426')`, whose output by then ranked SUPPORTPATH
  as `common_causes[0]` and "Check SUPPORTPATH FIRST" as `resolution_steps[0]`. Module 3
  Step 3b was discarding the answer that would have fixed the Bootcamper.

The underlying fact needs the network. The *instruction* does not, and it is the durable
form of the defect: whatever a tool returns today, telling the guide to suppress it is a
bet that the tool will never improve. Relay it and add what is missing — the plugin's own
corroboration, a platform condition, a pointer to the tool that owns the detail — rather
than withholding what came back.

This guard does not forbid *qualifying* a tool's output. Saying a cause is ranked last, or
conditioned, or corroborated elsewhere, is analysis. Telling the guide not to pass it on is
suppression.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"

#: Every MCP tool whose output the guide is ever told to present.
MCP_TOOLS = (
    "explain_error_code",
    "search_docs",
    "sdk_guide",
    "get_sdk_reference",
    "reporting_guide",
    "generate_scaffold",
    "get_sample_data",
    "find_examples",
    "mapping_workflow",
    "analyze_record",
    "get_capabilities",
    "download_resource",
    "submit_feedback",
)

#: Emphasis is part of the shipped wording, not noise around it: the instruction this guard
#: exists to catch was written `do **not** relay`, so a bare `do\s+not` would have missed the
#: only real instance the plugin ever had. Mutation-tested against that exact sentence.
_EMPH = r"[*_`]{0,2}"
#: Verbs that mean "keep this from the Bootcamper", as opposed to qualifying or ranking it.
_SUPPRESS = r"(?:relay|present|show|surface|repeat|quote|pass\s+on)"
_NEGATION = r"(?:do\s+%snot%s|don'?t|never)" % (_EMPH, _EMPH)

#: The trigger alone is not an offense. Bare "withhold"/"suppress" also describe what the
#: SERVER does — ground-rules.md notes most `reporting_guide` topics "withhold their content"
#: without `language`, and phaseD-validation.md says Senzing "suppresses legitimate" matches —
#: so an offense additionally requires the tool's OUTPUT as the object (below).
TRIGGER = re.compile(r"(?i)(?:%s\s+%s%s%s|withhold|suppress)" % (_NEGATION, _EMPH, _SUPPRESS, _EMPH))

#: A tool name followed closely by the thing it produced. Proximity, never `[^.]`-bounded:
#: shipped provenance is full of periods ("server 1.32.9, 2026-08-12"), and an earlier
#: sentence-bounded version of this guard silently passed its own mutation test because a
#: version stamp between the tool and the claim ended the "sentence".
TOOL_OUTPUT = re.compile(
    r"(?i)(?:%s)%s(?:\([^)]{0,40}\))?%s.{0,40}?"
    r"(?:returned|returns|output|result|response|explanation|causes)"
    % ("|".join(MCP_TOOLS), _EMPH, _EMPH)
)

#: How far past the trigger the object may sit and still be its object.
REACH = 90


#: A corroboration requirement is the OPPOSITE of suppression and must not be flagged.
#: `concepts.md` says "do not present the first `search_docs` result as-is: make a second,
#: confirming MCP call … and present it only once corroborated" — that withholds nothing, it
#: raises the evidence bar before presenting. Distinguishing the two is the whole subtlety
#: here: both sentences start "do not present".
CORROBORATION = re.compile(r"(?i)as-is|corroborat|confirming|cross-check|second[, ]|only once")


def shipped_markdown():
    return sorted(PLUGIN.rglob("*.md"))


def offenses():
    found = []
    for path in shipped_markdown():
        flat = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for match in TRIGGER.finditer(flat):
            tail = flat[match.end():match.end() + REACH]
            if not TOOL_OUTPUT.search(tail):
                continue
            window = flat[max(0, match.start() - 120):match.end() + REACH]
            if CORROBORATION.search(window):
                continue
            found.append((path.relative_to(REPO_ROOT), window[-200:]))
    return found


class NoShippedFileSuppressesToolOutput(unittest.TestCase):
    def test_the_scan_reaches_the_shipped_prose(self):
        """A vacuous pass would make the rest of this file meaningless."""
        files = shipped_markdown()
        self.assertGreater(len(files), 30, "the shipped markdown corpus was not found")
        corpus = " ".join(p.read_text(encoding="utf-8") for p in files)
        self.assertIn("explain_error_code", corpus)

    def test_no_file_tells_the_guide_to_withhold_a_tools_output(self):
        found = offenses()
        self.assertEqual(
            [],
            ["%s: %s" % (path, text) for path, text in found],
            "A shipped file instructs the guide to withhold an MCP tool's output. That is a "
            "bet that the tool will never improve, and it has lost twice "
            "(senz7221-now-names-its-own-remedy, explain-error-code-now-owns-senz7426). "
            "Relay what the tool returns and qualify it — rank a cause, name a condition, "
            "corroborate it, point at the tool that owns the detail — instead of "
            "suppressing it (INV-080).",
        )


class TheRetiredSenz7426ClaimIsGone(unittest.TestCase):
    """The specific sentences that made this class visible, pinned so they stay retired."""

    #: The denial the plugin carried for two weeks, in the forms it was written in.
    DENIAL = re.compile(
        r"(?i)only generic|makes no connection|names no connection|no connection to"
    )

    def test_no_file_says_explain_error_code_makes_no_supportpath_connection(self):
        offenders = []
        for path in shipped_markdown():
            flat = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            for match in self.DENIAL.finditer(flat):
                window = flat[max(0, match.start() - 250):match.end() + 250]
                if "explain_error_code" in window:
                    offenders.append("%s: %s" % (path.relative_to(REPO_ROOT), window[:200]))
        self.assertEqual(
            [],
            offenders,
            "The retired claim is restated. As of server 1.32.9 (2026-08-12) "
            "explain_error_code('7426') ranks SUPPORTPATH as common_causes[0] and 'Check "
            "SUPPORTPATH FIRST' as resolution_steps[0]:\n  " + "\n  ".join(offenders),
        )

    def test_module_03_now_relays_the_tools_output(self):
        """The relay instruction rests on a dated re-verification, now held by its owner.

        This asserted `"1.32.9" in` Module 3, because step 3b carried its own stamp for the
        re-verification that made relaying safe. #219 removed that copy: step 3b is an
        INV-300 pointer to Module 2 Step 8's two-tool block, and the stamp lives there. Left
        as it was, the assertion passed on an unrelated 1.32.9 elsewhere in the file (the
        Step 4 scaffold count), which is no check at all. So it follows the stamp: Module 3
        must route to the owning block, and that block must carry a server version and date
        for its `explain_error_code('7426')` reading.
        """
        phase1 = PLUGIN / "skills" / "module-03-system-verification" / "phase1-verification.md"
        module_02 = PLUGIN / "skills" / "module-02-sdk-setup" / "SKILL.md"
        flat = re.sub(r"\s+", " ", phase1.read_text(encoding="utf-8"))
        self.assertRegex(flat, r"(?i)relay what `explain_error_code` returned")
        owner = "Both tools agree on the diagnosis and the fix — not on the macOS literal"
        self.assertRegex(
            flat, r"If the code is `SENZ7426`.{0,400}" + re.escape(owner),
            "Module 3's SENZ7426 relay no longer names the Module 2 block that dates it",
        )
        owner_text = re.sub(
            r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", module_02.read_text(encoding="utf-8"))
        )
        self.assertRegex(
            owner_text,
            re.escape(owner) + r"\*\* \(INV-169\) — re-verified on \*\*MCP server "
            r"\d+\.\d+\.\d+, \d{4}-\d{2}-\d{2}\*\*\. `explain_error_code\('7426'\)`",
            "the owning block no longer dates its explain_error_code('7426') reading",
        )


if __name__ == "__main__":
    unittest.main()
