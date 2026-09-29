"""The step-3 name rejection is documented as a declaration fix, not as a data defect.

`mapping_workflow` step 3 rejects a source that declares both organization and person name
fields, with (server 1.37.15, 2026-09-29; the attribute list names what the mapping declared):

    NAME_ORG cannot co-exist with person name attributes NAME_FIRST, NAME_LAST — a record is
    either a person or an organization. FIX: declare the name ONCE and let the mapper emit
    NAME_ORG for an ORGANIZATION record and NAME_FULL (or parsed person parts) for a PERSON
    record, branched by RECORD_TYPE; or use a type_discriminator to make the mapping
    conditional.

⛔ **The rule is right about records and was applied to field DECLARATIONS.** Two sources
hit it on 2026-08-25 whose fields were verified disjoint — one populated per record, chosen
by `RECORD_TYPE`, zero rows carrying both — and the same rejection was hit independently on
2026-08-27. Where the type comes from a field value, the fix is to declare the names through
`type_discriminator.field_overrides`, including where the override is identity in both branches.

⚠️ **The authoritative scope is narrower than the message.** The Entity Specification's
`Feature: NAME` section says *"do not mix `NAME_ORG` with parsed person fields **in the same
object**"* (`search_docs(category='data_mapping')`, server 1.33.0, 2026-08-28) — one NAME
feature object. The message asserts a record-level rule; the validator enforces at
declaration level. Three different scopes, and the two that are written down disagree.

⚠️ **The cost is a misdirected first attempt.** "A record is either a person or an
organization" reads as *your data is wrong*, so the natural response is to re-check the data
— which is correct — rather than to change the declaration. Through server 1.33.0 the message
carried no fix at all. Since then its `FIX:` clause names two routes (declare the name once, or a
`type_discriminator`), but not `field_overrides` or the identity override, so this guard's core
assertion is still that the plugin's caution names them (#220).

⚠️ **The windows are measured from the END of the quote's fence, not from its first words
(#220, INV-219).** They used to start at `NAME_ORG cannot co-exist`, so the quote's own length
counted against them. Refreshing the quote to the 1.37.15 message, `FIX:` clause included,
pushed the "do not pre-emptively emit" caution past its 1600-character window with nothing in
the caution changed. Measuring from the closing fence makes the windows independent of the
server's wording. The last window is 2000 characters because #220 also added the field-value
route sentence to the block. Every assertion keeps its meaning: the same phrases, in the caution
that follows the quote. `test_the_quote_carries_a_server_version_and_date` requires the lead-in
to date the quote, and pins no word of the message.

⚠️ What this does NOT establish: that the server still rejects. That is runtime behavior of
one workflow step, unreachable offline (INV-108), and it was deliberately **not** re-driven
during triage — reaching step 3 requires completing steps 1-2 against a real multi-source
project. It rests on two field observations on this server version.

Source spec: `specs/mapping-step3-rejects-disjoint-name-declarations.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins"


def flatten(text):
    return re.sub(r"\s+", " ", text).lower()


def caution_after_quote(flat, size):
    """The `size` characters after the closing fence of the quoted rejection.

    Measured from the fence's end, so the quote's own length never counts against the window.
    """
    i = flat.index("name_org cannot co-exist")
    j = flat.find("```", i)
    start = j + 3 if j >= 0 else i
    return flat[start:start + size]


def lead_in_before_quote(flat):
    """The text just before the quote's opening fence, where its provenance is stated."""
    i = flat.index("name_org cannot co-exist")
    fence = flat.rfind("```", 0, i)
    end = fence if fence >= 0 else i
    return flat[max(0, end - 400):end]


def mapping_files():
    """Shipped files that drive `mapping_workflow` step 3 — derived, not hardcoded."""
    return sorted(p for p in PLUGIN.rglob("*.md")
                  if "__pycache__" not in p.parts
                  and "schema_mappings" in p.read_text(encoding="utf-8"))


class TheRejectionIsDocumentedAsADeclarationFix(unittest.TestCase):
    def test_a_step3_site_is_found(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        self.assertTrue(
            mapping_files(),
            "no shipped file drives mapping_workflow step 3 any more; the scan broke or the "
            "payload key was renamed. Re-derive it rather than deleting this guard")

    def test_the_rejection_is_named(self):
        hits = [p for p in mapping_files() if "name_org cannot co-exist" in flatten(
            p.read_text(encoding="utf-8"))]
        self.assertTrue(
            hits,
            "no shipped file quotes the step-3 name rejection, so a guide meeting it has "
            "nothing to match against and will read it as a data defect")

    def test_type_discriminator_is_named_as_the_fix(self):
        """⛔ The load-bearing assertion: the message never says this, so the plugin must."""
        for p in mapping_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            if "name_org cannot co-exist" not in flat:
                continue
            window = caution_after_quote(flat, 1200)
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("type_discriminator.field_overrides", window,
                              "the caution quotes the rejection without naming "
                              "type_discriminator.field_overrides as the fix")
                self.assertIn("identity", window,
                              "the caution does not say the override may be identity in both "
                              "branches, which is the non-obvious half of the workaround")

    def test_the_message_is_not_repeated_as_though_it_were_true_of_the_data(self):
        """It must be framed as a declaration problem, not as 'your data is wrong'."""
        for p in mapping_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            if "name_org cannot co-exist" not in flat:
                continue
            window = caution_after_quote(flat, 1400)
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertRegex(
                    window, r"declare it differently|about the \*field\s*declarations\*|"
                            r"field\s*\*?\*?declarations",
                    "the caution does not tell the reader the rejection is about the "
                    "declarations rather than the data, which is the whole misdirection")

    def test_the_coverage_consequence_is_referenced_not_restated(self):
        """INV-179 — the field-count note already owns this; point at it."""
        for p in mapping_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            if "name_org cannot co-exist" not in flat:
                continue
            window = caution_after_quote(flat, 1600)
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertRegex(
                    window, r"field-count warning|counted by nothing",
                    "the caution does not warn that coverage drops after the workaround, so "
                    "a Bootcamper reads the shortfall as unmapped data")

    def test_it_does_not_prescribe_a_blanket_type_discriminator(self):
        """⛔ The fix for a rejection must not become a default for every source."""
        for p in mapping_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            if "name_org cannot co-exist" not in flat:
                continue
            window = caution_after_quote(flat, 2000)
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertIn("do not pre-emptively emit a `type_discriminator`",
                              window.replace("**", ""),
                              "the caution does not rule out emitting a type_discriminator "
                              "everywhere, which would buy the coverage surprise for nothing")

    def test_the_quote_carries_a_server_version_and_date(self):
        """⛔ INV-080 — a quoted server message says which server said it, and when.

        Checks the lead-in's version and date shapes only, never the message's words (INV-219).
        """
        for p in mapping_files():
            flat = flatten(p.read_text(encoding="utf-8"))
            if "name_org cannot co-exist" not in flat:
                continue
            lead = lead_in_before_quote(flat)
            with self.subTest(file=str(p.relative_to(REPO_ROOT))):
                self.assertRegex(lead, r"\b\d+\.\d+\.\d+\b",
                                 "the quoted rejection carries no server version")
                self.assertRegex(lead, r"\b\d{4}-\d{2}-\d{2}\b",
                                 "the quoted rejection carries no date")


class TheWindowsAreMeasuredFromTheFence(unittest.TestCase):
    """Negative controls on synthetic text, so the rescoped windows are shown to discriminate."""

    QUOTE = ("server 1.37.15, 2026-09-29: ```text NAME_ORG cannot co-exist with person name "
             "attributes " + "x " * 400 + "```")

    def test_a_long_quote_does_not_push_the_caution_out(self):
        flat = flatten(self.QUOTE + " the fix is type_discriminator.field_overrides")
        self.assertIn("type_discriminator.field_overrides", caution_after_quote(flat, 1200))

    def test_a_caution_beyond_the_window_is_not_found(self):
        flat = flatten(self.QUOTE + " filler" * 400 + " type_discriminator.field_overrides")
        self.assertNotIn("type_discriminator.field_overrides", caution_after_quote(flat, 1200))

    def test_an_undated_quote_is_caught(self):
        flat = flatten("rejected with: ```text NAME_ORG cannot co-exist ```")
        lead = lead_in_before_quote(flat)
        self.assertNotRegex(lead, r"\b\d{4}-\d{2}-\d{2}\b")


if __name__ == "__main__":
    unittest.main()
