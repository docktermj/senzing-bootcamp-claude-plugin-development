"""A dated "this MCP tool does not contain X" claim carries a marker, so it can be re-asked.

MCP-NEGATIVE-SCAN: ignore-file — this file quotes the marker format and historical claims
as fixtures; none of them is a live assertion about the current server.

The plugin has twice recorded a negative about a tool's content, routed around the tool on
that basis, dated the claim honestly, and then been overtaken when the server gained the
coverage: `senz7221-now-names-its-own-remedy` (2026-07-30) and
`explain-error-code-now-owns-senz7426` (2026-08-12).

A negative is the one claim shape that cannot go stale **detectably** offline. INV-108 keeps
the suite off the network — rightly — so no test can notice that `explain_error_code('7426')`
started naming SUPPORTPATH. `tests/test_deferral_freshness.py` solves the same "the note
outlived the condition" problem for porting deferrals, but only because a deferral is
self-invalidating evidence: it names a path that should not resolve, which a filesystem check
settles. A Senzing negative has no offline equivalent, so the remedy is a *worklist* for the
runs that are already online, not a test pretending to check it.

The second instance is why this also polices **assertions**. Three guards in
`test_engine_verification_and_senz2027.py` encoded the stale claim — one asserted module 2
*must* say `explain_error_code` "makes no connection", another asserted Module 3 *must* say
"do not relay" — so the suite stayed green while enforcing a false statement, and correcting
the prose failed the suite with messages telling the fixer the opposite of what the server
says. A guard that pins a retraction outlives the retraction, and it is consulted precisely
by the person trying to fix the claim.

Prefer asserting what IS true ("module 2 names the tool that states the link") over what must
not be said ("module 2 must say the other tool does not"): the second form is the one that
goes stale.

No phrase-level pattern (#438): its line reads are of test files' assertion lines, which are Python
source, as #424 recorded (INV-346).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import io
import contextlib
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS = REPO_ROOT / "tests"
REPORTS = REPO_ROOT / ".claude" / "skills" / "dry-run" / "coverage_reports.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reports = load(REPORTS, "coverage_reports_negatives")

MCP_TOOLS = (
    "explain_error_code", "search_docs", "sdk_guide", "get_sdk_reference", "reporting_guide",
    "generate_scaffold", "get_sample_data", "find_examples", "mapping_workflow",
    "analyze_record", "get_capabilities", "download_resource", "submit_feedback",
)

#: Phrasings that assert a tool LACKS something. Deliberately narrow: this runs against
#: assertion lines only, where a false positive is a real cost.
NEGATIVE_VOCAB = re.compile(
    r"(?i)makes no\b|no connection|only generic|not relay|returns only|carries no|"
    r"does not (?:carry|return|name|list|include|cover|mention)"
)
TOOL_RE = re.compile(r"(?i)(%s)" % "|".join(MCP_TOOLS))


def _diagnose_malformed(rows):
    """Name the likely cause per malformed marker, rather than guessing one for all.

    The message this feeds used to read "almost always a missing `owner:` clause". It is not:
    a marker **wrapped across lines** fails identically, because `coverage_reports.py`'s
    `MCP_NEGATIVE` regex is not `re.DOTALL` and so cannot match past the newline. On
    2026-08-13 two wrapped markers were written in good faith, both fell off the worklist, and
    this assertion blamed the owner clause — which was present and correct. The two causes need
    different fixes, and the offending line already carries enough to tell them apart.
    """
    if not rows:
        return ""
    out = []
    for relpath, lineno, line in rows:
        if "owner:" not in line:
            cause = ("the line has no `owner:` clause. Either it is missing — add it, naming "
                     "the route that would CARRY the fact (INV-209) — or the marker is "
                     "WRAPPED across lines and the clause is on a continuation line. "
                     "⛔ A marker MUST be written on ONE line: the scanner's regex is not "
                     "re.DOTALL, so a wrapped marker cannot match at any length.")
        elif "server" not in line:
            cause = ("the `owner:` clause is present but the `— server <version>, "
                     "<YYYY-MM-DD>` tail is not on this line. Put the whole marker on one "
                     "line; the regex cannot match across a newline.")
        else:
            cause = ("all field names are on the line, so the order or the separators are "
                     "wrong. The form is exactly: `MCP-NEGATIVE: <tool(params)> — <what is "
                     "absent> — owner: <route + outcome> — server <version>, <YYYY-MM-DD>`, "
                     "with em dashes between fields.")
        out.append("  %s:%d — %s" % (relpath, lineno, cause))
    return "\n".join(out)


def assertion_lines(path):
    """(lineno, line) for each line that performs an assertion."""
    for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if re.search(r"\bself\.assert\w+\(", line):
            yield n, line


def unmarked_negative_assertions():
    found = []
    for path in sorted(TESTS.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if reports.NEGATIVE_OPT_OUT in text:
            continue
        has_marker = reports.MCP_NEGATIVE.search(text) is not None
        for lineno, line in assertion_lines(path):
            if not (TOOL_RE.search(line) and NEGATIVE_VOCAB.search(line)):
                continue
            if has_marker:
                continue
            found.append("%s:%d: %s" % (path.name, lineno, line.strip()[:120]))
    return found


class TheReportFindsTheLiveMarkers(unittest.TestCase):
    """A report that silently finds nothing is worse than no report."""

    def test_the_scan_is_not_vacuous(self):
        found = reports.find_negatives(str(REPO_ROOT))
        self.assertGreaterEqual(
            len(found), 1,
            "no MCP-NEGATIVE markers found anywhere. Either every dated negative was "
            "retired — check before believing that — or the markers were dropped, in "
            "which case the worklist is silently empty",
        )

    def test_each_marker_parses_into_all_five_fields(self):
        for row in reports.find_negatives(str(REPO_ROOT)):
            key, version, date, claim, owner, relpath, lineno = row
            with self.subTest(where="%s:%d" % (relpath, lineno)):
                self.assertTrue(key, "version did not parse into sortable parts")
                self.assertRegex(version, r"^\d+\.\d+")
                self.assertRegex(date, r"^\d{4}-\d{2}-\d{2}$")
                self.assertIn("—", claim, "a claim names the tool and what is absent")
                self.assertTrue(owner, "the owner clause parsed empty")

    def test_every_marker_names_the_route_that_owns_the_fact(self):
        """INV-209. The empty call proves a fact about that call, not the negative.

        A negative recorded from a tool that never carried the fact looks identical in the
        file to a verified one: real tool, real parameters, real empty result, honest date.
        The `owner:` clause is what distinguishes them, so it must name a route — a tool call
        or an equivalently concrete source such as a validator's rejection — and not merely
        restate the absence.

        The regex makes a marker without the clause fail to parse at all, so this test also
        depends on `test_the_scan_is_not_vacuous`: were the clause dropped everywhere, the
        worklist would empty rather than fail here, and that test is what catches it.
        """
        found = reports.find_negatives(str(REPO_ROOT))
        self.assertGreaterEqual(len(found), 1, "no markers to check — see the vacuity test")
        malformed = reports.find_malformed_negatives(str(REPO_ROOT))
        self.assertEqual(
            [], malformed,
            "an `MCP-NEGATIVE:` marker is present but does not parse. This is worse than a "
            "missing marker: the claim still ships and still routes the plugin, but it has "
            "dropped off the re-check worklist, which is the invisibility the convention "
            "exists to prevent.\n%s" % _diagnose_malformed(malformed),
        )
        for row in found:
            _key, _version, _date, _claim, owner, relpath, lineno = row
            with self.subTest(where="%s:%d" % (relpath, lineno)):
                names_a_route = (
                    TOOL_RE.search(owner)
                    or re.search(r"(?i)validator|rejection|error|response", owner)
                )
                self.assertTrue(
                    names_a_route,
                    "the owner clause must name the route that would CARRY this fact — an "
                    "MCP tool, or a concrete source such as a validator's rejection. Got: "
                    "%r. Without it the marker records only that some call came back empty, "
                    "which is how a wrong-route negative reaches an invariant looking "
                    "reviewed (INV-194)." % owner,
                )
                self.assertNotEqual(
                    owner.strip().rstrip("."), "",
                    "owner clause is present but empty",
                )

    def test_the_pattern_itself_rejects_a_marker_with_no_owner_clause(self):
        """Unit-test the regex, not the repo's current contents.

        Asserting `find_malformed_negatives(REPO) == []` is satisfied by a repo whose markers
        all happen to be well-formed — so it cannot notice the pattern being loosened. Caught
        by negative control: making `owner:` optional in `MCP_NEGATIVE` left the suite green,
        because nothing in the tree was missing its clause at the time. The next marker
        written would then slip through silently.
        """
        stamp = "— server 1.32.9, 2026-08-13"
        well_formed = ("MCP-NEGATIVE: sdk_guide(topic='install') — returns no language list "
                       "— owner: get_capabilities carries it " + stamp)
        clauseless = "MCP-NEGATIVE: sdk_guide(topic='install') — returns no language list " + stamp
        self.assertIsNotNone(
            reports.MCP_NEGATIVE.search(well_formed),
            "the pattern must still accept a well-formed marker (positive control)",
        )
        self.assertIsNone(
            reports.MCP_NEGATIVE.search(clauseless),
            "the pattern must REJECT a marker with no `owner:` clause. If it matches, a "
            "clauseless marker is accepted as well-formed and the ownership evidence INV-209 "
            "requires is never recorded.",
        )

    def test_the_malformed_detector_actually_detects(self):
        """A detector that always returns [] satisfies the no-malformed assertion trivially.

        Caught by negative control: stubbing `find_malformed_negatives` to `return []` left
        the suite green, because the only other check on it compares against the live repo,
        where the correct answer *is* empty. So exercise it against a scratch tree.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs").mkdir()                    # find_* expects a repo shape
            (root / "plugins").mkdir()
            stamp = "— server 1.32.9, 2026-08-13"
            (root / "plugins" / "bad.md").write_text(
                "MCP-NEGATIVE: sdk_guide(topic='install') — returns no language list " + stamp,
                encoding="utf-8",
            )
            (root / "plugins" / "good.md").write_text(
                "MCP-NEGATIVE: sdk_guide(topic='install') — returns no language list "
                "— owner: get_capabilities carries it " + stamp,
                encoding="utf-8",
            )
            malformed = reports.find_malformed_negatives(str(root))
            parsed = reports.find_negatives(str(root))
            self.assertEqual(
                ["bad.md"], [Path(r[0]).name for r in malformed],
                "the clauseless marker must be reported as malformed; got %r" % (malformed,),
            )
            self.assertEqual(
                ["good.md"], [Path(r[5]).name for r in parsed],
                "only the well-formed marker belongs on the worklist; got %r" % (parsed,),
            )

    def test_a_wrapped_marker_is_reported_and_diagnosed_as_a_wrap(self):
        """The failure message must name the cause it actually is.

        A wrapped marker and a clauseless one fail identically — `MCP_NEGATIVE` is not
        `re.DOTALL`, so it cannot match past a newline — and the assertion used to blame the
        `owner:` clause for both. Two wrapped markers were written that way on 2026-08-13 with
        the clause present and correct, and the message sent the author to the wrong field.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs").mkdir()
            (root / "plugins").mkdir()
            (root / "plugins" / "wrapped.md").write_text(
                "<!-- MCP-NEGATIVE: sdk_guide(topic='install') —\n"
                "     returns no language list — owner: get_capabilities carries it\n"
                "     — server 1.32.9, 2026-08-13 -->\n",
                encoding="utf-8",
            )
            malformed = reports.find_malformed_negatives(str(root))
            self.assertEqual(
                ["wrapped.md"], [Path(r[0]).name for r in malformed],
                "a marker wrapped across lines must be reported as malformed, not skipped — "
                "otherwise it drops off the worklist with nothing saying so; got %r"
                % (malformed,),
            )
            self.assertEqual(
                [], reports.find_negatives(str(root)),
                "a wrapped marker must NOT be counted as a live marker",
            )
            diagnosis = _diagnose_malformed(malformed)
            self.assertIn("ONE line", diagnosis,
                          "the diagnosis must name the wrap; got %r" % diagnosis)
            self.assertIn("re.DOTALL", diagnosis,
                          "the diagnosis must say WHY one line is required, or the next author "
                          "reformats for readability and breaks it again")

    def test_the_diagnosis_distinguishes_a_clauseless_marker_from_a_wrap(self):
        """Same output for both causes would be no better than the guess it replaced."""
        stamp = "— server 1.32.9, 2026-08-13"
        clauseless = [("f.md", 1, "MCP-NEGATIVE: sdk_guide(topic='install') — no list " + stamp)]
        misordered = [("f.md", 1, "MCP-NEGATIVE: sdk_guide(topic='install') — no list "
                                  "— owner: get_capabilities carries it — server 1.32.9 BAD")]
        self.assertIn("no `owner:` clause", _diagnose_malformed(clauseless))
        self.assertIn("order or the separators", _diagnose_malformed(misordered))
        self.assertEqual("", _diagnose_malformed([]),
                         "no malformed markers must produce no diagnosis noise")

    def test_markers_are_ordered_oldest_server_first(self):
        """The oldest is the one most likely to have moved — it must lead the worklist."""
        keys = [row[0] for row in reports.find_negatives(str(REPO_ROOT))]
        self.assertEqual(sorted(keys), keys)

    def test_the_report_runs_and_names_its_findings(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            reports.report_negatives(str(REPO_ROOT))
        out = buf.getvalue()
        self.assertIn("oldest server version first", out)
        self.assertIn("INV-108", out)
        # The report must also tell the reader to re-ask the OWNER, not just the empty route.
        self.assertIn("owner", out.lower())
        self.assertIn("INV-194", out)
        for row in reports.find_negatives(str(REPO_ROOT)):
            relpath, owner = row[5], row[4]
            self.assertIn(Path(relpath).name, out)
            self.assertIn(owner, out, "each marker's owner clause must be printed")

    def test_the_cli_accepts_the_new_report(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = reports.main(["negatives", "--repo", str(REPO_ROOT)])
        self.assertEqual(0, rc, "reports inform an audit; they never gate it")
        self.assertIn("Dated MCP negatives", buf.getvalue())

    def test_both_still_runs_all_three(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = reports.main(["both", "--repo", str(REPO_ROOT)])
        out = buf.getvalue()
        self.assertEqual(0, rc)
        self.assertIn("Invariants cited by no test file", out)
        self.assertIn("Predicted-but-unrecorded files", out)
        self.assertIn("Dated MCP negatives", out)


class NoTestAssertsAnUnmarkedNegative(unittest.TestCase):
    def test_no_assertion_encodes_a_dated_tool_content_negative_without_a_marker(self):
        found = unmarked_negative_assertions()
        self.assertEqual(
            [],
            found,
            "A test assertion encodes a claim that an MCP tool LACKS something, in a file "
            "carrying no MCP-NEGATIVE marker. That claim cannot be re-checked offline, and "
            "when the server gains the coverage this guard will enforce a false statement "
            "— which has happened twice. Add a marker so "
            "`coverage_reports.py negatives` lists it, or rewrite the assertion to state "
            "what IS true:\n  " + "\n  ".join(found),
        )

    def test_the_detector_recognizes_the_historical_offenders(self):
        """Pinned so the detector cannot be quietly narrowed into uselessness."""
        for line in (
            '        self.assertRegex(text, r"(?i)explain_error_code\\(\'SENZ7426\'\\)'
            '[^.]{0,200}(?:generic|no connection|makes no)")',
            '        self.assertRegex(flat(PHASE1), r"(?i)not relay what `explain_error_code`")',
        ):
            with self.subTest(line=line[:60]):
                self.assertTrue(TOOL_RE.search(line), "tool name not detected")
                self.assertTrue(NEGATIVE_VOCAB.search(line), "negative phrasing not detected")

    def test_the_detector_ignores_a_positive_assertion(self):
        """Asserting what IS true is the form this spec asks for; it must not be flagged."""
        line = '        self.assertRegex(text, r"(?i)relay what `explain_error_code` returned")'
        self.assertTrue(TOOL_RE.search(line))
        self.assertIsNone(NEGATIVE_VOCAB.search(line))


if __name__ == "__main__":
    unittest.main()
