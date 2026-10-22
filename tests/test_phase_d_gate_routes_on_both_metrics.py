"""Module 6 Phase D's gate routes on BOTH metrics, and every pair of readings has a branch.

The iterate-vs-proceed gate required the UAT % **and** the match accuracy for its success
branch — "UAT ≥90% and match accuracy ≥90%" — and then branched on the UAT % alone for every
other outcome: "UAT 80–89%" and "UAT <80%". A bootcamper holding UAT 95% with match accuracy
70% matched no branch at all. The gate that demanded two readings routed on one, and the
reading it dropped was the one that had failed.

The fix is a decision table in the gate, plus a branch for the outcome that had none:

* **the table** — a row for every pair of readings the gate can hold, with no pair matching two
  rows and no pair matching none. `any` and `none` are cells in their own right, so "no entity
  could be spot-checked" and "no per-record accuracy was established" route rather than fall
  through;
* **the accuracy-shortfall branch** — UAT ≥90% with match accuracy below 90% (or never
  established) is its own branch: not the strong branch, whose statement requires both figures,
  and not either low-UAT route, which routes on a UAT % that is fine. It reports the accuracy
  shortfall as the blocking evidence, recommends tuning the match keys before the sign-off
  stands, and hands the existing quality-iteration route a band of its own,
  `uat_90_accuracy_below_90`;
* **the strong label** — never stated where a metric the strong branch explicitly requires falls
  short or was never established;
* **what the branch does not change** — the match-key and how-state audit outcomes are still
  disclosed in full on it, still never block and still never move the gate to a different branch
  (INV-117, INV-264); accuracy still routes on the **per-record** bucket only (INV-264); and the
  handling step, the route and its resume are untouched, so "Iterate now" still names the
  sources, enters the route with `return_to: "module_6_phase_d"` and comes back to step 21.

⛔ **The router is built from the shipped table, not from a copy of it here.** The bands are
parsed out of the table's own cells, so the completeness and non-overlap checks cannot be
satisfied by editing a specification kept in this file. A cell whose text this file cannot read
is a FAILURE, never a skip (INV-265): an unparsed row is indistinguishable from a row that
routes nothing.

⚠️ **Boundaries.** The gate's bands are read as the table's legend states them — a band runs up
to the next band's floor, so `80–89%` is 80 up to but not including 90. The grid below therefore
includes the fractional readings either side of each boundary as well as the whole percentages,
and asserts exactly one matching row for each of the pairs it forms.

⛔ **Each check is a function of the file text, so the negative controls run the SAME check on a
mutated copy** (INV-265). ⛔ **Every phrase is matched across line wraps (INV-346):** the texts
are flattened before matching, and `ReWrapping` re-flows the prose to one word per line and
asserts the checks still pass.

**The accuracy figure the table routes on is defined once (#750).** The gate routed on "per-record
match accuracy" and no plugin text said how to compute it, so on a generated scenario with an
answer key a guide had three defensible readings (100% of merged records, 87.3% recall, 8 of 10
in the step-21 sample), and either of the two it did not route on would have sent the Bootcamper
to the accuracy-shortfall branch. Step 22 now anchors one definition, `#per-record-match-accuracy`,
beside `#uat-percent`:

* **the figure** — reviewed records whose resolution is judged correct ÷ records reviewed, a whole
  percentage written to `docs/uat_results.md` with both counts and the sample named; no record
  reviewed is `none`, which the table's `none` cells route;
* **what routes** — only this figure. Pairwise precision and recall, computed the way
  `reporting_guide(topic='quality')` describes, are reported beside it when a ground truth exists,
  never route, and are never estimated without one;
* **stated once** — the formula appears in no other shipped Markdown file, and nowhere else in
  this one (INV-300);
* **the links** — the gate prose, the accuracy column's legend and the table header link the
  anchor.

The checks assert that the skill files *state* these rules; they **cannot** establish that a live
guide follows them. `dry-run` phase 3 observes that.

Source issues: #678, #750. Invariants: INV-056, INV-117, INV-264, INV-265, INV-284, INV-300,
INV-346, INV-400, INV-404.

INV-404 (a gate whose outcome states a conjunction of conditions routes every combination of its
readings to exactly one branch, and a failed required condition gets a branch of its own) names
this file as its enforcer: the router built from the shipped table and its negative controls are
what it relies on. They establish that the table is total and non-overlapping as written; they do
not establish that a live guide routes a reading by it, which only `dry-run` phase 3 observes.

INV-400 (the gate routes on the per-record match accuracy step 22 defines, never on precision or
recall) names this file as its enforcer: `TheAccuracyFigureIsDefinedOnce` and its negative
controls are what it relies on. They establish that the skill file states the rule; they do not
establish that a live guide computes the figure or keeps recall out of the routing, which only
`dry-run` phase 3 observes.

Run:  python3 -m unittest discover -s tests
"""
import itertools
import re
import unittest
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
PHASE_D = SKILLS / "module-06-data-processing" / "phaseD-validation.md"
PHASE_1 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"

GATE_HEADING = "## Iterate vs. proceed decision gate"
GATE_END = "## Stakeholder summary"
SHORTFALL_BULLET = "- **UAT ≥90% but match accuracy <90% — the accuracy shortfall:**"
BAND = "uat_90_accuracy_below_90"

#: #750: the one definition of the accuracy figure, its anchor, and the link every routing site uses.
ACCURACY_ANCHOR = '<a id="per-record-match-accuracy"></a>'
ACCURACY_LINK = "(#per-record-match-accuracy)"
TABLE_HEADER = "| UAT % | [Per-record match accuracy](#per-record-match-accuracy) | Branch |"
STEP_22 = "## 22. "
STEP_22_END = "**Checkpoint:** write step 22."
#: The formula, matched across wraps; it must appear once in the shipped Markdown (INV-300).
FORMULA = "reviewed records whose resolution is judged correct ÷ records reviewed"

STRONG = "Results look strong"
SHORTFALL = "Accuracy shortfall"
MIXED = "Results are mixed"
IMPROVE = "Results need improvement"
BRANCHES = (STRONG, SHORTFALL, MIXED, IMPROVE)

#: Whole percentages and the fractional readings either side of each band boundary, plus the
#: "not computed" reading. 11 × 11 pairs, every one of which the table must route exactly once.
READINGS = (None, 0, 50, 79, 79.5, 80, 85, 89, 89.5, 90, 100)


def plain(text):
    return text.replace("**", "")


def flat(text):
    return re.sub(r"\s+", " ", plain(text)).strip()


def find(text, phrase, start=0):
    """The first match of `phrase` in `text` at or after `start`, across line wraps (INV-346)."""
    words = plain(phrase).split()
    return re.compile(r"\s+".join(re.escape(w) for w in words)).search(plain(text), start)


def read(path):
    return path.read_text(encoding="utf-8")


def gate(text):
    """The gate section of Phase D, or None when its heading moved."""
    if GATE_HEADING not in text or GATE_END not in text:
        return None
    start = text.index(GATE_HEADING)
    return text[start:text.index(GATE_END, start)]


# ------------------------------------------------------------------ the shipped decision table


class UnreadableCell(Exception):
    """A table cell this file cannot turn into a band. ⛔ Never swallowed (INV-265)."""


def band(cell):
    """The predicate a table cell states, over a reading that is a number or None.

    ⚠️ The bands come from the cells themselves. Nothing here hardcodes which bands the gate
    has, so a band added, removed or renamed in the shipped table is read as written — or, if
    its text cannot be parsed, raises, which fails the check rather than quietly dropping a row.
    """
    cell = plain(cell).strip()
    if cell == "any":
        return lambda value: True
    if cell == "none":
        return lambda value: value is None
    m = re.fullmatch(r"≥(\d+)%", cell)
    if m:
        low = float(m.group(1))
        return lambda value, low=low: value is not None and value >= low
    m = re.fullmatch(r"<(\d+)%", cell)
    if m:
        high = float(m.group(1))
        return lambda value, high=high: value is not None and value < high
    m = re.fullmatch(r"(\d+)[–-](\d+)%", cell)
    if m:
        # The legend states a band runs up to the next band's floor, so 80–89% is [80, 90).
        low, high = float(m.group(1)), float(m.group(2)) + 1
        return lambda value, low=low, high=high: (
            value is not None and low <= value < high)
    raise UnreadableCell(cell)


def table_rows(text):
    """`[(uat_cell, accuracy_cell, branch)]` read off the gate's decision table."""
    section = gate(text)
    if section is None:
        return []
    if TABLE_HEADER not in section:
        return []
    rows = []
    for line in section[section.index(TABLE_HEADER):].split("\n")[1:]:
        line = line.strip()
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 3 or set(cells[0]) <= set("-: "):
            continue
        rows.append(tuple(cells))
    return rows


def matching_branches(rows, uat, accuracy):
    """Every branch whose row matches this pair of readings."""
    return [branch for uat_cell, acc_cell, branch in rows
            if band(uat_cell)(uat) and band(acc_cell)(accuracy)]


# ------------------------------------------------------------------------------------- checks


def table_problems(text):
    """Every pair of readings matches exactly one row, and every branch has a bullet."""
    rows = table_rows(text)
    if not rows:
        return ["the gate has no decision table over the UAT % and the match accuracy"]
    problems = []
    section = flat(gate(text) or "")
    for uat, accuracy in itertools.product(READINGS, repeat=2):
        try:
            hits = matching_branches(rows, uat, accuracy)
        except UnreadableCell as unreadable:
            return ["a decision-table cell cannot be read as a band: %s" % unreadable]
        if len(hits) != 1:
            problems.append("UAT %r with accuracy %r matches %d rows (%s)"
                            % (uat, accuracy, len(hits), ", ".join(hits) or "none"))
    for _uat, _acc, branch in rows:
        if branch not in BRANCHES:
            problems.append("the table routes to an unknown branch %r" % branch)
        elif branch.lower() not in section.lower():
            problems.append("the table routes to %r and no branch below states it" % branch)
    return sorted(set(problems))[:12]


def shortfall_problems(text):
    """The accuracy-shortfall branch states evidence, recommendation, question and routes."""
    section = gate(text)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    opening = find(section, SHORTFALL_BULLET)
    if opening is None:
        return ["the gate has no accuracy-shortfall branch"]
    closing = find(section, "- UAT 80–89%:", opening.end())
    if closing is None:
        return ["the accuracy-shortfall branch is not followed by the 80–89% branch"]
    branch = flat(plain(section)[opening.start():closing.start()])
    problems = []
    needed = (
        # it is its own branch, and says which branches it is not
        "It is not the\n  strong branch",
        "it is not\n  either low-UAT route",
        # the evidence, reported as what blocks the sign-off
        "Evidence — the accuracy shortfall",
        "what blocks the sign-off",
        "below the 90% this gate requires",
        "never established is named as exactly that",
        # the recommendation
        "Recommendation — tune the match keys before the sign-off stands",
        # the next skill-defined question
        "Next question — the gate question below",
        "option 1 marked *(recommended)*",
        "No other question belongs to this branch",
        # the accepted and declined return routes
        "Accepted and declined — the handling step below",
        '"Iterate now" is the accepted',
        '`from_verdict: "%s"`' % BAND,
        '"Move forward" is the declined',
        # disclosure and the non-blocking rule, preserved verbatim in kind
        "match-key and how-state\n    audit outcomes are reported here in full",
        "neither moves this\n    branch nor blocks it (INV-117, INV-264)",
    )
    problems += ["the accuracy-shortfall branch does not say %r" % phrase
                 for phrase in needed if flat(phrase) not in branch]
    if flat("Results look strong") in branch:
        problems.append("the accuracy-shortfall branch states the strong label")
    return problems


def strong_label_problems(text):
    """The strong label is never reachable with a required metric short or missing."""
    section = gate(text)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    problems = []
    rule = ("⛔ **Never call a result strong when a metric the strong branch explicitly requires "
            "falls short or was never established**")
    if flat(rule) not in flat(section):
        problems.append("the gate does not forbid the strong label where a required metric fails")
    rows = table_rows(text)
    if not rows:
        return problems + ["the gate has no decision table"]
    required = band("≥90%")
    for uat, accuracy in itertools.product(READINGS, repeat=2):
        try:
            hits = matching_branches(rows, uat, accuracy)
        except UnreadableCell as unreadable:
            return problems + ["a decision-table cell cannot be read as a band: %s" % unreadable]
        if STRONG in hits and not required(accuracy):
            problems.append("accuracy %r is routed to %r" % (accuracy, STRONG))
    return sorted(set(problems))[:12]


def per_record_problems(text):
    """The accuracy the table routes on is the per-record figure, not a pooled share."""
    section = gate(text)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    section = flat(section)
    return [
        "the decision table does not say %r" % phrase for phrase in (
            "The accuracy column is the **per-record** figure (the INV-264 rule above), never a "
            "relationship-bucket share",
            "A band runs up to the next band's floor",
        ) if flat(phrase) not in section
    ] + [
        "the gate no longer says an audit finding leaves the branch alone"
    ] * (flat("does not\nmove the gate to a different branch (INV-117, INV-264)")
         not in section)


def route_problems(phase_d, phase_1):
    """The new band reaches the one canonical statement of the quality-iteration route."""
    problems = []
    if flat("(`uat_80_89`, `uat_below_80`, or `%s` on the accuracy-shortfall branch)" % BAND) \
            not in flat(phase_d):
        problems.append("Phase D's handling step does not hand the route the new band")
    for phrase in (
            '"from_verdict": "poor | marginal | uat_below_80 | uat_80_89 | %s"' % BAND,
            "`uat_below_80`, `uat_80_89` or `%s`" % BAND,
    ):
        if flat(phrase) not in flat(phase_1):
            problems.append("the quality-iteration route does not record %r" % phrase)
    # INV-300: Phase D hands the route a band; it does not restate the route or the record.
    if '"quality_iteration": {' in phase_d:
        problems.append("Phase D restates the quality_iteration key")
    return problems


def resume_problems(phase_d):
    """The iterate/resume behavior the new branch reuses is unchanged."""
    section = gate(phase_d)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    section = flat(section)
    return ["the gate's handling step no longer says %r" % phrase for phrase in (
        '`return_to: "module_6_phase_d"`',
        "Phase D runs again in full, from step 21",
        "this gate is asked again on the new results",
        "With one, ask nothing and use it",
    ) if flat(phrase) not in section]


def accuracy_definition(text):
    """Step 22's text from the accuracy anchor to the step's checkpoint, or None (#750)."""
    if STEP_22 not in text:
        return None
    start = text.index(STEP_22)
    # Matched across wraps on the raw text, so the slice keeps its offsets (INV-346).
    end = re.compile(r"\s+".join(map(re.escape, STEP_22_END.split()))).search(text, start)
    if end is None:
        return None
    step = text[start:end.start()]
    if ACCURACY_ANCHOR not in step:
        return None
    return step[step.index(ACCURACY_ANCHOR):]


def definition_problems(text):
    """Step 22 defines the figure: numerator, denominator, sample, `none`, and what routes."""
    if text.count(ACCURACY_ANCHOR) != 1:
        return ["Phase D anchors the per-record match accuracy %d times, not once"
                % text.count(ACCURACY_ANCHOR)]
    definition = accuracy_definition(text)
    if definition is None:
        return ["step 22 does not anchor the per-record match accuracy definition"]
    if '<a id="uat-percent"></a>' not in text[:text.index(ACCURACY_ANCHOR)]:
        problems = ["the per-record match accuracy is not defined beside the UAT %"]
    else:
        problems = []
    body = flat(definition)
    needed = (
        # the figure: numerator, denominator, unit, sample
        "**Per-record match accuracy**",
        FORMULA,
        "as a whole percentage",
        "The sample is the records step 21's review looked up, each counted once",
        "with 2+ sources, the records step 24 reviews join it",
        "A record that could not be found counts as reviewed and not correct",
        # where it is written, and with what
        "Write it to `docs/uat_results.md` beside the UAT %, with both counts and the sample named",
        # no record reviewed: no figure, routed as none
        "If no record was reviewed, write that instead, with the reason, and no percentage",
        "the gate reads it as `none`",
        "keep the two apart",
        # only this figure routes; precision and recall are findings beside it
        "⛔ **(INV-400) Only this figure routes the gate's accuracy column.**",
        "When a ground truth exists for the scenario",
        "pairwise precision and recall the way "
        "`reporting_guide(topic='quality', language='<chosen_language>', version='current')` "
        "describes",
        "report both beside this figure as findings",
        "They never route, and never replace or adjust this figure, including when they "
        "disagree with it",
        "With no ground truth, leave them out; never estimate them",
        "The Bootcamper's own data and generated data are computed the same way",
    )
    problems += ["the per-record match accuracy definition does not say %r" % phrase
                 for phrase in needed if flat(phrase) not in body]
    return problems


def link_problems(text):
    """The gate prose, the accuracy column's legend and the table header link the definition."""
    section = gate(text)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    problems = []
    if TABLE_HEADER not in section:
        problems.append("the decision table's accuracy header does not link the definition")
    rule = find(section, "⛔ **(INV-264) Route match accuracy")
    if rule is None:
        return problems + ["the gate's INV-264 rule moved, so its routing sentence is not found"]
    lead = flat(plain(section)[:rule.start()])
    if flat("the per-record match accuracy from the same file (step 22 → "
            "[per-record match accuracy]%s)" % ACCURACY_LINK) not in lead:
        problems.append("the gate's routing sentence does not read the linked figure")
    if flat("never a relationship-bucket share: the [per-record match accuracy]%s step 22 "
            "defines, never precision or recall" % ACCURACY_LINK) not in flat(section):
        problems.append("the accuracy column's legend does not link the definition")
    return problems


def stated_once_problems(corpus):
    """INV-300: the formula is written in one place across the shipped Markdown."""
    hits = ["%s (%d)" % (name, flat(text).count(flat(FORMULA)))
            for name, text in sorted(corpus.items()) if flat(FORMULA) in flat(text)]
    total = sum(flat(text).count(flat(FORMULA)) for text in corpus.values())
    if total != 1:
        return ["the per-record match accuracy formula is stated %d times: %s"
                % (total, ", ".join(hits) or "nowhere")]
    return []


CHECKS = {
    "definition": (definition_problems, ("phase_d",)),
    "links": (link_problems, ("phase_d",)),
    "table": (table_problems, ("phase_d",)),
    "shortfall": (shortfall_problems, ("phase_d",)),
    "strong": (strong_label_problems, ("phase_d",)),
    "per_record": (per_record_problems, ("phase_d",)),
    "route": (route_problems, ("phase_d", "phase_1")),
    "resume": (resume_problems, ("phase_d",)),
}


def run(name, texts):
    fn, keys = CHECKS[name]
    return fn(*(texts[k] for k in keys))


def read_all():
    return {"phase_d": read(PHASE_D), "phase_1": read(PHASE_1)}


def shipped_markdown():
    """`{relative path: text}` for every shipped Markdown file under `plugins/`."""
    return {path.relative_to(REPO_ROOT).as_posix(): read(path)
            for path in corpus_files("plugins", suffixes={".md"})}


def rewrap(text):
    """One word per line for every prose line; headings, anchors, tables and fences are kept."""
    out = []
    fenced = False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fenced = not fenced
        if fenced or stripped.startswith(("#", "|", "<a ", "```")) or not stripped:
            out.append(line)
            continue
        indent = line[:len(line) - len(stripped)]
        out.append(("\n" + indent).join([indent + stripped.split(" ")[0]] +
                                        stripped.split(" ")[1:]))
    return "\n".join(out)


# ----------------------------------------------------------------------------------- the file


class TheShippedGateRoutesEveryPairOfReadings(unittest.TestCase):
    def setUp(self):
        self.texts = read_all()

    def test_the_gate_is_found(self):
        """⛔ INV-265: a scan of a moved section certifies nothing."""
        self.assertIsNotNone(gate(self.texts["phase_d"]))
        self.assertTrue(table_rows(self.texts["phase_d"]), "the decision table is missing")

    def test_every_pair_of_readings_matches_exactly_one_row(self):
        self.assertEqual([], run("table", self.texts))

    def test_the_reported_case_routes_to_the_new_branch(self):
        """#678's own case: UAT 95% with match accuracy 70% matched no branch at all."""
        rows = table_rows(self.texts["phase_d"])
        self.assertEqual([SHORTFALL], matching_branches(rows, 95, 70))

    def test_the_boundary_readings_route_as_the_bands_state(self):
        rows = table_rows(self.texts["phase_d"])
        for uat, accuracy, expected in (
                (90, 90, STRONG), (90, 89.5, SHORTFALL), (90, 89, SHORTFALL),
                (100, 90, STRONG), (89.5, 100, MIXED), (89, 100, MIXED),
                (80, 0, MIXED), (79.5, 100, IMPROVE), (79, 100, IMPROVE),
                (95, None, SHORTFALL), (None, 95, STRONG), (None, 85, MIXED),
                (None, 79, IMPROVE), (None, None, SHORTFALL)):
            with self.subTest(uat=uat, accuracy=accuracy):
                self.assertEqual([expected], matching_branches(rows, uat, accuracy))

    def test_the_accuracy_shortfall_branch_states_everything_a_branch_states(self):
        self.assertEqual([], run("shortfall", self.texts))

    def test_a_result_is_never_strong_with_the_accuracy_condition_failing(self):
        self.assertEqual([], run("strong", self.texts))

    def test_accuracy_routes_on_the_per_record_bucket_only(self):
        self.assertEqual([], run("per_record", self.texts))

    def test_the_new_band_reaches_the_quality_iteration_route(self):
        self.assertEqual([], run("route", self.texts))

    def test_the_iterate_and_resume_behavior_is_preserved(self):
        self.assertEqual([], run("resume", self.texts))

    def test_the_strong_statement_is_pinned_to_its_own_branch(self):
        """One branch states "Results look strong." — the one with both figures."""
        section = gate(self.texts["phase_d"])
        self.assertEqual(1, flat(section).count('state "Results look strong."'))


class TheAccuracyFigureIsDefinedOnce(unittest.TestCase):
    """#750: the figure the accuracy column routes on is defined once, and every site links it."""

    def setUp(self):
        self.texts = read_all()

    def test_the_definition_is_found(self):
        """⛔ INV-265: a scan of a moved definition certifies nothing."""
        self.assertIsNotNone(accuracy_definition(self.texts["phase_d"]))

    def test_step_22_defines_the_figure_and_what_routes(self):
        self.assertEqual([], run("definition", self.texts))

    def test_the_gate_and_the_table_header_link_it(self):
        self.assertEqual([], run("links", self.texts))

    def test_the_formula_is_stated_once_in_the_shipped_markdown(self):
        self.assertEqual([], stated_once_problems(shipped_markdown()))

    def test_the_link_resolves_to_the_anchor(self):
        text = self.texts["phase_d"]
        self.assertGreaterEqual(text.count(ACCURACY_LINK), 3)
        self.assertEqual(1, text.count(ACCURACY_ANCHOR))


class EachCheckSeesTheDefectItWasWrittenFor(unittest.TestCase):
    """Negative controls: the same checks, run on mutated copies, must each report a problem."""

    def setUp(self):
        self.texts = read_all()

    def mutated(self, key, old, new=""):
        self.assertIn(old, self.texts[key], "negative control is stale: %r is gone" % old[:60])
        texts = dict(self.texts)
        texts[key] = texts[key].replace(old, new, 1)
        return texts

    def test_the_gate_before_the_fix_fails(self):
        """The three UAT-only bands with no table: the shape #678 reported."""
        texts = dict(self.texts)
        section = gate(texts["phase_d"])
        start = section.index("**The table below is the whole of the routing")
        end = section.index("- **UAT ≥90% and match accuracy ≥90%:**")
        texts["phase_d"] = texts["phase_d"].replace(section[start:end], "", 1)
        self.assertTrue(run("table", texts))

    def test_removing_the_shortfall_row_leaves_a_pair_unrouted(self):
        texts = self.mutated("phase_d", "| ≥90% | <90% | Accuracy shortfall |\n")
        problems = run("table", texts)
        self.assertTrue(any("matches 0 rows" in p for p in problems), problems)

    def test_an_overlapping_row_is_reported(self):
        texts = self.mutated("phase_d", "| 80–89% | any | Results are mixed |",
                             "| 80–89% | any | Results are mixed |\n"
                             "| ≥90% | any | Results are mixed |")
        problems = run("table", texts)
        self.assertTrue(any("matches 2 rows" in p for p in problems), problems)

    def test_routing_the_shortfall_to_the_strong_branch_is_reported(self):
        texts = self.mutated("phase_d", "| ≥90% | <90% | Accuracy shortfall |",
                             "| ≥90% | <90% | Results look strong |")
        self.assertTrue(run("strong", texts))

    def test_a_cell_that_cannot_be_read_is_a_failure_not_a_skip(self):
        texts = self.mutated("phase_d", "| ≥90% | <90% | Accuracy shortfall |",
                             "| mostly fine | a bit low | Accuracy shortfall |")
        problems = run("table", texts)
        self.assertTrue(any("cannot be read as a band" in p for p in problems), problems)

    def test_dropping_the_never_strong_rule_is_reported(self):
        texts = self.mutated("phase_d", "⛔ **Never call a result strong when a metric the "
                             "strong branch explicitly requires falls short or\nwas never "
                             "established**", "The strong branch is for strong results.")
        self.assertTrue(run("strong", texts))

    def test_removing_the_shortfall_branch_is_reported(self):
        texts = self.mutated("phase_d", SHORTFALL_BULLET, "- **Something else:**")
        self.assertTrue(run("shortfall", texts))

    def test_a_shortfall_branch_without_its_recommendation_is_reported(self):
        texts = self.mutated(
            "phase_d", "**Recommendation — tune the match keys before the sign-off stands.**",
            "**Recommendation — none.**")
        self.assertTrue(run("shortfall", texts))

    def test_a_shortfall_branch_without_its_return_routes_is_reported(self):
        texts = self.mutated("phase_d", '`from_verdict: "%s"`' % BAND, "`from_verdict` unset")
        self.assertTrue(run("shortfall", texts))

    def test_a_shortfall_branch_that_calls_the_results_strong_is_reported(self):
        texts = self.mutated("phase_d", "**Recommendation — tune the match keys",
                             "Results look strong. **Recommendation — tune the match keys")
        self.assertTrue(run("shortfall", texts))

    def test_pooling_the_buckets_at_the_table_is_reported(self):
        texts = self.mutated("phase_d", "The accuracy column is the **per-record** figure",
                             "The accuracy column is the pooled figure")
        self.assertTrue(run("per_record", texts))

    def test_a_route_that_never_learns_the_band_is_reported(self):
        texts = self.mutated("phase_1", " | %s" % BAND, "")
        self.assertTrue(run("route", texts))

    def test_a_handling_step_that_drops_the_band_is_reported(self):
        texts = self.mutated("phase_d", ", or `%s` on the accuracy-shortfall\n     branch" % BAND,
                             "")
        self.assertTrue(run("route", texts))

    def test_a_resume_that_stops_re_running_phase_d_is_reported(self):
        texts = self.mutated("phase_d", "Phase D runs again in full, from step 21",
                             "Phase D is skipped")
        self.assertTrue(run("resume", texts))

    # --- #750: the accuracy figure's definition and its links

    def test_the_gate_before_the_definition_fails(self):
        """The shape #750 reported: the term used, routed on, and defined nowhere."""
        texts = dict(self.texts)
        definition = accuracy_definition(texts["phase_d"])
        texts["phase_d"] = texts["phase_d"].replace(definition, "", 1)
        problems = run("definition", texts)
        self.assertTrue(any("does not anchor" in p or "0 times" in p for p in problems), problems)

    def test_a_definition_without_its_denominator_is_reported(self):
        texts = self.mutated("phase_d", "\n÷ records reviewed**", "**")
        self.assertTrue(run("definition", texts))

    def test_a_definition_that_lets_recall_route_is_reported(self):
        """The reading the #750 guide nearly took: recall at 87.3% sending a clean run to the
        shortfall branch."""
        texts = self.mutated("phase_d", "They never route, and never replace or adjust this "
                             "figure,", "When recall is lower, route on recall instead,")
        self.assertTrue(run("definition", texts))

    def test_a_definition_that_estimates_without_ground_truth_is_reported(self):
        texts = self.mutated("phase_d", "With no ground truth, leave them out; never estimate "
                             "them.", "With no ground truth, estimate them from the sample.")
        self.assertTrue(run("definition", texts))

    def test_a_definition_with_no_none_case_is_reported(self):
        texts = self.mutated("phase_d", "If no record was reviewed, write that\ninstead",
                             "Always write a percentage")
        self.assertTrue(run("definition", texts))

    def test_an_unlinked_table_header_is_reported(self):
        texts = self.mutated("phase_d", TABLE_HEADER,
                             "| UAT % | Per-record match accuracy | Branch |")
        self.assertTrue(run("links", texts))

    def test_a_routing_sentence_without_the_link_is_reported(self):
        texts = self.mutated("phase_d", " and the per-record match accuracy from the same file "
                             "(step 22 →\n[per-record match accuracy](#per-record-match-accuracy))",
                             "")
        self.assertTrue(run("links", texts))

    def test_a_legend_without_the_link_is_reported(self):
        texts = self.mutated("phase_d", ": the [per-record match accuracy]"
                             "(#per-record-match-accuracy)\nstep 22 defines, never precision or "
                             "recall", "")
        self.assertTrue(run("links", texts))

    def test_a_restated_formula_is_reported(self):
        """INV-300: a second copy of the formula, anywhere in the shipped Markdown, fails."""
        corpus = shipped_markdown()
        name = PHASE_1.relative_to(REPO_ROOT).as_posix()
        corpus[name] += "\n\nMatch accuracy is %s.\n" % FORMULA
        problems = stated_once_problems(corpus)
        self.assertTrue(problems)
        self.assertIn(name, problems[0])

    def test_a_missing_formula_is_reported(self):
        corpus = shipped_markdown()
        name = PHASE_D.relative_to(REPO_ROOT).as_posix()
        corpus[name] = corpus[name].replace("÷ records reviewed", "÷ entities", 1)
        self.assertTrue(stated_once_problems(corpus))


class ReWrapping(unittest.TestCase):
    """INV-346: re-flowed to one word per line, the live text still passes every check."""

    def setUp(self):
        self.texts = {k: rewrap(v) for k, v in read_all().items()}

    def test_every_check_passes_on_rewrapped_text(self):
        for name in CHECKS:
            with self.subTest(check=name):
                self.assertEqual([], run(name, self.texts))


if __name__ == "__main__":
    unittest.main()
