"""A path a shipped step hands over as its deliverable must be one a packaging profile reaches.

Enforces **INV-392**, registered by the maintainer 2026-10-20: a path a step hands over as a
deliverable is reachable by a packaging profile or declared non-traveling at the step. ⚠️ It
reads the shipped prose and the packager's own constants; it **cannot** establish that a real
archive contains the file, only that the rules say it would.

Module 7 step 4e tells the Bootcamper that "the deliverable is the written file (or files) and the
program that writes them", hands each written file over by path, and records them as `outputs` in
its checkpoint. Until #686 it wrote them under `data/temp/exports/<system>/`, and `data/temp` sits
in `package_bootcamp.py`'s `ALWAYS_EXCLUDE`. So a Bootcamper who ran `/package-bootcamp` to hand
their results to a colleague shipped an archive without the one artifact the step had just called
their deliverable -- and `PACKAGE_MANIFEST.json`'s **exclusion** list was the only place it was
named. Nothing read the hand-over against the packaging rules, so nothing could notice.

**The rule, stated as this file enforces it:** in a shipped step that hands something over, a
project-relative path the step says it **writes** MUST be reachable by the `share` or the
`transfer` profile, or carry, in the same sentence, an explicit statement that it does not travel.

⛔ **(INV-246) The site set is derived by SCANNING the shipped subtree, never from a list of
paths**, and the profile reach is read out of `plugins/senzing-bootcamp/scripts/package_bootcamp.py`
with `ast` rather than copied here. A copied `ALWAYS_EXCLUDE` / `SHARE_INCLUDE` / `SHARE_EXCLUDE` /
`TRANSFER_EXTRA` would stop tracking the script the moment either side changed -- which is the same
failure mode this issue is about: a deliverable and a packaging rule that each stayed correct on
their own while disagreeing with each other.

⚠️ **Wrap-aware (INV-346).** Both halves of the rule are sentences, and Markdown wraps a sentence
wherever the column runs out: the shipped text breaks between "It writes its files under" and the
path itself. The scan reads through `_wrapped_text.collapsed_blocks` and reports the line each
match started on. A line-at-a-time read is exactly how the original miss survived review.

**The hand-over vocabulary is the verb `hand ... over` and nothing wider, and the scope is stated
with its reason (INV-282).** Three narrowings, each measured against the shipped corpus rather than
guessed, because a vocabulary wide enough to catch every mention of a path reports correct prose
and gets waived:

1. **The verb only, never the noun.** `handover` / `handed-over` name the recap's handover block
   and a handed-over project; on trial they made graduation's Step 2 a hand-over step and reported
   its `config/data_sources.yaml` projection rules, which are correct prose about what production
   deliberately leaves behind.
2. **Never the word `deliverable`.** It reports a table cell in `docs/model-selection.md`, Module
   5's "visual deliverable" brand rules and Module 7's data-discoveries deliverable -- none of
   which is a hand-over of an unreachable path. On trial the two together reported 26 sites, 25 of
   them correct prose.
3. **The path and a writing verb in one sentence.** The unit a step is read in is the section
   between two Markdown headings, because the path is named where the program is written (item 8)
   and handed over three items later (item 10). Within it, only a path the step says it *writes*
   is a deliverable: pairing them per block instead reported graduation Step 6c's `licenses/g2.lic`,
   which that step points at and never writes.

⚠️ **What this cannot establish.** (a) A **bare top-level tree** (`data/`, `logs/`) is not a
candidate: a path with one segment names one of INV-050's trees rather than an artifact a step
hands over, and the two trees a step does hand over whole, `docs/` and `production/`, are reachable
anyway. (b) It reads paths written as inline code, which is how this corpus writes them; a path in
running prose is invisible here. (c) It says nothing about whether the file is *produced* -- only
about where the step says it lands. (d) The top-level names come from INV-050's layout tree in
`specs/INVARIANTS.md`, so a project directory the invariant does not carry is not recognized.

⚠️ **Scope: the shipped plugin (`plugins/`), stated with its reason (INV-246).** The rule is about
a *shipped* step and the archive a Bootcamper hands to a colleague. A test's or a maintainer
skill's prose discusses those paths rather than handing them over, and sweeping it would report
correct content.

⛔ **Every negative control runs the SAME check over a mutated copy of the shipped text (INV-265)**,
putting back the exact pre-#686 wording, and the scan asserts it read something: an empty corpus
would otherwise pass silently.

Stdlib only; shipped files are read as text and `package_bootcamp.py` is parsed, never imported
(INV-108).

Source issue: #686.

Run:  python3 -m unittest discover -s tests
"""
import ast
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _corpus import corpus_files  # noqa: E402
from _wrapped_text import collapsed_blocks, line_of  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIPPED = "plugins"
PACKAGER = REPO_ROOT / "plugins" / "senzing-bootcamp" / "scripts" / "package_bootcamp.py"
INVARIANTS = REPO_ROOT / "specs" / "INVARIANTS.md"
STEP_4E = "plugins/senzing-bootcamp/skills/module-07-query-visualize-discover/phase2b-discover.md"
STAGING = "plugins/senzing-bootcamp/skills/module-04-data-collection/SKILL.md"

#: The rule tuples read out of the packager. Named here only so a rename of one is a loud failure
#: rather than a silently empty rule set; their CONTENTS are never written down in this file.
RULE_NAMES = ("ALWAYS_EXCLUDE", "SHARE_EXCLUDE", "SHARE_INCLUDE", "TRANSFER_EXTRA",
              "DATABASE_SUFFIXES")

#: INV-050's section heading in `specs/INVARIANTS.md`, and the tree's indentation step.
TREE_HEADING = "## INV-050: Project layout"
BOX_CHARS = " \t│├└─"
INDENT = 4

#: Handing over, as a verb: "hand over", "hands the file over", "do not hand the file over".
#: ⛔ Never the noun (`handover`, `handed-over`): see narrowing 1 above.
HANDS_OVER = re.compile(r"(?i)\bhand(?:s|ed|ing)?(?:\s+\S+){0,4}?\s+over\b")
#: The step saying it writes the file. Reporting a path the step merely points at is narrowing 3.
WRITES = re.compile(r"(?i)\b(?:writes?|writing|written|wrote|saves?|saved)\b")
#: The escape hatch the rule allows: an explicit statement, beside the path, that it does not
#: travel. Deliberately a short closed list -- a vague one ("temporary", "scratch") would waive
#: the defect this guard exists to catch.
DOES_NOT_TRAVEL = re.compile(
    r"(?i)never packaged|not packaged|never travels?|does not travel|do not travel|"
    r"never copied|not copied|excluded from (?:both |every |each )?profile")
#: Inline code, which is how this corpus writes a path.
CODE = re.compile(r"`([^`\n]+)`")
#: An ATX heading line and a code-fence line, for cutting a file into steps.
HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
#: Sentence terminators, used to pair a path with the verb beside it.
TERMINATORS = ".!?"


def packaging_rules(source=None):
    """The packager's rule tuples, read with `ast` (INV-108) and never copied into this file.

    `source` replaces the script's text, for the controls.
    """
    text = PACKAGER.read_text(encoding="utf-8") if source is None else source
    found = {}
    for node in ast.parse(text).body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        name = node.targets[0].id
        if name in RULE_NAMES:
            found[name] = tuple(ast.literal_eval(node.value))
    missing = [name for name in RULE_NAMES if name not in found]
    if missing:
        raise AssertionError(
            "package_bootcamp.py no longer defines %s at module level, so this guard cannot read "
            "what the profiles reach and every result below would be meaningless" % ", ".join(
                missing))
    return found


def _matches(parts, rule):
    """Whether `rule`'s segments sit as a contiguous run anywhere in `parts` (the packager's rule).

    The packager matches a rule wherever its segments sit, not only at the project root, so that a
    rule about the Bootcamper's inputs stays true inside the generated tree that copies them.
    """
    rule_parts = rule.split("/")
    span = len(rule_parts)
    return any(parts[start:start + span] == rule_parts
               for start in range(len(parts) - span + 1))


def is_excluded(relpath, profile, rules):
    """The rule that excludes `relpath` from `profile`, or None."""
    parts = relpath.split("/")
    for rule in rules["ALWAYS_EXCLUDE"]:
        if _matches(parts, rule):
            return rule
    if profile == "share":
        for rule in rules["SHARE_EXCLUDE"]:
            if _matches(parts, rule):
                return rule
        if Path(relpath).suffix.lower() in rules["DATABASE_SUFFIXES"]:
            return "a database file"
    return None


def candidate_roots(profile, rules):
    return list(rules["SHARE_INCLUDE"]) + (
        list(rules["TRANSFER_EXTRA"]) if profile == "transfer" else [])


def profiles_reaching(relpath, rules):
    """The profiles that would package `relpath`: under a candidate root and excluded by no rule."""
    parts = relpath.split("/")
    reached = []
    for profile in ("share", "transfer"):
        under = any(parts[:len(root.split("/"))] == root.split("/")
                    for root in candidate_roots(profile, rules))
        if under and is_excluded(relpath, profile, rules) is None:
            reached.append(profile)
    return reached


def project_trees(text=None):
    """The top-level directory names of INV-050's layout tree, by reading the tree.

    These are what makes a backticked span a *project-relative* path rather than a link to another
    skill file. Derived, never listed (INV-246). `text` replaces the registry's text, for controls.
    """
    if text is None:
        text = INVARIANTS.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        heading = next(i for i, line in enumerate(lines) if line.strip() == TREE_HEADING)
    except StopIteration:
        raise AssertionError(
            "%r not found in specs/INVARIANTS.md -- INV-050's section was renamed and this guard "
            "can no longer find the tree that defines a project-relative path" % TREE_HEADING)
    opening = next(i for i in range(heading, len(lines))
                   if lines[i].strip().startswith("```text"))
    closing = next(i for i in range(opening + 1, len(lines)) if lines[i].strip() == "```")

    names, root_column = set(), None
    for offset, line in enumerate(lines[opening + 1:closing]):
        left, _, _ = line.partition("#")
        name = left.strip(BOX_CHARS).strip()
        if not name:
            continue
        column = left.index(name)
        if offset == 0:
            root_column = column
            continue
        if (column - root_column) // INDENT == 1 and name.endswith("/"):
            names.add(name.rstrip("/"))
    return frozenset(names)


def project_path(span, trees):
    """`span`'s project-relative path, or None when it is not one.

    A candidate has at least two segments (see limitation (a)), its first segment is one of
    INV-050's top-level trees, and it is neither absolute, nor relative to the current file, nor a
    URL. `**` and a trailing `/` are stripped, so `data/exports/**` and `data/exports/` are the
    same path -- the copy table writes the first and the step writes the second.
    """
    raw = span.strip()
    if not raw or " " in raw or "\\" in raw or "://" in raw or ".." in raw or "/" not in raw:
        return None
    if raw.startswith(("/", ".", "~", "$", "<", "-")):
        return None
    cleaned = raw.rstrip("*").rstrip("/")
    parts = cleaned.split("/")
    if len(parts) < 2 or parts[0] not in trees:
        return None
    return cleaned


def heading_lines(text):
    """The 1-based lines that open a Markdown heading, skipping fenced content.

    No phrase-level pattern (#686): a heading is a line by definition, and a `#` inside a fence is
    a shell comment rather than a heading, which is why the fence state is tracked here (INV-346).
    """
    opened, fence = [], None
    for number, line in enumerate(text.splitlines(), 1):
        fenced = FENCE.match(line)
        if fenced:
            char = fenced.group(1)[0]
            fence = char if fence is None else (None if fence == char else fence)
            continue
        if fence is None and HEADING.match(line):
            opened.append(number)
    return opened


def _sentence_around(flat, start, end):
    """The run of `flat` between sentence terminators that holds `flat[start:end]`."""
    before = max((flat.rfind(char, 0, start) for char in TERMINATORS), default=-1)
    after = [index for index in (flat.find(char, end) for char in TERMINATORS) if index != -1]
    return flat[before + 1:(min(after) + 1) if after else len(flat)]


def hand_over_problems(text, rules, trees):
    """Every path a hand-over step writes that no profile reaches and nothing declares.

    A pure function over one file's text, so each negative control runs this same check over a
    mutated copy (INV-265). Each problem reads `line N: <path> -- <the sentence>`.
    """
    headings = heading_lines(text)

    def step_of(line_number):
        opened = 0
        for heading in headings:
            if heading <= line_number:
                opened = heading
            else:
                break
        return opened

    steps = {}
    for flat, origin in collapsed_blocks(text):
        steps.setdefault(step_of(origin[0] if origin else 1), []).append((flat, origin))

    problems = []
    for blocks in steps.values():
        if not any(HANDS_OVER.search(flat) for flat, _ in blocks):
            continue
        for flat, origin in blocks:
            for match in CODE.finditer(flat):
                relpath = project_path(match.group(1), trees)
                if relpath is None:
                    continue
                sentence = _sentence_around(flat, match.start(), match.end()).strip()
                if not WRITES.search(sentence):
                    continue
                if profiles_reaching(relpath, rules):
                    continue
                if DOES_NOT_TRAVEL.search(sentence):
                    continue
                problems.append(
                    "line %d hands over `%s`, which no packaging profile reaches and which the "
                    "step does not declare as staying behind: %s"
                    % (line_of(origin, match.start()), relpath, sentence))
    return problems


def shipped_texts():
    """`(repo-relative path, text)` for every readable shipped file, by SCANNING (INV-246).

    Undecodable files are the plugin's binary assets; they carry no prose and are skipped.
    """
    for path in corpus_files(SHIPPED, root=REPO_ROOT):
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


#: The pre-#686 wording of step 4e's item 8 -- the sentence that names where the export lands --
#: as `(shipped now, as it read before)`. The controls put it back and run the same check.
PRE_686_PROSE = (
    "It writes its files under\n   `data/exports/<system>/`, which it recreates on every run.",
    "It writes its files under\n   `data/temp/exports/<system>/`, which it recreates on every "
    "run.")

#: The step's checkpoint example carried the same path. ⚠️ It is NOT reported by the scan and is
#: not expected to be: it sits in a fenced JSON block under a later heading, which is not a
#: hand-over step and states no writing verb. `TheExportPathIsNamedWhereverItMatters` is what
#: covers it, by scanning for the old path across the whole shipped subtree.
PRE_686_CHECKPOINT = ('"outputs": ["data/exports/<system>/<file>"]',
                      '"outputs": ["data/temp/exports/<system>/<file>"]')


class TheProfileReachIsReadFromTheScript(unittest.TestCase):
    """The packaging half: read with `ast`, then exercised on the paths this issue turns on."""

    @classmethod
    def setUpClass(cls):
        cls.rules = packaging_rules()

    def test_every_rule_tuple_was_found_and_is_not_empty(self):
        """⛔ (INV-265) An empty rule set would make every path below trivially reachable."""
        for name in RULE_NAMES:
            with self.subTest(rule=name):
                self.assertTrue(self.rules[name], "%s read as empty" % name)

    def test_the_export_tree_is_reached_by_both_profiles(self):
        reached = profiles_reaching("data/exports/neo4j/nodes.csv", self.rules)
        self.assertEqual(
            ["share", "transfer"], reached,
            "step 4e's export is its deliverable, so both profiles must carry it; "
            "`SHARE_INCLUDE` reached %r" % reached)

    def test_the_copied_export_tree_under_production_is_reached_too(self):
        """Graduation copies it to the same project-relative path (INV-186), so that copy travels."""
        self.assertEqual(["share", "transfer"],
                         profiles_reaching("production/data/exports/neo4j/nodes.csv", self.rules))

    def test_the_scratch_and_source_trees_are_still_reached_by_neither(self):
        """⛔ This issue widens nothing else: `data/temp` and `data/raw` stay excluded."""
        for relpath in ("data/temp/exports/neo4j/nodes.csv", "data/temp/scratch.txt",
                        "data/raw/customers.csv"):
            with self.subTest(path=relpath):
                self.assertEqual([], profiles_reaching(relpath, self.rules))

    def test_the_share_promise_still_holds_for_the_mapped_inputs(self):
        """`data/senzing-ready/` travels on `transfer` only, and only inside `production/`.

        ⚠️ Recorded because it is the shape of this whole issue: the mapped inputs reach the
        archive through the copy graduation makes at `production/data/senzing-ready/` (INV-186),
        never from the project root, which no candidate root covered before `data/exports` was
        added. A deliverable written anywhere else under `data/` reached no profile at all.
        """
        self.assertEqual([], profiles_reaching("data/senzing-ready/people.jsonl", self.rules))
        self.assertEqual(["transfer"],
                         profiles_reaching("production/data/senzing-ready/people.jsonl",
                                           self.rules))


class EveryHandedOverPathCanTravel(unittest.TestCase):
    """The whole shipped subtree, derived by scanning (INV-246)."""

    @classmethod
    def setUpClass(cls):
        cls.rules = packaging_rules()
        cls.trees = project_trees()
        cls.corpus = list(shipped_texts())

    def test_every_shipped_file_is_clean(self):
        for relative, text in self.corpus:
            with self.subTest(site=relative):
                self.assertEqual(
                    [], hand_over_problems(text, self.rules, self.trees),
                    "%s hands a path over that no packaging profile reaches. Either write it "
                    "somewhere a profile carries -- `docs/`, `production/` or `data/exports/` on "
                    "`share`, plus `config/`, `src/` and `backups/revisit/` on `transfer` -- or "
                    "say at the step, beside the path, that it does not travel." % relative)

    def test_the_scan_read_the_corpus_it_claims_to(self):
        """⛔ (INV-265) An empty match set is an unrun check, never a pass."""
        self.assertGreater(len(self.corpus), 50,
                           "the shipped subtree scan found almost no files; it is not scanning")
        self.assertIn(STEP_4E, [relative for relative, _text in self.corpus],
                      "step 4e's own file is not in the scanned set, so the scan is not reaching "
                      "the shipped skills")
        self.assertGreater(len(self.trees), 8,
                           "INV-050's tree parsed to almost no top-level directories, so no "
                           "backticked path can be recognized as project-relative")

    def test_the_scan_found_hand_over_steps_and_written_paths(self):
        """The floor beneath the clean result: a vocabulary that matches nothing passes silently."""
        steps, pairs, files = 0, 0, set()
        for relative, text in self.corpus:
            headings = heading_lines(text)
            blocks = list(collapsed_blocks(text))
            grouped = {}
            for flat, origin in blocks:
                opened = 0
                for heading in headings:
                    if heading <= (origin[0] if origin else 1):
                        opened = heading
                    else:
                        break
                grouped.setdefault(opened, []).append((flat, origin))
            for group in grouped.values():
                if not any(HANDS_OVER.search(flat) for flat, _ in group):
                    continue
                steps += 1
                files.add(relative)
                for flat, _origin in group:
                    for match in CODE.finditer(flat):
                        if project_path(match.group(1), self.trees) is None:
                            continue
                        if WRITES.search(_sentence_around(flat, match.start(), match.end())):
                            pairs += 1
        self.assertGreaterEqual(steps, 8, "the hand-over vocabulary matched %d steps" % steps)
        self.assertGreaterEqual(len(files), 5,
                                "hand-over steps were found in only %d files" % len(files))
        self.assertGreaterEqual(pairs, 8,
                                "only %d written project paths sit in a hand-over step, so a "
                                "clean result measures almost nothing" % pairs)


class TheControlsRunTheSameCheck(unittest.TestCase):
    """⛔ (INV-265) Each control runs `hand_over_problems` over the shipped text, mutated."""

    @classmethod
    def setUpClass(cls):
        cls.rules = packaging_rules()
        cls.trees = project_trees()

    def check(self, text):
        return hand_over_problems(text, self.rules, self.trees)

    def test_the_shipped_step_is_clean(self):
        self.assertEqual([], self.check(shipped(STEP_4E)))

    def test_the_pre_686_wording_is_reported(self):
        """The negative control the issue asks for: the text as it read before this change."""
        reported = self.check(mutate(self, shipped(STEP_4E), *PRE_686_PROSE))
        self.assertTrue(
            reported,
            "putting step 4e's pre-#686 wording back is not reported, so the check does not "
            "cover the defect it was written for")
        self.assertIn("data/temp/exports", " ".join(reported))

    def test_the_whole_pre_686_text_is_reported(self):
        """Both reverts at once, as the file actually read before this change."""
        text = mutate(self, shipped(STEP_4E), *PRE_686_PROSE)
        text = mutate(self, text, *PRE_686_CHECKPOINT)
        self.assertTrue(self.check(text))

    def test_the_pre_686_wording_is_reported_across_a_line_wrap(self):
        """⛔ (INV-346) The hand-over sentence wraps, and that is how the miss survived review."""
        text = mutate(self, shipped(STEP_4E), *PRE_686_PROSE)
        wrapped = mutate(self, text, "and only then hands the file over.",
                         "and only then hands the file\nover.")
        self.assertTrue(
            self.check(wrapped),
            "a wrapped `hands the file over` is no longer seen, so the guard has lost the "
            "wrap-awareness INV-346 requires")

    def test_an_explicit_declaration_at_the_step_is_accepted(self):
        """The rule's second arm: a deliverable may stay behind if the step says so, beside it."""
        text = mutate(self, shipped(STEP_4E), *PRE_686_PROSE)
        self.assertTrue(self.check(text), "the control's first half must fail")
        declared = mutate(
            self, text, "`data/temp/exports/<system>/`, which it recreates on every run.",
            "`data/temp/exports/<system>/`, which it recreates on every run and which is never "
            "packaged by either profile.")
        self.assertEqual([], self.check(declared),
                         "an explicit non-travel declaration beside the path is not accepted, so "
                         "the rule has only one arm")

    def test_a_staging_path_outside_a_hand_over_step_is_not_reported(self):
        """Scoped with its reason (INV-282): staging is written and never handed over.

        Module 4 fetches to `data/temp/<source>.jsonl` and moves the file to `data/raw/` once its
        checks pass. Both paths are unreachable by design and neither is a deliverable, so a guard
        that reported them would be reporting the one use of the scratch directory that is right.
        """
        text = shipped(STAGING)
        self.assertIn("data/temp/<source>.jsonl", text,
                      "Module 4's staging path is gone; this control no longer measures anything")
        self.assertEqual([], self.check(text))

    def test_a_bare_tree_is_not_a_candidate(self):
        """Limitation (a), pinned: `data/` names a tree, not an artifact handed over."""
        trees = self.trees
        self.assertIsNone(project_path("data/", trees))
        self.assertIsNone(project_path("../bootcamp-onboarding/ground-rules.md", trees))
        self.assertIsNone(project_path("module-07-query-visualize-discover/SKILL.md", trees))
        self.assertEqual("data/exports/<system>", project_path("data/exports/<system>/", trees))
        self.assertEqual("data/exports", project_path("data/exports/**", trees))

    def test_a_profile_that_stops_reaching_the_export_is_reported(self):
        """⛔ The check must fail when the PACKAGING side regresses, not only the prose side."""
        narrowed = dict(self.rules)
        narrowed["SHARE_INCLUDE"] = tuple(
            root for root in self.rules["SHARE_INCLUDE"] if root != "data/exports")
        reported = hand_over_problems(shipped(STEP_4E), narrowed, self.trees)
        self.assertTrue(
            reported,
            "dropping `data/exports` from `SHARE_INCLUDE` leaves step 4e clean, so this guard "
            "reads the prose and not the packaging rules")


class TheExportPathIsNamedWhereverItMatters(unittest.TestCase):
    """Criterion 2: step 4e, graduation and the packaging flow agree, found by scanning."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = list(shipped_texts())

    def test_no_shipped_file_still_writes_the_export_into_the_scratch_directory(self):
        stale = [relative for relative, text in self.corpus if "data/temp/exports" in text]
        self.assertEqual([], stale,
                         "the export's old scratch path survives in %r" % stale)

    def test_the_durable_path_is_named_at_the_step_the_packager_and_graduation(self):
        naming = {relative for relative, text in self.corpus if "data/exports" in text}
        for expected in (STEP_4E,
                         "plugins/senzing-bootcamp/scripts/package_bootcamp.py",
                         "plugins/senzing-bootcamp/skills/graduation/SKILL.md",
                         "plugins/senzing-bootcamp/skills/bootcamp-onboarding/packaging.md"):
            with self.subTest(site=expected):
                self.assertIn(expected, naming)

    def test_graduation_copies_the_tree_to_the_same_project_relative_path(self):
        """⛔ (INV-186) The copied export program writes there, so the destination cannot flatten."""
        graduation = shipped("plugins/senzing-bootcamp/skills/graduation/SKILL.md")
        flat = " ".join(graduation.split())
        self.assertIn("| `data/exports/**` | `production/data/exports/` |", flat)


if __name__ == "__main__":
    unittest.main()
