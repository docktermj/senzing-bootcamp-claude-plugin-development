"""A consented-but-forbidden upstream send has its own `Upstream:` value, everywhere.

Two rules, each correct alone, collided on 2026-08-27. **Graduation Step 0** offers to forward
`mcp-server`-routed findings and send on a yes. **`/dry-run`** forbids calling `submit_feedback`
under any category, so a dry run never files into Senzing's real queue. On the first phase-3
walk ever to reach graduation, the maintainer answered "yes" in character and the walk had to
break character to explain the send could not happen.

⚠️ **Reworded 2026-09-26 (#153).** `/dry-run` no longer bans `submit_feedback` outright: its
outbound rule lets the maintainer, out of character, approve sending a certain `mcp-server`
finding. What still blocks the send at graduation is that the *yes* was given in character, so the
disclosure the walk reads out now says a dry run never sends on the Bootcamper's answer, and the
pinned regex below follows it. The collision, and the value it needs, are unchanged.

⛔ **The vocabulary had no value for that outcome.** `feedback.md` Step 3 offered
`not applicable | offered, declined | submitted YYYY-MM-DD | submission failed: reason`, and the
nearest legal value — `offered, declined` — is **false about the one thing the field records**:
the bootcamper agreed. `submission failed:` is wrong too; nothing failed and no retry will
succeed. So `submission blocked: <reason>` was added.

⚠️ **What the harm is, stated accurately.** `feedback-to-issues` Step 1 skips a finding only when
the field says it was already *sent*, so a `declined` entry is not silently dropped from spec
filing — the spec that prompted this fix reasoned it would be, and that part is overstated. The
real cost is narrower and still worth fixing: the field is the record of what happened, and
`offered, declined` records the opposite of what happened, reading as "considered and rejected"
to anyone later deciding whether the report is still owed.

⚠️ What this does NOT establish: that a walk actually records the new value. That is a runtime
property of a phase-3 run (INV-108). It asserts the value exists wherever the vocabulary is
enumerated, so the two enumerations cannot drift.

Enforces **INV-281** — the `Upstream:` outcome vocabulary is a closed set stated identically at every site, and a
consented-but-blocked send carries its own value distinct from a decline.

**`offer pending` (#167).** Graduation Step 0, the bootcamper-driven flow (Step 3 -> 3c) and the
silent in-run append all save an `mcp-server`/`both` entry before its upstream question is
answered, so between the append and the answer no value was correct. A 2026-09-25 walk wrote an
ad-hoc `pending (offer below)`. `offer pending` is that value. It must be listed at every
entry-side enumeration, and `/feedback-to-issues` must read it as still owed, as it does
`submission blocked`.

⚠️ **The issue-side lines are exempt for `offer pending`, and only for it.** An issue
template's `Upstream:` records the ISSUE's field, not the entry's, and there are **two closed
sets**, not one (#223). The maintainer's decision on a pending entry lands in an issue-field
value (`sent <date> via submit_feedback (<category>, anonymous)`, `declined by the maintainer`,
`submission failed: <reason>`), and when no maintainer is asked the issue field has its own
pending value, `not yet sent — needs maintainer approval`. So `offer pending` itself is never
written on an issue (maintainer decision on #167, kept by #223). `submission blocked` is still
required on every line, the issue-side lines included: it is a member of both sets.

⛔ **Two closed sets, one owner, parsed (#223).** `feedback-to-issues/SKILL.md` Step 8.1 is the
canonical statement of both sets and the mapping between them, as two tables. This guard parses
the sets from those tables and holds every other site to them: every enumeration line equals
exactly one side's set, nothing missing and nothing extra; every value written into an
`Upstream:` field in prose is a member of its field's set; and no site still says `/dry-run`
forbids `submit_feedback`. A placeholder (`<reason>`, `<date>`, `YYYY-MM-DD`) matches any text in
its position, so values are compared by stem, not by a filled-in reason.

Source spec: `specs/graduation-upstream-offer-collides-with-the-dry-run-no-send-rule.md`.
Source issues: #167 (`offer pending`), #223 (two closed sets and their mapping).

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugins"
DRY_RUN = REPO_ROOT / ".claude" / "skills" / "dry-run" / "phase3-conversational.md"
#: Maintainer-side skills and commands that state the vocabulary. `.claude/` does not ship, so a
#: corpus of `plugins/` alone is structurally blind to it — which is exactly how the value
#: added on 2026-08-28 reached two of the vocabulary's three sites and not the third.
MAINTAINER_SIDE = REPO_ROOT / ".claude" / "skills"
#: ⛔ The commands tree writes `Upstream:` values too (the unattended loop's overlay), and the
#: guard was blind to it until #223.
COMMANDS = REPO_ROOT / ".claude" / "commands"
#: The canonical statement of both closed sets and their mapping (INV-281, INV-300). Named here
#: because it is the owner the sets are parsed from; every other site is derived by scanning.
OWNER = MAINTAINER_SIDE / "feedback-to-issues" / "SKILL.md"
LOOP_COMMAND = COMMANDS / "unattended-issue-loop.md"
VALUE = "submission blocked"
#: The value for an entry saved before its upstream question was answered (#167).
PENDING = "offer pending"
#: The other values, used to find every place the vocabulary is enumerated.
SIBLINGS = ("offered, declined", "submission failed")
#: The issue-side values that also find an enumeration line. It is a DIFFERENT closed set
#: from the entry side's, not a respelling of it (#223).
SPEC_SIDE_SIBLINGS = ("already sent", "declined by the maintainer")


def shipped_markdown():
    return sorted(p for p in PLUGIN.rglob("*.md") if "__pycache__" not in p.parts)


def vocabulary_corpus():
    """Shipped prose **and** the maintainer-side skills, because this vocabulary spans both.

    ⚠️ Scanning `plugins/` alone is the right default for a rule about shipped prose, and
    it is wrong here: `feedback-to-issues` states the same closed set from the spec side,
    and a guard that cannot see it cannot notice the two halves disagreeing. This is the
    site-set-is-larger-than-the-shipped-tree case of INV-246.
    """
    out = list(shipped_markdown())
    for tree in (MAINTAINER_SIDE, COMMANDS):
        if tree.is_dir():
            out += [p for p in tree.rglob("*.md") if "__pycache__" not in p.parts]
    return sorted(out)


def flatten(text):
    return re.sub(r"\s+", " ", text).lower()


def norm(value):
    """A value as compared: backticks dropped, whitespace collapsed, lower case."""
    return re.sub(r"\s+", " ", value.replace("`", "")).strip().lower()


PLACEHOLDER = r"(<[^>]+>|yyyy-mm-dd)"


def matches(value, member):
    """Does `value` state `member`? A placeholder matches any text in its position.

    A bare stem is accepted too (`submission blocked:`, `submitted`): prose names a value by its
    stem, and the placeholder that ends it carries no information to compare.
    """
    value, member = norm(value), norm(member)
    parts = re.split(PLACEHOLDER, member)
    pattern = "".join(".+" if i % 2 else re.escape(part) for i, part in enumerate(parts))
    stem = re.sub(r"\s*" + PLACEHOLDER + r"\s*$", "", member)
    return bool(re.fullmatch(pattern, value)) or value == stem


def matching(value, members):
    return [m for m in members if matches(value, m)]


def owner_tables():
    """{first header cell: [row cells]} for each table in the owner's Step 8."""
    text = OWNER.read_text(encoding="utf-8")
    step = text[text.index("## Step 8:"):text.index("## Step 9:")]
    tables, rows = {}, []
    for line in step.splitlines() + [""]:
        if line.lstrip().startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        if rows:
            tables[rows[0][0]] = [r for r in rows[2:]]
            rows = []
    return tables


def code_spans(cell):
    return re.findall(r"`([^`]+)`", cell)


def mapping_rows():
    return owner_tables().get("Entry value", [])


def entry_set():
    """The entry field's closed set: the mapping's first column, parsed from the owner."""
    return [v for row in mapping_rows() for v in code_spans(row[0])]


def issue_set():
    """The issue field's closed set: the owner's second table, parsed."""
    return [v for row in owner_tables().get("Issue value", []) for v in code_spans(row[0])]


def pipe_values(line):
    """The values of a ` | `-separated list on this line, or None when there is none.

    The list may open with `[`, `<` or a backtick and close with the matching one; a `<`
    inside a value is a placeholder, so the closing `>` is the first unbalanced one.
    """
    parts = line.split(" | ")
    if len(parts) < 3:
        return None
    first = re.split(r"[\[`<]", parts[0])[-1]
    last, depth = parts[-1], 0
    for i, ch in enumerate(last):
        if ch == "<":
            depth += 1
        elif ch == ">":
            if depth == 0:
                last = last[:i]
                break
            depth -= 1
        elif ch in "]`" and depth == 0:
            last = last[:i]
            break
    return [norm(v) for v in [first] + parts[1:-1] + [last]]


def set_problem(values, members):
    """(missing, extra) of a parsed enumeration against one closed set."""
    missing = [m for m in members if not [v for v in values if matches(v, m)]]
    extra = [v for v in values if len(matching(v, members)) != 1]
    return missing, extra


def enumeration_problems(lines, entry, issue):
    """Every enumeration line that does not equal exactly one side's set, naming its site."""
    out = []
    for p, n, line in lines:
        site = f"{p.relative_to(REPO_ROOT)}:{n}"
        values = pipe_values(line)
        if values is None:
            out.append(f"{site}  enumerates the vocabulary without a closed-set list: "
                       f"{line.strip()[:90]}")
            continue
        results = {side: set_problem(values, members)
                   for side, members in (("entry", entry), ("issue", issue))}
        if any(results[side] == ([], []) for side in results):
            continue
        side = min(results, key=lambda s: len(results[s][0]) + len(results[s][1]))
        missing, extra = results[side]
        out.append(f"{site}  equals neither closed set; nearest is the {side} field, "
                   f"missing {missing}, extra {extra}")
    return out


#: A value written into a field: a code span or a quoted phrase after a writer verb, or the
#: value that fills the label itself (`**Upstream:** not applicable`).
WRITTEN = re.compile(
    r"\b(?:as|record|records|recorded|reading|reads|write|writes|written)\s+"
    r"(?:\*\*)?(?:`([^`]+)`|\*[\"“]([^\"”]+)[\"”]\*)"
    r"|upstream:\*\*\s+([^`]+)`|upstream:`\*\*\s+`([^`]+)`", re.I)
LABEL = re.compile(r"[`*]upstream:[`*]", re.I)
#: Where the unit holding a label ends: a blank line, or the next bullet or numbered item. A
#: sentence is too small: graduation names the value two sentences after the label.
BOUNDARY = re.compile(r"\n\s*\n|\n\s*(?:[-*]|\d+\.)\s")

#: The #153-stale rationale: `/dry-run` said to forbid `submit_feedback` outright.
STALE_DRY_RUN = re.compile(r"/dry-run`?[^.]{0,80}?\bforbid\w*\b[^.]{0,40}?submit_feedback")

def field_of(path, before, after):
    """Which field a label names: the entry's, the issue's, or (unsaid) either."""
    if "plugins" in path.relative_to(REPO_ROOT).parts or "entry's" in before[-12:].lower():
        return "entry"
    if "issue's" in before[-12:].lower() or re.match(r"\s*line\b", after):
        return "issue"
    return "either"


def written_values(docs):
    """[(site, field, value)] for every value written into an `Upstream:` field in prose.

    The paragraph or list item holding the label is the unit: a value sits before its label as
    often as after it (`record X in the entry's Upstream: field`). Table rows and enumeration lines are
    left out; they are checked by the exact-set test.
    """
    out = []
    for path, text in docs:
        lines = text.split("\n")
        kept = "\n".join("" if l.lstrip().startswith("|") or pipe_values(l) is not None
                         else l for l in lines)
        masked = kept
        for label in LABEL.finditer(kept):
            starts = [m.end() for m in BOUNDARY.finditer(masked, 0, label.start())]
            start = starts[-1] if starts else 0
            end_m = BOUNDARY.search(masked, label.end())
            end = end_m.start() if end_m else len(kept)
            field = field_of(path, kept[:label.start()], kept[label.end():])
            for w in WRITTEN.finditer(kept, start, end):
                value = next(g for g in w.groups() if g is not None)
                if "upstream" in value.lower() or pipe_values(value):
                    continue
                n = kept.count("\n", 0, w.start()) + 1
                out.append((f"{path.relative_to(REPO_ROOT)}:{n}", field, norm(value)))
    return sorted(set(out))


def written_value_problems(values, entry, issue):
    sets = {"entry": entry, "issue": issue, "either": entry + issue}
    return [f"{site}  writes `{value}`, which is not a member of the {field} field's set"
            for site, field, value in values if not matching(value, sets[field])]


def corpus_docs():
    return [(p, p.read_text(encoding="utf-8")) for p in vocabulary_corpus()]


def enumeration_lines():
    """Every LINE in shipped markdown that lists the `Upstream:` outcome vocabulary.

    Derived by looking for the sibling values rather than by naming files (INV-246): the
    spec predicted two sites, and a hardcoded pair cannot notice a third appearing.

    ⛔ **Line-level, not file-level, and that distinction is load-bearing.** A file-level
    version of this passed its own negative control: removing the value from the entry
    template still left it elsewhere in the same file, so the drift the guard exists to
    catch was invisible to it. The vocabulary drifts one enumeration at a time.

    ⚠️ **Two finders, either one enough (#223).** A line with both siblings of either side, as
    before; or a pipe list with at least two values from either closed set. The second finds a
    line the siblings miss: the delegate template carried neither pair, so the guard never saw
    it. A table row is skipped: the owner's tables are parsed, not scanned.
    """
    members = entry_set() + issue_set()
    out = []
    for p in vocabulary_corpus():
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("|"):
                continue
            low = line.lower()
            values = pipe_values(line) or []
            if (all(s in low for s in SIBLINGS) or all(s in low for s in SPEC_SIDE_SIBLINGS)
                    or sum(1 for v in values if matching(v, members)) >= 2):
                out.append((p, i, line))
    return out


class TheVocabularyCarriesABlockedValue(unittest.TestCase):
    def test_the_enumerations_are_found(self):
        """⛔ INV-265 — a scan that matches nothing certifies nothing."""
        self.assertTrue(
            enumeration_lines(),
            "no shipped line enumerates the `Upstream:` outcome vocabulary any more; the scan "
            "broke or the vocabulary moved. Re-derive SIBLINGS rather than deleting this guard")

    def test_every_enumeration_includes_the_blocked_value(self):
        missing = [f"{p.relative_to(REPO_ROOT)}:{n}  {line.strip()[:90]}"
                   for p, n, line in enumeration_lines() if VALUE not in line.lower()]
        self.assertEqual(
            [], missing,
            f"an `Upstream:` vocabulary enumeration omits `{VALUE}:`, so the copies have "
            "drifted and a consented-but-forbidden send has no legal value there:\n  "
            + "\n  ".join(missing))

    def test_both_trees_state_the_value(self):
        """⛔ The finding this widening exists for: present in one tree, absent in the other.

        On 2026-08-28 the value reached `plugins/`'s two enumerations and not
        `feedback-to-issues`'s, and the guard could not see it because its corpus stopped at
        the shipped tree. A count per tree is what makes that visible.
        """
        trees = {"plugins": 0, ".claude": 0}
        for path, _, line in enumeration_lines():
            if VALUE in line.lower():
                key = "plugins" if "plugins" in path.parts else ".claude"
                trees[key] += 1
        for tree, n in trees.items():
            with self.subTest(tree=tree):
                self.assertGreater(
                    n, 0,
                    f"no enumeration under {tree}/ states `{VALUE}:`. The vocabulary spans "
                    "both trees, so a value in one and not the other is the drift this "
                    "guard exists to catch")

    def test_the_spec_side_says_the_report_is_still_owed(self):
        """`submission blocked` is an outcome that does NOT end the obligation."""
        skill = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md"
        flat = flatten(skill.read_text(encoding="utf-8"))
        self.assertIn(VALUE, flat,
                      "feedback-to-issues Step 1 never mentions the blocked value, so it "
                      "triages a consented-but-unsent finding as though it were declined")
        self.assertIn("still owed", flat,
                      "Step 1 does not say a blocked entry still owes a report — the whole "
                      "reason the value is distinct from a decline")

    def test_graduation_points_at_the_blocked_value(self):
        """Step 0 is where the collision fires, so the rule must be reachable there (INV-183)."""
        grad = PLUGIN / "senzing-bootcamp" / "skills" / "graduation" / "SKILL.md"
        flat = flatten(grad.read_text(encoding="utf-8"))
        self.assertIn(VALUE, flat,
                      "graduation Step 0 offers the forward but never names the value to record "
                      "when the session is forbidden to send")
        self.assertIn("never", flat[flat.index(VALUE):flat.index(VALUE) + 400],
                      "graduation names the blocked value without ruling out `offered, declined`, "
                      "which is the wrong value a runner would otherwise reach for")

    def test_the_blocked_value_is_distinguished_from_declined(self):
        """⛔ The whole point: it must not become a synonym for any other value."""
        fb = PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding" / "feedback.md"
        flat = flatten(fb.read_text(encoding="utf-8"))
        self.assertIn(VALUE, flat)
        window = flat[flat.index(f"⛔ **`{VALUE}"): flat.index(f"⛔ **`{VALUE}") + 900] \
            if f"⛔ **`{VALUE}" in flat else flat
        self.assertIn("not a synonym", window,
                      "feedback.md lists the blocked value without saying it is not a synonym "
                      "for declined/failed — which is how it becomes one")
        self.assertIn("offered, declined", window,
                      "the guidance does not name the wrong value it exists to displace")

    def test_the_dry_run_skill_names_the_gate_and_the_wording(self):
        """Maintainer-side, so it never ships — but it is where the runner reads."""
        self.assertTrue(DRY_RUN.is_file(), "dry-run phase3 doc is missing")
        flat = flatten(DRY_RUN.read_text(encoding="utf-8"))
        self.assertIn("graduation", flat)
        self.assertIn(VALUE, flat,
                      "the dry-run phase-3 doc does not tell the runner which value to record")
        self.assertIn("present the offer", flat,
                      "the doc must say the offer is PRESENTED — skipping the gate silently "
                      "corrupts the thing phase 3 exists to observe")
        # `(?:> )?` -- the disclosure is a blockquote, and its line break leaves a `>` behind.
        self.assertRegex(
            flat, r"this is a dry run, so i can present this gate but i can't send on your "
                  r"answer here: a dry run (?:> )?never sends on the bootcamper's answer",
            "the disclosure wording is gone, so a runner has to improvise it mid-walk — which "
            "is the situation this instruction exists to remove")


def entry_side_enumeration_lines():
    """The enumerations of the ENTRY's `Upstream:` field: the spec-side line is left out.

    Matched on the entry-side siblings only, so the spec-side line (which carries
    `SPEC_SIDE_SIBLINGS` and not `SIBLINGS`) drops out by the same rule that finds it.
    """
    return [(p, n, line) for p, n, line in enumeration_lines()
            if all(s in line.lower() for s in SIBLINGS)]


def missing_pending(lines):
    return [f"{p.relative_to(REPO_ROOT)}:{n}  {line.strip()[:90]}"
            for p, n, line in lines if PENDING not in line.lower()]


class TheVocabularyCarriesAPendingValue(unittest.TestCase):
    """#167: an entry saved before its upstream answer has a value of its own."""

    def test_the_entry_side_enumerations_are_found(self):
        """⛔ INV-265 — both entry-side lists in `feedback.md`, at least."""
        self.assertGreaterEqual(len(entry_side_enumeration_lines()), 2)

    def test_every_entry_side_enumeration_includes_offer_pending(self):
        missing = missing_pending(entry_side_enumeration_lines())
        self.assertEqual(
            [], missing,
            f"an entry-side `Upstream:` enumeration omits `{PENDING}`, so an entry saved "
            "before its upstream answer has no legal value there:\n  " + "\n  ".join(missing))

    def test_the_append_sites_write_it(self):
        """Every path that appends before asking writes `offer pending`, and replaces it."""
        fb = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
                      / "feedback.md").read_text(encoding="utf-8"))
        grad = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "graduation"
                        / "SKILL.md").read_text(encoding="utf-8"))
        step3 = fb[fb.index("## step 3: append the entry"):fb.index("## step 3b:")]
        self.assertIn("write `**upstream:**` as `offer pending` when step 2b's verdict is "
                      "`mcp-server` or `both`", step3)
        self.assertIn("replacing `offer pending`", fb)
        self.assertIn("never leave `offer pending` once an answer exists", fb)
        silent = fb[fb.index("## silent in-run append"):]
        self.assertIn("`offer pending` when step 2b says `mcp-server`/`both`", silent)
        self.assertIn("append the entry as `offer pending`", grad)
        self.assertIn("replaces every `offer pending` value in the same turn", grad)
        self.assertIn("entries already reading `offer pending` from the silent in-run append",
                      grad)

    def test_a_resumed_session_re_presents_the_offer_once(self):
        fb = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
                      / "feedback.md").read_text(encoding="utf-8"))
        self.assertIn("### unanswered offer on resume", fb)
        block = fb[fb.index("### unanswered offer on resume"):fb.index("## step 4:")]
        self.assertIn("present the unanswered offer once more, then never again", block)
        self.assertIn("(inv-006)", block)
        self.assertIn("(inv-251) **the offer is its own turn.**", block)
        self.assertIn("replace every `offer pending` value with the outcome", block)
        onboarding = flatten((PLUGIN / "senzing-bootcamp" / "skills" / "bootcamp-onboarding"
                              / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn('follow `feedback.md` → "unanswered offer on resume"', onboarding,
                      "the resume branch does not point at the rule, so a resumed session "
                      "never finds the unanswered offer")

    def test_the_spec_side_says_offer_pending_is_still_owed(self):
        skill = REPO_ROOT / ".claude" / "skills" / "feedback-to-issues" / "SKILL.md"
        flat = flatten(skill.read_text(encoding="utf-8"))
        self.assertIn(f"`{PENDING}` is still owed too", flat,
                      "feedback-to-issues does not treat an unanswered offer as still owed, so "
                      "the report stops being anyone's job")


class TheNegativeControlsForThePendingValue(unittest.TestCase):
    """Removing `offer pending` from any one enumeration must fail the guard."""

    def test_removing_it_from_each_enumeration_fails(self):
        lines = entry_side_enumeration_lines()
        self.assertTrue(lines)
        for i, (p, n, line) in enumerate(lines):
            with self.subTest(site=f"{p.name}:{n}"):
                mutant = list(lines)
                mutant[i] = (p, n, re.sub(r"`?offer pending`?( \|)?,? ?", "", line))
                self.assertNotIn(PENDING, mutant[i][2].lower())
                self.assertTrue(missing_pending(mutant))


class TheOwnerStatesBothClosedSets(unittest.TestCase):
    """#223: `feedback-to-issues` Step 8.1 owns both sets and the mapping, as two tables."""

    def test_both_sets_parse_from_the_owner(self):
        """⛔ INV-265 — an owner the parser cannot read would certify every site vacuously."""
        self.assertTrue(entry_set(), "no `Entry value` table parsed from the owner's Step 8")
        self.assertTrue(issue_set(), "no `Issue value` table parsed from the owner's Step 8")
        for name, members in (("entry", entry_set()), ("issue", issue_set())):
            with self.subTest(field=name):
                self.assertEqual(len(members), len({norm(m) for m in members}),
                                 f"the {name} field's set lists a value twice")
                self.assertTrue(matching(f"{VALUE}:", members),
                                f"the {name} field's set has no `{VALUE}:` value")
        self.assertTrue(matching(PENDING, entry_set()))
        self.assertFalse(matching(PENDING, issue_set()),
                         "`offer pending` is never written on an issue (#167)")

    def test_the_mapping_uses_only_issue_values_and_covers_them(self):
        mapped = [v for row in mapping_rows() for cell in row[2:] for v in code_spans(cell)]
        self.assertEqual([], [v for v in mapped if len(matching(v, issue_set())) != 1],
                         "the mapping writes a value the issue field's set does not hold")
        self.assertEqual([], [m for m in issue_set() if not [v for v in mapped if matches(v, m)]],
                         "an issue-field value no entry value maps to")

    def test_every_value_is_classified_and_the_two_tables_agree(self):
        """Each entry value ends the obligation or keeps it, and its issue value says the same."""
        owed = {"no": False, "**yes**": True}
        issue_owed = {}
        for row in owner_tables().get("Issue value", []):
            verdict = row[1].split(" ")[0]
            self.assertIn(verdict, owed, f"issue value {row[0]} is not classified")
            issue_owed[norm(code_spans(row[0])[0])] = owed[verdict]
        for row in mapping_rows():
            verdict = row[1].split(" ")[0]
            with self.subTest(entry=row[0]):
                self.assertIn(verdict, owed, "entry value is not classified as ends / still owed")
                unattended = code_spans(row[3]) or code_spans(row[2])
                for v in unattended:
                    self.assertEqual(owed[verdict], issue_owed[norm(matching(v, issue_set())[0])],
                                     f"{row[0]} and the issue value {v} disagree on whether "
                                     "the report is still owed")
        by_value = {norm(code_spans(r[0])[0]): owed[r[1].split(" ")[0]]
                    for r in mapping_rows() if code_spans(r[0])}
        # ⛔ INV-281's own distinction: a decline ends the obligation, a consented send keeps it.
        self.assertFalse(by_value["offered, declined"])
        for kept in ("submission blocked: <reason>", "submission failed: <reason>", PENDING):
            self.assertTrue(by_value[kept], f"`{kept}` must be classified as still owed")

    def test_step_one_reads_submitted_as_already_sent(self):
        flat = flatten(OWNER.read_text(encoding="utf-8"))
        step1 = flat[flat.index("1. **check the entry's `upstream:` field first"):
                     flat.index("2. **draft the message")]
        self.assertIn("already have sent it (`submitted yyyy-mm-dd`)", step1,
                      "Step 8.1 must match the entry's own spelling of a send, `submitted`")
        self.assertNotIn("already have sent it (`sent", step1,
                         "Step 8.1 looks for the issue-side spelling on an entry")


class EveryEnumerationEqualsOneClosedSet(unittest.TestCase):
    def test_every_enumeration_equals_exactly_one_set(self):
        problems = enumeration_problems(enumeration_lines(), entry_set(), issue_set())
        self.assertEqual([], problems,
                         "an `Upstream:` enumeration is not its field's full closed set, as "
                         "`feedback-to-issues/SKILL.md` Step 8.1 states it:\n  "
                         + "\n  ".join(problems))

    def test_both_sides_are_enumerated(self):
        """⛔ INV-265 — one side found and the other not is a scan that went blind."""
        sides = {"entry": 0, "issue": 0}
        for _, _, line in enumeration_lines():
            values = pipe_values(line) or []
            for side, members in (("entry", entry_set()), ("issue", issue_set())):
                sides[side] += set_problem(values, members) == ([], [])
        for side, n in sides.items():
            with self.subTest(side=side):
                self.assertGreater(n, 0, f"no line enumerates the {side} field's set")

    def test_every_issue_template_line_is_found(self):
        """⛔ INV-265 — the delegate template's line was invisible to the sibling finder."""
        found = {p for p, _, _ in enumeration_lines()}
        templates = [p for p in MAINTAINER_SIDE.rglob("issue-template.md")
                     if "- Upstream: <" in p.read_text(encoding="utf-8")]
        self.assertTrue(any(p.parent.name == "delegate-to-mcp-server" for p in templates))
        for p in templates:
            with self.subTest(template=str(p.relative_to(REPO_ROOT))):
                self.assertIn(p, found, "this template's `Upstream:` line is not scanned")


class EveryWrittenValueIsAMember(unittest.TestCase):
    def test_written_values_are_found_in_every_tree(self):
        """⛔ INV-265 — shipped prose, maintainer skills and the command files each write one."""
        sites = [site for site, _, _ in written_values(corpus_docs())]
        for tree in ("plugins/", ".claude/skills/", ".claude/commands/"):
            with self.subTest(tree=tree):
                self.assertTrue([s for s in sites if s.startswith(tree)],
                                f"no value written into an `Upstream:` field was found under "
                                f"{tree}; the prose scan broke or stopped reaching it")

    def test_every_written_value_is_a_member_of_its_field(self):
        problems = written_value_problems(written_values(corpus_docs()), entry_set(), issue_set())
        self.assertEqual([], problems, "a value written into an `Upstream:` field is outside "
                         "its closed set:\n  " + "\n  ".join(problems))


class NoSiteSaysDryRunForbidsTheSend(unittest.TestCase):
    """#153 replaced the blanket ban; what blocks the send is who said yes, not the tool."""

    def test_no_site_says_dry_run_forbids_submit_feedback(self):
        hits = [str(p.relative_to(REPO_ROOT)) for p, text in corpus_docs()
                if STALE_DRY_RUN.search(re.sub(r"\s+", " ", text))]
        self.assertEqual([], hits, "these still say `/dry-run` forbids `submit_feedback`")


class TheNegativeControlsForTheClosedSets(unittest.TestCase):
    """Each new check fails on a planted defect, and names the site."""

    def test_dropping_a_value_from_each_enumeration_fails(self):
        lines = enumeration_lines()
        for i, (p, n, line) in enumerate(lines):
            parts = line.split(" | ")
            for j in range(1, len(parts) - 1):
                with self.subTest(site=f"{p.name}:{n}", dropped=norm(parts[j])):
                    mutant = list(lines)
                    mutant[i] = (p, n, " | ".join(parts[:j] + parts[j + 1:]))
                    self.assertEqual(len(parts) - 1, len(pipe_values(mutant[i][2])))
                    problems = enumeration_problems(mutant, entry_set(), issue_set())
                    self.assertEqual(1, len(problems))
                    self.assertIn(f"{p.relative_to(REPO_ROOT)}:{n}", problems[0])

    def test_adding_an_extra_value_fails(self):
        lines = enumeration_lines()
        p, n, line = lines[0]
        mutant = [(p, n, line.replace(" | ", " | pending (offer below) | ", 1))] + lines[1:]
        problems = enumeration_problems(mutant, entry_set(), issue_set())
        self.assertEqual(1, len(problems))
        self.assertIn("pending (offer below)", problems[0])

    def test_an_owner_change_reaches_every_enumeration(self):
        """The owner is the authority: drop a value there and every site of that field fails."""
        problems = enumeration_problems(enumeration_lines(), entry_set(),
                                        [m for m in issue_set() if "not yet sent" not in m])
        for skill in ("feedback-to-issues", "delegate-to-mcp-server"):
            with self.subTest(template=skill):
                self.assertTrue(any(f"{skill}/issue-template.md" in s for s in problems),
                                f"{skill}'s template did not fail when the owner dropped a value")

    def test_an_out_of_set_value_in_the_loop_prose_fails(self):
        text = LOOP_COMMAND.read_text(encoding="utf-8")
        mutant, count = re.subn(r"not yet sent — needs maintainer\s+approval",
                                "queued for the maintainer", text)
        self.assertEqual(1, count, "the loop's written value moved; re-point this control")
        docs = [(p, mutant if p == LOOP_COMMAND else t) for p, t in corpus_docs()]
        problems = written_value_problems(written_values(docs), entry_set(), issue_set())
        self.assertEqual(1, len(problems))
        self.assertIn("unattended-issue-loop.md:", problems[0])

    def test_the_stale_dry_run_rationale_is_caught(self):
        self.assertTrue(STALE_DRY_RUN.search("a maintainer `/dry-run`, which forbids calling "
                                     "`submit_feedback` under any category"))


if __name__ == "__main__":
    unittest.main()
