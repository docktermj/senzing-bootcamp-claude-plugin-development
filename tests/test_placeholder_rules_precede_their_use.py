"""A placeholder a step tells the guide to substitute states its rule at or above the first use.

Module 7 shipped both halves of this failure at once (#695), which is why one file holds both:

- **The rule was missing.** Step 4e derived the program `export_row_<system>`, the program
  `export_<system>`, the project directory those build commands make and the export directory
  `data/exports/<system>/` from `<system>` -- "the name as recorded", which is the Bootcamper's own
  free text ("AWS Neptune", "Microsoft Dynamics 365"). Nothing said to shorten it, so the ground
  rules' build and run commands received a `<name>` with a space in it where that section states a
  base name such as `verify_pipeline`, and on Java that `<name>` is also the filename its class
  rules are read against (INV-237). The same module already got this right one file earlier:
  step 2 writes "`[query_name]` is a short snake_case name for the query".
- **The rule was below the use.** Step 3c's capture block read
  `--url "http://localhost:<the port 3c actually bound>"`, and the container-route override saying
  to hand over and capture against the URL `confirm-viz` printed -- `http://localhost:<host_port>`,
  never `<port>` from the server's own line -- sat about 80 lines further down. On that route the
  port 3c binds is `8080`, which is in-container only, so a guide following the block literally
  captured nothing. The override was right; only its position was wrong.

**The rule, stated as this file enforces it:** where a shipped step hands the guide a placeholder
to substitute, the rule for substituting it is readable at or above the place the step reads it --
in the same block, and in or before the sentence that reads it, for a program name; above the
first URL that reads it, for a route-specific correction. A governing sentence below its point of
use is the Goldilocks failure `tests/test_module07_step2_rules_beside_action.py` recorded for
step 2 (#611); this file is the scanning form of the same rule, for the two placeholder kinds
#695 found.

⛔ **(INV-246) Both site sets are derived by SCANNING the shipped subtree**, never from the issue's
list of line numbers, which was already stale when it was filed: #686, #689 and #692 had moved
every line it quoted. `corpus_files("plugins")` supplies the files.

⚠️ **Wrap-aware (INV-346).** Both rules are about sentences, and this corpus wraps a sentence
wherever the column runs out -- the shipped derivation breaks between "in `src/query`, where" and
"`<system>` is a short snake_case name". Everything is read through
`_wrapped_text.collapsed_blocks`, and each report names the line its match started on.

**The vocabulary was measured before it was narrowed (INV-282), on the text as it shipped:**

1. **"the program `<name>`" is the derivation idiom, and 49 spans in the shipped corpus use it.**
   35 of them sit in a sentence whose creating verb (save / generate / create / write) comes
   BEFORE the name; the other 14 only refer back to a program another step created. The verb's
   position is the narrowing, and it is load-bearing: "the program `discover_patterns` in
   `src/query` that step 4a saved" and "the program `load_[name]` in `src/load`, built at Phase A
   step 3" both carry a verb after the name, and both are references. Reading the verb anywhere in
   the sentence made the first a derivation, and would have reported the second for defining
   nothing -- when it has nothing to define, because Module 6 Phase A defined it where it is
   created.
2. **Only a name holding a placeholder is derived at all.** 30 of the 35 creation sites name a
   literal program (`verify_pipeline`, `results_server`, `discover_patterns`), which states its
   rule by being the name. A vocabulary with no placeholder filter would have reported all 30 as
   rule-less, and every one of them is correct prose.
3. **5 creation sites derive a name from a placeholder**, and that is the whole class:
   `transform_[name]` (Module 5), `load_[name]` (Module 6), `[query_name]` (Module 7 step 2), and
   `export_row_<system>` / `export_<system>` (Module 7 step 4e). Before #695 the first three
   defined their placeholder where they derived the name and the two step 4e sites defined it
   nowhere -- which is exactly the 2 the negative control below puts back.
4. **Two tiers, because the strict idiom was measured to hold in Module 7 only.** Every site, in
   every module, defines its placeholder where it derives the name. Module 7 also names the FORM,
   `snake_case`, as its step 2 already does -- the issue asks the module to have one idiom rather
   than two (INV-300). ⚠️ The strict tier is **not** applied outside Module 7, and the reason is a
   measurement rather than a preference: `transform_[name]` and `load_[name]` say "where `[name]`
   is this source's name" and name no form, so a plugin-wide strict tier would report 2 sites this
   issue does not touch and whose wording is a separate decision. They are recorded here rather
   than narrowed away silently: the same shape, in two more places, not fixed by #695.

**The URL half is keyed on the corpus's own cross-module phrase**, "the URL `confirm-viz`
printed", which `tests/test_container_viz_port_is_published_and_checked.py` already pins at both
launch steps. A file that states that override is a file whose port placeholders it corrects; a
`localhost:<host_port>` span is the corrected form and never a use that needs correcting.

⚠️ **What this cannot establish.** (a) It polices ordering only in a file that STATES the
override: `graduation/SKILL.md` names `--url http://localhost:<port>` in a remedy command with no
route rule anywhere in the file, and is not reported -- there is no governing sentence below the
use, which is the defect this guard is about. (b) It reads the text, not a run: it cannot observe
which port a server actually bound. (c) The program-name tier asks that a rule be stated, not that
a guide obeys it. (d) `8080` written as a literal is a different rule and a different guard's,
`tests/test_module_instructions_do_not_hardcode_the_port.py`. (e) The unit for a program name is
the Markdown block, and in a contiguous numbered list that is the whole list: step 4e's items 6-10
are one block, so item 7's rule is "above" item 8's derivation in the sense a guide reading the
step meets it first. The guard cannot require the clause in the derivation's own sentence, and
does not pretend to.

⚠️ **Scope: the shipped plugin (`plugins/`), stated with its reason (INV-246).** Both rules are
about what a guide reads while running a step for a Bootcamper. A test's or a maintainer skill's
prose discusses these placeholders rather than handing them to anyone, and sweeping it would
report correct content.

⛔ **Every negative control runs the SAME check over a mutated copy of the shipped text
(INV-265)**, restoring the exact pre-#695 wording and the pre-#695 position, and the scan asserts
it read something: an empty corpus would otherwise pass silently.

Stdlib only; shipped files are read as text and nothing under `plugins/` is imported (INV-108).

Source issue: #695.

Run:  python3 -m unittest discover -s tests
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files  # noqa: E402
from _wrapped_text import collapsed_blocks, line_of  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIPPED = "plugins"
MODULE_7 = "plugins/senzing-bootcamp/skills/module-07-query-visualize-discover"
STEP_4E = MODULE_7 + "/phase2b-discover.md"
STEP_3C = MODULE_7 + "/phase1-query-visualize.md"
DISCOVER = MODULE_7 + "/phase2-discover.md"
TRUTHSET_3B = ("plugins/senzing-bootcamp/skills/module-03b-truthset-visualization"
               "/phase1-visualization.md")
GRADUATION = "plugins/senzing-bootcamp/skills/graduation/SKILL.md"
LOAD_STEP = "plugins/senzing-bootcamp/skills/module-06-data-processing/phaseB-load-first-source.md"
MAPPING_SITE = ("plugins/senzing-bootcamp/skills/module-05-data-quality-mapping"
                "/phase2-data-mapping.md")
LOADING_SITE = "plugins/senzing-bootcamp/skills/module-06-data-processing/phaseA-build-loading.md"

#: The derivation idiom this corpus writes: "the program `<name>` in `<dir>`" (INV-370).
PROGRAM = re.compile(r"the program `([^`\n]+)`")
#: The step creating the program, rather than pointing back at one another step created.
CREATES = re.compile(r"(?i)\b(?:saves?|saved|saving|generates?|generated|creates?|created|"
                     r"writes?|written)\b")
#: A placeholder inside a program name: `<system>` or `[query_name]`. A name with none is literal.
PLACEHOLDER = re.compile(r"<[^<>\s]+>|\[[^\[\]\s]+\]")
#: The form Module 7 names, and the one idiom its step 2 already uses.
FORM = re.compile(r"snake_case")
#: Sentence terminators, for pairing a program name with the verb that precedes it.
TERMINATORS = ".!?:"

#: The container-route override, in the cross-module phrase both launch steps use.
OVERRIDE = re.compile(r"(?i)the URL\s+`confirm-viz`\s+printed")
#: A URL that reads a port placeholder. `<host_port>` is the corrected form, never a use.
URL_READ = re.compile(r"localhost:<([^<>]+)>")
CORRECTED = "host_port"
#: The bundled capture command as it is written in a fenced block, which is what reads the URL.
CAPTURE_URL = re.compile(r"--url\s+\"https?://localhost:<")


def _sentence_bounds(flat, index):
    """`(start, end)` of the sentence of `flat` that holds `index`."""
    start = max((flat.rfind(char, 0, index) for char in TERMINATORS), default=-1) + 1
    after = [found for found in (flat.find(char, index) for char in TERMINATORS) if found != -1]
    return start, (min(after) + 1 if after else len(flat))


def _lead_in(flat, start):
    """The run of `flat` from its sentence's start up to `start` -- where a creating verb sits.

    Narrowing 1: the verb comes BEFORE the name. "the program `discover_patterns` in `src/query`
    that step 4a saved" is a reference carrying a creating verb after the name, and reading the
    whole sentence made it a derivation.
    """
    return flat[_sentence_bounds(flat, start)[0]:start]


def derivation_sites(text):
    """`(line, name, placeholder, block, position)` for every program this text's steps CREATE.

    A pure function over one file's text, so the controls run it over mutated copies (INV-265).
    `placeholder` is None for a literal name, which states its rule by being the name.
    """
    found = []
    for flat, origin in collapsed_blocks(text):
        for match in PROGRAM.finditer(flat):
            name = match.group(1)
            if not CREATES.search(_lead_in(flat, match.start())):
                continue
            holder = PLACEHOLDER.search(name)
            found.append((line_of(origin, match.start()), name,
                          holder.group(0) if holder else None, flat, match.start()))
    return found


def defines(block, placeholder, position, form_too):
    """Whether `block` states the rule for `placeholder` where the guide reads the name.

    A defining clause counts when it opens before the name, or lies in the name's own sentence --
    "at or above the use". Every clause is considered, so a later restatement cannot stand in for
    a rule the guide passes the name without.
    """
    sentence = _sentence_bounds(block, position)
    for clause in re.finditer(r"`" + re.escape(placeholder) + r"`\s+is\b([^.]*)", block):
        if clause.start() > position and not (sentence[0] <= clause.start() < sentence[1]):
            continue
        if not form_too or FORM.search(clause.group(1)):
            return True
    return False


def derived_name_problems(relative, text):
    """Every derived program name in `relative` that does not state its rule where it is read."""
    strict = relative.startswith(MODULE_7)
    problems = []
    for line, name, placeholder, block, position in derivation_sites(text):
        if placeholder is None:
            continue
        if defines(block, placeholder, position, form_too=strict):
            continue
        problems.append(
            "line %d derives the program `%s` from %s without saying, at or above the name, what "
            "%s is%s" % (line, name, placeholder, placeholder,
                         " and that it is a snake_case name" if strict else ""))
    return problems


def override_line(text):
    """The line where the route-specific URL override is stated, or None when it is not."""
    for flat, origin in collapsed_blocks(text):
        match = OVERRIDE.search(flat)
        if match:
            return line_of(origin, match.start())
    return None


def url_reads(text):
    """`(line, placeholder)` for every URL that reads a port placeholder needing correction."""
    found = []
    for flat, origin in collapsed_blocks(text):
        for match in URL_READ.finditer(flat):
            if match.group(1) == CORRECTED:
                continue
            found.append((line_of(origin, match.start()), match.group(1)))
    return found


def rule_ordering_problems(text):
    """Every URL that reads a port placeholder above the override that corrects it."""
    stated = override_line(text)
    if stated is None:
        return []
    return ["line %d reads `localhost:<%s>`, which the container-route override at line %d "
            "corrects -- the rule sits %d lines BELOW the block that reads it"
            % (line, placeholder, stated, stated - line)
            for line, placeholder in url_reads(text) if line < stated]


def capture_block_line(text):
    """The line of the fenced capture command, which is what reads the handed-over URL."""
    for flat, origin in collapsed_blocks(text):
        match = CAPTURE_URL.search(flat)
        if match and "capture_screenshots.py" in flat:
            return line_of(origin, match.start())
    return None


def shipped_texts():
    """`(repo-relative path, text)` for every readable shipped Markdown file (INV-246)."""
    for path in corpus_files(SHIPPED, root=REPO_ROOT, suffixes={".md"}):
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield Path(path).relative_to(REPO_ROOT).as_posix(), text


def shipped(relative):
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def mutate(test, text, old, new):
    """Replace `old` once; fail the control if the anchor text has gone."""
    test.assertIn(old, text, "the control's anchor text is gone; update the control")
    return text.replace(old, new, 1)


#: Step 4e as it read before #695, in three `(shipped now, as it read before)` pairs: item 7's
#: rule, item 7's sentence saying what the rule governs, and item 8's restatement. ⛔ All three go
#: back together, because items 6-10 are ONE Markdown block (limitation (e)) and a clause left
#: behind anywhere in it would answer for the site the control is trying to expose.
PRE_695 = (
    ("the program `export_row_<system>` in `src/query`, where\n"
     "   `<system>` is a short snake_case name for the system (for example `aws_neptune` for a "
     "system\n   recorded as \"AWS Neptune\"), at the path",
     "the program `export_row_<system>` in `src/query` at the path"),
    ("with that section's commands. That section takes `<name>` as\n"
     "   a program's base name such as `verify_pipeline`, and on Java as the filename its class "
     "rules\n   are read against (INV-237), so the name as recorded — the Bootcamper's own free "
     "text, \"AWS\n   Neptune\" or \"Microsoft Dynamics 365\" — is written in that snake_case form "
     "here rather than\n   used as it stands. `<system>` is that name wherever this step builds a "
     "program name, a project\n   directory or an output path; `[system]`, the name as recorded at "
     "item 3, stays in what you say\n   to the Bootcamper and in the checkpoint's `\"system\"` "
     "value. The program opens the export with the",
     "with that section's commands. It opens the export with the"),
    ("the program `export_<system>` in `src/query` — `<system>`\n"
     "   is item 7's snake_case name, here and in the export directory below — at the path",
     "the program `export_<system>` in `src/query`, at the path"),
)

#: The container-route override, and the anchor that puts it back where it sat before #695:
#: lifted from above the MUST list, re-inserted after the teardown paragraph.
OVERRIDE_PARAGRAPH = (
    "⛔ **On SDK setup's container route, start it inside the SDK container (INV-260).** A "
    "server started\non the host, or bound to the container's loopback, does not reach the "
    "Bootcamper's browser.\n")
MOVED_FROM = "\"Identifying the server process\".\n"


def pre_695_step_4e(test):
    """Step 4e's text as it read before #695: no naming rule at either derivation."""
    text = shipped(STEP_4E)
    for now, before in PRE_695:
        text = mutate(test, text, now, before)
    return text


def move_the_override_back(test, text):
    """Put the container-route paragraph back below the capture block, as it sat before #695."""
    test.assertIn(OVERRIDE_PARAGRAPH, text, "the override paragraph's opening has changed")
    start = text.index(OVERRIDE_PARAGRAPH)
    end = text.index("\n\n", start) + len("\n\n")
    paragraph = text[start:end]
    lifted = text[:start] + text[end:]
    test.assertIn(MOVED_FROM, lifted,
                  "the teardown paragraph this control re-inserts after is gone")
    at = lifted.index(MOVED_FROM) + len(MOVED_FROM) + 1
    return lifted[:at] + paragraph + lifted[at:]


class EveryDerivedProgramNameStatesItsRule(unittest.TestCase):
    """Criterion 1, over the whole shipped subtree, with Module 7 held to the strict tier."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = list(shipped_texts())

    def test_every_shipped_file_is_clean(self):
        for relative, text in self.corpus:
            with self.subTest(site=relative):
                self.assertEqual(
                    [], derived_name_problems(relative, text),
                    "%s derives a program name from a placeholder without saying, where the "
                    "guide reads it, what the placeholder resolves to. Say it in the same "
                    "sentence, as step 2 does for `[query_name]`." % relative)

    def test_module_7_names_the_form_at_each_of_its_derivations(self):
        """The strict tier, named per site so a regression says which one lost its rule."""
        for relative, text in self.corpus:
            if not relative.startswith(MODULE_7):
                continue
            for line, name, placeholder, block, position in derivation_sites(text):
                if placeholder is None:
                    continue
                with self.subTest(site="%s:%d" % (relative, line), program=name):
                    self.assertTrue(
                        defines(block, placeholder, position, form_too=True),
                        "%s derives `%s` without naming the form of %s; Module 7 names "
                        "`snake_case` at every derivation so it has one idiom (INV-300)"
                        % (relative, name, placeholder))

    def test_the_two_step_4e_derivations_are_the_ones_this_issue_fixed(self):
        """⛔ The sites are found by scanning, and these two must be among what it finds."""
        derived = {name for _line, name, placeholder, _block, _pos
                   in derivation_sites(shipped(STEP_4E)) if placeholder}
        self.assertEqual({"export_row_<system>", "export_<system>"}, derived)

    def test_a_literal_program_name_is_not_reported(self):
        """30 of the 35 creation sites name a literal program; none of them owes a rule."""
        literals = [name for _line, name, placeholder, _block, _pos
                    in derivation_sites(shipped(STEP_3C)) if placeholder is None]
        self.assertIn("results_server", literals)
        self.assertEqual([], derived_name_problems(STEP_3C, shipped(STEP_3C)))

    def test_the_weak_tier_still_holds_outside_module_7(self):
        """Measurement 4: the two sites outside Module 7 define their placeholder, and pass."""
        for relative in (MAPPING_SITE, LOADING_SITE):
            with self.subTest(site=relative):
                text = shipped(relative)
                self.assertEqual([], derived_name_problems(relative, text))
                self.assertNotEqual(
                    [], derived_name_problems(MODULE_7 + "/fixture.md", text),
                    "%s would pass Module 7's strict tier too, so measurement 4's reason for "
                    "not applying it plugin-wide no longer holds" % relative)


class TheRouteRulePrecedesTheUrlItCorrects(unittest.TestCase):
    """Criterion 2: the override is readable above every URL placeholder it corrects."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = list(shipped_texts())

    def test_every_shipped_file_is_clean(self):
        for relative, text in self.corpus:
            with self.subTest(site=relative):
                self.assertEqual(
                    [], rule_ordering_problems(text),
                    "%s corrects a URL placeholder below the block that reads it. Move the "
                    "override above the first use, as Module 3b's step 2.3 does." % relative)

    def test_the_capture_block_reads_the_url_after_the_override(self):
        """The block #695 is about: step 3c's bundled capture command."""
        text = shipped(STEP_3C)
        stated, capture = override_line(text), capture_block_line(text)
        self.assertIsNotNone(stated, "step 3c no longer states the container-route override")
        self.assertIsNotNone(capture, "step 3c's capture command is gone")
        self.assertLess(stated, capture,
                        "the capture block at line %s reads the URL the override at line %s "
                        "corrects" % (capture, stated))

    def test_the_sibling_module_states_it_above_its_own_capture_block(self):
        """Module 3b is the precedent the move follows, and it must keep holding."""
        text = shipped(TRUTHSET_3B)
        self.assertLess(override_line(text), capture_block_line(text))
        self.assertEqual([], rule_ordering_problems(text))

    def test_a_file_with_no_override_is_outside_this_rule(self):
        """Limitation (a), pinned: nothing is below its use when no rule is stated at all."""
        text = shipped(GRADUATION)
        self.assertIsNone(override_line(text))
        self.assertNotEqual([], url_reads(text), "graduation no longer reads a port placeholder; "
                                                 "this control measures nothing")
        self.assertEqual([], rule_ordering_problems(text))


class TheScanReadsTheCorpusItClaimsTo(unittest.TestCase):
    """⛔ (INV-265) A vocabulary that matches nothing passes silently; these are the floors."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = list(shipped_texts())

    def test_the_shipped_subtree_is_reached(self):
        names = [relative for relative, _text in self.corpus]
        self.assertGreater(len(names), 30, "the shipped scan found almost no files")
        for expected in (STEP_4E, STEP_3C, TRUTHSET_3B):
            with self.subTest(site=expected):
                self.assertIn(expected, names)

    def test_the_derivation_vocabulary_finds_the_measured_class(self):
        """Measurements 1-3: creation sites, references dropped, placeholders separated."""
        creations, placeholders, files = 0, [], set()
        for relative, text in self.corpus:
            for _line, name, placeholder, _block, _pos in derivation_sites(text):
                creations += 1
                files.add(relative)
                if placeholder:
                    placeholders.append(name)
        self.assertGreaterEqual(creations, 30,
                                "only %d program derivations found, so a clean result measures "
                                "almost nothing" % creations)
        self.assertGreaterEqual(len(files), 8)
        self.assertGreaterEqual(len(placeholders), 5,
                                "the placeholder class collapsed to %r" % placeholders)

    def test_a_reference_to_an_existing_program_is_not_a_derivation(self):
        """Measurement 1: 14 spans point back at a program another step created."""
        text = shipped(DISCOVER)
        self.assertIn("the program `discover_patterns` in `src/query` that step", text)
        lines = [line for line, name, _p, _b, _pos in derivation_sites(text)
                 if name == "discover_patterns"]
        self.assertEqual(1, len(lines),
                         "step 4a creates `discover_patterns` and a later step points back at "
                         "it; both were read as derivations")

    def test_a_reference_to_a_placeholder_named_program_is_not_reported(self):
        """⛔ The narrowing is load-bearing: this reference defines nothing, and owes nothing."""
        text = shipped(LOAD_STEP)
        self.assertIn("the program `load_[name]` in `src/load`, built at Phase A step 3", text)
        self.assertEqual([], [name for _line, name, placeholder, _block, _pos
                              in derivation_sites(text) if placeholder],
                         "a step that only runs `load_[name]` was read as deriving it")
        self.assertEqual([], derived_name_problems(LOAD_STEP, text))

    def test_the_override_vocabulary_matches_both_launch_steps(self):
        stating = [relative for relative, text in self.corpus if override_line(text) is not None]
        self.assertIn(STEP_3C, stating)
        self.assertIn(TRUTHSET_3B, stating)

    def test_the_url_vocabulary_matches_the_uses_it_must_order(self):
        reads = url_reads(shipped(STEP_3C))
        self.assertGreaterEqual(len(reads), 3,
                                "step 3c reads %r port placeholders; before #695 three of them "
                                "sat above the rule" % reads)


class TheControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs the shipped check over the shipped text, mutated."""

    def test_the_shipped_text_is_clean_on_both_halves(self):
        self.assertEqual([], derived_name_problems(STEP_4E, shipped(STEP_4E)))
        self.assertEqual([], rule_ordering_problems(shipped(STEP_3C)))

    def test_the_pre_695_step_4e_reports_both_derivations(self):
        """The negative control criterion 3 asks for: step 4e as it read before this change."""
        reported = derived_name_problems(STEP_4E, pre_695_step_4e(self))
        self.assertEqual(2, len(reported), "the pre-#695 text reported %r" % reported)
        joined = " ".join(reported)
        self.assertIn("export_row_<system>", joined)
        self.assertIn("export_<system>", joined)
        self.assertIn("snake_case", joined)

    def test_the_one_sentence_is_what_clears_both_sites(self):
        """Item 7's rule governs item 8's derivation too, because the step is one block."""
        text = mutate(self, pre_695_step_4e(self), *reversed(PRE_695[0]))
        self.assertEqual([], derived_name_problems(STEP_4E, text))

    def test_a_defining_clause_that_names_no_form_fails_module_7s_tier(self):
        """The strict tier's teeth: defining the placeholder is not naming its form."""
        text = mutate(self, pre_695_step_4e(self),
                      "the program `export_row_<system>` in `src/query` at the path",
                      "the program `export_row_<system>` in `src/query`, where `<system>` is the "
                      "name as recorded, at the path")
        self.assertEqual([], derived_name_problems("plugins/elsewhere.md", text),
                         "the weak tier must accept a clause that defines the placeholder")
        reported = derived_name_problems(STEP_4E, text)
        self.assertEqual(2, len(reported), "Module 7's tier reported %r" % reported)
        self.assertIn("snake_case", " ".join(reported))

    def test_the_pre_695_wording_is_reported_across_a_line_wrap(self):
        """⛔ (INV-346) The shipped rule wraps mid-clause, which is how such a miss survives."""
        text = mutate(self, shipped(STEP_4E),
                      "`<system>` is a short snake_case name",
                      "`<system>` is a\n   short snake_case name")
        self.assertEqual([], derived_name_problems(STEP_4E, text),
                         "the rule is no longer seen across a line wrap, so the guard has lost "
                         "the wrap-awareness INV-346 requires")

    def test_the_pre_695_override_position_is_reported(self):
        """The second negative control: the override back below the capture block."""
        reported = rule_ordering_problems(move_the_override_back(self, shipped(STEP_3C)))
        self.assertEqual(3, len(reported),
                         "the pre-#695 position reported %r; three URL reads sat above the "
                         "rule when #695 was filed" % reported)
        self.assertIn("the port 3c actually bound", " ".join(reported))

    def test_the_capture_block_is_among_what_the_old_position_reported(self):
        """⛔ Item 2's own defect, not merely some URL: the bundled capture command."""
        text = move_the_override_back(self, shipped(STEP_3C))
        self.assertGreater(override_line(text), capture_block_line(text))

    def test_the_order_is_what_is_checked_and_not_the_presence_of_both_halves(self):
        """A control against the check degrading to "both halves are somewhere in the file".

        The same two halves are present in both texts below; only their order differs, and only
        one of them is reported.
        """
        text = shipped(STEP_3C)
        moved_back = move_the_override_back(self, text)
        self.assertEqual(sorted(name for _line, name in url_reads(text)),
                         sorted(name for _line, name in url_reads(moved_back)))
        self.assertIsNotNone(override_line(moved_back))
        self.assertEqual([], rule_ordering_problems(text))
        self.assertNotEqual([], rule_ordering_problems(moved_back))


if __name__ == "__main__":
    unittest.main()
