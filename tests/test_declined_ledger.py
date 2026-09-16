"""`specs/DECLINED.md` is the second terminal state a spec can reach, and it must stay honest.

MCP-NEGATIVE-SCAN: ignore-file — this file quotes the marker format and one retracted
historical claim as fixtures for its own detector; none of them is a live assertion about the
current server.

A spec used to have exactly one ending: implemented. `implement-spec` computed
``Unimplemented = candidates - implemented``, so a spec the maintainer ruled out stayed in the
candidate set permanently — re-offered every run, with the spec's own text arguing *for* the change
and nothing recording the argument against it. The first case was
`no-route-for-bootcampers-who-cannot-add-an-mcp-server`, declined 2026-07-31 as an architectural
decision.

The design precedent is `delegate-to-mcp-server`'s `keep-by-design` verdict, which requires a reason
for a stated cause: *"An unreasoned keep is indistinguishable from 'nobody looked', and the next run
will look again."* These tests enforce the same discipline here, plus the two integrity properties a
second ledger introduces — no spec in both, and no entry naming a file that does not exist.

⚠️ Every `##` heading in `DECLINED.md` is read as a spec name, which is why its prose uses bold
rather than headings. `test_no_declined_name_is_prose` is what catches a regression: a `## Why …`
section added to the header was counted as a declined spec the first time this ran.

⛔ And an absence claim here names the route that owns the fact (INV-194), because this file is
the one Senzing record with no re-verification path: a declined spec is never implemented, so
`implement-spec` Step 3.3 never re-asks its facts, while the skill positions this file as the
*higher* authority over the spec's own citations. `AnAbsenceClaimNamesItsOwningRoute` is the
guard. It exists because the 2026-08-13 revisit note on
`no-route-for-bootcampers-who-cannot-add-an-mcp-server` concluded that `sz-mcp-coworker` had
lost its citations by asking a tool description and the tool manifest — neither of which would
carry an install or invocation fact — when the binary was that manifest's own `server_name`.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS = REPO_ROOT / "specs"
DECLINED = SPECS / "DECLINED.md"
IMPLEMENTED = SPECS / "IMPLEMENTED.md"
SKILL = REPO_ROOT / ".claude" / "commands" / "implement-github-issue.md"
SCRIPT = REPO_ROOT / ".claude" / "skills" / "implement-spec" / "list_specs.py"
REPORTS = REPO_ROOT / ".claude" / "skills" / "dry-run" / "coverage_reports.py"

HEADING = re.compile(r"^## (.+)$", re.M)
#: The template block inside the HTML comment, which is not an entry.
PLACEHOLDER = "<spec-name>"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


#: The marker grammar is imported, never restated: a second copy of it would drift, and the
#: whole point is that a marker here parses exactly as one in `plugins/` does.
reports = load(REPORTS, "coverage_reports_for_declined")

#: Same 13 tools as `tests/test_dated_negatives_are_marked.py`, which polices assertion lines
#: in `tests/`. Kept local rather than shared because the two guards read different corpora and
#: neither should be able to break the other by narrowing its list.
MCP_TOOLS = (
    "explain_error_code", "search_docs", "sdk_guide", "get_sdk_reference", "reporting_guide",
    "generate_scaffold", "get_sample_data", "find_examples", "mapping_workflow",
    "analyze_record", "get_capabilities", "download_resource", "submit_feedback",
)
TOOL_RE = re.compile(r"(?i)(%s)" % "|".join(MCP_TOOLS))

#: Prose phrasings that assert a tool LACKS something. Broader than the assertion-line vocab in
#: `test_dated_negatives_are_marked.py`, because this runs over maintainer prose where a false
#: positive costs a marker rather than a rewrite — and because the wording that motivated the
#: guard ("neither X nor Y appears in the manifest") matches none of the narrow forms.
#:
#: ⚠️ It is a phrase list, so it is evadable by paraphrase, and that is disclosed rather than
#: papered over: it catches the shapes that have actually appeared, not every possible way to
#: say "absent". The backstop is `report_negatives`, which now reads this file — a negative that
#: dodges the vocab and carries no marker is invisible to both, so prefer the marker.
ABSENCE_VOCAB = re.compile(
    r"(?i)appear(?:s|ed)? nowhere|nowhere in|(?:does|do|did|would) not appear|"
    r"neither\b[^.]{0,200}\bnor\b[^.]{0,200}\bappear(?:s|ed)?\b|"
    r"return(?:s|ed|ing)? no\b|carr(?:y|ies|ied|ying) no\b|contain(?:s|ed|ing)? no\b|"
    r"has no\b|have no\b|(?:is|are|was|were) absent|names? neither|lost its citation|"
    r"(?:no longer|does not|did not|doesn't|never) "
    r"(?:names?|named|mentions?|contains?|carr(?:y|ies)|includes?|lists?|documents?)"
)
#: Block-level escape for prose that QUOTES a retracted claim, mirroring the file-level
#: `MCP-NEGATIVE-SCAN: ignore-file` that `coverage_reports.py` already honors. A correction has
#: to be able to restate what it corrects; without this, the honest move (quote the wrong claim
#: verbatim) is the one the guard punishes, and the author is pushed to paraphrase history
#: instead of adding evidence. Same abuse risk as the file-level opt-out, and the same answer:
#: it is one grep away from review.
QUOTED_HISTORY = "MCP-NEGATIVE-SCAN: quoted-history"

#: The wording this guard was built from, pinned so the detector cannot be quietly narrowed
#: into uselessness. Retracted 2026-08-13 — see the entry's correction bullet.
RETRACTED_WORDING = (
    'At 1.32.9 neither "stdio" nor `sz-mcp-coworker` appears in that description or anywhere '
    "in the `get_capabilities` manifest."
)


def headings(path):
    if not path.is_file():
        return []
    return [h.strip() for h in HEADING.findall(path.read_text(encoding="utf-8"))
            if h.strip() != PLACEHOLDER]


def entries():
    """(name, body) per declined entry, excluding the comment template."""
    text = DECLINED.read_text(encoding="utf-8")
    found = re.findall(r"^## (.+?)$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return [(n.strip(), b) for n, b in found if n.strip() != PLACEHOLDER]


def bullet_blocks(text):
    """[(first_lineno, block_text)] — one per Markdown list item, continuation lines included.

    Per BULLET, not per entry. A whole-entry check would have passed on the wording this guard
    exists for: the wrong sub-claim and a well-formed marker sat in the same entry, so any
    entry-level rule is satisfied by a marker attached to a different claim.
    """
    blocks, current = [], None
    for lineno, line in enumerate(text.split("\n"), 1):
        if re.match(r"^\s*[-*+]\s", line):
            current = [lineno, [line]]
            blocks.append(current)
        elif current is not None and line.strip():
            current[1].append(line)                     # continuation of the current item
        else:
            current = None                              # blank line ends the item
    return [(lineno, "\n".join(lines)) for lineno, lines in blocks]


def skill_section(text, title):
    """The named `## ` section of a skill file, fenced code blocks included.

    Fence-aware on purpose: the decline section's own entry template is a fenced block whose
    first line is `## <spec-name>`, so a plain `(?=^## )` boundary truncates the section right
    where the interesting part starts.
    """
    out, inside, fenced = [], False, False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            inside = line[3:].strip().startswith(title)
        if inside:
            out.append(line)
    return "\n".join(out)


def unmarked_absence_claims(text):
    """[(lineno, excerpt)] for each bullet asserting a tool lacks something with no marker."""
    found = []
    for lineno, block in bullet_blocks(text):
        if QUOTED_HISTORY in block:
            continue
        if not (TOOL_RE.search(block) and ABSENCE_VOCAB.search(block)):
            continue
        if reports.MCP_NEGATIVE.search(block):
            continue
        found.append((lineno, " ".join(block.split())[:160]))
    return found


class TheLedgerExists(unittest.TestCase):
    def test_the_file_ships(self):
        self.assertTrue(DECLINED.is_file(), "specs/DECLINED.md is missing")

    def test_it_has_at_least_one_entry(self):
        """Not vacuous: with no entries every check below would pass trivially."""
        self.assertTrue(entries(), "no declined entries — the checks below assert nothing")


class EveryEntryIsComplete(unittest.TestCase):
    """Reason is required for the `keep-by-design` reason; Revisit-if stops a graveyard."""

    def test_each_entry_has_a_date(self):
        for name, body in entries():
            with self.subTest(spec=name):
                self.assertRegex(body, r"- \*\*Declined:\*\*\s*\d{4}-\d{2}-\d{2}")

    def test_each_entry_names_who_decided(self):
        for name, body in entries():
            with self.subTest(spec=name):
                self.assertRegex(body, r"- \*\*Decided by:\*\*\s*\S")

    def test_each_entry_carries_a_non_empty_reason(self):
        for name, body in entries():
            with self.subTest(spec=name):
                m = re.search(r"- \*\*Reason:\*\*(.*?)(?=\n- \*\*|\Z)", body, re.S)
                self.assertIsNotNone(m, "%s has no Reason field" % name)
                self.assertGreater(
                    len(m.group(1).strip()), 40,
                    "%s's Reason is too thin to be a reason — an unreasoned decline is "
                    "indistinguishable from nobody having looked" % name,
                )

    def test_each_entry_says_what_would_reopen_it(self):
        for name, body in entries():
            with self.subTest(spec=name):
                m = re.search(r"- \*\*Revisit if:\*\*(.*?)(?=\n- \*\*|\Z)", body, re.S)
                self.assertIsNotNone(m, "%s has no Revisit-if field" % name)
                self.assertGreater(len(m.group(1).strip()), 10,
                                   "%s must name a trigger or say 'nothing foreseeable'" % name)


class TheTwoLedgersAgree(unittest.TestCase):
    def test_no_spec_is_both_implemented_and_declined(self):
        both = sorted(set(headings(DECLINED)) & set(headings(IMPLEMENTED)))
        self.assertEqual(
            [], both,
            "spec(s) in both ledgers — a spec has one terminal state, and discovery would "
            "subtract it twice while a reader cannot tell what happened: %s" % both,
        )

    def test_every_declined_name_resolves_to_a_spec_file(self):
        missing = [n for n in headings(DECLINED) if not (SPECS / f"{n}.md").is_file()]
        self.assertEqual(
            [], missing,
            "DECLINED.md names spec file(s) that do not exist — the decision's reasoning is "
            "unreachable: %s" % missing,
        )

    def test_no_declined_name_is_prose(self):
        """Every `##` here is parsed as a spec name, so a prose heading becomes a phantom entry.

        This fired on the first run: a `## Why every entry needs a reason` section in the header
        was counted as a declined spec, reporting 2 where there was 1.
        """
        for name in headings(DECLINED):
            with self.subTest(heading=name):
                self.assertTrue(
                    (SPECS / f"{name}.md").is_file(),
                    "%r is a prose heading, not a spec — use bold text instead, or it is "
                    "counted as a declined spec" % name,
                )

    def test_the_declined_spec_file_is_left_in_place(self):
        """Declining never archives or deletes: the analysis is why the call could be made."""
        for name in headings(DECLINED):
            with self.subTest(spec=name):
                self.assertTrue((SPECS / f"{name}.md").is_file())
                self.assertFalse((SPECS / "archive" / f"{name}.md").is_file(),
                                 "%s was archived; a declined spec stays in specs/" % name)


class TheComputationStillSubtractsTheDeclinedSet(unittest.TestCase):
    """INV-216's FIRST clause, which is untouched and still binding.

    ⚠️ **Re-pointed 2026-09-16 (#60).** These two assertions read `implement-spec/SKILL.md`
    until that skill retired. What they actually test is the **candidate-set computation** --
    that a declined item is subtracted rather than re-offered -- and that computation lives in
    `list_specs.py`, which is **kept**: INV-216's first clause still binds it. The script, not
    the prose, is the thing that must not regress.

    ⛔ INV-216's second and third clauses -- that a command NAMES the script, and that its prose
    steps explain it -- were scoped to the archive by a dated correction on 2026-09-16, so no
    assertion here reads a command file any more.
    """

    def setUp(self):
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_the_declined_set_is_subtracted(self):
        flat = " ".join(self.text.split())
        self.assertIn("candidates - implemented - declined", flat.replace("−", "-"),
                      "the computation no longer subtracts the declined set, so a declined "
                      "item is re-offered every run")

    def test_declined_md_is_treated_as_a_meta_file(self):
        self.assertIn(
            '"DECLINED"', self.text,
            "DECLINED.md is no longer in the script's META set, so it would be counted as a "
            "candidate spec rather than as a terminal-state ledger")


class TheIssuePathKnowsAboutIt(unittest.TestCase):
    """The live decline rule, which moved to the issue command in #66.

    ⛔ **Two assertions were DROPPED here on 2026-09-16 (#60), not re-pointed**, because their
    subject retired rather than moved:

    * *"Leave the spec file where it is"* -- `specs/` is a read-only archive (INV-307); nothing
      writes there, so an instruction not to move a spec file governs nothing.
    * *dedup visibility for a declined spec* -- deduplication moved to `/feedback-to-issues`,
      which searches the **issue tracker** (#49), and is asserted by that command's own guard.

    Keeping either by pointing it at the issue command would have written spec-workflow prose
    into a command about issues -- an assertion passing on text that describes nothing.
    """

    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_it_forbids_declining_unilaterally(self):
        flat = " ".join(self.text.split())
        self.assertRegex(
            flat, r"(?i)Never decline on your own initiative",
            "the decline rule no longer reserves the decision to the maintainer. Deciding NOT "
            "to build something is theirs (INV-217); a run that may decline can retire work "
            "nobody ruled on")

    def test_it_requires_a_reason_and_a_revisit_condition(self):
        flat = " ".join(self.text.split())
        self.assertIn("**Reason:**", flat)
        self.assertIn("**Revisit if:**", flat)


class TheCensusSeparatesTheTwoStates(unittest.TestCase):
    """`citations.py` was the second consumer: it reported declined specs as unimplemented."""

    def test_declined_is_a_meta_spec(self):
        src = (REPO_ROOT / ".claude" / "skills" / "compact-dev-environment"
               / "citations.py").read_text(encoding="utf-8")
        self.assertRegex(src, r'META_SPECS = \{[^}]*"DECLINED"',
                         "DECLINED.md would be counted as a spec file by the census")

    def test_the_census_reports_them_apart(self):
        import subprocess
        import sys
        proc = subprocess.run(
            # `--repo` is a top-level argument and must precede the subcommand.
            [sys.executable,
             str(REPO_ROOT / ".claude/skills/compact-dev-environment/citations.py"),
             "--repo", str(REPO_ROOT), "census", "--area", "specs"],
            capture_output=True, text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("declined (decided not to build)", proc.stdout)
        self.assertIn("genuinely unimplemented", proc.stdout)
        m = re.search(r"declined \(decided not to build\): (\d+)", proc.stdout)
        self.assertIsNotNone(m)
        self.assertEqual(len(headings(DECLINED)), int(m.group(1)),
                         "the census's declined count disagrees with the ledger")

    def test_the_unimplemented_count_actually_excludes_the_declined(self):
        """Printing both labels is not the same as subtracting one from the other.

        An earlier version asserted only that both lines appeared and that the declined
        count was right — so reverting the subtraction (`specs - headings - declined` back
        to `specs - headings`) left every assertion passing while the census again reported
        settled work as outstanding. Assert the arithmetic, not the labels.
        """
        import subprocess
        import sys
        proc = subprocess.run(
            [sys.executable,
             str(REPO_ROOT / ".claude/skills/compact-dev-environment/citations.py"),
             "--repo", str(REPO_ROOT), "census", "--area", "specs"],
            capture_output=True, text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        not_in_ledger = int(re.search(r"spec files not in ledger\s*: (\d+)", proc.stdout).group(1))
        declined = int(re.search(r"declined \(decided not to build\): (\d+)", proc.stdout).group(1))
        outstanding = int(re.search(r"genuinely unimplemented\s*: (\d+)", proc.stdout).group(1))
        self.assertGreater(declined, 0, "no declined specs — this check would be vacuous")
        self.assertEqual(
            not_in_ledger - declined, outstanding,
            "genuinely-unimplemented (%d) is not 'not in ledger' (%d) minus declined (%d) — the "
            "census is counting settled decisions as outstanding work"
            % (outstanding, not_in_ledger, declined),
        )


class AnAbsenceClaimNamesItsOwningRoute(unittest.TestCase):
    """INV-194 applied to the file that most needs it, because nothing else re-verifies it.

    `implement-spec` Step 3.3 re-asks a spec's Senzing facts at implementation time. A declined
    spec is never implemented, so its `Revisit if:` clause and any dated revisit note are the
    one Senzing claim shape in the repo with no re-verification path — and the skill tells the
    next reader to trust this file over the spec's own citations. A stale or wrong-route
    negative here therefore sends the recheck to the wrong answer while looking evidenced.
    """

    def setUp(self):
        self.text = DECLINED.read_text(encoding="utf-8")

    def test_every_absence_claim_carries_a_parseable_marker(self):
        found = unmarked_absence_claims(self.text)
        self.assertEqual(
            [], found,
            "A bullet in DECLINED.md states that an MCP tool LACKS something and carries no "
            "parseable `MCP-NEGATIVE:` marker. Nothing re-verifies this file, so that claim "
            "can never be re-asked — and naming the route that would CARRY the fact is what "
            "separates a verified negative from a wrong-route one (INV-194). Add the marker "
            "with its `owner:` clause, or mark quoted history with %r:\n  %s"
            % (QUOTED_HISTORY, "\n  ".join("line %d: %s" % row for row in found)),
        )

    def test_the_scan_reaches_this_file_at_all(self):
        """Not vacuous: the guard above passes trivially if the file is outside the scan.

        `coverage_reports.py` excluded all of `specs/` until 2026-08-13, which is precisely how
        a wrong negative reached a terminal-state record with nothing looking at it.
        """
        scanned = [Path(p).name for p in reports._scan_files(str(REPO_ROOT))]
        self.assertIn("DECLINED.md", scanned,
                      "specs/DECLINED.md is not in the negatives scan surface, so its markers "
                      "are on no worklist and this file's claims are unre-checkable")

    def test_this_files_markers_reach_the_worklist(self):
        found = reports.find_negatives(str(REPO_ROOT))
        here = [r for r in found if Path(r[5]).name == "DECLINED.md"]
        self.assertTrue(
            here,
            "DECLINED.md contributes no marker to `coverage_reports.py negatives`. If its "
            "absence claims were all retired, say so in the entry; otherwise the worklist "
            "silently lost them",
        )
        for _key, _version, _date, _claim, owner, relpath, lineno in here:
            with self.subTest(where="%s:%d" % (relpath, lineno)):
                self.assertTrue(
                    TOOL_RE.search(owner)
                    or re.search(r"(?i)validator|rejection|error|response", owner),
                    "the owner clause must name the route that would carry the fact, not "
                    "restate the absence. Got: %r" % owner,
                )

    def test_the_detector_fires_on_the_retracted_wording(self):
        """Negative control, pinned. Reintroducing the 2026-08-13 wording must fail the guard.

        Asserting only that the live file is clean cannot notice the vocabulary being narrowed
        until it detects nothing — the failure mode `test_the_detector_recognizes_the_historical
        _offenders` guards against in `test_dated_negatives_are_marked.py`.
        """
        block = "  - ⚠️ **One of the two routes lost its citation.** " + RETRACTED_WORDING
        self.assertTrue(TOOL_RE.search(block), "tool name not detected")
        self.assertTrue(ABSENCE_VOCAB.search(block), "absence phrasing not detected")
        self.assertEqual(
            [(1, " ".join(block.split())[:160])], unmarked_absence_claims(block),
            "the retracted wording must be reported as an unmarked absence claim",
        )

    def test_the_detector_accepts_the_same_claim_once_it_names_its_owner(self):
        """Positive control: the guard asks for evidence, not for silence about absences."""
        marked = (
            "  - **The stdio install citation is gone.** sdk_guide(topic='install', "
            "platform='linux_apt') names neither stdio nor extract.\n"
            "    MCP-NEGATIVE: sdk_guide(topic='install', platform='linux_apt') — no stdio "
            "mode and no sz-mcp-coworker extract command — owner: mapping_workflow"
            "(action='start') step-1 instructions still name stdio/airgap mode (routing "
            "negative) — server 1.32.9, 2026-08-13"
        )
        self.assertTrue(ABSENCE_VOCAB.search(marked), "the fixture must be absence-shaped")
        self.assertEqual([], unmarked_absence_claims(marked))

    def test_quoted_history_is_exempt_but_only_when_declared(self):
        quoted = "  - Corrected: it once said " + RETRACTED_WORDING
        self.assertEqual(1, len(unmarked_absence_claims(quoted)))
        self.assertEqual([], unmarked_absence_claims(
            quoted + "\n    <!-- %s — retracted claim, kept verbatim -->" % QUOTED_HISTORY))

    def test_a_bullet_that_makes_no_absence_claim_is_not_flagged(self):
        """Stating what IS true is the form the convention asks for; it must stay unencumbered."""
        positive = ("  - `get_capabilities` returns it as the server's own name — "
                    "`server_info.server_name = \"sz-mcp-coworker\"`.")
        self.assertTrue(TOOL_RE.search(positive))
        self.assertEqual([], unmarked_absence_claims(positive))

    def test_the_skill_shows_the_marker_in_its_declined_template(self):
        """A convention only the tests know about is a convention the next entry will miss.

        Scoped to the decline section, not the whole file: `MCP-NEGATIVE` appears in Step 3.4
        already, and a whole-file check would therefore have passed before this shipped.
        """
        section = skill_section(SKILL.read_text(encoding="utf-8"), "Declining an issue")
        self.assertTrue(section, "the decline section is gone from implement-github-issue.md")
        self.assertIn(
            "MCP-NEGATIVE", section,
            "the decline section must show the marker form for an absence-shaped "
            "`Revisit if:`, or the next entry is written without one — and nothing re-verifies "
            "DECLINED.md afterwards",
        )
        self.assertIn("Revisit if", section)


if __name__ == "__main__":
    unittest.main()
