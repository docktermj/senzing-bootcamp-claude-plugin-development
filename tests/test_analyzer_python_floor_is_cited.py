"""Module 5's analyzer gate says where the mapping scripts run and which Python the analyzer needs.

`sz_json_analyzer.py`, the primary validator `mapping_workflow` delivers, uses a `match`
statement, so it does not parse on Python 3.9. On a 2026-10-05 run (macOS, whose system
`python3` is 3.9) the gate ran it on the host and the Bootcamper's first sight of it was a
`SyntaxError` in Senzing-provided code, which reads as a broken download. The gate said which
scripts to run and how to degrade, but not where, or with which interpreter (#462).

This guard pins the two pieces the fix added, following
`tests/test_verbatim_check_limitations_freshness.py`:

* **The gate** (`> **Availability-aware mapping validation:**`) states that all four scripts run
  where the SDK runs (container on `docker`, host on a native route); the analyzer's floor and that
  the other three carry none; a `python3 --version` check before the analyzer's first run; one
  pinned 👉 offer to install when it is below 3.10; and the decline path (skip, say why, record,
  continue, never re-ask in the session, INV-006).
* **The ⛔ entry directly after the gate** records the floor with its evidence (the `match`
  statement and its line), the server version and the date (INV-080), and says to update or remove
  it when upstream lowers or documents a different floor.

⚠️ **The measurement this pins, so a reader can repeat it.** `download_resource(filenames=
['sz_json_analyzer.py'])` on server 1.37.26, 2026-10-09, delivered a 72,786-byte script whose line
370 is `match family:`; `py_compile` failed under Python 3.9.25 at that line and passed under
3.10.19. `sz_schema_generator.py`, `sz_verbatim_check.py` and `sz_routing_report.py` compiled under
3.8.20 and 3.9.25. The script's docstring now says "Requires Python 3.10 or newer" (it did not on
1.37.19, 2026-10-05, when the `match` sat at line 367). A re-measurement that moves any of these is
an edit to the entry AND to the constants below, together.

⛔ **(INV-346) Every phrase is matched on collapsed text**: blockquote markers stripped and every
run of whitespace made one space, so a phrase wrapped across lines still matches.

**Every later site that runs the analyzer reaches the check (#509).** The gate's "Later analyzer
runs" paragraph states, once (INV-300), what a later run does: run the check there when it has not
run this session; otherwise its outcome stands (at 3.10 or newer run the command `analyze_record`
returns; after **yes** run it with `python3` replaced by the installed interpreter, named
explicitly; after **no** the skip covers the site). The three later run sites, pinned by name, each
carry a pointer to that paragraph citing INV-347 and INV-300 and restate none of it:

* step 14 (`### 14. Test`);
* step 18's full-output check (`**Validate the full output (INV-043).**`, added by #521);
* Phase 3's Rules bullet "Always validate with `analyze_record` before loading"
  (`phase3-test-load.md`).

**A file-level census** closes the set: the files under `plugins/` (listed by `tests/_corpus.py`)
that mention `analyze_record` or `sz_json_analyzer.py` are exactly `KNOWN_FILES`. A new file that
starts mentioning the analyzer fails until it is classified here, as a run site with a pointer or as
a mention that runs nothing (`ground-rules.md`'s tool-argument rule is one). The census is per file;
inside the two Module 5 files the run sites are pinned by name, not counted.

Each check is a function over the file's text, so the negative controls at the bottom run the
same predicate against a copy with the pinned part removed or changed and confirm it fails.

Enforces **INV-347** (before Module 5 runs the analyzer, the Python where it runs is checked against
the measured floor; below it, one install offer and a recorded, non-repeated skip, never a bare
`SyntaxError`). It asserts that the gate and the entry *state* this. It does **not** establish that a
live run checks before running, which only `dry-run` phase 3 can observe, or that the floor still
holds on today's server, which only a re-measurement can.

Source issues: #462 (the gate and the entry), #509 (the later sites and the census).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE5 = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-05-data-quality-mapping"
PHASE2 = MODULE5 / "phase2-data-mapping.md"
PHASE3 = MODULE5 / "phase3-test-load.md"

#: The plugin files that mention the analyzer, each classified (repo-relative, `/`-separated).
#: A run site carries the pointer; the ground rules' mention is a tool-argument rule that runs nothing.
KNOWN_FILES = {
    "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase2-data-mapping.md":
        "run sites: step 11's gate, step 14, step 18's full-output check",
    "plugins/senzing-bootcamp/skills/module-05-data-quality-mapping/phase3-test-load.md":
        "run site: the Rules bullet 'Always validate with `analyze_record` before loading'",
    "plugins/senzing-bootcamp/skills/bootcamp-onboarding/ground-rules.md":
        "not a run site: the rule that a tool argument naming a writable directory is project-local",
}
MENTIONS = (b"analyze_record", b"sz_json_analyzer.py")

#: What each later site carries (matched on collapsed text), and what it must not restate.
POINTER = ("step 11's analyzer Python check → \"Later analyzer runs\" (INV-347, INV-300)")
RESTATEMENTS = ("3.10", "python3 --version", "installed interpreter")

STEP14_HEAD = "### 14. Test"
STEP18_CHECK = "**Validate the full output (INV-043).**"
STEP18_END = "**Checkpoint:** write step 18."
PHASE3_RULE = "- Always validate with `analyze_record` before loading"

#: The measured facts. Changing one means re-measuring, then editing the entry and this together.
FLOOR = "3.10"
SERVER = "1.37.26"
MEASURED_ON = "2026-10-09"
EVIDENCE_LINE = "370"
OTHER_THREE = ("sz_schema_generator.py", "sz_verbatim_check.py", "sz_routing_report.py")

GATE_START = "> **Availability-aware mapping validation:**"
ENTRY_START = "⛔ **(INV-080) `sz_json_analyzer.py` needs Python 3.10 or newer"
NEXT_BLOCK = "⛔ **The verbatim check harvests source *values* only"
GATE_CLOSING = "> In short: check the analyzer's Python first"


def wrapped_sub(text, phrase, replacement):
    """Replace the first ``phrase`` however it is wrapped, quote markers included (a mutation helper)."""
    pattern = r"(?:\s|>)+".join(re.escape(word) for word in phrase.split(" "))
    return re.sub(pattern, lambda _: replacement, text, count=1)


def squash(text):
    return re.sub(r"\s+", " ", re.sub(r"(?m)^[ \t]*>[ \t]?", "", text)).strip()


def regions(text):
    """(gate, between, entry) as raw text, or None when a locator is missing."""
    g = text.find(GATE_START)
    e = text.find(ENTRY_START, g if g >= 0 else 0)
    n = text.find(NEXT_BLOCK, e if e >= 0 else 0)
    if min(g, e, n) < 0:
        return None
    # The gate is a run of blockquotes: the 👉 question stands in a quote of its own, so the
    # gate's numbered scripts are not read as that question's options (INV-211). Its closing
    # "In short" paragraph ends it; anything from there to the entry stands between them.
    closing = text.find(GATE_CLOSING, g)
    gate_end = text.find("\n\n", closing) if closing >= 0 else -1
    if gate_end < 0 or gate_end > e:
        return None
    return text[g:gate_end], text[gate_end:e], text[e:n]


def gate_problems(text):
    """Every acceptance criterion the gate fails, as messages (empty when it passes)."""
    found = regions(text)
    if found is None:
        return ["the gate or the floor entry was not found"]
    gate = squash(found[0])
    out = []
    for script in ("sz_json_analyzer.py",) + OTHER_THREE:
        if script not in gate:
            out.append("the gate does not name %s among the scripts it places" % script)
    if not re.search(r"All four scripts `mapping_workflow` delivers", gate):
        out.append("the gate does not say the placement covers all four scripts")
    if not re.search(r"run where the bootcamp's SDK runs: \*\*inside the container on the "
                     r"`docker` route, on the host on a native route\*\*", gate):
        out.append("the gate does not say where the scripts run on each route")
    if not re.search(r"\*\*`sz_json_analyzer\.py` needs Python 3\.10 or newer; the other three "
                     r"carry no measured floor\*\*", gate):
        out.append("the gate does not state the analyzer's floor and that the others have none")
    if not re.search(r"whatever language the Bootcamper chose", gate):
        out.append("the gate does not say the scripts are Python tools in every language")
    check = gate.find("Check the analyzer's Python before its first run")
    item1 = gate.find("1. **`sz_json_analyzer.py` (primary validation):**")
    if check < 0:
        out.append("the gate has no version check before the analyzer's first run")
    elif item1 < 0 or check > item1:
        out.append("the version check does not come before the analyzer's run instruction")
    if not re.search(r"Run `python3 --version` where the analyzer will run: inside the container "
                     r"on the `docker` route .{0,120}on the host on a native route", gate):
        out.append("the check does not run `python3 --version` where the analyzer runs")
    if "run the check rather than assume it" not in gate:
        out.append("the docker route's check may be assumed rather than run")
    if not re.search(r"On Windows the command name is `python3` too", gate):
        out.append("the check does not name the Windows command")
    if not re.search(r"a bare `SyntaxError` is never the first thing the Bootcamper sees", gate):
        out.append("the gate does not rule out a bare SyntaxError as the first sight")
    questions = re.findall(r"👉 \*\*(.*?)\*\*", gate)
    if len(questions) != 1:
        out.append("the gate should pin exactly one 👉 question, found %d" % len(questions))
    elif not (re.search(r"needs Python 3\.10 or newer", questions[0])
              and re.search(r"install a newer Python", questions[0])):
        out.append("the pinned question does not state the floor and offer the install")
    if "(respond yes or no)" not in gate:
        out.append("the pinned question has no yes/no answer hint (INV-008)")
    if not re.search(r"end the turn on this one question", gate):
        out.append("the gate does not end the turn on the question")
    if not re.search(r"alongside the existing `python3`, never replacing it", gate):
        out.append("the install path may replace the system python3")
    if not re.search(r"If the install fails, take the \*\*no\*\* path", gate):
        out.append("a failed install has no handling")
    no_path = [
        (r"tell the Bootcamper the analyzer is being skipped because the Python here is older "
         r"than 3\.10", "the no path does not say why the analyzer is skipped"),
        (r"record the skip and its reason in the source's mapping notes",
         "the no path does not record the skip"),
        (r"continue with items 2 and 3 below under their optional/best-effort handling",
         "the no path does not continue with the remaining checks"),
        (r"do not ask again \(INV-006\)", "the no path may re-ask the question"),
        (r"every later analyzer run below", "the skip does not cover the later analyzer runs"),
        (r"names the analyzer as a check that did not run \(INV-163\)",
         "the closing summary does not name the skipped check"),
        (r"Once the check has passed, a `SyntaxError` from the analyzer is not the version floor",
         "a post-check SyntaxError may be misread as the version floor"),
    ]
    for pattern, message in no_path:
        if not re.search(pattern, gate):
            out.append(message)
    return out + later_site_problems(gate)


#: The gate's later-site rule (#509), each matched on the gate's collapsed text.
LATER_SITE_RULE = [
    (r"\*\*Later analyzer runs\.\*\*", "the gate has no 'Later analyzer runs' paragraph"),
    (r"Step 14's test, step 18's full-output check and Phase 3's validation before loading "
     r"\(`phase3-test-load\.md` → \"Rules\"\) each run the command `analyze_record` returns",
     "the later-site rule does not name step 14, step 18 and Phase 3"),
    (r"each points here rather than restating this check \(INV-300\)",
     "the later-site rule does not say each site points here (INV-300)"),
    (r"\*\*The check has not run this session\*\* \(this step was skipped, or the session "
     r"resumed\): run it at that site, before the analyzer, with the same question",
     "the later-site rule does not run the check at a site where it has not run this session"),
    (r"\*\*The check already ran this session:\*\* its outcome stands, and nothing is asked "
     r"again \(INV-006\)", "the later-site rule does not keep an earlier outcome"),
    (r"At 3\.10 or newer, run the command as `analyze_record` returns it",
     "the later-site rule does not say a passed check runs the command as returned"),
    (r"After \*\*yes\*\*, run it with `python3` replaced by the installed interpreter, named "
     r"explicitly", "the later-site rule does not name the installed interpreter on yes"),
    (r"After \*\*no\*\*, the skip covers that site: do not run the analyzer there",
     "the later-site rule does not carry the no path's skip to the site"),
]


def later_site_problems(gate):
    """Every part of the later-site rule the (collapsed) gate lacks."""
    return [message for pattern, message in LATER_SITE_RULE if not re.search(pattern, gate)]


def sites(phase2, phase3):
    """{site name: raw text} for the three later run sites; a missing locator gives ''."""
    def cut(text, start, ends):
        s = text.find(start)
        if s < 0:
            return ""
        stops = [e for e in (text.find(end, s + len(start)) for end in ends) if e >= 0]
        return text[s:min(stops) if stops else len(text)]
    return {
        "step 14": cut(phase2, STEP14_HEAD, ("\n### ",)),
        "step 18's full-output check": cut(phase2, STEP18_CHECK, (STEP18_END, "\n### ")),
        "Phase 3's Rules bullet": cut(phase3, PHASE3_RULE, ("\n- ", "\n\n")),
    }


def pointer_problems(phase2, phase3):
    """Every later site that lacks the pointer, or restates the rule it points to."""
    out = []
    for name, raw in sites(phase2, phase3).items():
        if not raw:
            out.append("%s was not found" % name)
            continue
        text = squash(raw)
        if POINTER not in text:
            out.append("%s does not point to step 11's 'Later analyzer runs' (INV-347, INV-300)"
                       % name)
        elif not re.search(r"Before running the command `analyze_record` returns, follow "
                           r"(`phase2-data-mapping\.md` )?" + re.escape(POINTER), text):
            out.append("%s does not say the pointer is followed before the analyzer runs" % name)
        for phrase in RESTATEMENTS:
            if phrase in text:
                out.append("%s restates the gate (%r) instead of pointing to it" % (name, phrase))
    return out


def census_problems(files):
    """``files`` maps repo-relative paths to bytes; every unclassified or stale mention."""
    mentioning = {path for path, data in files.items() if any(m in data for m in MENTIONS)}
    out = ["%s mentions the analyzer but is not classified in KNOWN_FILES" % path
           for path in sorted(mentioning - set(KNOWN_FILES))]
    out += ["%s is classified in KNOWN_FILES but no longer mentions the analyzer" % path
            for path in sorted(set(KNOWN_FILES) - mentioning)]
    return out


def plugin_files():
    return {path.relative_to(REPO_ROOT).as_posix(): path.read_bytes()
            for path in corpus_files("plugins")}


def entry_problems(text):
    """Every way the ⛔ floor entry fails its criteria, as messages (empty when it passes)."""
    found = regions(text)
    if found is None:
        return ["the gate or the floor entry was not found"]
    _gate, between, raw_entry = found
    out = []
    if between.strip():
        out.append("the floor entry is not directly after the gate: %r stands between"
                   % squash(between)[:80])
    entry = squash(raw_entry)
    head = "needs Python %s or newer: measured on server %s, %s" % (FLOOR, SERVER, MEASURED_ON)
    if head not in entry:
        out.append("the entry's floor, server version or date is missing or changed")
    if "download_resource(filenames=['sz_json_analyzer.py'])" not in entry:
        out.append("the entry does not name the route that measures the floor")
    if not re.search(r"answers with a listing, not the script", entry):
        out.append("the entry does not say the route answers with a listing (INV-234)")
    if not re.search(r"\*\*line %s is a `match` statement\*\* \(`match family:`\)"
                     % EVIDENCE_LINE, entry):
        out.append("the entry does not cite the match statement and its line")
    if not re.search(r"fails under Python 3\.9\.25 .{0,60}and passes under 3\.10\.19", entry):
        out.append("the entry does not record both sides of the measurement")
    for script in OTHER_THREE:
        if script not in entry:
            out.append("the entry does not say %s was measured" % script)
    if "so no floor is stated for them" not in entry:
        out.append("the entry does not say the other three carry no floor")
    if not re.search(r"First measured on server 1\.37\.19, 2026-10-05", entry):
        out.append("the entry lost the first measurement")
    if not re.search(r"upstream now documents the floor", entry):
        out.append("the entry does not record that upstream documents the floor")
    if not re.search(r"\*\*If upstream lowers the floor, or documents a different one, update or "
                     r"remove this entry and the gate's check with it\*\*", entry):
        out.append("the entry does not say when to update or remove it")
    if "INV-080" not in entry:
        out.append("the entry does not cite INV-080 at its line")
    return out


class TheRegionsAreLocatable(unittest.TestCase):
    def test_the_file_exists(self):
        self.assertTrue(PHASE2.is_file(), "phase2-data-mapping.md moved")

    def test_gate_and_entry_are_found(self):
        self.assertIsNotNone(regions(PHASE2.read_text(encoding="utf-8")),
                             "the gate, the floor entry or the verbatim block was not found")


class TheGateStatesWhereAndWithWhichPython(unittest.TestCase):
    def test_every_gate_criterion_holds(self):
        problems = gate_problems(PHASE2.read_text(encoding="utf-8"))
        self.assertEqual([], problems, "; ".join(problems))


class TheFloorIsCitedDirectlyAfterTheGate(unittest.TestCase):
    def test_every_entry_criterion_holds(self):
        problems = entry_problems(PHASE2.read_text(encoding="utf-8"))
        self.assertEqual([], problems, "; ".join(problems))

    def test_gate_and_entry_state_the_same_floor(self):
        gate, _between, entry = regions(PHASE2.read_text(encoding="utf-8"))
        floors = set(re.findall(r"Python (\d+\.\d+) or newer", squash(gate) + squash(entry)))
        self.assertEqual({FLOOR}, floors, "the gate and the entry disagree on the floor")


class EveryLaterSitePointsToTheGate(unittest.TestCase):
    def test_every_later_site_carries_the_pointer(self):
        problems = pointer_problems(PHASE2.read_text(encoding="utf-8"),
                                    PHASE3.read_text(encoding="utf-8"))
        self.assertEqual([], problems, "; ".join(problems))

    def test_every_plugin_file_mentioning_the_analyzer_is_classified(self):
        problems = census_problems(plugin_files())
        self.assertEqual([], problems, "; ".join(problems))


class NegativeControls(unittest.TestCase):
    """The predicates fail on text that lacks what they pin."""

    def setUp(self):
        self.text = PHASE2.read_text(encoding="utf-8")

    def test_without_the_entry_the_locator_fails(self):
        start = self.text.index(ENTRY_START)
        end = self.text.index(NEXT_BLOCK)
        cut = self.text[:start] + self.text[end:]
        self.assertTrue(entry_problems(cut))
        self.assertTrue(gate_problems(cut))

    def test_a_changed_server_version_or_date_fails(self):
        for old, new in ((SERVER, "1.37.19"), (MEASURED_ON, "2026-10-05"),
                         ("Python 3.10 or newer: measured", "Python 3.9 or newer: measured")):
            with self.subTest(changed=old):
                start = self.text.index(ENTRY_START)
                mutated = self.text[:start] + self.text[start:].replace(old, new, 1)
                self.assertTrue(entry_problems(mutated))

    def test_the_evidence_line_is_pinned(self):
        mutated = self.text.replace("**line 370 is a", "**line 999 is a", 1)
        self.assertTrue(entry_problems(mutated))

    def test_text_between_gate_and_entry_fails(self):
        start = self.text.index(ENTRY_START)
        mutated = self.text[:start] + "An interloper paragraph.\n\n" + self.text[start:]
        self.assertIn("directly after the gate", " ".join(entry_problems(mutated)))

    def test_without_the_check_the_gate_fails(self):
        mutated = self.text.replace("Check the analyzer's Python before its first run", "", 1)
        self.assertTrue(gate_problems(mutated))

    def test_a_second_question_fails(self):
        g = self.text.index(GATE_START)
        anchor = self.text.index("> 1. **`sz_json_analyzer.py` (primary validation):**", g)
        mutated = (self.text[:anchor] + "> 👉 **Shall I also re-run the profiler?**\n>\n"
                   + self.text[anchor:])
        self.assertIn("exactly one 👉 question", " ".join(gate_problems(mutated)))

    def test_without_the_no_re_ask_rule_the_gate_fails(self):
        mutated = self.text.replace("do not ask again (INV-006)", "ask again next source", 1)
        self.assertIn("may re-ask", " ".join(gate_problems(mutated)))

    def test_without_the_later_site_rule_the_gate_fails(self):
        start = self.text.index("> **Later analyzer runs.**")
        end = self.text.index("> Once the check has passed")
        mutated = self.text[:start] + self.text[end:]
        self.assertIn("'Later analyzer runs'", " ".join(gate_problems(mutated)))

    def test_each_part_of_the_later_site_rule_is_pinned(self):
        for old, new in (("run it at that site, before the analyzer", "skip that site"),
                         ("its outcome stands", "it is asked again"),
                         ("replaced by the installed interpreter", "as returned"),
                         ("the skip covers that site", "run the analyzer anyway")):
            with self.subTest(changed=old):
                mutated = wrapped_sub(self.text, old, new)
                self.assertNotEqual(mutated, self.text)
                self.assertTrue(gate_problems(mutated))

    def test_a_site_without_the_pointer_fails(self):
        phase3 = PHASE3.read_text(encoding="utf-8")
        pointer = re.compile(r"follow(\s+`phase2-data-mapping\.md`)?\s+step\s+11's\s+analyzer"
                             r"\s+Python\s+check\s+→\s+\"Later\s+analyzer\s+runs\"\s+"
                             r"\(INV-347,\s+INV-300\)\.")
        cases = {"step 14": (STEP14_HEAD, self.text, phase3),
                 "step 18's full-output check": (STEP18_CHECK, self.text, phase3),
                 "Phase 3's Rules bullet": (PHASE3_RULE, self.text, phase3)}
        for name, (anchor, phase2, p3) in cases.items():
            with self.subTest(site=name):
                if name.startswith("Phase 3"):
                    s = p3.index(anchor)
                    p3 = p3[:s] + pointer.sub("", p3[s:], count=1)
                    self.assertNotEqual(p3, phase3)
                else:
                    s = phase2.index(anchor)
                    phase2 = phase2[:s] + pointer.sub("", phase2[s:], count=1)
                    self.assertNotEqual(phase2, self.text)
                problems = " ".join(pointer_problems(phase2, p3))
                self.assertIn("%s does not point" % name, problems)

    def test_a_pointer_not_tied_to_the_run_fails(self):
        s = self.text.index(STEP14_HEAD)
        mutated = self.text[:s] + wrapped_sub(
            self.text[s:], "Before running the command `analyze_record` returns, follow",
            "After the run, see")
        self.assertIn("step 14 does not say the pointer is followed before the analyzer runs",
                      " ".join(pointer_problems(mutated, PHASE3.read_text(encoding="utf-8"))))

    def test_a_site_restating_the_rule_fails(self):
        s = self.text.index(STEP14_HEAD)
        mutated = (self.text[:s + len(STEP14_HEAD)]
                   + "\n\nRun `python3 --version` first; below 3.10, skip the analyzer.\n"
                   + self.text[s + len(STEP14_HEAD):])
        problems = " ".join(pointer_problems(mutated, PHASE3.read_text(encoding="utf-8")))
        self.assertIn("step 14 restates the gate", problems)

    def test_an_unclassified_file_mentioning_the_analyzer_fails(self):
        files = plugin_files()
        files["plugins/senzing-bootcamp/skills/module-06-load/new-step.md"] = (
            b"Validate with `analyze_record(workspace_dir='data/mapping')` first.\n")
        self.assertIn("new-step.md mentions the analyzer but is not classified",
                      " ".join(census_problems(files)))

    def test_a_classified_file_that_stops_mentioning_the_analyzer_fails(self):
        files = plugin_files()
        files["plugins/senzing-bootcamp/skills/bootcamp-onboarding/ground-rules.md"] = b"nothing"
        self.assertIn("no longer mentions the analyzer", " ".join(census_problems(files)))

    def test_the_census_sees_the_known_files(self):
        """The census really reads the corpus: every known file is listed and mentions it."""
        files = plugin_files()
        for path in KNOWN_FILES:
            with self.subTest(path=path):
                self.assertIn(path, files)
                self.assertTrue(any(m in files[path] for m in MENTIONS))

    def test_the_pre_change_gate_fails(self):
        """The gate as it shipped before #462: no placement, no floor, no check, no entry."""
        start = self.text.index("> **Where the scripts run, and with which Python.**")
        end = self.text.index("> 1. **`sz_json_analyzer.py` (primary validation):**")
        old = self.text[:start] + self.text[end:]
        old = old[:old.index(ENTRY_START)] + old[old.index(NEXT_BLOCK):]
        self.assertGreaterEqual(len(gate_problems(old)), 1)
        self.assertGreaterEqual(len(entry_problems(old)), 1)


if __name__ == "__main__":
    unittest.main()
