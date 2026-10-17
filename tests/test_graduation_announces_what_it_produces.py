"""Every artifact graduation is instructed to produce is named in its closing announcement.

Graduation is terminal. Its "Mandatory closing step" is the last thing the bootcamper reads, so
an artifact the flow writes and that step never names is one they never learn they have — which
is, from their side, indistinguishable from one that was never produced.

That happened. `render-any-bootcamp-document-as-a-styled-pdf` added Step 5b, which renders
`docs/business_problem.pdf` and `docs/data_source_evaluation.pdf` and tells the guide to "name the
ones that succeeded in the closing summary alongside the recap PDF". No such naming existed: the
closing step listed the recap and `production/` only, and the two PDFs appeared nowhere else in the
plugin. The spec's own criteria named the closing summary twice and its Affected files named it
explicitly; only the render step shipped.

It is the **third** recorded instance of one failure mode — a criterion naming a second consumer
where only the first was built (`relocate-integration-deployment-questions-to-module1`,
`defer-commonmark-to-graduation`, then this) — and INV-182 was written after the first two and did
not prevent the third. Nothing mechanical could: `coverage_reports.py affected` compares a spec's
predicted paths against the entry's `Files changed:` list, and `graduation/SKILL.md` *was* in that
list. It was touched, just not at the second site.

So this closes the class rather than the instance. It reads the `--output` paths out of
graduation's own bash blocks and requires each to be named in the closing step — so the *next*
artifact added to graduation cannot repeat it.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRADUATION = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "graduation" / "SKILL.md"

#: The closing step's heading. Everything from here to the end is what the bootcamper is told.
CLOSING_HEADING = "## Mandatory closing step"

#: Artifacts graduation produces that are announced elsewhere by design, with the reason.
#: `production/`'s own files are named as a group ("its GRADUATION_REPORT.md and
#: MIGRATION_CHECKLIST.md") rather than by path, and the revisit bundle under `backups/revisit/`
#: is deliberately silent (INV-094 — "a silent, non-blocking revisit/resume bundle").
ANNOUNCED_AS_A_GROUP = ("GRADUATION_REPORT.md", "MIGRATION_CHECKLIST.md")


def text():
    return GRADUATION.read_text(encoding="utf-8")


def closing_step():
    body = text()
    start = body.find(CLOSING_HEADING)
    assert start > 0, "the closing step's heading has changed; this test would be vacuous"
    return body[start:]


def render_step():
    """Step 5b — the step that renders the keepsake documents."""
    body = text()
    start = body.find("## Step 5b:")
    assert start > 0, "Step 5b's heading has changed; this test would be vacuous"
    end = body.find("\n## ", start + 1)
    return body[start:end if end > start else len(body)]


def produced_outputs():
    """PDFs graduation is instructed to produce, derived rather than hardcoded.

    Two sources, unioned, because one alone is not enough:

    - **`--output` targets** in graduation's bash blocks.
    - **Step 5b's own list of source documents**, mapped `.md` -> `.pdf`. Step 5b shows *one*
      worked invocation and names the second document only as `docs/<name>.md` in prose, saying
      "Render each" — so an `--output`-only derivation finds one of the two artifacts.

    That mattered: the first version of this guard swept `--output` alone, returned
    `['docs/business_problem.pdf']`, and passed while `docs/data_source_evaluation.pdf` was
    dropped from the announcement. A guard narrower than the property it claims is the defect
    class `production-readiness-audit` Step 7 item 3 exists for, and it was reached here by
    deriving from the *example* rather than from what the step says it does.
    """
    outputs = {m.group(1) for m in re.finditer(r"--output\s+(\S+\.pdf)", text())}
    for m in re.finditer(r"`(docs/[A-Za-z0-9_]+)\.md`", render_step()):
        outputs.add(m.group(1) + ".pdf")
    return sorted(outputs)


class TheScanIsNotVacuous(unittest.TestCase):
    def test_graduation_ships(self):
        self.assertTrue(GRADUATION.is_file())

    def test_the_closing_step_is_locatable(self):
        self.assertIn("closing announcement", closing_step())

    def test_output_paths_are_found(self):
        found = produced_outputs()
        self.assertGreaterEqual(
            len(found), 2,
            "fewer than two produced artifacts found (%s) — the derivation has narrowed and this "
            "guard would pass while an artifact goes unannounced, which is exactly how its first "
            "version failed" % found,
        )
        for expected in ("docs/business_problem.pdf", "docs/data_source_evaluation.pdf"):
            self.assertIn(expected, found)


def instruction_region():
    """The closing step's normative text — everything before the example.

    Checked separately from the example on purpose: a mutation that dropped one artifact from the
    instruction while the example kept it passed a whole-section presence check, because the
    section contains the example. The instruction is what the guide is told to do; the example is
    what it pattern-matches. Both must name every artifact, so both are asserted.
    """
    closing = closing_step()
    cut = closing.find("Example (list only what exists)")
    assert cut > 0, "the example's caption has changed; this slice would be wrong"
    return closing[:cut]


class EveryProducedArtifactIsAnnounced(unittest.TestCase):
    def test_each_output_path_is_named_in_the_instruction(self):
        instruction = instruction_region()
        missing = [p for p in produced_outputs() if p not in instruction]
        self.assertEqual(
            [], missing,
            "graduation writes these and the closing step's instruction never names them — "
            "graduation is terminal, so the bootcamper never learns they exist:\n  "
            + "\n  ".join(missing),
        )

    def test_the_recap_pdf_is_still_named(self):
        """The artifact that was always announced; if this breaks, the slice is wrong."""
        self.assertIn("docs/bootcamp_recap.pdf", closing_step())

    def test_the_example_models_the_full_list(self):
        """A guide pattern-matches the example. An example naming fewer artifacts than the
        instruction teaches the shorter list."""
        closing = closing_step()
        start = closing.find("Example (list only what exists)")
        self.assertGreater(start, 0, "the example's caption has changed")
        example = closing[start:closing.find("\n\n", closing.find(">", start))]
        for path in produced_outputs():
            with self.subTest(artifact=path):
                self.assertIn(path, example)


class TheAnnouncementStaysConditional(unittest.TestCase):
    """Announcing a PDF that was not produced is worse than not announcing one that was."""

    def test_the_instruction_names_only_what_exists(self):
        self.assertRegex(closing_step(),
                         r"(?i)naming only the artifacts confirmed to exist")

    def test_the_new_pdfs_are_explicitly_conditional(self):
        closing = closing_step()
        self.assertRegex(closing, r"(?i)each only if it exists|only if it exists")
        self.assertRegex(closing, r"(?i)absent or refused .{0,40}not\s+named|simply not\s*named")

    def test_it_names_the_rule_the_conditional_rests_on(self):
        """Item 1's own rule, not INV-048: INV-048 governs the recap PDF, and these two
        keepsakes are not it (#607, finished by #685)."""
        self.assertRegex(closing_step(),
                         r"(?i)item 1's rule that you never announce an artifact you have "
                         r"not confirmed exists")
        self.assertNotIn("INV-048", closing_step())

    def test_the_example_is_captioned_as_conditional(self):
        self.assertIn("list only what exists", closing_step())


class Step5bDelegationResolves(unittest.TestCase):
    """Step 5b says "name them in the closing summary". That target must exist (INV-182)."""

    def test_step5b_delegates_to_the_closing_summary(self):
        self.assertRegex(text(), r"(?i)in the closing summary alongside the recap PDF")

    def test_the_site_it_delegates_to_names_both_documents(self):
        closing = closing_step()
        for path in ("docs/business_problem.pdf", "docs/data_source_evaluation.pdf"):
            with self.subTest(artifact=path):
                self.assertIn(path, closing,
                              "Step 5b delegates naming to the closing step, which does not "
                              "name %s" % path)


if __name__ == "__main__":
    unittest.main()
