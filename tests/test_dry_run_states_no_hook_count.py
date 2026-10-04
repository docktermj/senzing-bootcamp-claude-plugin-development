"""The dry-run skill must not state a hook count -- it must ask the manifest.

`plugins/senzing-bootcamp/hooks/hooks.json` declares **seven** hook entries across **six**
events: `UserPromptSubmit` carries two, `feedback-capture.py` and `checkpoint-tick.py`. The
dry-run skill said "six" in three places, and all three were instructions to execute:

  .claude/skills/dry-run/phase2-hooks-and-scripts.md:3   "Execute all six hooks and every
                                                          bundled script..."
  .claude/skills/dry-run/phase2-hooks-and-scripts.md:38  "all six must exit 0 and emit nothing"
  .claude/skills/dry-run/phase3-conversational.md:227    "executes all six directly instead"

**A run that follows the instruction literally executes six scripts and leaves one untested**,
and the one most likely dropped is the second `UserPromptSubmit` entry -- a reader who counts
*events* runs one script per event and never reaches `checkpoint-tick.py`, which drives the
durability checkpoint the fold hooks depend on. Phase 2's whole value is executing every hook;
a run that tested six of seven reports phase 2 complete.

⚠️ **"Six" was defensible as an event count and the sentence did not say events.** It said
"six hooks", then "all six must exit 0", which is a per-process claim. The ambiguity was the
defect: both readings were available and one silently under-covered.

⛔ **The fix is not "seven".** That is the same defect with a fresher number, and the next hook
addition reproduces it -- which is precisely how "six" got there. The count must come from the
file or not be stated, so this guard forbids the construction outright and derives the true
figures from the JSON.

⛔ **`plugins/senzing-bootcamp/hooks/README.md` is deliberately NOT held to the same rule.**
It enumerates every script by name in a table, which is the form that cannot rot, and its one
count ("three hooks -- `PreCompact`, `SessionEnd`, and `SessionStart`") names its members in
the same breath, so it is self-verifying rather than stale-prone. The defect was confined to
the maintainer-side skill. What this file asserts about the README is that it still enumerates.

Per **INV-246** the figures are derived by parsing `hooks.json`, never hardcoded here --
hardcoding a 7 in this file would reproduce the defect in the guard.

Source spec: `specs/dry-run-phase2-says-six-hooks-when-seven-scripts-must-run.md`.

Run:  python3 -m unittest discover -s tests
"""
import json
import re
import unittest
from pathlib import Path

from _wrapped_text import blocks, match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_JSON = REPO_ROOT / "plugins" / "senzing-bootcamp" / "hooks" / "hooks.json"
HOOKS_README = REPO_ROOT / "plugins" / "senzing-bootcamp" / "hooks" / "README.md"
DRY_RUN = REPO_ROOT / ".claude" / "skills" / "dry-run"

_CARDINAL = (r"\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve")

#: A cardinal quantifying hooks -- "six hooks", "all six", "7 hook". This is the shape that
#: goes stale, and the shape all three defect sites used. Note that site 2 was "all six must
#: exit 0", with no noun at all: the subject came from the paragraph, which is why the scan is
#: paragraph-scoped below rather than looking for `<n> hooks` alone.
#:
#: The prose that replaced them deliberately quantifies nothing: "every hook entry",
#: "one event carries a second hook". An earlier wording, "one event carries more than one
#: hook", tripped this pattern on its own non-committal phrasing -- reworded rather than
#: excepted, because an exemption here is a hole a future count can be written through.
HOOK_COUNT = re.compile(
    r"\b(?:all\s+(?:%s)\b|(?:%s)\s+hooks?\b)" % (_CARDINAL, _CARDINAL), re.I)

#: Only paragraphs whose subject is hooks are in scope.
#:
#: ⚠️ **Scoped after a first draft failed on correct prose, twice.** Applied line-by-line
#: across the whole skill, the `all <cardinal>` branch flagged `SKILL.md`'s "1, 2, 3, or all
#: three" (a count of dry-run PHASES) and `phase2`'s "all four subsections" (a count of recap
#: subsections). Both are counts of sets that do not live in `hooks.json` and neither can go
#: stale the way a hook count does. A guard that fails on correct content gets loosened by
#: whoever hits it next, so the scope is the defect's own subject.
HOOK_TOPIC = re.compile(r"hook", re.I)


def hook_paragraphs(text):
    """(unit, first line number) for each unit of prose whose subject is hooks.

    The lines are only gathered into units here; ``HOOK_COUNT`` uses ``\\s+`` and runs on the
    whole unit, so a count wrapped inside a unit is already seen (#424).

    A unit is a blank-line-delimited block, further split at list-item boundaries. The list
    split matters: `phase2`'s fixture list is one block containing both "all four subsections"
    (recap subsections, correct) and "the durability hooks" three bullets later, so a
    block-level scope read the whole list as hook prose and flagged the wrong count. One bullet
    is one claim, which is the granularity the assertion actually wants.
    """
    units, current, start = [], [], 1
    for i, line in enumerate(text.splitlines(), 1):
        boundary = not line.strip() or re.match(r"\s*[-*] ", line)
        if boundary and current:
            units.append(("\n".join(current), start))
            current, start = [], i
        if line.strip():
            if not current:
                start = i
            current.append(line)
    if current:
        units.append(("\n".join(current), start))
    for unit, line_no in units:
        if HOOK_TOPIC.search(unit):
            yield unit, line_no


#: "<cardinal> hook(s)", the figure the comparison test measures against the manifest.
NUMBERED_HOOKS = re.compile(r"\b(%s)\s+hooks?\b" % _CARDINAL, re.I)


def hook_counts(text):
    """[(lineno, cardinal)] for each "<cardinal> hook(s)" in ``text``, across line wraps.

    The lines come from ``match_lines`` (#424), so "six\nhooks" is found at the line "six" is
    on. The cardinals come from the same blocks, collapsed the same way (every run of
    whitespace to one space, trimmed) and searched in the same order, so the two lists line up.
    """
    found = []
    for block in blocks(text):
        flat = " ".join(" ".join(line for _n, line in block).split())
        found += [m.group(1) for m in NUMBERED_HOOKS.finditer(flat)]
    lines = match_lines(text, NUMBERED_HOOKS)
    assert len(lines) == len(found), "match_lines and the block scan disagree"
    return list(zip(lines, found))


def hook_manifest():
    """The entries hooks.json actually declares, as [(event, command), ...]."""
    events = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
    return [(event, hook["command"])
            for event, groups in events.items()
            for group in groups
            for hook in group["hooks"]], events


def phase_files():
    return sorted(DRY_RUN.glob("*.md"))


def read(path):
    return path.read_text(encoding="utf-8")


class TheManifestIsWhatThisGuardMeasuresAgainst(unittest.TestCase):
    """Anti-vacuity, and the derivation the spec requires instead of a literal."""

    def test_the_manifest_parses_and_declares_entries(self):
        entries, events = hook_manifest()
        self.assertGreater(len(entries), 0, "hooks.json declares no hook entries")
        self.assertGreater(len(events), 0, "hooks.json declares no events")

    def test_at_least_one_event_carries_more_than_one_entry(self):
        """This is what makes the entries-not-events warning load-bearing.

        If every event carried exactly one hook, the warning below would be advice about a
        hazard that does not exist, and counting events would be a correct way to count hooks.
        The moment that stops being true the warning must stay -- so assert the condition it
        exists for, rather than asserting the number 7.
        """
        entries, events = hook_manifest()
        self.assertGreater(
            len(entries), len(events),
            "every event now carries exactly one hook, so 'iterate entries, not events' no "
            "longer describes a real hazard. Either an entry was removed, or this guard is "
            "reading a manifest it does not understand")

    def test_the_phase_files_are_found(self):
        found = phase_files()
        self.assertGreater(
            len(found), 1,
            "the dry-run skill has fewer than two markdown files; this guard is scanning "
            "almost nothing and would pass forever")


class NoDryRunFileStatesAHookCount(unittest.TestCase):
    def test_no_markdown_in_the_skill_quantifies_hooks(self):
        offenders = []
        for path in phase_files():
            for block, line_no in hook_paragraphs(read(path)):
                for match in HOOK_COUNT.finditer(block):
                    offenders.append("%s:~%d %r" % (path.name, line_no, match.group(0)))
        self.assertEqual(
            [], offenders,
            "the dry-run skill states a hook count: %s. A count of a set that lives in "
            "hooks.json disagrees with it the moment an entry is added — which is how 'all "
            "six' outlived a seven-entry manifest, telling three separate instructions to "
            "execute one script fewer than exist. Name the file or the command that lists "
            "them" % offenders)

    def test_any_count_that_does_appear_would_have_to_match_the_manifest(self):
        """The spec's criterion stated as a comparison, not only as a prohibition.

        The assertion above should keep this set empty; this one is what makes the *derivation*
        real, so that a count reintroduced as the currently-true figure is still measured
        against the file rather than believed.
        """
        entries, _ = hook_manifest()
        spelled = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
                   7: "seven", 8: "eight", 9: "nine", 10: "ten"}
        truthful = {str(len(entries)), spelled.get(len(entries), "")}
        for path in phase_files():
            for i, cardinal in hook_counts(read(path)):
                with self.subTest(site="%s:%d" % (path.name, i)):
                    self.assertIn(
                        cardinal.lower(), truthful,
                        "%s:%d says %r hooks; hooks.json declares %d entries"
                        % (path.name, i, cardinal, len(entries)))

    def test_a_wrapped_count_is_read_at_its_line(self):
        """Negative control (#424): "six" ends line 2 and "hooks" begins line 3."""
        wrapped = "Phase 2 runs the scripts.\nIt then checks that all six\nhooks exit 0.\n"
        self.assertEqual([(2, "six")], hook_counts(wrapped))
        # The old line-at-a-time read, kept only to show the fixture is the hard case.
        self.assertFalse(any(NUMBERED_HOOKS.search(l) for l in wrapped.split("\n")))


class TheInstructionNamesItsSourceInstead(unittest.TestCase):
    def test_phase_two_names_the_manifest(self):
        text = read(DRY_RUN / "phase2-hooks-and-scripts.md")
        self.assertIn(
            "hooks/hooks.json", text,
            "phase 2 no longer names the manifest, so the reader has no way to obtain the "
            "list the count used to (mis)state")

    def test_phase_two_warns_that_an_event_can_carry_a_second_hook(self):
        flat = re.sub(r"\s+", " ", read(DRY_RUN / "phase2-hooks-and-scripts.md"))
        self.assertRegex(
            flat, r"(?i)entries,? not events",
            "phase 2 does not tell the reader to iterate entries rather than events — the "
            "exact mistake that leaves the second UserPromptSubmit hook untested")

    def test_phase_two_names_the_script_a_reader_would_actually_miss(self):
        """Derived from the manifest: the second entry on the doubled-up event."""
        entries, events = hook_manifest()
        doubled = [ev for ev, groups in events.items()
                   if sum(len(g["hooks"]) for g in groups) > 1]
        text = read(DRY_RUN / "phase2-hooks-and-scripts.md")
        for event in doubled:
            with self.subTest(event=event):
                self.assertIn(
                    event, text,
                    "%s carries more than one hook and phase 2 never names it, so the warning "
                    "cannot be acted on" % event)
                second = [c for ev, c in entries if ev == event][1]
                script = second.rstrip('"').split("/")[-1]
                self.assertIn(
                    script, text,
                    "phase 2 warns about a doubled-up event without naming %s, the script a "
                    "reader who iterates events actually skips" % script)

    def test_phase_three_no_longer_states_a_count(self):
        flat = re.sub(r"\s+", " ", read(DRY_RUN / "phase3-conversational.md"))
        self.assertNotRegex(
            flat, r"(?i)executes all (?:%s)\b" % _CARDINAL,
            "phase3-conversational.md still states a count for what phase 2 executes")


class TheShippedReadmeStillEnumerates(unittest.TestCase):
    """Criterion 5: the README was already correct and must stay that way.

    It is held to *enumeration*, not to the no-count rule — its own count names its members
    in the same sentence, which is self-verifying. What would break it is a script existing in
    hooks.json and not in the table.
    """

    def test_every_declared_script_is_named_in_the_readme(self):
        entries, _ = hook_manifest()
        text = read(HOOKS_README)
        for event, command in entries:
            script = command.rstrip('"').split("/")[-1]
            with self.subTest(script=script):
                self.assertIn(
                    script, text,
                    "hooks.json declares %s under %s and hooks/README.md does not name it, so "
                    "the enumeration that replaced counting is itself incomplete"
                    % (script, event))


if __name__ == "__main__":
    unittest.main()
