"""The license record limit must be measured with an engine configuration in force.

``SzProduct.get_license()`` resolves the license from the settings it is handed.
SDK setup's Step 5a runs three steps before Step 8 writes ``CONFIGPATH``, so a
reading taken there cannot reach a license installed at the system config path --
the third of the four tiers in Step 5's own documented check order. On a machine
carrying such a license the early reading returns the built-in default and says
nothing about having missed anything.

That matters because ``license_record_limit`` is the one field the license
apparatus treats as authoritative *because* it was measured. A measured-but-
incomplete value is worse than an absent one: absence triggers Module 4's
re-measure branch, presence suppresses it, and the Bootcamper is then steered
toward sampling against a ceiling that may not exist.

Measured on Senzing SDK 4.4.0 (build 4.4.0.26242), 2026-09-01, on a machine with a
license at /etc/opt/senzing: ``{"PIPELINE": {}}`` returns ``recordLimit: 500``;
the same call with ``CONFIGPATH`` in force returns ``recordLimit: 0`` (no cap).
Which tier wins for a given settings string is engine behavior no MCP route
reports, so it is recorded as observation-only (INV-080/INV-149).

⛔ The site set here is DERIVED BY SCANNING, never hardcoded (INV-246). A guard
that names the files the author already thought of certifies exactly those and is
blind to the one that matters.

⛔ The marker is checked PER WRITE SITE, in the write's own list item or paragraph, never
per file (#385). A file that names the marker where it reads the field passed the old
file-scoped check while both of its writes omitted it. The write detector that finds the
sites is itself tested against known writes and known discussion lines first.

Enforces **INV-295** — a measurement whose result can change once later configuration
exists records WHEN it was taken, and a step branching on it treats a pre-configuration
reading as provisional rather than authoritative.

⚠️ Scoped deliberately: ``platform`` and ``database_type`` are also environment
measurements and need no marker, because neither can move once a later step writes
configuration. Asserting a timestamp on them would teach that the marker means nothing.

⚠️ What this establishes is that the six rules SHIP across four modules. Whether a live
walk actually re-measures at Step 8a is a claim about a turn, and ``dry-run`` phase 3's.

Stdlib only, and nothing under ``plugins/`` is imported (INV-108).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "senzing-bootcamp" / "skills"

FIELD = "license_record_limit"
MARKER = "license_record_limit_measured_at"

#: The field as written in prose: backticked, and closed right after its name, so
#: `license_record_limit_measured_at` is never mistaken for it.
FIELD_SPAN = "`" + FIELD + "`"

#: An *imperative* write verb. Both spellings the corpus uses appear: "Write the measured
#: value into ... as `license_record_limit`" and "Persist it as `license_record_limit`".
#:
#: ⚠️ Only the base form counts, and only in an imperative position (see
#: ``_is_imperative``). "Every step that writes `license_record_limit`", "steps write
#: configuration, so unlike `license_record_limit`" and Module 1's "`license_record_limit`
#: is written ONLY" are discussion: they describe writes and instruct none.
#:
#: ⚠️ "record" is deliberately NOT in this alternation. It is a noun far more often
#: than a verb in this corpus -- Module 1's "compute the total *record count* across
#: the mentioned sources and read `license_record_limit`" matched it and produced a
#: false positive against a file whose whole point is that it must NEVER write the
#: field. The same noun/verb split `conformance.py` draws for its stop-sign scan.
WRITE_VERB = re.compile(r"(?<![\w-])(?:write|persist)\b", re.IGNORECASE)

#: What may precede an imperative verb once trailing whitespace and bold markers are
#: stripped: the start of the unit, a list marker, a clause or sentence boundary, or a
#: coordinating "and" / "then" ("parse `recordLimit`, and write ...").
IMPERATIVE_BEFORE = re.compile(
    r"(?:^|^(?:[-*+]|\d+\.)|[.:;,(\u2014]|\band|\bthen)$", re.IGNORECASE
)

#: The verb and the field must sit in one sentence. Code spans are blanked first, so the
#: dot in `config/bootcamp_progress.json` is not read as a sentence end -- the defect that
#: made the old line regex miss Module 2 Step 8a.
SENTENCE_END = re.compile(r"[.!?;](?=\s|$)")

#: How far after the verb the field may sit, in normalized characters.
WRITE_REACH = 200

LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
HEADING = re.compile(r"^#{1,6} ")
FENCE = re.compile(r"^\s*(?:```|~~~)")


def units(text):
    """Split markdown into its list items and paragraphs, as (first line number, text).

    ⛔ The unit is the enclosing list item or paragraph, never the heading section and
    never the file: Module 4's absent-branch write shares its section with the read at
    the top of that framing, which names the marker, so a coarser unit passes a write
    that omits it. A nested list item is its own unit, and so is a paragraph inside a
    list item. Line breaks inside a unit are collapsed, so a write wrapped across lines
    is seen whole.
    """
    out, cur, start, fenced = [], [], 0, False

    def flush():
        if cur:
            out.append((start, " ".join(" ".join(cur).split())))
            cur.clear()

    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            flush()
            fenced = not fenced
            continue
        if fenced:
            continue
        if not line.strip():
            flush()
            continue
        if HEADING.match(line) or LIST_ITEM.match(line):
            flush()
            start = n
            cur.append(line)
            if HEADING.match(line):
                flush()
            continue
        if not cur:
            start = n
        cur.append(line)
    flush()
    return out


def _is_imperative(unit, at):
    before = unit[:at].rstrip().rstrip("*").rstrip()
    return bool(IMPERATIVE_BEFORE.search(before))


def is_write(unit):
    """True when the unit instructs writing the field, not merely discusses it."""
    for verb in WRITE_VERB.finditer(unit):
        if not _is_imperative(unit, verb.start()):
            continue
        field = unit.find(FIELD_SPAN, verb.end())
        if field == -1 or field - verb.end() > WRITE_REACH:
            continue
        between = re.sub(r"`[^`]*`", "``", unit[verb.end():field])
        if not SENTENCE_END.search(between):
            return True
    return False


def write_sites(text):
    """Every unit of ``text`` that instructs a write of the field."""
    return [(n, u) for n, u in units(text) if is_write(u)]


def sites_missing_the_marker(text):
    """The write sites whose own list item or paragraph never names the marker."""
    return [(n, u) for n, u in write_sites(text) if MARKER not in u]


def unit_containing(text, anchor):
    """The unit holding ``anchor`` (whitespace-normalized), located by content."""
    want = " ".join(anchor.split())
    found = [u for _, u in units(text) if want in u]
    if len(found) != 1:
        raise AssertionError("anchor %r found in %d units, expected 1" % (anchor, len(found)))
    return found[0]


def markdown_files():
    return sorted(p for p in SKILLS.rglob("*.md"))


def sections(text):
    """Split a skill file into (heading, body) pairs on ATX headings."""
    parts = re.split(r"^(#{2,4} .+)$", text, flags=re.M)
    out, i = [], 1
    while i < len(parts) - 1:
        out.append((parts[i].strip(), parts[i + 1]))
        i += 2
    return out


class TheReadingIsMarkedProvisionalUntilTheConfigExists(unittest.TestCase):
    def setUp(self):
        self.sdk_setup = SKILLS / "module-02-sdk-setup" / "SKILL.md"
        self.text = self.sdk_setup.read_text(encoding="utf-8")

    def _prose_of_5a(self):
        """Section 5a with inline-code spans removed.

        ⛔ The marker VALUE this step writes is the string
        ``"module-02 step 5a (provisional -- ...)"``, and it sits in a backticked span
        inside this very section. Asserting on the raw text therefore passes on the
        marker alone, even with the caveat deleted -- which is what the first version
        of this test did, and the M1 mutation proved it. Strip code spans so the
        assertion is about the PROSE that makes the claim.
        """
        body = next(b for h, b in sections(self.text) if h.startswith("### 5a."))
        return re.sub(r"`[^`]*`", "", body)

    def test_step_5a_names_its_reading_provisional(self):
        """The early reading must say it is provisional, not merely be corrected later."""
        self.assertRegex(
            self._prose_of_5a(), r"(?i)provisional",
            "SDK setup Step 5a takes the license reading before Step 8 writes CONFIGPATH, so it "
            "cannot see a license at the system config path. The step's PROSE must say the reading "
            "is provisional; otherwise a downstream reader treats it as complete. (The marker value "
            "this step writes also contains the word, so it is excluded from this assertion.)",
        )

    def test_step_5a_says_a_later_step_re_takes_the_reading(self):
        """'Provisional' with no successor names a problem and no remedy."""
        self.assertRegex(
            self._prose_of_5a(), r"(?i)(re-?take|re-?measure)",
            "Step 5a must say that a later step re-takes the reading. Calling it provisional "
            "without naming the successor tells the reader the figure is untrustworthy and gives "
            "them nowhere to go.",
        )

    def test_step_5a_names_configpath_as_the_reason(self):
        """A bare 'provisional' is unactionable -- the reason is what makes it checkable."""
        body = next(b for h, b in sections(self.text) if h.startswith("### 5a."))
        self.assertIn(
            "CONFIGPATH", body,
            "Step 5a must name CONFIGPATH as what the reading cannot yet see. Without the reason, "
            "a later editor cannot tell whether the caveat still applies.",
        )

    def test_a_re_measure_step_exists_AFTER_the_engine_configuration_is_written(self):
        """Position is the whole fix: re-measuring before Step 8 would change nothing."""
        step8 = self.text.find("## Step 8: Create Engine Configuration")
        self.assertNotEqual(step8, -1, "Step 8 heading not found -- has the module been renamed?")
        remeasure = re.search(r"(?im)^#{2,4} .*re-?measure.*$", self.text)
        self.assertIsNotNone(
            remeasure,
            "No re-measure step found in SDK setup. Step 5a's reading is provisional, so something "
            "after Step 8 must take the authoritative one.",
        )
        self.assertGreater(
            remeasure.start(), step8,
            "The re-measure step is positioned BEFORE Step 8 writes the engine configuration, so it "
            "reads the same incomplete settings Step 5a did and corrects nothing.",
        )

    def test_the_re_measure_step_says_a_withdrawn_figure_is_named_aloud(self):
        """Replacing the number silently leaves anything sized against it unexamined.

        Step 5a's sub-step 3 already requires naming both numbers on a disagreement;
        before the re-measure existed nothing in this module wrote the field twice, so
        that rule described a situation that could not arise. The re-measure is what
        makes it reachable, so it must carry the obligation too.
        """
        remeasure = re.search(r"(?im)^#{2,4} .*re-?measure.*$", self.text)
        body = self.text[remeasure.start():]
        body = body[: body.find("\n## ") if "\n## " in body else len(body)]
        self.assertRegex(
            body, r"(?i)withdraw",
            "The re-measure step must say the superseded figure is withdrawn and both numbers "
            "stated. A silent replacement leaves a sampling plan or generated scenario sized "
            "against a ceiling that has just been shown not to exist.",
        )


M2 = "module-02-sdk-setup/SKILL.md"
M4 = "module-04-data-collection/SKILL.md"
M6A = "module-06-data-processing/phaseA-build-loading.md"
M1 = "module-01-business-problem/phase1-discovery.md"

#: Controls on the DETECTOR, never the set the guard checks (INV-246): the guard scans
#: every skill file, and a sixth write added later is found by the scan, not by this
#: list. Each anchor locates its site by content, because line numbers drift.
KNOWN_WRITES = [
    (M2, "Step 5a sub-step 3", "**Write the measured value into `config/bootcamp_progress.json`**"),
    (M2, "Step 8a.1", "**Write it** to `config/bootcamp_progress.json` as `license_record_limit`"),
    (M4, "absent branch", "**Persist it** as `license_record_limit` in `config/bootcamp_progress.json`"),
    (M4, "Step 8a sub-step 7", "**Detect the active license's record limit"),
    (M6A, "phase A absent branch", "**Persist it** as `license_record_limit` in `config/bootcamp_progress.json`"),
]

#: Lines that name the field next to a write verb and write nothing.
KNOWN_DISCUSSION = [
    (M2, "Step 4's version marker", "so unlike `license_record_limit` its marker records provenance"),
    (M2, "Step 8a.1's reachability note", "in this module writes `license_record_limit` a second time"),
    (M6A, "the absent branch's premise", "**Every step that writes `license_record_limit` writes only a MEASURED value**"),
    (M1, "Step 5a's measured-only rule", "`license_record_limit` is written ONLY from a measured license"),
    (M1, "the built-in-capacity branch", "Every step that writes `license_record_limit` writes only a MEASURED value"),
]

M4_ABSENT_VALUE = '`license_record_limit_measured_at: "module-04 sampling decision (engine configuration in force)"`'
M4_STEP_8A_VALUE = '`license_record_limit_measured_at: "module-04 step 8a (engine configuration in force)"`'


def read(rel):
    return (SKILLS / rel).read_text(encoding="utf-8")


def m4_step_8a_substep_7(text):
    """Module 4 Step 8a sub-step 7, located by its text, ending at the next column-0 paragraph."""
    lines = text.splitlines()
    first = next(
        (i for i, l in enumerate(lines) if re.match(r"^\d+\. \*\*Detect the active license's record limit", l)),
        None,
    )
    if first is None:
        raise AssertionError("Module 4 Step 8a sub-step 7 ('Detect the active license's record limit') not found")
    end = len(lines)
    for i in range(first + 1, len(lines)):
        line = lines[i]
        new_paragraph = line[:1].strip() and not lines[i - 1].strip()
        if HEADING.match(line) or new_paragraph:
            end = i
            break
    return "\n".join(lines[first:end])


def substep_7_problems(text):
    """What Module 4 Step 8a sub-step 7 fails to say about a superseded figure."""
    body = " ".join(m4_step_8a_substep_7(text).split())
    problems = []
    if not re.search(r"(?i)withdraw", body):
        problems.append("does not say the superseded figure is withdrawn")
    if not re.search(r"(?i)both numbers", body):
        problems.append("does not name both numbers")
    if not re.search(r"Step 5a sub-step 3", body):
        problems.append("does not cite Module 2 Step 5a sub-step 3")
    if not re.search(r"(?i)\brais(?:e|es|ing)\b", body):
        problems.append("does not cover a correction that raises the limit")
    return problems


class TheWriteDetectorIsProvenAgainstKnownSites(unittest.TestCase):
    """The detector is what the per-site check stands on, so it is tested first."""

    def test_it_matches_every_known_write(self):
        for rel, where, anchor in KNOWN_WRITES:
            with self.subTest(site="%s %s" % (rel, where)):
                self.assertTrue(
                    is_write(unit_containing(read(rel), anchor)),
                    "The write detector misses %s %s. A write it cannot see is a write the "
                    "per-site check never examines -- the old line regex missed three of the "
                    "five this way (a line break, and the dot in `.json`)." % (rel, where),
                )

    def test_it_does_not_match_discussion(self):
        for rel, where, anchor in KNOWN_DISCUSSION:
            with self.subTest(site="%s %s" % (rel, where)):
                self.assertFalse(
                    is_write(unit_containing(read(rel), anchor)),
                    "The write detector treats %s %s as a write. It describes writes and "
                    "instructs none; requiring the marker there would demand bookkeeping in "
                    "prose about the rule." % (rel, where),
                )

    def test_a_wrapped_write_with_a_dotted_path_is_seen(self):
        """The two shapes the old regex could not see, in one synthetic unit."""
        text = "7. Save it to `config/license.json`, and write\n   `license_record_limit` into it.\n"
        self.assertEqual(1, len(write_sites(text)))

    def test_the_scan_finds_at_least_five_sites_across_three_files(self):
        """Guards the guard: a detector that matches nothing makes the per-site check vacuous."""
        found = {
            str(p.relative_to(SKILLS)): len(write_sites(p.read_text(encoding="utf-8")))
            for p in markdown_files()
        }
        found = {k: v for k, v in found.items() if v}
        self.assertGreaterEqual(
            sum(found.values()), 5,
            "Expected at least the five known write sites; the scan found %r." % found,
        )
        self.assertGreaterEqual(
            len(found), 3,
            "Expected write sites in SDK setup, Data collection and Data processing; the scan "
            "found %r." % found,
        )


class EveryWriteSiteRecordsWhenTheReadingWasTaken(unittest.TestCase):
    """Derived by scanning: each write's own list item or paragraph names the marker."""

    def test_every_write_site_names_the_marker_in_its_own_unit(self):
        offenders = []
        for path in markdown_files():
            for line, unit in sites_missing_the_marker(path.read_text(encoding="utf-8")):
                offenders.append("%s:%d" % (path.relative_to(REPO), line))
        self.assertEqual(
            [], offenders,
            "These list items or paragraphs instruct writing `%s` without naming `%s` beside "
            "it. Both readings are genuine measurements, so the figure alone cannot distinguish "
            "a complete one from a pre-configuration one; the marker is what lets a later step "
            "tell them apart. A mention elsewhere in the file does not count: %s"
            % (FIELD, MARKER, offenders),
        )

    def test_the_check_is_per_site_not_per_file(self):
        """Negative control: strip the marker from Module 4's absent branch only.

        Module 4 still names the marker at the read sites above it, which is exactly how
        the old file-scoped check passed while both of its writes omitted it.
        """
        text = read(M4)
        unit = unit_containing(text, "**Persist it** as `license_record_limit` in `config/bootcamp_progress.json`")
        self.assertIn(MARKER, unit)
        mutated = text.replace(M4_ABSENT_VALUE, "`" + "license_record_limit_note" + "`", 1)
        self.assertNotEqual(text, mutated, "the absent branch's marker value was not found to remove")
        self.assertIn(MARKER, mutated, "control is void: the file must still name the marker elsewhere")
        missing = sites_missing_the_marker(mutated)
        self.assertEqual(1, len(missing), missing)
        self.assertIn("**Persist it** as `license_record_limit`", missing[0][1])

    def test_module_4_writes_its_own_marker_values(self):
        text = read(M4)
        self.assertIn(
            M4_ABSENT_VALUE,
            unit_containing(text, "**Persist it** as `license_record_limit` in `config/bootcamp_progress.json`"),
            "Module 4's absent branch must write its own marker value, naming where it measured.",
        )
        self.assertIn(
            M4_STEP_8A_VALUE,
            unit_containing(text, "**Detect the active license's record limit"),
            "Module 4 Step 8a sub-step 7 must write its own marker value, so Module 6 and "
            "graduation stop reading SDK setup's provisional marker over a complete reading.",
        )


class Module4Step8aNamesASupersededFigureAloud(unittest.TestCase):
    """INV-295: a superseded figure is named aloud when replaced, a raise included."""

    def test_substep_7_says_a_superseded_figure_is_withdrawn(self):
        self.assertEqual(
            [], substep_7_problems(read(M4)),
            "Module 4 Step 8a sub-step 7 re-measures a figure that may already be recorded. A "
            "silent replacement leaves anything sized against the old figure unexamined, so it "
            "must cite SDK setup's Step 5a sub-step 3 rule: withdraw, name both numbers, and say "
            "a raise aloud too.",
        )

    def test_the_withdrawal_check_fails_without_the_wording(self):
        """Negative control: the same check on a copy with "withdraw" removed."""
        text = read(M4)
        body = m4_step_8a_substep_7(text)
        mutated = text.replace(body, re.sub(r"(?i)withdrawn?", "replaced", body), 1)
        self.assertNotEqual(text, mutated)
        self.assertIn("does not say the superseded figure is withdrawn", substep_7_problems(mutated))

    def test_substep_7_ends_before_the_gate_summary(self):
        """The locator must not run on into the text after the sub-step."""
        self.assertNotIn("This gate is non-blocking", m4_step_8a_substep_7(read(M4)))


class TheDownstreamGateDoesNotTrustAProvisionalReading(unittest.TestCase):
    def test_every_file_that_branches_on_the_field_consults_the_marker(self):
        """A consumer that decides capacity must know whether the reading was complete.

        Scanned, not listed. A file only *mentions* the field (cross-references, prose
        about the invariant) without deciding on it; the discriminator is whether it
        instructs reading the value to drive a decision.
        """
        reads = re.compile(r"(?i)read\b[^.\n]{0,120}`" + FIELD + "`")
        offenders = []
        for path in markdown_files():
            text = path.read_text(encoding="utf-8")
            if not reads.search(text):
                continue
            # Module 1 runs before SDK setup, so no measurement can exist yet there;
            # its own text says the field is "normally absent at this point".
            if "normally absent at this point" in text:
                continue
            if MARKER not in text:
                offenders.append(str(path.relative_to(REPO)))
        self.assertEqual(
            [], offenders,
            "These files read `%s` to drive a decision without consulting `%s`. A present figure is "
            "authoritative only if it was taken with an engine configuration in force: %s"
            % (FIELD, MARKER, offenders),
        )


if __name__ == "__main__":
    unittest.main()
