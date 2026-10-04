"""`find_examples`' coverage figures are not citeable, because the server states two of them.

One tool on one server describes its own coverage two different ways, read in the same
session (server 1.33.0, re-confirmed 2026-08-28):

- **Declared tool description** (the manifest a client loads): *"37 indexed Senzing GitHub
  repositories ... Indexes source code (.py, .java, .cs, .rs) ... Covers Python, Java, C#,
  Rust SDK patterns"*.
- **`get_capabilities`**, on the same tool: *"42 indexed Senzing GitHub repositories ...
  (.py, .java, .cs, .rs, .ts, .js) ... Python, Java, C# official; Rust and TypeScript/Node.js
  community"*.

Two counts and two extension sets. A call settles it:
`find_examples(query='add record engine initialization', language='typescript')` returns
`brianmacy/sz-napi` → `code-snippets/initialization/engine-priming/index.ts`. `.ts` is
indexed; the declared description is the stale half.

⛔ **So no repository count is citeable, and this guard exists to keep one out.** The plugin
was not wrong when this was found — it quotes `get_capabilities` and states no count. The
exposure is structural: `ground-rules.md` makes the **declared schema** authoritative for what
a tool accepts (INV-234), which is correct, and an editor applying that in reverse would trust
manifest *prose* — landing on the stale half with a citation that looks impeccable. A future
edit writing "37 repositories", or "indexes .py, .java, .cs and .rs", would be wrong while
carrying a real MCP citation.

⚠️ TypeScript is a shipped bootcamp language, not hypothetical — `bootcamp-preparation/SKILL.md`
offers it — so the stale half would send a TypeScript bootcamper past the one route that does
have examples for their binding.

⚠️ What this does NOT establish: which figure is current today. That is a live-server property
the offline suite cannot see (INV-108). It asserts the plugin cites **no** figure, which is the
only stance that cannot go stale.

Upstream: reported 2026-08-27 via `submit_feedback(category='bug')` on the maintainer's verbatim
approval. Anonymous, so no reply will arrive; re-check rather than assuming it was acted on.

Enforces **INV-280** — a declared schema is authoritative for the parameters a tool accepts, not for prose describing
what it covers; a coverage figure the server states two ways is not quotable at all.

Source spec: `specs/find-examples-self-describes-two-different-coverages.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import tempfile
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins"

#: A repo count asserted about the example index. Matched only near a repo/index word so the
#: many unrelated 37s and 42s in the corpus (record counts, line numbers) do not trip it.
COUNT_NEAR_REPO = re.compile(
    r"\b(37|42)\b[^.\n]{0,60}\b(repo|repositor|indexed)|"
    r"\b(repo|repositor|indexed)[^.\n]{0,60}\b(37|42)\b", re.I)
#: The declared description's extension list, which omits .ts/.js.
STALE_EXTENSIONS = re.compile(r"\.cs\s*,\s*\.rs(?!\s*,\s*\.ts)", re.I)


MARKER = "COVERAGE-FIGURE-SCAN: quoted-history"


def scannable_lines(path):
    """(lineno, line) pairs, skipping any block a quoted-history marker exempts.

    ⚠️ Prose that **quotes** the stale figures in order to correct them is not asserting
    them, and a guard that cannot tell the difference forbids the correction from naming
    what it corrects. This mirrors the repo's existing `MCP-NEGATIVE-SCAN: quoted-history`
    convention: the marker sits directly above the block and covers it to the next blank
    line, so the exemption is narrow and visible rather than a file-wide opt-out.
    """
    out, skipping = [], False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if MARKER in line:
            skipping = True
            continue
        if skipping:
            if not line.strip():
                skipping = False
            continue
        out.append((n, line))
    return out


def figure_lines(path, pattern):
    """1-based lines where ``pattern`` starts in ``path``, outside a quoted-history block.

    ⚠️ **Matched across line wraps (#424).** A figure is a number beside a word ("37
    repositories", "~9999 chunks"), and prose wraps between them; read one line at a time, a
    wrapped figure passed. ``match_lines`` runs the pattern on whitespace-collapsed Markdown
    blocks, so ``COUNT_NEAR_REPO``'s ``[^.\n]`` now spans a wrap within a block. A match whose
    first line is inside a block the marker exempts is dropped, as before.
    """
    scanned = {n for n, _line in scannable_lines(path)}
    return [n for n in match_lines(path.read_text(encoding="utf-8"), pattern) if n in scanned]


def shipped_files():
    """Shipped markdown plus scripts — a count could be written into either."""
    return sorted(p for p in PLUGIN.rglob("*")
                  if p.is_file() and p.suffix in {".md", ".py"}
                  and "__pycache__" not in p.parts)


class NoShippedFileCitesACoverageFigure(unittest.TestCase):
    def test_no_shipped_file_states_a_repository_count(self):
        bad = []
        for p in shipped_files():
            lines = p.read_text(encoding="utf-8").split("\n")
            for n in figure_lines(p, COUNT_NEAR_REPO):
                bad.append(f"{p.relative_to(REPO_ROOT)}:{n}  {lines[n - 1].strip()[:100]}")
        self.assertEqual(
            [], bad,
            "a shipped file states a find_examples repository count. A coverage figure is "
            "VOLATILE server-side state — the count moves as repositories are indexed — so no "
            "count is citeable, and one pinned here goes stale on the server's schedule with "
            "nothing in this repo noticing. (The two sources also once disagreed; that was "
            "reported upstream and resolved by server 1.36.0, 2026-09-02. The prohibition "
            "does not depend on it.) Ask get_capabilities instead:\n  " + "\n  ".join(bad))

    def test_no_shipped_file_enumerates_the_stale_extension_list(self):
        bad = []
        for p in shipped_files():
            lines = p.read_text(encoding="utf-8").split("\n")
            for n in figure_lines(p, STALE_EXTENSIONS):
                bad.append(f"{p.relative_to(REPO_ROOT)}:{n}  {lines[n - 1].strip()[:100]}")
        self.assertEqual(
            [], bad,
            "a shipped file enumerates find_examples' indexed extensions ending at `.rs`. "
            "That truncated list omits the indexed .ts/.js, and an enumerated coverage list is "
            "volatile server-side state for the same reason a count is — it moves when the "
            "index gains a file type. Name the languages via get_capabilities rather than "
            "freezing an extension list:\n  " + "\n  ".join(bad))

    def test_the_scan_is_not_vacuous(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        self.assertGreater(len(shipped_files()), 40, "the shipped corpus went empty or tiny")
        self.assertTrue(COUNT_NEAR_REPO.search("indexes 37 Senzing GitHub repositories"),
                        "the count matcher no longer detects the claim it exists for")
        self.assertTrue(STALE_EXTENSIONS.search("Indexes source code (.py, .java, .cs, .rs)"),
                        "the extension matcher no longer detects the stale list")

    def test_a_wrapped_figure_is_caught_at_its_first_line(self):
        """Negative control (#424): the number ends line 2 and its noun begins line 3."""
        wrapped = ("Use find_examples for code.\nIt indexes 37\nSenzing GitHub repositories, "
                   "and the chunk count is ~9999\nchunks.\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapped.md"
            path.write_text(wrapped, encoding="utf-8")
            self.assertEqual([2], figure_lines(path, COUNT_NEAR_REPO))
            self.assertEqual([3], figure_lines(path, re.compile(r"~?\d[\d,]*\s+chunks")))
        # The old line-at-a-time scan, kept only to show the fixture is the hard case.
        for pattern in (COUNT_NEAR_REPO, re.compile(r"~?\d[\d,]*\s+chunks")):
            self.assertFalse(any(pattern.search(l) for l in wrapped.split("\n")))

    def test_the_exemption_is_narrow(self):
        """⛔ The marker must not become a file-wide opt-out — but it need not exist at all.

        ⚠️ **Rescoped 2026-09-02.** This also asserted `scanned < total`, i.e. that the
        exemption marker is present and exempting something. That premise expired: the marker
        existed because ground-rules.md quoted the stale declared description in order to call
        it stale, and the disagreement was resolved upstream by server 1.36.0. Ground-rules now
        illustrates INV-280 with a live pair that trips neither pattern, so **no exemption is
        needed and its absence is the correct end state** — not a guard failing open. What
        survives is the real rule: if a marker IS present, it covers one quoting paragraph and
        never a region.
        """
        gr = PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding" / "ground-rules.md"
        total = len(gr.read_text(encoding="utf-8").splitlines())
        scanned = len(scannable_lines(gr))
        self.assertGreater(
            scanned, total - 15,
            f"the quoted-history exemption is skipping {total - scanned} lines of "
            "ground-rules.md; it is meant to cover one quoting paragraph, not a region")

    def test_the_current_list_is_not_flagged(self):
        """The complete list is fine to write — only the truncated one is stale."""
        self.assertFalse(STALE_EXTENSIONS.search(".py, .java, .cs, .rs, .ts, .js"),
                         "the matcher flags the CURRENT extension list, which would push an "
                         "editor into deleting a correct sentence")


class TheLiveIllustrationStaysCheckable(unittest.TestCase):
    """The rule outlives its examples — so each example must say when it was last true.

    The `find_examples` disagreement INV-280 was written from was resolved upstream between
    server 1.33.0 and 1.36.0, and nothing in this repo noticed: two shipped sites went on
    asserting it in the present tense, and this guard's own failure messages gave the resolved
    disagreement as the reason for a prohibition that has a better one. The fix is not a
    once-off correction — it is that every illustrating example carries the server version and
    date it was checked, so the *next* resolution costs a correction note instead of shipping a
    false claim.

    ⚠️ This deliberately does NOT assert that the live pair contradicts itself. The current
    illustration is `search_docs`' declared chunk count against a live
    `documents_indexed` figure, which may simply be different units — and that is enough for
    INV-280, whose subject is a coverage figure a caller cannot act on, not only one in outright
    conflict. Asserting a contradiction would pin a stronger claim than the evidence supports.
    """

    def test_ground_rules_dates_its_live_illustration(self):
        gr = PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding" / "ground-rules.md"
        flat = re.sub(r"\s+", " ", gr.read_text(encoding="utf-8"))
        self.assertIn(
            "The live illustration", flat,
            "INV-280's passage must name a CURRENT illustration, not only the historical one — "
            "a rule whose only example is resolved reads as resolved")
        self.assertRegex(
            flat, r"live illustration, same server and date",
            "the live illustration must be tied to the server version and date it was observed")
        self.assertIn(
            "documents_indexed", flat,
            "the live pair is the declared chunk figure against the response's "
            "documents_indexed; name the field so the next reader can re-ask it")

    def test_the_units_caveat_is_present_so_the_claim_is_not_overstated(self):
        gr = PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding" / "ground-rules.md"
        flat = re.sub(r"\s+", " ", gr.read_text(encoding="utf-8"))
        self.assertRegex(
            flat, r"not necessarily contradictory — they may simply be different units",
            "the live pair must not be presented as a contradiction it may not be; the rule "
            "rests on the figure being unactionable, which is the weaker and true claim")

    def test_the_live_illustration_quotes_neither_figure(self):
        """INV-280 — the illustration names the two fields, never the numbers they carry.

        It once quoted the declared chunk count and a live `documents_indexed` value; the
        latter had already moved by the next re-check (server 1.37.15, 2026-09-28), which is
        the rule's own reason. Negative-controlled by restoring either number.
        """
        figure = re.compile(r"~?\d[\d,]*\s+chunks|documents_indexed`?:\s*\d")
        bad = []
        for p in shipped_files():
            lines = p.read_text(encoding="utf-8").split("\n")
            for n in figure_lines(p, figure):
                bad.append(f"{p.relative_to(REPO_ROOT)}:{n}  {lines[n - 1].strip()[:100]}")
        self.assertEqual(
            [], bad,
            "a shipped file quotes a search_docs coverage figure. The server states the "
            "corpus size two ways, so neither number is citeable (INV-280); name the field "
            "and let the reader re-ask it:\n  " + "\n  ".join(bad))
        self.assertTrue(figure.search('corpus is *"~9999 chunks"*'),
                        "the matcher no longer detects a declared chunk count")
        self.assertTrue(figure.search("`metadata.documents_indexed: 9999`"),
                        "the matcher no longer detects a quoted documents_indexed value")

    def test_the_resolved_example_is_marked_as_history_everywhere_it_appears(self):
        """No shipped file may assert the resolved disagreement in the present tense."""
        offenders = []
        for path in sorted(PLUGIN.rglob("*.md")):
            if "__pycache__" in str(path):
                continue
            flat = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
            if "declared description" not in flat:
                continue
            if re.search(r"declared description\s+disagrees with it", flat):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            [], offenders,
            "these files still say find_examples' declared description DISAGREES with "
            "get_capabilities, in the present tense. Re-checked on server 1.36.0, 2026-09-02: "
            "they agree on count, extensions and languages. State it as dated history:\n  "
            + "\n  ".join(offenders))


class ThePluginRecordsWhichSourceGoverns(unittest.TestCase):
    def test_ground_rules_separates_parameters_from_coverage(self):
        """INV-234 is right about parameters and must not be read as endorsing stale prose."""
        gr = PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding" / "ground-rules.md"
        flat = re.sub(r"\s+", " ", gr.read_text(encoding="utf-8")).lower()
        self.assertIn("inv-234", flat)
        self.assertRegex(
            flat,
            r"authoritative for the parameters a tool accepts — not for prose",
            "ground-rules.md does not distinguish declared-schema authority over accepted "
            "parameters from get_capabilities' authority over coverage prose, so the INV-234 "
            "passage still reads as endorsing whatever the manifest says")
        self.assertIn("get_capabilities` governs", flat.replace("**", ""),
                      "ground-rules.md does not name which source governs for coverage")

    def test_the_contested_fact_is_recorded_where_the_index_is_quoted(self):
        """INV-183 — reachable at the step that quotes it, not only in ground-rules."""
        pa = (PLUGIN / "senzing-bootcamp" / "skills" / "module-06-data-processing"
              / "phaseA-build-loading.md")
        flat = re.sub(r"\s+", " ", pa.read_text(encoding="utf-8"))
        self.assertIn("get_capabilities", flat)
        self.assertIn("index.ts", flat,
                      "the note does not name the live .ts result that settled the "
                      "disagreement, so a reader cannot tell it was measured rather than argued")
        # ⚠️ Rescoped 2026-09-02: this pinned "2026-08-28", the date the disagreement was
        # last CONFIRMED. After the upstream fix landed, the date a reader acts on is the
        # RE-CHECK date — pinning the older one would have kept the guard green while the
        # note said the two sources still disagree. Require the re-check date; the historical
        # evidence is still required by the index.ts assertion above.
        self.assertIn("2026-09-02", flat,
                      "the contested-fact note does not carry the date its claim was last "
                      "re-checked against the server, so nobody can tell whether the "
                      "disagreement it describes still exists (INV-080)")
        self.assertRegex(
            flat, r"1\.36\.0",
            "the note must name the server version the re-check ran against, not only the "
            "version the original disagreement was observed on")


if __name__ == "__main__":
    unittest.main()
