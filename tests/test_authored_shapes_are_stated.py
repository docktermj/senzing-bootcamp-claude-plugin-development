"""Every Markdown shape a bundled generator keys on is stated where the guide authors it.

INV-242 binds all shipped prose, but the guard written with it checked one site: the recap's
image line. This file widens it to the rule's actual surface.

**Scope is Markdown, deliberately.** The bundled scripts also parse `bootcamp_progress.json`,
`bootcamp_preferences.yaml` and `data_sources.yaml`, and those are out of scope here because a
shape mismatch in them is **loud** — the stdlib parser raises and the step fails visibly. INV-242
exists for the silent case, which is a Markdown property: the document still renders, still looks
right to a human reader, and simply loses the treatment it was written to get. Two Markdown
surfaces qualify:

    docs/bootcamp_recap.md              <- bootcamp-onboarding/module-completion.md
    docs/bootcamp_data_discoveries.md   <- module-07.../phase1-query-visualize.md

The allowlists are read **from the generators themselves** rather than restated here, so adding a
label to `_NEW_LINE_LABELS` without telling the guide how to write it fails this file. A hardcoded
copy would drift the moment someone edited the generator, which is the whole defect class.

Found by taking INV-242's breadth seriously, 2026-08-14: the recap side was already compliant
(`module-completion.md` states `**Why it matters:**` four times), while the discoveries side
stated **neither** of its two labels in the form the generator keys on. Section 4 said to include
"at least one **near-miss**" and section 6 said "State the measurement" — both accurate prose, and
neither the `**Label:**` shape that triggers the layout. A guide following them wrote
"One near-miss: ..." and silently got inline rendering.

⚠️ Note `**Near-miss:**` alone does **not** match: `_normalize` maps it to `near miss`, and the
allowlist entry is `near miss the one that teaches more`. The parenthetical is load-bearing, which
is exactly the kind of detail INV-242 requires the instruction to state rather than leave to the
guide to infer.

Enforces **INV-242** — prose instructing the guide to author content a bundled script must parse states the shape that script accepts.

Source spec: `specs/recap-screenshots-in-bullets-never-reach-the-pdf.md` (INV-242's origin);
widened on maintainer review, 2026-08-14.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins" / "senzing-bootcamp"
SCRIPTS = PLUGIN / "scripts"
SKILLS = PLUGIN / "skills"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: both generators define @dataclass types, and dataclasses
    # resolves each class's module out of sys.modules while decorating it.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RECAP = load("recap_shapes_under_test", SCRIPTS / "generate_recap_pdf.py")
DISCOVERIES = load("discoveries_shapes_under_test", SCRIPTS / "generate_discoveries_pdf.py")

#: (generator, its normalizer, the instruction that tells the guide to author its input)
SURFACES = [
    (
        "bootcamp_recap.md",
        RECAP,
        RECAP._normalize_heading,
        SKILLS / "bootcamp-onboarding" / "module-completion.md",
    ),
    (
        "bootcamp_data_discoveries.md",
        DISCOVERIES,
        DISCOVERIES._normalize,
        SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md",
    ),
]


def squash(path):
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def bold_labels(text):
    """Every `**Label:**` the instruction actually writes out, normalized-ready."""
    return re.findall(r"\*\*([^*]+?):\*\*", text)


class EveryAllowlistedLabelIsStatedWhereItIsAuthored(unittest.TestCase):
    """The load-bearing check, and the one that found the gap.

    A label in `_NEW_LINE_LABELS` gets layout no other label gets. If the instruction never
    shows that exact form, the guide writes an equivalent-looking one and loses it silently.
    """

    def test_each_allowlisted_label_appears_in_its_instruction(self):
        for name, generator, normalize, instruction in SURFACES:
            allowlist = generator._NEW_LINE_LABELS
            self.assertTrue(allowlist, "%s: empty allowlist makes this test vacuous" % name)
            stated = {normalize(label) for label in bold_labels(squash(instruction))}
            for entry in allowlist:
                with self.subTest(surface=name, label=entry):
                    self.assertIn(
                        entry, stated,
                        "%s keys on the label %r for special layout, and %s never writes it "
                        "as a `**Label:**` — the guide cannot produce a shape it is not shown "
                        "(INV-242)" % (name, entry, instruction.name),
                    )

    def test_the_normalizer_round_trips_the_stated_forms(self):
        """Guards the subtle half: a near-miss spelling that normalizes to something else."""
        allowlist = DISCOVERIES._NEW_LINE_LABELS
        self.assertIn(
            DISCOVERIES._normalize("Near-miss (the one that teaches more)"), allowlist
        )
        self.assertNotIn(
            DISCOVERIES._normalize("Near-miss"), allowlist,
            "if the bare label started matching, the instruction's warning about the "
            "parenthetical would be wrong and must be updated with it",
        )

    def test_the_discoveries_instruction_warns_the_parenthetical_matters(self):
        """Stating the form is not enough when a shorter form looks equally correct."""
        text = squash(SURFACES[1][3])
        self.assertIn("`**Near-miss:**` alone", text)


class TheSectionHeadingsTheGeneratorChecksAreStated(unittest.TestCase):
    """The discoveries generator audits by section name; the instruction lists all seven."""

    def test_all_seven_section_headings_are_written_out(self):
        text = squash(SURFACES[1][3])
        for heading in (
            "Your question, answered",
            "Headline numbers, interpreted",
            "Merges and match keys",
            "Review queue",
            "Why and how: worked examples",
            "Relationship networks",
            "What was not found, and why",
        ):
            with self.subTest(heading):
                self.assertIn("`## %s`" % heading, text)

    def test_the_instruction_says_the_generator_checks_them_by_name(self):
        """Why the exact form matters, not merely what to write."""
        self.assertIn("the generator checks for them by name", squash(SURFACES[1][3]))

    def test_every_required_section_is_written_out_as_a_heading(self):
        """Read from the generator, so a section added to REQUIRED_SECTIONS without telling
        the guide how to write it fails here (#480 added the first one since this file)."""
        stated = {
            DISCOVERIES._normalize(h)
            for h in re.findall(r"`## ([^`]+)`", squash(SURFACES[1][3]))
        }
        for wanted in DISCOVERIES.REQUIRED_SECTIONS:
            with self.subTest(wanted):
                self.assertTrue(
                    any(DISCOVERIES._normalize(wanted) in heading for heading in stated),
                    "REQUIRED_SECTIONS checks for %r, and the instruction never writes a "
                    "`## ` heading that matches it (INV-242)" % wanted,
                )

    def test_your_question_answered_states_its_table_shape(self):
        """INV-242: the section is a table, and the generator draws one only from consecutive
        lines that start and end with `|`. The instruction must show the header row and say so."""
        text = squash(SURFACES[1][3])
        self.assertIn("| Requirement | Answer | Where in this document |", text)
        self.assertIn("start and end with `|`", text)
        self.assertIn("no `|` inside a cell", text)


class TheRecapImageShapeRemainsStated(unittest.TestCase):
    """INV-242's origin case, kept in the widened guard so the pair cannot diverge."""

    def test_the_recap_instruction_states_the_image_line_shape(self):
        text = squash(SURFACES[0][3])
        self.assertIn("Each image goes on a line of its own", text)
        self.assertIn("INV-242", text)


if __name__ == "__main__":
    unittest.main()
