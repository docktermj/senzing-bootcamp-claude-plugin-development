"""Every path that reaches CORD tells the Bootcamper the records are real.

``get_sample_data``'s tool contract places a disclosure obligation on its caller:

    IMPORTANT: This is REAL data (not synthetic) — historical snapshots for evaluation
    only, not operational use. Always inform the user of this.

(verbatim from the live tool description, server 1.35.3, 2026-09-01)

The plugin never discharged it, and the one place it characterized CORD to the Bootcamper
said the opposite -- "curated, real-world-like datasets ... realistic data patterns", which
reads as *synthesized to resemble real data*. CORD is real credit, healthcare-provider,
federal-loan, beneficial-ownership and labor-enforcement records about named people and
organizations.

⚠️ This matters more here than in most callers. The Bootcamper loads these records locally,
queries named entities in Module 7, and the screenshot flow embeds those renderings into
``docs/bootcamp_recap.md`` -- which graduation turns into a keepsake PDF they are encouraged
to share with their team. Real individuals' names reach a shared artifact from a dataset the
Bootcamper was told was "real-world-like".

⚠️ The site set is DERIVED BY SCANNING for the paths that reach CORD (INV-246), not
hardcoded: the originating spec named two, and the scan found three -- Module 3b offers a
CORD substitute when the Truth Set is unavailable, reaching the data without passing through
Module 4's wording at all.

Enforces **INV-293** — a provider's disclosure obligation is met at every path that
ACQUIRES the data, in the turn that acquires or binds it.

⚠️ Scope matters here and the guard respects it: `get_sample_data` also serves the Truth
Set, which is Senzing's demo data and carries no such obligation. A file that references
already-acquired CORD, or routes to the tool, acquires nothing. Asserting the disclosure
everywhere the tool is named would demand a false statement about the Truth Set.

Stdlib only; nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"
CANONICAL = SKILLS / "module-04-data-collection" / "SKILL.md"

#: A file ACQUIRES CORD when it recommends it as a source, binds a scenario to it, or offers
#: it as a substitute. The obligation rides on `get_sample_data`'s caller, so acquisition is
#: the property -- not mention.
#:
#: ⚠️ An earlier version matched any 👉 naming CORD and flagged
#: `module-05-data-quality-mapping/phase1-quality-assessment.md`, whose question asks about a
#: source the Bootcamper ALREADY HAS ("Your CORD source [SOURCE_NAME] is already in
#: Senzing-loadable form…"). That module cites `get_sample_data` only for response SHAPE and
#: says outright the data was "obtained via the `get_sample_data` MCP tool in Module 4". A
#: guard that demanded the disclosure there would push a repeat of it into a module where the
#: data is long since on disk. Narrowed to the claim and pinned below as a must-not-match.
REACHES_CORD = (
    re.compile(r"Senzing provides \*\*CORD"),
    re.compile(r"provenance\s+`cord`"),
    re.compile(r"👉[^\n]*\bCORD collection\b"),
)
#: Pinned must-not-match: consumers of already-acquired CORD data.
CONSUMES_NOT_ACQUIRES = (
    "module-05-data-quality-mapping/phase1-quality-assessment.md",
)
#: The disclosure, by its three claims rather than by one sentence: real, snapshot, not operational.
DISCLOSES = (
    re.compile(r"(?i)\breal\b[^.\n]{0,80}\brecords\b|\brecords\b[^.\n]{0,80}\breal\b"),
    re.compile(r"(?i)historical snapshots?"),
    re.compile(r"(?i)not (?:for )?operational use|evaluation rather than operational"),
)
#: A file may discharge it by pointing at the canonical block instead of restating it.
POINTS_AT_CANONICAL = re.compile(r"module-04-data-collection/SKILL\.md")


def shipped_markdown():
    return sorted(SKILLS.rglob("*.md"))


#: The real-data notice's wording, which a 👉 must not carry.
NOTICE = re.compile(r"(?i)historical snapshot|not operational|real data")
#: The same, after a 👉 in the same Markdown block and before any other 👉, matched by
#: ``match_lines`` on whitespace-collapsed blocks so a question that wraps is still read (#424).
NOTICE_QUESTION = re.compile(r"(?i)👉[^👉]*?(?:historical snapshot|not operational|real data)")


def notice_questions(text):
    """1-based lines of each 👉 that carries the notice's wording.

    The line check reads the whole line holding a 👉, as it did before #424; ``match_lines``
    adds a question whose wording wraps onto the next line, which the line check cannot see.
    """
    hits = {n for n, line in enumerate(text.split("\n"), 1)
            if "👉" in line and NOTICE.search(line)}
    return sorted(hits | set(match_lines(text, NOTICE_QUESTION)))


def enclosing_section(text, pos):
    """The Markdown section containing ``pos`` -- previous heading to the next of any depth.

    ⚠️ Scoping matters more than it looks. Checked against the whole FILE, three of the five
    negative controls passed while the disclosure was deleted: Module 1 and Module 3b both
    reference `module-04-data-collection/SKILL.md` elsewhere for unrelated reasons, so a
    file-level "points at the canonical wording" test was satisfied by a link that has
    nothing to do with CORD. A disclosure the Bootcamper never sees is not a disclosure.
    """
    starts = [m.start() for m in re.finditer(r"(?m)^#{1,5} ", text) if m.start() <= pos]
    start = starts[-1] if starts else 0
    nxt = re.search(r"(?m)^#{1,5} ", text[pos:])
    end = pos + nxt.start() if nxt else len(text)
    return text[start:end]


def files_reaching_cord():
    """[(path, acquisition-site section)] -- the section, never the whole file."""
    hits = []
    for md in shipped_markdown():
        text = md.read_text(encoding="utf-8")
        for pattern in REACHES_CORD:
            m = pattern.search(text)
            if m:
                hits.append((md, enclosing_section(text, m.start())))
                break
    return hits


def canonical_block(text):
    """Module 4's Bootcamper-facing CORD blockquote -- the lines actually shown to them.

    ⚠️ Also scoped deliberately: the guidance beside it QUOTES the tool contract, so a
    whole-file check passed with the disclosure stripped out of the block the Bootcamper
    reads. The obligation is to inform them, not to record the obligation nearby.

    The lines are only gathered here; the claims are matched on the whole block, so this is
    no line-at-a-time read (#424).
    """
    i = text.index('> "Senzing provides **CORD')
    lines = []
    for line in text[i:].split("\n"):
        if not line.startswith(">"):
            break
        lines.append(line)
    return "\n".join(lines)


class CordIsNeverDescribedAsSynthetic(unittest.TestCase):
    def test_no_file_calls_cord_real_world_like(self):
        """⚠️ Self-pinning: the one line that FORBIDS the phrase must not trip the scan.

        The prohibition has to quote the banned wording to be followable, so an exemption
        is unavoidable; it is scoped to a line that also forbids it rather than to a file,
        so a new descriptive use in the same file is still caught.

        Line-scoped by design (#424): "real-world-like" is one hyphenated token, which a line
        break cannot split.
        """
        offenders = []
        for md in shipped_markdown():
            for lineno, line in enumerate(md.read_text(encoding="utf-8").split("\n"), 1):
                if "real-world-like" not in line:
                    continue
                if re.search(r"(?i)never describe|do not describe|forbidden", line):
                    continue
                offenders.append("%s:%d" % (md.relative_to(REPO), lineno))
        self.assertEqual(
            [], offenders,
            "CORD must never be described as 'real-world-like'. It reads as synthesized-to-"
            "resemble-real, and the records are real people. Offenders: %s" % offenders,
        )

    def test_the_canonical_block_makes_all_three_claims(self):
        text = canonical_block(CANONICAL.read_text(encoding="utf-8"))
        for pattern in DISCLOSES:
            with self.subTest(claim=pattern.pattern[:40]):
                self.assertRegex(
                    text, pattern,
                    "Module 4's CORD block must state all three parts of the tool's required "
                    "disclosure: the data is real, it is a historical snapshot, and it is for "
                    "evaluation rather than operational use. Two of three still leaves the "
                    "Bootcamper with a wrong belief about what they are loading.",
                )


class EveryPathThatReachesCordDischargesTheDisclosure(unittest.TestCase):
    def test_the_scan_finds_more_than_one_path(self):
        """A scan matching only the canonical file would make the next test vacuous."""
        found = files_reaching_cord()
        self.assertGreaterEqual(
            len(found), 3,
            "Fewer than three CORD-reaching paths found. The scan is how this guard avoids "
            "certifying only the sites its author thought of (INV-246) -- if the patterns "
            "stopped matching, fix them rather than trusting the shorter list. Found: %s"
            % [str(p.relative_to(REPO)) for p, _ in found],
        )

    def test_a_consumer_of_already_fetched_cord_is_not_a_disclosure_site(self):
        """⚠️ The other side of the discrimination, pinned so a widening cannot swallow it.

        Module 5 works on CORD data Module 4 already fetched. Demanding the disclosure there
        would restate it to a Bootcamper who has had the files on disk for two modules --
        which INV-006/INV-012 argue against, and which is what the first version of this
        matcher would have required.
        """
        acquiring = {str(md.relative_to(SKILLS)) for md, _ in files_reaching_cord()}
        for consumer in CONSUMES_NOT_ACQUIRES:
            self.assertNotIn(
                consumer, acquiring,
                "%s consumes CORD data that Module 4 acquired; it is not an acquisition "
                "path and must not be required to repeat the disclosure. If the matcher "
                "started flagging it, the matcher widened -- fix the matcher." % consumer,
            )

    def test_every_path_says_the_data_is_real(self):
        """The load-bearing half, required at EVERY acquisition site with no delegation.

        ⚠️ Delegation was originally allowed for the whole disclosure, and two negative
        controls walked straight through it: deleting the disclosure from Module 1 and
        Module 3b left both green, because each section happens to cross-reference
        `module-04-data-collection/SKILL.md` for an unrelated reason (Module 1 points there
        for where synthesized files get generated). A pointer that is not about the
        disclosure is not a disclosure, so the one sentence that corrects the Bootcamper's
        belief is now required in place.
        """
        real_claim = DISCLOSES[0]
        for md, section in files_reaching_cord():
            with self.subTest(file=md.relative_to(REPO)):
                self.assertRegex(
                    section, real_claim,
                    "%s acquires CORD data without saying the records are real. That is the "
                    "sentence the whole fix turns on: 'Always inform the user of this' binds "
                    "every caller, and a path that skips it leaves the Bootcamper believing "
                    "the named people are fabricated." % md.relative_to(REPO),
                )

    def test_each_path_states_the_rest_or_points_at_the_canonical_wording(self):
        """Snapshot and evaluation-only MAY be delegated -- restating them everywhere is bloat."""
        for md, section in files_reaching_cord():
            with self.subTest(file=md.relative_to(REPO)):
                states_it = all(p.search(section) for p in DISCLOSES[1:])
                points = POINTS_AT_CANONICAL.search(section)
                self.assertTrue(
                    states_it or points,
                    "%s states neither the historical-snapshot and evaluation-only clauses "
                    "nor a pointer to Module 4's canonical wording." % md.relative_to(REPO),
                )


class TheDisclosureIsAStatementAndTheFetchRulesAreUntouched(unittest.TestCase):
    """The spec's fourth criterion, plus INV-012: inform, do not gate."""

    def setUp(self):
        self.text = CANONICAL.read_text(encoding="utf-8")

    def test_no_question_asks_the_bootcamper_about_the_real_data_notice(self):
        self.assertEqual(
            [], notice_questions(self.text),
            "The disclosure is a statement, never a 👉. They have already chosen sample "
            "data; a question here asks something with no action behind it (INV-012), and "
            "adds a gate the plugin's question economy argues against.",
        )

    def test_a_wrapped_notice_question_is_caught(self):
        """Negative control (#424): "real" ends line 1 and "data" begins line 2."""
        wrapped = "👉 **Do you understand that this is real\ndata about real people?**\n"
        self.assertEqual([1], notice_questions(wrapped))
        # The old line-at-a-time check, kept only to show the fixture is the hard case.
        self.assertFalse(any("👉" in l and NOTICE.search(l) for l in wrapped.split("\n")))

    def test_the_notice_as_a_statement_beside_a_question_is_not_flagged(self):
        """Must-not-flag (INV-282): the notice is stated in its own paragraph, then the 👉."""
        self.assertEqual([], notice_questions(
            "These are real records: historical snapshots, not for operational\nuse.\n\n"
            "👉 **Which source should we load first?**\n"))

    def test_the_existing_fetch_url_guidance_survives(self):
        for phrase in ("source_download_url", "download_url"):
            self.assertIn(
                phrase, self.text,
                "Rewriting the CORD block must not disturb the fetch-URL guidance beside it, "
                "which distinguishes the preview URL from the complete uncapped file.",
            )
        self.assertRegex(
            self.text, r"(?i)exactly as (?:the tool gives it|given|returned)",
            "The 'present the fetch URL exactly as returned' rule must survive unchanged.",
        )


if __name__ == "__main__":
    unittest.main()
