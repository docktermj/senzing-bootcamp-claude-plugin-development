"""Every option of every pinned gate has a handler marker entry saying what happens next.

Both Module 5 quality gates offered *"improve the data first"* and **no step in the plugin
defined what the guide does when it is chosen** — no procedure, no loop-back, no re-score,
no re-entry point. The file went from the pinned question straight to *"Success indicator"*
and Phase 1 ended. Hit live on 2026-08-28: CRM_EXPORT scored **75.1**, the gate was
presented as pinned, the maintainer answered **1**, and there was nothing to execute.

⛔ **This is the unsatisfiable-instruction shape, on the ANSWER side.** INV-056 pins every
gate question's wording and INV-247 requires every 👉 to trace to a step in a shipped skill
file — both govern the *ask*. Nothing governed what happens on the *answer*, so a guide
facing a chosen option with no procedure must improvise, and improvising against a pinned
gate teaches that the surrounding ⛔ rules are advisory.

**The wider check (#531, part of #504).** Until #531 this guard scanned one module
(`module-05-data-quality-mapping`) and only options whose leading verb was *iterate* or
*improve*, so five options in Modules 3, 5 and 6 shipped with no handler (#526–#530). It now
scans **every skill file** and **every option** of every gate:

- **A gate** is a bold 👉 question with a numbered list directly beneath it, outside a code
  fence, in any `*.md` under `plugins/senzing-bootcamp/skills/` (INV-246: derived, no module
  list and no verb list). The question may wrap, and may sit in a list item or a blockquote.
  **Every bold 👉 question saying `Reply with a number` or `Reply with one or more numbers` is a
  gate too (#620)**, list or not: one whose options are built in prose at runtime has no list
  beneath it, and until #620 two such gates (Bootcamp preparation's programming-language gate
  and Module 7 step 3a's recall question) shipped with no marker.
- **Its marker** is the first `**Handling each answer (INV-284).**` below its options and above
  the next heading, modeled on Module 7 step 3b's. Gates asked in place of one another (the
  bands of one quality gate, or a question's alternative forms) share the marker below the
  last of them.
- **Each entry** is a bullet at the marker's indent whose bold label names the option by
  number and by its opening words: `- **2, "Move forward":**`, `- **1, repair**`, or, where
  two gates share the marker, `- **2, "Continue to mapping now" or "Proceed anyway":**`. The
  entry then says what happens and where the flow resumes, or points to the step in the file
  that already says it (INV-300). The opening words must match the option's text, so a marker
  borrowed from a neighboring gate, a renumbered option or a stale entry fails.
- **A runtime list** (options that are placeholders, such as `` `<DATA_SOURCE>` `` or
  `{feature type}`) has no fixed options to name, so it carries one `- **Each number:**` entry.

It fails when a gate has no marker, when the marker leaves an option out, when an entry names
an option the gate does not have, and when the scan finds fewer gates than the floor (INV-265).
Each module's negative control removes a real entry from that module's shipped text, and one
of them removes Module 6 Phase D's "Iterate now" entry. The phrase checks read wrapped text
(INV-346): a question, an option or an entry label may wrap without changing the result.

⚠️ **What this establishes:** every gate's options are each named in a handler marker. It
does **not** establish that the entry's handling is correct or that a live guide follows it;
only `dry-run` phase 3 can observe that.

Enforces **INV-284** — every option a pinned gate offers has a handling step (a section in the
same skill file, or an inline branch at the gate) saying what the guide does when it is chosen and
where the flow resumes; and where that step changes the state the gate measured, re-presenting the
gate is not an INV-006 repeat.

Also enforces **INV-345** (on a `provenance: synthesized` source, disclose the deliberate gaps
before the gate's 👉, and never regenerate the Bootcamper's data silently):
`test_a_synthesized_source_is_disclosed_before_the_question` and
`test_it_forbids_silent_regeneration`. They assert that the skill file *states* both rules, and do
**not** establish that a live turn discloses before it asks or never regenerates silently, which
only `dry-run` phase 3 can observe.

#521 extends the disclosure to Phase 2 step 16's quality gate (INV-345's 2026-10-12 note, queued for
the maintainer's sign-off): `Step16DisclosesOnASynthesizedSource` asserts that step 16 points at
Phase 1's one statement of the wording (INV-300) before the 70-79% and <70% questions of both
blocks, keeps those questions verbatim with both options, and marks no ≥80% question.

#619 (part of #602) applies the answer side to Module 4 Step 2's provision path:
`Module4ProvisionPathCarriesOutEachAnswer` asserts that option 5's entry writes the source's
registry entry from `docs/business_problem.md` with `provenance: synthesized` and a
`quality_intent`, then points at Step 2's `provenance: synthesized` generation block, and names
no CORD route and no new 👉; that each entry of the secondary offer (read from its quote, not
listed) has its own entry under the marker, "Synthesized test data" pointing at option 5's entry
rather than restating its two steps (INV-300) and "Free raw data" recording
`provenance: free_data` after a count; and that the CORD recommendation, the free-data hierarchy and "last resort" are
scoped to a Bootcamper who did not choose option 5. Negative controls mutate the shipped text. It
asserts the file *states* the routes, and cannot establish that a live guide follows them.

Source spec:
`specs/the-quality-gates-improve-option-has-no-procedure-and-is-incoherent-on-a-generated-scenario.md`.
Source issue: #531 (part of #504). Widened by #620 (part of #602), which also pins the gate
answers `Issue620AnswersAreCarriedOut` checks: Module 4 Step 8a sub-step 6 and Step 8b sub-step 3
ask nothing the gate already answered, and Module 1's two confirmation gates revise and re-present
on a no.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from collections import namedtuple
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
MODULE = SKILLS / "module-05-data-quality-mapping"

#: The handler marker, verbatim (Module 7 step 3b's shape).
MARKER = "**Handling each answer (INV-284).**"
#: Where a bold 👉 question starts. A 👉 in running prose ("the pending 👉 question") is not one.
QUESTION = "👉 **"
#: Leading blockquote markers, each with the one optional space after it.
_QUOTE = re.compile(r"^[ \t]*(?:>[ \t]?)+")
_FENCE = re.compile(r"^[ \t]*(?:>[ \t]?)*[ \t]*(`{3,}|~{3,})")
_HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
_OPTION = re.compile(r"^(?P<indent>[ \t]*)(?P<num>\d+)\.[ \t]+(?P<text>\S.*?)\s*$")
_BULLET = re.compile(r"^(?P<indent>[ \t]*)-[ \t]+(?P<text>\S.*?)\s*$")
_LABEL = re.compile(r"^\*\*(?P<label>.+?)\*\*")
_NUMBERED = re.compile(r"^(?P<num>\d+),\s*(?P<rest>.*)$")
_EACH = re.compile(r"^Each number\b")
#: A numbered-reply question, on normalized text (#620): a gate whether or not a list follows.
REPLY = re.compile(r"reply with (?:a|one or more) number")

#: The scan's floors (INV-265). At #531 it found 51 gates with 141 options in 19 files across
#: 10 skill directories; each floor sits a little under that so a gate retired on purpose does
#: not fail it, while a parser that stops finding gates does.
MIN_GATES = 45
MIN_OPTIONS = 125
MIN_FILES = 15
MIN_MODULES = 9
#: #620 found 49 `Reply with (a|one or more) number` questions; the floor sits under that.
MIN_REPLIES = 45

Gate = namedtuple("Gate", "line question options end")
Entry = namedtuple("Entry", "num quotes start stop")


def _indent(line):
    return len(line) - len(line.lstrip(" \t"))


def norm(text):
    """Lower case, emphasis and code marks dropped, whitespace collapsed (INV-346)."""
    return re.sub(r"\s+", " ", text.replace("*", "").replace("`", "")).strip().lower()


def prose_lines(text):
    """Each line with its blockquote markers stripped, or None inside (or on) a code fence."""
    out, fence = [], None
    for line in text.split("\n"):
        m = _FENCE.match(line)
        if fence is None and m:
            fence = m.group(1)[0]
            out.append(None)
        elif fence is not None:
            if m and m.group(1)[0] == fence:
                fence = None
            out.append(None)
        else:
            out.append(_QUOTE.sub("", line, count=1))
    return out


def _read_options(prose, k):
    """[(number, text)] for the numbered list starting at line k, and the line after it."""
    options, base, blank, last = [], None, False, k
    while k < len(prose) and prose[k] is not None:
        line = prose[k]
        if not line.strip():
            blank = True
            k += 1
            continue
        m = _OPTION.match(line)
        if m and int(m.group("num")) == len(options) + 1 and base in (None, _indent(line)):
            base = _indent(line)
            options.append([int(m.group("num")), m.group("text")])
        elif options and not blank and _indent(line) > base:
            options[-1][1] += " " + line.strip()     # a wrapped option
        else:
            break
        blank, last = False, k
        k += 1
    return [tuple(o) for o in options], last + 1


def gates(text):
    """Every bold 👉 question with a numbered list directly beneath it."""
    prose = prose_lines(text)
    found, i = [], 0
    while i < len(prose):
        line = prose[i]
        if line is None or QUESTION not in line:
            i += 1
            continue
        question, j = line[line.index(QUESTION):], i
        while question.count("**") % 2 and j + 1 < len(prose) and (prose[j + 1] or "").strip():
            j += 1
            question += " " + prose[j].strip()   # a wrapped question
        k = j + 1
        while k < len(prose) and prose[k] is not None and not prose[k].strip():
            k += 1
        m = _OPTION.match(prose[k]) if k < len(prose) and prose[k] is not None else None
        if m and m.group("num") == "1":
            options, end = _read_options(prose, k)
            found.append(Gate(i + 1, norm(question), options, end))
            i = end
        elif REPLY.search(norm(question)):
            found.append(Gate(i + 1, norm(question), (), j + 1))   # options built in prose
            i = j + 1
        else:
            i = j + 1
    return found


def reply_questions_missed(text, name="text"):
    """Every numbered-reply question line no gate covers (#620)."""
    spans = [range(g.line, g.end + 1) for g in gates(text)]
    return ["%s:%d" % (name, n + 1) for n, line in enumerate(prose_lines(text))
            if line is not None and REPLY.search(norm(line)) and QUESTION in line
            and not any(n + 1 in s for s in spans)]


def find_marker(prose, start):
    """The index of the first marker line at or after ``start``, above the next heading."""
    for k in range(start, len(prose)):
        line = prose[k]
        if line is None:
            continue
        if _HEADING.match(line):
            return None
        if MARKER in line:
            return k
    return None


def marker_bullets(text, m):
    """[(start, stop)] for every bullet at the marker's indent in the block at line m."""
    raw, prose = text.split("\n"), prose_lines(text)
    ind = _indent(prose[m])
    k = m + 1
    while k < len(prose) and (prose[k] or "").strip() and not (
            _BULLET.match(prose[k]) and _indent(prose[k]) == ind):
        k += 1                                   # the marker's lead sentence, if it wraps
    bullets = []
    while k < len(prose):
        line = prose[k]
        if line is None:                         # a fence inside an entry belongs to it
            if bullets and _indent(raw[k]) > ind:
                bullets[-1][1] = k + 1
                k += 1
                continue
            break
        if not line.strip():
            k += 1
            continue
        b = _BULLET.match(line)
        if b and _indent(line) == ind:
            bullets.append([k, k + 1])
        elif bullets and _indent(line) > ind:
            bullets[-1][1] = k + 1
        else:
            break
        k += 1
    return [tuple(b) for b in bullets]


def marker_entries(text, m):
    """Every entry in the marker block at line m: Entry(num | 'each', quotes, start, stop)."""
    prose = prose_lines(text)
    entries = []
    for start, stop in marker_bullets(text, m):
        body = " ".join((prose[n] or "").strip() for n in range(start, stop))
        label = _LABEL.match(re.sub(r"^-\s+", "", body))
        if not label:
            continue
        text_label = label.group("label").strip()
        if _EACH.match(text_label):
            entries.append(Entry("each", (), start, stop))
            continue
        n = _NUMBERED.match(text_label)
        if not n:
            continue                             # a bullet in the block that is not an entry
        rest = n.group("rest").strip().rstrip(":").strip()
        quotes = tuple(q for q in (re.findall(r'"([^"]+)"', rest) or [rest]) if q.strip())
        entries.append(Entry(int(n.group("num")), quotes, start, stop))
    return entries


def is_runtime(gate):
    """A list built at runtime: every option is a placeholder."""
    return all(norm(t).startswith(("<", "{")) for _, t in gate.options)


def _names(quote, gate, num):
    return any(n == num and norm(t).startswith(norm(quote)) for n, t in gate.options)


def marker_problems(text, name="text"):
    """Every gate option with no entry in its marker, and every entry naming no option."""
    prose = prose_lines(text)
    problems, served = [], {}
    for gate in gates(text):
        m = find_marker(prose, gate.end)
        if m is None:
            problems.append("%s:%d: the gate %r has no %s below it, above the next heading"
                            % (name, gate.line, gate.question[:60], MARKER))
            continue
        served.setdefault(m, []).append(gate)
    for m, group in served.items():
        entries = marker_entries(text, m)
        if not entries:
            problems.append("%s:%d: the marker carries no entry" % (name, m + 1))
            continue
        for gate in group:
            for num, option in gate.options:
                if is_runtime(gate):
                    ok = any(e.num == "each" for e in entries)
                else:
                    ok = any(e.num == num and any(_names(q, gate, num) for q in e.quotes)
                             for e in entries)
                if not ok:
                    problems.append("%s:%d: option %d (%r) of %r has no entry in the marker at "
                                    "line %d" % (name, gate.line, num, option[:50],
                                                 gate.question[:50], m + 1))
        for e in entries:
            if e.num == "each":
                if not any(is_runtime(g) for g in group):
                    problems.append("%s:%d: an 'Each number' entry serves a gate with fixed "
                                    "options; name each option" % (name, e.start + 1))
                continue
            for q in e.quotes:
                if not any(_names(q, g, e.num) for g in group if not is_runtime(g)):
                    problems.append("%s:%d: the entry %d, %r names no option of the gate it "
                                    "serves" % (name, e.start + 1, e.num, q))
    return problems


def skill_files():
    """Every skill file carrying a gate — derived, not listed (INV-246)."""
    return sorted(p for p in SKILLS.rglob("*.md") if gates(p.read_text(encoding="utf-8")))


def without_entry(text, entry):
    """``text`` with one entry's lines removed (a negative control)."""
    lines = text.split("\n")
    return "\n".join(lines[:entry.start] + lines[entry.stop:])


def first_entry(text):
    """The first numbered entry of the first gate's marker in ``text``."""
    prose = prose_lines(text)
    for gate in gates(text):
        m = find_marker(prose, gate.end)
        numbered = [e for e in marker_entries(text, m) if e.num != "each"] if m is not None else []
        if numbered:
            return numbered[0]
    return None


class EveryGateOptionHasAMarkerEntry(unittest.TestCase):
    def test_the_scan_finds_the_gates(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        files = skill_files()
        found = [g for p in files for g in gates(p.read_text(encoding="utf-8"))]
        options = sum(len(g.options) for g in found)
        modules = {p.relative_to(SKILLS).parts[0] for p in files}
        for what, count, floor in (("gates", len(found), MIN_GATES),
                                   ("options", options, MIN_OPTIONS),
                                   ("files", len(files), MIN_FILES),
                                   ("skill directories", len(modules), MIN_MODULES)):
            with self.subTest(what=what):
                self.assertGreaterEqual(
                    count, floor, "the scan found %d %s, below its floor of %d: the parser broke "
                    "or the gates moved" % (count, what, floor))

    def test_every_option_has_an_entry(self):
        bad = []
        for path in skill_files():
            bad += marker_problems(path.read_text(encoding="utf-8"),
                                   str(path.relative_to(SKILLS)))
        self.assertEqual(
            [], bad,
            "a pinned gate offers an option no handler marker names, so nothing says what the "
            "guide does when it is chosen or where the flow resumes (INV-284):\n  "
            + "\n  ".join(bad))

    def test_every_numbered_reply_question_is_a_gate(self):
        """#620: the scan sees every `Reply with (a|one or more) number` question."""
        missed, count = [], 0
        for path in sorted(SKILLS.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            count += sum(1 for line in prose_lines(text)
                         if line is not None and QUESTION in line and REPLY.search(norm(line)))
            missed += reply_questions_missed(text, str(path.relative_to(SKILLS)))
        self.assertGreaterEqual(count, MIN_REPLIES, "the reply scan found %d questions" % count)
        self.assertEqual([], missed, "a numbered-reply question the gate scan does not see")


class TheGuardBites(unittest.TestCase):
    """Negative controls on the shipped text, and must-not-flag fixtures."""

    def test_removing_an_entry_fails_in_every_module(self):
        """One control per skill directory, derived from the scan rather than listed."""
        by_module = {}
        for path in skill_files():
            by_module.setdefault(path.relative_to(SKILLS).parts[0], []).append(path)
        self.assertGreaterEqual(len(by_module), MIN_MODULES)
        for module, paths in sorted(by_module.items()):
            with self.subTest(module=module):
                # The module's first file with a fixed-option gate: a runtime list's one
                # "Each number" entry is not a numbered entry to remove (#620).
                texts = [p.read_text(encoding="utf-8") for p in paths]
                text = next((x for x in texts if first_entry(x)), texts[0])
                entry = first_entry(text)
                self.assertIsNotNone(entry, "no numbered entry to remove in %s" % module)
                self.assertEqual([], marker_problems(text))
                self.assertNotEqual([], marker_problems(without_entry(text, entry)))

    def test_removing_phase_d_iterate_now_fails(self):
        """Module 6 Phase D's iterate-vs-proceed gate: #526's site."""
        text = (SKILLS / "module-06-data-processing" / "phaseD-validation.md").read_text(
            encoding="utf-8")
        gate = next(g for g in gates(text) if "most tests pass" in g.question)
        entry = next(e for e in marker_entries(text, find_marker(prose_lines(text), gate.end))
                     if e.num == 1)
        self.assertIn('"Iterate now"', text.split("\n")[entry.start])
        problems = marker_problems(without_entry(text, entry))
        self.assertTrue(any("option 1" in p and "iterate now" in p.lower() for p in problems),
                        problems)

    def test_removing_a_whole_marker_fails(self):
        text = (SKILLS / "module-06-data-processing" / "phaseD-validation.md").read_text(
            encoding="utf-8")
        mutant = text.replace(MARKER, "**Handling.**", 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertNotEqual([], marker_problems(mutant))

    def test_a_reworded_option_fails(self):
        """The entry names the option by its opening words, so a renumber or rename is caught."""
        text = (SKILLS / "module-06-data-processing" / "phaseD-validation.md").read_text(
            encoding="utf-8")
        mutant = text.replace("2. Move forward to the next module.",
                              "2. Revisit the mapping first.", 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertNotEqual([], marker_problems(mutant))

    def test_a_stale_entry_fails(self):
        text = (SKILLS / "module-03-system-verification" / "phase2-report-close.md").read_text(
            encoding="utf-8")
        old = '   - **2, "Move on":**'
        mutant = text.replace(old, '   - **3, "Skip the report":** nothing.\n' + old, 1)
        self.assertNotEqual(text, mutant, "the mutation no longer applies")
        self.assertNotEqual([], marker_problems(mutant))

    def test_a_borrowed_marker_fails(self):
        """A band whose own marker is gone may not pass on its neighbor's entries."""
        text = (MODULE / "phase2-data-mapping.md").read_text(encoding="utf-8")
        start = text.index("**While one or more unmapped sources remain**")
        at = text.index(MARKER, start)
        mutant = text[:at] + "**Handling.**" + text[at + len(MARKER):]
        self.assertNotEqual([], marker_problems(mutant))

    def test_a_new_gate_with_no_marker_fails(self):
        fixture = ("👉 **Which one? Reply with a number:**\n\n1. This one.\n2. That one.\n\n"
                   "Then carry on.\n")
        self.assertEqual(1, len(gates(fixture)))
        self.assertNotEqual([], marker_problems(fixture))

    def test_a_reply_question_with_no_list_is_a_gate(self):
        """#620: options built in prose leave no list beneath; the question still needs a marker."""
        fixture = "👉 **Which one? Reply with a number:**\n\nThe options come from the server.\n"
        self.assertEqual(1, len(gates(fixture)))
        self.assertEqual([], reply_questions_missed(fixture))
        self.assertNotEqual([], marker_problems(fixture))
        self.assertEqual([], marker_problems(fixture + "\n" + MARKER + "\n\n- **Each number:** go.\n"))

    def test_removing_a_runtime_gates_marker_fails(self):
        """#620's two gates, each with its marker gone, as they shipped before #620."""
        for path, question in (
                (SKILLS / "bootcamp-preparation" / "SKILL.md", "which programming language"),
                (SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md",
                 "what does that tell you about entity")):
            with self.subTest(file=path.name):
                text = path.read_text(encoding="utf-8")
                gate = next(g for g in gates(text) if question in g.question)
                m = find_marker(prose_lines(text), gate.end)
                self.assertIsNotNone(m, "the gate has no marker")
                lines = text.split("\n")
                lines[m] = lines[m].replace(MARKER, "**Handling.**")
                problems = marker_problems("\n".join(lines))
                self.assertTrue(any(question in p for p in problems), problems)

    def test_each_number_on_a_fixed_gate_fails(self):
        fixture = ("👉 **Which one? Reply with a number:**\n\n1. This one.\n2. That one.\n\n"
                   + MARKER + "\n\n- **Each number:** carry on.\n")
        self.assertNotEqual([], marker_problems(fixture))

    def test_a_complete_marker_passes(self):
        """Must-not-flag (INV-282): the documented shape, one entry per option."""
        fixture = ("> 👉 **Which one? Reply with a number:**\n>\n> 1. **This one** — first.\n"
                   "> 2. That one, which wraps\n>    onto a second line.\n\n" + MARKER + "\n\n"
                   '- **1, "This one":** step 2.\n- **2, that one** → step 3.\n')
        self.assertEqual([], marker_problems(fixture))

    def test_runtime_lists_take_one_each_number_entry(self):
        fixture = ("👉 **Which sources? Reply with one or more numbers:**\n\n1. `<DATA_SOURCE>`\n"
                   "2. `<DATA_SOURCE>`\n\n" + MARKER + "\n\n- **Each number:** that source.\n")
        self.assertEqual([], marker_problems(fixture))

    def test_what_is_not_a_gate(self):
        """Must-not-flag: a 👉 in prose, a fenced example, and a yes/no question."""
        for fixture in ("Re-present the pending 👉 question on the next turn.\n\n1. Do this.\n",
                        "```text\n👉 **Which one? Reply with a number:**\n\n1. This one.\n```\n",
                        "👉 **Shall we go on?** (respond yes or no)\n\n- **Yes:** go on.\n"):
            with self.subTest(fixture=fixture[:30]):
                self.assertEqual([], gates(fixture))

    def test_a_rewrap_still_passes(self):
        """INV-346: the question, an option and an entry label may each wrap."""
        mutant = (MODULE / "phase2-data-mapping.md").read_text(encoding="utf-8")
        for old, new in (
                ("Ready to map the next source, {next}? Reply with a number:**",
                 "Ready to map the next source,\n  {next}? Reply with a number:**"),
                ('- **2, "No, I\'d like to iterate on {source} first" or',
                 '- **2, "No, I\'d like to iterate on {source} first"\n  or'),
                ("   2. **Try the mapping workflow once more** — it may",
                 "   2. **Try the mapping workflow once more** —\n      it may")):
            with self.subTest(wrap=old[:40]):
                self.assertIn(old, mutant, "the re-wrap no longer applies")
                mutant = mutant.replace(old, new, 1)
        self.assertEqual([], marker_problems(mutant))


M1_DISCOVERY = SKILLS / "module-01-business-problem" / "phase1-discovery.md"
M1_CONFIRM = SKILLS / "module-01-business-problem" / "phase2-document-confirm.md"
M4 = SKILLS / "module-04-data-collection" / "SKILL.md"
M7_PHASE1 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"

#: #620's answer pins: (what, file, section start, section end, must state, must not state).
#: Phrases are matched on normalized text, so they may wrap (INV-346).
ANSWER_PINS = (
    ("8a sub-step 6 gives the chosen path only", M4, "6. **Obtain a Senzing License Key",
     "### 6a.", ("guidance for the chosen path only", "never re-offer the paths",
                 "option 4 goes to sub-step 6a", "sub-step 5 whenever it arrives"),
     ("individually selectable",)),
    ("8a option 4 goes to sub-step 6a only", M4,
     '- **4, "No — request a free evaluation license now":**', "\n", ("sub-step 6a.",),
     ("sub-step 6's",)),
    ("8b's load-all branch asks nothing more", M4, "- **Load all collected records on SQLite:**",
     "- **Sample down", ("the choice is the confirmation, so ask nothing more",),
     ("explicit confirmation",)),
    ("6a's no branch revises and re-presents", M1_DISCOVERY, "### 6a. Present summary and confirm",
     "### 6b", ("on a no, ask what to change, revise the summary, and present this question again",
                "not an inv-006 repeat"), ()),
    ("Step 15's no branch revises and re-presents", M1_CONFIRM, "## 15. Get confirmation",
     "## 16.", ("on a no, ask what to change, revise docs/business_problem.md",
                "present this question again", "not an inv-006 repeat"), ()),
    ("Step 4 option 2 shows the gallery when none was picked", M1_DISCOVERY,
     '- **2, "Adopt a design pattern":**', '- **3, "',
     ("when none was picked, show step 3's pattern gallery first",), ()),
    ("4a carries no unreachable Declined branch", M1_DISCOVERY, "### 4a.", "### 4b.", (),
     ("declined: continue",)),
    ("Module 7 gate item 6 is handled", M7_PHASE1, "6. **Ready to proceed?**",
     "## Visualization server teardown",
     ("on a yes, continue to the visualization server teardown",
      "returns to the discover phase", "not an inv-006 repeat"), ()),
)


def _between(text, start, end):
    i = text.find(start)
    if i < 0:
        return None
    j = text.find(end, i + len(start))
    return text[i:j if j > 0 else len(text)]


def answer_pin_problems(texts):
    """Each #620 pin, read from ``texts`` ({path: text}); a problem names its pin."""
    problems = []
    for what, path, start, end, must, must_not in ANSWER_PINS:
        part = _between(texts[path], start, end)
        if part is None:
            problems.append("%s: the section moved" % what)
            continue
        flat = norm(part)
        problems += ["%s: does not state %r" % (what, s) for s in must if s not in flat]
        problems += ["%s: still states %r" % (what, s) for s in must_not if s in flat]
    return problems


#: Negative controls: each puts back the text that shipped before #620 (new, old).
BEFORE_620 = {
    "8a sub-step 6 gives the chosen path only": (M4, (
        "Give guidance for\n   the chosen path only: the gate already chose, so never re-offer the "
        "paths (INV-006). **Option\n   4** goes to sub-step 6a. **Option 3:** consult",
        "Present the available paths as distinct,\n   individually selectable options. Consult")),
    "8a option 4 goes to sub-step 6a only": (M4, (
        'evaluation license now":** sub-step 6a.',
        'evaluation license now":** sub-step 6\'s in-flow request, sub-step 6a.')),
    "8b's load-all branch asks nothing more": (M4, (
        "the choice is the confirmation, so ask nothing\n     more (INV-006)",
        "first obtain an **explicit confirmation** that\n     the bootcamper accepts the expected "
        "load time")),
    "6a's no branch revises and re-presents": (M1_DISCOVERY, (
        "**On a no,** ask what to change, revise the summary, and present", "")),
    "Step 15's no branch revises and re-presents": (M1_CONFIRM, (
        "**On a no,** ask what to change, revise\n`docs/business_problem.md`", "")),
    "Step 4 option 2 shows the gallery when none was picked": (M1_DISCOVERY, (
        "When none was picked,\n  show Step 3's pattern gallery first", "")),
    "4a carries no unreachable Declined branch": (M1_DISCOVERY, (
        "- **Generation failed",
        "- **Declined:** continue with their own description (Path 1/2); do not generate a "
        "scenario.\n- **Generation failed")),
    "Module 7 gate item 6 is handled": (M7_PHASE1, (
        "6. **Ready to proceed?** On a yes,", "6. **Ready to proceed?**\n\nOn a")),
}


class Issue620AnswersAreCarriedOut(unittest.TestCase):
    """#620: no pinned answer is re-asked, and each confirmation gate has a no branch."""

    def setUp(self):
        self.texts = {p: p.read_text(encoding="utf-8")
                      for p in (M1_DISCOVERY, M1_CONFIRM, M4, M7_PHASE1)}

    def test_each_answer_is_carried_out(self):
        self.assertEqual([], answer_pin_problems(self.texts))

    def test_the_text_before_620_fails_each_pin(self):
        self.assertEqual({w for w, *_ in ANSWER_PINS}, set(BEFORE_620))
        for what, (path, (new, old)) in BEFORE_620.items():
            with self.subTest(pin=what):
                self.assertEqual(1, self.texts[path].count(new), "the mutation no longer applies")
                mutant = {**self.texts, path: self.texts[path].replace(new, old, 1)}
                problems = answer_pin_problems(mutant)
                self.assertTrue(any(p.startswith(what + ":") for p in problems), problems)


class TheImprovePathIsUsable(unittest.TestCase):
    """The three properties the improve path has to have to be executable at all."""

    def setUp(self):
        self.text = (MODULE / "phase1-quality-assessment.md").read_text(encoding="utf-8")
        start = self.text.index("### 7a.")
        end = self.text.index("**Success indicator:**", start)
        #: The improve path alone. Scoped, because the fields below appear elsewhere in the
        #: module and a whole-file search would pass on a neighbor's mention of them.
        self.improve_path = self.text[start:end]

    def test_it_separates_what_can_be_fixed_from_what_cannot(self):
        """A missing value cannot be invented, and offering to fill one invites fabrication."""
        self.assertRegex(self.text, r"cannot be invented",
                         "the improve path does not say that missing values cannot be "
                         "invented, so 'improve completeness' reads as an instruction to "
                         "fabricate data")
        self.assertIn("format_consistency", self.text)
        self.assertIn("duplicate_rate", self.text)

    def test_it_re_scores_and_re_presents_the_gate(self):
        self.assertRegex(self.text, r"[Rr]e-score",
                         "the improve path never re-scores, so nothing tells the "
                         "Bootcamper whether the work helped")
        self.assertRegex(
            self.text, r"NOT an INV-006 repeat",
            "the file does not sanction re-presenting the gate after a re-score, so a "
            "guide honoring INV-006 suppresses it and the improve path dead-ends one step "
            "later than before")

    def test_it_never_overwrites_the_collected_file(self):
        self.assertRegex(self.text, r"never overwrite|NEW file",
                         "the improve path does not protect the file as collected")

    def test_a_synthesized_source_is_disclosed_before_the_question(self):
        """⛔ Criterion 2 — the disclosure has to PRECEDE the 👉, or it cannot inform it."""
        self.assertIn("provenance: synthesized", self.text)
        self.assertIn("INV-239", self.text)
        disclosure = self.text.index("those gaps are deliberate")
        question = self.text.index(
            "👉 **Your data quality is acceptable but has some gaps.")
        self.assertLess(
            disclosure, question,
            "the synthesized-source disclosure comes after the gate question it exists to "
            "inform; anything meant to inform an answer goes before the question")

    def test_it_updates_every_registry_field_the_new_file_changes(self):
        """⛔ INV-243 — the entry is a set of claims about the file it points at.

        The first version of this step repointed `file_path` and stopped there. Resolving
        duplicates removes records, and Module 6 Phase B compares its loaded count against
        the `record_count` written here — so a stale figure reports a CORRECT load as short
        by exactly the number of duplicates this step just removed, one module downstream
        of the cause. Repointing the file without re-measuring it is what makes the entry
        wrong; the fetch-provenance fields are the opposite case, below.
        """
        # ⛔ Matched as an UPDATE BULLET, not as a token anywhere in the section. A first
        # version asserted the bare substring and **passed the mutation**: deleting the
        # whole `record_count` bullet left the word standing in the ⛔ prose that explains
        # why it matters, so the guard certified the field was updated while the
        # instruction to update it was gone. An assertion a neighbor can satisfy is not an
        # assertion about the claim (INV-282).
        for field in ("file_path", "record_count", "file_size_bytes", "quality_score",
                      "updated_at"):
            with self.subTest(field=field):
                self.assertRegex(
                    self.improve_path, r"(?m)^\s*-\s+\*\*`" + re.escape(field) + r"`\*\*\s*→",
                    f"the improve path repoints the registry without an update bullet for "
                    f"`{field}`, so that field goes on describing the file it replaced")
        self.assertIn("INV-243", self.improve_path,
                      "the rule that makes record_count load-bearing is not nameable at the "
                      "step that changes it (INV-183)")

    def test_it_leaves_the_fetch_provenance_fields_with_the_original(self):
        """The mirror: a derived file must not be described as fetched and count-verified."""
        for field in ("expected_record_count", "validation_status", "validation_checks"):
            with self.subTest(field=field):
                self.assertIn(
                    field, self.improve_path,
                    f"the improve path says nothing about `{field}`, so a reader must guess "
                    "whether a derived file inherits a fetch's checks")
        self.assertRegex(
            self.improve_path, r"ORIGINAL fetch|original fetch",
            "the improve path does not say those fields keep describing the original fetch, "
            "which is the only thing stopping them being re-pointed at a file nobody fetched")

    def test_it_names_registry_fields_that_actually_exist(self):
        """⛔ A field name the schema does not have sends an editor to invent one.

        The first version said *"point that source's `path`"*. The registry's field is
        `file_path` (`module-04-data-collection/SKILL.md`'s entry contract), and no entry
        has ever had a `path` key.
        """
        self.assertNotRegex(
            self.improve_path, r"source's `path`",
            "the improve path names a registry field that does not exist; the schema's field "
            "is `file_path`")

    def test_it_forbids_silent_regeneration(self):
        self.assertRegex(self.text, r"[Nn]ever\s+\*\*silently\s+regenerate|silently regenerate",
                         "nothing forbids answering the question by rewriting the "
                         "Bootcamper's data without telling them")


PHASE2 = MODULE / "phase2-data-mapping.md"
PHASE1 = MODULE / "phase1-quality-assessment.md"
ANCHOR = '<a id="synthesized-source-disclosure"></a>'
#: The band marker that carries the pointer to the rule paragraph into each gated band.
BAND_MARKER = "*(on a synthesized source, the disclosure above first)*:"
#: The rule paragraph's opening and its pointer, matched on whitespace-collapsed text (INV-346).
STEP16_RULE = ("⛔ **(INV-345) On a `provenance: synthesized` source, the 70-79% and <70% questions "
               "are disclosed first.**")
STEP16_POINTER = ("its wording is stated once, at Phase 1's [synthesized-source disclosure]"
                  "(phase1-quality-assessment.md#synthesized-source-disclosure); say it as written "
                  "there rather than a copy here (INV-300)")
#: Step 16's gated questions (#333), which stay verbatim (INV-056), each with its options.
GATED = (
    ("👉 **Quality for {source} is acceptable. What would you like to do? Reply with a number:**",
     ("1. Move on to the next source, {next}.",
      "2. Iterate to improve [specific weak areas] first.")),
    ("👉 **Quality for {source} needs improvement before loading will produce meaningful results. "
     "I'd recommend going back to address [specific issues]. What would you like to do? Reply with "
     "a number:**",
     ("1. Iterate to improve the data.",
      "2. Move on to {next} anyway, knowing results may be limited.")),
    ("👉 **Quality is acceptable. What would you like to do? Reply with a number:**",
     ("1. Proceed to loading now.", "2. Iterate to improve [specific weak areas] first.")),
    ("👉 **Quality needs improvement before loading will produce meaningful results. I'd recommend "
     "going back to address [specific issues]. What would you like to do? Reply with a number:**",
     ("1. Iterate to improve the data.", "2. Proceed anyway, knowing results may be limited.")),
)
UNGATED = (
    "👉 **Quality looks strong for {source}. Ready to map the next source, {next}? Reply with a "
    "number:**",
    "👉 **Quality looks strong. Ready to proceed to loading (Data processing)? Reply with a number:**",
)


def _flat(text):
    return re.sub(r"\s+", " ", text)


def step16_disclosure_problems(phase2, phase1):
    """Step 16 discloses before every 70-79% and <70% question, by pointing at Phase 1 (#521)."""
    start = phase2.find("### 16. Review")
    end = phase2.find("### 17. Iterate", start)
    if start < 0 or end < 0:
        return ["step 16 moved"]
    s16 = phase2[start:end]
    flat = _flat(s16)
    problems = []
    if ANCHOR not in phase1:
        return ["Phase 1 has no synthesized-source-disclosure anchor"]
    if not phase1.index(ANCHOR) < phase1.index("those gaps are deliberate"):
        problems.append("Phase 1's anchor does not sit on the disclosure")
    for needle, what in ((STEP16_RULE, "the INV-345 rule"),
                         (STEP16_POINTER, "the pointer to Phase 1's one statement (INV-300)"),
                         ("Then ask the band's pinned question unchanged, with both options live "
                          "(INV-056)", "the question unchanged with both options live"),
                         ("Say it even when the Bootcamper heard it at Phase 1's gate",
                          "that it is said again after Phase 1's gate"),
                         ("The ≥80% band gets no disclosure", "that the ≥80% band gets none")):
        if needle not in flat:
            problems.append("step 16 does not state %s" % what)
    if "One thing worth knowing before you choose" in s16:
        problems.append("step 16 copies Phase 1's disclosure wording (INV-300)")
    rule_at = flat.find(STEP16_RULE)
    lines = s16.split("\n")
    for question, options in GATED:
        if s16.count(question) != 1:
            problems.append("a gated question is not kept verbatim once: %s" % question[:50])
            continue
        q_line = next(i for i, line in enumerate(lines) if line.strip() == question)
        band = next((lines[i] for i in range(q_line - 1, -1, -1)
                     if lines[i].startswith("- **Quality")), "")
        if BAND_MARKER not in band:
            problems.append("the band before %r carries no disclosure marker" % question[:50])
        if rule_at < 0 or not rule_at < flat.find(_flat(question)):
            problems.append("the disclosure rule does not precede %r" % question[:50])
        after = s16[s16.index(question) + len(question):].split("👉", 1)[0]
        for option in options:
            if option not in after:
                problems.append("%r lost its option %r" % (question[:40], option))
    for question in UNGATED:
        q_line = next((i for i, line in enumerate(lines) if line.strip() == question), None)
        if q_line is None:
            problems.append("a ≥80%% question moved: %s" % question[:50])
            continue
        band = next((lines[i] for i in range(q_line - 1, -1, -1)
                     if lines[i].startswith("- **Quality")), "")
        if BAND_MARKER in band:
            problems.append("a ≥80%% band carries the disclosure marker")
    if s16.count(BAND_MARKER) != 4:
        problems.append("step 16 carries %d disclosure markers, not 4" % s16.count(BAND_MARKER))
    return problems


def _move_rule_last(phase2):
    """Step 16 with its rule paragraph moved below every question (a negative control)."""
    start = phase2.index("⛔ **(INV-345) On a `provenance: synthesized` source, the 70-79%")
    end = phase2.index("\n\n", start)
    rule = phase2[start:end]
    without = phase2[:start] + phase2[end + 2:]
    closing = "*(Internal: end the turn on the applicable question and wait.)*"
    return without.replace(closing, rule + "\n\n" + closing, 1)


class Step16DisclosesOnASynthesizedSource(unittest.TestCase):
    """#521: INV-345's disclosure also precedes step 16's 70-79% and <70% questions."""

    def setUp(self):
        self.phase2 = PHASE2.read_text(encoding="utf-8")
        self.phase1 = PHASE1.read_text(encoding="utf-8")

    def test_step_16_discloses_before_the_gated_questions(self):
        self.assertEqual([], step16_disclosure_problems(self.phase2, self.phase1))

    def test_the_link_resolves(self):
        self.assertEqual(1, self.phase1.count(ANCHOR))

    def test_negative_controls(self):
        p2, p1 = self.phase2, self.phase1
        first_gated = GATED[0][0]
        mutants = {
            "rule dropped": (p2.replace(STEP16_RULE[:40], "⛔ **(see below) Something else", 1), p1),
            "pointer dropped": (p2.replace("(phase1-quality-assessment.md#synthesized-source-"
                                           "disclosure)", "", 1), p1),
            "wording copied": (p2.replace("**While one or more unmapped sources remain**",
                                          '> "One thing worth knowing before you choose."\n\n'
                                          "**While one or more unmapped sources remain**", 1), p1),
            "a band loses its marker": (p2.replace("- **Quality 70-79%** " + BAND_MARKER,
                                                   "- **Quality 70-79%:**", 1), p1),
            "≥80% band marked": (p2.replace("- **Quality ≥80% and all critical fields mapped:**",
                                            "- **Quality ≥80% and all critical fields mapped** "
                                            + BAND_MARKER, 1), p1),
            "question reworded": (p2.replace(first_gated, first_gated.replace("acceptable",
                                                                              "fine"), 1), p1),
            "anchor dropped": (p2, p1.replace(ANCHOR, "", 1)),
            "rule moved after the questions": (_move_rule_last(p2), p1),
        }
        for name, (m2, m1) in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual((p2, p1), (m2, m1), "the mutation no longer applies")
                self.assertNotEqual([], step16_disclosure_problems(m2, m1))

    def test_a_rewrap_still_passes(self):
        """INV-346: the rule paragraph's phrase checks read whitespace-collapsed text."""
        m2 = self.phase2.replace("say it\nas written there", "say it as\nwritten there", 1)
        self.assertNotEqual(self.phase2, m2, "the re-wrap no longer applies")
        self.assertEqual([], step16_disclosure_problems(m2, self.phase1))


MODULE_04 = SKILLS / "module-04-data-collection" / "SKILL.md"
#: Module 4 Step 2's provision question, normalized as `gates` reports it.
PROVISION = "how would you like to provide the data for this source?"
#: The generation block's bold label in Step 2's marker check, which the entries point at.
GENERATION_LABEL = "**`provenance: synthesized`** → **generate the source files.**"
SECONDARY_LEAD = "**If the bootcamper declines CORD data**"
CORD_QUOTE = '"Senzing provides **CORD'
#: The catalog is named, not linked, in the entry: the offer above is the recommendation site
#: (`tests/test_free_data_catalog_caveats.py` counts the sites by URL).
FREE_DATA = "senzing-bootcamp-free-data"
_OFFER = re.compile(r"^[ \t]*>[ \t]*-[ \t]+\*\*(?P<name>[^*]+?):\*\*")
_SECONDARY = re.compile(r'^Secondary offer,\s*"(?P<name>[^"]+)"\s*:?$')
#: What each answer's entry must say, and must not (#619). Option 5 writes the registry entry
#: from the business problem, then points at the generation block; the secondary offer's
#: synthesized entry points at option 5's entry and restates none of it (INV-300, a graft from
#: the race's approach B); the free-data entry fetches, counts and records its provenance.
GENERATES = ("docs/business_problem.md", "provenance: synthesized", "quality_intent",
             norm(GENERATION_LABEL))
NEVER_CORD = ("get_sample_data", "if the bootcamper chose option 5", "👉")
#: The synthesized entry's pointer at option 5's entry, by that entry's bold label.
TO_OPTION_5 = ("take option 5's entry", '5, "i don\'t have my own data"', "ask nothing more")
SECONDARY_NEEDS = {
    "synthesized test data": TO_OPTION_5,
    "free raw data": (FREE_DATA, "count its records", "data source registry", "inv-243",
                      "provenance: free_data"),
}


def secondary_options(text):
    """The secondary offer's entries, read from its quote (derived, not listed: INV-246)."""
    start = text.find(SECONDARY_LEAD)
    if start < 0:
        return []
    names = []
    for line in text[start:].split("\n")[1:]:
        if line.strip() and not line.lstrip().startswith((">", "(")):
            break
        m = _OFFER.match(line)
        if m:
            names.append(norm(m.group("name")))
    return names


def provision_path_problems(text):
    """Module 4 Step 2's provision path: every answer carries out what it says (#619)."""
    flat = norm(text)
    gate = next((g for g in gates(text) if PROVISION in g.question), None)
    if gate is None:
        return ["Module 4 Step 2's provision question moved"]
    if not any(n == 5 and norm(o).startswith("i don't have my own data") for n, o in gate.options):
        return ["the provision question has no option 5, \"I don't have my own data\""]
    prose = prose_lines(text)
    m = find_marker(prose, gate.end)
    if m is None:
        return ["the provision question has no %s" % MARKER]
    bodies, secondary = {}, {}
    for start, stop in marker_bullets(text, m):
        body = norm(" ".join((prose[n] or "").strip() for n in range(start, stop)))
        label = _LABEL.match(re.sub(r"^-\s+", "", " ".join(
            (prose[n] or "").strip() for n in range(start, stop))))
        if not label:
            continue
        n = _NUMBERED.match(label.group("label").strip())
        s = _SECONDARY.match(label.group("label").strip())
        if n:
            bodies[int(n.group("num"))] = body
        elif s:
            secondary[norm(s.group("name"))] = body
    problems = []
    if text.count("- " + GENERATION_LABEL) != 1:
        problems.append("Step 2 has no single generation branch labeled %s for the entries to "
                        "point at" % GENERATION_LABEL)
    five = bodies.get(5, "")
    for needle in GENERATES + ("license limit and dataset size (canonical framing)",
                               "recommend no cord alternative"):
        if needle not in five:
            problems.append("option 5's entry does not say %r" % needle)
    for needle in NEVER_CORD:
        if needle in five:
            problems.append("option 5's entry still routes to CORD or asks again (%r)" % needle)
    if GENERATES[0] in five and GENERATES[-1] in five and not (
            five.index(GENERATES[0]) < five.index(GENERATES[-1])):
        problems.append("option 5's entry generates before it writes the registry entry")
    offered = secondary_options(text)
    if len(offered) < 2:
        problems.append("the secondary offer lists %d entries; the parser broke" % len(offered))
    for name in offered:
        body = secondary.get(name)
        if body is None:
            problems.append("the secondary offer's %r has no entry under the marker" % name)
            continue
        for needle in SECONDARY_NEEDS.get(name, ()):
            if needle not in body:
                problems.append("the secondary offer's %r entry does not say %r" % (name, needle))
        if name != "synthesized test data":
            continue
        for needle in NEVER_CORD:
            if needle in body:
                problems.append("the %r entry routes to CORD or asks again (%r)" % (name, needle))
        for needle in GENERATES:
            if needle in body:
                problems.append("the %r entry restates option 5's steps (%r) instead of pointing "
                                "at its entry (INV-300)" % (name, needle))
    for name in secondary:
        if name not in offered:
            problems.append("the entry %r names no entry of the secondary offer" % name)
    q, c = flat.find(PROVISION), flat.find(norm(CORD_QUOTE))
    lead = flat[q:c] if 0 <= q < c else ""
    if "did not choose option 5" not in lead or "if the bootcamper chose option 5" in lead:
        problems.append("the CORD recommendation is not scoped to a Bootcamper who did not "
                        "choose option 5")
    h = flat.find("follow the data recommendation hierarchy")
    if h < 0 or "did not choose option 5" not in flat[max(0, h - 300):h]:
        problems.append("the free-data hierarchy is not scoped to a Bootcamper who did not "
                        "choose option 5")
    if "nor is it a judgment on option 5" not in flat:
        problems.append('"last resort" is not scoped away from option 5')
    return problems


class Module4ProvisionPathCarriesOutEachAnswer(unittest.TestCase):
    """#619: option 5 generates, and the secondary offer's entries each have a procedure."""

    def setUp(self):
        self.text = MODULE_04.read_text(encoding="utf-8")

    def test_every_answer_carries_out_what_it_says(self):
        self.assertEqual([], provision_path_problems(self.text))

    def test_the_secondary_offer_is_read_not_listed(self):
        self.assertEqual(["free raw data", "synthesized test data"],
                         secondary_options(self.text))

    def _entry(self, label):
        start = self.text.index(label)
        end = self.text.index("\n- **", start + 1)
        return start, end

    def test_negative_controls(self):
        t = self.text
        s5, e5 = self._entry('- **5, "I don\'t have my own data":**')
        sf, ef = self._entry('- **Secondary offer, "Free raw data":**')
        ss, es = self._entry('- **Secondary offer, "Synthesized test data":**')
        step1 = t.index("  1. **Write the source's registry entry first.**", s5)
        step2 = t.index("  2. **Then run the generation block", s5)
        old_five = ('- **5, "I don\'t have my own data":** the CORD recommendation right after '
                    "the question (**If the\n  bootcamper chose option 5**).\n")
        offer_end = t.index('scenario."', t.index(SECONDARY_LEAD)) + len('scenario."')
        mutants = {
            "option 5 routes to CORD again": t[:s5] + old_five + t[e5 + 1:],
            "option 5 skips the registry entry": t[:step1] + t[step2:],
            "option 5 generates first": (t[:step1] + t[step2:e5] + "\n" + t[step1:step2]
                                         .rstrip("\n") + t[e5:]),
            "option 5 asks again": t.replace(
                "for one who did not choose a number.",
                "for one who did not choose a number. 👉 **Use CORD instead?**", 1),
            "the free-data entry is gone": t[:sf] + t[ef + 1:],
            "the synthesized entry is gone": t[:ss] + t[es + 1:],
            "the free-data entry records no provenance": t[:sf] + t[sf:ef].replace(
                "`provenance: free_data`", "the provenance") + t[ef:],
            "the synthesized entry restates option 5's steps": t[:ss] + t[ss:es].replace(
                "and carry it out as written;",
                "and carry it out as written: write the source's entry from "
                "`docs/business_problem.md` with `provenance: synthesized` and a "
                "`quality_intent`, then run the generation block;", 1) + t[es:],
            "the synthesized entry drops its pointer": t[:ss] + t[ss:es].replace(
                "take option 5's entry above\n  (**5, \"I don't have my own data\"**)",
                "generate the data", 1) + t[es:],
            "a new secondary option with no entry": (
                t[:offer_end - 1] + '\n> - **Paid data:** a vendor sample."' + t[offer_end:]),
            "the generation label is renamed": t.replace(
                "- " + GENERATION_LABEL, "- **`provenance: synthesized`** → **generate files.**",
                1),
            "the CORD recommendation is unscoped": t.replace(
                "**If the bootcamper did not choose option 5, but says",
                "**If the bootcamper chose option 5, or says", 1),
            "the hierarchy is unscoped": t.replace(
                ", and did not choose option 5 at\n  Step 2's provision question", "", 1),
            "last resort reaches option 5": t.replace("Nor is it a judgment on option 5",
                                                      "It also applies to option 5", 1),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(t, mutant, "the mutation no longer applies")
                self.assertNotEqual([], provision_path_problems(mutant))

    def test_a_rewrap_still_passes(self):
        """INV-346: an entry's label and its phrases may wrap."""
        mutant = self.text.replace('- **Secondary offer, "Free raw data":** fetch the file',
                                   '- **Secondary offer, "Free raw data":**\n  fetch the file', 1)
        mutant = mutant.replace("recommend no CORD alternative, ask nothing more",
                                "recommend no CORD\n  alternative, ask nothing more", 1)
        self.assertNotEqual(self.text, mutant, "the re-wrap no longer applies")
        self.assertEqual([], provision_path_problems(mutant))


if __name__ == "__main__":
    unittest.main()
