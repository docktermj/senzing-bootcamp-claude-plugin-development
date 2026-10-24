"""Every pinned gate whose strong branch states a conjunction routes every combination of readings.

The iterate-vs-proceed gate in Module 6 Phase D required the UAT % **and** the match accuracy for
its success branch — "UAT ≥90% and match accuracy ≥90%" — and then branched on the UAT % alone for
every other outcome: "UAT 80–89%" and "UAT <80%". A bootcamper holding UAT 95% with match accuracy
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

**#776: one guard for every such gate, found by scanning.** Two gates still did not route every
combination. Phase D routed a UAT % that was never computed (`none`) by match accuracy alone, so a
Bootcamper with no spot-checkable entity heard "Results look strong" and the route was handed a UAT
band the run never measured. Module 5 Phase 2 step 16's strong branch was "Quality ≥80% **and** all
critical fields mapped" while its other branches routed on quality alone, so ≥80% with a critical
field unmapped reached no branch, and no branch covered a source with no quality score. Now:

* **Phase D** — the four `none` UAT rows route to "UAT not established", a branch of its own with
  its evidence, recommendation, pinned question and return routes, whose "Iterate now" hands the
  route `from_verdict: "uat_not_established"`, which the route's record shape and band table
  accept;
* **Module 5 step 16** — ONE decision table over the quality band (`≥80%`, `70–79%`, `<70%`,
  `none`) × the critical-field state (`all critical fields mapped`, `a critical field unmapped`,
  `not recorded`) names a branch key, and the next-source block and the loading block each map
  every key to their own pinned question; `not recorded` routes on the quality score alone but has
  a key of its own, so it is never read as "all critical fields mapped";
* **`critical_fields`** — Module 5 Phase 1 Step 4 records the source fields that correspond to the
  Entity Specification's critical attributes, read from the saved specification on every run (its
  *What features to map* table's Importance column) rather than from a list in the skill, and the
  field is defined once, with the registry's other fields, in Module 4 (INV-300, INV-080);
* **the guard** — `find_gates` scans every shipped Markdown file for a section holding a bold
  bullet label that joins two conditions with "and", one of them a percentage threshold, and
  `gate_problems` builds each gate's router from its own table: a column is numeric when its cells
  are bands, or categorical when the gate's legend declares its states (`**<column>** is one of …
  states: …`). It asserts exactly one branch per combination, including `none` and every declared
  state, and it tests the strong label on **both** axes: every combination routed to the strong
  branch must meet each of the label's conditions — a threshold the reading meets, or the exact
  state the label names. Phase D's and step 16's gates are pinned as a floor (INV-265), and a
  scan that finds no gate at all is a failure.

⛔ **The router is built from the shipped table, not from a copy of it here.** The bands are
parsed out of the table's own cells, and a categorical column's states out of the gate's own
legend, so the completeness and non-overlap checks cannot be satisfied by editing a specification
kept in this file. A cell whose text this file cannot read is a FAILURE, never a skip (INV-265):
an unparsed row is indistinguishable from a row that routes nothing.

⚠️ **Boundaries.** A gate's bands are read as its table's legend states them — a band runs up
to the next band's floor, so `80–89%` is 80 up to but not including 90. Each numeric axis is
therefore probed at the fractional readings either side of every boundary its cells name, as well
as the whole percentages, plus `None` for the reading that was never computed.

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

Source issues: #678, #750, #776. Invariants: INV-056, INV-080, INV-117, INV-264, INV-265,
INV-284, INV-300, INV-346, INV-400, INV-404.

INV-404 (a gate whose outcome states a conjunction of conditions routes every combination of its
readings to exactly one branch, and a failed required condition gets a branch of its own) names
this file as its enforcer: the router built from each scanned gate's shipped table and its
negative controls are what it relies on. They establish that each table is total and
non-overlapping as written; they do not establish that a live guide routes a reading by it, which
only `dry-run` phase 3 observes.

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
from collections import namedtuple
from pathlib import Path

from _corpus import corpus_files

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "senzing-bootcamp" / "skills"
PHASE_D = SKILLS / "module-06-data-processing" / "phaseD-validation.md"
PHASE_1 = SKILLS / "module-07-query-visualize-discover" / "phase1-query-visualize.md"
M5_PHASE_1 = SKILLS / "module-05-data-quality-mapping" / "phase1-quality-assessment.md"
M5_PHASE_2 = SKILLS / "module-05-data-quality-mapping" / "phase2-data-mapping.md"
M4_SKILL = SKILLS / "module-04-data-collection" / "SKILL.md"

GATE_HEADING = "## Iterate vs. proceed decision gate"
GATE_END = "## Stakeholder summary"
SHORTFALL_BULLET = "- **UAT ≥90% but match accuracy <90% — the accuracy shortfall:**"
UAT_NOT_BULLET = "- **No UAT % — UAT not established:**"
BAND = "uat_90_accuracy_below_90"
UAT_NOT_BAND = "uat_not_established"

STEP_16 = "### 16. Review"
STEP_17 = "### 17. Iterate"
WHILE_REMAINING = "**While one or more unmapped sources remain**"
NONE_REMAINING = "**When no unmapped source remains**"
BLOCKS_END = "*(Internal: end the turn on the applicable question and wait.)*"

#: The gates the scan must find, by repo-relative path and section heading: a floor (INV-265).
PINNED_GATES = (
    (PHASE_D.relative_to(REPO_ROOT).as_posix(), GATE_HEADING),
    (M5_PHASE_2.relative_to(REPO_ROOT).as_posix(), STEP_16),
)

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
UAT_NOT = "UAT not established"

#: Module 5 step 16's branch keys, as its table names them.
M5_STRONG = "Quality ≥80% and all critical fields mapped"
M5_NOT_RECORDED = "Quality ≥80%, critical fields not recorded"
M5_UNMAPPED = "Quality ≥80% with a critical field unmapped"
M5_ACCEPTABLE = "Quality 70-79%"
M5_IMPROVE = "Quality <70%"
M5_NO_SCORE = "No quality score"
ALL_MAPPED = "all critical fields mapped"
UNMAPPED = "a critical field unmapped"
NOT_RECORDED = "not recorded"

#: #776: the one definition of `critical_fields`, and the link to it.
CRITICAL_ANCHOR = '<a id="critical-fields"></a>'
CRITICAL_LINK = "../module-04-data-collection/SKILL.md#critical-fields"
CRITICAL_DEFINITION = "`critical_fields` (optional) is a list of this source's field names"


def plain(text):
    return text.replace("**", "")


def flat(text):
    return re.sub(r"\s+", " ", plain(text)).strip()


def unquote(text):
    """The text with one level of blockquote marker taken off each line."""
    return re.sub(r"(?m)^[ \t]*>[ \t]?", "", text)


def squash(text):
    """Whitespace collapsed, emphasis kept (INV-346)."""
    return re.sub(r"\s+", " ", text).strip()


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


def step16(text):
    """Module 5 Phase 2 step 16, or None when its heading moved."""
    if STEP_16 not in text or STEP_17 not in text:
        return None
    start = text.index(STEP_16)
    return text[start:text.index(STEP_17, start)]


# ------------------------------------------------------------ reading a shipped decision table


class UnreadableCell(Exception):
    """A table cell this file cannot turn into a band. ⛔ Never swallowed (INV-265)."""


def band(cell):
    """The predicate a numeric table cell states, over a reading that is a number or None.

    ⚠️ The bands come from the cells themselves. Nothing here hardcodes which bands a gate
    has, so a band added, removed or renamed in a shipped table is read as written — or, if
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


def is_band(cell):
    """True for a cell that names a band or `none` (not `any`)."""
    if plain(cell).strip() == "any":
        return False
    try:
        band(cell)
    except UnreadableCell:
        return False
    return True


def boundaries(cell):
    """The band edges a numeric cell names."""
    cell = plain(cell).strip()
    m = re.fullmatch(r"[≥<](\d+)%", cell)
    if m:
        return [float(m.group(1))]
    m = re.fullmatch(r"(\d+)[–-](\d+)%", cell)
    if m:
        return [float(m.group(1)), float(m.group(2)) + 1]
    return []


def split_row(line):
    line = line.strip()
    if not line.startswith("|"):
        return None
    return [c.strip() for c in line.strip("|").split("|")]


def unlink(text):
    """A header cell's text with any Markdown link reduced to its label."""
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).strip()


Table = namedtuple("Table", "columns rows")
Gate = namedtuple("Gate", "path heading body labels")
Axis = namedtuple("Axis", "name kind readings")


def decision_table(body):
    """The section's decision table — the one whose last header cell is `Branch` — or None."""
    lines = body.split("\n")
    for i, line in enumerate(lines):
        header = split_row(line)
        if not header or len(header) < 2 or header[-1] != "Branch":
            continue
        rows = []
        for row_line in lines[i + 1:]:
            row = split_row(row_line)
            if row is None:
                break
            if set("".join(row)) <= set("-: "):
                continue
            rows.append(tuple(row))
        return Table(tuple(unlink(c) for c in header[:-1]), rows)
    return None


#: A legend line declaring a categorical column's states: **<column>** is one of … states: `a`, `b`.
STATES = re.compile(r"\*\*(?P<col>[^*]+)\*\* is one of (?:\w+ )?states: (?P<states>[^.]*)\.")


def declared_states(body):
    """`{column name, lower case: [state, …]}` from the section's legend."""
    out = {}
    for m in STATES.finditer(squash(body)):
        out[m.group("col").strip().lower()] = re.findall(r"`([^`]+)`", m.group("states"))
    return out


def axes(body, table):
    """One Axis per metric column, its readings drawn from the table's cells and the legend.

    ⛔ A categorical column's states come from the legend, never from the rows: a state whose only
    row was deleted must still be probed, so its combinations are reported as unrouted.
    """
    states = declared_states(body)
    out, problems = [], []
    for j, name in enumerate(table.columns):
        cells = [row[j] for row in table.rows if len(row) == len(table.columns) + 1]
        if any(is_band(c) for c in cells):
            edges = {e for c in cells if is_band(c) for e in boundaries(c)}
            grid = {0.0, 50.0, 100.0}
            for e in edges:
                grid |= {e - 1, e - 0.5, e, e + 0.5}
            out.append(Axis(name, "numeric", [None] + sorted(grid)))
        elif name.lower() in states and states[name.lower()]:
            out.append(Axis(name, "categorical", states[name.lower()]))
        else:
            problems.append("column %r is neither banded nor declared by the legend "
                            "(\"**%s** is one of … states: …\")" % (name, name))
    return out, problems


def matches(axis, cell, reading):
    """Whether a table cell admits a reading on an axis. ⛔ Raises on an unreadable cell."""
    if plain(cell).strip() == "any":
        return True
    if axis.kind == "numeric":
        return band(cell)(reading)
    if cell not in axis.readings:
        raise UnreadableCell("%s (not a state the legend declares for %r)" % (cell, axis.name))
    return cell == reading


def route(table, axes_, readings):
    """Every branch whose row admits this combination of readings."""
    return [row[-1] for row in table.rows
            if all(matches(a, cell, r) for a, cell, r in zip(axes_, row, readings))]


# --------------------------------------------------------------------------- finding the gates


HEADING = re.compile(r"(?m)^#{1,6} .*$")
#: A bold bullet label, on whitespace-collapsed text: `- **<label>:**` or `- **<label>** …`.
LABEL = re.compile(r"(?:^| )- \*\*([^*]+?)\*\*")
THRESHOLD = re.compile(r"≥\d+%|<\d+%|\d+[–-]\d+%")


def sections(text):
    """[(heading, body)] for every heading in the text, each up to the next heading."""
    marks = list(HEADING.finditer(text))
    return [(m.group(0).strip(),
             text[m.start():marks[i + 1].start() if i + 1 < len(marks) else len(text)])
            for i, m in enumerate(marks)]


def conjunctive_labels(body):
    """Each distinct bold bullet label that joins conditions with "and", one a threshold."""
    labels = []
    for m in LABEL.finditer(squash(body)):
        label = m.group(1).strip().rstrip(":").strip()
        if " and " in label and THRESHOLD.search(label) and label not in labels:
            labels.append(label)
    return labels


def find_gates(corpus):
    """Every section of every file in `corpus` (`{path: text}`) that holds a conjunctive label."""
    found = []
    for path, text in sorted(corpus.items()):
        for heading, body in sections(text):
            labels = conjunctive_labels(body)
            if labels:
                found.append(Gate(path, heading, body, labels))
    return found


def strong_branch(gate_, table, label):
    """The table branch the strong label states: the label itself, or the one its bullet names."""
    branches = sorted({row[-1] for row in table.rows})
    if label in branches:
        return label, []
    text = squash(gate_.body)
    at = text.find("- **%s" % label)
    body = text[at:]
    nxt = body.find("- **", 4)
    body = (body[:nxt] if nxt > 0 else body).lower()
    named = [b for b in branches if b.lower() in body]
    if len(named) != 1:
        return None, ["the strong label %r names %d of the table's branches, not one (%s)"
                      % (label, len(named), ", ".join(named) or "none")]
    return named[0], []


def words(text):
    return set(re.findall(r"[a-z]{3,}", unlink(text).lower())) - {"and", "the", "all"}


def conditions(label, axes_):
    """[(axis, predicate)] — the strong label's conditions, one per column, in column order."""
    parts = [p.strip() for p in label.split(" and ")]
    if len(parts) != len(axes_):
        return None, ["the strong label %r states %d conditions over %d columns"
                      % (label, len(parts), len(axes_))]
    out, problems = [], []
    for part, axis in zip(parts, axes_):
        if not words(part) & words(axis.name):
            problems.append("the strong label's condition %r does not name column %r"
                            % (part, axis.name))
        threshold = THRESHOLD.search(part)
        if axis.kind == "numeric":
            if threshold is None:
                problems.append("the condition %r states no threshold for the banded column %r"
                                % (part, axis.name))
                continue
            out.append((axis, band(threshold.group(0))))
        else:
            if part not in axis.readings:
                problems.append("the condition %r is not a state the legend declares for %r"
                                % (part, axis.name))
                continue
            out.append((axis, lambda value, part=part: value == part))
    return out, problems


def gate_problems(gate_):
    """Total, non-overlapping, every branch stated, and the strong branch met on every axis."""
    where = "%s → %s" % (gate_.path, gate_.heading)
    table = decision_table(gate_.body)
    if table is None or not table.rows:
        return ["%s: the gate has no decision table" % where]
    problems = ["%s: a row has %d cells, not %d: %r" % (where, len(r), len(table.columns) + 1, r)
                for r in table.rows if len(r) != len(table.columns) + 1]
    axes_, axis_problems = axes(gate_.body, table)
    problems += ["%s: %s" % (where, p) for p in axis_problems]
    if problems:
        return problems
    combos = list(itertools.product(*(a.readings for a in axes_)))
    try:
        routed = {combo: route(table, axes_, combo) for combo in combos}
    except UnreadableCell as unreadable:
        return ["%s: a decision-table cell cannot be read as a band: %s" % (where, unreadable)]
    for combo, hits in routed.items():
        if len(hits) != 1:
            problems.append("%s: %r matches %d rows (%s)"
                            % (where, combo, len(hits), ", ".join(hits) or "none"))
    prose = flat("\n".join(line for line in gate_.body.split("\n")
                           if not line.strip().startswith("|"))).lower()
    for branch in sorted({row[-1] for row in table.rows}):
        if flat(branch).lower() not in prose:
            problems.append("%s: the table routes to %r and no branch below states it"
                            % (where, branch))
    for label in gate_.labels:
        strong, why = strong_branch(gate_, table, label)
        problems += ["%s: %s" % (where, p) for p in why]
        needed, why = conditions(label, axes_)
        problems += ["%s: %s" % (where, p) for p in why]
        if strong is None or needed is None:
            continue
        for combo, hits in routed.items():
            if strong not in hits:
                continue
            for axis, holds in needed:
                reading = combo[axes_.index(axis)]
                if not holds(reading):
                    problems.append("%s: %s %r is routed to %r" % (where, axis.name, reading,
                                                                   strong))
    return sorted(set(problems))[:16]


def scan_problems(corpus):
    """The scan finds a gate, finds every pinned one, and every gate it finds is total."""
    found = find_gates(corpus)
    if not found:
        return ["the scan found no pinned gate whose strong label joins two conditions with "
                "\"and\" (INV-265)"]
    problems = []
    keys = {(g.path, g.heading) for g in found}
    for path, heading in PINNED_GATES:
        if path in corpus and (path, heading) not in keys:
            problems.append("the scan no longer finds the gate %s → %s" % (path, heading))
    missing = [p for p, _h in PINNED_GATES if p not in corpus]
    if missing:
        problems.append("the scanned corpus is missing %s" % ", ".join(missing))
    for g in found:
        problems += gate_problems(g)
    return problems


def gate_in(path, text, heading):
    """The scanned gate at `heading` in one file, or None."""
    for g in find_gates({path: text}):
        if g.heading == heading:
            return g
    return None


def phase_d_gate(text):
    return gate_in(PINNED_GATES[0][0], text, GATE_HEADING)


def step16_gate(text):
    return gate_in(PINNED_GATES[1][0], text, STEP_16)


def routes(g, *readings):
    """Phase D's or step 16's branches for one combination of readings."""
    table = decision_table(g.body)
    axes_, problems = axes(g.body, table)
    assert not problems, problems
    return route(table, axes_, readings)


# ------------------------------------------------------------------------------ Phase D checks


def table_problems(text):
    """Phase D's table is total, every branch is stated, and its legend links the figure."""
    g = phase_d_gate(text)
    if g is None:
        return ["the scan does not find Phase D's gate"]
    return gate_problems(g)


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


def uat_not_problems(text):
    """#776: "UAT not established" states evidence, recommendation, its question and routes."""
    section = gate(text)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    opening = find(section, UAT_NOT_BULLET)
    if opening is None:
        return ["the gate has no UAT-not-established branch"]
    closing = find(section, "The gate question, asked word for word", opening.end())
    if closing is None:
        return ["the UAT-not-established branch is not followed by the gate question"]
    branch = flat(plain(section)[opening.start():closing.start()])
    needed = (
        "a branch of its own, whatever the per-record match accuracy reads",
        "It is not the strong branch",
        "it is not a branch named for a UAT band",
        # the evidence: no entity spot-checked, why, and the accuracy reported as a finding
        "Evidence — the missing UAT %, and why",
        "with the reason `docs/uat_results.md` records",
        "The per-record match accuracy is reported as a finding",
        "it does not route here",
        "When it was never established either, name both as not established",
        "neither moves this branch nor blocks it (INV-117, INV-264)",
        # the recommendation
        "Recommendation — establish the UAT % before treating the results as strong",
        # its own pinned question, numbered (INV-056, INV-051)
        "Next question — this branch's own",
        "👉 **No entity could be spot-checked, so these results have no UAT %. What would you "
        "like to do? Reply with a number:**",
        "1. Iterate now to establish the UAT % before moving on. *(recommended)*",
        "2. Move forward to the next module without it.",
        "*(Internal: end the turn on this question and wait.)*",
        # the accepted and declined return routes
        "Accepted and declined — the handling step below",
        '"Iterate now" is the accepted route',
        '`from_verdict: "%s"`' % UAT_NOT_BAND,
        "step 22 spot-checks again",
        '"Move forward" is the declined route',
        "accepted with no UAT % established",
    )
    problems = ["the UAT-not-established branch does not say %r" % phrase
                for phrase in needed if flat(phrase) not in branch]
    if flat("Results look strong") in branch:
        problems.append("the UAT-not-established branch states the strong label")
    if flat("route on match accuracy alone") in flat(section) and \
            flat("never\nroute on match accuracy alone") not in flat(section):
        problems.append("the gate still routes a missing UAT % on match accuracy alone")
    if flat("take the UAT-not-established branch, by the `none` rows of the table below") \
            not in flat(section):
        problems.append("the no-UAT sentence does not send a missing UAT % to its branch")
    return problems


def strong_label_problems(text):
    """The strong label is never reachable with a required metric short or missing."""
    section = gate(text)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    problems = []
    rule = ("⛔ **(INV-404) Never call a result strong when a metric the strong branch explicitly "
            "requires falls short or was never established**")
    if flat(rule) not in flat(section):
        problems.append("the gate does not forbid the strong label where a required metric fails")
    g = phase_d_gate(text)
    if g is None:
        return problems + ["the scan does not find Phase D's gate"]
    return problems + [p for p in gate_problems(g) if "is routed to" in p or "strong label" in p
                       or "condition" in p or "decision table" in p or "cannot be read" in p]


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
    """The Phase D bands reach the one canonical statement of the quality-iteration route."""
    problems = []
    if flat("(`uat_80_89`, `uat_below_80`, `%s` on the accuracy-shortfall branch, or `%s` on "
            "the UAT-not-established branch)" % (BAND, UAT_NOT_BAND)) not in flat(phase_d):
        problems.append("Phase D's handling step does not hand the route both new bands")
    for phrase in (
            '"from_verdict": "poor | marginal | uat_below_80 | uat_80_89 | %s | %s"'
            % (BAND, UAT_NOT_BAND),
            "`uat_below_80`, `uat_80_89`, `%s` or `%s`" % (BAND, UAT_NOT_BAND),
    ):
        if flat(phrase) not in flat(phase_1):
            problems.append("the quality-iteration route does not record %r" % phrase)
    # INV-300: Phase D hands the route a band; it does not restate the route or the record.
    if '"quality_iteration": {' in phase_d:
        problems.append("Phase D restates the quality_iteration key")
    return problems


def resume_problems(phase_d):
    """The iterate/resume behavior the new branches reuse is unchanged."""
    section = gate(phase_d)
    if section is None:
        return ["Phase D has no iterate-vs-proceed gate"]
    section = flat(section)
    return ["the gate's handling step no longer says %r" % phrase for phrase in (
        '`return_to: "module_6_phase_d"`',
        "Phase D runs again in full, from step 21",
        "this gate is asked again on the new results",
        "With one, ask nothing and use it",
        "These entries serve the gate question and the UAT-not-established question alike",
    ) if flat(phrase) not in section]


# ------------------------------------------------------------------------- Module 5 checks


def step16_table_problems(text):
    """Step 16's one decision table is total, and the strong branch needs both conditions."""
    g = step16_gate(text)
    if g is None:
        return ["the scan does not find step 16's gate"]
    problems = gate_problems(g)
    section = flat(g.body)
    for phrase in (
            "Route on the quality score and the critical fields (INV-404)",
            "the table below is the whole of the routing, for both blocks",
            "each block asks that branch's own question",
            "`none` means step 15 produced no score, which is said as exactly that and never "
            "given a band",
            "[`critical_fields`](%s)" % CRITICAL_LINK,
            "An empty list is `all critical fields mapped`",
            "say so in one line and route on the quality score alone, never as a critical field "
            "unmapped",
            "A band runs up to the next band's floor",
    ):
        if flat(phrase) not in section:
            problems.append("step 16 does not say %r" % phrase)
    return problems


def blocks(text):
    """(next-source block, loading block) of step 16, or None."""
    s16 = step16(text)
    s16 = squash(s16) if s16 is not None else None
    if s16 is None or any(squash(m) not in s16 for m in (WHILE_REMAINING, NONE_REMAINING,
                                                         BLOCKS_END)):
        return None
    w, n = s16.index(squash(WHILE_REMAINING)), s16.index(squash(NONE_REMAINING))
    return s16[w:n], s16[n:s16.index(squash(BLOCKS_END))]


#: Each block's own question for the two new branches (INV-056), with its options.
NEW_QUESTIONS = {
    "next source": {
        M5_UNMAPPED: ("👉 **{source} scores [score], but these critical fields are not mapped: "
                      "[unmapped critical fields]. What would you like to do? Reply with a "
                      "number:**", ("1. Iterate to map them first.",
                                    "2. Move on to {next} without them.")),
        M5_NO_SCORE: ("👉 **The quality analysis produced no score for {source}, so I can't say "
                      "how ready it is. What would you like to do? Reply with a number:**",
                      ("1. Iterate on {source} to get a quality score first.",
                       "2. Move on to {next} without one.")),
    },
    "loading": {
        M5_UNMAPPED: ("👉 **The quality score is [score], but these critical fields are not "
                      "mapped: [unmapped critical fields]. What would you like to do? Reply with "
                      "a number:**", ("1. Iterate to map them first.",
                                      "2. Proceed to loading without them.")),
        M5_NO_SCORE: ("👉 **The quality analysis produced no score, so I can't say how ready the "
                      "mapping is. What would you like to do? Reply with a number:**",
                      ("1. Iterate to get a quality score first.",
                       "2. Proceed to loading without one.")),
    },
}


def step16_block_problems(text):
    """Both blocks give every branch of the one table a bullet, and the new ones their question."""
    found = blocks(text)
    if found is None:
        return ["step 16's two blocks moved"]
    g = step16_gate(text)
    table = decision_table(g.body) if g else None
    if table is None:
        return ["step 16 has no decision table"]
    problems = []
    for (name, block) in zip(("next source", "loading"), found):
        squashed = squash(block)
        for branch in sorted({row[-1] for row in table.rows}):
            if "- **%s" % branch not in squashed:
                problems.append("the %s block has no bullet for the branch %r" % (name, branch))
        for branch, (question, options) in NEW_QUESTIONS[name].items():
            at = squashed.find("- **%s" % branch)
            if at < 0:
                continue
            body = squashed[at:]
            nxt = body.find("- **", 4)
            body = body[:nxt] if nxt > 0 else body
            if squash(question) not in body:
                problems.append("the %s block's %r branch does not ask its pinned question"
                                % (name, branch))
            problems += ["the %s block's %r branch lost its option %r" % (name, branch, o)
                         for o in options if o not in body]
        nr = squashed.find("- **%s:**" % M5_NOT_RECORDED)
        if nr >= 0 and squash("say in one line that this source's critical fields were not "
                              "recorded, so this gate routes on its quality score alone, then "
                              "ask the question above word for word") not in squashed[nr:]:
            problems.append("the %s block's not-recorded branch does not say so and route on "
                            "the score alone" % name)
        ns = squashed.find("- **%s:**" % M5_NO_SCORE)
        if ns >= 0 and squash("and state no band") not in squashed[ns:]:
            problems.append("the %s block's no-score branch does not refuse a band" % name)
    return problems


def critical_fields_problems(m4, m5_phase_1, m5_phase_2):
    """`critical_fields`: defined once in Module 4, written by Phase 1 Step 4, read by step 16."""
    problems = []
    m4 = squash(unquote(m4))
    if m4.count(CRITICAL_ANCHOR) != 1:
        problems.append("Module 4 anchors critical_fields %d times, not once"
                        % m4.count(CRITICAL_ANCHOR))
    at = m4.find(CRITICAL_ANCHOR)
    definition = flat(m4[at:m4.find("`scenario_intent` (optional", at)]) if at >= 0 else ""
    for phrase in (CRITICAL_DEFINITION,
                   "an empty list when the source carries none",
                   "Module 5 writes it for every source it compares, at Step 4",
                   "This note is the one definition of the field (INV-300)",
                   "its critical fields are **not recorded**, which is not the same as an empty "
                   "list"):
        if flat(phrase) not in definition:
            problems.append("the critical_fields definition does not say %r" % phrase)
    start, end = m5_phase_1.find("## 4. Compare"), m5_phase_1.find("## 5. Categorize")
    if start < 0 or end < 0:
        return problems + ["Module 5 Phase 1 Step 4 moved"]
    step4 = squash(m5_phase_1[start:end])
    at = step4.find("- **Record the source's critical fields.**")
    stop = step4.find("**Checkpoint:** write step 4.", at)
    if at < 0 or stop < 0:
        return problems + ["Phase 1 Step 4 does not record the source's critical fields"]
    bullet = step4[at:stop]   # the step's last bullet, up to its checkpoint
    for phrase in (
            "*What features to map* table ranks **High** or higher in its Importance column",
            "Read that ranking from the saved copy at "
            "`docs/reference/senzing_entity_specification.md` (Step 3) on every run, never from "
            "a list kept in this file (INV-080)",
            "as the source's `critical_fields` in `config/data_sources.yaml`, with `updated_at`",
            "an empty list when the source carries none",
            "[`critical_fields`](%s) (INV-300)" % CRITICAL_LINK,
    ):
        if flat(phrase) not in flat(bullet):
            problems.append("Phase 1 Step 4 does not say %r" % phrase)
    # INV-080: the critical attributes are read at run time, so the step names none of them.
    named = sorted(set(re.findall(r"\b[A-Z][A-Z_]{2,}\b(?!\.md)", bullet)) - {"INV"})
    if named:
        problems.append("Phase 1 Step 4 restates attributes as critical: %s" % ", ".join(named))
    if CRITICAL_LINK not in m5_phase_2:
        problems.append("step 16 does not link the critical_fields definition")
    return problems


def critical_defined_once_problems(corpus):
    """INV-300: the field is defined in one shipped Markdown file."""
    hits = sorted(name for name, text in corpus.items()
                  if flat(CRITICAL_DEFINITION) in flat(text))
    if len(hits) != 1:
        return ["critical_fields is defined in %d files: %s" % (len(hits), ", ".join(hits)
                                                                 or "none")]
    return []


# ----------------------------------------------------------------------- #750: the definition


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


#: #809: the steps that judge match accuracy before the gate, by heading and end marker.
STEP_21 = ("## 21. ", "## 22. ")
STEP_24 = ("## 24. ", "**Checkpoint:** write step 24.")


def step_span(text, bounds):
    """The text from a step's heading to its end marker, or None when either moved.

    The end marker is matched across wraps (INV-346), as `accuracy_definition` matches its own.
    """
    start, end = bounds
    if start not in text:
        return None
    i = text.index(start)
    j = re.compile(r"\s+".join(map(re.escape, end.split()))).search(text, i + len(start))
    return None if j is None else text[i:j.start()]


def step_link_problems(text):
    """Steps 21 and 24 link the figure they judge; step 24 reads precision/recall as support only.

    INV-400: step 22 defines the one accuracy figure. Steps 21 and 24 judged "match accuracy"
    without linking it, and step 24 sent the guide to `reporting_guide(topic='quality')` "for
    precision/recall metrics" beside it, which reads as a second accuracy measure.
    """
    problems = []
    step21 = step_span(text, STEP_21)
    if step21 is None:
        problems.append("step 21 moved")
    else:
        bullet = find(step21, "- If match accuracy is poor")
        tail = plain(step21)[bullet.start():] if bullet else ""
        if bullet is None or ACCURACY_LINK not in tail.split("\n\n")[0]:
            problems.append("step 21's accuracy bullet does not link the per-record figure")
    step24 = step_span(text, STEP_24)
    if step24 is None:
        return problems + ["step 24 moved"]
    body = flat(step24)
    if flat("Validate: match accuracy, which is the [per-record match accuracy]%s step 22 "
            "defines" % ACCURACY_LINK) not in body:
        problems.append("step 24 does not name the per-record figure as the accuracy it validates")
    if "for precision/recall metrics" in body:
        problems.append("step 24 still offers precision/recall as accuracy metrics")
    if "Pairwise precision and recall" not in body or "supporting reading only" not in body:
        problems.append("step 24 does not read precision and recall as supporting reading only")
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


def gates_corpus(texts):
    """The two pinned gates' files, as the scan reads them."""
    return {PINNED_GATES[0][0]: texts["phase_d"], PINNED_GATES[1][0]: texts["m5_phase_2"]}


CHECKS = {
    "definition": (definition_problems, ("phase_d",)),
    "links": (link_problems, ("phase_d",)),
    "step_links": (step_link_problems, ("phase_d",)),
    "table": (table_problems, ("phase_d",)),
    "shortfall": (shortfall_problems, ("phase_d",)),
    "uat_not": (uat_not_problems, ("phase_d",)),
    "strong": (strong_label_problems, ("phase_d",)),
    "per_record": (per_record_problems, ("phase_d",)),
    "route": (route_problems, ("phase_d", "phase_1")),
    "resume": (resume_problems, ("phase_d",)),
    "step16_table": (step16_table_problems, ("m5_phase_2",)),
    "step16_blocks": (step16_block_problems, ("m5_phase_2",)),
    "critical_fields": (critical_fields_problems, ("m4", "m5_phase_1", "m5_phase_2")),
    "scan": (lambda *t: scan_problems(dict(zip((PINNED_GATES[0][0], PINNED_GATES[1][0]), t))),
             ("phase_d", "m5_phase_2")),
}


def run(name, texts):
    fn, keys = CHECKS[name]
    return fn(*(texts[k] for k in keys))


def read_all():
    return {"phase_d": read(PHASE_D), "phase_1": read(PHASE_1), "m5_phase_1": read(M5_PHASE_1),
            "m5_phase_2": read(M5_PHASE_2), "m4": read(M4_SKILL)}


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


# ----------------------------------------------------------------------------------- the files


class EveryConjunctiveGateIsFoundAndRoutesEveryCombination(unittest.TestCase):
    """#776: the scan over the shipped Markdown, and the floor it must reach."""

    def test_the_scan_finds_the_pinned_gates_and_every_gate_is_total(self):
        self.assertEqual([], scan_problems(shipped_markdown()))

    def test_the_scan_finds_at_least_the_floor(self):
        """⛔ INV-265: a scan that finds nothing certifies nothing."""
        keys = {(g.path, g.heading) for g in find_gates(shipped_markdown())}
        for pinned in PINNED_GATES:
            self.assertIn(pinned, keys)


class TheShippedGateRoutesEveryPairOfReadings(unittest.TestCase):
    def setUp(self):
        self.texts = read_all()
        self.gate = phase_d_gate(self.texts["phase_d"])

    def test_the_gate_is_found(self):
        """⛔ INV-265: a scan of a moved section certifies nothing."""
        self.assertIsNotNone(gate(self.texts["phase_d"]))
        self.assertIsNotNone(self.gate)
        self.assertTrue(decision_table(self.gate.body).rows, "the decision table is missing")

    def test_every_pair_of_readings_matches_exactly_one_row(self):
        self.assertEqual([], run("table", self.texts))

    def test_the_reported_case_routes_to_the_new_branch(self):
        """#678's own case: UAT 95% with match accuracy 70% matched no branch at all."""
        self.assertEqual([SHORTFALL], routes(self.gate, 95, 70))

    def test_the_boundary_readings_route_as_the_bands_state(self):
        for uat, accuracy, expected in (
                (90, 90, STRONG), (90, 89.5, SHORTFALL), (90, 89, SHORTFALL),
                (100, 90, STRONG), (89.5, 100, MIXED), (89, 100, MIXED),
                (80, 0, MIXED), (79.5, 100, IMPROVE), (79, 100, IMPROVE),
                (95, None, SHORTFALL), (None, 95, UAT_NOT), (None, 85, UAT_NOT),
                (None, 79, UAT_NOT), (None, None, UAT_NOT)):
            with self.subTest(uat=uat, accuracy=accuracy):
                self.assertEqual([expected], routes(self.gate, uat, accuracy))

    def test_the_accuracy_shortfall_branch_states_everything_a_branch_states(self):
        self.assertEqual([], run("shortfall", self.texts))

    def test_the_uat_not_established_branch_states_everything_a_branch_states(self):
        self.assertEqual([], run("uat_not", self.texts))

    def test_a_result_is_never_strong_with_either_condition_failing(self):
        self.assertEqual([], run("strong", self.texts))

    def test_accuracy_routes_on_the_per_record_bucket_only(self):
        self.assertEqual([], run("per_record", self.texts))

    def test_the_new_bands_reach_the_quality_iteration_route(self):
        self.assertEqual([], run("route", self.texts))

    def test_the_iterate_and_resume_behavior_is_preserved(self):
        self.assertEqual([], run("resume", self.texts))

    def test_the_strong_statement_is_pinned_to_its_own_branch(self):
        """One branch states "Results look strong." — the one with both figures."""
        section = gate(self.texts["phase_d"])
        self.assertEqual(1, flat(section).count('state "Results look strong."'))


class Step16RoutesEveryBandAndCriticalFieldState(unittest.TestCase):
    """#776: Module 5 step 16's one table, its two blocks, and the field it reads."""

    def setUp(self):
        self.texts = read_all()
        self.gate = step16_gate(self.texts["m5_phase_2"])

    def test_the_gate_is_found(self):
        """⛔ INV-265: a scan of a moved step certifies nothing."""
        self.assertIsNotNone(self.gate)
        self.assertTrue(decision_table(self.gate.body).rows, "the decision table is missing")

    def test_every_combination_matches_exactly_one_row(self):
        self.assertEqual([], run("step16_table", self.texts))

    def test_the_readings_route_as_the_issue_states(self):
        for quality, critical, expected in (
                (85, ALL_MAPPED, M5_STRONG), (80, ALL_MAPPED, M5_STRONG),
                (85, UNMAPPED, M5_UNMAPPED), (100, UNMAPPED, M5_UNMAPPED),
                (85, NOT_RECORDED, M5_NOT_RECORDED), (79.5, ALL_MAPPED, M5_ACCEPTABLE),
                (70, UNMAPPED, M5_ACCEPTABLE), (79, NOT_RECORDED, M5_ACCEPTABLE),
                (69.5, ALL_MAPPED, M5_IMPROVE), (0, UNMAPPED, M5_IMPROVE),
                (None, ALL_MAPPED, M5_NO_SCORE), (None, UNMAPPED, M5_NO_SCORE),
                (None, NOT_RECORDED, M5_NO_SCORE)):
            with self.subTest(quality=quality, critical=critical):
                self.assertEqual([expected], routes(self.gate, quality, critical))

    def test_both_blocks_ask_every_branch(self):
        self.assertEqual([], run("step16_blocks", self.texts))

    def test_critical_fields_is_recorded_and_defined_once(self):
        self.assertEqual([], run("critical_fields", self.texts))
        self.assertEqual([], critical_defined_once_problems(shipped_markdown()))


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

    def test_steps_21_and_24_link_the_figure_they_judge(self):
        """#809: each step that judges accuracy names the one figure, by link."""
        self.assertEqual([], run("step_links", self.texts))

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

    # --- the scan (#776)

    def test_a_scan_that_finds_no_gate_fails(self):
        """⛔ INV-265: an empty corpus, and one whose labels lost their "and", both fail."""
        self.assertTrue(scan_problems({}))
        corpus = gates_corpus(self.texts)
        stripped = {k: v.replace("≥90% and match", "≥90% with match")
                    .replace("≥80% and all", "≥80% with all") for k, v in corpus.items()}
        self.assertNotEqual(corpus, stripped, "negative control is stale")
        self.assertTrue(any("found no pinned gate" in p for p in scan_problems(stripped)))

    def test_a_scan_that_loses_a_pinned_gate_fails(self):
        texts = dict(self.texts)
        texts["m5_phase_2"] = texts["m5_phase_2"].replace(
            "- **Quality ≥80% and all critical fields mapped:**",
            "- **Quality ≥80% with all critical fields mapped:**")
        self.assertNotEqual(texts, self.texts, "negative control is stale")
        problems = run("scan", texts)
        self.assertTrue(any("no longer finds the gate" in p for p in problems), problems)

    def test_a_scanned_gate_with_no_table_fails(self):
        """A third conjunctive gate the scan finds, with no table, is reported (not exempted)."""
        corpus = gates_corpus(self.texts)
        corpus["plugins/x.md"] = ("## A gate\n\n- **Score ≥50% and all checks passed:** go on.\n"
                                  "- **Anything else:** stop.\n")
        problems = scan_problems(corpus)
        self.assertTrue(any("plugins/x.md" in p and "no decision table" in p for p in problems),
                        problems)

    # --- Phase D

    def test_the_gate_before_the_fix_fails(self):
        """The three UAT-only bands with no table: the shape #678 reported."""
        texts = dict(self.texts)
        section = gate(texts["phase_d"])
        start = section.index("**The table below is the whole of the routing")
        end = section.index("- **UAT ≥90% and match accuracy ≥90%:**")
        texts["phase_d"] = texts["phase_d"].replace(section[start:end], "", 1)
        self.assertTrue(run("table", texts))
        self.assertTrue(run("scan", texts))

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

    def test_a_none_uat_row_routed_to_the_strong_branch_is_reported(self):
        """#776: the shape #678 shipped — a UAT % never computed read as one that met ≥90%."""
        texts = self.mutated("phase_d", "| none | ≥90% | UAT not established |",
                             "| none | ≥90% | Results look strong |")
        problems = run("strong", texts)
        self.assertTrue(any("UAT % None is routed to 'Results look strong'" in p
                            for p in problems), problems)

    def test_the_none_rows_routed_by_accuracy_alone_are_reported(self):
        """#776: all four `none` rows as #678 wrote them."""
        texts = dict(self.texts)
        for old, new in (("| none | ≥90% | UAT not established |",
                          "| none | ≥90% | Results look strong |"),
                         ("| none | 80–89% | UAT not established |",
                          "| none | 80–89% | Results are mixed |"),
                         ("| none | <80% | UAT not established |",
                          "| none | <80% | Results need improvement |"),
                         ("| none | none | UAT not established |",
                          "| none | none | Accuracy shortfall |")):
            self.assertIn(old, texts["phase_d"])
            texts["phase_d"] = texts["phase_d"].replace(old, new, 1)
        self.assertTrue(run("strong", texts))
        self.assertTrue(run("table", texts))   # "UAT not established" is no longer routed to

    def test_a_cell_that_cannot_be_read_is_a_failure_not_a_skip(self):
        texts = self.mutated("phase_d", "| ≥90% | <90% | Accuracy shortfall |",
                             "| mostly fine | a bit low | Accuracy shortfall |")
        problems = run("table", texts)
        self.assertTrue(any("cannot be read as a band" in p for p in problems), problems)

    def test_dropping_the_never_strong_rule_is_reported(self):
        texts = self.mutated("phase_d", "⛔ **(INV-404) Never call a result strong when a metric "
                             "the strong branch explicitly requires falls\nshort or was never "
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

    def test_removing_the_uat_not_established_branch_is_reported(self):
        texts = self.mutated("phase_d", UAT_NOT_BULLET, "- **Something else:**")
        self.assertTrue(run("uat_not", texts))

    def test_a_uat_not_established_branch_without_its_question_is_reported(self):
        texts = self.mutated("phase_d", "    1. Iterate now to establish the UAT % before moving "
                             "on. *(recommended)*\n", "")
        self.assertTrue(run("uat_not", texts))

    def test_a_uat_not_established_branch_without_its_band_is_reported(self):
        texts = self.mutated("phase_d", '`from_verdict: "%s"`' % UAT_NOT_BAND,
                             '`from_verdict: "uat_below_80"`')
        self.assertTrue(run("uat_not", texts))

    def test_a_uat_not_established_branch_that_routes_on_accuracy_is_reported(self):
        texts = self.mutated("phase_d", "The per-record match accuracy is reported as a finding",
                             "The per-record match accuracy decides the band")
        self.assertTrue(run("uat_not", texts))

    def test_pooling_the_buckets_at_the_table_is_reported(self):
        texts = self.mutated("phase_d", "The accuracy column is the **per-record** figure",
                             "The accuracy column is the pooled figure")
        self.assertTrue(run("per_record", texts))

    def test_a_route_that_never_learns_the_band_is_reported(self):
        texts = self.mutated("phase_1", " | %s" % BAND, "")
        self.assertTrue(run("route", texts))

    def test_a_route_that_never_learns_uat_not_established_is_reported(self):
        """#776: the record shape and the band table both accept the new value."""
        for old in (" | %s" % UAT_NOT_BAND, " or `%s`" % UAT_NOT_BAND):
            with self.subTest(removed=old):
                texts = self.mutated("phase_1", old, "")
                self.assertTrue(run("route", texts))

    def test_a_handling_step_that_drops_the_band_is_reported(self):
        texts = self.mutated("phase_d", ", or\n     `%s` on the UAT-not-established branch" %
                             UAT_NOT_BAND, "")
        self.assertTrue(run("route", texts))

    def test_a_resume_that_stops_re_running_phase_d_is_reported(self):
        texts = self.mutated("phase_d", "Phase D runs again in full, from step 21",
                             "Phase D is skipped")
        self.assertTrue(run("resume", texts))

    # --- Module 5 step 16 (#776)

    def test_a_deleted_critical_field_row_is_reported(self):
        texts = self.mutated("m5_phase_2", "| ≥80% | a critical field unmapped | Quality ≥80% "
                             "with a critical field unmapped |\n")
        problems = run("step16_table", texts)
        self.assertTrue(any("matches 0 rows" in p for p in problems), problems)

    def test_a_deleted_critical_field_branch_is_reported(self):
        """The branch's bullet dropped from one block: that block no longer asks it."""
        texts = self.mutated("m5_phase_2", "- **Quality ≥80% with a critical field unmapped:**",
                             "- **Something else:**")
        self.assertTrue(run("step16_blocks", texts))

    def test_a_deleted_no_score_row_is_reported(self):
        texts = self.mutated("m5_phase_2", "| none | any | No quality score |\n")
        problems = run("step16_table", texts)
        self.assertTrue(any("matches 0 rows" in p for p in problems), problems)

    def test_a_deleted_no_score_branch_is_reported(self):
        texts = self.mutated("m5_phase_2", "- **No quality score:**", "- **Something else:**")
        self.assertTrue(run("step16_blocks", texts))

    def test_not_recorded_routed_to_the_strong_branch_is_reported(self):
        """INV-404: a state never established is never read as the one the label requires."""
        texts = self.mutated("m5_phase_2", "| ≥80% | not recorded | Quality ≥80%, critical "
                             "fields not recorded |", "| ≥80% | not recorded | Quality ≥80% and "
                             "all critical fields mapped |")
        problems = run("step16_table", texts)
        self.assertTrue(any("is routed to" in p for p in problems), problems)

    def test_a_no_score_reading_routed_to_the_strong_branch_is_reported(self):
        texts = self.mutated("m5_phase_2", "| none | any | No quality score |",
                             "| none | any | Quality ≥80% and all critical fields mapped |")
        problems = run("step16_table", texts)
        self.assertTrue(any("Quality score None is routed to" in p for p in problems), problems)

    def test_the_step_before_the_fix_fails(self):
        """The shape #776 reported: no table, so the scan finds a gate with nothing to route."""
        texts = dict(self.texts)
        s16 = step16(texts["m5_phase_2"])
        start = s16.index("**Route on the quality score and the critical fields")
        end = s16.index(WHILE_REMAINING)
        texts["m5_phase_2"] = texts["m5_phase_2"].replace(s16[start:end], "", 1)
        self.assertTrue(any("no decision table" in p for p in run("step16_table", texts)))

    def test_a_legend_that_declares_no_states_is_reported(self):
        texts = self.mutated("m5_phase_2", "**Critical fields** is one of\nthree states:",
                             "Critical fields takes:")
        problems = run("step16_table", texts)
        self.assertTrue(any("neither banded nor declared" in p for p in problems), problems)

    def test_an_undeclared_state_in_the_table_is_reported(self):
        texts = self.mutated("m5_phase_2", "| ≥80% | not recorded |", "| ≥80% | unknown |")
        problems = run("step16_table", texts)
        self.assertTrue(any("cannot be read" in p for p in problems), problems)

    def test_a_block_that_loses_a_new_question_is_reported(self):
        texts = self.mutated("m5_phase_2", "  2. Proceed to loading without one.\n", "")
        self.assertTrue(run("step16_blocks", texts))

    def test_a_not_recorded_branch_that_claims_unmapped_fields_is_reported(self):
        texts = self.mutated("m5_phase_2", "say in one line that this source's critical fields\n"
                             "  were not recorded", "treat the critical fields as unmapped and\n"
                             "  say they were not recorded")
        self.assertTrue(run("step16_blocks", texts))

    def test_a_missing_critical_fields_definition_is_reported(self):
        texts = self.mutated("m4", CRITICAL_ANCHOR, "")
        self.assertTrue(run("critical_fields", texts))

    def test_a_step_4_that_restates_the_critical_attributes_is_reported(self):
        """INV-080: a list kept in the skill instead of read from the specification."""
        texts = self.mutated("m5_phase_1", "Note any critical attribute the source lacks "
                             "entirely.", "The critical attributes are NAME, DOB and ADDRESS.")
        problems = run("critical_fields", texts)
        self.assertTrue(any("restates attributes" in p for p in problems), problems)

    def test_a_step_4_that_does_not_record_the_field_is_reported(self):
        texts = self.mutated("m5_phase_1", "- **Record the source's critical fields.**",
                             "- **Note the source's critical fields.**")
        self.assertTrue(run("critical_fields", texts))

    def test_a_second_critical_fields_definition_is_reported(self):
        corpus = shipped_markdown()
        name = M5_PHASE_1.relative_to(REPO_ROOT).as_posix()
        corpus[name] += "\n\n%s, written here too.\n" % CRITICAL_DEFINITION
        self.assertTrue(critical_defined_once_problems(corpus))

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

    def test_a_step_21_bullet_without_the_link_is_reported(self):
        texts = self.mutated("phase_d", " The accuracy judged here is\n  the [per-record match "
                             "accuracy](#per-record-match-accuracy) step 22 computes on this "
                             "sample.", "")
        self.assertEqual(["step 21's accuracy bullet does not link the per-record figure"],
                         run("step_links", texts))

    def test_the_shipped_step_24_is_reported(self):
        """The #809 defect, put back: no link, and precision/recall offered beside accuracy."""
        texts = self.mutated(
            "phase_d", "Validate: match accuracy, which is the [per-record match accuracy]"
            "(#per-record-match-accuracy)\nstep 22 defines, with the records reviewed here "
            "joining its sample (query", "Validate: match accuracy (query")
        texts["phase_d"] = texts["phase_d"].replace(
            "evaluation\nframework.\n", "evaluation\nframework and `reporting_guide(topic="
            "'quality', language='<chosen_language>', version='current')` for precision/recall\n"
            "metrics.\n", 1)
        self.assertEqual(2, len(run("step_links", texts)), run("step_links", texts))

    def test_precision_and_recall_read_as_accuracy_are_reported(self):
        texts = self.mutated("phase_d", "are supporting\nreading only:", "are the accuracy:")
        self.assertEqual(
            ["step 24 does not read precision and recall as supporting reading only"],
            run("step_links", texts))

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
