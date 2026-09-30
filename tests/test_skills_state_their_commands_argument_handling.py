"""Each skill states the argument handling its same-name command carried, because the skill runs.

When a project skill and a project command share a name, `/<name>` runs the **skill**, with or
without an argument (measured 2026-09-29 on Claude Code 2.1.284, #241). So none of the ten
same-name files under `.claude/commands/` has ever run here, and every rule stated only in one
of them -- all ten `argument-hint` lines, and each `$ARGUMENTS` rule such as `/dry-run`'s "ask
which phases" or `/release`'s "do not pick a bump" -- was never in effect. #241 moved them into
the skills. This guard keeps them there:

* **The hint.** Each skill in `ARGUMENT_RULES` carries an `argument-hint` in its frontmatter,
  and where its same-name command still ships, the two hints are the same string.
* **The rules.** Each `$ARGUMENTS` rule is a row of `ARGUMENT_RULES`: a pattern locating the
  rule in the command, and one or more patterns the skill's text must match. ⛔ **Every
  paragraph or bullet of a shipping command that names `$ARGUMENTS` must be matched by a row**,
  so a rule added to a command cannot pass unnoticed by being absent from the table, and a row
  whose command pattern matches nothing fails as stale.
* **The invocation.** No skill sets `disable-model-invocation` (the ten skills stay
  model-invocable), and none says it is "invoked explicitly rather than inferred", a sentence
  the `dry-run` command file carried that would be false in a model-invocable skill.

**INV-333** is the invariant this enforces for the costly choices: `/dry-run`'s phase 3,
`/auto-test`'s simulated walk and `/release`'s bump are asked about, never defaulted from an
empty argument. The rows pinning those three sentences are its checks; like the rest of this
guard they establish that the rule is stated, not that a live run asks.

`TheChecksAreNotVacuous` is the negative control, run on every suite: removing one skill's
`argument-hint`, or one moved rule's sentence, fails the check that covers it (INV-265).

⚠️ **When the commands go (#262)**, the command-side checks skip with a stated reason rather
than pass over an empty set (INV-308), and the skill-side checks keep running from the table,
which is then the record of what the commands said. (⚠️ **Dated note, 2026-09-30 (#262):** the
ten command files are deleted, and this is the state the guard now runs in.)

⚠️ **What this does NOT establish.** It pins that the rules are *stated* in each skill. It cannot
establish that a live run obeys one (that `/dry-run` with no argument actually asks), nor that
the skill's wording means what the command's did. That was read when #241 moved them, and the
moved-rule list is in #241's `specs/IMPLEMENTED.md` entry. Rules a command states that are not
about its argument are listed there too, and are not pinned here.

Stdlib only; the skill and command files are read as text (INV-108).

Source issue: #241.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

#: skill name -> rows of (label, pattern locating the rule in the command, patterns the skill
#: must match). Patterns match text with every run of whitespace collapsed to one space.
ARGUMENT_RULES = {
    "auto-test": [
        ("no argument: ask which halves",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, present the two halves and ask",
         [r"No argument: present the two halves and ask which to run",
          r"⛔ \*\*The walk is never inferred from silence\.\*\*"]),
        ("an argument naming a walk runs both, with the walk's parameters",
         r"If `\$ARGUMENTS` \*\*names a walk\*\*",
         [r"An argument naming a walk\*\* is the answer: run both",
          r"otherwise the defaults \(`terse`, 12\) stand"]),
    ],
    "compact-dev-environment": [
        ("no argument: full census, all four classes",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, take the full census",
         [r"With no argument, take the full census and assess all four classes, then propose "
          r"a plan"]),
        ("a named class still takes the full census",
         r"If `\$ARGUMENTS` \*\*names a class\*\*",
         [r"With an argument naming a class \(`invariants`, `specs`, `tests` or `feedback`\), "
          r"still take the full census",
          r"scope only the assessment and the plan to that class"]),
    ],
    "delegate-to-mcp-server": [
        ("no argument: all four sources, bounded at Step 3",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, build the re-check list from all four",
         [r"With no argument, build the list from all four sources and bound the inventory at "
          r"Step 3"]),
        ("a named area or category is the bound, reported",
         r"If `\$ARGUMENTS` \*\*names an area or category\*\*",
         [r"With an argument naming an area or category, take that as the bound, and say so "
          r"in the Step 10 report"]),
    ],
    "dry-run": [
        ("no argument: ask which phases",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, run the skill's own question",
         [r"Ask which phases to run\*\* if the maintainer did not say, including when there "
          r"is no argument",
          r'do not read "dry-run the plugin" as "all three"',
          r'so it is never implied by "dry-run the plugin"']),
        ("named phases answer the question",
         r"If `\$ARGUMENTS` \*\*names phases\*\*",
         [r"An argument naming phases is the answer to this question:\*\* start at the "
          r"lowest one"]),
        ("a trailing module name answers phase 3's second question",
         r"If \*\*phase 3 is among them\*\*",
         [r"A trailing module name in the argument answers it"]),
    ],
    "feedback-to-issues": [
        ("no argument: default candidates, else stop",
         r"If `\$ARGUMENTS` is empty, default to",
         [r"An explicit path the maintainer gave \(argument or message\)",
          r"`SENZING_BOOTCAMP_PLUGIN_FEEDBACK\.md` at the repo root",
          r"If none is found, say so and stop"]),
    ],
    "production-readiness-audit": [
        ("no argument: the run chooses the scope",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, let the run choose the scope",
         [r"With no argument, those four are the scope the run chooses"]),
        ("a named area is swept first, generators still run",
         r"If `\$ARGUMENTS` \*\*names an area\*\*, sweep that first",
         [r"With an argument naming an area, sweep that first, and still run every lead "
          r"generator\*\*"]),
    ],
    "propagate-to-public": [
        ("no argument: the default checkout",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, use the skill's default checkout",
         [r"With no argument, use the default checkout"]),
        ("an argument is the destination",
         r"If `\$ARGUMENTS` is \*\*given\*\*",
         [r"An argument is the path to the public repo's working tree: pass it to "
          r"`propagate\.sh` as its destination"]),
        ("an uncertain destination is asked about",
         r"If the destination does not exist",
         [r"or the destination does not exist, is not a git repo, or its `origin` is not "
          r"`Senzing/senzing-bootcamp-claude-plugin`, ask"]),
    ],
    "release": [
        ("no argument: dry run, show both versions, ask",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, run the dry run with no bump named",
         [r"With no argument, run the dry run with no bump named, show the maintainer the "
          r"current version and the newest tag, and ask",
          r"\*\*Never invent the version\.\*\*"]),
        ("a named bump is a flag",
         r"If `\$ARGUMENTS` names `major`, `minor` or `patch`",
         [r"Pass `major`, `minor` or `patch` as `--major`/`--minor`/`--patch`"]),
        ("an explicit version is positional",
         r"If `\$ARGUMENTS` is an explicit `MAJOR\.MINOR\.PATCH` version",
         [r"an explicit `MAJOR\.MINOR\.PATCH` version positionally"]),
    ],
    "retrofit-from-public": [
        ("no argument: the default checkout",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, use the skill's default checkout",
         [r"With no argument, use the default checkout"]),
        ("an argument is the source",
         r"If `\$ARGUMENTS` is \*\*given\*\*",
         [r"An argument is the path to the public repo's working tree: pass it to "
          r"`retrofit\.sh` as its source"]),
        ("an uncertain source is asked about",
         r"If the source does not exist",
         [r"or the source does not exist, is not a git repo, or its `origin` is not "
          r"`Senzing/senzing-bootcamp-claude-plugin`, ask"]),
    ],
    "review-invariants": [
        ("no argument: the first pending block",
         r"If `\$ARGUMENTS` is \*\*empty\*\*, load the queue and start at the first pending",
         [r"With no argument, start at the first pending block"]),
        ("a named number is where to start",
         r"If `\$ARGUMENTS` \*\*names a number\*\*",
         [r"an argument naming a number starts there, as the `<n>` that `show` and `sites` "
          r"take"]),
    ],
}

#: The line a command uses to hand its argument over, e.g. "Phases to run: $ARGUMENTS". It
#: names the argument without stating a rule about it.
HANDOVER = re.compile(r"^[A-Z][^:\n]*: \$ARGUMENTS$")

#: A sentence that is false for a model-invocable skill (#241).
EXPLICIT_ONLY = re.compile(r"invoked\s+explicitly\s+rather\s+than\s+inferred", re.I)


def squash(text):
    return re.sub(r"\s+", " ", text).strip()


def split_frontmatter(text):
    """(frontmatter lines, body) for a file opening with a `---` block; ([], text) otherwise."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return [], text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return [], text


def frontmatter_value(text, key):
    """The raw value of a top-level frontmatter key, or None when the key is absent."""
    for line in split_frontmatter(text)[0]:
        if line.startswith(key + ":"):
            return line[len(key) + 1:].strip()
    return None


def argument_units(command_text):
    """Each paragraph or bullet of a command body that names `$ARGUMENTS`, whitespace-collapsed.

    A bullet runs from its `- ` line through the indented lines that continue it; a paragraph
    runs to the next blank line. The hand-over line is not a rule and is dropped.
    """
    units, current = [], []

    def flush():
        if current:
            units.append(squash("\n".join(current)))
            current.clear()

    for line in split_frontmatter(command_text)[1].split("\n"):
        if not line.strip():
            flush()
        elif line.startswith("- ") or HANDOVER.match(line.strip()):
            flush()
            current.append(line)
            if HANDOVER.match(line.strip()):
                flush()
        else:
            current.append(line)
    flush()
    return [u for u in units if "$ARGUMENTS" in u and not HANDOVER.match(u)]


def unmatched_units(skill, command_text):
    """Command units naming `$ARGUMENTS` that no row of `ARGUMENT_RULES[skill]` locates."""
    patterns = [re.compile(row[1]) for row in ARGUMENT_RULES.get(skill, [])]
    return [u for u in argument_units(command_text) if not any(p.search(u) for p in patterns)]


def stale_rows(skill, command_text):
    """Rows of `ARGUMENT_RULES[skill]` whose command pattern matches nothing in the command."""
    body = squash(split_frontmatter(command_text)[1])
    return [row[0] for row in ARGUMENT_RULES[skill] if not re.search(row[1], body)]


def missing_rules(skill, skill_text):
    """(row label, pattern) pairs the skill's text does not match."""
    body = squash(skill_text)
    return [(label, pat)
            for label, _cmd, pats in ARGUMENT_RULES[skill]
            for pat in pats if not re.search(pat, body)]


def hint_problems(skill_text, command_text):
    """Why a skill's `argument-hint` fails: absent, or (when the command ships) different."""
    hint = frontmatter_value(skill_text, "argument-hint")
    if not hint:
        return ["the skill's frontmatter has no argument-hint"]
    if command_text is not None:
        wanted = frontmatter_value(command_text, "argument-hint")
        if hint != wanted:
            return ["argument-hint %s differs from the command's %s" % (hint, wanted)]
    return []


def read(path):
    return path.read_text(encoding="utf-8")


def skill_path(name):
    return SKILLS_DIR / name / "SKILL.md"


def same_name_commands():
    """{skill name: command path} for every command whose stem is a skill in the table."""
    return {p.stem: p for p in sorted(COMMANDS_DIR.glob("*.md"))
            if p.stem in ARGUMENT_RULES and skill_path(p.stem).is_file()}


class TheTableIsNotVacuous(unittest.TestCase):
    """INV-265: a table with nothing in it, or naming skills that do not exist, proves nothing."""

    def test_the_table_names_the_ten_skills(self):
        self.assertEqual(10, len(ARGUMENT_RULES),
                         "ARGUMENT_RULES should hold the ten skills #241 moved rules into")
        self.assertGreaterEqual(sum(len(rows) for rows in ARGUMENT_RULES.values()), 23)

    def test_every_skill_in_the_table_exists(self):
        missing = sorted(n for n in ARGUMENT_RULES if not skill_path(n).is_file())
        self.assertEqual([], missing, "skills named in ARGUMENT_RULES with no SKILL.md")

    def test_the_unit_parser_finds_the_rules(self):
        """Anchored on dry-run, whose command states three `$ARGUMENTS` rules."""
        command = COMMANDS_DIR / "dry-run.md"
        if not command.is_file():
            self.skipTest("%s no longer ships (#262); nothing to parse" % command.name)
        self.assertEqual(3, len(argument_units(read(command))),
                         "the parser no longer finds dry-run's three $ARGUMENTS rules")


class EachSkillCarriesItsArgumentHint(unittest.TestCase):
    def test_every_skill_has_an_argument_hint_matching_its_command(self):
        commands = same_name_commands()
        for name in sorted(ARGUMENT_RULES):
            with self.subTest(skill=name):
                command = commands.get(name)
                self.assertEqual(
                    [], hint_problems(read(skill_path(name)),
                                      read(command) if command else None),
                    "%s: /%s runs the skill, so the command's argument-hint never showed; "
                    "the skill's frontmatter must carry it (#241)" % (name, name))

    def test_no_skill_disables_model_invocation(self):
        for name in sorted(ARGUMENT_RULES):
            with self.subTest(skill=name):
                self.assertIsNone(
                    frontmatter_value(read(skill_path(name)), "disable-model-invocation"),
                    "%s sets disable-model-invocation; #241 keeps all ten model-invocable"
                    % name)

    def test_no_skill_says_it_is_invoked_explicitly(self):
        for name in sorted(ARGUMENT_RULES):
            with self.subTest(skill=name):
                self.assertIsNone(
                    EXPLICIT_ONLY.search(read(skill_path(name))),
                    "%s says it is invoked explicitly rather than inferred, which is false "
                    "for a model-invocable skill" % name)


class EachSkillStatesItsArgumentRules(unittest.TestCase):
    def test_every_rule_in_the_table_is_stated_in_the_skill(self):
        for name in sorted(ARGUMENT_RULES):
            with self.subTest(skill=name):
                self.assertEqual(
                    [], missing_rules(name, read(skill_path(name))),
                    "%s no longer states an argument rule its command carried; the skill is "
                    "what runs, so the rule is not in effect anywhere else" % name)

    def test_every_commands_argument_rule_has_a_row(self):
        commands = same_name_commands()
        if not commands:
            self.skipTest("no same-name command ships (#262); ARGUMENT_RULES is the record")
        for name, command in commands.items():
            with self.subTest(command=command.name):
                self.assertEqual(
                    [], unmatched_units(name, read(command)),
                    "%s states a $ARGUMENTS rule no row of ARGUMENT_RULES covers: move it "
                    "into the skill and add a row" % command.name)

    def test_no_row_is_stale(self):
        commands = same_name_commands()
        if not commands:
            self.skipTest("no same-name command ships (#262); rows cannot be located")
        for name, command in commands.items():
            with self.subTest(command=command.name):
                self.assertEqual([], stale_rows(name, read(command)),
                                 "rows whose command pattern matches nothing in %s"
                                 % command.name)


class TheChecksAreNotVacuous(unittest.TestCase):
    """Negative controls, run on every suite: each mutation must fail the check it targets."""

    def test_removing_one_skills_argument_hint_fails(self):
        text = read(skill_path("release"))
        command = COMMANDS_DIR / "release.md"
        command_text = read(command) if command.is_file() else None
        self.assertEqual([], hint_problems(text, command_text), "release is failing as shipped")
        stripped = re.sub(r"(?m)^argument-hint:.*\n", "", text, count=1)
        self.assertNotEqual(text, stripped, "the mutation did not land")
        self.assertTrue(hint_problems(stripped, command_text))

    def test_a_changed_hint_fails_while_the_command_ships(self):
        command = COMMANDS_DIR / "dry-run.md"
        if not command.is_file():
            self.skipTest("%s no longer ships (#262)" % command.name)
        text = read(skill_path("dry-run")).replace(
            "argument-hint: \"[phases:", "argument-hint: \"[stages:", 1)
        self.assertTrue(hint_problems(text, read(command)))

    def test_removing_one_moved_rule_fails(self):
        text = read(skill_path("dry-run"))
        self.assertEqual([], missing_rules("dry-run", text), "dry-run is failing as shipped")
        sentence = "A trailing module name in the argument answers\n   it."
        self.assertIn(sentence, text, "the mutation target moved; re-anchor this control")
        self.assertEqual(
            ["a trailing module name answers phase 3's second question"],
            [label for label, _ in missing_rules("dry-run", text.replace(sentence, ""))])

    def test_a_command_rule_with_no_row_fails(self):
        command = COMMANDS_DIR / "review-invariants.md"
        if not command.is_file():
            self.skipTest("%s no longer ships (#262)" % command.name)
        text = read(command) + "\n- If `$ARGUMENTS` **names a range**, walk only that range.\n"
        self.assertEqual(1, len(unmatched_units("review-invariants", text)))

    def test_the_explicit_only_sentence_is_caught(self):
        self.assertTrue(EXPLICIT_ONLY.search(
            "This is a test-gate action, which is why it is invoked\nexplicitly rather than "
            "inferred."))


if __name__ == "__main__":
    unittest.main()
