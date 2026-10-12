"""Module 3b completes on its own no-live-server path, on a verified snapshot (#512).

Before #512 the pre-advancement gate in `module-03b-truthset-visualization/phase2-close.md`
required `web_service.status` and `web_page.status` to be `"passed"` and said "If missing:
STOP", while Phase 1 documents two routes on which no server ever serves: a declined container
recreate (2.3) and "Fallback: guarantee the snapshot if the live server cannot run". On either,
`web_service` is never `passed`, so the Bootcamper could not complete the module by the route
the module itself prescribes. Step 3 meanwhile said "If failed: note the failure and proceed",
and all three success indicators required "the live app served its endpoints".

**One rule, stated once (INV-300).** The no-live-server completion rule lives at the gate, in an
anchored passage (`#no-live-server-completion`) that declares itself the canonical statement. It
names the `unavailable` state and its two reasons (`recreate_declined`, `server_failed`), the
record's shape (no `pid`, no `url`), what the gate accepts (`passed`, or `unavailable` with a
reason, and on either a present, non-empty snapshot built from `records_total > 0`), that a
missing, empty or zero-record snapshot blocks on every status, that `failed` is not accepted and
sends the agent to the Fallback, the snapshot-only tab check that replaces the server comparison
(INV-130 as amended, INV-155, INV-265), showing the snapshot by its path, and what Step 4 does.

Every other site points at it, carries INV-300, and carries none of its rule-only clauses:

- `phase2-close.md`: Step 3, Step 4 and the success indicator;
- `phase1-visualization.md`: 2.3's declined recreate, the checkpoint, the success indicator and
  the Fallback's closing step;
- `SKILL.md`: the success indicator.

So the checks are:

- `rule_problems` on the canonical passage, one entry per clause;
- `pointer_problems` on each site: a link to the anchor (by `phase2-close.md#…` from another
  file), INV-300, and no copy of a rule-only clause. One exemption, named in `SITE_MAY_SAY`:
  Step 4 says itself which of its items it skips (item 2, the live-server screenshots; item 3,
  server termination), because skipping them is that step's own action. That sentence was
  grafted from the race's losing approach A, which stated it at Step 4; B had left a reader at
  Step 4 to follow the link to learn it;
- `site_problems`: what each site still carries of its own (the success indicators' wording, the
  schema's three states and two reasons, Step 3 with no "note the failure and proceed", Step 4
  naming the two items it skips, 2.3 and the Fallback naming their reason);
- `retired_problems`: "note the failure and proceed" appears nowhere in the module.

Each check is a pure function over the shipped text, so each runs on a mutated copy as its
negative control and must report the clause it targets, not merely some problem. Phrases are
matched with `_wrapped_text.match_lines` (INV-346), and `ReWrapping` re-wraps every site to one
word per line and asserts the checks still pass, so a re-flow cannot turn the guard red and a
wrapped regression cannot turn it green.

⛔ **What this cannot establish:** that a live guide records `unavailable` rather than `passed`,
or shows the snapshot path before close. That is a conversational outcome and belongs to
`dry-run` phase 3. What it holds is that the instruction says so, once, and that every site that
depends on it points there.

Stdlib only; shipped files are read as text, never imported (INV-108).

Source issue: #512. Enforces the PROPOSED AMENDMENT to INV-130 queued in `specs/IMPLEMENTED.md`.

Run:  python3 -m unittest discover -s tests
"""
import re
import unittest
from pathlib import Path

from _wrapped_text import match_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills" / "module-03b-truthset-visualization"
PHASE1 = MODULE / "phase1-visualization.md"
PHASE2 = MODULE / "phase2-close.md"
SKILL = MODULE / "SKILL.md"

ANCHOR = '<a id="no-live-server-completion"></a>'
RULE_LINK_LOCAL = "(#no-live-server-completion)"
RULE_LINK_REMOTE = "(phase2-close.md#no-live-server-completion)"

#: INV-155's six identifiers, in the tab table's order.
TAB_IDS = ("tab-graph", "tab-stats", "tab-matchkeys", "tab-features", "tab-overlap", "tab-probe")

SUCCESS_PHRASE = (r"the live app served its endpoints, \*\*or\*\* the no-live-server state is "
                  r"recorded with its reason")


def read(path):
    return path.read_text(encoding="utf-8")


def has(text, pattern, flags=re.I):
    """True when ``pattern`` matches ``text`` anywhere, across a line wrap (INV-346)."""
    return bool(match_lines(text, re.compile(pattern, flags)))


def between(text, start, end=None):
    """The text from ``start`` up to ``end`` (or the end of the file); None if ``start`` is gone."""
    begin = text.find(start)
    if begin < 0:
        return None
    if end is None:
        return text[begin:]
    stop = text.find(end, begin + len(start))
    return text[begin:stop if stop >= 0 else len(text)]


# --------------------------------------------------------------------------------------------
# The canonical statement
# --------------------------------------------------------------------------------------------

#: (label, pattern) for each clause of the rule. A label is what a problem names.
RULE_CLAUSES = (
    ("owner declaration", r"This is the canonical statement of how this module completes"),
    ("INV-300", r"INV-300"),
    ("route: declined recreate", r'`"recreate_declined"`, when the bootcamper declined to '
                                 r"recreate a container that has no published port"),
    ("route: the Fallback", r'`"server_failed"`, when the server could not be made to serve '
                            r"after iterating with the MCP tools"),
    ("its own state, never passed", r"Record it as its own state, never as `passed`"),
    ("web_service shape: recreate_declined",
     r'`\{"status": "unavailable", "reason": "recreate_declined"\}`'),
    ("web_service shape: server_failed",
     r'`\{"status": "unavailable", "reason": "server_failed"\}`, with no `pid`'),
    ("web_page shape", r'`web_page` is `\{"status": "unavailable", "snapshot": '
                       r'"docs/visualizations/truthset_verification\.html"\}`, with no `url`'),
    ("accepted states", r'accepts\*\* `web_service\.status` = `"passed"`, or `"unavailable"` with '
                        r"one of the two reasons"),
    ("snapshot conditions on either",
     r"on either, the snapshot conditions above: present, non-empty, and built from "
     r"`records_total > 0`"),
    ("snapshot blocks on every status",
     r"A missing, empty or zero-record snapshot blocks on every status"),
    ("routes back to Phase 1", r"routes back to Phase 1"),
    ("failed not accepted", r"`failed` is not accepted"),
    ("failed runs the Fallback", r'run its "Fallback" section, which ends by recording '
                                 r'`unavailable` with `reason: "server_failed"`'),
    ("missing reason not accepted", r"`unavailable` with no reason, or with any other reason, is "
                                    r"not accepted"),
    ("snapshot tab check", r"On `unavailable`, check the snapshot's own tab set instead"),
    ("non-zero count", r"each with a non-zero count"),
    ("zero count did not run", r"means the check did not run, not that it passed \(INV-265\)"),
    ("warns, never blocks", r"warns and never blocks module completion \(INV-130, INV-048\)"),
    ("show the snapshot path", r"give them the snapshot by its file path, "
                               r"`docs/visualizations/truthset_verification\.html`"),
    ("skip item 2", r"Skip item 2, the live-server screenshots"),
    ("skip item 3", r"Skip item 3, termination: no `pid` was recorded"),
    ("INV-223 does not apply", r"INV-223's kill-by-pid does not apply"),
    ("teardown still asked", r"Still ask the teardown question\*\*, because the purge is "
                             r"irreversible"),
    ("disclosure: no live server", r"its disclosure says there is no live server"),
    ("disclosure: records removed", r"the Truth Set records will be removed from the database"),
) + tuple(("tab id %s" % tab, r'id="%s"' % tab) for tab in TAB_IDS)


def gate_blockquote(text):
    """The pre-advancement gate: the blockquote that opens with its bold title."""
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines)
                  if line.startswith("> **Pre-advancement verification")), None)
    if start is None:
        return ""
    end = start
    while end < len(lines) and lines[end].startswith(">"):
        end += 1
    return "\n".join(lines[start:end])


def rule_region(text):
    """The canonical passage: from its anchor to Step 3."""
    return between(text, ANCHOR, "## Step 3")


def rule_problems(text):
    """Problems with the canonical statement in ``text`` (all of `phase2-close.md`)."""
    region = rule_region(text)
    if region is None:
        return ["the canonical passage's anchor %s is gone" % ANCHOR]
    problems = []
    if ANCHOR not in gate_blockquote(text):
        problems.append("the canonical passage is not inside the pre-advancement gate")
    for label, pattern in RULE_CLAUSES:
        if not has(region, pattern):
            problems.append("the canonical passage is missing: %s" % label)
    return problems


def gate_problems(text):
    """The gate's own checkpoint bullet and STOP paragraph, outside the canonical passage."""
    gate = between(text, "Pre-advancement verification", ANCHOR)
    if gate is None:
        return ["the pre-advancement gate is gone"]
    problems = []
    checkpoint = between(gate, "In `config/bootcamp_progress.json`", "**The visualization artifact")
    if checkpoint is None or not has(checkpoint, r'or both `"unavailable"` with a `reason`'):
        problems.append("the gate's checkpoint bullet does not accept `unavailable` with a reason")
    if not has(gate, r"If the checkpoints are missing OR the snapshot file does not exist OR the "
                     r"snapshot was built from zero records"):
        problems.append("the gate's STOP paragraph is gone")
    if not has(gate, r"no-live-server completion rule below says what replaces this comparison"):
        problems.append("the tab-set bullet does not point at the no-live-server substitute")
    return problems


# --------------------------------------------------------------------------------------------
# The pointing sites
# --------------------------------------------------------------------------------------------

#: Phrases only the canonical passage may carry. A pointer that carries one has started a copy.
RULE_ONLY = (
    r"blocks on every status",
    r"non-zero count",
    r'id="tab-graph"',
    r"Skip item 2",
    r"Skip item 3",
    r"Still ask the teardown question",
    r"kill-by-pid does not apply",
    r"by its file path",
    r"never as `passed`",
)

#: {site label: rule-only phrases that site may carry}. Step 4 names its own skips (#512's graft
#: from approach A): skipping item 2 and item 3 is what Step 4 itself does, so a reader at Step 4
#: learns it there. Every other rule-only phrase stays forbidden at Step 4, and these two stay
#: forbidden everywhere else.
SITE_MAY_SAY = {"phase2 Step 4": (r"Skip item 2", r"Skip item 3")}


def sites():
    """{label: (region, link)} for every site that must point at the canonical passage."""
    p1, p2, sk = read(PHASE1), read(PHASE2), read(SKILL)
    return {
        "phase2 Step 3": (between(p2, "## Step 3", "## Step 4"), RULE_LINK_LOCAL),
        "phase2 Step 4": (between(p2, "## Step 4", "1. **Rebuild the snapshot"), RULE_LINK_LOCAL),
        "phase2 success indicator": (between(p2, "**Success indicator:**"), RULE_LINK_LOCAL),
        "phase1 2.3": (between(p1, "### 2.3 Start the live web app", "### 2.4"), RULE_LINK_REMOTE),
        "phase1 checkpoint": (between(p1, '"web_service": {"status"', "**Success indicator:**"),
                              RULE_LINK_REMOTE),
        "phase1 success indicator": (between(p1, "**Success indicator:**", "## Fallback"),
                                     RULE_LINK_REMOTE),
        "phase1 Fallback": (between(p1, "## Fallback"), RULE_LINK_REMOTE),
        "SKILL success indicator": (between(sk, "**Success indicator:**"), RULE_LINK_REMOTE),
    }


def pointer_problems(label, region, link):
    if region is None:
        return ["%s: the site is gone" % label]
    problems = []
    if link not in re.sub(r"\s+", "", region):
        problems.append("%s: no link to the canonical passage %s" % (label, link))
    if not has(region, r"INV-300"):
        problems.append("%s: the pointer does not cite INV-300" % label)
    for phrase in RULE_ONLY:
        if phrase in SITE_MAY_SAY.get(label, ()):
            continue
        if has(region, phrase):
            problems.append("%s: restates the rule (%s)" % (label, phrase))
    return problems


def all_pointer_problems(site_map=None):
    out = []
    for label, (region, link) in (site_map or sites()).items():
        out.extend(pointer_problems(label, region, link))
    return out


#: What each site still carries of its own: (label, pattern).
OWN = {
    "phase2 Step 3": (("failed or unavailable branch", r'If `"failed"` or `"unavailable"`'),
                      ("missing still stops", r"If missing: STOP")),
    "phase2 Step 4": (("skips item 2", r'When `web_service\.status` is `"unavailable"`,\*\* skip '
                                       r"item 2 \(the live-server screenshots\)"),
                      ("skips item 3", r"and item 3 \(server termination\) below")),
    "phase2 success indicator": (("success wording", SUCCESS_PHRASE),
                                 ("terminated when one ran", r"terminated when one ran")),
    "phase1 2.3": (("no live server", r"there is no live server"),
                   ("its reason", r'`reason: "recreate_declined"`')),
    "phase1 checkpoint": (
        ("web_service states", r'"web_service": \{"status": "passed\|failed\|unavailable"'),
        ("reasons", r'"reason": "recreate_declined\|server_failed"'),
        ("web_page states", r'"web_page": \{"status": "passed\|failed\|unavailable"'),
        ("reason only with unavailable", r'`reason` is written only with `"unavailable"`')),
    "phase1 success indicator": (("success wording", SUCCESS_PHRASE),),
    "phase1 Fallback": (("closing record", r"Close the fallback by recording the no-live-server "
                                           r'state:\*\* `web_service` and `web_page` as '
                                           r'`"unavailable"`, with `reason: "server_failed"`'),
                        ("failed does not complete", r'A `"failed"` status left in place does '
                                                     r"not complete the module")),
    "SKILL success indicator": (("success wording", SUCCESS_PHRASE),
                                ("terminated when one ran", r"when one ran, is terminated")),
}


def site_problems(site_map=None):
    out = []
    site_map = site_map or sites()
    for label, clauses in OWN.items():
        region = site_map[label][0]
        if region is None:
            out.append("%s: the site is gone" % label)
            continue
        for what, pattern in clauses:
            if not has(region, pattern):
                out.append("%s: missing %s" % (label, what))
    return out


RETIRED = r"note the failure and proceed"


def retired_problems(texts):
    """{name: text} -> the files that still carry Step 3's retired branch."""
    return ["%s:%s still says %r" % (name, lines, RETIRED)
            for name, text in sorted(texts.items())
            for lines in [match_lines(text, re.compile(RETIRED, re.I))] if lines]


def module_texts():
    return {p.name: read(p) for p in sorted(MODULE.glob("*.md"))}


# --------------------------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------------------------


class TheShippedTextIsClean(unittest.TestCase):
    def test_the_canonical_statement_carries_every_clause(self):
        self.assertEqual([], rule_problems(read(PHASE2)))

    def test_the_gate_accepts_unavailable_and_keeps_its_stop(self):
        self.assertEqual([], gate_problems(read(PHASE2)))

    def test_every_site_points_at_it_and_copies_none_of_it(self):
        self.assertEqual([], all_pointer_problems())

    def test_every_site_carries_its_own_part(self):
        self.assertEqual([], site_problems())

    def test_note_the_failure_and_proceed_is_gone(self):
        self.assertEqual([], retired_problems(module_texts()))

    def test_the_anchor_is_stated_once(self):
        """A second anchor would make every link ambiguous; the rule is stated once."""
        total = sum(text.count('id="no-live-server-completion"') for text in module_texts().values())
        self.assertEqual(1, total)


class TheChecksSeeSomething(unittest.TestCase):
    """⛔ INV-265: a guard over an empty site list passes by inspecting nothing."""

    def test_every_site_is_found(self):
        found = {label: region for label, (region, _link) in sites().items() if region}
        self.assertEqual(8, len(found), "sites not found: %s"
                         % sorted(set(sites()) - set(found)))

    def test_the_rule_clauses_are_numerous(self):
        self.assertGreaterEqual(len(RULE_CLAUSES), 30)


class TheCanonicalStatementCatchesARegression(unittest.TestCase):
    """Each removal must be reported by the clause it removed."""

    def setUp(self):
        self.text = read(PHASE2)

    def mutate(self, old, new=""):
        self.assertIn(old, self.text, "the control's target text is gone: %r" % old)
        return self.text.replace(old, new, 1)

    def assertReports(self, text, needle):
        problems = rule_problems(text)
        self.assertTrue(any(needle in p for p in problems),
                        "expected a problem naming %r, got %s" % (needle, problems))

    def test_each_accepted_state_and_reason(self):
        for old, needle in (
                ('or `"unavailable"` with one of the', "accepted states"),
                ('`{"status": "unavailable", "reason": "recreate_declined"}`',
                 "web_service shape: recreate_declined"),
                ('`"recreate_declined"`, when', "route: declined recreate"),
                ('`"server_failed"`, when', "route: the Fallback"),
                ('with `reason: "server_failed"`, then re-verify', "failed runs the Fallback"),
        ):
            with self.subTest(old=old):
                self.assertReports(self.mutate(old, "X"), needle)

    def test_the_snapshot_block_removed(self):
        self.assertReports(
            self.mutate("A missing, empty or zero-record snapshot blocks on every status"),
            "snapshot blocks on every status")

    def test_the_snapshot_block_narrowed_to_one_status(self):
        self.assertReports(
            self.mutate("blocks on every status", "blocks on `passed`"),
            "snapshot blocks on every status")

    def test_failed_accepted(self):
        self.assertReports(self.mutate("**`failed` is not accepted.**", "**`failed` is fine.**"),
                           "failed not accepted")

    def test_passed_allowed_on_this_path(self):
        self.assertReports(self.mutate("never as `passed`", "or as `passed`"),
                           "its own state, never passed")

    def test_each_tab_identifier_dropped(self):
        for tab in TAB_IDS:
            with self.subTest(tab=tab):
                self.assertReports(self.mutate('`id="%s"`' % tab, "`x`"), "tab id %s" % tab)

    def test_the_zero_count_reading(self):
        self.assertReports(self.mutate("each with a non-zero count"), "non-zero count")
        self.assertReports(self.mutate("means the check did not run, not that it passed",
                                       "means it passed"), "zero count did not run")

    def test_the_tab_check_made_blocking(self):
        self.assertReports(self.mutate("this warns and never blocks", "this blocks"),
                           "warns, never blocks")

    def test_the_snapshot_path_not_shown(self):
        self.assertReports(self.mutate("give them the snapshot by its file path",
                                       "tell them about the snapshot"), "show the snapshot path")

    def test_step_four_clauses(self):
        for old, needle in (
                ("Skip item 2, the live-server screenshots", "skip item 2"),
                ("Skip item 3, termination", "skip item 3"),
                ("**Still ask the\n>   teardown question**", "teardown still asked"),
                ("its disclosure says there is no live", "disclosure: no live server"),
                ("the Truth Set records will\n>   be removed", "disclosure: records removed"),
        ):
            with self.subTest(old=old):
                self.assertReports(self.mutate(old, "X"), needle)

    def test_the_owner_declaration_and_citation(self):
        self.assertReports(self.mutate("This is the canonical statement of how", "This says how"),
                           "owner declaration")

    def test_the_anchor_removed(self):
        self.assertEqual(["the canonical passage's anchor %s is gone" % ANCHOR],
                         rule_problems(self.mutate(ANCHOR)))

    def test_the_passage_moved_out_of_the_gate(self):
        moved = self.mutate(ANCHOR).replace("## Step 3", ANCHOR + "\n\n## Step 3", 1)
        self.assertTrue(any("not inside the pre-advancement gate" in p
                            for p in rule_problems(moved)))


class TheGateCatchesARegression(unittest.TestCase):
    def setUp(self):
        self.text = read(PHASE2)

    def test_passed_only_restored(self):
        old = ('`"passed"`, or both\n>   `"unavailable"` with a `reason` on `web_service`, as the '
               "no-live-server completion rule below\n>   allows.")
        self.assertIn(old, self.text)
        problems = gate_problems(self.text.replace(old, '`"passed"`.', 1))
        self.assertTrue(any("does not accept `unavailable`" in p for p in problems), problems)

    def test_the_stop_paragraph_removed(self):
        old = "If the checkpoints are missing OR the snapshot file does not exist OR"
        self.assertIn(old, self.text)
        problems = gate_problems(self.text.replace(old, "If anything is off", 1))
        self.assertTrue(any("STOP paragraph" in p for p in problems), problems)


class ThePointersCatchARegression(unittest.TestCase):
    def test_a_missing_link_is_reported_at_each_site(self):
        for label, (region, link) in sites().items():
            with self.subTest(site=label):
                self.assertIn(link, re.sub(r"\s+", "", region))
                broken = region.replace("#no-live-server-completion", "#elsewhere")
                problems = pointer_problems(label, broken, link)
                self.assertIn("%s: no link to the canonical passage %s" % (label, link), problems)

    def test_a_missing_citation_is_reported_at_each_site(self):
        for label, (region, link) in sites().items():
            with self.subTest(site=label):
                problems = pointer_problems(label, region.replace("INV-300", ""), link)
                self.assertIn("%s: the pointer does not cite INV-300" % label, problems)

    def test_step_fours_exemption_covers_only_its_own_skips(self):
        """`SITE_MAY_SAY` lets Step 4 name its skips, and nothing else, and no other site."""
        p2 = sites()
        region, link = p2["phase2 Step 4"]
        self.assertTrue(has(region, r"Skip item 2"), "the control needs Step 4's own skip sentence")
        self.assertEqual([], pointer_problems("phase2 Step 4", region, link))
        copied = region + "\n\nStill ask the teardown question.\n"
        self.assertIn("phase2 Step 4: restates the rule (Still ask the teardown question)",
                      pointer_problems("phase2 Step 4", copied, link))
        step3, link3 = p2["phase2 Step 3"]
        moved = step3 + "\n\nOn `unavailable`, skip item 2 and Skip item 3.\n"
        problems = pointer_problems("phase2 Step 3", moved, link3)
        self.assertIn("phase2 Step 3: restates the rule (Skip item 2)", problems)
        self.assertIn("phase2 Step 3: restates the rule (Skip item 3)", problems)

    def test_a_copied_clause_is_reported_at_each_site(self):
        copied = "\n\nA missing, empty or zero-record snapshot blocks on every status.\n"
        for label, (region, link) in sites().items():
            with self.subTest(site=label):
                problems = pointer_problems(label, region + copied, link)
                self.assertIn("%s: restates the rule (blocks on every status)" % label, problems)


class TheSitesCatchARegression(unittest.TestCase):
    def mutated(self, label, old, new):
        site_map = sites()
        region, link = site_map[label]
        self.assertIn(old, region, "the control's target text is gone: %r" % old)
        site_map[label] = (region.replace(old, new, 1), link)
        return site_problems(site_map)

    def test_the_success_wording_at_each_indicator(self):
        for label, old in (("phase2 success indicator", "**or** the no-live-server state"),
                           ("phase1 success indicator", "**or**\nthe no-live-server state"),
                           ("SKILL success indicator", "**or** the no-live-server state")):
            with self.subTest(site=label):
                self.assertIn("%s: missing success wording" % label,
                              self.mutated(label, old, "and the live server state"))

    def test_the_schema_states_and_reasons(self):
        for old, what in (('"passed|failed|unavailable", "port"', "web_service states"),
                          ('"recreate_declined|server_failed"', "reasons"),
                          ('"passed|failed|unavailable", "url"', "web_page states")):
            with self.subTest(what=what):
                self.assertIn("phase1 checkpoint: missing %s" % what,
                              self.mutated("phase1 checkpoint", old, '"passed|failed", "x"'))

    def test_the_fallback_closing_record(self):
        self.assertIn("phase1 Fallback: missing closing record",
                      self.mutated("phase1 Fallback", 'with `reason: "server_failed"`',
                                   'with no reason'))

    def test_the_declined_recreate_names_its_reason(self):
        self.assertIn("phase1 2.3: missing its reason",
                      self.mutated("phase1 2.3", '`reason: "recreate_declined"`', "a note"))

    def test_step_four_loses_its_own_skips(self):
        """The graft from approach A: Step 4 names the items it skips on `unavailable`."""
        for old, what in (("skip item 2 (the live-server screenshots) and\nitem 3 (server "
                           "termination) below", ("skips item 2", "skips item 3")),
                          ("item 3 (server termination) below", ("skips item 3",)),
                          ("skip item 2 (the live-server screenshots)", ("skips item 2",))):
            with self.subTest(old=old):
                problems = self.mutated("phase2 Step 4", old, "follow the rule")
                for one in what:
                    self.assertIn("phase2 Step 4: missing %s" % one, problems)

    def test_step_three_loses_its_branch(self):
        self.assertIn("phase2 Step 3: missing failed or unavailable branch",
                      self.mutated("phase2 Step 3", '`"failed"` or `"unavailable"`',
                                   '`"failed"`'))

    def test_the_retired_branch_restored_and_rewrapped(self):
        for restored in ("- If failed: note the failure and proceed.",
                         "- If failed: note the failure\n  and proceed (it was attempted)."):
            with self.subTest(restored=restored):
                text = read(PHASE2).replace("## Step 4", restored + "\n\n## Step 4", 1)
                self.assertEqual(1, len(retired_problems({"phase2-close.md": text})))


def rewrap(text):
    """One word per line, keeping a blockquote's marker: the most extreme legal re-flow."""
    out = []
    for line in text.split("\n"):
        quote = re.match(r"^(\s*>\s?)", line)
        prefix = quote.group(1) if quote else ""
        body = line[len(prefix):]
        if not body.strip() or body.lstrip().startswith(("```", "|", "#", "<a ")):
            out.append(line)
            continue
        indent = re.match(r"^\s*", body).group(0)
        words = body.strip().split(" ")
        out.append(prefix + indent + words[0])
        for word in words[1:]:
            # A word that would read as Markdown structure at a line's start (a quote marker,
            # a heading, a table row, a list marker) stays on the line before, as a writer
            # re-flowing by hand would keep it.
            if re.match(r"^(?:[>#|+*-]|\d+\.$)", word):
                out[-1] += " " + word
            else:
                out.append(prefix + indent + "  " + word)
    return "\n".join(out)


class ReWrapping(unittest.TestCase):
    """INV-346: a re-flow of the shipped prose must not turn the guard red."""

    def test_the_canonical_statement_survives_a_rewrap(self):
        text = read(PHASE2)
        region = rule_region(text)
        self.assertEqual([], rule_problems(text.replace(region, rewrap(region), 1)))

    def test_every_site_survives_a_rewrap(self):
        site_map = {label: (rewrap(region), link) for label, (region, link) in sites().items()}
        self.assertEqual([], all_pointer_problems(site_map))
        self.assertEqual([], site_problems(site_map))

    def test_a_rewrapped_regression_is_still_caught(self):
        text = read(PHASE2)
        region = rule_region(text)
        broken = rewrap(region.replace("blocks on every status", "blocks on `passed`"))
        problems = rule_problems(text.replace(region, broken, 1))
        self.assertTrue(any("snapshot blocks on every status" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
