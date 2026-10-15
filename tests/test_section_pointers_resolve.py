"""Every `<file>.md` → "<name>" pointer in shipped Markdown lands on a section of its file (#615).

A shipped step that sends the guide elsewhere writes `` `<file>.md` → "<name>" ``: the file, then
the section to read. Nothing checked that the section existed. #615 found five references that sent
a reader to a section that did not exist or to the wrong one, and a scan found 24 more pointers of
this form that failed: 16 named a file that does not resolve from the pointer's own file (a bare
`ground-rules.md` from a module directory), and 13 named only the opening words of a bold sentence
(5 did both). Two more, written by #600 before this guard merged, named a heading without its code
span ("Receiving a quality_iteration …") and a bold label with its closing period ("The update
command.").

**The rule, in one sentence (INV-374, which this file enforces):** the backticked file resolves from the file holding the pointer, and
the quoted name is a heading or a bold label opening a line in it, ignoring case, leading
numbering (``2.``, ``6c.``) and a parenthetical qualifier at either end ("(required)",
"(INV-160)"). Nothing shorter matches: a sentence's opening words are not a name.

The scan and the rule live in ``_pointer_sites.py`` (``section_pointers``, ``section_names``,
``section_pointer_problems``), beside the quoted-name pointer scan the ground-rules guards share,
so one place says what a section name is. The pointers are derived by scanning every ``.md`` file
under ``plugins/``, wrap-aware (INV-246, INV-346), never listed.

⚠️ **What this guard cannot see:**

- a pointer in another form: (`SKILL.md`, "<name>"), "see Step 6c", a Markdown link, or a pointer
  in a script or a hook's JSON. #615's five are asserted at their sites below instead;
- whether the section named is the **right** one for what the sentence says;
- a pointer whose file is a bootcamper-project path rather than a plugin file (none today: such
  a path does not resolve, so it fails here and would have to be rewritten or exempted).

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issue: #615.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest

import _corpus
from _pointer_sites import (REPO_ROOT, names_a_section, section_kind, section_names,
                            section_pointer_problems, section_pointers)

SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
M7 = SKILLS / "module-07-query-visualize-discover"
PHASE1 = M7 / "phase1-query-visualize.md"
PHASE2 = M7 / "phase2-discover.md"
PHASE2B = M7 / "phase2b-discover.md"
M0 = SKILLS / "module-00-entity-resolution-concepts"
SDK_SETUP = SKILLS / "module-02-sdk-setup" / "SKILL.md"
CONTRACT = "../module-03b-truthset-visualization/visualization-api-reference.md"


def read(path):
    return path.read_text(encoding="utf-8")


def shipped():
    return {p: read(p) for p in _corpus.corpus_files("plugins", suffixes={".md"})}


def all_problems(texts):
    return [problem for path, text in sorted(texts.items())
            for problem in section_pointer_problems(path, text)]


def pointers_in(path):
    return {(target, name) for _, target, name in section_pointers(path, read(path))}


def clause_in_step(text, heading, clause):
    """Whether ``clause`` sits, at any wrap, in the step from ``heading`` to the next h1-h3."""
    lines = text.split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"#{1,3} ", lines[i])),
               len(lines))
    return clause in " ".join(" ".join(lines[start:end]).split())


class TheScanIsNotVacuous(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.texts = shipped()
        cls.found = [(path, target, name) for path, text in cls.texts.items()
                     for _, target, name in section_pointers(path, text)]

    def test_it_finds_the_pointers(self):
        """190 on 2026-10-14; a floor, so a regex that stopped matching cannot pass quietly."""
        self.assertGreater(len(self.found), 120)

    def test_it_resolves_both_kinds_of_target(self):
        """158 land on a heading and 32 on a bold label on 2026-10-14 (a name that is both counts
        as a heading). Floors per kind, so a matcher that silently stopped reading one kind of
        target cannot pass on the other kind's count."""
        counts = {}
        for path, target, name in self.found:
            resolved = path.parent / target
            kind = section_kind(read(resolved), name) if resolved.is_file() else None
            counts[kind] = counts.get(kind, 0) + 1
        self.assertGreaterEqual(counts.get("heading", 0), 100, counts)
        self.assertGreaterEqual(counts.get("bold label", 0), 20, counts)

    def test_it_reads_every_kind_of_name(self):
        """A heading, a bold label, a qualified heading and a numbered heading each resolve."""
        cases = {
            "heading": (SKILLS / "graduation" / "SKILL.md", "Return guide"),
            "numbered heading": (SKILLS / "graduation" / "SKILL.md", "6c. Return guide"),
            "qualified heading": (SKILLS / "module-03b-truthset-visualization"
                                  / "visualization-api-reference.md", "Server lifetime"),
            "bold label": (SDK_SETUP, "Publishing the visualization port on the SDK container"),
            "qualifier at the front": (SKILLS / "bootcamp-onboarding" / "ground-rules.md",
                                       "Once every fetch and clone step in the response's "
                                       "`access_steps` has failed, report the example as "
                                       "unreachable"),
        }
        for kind, (target, name) in cases.items():
            with self.subTest(kind=kind):
                self.assertTrue(names_a_section(read(target), name))


class EveryPointerResolves(unittest.TestCase):

    def test_every_section_pointer_names_a_heading_or_bold_label(self):
        problems = all_problems(shipped())
        self.assertEqual([], problems, "a `<file>.md` → \"<name>\" pointer must resolve from its "
                         "own file and name a heading or bold label there:\n  "
                         + "\n  ".join(problems))


class TheFiveReferencesLand(unittest.TestCase):
    """#615's five references, at their sites; the three in pointer form are also scanned above."""

    def test_the_snapshot_rule_points_at_the_contracts_section(self):
        self.assertIn((CONTRACT, "Tab identifiers and deep-linking (required)"), pointers_in(PHASE1))
        self.assertNotIn('"Snapshot" section', read(PHASE1))

    def test_the_how_schema_points_at_the_api_reference(self):
        self.assertIn((CONTRACT, "API Endpoints"), pointers_in(PHASE2))
        self.assertNotIn("this module's API reference", read(PHASE2))

    def test_step_6c_is_graduations(self):
        self.assertIn(("../graduation/SKILL.md", "6c. Return guide"), pointers_in(PHASE1))
        self.assertRegex(re.sub(r"\s+", " ", read(PHASE1)), r"graduation Step 6c \(`\.\./graduation")

    def test_the_household_condition_is_step_4ds(self):
        text = re.sub(r"\s+", " ", read(PHASE2B))
        self.assertNotIn("step 4's generated-scenario paragraph", text)
        self.assertEqual(2, text.count("the condition in step 4d's INV-239 paragraph"))

    def test_the_module_0_handoff_names_its_heading(self):
        text = re.sub(r"\s+", " ", read(M0 / "concepts.md"))
        m = re.search(r'\(`SKILL\.md`, "([^"]+)"\)', text)
        self.assertIsNotNone(m, "concepts.md no longer points at SKILL.md for the hand-off")
        self.assertTrue(names_a_section(read(M0 / "SKILL.md"), m.group(1)))


class TheRepresentClauseInv366NamesIsWhereItsTextSays(unittest.TestCase):
    """INV-366 named the INV-284 lines it excludes by line, and every line moved (#615).

    Its queued amendment names each by its text and step instead; this holds the text there:
    the re-present clause in Module 5 step 7b and in both of Module 7 step 3b's returns, and the
    Module 5 ``SKILL.md`` line that cites INV-284 for an old step-26 progress file.
    """

    SITES = (
        (SKILLS / "module-05-data-quality-mapping" / "phase1-quality-assessment.md",
         "### 7b. Return to Data collection",
         "⛔ **(INV-284) that is a new state, NOT an INV-006 repeat**"),
        (PHASE1, "### 3b. Quality evaluation",
         "⛔ **(INV-284) That is a new state, NOT an INV-006 repeat**"),
        (PHASE1, "### 3b. Quality evaluation",
         "⛔ **(INV-284) That too is a new state, NOT an INV-006 repeat**"),
        (SKILLS / "module-05-data-quality-mapping" / "SKILL.md", "## Resuming",
         "Do not run Module Completion again: no second Module 5 recap section, no second "
         "end-of-module summary, and no Phase 3 question (INV-284)."),
    )

    def test_each_clause_is_in_its_step(self):
        for path, heading, clause in self.SITES:
            with self.subTest(file=path.name, clause=clause[:40]):
                self.assertTrue(clause_in_step(read(path), heading, clause),
                                "the clause left %s; re-cite INV-366's amendment" % heading)

    def test_a_moved_clause_fails(self):
        path, heading, clause = self.SITES[2]
        text = read(path)
        moved = text.replace(clause, "INV-284 applies", 1) + "\n\n## Elsewhere\n\n" + clause + "\n"
        self.assertFalse(clause_in_step(moved, heading, clause))


class NegativeControls(unittest.TestCase):
    """Each mutation of live text, or each synthetic target, must turn its check red."""

    @classmethod
    def setUpClass(cls):
        cls.live = read(SDK_SETUP)

    def _mutated(self, old, new, path=SDK_SETUP):
        text = read(path)
        self.assertIn(old, text, "the control's target is gone, so it would mutate nothing")
        return section_pointer_problems(path, text.replace(old, new, 1))

    def test_the_live_file_is_clean(self):
        self.assertEqual([], section_pointer_problems(SDK_SETUP, self.live))

    def test_a_heading_that_does_not_exist_fails(self):
        self.assertTrue(self._mutated('→ "Binding the port"', '→ "Binding the harbor"'))

    def test_a_file_that_does_not_resolve_fails(self):
        """The pre-#615 bare `ground-rules.md` from a module directory."""
        self.assertTrue(self._mutated("`../bootcamp-onboarding/ground-rules.md` →",
                                      "`ground-rules.md` →"))

    def test_a_sentence_opening_fails(self):
        """The pre-#615 pointer: the opening words of a bold sentence, not the label."""
        self.assertTrue(self._mutated("own\n`access_steps`, in the order it gives them\"",
                                      "own\n`access_steps`\""))

    def test_a_prefix_of_a_heading_fails(self):
        self.assertTrue(self._mutated('→ "Binding the port"', '→ "Binding"'))

    def test_a_wrapped_pointer_is_still_read(self):
        text = 'See `SKILL.md` →\n"No such\nsection" for it.\n'
        self.assertEqual([(1, "SKILL.md", "No such section")], section_pointers(SDK_SETUP, text))
        self.assertTrue(section_pointer_problems(SDK_SETUP, text))

    def test_bold_mid_line_is_not_a_label(self):
        names = section_names("Some text with **Mid-line bold.** in it.\n\n- **A label.** Text.\n")
        self.assertNotIn("mid-line bold", names)
        self.assertIn("a label", names)

    def test_a_heading_inside_a_fence_is_not_a_section(self):
        names = section_names("```bash\n# Not a heading\n```\n\n## A heading\n")
        self.assertNotIn("not a heading", names)
        self.assertIn("a heading", names)

    def test_only_a_qualifier_at_an_end_is_dropped(self):
        names = section_names("## Binding the port (required) everywhere\n")
        self.assertNotIn("binding the port everywhere", names)
        self.assertNotIn("binding the port", names)


if __name__ == "__main__":
    unittest.main()
