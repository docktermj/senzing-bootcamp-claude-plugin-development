"""Every hard rule added since the last audit is cited at its line, or deferred by name.

The reverse contract has two legitimate states for a hard rule the plugin ships, and
silence is neither:

- **Cited** — an `INV-nnn` at the rule's own line, so a reader standing there can look the
  governing rule up (INV-183).
- **Deferred** — the rule is named in a `DEFERRED INVARIANT` block in `IMPLEMENTED.md`, with
  drafted wording, because only the maintainer may sign off on an invariant. The citation is
  then *un-writable* until the id is minted, which is exactly the queued-approval hazard
  `implement-spec` Step 5 names.

⛔ **INV-282 governs how this guard matches** — from the claim, not from phrasings already seen.

⛔ **This guard exists because the manual version of the check failed twice.** On 2026-08-28 a
ledger entry claimed *"all four hard-rule lines cite one of those at the line"* when two did
not — written from a `per-rule --uncited | grep` narrowed to two phrases, three cycles after
an audit had already recorded that method as unsound. A grep can only confirm lines you
already suspect; the uncited ones are by construction the ones you did not. The check has to
be a set difference, and a set difference is a thing a test can do.

⚠️ **Scope: rules added since the newest audit entry's recorded commit** — the set a run is
answerable for, resolved from the ledger rather than guessed. It does **not** police the
standing backlog of uncited rules across the corpus; that is `per-rule --uncited`'s worklist
and is far larger.

⚠️ **A rule REVERTED to its pre-audit wording leaves this guard's scope, and that is not a
hole to plug.** `since` diffs against the newest audit's commit, so deleting a citation that
was added *after* that commit makes the line identical to the committed one and it stops
being reported. Verified by negative control: the guard is unmoved by that edit and fails
correctly on a genuinely new uncited rule, which is what it claims to cover. The standing
backlog is `per-rule --uncited`'s job, and it is far larger.

⛔ **The parser reads `conformance.py`'s own `SCAN_ROOTS`, and a line it cannot place is a
FAILURE, never a drop.** This guard consumes a report it does not produce, and for its whole
life it carried a private idea of which roots that report mentions: it keyed file headings on
`plugins/`, so when the `since` view was widened to the maintainer surface (#38) all 112 lines
it reported under `.claude/` were dropped between the two halves of this file. `added` came out
empty, and empty took the "nothing added" skip — the guard reported the *absence of new rules*
while looking at 112 of them. ⚠️ The plugins-keyed read was not an oversight in the dark: a
2026-09-03 ledger entry states it outright, reasoning about which lines could confuse the
parser, and nobody asked what the key would do to a root added later.

⚠️ **The maintainer surface is COUNTED, not checked, and the count is printed even when it is
zero.** Command files restate their skill's rules by design and cite nothing, so checking
`.claude/` here turns roughly 49 restatements into failures; `test_since_view_sees_the_maintainer_surface.py`
measured that and scoped this consumer out deliberately. What was wrong was doing it by
*silence*. The number is now reported on every run, so 93 unchecked lines are a visible
decision rather than an invisible one — and a genuinely new `.claude/` guarantee is still not
caught by this guard. That is the remaining gap, stated rather than closed.

⚠️ **Skips rather than fails when the range cannot be resolved** — no git, a shallow clone, an
audit entry whose `Commit:` is `uncommitted`. A guard that hard-failed there would fail on
checkouts that have nothing wrong with them.

Source spec:
`specs/three-hard-rules-from-the-2026-08-28-loop-carry-no-citation-at-the-line.md`.

Source issue: #74 (the reverse-contract gate silently discards every rule outside `plugins/`).

Run:  python3 -m unittest discover -s tests
"""
import collections
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / ".claude" / "skills" / "production-readiness-audit" / "conformance.py"
IMPLEMENTED = REPO_ROOT / "specs" / "IMPLEMENTED.md"


def _scan_roots():
    """The producer's own root list (INV-308), imported rather than restated.

    ⛔ Returns `()` when it cannot be read, and the callers say so. **There is deliberately no
    fallback literal**: a private copy that silently disagrees with the producer is the entire
    defect this module was rebuilt around, and a fallback is just that copy with a nicer name.
    """
    if not CONFORMANCE.is_file():
        return ()
    try:
        spec = importlib.util.spec_from_file_location("conformance_for_the_gate", CONFORMANCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules["conformance_for_the_gate"] = module
        spec.loader.exec_module(module)
        roots = getattr(module, "SCAN_ROOTS", ())
    except Exception:
        return ()
    return tuple(str(r) for r in roots)


SCAN_ROOTS = _scan_roots()

#: Which scanned roots this guard CHECKS and which it only counts, derived from `SCAN_ROOTS` by
#: one rule -- the maintainer surface is not shipped -- so a fourth root joins the right half
#: without being named here a second time.
CHECKED_ROOTS = tuple(r for r in SCAN_ROOTS if not r.startswith(".claude/"))
OUT_OF_SCOPE_ROOTS = tuple(r for r in SCAN_ROOTS if r.startswith(".claude/"))


def conformance(*args):
    """Run a conformance view, or return None when it cannot run here."""
    if not CONFORMANCE.is_file():
        return None
    try:
        r = subprocess.run(["python3", str(CONFORMANCE), *args],
                           capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=180)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def normalize(line):
    """A rule line reduced to a comparable key, matching how `per-rule` prints it."""
    s = re.sub(r"^[-\d.\s]*", "", line).replace("⛔", "").strip()
    return re.sub(r"\s+", " ", s)[:60]


def deferred_rule_text():
    """All prose inside `DEFERRED INVARIANT` bullets, flattened.

    A deferral names the rule and its site, so a rule whose wording appears here is
    accounted for even though no id exists to cite yet.
    """
    text = IMPLEMENTED.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"DEFERRED INVARIANT", text):
        out.append(text[m.start():m.start() + 4000])
    return re.sub(r"\s+", " ", " ".join(out)).lower()


#: ⛔ The citation must be on the RULE'S OWN LINE, not merely near it.
#:
#: This check used to ask `conformance.py per-rule --uncited` whether a rule was cited, and
#: `per-rule` counts an invariant cited in the **sentence beside** a rule as citing it. That is
#: right for `per-rule`'s own question — can a reader at this line name the governing rule — and
#: wrong as an accounting test, because the neighbor's citation can be about something else.
#:
#: Found by the 2026-09-01 audit: `module-04-data-collection/SKILL.md:469` ships
#: ⛔ "Prefer `download_url` (MCP-hosted) over `source_download_url` for every CORD fetch" with no
#: invariant at its line and no deferral naming it, and this test passed — because the paragraph
#: two lines below reads "Observation, not an MCP-sourced fact (INV-080/INV-149)", which govern the
#: provenance of a 403 observation and say nothing about route preference. The reverse-contract
#: defense reported an unregistered guarantee as accounted for.
#:
#: ⚠️ `per-rule`'s own counting is deliberately NOT changed — every past ledger figure was measured
#: against it, and widening it would move a number nobody would re-measure. The guard is stricter
#: than the report instead.
#:
#: ⛔ And the check must run on the SOURCE line, not the reported one: `since` truncates its
#: display at 110 characters, so a citation past the cut is invisible. Checked against the
#: truncated text this flagged four rules that ARE cited — including a 638-character bullet
#: carrying INV-146 and INV-242 — which is the same truncation defect the 2026-09-01 audit
#: found in `test_conformance_sees_a_rule_beside_a_citation.py`, reintroduced here within the
#: hour by the fix for the audit's own finding.
INV_ON_THE_LINE = re.compile(r"INV-\d+")


def _comparable(text):
    """Both sides of the deferral match, reduced the same way.

    ⚠️ `normalize()` strips the ⛔ from a rule line; the deferral quotes the rule WITH it. For a
    rule whose ⛔ leads the line that still matched, because the probe was a substring of
    "⛔ <same text>". For a rule whose ⛔ sits mid-line — `- **6d (desired outcome).** ⛔ **This
    one is MULTI-select…** — the stop sign lands between the two halves of the probe and the
    match fails against a deferral that names the rule correctly. Strip it from both sides.
    """
    return re.sub(r"\s+", " ", re.sub(r"[`*⛔]", "", text)).lower().strip()


#: What `since` prints, split into the three populations a consumer must tell apart. Every
#: reported line lands in exactly one of them, and `reported` is the producer's own total -- so
#: `checked + out_of_scope + unresolved != reported` is arithmetic that cannot be argued with.
Parsed = collections.namedtuple(
    "Parsed", "checked out_of_scope unresolved unknown_headings reported")


def _is_heading(stripped):
    """A file heading in `since`'s output: a path, alone on its line."""
    return stripped.endswith(".md") and " " not in stripped and not stripped.startswith("+")


def _root_of(heading):
    """The `SCAN_ROOTS` entry a heading sits under, or None if it sits under none."""
    if heading is None:
        return None
    for root in SCAN_ROOTS:
        if heading == root or heading.startswith(root + "/"):
            return root
    return None


def _full_source_line(relpath, body):
    """`since` truncates its display at 110 characters; resolve back to the whole line.

    A citation past the cut is invisible, which once flagged four cited rules as uncited --
    including a 638-character bullet carrying two ids.
    """
    path = REPO_ROOT / relpath
    if path.exists():
        for line in path.read_text(encoding="utf-8").split("\n"):
            if line.startswith(body):
                return line
    return body


def parse_since(since_output):
    """Every rule `since` reported, placed under the root it came from.

    ⛔ **Nothing is discarded.** A line whose heading matches no known root is `unresolved` and
    fails the guard; it is never skipped past, because a silently skipped line is indis-
    tinguishable from a line that was never reported.
    """
    heading = None
    checked, out_of_scope, unresolved = [], [], []
    unknown_headings, reported = [], 0
    for raw in since_output.splitlines():
        stripped = raw.strip()
        if _is_heading(stripped):
            heading = stripped
            if _root_of(heading) is None and heading not in unknown_headings:
                unknown_headings.append(heading)
            continue
        if not stripped.startswith("+ "):
            continue
        reported += 1
        body = stripped[2:]
        root = _root_of(heading)
        if root is None:
            unresolved.append((heading, body))
        elif root in OUT_OF_SCOPE_ROOTS:
            out_of_scope.append((heading, body))
        else:
            checked.append((heading, _full_source_line(heading, body)))
    return Parsed(checked, out_of_scope, unresolved, unknown_headings, reported)


def announce(parsed):
    """⛔ Report the breakdown on every run, **including the zeroes**.

    An out-of-scope count that appears only when it is non-zero makes its absence ambiguous:
    the reader cannot tell "no maintainer-surface rules were added" from "the line was dropped
    again". One line, always, is what makes the 93 unchecked lines a decision on the record.
    Written to stderr like the fpdf2 notice, for the same reason -- it is a notice, not output.
    """
    sys.stderr.write(
        "[new-hard-rules] %d line(s) reported since the last audit: %d checked, %d out of "
        "scope (%s), %d unresolved\n"
        % (parsed.reported, len(parsed.checked), len(parsed.out_of_scope),
           ", ".join(OUT_OF_SCOPE_ROOTS) or "no out-of-scope root", len(parsed.unresolved)))
    sys.stderr.flush()


class EveryNewHardRuleIsAccountedFor(unittest.TestCase):
    def test_the_check_can_run(self):
        """⛔ INV-265 — say so when the scan cannot run, rather than passing silently."""
        if conformance("rules") is None:
            self.skipTest("conformance.py unavailable here (no git range, or not executable)")
        self.assertTrue(True)

    def test_each_rule_added_since_the_last_audit_is_cited_or_deferred(self):
        since = conformance("since", "--since-last-audit")
        uncited = conformance("per-rule", "--uncited")
        if since is None or uncited is None:
            self.skipTest("conformance.py could not resolve the since-last-audit range")
        if not SCAN_ROOTS:
            self.skipTest(
                "conformance.py's scanned-root list could not be imported, so this guard "
                "cannot know which headings the report contains. It refuses to guess -- see "
                "TheParserAgreesWithTheProducer, which FAILS on this rather than skipping")

        parsed = parse_since(since)
        announce(parsed)

        # ⛔ A line the parser cannot place is reported, never dropped. This is the defect
        # itself: 112 placeable lines were dropped here and the emptiness read as "none".
        self.assertEqual(
            [], parsed.unknown_headings,
            "`since` reported rules under %d heading(s) matching no scanned root: %s. The "
            "producer and this consumer disagree about which roots exist, and every rule "
            "under those headings goes unchecked"
            % (len(parsed.unknown_headings), ", ".join(parsed.unknown_headings)))
        self.assertEqual(
            [], [line for _h, line in parsed.unresolved],
            "%d reported rule line(s) could not be attributed to any file, so nothing can be "
            "checked at their source line" % len(parsed.unresolved))

        if not parsed.reported:
            # ⛔ **Say WHICH kind of nothing this is.** An empty range and a range that never
            # covered the work both arrive here as "no hard rules added", and until 2026-09-03
            # the skip message asserted the first. It was the second: the newest audit entry
            # recorded the commit that carried the implementations, so the range started AT
            # them and six added rules sat outside it while this guard reported green by not
            # running. The resolver now widens past such a ref and says so; this repeats it,
            # because a skip line is what a reader actually sees.
            # (Source: `since-last-audit-reports-zero-when-the-audit-record-shares-the-work-commit`.)
            if "SUSPECT-REF" in since:
                self.skipTest(
                    "the range's recorded ref carried shipped work, so it was widened past it "
                    "and STILL reports nothing added -- read the widened range in the "
                    "conformance output before believing this skip")
            self.skipTest(
                "the report lists no hard-rule lines at all since the newest audit entry. The "
                "ref was accepted as recorded (no SUSPECT-REF), so this is an empty range "
                "rather than a range that missed the work")

        if not parsed.checked:
            # ⚠️ A THIRD kind of nothing, and the one this guard used to disguise as the
            # first: rules were added, all of them outside the corpus this check covers.
            self.skipTest(
                "%d hard-rule line(s) were added since the newest audit entry and none is in "
                "the checked corpus (%s): %d sit under the maintainer surface, which this "
                "guard counts and does not check. Rules WERE added -- this is not an empty "
                "range" % (parsed.reported, ", ".join(CHECKED_ROOTS), len(parsed.out_of_scope)))

        deferred = deferred_rule_text()
        unaccounted = []
        for _path, line in parsed.checked:
            key = normalize(line)
            if not key:
                continue
            if INV_ON_THE_LINE.search(line):
                continue                                   # cited ON its own line
            probe = _comparable(key)[:44]
            if probe and probe in _comparable(deferred):
                continue                                   # named in a deferral
            unaccounted.append(line[:110])

        self.assertEqual(
            [], unaccounted,
            "a hard rule added since the last audit cites no invariant at its line AND is "
            "named in no DEFERRED INVARIANT block. Those are the only two legitimate states; "
            "silence is the reverse-contract defect. Either add the citation, or record the "
            "deferral with its drafted wording:\n  " + "\n  ".join(unaccounted))

    def test_the_deferral_scan_is_not_vacuous(self):
        """⛔ INV-265 — an empty deferral corpus would make the escape hatch match nothing."""
        deferred = deferred_rule_text()
        self.assertGreater(
            len(deferred), 500,
            "no DEFERRED INVARIANT prose was found in IMPLEMENTED.md, so the deferral escape "
            "hatch above can never match and this guard is stricter than the contract")
        self.assertIn("inv-nnn", deferred,
                      "no deferral carries drafted `INV-NNN` wording, which is what makes a "
                      "deferral an answer rather than a label")


if __name__ == "__main__":
    unittest.main()
